# -*- coding: utf-8 -*-
"""对账 job 终态 → LINE 回推(收件流 params.notify 指定目标时才发 · 2026-07-03)。

worker._run_one 的 finally 调进来;任何故障吞掉只记日志——通知是锦上添花,
绝不许影响 job 本体/暂存清理。文案确定性四语;done 尽量带真实计数
(读结果 store,读不到就发不带数字的完成句,绝不编)。
"""

from __future__ import annotations

import logging

logger = logging.getLogger("mr-pilot")

_DONE = {
    "th": "✅ กระทบยอดเสร็จแล้วค่ะ: ตรงกัน {m} รายการ ไม่ตรง {u} รายการ · ถาม 'รายการไหนไม่ตรง' ต่อได้เลย",
    "zh": "✅ 对账好了:一致 {m} 笔,不一致 {u} 笔·想看明细就问「哪些对不上」。",
    "en": "✅ Reconciliation done: {m} matched, {u} unmatched · ask 'which ones differ' for details.",
    "ja": "✅ 照合完了:一致 {m} 件、不一致 {u} 件 · 明細は「どれが不一致?」と聞いてください。",
}
_DONE_PLAIN = {
    "th": "✅ กระทบยอดเสร็จแล้วค่ะ ถามผลกับฉันหรือดูบนเว็บได้เลย",
    "zh": "✅ 对账好了,可以直接问我结果,或到网页查看。",
    "en": "✅ Reconciliation finished — ask me for the results or view them on the web.",
    "ja": "✅ 照合が完了しました。結果は私に聞くかウェブでご確認ください。",
}
_FAILED = {
    "th": "❌ กระทบยอดไม่สำเร็จค่ะ ({code}) ลองใหม่หรือทำบนเว็บนะคะ",
    "zh": "❌ 对账没跑成({code}),请再试一次或到网页跑。",
    "en": "❌ Reconciliation failed ({code}) — try again or run it on the web.",
    "ja": "❌ 照合に失敗しました({code})。再試行するかウェブでお試しください。",
}
_NEEDS_WEB = {
    "th": "⏸️ กระทบยอดต้องยืนยันบางอย่างบนเว็บก่อนค่ะ (เมนูกระทบยอดธนาคาร) แล้วระบบจะทำต่อให้",
    "zh": "⏸️ 这次对账需要到网页「银行对账」里确认几处(读数核对/列对应),确认后会继续跑完。",
    "en": "⏸️ This run needs a quick confirmation on the web (Bank Reconciliation) before it can finish.",
    "ja": "⏸️ 今回はウェブの「銀行照合」で確認が必要です。確認後に続行されます。",
}


def _t(table: dict, lang: str) -> str:
    return table.get(lang, table["en"])


def _done_text(job: dict, result_table, result_id, lang: str) -> str:
    """结果计数:按 result_table 读对应 store;读不到发不带数字的完成句(绝不编)。"""
    try:
        params = job.get("params") or {}
        uid = str(params.get("user_id") or job.get("user_id") or "")
        tid = params.get("tenant_id") or job.get("tenant_id")
        m = u = None
        if result_table == "bank_recon_v2_task" and result_id is not None:
            from services.recon.bank_recon_v2_store import get_bank_recon_v2_task

            t = get_bank_recon_v2_task(int(result_id), uid, tid) or {}
            m = int(t.get("matched_count") or 0)
            u = int(t.get("unmatched_gl") or 0) + int(t.get("unmatched_stmt") or 0)
        elif result_table == "gl_vat_task" and result_id is not None:
            from services.recon.gl_vat_store import get_gl_vat_task

            t = get_gl_vat_task(int(result_id), uid, tid) or {}
            m = int(t.get("matched_count") or 0)
            u = int(t.get("unmatched_count") or 0) + int(t.get("diff_count") or 0)
        elif result_table == "vat_recon_tasks" and result_id:
            from services.recon.vat_recon_tasks_store import get_vat_recon_task

            t = get_vat_recon_task(str(result_id), tid, uid) or {}
            m = int(t.get("matched") or 0)
            u = int(t.get("mismatched") or 0)
        if m is not None:
            return _t(_DONE, lang).format(m=m, u=u)
    except Exception:
        logger.warning("[recon-notify] result read failed; plain done text", exc_info=True)
    return _t(_DONE_PLAIN, lang)


def notify_terminal(job: dict, *, status, result_table=None, result_id=None, error_code=None):
    """job 终态回推。没有 notify 目标(网页起的任务)= 无动作。"""
    params = (job or {}).get("params") or {}
    target = params.get("notify") or {}
    line_user_id = target.get("line_user_id")
    if not line_user_id:
        return
    lang = target.get("lang") or "th"
    tid = job.get("tenant_id")
    if status == "done":
        text = _done_text(job, result_table, result_id, lang)
    elif status in ("needs_review", "needs_mapping"):
        text = _t(_NEEDS_WEB, lang)
    else:
        text = _t(_FAILED, lang).format(code=str(error_code or "error")[:60])
    from services.line_binding import line_reply

    line_reply.push_text_context(line_user_id, text, tenant_id=str(tid) if tid else None)
    logger.info("[recon-notify] job %s -> line %s (%s)", job.get("id"), line_user_id[:8], status)
