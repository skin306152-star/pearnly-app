# -*- coding: utf-8 -*-
"""LINE 批量撤销(撤最近 N 笔 / 今天全部)· 破坏性 → 先确认卡再执行。

范围判定走本模块 detect_bulk_undo(明确数量 N 或「全部」才进批量·裸「取消」不进)。
确认卡列出要撤的几笔 + 笔数 + 合计 + 一次性 nonce(防重放)→ 用户点确认才撤。执行口径复用现有
确定性引擎:草稿 delete_doc、已入账 void_doc(已结期内部红冲;无开放期 PosError → 诚实跳过计数,
绝不破账)。每笔独立事务 → 一笔跳过不回滚其余。
"""

from __future__ import annotations

import logging
import re
from decimal import Decimal

from core import db
from services.line_binding import line_card_sections as s
from services.line_binding import line_postback, line_reply

logger = logging.getLogger(__name__)

# ── 范围判定:撤销动词须搭【明确范围】才进批量流;裸「取消/算了」「撤上一笔」仍归单条/改错取消 ──
_BULK_VERBS = (
    "撤",
    "撤销",
    "取消",
    "删",
    "删除",
    "清空",
    "清掉",
    "清空掉",
    "ยกเลิก",
    "ลบ",
    "ถอน",
    "เคลียร์",
    "cancel",
    "delete",
    "remove",
    "undo",
    "clear",
)
_BULK_ALL = ("全部", "所有", "全清", "ทั้งหมด", "วันนี้ทั้งหมด", "all", "everything")
# 独立全清短语(本身即明确的「清今天全部」命令·无需另带动词)。
_BULK_ALL_STANDALONE = (
    "今天全部",
    "今天所有",
    "清空今天",
    "清空今日",
    "清空全部",
    "全部取消",
    "取消全部",
)
_NUM_WORDS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "หนึ่ง": 1,
    "สอง": 2,
    "สาม": 3,
    "สี่": 4,
    "ห้า": 5,
    "หก": 6,
    "เจ็ด": 7,
    "แปด": 8,
    "เก้า": 9,
    "สิบ": 10,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}
_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
# 数量须搭量词/「最近/刚发」语境才算笔数 → 防「取消7-11买的咖啡」里的店号数字被当笔数。
_BULK_COUNT_CTX = (
    "笔",
    "条",
    "张",
    "项",
    "最近",
    "刚发",
    "刚才",
    "刚刚",
    "上面",
    "รายการ",
    "ล่าสุด",
    "เมื่อกี้",
    "last",
    "recent",
    "entries",
    "records",
    "transactions",
)


def _bulk_count(low: str):
    """文本里的撤销笔数:阿拉伯/泰文数字优先,否则中/泰/英数字词。无 → None。"""
    m = re.search(r"\d+", low.translate(_THAI_DIGITS))
    if m:
        try:
            return int(m.group(0))
        except ValueError:
            return None
    for word, n in _NUM_WORDS.items():
        if word in low:
            return n
    return None


def detect_bulk_undo(text: str) -> dict | None:
    """批量撤销范围:{"scope":"all"} / {"scope":"count","n":N}。撤销动词 + 明确范围才命中;否则 None。

    「全部取消/今天全部/清空今天」→ all;「撤最近3笔/取消刚发的三条/cancel last 3」→ count/3。
    裸「取消/算了」「撤上一笔」(无数量/无全部)→ None,仍交单条撤销 / 改错取消流。
    """
    low = (text or "").strip().lower()
    if not low:
        return None
    if any(p in low for p in _BULK_ALL_STANDALONE):
        return {"scope": "all"}
    if not any(v in low for v in _BULK_VERBS):
        return None
    if any(a in low for a in _BULK_ALL):
        return {"scope": "all"}
    if any(c in low for c in _BULK_COUNT_CTX):
        n = _bulk_count(low)
        if n and n >= 2:
            return {"scope": "count", "n": n}
    return None


_REF_PREFIX = "bulkundo:"
_LIST_CAP = 5
_TODAY_LIMIT = 200  # 「全部」上限(防极端·实际一天 LINE 记录远不及)

