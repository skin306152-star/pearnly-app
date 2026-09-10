# -*- coding: utf-8 -*-
"""DMS 订车单的客户主档选择与快照。"""

from __future__ import annotations

from typing import Any

from services.erp.dms_id_validate import normalize_thai_id
from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_models import ThaiAddress, ThaiIdCardPayload


def card_from_customer(client: Any, *, customer_id: str, people_id: str) -> ThaiIdCardPayload:
    """在当前订车账号中直读已选客户，核验完整证号后使用实时主档。"""
    expected = normalize_thai_id(people_id)
    if not str(customer_id or "").strip() or not expected:
        raise DMSClientError("booking customer identity missing", "ERR_DMS_CUSTOMER_LOOKUP")
    fields = client.read_customer(str(customer_id))
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
    if not all(required):
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
