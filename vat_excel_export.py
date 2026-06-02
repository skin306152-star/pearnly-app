# -*- coding: utf-8 -*-
"""
v118.32.4.10.1 · Pearnly · Excel 公式对账模块(全网开放)
完全独立于 vat_report_parser / reconciliation_matcher

设计哲学(Zihao 2026-05-13 拍板):
  AI 只抽字段 · 不做对账判定 · 让 Excel 公式让用户/Excel 自己核对
  A/B 测试是否比"AI 全程对账"更稳更便宜

调用方式:
  from vat_excel_export import extract_invoice_fields, merge_vat_reports, build_excel
"""

from field_comparator import (  # noqa: F401  re-export (safety-net 测试)
    normalize_invoice_no,
    normalize_tax_id,
    normalize_str,
    tax_id_fuzzy_distance,
)

# 对账核心 · moved to vat_recon_core.py
from vat_recon_core import (  # noqa: F401  re-export (tests) + facade-internal(build_excel/OCR/merge)
    _to_float,
    _derive_period,
    _dominant_report_period,
    _eq_amount,
    _get_inv_total,
    _get_rep_total,
    _build_recon_pairs,
    _diff_dims,
)

MODULE_VERSION = "1.5.0"


# 单张发票 OCR · moved to vat_ocr_extract.py
from vat_ocr_extract import (  # noqa: F401  re-export (routes/handlers/tests) + facade-internal
    extract_invoice_fields,
    _ocr_validate_invoice,
    extract_invoices_parallel,
    _ocr_with_hard_timeout,
    _VEX_OCR_PER_FILE_TIMEOUT,
)

# 批量 OCR · moved to vat_ocr_batch.py
from vat_ocr_batch import (  # noqa: F401  re-export (routes/handlers)
    extract_invoice_fields_batch,
    extract_invoices_batched_parallel,
)

# VAT 报告拼接 · moved to vat_report_merge.py
from vat_report_merge import merge_vat_reports  # noqa: F401  re-export (routes/handlers/tests)

# 4-sheet Excel 生成 · moved to vat_excel_build.py
from vat_excel_build import build_excel  # noqa: F401  re-export (routes/handlers/tests)
