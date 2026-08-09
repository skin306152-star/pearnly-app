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
    # 逐问的按钮在 quickReply(不是 Flex footer),flex_buttons 解不到 —— 两处都收。
    vals = list(C.flex_buttons(rec))
    for msg in rec.get("messages") or []:
        for item in ((msg or {}).get("quickReply") or {}).get("items") or []:
            data = ((item or {}).get("action") or {}).get("data")
            if data:
                vals.append(data)
    return vals


def wait_data(prefix: str, since: int, timeout: float = 240) -> tuple[dict | None, str]:
    # 逐问发问两种出口都有:图片/后台路径 push,postback 应答路径 reply。
    _, rec = C.wait_outbox(
        lambda r: r.get("kind") in ("push_messages", "reply_messages")
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
    # 真实旅程 = 先召唤菜单再选 2:单字 1/2 只在 menu 态才是菜单选项,
    # 无会话直接发「2」会被含数字文本当号码路由走。
    base = C.outbox_len()
    C.post_webhook([C.ev_text("เมนู")])
    _, menu = C.wait_outbox(
        lambda r: r.get("kind") == "reply_messages"
        and "จัดทำใบจอง" in json.dumps(r, ensure_ascii=False),
        base,
        20,
    )
    if not menu:
        raise AssertionError("booking menu missing")
    base = C.outbox_len()
    C.post_webhook([C.ev_text("2")])
    _, chose = C.wait_outbox(
        lambda r: "บัตรประชาชน" in json.dumps(r, ensure_ascii=False), base, 20
    )
    if not chose:
        raise AssertionError("mode=booking intake prompt missing")


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


def car_keyword() -> str:
    """车型搜索词从主档缓存现取(测试站车名是 Test/TestModel 一类,写死会搜空)。"""
    with C._conn() as c, c.cursor() as cur:
        cur.execute("SELECT masters->'cars'->0 AS car FROM dms_masters_cache LIMIT 1")
        row = cur.fetchone()
    car = (dict(row) if row else {}).get("car") or []
    name = str(car[2] if len(car) > 2 else "") or str(car[1] if len(car) > 1 else "")
    if not name:
        raise AssertionError("no car master cached; place step should have fetched masters")
    return name[:4]


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
    # 基线一律在动作【前】取:问句可能在 post 返回前就落 outbox,后取基线会把它跳过
    # (首版在 place 步就是这么死锁的:等到了问句→重置基线→再等同一条,永远超时)。
    place = latest_button(base, "qa:place:")
    base = C.outbox_len()
    post(place)
    C.post_webhook([C.ev_text(car_keyword())])
    car_card, _ = wait_data("qa:car:", base, 150)
    if not car_card:
        raise AssertionError("car search result missing")
    car = next(v for v in data_values(car_card) if v.startswith("qa:car:"))
    base = C.outbox_len()
    post(car)
    paint = latest_button(base, "qa:paint:")
    base = C.outbox_len()
    post(paint)
    C.wait_outbox(lambda r: "วันที่คาดว่าจะส่งมอบ" in json.dumps(r, ensure_ascii=False), base, 120)
    base = C.outbox_len()
    post("qa:date", {"date": (date.today() + timedelta(days=30)).isoformat()})
    term = latest_button(base, "qa:term:")
    base = C.outbox_len()
    post(term)
    regis = latest_button(base, "qa:regis:")
    base = C.outbox_len()
    post(regis)
    regis_card, _ = wait_data("qa:regisname:", base, 120)
    base = C.outbox_len()
    post(next(v for v in data_values(regis_card) if v.endswith(":card")))
    pay_card, _ = wait_data("qa:pay:", base, 120)
    base = C.outbox_len()
    post(next(v for v in data_values(pay_card) if v.endswith(":transfer" if not cash else ":cash")))
    C.wait_outbox(lambda r: "จำนวนเงิน" in json.dumps(r, ensure_ascii=False), base, 120)
    base = C.outbox_len()
    C.post_webhook([C.ev_text("2000" if cash else "1500")])
    if not cash:
        C.wait_outbox(lambda r: "บัญชีต้นทาง" in json.dumps(r, ensure_ascii=False), base, 120)
        base = C.outbox_len()
        C.post_webhook([C.ev_text("บัญชีลูกค้า 123-4")])
        C.wait_outbox(lambda r: "บัญชีปลายทาง" in json.dumps(r, ensure_ascii=False), base, 120)
        base = C.outbox_len()
        C.post_webhook([C.ev_text("บัญชีบริษัท 567-8")])
    more = latest_button(base, "qa:more:")
    base = C.outbox_len()
    post("qa:more:done")
    _, preview = C.wait_outbox(
        lambda r: r.get("kind") in ("push_messages", "reply_messages")
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
            and str(fields.get("txtmoneytfmon", "")).replace(",", "") == "1500.00"
            and str(fields.get("txtearnestmoney", "")).replace(",", "") == "1500.00"
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
            lambda r: r.get("kind") in ("push_messages", "reply_messages")
            and "สรุปใบจอง" in json.dumps(r, ensure_ascii=False),
            base - 2,
            30,
        )
        post(next(v for v in data_values(preview) if "action=cancel_booking" in v))
        _, receipt = C.wait_outbox(
            lambda r: r.get("kind") in ("push_text", "reply_text")
            and "ทิ้งรายการแล้ว" in r.get("text", ""),
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
            and str(fields.get("txtmoneycash", "")).replace(",", "") == "2000.00"
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
        need_slip = any(
            "มีช่องทางเงินโอน" in json.dumps(r, ensure_ascii=False) for r in recs[-10:]
        )
        base = C.outbox_len()
        C.post_webhook([C.ev_text("เงินสด")])
        _, still = C.wait_outbox(
            lambda r: "มีช่องทางเงินโอน" in json.dumps(r, ensure_ascii=False), base, 30
        )
        base = C.outbox_len()
        C.post_webhook([C.ev_image()])
        _, preview = C.wait_outbox(
            lambda r: r.get("kind") in ("push_messages", "reply_messages")
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
        post(next(v for v in data_values(place) if v.startswith("qa:place:")))
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
    # DL7_ONLY=qa1,nonce 只重跑指定场景:测试站抖动时避免全量重试狂造垃圾单。
    only = {t for t in os.environ.get("DL7_ONLY", "").split(",") if t}
    result = g_qa1()
    if not only or "cancel" in only:
        g_cancel()
    if not only or "cash" in only:
        g_cash()
    if not only or "slip" in only:
        g_slip_gate()
    if not only or "noise" in only:
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
