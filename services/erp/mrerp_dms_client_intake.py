# -*- coding: utf-8 -*-
"""DMS 客户交互层:查重 / 建改(用户编辑字段) / 地址级联 / 称谓主档。

支撑「身份证识别 → 可编辑面板 → 确认推送」两步流(dms_routes 新端点)。
方法走与 ops/forms 同一个 transport,self.* 经 MRO 解析回 DMSClient。

字段契约(前端面板 ↔ DMS 表单名):
    prefix_id→selprefix · name→txtcusname · people_id→txtpeopleid · tax_id→txttaxid
    birthday_be→txtbirthday · phone→txttel · 地址 house_no/moo/soi/road/province_id/
    district_id/subdistrict_id/zipcode_id → txthousenum/txtmoo/txtsoi/txtroad/
    selprovinces/seldistricts/selsubdistricts/selzipcodes(三段地址 ""/_ct/_sd 同值)

坑(实测 · 铁律#8/#9):
- 保存走 cus/new.php(建)/ cus/edit.php(改)· stsel + idsel 带上下文(同订车单 drfcbc)。
- 空的必填 select(称谓/邮编)会让服务端报误导性 "ข้อมูลถูกใช้งานในระบบ" → 保存前补全。
- PHP 200/无 err:: 不代表写库成功 → 建后 search 复核、改后重读姓名复核。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services.erp.mrerp_dms_client_base import DMSClientError

# 前端友好键 → DMS 客户表单字段名(非地址部分)
_IDENTITY_MAP = {
    "prefix_id": "selprefix",
    "name": "txtcusname",
    "people_id": "txtpeopleid",
    "tax_id": "txttaxid",
    "birthday_be": "txtbirthday",
    "phone": "txttel",
    "email": "txtemail",
    "line_id": "txtlineid",
    "credit_day": "txtcreditday",
}
# 地址友好键 → DMS 字段前缀(三段地址各加 ""/_ct/_sd 后缀)
_ADDR_MAP = {
    "house_no": "txthousenum",
    "building": "txtbuilding",
    "floor": "txtfloor",
    "room": "txtroom",
    "village": "txtvillage",
    "moo": "txtmoo",
    "soi": "txtsoi",
    "road": "txtroad",
    "province_id": "selprovinces",
    "district_id": "seldistricts",
    "subdistrict_id": "selsubdistricts",
    "zipcode_id": "selzipcodes",
}
_ADDR_SUFFIXES = ("", "_ct", "_sd")


class DMSClientIntakeMixin:
    # ── 读 ──────────────────────────────────────────────────────────
    def lookup_customer(self, people_id: str) -> Dict[str, Any]:
        """按身份证号查 DMS 客户。命中则回当前全字段(给面板「历史资料」)。"""
        cid = self.search_customer(people_id) if (people_id or "").strip() else None
        if not cid:
            return {"found": False, "customer_id": None, "fields": {}}
        html = self._post_text("cus/form.php", {"status": "e", "id": cid})
        return {
            "found": True,
            "customer_id": cid,
            "fields": self._extract_customer_fields(self._parse_form_defaults(html)),
        }

    def list_prefixes(self) -> List[List[str]]:
        html = self._post_text("cus/form.php", {"status": "n"})
        return self._select_options(html, "selprefix")

    def list_geo(self, level: str, parent_id: str = "") -> List[List[str]]:
        """四级联动选项:provinces 无 parent;其余按上一级 id 取。返回 [[id,label],...]。"""
        if level == "provinces":
            html = self._post_text("cus/form.php", {"status": "n"})
            return self._select_options(html, "selprovinces")
        endpoints = {
            "districts": ("cus/component/listdistricts.php", "selprovinces"),
            "subdistricts": ("cus/component/listsubdistricts.php", "seldistricts"),
            "zipcodes": ("cus/component/listzipcodes.php", "selsubdistricts"),
        }
        if level not in endpoints or not parent_id:
            return []
        path, key = endpoints[level]
        return self._fetch_options(path, {key: parent_id})

    # ── 写 ──────────────────────────────────────────────────────────
    def save_customer(
        self, *, fields: Dict[str, Any], mode: str, customer_id: Optional[str] = None
    ) -> str:
        """建(mode='create')或覆盖(mode='overwrite')客户。返回 customer_id。
        覆盖:载现表单 → 合并面板字段(非身份证字段原样保留)→ 提交。"""
        if mode not in ("create", "overwrite"):
            raise DMSClientError(f"bad save mode: {mode!r}", "ERR_DMS_CUSTOMER_SAVE")
        # 幂等:一个身份证 = DMS 一个客户(编号/身份证号唯一)。create 前先按身份证号查,
        # 已存在则转更新它 —— 修「撞客户编号重复」+ 自愈「建了客户但订车失败」后的重推。
        if mode == "create":
            existing = self.search_customer((fields.get("people_id") or "").strip())
            if existing:
                mode, customer_id = "overwrite", existing
        if mode == "overwrite" and not customer_id:
            raise DMSClientError("overwrite needs customer_id", "ERR_DMS_CUSTOMER_SAVE")

        form_args = {"status": "n"} if mode == "create" else {"status": "e", "id": customer_id}
        form_html = self._post_text("cus/form.php", form_args)
        data = self._parse_form_defaults(form_html)
        data["stsel"] = "n" if mode == "create" else "e"
        if mode == "overwrite":
            data["idsel"] = customer_id
        if mode == "create" and not (fields.get("people_id") and data.get("txtcuscode")):
            data["txtcuscode"] = fields.get("people_id") or data.get("txtcuscode") or ""

        self._apply_customer_fields(data, fields)
        self._guard_required_selects(data, form_html)

        endpoint = "cus/new.php" if mode == "create" else "cus/edit.php"
        resp = self.transport.post(self._url(endpoint), data=data, timeout_ms=60000)
        body = (resp.text or "").strip()
        if resp.status_code != 200 or body.startswith("err::"):
            raise DMSClientError(
                f"customer {mode} failed: {resp.status_code} {body[:200]!r}",
                "ERR_DMS_CUSTOMER_SAVE",
            )
        return self._verify_saved(mode, fields, customer_id)

    # ── 内部 ────────────────────────────────────────────────────────
    def _extract_customer_fields(self, data: Dict[str, str]) -> Dict[str, str]:
        out = {fk: data.get(dms, "") for fk, dms in _IDENTITY_MAP.items()}
        for fk, dms in _ADDR_MAP.items():
            out[fk] = data.get(dms, "")
        out["cuscode"] = data.get("txtcuscode", "")
        return out

    def _apply_customer_fields(self, data: Dict[str, str], f: Dict[str, Any]) -> None:
        for fk, dms in _IDENTITY_MAP.items():
            v = f.get(fk)
            if v is not None:
                data[dms] = str(v)
        # 个人主体:税号留空时取身份证号(DMS 个人客户税号=身份证号)
        if not f.get("tax_id") and f.get("people_id"):
            data["txttaxid"] = str(f["people_id"])
        for sfx in _ADDR_SUFFIXES:
            for fk, dms in _ADDR_MAP.items():
                v = f.get(fk)
                if v is not None:
                    data[dms + sfx] = str(v)

    def _guard_required_selects(self, data: Dict[str, str], form_html: str) -> None:
        """空必填 select 触发误导性 "already in use" → 补成有效值(实测坑)。"""
        if not data.get("selprefix"):
            opts = self._select_options(form_html, "selprefix")
            if opts:
                data["selprefix"] = opts[0][0]
        for sfx in _ADDR_SUFFIXES:
            zk = "selzipcodes" + sfx
            if not data.get(zk):
                sub = data.get("selsubdistricts" + sfx) or data.get("selsubdistricts")
                if sub:
                    z = self._fetch_options(
                        "cus/component/listzipcodes.php", {"selsubdistricts": sub}
                    )
                    if z:
                        data[zk] = z[0][0]

    def _verify_saved(self, mode: str, fields: Dict[str, Any], customer_id: Optional[str]) -> str:
        """PHP 成功码 ≠ 真写库(铁律#9):建→search 复核;改→重读姓名复核。"""
        if mode == "create":
            cid = self.search_customer(fields.get("people_id") or fields.get("name") or "")
            if not cid:
                raise DMSClientError(
                    "customer create returned success but search could not find row",
                    "ERR_DMS_CUSTOMER_SAVE",
                )
            return cid
        html = self._post_text("cus/form.php", {"status": "e", "id": customer_id})
        saved = self._parse_form_defaults(html)
        want = str(fields.get("name") or "").strip()
        if want and saved.get("txtcusname", "").strip() != want:
            raise DMSClientError(
                "customer overwrite returned success but re-read name mismatch",
                "ERR_DMS_CUSTOMER_SAVE",
            )
        return customer_id

    def _select_options(self, html: str, name: str) -> List[List[str]]:
        m = re.search(
            r'<select[^>]+name="%s"[^>]*>(.*?)</select>' % re.escape(name), html, re.S | re.I
        )
        return self._parse_options(m.group(1)) if m else []
