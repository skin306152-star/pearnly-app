# -*- coding: utf-8 -*-
"""成文失败时的诚实兜底文案 —— 从工具真实观测拼一句话(绝不编数字)。

模型两次不肯成文时的最后一道:拿已取到的工具结果给诚实回复,而不是把已查到的查询
掉回旧路念"这笔多少钱"。计数型(list_history/list_notifications)走 zero/some;
值型(balance/history_summary/usage_this_month)展示真实数字;未覆盖工具 → None(交入口安全兜底)。
"""

from __future__ import annotations

from typing import Optional

# 计数型工具的四语兜底(zero/some · {n} 为数量)。只覆盖搜索/通知——旧路 has_item_context
# 会把这两类的成文失败误路成"问价格";其它工具的查询兜底不误路,罕见失败交旧路即可。
_FALLBACK = {
    "list_history": {
        "zero": {
            "th": "ไม่พบเอกสารที่ตรงกับคำค้นครับ",
            "zh": "没有找到相关单据。",
            "en": "No matching receipts found.",
            "ja": "該当する書類は見つかりませんでした。",
        },
        "some": {
            "th": "พบเอกสารที่ตรงกับคำค้น {n} รายการ",
            "zh": "找到 {n} 条相关单据。",
            "en": "Found {n} matching receipts.",
            "ja": "{n}件見つかりました。",
        },
    },
    "list_notifications": {
        "zero": {
            "th": "ไม่มีแจ้งเตือนใหม่ครับ",
            "zh": "目前没有新通知。",
            "en": "No new notifications.",
            "ja": "新しい通知はありません。",
        },
        "some": {
            "th": "มีแจ้งเตือน {n} รายการ",
            "zh": "有 {n} 条通知。",
            "en": "{n} notifications.",
            "ja": "通知が{n}件あります。",
        },
    },
}
_FALLBACK_COUNT_KEY = {"list_history": "total", "list_notifications": "count"}

# 值型只读工具的兜底(展示真实数字·非计数)。套账导航(list/switch_workspace)低风险 → 不兜底,交安全兜底。
_FB_BALANCE = {
    "th": "ยอดเครดิตคงเหลือ ฿{v} ครับ",
    "zh": "你的余额是 ฿{v}。",
    "en": "Your balance is ฿{v}.",
    "ja": "残高は฿{v}です。",
}
_FB_SUMMARY = {
    "th": "เดือนนี้บันทึกไป {n} รายการ รวม ฿{v} ครับ",
    "zh": "本月记录 {n} 单,合计 ฿{v}。",
    "en": "This month: {n} documents, ฿{v} total.",
    "ja": "今月は{n}件、合計฿{v}です。",
}
_FB_USAGE = {
    "th": "เดือนนี้ใช้ไป {p} หน้าครับ",
    "zh": "本月已用 {p} 页。",
    "en": "You've used {p} pages this month.",
    "ja": "今月は{p}ページ使いました。",
}


def _fb_money(v) -> str:
    try:
        return f"{float(v or 0):,.0f}"
    except (TypeError, ValueError):
        return "0"


def _fb_int(v) -> int:
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


_FB_PLAN = {
    "th": "ตอนนี้ใช้แพ็กเกจ {plan} ค่ะ",
    "zh": "你当前的套餐是 {plan}。",
    "en": "Your current plan is {plan}.",
    "ja": "現在のプランは {plan} です。",
}
_FB_RD = {
    "th": "เลข {tax_id}: {name}",
    "zh": "税号 {tax_id}:{name}",
    "en": "Tax ID {tax_id}: {name}",
    "ja": "納税者番号 {tax_id}:{name}",
}

# 推送状态是布尔分叉(推了/没推),单模板装不下 → 独立两态表。状态诚实:failed 走 no。
_FB_PUSH = {
    "yes": {
        "th": "ใบนี้ส่งเข้า {e} แล้วค่ะ",
        "zh": "这张已推进 {e}。",
        "en": "This document was pushed to {e}.",
        "ja": "この伝票は {e} へ送信済みです。",
    },
    "no": {
        "th": "ใบนี้ยังไม่ได้ส่งเข้า ERP ค่ะ",
        "zh": "这张还没推进 ERP。",
        "en": "This document has not been pushed to ERP yet.",
        "ja": "この伝票はまだ ERP へ送信されていません。",
    },
}

