"""Server-side access check for the privileged DMS query flow."""

from __future__ import annotations

from services.dms_roster import store as roster_store


def can_query(binding: dict) -> bool:
    tenant_id = str(binding.get("tenant_id") or "")
    user_id = str(binding.get("user_id") or "")
    if not tenant_id or not user_id:
        return False
    profile = roster_store.get_profile(tenant_id, user_id)
    return bool(
        profile and profile.get("status") == "active" and profile.get("can_query_dms") is True
    )


__all__ = ["can_query"]
