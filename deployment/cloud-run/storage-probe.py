"""Verify mounted storage across separate Cloud Run Job executions.

Run write, then read in a separate execution, then cleanup. Each invocation only
accesses its explicitly named probe file. Chromium can be checked independently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOTS = (
    Path("/opt/mrpilot/storage"),
    Path("/opt/mrpilot/uploads"),
    Path("/opt/mrpilot/var"),
)


def probe_storage(phase, nonce, roots=ROOTS):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{16,80}", nonce):
        raise ValueError("nonce must contain 16-80 letters, digits, underscores or hyphens")
    if phase not in {"write", "read", "cleanup"}:
        raise ValueError("invalid storage probe phase")
    payload = f"pearnly-cloud-run-storage-probe:{nonce}".encode()
    results = []
    for root in roots:
        path = root / f".migration-probe-{nonce}"
        if phase == "write":
            # Do not overwrite another execution's evidence.
            with path.open("xb") as stream:
                stream.write(payload)
        elif phase == "read":
            if path.read_bytes() != payload:
                raise RuntimeError(f"probe content mismatch at {root}")
        else:
            path.unlink(missing_ok=True)
        results.append({"root": str(root), "phase": phase, "ok": True})
    return {"storage": results, "sha256": hashlib.sha256(payload).hexdigest()}


def probe_chromium():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--disable-dev-shm-usage"])
        try:
            page = browser.new_page()
            page.set_content("<title>Pearnly Chromium probe</title><p>ready</p>")
            if page.title() != "Pearnly Chromium probe":
                raise RuntimeError("Chromium page rendering failed")
            return {"chromium": {"ok": True, "version": browser.version}}
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["write", "read", "cleanup"])
    parser.add_argument("--nonce")
    parser.add_argument("--chromium", action="store_true")
    args = parser.parse_args()
    if not args.phase and not args.chromium:
        parser.error("choose a storage phase or --chromium")
    if args.phase and not args.nonce:
        parser.error("--nonce is required for a storage phase")
    result = probe_storage(args.phase, args.nonce) if args.phase else {}
    if args.chromium:
        result.update(probe_chromium())
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
