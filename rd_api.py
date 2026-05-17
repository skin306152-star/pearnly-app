# -*- coding: utf-8 -*-
"""
Mr.Pilot · 泰国 RD 税务局 SOAP API 客户端 (v0.5.1)

提供两个能力:
  1. verify_tin(tax_id)         → 校验 13 位税号(TIN Service)
  2. lookup_vat(tax_id, branch) → 查询 VAT 注册公司信息(VAT Service · 17 字段)

特性:
  - 7 天 DB 缓存(rd_cache 表)
  - 5 秒超时 · 失败不抛异常,返回 {ok: false, error: ...}
  - 自动重试 1 次
  - anonymous/anonymous 公开认证
"""

import logging
import re
from typing import Optional, Dict, Any
from xml.etree import ElementTree as ET

import requests

from db import get_cursor

logger = logging.getLogger(__name__)

TIN_ENDPOINT = "https://rdws.rd.go.th/serviceRD3/checktinpinservice.asmx"
VAT_ENDPOINT = "https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx"

TIMEOUT_SEC = 5
RETRY_TIMES = 1

# SOAP 1.2 envelope 模板(按官方 PDF Sample_SOAP_Request_V5 规范)
TIN_SOAP_TPL = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:chec="https://rdws.rd.go.th/serviceRD3/checktinpinservice">
  <soap:Header/>
  <soap:Body>
    <chec:ServiceTIN>
      <chec:username>anonymous</chec:username>
      <chec:password>anonymous</chec:password>
      <chec:TIN>{tax_id}</chec:TIN>
    </chec:ServiceTIN>
  </soap:Body>
</soap:Envelope>"""

VAT_SOAP_TPL = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:vat="https://rdws.rd.go.th/serviceRD3/vatserviceRD3">
  <soap:Header/>
  <soap:Body>
    <vat:Service>
      <vat:username>anonymous</vat:username>
      <vat:password>anonymous</vat:password>
      <vat:TIN>{tax_id}</vat:TIN>
      <vat:Name></vat:Name>
      <vat:ProvinceCode>0</vat:ProvinceCode>
      <vat:BranchNumber>{branch_no}</vat:BranchNumber>
      <vat:AmphurCode>0</vat:AmphurCode>
    </vat:Service>
  </soap:Body>
</soap:Envelope>"""


def _normalize_tin(s: str) -> Optional[str]:
    """提取 13 位数字。任何非数字都剥离。"""
    if not s:
        return None
    digits = re.sub(r"\D", "", str(s))
    return digits if len(digits) == 13 else None


# ============================================================
# 缓存
# ============================================================

def _cache_get(tax_id: str, branch: int, service: str) -> Optional[dict]:
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT payload, is_success, error_msg
                FROM rd_cache
                WHERE tax_id = %s AND branch_no = %s AND service = %s
                  AND expires_at > NOW()
                LIMIT 1
            """, (tax_id, branch, service))
            row = cur.fetchone()
            if not row:
                logger.info(f"  [RD Cache MISS] tax_id={tax_id[:6]}..., service={service}")
                return None
            if row["is_success"]:
                logger.info(f"  [RD Cache HIT SUCCESS] tax_id={tax_id[:6]}..., service={service}, payload={row['payload']}")
                return {"ok": True, "data": row["payload"], "cached": True}
            logger.info(f"  [RD Cache HIT FAIL] tax_id={tax_id[:6]}..., service={service}, error={row['error_msg']}")
            return {"ok": False, "error": row["error_msg"] or "cached_error", "cached": True}
    except Exception as e:
        logger.warning(f"rd_cache 读失败: {e}")
        return None


def _cache_set(tax_id: str, branch: int, service: str, payload: Any, is_success: bool, error_msg: Optional[str] = None):
    import json as _json
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO rd_cache (tax_id, branch_no, service, payload, is_success, error_msg, cached_at, expires_at)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s, NOW(), NOW() + INTERVAL '7 days')
                ON CONFLICT (tax_id, branch_no, service)
                DO UPDATE SET
                    payload    = EXCLUDED.payload,
                    is_success = EXCLUDED.is_success,
                    error_msg  = EXCLUDED.error_msg,
                    cached_at  = NOW(),
                    expires_at = NOW() + INTERVAL '7 days'
            """, (tax_id, branch, service, _json.dumps(payload, ensure_ascii=False), is_success, error_msg))
    except Exception as e:
        logger.warning(f"rd_cache 写失败: {e}")


# ============================================================
# SOAP 调用 + XML 解析
# ============================================================

