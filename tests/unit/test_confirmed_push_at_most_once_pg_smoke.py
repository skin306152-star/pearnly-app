# -*- coding: utf-8 -*-
"""带 duplicate_confirmed 的推送在两条队列上都必须「至多投一次」(真 Postgres 冒烟)。

会计按下「知道了,还是推」的那一次,写侧的幂等闸(find_existing:同 ref_no + 对手方码就当
重投)是**关着的** —— 那正是这个键的作用。而两条队列默认都是 at-least-once:租约到期就把活
退回去再派一次。两件事凑在一起,丢一次 ack 就是账上多一张,丢 N 次多 N 张。

于是这类行改成至多一次,并配一个诚实收尾:租约过期还没等到回执,就落人工/expired 并说清
「可能写了也可能没写,系统不会自动再推」,绝不悄悄躺回队列装作还在排队。

判据必须在真库上跑:`request_body->>'duplicate_confirmed'` 的真值判断、jsonb_build_object、
以及「先收尾再回收」的语句顺序,FakeCursor 只能证明 SQL 字符串长这样,证不了它选中了哪些行。
连库口见 tests/unit/_pg_smoke(连不上整类 skip);建表见下面 _LEGACY_TABLES_DDL。
"""

from __future__ import annotations

import contextlib
import json
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.bridge import schema as bridge_schema  # noqa: E402
from services.erp.bridge import store as bridge_store  # noqa: E402
from services.erp.bridge import write_gate  # noqa: E402
from services.erp.express_push import agent_store  # noqa: E402
from tests.unit._pg_smoke import connect_or_skip  # noqa: E402

TENANT = str(uuid.uuid4())
BRIDGE_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())
ENDPOINT_ID = str(uuid.uuid4())

CONFIRMED_PAYLOAD = {"ref_no": "IV69/09001", "duplicate_confirmed": True}
PLAIN_PAYLOAD = {"ref_no": "IV69/09002"}

