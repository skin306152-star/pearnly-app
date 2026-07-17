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

import html
import re
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from services.erp.mrerp_dms_client_base import DMSClientError

# 前端友好键 → DMS 客户表单字段名(非地址部分)
_IDENTITY_MAP = {
    "prefix_id": "selprefix",
    "name": "txtcusname",
    "people_id": "txtpeopleid",
    "tax_id": "txttaxid",
    "birthday_be": "txtbirthday",
    "phone": "txttel",
    "tel_work": "txttelwork",
    "tel_home": "txttelhome",
    "email": "txtemail",
    "line_id": "txtlineid",
    "facebook": "txtfacebook",
    "credit_day": "txtcreditday",
}
# 分店(สาขา)= 隐藏 branchcusval(主档 id)+ txtbranchcus(显示码)配对的 typeahead。
# 身份证录入不改分店:只读显示当前码,保存时由载入的表单默认值原样保留(不进可写映射)。
_BRANCH_VAL = "branchcusval"
_BRANCH_CODE = "txtbranchcus"
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
# 地址下拉「选中标签」键 → DMS select 名(各加 ""/_ct/_sd 后缀)· 仅供显示现值
_GEO_LABEL_MAP = {
    "province_name": "selprovinces",
    "district_name": "seldistricts",
    "subdistrict_name": "selsubdistricts",
    "zipcode_name": "selzipcodes",
}


