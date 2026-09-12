"""Persist the attempted booking number before the external write boundary."""

import secrets

from services.erp.dms_booking_errors import BOOKING_MAPPING_ERRORS
from services.erp.mrerp_dms_client_base import DMSClientError
from services.line_dms import session_store, store

UNKNOWN = "ERR_DMS_BOOKING_OUTCOME_UNKNOWN"


def unknown_result(booking_no):
    return {
        "ok": False,
        "booking_no": str(booking_no or ""),
        "error_code": UNKNOWN,
        "error_friendly": BOOKING_MAPPING_ERRORS[UNKNOWN],
        "response_body": {"submitted": True, "retry_safe": False, "submission_status": "unknown"},
    }


def pending(tenant, line_user_id, payload):
    current = (store.get_session(tenant, line_user_id) or {}).get("payload") or {}
    marker = current.get("booking_attempt") or {}
    if marker and marker.get("nonce") == payload.get("nonce"):
        return unknown_result(marker.get("booking_no"))
    return None


def recorder(tenant, line_user_id, payload):
    """Each execution can mark once; only its duplicate rejection may advance the number."""
    owner = secrets.token_hex(16)
    previous_no = None

    def record(booking_no):
        nonlocal previous_no
        if not session_store.record_booking_attempt(
            tenant, line_user_id, payload.get("nonce"), str(booking_no), owner, previous_no
        ):
            raise DMSClientError(
                "booking draft was replaced or attempt already exists; not submitted",
                "ERR_DMS_BOOKING_ATTEMPT_BLOCKED",
            )
        previous_no = str(booking_no)

    return record


def clear_completed(tenant, line_user_id, payload):
    return session_store.clear_booking_attempt(tenant, line_user_id, payload.get("nonce"))


def message(result):
    text = BOOKING_MAPPING_ERRORS[UNKNOWN]["th"]
    number = str(result.get("booking_no") or "")
    return f"{text}\nเลขที่รายการ: {number}" if number else text


def review_message(session, fallback):
    marker = ((session or {}).get("payload") or {}).get("booking_attempt")
    return message(marker) if marker else fallback
