#!/usr/bin/env python3
"""
services/ocr/connectivity_check.py

Pre-Stage-3 connectivity check for Google Cloud Vision API integration.
Must pass on both local dev machine and production server before proceeding
to Stage 3 (writing services/ocr/layer1_vision.py).

Usage:
    python services/ocr/connectivity_check.py
    python -m services.ocr.connectivity_check

Exit code:
    0  = all 6 checks pass
    N  = first failing check number (1-6)
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

# 1x1 transparent PNG, base64 encoded - valid PNG accepted by Vision API.
# Used for minimal connectivity test only; not for text recognition.
_PIXEL_PNG_B64 = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAA"
    b"YAAjCB0C8AAAAASUVORK5CYII="
)


def _print(label, status, detail=""):
    line = f"[{status:4s}] {label}"
    if detail:
        line += f" -- {detail}"
    print(line)


def _fail(check_num, label, detail):
    _print(label, "FAIL", detail)
    print(f"\nConnectivity check FAILED at step {check_num}/6.")
    sys.exit(check_num)


def main():
    print("=" * 60)
    print("Pearnly OCR  Google Cloud Vision connectivity check")
    print("=" * 60)
    print(f"Python:      {sys.version.split()[0]}")
    print(f"Working dir: {os.getcwd()}")
    print(f"Platform:    {sys.platform}")
    print()

    # === Check 1: env var ===
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        _fail(
            1,
            "GOOGLE_APPLICATION_CREDENTIALS set",
            "env variable not set. See migration-plan.md Section 7 step 3/4.",
        )
    _print(f"env GOOGLE_APPLICATION_CREDENTIALS = {creds_path}", "PASS")

    # === Check 2: file exists + readable + parsable + service_account format ===
    p = Path(creds_path)
    if not p.exists():
        _fail(2, "Credentials file exists", f"path not found: {creds_path}")
    if not p.is_file():
        _fail(2, "Credentials path is a file", f"is a directory: {creds_path}")
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except PermissionError as e:
        _fail(2, "Credentials file readable", str(e))
    except json.JSONDecodeError as e:
        _fail(2, "Credentials file is valid JSON", str(e))
    except Exception as e:
        _fail(2, "Credentials file can be opened", f"{type(e).__name__}: {e}")

    required_keys = ["type", "project_id", "private_key", "client_email"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        _fail(2, "JSON has service_account fields", f"missing keys: {missing}")
    if data.get("type") != "service_account":
        _fail(2, "JSON type is service_account", f"got type={data.get('type')!r}")
    project_id = data.get("project_id")
    client_email = data.get("client_email")
    _print(f"JSON parsed: project_id={project_id} client_email={client_email}", "PASS")

    # === Check 3: import google.cloud.vision ===
    try:
        from google.cloud import vision
    except ImportError as e:
        _fail(
            3, "import google.cloud.vision", f"{e}. Install with: pip install google-cloud-vision"
        )
    _print("import google.cloud.vision OK", "PASS")

    # === Check 4: create ImageAnnotatorClient ===
    try:
        client = vision.ImageAnnotatorClient()
    except Exception as e:
        _fail(4, "vision.ImageAnnotatorClient()", f"{type(e).__name__}: {e}")
    _print("ImageAnnotatorClient() created", "PASS")

    # === Check 5: minimal API call ===
    elapsed_ms = -1
    try:
        img_bytes = base64.b64decode(_PIXEL_PNG_B64)
        image = vision.Image(content=img_bytes)
        t0 = time.time()
        resp = client.document_text_detection(
            image=image,
            image_context={"language_hints": ["th", "en"]},
        )
        elapsed_ms = int((time.time() - t0) * 1000)
    except Exception as e:
        _fail(5, "Vision API document_text_detection call", f"{type(e).__name__}: {e}")

    error = getattr(resp, "error", None)
    if error is not None and getattr(error, "code", 0) != 0:
        _fail(5, "API response no error", f"code {error.code}: {error.message}")
    full_text_len = len(resp.full_text_annotation.text or "")
    _print(f"API call OK (latency: {elapsed_ms}ms, " f"full_text_len: {full_text_len})", "PASS")

    # === Check 6: report summary ===
    print()
    print("--- Summary ---")
    print(f"  Project ID:    {project_id}")
    print(f"  SA email:      {client_email}")
    print(f"  API latency:   {elapsed_ms}ms")
    print("  Endpoint:      vision.googleapis.com (direct, no proxy)")
    _print("Summary printed", "PASS")

    print()
    print("=" * 60)
    print("ALL 6 CHECKS PASSED. Ready for Stage 3 layer1_vision.py.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
