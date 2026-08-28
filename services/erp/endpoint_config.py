# -*- coding: utf-8 -*-
"""ERP 端点配置的响应脱敏与 DMS 归一化。"""

from __future__ import annotations

from typing import Any, Dict


def strip_endpoint_for_response(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """隐藏令牌、Agent 哈希和加密凭据,只把已配置标记发给前端。"""
    out = dict(endpoint)
    config = dict(out.get("config") or {})
    config.pop("agent_token_hash", None)
    if config.get("token"):
        token = str(config["token"])
        config["token"] = (token[:4] + "***" + token[-4:]) if len(token) > 10 else "***"
        config["_token_set"] = True
    for sensitive in (
        "username_enc",
        "password_enc",
        "admin_username_enc",
        "admin_password_enc",
    ):
        if config.get(sensitive):
            config[sensitive] = "***"
            config[f"_{sensitive}_set"] = True
    out["config"] = config
    return out


def normalize_mrerp_dms_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """让老板端只保留一组有修改权限的凭据,并淘汰自定义订车单前缀。"""
    normalized = dict(config or {})
    booking_defaults = dict(normalized.get("booking_defaults") or {})
    booking_defaults.pop("booking_prefix", None)
    if booking_defaults:
        normalized["booking_defaults"] = booking_defaults
    else:
        normalized.pop("booking_defaults", None)

    admin_pair = (
        normalized.get("admin_username_enc"),
        normalized.get("admin_password_enc"),
    )
    primary_pair = (normalized.get("username_enc"), normalized.get("password_enc"))
    username, password = admin_pair if all(admin_pair) else primary_pair
    if username and password:
        normalized.update(
            {
                "username_enc": username,
                "password_enc": password,
                "admin_username_enc": username,
                "admin_password_enc": password,
            }
        )
    return normalized


__all__ = ["normalize_mrerp_dms_config", "strip_endpoint_for_response"]
