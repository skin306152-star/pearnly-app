# -*- coding: utf-8 -*-
"""入口级 API 作用域隔离(各是各的 · Phase3)判据契约 —— 集合模型。

两层:
  1. entrance_of_code 前缀 → 允许入口【集合】(pos={pos} / tax={main,ai} /
     sales·purchase·inv·intake={main,pos} 共用 / acct·recon·kb·ar={main} / 中性 None)。
  2. deps._check 入口闸:entrance_api_scope 开时 token.entry ∉ 码入口集 → entrance_scope 拒;
     中性横切码短路放行(bootstrap 不崩);闸关零行为变化;超管/收银员不回归。

mock 掉 core.feature_flags.entrance_api_scope_enabled_for 与查库面(_cached_authz/_module_disabled),
只验判据逻辑,不碰真库(照 test_authz_deps.py 范式)。
"""

import os
import unittest
from unittest import mock

from fastapi import HTTPException

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from services.auth import entrance as entrance_mod  # noqa: E402
from services.auth.entrance import entrance_of_code  # noqa: E402
from services.authz import deps  # noqa: E402
from services.authz.registry import ALL_CODES  # noqa: E402
from services.authz.resolver import Authz  # noqa: E402


def _user(**kw):
    base = {
        "id": "u1",
        "tenant_id": "t1",
        "role": "member",
        "is_super_admin": False,
        "entry": "main",
    }
    base.update(kw)
    return base


def _scope(on: bool):
    return mock.patch("core.feature_flags.entrance_api_scope_enabled_for", return_value=on)


def _entrance_deny(user, code):
    return deps._entrance_scope_deny(user, code)


class EntranceOfCodeTests(unittest.TestCase):
    def test_pos_prefix_is_pos_only(self):
        self.assertEqual(entrance_of_code("pos.sale.operate"), frozenset({"pos"}))

    def test_tax_prefix_spans_main_and_ai(self):
        # 会计主壳报税中心 + AI SPA 工单都调 tax.* 码(2026-07-16 查证)
        self.assertEqual(entrance_of_code("tax.filing.view"), frozenset({"main", "ai"}))

    def test_shared_business_prefixes_span_main_and_pos(self):
        # POS 商户也做销售开票/盘点/收料 → 共用,两门都放行
        for code in ("sales.doc.view", "inv.view", "intake.upload"):
            self.assertEqual(entrance_of_code(code), frozenset({"main", "pos"}), code)

    def test_purchase_prefix_spans_main_pos_and_ai(self):
        # 采购/供应商数据跨会计/POS/AI 三方共用(AI 客户画像供应商档案 ai-profile.js → purchase.*)
        for code in ("purchase.doc.view", "purchase.doc.create", "purchase.supplier.manage"):
            self.assertEqual(entrance_of_code(code), frozenset({"main", "pos", "ai"}), code)

    def test_accounting_only_prefixes_are_main_only(self):
        # 做账/对账/知识库/应收 = 会计主壳专属(POS/AI 壳无这些菜单)
        for code in ("acct.entry.view", "recon.view", "kb.doc.view", "ar.view"):
            self.assertEqual(entrance_of_code(code), frozenset({"main"}), code)

    def test_cross_cutting_codes_are_neutral(self):
        for code in (
            "settings.modules.manage",
            "billing.view",
            "billing.manage",
            "team.member.view",
            "ownership.transfer",
            "audit.log.view",
            "field.cost.view",
        ):
            self.assertIsNone(entrance_of_code(code), code)

    def test_unknown_prefix_is_neutral(self):
        self.assertIsNone(entrance_of_code("made.up.code"))

    def test_no_unclassified_registry_prefix(self):
        """registry 每个权限码前缀必须落进 _ENTRANCE_BY_PREFIX(限入口)或 _NEUTRAL_PREFIXES
        (横切中性)。漏分类 → entrance_of_code 静默返 None → 该码 fail-open 不受作用域限制
        (altitude 审出的唯一软肋)。新增模块前缀漏补此处 = 测试红,不再靠人记。"""
        prefixes = {code.split(".", 1)[0] for code in ALL_CODES}
        classified = set(entrance_mod._ENTRANCE_BY_PREFIX) | entrance_mod._NEUTRAL_PREFIXES
        missing = prefixes - classified
        self.assertEqual(
            missing,
            set(),
            f"新前缀 {sorted(missing)} 未分类会 fail-open;去 services/auth/entrance.py 补进 "
            "_ENTRANCE_BY_PREFIX(限入口)或 _NEUTRAL_PREFIXES(横切中性)",
        )


