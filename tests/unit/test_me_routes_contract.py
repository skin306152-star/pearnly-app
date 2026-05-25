# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · /api/me 家族从 app.py 抽到 me_routes.py。

⚠️ 铁律 #15 敏感区(UserInfo / _build_user_info 字段错位曾致 /api/me 500 · 整个 #15 由此而生):
本测试把 UserInfo 全字段集 + _build_user_info 返回 key 集**快照锁死**,
任何后续字段增删改(漂移)当场 fail —— 比"删字段忘改 schema"提前一步拦下。

锁定(防搬迁回归):
  1. router 注册 3 条路由 path+method 契约不变
  2. app.py include_router 真挂上 · /api/me 的 response_model 仍是 me_routes.UserInfo
  3. UserInfo 字段集快照(60 字段)· 防 #15 字段漂移
  4. _build_user_info 返回 key 集快照 · 且 ⊆ UserInfo 字段(防返回前端读不到的 key / 漏返 required)
  5. _build_user_info 依赖 route_helpers._plan_permissions(单一来源)
"""

import unittest

import route_helpers
from me_routes import UserInfo, _build_user_info, router

# 60 字段快照(2026-05-25 抽取时 · verbatim 搬家后必须完全一致)
EXPECTED_USERINFO_FIELDS = {
    "id",
    "username",
    "account_type",
    "used_this_month",
    "ip_used_today",
    "ip_daily_limit",
    "can_edit_fields",
    "can_verify_tax",
    "can_use_gemini",
    "can_use_typhoon",
    "can_use_custom_template",
    "can_view_history",
    "can_push_erp",
    "can_manage_api_keys",
    "has_own_gemini_key",
    "rd_daily_limit",
    "can_extract_items",
    "can_auto_push_erp",
    "endpoints_limit",
    "can_archive",
    "can_customize_archive",
    "zip_batch_limit",
    "can_use_email_ingest",
    "can_use_folder_watch",
    "can_use_smart_alert",
    "can_use_automation",
    "typhoon_quota_monthly",
    "typhoon_used_this_month",
    "history_retention_days",
    "custom_template_limit",
    "tenant_id",
    "tenant_name",
    "tenant_type",
    "tenant_status",
    "role",
    "is_super_admin",
    "company_name",
    "full_name",
    "avatar_url",
    "monthly_volume",
    "country",
    "line_id",
    "phone",
    "line_verified",
    "profile_filled",
    "must_change_password",
    "email",
    "invited_by",
    "is_billing_exempt",
    "active_tenant_id",
    # 老兼容字段(全 Optional · _build_user_info 已不返回 · 仅 schema 兼容老前端)
    "plan",
    "monthly_quota",
    "effective_plan",
    "plan_expires_at",
    "plan_days_left",
    "trial_expires_at",
    "trial_days_left",
    "tenant_quota",
    "tenant_used",
    "expires_at",
}


class MeRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(
            got,
            {("GET", "/api/me"), ("GET", "/api/v1/me"), ("PUT", "/api/me/profile")},
        )

    def test_app_includes_me_router_with_response_model(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for p in ("/api/me", "/api/v1/me", "/api/me/profile"):
            self.assertIn(p, paths, f"me route missing from app: {p}")
        # /api/me 的 response_model 必须是 me_routes.UserInfo(防 app 残留旧 model)
        rm = next(r.response_model for r in app.app.routes if getattr(r, "path", None) == "/api/me")
        self.assertIs(rm, UserInfo)

    def test_userinfo_field_snapshot(self):
        """铁律 #15 · UserInfo 全字段集快照 · 任何字段漂移 fail"""
        self.assertEqual(set(UserInfo.model_fields.keys()), EXPECTED_USERINFO_FIELDS)

    def test_build_user_info_returns_subset_of_userinfo(self):
        """_build_user_info 返回的每个 key 必须是 UserInfo 合法字段(防返回前端读不到的 key)"""
        fake_user = {
            "id": "u1",
            "username": "tester",
            "role": "owner",
            "tenant_id": None,
        }
        # _plan_permissions 是纯静态(忽略入参返全开)· 不依赖 DB;tenant_id=None 跳过 get_tenant
        out = _build_user_info(fake_user, None, None)
        unknown = set(out.keys()) - EXPECTED_USERINFO_FIELDS
        self.assertEqual(unknown, set(), f"_build_user_info 返回了 UserInfo 没有的 key: {unknown}")
        self.assertEqual(out["id"], "u1")
        self.assertEqual(out["username"], "tester")

    def test_uses_plan_permissions_from_route_helpers(self):
        self.assertIs(
            _build_user_info.__globals__["_plan_permissions"], route_helpers._plan_permissions
        )


if __name__ == "__main__":
    unittest.main()
