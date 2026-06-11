# -*- coding: utf-8 -*-
"""安全日志查询纯逻辑守门(G2 · docs/permissions/07 §五 V5):
游标编解码 / 域+筛选 WHERE 参数化 / 游标分页 next_cursor / CSV(BOM·泰文不乱码·过滤一致)。"""

import csv
import io
import unittest
from datetime import datetime, timezone
from unittest import mock

from services.team import security_log as sl


class CursorTests(unittest.TestCase):
    def test_roundtrip(self):
        cur = sl.encode_cursor("2026-06-11T03:00:00+00:00", "abc-123")
        self.assertEqual(sl.decode_cursor(cur), ("2026-06-11T03:00:00+00:00", "abc-123"))

    def test_none_and_empty(self):
        self.assertIsNone(sl.decode_cursor(None))
        self.assertIsNone(sl.decode_cursor(""))

    def test_malformed_is_none_not_raise(self):
        self.assertIsNone(sl.decode_cursor("!!!not-base64!!!"))
        self.assertIsNone(sl.decode_cursor("bm9waXBl"))  # base64 of "nopipe" — 无分隔符

    def test_opaque_no_plaintext_pipe(self):
        cur = sl.encode_cursor("2026-06-11T03:00:00+00:00", "u1")
        self.assertNotIn("|", cur)


class FilterSqlTests(unittest.TestCase):
    def test_default_scopes_all_security_domains(self):
        where, params = sl._filters("t1", None, None, None, None)
        self.assertEqual(where[0], "tenant_id = %s")
        self.assertEqual(params[0], "t1")
        self.assertIn("split_part(action, '.', 1) = ANY(%s)", where)
        self.assertIn(list(sl.SECURITY_CATEGORIES), params)

    def test_category_narrows_to_single_domain(self):
        where, params = sl._filters("t1", "role", None, None, None)
        self.assertIn("split_part(action, '.', 1) = %s", where)
        self.assertIn("role", params)

    def test_unknown_category_falls_back_to_all(self):
        # 防注入/拼写错:非白名单 category 退回全域,绝不拼进 SQL
        where, _ = sl._filters("t1", "role'; DROP", None, None, None)
        self.assertIn("split_part(action, '.', 1) = ANY(%s)", where)

    def test_actor_and_date_filters_parametrized(self):
        where, params = sl._filters("t1", None, "Boss", "2026-06-01", "2026-06-30")
        self.assertIn("LOWER(COALESCE(actor_username, '')) LIKE %s", where)
        self.assertIn("%boss%", params)
        self.assertIn("created_at >= %s", where)
        self.assertIn("created_at <= %s", where)
        self.assertIn("2026-06-01", params)
        self.assertIn("2026-06-30", params)

    def test_no_optional_clauses_when_absent(self):
        # actor=None / 空时间 → 不拼 actor/date 子句(避免空串 LIKE 误伤)
        where, _ = sl._filters("t1", None, None, None, None)
        joined = " ".join(where)
        self.assertNotIn("actor_username", joined)
        self.assertNotIn("created_at >=", joined)
        for empty in ("", None):
            w, _ = sl._filters("t1", None, empty, empty, empty)
            self.assertNotIn("actor_username", " ".join(w))


class _FakeCursor:
    """记录最后一次 execute 的 SQL/params,fetchall 回放注入的行。"""

    def __init__(self, rows):
        self._rows = rows
        self.sql = None
        self.params = None

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _row(i, created):
    return {
        "id": f"id-{i}",
        "action": "role.change",
        "actor_username": "boss",
        "target_name": "clerk",
        "details": {"k": "v"},
        "ip": "1.2.3.4",
        "created_at": created,
    }


