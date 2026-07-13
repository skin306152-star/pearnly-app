# -*- coding: utf-8 -*-
"""真复现集成测试的子进程(test_workorder_reaper_interrupt.py 专用)。

在独立进程里把一张工单按生产路径推进(抢租约 → run_requested → runner.advance),
OCR 换成慢速桩(逐件 sleep,给父进程硬杀本进程的窗口)。进程死亡必须是真的——父进程
TerminateProcess,无 finally、无收尾,留下 status=running + 未过期租约的事故现场。

env 契约(父进程注入):DATABASE_URL / WO_TENANT / WO_ID / WO_OWN_TAX(方向锚税号)
/ WO_OCR_DELAY(秒/件)。父进程另设 PEARNLY_WORKORDER_OCR_CONCURRENCY=1 保证逐件
顺序提交,检查点计数确定。
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _slow_ocr_stub(own_tax: str, delay: float):
    """每件 sleep 后返回一张干净进项票(买方=自家 → purchase_invoice,钱字段勾稽平,
    卖方税号/票号按文件名唯一 → 不触票面查重)。"""

    def read(path: str) -> dict:
        time.sleep(delay)
        seq = "".join(ch for ch in Path(path).stem if ch.isdigit()) or "0"
        return {
            "document_type": "tax_invoice",
            "buyer_tax": own_tax,
            "seller_tax": f"1{int(seq):012d}",
            "invoice_number": f"INV-{seq}",
            "subtotal": "100.00",
            "vat": "7.00",
            "total_amount": "107.00",
        }

    return read


def main() -> None:
    from core import db
    from services.workorder import runner, store
    from services.workorder.steps import classify

    tenant = os.environ["WO_TENANT"]
    wo_id = os.environ["WO_ID"]
    own_tax = os.environ["WO_OWN_TAX"]
    delay = float(os.environ.get("WO_OCR_DELAY", "0.8"))

    classify._ocr_image = _slow_ocr_stub(own_tax, delay)
    classify._resolve_own_tax_id = lambda ctx: own_tax
    classify._resolve_own_name = lambda ctx: None
    classify._resolve_own_names = lambda ctx: []
    classify._m1_enabled = lambda ctx: False

    owner = f"run:{uuid.uuid4().hex}"
    store.ensure_runtime()
    with db.get_cursor(commit=True) as cur:
        if not store.acquire_run_lease(
            cur,
            tenant_id=tenant,
            work_order_id=wo_id,
            owner=owner,
            ttl_seconds=runner.run_lease_ttl_seconds(),
        ):
            raise SystemExit("lease acquisition failed - stale test state")
        store.append_event(
            cur,
            tenant_id=tenant,
            work_order_id=wo_id,
            step=runner.RUN_STEP,
            event_type=runner.EVT_RUN_REQUESTED,
            actor="user:e2e",
        )
    runner.advance(tenant, wo_id, owner)


if __name__ == "__main__":
    main()
