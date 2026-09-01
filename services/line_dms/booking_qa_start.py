# -*- coding: utf-8 -*-
"""Start a LINE booking questionnaire from one strict live DMS snapshot."""

from __future__ import annotations

from services.line_dms import qa_cards, store
from services.line_dms._out import _send, _thr
from services.line_dms.master_contract import MasterSyncError, build_snapshot


async def start(
    tenant_id,
    line_user_id,
    endpoint_id,
    customer_id,
    customer_name,
    id_card_mid,
    *,
    persist,
    send_step,
    resolve_endpoint,
    get_masters,
    resolve_advisor,
    reply_token=None,
    draft=None,
    user_id="",
    summary=None,
) -> None:
    """Resolve the operator and freeze the live master bundle used by this session."""
    endpoint = await _thr(resolve_endpoint, user_id, endpoint_id)
    advisor, dms_username = (None, "")
    snapshot = None
    if endpoint:
        try:
            live_masters = await _thr(
                get_masters,
                endpoint,
                force_refresh=True,
                require_complete=True,
            )
            snapshot = build_snapshot(live_masters)
        except MasterSyncError as exc:
            await _thr(store.clear_session, tenant_id, line_user_id)
            _send(line_user_id, qa_cards.master_problem(exc.code))
            return
        advisor, dms_username = await _thr(
            resolve_advisor,
            endpoint,
            masters=live_masters,
        )
    if advisor is None:
        await _thr(store.clear_session, tenant_id, line_user_id)
        msg = qa_cards.no_endpoint() if not endpoint else qa_cards.advisor_block_msg(dms_username)
        _send(line_user_id, msg)
        return

    qa = {
        "step": "place",
        "endpoint_id": str(endpoint_id or ""),
        "customer": {"id": str(customer_id or ""), "name": customer_name or ""},
        "advisor": advisor,
        "draft": dict(draft or {}),
        "summary": dict(summary or {}),
        "user_id": str(user_id or ""),
        "files": {"id_card_mid": id_card_mid or None, "slip_mid": None},
        "answers": {},
        "payments": [],
        "pending_channel": {},
        "audit": [],
        "master_snapshot": snapshot,
    }
    await persist(tenant_id, line_user_id, qa)
    await send_step(tenant_id, line_user_id, qa, "place", reply_token)
