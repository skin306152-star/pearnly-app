# -*- coding: utf-8 -*-
"""Pearnly DMS · 独立 LINE 通道的绑定 / 绑定码 / 会话 DAL(DL-1)。

老会计站 line_bindings 与本包三表完全隔离:DMS 是独立产品、独立 LINE OA,不复用
line_binding.store 以免两条产品线互相牵连(换绑冲突、RLS、TTL 语义各走各的)。

三张表:
  line_dms_bindings       —— LINE user ↔ (tenant, user) 绑定,line_user_id UNIQUE。
  line_dms_binding_codes  —— 6 位数字绑定码(App 发码 · webhook 核销),code PK。
  dms_line_sessions       —— 多轮会话态(state + payload + TTL),(tenant, line_user) PK。

建表照 line_intent_store 范式:prod 无 alembic 钩子 → 首用 ensure 幂等自愈 + _with_heal
重试一次。绑定/绑定码按 line_user_id 反查(webhook 无登录态,穿不进租户上下文)故走 owner
连接;会话态租户已知 → 走 get_cursor_rls 施加 RLS(与 line_intent_store 同款)。
"""

from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_CODE_TTL_MINUTES = 10

_BINDINGS = """
CREATE TABLE IF NOT EXISTS line_dms_bindings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    line_user_id text UNIQUE,
    tenant_id uuid NOT NULL,
    user_id uuid NOT NULL,
    display_name text,
    bound_at timestamptz DEFAULT now(),
    last_active_at timestamptz
)
"""

_BINDING_CODES = """
CREATE TABLE IF NOT EXISTS line_dms_binding_codes (
    code text PRIMARY KEY,
    tenant_id uuid,
    user_id uuid,
    expires_at timestamptz,
    used_at timestamptz
)
"""

_SESSIONS = """
CREATE TABLE IF NOT EXISTS dms_line_sessions (
    tenant_id uuid NOT NULL,
    line_user_id text NOT NULL,
    state text,
    payload jsonb DEFAULT '{}',
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, line_user_id)
)
"""

_TABLES = ("line_dms_bindings", "line_dms_binding_codes", "dms_line_sessions")


def ensure_tables() -> None:
    """幂等建三表 + apply_tenant_rls(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_BINDINGS)
        cur.execute(_BINDING_CODES)
        cur.execute(_SESSIONS)
        apply_tenant_rls(cur, *_TABLES)


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方兜底。"""
    try:
        return fn()
    except Exception as e:
        if not any(t in str(e) for t in _TABLES):
            raise
        ensure_tables()
        return fn()


def _dal(label: str, default):
    """DAL 兜底套件:跑 fn(经 _with_heal 建表重试一次),异常记 error 返 default。

    webhook 无人接错 → 失败软降级不抛。业务函数只留 SQL 与结果整形。用法 `_dal(label, dft)(fn)`。
    """

    def run(fn):
        try:
            return _with_heal(fn)
        except Exception as e:
            logger.error(f"[line_dms] {label} failed: {e}")
            return default

    return run


# ── 绑定码 ────────────────────────────────────────────────────────────────


def generate_bind_code(tenant_id, user_id, ttl_minutes: int = DEFAULT_CODE_TTL_MINUTES):
    """为 (tenant, user) 发一个 6 位数字绑定码,作废该 user 旧的未用码(只留最新一个)。

    返回 {"code", "expires_at"(iso)} 或 None。
    """
    from core import db

    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=int(ttl_minutes))

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE line_dms_binding_codes SET used_at = now() "
                "WHERE user_id = %s AND used_at IS NULL",
                (str(user_id),),
            )
            cur.execute(
                "INSERT INTO line_dms_binding_codes (code, tenant_id, user_id, expires_at) "
                "VALUES (%s, %s, %s, %s) RETURNING code, expires_at",
                (code, str(tenant_id), str(user_id), expires_at),
            )
            return cur.fetchone()

    row = _dal("generate_bind_code", None)(_run)
    if not row:
        return None
    return {"code": row["code"], "expires_at": row["expires_at"].isoformat()}


