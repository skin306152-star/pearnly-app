# -*- coding: utf-8 -*-
"""Load and save the browser editor for a pending LINE DMS booking."""

from __future__ import annotations

import secrets
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable

from services.erp import dms_id_ocr
from services.erp.erp_dms_intake import _run_logged_in, geo_mrerp_dms
from services.erp.dms_id_validate import is_valid_thai_id, normalize_thai_id
from services.erp.dms_masters_cache import get_masters, get_paints
from services.line_dms import qa_cards, store
from services.line_dms._out import _send
from services.line_dms.qa_util import (
    CHANNEL_EXTRA_SHAPE,
    car_label,
    find_row,
    parse_amount,
    row_name,
)

MASTER_FIELDS = {
    "place": "place_books",
    "car": "cars",
    "term": "term_sales",
    "regis": "regis_behalfs",
}
CUSTOMER_FIELDS = (
    "people_id",
    "prefix_id",
    "name",
    "birthday_be",
    "phone",
    "house_no",
    "building",
    "floor",
    "room",
    "village",
    "moo",
    "soi",
    "road",
    "province_id",
    "province_name",
    "district_id",
    "district_name",
    "subdistrict_id",
    "subdistrict_name",
    "zipcode_id",
    "zipcode",
)


class BookingEditError(ValueError):
    def __init__(self, code: str, status: int = 400):
        super().__init__(code)
        self.code = code
        self.status = status


def _binding(user: dict) -> dict:
    binding = store.get_binding_by_user(str(user.get("id") or ""))
    if not binding or str(binding.get("tenant_id")) != str(user.get("tenant_id")):
        raise BookingEditError("dms_booking.not_bound", 403)
    return binding


def _review(user: dict, nonce: str) -> tuple[dict, dict, dict]:
    binding = _binding(user)
    sess = store.get_session(binding["tenant_id"], binding["line_user_id"])
    if not store.verify_nonce(sess, nonce, "booking_review"):
        raise BookingEditError("dms_booking.expired", 409)
    payload = (sess or {}).get("payload") or {}
    qa = payload.get("qa") or {}
    endpoint = dms_id_ocr.resolve_dms_endpoint(str(user["id"]), qa.get("endpoint_id"))
    if not endpoint:
        raise BookingEditError("dms_booking.no_endpoint", 409)
    return binding, payload, endpoint


def _option(row: list, label=None) -> dict:
    return {"id": str(row[0]), "label": (label or row_name)(row)}


def _options(rows: Iterable[list], label=None) -> list[dict]:
    return [_option(row, label) for row in rows if row and row[0] is not None]


def _form(qa: dict) -> dict:
    draft = dict(qa.get("draft") or {})
    draft["name"] = str((qa.get("customer") or {}).get("name") or draft.get("name") or "")
    return {
        "customer": {key: str(draft.get(key) or "") for key in CUSTOMER_FIELDS},
        "answers": qa.get("answers") or {},
        "payments": qa.get("payments") or [],
        "files": {
            "id_card": bool((qa.get("files") or {}).get("id_card_mid")),
            "slip": bool((qa.get("files") or {}).get("slip_mid")),
        },
        "advisor": qa.get("advisor") or {},
    }


def load(user: dict, nonce: str) -> dict:
    _, payload, endpoint = _review(user, nonce)
    qa = payload.get("qa") or {}
    # 编辑页展示的是用户即将确认的主档,不能让 12 小时前的银行/车型快照继续占位。
    masters = get_masters(endpoint, force_refresh=True)
    prefix_rows = masters.get("prefixes") or []
    car_id = str(((qa.get("answers") or {}).get("car") or {}).get("id") or "")
    return {
        "form": _form(qa),
        "masters": {
            "places": _options(masters.get("place_books") or []),
            "cars": _options(masters.get("cars") or [], car_label),
            "paints": _options(get_paints(endpoint, car_id, masters)) if car_id else [],
            "terms": _options(masters.get("term_sales") or []),
            "regis": _options(masters.get("regis_behalfs") or []),
            "company_banks": _options(masters.get("company_banks") or []),
            "prefixes": _options(prefix_rows or []),
        },
    }


