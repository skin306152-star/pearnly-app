# -*- coding: utf-8 -*-
"""销项 PO-7 · 分享能力 token(生成/复用/反查)守门 · 不连库。"""

import unittest

from services.sales import share


class TokenCursor:
    """假游标:SELECT share_token 回 self.row;记录 execute。"""

    def __init__(self, row):
        self.row = row
        self.calls = []
        self._sel = False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        self._sel = sql.strip().startswith("SELECT")

    def fetchone(self):
        return self.row if self._sel else None


class ShareTokenTests(unittest.TestCase):
    def test_generates_when_absent(self):
        cur = TokenCursor({"share_token": None})
        tok = share.get_or_create_share_token(cur, tenant_id="t", doc_id="d")
        self.assertTrue(tok and len(tok) >= 20)
        self.assertTrue(any("UPDATE sales_documents SET share_token" in s for s, _ in cur.calls))

    def test_reuses_existing(self):
        cur = TokenCursor({"share_token": "abc123existing"})
        tok = share.get_or_create_share_token(cur, tenant_id="t", doc_id="d")
        self.assertEqual(tok, "abc123existing")
        self.assertFalse(any("UPDATE" in s for s, _ in cur.calls))

    def test_missing_document_returns_none(self):
        cur = TokenCursor(None)
        self.assertIsNone(share.get_or_create_share_token(cur, tenant_id="t", doc_id="d"))

    def test_resolve_token_queries_by_token(self):
        cur = TokenCursor({"tenant_id": "t", "document_id": "d"})
        ref = share.resolve_token(cur, "sometoken")
        self.assertEqual(ref["tenant_id"], "t")
        self.assertIn("WHERE share_token=%s", cur.calls[0][0])

    def test_resolve_empty_token(self):
        self.assertIsNone(share.resolve_token(TokenCursor(None), ""))


if __name__ == "__main__":
    unittest.main()
