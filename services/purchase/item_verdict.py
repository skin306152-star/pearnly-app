# -*- coding: utf-8 -*-
"""货/费判据(采购单据 = 可抵扣进项货品 vs 不可抵扣费用)· 单一事实源。

Express 采购车道(express_push.mapper.build_express_payload)与 MR.ERP 路由
(mrerp_http.routing.choose_doc_type)各自要把同一张票分流成「货品」或「费用」,此前
两处各自重复一份"人工优先 + judge_direction 兜底"的判据——两处判据一旦漂移,同一张票
会在两条推送车道被判成不同类型(可抵扣进项税是否入账不是习惯而是会计口径,必须唯一)。
抽成这个 helper 后,两处调用点逐字等价。
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

SRC_MANUAL = "manual"


def item_verdict(fields: Dict[str, Any]) -> Tuple[bool, str]:
    """(is_expense, src)。

    人工裁决(posting_item_type_manual · 复核屏显式点过)优先于自动判据——会计裁决,
    不是习惯裁决:有完整税票 = 可抵进项,票面法定证据不许被自动判据/档案习惯压过。
    无人工裁决 → judge_direction(与 Pearnly 自身单据同口径)兜底,src 带上判到的
    kind(purchase_invoice/expense)供排障——沿用两处调用点此前各自打的日志值域。
    """
    manual = str(fields.get("posting_item_type_manual") or "").strip().lower()
    if manual in ("expense", "goods"):
        return manual == "expense", SRC_MANUAL

    from services.purchase.intake import judge_direction

    kind, _ = judge_direction(fields)
    return kind == "expense", f"judge_direction={kind}"
