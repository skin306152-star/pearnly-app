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

# E1 verbatim 搬家 re-export(MR.ERP 连接测试 + 客户/产品拉取 · 调用方/dispatch 测 0 改动)
from erp_mrerp_listing import (  # noqa: E402,F401
    list_mrerp_customers,
    list_mrerp_products,
    test_mrerp_endpoint,
)

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
    for it in fields.get("items") or []:
        items.append(
            {
                "name": it.get("name", ""),
                "qty": it.get("qty", ""),
                "price": it.get("price", ""),
                "subtotal": it.get("subtotal", ""),
            }
        )

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


def build_payload_with_idempotency(
    history_record: Dict[str, Any], endpoint_id: str
) -> Dict[str, Any]:
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


def push_flowaccount(
    endpoint_config: Dict[str, Any], payload: Dict[str, Any]
) -> Tuple[bool, int, str]:
    """FlowAccount API · 以后做"""
    return False, 0, "flowaccount adapter not implemented yet"


# ============================================================
# 适配器分发器
# ============================================================


def push_mrerp(endpoint_config: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, int, str]:
    """MR.ERP push entry · stub kept for ADAPTER_REGISTRY back-compat.

    The actual mrerp push lives in `push_mrerp_history(endpoint, history)`
    and is dispatched directly from `push_to_endpoint` (early-return for
    adapter='mrerp'), bypassing the (config, payload) shape entirely
    because MRERPAdapter needs the raw history + per-tenant mappings.

    The guard test `test_push_mrerp_is_still_a_refusal_stub` deliberately
    pins this stub down: if it ever stops returning the "not wired" body,
    the test fires — forcing the auditor to re-check whether
    push_to_endpoint's early-return is still in place. Don't remove the
    stub even after the real path lands."""
    return (
        False,
        0,
        (
            "mrerp push is not wired into push_to_endpoint yet; "
            "use MRERPAdapter.upload_invoice_batch directly"
        ),
    )


def push_mrerp_dms(
    endpoint_config: Dict[str, Any], payload: Dict[str, Any]
) -> Tuple[bool, int, str]:
    """MR.ERP DMS (car-sales) push entry · stub kept for ADAPTER_REGISTRY
    membership only.

    The DMS adapter is NOT an invoice-history push target. The ID-card →
    booking flow has its own route (POST /api/dms/id-card-booking →
    push_mrerp_dms_id_card). `push_to_endpoint` early-rejects adapter=
    'mrerp_dms' (ERR_DMS_NOT_INVOICE_ENDPOINT) so an invoice history can
    never be misrouted into DMS. This stub exists only so endpoint creation
    (which validates `adapter in ADAPTER_REGISTRY`) accepts mrerp_dms; if it
    is ever actually reached, that early-reject regressed.

    Guard test: test_push_mrerp_dms_stub_refuses (+ the not-invoice route
    test). Don't remove the stub even though the early-reject shadows it."""
    return (
        False,
        0,
        "mrerp_dms is not an invoice push target; use POST /api/dms/id-card-booking",
    )


def flatten_history_for_mrerp(history_record: Dict[str, Any]) -> Dict[str, Any]:
    """P1c · 把 OCR pages 顶层 fields 拍平,让 MRERPAdapter._extract_buyer 能直接
    在 history_flat['fields'] 找到 buyer_name(行为不变 · 从 push_mrerp_history 抽出)。
    选第一个非 duplicate/copy 的 page · 没有就退第一页。不写 tenant_id(caller 加)。"""
    pages = history_record.get("pages") or []
    primary = None
    for p in pages:
        if isinstance(p, dict) and not p.get("is_duplicate") and not p.get("is_copy"):
            primary = p
            break
    if primary is None and pages and isinstance(pages[0], dict):
        primary = pages[0]
    fields = (primary or {}).get("fields") if isinstance(primary, dict) else {}
    fields = fields if isinstance(fields, dict) else {}

    history_flat = dict(history_record)
    history_flat["fields"] = fields
    return history_flat


