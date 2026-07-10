# -*- coding: utf-8 -*-
"""Earn 超管「发放 POS 账号」一条龙(PS-5)。

现有 admin_pos_entitlement_routes 的 grant 只对【已存在】租户开通;拆卖客户常常连账号都还没有。
本模块补上「输邮箱 → 若无账号则建号 + 建租户 + grant 一条龙」:

  - 邮箱已存在 → 走既有租户开通路(拿该用户的租户,直接 grant),绝不返回密码。
  - 邮箱不存在 → 建 owner 用户(生成一次性初始密码,仅回显给超管转交客户)+ 建租户
    (复用注册同一入口 _ensure_tenant_for_new_user)+ grant。grant 内 apply_preset('pos_only')
    会把业态切成精简外壳并清「待选业态」标记,客户首登直接进 7 项 POS 后台。

铁律面:密码用 secrets 生成、只在返回值里出现一次、绝不写日志(调用方 _log_op 也不得带);
建号/建租户/grant 全在调用方同一 commit 事务里(cur 传入),失败整体回滚不留半个账号。
初始密码满足重置流强度(≥8 · 含字母和数字),客户可随时用现有改密流自行更换。
"""

from __future__ import annotations

import logging

from services.auth.account_provision import (
    create_owner_login_user,
    find_login_user,
    generate_one_time_password as _gen_initial_password,  # noqa: F401 · 单测经本名引用
    resolve_account_identifier,
    resolve_password,
    write_login_password,
)
from services.auth.signup_core import (
    _ensure_tenant_for_new_user,
    _hash_password,
)
from services.pos import entitlements as ent

logger = logging.getLogger("mr-pilot")

_DEFAULT_AMOUNT_THB = 1000


def provision_pos_account(
    cur,
    *,
    account: str,
    tenant_name: str | None = None,
    granted_by: str | None = None,
    amount_paid_thb=None,
    password: str | None = None,
) -> dict:
    """发放 POS 账号一条龙。调用方负责 commit(建号/建租户/grant 同一事务)。

    account 支持任意用户名或邮箱(resolve_account_identifier 归一);用户名大小写不敏感、
    存储归一小写,登录按 username 走(邮箱非必填)。password 可选:传了(过策略校验)就作
    初始密码,留空自动生成强随机;账号已存在时不改密(existed 路不碰凭据,要改走重置密码流)。
    返回 {existed, user_id, tenant_id, grant_code, initial_password, username};
    initial_password 仅【新建账号】非 None(一次性回显,自定义的也回显)。
    账号标识非法 → ValueError('email_invalid' | 'username_invalid' | 'account_missing');
    密码不合格 → ValueError('password_too_*');建租户失败 → ValueError(由路由翻错误码)。
    """
    ident = resolve_account_identifier(account)
    amount = _DEFAULT_AMOUNT_THB if amount_paid_thb is None else amount_paid_thb

    existing = find_login_user(cur, ident["lookup_key"])
    if existing:
        tid = existing.get("tenant_id")
        if not tid:
            # 账号在、但没租户(历史 orphan)→ 补建租户再开通,不另起炉灶。
            tid = _ensure_tenant_for_new_user(
                cur,
                existing["id"],
                "credits",
                company_name=tenant_name,
                username=existing.get("username"),
            )
            if not tid:
                raise ValueError("tenant_provision_failed")
        row = ent.grant(cur, tenant_id=tid, amount_paid_thb=amount, granted_by=granted_by)
        return {
            "existed": True,
            "user_id": existing["id"],
            "tenant_id": str(tid),
            "grant_code": row["grant_code"],
            "initial_password": None,
            "username": existing.get("username"),
        }

    initial_password = resolve_password(password)
    user_id = create_owner_login_user(
        cur,
        username=ident["username"],
        email=ident["email"],
        email_norm=ident["email_norm"],
        password_hash=_hash_password(initial_password),
    )
    tid = _ensure_tenant_for_new_user(
        cur, user_id, "credits", company_name=tenant_name, username=ident["username"]
    )
    if not tid:
        raise ValueError("tenant_provision_failed")
    row = ent.grant(cur, tenant_id=tid, amount_paid_thb=amount, granted_by=granted_by)
    return {
        "existed": False,
        "user_id": user_id,
        "tenant_id": str(tid),
        "grant_code": row["grant_code"],
        "initial_password": initial_password,
        "username": ident["username"],
    }


def reset_pos_account_password(cur, *, account: str, password: str | None = None) -> dict:
    """发放制账号重置密码(超管 · Earn 后台)。调用方负责 commit。

    account 支持任意用户名或邮箱(与发放同一 resolve_account_identifier 口径)。范围严格
    限定(2026-07-10 安全纠正 · 照 TaxOps Z1-c 先例):账号所属租户必须持 pos_entitlement
    (任意 status)且账号是该租户成员(users.tenant_id 归属);超管账号、无租户账号、租户无
    授权(=主站自由注册用户,有自助忘记密码通道)、账号不存在、标识非法——一律
    ValueError('not_in_scope'),路由统一翻 404 不区分缘由(防枚举)。历史上通用超管改密
    端点因账户接管风险被砍 410(勘察修复台账 #1),此处绝不复活通用口。

    password 可选:传了(过策略校验)就用它,留空自动生成强随机。返回
    {user_id, account, new_password};明文只出现在返回值里,绝不写日志(调用方审计也不得带)。
    """
    try:
        ident = resolve_account_identifier(account)
    except ValueError:
        # 标识非法(空/超长/带空格)与「查无此账号」同归 not_in_scope,不泄露差异(防枚举)。
        raise ValueError("not_in_scope") from None
    user = find_login_user(cur, ident["lookup_key"])
    if not user or user.get("is_super_admin") or not user.get("tenant_id"):
        raise ValueError("not_in_scope")
    if not ent.get_for_tenant(cur, tenant_id=user["tenant_id"], active_only=False):
        raise ValueError("not_in_scope")

    new_password = resolve_password(password)
    write_login_password(cur, user_id=user["id"], password_hash=_hash_password(new_password))
    return {"user_id": user["id"], "account": ident["username"], "new_password": new_password}
