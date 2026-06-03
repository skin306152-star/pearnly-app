# -*- coding: utf-8 -*-
"""ERP OAuth 2.0 token 存储 · 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
Xero / FlowAccount / QuickBooks 共用的 OAuth token + state 表 CRUD ·
含 base64 token 编解码 helper(_b64_encode/_b64_decode)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging

from core import db

logger = logging.getLogger(__name__)


def ensure_erp_oauth_tables():
    """v118.27.4 · OAuth token 表 + state 临时表 · 启动时幂等建
    v27.8.1.3 加 auto_push 字段(端到端自动推开关 · tenant 级别)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_oauth_tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    erp_type TEXT NOT NULL,
                    organisation_id TEXT NOT NULL,
                    organisation_name TEXT,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    scope TEXT,
                    is_default BOOLEAN NOT NULL DEFAULT FALSE,
                    token_version INT NOT NULL DEFAULT 1,
                    created_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(tenant_id, erp_type, organisation_id)
                );
                CREATE INDEX IF NOT EXISTS idx_oauth_tokens_tenant ON erp_oauth_tokens(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_oauth_tokens_default ON erp_oauth_tokens(is_default) WHERE is_default = TRUE;
            """)
            # v27.8.1.3 · 幂等加 auto_push 字段
            cur.execute("""
                ALTER TABLE erp_oauth_tokens
                ADD COLUMN IF NOT EXISTS auto_push BOOLEAN NOT NULL DEFAULT FALSE;
            """)
            # OAuth state 防 CSRF · 5 分钟过期
            cur.execute("""
                CREATE TABLE IF NOT EXISTS erp_oauth_states (
                    state TEXT PRIMARY KEY,
                    tenant_id UUID NOT NULL,
                    user_id UUID NOT NULL,
                    erp_type TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_oauth_states_created ON erp_oauth_states(created_at);
            """)
            logger.info(
                "✅ v118.27.4 · erp_oauth_tokens / erp_oauth_states 表已就绪(含 v27.8.1.3 auto_push)"
            )
    except Exception as e:
        logger.error(f"ensure_erp_oauth_tables failed: {e}")


def set_xero_auto_push(tenant_id: str, on: bool) -> bool:
    """v27.8.1.3 · 切换 Xero 自动推送开关(tenant 级别 · 影响所有 org)"""
    if not tenant_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_oauth_tokens SET auto_push = %s, updated_at = NOW()
                WHERE tenant_id = %s AND erp_type = 'xero'
            """,
                (bool(on), tenant_id),
            )
        return True
    except Exception as e:
        logger.error(f"set_xero_auto_push failed: {e}")
        return False


def get_xero_auto_push(tenant_id: str) -> bool:
    """v27.8.1.3 · 拿 Xero 自动推送状态(任一 org auto_push=true 都算开)"""
    if not tenant_id:
        return False
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM erp_oauth_tokens
                WHERE tenant_id = %s AND erp_type = 'xero' AND auto_push = TRUE LIMIT 1
            """,
                (tenant_id,),
            )
            return cur.fetchone() is not None
    except Exception:
        return False


def list_tenants_xero_auto_push_on() -> list:
    """v27.8.1.3 · 给 OCR hook 用 · 拉所有开了 Xero 自动推的 tenant_id 列表"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT DISTINCT tenant_id::text AS tid
                FROM erp_oauth_tokens
                WHERE erp_type = 'xero' AND auto_push = TRUE
            """)
            return [r["tid"] for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_tenants_xero_auto_push_on failed: {e}")
        return []


def _b64_encode(s: str) -> str:
    """v118.27.4 · token_version=1 · base64 编码(P1 升 AES)"""
    import base64

    return base64.b64encode((s or "").encode("utf-8")).decode("ascii")


def _b64_decode(s: str) -> str:
    import base64

    try:
        return base64.b64decode((s or "").encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def save_oauth_state(state, tenant_id, user_id, erp_type):
    """存 state · 5 分钟过期 · 同 tenant 同 erp 老的会被覆盖"""
    if not state or not tenant_id or not user_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            # 顺手清掉 5 分钟前的 state(轻量 GC)
            cur.execute(
                "DELETE FROM erp_oauth_states WHERE created_at < NOW() - INTERVAL '5 minutes'"
            )
            cur.execute(
                """
                INSERT INTO erp_oauth_states (state, tenant_id, user_id, erp_type)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (state) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    user_id = EXCLUDED.user_id,
                    erp_type = EXCLUDED.erp_type,
                    created_at = NOW()
            """,
                (str(state), str(tenant_id), str(user_id), str(erp_type)),
            )
            return True
    except Exception as e:
        logger.error(f"save_oauth_state failed: {e}")
        return False


def consume_oauth_state(state):
    """callback 用 · 验证 + 单次消费"""
    if not state:
        return None
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                DELETE FROM erp_oauth_states
                WHERE state = %s AND created_at >= NOW() - INTERVAL '5 minutes'
                RETURNING tenant_id, user_id, erp_type
            """,
                (str(state),),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "tenant_id": str(row["tenant_id"]),
                "user_id": str(row["user_id"]),
                "erp_type": str(row["erp_type"]),
            }
    except Exception as e:
        logger.error(f"consume_oauth_state failed: {e}")
        return None


