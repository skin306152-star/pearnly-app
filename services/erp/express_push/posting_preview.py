# -*- coding: utf-8 -*-
"""推送前预览:算「这批推下去会怎样」的 gate + 逐行解析 + 画像(纯函数 · 无 IO · 可单测)。

供 /api/erp/posting-preview 端点 + 步④前端「例外捞出来给人裁」。对标成熟对账/导入 UI:能确定的
自动过,只把例外(拿不准 / 跨类)捞给人。gate 四态决定前端是否打断:
  ok            全干净 → 一行摘要直接推,不打断
  confirm_profile 画像待确认(unknown/mixed/首次)→ 一次性问这家记账模式,存 config 后不再问
  escalate      永续客户 + 库存路未开 → 商品行不可自动落,留人工(不假装成功)
  decide_items  有行 fuzzy 或【只存在于库存目录】→ 捞出例外给人看 · 默认 firm-safe 另建非库存
                (逐项复用 override 是后续增量,当前仅透明展示不阻断)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.erp.express_push.catalog_resolver import build_name_index, resolve_product_indexed
from services.erp.express_push.posting_profile import profile_from_config


def compute_posting_preview(
    docs: List[Dict[str, Any]], config: Optional[Dict[str, Any]], *, stock_enabled: bool = False
) -> Dict[str, Any]:
    """算推送前预览。

    docs = [{history_id, items:[{name}, ...]}, ...];config = 端点 config(含 reported_products /
    catalog_fingerprint / posting_profile)。返回 {profile, gate, items, summary}。
    """
    profile = profile_from_config(config, stock_enabled=stock_enabled)
    products = (config or {}).get("reported_products") or []
    index = build_name_index(products)  # 预建一次骨架索引(H1:精确命中 O(1),不每行重扫)
    # 本客户新建落哪类:stock 模式建库存,其余建非库存(firm-safe 默认)。
    target_kind = "stock" if profile.posting_mode == "stock" else "non_stock"

    items_out: List[Dict[str, Any]] = []
    reuse = new = confirm = 0
    for d in docs or []:
        for it in d.get("items") or []:
            name = str((it or {}).get("name") or "").strip()
            if not name:
                continue
            v = resolve_product_indexed(name, index, products)
            status = v.get("status")
            row: Dict[str, Any] = {"name": name, "status": status}
            if status == "reuse":
                row["code"] = v.get("code")
                row["kind"] = v.get("kind")
                # 跨类:命中的是库存目录,但本客户按非库存落 → 复用库存码(挂客户库存)vs 另建非库存,
                # 是有会计后果的选择,交人裁一次(默认另建 · firm-safe)。
                row["cross_kind"] = bool(v.get("kind") == "stock" and target_kind == "non_stock")
                reuse += 1
            elif status == "confirm":
                row["guess"] = v.get("guess")
                row["sim"] = v.get("sim")
                confirm += 1
            else:
                new += 1
            items_out.append(row)

    # gate 优先级:escalate(不可自动落)> confirm_profile(画像未定)> decide_items(有例外)> ok。
    if profile.blocks_auto_posting():
        gate = "escalate"
    elif profile.needs_confirm:
        gate = "confirm_profile"
    elif confirm or any(r.get("cross_kind") for r in items_out):
        gate = "decide_items"
    else:
        gate = "ok"

    return {
        "profile": profile.to_dict(),
        "gate": gate,
        "items": items_out,
        "summary": {"reuse": reuse, "new": new, "confirm": confirm},
    }
