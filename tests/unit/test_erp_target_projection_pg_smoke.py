"""Disposable PostgreSQL proof for target projection versioning and isolation."""

from __future__ import annotations

import unittest
import uuid
from copy import deepcopy
from threading import Barrier, Thread

import psycopg2
from psycopg2.extras import RealDictCursor

from core.rls import RLS_APP_ROLE, ensure_rls_app_role
from services.erp.target_projection_contract import normalize_projection
from services.erp.mrerp_target_projection import (
    MRErpProjectionError,
    claim_endpoint_tenant_with_cursor,
)
from services.erp.target_projection_schema import TABLES, apply_target_projection_schema
from services.erp.target_projection_store import (
    load_state_with_cursor,
    publish_with_cursor,
    record_refresh_state_with_cursor,
)
from tests.unit._pg_smoke import LOCAL_DSN, connect_or_skip, require_disposable_db

TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
ENDPOINT_A = "33333333-3333-4333-8333-333333333333"
ENDPOINT_B = "44444444-4444-4444-8444-444444444444"
LEGACY_ENDPOINT = "55555555-5555-4555-8555-555555555555"
OWNER_A = "11111111-1111-4111-8111-111111111111"


def _observation(label: str = "Alpha", *, action_enabled: bool = True) -> dict:
    return {
        "adapter": "express",
        "account_set_key": "2026",
        "observed_at": "2026-09-02T09:00:00+07:00",
        "collector": {"kind": "companion", "profile_id": "profile-a"},
        "account_sets": [{"source_id": "2026", "label": "2026"}],
        "masters": {
            "products": [{"source_id": "P1", "label": label}],
            "customers": [{"source_id": "C1", "label": "Buyer"}],
        },
        "form_schema": {
            "fields": [
                {
                    "key": "product",
                    "label": "Product",
                    "type": "reference",
                    "required": True,
                    "options_source": "products",
                }
            ]
        },
        "capabilities": {
            "actions": [{"key": "purchase", "label": "Purchase", "enabled": action_enabled}]
        },
    }


class TargetProjectionPgSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = connect_or_skip()
        cls.cur = cls.conn.cursor(cursor_factory=RealDictCursor)
        cls.schema = f"smoke_projection_{uuid.uuid4().hex[:12]}"
        cls.cur.execute(f'CREATE SCHEMA "{cls.schema}"')
        cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
        cls.cur.execute(
            "CREATE TABLE tenants (id uuid PRIMARY KEY);"
            "CREATE TABLE users (id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id));"
            "CREATE TABLE erp_endpoints ("
            "id uuid PRIMARY KEY, tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,"
            "user_id uuid REFERENCES users(id), adapter text NOT NULL, "
            "enabled boolean NOT NULL DEFAULT TRUE);"
        )
        ensure_rls_app_role(cls.cur)
        apply_target_projection_schema(cls.cur)
        cls.cur.execute(f'GRANT USAGE ON SCHEMA "{cls.schema}" TO {RLS_APP_ROLE}')
        cls.cur.execute(
            f'GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA "{cls.schema}" '
            f"TO {RLS_APP_ROLE}"
        )
        for table in TABLES:
            cls.cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.conn.rollback()
            cls.cur.execute(f'SET search_path TO "{cls.schema}", public')
            require_disposable_db(cls.cur, cls.schema, "smoke_projection_")
            cls.cur.execute(f'DROP SCHEMA "{cls.schema}" CASCADE')
            cls.conn.commit()
        finally:
            cls.cur.close()
            cls.conn.close()

    def setUp(self):
        self.conn.rollback()
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        self.cur.execute(
            "TRUNCATE erp_target_projection_items, erp_target_projection_heads, "
            "erp_target_projection_snapshots, erp_endpoints, users, tenants CASCADE"
        )
        self.cur.execute("INSERT INTO tenants(id) VALUES (%s),(%s)", (TENANT_A, TENANT_B))
        self.cur.execute("INSERT INTO users(id,tenant_id) VALUES (%s,%s)", (OWNER_A, TENANT_A))
        self.cur.execute(
            "INSERT INTO erp_endpoints(id,tenant_id,adapter) VALUES "
            "(%s,%s,'express'),(%s,%s,'express')",
            (ENDPOINT_A, TENANT_A, ENDPOINT_B, TENANT_B),
        )
        self.cur.execute(
            "INSERT INTO erp_endpoints(id,user_id,adapter) VALUES (%s,%s,'mrerp')",
            (LEGACY_ENDPOINT, OWNER_A),
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.rollback()

    def _publish(self, raw: dict, tenant=TENANT_A, endpoint=ENDPOINT_A):
        return publish_with_cursor(
            self.cur,
            tenant_id=tenant,
            endpoint_id=endpoint,
            projection=normalize_projection(raw),
        )

    def test_publish_is_idempotent_and_components_advance_independently(self):
        first = self._publish(_observation())
        self.conn.commit()
        same = deepcopy(_observation())
        same["observed_at"] = "2026-09-02T10:00:00+07:00"
        second = self._publish(same)
        self.assertTrue(first["published"])
        self.assertFalse(second["published"])
        self.assertEqual(second["revision"], 1)

        expanded = _observation()
        expanded["account_sets"].append({"source_id": "2027", "label": "2027"})
        account_set_changed = self._publish(expanded)
        self.assertEqual(account_set_changed["revision"], 2)
        self.assertEqual(account_set_changed["account_sets_revision"], 2)
        self.assertEqual(account_set_changed["master_revision"], 1)

        product_input = deepcopy(expanded)
        product_input["masters"]["products"][0]["label"] = "Renamed"
        product_changed = self._publish(product_input)
        self.assertEqual(product_changed["revision"], 3)
        self.assertEqual(product_changed["master_revision"], 2)
        self.assertEqual(product_changed["capability_revision"], 1)

        field_input = deepcopy(product_input)
        field_input["form_schema"]["fields"][0]["required"] = False
        field_changed = self._publish(field_input)
        self.assertEqual(field_changed["revision"], 4)
        self.assertEqual(field_changed["form_schema_revision"], 2)
        self.assertEqual(field_changed["master_revision"], 2)

        action_input = deepcopy(field_input)
        action_input["capabilities"]["actions"][0]["enabled"] = False
        action_changed = self._publish(action_input)
        self.assertEqual(action_changed["revision"], 5)
        self.assertEqual(action_changed["master_revision"], 2)
        self.assertEqual(action_changed["capability_revision"], 2)
        state = load_state_with_cursor(
            self.cur,
            tenant_id=TENANT_A,
            endpoint_id=ENDPOINT_A,
            account_set_key="2026",
            entity_types=("products",),
        )
        self.assertEqual(state["snapshot"]["masters"]["products"][0]["label"], "Renamed")

    def test_endpoint_scope_catalog_has_independent_current_revision(self):
        endpoint_projection = _observation()
        endpoint_projection.pop("account_set_key")
        endpoint_projection["masters"] = {}
        endpoint_projection["form_schema"] = {"fields": []}
        endpoint_projection["capabilities"] = {"actions": []}
        first = self._publish(endpoint_projection)
        endpoint_projection["account_sets"].append({"source_id": "2027", "label": "2027"})
        second = self._publish(endpoint_projection)
        state = load_state_with_cursor(
            self.cur,
            tenant_id=TENANT_A,
            endpoint_id=ENDPOINT_A,
        )
        self.assertEqual((first["revision"], second["revision"]), (1, 2))
        self.assertEqual(state["scope_kind"], "endpoint")
        self.assertEqual(state["snapshot"]["account_sets_revision"], 2)
        self.assertEqual(
            [item["source_id"] for item in state["snapshot"]["account_sets"]],
            ["2026", "2027"],
        )

    def test_refresh_failure_preserves_last_successful_snapshot(self):
        self._publish(_observation())
        record_refresh_state_with_cursor(
            self.cur,
            tenant_id=TENANT_A,
            endpoint_id=ENDPOINT_A,
            account_set_key="2026",
            status="offline",
            observed_at="2026-09-02T11:00:00+07:00",
            collector={"kind": "companion", "profile_id": "profile-a"},
            error_code="erp.companion_offline",
        )
        state = load_state_with_cursor(
            self.cur,
            tenant_id=TENANT_A,
            endpoint_id=ENDPOINT_A,
            account_set_key="2026",
        )
        self.assertEqual(state["snapshot"]["revision"], 1)
        self.assertEqual(state["freshness"]["status"], "offline")
        self.assertEqual(state["freshness"]["error_code"], "erp.companion_offline")
        self.assertEqual(state["freshness"]["observed_at"].hour, 2)
        self.assertEqual(state["freshness"]["attempted_at"].hour, 4)

    def test_legacy_endpoint_can_only_be_claimed_by_owner_tenant(self):
        with self.assertRaises(MRErpProjectionError):
            claim_endpoint_tenant_with_cursor(
                self.cur, tenant_id=TENANT_B, endpoint_id=LEGACY_ENDPOINT
            )
        self.conn.rollback()
        self.cur.execute(f'SET search_path TO "{self.schema}", public')
        claim_endpoint_tenant_with_cursor(self.cur, tenant_id=TENANT_A, endpoint_id=LEGACY_ENDPOINT)
        self.cur.execute(
            "SELECT tenant_id::text AS tenant_id FROM erp_endpoints WHERE id=%s",
            (LEGACY_ENDPOINT,),
        )
        self.assertEqual(self.cur.fetchone()["tenant_id"], TENANT_A)

    def test_rls_hides_other_tenant_projection(self):
        self._publish(_observation(), TENANT_A, ENDPOINT_A)
        self._publish(_observation("Other"), TENANT_B, ENDPOINT_B)
        self.conn.commit()
        self.cur.execute(f"SET LOCAL ROLE {RLS_APP_ROLE}")
        self.cur.execute(f'SET LOCAL search_path TO "{self.schema}", public')
        self.cur.execute("SELECT set_config('app.current_tenant_id', %s, true)", (TENANT_A,))
        for table in TABLES:
            self.cur.execute(f"SELECT DISTINCT tenant_id::text AS tenant_id FROM {table}")
            self.assertEqual(
                {row["tenant_id"] for row in self.cur.fetchall()},
                {TENANT_A},
            )

    def test_concurrent_publish_serializes_monotonic_revisions(self):
        self._publish(_observation())
        self.conn.commit()
        barrier = Barrier(2)
        results: list[dict] = []
        errors: list[Exception] = []

        def publish(label: str):
            connection = psycopg2.connect(LOCAL_DSN, cursor_factory=RealDictCursor)
            try:
                cursor = connection.cursor()
                cursor.execute(f'SET search_path TO "{self.schema}", public')
                barrier.wait(timeout=3)
                results.append(
                    publish_with_cursor(
                        cursor,
                        tenant_id=TENANT_A,
                        endpoint_id=ENDPOINT_A,
                        projection=normalize_projection(_observation(label)),
                    )
                )
                connection.commit()
            except Exception as exc:
                connection.rollback()
                errors.append(exc)
            finally:
                connection.close()

        threads = [
            Thread(target=publish, args=(label,)) for label in ("Concurrent A", "Concurrent B")
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=8)
        self.assertEqual(errors, [])
        self.assertEqual({result["revision"] for result in results}, {2, 3})
        self.cur.execute(
            "SELECT current_revision FROM erp_target_projection_heads "
            "WHERE tenant_id=%s AND endpoint_id=%s",
            (TENANT_A, ENDPOINT_A),
        )
        self.assertEqual(self.cur.fetchone()["current_revision"], 3)


if __name__ == "__main__":
    unittest.main()
