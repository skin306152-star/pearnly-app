#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/probe/_debug/probe_armas_delete.py

Probe the delete pathway for an armas (customer) row. Goal: find what
URL pattern accepts a "delete this customer" request, so the auto-create
integration test can clean up after itself.

Strategy: scrape the customer-listing detail/click handlers + try several
candidate URLs that mirror the artran pattern.

Read-only — no actual deletes. Outputs a JSON report.
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

    report = {}

    # 1. Look at listing HTML for any onclick handlers that look like delete
    page.goto(adapter.login_url + "/armas/allview.php",
              wait_until="networkidle", timeout=15_000)
    listing = page.content() or ""
    matches = re.findall(
        r'(?:href|onclick)=["\']([^"\']*(?:del|delete|edit|view|allform)[^"\']*)["\']',
        listing, re.IGNORECASE,
    )
    report["listing_link_patterns"] = list(set(matches))[:30]

    # 2. Try fetching allform.php with the customer code as id
    test_id = "0006"
    for status in ("view", "edit", "del"):
        url = adapter.login_url + f"/armas/allform.php?id={test_id}&status={status}"
        try:
            page.goto(url, wait_until="networkidle", timeout=10_000)
            html = page.content() or ""
            # Look for btndel button presence
            has_btndel = 'id="btndel"' in html or "btndel" in html.lower()
            report[f"status_{status}"] = {
                "url": url,
                "final_url": page.url,
                "has_btndel": has_btndel,
                "html_size": len(html),
                "html_head_500": re.sub(r"\s+", " ", html[:500])[:500],
            }
        except Exception as e:
            report[f"status_{status}"] = {"url": url, "error": str(e)[:200]}

    # 3. Try the customer code as a query param variant
    for variant in (
        "?txtarcode=0006",
        "?arcode=0006",
        "?code=0006",
    ):
        url = adapter.login_url + f"/armas/allform.php{variant}"
        try:
            page.goto(url, wait_until="networkidle", timeout=10_000)
            html = page.content() or ""
            report[f"variant_{variant}"] = {
                "url": url,
                "final_url": page.url,
                "html_size": len(html),
                "has_data": "Skin Trading" in html or "0006" in html,
            }
        except Exception as e:
            report[f"variant_{variant}"] = {"error": str(e)[:200]}

    ts = int(time.time())
    out = Path(__file__).parent / f"armas_delete_probe_{ts}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"saved {out.name}")
    print(json.dumps(report, ensure_ascii=False, indent=2)[:3000])
