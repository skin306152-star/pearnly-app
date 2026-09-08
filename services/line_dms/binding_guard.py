"""Revalidate the same LINE binding before work and after asynchronous waits."""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import functools
import logging

from core import db
from core.pos_api import PosError
from services.dms_roster import store as roster_store
from services.line_dms import store

logger = logging.getLogger(__name__)
_binding = contextvars.ContextVar("line_dms_binding", default=None)


class BindingChanged(Exception):
    """An old operation must stop without notifying the newly bound user."""


def current(binding: dict, line_user_id: str = "") -> bool:
    if not binding or not binding.get("id"):
        return False
    line_id = line_user_id or binding.get("line_user_id")
    if not line_id or line_id != binding.get("line_user_id"):
        return False
    channel = str(binding.get("channel_key") or "")
    live = store.get_binding_by_line_user(line_id, channel)
    if not live or any(
        str(live.get(k) or "") != str(binding.get(k) or "")
        for k in ("id", "user_id", "tenant_id", "channel_key")
    ):
        return False
    from services.line_dms import account_channel

    try:
        assigned = account_channel.get_channel(
            account_channel.subject_for(binding.get("tenant_id"), binding.get("user_id"))
        )
    except account_channel.AccountChannelError:
        logger.error("DMS binding rejected: account OA assignment unavailable")
        return False
    if assigned != channel:
        return False
    user = db.find_user_by_id(str(binding["user_id"]))
    if not user or not user.get("is_active", True):
        return False
    if str(user.get("tenant_id") or "") != str(binding["tenant_id"]):
        return False
    profile = roster_store.get_profile(str(binding["tenant_id"]), str(binding["user_id"]))
    if profile:
        return (
            profile.get("status") == "active"
            and (not binding.get("_require_query") or profile.get("can_query_dms") is True)
            and (not binding.get("_require_admin") or profile.get("dms_role") == "admin")
        )
    # Existing owner bindings do not require an operator profile; members always do.
    return (
        user.get("role") == "owner"
        and not binding.get("_require_query")
        and not binding.get("_require_admin")
    )


def snapshot():
    return _binding.get()


def current_channel() -> str:
    """OA key of the binding in scope; legacy default when no binding is scoped.

    Every DMS outbound call resolves its channel through this, so a reply/push/rich-menu
    operation always uses the same OA the event arrived on.
    """
    from services.line_platform import channels as line_channels

    binding = snapshot()
    if binding and binding.get("channel_key"):
        return line_channels.normalize(binding.get("channel_key"))
    return line_channels.DEFAULT_DMS_CHANNEL


def require_current() -> None:
    binding = snapshot()
    if binding is not None and not current(binding):
        raise BindingChanged("dms_binding_changed")


@contextlib.contextmanager
def scope(binding):
    token = _binding.set(binding)
    try:
        yield
    finally:
        _binding.reset(token)


def bound_task(function):
    """Works for both durable deliveries and local asyncio tasks."""

    @functools.wraps(function)
    async def run(binding, line_user_id, *args, **kwargs):
        if not await asyncio.to_thread(current, binding, line_user_id):
            logger.warning("DMS stale task cancelled: handler=%s", function.__name__)
            return
        scoped_binding = {
            **binding,
            "_require_query": function.__name__ in {"_run_records", "_run_top"},
            "_require_admin": function.__name__ == "_execute_approved",
        }
        with scope(scoped_binding):
            try:
                return await function(binding, line_user_id, *args, **kwargs)
            except BindingChanged:
                logger.warning("DMS binding changed during task: handler=%s", function.__name__)

    return run


def authorize_browser(request, user: dict) -> dict:
    from core.auth import decode_access_token
    from services.line_platform import channels

    header = request.headers.get("Authorization", "")
    claims = decode_access_token(header[7:].strip()) if header.startswith("Bearer ") else None
    identity = (claims or {}).get("dms_binding") or {}
    raw_channel = str(identity.get("channel_key") or "").strip()
    if raw_channel and not channels.is_valid(raw_channel):
        raise PosError("dms_booking.not_bound", 401, detail="line_binding_changed")
    token_channel = raw_channel or channels.DEFAULT_DMS_CHANNEL
    binding = store.get_binding_by_line_user(identity.get("line_user_id"), token_channel)
    if (
        not claims
        or claims.get("entry") != "dms"
        or claims.get("typ") != "access"
        or not identity.get("id")
        or not binding
        or str(binding.get("id")) != str(identity["id"])
        or str(binding.get("user_id")) != str(user.get("id"))
        or str(claims.get("sub")) != str(user.get("id"))
        or str(binding.get("channel_key") or "") != token_channel
        or not current(binding)
    ):
        raise PosError("dms_booking.not_bound", 401, detail="line_binding_changed")
    return {**user, "_dms_binding": binding}


def browser_call(user: dict, function, *args, **kwargs):
    """Keep the browser's binding through synchronous external work."""
    with scope(user.get("_dms_binding")):
        try:
            require_current()
            result = function(*args, **kwargs)
            require_current()
            return result
        except BindingChanged as exc:
            raise PosError("dms_booking.not_bound", 401, detail="line_binding_changed") from exc
