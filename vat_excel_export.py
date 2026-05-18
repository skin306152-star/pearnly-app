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
import io
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from vat_report_parser import parse_vat_report  # 复用但不修改
from field_comparator import (
    normalize_invoice_no, normalize_tax_id, normalize_str,
    parse_date, tax_id_fuzzy_distance,
)

logger = logging.getLogger(__name__)
MODULE_VERSION = "1.5.0"  # v4.10.23 · Sheet3 KPI 区升级为 Korn 模板格式(EFF6FF 行 · 标签+彩色大值)


# ════════════════════════════════════════════════════════════════════════
# 单张发票 OCR · 只抽 8 字段(独立 prompt · 不做匹配)
# ════════════════════════════════════════════════════════════════════════
_INVOICE_PROMPT = """You are reading a Thai tax invoice (ใบกำกับภาษี) or its image.

Extract ONLY these 8 fields. Do NOT interpret · do NOT match · do NOT clean.

Output JSON ONLY:
{
  "buyer_tax_id": "13-digit Thai tax ID of the BUYER (ลูกค้า / ผู้ซื้อ) · digits only · empty string if missing",
  "buyer_name":   "Buyer name EXACTLY as printed (Thai/English/mixed) · keep prefixes like บริษัท ... จำกัด",
  "buyer_branch": "Branch · 'สำนักงานใหญ่' or 5-digit code (e.g. 00001) · empty string if cash customer",
  "invoice_no":   "Invoice number EXACTLY as printed · keep prefixes (INV/IV/TAX) · do NOT strip leading zeros",
  "invoice_date": "Date EXACTLY as printed · format DD/MM/YYYY · if Buddhist Era (e.g. 2569) keep that year",
  "period":       "If invoice header shows a tax period (e.g. 04/2026), copy it · else derive MM/YYYY from invoice_date · Gregorian only",
  "amount_pre_vat": "Net amount BEFORE VAT · number only · 2 decimals",
  "vat_amount":     "VAT amount · number only · 2 decimals",
  "total_amount":   "TOTAL including VAT · number only · 2 decimals"
}

STRICT RULES:
1. If a field is partially visible or unreadable · output "" · do NOT guess
2. Do NOT normalize prefixes · do NOT fuzzy-match · just copy what is printed
3. Cash customer (ลูกค้าขายเงินสด) → buyer_tax_id="" buyer_branch=""
4. Date: BE years (2500+) stay as printed · period: convert BE → Gregorian (BE-543)
5. Numbers: digits and dot only · no commas · no currency
"""


def extract_invoice_fields(file_bytes: bytes, filename: str,
                             api_key: Optional[str] = None) -> Dict[str, Any]:
    """单张发票 OCR · 抽 8 字段
    返回:{ok, filename, buyer_tax_id, buyer_name, buyer_branch, invoice_no,
           invoice_date, period, amount_pre_vat, vat_amount, total_amount, error}
    """
    ext = (filename or "").lower().rsplit(".", 1)[-1]

    # v118.32.5.5.9 · text_path 快路径(电子 PDF · 跳 Gemini · 5-10x 提速)
    # BAKELAB / 多数泰国电子发票文字层完整 · 不需要 Gemini
    if ext == "pdf":
        try:
            from pdf_text_extractor import try_text_extraction
            tp = try_text_extraction(file_bytes, strict=False)
            if tp:
                fld: Dict[str, Any] = {}
                for p in (tp.get("pages") or []):
                    for k, v in (p.get("fields") or {}).items():
                        if k not in fld and v:
                            fld[k] = v
                date_str = str(fld.get("date") or "").strip()
                # 从 date 推 period MM/YYYY(兼容佛历)
                period = ""
                if date_str:
                    m = re.match(r'(\d{1,2})[\-/.](\d{1,2})[\-/.](\d{2,4})', date_str)
                    if m:
                        y = int(m.group(3))
                        if y < 100: y += 2000
                        if y > 2400: y -= 543
                        period = f"{int(m.group(2)):02d}/{y}"
                logger.info(f"[vex.text_path] {filename} · 跳 Gemini · 0 cost")
                return {
                    "ok":              True,
                    "filename":        filename,
                    "buyer_tax_id":    str(fld.get("buyer_tax") or "").strip(),
                    "buyer_name":      str(fld.get("buyer_name") or "").strip(),
                    "buyer_branch":    "",
                    "invoice_no":      str(fld.get("invoice_number") or "").strip(),
                    "invoice_date":    date_str,
                    "period":          period,
                    "amount_pre_vat":  _to_float(fld.get("subtotal")),
                    "vat_amount":      _to_float(fld.get("vat")),
                    "total_amount":    _to_float(fld.get("total_amount")),
                    "_input_tokens":   0,
                    "_output_tokens":  0,
                    "_engine":         "text_path",
                }
        except Exception as _tpe:
            logger.info(f"[vex.text_path] {filename} 异常 fallback Gemini · {type(_tpe).__name__}: {_tpe}")

    mime = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}.get(ext)
    if not mime:
        return {"ok": False, "filename": filename, "error": f"不支持的格式 .{ext}"}

    try:
        import google.generativeai as genai
    except ImportError:
        return {"ok": False, "filename": filename, "error": "google-generativeai 未安装"}

    key = (api_key or os.environ.get("GEMINI_API_KEY")
           or os.environ.get("GOOGLE_API_KEY"))
    if not key:
        return {"ok": False, "filename": filename, "error": "Gemini key 未配置"}

    text = ""
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        )
        response = model.generate_content(
            [_INVOICE_PROMPT, {"mime_type": mime, "data": file_bytes}],
            request_options={"timeout": 30},
        )
        text = (response.text or "").strip()
        data = json.loads(text)
        _usage = getattr(response, "usage_metadata", None)
        _in_tok  = int(getattr(_usage, "prompt_token_count",     0) or 0)
        _out_tok = int(getattr(_usage, "candidates_token_count", 0) or 0)
        return {
            "ok":              True,
            "filename":        filename,
            "buyer_tax_id":    str(data.get("buyer_tax_id") or "").strip(),
            "buyer_name":      str(data.get("buyer_name") or "").strip(),
            "buyer_branch":    str(data.get("buyer_branch") or "").strip(),
            "invoice_no":      str(data.get("invoice_no") or "").strip(),
            "invoice_date":    str(data.get("invoice_date") or "").strip(),
            "period":          str(data.get("period") or "").strip(),
            "amount_pre_vat":  _to_float(data.get("amount_pre_vat")),
            "vat_amount":      _to_float(data.get("vat_amount")),
            "total_amount":    _to_float(data.get("total_amount")),
            "_input_tokens":   _in_tok,
            "_output_tokens":  _out_tok,
        }
    except json.JSONDecodeError as e:
        logger.warning(f"[vex.extract] {filename} JSON 解析失败: {e} · raw={text[:200]}")
        return {"ok": False, "filename": filename,
                "error": f"AI 返回格式异常: {str(e)[:60]}"}
    except Exception as e:
        logger.error(f"[vex.extract] {filename} 失败: {type(e).__name__}: {e}")
        return {"ok": False, "filename": filename, "error": str(e)[:120]}


def _to_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return round(float(str(v).replace(",", "")), 2)
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════
# v4.10.22 · OCR 准确率底线 · 7 项硬校验
# ════════════════════════════════════════════════════════════════════════

def _ocr_validate_invoice(inv: Dict) -> List[str]:
    """7 项 OCR 准确率底线校验 · 返回问题 key 列表(空=全通过)
    校验规则:发票号空 / 客户名空 / 税号非13位 / 日期格式异常 /
             含税金额为0 / VAT≠7% / 净额+VAT≠总额"""
    warns: List[str] = []
    # 1. 发票号空
    if not (inv.get("invoice_no") or "").strip():
        warns.append("w_invoice_no_empty")
    # 2. 客户名空
    if not (inv.get("buyer_name") or "").strip():
        warns.append("w_buyer_name_empty")
    # 3. 税号非 13 位(仅当非空时校验 · 只数数字位数)
    tax_digits = "".join(c for c in (inv.get("buyer_tax_id") or "") if c.isdigit())
    if tax_digits and len(tax_digits) != 13:
        warns.append("w_tax_id_bad_length")
    # 4. 日期格式异常(仅当非空时校验)
    date_str = (inv.get("invoice_date") or "").strip()
    if date_str and parse_date(date_str) is None:
        warns.append("w_date_parse_fail")
    # 5. 含税金额为 0 或缺失
    total = _to_float(inv.get("total_amount"))
    if total is None or total == 0.0:
        warns.append("w_total_zero")
    # 6. VAT ≠ 7%(净额 > 10 THB 才检查 · 容差 max(1 THB, 5%))
    pre = _to_float(inv.get("amount_pre_vat"))
    vat = _to_float(inv.get("vat_amount"))
    if pre is not None and vat is not None and pre > 10.0:
        expected_vat = round(pre * 0.07, 2)
        tol = max(1.0, expected_vat * 0.05)
        if abs(vat - expected_vat) > tol:
            warns.append("w_vat_rate_mismatch")
    # 7. 净额 + VAT ≠ 总额(三值都有 · 容差 0.02 THB)
    if pre is not None and vat is not None and total is not None and total > 0:
        computed = round(pre + vat, 2)
        if abs(computed - total) > 0.02:
            warns.append("w_amount_sum_mismatch")
    return warns


