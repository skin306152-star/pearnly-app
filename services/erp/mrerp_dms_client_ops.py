# -*- coding: utf-8 -*-
"""DMS 客户/订单业务操作(ensure/import/patch/push/fetch/resolve/search)mixin.

从 mrerp_dms_client.py 抽出 · 方法体一字未改(verbatim)· self.* 经 MRO 解析回 DMSClient。
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from services.erp.mrerp_dms_models import (
    BookingDefaults,
    DMSBookingPayload,
    DMSMasterRef,
    DMSPushResult,
    ThaiIdCardPayload,
)
from services.erp.mrerp_dms_xlsx import BookingImportRow, DMSBookingImportXlsxBuilder
from services.erp.mrerp_dms_client_base import DMSClientError, to_be_date


class DMSClientOpsMixin:
    def ensure_customer(self, card: ThaiIdCardPayload) -> str:
        existing = self.search_customer(card.people_id)
        if existing:
            return existing

        form_html = self._post_text("cus/form.php", {"status": "n"})
        data = self._parse_form_defaults(form_html)
        prefix_name = card.prefix_name or self._select_label(form_html, "selprefix", card.prefix_id)

        data.update(
            {
                "stsel": "n",
                "idsel": "",
                "txtcuscode": card.people_id,
                "selprefix": card.prefix_id,
                "txtcusname": card.full_name,
                "txttel": card.phone,
                "txtbirthday": card.birthday_be,
                "txtpeopleid": card.people_id,
                "txttaxid": card.people_id,
                "txtcreditday": "0",
            }
        )
        if prefix_name:
            data["txtprefix"] = prefix_name
        resolved_address = self._resolve_address_geo(card.address, form_html)
        self._apply_address_to_customer_form(data, resolved_address)
        resp = self.transport.post(self._url("cus/new.php"), data=data, timeout_ms=60000)
        if resp.status_code != 200 or resp.text.strip().startswith("err::"):
            raise DMSClientError(
                f"customer create failed: {resp.status_code} {resp.text[:300]!r}",
                "ERR_DMS_CUSTOMER_CREATE",
            )

        customer_id = self.search_customer(card.people_id)
        if not customer_id:
            raise DMSClientError(
                "customer create returned success but search could not find row",
                "ERR_DMS_CUSTOMER_CREATE",
            )
        return customer_id

    def import_booking_from_xlsx(
        self,
        *,
        template_bytes: bytes,
        booking: DMSBookingPayload,
        card: ThaiIdCardPayload,
        doc_date_serial: int,
        delivery_date_serial: int,
    ) -> str:
        xlsx = DMSBookingImportXlsxBuilder().build(
            template_bytes,
            BookingImportRow(
                booking_no=booking.booking_no,
                advisor_code=booking.advisor.code,
                advisor_name=booking.advisor.name,
                doc_date_serial=doc_date_serial,
                car_code=booking.car.code,
                paint_code=booking.paint.code,
                delivery_date_serial=delivery_date_serial,
                customer_first_name=card.first_name,
                customer_last_name=card.last_name,
            ),
        )

        self.transport.get(self._url("impcarbookcon/formupload.php"))
        upload = self.transport.post(
            self._url("impcarbookcon/component/uploadexcel.php"),
            files={
                "uploadfile": (
                    f"{booking.booking_no}.xlsx",
                    xlsx,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            timeout_ms=60000,
        )
        if upload.status_code != 200 or upload.text.strip().startswith("err::"):
            raise DMSClientError(f"booking upload failed: {upload.text[:300]!r}", "ERR_DMS_IMPORT")

        preview = self._post_text("impcarbookcon/formrdpc.php", {})
        if booking.booking_no not in preview:
            raise DMSClientError(
                "booking upload preview did not contain booking_no", "ERR_DMS_IMPORT"
            )

        # cbimportdata[]=2 selects ONLY data row 2 (our row); the template's
        # example rows 3-6 are not imported. Verify by reading back drfcbc.
        result = self.transport.post(
            self._url("impcarbookcon/component/importpc.php"),
            data={"cballimportdata[]": "1", "cbimportdata[]": "2"},
            timeout_ms=120000,
        )
        code = result.text.strip()
        if code == "sc::1":
            booking_id = self.search_booking(booking.booking_no)
            if not booking_id:
                raise DMSClientError(
                    "booking import returned success but search failed", "ERR_DMS_IMPORT"
                )
            return booking_id
        if code.startswith("ep::"):
            # ep::1 means DMS produced an error report — never treat as success.
            raise DMSClientError(
                "booking import produced DMS error report", "ERR_DMS_IMPORT_REPORT"
            )
        raise DMSClientError(f"booking import returned unexpected body: {code!r}", "ERR_DMS_IMPORT")

    def patch_booking_identity(
        self,
        *,
        booking_id: str,
        customer_id: str,
        booking: DMSBookingPayload,
        card: ThaiIdCardPayload,
    ) -> None:
        form_html = self._post_text("drfcbc/form.php", {"status": "e", "id": booking_id})
        data = self._parse_form_defaults(form_html)
        data.update(
            {
                "stsel": "e",
                "idsel": booking_id,
                "usersval": booking.advisor.id,
                "txtusers": booking.advisor.name,
                "txtuserstel": booking.advisor.extra[0] if booking.advisor.extra else ".",
                "placebookval": booking.place_book.id,
                "txtplacebook": booking.place_book.name,
                "cusval": customer_id,
                "txtcus": card.full_name,
                "prefixval": card.prefix_id,
                "txtprefix": card.prefix_name,
                "txtpeopleid": card.people_id,
                "txtbirthday": card.birthday_be,
                "txttel": card.phone,
                "carval": booking.car.id,
                "txtcar": booking.car.code,
                "carbrandval": self._extra(booking.car, 0),
                "txtcarbrand": self._extra(booking.car, 1),
                "typecarval": self._extra(booking.car, 2),
                "txttypecar": self._extra(booking.car, 3),
                "typecardescval": self._extra(booking.car, 4),
                "txttypecardesc": self._extra(booking.car, 5),
                "gradeval": self._extra(booking.car, 6),
                "txtgrade": self._extra(booking.car, 7),
                "cargearval": self._extra(booking.car, 8),
                "txtcargear": self._extra(booking.car, 9),
                "txtmanuyear": self._extra(booking.car, 10),
                "enginepowerval": self._extra(booking.car, 11),
                "txtenginepower": self._extra(booking.car, 12),
                "carpaintval": booking.paint.id,
                "txtcarpaint": booking.paint.code,
                "carpaintname": booking.paint.name,
                "txtprice": self._extra(booking.car, 13),
                "txtcardeliverydate": booking.delivery_date_be,
                "termsaleval": booking.term_sale.id,
                "txttermsale": booking.term_sale.name,
                "branch_bookval": booking.branch.id,
                "txtbranch_book": booking.branch.name,
                "team_bookval": booking.team.id,
                "txtteam_book": booking.team.name,
                "branch_sellval": booking.branch.id,
                "txtbranch_sell": booking.branch.name,
                "team_sellval": booking.team.id,
                "txtteam_sell": booking.team.name,
                "txtearnestmoney": "0.00",
                "regisbehalfval": booking.regis_behalf.id,
                "txtregisbehalf": booking.regis_behalf.name,
                "txtregisname": card.full_name,
            }
        )
        self._apply_address_to_booking_form(data, card.address)
        resp = self.transport.post(self._url("drfcbc/edit.php"), data=data, timeout_ms=120000)
        if resp.status_code != 200 or resp.text.strip().startswith("err::"):
            raise DMSClientError(
                f"booking patch failed: {resp.status_code} {resp.text[:300]!r}",
                "ERR_DMS_BOOKING_PATCH",
            )

    def push_id_card_booking(
        self,
        *,
        card: ThaiIdCardPayload,
        booking: DMSBookingPayload,
        template_bytes: bytes,
        doc_date_serial: int,
        delivery_date_serial: int,
    ) -> DMSPushResult:
        """Orchestrate the full flow. Assumes the transport is already
        authenticated (the adapter logged in via Playwright)."""
        customer_id = self.ensure_customer(card)
        booking_id = self.import_booking_from_xlsx(
            template_bytes=template_bytes,
            booking=booking,
            card=card,
            doc_date_serial=doc_date_serial,
            delivery_date_serial=delivery_date_serial,
        )
        self.patch_booking_identity(
            booking_id=booking_id,
            customer_id=customer_id,
            booking=booking,
            card=card,
        )
        return DMSPushResult(
            ok=True,
            customer_id=customer_id,
            booking_id=booking_id,
            booking_no=booking.booking_no,
            response_code="sc::1",
        )

    def download_booking_template(self) -> bytes:
        resp = self.transport.get(self._url("impcarbookcon/example.xlsx"), timeout_ms=60000)
        if resp.status_code != 200 or resp.content[:2] != b"PK":
            raise DMSClientError("DMS booking example.xlsx download failed", "ERR_DMS_TEMPLATE")
        return resp.content

    def fetch_masters(self) -> Dict[str, List[List[Any]]]:
        """Pull the dropdown lists the connect wizard needs. Best-effort:
        a missing/empty list comes back as []."""
        out: Dict[str, List[List[Any]]] = {}
        for key, elem, extra in (
            ("advisors", "txtusers", {}),
            ("cars", "txtcar", {}),
            ("place_books", "txtplacebook", {}),
            ("term_sales", "txttermsale", {}),
            ("branches", "txtbranch_book", {}),
            ("regis_behalfs", "txtregisbehalf", {}),
        ):
            try:
                out[key] = self._bshsd(elem, **extra)
            except Exception:
                out[key] = []
        return out

    def resolve_booking_payload(
        self, defaults: BookingDefaults, card: ThaiIdCardPayload, *, today: Optional[date] = None
    ) -> DMSBookingPayload:
        """Build a DMSBookingPayload from endpoint defaults, resolving any
        master ref the user did not pin from live DMS master data."""
        today = today or date.today()
        delivery = today + timedelta(days=defaults.delivery_days)

        advisor = self._ref_from_default(
            "txtusers", defaults.advisor_id, defaults.advisor_code, defaults.advisor_name
        )
        car = self._ref_from_default("txtcar", defaults.car_id, defaults.car_code, "")
        paint = self._ref_from_default(
            "txtcarpaint", defaults.paint_id, defaults.paint_code, "", idcar=car.id
        )
        place = self._ref_from_default("txtplacebook", defaults.place_book_id, "", "")
        term = self._ref_from_default("txttermsale", defaults.term_sale_id, "", "")
        branch = self._ref_from_default("txtbranch_book", defaults.branch_id, "", "")
        team = self._ref_from_default(
            "txtteam_book", defaults.team_id, "", "", branch_book=branch.id
        )
        regis = self._ref_from_default("txtregisbehalf", defaults.regis_behalf_id, "", "")

        booking_no = f"{defaults.booking_prefix}{card.people_id[-6:]}{today.strftime('%m%d')}"
        return DMSBookingPayload(
            booking_no=booking_no,
            doc_date_be=to_be_date(today),
            delivery_date_be=to_be_date(delivery),
            advisor=advisor,
            car=car,
            paint=paint,
            place_book=place,
            term_sale=term,
            branch=branch,
            team=team,
            regis_behalf=regis,
        )

    def search_customer(self, text: str) -> Optional[str]:
        body = self._post_text(
            "cus/component/showdata.php",
            {
                "sdtamt": "10",
                "sdtpage": "1",
                "sd": text,
                "selcolsort": "1",
                "selcolsorttype": "1",
            },
        )
        return self._first_data_val(body)

    def search_booking(self, booking_no: str) -> Optional[str]:
        body = self._post_text(
            "drfcbc/component/showdata.php",
            {
                "sdtamt": "10",
                "sdtpage": "1",
                "sd": booking_no,
                "ftd": "1",
                "selcolsort": "1",
                "selcolsorttype": "1",
            },
        )
        return self._first_data_val(body)

    def _ref_from_default(
        self, elemname: str, pinned_id: str, pinned_code: str, pinned_name: str, **extra
    ) -> DMSMasterRef:
        """Resolve a master ref: if the user pinned an id, fetch that exact
        row; else take the first available row from live master data."""
        rows = self._bshsd(elemname, **extra)
        chosen = None
        if pinned_id:
            for row in rows:
                if str(row[0]) == str(pinned_id):
                    chosen = row
                    break
        if chosen is None and rows:
            chosen = rows[0]
        if chosen is None:
            # No live rows and no pin — fall back to the pinned scalars so the
            # caller still gets a usable (if unverified) ref.
            return DMSMasterRef(id=pinned_id, code=pinned_code, name=pinned_name)
        return DMSMasterRef(
            id=str(chosen[0]),
            code=str(chosen[1]) if len(chosen) > 1 else str(chosen[0]),
            name=str(chosen[2]) if len(chosen) > 2 else (str(chosen[1]) if len(chosen) > 1 else ""),
            extra=tuple(chosen[3:]),
        )

    def _bshsd(self, elemname: str, **extra) -> List[List[Any]]:
        data = {"bshsdamt": "10", "bshsdcurrpage": "1", "elemname": elemname, "sdt": ""}
        data.update({k: str(v) for k, v in extra.items()})
        text = self._post_text("drfcbc/component/bshsd.php", data)
        try:
            return json.loads(text) if text.strip() else []
        except (ValueError, json.JSONDecodeError):
            return []
