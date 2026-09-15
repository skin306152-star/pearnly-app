# -*- coding: utf-8 -*-
"""订车提交前的权威主档复核对(读-only),写路径不受它控制。

提交前必须按 DMS **当下**的主档判能否继续,而销售账号常看不到车型/颜色/收款银行的全表 ——
用销售的不完整视图复核,会把「DMS 里明明还在」的选择判成主档变更。所以复核走权威只读
会话(配了独立管理员凭据组时由 dms_admin_read 借管理员,未配即销售),整块只解析一次
管理员 transport。

本模块只做读取与结论,不写任何 DMS 单据:readonly_preflight 抓一份实时主档(+选中车型的
颜色)再交给 master_contract.reconcile 判。建单/客户写入/附件挂载仍由 booking_flow 在
**原销售 transport** 上执行,只提交一次。
"""

from __future__ import annotations

from typing import Any, Dict, List

from services.line_dms import master_contract
from services.line_dms.qa_util import find_row


def readonly_preflight(
    client: Any,
    adapter: Any,
    qa: dict,
    *,
    fetch_masters,
    fetch_payment_banks,
) -> Dict[str, Any]:
    """实时复核主档:返回 {status, field, code, qa} 或 {status: "ok", masters, paints, qa}。

    `client` 是权威读取会话上的 DMSClient(`fetch_masters`/`_bshsd_all` 走它的 transport)。
    颜色读不到(回 None)按 ERR_DMS_MASTER_UNAVAILABLE 处理 —— 不拿空表冒充「这车没颜色」。
    """
    from services.erp.mrerp_dms_client_base import DMSClientError

    answers = (qa.get("answers") or {}) if isinstance(qa, dict) else {}
    live_masters = {**fetch_masters(client), **fetch_payment_banks(adapter)}
    selected_car_id = str((answers.get("car") or {}).get("id") or "")
    selected_car = find_row(live_masters.get("cars"), selected_car_id)
    live_paints: List[list] = []
    if selected_car is not None:
        live_paints = client._bshsd_all("txtcarpaint", idcar=selected_car_id)
        if live_paints is None:
            raise DMSClientError(
                f"DMS paint master unavailable for car {selected_car_id!r}",
                "ERR_DMS_MASTER_UNAVAILABLE",
            )
    preflight = master_contract.reconcile(qa, live_masters, live_paints)
    if preflight["status"] != "ok":
        return {
            "status": preflight["status"],
            "field": preflight.get("field", ""),
            "code": preflight.get("code", "ERR_DMS_MASTER_CHANGED"),
            "qa": preflight["qa"],
        }
    return {
        "status": "ok",
        "masters": live_masters,
        "paints": live_paints,
        "qa": preflight["qa"],
    }
