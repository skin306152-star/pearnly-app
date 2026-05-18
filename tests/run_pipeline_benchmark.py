#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/run_pipeline_benchmark.py

Concurrency benchmark + large-file stress test for the pipeline.

Usage:
    # serial baseline (matches run_pipeline_batches's default)
    python tests/run_pipeline_benchmark.py --concurrency 1

    # concurrent 5
    python tests/run_pipeline_benchmark.py --concurrency 5

    # concurrent 10
    python tests/run_pipeline_benchmark.py --concurrency 10

    # large-file stress test (synthesizes a ~60-page PDF by replicating a
    # source PDF's pages with fitz, then runs pipeline serially)
    python tests/run_pipeline_benchmark.py --large-source /opt/mrpilot/tests/fixtures/scanned/scan_002.pdf \
                                            --large-target-pages 60

Outputs:
    tests/pipeline-benchmark-c{N}.json     (per concurrency run)
    tests/pipeline-benchmark-large.json    (large file run)

Metrics per run:
    - total wall-clock seconds
    - per-page elapsed: min / mean / p50 / p90 / p99 / max
    - peak RSS (resident memory) in MB (server-side, Linux `resource` module)
    - rate-limit detection (Layer 2/3 QuotaError occurrences)
    - cost: total + avg per page
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr.pipeline import (  # noqa: E402
    InvoicePatternMemory,
    run_on_path,
)


