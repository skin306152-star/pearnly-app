# -*- coding: utf-8 -*-
"""
Pearnly · ERP 自动推送编排(REFACTOR-WA-B1 · 2026-05-29 从 app.py L1748-2251 抽出)

纯搬家 · 0 逻辑改 · OCR 识别完成 hook(app.py ocr_recognize / _handle_line_image_ocr)
后台异步触发。函数名保留下划线(内部互调 + 单测 patch 锚点 test_auto_push_smart_routing)。

7 个函数:
  · _auto_push_history          逐张推 auto_push 端点(dedup + pending + 落库 + 失败入重试队列)
  · _erp_seller_routing_enabled ERP_SELLER_ROUTING 回滚开关(全局 / 灰度名单)
  · _persist_push_outcome       一条 push 结果落库(与 _auto_push_history 单张写库同源 · 铁律#12)
  · _auto_push_batch_for_endpoint  P1d · 一端点一批 · dedup → dispatch_endpoint_batch → 逐张落库
  · _auto_push_smart_routed     P1d · 按卖方账套绑定 endpoint 分组批量推 + 未匹配兜底
  · _auto_push_xero_for_history v27.8.1.3 · Xero 后台自动推
  · _trigger_auto_push_all      OCR hook 总入口 · 触发 Xero 自动推

依赖:db(运行时 db.xxx · 保 tenant 隔离 patch 生效)· erp_push.push_to_endpoint ·
services.erp.push_dispatch(批量 · 函数内 import)· erp_xero_routes._ensure_fresh_xero_token
(Xero token · 函数内 lazy import 解循环)· xero_pusher(函数内 import)。
"""

from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger("mr-pilot")


async def _auto_push_history(
    user_id: str, history_id: str, endpoints: List[Dict[str, Any]], tenant_id: Optional[str] = None
):
    """
    后台异步任务 · 对 auto_push=TRUE 的端点批量推送一条历史记录
    失败不影响识别返回,只写入日志 · Plus/Pro 才会走这里
    v118.14 · tenant_id 给了 → 推送日志查询同 tenant 共享(老板能看员工触发的推送日志)
    """
    import asyncio

    # 1) 读历史详情(push_to_endpoint 要完整字段)
    history = db.get_ocr_history_detail(user_id, history_id, tenant_id=tenant_id)
    if not history:
        logger.warning(f"[AutoPush] 历史 {history_id} 不存在,跳过")
        return

    # 2) 循环推每个端点 · 用线程池避免阻塞事件循环(requests 是同步库)
    for ep in endpoints:
        try:
            # 批 2 改动 2 (v118.34.34) · 推送去重 · 同 history × endpoint
            # 已 success 过 → 静默跳过 + 写 skipped_dup log.
            existing = db.has_recent_successful_push(
                history_id,
                ep["id"],
                user_id,
            )
            if existing:
                db.insert_push_log(
                    user_id=user_id,
                    endpoint_id=ep["id"],
                    history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status="skipped_dup",
                    http_status=200,
                    request_body={
                        "adapter": ep.get("adapter"),
                        "skipped_reason": "already_success",
                        "prior_log_id": str(existing.get("id")),
                    },
                    response_body=existing.get("response_body"),
                    error_msg=None,
                    attempt=1,
                    elapsed_ms=0,
                    trigger="auto",
                )
                logger.info(
                    "[AutoPush-dedup] skipped · history=%s endpoint=%s " "(prior=%s)",
                    history_id[:8],
                    ep["id"][:8],
                    str(existing.get("id"))[:8],
                )
                continue

            # 先写 pending(推送中)· 识别后用户立刻在日志看到排队(2026-05-26 · 兜底路径补齐)。
            pending_id = db.insert_push_log(
                user_id=user_id,
                endpoint_id=ep["id"],
                history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="pending",
                http_status=None,
                request_body={"adapter": ep.get("adapter"), "stage": "pushing"},
                response_body=None,
                error_msg=None,
                attempt=1,
                elapsed_ms=0,
                trigger="auto",
            )

            # push_to_endpoint 是同步调用(requests) · 用 run_in_executor 挪到线程
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, erp_push.push_to_endpoint, ep, history)

            # P2-D(B8)· 「发票号已存在」= skipped_dup 中性态(不算失败)。
            final_status = db.classify_push_status(result["success"], result.get("error_msg"))
            # 把 pending 行原地更新成终态(没拿到 pending_id 才退回新插一行)。
            if pending_id:
                db.update_log_status_after_retry(
                    pending_id,
                    result["success"],
                    result.get("http_status"),
                    result.get("response_body"),
                    result.get("error_msg"),
                    result.get("elapsed_ms", 0),
                    request_body=result.get("request_body"),
                    final_status=final_status,
                )
                new_log_id = pending_id
            else:
                new_log_id = db.insert_push_log(
                    user_id=user_id,
                    endpoint_id=ep["id"],
                    history_id=history_id,
                    invoice_no=history.get("invoice_no"),
                    seller_name=history.get("seller_name"),
                    total_amount=history.get("total_amount"),
                    status=final_status,
                    http_status=result.get("http_status"),
                    request_body=result.get("request_body"),
                    response_body=result.get("response_body"),
                    error_msg=result.get("error_msg"),
                    attempt=1,
                    elapsed_ms=result.get("elapsed_ms", 0),
                    trigger="auto",  # 标记自动触发
                )

            db.update_endpoint_stats(ep["id"], final_status != "failed")
            db.update_history_push_status(history_id, final_status)

            # v118.25 · 自动推送失败 · 进入重试队列(60s 后第一次重试)
            # 批 1 改动 3 (v118.34.33) · 用户数据错 / 已推送过跳过重试队列.
            if final_status == "failed" and new_log_id:
                if db.is_user_data_error(result.get("error_msg")):
                    logger.info(
                        "[AutoPush] user-data error · NOT scheduling retry · " "log=%s err=%r",
                        str(new_log_id)[:8],
                        (result.get("error_msg") or "")[:80],
                    )
                else:
                    first_delay = db.get_erp_retry_delay_sec(0)
                    if first_delay is not None:
                        db.schedule_log_retry(str(new_log_id), first_delay)
                        logger.info(
                            f"[AutoPush] 失败入重试队列 · log={new_log_id} · {first_delay}s 后第 1 次重试"
                        )

            logger.info(
                f"[AutoPush] user={user_id[:8]}.. history={history_id[:8]}.. "
                f"ep={ep.get('name')!r} success={result['success']}"
            )
        except Exception as e:
            logger.exception(f"[AutoPush] endpoint={ep.get('name')!r} 处理异常: {e}")


