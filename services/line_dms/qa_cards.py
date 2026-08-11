# -*- coding: utf-8 -*-
"""DMS LINE 订车逐问(DL-7 · batch 1/3)的 Flex 卡与泰语文案(纯函数,零副作用)。

booking_qa 状态机的每步「发问」在这里出消息 dict(文本 + quickReply 结构 + 预览 Flex 卡)。
文案是业主逐条确认的定稿,集中在本文件顶部常量区,测试按此断言。按钮一律 postback,
data 用 "qa:<action>[:<value>]" 编码;预览卡的确认/取消复用 cards.ACT_* 常量与 _data
编码(flow 侧 parse_qs 解析,既有 booking_flow 的确认/取消直接接得上)。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from services.erp.erp_dms_push import _DMS_FRIENDLY
from services.line_dms.cards import (
    ACT_CANCEL_BOOKING,
    ACT_CONFIRM_BOOKING,
    TXT_NO_ENDPOINT,
    _bubble,
    _btn,
    _data,
    _kv_row,
    _qr_item,
)
from services.line_dms.qa_util import CHANNEL_EXTRA_SHAPE
from services.line_dms.qa_util import car_label as _car_label
from services.line_dms.qa_util import row_name as _name

# ── 文案(业主逐条确认 · 逐字不改) ─────────────────────────────────────────
TXT_ASK_SLIP = (
    "ส่งสลิปโอนเงินจอง (ใบโอนเงิน) ได้เลยครับ · ถ้าลูกค้าจ่ายเงินสด พิมพ์ เงินสด เพื่อข้ามขั้นนี้"
)
TXT_ASK_PLACE = "ข้อ 2/8 · สถานที่รับจอง — กดเลือกด้านล่าง"
TXT_ASK_CAR = "ข้อ 3/8 · รุ่นรถ — พิมพ์ชื่อรุ่นสั้น ๆ เพื่อค้นหา เช่น dmax"
TXT_CAR_PICK = "เลือกรุ่นรถ (พบ {n} รายการ)"
TXT_CAR_NONE = "ไม่พบรุ่นที่ตรง ลองพิมพ์ใหม่อีกครั้ง"
TXT_CAR_MANY = "พบ {n} รายการ พิมพ์ให้เจาะจงขึ้นอีกนิดครับ"
TXT_ASK_PAINT = "เลือกสีของ {car}"
TXT_PAINT_MANY = "มีสีมากกว่านี้ พิมพ์ชื่อสีเพื่อค้นหาได้"
TXT_ASK_DATE = "ข้อ 4/8 · วันที่คาดว่าจะส่งมอบรถ — กดปุ่มเพื่อเลือกวันที่"
BTN_PICK_DATE = "เลือกวันที่"
TXT_ASK_TERM = "ข้อ 5/8 · เงื่อนไขการขาย — กดเลือกด้านล่าง"
TXT_ASK_REGIS = "ข้อ 6/8 · จดทะเบียนในนาม — กดเลือกด้านล่าง"
TXT_ASK_REGIS_NAME = "ข้อ 7/8 · ชื่อผู้จดทะเบียน — กดปุ่มใช้ชื่อตามบัตร หรือพิมพ์ชื่ออื่น"
BTN_REGIS_NAME_CARD = "ใช้ชื่อตามบัตร"
TXT_ASK_PAY_CHANNEL = "ข้อ 8/8 · ช่องทางชำระเงินจอง — เลือกช่องทาง"
PAY_LABELS = {
    "cash": "เงินสด",
    "transfer": "เงินโอน",
    "cheque": "เช็ค",
    "cashier_cheque": "แคชเชียร์เช็ค",
    "card": "บัตรเครดิต/เดบิต",
    "other": "อื่นๆ",
}
TXT_ASK_AMOUNT = "ยอดเงิน ({channel}) — พิมพ์จำนวนเงิน เช่น 5000"
TXT_BAD_AMOUNT = "จำนวนเงินไม่ถูกต้อง พิมพ์เป็นตัวเลข เช่น 5000 หรือ 5,000.50"
TXT_ASK_PAY_SRC = "บัญชีต้นทาง (ธนาคาร + เลขบัญชี) — พิมพ์ หรือพิมพ์ - เพื่อข้าม"
TXT_ASK_PAY_DST = "บัญชีปลายทาง (บัญชีบริษัท) — พิมพ์ หรือพิมพ์ - เพื่อข้าม"
TXT_ASK_CHEQUE_REF = "เลขที่เช็ค + ธนาคาร — พิมพ์"
TXT_ASK_CARD_REF = "ธนาคาร/ประเภทบัตร — พิมพ์"
TXT_ASK_OTHER_REF = "รายละเอียดช่องทาง — พิมพ์"
TXT_ASK_MORE = "มีช่องทางอื่นอีกไหม"
BTN_MORE_DONE = "ครบแล้ว"
BTN_MORE_ADD = "เพิ่มช่องทาง"
TXT_NEED_SLIP = "มีช่องทางเงินโอน กรุณาส่งสลิปโอนเงินก่อนดูสรุปครับ"
TXT_PREVIEW_TITLE = "สรุปใบจอง — ตรวจสอบก่อนยืนยัน"
BTN_CONFIRM = "ยืนยัน"
BTN_DISCARD = "ทิ้ง"
TXT_SLIP_ONLY_IMAGE = "ขั้นนี้ต้องการรูปสลิปครับ ส่งเป็นรูปภาพ หรือพิมพ์ เงินสด ถ้าไม่มีการโอน"
# 逐问/确认态收到的非本步文本或图片,不覆写会话、不推 OCR——只说继续点卡(接线层用)。
TXT_CONFIRM_ABOVE = "กด ยืนยัน หรือ ทิ้ง ที่สรุปด้านบนครับ"
TXT_NO_IMAGE_NEEDED = "ขั้นตอนนี้ไม่ต้องการรูปภาพครับ ทำตามคำถามด้านบนได้เลย"
# 建单成功但附件没挂全时的诚实追加行(不谎报附件成功)。
TXT_ATTACH_FAIL = "แนบไฟล์ไม่ครบ กรุณาแนบเพิ่มในระบบ DMS"
# 开局闸:DMS 账号对不上顾问名册就开不了单(提成没人认)。告诉销售哪个账号出错、谁能修。
# 补救指引与错误码目录同一份泰语原文 —— 同一件事在 LINE 与主 UI 上说法漂了,用户会以为
# 是两个毛病。会话语气(ครับ / 账号名)只加在前缀,不改目录原文。
_TH_ADVISOR_UNMATCHED = _DMS_FRIENDLY["ERR_DMS_ADVISOR_UNMATCHED"]["th"]
_TH_RETRY = " แล้วลองใหม่อีกครั้ง"
TXT_ADVISOR_BLOCK = (
    "ยังเปิดใบจองไม่ได้ครับ · บัญชี DMS ที่ใช้อยู่คือ «{username}»\n"
    + _TH_ADVISOR_UNMATCHED
    + _TH_RETRY
)
TXT_ADVISOR_BLOCK_NO_USER = (
    "ยังเปิดใบจองไม่ได้ครับ · ระบบยังอ่านบัญชี DMS ของผู้ใช้นี้ไม่ได้\n"
    + _TH_ADVISOR_UNMATCHED
    + _TH_RETRY
)

# 预览卡行标签(与确认后建单要回显的字段一一对应)。
LBL_CUSTOMER = "ลูกค้า"
LBL_ADVISOR = "ที่ปรึกษาการขาย"
LBL_PLACE = "สถานที่รับจอง"
LBL_CAR = "รุ่น/สี"
LBL_DELIVERY = "วันส่งมอบ"
LBL_TERM = "เงื่อนไขการขาย"
LBL_REGIS = "จดทะเบียนในนาม"
LBL_TOTAL = "ยอดเงินจองรวม"
LBL_ATTACH_CARD = "สำเนาบัตรประชาชน"
LBL_ATTACH_SLIP = "ใบโอนเงินจอง"
VAL_ATTACHED = "แนบแล้ว"

_MAX_BTN = 20  # quick reply 按钮标签截断(display 宽度)
_MAX_PAINT_BTNS = 12  # 颜色超过则只列前 12 个,余下可打字匹配


def _msg(text: str, items: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """文本消息 + 可选 quickReply;无按钮时不出空 items(LINE 会拒)。"""
    msg: Dict[str, Any] = {"type": "text", "text": text}
    if items:
        msg["quickReply"] = {"items": items}
    return msg


def _pick_rows(rows: List[list], action: str, label_fn) -> List[Dict[str, Any]]:
    """主档按钮列表:data="qa:<action>:<id>",label 截 20 字符。"""
    return [
        _qr_item(label_fn(r)[:_MAX_BTN], f"qa:{action}:{r[0]}")
        for r in rows or []
        if r and r[0] is not None
    ]


def _plus_years(d: date, years: int) -> date:
    """跨闰日安全加整年(datetimepicker 的 max 用)。"""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d + timedelta(days=365 * years)


# ── 开局闸 ───────────────────────────────────────────────────────────────
def no_endpoint() -> Dict[str, Any]:
    """端点没配/被停用 → 沿用全站同一句无端点话术。"""
    return _msg(TXT_NO_ENDPOINT)


def advisor_block_msg(username: str) -> Dict[str, Any]:
    """顾问认不出 → 说清哪个账号、谁能修、修完重试;连账号都解不出时退通用版。"""
    username = (username or "").strip()
    if not username:
        return _msg(TXT_ADVISOR_BLOCK_NO_USER)
    return _msg(TXT_ADVISOR_BLOCK.format(username=username))


# ── 各步发问 ─────────────────────────────────────────────────────────────
def ask_slip() -> Dict[str, Any]:
    """第 1 问:送转账凭证;现金可打字 เงินสด 跳过。"""
    return _msg(TXT_ASK_SLIP)


def slip_only_image() -> Dict[str, Any]:
    """slip 步收到无法解析的文本时的重发提示。"""
    return _msg(TXT_SLIP_ONLY_IMAGE)


def ask_place(place_books: List[list]) -> Dict[str, Any]:
    """第 2 问:สถานที่รับจอง 按钮(place_books 主档)。"""
    return _msg(TXT_ASK_PLACE, _pick_rows(place_books, "place", _name))


def ask_car() -> Dict[str, Any]:
    """第 3 问:打字搜车型。"""
    return _msg(TXT_ASK_CAR)


def car_results(rows: List[list], n: int) -> Dict[str, Any]:
    """车型命中 1-10 条:按钮列出(data="qa:car:<id>")。"""
    return _msg(TXT_CAR_PICK.format(n=n), _pick_rows(rows, "car", _car_label))


def car_none() -> Dict[str, Any]:
    return _msg(TXT_CAR_NONE)


def car_many(n: int) -> Dict[str, Any]:
    return _msg(TXT_CAR_MANY.format(n=n))


def ask_paint(car_label: str, paints: List[list]) -> Dict[str, Any]:
    """第 4 问(顺序表里的 paint):选颜色。>12 色只列前 12 个 + 打字提示。"""
    text = TXT_ASK_PAINT.format(car=car_label)
    if len(paints or []) > _MAX_PAINT_BTNS:
        text = f"{text}\n{TXT_PAINT_MANY}"
    return _msg(text, _pick_rows(paints[:_MAX_PAINT_BTNS], "paint", _name))


def ask_date(today: date) -> Dict[str, Any]:
    """第 5 问(顺序表里的 date):LINE datetimepicker· initial=+7 天,min=今天,max=+2 年。"""
    action = {
        "type": "datetimepicker",
        "label": BTN_PICK_DATE,
        "data": "qa:date",
        "mode": "date",
        "initial": (today + timedelta(days=7)).isoformat(),
        "min": today.isoformat(),
        "max": _plus_years(today, 2).isoformat(),
    }
    return _msg(TXT_ASK_DATE, [{"type": "action", "action": action}])


def ask_term(term_sales: List[list]) -> Dict[str, Any]:
    """第 6 问:เงื่อนไขการขาย 按钮(term_sales 主档)。"""
    return _msg(TXT_ASK_TERM, _pick_rows(term_sales, "term", _name))


def ask_regis(regis_behalfs: List[list]) -> Dict[str, Any]:
    """第 7 问:จดทะเบียนในนาม 按钮(regis_behalfs 主档)。"""
    return _msg(TXT_ASK_REGIS, _pick_rows(regis_behalfs, "regis", _name))


def ask_regis_name() -> Dict[str, Any]:
    """第 8 问:登记人姓名,一个按钮用客户档姓名。"""
    return _msg(TXT_ASK_REGIS_NAME, [_qr_item(BTN_REGIS_NAME_CARD, "qa:regisname:card")])


def ask_pay_channel() -> Dict[str, Any]:
    """支付渠道六按钮(固定顺序照业主确认的 PAY_LABELS)。"""
    return _msg(
        TXT_ASK_PAY_CHANNEL, [_qr_item(label, f"qa:pay:{ch}") for ch, label in PAY_LABELS.items()]
    )


def ask_amount(channel_label: str) -> Dict[str, Any]:
    return _msg(TXT_ASK_AMOUNT.format(channel=channel_label))


def bad_amount() -> Dict[str, Any]:
    return _msg(TXT_BAD_AMOUNT)


def ask_pay_src() -> Dict[str, Any]:
    return _msg(TXT_ASK_PAY_SRC)


def ask_pay_dst() -> Dict[str, Any]:
    return _msg(TXT_ASK_PAY_DST)


def ask_pay_ref(channel: str) -> Dict[str, Any]:
    """渠道补充信息文案:分类查 CHANNEL_EXTRA_SHAPE 单表,不再各处硬编码渠道子集。"""
    shape = CHANNEL_EXTRA_SHAPE.get(channel)
    if shape == "ref":
        return _msg(TXT_ASK_CARD_REF if channel == "card" else TXT_ASK_CHEQUE_REF)
    return _msg(TXT_ASK_OTHER_REF)


def ask_more() -> Dict[str, Any]:
    """支付循环出口:ครบแล้ว / เพิ่มช่องทาง。"""
    return _msg(
        TXT_ASK_MORE,
        [_qr_item(BTN_MORE_DONE, "qa:more:done"), _qr_item(BTN_MORE_ADD, "qa:more:add")],
    )


def need_slip() -> Dict[str, Any]:
    """pay_more 收尾时发现转账渠道没凭证 → 补要(或 slip_after 步重发)。"""
    return _msg(TXT_NEED_SLIP)


# ── 预览汇总卡 ────────────────────────────────────────────────────────────
def deposit_total(payments: List[Dict[str, Any]]) -> Decimal:
    """各渠道金额 Decimal 求和(金额一律 Decimal,不用 float)。"""
    return sum((Decimal(str(p.get("amount") or "0")) for p in payments or []), Decimal("0"))


def _car_paint_line(answers: Dict[str, Any]) -> str:
    car = str((answers.get("car") or {}).get("label") or "")
    paint = str((answers.get("paint") or {}).get("name") or "")
    return " · ".join(p for p in (car, paint) if p) or "—"


def _regis_line(answers: Dict[str, Any]) -> str:
    regis = str((answers.get("regis") or {}).get("name") or "")
    name = str(answers.get("regis_name") or "")
    if regis and name:
        return f"{regis} · {name}"
    return regis or name or "—"


def preview_card(qa: Dict[str, Any], nonce: str) -> Dict[str, Any]:
    """逐问结束的汇总卡:全部答案 + 各渠道金额 + 合计 + 附件两行 + 确认/丢弃。

    按钮复用 ACT_CONFIRM_BOOKING / ACT_CANCEL_BOOKING 与 _data 编码,既有 booking_flow
    的确认/取消(parse_qs + consume_nonce)无需任何改动即可接住。
    """
    answers = qa.get("answers") or {}
    files = qa.get("files") or {}
    payments = qa.get("payments") or []
    advisor = str((qa.get("advisor") or {}).get("name") or "")
    rows: List[Dict[str, Any]] = [
        _kv_row(LBL_CUSTOMER, str((qa.get("customer") or {}).get("name") or "")),
        # 顾问 = 提成归属,确认前让销售自己看一眼落在谁头上;没匹配上时开局就拦了,不会到这。
        *([_kv_row(LBL_ADVISOR, advisor)] if advisor else []),
        _kv_row(LBL_PLACE, str((answers.get("place") or {}).get("name") or "")),
        _kv_row(LBL_CAR, _car_paint_line(answers)),
        _kv_row(LBL_DELIVERY, str(answers.get("delivery_date_be") or "")),
        _kv_row(LBL_TERM, str((answers.get("term") or {}).get("name") or "")),
        _kv_row(LBL_REGIS, _regis_line(answers)),
    ]
    for p in payments:
        label = PAY_LABELS.get(p.get("channel") or "", p.get("channel") or "")
        rows.append(_kv_row(label, str(p.get("amount") or "")))
    rows.append(_kv_row(LBL_TOTAL, f"{deposit_total(payments):,.2f}"))
    rows.append({"type": "separator", "margin": "sm"})
    rows.append(_kv_row(LBL_ATTACH_CARD, VAL_ATTACHED if files.get("id_card_mid") else "—"))
    rows.append(_kv_row(LBL_ATTACH_SLIP, VAL_ATTACHED if files.get("slip_mid") else "—"))
    footer = [
        _btn(BTN_CONFIRM, _data(ACT_CONFIRM_BOOKING, nonce=nonce), "primary"),
        _btn(BTN_DISCARD, _data(ACT_CANCEL_BOOKING), "secondary"),
    ]
    return _bubble(TXT_PREVIEW_TITLE, rows, footer, TXT_PREVIEW_TITLE)
