#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/probe/_debug/trace_uploadfrm.py

Throwaway diagnostic: hooks every HTTP response in the Playwright context
to find out where report.php's response goes. If we never see it, either
sdpt() doesn't fire, importpc.php takes ages, or the request happens in
a context Playwright doesn't observe.

Run:
    python scripts/probe/_debug/trace_uploadfrm.py

Outputs:
    scripts/probe/_debug/trace_uploadfrm_<ts>.json
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env.local")

from services.erp import mrerp_xlsx_generator

from services.erp.mrerp_adapter import MRERPAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("trace")

inv_no = f"PEARNLY-TEST-{uuid.uuid4().hex[:4].upper()}"
mrerp_xlsx_generator.derive_mrerp_invoice_no = lambda h: inv_no

events: list[dict] = []

with MRERPAdapter(
    login_url=os.environ["MRERP_LOGIN_URL"],
    username=os.environ["MRERP_USERNAME"],
    password=os.environ["MRERP_PASSWORD"],
    comidyear=os.environ.get("MRERP_COMIDYEAR", "6"),
    seldb=os.environ.get("MRERP_SELDB", "1"),
    headless=True,
) as adapter:
    ctx = adapter._session._ctx
    page = adapter._page

    def on_resp(r):
        body_preview = None
        if "importpc.php" in r.url or "report.php" in r.url:
            try:
                body_preview = (r.text() or "")[:1000]
            except Exception as e:
                body_preview = f"<read fail: {e}>"
        events.append(
            {
                "t": time.time(),
                "kind": "response",
                "url": r.url,
                "status": r.status,
                "content_type": r.headers.get("content-type", ""),
                "body_preview": body_preview,
            }
        )

    def on_page(p):
        events.append(
            {
                "t": time.time(),
                "kind": "popup_page",
                "url": p.url,
            }
        )

    def on_console(msg):
        text = msg.text[:200] if msg.text else ""
        events.append(
            {
                "t": time.time(),
                "kind": "console",
                "type": msg.type,
                "text": text,
            }
        )

    ctx.on("response", on_resp)
    ctx.on("page", on_page)
    page.on("console", on_console)

    adapter.login()
    adapter.select_company()

    # Build minimal test history
    history = {
        "client_id": 99,
        "invoice_number": inv_no,
        "invoice_date": "2026-05-18",
        "subtotal": "100.00",
        "vat": "7.00",
        "total_amount": "107.00",
        "items": [
            {
                "name": f"TEST {inv_no}",
                "qty": 1,
                "unit_price": 100,
                "amount": 100,
            }
        ],
    }
    mappings = {
        "clients": [
            {
                "erp_type": "mrerp",
                "client_id": 99,
                "erp_code": "0006",
            }
        ],
        "accounts": [],
        "taxes": [],
        "products": [],
    }

    log.info("uploading invoice_no=%s", inv_no)
    try:
        # We want to manually do the flow so we can inspect after timeout.
        xlsx_bytes = mrerp_xlsx_generator.generate_xlsx(
            [history], mappings, sheet_kind="sales_credit"
        )
        # Manually nav + upload + confirm using adapter's lower helpers.
        # (We bypass upload_invoice_batch so the event log captures
        # everything explicitly.)
        result = adapter._upload_and_fetch_report(
            xlsx_bytes,
            expected_invoices=[inv_no],
        )
        log.info(
            "upload_invoice_batch returned report_bytes=%s",
            "Y" if result else "N (listing fallback)",
        )
    except Exception as e:
        log.error("flow raised: %s", e)
        events.append({"t": time.time(), "kind": "exception", "msg": str(e)})

    # Capture state of sdpt patch
    try:
        sdpt_src = page.evaluate("typeof sdpt === 'function' ? sdpt.toString() : null")
        events.append(
            {
                "t": time.time(),
                "kind": "sdpt_source",
                "src": (sdpt_src or "")[:600],
            }
        )
    except Exception as e:
        log.warning("sdpt source fetch failed: %s", e)

    # Cleanup attempt
    try:
        rec = adapter.search_invoice(inv_no)
        if rec:
            adapter.delete_invoice(rec.db_row_id)
            log.info("cleaned up db_row_id=%s", rec.db_row_id)
    except Exception as e:
        log.warning("cleanup failed: %s", e)

# Persist
ts = int(time.time())
outpath = Path(__file__).parent / f"trace_uploadfrm_{ts}.json"
outpath.write_text(
    json.dumps({"invoice_no": inv_no, "events": events}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
log.info("wrote %s (%d events)", outpath, len(events))

# Tail-print the last 30 events for quick eyeball
print("\n=== Last 30 events ===")
for ev in events[-30:]:
    print(json.dumps(ev, ensure_ascii=False, default=str))
