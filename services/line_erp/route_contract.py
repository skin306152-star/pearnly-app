"""Request models and token-secret derivation for ERP LINE routes."""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, Field

from core.auth import _jwt_secret


class LiffAuthIn(BaseModel):
    id_token: str = ""
    draft_id: str = ""


class DraftUpdateIn(BaseModel):
    records: list[dict] = Field(default_factory=list)
    pages: list[dict] = Field(default_factory=list)
    fields: dict = Field(default_factory=dict)
    endpoint_id: str = ""
    workspace_client_id: int | None = None
    direction: str = ""
    adapter: str = ""
    target_label: str = ""
    account_root: str | None = None
    account_set: str | None = None
    catalog_refresh_request_id: str | None = None
    catalog_refresh_revision: int | None = None
    posting_kind: str | None = None
    payment: str | None = None


def draft_secret() -> str:
    raw = (_jwt_secret() + "line_erp_draft:v1").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


__all__ = ["DraftUpdateIn", "LiffAuthIn", "draft_secret"]
