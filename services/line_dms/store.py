# -*- coding: utf-8 -*-
"""Pearnly DMS · 独立 LINE 通道的绑定 / 绑定码 / 会话 DAL(DL-1)。

DMS 使用独立 LINE OA 与专属表，不复用 Cowork / ERP 的绑定状态。

三张表(结构见 schema.py):
  line_dms_bindings       —— (channel, LINE user) ↔ (tenant, user) 绑定,(channel,line_user) 唯一。
  line_dms_binding_codes  —— 6 位数字绑定码(App 发码 · webhook 核销),code PK + channel 归属。
  dms_line_sessions       —— 多轮会话态(state + payload + TTL),(tenant, channel, line_user) PK。

多 OA:channel_key 把绑定/码/会话都钉在签发它的那个 OA 上,同一 LINE id 不会跨 OA 命中。
建表/迁移照 line_intent_store 范式:prod 无 alembic 钩子 → 首用 ensure 幂等自愈 + _with_heal
重试一次。绑定/绑定码按 (channel, line_user_id) 反查(webhook 无登录态,穿不进租户上下文)故走
owner 连接;会话态租户已知 → 走 get_cursor_rls 施加 RLS(与 line_intent_store 同款)。
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.line_dms.schema import _with_heal, ensure_tables  # noqa: F401 · 兼容旧调用点

logger = logging.getLogger(__name__)

DEFAULT_CODE_TTL_MINUTES = 10


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


def _void_unused_codes(cur, user_id) -> None:
    """作废该 user 全部未用绑定码(发新码只留最新 / 停用收权 共用同一句)。"""
    cur.execute(
        "UPDATE line_dms_binding_codes SET used_at = now() "
        "WHERE user_id = %s AND used_at IS NULL",
        (str(user_id),),
    )


def generate_bind_code(
    tenant_id,
    user_id,
    channel_key: Optional[str] = None,
    ttl_minutes: int = DEFAULT_CODE_TTL_MINUTES,
):
    """为 (tenant, user) 发一个 6 位数字绑定码,作废该 user 旧的未用码(只留最新一个)。

    channel_key = 该账号被分配的 OA;码只在同一个 OA 的 webhook 里能被核销(防串 OA)。
    返回 {"code", "expires_at"(iso), "channel_key"} 或 None。
    """
    from core import db
    from services.line_platform import channels as line_channels

    key = line_channels.normalize(channel_key)
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=int(ttl_minutes))

    def _run():
        with db.get_cursor(commit=True) as cur:
            _void_unused_codes(cur, user_id)
            cur.execute(
                "INSERT INTO line_dms_binding_codes "
                "(code, channel_key, tenant_id, user_id, expires_at) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING code, expires_at",
                (code, key, str(tenant_id), str(user_id), expires_at),
            )
            return cur.fetchone()

    row = _dal("generate_bind_code", None)(_run)
    if not row:
        return None
    return {
        "code": row["code"],
        "expires_at": row["expires_at"].isoformat(),
        "channel_key": key,
    }


def consume_bind_code(code: str, channel_key: Optional[str] = None) -> Optional[dict]:
    """核销绑定码(6 位数字 · 未用 · 未过期 · 属于当前 OA)→ 标记已用并返回归属。

    无效/已用/过期/不属于该 OA → None。webhook 无租户上下文 → owner 连接。
    ``channel_key`` 省略时不过滤(仅测试/内部调用);生产 webhook 必须传,否则错 OA 也能兑换。
    """
    from core import db
    from services.line_platform import channels as line_channels

    code = (code or "").strip()
    if len(code) != 6 or not code.isdigit():
        return None
    key = (channel_key or "").strip()

    def _run():
        with db.get_cursor(commit=True) as cur:
            if key:
                cur.execute(
                    "UPDATE line_dms_binding_codes SET used_at = now() "
                    "WHERE code = %s AND channel_key = %s AND used_at IS NULL "
                    "AND expires_at > now() RETURNING tenant_id, user_id, channel_key",
                    (code, key),
                )
            else:
                cur.execute(
                    "UPDATE line_dms_binding_codes SET used_at = now() "
                    "WHERE code = %s AND used_at IS NULL AND expires_at > now() "
                    "RETURNING tenant_id, user_id, channel_key",
                    (code,),
                )
            return cur.fetchone()

    row = _dal("consume_bind_code", None)(_run)
    if not row:
        return None
    return {
        "tenant_id": str(row["tenant_id"]),
        "user_id": str(row["user_id"]),
        "channel_key": line_channels.normalize(row.get("channel_key")),
    }


def peek_bind_code_tenant(code: str, channel_key: Optional[str] = None) -> Optional[str]:
    """窥探绑定码所属租户(不核销 · 不动 used_at)· 供「先按码定租户判闸再决定是否核销」。

    未绑用户提交码时 webhook 无租户上下文,须先知道码归谁才能按该租户判 dms_line 闸——否则
    allowlist 灰度下 tenant=None 恒判关会静默吞码。命中(不论未用/已用/过期)→ tenant_id 串;
    无此码(判不出归属)→ None(fail-closed)。owner 连接(webhook 无登录态)。

    传 channel_key 时只认该 OA 的码:在错误 OA 里提交正确码 → 判不出归属 → 零回复零核销。
    """
    from core import db

    code = (code or "").strip()
    if len(code) != 6 or not code.isdigit():
        return None
    key = (channel_key or "").strip()

    def _run():
        with db.get_cursor() as cur:
            if key:
                cur.execute(
                    "SELECT tenant_id FROM line_dms_binding_codes "
                    "WHERE code = %s AND channel_key = %s LIMIT 1",
                    (code, key),
                )
            else:
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
    tenant_id,
    user_id,
    line_user_id: str,
    display_name: Optional[str] = None,
    channel_key: Optional[str] = None,
) -> bool:
    """建/换绑 (channel, LINE user) ↔ (tenant, user)。同 OA 的 line_user_id 已绑别的 user → 拒。

    一个 user 任一时刻只留一个绑定(跨 OA 也先删旧);重复绑同一对 → 更新昵称/活跃时间。
    """
    from core import db
    from services.line_dms import binding_state
    from services.line_platform import channels as line_channels

    key = line_channels.normalize(channel_key)
    old_lines = []

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                ("dms-binding-user:" + str(user_id),),
            )
            binding_state.lock_line(cur, line_user_id, key)
            cur.execute(
                "SELECT user_id FROM line_dms_bindings "
                "WHERE channel_key = %s AND line_user_id = %s LIMIT 1",
                (key, line_user_id),
            )
            row = cur.fetchone()
            if row and str(row["user_id"]) != str(user_id):
                logger.warning(
                    f"[line_dms] LINE {line_user_id} 已绑 user {row['user_id']}·拒绑 {user_id}"
                )
                return False
            cur.execute(
                "SELECT line_user_id, channel_key FROM line_dms_bindings WHERE user_id=%s",
                (str(user_id),),
            )
            for old in cur.fetchall():
                old_lines.append((old["line_user_id"], old["channel_key"]))
                binding_state.lock_line(cur, old["line_user_id"], old["channel_key"])
                binding_state.invalidate(cur, old["line_user_id"], user_id)
            binding_state.invalidate(cur, line_user_id, user_id)
            cur.execute(
                "DELETE FROM line_dms_bindings WHERE user_id = %s "
                "AND NOT (channel_key = %s AND line_user_id = %s)",
                (str(user_id), key, line_user_id),
            )
            cur.execute(
                "INSERT INTO line_dms_bindings "
                "(line_user_id, channel_key, tenant_id, user_id, display_name, last_active_at) "
                "VALUES (%s, %s, %s, %s, %s, now()) "
                "ON CONFLICT (channel_key, line_user_id) DO UPDATE SET "
                "  id = gen_random_uuid(), bound_at = now(), "
                "  tenant_id = EXCLUDED.tenant_id, user_id = EXCLUDED.user_id, "
                "  display_name = EXCLUDED.display_name, last_active_at = now()",
                (line_user_id, key, str(tenant_id), str(user_id), display_name),
            )
            return True

    changed = bool(_dal("create_or_update_binding", False)(_run))
    if changed:
        from services.line_dms.menu_sync import request_sync

        for line_id, line_channel in set(old_lines) | {(line_user_id, key)}:
            request_sync(line_id, line_channel)
    return changed


def get_binding_by_line_user(
    line_user_id: str, channel_key: Optional[str] = None
) -> Optional[dict]:
    """按 (channel, LINE user) 反查绑定(webhook 入口用)。无 → None。

    channel_key 省略时不按 OA 过滤(旧调用/无 OA 上下文);webhook 必须传,否则同一个人
    在另一个 OA 的绑定可能被误匹配。
    """
    from core import db

    if not line_user_id:
        return None
    key = (channel_key or "").strip()

    def _run():
        with db.get_cursor() as cur:
            if key:
                cur.execute(
                    "SELECT id, channel_key, tenant_id, user_id, display_name, bound_at "
                    "FROM line_dms_bindings WHERE channel_key = %s AND line_user_id = %s LIMIT 1",
                    (key, line_user_id),
                )
            else:
                cur.execute(
                    "SELECT id, channel_key, tenant_id, user_id, display_name, bound_at "
                    "FROM line_dms_bindings WHERE line_user_id = %s LIMIT 1",
                    (line_user_id,),
                )
            return cur.fetchone()

    row = _dal("get_binding_by_line_user", None)(_run)
    return _binding_dict(row, line_user_id) if row else None


def get_binding_by_user(user_id: str) -> Optional[dict]:
    """按 Pearnly user 查绑定(App 侧「已绑?」用)。无 → None。"""
    from core import db
    from services.line_platform import channels as line_channels

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT id, line_user_id, channel_key, tenant_id, display_name, bound_at "
                "FROM line_dms_bindings WHERE user_id = %s LIMIT 1",
                (str(user_id),),
            )
            return cur.fetchone()

    row = _dal("get_binding_by_user", None)(_run)
    if not row:
        return None
    out = dict(row)
    out["channel_key"] = line_channels.normalize(out.get("channel_key"))
    return out


def unbind_by_user(user_id: str) -> bool:
    """Revoke the binding and its pending browser tickets and conversation together."""
    from core import db
    from services.line_dms import binding_state

    removed_lines = []

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                ("dms-binding-user:" + str(user_id),),
            )
            cur.execute(
                "SELECT line_user_id, channel_key FROM line_dms_bindings WHERE user_id=%s",
                (str(user_id),),
            )
            for row in cur.fetchall():
                removed_lines.append((row["line_user_id"], row["channel_key"]))
                binding_state.lock_line(cur, row["line_user_id"], row["channel_key"])
                binding_state.invalidate(cur, row["line_user_id"], user_id)
            cur.execute("DELETE FROM line_dms_bindings WHERE user_id = %s", (str(user_id),))
            return True

    changed = bool(_dal("unbind_by_user", False)(_run))
    if changed:
        from services.line_dms.menu_sync import request_sync

        for line_id, line_channel in removed_lines:
            request_sync(line_id, line_channel)
    return changed


def void_bind_codes_for_user(user_id: str) -> bool:
    """作废该 user 全部未用绑定码(停用操作员时的收权动作:在外流通的码即刻失效)。"""
    from core import db

    def _run():
        with db.get_cursor(commit=True) as cur:
            _void_unused_codes(cur, user_id)
            return True

    return bool(_dal("void_bind_codes_for_user", False)(_run))


def unbind_by_line_user(line_user_id: str, channel_key: Optional[str] = None) -> bool:
    """LINE 侧解绑(unfollow / 解绑命令)。返回是否真删到一行。"""
    from core import db
    from services.line_dms import binding_state
    from services.line_platform import channels as line_channels

    if not line_user_id:
        return False
    key = (channel_key or "").strip()

    def _run():
        with db.get_cursor(commit=True) as cur:
            binding_state.lock_scope(cur, line_user_id, key)
            if key:
                cur.execute(
                    "DELETE FROM line_dms_bindings "
                    "WHERE channel_key = %s AND line_user_id = %s "
                    "RETURNING user_id, channel_key",
                    (key, line_user_id),
                )
            else:
                cur.execute(
                    "DELETE FROM line_dms_bindings WHERE line_user_id = %s "
                    "RETURNING user_id, channel_key",
                    (line_user_id,),
                )
            row = cur.fetchone()
            if row:
                binding_state.invalidate(cur, line_user_id, row["user_id"])
            return row

    row = _dal("unbind_by_line_user", None)(_run)
    if not row:
        return False
    from services.line_dms.menu_sync import request_sync

    request_sync(line_user_id, line_channels.normalize(row.get("channel_key")))
    return True


def _binding_dict(row, line_user_id: str) -> dict:
    from services.line_platform import channels as line_channels

    out = dict(row)
    out["id"] = str(out["id"])
    out["line_user_id"] = line_user_id
    out["channel_key"] = line_channels.normalize(out.get("channel_key"))
    out["tenant_id"] = str(out["tenant_id"])
    out["user_id"] = str(out["user_id"])
    return out


# ── 会话态 ────────────────────────────────────────────────────────────────


DEFAULT_TTL_MINUTES = 30
# 会话寿命是状态的属性,不是调用点的参数。待选车/待确认订车这两个态里客户档已经落定,
# 会话是重签选车链接的唯一凭据 —— 它先于 15 分钟的面板 token 断掉,重发入口就等于不存在,
# 用户只剩重拍身份证一条路(真扣一次 OCR 费)。写在表里,免得哪个写会话的调用点漏传。
_STATE_TTL_MINUTES = {"picking": 120, "booking_review": 120, "booking_qa": 120}


def state_ttl_minutes(state: str) -> int:
    return _STATE_TTL_MINUTES.get(state, DEFAULT_TTL_MINUTES)


def verify_nonce(
    sess: Optional[dict], nonce: Optional[str], expect_state: str = "reviewing"
) -> bool:
    """只校验不消费的那半边守卫(consume_nonce 是校验+消费的孪生)。

    读操作(开编辑菜单/重拍/保留旧档)不该吃掉 nonce,但也不能没有守卫——判据只此一份,
    别再在各 handler 里就地手写状态与 nonce 比较。
    """
    payload = (sess or {}).get("payload") or {}
    return bool(
        sess and sess.get("state") == expect_state and nonce and payload.get("nonce") == nonce
    )


from services.line_dms.session_store import (  # noqa: E402,F401
    set_session,
    get_session,
    clear_session,
    consume_nonce,
    replace_review_payload,
)
