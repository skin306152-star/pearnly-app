# -*- coding: utf-8 -*-
"""对账重活 · 共享辅助(暂存文件读取 / 并行映射 / 跑前余额闸 / 事后扣费 / 失败分流)· ADR-005。"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional, Tuple

from core.concurrency import submit_ctx

logger = logging.getLogger("recon_jobs.handlers")

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


def _resolve_api_key(params: dict) -> str:
    """Gemini key for the worker. The submit route no longer persists it in the
    job row (secret-at-rest), so fall back to the environment — same precedence
    as the submit route's _user_key."""
    return (
        (params.get("api_key") or "")
        or os.environ.get("GEMINI_API_KEY", "")
        or os.environ.get("GOOGLE_API_KEY", "")
    ).strip()


def _runtime_balance_gate(
    tag: str, params: dict, files: List[Tuple[bytes, str]]
) -> Optional[Tuple[str, dict]]:
    """跑前二次余额闸(提交时过 ≠ 现在够:余额可能被别的请求扣走)· 放行返 None。

    units 优先用 submit 预检快照 params["billing_units"](单位不随排队时间变,只有余额
    会变,免得整簿 Excel 在 worker 里再逐格读一遍);改动上线瞬间队列里的旧 job 无快照
    → 回落现算。不足返 __failed__ 信号 · 别让付费解析跑一半扣不了钱。
    """
    from core import db
    from services.billing import account_status
    from services.billing.pricing import estimate_recon_units

    user_id = str(params.get("user_id"))
    billing = db.get_billing_status_combined(user_id, params.get("tenant_id"))
    if account_status.lookup_failed(billing):
        logger.warning(f"[{tag}] billing lookup failed at run time · user={user_id}")
        return ("__failed__", {"error_code": account_status.LOOKUP_ERROR})
    units = params.get("billing_units")
    if units:
        pdf_units, excel_chars = int(units[0]), int(units[1])
    else:
        pdf_units, excel_chars = estimate_recon_units(files)
    covers, _ = account_status.can_cover_estimate(billing, pdf_units, excel_chars)
    if not covers:
        logger.warning(f"[{tag}] insufficient_balance at run time · user={user_id}")
        return ("__failed__", {"error_code": "insufficient_balance"})
    return None


def _charge_parsed(tag: str, desc_label: str, user_id, tenant_id, pairs) -> None:
    """成功解析件的事后扣费(worker 线程内同步调)· 失败只记 log 不打断任务。

    分类/单位判据单源在 pricing.billed_units_for_parses(失败件/0 行件不收钱)。"""
    from core import db
    from services.billing.pricing import billed_units_for_parses

    try:
        pdf_units, excel_chars = billed_units_for_parses(pairs)
        if pdf_units > 0:
            db.charge_ocr_async(
                user_id, tenant_id, "pdf", pdf_units, None, f"{desc_label} PDF · {pdf_units} 页"
            )
        if excel_chars > 0:
            db.charge_ocr_async(
                user_id,
                tenant_id,
                "excel",
                excel_chars,
                None,
                f"{desc_label} Excel · {excel_chars} 字符",
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"💳 {tag} async charge skip: {e}")


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
        # 对账重活底下就是 OCR,成本归因走 contextvars:submit_ctx 逐件快照提交时刻的
        # 上下文(不能在 worker 里 copy,那时已是空上下文),整批的钱不会落成「未归因」。
        futures = [submit_ctx(ex, fn, it) for it in items]
        return [f.result() for f in futures]