def load_mrerp_mappings(tenant_id: Optional[str]) -> Dict[str, Any]:
    """P1c · 取该 tenant 的 MR.ERP 主数据映射 bundle(clients/products/accounts/taxes)。
    无 tenant → 空 bundle(行为不变 · 从 push_mrerp_history 抽出)。"""
    try:
        import db as _db
    except Exception:
        return {"clients": [], "products": [], "accounts": [], "taxes": []}
    return (
        _db.get_mrerp_mappings_bundle(tenant_id)
        if tenant_id
        else {"clients": [], "products": [], "accounts": [], "taxes": []}
    )


def build_mrerp_adapter(config: Dict[str, Any]):
    """P1c · 从 endpoint.config 构造 MRERPAdapter(行为不变 · 从 push_mrerp_history 抽出)。

    返回 (adapter, err):
      - 成功 → (adapter, None)
      - 失败 → (None, {"http_status", "body", "error_msg"}) · caller 直接拼成 push 结果 dict
    单张(push_mrerp_history)和批量(push_dispatch.dispatch_endpoint_batch)共用此构造逻辑。
    """
    # lazy adapter import (Playwright may be missing on dev boxes).
    try:
        from services.erp.mrerp_adapter import MRERPAdapter
    except ImportError as e:
        return None, {
            "http_status": 0,
            "body": f"playwright_missing: {e}",
            "error_msg": f"ERR_PLAYWRIGHT_MISSING: {e}",
        }

    # credentials. Accept both shapes:
    #   enc_user/enc_pass (Fernet ciphertext via wizard POST encryption)
    #   plain_user/plain_pass (legacy plaintext or PATCH-not-yet-encrypted path)
    enc_user = (config.get("username_enc") or "").strip()
    enc_pass = config.get("password_enc") or ""
    plain_user = (config.get("username") or "").strip()
    plain_pass = config.get("password") or ""

    # If a plaintext field actually contains Fernet ciphertext (the wizard's
    # "edit saved endpoint" pre-fills with stored ciphertext), route it to
    # the decrypt path. Heuristic: gAAAAA* prefix.
    try:
        from kms_helper import is_encrypted as _is_enc

        if enc_user and not _is_enc(enc_user):
            plain_user, enc_user = enc_user, ""
        if enc_pass and not _is_enc(enc_pass):
            plain_pass, enc_pass = enc_pass, ""
    except ImportError:
        pass

    common_kwargs: Dict[str, Any] = dict(
        login_url=(config.get("system_url") or "https://www.mrerp4sme.com").strip(),
        comidyear=str(config.get("comidyear") or "6"),
        seldb=str(config.get("seldb") or "1"),
        headless=True,
        retry_attempts=2,
        retry_delays_seconds=(2.0,),
        enable_master_data_sync=True,
        master_data_auto_create=bool(config.get("master_data_auto_create", True)),
        seed_customer_code=(config.get("seed_customer_code") or None),
        seed_product_code=(config.get("seed_product_code") or None),
        # P1「开箱即用」· 通用销售商品码 · 配了 → 商品「匹配优先 + 通用兜底 · 不自动建」;
        # 未配 → 精确模式(逐行 auto-create · 老行为不变 · 保护现有付费用户)。
        generic_product_code=(config.get("generic_product_code") or None),
    )

    try:
        if enc_user and enc_pass:
            adapter = MRERPAdapter.from_encrypted(
                encrypted_username=enc_user,
                encrypted_password=enc_pass,
                **common_kwargs,
            )
        elif plain_user and plain_pass:
            adapter = MRERPAdapter(
                username=plain_user,
                password=plain_pass,
                **common_kwargs,
            )
        else:
            return None, {
                "http_status": 401,
                "body": "no_credentials",
                "error_msg": "ERR_NO_CREDS: username/password missing in endpoint.config",
            }
    except ValueError as e:
        return None, {
            "http_status": 401,
            "body": f"decrypt_failed: {e}",
            "error_msg": f"ERR_CRED_DECRYPT: {e}",
        }
    except Exception as e:
        logger.exception("build_mrerp_adapter: adapter construct failed")
        return None, {
            "http_status": 0,
            "body": f"adapter_construct: {type(e).__name__}: {e}",
            "error_msg": f"ERR_UNEXPECTED: adapter construct: {e}",
        }
    return adapter, None


