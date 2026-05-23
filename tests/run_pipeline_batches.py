#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/run_pipeline_batches.py

Run pipeline on 3 batches:
    batch 1 electronic: 12 representative server subset (PDFs nested by tenant)
    batch 2 photos:     local-uploaded phone photos (JPG)
    batch 3 scanned:    local-uploaded BAKELAB + SINCERE scanned (PDF)

Outputs:
    tests/pipeline-results.json     (machine-readable, ALL per-page details)
    stdout                          (human summary printed at end)

Env requirements:
    GOOGLE_APPLICATION_CREDENTIALS   layer 1
    GOOGLE_API_KEY or GEMINI_API_KEY layer 2 + 3
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr.pipeline import (  # noqa: E402
    InvoicePatternMemory,
    run_on_path,
)

# ============================================================
# Batch file lists
# ============================================================
# Batch 1: 12 server-side representative subset (already on server at original
# paths; no upload needed)
PDFS_ROOT_SERVER = "/opt/mrpilot/storage/pdfs"
BATCH_1_REL = [
    "20509799/2026-05/2aa032839fd34354a59eef054571b5af.pdf",
    "8f1e45df/2026-05/00ef7f60a3e6484e829b1181dc827ab9.pdf",
    "8f1e45df/2026-05/83cad7f961bc4afb81910d0e79166c1e.pdf",
    "932e2cc8/2026-05/220562f8d75c4b8a9d576e3261324d69.pdf",
    "932e2cc8/2026-05/dc81400a41984b1db2832e85b0ead13e.pdf",
    "468b50c1/2026-05/3f5a6dd540604dff966f7ae6a6ee009d.pdf",
    "468b50c1/2026-05/18931440c8594cf085b4d24be38b295a.pdf",
    "9707bdff/2026-05/125ba23b45b74e4e93bbce2964d087eb.pdf",
    "9707bdff/2026-05/4dfe953a921b4f088735052fcb535de0.pdf",
    "9707bdff/2026-05/d59556884fbd4f629982561ae3757825.pdf",
    "d256a4d3/2026-05/4adc33e23f5d47158323e3df3556e1c6.pdf",
    "d256a4d3/2026-05/9bc545f9c90d46bf9ade3bcc50e719cc.pdf",
]

# Batches 2 + 3: uploaded fixtures (paths depend on where the script runs)
PHOTOS_DIR_SERVER = "/opt/mrpilot/tests/fixtures/photos"
SCANNED_DIR_SERVER = "/opt/mrpilot/tests/fixtures/scanned"

# Cost watchdog: architecture.md target ~$0.0023/page * 35 THB/USD = ~฿0.0805/page;
# 20% over = ฿0.0966/page. Cap at ฿0.10/page average to give rounding headroom.
COST_CAP_THB_PER_PAGE = 0.10


def serialize_pipeline_result(pr_obj, path):
    """PipelineResult -> JSON-friendly dict + file metadata."""
    return {
        "file": str(path),
        "filename": Path(path).name,
        "page_count": pr_obj.page_count,
        "elapsed_ms": pr_obj.elapsed_ms,
        "cost_thb": round(pr_obj.estimated_cost_thb, 6),
        "pages": [
            {
                "page_number": p.page_number,
                "layer_chain": p.layer_chain,
                "trigger_reasons": p.trigger_reasons,
                "layer1_avg_conf": round(p.layer1_avg_confidence, 4),
                "layer1_ms": p.layer1_ms,
                "layer2_ms": p.layer2_ms,
                "layer3_ms": p.layer3_ms,
                "l2_tokens": [p.layer2_input_tokens, p.layer2_output_tokens],
                "l3_tokens": [p.layer3_input_tokens, p.layer3_output_tokens],
                "needs_manual_review": p.needs_manual_review,
                "error": p.error,
                "fields": {
                    "document_type": p.invoice.document_type,
                    "is_not_invoice": p.invoice.is_not_invoice,
                    "is_copy_or_duplicate": p.invoice.is_copy_or_duplicate,
                    "invoice_number": p.invoice.invoice_number,
                    "date": p.invoice.date,
                    "date_raw": p.invoice.date_raw,
                    "seller_name": p.invoice.seller_name,
                    "seller_tax": p.invoice.seller_tax,
                    "buyer_name": p.invoice.buyer_name,
                    "buyer_tax": p.invoice.buyer_tax,
                    "subtotal": p.invoice.subtotal,
                    "vat": p.invoice.vat,
                    "wht_rate": p.invoice.wht_rate,
                    "wht_amount": p.invoice.wht_amount,
                    "total_amount": p.invoice.total_amount,
                    "category": p.invoice.category,
                    "items_count": len(p.invoice.items),
                    "items_preview": [
                        {
                            "name": it.name[:60],
                            "qty": it.qty,
                            "price": it.price,
                            "subtotal": it.subtotal,
                        }
                        for it in p.invoice.items[:5]
                    ],
                },
            }
            for p in pr_obj.pages
        ],
    }