_T = {
    "zh": {
        "confirm_title": "确认撤销",
        "confirm_desc": "将撤销以下 {n} 笔记录,确认吗?",
        "summary": "共 {n} 笔 · 合计 ฿{amount}",
        "more": "还有 {m} 笔…",
        "btn_confirm": "确认撤销 {n} 笔",
        "btn_cancel": "不用了",
        "done_title": "已撤销",
        "done_desc": "已撤销 {n} 笔 · 合计 ฿{amount}",
        "skipped": "{m} 笔已结期,未撤(不破账)",
        "nothing": "今天没有可撤销的记录哦~ 发笔费用我帮你记?",
        "cancelled": "好的,没有撤销任何记录😊",
        "stale": "这张确认卡已失效,请重新说一次要撤几笔",
    },
    "th": {
        "confirm_title": "ยืนยันการยกเลิก",
        "confirm_desc": "จะยกเลิก {n} รายการต่อไปนี้ ยืนยันไหมคะ?",
        "summary": "รวม {n} รายการ · ฿{amount}",
        "more": "และอีก {m} รายการ…",
        "btn_confirm": "ยืนยันยกเลิก {n} รายการ",
        "btn_cancel": "ไม่ใช่",
        "done_title": "ยกเลิกแล้ว",
        "done_desc": "ยกเลิกแล้ว {n} รายการ · รวม ฿{amount}",
        "skipped": "{m} รายการอยู่ในงวดที่ปิดแล้ว ไม่ได้ยกเลิก (ไม่กระทบบัญชี)",
        "nothing": "วันนี้ยังไม่มีรายการให้ยกเลิกค่ะ~ ส่งค่าใช้จ่ายมาบันทึกได้นะคะ",
        "cancelled": "ได้ค่ะ ไม่ได้ยกเลิกอะไรค่ะ😊",
        "stale": "การ์ดยืนยันนี้หมดอายุแล้ว กรุณาบอกใหม่ว่าต้องการยกเลิกกี่รายการค่ะ",
    },
    "en": {
        "confirm_title": "Confirm cancellation",
        "confirm_desc": "This will undo the following {n} record(s). Confirm?",
        "summary": "{n} record(s) · ฿{amount} total",
        "more": "and {m} more…",
        "btn_confirm": "Undo {n} record(s)",
        "btn_cancel": "No, keep them",
        "done_title": "Undone",
        "done_desc": "Undone {n} record(s) · ฿{amount} total",
        "skipped": "{m} in a closed period, kept (books untouched)",
        "nothing": "Nothing to undo today~ send me an expense to log?",
        "cancelled": "Okay, nothing was undone 😊",
        "stale": "This confirmation expired — tell me again how many to undo",
    },
    "ja": {
        "confirm_title": "取り消しの確認",
        "confirm_desc": "以下の {n} 件を取り消します。よろしいですか?",
        "summary": "計 {n} 件 · ฿{amount}",
        "more": "ほか {m} 件…",
        "btn_confirm": "{n} 件を取り消す",
        "btn_cancel": "やめておく",
        "done_title": "取り消しました",
        "done_desc": "{n} 件を取り消しました · 計 ฿{amount}",
        "skipped": "{m} 件は締め済み期間のため取り消していません(帳簿は変更なし)",
        "nothing": "今日は取り消せる記録がありません~ 経費を送ってください?",
        "cancelled": "了解です、何も取り消していません😊",
        "stale": "この確認カードは期限切れです。もう一度件数を教えてください",
    },
}


def _t(lang):
    return _T.get((lang or "zh").lower(), _T["zh"])


def _money(x) -> str:
    try:
        return f"{Decimal(str(x or 0)):,.2f}"
    except Exception:  # noqa: BLE001
        return "0.00"


def _doc_line(d) -> str:
    """一笔简列:日期 · 卖家 · ฿金额。"""
    date = str(d.get("doc_date") or "").strip()
    vendor = str(d.get("supplier_name") or "").strip()
    head = " · ".join(p for p in (date, vendor) if p)
    return (
        f"{head} · ฿{_money(d.get('grand_total'))}" if head else f"฿{_money(d.get('grand_total'))}"
    )


