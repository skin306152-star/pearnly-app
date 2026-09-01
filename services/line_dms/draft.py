# -*- coding: utf-8 -*-
"""DMS LINE 对话流的取值模型(DL-3)· 纯函数,零副作用。

把身份证 OCR + DMS 查重结果(geo/prefixes)整成:
  · draft —— 写库字段值(与网页 dms-intake-core.js buildNewVals 同口径)。
  · summary —— 卡片复述用的可读五要素。
  · display_diffs —— 差异卡逐条「字段名: 旧 → 新」(地址 id 映成可读名,写入仍用原始 diff)。
从 flow.py 抽出(单一职责 + 控 flow 行数);flow 只做时序/状态,值映射集中在此。
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from services.erp.erp_dms_push import _dms_resolve_admin_creds
from services.line_dms import cards

_GEO_LISTS = {
    "province_id": "provinces",
    "district_id": "districts",
    "subdistrict_id": "subdistricts",
    "zipcode_id": "zipcodes",
}

_MASTER_DRAFT_KEYS = (
    "people_id",
    "prefix_id",
    "prefix_name",
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
)


def build_draft(id_card: dict, geo: dict, prefixes: List[list], phone: str) -> Dict[str, str]:
    """OCR 身份证 + 地址级联 → 写库字段值。称谓 OCR 优先,不命中时回退主档首项。"""
    addr = id_card.get("address") or {}
    sel = geo.get("selected") or {}
    txt = geo.get("text") or {}
    pn = id_card.get("prefix_name") or ""
    prefix = next(
        (opt for opt in prefixes or [] if opt and len(opt) > 1 and opt[1] == pn),
        None,
    )
    if prefix is None:
        prefix = next((opt for opt in prefixes or [] if opt and opt[0] is not None), None)
    prefix_id = str(prefix[0]) if prefix else ""
    return {
        "prefix_id": prefix_id,
        "name": id_card.get("name") or "",
        "people_id": id_card.get("people_id") or "",
        "tax_id": id_card.get("people_id") or "",
        "birthday_be": id_card.get("birthday_be") or "",
        "phone": phone or "",
        "house_no": txt.get("house_no") or addr.get("house_no") or "",
        "moo": txt.get("moo") or addr.get("moo") or "",
        "soi": txt.get("soi") or addr.get("soi") or "",
        "road": txt.get("road") or addr.get("road") or "",
        "province_id": sel.get("province_id") or "",
        "district_id": sel.get("district_id") or "",
        "subdistrict_id": sel.get("subdistrict_id") or "",
        "zipcode_id": sel.get("zipcode_id") or "",
        # 预览卡读 draft.zipcode 显示;zipcode_id 是主档 ID,label 单独解析。
        "zipcode": geo_name(geo, "zipcode_id", sel.get("zipcode_id") or ""),
    }


def geo_name(geo: dict, field: str, value: str) -> str:
    """把地址 id 映成可读名(在对应级联选项里查);非地址字段/查不到 → 原值。"""
    key = _GEO_LISTS.get(field)
    if not key or not value:
        return value or ""
    for opt in geo.get(key) or []:
        if opt and str(opt[0]) == str(value):
            return opt[1]
    return value


def build_summary(draft: Dict[str, str], geo: dict) -> Dict[str, str]:
    """新建卡复述的五要素(证号/姓名/生日/地址/电话);地址拼成一行可读串。"""
    bits: List[str] = []
    if draft.get("house_no"):
        bits.append(draft["house_no"])
    if draft.get("moo"):
        bits.append("หมู่ " + draft["moo"])
    if draft.get("soi"):
        bits.append("ซ." + draft["soi"])
    if draft.get("road"):
        bits.append("ถ." + draft["road"])
    for field, pfx in (("subdistrict_id", "ต."), ("district_id", "อ."), ("province_id", "จ.")):
        name = geo_name(geo, field, draft.get(field, ""))
        if name:
            bits.append(pfx + name)
    zc = geo_name(geo, "zipcode_id", draft.get("zipcode_id", ""))
    if zc:
        bits.append(zc)
    return {
        "people_id": draft.get("people_id", ""),
        "name": draft.get("name", ""),
        "birthday_be": draft.get("birthday_be", ""),
        "address": " ".join(bits),
        "zipcode": zc,
        "phone": draft.get("phone", ""),
    }


def master_snapshot(fields: dict) -> Tuple[Dict[str, str], Dict[str, str]]:
    """保留 DMS 旧资料时，生成订车逐问使用的主档快照。"""
    current = {key: str(fields.get(key) or "") for key in _MASTER_DRAFT_KEYS}
    current["zipcode"] = str(fields.get("zipcode_name") or fields.get("zipcode") or "")
    bits = [
        current.get("house_no"),
        f"หมู่ {current['moo']}" if current.get("moo") else "",
        f"ซ.{current['soi']}" if current.get("soi") else "",
        f"ถ.{current['road']}" if current.get("road") else "",
        f"ต.{current['subdistrict_name']}" if current.get("subdistrict_name") else "",
        f"อ.{current['district_name']}" if current.get("district_name") else "",
        f"จ.{current['province_name']}" if current.get("province_name") else "",
        current.get("zipcode"),
    ]
    summary = {
        "people_id": current.get("people_id", ""),
        "name": current.get("name", ""),
        "birthday_be": current.get("birthday_be", ""),
        "address": " ".join(part for part in bits if part),
        "zipcode": current.get("zipcode", ""),
        "phone": current.get("phone", ""),
    }
    return current, summary


def display_diffs(field_diffs: List[dict], geo: dict) -> List[Dict[str, str]]:
    """差异卡逐条:地址 id 值映成可读名(写入仍用原始 diff.new)。"""
    rows: List[Dict[str, str]] = []
    for d in field_diffs:
        f = d.get("field", "")
        rows.append(
            {
                "label": cards.FIELD_LABELS_TH.get(f, f),
                "old": geo_name(geo, f, d.get("old", "")),
                "new": geo_name(geo, f, d.get("new", "")),
            }
        )
    return rows


def has_admin_creds(ep: dict) -> bool:
    """端点是否配了 admin 凭据组(决定差异卡给不给 [อัปเดตข้อมูล])。"""
    cfg = (ep or {}).get("config") or {}
    pu, pp, eu, ep_ = _dms_resolve_admin_creds(cfg)
    return bool((pu and pp) or (eu and ep_))
