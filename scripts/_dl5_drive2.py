# -*- coding: utf-8 -*-
"""DL-5 forensic driver · phase 2 (single-cred, reuse customer 107).

Underscore = not shipped. Proves the rest of the LINE car-sales chain with REAL
DMS writes once the admin-writer defect (phase 1) is routed around by using the
admin-capable dmstest user session directly. Covers: dedup exact/idempotent
(G2), diff detection (G3), booking (G5), one-time token replay (G7). The admin
config path (G1 create / G3 update over LINE) is broken — see phase 1.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly?sslmode=disable",
)
os.environ["PGSSLMODE"] = "disable"
os.environ["LINE_DMS_CHANNEL_SECRET"] = "e2e-test-secret"
os.environ.setdefault("JWT_SECRET", "dl5-e2e-jwt-secret-please-32chars-long")

from scripts import _dl5_common as C  # noqa: E402
from scripts._dl5_drive import (  # noqa: E402
    RESULTS,
    record,
    save,
    http_get,
    reset_conversation,
    clear_session,
    nonce_of,
    push_logs_by_mode,
)


def exact_and_pick_setup():
    """Bind + exact-match dedup on existing customer 107 → TXT_SAME + pick button.
    Covers G2 (idempotent, zero write, readback unchanged). Returns pick token."""
    from services.line_dms import store

    reset_conversation()
    code = store.generate_bind_code(C.TENANT_ID, C.USER_ID)["code"]
    b0 = C.outbox_len()
    C.post_webhook([C.ev_text(code)])
    _, bind = C.wait_outbox(
        lambda r: r["kind"] == "reply_text" and "เชื่อมต่อสำเร็จ" in r["text"], since=b0, timeout=15
    )
    record("G1b", "bind code → BIND_OK (real webhook)", bool(bind), f"bind_ok={bool(bind)}")

    creates_before = len(push_logs_by_mode("create"))
    over_before = len(push_logs_by_mode("overwrite"))
    C.set_ocr(C.id_card_g1())
    b = C.outbox_len()
    C.post_webhook([C.ev_image()])
    C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "เบอร์โทร" in r["text"], since=b, timeout=60
    )
    b2 = C.outbox_len()
    C.post_webhook([C.ev_text(C.PHONE)])
    _, same = C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "ข้อมูลตรงกัน" in r["text"], since=b2, timeout=120
    )
    _, pick = C.wait_outbox(
        lambda r: r["kind"] == "push_messages"
        and any(d.startswith("URI::") and "dms-pick" in d for d in C.flex_buttons(r)),
        since=b2,
        timeout=120,
    )
    save("g2_exact_outbox.json", C.read_outbox()[b2:])

    rb = C.lookup(C.PID_GOOD)
    f = rb.get("fields") or {}
    unchanged = (
        f.get("house_no") == C.ADDR_G1["house_no"]
        and f.get("name") == C.FULL_NAME
        and f.get("phone") == C.PHONE
        and f.get("birthday_be") == C.BIRTHDAY_BE
    )
    no_write = (
        len(push_logs_by_mode("create")) == creates_before
        and len(push_logs_by_mode("overwrite")) == over_before
    )
    save("g2_readback.json", rb)
    record(
        "G2",
        "idempotent exact-match (data matches, zero write)",
        bool(same) and unchanged and no_write,
        f"TXT_SAME={bool(same)} readback_unchanged={unchanged} no_write={no_write} cid={rb.get('customer_id')}",
        ["g2_exact_outbox.json", "g2_readback.json"],
    )

    if not pick:
        return None
    save("g5_pick_button.json", pick)
    uri = [d[5:] for d in C.flex_buttons(pick) if d.startswith("URI::")][0]
    return (parse_qs(urlparse(uri).query).get("t") or [""])[0]


def booking(token):
    """G5: drive the real pick page → submit → confirm → real booking + readback.
    G7: replay the (rotated) token → 401."""
    from playwright.sync_api import sync_playwright

    local_url = f"{C.BASE}/dms-pick?t={token}"
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        pg = br.new_page(viewport={"width": 390, "height": 844})
        pg.goto(local_url, wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_selector("[data-car]", timeout=90000)
        pg.screenshot(path=str(C.art("g5_1_car_list.png")))
        pg.query_selector("[data-car]").click()
        pg.wait_for_selector("[data-paint]", timeout=90000)
        pg.screenshot(path=str(C.art("g5_2_paints.png")))
        pg.query_selector("[data-paint]").click()
        pg.wait_for_function("!document.getElementById('pk-submit').disabled", timeout=15000)
        pg.click("#pk-submit")
        pg.wait_for_selector(".state.ok", timeout=120000)
        pg.screenshot(path=str(C.art("g5_3_success.png")))
        br.close()

    st, _ = http_get(f"/api/dms/pick/data?t={token}")
    record(
        "G7",
        "one-time pick token replay after submit → 401",
        st == 401,
        f"replay /api/dms/pick/data → HTTP {st} (expect 401)",
        ["g5_3_success.png"],
    )

    _, review = C.wait_outbox(
        lambda r: r["kind"] == "push_messages"
        and any(d.startswith("action=confirm_booking") for d in C.flex_buttons(r)),
        since=0,
        timeout=60,
    )
    if not review:
        return record("G5", "booking", False, "no booking_review card after submit")
    save("g5_booking_review_card.json", review)
    nonce = nonce_of(
        [d for d in C.flex_buttons(review) if d.startswith("action=confirm_booking")][0]
    )

    b = C.outbox_len()
    C.post_webhook([C.ev_postback(f"action=confirm_booking&nonce={nonce}")])
    _, rcpt = C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "เปิดใบจองสำเร็จ" in r["text"], since=b, timeout=180
    )
    if not rcpt:
        save("g5_after_confirm_outbox.json", C.read_outbox()[b:])
        return record(
            "G5", "booking", False, "no booking receipt", ["g5_after_confirm_outbox.json"]
        )
    save("g5_booking_receipt.json", rcpt)
    booking_no = ""
    for ln in rcpt["text"].splitlines():
        if "เลขที่ใบจอง" in ln:
            booking_no = ln.split(":", 1)[1].strip()
    found = C.search_booking(booking_no) if booking_no else None
    blogs = push_logs_by_mode("booking")
    save("g5_booking_readback.json", {"booking_no": booking_no, "search_booking_id": found})
    save("g5_push_logs_booking.json", blogs)
    ok = bool(booking_no) and bool(found) and any(x["status"] == "success" for x in blogs)
    record(
        "G5",
        "booking (pick car→color→confirm→BK, real)",
        ok,
        f"booking_no={booking_no} search_hit={found} booking_log={bool(blogs)}",
        [
            "g5_1_car_list.png",
            "g5_2_paints.png",
            "g5_3_success.png",
            "g5_booking_review_card.json",
            "g5_booking_receipt.json",
            "g5_booking_readback.json",
            "g5_push_logs_booking.json",
        ],
    )


def diff_detection():
    """G3: change house_no → diff card must show exactly 1 diff (house_no old→new).
    Under single-cred the update button is (correctly) withheld (has_admin=False);
    under admin creds the update WRITE crashes (phase-1 defect). Either way the
    LINE-driven update is unreachable — reported as blocked."""
    clear_session()
    C.set_ocr(C.id_card_g3())
    b = C.outbox_len()
    C.post_webhook([C.ev_image()])
    C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "เบอร์โทร" in r["text"], since=b, timeout=60
    )
    b2 = C.outbox_len()
    C.post_webhook([C.ev_text(C.PHONE)])
    _, card = C.wait_outbox(
        lambda r: r["kind"] == "push_messages"
        and "พบข้อมูลเดิม" in json.dumps(r, ensure_ascii=False),
        since=b2,
        timeout=120,
    )
    if not card:
        save("g3_after_phone_outbox.json", C.read_outbox()[b2:])
        return record("G3", "diff detection", False, "no diff card", ["g3_after_phone_outbox.json"])
    save("g3_diff_card.json", card)
    body = ((card["messages"][0].get("contents") or {}).get("body") or {}).get("contents") or []
    diff_rows = [x for x in body if x.get("type") == "box" and x.get("layout") == "vertical"]
    btns = C.flex_buttons(card)
    has_update_btn = any(d.startswith("action=update") for d in btns)
    # read the rendered old→new text
    old_new = ""
    if diff_rows:
        texts = [t.get("text", "") for t in diff_rows[0].get("contents", [])]
        old_new = " | ".join(texts)
    ok = len(diff_rows) == 1 and (C.ADDR_G1["house_no"] in old_new) and (C.HOUSE_NO_G3 in old_new)
    record(
        "G3",
        "diff detection (exactly 1 = house_no old→new)",
        ok,
        f"diff_rows={len(diff_rows)} content='{old_new}' update_button_shown={has_update_btn} "
        f"(single-cred withholds it; admin path crashes → LINE update BLOCKED)",
        ["g3_diff_card.json"],
    )


def overwrite_write_contract():
    """Prove the overwrite WRITE contract itself is sound (via user session, the
    same route the LINE update would take minus the broken admin browser).
    Touches only customer 107: house_no → G3 value, birthday must stay put."""
    from services.erp.erp_dms_intake import push_idcard_fields_mrerp_dms

    cfg = dict(C.DMS_CFG)
    cfg.pop("admin_username", None)
    cfg.pop("admin_password", None)
    ep = {"id": "dl5-overwrite", "config": cfg}
    fields = {"people_id": C.PID_GOOD, "name": C.FULL_NAME, "house_no": C.HOUSE_NO_G3}
    r = push_idcard_fields_mrerp_dms(
        ep, fields=fields, mode="overwrite", customer_id="107", addresses=None
    )
    time.sleep(1)
    rb = C.lookup(C.PID_GOOD)
    f = rb.get("fields") or {}
    save(
        "g3b_overwrite_readback.json",
        {"write": {k: r.get(k) for k in ("ok", "success", "customer_id")}, "fields": f},
    )
    ok = (
        r.get("success")
        and f.get("house_no") == C.HOUSE_NO_G3
        and f.get("birthday_be") == C.BIRTHDAY_BE
        and str(f.get("province_id")) == "1"
    )
    record(
        "G3b",
        "overwrite write contract (direct, user session)",
        bool(ok),
        f"write_ok={r.get('success')} house_no={f.get('house_no')} birthday={f.get('birthday_be')} "
        f"province_id={f.get('province_id')}",
        ["g3b_overwrite_readback.json"],
    )


def main():
    # Order matters: booking consumes the picking session before diff_detection
    # clears it; overwrite mutates house_no last so booking sees a stable 107.
    tok = exact_and_pick_setup()
    if tok:
        booking(tok)
    diff_detection()
    overwrite_write_contract()
    save("results_phase2.json", RESULTS)
    print("\n=== PHASE2 SUMMARY ===")
    for r in RESULTS:
        print(f"{r['g']}: {r['status']} — {r['notes']}")


if __name__ == "__main__":
    main()
