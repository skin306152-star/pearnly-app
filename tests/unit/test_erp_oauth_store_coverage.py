# -*- coding: utf-8 -*-
"""REFACTOR-D2 覆盖补强 · services/erp/oauth_store.py 数据层行为契约

用假游标截 SQL/params,验证 OAuth token / state CRUD 的:
  - base64 编解码可逆 + 空值容错。
  - state 存/消费(5 分钟过期窗 + 单次消费 RETURNING)。
  - token upsert 的 base64 编码、is_default 互斥、必填校验短路。
  - 默认 token 取出后解码、列举、刷新写回、删除、切默认。
  - 自动推送开关(set/get/list)的 tenant scope 与边界。
  - 异常分支吞掉 → 安全默认值。

不触真实 OAuth / token 刷新 / 计费。
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core import db  # noqa: E402,F401
from services.erp import oauth_store as store  # noqa: E402


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None, rowcount=0):
        self.calls = []
        self._fetchone = fetchone
        self._fetchall = fetchall if fetchall is not None else []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall

    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class FakeCM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def patch_cursor(cur):
    return mock.patch.object(store.db, "get_cursor", lambda *a, **k: FakeCM(cur))


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(store.db, "get_cursor", factory)


# ─────────────────────── base64 helper ───────────────────────
class B64HelperTests(unittest.TestCase):
    def test_roundtrip_unicode(self):
        s = "tok-สวัสดี-🔑-123"
        self.assertEqual(store._b64_decode(store._b64_encode(s)), s)

    def test_encode_none_and_empty(self):
        # _b64_encode(None) → 编码空串(不抛)
        self.assertEqual(store._b64_decode(store._b64_encode(None)), "")
        self.assertEqual(store._b64_decode(store._b64_encode("")), "")

    def test_decode_garbage_returns_empty(self):
        # 非法 base64 → 返回空串(吞异常),不冒泡
        self.assertEqual(store._b64_decode("!!!not base64!!!"), "")

    def test_decode_none(self):
        self.assertEqual(store._b64_decode(None), "")


# ─────────────────────── 自动推送开关 ───────────────────────
class AutoPushSwitchTests(unittest.TestCase):
    def test_set_requires_tenant(self):
        with patch_cursor_raises(AssertionError("no query")):
            self.assertFalse(store.set_xero_auto_push("", True))

    def test_set_updates_xero_rows(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            ok = store.set_xero_auto_push("t1", True)
        self.assertTrue(ok)
        self.assertIn("erp_type = 'xero'", cur.last_sql)
        self.assertEqual(cur.last_params, (True, "t1"))

    def test_set_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.set_xero_auto_push("t1", True))

    def test_get_true_when_any_row(self):
        cur = FakeCursor(fetchone={"?column?": 1})
        with patch_cursor(cur):
            self.assertTrue(store.get_xero_auto_push("t1"))
        self.assertIn("auto_push = TRUE", cur.last_sql)

    def test_get_false_when_no_row(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertFalse(store.get_xero_auto_push("t1"))

    def test_get_no_tenant_false(self):
        self.assertFalse(store.get_xero_auto_push(""))

    def test_get_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.get_xero_auto_push("t1"))

    def test_list_tenants_returns_tid_list(self):
        cur = FakeCursor(fetchall=[{"tid": "t1"}, {"tid": "t2"}])
        with patch_cursor(cur):
            out = store.list_tenants_xero_auto_push_on()
        self.assertEqual(out, ["t1", "t2"])
        self.assertIn("auto_push = TRUE", cur.last_sql)

    def test_list_tenants_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(store.list_tenants_xero_auto_push_on(), [])


# ─────────────────────── OAuth state ───────────────────────
class SaveOauthStateTests(unittest.TestCase):
    def test_missing_args_false(self):
        with patch_cursor_raises(AssertionError("no query")):
            self.assertFalse(store.save_oauth_state("", "t", "u", "xero"))
            self.assertFalse(store.save_oauth_state("s", "", "u", "xero"))
            self.assertFalse(store.save_oauth_state("s", "t", "", "xero"))

    def test_gc_old_then_upsert(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            ok = store.save_oauth_state("s1", "t1", "u1", "xero")
        self.assertTrue(ok)
        # 第一条:GC 5 分钟前的;第二条:INSERT ... ON CONFLICT
        self.assertIn("DELETE FROM erp_oauth_states", cur.calls[0][0])
        self.assertIn("INTERVAL '5 minutes'", cur.calls[0][0])
        self.assertIn("ON CONFLICT (state)", cur.calls[1][0])
        self.assertEqual(cur.calls[1][1], ("s1", "t1", "u1", "xero"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.save_oauth_state("s", "t", "u", "xero"))


class ConsumeOauthStateTests(unittest.TestCase):
    def test_none_state_short_circuit(self):
        with patch_cursor_raises(AssertionError("no query")):
            self.assertIsNone(store.consume_oauth_state(None))

    def test_returns_dict_within_window(self):
        cur = FakeCursor(fetchone={"tenant_id": "t1", "user_id": "u1", "erp_type": "xero"})
        with patch_cursor(cur):
            out = store.consume_oauth_state("s1")
        self.assertEqual(out, {"tenant_id": "t1", "user_id": "u1", "erp_type": "xero"})
        # 单次消费 + 5 分钟窗
        self.assertIn("DELETE FROM erp_oauth_states", cur.last_sql)
        self.assertIn("RETURNING", cur.last_sql)
        self.assertIn("INTERVAL '5 minutes'", cur.last_sql)

    def test_expired_or_missing_returns_none(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(store.consume_oauth_state("s1"))

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.consume_oauth_state("s1"))


# ─────────────────────── token upsert / get / list ───────────────────────
class UpsertOauthTokenTests(unittest.TestCase):
    def _args(self, **over):
        base = dict(
            tenant_id="t1",
            erp_type="xero",
            organisation_id="org1",
            organisation_name="Acme",
            access_token="acc",
            refresh_token="ref",
            expires_at="2026-01-01T00:00:00Z",
            scope="scope",
            is_default=False,
            user_id="u1",
        )
        base.update(over)
        return base

    def test_required_fields_short_circuit(self):
        with patch_cursor_raises(AssertionError("no query")):
            self.assertIsNone(store.upsert_oauth_token(**self._args(tenant_id="")))
            self.assertIsNone(store.upsert_oauth_token(**self._args(access_token="")))
            self.assertIsNone(store.upsert_oauth_token(**self._args(refresh_token="")))
            self.assertIsNone(store.upsert_oauth_token(**self._args(organisation_id="")))

    def test_tokens_base64_encoded_in_params(self):
        cur = FakeCursor(fetchone={"id": "tk-1"})
        with patch_cursor(cur):
            out = store.upsert_oauth_token(**self._args())
        self.assertEqual(out, "tk-1")
        insert_call = [c for c in cur.calls if "INSERT INTO erp_oauth_tokens" in c[0]][0]
        params = insert_call[1]
        # access/refresh 在 params 中应是 base64,不是明文
        self.assertIn(store._b64_encode("acc"), params)
        self.assertIn(store._b64_encode("ref"), params)
        self.assertNotIn("acc", [p for p in params if p == "acc"])

    def test_is_default_unsets_others_first(self):
        cur = FakeCursor(fetchone={"id": "tk-1"})
        with patch_cursor(cur):
            store.upsert_oauth_token(**self._args(is_default=True))
        self.assertIn("SET is_default = FALSE", cur.calls[0][0])

    def test_not_default_no_unset(self):
        cur = FakeCursor(fetchone={"id": "tk-1"})
        with patch_cursor(cur):
            store.upsert_oauth_token(**self._args(is_default=False))
        self.assertNotIn("SET is_default = FALSE", cur.all_sql())

    def test_exception_returns_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.upsert_oauth_token(**self._args()))


class GetDefaultOauthTokenTests(unittest.TestCase):
    def test_missing_args_none(self):
        self.assertIsNone(store.get_default_oauth_token("", "xero"))
        self.assertIsNone(store.get_default_oauth_token("t1", ""))

    def test_decodes_tokens(self):
        enc_acc = store._b64_encode("plain-access")
        enc_ref = store._b64_encode("plain-refresh")
        cur = FakeCursor(
            fetchone={
                "id": "tk1",
                "access_token": enc_acc,
                "refresh_token": enc_ref,
                "organisation_id": "org1",
            }
        )
        with patch_cursor(cur):
            out = store.get_default_oauth_token("t1", "xero")
        # 返回的是解码后明文
        self.assertEqual(out["access_token"], "plain-access")
        self.assertEqual(out["refresh_token"], "plain-refresh")
        self.assertIn("is_default DESC", cur.last_sql)

    def test_no_row_none(self):
        cur = FakeCursor(fetchone=None)
        with patch_cursor(cur):
            self.assertIsNone(store.get_default_oauth_token("t1", "xero"))

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(store.get_default_oauth_token("t1", "xero"))


class ListOauthTokensTests(unittest.TestCase):
    def test_missing_args_empty(self):
        self.assertEqual(store.list_oauth_tokens("", "xero"), [])
        self.assertEqual(store.list_oauth_tokens("t1", ""), [])

    def test_returns_dict_rows_scoped(self):
        cur = FakeCursor(fetchall=[{"id": "a"}, {"id": "b"}])
        with patch_cursor(cur):
            out = store.list_oauth_tokens("t1", "xero")
        self.assertEqual([r["id"] for r in out], ["a", "b"])
        self.assertEqual(cur.last_params, ("t1", "xero"))

    def test_exception_empty(self):
        with patch_cursor_raises():
            self.assertEqual(store.list_oauth_tokens("t1", "xero"), [])


class UpdateAccessTokenTests(unittest.TestCase):
    def test_required_fields_false(self):
        self.assertFalse(store.update_oauth_access_token("", "a", "r", "exp"))
        self.assertFalse(store.update_oauth_access_token("id", "", "r", "exp"))
        self.assertFalse(store.update_oauth_access_token("id", "a", "", "exp"))

    def test_writes_base64_and_rowcount_true(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = store.update_oauth_access_token("tk1", "newacc", "newref", "exp")
        self.assertTrue(ok)
        self.assertIn(store._b64_encode("newacc"), cur.last_params)
        self.assertIn(store._b64_encode("newref"), cur.last_params)

    def test_rowcount_zero_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(store.update_oauth_access_token("tk1", "a", "r", "e"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.update_oauth_access_token("tk1", "a", "r", "e"))


class DeleteOauthTokensTests(unittest.TestCase):
    def test_missing_args_zero(self):
        self.assertEqual(store.delete_oauth_tokens("", "xero"), 0)
        self.assertEqual(store.delete_oauth_tokens("t1", ""), 0)

    def test_returns_rowcount(self):
        cur = FakeCursor(rowcount=3)
        with patch_cursor(cur):
            n = store.delete_oauth_tokens("t1", "xero")
        self.assertEqual(n, 3)
        self.assertEqual(cur.last_params, ("t1", "xero"))

    def test_exception_zero(self):
        with patch_cursor_raises():
            self.assertEqual(store.delete_oauth_tokens("t1", "xero"), 0)


class SetDefaultOauthTokenTests(unittest.TestCase):
    def test_missing_args_false(self):
        self.assertFalse(store.set_default_oauth_token("", "xero", "tk1"))
        self.assertFalse(store.set_default_oauth_token("t1", "", "tk1"))
        self.assertFalse(store.set_default_oauth_token("t1", "xero", ""))

    def test_unsets_all_then_sets_one(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            ok = store.set_default_oauth_token("t1", "xero", "tk1")
        self.assertTrue(ok)
        self.assertIn("SET is_default = FALSE", cur.calls[0][0])
        self.assertIn("SET is_default = TRUE", cur.calls[1][0])
        # 切默认时第二条带 tenant + erp scope(防跨租户切默认)
        self.assertEqual(cur.calls[1][1], ("tk1", "t1", "xero"))

    def test_rowcount_zero_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(store.set_default_oauth_token("t1", "xero", "tk1"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(store.set_default_oauth_token("t1", "xero", "tk1"))


if __name__ == "__main__":
    unittest.main()