def run_batch(name, file_list, pattern_memory=None):
    """Run pipeline on every file in list, return list of dicts.

    pattern_memory: shared InvoicePatternMemory passed to every pipeline.run
    so the template-familiarity check learns across files within the batch.
    """
    results = []
    for i, fp in enumerate(file_list, 1):
        rel_name = Path(fp).name
        print(f"  [{i:2}/{len(file_list)}] {rel_name[:70]}", flush=True)
        t0 = time.time()
        try:
            pr_obj = run_on_path(fp, pattern_memory=pattern_memory)
            r = serialize_pipeline_result(pr_obj, fp)
            r["status"] = "OK"
            # Compact echo
            for pg in r["pages"]:
                chain = "+".join(c.replace("L", "") for c in pg["layer_chain"])
                inv_no = pg["fields"]["invoice_number"]
                total = pg["fields"]["total_amount"]
                conf = pg["layer1_avg_conf"]
                print(
                    f"        p{pg['page_number']}: chain={chain} conf={conf:.2f} "
                    f"inv={inv_no!r} total={total!r} triggers={len(pg['trigger_reasons'])}",
                    flush=True,
                )
        except Exception as e:
            elapsed = int((time.time() - t0) * 1000)
            r = {
                "file": str(fp),
                "filename": rel_name,
                "status": "FAIL",
                "exception": type(e).__name__,
                "error": str(e)[:500],
                "elapsed_ms": elapsed,
                "page_count": 0,
                "cost_thb": 0.0,
                "pages": [],
            }
            print(f"        FAIL: {type(e).__name__}: {str(e)[:200]}", flush=True)
            traceback.print_exc(limit=2)
        results.append(r)
    return results


def discover_batch_files():
    """Return list of (batch_name, file_paths) tuples."""
    batches = []

    # Batch 1: hardcoded server paths
    batch1 = [str(Path(PDFS_ROOT_SERVER) / rel) for rel in BATCH_1_REL]
    batches.append(("electronic", batch1))

    # Batch 2: photos dir
    photos_dir = Path(PHOTOS_DIR_SERVER)
    batch2 = []
    if photos_dir.exists():
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            batch2.extend(sorted(photos_dir.glob(ext)))
    batches.append(("photos", [str(p) for p in batch2]))

    # Batch 3: scanned dir
    scanned_dir = Path(SCANNED_DIR_SERVER)
    batch3 = []
    if scanned_dir.exists():
        batch3.extend(sorted(scanned_dir.glob("*.pdf")))
    batches.append(("scanned", [str(p) for p in batch3]))

    return batches


def summarize_batch(batch_name, results):
    """Compute summary metrics for one batch."""
    ok_results = [r for r in results if r.get("status") == "OK"]
    fail_count = len(results) - len(ok_results)

    total_pages = sum(r.get("page_count", 0) for r in ok_results)
    total_cost = sum(r.get("cost_thb", 0) for r in ok_results)
    total_ms = sum(r.get("elapsed_ms", 0) for r in ok_results)

    chains = Counter()
    trigger_buckets = Counter()
    review_pages = 0
    confidence_dist = []

    for r in ok_results:
        for p in r.get("pages", []):
            chains[tuple(p["layer_chain"])] += 1
            for t in p["trigger_reasons"]:
                tl = t.lower()
                if "conf" in tl:
                    trigger_buckets["word_low_confidence"] += 1
                elif "not found in l1" in tl:
                    trigger_buckets["l1_hallucination"] += 1
                elif "pattern" in tl and "differs" in tl:
                    trigger_buckets["pattern_anomaly"] += 1
                elif "missing" in tl:
                    trigger_buckets["missing_field"] += 1
                elif "math" in tl:
                    trigger_buckets["math_fail"] += 1
                elif "tax" in tl:
                    trigger_buckets["tax_format"] += 1
                else:
                    trigger_buckets["other"] += 1
            if p["needs_manual_review"]:
                review_pages += 1
            confidence_dist.append(p["layer1_avg_conf"])

    avg_cost = total_cost / total_pages if total_pages else 0
    avg_ms = total_ms / total_pages if total_pages else 0
    avg_conf = sum(confidence_dist) / len(confidence_dist) if confidence_dist else 0
    min_conf = min(confidence_dist) if confidence_dist else 0
    max_conf = max(confidence_dist) if confidence_dist else 0

    layer3_pages = sum(v for chain, v in chains.items() if "L3" in chain)
    layer3_failed_pages = sum(
        v for chain, v in chains.items() if any(c.startswith("L3_") for c in chain)
    )
    l3_trigger_rate = (layer3_pages / total_pages) if total_pages else 0
    cost_over_cap = avg_cost > COST_CAP_THB_PER_PAGE

    return {
        "batch": batch_name,
        "files_total": len(results),
        "files_ok": len(ok_results),
        "files_fail": fail_count,
        "pages_total": total_pages,
        "total_cost_thb": round(total_cost, 4),
        "avg_cost_thb_per_page": round(avg_cost, 4),
        "total_elapsed_ms": total_ms,
        "avg_elapsed_ms_per_page": round(avg_ms, 0),
        "layer_chain_distribution": {"+".join(k): v for k, v in chains.items()},
        "trigger_buckets": dict(trigger_buckets),
        "layer3_triggered_pages": layer3_pages,
        "layer3_failed_pages": layer3_failed_pages,
        "layer3_trigger_rate": round(l3_trigger_rate, 3),
        "needs_manual_review_pages": review_pages,
        "layer1_avg_conf_mean": round(avg_conf, 4),
        "layer1_avg_conf_min": round(min_conf, 4),
        "layer1_avg_conf_max": round(max_conf, 4),
        "cost_over_cap": cost_over_cap,
    }


