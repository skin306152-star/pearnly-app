# -*- coding: utf-8 -*-
"""
v118.32.0 · Pearnly · 销项税对账字段级对比引擎
9 字段 compare + 标准化工具
"""

import re
import unicodedata
from datetime import date, datetime
from typing import Optional, Dict, Any
from difflib import SequenceMatcher

# 泰文"总部"多种写法
_HQ_ALIASES = {"00000", "สำนักงานใหญ่", "สนญ", "head office", "hq", "หลัก", "สำนักงานหลัก"}


def normalize_str(s) -> str:
    """去首尾空格 · 全角→半角 · 大小写折叠"""
    if not s:
        return ""
    return unicodedata.normalize("NFKC", str(s)).strip().lower()


def normalize_name(s) -> str:
    """v118.32.2.5 · 姓名/公司名标准化:去所有空格(适合泰文/中文/日文 OCR 排版差) + 全角半角 + 大小写"""
    if not s:
        return ""
    v = unicodedata.normalize("NFKC", str(s)).lower()
    return re.sub(r"\s+", "", v)


def normalize_invoice_no(s) -> str:
    """v118.32.4.9 · 改"逐字段对照"模式 · 只做纯视觉归一化(空格/连字符/斜杠/大小写)
    不再剥离 INV/IV/TAX 前缀 —— 那是替用户判定"INV 和 IV 是同一笔"违反新铁律
    前导零也保留(用户视觉看到的写法)"""
    if not s:
        return ""
    return normalize_str(s).replace(" ", "").replace("-", "").replace("/", "")


def normalize_tax_id(s) -> str:
    """去连字符和空格,只留数字"""
    return re.sub(r"[^0-9]", "", str(s or ""))


def normalize_branch(s) -> str:
    """总部多种写法归一为 '00000'"""
    if not s:
        return "00000"
    n = normalize_str(s).replace(" ", "")
    # 别名集合走同款归一化(NFKC + lower + 去空格)再比 ·
    # 否则带空格的 "head office" / 泰文 "สำนักงานใหญ่"(NFKC 拆 ำ)永远匹配不上
    hq_norm = {normalize_str(v).replace(" ", "") for v in _HQ_ALIASES}
    if n in hq_norm or n == "":
        return "00000"
    if n.isdigit():
        return n.zfill(5)
    return n


def _thai_to_gregorian(year: int) -> int:
    """佛历年→西历年。
    · 2 位年(<100):泰国财税文档一律佛历缩写(25xx),2500+yy 佛历 → 西历(=1957+yy);
      如 69→พ.ศ.2569→2026。Python %y 会把这类年扩成 19xx/20xx 西历,须先取回 2 位再折算。
    · 4 位佛历(>2400):-543。
    · 4 位西历:原样返回。
    """
    if year < 100:
        return 1957 + year  # 2500 + yy − 543
    return year - 543 if year > 2400 else year


def parse_date(s) -> Optional[date]:
    """解析日期字符串,支持多种格式 + 佛历自动转换。
    2 位年份按泰国财税惯例视作佛历缩写(25xx),不套用 Python %y 的西历假设。
    """
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            d = datetime.strptime(s, fmt).date()
        except ValueError:
            continue
        # %y 已被 strptime 扩成 4 位西历(69→1969),取回 2 位交佛历折算
        year = d.year % 100 if "%y" in fmt else d.year
        return d.replace(year=_thai_to_gregorian(year))
    return None


