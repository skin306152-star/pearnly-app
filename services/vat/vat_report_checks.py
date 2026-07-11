# -*- coding: utf-8 -*-
"""销项税报告三查(纯函数·N1-a)。

消费 vat_report_parser.parse_vat_report 的 parsed_rows,不改其一行、不进配对引擎
vat_recon_core —— 三查是报告自身的静态自查,不需要发票库参与。

三查:
  1. check_invoice_sequence  连号(缺号/乱序/重复/作废/格式笔误)
  2. check_buyer_summary     买家分组(按税号聚合·分店自然归并·Decimal 全程)
  3. check_period_consistency 期间一致性(每行日期落在申报期内)

连号号型(泰国销项报告实证三型):
  - 传统数字连号:前缀 + 分隔符 + 纯数字尾号(如 IV69/00512、IV69/06-001),
    按尾号 min~max 差集找缺号。
  - 日期编码号:前缀 + 6 位数字(年月日)+ "-" + 定长序号(如 7-Eleven 的
    IV6906DD-001),按日历天查缺,不落入数字断号逻辑。
  - 格式笔误:多/少分隔符等偏离同组多数派签名的写法(如 IV69//06-018、
    IV6906-021),复用 services/ocr/invoice_no.py 的多数派签名裁定,不吞进
    缺号计算,也不误判成另一个号型。
"""

from __future__ import annotations

import calendar
import re
from collections import Counter, defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from services.ocr.invoice_no import inconsistent_indices

_TOKEN_RE = re.compile(r"[A-Za-z]+|\d+")
_DATE_CODE_RE = re.compile(r"^([A-Za-z]+)(\d{2})(\d{2})(\d{2})-(\d+)$")

_Member = Tuple[int, str, str]  # (row_index, clean_invoice_no, last_token)


def _strip_void(raw: str) -> Tuple[str, bool]:
    """去掉作废标记 '*'(前缀或后缀均认)。"""
    is_void = raw.startswith("*") or raw.endswith("*")
    return raw.strip("*").strip(), is_void


def _tokens(invoice_no: str) -> List[str]:
    return _TOKEN_RE.findall(invoice_no)


def _split_date_coded(
    items: List[Tuple[int, str]],
) -> Tuple[Dict[Tuple[str, str, str, str], List[Tuple[int, str, int]]], List[Tuple[int, str]]]:
    """挑出「前缀+年月日6位+ -序号」型(如 IV6906DD-001)· 按(前缀,年,月,序号)分组,
    同组内只有日部分变化 → 判定日期编码号。size<2 的候选退回传统数字连号处理,
    避免把巧合命中正则的孤例误判。
    """
    buckets: Dict[Tuple[str, str, str, str], List[Tuple[int, str, int]]] = defaultdict(list)
    rest: List[Tuple[int, str]] = []
    for idx, inv in items:
        m = _DATE_CODE_RE.match(inv)
        if not m:
            rest.append((idx, inv))
            continue
        prefix, yy, mm, dd, seq = m.groups()
        day, month = int(dd), int(mm)
        if not (1 <= day <= 31) or not (1 <= month <= 12):
            rest.append((idx, inv))
            continue
        buckets[(prefix, yy, mm, seq)].append((idx, inv, day))

    date_families = {k: v for k, v in buckets.items() if len(v) >= 2}
    for key, members in buckets.items():
        if key not in date_families:
            rest.extend((idx, inv) for idx, inv, _ in members)
    return date_families, rest


def _modal_length(members: List[_Member]) -> int:
    lengths = Counter(len(t) for (_, _, t) in members)
    return lengths.most_common(1)[0][0]


