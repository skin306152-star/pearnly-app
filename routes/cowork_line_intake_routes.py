"""Cowork LINE LIFF authentication and scoped draft review endpoints."""

from __future__ import annotations

import asyncio
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from core.auth import JWT_ALGORITHM, _jwt_secret
from core.feature_flags import erp_target_projection_enabled_for
from services.cloud_tasks import dispatch as cloud_dispatch
from services.erp import target_catalog_evidence, target_refresh
from services.cowork_line import identity_store, intake, session_store
from services.line_platform.liff import verify_id_token

router = APIRouter(tags=["cowork-line-intake"])
_ROOT = Path(__file__).resolve().parent.parent


class LiffAuthIn(BaseModel):
    id_token: str = ""
    draft_id: str = ""


class DraftUpdateIn(BaseModel):
    records: list[dict] = Field(default_factory=list)
    connection_workspace_client_id: int | None = None
    workspace_client_id: int | None = None
    endpoint_id: str = ""
    direction: str = ""
    adapter: str = ""
    target_label: str = ""
    account_root: str | None = None
    account_set: str | None = None
    catalog_refresh_request_id: str | None = None
    catalog_refresh_revision: int | None = None
    posting_kind: str | None = None
    payment: str | None = None


def _secret() -> str:
    raw = (_jwt_secret() + "cowork_line_intake:v1").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _error(exc: intake.CoworkLineIntakeError) -> HTTPException:
    return HTTPException(exc.status_code, detail=f"cowork_line_intake.{exc.code}")


def _session_for(identity: dict, draft_id: str) -> dict:
    session = session_store.get_session(
        tenant_id=identity["tenant_id"], line_user_id=identity["line_user_id"]
    )
    payload = (session or {}).get("payload") or {}
    ids = [str(value) for value in payload.get("history_ids") or []]
    if (
        not session
        or session.get("state") not in {"draft", "editing", "review"}
        or not payload.get("nonce")
        or str(draft_id) not in ids
    ):
        raise HTTPException(403, detail="cowork_line_intake.draft_forbidden")
    return session


@router.get("/api/cowork-line/intake/liff/config")
async def cowork_intake_liff_config():
    liff_id = os.getenv("LINE_COWORK_LIFF_ID", "").strip() or os.getenv("LINE_LIFF_ID", "").strip()
    return {"ok": True, "data": {"liff_id": liff_id}}


@router.post("/api/cowork-line/intake/liff/auth")
async def cowork_intake_liff_auth(req: LiffAuthIn):
    claims = verify_id_token(req.id_token, "LINE_COWORK_LIFF_ID")
    line_user_id = str((claims or {}).get("sub") or "")
    identity = identity_store.resolve_active_identity(line_user_id)
    if not identity:
        raise HTTPException(403, detail="cowork_line_intake.not_bound")
    session = _session_for(identity, req.draft_id)
    payload = session.get("payload") or {}
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "scope": "cowork_line_intake",
            "sub": identity["user_id"],
            "membership_id": identity["membership_id"],
            "tenant_id": identity["tenant_id"],
            "line_user_id": identity["line_user_id"],
            "draft_id": str(req.draft_id),
            "session_nonce": str(payload["nonce"]),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=20)).timestamp()),
            "aud": "cowork_line_intake",
        },
        _secret(),
        algorithm=JWT_ALGORITHM,
    )
    return {"ok": True, "data": {"token": token}}


