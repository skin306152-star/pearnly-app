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
        try:
            from services.accounting import posting_failures

            posting_failures.mark_resolved(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                source_type=source_type,
                source_id=source_id,
            )
        except Exception as e:
            logger.warning(f"accounting failure close failed source={source_type}:{source_id}: {e}")
        cur.execute("RELEASE SAVEPOINT acct_enqueue")
    except Exception as e:
        logger.warning(f"accounting enqueue failed source={source_type}:{source_id}: {e}")
        try:
            cur.execute("ROLLBACK TO SAVEPOINT acct_enqueue")
        except Exception:
            pass
        try:
            from services.accounting import posting_failures

            posting_failures.record_failure(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                source_type=source_type,
                source_id=source_id,
                error=str(e),
                created_by=created_by,
                context=context,
            )
        except Exception as rec_e:
            logger.warning(
                f"accounting failure record failed source={source_type}:{source_id}: {rec_e}"
            )


def void_for_source(
    cur,
    *,
    tenant_id: str,
    workspace_client_id,
    source_type: str,
    source_id,
    created_by=None,
) -> None:
    """源单作废 → 作废/红冲其做账凭证(账本 / ภ.พ.30 同步对冲)。业务事务内调。

    与 enqueue_posting 的关键反差:**不吞错**。enqueue 用 SAVEPOINT 吞错是为护业务过账路径;
    作废反过来——凭证处理失败必须让整个作废事务回滚,绝不留「单已作废、账本/税表还在算」的不一致。
    期间已结/已申报 → 走红冲(当期反向凭证)而非 void(见 void_or_reverse)。模块未开 / 无凭证 = no-op。
    """
    if not tenant_id or not workspace_client_id:
        return
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
    void_or_reverse(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=int(workspace_client_id),
        voucher_id=voucher["id"],
        created_by=created_by,
    )


def void_or_reverse(
    cur, *, tenant_id: str, workspace_client_id, voucher_id, created_by=None
) -> None:
    """seam:开放期 → 作废凭证;已结/已申报期 → 当期红冲(反向凭证·原凭证不动·docs/purchasing/04)。

    供业务整单作废/更正逐张处理凭证用(不直连引擎)。已报历史绝不篡改,调整落当期。不吞错:
    period_closed / no_open_period 等透传 → 调用方整事务回滚。已 void → no-op。
    """
    from services.accounting import posting
    from services.accounting import settings as acct_settings
    from services.accounting import vouchers as jv

    ws = int(workspace_client_id)
    voucher = jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=ws, voucher_id=voucher_id
    )
    if voucher is None or voucher["status"] == "void":
        return
    settings = acct_settings.get_settings(cur, tenant_id=tenant_id, workspace_client_id=ws)
    if acct_settings.is_period_closed(settings, voucher["period"]):
        posting.reverse_voucher(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=ws,
            voucher_id=voucher_id,
            created_by=created_by,
        )
    else:
        posting.void_voucher(
            cur, tenant_id=tenant_id, workspace_client_id=ws, voucher_id=voucher_id
        )


def payment_event_id(doc_id, paid_after) -> uuid.UUID:
    """付款事件确定性 id:进项付款只更新累计无独立行,以(单+累计已付)派生。

    同一事件重放 → 同 id(幂等防重);多次部分付款 → 各自成凭证。
    """
    return uuid.uuid5(_PAYMENT_NS, f"purchase_pay:{doc_id}:{paid_after}")
