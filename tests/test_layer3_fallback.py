#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_layer3_fallback.py

Local debugging script for services/ocr/layer3_fallback.py.

For each test PDF:
    1. Run layer 1 + layer 2 to get a baseline ThaiInvoice (ground truth)
    2. Corrupt the baseline (zero out invoice_number; replace total_amount
       with a wrong value)
    3. Render the PDF page to PNG bytes (via fitz, inline)
    4. Call layer 3 with the corrupted invoice + plausible trigger reasons
    5. Verify layer 3 corrects the wrong/missing fields back toward the
       baseline

Usage:
    python tests/test_layer3_fallback.py
    python tests/test_layer3_fallback.py --limit 2
    python tests/test_layer3_fallback.py --file path/to/invoice.pdf

Env requirements:
    GOOGLE_APPLICATION_CREDENTIALS   layer 1 (Vision SDK)
    GOOGLE_API_KEY or GEMINI_API_KEY layer 2 + layer 3 (Gemini SDK)

Exit code:
    0 = all PDFs ran layer 3 without exception
    1 = at least one layer 3 call raised an exception
    2 = setup error (env / storage / etc.)

Note: this is a CORRECTNESS test, not a strict regression test. We don't
fail on minor whitespace differences in Gemini's output — just print a
side-by-side diff for the user to eyeball.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr.layer1_vision import extract_from_path  # noqa: E402
from services.ocr.layer2_structure import extract_from_layer1  # noqa: E402
from services.ocr.layer3_fallback import refine_page  # noqa: E402


