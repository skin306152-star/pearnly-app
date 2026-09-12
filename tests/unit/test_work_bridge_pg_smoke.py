"""Real SQL, one-time handoff, revocation and native employee provisioning."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from core.auth import verify_password
from services.authz.resolver import resolve
from services.work_bridge import accounts, schema, sessions
from tests.unit._pg_smoke import connect_or_skip, require_disposable_db


class WorkBridgePgTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect_or_skip()
        self.schema_name = "smoke_work_bridge_" + uuid4().hex[:12]
        with self.conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA "{self.schema_name}"')
            cur.execute(f'SET search_path TO "{self.schema_name}", public')
            cur.execute("CREATE TABLE tenants (id uuid PRIMARY KEY, status text DEFAULT 'active')")
            cur.execute("""CREATE TABLE users (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid REFERENCES tenants,
                active_tenant_id uuid, username text UNIQUE, full_name text, email text,
                email_normalized text, password_hash text, password_changed_at timestamptz,
                is_active boolean DEFAULT true, is_super_admin boolean DEFAULT false,
                active_jti text, expires_at timestamptz, role text, company_name text,
                invited_by uuid, plan text
            )""")
            cur.execute("""CREATE TABLE roles (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid, key text,
                permissions jsonb DEFAULT '[]', is_active boolean DEFAULT true
            )""")
            cur.execute("""CREATE TABLE memberships (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid UNIQUE,
                tenant_id uuid, role_id uuid REFERENCES roles, status text,
                scope_mode text, granted_by uuid, granted_at timestamptz
            )""")
            cur.execute(
                "INSERT INTO roles (key, permissions) VALUES ('accountant', '[\"acct.entry.view\"]')"
            )
        self.conn.commit()
        self.db_patch = patch("core.db.get_cursor", self.cursor)
        self.env_patch = patch.dict(
            os.environ,
            {
                "WORK_BRIDGE_URL": "https://work.example.test",
                "WORK_BRIDGE_SECRET": "test-only-" + "a" * 32,
            },
        )
        self.db_patch.start()
        self.env_patch.start()
        schema.migrate_schema()
        schema.migrate_schema()

    @contextmanager
    def cursor(self, commit=False, **_kwargs):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                yield cur
                if commit:
                    self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

    def tearDown(self):
        self.db_patch.stop()
        self.env_patch.stop()
        self.conn.rollback()
        with self.conn.cursor() as cur:
            require_disposable_db(cur, self.schema_name, "smoke_work_bridge_")
            cur.execute(f'DROP SCHEMA "{self.schema_name}" CASCADE')
        self.conn.commit()
        self.conn.close()

    def user(self, personal=False):
        tenant_id = None if personal else str(uuid4())
        user_id, jti = str(uuid4()), str(uuid4())
        with self.cursor(commit=True) as cur:
            if tenant_id:
                cur.execute("INSERT INTO tenants (id) VALUES (%s)", (tenant_id,))
            cur.execute(
                "INSERT INTO users (id, tenant_id, username, active_jti, role) VALUES (%s,%s,%s,%s,'owner')",
                (user_id, tenant_id, user_id, jti),
            )
        user = {"id": user_id, "tenant_id": tenant_id}
        now = datetime.now(timezone.utc)
        claims = {
            "sub": user_id,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        return user, claims

    def handoff(self, user, claims):
        issued = sessions.issue(user, claims, "s" * 43)
        self.assertEqual(issued["consume_url"], "https://work.example.test/_pearnly/consume")
        return sessions.consume(issued["ticket"], "s" * 43)

    def test_every_firm_and_personal_account_use_the_same_service(self):
        seen = set()
        for personal in (False, False, True):
            user, claims = self.user(personal)
            result = self.handoff(user, claims)
            self.assertEqual(result["user_id"], user["id"])
            self.assertEqual(result["tenant_id"], user["tenant_id"])
            self.assertFalse(result["is_platform_admin"])
            seen.add(result["session"])
        self.assertEqual(len(seen), 3)

    def test_browser_state_expiry_and_replay(self):
        user, claims = self.user()
        ticket = sessions.issue(user, claims, "s" * 43)["ticket"]
        with self.assertRaises(HTTPException):
            sessions.consume(ticket, "wrong-state")
        result = sessions.consume(ticket, "s" * 43)
        self.assertEqual(result["user_id"], user["id"])
        with self.assertRaises(HTTPException):
            sessions.consume(ticket, "s" * 43)
        expired = sessions.issue(user, claims, "s" * 43)["ticket"]
        with self.cursor(commit=True) as cur:
            cur.execute("UPDATE work_bridge_tickets SET expires_at = now() - interval '1 second'")
        with self.assertRaises(HTTPException):
            sessions.consume(expired, "s" * 43)

    def test_logout_password_change_disabled_user_tenant_and_membership_revoke(self):
        for mutation in (
            "UPDATE users SET active_jti = NULL WHERE id = %s",
            "UPDATE users SET password_changed_at = now() + interval '2 seconds' WHERE id = %s",
            "UPDATE users SET is_active = false WHERE id = %s",
            "UPDATE tenants SET status = 'disabled' WHERE id = (SELECT tenant_id FROM users WHERE id = %s)",
            "INSERT INTO memberships (user_id, tenant_id, role_id, status) SELECT id, tenant_id, (SELECT id FROM roles LIMIT 1), 'disabled' FROM users WHERE id = %s",
        ):
            user, claims = self.user()
            result = self.handoff(user, claims)
            with self.cursor(commit=True) as cur:
                cur.execute(mutation, (user["id"],))
            with self.assertRaises(HTTPException):
                sessions.validate(result["session"])

    def test_wekan_member_has_native_employee_password_and_role_without_admin_grants(self):
        actor, _ = self.user()
        kwargs = {
            "actor_id": actor["id"],
            "request_id": "wekan-test-request-1",
            "account": "new-employee",
            "email": "employee@example.test",
            "password": "TestMember!2026",
            "display_name": "พนักงานทดสอบ",
        }
        result = accounts.create_member(**kwargs)
        self.assertEqual(accounts.create_member(**kwargs), result)
        with self.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (result["user_id"],))
            user = dict(cur.fetchone())
            self.assertTrue(verify_password(kwargs["password"], user["password_hash"]))
            self.assertFalse(user["is_super_admin"])
            self.assertEqual(user["role"], "member")
            self.assertEqual(str(user["tenant_id"]), actor["tenant_id"])
            self.assertEqual(str(user["invited_by"]), actor["id"])
            self.assertEqual(resolve(user, cur).role_key, "accountant")
        with self.assertRaises(HTTPException) as duplicate:
            accounts.create_member(
                **{**kwargs, "request_id": "different-request", "password": "Different!2026"}
            )
        self.assertEqual(duplicate.exception.status_code, 409)
        with self.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s", (result["user_id"],))
            self.assertTrue(verify_password(kwargs["password"], cur.fetchone()["password_hash"]))

    def test_enrollment_keeps_inviter_scope_and_reports_delivery_failure(self):
        actor, _ = self.user()
        other, _ = self.user()
        member = accounts.create_member(
            actor_id=actor["id"],
            request_id="enrollment-1",
            account="mail-member",
            email="mail-member@example.test",
            password=None,
            display_name="Member",
        )
        with patch(
            "routes.auth_password_routes.send_reset_link_for_employee", return_value={"ok": True}
        ) as send:
            self.assertEqual(accounts.enroll(actor["id"], member["user_id"]), {"ok": True})
            send.assert_called_once_with(member["user_id"], actor_username="WeKan")
            send.reset_mock()
            with self.assertRaises(HTTPException) as denied:
                accounts.enroll(other["id"], member["user_id"])
            self.assertEqual(denied.exception.status_code, 403)
            send.assert_not_called()
            send.return_value = {"ok": False}
            with self.assertRaises(HTTPException) as failed:
                accounts.enroll(actor["id"], member["user_id"])
            self.assertEqual(failed.exception.status_code, 503)
            send.reset_mock()
            with self.cursor(commit=True) as cur:
                cur.execute(
                    "UPDATE tenants SET status = 'disabled' WHERE id = %s", (actor["tenant_id"],)
                )
            with self.assertRaises(HTTPException):
                accounts.enroll(actor["id"], member["user_id"])
            send.assert_not_called()

    def test_database_policy_hides_other_firms_and_rejects_cross_firm_write(self):
        from psycopg2.errors import InsufficientPrivilege

        first, claims = self.user()
        second, other_claims = self.user()
        sessions.issue(first, claims, "s" * 43)
        sessions.issue(second, other_claims, "s" * 43)
        # This role exists only in this rolled-back test transaction.
        role = self.schema_name + "_reader"
        self.conn.commit()
        try:
            with self.conn.cursor() as cur:
                cur.execute(f'CREATE ROLE "{role}" NOLOGIN NOSUPERUSER NOBYPASSRLS')
                cur.execute(f'GRANT USAGE ON SCHEMA "{self.schema_name}" TO "{role}"')
                cur.execute(
                    f'GRANT SELECT, UPDATE ON ALL TABLES IN SCHEMA "{self.schema_name}" TO "{role}"'
                )
                cur.execute(f'SET LOCAL ROLE "{role}"')
                cur.execute(
                    "SELECT set_config('app.current_tenant_id', %s, true)", (first["tenant_id"],)
                )
                for table in ("work_bridge_sessions", "work_bridge_tickets"):
                    cur.execute(f"SELECT tenant_id::text FROM {table}")
                    self.assertEqual(cur.fetchall(), [(first["tenant_id"],)])
                with self.assertRaises(InsufficientPrivilege):
                    cur.execute(
                        "UPDATE work_bridge_sessions SET tenant_id = %s", (second["tenant_id"],)
                    )
        finally:
            self.conn.rollback()
