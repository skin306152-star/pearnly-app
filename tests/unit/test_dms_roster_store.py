# -*- coding: utf-8 -*-
"""dms_operator_profiles DAL 契约(波3 · DL-8)· 无 DATABASE_URL(mock db.get_cursor)。

覆盖:建用户+档案同事务(profile INSERT 带同一 uid)、update_profile 无字段即 no-op、
_with_heal 表缺失自愈重试一次。
"""

import unittest
from unittest import mock

from services.dms_roster import store


class _FakeCur:
    def __init__(self, fetchone_val=None, fetchall_val=None, rowcount=1):
        self.calls = []
        self._fetchone = fetchone_val
        self._fetchall = fetchall_val or []
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall


class _FakeCtx:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class DmsRosterStoreTest(unittest.TestCase):
    def test_update_profile_no_fields_is_noop(self):
        with mock.patch("core.db.get_cursor") as mk:
            self.assertFalse(store.update_profile("t", "u"))
            mk.assert_not_called()

    def test_update_profile_builds_scoped_set(self):
        cur = _FakeCur(rowcount=1)
        with mock.patch("core.db.get_cursor", return_value=_FakeCtx(cur)):
            self.assertTrue(store.update_profile("t1", "u1", display_name="New"))
        sql, params = cur.calls[0]
        self.assertIn("display_name = %s", sql)
        self.assertNotIn("dms_role", sql)
        self.assertEqual(params, ("New", "t1", "u1"))

    def test_create_records_inserts_user_and_profile_same_uid(self):
        cur = _FakeCur()
        with (
            mock.patch("core.db.get_cursor", return_value=_FakeCtx(cur)),
            mock.patch(
                "services.tenant.owner_users.create_member_user", return_value="op-7"
            ) as mk_cmu,
        ):
            uid = store.create_operator_records(
                tenant_id="t1",
                username="dmsop-abcd1234",
                password="secret",
                company_name="Acme",
                display_name="สมชาย",
                dms_role="sales",
            )
        self.assertEqual(uid, "op-7")
        mk_cmu.assert_called_once()
        ins = [c for c in cur.calls if "dms_operator_profiles" in c[0]]
        self.assertTrue(ins)
        self.assertEqual(ins[0][1], ("op-7", "t1", "สมชาย", "sales"))

    def test_with_heal_retries_once_on_missing_table(self):
        seq = {"n": 0}

        def fn():
            seq["n"] += 1
            if seq["n"] == 1:
                raise Exception('relation "dms_operator_profiles" does not exist')
            return "ok"

        with mock.patch.object(store, "ensure_tables") as mk_ensure:
            self.assertEqual(store._with_heal(fn), "ok")
            mk_ensure.assert_called_once()
        self.assertEqual(seq["n"], 2)


if __name__ == "__main__":
    unittest.main()