def push_mrerp_history(
    endpoint: Dict[str, Any],
    history_record: Dict[str, Any],
) -> Dict[str, Any]:
    """A1 (Zihao 2026-05-19 拍板) · The real mrerp pusher.

    Unlike push_webhook / push_flowaccount which work on a "standard
    payload" dict, mrerp's adapter wants the raw history + per-tenant
    mappings. This function builds those, drives
    MRERPAdapter.upload_invoice_batch, and translates the ImportResult
    back into the dict shape push_to_endpoint promises its caller
    (success / http_status / response_body / error_msg / elapsed_ms /
    request_body / adapter / + optional mrerp_bill_no for success).

    Returns the same shape as push_to_endpoint so the calling routes
    (manual push / auto push / log retry / batch retry / retry worker)
    don't need to special-case mrerp at all — they just write the
    insert_push_log + update_history_push_status rows from this result.

    Never raises — every failure path returns a dict.
    """
    t0 = time.time()
    config = endpoint.get("config") or {}
    user_id = endpoint.get("user_id")
    endpoint_id = str(endpoint.get("id") or "")

    # ── flatten OCR pages -> top-level fields so MRERPAdapter._extract_buyer
    #    can find buyer_name (P1c · 抽到 flatten_history_for_mrerp · 行为不变).
    history_flat = flatten_history_for_mrerp(history_record)

    # ── tenant_id needed for mappings + product/customer sync attribution.
    try:
        import db as _db
    except Exception as e:
        logger.exception("push_mrerp_history: db import failed")
        return _mrerp_result_dict(
            False,
            0,
            "",
            error_msg=f"ERR_DB_IMPORT: {e}",
            elapsed_ms=int((time.time() - t0) * 1000),
            endpoint_id=endpoint_id,
            history_id=str(history_record.get("id") or ""),
        )

    tenant_id = _db.get_user_tenant_id(user_id) if user_id else None
    if tenant_id:
        history_flat["tenant_id"] = tenant_id

    mappings = load_mrerp_mappings(tenant_id)

    request_body = {
        "history_id": str(history_record.get("id") or ""),
        "invoice_no": history_record.get("invoice_no"),
        "tenant_id": tenant_id,
        "endpoint_id": endpoint_id,
        "adapter": "mrerp",
    }

    def _resp(
        success: bool, http_status: int, body, error_msg: Optional[str] = None, **extra
    ) -> Dict[str, Any]:
        body_str = (
            body if isinstance(body, str) else json.dumps(body, default=str, ensure_ascii=False)
        )
        return {
            "success": success,
            "http_status": http_status,
            "response_body": body_str[:4000],
            "error_msg": error_msg,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "request_body": request_body,
            "adapter": "mrerp",
            **extra,
        }

    # ── build adapter (P1c · 抽到 build_mrerp_adapter · 行为不变:含 playwright
    #    import / cred enc-plain 启发式 / construct;失败回 (None, err) → 同样的 _resp).
    adapter, build_err = build_mrerp_adapter(config)
    if build_err:
        return _resp(
            False,
            build_err["http_status"],
            build_err["body"],
            error_msg=build_err["error_msg"],
        )

    # adapter 已构造成功 → playwright 必可 import · 取异常类用于下方分类。
    from services.erp.mrerp_adapter import (
        MRERPAuthError,
        MRERPTechnicalError,
        MRERPBusinessError,
    )

    # ── run the batch (sync · MUST be off the event loop · the caller
    #    in app.py wraps push_to_endpoint with asyncio.to_thread).
    try:
        with adapter:
            result = adapter.upload_invoice_batch([history_flat], mappings)
    except MRERPAuthError as e:
        return _resp(False, 401, f"auth: {e}", error_msg=f"ERR_AUTH: {e}")
    except MRERPTechnicalError as e:
        return _resp(False, 0, f"technical: {e}", error_msg=f"ERR_TECHNICAL: {e}")
    except MRERPBusinessError as e:
        return _resp(False, 200, f"business: {e}", error_msg=f"ERR_BUSINESS: {e}")
    except Exception as e:
        logger.exception("push_mrerp_history: upload_invoice_batch raised")
        return _resp(
            False, 0, f"unexpected: {type(e).__name__}: {e}", error_msg=f"ERR_UNEXPECTED: {e}"
        )

    # ── translate ImportResult → response dict
    if result.all_success and result.success:
        s = result.success[0]
        body = {
            "ok": True,
            "mrerp_bill_no": s.mrerp_bill_no,
            "invoice_no": s.invoice_no,
            "elapsed_ms": result.elapsed_ms,
            "xlsx_size_bytes": result.xlsx_size_bytes,
        }
        return _resp(True, 200, body, mrerp_bill_no=s.mrerp_bill_no, invoice_no=s.invoice_no)

    # Failure (preflight reject, or report.php หมายเหตุ rejection)
    failed = result.failed[0] if result.failed else None
    reasons = failed.reasons if failed else ["ERR_UNKNOWN_UPLOAD_OUTCOME"]
    friendly = failed.reasons_friendly if failed else []
    screenshot = failed.evidence_screenshot if failed else None
    body = {
        "ok": False,
        "reasons": reasons,
        "reasons_friendly": friendly,
        "screenshot": screenshot,
        "elapsed_ms": result.elapsed_ms,
    }
    return _resp(False, 200, body, error_msg="; ".join(reasons)[:500])