def _banner(icon, title, desc, *, bg, title_color) -> dict:
    """卡头条:彩色徽章标题 + 灰色说明(确认卡/汇总卡共用)。"""
    return {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "14px",
        "paddingStart": "20px",
        "backgroundColor": bg,
        "contents": [
            s.txt(f"{icon} {title}", size="sm", color=title_color, weight="bold", wrap=True),
            s.txt(desc, size="xxs", color="#475467", margin="xs", wrap=True),
        ],
    }


def _doc_rows(docs, t) -> list:
    """逐笔简列(cap _LIST_CAP)+ 「还有 M 笔…」溢出行(两卡共用)。"""
    rows = [
        s.txt(f"• {_doc_line(d)}", size="xxs", color="#475467", wrap=True) for d in docs[:_LIST_CAP]
    ]
    if len(docs) > _LIST_CAP:
        rows.append(s.txt(t["more"].format(m=len(docs) - _LIST_CAP), size="xxs", color="#98A2B3"))
    return rows


def _bubble(alt, header, rows, footer=None) -> dict:
    """组装 mega bubble → flex(出口剔空 text 节点)。footer 非空才带动作区。"""
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": header,
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "16px",
            "spacing": "sm",
            "contents": rows or [s.txt("—", size="xxs", color="#98A2B3")],
        },
    }
    if footer:
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "12px",
            "contents": footer,
        }
    return s.prune_empty_text({"type": "flex", "altText": alt, "contents": bubble})


def route(bound_user, reply_token, line_user_id, text, lang, tid, ws, ctx) -> bool:
    """批量撤销入口(改错流最前):命中明确范围 → 查单 + 出确认卡。无范围 → False(交单条流)。"""
    scope = detect_bulk_undo(text)
    if not scope:
        return False
    t = _t(lang)
    from services.purchase import line_docs

    with db.get_cursor_rls(tid, commit=True) as cur:
        if scope["scope"] == "all":
            docs = line_docs.find_today_line_docs(cur, tenant_id=tid, workspace_client_id=ws)
        else:
            docs = line_docs.find_recent_line_docs(
                cur, tenant_id=tid, workspace_client_id=ws, limit=min(scope["n"], _TODAY_LIMIT)
            )
        if not docs:
            _say(reply_token, t["nothing"], ctx)
            return True
        ids = ",".join(str(d["id"]) for d in docs)
        from services.line_binding import line_action_nonce as nonce

        token = nonce.mint(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            action_ref=f"{_REF_PREFIX}{ids}",
            user_id=line_user_id,
        )
    card = _confirm_card(docs, token, lang)
    line_reply.reply_messages_context(
        reply_token,
        [card],
        line_user_id=line_user_id,
        tenant_id=tid,
        quote_token=ctx.get("quote_token", ""),
    )
    return True


def _say(reply_token, body, ctx) -> None:
    line_reply.reply_text_context(reply_token, body, **ctx)


def _confirm_card(docs, token, lang) -> dict:
    """批量撤销确认卡:列前 N 笔(cap 5)+ 笔数/合计 + [确认撤销 N 笔]/[不用了]。"""
    t = _t(lang)
    n = len(docs)
    total = sum(Decimal(str(d.get("grand_total") or 0)) for d in docs)
    rows = _doc_rows(docs, t)
    rows.append(
        s.txt(
            t["summary"].format(n=n, amount=_money(total)),
            size="sm",
            color="#111827",
            weight="bold",
            margin="md",
        )
    )
    header = _banner(
        "⚠", t["confirm_title"], t["confirm_desc"].format(n=n), bg="#FEF3E2", title_color="#B45309"
    )
    footer = [
        s.btn(
            t["btn_confirm"].format(n=n),
            primary=True,
            postback=line_postback.bulk_undo_data(token),
            danger=True,
        ),
        s.btn(t["btn_cancel"], primary=False, postback=line_postback.bulk_cancel_data(token)),
    ]
    return _bubble(f"{t['confirm_title']} · {n}", header, rows, footer)


