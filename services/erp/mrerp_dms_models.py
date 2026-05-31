# -*- coding: utf-8 -*-
"""
services/erp/mrerp_dms_models.py

Dataclasses for the MR.ERP DMS (car-sales) adapter — Thai ID card intake →
DMS customer + booking draft.

Lineage:
    Ported from the lab adapter
    D:\\pearnly-dms-adapter-lab\\src\\dms_adapter\\models.py and extended with
    a BookingDefaults config holder so the route layer can pass the
    endpoint.config booking-default fields without a positional explosion.

These types carry NO transport / Playwright dependency — they are plain data,
unit-testable in isolation. The adapter (mrerp_dms_adapter.py) and the
transport-agnostic client (mrerp_dms_client.py) consume them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ThaiAddress:
    """Normalized Thai address resolved to DMS master ids.

    The *_id fields are DMS province/district/subdistrict/zipcode ids; the
    *_name fields are the human labels DMS echoes back on the booking form.
    Empty ids mean "could not map" — the adapter must NOT auto-push then.
    """

    house_no: str = ""
    province_id: str = ""
    province_name: str = ""
    district_id: str = ""
    district_name: str = ""
    subdistrict_id: str = ""
    subdistrict_name: str = ""
    zipcode_id: str = ""
    zipcode: str = ""
    building: str = ""
    floor: str = ""
    room: str = ""
    village: str = ""
    moo: str = ""
    soi: str = ""
    road: str = ""


@dataclass(frozen=True)
class ThaiIdCardPayload:
    """Extracted Thai ID-card identity fields used to create the customer."""

    people_id: str
    first_name: str
    last_name: str
    birthday_be: str  # Buddhist-era dd/mm/yyyy, e.g. "01/01/2530"
    address: ThaiAddress = field(default_factory=ThaiAddress)
    prefix_id: str = "17"
    prefix_name: str = ""
    phone: str = "0800000000"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass(frozen=True)
class DMSMasterRef:
    """One DMS master-data row (advisor / car / paint / branch / ...).

    `extra` carries the trailing columns DMS returns for cars (brand id/name,
    type, grade, gear, year, engine power, price ...) which the booking patch
    needs to echo back verbatim.
    """

    id: str
    code: str
    name: str
    extra: tuple = ()


@dataclass(frozen=True)
class DMSBookingPayload:
    """Everything the booking draft (drfcbc) needs beyond the ID card."""

    booking_no: str
    doc_date_be: str
    delivery_date_be: str
    advisor: DMSMasterRef
    car: DMSMasterRef
    paint: DMSMasterRef
    place_book: DMSMasterRef
    term_sale: DMSMasterRef
    branch: DMSMasterRef
    team: DMSMasterRef
    regis_behalf: DMSMasterRef


@dataclass
class DMSPushResult:
    """Return value of the adapter's one-call push.

    `ok` drives the erp_push_logs status (success/failed). evidence carries
    timing + any DMS response codes for the log's response_body.
    """

    ok: bool
    customer_id: Optional[str] = None
    booking_id: Optional[str] = None
    booking_no: Optional[str] = None
    response_code: Optional[str] = None
    error_code: Optional[str] = None  # ERR_* taxonomy for the UI
    error: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_response_body(self) -> Dict[str, Any]:
        """Shape stored in erp_push_logs.response_body so external_ref.py's
        _derive_mrerp_dms can lift booking_no → external_doc_no."""
        return {
            "adapter": "mrerp_dms",
            "booking_no": self.booking_no or "",
            "booking_id": self.booking_id or "",
            "customer_id": self.customer_id or "",
            "response_code": self.response_code or "",
            "error_code": self.error_code or "",
        }


@dataclass(frozen=True)
class BookingDefaults:
    """Per-endpoint booking defaults (from endpoint.config.booking_defaults).

    Stored as DMS master ids/codes picked once in the connect wizard. The
    adapter resolves any missing id from live master data at push time.
    """

    advisor_id: str = ""
    advisor_code: str = ""
    advisor_name: str = ""
    car_id: str = ""
    car_code: str = ""
    paint_id: str = ""
    paint_code: str = ""
    place_book_id: str = ""
    term_sale_id: str = ""
    branch_id: str = ""
    team_id: str = ""
    regis_behalf_id: str = ""
    booking_prefix: str = "PN"
    delivery_days: int = 15

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "BookingDefaults":
        d = dict((config or {}).get("booking_defaults") or {})
        try:
            days = int(d.get("delivery_days") or 15)
        except (TypeError, ValueError):
            days = 15
        return cls(
            advisor_id=str(d.get("advisor_id") or "").strip(),
            advisor_code=str(d.get("advisor_code") or "").strip(),
            advisor_name=str(d.get("advisor_name") or "").strip(),
            car_id=str(d.get("car_id") or "").strip(),
            car_code=str(d.get("car_code") or "").strip(),
            paint_id=str(d.get("paint_id") or "").strip(),
            paint_code=str(d.get("paint_code") or "").strip(),
            place_book_id=str(d.get("place_book_id") or "").strip(),
            term_sale_id=str(d.get("term_sale_id") or "").strip(),
            branch_id=str(d.get("branch_id") or "").strip(),
            team_id=str(d.get("team_id") or "").strip(),
            regis_behalf_id=str(d.get("regis_behalf_id") or "").strip(),
            booking_prefix=str(d.get("booking_prefix") or "PN").strip() or "PN",
            delivery_days=days,
        )