class DMSClientIntakeMixin:
    # ── 读 ──────────────────────────────────────────────────────────
    def lookup_customer(self, people_id: str) -> Dict[str, Any]:
        """按身份证号查 DMS 客户。命中则回当前全字段(给面板「历史资料」)。"""
        cid = self.search_customer(people_id) if (people_id or "").strip() else None
        if not cid:
            return {"found": False, "customer_id": None, "fields": {}}
        page = self._post_text("cus/form.php", {"status": "e", "id": cid})
        return {
            "found": True,
            "customer_id": cid,
            "fields": self._extract_customer_fields(self._parse_form_defaults(page), page),
        }

    def search_customers_detailed(self, text: str, limit: int = 10) -> List[Dict[str, str]]:
        """按 码/姓名/证号 搜 DMS 客户,解析多行候选(给相似匹配)。
        返回 [{customer_id, cuscode, name, people_id}, ...](命中顺序)。"""
        term = (text or "").strip()
        if not term:
            return []
        body = self._post_text(
            "cus/component/showdata.php",
            {
                "sdtamt": str(limit),
                "sdtpage": "1",
                "sd": term,
                "selcolsort": "1",
                "selcolsorttype": "1",
            },
        )
        return self._parse_customer_rows(body)

    def _parse_customer_rows(self, body: str) -> List[Dict[str, str]]:
        """解析 cus/component/showdata.php 的结果行。空结果体以 ndt:: 开头。
        每行:<div data-val=客户号 onclick=ctllistdata> → detaildata 两列
        (列1:客户码 + 姓名;列2:身份证号)· colnodt/"-" 占位视为空。"""
        rows: List[Dict[str, str]] = []
        for block in re.split(r'(?=<div\s+data-val=")', body):
            m = re.match(r'<div\s+data-val="([^"]+)"[^>]*onclick="ctllistdata', block)
            if not m:
                continue
            cid = m.group(1)
            dd = re.search(
                r'<div class="detaildata">(.*?)</div>\s*<div class="statuscf"', block, re.S
            )
            inner = dd.group(1) if dd else block
            cols = re.findall(r"<div>(.*?)</div>", inner, re.S)
            col0 = self._row_texts(cols[0]) if cols else []
            col1 = self._row_texts(cols[1]) if len(cols) > 1 else []
            rows.append(
                {
                    "customer_id": cid,
                    "cuscode": col0[0] if len(col0) > 0 else "",
                    "name": col0[1] if len(col0) > 1 else (col0[0] if col0 else ""),
                    "people_id": col1[0] if col1 else "",
                }
            )
        return rows

    @staticmethod
    def _row_texts(col_html: str) -> List[str]:
        """取一列里各 <p> 的纯文本;占位 "-" 归一为空串。"""
        out: List[str] = []
        for pm in re.finditer(r"<p[^>]*>(.*?)</p>", col_html, re.S):
            t = html.unescape(re.sub(r"<.*?>", "", pm.group(1))).strip()
            out.append("" if t == "-" else t)
        return out

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
        self,
        *,
        fields: Dict[str, Any],
        mode: str,
        customer_id: Optional[str] = None,
        addresses: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> str:
        """建(mode='create')或覆盖(mode='overwrite')客户。返回 customer_id。
        覆盖:载现表单 → 合并面板字段(非身份证字段原样保留)→ 提交。
        空值一律跳过(不清除 DMS 原值)。addresses 给 {""/_ct/_sd: 地址块} 时
        三套地址分别写;不给则用 fields 里的单套地址写满三处(向后兼容)。"""
        if mode not in ("create", "overwrite"):
            raise DMSClientError(f"bad save mode: {mode!r}", "ERR_DMS_CUSTOMER_SAVE")
        with self._writer_session():
            return self._save_customer_locked(
                fields=fields, mode=mode, customer_id=customer_id, addresses=addresses
            )

    @contextmanager
    def _writer_session(self) -> Iterator[None]:
        """客户档写操作(建/改)走 admin 凭据组会话(配了 admin 时);读操作不受影响。
        没配 admin(_resolve_admin_transport → None)则原样用当前会话 —— 单凭据路径
        逐字节不变。整段写流程(含载表单/复核读)都在同一会话内一致。"""
        admin = self._resolve_admin_transport()
        if admin is None:
            yield
            return
        prev = self.transport
        self.transport = admin
        try:
            yield
        finally:
            self.transport = prev

    def _save_customer_locked(
        self,
        *,
        fields: Dict[str, Any],
        mode: str,
        customer_id: Optional[str] = None,
        addresses: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> str:
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

        self._apply_customer_fields(data, fields, addresses)
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
    def _extract_customer_fields(self, data: Dict[str, str], form_html: str = "") -> Dict[str, str]:
        out = {fk: data.get(dms, "") for fk, dms in _IDENTITY_MAP.items()}
        # 三套地址各自抽出(户籍 ""·联系 _ct·寄送 _sd),供全字段表单分区显示。
        for sfx in _ADDR_SUFFIXES:
            for fk, dms in _ADDR_MAP.items():
                out[fk + sfx] = data.get(dms + sfx, "")
            # 地址下拉的选中标签(显示现值用·id 不够):府/县/区/邮编
            if form_html:
                for fk, dms in _GEO_LABEL_MAP.items():
                    out[fk + sfx] = self._geo_label(form_html, dms + sfx, data.get(dms + sfx, ""))
        out["cuscode"] = data.get("txtcuscode", "")
        out["branch_id"] = data.get(_BRANCH_VAL, "")
        out["branch_code"] = data.get(_BRANCH_CODE, "")
        return out

    def _geo_label(self, form_html: str, select_name: str, value: str) -> str:
        if not value:
            return ""
        for v, label in self._select_options(form_html, select_name):
            if v == value:
                return label
        return ""

    def _apply_customer_fields(
        self,
        data: Dict[str, str],
        f: Dict[str, Any],
        addresses: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        # 所见即所存:字段【存在】(键在)就写,空串=真清空 DMS;字段【缺省】(键不在)
        # 才保留载入的 DMS 原值。前端表单初值来自 DMS,没动的字段原样回写(=保留)、
        # 手动清空的字段送空串(=清除)。需求:更新只动身份证有的、手动改的按用户来。
        for fk, dms in _IDENTITY_MAP.items():
            if fk in f:
                data[dms] = str(f.get(fk) or "")
        # 个人主体:税号留空时取身份证号(DMS 个人客户税号=身份证号)
        if not f.get("tax_id") and f.get("people_id"):
            data["txttaxid"] = str(f["people_id"])
        # 三套地址:给了 addresses 就各套分别写;否则单套写满三处(向后兼容)。
        blocks = addresses if addresses else {sfx: f for sfx in _ADDR_SUFFIXES}
        for sfx, blk in blocks.items():
            if sfx not in _ADDR_SUFFIXES:
                continue
            blk = blk or {}
            for fk, dms in _ADDR_MAP.items():
                if fk in blk:
                    data[dms + sfx] = str(blk.get(fk) or "")

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