class ListEventsPagingTests(unittest.TestCase):
    def _run(self, rows, **kw):
        fake = _FakeCursor(rows)
        with mock.patch.object(sl.db, "get_cursor", lambda *a, **k: fake):
            out = sl.list_events(tenant_id="t1", **kw)
        return out, fake

    def test_no_next_when_under_limit(self):
        now = datetime(2026, 6, 11, 3, 0, tzinfo=timezone.utc)
        out, _ = self._run([_row(0, now)], limit=50)
        self.assertEqual(len(out["events"]), 1)
        self.assertIsNone(out["next_cursor"])

    def test_next_cursor_when_over_limit(self):
        now = datetime(2026, 6, 11, 3, 0, tzinfo=timezone.utc)
        rows = [_row(i, now) for i in range(3)]  # limit+1
        out, _ = self._run(rows, limit=2)
        self.assertEqual(len(out["events"]), 2)  # 多取的一条被裁掉
        self.assertIsNotNone(out["next_cursor"])
        self.assertEqual(sl.decode_cursor(out["next_cursor"])[1], "id-1")  # 第 limit 条的 id

    def test_limit_clamped_and_fetch_plus_one(self):
        out, fake = self._run([], limit=99999)
        # 取数 = clamp 后的 limit + 1
        self.assertEqual(fake.params[-1], sl.MAX_PAGE_SIZE + 1)

    def test_cursor_appends_compound_predicate(self):
        cur = sl.encode_cursor("2026-06-11T03:00:00+00:00", "id-9")
        _, fake = self._run([], cursor=cur, limit=10)
        self.assertIn("created_at < %s OR", fake.sql)

    def test_serialize_shape(self):
        now = datetime(2026, 6, 11, 3, 0, tzinfo=timezone.utc)
        out, _ = self._run([_row(0, now)], limit=50)
        ev = out["events"][0]
        self.assertEqual(ev["actor"], "boss")
        self.assertEqual(ev["target"], "clerk")
        self.assertTrue(ev["created_at"].startswith("2026-06-11T03:00"))

    def test_db_failure_returns_empty(self):
        def _boom(*a, **k):
            raise RuntimeError("db down")

        with mock.patch.object(sl.db, "get_cursor", _boom):
            out = sl.list_events(tenant_id="t1")
        self.assertEqual(out, {"events": [], "next_cursor": None})

    def test_full_paging_no_dup_no_skip(self):
        """V5「分页不重不漏」:游标翻完全集,顺序 DESC、不重复、不漏。"""
        rows = sorted(
            (_row(i, datetime(2026, 6, 11, 3, 0, i, tzinfo=timezone.utc)) for i in range(6)),
            key=lambda r: r["created_at"],
            reverse=True,
        )

        def _slice(params):
            """模拟 SQL:按游标谓词过滤 + DESC + LIMIT(params 末位为 limit+1)。"""
            limit = params[-1]
            after = (params[-4], params[-2]) if len(params) >= 6 else None
            pool = rows
            if after:
                c_created, c_id = after
                pool = [
                    r
                    for r in rows
                    if (r["created_at"].isoformat() < c_created)
                    or (r["created_at"].isoformat() == c_created and str(r["id"]) < c_id)
                ]
            return pool[:limit]

        class _Cur:
            params = None

            def execute(self, sql, params=None):
                _Cur.params = params

            def fetchall(self):
                return _slice(_Cur.params)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        seen, cursor = [], None
        for _ in range(10):
            with mock.patch.object(sl.db, "get_cursor", lambda *a, **k: _Cur()):
                out = sl.list_events(tenant_id="t1", cursor=cursor, limit=2)
            seen += [e["id"] for e in out["events"]]
            cursor = out["next_cursor"]
            if not cursor:
                break
        self.assertEqual(seen, [f"id-{i}" for i in range(5, -1, -1)])  # 全集 DESC
        self.assertEqual(len(seen), len(set(seen)))  # 不重

    def test_same_timestamp_tiebreak_no_dup(self):
        """同一 created_at 的多行靠 id::text 破平,游标翻页不重不漏。"""
        same = datetime(2026, 6, 11, 3, 0, tzinfo=timezone.utc)
        rows = sorted(
            (_row(i, same) for i in range(4)),
            key=lambda r: str(r["id"]),
            reverse=True,
        )

        def _slice(params):
            limit = params[-1]
            after = (params[-4], params[-2]) if len(params) >= 6 else None
            pool = rows
            if after:
                c_created, c_id = after
                pool = [
                    r
                    for r in rows
                    if (r["created_at"].isoformat() < c_created)
                    or (r["created_at"].isoformat() == c_created and str(r["id"]) < c_id)
                ]
            return pool[:limit]

        class _Cur:
            params = None

            def execute(self, sql, params=None):
                _Cur.params = params

            def fetchall(self):
                return _slice(_Cur.params)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        seen, cursor = [], None
        for _ in range(10):
            with mock.patch.object(sl.db, "get_cursor", lambda *a, **k: _Cur()):
                out = sl.list_events(tenant_id="t1", cursor=cursor, limit=1)
            seen += [e["id"] for e in out["events"]]
            cursor = out["next_cursor"]
            if not cursor:
                break
        self.assertEqual(sorted(seen), [f"id-{i}" for i in range(4)])
        self.assertEqual(len(seen), len(set(seen)))


