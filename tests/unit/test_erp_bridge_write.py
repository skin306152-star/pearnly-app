# -*- coding: utf-8 -*-
"""桥写路云端侧单测(fake cursor · 无真实 DB)。

钉死:job kind 白名单(未知拒)· 写活只投/只派 effective_role=write 的桥(入队闸 +
lease 兜底,唯一闸降级后两口都拒)· 写租约 300s / 写超龄 600s 与查询 60/120 分道 ·
写桥挑选只认在线写桥且账套在其清单内 · 写载荷轻校验逐条拒收 · submit/status/blocking
全路径 · query 老行为不破。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.bridge import BridgeRejected, BridgeTimeout, BridgeUnavailable  # noqa: E402
from services.erp.bridge import client, store, write_gate  # noqa: E402
from tests.unit.test_erp_bridge_store import (  # noqa: E402
    BRIDGE_A,
    JOB_ID,
    TENANT,
    FakeCursor,
    bridge_row,
    patch_db,
)


def write_payload(**over):
    """契约样单(express_push mapper 产物形状 · 借 100+7 = 贷 107 必平)。"""
    payload = {
        "payload_version": 1,
        "direction": "purchase",
        "doctype": "RR",
        "account_set": "DATAT",
        "docdate_be": "690115",
        "vat_period_be": "690101",
        "ref_no": "INV-001",
        "base_amount": "100.00",
        "vat_amount": "7.00",
        "total_amount": "107.00",
        "lines": [
            {"acc": "116200", "side": "D", "amount": "100.00", "desc": "สินค้า"},
            {"acc": "115510", "side": "D", "amount": "7.00", "desc": "ภาษีซื้อ"},
            {"acc": "211100", "side": "C", "amount": "107.00", "desc": "เจ้าหนี้"},
        ],
    }
    payload.update(over)
    return payload


class KindWhitelistTests(unittest.TestCase):
    def test_job_kinds_is_the_whitelist(self):
        self.assertEqual(write_gate.JOB_KINDS, ("query", "write"))

    def test_unknown_kind_is_rejected_before_sql(self):
        cur = FakeCursor()
        with patch_db(cur):
            with self.assertRaises(BridgeRejected) as ctx:
                store.enqueue_job(bridge_row(), "delete", {})
        self.assertEqual(ctx.exception.code, "bridge.bad_kind")
        self.assertEqual(cur.executed, [])

    def test_query_kind_still_enqueues_on_read_bridge(self):
        # 老行为回归:读桥照常收 query,白名单不误伤既有链路。
        cur = FakeCursor(script=[("INSERT INTO bridge_jobs", [{"id": JOB_ID}])])
        with patch_db(cur):
            job_id = store.enqueue_job(bridge_row(), "query", {"op": "tables"}, book_id="DATAT")
        self.assertEqual(job_id, JOB_ID)
        self.assertIn("query", cur.executed[0][1])


class WriteRoleGateTests(unittest.TestCase):
    """写活只许投生效写桥 —— 入队口就拒,不等桥端才发现。"""

    def test_write_to_read_bridge_is_rejected(self):
        cur = FakeCursor()
        with patch_db(cur):
            with self.assertRaises(BridgeRejected) as ctx:
                store.enqueue_job(bridge_row(effective="read"), "write", write_payload())
        self.assertEqual(ctx.exception.code, "bridge.write_role_required")
        self.assertEqual(cur.executed, [])

    def test_downgraded_write_bridge_is_rejected(self):
        # 唯一闸把自述 write 的桥降成了 read → 入队闸只认 effective_role,照拒。
        with patch_db(FakeCursor()):
            with self.assertRaises(BridgeRejected) as ctx:
                store.enqueue_job(bridge_row(role="write", effective="read"), "write", {})
        self.assertEqual(ctx.exception.code, "bridge.write_role_required")

    def test_write_to_effective_write_bridge_enqueues(self):
        cur = FakeCursor(script=[("INSERT INTO bridge_jobs", [{"id": JOB_ID}])])
        with patch_db(cur):
            job_id = store.enqueue_job(
                bridge_row(role="write", effective="write"),
                "write",
                write_payload(),
                book_id="DATAT",
            )
        self.assertEqual(job_id, JOB_ID)
        self.assertIn("write", cur.executed[0][1])


class LeasePerKindTests(unittest.TestCase):
    """租约/超龄按 kind 分道:写活跨 SMB 备份+写+CDX 重建,比查询慢一个量级。"""

    def _lease(self, effective):
        cur = FakeCursor(script=[("WITH due AS", [])])
        with patch_db(cur):
            store.lease_jobs(bridge_row(role="write", effective=effective), 3)
        return cur

    def test_write_lease_is_300s_and_query_stays_60s(self):
        cur = self._lease("write")
        sql, params = next((s, p) for s, p in cur.executed if "WITH due AS" in s)
        self.assertIn("CASE WHEN j.kind = 'write'", sql)
        self.assertEqual(params[5], write_gate.WRITE_LEASE_SECONDS)
        self.assertEqual(params[6], store.LEASE_SECONDS)
        self.assertEqual(write_gate.WRITE_LEASE_SECONDS, 300)
        self.assertEqual(store.LEASE_SECONDS, 60)

    def test_write_ttl_is_600s_and_query_stays_120s(self):
        cur = self._lease("write")
        sql, params = next((s, p) for s, p in cur.executed if "SET status = 'expired'" in s)
        self.assertIn("CASE WHEN kind = 'write'", sql)
        self.assertEqual(params, (BRIDGE_A, 600, 120))
        self.assertEqual(write_gate.WRITE_JOB_TTL_SECONDS, 600)
        self.assertEqual(store.JOB_TTL_SECONDS, 120)

    def test_read_bridge_is_never_offered_write_jobs(self):
        # lease 兜底:hello 后被降级的桥,队列里降级前的写活不再派给它。
        cur = self._lease("read")
        sql, params = next((s, p) for s, p in cur.executed if "WITH due AS" in s)
        self.assertIn("kind = ANY(%s::text[])", sql)
        self.assertEqual(params[2], ["query"])

    def test_write_bridge_leases_both_kinds(self):
        cur = self._lease("write")
        params = next(p for s, p in cur.executed if "WITH due AS" in s)
        self.assertEqual(sorted(params[2]), ["query", "write"])


class PickWriteBridgeTests(unittest.TestCase):
    def test_picks_online_write_bridge_reporting_the_book(self):
        row = bridge_row(role="write", effective="write", books=("DATAT",))
        cur = FakeCursor(script=[("FROM erp_bridges", [row])])
        with patch_db(cur):
            picked = write_gate.pick_write_bridge(TENANT, "DATAT")
        self.assertEqual(picked["id"], BRIDGE_A)
        sql = cur.executed[0][0]
        self.assertIn("effective_role = 'write'", sql)
        self.assertIn("last_seen_at >", sql)

    def test_no_online_write_bridge_is_unavailable(self):
        with patch_db(FakeCursor(script=[("FROM erp_bridges", [])])):
            with self.assertRaises(BridgeUnavailable):
                write_gate.pick_write_bridge(TENANT, "DATAT")

    def test_write_bridge_without_the_book_is_skipped(self):
        row = bridge_row(role="write", effective="write", books=("OTHERBOOK",))
        with patch_db(FakeCursor(script=[("FROM erp_bridges", [row])])):
            with self.assertRaises(BridgeUnavailable):
                write_gate.pick_write_bridge(TENANT, "DATAT")


class WritePayloadTests(unittest.TestCase):
    def test_valid_purchase_and_sales_pass(self):
        self.assertEqual(client.build_write_payload(write_payload(), "DATAT")["doctype"], "RR")
        sales = write_payload(direction="sales", doctype="IV")
        self.assertEqual(client.build_write_payload(sales, "DATAT")["direction"], "sales")

    def test_each_bad_shape_is_rejected(self):
        unbalanced = write_payload()
        unbalanced["lines"] = [dict(line) for line in unbalanced["lines"]]
        unbalanced["lines"][0]["amount"] = "99.00"
        bad = [
            ("非对象", "not-a-dict", "DATAT"),
            ("版本不符", write_payload(payload_version=2), "DATAT"),
            ("缺版本", write_payload(payload_version=None), "DATAT"),
            ("方向非法", write_payload(direction="expense"), "DATAT"),
            ("票种与方向不配", write_payload(doctype="IV"), "DATAT"),
            ("票种非法", write_payload(doctype="XX"), "DATAT"),
            ("缺账套", write_payload(account_set=""), "DATAT"),
            ("账套与book不一致", write_payload(), "DATA2"),
            ("book缺失", write_payload(), None),
            ("缺lines", write_payload(lines=None), "DATAT"),
            ("空lines", write_payload(lines=[]), "DATAT"),
            ("行缺acc", write_payload(lines=[{"side": "D", "amount": "1"}]), "DATAT"),
            ("side非法", write_payload(lines=[{"acc": "1", "side": "X", "amount": "1"}]), "DATAT"),
            (
                "金额解析不了",
                write_payload(lines=[{"acc": "1", "side": "D", "amount": "abc"}]),
                "DATAT",
            ),
            ("借贷不平", unbalanced, "DATAT"),
        ]
        for label, payload, book in bad:
            with self.subTest(label=label), self.assertRaises(BridgeRejected) as ctx:
                client.build_write_payload(payload, book)
            self.assertEqual(ctx.exception.code, "bridge.bad_payload")


class WriteFacadeTests(unittest.TestCase):
    def _write_bridge(self):
        return bridge_row(role="write", effective="write")

    def test_submit_returns_job_id_without_blocking(self):
        with (
            mock.patch.object(
                write_gate, "pick_write_bridge", return_value=self._write_bridge()
            ) as pick,
            mock.patch.object(store, "enqueue_job", return_value=JOB_ID) as enqueue,
        ):
            job_id = client.submit_write(TENANT, "DATAT", write_payload())
        self.assertEqual(job_id, JOB_ID)
        pick.assert_called_once_with(TENANT, "DATAT")
        args, kwargs = enqueue.call_args
        self.assertEqual(args[1], "write")
        self.assertEqual(kwargs["book_id"], "DATAT")

    def test_submit_validates_payload_before_picking_a_bridge(self):
        with mock.patch.object(write_gate, "pick_write_bridge") as pick:
            with self.assertRaises(BridgeRejected):
                client.submit_write(TENANT, "DATAT", write_payload(doctype="IV"))
        pick.assert_not_called()

    def test_submit_without_write_bridge_is_unavailable(self):
        with mock.patch.object(
            write_gate, "pick_write_bridge", side_effect=BridgeUnavailable("没写桥")
        ):
            with self.assertRaises(BridgeUnavailable):
                client.submit_write(TENANT, "DATAT", write_payload())

    def test_status_maps_job_row_and_none_for_unknown(self):
        job = {"id": JOB_ID, "status": "done", "result": {"docnum": "RR2601001"}, "error": None}
        with mock.patch.object(store, "get_job", return_value=job):
            status = client.write_status(TENANT, JOB_ID)
        self.assertEqual(
            status,
            {"job_id": JOB_ID, "status": "done", "result": {"docnum": "RR2601001"}, "error": None},
        )
        with mock.patch.object(store, "get_job", return_value=None):
            self.assertIsNone(client.write_status(TENANT, JOB_ID))

    def test_blocking_write_returns_result(self):
        job = {"id": JOB_ID, "status": "done", "result": {"docnum": "RR2601001"}}
        with (
            mock.patch.object(write_gate, "pick_write_bridge", return_value=self._write_bridge()),
            mock.patch.object(store, "enqueue_job", return_value=JOB_ID),
            mock.patch.object(store, "get_job", return_value=job),
        ):
            out = client.write(TENANT, "DATAT", write_payload())
        self.assertEqual(out["docnum"], "RR2601001")

    def test_blocking_write_timeout_expires_the_job(self):
        with (
            mock.patch.object(write_gate, "pick_write_bridge", return_value=self._write_bridge()),
            mock.patch.object(store, "enqueue_job", return_value=JOB_ID),
            mock.patch.object(store, "get_job", return_value={"id": JOB_ID, "status": "queued"}),
            mock.patch.object(store, "expire_job", return_value=True) as expired,
            mock.patch.object(client, "POLL_INTERVAL", 0.001),
        ):
            with self.assertRaises(BridgeTimeout):
                client.write(TENANT, "DATAT", write_payload(), timeout=0.05)
        expired.assert_called_once_with(TENANT, JOB_ID)

    def test_write_timeout_default_matches_write_lease(self):
        self.assertEqual(client.WRITE_TIMEOUT, 300.0)
        self.assertEqual(client.DEFAULT_TIMEOUT, 20.0)  # 查询默认不动


if __name__ == "__main__":
    unittest.main(verbosity=2)
