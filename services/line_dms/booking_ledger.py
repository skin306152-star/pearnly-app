# -*- coding: utf-8 -*-
"""订车推送台账(erp_push_logs)写入 · 从 booking_flow 拆出以守住 500 行硬闸。

request_body.trigger='line_dms',BK 单号进 invoice_no 位(照客户 push 把外部单号放该列
的先例),push_type 保持 'id_card'。qa 块只进摘要(place/term/regis/渠道/总额/凭证有无),
audit 过大不进台账、留会话。
"""

from __future__ import annotations

import json

from core import db
from services.line_dms import qa_cards


def log_booking(user_id: str, ep: dict, payload: dict, result: dict) -> None:
    """按结果如实落台账:成功记 success/200,失败记 failed/0 + error_code。"""
    ok = bool(result.get("ok"))
    qa = payload.get("qa") or {}
    answers = qa.get("answers") or {}
    adv = qa.get("advisor") or {}
    payments = qa.get("payments") or []
    request_body = {
        "adapter": "mrerp_dms",
        "trigger": "line_dms",
        "mode": "booking",
        "customer_id": str((qa.get("customer") or {}).get("id") or ""),
        "car_id": str((answers.get("car") or {}).get("id") or ""),
        "paint_id": str((answers.get("paint") or {}).get("id") or ""),
        "advisor_id": str(adv.get("id") or ""),
        # 归属名与 id 同层:对账翻台账时不用回查主档,也不用跨层拼。
        "advisor_name": str(adv.get("name") or ""),
        "qa": {
            "place_id": str((answers.get("place") or {}).get("id") or ""),
            "term_id": str((answers.get("term") or {}).get("id") or ""),
            "regis_id": str((answers.get("regis") or {}).get("id") or ""),
            "regis_name": str(answers.get("regis_name") or ""),
            "payments": [
                {"channel": str(p.get("channel") or ""), "amount": str(p.get("amount") or "")}
                for p in payments
            ],
            "earnest_total": str(qa_cards.deposit_total(payments)),
            "slip_attached": bool((qa.get("files") or {}).get("slip_mid")),
            "master_snapshot_version": str((qa.get("master_snapshot") or {}).get("version") or ""),
            "master_snapshot_at": str((qa.get("master_snapshot") or {}).get("captured_at") or ""),
            "master_validated_at": str(
                (qa.get("master_validation") or {}).get("validated_at") or ""
            ),
        },
    }
    response_body = {
        **(result.get("response_body") or {}),
        "booking_id": result.get("booking_id", ""),
        "booking_no": result.get("booking_no", ""),
    }
    if "attach_ok" in result:
        response_body["attach_ok"] = result.get("attach_ok")
        response_body["attached"] = result.get("attached", 0)
        response_body["attach_failed"] = result.get("attach_failed") or []
    if not ok:
        response_body["raw_error"] = (result.get("response_body") or {}).get("raw_error", "")
    db.insert_push_log(
        user_id,
        str(ep["id"]),
        None,
        result.get("booking_no") or "",
        str((qa.get("customer") or {}).get("name") or ""),
        None,
        "success" if ok else "failed",
        200 if ok else 0,
        request_body,
        json.dumps(response_body, ensure_ascii=False),
        result.get("error_code"),
        1,
        0,
        "id_card",
    )
