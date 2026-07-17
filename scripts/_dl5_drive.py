# -*- coding: utf-8 -*-
"""DL-5 forensic driver · runs G1..G7 against the live app + real DMS test site.

Underscore = not shipped. Assumes scripts/_dl5_app.py is serving on :8300 and
scripts/_dl5_seed.py has been run. Only OCR is injected; every DMS read/write
is real. Writes evidence JSON + screenshots + REPORT.md under _artifacts/dl5/.
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

RESULTS: list[dict] = []


def record(gid, name, ok, notes, evidence=None):
    RESULTS.append(
        {"g": gid, "name": name, "status": "PASS" if ok else "FAIL",
         "notes": notes, "evidence": evidence or []}
    )
    print(f"[{gid}] {'PASS' if ok else 'FAIL'} — {name} :: {notes}")
    return ok


def save(name, obj):
    p = C.art(name)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return name


def http_get(path):
    import urllib.request
    import urllib.error

    try:
        with urllib.request.urlopen(C.BASE + path, timeout=90) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def reset_conversation():
    """Fresh conversation: drop binding + session (push_logs kept, filtered by mode)."""
    from services.line_dms import store

    store.unbind_by_line_user(C.LINE_USER_ID)
    store.clear_session(C.TENANT_ID, C.LINE_USER_ID)


def clear_session():
    from services.line_dms import store

    store.clear_session(C.TENANT_ID, C.LINE_USER_ID)


def nonce_of(data_str):
    return (parse_qs(data_str).get("nonce") or [""])[0]


def push_logs_by_mode(mode):
    rows = []
    for r in C.db_push_logs():
        rb = r.get("request_body") or {}
        if isinstance(rb, str):
            try:
                rb = json.loads(rb)
            except Exception:
                rb = {}
        if rb.get("mode") == mode:
            rows.append({**r, "request_body": rb, "created_at": str(r.get("created_at"))})
    return rows


# ───────────────────────── G1 ─────────────────────────
def g1():
    from services.line_dms import store

    reset_conversation()
    pre = C.lookup(C.PID_GOOD)
    save("g1_precheck_lookup.json", pre)
    if pre.get("found"):
        record("G1", "new customer full chain", False,
               f"customer {C.PID_GOOD} already exists in DMS before run — cannot prove create",
               ["g1_precheck_lookup.json"])
        return None

    base = C.outbox_len()
    code = store.generate_bind_code(C.TENANT_ID, C.USER_ID)["code"]
    st, _ = C.post_webhook([C.ev_text(code)])
    i, rec = C.wait_outbox(lambda r: r["kind"] == "reply_text" and "เชื่อมต่อสำเร็จ" in r["text"],
                           since=base, timeout=15)
    if not rec:
        return record("G1", "bind", False, f"no BIND_OK reply (webhook {st})") or None

    # image → ask phone
    C.set_ocr(C.id_card_g1())
    b2 = C.outbox_len()
    C.post_webhook([C.ev_image()])
    i, rec = C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "เบอร์โทร" in r["text"], since=b2, timeout=60)
    if not rec:
        return record("G1", "ocr→ask-phone", False, "no ASK_PHONE push") or None

    # phone → dedup → new_customer_card (scenario none)
    b3 = C.outbox_len()
    C.post_webhook([C.ev_text(C.PHONE)])
    i, card = C.wait_outbox(
        lambda r: r["kind"] == "push_messages"
        and any(d.startswith("action=create_new") for d in C.flex_buttons(r)),
        since=b3, timeout=120)
    if not card:
        # maybe TXT_SAME (already exists) or similar — capture what came
        save("g1_after_phone_outbox.json", C.read_outbox()[b3:])
        return record("G1", "dedup→new-card", False,
                      "no new_customer_card (see g1_after_phone_outbox.json)",
                      ["g1_after_phone_outbox.json"]) or None
    save("g1_new_customer_card.json", card)
    nonce = nonce_of([d for d in C.flex_buttons(card) if d.startswith("action=create_new")][0])

    # postback create
    b4 = C.outbox_len()
    C.post_webhook([C.ev_postback(f"action=create_new&nonce={nonce}")])
    i, rcpt = C.wait_outbox(lambda r: r["kind"] == "push_text" and "บันทึกสำเร็จ" in r["text"],
                            since=b4, timeout=120)
    if not rcpt:
        save("g1_after_confirm_outbox.json", C.read_outbox()[b4:])
        return record("G1", "confirm→receipt", False,
                      "no create receipt", ["g1_after_confirm_outbox.json"]) or None
    save("g1_receipt.json", rcpt)

    # readback
    rb = None
    for _ in range(20):
        rb = C.lookup(C.PID_GOOD)
        if rb.get("found"):
            break
        time.sleep(2)
    save("g1_readback_lookup.json", rb)
    f = rb.get("fields") or {}
    checks = {
        "found": rb.get("found") is True,
        "name": f.get("name") == C.FULL_NAME,
        "phone": f.get("phone") == C.PHONE,
        "birthday_be": f.get("birthday_be") == C.BIRTHDAY_BE,
        "house_no": f.get("house_no") == C.ADDR_G1["house_no"],
        "province_id": str(f.get("province_id")) == "1",
        "district_id": str(f.get("district_id")) == "18",
        "subdistrict_id": str(f.get("subdistrict_id")) == "72",
        "moo": f.get("moo") == C.ADDR_G1["moo"],
    }
    logs = push_logs_by_mode("create")
    checks["push_log_create_success"] = any(x["status"] == "success" for x in logs)
    save("g1_push_logs_create.json", logs)
    cid = rb.get("customer_id")
    ok = all(checks.values())
    record("G1", "new customer full chain", ok,
           f"customer_id={cid} checks={checks}",
           ["g1_new_customer_card.json", "g1_receipt.json", "g1_readback_lookup.json",
            "g1_push_logs_create.json"])
    return {"customer_id": cid, "readback": f}


# ───────────────────────── G2 ─────────────────────────
def g2(g1_fields):
    clear_session()
    C.set_ocr(C.id_card_g1())
    creates_before = len(push_logs_by_mode("create"))
    over_before = len(push_logs_by_mode("overwrite"))

    b = C.outbox_len()
    C.post_webhook([C.ev_image()])
    C.wait_outbox(lambda r: r["kind"] == "push_text" and "เบอร์โทร" in r["text"], since=b, timeout=60)
    b2 = C.outbox_len()
    C.post_webhook([C.ev_text(C.PHONE)])
    i, same = C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "ข้อมูลตรงกัน" in r["text"], since=b2, timeout=120)
    save("g2_after_phone_outbox.json", C.read_outbox()[b2:])

    rb = C.lookup(C.PID_GOOD)
    f = rb.get("fields") or {}
    unchanged = all(f.get(k) == (g1_fields or {}).get(k)
                    for k in ("name", "phone", "birthday_be", "house_no",
                              "province_id", "district_id", "subdistrict_id"))
    no_write = (len(push_logs_by_mode("create")) == creates_before
                and len(push_logs_by_mode("overwrite")) == over_before)
    ok = bool(same) and unchanged and no_write
    record("G2", "idempotent re-run (data matches)", ok,
           f"TXT_SAME={bool(same)} unchanged={unchanged} no_write={no_write}",
           ["g2_after_phone_outbox.json"])


# ───────────────────────── G3 ─────────────────────────
def g3():
    clear_session()
    C.set_ocr(C.id_card_g3())
    over_before = len(push_logs_by_mode("overwrite"))

    b = C.outbox_len()
    C.post_webhook([C.ev_image()])
    C.wait_outbox(lambda r: r["kind"] == "push_text" and "เบอร์โทร" in r["text"], since=b, timeout=60)
    b2 = C.outbox_len()
    C.post_webhook([C.ev_text(C.PHONE)])
    i, card = C.wait_outbox(
        lambda r: r["kind"] == "push_messages"
        and any(d.startswith("action=update") for d in C.flex_buttons(r)),
        since=b2, timeout=120)
    if not card:
        save("g3_after_phone_outbox.json", C.read_outbox()[b2:])
        return record("G3", "diff update", False, "no diff card with update button",
                      ["g3_after_phone_outbox.json"])
    save("g3_diff_card.json", card)
    # count diff rows rendered in the card body (label + old→new pairs)
    body = ((card["messages"][0].get("contents") or {}).get("body") or {}).get("contents") or []
    diff_rows = [x for x in body if x.get("type") == "box" and x.get("layout") == "vertical"]
    nonce = nonce_of([d for d in C.flex_buttons(card) if d.startswith("action=update")][0])

    b3 = C.outbox_len()
    C.post_webhook([C.ev_postback(f"action=update&nonce={nonce}")])
    i, rcpt = C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "อัปเดตข้อมูลลูกค้า" in r["text"],
        since=b3, timeout=120)
    save("g3_receipt.json", rcpt or {})

    rb = None
    for _ in range(20):
        rb = C.lookup(C.PID_GOOD)
        f = rb.get("fields") or {}
        if f.get("house_no") == C.HOUSE_NO_G3:
            break
        time.sleep(2)
    save("g3_readback_lookup.json", rb)
    f = rb.get("fields") or {}
    over_logs = push_logs_by_mode("overwrite")
    latest = over_logs[-1] if over_logs else {}
    fd = (latest.get("request_body") or {}).get("field_diffs") or []
    save("g3_push_logs_overwrite.json", over_logs)
    checks = {
        "diff_rows_eq_1": len(diff_rows) == 1,
        "receipt_overwrite": bool(rcpt),
        "house_no_new": f.get("house_no") == C.HOUSE_NO_G3,
        "birthday_unchanged": f.get("birthday_be") == C.BIRTHDAY_BE,
        "province_unchanged": str(f.get("province_id")) == "1",
        "push_log_overwrite_added": len(over_logs) == over_before + 1,
        "field_diffs_eq_1": len(fd) == 1,
        "field_diff_is_house_no": bool(fd) and fd[0].get("field") == "house_no",
    }
    record("G3", "diff update (house_no)", all(checks.values()),
           f"field_diffs={fd} checks={checks}",
           ["g3_diff_card.json", "g3_receipt.json", "g3_readback_lookup.json",
            "g3_push_logs_overwrite.json"])


# ───────────────────────── G4 ─────────────────────────
def g4():
    clear_session()
    C.set_ocr(C.id_card_g4())
    logs_before = len(C.db_push_logs())
    b = C.outbox_len()
    C.post_webhook([C.ev_image()])
    i, blur = C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "อ่านบัตรไม่ชัด" in r["text"], since=b, timeout=60)
    after = C.read_outbox()[b:]
    save("g4_outbox.json", after)
    no_card = not any(r["kind"] == "push_messages" for r in after)
    no_write = len(C.db_push_logs()) == logs_before
    ok = bool(blur) and no_card and no_write
    record("G4", "checksum reject (bad last digit)", ok,
           f"blurry_push={bool(blur)} no_confirm_card={no_card} no_push_log={no_write}",
           ["g4_outbox.json"])


# ───────────────────────── G5 + G7 ─────────────────────────
def g5():
    # Re-establish a clean picking session via an exact (no-diff) match on the
    # current customer state (house_no was changed to G3 value), which fires
    # offer_pick without any write.
    clear_session()
    C.set_ocr(C.id_card_g3())
    b = C.outbox_len()
    C.post_webhook([C.ev_image()])
    C.wait_outbox(lambda r: r["kind"] == "push_text" and "เบอร์โทร" in r["text"], since=b, timeout=60)
    b2 = C.outbox_len()
    C.post_webhook([C.ev_text(C.PHONE)])
    i, pick = C.wait_outbox(
        lambda r: r["kind"] == "push_messages"
        and any(d.startswith("URI::") and "dms-pick" in d for d in C.flex_buttons(r)),
        since=b2, timeout=120)
    if not pick:
        save("g5_setup_outbox.json", C.read_outbox()[b2:])
        return record("G5", "booking", False, "no pick button after exact match",
                      ["g5_setup_outbox.json"])
    save("g5_pick_button.json", pick)
    uri = [d[5:] for d in C.flex_buttons(pick) if d.startswith("URI::")][0]
    token = (parse_qs(urlparse(uri).query).get("t") or [""])[0]

    # rewrite pick URL to the local app
    local_url = f"{C.BASE}/dms-pick?t={token}"
    bk, g7_status = _drive_pick_and_confirm(local_url, token)
    return bk


def _drive_pick_and_confirm(local_url, token):
    from playwright.sync_api import sync_playwright

    booking_no = None
    g7_status = None
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
        # advisor + date come pre-filled from defaults; submit
        pg.wait_for_function("!document.getElementById('pk-submit').disabled", timeout=15000)
        pg.click("#pk-submit")
        pg.wait_for_selector(".state.ok", timeout=120000)
        pg.screenshot(path=str(C.art("g5_3_success.png")))
        br.close()

    # G7: replay the (now-rotated) token — must be 401
    st, _ = http_get(f"/api/dms/pick/data?t={token}")
    record("G7", "one-time token replay after submit", st == 401,
           f"replay /api/dms/pick/data → HTTP {st} (expect 401)", ["g5_3_success.png"])

    # booking_review card → confirm
    i, review = C.wait_outbox(
        lambda r: r["kind"] == "push_messages"
        and any(d.startswith("action=confirm_booking") for d in C.flex_buttons(r)),
        since=0, timeout=60)
    if not review:
        record("G5", "booking", False, "no booking_review card after submit")
        return None
    save("g5_booking_review_card.json", review)
    nonce = nonce_of([d for d in C.flex_buttons(review) if d.startswith("action=confirm_booking")][0])

    b = C.outbox_len()
    C.post_webhook([C.ev_postback(f"action=confirm_booking&nonce={nonce}")])
    i, rcpt = C.wait_outbox(
        lambda r: r["kind"] == "push_text" and "เปิดใบจองสำเร็จ" in r["text"], since=b, timeout=180)
    if not rcpt:
        save("g5_after_confirm_outbox.json", C.read_outbox()[b:])
        record("G5", "booking", False, "no booking receipt", ["g5_after_confirm_outbox.json"])
        return None
    save("g5_booking_receipt.json", rcpt)
    # BK number is the 2nd line "เลขที่ใบจอง: BK..."
    booking_no = ""
    for ln in rcpt["text"].splitlines():
        if "เลขที่ใบจอง" in ln:
            booking_no = ln.split(":", 1)[1].strip()
    found = C.search_booking(booking_no) if booking_no else None
    save("g5_booking_readback.json", {"booking_no": booking_no, "search_booking_id": found})
    blogs = push_logs_by_mode("booking")
    save("g5_push_logs_booking.json", blogs)
    ok = bool(booking_no) and bool(found) and any(x["status"] == "success" for x in blogs)
    record("G5", "booking (pick car→color→confirm→BK)", ok,
           f"booking_no={booking_no} search_hit={found} booking_log={bool(blogs)}",
           ["g5_1_car_list.png", "g5_2_paints.png", "g5_3_success.png",
            "g5_booking_review_card.json", "g5_booking_receipt.json",
            "g5_booking_readback.json", "g5_push_logs_booking.json"])
    return booking_no


# ───────────────────────── G6 ─────────────────────────
def g6():
    body_events = [C.ev_text("hello")]
    import json as _j
    import hmac
    import hashlib
    import base64

    body = _j.dumps({"destination": "dl5", "events": body_events}).encode("utf-8")
    wrong = base64.b64encode(hmac.new(b"acc-secret", body, hashlib.sha256).digest()).decode()
    st, resp = C.post_webhook(body_events, signature=wrong)
    save("g6_wrong_secret_response.json", {"status": st, "body": resp})
    record("G6", "channel isolation (old-OA secret rejected)", st == 400,
           f"foreign-secret webhook → HTTP {st} (expect 400)", ["g6_wrong_secret_response.json"])


def write_report(regression_line):
    lines = ["# DL-5 · DMS LINE car-sales end-to-end forensic report", ""]
    lines.append(f"- Run: {time.strftime('%Y-%m-%d %H:%M:%S %z')}")
    lines.append("- OCR: **injected** (recognize_id_card patched; real mod-11 checksum kept).")
    lines.append("- Every DMS read/write: **real** against https://www.mrerp4sme.com/dms .")
    lines.append(f"- Fixtures: people_id(good)={C.PID_GOOD} people_id(bad)={C.PID_BAD}")
    lines.append("")
    lines.append("| G | Assertion | Status | Key evidence |")
    lines.append("|---|-----------|--------|--------------|")
    for r in RESULTS:
        ev = ", ".join(r["evidence"]) if r["evidence"] else "—"
        lines.append(f"| {r['g']} | {r['name']} | **{r['status']}** | {r['notes']} · {ev} |")
    lines.append("")
    lines.append("## Regression")
    lines.append("```")
    lines.append(regression_line)
    lines.append("```")
    C.art("REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    save("results.json", RESULTS)


def main():
    g1res = g1()
    g1_fields = (g1res or {}).get("readback") if g1res else None
    if g1res:
        g2(g1_fields)
        g3()
    g4()
    g6()
    if g1res:
        g5()
    write_report("(filled in by caller)")
    print("\n=== SUMMARY ===")
    for r in RESULTS:
        print(f"{r['g']}: {r['status']} — {r['notes']}")


if __name__ == "__main__":
    main()
