# -*- coding: utf-8 -*-
"""
Mr.Pilot · 统一报表引擎 v109.0
==============================
职责:
  - 4 个内置模板(input_vat / standard / erp / print)
  - 统一 build_report(template_code, rows, meta, lang) → bytes
  - 统一 list_templates(lang) → 给前端弹窗
  - 多 Sheet 输出(主明细 + 汇总分析)
  - 4 语言跟随 UI
  - 专业样式(深蓝表头 / 斑马行 / 千位分隔 / SUM 公式 / 冻结首行)

老 excel_export.build_xlsx 保留兼容 · 不删。
"""

import io
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from openpyxl import Workbook

from services.report.i18n_reports import i18n_get  # noqa: F401  used by facade fns
from services.report.report_engine_templates import REPORT_TEMPLATES  # noqa: F401  public re-export
from services.report.report_engine_format import _normalize_row
from services.report.report_engine_sheets import _write_main_sheet, _write_summary_sheet


def list_templates(lang: str = "zh") -> List[Dict[str, Any]]:
    """前端模板选择弹窗用"""
    out = []
    for code, t in REPORT_TEMPLATES.items():
        out.append(
            {
                "code": code,
                "name": i18n_get(lang, t["name_key"]),
                "desc": i18n_get(lang, t["desc_key"]),
                "category": i18n_get(lang, t["category_key"]),
                "category_code": t["category_key"].replace("tpl-cat-", ""),
                "recommended": bool(t.get("recommended")),
            }
        )
    return out


def build_report(
    template_code: str,
    rows: List[Dict[str, Any]],
    meta: Optional[Dict[str, Any]] = None,
    lang: str = "zh",
) -> bytes:
    """
    统一报表生成器
    template_code: input_vat / standard / erp / print
    rows: 任意来源的发票数据(自动归一化)
    meta: {client_name, client_tax_id, client_branch, period_label, doc_count}
    lang: zh / th / en / ja
    返回:xlsx bytes
    """
    if template_code not in REPORT_TEMPLATES:
        raise ValueError(f"Unknown template: {template_code}")
    if lang not in ("zh", "th", "en", "ja"):
        lang = "zh"
    template = REPORT_TEMPLATES[template_code]
    meta = dict(meta or {})

    # 归一化行
    norm_rows = [_normalize_row(r, idx + 1) for idx, r in enumerate(rows or [])]
    if "doc_count" not in meta:
        meta["doc_count"] = len(norm_rows)

    wb = Workbook()
    _write_main_sheet(wb, template, norm_rows, meta, lang)

    if template.get("show_summary_sheet") and norm_rows:
        _write_summary_sheet(wb, norm_rows, lang)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def default_filename(template_code: str = "standard", client: str = "", period: str = "") -> str:
    """生成默认文件名"""
    parts = ["mrpilot"]
    if client:
        # 清理文件名非法字符
        safe_client = re.sub(r"[\\/:*?\"<>|]", "_", client.strip())[:40]
        if safe_client:
            parts.append(safe_client)
    if period:
        parts.append(period.replace("/", "-"))
    parts.append(template_code)
    parts.append(datetime.now().strftime("%Y%m%d-%H%M%S"))
    return "-".join(parts) + ".xlsx"


__all__ = [
    "build_report",
    "list_templates",
    "default_filename",
    "REPORT_TEMPLATES",
]
