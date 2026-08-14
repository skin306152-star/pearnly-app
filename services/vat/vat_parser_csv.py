# -*- coding: utf-8 -*-
"""VAT 报告解析 · CSV/TSV 确定性直读(2026-08-13 · F23)。

背景(bench 实弹):vat_report 的 csv 支路原先走 run_on_table_bytes → layer2 把
整份 CSV 序列化成文本交给 LLM 重读。779 行真表被 layer2_structure.MAX_TEXT_LENGTH
=30000 截到只剩 ~20 行(B 档召回 0.64%),qwen 档稳定 60s 超时。CSV 是结构化文本,
读列名 + 逐行取值是代码的本职,不是模型的本职 —— 列名映射命中就全行直读,映射
不命中(未知列结构)返回 None 让调用方走原 pipeline 兜底,行为不变。

产出形状与 _parse_vat_via_pipeline 完全一致(下游零改动):
rows 每行含 row_no / report_date / report_invoice_no / report_ref_no /
report_buyer_name / report_buyer_tax_id / report_buyer_branch /
report_amount_pre_vat / report_vat_amount / report_amount / is_individual。
金额用 Decimal 解析(避免 float 累加漂移),出线仍是 float(jsonb 落库/下游
float() 转换都认 float)。日期与现链一致:parse_date 归一化成 ISO(佛历自动转西历),
解析不了才保留票面原样。
"""

import csv
import io
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from services.recon.field_comparator import normalize_tax_id, normalize_branch, parse_date
from services.vat.vat_parser_common import (
    _map_columns,
    _SKIP_H,
    PARSER_VERSION,
)

# ── MR ERP 销项税登记簿(acvatsaled)导出列名 → 行字段 ───────────────
# 列名是 ERP 系统字段(非用户语言表头),_map_columns 的词表认不全(txtsino/txtamt
# 落不进 invoice no / net 的关键词),故此处精确匹配。其余列(vat_no/detail_id/
# txtdoctype/txtvatamtbal 等)不进行 schema,忽略。
_ERP_COL_FIELDS: Dict[str, str] = {
    "ref": "ref_no",
    "txtsino": "invoice_no",
    "txtamt": "amount_pre_vat",
    "txtvatamt": "vat_amount",
    "vat_date": "date",
    "txtsidate": "date",
    "txtvatdate": "date",
}

# 编码嗅探顺序与 table_path._decode_bytes 一致:泰文 csv 可能是 cp874/tis-620。
_ENCODINGS = ("utf-8-sig", "utf-8", "cp874", "tis-620", "cp1252", "latin-1")

# 找表头最多扫这么多行(ERP 导出可能有前置说明行)。
_MAX_HEADER_SCAN = 20


def _decode_bytes(b: bytes) -> str:
    for enc in _ENCODINGS:
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


def _to_amount(val) -> Optional[float]:
    """金额解析:Decimal 精确取 2 位小数,输出 float(与现链 _to_float 同型)。"""
    s = str(val or "").strip().replace(",", "").replace(" ", "").replace("\u00a0", "")
    if not s or s in {"-", "–"}:
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    try:
        d = Decimal(s)
    except Exception:  # noqa: BLE001 — 单个坏单元格不拖垮整行,置 None 由调用方判
        return None
    v = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(-v if neg else v)


def _map_erp_columns(headers: List[str]) -> Dict[str, int]:
    """ERP 导出列名 → 行字段列位(精确匹配 · 首见即取)。"""
    col_map: Dict[str, int] = {}
    for i, h in enumerate(headers):
        field = _ERP_COL_FIELDS.get((h or "").strip().lower())
        if field is None or field in col_map:
            continue
        col_map[field] = i
    return col_map


def _usable(col_map: Dict[str, int]) -> bool:
    """映射可用 = 有单据号(发票号或参考号)+ 至少一个金额列。"""
    has_doc = "invoice_no" in col_map or "ref_no" in col_map
    has_amt = any(k in col_map for k in ("amount_pre_vat", "vat_amount", "total_amount"))
    return has_doc and has_amt


