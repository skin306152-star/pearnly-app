"""Concurrent managed heartbeat, confirm and lifecycle PostgreSQL proofs."""

import uuid
from datetime import datetime, timezone
from threading import Barrier, Thread

import psycopg2
from psycopg2.extras import RealDictCursor

from core.rls import RLS_APP_ROLE
from services.erp.legacy_generation import lock_endpoint_binding
from services.erp.shared_express_live import ManagedLiveError
from services.erp.shared_express_profile import profile_key
from tests.unit._erp_shared_express_live_pg_harness import (
    ENDPOINT,
    OWNER,
    TARGET_WORKSPACE,
    TENANT,
    WORKSPACE,
    ManagedLivePgHarness,
)
from tests.unit._pg_smoke import LOCAL_DSN


class ManagedLiveConcurrencyPgSmokeTests(ManagedLivePgHarness):
    def test_two_heartbeats_and_heartbeat_confirm_are_serialized(self):
        bodies = (
            {
                "account_set": "a",
                "account_dir": r"C:\Express\A",
                "companion_version": "1.1.64",
            },
            {
                "account_set": "b",
                "account_dir": r"C:\Express\B",
                "companion_version": "1.1.64",
            },
        )
        barrier = Barrier(2)
        results = []

        def heartbeat(body):
            barrier.wait(timeout=3)
            results.append(self._record(body))

        threads = [Thread(target=heartbeat, args=(body,)) for body in bodies]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(len(results), 2)
        self.cur.execute(
            "SELECT live_account_set,live_profile_key FROM erp_endpoints WHERE id=%s", (ENDPOINT,)
        )
        row = self.cur.fetchone()
        self.assertIn(row["live_account_set"], {"a", "b"})
        self.assertEqual(
            row["live_profile_key"],
            profile_key(row["live_account_set"], rf"C:\Express\{row['live_account_set'].upper()}"),
        )

        key_a = profile_key("a", r"C:\Express\A")
        self._insert_endpoint(live_set="a", live_key=key_a, seen=datetime.now(timezone.utc))
        barrier = Barrier(2)
        heartbeat_results = []
        confirm_results = []

        def second_heartbeat():
            barrier.wait(timeout=3)
            heartbeat_results.append(self._record(bodies[1]))

        def confirm():
            barrier.wait(timeout=3)
            confirm_results.append(self._confirm())

        threads = [Thread(target=second_heartbeat), Thread(target=confirm)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual((len(heartbeat_results), len(confirm_results)), (1, 1))
        self.cur.execute(
            "SELECT binding_generation,bound_account_set,bound_profile_key,"
            "live_account_set,live_profile_key FROM erp_endpoints WHERE id=%s",
            (ENDPOINT,),
        )
        row = self.cur.fetchone()
        self.assertEqual(row["binding_generation"], 2)
        self.assertEqual(
            row["bound_profile_key"],
            profile_key(
                row["bound_account_set"], rf"C:\Express\{row['bound_account_set'].upper()}"
            ),
        )
        self.assertEqual(
            row["live_profile_key"],
            profile_key(row["live_account_set"], rf"C:\Express\{row['live_account_set'].upper()}"),
        )

    def _lifecycle_transition(self, action):
        connection = psycopg2.connect(LOCAL_DSN, cursor_factory=RealDictCursor)
        try:
            cur = connection.cursor()
            cur.execute(f'SET search_path TO "{self.schema}", public')
            cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
            target = TARGET_WORKSPACE if action == "rebind" else ""
            settings = {
                "app.current_tenant_id": TENANT,
                "app.current_user_id": OWNER,
                "app.current_workspace_id": str(WORKSPACE),
                "app.erp_endpoint_lifecycle": "on",
                "app.erp_endpoint_lifecycle_tenant_id": TENANT,
                "app.erp_endpoint_lifecycle_actor_id": OWNER,
                "app.erp_endpoint_lifecycle_endpoint_id": ENDPOINT,
                "app.erp_endpoint_lifecycle_action": action,
                "app.erp_endpoint_lifecycle_source_workspace_id": str(WORKSPACE),
                "app.erp_endpoint_lifecycle_target_workspace_id": str(target),
                "app.erp_endpoint_lifecycle_expected_generation": "1",
                "app.erp_endpoint_lifecycle_operation_id": str(uuid.uuid4()),
            }
            for key, value in settings.items():
                cur.execute("SELECT set_config(%s,%s,true)", (key, value))
            lock_endpoint_binding(cur, ENDPOINT)
            if action == "rebind":
                cur.execute(
                    "UPDATE erp_endpoints SET workspace_client_id=%s,binding_generation=2 "
                    "WHERE id=%s",
                    (TARGET_WORKSPACE, ENDPOINT),
                )
            else:
                cur.execute(
                    "UPDATE erp_endpoints SET workspace_client_id=NULL,enabled=FALSE,"
                    "shared_scope=FALSE,revoked_at=clock_timestamp(),revoked_by=%s,"
                    "binding_generation=2,config=config-ARRAY['agent_token','agent_token_hash',"
                    "'agent_token_tail','agent_token_created_at']::text[] WHERE id=%s",
                    (OWNER, ENDPOINT),
                )
            connection.commit()
        finally:
            connection.close()

    def test_heartbeat_races_rebind_and_revoke_fail_closed(self):
        body = {
            "account_set": "test",
            "account_dir": r"C:\Express\TEST",
            "companion_version": "1.1.64",
        }
        for action in ("rebind", "revoke"):
            with self.subTest(action=action):
                self._insert_endpoint(enabled=False)
                barrier = Barrier(2)
                errors = []

                def heartbeat():
                    barrier.wait(timeout=3)
                    try:
                        self._record(body)
                    except ManagedLiveError as exc:
                        errors.append(exc.code)

                def transition():
                    barrier.wait(timeout=3)
                    self._lifecycle_transition(action)

                threads = [Thread(target=heartbeat), Thread(target=transition)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=5)
                self.assertEqual(len(errors), 1)
                self.assertIn(errors[0], {"erp.endpoint_disabled", "erp.agent_unauthorized"})
                self.cur.execute(
                    "SELECT binding_generation,workspace_client_id,revoked_at,"
                    "live_profile_key FROM erp_endpoints WHERE id=%s",
                    (ENDPOINT,),
                )
                row = self.cur.fetchone()
                self.assertEqual(row["binding_generation"], 2)
                self.assertIsNone(row["live_profile_key"])
                if action == "rebind":
                    self.assertEqual(row["workspace_client_id"], TARGET_WORKSPACE)
                else:
                    self.assertIsNotNone(row["revoked_at"])
