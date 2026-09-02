"""Apply one server-validated LINE account choice to an in-memory ERP endpoint."""

from __future__ import annotations

import hashlib
import ntpath
from typing import Any

_MAPPING_KEYS = (
    "revenue_acc",
    "ar_acc",
    "vat_output_acc",
    "fallback_acc",
    "ap_acc",
    "vat_input_acc",
)


def _path_identity(value: object) -> str:
    path = str(value or "").strip()
    return ntpath.normcase(ntpath.normpath(path)) if path else ""


def account_reference(account_key: object) -> str:
    """Return a short opaque reference safe for LINE postback payloads."""
    raw = str(account_key or "").strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def find_account_choice(
    target: dict[str, Any],
    *,
    account_key: object = None,
    account_ref: object = None,
) -> dict[str, Any] | None:
    wanted_key = str(account_key or "").strip()
    wanted_ref = str(account_ref or "").strip()
    for row in target.get("account_choices") or []:
        if not isinstance(row, dict) or row.get("writable") is False:
            continue
        key = str(row.get("key") or row.get("account_set") or "").strip()
        if not key:
            continue
        if wanted_key and key == wanted_key:
            return row
        if wanted_ref and account_reference(key) == wanted_ref:
            return row
    return None


def target_label_for_account(target: dict[str, Any], account: dict[str, Any]) -> str:
    connection = str(
        target.get("connection_label")
        or ("MR.ERP" if str(target.get("adapter") or "").lower() == "mrerp" else "Express")
    ).strip()
    account_label = str(
        account.get("label") or account.get("account_company") or account.get("key") or ""
    ).strip()
    return " · ".join(value for value in (connection, account_label) if value)[:200]


def account_option_label(target: dict[str, Any], account: dict[str, Any]) -> str:
    """Put the distinguishing account name first so LINE's 20-char limit keeps it."""
    account_label = str(
        account.get("label") or account.get("account_company") or account.get("key") or ""
    ).strip()
    owner = str(target.get("workspace_name") or "").strip()
    return " · ".join(value for value in (account_label, owner) if value)


def endpoint_with_account_choice(
    endpoint: dict[str, Any], account_config: dict[str, Any] | None
) -> dict[str, Any]:
    choice = account_config if isinstance(account_config, dict) else {}
    if not choice:
        return endpoint
    projected = dict(endpoint)
    config = dict(endpoint.get("config") or {})
    previous_account = str(config.get("account_set") or config.get("account_dir") or "").strip()
    chosen_account = str(choice.get("account_set") or choice.get("account_dir") or "").strip()
    account_changed = bool(
        previous_account
        and chosen_account
        and _path_identity(previous_account) != _path_identity(chosen_account)
    )
    if account_changed:
        for key in (
            *_MAPPING_KEYS,
            "reported_accounts",
            "reported_products",
            "reported_customers",
            "reported_stock_acc_groups",
            "catalog_fingerprint",
        ):
            config.pop(key, None)
    for key in (
        "comidyear",
        "seldb",
        "account_set",
        "account_dir",
        "account_company",
        "account_set_row",
    ):
        value = choice.get(key)
        if value not in (None, ""):
            config[key] = value
    root = str(choice.get("root_key") or "").strip()
    if root:
        config["express_root"] = root
    mapping = choice.get("mapping") if isinstance(choice.get("mapping"), dict) else {}
    for key in _MAPPING_KEYS:
        value = str(mapping.get(key) or "").strip()
        if value:
            config[key] = value
    projected["config"] = config
    return projected


__all__ = [
    "account_option_label",
    "account_reference",
    "endpoint_with_account_choice",
    "find_account_choice",
    "target_label_for_account",
]
