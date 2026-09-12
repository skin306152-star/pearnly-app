# -*- coding: utf-8 -*-
"""DMS 订车单的客户主档选择与快照。"""

from __future__ import annotations

from typing import Any

from services.erp.dms_id_validate import normalize_thai_id
from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_models import ThaiAddress, ThaiIdCardPayload


def card_from_customer(client: Any, *, customer_id: str, people_id: str) -> ThaiIdCardPayload:
    """直读已选客户并核验完整证号;销售不可读时只读借用本端点管理员。"""
    expected = normalize_thai_id(people_id)
    if (
        not str(customer_id or "").strip()
        or len(expected) != 13
        or not expected.isascii()
        or not expected.isdigit()
    ):
        raise DMSClientError("booking customer identity missing", "ERR_DMS_CUSTOMER_LOOKUP")
    try:
        fields = client.read_customer(str(customer_id))
    except DMSClientError:
        fields = {}
    actual = normalize_thai_id(str((fields or {}).get("people_id") or ""))
    if actual and actual != expected:
        # A contradictory identity is not a visibility failure. Stop before
        # consulting another account, so no other customer's data can escape.
        raise DMSClientError("selected customer identity mismatch", "ERR_DMS_CUSTOMER_LOOKUP")
    try:
        return _card_from_fields(fields or {}, customer_id=customer_id, expected=expected)
    except DMSClientError:
        resolve_admin = getattr(client, "_resolve_admin_transport", None)
        admin = resolve_admin() if resolve_admin else None
        if admin is None:
            raise
        from services.erp.mrerp_dms_client import DMSClient

        # Same configured base URL, same exact customer ID; no broad search,
        # source switch, cached fields, or elevation of the booking writer.
        reader = DMSClient(admin, client.base_url)
        try:
            fields = reader.read_customer(str(customer_id))
        except DMSClientError as exc:
            raise DMSClientError(
                "configured admin could not read selected customer", "ERR_DMS_CUSTOMER_LOOKUP"
            ) from exc
        return _card_from_fields(fields, customer_id=customer_id, expected=expected)


def _card_from_fields(fields: dict, *, customer_id: str, expected: str) -> ThaiIdCardPayload:
    """Both principals must pass the same identity and completeness checks."""
    if normalize_thai_id(str(fields.get("people_id") or "")) != expected:
        raise DMSClientError(
            f"booking customer {customer_id!r} identity could not be verified",
            "ERR_DMS_CUSTOMER_LOOKUP",
        )

    address = ThaiAddress(
        house_no=str(fields.get("house_no") or ""),
        building=str(fields.get("building") or ""),
        floor=str(fields.get("floor") or ""),
        room=str(fields.get("room") or ""),
        village=str(fields.get("village") or ""),
        moo=str(fields.get("moo") or ""),
        soi=str(fields.get("soi") or ""),
        road=str(fields.get("road") or ""),
        province_id=str(fields.get("province_id") or ""),
        province_name=str(fields.get("province_name") or ""),
        district_id=str(fields.get("district_id") or ""),
        district_name=str(fields.get("district_name") or ""),
        subdistrict_id=str(fields.get("subdistrict_id") or ""),
        subdistrict_name=str(fields.get("subdistrict_name") or ""),
        zipcode_id=str(fields.get("zipcode_id") or ""),
        zipcode=str(fields.get("zipcode_name") or ""),
    )
    required = (
        fields.get("name"),
        fields.get("people_id"),
        fields.get("birthday_be"),
        fields.get("prefix_id"),
        fields.get("prefix_name"),
        fields.get("phone"),
        address.house_no,
        address.province_id,
        address.province_name,
        address.district_id,
        address.district_name,
        address.subdistrict_id,
        address.subdistrict_name,
        address.zipcode_id,
        address.zipcode,
    )
    if not all(str(value or "").strip() for value in required):
        raise DMSClientError(
            f"booking customer {customer_id!r} has incomplete master data",
            "ERR_DMS_CUSTOMER_LOOKUP",
        )

    return ThaiIdCardPayload(
        people_id=str(fields["people_id"]),
        first_name=str(fields["name"]),
        last_name="",
        birthday_be=str(fields["birthday_be"]),
        address=address,
        prefix_id=str(fields["prefix_id"]),
        prefix_name=str(fields.get("prefix_name") or ""),
        phone=str(fields["phone"]),
    )
