# -*- coding: utf-8 -*-
"""
services/recon/bank_gl_common.py · Pearnly

GL column recognition shared by the Excel and PDF parsers: multilingual
header-keyword dictionaries, account-code regex, header→column mapping, and
account-code extraction. Leaf module (header matching from bank_table_io).
"""

import re
from typing import List, Dict

from services.recon.bank_table_io import _hit

# ─────────────────────────────────────────────────────────────────────────────
# GL PARSERS
# ─────────────────────────────────────────────────────────────────────────────
_GL_DATE_H = {"วันที่", "date", "วัน", "日期", "日付"}
_GL_DOC_H = {
    "ใบสำคัญ",
    "เลขที่เอกสาร",
    "doc",
    "voucher",
    "reference",
    "เอกสาร",
    "凭证",
    "伝票番号",
    "伝票",
    "ref",
}
_GL_DESC_H = {"คำอธิบาย", "รายการ", "description", "detail", "รายละเอียด", "摘要"}
_GL_DEBIT_H = {"เดบิต", "เดบิท", "debit", "dr", "借方", "ถอน", "จ่าย"}
_GL_CRED_H = {"เครดิต", "credit", "cr", "贷方", "貸方", "ฝาก", "รับ"}
_GL_ACCT_H = {"รหัสบัญชี", "account", "gl account", "เลขที่บัญชี", "รหัส", "账号", "科目"}
# BUG-FIX-T2 v118.35.0.43 · balance/余额 列识别 · 给 opening 检测读期初余额用
# (老逻辑只看 debit/credit · Row 2 期初 ยอดยกมา 余额列填 39749.85 没读到 → opening=0 → closing 全错)
_GL_BAL_H = {"คงเหลือ", "ยอดคงเหลือ", "balance", "running balance", "余额", "残高"}

_ACCT_RE = re.compile(r"(?<![\d.])([1-9]\d{3,6}(?:[-–]\d{2,3})?)(?![\d.])")


def _map_gl_cols(header_row: List) -> Dict[str, int]:
    col_map: Dict[str, int] = {}
    for i, cell in enumerate(header_row):
        h = str(cell or "").strip().lower()
        if not h:
            continue
        if "date" not in col_map and _hit(h, _GL_DATE_H):
            col_map["date"] = i
        elif "doc_no" not in col_map and _hit(h, _GL_DOC_H):
            col_map["doc_no"] = i
        elif "description" not in col_map and _hit(h, _GL_DESC_H):
            col_map["description"] = i
        elif "debit" not in col_map and _hit(h, _GL_DEBIT_H):
            col_map["debit"] = i
        elif "credit" not in col_map and _hit(h, _GL_CRED_H):
            col_map["credit"] = i
        elif "account" not in col_map and _hit(h, _GL_ACCT_H):
            col_map["account"] = i
        elif "balance" not in col_map and _hit(h, _GL_BAL_H):
            col_map["balance"] = i  # BUG-FIX-T2 v118.35.0.43 · 给 opening 检测读期初余额
    return col_map


def _extract_acct_code(text: str) -> str:
    m = _ACCT_RE.search(str(text or ""))
    return m.group(1) if m else ""


def attach_running_balance(rows, opening: float) -> None:
    """给每行附运行余额(期初 + 累计借−贷 · 借=存入抬升)· 原始顺序就地写 row.balance。
    PDF/Excel 两个 GL 解析器共用 · 单点维护舍入与方向约定。仅展示/导出 · 不参与匹配。"""
    bal = opening
    for r in rows:
        bal = round(bal + r.debit - r.credit, 2)
        r.balance = bal
