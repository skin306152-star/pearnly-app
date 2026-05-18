# -*- coding: utf-8 -*-
"""
Mr.Pilot · ERP 推送模块 (v0.6.0 · 支柱 3)

设计:
- 适配器(adapter)模式:不同的 ERP 走不同的 push 函数,但对外接口统一
- 标准化 payload:不管哪个适配器,都用统一的 JSON 结构
- 失败自动重试:1/5/30 分钟三次重试(放在调用方实现,这里只管单次)
- 推送日志:每次调用都写一条 erp_push_logs

支持的适配器:
- webhook:通用 HTTP POST(MVP)
- flowaccount:FlowAccount API(以后做)
"""

import os
import json
import time
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# 推送超时(秒)
PUSH_TIMEOUT_SEC = int(os.environ.get("ERP_PUSH_TIMEOUT_SEC", "30"))


# ============================================================
# 标准化 payload
# ============================================================

def build_standard_payload(history_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    把 ocr_history 一行数据转成对外推送的标准 JSON。
    任何适配器都从这里开始,各家适配器可以再自己映射字段。

    输入示例(history_record):
    {
        "id": "uuid...",
        "filename": "SINCERE.pdf",
        "invoice_no": "IV69/00179",
        "invoice_date": "2026-02-28",
        "seller_name": "...",
        "total_amount": 2889.00,
        "confidence": "high",
        "pages": [{"fields": {...}}, ...],
        ...
    }
    """
    pages = history_record.get("pages") or []
    # 从 pages 里找主页(非副本),取它的 fields
    primary = None
    for p in pages:
        if not p.get("is_duplicate") and not p.get("is_copy"):
            primary = p
            break
    if primary is None and pages:
        primary = pages[0]
    fields = (primary or {}).get("fields") or {}

    seller = {
        "name": fields.get("seller_name") or history_record.get("seller_name") or "",
        "tax_id": fields.get("seller_tax") or "",
        "address": fields.get("seller_addr") or "",
    }
    buyer = {
        "name": fields.get("buyer_name") or "",
        "tax_id": fields.get("buyer_tax") or "",
        "address": fields.get("buyer_addr") or "",
    }
    items = []
    for it in (fields.get("items") or []):
        items.append({
            "name": it.get("name", ""),
            "qty": it.get("qty", ""),
            "price": it.get("price", ""),
            "subtotal": it.get("subtotal", ""),
        })

    payload = {
        "source": "mrpilot",
        "version": "1.0",
        "invoice_no": history_record.get("invoice_no") or fields.get("invoice_number") or "",
        "date": history_record.get("invoice_date") or fields.get("date") or "",
        "currency": "THB",
        "subtotal": fields.get("subtotal") or "",
        "vat": fields.get("vat") or "",
        "total": str(history_record.get("total_amount") or fields.get("total_amount") or ""),
        "seller": seller,
        "buyer": buyer,
        "items": items,
        "notes": fields.get("notes") or "",
        "metadata": {
            "filename": history_record.get("filename"),
            "confidence": history_record.get("confidence"),
            "page_count": history_record.get("page_count"),
            "history_id": str(history_record.get("id")),
            "recognized_at": _iso(history_record.get("created_at")),
        },
    }
    return payload


def build_payload_with_idempotency(history_record: Dict[str, Any], endpoint_id: str) -> Dict[str, Any]:
    """build_standard_payload 的包装 · 额外注入 idempotency_key 供接收端去重"""
    payload = build_standard_payload(history_record)
    history_id = str(history_record.get("id") or "")
    payload["idempotency_key"] = f"{history_id}:{endpoint_id}" if history_id and endpoint_id else ""
    return payload


def _iso(dt) -> Optional[str]:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


# ============================================================
# 适配器:Webhook(通用)
# ============================================================

def push_webhook(endpoint_config: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, int, str]:
    """
    通用 HTTP POST 推送。

    endpoint_config 期望字段:
      - url:     必填,目标 URL
      - token:   选填,会作为 X-Mrpilot-Token header 传过去
      - method:  选填,默认 POST,可选 PUT
      - field_map: 选填,字段重命名 {our_field: their_field}
      - extra_headers: 选填,额外 header dict

    返回:(success, http_status, response_body_text)
    """
    url = endpoint_config.get("url", "").strip()
    if not url:
        return False, 0, "endpoint config missing 'url'"

    token = endpoint_config.get("token", "").strip()
    method = endpoint_config.get("method", "POST").upper()
    extra_headers = endpoint_config.get("extra_headers") or {}

    # 字段映射(可选)
    body = payload
    field_map = endpoint_config.get("field_map") or {}
    if field_map and isinstance(field_map, dict):
        body = _apply_field_map(payload, field_map)

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MrPilot/0.96 (+https://pearnly.com)",
    }
    if token:
        headers["X-Mrpilot-Token"] = token
        headers["Authorization"] = f"Bearer {token}"  # 兼容标准 Bearer
    for k, v in extra_headers.items():
        headers[str(k)] = str(v)

    try:
        resp = requests.request(
            method=method,
            url=url,
            json=body,
            headers=headers,
            timeout=PUSH_TIMEOUT_SEC,
        )
        body_text = (resp.text or "")[:2000]  # 截断,防止超大响应炸日志
        success = 200 <= resp.status_code < 300
        return success, resp.status_code, body_text
    except requests.exceptions.Timeout:
        return False, 0, f"timeout after {PUSH_TIMEOUT_SEC}s"
    except requests.exceptions.ConnectionError as e:
        return False, 0, f"connection error: {str(e)[:200]}"
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {str(e)[:200]}"


def _apply_field_map(payload: Dict[str, Any], field_map: Dict[str, str]) -> Dict[str, Any]:
    """简单字段重命名:支持顶层字段重命名,如 {"invoice_no": "doc_number"}"""
    out = dict(payload)
    for src, dst in field_map.items():
        if src in out and dst != src:
            out[dst] = out.pop(src)
    return out


# ============================================================
# 适配器:FlowAccount(以后做,先占位)
# ============================================================

def push_flowaccount(endpoint_config: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, int, str]:
    """FlowAccount API · 以后做"""
    return False, 0, "flowaccount adapter not implemented yet"


# ============================================================
# 适配器分发器
# ============================================================

ADAPTER_REGISTRY = {
    "webhook":     push_webhook,
    "flowaccount": push_flowaccount,
}


def push_to_endpoint(endpoint: Dict[str, Any], history_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    主入口:把一条 history 推到指定 endpoint。

    返回值统一格式:
    {
        "success": True/False,
        "http_status": 200,
        "response_body": "...",
        "error_msg": None | "...",
        "elapsed_ms": 234,
        "request_body": {推送的完整 JSON},
        "adapter": "webhook",
    }
    """
    adapter = endpoint.get("adapter", "webhook")
    config = endpoint.get("config") or {}
    push_fn = ADAPTER_REGISTRY.get(adapter)
    if push_fn is None:
        return {
            "success": False,
            "http_status": 0,
            "response_body": "",
            "error_msg": f"unknown adapter: {adapter}",
            "elapsed_ms": 0,
            "request_body": None,
            "adapter": adapter,
        }

    payload = build_payload_with_idempotency(history_record, str(endpoint.get("id") or ""))
    t0 = time.time()
    try:
        success, http_status, response_body = push_fn(config, payload)
        error_msg = None if success else (response_body[:500] if response_body else "push failed")
    except Exception as e:
        logger.exception(f"[ERP Push] adapter={adapter} 异常")
        success = False
        http_status = 0
        response_body = ""
        error_msg = f"{type(e).__name__}: {str(e)[:300]}"

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[ERP Push] adapter={adapter} success={success} "
        f"http={http_status} elapsed={elapsed_ms}ms "
        f"endpoint_name={endpoint.get('name')!r}"
    )

    return {
        "success": success,
        "http_status": http_status,
        "response_body": response_body,
        "error_msg": error_msg,
        "elapsed_ms": elapsed_ms,
        "request_body": payload,
        "adapter": adapter,
    }


