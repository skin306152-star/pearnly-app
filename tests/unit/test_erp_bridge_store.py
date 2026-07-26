# -*- coding: utf-8 -*-
"""ERP 桥 DAL + 门面单测(fake cursor · 无真实 DB)。

钉死:密钥 sha256 校验 · 账套镜像净化 · 写桥唯一闸(同账套已有在线写桥 → 后来者降 read)·
lease 只领本桥且只领上报过的账套 · ack 越权/迟到 · 结果 2MB 截断 · 协议参数白名单 ·
门面等超时把 job 落 expired。
"""

from __future__ import annotations

import contextlib
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.bridge import (  # noqa: E402
    BridgeRejected,
    BridgeTimeout,
    BridgeUnavailable,
    bridge_enabled,
    poll_hold_seconds,
)
from services.erp.bridge import client, schema, store  # noqa: E402

TENANT = "11111111-1111-1111-1111-111111111111"
BRIDGE_A = "aaaaaaaa-1111-1111-1111-111111111111"
BRIDGE_B = "bbbbbbbb-2222-2222-2222-222222222222"
JOB_ID = "cccccccc-3333-3333-3333-333333333333"


class FakeCursor:
    """按 SQL 片段路由返回值的假游标(仓内 FakeCursor 范式的多语句版)。

    script = [(SQL 片段, 行列表 | rowcount 整数)] · 第一个命中的片段决定本次 execute 的结果。
    """

    def __init__(self, script=None, rowcount=1):
        self.script = list(script or [])
        self.executed = []
        self._default_rowcount = rowcount
        self.rowcount = rowcount
        self._rows = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self._rows = []
        self.rowcount = self._default_rowcount
        for needle, value in self.script:
            if needle in sql:
                if isinstance(value, int):
                    self.rowcount = value
                else:
                    self._rows = [dict(r) for r in value]
                    self.rowcount = len(self._rows)
                break

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def all_sql(self):
        return " ".join(s for s, _ in self.executed)


def patch_db(cur):
    @contextlib.contextmanager
    def _gc(*_a, **_k):
        yield cur

    return mock.patch.multiple("core.db", get_cursor=_gc, get_cursor_rls=_gc)


def bridge_row(bridge_id=BRIDGE_A, books=("DATAT",), role="read", effective="read"):
    return {
        "id": bridge_id,
        "tenant_id": TENANT,
        "name": "office-nas",
        "secret_hash": "",
        "role": role,
        "effective_role": effective,
        "books": [{"book_id": b} for b in books],
    }