def _summary_card(undone, skipped, lang) -> dict:
    """撤完汇总终态卡:已撤 N 笔 + 合计 + 逐笔简列 + 跳过(已结期)诚实说明。"""
    t = _t(lang)
    n = len(undone)
    total = sum(Decimal(str(d.get("grand_total") or 0)) for d in undone)
    header = _banner(
        "↩",
        t["done_title"],
        t["done_desc"].format(n=n, amount=_money(total)),
        bg="#F2F4F7",
        title_color="#667085",
    )
    rows = _doc_rows(undone, t)
    if skipped:
        rows.append(
            s.txt(
                t["skipped"].format(m=skipped), size="xxs", color="#B45309", margin="md", wrap=True
            )
        )
    return _bubble(f"{t['done_title']} · {n}", header, rows)


def handle_postback(bound_user, reply_token, action, token, lang) -> None:
    """批量撤销 postback:确认 → 逐笔撤 + 汇总卡;取消 → 作废令牌 + 友好回执。绝不抛(主路径不崩)。"""
    tid = str(bound_user["tenant_id"]) if bound_user.get("tenant_id") else None
    luid = bound_user.get("line_user_id") or ""
    t = _t(lang)
    if not tid:
        return
    try:
        from services.line_binding import line_action_nonce as nonce

        with db.get_cursor_rls(tid, commit=True) as cur:
            res = nonce.consume(cur, tenant_id=tid, token=token)
        if action == line_postback.ACTION_BULK_CANCEL:
            line_reply.reply_text_context(
                reply_token, t["cancelled"], line_user_id=luid, tenant_id=tid
            )
            return
        if res["status"] != "ok":
            # 重放/过期/伪造 → 不重复撤(令牌已消费),友好提示。
            line_reply.reply_text_context(reply_token, t["stale"], line_user_id=luid, tenant_id=tid)
            return
        ws = res["workspace_client_id"]
        ref = res.get("action_ref") or ""
        ids = (
            [x for x in ref[len(_REF_PREFIX) :].split(",") if x]
            if ref.startswith(_REF_PREFIX)
            else []
        )
        undone, skipped = _execute(bound_user, tid, ws, ids)
        card = _summary_card(undone, skipped, lang)
        line_reply.reply_messages_context(reply_token, [card], line_user_id=luid, tenant_id=tid)
    except Exception:  # noqa: BLE001 — 批量撤销失败不崩主路径
        logger.warning("[line bulk undo] postback failed", exc_info=True)
        line_reply.reply_text_context(reply_token, t["stale"], line_user_id=luid, tenant_id=tid)


def _execute(bound_user, tid, ws, doc_ids) -> tuple[list, int]:
    """逐笔撤(各自独立事务):draft→delete,posted→void(已结期内部红冲;PosError→跳过计数)。

    返回 (已撤单详情列表, 已结期跳过数)。一笔异常只跳过该笔,不影响其余(per-doc commit)。
    """
    from core.pos_api import PosError
    from services.purchase import correct as correct_svc
    from services.purchase import docs as docs_svc
    from services.purchase import posting as posting_svc

    uid = str(bound_user["id"]) if bound_user.get("id") else None
    undone, skipped = [], 0
    for did in doc_ids:
        try:
            with db.get_cursor_rls(tid, commit=True) as cur:
                detail = docs_svc.get_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=did)
                doc = (detail or {}).get("doc") or {}
                status = doc.get("status")
                if status == "draft":
                    correct_svc.discard_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=did)
                    undone.append(doc)
                elif status == "posted":
                    posting_svc.void_doc(
                        cur, tenant_id=tid, workspace_client_id=ws, doc_id=did, created_by=uid
                    )
                    undone.append(doc)
                # 其它(已 void/已删/不存在)→ 静默跳过(不计入跳过提示·非已结期)
        except PosError as e:
            if (e.code or "").startswith("acct."):  # 已结期/无开放期 → 诚实跳过,不破账
                skipped += 1
                continue
            logger.warning("[line bulk undo] void %s failed: %s", did, e.code)
        except Exception:  # noqa: BLE001 — 单笔异常不拖垮整批
            logger.warning("[line bulk undo] doc %s failed", did, exc_info=True)
    return undone, skipped
