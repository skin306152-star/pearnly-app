"""Read-only parity check against separately stored, user-owned pilot outputs.

Usage: PYTHONPATH=. python scripts/verify_enterprise_local_parity.py PILOT_DIRECTORY
No cloud calls, gold answers never enter the extraction function, no raw data printed.
"""

import argparse
import json
from pathlib import Path

from services.ocr.enterprise_local.result import reconstruct


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot_directory", type=Path)
    root = parser.parse_args().pilot_directory
    failed = False
    for category, pages, raw_files, expected_file in (
        (
            "bank",
            18,
            ["bank_pages_01_15.raw.json", "bank_pages_16_18.raw.json"],
            "bank_result_final.json",
        ),
        ("gl", 7, ["gl_ttb_7_pages.raw.json"], "gl_result_final.json"),
    ):
        payloads = [json.loads((root / "raw" / name).read_text()) for name in raw_files]
        actual = reconstruct(payloads, category, expected_pages=pages)
        # Expected data is read only AFTER extraction, and is never passed to it.
        expected = json.loads((root / expected_file).read_text())
        schema_same = actual.document == expected["schema"]
        audit_same = actual.audit == expected["audit"]
        result = {
            "category": category,
            "pages": pages,
            "rows": len(actual.document.get("entries") or []),
            "schema_identical": schema_same,
            "audit_identical": audit_same,
            "runtime_issues": actual.issues,
            "requires_review": actual.requires_review,
            "scope": "cached_response_parity_not_live_accuracy",
        }
        print(json.dumps(result))
        failed |= not (schema_same and audit_same and actual.arithmetic_passed)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
