#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/compare_b1_b2_fix.py

Compare two pipeline-results.json runs (before vs after B1/B2 fix).

Loads:
    tests/pipeline-results-before-fix.json  (saved before)
    tests/pipeline-results.json             (latest)

Prints a side-by-side delta on:
    - IV69 invoice_number accuracy (containing `/` separator)
    - L3 trigger rate
    - L3 failure rate
    - Avg cost per page
    - Per-batch numbers
    - File-level diffs where the extracted invoice_number changed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def iter_pages(data):
    for batch_name, results in data["results"].items():
        for r in results:
            if r.get("status") != "OK":
                continue
            for p in r["pages"]:
                yield batch_name, r["filename"], p


def aggregate(data):
    """Pull headline metrics from a pipeline-results.json."""
    total_pages = 0
    total_cost = 0.0
    l3_triggered = 0
    l3_failed = 0
    review_pages = 0
    iv69_pages = []  # list of (batch, filename, inv_str, has_slash)
    field_records = []  # for cross-comparison

    for batch_name, filename, page in iter_pages(data):
        total_pages += 1
        f_ = page["fields"]
        # cost from page level not directly — rebuild from summaries
        chain = page["layer_chain"]
        if any("L3" in c for c in chain):
            l3_triggered += 1
        if any(c.startswith("L3_") for c in chain):
            l3_failed += 1
        if page.get("needs_manual_review"):
            review_pages += 1

        inv = (f_.get("invoice_number") or "")
        if "IV69" in inv.upper() or "IV60" in inv.upper() or "IV6" in inv.upper():
            iv69_pages.append({
                "batch": batch_name,
                "file": filename,
                "page": page["page_number"],
                "inv": inv,
                "has_slash": "/" in inv,
                "triggers": page["trigger_reasons"],
                "chain": page["layer_chain"],
            })

        field_records.append({
            "batch": batch_name,
            "file": filename,
            "page": page["page_number"],
            "fields": {
                "invoice_number": f_.get("invoice_number"),
                "total_amount": f_.get("total_amount"),
                "seller_tax": f_.get("seller_tax"),
                "date": f_.get("date"),
                "is_not_invoice": f_.get("is_not_invoice"),
            },
            "chain": page["layer_chain"],
            "triggers": page["trigger_reasons"],
            "needs_review": page.get("needs_manual_review"),
        })

    # pull total cost from summaries (not per-page)
    for s in data.get("summaries", []):
        total_cost += s.get("total_cost_thb", 0)

    return {
        "total_pages": total_pages,
        "total_cost_thb": round(total_cost, 4),
        "avg_cost_per_page_thb": round(total_cost / total_pages, 4) if total_pages else 0,
        "l3_triggered_pages": l3_triggered,
        "l3_failed_pages": l3_failed,
        "l3_trigger_rate": round(l3_triggered / total_pages, 4) if total_pages else 0,
        "l3_failure_rate": round(l3_failed / total_pages, 4) if total_pages else 0,
        "needs_manual_review_pages": review_pages,
        "iv69_total": len(iv69_pages),
        "iv69_with_slash": sum(1 for x in iv69_pages if x["has_slash"]),
        "iv69_correct_pct": (
            round(sum(1 for x in iv69_pages if x["has_slash"]) / len(iv69_pages) * 100, 1)
            if iv69_pages else 0
        ),
        "iv69_pages_detail": iv69_pages,
        "field_records": field_records,
    }


def field_diff(before_records, after_records):
    """Find pages where the extracted invoice_number / total_amount / seller_tax changed."""
    by_key_before = {(r["batch"], r["file"], r["page"]): r for r in before_records}
    by_key_after = {(r["batch"], r["file"], r["page"]): r for r in after_records}
    diffs = []
    for key, after_r in by_key_after.items():
        before_r = by_key_before.get(key)
        if not before_r:
            continue
        bf = before_r["fields"]
        af = after_r["fields"]
        # ignore non-invoices
        if af.get("is_not_invoice") or bf.get("is_not_invoice"):
            continue
        for f in ("invoice_number", "total_amount", "seller_tax"):
            if (bf.get(f) or None) != (af.get(f) or None):
                diffs.append({
                    "key": key,
                    "field": f,
                    "before": bf.get(f),
                    "after": af.get(f),
                    "before_chain": before_r["chain"],
                    "after_chain": after_r["chain"],
                    "after_triggers": after_r["triggers"],
                })
    return diffs