# ============================================================
# P1d (Zihao 2026-05-26) · 卖方智能分拣 → 按账套路由批量推送
#   回滚开关 ERP_SELLER_ROUTING(默认关 · 关 = 现"全推 auto_push 端点"行为)。
#   开 + mode=smart → 按每张 history 的卖方账套(workspace)绑定的 endpoint 分组,
#   一组一次 dispatch_endpoint_batch(解 1000 张规模);未匹配/未绑端点 → 兼容兜底
#   推现有 auto_push 端点(不阻断 · 回滚安全线)。per-invoice 隔离。
#   写库逻辑(dedup / push 日志 / stats / 历史状态 / retry 队列)与逐张路径同源(铁律#12)。
# ============================================================
def _erp_seller_routing_enabled(user_id=None) -> bool:
    """ERP_SELLER_ROUTING 回滚开关 · 默认关。

    - 全局开:`ERP_SELLER_ROUTING` = 1/true/yes/on(忽略大小写)→ 所有用户走智能分拣。
    - 灰度开:`ERP_SELLER_ROUTING_USERS` = 逗号分隔 user_id → **仅名单内**用户走 ·
      其余用户(含现付费用户 mrerp)照旧。沙箱/灰度真账号测专用,隔离风险。
    """
    if (os.environ.get("ERP_SELLER_ROUTING") or "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    if user_id:
        allow = os.environ.get("ERP_SELLER_ROUTING_USERS") or ""
        ids = {x.strip() for x in allow.split(",") if x.strip()}
        if str(user_id) in ids:
            return True
    return False


def _persist_push_outcome(user_id, ep, history, result, trigger="auto", pending_log_id=None):
    """把一条 push 结果落库:push 日志 + endpoint stats + 历史状态 + 失败入重试队列。
    与 _auto_push_history 单张写库逻辑同源(铁律#12 单一源)· 供 P1d 批量路径复用。
    pending_log_id(2026-05-26):若推送前已写「pending(推送中)」行,这里把它**更新**
    成 success/failed(不再新插一行),让用户识别后立刻看到的「推送中」原地变成最终态。"""
    history_id = str(history["id"])
    # P2-D(Zihao 2026-05-27 · B8)· 「发票号已存在」= skipped_dup 中性态(不算失败)。
    final_status = db.classify_push_status(result["success"], result.get("error_msg"))
    if pending_log_id:
        db.update_log_status_after_retry(
            pending_log_id,
            result["success"],
            result.get("http_status"),
            result.get("response_body"),
            result.get("error_msg"),
            result.get("elapsed_ms", 0),
            request_body=result.get("request_body"),
            final_status=final_status,
        )
        new_log_id = pending_log_id
    else:
        new_log_id = db.insert_push_log(
            user_id=user_id,
            endpoint_id=ep["id"],
            history_id=history_id,
            invoice_no=history.get("invoice_no"),
            seller_name=history.get("seller_name"),
            total_amount=history.get("total_amount"),
            status=final_status,
            http_status=result.get("http_status"),
            request_body=result.get("request_body"),
            response_body=result.get("response_body"),
            error_msg=result.get("error_msg"),
            attempt=1,
            elapsed_ms=result.get("elapsed_ms", 0),
            trigger=trigger,
        )
    db.update_endpoint_stats(ep["id"], final_status != "failed")
    db.update_history_push_status(history_id, final_status)

    # 失败入重试队列(用户数据错 / 已推送过都跳过 · 同 _auto_push_history)。
    if final_status == "failed" and new_log_id:
        if db.is_user_data_error(result.get("error_msg")):
            logger.info(
                "[SmartPush] user-data error · NOT scheduling retry · log=%s err=%r",
                str(new_log_id)[:8],
                (result.get("error_msg") or "")[:80],
            )
        else:
            first_delay = db.get_erp_retry_delay_sec(0)
            if first_delay is not None:
                db.schedule_log_retry(str(new_log_id), first_delay)
                logger.info(
                    f"[SmartPush] 失败入重试队列 · log={new_log_id} · {first_delay}s 后第 1 次重试"
                )


async def _auto_push_batch_for_endpoint(user_id, endpoint, histories, tenant_id=None):
    """P1d · 一个 endpoint 一批 history:dedup → 一次 dispatch_endpoint_batch → 逐张落库。
    dispatch 是同步(Playwright)· 用 run_in_executor 挪线程 · 不阻塞事件循环。"""
    import asyncio

    from services.erp import push_dispatch

    # 1) dedup:已 success 过 → 写 skipped_dup,不进 dispatch(同 _auto_push_history)。
    to_push = []
    for h in histories:
        try:
            existing = db.has_recent_successful_push(str(h["id"]), endpoint["id"], user_id)
        except Exception:
            existing = None
        if existing:
            db.insert_push_log(
                user_id=user_id,
                endpoint_id=endpoint["id"],
                history_id=str(h["id"]),
                invoice_no=h.get("invoice_no"),
                seller_name=h.get("seller_name"),
                total_amount=h.get("total_amount"),
                status="skipped_dup",
                http_status=200,
                request_body={
                    "adapter": endpoint.get("adapter"),
                    "skipped_reason": "already_success",
                    "prior_log_id": str(existing.get("id")),
                },
                response_body=existing.get("response_body"),
                error_msg=None,
                attempt=1,
                elapsed_ms=0,
                trigger="auto",
            )
            continue
        to_push.append(h)

    if not to_push:
        return

    # 1.5) 立刻给每张写一条 pending(推送中)日志 · 识别后用户马上能在日志看到排队,
    #      不用干等几秒的 Playwright 往返(2026-05-26 Zihao 反馈)· 推完原地更新成 ✓/✗。
    pending_ids = {}
    for h in to_push:
        try:
            pid = db.insert_push_log(
                user_id=user_id,
                endpoint_id=endpoint["id"],
                history_id=str(h["id"]),
                invoice_no=h.get("invoice_no"),
                seller_name=h.get("seller_name"),
                total_amount=h.get("total_amount"),
                status="pending",
                http_status=None,
                request_body={"adapter": endpoint.get("adapter"), "stage": "pushing"},
                response_body=None,
                error_msg=None,
                attempt=1,
                elapsed_ms=0,
                trigger="auto",
            )
            if pid:
                pending_ids[str(h["id"])] = pid
        except Exception as e:
            logger.warning(
                "[SmartPush] pending 日志写入失败 history=%s: %s", str(h.get("id"))[:8], e
            )

    # 2) 一次性批量推(off-loop)。
    loop = asyncio.get_event_loop()
    try:
        results = await loop.run_in_executor(
            None, push_dispatch.dispatch_endpoint_batch, endpoint, to_push
        )
    except Exception as e:
        logger.exception(
            "[SmartPush] dispatch_endpoint_batch raised · endpoint=%s · %s",
            endpoint.get("name"),
            e,
        )
        # dispatch 整体炸了 → 把 pending(推送中)行落定成 failed · 不让它卡在「推送中」。
        for h in to_push:
            pid = pending_ids.get(str(h["id"]))
            if not pid:
                continue
            try:
                db.update_log_status_after_retry(
                    pid, False, None, None, f"dispatch_error: {type(e).__name__}", 0
                )
                db.update_history_push_status(str(h["id"]), "failed")
            except Exception:
                pass
        return

    # 3) 逐张落库(per-invoice 隔离:一张写库异常不影响其余)· 把 pending 行更新成终态。
    for h, result in zip(to_push, results):
        try:
            _persist_push_outcome(
                user_id, endpoint, h, result, pending_log_id=pending_ids.get(str(h["id"]))
            )
            logger.info(
                "[SmartPush] user=%s.. history=%s.. ep=%r success=%s",
                user_id[:8],
                str(h["id"])[:8],
                endpoint.get("name"),
                result.get("success"),
            )
        except Exception as e:
            logger.exception("[SmartPush] 落库异常 history=%s: %s", str(h.get("id"))[:8], e)


async def _auto_push_smart_routed(user_id, history_ids, tenant_id, fallback_eps):
    """P1d · 智能分拣编排:按每张 history 的卖方账套(workspace)绑定的 endpoint 分组批量推;
    未匹配/未绑端点/端点停用 → 兼容兜底推现有 auto_push 端点(回滚安全线 · 不阻断)。"""
    groups = {}  # endpoint_id -> {"endpoint": ep, "histories": [...]}
    fallback = []  # 未匹配 → 兜底
    ep_cache = {}

    for hid in history_ids:
        try:
            h = db.get_ocr_history_detail(user_id, hid, tenant_id=tenant_id)
        except Exception:
            h = None
        if not h:
            continue
        wcid = h.get("workspace_client_id")
        target_ep = None
        if wcid:
            try:
                wc = db.get_workspace_client(int(wcid), user_id, tenant_id=tenant_id)
            except Exception:
                wc = None
            eid = ((wc or {}).get("erp_endpoint_id") or "").strip() or None
            if eid:
                if eid not in ep_cache:
                    ep_cache[eid] = db.get_erp_endpoint(user_id, eid)
                target_ep = ep_cache[eid]
        if target_ep and target_ep.get("enabled", True):
            g = groups.setdefault(str(target_ep["id"]), {"endpoint": target_ep, "histories": []})
            g["histories"].append(h)
        else:
            fallback.append(h)

    logger.info(
        "[SmartPush] 分拣 · %d 端点组 + %d 张兜底",
        len(groups),
        len(fallback),
    )

    # 各账套端点分组批量推(组间串行 · MR.ERP 会话锁本就跨进程串行)。
    for g in groups.values():
        try:
            await _auto_push_batch_for_endpoint(
                user_id, g["endpoint"], g["histories"], tenant_id=tenant_id
            )
        except Exception as e:
            logger.exception("[SmartPush] 端点组推送异常: %s", e)

    # 兜底:未匹配的推现有 auto_push 端点(现行为 · 不阻断付费用户)。
    for h in fallback:
        try:
            await _auto_push_history(user_id, str(h["id"]), fallback_eps, tenant_id=tenant_id)
        except Exception as e:
            logger.exception("[SmartPush] 兜底推送异常 history=%s: %s", str(h.get("id"))[:8], e)


def _trigger_auto_push_all(user_id: str, tenant_id: Optional[str], history_id: str):
    """v27.8.1.3 · 给 OCR hook 用 · 一次性触发 webhook + Xero 两类自动推
    每类独立 task · 互不影响"""
    if not tenant_id:
        return
    import asyncio

    # Xero
    try:
        if db.get_xero_auto_push(tenant_id):
            asyncio.create_task(_auto_push_xero_for_history(user_id, tenant_id, history_id))
    except Exception as e:
        logger.warning(f"[AutoPushAll] xero schedule failed: {e}")


# ⚠️ `import db` / `import erp_push` 放 def 之后(解循环 import · 见 services/billing/charge.py 注释)
import db  # noqa: E402
import erp_push  # noqa: E402

# R19 · Xero 自动推路径下沉 auto_push_xero · 此处 re-import:_trigger_auto_push_all 调 + 契约 re-export
from services.erp.auto_push_xero import _auto_push_xero_for_history  # noqa: E402,F401
