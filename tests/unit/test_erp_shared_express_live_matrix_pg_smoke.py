"""Authentication, Profile and lifecycle PostgreSQL matrix for managed Express."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import mock
import uuid

from core.rls import RLS_APP_ROLE
from services.erp.express_push import agent_store
from services.erp.legacy_generation import lock_legacy_endpoint
from services.erp.shared_express_live import ManagedLiveError, record_managed_heartbeat
from services.erp.shared_express_profile import profile_key
from tests.unit._erp_shared_express_live_pg_harness import (
    CLERK,
    ENDPOINT,
    FOREIGN_WORKSPACE,
    OWNER,
    TENANT,
    TOKEN,
    WORKSPACE,
    ManagedLivePgHarness,
)


class ManagedLiveMatrixPgSmokeTests(ManagedLivePgHarness):
    def test_online_heartbeat_uses_wall_clock_after_transaction_delay(self):
        timing = {}

        @contextmanager
        def delayed_cursor(commit=False):
            with self._service_cursor(commit=commit) as cur:
                cur.execute("SELECT transaction_timestamp() AS started_at")
                timing["started_at"] = cur.fetchone()["started_at"]
                cur.execute("SELECT pg_sleep(0.15)")
                yield cur

        with (
            mock.patch("services.erp.shared_express_live.db.get_cursor", delayed_cursor),
            mock.patch("services.erp.shared_express_live.live_schema_ready", return_value=True),
        ):
            record_managed_heartbeat(
                TOKEN, account_set="test", account_dir=r"C:\Express\TEST", agent_version="1.1.64"
            )
        self.cur.execute(
            "SELECT agent_last_seen_at,clock_timestamp() AS wall_now FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        heartbeat = self.cur.fetchone()
        self.assertGreaterEqual(
            (heartbeat["agent_last_seen_at"] - timing["started_at"]).total_seconds(), 0.1
        )
        self.assertLess(
            abs((heartbeat["wall_now"] - heartbeat["agent_last_seen_at"]).total_seconds()), 2
        )

    def test_managed_auth_matrix_and_creator_independence(self):
        body = {
            "account_set": "TEST",
            "account_dir": r"C:\Express\TEST",
            "companion_version": "1.1.64",
        }
        for changes, expected in (
            ({"user_id": None}, None),
            ({"enabled": False}, ("erp.endpoint_disabled", 403)),
            (
                {
                    "revoked_at": datetime.now(timezone.utc),
                    "revoked_by": OWNER,
                    "enabled": False,
                    "shared_scope": False,
                    "workspace_id": None,
                },
                ("erp.agent_unauthorized", 401),
            ),
            ({"workspace_id": FOREIGN_WORKSPACE}, ("erp.agent_unauthorized", 401)),
            ({"generation": 0, "shared_scope": False}, ("erp.agent_unauthorized", 401)),
            (
                {"generation": 0, "shared_scope": False, "adapter": "mrerp"},
                ("erp.agent_unauthorized", 401),
            ),
        ):
            with self.subTest(changes=changes):
                self._insert_endpoint(**changes)
                if expected is None:
                    self.assertEqual(self._record(body)["profile_status"], "unbound")
                else:
                    with self.assertRaises(ManagedLiveError) as raised:
                        self._record(body)
                    self.assertEqual((raised.exception.code, raised.exception.status), expected)
        self._insert_endpoint()
        with self.assertRaises(ManagedLiveError) as wrong_secret:
            self._record(body, f"exp_{ENDPOINT}_wrong")
        self.assertEqual(wrong_secret.exception.code, "erp.agent_unauthorized")
        for status, allowed in (("warning", True), ("suspended", False), ("frozen", False)):
            with self.subTest(status=status):
                self.cur.execute("UPDATE tenants SET status=%s WHERE id=%s", (status, TENANT))
                self.conn.commit()
                if allowed:
                    self.assertTrue(self._record(body)["connected"])
                else:
                    with self.assertRaises(ManagedLiveError) as denied:
                        self._record(body)
                    self.assertEqual(denied.exception.code, "erp.agent_unauthorized")

    def test_companion_1164_states_and_offline_preserves_live_pair(self):
        body = {
            "account_set": " TEST ",
            "account_dir": r"C:\Express\TEST",
            "account_company": "Example",
            "account_set_row": 2,
            "companion_version": "1.1.64",
            "max_payload_version": 1,
            "device": {"name": "PC"},
        }
        self.assertNotIn("profile_key", body)
        self.assertNotIn("account_dir_resolved", body)
        first = self._record(body)
        second = self._record(body)
        self.assertEqual(
            (first["profile_status"], second["profile_status"]), ("unbound", "unbound")
        )
        self.cur.execute(
            "SELECT live_account_set,live_profile_key,agent_version FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        live = self.cur.fetchone()
        expected_key = profile_key("test", r"c:/express/test")
        self.assertEqual(
            (live["live_account_set"], live["live_profile_key"], live["agent_version"]),
            ("test", expected_key, "1.1.64"),
        )
        offline = self._record({"offline": True})
        self.assertEqual(
            (offline["connected"], offline["profile_status"], offline["account_set"]),
            (False, "offline", "test"),
        )
        self.cur.execute(
            "SELECT live_account_set,live_profile_key FROM erp_endpoints WHERE id=%s", (ENDPOINT,)
        )
        persisted = self.cur.fetchone()
        self.assertEqual(
            (persisted["live_account_set"], persisted["live_profile_key"]), ("test", expected_key)
        )
        invalid_profiles = (
            {"account_set": "TEST"},
            {"account_set": "TEST", "account_dir": r"C:\x\..\bad"},
        )
        for invalid in invalid_profiles:
            with self.subTest(invalid=invalid):
                self.assertEqual(self._record(invalid)["profile_status"], "needs_attention")
                self.cur.execute(
                    "SELECT live_account_set,live_profile_key FROM erp_endpoints WHERE id=%s",
                    (ENDPOINT,),
                )
                cleared = self.cur.fetchone()
                self.assertEqual(
                    (cleared["live_account_set"], cleared["live_profile_key"]), (None, None)
                )
        bound_key = profile_key("old", r"C:\Express\OLD")
        self._insert_endpoint(bound_set="old", bound_key=bound_key)
        mismatch = self._record(body)
        self.assertEqual(
            (mismatch["profile_status"], mismatch["profile_ready"]), ("mismatch", False)
        )

    def test_confirm_matrix_audit_and_rollback(self):
        now = datetime.now(timezone.utc)
        live_key = profile_key("test", r"C:\Express\TEST")
        self._insert_endpoint(live_set="test", live_key=live_key, seen=now, version="1.1.64")
        result = self._confirm()
        self.assertEqual(
            (result["generation"], result["bound_account_set"], result["profile_ready"]),
            (2, "test", True),
        )
        self.cur.execute(
            "SELECT action,details FROM operation_logs WHERE target_id=%s", (ENDPOINT,)
        )
        audit = self.cur.fetchone()
        self.assertEqual(
            (audit["action"], audit["details"]["action"], audit["details"]["reason"]),
            ("erp.endpoint.bind", "bind", "managed_live_profile_confirmed"),
        )
        self.assertTrue(audit["details"]["profile_changed"])

        for changes, expected in (
            ({"seen": now - timedelta(seconds=181)}, "erp.profile_stale"),
            ({"seen": now + timedelta(seconds=10)}, "erp.profile_stale"),
            ({"enabled": False}, "erp.endpoint_not_found"),
            (
                {
                    "revoked_at": now,
                    "revoked_by": OWNER,
                    "enabled": False,
                    "shared_scope": False,
                    "workspace_id": None,
                },
                "erp.endpoint_not_found",
            ),
        ):
            with self.subTest(changes=changes):
                self._insert_endpoint(live_set="test", live_key=live_key, **changes)
                with self.assertRaises(ManagedLiveError) as raised:
                    self._confirm()
                self.assertEqual(raised.exception.code, expected)

        self._insert_endpoint(live_set="test", live_key=live_key, seen=now)
        self.cur.execute(
            "INSERT INTO erp_push_logs VALUES (%s,%s,%s,'pending',NULL,NULL,NULL,%s)",
            (str(uuid.uuid4()), OWNER, ENDPOINT, TENANT),
        )
        self.conn.commit()
        with self.assertRaises(ManagedLiveError) as busy:
            self._confirm()
        self.assertEqual(busy.exception.code, "erp.endpoint_busy")
        self.cur.execute("DELETE FROM erp_push_logs")
        self.conn.commit()
        denials = (
            (
                SimpleNamespace(membership_id="m", role_key="clerk", has=lambda code: True),
                {"id": CLERK, "tenant_id": TENANT},
                WORKSPACE,
            ),
            (
                SimpleNamespace(membership_id="m", role_key="owner", has=lambda code: False),
                {"id": OWNER, "tenant_id": TENANT},
                WORKSPACE,
            ),
            (None, None, 202),
        )
        for authz, user, workspace in denials:
            with self.subTest(user=user, workspace=workspace):
                with self.assertRaises(ManagedLiveError) as denied:
                    self._confirm(workspace=workspace, user=user, authz=authz)
                self.assertIn(denied.exception.code, {"authz.forbidden", "erp.endpoint_not_found"})

        old_key = profile_key("old", r"C:\Express\OLD")
        self.cur.execute("TRUNCATE operation_logs")
        self.conn.commit()
        self._insert_endpoint(
            bound_set="old", bound_key=old_key, live_set="test", live_key=live_key, seen=now
        )
        switched = self._confirm()
        reconfirmed = self._confirm(generation=2)
        self.assertEqual((switched["generation"], reconfirmed["generation"]), (2, 3))
        self.cur.execute("SELECT details FROM operation_logs ORDER BY id")
        audits = [row["details"] for row in self.cur.fetchall()]
        self.assertEqual(
            [row["reason"] for row in audits],
            ["managed_live_profile_switched", "managed_live_profile_reconfirmed"],
        )
        self.assertEqual([row["profile_changed"] for row in audits], [True, False])

        self._insert_endpoint(live_set="test", live_key=live_key, seen=now)
        self.cur.execute(
            "ALTER TABLE operation_logs ADD CONSTRAINT matrix_audit_fail CHECK (FALSE) NOT VALID"
        )
        self.conn.commit()
        with self.assertRaises(Exception):
            self._confirm()
        self.cur.execute("ALTER TABLE operation_logs DROP CONSTRAINT matrix_audit_fail")
        self.cur.execute(
            "SELECT binding_generation,bound_account_set FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        rolled_back = self.cur.fetchone()
        self.assertEqual(
            (rolled_back["binding_generation"], rolled_back["bound_account_set"]), (1, None)
        )
        self.conn.commit()

    def test_schema_acl_mixed_write_gen0_and_legacy_lane(self):
        self.cur.execute(
            "SELECT p.prosecdef,p.proconfig,has_function_privilege('public',p.oid,'EXECUTE') AS public_exec,"
            "has_function_privilege(%s,p.oid,'EXECUTE') AS app_exec FROM pg_proc p "
            "JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=%s "
            "AND p.proname='erp_managed_live_authenticate'",
            (RLS_APP_ROLE, self.schema),
        )
        contract = self.cur.fetchone()
        self.assertEqual(
            (
                contract["prosecdef"],
                contract["proconfig"],
                contract["public_exec"],
                contract["app_exec"],
            ),
            (True, ["search_path=pg_catalog"], False, True),
        )
        self.cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        settings = (
            ("app.current_tenant_id", TENANT),
            ("app.current_workspace_id", WORKSPACE),
            ("app.erp_managed_live_heartbeat", "on"),
            ("app.erp_managed_live_tenant_id", TENANT),
            ("app.erp_managed_live_endpoint_id", ENDPOINT),
            ("app.erp_managed_live_generation", "1"),
        )
        for key, value in settings:
            self.cur.execute("SELECT set_config(%s,%s,true)", (key, str(value)))
        with self.assertRaises(Exception):
            self.cur.execute(
                "UPDATE erp_endpoints SET live_account_set='x',live_profile_key='v1:x',"
                "bound_account_set='x',bound_profile_key='v1:x',enabled=FALSE WHERE id=%s",
                (ENDPOINT,),
            )
        self.conn.rollback()
        self._insert_endpoint(generation=0, shared_scope=False)
        with mock.patch("core.db.get_cursor", side_effect=self._service_cursor):
            self.assertIsNotNone(agent_store.authenticate(TOKEN))
        self.assertTrue(lock_legacy_endpoint(self.cur, ENDPOINT))
        self.cur.execute(
            "UPDATE erp_endpoints SET live_account_set='legacy',live_profile_key='v1:legacy' "
            "WHERE id=%s",
            (ENDPOINT,),
        )
        self.assertEqual(self.cur.rowcount, 1)
        self.conn.rollback()
        self._insert_endpoint()
        with mock.patch("core.db.get_cursor", side_effect=self._service_cursor):
            self.assertIsNone(agent_store.authenticate(TOKEN))
        self.assertFalse(lock_legacy_endpoint(self.cur, ENDPOINT))
