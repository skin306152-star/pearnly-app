# -*- coding: utf-8 -*-
"""ERP 专属 /api/erp/* 入口闸契约 —— 各是各的(ERP 能力面只对 ERP 有关的门开)。

背景:ERP 路由大多只做 plan 推送闸(_check_push_access),没走 require_perm 的码级入口
作用域闸(authz.deps 按码前缀判),而 settings.org.* 是中性码、入口闸管不到 → pos/ai/dms/daily
会话凭登录状态就能调 ERP 能力面。本批在公共认证 seam 加单一可复用 fail-closed helper
(services.auth.entrance.require_erp_portal),并给每个 /api/erp/* 用户会话 handler 挂闸:

  - 拒绝:entry ∈ {pos, ai, dms, daily},且不在窄 allowlist 例外 → 403 authz.entrance_scope;
  - 放行:main / cowork / erp + 超管;entry 缺失/未知按 main 兼容;
  - 窄 allowlist(逐端点确证 · 禁用一刀切 URL 中间件):DMS 录入工作台(entry='dms')正当复用
    GET/POST/PATCH /api/erp/endpoints*、POST /api/erp/test-connection、
    POST /api/erp/endpoints/{id}/test-connection、GET /api/erp/logs(记录页)。
    非 DMS 复用面的其它端点(push / posting-preview / mrerp-xlsx-batch / mappings / bridge)
    对 dms 一律 403 —— 它们仅供 main/cowork/erp 主壳。
  - 不削弱 tenant_id / workspace_client_id / assigned scope / RLS:允许入口跨租户资源仍 404。

测试两层:
  1. require_erp_portal 单测(判据逻辑 · 不碰库)。
  2. 路由级反向测试(mock 掉 get_current_user_from_request/_check_push_access,直接跑 handler):
    POS/AI token 打代表性 ERP 端点 → 403;cowork/erp 正常;dms 只在窄 allowlist 放行;
    跨租户仍 404;超管不回归。
"""

from __future__ import annotations

import asyncio
import os
import unittest
from contextlib import ExitStack
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")
os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")

from fastapi import HTTPException  # noqa: E402

from services.auth.entrance import DMS, require_erp_portal  # noqa: E402


def _invoke(coro):
    """跑一个 async handler,返回 (kind, result):('ok', result) 或 ('http', HTTPException)。"""
    try:
        return ("ok", asyncio.run(coro))
    except HTTPException as e:
        return ("http", e)


def _user(entry=None, *, super_admin=False, tenant="t1", uid="u1", **kw):
    base = {
        "id": uid,
        "tenant_id": tenant,
        "role": "owner",
        "is_super_admin": super_admin,
        "plan": "pro",
    }
    if entry is not None:
        base["entry"] = entry
    base.update(kw)
    return base


class _AuthStack:
    """模块级鉴权 patch 栈:按需 patch get_current_user_from_request + _check_push_access。"""

    def __init__(self, module, user, *, push_gate=None):
        self._patches = [
            mock.patch.object(module, "get_current_user_from_request", return_value=user)
        ]
        if push_gate is None:
            push_gate = hasattr(module, "_check_push_access")
        if push_gate:
            self._patches.append(mock.patch.object(module, "_check_push_access", return_value=None))

    def __enter__(self):
        for p in self._patches:
            p.start()

    def __exit__(self, *exc):
        for p in reversed(self._patches):
            p.stop()


def _extras(*patches):
    stack = ExitStack()
    for p in patches:
        stack.enter_context(p)
    return stack


class RequireErpPortalTests(unittest.TestCase):
    """判据逻辑单测:拒绝集 {pos, ai, dms, daily},其余放行;超管放行;缺失 entry 按 main。"""

    def test_super_admin_passes_any_entry(self):
        user = _user("pos", super_admin=True)
        self.assertIs(require_erp_portal(user), user)

    def test_denies_pos_ai_dms_daily(self):
        for entry in ("pos", "ai", "dms", "daily"):
            user = _user(entry)
            with self.assertRaises(HTTPException) as ctx:
                require_erp_portal(user)
            self.assertEqual(ctx.exception.status_code, 403, entry)
            self.assertEqual(ctx.exception.detail, "authz.entrance_scope", entry)

    def test_allows_main_cowork_erp(self):
        for entry in ("main", "cowork", "erp"):
            user = _user(entry)
            self.assertIs(require_erp_portal(user), user)

    def test_missing_entry_treated_as_main(self):
        user = _user()
        self.assertNotIn("entry", user)
        self.assertIs(require_erp_portal(user), user)

    def test_unknown_entry_main_compatible(self):
        user = _user("weird")
        self.assertIs(require_erp_portal(user), user)

    def test_also_allowed_narrowly_unlocks_one_entry_only(self):
        dms = _user("dms")
        self.assertIs(require_erp_portal(dms, also_allowed={"dms"}), dms)
        with self.assertRaises(HTTPException):
            require_erp_portal(_user("pos"), also_allowed={"dms"})

    def test_returns_user_for_downstream_use(self):
        user = _user("erp")
        self.assertIs(require_erp_portal(user), user)