@router.get("/liff/cowork-intake")
async def cowork_intake_liff_entry():
    return FileResponse(
        _ROOT / "static" / "dist" / "cowork-line-intake.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


def _draft_identity(request: Request, draft_id: str) -> dict:
    raw = request.headers.get("authorization", "")
    if not raw.lower().startswith("bearer "):
        raise HTTPException(401, detail="cowork_line_intake.auth_required")
    try:
        claims = jwt.decode(
            raw[7:].strip(),
            _secret(),
            algorithms=[JWT_ALGORITHM],
            audience="cowork_line_intake",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(401, detail="cowork_line_intake.auth_invalid")
    if claims.get("scope") != "cowork_line_intake" or str(claims.get("draft_id")) != draft_id:
        raise HTTPException(403, detail="cowork_line_intake.draft_forbidden")
    identity = identity_store.resolve_active_identity(str(claims.get("line_user_id") or ""))
    if (
        not identity
        or identity["membership_id"] != str(claims.get("membership_id") or "")
        or identity["tenant_id"] != str(claims.get("tenant_id") or "")
        or identity["user_id"] != str(claims.get("sub") or "")
    ):
        raise HTTPException(403, detail="cowork_line_intake.draft_forbidden")
    session = _session_for(identity, draft_id)
    if str((session.get("payload") or {}).get("nonce") or "") != str(
        claims.get("session_nonce") or ""
    ):
        raise HTTPException(403, detail="cowork_line_intake.draft_forbidden")
    return identity


@router.get("/api/cowork-line/intake/draft/{draft_id}")
async def cowork_intake_draft(request: Request, draft_id: str):
    identity = _draft_identity(request, draft_id)
    try:
        data = await asyncio.to_thread(intake.get_draft, identity, draft_id)
    except intake.CoworkLineIntakeError as exc:
        raise _error(exc) from exc
    return {"ok": True, "data": data}


@router.post("/api/cowork-line/intake/draft/{draft_id}/target/{endpoint_id}/refresh")
async def cowork_intake_target_refresh(
    request: Request,
    draft_id: str,
    endpoint_id: str,
    response: Response,
    workspace_client_id: int | None = Query(default=None),
):
    identity = _draft_identity(request, draft_id)
    try:
        target = await asyncio.to_thread(
            intake.get_target,
            identity,
            endpoint_id,
            workspace_client_id,
            include_account_catalog=False,
        )
    except intake.CoworkLineIntakeError as exc:
        raise _error(exc) from exc
    adapter = str(target.get("adapter") or "").lower()
    if not erp_target_projection_enabled_for(identity["tenant_id"], identity["user_id"]):
        raise HTTPException(409, detail="cowork_line_intake.target_refresh_unavailable")
    if adapter == "express" and not target.get("supports_master_refresh"):
        raise HTTPException(409, detail="cowork_line_intake.companion_update_required")
    try:
        refresh = await asyncio.to_thread(
            target_refresh.request_refresh,
            tenant_id=str(identity["tenant_id"]),
            user_id=str(identity["user_id"]),
            endpoint_id=str(target["endpoint_id"]),
            account_set_key=target_refresh.ENDPOINT_SCOPE_KEY,
            adapter=adapter,
            reason="cowork_line_editor_account_catalog",
        )
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from None
    if adapter == "mrerp":
        cloud_dispatch.spawn_sync(
            "erp.refresh", target_refresh.process_mrerp_request, refresh["request_id"]
        )
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True, "data": refresh}


@router.get("/api/cowork-line/intake/draft/{draft_id}/target/{endpoint_id}/refresh/{request_id}")
async def cowork_intake_target_refresh_status(
    request: Request,
    draft_id: str,
    endpoint_id: str,
    request_id: str,
    response: Response,
    workspace_client_id: int | None = Query(default=None),
):
    identity = _draft_identity(request, draft_id)
    try:
        compact_target = await asyncio.to_thread(
            intake.get_target,
            identity,
            endpoint_id,
            workspace_client_id,
            include_account_catalog=False,
        )
    except intake.CoworkLineIntakeError as exc:
        raise _error(exc) from exc
    if not erp_target_projection_enabled_for(identity["tenant_id"], identity["user_id"]):
        raise HTTPException(409, detail="cowork_line_intake.target_refresh_unavailable")
    refresh = await asyncio.to_thread(
        target_refresh.refresh_status,
        request_id,
        tenant_id=str(identity["tenant_id"]),
        endpoint_id=endpoint_id,
    )
    if (
        not refresh
        or str(refresh.get("account_set_key") or "") != target_refresh.ENDPOINT_SCOPE_KEY
    ):
        raise HTTPException(404, detail="cowork_line_intake.target_refresh_missing")
    data = {"refresh": refresh}
    if str(refresh.get("status") or "") == "succeeded":
        try:
            target = await asyncio.to_thread(
                intake.get_target,
                identity,
                endpoint_id,
                workspace_client_id,
                include_account_catalog=True,
            )
        except intake.CoworkLineIntakeError as exc:
            raise _error(exc) from exc
        receipt = await asyncio.to_thread(
            target_catalog_evidence.validate_refresh_receipt,
            tenant_id=str(identity["tenant_id"]),
            user_id=str(identity["user_id"]),
            endpoint_id=endpoint_id,
            adapter=str(compact_target.get("adapter") or ""),
            request_id=request_id,
            request_revision=refresh.get("result_revision"),
            catalog_revision=target.get("projection_revision"),
        )
        if not receipt["ok"]:
            raise HTTPException(409, detail="cowork_line_intake.target_refresh_superseded")
        data["target"] = target
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True, "data": data}


@router.put("/api/cowork-line/intake/draft/{draft_id}")
async def cowork_intake_update(request: Request, draft_id: str, req: DraftUpdateIn):
    identity = _draft_identity(request, draft_id)
    selection = req.model_dump(exclude={"records"})
    try:
        data = await asyncio.to_thread(
            intake.save_draft, identity, draft_id, req.records, selection
        )
    except intake.CoworkLineIntakeError as exc:
        raise _error(exc) from exc
    return {"ok": True, "data": data}


@router.post("/api/cowork-line/intake/draft/{draft_id}/confirm")
async def cowork_intake_confirm(request: Request, draft_id: str):
    identity = _draft_identity(request, draft_id)
    try:
        data = await intake.confirm_and_push(identity, draft_id)
    except intake.CoworkLineIntakeError as exc:
        raise _error(exc) from exc
    return {"ok": True, "data": data}


@router.post("/api/cowork-line/intake/draft/{draft_id}/discard")
async def cowork_intake_discard(request: Request, draft_id: str):
    identity = _draft_identity(request, draft_id)
    try:
        data = await asyncio.to_thread(intake.discard_draft, identity, draft_id)
    except intake.CoworkLineIntakeError as exc:
        raise _error(exc) from exc
    return {"ok": True, "data": data}


@router.get("/api/cowork-line/intake/draft/{draft_id}/records/{history_id}/page/{page}.png")
async def cowork_intake_page(request: Request, draft_id: str, history_id: str, page: int):
    identity = _draft_identity(request, draft_id)
    if page < 0:
        raise HTTPException(404, detail="cowork_line_intake.pdf_not_found")
    try:
        info = await asyncio.to_thread(intake.pdf_info, identity, draft_id, history_id)
    except intake.CoworkLineIntakeError as exc:
        raise _error(exc) from exc
    from services.ocr import pdf_storage
    from services.ocr.pdf_utils import render_page_png_bytes

    raw = await asyncio.to_thread(pdf_storage.read_bytes, info["pdf_storage_path"])
    rendered = await asyncio.to_thread(render_page_png_bytes, raw, page=page + 1)
    if rendered is None:
        raise HTTPException(422, detail="cowork_line_intake.render_failed")
    png, total_pages = rendered
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=300", "X-Page-Count": str(total_pages)},
    )
