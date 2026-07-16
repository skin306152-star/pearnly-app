# -*- coding: utf-8 -*-
"""GL 上传件 → GlRow 适配器(T4a · F2 对平的解析入口)。

主路 PDF 走 fileconv.extract_ledger(K1a 真料已验,忠实抽取 + 守恒在 fileconv 侧),本层只做
LedgerRow → GlRow 形状转换;xlsx/csv 走现成 bank_gl_excel.parse_gl_excel(产出即 GlRow)。
借贷双列行直搬;单金额列行照 bank_gl_stacked 的余额变动定向法(余额涨=借、跌=贷),
定不了向的行(无期初可锚 / 余额持平)如实丢 row_issues 不臆造方向。

Decimal → float 只发生在 GlRow 边界(GlRow 是展示型 float 契约);下游 shadow_gl_recon
经 str() 转回 Decimal 清算,两位小数金额在此往返无损(金标数值精度测试钉住)。
整件解析失败抛 GlUploadParseError,由 reconcile 注入点收进 gl_source=parse_failed,
绝不静默降级成 no_gl_source。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Dict, List, Tuple

from services.fileconv.ledger import extract_ledger
from services.fileconv.model import LedgerRow
from services.fileconv.text_layer import extract_pages, has_text_layer
from services.recon.bank_recon_types import GlRow

_PDF_EXTS = {"pdf"}
_SHEET_EXTS = {"xlsx", "xlsm", "xls", "csv"}


class GlUploadParseError(Exception):
    """整件 GL 解析失败(无文字层/认不出结构/零行)。消息即诚实降级的 note 摘要。"""


def _iso_date(value: str) -> date | None:
    """LedgerRow.date_ce(ISO 或空)→ date。解析不了 → None(GlRow.date 允许空,不编日期)。"""
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def from_ledger_rows(
    rows: List[LedgerRow], opening: Dict[str, Decimal], source_file: str = ""
) -> Tuple[List[GlRow], List[str]]:
    """LedgerRow 列表 → (GlRow 列表, 行级丢弃清单)。

    借贷双列行(MR.ERP 三栏)直搬。单金额列行按余额变动定向:每科目从期初链起,
    余额差>0 记借、<0 记贷(与 bank_gl_stacked 同口径);首行无期初可锚或余额持平
    → 方向无据,如实丢一条 issue,绝不猜借贷。所有行都推进余额链(丢弃行的余额
    仍是下一行的锚,链不断)。
    """
    out: List[GlRow] = []
    issues: List[str] = []
    prev: Dict[str, Decimal] = dict(opening)

    for r in rows:
        if r.debit is not None or r.credit is not None:
            out.append(_gl_row(r, r.debit or Decimal("0"), r.credit or Decimal("0"), source_file))
            prev[r.account] = r.balance
            continue

        anchor = prev.get(r.account)
        prev[r.account] = r.balance
        if anchor is None:
            issues.append(f"line {r.line_no}: 单金额行无期初可锚,方向定不了,如实丢弃")
            continue
        delta = r.balance - anchor
        if delta == 0:
            issues.append(f"line {r.line_no}: 余额持平,单金额行方向定不了,如实丢弃")
            continue
        amount = delta.copy_abs()
        debit = amount if delta > 0 else Decimal("0")
        credit = amount if delta < 0 else Decimal("0")
        out.append(_gl_row(r, debit, credit, source_file))

    return out, issues


def _gl_row(r: LedgerRow, debit: Decimal, credit: Decimal, source_file: str) -> GlRow:
    return GlRow(
        date=_iso_date(r.date_ce),
        doc_no=r.doc_no,
        account_code=r.account,
        description=r.description,
        debit=float(debit),
        credit=float(credit),
        source_file=source_file,
        balance=float(r.balance),
    )


def parse_gl_bytes(data: bytes, filename: str) -> dict:
    """一份 GL 上传件字节 → {"rows": [GlRow], "row_issues": [str]}。

    PDF:文字层 → extract_ledger → from_ledger_rows;扫描件(无文字层)诚实拒绝。
    表格:parse_gl_excel(固定词典识列,不开 AI 路)。零行/认不出结构一律抛
    GlUploadParseError——「有件但读不出」必须与「没件」分得开。
    """
    ext = (filename or "").rsplit(".", 1)[-1].lower()
    if ext in _PDF_EXTS:
        pages = extract_pages(data)
        if not has_text_layer(pages):
            raise GlUploadParseError("no_text_layer")
        ledger_rows, opening = extract_ledger(pages)
        rows, issues = from_ledger_rows(ledger_rows, opening, source_file=filename)
        if not rows:
            raise GlUploadParseError("no_ledger_rows")
        return {"rows": rows, "row_issues": issues}

    if ext in _SHEET_EXTS:
        from services.accounting import express_gl_adapter

        # Express GLJNLIT csv(表头 VOUCHER/ACCNUM/TRNTYP)走专用适配器;其余 csv/xlsx 原路不改。
        if express_gl_adapter.is_express_gl(data, filename):
            rows, issues = express_gl_adapter.parse_express_gl_csv(data, filename)
            if not rows:
                raise GlUploadParseError("no_express_gl_rows")
            return {"rows": rows, "row_issues": issues}

        from services.accounting import mrerp_gl_adapter

        # MR.ERP 分类账 xlsx(逐科目分组·表头 วันที่/สมุด/เดบิต/เครดิต)走专用适配器;非 MR.ERP xlsx 原路不改。
        if mrerp_gl_adapter.is_mrerp_gl(data, filename):
            rows, issues = mrerp_gl_adapter.parse_mrerp_gl_xlsx(data, filename)
            if not rows:
                raise GlUploadParseError("no_mrerp_gl_rows")
            return {"rows": rows, "row_issues": issues}

        from services.recon.bank_gl_excel import parse_gl_excel

        parsed = parse_gl_excel(data, filename)
        if not parsed.get("ok"):
            raise GlUploadParseError(parsed.get("error_code") or parsed.get("error") or "gl_excel")
        rows = parsed.get("rows") or []
        if not rows:
            raise GlUploadParseError("no_ledger_rows")
        for row in rows:
            if not row.source_file:
                row.source_file = filename
        return {"rows": rows, "row_issues": []}

    raise GlUploadParseError(f"unsupported_ext:{ext or '(none)'}")
