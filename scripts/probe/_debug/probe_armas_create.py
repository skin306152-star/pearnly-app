#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/probe/_debug/probe_armas_create.py

Diagnostic: dump the structure of MR.ERP's customer-create form
(armas/allform.php) so the customer-sync auto-create flow knows which
inputs to fill and which button to click.

Run:
    python scripts/probe/_debug/probe_armas_create.py

Outputs:
    scripts/probe/_debug/armas_create_<ts>.html
    scripts/probe/_debug/armas_create_<ts>.json (input/select/button summary)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env.local")

from services.erp.mrerp_adapter import MRERPAdapter


def summarize_form(html: str) -> dict:
    inputs = []
    for m in re.finditer(
        r'<input\b([^>]*?)>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        attrs = m.group(1)
        rec = {}
        for k in ("name", "id", "type", "value", "placeholder", "onclick",
                  "onchange"):
            mm = re.search(
                rf'\b{k}\s*=\s*["\']([^"\']*)["\']',
                attrs,
                re.IGNORECASE,
            )
            if mm:
                rec[k] = mm.group(1)[:120]
        if rec:
            inputs.append(rec)
    buttons = []
    for m in re.finditer(
        r'<button\b([^>]*?)>(.*?)</button>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        attrs, inner = m.group(1), m.group(2)
        rec = {}
        for k in ("name", "id", "type", "onclick"):
            mm = re.search(
                rf'\b{k}\s*=\s*["\']([^"\']*)["\']',
                attrs,
                re.IGNORECASE,
            )
            if mm:
                rec[k] = mm.group(1)[:120]
        rec["text"] = re.sub(r"<[^>]+>", "", inner).strip()[:120]
        if rec.get("text") or rec.get("onclick"):
            buttons.append(rec)
    selects = []
    for m in re.finditer(
        r'<select\b([^>]*?)>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        attrs = m.group(1)
        rec = {}
        for k in ("name", "id", "onchange"):
            mm = re.search(
                rf'\b{k}\s*=\s*["\']([^"\']*)["\']',
                attrs,
                re.IGNORECASE,
            )
            if mm:
                rec[k] = mm.group(1)[:120]
        if rec:
            selects.append(rec)
    return {"inputs": inputs, "buttons": buttons, "selects": selects}


with MRERPAdapter(
    login_url=os.environ["MRERP_LOGIN_URL"],
    username=os.environ["MRERP_USERNAME"],
    password=os.environ["MRERP_PASSWORD"],
    comidyear=os.environ.get("MRERP_COMIDYEAR", "6"),
    seldb=os.environ.get("MRERP_SELDB", "1"),
    headless=True,
) as adapter:
    adapter.login()
    adapter.select_company()
    page = adapter._page

    # Customer-create form: armas/allform.php with no id arg = "create".
    target_url = adapter.login_url + "/armas/allform.php"
    print(f"GET {target_url}")
    page.goto(target_url, wait_until="networkidle", timeout=15_000)
    html = page.content() or ""

    ts = int(time.time())
    base = Path(__file__).parent
    (base / f"armas_create_{ts}.html").write_text(html, encoding="utf-8")
    summary = summarize_form(html)
    (base / f"armas_create_{ts}.json").write_text(
        json.dumps({
            "url": page.url,
            "html_size": len(html),
            **summary,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"saved armas_create_{ts}.html ({len(html)} bytes)")
    print(f"inputs={len(summary['inputs'])} buttons={len(summary['buttons'])} selects={len(summary['selects'])}")
    print("\n--- first 20 inputs ---")
    for inp in summary["inputs"][:20]:
        print(json.dumps(inp, ensure_ascii=False)[:200])
    print("\n--- first 10 buttons ---")
    for b in summary["buttons"][:10]:
        print(json.dumps(b, ensure_ascii=False)[:200])
    print("\n--- first 10 selects ---")
    for s in summary["selects"][:10]:
        print(json.dumps(s, ensure_ascii=False)[:200])
