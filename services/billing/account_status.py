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
from decimal import Decimal as _Dec

from core import db

logger = logging.getLogger(__name__)

_BKK_TZ = _tz(_td(hours=7))

# 「我们查不出来」的码。与 insufficient_balance(「用户没钱」)必须两条码两条出路:前者 503
# 稍后再试、后者 402 去充值。把系统故障报成用户没钱 = 让会计去充一笔本来就够的钱。
LOOKUP_ERROR = "lookup_error"

# 白名单 LRU cache(进程内 · 5 分钟 TTL · 减少 DB 压力)
_EXEMPT_CACHE: dict = {}
_EXEMPT_CACHE_TTL = 300


def lookup_failed(status) -> bool:
    """这次是「查不出来」而不是「余额不足」。调用方据此分派 503 / 402,别把两件事合成一句话。"""
    return (status or {}).get("error_code") == LOOKUP_ERROR


def can_cover_estimate(status: dict, pdf_units: int, excel_chars: int = 0) -> bool:
    """余额/套餐额度是否盖得住这批的预检估价(纯判断 · 无 DB 调用)。

    估价 = PDF 阶梯价 + Excel 字符折算成张 × 基准张价(见 pricing.estimate_recon_cost_thb,
    与事后实扣同口径)。套餐额度能整个吃下 → 免费放行(不看余额);有套餐但额度不足 → 超额
    部分按套餐 over_rate 估;无套餐 → 余额必须 ≥ 整批估价。豁免由调用方先判,这里只回答
    「钱够不够」。余额不足却放行 = 大 Excel 打穿余额透支(生产实锤 2026-08-12)。
    """
    if status.get("is_exempt"):
        return True
    if not status.get("allowed"):
        return False  # 余额≤0 且无套餐额度 → 一律不够(既有判据保留)
    used = int(status.get("pages_used_this_month") or 0)
    est_cost = float(db.estimate_recon_cost_thb(used, int(pdf_units or 0), int(excel_chars or 0)))
    sub = status.get("subscription")
    quota_pages = int(pdf_units or 0) + db.doc_quota_pages(int(excel_chars or 0))
    if sub is not None and int(sub.get("remaining", 0)) >= quota_pages:
        return True  # 套餐额度全覆盖 → 免费
    payable = est_cost
    if sub is not None:
        billable = max(0, quota_pages - int(sub.get("remaining", 0)))
        payable = float(_Dec(str(billable)) * _Dec(str(sub.get("over_rate", 1.5))))
    return float(status.get("balance_thb", 0.0)) >= payable


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

    error_code 两种拒绝必须分得清,调用方据此走不同出路:
      insufficient_balance = 用户没钱(去充值 · 402)
      lookup_error         = 我们查不出来(稍后再试 · 503)· 不许报成用户没钱
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
        with db.get_cursor_rls(tenant_id=str(tenant_id)) as cur:
            # 一次 SELECT 合并三个 LEFT JOIN · 一次 DB roundtrip
            # 用量 = 按量表 + 活跃订阅本周期用量(两计数器互斥不重复计 · 见
            # services/billing/subscription.py active_sub_usage_join_sql)
            cur.execute(
                f"""
                SELECT
                    COALESCE(tc.balance_thb, 0) AS balance_thb,
                    COALESCE(mpu.pages_used, 0) AS pages_used,
                    COALESCE(ts.pages_used_this_cycle, 0) AS sub_pages_used
                FROM (SELECT 1) AS dummy
                LEFT JOIN tenant_credits tc ON tc.tenant_id = %s::uuid
                LEFT JOIN monthly_page_usage mpu
                       ON mpu.tenant_id = %s::uuid AND mpu.year_month = %s
                {db.active_sub_usage_join_sql("ts", "%s::uuid")}
                LIMIT 1
            """,
                (str(tenant_id), str(tenant_id), ym, str(tenant_id)),
            )
            row = cur.fetchone()
            bal = float(row["balance_thb"] if row else 0)
            used = int(row["pages_used"] if row else 0) + int(
                (row.get("sub_pages_used") if row else 0) or 0
            )

        # 有有效订阅:套餐内有剩余额度即放行(额度免费 · 不看余额);额度耗尽才要余额>0 扣超额。
        # 单独 try:订阅查询失败按"无套餐"处理(走下方余额闸)。余额这一手已经查到了,不该让
        # 订阅这一手的故障冒到外层被判成 lookup_error —— 那会把「余额够、能跑」的人也拒掉。
        try:
            sub = db.get_active_subscription(tenant_id)
        except Exception as _se:
            logger.warning(f"get_active_subscription error tenant={tenant_id}: {_se}")
            sub = None
        if sub is not None:
            allowed = sub["remaining"] > 0 or bal > 0
            return {
                "allowed": allowed,
                "is_exempt": False,
                "balance_thb": bal,
                "pages_used_this_month": used,
                "subscription": sub,
                "error_code": None if allowed else "insufficient_balance",
            }

        if bal <= 0:
            return {
                "allowed": False,
                "is_exempt": False,
                "balance_thb": bal,
                "pages_used_this_month": used,
                "subscription": None,
                "error_code": "insufficient_balance",
            }
        return {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": bal,
            "pages_used_this_month": used,
            "subscription": None,
            "error_code": None,
        }
    except Exception as e:
        # 钱闸 fail-closed:这里是全站计费的单一事实源,DB 抖一下就放行 = 全站免费,且损失
        # 不可逆也不可发现(服务已交付、钱收不回、事后无从追认谁白嫖了)。拒绝的代价只是用户
        # 重试一次,可逆。故「查不到计费状态」一律不放行。
        # 与 services/pos/entitlements.pos_provision_allowed 的 fail-open 有意相反——那条闸
        # 「绝不误伤任何在闸开启前就存在的租户」,拒绝会把 POS 从既有客户手里锁没,不可逆的是
        # 拒绝那一侧;此处不可逆的是放行那一侧,所以方向相反。
        logger.error(f"get_billing_status_combined error tenant={tenant_id}: {e}", exc_info=True)
        return {
            "allowed": False,
            "is_exempt": False,
            "balance_thb": 0.0,
            "pages_used_this_month": 0,
            "error_code": "lookup_error",
        }
