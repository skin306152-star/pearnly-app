# -*- coding: utf-8 -*-
"""管家成本台账(steward_cost_entries)真 Postgres 冒烟 —— 补假游标证不了的三样。

tests/unit/test_steward_authz.py 用 FakeCursor 只能钉「SQL 长这样、参数接在这个位」;
三件只有真库才成立的事在那里一条都验不了,而它们全在钱路径上:
  1. numeric(12, 6) —— 多次小额结算累加后合计逐位相等(float 累加会漂),第 7 位四舍五入到
     scale 6,整数位超 6 位被拒。列被改宽/改窄,封顶的合计与进位口径就变了。
  2. pg_advisory_xact_lock —— 同租户两路并发预留必须串行:两路各自没超、合计超上限时要拦住
     第二路。假游标下这句锁是零执行的。
  3. RLS —— A 租户的连接读不到 B 租户的台账行,也塞不进 B 的行(WITH CHECK)。

每条真闸都配反证(见 *_without_* / *_when_* 命名的用例):把锁那句吞掉、把 RLS 关掉之后
对应断言必须翻红。没有「改坏必红」,清单式的绿分不清「代码对」和「闸根本没看」。

只认显式本地 DSN(env PEARNLY_PG_SMOKE_URL 或 compose 默认),绝不回落 DATABASE_URL
(防误连生产);连不上(docker 没开 / CI 无 Postgres 服务)则整类 skip。照
tests/unit/test_erp_bridge_pg_smoke.py 的既有范式,CI 一旦配上 postgres service 两份一起亮。

本地跑:
    docker compose up -d pearnly-db
    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 \
      python -m unittest tests.unit.test_steward_budget_pg_smoke -v
"""

from __future__ import annotations

import contextlib
import functools
import os
import sys
import threading
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.steward import budget  # noqa: E402

_LOCAL_DSN = os.environ.get(
    "PEARNLY_PG_SMOKE_URL", "postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly"
)

_TABLE = "steward_cost_entries"
_APP_ROLE = "pearnly_app"

# 并发用例的竞态窗口:reserve 读完合计、写占坑行之前停这么久。
# 拿不到竞态就等于没验,所以窗口要大到「没有锁必然重叠」,又小到测试还能秒回。
_HOLD_SECONDS = 0.6


def _connect():
    import psycopg2

    return psycopg2.connect(_LOCAL_DSN, connect_timeout=3)


class _NoAdvisoryLockCursor:
    """把 reserve 里那句 pg_advisory_xact_lock 换成空查询,其余 SQL 原样执行。

    反证要的是「锁拆掉就出竞态」这件事本身可复跑。改源码跑一遍留不进仓库,下一个人也无从
    确认这条并发用例当初真的会红。
    """

    def __init__(self, inner):
        self._inner = inner

    def execute(self, sql, params=None):
        if "pg_advisory_xact_lock" in sql:
            return self._inner.execute("SELECT NULL AS lock_stripped")
        return self._inner.execute(sql, params)

    def __getattr__(self, name):
        return getattr(self._inner, name)


@contextlib.contextmanager
def _own_cursor(commit: bool = False, *, strip_lock: bool = False):
    """替身 core.db.get_cursor:每次一条独立连接(并发用例两线程不共享 SimpleConnectionPool)。"""
    from psycopg2.extras import RealDictCursor

    conn = _connect()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield _NoAdvisoryLockCursor(cur) if strip_lock else cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()


@contextlib.contextmanager
def _tenant_cursor(tenant_id):
    """最小权限连接(照 core.db.get_cursor_rls 的口径):SET LOCAL ROLE + tenant 上下文。

    RLS 只对 NOBYPASSRLS 且非属主的角色强制,不切角色的连接看不出隔离有没有生效。
    """
    from psycopg2.extras import RealDictCursor

    conn = _connect()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(f"SET LOCAL ROLE {_APP_ROLE}")
            cur.execute("SET LOCAL app.current_tenant_id = %s", (str(tenant_id),))
            yield cur
        finally:
            cur.close()
            conn.rollback()
    finally:
        conn.close()


def _race_pair(tenant_id: str, *, strip_lock: bool) -> tuple[list, float]:
    """同租户两个会话同时 reserve,返回(两路结果, 两路合起来的墙钟跨度)。

    跨度是串行化的直接证据:锁在 → 第二路被挡在锁上,跨度约 2×窗口;锁不在 → 两路重叠,
    跨度约 1×窗口。只看「谁被拒」判不出是锁起了作用还是恰好排队。
    """
    ready = threading.Barrier(2)
    marks: dict[int, tuple[float, float]] = {}
    results: dict[int, dict] = {}

    def one(idx: int):
        ready.wait(timeout=5)
        started = time.monotonic()
        results[idx] = budget.reserve(
            tenant_id=tenant_id, session_id=str(uuid.uuid4()), task_id=None
        )
        marks[idx] = (started, time.monotonic())

    real_decide = budget.decide

    def held_decide(**kwargs):
        # 停在「读完合计、还没写占坑行」之间 —— check-then-spend 的赛道正好在这里。
        time.sleep(_HOLD_SECONDS)
        return real_decide(**kwargs)

    cursor = functools.partial(_own_cursor, strip_lock=True) if strip_lock else _own_cursor
    with mock.patch("core.db.get_cursor", cursor), mock.patch.object(budget, "decide", held_decide):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(one, i) for i in (0, 1)]
            for fut in futures:
                fut.result(timeout=30)

    span = max(end for _s, end in marks.values()) - min(start for start, _e in marks.values())
    return [results[0], results[1]], span


