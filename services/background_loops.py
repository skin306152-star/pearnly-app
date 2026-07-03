# -*- coding: utf-8 -*-
"""
Pearnly · 后台常驻 loop(REFACTOR-WA-B1 · 2026-05-29 从 app.py 抽出)

纯搬家 · 0 逻辑改 · app.py lifespan 用 asyncio.create_task() 起这两条 loop:
  · erp_retry_loop()      — 每 30s 跑 run_erp_retry_tick(ERP 推送失败重试队列)
  · email_ingest_loop()   — 每 5min tick · 扫启用邮箱账号按 interval_min 抓取

单 tick 函数(loop 内部调 · 也供测试单独调):
  · run_erp_retry_tick()      — 找到期失败 log → erp_push.push_to_endpoint 重推 → 更新状态
  · run_email_ingest_tick()   — 扫启用账号 → email_ingest.run_account_ingest → 写 ingest log

依赖:db(运行时 db.xxx · 保 tenant 隔离 patch 生效)· erp_push(推送适配)·
email_ingest(运行时 import · 未配 EMAIL_ENCRYPTION_KEY 时 is_available() False 直接跳过)。
"""

import os
import logging

from core import db
from services.erp import erp_push

logger = logging.getLogger("mr-pilot")


async def erp_retry_loop():
    """每 30 秒跑一次重试 tick"""
    import asyncio

    # 启动时先等 30 秒 · 避开和其他 startup 竞争
    await asyncio.sleep(30)
    interval_sec = int(os.environ.get("ERP_RETRY_TICK_SEC", "30"))
    while True:
        try:
            await run_erp_retry_tick()
        except Exception as e:
            logger.warning(f"[erp_retry_loop] tick 异常(继续): {e}")
        try:
            await asyncio.sleep(interval_sec)
        except asyncio.CancelledError:
            raise


async def run_erp_retry_tick():
    """单次 tick:找到期失败 log · 重新调用 erp_push 推送 · 更新 log 状态"""
    import asyncio as _asyncio

    try:
        due = db.list_logs_due_for_retry(limit=20)
        if not due:
            await run_recovery_tick()
            return
        logger.info(f"[erp_retry] 本轮到期重试 {len(due)} 条")

        for log in due:
            try:
                # 取上下文(history + endpoint)
                history = (
                    db.get_ocr_history_detail(
                        str(log["user_id"]),
                        str(log["history_id"]),
                        tenant_id=None,
                    )
                    if log.get("history_id")
                    else None
                )
                endpoint = (
                    db.get_erp_endpoint(
                        str(log["user_id"]),
                        str(log["endpoint_id"]),
                    )
                    if log.get("endpoint_id")
                    else None
                )

                if not history or not endpoint:
                    # 关联实体已删 · 终止此 log 的重试
                    db.clear_retry_schedule(str(log["id"]))
                    logger.info(f"[erp_retry] log {log['id']} 关联记录已删 · 停止重试")
                    continue

                # 在 worker 线程里跑同步 push(避免阻塞事件循环)
                result = await _asyncio.to_thread(
                    erp_push.push_to_endpoint,
                    endpoint,
                    history,
                )

                # 自增 retry_count · 更新 log 状态(直接覆盖原行 · 不写新行)
                # P2-D(B8)· 「发票号已存在」= skipped_dup 中性态(不算失败)。
                final_status = db.classify_push_status(
                    bool(result.get("success")), result.get("error_msg")
                )
                new_count = db.increment_retry_count(str(log["id"]))
                db.update_log_status_after_retry(
                    log_id=str(log["id"]),
                    success=bool(result.get("success")),
                    http_status=result.get("http_status"),
                    response_body=result.get("response_body"),
                    error_msg=result.get("error_msg"),
                    elapsed_ms=int(result.get("elapsed_ms", 0)),
                    final_status=final_status,
                )
                # 端点 + history 状态同步(skipped_dup 视为非失败)
                db.update_endpoint_stats(str(endpoint["id"]), final_status != "failed")
                if log.get("history_id"):
                    db.update_history_push_status(str(log["history_id"]), final_status)

                if final_status != "failed":
                    # 重试成功 / 已推送过 · 摘出队列
                    db.clear_retry_schedule(str(log["id"]))
                    logger.info(f"[erp_retry] log {log['id']} 重试 #{new_count} → {final_status}")
                else:
                    # 批 1 改动 3 (v118.34.33) · 用户数据错 retry 阶段也要识别 ·
                    # 一旦从技术错变成用户数据错(或本来就是)· 立刻摘队列.
                    if db.is_user_data_error(result.get("error_msg")):
                        db.clear_retry_schedule(str(log["id"]))
                        logger.info(
                            "[erp_retry] log %s 重试 #%d 命中 user-data 错 · " "停止队列 (err=%r)",
                            log["id"],
                            new_count,
                            (result.get("error_msg") or "")[:80],
                        )
                    else:
                        # 仍失败 · 看还有没有下一次
                        next_delay = db.get_erp_retry_delay_sec(new_count)
                        if next_delay is None:
                            # 用完 3 次 · 不再调度 · 等用户手动
                            db.clear_retry_schedule(str(log["id"]))
                            logger.warning(
                                f"[erp_retry] log {log['id']} 重试 {new_count} 次仍失败 · 停止"
                            )
                        else:
                            db.schedule_log_retry(str(log["id"]), next_delay)
                            logger.info(
                                f"[erp_retry] log {log['id']} 重试 #{new_count} 失败 · {next_delay}s 后再试"
                            )
            except Exception as e_inner:
                logger.warning(f"[erp_retry] 单条处理失败 log_id={log.get('id')}: {e_inner}")
                # 单条失败不影响其它
                continue
    except Exception as e:
        logger.warning(f"[erp_retry] tick 整体异常: {e}")
    await run_recovery_tick()