# ════════════════════════════════════════════════════════════════════════
# v118.32.4.9.6 新增 · 辅助函数(Bug 1/2/3/4/5)
# ════════════════════════════════════════════════════════════════════════

def _derive_period(date_str: str, period_str: str = "") -> str:
    """Bug 1 · 期间降级 · period 非空直接用 · 否则从日期算 MM/YYYY 公历(BE 自动转)"""
    s = (period_str or "").strip()
    if s:
        return s
    d = parse_date(date_str or "")
    if d:
        return f"{d.month:02d}/{d.year}"
    return ""


def _eq_amount(a, b, tol: float = 0.01) -> bool:
    try:
        return abs(float(a or 0) - float(b or 0)) <= tol
    except Exception:
        return False


def _get_inv_total(inv: Dict) -> float:
    try:
        return round(float(inv.get("total_amount") or 0), 2)
    except Exception:
        return 0.0


def _get_rep_total(row: Dict) -> float:
    pre = row.get("report_amount_pre_vat") or row.get("report_amount") or 0
    vat = row.get("report_vat_amount") or 0
    try:
        return round(float(pre or 0) + float(vat or 0), 2)
    except Exception:
        return 0.0


def _build_recon_pairs(invoices: List[Dict], report_rows: List[Dict]) -> Dict[str, Any]:
    """v118.32.4.9.6 · 一对一配对引擎(Bug 2/3/4/5)
    多轮匹配 · 优先级从高到低:
      1) 发票号 normalize 一致 → matched
      2) 税号 + 含税金额 一致 → matched
      3) 散客双方都无税号 · 客户名 + 发票号 + 金额 三重一致 → matched_cash(Bug 2)
      4) 税号编辑距离 ≤2 + 金额一致 → fuzzy(Bug 4 · 疑似 · 标 "请确认")
      5) 发票税号空 + 报告里能查到(客户名+发票号+金额一致)→ ocr_missing(Bug 5 · OCR 漏抽)
      剩余:invoice_orphan / report_orphan
    返回: {pairs:[{inv_idx, rep_idx, kind, note}], unmatched_inv:[idx], unmatched_rep:[idx]}
    """
    n_inv = len(invoices)
    n_rep = len(report_rows)
    used_inv: set = set()
    used_rep: set = set()
    pairs: List[Dict] = []

    # ── 第 1 轮 · 发票号 normalize 一致
    rep_no_idx: Dict[str, List[int]] = {}
    for ri in range(n_rep):
        key = normalize_invoice_no(report_rows[ri].get("report_invoice_no") or "")
        if key:
            rep_no_idx.setdefault(key, []).append(ri)

    for ii in range(n_inv):
        key = normalize_invoice_no(invoices[ii].get("invoice_no") or "")
        if not key:
            continue
        candidates = rep_no_idx.get(key, [])
        for ri in candidates:
            if ri in used_rep:
                continue
            used_inv.add(ii); used_rep.add(ri)
            pairs.append({"inv_idx": ii, "rep_idx": ri, "kind": "matched", "note": ""})
            break

    # ── 第 2 轮 · 税号 + 含税金额 一致
    for ii in range(n_inv):
        if ii in used_inv: continue
        inv = invoices[ii]
        t1 = normalize_tax_id(inv.get("buyer_tax_id") or "")
        if not t1: continue
        a1 = _get_inv_total(inv)
        for ri in range(n_rep):
            if ri in used_rep: continue
            rep = report_rows[ri]
            t2 = normalize_tax_id(rep.get("report_buyer_tax_id") or "")
            if t1 != t2: continue
            if _eq_amount(a1, _get_rep_total(rep)):
                used_inv.add(ii); used_rep.add(ri)
                pairs.append({"inv_idx": ii, "rep_idx": ri, "kind": "matched", "note": ""})
                break

    # ── 第 3 轮 · 散客双方都无税号 · 三重匹配(Bug 2)
    for ii in range(n_inv):
        if ii in used_inv: continue
        inv = invoices[ii]
        if normalize_tax_id(inv.get("buyer_tax_id") or ""):
            continue  # 不是散客
        inv_name = normalize_str(inv.get("buyer_name") or "")
        inv_no   = normalize_invoice_no(inv.get("invoice_no") or "")
        inv_amt  = _get_inv_total(inv)
        for ri in range(n_rep):
            if ri in used_rep: continue
            rep = report_rows[ri]
            if normalize_tax_id(rep.get("report_buyer_tax_id") or ""):
                continue  # 报告这行不是散客
            rep_name = normalize_str(rep.get("report_buyer_name") or "")
            rep_no   = normalize_invoice_no(rep.get("report_invoice_no") or "")
            rep_amt  = _get_rep_total(rep)
            # 名 + 号 + 金 三重 · 金最严 · 名/号至少一个非空且一致
            if not _eq_amount(inv_amt, rep_amt): continue
            name_ok = inv_name and rep_name and inv_name == rep_name
            no_ok   = inv_no and rep_no and inv_no == rep_no
            if name_ok or no_ok:
                used_inv.add(ii); used_rep.add(ri)
                pairs.append({"inv_idx": ii, "rep_idx": ri,
                               "kind": "matched_cash", "note": "散客三重匹配"})
                break

    # ── 第 4 轮 · 税号编辑距离 ≤2 + 金额一致 → 疑似(Bug 4)
    for ii in range(n_inv):
        if ii in used_inv: continue
        inv = invoices[ii]
        t1 = normalize_tax_id(inv.get("buyer_tax_id") or "")
        if not t1 or len(t1) < 10:  # 太短不参与 fuzzy
            continue
        a1 = _get_inv_total(inv)
        best = None
        for ri in range(n_rep):
            if ri in used_rep: continue
            rep = report_rows[ri]
            t2 = normalize_tax_id(rep.get("report_buyer_tax_id") or "")
            if not t2 or len(t2) < 10: continue
            d = tax_id_fuzzy_distance(t1, t2)
            if d == 0 or d > 2: continue
            if not _eq_amount(a1, _get_rep_total(rep)): continue
            if best is None or d < best[1]:
                best = (ri, d)
        if best:
            ri, d = best
            used_inv.add(ii); used_rep.add(ri)
            pairs.append({"inv_idx": ii, "rep_idx": ri,
                           "kind": "fuzzy",
                           "note": f"税号差 {d} 位 · 请人工确认"})

    # ── 第 5 轮 · 发票税号空 + 报告反查(Bug 5 · OCR 漏抽)
    for ii in range(n_inv):
        if ii in used_inv: continue
        inv = invoices[ii]
        if normalize_tax_id(inv.get("buyer_tax_id") or ""):
            continue  # 有税号 · 不是 OCR 漏抽
        inv_name = normalize_str(inv.get("buyer_name") or "")
        inv_no   = normalize_invoice_no(inv.get("invoice_no") or "")
        inv_amt  = _get_inv_total(inv)
        for ri in range(n_rep):
            if ri in used_rep: continue
            rep = report_rows[ri]
            rep_tax = normalize_tax_id(rep.get("report_buyer_tax_id") or "")
            if not rep_tax: continue  # 报告这行也没税号 → 第 3 轮已处理
            rep_name = normalize_str(rep.get("report_buyer_name") or "")
            rep_no   = normalize_invoice_no(rep.get("report_invoice_no") or "")
            rep_amt  = _get_rep_total(rep)
            if not _eq_amount(inv_amt, rep_amt): continue
            name_ok = inv_name and rep_name and inv_name == rep_name
            no_ok   = inv_no and rep_no and inv_no == rep_no
            if name_ok and no_ok:
                used_inv.add(ii); used_rep.add(ri)
                pairs.append({"inv_idx": ii, "rep_idx": ri,
                               "kind": "ocr_missing",
                               "note": f"OCR 漏抽税号 · 实际应为 {rep_tax}"})
                break

    # ── 后处理 · 跨轮升级状态(第 1/2 轮匹配后才能定的标签)
    for p in pairs:
        if p["kind"] != "matched":  # fuzzy / matched_cash / ocr_missing 已定 · 不动
            continue
        inv = invoices[p["inv_idx"]]
        rep = report_rows[p["rep_idx"]]
        inv_tax = normalize_tax_id(inv.get("buyer_tax_id") or "")
        rep_tax = normalize_tax_id(rep.get("report_buyer_tax_id") or "")
        # 双方都无税号 · 实为散客匹配
        if not inv_tax and not rep_tax:
            p["kind"] = "matched_cash"
            p["note"] = "散客匹配"
            continue
        # 发票无税号 但 报告有 → OCR 漏抽(Bug 5)
        if not inv_tax and rep_tax:
            p["kind"] = "ocr_missing"
            p["note"] = f"OCR 漏抽税号 · 实际应为 {rep_tax}"

    unmatched_inv = [i for i in range(n_inv) if i not in used_inv]
    unmatched_rep = [i for i in range(n_rep) if i not in used_rep]
    return {"pairs": pairs, "unmatched_inv": unmatched_inv, "unmatched_rep": unmatched_rep}


