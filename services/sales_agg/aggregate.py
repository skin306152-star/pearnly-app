# -*- coding: utf-8 -*-
"""SA-1 聚合核心:三渠道行级输入 → 按日/按渠道销售汇总 + 建议月合计(纯函数,零 I/O)。

纳入规则(方案 §4 EDC 口径定案):销项 = EDC 毛额 + 销售税票票面额;银行到账永不计入
销售,只当交叉核对与缺口探测(到账+手续费≈毛额)。判不了的行(缺日期/缺毛额/方向不对)
一律进 conflicts 点名——绝不静默吞也绝不硬猜。聚合结果是权威源【候选】,采用权在会计
(SA-2 裁决卡),每个数字都带源行引用可回查。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Optional

from services.recon.field_comparator import normalize_invoice_no
from services.sales_agg import linker, vat
from services.sales_agg.model import BankCredit, EdcSettlement, SalesDoc

INCLUSION_RULES = {
    "edc_settlement": "counted:gross(ยอดขาย 毛额口径;手续费只点名不冲减,银行到账不重计)",
    "sales_doc": "counted:face_total(票面含税额;与 EDC 同日共存不自动判重,疑似逐笔点名)",
    "bank_credit": "excluded:cross_check_only(到账=结算净额,计入即与 EDC 毛额双计)",
}
NOTE_BANK_ABSENT = "bank_channel_absent:未提供银行入账,交叉核对与缺口探测未执行"

_ZERO = Decimal("0")


def aggregate_month(
    edc_payloads: list[dict], bank_payloads: list[dict], doc_payloads: list[dict]
) -> dict:
    """三渠道 payload 列表 → 聚合报告。报告内钱字段全为字符串(Decimal 算出后定格),
    日期全为 ISO 字符串,可直接 json 序列化。"""
    conflicts: list[dict] = []
    notes: list[str] = []

    edc_rows = _adapt(edc_payloads, EdcSettlement.adapt, "edc", conflicts)
    bank_rows = _adapt(bank_payloads, BankCredit.adapt, "bank", conflicts)
    doc_rows = _adapt(doc_payloads, SalesDoc.adapt, "doc", conflicts)

    edc_ok, edc_dups = _dedupe([r for r in edc_rows if r.usable], _edc_fingerprint)
    bank_ok, bank_dups = _dedupe([r for r in bank_rows if r.usable], _bank_fingerprint)
    doc_ok, doc_dups = _dedupe_docs([r for r in doc_rows if r.usable], conflicts)

    conflicts.extend(linker.edc_internal_conflicts(edc_ok))
    links, link_conflicts, matched_bank, matched_edc = linker.link_settlements(edc_ok, bank_ok)
    conflicts.extend(link_conflicts)
    edc_days = {r.day for r in edc_ok}
    conflicts.extend(linker.overlap_suspects(doc_ok, edc_days))

    if bank_ok:
        gaps = _gaps(edc_ok, bank_ok, doc_ok, matched_bank, matched_edc)
    else:
        gaps = []
        notes.append(NOTE_BANK_ABSENT)

    daily = _daily(edc_ok, doc_ok)
    report = vat.split_report([r.gross for r in edc_ok] + [r.gross for r in doc_ok])
    month_total = {
        "gross": str(report["gross_total"]),
        "sales_amount": str(report["sales_amount"]),
        "output_vat": str(report["output_vat"]),
        "per_line_sales": str(report["per_line_sales"]),
        "per_line_vat": str(report["per_line_vat"]),
        "vat_method_diff": str(report["vat_method_diff"]),
        "vat_method": "aggregate_first",
    }

    return {
        "daily": daily,
        "by_channel": {
            "edc_settlement": _edc_channel(edc_rows, edc_ok, edc_dups),
            "bank_credit": _bank_channel(bank_rows, bank_ok, bank_dups, matched_bank),
            "sales_doc": _doc_channel(doc_rows, doc_ok, doc_dups),
        },
        "month_total": month_total,
        "inclusion_rules": dict(INCLUSION_RULES),
        "links": links,
        "conflicts": conflicts,
        "gaps": gaps,
        "notes": notes,
    }


def _adapt(payloads: list[dict], adapt: Callable, prefix: str, conflicts: list[dict]) -> list:
    rows = []
    for i, payload in enumerate(payloads or []):
        row, issues = adapt(payload or {}, i)
        rows.append(row)
        conflicts.extend({"kind": f"{prefix}_{issue}", "refs": [row.ref]} for issue in issues)
    return rows


def _dedupe(rows: list, fingerprint: Callable) -> tuple[list, list[dict]]:
    """同渠道去重:指纹重合只算首件,后到者点名。算不出指纹的行不猜、原样保留。"""
    seen: dict = {}
    kept, dups = [], []
    for row in rows:
        key = fingerprint(row)
        if key is not None and key in seen:
            dups.append({"ref": row.ref, "duplicate_of": seen[key]})
            continue
        if key is not None:
            seen[key] = row.ref
        kept.append(row)
    return kept, dups


def _dedupe_docs(rows: list[SalesDoc], conflicts: list[dict]) -> tuple[list, list[dict]]:
    """税票按票号去重。同票号但金额不同 ≠ 重复(可能是读错/改开),两张都留 + 点名交人。"""
    seen: dict[str, SalesDoc] = {}
    kept, dups = [], []
    for row in rows:
        key = normalize_invoice_no(row.invoice_no) or None
        first = seen.get(key) if key else None
        if first is None:
            if key:
                seen[key] = row
            kept.append(row)
        elif row.gross == first.gross:
            dups.append({"ref": row.ref, "duplicate_of": first.ref})
        else:
            kept.append(row)
            conflicts.append(
                {
                    "kind": "doc_dup_number_amount_differs",
                    "refs": [first.ref, row.ref],
                    "detail": (
                        f"票号 {row.invoice_no} 出现两次且金额不同"
                        f"({first.gross} vs {row.gross}),两张均已计入,请人工裁"
                    ),
                }
            )
    return kept, dups


def _edc_fingerprint(row: EdcSettlement) -> Optional[tuple]:
    anchor = row.batch_no or row.terminal_id
    return (row.day.isoformat(), anchor, str(row.gross)) if anchor else None


def _bank_fingerprint(row: BankCredit) -> tuple:
    if row.tx_id:
        return ("tx", row.tx_id)
    # 无 row_hash 的裸行退化指纹,与 StatementRow.__post_init__ 的要素口径一致(无余额可用)。
    return ("raw", row.day.isoformat(), str(row.amount), row.description[:40])


def _gaps(edc_ok, bank_ok, doc_ok, matched_bank: set[str], matched_edc: set[str]) -> list[dict]:
    """缺口探测:有入账无凭据 / 有结算单无到账,按日点名。"""
    evidence_days = {r.day for r in edc_ok} | {r.day for r in doc_ok}
    by_day: dict = {}
    for credit in bank_ok:
        if credit.ref in matched_bank:
            continue
        kind = "credit_unlinked" if credit.day in evidence_days else "credit_without_evidence"
        by_day.setdefault((credit.day, kind), []).append(credit.ref)
    for edc in edc_ok:
        if edc.ref not in matched_edc:
            by_day.setdefault((edc.day, "settlement_without_credit"), []).append(edc.ref)
    return [
        {"date": day.isoformat(), "kind": kind, "refs": refs}
        for (day, kind), refs in sorted(by_day.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    ]


def _daily(edc_ok: list[EdcSettlement], doc_ok: list[SalesDoc]) -> list[dict]:
    days = sorted({r.day for r in edc_ok} | {r.day for r in doc_ok})
    out = []
    for day in days:
        edc_day = [r for r in edc_ok if r.day == day]
        doc_day = [r for r in doc_ok if r.day == day]
        edc_gross = sum((r.gross for r in edc_day), _ZERO)
        doc_gross = sum((r.gross for r in doc_day), _ZERO)
        sales, output_vat = vat.split_gross(edc_gross + doc_gross)
        out.append(
            {
                "date": day.isoformat(),
                "edc_gross": str(edc_gross),
                "doc_gross": str(doc_gross),
                "gross": str(edc_gross + doc_gross),
                "sales_amount": str(sales),
                "output_vat": str(output_vat),
                "sources": {
                    "edc_settlement": [r.ref for r in edc_day],
                    "sales_doc": [r.ref for r in doc_day],
                },
            }
        )
    return out


def _edc_channel(rows, included, dups) -> dict:
    return {
        "count": len(rows),
        "included_count": len(included),
        "duplicates": dups,
        "gross_total": str(sum((r.gross for r in included), _ZERO)),
        "fee_total": str(sum((r.fee for r in included if r.fee is not None), _ZERO)),
        "net_total": str(sum((r.net for r in included if r.net is not None), _ZERO)),
        "fee_missing_count": sum(1 for r in included if r.fee is None),
    }


def _bank_channel(rows, included, dups, matched: set[str]) -> dict:
    return {
        "count": len(rows),
        "included_count": len(included),
        "duplicates": dups,
        "credit_total": str(sum((r.amount for r in included), _ZERO)),
        "matched_count": sum(1 for r in included if r.ref in matched),
    }


def _doc_channel(rows, included, dups) -> dict:
    return {
        "count": len(rows),
        "included_count": len(included),
        "duplicates": dups,
        "gross_total": str(sum((r.gross for r in included), _ZERO)),
        "face_net_total": str(sum((r.net for r in included if r.net is not None), _ZERO)),
        "face_vat_total": str(sum((r.vat for r in included if r.vat is not None), _ZERO)),
    }
