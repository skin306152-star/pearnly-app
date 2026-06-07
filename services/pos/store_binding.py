# -*- coding: utf-8 -*-
"""收银台设备绑定:店铺码 DAL(POS 项目 · docs/pos/04 §1b)。

每个 (tenant, workspace) 一个短店铺码(如 MTA-7K9Q · 全局唯一 · 设备扫码/输码绑定)。绑定 = 服务端
按码解析出 (tenant, workspace) 并签发长期店铺令牌(core.auth.create_pos_store_token)。老板「重置」=
换码 + bump token_version,旧设备令牌 ver 对不上即失效。每条语句 WHERE tenant_id(应用层硬隔离 ·
prod BYPASSRLS · 见 [[pos-rls-bypass-app-layer-isolation]]);resolve(按码反查)是绑定前唯一入口,
码本身即低敏凭证(列收银员名 + 需 PIN 才能卖),故走 bypass 游标按 code 查。
"""

from __future__ import annotations

import logging
import re
import secrets
from typing import Optional

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

# 去掉易混字符(0/O/1/I/L)的大写字母数字表
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_BODY_LEN = 4


def ensure_store_schema() -> None:
    """幂等建表 + RLS(启动双跑 · 与 alembic 0028 同源 · prod 无自动迁移)。失败仅告警。"""
    from core import db

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_store_codes (
                    id bigserial PRIMARY KEY,
                    tenant_id uuid NOT NULL,
                    workspace_client_id bigint NOT NULL,
                    code text NOT NULL,
                    token_version integer NOT NULL DEFAULT 1,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    UNIQUE (tenant_id, workspace_client_id)
                )
                """)
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_store_code ON pos_store_codes (code)"
            )
            apply_tenant_rls(cur, "pos_store_codes")
        logger.info("✅ pos_store_codes 表 + RLS 已就绪 (店铺码绑定)")
    except Exception as e:
        logger.warning(f"ensure_store_schema 失败(跳过 · 等 alembic 0028): {e}")


def _prefix(store_name: Optional[str]) -> str:
    letters = re.sub(r"[^A-Za-z]", "", store_name or "").upper()
    return (letters[:3] or "POS").ljust(3, "X")


def _gen_code(prefix: str) -> str:
    body = "".join(secrets.choice(_ALPHABET) for _ in range(_BODY_LEN))
    return f"{prefix}-{body}"


def _unique_code(cur, prefix: str) -> str:
    for _ in range(12):
        code = _gen_code(prefix)
        # 全局码唯一性探测(店铺码跨租户唯一 · 绑定前按码反查)· 选 tenant_id 列即存在性
        cur.execute("SELECT tenant_id FROM pos_store_codes WHERE code = %s", (code,))
        if not cur.fetchone():
            return code
    # 极小概率连撞 12 次 → 退化为更长随机体
    return f"{prefix}-{''.join(secrets.choice(_ALPHABET) for _ in range(6))}"


def get_or_create_code(cur, *, tenant_id: str, workspace_client_id: int, store_name: str) -> dict:
    """取该账套店铺码(无则建)。返回 {code, token_version}。"""
    cur.execute(
        "SELECT code, token_version FROM pos_store_codes "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row:
        return {"code": row["code"], "token_version": int(row["token_version"])}
    code = _unique_code(cur, _prefix(store_name))
    cur.execute(
        "INSERT INTO pos_store_codes (tenant_id, workspace_client_id, code) VALUES (%s, %s, %s) "
        "ON CONFLICT (tenant_id, workspace_client_id) DO NOTHING "
        "RETURNING code, token_version",
        (tenant_id, workspace_client_id, code),
    )
    row = cur.fetchone()
    if row:
        return {"code": row["code"], "token_version": int(row["token_version"])}
    # 并发下被别人抢先插入 → 回读
    cur.execute(
        "SELECT code, token_version FROM pos_store_codes "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    return {"code": row["code"], "token_version": int(row["token_version"])}


def reset_code(cur, *, tenant_id: str, workspace_client_id: int, store_name: str) -> dict:
    """重置:换新码 + bump token_version(吊销所有已绑设备)。无行则建。返回 {code, token_version}。"""
    code = _unique_code(cur, _prefix(store_name))
    cur.execute(
        "INSERT INTO pos_store_codes (tenant_id, workspace_client_id, code) VALUES (%s, %s, %s) "
        "ON CONFLICT (tenant_id, workspace_client_id) "
        "DO UPDATE SET code = EXCLUDED.code, token_version = pos_store_codes.token_version + 1, "
        "             updated_at = now() "
        "RETURNING code, token_version",
        (tenant_id, workspace_client_id, code),
    )
    row = cur.fetchone()
    return {"code": row["code"], "token_version": int(row["token_version"])}


def resolve(cur, *, code: str):
    """按店铺码反查 (tenant, workspace, token_version)。绑定前入口。找不到返 None。"""
    cur.execute(
        "SELECT tenant_id, workspace_client_id, token_version FROM pos_store_codes WHERE code = %s",
        (code.strip().upper(),),
    )
    return cur.fetchone()


def current_version(cur, *, tenant_id: str, workspace_client_id: int) -> Optional[int]:
    """该账套当前 token_version(校验店铺令牌是否被重置吊销)。无行返 None。"""
    cur.execute(
        "SELECT token_version FROM pos_store_codes "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    return int(row["token_version"]) if row else None