def _diff_dims(inv: Dict, rep: Dict) -> Dict[str, str]:
    """v118.32.4.9.6.1 · 6 维度差异检测(发票号 / 日期 / 期间 / 税号 / 分公司 / 客户名)
    tax_id 值以 '~' 开头表示 fuzzy(编辑距离 ≤2) · 不含 '~' 为硬差异
    返回 dict · 值为空 = 无差异 · 非空 = 差异文案"""
    out = {"inv_no": "", "date": "", "period": "", "tax_id": "", "branch": "", "name": ""}
    # 发票号
    n1 = normalize_invoice_no(inv.get("invoice_no") or "")
    n2 = normalize_invoice_no(rep.get("report_invoice_no") or "")
    if n1 != n2 and (n1 or n2):
        out["inv_no"] = f"{inv.get('invoice_no') or '—'} ≠ {rep.get('report_invoice_no') or '—'}"
    # 日期
    d1 = parse_date(inv.get("invoice_date"))
    d2 = parse_date(rep.get("report_date"))
    if d1 and d2 and d1 != d2:
        delta = (d2 - d1).days
        out["date"] = f"差 {delta:+d} 天"
    elif (d1 is None) != (d2 is None):
        out["date"] = "日期一边缺"
    # 期间
    p1 = _derive_period(inv.get("invoice_date") or "", inv.get("period") or "")
    p2 = ""
    if d2:
        p2 = f"{d2.month:02d}/{d2.year}"
    if p1 and p2 and p1 != p2:
        out["period"] = f"{p1} ≠ {p2}"
    # 税号差异 (Bug 3 · v118.32.4.9.6.1)
    inv_tax = normalize_tax_id(inv.get("buyer_tax_id") or "")
    rep_tax = normalize_tax_id(rep.get("report_buyer_tax_id") or "")
    if (inv_tax or rep_tax) and inv_tax != rep_tax:
        raw1 = inv.get("buyer_tax_id") or inv_tax
        raw2 = rep.get("report_buyer_tax_id") or rep_tax
        if not inv_tax:
            out["tax_id"] = f"(发票空) · 报={raw2}"
        elif not rep_tax:
            out["tax_id"] = f"发={raw1} · (报告空)"
        else:
            _td = tax_id_fuzzy_distance(inv_tax, rep_tax)
            if _td <= 2:
                out["tax_id"] = f"~{raw1} ≈ {raw2}"  # ~ 前缀 = fuzzy
            else:
                out["tax_id"] = f"{raw1} ≠ {raw2}"
    # 分公司
    b1 = (inv.get("buyer_branch") or "").strip()
    b2 = (rep.get("report_buyer_branch") or "").strip()
    # 简单规范:总部相关词都归 00000
    def _norm_branch(s):
        if not s: return ""
        n = s.lower().replace(" ", "")
        if n in ("00000", "สำนักงานใหญ่", "head", "headoffice", "hq", "สนญ"):
            return "00000"
        return s
    if _norm_branch(b1) != _norm_branch(b2) and (b1 or b2):
        out["branch"] = f"{b1 or '—'} ≠ {b2 or '—'}"
    # 客户名
    name1 = (inv.get("buyer_name") or "").strip()
    name2 = (rep.get("report_buyer_name") or "").strip()
    if normalize_str(name1) != normalize_str(name2) and (name1 or name2):
        out["name"] = f"{name1 or '—'} ≠ {name2 or '—'}"
    return out


def extract_invoices_parallel(invoice_files: List[Dict[str, Any]],
                                api_key: Optional[str] = None,
                                max_workers: int = 10) -> List[Dict[str, Any]]:
    """v118.32.4.9.5 · 并行 10 路 OCR · 防止 1000 张串行跑死
    invoice_files: [{filename, bytes}]
    返回:同顺序的结果列表"""
    results: List[Optional[Dict]] = [None] * len(invoice_files)

    def _one(idx: int, f: Dict):
        results[idx] = extract_invoice_fields(f["bytes"], f["filename"], api_key=api_key)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_one, i, f) for i, f in enumerate(invoice_files)]
        for fut in as_completed(futures):
            try: fut.result()
            except Exception as e:
                logger.error(f"[vex.parallel] 单张抽取异常: {e}")
    return [r or {"ok": False, "error": "worker_returned_none"} for r in results]


# ════════════════════════════════════════════════════════════════════════
# v118.32.5 · 性能优化 B · 多发票批量 OCR（800+ 张场景，减少 5x API 调用）
# ════════════════════════════════════════════════════════════════════════
_INVOICE_BATCH_PROMPT = """You are reading {n} Thai tax invoices (ใบกำกับภาษี) attached in order: invoice_1, invoice_2, ..., invoice_{n}.

For EACH invoice, extract the SAME 8 fields. Do NOT interpret · do NOT match · do NOT clean.

Output JSON ONLY in this exact shape:
{{
  "invoices": [
    {{
      "index": 1,
      "buyer_tax_id": "...",
      "buyer_name":   "...",
      "buyer_branch": "...",
      "invoice_no":   "...",
      "invoice_date": "...",
      "period":       "...",
      "amount_pre_vat": 0.00,
      "vat_amount":     0.00,
      "total_amount":   0.00
    }},
    ... (one object per attached invoice, in same order)
  ]
}}

Field rules (identical to single-invoice mode):
- buyer_tax_id: 13-digit Thai tax ID of the BUYER · digits only · "" if missing
- buyer_name:   Buyer name EXACTLY as printed (keep prefixes like บริษัท ... จำกัด)
- buyer_branch: "สำนักงานใหญ่" or 5-digit code · "" if cash customer
- invoice_no:   Invoice number EXACTLY as printed · keep prefixes (INV/IV/TAX) · do NOT strip leading zeros
- invoice_date: Date EXACTLY as printed · format DD/MM/YYYY · keep BE year as printed
- period:       MM/YYYY (Gregorian only · BE-543 if Buddhist Era)
- amount_pre_vat / vat_amount / total_amount: number · 2 decimals · no commas

STRICT RULES:
1. Output exactly {n} objects in the same order as the attached files
2. If a field is partially visible or unreadable · output "" · do NOT guess
3. Cash customer → buyer_tax_id="" buyer_branch=""
4. Numbers: digits and dot only · no commas · no currency
"""


def _mime_for(filename: str) -> Optional[str]:
    ext = (filename or "").lower().rsplit(".", 1)[-1]
    return {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}.get(ext)


def extract_invoice_fields_batch(
    invoice_files: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    timeout: int = 90,
) -> List[Dict[str, Any]]:
    """一次 Gemini 调用抽取多张发票字段
    invoice_files: [{filename, bytes}]，建议 ≤ 5 张/批
    返回顺序与输入一致；任何一张失败/缺失 → 该 index 标记 ok=False
    """
    n = len(invoice_files)
    if n == 0:
        return []
    if n == 1:
        # 单张直接走原 single 流程，少一层包装
        f = invoice_files[0]
        return [extract_invoice_fields(f["bytes"], f["filename"], api_key=api_key)]

    # 校验 mime
    parts: List[Any] = [_INVOICE_BATCH_PROMPT.format(n=n)]
    for f in invoice_files:
        mime = _mime_for(f.get("filename") or "")
        if not mime:
            return [{"ok": False, "filename": x.get("filename"),
                     "error": "batch contains unsupported format"} for x in invoice_files]
        parts.append({"mime_type": mime, "data": f["bytes"]})

    try:
        import google.generativeai as genai
    except ImportError:
        return [{"ok": False, "filename": f.get("filename"),
                 "error": "google-generativeai 未安装"} for f in invoice_files]

    key = (api_key or os.environ.get("GEMINI_API_KEY")
           or os.environ.get("GOOGLE_API_KEY"))
    if not key:
        return [{"ok": False, "filename": f.get("filename"),
                 "error": "Gemini key 未配置"} for f in invoice_files]

    text = ""
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        )
        response = model.generate_content(
            parts,
            request_options={"timeout": timeout},
        )
        text = (response.text or "").strip()
        data = json.loads(text)
        items = data.get("invoices") or []
        _usage = getattr(response, "usage_metadata", None)
        _in_tok  = int(getattr(_usage, "prompt_token_count",     0) or 0)
        _out_tok = int(getattr(_usage, "candidates_token_count", 0) or 0)
        # token 均摊到每张
        _in_per  = _in_tok  // max(n, 1)
        _out_per = _out_tok // max(n, 1)

        out: List[Dict[str, Any]] = [None] * n  # type: ignore
        for r in items:
            try:
                idx = int(r.get("index", 0)) - 1
            except Exception:
                continue
            if not (0 <= idx < n):
                continue
            out[idx] = {
                "ok":              True,
                "filename":        invoice_files[idx].get("filename"),
                "buyer_tax_id":    str(r.get("buyer_tax_id") or "").strip(),
                "buyer_name":      str(r.get("buyer_name") or "").strip(),
                "buyer_branch":    str(r.get("buyer_branch") or "").strip(),
                "invoice_no":      str(r.get("invoice_no") or "").strip(),
                "invoice_date":    str(r.get("invoice_date") or "").strip(),
                "period":          str(r.get("period") or "").strip(),
                "amount_pre_vat":  _to_float(r.get("amount_pre_vat")),
                "vat_amount":      _to_float(r.get("vat_amount")),
                "total_amount":    _to_float(r.get("total_amount")),
                "_input_tokens":   _in_per,
                "_output_tokens":  _out_per,
                "_batch_size":     n,
            }
        # 漏掉的 index → 标 fail，调用方会 fallback 单张
        for i in range(n):
            if out[i] is None:
                out[i] = {"ok": False,
                          "filename": invoice_files[i].get("filename"),
                          "error": "batch_missing_index"}
        return out  # type: ignore
    except json.JSONDecodeError as e:
        logger.warning(f"[vex.batch] JSON 解析失败 n={n}: {e} · raw={text[:200]}")
        return [{"ok": False, "filename": f.get("filename"),
                 "error": f"AI 返回格式异常: {str(e)[:60]}"} for f in invoice_files]
    except Exception as e:
        logger.error(f"[vex.batch] n={n} 失败: {type(e).__name__}: {e}")
        return [{"ok": False, "filename": f.get("filename"),
                 "error": str(e)[:120]} for f in invoice_files]


