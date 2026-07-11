# -*- coding: utf-8 -*-
"""客户 LINE 联系人 · 客户绑定码(D2 方案 §1.2 / §2.2)· 数据访问层。

workspace_client(会计的客户业主)↔ LINE user 的映射——line_bindings 绑的是 Pearnly 登录
用户(会计自己),客户不是登录用户、无 users 行,一 LINE 可能挂多主体,硬塞会污染
「谁是真用户」与 RLS 口径(方案 §1.2)。建表范式照 line_pending_actions.py 的首用幂等
自愈 + apply_tenant_rls。

绑定流程:会计在客户档案页生成 6 位邀请码(与 line_binding_codes 同长度,靠码表区分)→
客户加 Bot 好友、发码 → webhook 认出这是客户绑定码 → 落 line_client_contacts。邀请码表
按方案 §2.2 DDL 原样无 used_at 列:单发单用靠 DELETE ... RETURNING 原子消费(与
line_pending_actions.take_action 同一范式),消费即删,不留已用行占位。
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_CODE_TTL_MINUTES = 10

_TABLE_CONTACTS = """
CREATE TABLE IF NOT EXISTS line_client_contacts (
    tenant_id           uuid   NOT NULL,
    workspace_client_id bigint NOT NULL,
    line_user_id        text   NOT NULL,
    preferred_lang      text   NOT NULL DEFAULT 'th',
    display_name        text,
    bound_at            timestamptz NOT NULL DEFAULT now(),
    last_active_at      timestamptz,
    PRIMARY KEY (tenant_id, workspace_client_id)
)
"""

_INDEX_CONTACTS_LUID = """
CREATE INDEX IF NOT EXISTS ix_line_client_contacts_luid
    ON line_client_contacts (line_user_id)
"""

_TABLE_BIND_CODES = """
CREATE TABLE IF NOT EXISTS line_client_bind_codes (
    code                text   PRIMARY KEY,
    tenant_id           uuid   NOT NULL,
    workspace_client_id bigint NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    expires_at          timestamptz NOT NULL
)
"""

_TABLES = ("line_client_contacts", "line_client_bind_codes")


def ensure_table() -> None:
    """幂等建两张表 + 索引 + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE_CONTACTS)
        cur.execute(_INDEX_CONTACTS_LUID)
        cur.execute(_TABLE_BIND_CODES)
        apply_tenant_rls(cur, *_TABLES)


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方 fail-safe。"""
    try:
        return fn()
    except Exception as e:
        msg = str(e)
        if not any(t in msg for t in _TABLES):
            raise
        ensure_table()
        return fn()


def generate_client_bind_code(
    tenant_id, workspace_client_id, *, ttl_minutes: int = DEFAULT_CODE_TTL_MINUTES
) -> Optional[dict]:
    """会计在客户档案页点「连客户 LINE」生成邀请码。同客户重复生成先作废旧码再发新码。"""
    from core import db

    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "DELETE FROM line_client_bind_codes "
                "WHERE tenant_id = %s AND workspace_client_id = %s",
                (str(tenant_id), workspace_client_id),
            )
            cur.execute(
                "INSERT INTO line_client_bind_codes "
                "(code, tenant_id, workspace_client_id, expires_at) "
                "VALUES (%s, %s, %s, %s) "
                "RETURNING code, expires_at",
                (code, str(tenant_id), workspace_client_id, expires_at),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {"code": row["code"], "expires_at": row["expires_at"].isoformat()}

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_client_contact] generate_client_bind_code failed", exc_info=True)
        return None


def _valid_code(code: str) -> str:
    code = (code or "").strip()
    return code if code and len(code) == 6 and code.isdigit() else ""


def peek_client_bind_code(code: str) -> Optional[dict]:
    """只读查码归属(tenant_id/workspace_client_id),不消费——闸判定要先知道 tenant 才能
    问 pearnly_ai_client_pool_enabled_for,真消费动作留到闸确认开了才做(闸关时绝不误耗
    这个一次性码)。过期/不存在 → None。"""
    from core import db

    code = _valid_code(code)
    if not code:
        return None

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT tenant_id, workspace_client_id FROM line_client_bind_codes "
                "WHERE code = %s AND expires_at > now()",
                (code,),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_client_contact] peek_client_bind_code failed", exc_info=True)
        return None


def consume_client_bind_code(code: str) -> Optional[dict]:
    """原子消费(DELETE ... RETURNING · 单发单用,过期行同删不返)。"""
    from core import db

    code = _valid_code(code)
    if not code:
        return None

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM line_client_bind_codes "
                "WHERE code = %s AND expires_at > now() "
                "RETURNING tenant_id, workspace_client_id",
                (code,),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_client_contact] consume_client_bind_code failed", exc_info=True)
        return None


def bind_contact(
    tenant_id,
    workspace_client_id,
    line_user_id: str,
    *,
    display_name: Optional[str] = None,
    preferred_lang: str = "th",
) -> bool:
    """落客户 LINE 联系人(upsert:重发码换绑覆盖旧行)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id), commit=True) as cur:
            cur.execute(
                "INSERT INTO line_client_contacts "
                "(tenant_id, workspace_client_id, line_user_id, preferred_lang, "
                " display_name, last_active_at) "
                "VALUES (%s, %s, %s, %s, %s, now()) "
                "ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE SET "
                "  line_user_id = EXCLUDED.line_user_id, "
                "  preferred_lang = EXCLUDED.preferred_lang, "
                "  display_name = EXCLUDED.display_name, "
                "  last_active_at = now()",
                (str(tenant_id), workspace_client_id, line_user_id, preferred_lang, display_name),
            )
        return True

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_client_contact] bind_contact failed", exc_info=True)
        return False


