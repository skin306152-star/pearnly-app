# -*- coding: utf-8 -*-
"""业务模块挂点入口(docs/accounting/02 seam):一行 enqueue,做账绝不拖垮业务。

铁规矩:进项 post / 销项 issue / POS 埋单 / 付款的主路径不能因做账失败而失败。
实现:SAVEPOINT 隔离(引擎内任何 DB 错误只回滚到挂点前,业务事务不受污染)+ 全异常吞
(只告警)。模块未开通(accounting 关)= 早退零开销。
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

logger = logging.getLogger("mr-pilot")

_PAYMENT_NS = uuid.UUID("f6b1c9e2-8a4d-4f3b-9c70-1d2e3a4b5c6d")


def enqueue_posting(
    cur,
    *,
    tenant_id: str,
    workspace_client_id,
    source_type: str,
    source_id,
    created_by=None,
    context: Optional[dict] = None,
) -> None:
    """业务事务内调(与业务同 commit)。失败静默吞 + 告警,主路径照常。"""
    if not tenant_id or not workspace_client_id:
        return
    try:
        cur.execute("SAVEPOINT acct_enqueue")
    except Exception as e:
        logger.warning(f"accounting enqueue savepoint failed: {e}")
        return
    try:
        from services.accounting import posting
        from services.modules import store as modules_store

        if not modules_store.is_enabled(cur, tenant_id=tenant_id, module_key="accounting"):
            cur.execute("RELEASE SAVEPOINT acct_enqueue")
            return
        posting.generate_for_source(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=int(workspace_client_id),
            source_type=source_type,
            source_id=source_id,
            created_by=created_by,
            context=context,
        )
        cur.execute("RELEASE SAVEPOINT acct_enqueue")
    except Exception as e:
        logger.warning(f"accounting enqueue failed source={source_type}:{source_id}: {e}")
        try:
            cur.execute("ROLLBACK TO SAVEPOINT acct_enqueue")
        except Exception:
            pass


def void_for_source(
    cur,
    *,
    tenant_id: str,
    workspace_client_id,
    source_type: str,
    source_id,
) -> None:
    """源单作废 → 作废其做账凭证(账本 / ภ.พ.30 进项税同步对冲)。业务事务内调。

    与 enqueue_posting 的关键反差:**不吞错**。enqueue 用 SAVEPOINT 吞错是为护业务过账
    路径;作废反过来——凭证作废失败(如期间已结账/已申报 acct.period_closed)必须让整个
    作废事务回滚,绝不留「单已作废、账本/税表还在算」的不一致。模块未开通 / 无凭证 = no-op。
    """
    if not tenant_id or not workspace_client_id:
        return
    from services.accounting import posting
    from services.accounting import vouchers as jv
    from services.modules import store as modules_store

    if not modules_store.is_enabled(cur, tenant_id=tenant_id, module_key="accounting"):
        return
    voucher = jv.find_active_by_source(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=int(workspace_client_id),
        source_type=source_type,
        source_id=source_id,
    )
    if voucher is None:
        return
    posting.void_voucher(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=int(workspace_client_id),
        voucher_id=voucher["id"],
    )


def void_voucher(cur, *, tenant_id: str, workspace_client_id, voucher_id) -> None:
    """seam:作废指定凭证(带期间锁断言)。供业务模块整单作废逐张撤凭证用,不直连引擎。

    与 void_for_source 同纪律:不吞错,period_closed 等透传 → 调用方整事务回滚。
    """
    from services.accounting import posting

    posting.void_voucher(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=int(workspace_client_id),
        voucher_id=voucher_id,
    )


def payment_event_id(doc_id, paid_after) -> uuid.UUID:
    """付款事件确定性 id:进项付款只更新累计无独立行,以(单+累计已付)派生。

    同一事件重放 → 同 id(幂等防重);多次部分付款 → 各自成凭证。
    """
    return uuid.uuid5(_PAYMENT_NS, f"purchase_pay:{doc_id}:{paid_after}")
