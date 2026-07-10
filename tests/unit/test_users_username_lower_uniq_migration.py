# -*- coding: utf-8 -*-
"""0065_users_username_lower_uniq 守门测试(静态契约 · 不连库)。

钉死:接在当前 head(0064)后、大小写不敏感唯一索引建在 lower(username)、幂等 IF NOT EXISTS、
downgrade 能 DROP。"""

import os
import re
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


class UsersUsernameLowerUniqMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mig = _read("alembic", "versions", "0065_users_username_lower_uniq.py")

    def test_revision_chain(self):
        self.assertIn('revision = "0065_users_username_lower_uniq"', self.mig)
        self.assertIn('down_revision = "0064_client_tax_profile"', self.mig)

    def test_unique_index_on_lower_username(self):
        self.assertIn("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username_lower", self.mig)
        self.assertIn("ON users (lower(username))", self.mig)

    def test_downgrade_drops_index(self):
        m = re.search(r"def downgrade\(\)[^:]*:(.*)", self.mig, re.DOTALL)
        self.assertIsNotNone(m)
        self.assertIn("DROP INDEX IF EXISTS uq_users_username_lower", m.group(1))


if __name__ == "__main__":
    unittest.main()
