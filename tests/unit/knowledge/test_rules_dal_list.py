"""list_client_rules active-filter behaviour (no DB; SQL is captured).

The settings UI must list disabled rules so they can be re-enabled, while the
engine's ruleset loader stays active-only. This pins the include_inactive switch.
"""

import unittest

from services.knowledge import rules_dal


class _FakeCursor:
    def __init__(self):
        self.sql = ""
        self.args = None

    def execute(self, sql, args=None):
        self.sql = sql
        self.args = args

    def fetchall(self):
        return []


class ListClientRulesActiveFilterTests(unittest.TestCase):
    def test_default_filters_active_only(self):
        cur = _FakeCursor()
        rules_dal.list_client_rules(cur, tenant_id="t1", accessible_ids=None)
        self.assertIn("AND is_active", cur.sql)

    def test_include_inactive_drops_active_filter(self):
        cur = _FakeCursor()
        rules_dal.list_client_rules(cur, tenant_id="t1", accessible_ids=None, include_inactive=True)
        self.assertNotIn("AND is_active", cur.sql)
        self.assertIn("WHERE tenant_id = %s", cur.sql)


if __name__ == "__main__":
    unittest.main()