def paints(user: dict, nonce: str, car_id: str) -> list[dict]:
    _, _, endpoint = _review(user, nonce)
    # 颜色选项同 load:映射当前 DMS 主档,不拿 12h 快照(旧色会错配已下架车型)。
    masters = get_masters(endpoint, force_refresh=True)
    if find_row(masters.get("cars"), car_id) is None:
        raise BookingEditError("dms_booking.invalid_master")
    return _options(get_paints(endpoint, car_id, masters))


def geo(user: dict, nonce: str, level: str, parent_id: str = "") -> list[dict]:
    _, _, endpoint = _review(user, nonce)
    if level not in {"provinces", "districts", "subdistricts", "zipcodes"}:
        raise BookingEditError("dms_booking.invalid_geo")
    result = geo_mrerp_dms(endpoint, level=level, parent_id=parent_id)
    if not result.get("ok"):
        raise BookingEditError("dms_booking.geo_unavailable", 503)
    return _options(result.get("options") or [])


def _required(value: Any, code: str, limit: int = 160) -> str:
    text = str(value or "").strip()
    if not text or len(text) > limit:
        raise BookingEditError(code)
    return text


def _customer(raw: dict) -> dict:
    out = {key: str(raw.get(key) or "").strip() for key in CUSTOMER_FIELDS}
    out["people_id"] = normalize_thai_id(out["people_id"])
    if not is_valid_thai_id(out["people_id"]):
        raise BookingEditError("dms_booking.invalid_people_id")
    out["name"] = _required(out["name"], "dms_booking.invalid_name")
    out["phone"] = _required(out["phone"], "dms_booking.invalid_phone", 30)
    try:
        datetime.strptime(out["birthday_be"], "%d/%m/%Y")
    except ValueError as exc:
        raise BookingEditError("dms_booking.invalid_birthday") from exc
    for field in ("house_no", "province_id", "district_id", "subdistrict_id", "zipcode_id"):
        _required(out[field], f"dms_booking.invalid_{field}")
    return out


def _customer_master_labels(endpoint: dict, customer: dict) -> dict:
    def read(client, adapter):
        levels = (
            ("prefix_id", "prefix_name", client.list_prefixes()),
            ("province_id", "province_name", client.list_geo("provinces")),
            (
                "district_id",
                "district_name",
                client.list_geo("districts", customer["province_id"]),
            ),
            (
                "subdistrict_id",
                "subdistrict_name",
                client.list_geo("subdistricts", customer["district_id"]),
            ),
            (
                "zipcode_id",
                "zipcode",
                client.list_geo("zipcodes", customer["subdistrict_id"]),
            ),
        )
        labels = {}
        for id_field, name_field, rows in levels:
            row = find_row(rows, customer[id_field])
            if row is None:
                return None
            labels[name_field] = row_name(row)
        return labels

    result = _run_logged_in(endpoint, read)
    if isinstance(result, dict) and result.get("ok") is False:
        raise BookingEditError("dms_booking.geo_unavailable", 503)
    if result is None:
        raise BookingEditError("dms_booking.invalid_master")
    return result


def _pick(masters: dict, key: str, rid: Any) -> dict:
    row = find_row(masters.get(MASTER_FIELDS[key]) or [], str(rid or ""))
    if row is None:
        raise BookingEditError("dms_booking.invalid_master")
    label = car_label(row) if key == "car" else row_name(row)
    return {"id": str(row[0]), "label" if key == "car" else "name": label}