# ============================================================
# MR.ERP DMS (car-sales · ID-card → booking) · 2026-05-31
# Separate adapter from the accounting `mrerp`. Test-connection mirrors
# test_mrerp_endpoint's never-raise contract; the booking push has its
# own route (NOT push_to_endpoint).
# ============================================================

_DMS_DEFAULT_URL = "https://www.mrerp4sme.com/dms/index.php"

_DMS_FRIENDLY = {
    "ERR_UNEXPECTED": {
        "zh": "服务器内部错误,请联系管理员",
        "en": "Internal server error, please contact admin",
        "th": "ข้อผิดพลาดของเซิร์ฟเวอร์ภายใน กรุณาติดต่อผู้ดูแล",
        "zh_TW": "伺服器內部錯誤,請聯絡管理員",
        "ja": "サーバー内部エラーが発生しました。管理者にお問い合わせください",
    },
    "ERR_PLAYWRIGHT_MISSING": {
        "zh": "服务器缺少 Playwright 依赖,请联系运维",
        "en": "Server is missing the Playwright dependency",
        "th": "เซิร์ฟเวอร์ขาดไลบรารี Playwright",
        "zh_TW": "伺服器缺少 Playwright 依賴",
        "ja": "サーバーに Playwright 依存関係がありません。運用担当者にお問い合わせください",
    },
    "ERR_KMS_MISSING": {
        "zh": "服务器加密密钥未配置,请联系运维",
        "en": "Server KMS key is not configured",
        "th": "เซิร์ฟเวอร์ยังไม่ตั้งค่าคีย์เข้ารหัส",
        "zh_TW": "伺服器加密金鑰未設定",
        "ja": "サーバーの暗号化キーが設定されていません。運用担当者にお問い合わせください",
    },
    "ERR_NO_CREDS": {
        "zh": "请输入用户名和密码",
        "en": "Username and password required",
        "th": "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน",
        "zh_TW": "請輸入使用者名稱和密碼",
        "ja": "ユーザー名とパスワードを入力してください",
    },
    "ERR_CRED_DECRYPT": {
        "zh": "凭据解密失败 · 请重新输入用户名和密码",
        "en": "Credential decrypt failed — please re-enter username and password",
        "th": "ถอดรหัสข้อมูลรับรองไม่สำเร็จ",
        "zh_TW": "憑證解密失敗 · 請重新輸入",
        "ja": "認証情報の復号に失敗しました · ユーザー名とパスワードを再入力してください",
    },
    "ERR_DMS_AUTH": {
        "zh": "DMS 登录失败 · 请检查用户名和密码",
        "en": "DMS login failed — check username and password",
        "th": "เข้าสู่ระบบ DMS ไม่สำเร็จ — ตรวจสอบชื่อผู้ใช้และรหัสผ่าน",
        "zh_TW": "DMS 登入失敗 · 請檢查使用者名稱和密碼",
        "ja": "DMS へのログインに失敗しました · ユーザー名とパスワードをご確認ください",
    },
    "ERR_DMS_TECHNICAL": {
        "zh": "连接 DMS 超时或网络异常 · 请稍后重试",
        "en": "DMS connection timed out — please retry",
        "th": "การเชื่อมต่อ DMS หมดเวลา — กรุณาลองใหม่",
        "zh_TW": "連線 DMS 逾時或網路異常 · 請稍後重試",
        "ja": "DMS への接続がタイムアウトまたはネットワーク異常です · しばらくしてから再試行してください",
    },
}


