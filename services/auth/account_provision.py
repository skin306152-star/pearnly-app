# -*- coding: utf-8 -*-
"""登录账号(users 表)查找 / 建号 / 超管重置密码的事务级 DAL(PS-5 · 供超管发放账号复用)。

放在 auth 域而非 services/pos:users 是【全局】账号表(建号时还没租户,tenant_id 随后由
_ensure_tenant_for_new_user 补),不受 POS 租户隔离闸约束——POS 隔离闸只管 services/pos +
services/inventory 里的租户维度表。这里的 helper 都吃调用方传入的 cursor,和建租户 / grant
落在同一事务里(失败整体回滚,不留半个账号)。

重置密码(2026-07-10 Zihao 拍板 + 安全纠正):发放制账号不走自助找回,超管在 Earn 后台重发
一次性密码。本模块【刻意不提供】"按邮箱直接重置"的通用函数——历史上通用超管改密端点因账户
接管风险被砍成 410(勘察修复台账 #1),不许复活。这里只有低层 write_login_password(按
user_id 写哈希),范围判定(账号所属租户持 pos_entitlement + 成员归属)在 services/pos/provision
的 reset_pos_account_password 把关;将来 /acc 发放账号接入时按其发放标记另开门,不走通用口。
"""

from __future__ import annotations

import secrets

# 初始/重置密码字母表:去掉易混字符(0/O/1/I/l),人念/手输/口头转交友好。
_PW_LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz"
_PW_DIGITS = "23456789"
_PW_LEN = 12


def generate_one_time_password() -> str:
    """生成一次性密码:满足 /reset 强度闸(≥8 · 至少一字母一数字),取 12 位。"""
    pool = _PW_LETTERS + _PW_DIGITS
    while True:
        pw = "".join(secrets.choice(pool) for _ in range(_PW_LEN))
        if any(c in _PW_LETTERS for c in pw) and any(c in _PW_DIGITS for c in pw):
            return pw


def validate_custom_password(password: str) -> None:
    """超管自定义密码策略校验:与 /api/auth/reset_password 同口径(≥8 · 含字母和数字)。

    不合格抛 ValueError('password_too_short' | 'password_too_weak'),路由翻 422 结构化人话。
    """
    if not password or len(password) < 8:
        raise ValueError("password_too_short")
    if not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
        raise ValueError("password_too_weak")


def resolve_password(custom: str | None) -> str:
    """发放/重置共用的密码决策:传了自定义就校验后用它,留空自动生成强随机。"""
    if custom:
        validate_custom_password(custom)
        return custom
    return generate_one_time_password()


def find_login_user(cur, email_norm: str):
    """按归一化邮箱找已存在账号(邮箱 / 归一化邮箱 / 用户名三路,与注册防薅同口径)。

    返回 dict(id / tenant_id / username / is_super_admin)或 None。用调用方事务游标。
    """
    cur.execute(
        "SELECT id::text AS id, tenant_id::text AS tenant_id, username, "
        "COALESCE(is_super_admin, FALSE) AS is_super_admin "
        "FROM users WHERE lower(COALESCE(email,'')) = %s "
        "OR lower(COALESCE(email_normalized,'')) = %s OR lower(username) = %s LIMIT 1",
        (email_norm, email_norm, email_norm),
    )
    return cur.fetchone()


def create_owner_login_user(cur, *, email: str, email_norm: str, password_hash: str) -> str:
    """建一个 owner 登录账号(is_active · plan=credits · 初始密码哈希已入库)。返回 user_id。

    只写 users 表铁定存在的核心列(注册路径同款):username/email/email_normalized/
    password_hash/role/plan/is_active;tenant_id 留空,由调用方随后补建租户回填。
    """
    cur.execute(
        "INSERT INTO users (username, email, email_normalized, password_hash, "
        "role, plan, is_active, created_at) "
        "VALUES (%s, %s, %s, %s, 'owner', 'credits', TRUE, NOW()) RETURNING id::text AS id",
        (email, email, email_norm, password_hash),
    )
    row = cur.fetchone()
    return row["id"] if isinstance(row, dict) else row[0]


def write_login_password(cur, *, user_id: str, password_hash: str) -> None:
    """低层:按 user_id 写入新密码哈希(单账号精确定界)。

    刻意只收 user_id 不收邮箱:范围判定(发放制账号)必须先在调用方(services/pos/provision)
    完成,这里不做也做不了绕过。明文密码不进本函数(只收哈希)。
    """
    cur.execute(
        "UPDATE users SET password_hash = %s, password_changed_at = NOW() WHERE id = %s",
        (password_hash, str(user_id)),
    )
