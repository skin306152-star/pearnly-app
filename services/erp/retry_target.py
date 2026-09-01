"""Reapply the account choice captured by a push log before retrying it."""

from __future__ import annotations

import json
from typing import Any

from services.erp.line_target_choice import endpoint_with_account_choice


def _body(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def endpoint_for_retry(endpoint: dict[str, Any], request_body: Any) -> dict[str, Any]:
    request = _body(request_body)
    payload = request.get("payload") if isinstance(request.get("payload"), dict) else request
    adapter = str(endpoint.get("adapter") or "").lower()
    if adapter == "mrerp":
        account_set = str(payload.get("account_set") or request.get("account_set") or "")
        parts = account_set.split(":", 1)
        if len(parts) == 2 and all(part.strip() for part in parts):
            return endpoint_with_account_choice(
                endpoint,
                {"comidyear": parts[0].strip(), "seldb": parts[1].strip()},
            )
    if adapter == "express":
        account_set = str(payload.get("account_set") or request.get("account_set") or "").strip()
        if account_set:
            return endpoint_with_account_choice(endpoint, {"account_set": account_set})
    return endpoint


def request_after_retry(original: Any, attempted: Any) -> dict[str, Any]:
    previous = _body(original)
    current = _body(attempted)
    if not current:
        return previous
    source = str(previous.get("source") or "").strip()
    if source:
        current["source"] = source
    return current


__all__ = ["endpoint_for_retry", "request_after_retry"]
