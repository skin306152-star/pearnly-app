# -*- coding: utf-8 -*-
"""Validate customer select values against the current native address cascade."""

import re

from services.erp.mrerp_dms_client_base import DMSClientError

_SELECTS = ("selprovinces", "seldistricts", "selsubdistricts", "selzipcodes")
_SUFFIXES = ("", "_ct", "_sd")
_CHILDREN = (
    ("cus/component/listdistricts.php", "selprovinces"),
    ("cus/component/listsubdistricts.php", "seldistricts"),
    ("cus/component/listzipcodes.php", "selsubdistricts"),
)


def clear_customer_select_defaults(data: dict) -> None:
    """A new customer must not inherit the new form's arbitrary address defaults."""
    for key in ("selprefix", *(field + suffix for suffix in _SUFFIXES for field in _SELECTS)):
        if key in data:
            data[key] = ""


def _require_member(value: str, rows: list, field: str) -> None:
    if not value:
        raise DMSClientError(
            f"customer {field} requires an explicit selection", "ERR_DMS_MASTER_UNMATCHED"
        )
    if not rows:
        raise DMSClientError(f"DMS {field} options unavailable", "ERR_DMS_MASTER_UNAVAILABLE")
    if not any(str(row[0]) == str(value) for row in rows):
        raise DMSClientError(
            f"customer {field} no longer belongs to the selected parent", "ERR_DMS_MASTER_UNMATCHED"
        )


def validate_customer_selects(client, data: dict, form_html: str) -> None:
    """No guessing: retain explicit IDs only when their live parent chain agrees."""
    prefix = str(data.get("selprefix") or "")
    prefixes = client._select_options(form_html, "selprefix")
    if prefix and not any(str(row[0]) == prefix for row in prefixes):
        # Some valid titles occur only in the native quick-customer form. Keep
        # the existing two-source contract, but never invent a missing title.
        prefixes = client.list_prefixes()
    _require_member(prefix, prefixes, "selprefix")

    # Shared parent chains are read once during this validation only. There is
    # no reuse across OCR, selections, users, saves, or DMS login sessions.
    fetched = {}
    for suffix in _SUFFIXES:
        provinces = client._select_options(form_html, "selprovinces" + suffix)
        if suffix and not re.search(rf'<select\b[^>]*name="selprovinces{suffix}"', form_html, re.I):
            continue  # This DMS form does not expose that optional address block.
        values = [str(data.get(field + suffix) or "") for field in _SELECTS]
        if suffix and not any(values):
            continue  # An unused optional address must stay empty.
        _require_member(values[0], provinces, "selprovinces" + suffix)
        for index, (path, parent_field) in enumerate(_CHILDREN, 1):
            parent_id = values[index - 1]
            key = (path, parent_id)
            if key not in fetched:
                fetched[key] = client._fetch_options(path, {parent_field: parent_id})
            _require_member(values[index], fetched[key], _SELECTS[index] + suffix)
