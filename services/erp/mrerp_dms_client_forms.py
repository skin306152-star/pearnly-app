# -*- coding: utf-8 -*-
"""DMS 表单 POST/解析 + 地址地理主档级联 + HTML 微解析 mixin.

从 mrerp_dms_client.py 抽出 · 方法体一字未改(verbatim)· self.* 经 MRO 解析回 DMSClient。
"""

from __future__ import annotations

import html
import re
from dataclasses import replace
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from services.erp.mrerp_dms_models import (
    DMSMasterRef,
)
from services.erp.mrerp_dms_client_base import DMSClientError


class DMSClientFormsMixin:
    # Thai geo names in DMS master lists may carry administrative prefixes
    # though the id-card prompt asks for bare names; strip them so the
    # master-list lookup still lands on the right row.
    _GEO_PREFIXES = ("จังหวัด", "อำเภอ", "ตำบล", "แขวง", "เขต", "จ.", "อ.", "ต.")

    def _post_text(self, path: str, data: Dict[str, Any]) -> str:
        resp = self.transport.post(self._url(path), data=data)
        if resp.status_code != 200:
            raise DMSClientError(f"{path} http={resp.status_code}", "ERR_DMS_TECHNICAL")
        return resp.text

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path)

    def _parse_form_defaults(self, page: str) -> Dict[str, str]:
        data: Dict[str, str] = {}
        for match in re.finditer(r"<input\b([^>]*)>", page, re.I | re.S):
            attrs = match.group(1)
            name = self._attr(attrs, "name")
            if not name:
                continue
            input_type = (self._attr(attrs, "type") or "text").lower()
            if input_type in {"button", "file", "submit"}:
                continue
            if input_type in {"checkbox", "radio"} and "checked" not in attrs.lower():
                continue
            data[name] = self._attr(attrs, "value") or ""
        for match in re.finditer(r"<select\b([^>]*)>(.*?)</select>", page, re.I | re.S):
            name = self._attr(match.group(1), "name")
            if name:
                data[name] = self._selected_value(match.group(2))
        for match in re.finditer(r"<textarea\b([^>]*)>(.*?)</textarea>", page, re.I | re.S):
            name = self._attr(match.group(1), "name")
            if name:
                data[name] = re.sub(r"<.*?>", "", match.group(2))
        return data

    def _norm_geo(self, name: str) -> str:
        s = html.unescape(str(name or "")).strip()
        for prefix in self._GEO_PREFIXES:
            if s.startswith(prefix):
                return s[len(prefix) :].strip()
        return s

    def _parse_options(self, options_html: str) -> List[List[str]]:
        """[[value, label], ...] for a block of <option> tags, dropping the
        empty-value placeholder row."""
        out: List[List[str]] = []
        for attrs, label in re.findall(r"<option([^>]*)>(.*?)</option>", options_html, re.S | re.I):
            value = self._attr(attrs, "value")
            if not value:
                continue
            out.append([value, html.unescape(re.sub(r"<.*?>", "", label).strip())])
        return out

    def _match_geo(self, options: List[List[str]], name: str) -> str:
        target = self._norm_geo(name)
        if not target:
            return ""
        for value, label in options:
            if self._norm_geo(label) == target:
                return value
        return ""

    def _resolve_address_geo(self, address, form_html: str):
        """Resolve province/district/subdistrict/zipcode TEXT → DMS master ids
        via the customer form's cascade endpoints (listdistricts → … → zipcodes).

        cus/new.php rejects an empty geo select with a misleading "already used"
        error, so every level falls back to the list's first option (and the
        form's pre-selected province) when the OCR'd name finds no match — the
        customer is always created with a valid chain while the address TEXT
        fields still carry the real registered address."""
        prov = re.search(
            r'<select[^>]+name="selprovinces"[^>]*>(.*?)</select>', form_html, re.S | re.I
        )
        if not prov:
            return address
        provinces = self._parse_options(prov.group(1))
        default_province = self._selected_value(prov.group(1)) or (
            provinces[0][0] if provinces else ""
        )
        province_id = self._match_geo(provinces, address.province_name) or default_province
        if not province_id:
            return address

        districts = self._fetch_options(
            "cus/component/listdistricts.php", {"selprovinces": province_id}
        )
        district_id = self._match_geo(districts, address.district_name) or (
            districts[0][0] if districts else ""
        )
        subdistricts = self._fetch_options(
            "cus/component/listsubdistricts.php", {"seldistricts": district_id}
        )
        subdistrict_id = self._match_geo(subdistricts, address.subdistrict_name) or (
            subdistricts[0][0] if subdistricts else ""
        )
        zipcodes = self._fetch_options(
            "cus/component/listzipcodes.php", {"selsubdistricts": subdistrict_id}
        )
        zipcode_id = self._match_geo(zipcodes, address.zipcode) or (
            zipcodes[0][0] if zipcodes else ""
        )
        return replace(
            address,
            province_id=province_id,
            district_id=district_id,
            subdistrict_id=subdistrict_id,
            zipcode_id=zipcode_id,
        )

    def _fetch_options(self, path: str, body: Dict[str, str]) -> List[List[str]]:
        return self._parse_options(self._post_text(path, body))

    def _apply_address_to_booking_form(self, data: Dict[str, str], address) -> None:
        data.update(
            {
                "txthousenum": address.house_no,
                "txtbuilding": address.building,
                "txtfloor": address.floor,
                "txtroom": address.room,
                "txtvillage": address.village,
                "txtmoo": address.moo,
                "txtsoi": address.soi,
                "txtroad": address.road,
                "provincesval": address.province_id,
                "txtprovinces": address.province_name,
                "districtsval": address.district_id,
                "txtdistricts": address.district_name,
                "subdistrictsval": address.subdistrict_id,
                "txtsubdistricts": address.subdistrict_name,
                "zipcodesval": address.zipcode_id,
                "txtzipcodes": address.zipcode,
            }
        )

    def _first_data_val(self, html_text: str) -> Optional[str]:
        match = re.search(r'data-val="([^"]+)"', html_text)
        return match.group(1) if match else None

    def _selected_value(self, options_html: str) -> str:
        selected = re.search(
            r'<option[^>]*value="([^"]*)"[^>]*selected[^>]*>', options_html, re.I | re.S
        )
        first = re.search(r'<option[^>]*value="([^"]*)"', options_html, re.I | re.S)
        node = selected or first
        return node.group(1) if node else ""

    def _attr(self, attrs: str, name: str) -> Optional[str]:
        match = re.search(rf'{re.escape(name)}="([^"]*)"', attrs, re.I)
        return html.unescape(match.group(1)) if match else None

    def _extra(self, ref: DMSMasterRef, idx: int) -> str:
        return str(ref.extra[idx]) if len(ref.extra) > idx else ""
