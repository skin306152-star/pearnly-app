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
        matches = [value for value, label in options if self._norm_geo(label) == target]
        return matches[0] if len(set(matches)) == 1 else ""

    def _resolve_address_geo(self, address, form_html: str):
        """Prefill only exact, unambiguous matches from the current native cascade.

        Unmatched OCR text leaves that level and its descendants unselected so
        the user can correct them. It must never choose the form default or an
        unrelated first option just to make the native save accept the record.
        """
        prov = re.search(
            r'<select[^>]+name="selprovinces"[^>]*>(.*?)</select>', form_html, re.S | re.I
        )
        if not prov:
            raise DMSClientError("DMS province options unavailable", "ERR_DMS_MASTER_UNAVAILABLE")
        resolved = replace(
            address, province_id="", district_id="", subdistrict_id="", zipcode_id=""
        )
        provinces = self._parse_options(prov.group(1))
        province_id = self._match_geo(provinces, address.province_name)
        if not province_id:
            return resolved
        resolved = replace(resolved, province_id=province_id)
        districts = self._fetch_options(
            "cus/component/listdistricts.php", {"selprovinces": province_id}
        )
        district_id = self._match_geo(districts, address.district_name)
        if not district_id:
            return resolved
        resolved = replace(resolved, district_id=district_id)
        subdistricts = self._fetch_options(
            "cus/component/listsubdistricts.php", {"seldistricts": district_id}
        )
        subdistrict_id = self._match_geo(subdistricts, address.subdistrict_name)
        if not subdistrict_id:
            return resolved
        resolved = replace(resolved, subdistrict_id=subdistrict_id)
        zipcodes = self._fetch_options(
            "cus/component/listzipcodes.php", {"selsubdistricts": subdistrict_id}
        )
        zipcode_id = self._match_geo(zipcodes, address.zipcode)
        # 泰国身份证正面常不印邮编。当前街道若在 DMS 只对应一个邮编，可确定性补齐；
        # 多个候选仍保持空白，留给用户选择，绝不猜第一项。
        if not zipcode_id:
            unique_ids = {str(row[0]) for row in zipcodes if row and row[0] is not None}
            zipcode_id = next(iter(unique_ids)) if len(unique_ids) == 1 else ""
        return replace(resolved, zipcode_id=zipcode_id)

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
