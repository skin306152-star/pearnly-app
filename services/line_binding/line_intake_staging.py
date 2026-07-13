# -*- coding: utf-8 -*-
"""LINE 收料暂存编排(LN-1):图片/文件消息 → 命中绑定上下文 → 落暂存池 + 四语确认。

排在 webhook 图片/文件分支最前:单聊只接「客户 contact 且非登录用户」的图(登录用户
发图仍走自己账本的 OCR 现状),群聊接已绑群任何成员的图。闸关/未绑定/一人挂多主体
歧义一律返 False 交回原路(fail-open 不挡主路,照 line_client_bind_intake 纪律)。

下载或落盘失败诚实不回「已收到」,落日志等客户重发——LINE 内容 API 偶发失败,回执
谎报会让料静默丢失;此时仍返 True(消息归本分支管,回落原路会对客户弹「请先绑定」
或把群图错进会计自己账本)。幂等锚 = client_intake_staging.line_message_id 唯一。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_BASE = os.environ.get("LINE_INTAKE_STORAGE_DIR", "/opt/mrpilot/storage/line_intake")

# bound_user 未传时的哨兵:分支内自查(None 是合法预查结果「已查无」,不能当未传)。
_SELF_RESOLVE = object()

# 收料确认回执四语(照 line_client_contact._BOUND_COPY 范式:客户侧措辞,独立小词表)。
_RECEIPT_COPY = {
    "th": "ได้รับเอกสารแล้วค่ะ ✅ จัดเก็บเข้าแฟ้มของ {client} เรียบร้อย",
    "en": "Got your document ✅ filed under {client}.",
    "zh": "收到票据 ✅ 已归入 {client}。",
    "ja": "書類を受け取りました ✅ {client} のファイルに保存しました。",
}


def receipt_text(lang: Optional[str], client_name: str) -> str:
    """收料确认回执(4 语 · th 兜底)。"""
    tpl = _RECEIPT_COPY.get(lang or "") or _RECEIPT_COPY["th"]
    return tpl.format(client=client_name)


async def try_stage_media(ev: dict, *, lang_hint: str = "th", bound_user=_SELF_RESOLVE) -> bool:
    """webhook 图片/文件分支入口。True=本分支已处理完(调用方 return);False=交回原路。

    to_thread:下载(阻塞 urllib)+ 同步 DB 不能卡 webhook 事件循环(照 line_expense 先例)。
    bound_user:调用方预查好的登录用户行(None=已查无),免单聊路二查同一 LINE 身份。
    """
    try:
        return await asyncio.to_thread(_stage_sync, ev, lang_hint, bound_user)
    except Exception:
        logger.warning("[line_intake_staging] 收料分支异常 · 回落原路", exc_info=True)
        return False


def _resolve_target(
    src: dict, line_user_id: Optional[str], bound_user=_SELF_RESOLVE
) -> Optional[tuple]:
    """发送上下文 → (归属行, 来源, 语言) 或 None(未命中绑定 → 交回原路)。

    群聊按 groupId 查已绑群(成员是谁不影响归属);单聊排除登录用户(他们的图是
    自己账本的 OCR 料),一人挂多主体时歧义不猜、回落原路。
    """
    from core import db
    from services.line_binding import line_client_contact, line_client_group

    if src.get("type") == "group":
        g = line_client_group.get_group(src.get("groupId"))
        return (g, "group", None) if g else None
    if not line_user_id:
        return None
    if bound_user is _SELF_RESOLVE:
        bound_user = db.get_user_by_line_user_id(line_user_id)
    if bound_user:
        return None
    contacts = line_client_contact.list_contacts_by_line_user(line_user_id)
    if len(contacts) != 1:
        if len(contacts) > 1:
            logger.info("[line_intake_staging] 单聊多主体歧义 · 回落原路 luid=%s", line_user_id)
        return None
    return (contacts[0], "dm", contacts[0].get("preferred_lang"))


def _save_to_disk(tenant_id: str, workspace_client_id, content: bytes, msg: dict) -> Optional[str]:
    """原件落盘 {BASE}/{tenant前8}/{client_id}/{uuid}{ext}(照 workorder/storage 布局惯例:
    租户段隔离 + uuid 名不可猜)。失败 → None(调用方诚实不回执)。"""
    try:
        ext = ".jpg"
        if msg.get("type") == "file":
            suffix = Path(str(msg.get("fileName") or "")).suffix.lower()
            ext = suffix if 2 <= len(suffix) <= 6 else ".bin"
        dest_dir = Path(_BASE) / str(tenant_id).replace("-", "")[:8] / str(int(workspace_client_id))
        dest_dir.mkdir(parents=True, exist_ok=True)
        path = dest_dir / f"{uuid.uuid4().hex}{ext}"
        path.write_bytes(content)
        return str(path)
    except Exception:
        logger.warning("[line_intake_staging] 落盘失败", exc_info=True)
        return None


def _discard_file(path: Optional[str]) -> None:
    """幂等撞行/插库失败时清掉刚落的盘件,不留无主孤儿(best-effort)。"""
    if not path:
        return
    try:
        os.remove(path)
    except OSError:
        pass


def _stage_sync(ev: dict, lang_hint: str, bound_user=_SELF_RESOLVE) -> bool:
    from core import feature_flags
    from services.line_binding import line_intake_store, line_reply

    msg = ev.get("message") or {}
    message_id = msg.get("id")
    src = ev.get("source") or {}
    line_user_id = src.get("userId")
    if not message_id:
        return False

    target = _resolve_target(src, line_user_id, bound_user)
    if not target:
        return False
    row, source, lang = target
    tenant_id = str(row["tenant_id"])
    ws_id = row["workspace_client_id"]
    if not feature_flags.pearnly_ai_line_intake_enabled_for(tenant_id):
        return False

    from services.line_binding import line_client

    content = line_client.download_message_content(message_id)
    if not content:
        logger.warning("[line_intake_staging] 下载失败 · 不回执等重发 mid=%s", message_id)
        return True
    file_path = _save_to_disk(tenant_id, ws_id, content, msg)
    if not file_path:
        return True

    inserted = line_intake_store.insert_staging(
        tenant_id,
        ws_id,
        line_message_id=message_id,
        file_path=file_path,
        sha256=hashlib.sha256(content).hexdigest(),
        source=source,
        sender_line_user_id=line_user_id,
        suggested_period=line_intake_store.latest_open_period(tenant_id, ws_id),
    )
    if inserted is not True:
        # False=redelivery 重投已在池(不双记不双回执)/ None=插库故障(诚实不回执)。
        _discard_file(file_path)
        if inserted is None:
            logger.warning("[line_intake_staging] 插池失败 · 不回执 mid=%s", message_id)
        return True

    reply_token = ev.get("replyToken")
    if reply_token:
        name = line_intake_store.client_display_name(tenant_id, ws_id)
        line_reply.reply_text_context(
            reply_token,
            receipt_text(lang or lang_hint, name or f"#{ws_id}"),
            quote_token=msg.get("quoteToken") or "",
            line_user_id=line_user_id or "",
            tenant_id=tenant_id,
        )
    return True