class ExportTests(unittest.TestCase):
    def test_db_failure_yields_header_only_csv(self):
        def _boom(*a, **k):
            raise RuntimeError("db down")

        with mock.patch.object(sl.db, "get_cursor", _boom):
            text = sl.export_events(tenant_id="t1")
        self.assertTrue(text.startswith("﻿"))
        lines = text.lstrip("﻿").splitlines()
        self.assertEqual(lines, ["created_at,action,actor,target,ip,details"])


class CsvTests(unittest.TestCase):
    def test_bom_prefix(self):
        text = sl.build_csv([])
        self.assertTrue(text.startswith("﻿"))

    def test_header_and_thai_not_garbled(self):
        rows = [
            {
                "action": "team.invite",
                "actor_username": "เจ้าของ",  # 泰文 owner
                "target_name": "พนักงาน",
                "ip": "1.1.1.1",
                "details": {"role_key": "clerk"},
                "created_at": datetime(2026, 6, 11, 3, 0, tzinfo=timezone.utc),
            }
        ]
        text = sl.build_csv(rows)
        parsed = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
        self.assertEqual(parsed[0], list(sl.CSV_COLUMNS))
        self.assertEqual(parsed[1][1], "team.invite")
        self.assertEqual(parsed[1][2], "เจ้าของ")
        self.assertIn("clerk", parsed[1][5])  # details JSON 含角色码

    def test_details_unicode_not_escaped(self):
        rows = [{"action": "a", "details": {"name": "ร้านค้า"}, "created_at": ""}]
        text = sl.build_csv(rows)
        self.assertIn("ร้านค้า", text)  # ensure_ascii=False

    def test_special_chars_escaped_and_column_count(self):
        # 逗号/引号/换行不破列(csv.writer 标准转义)· 每行恒 6 列
        rows = [
            {
                "action": "role.change",
                "actor_username": 'Boss, "Senior"\nline2',
                "target_name": "a,b",
                "ip": "1.1.1.1",
                "details": {"k": "v"},
                "created_at": "",
            }
        ]
        parsed = list(csv.reader(io.StringIO(sl.build_csv(rows).lstrip("﻿"))))
        self.assertEqual(len(parsed[0]), 6)
        self.assertEqual(len(parsed[1]), 6)
        self.assertEqual(parsed[1][2], 'Boss, "Senior"\nline2')

    def test_empty_details_becomes_blank(self):
        rows = [{"action": "a", "details": None, "created_at": ""}]
        parsed = list(csv.reader(io.StringIO(sl.build_csv(rows).lstrip("﻿"))))
        self.assertEqual(parsed[1][5], "")


if __name__ == "__main__":
    unittest.main()