def _dms_friendly(code: str) -> Dict[str, str]:
    return _DMS_FRIENDLY.get(code, _DMS_FRIENDLY["ERR_UNEXPECTED"])


def _dms_resolve_creds(cfg: Dict[str, Any]):
    """Return (plain_user, plain_pass, enc_user, enc_pass) applying the same
    ciphertext-in-plaintext-field heuristic as test_mrerp_endpoint."""
    plain_user = (cfg.get("username") or "").strip()
    plain_pass = cfg.get("password") or ""
    enc_user = (cfg.get("username_enc") or "").strip()
    enc_pass = cfg.get("password_enc") or ""
    try:
        from kms_helper import is_encrypted as _is_enc

        if plain_user and _is_enc(plain_user) and not enc_user:
            enc_user, plain_user = plain_user, ""
        if plain_pass and _is_enc(plain_pass) and not enc_pass:
            enc_pass, plain_pass = plain_pass, ""
    except ImportError:
        pass
    return plain_user, plain_pass, enc_user, enc_pass


def _build_mrerp_dms_adapter(cfg: Dict[str, Any]):
    """Construct a MrerpDmsAdapter from endpoint config (plain or encrypted
    creds). Returns (adapter, None) or (None, fail_dict)."""
    try:
        from services.erp.mrerp_dms_adapter import MrerpDmsAdapter
    except ImportError as e:
        code = "ERR_PLAYWRIGHT_MISSING" if "playwright" in str(e).lower() else "ERR_UNEXPECTED"
        return None, {"error_code": code, "raw": f"{type(e).__name__}: {e}"}

    system_url = (cfg.get("system_url") or _DMS_DEFAULT_URL).strip()
    plain_user, plain_pass, enc_user, enc_pass = _dms_resolve_creds(cfg)
    if not ((plain_user and plain_pass) or (enc_user and enc_pass)):
        return None, {"error_code": "ERR_NO_CREDS", "raw": "username/password missing"}
    try:
        if plain_user and plain_pass:
            adapter = MrerpDmsAdapter(
                system_url=system_url, username=plain_user, password=plain_pass, headless=True
            )
        else:
            adapter = MrerpDmsAdapter.from_encrypted(
                system_url=system_url,
                encrypted_username=enc_user,
                encrypted_password=enc_pass,
                headless=True,
            )
        return adapter, None
    except ImportError as e:
        return None, {"error_code": "ERR_KMS_MISSING", "raw": f"{type(e).__name__}: {e}"}
    except ValueError as e:
        return None, {"error_code": "ERR_CRED_DECRYPT", "raw": f"{type(e).__name__}: {e}"}
    except Exception as e:
        logger.exception("_build_mrerp_dms_adapter failed")
        return None, {"error_code": "ERR_UNEXPECTED", "raw": f"{type(e).__name__}: {e}"}