def extract_invoices_batched_parallel(
    invoice_files: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    batch_size: int = 5,
    max_workers: int = 4,
    auto_fallback_single: bool = True,
) -> List[Dict[str, Any]]:
    """v118.32.5 · 批量 + 并行：
       - 每批 batch_size 张走一次 Gemini
       - 多批并行 max_workers 路
       - 批失败时 auto_fallback_single 自动回退单张重试（保证不丢数据）
    """
    n = len(invoice_files)
    if n == 0:
        return []
    results: List[Optional[Dict]] = [None] * n
    batches: List[Tuple[int, List[Dict[str, Any]]]] = []
    for start in range(0, n, batch_size):
        chunk = invoice_files[start:start + batch_size]
        batches.append((start, chunk))

    def _run_batch(start: int, chunk: List[Dict[str, Any]]):
        out = extract_invoice_fields_batch(chunk, api_key=api_key)
        # fallback：批失败 / 批内部分失败 → 单张重试
        if auto_fallback_single:
            for j, r in enumerate(out):
                if not (r and r.get("ok")):
                    try:
                        f = chunk[j]
                        out[j] = extract_invoice_fields(
                            f["bytes"], f["filename"], api_key=api_key
                        )
                    except Exception as e:
                        logger.error(f"[vex.batch] fallback 单张失败 {chunk[j].get('filename')}: {e}")
        for j, r in enumerate(out):
            results[start + j] = r

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_run_batch, s, c) for (s, c) in batches]
        for fut in as_completed(futures):
            try: fut.result()
            except Exception as e:
                logger.error(f"[vex.batch.parallel] 批失败: {e}")

    return [r or {"ok": False, "error": "worker_returned_none"} for r in results]


# ════════════════════════════════════════════════════════════════════════
# VAT 报告多份拼接 · 校验同卖方同期间
# ════════════════════════════════════════════════════════════════════════
def merge_vat_reports(report_files: List[Dict[str, Any]],
                       api_key: Optional[str] = None) -> Dict[str, Any]:
    """多份 VAT 报告 PDF 串行解析 · 拼接 rows · 校验同卖方同期间
    report_files: [{filename, bytes}]
    返回:{ok, rows, seller_name, seller_tax_id, period_year, period_month,
           sources(各文件解析摘要), error}
    """
    if not report_files:
        return {"ok": False, "error": "未上传 VAT 报告", "rows": []}

    parsed_list: List[Dict] = []
    sources: List[Dict] = []
    _rep_in_tok  = 0
    _rep_out_tok = 0
    for f in report_files:
        r = parse_vat_report(f["bytes"], f["filename"], api_key=api_key)
        if not r.get("ok"):
            return {"ok": False, "rows": [],
                    "error": f"「{f['filename']}」解析失败: {r.get('error', '未知')}"}
        parsed_list.append(r)
        _rep_in_tok  += int(r.get("_input_tokens")  or 0)
        _rep_out_tok += int(r.get("_output_tokens") or 0)
        sources.append({
            "filename": f["filename"],
            "row_count": r.get("row_count", len(r.get("rows", []))),
            "method": r.get("method", ""),
        })

    # 校验:多份必须同卖方 + 同期间(从第 1 份起对照)
    metas = [p.get("meta", {}) for p in parsed_list]
    sellers = set()
    periods = set()
    for m in metas:
        sid = m.get("seller_tax_id") or m.get("issuer_tax_id") or ""
        if sid:
            sellers.add(sid)
        per = (m.get("period_year"), m.get("period_month"))
        if all(per):
            periods.add(per)

    if len(sellers) > 1:
        return {"ok": False, "rows": [],
                "error": f"多份报告卖方不一致(税号: {' / '.join(sorted(sellers))})· 请检查"}
    if len(periods) > 1:
        return {"ok": False, "rows": [],
                "error": f"多份报告期间不一致 · 请检查"}

    # 合并 rows · 重排 row_no 连续递增
    all_rows: List[Dict] = []
    seq = 0
    for p in parsed_list:
        for row in p.get("rows", []):
            seq += 1
            row = dict(row)
            row["row_no"] = seq
            all_rows.append(row)

    seller_tax_id = (next(iter(sellers)) if sellers else "")
    seller_name = ""
    for m in metas:
        if m.get("seller_name"):
            seller_name = m["seller_name"]; break
    period_year = next(iter(periods))[0] if periods else None
    period_month = next(iter(periods))[1] if periods else None

    return {
        "ok": True,
        "rows": all_rows,
        "seller_tax_id":   seller_tax_id,
        "seller_name":     seller_name,
        "period_year":     period_year,
        "period_month":    period_month,
        "sources":         sources,
        "row_count":       len(all_rows),
        "_input_tokens":   _rep_in_tok,
        "_output_tokens":  _rep_out_tok,
    }


