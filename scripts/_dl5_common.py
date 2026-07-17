# -*- coding: utf-8 -*-
"""DL-5 forensic harness · shared config + helpers (underscore = not shipped).

Drives the DMS LINE car-sales chain end to end against the real DMS test site
(https://www.mrerp4sme.com/dms). Only OCR is injected; every DMS write is real.
Secrets live in env/local DB only — never printed here beyond what the operator
already supplied on the command line.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

# ── fixed identifiers (deterministic across reruns) ─────────────────────────
DB_URL = os.environ.get(
    "DL5_DATABASE_URL",
    "postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly?sslmode=disable",
)
os.environ.setdefault("PGSSLMODE", "disable")
TENANT_ID = "d5000000-0000-4000-8000-000000000001"
USER_ID = "d5000000-0000-4000-8000-000000000002"
LINE_USER_ID = "Udl5e2e000000000000000000000001"
ENDPOINT_NAME = "DL5 DMS test site"

SECRET = "e2e-test-secret"  # self-sign / self-verify (env LINE_DMS_CHANNEL_SECRET)
PORT = 8300
BASE = f"http://127.0.0.1:{PORT}"

# DMS test-site credentials (dmstest is also the admin on the test tenant).
DMS_CFG = {
    "username": "dmstest",
    "password": "dmstest",
    "admin_username": "dmstest",
    "admin_password": "dmstest",
    "system_url": "https://www.mrerp4sme.com/dms/index.php",
    "id_card_auto_push": True,
}

# ── people ids ──────────────────────────────────────────────────────────────
PID_GOOD = "1101700998118"  # valid mod-11 checksum, absent from DMS at seed time
PID_BAD = "1101700998119"  # last digit flipped → checksum fails (G4)

NAME_FIRST = "ดีแอลห้า"
NAME_LAST = "ทดสอบพเนิร์ลลี่"
FULL_NAME = f"{NAME_FIRST} {NAME_LAST}"
BIRTHDAY_BE = "15/05/2530"
PHONE = "0811111111"

# Address whose province/district/subdistrict names resolve on the DMS test
# site to province_id=1 / district_id=18 / subdistrict_id=72 / zipcode_id=197.
ADDR_G1 = {
    "house_no": "199/8",
    "moo": "5",
    "soi": "ทดสอบดีแอล",
    "road": "เจริญนคร",
    "province": "กรุงเทพมหานคร",
    "district": "คลองสาน",
    "subdistrict": "คลองต้นไทร",
    "zipcode": "10600",
}
HOUSE_NO_G3 = "271/35"  # G3 changes only house_no


def _id_card(people_id: str, address: dict) -> dict:
    """Shape an OCR id-card dict as extract_thai_id_card would return it."""
    return {
        "prefix_name": "นาย",
        "first_name": NAME_FIRST,
        "last_name": NAME_LAST,
        "people_id": people_id,
        "birthday_be": BIRTHDAY_BE,
        "issue_date_be": "01/01/2560",
        "expiry_date_be": "01/01/2570",
        "address": dict(address),
    }


def id_card_g1() -> dict:
    return _id_card(PID_GOOD, ADDR_G1)


def id_card_g3() -> dict:
    a = dict(ADDR_G1)
    a["house_no"] = HOUSE_NO_G3
    return _id_card(PID_GOOD, a)


def id_card_g4() -> dict:
    return _id_card(PID_BAD, ADDR_G1)


# ── artifact paths ──────────────────────────────────────────────────────────
ART_DIR = Path(__file__).resolve().parents[1] / "tests" / "e2e" / "_artifacts" / "dl5"
OUTBOX = ART_DIR / "outbox.jsonl"
OCR_INJECT = ART_DIR / "ocr_inject.json"


def art(name: str) -> Path:
    return ART_DIR / name


# ── LINE signing / webhook post ─────────────────────────────────────────────
def sign(body: bytes) -> str:
    mac = hmac.new(SECRET.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


def post_webhook(events: list, *, signature: str | None = None, secret: str | None = None):
    import urllib.request
    import urllib.error

    body = json.dumps({"destination": "dl5", "events": events}).encode("utf-8")
    if signature is None:
        sig_secret = secret if secret is not None else SECRET
        mac = hmac.new(sig_secret.encode("utf-8"), body, hashlib.sha256).digest()
        signature = base64.b64encode(mac).decode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/api/line/dms/webhook",
        data=body,
        headers={"Content-Type": "application/json", "x-line-signature": signature},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def ev_text(text: str) -> dict:
    return {
        "type": "message",
        "replyToken": "rt_" + str(int(time.time() * 1000)),
        "source": {"type": "user", "userId": LINE_USER_ID},
        "message": {"type": "text", "id": "m" + str(int(time.time() * 1000)), "text": text},
    }


def ev_image() -> dict:
    return {
        "type": "message",
        "replyToken": "rt_" + str(int(time.time() * 1000)),
        "source": {"type": "user", "userId": LINE_USER_ID},
        "message": {"type": "image", "id": "img" + str(int(time.time() * 1000))},
    }


def ev_postback(data: str) -> dict:
    return {
        "type": "postback",
        "replyToken": "rt_" + str(int(time.time() * 1000)),
        "source": {"type": "user", "userId": LINE_USER_ID},
        "postback": {"data": data},
    }


# ── OCR injection control ────────────────────────────────────────────────────
def set_ocr(id_card: dict) -> None:
    OCR_INJECT.write_text(json.dumps({"id_card": id_card}, ensure_ascii=False), encoding="utf-8")


# ── outbox (patched LINE outbound calls) ────────────────────────────────────
def read_outbox() -> list:
    if not OUTBOX.exists():
        return []
    out = []
    for line in OUTBOX.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def outbox_len() -> int:
    return len(read_outbox())


def wait_outbox(pred, since: int = 0, timeout: float = 90.0, poll: float = 0.6):
    """Wait until an outbox record at index >= since satisfies pred(rec).
    Returns (index, rec) or (None, None) on timeout."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        recs = read_outbox()
        for i in range(since, len(recs)):
            if pred(recs[i]):
                return i, recs[i]
        time.sleep(poll)
    return None, None