class EntranceScopeDenyTests(unittest.TestCase):
    def test_gate_off_never_denies(self):
        with _scope(False):
            self.assertEqual(_entrance_deny(_user(entry="main"), "pos.sale.operate"), "")

    def test_gate_on_shared_code_allows_either_shell(self):
        # 共用码:pos-entry 打 sales.* / main-entry 打 sales.* 都放行
        with _scope(True):
            self.assertEqual(_entrance_deny(_user(entry="pos"), "sales.doc.view"), "")
            self.assertEqual(_entrance_deny(_user(entry="main"), "sales.doc.view"), "")
            self.assertEqual(_entrance_deny(_user(entry="pos"), "inv.view"), "")

    def test_gate_on_ai_entry_allowed_purchase(self):
        # AI 客户画像供应商档案(ai-profile.js → /api/purchase/supplier-profiles)走 purchase.* 码,
        # purchase 映射含 ai → ai-entry 打 purchase.* 放行(否则开闸误伤 AI 工作台)
        with _scope(True):
            self.assertEqual(_entrance_deny(_user(entry="ai"), "purchase.doc.view"), "")
            self.assertEqual(_entrance_deny(_user(entry="ai"), "purchase.supplier.manage"), "")

    def test_gate_on_accounting_code_denies_pos(self):
        # 做账/对账是会计专属:pos-entry 打 acct.*/recon.* → 拒
        with _scope(True):
            self.assertEqual(
                _entrance_deny(_user(entry="pos"), "acct.entry.view"), "entrance_scope"
            )
            self.assertEqual(_entrance_deny(_user(entry="pos"), "recon.view"), "entrance_scope")

    def test_gate_on_pos_code_denies_main(self):
        with _scope(True):
            self.assertEqual(
                _entrance_deny(_user(entry="main"), "pos.sale.operate"), "entrance_scope"
            )

    def test_gate_on_tax_spans_main_and_ai(self):
        # tax = {main, ai}:main/ai 放行,pos 拒
        with _scope(True):
            self.assertEqual(_entrance_deny(_user(entry="main"), "tax.filing.view"), "")
            self.assertEqual(_entrance_deny(_user(entry="ai"), "tax.filing.view"), "")
            self.assertEqual(
                _entrance_deny(_user(entry="pos"), "tax.filing.view"), "entrance_scope"
            )

    def test_gate_on_neutral_code_short_circuits(self):
        # 中性横切码任意 entry 都放行(否则 /api/me bootstrap 全崩)
        with _scope(True):
            self.assertEqual(_entrance_deny(_user(entry="pos"), "settings.modules.manage"), "")
            self.assertEqual(_entrance_deny(_user(entry="pos"), "billing.view"), "")
            self.assertEqual(_entrance_deny(_user(entry="main"), "team.member.view"), "")

    def test_missing_entry_treated_as_main(self):
        with _scope(True):
            u = _user()
            u.pop("entry")
            self.assertEqual(_entrance_deny(u, "acct.entry.view"), "")  # main ∈ {main}
            self.assertEqual(_entrance_deny(u, "pos.sale.operate"), "entrance_scope")


class CheckIntegrationTests(unittest.TestCase):
    """整链 _check:入口闸嵌在超管短路之后、其余码校验之前。"""

    def test_super_admin_exempt_any_entry_any_code(self):
        # 超管上游短路,连闸都不读(不 mock 也放行)
        allowed, _ = deps._check(None, _user(is_super_admin=True, entry="pos"), "acct.entry.view")
        self.assertTrue(allowed)

    def test_gate_on_main_token_denied_pos_code(self):
        with _scope(True):
            allowed, reason = deps._check(None, _user(entry="main"), "pos.sale.operate")
        self.assertFalse(allowed)
        self.assertEqual(reason, "entrance_scope")

    def test_gate_on_pos_token_denied_accounting_code(self):
        with _scope(True):
            allowed, reason = deps._check(None, _user(entry="pos"), "acct.entry.view")
        self.assertFalse(allowed)
        self.assertEqual(reason, "entrance_scope")

    def test_cashier_not_regressed(self):
        # 收银员 entry='pos' 与 pos.* 天然匹配,闸开也照过(不误伤收银台)
        with _scope(True):
            allowed, _ = deps._check(None, _user(role="cashier", entry="pos"), "pos.sale.operate")
        self.assertTrue(allowed)

    def test_gate_off_neutral_flow_unchanged(self):
        # 闸关:入口闸不介入,普通授权判定照常(现状零变化)
        granting = Authz(role_key="owner", permissions=frozenset({"acct.entry.view"}))
        with (
            _scope(False),
            mock.patch.object(deps, "_module_disabled", return_value=False),
            mock.patch.object(deps, "_cached_authz", return_value=granting),
        ):
            allowed, _ = deps._check(None, _user(entry="pos"), "acct.entry.view")
        self.assertTrue(allowed)


class RequirePermDetailTests(unittest.TestCase):
    def _detail_for(self, reason):
        request = mock.Mock()
        user = _user()
        with (
            mock.patch("core.auth.get_current_user_from_request", return_value=user),
            mock.patch.object(deps, "_check", return_value=(False, reason)),
            mock.patch.object(deps, "_deny_log"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                deps.require_perm(request, "tax.filing.view")
        self.assertEqual(ctx.exception.status_code, 403)
        return ctx.exception.detail

    def test_entrance_scope_has_machine_readable_detail(self):
        self.assertEqual(self._detail_for("entrance_scope"), "authz.entrance_scope")

    def test_existing_denial_details_stay_stable(self):
        self.assertEqual(self._detail_for("module_disabled"), "authz.module_disabled")
        self.assertEqual(self._detail_for("forbidden"), "authz.forbidden")


if __name__ == "__main__":
    unittest.main()
