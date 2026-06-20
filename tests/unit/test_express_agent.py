# -*- coding: utf-8 -*-
"""Express Agent DAL + 路由契约单测(fake cursor · 无真实 DB)。

钉死:token sha256 校验(防越权)· lease 返回载荷 · ack 状态机(success 回填 /
lease 不符拒 / 终态幂等 / 失败 attempt+1 超 3 置 manual)· schema ALTER 含租约列 ·
4 个 Agent 路由注册齐 · 租约列 ensure SQL 幂等。
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

from services.erp import push_schema  # noqa: E402
from services.erp.express_push import agent_store  # noqa: E402


class FakeCursor:
    """记录 execute · fetchone/fetchall 返预设值。"""

    def __init__(self, one=None, many=None):
        self._one = one
        self._many = many or []
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._many


def _patch_cursor(cur):
    @contextlib.contextmanager
    def _gc(*a, **k):
        yield cur

    return mock.patch("core.db.get_cursor", _gc)


class TokenAuthTests(unittest.TestCase):
    def test_hash_deterministic(self):
        self.assertEqual(agent_store.hash_token("abc"), agent_store.hash_token("abc"))
        self.assertNotEqual(agent_store.hash_token("abc"), agent_store.hash_token("abd"))

    def test_authenticate_rejects_malformed(self):
        self.assertIsNone(agent_store.authenticate(""))
        self.assertIsNone(agent_store.authenticate("Bearer x"))
        self.assertIsNone(agent_store.authenticate("exp_only"))

    def test_authenticate_matches_hash(self):
        token = "exp_ep-1_secretsecret"
        ep = {"id": "ep-1", "config": {"agent_token_hash": agent_store.hash_token(token)}}
        with mock.patch.object(agent_store, "get_express_endpoint", return_value=ep):
            self.assertEqual(agent_store.authenticate(token)["id"], "ep-1")
            # 篡改 token → 拒
            self.assertIsNone(agent_store.authenticate("exp_ep-1_tampered"))


class LeaseAckTests(unittest.TestCase):
    def test_lease_returns_payloads(self):
        rows = [
            {
                "id": "log-1",
                "history_id": "h1",
                "invoice_no": "RR1",
                "request_body": {"account_set": "DATAT"},
                "lease_expires_at": None,
            }
        ]
        with _patch_cursor(FakeCursor(many=rows)):
            out = agent_store.lease_pending("ep-1", "agentA", 5)
        self.assertEqual(out[0]["id"], "log-1")
        self.assertEqual(out[0]["request_body"]["account_set"], "DATAT")

    def test_ack_success_fills_docnum(self):
        row = {
            "id": "log-1",
            "status": "pending",
            "attempt": 0,
            "lease_owner": "agentA",
            "response_body": None,
        }
        cur = FakeCursor(one=row)
        with _patch_cursor(cur):
            res = agent_store.ack("ep-1", "log-1", "agentA", True, express_docnum="RR581231-002")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["express_docnum"], "RR581231-002")
        self.assertTrue(any("status = 'success'" in sql for sql, _ in cur.executed))

    def test_ack_lease_mismatch_rejected(self):
        row = {
            "id": "log-1",
            "status": "pending",
            "attempt": 0,
            "lease_owner": "agentA",
            "response_body": None,
        }
        with _patch_cursor(FakeCursor(one=row)):
            res = agent_store.ack("ep-1", "log-1", "intruder", True)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "lease_mismatch")

    def test_ack_terminal_idempotent(self):
        row = {
            "id": "log-1",
            "status": "success",
            "attempt": 1,
            "lease_owner": None,
            "response_body": "{}",
        }
        with _patch_cursor(FakeCursor(one=row)):
            res = agent_store.ack("ep-1", "log-1", "agentA", True)
        self.assertTrue(res["ok"])
        self.assertTrue(res.get("idempotent"))

    def test_ack_failed_increments_then_manual(self):
        # attempt 0 → 1 · 仍 pending(可重领)
        row1 = {
            "id": "log-1",
            "status": "pending",
            "attempt": 0,
            "lease_owner": "agentA",
            "response_body": None,
        }
        with _patch_cursor(FakeCursor(one=row1)):
            res = agent_store.ack("ep-1", "log-1", "agentA", False, error="rpa timeout")
        self.assertEqual(res["status"], "pending")
        self.assertEqual(res["attempt"], 1)
        # attempt 2 → 3 · 置 manual(留人工)
        row3 = {
            "id": "log-1",
            "status": "pending",
            "attempt": 2,
            "lease_owner": "agentA",
            "response_body": None,
        }
        with _patch_cursor(FakeCursor(one=row3)):
            res = agent_store.ack("ep-1", "log-1", "agentA", False, error="rpa timeout")
        self.assertEqual(res["status"], "manual")
        self.assertEqual(res["attempt"], 3)

    def test_ack_log_not_found(self):
        with _patch_cursor(FakeCursor(one=None)):
            res = agent_store.ack("ep-1", "missing", "agentA", True)
        self.assertEqual(res["reason"], "log_not_found")


class SchemaAndRouteTests(unittest.TestCase):
    def test_lease_columns_alter_sql(self):
        # 租约列折叠进已接线的 ensure_erp_retry_columns(同表运营列 · 不另加启动钩子)。
        cur = FakeCursor()
        with mock.patch("services.erp.push_schema.db") as fake_db:
            fake_db.get_cursor.return_value.__enter__.return_value = cur
            fake_db.get_cursor.return_value.__exit__.return_value = False
            push_schema.ensure_erp_retry_columns()
        sql = " ".join(s for s, _ in cur.executed)
        self.assertIn("lease_owner", sql)
        self.assertIn("lease_expires_at", sql)
        self.assertIn("idx_erp_logs_pending_lease", sql)
        self.assertIn("IF NOT EXISTS", sql)

    def test_agent_routes_registered(self):
        from routes.erp_agent import router

        paths = {r.path for r in router.routes}
        self.assertIn("/api/erp/agent/heartbeat", paths)
        self.assertIn("/api/erp/agent/lease", paths)
        self.assertIn("/api/erp/agent/ack", paths)
        self.assertIn("/api/erp/endpoints/{endpoint_id}/agent-token", paths)


if __name__ == "__main__":
    unittest.main(verbosity=2)