class _LedgerPgTestCase(unittest.TestCase):
    """连不上本地库整类 skip;连得上就用独立连接替掉连接池,真建表真跑。"""

    @classmethod
    def setUpClass(cls):
        try:
            _connect().close()
        except Exception as exc:
            raise unittest.SkipTest(f"本地 pearnly-db 不可达({exc!r})· 起 docker compose 后再跑")
        cls._patch = mock.patch("core.db.get_cursor", _own_cursor)
        cls._patch.start()
        cls._ensured_before = budget._ensured
        budget.ensure_tables()
        # 让后续 reserve 跳过 ensure_once:建表里的 DROP/CREATE POLICY 要 ACCESS EXCLUSIVE 锁,
        # 并发用例下会跟在途事务顶死。
        budget._ensured = True

    @classmethod
    def tearDownClass(cls):
        budget._ensured = cls._ensured_before
        cls._patch.stop()

    def new_tenant(self) -> str:
        tenant = str(uuid.uuid4())
        self.addCleanup(self.purge, tenant)
        return tenant

    @staticmethod
    def purge(tenant_id: str) -> int:
        with _own_cursor(commit=True) as cur:
            cur.execute(f"DELETE FROM {_TABLE} WHERE tenant_id = %s", (tenant_id,))
            return cur.rowcount

    @staticmethod
    def ledger(tenant_id: str) -> list[dict]:
        with _own_cursor() as cur:
            cur.execute(
                f"SELECT id, cost_thb, settled FROM {_TABLE} "
                "WHERE tenant_id = %s ORDER BY created_at, id",
                (tenant_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def total(tenant_id: str) -> Decimal:
        with _own_cursor() as cur:
            cur.execute(
                f"SELECT COALESCE(SUM(cost_thb), 0) AS s FROM {_TABLE} WHERE tenant_id = %s",
                (tenant_id,),
            )
            return cur.fetchone()["s"]

    @staticmethod
    def caps(*, task="0", session="0", tenant="0", reserve="0.30"):
        return mock.patch.dict(
            os.environ,
            {
                "STEWARD_TASK_COST_CAP_THB": task,
                "STEWARD_SESSION_COST_CAP_THB": session,
                "STEWARD_TENANT_DAILY_CAP_THB": tenant,
                "STEWARD_CALL_COST_RESERVE_THB": reserve,
            },
        )


class CostLedgerPrecisionTests(_LedgerPgTestCase):
    def test_repeated_settlements_sum_without_float_drift(self):
        """12 次 ฿0.070001 结算,合计逐位等于 0.840012(同一串加法走 float 落到 ...119999999999)。"""
        tenant, session = self.new_tenant(), str(uuid.uuid4())
        unit = Decimal("0.070001")
        with self.caps(session="1000"):
            for _ in range(12):
                gate = budget.reserve(tenant_id=tenant, session_id=session)
                self.assertTrue(gate["allowed"])
                self.assertIsNotNone(gate["entry_id"], "占坑行没落库 = reserve 走了 fail-open")
                budget.settle(tenant_id=tenant, entry_id=gate["entry_id"], cost_thb=unit)

        rows = self.ledger(tenant)
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(r["settled"] for r in rows))
        self.assertEqual([r["cost_thb"] for r in rows], [unit] * 12)
        got = self.total(tenant)
        self.assertEqual(got, Decimal("0.840012"))
        self.assertEqual(str(got), "0.840012", "scale 被吞 = 列不是 numeric(_, 6)")

        drifted = 0.0
        for _ in range(12):
            drifted += float(unit)
        self.assertNotEqual(repr(drifted), str(got), "float 都没漂,这条用例证不出精度")

    def test_seventh_decimal_rounds_into_scale_six(self):
        """结算额比 scale 多一位:落库四舍五入到 6 位,不是截断也不是原样存下。"""
        tenant = self.new_tenant()
        with self.caps(session="1000"):
            gate = budget.reserve(tenant_id=tenant, session_id=str(uuid.uuid4()))
            budget.settle(
                tenant_id=tenant, entry_id=gate["entry_id"], cost_thb=Decimal("0.12345678")
            )
        self.assertEqual(self.ledger(tenant)[0]["cost_thb"], Decimal("0.123457"))

    def test_amount_past_six_integer_digits_is_rejected(self):
        """precision 12 - scale 6 = 整数位上限 6:฿1,000,000 落不进去(列被改宽这条会绿)。

        走裸 SQL 而不走 settle:settle 吞异常只告警(结算不连坐已完成的调用),
        经它看不出列拒没拒。
        """
        import psycopg2

        tenant = self.new_tenant()
        with self.assertRaises(psycopg2.errors.NumericValueOutOfRange):
            with _own_cursor(commit=True) as cur:
                cur.execute(
                    f"INSERT INTO {_TABLE} (tenant_id, session_id, cost_thb) VALUES (%s, %s, %s)",
                    (tenant, str(uuid.uuid4()), Decimal("1000000")),
                )


class CostLedgerAdvisoryLockTests(_LedgerPgTestCase):
    """租户日额跨会话汇总,会话行锁串行化不了两个会话的并发预留 —— 靠 advisory lock。"""

    def test_concurrent_reserves_cannot_both_pass_tenant_cap(self):
        """两路各自没超(0.30 ≤ 0.50)、合计超(0.60 > 0.50):锁在 → 第二路被拒,台账只留一行。"""
        tenant = self.new_tenant()
        with self.caps(tenant="0.5"):
            results, span = _race_pair(tenant, strip_lock=False)

        allowed = [r for r in results if r["allowed"]]
        refused = [r for r in results if not r["allowed"]]
        self.assertEqual(len(allowed), 1, f"应只放行一路,实得 {results}")
        self.assertIsNotNone(allowed[0]["entry_id"], "放行那路走了 fail-open,不算通过")
        self.assertEqual(refused[0]["code"], budget.ERR_TENANT)
        self.assertEqual(self.total(tenant), Decimal("0.300000"))
        self.assertGreater(
            span,
            _HOLD_SECONDS * 1.8,
            f"两路墙钟跨度 {span:.2f}s < 2×窗口:没有真串行,只是碰巧一前一后",
        )

    def test_race_reappears_without_the_advisory_lock(self):
        """反证:把那句锁吞掉,同一场景两路全放行、合计破线 —— 上一条用例确实看得见竞态。"""
        tenant = self.new_tenant()
        with self.caps(tenant="0.5"):
            results, span = _race_pair(tenant, strip_lock=True)

        self.assertTrue(all(r["allowed"] for r in results), f"竞态没复现出来:{results}")
        self.assertTrue(all(r["entry_id"] for r in results))
        self.assertEqual(self.total(tenant), Decimal("0.600000"))
        self.assertLess(
            span, _HOLD_SECONDS * 1.5, f"两路墙钟跨度 {span:.2f}s:没重叠,这条反证不成立"
        )


class CostLedgerRlsTests(_LedgerPgTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from core import rls

        with _own_cursor(commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {_TABLE} TO {_APP_ROLE}")

    def _two_tenants(self):
        a, b = self.new_tenant(), self.new_tenant()
        with self.caps(session="1000"):
            ga = budget.reserve(tenant_id=a, session_id=str(uuid.uuid4()))
            gb = budget.reserve(tenant_id=b, session_id=str(uuid.uuid4()))
        self.assertTrue(ga["entry_id"] and gb["entry_id"])
        return (a, ga["entry_id"]), (b, gb["entry_id"])

    @staticmethod
    def _visible(tenant_id, entry_id) -> int:
        with _tenant_cursor(tenant_id) as cur:
            cur.execute(f"SELECT count(*) AS n FROM {_TABLE} WHERE id = %s", (entry_id,))
            return cur.fetchone()["n"]

    def test_tenant_reads_own_rows_only(self):
        (a, entry_a), (b, entry_b) = self._two_tenants()
        self.assertEqual(self._visible(a, entry_a), 1, "A 应看得见自己的行")
        self.assertEqual(self._visible(a, entry_b), 0, "A 看见了 B 的台账行")
        self.assertEqual(self._visible(b, entry_a), 0, "B 看见了 A 的台账行")
        with _tenant_cursor(a) as cur:
            cur.execute(f"SELECT DISTINCT tenant_id FROM {_TABLE}")
            self.assertEqual({str(r["tenant_id"]) for r in cur.fetchall()}, {a})

    def test_with_check_blocks_writing_into_another_tenant(self):
        import psycopg2

        a, b = self.new_tenant(), self.new_tenant()
        with _tenant_cursor(a) as cur:
            with self.assertRaises(psycopg2.errors.Error):
                cur.execute(
                    f"INSERT INTO {_TABLE} (tenant_id, session_id, cost_thb) VALUES (%s, %s, 1)",
                    (b, str(uuid.uuid4())),
                )

    def test_rows_leak_when_row_level_security_is_off(self):
        """反证:关掉 RLS,A 的连接立刻读得到 B 的行 —— 上面那条不是因为查询本身查不到东西。"""
        (a, _entry_a), (_b, entry_b) = self._two_tenants()
        self.addCleanup(budget.ensure_tables)
        with _own_cursor(commit=True) as cur:
            cur.execute(f"ALTER TABLE {_TABLE} DISABLE ROW LEVEL SECURITY")
        self.assertEqual(self._visible(a, entry_b), 1, "RLS 关了还是看不到 = 这条隔离断言是空的")


if __name__ == "__main__":
    unittest.main(verbosity=2)
