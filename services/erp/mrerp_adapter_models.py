# -*- coding: utf-8 -*-
"""
mrerp_adapter_models.py · MRERPAdapter 返回值 dataclasses

从 mrerp_adapter.py 抽出（REFACTOR-WB-modularize M0 · verbatim 搬家 0 逻辑改）。
InvoiceRecord / FailedRow / SuccessRow / ImportResult —— 纯 dataclass 定义,零外部依赖。
作 leaf 模块供 mrerp_adapter 主体 + 各 Mixin 共同 import,破「主类 ←→ mixin」循环。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class InvoiceRecord:
    """One row found via search_invoice()."""

    invoice_no: str
    bill_no: str
    db_row_id: str
    listing_url: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FailedRow:
    """One invoice that failed business validation.

    `reasons` holds the raw Thai/English text exactly as MR.ERP wrote it
    in the report.xlsx (or our ERR_* code for preflight failures).
    `reasons_friendly` is a parallel list of `{lang: translation}` dicts
    sourced from `services.erp.mrerp_business_friendly`; the UI picks
    whichever language matches the viewer."""

    invoice_no: str
    reasons: List[str]
    original: Dict[str, Any]
    reasons_friendly: List[Dict[str, str]] = field(default_factory=list)
    evidence_screenshot: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SuccessRow:
    """One invoice that landed in MR.ERP's DB."""

    invoice_no: str
    mrerp_bill_no: str
    original: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImportResult:
    """Return value of upload_invoice_batch."""

    total: int
    success: List[SuccessRow] = field(default_factory=list)
    failed: List[FailedRow] = field(default_factory=list)
    elapsed_ms: int = 0
    xlsx_size_bytes: int = 0
    report_xlsx_path: Optional[str] = None

    @property
    def all_success(self) -> bool:
        return self.total > 0 and not self.failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "success": [s.to_dict() for s in self.success],
            "failed": [f.to_dict() for f in self.failed],
            "elapsed_ms": self.elapsed_ms,
            "xlsx_size_bytes": self.xlsx_size_bytes,
            "report_xlsx_path": self.report_xlsx_path,
            "all_success": self.all_success,
        }


def bill_no_for(doc_type: str, invoice_no: str) -> str:
    """回执单号:销项类 MR.ERP 列表实测显示 SI+票号;采购/库存前缀未实测过,
    不臆造(曾把采购也标 SI·纯显示化妆债)→ 非销项原样返票号(REFNUM 可查)。"""
    prefix = "SI" if str(doc_type or "").startswith("sales") else ""
    return f"{prefix}{invoice_no}"
