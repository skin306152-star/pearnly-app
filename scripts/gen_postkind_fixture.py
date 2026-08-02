#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「未指定过账去向」那条推送日志的 API 形状,喂 tests/e2e/_postkind_fix_local.spec.js。

E2E stub 的数据可以是假的,**被验证的标识符不能是脚本自己编的**(2026-07-26 血泪:35 条深链
全落空却 16 项全绿,因为断言的对象是桩造出来、产品里根本不存在的)。所以这里 reason /
category / posting_fix 一律由真 mapper + 真分类器算出来,脚本只负责把日志行的外围字段
(单号 / 时间 / 端点名)填齐 —— 那些字段没有任何断言挂着。

    python scripts/gen_postkind_fixture.py          # 重写 tests/fixtures/postkind_escalated_log.json

一致性由 tests/unit/test_postkind_fixture_is_real.py 每次跑单测时重算比对:夹具被手改成
产品不会产出的形状就红。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import push_exception_classify as pxc  # noqa: E402
from services.erp.express_push.mapper import build_express_payload  # noqa: E402

FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "postkind_escalated_log.json"

# 永续账套指纹(六家真账标定值,同 test_express_posting_wire)+ 库存路未开 → 画像判
# manual_review → 没声明过账去向的货票 escalate。这是这条死胡同在生产里唯一的成因。
_PERPETUAL_FP = {"stock_master_count": 672, "stcrd_lines": 9300, "stcrd_lines_moving_stock": 8102}
_CONFIG = {
    "account_set": "DATAT",
    "fallback_acc": "11-04-02-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
    "catalog_fingerprint": _PERPETUAL_FP,
}
_HISTORY = {
    "id": "h-pk-1",
    "invoice_date": "2026-07-15",
    "invoice_no": "RR690715-004",
    "total_amount": "2289.80",
    "fields": {
        "seller_name": "บริษัท ปตท จำกัด (มหาชน)",
        "seller_tax": "0107561000013",
        "buyer_name": "Sister Makeup Steward Co., Ltd.",
        "subtotal": "2140.00",
        "vat": "149.80",
        "invoice_number": "RR690715-004",
        "posting_item_type_manual": "goods",
        "items": [
            {"name": "แชมพู 500ml", "subtotal": "1400.00"},
            {"name": "ครีมนวดผม 250ml", "subtotal": "740.00"},
        ],
    },
}


def build_fixture() -> dict:
    """跑真 mapper → 真分类器,还原 GET /api/erp/logs 对这条票回的那一项。"""
    res = build_express_payload(_HISTORY, config=_CONFIG)
    if res.ok:
        raise SystemExit("这条本该 escalate · 画像判据变了就得重看这条死胡同还在不在")
    error_msg = "EXPRESS_MANUAL: " + res.reason
    # 与 preflight._block 落库的 request_body 同构(mapping 阶段那一支)。
    request_body = {"adapter": "express", "manual_reason": res.reason}
    if res.items:
        request_body["items"] = res.items

    item = {
        "id": "log-pk-1",
        "endpoint_id": "ep-1",
        "history_id": _HISTORY["id"],
        "invoice_no": _HISTORY["invoice_no"],
        "seller_name": _HISTORY["fields"]["seller_name"],
        "ocr_buyer_name": _HISTORY["fields"]["buyer_name"],
        "total_amount": _HISTORY["total_amount"],
        "status": "manual",
        "http_status": 0,
        "error_msg": error_msg,
        "attempt": 1,
        "elapsed_ms": 12,
        "trigger": "auto",
        "created_at": "2026-07-31T09:15:00",
        "retry_count": 0,
        "max_retries": 3,
        "next_retry_at": None,
        "endpoint_name": "Express · DATAT",
        "endpoint_adapter": "express",
        "push_type": "invoice",
        "push_stage": "needs_review",
        "category": pxc.classify_push_exception(error_msg),
        "posting_fix": pxc.derive_posting_fix(error_msg, request_body),
    }
    return {"items": [item], "total": 1}


if __name__ == "__main__":
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(
        json.dumps(build_fixture(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {FIXTURE_PATH}")
