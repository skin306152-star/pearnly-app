# -*- coding: utf-8 -*-
"""Real host provider: binds the knowledge contract to the main project.

The sandbox ran against host.stubs_local; in the app this provider supplies the
real identity, workspace visibility, OCR history, file storage, and usage
accounting. It is registered once at startup via contract.use_provider, so the
knowledge code keeps calling the contract layer unchanged.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from services.knowledge.contract import HostProvider, Identity, OcrHistoryRow
from services.membership.assignments import get_visible_client_ids_for_user
from services.ocr_history.queries import get_ocr_history_detail

logger = logging.getLogger(__name__)

_STORAGE_BASE = Path(os.environ.get("PDF_STORAGE_DIR", "/opt/mrpilot/storage/pdfs")) / "knowledge"


def _safe_path(key: str) -> Path:
    """Resolve a storage key under the knowledge base dir, rejecting traversal."""
    if ".." in key or key.startswith("/"):
        raise ValueError(f"illegal storage key: {key!r}")
    target = (_STORAGE_BASE / key).resolve()
    base = _STORAGE_BASE.resolve()
    if target != base and base not in target.parents:
        raise ValueError(f"illegal storage key: {key!r}")
    return target


class MainHostProvider(HostProvider):
    def get_current_identity(self, request: Any) -> Identity:
        user = get_current_user_from_request(request)
        owner = bool(user.get("is_super_admin")) or (user.get("role") or "owner") == "owner"
        return Identity(
            user_id=str(user["id"]),
            tenant_id=_tid(user),
            role="owner" if owner else "member",
        )

    def get_accessible_workspace_client_ids(self, identity: Identity) -> Optional[list[int]]:
        # get_visible_client_ids_for_user reads is_super_admin/role/id; identity
        # already folds super-admin into the "owner" role (unrestricted), so a
        # minimal user dict reproduces the canonical visibility without a re-fetch.
        return get_visible_client_ids_for_user({"id": identity.user_id, "role": identity.role})

    def get_ocr_history(self, history_id: str, identity: Identity) -> Optional[OcrHistoryRow]:
        detail = get_ocr_history_detail(identity.user_id, history_id, identity.tenant_id)
        if detail is None:
            return None
        return OcrHistoryRow(
            id=str(detail["id"]),
            user_id=identity.user_id,
            tenant_id=identity.tenant_id,
            workspace_client_id=detail.get("workspace_client_id"),
            payload=detail,
        )

    def storage_put(self, key: str, data: bytes) -> str:
        path = _safe_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def storage_get(self, key: str) -> bytes:
        return _safe_path(key).read_bytes()

    def storage_delete(self, key: str) -> None:
        _safe_path(key).unlink(missing_ok=True)

    def charge_credits(self, tenant_id: Optional[str], kind: str, amount: int, meta: dict) -> None:
        # Metered, not billed (product decision 2026-06-04). Log-only placeholder:
        # a durable usage sink (e.g. a usage_events row) is a follow-up before GA —
        # rotated logs alone cannot reconstruct billing.
        logger.info("knowledge usage tenant=%s kind=%s amount=%s", tenant_id, kind, amount)
