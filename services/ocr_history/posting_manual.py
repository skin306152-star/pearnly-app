# -*- coding: utf-8 -*-
"""F5 人工裁决(L4)· 复核屏改现/赊、货/费 → 窄写主页 fields 的两把手动键。

只改 posting_payment_manual / posting_item_type_manual 两键(payment_verdict / choose_doc_type
的最高优先级判据,见 services/erp/express_push/common.py · services/erp/mrerp_http/routing.py),
不走 update_ocr_history_pages(那会 bump edit_count + 触发反馈捕获,把"人工点了现结/记货品"这类
过账元信息误当成"用户改了票面事实"去学反馈)。独立小文件,不塞进已近上限的 mutations.py。
"""

from __future__ import annotations

import json as _json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from core import db
from services.purchase.field_clean import clean_tax_id

logger = logging.getLogger(__name__)

# 路由层的"不动该字段"哨兵:与 None(=显式删键恢复自动判据)区分开,不能共用默认值。
UNSET: Any = object()

_PAYMENT_VALUES = {"cash", "credit"}
_ITEM_TYPE_VALUES = {"goods", "expense"}


@dataclass(frozen=True)
class PostingManualResult:
    """update_history_posting_manual 的结果:ok=False → 路由层 404。ok=True 时顺带带出
    workspace_client_id + 主页卖方税号(SELECT 已取到),喂 backflow_supplier_profile 免它
    再整单重拉一次 get_ocr_history_detail。"""

    ok: bool
    workspace_client_id: Optional[int] = None
    seller_tax: str = ""


def _primary_page_index(pages: list) -> int:
    for i, p in enumerate(pages):
        if isinstance(p, dict) and not p.get("is_duplicate") and not p.get("is_copy"):
            return i
    return 0


def update_history_posting_manual(
    user_id: str,
    record_id: str,
    tenant_id: Optional[str] = None,
    *,
    payment: Any = UNSET,
    item_type: Any = UNSET,
) -> PostingManualResult:
    """写/清主页 fields 的人工裁决键。payment/item_type 三态:
    UNSET(缺省,不传该 kwarg)= 不动该字段;None = 删键(退回自动判据);合法值 = 写入。
    """
    if payment is UNSET and item_type is UNSET:
        return PostingManualResult(False)
    try:
        with db.get_cursor_rls(tenant_id=tenant_id, user_id=user_id, commit=True) as cur:
            if tenant_id:
                scope_sql = "AND user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)"
                scope_param: Any = tenant_id
            else:
                scope_sql = "AND user_id = %s::uuid"
                scope_param = user_id

            cur.execute(
                f"SELECT pages, workspace_client_id FROM ocr_history "
                f"WHERE id = %s::uuid {scope_sql}",
                (record_id, scope_param),
            )
            row = cur.fetchone()
            if not row or not row.get("pages"):
                return PostingManualResult(False)
            pages = list(row["pages"])
            idx = _primary_page_index(pages)
            page = dict(pages[idx]) if isinstance(pages[idx], dict) else {}
            fields = dict(page.get("fields") or {})

            if payment is not UNSET:
                if payment in _PAYMENT_VALUES:
                    fields["posting_payment_manual"] = payment
                else:
                    fields.pop("posting_payment_manual", None)
            if item_type is not UNSET:
                if item_type in _ITEM_TYPE_VALUES:
                    fields["posting_item_type_manual"] = item_type
                else:
                    fields.pop("posting_item_type_manual", None)

            seller_tax = clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id"))
            page["fields"] = fields
            pages[idx] = page
            # UPDATE 自带归属条件(纵深防御 · 多租户铁律:写语句不依赖前置 SELECT 的验证)。
            cur.execute(
                f"UPDATE ocr_history SET pages = %s::jsonb, updated_at = NOW() "
                f"WHERE id = %s::uuid {scope_sql}",
                (_json.dumps(pages, ensure_ascii=False), record_id, scope_param),
            )
            if cur.rowcount <= 0:
                return PostingManualResult(False)
            return PostingManualResult(True, row.get("workspace_client_id"), seller_tax)
    except Exception as e:
        logger.warning(f"update_history_posting_manual skip (id={record_id}): {e}")
        return PostingManualResult(False)


def backflow_supplier_profile(
    *,
    record_id: str,
    tenant_id: Optional[str],
    payment: Optional[str],
    item_type: Optional[str],
    workspace_client_id: Optional[int],
    seller_tax: str,
) -> None:
    """F4 回流(L2):复核屏这次改的现/赊或货/费,顺手记进供应商过账档案的默认值,同供应商
    下次免重复裁决(payment_verdict/choose_doc_type 第四级判据)。workspace_client_id/seller_tax
    由 update_history_posting_manual 的 SELECT 顺带带出(省一次 get_ocr_history_detail 整单重拉)。
    seller_tax 命中账套自家税号(销项票)时跳过 · 供应商档案没有"卖给自己"这维度。
    失败只 warning,不挡本次保存。
    """
    if not payment and not item_type:
        return
    if not workspace_client_id or not tenant_id or not seller_tax:
        return
    try:
        from services.purchase.supplier_posting import upsert_profile
        from services.sales.seller_profile import get_seller

        with db.get_cursor(commit=True) as cur:
            # 供应商档案语义 = 采购习惯,销项票(账套自己是卖方)seller_tax 是账套自家税号,
            # 没有"供应商"这维度;照写会留一行以自家税号为锚的死档案(采购判定永远匹配不到)。
            # 查不到账套税号时保守照旧回流,别把正常采购回流误杀。
            own = get_seller(cur, tenant_id=tenant_id, workspace_client_id=int(workspace_client_id))
            own_tax = clean_tax_id((own or {}).get("tax_id"))
            if own_tax and own_tax == seller_tax:
                return
            upsert_profile(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=int(workspace_client_id),
                seller_tax_id=seller_tax,
                default_payment=payment,
                default_item_type=item_type,
                source="correction",
            )
    except Exception as e:
        logger.warning(f"F4 回流 supplier profile 失败(不挡保存,id={record_id}): {e}")