# 桥那条队列的表由 bridge_schema.ensure_tables() 建;小助手这条队列踩的四张是 legacy 表 ——
# 建表 DDL 从来没进过版本控制(alembic 里一个 create_table 都没有,只有 ALTER;见
# scripts/check_destructive_db_tests.py 开头那段出身),而 CI 的 pg-smoke 起的是一次性空库,
# 于是这里必须自带建表,否则整类 setUpClass 直接 UndefinedTable。
#
# 列定义逐列抄自本机开发库的 information_schema/pg_constraint,只留本用例与 agent_store
# 真读写的那些;CREATE TABLE IF NOT EXISTS 让开发机上整段 no-op —— 那边跑的仍是生产同款
# 结构,真有列型漂移会在本机先红。status CHECK 一并带上:这条用例断的就是状态落点,
# 少了它 CI 上 'manual' 写得进去而 prod 写不进去(白名单正本在
# services/erp/push_schema.py::ensure_erp_push_logs_status_constraint)。
_LEGACY_TABLES_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      TEXT NOT NULL,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS erp_endpoints (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    adapter    TEXT NOT NULL,
    config     JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT erp_endpoints_adapter_chk CHECK (adapter IN (
        'webhook', 'xero', 'flowaccount', 'mrerp', 'mrerp_dms', 'express'))
);
CREATE TABLE IF NOT EXISTS ocr_history (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename         TEXT NOT NULL,
    pages            JSONB NOT NULL,
    last_pushed_at   TIMESTAMPTZ,
    last_push_status TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS last_pushed_at TIMESTAMPTZ;
ALTER TABLE ocr_history ADD COLUMN IF NOT EXISTS last_push_status TEXT;
CREATE TABLE IF NOT EXISTS erp_push_logs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint_id      UUID REFERENCES erp_endpoints(id) ON DELETE SET NULL,
    history_id       UUID,
    invoice_no       TEXT,
    status           TEXT NOT NULL,
    http_status      INTEGER,
    request_body     JSONB,
    response_body    TEXT,
    error_msg        TEXT,
    attempt          INTEGER NOT NULL DEFAULT 1,
    elapsed_ms       INTEGER,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    trigger          TEXT NOT NULL DEFAULT 'manual',
    lease_owner      TEXT,
    lease_expires_at TIMESTAMPTZ,
    CONSTRAINT erp_push_logs_status_chk CHECK (status IN (
        'success', 'failed', 'skipped_dup', 'pending', 'retrying', 'manual'))
);
"""


def _bridge():
    return {
        "id": BRIDGE_ID,
        "tenant_id": TENANT,
        "effective_role": "write",
        "books": [{"book_id": "DATAT"}],
    }


class _PgFixture(unittest.TestCase):
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
        bridge_schema.ensure_tables()
        # erp_push_logs / ocr_history 都有外键指回 users 与 erp_endpoints,拿造好的 uuid 直插
        # 会被外键挡下 —— 种一个本用例专属的用户 + Express 连接,tearDown 原路删掉。
        with _cursor() as cur:
            cur.execute(_LEGACY_TABLES_DDL)
            cur.execute(
                "INSERT INTO users (id, username, password_hash) VALUES (%s, %s, 'x') "
                "ON CONFLICT DO NOTHING",
                (USER_ID, f"pgsmoke-{USER_ID[:8]}"),
            )
            cur.execute(
                "INSERT INTO erp_endpoints (id, user_id, name, adapter) "
                "VALUES (%s, %s, 'pg-smoke', 'express') ON CONFLICT DO NOTHING",
                (ENDPOINT_ID, USER_ID),
            )

    @classmethod
    def tearDownClass(cls):
        if cls.conn is None:
            return
        try:
            with cls._cursor() as cur:
                cur.execute(f"DELETE FROM {bridge_schema.JOBS} WHERE tenant_id = %s", (TENANT,))
                cur.execute("DELETE FROM erp_push_logs WHERE user_id = %s", (USER_ID,))
                cur.execute("DELETE FROM ocr_history WHERE user_id = %s", (USER_ID,))
                cur.execute("DELETE FROM erp_endpoints WHERE user_id = %s", (USER_ID,))
                cur.execute("DELETE FROM users WHERE id = %s", (USER_ID,))
        finally:
            cls._patch.stop()
            cls.conn.close()


class ExpressQueueAtMostOnceTests(_PgFixture):
    """小助手那条队列(erp_push_logs · status='pending')。"""

    def _history(self) -> str:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO ocr_history (user_id, filename, pages, last_push_status) "
                "VALUES (%s, %s, %s::jsonb, 'pending') RETURNING id",
                (USER_ID, "smoke.pdf", "[]"),
            )
            return str(cur.fetchone()["id"])

    def _log(self, payload: dict, *, history_id=None, owner=None, lease_secs=None) -> str:
        """直接插一行队列行。lease_secs 为负 = 租约已过期。"""
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO erp_push_logs (
                    user_id, endpoint_id, history_id, invoice_no, status,
                    request_body, error_msg, attempt, elapsed_ms, trigger,
                    lease_owner, lease_expires_at
                ) VALUES (%s, %s, %s, %s, 'pending', %s::jsonb, 'EXPRESS_QUEUED', 1, 0,
                          'manual', %s,
                          CASE WHEN %s IS NULL THEN NULL
                               ELSE now() + make_interval(secs => %s) END)
                RETURNING id
                """,
                (
                    USER_ID,
                    ENDPOINT_ID,
                    history_id,
                    payload.get("ref_no"),
                    json.dumps(payload),
                    owner,
                    lease_secs,
                    lease_secs,
                ),
            )
            return str(cur.fetchone()["id"])

    def _row(self, log_id: str) -> dict:
        with self._cursor() as cur:
            cur.execute(
                "SELECT status, error_msg, response_body, lease_owner FROM erp_push_logs "
                "WHERE id = %s",
                (log_id,),
            )
            return dict(cur.fetchone())

    def test_plain_row_with_a_dead_lease_is_still_re_leased(self):
        """不带确认位的行照旧 at-least-once —— 这条改动不该动到普通重投。"""
        log_id = self._log(PLAIN_PAYLOAD, owner="agentA", lease_secs=-30)
        leased = agent_store.lease_pending(ENDPOINT_ID, "agentB", 10)
        self.assertIn(log_id, {str(r["id"]) for r in leased})
        self.assertEqual(self._row(log_id)["lease_owner"], "agentB")

    def test_confirmed_row_is_leased_exactly_once(self):
        """确认过的行只在 lease_owner IS NULL 时可领:第二拍(租约已死)绝不再派。"""
        log_id = self._log(CONFIRMED_PAYLOAD)
        first = agent_store.lease_pending(ENDPOINT_ID, "agentA", 10)
        self.assertIn(log_id, {str(r["id"]) for r in first})

        self._expire(log_id)
        second = agent_store.lease_pending(ENDPOINT_ID, "agentB", 10)
        self.assertNotIn(log_id, {str(r["id"]) for r in second})

    def test_confirmed_row_whose_lease_died_is_closed_honestly(self):
        """不重投之外还得说话:落 manual + 可翻译的原因码,单据记录同步落人工。"""
        history_id = self._history()
        log_id = self._log(CONFIRMED_PAYLOAD, history_id=history_id, owner="agentA", lease_secs=-1)

        agent_store.lease_pending(ENDPOINT_ID, "agentB", 10)

        row = self._row(log_id)
        self.assertEqual(row["status"], "manual")
        self.assertEqual(
            row["error_msg"], f"EXPRESS_MANUAL: {agent_store.REASON_CONFIRMED_UNACKED}"
        )
        self.assertIsNone(row["lease_owner"])  # 租约放掉,但状态已是终态,不会被再领
        meta = json.loads(row["response_body"])["meta"]
        self.assertEqual(meta["reason"], agent_store.REASON_CONFIRMED_UNACKED)
        self.assertEqual(meta["ref_no"], CONFIRMED_PAYLOAD["ref_no"])
        self.assertEqual(meta["stage"], "needs_review")

        with self._cursor() as cur:
            cur.execute("SELECT last_push_status FROM ocr_history WHERE id = %s", (history_id,))
            self.assertEqual(cur.fetchone()["last_push_status"], "manual")

    def test_confirmed_row_still_in_flight_is_left_alone(self):
        """租约还没到点 = 桥/小助手可能正写着账套:既不重派,也不能急着判它没写。"""
        log_id = self._log(CONFIRMED_PAYLOAD, owner="agentA", lease_secs=600)
        leased = agent_store.lease_pending(ENDPOINT_ID, "agentB", 10)
        self.assertNotIn(log_id, {str(r["id"]) for r in leased})
        row = self._row(log_id)
        self.assertEqual((row["status"], row["lease_owner"]), ("pending", "agentA"))

    def _expire(self, log_id: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE erp_push_logs SET lease_expires_at = now() - make_interval(secs => 5) "
                "WHERE id = %s",
                (log_id,),
            )

    def setUp(self):
        with self._cursor() as cur:
            cur.execute("DELETE FROM erp_push_logs WHERE user_id = %s", (USER_ID,))


