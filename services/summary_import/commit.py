# -*- coding: utf-8 -*-
"""汇总表批量落库:每行 → 一条 ocr_history,并当场转正式单据(purchase_docs/sales_documents)。

2026-08-07 拍板改向(推翻此前"只写 ocr_history 不建单据"的产品判断):商品收发存报表读的是
purchase_docs(posted)/sales_documents(issued),只写识别记录会让汇总表导入的行永远进不了
报表 —— 报表需要正式单据当数据源,这条硬需求盖过了先前"记账/开票混同=造幻单"的顾虑。
建单据不是替客户"新开一张票":doc_number 仍是表里的原始票号(见 intake_bridge.sales_leg
"登记不发号"的注释),系统只是把事务所早就在做的记账动作接上正式单据。写完 ocr_history 后
调 services.intake_bridge.convert.convert_histories,与录入工作台「确认」按钮走同一套桥
(方向判定/幂等/防重不重复实现,一处改全处生效)。

存量边界(2026-08-07 拍板 · 明确不做):source='summary_table_batch' 的历史记录**不自动
回填**——那是真租户真账,批量突变必须 Zihao 单独拍板;本桥只接管新 commit 之后写入的行。

逐行独立:某行失败只该行落 failed,不连坐其它行(真实失败要看得见,不是全成功的假象)。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core import db
from services.intake_bridge import convert as convert_svc

logger = logging.getLogger("mr-pilot")

_SUMMARY_SOURCE = "summary_table_batch"


def _clean_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
    """剥内部下划线字段(_direction/_walkin/_product_code)→ ERP mapper / ocr_history 读的干净 fields。

    _direction(批次声明的方向)剥前先映射进 fields.direction —— intake_bridge.resolve_direction
    读的是这一列,不映射的话批量导入永远只能靠税号锚点判方向,账套没税号时就 no_direction 卡死。
    已有 direction 值不覆盖(与 direction.apply_batch_direction 同一条"逐行裁决优先"准则)。
    """
    declared = str(fields.get("_direction") or "").strip()
    out = {k: v for k, v in fields.items() if not k.startswith("_")}
    if declared and not out.get("direction"):
        out["direction"] = declared
    return out


def _write_ocr_history(*, created_by, tenant_id, ws_id, fields, batch_ref, index) -> Optional[str]:
    """写推送/记账读源。source_ref 留空(没有上游票据文件可反指);正式单据事后由
    _bridge_to_documents 反过来挂 ocr_history_id,不是这里正向填 source_ref。
    workspace_client_id 让推送/建单时都能解析账套税号判方向。"""
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


def _bridge_to_documents(
    *, tenant_id: str, created_by: Optional[str], history_ids: List[str]
) -> tuple:
    """新写的 history_ids → intake_bridge 当场转正式单据。失败不影响已写入的记账料
    (ocr_history 早已各自 commit),只把桥结果如实回传;无 created_by 没法归属就不转。"""
    if not history_ids or not created_by:
        return [], []
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=created_by, commit=True) as cur:
            bridged = convert_svc.convert_histories(
                cur, tenant_id=tenant_id, user_id=created_by, history_ids=history_ids
            )
        return bridged["converted"], bridged["skipped"]
    except Exception as e:
        logger.warning(f"summary-import → intake_bridge convert 失败(记账料已写入,不受影响): {e}")
        return [], []


def commit_rows(
    *,
    tenant_id: str,
    workspace_client_id: int,
    created_by: Optional[str],
    rows: List[Dict[str, Any]],
    batch_ref: str = "batch",
) -> Dict[str, Any]:
    """整批写记账料 + 当场转正式单据。rows = [{row_index, fields}](已过 mapping;judge 的
    硬阻断行不应传进来)。

    每行写一条 ocr_history(insert_ocr_history 自管事务)。返回
    {rows:[{row_index,status(created|failed),ocr_history_id?,error?}],
     converted:[...], skipped:[...]}(converted/skipped 结构见 services.intake_bridge.convert)。
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
    new_ids = [
        r["ocr_history_id"] for r in results if r["status"] == "created" and r["ocr_history_id"]
    ]
    converted, skipped = _bridge_to_documents(
        tenant_id=tenant_id, created_by=created_by, history_ids=new_ids
    )
    return {"rows": results, "converted": converted, "skipped": skipped}
