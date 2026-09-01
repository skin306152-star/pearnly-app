"""Localized labels for system-owned LINE invoice fields and enum values."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "static" / "line-intake-review" / "system-fields.json"
)
_LANGUAGES = ("th", "en", "zh", "ja")


@lru_cache(maxsize=1)
def _catalog() -> dict:
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def _lang(lang: str) -> str:
    return lang if lang in _LANGUAGES else "th"


def _localized(row: dict | None, lang: str) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get(_lang(lang)) or row.get("en") or row.get("th") or "")


def _field(key: str) -> str:
    aliases = _catalog().get("label_aliases") or {}
    return str(aliases.get(key) or key)


def _value(value) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def field_label(lang: str, key: str) -> str:
    row = (_catalog().get("labels") or {}).get(_field(key))
    return (
        _localized(row, lang)
        or {
            "th": "ข้อมูลเพิ่มเติม",
            "en": "Additional information",
            "zh": "附加信息",
            "ja": "追加情報",
        }[_lang(lang)]
    )


def field_value(lang: str, key: str, value) -> str:
    raw = str(value or "").strip()
    enum_key = _field(key)
    table = (_catalog().get("enums") or {}).get(enum_key)
    if not isinstance(table, dict) or not raw:
        return raw
    canonical = _value(raw)
    aliases = (_catalog().get("enum_aliases") or {}).get(enum_key) or {}
    canonical = str(aliases.get(canonical) or canonical)
    translated = _localized(table.get(canonical), lang)
    if translated:
        return translated
    return {
        "th": "ค่าระบบที่ไม่รู้จัก",
        "en": "Unrecognized system value",
        "zh": "未识别的系统值",
        "ja": "未認識のシステム値",
    }[_lang(lang)]


__all__ = ["field_label", "field_value"]
