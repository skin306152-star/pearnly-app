# -*- coding: utf-8 -*-
"""进项票票面级查重指纹 + 从事件流重建查重表(从 classify 抽出 · 单一职责 · 500 行铁律)。

classify 归堆进项票时要认「同一张票在本单里重复上传」(税号|票号|含税合计 三要素指纹),
且断点续跑时必须从已提交事件重建这张查重表——否则逐件提交后被 kill,已落库原件不在 pending
里,内存从空建会让其复件漏判 duplicate → R1 双计(C1 打回单的静默钱洞)。这两件事从 classify
拆出成纯装配层:classify 只管编排,指纹算法/重建逻辑单一职责在此。跨单去重(R2B)是另一回事
(那是哈希级、跨工单省 OCR,见 ocr_reuse);这里是单内票面级、防重复计税。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from services.purchase.totals import dedupe_key
from services.workorder import evidence, kinds

# item_classified 是存量事件词(evidence/reconcile/classify 均用),本模块只读回放不新增语义。
_EVT_CLASSIFIED = "item_classified"


def purchase_fingerprint(fields: dict) -> Optional[str]:
    """票面级查重指纹(任务包 §5:税号|票号|含税合计,复用 purchase.totals.dedupe_key)。"""
    digest = dedupe_key(
        supplier_tax=fields.get("seller_tax"),
        doc_no=fields.get("invoice_number"),
        grand_total=fields.get("total_amount") or fields.get("subtotal"),
    )
    return f"doc:{digest}" if digest else None


def replay_seen_fingerprints(ctx) -> dict:
    """从已提交 item_classified 事件重建进项查重表 {指纹: 原件文件名}。

    指纹三要素(seller_tax/invoice_number/total_amount)都在事件的 money 快照里,与在跑时
    对 OCR fields 算指纹同源同值;文件名从 items 表按 item_id 回查(duplicate_of:{name} 的
    展示口径不变)。只认 kind=purchase_invoice(方向票/复件事件无 money 或非该 kind,天然
    跳过——与在跑时只为进项票种表的语义一致)。首个持有者在先(事件按落库序,复件不覆写)。"""
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    classified = evidence.replay_items_by_type(events, _EVT_CLASSIFIED)
    if not classified:
        return {}
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    ref_by_id = {it["id"]: it.get("file_ref") for it in items}
    seen: dict[str, str] = {}
    for item_id, rec in classified.items():
        payload = rec["payload"]
        if payload.get("kind") != kinds.PURCHASE_INVOICE:
            continue
        fp = purchase_fingerprint(payload.get("money") or {})
        if fp and fp not in seen:
            seen[fp] = Path(ref_by_id.get(item_id) or "").name
    return seen