# ============================================================
# Same 49 files as run_pipeline_batches.py
# ============================================================
PDFS_ROOT_SERVER = "/opt/mrpilot/storage/pdfs"
ELECTRONIC_REL = [
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
PHOTOS_DIR_SERVER = "/opt/mrpilot/tests/fixtures/photos"
SCANNED_DIR_SERVER = "/opt/mrpilot/tests/fixtures/scanned"


def discover_all_files():
    files = []
    files.extend([Path(PDFS_ROOT_SERVER) / rel for rel in ELECTRONIC_REL])
    photos = Path(PHOTOS_DIR_SERVER)
    if photos.exists():
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            files.extend(sorted(photos.glob(ext)))
    scanned = Path(SCANNED_DIR_SERVER)
    if scanned.exists():
        files.extend(sorted(scanned.glob("*.pdf")))
    return files


def _peak_mem_mb():
    """Return peak RSS in MB. Linux only via stdlib `resource`; fall back to 0."""
    try:
        import resource  # noqa: E501
        # ru_maxrss on Linux is in KB, on macOS in bytes; this is for Linux server.
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        return 0.0


def _run_one(fp: str, pattern_memory) -> dict:
    """Run pipeline on one file; return result dict including timing + errors."""
    t0 = time.time()
    err = None
    rate_limited = False
    page_count = 0
    cost_thb = 0.0
    chain_distribution = {}
    l3_triggered_count = 0
    l3_failed_count = 0
    try:
        pr = run_on_path(str(fp), pattern_memory=pattern_memory)
        page_count = pr.page_count
        cost_thb = pr.estimated_cost_thb
        for p in pr.pages:
            chain_key = "+".join(p.layer_chain)
            chain_distribution[chain_key] = chain_distribution.get(chain_key, 0) + 1
            if any("L3" in c for c in p.layer_chain):
                l3_triggered_count += 1
            if any(c.startswith("L3_") for c in p.layer_chain):
                l3_failed_count += 1
            if p.error and ("quota" in p.error.lower() or "rate" in p.error.lower()):
                rate_limited = True
    except Exception as e:
        msg = str(e)
        err = f"{type(e).__name__}: {msg[:200]}"
        if "quota" in msg.lower() or "rate" in msg.lower() or "429" in msg:
            rate_limited = True
    elapsed = time.time() - t0
    return {
        "file": str(fp),
        "filename": Path(fp).name,
        "elapsed_s": round(elapsed, 3),
        "pages": page_count,
        "cost_thb": round(cost_thb, 4),
        "error": err,
        "rate_limited": rate_limited,
        "chain_distribution": chain_distribution,
        "l3_triggered_count": l3_triggered_count,
        "l3_failed_count": l3_failed_count,
    }


def benchmark(files, concurrency: int) -> dict:
    """Run pipeline on files at given concurrency; aggregate stats."""
    pattern_memory = InvoicePatternMemory()
    print(f"\n=== Benchmark concurrency={concurrency} on {len(files)} files ===", flush=True)
    t_start = time.time()
    results = []
    if concurrency == 1:
        for fp in files:
            r = _run_one(fp, pattern_memory)
            results.append(r)
            print(f"  [{len(results)}/{len(files)}] {r['filename'][:50]:50s} "
                  f"{r['elapsed_s']:6.2f}s  pages={r['pages']}  cost=฿{r['cost_thb']}"
                  + ("  RATE_LIMITED" if r["rate_limited"] else "")
                  + (f"  ERR={r['error'][:50]}" if r["error"] else ""), flush=True)
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = {ex.submit(_run_one, fp, pattern_memory): fp for fp in files}
            for fut in as_completed(futures):
                r = fut.result()
                results.append(r)
                print(f"  [{len(results)}/{len(files)}] {r['filename'][:50]:50s} "
                      f"{r['elapsed_s']:6.2f}s  pages={r['pages']}  cost=฿{r['cost_thb']}"
                      + ("  RATE_LIMITED" if r["rate_limited"] else "")
                      + (f"  ERR={r['error'][:50]}" if r["error"] else ""), flush=True)
    total_wall_s = time.time() - t_start
    peak_mb = _peak_mem_mb()

    # Per-page elapsed (divide each file's wall time by its page count)
    page_elapsed = []
    for r in results:
        if r["pages"] > 0:
            # NOTE: under concurrency, per-file wall time has overlap; this is
            # an upper bound on per-page time (sequential within file).
            page_elapsed.append(r["elapsed_s"] / r["pages"])
    page_elapsed.sort()
    n = len(page_elapsed)
    def _pct(p):
        if not n:
            return 0
        idx = min(int(n * p), n - 1)
        return page_elapsed[idx]

    total_pages = sum(r["pages"] for r in results)
    total_cost = sum(r["cost_thb"] for r in results)
    rate_limited_files = sum(1 for r in results if r["rate_limited"])
    error_files = sum(1 for r in results if r["error"])
    total_l3_triggered = sum(r["l3_triggered_count"] for r in results)
    total_l3_failed = sum(r["l3_failed_count"] for r in results)

    return {
        "concurrency": concurrency,
        "files_total": len(files),
        "files_with_errors": error_files,
        "files_rate_limited": rate_limited_files,
        "total_pages": total_pages,
        "total_wall_s": round(total_wall_s, 2),
        "throughput_pages_per_s": round(total_pages / total_wall_s, 3) if total_wall_s else 0,
        "throughput_pages_per_min": round(total_pages / total_wall_s * 60, 1) if total_wall_s else 0,
        "per_page_elapsed_s": {
            "min": round(page_elapsed[0], 2) if n else 0,
            "p50": round(_pct(0.50), 2),
            "p90": round(_pct(0.90), 2),
            "p99": round(_pct(0.99), 2),
            "max": round(page_elapsed[-1], 2) if n else 0,
            "mean": round(sum(page_elapsed) / n, 2) if n else 0,
        },
        "total_cost_thb": round(total_cost, 4),
        "avg_cost_per_page_thb": round(total_cost / total_pages, 4) if total_pages else 0,
        "peak_rss_mb": round(peak_mb, 1),
        "l3_triggered_pages": total_l3_triggered,
        "l3_failed_pages": total_l3_failed,
        "l3_trigger_rate": round(total_l3_triggered / total_pages, 4) if total_pages else 0,
        "results": results,
    }


def synthesize_large_pdf(source: Path, target_pages: int, output: Path) -> Path:
    """Replicate source PDF's pages until we have >= target_pages, trim if needed."""
    import fitz

    src = fitz.open(str(source))
    dst = fitz.open()
    try:
        while dst.page_count < target_pages:
            dst.insert_pdf(src)
        # Trim if overshot
        if dst.page_count > target_pages:
            dst.delete_pages(target_pages, dst.page_count - 1)
        output.parent.mkdir(parents=True, exist_ok=True)
        dst.save(str(output))
    finally:
        dst.close()
        src.close()
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument(
        "--large-source",
        default=None,
        help="if given, run large-file test (synthesize from this PDF) instead of batch",
    )
    ap.add_argument("--large-target-pages", type=int, default=60)
    ap.add_argument(
        "--out",
        default=None,
        help="explicit output JSON path (default auto-named)",
    )
    args = ap.parse_args()

    if args.large_source:
        src = Path(args.large_source)
        if not src.exists():
            print(f"FAIL: source PDF not found: {src}")
            return 2
        output_pdf = Path("/tmp/pipeline_benchmark_large.pdf")
        print(f"Synthesizing {args.large_target_pages}-page PDF from {src.name}...")
        synthesize_large_pdf(src, args.large_target_pages, output_pdf)
        files = [output_pdf]
        out_path = Path(args.out) if args.out else (
            Path(__file__).resolve().parent / "pipeline-benchmark-large.json"
        )
    else:
        files = discover_all_files()
        if not files:
            print("FAIL: no files discovered")
            return 2
        out_path = Path(args.out) if args.out else (
            Path(__file__).resolve().parent / f"pipeline-benchmark-c{args.concurrency}.json"
        )

    bench = benchmark(files, args.concurrency)

    out_path.write_text(json.dumps(bench, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON saved to: {out_path}")
    # Print summary
    print("\n" + "=" * 78)
    print(f"SUMMARY (concurrency={args.concurrency}"
          + (f", large-file synth from {Path(args.large_source).name}" if args.large_source else "")
          + ")")
    print("=" * 78)
    summary = {k: v for k, v in bench.items() if k != "results"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main() or 0)
