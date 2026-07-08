# -*- coding: utf-8 -*-
"""Google 外流凭据/state/归档台账 DAL(export.google_store)· FakeCursor(阶段二)。

锁:token base64 落库(非明文)· get 解码回明文 · state 单次消费 · 归档台账已成功集。
"""

import base64
import unittest

from services.export import google_store as gs


class FakeCursor:
    def __init__(self, one=None, allrows=None, rowcount=1):
        self.calls = []
        self._one = list(one or [])
        self._all = list(allrows or [])
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._one.pop(0) if self._one else None

    def fetchall(self):
        return self._all.pop(0) if self._all else []


class TokenCodecTests(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(gs._b64d(gs._b64e("secret-tok")), "secret-tok")

    def test_bad_b64_returns_empty(self):
        self.assertEqual(gs._b64d("!!!notb64"), "")


class CredentialTests(unittest.TestCase):
    def test_upsert_stores_tokens_base64_not_plaintext(self):
        cur = FakeCursor()
        gs.upsert_credential(
            cur,
            tenant_id="t1",
            workspace_client_id=11,
            google_email="a@b.com",
            access_token="AT-plain",
            refresh_token="RT-plain",
            expires_at=None,
            scope="drive",
        )
        params = cur.calls[-1][1]
        self.assertIn("AT-plain", base64.b64decode(params[3]).decode())
        self.assertIn("RT-plain", base64.b64decode(params[4]).decode())
        # 明文绝不直接进 SQL 参数
        self.assertNotIn("AT-plain", params)

    def test_get_decodes_tokens(self):
        cur = FakeCursor(
            one=[
                {
                    "id": "c1",
                    "google_email": "a@b.com",
                    "access_token": gs._b64e("AT"),
                    "refresh_token": gs._b64e("RT"),
                    "expires_at": None,
                    "scope": "drive",
                    "token_version": 1,
                    "updated_at": None,
                }
            ]
        )
        cred = gs.get_credential(cur, tenant_id="t1", workspace_client_id=11)
        self.assertEqual(cred["access_token"], "AT")
        self.assertEqual(cred["refresh_token"], "RT")

    def test_get_missing_returns_none(self):
        self.assertIsNone(gs.get_credential(FakeCursor(), tenant_id="t1", workspace_client_id=11))


class StateTests(unittest.TestCase):
    def test_consume_returns_owner(self):
        cur = FakeCursor(
            one=[
                {
                    "tenant_id": "t1",
                    "workspace_client_id": 11,
                    "user_id": "u1",
                    "return_to": "pos",
                }
            ]
        )
        out = gs.consume_state(cur, state="xyz")
        self.assertEqual(
            out,
            {"tenant_id": "t1", "workspace_client_id": 11, "user_id": "u1", "return_to": "pos"},
        )

    def test_consume_missing_return_to_falls_back_to_purchase_export(self):
        # 旧 state 行(升级前建的)没有 return_to 值时列默认已保底,这里只测 None 兜底分支。
        cur = FakeCursor(
            one=[{"tenant_id": "t1", "workspace_client_id": 11, "user_id": "u1", "return_to": None}]
        )
        out = gs.consume_state(cur, state="xyz")
        self.assertEqual(out["return_to"], "purchase-export")

    def test_consume_missing_returns_none(self):
        self.assertIsNone(gs.consume_state(FakeCursor(), state="xyz"))

    def test_save_state_defaults_return_to_purchase_export(self):
        cur = FakeCursor()
        gs.save_state(cur, state="xyz", tenant_id="t1", workspace_client_id=11, user_id="u1")
        insert = cur.calls[-1]
        self.assertIn("return_to", insert[0])
        self.assertEqual(insert[1], ("xyz", "t1", 11, "u1", "purchase-export"))

    def test_save_state_custom_return_to(self):
        cur = FakeCursor()
        gs.save_state(
            cur,
            state="xyz",
            tenant_id="t1",
            workspace_client_id=11,
            user_id="u1",
            return_to="pos",
        )
        insert = cur.calls[-1]
        self.assertEqual(insert[1], ("xyz", "t1", 11, "u1", "pos"))


class ArchivedTests(unittest.TestCase):
    def test_already_archived_ids(self):
        cur = FakeCursor(allrows=[[{"doc_id": "d1"}, {"doc_id": "d2"}]])
        got = gs.already_archived_ids(
            cur, tenant_id="t1", workspace_client_id=11, doc_ids=["d1", "d2", "d3"]
        )
        self.assertEqual(got, {"d1", "d2"})

    def test_already_archived_empty_input(self):
        self.assertEqual(
            gs.already_archived_ids(
                FakeCursor(), tenant_id="t1", workspace_client_id=11, doc_ids=[]
            ),
            set(),
        )


if __name__ == "__main__":
    unittest.main()
