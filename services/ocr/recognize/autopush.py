"""
services/ocr/recognize/autopush.py · OCR 识别·ERP 自动推送分发

从 app.py ocr_recognize 抽出(REFACTOR-WB-app · 2026-06-01 · 纯搬家 0 逻辑改)。
仅对已归属(有 client_id)的 history 触发 auto-push(防 ERR_NO_CLIENT 空炸 retry 队列);
ERP_SELLER_ROUTING 开启时走卖方账套分拣,否则每张推所有自动推送端点。
返回 auto_pushed(布尔·进响应)。
"""

import logging

from core import db
from core.route_helpers import _plan_permissions, _tid
from services.erp.auto_push import (
    _auto_push_history,
    _auto_push_smart_routed,
    _erp_seller_routing_enabled,
)

logger = logging.getLogger("mr-pilot")


def dispatch_auto_push(*, history_ids, plan, user):
    # v0.9 · 自动推送 ERP(异步 · 不阻塞返回)· 每张发票都推
    # 批 1 改动 1 (v118.34.33) · 只对有 client_id 的 history 触发 auto-push.
    # 没 client_id 的就交给「待归属」/「建议归属」UI 让用户确认 · 防止
    # auto-push 必炸 ERR_NO_CLIENT 浪费 retry 队列(对应 Zihao 截图里
    # 一直 retry 的混乱).
    auto_pushed = False
    if history_ids and _plan_permissions(plan).get("can_auto_push_erp"):
        try:
            auto_eps = db.list_erp_endpoints(str(user["id"]), auto_push_only=True)
            if auto_eps:
                # 重新查 history 拿真实 client_id (auto-resolve 已经 update 过)
                pushable_ids = []
                for hid in history_ids:
                    h = db.get_ocr_history_detail(
                        str(user["id"]),
                        hid,
                        tenant_id=_tid(user),
                    )
                    if h and h.get("client_id"):
                        pushable_ids.append(hid)
                    else:
                        logger.info(
                            "[auto-push] skip history=%s · no client_id assigned",
                            hid[:8],
                        )
                if pushable_ids:
                    import asyncio

                    if _erp_seller_routing_enabled(str(user["id"])):
                        asyncio.create_task(
                            _auto_push_smart_routed(
                                str(user["id"]),
                                pushable_ids,
                                _tid(user),
                                auto_eps,
                            ),
                        )
                    else:
                        for hid in pushable_ids:
                            asyncio.create_task(
                                _auto_push_history(
                                    str(user["id"]),
                                    hid,
                                    auto_eps,
                                    tenant_id=_tid(user),
                                ),
                            )
                    auto_pushed = True
                    logger.info(
                        "🚀 自动推送已入队 · %d/%d 张发票 × %d 端点 " "(没归属的发票跳过)",
                        len(pushable_ids),
                        len(history_ids),
                        len(auto_eps),
                    )
        except Exception as e:
            logger.warning(f"自动推送入队失败(不影响识别): {e}")

    return auto_pushed