def upsert_oauth_token(
    tenant_id,
    erp_type,
    organisation_id,
    organisation_name,
    access_token,
    refresh_token,
    expires_at,
    scope,
    is_default,
    user_id,
):
    """存/更新 OAuth token · 同 (tenant, erp, org) 覆盖
    expires_at: datetime aware 或 ISO 字符串
    """
    if (
        not tenant_id
        or not erp_type
        or not organisation_id
        or not access_token
        or not refresh_token
    ):
        return None
    try:
        with db.get_cursor(commit=True) as cur:
            if is_default:
                # 同 tenant 同 erp 老的全部 unset is_default
                cur.execute(
                    "UPDATE erp_oauth_tokens SET is_default = FALSE WHERE tenant_id = %s AND erp_type = %s",
                    (str(tenant_id), str(erp_type)),
                )
            cur.execute(
                """
                INSERT INTO erp_oauth_tokens
                    (tenant_id, erp_type, organisation_id, organisation_name,
                     access_token, refresh_token, expires_at, scope,
                     is_default, token_version, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
                ON CONFLICT (tenant_id, erp_type, organisation_id)
                DO UPDATE SET
                    organisation_name = EXCLUDED.organisation_name,
                    access_token = EXCLUDED.access_token,
                    refresh_token = EXCLUDED.refresh_token,
                    expires_at = EXCLUDED.expires_at,
                    scope = EXCLUDED.scope,
                    is_default = EXCLUDED.is_default,
                    updated_at = NOW()
                RETURNING id
            """,
                (
                    str(tenant_id),
                    str(erp_type),
                    str(organisation_id),
                    (organisation_name or "")[:200],
                    _b64_encode(access_token),
                    _b64_encode(refresh_token),
                    expires_at,
                    (scope or "")[:500],
                    bool(is_default),
                    str(user_id) if user_id else None,
                ),
            )
            row = cur.fetchone()
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"upsert_oauth_token failed: {e}")
        return None


def get_default_oauth_token(tenant_id, erp_type):
    """拿默认 organisation 的 token(解码后明文)"""
    if not tenant_id or not erp_type:
        return None
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, organisation_id, organisation_name,
                       access_token, refresh_token, expires_at, scope, is_default,
                       token_version, updated_at
                FROM erp_oauth_tokens
                WHERE tenant_id = %s AND erp_type = %s
                ORDER BY is_default DESC, updated_at DESC
                LIMIT 1
            """,
                (str(tenant_id), str(erp_type)),
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["access_token"] = _b64_decode(d["access_token"])
            d["refresh_token"] = _b64_decode(d["refresh_token"])
            return d
    except Exception as e:
        logger.error(f"get_default_oauth_token failed: {e}")
        return None


def list_oauth_tokens(tenant_id, erp_type):
    """列出该 tenant 在该 ERP 下所有 organisation(供 UI 切换)"""
    if not tenant_id or not erp_type:
        return []
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, organisation_id, organisation_name, expires_at,
                       is_default, scope, updated_at
                FROM erp_oauth_tokens
                WHERE tenant_id = %s AND erp_type = %s
                ORDER BY is_default DESC, organisation_name ASC
            """,
                (str(tenant_id), str(erp_type)),
            )
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"list_oauth_tokens failed: {e}")
        return []


def update_oauth_access_token(token_id, access_token, refresh_token, expires_at):
    """refresh 后写回新 access + refresh + expires"""
    if not token_id or not access_token or not refresh_token:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE erp_oauth_tokens
                SET access_token = %s,
                    refresh_token = %s,
                    expires_at = %s,
                    updated_at = NOW()
                WHERE id = %s
            """,
                (
                    _b64_encode(access_token),
                    _b64_encode(refresh_token),
                    expires_at,
                    str(token_id),
                ),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"update_oauth_access_token failed: {e}")
        return False


def delete_oauth_tokens(tenant_id, erp_type):
    """断开连接 · 删该 tenant 在该 ERP 的所有 token"""
    if not tenant_id or not erp_type:
        return 0
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM erp_oauth_tokens WHERE tenant_id = %s AND erp_type = %s",
                (str(tenant_id), str(erp_type)),
            )
            return cur.rowcount
    except Exception as e:
        logger.error(f"delete_oauth_tokens failed: {e}")
        return 0


def set_default_oauth_token(tenant_id, erp_type, token_id):
    """切换默认 organisation"""
    if not tenant_id or not erp_type or not token_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE erp_oauth_tokens SET is_default = FALSE WHERE tenant_id = %s AND erp_type = %s",
                (str(tenant_id), str(erp_type)),
            )
            cur.execute(
                "UPDATE erp_oauth_tokens SET is_default = TRUE, updated_at = NOW() "
                "WHERE id = %s AND tenant_id = %s AND erp_type = %s",
                (str(token_id), str(tenant_id), str(erp_type)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"set_default_oauth_token failed: {e}")
        return False
