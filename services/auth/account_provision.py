# -*- coding: utf-8 -*-
"""登录账号(users 表)查找 / 建号的事务级 DAL(PS-5 · 供超管发放账号复用)。

放在 auth 域而非 services/pos:users 是【全局】账号表(建号时还没租户,tenant_id 随后由
_ensure_tenant_for_new_user 补),不受 POS 租户隔离闸约束——POS 隔离闸只管 services/pos +
services/inventory 里的租户维度表。这里的两个 helper 都吃调用方传入的 cursor,和建租户 / grant
落在同一事务里(失败整体回滚,不留半个账号)。
"""

from __future__ import annotations


def find_login_user(cur, email_norm: str):
    """按归一化邮箱找已存在账号(邮箱 / 归一化邮箱 / 用户名三路,与注册防薅同口径)。

    返回 dict(id / tenant_id / username)或 None。用调用方事务游标(与建号同事务)。
    """
    cur.execute(
        "SELECT id::text AS id, tenant_id::text AS tenant_id, username "
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
