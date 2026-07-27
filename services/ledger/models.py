# -*- coding: utf-8 -*-
"""销售票的输入契约:OCR/回导给的松散 dict → 账簿配方吃的确定性结构。

归一放在这里一处,是因为同一张票的字段在仓里有三种来源(OCR 的 ThaiInvoice、回导解析器、
汇总表导入),键名各不相同。各配方各写一套取值就会漂;要漂只在这个文件里漂。

钱一律 Decimal:0.07 在 float 里不是精确的 0.07,而这些数字要进 ภ.พ.30。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Mapping, Optional, Sequence, Tuple

from services.excel.erp_money import to_money
from services.knowledge.rules.validity import parse_invoice_date
from services.sales_agg.vat import split_gross

# 结算去向 —— 决定分录借哪个科目。空 = 票面没印,不许猜。
SETTLE_CASH = "cash"
SETTLE_BANK = "bank"

# 票面付款方式原词(OCR 按 services/ocr/layer2_prompts 读的是 cash|transfer|qr|card)→ 结算去向。
# card 故意不在表里:coa_preset 没有信用卡清算户科目,硬塞进银行就是记错账,该进待判。
_SETTLEMENT_BY_METHOD = {
    "cash": SETTLE_CASH,
    "เงินสด": SETTLE_CASH,
    "现金": SETTLE_CASH,
    "transfer": SETTLE_BANK,
    "bank": SETTLE_BANK,
    "bank_transfer": SETTLE_BANK,
    "bank transfer": SETTLE_BANK,
    "โอน": SETTLE_BANK,
    "โอนเงิน": SETTLE_BANK,
    "qr": SETTLE_BANK,
    "promptpay": SETTLE_BANK,
    "prompt_pay": SETTLE_BANK,
}

REASON_NO_DATE = "ไม่พบวันที่ในเอกสาร · ต้องระบุวันที่ก่อนลงบัญชี"
REASON_CROSS_MONTH = "เวลาเข้า-ออกคาบเกี่ยวข้ามเดือน · ต้องยืนยันวันที่ของใบกำกับ"
REASON_NO_SETTLEMENT = "ไม่ระบุวิธีชำระเงินบนเอกสาร · ระบุไม่ได้ว่าเป็นเงินสดหรือเงินโอน"
REASON_TOTAL_MISMATCH = "ยอดรวมบนเอกสารไม่ตรงกับผลรวมรายการสินค้า"
REASON_NO_LINES = "ไม่พบรายการสินค้าในเอกสาร"

DATE_FROM_PRINTED = "printed"
DATE_FROM_TIME_OUT = "time_out"
DATE_FROM_TIME_IN = "time_in"

ZERO = Decimal("0")


def _s(v: Any) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("none", "null", "nan") else s


def _pick(fields: Mapping[str, Any], *keys: str) -> Any:
    for k in keys:
        v = fields.get(k)
        if v not in (None, ""):
            return v
    return None


def settlement_of(payment_method: Any) -> str:
    """票面付款方式 → 结算去向。认不出返回空串 —— 空串是「不知道」,不是「现金」。"""
    return _SETTLEMENT_BY_METHOD.get(_s(payment_method).lower(), "")


@dataclass(frozen=True)
class DocDate:
    """票面日期裁决结果。source 说明这个日期是从哪一格读出来的,便于事后追。"""

    value: Optional[date]
    source: str
    pending_reason: str


def resolve_doc_date(fields: Mapping[str, Any]) -> DocDate:
    """票面日期口径(硬规则,不交给模型):

    1. 有独立的 Date / วันที่ → 用它,不看 in/out。
    2. 只有 Time in / Time out → 用 **out**(ABB 的纳税义务发生时点是收款/开票,不是进店)。
    3. in 与 out 跨月 → 该票进待判:跨月会把销项挪到上一期申报,这必须人拍板。
    """
    printed = parse_invoice_date(_s(_pick(fields, "date", "invoice_date", "doc_date")))
    if printed:
        return DocDate(printed, DATE_FROM_PRINTED, "")

    time_in = parse_invoice_date(_s(_pick(fields, "time_in", "timein")))
    time_out = parse_invoice_date(_s(_pick(fields, "time_out", "timeout")))
    if time_in and time_out and (time_in.year, time_in.month) != (time_out.year, time_out.month):
        return DocDate(time_out, DATE_FROM_TIME_OUT, REASON_CROSS_MONTH)
    if time_out:
        return DocDate(time_out, DATE_FROM_TIME_OUT, "")
    if time_in:
        # 只有入座时刻:它是唯一的datum,用它但标明来源,不假装是开票时刻。
        return DocDate(time_in, DATE_FROM_TIME_IN, "")
    return DocDate(None, "", REASON_NO_DATE)


@dataclass(frozen=True)
class SalesLine:
    """一个商品行。amount 是票面印的行金额;unit_price 缺失时表里写死值不写公式。"""

    description: str
    qty: Decimal
    unit_price: Optional[Decimal]
    amount: Decimal


@dataclass(frozen=True)
class SalesDoc:
    """一张销售票。gross/vat/net 全部由行金额派生,内含 VAT 口径 gross × 7/107。"""

    invoice_number: str
    doc_date: Optional[date]
    date_source: str
    customer_name: str
    customer_tax_id: str
    settlement: str
    payment_method_raw: str
    lines: Tuple[SalesLine, ...]
    row_key: str
    pending_reason: str

    @property
    def gross(self) -> Decimal:
        return sum((ln.amount for ln in self.lines), ZERO)

    @property
    def vat(self) -> Decimal:
        return split_gross(self.gross)[1]

    @property
    def net(self) -> Decimal:
        return split_gross(self.gross)[0]

    @property
    def bookable(self) -> bool:
        return not self.pending_reason


def _line_from(raw: Mapping[str, Any]) -> Optional[SalesLine]:
    amount = to_money(_pick(raw, "subtotal", "amount", "line_total", "total"))
    qty = to_money(_pick(raw, "qty", "quantity")) or Decimal("1")
    price = to_money(_pick(raw, "price", "unit_price"))
    if amount is None:
        if price is None:
            return None
        amount = (qty * price).quantize(Decimal("0.01"))
    description = _s(_pick(raw, "name", "description", "item_name"))
    return SalesLine(description=description, qty=qty, unit_price=price, amount=amount)


def _pending_reason(
    lines: Sequence[SalesLine], doc_date: DocDate, settlement: str, printed_total: Optional[Decimal]
) -> str:
    """待判原因 —— 只报第一条,报一串会让会计不知道先修哪个。"""
    if not lines:
        return REASON_NO_LINES
    if doc_date.pending_reason:
        return doc_date.pending_reason
    if not settlement:
        return REASON_NO_SETTLEMENT
    total = sum((ln.amount for ln in lines), ZERO)
    if printed_total is not None and printed_total != total:
        return f"{REASON_TOTAL_MISMATCH} ({printed_total} ≠ {total})"
    return ""


def parse_sales_doc(fields: Mapping[str, Any], *, row_key: str = "") -> SalesDoc:
    """一张票的松散字段 → SalesDoc。缺了什么如实落 pending_reason,不补默认值蒙混。"""
    raw_lines = fields.get("items") or fields.get("lines") or []
    lines = tuple(ln for ln in (_line_from(r or {}) for r in raw_lines) if ln is not None)
    doc_date = resolve_doc_date(fields)
    method_raw = _s(_pick(fields, "payment_method", "payment"))
    settlement = settlement_of(method_raw)
    printed_total = to_money(_pick(fields, "total_amount", "total"))
    return SalesDoc(
        invoice_number=_s(_pick(fields, "invoice_number", "invoice_no", "doc_number")),
        doc_date=doc_date.value,
        date_source=doc_date.source,
        customer_name=_s(_pick(fields, "buyer_name", "customer_name")),
        customer_tax_id=_s(_pick(fields, "buyer_tax", "buyer_tax_id", "customer_tax_id")),
        settlement=settlement,
        payment_method_raw=method_raw,
        lines=lines,
        row_key=row_key,
        pending_reason=_pending_reason(lines, doc_date, settlement, printed_total),
    )


def parse_sales_docs(records: Sequence[Mapping[str, Any]]) -> Tuple[SalesDoc, ...]:
    """一批识别记录 → SalesDoc 列表。

    records 元素既可以是 {"merged_fields": {...}, "history_id": …}(识别记录原样),
    也可以是扁平的字段 dict —— 上游三种来源都能直接喂进来。
    """
    from services.excel.erp_roundtrip import encode_row_key

    out = []
    for rec in records or []:
        rec = rec or {}
        fields = rec.get("merged_fields") if isinstance(rec.get("merged_fields"), Mapping) else rec
        history_id = rec.get("history_id") or fields.get("history_id")
        out.append(parse_sales_doc(fields, row_key=encode_row_key(history_id, 0)))
    return tuple(out)
