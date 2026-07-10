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
import secrets

from services.auth.account_provision import create_owner_login_user, find_login_user
from services.auth.signup_core import (
    _ensure_tenant_for_new_user,
    _hash_password,
    normalize_email,
)
from services.pos import entitlements as ent

logger = logging.getLogger("mr-pilot")

_DEFAULT_AMOUNT_THB = 1000
# 初始密码字母表:去掉易混字符(0/O/1/I/l),人念/手输/口头转交友好。
_PW_LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"
_PW_DIGITS = "23456789"
_PW_LEN = 12


def _gen_initial_password() -> str:
    """生成一次性初始密码:满足 /reset 强度闸(≥8 · 至少一字母一数字),取 12 位。"""
    pool = _PW_LETTERS + _PW_DIGITS
    while True:
        pw = "".join(secrets.choice(pool) for _ in range(_PW_LEN))
        if any(c in _PW_LETTERS for c in pw) and any(c in _PW_DIGITS for c in pw):
            return pw


def provision_pos_account(
    cur,
    *,
    email: str,
    tenant_name: str | None = None,
    granted_by: str | None = None,
    amount_paid_thb=None,
) -> dict:
    """发放 POS 账号一条龙。调用方负责 commit(建号/建租户/grant 同一事务)。

    返回 {existed, user_id, tenant_id, grant_code, initial_password}。
    initial_password 仅在【新建账号】时非 None(一次性回显),已存在账号恒 None。
    邮箱非法 → ValueError('email_invalid');重复开通/建租户失败 → ValueError(由路由翻错误码)。
    """
    email_clean = (email or "").strip().lower()
    if not email_clean or "@" not in email_clean or "." not in email_clean.split("@", 1)[1]:
        raise ValueError("email_invalid")
    email_norm = normalize_email(email_clean)
    amount = _DEFAULT_AMOUNT_THB if amount_paid_thb is None else amount_paid_thb

    existing = find_login_user(cur, email_norm)
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
        }

    password = _gen_initial_password()
    user_id = create_owner_login_user(
        cur, email=email_clean, email_norm=email_norm, password_hash=_hash_password(password)
    )
    tid = _ensure_tenant_for_new_user(
        cur, user_id, "credits", company_name=tenant_name, username=email_clean
    )
    if not tid:
        raise ValueError("tenant_provision_failed")
    row = ent.grant(cur, tenant_id=tid, amount_paid_thb=amount, granted_by=granted_by)
    return {
        "existed": False,
        "user_id": user_id,
        "tenant_id": str(tid),
        "grant_code": row["grant_code"],
        "initial_password": password,
    }
