# -*- coding: utf-8 -*-
"""
erp_mrerp_crud.py · MR.ERP 客户/产品列表拉取(只读)

从 erp_mrerp_listing.py 再拆（REFACTOR-WB-modularize E1b · verbatim 搬家 0 逻辑改）·
保持 erp_mrerp_listing < 500。list_mrerp_customers / list_mrerp_products 均 lazy-import
MRERPAdapter·零内部依赖。erp_push 顶部 re-export 回原命名空间(调用方 0 改动)。
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


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
        MRERPAdapter,
        MRERPAuthError,
        MRERPBusinessError,
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
            "ok": False,
            "elapsed_ms": 0,
            "customers": [],
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
            "customers": [],
            "error_code": "ERR_CRED_DECRYPT",
            "error_friendly": get_friendly("ERR_CRED_DECRYPT"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    try:
        with adapter:
            svc = MRERPCustomerSyncService(adapter)
            # picker 下拉:拉全量(用户主动点·可缓存·不在推送热路径)。
            rows = svc._fetch_listing(max_pages=400)
        customers = [
            {
                "code": r.code,
                "name": r.name,
                "type_name": r.type_name,
                "prefix": r.prefix,
            }
            for r in rows
        ]
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
        MRERPAdapter,
        MRERPAuthError,
        MRERPBusinessError,
        MRERPTechnicalError,
    )
    from services.erp.mrerp_product_sync import MRERPProductSyncService
    from services.erp.mrerp_business_friendly import get_friendly

    cfg = config or {}
    login_url = (cfg.get("system_url") or "https://www.mrerp4sme.com").strip()
    comidyear = str(cfg.get("comidyear") or "6")
    seldb = str(cfg.get("seldb") or "1")

    # P1「开箱即用」· 向导探测路由(/api/erp/wizard/products)在「保存连接前」
    # 用内存「明文」凭据拉商品做智能预选,而 saved-endpoint 的 /products 路由
    # 仍传 Fernet「密文」。这里镜像 test_mrerp_endpoint 的双形态启发式:
    # 明文优先,但形如 gAAAAA* 的值仍走解密路径(覆盖「编辑已存连接」时表单
    # 预填的密文)。两条调用路径共用本函数,行为对已存连接不变(只多支持明文)。
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

    if not ((plain_user and plain_pass) or (enc_user and enc_pass)):
        return {
            "ok": False,
            "elapsed_ms": 0,
            "products": [],
            "error_code": "ERR_NO_CREDS",
            "error_friendly": get_friendly("ERR_NO_CREDS"),
            "raw_error": "username/password missing (neither plain nor encrypted)",
        }

    t0 = _time.time()
    try:
        if plain_user and plain_pass:
            adapter = MRERPAdapter(
                login_url=login_url,
                username=plain_user,
                password=plain_pass,
                comidyear=comidyear,
                seldb=seldb,
                headless=True,
                retry_attempts=1,
                retry_delays_seconds=(0.5,),
            )
        else:
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
            "products": [],
            "error_code": "ERR_CRED_DECRYPT",
            "error_friendly": get_friendly("ERR_CRED_DECRYPT"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    try:
        with adapter:
            svc = MRERPProductSyncService(adapter)
            # picker 下拉:拉全量(用户主动点·可缓存·不在推送热路径)。
            rows = svc._fetch_listing(max_pages=400)
        products = [
            {
                "code": r.code,
                "name": r.name,
                "category_code": r.category_code,
                "category_name": r.category_name,
            }
            for r in rows
        ]
    except MRERPAuthError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "products": [],
            "error_code": "ERR_AUTH",
            "error_friendly": get_friendly("ERR_AUTH"),
            "raw_error": str(e)[:300],
        }
    except MRERPTechnicalError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "products": [],
            "error_code": "ERR_TECHNICAL",
            "error_friendly": get_friendly("ERR_TECHNICAL"),
            "raw_error": str(e)[:300],
        }
    except MRERPBusinessError as e:
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "products": [],
            "error_code": "ERR_BUSINESS",
            "error_friendly": get_friendly("ERR_BUSINESS"),
            "raw_error": str(e)[:300],
        }
    except Exception as e:
        logger.exception("list_mrerp_products unexpected error")
        return {
            "ok": False,
            "elapsed_ms": int((_time.time() - t0) * 1000),
            "products": [],
            "error_code": "ERR_UNEXPECTED",
            "error_friendly": get_friendly("ERR_UNEXPECTED"),
            "raw_error": f"{type(e).__name__}: {str(e)[:200]}",
        }

    return {
        "ok": True,
        "elapsed_ms": int((_time.time() - t0) * 1000),
        "products": products,
        "error_code": None,
        "error_friendly": None,
        "raw_error": None,
    }
