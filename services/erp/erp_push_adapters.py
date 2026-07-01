# -*- coding: utf-8 -*-
"""MR.ERP 适配器构造 + 主数据映射加载(从 erp_push 抽出 · 0 逻辑改 · 让 erp_push<500)。

单张(push_mrerp_history)和批量(push_dispatch.dispatch_endpoint_batch)共用这两个函数;
erp_push.py re-export 二者,调用方与测试经 erp_push.<name> 访问的契约不变。
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


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
    """从 endpoint.config 构造发票推送 adapter(HTTP 直写 · S5 删旧 Playwright 发票路后唯一路径)。

    返回 (adapter, err):
      - 成功 → (adapter, None)
      - 失败 → (None, {"http_status", "body", "error_msg"}) · caller 直接拼成 push 结果 dict
    单张(push_mrerp_history)和批量(push_dispatch.dispatch_endpoint_batch)共用此构造逻辑。
    ★发票推送恒走 HTTP 直写(销/采/库存 + 客户/供应商/商品自建 + 科目安全阀)。Playwright
    MRERPAdapter 仅保留给「测试连接」+「列客户/商品」两个尚未迁 HTTP 的功能(见 erp_mrerp_*)。
    """
    from services.erp.mrerp_http import MrErpHttpAdapter as AdapterCls

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

    # HTTP 直写只认这几项(自建客户/供应商/商品在 adapter 内部走 autocreate,不再靠 Playwright
    # 的 enable_master_data_sync/seed_*/generic_product_code)· doc_type 默认 sales_credit,
    # 方向自动路由(销/采/库存)是 S2 收尾:choose_doc_type 接进 push 流 + 批量按 doc_type 分组。
    common_kwargs: Dict[str, Any] = dict(
        login_url=(config.get("system_url") or "https://www.mrerp4sme.com").strip(),
        comidyear=str(config.get("comidyear") or "6"),
        seldb=str(config.get("seldb") or "1"),
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
