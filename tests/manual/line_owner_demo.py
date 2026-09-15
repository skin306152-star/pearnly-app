"""Local-only interactive LINE simulator backed by disposable PG and native WeKan.

Run with the same loopback environment as test_cowork_line_owner_native.
LINE transport and browser SSO are simulated; business code and native storage
are real. This server is never included in the production application.
"""

import base64
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sys
import threading
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from services.cowork_line import work_flow, work_store, work_notifications, work_invites, work_live
from tests.manual import line_demo_accounts
from services.work_bridge import line_owner
from tests.unit.test_cowork_line_work_pg_smoke import WorkOwnerPgTests


def main():
    native_url = os.environ["LINE_OWNER_TEST_URL"]
    if urlsplit(native_url).hostname not in {"localhost", "127.0.0.1"}:
        raise RuntimeError("A disposable local WeKan is required")
    secret = os.environ["LINE_OWNER_TEST_SECRET"]
    fixture = WorkOwnerPgTests()
    fixture.setUp()
    identity = fixture.identity
    employee_id = str(uuid4())
    with fixture.cursor(commit=True) as cur:
        cur.execute("INSERT INTO users VALUES (%s,'ming','阿明',NULL,true,NULL)", (employee_id,))
        employee_role = str(uuid4())
        cur.execute("INSERT INTO roles VALUES (%s,'accountant')", (employee_role,))
        membership = str(uuid4())
        cur.execute(
            "INSERT INTO memberships VALUES (%s,%s,%s,%s,'active')",
            (membership, employee_id, identity["tenant_id"], employee_role),
        )
        cur.execute(
            "INSERT INTO cowork_line_identities VALUES (%s,%s,%s,'local-employee',NULL)",
            (membership, employee_id, identity["tenant_id"]),
        )
    employee_identity = {
        "user_id": employee_id,
        "tenant_id": identity["tenant_id"],
        "membership_id": membership,
        "line_user_id": "local-employee",
    }

    def persona(value):
        return employee_identity if value == "employee" else identity

    line_demo_accounts.prepare(fixture)
    notices = []
    messages = []
    files = {}
    mutex = threading.RLock()
    session = secrets.token_hex(32)
    native_identity = {
        "user_id": employee_id,
        "tenant_id": identity["tenant_id"],
        "username": "pearnly-" + employee_id,
        "display_name": "阿明",
        "email": None,
        "is_platform_admin": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
    }

    def notice(*args, **kwargs):
        notices.append(
            {"recipient": args[0], "messages": args[1] if isinstance(args[1], list) else [args[1]]}
        )
        return True

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send(self, value, status=200):
            raw = json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            route = urlsplit(self.path)
            if route.path == "/api/cowork-line/intake/liff/config":
                return self.send({"ok": True, "data": {"liff_id": "local-demo"}})
            asset = line_demo_accounts.asset(route.path)
            if asset:
                self.send_response(200)
                self.send_header("Content-Type", asset[1])
                self.end_headers()
                self.wfile.write(asset[0])
                return
            if route.path == "/":
                raw = Path(__file__).with_suffix(".html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(raw)
                return
            if route.path == "/work":
                state = parse_qs(route.query).get("state", [""])[0]
                if not state or len(state) != 43:
                    return self.send({"error": "state"}, 400)
                import html

                raw = (
                    f'<form method="post" action="{native_url}/_pearnly/consume">'
                    f'<input name="state" value="{html.escape(state)}"><input name="ticket" value="demo-ticket">'
                    "</form><script>document.forms[0].submit()</script>"
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(raw)
                return
            if route.path == "/demo/state":
                with mutex:
                    selected = persona(parse_qs(route.query).get("persona", ["owner"])[0])
                    with work_store.conversation(selected) as state:
                        data = json.loads(json.dumps(state))
                    native = (
                        line_owner.snapshot(selected, data["board"]) if data.get("board") else {}
                    )
                return self.send(
                    {
                        "state": data,
                        "native": native,
                        "notices": notices,
                        "messages": [
                            x
                            for x in messages
                            if x["persona"]
                            == ("employee" if selected is employee_identity else "owner")
                        ],
                        "employee": employee_identity["user_id"],
                        "line_user_id": selected["line_user_id"],
                    }
                )
            self.send({}, 404)

        def do_POST(self):
            body = json.loads(
                self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}"
            )
            if self.path.startswith("/api/cowork-line/work-live/"):
                with mutex:
                    try:
                        result = (
                            work_live.authenticate(body["id_token"])
                            if self.path.endswith("/auth")
                            else work_live.read(body["token"], body.get("board", ""))
                        )
                        return self.send(result)
                    except Exception as exc:
                        return self.send(
                            {"detail": getattr(exc, "detail", "failed")},
                            getattr(exc, "status_code", 500),
                        )
            if self.path.startswith("/api/work/service/"):
                if self.headers.get("Authorization") != "Bearer " + secret:
                    return self.send({}, 401)
                with mutex:
                    if self.path.endswith("/session"):
                        return self.send(
                            native_identity if body.get("session") == session else {},
                            200 if body.get("session") == session else 401,
                        )
                    if self.path.endswith("/consume"):
                        return self.send({**native_identity, "session": session})
                    if self.path.endswith(("/line-owner", "/line-actor")):
                        try:
                            return self.send(line_owner.actor(body))
                        except Exception:
                            return self.send({}, 403)
                    if self.path.endswith("/line-event"):
                        return self.send(work_notifications.deliver(**body))
                    return self.send({}, 404)
            if self.path in {
                "/api/login",
                "/api/cowork-line/connect",
                "/api/cowork-line/work-invite",
            }:
                with mutex:
                    try:
                        if self.path.endswith("/connect"):
                            auth = self.headers.get("Authorization", "")
                            if not auth.startswith("Bearer demo-session-"):
                                return self.send({"detail": "unauthorized"}, 401)
                            body["_demo_user"] = auth.removeprefix("Bearer demo-session-")
                        return self.send(
                            line_demo_accounts.account_request(
                                self.path, body, fixture, employee_identity
                            )
                        )
                    except Exception as exc:
                        return self.send({"detail": getattr(exc, "detail", str(exc))}, 400)
            if self.path != "/demo/message":
                return self.send({}, 404)
            with mutex:
                event = body.get("event", {})
                if body.get("file"):
                    file = body["file"]
                    message_id = "demo-" + secrets.token_hex(8)
                    files[message_id] = base64.b64decode(file["data"])
                    event = {
                        "type": "message",
                        "message": {
                            "type": "file",
                            "id": message_id,
                            "fileName": file["name"],
                            "fileSize": len(files[message_id]),
                        },
                    }
                try:
                    response = work_flow.process(
                        event, persona(body.get("persona")), body.get("lang", "th")
                    )
                    if response is None and event.get("message", {}).get("text") == "เมนู":
                        from services.cowork_line.menu_cards import menu_card

                        response = menu_card("th")
                    messages.append(
                        {
                            "event": event,
                            "response": response,
                            "persona": body.get("persona", "owner"),
                        }
                    )
                    self.send({"response": response})
                except Exception as exc:
                    self.send({"error": str(exc)}, 500)

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(work_invites, "url", side_effect=line_demo_accounts.local_url)
        )
        stack.enter_context(
            patch.object(
                work_invites,
                "claims",
                side_effect=lambda token: (
                    {"sub": token} if token in {"local-owner", "local-invited"} else {}
                ),
            )
        )
        stack.enter_context(
            patch("services.cowork_line.push_recovery.reconcile_stale_legacy_reservations")
        )
        stack.enter_context(
            patch.dict(
                os.environ,
                {
                    "WORK_BRIDGE_URL": native_url,
                    "WORK_BRIDGE_SECRET": secret,
                    "PEARNLY_ENV": "development",
                },
            )
        )
        stack.enter_context(patch.object(work_flow.line, "push_messages", side_effect=notice))
        stack.enter_context(patch.object(work_notifications, "push", side_effect=notice))
        stack.enter_context(
            patch.object(
                work_flow.line,
                "download_message_content",
                side_effect=lambda key, **kw: files.get(key),
            )
        )
        print("LINE simulator: http://localhost:18099 · isolated native storage", flush=True)
        try:
            ThreadingHTTPServer(("0.0.0.0", 18099), Handler).serve_forever()
        finally:
            fixture.tearDown()
            fixture.doCleanups()


if __name__ == "__main__":
    main()
