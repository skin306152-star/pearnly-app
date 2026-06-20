# -*- coding: utf-8 -*-
"""LINE「本月凭证 PDF」命令(Phase C-1):识别命令 + 解析期间 → 即回 ack → 异步打包 → 推下载卡。

诚实边界:0 笔已入账 → 不生成、回「本月还没已入账」;生成失败 → 回「稍后再试」(不静默)。重 CPU
(fitz 合并多图)走 asyncio.to_thread,不卡事件循环。下载链接=时效签名 token(proof_pdf.sign_token)。
"""

from __future__ import annotations

import asyncio
import calendar
import logging
import os
from datetime import date
from decimal import Decimal

from core import db
from core.workspace_context import default_workspace_id
from services.export import archive, proof_pdf
from services.line_binding import line_client, line_reply
from services.ocr import pdf_storage
from services.purchase import reports as reports_svc

logger = logging.getLogger(__name__)

# 触发词(命中任一即「取本月凭证 PDF」)。精确短语·不误触正常记账/查账。
_TRIGGERS = (
    "ขอ pdf",
    "รวมใบเสร็จ",
    "ส่งหลักฐาน",
    "หลักฐานเดือน",
    "本月凭证",
    "导出凭证",
    "凭证pdf",
    "凭证 pdf",
    "凭证打包",
    "打包凭证",
    "proof pdf",
    "export proof",
    "monthly proof",
)
_LAST_MONTH = ("เดือนที่แล้ว", "เดือนก่อน", "上月", "上个月", "上一个月", "last month")

_MSG = {
    "ack": {
        "zh": "正在为你打包本月凭证,稍后把下载链接发给你 📎",
        "th": "กำลังรวมหลักฐานเดือนนี้ให้ค่ะ เดี๋ยวส่งลิงก์ให้ 📎",
        "en": "Packing this month's proof bundle — I'll send you the link shortly 📎",
        "ja": "今月の証憑をまとめています。リンクを後ほどお送りします 📎",
    },
    "empty": {
        "zh": "这个期间还没有已入账的记录,无法打包凭证。",
        "th": "ช่วงนี้ยังไม่มีรายการที่บันทึกแล้วค่ะ จึงยังรวมหลักฐานไม่ได้",
        "en": "No posted entries for this period yet — nothing to bundle.",
        "ja": "この期間に記帳済みの記録がないため、まとめられません。",
    },
    "fail": {
        "zh": "凭证打包生成失败,请稍后再试。",
        "th": "รวมหลักฐานไม่สำเร็จ กรุณาลองใหม่อีกครั้งค่ะ",
        "en": "Couldn't build the proof bundle — please try again later.",
        "ja": "証憑のまとめに失敗しました。後ほど再度お試しください。",
    },
    "card_title": {
        "zh": "凭证 {period} · {n} 笔 · ฿{total}",
        "th": "หลักฐานเดือน {period} · {n} รายการ · ฿{total}",
        "en": "Proof {period} · {n} entries · ฿{total}",
        "ja": "証憑 {period} · {n} 件 · ฿{total}",
    },
    "btn": {
        "zh": "下载 PDF",
        "th": "ดาวน์โหลด PDF",
        "en": "Download PDF",
        "ja": "PDF ダウンロード",
    },
}


def _m(key: str, lang: str, **kw) -> str:
    pool = _MSG[key]
    return (pool.get((lang or "th").lower()) or pool["th"]).format(**kw)


def _month_range(today: date, back: int = 0) -> tuple:
    """(today, back) → (date_from, date_to, 'YYYY-MM')。back=0 本月·1 上月。"""
    y, mo = today.year, today.month - back
    while mo <= 0:
        mo += 12
        y -= 1
    last = calendar.monthrange(y, mo)[1]
    return (date(y, mo, 1).isoformat(), date(y, mo, last).isoformat(), f"{y}-{mo:02d}")


def parse_proof_command(text: str, today: date = None):
    """命中凭证命令 → {date_from,date_to,period};否则 None。默认本月·含上月词 → 上月。"""
    low = (text or "").lower().strip()
    if not any(k in low for k in _TRIGGERS):
        return None
    f, t, label = _month_range(
        today or date.today(), 1 if any(k in low for k in _LAST_MONTH) else 0
    )
    return {"date_from": f, "date_to": t, "period": label}


def _base_url() -> str:
    return (os.environ.get("PEARNLY_BASE_URL") or "https://pearnly.com").rstrip("/")


def _download_card(result: dict, lang: str) -> dict:
    """下载卡(template buttons·按钮 URI 直开签名链接)。"""
    title = _m(
        "card_title",
        lang,
        period=result["period"],
        n=result["n"],
        total=f"{Decimal(str(result['total'] or 0)):,.2f}",
    )
    return {
        "type": "template",
        "altText": title,
        "template": {
            "type": "buttons",
            "text": title[:160],
            "actions": [{"type": "uri", "label": _m("btn", lang)[:20], "uri": result["url"]}],
        },
    }


def start(bound_user, reply_token, line_user_id, lang, cmd) -> bool:
    """命中命令:0 笔 → 回提示不生成;有笔 → 回 ack + 异步打包推卡。返回 True(已处理)。"""
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    if not tid:
        return False
    with db.get_cursor_rls(tid, commit=False) as cur:
        ws = default_workspace_id(cur, tid)
        doc_ids = (
            archive._posted_doc_ids(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                date_from=cmd["date_from"],
                date_to=cmd["date_to"],
            )
            if ws is not None
            else []
        )
    if not doc_ids:
        line_reply.reply_text_context(
            reply_token, _m("empty", lang), line_user_id=line_user_id, tenant_id=tid
        )
        return True
    line_reply.reply_text_context(
        reply_token, _m("ack", lang), line_user_id=line_user_id, tenant_id=tid
    )
    asyncio.create_task(_run_and_push(tid, ws, line_user_id, lang, cmd))
    return True


def _build_and_save(tid, ws, line_user_id, lang, cmd) -> dict:
    """同步:建 PDF + 落盘 + 签 token + 汇总(在线程池跑·不卡事件循环)。失败抛异常。"""
    with db.get_cursor_rls(tid, commit=False) as cur:
        pdf = proof_pdf.build_monthly_proof_pdf(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            date_from=cmd["date_from"],
            date_to=cmd["date_to"],
            lang=lang,
            period=cmd["period"],
        )
        summ = reports_svc.summary(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            date_from=cmd["date_from"],
            date_to=cmd["date_to"],
        )
    rel, _size = pdf_storage.save_bytes(line_user_id, pdf, ".pdf")
    if not rel:
        raise RuntimeError("save_bytes failed")
    token = proof_pdf.sign_token(
        tenant_id=tid, workspace_client_id=ws, period=cmd["period"], rel=rel
    )
    total = (summ.get("goods_total") or 0) + (summ.get("expense_total") or 0)
    return {
        "url": f"{_base_url()}/api/purchase/proof-pdf/{token}",
        "n": summ.get("doc_count") or 0,
        "total": total,
        "period": cmd["period"],
    }


async def _run_and_push(tid, ws, line_user_id, lang, cmd) -> None:
    """异步编排:线程池建包 → 推下载卡;失败 → 诚实推「稍后再试」。"""
    try:
        result = await asyncio.to_thread(_build_and_save, tid, ws, line_user_id, lang, cmd)
        line_client.push_messages(line_user_id, [_download_card(result, lang)])
    except Exception:  # noqa: BLE001
        logger.warning("[line proof] build/push failed", exc_info=True)
        line_client.push_messages(line_user_id, [{"type": "text", "text": _m("fail", lang)}])
