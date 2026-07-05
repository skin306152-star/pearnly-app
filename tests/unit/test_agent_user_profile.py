# -*- coding: utf-8 -*-
"""用户画像 v1(user_profile)契约。

铁四条:① context_note 任何故障回空串(画像层不许挡对话主路);② 缓存命中不重算
(TTL 内零聚合查询);③ 新用户(零数据)回空串不加提示词噪音;④ 表不存在首用自愈。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.agent import user_profile


class TestRender(unittest.TestCase):
    def test_full_profile_lines(self):
        note = user_profile.render(
            {
                "merchants": ["Starbucks", "Makro"],
                "categories": ["เครื่องดื่ม"],
                "docs_30d": 42,
                "y_docs": 3,
                "y_total": 540.5,
                "y_queries": 2,
            }
        )
        self.assertIn("# User profile", note)
        self.assertIn("Starbucks, Makro", note)
        self.assertIn("42", note)
        self.assertIn("฿540.50", note)
        self.assertIn("asked 2", note)

    def test_empty_profile_no_noise(self):
        self.assertEqual(user_profile.render({}), "")
        self.assertEqual(user_profile.render({"merchants": [], "docs_30d": 0}), "")

    def test_partial_profile_skips_missing_lines(self):
        note = user_profile.render({"merchants": ["A"], "categories": [], "docs_30d": 5})
        self.assertIn("Frequent merchants: A", note)
        self.assertNotIn("categories", note.lower())
        self.assertNotIn("Yesterday", note)


class TestContextNote(unittest.TestCase):
    def test_cached_hit_skips_compute(self):
        cached = {"merchants": ["A"], "docs_30d": 5}
        with (
            patch.object(user_profile, "_load_cached", return_value=cached),
            patch.object(user_profile, "_compute") as compute,
        ):
            note = user_profile.context_note("u1", "t1", "U_line")
        compute.assert_not_called()
        self.assertIn("Frequent merchants: A", note)

    def test_cache_miss_returns_empty_and_refreshes_async(self):
        # 热路径不阻塞:未命中当轮回空串,把重活甩后台,不同步 _compute。
        with (
            patch.object(user_profile, "_load_cached", return_value=None),
            patch.object(user_profile, "_refresh_async") as refresh,
            patch.object(user_profile, "_compute") as compute,
        ):
            note = user_profile.context_note("u1", "t1", "U_line")
        self.assertEqual(note, "")
        refresh.assert_called_once_with("u1", "t1", "U_line")
        compute.assert_not_called()  # 当轮绝不同步算

    def test_refresh_async_computes_and_stores(self):
        # 后台刷新真算+写(线程内跑,patch Thread 成同步执行以断言)。
        fresh = {"merchants": [], "categories": [], "docs_30d": 7, "y_docs": 0, "y_total": 0.0}

        def _sync_thread(target, daemon=None):
            t = MagicMock()
            t.start = target
            return t

        with (
            patch.object(user_profile, "_compute", return_value=dict(fresh)),
            patch.object(user_profile, "_yesterday_queries", return_value=1),
            patch.object(user_profile, "_store") as store,
            patch("threading.Thread", _sync_thread),
        ):
            user_profile._refresh_async("u1", "t1", "U_line")
        store.assert_called_once()
        stored = store.call_args.args[2]
        self.assertEqual(stored["y_queries"], 1)

    def test_any_failure_returns_empty(self):
        with patch.object(user_profile, "_load_cached", side_effect=RuntimeError("db down")):
            self.assertEqual(user_profile.context_note("u1", "t1", "U_line"), "")

    def test_missing_identity_returns_empty(self):
        self.assertEqual(user_profile.context_note(None, "t1", "U"), "")
        self.assertEqual(user_profile.context_note("u1", None, "U"), "")
        self.assertEqual(user_profile.context_note("u1", "t1", None), "")

    def test_missing_table_heals(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError('relation "line_agent_profiles" does not exist')
            return None

        with patch.object(user_profile, "ensure_table") as ens:
            result = user_profile._with_heal(flaky)
        ens.assert_called_once()
        self.assertIsNone(result)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