def _build_csv_row(row_no: int, cells: List[str], col_map: Dict[str, int]) -> Dict[str, Any]:
    """行构建:与 vat_parser_common._build_row 同形状,仅金额走 Decimal 解析。
    无 total 列时 report_amount = 净额 + 税(与 pdf/gemini 路径的补算一致)。"""
    parsed: Dict[str, Any] = {"row_no": row_no}
    for field, ci in col_map.items():
        raw = cells[ci] if ci < len(cells) else None
        val = str(raw).strip() if raw is not None else ""
        if field == "date":
            d = parse_date(val)
            parsed["report_date"] = d.isoformat() if d else val
        elif field == "invoice_no":
            parsed["report_invoice_no"] = val
        elif field == "ref_no":
            parsed["report_ref_no"] = val
        elif field == "buyer_name":
            parsed["report_buyer_name"] = val
        elif field == "buyer_tax_id":
            parsed["report_buyer_tax_id"] = normalize_tax_id(val)
        elif field == "buyer_branch":
            parsed["report_buyer_branch"] = normalize_branch(val)
        elif field == "amount_pre_vat":
            parsed["report_amount_pre_vat"] = _to_amount(val)
        elif field == "vat_amount":
            parsed["report_vat_amount"] = _to_amount(val)
        elif field == "total_amount":
            parsed["report_amount"] = _to_amount(val)
    if "report_amount" not in parsed:
        pre = parsed.get("report_amount_pre_vat")
        vat = parsed.get("report_vat_amount")
        if pre is not None and vat is not None:
            parsed["report_amount"] = round(pre + vat, 2)
    # 与 pipeline 出口同形状:ERP 导出没有买方列时这些键也要在(下游 .get 可空,
    # 但缺键会让 JSON 形状漂移)。tax_id/branch 沿用现链归一化规则。
    parsed.setdefault("report_buyer_name", "")
    parsed.setdefault("report_buyer_tax_id", "")
    parsed.setdefault("report_buyer_branch", normalize_branch(""))
    parsed["is_individual"] = not bool(parsed.get("report_buyer_tax_id"))
    return parsed


def parse_csv_direct(file_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
    """CSV/TSV 确定性直读。列结构认得出 → 返回与 pipeline 同形状的解析结果;
    认不出(空文件 / 表头映射不命中)→ 返回 None,调用方走原 pipeline 兜底。"""
    ext = (filename or "").lower().rsplit(".", 1)[-1]
    delimiter = "\t" if ext == "tsv" else ","
    text = _decode_bytes(file_bytes)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        rows = [r for r in reader]
    except Exception:  # noqa: BLE001 — csv 结构坏(引号不成对等)→ 兜底
        return None
    if not rows:
        return None

    # 找表头:前 _MAX_HEADER_SCAN 行里首个映射可用的行(ERP 精确映射优先,
    # 人类表头走 _map_columns 复用)。数据行不会命中列头关键词。
    header_idx = None
    col_map: Dict[str, int] = {}
    for i, r in enumerate(rows[:_MAX_HEADER_SCAN]):
        headers = [(c or "").strip() for c in r]
        erp = _map_erp_columns(headers)
        if _usable(erp):
            header_idx, col_map = i, erp
            break
        generic = _map_columns(headers)
        if _usable(generic):
            header_idx, col_map = i, generic
            break
    if header_idx is None:
        return None

    parsed_rows: List[Dict[str, Any]] = []
    skipped = 0
    for r in rows[header_idx + 1 :]:
        cells = [(c or "").strip() for c in r]
        if not any(cells):
            continue
        # 合计/小计行不进数据(现链 excel 路径同样行为)
        first = cells[0].lower()
        if any(k in first for k in _SKIP_H):
            continue
        row = _build_csv_row(len(parsed_rows) + 1, cells, col_map)
        doc_no = row.get("report_invoice_no") or row.get("report_ref_no") or ""
        if not doc_no:
            skipped += 1
            continue
        parsed_rows.append(row)

    warnings: List[str] = []
    if skipped:
        warnings.append(f"跳过 {skipped} 行(无单据号)")

    return {
        "ok": True,
        "rows": parsed_rows,
        "row_count": len(parsed_rows),
        "meta": {},
        "warnings": warnings,
        "parser_version": PARSER_VERSION,
        "method": "csv_direct_v1",
        "needs_review": False,
    }
