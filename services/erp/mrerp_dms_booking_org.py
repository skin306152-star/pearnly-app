# -*- coding: utf-8 -*-
"""Resolve the booking organization through the native advisor cascade.

The DMS booking form's detailbooksell() reads this endpoint after choosing
the advisor. Its twelve columns populate both booking and selling teams,
including their four optional manager levels. A branch list's first row is
not an advisor's branch, even when the list was fetched live.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_models import BookingDefaults, DMSMasterRef

logger = logging.getLogger(__name__)
_PATH = "drfcbc/component/detailbooksell.php"


@dataclass(frozen=True)
class BookingOrganization:
    branch: DMSMasterRef
    team: DMSMasterRef
    form_fields: tuple[tuple[str, str], ...]


def _scalar(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise DMSClientError("DMS advisor organization malformed", "ERR_DMS_MASTER_UNAVAILABLE")
    return str(value).strip()


def parse_booking_org(body: str) -> BookingOrganization:
    """Parse the native response; incomplete organization never becomes a draft."""
    try:
        raw = json.loads(body)
    except (TypeError, ValueError) as exc:
        raise DMSClientError(
            "DMS advisor organization unavailable", "ERR_DMS_MASTER_UNAVAILABLE"
        ) from exc
    if not isinstance(raw, list) or len(raw) < 12:
        raise DMSClientError("DMS advisor organization malformed", "ERR_DMS_MASTER_UNAVAILABLE")
    values = [_scalar(value) for value in raw[:12]]
    for offset in range(0, 12, 2):
        rid, name = values[offset : offset + 2]
        # Branch/team are required by the native form. Manager levels may have
        # gaps, but a present manager must retain its matching display name.
        if rid in {"0", "null", "undefined"}:
            rid = values[offset] = ""
        if (offset < 4 and not rid) or bool(rid) != bool(name):
            raise DMSClientError("DMS advisor organization incomplete", "ERR_DMS_MASTER_UNMATCHED")

    fields = {}
    for side in ("book", "sell"):
        fields[f"branch_{side}val"] = values[0]
        fields[f"txtbranch_{side}"] = values[1]
        fields[f"team_{side}val"] = values[2]
        fields[f"txtteam_{side}"] = values[3]
        for level in range(2, 6):
            fields[f"usersposival{level}_{side}"] = values[level * 2]
            fields[f"txtusersposi{level}_{side}"] = values[level * 2 + 1]
    return BookingOrganization(
        branch=DMSMasterRef(id=values[0], code=values[0], name=values[1]),
        team=DMSMasterRef(id=values[2], code=values[2], name=values[3]),
        form_fields=tuple(fields.items()),
    )


def resolve_booking_org(client, advisor_id: str, defaults: BookingDefaults) -> BookingOrganization:
    """Read the selected advisor's current organization, with configured admin fallback.

    The fallback reads only this advisor in the same DMS endpoint. It does not
    change the salesperson session or elevate the booking write. No master-list
    cache is used, including when the advisor is resolved again in one session.
    """
    if not advisor_id:
        raise DMSClientError("booking advisor not pinned for operator", "ERR_DMS_ADVISOR_REQUIRED")
    try:
        org = parse_booking_org(client._post_text(_PATH, {"idusers": advisor_id}))
    except DMSClientError:
        resolve_admin = getattr(client, "_resolve_admin_transport", None)
        admin = resolve_admin() if resolve_admin else None
        if admin is None:
            raise
        # A separate reader prevents principal switches from sharing client memo
        # state. The transport is still the adapter's authenticated browser API.
        from services.erp.mrerp_dms_client import DMSClient

        reader = DMSClient(admin, client.base_url)
        org = parse_booking_org(reader._post_text(_PATH, {"idusers": advisor_id}))
    if (defaults.branch_id and defaults.branch_id != org.branch.id) or (
        defaults.team_id and defaults.team_id != org.team.id
    ):
        logger.warning("[dms] booking organization defaults differ from live advisor assignment")
    return org
