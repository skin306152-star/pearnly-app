# -*- coding: utf-8 -*-
"""暂存目录 + 老对账产物清扫 janitor(ENC-c · prod 实锤 45 个残留 recon_jobs 目录 17M 无人清)。

挂 services/background_loops.run_recovery_tick 顺带跑(照 proactive/auto_open 先例·
不建新 cron、不建新表)。两条清扫线:

  1) recon_jobs / ocr_jobs 的 STAGE_DIR/<job_id>/ 暂存目录:worker 正常完成时已在
     finally 里自己删(services/recon_jobs/worker.py _cleanup_stage 同款),这里是安全网,
     兜工人崩溃/部署杀掉进程留下的孤儿。判据两条都要满足才删:
       · 目录 mtime 已 >48h(给在跑任务和刚落盘的上传留够缓冲)
       · 且对应 job 行不存在(孤儿)或已终态(done/failed)
     在跑/排队/needs_review/needs_mapping 一律不碰 —— 这是本 janitor 的命门,宁可多留
     不可误删正在用的暂存文件。
  2) vat_recon_tasks 老 Excel 产物:复用 routes/vat_excel_tasks_routes.py clear_old 的
     7 天判定(created_at),从『用户手动触发』补成后台自动扫描(手动端点原样保留)。

单目录/单批次异常互不连坐:出错记 warning 跳过,继续下一个,不让一个坏目录拖垮整轮。
"""

from __future__ import annotations

import logging
import os
import shutil
import time
import uuid
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("ops.stage_janitor")

# 48h:比对账任务的最长租约(LEASE_SEC 默认 600s)宽绰得多,只兜『早就没人管了』的目录。
STAGE_STALE_SEC = int(os.environ.get("JANITOR_STAGE_STALE_SEC", str(48 * 3600)))
# 7 天:与 routes/vat_excel_tasks_routes.py clear_old 的默认 days=7 判定口径一致。
VAT_RECON_STALE_DAYS = int(os.environ.get("JANITOR_VAT_RECON_DAYS", "7"))

_TERMINAL_STATUSES = frozenset({"done", "failed"})


def _is_job_id(name: str) -> bool:
    """暂存目录名须是 job_id(UUID)· 非法名不查 DB(必炸 ANY(uuid[]))· 直接按孤儿处理。"""
    try:
        uuid.UUID(name)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def sweep_stage_root(
    stage_root: str,
    get_status_map: Callable[[List[str]], Dict[str, str]],
    label: str,
) -> Dict[str, int]:
    """扫一个 STAGE_DIR 下的全部 <job_id>/ 子目录 · 满足判据的删掉。

    get_status_map 由调用方注入(store.get_status_map)· 纯函数化以便单测不碰真 DB/真磁盘之外
    的东西——测试可传假的 stage_root(tmp dir)+ 假的 get_status_map。
    """
    stats = {"scanned": 0, "deleted": 0, "kept": 0, "errors": 0}
    try:
        entries = os.listdir(stage_root)
    except FileNotFoundError:
        return stats  # 目录本不存在(ocr_jobs 在 prod 现状)· 兜底不炸
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[stage_janitor] {label}: list {stage_root} failed: {e}")
        return stats

    now = time.time()
    stale_names: List[str] = []
    for name in entries:
        path = os.path.join(stage_root, name)
        stats["scanned"] += 1
        try:
            if not os.path.isdir(path):
                continue
            if now - os.path.getmtime(path) <= STAGE_STALE_SEC:
                stats["kept"] += 1
                continue
            stale_names.append(name)
        except Exception as e:  # noqa: BLE001
            stats["errors"] += 1
            logger.warning(f"[stage_janitor] {label}: stat {path} failed(skip): {e}")

    if not stale_names:
        return stats

    valid_ids = [n for n in stale_names if _is_job_id(n)]
    try:
        status_map = get_status_map(valid_ids) if valid_ids else {}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[stage_janitor] {label}: status lookup failed(skip round): {e}")
        return stats

    for name in stale_names:
        status: Optional[str] = status_map.get(name) if _is_job_id(name) else None
        if status is not None and status not in _TERMINAL_STATUSES:
            stats["kept"] += 1
            continue  # 在跑/排队/needs_review/needs_mapping —— 命门,一律不碰
        path = os.path.join(stage_root, name)
        try:
            if not os.path.isdir(path):
                continue  # 已被别处(worker 自己的 finally)清过 · 不算错
            shutil.rmtree(path)
            stats["deleted"] += 1
            reason = "orphan(no job row)" if status is None else f"terminal({status})"
            logger.info(f"[stage_janitor] {label}: removed {path} · reason={reason}")
        except Exception as e:  # noqa: BLE001
            stats["errors"] += 1
            logger.warning(f"[stage_janitor] {label}: rmtree {path} failed(skip): {e}")
    return stats


def sweep_recon_stage() -> Dict[str, int]:
    from services.recon_jobs import store, worker

    return sweep_stage_root(worker.STAGE_DIR, store.get_status_map, "recon_jobs")


def sweep_ocr_stage() -> Dict[str, int]:
    from services.ocr.jobs import store, worker

    return sweep_stage_root(worker.STAGE_DIR, store.get_status_map, "ocr_jobs")


def sweep_vat_recon_products() -> Dict[str, int]:
    """vat_recon_tasks 老 Excel 产物 · 复用 clear_old 的 7 天判定(created_at)· 全租户扫描。"""
    from services.recon.vat_recon_tasks_store import delete_vat_recon_tasks_older_than_global

    stats = {"deleted_rows": 0, "deleted_files": 0, "errors": 0}
    try:
        deleted_count, excel_paths = delete_vat_recon_tasks_older_than_global(VAT_RECON_STALE_DAYS)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[stage_janitor] vat_recon: db sweep failed: {e}")
        return stats
    stats["deleted_rows"] = deleted_count
    for p in excel_paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
                stats["deleted_files"] += 1
                logger.info(f"[stage_janitor] vat_recon: removed file {p}")
        except Exception as e:  # noqa: BLE001
            stats["errors"] += 1
            logger.warning(f"[stage_janitor] vat_recon: remove {p} failed(skip): {e}")
    return stats


def run_once() -> Dict[str, Dict[str, int]]:
    """同步跑一轮全部清扫 · 三段互不连坐(一段炸不连累其它两段)。挂 background_loops 时
    用 asyncio.to_thread 包一层(阻塞文件/DB IO 不占事件循环)。"""
    result: Dict[str, Dict[str, int]] = {}
    for name, fn in (
        ("recon_jobs_stage", sweep_recon_stage),
        ("ocr_jobs_stage", sweep_ocr_stage),
        ("vat_recon_products", sweep_vat_recon_products),
    ):
        try:
            result[name] = fn()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[stage_janitor] {name} sweep failed: {e}")
            result[name] = {"errors": 1}
    return result