def _build_numeric_families(items: List[Tuple[int, str]]) -> Dict[Tuple[str, ...], List[_Member]]:
    """按 token 化前缀分组(字母/数字段·标点忽略)。前缀相同 → 同一编号序列。

    分隔符缺失会把两段数字粘成一个 token(如 IV6906-021 的 "6906"),
    与已成型的大组(size>=2)按"前缀 token 拼接后字符串相等 + 尾号位数吻合"
    做二次合并,这类孤例本身就是要另揪出的格式笔误,不该让它把该号单独
    误判成"独立断号序列"或漏统计进正确的缺号范围。
    """
    raw_families: Dict[Tuple[str, ...], List[_Member]] = defaultdict(list)
    for idx, inv in items:
        toks = _tokens(inv)
        if len(toks) < 2:
            continue
        prefix, last = tuple(toks[:-1]), toks[-1]
        raw_families[prefix].append((idx, inv, last))

    canonical_keys = sorted(
        (k for k, v in raw_families.items() if len(v) >= 2),
        key=lambda k: -len(raw_families[k]),
    )
    orphan_keys = [k for k, v in raw_families.items() if len(v) == 1 and k not in canonical_keys]
    for key in orphan_keys:
        member = raw_families[key][0]
        joined = "".join(key)
        for ck in canonical_keys:
            if joined == "".join(ck) and len(member[2]) == _modal_length(raw_families[ck]):
                raw_families[ck].append(member)
                del raw_families[key]
                break
    return raw_families


def _numeric_family_result(
    key: Tuple[str, ...], members: List[_Member], date_by_idx: Dict[int, str]
) -> Dict[str, Any]:
    nums = [int(t) for (_, _, t) in members]
    lo, hi = min(nums), max(nums)
    present = set(nums)
    missing = sorted(n for n in range(lo, hi + 1) if n not in present)
    counts = Counter(nums)
    duplicates = sorted(n for n, c in counts.items() if c > 1)

    ordered = sorted(members, key=lambda m: int(m[2]))
    out_of_order: List[str] = []
    running_max_date: Optional[str] = None
    for row_idx, inv, _ in ordered:
        d = date_by_idx.get(row_idx)
        if not d:
            continue
        if running_max_date is not None and d < running_max_date:
            out_of_order.append(inv)
        else:
            running_max_date = d

    raw_strings = [inv for (_, inv, _) in members]
    anomaly_idx = inconsistent_indices(raw_strings)

    return {
        "type": "numeric",
        "label": "".join(key),
        "invoice_numbers": raw_strings,
        "count": len(members),
        "min": lo,
        "max": hi,
        "missing": missing,
        "duplicates": duplicates,
        "out_of_order": out_of_order,
        "format_anomalies": [raw_strings[i] for i in anomaly_idx],
    }


def _date_coded_family_result(
    key: Tuple[str, str, str, str],
    members: List[Tuple[int, str, int]],
    period_year: Optional[int],
    period_month: Optional[int],
) -> Dict[str, Any]:
    prefix, yy, mm, seq = key
    days = sorted(set(day for (_, _, day) in members))
    if period_year and period_month:
        days_in_month = calendar.monthrange(period_year, period_month)[1]
    else:
        days_in_month = max(days) if days else 0
    missing_days = sorted(set(range(1, days_in_month + 1)) - set(days))
    counts = Counter(day for (_, _, day) in members)
    duplicate_days = sorted(d for d, c in counts.items() if c > 1)

    return {
        "type": "date_coded",
        "label": f"{prefix}{yy}{mm}DD-{seq}",
        "invoice_numbers": [inv for (_, inv, _) in members],
        "count": len(members),
        "days_present": days,
        "missing_days": missing_days,
        "duplicate_days": duplicate_days,
    }


