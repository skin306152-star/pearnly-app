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
    """C-1 (Zihao 2026-05-18 拍板) + v118.34.2 hardening (2026-05-19) ·
    MR.ERP-specific health check.

    Drives MRERPAdapter.login + select_company against the configured
    instance, then reports back the company-picker page (so the wizard
    can render a company dropdown in Step 3 of the connect modal).

    Accepts TWO credential shapes:
        wizard path (plaintext, in-memory only):
            username:     "myuser"
            password:     "mypass"
        DB path (Fernet ciphertext, persisted endpoint):
            username_enc: "gAAAAA..."
            password_enc: "gAAAAA..."
    Plus common fields:
        system_url:   https://www.mrerp4sme.com (default)
        comidyear:    "6" (optional)
        seldb:        "1" (optional)

    Returns a dict the route handler can pass straight to the UI:
        ok               bool
        elapsed_ms       int
        companies        List[{label, comidyear, seldb}] (best-effort)
        error_code       Optional[str]
        error_friendly   Optional[Dict[lang -> str]]
        raw_error        Optional[str]   for debugging; UI hides under "details"

    NEVER raises — even if Playwright is missing on the host, kms_helper
    can't import, or the adapter blows up on construction. Any uncaught
    exception is wrapped into a {ok: False, error_code: "ERR_UNEXPECTED",
    raw_error: "<exception detail>"} response so the wizard error bar
    always has something to render and we never surface a 500 to the UI.
    """
    import time as _time
    t0 = _time.time()

    def _elapsed():
        return int((_time.time() - t0) * 1000)

    # Hard-coded fallback friendly catalog — used when even
    # mrerp_business_friendly fails to import. Covers the same 4 langs
    # as the regular catalog so the UI rendering layer doesn't need to
    # special-case.
    _FALLBACK_FRIENDLY = {
        "ERR_UNEXPECTED": {
            "zh": "服务器内部错误,请联系管理员",
            "en": "Internal server error, please contact admin",
            "th": "ข้อผิดพลาดของเซิร์ฟเวอร์ภายใน กรุณาติดต่อผู้ดูแล",
            "zh_TW": "伺服器內部錯誤,請聯絡管理員",
        },
        "ERR_PLAYWRIGHT_MISSING": {
            "zh": "服务器缺少 Playwright 依赖,请联系运维",
            "en": "Server is missing the Playwright dependency",
            "th": "เซิร์ฟเวอร์ขาดไลบรารี Playwright",
            "zh_TW": "伺服器缺少 Playwright 依賴",
        },
        "ERR_KMS_MISSING": {
            "zh": "服务器加密密钥未配置,请联系运维",
            "en": "Server KMS key (PEARNLY_KMS_KEY) is not configured",
            "th": "เซิร์ฟเวอร์ยังไม่ตั้งค่าคีย์เข้ารหัส",
            "zh_TW": "伺服器加密金鑰未設定",
        },
        "ERR_NO_CREDS": {
            "zh": "请输入用户名和密码",
            "en": "Username and password required",
            "th": "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน",
            "zh_TW": "請輸入使用者名稱和密碼",
        },
        "ERR_CRED_DECRYPT": {
            "zh": "凭据解密失败 · 请重新输入用户名和密码",
            "en": "Credential decrypt failed — please re-enter username and password",
            "th": "ถอดรหัสข้อมูลรับรองไม่สำเร็จ",
            "zh_TW": "憑證解密失敗 · 請重新輸入",
        },
    }

    def _friendly(code: str) -> Dict[str, str]:
        try:
            from services.erp.mrerp_business_friendly import get_friendly
            f = get_friendly(code)
            if f:
                return f
        except Exception:
            pass
        return _FALLBACK_FRIENDLY.get(code, _FALLBACK_FRIENDLY["ERR_UNEXPECTED"])

    def _fail(code: str, raw: str = "") -> Dict[str, Any]:
        return {
            "ok": False,
            "elapsed_ms": _elapsed(),
            "companies": [],
            "error_code": code,
            "error_friendly": _friendly(code),
            "raw_error": (raw or "")[:300],
        }

    # ── top-level safety net: if ANY of the body below raises, we
    #    still want to return a clean 200 with a friendly error.
    try:
        # ── imports (may fail on prod if Playwright wasn't installed) ──
        try:
            import re as _re
            from services.erp.mrerp_adapter import (
                MRERPAdapter, MRERPAuthError, MRERPBusinessError,
                MRERPTechnicalError,
            )
        except ImportError as e:
            logger.exception("test_mrerp_endpoint import failure")
            msg = f"{type(e).__name__}: {e}"
            code = ("ERR_PLAYWRIGHT_MISSING"
                    if "playwright" in str(e).lower()
                    else "ERR_UNEXPECTED")
            return _fail(code, msg)

        cfg = config or {}
        login_url = (cfg.get("system_url") or "https://www.mrerp4sme.com").strip()
        comidyear = str(cfg.get("comidyear") or "6")
        seldb = str(cfg.get("seldb") or "1")

        # Both credential shapes are accepted. Plaintext wins if both are
        # present (wizard explicitly typed something fresh).
        plain_user = (cfg.get("username") or "").strip()
        plain_pass = cfg.get("password") or ""
        enc_user = (cfg.get("username_enc") or "").strip()
        enc_pass = cfg.get("password_enc") or ""

        # Heuristic: a value that looks like Fernet ciphertext (gAAAAA*
        # prefix) gets routed through the decrypt path even if it landed
        # in the plaintext field. Covers the wizard's "edit saved
        # endpoint" flow where the form pre-fills with stored ciphertext.
        try:
            from kms_helper import is_encrypted as _is_enc
            if plain_user and _is_enc(plain_user) and not enc_user:
                enc_user, plain_user = plain_user, ""
            if plain_pass and _is_enc(plain_pass) and not enc_pass:
                enc_pass, plain_pass = plain_pass, ""
        except ImportError:
            # kms_helper is broken; we can still serve the plaintext path.
            pass

        if not ((plain_user and plain_pass) or (enc_user and enc_pass)):
            return _fail("ERR_NO_CREDS",
                         "username/password missing (neither plain nor encrypted)")

        # ── adapter construction (caught individually so we can
        #    distinguish decrypt failure from constructor failure) ──
        try:
            # v118.34.15 · retry_attempts=2 + 2s delay between · 配合
            # 新加的 login form wait+reload 内层 retry · 两层组合给一次
            # 测试连接最多:
            #   外层 attempt 1:
            #     login form wait 15s (try1) → reload+wait 15s (try2) → fail
            #   sleep 2s
            #   外层 attempt 2:
            #     login form wait 15s (try1) → reload+wait 15s (try2) → fail
            # 总预算 ~64s · 但绝大多数情况都在第一层就过了。
            if plain_user and plain_pass:
                adapter = MRERPAdapter(
                    login_url=login_url,
                    username=plain_user,
                    password=plain_pass,
                    comidyear=comidyear,
                    seldb=seldb,
                    headless=True,
                    retry_attempts=2,
                    retry_delays_seconds=(2.0,),
                )
            else:
                adapter = MRERPAdapter.from_encrypted(
                    login_url=login_url,
                    encrypted_username=enc_user,
                    encrypted_password=enc_pass,
                    comidyear=comidyear,
                    seldb=seldb,
                    headless=True,
                    retry_attempts=2,
                    retry_delays_seconds=(2.0,),
                )
        except ImportError as e:
            # kms_helper failed to import — PEARNLY_KMS_KEY env likely missing.
            logger.exception("test_mrerp_endpoint kms import failure")
            return _fail("ERR_KMS_MISSING", f"{type(e).__name__}: {e}")
        except ValueError as e:
            # Constructor's own validation (login_url empty / decrypt
            # failed with InvalidToken wrapped to ValueError).
            return _fail("ERR_CRED_DECRYPT", f"{type(e).__name__}: {e}")
        except Exception as e:
            logger.exception("test_mrerp_endpoint adapter construction failed")
            return _fail("ERR_UNEXPECTED", f"{type(e).__name__}: {e}")

        # ── login + scrape ──
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
                    for m in _re.finditer(
                        r"(?:onclick|href)=[\"'][^\"']*"
                        r"comidyear=(?P<y>\d+)[^\"']*seldb=(?P<s>\d+)[^\"']*[\"']"
                        r"[^>]*>(?P<label>[^<]+)",
                        html,
                        _re.DOTALL,
                    ):
                        label = _re.sub(r"\s+", " ", m.group("label")).strip()
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
            return _fail("ERR_AUTH", str(e))
        except MRERPTechnicalError as e:
            # v118.34.15 · the new login form retry path puts the
            # screenshot path inside the exception message after
            # "screenshot=". Echo it into raw_error so the wizard's
            # error bar carries actionable hint and /api/version's
            # last_500 has a real path to /tmp/mrerp_login_fail_<ts>.png.
            return _fail("ERR_TECHNICAL", str(e))
        except MRERPBusinessError as e:
            return _fail("ERR_BUSINESS", str(e))
        except Exception as e:
            logger.exception("test_mrerp_endpoint login/scrape failed")
            return _fail("ERR_UNEXPECTED", f"{type(e).__name__}: {e}")

        return {
            "ok": True,
            "elapsed_ms": _elapsed(),
            "companies": companies,
            "error_code": None,
            "error_friendly": None,
            "raw_error": None,
        }

    except Exception as e:
        # Catastrophic outer-loop catch. Should never fire (every path
        # above handles its own errors) but the contract is "never raise"
        # so a final safety net is mandatory.
        logger.exception("test_mrerp_endpoint catastrophic failure")
        return _fail("ERR_UNEXPECTED", f"{type(e).__name__}: {e}")


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


