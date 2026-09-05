"""Cloud startup against a disposable restored schema, including broken guards."""

from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

import psycopg2
from psycopg2.extras import RealDictCursor

from services.erp import shared_express_readiness as readiness


class CloudErpReadinessPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ.get("PEARNLY_ERP_READINESS_TEST_DSN", "")
        if not cls.dsn:
            raise unittest.SkipTest("explicit disposable restored-schema DSN required")
        parsed = urlsplit(cls.dsn)
        if parsed.hostname not in {"127.0.0.1", "localhost"} or not parsed.path.startswith(
            "/pearnly_ci_runtime_ready"
        ):
            raise RuntimeError("refusing non-disposable ERP readiness database")

    def tearDown(self):
        readiness._set_ready(False)

    def test_fresh_cloud_process_initializes_all_flags_without_ddl_or_background_loops(self):
        source = """
import asyncio
from unittest.mock import patch
from services import startup
from services.erp import shared_express_readiness as r
from services.erp.shared_express_live import record_managed_heartbeat, ManagedLiveError
checks = [r.managed.managed_foundation_ready, r.enrollment.enrollment_rls_ready,
          r.lifecycle.lifecycle_schema_ready, r.live.live_schema_ready]
assert not any(check() for check in checks)
with patch.object(startup, '_boot_schema_ddl', side_effect=AssertionError('serving DDL')), \\
     patch.object(startup.asyncio, 'create_task', side_effect=AssertionError('background loop')):
    result = asyncio.run(startup.run_startup())
assert result == {'email_task': None, 'erp_retry_task': None}
assert all(check() for check in checks)
try:
    record_managed_heartbeat('', account_set=None, account_dir=None, agent_version=None)
except ManagedLiveError as exc:
    assert exc.status == 401, exc.status
else:
    raise AssertionError('unauthenticated heartbeat accepted')
"""
        for role in ("web", "worker"):
            with self.subTest(role=role):
                result = subprocess.run(
                    [sys.executable, "-c", source],
                    cwd=Path(__file__).resolve().parents[2],
                    env={
                        **os.environ,
                        "DATABASE_URL": self.dsn,
                        "PGSSLMODE": "disable",
                        "PGOPTIONS": "-c default_transaction_read_only=on",
                        "PEARNLY_RUNTIME_ROLE": role,
                    },
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-1500:])

    def test_missing_or_disabled_security_objects_fail_closed_and_are_not_repaired(self):
        changes = (
            "ALTER TABLE erp_endpoints DISABLE ROW LEVEL SECURITY",
            "ALTER TABLE erp_endpoints DISABLE TRIGGER erp_endpoints_managed_live_columns_guard",
            "ALTER TABLE users DISABLE TRIGGER erp_endpoints_preserve_managed_creator_delete",
            "ALTER TABLE erp_endpoints DISABLE TRIGGER erp_endpoints_enrollment_columns_guard",
            "ALTER TABLE erp_endpoints DROP CONSTRAINT erp_endpoints_legacy_creator_chk",
            "ALTER TABLE erp_endpoints DROP COLUMN agent_version CASCADE",
            "DROP POLICY erp_endpoints_managed_live_confirm_select ON erp_endpoints",
            "DROP POLICY erp_endpoints_shared_express_enroll ON erp_endpoints",
            "ALTER POLICY erp_endpoints_shared_express_enroll ON erp_endpoints USING (true) WITH CHECK (true)",
            "ALTER FUNCTION public.erp_endpoint_has_legacy_activity(uuid) SET search_path = public",
            "GRANT EXECUTE ON FUNCTION public.erp_managed_live_authenticate(uuid,text) TO PUBLIC",
            "REVOKE EXECUTE ON FUNCTION public.erp_endpoint_has_legacy_activity(uuid) FROM pearnly_app",
        )
        for change in changes:
            with self.subTest(change=change), psycopg2.connect(self.dsn) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(change)
                    readiness._set_ready(True)

                    @contextmanager
                    def transaction_cursor(commit=False):
                        yield cur

                    with patch.object(readiness.db, "get_cursor", transaction_cursor):
                        with self.assertRaises((RuntimeError, psycopg2.errors.RaiseException)):
                            readiness.initialize_serving_schema()
                    self.assertFalse(readiness.managed.managed_foundation_ready())
                    self.assertFalse(readiness.enrollment.enrollment_rls_ready())
                    self.assertFalse(readiness.lifecycle.lifecycle_schema_ready())
                    self.assertFalse(readiness.live.live_schema_ready())
                    conn.rollback()


if __name__ == "__main__":
    unittest.main()
