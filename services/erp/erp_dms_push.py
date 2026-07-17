# -*- coding: utf-8 -*-
"""
erp_dms_push.py · MR.ERP DMS（车销 / 身份证→订车单）推送 + 连接测试

DMS 连接测试 + 凭据解析 + 身份证字段映射：_DMS_DEFAULT_URL/_DMS_FRIENDLY/
_dms_friendly/_dms_resolve_creds/_build_mrerp_dms_adapter/test_mrerp_dms_endpoint/
_id_card_payload_from_dict。零 erp_push 内部依赖（service import 全 lazy）。
erp_push 顶部 re-export 回原命名空间 → dms_routes/erp_routes（_erp.test_mrerp_dms_endpoint）
+ push_mrerp_history（用 _mrerp_result_dict）。
身份证→订车单的实际建单走两步流 services/erp/erp_dms_intake.py（dms_routes 的
/api/dms/id-card/recognize + /push），不在本模块。
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
    "ERR_DMS_ADMIN_AUTH": {
        "zh": "DMS 管理员凭据登录失败 · 请检查管理员用户名和密码",
        "en": "DMS admin credential login failed — check the admin username and password",
        "th": "เข้าสู่ระบบด้วยบัญชีผู้ดูแล DMS ไม่สำเร็จ — ตรวจสอบชื่อผู้ใช้และรหัสผ่านผู้ดูแล",
        "zh_TW": "DMS 管理員憑證登入失敗 · 請檢查管理員使用者名稱和密碼",
        "ja": "DMS 管理者資格情報でのログインに失敗しました · 管理者のユーザー名とパスワードをご確認ください",
    },
    "ERR_DMS_CUSTOMER_SAVE": {
        "zh": "保存客户到 DMS 失败 · 请检查字段后重试",
        "en": "Failed to save the customer to DMS — check the fields and retry",
        "th": "บันทึกลูกค้าเข้า DMS ไม่สำเร็จ — ตรวจสอบข้อมูลแล้วลองใหม่",
        "zh_TW": "儲存客戶到 DMS 失敗 · 請檢查欄位後重試",
        "ja": "DMS への顧客保存に失敗しました · 項目を確認して再試行してください",
    },
    "ERR_DMS_IMPORT": {
        "zh": "建订车单失败 · 请稍后重试",
        "en": "Failed to create the booking — please retry",
        "th": "สร้างใบจองรถไม่สำเร็จ — กรุณาลองใหม่",
        "zh_TW": "建立訂車單失敗 · 請稍後重試",
        "ja": "予約の作成に失敗しました · 再試行してください",
    },
    "ERR_DMS_IMPORT_REPORT": {
        "zh": "订车单导入被 DMS 拒绝 · 请检查订车资料",
        "en": "DMS rejected the booking import — check the booking details",
        "th": "DMS ปฏิเสธการนำเข้าใบจอง — ตรวจสอบรายละเอียดการจอง",
        "zh_TW": "訂車單匯入被 DMS 拒絕 · 請檢查訂車資料",
        "ja": "DMS が予約取込を拒否しました · 予約内容をご確認ください",
    },
    "ERR_DMS_BOOKING_PATCH": {
        "zh": "回填订车单资料失败 · 请稍后重试",
        "en": "Failed to fill in the booking details — please retry",
        "th": "เติมข้อมูลใบจองไม่สำเร็จ — กรุณาลองใหม่",
        "zh_TW": "回填訂車單資料失敗 · 請稍後重試",
        "ja": "予約情報の入力に失敗しました · 再試行してください",
    },
    "ERR_DMS_TEMPLATE": {
        "zh": "下载订车单模板失败 · 请稍后重试",
        "en": "Failed to download the booking template — please retry",
        "th": "ดาวน์โหลดเทมเพลตใบจองไม่สำเร็จ — กรุณาลองใหม่",
        "zh_TW": "下載訂車單範本失敗 · 請稍後重試",
        "ja": "予約テンプレートのダウンロードに失敗しました · 再試行してください",
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


def _dms_resolve_admin_creds(cfg: Dict[str, Any]):
    """admin 凭据组解析,与 _dms_resolve_creds 同一 ciphertext-in-plaintext 启发式。
    未配 admin 时四值皆空。"""
    plain_user = (cfg.get("admin_username") or "").strip()
    plain_pass = cfg.get("admin_password") or ""
    enc_user = (cfg.get("admin_username_enc") or "").strip()
    enc_pass = cfg.get("admin_password_enc") or ""
    try:
        from core.kms_helper import is_encrypted as _is_enc

        if plain_user and _is_enc(plain_user) and not enc_user:
            enc_user, plain_user = plain_user, ""
        if plain_pass and _is_enc(plain_pass) and not enc_pass:
            enc_pass, plain_pass = plain_pass, ""
    except ImportError:
        pass
    return plain_user, plain_pass, enc_user, enc_pass


def _dms_admin_kwargs(cfg: Dict[str, Any]) -> Dict[str, str]:
    """把 admin 凭据组解析成传给适配器的明文 kwargs。没配 admin → {}(单凭据路径
    逐字节不变)。加密态就地解密(ValueError/ImportError 交由外层 build 兜成
    ERR_CRED_DECRYPT/ERR_KMS_MISSING)。"""
    plain_user, plain_pass, enc_user, enc_pass = _dms_resolve_admin_creds(cfg)
    if plain_user and plain_pass:
        return {"admin_username": plain_user, "admin_password": plain_pass}
    if enc_user and enc_pass:
        from core.kms_helper import decrypt_str

        return {"admin_username": decrypt_str(enc_user), "admin_password": decrypt_str(enc_pass)}
    return {}


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
        admin_kwargs = _dms_admin_kwargs(cfg)
        if plain_user and plain_pass:
            adapter = MrerpDmsAdapter(
                system_url=system_url,
                username=plain_user,
                password=plain_pass,
                headless=True,
                **admin_kwargs,
            )
        else:
            adapter = MrerpDmsAdapter.from_encrypted(
                system_url=system_url,
                encrypted_username=enc_user,
                encrypted_password=enc_pass,
                headless=True,
                **admin_kwargs,
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
    booking flow has its own route (POST /api/dms/id-card/recognize + /push).
    `push_to_endpoint` early-rejects adapter='mrerp_dms'
    (ERR_DMS_NOT_INVOICE_ENDPOINT) so an invoice history can never be
    misrouted into DMS. This stub exists only so endpoint creation
    (which validates `adapter in ADAPTER_REGISTRY`) accepts mrerp_dms; if it
    is ever actually reached, that early-reject regressed.

    Guard test: test_push_mrerp_dms_stub_refuses (+ the not-invoice route
    test). Don't remove the stub even though the early-reject shadows it."""
    return (
        False,
        0,
        "mrerp_dms is not an invoice push target; use POST /api/dms/id-card/push",
    )
