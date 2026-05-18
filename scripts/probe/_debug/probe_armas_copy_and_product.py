#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/probe/_debug/probe_armas_copy_and_product.py

Two probes in one session (saves a login):

1) Customer "Copy from existing" (สำเนา / inpdupdata) flow.
   - Find the inpdupdata button on armas/allform.php
   - Inspect its `onclick=bshlistbox(this)` behavior
   - Open the popup, look at the list shape + the AJAX endpoint it
     pulls from (bshlistboxdata.php response we already captured shows
     the data is preloaded on form load)
   - Simulate "pick customer 0006" → observe which fields get auto-
     populated, then dump every input value for diff vs blank form

2) Product master listing + create form (ระบบสินค้า).
   - From mainmenu, find the product module's URL
   - Visit listing + form
   - Output: list of input fields with types, the checknull rules
     (if any), the inpdupdata equivalent for copy-from-existing

Outputs:
    scripts/probe/_debug/armas_copy_<ts>.json
    scripts/probe/_debug/product_listing_<ts>.html
    scripts/probe/_debug/product_form_<ts>.json
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


def dump_inputs(page) -> dict:
    """Return every input + select value + select options on the page."""
    return page.evaluate("""
        () => {
            const result = {inputs: [], selects: []};
            document.querySelectorAll('input').forEach(i => {
                if (!i.name && !i.id) return;
                result.inputs.push({
                    name: i.name || null,
                    id: i.id || null,
                    type: i.type || null,
                    value: i.value || null,
                    readonly: i.readOnly,
                    placeholder: i.placeholder || null,
                    onclick: i.getAttribute('onclick') || null,
                    onfocus: i.getAttribute('onfocus') || null,
                });
            });
            document.querySelectorAll('select').forEach(s => {
                result.selects.push({
                    name: s.name || null,
                    id: s.id || null,
                    value: s.value || null,
                    options: Array.from(s.options).map(o => ({
                        value: o.value, text: (o.text || '').slice(0, 80),
                    })).slice(0, 20),
                });
            });
            return result;
        }
    """)


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

    adapter.login()
    adapter.select_company()

    ts = int(time.time())
    base = Path(__file__).parent

    # =====================================================
    # PART 1: Customer Copy probe
    # =====================================================
    print("=" * 60)
    print("PART 1: Customer Copy via inpdupdata")
    print("=" * 60)

    captured_resp = []
    def on_resp(r):
        try:
            url = r.url or ""
        except Exception:
            return
        if "armas" in url and (
            "bshlistboxdata" in url or "allform" in url
            or "allsave" in url or "showdata" in url
        ):
            body = ""
            try:
                body = (r.text() or "")[:5000]
            except Exception:
                pass
            captured_resp.append({
                "url": url, "status": r.status,
                "method": r.request.method if r.request else None,
                "body_preview": body,
            })
    ctx.on("response", on_resp)

    page.goto(adapter.login_url + "/armas/allform.php",
              wait_until="networkidle", timeout=15_000)
    page.wait_for_timeout(2_000)

    # State A: blank form
    state_blank = dump_inputs(page)
    print(f"  blank inputs: {len(state_blank['inputs'])}, "
          f"selects: {len(state_blank['selects'])}")

    # Inspect the inpdupdata button — what does it do?
    btn_info = page.evaluate("""
        () => {
            const b = document.getElementById('inpdupdata');
            if (!b) return null;
            return {
                name: b.name, value: b.value,
                onclick: b.getAttribute('onclick'),
                outerHTML: b.outerHTML.slice(0, 500),
            };
        }
    """)
    print(f"  inpdupdata button: {json.dumps(btn_info, ensure_ascii=False)[:400]}")

    # Look at bshlistbox JS function — what does it do for inpdupdata?
    bshlist_src = page.evaluate(
        "typeof bshlistbox === 'function' ? bshlistbox.toString().slice(0, 4000) : null"
    )
    if bshlist_src:
        print(f"\n  bshlistbox(this) source ({len(bshlist_src)} chars):")
        print(bshlist_src)

    # Look at the bshlistbox preloaded data — earlier we saw it has
    # txtrectype + txtacfile entries. Does it have inpdupdata too?
    bshdata = page.evaluate("""
        () => {
            // The data is loaded into a global var by bshlistboxdata.php
            const v = window.bshlistboxdata || window.bshdata || null;
            if (!v) return null;
            const keys = Object.keys(v);
            const summary = {};
            keys.forEach(k => {
                summary[k] = Array.isArray(v[k]) ? v[k].slice(0, 3) : v[k];
            });
            return {keys, summary};
        }
    """)
    print(f"\n  bshlistbox preloaded data: {json.dumps(bshdata, ensure_ascii=False)[:1500]}")

    # Try clicking inpdupdata
    try:
        page.locator('input#inpdupdata').click(timeout=5_000)
        page.wait_for_timeout(1_500)
        # After click, check what new elements/popups appeared
        popup_state = page.evaluate("""
            () => {
                const overlays = Array.from(document.querySelectorAll('div, ul, table'))
                    .filter(el => {
                        const cs = window.getComputedStyle(el);
                        return cs.display !== 'none' && cs.visibility !== 'hidden'
                               && (el.className || '').toLowerCase().includes('bsh');
                    })
                    .slice(0, 5)
                    .map(el => ({
                        tag: el.tagName,
                        class: el.className,
                        id: el.id,
                        html: (el.innerHTML || '').slice(0, 600),
                    }));
                return overlays;
            }
        """)
        print(f"\n  After clicking inpdupdata - popup elements: "
              f"{len(popup_state)} matches")
        for p in popup_state[:3]:
            print(f"    tag={p['tag']} class={p['class']} id={p['id']}")
            print(f"    html: {p['html'][:300]}")
    except Exception as e:
        print(f"  inpdupdata click failed: {e}")

    # Try to pick customer 0006 via the popup. The popup contents may
    # have a clickable row.
    try:
        # Standard bshlistbox uses #bshlistboxlist or similar
        # try to find any element containing "0006" that's clickable
        page.wait_for_timeout(500)
        success = page.evaluate("""
            () => {
                const all = document.querySelectorAll('li, tr, span, div');
                for (const el of all) {
                    const txt = (el.textContent || '').trim();
                    if (txt.startsWith('0006') || txt === '0006') {
                        // Simulate a click
                        if (el.onclick || el.parentElement?.onclick) {
                            (el.onclick || el.parentElement.onclick).call(el);
                            return {clicked: true, text: txt.slice(0, 200)};
                        }
                        // Or just dispatch a click event
                        el.click();
                        return {clicked: true, text: txt.slice(0, 200), how: 'dispatch'};
                    }
                }
                return {clicked: false};
            }
        """)
        print(f"  pick 0006 result: {success}")
        page.wait_for_timeout(2_000)
    except Exception as e:
        print(f"  pick 0006 failed: {e}")

    # State B: after picking 0006
    state_after = dump_inputs(page)
    print(f"\n  After-pick inputs: {len(state_after['inputs'])}, "
          f"selects: {len(state_after['selects'])}")

    # Diff blank vs after — which fields changed?
    blank_map = {(i['name'] or i['id']): i['value'] or ''
                 for i in state_blank['inputs']}
    after_map = {(i['name'] or i['id']): i['value'] or ''
                 for i in state_after['inputs']}
    changes = []
    for k, av in after_map.items():
        bv = blank_map.get(k, '')
        if av != bv and (av or bv):
            changes.append({"field": k, "blank": bv, "after": av})
    print(f"\n  {len(changes)} fields changed:")
    for c in changes[:30]:
        print(f"    {c['field']:30s} {c['blank']!r:30s} -> {c['after']!r}"[:200])

    # Save full state
    (base / f"armas_copy_{ts}.json").write_text(
        json.dumps({
            "blank_inputs": state_blank,
            "after_pick_inputs": state_after,
            "changes": changes,
            "btn_info": btn_info,
            "bshlist_src": bshlist_src,
            "captured_responses": captured_resp[-20:],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n  → wrote armas_copy_{ts}.json")

    # =====================================================
    # PART 2: Product master probe
    # =====================================================
    print("\n" + "=" * 60)
    print("PART 2: Product (ระบบสินค้า) master")
    print("=" * 60)

    # Step 1: Navigate to mainmenu and find product-master menu link
    page.goto(adapter.login_url + "/login/mainmenu.php"
              f"?comidyear={adapter.comidyear}&seldb={adapter.seldb}",
              wait_until="networkidle", timeout=15_000)

    # Look for product-related links / menu items via JS
    product_menu = page.evaluate("""
        () => {
            const out = [];
            // m3 = ระบบสินค้า per known-facts §10
            const m3 = document.querySelector('[data-code="m3"]');
            if (m3) {
                m3.click();
                // Wait a tick for submenu render
            }
            // Find all <a> tags whose href looks like product master paths
            // Common patterns: stmas / prmas / pdmas / pdstmas
            const links = Array.from(document.querySelectorAll('a, span[onclick]'));
            for (const el of links) {
                const href = el.getAttribute('href') || '';
                const onclick = el.getAttribute('onclick') || '';
                const text = (el.textContent || '').trim();
                if (
                    href.includes('mas/') || href.includes('stm') ||
                    onclick.includes('mas/') ||
                    text.includes('สินค้า') || text.includes('Product')
                ) {
                    out.push({href, onclick, text: text.slice(0, 80)});
                }
            }
            return out.slice(0, 30);
        }
    """)
    print(f"  product menu candidates: {len(product_menu)}")
    for m in product_menu[:15]:
        print(f"    href={m.get('href','')[:80]:60s} text={m.get('text','')[:40]}")

    # Try common product-master path guesses
    candidates = [
        "/stmas/allview.php",
        "/prmas/allview.php",
        "/itmas/allview.php",
        "/pdmas/allview.php",
        "/stkmas/allview.php",
    ]
    product_listing_url = None
    for c in candidates:
        url = adapter.login_url + c
        try:
            page.goto(url, wait_until="networkidle", timeout=10_000)
            html = page.content() or ""
            if "404" in html[:200] or "ไม่พบ" in html[:200] or len(html) < 500:
                continue
            # check if it has showdata
            if 'id="showdata"' in html or "allform.php" in html:
                product_listing_url = c
                (base / f"product_listing_{ts}.html").write_text(
                    html, encoding="utf-8")
                print(f"\n  ✓ found product listing at {c} ({len(html)} bytes)")
                break
        except Exception as e:
            print(f"    tried {c}: {e}")
    if not product_listing_url:
        print("  ⚠ no product listing URL discovered via common guesses")

    # If found, also probe the create form
    if product_listing_url:
        form_url = product_listing_url.replace("allview.php", "allform.php")
        page.goto(adapter.login_url + form_url,
                  wait_until="networkidle", timeout=15_000)
        page.wait_for_timeout(1_500)
        state_product = dump_inputs(page)
        # Try to grab checknull source
        cn_src = page.evaluate(
            "typeof checknull === 'function' ? checknull.toString() : null"
        )
        (base / f"product_form_{ts}.json").write_text(
            json.dumps({
                "listing_url": product_listing_url,
                "form_url": form_url,
                "inputs": state_product["inputs"],
                "selects": state_product["selects"],
                "checknull": cn_src,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  → wrote product_form_{ts}.json")
        print(f"  product form inputs: {len(state_product['inputs'])}")
        print(f"  has checknull(): {bool(cn_src)}")

print("\n--- probe done ---")