def get_contact(tenant_id, workspace_client_id) -> Optional[dict]:
    """查某客户当前的 LINE 联系人。跨 tenant 传错 tenant_id 查不到(RLS + 本 WHERE 双证)。"""
    from core import db

    def _run():
        with db.get_cursor_rls(str(tenant_id)) as cur:
            cur.execute(
                "SELECT tenant_id, workspace_client_id, line_user_id, preferred_lang, "
                "       display_name, bound_at, last_active_at "
                "FROM line_client_contacts "
                "WHERE tenant_id = %s AND workspace_client_id = %s",
                (str(tenant_id), workspace_client_id),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_client_contact] get_contact failed", exc_info=True)
        return None


def list_contacts_by_line_user(line_user_id: str) -> list:
    """反查该 sender 名下所有客户联系人(§4.3 回答拦截消歧用:一个业主可能挂多主体)。
    webhook 尚未知道 tenant → 走 owner 连接读全表按 line_user_id 过滤;调用方按行自带的
    tenant_id 各自建 RLS 上下文做后续写操作,读侧本身不代表放弃隔离。"""
    from core import db

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT tenant_id, workspace_client_id, line_user_id, preferred_lang, "
                "       display_name, bound_at, last_active_at "
                "FROM line_client_contacts "
                "WHERE line_user_id = %s",
                (line_user_id,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_client_contact] list_contacts_by_line_user failed", exc_info=True)
        return []


# 客户绑定成功回执(四语·极简)。独立小词表,不并进 line_bind_i18n——那本文件是「用会计软件
# 的人」的绑定文案,客户绑定是另一身份维度,措辞对象不同,混进一张表会绕晕维护者(§1.2)。
_BOUND_COPY = {
    "th": "เชื่อมต่อ LINE เรียบร้อยแล้วค่ะ ต่อไปนักบัญชีจะส่งคำถามเกี่ยวกับบิลมาทาง LINE นี้ได้เลย",
    "en": "Your LINE is now connected. Your accountant can send bill questions here.",
    "zh": "LINE 已连接。之后会计有票据问题会通过这个 LINE 发给你。",
    "ja": "LINEの連携が完了しました。今後、会計担当者が請求書に関する質問をこちらに送ります。",
}


def client_bound_text(lang: Optional[str]) -> str:
    """客户绑定成功回执文案(4 语 · th 兜底)。"""
    return _BOUND_COPY.get(lang or "") or _BOUND_COPY["th"]