# ════════════════════════════════════════════════════════════════════════
# Excel 生成 · 4 sheet + 公式 + 条件格式
# ════════════════════════════════════════════════════════════════════════
# v118.32.4.9.6 · 4 语 Sheet 标题 + 列名 + 使用说明 + 5 维度差异列
# h_recon 改 15 列(一对一比对 + 6 维度独立显示):
# # | 状态 | 客户 | 发票号 | 期间 | 金额(发) | 金额(报) | 差异金额 |
# 发票号差 | 日期差 | 期间差 | 税号差 | 分公司差 | 客户名差 | 备注
_I18N = {
    "th": {
        "fname_prefix": "รายงานกระทบยอดภาษีขาย",
        "sh1": "รายการใบกำกับภาษี",
        "sh2": "รายงานภาษีขาย",
        "sh3": "กระทบยอด",
        "sh4": "วิธีใช้งาน",
        "h_inv":     ["#", "เลขผู้เสียภาษี", "ชื่อลูกค้า", "เลขที่ใบกำกับ", "วันที่",
                      "งวด", "ก่อนภาษี", "ภาษีมูลค่าเพิ่ม", "รวมทั้งสิ้น", "ไฟล์ต้นฉบับ", "ตรวจสอบ OCR"],
        "h_rep":     ["#", "เลขผู้เสียภาษี", "ชื่อลูกค้า", "วันที่", "งวด",
                      "ก่อนภาษี", "ภาษีมูลค่าเพิ่ม", "รวมทั้งสิ้น"],
        "h_recon":   ["#", "สถานะ", "ชื่อลูกค้า", "เลขใบกำกับ", "งวด",
                      "ยอด(ใบกำกับ)", "ยอด(รายงาน)", "ส่วนต่างยอด",
                      "เลขใบกำกับต่าง", "วันที่ต่าง", "งวดต่าง", "เลขภาษีต่าง", "สาขาต่าง", "ชื่อลูกค้าต่าง",
                      "หมายเหตุ"],
        "sum":       "รวม",
        "kpi_total": "ทั้งหมด", "kpi_ok": "ตรงกัน",
        "kpi_diff":  "ไม่ตรง", "kpi_amt": "ยอดต่างรวม",
        "st_ok":     "✓ ตรงกัน",
        "st_no_inv": "❗ มีในรายงาน · ไม่มีใบกำกับ",
        "st_no_rep": "❗ มีใบกำกับ · ไม่มีในรายงาน",
        "st_diff":   "⚠ ยอดต่างกัน",
        "st_fuzzy":  "🔍 คล้ายกัน · โปรดยืนยัน",
        "st_ocr_missing": "🟡 OCR อ่านเลขผู้เสียภาษีไม่ได้",
        "st_cash":          "✓ ลูกค้าทั่วไป(ตรงกัน)",
        "st_date_diff":     "⚠ วันที่ต่าง",
        "st_branch_diff":   "⚠ สาขาต่าง",
        "st_name_diff":     "⚠ ชื่อลูกค้าต่าง",
        "st_inv_no_diff":   "⚠ เลขใบกำกับต่าง",
        "st_tax_id_diff":   "⚠ เลขภาษีต่าง",
        "st_multi_diff":    "⚠ หลายรายการต่าง",
        "title":     "รายงานกระทบยอดภาษีขาย",
        "client":    "ลูกค้า", "period": "งวด",
        "help_lines": [
            "วิธีใช้งาน:",
            "1. Sheet รายการใบกำกับภาษี = ข้อมูลใบกำกับภาษีที่ AI อ่านได้ · แก้ไขตัวเลขได้ก่อนกระทบยอด",
            "2. Sheet รายงานภาษีขาย = รายงานภาษีขายจากสรรพากรที่ AI อ่านได้ · แก้ไขได้",
            "3. Sheet กระทบยอด = จับคู่ใบกำกับฯ กับรายงานภาษีขาย 1 ต่อ 1 · แสดงผลต่างแต่ละมิติในคอลัมน์อิสระ",
            "4. สถานะ: ✓ กระทบยอดได้ · ❗ ขาดด้านใดด้านหนึ่ง · ⚠ ยอดเงินต่างกัน · 🔍 เลขประจำตัวผู้เสียภาษีคล้ายกัน · 🟡 OCR อ่านเลขภาษีไม่ได้",
            "5. หากต้องการกระทบยอดใหม่ → แก้ไข Sheet 1 หรือ 2 แล้วสร้างไฟล์ Excel ใหม่",
        ],
        "ocr_col": "ตรวจสอบ OCR",
        "ocr_ok":  "✓ ผ่าน",
        "w_invoice_no_empty":  "ไม่มีเลขใบกำกับ",
        "w_buyer_name_empty":  "ไม่มีชื่อผู้ซื้อ",
        "w_tax_id_bad_length": "เลขภาษีไม่ใช่ 13 หลัก",
        "w_date_parse_fail":   "รูปแบบวันที่ผิดพลาด",
        "w_total_zero":        "ยอดรวมเป็น 0",
        "w_vat_rate_mismatch": "VAT ≠ 7%",
        "w_amount_sum_mismatch": "ก่อนVAT+VAT≠รวม",
    },
    "en": {
        "fname_prefix": "Sales_VAT_Reconciliation",
        "sh1": "Invoices", "sh2": "VAT_Report", "sh3": "Reconciliation", "sh4": "How_to_Use",
        "h_inv":   ["#", "Buyer Tax ID", "Buyer Name", "Invoice No", "Date", "Period",
                    "Pre-VAT", "VAT", "Total", "Source file", "OCR Check"],
        "h_rep":   ["#", "Buyer Tax ID", "Buyer Name", "Date", "Period",
                    "Pre-VAT", "VAT", "Total"],
        "h_recon": ["#", "Status", "Customer", "Invoice No", "Period",
                    "Amt (Inv)", "Amt (Rep)", "Amt Diff",
                    "Inv No Diff", "Date Diff", "Period Diff", "Tax ID Diff", "Branch Diff", "Name Diff",
                    "Note"],
        "sum": "Total",
        "kpi_total": "Total rows", "kpi_ok": "Matched", "kpi_diff": "Diff",
        "kpi_amt": "Total diff amount",
        "st_ok":     "✓ Match",
        "st_no_inv": "❗ In report · no invoice",
        "st_no_rep": "❗ Invoice · not in report",
        "st_diff":   "⚠ Amount mismatch",
        "st_fuzzy":  "🔍 Fuzzy · please confirm",
        "st_ocr_missing": "🟡 OCR missed tax ID",
        "st_cash":          "✓ Cash customer match",
        "st_date_diff":     "⚠ Date diff",
        "st_branch_diff":   "⚠ Branch diff",
        "st_name_diff":     "⚠ Name diff",
        "st_inv_no_diff":   "⚠ Invoice no diff",
        "st_tax_id_diff":   "⚠ Tax ID diff",
        "st_multi_diff":    "⚠ Multiple diffs",
        "title": "Sales VAT Reconciliation", "client": "Client", "period": "Period",
        "help_lines": [
            "How to use:",
            "1. 'Invoices' sheet = AI-extracted tax invoice data · edit values before reconciliation if needed",
            "2. 'VAT_Report' sheet = AI-extracted VAT report (Revenue Department submission) · editable",
            "3. 'Reconciliation' sheet = 1-to-1 match between invoices and VAT report · each difference shown as a separate column",
            "4. Status: ✓ Matched · ❗ One side only · ⚠ Amount mismatch · 🔍 Tax ID fuzzy · 🟡 OCR missed tax ID",
            "5. To re-reconcile → edit Sheet 1 or 2, then regenerate the Excel file",
        ],
        "ocr_col": "OCR Check",
        "ocr_ok":  "✓ OK",
        "w_invoice_no_empty":  "Invoice no. missing",
        "w_buyer_name_empty":  "Buyer name missing",
        "w_tax_id_bad_length": "Tax ID ≠ 13 digits",
        "w_date_parse_fail":   "Date format error",
        "w_total_zero":        "Total = 0",
        "w_vat_rate_mismatch": "VAT ≠ 7%",
        "w_amount_sum_mismatch": "Pre-VAT + VAT ≠ Total",
    },
    "zh": {
        "fname_prefix": "销项税对账表",
        "sh1": "发票明细", "sh2": "VAT 报告明细", "sh3": "对账结果", "sh4": "使用说明",
        "h_inv":   ["#", "买方税号", "客户名", "发票号", "日期", "期间", "不含税", "VAT", "含税", "原文件", "OCR 校验"],
        "h_rep":   ["#", "买方税号", "客户名", "日期", "期间", "不含税", "VAT", "含税"],
        "h_recon": ["#", "状态", "客户名", "发票号", "期间",
                    "金额(发)", "金额(报)", "差异金额",
                    "发票号差", "日期差", "期间差", "税号差", "分公司差", "客户名差",
                    "备注"],
        "sum": "合计",
        "kpi_total": "总笔数", "kpi_ok": "匹配数", "kpi_diff": "异常数", "kpi_amt": "异常金额合计",
        "st_ok":     "✓ 匹配",
        "st_no_inv": "❗ 报告有 · 发票无",
        "st_no_rep": "❗ 发票有 · 报告无",
        "st_diff":   "⚠ 金额不一致",
        "st_fuzzy":  "🔍 疑似匹配 · 请确认",
        "st_ocr_missing": "🟡 OCR 漏抽税号",
        "st_cash":          "✓ 散客匹配",
        "st_date_diff":     "⚠ 日期差异",
        "st_branch_diff":   "⚠ 分公司差异",
        "st_name_diff":     "⚠ 客户名差异",
        "st_inv_no_diff":   "⚠ 发票号差异",
        "st_tax_id_diff":   "⚠ 税号差异",
        "st_multi_diff":    "⚠ 多项差异",
        "title": "销项税对账表", "client": "客户", "period": "期间",
        "help_lines": [
            "使用说明:",
            "1. 「发票明细」Sheet = AI 读出的发票明细 · 可修改字段后再对账",
            "2. 「VAT 报告明细」Sheet = AI 读出的增值税销项税申报明细 · 可修改",
            "3. 「对账结果」Sheet = 发票与报告按发票号一对一比对 · 每个维度差异独立列显示",
            "4. 状态: ✓ 匹配 · ❗ 只一边有 · ⚠ 金额不一致 · 🔍 税号疑似 · 🟡 OCR 漏抽税号",
            "5. 想重新对账 → 改 Sheet 1 或 2 后重新生成 Excel",
        ],
        "ocr_col": "OCR 校验",
        "ocr_ok":  "✓ 通过",
        "w_invoice_no_empty":  "发票号空",
        "w_buyer_name_empty":  "客户名空",
        "w_tax_id_bad_length": "税号非13位",
        "w_date_parse_fail":   "日期格式异常",
        "w_total_zero":        "含税金额为0",
        "w_vat_rate_mismatch": "VAT≠7%",
        "w_amount_sum_mismatch": "净额+VAT≠总额",
    },
    "ja": {
        "fname_prefix": "売上VAT照合表",
        "sh1": "請求書明細", "sh2": "VAT報告明細", "sh3": "照合結果", "sh4": "使い方",
        "h_inv":   ["#", "買方税番号", "取引先名", "請求書番号", "日付", "期間",
                    "税抜", "VAT", "合計", "元ファイル", "OCR 確認"],
        "h_rep":   ["#", "買方税番号", "取引先名", "日付", "期間",
                    "税抜", "VAT", "合計"],
        "h_recon": ["#", "ステータス", "取引先名", "請求書番号", "期間",
                    "金額(請)", "金額(報)", "差額",
                    "番号差", "日付差", "期間差", "税番号差", "支店差", "名称差",
                    "備考"],
        "sum": "合計",
        "kpi_total": "件数", "kpi_ok": "一致", "kpi_diff": "不一致", "kpi_amt": "差額合計",
        "st_ok":     "✓ 一致",
        "st_no_inv": "❗ レポートのみ",
        "st_no_rep": "❗ 請求書のみ",
        "st_diff":   "⚠ 金額不一致",
        "st_fuzzy":  "🔍 類似 · 確認願います",
        "st_ocr_missing": "🟡 OCR 番号未取得",
        "st_cash":          "✓ 一般客一致",
        "st_date_diff":     "⚠ 日付差",
        "st_branch_diff":   "⚠ 支店差",
        "st_name_diff":     "⚠ 名称差",
        "st_inv_no_diff":   "⚠ 番号差",
        "st_tax_id_diff":   "⚠ 税番号差",
        "st_multi_diff":    "⚠ 複数不一致",
        "title": "売上 VAT 照合表", "client": "取引先", "period": "期間",
        "help_lines": [
            "使い方:",
            "1. 「請求書明細」シート = AI が読み取った適格請求書の明細 · 照合前に金額等を修正できます",
            "2. 「VAT報告明細」シート = AI が読み取った売上税報告書（歳入局提出分）· 編集可能",
            "3. 「照合結果」シート = 請求書と売上税報告書を請求書番号で 1 対 1 照合 · 差異を各列に分けて表示",
            "4. ステータス: ✓ 一致 · ❗ 片方のみ · ⚠ 金額不一致 · 🔍 納税者番号が類似 · 🟡 OCR で番号未取得",
            "5. 再照合する場合 → シート 1 または 2 を修正後、Excel ファイルを再生成してください",
        ],
        "ocr_col": "OCR 確認",
        "ocr_ok":  "✓ 正常",
        "w_invoice_no_empty":  "番号なし",
        "w_buyer_name_empty":  "取引先名なし",
        "w_tax_id_bad_length": "税番号13桁でない",
        "w_date_parse_fail":   "日付フォーマット異常",
        "w_total_zero":        "合計が0",
        "w_vat_rate_mismatch": "VAT≠7%",
        "w_amount_sum_mismatch": "税抜+VAT≠合計",
    },
}


