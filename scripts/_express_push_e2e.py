#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Express Push 后端无头 E2E(P1 施工单 §8.1)· 需真实 Postgres。

本地无 DATABASE_URL → 在 prod venv 跑:
    ERP_PUSH_ENABLED=true USER_ID=<有推送权限的测试用户 id> \
    PYTHONPATH=/opt/mrpilot /opt/mrpilot/venv/bin/python scripts/_express_push_e2e.py

走的是真实 push 路径(erp_push.push_to_endpoint → express 分支 → enqueue),并按
/api/erp/push 路由同样的 classify_push_status + insert_push_log 落库,证明该路由会
产出同一条 pending 行。覆盖:pending 入队 → lease → ack success → success;
ack failed×3 → manual;低置信直 manual 不进队列;账套白名单 PDATAT 被拒;
account_set 不符的载荷不被 lease 返回。结束自清(删本次建的 endpoint + 日志)。
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("ERP_PUSH_ENABLED", "true")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import db  # noqa: E402
from services.erp import erp_push  # noqa: E402
from services.erp.express_push import agent_store  # noqa: E402

USER_ID = os.environ.get("USER_ID") or ""

_CFG = {
    "account_set": "DATAT",
    "method": "rpa",
    "fallback_acc": "11-04-02-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
}

_PASS = 0
_FAIL = 0


def check(name, cond):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  PASS · {name}")
    else:
        _FAIL += 1
        print(f"  FAIL · {name}")


def _history(confidence="high", **fover):
    fields = {
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "seller_tax": "0107561000013",
        "subtotal": "375347.20",
        "vat": "26274.30",
        "invoice_number": "RR581231-002",
        "document_type": "tax_invoice",
    }
    fields.update(fover)
    return {
        "id": "",
        "invoice_date": "2015-12-31",
        "invoice_no": "RR581231-002",
        "seller_name": fields["seller_name"],
        "total_amount": "401621.50",
        "confidence": confidence,
        "pages": [{"fields": fields}],
    }


def _push_and_log(ep, history):
    """复刻 /api/erp/push 的落库:push_to_endpoint → classify → insert_push_log。"""
    result = erp_push.push_to_endpoint(ep, history)
    status = db.classify_push_status(result["success"], result.get("error_msg"))
    log_id = db.insert_push_log(
        user_id=USER_ID,
        endpoint_id=str(ep["id"]),
        history_id=None,
        invoice_no=history.get("invoice_no"),
        seller_name=history.get("seller_name"),
        total_amount=None,
        status=status,
        http_status=result.get("http_status"),
        request_body=result.get("request_body"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        attempt=1,
        elapsed_ms=result.get("elapsed_ms", 0),
        trigger="manual",
    )
    return log_id, status


def main():
    if not USER_ID:
        print("FAIL · set USER_ID env (a user with push access)")
        return 1

    # 启动期 schema(幂等)· 租约列折叠在 retry 列 ensure 里。
    db.ensure_erp_retry_columns()
    db.ensure_erp_endpoints_adapter_constraint()
    db.ensure_erp_push_logs_adapter_constraint()
    db.ensure_erp_push_logs_status_constraint()

    created_eps = []
    try:
        ep_id = db.create_erp_endpoint(USER_ID, "E2E Express", "express", dict(_CFG))
        check("create express endpoint", bool(ep_id))
        if not ep_id:
            return 1
        created_eps.append(ep_id)

        token = agent_store.set_agent_token(USER_ID, ep_id)
        check("generate agent token", bool(token))
        ep = db.get_erp_endpoint(USER_ID, ep_id)
        check("token authenticates", agent_store.authenticate(token) is not None)

        # 1) 高置信 → pending,载荷正确
        log1, st1 = _push_and_log(ep, _history())
        check("good history → pending", st1 == "pending" and bool(log1))
        d1 = db.get_push_log_detail(USER_ID, log1)
        rb = d1.get("request_body") if d1 else {}
        check("pending request_body 是正确载荷", bool(rb) and rb.get("account_set") == "DATAT")

        # 2) lease 取到
        jobs = agent_store.lease_pending(ep_id, "agentE2E", 10)
        leased_ids = {j["id"] for j in jobs}
        check("lease 取到该单", log1 in leased_ids)

        # 3) ack success → success + docnum
        res = agent_store.ack(ep_id, log1, "agentE2E", True, express_docnum="RR690001-001")
        check("ack success", res.get("status") == "success")
        d1b = db.get_push_log_detail(USER_ID, log1)
        check("log 变 success", d1b and d1b.get("status") == "success")
        check("回填 express_docnum", "RR690001-001" in str((d1b or {}).get("response_body") or ""))

        # 4) ack failed × 3 → manual
        log2, st2 = _push_and_log(ep, _history(invoice_number="RR581231-003"))
        check("第二单入队 pending", st2 == "pending")
        st = None
        for i in range(3):
            agent_store.lease_pending(ep_id, "agentE2E", 10)  # 重新领(上次失败已释放租约)
            r = agent_store.ack(ep_id, log2, "agentE2E", False, error="rpa timeout")
            st = r.get("status")
        check("ack failed×3 → manual", st == "manual")

        # 5) 低置信 → 直接 manual,不进队列
        log3, st3 = _push_and_log(ep, _history(confidence="low", invoice_number="RR581231-004"))
        check("低置信 → manual", st3 == "manual")
        jobs3 = agent_store.lease_pending(ep_id, "agentE2E", 10)
        check("低置信单不可被 lease", log3 not in {j["id"] for j in jobs3})

        # 6) 账套白名单 PDATAT 被拒
        ep2_id = db.create_erp_endpoint(
            USER_ID, "E2E Express PDATAT", "express", {**_CFG, "account_set": "PDATAT"}
        )
        created_eps.append(ep2_id)
        ep2 = db.get_erp_endpoint(USER_ID, ep2_id)
        _, st_wl = _push_and_log(ep2, _history(invoice_number="RR581231-005"))
        check("白名单 PDATAT 被拒 → manual(不入队)", st_wl == "manual")

        print(f"\nE2E 结果: {_PASS} PASS / {_FAIL} FAIL")
        return 0 if _FAIL == 0 else 1
    finally:
        # 自清:删本次建的 endpoint(连带其推送日志)。
        for eid in created_eps:
            try:
                with db.get_cursor(commit=True) as cur:
                    cur.execute(
                        "DELETE FROM erp_push_logs WHERE endpoint_id = %s AND user_id = %s",
                        (eid, USER_ID),
                    )
                db.delete_erp_endpoint(USER_ID, eid)
            except Exception as e:  # noqa: BLE001
                print(f"  cleanup warn (endpoint {eid}): {e}")


if __name__ == "__main__":
    sys.exit(main())
