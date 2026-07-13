# -*- coding: utf-8 -*-
"""客户 LINE 群绑定(LN-1 · 群聊收料形态)· 数据访问层 + 群侧四语文案。

一群只绑一个客户(line_group_id 是 PK):绑定后群内任何成员发的票据都算该客户的料
(方案 §2 双形态拍板)。同群再收别家绑定码 → 拒绝提示开新群,原码不消费(留给新群)。

webhook 判归属时还不知道 tenant,且「已属别家」必须跨租户可见才判得出冲突 → 读写都走
owner 连接按 group id 直查/条件 upsert(照 line_client_contact.list_contacts_by_line_user
先例;表仍启 RLS,租户上下文读取方照常受隔离)。建表范式照 line_client_contact 的首用
幂等自愈 + apply_tenant_rls,alembic 0074 双跑同一 DDL。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_TABLE_GROUPS = """
CREATE TABLE IF NOT EXISTS line_client_groups (
    line_group_id       text   PRIMARY KEY,
    tenant_id           uuid   NOT NULL,
    workspace_client_id bigint NOT NULL,
    bound_by_line_user  text,
    bound_at            timestamptz NOT NULL DEFAULT now()
)
"""

_INDEX_GROUPS_CLIENT = """
CREATE INDEX IF NOT EXISTS ix_line_client_groups_client
    ON line_client_groups (tenant_id, workspace_client_id)
"""

_TABLE_NAME = "line_client_groups"


def ensure_table() -> None:
    """幂等建表 + 索引 + RLS(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE_GROUPS)
        cur.execute(_INDEX_GROUPS_CLIENT)
        apply_tenant_rls(cur, _TABLE_NAME)


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方 fail-safe。"""
    try:
        return fn()
    except Exception as e:
        if _TABLE_NAME not in str(e):
            raise
        ensure_table()
        return fn()


def get_group(line_group_id: str) -> Optional[dict]:
    """按 group id 查绑定(webhook 归属判定 + 冲突预检,须跨租户可见故走 owner 连接)。"""
    from core import db

    if not line_group_id:
        return None

    def _run():
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT line_group_id, tenant_id, workspace_client_id, "
                "       bound_by_line_user, bound_at "
                "FROM line_client_groups WHERE line_group_id = %s",
                (line_group_id,),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_client_group] get_group failed", exc_info=True)
        return None


def bind_group(
    tenant_id, workspace_client_id, line_group_id: str, *, bound_by: Optional[str] = None
) -> Optional[str]:
    """群 ↔ 客户绑定。返回 'ok'(绑上/同客户刷新)/ 'conflict'(已属别家)/ None(故障)。

    单语句条件 upsert:PK 撞行时仅同 (tenant, client) 才允许刷新,别家行 WHERE 不中 →
    RETURNING 无行判 conflict——两码同刻竞绑同群也只有一家赢,不出双绑。
    """
    from core import db

    if not line_group_id:
        return None

    def _run():
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO line_client_groups "
                "(line_group_id, tenant_id, workspace_client_id, bound_by_line_user) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (line_group_id) DO UPDATE SET "
                "  bound_at = now(), bound_by_line_user = EXCLUDED.bound_by_line_user "
                "WHERE line_client_groups.tenant_id = EXCLUDED.tenant_id "
                "  AND line_client_groups.workspace_client_id = EXCLUDED.workspace_client_id "
                "RETURNING line_group_id",
                (line_group_id, str(tenant_id), workspace_client_id, bound_by),
            )
            row = cur.fetchone()
        return "ok" if row else "conflict"

    try:
        return _with_heal(_run)
    except Exception:
        logger.warning("[line_client_group] bind_group failed", exc_info=True)
        return None


# 群绑定回执四语(照 line_client_contact._BOUND_COPY 范式:客户侧措辞,独立小词表)。
_GROUP_BOUND_COPY = {
    "th": "เชื่อมต่อกลุ่มนี้กับ {client} เรียบร้อยแล้วค่ะ ส่งรูปบิลในกลุ่มนี้ได้เลย ระบบจะจัดเก็บให้อัตโนมัติ",
    "en": "This group is now linked to {client}. Send bill photos here and they will be filed automatically.",
    "zh": "本群已连接到 {client},在群里发票据照片即可自动归档。",
    "ja": "このグループを {client} に連携しました。請求書の写真を送るだけで自動的に整理されます。",
}

_GROUP_CONFLICT_COPY = {
    "th": "กลุ่มนี้เชื่อมต่อกับลูกค้ารายอื่นอยู่แล้วค่ะ หนึ่งกลุ่มต่อหนึ่งลูกค้า กรุณาเปิดกลุ่มใหม่แล้วส่งรหัสอีกครั้งนะคะ",
    "en": "This group is already linked to another client. One group per client - please open a new group and send the code there.",
    "zh": "这个群已绑定其他客户。一群一客户,请开个新群再发绑定码。",
    "ja": "このグループはすでに別のお客様と連携しています。1グループ1クライアントのため、新しいグループでコードを送り直してください。",
}


def group_bound_text(lang: Optional[str], client_name: str) -> str:
    """群绑定成功回执(4 语 · th 兜底)。"""
    tpl = _GROUP_BOUND_COPY.get(lang or "") or _GROUP_BOUND_COPY["th"]
    return tpl.format(client=client_name)


def group_conflict_text(lang: Optional[str]) -> str:
    """一群一客户拒绝提示(4 语 · th 兜底)。"""
    return _GROUP_CONFLICT_COPY.get(lang or "") or _GROUP_CONFLICT_COPY["th"]