class ErpPortalRouteGuardTests(unittest.TestCase):
    """路由级反向测试:POS/AI token 打代表性 ERP 端点被 403;cowork/erp 正常;dms 窄放行。"""

    @classmethod
    def setUpClass(cls):
        from routes import (  # noqa: F401
            erp_agent,
            erp_bridge_routes,
            erp_endpoints_routes,
            erp_export_routes,
            erp_listing_routes,
            erp_mappings_routes,
            erp_posting_preview_routes,
            erp_push_log_routes,
        )

        cls.mod = {
            "agent": erp_agent,
            "bridge": erp_bridge_routes,
            "endpoints": erp_endpoints_routes,
            "export": erp_export_routes,
            "listing": erp_listing_routes,
            "mappings": erp_mappings_routes,
            "preview": erp_posting_preview_routes,
            "pushlog": erp_push_log_routes,
        }

    def _user(self, entry, **kw):
        return _user(entry, **kw)

    def _assert_denied(self, module, handler, *args, entry):
        # 所有 /api/erp/* handler 的最后一个参数都是 request → 末尾补一个 mock request。
        with _AuthStack(module, self._user(entry)):
            status, exc = _invoke(handler(*args, mock.Mock()))
        self.assertEqual(status, "http")
        self.assertEqual(exc.status_code, 403, f"{handler.__name__} {entry}")
        self.assertEqual(exc.detail, "authz.entrance_scope", f"{handler.__name__} {entry}")

    # ── 端点 CRUD 类 ─────────────────────────────────────────────────────
    def test_endpoints_list_pos_and_ai_denied(self):
        m = self.mod["endpoints"]
        self._assert_denied(m, m.erp_endpoints_list, entry="pos")
        self._assert_denied(m, m.erp_endpoints_list, entry="ai")

    def test_endpoints_create_pos_denied(self):
        m = self.mod["endpoints"]
        self._assert_denied(
            m,
            m.erp_endpoints_create,
            m.ErpEndpointCreate(name="x", adapter="mrerp", config={}),
            entry="pos",
        )

    # ── 推送/日志类 ─────────────────────────────────────────────────────
    def test_push_pos_denied(self):
        m = self.mod["pushlog"]
        self._assert_denied(m, m.erp_push, m.ErpPushRequest(history_id="h-1"), entry="pos")

    def test_logs_ai_denied(self):
        m = self.mod["pushlog"]
        self._assert_denied(m, m.erp_logs, entry="ai")

    def test_log_detail_cross_tenant_still_fail_closed(self):
        # 允许入口(cowork)· 跨租户资源(库里按 user_id+tenant_id 查不到)→ 404 不透传数据。
        m = self.mod["pushlog"]
        user = self._user("cowork")
        with (
            _AuthStack(m, user),
            _extras(
                mock.patch.object(m, "_tid", return_value="t1"),
                mock.patch.object(m.db, "get_push_log_detail", return_value=None),
            ),
        ):
            status, exc = _invoke(m.erp_log_detail("log-x", mock.Mock()))
        self.assertEqual(status, "http")
        self.assertEqual(exc.status_code, 404, exc.detail)

    # ── 映射类 ─────────────────────────────────────────────────────────
    def test_mappings_clients_pos_denied(self):
        m = self.mod["mappings"]
        self._assert_denied(m, m.erp_map_list_clients, entry="pos")

    def test_mappings_upsert_require_perm_path_ai_denied(self):
        # settings.org.* 是中性码(入口闸管不到)→ 本批的 require_erp_portal 在此兜底。
        m = self.mod["mappings"]
        user = self._user("ai")
        with _extras(
            mock.patch.object(m, "require_perm", return_value=user),
            mock.patch.object(m, "get_current_user_from_request", return_value=user),
        ):
            status, exc = _invoke(m.erp_map_upsert_client(mock.Mock()))
        self.assertEqual(status, "http")
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.detail, "authz.entrance_scope")

    # ── 连接测试类 ──────────────────────────────────────────────────────
    def test_test_connection_pos_denied(self):
        m = self.mod["listing"]
        self._assert_denied(
            m,
            m.erp_test_connection,
            m.ErpTestConnectionRequest(adapter="mrerp", config={}),
            entry="pos",
        )

    # ── 导出类(dms 非复用面 · 一律拒)───────────────────────────────
    def test_export_batch_dms_denied(self):
        # mrerp-xlsx-batch 仅供 main/cowork/erp 主壳 · dms 录入工作台不走这条 → 403。
        m = self.mod["export"]
        self._assert_denied(
            m,
            m.download_mrerp_xlsx_batch,
            m.MrerpXlsxBatchRequest(history_ids=["h-1"]),
            entry="dms",
        )

    def test_export_batch_pos_denied(self):
        m = self.mod["export"]
        self._assert_denied(
            m,
            m.download_mrerp_xlsx_batch,
            m.MrerpXlsxBatchRequest(history_ids=["h-1"]),
            entry="pos",
        )

    # ── 画像预览类(dms 非复用面 · 一律拒)───────────────────────────
    def test_posting_preview_dms_denied(self):
        m = self.mod["preview"]
        self._assert_denied(
            m,
            m.erp_posting_preview,
            m.PostingPreviewRequest(history_ids=["h-1"], endpoint_id="ep-1"),
            entry="dms",
        )

    def test_posting_preview_pos_denied(self):
        m = self.mod["preview"]
        self._assert_denied(
            m,
            m.erp_posting_preview,
            m.PostingPreviewRequest(history_ids=["h-1"], endpoint_id="ep-1"),
            entry="pos",
        )

    # ── 桥管理类(require_perm 路径)─────────────────────────────────────
    def test_bridge_mint_ai_denied(self):
        m = self.mod["bridge"]
        user = self._user("ai")
        with _extras(
            mock.patch.object(m, "bridge_enabled", return_value=True),
            mock.patch.object(m, "require_perm", return_value=user),
        ):
            status, exc = _invoke(m.erp_bridge_mint(m.MintRequest(name="bridge-a"), mock.Mock()))
        self.assertEqual(status, "http")
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.detail, "authz.entrance_scope")

    # ── Agent 密钥类 ───────────────────────────────────────────────────
    def test_agent_token_pos_denied(self):
        m = self.mod["agent"]
        with (
            mock.patch.object(m, "express_push_enabled", return_value=True),
            _AuthStack(m, self._user("pos")),
        ):
            status, exc = _invoke(m.erp_agent_token("ep-1", mock.Mock()))
        self.assertEqual(status, "http")
        self.assertEqual(exc.status_code, 403)

    # ── Express 修复卡类 ───────────────────────────────────────────────
    def test_express_account_fix_pos_denied(self):
        from routes import erp_express_account_routes as ea

        self._assert_denied(
            ea,
            ea.erp_express_account_fix,
            "log-1",
            ea.ErpExpressAccountFixRequest(accounts={}),
            entry="pos",
        )

    # ── DMS 复用面(dms 命中窄 allowlist · 放行到下一闸)───────────────
    def test_logs_dms_exception_let_through(self):
        # /dms 记录页(entry='dms')读本租户推送日志 → 窄 allowlist 放行,绝不 403 entrance_scope。
        m = self.mod["pushlog"]
        user = self._user("dms")
        with (
            _AuthStack(m, user),
            _extras(
                mock.patch.object(m, "_tid", return_value="t1"),
                mock.patch.object(m.db, "list_push_logs", return_value={"items": []}),
                mock.patch.object(m.wc, "active_workspace_for_request", return_value="c1"),
            ),
        ):
            status, res = _invoke(m.erp_logs(mock.Mock()))
        self.assertEqual(status, "ok", res if status == "http" else "")
        self.assertEqual(res, {"items": []})

    def test_test_connection_dms_exception_let_through(self):
        # DMS 录入工作台连接向导测试连接 → 闸放行 dms。用未知 adapter 让 handler 提早走
        # 400 unknown_adapter(而非 403 entrance_scope),证明它穿过了入口闸。
        m = self.mod["listing"]
        with _AuthStack(m, self._user("dms")):
            status, exc = _invoke(
                m.erp_test_connection(
                    m.ErpTestConnectionRequest(adapter="bogus-adapter", config={}), mock.Mock()
                )
            )
        self.assertEqual(status, "http")
        self.assertEqual(exc.status_code, 400, exc.detail)
        self.assertEqual(exc.detail, "erp.unknown_adapter")

    def test_endpoints_create_carries_dms_allowlist(self):
        # create 端点须把 DMS 放进 also_allowed 放行 dms(具体放行判据由 helper 单测锁)。
        m = self.mod["endpoints"]
        calls = []
        real = m.require_erp_portal

        def spy(user, *, also_allowed=None):
            calls.append(also_allowed)
            return real(user, also_allowed=also_allowed)

        with (
            mock.patch.object(m, "require_erp_portal", side_effect=spy),
            _AuthStack(m, self._user("dms")),
            _extras(
                mock.patch.object(m, "_plan_permissions", return_value={"endpoints_limit": -1}),
                mock.patch.object(m.db, "list_erp_endpoints", return_value=[]),
                mock.patch.object(m.db, "create_erp_endpoint", return_value=None),
            ),
        ):
            status, exc = _invoke(
                m.erp_endpoints_create(
                    m.ErpEndpointCreate(name="x", adapter="mrerp", config={}), mock.Mock()
                )
            )
        self.assertEqual(len(calls), 1, "create 端点应调用 require_erp_portal")
        self.assertEqual(set(calls[0] or ()), {DMS}, "create 端点应把 DMS 放进 also_allowed")
        self.assertNotEqual(getattr(exc, "detail", None), "authz.entrance_scope")

    def test_endpoints_delete_carries_dms_allowlist(self):
        m = self.mod["endpoints"]
        calls = []
        real = m.require_erp_portal

        def spy(user, *, also_allowed=None):
            calls.append(also_allowed)
            return real(user, also_allowed=also_allowed)

        with (
            mock.patch.object(m, "require_erp_portal", side_effect=spy),
            _AuthStack(m, self._user("dms")),
            _extras(mock.patch.object(m.db, "delete_erp_endpoint", return_value=True)),
        ):
            status, res = _invoke(m.erp_endpoints_delete("ep-1", mock.Mock()))
        self.assertEqual(len(calls), 1, "delete 端点应调用 require_erp_portal")
        self.assertEqual(set(calls[0] or ()), {DMS}, "delete 端点应把 DMS 放进 also_allowed")
        self.assertEqual(status, "ok")

    def test_endpoints_delete_pos_still_denied(self):
        m = self.mod["endpoints"]
        self._assert_denied(m, m.erp_endpoints_delete, "ep-1", entry="pos")

    # ── 正常入口放行 ───────────────────────────────────────────────────
    def test_endpoints_list_cowork_and_erp_normal(self):
        m = self.mod["endpoints"]
        for entry in ("cowork", "erp"):
            user = self._user(entry)
            with (
                _AuthStack(m, user),
                _extras(mock.patch.object(m.db, "list_erp_endpoints", return_value=[])),
            ):
                status, res = _invoke(m.erp_endpoints_list(mock.Mock()))
            self.assertEqual(status, "ok", entry)
            self.assertEqual(res, {"items": []}, entry)

    def test_mappings_clients_erp_normal(self):
        m = self.mod["mappings"]
        user = self._user("erp")
        with (
            _AuthStack(m, user),
            _extras(
                mock.patch.object(m.db, "get_visible_client_ids_for_user", return_value=[]),
                mock.patch.object(m.db, "list_erp_client_mappings", return_value=[{"id": 1}]),
            ),
        ):
            status, res = _invoke(m.erp_map_list_clients(mock.Mock()))
        self.assertEqual(status, "ok")
        self.assertEqual(res["count"], 1)

    def test_endpoints_list_super_admin_normal(self):
        m = self.mod["endpoints"]
        user = self._user("pos", super_admin=True)
        with (
            _AuthStack(m, user),
            _extras(mock.patch.object(m.db, "list_erp_endpoints", return_value=[])),
        ):
            status, res = _invoke(m.erp_endpoints_list(mock.Mock()))
        self.assertEqual(status, "ok")
        self.assertEqual(res, {"items": []})

    def test_logs_workspace_scope_still_applies_for_allowed_entry(self):
        # 允许入口(cowork)· assigned-scope / workspace_client_id 校验仍 fail-closed:
        # active_workspace_for_request 抛 404 authz.not_found → 原样透传,不被入口闸吞掉。
        m = self.mod["pushlog"]
        user = self._user("cowork")
        with (
            _AuthStack(m, user),
            _extras(
                mock.patch.object(m, "_tid", return_value="t1"),
                mock.patch.object(
                    m.wc,
                    "active_workspace_for_request",
                    side_effect=HTTPException(404, detail="authz.not_found"),
                ),
            ),
        ):
            status, exc = _invoke(m.erp_logs(mock.Mock()))
        self.assertEqual(status, "http")
        self.assertEqual(exc.status_code, 404, exc.detail)
        self.assertEqual(exc.detail, "authz.not_found")


if __name__ == "__main__":
    unittest.main()
