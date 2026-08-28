from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from core import db
from core.auth import JWT_ALGORITHM, _jwt_secret, get_current_user_from_request
from core.feature_flags import erp_line_enabled_for
from core.workspace_context import WS_HEADER
from services.auth.entrance import require_erp_portal
from services.line_binding import line_client, line_webhook_runner
from services.line_erp import store, webhook

router = APIRouter(tags=["line-erp"])
CHANNEL = "erp"
_ROOT = Path(__file__).resolve().parent.parent


class LiffAuthIn(BaseModel):
    id_token: str = ""
    draft_id: str = ""


class DraftUpdateIn(BaseModel):
    records: list[dict] = Field(default_factory=list)
    pages: list[dict] = Field(default_factory=list)
    fields: dict = Field(default_factory=dict)


def _draft_secret() -> str:
    raw = (_jwt_secret() + "line_erp_draft:v1").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _require_erp_account(request: Request) -> dict:
    user = get_current_user_from_request(request)
    if not user.get("is_super_admin") and (
        user.get("entry") != "erp"
        or not erp_line_enabled_for(user.get("tenant_id"), user.get("id"))
    ):
        raise HTTPException(403, detail="line_erp.not_invited")
    require_erp_portal(user)
    return user


@router.post("/api/line/erp/liff/auth")
async def erp_liff_auth(req: LiffAuthIn):
    from routes.line_liff_routes import _verify_id_token

    claims = _verify_id_token(req.id_token, "LINE_ERP_LIFF_ID")
    line_user_id = (claims or {}).get("sub", "")
    binding = store.get_binding(line_user_id)
    if not binding:
        raise HTTPException(403, detail="line_erp.not_bound")
    user = db.find_user_by_id(binding["user_id"])
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id")) != str(binding.get("tenant_id"))
    ):
        raise HTTPException(403, detail="line_erp.not_bound")
    if not user.get("is_super_admin") and not erp_line_enabled_for(
        binding.get("tenant_id"), binding.get("user_id")
    ):
        raise HTTPException(403, detail="line_erp.not_invited")
    draft_id = str(req.draft_id or "").strip()
    session = store.get_session(binding["tenant_id"], line_user_id)
    payload = (session or {}).get("payload") or {}
    history_ids = [str(value) for value in payload.get("history_ids") or []]
    nonce = str(payload.get("nonce") or "")
    if not draft_id or not session or draft_id not in history_ids or not nonce:
        raise HTTPException(403, detail="line_erp.draft_forbidden")
    now = datetime.now(timezone.utc)
    token_claims = {
        "scope": "line_erp_draft",
        "sub": str(user["id"]),
        "user_id": str(user["id"]),
        "tenant_id": str(binding["tenant_id"]),
        "line_user_id": line_user_id,
        "is_super_admin": bool(user.get("is_super_admin")),
        "draft_id": draft_id,
        "session_nonce": nonce,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=20)).timestamp()),
        "aud": "line_erp_draft",
    }
    token = jwt.encode(token_claims, _draft_secret(), algorithm=JWT_ALGORITHM)
    return {"ok": True, "data": {"token": token, "username": user.get("username") or ""}}


