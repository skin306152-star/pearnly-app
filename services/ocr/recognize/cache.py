"""
services/ocr/recognize/cache.py · OCR 识别·文件指纹缓存命中分支

从 app.py ocr_recognize 抽出(REFACTOR-WB-app · 2026-06-01 · 纯搬家 0 逻辑改)。
缓存命中时:触发 auto-push / 异常检测 / 成本日志(成本 0 engine=cache),返回响应 dict。
调用方(ocr_recognize)在 `if cached:` 守卫内调本函数并直接 return。
"""

import logging

import db
from route_helpers import _plan_permissions, _tid
from exception_checks import _async_run_exception_checks
from services.erp.auto_push import (
    _auto_push_history,
    _auto_push_smart_routed,
    _trigger_auto_push_all,
    _erp_seller_routing_enabled,
)

logger = logging.getLogger("mr-pilot")


def serve_cache_hit(cached, user, plan, _erp_mode, file, monthly_quota, file_hash):
    logger.info(f"  🎯 命中文件缓存 (hash={file_hash[:12]}..., 省额度)")

    # v0.9 · 缓存命中也触发自动推送(用户的期待是"每次上传就推送")
    # P1b · ocr_only 模式 → 完全跳过 auto-push(纯跳过 · 零风险)。
    cache_auto_pushed = False
    if _erp_mode == "ocr_only":
        logger.info("[Cache][P1b] ocr_only 模式 · 跳过自动推送")
    elif _plan_permissions(plan).get("can_auto_push_erp"):
        try:
            auto_eps = db.list_erp_endpoints(str(user["id"]), auto_push_only=True)
            if auto_eps:
                import asyncio

                # P1d · 缓存命中也走同一分流(开+smart→分拣 · 否则现行为)。
                if _erp_seller_routing_enabled(str(user["id"])) and _erp_mode == "smart":
                    asyncio.create_task(
                        _auto_push_smart_routed(
                            str(user["id"]), [cached["id"]], _tid(user), auto_eps
                        )
                    )
                else:
                    asyncio.create_task(
                        _auto_push_history(
                            str(user["id"]), cached["id"], auto_eps, tenant_id=_tid(user)
                        )
                    )
                cache_auto_pushed = True
                logger.info(f"🚀 [Cache] 自动推送已入队 · history={cached['id']}")
        except Exception as e:
            logger.warning(f"[Cache] 自动推送入队失败: {e}")
        # v27.8.1.3 · 同时触发 Xero 自动推(独立通道)
        try:
            _trigger_auto_push_all(str(user["id"]), _tid(user), cached["id"])
        except Exception as e:
            logger.warning(f"[Cache] xero 自动推入队失败: {e}")

    # v118.20.1.7 · 缓存命中也跑异常检测(unique index 保证幂等 · 不会重写)
    # 这是关键 · 否则:历史已识别 + 这次重传 → 缓存命中 → 异常栏永远收不到这张
    try:
        import asyncio as _asyncio_exc_c

        _cached_pages = cached.get("pages") or []
        _primary = next(
            (p for p in _cached_pages if not p.get("is_duplicate") and not p.get("is_copy")),
            None,
        )
        _primary = _primary or (_cached_pages[0] if _cached_pages else None)
        _cf = (_primary or {}).get("fields") or {}
        _exc_total_c = None
        _raw_t_c = _cf.get("total_amount")
        if _raw_t_c:
            try:
                _exc_total_c = float(str(_raw_t_c).replace(",", "").strip())
            except Exception as e:
                logger.warning(f"[cache_hit] total_amount 解析失败: {e}")
        _asyncio_exc_c.create_task(
            _async_run_exception_checks(
                history_id=str(cached["id"]),
                user_id=str(user["id"]),
                tenant_id=_tid(user),
                seller_name=_cf.get("seller_name"),
                invoice_no=_cf.get("invoice_number"),
                total_amount=_exc_total_c,
                confidence=cached.get("confidence"),
                duplicate=None,  # 缓存命中说明 hash 全等 · 由专门的 duplicate 路径处理(本身已是同张)
                fields=_cf,
            )
        )
        logger.info(f"  🛡  [Cache] 异常检测已入队 · hid={cached['id']}")
    except Exception as _e_c:
        logger.warning(f"[Cache] 异常检测入队失败(不影响识别): {_e_c}")

    # v106.2 · 缓存命中也记 1 条成本日志(成本 0 · engine=cache)
    # 让面板能看到"省了多少次"+ 总张数也包含缓存命中
    try:
        db.log_ocr_cost(
            user_id=str(user["id"]),
            tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
            history_id=cached["id"],
            engine="cache",
            pages=int(cached.get("page_count") or 0),
            input_tokens=0,
            output_tokens=0,
            cost_thb=0.0,
            elapsed_ms=0,
        )
    except Exception as _ce:
        logger.warning(f"缓存命中日志写入失败(不影响识别): {_ce}")

    return {
        "filename": file.filename,
        "page_count": cached["page_count"],
        "elapsed_ms": 0,
        "engine": "cache",
        "pages": cached["pages"],
        "confidence": cached["confidence"],
        "history_id": cached["id"],
        "archive_name": cached.get("archive_name"),
        "category_tag": cached.get("category_tag"),
        "from_cache": True,
        "auto_pushed": cache_auto_pushed,
        "quota": {
            "ip_used_today": None,
            "ip_daily_limit": None,
            "used_this_month": int(user.get("used_this_month") or 0),
            "monthly_quota": monthly_quota,
        },
    }
