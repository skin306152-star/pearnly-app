# -*- coding: utf-8 -*-
"""POS 离线批量补传纯逻辑守门测试(POS 项目 · PO-B5)。

不连库:验 sync_sales 的 SAVEPOINT 隔离 + 部分失败不卡其余 + 结果形状(client_uuid/ok/
错误码)+ 幂等透传(deduped)。重流程(真扣库存/连号)由 _e2e_po_b5 真库覆盖。"""

import unittest
from unittest import mock

from core.pos_api import PosError
from services.pos import sale


class _Cur:
    def __init__(self):
        self.savepoints = []

    def execute(self, sql, params=None):
        self.savepoints.append(sql.strip())


class SyncTests(unittest.TestCase):
    def test_partial_failure_isolated_per_item(self):
        cur = _Cur()
        calls = {"n": 0}

        def fake_create_sale(c, *, tenant_id, workspace_client_id, payload, created_by=None):
            calls["n"] += 1
            cu = payload.get("client_uuid")
            if cu == "bad":
                raise PosError("pos.out_of_stock", 409, detail="p1")
            return {"sale": {"id": f"s-{cu}", "receipt_no": f"RCP-{cu}"}, "deduped": cu == "dup"}

        items = [
            {"client_uuid": "ok1", "lines": [1]},
            {"client_uuid": "bad", "lines": [1]},
            {"client_uuid": "dup", "lines": [1]},
        ]
        with mock.patch.object(sale, "create_sale", side_effect=fake_create_sale):
            out = sale.sync_sales(
                cur, tenant_id="t", workspace_client_id=9, items=items, cashier_id="c1"
            )

        res = out["results"]
        self.assertEqual(len(res), 3)
        self.assertEqual(
            res[0],
            {
                "client_uuid": "ok1",
                "ok": True,
                "sale_id": "s-ok1",
                "receipt_no": "RCP-ok1",
                "deduped": False,
            },
        )
        self.assertFalse(res[1]["ok"])
        self.assertEqual(res[1]["error"]["code"], "pos.out_of_stock")
        self.assertEqual(res[1]["error"]["detail"], "p1")
        self.assertTrue(res[2]["ok"])
        self.assertTrue(res[2]["deduped"])  # 幂等透传
        # 成功张 RELEASE、失败张 ROLLBACK TO —— 每张都有自己的 savepoint
        self.assertEqual(cur.savepoints.count("SAVEPOINT pos_sync_item"), 3)
        self.assertIn("ROLLBACK TO SAVEPOINT pos_sync_item", cur.savepoints)
        self.assertEqual(cur.savepoints.count("RELEASE SAVEPOINT pos_sync_item"), 2)

    def test_structurally_bad_item_does_not_poison_batch(self):
        cur = _Cur()

        def fake_create_sale(c, *, tenant_id, workspace_client_id, payload, created_by=None):
            if payload.get("client_uuid") == "boom":
                raise KeyError("lines")  # 非 PosError 的结构性错
            cu = payload["client_uuid"]
            return {"sale": {"id": f"s-{cu}", "receipt_no": f"RCP-{cu}"}, "deduped": False}

        items = [{"client_uuid": "boom"}, {"client_uuid": "ok2", "lines": [1]}]
        with mock.patch.object(sale, "create_sale", side_effect=fake_create_sale):
            out = sale.sync_sales(cur, tenant_id="t", workspace_client_id=9, items=items)

        self.assertFalse(out["results"][0]["ok"])
        self.assertEqual(out["results"][0]["error"]["code"], "pos.line_invalid")
        self.assertTrue(out["results"][1]["ok"])  # 坏张没拖垮好张

    def test_cashier_id_from_token_not_body(self):
        cur = _Cur()
        seen = {}

        def fake_create_sale(c, *, tenant_id, workspace_client_id, payload, created_by=None):
            seen["cashier_id"] = payload.get("cashier_id")
            return {"sale": {"id": "s", "receipt_no": "R"}, "deduped": False}

        # body 里塞了伪造 cashier_id,必须被 token 的覆盖
        items = [{"client_uuid": "x", "cashier_id": "forged", "lines": [1]}]
        with mock.patch.object(sale, "create_sale", side_effect=fake_create_sale):
            sale.sync_sales(
                cur, tenant_id="t", workspace_client_id=9, items=items, cashier_id="real-cashier"
            )
        self.assertEqual(seen["cashier_id"], "real-cashier")


if __name__ == "__main__":
    unittest.main()
