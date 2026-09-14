"""Disposable simulator account support; never registered in the application."""

from pathlib import Path
from urllib.parse import urlencode

from core.auth import verify_password
from services.cowork_line import work_invites
from services.work_bridge import schema


def prepare(fixture):
    with fixture.cursor(commit=True) as cur:
        cur.execute(
            "ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid(), ADD COLUMN tenant_id uuid, ADD COLUMN company_name text, ADD COLUMN password_hash text, ADD COLUMN email_normalized text, ADD COLUMN plan text, ADD COLUMN is_super_admin boolean DEFAULT false, ADD COLUMN role text, ADD COLUMN invited_by uuid"
        )
        cur.execute("UPDATE users SET tenant_id=%s", (fixture.identity["tenant_id"],))
        cur.execute(
            "ALTER TABLE roles ADD COLUMN tenant_id uuid, ADD COLUMN is_active boolean DEFAULT true, ADD COLUMN permissions jsonb DEFAULT '[]'"
        )
        cur.execute(
            "ALTER TABLE memberships ALTER COLUMN id SET DEFAULT gen_random_uuid(), ADD UNIQUE(user_id), ADD COLUMN scope_mode text, ADD COLUMN granted_by uuid, ADD COLUMN granted_at timestamptz"
        )
        cur.execute(
            "ALTER TABLE cowork_line_identities ADD PRIMARY KEY(membership_id), ADD UNIQUE(line_user_id), ADD COLUMN display_name text, ADD COLUMN picture_url text, ADD COLUMN friendship_ready boolean, ADD COLUMN friendship_checked_at timestamptz, ADD COLUMN connected_at timestamptz, ADD COLUMN last_seen_at timestamptz"
        )
    schema.migrate_schema()


def local_url(mode="connect", board=""):
    return (
        "http://localhost:18099/liff/"
        + ("cowork-live" if mode == "live" else "cowork-connect")
        + "?"
        + urlencode({"flow": "cowork-connect", "draft": mode, "board": board})
    )


def asset(route):
    root = Path(__file__).resolve().parents[2]
    if route in {"/liff/cowork-connect", "/liff/cowork-live"}:
        raw = (
            (
                root
                / (
                    "static/cowork-live/index.html"
                    if route.endswith("cowork-live")
                    else "static/cowork-connect/index.html"
                )
            )
            .read_text()
            .replace("https://static.line-scdn.net/liff/edge/2/sdk.js", "/demo/liff.js")
        )
        return raw.encode(), "text/html; charset=utf-8"
    if route == "/demo/liff.js":
        return (
            b"window.liff={init:async()=>{},isLoggedIn:()=>true,getIDToken:()=>new URLSearchParams(location.search).get('persona')==='owner'||new URLSearchParams(location.search).get('draft')==='invite'?'local-owner':'local-invited',closeWindow:()=>{location.href='/';}};",
            "text/javascript",
        )
    if route in {
        "/static/cowork-connect/app.js",
        "/static/pearnly-ui.css",
        "/static/cowork-live/app.js",
        "/static/cowork-live/style.css",
    }:
        return (root / route.lstrip("/")).read_bytes(), (
            "text/javascript" if route.endswith("js") else "text/css"
        )
    return None


def account_request(path, body, fixture, employee_identity):
    if path == "/api/cowork-line/work-invite":
        return work_invites.invite(
            body["id_token"],
            body["request_id"],
            body["account"],
            body["password"],
            body["display_name"],
            body["board"],
        )
    if path == "/api/login":
        with fixture.cursor() as cur:
            cur.execute(
                "SELECT id::text,password_hash FROM users WHERE username=%s AND is_active=TRUE",
                (body["username"].lower(),),
            )
            row = cur.fetchone()
        if not row or not verify_password(body["password"], row["password_hash"]):
            raise ValueError("login_failed")
        # Explicit test-only session. Production uses the existing /api/login JWT.
        return {"token": "demo-session-" + row["id"]}
    if path == "/api/cowork-line/connect":
        user_id = body.pop("_demo_user")
        result = work_invites.connect(user_id, fixture.identity["tenant_id"], body["id_token"])
        with fixture.cursor() as cur:
            cur.execute("SELECT id::text FROM memberships WHERE user_id=%s", (user_id,))
            membership = cur.fetchone()["id"]
        employee_identity.update(
            user_id=user_id, membership_id=membership, line_user_id="local-invited"
        )
        return {**result, "bot_friend_url": "http://localhost:18099/"}
    return None
