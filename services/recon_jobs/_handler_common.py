# -*- coding: utf-8 -*-
"""对账重活 · 共享辅助(暂存文件读取 / 并行映射 / 整侧失败分流信号)· ADR-005。"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Tuple

ProgressCb = Callable[[dict], None]


# ── 暂存文件读取 ────────────────────────────────────────────────────
def _read_inputs(input_ref: List[dict], role: str) -> List[Tuple[bytes, str]]:
    """从暂存目录按 role 读出 (bytes, filename) 列表 · 保序。"""
    out: List[Tuple[bytes, str]] = []
    for item in input_ref or []:
        if (item or {}).get("role") != role:
            continue
        path = item.get("path")
        fname = item.get("filename") or os.path.basename(path or "") or "file"
        with open(path, "rb") as f:
            out.append((f.read(), fname))
    return out


def _noop(_p: dict) -> None:
    pass


def _side_fail_signal(stmt_results, stmt_data, gl_results, gl_data, failed_id):
    """整侧解析全失败 → 给 worker 的非 done 信号(BUG-FIX-RECON-GLCSV · 失败分流)。

    ① 任一失败结果带 mapping_request(读到了表格结构 · 有 headers/preview · 只是不认识列)
       → ("__needs_mapping__", …)· worker 置 needs_mapping · 前端弹『确认列对应』让用户指认。
    ② 否则(连表格结构都没读出:PDF/OCR 失败 / 空 / 损坏 / 无 headers)
       → ("__failed__", …)· worker 置 failed · 前端显示明确失败原因。
    result_id 指向已存的诊断任务(#16:历史/GET 仍能看解析诊断表)。
    """
    paired = list(zip(stmt_results, stmt_data)) + list(zip(gl_results, gl_data))
    # ① 有 mapping_request 的优先(stmt 先 gl 后)· 可现场弹面板修
    for r, (_, fn) in paired:
        if r.get("ok"):
            continue
        if r.get("needs_mapping") and r.get("mapping_request"):
            return (
                "__needs_mapping__",
                {
                    "mapping": {"file": fn, **(r.get("mapping_request") or {})},
                    "result_table": "bank_recon_v2_task",
                    "result_id": failed_id,
                    "error_code": "needs_mapping",
                },
            )
    # ② 无表格结构可修 → 明确失败 · 取第一条失败结果的 error_code(前端翻译成友好文案)
    code = "parse_failed"
    for r, _ in paired:
        if not r.get("ok"):
            code = r.get("error_code") or "parse_failed"
            break
    return (
        "__failed__",
        {
            "result_table": "bank_recon_v2_task",
            "result_id": failed_id,
            "error_code": code,
        },
    )


def _parallel(fn: Callable, items: List, max_workers: int = 4) -> List:
    """并行映射 · 保持输入顺序(复刻原路由 asyncio.gather 行为)。"""
    if not items:
        return []
    if len(items) == 1:
        return [fn(items[0])]
    with ThreadPoolExecutor(max_workers=min(max_workers, len(items))) as ex:
        return list(ex.map(fn, items))
