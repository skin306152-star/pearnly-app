"""Apply one server-validated LINE account choice to an in-memory ERP endpoint."""

from __future__ import annotations

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


__all__ = ["endpoint_with_account_choice"]
