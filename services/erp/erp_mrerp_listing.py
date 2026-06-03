# -*- coding: utf-8 -*-
"""
erp_mrerp_listing.py · MR.ERP 连接测试 + 客户/产品拉取(只读)

从 erp_push.py 抽出(REFACTOR-WB-modularize E1 · verbatim 搬家 0 逻辑改)。
test_mrerp_endpoint / list_mrerp_customers / list_mrerp_products —— 均内部 lazy-import
MRERPAdapter·零 erp_push 内部依赖。erp_push 顶部 re-export 回原命名空间→
`import erp_push as _erp` 消费方 + dispatch 单测(_erp.test_mrerp_endpoint)0 改动。
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


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
                MRERPAdapter,
                MRERPAuthError,
                MRERPBusinessError,
                MRERPTechnicalError,
            )
        except ImportError as e:
            logger.exception("test_mrerp_endpoint import failure")
            msg = f"{type(e).__name__}: {e}"
            code = "ERR_PLAYWRIGHT_MISSING" if "playwright" in str(e).lower() else "ERR_UNEXPECTED"
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
            from core.kms_helper import is_encrypted as _is_enc

            if plain_user and _is_enc(plain_user) and not enc_user:
                enc_user, plain_user = plain_user, ""
            if plain_pass and _is_enc(plain_pass) and not enc_pass:
                enc_pass, plain_pass = plain_pass, ""
        except ImportError:
            # kms_helper is broken; we can still serve the plaintext path.
            pass

        if not ((plain_user and plain_pass) or (enc_user and enc_pass)):
            return _fail("ERR_NO_CREDS", "username/password missing (neither plain nor encrypted)")

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
                        companies.append(
                            {
                                "label": label[:80],
                                "comidyear": m.group("y"),
                                "seldb": m.group("s"),
                            }
                        )
                    # If the regex finds nothing, fall back to a single
                    # configured entry so the wizard at least shows the
                    # tenant's saved choice.
                    if not companies:
                        companies.append(
                            {
                                "label": f"TEST{comidyear}-{seldb}",
                                "comidyear": comidyear,
                                "seldb": seldb,
                            }
                        )
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