class SchemaTests(unittest.TestCase):
    """prod 不跑 alembic —— 建表全靠首用自愈,这条断了整座桥连不上。"""

    def test_ensure_creates_both_tables_with_index_and_rls(self):
        cur = FakeCursor()
        with patch_db(cur), mock.patch("core.rls.apply_tenant_rls") as rls:
            schema.ensure_tables()
        blob = cur.all_sql()
        self.assertIn("CREATE TABLE IF NOT EXISTS erp_bridges", blob)
        self.assertIn("CREATE TABLE IF NOT EXISTS bridge_jobs", blob)
        self.assertIn("ix_bridge_jobs_bridge_status", blob)
        rls.assert_called_once_with(cur, schema.BRIDGES, schema.JOBS)

    def test_heal_builds_tables_once_then_retries(self):
        calls = {"n": 0}

        def _flaky():
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError('relation "bridge_jobs" does not exist')
            return "ok"

        with mock.patch.object(schema, "ensure_tables") as ensure:
            self.assertEqual(schema.heal(_flaky), "ok")
        ensure.assert_called_once()

    def test_heal_does_not_swallow_unrelated_errors(self):
        with mock.patch.object(schema, "ensure_tables") as ensure:
            with self.assertRaises(ValueError):
                schema.heal(lambda: (_ for _ in ()).throw(ValueError("connection refused")))
        ensure.assert_not_called()

    def test_poll_window_is_clamped_under_nginx_read_timeout(self):
        for raw, want in (("", 20), ("8", 8), ("0", 1), ("600", 45), ("abc", 20)):
            with (
                self.subTest(raw=raw),
                mock.patch.dict("os.environ", {"ERP_BRIDGE_POLL_HOLD_SECONDS": raw}),
            ):
                self.assertEqual(poll_hold_seconds(), want)

    def test_kill_switch_defaults_open(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            self.assertTrue(bridge_enabled())
        with mock.patch.dict("os.environ", {"ERP_BRIDGE_ENABLED": "0"}):
            self.assertFalse(bridge_enabled())


class SecretTests(unittest.TestCase):
    def test_hash_is_deterministic(self):
        self.assertEqual(store.hash_secret("abc"), store.hash_secret("abc"))
        self.assertNotEqual(store.hash_secret("abc"), store.hash_secret("abd"))

    def test_authenticate_rejects_malformed(self):
        for bad in ("", "exp_x_y", "brg_only", "brg_not-a-uuid_secret"):
            with self.subTest(bad=bad):
                self.assertIsNone(store.authenticate(bad))

    def test_authenticate_matches_hash_and_rejects_tamper(self):
        token = f"brg_{BRIDGE_A}_s3cret"
        row = {**bridge_row(), "secret_hash": store.hash_secret(token)}
        with mock.patch.object(store, "_get_bridge_by_id", return_value=row):
            self.assertEqual(store.authenticate(token)["id"], BRIDGE_A)
            self.assertIsNone(store.authenticate(f"brg_{BRIDGE_A}_tampered"))

    def test_mint_returns_plaintext_once_and_stores_hash(self):
        cur = FakeCursor(script=[("INSERT INTO erp_bridges", [{"id": BRIDGE_A}])])
        with patch_db(cur):
            res = store.mint_bridge(TENANT, "office-nas", "write")
        self.assertTrue(res["token"].startswith(f"brg_{BRIDGE_A}_"))
        self.assertEqual(res["tail"], res["token"][-4:])
        update = next(p for s, p in cur.executed if "SET secret_hash" in s)
        self.assertEqual(update[0], store.hash_secret(res["token"]))
        # 铸出来先是 read:要不要给写权,等 hello 过唯一闸才算数。
        insert = next(p for s, p in cur.executed if "INSERT INTO erp_bridges" in s)
        self.assertIn("write", insert)
        self.assertIn("'read'", next(s for s, _ in cur.executed if "INSERT INTO erp_bridges" in s))


class BooksTests(unittest.TestCase):
    def test_sanitize_keeps_protocol_keys_only(self):
        raw = [{"book_id": "DATAT", "dir": r"\\acc\X", "company": "A", "taxid": "1", "evil": "x"}]
        self.assertEqual(
            store.sanitize_books(raw),
            [{"book_id": "DATAT", "dir": r"\\acc\X", "company": "A", "taxid": "1"}],
        )

    def test_sanitize_drops_bookless_and_caps(self):
        self.assertEqual(store.sanitize_books("nope"), [])
        self.assertEqual(store.sanitize_books([{"company": "A"}]), [])
        self.assertEqual(len(store.sanitize_books([{"book_id": f"b{i}"} for i in range(400)])), 200)

    def test_assert_book_allowed(self):
        bridge = bridge_row(books=("DATAT", "DATA2"))
        store.assert_book_allowed(bridge, "DATAT")
        store.assert_book_allowed(bridge, None)  # 无账套维度的任务(op=books)放行
        with self.assertRaises(BridgeRejected) as ctx:
            store.assert_book_allowed(bridge, "SOMEONE_ELSE")
        self.assertEqual(ctx.exception.code, "bridge.book_not_reported")


class WriteBridgeGateTests(unittest.TestCase):
    """同一账套同一时刻只许一个写桥在线 —— 后来者必须被降为 read。"""

    def _hello(self, role, incumbent_books=None):
        script = [("SELECT id FROM erp_bridges", [{"id": BRIDGE_A}])]
        if incumbent_books is not None:
            script.append(
                (
                    "SELECT id, name, books FROM erp_bridges",
                    [
                        {
                            "id": BRIDGE_A,
                            "name": "first",
                            "books": [{"book_id": b} for b in incumbent_books],
                        }
                    ],
                )
            )
        cur = FakeCursor(script=script)
        with patch_db(cur):
            res = store.register_hello(
                bridge_row(BRIDGE_B),
                role=role,
                books=[{"book_id": "DATAT", "dir": r"\\acc\DATAT"}],
                bridge_version="1.0.0",
                host="nas01",
            )
        return res, cur

    def test_second_write_bridge_on_same_book_is_downgraded(self):
        res, cur = self._hello("write", incumbent_books=["DATAT"])
        self.assertEqual(res["effective_role"], "read")
        self.assertEqual(res["held_by"]["name"], "first")
        update = next(p for s, p in cur.executed if "SET role" in s)
        self.assertEqual(update[0], "write")  # 自述角色照实记
        self.assertEqual(update[1], "read")  # 生效角色被闸压回只读

    def test_write_bridge_alone_keeps_write(self):
        res, _ = self._hello("write", incumbent_books=None)
        self.assertEqual(res["effective_role"], "write")

    def test_incumbent_on_other_book_does_not_block(self):
        res, _ = self._hello("write", incumbent_books=["OTHERBOOK"])
        self.assertEqual(res["effective_role"], "write")

    def test_read_role_never_probes_write_holder(self):
        res, cur = self._hello("read", incumbent_books=["DATAT"])
        self.assertEqual(res["effective_role"], "read")
        self.assertNotIn("SELECT id, name, books", cur.all_sql())

    def test_hello_locks_tenant_rows_before_deciding(self):
        # 不上锁的话两个写桥同时问「有人占了吗」会都答没有,双写就漏进来了。
        _, cur = self._hello("write", incumbent_books=None)
        self.assertIn("FOR UPDATE", cur.executed[0][0])

    def test_unknown_role_falls_back_to_read(self):
        self.assertEqual(store.normalize_role("admin"), "read")
        self.assertEqual(store.normalize_role(None), "read")
        self.assertEqual(store.normalize_role("WRITE"), "write")


class LeaseTests(unittest.TestCase):
    def _lease(self, rows):
        cur = FakeCursor(script=[("WITH due AS", rows)])
        with patch_db(cur):
            out = store.lease_jobs(bridge_row(books=("DATAT",)), 3)
        return out, cur

    def test_lease_returns_jobs_and_scopes_to_this_bridge(self):
        rows = [{"id": JOB_ID, "kind": "query", "book_id": "DATAT", "payload": {"op": "tables"}}]
        out, cur = self._lease(rows)
        self.assertEqual(out[0]["id"], JOB_ID)
        sql, params = next((s, p) for s, p in cur.executed if "WITH due AS" in s)
        self.assertIn("bridge_id = %s", sql)
        self.assertEqual(params[0], BRIDGE_A)
        self.assertEqual(params[3], BRIDGE_A)  # lease_owner = 本桥
        self.assertEqual(params[4], store.LEASE_SECONDS)

    def test_lease_only_offers_books_the_bridge_reported(self):
        _, cur = self._lease([])
        sql, params = next((s, p) for s, p in cur.executed if "WITH due AS" in s)
        self.assertIn("book_id = ANY(%s::text[])", sql)
        self.assertEqual(params[1], ["DATAT"])

    def test_lease_reclaims_dead_leases_and_expires_stale(self):
        _, cur = self._lease([])
        blob = cur.all_sql()
        self.assertIn("SET status = 'queued'", blob)  # 租约到期退回队列
        self.assertIn("SET status = 'expired'", blob)  # 超龄任务不再派出去
        self.assertIn("SKIP LOCKED", blob)


class AckTests(unittest.TestCase):
    def test_ack_fills_result_and_clears_lease(self):
        cur = FakeCursor(rowcount=1)
        with patch_db(cur):
            res = store.finish_job(bridge_row(), JOB_ID, True, {"rows": [{"a": 1}]})
        self.assertEqual(res, {"ok": True, "status": "done", "truncated": False})
        sql, params = cur.executed[0]
        self.assertIn("lease_owner = NULL", sql)
        self.assertIn("status = 'leased'", sql)  # 只有持租约的才回得进来
        self.assertIn('"rows"', params[1])

    def test_ack_from_another_bridge_is_not_found(self):
        cur = FakeCursor(rowcount=0)
        with patch_db(cur):
            res = store.finish_job(bridge_row(BRIDGE_B), JOB_ID, True, {})
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "job_not_found")

    def test_late_ack_on_expired_job_is_honest(self):
        cur = FakeCursor(script=[("SELECT status FROM bridge_jobs", [{"status": "expired"}])])
        cur._default_rowcount = 0
        with patch_db(cur):
            res = store.finish_job(bridge_row(), JOB_ID, True, {})
        self.assertTrue(res["ok"])
        self.assertTrue(res["stale"])
        self.assertEqual(res["status"], "expired")

    def test_ack_failure_records_error_code(self):
        cur = FakeCursor(rowcount=1)
        with patch_db(cur):
            store.finish_job(
                bridge_row(), JOB_ID, False, None, {"code": "dbf.locked", "message": "x"}
            )
        params = cur.executed[0][1]
        self.assertEqual(params[0], "failed")
        self.assertIn("dbf.locked", params[2])

    def test_bad_job_id_never_reaches_sql(self):
        cur = FakeCursor()
        with patch_db(cur):
            res = store.finish_job(bridge_row(), "'; DROP TABLE bridge_jobs; --", True, {})
        self.assertEqual(res["reason"], "job_not_found")
        self.assertEqual(cur.executed, [])