def test_mrerp_dms_endpoint(config: Dict[str, Any]) -> Dict[str, Any]:
    """DMS connect-wizard health check: login + master-data scrape.

    NEVER raises. Returns the wizard-shaped dict:
        {ok, status, message, adapter, defaults_required, masters, elapsed_ms}
    or on failure {ok: False, error_code, error_friendly, raw_error, masters: {}}.
    Sync — the route wraps this in asyncio.to_thread (Playwright sync API)."""
    import time as _time

    t0 = _time.time()

    def _fail(code: str, raw: str = "") -> Dict[str, Any]:
        return {
            "ok": False,
            "adapter": "mrerp_dms",
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "masters": {},
            "error_code": code,
            "error_friendly": _dms_friendly(code),
            "raw_error": (raw or "")[:300],
        }

    try:
        adapter, build_err = _build_mrerp_dms_adapter(config or {})
        if build_err:
            return _fail(build_err["error_code"], build_err["raw"])
        from services.erp.mrerp_dms_adapter import MrerpDmsAuthError, MrerpDmsTechnicalError

        try:
            with adapter:
                adapter.login()
                return adapter.test_connection()
        except MrerpDmsAuthError as e:
            return _fail("ERR_DMS_AUTH", f"{type(e).__name__}: {e}")
        except MrerpDmsTechnicalError as e:
            return _fail("ERR_DMS_TECHNICAL", f"{type(e).__name__}: {e}")
    except Exception as e:
        logger.exception("test_mrerp_dms_endpoint unexpected failure")
        return _fail("ERR_UNEXPECTED", f"{type(e).__name__}: {e}")


def _id_card_payload_from_dict(id_card: Dict[str, Any]):
    """Build ThaiIdCardPayload + ThaiAddress from the OCR id-card dict the
    route assembled. Missing address master ids stay empty (v1: address text
    is written; DMS province/district ID mapping is future work)."""
    from services.erp.mrerp_dms_models import ThaiAddress, ThaiIdCardPayload

    addr = id_card.get("address") or {}
    address = ThaiAddress(
        house_no=str(addr.get("house_no") or "").strip(),
        province_id=str(addr.get("province_id") or "").strip(),
        province_name=str(addr.get("province") or addr.get("province_name") or "").strip(),
        district_id=str(addr.get("district_id") or "").strip(),
        district_name=str(addr.get("district") or addr.get("district_name") or "").strip(),
        subdistrict_id=str(addr.get("subdistrict_id") or "").strip(),
        subdistrict_name=str(addr.get("subdistrict") or addr.get("subdistrict_name") or "").strip(),
        zipcode_id=str(addr.get("zipcode_id") or "").strip(),
        zipcode=str(addr.get("zipcode") or "").strip(),
        moo=str(addr.get("moo") or "").strip(),
        soi=str(addr.get("soi") or "").strip(),
        road=str(addr.get("road") or "").strip(),
    )
    return ThaiIdCardPayload(
        people_id=str(id_card.get("people_id") or "").strip(),
        first_name=str(id_card.get("first_name") or "").strip(),
        last_name=str(id_card.get("last_name") or "").strip(),
        birthday_be=str(id_card.get("birthday_be") or "").strip(),
        address=address,
        prefix_id=str(id_card.get("prefix_id") or "17").strip() or "17",
        prefix_name=str(id_card.get("prefix_name") or "").strip(),
        phone=str(id_card.get("phone") or "0800000000").strip() or "0800000000",
    )