def _soap_post(url: str, body: str) -> Optional[str]:
    """发 SOAP 1.2 请求,返回 XML 字符串(失败返回 None)"""
    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
    }
    last_err = None
    for attempt in range(RETRY_TIMES + 1):
        try:
            r = requests.post(url, data=body.encode("utf-8"), headers=headers, timeout=TIMEOUT_SEC)
            if r.status_code == 200:
                logger.info(f"  RD SOAP 成功 ({url.rsplit('/', 1)[-1]}, {len(r.text)} bytes)")
                return r.text
            last_err = f"HTTP {r.status_code}"
            # 打印请求和响应的关键信息,方便排查
            body_snippet = (r.text or "")[:400].replace("\n", " ").replace("  ", " ")
            logger.warning(f"  RD SOAP 返回 {last_err} · 响应头={dict(r.headers)} · body={body_snippet}")
        except requests.Timeout:
            last_err = "timeout"
            logger.warning(f"  RD SOAP 超时 (timeout={TIMEOUT_SEC}s)")
        except Exception as e:
            last_err = type(e).__name__
            logger.warning(f"  RD SOAP 异常: {e}")
        if attempt < RETRY_TIMES:
            logger.info(f"  RD SOAP 重试 ({attempt+1}/{RETRY_TIMES})")
    logger.warning(f"  RD SOAP 最终失败: {last_err} (版本标记: v0.5.1-soap12)")
    return None


def _strip_ns(tag: str) -> str:
    """去掉 XML 命名空间前缀: {ns}TagName → TagName"""
    return tag.split("}", 1)[1] if "}" in tag else tag


def _xml_to_dict(elem) -> Dict[str, Any]:
    """递归转 XML 元素为 dict(取首个文本子节点)"""
    result = {}
    for child in elem:
        tag = _strip_ns(child.tag)
        text = (child.text or "").strip()
        if list(child):
            # 子元素优先递归;如果只有一层,数组形式
            children_dict = _xml_to_dict(child)
            if children_dict:
                result[tag] = children_dict
            elif text:
                result[tag] = text
        else:
            result[tag] = text
    return result


def _flatten_vat_response(xml_text: str) -> Optional[Dict[str, Any]]:
    """
    VAT Service 返回的 XML 各字段都被嵌套在 <anyType xsi:type="xsd:string">...</anyType> 里。
    字段名带 v 前缀(vNID, vBranchName, ...)
    """
    snippet = xml_text[:1200].replace("\n", " ")
    logger.info(f"  [RD VAT 响应前 1200 字] {snippet}")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning(f"  [RD VAT] XML 解析失败: {e}")
        return None

    # 所有 VAT 字段(带 v 前缀的版本是实际返回的)
    known_tags_lower = {
        "nid", "branchnumber",
        "branchtitlename", "branchtitle", "branchname",
        "buildingname", "roomnumber", "floornumber", "villagename",
        "housenumber", "moonumber", "soiname", "streetname",
        "thumbolname", "amphurname", "provincename", "postcode",
        "businessfirstdate", "msgerr", "messageerr",
    }

    def _inner_value(elem) -> Optional[str]:
        own = (elem.text or "").strip()
        if own:
            return own
        for sub in elem.iter():
            if sub is elem:
                continue
            t = (sub.text or "").strip()
            if t:
                return t
        return None

    fields = {}
    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        t_low = tag.lower()
        # 同时检查带 v 前缀和不带的
        normalized = t_low[1:] if t_low.startswith("v") and len(t_low) > 1 else t_low
        if normalized not in known_tags_lower:
            continue
        value = _inner_value(elem)
        if not value:
            continue
        # 去除前导 v 让 key 统一
        clean_key = tag[1:] if tag.startswith("v") and len(tag) > 1 and tag[1].isupper() else tag
        if clean_key not in fields:
            fields[clean_key] = value
    logger.info(f"  [RD VAT] 解析到字段: {fields}")
    if not fields:
        return None
    return fields


def _flatten_tin_response(xml_text: str) -> Optional[Dict[str, Any]]:
    """TIN Service 返回值解析。实际响应结构:
    <ServiceTINResult>
      <vMessageErr />
      <vID><anyType xsi:type=\"xsd:string\">0105546015062</anyType></vID>
      <vDigitOk><anyType xsi:type=\"xsd:string\">True</anyType></vDigitOk>
      <vIsExist><anyType xsi:type=\"xsd:string\">Yes</anyType></vIsExist>
    </ServiceTINResult>
    """
    snippet = xml_text[:800].replace("\n", " ")
    logger.info(f"  [RD TIN 响应] {snippet}")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning(f"  [RD TIN] XML 解析失败: {e}")
        return None

    # 辅助:从 <vXxx><anyType>value</anyType></vXxx> 里取出最深的文本
    def _inner_value(elem) -> Optional[str]:
        # 先看自身文本
        own = (elem.text or "").strip()
        if own:
            return own
        # 再找最深的有文本的子节点
        for sub in elem.iter():
            if sub is elem:
                continue
            t = (sub.text or "").strip()
            if t:
                return t
        return None

    result = {"valid": False, "exists": False, "raw_tags": {}}
    for elem in root.iter():
        tag = _strip_ns(elem.tag)
        t_low = tag.lower()
        # 只关心 vXxx / Xxx 这类语义字段,跳过 anyType/string 等包装
        if t_low in ("anytype", "string", "soap:envelope", "envelope", "body", "soap:body"):
            continue
        value = _inner_value(elem)
        if not value:
            continue
        result["raw_tags"][tag] = value
        v_low = value.lower()

        if t_low in ("visexist", "isexist"):
            # 支持多种真值表达:Yes / True / 1
            result["exists"] = v_low in ("true", "1", "yes", "y")
        elif t_low in ("vdigitok", "digitok"):
            # 税号数字校验(格式对不对)
            result["digit_ok"] = v_low in ("true", "1", "yes", "y")
        elif t_low in ("vid", "nid"):
            result["nid"] = value
        elif t_low in ("vmessageerr", "vmsgerr", "messageerr"):
            result["error"] = value

    # valid = 数字格式对 + 确实存在
    result["valid"] = result.get("exists", False) and result.get("digit_ok", True)
    logger.info(f"  [RD TIN] 解析结果: valid={result['valid']}, exists={result['exists']}, raw={result['raw_tags']}")
    return result


