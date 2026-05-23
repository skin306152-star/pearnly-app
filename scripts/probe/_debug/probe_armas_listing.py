#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/probe/_debug/probe_armas_listing.py

Diagnostic: capture the structure of MR.ERP's customer master listing
(armas/allview.php) so the customer-sync service knows what to parse.

Run:
    python scripts/probe/_debug/probe_armas_listing.py

Outputs:
    scripts/probe/_debug/armas_listing_<ts>.html  (raw)
    scripts/probe/_debug/armas_listing_<ts>.json  (parsed sample rows)
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

    # Customer master listing.
    list_url = adapter.login_url + "/armas/allview.php"
    print(f"GET {list_url}")
    page.goto(list_url, wait_until="networkidle", timeout=15_000)
    html = page.content() or ""

    ts = int(time.time())
    out_html = Path(__file__).parent / f"armas_listing_{ts}.html"
    out_html.write_text(html, encoding="utf-8")
    print(f"saved {out_html.name} ({len(html)} bytes)")

    # First quick parse: look for any rows resembling artran format
    # (<p>...code...<a href="allform.php?id=N&status=del">).
    rows = []
    pattern = re.compile(
        r"<p\b[^>]*>(?P<body>.*?)</p>",
        re.DOTALL,
    )
    for m in pattern.finditer(html):
        body = m.group("body")
        # Detect rows that hold customer references
        if "allform.php?id=" in body and "armas" in m.group(0).lower() or "allform.php?id=" in body:
            spans = re.findall(r"<span\b[^>]*>(.*?)</span>", body, re.DOTALL)
            del_match = re.search(
                r'allform\.php\?id=(\d+)[^"]*status=del',
                body,
            )
            rows.append(
                {
                    "spans": [re.sub(r"<[^>]+>", "", s).strip()[:80] for s in spans],
                    "delete_id": del_match.group(1) if del_match else None,
                    "raw_html_preview": body[:300].strip(),
                }
            )

    out_json = Path(__file__).parent / f"armas_listing_{ts}.json"
    out_json.write_text(
        json.dumps(
            {
                "url": page.url,
                "html_size": len(html),
                "row_count": len(rows),
                "rows_sample": rows[:5],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"saved {out_json.name} ({len(rows)} rows)")
    print("\n--- first 3 rows ---")
    for r in rows[:3]:
        print(json.dumps(r, ensure_ascii=False, indent=2)[:1500])
