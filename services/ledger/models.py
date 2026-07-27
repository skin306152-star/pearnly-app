# -*- coding: utf-8 -*-
"""销售票的输入契约:OCR/回导给的松散 dict → 账簿配方吃的确定性结构。

归一放在这一层一处,是因为同一张票的字段在仓里有三种来源(OCR 的 ThaiInvoice、回导解析器、
汇总表导入),键名各不相同。各配方各写一套取值就会漂。取值口径在 fields.py,日期口径在
doc_date.py;这个文件只管「一张票齐不齐、能不能入账」。

票号在这里当主键看:下游三张表的每一格都按票号 SUMIF 回明细,所以票号空或本批撞车的票
一律进待判 —— 那两种情况都会让表里的数和我们要推的数不一致,而借贷仍然相等、自检格照绿。

钱一律 Decimal:0.07 在 float 里不是精确的 0.07,而这些数字要进 ภ.พ.30。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Mapping, Optional, Sequence, Tuple

from services.excel.erp_money import to_money
from services.ledger.doc_date import DocDate, resolve_doc_date
from services.ledger.fields import pick, text
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

REASON_NO_SETTLEMENT = "ไม่ระบุวิธีชำระเงินบนเอกสาร · ระบุไม่ได้ว่าเป็นเงินสดหรือเงินโอน"
REASON_TOTAL_MISMATCH = "ยอดรวมบนเอกสารไม่ตรงกับผลรวมรายการสินค้า"
REASON_NO_LINES = "ไม่พบรายการสินค้าในเอกสาร"
REASON_NO_INVOICE_NUMBER = "ไม่พบเลขที่ใบเสร็จ · ทุกตารางในไฟล์นี้อ้างอิงกันด้วยเลขที่ใบเสร็จ"
REASON_DUPLICATE_INVOICE = (
    "เลขที่ใบเสร็จซ้ำในชุดนี้ ({inv}) · ต้องยืนยันว่าเป็นใบเดียวกันหรือคนละใบ"
)

CENT = Decimal("0.01")
ZERO = Decimal("0")


def settlement_of(payment_method: Any) -> str:
    """票面付款方式 → 结算去向。认不出返回空串 —— 空串是「不知道」,不是「现金」。"""
    return _SETTLEMENT_BY_METHOD.get(text(payment_method).lower(), "")


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
    amount = to_money(pick(raw, "subtotal", "amount", "line_total", "total"))
    qty = to_money(pick(raw, "qty", "quantity")) or Decimal("1")
    price = to_money(pick(raw, "price", "unit_price"))
    if amount is None:
        if price is None:
            return None
        # HALF_UP:与 split_gross 和表里的 ROUND(...,2) 同口径。上下文默认的 HALF_EVEN 在
        # 0.125 这类分位上给 0.12、Excel 给 0.13,同一张票会拆出两个数。
        amount = (qty * price).quantize(CENT, rounding=ROUND_HALF_UP)
    description = text(pick(raw, "name", "description", "item_name"))
    return SalesLine(description=description, qty=qty, unit_price=price, amount=amount)


def _pending_reason(
    lines: Sequence[SalesLine],
    invoice_number: str,
    doc_date: DocDate,
    settlement: str,
    printed_total: Optional[Decimal],
) -> str:
    """待判原因 —— 只报第一条,报一串会让会计不知道先修哪个。"""
    if not lines:
        return REASON_NO_LINES
    if not invoice_number:
        # 票号是这套工作簿事实上的主键:下游每一格都 SUMIF 回明细的票号列。票号空,
        # SUMIF 的 criteria 也空 —— Excel 匹配不到任何文本票号,这张票在三张派生表里
        # 显示 0,而回执照报全额。
        return REASON_NO_INVOICE_NUMBER
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
    method_raw = text(pick(fields, "payment_method", "payment"))
    settlement = settlement_of(method_raw)
    printed_total = to_money(pick(fields, "total_amount", "total"))
    invoice_number = text(pick(fields, "invoice_number", "invoice_no", "doc_number"))
    return SalesDoc(
        invoice_number=invoice_number,
        doc_date=doc_date.value,
        date_source=doc_date.source,
        customer_name=text(pick(fields, "buyer_name", "customer_name")),
        customer_tax_id=text(pick(fields, "buyer_tax", "buyer_tax_id", "customer_tax_id")),
        settlement=settlement,
        payment_method_raw=method_raw,
        lines=lines,
        row_key=row_key,
        pending_reason=_pending_reason(lines, invoice_number, doc_date, settlement, printed_total),
    )


def flag_duplicate_invoice_numbers(docs: Sequence[SalesDoc]) -> Tuple[SalesDoc, ...]:
    """本批内票号撞车的票一律进待判(两张都进,由会计判是不是同一张)。

    重号的后果不是少算而是**双算**:两张票的分录各自 SUMIF 都命中两张,借贷两侧同步翻倍,
    借贷仍然相等 —— 试算平衡照样显示 Balanced。「重拍即重扣」是拍板过的设计、不做去重,
    同一张票的两条识别记录进同一批时票号必然相同,所以这条路是常态不是理论。

    已经有待判原因的票不覆盖 —— 只报第一条。
    """
    counts = Counter(d.invoice_number for d in docs if d.invoice_number)
    return tuple(
        (
            replace(d, pending_reason=REASON_DUPLICATE_INVOICE.format(inv=d.invoice_number))
            if d.bookable and counts[d.invoice_number] > 1
            else d
        )
        for d in docs
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
    return flag_duplicate_invoice_numbers(out)