# ============================================================
# 对外 API
# ============================================================

def verify_tin(raw_tax_id: str) -> Dict[str, Any]:
    """
    校验 13 位税号是否真实存在。
    返回:{ok: bool, data: {valid, exists}, error?: str, cached?: bool}
    """
    tin = _normalize_tin(raw_tax_id)
    if not tin:
        return {"ok": False, "error": "invalid_format"}

    # 缓存
    cached = _cache_get(tin, 0, "tin")
    if cached:
        return cached

    body = TIN_SOAP_TPL.format(tax_id=tin)
    xml = _soap_post(TIN_ENDPOINT, body)
    if not xml:
        return {"ok": False, "error": "rd_unreachable"}

    parsed = _flatten_tin_response(xml)
    if parsed is None:
        # 解析完全失败 · 不缓存(这样下次重试会再拿真实响应)
        return {"ok": False, "error": "parse_error"}

    # 如果 raw_tags 为空或只有空字段,说明解析有 bug,不要缓存
    if not parsed.get("raw_tags"):
        logger.warning(f"  [RD TIN] raw_tags 为空,可能是解析 bug,暂不缓存")
        return {"ok": False, "error": "parse_empty", "debug_raw": xml[:500]}

    _cache_set(tin, 0, "tin", parsed, True)
    return {"ok": True, "data": parsed, "cached": False}


def lookup_vat(raw_tax_id: str, branch: int = 0) -> Dict[str, Any]:
    """
    查询 VAT 注册公司信息(返回 17 字段)。
    返回:{ok: bool, data: {NID, BranchName, ProvinceName, ...}, error?: str, cached?: bool}
    """
    tin = _normalize_tin(raw_tax_id)
    if not tin:
        return {"ok": False, "error": "invalid_format"}

    branch = max(0, int(branch or 0))
    cached = _cache_get(tin, branch, "vat")
    if cached:
        return cached

    body = VAT_SOAP_TPL.format(tax_id=tin, branch_no=branch)
    xml = _soap_post(VAT_ENDPOINT, body)
    if not xml:
        return {"ok": False, "error": "rd_unreachable"}

    fields = _flatten_vat_response(xml)
    if not fields or not fields.get("NID"):
        # 没找到这家公司
        _cache_set(tin, branch, "vat", {}, False, "not_found")
        return {"ok": False, "error": "not_found"}

    # 拼装 mr-pilot 友好的字段(给前端用)
    addr_parts = []
    for k in ("HouseNumber", "MooNumber", "VillageName", "BuildingName",
              "RoomNumber", "FloorNumber", "SoiName", "StreetName",
              "ThumbolName", "AmphurName", "ProvinceName", "PostCode"):
        v = fields.get(k, "").strip()
        if v and v != "-":
            addr_parts.append(v)
    full_addr = " ".join(addr_parts)

    branch_no_raw = fields.get("BranchNumber", "0")
    try:
        branch_no_int = int(branch_no_raw)
    except (TypeError, ValueError):
        branch_no_int = 0

    name_parts = []
    title = (fields.get("BranchTitleName") or fields.get("BranchTitle") or "").strip()
    name = (fields.get("BranchName") or "").strip()
    if title:
        name_parts.append(title)
    if name:
        name_parts.append(name)
    full_name = " ".join(name_parts) if name_parts else None

    branch_label = "สำนักงานใหญ่" if branch_no_int == 0 else f"สาขา {branch_no_int:05d}"

    payload = {
        "tax_id": fields.get("NID", tin),
        "branch_no": branch_no_int,
        "branch_label": branch_label,
        "name": full_name,
        "address": full_addr,
        "post_code": fields.get("PostCode"),
        "province": fields.get("ProvinceName"),
        "vat_register_date": fields.get("BusinessFirstDate"),
        "raw_fields": fields,  # 原始 17 字段保留,前端能对照用
    }

    _cache_set(tin, branch, "vat", payload, True)
    return {"ok": True, "data": payload, "cached": False}
