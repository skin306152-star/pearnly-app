# -*- coding: utf-8 -*-
"""LINE 卡片动作一次性令牌(PO-12):mint 入库 + consume 原子消费 + 重放/过期分类。"""

import unittest

from services.line_binding import line_action_nonce as nonce


class FakeNonceCursor:
    """模拟 line_action_nonces 的 INSERT / 原子 UPDATE / 分类 SELECT 行为(无真库)。"""

    def __init__(self):
        self.rows = {}
        self._ret = None

    def execute(self, sql, params=()):
        if "INSERT INTO line_action_nonces" in sql:
            token, tid, ws, uid, ref, ttl = params
            self.rows[token] = {
                "tenant_id": str(tid),
                "workspace_client_id": ws,
                "user_id": uid,
                "action_ref": ref,
                "consumed": False,
                "expired": int(ttl) <= 0,
            }
            self._ret = None
        elif "UPDATE line_action_nonces SET consumed_at" in sql:
            token, tid = params
            r = self.rows.get(token)
            if r and r["tenant_id"] == str(tid) and not r["consumed"] and not r["expired"]:
                r["consumed"] = True
                self._ret = {
                    "action_ref": r["action_ref"],
                    "workspace_client_id": r["workspace_client_id"],
                    "user_id": r["user_id"],
                }
            else:
                self._ret = None
        elif "SELECT consumed_at" in sql:
            token, tid = params
            r = self.rows.get(token)
            self._ret = (
                {"consumed_at": (1 if r["consumed"] else None), "expired": r["expired"]}
                if r and r["tenant_id"] == str(tid)
                else None
            )

    def fetchone(self):
        return self._ret


class MintTests(unittest.TestCase):
    def test_mint_returns_token(self):
        cur = FakeNonceCursor()
        tok = nonce.mint(cur, tenant_id="t", workspace_client_id=1, action_ref="D1", user_id="u")
        self.assertTrue(tok)
        self.assertIn(tok, cur.rows)
        self.assertEqual(cur.rows[tok]["action_ref"], "D1")

    def test_mint_empty_ref_no_token(self):
        cur = FakeNonceCursor()
        self.assertEqual(nonce.mint(cur, tenant_id="t", workspace_client_id=1, action_ref=""), "")
        self.assertEqual(cur.rows, {})


class ConsumeTests(unittest.TestCase):
    def _mint(self, cur, **kw):
        return nonce.mint(
            cur, tenant_id="t", workspace_client_id=7, action_ref="D9", user_id="u", **kw
        )

    def test_first_consume_ok_carries_ref(self):
        cur = FakeNonceCursor()
        tok = self._mint(cur)
        res = nonce.consume(cur, tenant_id="t", token=tok)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action_ref"], "D9")
        self.assertEqual(res["workspace_client_id"], 7)

    def test_replay_second_consume_used(self):
        cur = FakeNonceCursor()
        tok = self._mint(cur)
        self.assertEqual(nonce.consume(cur, tenant_id="t", token=tok)["status"], "ok")
        self.assertEqual(nonce.consume(cur, tenant_id="t", token=tok)["status"], "used")

    def test_expired_token(self):
        cur = FakeNonceCursor()
        tok = self._mint(cur, ttl_hours=0)
        self.assertEqual(nonce.consume(cur, tenant_id="t", token=tok)["status"], "expired")

    def test_missing_token(self):
        cur = FakeNonceCursor()
        self.assertEqual(nonce.consume(cur, tenant_id="t", token="nope")["status"], "missing")
        self.assertEqual(nonce.consume(cur, tenant_id="t", token="")["status"], "missing")

    def test_wrong_tenant_cannot_consume(self):
        cur = FakeNonceCursor()
        tok = self._mint(cur)
        self.assertEqual(nonce.consume(cur, tenant_id="other", token=tok)["status"], "missing")


if __name__ == "__main__":
    unittest.main()