def build_excel(invoices: List[Dict[str, Any]],
                  report_rows: List[Dict[str, Any]],
                  client_name: str = "",
                  client_tax_id: str = "",
                  period_year: Optional[int] = None,
                  period_month: Optional[int] = None,
                  lang: str = "th") -> bytes:
    """v118.32.4.9.6 · 生成 4-sheet Excel · 返回 xlsx bytes
    Bug 1-5 修复 + Sheet 3 一对一重做 + UI 美化(Sarabun/斑马/Tab 色/4 KPI 大卡)"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    if lang not in _I18N: lang = "th"
    L = _I18N[lang]

    wb = openpyxl.Workbook()

    # ── 通用样式(Sarabun 优先 · 泰文友好) ──
    FONT_NAME = "Sarabun"
    F_HEAD  = Font(name=FONT_NAME, size=11, bold=True, color="FFFFFF")
    F_NORM  = Font(name=FONT_NAME, size=10)
    F_BOLD  = Font(name=FONT_NAME, size=10, bold=True)
    F_TITLE = Font(name=FONT_NAME, size=18, bold=True, color="111827")
    # F_KPI_LBL / F_KPI_VAL removed in v4.10.23 (replaced by Korn-style inline KPI)
    F_DIFF_RED = Font(name=FONT_NAME, size=10, color="DC2626")

    FILL_HEAD   = PatternFill("solid", fgColor="2563EB")  # 蓝表头
    FILL_SUM    = PatternFill("solid", fgColor="EFF6FF")
    FILL_ZEBRA  = PatternFill("solid", fgColor="F9FAFB")  # 斑马偶数行
    FILL_OK     = PatternFill("solid", fgColor="DCFCE7")  # 绿底匹配
    FILL_DIFF   = PatternFill("solid", fgColor="FEF3C7")  # 黄底差异
    FILL_MISS   = PatternFill("solid", fgColor="FEE2E2")  # 红底缺一边
    FILL_FUZZY  = PatternFill("solid", fgColor="DBEAFE")  # 蓝底疑似
    FILL_OCRMSG = PatternFill("solid", fgColor="FED7AA")  # 橙底 OCR 漏抽
    # FILL_KPI_B/G/R/O removed in v4.10.23 (KPI row now uses EFF6FF bg + colored text)

    BORDER_TH = Border(left=Side(style="thin", color="E5E7EB"),
                       right=Side(style="thin", color="E5E7EB"),
                       top=Side(style="thin", color="E5E7EB"),
                       bottom=Side(style="thin", color="E5E7EB"))
    AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
    AL_R = Alignment(horizontal="right",  vertical="center")
    AL_L = Alignment(horizontal="left",   vertical="center", wrap_text=True)

    HEAD_HEIGHT = 32  # 表头行高 32
    ROW_HEIGHT  = 22

    def _style_header(ws, row, num_cols):
        for c in range(1, num_cols + 1):
            cell = ws.cell(row=row, column=c)
            cell.font = F_HEAD; cell.fill = FILL_HEAD; cell.alignment = AL_C
            cell.border = BORDER_TH
        ws.row_dimensions[row].height = HEAD_HEIGHT

    def _zebra(ws, start_row, end_row, num_cols):
        """偶数行(相对 start_row)斑马条纹"""
        for r in range(start_row, end_row + 1):
            if (r - start_row) % 2 == 1:
                for c in range(1, num_cols + 1):
                    cell = ws.cell(row=r, column=c)
                    if cell.fill.fgColor and cell.fill.fgColor.rgb in (None, "00000000"):
                        cell.fill = FILL_ZEBRA

    # ════════════ Sheet 1 · 发票明细 ════════════
    ws1 = wb.active
    ws1.title = L["sh1"]
    ws1.sheet_properties.tabColor = "2563EB"  # Tab 蓝
    headers1 = L["h_inv"]
    ws1.append(headers1)
    _style_header(ws1, 1, len(headers1))

    # v4.10.22 · OCR 校验色
    FILL_OCR_WARN = FILL_MISS   # 有问题 → 红底(复用)
    FILL_OCR_OK   = FILL_OK     # 全通过 → 绿底(复用)
    F_OCR_WARN = Font(name=FONT_NAME, size=10, color="DC2626")
    F_OCR_OK   = Font(name=FONT_NAME, size=10, color="16A34A", bold=True)

    # 校验问题 key → 发票明细列号对应关系
    _WARN_COL = {
        "w_invoice_no_empty":  4,
        "w_buyer_name_empty":  3,
        "w_tax_id_bad_length": 2,
        "w_date_parse_fail":   5,
        "w_total_zero":        9,
        "w_vat_rate_mismatch": 8,
        "w_amount_sum_mismatch": 9,
    }

    # v4.10.22 · 先收集每行 OCR 校验结果(稍后在样式循环后应用)
    _inv_ocr_warns: List[List[str]] = []
    for i, inv in enumerate(invoices, 1):
        # Bug 1 · 期间降级
        period_val = _derive_period(inv.get("invoice_date") or "", inv.get("period") or "")
        warn_keys = _ocr_validate_invoice(inv)
        _inv_ocr_warns.append(warn_keys)
        warn_text = " · ".join(L.get(k, k) for k in warn_keys)
        ws1.append([
            i,
            inv.get("buyer_tax_id") or "",
            inv.get("buyer_name")   or "",
            inv.get("invoice_no")   or "",
            inv.get("invoice_date") or "",
            period_val,
            inv.get("amount_pre_vat") or 0,
            inv.get("vat_amount")     or 0,
            inv.get("total_amount")   or 0,
            inv.get("filename")     or "",
            warn_text if warn_text else L.get("ocr_ok", "✓ OK"),
        ])

    # 合计行
    if invoices:
        last1 = len(invoices) + 1
        sum_row = last1 + 1
        ws1.cell(row=sum_row, column=1, value=L["sum"]).font = F_BOLD
        for col in (7, 8, 9):
            cell = ws1.cell(row=sum_row, column=col,
                            value=f"=SUM({get_column_letter(col)}2:{get_column_letter(col)}{last1})")
            cell.font = F_BOLD; cell.fill = FILL_SUM
        for c in range(1, len(headers1) + 1):
            ws1.cell(row=sum_row, column=c).fill = FILL_SUM
            ws1.cell(row=sum_row, column=c).border = BORDER_TH
            ws1.cell(row=sum_row, column=c).font = F_BOLD

    # 列宽 + 数字格式 + 斑马 + 行高(先统一设 F_NORM · 后面 OCR pass 再覆盖)
    widths1 = [5, 18, 28, 18, 13, 10, 14, 14, 14, 28, 30]
    for i, w in enumerate(widths1, 1):
        ws1.column_dimensions[get_column_letter(i)].width = w
    for r in range(2, len(invoices) + 2):
        ws1.row_dimensions[r].height = ROW_HEIGHT
        for c in range(1, len(headers1) + 1):
            cell = ws1.cell(row=r, column=c)
            cell.font = F_NORM
            cell.border = BORDER_TH
        for col in (7, 8, 9):
            ws1.cell(row=r, column=col).alignment = AL_R
            ws1.cell(row=r, column=col).number_format = "#,##0.00"
        ws1.cell(row=r, column=11).alignment = AL_L
    _zebra(ws1, 2, len(invoices) + 1, len(headers1))

    # v4.10.22 · OCR 高亮 pass(在通用样式之后应用 · 确保覆盖 F_NORM)
    for i, warn_keys in enumerate(_inv_ocr_warns, 1):
        data_row = i + 1
        ocr_cell = ws1.cell(row=data_row, column=11)
        if warn_keys:
            ocr_cell.fill = FILL_OCR_WARN
            ocr_cell.font = F_OCR_WARN
            for wk in warn_keys:
                col = _WARN_COL.get(wk)
                if col:
                    ws1.cell(row=data_row, column=col).fill = FILL_OCR_WARN
        else:
            ocr_cell.fill = FILL_OCR_OK
            ocr_cell.font = F_OCR_OK

    ws1.freeze_panes = "A2"

    # ════════════ Sheet 2 · VAT 报告明细 ════════════
    ws2 = wb.create_sheet(L["sh2"])
    ws2.sheet_properties.tabColor = "16A34A"  # Tab 绿
    headers2 = L["h_rep"]
    ws2.append(headers2)
    _style_header(ws2, 1, len(headers2))

    for i, row in enumerate(report_rows, 1):
        # Bug 1 · 期间降级 · 优先用 report_date 算 · fallback period_year/month
        date_str = row.get("report_date") or ""
        period_val = _derive_period(date_str, "")
        if not period_val and period_year and period_month:
            period_val = f"{period_month:02d}/{period_year}"
        pre = row.get("report_amount_pre_vat") or row.get("report_amount") or 0
        vat = row.get("report_vat_amount") or 0
        try:
            total = round(float(pre or 0) + float(vat or 0), 2)
        except Exception:
            total = 0
        ws2.append([
            i,
            row.get("report_buyer_tax_id") or "",
            row.get("report_buyer_name")   or "",
            date_str,
            period_val,
            pre, vat, total,
        ])

    if report_rows:
        last2 = len(report_rows) + 1
        sum_row2 = last2 + 1
        ws2.cell(row=sum_row2, column=1, value=L["sum"]).font = F_BOLD
        for col in (6, 7, 8):  # Sheet 2 数字列 偏移 1(加了 日期 列)
            cell = ws2.cell(row=sum_row2, column=col,
                            value=f"=SUM({get_column_letter(col)}2:{get_column_letter(col)}{last2})")
            cell.font = F_BOLD; cell.fill = FILL_SUM
        for c in range(1, len(headers2) + 1):
            ws2.cell(row=sum_row2, column=c).fill = FILL_SUM
            ws2.cell(row=sum_row2, column=c).border = BORDER_TH
            ws2.cell(row=sum_row2, column=c).font = F_BOLD

    widths2 = [5, 18, 28, 13, 12, 14, 14, 14]
    for i, w in enumerate(widths2, 1):
        ws2.column_dimensions[get_column_letter(i)].width = w
    for r in range(2, len(report_rows) + 2):
        ws2.row_dimensions[r].height = ROW_HEIGHT
        for c in range(1, len(headers2) + 1):
            cell = ws2.cell(row=r, column=c)
            cell.font = F_NORM
            cell.border = BORDER_TH
        for col in (6, 7, 8):
            ws2.cell(row=r, column=col).alignment = AL_R
            ws2.cell(row=r, column=col).number_format = "#,##0.00"
    _zebra(ws2, 2, len(report_rows) + 1, len(headers2))
    ws2.freeze_panes = "A2"

    # ════════════ Sheet 3 · 对账结果(一对一 15 列 · 后端预算结果)════════════
    ws3 = wb.create_sheet(L["sh3"])
    ws3.sheet_properties.tabColor = "D97706"  # Tab 橙

    # 跑配对(Bug 2/3/4/5 全在这里)
    match_result = _build_recon_pairs(invoices, report_rows)
    pairs = match_result["pairs"]
    unmatched_inv = match_result["unmatched_inv"]
    unmatched_rep = match_result["unmatched_rep"]

    # 计算 KPI
    n_total = len(pairs) + len(unmatched_inv) + len(unmatched_rep)
    n_ok = 0
    for _p in pairs:
        _inv = invoices[_p["inv_idx"]]; _rep = report_rows[_p["rep_idx"]]
        if not _eq_amount(_get_inv_total(_inv), _get_rep_total(_rep)): continue
        if _p["kind"] == "matched_cash":
            n_ok += 1
        elif _p["kind"] == "matched":
            _d = _diff_dims(_inv, _rep)
            if not any(_d.values()):
                n_ok += 1
    n_diff = n_total - n_ok
    diff_amount_total = 0.0
    for p in pairs:
        if p["kind"] in ("matched", "matched_cash"):
            a = _get_inv_total(invoices[p["inv_idx"]])
            b = _get_rep_total(report_rows[p["rep_idx"]])
            if not _eq_amount(a, b):
                diff_amount_total += abs(a - b)
    for ii in unmatched_inv:
        diff_amount_total += _get_inv_total(invoices[ii])
    for ri in unmatched_rep:
        diff_amount_total += _get_rep_total(report_rows[ri])

    # R1 · 标题行(Korn 样式 · 合并全行 · sz=18 · 高 36)
    _n_cols3 = len(L["h_recon"])
    ws3.merge_cells(f'A1:{get_column_letter(_n_cols3)}1')
    _c_title = ws3.cell(row=1, column=1, value=L["title"])
    _c_title.font = F_TITLE; _c_title.alignment = AL_C
    ws3.row_dimensions[1].height = 36

    # R2 · 客户+期间 meta
    meta_parts = []
    if client_name: meta_parts.append(f"{L['client']}: {client_name}")
    if period_year and period_month:
        meta_parts.append(f"{L['period']}: {period_month:02d}/{period_year}")
    if meta_parts:
        ws3.cell(row=2, column=1, value=" · ".join(meta_parts)).font = F_NORM

    # R3 · 空行

    # R4-R5 · KPI 4 大卡(每卡 4 列宽 · 共 16 列 · 彩色底色)
    F_KPI_LBL2  = Font(name=FONT_NAME, size=10, bold=True, color="FFFFFF")
    F_KPI_VAL2  = Font(name=FONT_NAME, size=22, bold=True, color="FFFFFF")
    FILL_KPI_B  = PatternFill("solid", fgColor="2563EB")
    FILL_KPI_G  = PatternFill("solid", fgColor="16A34A")
    FILL_KPI_R  = PatternFill("solid", fgColor="DC2626")
    FILL_KPI_O  = PatternFill("solid", fgColor="D97706")
    KPI_ROW_LBL = 4
    KPI_ROW_VAL = 5
    ws3.row_dimensions[KPI_ROW_LBL].height = 22
    ws3.row_dimensions[KPI_ROW_VAL].height = 44

    def _kpi(col_start, label, value, fill):
        ws3.merge_cells(start_row=KPI_ROW_LBL, start_column=col_start,
                        end_row=KPI_ROW_LBL,   end_column=col_start + 3)
        c1 = ws3.cell(row=KPI_ROW_LBL, column=col_start, value=label)
        c1.font = F_KPI_LBL2; c1.fill = fill; c1.alignment = AL_C
        ws3.merge_cells(start_row=KPI_ROW_VAL, start_column=col_start,
                        end_row=KPI_ROW_VAL,   end_column=col_start + 3)
        c2 = ws3.cell(row=KPI_ROW_VAL, column=col_start, value=value)
        c2.font = F_KPI_VAL2; c2.fill = fill; c2.alignment = AL_C

    _kpi(1, L["kpi_total"], n_total, FILL_KPI_B)
    _kpi(5, L["kpi_ok"],    n_ok,    FILL_KPI_G)
    _kpi(9, L["kpi_diff"],  n_diff,  FILL_KPI_R)
    _kpi(13, L["kpi_amt"],  f"฿ {diff_amount_total:,.2f}", FILL_KPI_O)

    # R6 · 表头(15 列)
    HEADER_ROW = 6
    DATA_START = 7
    headers3 = L["h_recon"]
    for c, h in enumerate(headers3, 1):
        cell = ws3.cell(row=HEADER_ROW, column=c, value=h)
        cell.font = F_HEAD; cell.fill = FILL_HEAD
        cell.alignment = AL_C; cell.border = BORDER_TH
    ws3.row_dimensions[HEADER_ROW].height = HEAD_HEIGHT

    # ── 写数据行 · 配对 + 孤儿
    def _status_for(pair, dims) -> tuple:
        """v118.32.4.10.0 · 维度感知状态判定 · 返回 (status_key, text, fill)"""
        kind = pair["kind"]
        if kind == "fuzzy":       return "st_fuzzy",       L["st_fuzzy"],       FILL_FUZZY
        if kind == "ocr_missing": return "st_ocr_missing", L["st_ocr_missing"], FILL_OCRMSG
        if dims.get("tax_id", "").startswith("~"):
            return "st_fuzzy", L["st_fuzzy"], FILL_FUZZY
        if kind == "matched_cash":
            a = _get_inv_total(invoices[pair["inv_idx"]])
            b = _get_rep_total(report_rows[pair["rep_idx"]])
            if _eq_amount(a, b): return "st_cash", L["st_cash"], FILL_OK
            return "st_diff", L["st_diff"], FILL_DIFF
        diff_keys = [k for k, v in dims.items() if v and not (k == "tax_id" and v.startswith("~"))]
        a = _get_inv_total(invoices[pair["inv_idx"]])
        b = _get_rep_total(report_rows[pair["rep_idx"]])
        if not _eq_amount(a, b): diff_keys.append("_amt")
        n = len(diff_keys)
        if n == 0: return "st_ok",         L["st_ok"],         FILL_OK
        if n >= 2: return "st_multi_diff", L["st_multi_diff"], FILL_DIFF
        key = diff_keys[0]
        if key == "_amt":             return "st_diff",        L["st_diff"],        FILL_DIFF
        if key in ("date", "period"): return "st_date_diff",   L["st_date_diff"],   FILL_DIFF
        if key == "branch":           return "st_branch_diff", L["st_branch_diff"], FILL_DIFF
        if key == "name":             return "st_name_diff",   L["st_name_diff"],   FILL_DIFF
        if key == "inv_no":           return "st_inv_no_diff", L["st_inv_no_diff"], FILL_DIFF
        if key == "tax_id":           return "st_tax_id_diff", L["st_tax_id_diff"], FILL_DIFF
        return "st_diff", L["st_diff"], FILL_DIFF

    row_cursor = DATA_START
    seq_no = 0
    diff_col_indices = (9, 10, 11, 12, 13, 14)  # 6 维度差异列(含税号差)
    F_FUZZY_BLUE = Font(name=FONT_NAME, size=10, color="2563EB")
    task_rows: List[Dict] = []  # v118.32.4.10.0 · 任务摘要行

    for pair in pairs:
        seq_no += 1
        inv = invoices[pair["inv_idx"]]
        rep = report_rows[pair["rep_idx"]]
        dims = _diff_dims(inv, rep)
        # Bug 2 · 散客:不比较/不显示分公司和税号差
        if pair["kind"] == "matched_cash":
            dims["branch"] = ""
            dims["tax_id"] = ""
        # tax_id fuzzy ~ 前缀处理(显示时去掉 · 用蓝色替换红色)
        tax_id_raw = dims.get("tax_id", "")
        tax_id_is_fuzzy = tax_id_raw.startswith("~")
        tax_id_display = tax_id_raw[1:] if tax_id_is_fuzzy else tax_id_raw
        status_key, status_text, row_fill = _status_for(pair, dims)
        amt_inv = _get_inv_total(inv)
        amt_rep = _get_rep_total(rep)
        amt_diff = round(amt_inv - amt_rep, 2)
        period_inv = _derive_period(inv.get("invoice_date") or "", inv.get("period") or "")

        # v4.10.13 · 净额/VAT 分字段差异备注
        amt_pre_inv = float(inv.get("amount_pre_vat") or 0)
        amt_vat_inv = float(inv.get("vat_amount") or 0)
        amt_pre_rep = float((rep.get("report_amount_pre_vat") or rep.get("report_amount")) or 0)
        amt_vat_rep = float(rep.get("report_vat_amount") or 0)
        pre_diff  = round(amt_pre_inv - amt_pre_rep, 2)
        vat_diff_ = round(amt_vat_inv - amt_vat_rep, 2)
        if not _eq_amount(amt_inv, amt_rep):
            if not _eq_amount(pre_diff, 0) and not _eq_amount(vat_diff_, 0):
                _amt_note = f"净额差 {pre_diff:+,.2f} · VAT 差 {vat_diff_:+,.2f}"
            elif not _eq_amount(pre_diff, 0):
                _amt_note = f"净额差 {pre_diff:+,.2f} · VAT 一致"
            else:
                _amt_note = f"VAT 差 {vat_diff_:+,.2f} · 净额一致"
        else:
            _amt_note = ""

        # v4.10.13 · ocr_missing · 备注追加提醒(dims 原样保留)
        _base_note = pair.get("note") or ""
        if pair["kind"] == "ocr_missing":
            _base_note = (_base_note + " · OCR 抽取可能不完整 · 请核对原 PDF").lstrip(" · ")
        _note_val = " · ".join(filter(None, [_base_note, _amt_note]))

        values = [
            seq_no,                                  # 1 #
            status_text,                              # 2 status
            inv.get("buyer_name") or rep.get("report_buyer_name") or "",  # 3 客户
            inv.get("invoice_no") or "",              # 4 发票号
            period_inv,                               # 5 期间
            amt_inv,                                  # 6 金额(发)
            amt_rep,                                  # 7 金额(报)
            amt_diff,                                 # 8 差异金额
            dims["inv_no"],                           # 9 发票号差
            dims["date"],                             # 10 日期差
            dims["period"],                           # 11 期间差
            tax_id_display,                           # 12 税号差(新)
            dims["branch"],                           # 13 分公司差
            dims["name"],                             # 14 客户名差
            _note_val,                                # 15 备注
        ]
        for c, v in enumerate(values, 1):
            cell = ws3.cell(row=row_cursor, column=c, value=v)
            cell.font = F_NORM
            cell.border = BORDER_TH
            cell.fill = row_fill
            if c in (6, 7, 8):
                cell.alignment = AL_R
                cell.number_format = "#,##0.00"
            elif c == 1:
                cell.alignment = AL_C
            else:
                cell.alignment = AL_L
            # 差异维度列若有内容 · 税号 fuzzy 蓝 · 其余红
            if c in diff_col_indices and v:
                if c == 12 and tax_id_is_fuzzy:
                    cell.font = F_FUZZY_BLUE
                else:
                    cell.font = F_DIFF_RED
        # v118.32.4.10.0 · 收集摘要行
        task_rows.append({
            "status_key": status_key,
            "status":     status_text,
            "customer":   inv.get("buyer_name") or rep.get("report_buyer_name") or "",
            "invoice_no": inv.get("invoice_no") or "",
            "amount_inv": amt_inv,
            "amount_rep": amt_rep,
            "dims":       {k: (v[1:] if k == "tax_id" and v.startswith("~") else v) for k, v in dims.items()},
            "kind":       pair["kind"],
        })
        ws3.row_dimensions[row_cursor].height = ROW_HEIGHT
        row_cursor += 1

    # 发票孤儿(报告无)
    for ii in unmatched_inv:
        seq_no += 1
        inv = invoices[ii]
        amt_inv = _get_inv_total(inv)
        period_inv = _derive_period(inv.get("invoice_date") or "", inv.get("period") or "")
        values = [seq_no, L["st_no_rep"],
                  inv.get("buyer_name") or "", inv.get("invoice_no") or "",
                  period_inv, amt_inv, 0, amt_inv,
                  "", "", "", "", "", "", ""]
        for c, v in enumerate(values, 1):
            cell = ws3.cell(row=row_cursor, column=c, value=v)
            cell.font = F_NORM; cell.border = BORDER_TH; cell.fill = FILL_MISS
            if c in (6, 7, 8):
                cell.alignment = AL_R; cell.number_format = "#,##0.00"
            elif c == 1:
                cell.alignment = AL_C
            else:
                cell.alignment = AL_L
        task_rows.append({
            "status_key": "st_no_rep", "status": L["st_no_rep"],
            "customer": inv.get("buyer_name") or "", "invoice_no": inv.get("invoice_no") or "",
            "amount_inv": amt_inv, "amount_rep": 0, "dims": {}, "kind": "invoice_orphan",
        })
        ws3.row_dimensions[row_cursor].height = ROW_HEIGHT
        row_cursor += 1

    # 报告孤儿(发票无)
    for ri in unmatched_rep:
        seq_no += 1
        rep = report_rows[ri]
        amt_rep = _get_rep_total(rep)
        rep_date = rep.get("report_date") or ""
        d = parse_date(rep_date)
        period_rep = f"{d.month:02d}/{d.year}" if d else ""
        values = [seq_no, L["st_no_inv"],
                  rep.get("report_buyer_name") or "", rep.get("report_invoice_no") or "",
                  period_rep, 0, amt_rep, -amt_rep,
                  "", "", "", "", "", "", ""]
        for c, v in enumerate(values, 1):
            cell = ws3.cell(row=row_cursor, column=c, value=v)
            cell.font = F_NORM; cell.border = BORDER_TH; cell.fill = FILL_MISS
            if c in (6, 7, 8):
                cell.alignment = AL_R; cell.number_format = "#,##0.00"
            elif c == 1:
                cell.alignment = AL_C
            else:
                cell.alignment = AL_L
        task_rows.append({
            "status_key": "st_no_inv", "status": L["st_no_inv"],
            "customer": rep.get("report_buyer_name") or "", "invoice_no": rep.get("report_invoice_no") or "",
            "amount_inv": 0, "amount_rep": amt_rep, "dims": {}, "kind": "report_orphan",
        })
        ws3.row_dimensions[row_cursor].height = ROW_HEIGHT
        row_cursor += 1

    # 列宽
    widths3 = [5, 22, 26, 16, 10, 14, 14, 13, 22, 14, 16, 22, 18, 26, 22]
    for i, w in enumerate(widths3, 1):
        ws3.column_dimensions[get_column_letter(i)].width = w
    ws3.freeze_panes = f"A{DATA_START}"

    # ════════════ Sheet 4 · 使用说明 ════════════
    ws4 = wb.create_sheet(L["sh4"])
    ws4.sheet_properties.tabColor = "6B7280"  # Tab 灰
    ws4.column_dimensions["A"].width = 100
    ws4.cell(row=1, column=1, value=L["title"]).font = F_TITLE
    ws4.row_dimensions[1].height = 28
    for i, line in enumerate(L["help_lines"], start=3):
        ws4.cell(row=i, column=1, value=line).font = F_NORM
        ws4.cell(row=i, column=1).alignment = AL_L
        ws4.row_dimensions[i].height = 22
    other_langs = [k for k in _I18N.keys() if k != lang]
    base_row = 3 + len(L["help_lines"]) + 2
    for lk in other_langs:
        for line in _I18N[lk]["help_lines"]:
            c = ws4.cell(row=base_row, column=1, value=line)
            c.font = Font(name=FONT_NAME, size=9, color="6B7280")
            c.alignment = AL_L
            base_row += 1
        base_row += 1

    # ── 保存为 bytes ──
    bio = io.BytesIO()
    wb.save(bio)
    task_summary = {
        "n_total": n_total,
        "n_ok": n_ok,
        "n_diff": n_diff,
        "diff_amount_total": round(diff_amount_total, 2),
        "rows": task_rows,
    }
    return bio.getvalue(), task_summary
