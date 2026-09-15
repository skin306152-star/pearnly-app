"""Customer review in the shared browser editor; saving never writes to DMS."""

from __future__ import annotations

import secrets

from services.erp.dms_customer_diff import diff_customer_fields
from services.erp.erp_dms_intake import recognize_lookup_mrerp_dms
from services.line_dms import approval_flow, booking_edit as editor, cards, draft, store
from services.line_dms._out import _send


def _review(user: dict, nonce: str):
    binding = editor._binding(user)
    session = store.get_session(binding["tenant_id"], binding["line_user_id"])
    if not store.verify_nonce(session, nonce, "reviewing"):
        raise editor.BookingEditError("dms_booking.expired", 409)
    payload = session["payload"]
    endpoint = editor.dms_id_ocr.resolve_dms_endpoint(str(user["id"]), payload.get("endpoint_id"))
    if not endpoint:
        raise editor.BookingEditError("dms_booking.no_endpoint", 409)
    return binding, payload, endpoint


def load(user: dict, nonce: str) -> dict:
    _, payload, endpoint = _review(user, nonce)
    customer = dict(payload.get("draft") or {})
    snapshot = editor._snapshot(
        endpoint, customer=customer, customer_id=payload.get("customer_id", "")
    )
    # Resolve the OCR title before filling any gaps from the old customer record.
    title = customer.get("prefix_name") or (payload.get("id_card") or {}).get("prefix_name")
    if title and not customer.get("prefix_id"):
        customer["prefix_id"] = draft._prefix_id(title, snapshot["prefixes"])
    merged = {**snapshot.get("resolved_customer", {}), **{k: v for k, v in customer.items() if v}}
    if title and not customer.get("prefix_id"):
        merged["prefix_id"] = ""
    return {
        "form": {"customer": merged},
        "masters": {"prefixes": editor._options(snapshot["prefixes"])},
        "geo": {k: editor._options(v) for k, v in snapshot["geo"].items()},
    }


def geo(user: dict, nonce: str, level: str, parent_id: str = "") -> list:
    _, _, endpoint = _review(user, nonce)
    if level not in {"provinces", "districts", "subdistricts", "zipcodes"}:
        raise editor.BookingEditError("dms_booking.invalid_geo")
    result = editor.geo_mrerp_dms(endpoint, level=level, parent_id=parent_id)
    if not result.get("ok"):
        raise editor.BookingEditError("dms_booking.geo_unavailable", 503)
    return editor._options(result.get("options") or [])


def _card(binding, payload, customer, lookup, snapshot, nonce, has_admin):
    summary = draft.build_summary(customer, {**snapshot["geo"], "selected": customer})
    incoming = {
        **(payload.get("id_card") or {}),
        **{k: customer[k] for k in ("people_id", "name", "birthday_be", "prefix_name")},
        "address": {
            **customer,
            "province": customer["province_name"],
            "district": customer["district_name"],
            "subdistrict": customer["subdistrict_name"],
        },
    }
    new = {
        k: v
        for k, v in payload.items()
        if k
        not in {
            "customer_id",
            "master_draft",
            "master_summary",
            "approval",
            "has_admin",
            "display_diffs",
        }
    }
    new.update(
        draft=customer,
        summary=summary,
        id_card=incoming,
        phone=customer["phone"],
        nonce=nonce,
        field_diffs=[],
        scenario=lookup["scenario"],
    )
    if lookup["scenario"] == "exact":
        current = lookup["match"]["current_fields"]
        diffs = diff_customer_fields(current, customer)
        # Explicit browser edits may clear optional address details; OCR blanks may not.
        for key in ("building", "floor", "room", "village", "moo", "soi", "road"):
            if current.get(key) and not customer.get(key):
                diffs.append({"field": key, "old": str(current[key]), "new": ""})
        new.update(
            customer_id=lookup["match"]["customer_id"], scenario="exact_diff", field_diffs=diffs
        )
        new["master_draft"], new["master_summary"] = draft.master_snapshot(current)
        if diffs:
            display = draft.display_diffs(
                diffs, {**snapshot["geo"], "prefixes": snapshot["prefixes"]}
            )
            # Caller supplies the current endpoint permission, never trusts browser input.
            card, approval = approval_flow.exact_diff_card(
                binding["tenant_id"], binding["user_id"], display, has_admin, nonce, summary
            )
            new.update(display_diffs=display, has_admin=has_admin, approval=approval)
        else:
            from services.line_dms import menu_flow

            card = (
                cards.same_customer_card
                if new.get("mode") == menu_flow.MODE_CUSTOMER
                else cards.booking_customer_card
            )(summary, nonce)
    elif lookup["scenario"] == "none":
        card = cards.new_customer_card(summary, nonce)
    else:
        new["candidates"] = lookup.get("candidates") or []
        card = cards.candidates_card(new["candidates"], nonce)
    return new, card


def save(user: dict, nonce: str, submitted: dict) -> str:
    binding, payload, endpoint = _review(user, nonce)
    customer = editor._customer(dict(submitted.get("customer") or {}))
    snapshot = editor._snapshot(endpoint, customer=customer)
    labels = editor._customer_master_labels(snapshot, customer)
    if labels is None:
        raise editor.BookingEditError("dms_booking.invalid_master")
    customer.update(labels)
    customer["tax_id"] = customer["people_id"]
    lookup = recognize_lookup_mrerp_dms(
        endpoint,
        people_id=customer["people_id"],
        name=customer["name"],
        ocr_address=customer,
        phone=customer["phone"],
    )
    if not lookup.get("ok"):
        raise editor.BookingEditError("dms_booking.master_unavailable", 503)
    new_nonce = secrets.token_hex(8)
    new, card = _card(
        binding, payload, customer, lookup, snapshot, new_nonce, draft.has_admin_creds(endpoint)
    )
    args = (binding["tenant_id"], binding["line_user_id"])
    if not store.replace_review_payload(*args, nonce, new, state="reviewing"):
        raise editor.BookingEditError("dms_booking.expired", 409)
    try:
        if not _send(binding["line_user_id"], card):
            raise RuntimeError("customer_preview_not_delivered")
    except Exception as exc:
        store.replace_review_payload(*args, new_nonce, payload, state="reviewing")
        raise editor.BookingEditError("dms_booking.preview_send_failed", 503) from exc
    return new_nonce
