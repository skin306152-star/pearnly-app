# -*- coding: utf-8 -*-
"""
services/ocr/id_card_extract.py

Thai national ID card → structured identity fields, for the MR.ERP DMS
car-sales intake flow (document_type = "thai_id_card").

Deliberately SEPARATE from the invoice OCR hot path: it reuses the shared
ai_gateway transport (multimodal → JSON), but with its OWN prompt and its OWN
output shape. The invoice _SYSTEM_PROMPT / ThaiInvoice
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

from services.ocr.layer2_structure import DEFAULT_TIMEOUT_SECONDS

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
    """身份证图 → 结构化字段。直接走 Gemini 多模态视觉(图→JSON),与发票 OCR
    同一条 prod 可用路;不依赖 Google Vision(prod 未配 GOOGLE_APPLICATION_CREDENTIALS)。"""
    if not image_bytes:
        raise IdCardExtractError("empty image bytes")
    data = _gemini_vision_extract(image_bytes, (api_key or "").strip() or None)
    return _normalize(data if isinstance(data, dict) else {})


def _detect_image_mime(b: bytes) -> str:
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _gemini_vision_extract(image_bytes: bytes, api_key: Optional[str]) -> Dict[str, Any]:
    """多模态调用:身份证图 + 专用 prompt → JSON dict。便宜首读(flash_lite)读不出合规
    13 位身份证号时升级到 OCR_FALLBACK_MODEL(=3.5-flash·糊图/缺一位救场)再读一次。
    经 ai_gateway 网关(随 OCR_LLM_BACKEND 切 vertex/selfhost)。两档都不出号 → 抛
    IdCardExtractError(路由据此回 422 needs_review / 500)。"""
    import os

    key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise IdCardExtractError("no Gemini api key (GOOGLE_API_KEY / GEMINI_API_KEY)")
    from services.ai_gateway import transport
    from services.ocr.gemini_models import flash_lite, tier_for_model, try_with_fallback

    img = bytes(image_bytes)

    def _call(model_name: str):
        out = transport.multimodal_to_json(
            _ID_CARD_PROMPT,
            [(img, _detect_image_mime(img))],
            tier=tier_for_model(model_name),
            api_key=key.strip(),
            temperature=0.0,
            response_mime=True,
            max_tokens=16384,
            timeout_s=DEFAULT_TIMEOUT_SECONDS,
            max_retries=0,
            task="ocr.id_card",
        )
        return out.data if out.ok and isinstance(out.data, dict) else None

    # 身份证唯一刚需字段=13 位号;首读没读出合规号即升级(_normalize 也以 len==13 为采信门槛)。
    def _has_id(d) -> bool:
        return isinstance(d, dict) and len(re.sub(r"\D", "", str(d.get("people_id") or ""))) == 13

    data = try_with_fallback(_call, primary=flash_lite(), ok=_has_id, label="ocr.id_card")
    if data is None:
        raise IdCardExtractError("gemini vision call failed (no valid id, all models)")
    return data


def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
    people_id = re.sub(r"\D", "", str(data.get("people_id") or ""))
    if len(people_id) != 13:
        people_id = ""  # never push a non-13-digit citizen id
    first_name = str(data.get("first_name_th") or data.get("first_name") or "").strip()
    last_name = str(data.get("last_name_th") or data.get("last_name") or "").strip()
    birthday_be = _normalize_be_date(str(data.get("date_of_birth_be") or "").strip())
    prefix_name = _normalize_thai_prefix(str(data.get("prefix") or "").strip())

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
    needs_review = bool(
        missing and any(f in missing for f in ("people_id", "first_name", "last_name"))
    )

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


# 泰文称谓缩写 → 全称(身份证印缩写 น.ส.,但 DMS 称谓下拉是全称 นางสาว · 不归一会
# 匹配不到回落错值 → 称谓写不进/恒显差异)。点号/空格容错。
_THAI_PREFIX_ALIASES = {
    "น.ส.": "นางสาว",
    "นส.": "นางสาว",
    "นส": "นางสาว",
    "ด.ช.": "เด็กชาย",
    "ดช.": "เด็กชาย",
    "ด.ญ.": "เด็กหญิง",
    "ดญ.": "เด็กหญิง",
}


def _normalize_thai_prefix(s: str) -> str:
    """身份证称谓缩写归一为全称(与 DMS 称谓主档对齐)。非缩写原样返回。"""
    if not s:
        return ""
    key = s.replace(" ", "")
    return _THAI_PREFIX_ALIASES.get(key, s)


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
