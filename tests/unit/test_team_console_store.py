# -*- coding: utf-8 -*-
"""成员管理边界守门:自锁 / owner 不可动 / 角色白名单 / 作用域约束(批3)。

mock 掉 get_member 与游标,只验集中在 console_store 的拒绝逻辑。
"""

import unittest
from unittest import mock

from services.team import console_store, ownership


class ChangeRoleGuardTests(unittest.TestCase):
    def test_cannot_modify_self(self):
        out = console_store.change_role(
            tenant_id="t", actor_id="u1", target_user_id="u1", role_key="viewer"
        )
        self.assertEqual(out["error"], "team.cannot_modify_self")

    def test_owner_role_not_assignable(self):
        out = console_store.change_role(
            tenant_id="t", actor_id="u1", target_user_id="u2", role_key="owner"
        )
        self.assertEqual(out["error"], "team.role_not_assignable")

    def test_cashier_role_not_assignable(self):
        out = console_store.change_role(
            tenant_id="t", actor_id="u1", target_user_id="u2", role_key="cashier"
        )
        self.assertEqual(out["error"], "team.role_not_assignable")

    def test_target_owner_blocked(self):
        member = {"membership_id": "m1", "role_key": "owner", "username": "boss"}
        with mock.patch.object(console_store, "get_member", return_value=member):
            out = console_store.change_role(
                tenant_id="t", actor_id="u1", target_user_id="u2", role_key="viewer"
            )
        self.assertEqual(out["error"], "team.target_is_owner")

    def test_member_not_found(self):
        with mock.patch.object(console_store, "get_member", return_value=None):
            out = console_store.change_role(
                tenant_id="t", actor_id="u1", target_user_id="u2", role_key="viewer"
            )
        self.assertEqual(out["error"], "team.member_not_found")


class SetScopeGuardTests(unittest.TestCase):
    def test_cannot_modify_self(self):
        out = console_store.set_scope(
            tenant_id="t", actor_id="u1", target_user_id="u1", scope_mode="all", workspace_ids=[]
        )
        self.assertEqual(out["error"], "team.cannot_modify_self")

    def test_admin_cannot_be_assigned(self):
        member = {"membership_id": "m1", "role_key": "admin", "username": "a"}
        with mock.patch.object(console_store, "get_member", return_value=member):
            out = console_store.set_scope(
                tenant_id="t",
                actor_id="u1",
                target_user_id="u2",
                scope_mode="assigned",
                workspace_ids=[1],
            )
        self.assertEqual(out["error"], "team.scope_not_allowed")

    def test_target_owner_blocked(self):
        member = {"membership_id": "m1", "role_key": "owner", "username": "boss"}
        with mock.patch.object(console_store, "get_member", return_value=member):
            out = console_store.set_scope(
                tenant_id="t",
                actor_id="u1",
                target_user_id="u2",
                scope_mode="all",
                workspace_ids=[],
            )
        self.assertEqual(out["error"], "team.target_is_owner")


class MemberActionGuardTests(unittest.TestCase):
    def test_self_blocked(self):
        self.assertEqual(
            console_store.guard_member_action("t", "u1", "u1"), "team.cannot_modify_self"
        )

    def test_owner_blocked(self):
        member = {"membership_id": "m1", "role_key": "owner", "username": "boss"}
        with mock.patch.object(console_store, "get_member", return_value=member):
            self.assertEqual(
                console_store.guard_member_action("t", "u1", "u2"), "team.target_is_owner"
            )

    def test_normal_member_allowed(self):
        member = {"membership_id": "m1", "role_key": "clerk", "username": "c"}
        with mock.patch.object(console_store, "get_member", return_value=member):
            self.assertIsNone(console_store.guard_member_action("t", "u1", "u2"))


class OwnershipGuardTests(unittest.TestCase):
    def test_transfer_to_self_rejected(self):
        out = ownership.initiate(tenant_id="t", from_user_id="u1", to_user_id="u1")
        self.assertEqual(out["error"], "transfer.self")

    def test_target_must_be_admin(self):
        member = {"membership_id": "m1", "role_key": "accountant", "username": "a"}
        with mock.patch("services.team.console_store.get_member", return_value=member):
            out = ownership.initiate(tenant_id="t", from_user_id="u1", to_user_id="u2")
        self.assertEqual(out["error"], "transfer.target_not_admin")
