# -*- coding: utf-8 -*-
"""汇总表批量落库:每行 → 一条 ocr_history(ERP 推送/记账的唯一读源)。

事务所拿客户汇总表是**替客户记账、推 ERP**,不是替客户**开票**——客户的销售早已开过票/或是
现金流水,Pearnly 这里再往账本/发票工作台建"待开"草稿=把记账和开票两件事混在一起、造重复幻单。
故本模块**只写 ocr_history**(MR.ERP/Express 推送读源;记录落"识别记录",从那里推 ERP),不建
账本单据。逐行独立:某行失败只该行落 failed,不连坐其它行(真实失败要看得见,不是全成功的假象)。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core import db

_SUMMARY_SOURCE = "summary_table_batch"


def _clean_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """剥内部下划线字段(_direction/_walkin/_product_code)→ ERP mapper / ocr_history 读的干净 fields。"""
    return {k: v for k, v in fields.items() if not k.startswith("_")}


def _write_ocr_history(*, created_by, tenant_id, ws_id, fields, batch_ref, index) -> Optional[str]:
    """写推送/记账读源。不建账本单据故 source_ref 留空;workspace_client_id 让推送时能解析账套
    税号判方向。"""
    return db.insert_ocr_history(
        user_id=created_by,
        filename=f"summary-{batch_ref}-{index + 1}",
        page_count=1,
        pages=[{"fields": fields, "is_copy": False, "is_duplicate": False}],
        # 汇总批量=确定性精确数据(表里金额或量×固定单价算出,无 OCR 不确定性)→ 高置信,
        # 让它过 Express/MR.ERP 推送的 low_confidence_band 闸(闸只认 high/auto)。
        confidence="high",
        elapsed_ms=0,
        source=_SUMMARY_SOURCE,
        source_ref=None,
        tenant_id=tenant_id,
        workspace_client_id=ws_id,
    )


def commit_rows(
    *,
    tenant_id: str,
    workspace_client_id: int,
    created_by: Optional[str],
    rows: List[Dict[str, Any]],
    batch_ref: str = "batch",
) -> List[Dict[str, Any]]:
    """整批写记账料。rows = [{row_index, fields}](已过 mapping;judge 的硬阻断行不应传进来)。

    每行写一条 ocr_history(insert_ocr_history 自管事务)。返回逐行结果
    [{row_index, status(created|failed), ocr_history_id?, error?}]。
    """
    results: List[Dict[str, Any]] = []
    for i, r in enumerate(rows):
        fields = _clean_fields(r.get("fields") or {})
        try:
            ocr_id = _write_ocr_history(
                created_by=created_by,
                tenant_id=tenant_id,
                ws_id=workspace_client_id,
                fields=fields,
                batch_ref=batch_ref,
                index=r.get("row_index", i),
            )
            results.append(
                {
                    "row_index": r.get("row_index", i),
                    "status": "created" if ocr_id else "failed",
                    "ocr_history_id": ocr_id,
                }
            )
        except Exception as e:  # noqa: BLE001 — 逐行兜底:该行失败不连坐,错误如实回传
            results.append(
                {
                    "row_index": r.get("row_index", i),
                    "status": "failed",
                    "error": str(getattr(e, "code", None) or e)[:200],
                }
            )
    return results