def list_mrerp_products(
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Task 2 Phase 5 (Zihao 2026-05-18 拍板) · Pull the product listing
    from stkmas/allview.php so the wizard's Step-3 seed-product
    dropdown can show real options.

    Returns the same shape as list_mrerp_customers but with a
    `products` key:
        {
          "ok": bool, "elapsed_ms": int,
          "products": [{code, name, category_code, category_name}],
          "error_code", "error_friendly", "raw_error",
        }
    """
    import time as _time
    from services.erp.mrerp_adapter import (
        MRERPAdapter, MRERPAuthError, MRERPBusinessError,
        MRERPTechnicalError,
    )
    from services.erp.mrerp_product_sync import MRERPProductSyncService
    from services.erp.mrerp_business_friendly import get_friendly

    cfg = config or {}
    login_url = (cfg.get("system_url") or "https://www.mrerp4sme.com").strip()
    enc_user = cfg.get("username_enc") or ""
    enc_pass = cfg.get("password_enc") or ""
    comidyear = str(cfg.get("comidyear") or "6")
    seldb = str(cfg.get("seldb") or "1")

    if not (enc_user and enc_pass):
        return {
            "ok": False, "elapsed_ms": 0, "products": [],
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
            "products": [],
            "error_code": "ERR_CRED_DECRYPT",
            "error_friendly": get_friendly("ERR_CRED_DECRYPT"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    try:
        with adapter:
            svc = MRERPProductSyncService(adapter)
            rows = svc._fetch_listing()
        products = [{
            "code": r.code,
            "name": r.name,
            "category_code": r.category_code,
            "category_name": r.category_name,
        } for r in rows]
    except MRERPAuthError as e:
        return {
            "ok": False, "elapsed_ms": int((_time.time() - t0) * 1000),
            "products": [], "error_code": "ERR_AUTH",
            "error_friendly": get_friendly("ERR_AUTH"),
            "raw_error": str(e)[:300],
        }
    except MRERPTechnicalError as e:
        return {
            "ok": False, "elapsed_ms": int((_time.time() - t0) * 1000),
            "products": [], "error_code": "ERR_TECHNICAL",
            "error_friendly": get_friendly("ERR_TECHNICAL"),
            "raw_error": str(e)[:300],
        }
    except MRERPBusinessError as e:
        return {
            "ok": False, "elapsed_ms": int((_time.time() - t0) * 1000),
            "products": [], "error_code": "ERR_BUSINESS",
            "error_friendly": get_friendly("ERR_BUSINESS"),
            "raw_error": str(e)[:300],
        }
    except Exception as e:
        logger.exception("list_mrerp_products unexpected error")
        return {
            "ok": False, "elapsed_ms": int((_time.time() - t0) * 1000),
            "products": [], "error_code": "ERR_UNEXPECTED",
            "error_friendly": get_friendly("ERR_UNEXPECTED"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    return {
        "ok": True, "elapsed_ms": int((_time.time() - t0) * 1000),
        "products": products, "error_code": None,
        "error_friendly": None, "raw_error": None,
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
