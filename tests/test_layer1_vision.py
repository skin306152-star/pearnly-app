#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_layer1_vision.py

Local debugging script for services/ocr/layer1_vision.py.

Iterates through PDFs in storage/pdfs/ (REAL USER DATA - do not commit,
already covered by .gitignore), calls extract_from_path on each, prints
a per-page summary.

Usage:
    # default: first 3 files from storage/pdfs/, max 3 pages each
    python tests/test_layer1_vision.py

    # only one specific file
    python tests/test_layer1_vision.py --file storage/pdfs/<hash>.pdf

    # more files, more pages
    python tests/test_layer1_vision.py --limit 10 --max-pages 5

    # custom DPI
    python tests/test_layer1_vision.py --dpi 150

Exit code:
    0 = all files processed without exception
    1 = at least one file raised an exception
    2 = setup error (storage/pdfs/ empty, env not set, etc.)
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

# Make `services.ocr.layer1_vision` importable when run from any cwd
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr.layer1_vision import extract_from_path  # noqa: E402


def _summarize_page(page) -> dict:
    """Compute simple per-page stats for printing."""
    blocks = len(page.blocks)
    paragraphs = sum(len(b.paragraphs) for b in page.blocks)
    words = sum(len(p.words) for b in page.blocks for p in b.paragraphs)
    return {
        "blocks": blocks,
        "paragraphs": paragraphs,
        "words": words,
    }


def _sample_words(page, n: int = 5):
    """First n words on the page, for spot-checking output."""
    out = []
    for b in page.blocks:
        for pp in b.paragraphs:
            for w in pp.words:
                out.append(w)
                if len(out) >= n:
                    return out
    return out


def _format_text_preview(text: str, n: int = 120) -> str:
    """Truncate + replace newlines for one-line preview."""
    s = text[:n].replace("\n", " / ")
    if len(text) > n:
        s += "..."
    return s


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        help="single PDF/image path (overrides --limit)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="when iterating storage/pdfs/, process at most N files (default 3)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="max pages per PDF (default 3 for fast iteration)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="render DPI for PDF (default 200)",
    )
    args = parser.parse_args()

    # Resolve target files
    if args.file:
        files = [Path(args.file)]
        if not files[0].exists():
            print(f"FAIL: file not found: {files[0]}")
            return 2
    else:
        storage = PROJECT_ROOT / "storage" / "pdfs"
        if not storage.exists():
            print(f"FAIL: {storage} not found")
            print("      Either scp PDFs there, or use --file to test a specific path.")
            return 2
        # Production server stores PDFs nested by user_id/YYYY-MM/<file>.pdf,
        # so use recursive glob to find them regardless of layout.
        files = sorted(storage.rglob("*.pdf"))[: args.limit]
        if not files:
            print(f"FAIL: no *.pdf files (recursive) in {storage}")
            return 2

    print("Layer 1 (Vision API) debug run")
    print(f"Files:       {len(files)}")
    print(f"Max pages:   {args.max_pages}")
    print(f"DPI:         {args.dpi}")
    print("=" * 72)

    fail_count = 0
    for i, f in enumerate(files, 1):
        size_kb = f.stat().st_size // 1024
        print(f"\n[{i}/{len(files)}] {f.name}  ({size_kb} KB)")
        print("-" * 72)
        try:
            result = extract_from_path(
                f,
                max_pages=args.max_pages,
                dpi=args.dpi,
            )
        except Exception as e:
            print(f"  EXCEPTION  {type(e).__name__}: {e}")
            traceback.print_exc()
            fail_count += 1
            continue

        print(f"  pages:        {result.page_count}")
        print(f"  elapsed_ms:   {result.elapsed_ms}")
        print(f"  engine:       {result.engine}")
        print(f"  dpi:          {result.dpi}")
        print(f"  language:     {result.language_hints}")

        for page in result.pages:
            stats = _summarize_page(page)
            preview = _format_text_preview(page.full_text)
            print(f"\n  Page {page.page_number}")
            print(f"    size:        {page.width}x{page.height} px")
            print(f"    blocks:      {stats['blocks']}")
            print(f"    paragraphs:  {stats['paragraphs']}")
            print(f"    words:       {stats['words']}")
            print(f"    avg_conf:    {page.avg_confidence:.3f}")
            print(f"    text:        {preview!r}")

            samples = _sample_words(page, n=5)
            if samples:
                print("    sample words (first 5):")
                for w in samples:
                    bb = w.bbox.vertices
                    bb_str = "[" + ", ".join(f"({x},{y})" for x, y in bb) + "]"
                    print(f"      {w.text!r:30s} conf={w.confidence:.3f} bbox={bb_str}")

    print("\n" + "=" * 72)
    if fail_count == 0:
        print(f"OK: {len(files)} / {len(files)} files processed without exception")
        return 0
    print(f"FAIL: {len(files) - fail_count} / {len(files)} OK, {fail_count} failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
