# -*- coding: utf-8 -*-
"""
erp_dms_push.py · MR.ERP DMS（车销 / 身份证→订车单）推送 + 连接测试

从 erp_push.py 抽出（REFACTOR-WB-modularize E3 · verbatim 搬家 0 逻辑改）。
DMS 全段：_DMS_DEFAULT_URL/_DMS_FRIENDLY/_dms_friendly/_dms_resolve_creds/
_build_mrerp_dms_adapter/test_mrerp_dms_endpoint/_id_card_payload_from_dict/
push_mrerp_dms_id_card/_mrerp_result_dict。零 erp_push 内部依赖（service import 全 lazy）。
erp_push 顶部 re-export 回原命名空间 → dms_routes/erp_routes（_erp.push_mrerp_dms_id_card /
_erp.test_mrerp_dms_endpoint）+ push_mrerp_history（用 _mrerp_result_dict）0 改动。
⚠️ DMS 不是发票推送目标：push_to_endpoint 对 adapter=mrerp_dms 硬拒（防误推）· 此模块走
自己的 dms_routes，与 push_to_endpoint 无关。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

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
        from core.kms_helper import is_encrypted as _is_enc

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
