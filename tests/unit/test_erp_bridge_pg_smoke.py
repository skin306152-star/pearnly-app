# -*- coding: utf-8 -*-
"""桥任务信箱 SQL 真 Postgres 冒烟(补「按 kind 分租约/超龄的 CASE WHEN 零执行覆盖」)。

FakeCursor 单测只能钉「SQL 字符串长这样、参数接在这个位」;`make_interval(secs => CASE
WHEN ...)`、`kind = ANY(%s::text[])` 这些方言若有细微类型/语法错,要等 prod 首个真实写活
lease 才炸。本文件对本地 docker pearnly-db(docker-compose.yml 那套)执行真 SQL:
入队 write+query 各一条 → 验证各自租约秒数真落进 lease_expires_at,再把超龄扫尾、
租约回收、expire 语义(在途写活不 expire)、迟到 ack 落结果四条路各真跑一遍。

连哪个库、连不上怎么办,全在 tests/unit/_pg_smoke.py(两份 smoke 共用,理由写在那)。
"""

from __future__ import annotations

import contextlib
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.bridge import schema, store, write_gate  # noqa: E402
from tests.unit._pg_smoke import connect_or_skip  # noqa: E402

TENANT = str(uuid.uuid4())
BRIDGE_ID = str(uuid.uuid4())


def _bridge(effective="write"):
    return {
        "id": BRIDGE_ID,
        "tenant_id": TENANT,
        "effective_role": effective,
        "books": [{"book_id": "DATAT"}],
    }


class BridgeStorePgSmokeTests(unittest.TestCase):
    conn = None

    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        from psycopg2.extras import RealDictCursor

        @contextlib.contextmanager
        def _cursor(*_a, **_k):
            cur = cls.conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cur
                cls.conn.commit()
            except Exception:
                cls.conn.rollback()
                raise
            finally:
                cur.close()

        cls._patch = mock.patch.multiple("core.db", get_cursor=_cursor, get_cursor_rls=_cursor)
        cls._patch.start()
        cls._cursor = _cursor
        schema.ensure_tables()

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        try:
            with cls._cursor() as cur:
                cur.execute(f"DELETE FROM {schema.JOBS} WHERE tenant_id = %s", (TENANT,))
        finally:
            cls._patch.stop()
            cls.conn.close()

    # ── 工具 ──────────────────────────────────────────────────────────────

    def _job(self, job_id):
        with self._cursor() as cur:
            cur.execute(
                f"SELECT status, kind, result, "
                f"extract(epoch FROM (lease_expires_at - now())) AS lease_secs "
                f"FROM {schema.JOBS} WHERE id = %s",
                (job_id,),
            )
            return dict(cur.fetchone())

    def _enqueue(self, kind):
        payload = {"op": "tables"} if kind == "query" else {"ref_no": "INV-PGSMOKE"}
        return store.enqueue_job(_bridge(), kind, payload, book_id="DATAT")

    def _backdate(self, job_id, column, seconds):
        with self._cursor() as cur:
            cur.execute(
                f"UPDATE {schema.JOBS} SET {column} = now() - make_interval(secs => %s) "
                "WHERE id = %s",
                (seconds, job_id),
            )

    # ── 真 SQL 冒烟 ───────────────────────────────────────────────────────

    def test_lease_seconds_land_per_kind(self):
        """写活租约 300s / 查询 60s 真落进 lease_expires_at(CASE WHEN 真执行)。"""
        wid, qid = self._enqueue("write"), self._enqueue("query")
        leased = store.lease_jobs(_bridge(), 10)
        self.assertEqual({str(j["id"]) for j in leased} & {wid, qid}, {wid, qid})
        w, q = self._job(wid), self._job(qid)
        self.assertEqual((w["status"], q["status"]), ("leased", "leased"))
        self.assertAlmostEqual(float(w["lease_secs"]), write_gate.WRITE_LEASE_SECONDS, delta=10)
        self.assertAlmostEqual(float(q["lease_secs"]), store.LEASE_SECONDS, delta=10)

    def test_stale_sweep_ttl_is_per_kind(self):
        """排队 400s:查询(TTL 120)落 expired,写活(TTL 600)还活着且能被领走。"""
        wid, qid = self._enqueue("write"), self._enqueue("query")
        for jid in (wid, qid):
            self._backdate(jid, "created_at", 400)
        store.lease_jobs(_bridge(), 10)
        self.assertEqual(self._job(qid)["status"], "expired")
        self.assertEqual(self._job(wid)["status"], "leased")

    def test_reclaim_returns_dead_lease_to_queue(self):
        """租约到点的写活退回队列并在同一拍被重新领走(回收 UPDATE 真执行)。"""
        wid = self._enqueue("write")
        store.lease_jobs(_bridge(), 10)
        self._backdate(wid, "lease_expires_at", 5)
        store.lease_jobs(_bridge(), 10)
        job = self._job(wid)
        self.assertEqual(job["status"], "leased")
        self.assertGreater(float(job["lease_secs"]), 0)

    def test_expire_spares_leased_write_but_not_query(self):
        """expire 语义:在途写活不动(桥可能正写账套);在途查询/排队写活照落 expired。"""
        wid, qid = self._enqueue("write"), self._enqueue("query")
        store.lease_jobs(_bridge(), 10)
        self.assertFalse(store.expire_job(TENANT, wid))
        self.assertEqual(self._job(wid)["status"], "leased")
        self.assertTrue(store.expire_job(TENANT, qid))
        self.assertEqual(self._job(qid)["status"], "expired")

        queued_wid = self._enqueue("write")
        self.assertTrue(store.expire_job(TENANT, queued_wid))
        self.assertEqual(self._job(queued_wid)["status"], "expired")

    def test_late_write_ack_lands_result_on_expired_row(self):
        """回收+超龄后桥才写完:结果(docnum)仍落库,状态如实留 expired。"""
        wid = self._enqueue("write")
        store.lease_jobs(_bridge(), 10)
        with self._cursor() as cur:
            cur.execute(
                f"UPDATE {schema.JOBS} SET status = 'expired', lease_owner = NULL, "
                "lease_expires_at = NULL WHERE id = %s",
                (wid,),
            )
        res = store.finish_job(_bridge(), wid, True, {"docnum": "RR2601001"})
        self.assertEqual(
            res, {"ok": True, "status": "expired", "stale": True, "result_saved": True}
        )
        job = self._job(wid)
        self.assertEqual(job["status"], "expired")
        self.assertEqual((job["result"] or {}).get("docnum"), "RR2601001")


if __name__ == "__main__":
    unittest.main(verbosity=2)
