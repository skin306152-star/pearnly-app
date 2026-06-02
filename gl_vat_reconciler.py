# -*- coding: utf-8 -*-
"""
gl_vat_reconciler.py · v1.0.0
GL(总账) vs 销项税报告 对账核心引擎

匹配规则（客户 2026-05-15 确认）：
- 主键：VAT.เลขที่เอกสารอ้างอิง（参考单号）↔ GL.ใบสำคัญ（凭证号），归一化后比对
- VAT.มูลค่าสินค้าและบริการ 正数 → 取 GL Credit
- VAT.มูลค่าสินค้าและบริการ 负数 → 取 GL Debit 并转为负数
- 末列附加 GL 的 รหัสบัญชี（收入科目代码）
"""

# DATA CLASSES · moved to services/recon/gl_vat_types.py
from services.recon.gl_vat_types import (  # noqa: F401,E402  re-export (recon_routes/tests) + facade-internal
    GlRow,
    ReconRow,
    GlVatSummary,
)

# EXCEL EXPORT · moved to services/recon/gl_vat_excel.py
from services.recon.gl_vat_excel import (  # noqa: F401,E402  re-export (recon_routes)
    export_gl_vat_excel,
)

# PARSE COMMON · moved to services/recon/gl_vat_parse_common.py
from services.recon.gl_vat_parse_common import (  # noqa: F401  re-export (tests) + facade-internal
    _to_float,
    _is_revenue_acct,
    _hit,
    _extract_account_code,
    _is_debit_line,
    _is_skip_row,
    normalize_doc_no,
    _map_gl_columns,
    _row_has_amount,
    _GL_DATE_H,
    _GL_DOC_H,
    _GL_DESC_H,
    _GL_DEBIT_H,
    _GL_CRED_H,
    _GL_ACCT_H,
    _ACCT_RE,
    _SKIP_ROWS,
    _DEBIT_LINE_KW,
)

# PARSE PDF · moved to services/recon/gl_vat_parse_pdf.py
from services.recon.gl_vat_parse_pdf import (  # noqa: F401  re-export + facade-internal(parse_gl dispatch)
    _parse_gl_text_lines,
    parse_gl_pdf,
)


# PARSE EXCEL/DISPATCH · moved to services/recon/gl_vat_parse_excel.py
from services.recon.gl_vat_parse_excel import (  # noqa: F401  re-export (recon_routes/tests)
    parse_gl_excel,
    parse_gl,
)

# RECONCILE CORE(高敏 VAT 判定)· moved to services/recon/gl_vat_reconcile.py
from services.recon.gl_vat_reconcile import (  # noqa: F401  re-export (recon_routes/tests)
    reconcile_gl_vat,
)


# SERIALIZE · moved to services/recon/gl_vat_serialize.py
from services.recon.gl_vat_serialize import (  # noqa: F401  re-export (recon_routes/tests)
    detail_to_json,
    summary_to_json,
    detail_from_json,
    summary_from_json,
)
