"""Submit a booking once and verify its exact persisted form before reporting success."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation

from services.erp import mrerp_dms_docno
from services.erp.dms_id_validate import normalize_thai_id
from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_payments import _PAYMENT_MONEY_FIELD, _PAYMENT_TEXT_FIELD

_IDENTITY_FIELDS = ("txtdocno", "cusval", "txtpeopleid", "usersval", "carval", "carpaintval")
_BUSINESS_FIELDS = (
    "branch_bookval",
    "team_bookval",
    "branch_sellval",
    "team_sellval",
    "placebookval",
    "termsaleval",
    "regisbehalfval",
    "txtregisname",
    "txtcardeliverydate",
    "txtearnestmoney",
    "txtusers",
    "txtuserstel",
    "txtplacebook",
    "txtcus",
    "prefixval",
    "txtprefix",
    "txtbirthday",
    "txttel",
    "txtcar",
    "carbrandval",
    "txtcarbrand",
    "typecarval",
    "txttypecar",
    "typecardescval",
    "txttypecardesc",
    "gradeval",
    "txtgrade",
    "cargearval",
    "txtcargear",
    "txtmanuyear",
    "enginepowerval",
    "txtenginepower",
    "carpaintname",
    "txtcarpaint",
    "txtprice",
    "txttermsale",
    "txtbranch_book",
    "txtteam_book",
    "txtbranch_sell",
    "txtteam_sell",
    "txtregisbehalf",
    "txthousenum",
    "txtbuilding",
    "txtfloor",
    "txtroom",
    "txtvillage",
    "txtmoo",
    "txtsoi",
    "txtroad",
    "provincesval",
    "txtprovinces",
    "districtsval",
    "txtdistricts",
    "subdistrictsval",
    "txtsubdistricts",
    "zipcodesval",
    "txtzipcodes",
)
_MONEY_FIELDS = {"txtprice", "txtearnestmoney", *_PAYMENT_MONEY_FIELD.values()}
_PAYMENT_FIELDS = _MONEY_FIELDS | {
    field for channel in _PAYMENT_TEXT_FIELD.values() for field in channel.values()
}


class DMSBookingOutcomeUnknown(DMSClientError):
    """A write was attempted; callers must retain the draft and forbid a new POST."""

    def __init__(self, docno: str, *, http_status=None, body: str = ""):
        super().__init__(
            f"booking {docno!r} was submitted but its stored result could not be verified",
            "ERR_DMS_BOOKING_OUTCOME_UNKNOWN",
        )
        self.booking_no = docno
        self.response_body = {
            "booking_no": docno,
            "submission_status": "unknown",
            "submitted": True,
            "retry_safe": False,
            "http_status": http_status,
            # Keep evidence of the acknowledgement without persisting arbitrary HTML/PII.
            "response_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest() if body else "",
        }


def _same(field: str, expected: str, actual: str) -> bool:
    if field == "txtpeopleid":
        return bool(normalize_thai_id(expected)) and normalize_thai_id(
            expected
        ) == normalize_thai_id(actual)
    if field in _MONEY_FIELDS:
        try:
            return Decimal(expected.replace(",", "") or "0") == Decimal(
                actual.replace(",", "") or "0"
            )
        except InvalidOperation:
            return False
    return " ".join(expected.split()) == " ".join(actual.split())


def _matches(form: dict, submitted: dict, booking_id: str) -> bool:
    if str(form.get("idsel") or "") != booking_id:
        return False
    if not all(str(submitted.get(field) or "").strip() for field in _IDENTITY_FIELDS):
        return False
    fields = set(_IDENTITY_FIELDS + _BUSINESS_FIELDS) | _PAYMENT_FIELDS
    # Native advisor organization fields include all approval managers, not just branch/team.
    fields.update(key for key in submitted if "usersposi" in key.lower())
    return all(
        field in form and _same(field, str(submitted[field]), str(form[field]))
        for field in fields
        if field in submitted
    )


def _verify_session(client, docno: str, submitted: dict) -> str | None:
    # Native view initializes visibility filters in fresh DMS sessions. It performs no write.
    client._post_text("drfcbc/view.php", {"idmenu": "25", "menulv": "2"})
    body = client._post_text(
        "drfcbc/component/showdata.php",
        {
            "sdtamt": "30",
            "sdtpage": "1",
            "sd": docno,
            "ftd": "1",
            "selcolsort": "1",
            "selcolsorttype": "1",
        },
    )
    # DMS search is not exact: never accept the first row or another customer's booking.
    candidates = list(dict.fromkeys(re.findall(r'data-val=["\']([^"\']+)["\']', body or "")))[:30]
    matches = []
    for booking_id in candidates:
        form = client._parse_form_defaults(
            client._post_text("drfcbc/form.php", {"status": "e", "id": booking_id})
        )
        if _matches(form, submitted, booking_id):
            matches.append(booking_id)
    return matches[0] if len(matches) == 1 else None


def verify_created_booking(client, docno: str, submitted: dict) -> str | None:
    """Fresh salesperson read, then configured same-endpoint admin read of only this booking."""
    try:
        booking_id = _verify_session(client, docno, submitted)
        if booking_id:
            return booking_id
    except Exception:
        pass
    try:
        admin = client._resolve_admin_transport()
        if admin is not None:
            from services.erp.mrerp_dms_client import DMSClient

            # A new client prevents salesperson master memo entries leaking into the admin read.
            return _verify_session(DMSClient(admin, client.base_url), docno, submitted)
    except Exception:
        pass
    return None


def submit_booking(client, base: dict, docno: str, *, on_attempt=None) -> tuple[str, str]:
    """Only an explicit duplicate rejection permits another write attempt."""
    last_body = ""
    for _ in range(mrerp_dms_docno.BOOKING_DOCNO_MAX_TRIES):
        data = {**base, "txtdocno": docno}
        status = None
        if on_attempt is not None:
            # Persist the attempt before crossing the write boundary. A crash after POST
            # must not turn the next worker delivery into a second business document.
            on_attempt(docno)
        try:
            resp = client.transport.post(
                client._url("drfcbc/new.php"), data=data, timeout_ms=120000
            )
            status, last_body = resp.status_code, (resp.text or "").strip()
        except Exception:
            # A timeout/disconnect can happen after commit. Readback is safe; another POST is not.
            last_body = ""
        if status == 200 and last_body.startswith("err::"):
            if mrerp_dms_docno.is_duplicate_docno_error(last_body):
                docno = mrerp_dms_docno.bump_docno(docno)
                continue
            raise DMSClientError(f"booking create rejected: {last_body[:300]!r}", "ERR_DMS_IMPORT")
        booking_id = verify_created_booking(client, docno, data)
        if booking_id:
            return booking_id, docno
        raise DMSBookingOutcomeUnknown(docno, http_status=status, body=last_body)
    raise DMSClientError(f"booking create rejected: {last_body[:300]!r}", "ERR_DMS_IMPORT")
