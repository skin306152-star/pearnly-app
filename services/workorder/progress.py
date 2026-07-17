# -*- coding: utf-8 -*-
"""工单跑批中逐件进度只读投影(P-4 classify + J-B reconcile 银行流水)。

从 api.py 拆出(铁律 #27.1 单文件 <500 行 · api.py 加 J-B bank_progress 后到 508,起票
搬这两个纯函数减负)。两段进度共用同一个 {step, processed, total} 形状,只在各自步位
现算,零副作用、零新状态表——事件流仍是唯一事实源,这里只是把两段只读现算搬了个文件
位置,api.order_detail() 的调用点/传参/返回值逐字节不变(见 tests/unit/test_workorder_api.py
的 ClassifyProgressTests/BankProgressTests,行为断言原样保留)。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from services.workorder import kinds
from services.workorder.steps import sort as sort_step


def classify_progress(wo: dict, items: list[dict], classified: dict) -> Optional[dict]:
    """classify 逐件进度(P-4:219 秒别再像死机)。仅当工单正卡在 classify 步时给一份
    {processed, total};其余步返 None(前端只在 classify 期显进度条)。

    classified 是调用方(order_detail)已回放好的 item_classified 索引,不建新状态表:
    total = 本单要过 OCR 的图片件数(file_ref 是图片扩展名);processed = 其中已落
    item_classified 事件的件数(classify 逐件独立事务提交,已处理件即时可见)——processed
    随 OCR 推进单调递增,跑完 == total。销项直读/银行件不过 OCR,不计入。"""
    if wo.get("current_step") != "classify":
        return None
    image_ids = {
        it["id"]
        for it in items
        if Path(it.get("file_ref") or "").suffix.lower() in sort_step.IMAGE_EXTS
    }
    if not image_ids:
        return None
    processed = sum(1 for iid in image_ids if iid in classified)
    return {"step": "classify", "processed": processed, "total": len(image_ids)}


def bank_progress(wo: dict, items: list[dict], bank_parsed: dict) -> Optional[dict]:
    """reconcile 步银行流水逐件进度(J-B:分批传料期间前端「读对账单 X/N」,同
    classify_progress 的现算范式——只在工单正卡在 reconcile 步时给一份 {processed,total},
    其余步返 None。bank_parsed 是调用方已回放好的 item_bank_parsed 索引,不建新状态表。"""
    if wo.get("current_step") != "reconcile":
        return None
    bank_ids = {it["id"] for it in items if it.get("kind") == kinds.BANK_STATEMENT}
    if not bank_ids:
        return None
    processed = sum(1 for iid in bank_ids if iid in bank_parsed)
    return {"step": "reconcile", "processed": processed, "total": len(bank_ids)}