def push_mrerp_dms_id_card(endpoint: Dict[str, Any], id_card: Dict[str, Any]) -> Dict[str, Any]:
    """Push one Thai ID card into DMS as customer + booking draft.

    Called by dms_routes (NOT push_to_endpoint). Returns a dict shaped for an
    erp_push_logs insert + the route response. NEVER raises. Sync — the route
    wraps in asyncio.to_thread.

    Shape:
        {success, http_status, response_body(dict), error_msg, error_code,
         elapsed_ms, adapter, customer_id, booking_id, booking_no}
    """
    import time as _time

    t0 = _time.time()

    def _resp_dict(ok, code=None, body=None, customer_id="", booking_id="", booking_no=""):
        return {
            "success": ok,
            "http_status": 200 if ok else 0,
            "response_body": body or {},
            "error_msg": None if ok else (code or "ERR_DMS_UNEXPECTED"),
            "error_code": None if ok else (code or "ERR_DMS_UNEXPECTED"),
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "adapter": "mrerp_dms",
            "customer_id": customer_id,
            "booking_id": booking_id,
            "booking_no": booking_no,
        }

    cfg = endpoint.get("config") or {}
    adapter, build_err = _build_mrerp_dms_adapter(cfg)
    if build_err:
        return _resp_dict(False, build_err["error_code"], {"raw_error": build_err["raw"]})

    try:
        from services.erp.mrerp_dms_models import BookingDefaults

        card = _id_card_payload_from_dict(id_card)
        defaults = BookingDefaults.from_config(cfg)
        with adapter:
            result = adapter.push_id_card_booking(card, defaults)
        body = result.to_response_body()
        if result.ok:
            return _resp_dict(
                True,
                body=body,
                customer_id=result.customer_id or "",
                booking_id=result.booking_id or "",
                booking_no=result.booking_no or "",
            )
        body["raw_error"] = (result.error or "")[:300]
        return _resp_dict(False, result.error_code or "ERR_DMS_UNEXPECTED", body)
    except Exception as e:
        logger.exception("push_mrerp_dms_id_card unexpected failure")
        return _resp_dict(False, "ERR_DMS_UNEXPECTED", {"raw_error": f"{type(e).__name__}: {e}"})


def _mrerp_result_dict(
    success: bool,
    http_status: int,
    body: str,
    *,
    error_msg: Optional[str],
    elapsed_ms: int,
    endpoint_id: str,
    history_id: str,
) -> Dict[str, Any]:
    """Minimal early-error response builder · used only when even
    `import db` fails (catastrophic) so we can't build the richer dict."""
    return {
        "success": success,
        "http_status": http_status,
        "response_body": body[:4000],
        "error_msg": error_msg,
        "elapsed_ms": elapsed_ms,
        "request_body": {
            "history_id": history_id,
            "endpoint_id": endpoint_id,
            "adapter": "mrerp",
        },
        "adapter": "mrerp",
    }


ADAPTER_REGISTRY = {
    "webhook": push_webhook,
    "flowaccount": push_flowaccount,
    "mrerp": push_mrerp,
    "mrerp_dms": push_mrerp_dms,
}

# Adapters whose endpoint.config carries Fernet-encrypted credentials.
# UI must never round-trip the raw values; the test-connection +
# upload routes decrypt at the last moment.
ENCRYPTED_CRED_ADAPTERS = {"mrerp", "mrerp_dms"}


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

    # DMS guard (2026-05-31) · mrerp_dms is a car-sales ID-card→booking
    # adapter, NEVER an invoice-history target. Reject hard so the invoice
    # auto-push / manual-push paths can't misroute an invoice into DMS.
    # The real DMS flow is POST /api/dms/id-card-booking. Named guard:
    #     test_push_to_endpoint_rejects_mrerp_dms_invoice
    if adapter == "mrerp_dms":
        return {
            "success": False,
            "http_status": 0,
            "response_body": "",
            "error_msg": "ERR_DMS_NOT_INVOICE_ENDPOINT",
            "elapsed_ms": 0,
            "request_body": None,
            "adapter": adapter,
        }

    # A1 (Zihao 2026-05-19 拍板) · MR.ERP early-route.
    #
    # The legacy (config, payload) adapter shape doesn't fit MR.ERP because
    # the batch adapter needs the raw history dict + per-tenant mappings.
    # Route mrerp through push_mrerp_history (the real implementation)
    # before we build the standard payload — this completely bypasses the
    # push_mrerp stub in ADAPTER_REGISTRY, which exists only as a tripwire
    # for guard tests.
    #
    # Named guard test that locks this in:
    #     test_push_to_endpoint_route_calls_mrerp_adapter_not_stub
    if adapter == "mrerp":
        return push_mrerp_history(endpoint, history_record)

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
        return {
            "success": False,
            "http_status": 0,
            "response_body": "",
            "error_msg": f"unknown adapter: {adapter}",
        }

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
