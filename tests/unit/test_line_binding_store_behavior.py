# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/line_binding/store.py 行为单测(LINE 绑定 DAL · 高敏 line·只加测试不改逻辑)

补真实行为/边界/错误分支(原仅 contract · 行为覆盖 ~26%):
generate/consume 绑定码(6 位数字格式守卫)+ create_or_update(LINE 已绑他人 → 拒绝)+ 反查(更新活跃时间)+
get/unbind 的 SQL 形状 + 返回 + 冲突拒绝 + 异常吞咽兜底。
全部 FakeCursor mock(隔离确定 · 不打真实 DB · 不发任何 LINE 消息)。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401  · 先 import db 完成,避免 dal_reexports partial-init 循环
from services.line_binding import store as lb


class FakeDT:
    def isoformat(self):
        return "2026-05-29T00:00:00+00:00"


class FakeCursor:
    def __init__(self, fetchone=None, fetchone_seq=None, rowcount=0):
        self.calls = []
        self._fetchone = fetchone
        self._seq = list(fetchone_seq) if fetchone_seq is not None else None
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        if self._seq is not None:
            return self._seq.pop(0) if self._seq else None
        return self._fetchone

    @property
    def last_sql(self):
        return self.calls[-1][0] if self.calls else ""

    @property
    def last_params(self):
        return self.calls[-1][1] if self.calls else None

    def all_sql(self):
        return " ".join(c[0] for c in self.calls)


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


def patch_cursor(cur):
    cur.cm_kwargs = []

    def factory(*a, **k):
        cur.cm_kwargs.append(k)
        return _CM(cur)

    return mock.patch.object(lb.db, "get_cursor", factory)


def patch_cursor_raises(exc=RuntimeError("boom")):
    def factory(*a, **k):
        raise exc

    return mock.patch.object(lb.db, "get_cursor", factory)


