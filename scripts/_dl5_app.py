# -*- coding: utf-8 -*-
"""DL-5 forensic harness · boots the real app with LINE outbound spied and OCR
injected (underscore = not shipped).

Patches (test scaffolding only — product code untouched):
  * services.line_binding.line_client outbound funcs → record to outbox.jsonl,
    never hit api.line.me (LINE_DMS_CHANNEL_ACCESS_TOKEN is a dummy).
  * services.erp.dms_id_ocr.recognize_id_card → return the id-card dict staged
    in ocr_inject.json, then run the REAL mod-11 checksum flag so the checksum
    gate (G4) is exercised for real. DMS writes stay real.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly?sslmode=disable",
)
os.environ["PGSSLMODE"] = "disable"
os.environ["LINE_DMS_CHANNEL_SECRET"] = "e2e-test-secret"
os.environ["LINE_DMS_CHANNEL_ACCESS_TOKEN"] = "dummy"
os.environ.setdefault("JWT_SECRET", "dl5-e2e-jwt-secret-please-32chars-long")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from scripts import _dl5_common as C  # noqa: E402

C.OUTBOX.parent.mkdir(parents=True, exist_ok=True)
C.OUTBOX.write_text("", encoding="utf-8")


def _record(kind: str, **fields) -> None:
    rec = {"kind": kind, **fields}
    with open(C.OUTBOX, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _patch_line_client() -> None:
    from services.line_binding import line_client as lc

    def reply_text(reply_token, text, *, channel="default"):
        _record("reply_text", channel=channel, reply_token=reply_token, text=text)
        return True

    def push_text(to, text, *, channel="default"):
        _record("push_text", channel=channel, to=to, text=text)
        return True

    def push_messages(to, messages, *, channel="default"):
        _record("push_messages", channel=channel, to=to, messages=messages)
        return True

    def push_messages_with_meta(to, messages, *, channel="default"):
        _record("push_messages_meta", channel=channel, to=to, messages=messages)
        return [{"id": "sent"} for _ in (messages or [])]

    def reply_messages(reply_token, messages, *, channel="default"):
        _record("reply_messages", channel=channel, reply_token=reply_token, messages=messages)
        return True

    def reply_messages_with_meta(reply_token, messages, *, channel="default"):
        _record("reply_messages_meta", channel=channel, reply_token=reply_token, messages=messages)
        return [{"id": "sent"} for _ in (messages or [])]

    def start_loading(to, seconds=20, *, channel="default"):
        _record("start_loading", channel=channel, to=to, seconds=seconds)
        return True

    def download_message_content(message_id, *, channel="default"):
        _record("download", channel=channel, message_id=message_id)
        return b"\x89PNG\r\n\x1a\n" + b"0" * 64  # non-empty; OCR is injected

    def get_user_profile(line_user_id, *, channel="default"):
        return {"displayName": "DL5 Tester", "userId": line_user_id}

    lc.reply_text = reply_text
    lc.push_text = push_text
    lc.push_messages = push_messages
    lc.push_messages_with_meta = push_messages_with_meta
    lc.reply_messages = reply_messages
    lc.reply_messages_with_meta = reply_messages_with_meta
    lc.start_loading = start_loading
    lc.download_message_content = download_message_content
    lc.get_user_profile = get_user_profile


def _patch_ocr() -> None:
    from services.erp import dms_id_ocr as ocr

    real_resolve = ocr.resolve_dms_endpoint
    real_flag = ocr._flag_bad_id_checksum

    def fake_recognize(user, content, filename, content_type="", endpoint_id=None):
        ep = real_resolve(str(user["id"]), endpoint_id)
        if not ep:
            raise ocr.DmsOcrError("dms.no_endpoint", 400, "dms.no_endpoint")
        staged = json.loads(C.OCR_INJECT.read_text(encoding="utf-8"))
        result = {"id_card": staged["id_card"]}
        real_flag(result)  # real mod-11 checksum → sets needs_review for G4
        _record("ocr_injected", people_id=staged["id_card"].get("people_id"),
                needs_review=bool(result.get("needs_review")))
        return ep, result, 0

    ocr.recognize_id_card = fake_recognize


_patch_line_client()
_patch_ocr()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=C.PORT, log_level="warning")