def fuzzy_ratio(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def levenshtein(a: str, b: str) -> int:
    """v118.32.4.9.6 · 编辑距离 · 用于税号 fuzzy 疑似匹配(Bug 4)
    a/b 都是数字串(已 normalize_tax_id 过)· 不考虑 unicode 重码"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def tax_id_fuzzy_distance(t1: str, t2: str) -> int:
    """v118.32.4.9.6 · 税号 fuzzy 距离(Bug 4)
    两边都先 normalize_tax_id · 返回编辑距离
    距离 ≤ 2 → 调用方标"疑似匹配 · 请确认" · 不直接判定"""
    n1 = normalize_tax_id(t1)
    n2 = normalize_tax_id(t2)
    if not n1 or not n2:
        return 99
    return levenshtein(n1, n2)


def mod11_check(tax_id: str) -> bool:
    """泰国 13 位税号 Mod-11 校验"""
    digits = normalize_tax_id(tax_id)
    if len(digits) != 13:
        return False
    try:
        total = sum(int(d) * w for d, w in zip(digits, range(13, 1, -1)))
        return (11 - total % 11) % 10 == int(digits[-1])
    except Exception:
        return False


def _r(matched: bool, delta: str = "", category: str = "") -> Dict[str, Any]:
    return {"matched": matched, "delta": delta, "category": category}


def compare_field(field_name: str, invoice_val, report_val) -> Dict[str, Any]:
    """单字段对比,返回 {matched, delta, category}"""
    f = field_name.lower()

    # 字段 3 · 日期
    if f in ("date", "document_date", "invoice_date"):
        d1, d2 = parse_date(invoice_val), parse_date(report_val)
        if d1 is None or d2 is None:
            return _r(False, "日期无法解析", "date_parse_error")
        delta = (d2 - d1).days
        if delta == 0:
            return _r(True)
        if abs(delta) <= 1:
            return _r(False, f"差 {delta:+d} 天", "date_diff")
        if abs(delta) > 20:
            return _r(False, f"差 {delta:+d} 天(跨期)", "date_period_mismatch")
        return _r(False, f"差 {delta:+d} 天", "date_diff")

    # 字段 4 · 发票号 · v118.32.4.9 · 砍前缀差细分 · 不归一化判定
    if f in ("invoice_no", "document_no", "doc_no"):
        n1 = normalize_invoice_no(invoice_val)
        n2 = normalize_invoice_no(report_val)
        if n1 == n2 and n1:
            return _r(True)
        return _r(False, f"{invoice_val} ≠ {report_val}", "invoice_no_mismatch")

    # 字段 5 · 买方名称 · v118.32.4.9 · 砍 fuzzy 0.92 自动判定 · 如实展示差异
    if f in ("buyer_name", "customer_name"):
        a = normalize_name(invoice_val)
        b = normalize_name(report_val)
        if a == b and a:
            return _r(True)
        return _r(False, f"{invoice_val} ≠ {report_val}", "name_mismatch")

    # 字段 6 · 买方税号
    if f in ("buyer_tax_id", "customer_tax_id"):
        if not invoice_val and not report_val:
            return _r(True)  # 个人买家双空
        t1 = normalize_tax_id(str(invoice_val or ""))
        t2 = normalize_tax_id(str(report_val or ""))
        if t1 == t2:
            return _r(True)
        return _r(False, f"{invoice_val} ≠ {report_val}", "tax_id_mismatch")

    # 字段 7 · 买方分支
    if f in ("buyer_branch", "customer_branch"):
        if not invoice_val and not report_val:
            return _r(True)
        b1 = normalize_branch(str(invoice_val or ""))
        b2 = normalize_branch(str(report_val or ""))
        if b1 == b2:
            return _r(True)
        return _r(False, f"{b1} ≠ {b2}", "branch_mismatch")

    # 字段 8 · 不含税金额
    if f in ("amount_pre_vat", "net_amount"):
        try:
            v1 = float(str(invoice_val or 0).replace(",", ""))
            v2 = float(str(report_val or 0).replace(",", ""))
            diff = abs(v1 - v2)
            if diff <= 0.01:
                return _r(True)
            return _r(False, f"差 {v2 - v1:+.2f}", "amount_diff")
        except Exception:
            return _r(False, "金额无法解析", "amount_parse_error")

    # 字段 9 · 销项税额 · v118.32.4.9 · 砍 0.10 内"精度容忍"判定 · >0.01 即标差异
    if f in ("vat_amount", "tax_amount", "output_vat"):
        try:
            v1 = float(str(invoice_val or 0).replace(",", ""))
            v2 = float(str(report_val or 0).replace(",", ""))
            if abs(v1 - v2) <= 0.01:
                return _r(True)
            return _r(False, f"差 {v2 - v1:+.2f}", "vat_diff")
        except Exception:
            return _r(False, "税额无法解析", "amount_parse_error")

    # 默认字符串严格比较
    a = normalize_str(invoice_val)
    b = normalize_str(report_val)
    return _r(a == b, "" if a == b else f"{invoice_val} ≠ {report_val}")


# 字段名 → (invoice_key, report_key) 映射
_FIELD_MAP = [
    ("date", "invoice_date", "report_date"),
    ("invoice_no", "invoice_no", "report_invoice_no"),
    ("buyer_name", "buyer_name", "report_buyer_name"),
    ("buyer_tax_id", "buyer_tax_id", "report_buyer_tax_id"),
    ("buyer_branch", "buyer_branch", "report_buyer_branch"),
    ("amount_pre_vat", "amount_pre_vat", "report_amount_pre_vat"),
    ("vat_amount", "vat_amount", "report_vat_amount"),
]


def compare_all_fields(
    invoice_row: Dict, report_row: Dict, skip_buyer: bool = False
) -> Dict[str, Any]:
    """
    对一对已配对的行跑全部字段对比
    skip_buyer=True → 跳过字段 6/7(个人买家,铁律 61-VAT)
    返回 {fields, categories, has_diff}
    """
    fields: Dict[str, Any] = {}
    categories = set()
    for field_name, inv_key, rep_key in _FIELD_MAP:
        if skip_buyer and field_name in ("buyer_tax_id", "buyer_branch"):
            continue
        r = compare_field(field_name, invoice_row.get(inv_key), report_row.get(rep_key))
        fields[field_name] = r
        if not r["matched"] and r["category"]:
            categories.add(r["category"])
    return {
        "fields": fields,
        "categories": sorted(categories),
        "has_diff": any(not v["matched"] for v in fields.values()),
    }
