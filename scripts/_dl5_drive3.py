# -*- coding: utf-8 -*-
"""DL-5 batch 3: LINE chat booking QA against the DMS test site.

The app is expected to be running from ``scripts/_dl5_app.py``.  OCR remains
the only injected input; booking writes, attachment uploads, readbacks, and
the final screenshots use the real DMS test account.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "DATABASE_URL", "postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly?sslmode=disable"
)
os.environ["PGSSLMODE"] = "disable"
os.environ["LINE_DMS_CHANNEL_SECRET"] = "e2e-test-secret"
os.environ.setdefault("JWT_SECRET", "dl5-e2e-jwt-secret-please-32chars-long")

from scripts import _dl5_common as C  # noqa: E402
from scripts._dl5_drive import reset_conversation  # noqa: E402

ART = ROOT / "tests" / "e2e" / "_artifacts" / "dl7"
RESULTS: list[dict] = []
BOOKINGS: list[str] = []
LAST_CONFIRM = ""


def save(name: str, value) -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def record(g: str, name: str, ok: bool, notes: str, evidence: list[str] | None = None) -> None:
    row = {
        "g": g,
        "name": name,
        "status": "PASS" if ok else "FAIL",
        "notes": notes,
        "evidence": evidence or [],
    }
    RESULTS.append(row)
    print(f"[{g}] {row['status']} — {name} :: {notes}")


def records_since(index: int) -> list[dict]:
    return C.read_outbox()[index:]


def text_in(recs: list[dict], needle: str) -> bool:
    return any(needle in str(r.get("text", "")) for r in recs)


def data_values(rec: dict) -> list[str]:
    return C.flex_buttons(rec)


def wait_data(prefix: str, since: int, timeout: float = 120) -> tuple[dict | None, str]:
    _, rec = C.wait_outbox(
        lambda r: r.get("kind") == "push_messages"
        and any(v.startswith(prefix) for v in data_values(r)),
        since=since,
        timeout=timeout,
    )
    if not rec:
        return None, ""
    return rec, next(v for v in data_values(rec) if v.startswith(prefix))


def post(data: str, params: dict | None = None) -> None:
    event = C.ev_postback(data)
    if params:
        event["postback"]["params"] = params
    C.post_webhook([event])


def bind_booking_menu() -> None:
    from services.line_dms import store

    reset_conversation()
    code = store.generate_bind_code(C.TENANT_ID, C.USER_ID)["code"]
    base = C.outbox_len()
    C.post_webhook([C.ev_text(code)])
    _, bound = C.wait_outbox(
        lambda r: r.get("kind") == "reply_text" and "เชื่อมต่อสำเร็จ" in r.get("text", ""), base, 20
    )
    if not bound:
        raise AssertionError("binding receipt missing")
    base = C.outbox_len()
    C.post_webhook([C.ev_text("2")])
    _, menu = C.wait_outbox(
        lambda r: r.get("kind") == "reply_messages"
        and "จัดทำใบจอง" in json.dumps(r, ensure_ascii=False),
        base,
        20,
    )
    if not menu:
        raise AssertionError("booking menu missing")


def prepare_customer() -> str:
    bind_booking_menu()
    C.set_ocr(C.id_card_g1())
    base = C.outbox_len()
    C.post_webhook([C.ev_image()])
    if not C.wait_outbox(
        lambda r: r.get("kind") == "push_text" and "เบอร์โทร" in r.get("text", ""), base, 90
    )[1]:
        raise AssertionError("phone question missing")
    base = C.outbox_len()
    C.post_webhook([C.ev_text(C.PHONE)])
    card, data = wait_data("action=", base, 150)
    if not card:
        raise AssertionError("customer review card missing")
    save("qa1-customer-review.json", card)
    keep = next((v for v in data_values(card) if v.startswith("action=keep")), "")
    if not keep:
        raise AssertionError("ACT_KEEP missing for existing customer")
    base = C.outbox_len()
    post(keep)
    _, prompt = C.wait_outbox(
        lambda r: r.get("kind") in ("push_text", "push_messages")
        and "สลิป" in json.dumps(r, ensure_ascii=False),
        base,
        120,
    )
    if not prompt:
        raise AssertionError("booking QA slip prompt missing")
    sess = C.db_session() or {}
    return str(((sess.get("payload") or {}).get("qa") or {}).get("customer", {}).get("id") or "")


def latest_button(since: int, prefix: str) -> str:
    rec, data = wait_data(prefix, since)
    if not rec:
        raise AssertionError(f"button {prefix} missing")
    return data


def qa_common(*, cash: bool = False, slip: bool = True) -> tuple[str, str, dict]:
    customer_id = prepare_customer()
    if cash:
        base = C.outbox_len()
        C.post_webhook([C.ev_text("เงินสด")])
    elif slip:
        base = C.outbox_len()
        C.post_webhook([C.ev_image()])
    else:
        base = C.outbox_len()
        C.post_webhook([C.ev_text("เงินสด")])
    if not C.wait_outbox(
        lambda r: r.get("kind") in ("push_messages", "reply_messages")
        and "สถานที่รับจอง" in json.dumps(r, ensure_ascii=False),
        base,
        120,
    )[1]:
        raise AssertionError("place question missing")

    base = C.outbox_len()
    place = latest_button(base, "qa:place:")
    post(place)
    base = C.outbox_len()
    C.post_webhook([C.ev_text("dmax")])
    car_card, _ = wait_data("qa:car:", base, 150)
    if not car_card:
        raise AssertionError("car search result missing")
    base = C.outbox_len()
    car = next(v for v in data_values(car_card) if v.startswith("qa:car:"))
    post(car)
    base = C.outbox_len()
    paint = latest_button(base, "qa:paint:")
    post(paint)
    base = C.outbox_len()
    C.wait_outbox(lambda r: "วันที่คาดว่าจะส่งมอบ" in json.dumps(r, ensure_ascii=False), base, 120)
    post("qa:date", {"date": (date.today() + timedelta(days=30)).isoformat()})
    base = C.outbox_len()
    term = latest_button(base, "qa:term:")
    post(term)
    base = C.outbox_len()
    regis = latest_button(base, "qa:regis:")
    post(regis)
    base = C.outbox_len()
    regis_card, _ = wait_data("qa:regisname:", base, 120)
    post(next(v for v in data_values(regis_card) if v.endswith(":card")))
    base = C.outbox_len()
    pay_card, _ = wait_data("qa:pay:", base, 120)
    post(next(v for v in data_values(pay_card) if v.endswith(":transfer" if not cash else ":cash")))
    base = C.outbox_len()
    C.post_webhook([C.ev_text("2000" if cash else "1500")])
    if cash:
        base = C.outbox_len()
    else:
        C.wait_outbox(lambda r: "บัญชีต้นทาง" in json.dumps(r, ensure_ascii=False), base, 120)
        C.post_webhook([C.ev_text("บัญชีลูกค้า 123-4")])
        base = C.outbox_len()
        C.wait_outbox(lambda r: "บัญชีปลายทาง" in json.dumps(r, ensure_ascii=False), base, 120)
        C.post_webhook([C.ev_text("บัญชีบริษัท 567-8")])
    base = C.outbox_len()
    more = latest_button(base, "qa:more:")
    post("qa:more:done")
    _, preview = C.wait_outbox(
        lambda r: r.get("kind") == "push_messages"
        and "สรุปใบจอง" in json.dumps(r, ensure_ascii=False),
        base,
        120,
    )
    if not preview:
        raise AssertionError("preview missing")
    save("qa-preview-cash.json" if cash else "qa-preview-transfer.json", preview)
    return customer_id, more, preview


def g_qa1() -> tuple[str, str, dict] | None:
    global LAST_CONFIRM
    try:
        cid, _, preview = qa_common()
        body = json.dumps(preview, ensure_ascii=False)
        labels = all(
            x in body for x in ("สรุปใบจอง", "ยอดเงินจองรวม", "สำเนาบัตรประชาชน", "ใบโอนเงินจอง")
        )
        confirm = next(v for v in data_values(preview) if "action=confirm_booking" in v)
        LAST_CONFIRM = confirm
        nonce = (parse_qs(confirm).get("nonce") or [""])[0]
        base = C.outbox_len()
        post(confirm)
        _, receipt = C.wait_outbox(
            lambda r: r.get("kind") == "push_text" and "เลขที่ใบจอง" in r.get("text", ""), base, 180
        )
        if not receipt:
            raise AssertionError("booking receipt missing")
        booking_no = next(
            (
                line.split(":", 1)[1].strip()
                for line in receipt["text"].splitlines()
                if "เลขที่ใบจอง" in line
            ),
            "",
        )
        found = C.search_booking(booking_no)
        readback = read_booking(found)
        save("qa1-receipt.json", receipt)
        save("qa1-dms-readback.json", readback)
        fields = readback.get("fields", {})
        names = {v for k, v in fields.items() if k.startswith("fulcurrname")}
        ok = (
            labels
            and nonce
            and booking_no
            and found
            and fields.get("txtmoneytfmon") == "1500.00"
            and fields.get("txtearnestmoney") == "1500.00"
            and fields.get("txtaccountnumtffrom") == "บัญชีลูกค้า 123-4"
            and fields.get("txtaccountnumtfmon") == "บัญชีบริษัท 567-8"
            and "สำเนาบัตรประชาชน" in names
            and "ใบโอนเงินจอง" in names
        )
        if booking_no:
            BOOKINGS.append(booking_no)
        record(
            "G-QA1",
            "transfer full chain",
            bool(ok),
            f"booking={booking_no} search_id={found} preview_labels={labels} nonce={bool(nonce)} attachments={sorted(names)} payment_fields={fields.get('txtmoneytfmon')}/{fields.get('txtearnestmoney')}",
            ["qa1-receipt.json", "qa1-dms-readback.json"],
        )
        return booking_no, str(found), readback
    except Exception as exc:
        record("G-QA1", "transfer full chain", False, f"blocked: {type(exc).__name__}: {exc}")
        return None


def read_booking(booking_id: str | None) -> dict:
    if not booking_id:
        return {}

    def op(cl, _adapter):
        html = cl._post_text("drfcbc/form.php", {"status": "e", "id": str(booking_id)})
        return {"id": booking_id, "fields": cl._parse_form_defaults(html)}

    return C.dms_op(op)


def g_cancel() -> None:
    try:
        before = len(C.db_push_logs())
        qa_common()
        base = C.outbox_len()
        _, preview = C.wait_outbox(
            lambda r: r.get("kind") == "push_messages"
            and "สรุปใบจอง" in json.dumps(r, ensure_ascii=False),
            base - 2,
            30,
        )
        post(next(v for v in data_values(preview) if "action=cancel_booking" in v))
        _, receipt = C.wait_outbox(
            lambda r: r.get("kind") == "push_text" and "ทิ้งรายการแล้ว" in r.get("text", ""),
            base,
            60,
        )
        ok = bool(receipt) and len(C.db_push_logs()) == before
        record(
            "G-QA2",
            "discard preview without DMS write",
            ok,
            f"receipt={bool(receipt)} logs_before={before} logs_after={len(C.db_push_logs())}",
        )
    except Exception as exc:
        record(
            "G-QA2",
            "discard preview without DMS write",
            False,
            f"blocked: {type(exc).__name__}: {exc}",
        )


def g_cash() -> None:
    try:
        cid, _, preview = qa_common(cash=True)
        confirm = next(v for v in data_values(preview) if "action=confirm_booking" in v)
        base = C.outbox_len()
        post(confirm)
        _, receipt = C.wait_outbox(
            lambda r: r.get("kind") == "push_text" and "เลขที่ใบจอง" in r.get("text", ""), base, 180
        )
        no = (
            next(
                (
                    x.split(":", 1)[1].strip()
                    for x in receipt["text"].splitlines()
                    if "เลขที่ใบจอง" in x
                ),
                "",
            )
            if receipt
            else ""
        )
        rb = read_booking(C.search_booking(no))
        fields = rb.get("fields", {})
        names = {v for k, v in fields.items() if k.startswith("fulcurrname")}
        ok = (
            bool(receipt)
            and fields.get("txtmoneycash") == "2000.00"
            and "ใบโอนเงินจอง" not in names
        )
        if no:
            BOOKINGS.append(no)
        save("qa3-dms-readback.json", rb)
        record(
            "G-QA3",
            "cash path",
            ok,
            f"booking={no} txtmoneycash={fields.get('txtmoneycash')} attachments={sorted(names)}",
            ["qa3-dms-readback.json"],
        )
    except Exception as exc:
        record("G-QA3", "cash path", False, f"blocked: {type(exc).__name__}: {exc}")


def g_slip_gate() -> None:
    try:
        qa_common(cash=False, slip=False)
        record(
            "G-QA4",
            "transfer requires slip",
            False,
            "scenario unexpectedly reached preview before gate",
        )
    except AssertionError:
        recs = C.read_outbox()
        need_slip = text_in(recs[-8:], "มีช่องทางเงินโอน กรุณาส่งสลิป")
        base = C.outbox_len()
        C.post_webhook([C.ev_text("เงินสด")])
        _, still = C.wait_outbox(
            lambda r: r.get("kind") == "push_text" and "มีช่องทางเงินโอน" in r.get("text", ""),
            base,
            30,
        )
        base = C.outbox_len()
        C.post_webhook([C.ev_image()])
        _, preview = C.wait_outbox(
            lambda r: r.get("kind") == "push_messages"
            and "สรุปใบจอง" in json.dumps(r, ensure_ascii=False),
            base,
            120,
        )
        record(
            "G-QA4",
            "transfer requires slip",
            need_slip and bool(still) and bool(preview),
            f"need_slip={need_slip} cash_rejected={bool(still)} preview_after_image={bool(preview)}",
        )
    except Exception as exc:
        record("G-QA4", "transfer requires slip", False, f"blocked: {type(exc).__name__}: {exc}")


def g_noise_image() -> None:
    try:
        cid = prepare_customer()
        base = C.outbox_len()
        C.post_webhook([C.ev_text("เงินสด")])
        _, place = C.wait_outbox(
            lambda r: "สถานที่รับจอง" in json.dumps(r, ensure_ascii=False), base, 90
        )
        if not place:
            raise AssertionError("place question missing")
        base = C.outbox_len()
        post(latest_button(base, "qa:place:"))
        base = C.outbox_len()
        C.post_webhook([C.ev_image()])
        _, msg = C.wait_outbox(
            lambda r: r.get("kind") == "push_text" and "ไม่ต้องการรูปภาพ" in r.get("text", ""),
            base,
            60,
        )
        injected = [r for r in records_since(base) if r.get("kind") == "ocr_injected"]
        ok = (
            bool(msg)
            and not injected
            and ((C.db_session() or {}).get("payload") or {}).get("qa", {}).get("step")
            == "car_search"
        )
        record(
            "G-QA5",
            "mid-flow image is rejected without OCR",
            ok,
            f"customer={cid} reply={bool(msg)} ocr_delta={len(injected)}",
        )
    except Exception as exc:
        record(
            "G-QA5",
            "mid-flow image is rejected without OCR",
            False,
            f"blocked: {type(exc).__name__}: {exc}",
        )


def g_nonce(result: tuple[str, str, dict] | None) -> None:
    if not result:
        record("G-QA6", "nonce replay", False, "G-QA1 did not produce a booking")
        return
    if not LAST_CONFIRM:
        record("G-QA6", "nonce replay", False, "confirmation card not retained")
        return
    confirm = LAST_CONFIRM
    try:
        before = len(C.search_booking(result[0]) or "")
        base = C.outbox_len()
        post(confirm)
        _, expired = C.wait_outbox(
            lambda r: r.get("kind") == "reply_text" and "หมดอายุ" in r.get("text", ""), base, 60
        )
        after = len(C.search_booking(result[0]) or "")
        record(
            "G-QA6",
            "nonce replay",
            bool(expired) and before == after,
            f"expired={bool(expired)} booking_lookup_stable={before == after}",
        )
    except Exception as exc:
        record("G-QA6", "nonce replay", False, f"blocked: {type(exc).__name__}: {exc}")


def screenshots(booking_id: str | None) -> None:
    if not booking_id:
        return
    from playwright.sync_api import sync_playwright

    url = os.environ.get("DMS_LOGIN_URL") or C.DMS_CFG["system_url"]
    user = os.environ.get("DMS_USERNAME") or C.DMS_CFG["username"]
    password = os.environ.get("DMS_PASSWORD") or C.DMS_CFG["password"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="th-TH")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.locator(
            'input[name="txtusers"], input[name="username"], input[type="text"]'
        ).first.fill(user)
        page.locator(
            'input[name="txtpasswords"], input[name="password"], input[type="password"]'
        ).first.fill(password)
        page.locator("#btnlogin, input[name='btnlogin'], button").first.click()
        page.wait_for_timeout(4000)
        base = url.rsplit("/", 1)[0] + "/"
        page.goto(
            f"{base}drfcbc/form.php?status=e&id={booking_id}",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.screenshot(path=str(ART / "dms-booking-attachments.png"), full_page=True)
        page.screenshot(path=str(ART / "dms-booking-payment.png"), full_page=True)
        browser.close()


def report() -> None:
    lines = [
        "# DL-7 DMS LINE chat QA E2E",
        "",
        *[f"- **{r['g']}** {r['status']}: {r['name']} — {r['notes']}" for r in RESULTS],
        "",
        "## Booking numbers",
        *[f"- `{x}`" for x in BOOKINGS],
        "",
        "## Evidence",
        *[f"- `{p.name}`" for p in sorted(ART.iterdir()) if p.name != "REPORT.md"],
    ]
    (ART / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    save("outbox.json", C.read_outbox())
    result = g_qa1()
    g_cancel()
    g_cash()
    g_slip_gate()
    g_noise_image()
    g_nonce(result)
    try:
        screenshots(result[1] if result else None)
    except Exception as exc:
        record("DMS", "evidence screenshots", False, f"blocked: {type(exc).__name__}: {exc}")
    save("results.json", RESULTS)
    save("dms-booking-numbers.json", BOOKINGS)
    report()
    return 0 if all(r["status"] == "PASS" for r in RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