class ResultCapTests(unittest.TestCase):
    def test_small_result_passes_through(self):
        blob, truncated = store.clamp_result({"rows": [{"a": 1}]})
        self.assertFalse(truncated)
        self.assertIn('"a": 1', blob)

    def test_oversized_rows_are_trimmed_and_marked(self):
        rows = [{"v": "x" * 512} for _ in range(6000)]
        blob, truncated = store.clamp_result({"rows": rows})
        self.assertTrue(truncated)
        self.assertLessEqual(len(blob.encode("utf-8")), store.RESULT_MAX_BYTES)
        self.assertIn('"rows_total": 6000', blob)

    def test_oversized_without_rows_falls_back_to_metadata(self):
        blob, truncated = store.clamp_result({"blob": "x" * (store.RESULT_MAX_BYTES + 10)})
        self.assertTrue(truncated)
        self.assertIn("original_bytes", blob)
        self.assertNotIn("xxxx", blob)


class PayloadWhitelistTests(unittest.TestCase):
    def test_accepts_protocol_fields(self):
        payload = client.build_query_payload(
            "rows",
            {"table": "ARTRAN", "filters": {"BOOK": "DATAT"}, "from": "2026-01-01", "limit": 10},
        )
        self.assertEqual(payload["op"], "rows")
        self.assertEqual(payload["table"], "ARTRAN")
        self.assertEqual(payload["limit"], 10)

    def test_rejects_unknown_op_and_stray_fields(self):
        with self.assertRaises(BridgeRejected):
            client.build_query_payload("delete", {})
        with self.assertRaises(BridgeRejected):
            client.build_query_payload("tables", {"table": "ARTRAN"})

    def test_rejects_bad_shapes(self):
        bad = [
            ("rows", {"table": "AR TRAN"}),
            ("rows", {"table": "AR;DROP"}),
            ("rows", {"table": "AR", "from": "2026/01/01"}),
            ("rows", {"table": "AR", "filters": ["nope"]}),
            ("rows", {"table": "AR", "filters": {"a b": 1}}),
            ("rows", {"table": "AR", "filters": {"a": {"nested": 1}}}),
            ("rows", {"table": "AR", "limit": "many"}),
            ("rows", {}),
        ]
        for op, params in bad:
            with self.subTest(params=params), self.assertRaises(BridgeRejected):
                client.build_query_payload(op, params)

    def test_limits_are_clamped(self):
        self.assertEqual(client.build_query_payload("tables", {"limit": 10**9})["limit"], 5000)
        self.assertEqual(client.build_query_payload("tables", {"offset": -5})["offset"], 0)