# ============================================================
# 测试连接(给前端「测试连接」按钮用)
# ============================================================

def test_endpoint_connection(adapter: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    用一个最小化测试 payload 调一次,验证配置是否正确。
    """
    test_payload = {
        "source": "mrpilot",
        "version": "1.0",
        "test": True,
        "invoice_no": "TEST-PING",
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "total": "0.00",
        "seller": {"name": "Mr.Pilot Test"},
        "buyer": {"name": "Mr.Pilot Test"},
        "items": [],
        "metadata": {
            "filename": "test-ping.pdf",
            "test_purpose": "connection check from Mr.Pilot",
        },
    }
    push_fn = ADAPTER_REGISTRY.get(adapter)
    if push_fn is None:
        return {"success": False, "http_status": 0, "response_body": "",
                "error_msg": f"unknown adapter: {adapter}"}

    t0 = time.time()
    try:
        success, http_status, response_body = push_fn(config, test_payload)
        error_msg = None if success else (response_body[:500] if response_body else "test failed")
    except Exception as e:
        success = False
        http_status = 0
        response_body = ""
        error_msg = f"{type(e).__name__}: {str(e)[:300]}"

    return {
        "success": success,
        "http_status": http_status,
        "response_body": response_body,
        "error_msg": error_msg,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }
