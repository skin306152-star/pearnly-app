#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/probe/_debug/probe_armas_save_response.py

Capture the actual server response when the customer-create form is
submitted, so we know why the alert 'Data is use in the system' fires.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env.local")

from services.erp.mrerp_adapter import MRERPAdapter
from services.erp.mrerp_customer_sync import MRERPCustomerSyncService, BuyerInfo

with MRERPAdapter(
    login_url=os.environ["MRERP_LOGIN_URL"],
    username=os.environ["MRERP_USERNAME"],
    password=os.environ["MRERP_PASSWORD"],
    comidyear="6",
    seldb="1",
    headless=True,
) as a:
    page = a._page
    ctx = a._session._ctx

    # Capture all responses + their bodies for armas paths
    captured = []

    def on_resp(r):
        try:
            url = r.url or ""
        except Exception:
            return
        if "armas" not in url:
            return
        body_text = ""
        try:
            body_text = r.text() or ""
        except Exception:
            pass
        captured.append(
            {
                "url": url,
                "status": r.status,
                "ct": r.headers.get("content-type", ""),
                "body_preview": body_text[:2000],
                "method": r.request.method if r.request else "",
            }
        )

    ctx.on("response", on_resp)

    # Look at form action attribute too
    a.login()
    a.select_company()
    page.goto(a.login_url + "/armas/allform.php", wait_until="networkidle")

    action = page.evaluate(
        'document.getElementById("frm") ? document.getElementById("frm").action : null'
    )
    method = page.evaluate(
        'document.getElementById("frm") ? document.getElementById("frm").method : null'
    )
    print(f"form action: {action}")
    print(f"form method: {method}")

    # Run the actual fill logic via the service so we exercise the real path
    svc = MRERPCustomerSyncService(a)
    buyer = BuyerInfo(
        name=f"Pearnly Probe Save Test {os.urandom(4).hex().upper()}",
        client_id=99999,
        tenant_id="probe",
        tax_id="1234567890123",
    )
    try:
        out = svc.lookup_or_create(buyer, {"clients": []})
        print(f"OK code={out.customer_code} source={out.source}")
    except Exception as e:
        print(f"FAILED: {e}")

    # Dump captured responses
    print(f"\n--- {len(captured)} armas responses ---")
    for r in captured[-10:]:
        print(f"[{r['method']}] {r['status']} {r['url'][:100]}  ct={r['ct'][:40]}")
        if r["body_preview"]:
            # Look for the alert string
            if "Data is" in r["body_preview"]:
                idx = r["body_preview"].find("Data is")
                snippet = r["body_preview"][max(0, idx - 200) : idx + 500]
                print(f"  >>> Data is alert context: {snippet[:700]}")
            else:
                first_300 = re.sub(r"\s+", " ", r["body_preview"][:300])
                print(f"  body[:300]: {first_300}")
