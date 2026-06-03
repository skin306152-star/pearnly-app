# -*- coding: utf-8 -*-
"""收入对账进度反馈子系统(内存进度存储 · 60min TTL)· recon_routes 拆分共享 leaf。

get_progress(主)/ run_recon(主)/ batch_process(v1_batch)共享同一 _progress_store 实例。"""

import time
from typing import Dict, Any

# v118.32.4 · C 进度反馈业务化 · 内存进度存储(60 分钟 TTL)
# 5 个业务阶段:upload / parse_report / ocr_invoices / match / done
_progress_store: Dict[str, Dict[str, Any]] = {}
_PROGRESS_TTL_SEC = 3600


def _progress_init(pid: str, **kwargs):
    if not pid:
        return
    _progress_gc()
    _progress_store[pid] = {
        "stage": "upload",
        "stage_done": 0,
        "stage_total": 0,
        "current_file": "",
        "started_at": time.time(),
        "updated_at": time.time(),
        "stats": None,
        "error": "",
        **kwargs,
    }


def _progress_update(pid: str, **kwargs):
    if not pid or pid not in _progress_store:
        return
    _progress_store[pid].update(kwargs)
    _progress_store[pid]["updated_at"] = time.time()


def _progress_gc():
    now = time.time()
    stale = [
        k for k, v in _progress_store.items() if now - v.get("updated_at", 0) > _PROGRESS_TTL_SEC
    ]
    for k in stale:
        _progress_store.pop(k, None)