def print_summary(batches_summary, all_results):
    """Print human-readable summary."""
    print("\n" + "=" * 78)
    print("PIPELINE TEST RESULTS — SUMMARY")
    print("=" * 78)

    for s in batches_summary:
        print(f"\n[ batch: {s['batch']} ]")
        print(f"  files:        {s['files_total']}  (ok={s['files_ok']}, fail={s['files_fail']})")
        print(f"  pages:        {s['pages_total']}")
        print(
            f"  cost:         ฿{s['total_cost_thb']}  avg ฿{s['avg_cost_thb_per_page']}/page"
            + ("  ⚠ OVER CAP" if s["cost_over_cap"] else "")
        )
        print(
            f"  elapsed:      {s['total_elapsed_ms']}ms  avg {s['avg_elapsed_ms_per_page']}ms/page"
        )
        print(
            f"  L1 avg conf:  mean={s['layer1_avg_conf_mean']}  "
            f"min={s['layer1_avg_conf_min']}  max={s['layer1_avg_conf_max']}"
        )
        print(f"  layer chains: {s['layer_chain_distribution']}")
        print(f"  triggers:     {s['trigger_buckets']}")
        print(
            f"  L3 triggered: {s['layer3_triggered_pages']}/{s['pages_total']} "
            f"({s['layer3_trigger_rate'] * 100:.0f}%) "
            f"(failed: {s['layer3_failed_pages']})"
        )
        print(f"  manual review: {s['needs_manual_review_pages']} page(s)")

    # Grand total
    grand_pages = sum(s["pages_total"] for s in batches_summary)
    grand_cost = sum(s["total_cost_thb"] for s in batches_summary)
    grand_ms = sum(s["total_elapsed_ms"] for s in batches_summary)
    grand_avg_cost = grand_cost / grand_pages if grand_pages else 0
    grand_avg_ms = grand_ms / grand_pages if grand_pages else 0
    print("\n[ GRAND TOTAL ]")
    print(f"  pages:        {grand_pages}")
    print(f"  cost:         ฿{round(grand_cost, 4)}  avg ฿{round(grand_avg_cost, 4)}/page")
    print(
        f"  cap (avg/p):  ฿{COST_CAP_THB_PER_PAGE}  "
        + ("⚠ EXCEEDED" if grand_avg_cost > COST_CAP_THB_PER_PAGE else "OK")
    )
    print(f"  elapsed:      {grand_ms}ms  avg {grand_avg_ms:.0f}ms/page")


def main():
    print("Pipeline batch test — discovering files...")
    batches = discover_batch_files()
    for name, files in batches:
        print(f"  batch {name}: {len(files)} files")

    # B1 fix: shared pattern memory across all batches, so template
    # familiarity check accumulates knowledge of each seller_tax's
    # invoice_number prefixes.
    shared_pattern_memory = InvoicePatternMemory()

    all_results = {}
    summaries = []
    for name, files in batches:
        if not files:
            print(f"\n=== batch '{name}' is empty — skipping ===")
            all_results[name] = []
            summaries.append(
                {
                    "batch": name,
                    "files_total": 0,
                    "files_ok": 0,
                    "files_fail": 0,
                    "pages_total": 0,
                    "total_cost_thb": 0,
                    "avg_cost_thb_per_page": 0,
                    "total_elapsed_ms": 0,
                    "avg_elapsed_ms_per_page": 0,
                    "layer_chain_distribution": {},
                    "trigger_buckets": {},
                    "layer3_triggered_pages": 0,
                    "layer3_failed_pages": 0,
                    "layer3_trigger_rate": 0,
                    "needs_manual_review_pages": 0,
                    "layer1_avg_conf_mean": 0,
                    "layer1_avg_conf_min": 0,
                    "layer1_avg_conf_max": 0,
                    "cost_over_cap": False,
                }
            )
            continue
        print(f"\n=== batch '{name}' ({len(files)} files) ===", flush=True)
        results = run_batch(name, files, pattern_memory=shared_pattern_memory)
        all_results[name] = results
        summaries.append(summarize_batch(name, results))

    # Write JSON
    out_path = Path(__file__).resolve().parent / "pipeline-results.json"
    out_path.write_text(
        json.dumps(
            {"summaries": summaries, "results": all_results},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nJSON saved to: {out_path}")

    # Print summary
    print_summary(summaries, all_results)


if __name__ == "__main__":
    main()