def check_invoice_sequence(
    rows: List[Dict[str, Any]],
    period_year: Optional[int] = None,
    period_month: Optional[int] = None,
) -> Dict[str, Any]:
    """连号检查:号型分流(日期编码优先剔出)+ 缺号/乱序/重复/作废/格式笔误。"""
    date_by_idx: Dict[int, str] = {}
    void_invoices: List[Dict[str, Any]] = []
    items: List[Tuple[int, str]] = []

    for idx, row in enumerate(rows):
        raw = str(row.get("report_invoice_no") or "").strip()
        if not raw:
            continue
        clean, is_void = _strip_void(raw)
        if not clean:
            continue
        date_by_idx[idx] = str(row.get("report_date") or "")
        if is_void:
            void_invoices.append(
                {
                    "invoice_no": clean,
                    "row_no": row.get("row_no"),
                    "date": row.get("report_date"),
                }
            )
        items.append((idx, clean))

    date_families, rest = _split_date_coded(items)
    numeric_families = _build_numeric_families(rest)

    families: List[Dict[str, Any]] = []
    for key, members in date_families.items():
        families.append(_date_coded_family_result(key, members, period_year, period_month))
    for key, members in numeric_families.items():
        families.append(_numeric_family_result(key, members, date_by_idx))

    format_anomalies: List[str] = []
    for fam in families:
        format_anomalies.extend(fam.get("format_anomalies") or [])

    dup_counter = Counter(inv for _, inv in items)
    duplicate_invoices = sorted(inv for inv, c in dup_counter.items() if c > 1)

    return {
        "families": families,
        "void_invoices": void_invoices,
        "format_anomalies": format_anomalies,
        "duplicate_invoices": duplicate_invoices,
    }


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def check_buyer_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """按 buyer_tax_id 聚合(分店天然归并到税号)· 每买家一行 · Decimal 全程。"""
    groups: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []

    for row in rows:
        tax_id = str(row.get("report_buyer_tax_id") or "").strip()
        name = str(row.get("report_buyer_name") or "").strip()
        key = tax_id or f"__no_tax_id__{name}"
        if key not in groups:
            groups[key] = {
                "tax_id": tax_id,
                "names": Counter(),
                "count": 0,
                "net_total": Decimal("0"),
                "vat_total": Decimal("0"),
                "amount_total": Decimal("0"),
            }
            order.append(key)
        g = groups[key]
        g["names"][name] += 1
        g["count"] += 1
        net = _to_decimal(row.get("report_amount_pre_vat"))
        vat = _to_decimal(row.get("report_vat_amount"))
        amount_raw = row.get("report_amount")
        g["net_total"] += net
        g["vat_total"] += vat
        g["amount_total"] += _to_decimal(amount_raw) if amount_raw is not None else net + vat

    buyers = []
    grand = {
        "invoice_count": 0,
        "net_total": Decimal("0"),
        "vat_total": Decimal("0"),
        "amount_total": Decimal("0"),
    }
    for key in order:
        g = groups[key]
        rep_name = g["names"].most_common(1)[0][0] if g["names"] else ""
        buyers.append(
            {
                "tax_id": g["tax_id"],
                "buyer_name": rep_name,
                "invoice_count": g["count"],
                "net_total": g["net_total"],
                "vat_total": g["vat_total"],
                "amount_total": g["amount_total"],
            }
        )
        grand["invoice_count"] += g["count"]
        grand["net_total"] += g["net_total"]
        grand["vat_total"] += g["vat_total"]
        grand["amount_total"] += g["amount_total"]

    buyers.sort(key=lambda b: b["invoice_count"], reverse=True)
    return {"buyers": buyers, "grand_total": grand}


def _detect_period(rows: List[Dict[str, Any]]) -> Tuple[Optional[int], Optional[int]]:
    counts: Counter = Counter()
    for row in rows:
        d = str(row.get("report_date") or "")
        if len(d) >= 7 and d[4] == "-":
            counts[d[:7]] += 1
    if not counts:
        return None, None
    ym = counts.most_common(1)[0][0]
    year_str, month_str = ym.split("-")
    return int(year_str), int(month_str)


def check_period_consistency(
    rows: List[Dict[str, Any]],
    period_year: Optional[int] = None,
    period_month: Optional[int] = None,
) -> Dict[str, Any]:
    """每行日期须落在申报期内(period 由报告头/调用方给·缺省取行日期众数)。"""
    if period_year is None or period_month is None:
        period_year, period_month = _detect_period(rows)

    out_of_period: List[Dict[str, Any]] = []
    if period_year and period_month:
        target = f"{period_year:04d}-{period_month:02d}"
        for row in rows:
            d = str(row.get("report_date") or "")
            if d and not d.startswith(target):
                out_of_period.append(
                    {
                        "invoice_no": row.get("report_invoice_no"),
                        "row_no": row.get("row_no"),
                        "date": d,
                    }
                )

    return {
        "period_year": period_year,
        "period_month": period_month,
        "out_of_period": out_of_period,
    }


def run_report_checks(
    rows: List[Dict[str, Any]],
    period_year: Optional[int] = None,
    period_month: Optional[int] = None,
) -> Dict[str, Any]:
    """三查一次跑齐(供端点直接调用)。"""
    period = check_period_consistency(rows, period_year, period_month)
    sequence = check_invoice_sequence(rows, period.get("period_year"), period.get("period_month"))
    return {
        "sequence": sequence,
        "buyer_summary": check_buyer_summary(rows),
        "period": period,
    }


def to_jsonable(obj: Any) -> Any:
    """Decimal → float(仅出线序列化边界·内部计算全程 Decimal)。"""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    return obj
