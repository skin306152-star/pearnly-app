"""Cowork web and bound LINE identities share existing membership permissions."""

from datetime import datetime, timedelta, timezone
import hashlib
import jwt
from fastapi import HTTPException

from core import db
from core.auth import JWT_ALGORITHM, _jwt_secret
from core.workspace_context import WorkspaceScope, require_workspace_id
from services.authz.deps import actor_has_perm, check_workspace_scope, get_authz, require_perm
from services.cowork_line.identity_store import resolve_active_identity
from services.line_platform.liff import verify_id_token


def _secret():
    return hashlib.sha256((_jwt_secret() + ":cowork_stocktake:v1").encode()).hexdigest()


def line_login(id_token):
    claims = verify_id_token(id_token, "LINE_COWORK_LIFF_ID")
    identity = resolve_active_identity(str((claims or {}).get("sub") or ""))
    if not identity:
        raise HTTPException(403, detail="stocktake.not_bound")
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": identity["line_user_id"],
            "membership": identity["membership_id"],
            "aud": "cowork_stocktake",
            "iat": now,
            "exp": now + timedelta(hours=8),
        },
        _secret(),
        algorithm=JWT_ALGORITHM,
    )
    return {"token": token}


def authorize(request, code):
    if request.headers.get("X-Stocktake-Line") == "1":
        try:
            claims = jwt.decode(
                request.headers.get("Authorization", "")[7:],
                _secret(),
                algorithms=[JWT_ALGORITHM],
                audience="cowork_stocktake",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(401, detail="stocktake.auth_required") from None
        identity = resolve_active_identity(str(claims.get("sub") or ""))
        if not identity or identity["membership_id"] != claims.get("membership"):
            raise HTTPException(403, detail="stocktake.not_bound")
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE id=%s AND is_active=TRUE", (identity["user_id"],)
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(403, detail="stocktake.not_bound")
        user = dict(row)
        user.update(tenant_id=identity["tenant_id"], entry="cowork", is_super_admin=False)
        if not actor_has_perm(request, user, code):
            raise HTTPException(403, detail="authz.forbidden")
    else:
        user = require_perm(request, code)
    if user.get("entry") in ("erp", "pos", "ai", "dms") or not user.get("tenant_id"):
        raise HTTPException(403, detail="authz.forbidden")
    return user


def scope_for(request, code):
    user = authorize(request, code)
    ws = require_workspace_id(request)
    check_workspace_scope(request, user, ws)
    return WorkspaceScope(str(user["tenant_id"]), ws, str(user["id"]))


def workspaces(request):
    user = authorize(request, "recon.view")
    authz = get_authz(request, user)
    with db.get_cursor_rls(tenant_id=str(user["tenant_id"])) as cur:
        cur.execute(
            "SELECT id, name FROM workspace_clients WHERE tenant_id=%s AND is_active=TRUE "
            "ORDER BY name",
            (str(user["tenant_id"]),),
        )
        rows = [dict(r) for r in cur.fetchall() if authz.allows_workspace(r["id"])]
    return {"clients": rows}