def main():
    before_path = PROJECT_ROOT / "tests" / "pipeline-results-before-fix.json"
    after_path = PROJECT_ROOT / "tests" / "pipeline-results.json"
    if not before_path.exists():
        print(f"FAIL: {before_path} not found")
        return 2
    if not after_path.exists():
        print(f"FAIL: {after_path} not found")
        return 2

    before = load(before_path)
    after = load(after_path)

    before_agg = aggregate(before)
    after_agg = aggregate(after)

    print("=" * 78)
    print("B1 / B2 Fix Comparison Report")
    print("=" * 78)

    def _row(label, b, a, fmt_str="{}"):
        b_str = fmt_str.format(b)
        a_str = fmt_str.format(a)
        delta = ""
        try:
            if isinstance(b, (int, float)) and isinstance(a, (int, float)) and b != 0:
                pct = (a - b) / b * 100
                delta = f"  ({pct:+.1f}%)"
            elif isinstance(b, (int, float)) and isinstance(a, (int, float)):
                delta = f"  ({a-b:+})"
        except Exception:
            pass
        print(f"  {label:32s}  {b_str:>14s}  ->  {a_str:>14s}{delta}")

    print("\n--- Headline metrics ---")
    _row("total_pages", before_agg["total_pages"], after_agg["total_pages"])
    _row("total_cost_thb",
         before_agg["total_cost_thb"], after_agg["total_cost_thb"],
         fmt_str="฿{:.4f}")
    _row("avg_cost_per_page",
         before_agg["avg_cost_per_page_thb"], after_agg["avg_cost_per_page_thb"],
         fmt_str="฿{:.4f}")
    _row("L3 triggered pages",
         before_agg["l3_triggered_pages"], after_agg["l3_triggered_pages"])
    _row("L3 trigger rate",
         before_agg["l3_trigger_rate"], after_agg["l3_trigger_rate"],
         fmt_str="{:.3%}")
    _row("L3 failed pages",
         before_agg["l3_failed_pages"], after_agg["l3_failed_pages"])
    _row("L3 failure rate",
         before_agg["l3_failure_rate"], after_agg["l3_failure_rate"],
         fmt_str="{:.3%}")
    _row("needs_manual_review pages",
         before_agg["needs_manual_review_pages"], after_agg["needs_manual_review_pages"])

    print("\n--- IV69 invoice_number accuracy (slash separator preserved) ---")
    _row("IV69 / similar pages total",
         before_agg["iv69_total"], after_agg["iv69_total"])
    _row("with `/` (correct format)",
         before_agg["iv69_with_slash"], after_agg["iv69_with_slash"])
    _row("correct %",
         before_agg["iv69_correct_pct"], after_agg["iv69_correct_pct"],
         fmt_str="{:.1f}%")

    print("\n--- IV69 page-by-page comparison ---")
    print(f"  {'batch':10s} {'file':52s} {'p':3s} {'before':14s} {'after':14s}  delta")
    bef_iv = {(x["batch"], x["file"], x["page"]): x for x in before_agg["iv69_pages_detail"]}
    aft_iv = {(x["batch"], x["file"], x["page"]): x for x in after_agg["iv69_pages_detail"]}
    for key in sorted(set(bef_iv.keys()) | set(aft_iv.keys())):
        b = bef_iv.get(key)
        a = aft_iv.get(key)
        bv = (b["inv"] if b else "—")
        av = (a["inv"] if a else "—")
        delta = "✓ FIXED" if (b and a and not b["has_slash"] and a["has_slash"]) else (
                "✗ BROKEN" if (b and a and b["has_slash"] and not a["has_slash"]) else
                "✓ STILL OK" if (b and a and b["has_slash"] and a["has_slash"]) else
                "✗ STILL WRONG" if (b and a and not b["has_slash"] and not a["has_slash"]) else
                "")
        print(f"  {key[0]:10s} {key[1][:52]:52s} {key[2]:3d} {bv[:14]:14s} {av[:14]:14s}  {delta}")

    print("\n--- Field-level diffs (only pages where invoice_number / total / seller_tax changed) ---")
    diffs = field_diff(before_agg["field_records"], after_agg["field_records"])
    if not diffs:
        print("  (none)")
    for d in diffs:
        batch, fname, pg = d["key"]
        print(f"  [{batch}] {fname[:50]}#{pg}  {d['field']}: {d['before']!r} -> {d['after']!r}")
        print(f"      chain: {'+'.join(d['before_chain'])} -> {'+'.join(d['after_chain'])}")
        if d["after_triggers"]:
            print(f"      triggers (after): {d['after_triggers']}")

    # JSON dump for downstream
    out = PROJECT_ROOT / "tests" / "compare-b1-b2-result.json"
    out.write_text(json.dumps({
        "before": before_agg,
        "after": after_agg,
        "field_diffs": diffs,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDiff JSON saved to: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
