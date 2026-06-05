"""rules_dal list/delete behaviour (no DB; SQL is captured).

- The settings UI lists disabled rules so they can be re-enabled, while the
  engine's ruleset loader stays active-only (include_inactive switch).
- The trash action hard-deletes (DELETE), not soft-deactivates — disabling
  without removing is the toggle path.
"""

import unittest

from services.knowledge import rules_dal


class _FakeCursor:
    def __init__(self, rowcount=1):
        self.sql = ""
        self.args = None
        self.rowcount = rowcount

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


class DeleteClientRuleTests(unittest.TestCase):
    def test_delete_is_hard_delete(self):
        cur = _FakeCursor(rowcount=1)
        gone = rules_dal.delete_client_rule(cur, tenant_id="t1", rule_id=5, accessible_ids=None)
        self.assertTrue(gone)
        self.assertIn("DELETE FROM client_rules", cur.sql)
        self.assertNotIn("is_active", cur.sql)  # not a soft-deactivate

    def test_delete_missing_returns_false(self):
        cur = _FakeCursor(rowcount=0)
        self.assertFalse(
            rules_dal.delete_client_rule(cur, tenant_id="t1", rule_id=9, accessible_ids=None)
        )


if __name__ == "__main__":
    unittest.main()
