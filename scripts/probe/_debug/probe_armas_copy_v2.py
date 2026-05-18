#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/probe/_debug/probe_armas_copy_v2.py

V2 of the inpdupdata copy probe. Difference: actually wait for the
bshlistbox AJAX to load + use Playwright UI click on the row instead of
JS injection (which fires before bshlistboxdata is populated).
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
    page = adapter._page
    ctx = adapter._session._ctx
    adapter.login(); adapter.select_company()

    ts = int(time.time())
    base = Path(__file__).parent

    captured_resp = []
    def on_resp(r):
        try:
            url = r.url or ""
        except Exception:
            return
        if "armas" in url:
            body = ""
            try:
                body = (r.text() or "")[:8000]
            except Exception:
                pass
            captured_resp.append({"url": url, "status": r.status, "body": body[:5000]})
    ctx.on("response", on_resp)

    page.goto(adapter.login_url + "/armas/allform.php", wait_until="networkidle")
    page.wait_for_timeout(2000)

    print("Form loaded. Clicking inpdupdata via locator...")
    page.locator('input#inpdupdata').first.click(timeout=5000)
    # Wait LONGER for the bshlistbox AJAX
    page.wait_for_timeout(3500)

    # Now look at all visible elements that might be the listbox popup
    popup_state = page.evaluate("""
        () => {
            const visible = [];
            document.querySelectorAll('*').forEach(el => {
                let cs;
                try { cs = window.getComputedStyle(el); } catch (e) { return; }
                if (!cs || cs.display === 'none' || cs.visibility === 'hidden') return;
                const id = String(el.id || '');
                const cls = typeof el.className === 'string'
                    ? el.className
                    : (el.className?.baseVal || '');
                if (
                    id.toLowerCase().includes('bsh') ||
                    cls.toLowerCase().includes('bsh') ||
                    id === 'bshlistboxdetail' ||
                    cls.toLowerCase().includes('listbox')
                ) {
                    visible.push({
                        tag: el.tagName, id, class: cls,
                        innerText_first_300: (el.innerText || '').slice(0, 300),
                        outerHTML_first_500: (el.outerHTML || '').slice(0, 500),
                    });
                }
            });
            return visible.slice(0, 5);
        }
    """)
    print(f"\nbsh-related visible elements: {len(popup_state)}")
    for el in popup_state[:5]:
        print(f"  tag={el['tag']} id={el['id']} class={el['class']}")
        print(f"    text: {el['innerText_first_300'][:200]}")

    # Look at what bshlistboxdata is now (after AJAX)
    bshdata_now = page.evaluate("""
        () => {
            const v = window.bshlistboxdata;
            if (!v) return null;
            if (Array.isArray(v)) {
                return {type: 'array', len: v.length, sample: v.slice(0, 5)};
            }
            return {type: typeof v, keys: Object.keys(v).slice(0, 10),
                    sample_first: v[Object.keys(v)[0]]?.slice ? v[Object.keys(v)[0]].slice(0, 3) : null};
        }
    """)
    print(f"\nbshlistboxdata after click: {json.dumps(bshdata_now, ensure_ascii=False)[:800]}")

    # Look at the popup HTML structure for the 0006 row
    bshdetail_html = page.evaluate("""
        () => {
            const el = document.getElementById('bshlistboxdetail');
            if (!el) return null;
            return el.innerHTML.slice(0, 3000);
        }
    """)
    if bshdetail_html:
        print(f"\nbshlistboxdetail innerHTML (first 1500 chars):")
        print(bshdetail_html[:1500])

    # Find the click handler used to pick a row, e.g. bshlistboxdata2field
    pick_fn_src = page.evaluate(
        "typeof bshlistboxdata2field === 'function' ? "
        "bshlistboxdata2field.toString().slice(0, 4000) : null"
    )
    if pick_fn_src:
        print(f"\nbshlistboxdata2field source (first 3000):")
        print(pick_fn_src[:3000])

    # Try to click the actual 0006 row in the popup using Playwright UI
    try:
        # Probably <span> elements inside bshlistboxdetail
        all_spans_with_text = page.evaluate("""
            () => {
                const detail = document.getElementById('bshlistboxdetail');
                if (!detail) return [];
                return Array.from(detail.querySelectorAll('*'))
                    .filter(el => {
                        const t = (el.textContent || '').trim();
                        return t === '0006' || t.startsWith('0006');
                    })
                    .slice(0, 3)
                    .map(el => ({
                        tag: el.tagName, id: el.id || '',
                        class: el.className || '',
                        onclick: el.getAttribute('onclick') || '',
                        text: (el.textContent || '').trim().slice(0, 100),
                    }));
            }
        """)
        print(f"\n0006 row candidates in popup: {len(all_spans_with_text)}")
        for s in all_spans_with_text:
            print(f"  {s}")

        # Locate the 0006 row clickable element and click via Playwright
        # Find inner span with text "0006" inside bshlistboxdetail
        loc = page.locator('#bshlistboxdetail >> text=0006').first
        if loc.count() > 0:
            loc.click(timeout=3000)
            print("\n  ✓ clicked 0006 row")
        else:
            print("\n  ⚠ couldn't locate 0006 row")
        page.wait_for_timeout(2500)
    except Exception as e:
        print(f"  click row failed: {e}")

    # Now dump the form state
    final_state = page.evaluate("""
        () => {
            const out = {};
            document.querySelectorAll('input').forEach(i => {
                if (i.name || i.id) {
                    const k = i.name || i.id;
                    if (i.value || i.type === 'hidden') out[k] = i.value || '';
                }
            });
            document.querySelectorAll('select').forEach(s => {
                if (s.name || s.id) {
                    out[s.name || s.id] = s.value || '';
                }
            });
            return out;
        }
    """)
    print(f"\nFinal form populated fields ({len(final_state)} total non-empty):")
    for k, v in sorted(final_state.items()):
        if v:
            print(f"  {k:30s} = {v!r}"[:200])

    # Save full state
    (base / f"armas_copy_v2_{ts}.json").write_text(
        json.dumps({
            "final_state": final_state,
            "bshdata_after_click": bshdata_now,
            "popup_html_preview": bshdetail_html,
            "pick_fn_src": pick_fn_src,
            "armas_resp_urls": [r["url"] for r in captured_resp][-15:],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n  → wrote armas_copy_v2_{ts}.json")
