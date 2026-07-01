# -*- coding: utf-8 -*-
"""
erp_mrerp_listing.py · MR.ERP 连接测试(HTTP 直写 · 只读)

S5 后 test-connection 改走 HTTP 会话(不再 Playwright):登录 → 抓 selectdb.php 列
该账号可选账套(年度账套)供连接向导「选套账」步用。永不抛(契约:任何异常都包成
{ok:False,...} 让向导错误条有东西渲染,绝不冒 500)。
erp_push 顶部 re-export 回原命名空间 → 消费方 + dispatch 单测 0 改动。
"""

from __future__ import annotations

import logging
import time as _time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_URL = "https://www.mrerp4sme.com"

# get_friendly catalog 不可用时的兜底(覆盖同 4 语,渲染层不必特判)。
_FALLBACK_FRIENDLY = {
    "ERR_UNEXPECTED": {
        "zh": "服务器内部错误,请联系管理员",
        "en": "Internal server error, please contact admin",
        "th": "ข้อผิดพลาดของเซิร์ฟเวอร์ภายใน กรุณาติดต่อผู้ดูแล",
        "zh_TW": "伺服器內部錯誤,請聯絡管理員",
    },
    "ERR_AUTH": {
        "zh": "账号或密码错误 · 请检查后重试",
        "en": "Wrong username or password",
        "th": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
        "zh_TW": "帳號或密碼錯誤",
    },
    "ERR_TECHNICAL": {
        "zh": "连接 MR.ERP 超时或网络异常 · 请稍后重试",
        "en": "MR.ERP timed out or network error",
        "th": "เชื่อมต่อ MR.ERP หมดเวลา",
        "zh_TW": "連線 MR.ERP 逾時或網路異常",
    },
    "ERR_KMS_MISSING": {
        "zh": "服务器加密密钥未配置,请联系运维",
        "en": "Server KMS key (PEARNLY_KMS_KEY) is not configured",
        "th": "เซิร์ฟเวอร์ยังไม่ตั้งค่าคีย์เข้ารหัส",
        "zh_TW": "伺服器加密金鑰未設定",
    },
    "ERR_CRED_DECRYPT": {
        "zh": "凭据解密失败 · 请重新输入用户名和密码",
        "en": "Credential decrypt failed — please re-enter username and password",
        "th": "ถอดรหัสข้อมูลรับรองไม่สำเร็จ",
        "zh_TW": "憑證解密失敗 · 請重新輸入",
    },
    "ERR_NO_CREDS": {
        "zh": "请输入用户名和密码",
        "en": "Username and password required",
        "th": "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน",
        "zh_TW": "請輸入使用者名稱和密碼",
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


def _resolve_creds(
    cfg: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str], Optional[Tuple[str, str]]]:
    """解析明文/密文两形态凭据 → (username, password, err)。err 非空表示失败(code, raw)。

    密文(edit saved endpoint 预填 Fernet)靠 is_encrypted 识别后 decrypt_str 还原。
    """
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
        pass  # kms 坏了仍能走明文路

    if plain_user and plain_pass:
        return plain_user, plain_pass, None
    if enc_user and enc_pass:
        try:
            from core.kms_helper import decrypt_str

            return decrypt_str(enc_user), decrypt_str(enc_pass), None
        except ImportError as e:
            return None, None, ("ERR_KMS_MISSING", f"{type(e).__name__}: {e}")
        except Exception as e:
            return None, None, ("ERR_CRED_DECRYPT", f"{type(e).__name__}: {e}")
    return None, None, ("ERR_NO_CREDS", "username/password missing (neither plain nor encrypted)")


def test_mrerp_endpoint(config: Dict[str, Any]) -> Dict[str, Any]:
    """MR.ERP 连接测试 · 登录并列账套(HTTP · 永不抛)。

    接受两种凭据形态:向导明文(username/password)或已存端点密文(username_enc/
    password_enc)· 明文优先。返回向导可直接渲染的 dict:
        ok bool · elapsed_ms int · companies [{label, comidyear, seldb}]
        error_code / error_friendly / raw_error(失败时)
    companies 即该账号可选账套,供向导「选套账」下拉。
    """
    t0 = _time.time()

    def _elapsed() -> int:
        return int((_time.time() - t0) * 1000)

    def _fail(code: str, raw: str = "") -> Dict[str, Any]:
        return {
            "ok": False,
            "elapsed_ms": _elapsed(),
            "companies": [],
            "error_code": code,
            "error_friendly": _friendly(code),
            "raw_error": (raw or "")[:300],
        }

    try:
        from services.erp.exceptions import MRERPAuthError, MRERPTechnicalError
        from services.erp.mrerp_http.session import MrErpSession

        cfg = config or {}
        login_url = (cfg.get("system_url") or _DEFAULT_URL).strip()
        user, pw, cred_err = _resolve_creds(cfg)
        if cred_err:
            return _fail(cred_err[0], cred_err[1])

        sess: Optional[MrErpSession] = None
        try:
            sess = MrErpSession(
                login_url=login_url,
                username=user,
                password=pw,
                comidyear=str(cfg.get("comidyear") or "6"),
                seldb=str(cfg.get("seldb") or "1"),
            )
            sets = sess.list_account_sets()  # 登录 + 列账套(selectdb 不鉴权,恒可列)
            # ★真凭据校验:selectdb 任何会话都列账套,唯有进 mainmenu 才鉴权。用列出的第一个
            #   账套试选,凭据错则被踢回登录页 → MRERPAuthError(known-facts §2)。
            if sets:
                sess.comidyear, sess.seldb = sets[0]["comidyear"], sets[0]["seldb"]
            sess.select_company()
        except MRERPAuthError as e:
            return _fail("ERR_AUTH", str(e))
        except MRERPTechnicalError as e:
            return _fail("ERR_TECHNICAL", str(e))
        finally:
            if sess is not None:
                try:
                    sess.session.close()
                except Exception:
                    pass

        companies: List[Dict[str, str]] = [
            {"label": s["name"][:80], "comidyear": s["comidyear"], "seldb": s["seldb"]}
            for s in sets
        ]
        return {
            "ok": True,
            "elapsed_ms": _elapsed(),
            "companies": companies,
            "error_code": None,
            "error_friendly": None,
            "raw_error": None,
        }
    except Exception as e:  # 契约:永不抛
        logger.exception("test_mrerp_endpoint failure")
        return _fail("ERR_UNEXPECTED", f"{type(e).__name__}: {e}")