def _render_page_png(pdf_path: Path, page_index: int = 0, dpi: int = 200) -> bytes:
    """Render one PDF page to PNG bytes using PyMuPDF.

    Inline (not imported from layer 1) so the test doesn't depend on
    layer 1 internals.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    try:
        if page_index >= doc.page_count:
            raise IndexError(
                f"page_index {page_index} out of range (PDF has {doc.page_count} pages)"
            )
        page = doc.load_page(page_index)
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def _short(s, n: int = 50) -> str:
    """Truncate a string for display."""
    if s is None:
        return "<None>"
    s = str(s)
    if len(s) <= n:
        return s
    return s[:n] + "..."


def _print_compare(label: str, baseline, corrupted, corrected) -> None:
    """Print a one-line per-field comparison."""
    b = _short(baseline)
    c = _short(corrupted)
    r = _short(corrected)
    match_baseline = "==" if str(corrected) == str(baseline) else "!="
    print(f"  {label:18s}  baseline={b!r}")
    print(f"  {'':18s}  corrupted={c!r}")
    print(f"  {'':18s}  corrected={r!r}  ({match_baseline} baseline)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="single PDF path (overrides --limit)")
    parser.add_argument("--limit", type=int, default=2,
                        help="when iterating storage/pdfs/, process at most N files (default 2)")
    parser.add_argument("--dpi", type=int, default=200,
                        help="layer 1 + layer 3 PDF render DPI (default 200)")
    args = parser.parse_args()

    # Env sanity
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("FAIL: GOOGLE_APPLICATION_CREDENTIALS not set (layer 1)")
        return 2
    if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        print("FAIL: neither GOOGLE_API_KEY nor GEMINI_API_KEY set (layer 2 + 3)")
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
            print(f"FAIL: no PDFs in {storage}")
            return 2

    print("Layer 3 (Flash visual fallback) correction test")
    print(f"Files:       {len(files)}")
    print(f"DPI:         {args.dpi}")
    print(f"Model (l3):  {os.environ.get('OCR_FLASH_MODEL', 'gemini-2.5-flash (default)')}")
    print("=" * 78)

    fail_count = 0
    for i, f in enumerate(files, 1):
        size_kb = f.stat().st_size // 1024
        print(f"\n[{i}/{len(files)}] {f.name}  ({size_kb} KB)")
        print("-" * 78)

        # Step 1: baseline (layer1 + layer2)
        try:
            l1 = extract_from_path(f, max_pages=1, dpi=args.dpi)
        except Exception as e:
            print(f"  SETUP FAIL (layer 1): {type(e).__name__}: {e}")
            fail_count += 1
            continue
        if not l1.pages:
            print(f"  SETUP FAIL: layer 1 returned 0 pages")
            fail_count += 1
            continue

        try:
            l2 = extract_from_layer1(l1)
        except Exception as e:
            print(f"  SETUP FAIL (layer 2): {type(e).__name__}: {e}")
            fail_count += 1
            continue

        baseline_page = l1.pages[0]
        baseline_invoice = l2.pages[0].invoice
        print(f"  baseline: invoice_no={baseline_invoice.invoice_number!r} "
              f"total={baseline_invoice.total_amount!r} "
              f"seller_tax={baseline_invoice.seller_tax!r}")

        # Step 2: corrupt — wipe invoice_number, replace total_amount with wrong value
        corrupted = baseline_invoice.model_copy(deep=True)
        corrupted.invoice_number = None
        corrupted.total_amount = "99999.99"  # obviously wrong
        # Also wipe seller_tax to test 3-field correction
        original_seller_tax = baseline_invoice.seller_tax
        corrupted.seller_tax = ""

        trigger_reasons = [
            "invoice_number is missing in previous extraction; please read the invoice header carefully",
            "total_amount in previous extraction (99999.99) does not match subtotal + vat from the image; please re-read the totals line",
            "seller_tax is missing in previous extraction; please find the 13-digit tax ID near the seller header",
        ]
        print(f"  corrupted: invoice_no=None  total='99999.99'  seller_tax=''")
        print(f"  triggers ({len(trigger_reasons)}):")
        for t in trigger_reasons:
            print(f"    - {t[:80]}{'...' if len(t) > 80 else ''}")

        # Step 3: render PDF page to PNG
        try:
            image_bytes = _render_page_png(f, page_index=0, dpi=args.dpi)
        except Exception as e:
            print(f"  SETUP FAIL (render): {type(e).__name__}: {e}")
            fail_count += 1
            continue
        print(f"  rendered: {len(image_bytes)} bytes PNG @ {args.dpi}dpi")

        # Step 4: call layer 3
        try:
            l3 = refine_page(
                image_bytes=image_bytes,
                layer1_page=baseline_page,
                layer2_invoice=corrupted,
                trigger_reasons=trigger_reasons,
            )
        except Exception as e:
            print(f"  LAYER 3 FAIL: {type(e).__name__}: {e}")
            traceback.print_exc()
            fail_count += 1
            continue

        print(f"\n  Layer 3 result:")
        print(f"    elapsed:        {l3.elapsed_ms}ms")
        print(f"    tokens:         in={l3.input_tokens}  out={l3.output_tokens}  "
              f"(retries={l3.retries})")
        print(f"    model:          {l3.model}")

        # Step 5: side-by-side comparison
        corrected = l3.invoice
        print(f"\n  Comparison (baseline vs corrupted vs corrected):")
        _print_compare("invoice_number",
                       baseline_invoice.invoice_number,
                       corrupted.invoice_number,
                       corrected.invoice_number)
        _print_compare("total_amount",
                       baseline_invoice.total_amount,
                       corrupted.total_amount,
                       corrected.total_amount)
        _print_compare("seller_tax",
                       original_seller_tax,
                       corrupted.seller_tax,
                       corrected.seller_tax)

        # Quick eyeball summary
        match_score = 0
        if str(corrected.invoice_number) == str(baseline_invoice.invoice_number):
            match_score += 1
        if str(corrected.total_amount) == str(baseline_invoice.total_amount):
            match_score += 1
        if str(corrected.seller_tax) == str(original_seller_tax):
            match_score += 1
        print(f"\n  Recovery score: {match_score} / 3 fields match baseline exactly")

    print("\n" + "=" * 78)
    if fail_count == 0:
        print(f"OK: {len(files)} / {len(files)} files ran layer 3 without exception")
        return 0
    print(f"FAIL: {len(files) - fail_count} / {len(files)} OK, {fail_count} failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