class FacadeTests(unittest.TestCase):
    def test_query_without_online_bridge_is_unavailable(self):
        with mock.patch.object(store, "pick_bridge", return_value=None):
            with self.assertRaises(BridgeUnavailable):
                client.query(TENANT, "DATAT", "tables")

    def test_query_rejects_book_outside_reported_list(self):
        with mock.patch.object(store, "pick_bridge", return_value=bridge_row(books=("DATAT",))):
            with self.assertRaises(BridgeRejected):
                client.query(TENANT, "GHOSTBOOK", "tables")

    def test_query_returns_result_when_bridge_acks(self):
        job = {"id": JOB_ID, "status": "done", "result": {"rows": [{"a": 1}]}}
        with (
            mock.patch.object(store, "pick_bridge", return_value=bridge_row()),
            mock.patch.object(store, "enqueue_job", return_value=JOB_ID),
            mock.patch.object(store, "get_job", return_value=job),
        ):
            out = client.query(TENANT, "DATAT", "tables")
        self.assertEqual(out["rows"], [{"a": 1}])

    def test_timeout_marks_job_expired(self):
        pending = {"id": JOB_ID, "status": "queued"}
        with (
            mock.patch.object(store, "pick_bridge", return_value=bridge_row()),
            mock.patch.object(store, "enqueue_job", return_value=JOB_ID),
            mock.patch.object(store, "get_job", return_value=pending),
            mock.patch.object(store, "expire_job", return_value=True) as expired,
            mock.patch.object(client, "POLL_INTERVAL", 0.001),
        ):
            with self.assertRaises(BridgeTimeout):
                client.query(TENANT, "DATAT", "tables", timeout=0.05)
        expired.assert_called_once_with(TENANT, JOB_ID)

    def test_expire_job_only_touches_unfinished(self):
        cur = FakeCursor(rowcount=1)
        with patch_db(cur):
            self.assertTrue(store.expire_job(TENANT, JOB_ID))
        self.assertIn("status IN ('queued', 'leased')", cur.executed[0][0])

    def test_list_books_dedupes_and_skips_offline(self):
        bridges = [
            {"id": BRIDGE_A, "online": True, "books": [{"book_id": "DATAT"}, {"book_id": "D2"}]},
            {"id": BRIDGE_B, "online": True, "books": [{"book_id": "DATAT"}]},
            {"id": BRIDGE_B, "online": False, "books": [{"book_id": "OFFLINE"}]},
        ]
        with mock.patch.object(store, "list_bridges", return_value=bridges):
            books = client.list_books(TENANT)
        self.assertEqual([b["book_id"] for b in books], ["D2", "DATAT"])

    def test_bridge_status_reports_writer(self):
        bridges = [
            {"id": BRIDGE_A, "name": "a", "online": False, "effective_role": "write", "books": []},
            {"id": BRIDGE_B, "name": "b", "online": True, "effective_role": "write", "books": []},
        ]
        with mock.patch.object(store, "list_bridges", return_value=bridges):
            status = client.bridge_status(TENANT)
        self.assertTrue(status["configured"])
        self.assertTrue(status["online"])
        self.assertEqual(status["writer"], BRIDGE_B)


if __name__ == "__main__":
    unittest.main(verbosity=2)