class GenerateCodeTests(unittest.TestCase):
    def test_invalidates_old_and_inserts_new(self):
        cur = FakeCursor(fetchone={"code": "123456", "expires_at": FakeDT()})
        with patch_cursor(cur):
            out = lb.generate_line_binding_code("u1", ttl_minutes=5)
        self.assertEqual(out["code"], "123456")
        self.assertEqual(out["expires_at"], "2026-05-29T00:00:00+00:00")
        sql = cur.all_sql()
        self.assertIn("UPDATE line_binding_codes", sql)  # 作废旧码
        self.assertIn("INSERT INTO line_binding_codes", sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)
        # INSERT 的 code 参数是 6 位数字
        ins_params = cur.calls[-1][1]
        self.assertTrue(ins_params[0].isdigit() and len(ins_params[0]) == 6)

    def test_no_row_returns_none(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(lb.generate_line_binding_code("u1"))

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(lb.generate_line_binding_code("u1"))


class ConsumeCodeTests(unittest.TestCase):
    def test_invalid_format_returns_none_without_db(self):
        with patch_cursor_raises():
            self.assertIsNone(lb.consume_line_binding_code(""))
            self.assertIsNone(lb.consume_line_binding_code("12345"))  # 5 位
            self.assertIsNone(lb.consume_line_binding_code("abcdef"))  # 非数字

    def test_valid_code_returns_user(self):
        cur = FakeCursor(fetchone={"user_id": "u9"})
        with patch_cursor(cur):
            self.assertEqual(lb.consume_line_binding_code("654321"), "u9")
        self.assertIn("used_at IS NULL", cur.last_sql)
        self.assertIn("expires_at > NOW()", cur.last_sql)

    def test_expired_or_used_returns_none(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(lb.consume_line_binding_code("654321"))

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(lb.consume_line_binding_code("654321"))


class CreateOrUpdateTests(unittest.TestCase):
    def test_conflict_line_bound_to_other_user_rejected(self):
        cur = FakeCursor(fetchone={"user_id": "other"})  # 该 LINE 已绑别人
        with patch_cursor(cur):
            self.assertFalse(lb.create_or_update_line_binding("u1", "LINE-1"))
        # 拒绝后不应执行 upsert
        self.assertNotIn("INSERT INTO line_bindings", cur.all_sql())

    def test_happy_path_upserts(self):
        cur = FakeCursor(fetchone=None)  # 无冲突
        with patch_cursor(cur):
            self.assertTrue(lb.create_or_update_line_binding("u1", "LINE-1", "Name", "pic"))
        sql = cur.all_sql()
        self.assertIn("DELETE FROM line_bindings", sql)  # 换绑清旧
        self.assertIn("ON CONFLICT (line_user_id) DO UPDATE", sql)

    def test_same_user_rebind_allowed(self):
        cur = FakeCursor(fetchone={"user_id": "u1"})  # 同一 user → 不算冲突
        with patch_cursor(cur):
            self.assertTrue(lb.create_or_update_line_binding("u1", "LINE-1"))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(lb.create_or_update_line_binding("u1", "LINE-1"))


class GetBindingTests(unittest.TestCase):
    def test_returns_dict(self):
        cur = FakeCursor(fetchone={"line_user_id": "L1", "line_display_name": "N"})
        with patch_cursor(cur):
            out = lb.get_line_binding_by_user("u1")
        self.assertEqual(out["line_user_id"], "L1")

    def test_none(self):
        with patch_cursor(FakeCursor(fetchone=None)):
            self.assertIsNone(lb.get_line_binding_by_user("u1"))

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(lb.get_line_binding_by_user("u1"))


class GetUserByLineTests(unittest.TestCase):
    def test_updates_active_and_returns_user(self):
        # 第 1 个 fetchone = UPDATE RETURNING user_id;第 2 = SELECT users 行
        cur = FakeCursor(fetchone_seq=[{"user_id": "u5"}, {"id": "u5", "plan": "pro"}])
        with patch_cursor(cur):
            out = lb.get_user_by_line_user_id("L1")
        self.assertEqual(out["id"], "u5")
        self.assertIn("last_active_at = NOW()", cur.all_sql())

    def test_no_binding_returns_none(self):
        cur = FakeCursor(fetchone_seq=[None])  # UPDATE RETURNING 无行
        with patch_cursor(cur):
            self.assertIsNone(lb.get_user_by_line_user_id("L1"))

    def test_exception_none(self):
        with patch_cursor_raises():
            self.assertIsNone(lb.get_user_by_line_user_id("L1"))


class UnbindTests(unittest.TestCase):
    def test_deletes_returns_true(self):
        cur = FakeCursor()
        with patch_cursor(cur):
            self.assertTrue(lb.unbind_line_by_user("u1"))
        self.assertIn("DELETE FROM line_bindings", cur.last_sql)
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(lb.unbind_line_by_user("u1"))


class UnbindByLineUserIdTests(unittest.TestCase):
    def test_deletes_row_returns_true(self):
        cur = FakeCursor(rowcount=1)
        with patch_cursor(cur):
            self.assertTrue(lb.unbind_line_by_line_user_id("L1"))
        self.assertIn("DELETE FROM line_bindings", cur.last_sql)
        self.assertIn("line_user_id = %s", cur.last_sql)
        self.assertEqual(cur.last_params, ("L1",))
        self.assertEqual(cur.cm_kwargs[0].get("commit"), True)

    def test_no_binding_returns_false(self):
        cur = FakeCursor(rowcount=0)
        with patch_cursor(cur):
            self.assertFalse(lb.unbind_line_by_line_user_id("L1"))

    def test_empty_id_skips_db(self):
        with patch_cursor_raises():
            self.assertFalse(lb.unbind_line_by_line_user_id(""))

    def test_exception_false(self):
        with patch_cursor_raises():
            self.assertFalse(lb.unbind_line_by_line_user_id("L1"))


if __name__ == "__main__":
    unittest.main()