async def run_recovery_tick():
    """Run non-ERP recovery queues on the existing background cadence."""
    try:
        await run_accounting_posting_failure_tick()
    except Exception as e:
        logger.warning(f"[acct_recovery] tick failed: {e}")
    try:
        await run_line_ocr_job_tick()
    except Exception as e:
        logger.warning(f"[line_ocr_jobs] tick failed: {e}")
    try:
        from services.notification import proactive

        await proactive.run_tick()
    except Exception as e:
        logger.warning(f"[proactive_nudge] tick failed: {e}")


async def run_accounting_posting_failure_tick():
    import asyncio as _asyncio

    from services.accounting import posting_failures

    await _asyncio.to_thread(posting_failures.retry_due, limit=10)


async def run_line_ocr_job_tick():
    from services.ocr import line_ocr_jobs

    await line_ocr_jobs.process_due(limit=3)


async def email_ingest_loop():
    import asyncio

    # 启动时先等 60 秒避免和其他启动动作抢资源
    await asyncio.sleep(60)
    # tick 粒度固定 5 分钟(最小档)· 每账号根据自己 interval_min 判断是否到期
    interval_sec = int(os.environ.get("EMAIL_INGEST_TICK_SEC", "300"))
    while True:
        try:
            await run_email_ingest_tick()
        except Exception as e:
            logger.warning(f"[email_ingest_loop] tick 异常(继续): {e}")
        try:
            await asyncio.sleep(interval_sec)
        except asyncio.CancelledError:
            raise


async def run_email_ingest_tick():
    """一个 tick · 扫所有启用账号 · 按 interval_min 决定哪些到期需处理"""
    import asyncio
    from datetime import datetime, timezone, timedelta

    try:
        from services.email_ingest import email_ingest

        if not email_ingest.is_available():
            return  # 未配 EMAIL_ENCRYPTION_KEY
        accounts = db.list_enabled_email_accounts()
        if not accounts:
            return

        now = datetime.now(timezone.utc)
        due_accounts = []
        for a in accounts:
            interval = int(a.get("interval_min") or 15)
            last = a.get("last_check_at")
            # 没扫过 · 或距上次 check 超过 interval · 就到期
            if last is None:
                due_accounts.append(a)
                continue
            # 容忍 30 秒提前(避免轮询 boundary 漂移多等一轮)
            if (now - last) >= timedelta(minutes=interval) - timedelta(seconds=30):
                due_accounts.append(a)

        if not due_accounts:
            return
        logger.info(f"[email_ingest_loop] 扫 {len(accounts)} 个账号 · 到期 {len(due_accounts)} 个")

        for account in due_accounts:
            try:
                # 阻塞 IO 放到线程池 · 避免卡住 asyncio loop
                result = await asyncio.to_thread(email_ingest.run_account_ingest, account, "auto")
                db.insert_email_ingest_log(
                    account_id=account["id"],
                    user_id=account["user_id"],
                    stats=result,
                    trigger="auto",
                )
                db.update_email_account_status(
                    account["id"],
                    success=result["status"] in ("success", "partial"),
                    error_msg=result.get("error_message"),
                    fetched_any=result.get("attachments_found", 0) > 0,
                )
            except Exception as e:
                logger.warning(f"[email_ingest_loop] account={account.get('id')} 处理异常: {e}")
    except Exception as e:
        logger.warning(f"[email_ingest_loop] tick 外层异常: {e}")
