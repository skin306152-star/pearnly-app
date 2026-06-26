# -*- coding: utf-8 -*-
"""B8 RLS wave3 3c · 真 archive_settings 表端到端隔离(REFACTOR-B8)。

真 ensure_archive_settings_table()(建表 + enroll apply_user_rls)+ 真 store 函数,在真 postgres
上验:archive_settings 是 per-user 命名偏好,用户 A 的设置用户 B 读不到(纯 user 维度隔离)。
CI 默认 skip,本地跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_archive_rls_real_tables -v
"""

import os
import unittest

from tests.integration._helpers import require_db

UA = "11111111-1111-1111-1111-111111111111"
UB = "22222222-2222-2222-2222-222222222222"


class ArchiveRlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls
        from services.archive import store

        cls.db, cls.s = db, store
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute("DROP TABLE IF EXISTS archive_settings CASCADE")

        store.ensure_archive_settings_table()  # 建表 + enroll apply_user_rls

        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON archive_settings TO pearnly_app")
            cur.execute("ALTER TABLE archive_settings FORCE ROW LEVEL SECURITY")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute("DROP TABLE IF EXISTS archive_settings CASCADE")

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("TRUNCATE archive_settings")

    def _seed(self):
        self.assertTrue(self.s.upsert_archive_settings(UA, [{"f": "date"}], "by_month"))
        self.assertTrue(self.s.upsert_archive_settings(UB, [{"f": "seller"}], "none"))

    def test_real_functions_read_own(self):
        self._seed()
        self.assertEqual(self.s.get_archive_settings(UA)["folder_strategy"], "by_month")
        self.assertEqual(self.s.get_archive_settings(UB)["folder_strategy"], "none")

    def test_rls_hides_other_user(self):
        self._seed()
        # 在 A 的 user 上下文下裸查全表 → policy 只放行 A 自己的行
        with self.db.get_cursor_rls(user_id=UA) as cur:
            cur.execute("SELECT count(*) n FROM archive_settings")
            self.assertEqual(cur.fetchone()["n"], 1)
        with self.db.get_cursor_rls(user_id="00000000-0000-0000-0000-0000000000ff") as cur:
            cur.execute("SELECT count(*) n FROM archive_settings")
            self.assertEqual(cur.fetchone()["n"], 0)


if __name__ == "__main__":
    unittest.main()
