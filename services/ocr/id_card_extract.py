# -*- coding: utf-8 -*-
"""
services/ocr/id_card_extract.py

Thai national ID card → structured identity fields, for the MR.ERP DMS
car-sales intake flow (document_type = "thai_id_card").

Deliberately SEPARATE from the invoice OCR hot path: it reuses the shared
Layer-1 Vision text extraction and the Layer-2 Gemini transport, but with its
OWN prompt and its OWN output shape. The invoice _SYSTEM_PROMPT / ThaiInvoice
schema are never touched (CLAUDE.md/CLAUDE.md high-sensitivity OCR rule + the
DMS handoff doc: "do not force Thai ID cards through the invoice fields").

Public:
    extract_thai_id_card(image_bytes, api_key=None) -> dict
        {
          "id_card": { people_id, first_name, last_name, birthday_be,
                       prefix_name, address: {...} },
          "confidence": "high|medium|low",
          "needs_review": bool,
          "missing_fields": [str, ...],
          "raw": { ...the raw model JSON... }
        }
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from services.ocr import layer1_vision
from services.ocr.layer2_structure import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    _call_gemini_with_retry,
    _page_to_text,
)

logger = logging.getLogger(__name__)


class IdCardExtractError(RuntimeError):
    """OCR/extraction failed before any structured fields could be produced."""


_ID_CARD_PROMPT = (
    "You are reading a THAI NATIONAL ID CARD (บัตรประจำตัวประชาชน) from OCR text.\n"
    "Extract ONLY the cardholder identity fields. Return STRICT JSON, no prose, "
    "no markdown fences. Use EMPTY STRING for any field you cannot read.\n"
    "Schema:\n"
    "{\n"
    '  "people_id": "the 13-digit Thai citizen ID, digits only (strip spaces/dashes)",\n'
    '  "prefix": "Thai title e.g. นาย / นาง / นางสาว / เด็กชาย / เด็กหญิง, else empty",\n'
    '  "first_name_th": "given name in Thai",\n'
    '  "last_name_th": "family name in Thai",\n'
    '  "date_of_birth_be": "date of birth as dd/mm/yyyy in BUDDHIST ERA (พ.ศ.). '
    "If the card shows a Thai month name, convert to numeric month. If the year is "
    'Gregorian (ค.ศ.), add 543 to make it Buddhist era.",\n'
    '  "address_raw": "the full registered address line as printed",\n'
    '  "house_no": "house number (บ้านเลขที่)",\n'
    '  "moo": "village no (หมู่ที่) digits only, else empty",\n'
    '  "soi": "soi/alley, else empty",\n'
    '  "road": "road (ถนน), else empty",\n'
    '  "subdistrict": "tambon/khwaeng (ตำบล/แขวง) name without prefix word",\n'
    '  "district": "amphoe/khet (อำเภอ/เขต) name without prefix word",\n'
    '  "province": "province (จังหวัด) name without prefix word",\n'
    '  "zipcode": "5-digit postal code if present, else empty"\n'
    "}\n"
    "Do NOT invent a 13-digit number. If you are not sure it is exactly 13 digits, "
    "return an empty people_id."
)


def extract_thai_id_card(image_bytes: bytes, api_key: Optional[str] = None) -> Dict[str, Any]:
    if not image_bytes:
        raise IdCardExtractError("empty image bytes")

    # Layer 1: Google Vision OCR text (shared infra; no invoice coupling).
    l1 = layer1_vision.extract_from_image_bytes(image_bytes, page_number=1)
    if not l1.pages:
        raise IdCardExtractError("layer1 returned no pages")
    text = _page_to_text(l1.pages[0]) or ""
    if not text.strip():
        raise IdCardExtractError("layer1 produced no text from the image")

    # Layer 2: Gemini with the dedicated ID-card prompt (override → invoice
    # prompt/schema untouched).
    data, _meta = _call_gemini_with_retry(
        text,
        api_key=(api_key or "").strip() or None,
        model_name=DEFAULT_MODEL,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        system_prompt_override=_ID_CARD_PROMPT,
    )
    data = data if isinstance(data, dict) else {}
    return _normalize(data)


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    people_id = re.sub(r"\D", "", str(data.get("people_id") or ""))
    if len(people_id) != 13:
        people_id = ""  # never push a non-13-digit citizen id
    first_name = str(data.get("first_name_th") or data.get("first_name") or "").strip()
    last_name = str(data.get("last_name_th") or data.get("last_name") or "").strip()
    birthday_be = _normalize_be_date(str(data.get("date_of_birth_be") or "").strip())
    prefix_name = str(data.get("prefix") or "").strip()

    address = {
        "house_no": str(data.get("house_no") or "").strip(),
        "moo": str(data.get("moo") or "").strip(),
        "soi": str(data.get("soi") or "").strip(),
        "road": str(data.get("road") or "").strip(),
        "subdistrict": str(data.get("subdistrict") or "").strip(),
        "district": str(data.get("district") or "").strip(),
        "province": str(data.get("province") or "").strip(),
        "zipcode": str(data.get("zipcode") or "").strip(),
        "address_raw": str(data.get("address_raw") or "").strip(),
        # DMS master ids are NOT resolved in v1 — address text is written but
        # province/district/subdistrict ID mapping is future work.
        "province_id": "",
        "district_id": "",
        "subdistrict_id": "",
        "zipcode_id": "",
    }
    # If house_no missing, fall back to the raw line so DMS has something.
    if not address["house_no"] and address["address_raw"]:
        address["house_no"] = address["address_raw"][:120]

    missing = []
    if not people_id:
        missing.append("people_id")
    if not first_name:
        missing.append("first_name")
    if not last_name:
        missing.append("last_name")
    if not birthday_be:
        missing.append("birthday")

    # Blocking rule: citizen id (13) + first + last are required to push.
    needs_review = bool(missing and any(f in missing for f in ("people_id", "first_name", "last_name")))

    score = 4 - len(missing)
    confidence = "high" if score >= 4 else ("medium" if score >= 2 else "low")

    return {
        "id_card": {
            "people_id": people_id,
            "first_name": first_name,
            "last_name": last_name,
            "birthday_be": birthday_be,
            "prefix_name": prefix_name,
            "address": address,
        },
        "confidence": confidence,
        "needs_review": needs_review,
        "missing_fields": missing,
        "raw": data,
    }


def _normalize_be_date(s: str) -> str:
    """Best-effort normalize a dd/mm/yyyy date to BE. If the year looks
    Gregorian (< 2200), add 543. Returns '' if no parseable date."""
    if not s:
        return ""
    m = re.search(r"(\d{1,2})\D+(\d{1,2})\D+(\d{4})", s)
    if not m:
        return ""
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if year < 2200:  # Gregorian → Buddhist era
        year += 543
    return f"{day:02d}/{month:02d}/{year}"