def _payments(rows: list, masters: dict) -> list[dict]:
    if not rows:
        raise BookingEditError("dms_booking.payment_required")
    banks = masters.get("company_banks") or []
    clean = []
    for item in rows[:12]:
        channel = str(item.get("channel") or "")
        if channel not in CHANNEL_EXTRA_SHAPE:
            raise BookingEditError("dms_booking.invalid_payment")
        amount = parse_amount(str(item.get("amount") or ""))
        if amount is None:
            raise BookingEditError("dms_booking.invalid_amount")
        extra = dict(item.get("extra") or {})
        if channel == "transfer":
            bank = find_row(banks, str(extra.get("dst_id") or ""))
            if bank is None:
                raise BookingEditError("dms_booking.invalid_bank")
            extra = {
                "src": str(extra.get("src") or "").strip(),
                "dst_id": str(bank[0]),
                "dst": row_name(bank),
            }
        elif CHANNEL_EXTRA_SHAPE[channel] in ("ref", "detail"):
            slot = "detail" if channel == "other" else "ref"
            extra = {slot: _required(extra.get(slot), "dms_booking.payment_detail_required")}
        else:
            extra = {}
        clean.append({"channel": channel, "amount": f"{Decimal(amount):.2f}", "extra": extra})
    return clean


def save(user: dict, nonce: str, submitted: dict) -> str:
    binding, payload, endpoint = _review(user, nonce)
    qa = dict(payload.get("qa") or {})
    # 保存校验按当前 DMS 主档判(称谓/地点/车型/条件/登记/银行都可能被 12h 快照带偏)。
    masters = get_masters(endpoint, force_refresh=True)
    customer = _customer(dict(submitted.get("customer") or {}))
    customer.update(_customer_master_labels(endpoint, customer))
    raw_answers = dict(submitted.get("answers") or {})
    car = _pick(masters, "car", raw_answers.get("car_id"))
    paint_rows = get_paints(endpoint, car["id"], masters)
    paint_row = find_row(paint_rows, str(raw_answers.get("paint_id") or ""))
    if paint_row is None:
        raise BookingEditError("dms_booking.invalid_master")
    delivery = _required(raw_answers.get("delivery_date_be"), "dms_booking.invalid_delivery")
    try:
        datetime.strptime(delivery, "%d/%m/%Y")
    except ValueError as exc:
        raise BookingEditError("dms_booking.invalid_delivery") from exc
    qa["draft"] = {**(qa.get("draft") or {}), **customer}
    qa["customer"] = {**(qa.get("customer") or {}), "name": customer["name"]}
    qa["summary"] = qa_cards._fallback_summary(qa)
    qa["customer_dirty"] = True
    qa["answers"] = {
        "place": _pick(masters, "place", raw_answers.get("place_id")),
        "car": car,
        "paint": {"id": str(paint_row[0]), "name": row_name(paint_row)},
        "delivery_date_be": delivery,
        "term": _pick(masters, "term", raw_answers.get("term_id")),
        "regis": _pick(masters, "regis", raw_answers.get("regis_id")),
        "regis_name": _required(raw_answers.get("regis_name"), "dms_booking.invalid_regis_name"),
    }
    qa["payments"] = _payments(list(submitted.get("payments") or []), masters)
    files = dict(qa.get("files") or {})
    keep = dict(submitted.get("keep_files") or {})
    if not keep.get("id_card", True):
        files["id_card_mid"] = None
    if not keep.get("slip", True):
        files["slip_mid"] = None
    if any(payment["channel"] == "transfer" for payment in qa["payments"]) and not files.get(
        "slip_mid"
    ):
        raise BookingEditError("dms_booking.slip_required")
    qa["files"] = files
    qa.setdefault("audit", []).append({"step": "browser_edit", "input": "saved"})
    new_nonce = secrets.token_hex(8)
    new_payload = {**payload, "qa": qa, "nonce": new_nonce}
    if not store.replace_review_payload(
        binding["tenant_id"], binding["line_user_id"], nonce, new_payload
    ):
        raise BookingEditError("dms_booking.expired", 409)
    try:
        _send(binding["line_user_id"], qa_cards.preview_card(qa, new_nonce))
    except Exception as exc:
        store.replace_review_payload(
            binding["tenant_id"], binding["line_user_id"], new_nonce, payload
        )
        raise BookingEditError("dms_booking.preview_send_failed", 503) from exc
    return new_nonce
