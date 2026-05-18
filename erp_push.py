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

def push_mrerp(endpoint_config: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, int, str]:
    """MR.ERP push entry — currently a stub at the push_to_endpoint
    boundary because MRERPAdapter operates on batches of histories
    (`upload_invoice_batch(histories, mappings)`), not single payloads.
    The wiring to feed single OCR rows through the batch adapter is
    handled by a separate higher-level entry point (planned for the
    push-pipeline rewrite); for now creating an "mrerp" endpoint is
    allowed so the wizard / cards flow can exercise the test-connection
    + config-storage path without enabling pushes."""
    return False, 0, (
        "mrerp push is not wired into push_to_endpoint yet; "
        "use MRERPAdapter.upload_invoice_batch directly"
    )


ADAPTER_REGISTRY = {
    "webhook":     push_webhook,
    "flowaccount": push_flowaccount,
    "mrerp":       push_mrerp,
}

# Adapters whose endpoint.config carries Fernet-encrypted credentials.
# UI must never round-trip the raw values; the test-connection +
# upload routes decrypt at the last moment.
ENCRYPTED_CRED_ADAPTERS = {"mrerp"}


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

def test_mrerp_endpoint(
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """C-1 (Zihao 2026-05-18 拍板) MR.ERP-specific health check.

    Drives MRERPAdapter.login + select_company against the configured
    instance, then reports back the company-picker page (so the wizard
    can render a company dropdown in Step 3 of the connect modal).

    Expected `config` shape:
        system_url:       https://www.mrerp4sme.com (default)
        username_enc:     kms_helper-encrypted username
        password_enc:     kms_helper-encrypted password
        comidyear:        "6" (optional; used by select_company)
        seldb:            "1" (optional)

    Returns a dict the route handler can pass straight to the UI:
        ok               bool
        elapsed_ms       int
        companies        List[{label, comidyear, seldb}] (best-effort)
        error_code       Optional[str]   ERR_* matching mrerp_business_friendly catalog
        error_friendly   Optional[Dict[lang -> str]]
        raw_error        Optional[str]   for debugging; UI hides under "details"

    Never raises; always returns a dict.
    """
    import os
    import re
    import time as _time
    from services.erp.mrerp_adapter import (
        MRERPAdapter, MRERPAuthError, MRERPBusinessError,
        MRERPTechnicalError,
    )
    from services.erp.mrerp_business_friendly import get_friendly

    cfg = config or {}
    login_url = (cfg.get("system_url") or "https://www.mrerp4sme.com").strip()
    enc_user = cfg.get("username_enc") or ""
    enc_pass = cfg.get("password_enc") or ""
    comidyear = str(cfg.get("comidyear") or "6")
    seldb = str(cfg.get("seldb") or "1")

    if not (enc_user and enc_pass):
        return {
            "ok": False,
            "elapsed_ms": 0,
            "companies": [],
            "error_code": "ERR_NO_CREDS",
            "error_friendly": get_friendly("ERR_NO_CREDS"),
            "raw_error": "username_enc / password_enc missing in config",
        }

    t0 = _time.time()
    try:
        adapter = MRERPAdapter.from_encrypted(
            login_url=login_url,
            encrypted_username=enc_user,
            encrypted_password=enc_pass,
            comidyear=comidyear,
            seldb=seldb,
            headless=True,
            retry_attempts=1,
            retry_delays_seconds=(0.5,),
        )
    except Exception as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "companies": [],
            "error_code": "ERR_CRED_DECRYPT",
            "error_friendly": get_friendly("ERR_CRED_DECRYPT"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    companies: list = []
    try:
        with adapter:
            adapter.login()
            # Scrape the company-picker page (selectdb.php). Each
            # company appears as a click target inside the page; we
            # extract the text labels for the wizard's dropdown.
            try:
                adapter._page.goto(
                    adapter.login_url + adapter.SELECTDB_PATH,
                    wait_until="networkidle",
                    timeout=10_000,
                )
                html = adapter._page.content() or ""
                # MR.ERP selectdb.php renders <button onclick="...
                # comidyear=N&seldb=M"> per company.
                for m in re.finditer(
                    r"(?:onclick|href)=[\"'][^\"']*"
                    r"comidyear=(?P<y>\d+)[^\"']*seldb=(?P<s>\d+)[^\"']*[\"']"
                    r"[^>]*>(?P<label>[^<]+)",
                    html,
                    re.DOTALL,
                ):
                    label = re.sub(r"\s+", " ", m.group("label")).strip()
                    if not label or label.startswith("&"):
                        continue
                    companies.append({
                        "label": label[:80],
                        "comidyear": m.group("y"),
                        "seldb": m.group("s"),
                    })
                # If the regex finds nothing, fall back to a single
                # configured entry so the wizard at least shows the
                # tenant's saved choice.
                if not companies:
                    companies.append({
                        "label": f"TEST{comidyear}-{seldb}",
                        "comidyear": comidyear,
                        "seldb": seldb,
                    })
            except Exception as e:
                logger.warning("company scrape failed: %s", e)
                companies = []
            # Confirm select_company actually works on the saved choice.
            adapter.select_company()
    except MRERPAuthError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "companies": [],
            "error_code": "ERR_AUTH",
            "error_friendly": get_friendly("ERR_AUTH"),
            "raw_error": str(e)[:300],
        }
    except MRERPTechnicalError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "companies": [],
            "error_code": "ERR_TECHNICAL",
            "error_friendly": get_friendly("ERR_TECHNICAL"),
            "raw_error": str(e)[:300],
        }
    except MRERPBusinessError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "companies": [],
            "error_code": "ERR_BUSINESS",
            "error_friendly": get_friendly(str(e)[:80]),
            "raw_error": str(e)[:300],
        }
    except Exception as e:
        logger.exception("test_mrerp_endpoint unexpected error")
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "companies": [],
            "error_code": "ERR_UNEXPECTED",
            "error_friendly": get_friendly("ERR_UNEXPECTED"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    return {
        "ok": True,
        "elapsed_ms": int((_time.time() - t0) * 1000),
        "companies": companies,
        "error_code": None,
        "error_friendly": None,
        "raw_error": None,
    }


def list_mrerp_customers(
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """C-3 follow-up (Zihao 2026-05-18 拍板 Task 1): pull the customer
    listing from armas/allview.php so the wizard's Step-3 seed dropdown
    can show real options instead of asking the user to remember a code.

    Returns:
        {
          "ok": bool,
          "elapsed_ms": int,
          "customers": [{code, name, type_name, prefix}],
          "error_code": Optional[str],
          "error_friendly": Optional[Dict[lang, str]],
          "raw_error": Optional[str],
        }

    The route layer caches this for 60s per (user, endpoint) to keep
    MR.ERP load sane.
    """
    import time as _time
    from services.erp.mrerp_adapter import (
        MRERPAdapter, MRERPAuthError, MRERPBusinessError,
        MRERPTechnicalError,
    )
    from services.erp.mrerp_customer_sync import MRERPCustomerSyncService
    from services.erp.mrerp_business_friendly import get_friendly

    cfg = config or {}
    login_url = (cfg.get("system_url") or "https://www.mrerp4sme.com").strip()
    enc_user = cfg.get("username_enc") or ""
    enc_pass = cfg.get("password_enc") or ""
    comidyear = str(cfg.get("comidyear") or "6")
    seldb = str(cfg.get("seldb") or "1")

    if not (enc_user and enc_pass):
        return {
            "ok": False, "elapsed_ms": 0, "customers": [],
            "error_code": "ERR_NO_CREDS",
            "error_friendly": get_friendly("ERR_NO_CREDS"),
            "raw_error": "username_enc / password_enc missing in config",
        }

    t0 = _time.time()
    try:
        adapter = MRERPAdapter.from_encrypted(
            login_url=login_url,
            encrypted_username=enc_user,
            encrypted_password=enc_pass,
            comidyear=comidyear, seldb=seldb,
            headless=True,
            retry_attempts=1, retry_delays_seconds=(0.5,),
        )
    except Exception as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "customers": [],
            "error_code": "ERR_CRED_DECRYPT",
            "error_friendly": get_friendly("ERR_CRED_DECRYPT"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    try:
        with adapter:
            svc = MRERPCustomerSyncService(adapter)
            rows = svc._fetch_listing()
        customers = [{
            "code": r.code,
            "name": r.name,
            "type_name": r.type_name,
            "prefix": r.prefix,
        } for r in rows]
    except MRERPAuthError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "customers": [],
            "error_code": "ERR_AUTH",
            "error_friendly": get_friendly("ERR_AUTH"),
            "raw_error": str(e)[:300],
        }
    except MRERPTechnicalError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "customers": [],
            "error_code": "ERR_TECHNICAL",
            "error_friendly": get_friendly("ERR_TECHNICAL"),
            "raw_error": str(e)[:300],
        }
    except MRERPBusinessError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "customers": [],
            "error_code": "ERR_BUSINESS",
            "error_friendly": get_friendly("ERR_BUSINESS"),
            "raw_error": str(e)[:300],
        }
    except Exception as e:
        logger.exception("list_mrerp_customers unexpected error")
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "customers": [],
            "error_code": "ERR_UNEXPECTED",
            "error_friendly": get_friendly("ERR_UNEXPECTED"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    return {
        "ok": True,
        "elapsed_ms": int((_time.time() - t0) * 1000),
        "customers": customers,
        "error_code": None,
        "error_friendly": None,
        "raw_error": None,
    }


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