def flex_buttons(rec: dict) -> list:
    """Extract postback button data strings from a push_messages flex record."""
    out = []
    for msg in rec.get("messages") or []:
        contents = (msg or {}).get("contents") or {}
        footer = (contents.get("footer") or {}).get("contents") or []
        body = (contents.get("body") or {}).get("contents") or []
        for box in list(footer) + list(body):
            act = (box or {}).get("action") or {}
            if act.get("type") == "postback" and act.get("data"):
                out.append(act["data"])
            if act.get("type") == "uri" and act.get("uri"):
                out.append("URI::" + act["uri"])
    return out


# ── DMS readback (real login to the test site) ──────────────────────────────
def dms_op(fn):
    from services.erp.erp_dms_intake import _run_logged_in

    return _run_logged_in({"id": "dl5-readback", "config": DMS_CFG}, fn)


def lookup(pid: str) -> dict:
    return dms_op(lambda cl, ad: cl.lookup_customer(pid))


def search_booking(bk: str):
    return dms_op(lambda cl, ad: cl.search_booking(bk))


# ── DB helpers ──────────────────────────────────────────────────────────────
def _conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


def db_push_logs(user_id: str = USER_ID) -> list:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT id, invoice_no, seller_name, status, request_body, response_body, "
            "created_at FROM erp_push_logs WHERE user_id=%s ORDER BY created_at",
            (user_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def db_session() -> dict | None:
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT state, payload FROM dms_line_sessions WHERE line_user_id=%s",
            (LINE_USER_ID,),
        )
        r = cur.fetchone()
        return dict(r) if r else None
