"""Push confirmed ERP LINE records through the owner's configured target."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException

from services.erp.confirmed_push import dispatch_confirmed_history

logger = logging.getLogger("mr-pilot")


async def dispatch_confirmed(
    *, user: dict[str, Any], binding: dict[str, Any], history_ids: list[str]
) -> dict[str, Any]:
    results = []
    for history_id in history_ids:
        try:
            pushed = await dispatch_confirmed_history(
                user=user,
                history_id=history_id,
                workspace_client_id=binding.get("workspace_client_id"),
            )
        except HTTPException as exc:
            detail = exc.detail
            code = detail.get("code") if isinstance(detail, dict) else str(detail)
            pushed = {"ok": False, "status": "failed", "error_msg": code}
        except Exception as exc:
            logger.exception("[line-erp] confirmed history push failed · history=%s", history_id)
            pushed = {
                "ok": False,
                "status": "failed",
                "error_msg": type(exc).__name__,
            }
        results.append({"history_id": history_id, **pushed})
    return {
        "ok": True,
        "push_ok": bool(results) and all(row.get("ok") for row in results),
        "push_results": results,
    }


__all__ = ["dispatch_confirmed"]
