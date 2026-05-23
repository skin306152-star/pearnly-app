#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_layer2_structure.py

Local debugging script for services/ocr/layer2_structure.py.

Chains layer 1 (Vision API OCR) and layer 2 (Gemini Flash-Lite field
extraction) against real PDFs from storage/pdfs/ (REAL USER DATA — DO NOT
COMMIT, already covered by .gitignore).

Usage:
    # default: 2 files, max 2 pages each
    python tests/test_layer2_structure.py

    # one specific file
    python tests/test_layer2_structure.py --file path/to/invoice.pdf

    # more files, more pages
    python tests/test_layer2_structure.py --limit 5 --max-pages 3

Env requirements:
    GOOGLE_APPLICATION_CREDENTIALS   layer 1 (Vision SDK)
    GOOGLE_API_KEY or GEMINI_API_KEY layer 2 (Gemini SDK)

Exit code:
    0 = all files chained layer1 + layer2 without exception
    1 = at least one file failed
    2 = setup error (storage/pdfs/ missing, etc.)
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr.layer1_vision import extract_from_path  # noqa: E402
from services.ocr.layer2_structure import extract_from_layer1  # noqa: E402


def _print_invoice(invoice, indent: str = "    ") -> None:
    """Pretty-print a ThaiInvoice."""
    print(f"{indent}document_type:      {invoice.document_type}")
    print(f"{indent}is_not_invoice:     {invoice.is_not_invoice}")
    print(f"{indent}is_copy_or_dup:     {invoice.is_copy_or_duplicate}")
    print(f"{indent}invoice_number:     {invoice.invoice_number!r}")
    print(f"{indent}date:               {invoice.date!r} (raw: {invoice.date_raw!r})")
    print(f"{indent}seller_name:        {invoice.seller_name!r}")
    print(f"{indent}seller_tax:         {invoice.seller_tax!r}")
    print(
        f"{indent}seller_addr:        {invoice.seller_addr[:70]!r}{'...' if len(invoice.seller_addr) > 70 else ''}"
    )
    print(f"{indent}buyer_name:         {invoice.buyer_name!r}")
    print(f"{indent}buyer_tax:          {invoice.buyer_tax!r}")
    print(
        f"{indent}buyer_addr:         {invoice.buyer_addr[:70]!r}{'...' if len(invoice.buyer_addr) > 70 else ''}"
    )
    print(f"{indent}subtotal:           {invoice.subtotal!r}")
    print(f"{indent}vat:                {invoice.vat!r}")
    print(f"{indent}wht_rate / amount:  {invoice.wht_rate!r} / {invoice.wht_amount!r}")
    print(f"{indent}total_amount:       {invoice.total_amount!r}")
    print(f"{indent}category:           {invoice.category!r}")
    if invoice.notes:
        notes_preview = invoice.notes[:120]
        print(
            f"{indent}notes:              {notes_preview!r}{'...' if len(invoice.notes) > 120 else ''}"
        )
    print(f"{indent}items:              {len(invoice.items)} item(s)")
    for j, it in enumerate(invoice.items[:5], 1):
        print(
            f"{indent}  [{j}] name={it.name!r} qty={it.qty!r} price={it.price!r} subtotal={it.subtotal!r}"
        )
    if len(invoice.items) > 5:
        print(f"{indent}  ... and {len(invoice.items) - 5} more")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="single PDF/image path (overrides --limit)")
    parser.add_argument(
        "--limit",
        type=int,
        default=2,
        help="when iterating storage/pdfs/, process at most N files (default 2)",
    )
    parser.add_argument("--max-pages", type=int, default=2, help="max pages per PDF (default 2)")
    parser.add_argument("--dpi", type=int, default=200, help="layer 1 PDF render DPI (default 200)")
    args = parser.parse_args()

    # Env sanity
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("FAIL: GOOGLE_APPLICATION_CREDENTIALS not set (layer 1 needs it)")
        return 2
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        print("FAIL: neither GOOGLE_API_KEY nor GEMINI_API_KEY set (layer 2 needs one)")
        return 2

    # Resolve files
    if args.file:
        files = [Path(args.file)]
        if not files[0].exists():
            print(f"FAIL: file not found: {files[0]}")
            return 2
    else:
        storage = PROJECT_ROOT / "storage" / "pdfs"
        if not storage.exists():
            print(f"FAIL: {storage} not found")
            return 2
        files = sorted(storage.rglob("*.pdf"))[: args.limit]
        if not files:
            print(f"FAIL: no *.pdf in {storage}")
            return 2

    print("Layer 1 + Layer 2 chained run")
    print(f"Files:       {len(files)}")
    print(f"Max pages:   {args.max_pages}")
    print(f"DPI (l1):    {args.dpi}")
    print(
        f"Model (l2):  {os.environ.get('OCR_FLASHLITE_MODEL', 'gemini-2.5-flash-lite (default)')}"
    )
    print("=" * 72)

    fail_count = 0
    for i, f in enumerate(files, 1):
        size_kb = f.stat().st_size // 1024
        print(f"\n[{i}/{len(files)}] {f.name}  ({size_kb} KB)")
        print("-" * 72)

        # Layer 1
        try:
            l1 = extract_from_path(f, max_pages=args.max_pages, dpi=args.dpi)
        except Exception as e:
            print(f"  LAYER 1 FAIL  {type(e).__name__}: {e}")
            traceback.print_exc()
            fail_count += 1
            continue
        print(
            f"  layer1: {l1.page_count} page(s), {l1.elapsed_ms}ms, "
            f"avg_conf={sum(p.avg_confidence for p in l1.pages) / max(len(l1.pages), 1):.3f}"
        )

        # Layer 2
        try:
            l2 = extract_from_layer1(l1)
        except Exception as e:
            print(f"  LAYER 2 FAIL  {type(e).__name__}: {e}")
            traceback.print_exc()
            fail_count += 1
            continue
        total_in = sum(p.input_tokens for p in l2.pages)
        total_out = sum(p.output_tokens for p in l2.pages)
        total_retries = sum(p.retries for p in l2.pages)
        print(
            f"  layer2: {l2.elapsed_ms}ms, model={l2.model}, "
            f"tokens={total_in}+{total_out}, retries={total_retries}"
        )

        # Per-page details
        for pr in l2.pages:
            print(
                f"\n  --- Page {pr.page_number} (l2 elapsed={pr.elapsed_ms}ms, "
                f"in={pr.input_tokens}, out={pr.output_tokens}, "
                f"retries={pr.retries}, skipped={pr.skipped}) ---"
            )
            _print_invoice(pr.invoice)

    print("\n" + "=" * 72)
    if fail_count == 0:
        print(f"OK: {len(files)} / {len(files)} files chained without exception")
        return 0
    print(f"FAIL: {len(files) - fail_count} / {len(files)} OK, {fail_count} failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
