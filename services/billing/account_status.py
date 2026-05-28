# -*- coding: utf-8 -*-
"""
services/billing/account_status.py · 计费豁免 / 状态聚合 / BKK 月锚(REFACTOR-B2)

从 db.py 抽出的「Credits 计费业务层」前置查询(v0.21):
- _bkk_year_month   Asia/Bangkok UTC+7 月度统计锚("YYYY-MM")· monthly_page_usage 用
- is_user_billing_exempt   白名单查询 · 5min LRU cache · 进程内
- get_billing_status_combined   一次 SELECT 拿 is_exempt + balance + pages_used
                                  取代 v0.20 三次独立查询(DB roundtrip 1 vs 3)

E2E 覆盖(spec 16 OCR + spec 11 charge-ocr-closure):recognize 端点前置走
db.get_billing_status_combined 拿 balance · charge_ocr 跳过豁免账号。

范式(ADR-007):import db + 运行时 db.get_cursor()。db.py 文件尾 re-export 3 个对外
名字(含 _bkk_year_month 私有 helper 也 re-export · charge_ocr/charge_ocr_async 内部
bare 调 · 必须留在 db 模块命名空间)。
"""

from __future__ import annotations

import logging
import time as _time
from datetime import datetime as _dt, timedelta as _td, timezone as _tz

import db

logger = logging.getLogger(__name__)

_BKK_TZ = _tz(_td(hours=7))

# 白名单 LRU cache(进程内 · 5 分钟 TTL · 减少 DB 压力)
_EXEMPT_CACHE: dict = {}
_EXEMPT_CACHE_TTL = 300


def _bkk_year_month() -> str:
    """Asia/Bangkok timezone · YYYY-MM · 月度统计锚定 UTC+7."""
    return _dt.now(_BKK_TZ).strftime("%Y-%m")


def is_user_billing_exempt(user_id) -> bool:
    """v0.21 · 5 分钟 cache · 白名单极少变 · 减少 DB roundtrip"""
    if not user_id:
        return False
    key = str(user_id)
    now = _time.time()
    hit = _EXEMPT_CACHE.get(key)
    if hit and hit[1] > now:
        return hit[0]
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT COALESCE(is_billing_exempt, FALSE) AS x "
                "FROM users WHERE id = %s::uuid LIMIT 1",
                (str(user_id),),
            )
            row = cur.fetchone()
            result = bool(row["x"]) if row else False
            _EXEMPT_CACHE[key] = (result, now + _EXEMPT_CACHE_TTL)
            if len(_EXEMPT_CACHE) > 5000:
                # 限制 cache 体积 · 简单清理
                _EXEMPT_CACHE.clear()
            return result
    except Exception as e:
        logger.warning(f"is_user_billing_exempt error user={user_id}: {e}")
        return False


def get_billing_status_combined(user_id, tenant_id) -> dict:
    """v0.21 · 一次 SELECT 拿 is_exempt + balance + pages_used_this_month
    取代 v0.20 的 3 次独立查询 · DB roundtrip 从 3 → 1。
    返: {allowed, is_exempt, balance_thb, pages_used_this_month, error_code}
    """
    # 白名单走 cache(不查 DB · 0 RTT)
    if is_user_billing_exempt(user_id):
        return {
            "allowed": True,
            "is_exempt": True,
            "balance_thb": 0.0,
            "pages_used_this_month": 0,
            "error_code": None,
        }
    if not tenant_id:
        return {
            "allowed": False,
            "is_exempt": False,
            "balance_thb": 0.0,
            "pages_used_this_month": 0,
            "error_code": "no_tenant",
        }
    try:
        ym = _bkk_year_month()
        with db.get_cursor() as cur:
            # 一次 SELECT 合并两个 LEFT JOIN · 一次 DB roundtrip
            cur.execute(
                """
                SELECT
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_used
                FROM (SELECT 1) AS dummy
                LEFT JOIN tenant_credits tc ON tc.tenant_id = %s::uuid
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = %s::uuid AND mpu.year_month = %s
                LIMIT 1
            """,
                (str(tenant_id), str(tenant_id), ym),
            )
            row = cur.fetchone()
            bal = float(row["balance_thb"] if row else 0)
            used = int(row["pages_used"] if row else 0)
        if bal <= 0:
            return {
                "allowed": False,
                "is_exempt": False,
                "balance_thb": bal,
                "pages_used_this_month": used,
                "error_code": "insufficient_balance",
            }
        return {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": bal,
            "pages_used_this_month": used,
            "error_code": None,
        }
    except Exception as e:
        logger.warning(f"get_billing_status_combined error tenant={tenant_id}: {e}")
        # 失败时不阻塞 OCR(降级到允许 · 但 log 警报)
        return {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": 0.0,
            "pages_used_this_month": 0,
            "error_code": "lookup_error",
        }