# 对账两态(有结果/还没跑过)。detail 的"哪些对不上"细行交模型;兜底只给诚实计数。
_FB_RECON = {
    "some": {
        "th": "กระทบยอดล่าสุด: ตรงกัน {m} รายการ ไม่ตรง {u} รายการค่ะ",
        "zh": "最近一次对账:一致 {m} 笔,不一致 {u} 笔。",
        "en": "Latest reconciliation: {m} matched, {u} unmatched.",
        "ja": "最新の照合:一致 {m} 件、不一致 {u} 件です。",
    },
    "zero": {
        "th": "ยังไม่มีผลกระทบยอดค่ะ ลองอัปโหลดที่เมนูกระทบยอดธนาคารบนเว็บก่อนนะคะ",
        "zh": "还没有对账记录,先到网页「银行对账」上传跑一次。",
        "en": "No reconciliation runs yet — upload files under Bank Reconciliation on the web first.",
        "ja": "まだ照合結果がありません。ウェブの「銀行照合」で先に実行してください。",
    },
}


def _recon_fb(tool: str, o: dict, lang: str) -> str:
    if tool == "recon_overview":
        # 三档形状:bank→income→tax 取第一个有任务的档(条目已带归一 matched/unmatched)。
        t = next(
            (
                ((o.get(k) or {}).get("recent") or [None])[0]
                for k in ("bank", "income", "tax")
                if ((o.get(k) or {}).get("recent") or [None])[0]
            ),
            None,
        )
    else:
        t = o.get("task")
    if not t:
        msgs = _FB_RECON["zero"]
        return msgs.get(lang, msgs["en"])
    from services.agent.copy_map import _recon_unmatched  # 归一口径单一定义点

    msgs = _FB_RECON["some"]
    return msgs.get(lang, msgs["en"]).format(m=_fb_int(t.get("matched")), u=_recon_unmatched(t))


# 值型只读工具:tool → (四语模板, 从观测取模板槽位的函数)。加一个值型工具 = 加一行,不再加 if 分支。
_VALUE_FB = {
    "balance": (_FB_BALANCE, lambda o: {"v": _fb_money(o.get("balance_thb"))}),
    "history_summary": (
        _FB_SUMMARY,
        lambda o: {"n": _fb_int(o.get("doc_count")), "v": _fb_money(o.get("amount_total"))},
    ),
    "usage_this_month": (_FB_USAGE, lambda o: {"p": _fb_int(o.get("pages_used_this_month"))}),
    "my_plan": (_FB_PLAN, lambda o: {"plan": str(o.get("plan") or "")}),
    "rd_lookup": (
        _FB_RD,
        lambda o: {"tax_id": str(o.get("tax_id") or ""), "name": str(o.get("name") or "")},
    ),
}


def grounded_fallback(observations: list, lang: str) -> Optional[str]:
    """成文失败的最后兜底:从最后一个工具观测取真实数字拼一句诚实话(绝不编)。
    计数型走 _FALLBACK(zero/some),值型走 _VALUE_FB;套账导航未覆盖 → None → 交入口安全兜底。"""
    last = observations[-1] if observations else {}
    tool = last.get("tool")
    if not last.get("ok"):
        return None  # 失败观测绝不格式化成自信数字(零命中≠查询失败)→ 交安全兜底
    table = _FALLBACK.get(tool)
    if table:  # 计数型(list_history / list_notifications)
        n = _fb_int(last.get(_FALLBACK_COUNT_KEY[tool]))
        msgs = table["some" if n else "zero"]
        return msgs.get(lang, msgs["en"]).format(n=n)
    if tool == "push_status":
        msgs = _FB_PUSH["yes" if last.get("pushed") else "no"]
        return msgs.get(lang, msgs["en"]).format(e=str(last.get("endpoint") or "ERP"))
    if tool in ("recon_overview", "recon_detail"):
        return _recon_fb(tool, last, lang)
    spec = _VALUE_FB.get(tool)  # 值型(balance / history_summary / usage / my_plan / rd)
    if spec:
        msgs, extract = spec
        return msgs.get(lang, msgs["en"]).format(**extract(last))
    return None