def consume_bind_code(code: str) -> Optional[dict]:
    """核销绑定码(6 位数字 · 未用 · 未过期)→ 标记已用并返回 {tenant_id, user_id}。

    无效/已用/过期 → None。webhook 无租户上下文 → owner 连接。
    """
    from core import db

    code = (code or "").strip()
    if len(code) != 6 or not code.isdigit():
        return None

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE line_dms_binding_codes SET used_at = now() "
                "WHERE code = %s AND used_at IS NULL AND expires_at > now() "
                "RETURNING tenant_id, user_id",
                (code,),
            )
            return cur.fetchone()

    row = _dal("consume_bind_code", None)(_run)
    if not row:
        return None
    return {"tenant_id": str(row["tenant_id"]), "user_id": str(row["user_id"])}


def peek_bind_code_tenant(code: str) -> Optional[str]:
    """窥探绑定码所属租户(不核销 · 不动 used_at)· 供「先按码定租户判闸再决定是否核销」。

    未绑用户提交码时 webhook 无租户上下文,须先知道码归谁才能按该租户判 dms_line 闸——否则
    allowlist 灰度下 tenant=None 恒判关会静默吞码。命中(不论未用/已用/过期)→ tenant_id 串;
    无此码(判不出归属)→ None(fail-closed)。owner 连接(webhook 无登录态)。
    """
    from core import db

    code = (code or "").strip()
    if len(code) != 6 or not code.isdigit():
        return None

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT tenant_id FROM line_dms_binding_codes WHERE code = %s LIMIT 1",
                (code,),
            )
            return cur.fetchone()

    row = _dal("peek_bind_code_tenant", None)(_run)
    if not row or row.get("tenant_id") is None:
        return None
    return str(row["tenant_id"])


# ── 绑定 ─────────────────────────────────────────────────────────────────


def create_or_update_binding(
    tenant_id, user_id, line_user_id: str, display_name: Optional[str] = None
) -> bool:
    """建/换绑 LINE user ↔ (tenant, user)。line_user_id 已绑别的 user → 拒绝(返回 False)。

    同一 user 换到新 LINE 账号 → 先删其旧绑定;重复绑同一对 → 更新昵称/活跃时间。
    """
    from core import db

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "SELECT user_id FROM line_dms_bindings WHERE line_user_id = %s LIMIT 1",
                (line_user_id,),
            )
            row = cur.fetchone()
            if row and str(row["user_id"]) != str(user_id):
                logger.warning(
                    f"[line_dms] LINE {line_user_id} 已绑 user {row['user_id']}·拒绑 {user_id}"
                )
                return False
            cur.execute(
                "DELETE FROM line_dms_bindings WHERE user_id = %s AND line_user_id != %s",
                (str(user_id), line_user_id),
            )
            cur.execute(
                "INSERT INTO line_dms_bindings "
                "(line_user_id, tenant_id, user_id, display_name, last_active_at) "
                "VALUES (%s, %s, %s, %s, now()) "
                "ON CONFLICT (line_user_id) DO UPDATE SET "
                "  tenant_id = EXCLUDED.tenant_id, user_id = EXCLUDED.user_id, "
                "  display_name = EXCLUDED.display_name, last_active_at = now()",
                (line_user_id, str(tenant_id), str(user_id), display_name),
            )
            return True

    return bool(_dal("create_or_update_binding", False)(_run))


def get_binding_by_line_user(line_user_id: str) -> Optional[dict]:
    """按 LINE user 反查绑定(webhook 入口用)。无 → None。"""
    from core import db

    if not line_user_id:
        return None

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT tenant_id, user_id, display_name, bound_at "
                "FROM line_dms_bindings WHERE line_user_id = %s LIMIT 1",
                (line_user_id,),
            )
            return cur.fetchone()

    row = _dal("get_binding_by_line_user", None)(_run)
    return _binding_dict(row, line_user_id) if row else None


def get_binding_by_user(user_id: str) -> Optional[dict]:
    """按 Pearnly user 查绑定(App 侧「已绑?」用)。无 → None。"""
    from core import db

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT line_user_id, tenant_id, display_name, bound_at "
                "FROM line_dms_bindings WHERE user_id = %s LIMIT 1",
                (str(user_id),),
            )
            return cur.fetchone()

    row = _dal("get_binding_by_user", None)(_run)
    return dict(row) if row else None