class BridgeQueueAtMostOnceTests(_PgFixture):
    """桥那条队列(bridge_jobs · kind='write')—— 同一个病,同一套处置。"""

    def _job(self, payload: dict) -> str:
        return bridge_store.enqueue_job(_bridge(), "write", payload, book_id="DATAT")

    def _row(self, job_id: str) -> dict:
        with self._cursor() as cur:
            cur.execute(
                f"SELECT status, error, result, lease_owner FROM {bridge_schema.JOBS} "
                "WHERE id = %s",
                (job_id,),
            )
            return dict(cur.fetchone())

    def _kill_lease(self, job_id: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                f"UPDATE {bridge_schema.JOBS} "
                "SET lease_expires_at = now() - make_interval(secs => 5) WHERE id = %s",
                (job_id,),
            )

    def setUp(self):
        with self._cursor() as cur:
            cur.execute(f"DELETE FROM {bridge_schema.JOBS} WHERE tenant_id = %s", (TENANT,))

    def test_plain_write_job_still_returns_to_the_queue(self):
        """普通写活的租约回收不受影响(桥崩溃了就该重派)。"""
        job_id = self._job(PLAIN_PAYLOAD)
        bridge_store.lease_jobs(_bridge(), 10)
        self._kill_lease(job_id)
        bridge_store.lease_jobs(_bridge(), 10)
        self.assertEqual(self._row(job_id)["status"], "leased")

    def test_confirmed_write_job_is_closed_instead_of_re_queued(self):
        """确认放行的写活:租约死了就落 expired 挂专属码,不回队列、不再派第二次。"""
        job_id = self._job(CONFIRMED_PAYLOAD)
        leased = bridge_store.lease_jobs(_bridge(), 10)
        self.assertIn(job_id, {str(j["id"]) for j in leased})

        self._kill_lease(job_id)
        again = bridge_store.lease_jobs(_bridge(), 10)
        self.assertNotIn(job_id, {str(j["id"]) for j in again})

        row = self._row(job_id)
        self.assertEqual(row["status"], "expired")
        self.assertEqual(row["error"]["code"], write_gate.CONFIRMED_UNACKED_CODE)
        self.assertIsNone(row["lease_owner"])

    def test_a_late_ack_after_that_still_records_the_document_number(self):
        """收尾之后桥才回来:docnum 仍要落库 —— 它是改票号重推时防重单链的唯一钥匙。"""
        job_id = self._job(CONFIRMED_PAYLOAD)
        bridge_store.lease_jobs(_bridge(), 10)
        self._kill_lease(job_id)
        bridge_store.lease_jobs(_bridge(), 10)

        out = bridge_store.finish_job(_bridge(), job_id, True, {"docnum": "IV69/09001"})
        self.assertEqual(out.get("result_saved"), True)
        self.assertEqual((self._row(job_id)["result"] or {}).get("docnum"), "IV69/09001")


if __name__ == "__main__":
    unittest.main(verbosity=2)
