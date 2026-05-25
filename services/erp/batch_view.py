# -*- coding: utf-8 -*-
"""批次中心展示态派生 + 聚合(B5 · 纯逻辑 · 2026-05-26)

设计原则(Zihao 拍板):**不新增重复状态源**。批次中心展示的"成功/待处理/重试中/
失败"全部从现有 `erp_push_logs` 字段**派生**,不改 push log 状态机、不加新 status。

派生映射(只读现有列 · 不写库):
  status='success'                                   → success(已推送)
  status='skipped_dup'                               → skipped(已推过·去重)
  status='failed' + next_retry_at 有 + retry<max     → retrying(重试中)
  status='failed' + 用户数据错(is_user_data_error)  → needs_action(需人工处理)
  status='failed' 其余                                → failed(终态失败)
  status in (queued/running/pending)                 → 原样(预留·当前主路径不产生)

⚠️ 非接入:本模块不被任何上传/推送主路径调用 · 仅为批次中心 API/UI 落地后复用。
⚠️ batch_id:一次上传聚合需要 erp_push_logs 新增 batch_id 列(schema 改动)·
   见 docs/refactor/batch-center-plan.md · **待 Zihao 确认后再实现**。本聚合器对
   有/无 batch_id 都能工作(无则归入单一隐式批次),便于 schema 落地后直接复用。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

# 展示态桶(顺序即 UI 建议展示顺序)
BUCKETS = (
    "success",
    "skipped",
    "queued",
    "running",
    "retrying",
    "needs_action",
    "failed",
)

NO_BATCH_KEY = "__no_batch__"


def _default_is_user_data_error(error_msg: Optional[str]) -> bool:
    """默认用 db.is_user_data_error(单一权威源)· 懒 import 便于无 DB 单测注入替身。"""
    try:
        import db

        return bool(db.is_user_data_error(error_msg))
    except Exception:
        return False


def classify_push_log(
    row: Dict[str, Any],
    *,
    is_user_data_error: Optional[Callable[[Optional[str]], bool]] = None,
) -> str:
    """把一条 erp_push_logs 行派生成批次中心展示态(纯函数 · 不写库)。"""
    udf = is_user_data_error or _default_is_user_data_error
    status = (row.get("status") or "").lower()

    if status == "success":
        return "success"
    if status == "skipped_dup":
        return "skipped"
    if status in ("queued", "pending"):
        return "queued"
    if status == "running":
        return "running"
    if status == "failed":
        next_retry_at = row.get("next_retry_at")
        retry_count = int(row.get("retry_count") or 0)
        max_retries = int(row.get("max_retries") or 0)
        if next_retry_at is not None and retry_count < max_retries:
            return "retrying"
        if udf(row.get("error_msg")):
            return "needs_action"
        return "failed"
    # 未知 status 兜底(不吞 · 便于发现新状态)
    return status or "unknown"


def summarize_logs(
    rows: Iterable[Dict[str, Any]],
    *,
    is_user_data_error: Optional[Callable[[Optional[str]], bool]] = None,
) -> Dict[str, int]:
    """聚合一批 push log → 各展示态计数 + total。100/1000 张同样 O(N) 一次过。"""
    out: Dict[str, int] = {b: 0 for b in BUCKETS}
    out["total"] = 0
    out["unknown"] = 0
    for r in rows:
        out["total"] += 1
        bucket = classify_push_log(r, is_user_data_error=is_user_data_error)
        out[bucket] = out.get(bucket, 0) + 1
    return out


def group_into_batches(
    rows: Iterable[Dict[str, Any]],
    *,
    key: str = "batch_id",
    is_user_data_error: Optional[Callable[[Optional[str]], bool]] = None,
) -> Dict[str, Dict[str, int]]:
    """按 batch_id 分组聚合。无 batch_id 的行归入单一隐式批次(NO_BATCH_KEY)·
    schema 加上 batch_id 后无需改本函数。"""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        bid = r.get(key) or NO_BATCH_KEY
        groups.setdefault(str(bid), []).append(r)
    return {
        bid: summarize_logs(rs, is_user_data_error=is_user_data_error) for bid, rs in groups.items()
    }
