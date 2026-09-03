"""商品名称呈现规则。"""

from __future__ import annotations

from collections.abc import Mapping

_FIELDS = ("name_th", "name_en", "name_zh")


def product_names(row: Mapping) -> list[str]:
    """主名称在前，追加其它已填写且不重复的名称。"""
    names: list[str] = []
    seen: set[str] = set()
    for field in _FIELDS:
        value = str(row.get(field) or "").strip()
        key = value.casefold()
        if value and key not in seen:
            names.append(value)
            seen.add(key)
    return names


def display_product_name(row: Mapping, *, missing: str = "") -> str:
    return " / ".join(product_names(row)) or missing


def product_name_object(row: Mapping) -> dict:
    return {
        "th": row.get("name_th"),
        "en": row.get("name_en"),
        "zh": row.get("name_zh"),
        "display": display_product_name(row),
    }
