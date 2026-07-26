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
            token, tid = params[0], params[1]
            r = self.rows.get(token)
            hit = (
                r
                and r["tenant_id"] == str(tid)
                and not r["consumed"]
                and not r["expired"]
                and self._kind_ok(sql, params, r)
            )
            if hit:
                r["consumed"] = True
                self._ret = {
                    "action_ref": r["action_ref"],
                    "workspace_client_id": r["workspace_client_id"],
                    "user_id": r["user_id"],
                }
            else:
                self._ret = None
        elif "SELECT consumed_at" in sql:
            token, tid = params[0], params[1]
            r = self.rows.get(token)
            self._ret = (
                {
                    "consumed_at": (1 if r["consumed"] else None),
                    "action_ref": r["action_ref"],
                    "workspace_client_id": r["workspace_client_id"],
                    "expired": r["expired"],
                }
                if r and r["tenant_id"] == str(tid) and self._kind_ok(sql, params, r)
                else None
            )

    @staticmethod
    def _kind_ok(sql, params, row):
        """`action_ref LIKE %s` 的前缀语义(pattern 尾是 %)。"""
        if "action_ref LIKE %s" not in sql:
            return True
        return row["action_ref"].startswith(params[2].rstrip("%"))

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
        replay = nonce.consume(cur, tenant_id="t", token=tok)
        self.assertEqual(replay["status"], "used")
        # 重放仍携目标记录 → 据此按真实状态重发当前卡(P1G 验收 2)。
        self.assertEqual(replay["action_ref"], "D9")
        self.assertEqual(replay["workspace_client_id"], 7)

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

    def test_ref_kind_filter_refuses_foreign_kind_without_burning(self):
        """表由 LINE 卡与管家授权卡共用:带 ref_kind 的消费对别家类别按 missing,
        且绝不落 consumed —— 一次性凭证不被别的子系统隔空烧掉。"""
        cur = FakeNonceCursor()
        tok = nonce.mint(
            cur,
            tenant_id="t",
            workspace_client_id=7,
            action_ref='{"kind": "agent_push", "doc_id": "d1"}',
            user_id="u",
        )
        res = nonce.consume(cur, tenant_id="t", token=tok, ref_kind="steward_write")
        self.assertEqual(res["status"], "missing")
        self.assertFalse(cur.rows[tok]["consumed"])
        # 类别对上照常单次单用。
        ok = nonce.consume(cur, tenant_id="t", token=tok, ref_kind="agent_push")
        self.assertEqual(ok["status"], "ok")


if __name__ == "__main__":
    unittest.main()