def unbind_by_user(user_id: str) -> bool:
    """App 侧主动解绑。"""
    from core import db

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM line_dms_bindings WHERE user_id = %s", (str(user_id),))
            return True

    return bool(_dal("unbind_by_user", False)(_run))


def void_bind_codes_for_user(user_id: str) -> bool:
    """作废该 user 全部未用绑定码(停用操作员时的收权动作:在外流通的码即刻失效)。"""
    from core import db

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE line_dms_binding_codes SET used_at = now() "
                "WHERE user_id = %s AND used_at IS NULL",
                (str(user_id),),
            )
            return True

    return bool(_dal("void_bind_codes_for_user", False)(_run))


def unbind_by_line_user(line_user_id: str) -> bool:
    """LINE 侧解绑(unfollow / 解绑命令)。返回是否真删到一行。"""
    from core import db

    if not line_user_id:
        return False

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM line_dms_bindings WHERE line_user_id = %s", (line_user_id,))
            return cur.rowcount > 0

    return bool(_dal("unbind_by_line_user", False)(_run))


def _binding_dict(row, line_user_id: str) -> dict:
    out = dict(row)
    out["line_user_id"] = line_user_id
    out["tenant_id"] = str(out["tenant_id"])
    out["user_id"] = str(out["user_id"])
    return out


# ── 会话态 ────────────────────────────────────────────────────────────────


def set_session(tenant_id, line_user_id: str, state: str, payload=None, ttl_minutes: int = 30):
    """存/覆盖会话态(upsert)。TTL 默认 30 分钟。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO dms_line_sessions "
                "(tenant_id, line_user_id, state, payload, expires_at) "
                "VALUES (%s, %s, %s, %s::jsonb, now() + make_interval(mins => %s)) "
                "ON CONFLICT (tenant_id, line_user_id) DO UPDATE SET "
                "  state = EXCLUDED.state, payload = EXCLUDED.payload, "
                "  expires_at = EXCLUDED.expires_at",
                (
                    str(tenant_id),
                    str(line_user_id),
                    state,
                    json.dumps(payload or {}, ensure_ascii=False),
                    int(ttl_minutes),
                ),
            )

    try:
        _with_heal(_run)
    except Exception as e:
        logger.warning(f"[line_dms] set_session failed: {e}")


def get_session(tenant_id, line_user_id: str) -> Optional[dict]:
    """读未过期会话态(过期视为无)。返回 {state, payload} 或 None。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT state, payload FROM dms_line_sessions "
                "WHERE tenant_id = %s AND line_user_id = %s AND expires_at > now()",
                (str(tenant_id), str(line_user_id)),
            )
            return cur.fetchone()

    try:
        row = _with_heal(_run)
    except Exception:
        logger.warning("[line_dms] get_session failed; treat as none", exc_info=True)
        return None
    if not row:
        return None
    payload = row.get("payload")
    return {
        "state": row.get("state"),
        "payload": payload if isinstance(payload, dict) else json.loads(payload or "{}"),
    }


def clear_session(tenant_id, line_user_id: str) -> None:
    """删会话态(会话结束/取消)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "DELETE FROM dms_line_sessions WHERE tenant_id = %s AND line_user_id = %s",
                (str(tenant_id), str(line_user_id)),
            )

    try:
        _with_heal(_run)
    except Exception as e:
        logger.warning(f"[line_dms] clear_session failed: {e}")


def consume_nonce(tenant_id, line_user_id: str, expect_state: str, nonce: str) -> Optional[dict]:
    """确认执行守卫:会话须在 expect_state 且 payload.nonce 吻合 nonce → 原子清 nonce
    并返回 payload;态不符 / 无会话 / 无 nonce / 不吻合 → None(绝不写)。

    token 一次性:清 nonce 后同一 nonce 的二次确认必然 mismatch(防双击双写 / 双建单)。
    """
    sess = get_session(tenant_id, line_user_id)
    payload = (sess or {}).get("payload") or {}
    if not sess or sess.get("state") != expect_state:
        return None
    if not payload.get("nonce") or payload.get("nonce") != nonce:
        return None
    set_session(tenant_id, line_user_id, expect_state, {**payload, "nonce": None})
    return payload
