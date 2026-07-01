# -*- coding: utf-8 -*-
"""MR.ERP 适配器构造 + 主数据映射加载(从 erp_push 抽出 · 0 逻辑改 · 让 erp_push<500)。

单张(push_mrerp_history)和批量(push_dispatch.dispatch_endpoint_batch)共用这两个函数;
erp_push.py re-export 二者,调用方与测试经 erp_push.<name> 访问的契约不变。
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _mrerp_transport(config: Dict[str, Any]) -> str:
    """直写(http)还是 Playwright · endpoint.config.transport 优先,其次 env,默认 playwright(安全)。
    S1 灰度用:MRERP_TRANSPORT=http 或单 endpoint 配 transport=http 切直写,一秒回退。"""
    return (
        str(config.get("transport") or "").strip().lower()
        or os.getenv("MRERP_TRANSPORT", "").strip().lower()
        or "playwright"
    )


def load_mrerp_mappings(tenant_id: Optional[str]) -> Dict[str, Any]:
    """P1c · 取该 tenant 的 MR.ERP 主数据映射 bundle(clients/products/accounts/taxes)。
    无 tenant → 空 bundle(行为不变 · 从 push_mrerp_history 抽出)。"""
    try:
        from core import db as _db
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
    # 选传输 → 定 adapter 类。http 直写不碰 Playwright(为将来删 Playwright 铺路)。
    transport = _mrerp_transport(config)
    if transport == "http":
        from services.erp.mrerp_http import MrErpHttpAdapter as AdapterCls
    else:
        # lazy adapter import (Playwright may be missing on dev boxes).
        try:
            from services.erp.mrerp_adapter import MRERPAdapter as AdapterCls
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
        from core.kms_helper import is_encrypted as _is_enc

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
            adapter = AdapterCls.from_encrypted(
                encrypted_username=enc_user,
                encrypted_password=enc_pass,
                **common_kwargs,
            )
        elif plain_user and plain_pass:
            adapter = AdapterCls(
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