@router.get("/liff/erp/{draft_id}")
async def erp_liff_entry(draft_id: str):
    return FileResponse(
        _ROOT / "static" / "dist" / "erp-line-intake.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.post("/api/line/erp/binding-code")
async def erp_binding_code(request: Request):
    user = _require_erp_account(request)
    raw_workspace = request.headers.get(WS_HEADER, "").strip()
    workspace_client_id = None
    if raw_workspace:
        try:
            workspace_client_id = int(raw_workspace)
        except ValueError:
            raise HTTPException(400, detail="workspace.invalid")
        if not db.get_workspace_client(
            workspace_client_id, user["id"], tenant_id=user.get("tenant_id")
        ):
            raise HTTPException(403, detail="workspace.forbidden")
    data = store.new_code(user["tenant_id"], user["id"], workspace_client_id)
    basic_id = os.getenv("LINE_ERP_BOT_BASIC_ID", "").strip()
    friend_url = os.getenv("LINE_ERP_BOT_FRIEND_URL", "").strip()
    if basic_id and not friend_url:
        friend_url = f"https://line.me/R/ti/p/{basic_id}"
    data.update(
        {
            "bot_basic_id": basic_id or None,
            "bot_friend_url": friend_url or None,
        }
    )
    return {"ok": True, "data": data}


@router.get("/api/line/erp/binding")
async def erp_binding(request: Request):
    user = _require_erp_account(request)
    binding = store.get_binding_by_user(user["id"])
    return {
        "ok": True,
        "data": {
            "bound": bool(binding),
            "display_name": (binding or {}).get("display_name"),
            "workspace_client_id": (binding or {}).get("workspace_client_id"),
            "bound_at": (binding or {}).get("bound_at"),
        },
    }


@router.delete("/api/line/erp/binding")
async def erp_unbind(request: Request):
    user = _require_erp_account(request)
    store.unbind_by_user(user["id"])
    return {"ok": True, "data": {"bound": False}}


@router.get("/api/line/erp/liff/config")
async def erp_liff_config():
    return {"ok": True, "data": {"liff_id": os.getenv("LINE_ERP_LIFF_ID", "").strip()}}


def _draft_token(request: Request, draft_id: str) -> tuple[dict, dict, dict]:
    raw = request.headers.get("authorization", "")
    if not raw.lower().startswith("bearer "):
        raise HTTPException(401, detail="line_erp.draft_auth_required")
    try:
        claims = jwt.decode(
            raw[7:].strip(),
            _draft_secret(),
            algorithms=[JWT_ALGORITHM],
            audience="line_erp_draft",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(401, detail="line_erp.draft_auth_invalid")
    if claims.get("scope") != "line_erp_draft" or str(claims.get("draft_id")) != draft_id:
        raise HTTPException(403, detail="line_erp.draft_forbidden")
    binding = store.get_binding(str(claims.get("line_user_id") or ""))
    if (
        not binding
        or str(binding.get("tenant_id")) != str(claims.get("tenant_id"))
        or str(binding.get("user_id")) != str(claims.get("user_id"))
    ):
        raise HTTPException(403, detail="line_erp.draft_forbidden")
    if not claims.get("is_super_admin") and not erp_line_enabled_for(
        binding.get("tenant_id"), binding.get("user_id")
    ):
        raise HTTPException(403, detail="line_erp.not_invited")
    line_user_id = str(claims.get("line_user_id") or "")
    session = store.get_session(binding["tenant_id"], line_user_id)
    payload = (session or {}).get("payload") or {}
    history_ids = [str(value) for value in payload.get("history_ids") or []]
    if (
        not session
        or str(claims.get("session_nonce")) != str(payload.get("nonce"))
        or draft_id not in history_ids
    ):
        raise HTTPException(403, detail="line_erp.draft_forbidden")
    user = db.find_user_by_id(str(claims["user_id"]))
    if (
        not user
        or not user.get("is_active", True)
        or str(user.get("tenant_id")) != str(binding.get("tenant_id"))
    ):
        raise HTTPException(403, detail="line_erp.draft_forbidden")
    return claims, binding, session


@router.get("/api/line/erp/draft/{draft_id}/records/{history_id}/page/{page}.png")
async def erp_draft_page(request: Request, draft_id: str, history_id: str, page: int):
    claims, binding, session = _draft_token(request, draft_id)
    history_ids = [str(value) for value in (session.get("payload") or {}).get("history_ids") or []]
    if history_id not in history_ids or page < 0:
        raise HTTPException(403, detail="line_erp.draft_forbidden")
    from services.ocr import pdf_storage
    from services.ocr.pdf_utils import render_page_png_bytes
    from services.ocr_history.queries import get_history_pdf_info

    info = get_history_pdf_info(
        str(claims["user_id"]), history_id, tenant_id=str(binding["tenant_id"])
    )
    if not info:
        raise HTTPException(404, detail="line_erp.pdf_not_found")
    data = pdf_storage.read_bytes(info["pdf_storage_path"])
    # URL 使用 0-based 页码，渲染器使用 1-based；边界只在这里转换一次。
    rendered = render_page_png_bytes(data, page=page + 1) if data else None
    if rendered is None:
        raise HTTPException(422, detail="line_erp.render_failed")
    png, total_pages = rendered
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=300", "X-Page-Count": str(total_pages)},
    )


@router.get("/api/line/erp/draft/{draft_id}")
async def erp_draft_get(request: Request, draft_id: str):
    claims, binding, session = _draft_token(request, draft_id)
    payload = session.get("payload") or {}
    history_ids = [str(value) for value in payload.get("history_ids") or []]
    return {
        "ok": True,
        "data": {
            "draft_id": draft_id,
            "mode": payload.get("mode"),
            "direction": payload.get("mode"),
            "records": webhook.draft_records(
                str(claims["user_id"]), str(binding["tenant_id"]), draft_id, history_ids
            ),
        },
    }


@router.put("/api/line/erp/draft/{draft_id}")
async def erp_draft_update(request: Request, draft_id: str, req: DraftUpdateIn):
    claims, binding, session = _draft_token(request, draft_id)
    expected_ids = [str(value) for value in (session.get("payload") or {}).get("history_ids") or []]
    submitted_ids = [
        str(record.get("id") or record.get("history_id") or "") for record in req.records
    ]
    if submitted_ids != expected_ids:
        raise HTTPException(409, detail="line_erp.records_incomplete")
    from services.ocr_history.mutations import update_ocr_history_pages

    allowed_ids = set(expected_ids)
    for record in req.records:
        history_id = str(record.get("id") or record.get("history_id") or "")
        pages = record.get("pages")
        if history_id not in allowed_ids or not isinstance(pages, list):
            raise HTTPException(403, detail="line_erp.draft_forbidden")
        if not update_ocr_history_pages(
            str(claims["user_id"]), history_id, pages, tenant_id=str(binding["tenant_id"])
        ):
            raise HTTPException(409, detail="line_erp.draft_save_failed")
    return {
        "ok": True,
        "data": {
            "draft_id": draft_id,
            "records": webhook.draft_records(
                str(claims["user_id"]), str(binding["tenant_id"]), draft_id, expected_ids
            ),
        },
    }


@router.post("/api/line/erp/draft/{draft_id}/confirm")
async def erp_draft_confirm(request: Request, draft_id: str):
    claims, binding, _ = _draft_token(request, draft_id)
    result = await webhook.act_draft(
        binding, str(claims["line_user_id"]), None, draft_id, "confirm"
    )
    if not result.get("ok"):
        raise HTTPException(
            result.get("status", 409), detail=result.get("detail", "line_erp.confirm_failed")
        )
    return {"ok": True, "data": result}


@router.post("/api/line/erp/draft/{draft_id}/discard")
async def erp_draft_discard(request: Request, draft_id: str):
    claims, binding, _ = _draft_token(request, draft_id)
    result = await webhook.act_draft(
        binding, str(claims["line_user_id"]), None, draft_id, "discard"
    )
    if not result.get("ok"):
        raise HTTPException(
            result.get("status", 409), detail=result.get("detail", "line_erp.discard_failed")
        )
    return {"ok": True, "data": result}


@router.post("/api/line/erp/webhook")
async def erp_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")
    if not line_client.verify_signature(body, signature, channel=CHANNEL):
        raise HTTPException(400, detail="line_erp.bad_signature")
    try:
        payload = json.loads(body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(400, detail="line_erp.bad_json")
    for event in payload.get("events") or []:
        await line_webhook_runner.run_event(
            event,
            webhook.handle_event,
            source="line_erp_webhook",
            channel=CHANNEL,
            failed_text="ดำเนินการไม่สำเร็จ กรุณาส่งใหม่",
        )
    return {"ok": True}
