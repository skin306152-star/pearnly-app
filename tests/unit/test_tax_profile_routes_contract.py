# -*- coding: utf-8 -*-
"""税务画像/别名/义务清单路由契约(routes/tax_profile_routes.py · B2-e)。

锁定:①六端点按 path+method 注册且挂进 app;②M1 闸关时端点 404(fail-closed);
③越权/跨租户账套 → 404(不泄漏存在性);④别名污染闸(AliasError)→ 422 且机器码原样
透传给前端;⑤画像校验错(TaxProfileError)→ 422;⑥义务清单 shape:date/datetime 序列化
成 ISO 字符串,display_names 透传;⑦画像保存后触发当期义务重物化,重物化失败不挡保存。
"""

from __future__ import annotations

import unittest
from datetime import date, datetime
from unittest import mock

from fastapi import HTTPException

from core import route_helpers
from routes.tax_profile_routes import router as tax_profile_router
from services.workspace.client_alias_store import AliasError
from services.workspace.tax_profile_store import TaxProfileError


def _route_set(router):
    out = set()
    for r in router.routes:
        for m in getattr(r, "methods", set()) or set():
            if m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                out.add((m, r.path))
    return out


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        rs = _route_set(tax_profile_router)
        expected = {
            ("GET", "/api/workspace/clients/{workspace_client_id}/tax-profile"),
            ("PUT", "/api/workspace/clients/{workspace_client_id}/tax-profile"),
            ("POST", "/api/workspace/clients/{workspace_client_id}/tax-profile/confirm"),
            ("GET", "/api/workspace/clients/{workspace_client_id}/aliases"),
            ("POST", "/api/workspace/clients/{workspace_client_id}/aliases"),
            (
                "POST",
                "/api/workspace/clients/{workspace_client_id}/aliases/{alias_id}/deactivate",
            ),
            ("GET", "/api/workspace/clients/{workspace_client_id}/obligations"),
            ("GET", "/api/tax-profile/matrix"),
        }
        self.assertEqual(rs, expected)


class RouterMountedTests(unittest.TestCase):
    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/workspace/clients/{workspace_client_id}/tax-profile", paths)
        self.assertIn("/api/workspace/clients/{workspace_client_id}/obligations", paths)


class _Cur:
    """单查询假游标:ownership 检查吃 fetchone_value,主查询吃 fetchall_value。"""

    def __init__(self, fetchone_value=(1,), fetchall_value=None):
        self._fetchone = fetchone_value
        self._fetchall = fetchall_value if fetchall_value is not None else []
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class _FakeDB:
    def __init__(self, cur):
        self._cur = cur

    def get_cursor(self, commit=False):
        return _CM(self._cur)


_USER = {"id": "u1", "tenant_id": "t-1"}


def _common_patches(tr, cur):
    """闸开 + 鉴权通过 + 归属校验放行的标准四件套,四个「越权闸后走正常业务」测试类
    (PutProfileTests/AliasCreateTests/AliasDeactivateTests/ObligationListTests)共用。"""
    return (
        mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
        mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
        mock.patch.object(route_helpers, "require_perm", return_value=_USER),
        mock.patch.object(tr, "check_workspace_scope", return_value=None),
        mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
        mock.patch.object(tr, "db", _FakeDB(cur)),
    )


class GateClosedTests(unittest.IsolatedAsyncioTestCase):
    async def test_gate_closed_hides_tax_profile_as_404(self):
        from routes import tax_profile_routes as tr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.get_tax_profile(7, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_gate_closed_hides_obligations_as_404(self):
        from routes import tax_profile_routes as tr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.list_client_obligations(7, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)


class OwnershipIsolationTests(unittest.IsolatedAsyncioTestCase):
    """跨租户/不存在的账套 → 404,不泄漏存在性(照 workorder_routes 同款闸)。"""

    async def test_unowned_workspace_get_profile_404(self):
        from routes import tax_profile_routes as tr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "db", _FakeDB(_Cur(fetchone_value=None))),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.get_tax_profile(99, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "workspace.not_found")


class GetProfileTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_profile_serializes_decimal_and_datetime(self):
        from decimal import Decimal

        from routes import tax_profile_routes as tr

        profile = {
            "vat_status": "registered",
            "branch": "สำนักงานใหญ่",
            "sbt_status": "none",
            "has_employees": "unknown",
            "vat_credit_carry": Decimal("1234.56"),
            "confidence": None,
            "updated_at": datetime(2026, 7, 10, 3, 0, 0),
            "created_at": None,
        }
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(tr, "db", _FakeDB(_Cur(fetchone_value=(1,)))),
            mock.patch.object(tr.tax_profile_store, "get_profile", return_value=profile),
        ):
            out = await tr.get_tax_profile(7, mock.Mock())
        self.assertEqual(out["profile"]["vat_credit_carry"], "1234.56")
        self.assertIsInstance(out["profile"]["vat_credit_carry"], str)
        self.assertEqual(out["profile"]["updated_at"], "2026-07-10T03:00:00")
        self.assertIsNone(out["profile"]["created_at"])
        # 档案页完整度条消费(画像卡智能判断批次改口径:全 14 字段,见 matrix.py 顶注)——
        # sbt_status='none'/filing_disposition 缺省回落'active' 结构性天然算已答(2),
        # 3 个恒答字段(has_multi_branch/tax_agent_authorized/vat_credit_carry)+ 3 个
        # 条件字段父开关全未打开、隐藏视为已答(3),共 8/14。
        self.assertEqual(out["completeness"], 0.57)

    async def test_profile_not_found_404(self):
        from routes import tax_profile_routes as tr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "check_workspace_scope", return_value=None),
            mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
            mock.patch.object(tr, "db", _FakeDB(_Cur(fetchone_value=(1,)))),
            mock.patch.object(tr.tax_profile_store, "get_profile", return_value=None),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.get_tax_profile(7, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)


class PutProfileTests(unittest.IsolatedAsyncioTestCase):
    async def test_upsert_ok_triggers_obligation_regeneration(self):
        from routes import tax_profile_routes as tr

        profile = {"has_employees": "yes", "vat_credit_carry": None, "confidence": None}
        with (
            mock.patch.object(tr.tax_profile_store, "upsert_profile") as m_upsert,
            mock.patch.object(tr.tax_profile_store, "get_profile", return_value=profile),
            mock.patch.object(tr.tax_profile_store, "load_active_defs", return_value={}),
            mock.patch.object(
                tr.obligation_engine, "generate_obligations", return_value=[]
            ) as m_gen,
            mock.patch.object(tr.obligation_engine, "materialize_obligations") as m_mat,
        ):
            for p in _common_patches(tr, _Cur(fetchone_value=(1,))):
                self.enterContext(p)
            out = await tr.put_tax_profile(7, tr.TaxProfileUpdate(has_employees="yes"), mock.Mock())
        m_upsert.assert_called_once()
        self.assertEqual(m_upsert.call_args.kwargs["updated_by"], "user:u1")
        self.assertEqual(m_upsert.call_args.kwargs["has_employees"], "yes")
        m_gen.assert_called_once()
        m_mat.assert_called_once()
        self.assertEqual(out["profile"]["has_employees"], "yes")

    async def test_invalid_enum_maps_422(self):
        from routes import tax_profile_routes as tr

        with (
            mock.patch.object(
                tr.tax_profile_store,
                "upsert_profile",
                side_effect=TaxProfileError("invalid_enum_value", field="has_employees"),
            ),
        ):
            for p in _common_patches(tr, _Cur(fetchone_value=(1,))):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await tr.put_tax_profile(7, tr.TaxProfileUpdate(has_employees="maybe"), mock.Mock())
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "invalid_enum_value")

    async def test_obligation_regeneration_failure_does_not_block_save(self):
        """义务重物化是供料层,出错不该让画像保存整体失败(路由内 try/except 吞并记日志)。"""
        from routes import tax_profile_routes as tr

        profile = {"has_employees": "yes"}
        with (
            mock.patch.object(tr.tax_profile_store, "upsert_profile"),
            mock.patch.object(tr.tax_profile_store, "get_profile", return_value=profile),
            mock.patch.object(
                tr.tax_profile_store, "load_active_defs", side_effect=RuntimeError("db down")
            ),
        ):
            for p in _common_patches(tr, _Cur(fetchone_value=(1,))):
                self.enterContext(p)
            out = await tr.put_tax_profile(7, tr.TaxProfileUpdate(has_employees="yes"), mock.Mock())
        self.assertEqual(out["profile"]["has_employees"], "yes")

    async def test_added_obligations_diffs_before_and_after(self):
        """新增义务码 = 保存后物化表里多出的 obligation_code(画像卡确认后 toast 消费此值)。"""
        from routes import tax_profile_routes as tr

        profile = {"has_employees": "yes"}
        cur = _Cur(fetchone_value=(1,))
        calls = iter([[], [{"obligation_code": "pnd1"}, {"obligation_code": "sso"}]])
        cur.fetchall = lambda: next(calls)
        with (
            mock.patch.object(tr.tax_profile_store, "upsert_profile"),
            mock.patch.object(tr.tax_profile_store, "get_profile", return_value=profile),
            mock.patch.object(tr.tax_profile_store, "load_active_defs", return_value={}),
            mock.patch.object(tr.obligation_engine, "generate_obligations", return_value=[]),
            mock.patch.object(tr.obligation_engine, "materialize_obligations"),
        ):
            for p in _common_patches(tr, cur):
                self.enterContext(p)
            out = await tr.put_tax_profile(7, tr.TaxProfileUpdate(has_employees="yes"), mock.Mock())
        self.assertEqual(out["added_obligations"], ["pnd1", "sso"])


class ConfirmProfileFieldsTests(unittest.IsolatedAsyncioTestCase):
    """确认端点(画像卡智能判断批次):把 GET 里带出的推断候选转正。"""

    async def test_confirm_writes_live_proposal_and_returns_added_obligations(self):
        from routes import tax_profile_routes as tr

        profile_before = {"pays_individuals": "unknown", "field_meta": {}}
        profile_after = {"pays_individuals": "yes", "field_meta": {"pays_individuals": {}}}
        cur = _Cur(fetchone_value=(1,))
        calls = iter([[], [{"obligation_code": "pnd3"}]])
        cur.fetchall = lambda: next(calls)
        with (
            mock.patch.object(
                tr.tax_profile_store, "get_profile", side_effect=[profile_before, profile_after]
            ),
            mock.patch.object(
                tr.wht_signals,
                "scan_period_wht_signals_isolated",
                return_value={"has_any_material": True},
            ),
            mock.patch.object(
                tr.profile_inference,
                "compute_proposals",
                return_value={
                    "pays_individuals": {"value": "yes", "confidence": "high", "evidence": "e"}
                },
            ),
            mock.patch.object(tr.tax_profile_store, "confirm_field_proposals") as m_confirm,
            mock.patch.object(tr.tax_profile_store, "load_active_defs", return_value={}),
            mock.patch.object(tr.obligation_engine, "generate_obligations", return_value=[]),
            mock.patch.object(tr.obligation_engine, "materialize_obligations"),
        ):
            for p in _common_patches(tr, cur):
                self.enterContext(p)
            out = await tr.confirm_tax_profile_fields(
                7, tr.TaxProfileConfirm(fields=["pays_individuals"]), mock.Mock()
            )
        m_confirm.assert_called_once()
        self.assertEqual(
            m_confirm.call_args.kwargs["proposals"]["pays_individuals"]["value"], "yes"
        )
        self.assertEqual(out["profile"]["pays_individuals"], "yes")
        self.assertEqual(out["added_obligations"], ["pnd3"])

    async def test_stale_proposal_field_returns_409(self):
        """两次请求之间信号已经变了(候选跟不上)→ 诚实报冲突,不假装还是原来那份候选。"""
        from routes import tax_profile_routes as tr

        profile = {"pays_individuals": "unknown", "field_meta": {}}
        with (
            mock.patch.object(tr.tax_profile_store, "get_profile", return_value=profile),
            mock.patch.object(tr.wht_signals, "scan_period_wht_signals_isolated", return_value={}),
            mock.patch.object(tr.profile_inference, "compute_proposals", return_value={}),
        ):
            for p in _common_patches(tr, _Cur(fetchone_value=(1,))):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await tr.confirm_tax_profile_fields(
                    7, tr.TaxProfileConfirm(fields=["pays_individuals"]), mock.Mock()
                )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "tax_profile.proposal_stale")

    async def test_profile_not_found_404(self):
        from routes import tax_profile_routes as tr

        with mock.patch.object(tr.tax_profile_store, "get_profile", return_value=None):
            for p in _common_patches(tr, _Cur(fetchone_value=(1,))):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await tr.confirm_tax_profile_fields(
                    7, tr.TaxProfileConfirm(fields=["pays_individuals"]), mock.Mock()
                )
        self.assertEqual(ctx.exception.status_code, 404)


class AliasCreateTests(unittest.IsolatedAsyncioTestCase):
    async def test_add_alias_ok(self):
        from routes import tax_profile_routes as tr

        with mock.patch.object(tr.client_alias_store, "add_alias", return_value=42) as m_add:
            for p in _common_patches(tr, _Cur(fetchone_value=(1,))):
                self.enterContext(p)
            out = await tr.create_client_alias(
                7, tr.AliasCreate(alias_raw="Sister Makeup"), mock.Mock()
            )
        self.assertEqual(out, {"ok": True, "id": 42})
        # source 固定 human_confirmed,不接受调用方指定(方案 §4.6 闸3)。
        self.assertEqual(m_add.call_args.kwargs["source"], "human_confirmed")

    async def test_pollution_gate_error_passes_through_as_422_with_machine_code(self):
        """闸1/闸2 触发的 AliasError.code 原样透传给 detail,前端靠机器码做四语分流。"""
        from routes import tax_profile_routes as tr

        with mock.patch.object(
            tr.client_alias_store, "add_alias", side_effect=AliasError("alias.norm_conflict")
        ):
            for p in _common_patches(tr, _Cur(fetchone_value=(1,))):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await tr.create_client_alias(7, tr.AliasCreate(alias_raw="shop"), mock.Mock())
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "alias.norm_conflict")

    async def test_empty_normalized_alias_422(self):
        from routes import tax_profile_routes as tr

        with mock.patch.object(tr.client_alias_store, "add_alias", return_value=None):
            for p in _common_patches(tr, _Cur(fetchone_value=(1,))):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await tr.create_client_alias(7, tr.AliasCreate(alias_raw="***"), mock.Mock())
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "alias.empty")


class AliasDeactivateTests(unittest.IsolatedAsyncioTestCase):
    async def test_alias_not_belonging_to_client_is_404(self):
        """别名存在但归属另一客户(URL 路径与资源不一致)→ 404,不能跨客户误删。"""
        from routes import tax_profile_routes as tr

        cur = _Cur(fetchone_value=(1,))
        # 第一次 fetchone 给 ownership 检查用(账套属本租户);第二次给「别名属该客户」检查用。
        calls = iter([(1,), None])
        cur.fetchone = lambda: next(calls)
        with mock.patch.object(tr.client_alias_store, "deactivate_alias") as m_deact:
            for p in _common_patches(tr, cur):
                self.enterContext(p)
            with self.assertRaises(HTTPException) as ctx:
                await tr.deactivate_client_alias(7, 55, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        m_deact.assert_not_called()

    async def test_deactivate_ok(self):
        from routes import tax_profile_routes as tr

        cur = _Cur(fetchone_value=(1,))
        calls = iter([(1,), (1,)])
        cur.fetchone = lambda: next(calls)
        with mock.patch.object(tr.client_alias_store, "deactivate_alias", return_value=True):
            for p in _common_patches(tr, cur):
                self.enterContext(p)
            out = await tr.deactivate_client_alias(7, 55, mock.Mock())
        self.assertEqual(out, {"ok": True})


class ObligationListTests(unittest.IsolatedAsyncioTestCase):
    async def test_shape_serializes_dates_and_carries_display_names(self):
        from routes import tax_profile_routes as tr

        rows = [
            {
                "obligation_code": "pp30",
                "status": "due",
                "trigger_source": "profile",
                "due_paper": date(2569 - 543, 8, 15),
                "due_efiling": date(2569 - 543, 8, 23),
                "updated_at": datetime(2026, 7, 10, 3, 0, 0),
                "display_names": {"zh": "增值税申报(PP30)", "en": "VAT Return (PP30)"},
            }
        ]
        cur = _Cur(fetchone_value=(1,), fetchall_value=rows)
        for p in _common_patches(tr, cur):
            self.enterContext(p)
        out = await tr.list_client_obligations(7, mock.Mock(), period="2569-08")
        self.assertEqual(out["period"], "2569-08")
        row = out["obligations"][0]
        self.assertEqual(row["due_paper"], "2026-08-15")
        self.assertEqual(row["due_efiling"], "2026-08-23")
        self.assertEqual(row["updated_at"], "2026-07-10T03:00:00")
        self.assertEqual(row["display_names"]["zh"], "增值税申报(PP30)")
        # G3 顺延(MC2-B 件2):原始日照旧(上面两条断言),读侧另带顺延后的事实——
        # 2026-08-15 是周六 → 顺延至周一 08-17;2026-08-23 是周日 → 顺延至周一 08-24。
        self.assertEqual(row["due_paper_deferred"], "2026-08-17")
        self.assertEqual(row["due_efiling_deferred"], "2026-08-24")

    async def test_deferred_fields_pass_through_none_when_due_dates_absent(self):
        from routes import tax_profile_routes as tr

        rows = [
            {
                "obligation_code": "pnd1",
                "status": "tentative",
                "trigger_source": "profile_unknown",
                "due_paper": None,
                "due_efiling": None,
                "updated_at": None,
                "display_names": None,
            }
        ]
        cur = _Cur(fetchone_value=(1,), fetchall_value=rows)
        for p in _common_patches(tr, cur):
            self.enterContext(p)
        out = await tr.list_client_obligations(7, mock.Mock(), period="2569-08")
        row = out["obligations"][0]
        self.assertIsNone(row["due_paper_deferred"])
        self.assertIsNone(row["due_efiling_deferred"])

    async def test_defaults_to_current_period_when_missing(self):
        from routes import tax_profile_routes as tr

        cur = _Cur(fetchone_value=(1,), fetchall_value=[])
        for p in _common_patches(tr, cur):
            self.enterContext(p)
        out = await tr.list_client_obligations(7, mock.Mock(), period=None)
        self.assertRegex(out["period"], r"^\d{4}-\d{2}$")

    async def test_malformed_period_422(self):
        from routes import tax_profile_routes as tr

        with self.assertRaises(HTTPException) as ctx:
            with (
                mock.patch.object(
                    route_helpers, "get_current_user_from_request", return_value=_USER
                ),
                mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
                mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            ):
                await tr.list_client_obligations(7, mock.Mock(), period="not-a-period")
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "obligation.invalid_period")


class MatrixTests(unittest.IsolatedAsyncioTestCase):
    """C4 事务所矩阵聚合端点:闸群 + 单查询无 N+1 + 徽章映射 + 作用域过滤。"""

    async def test_gate_closed_404(self):
        from routes import tax_profile_routes as tr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.get_tax_profile_matrix(mock.Mock(), period=None)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "workorder.not_found")

    async def test_malformed_period_422(self):
        from routes import tax_profile_routes as tr

        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.get_tax_profile_matrix(mock.Mock(), period="not-a-period")
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "obligation.invalid_period")

    async def test_single_query_no_n_plus_one(self):
        """一次 cur.execute,零额外往返——聚合端点无 N+1 的硬证(不是代码评审断言)。"""
        from routes import tax_profile_routes as tr

        rows = [
            {
                "client_id": 1,
                "client_name": "A",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": None,
                "order_status": None,
                "display_names": {"zh": "增值税申报(PP30)"},
            },
        ]
        cur = _Cur(fetchall_value=rows)
        authz = mock.Mock(scope_mode="all", workspace_ids=None)
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(tr, "get_authz", return_value=authz),
        ):
            out = await tr.get_tax_profile_matrix(mock.Mock(), period="2569-05")
        self.assertEqual(len(cur.queries), 1)
        self.assertEqual(
            out["clients"],
            [
                {
                    "id": 1,
                    "name": "A",
                    "missing_order": True,
                    "tax_id": None,
                    # 行里没带任何 p_ 画像列(fixture 没模拟画像 JOIN)→ 全 14 字段按各自
                    # DDL 默认回落,与 profile_completeness({}) 同值(matrix.py 顶注)。
                    "profile_completeness": 0.57,
                }
            ],
        )
        self.assertEqual(out["obligation_codes"], ["pp30"])
        self.assertEqual(out["obligation_labels"]["pp30"]["zh"], "增值税申报(PP30)")
        self.assertEqual(out["cells"][0]["badge"], "pending_order")

    async def test_cell_carries_original_and_deferred_due_dates(self):
        """矩阵读侧「两个事实」:原始日照旧透传,顺延日(G3 · MC2-B 件2)另加字段,
        不覆盖原始值(存量快照/审计原样,顺延只在展示层现算)。"""
        from routes import tax_profile_routes as tr

        rows = [
            {
                "client_id": 1,
                "client_name": "A",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": date(2026, 8, 15),  # 周六
                "due_efiling": date(2026, 8, 23),  # 周日
                "work_order_id": None,
                "order_status": None,
                "display_names": {"zh": "增值税申报(PP30)"},
            },
        ]
        cur = _Cur(fetchall_value=rows)
        authz = mock.Mock(scope_mode="all", workspace_ids=None)
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(tr, "get_authz", return_value=authz),
        ):
            out = await tr.get_tax_profile_matrix(mock.Mock(), period="2569-05")
        cell = out["cells"][0]
        self.assertEqual(cell["due_paper"], "2026-08-15")
        self.assertEqual(cell["due_efiling"], "2026-08-23")
        self.assertEqual(cell["due_paper_deferred"], "2026-08-17")
        self.assertEqual(cell["due_efiling_deferred"], "2026-08-24")

    async def test_badge_mapping_covers_all_engine_states(self):
        """状态词汇全部取自 engine.STATUS_*(单一事实源)——C4-R1 教训:首版测试手打
        "archived"/"signed" 臆造词与实现自证自洽,真冻结单(status=archive)错标未评估。"""
        from services.workorder import engine, matrix
        from services.workorder.obligation_engine import STATUS_NIL

        self.assertEqual(matrix.badge(None, None), "not_evaluated")
        self.assertEqual(matrix.badge(STATUS_NIL, engine.STATUS_ARCHIVE), "no_need")
        self.assertEqual(matrix.badge("due", None), "pending_order")
        self.assertEqual(matrix.badge("due", engine.STATUS_COLLECTING), "missing_materials")
        self.assertEqual(matrix.badge("due", engine.STATUS_RUNNING), "in_progress")
        self.assertEqual(matrix.badge("due", engine.STATUS_STUCK), "pending_review")
        self.assertEqual(matrix.badge("tentative", engine.STATUS_REVIEW), "pending_review")
        self.assertEqual(matrix.badge("due", engine.STATUS_ARCHIVE), "frozen")
        self.assertEqual(matrix.badge("due", "some_future_status"), "not_evaluated")

    async def test_badge_vocabulary_drift_guard(self):
        """引擎词汇全集逐一喂给徽章映射,任何一个落 fallthrough(未评估)即红——
        引擎未来新增/改名 status 时本测试先失败,矩阵必须同步认识新词才能过。"""
        from services.workorder import engine, matrix
        from services.workorder.archive import _STATUS_ARCHIVE

        for status in engine.ALL_STATUSES:
            got = matrix.badge("due", status)
            self.assertNotEqual(
                got,
                "not_evaluated",
                f"引擎状态 {status!r} 未被矩阵徽章映射认识(词汇漂移)",
            )
        # 冻结徽章必须由归档模块真正写库的终态触发(主窗复验点:真冻结单 453b5a8c)。
        self.assertEqual(matrix.badge("due", _STATUS_ARCHIVE), "frozen")

    async def test_client_without_any_obligation_row_still_listed(self):
        """无物化记录的客户仍出现在矩阵里(LEFT JOIN 空行不吞客户),且不产生虚假列。"""
        from routes import tax_profile_routes as tr

        rows = [
            {
                "client_id": 2,
                "client_name": "B",
                "obligation_code": None,
                "obligation_status": None,
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": None,
                "order_status": None,
                "display_names": None,
            },
        ]
        cur = _Cur(fetchall_value=rows)
        authz = mock.Mock(scope_mode="all", workspace_ids=None)
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(tr, "get_authz", return_value=authz),
        ):
            out = await tr.get_tax_profile_matrix(mock.Mock(), period="2569-05")
        self.assertEqual(
            out["clients"],
            [
                {
                    "id": 2,
                    "name": "B",
                    "missing_order": True,
                    "tax_id": None,
                    # 行里没带任何 p_ 画像列(fixture 没模拟画像 JOIN)→ 全 14 字段按各自
                    # DDL 默认回落,与 profile_completeness({}) 同值(matrix.py 顶注)。
                    "profile_completeness": 0.57,
                }
            ],
        )
        self.assertEqual(out["obligation_codes"], [])
        self.assertEqual(out["cells"], [])

    async def test_assigned_scope_filters_unallowed_clients(self):
        from routes import tax_profile_routes as tr

        rows = [
            {
                "client_id": 1,
                "client_name": "A",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": None,
                "order_status": None,
                "display_names": None,
            },
            {
                "client_id": 2,
                "client_name": "B",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": None,
                "order_status": None,
                "display_names": None,
            },
        ]
        cur = _Cur(fetchall_value=rows)
        authz = mock.Mock(scope_mode="assigned", workspace_ids=frozenset({1}))
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(tr, "get_authz", return_value=authz),
        ):
            out = await tr.get_tax_profile_matrix(mock.Mock(), period="2569-05")
        self.assertEqual([c["id"] for c in out["clients"]], [1])

    async def test_missing_order_false_when_any_cell_has_work_order(self):
        from routes import tax_profile_routes as tr

        rows = [
            {
                "client_id": 1,
                "client_name": "A",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": "11111111-1111-1111-1111-111111111111",
                "order_status": "collecting",
                "display_names": None,
            },
            {
                "client_id": 1,
                "client_name": "A",
                "obligation_code": "sso",
                "obligation_status": "tentative",
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": None,
                "order_status": None,
                "display_names": None,
            },
        ]
        cur = _Cur(fetchall_value=rows)
        authz = mock.Mock(scope_mode="all", workspace_ids=None)
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(tr, "get_authz", return_value=authz),
        ):
            out = await tr.get_tax_profile_matrix(mock.Mock(), period="2569-05")
        self.assertFalse(out["clients"][0]["missing_order"])

    def test_profile_completeness_full_14_field_algorithm(self):
        """纯函数:全 14 字段口径(画像卡智能判断批次改口径,见 matrix.py 顶注三类判据)。
        EN-clients 客户目录 · 矩阵行画像列带 p_ 前缀走 prefix 参数;GET tax-profile 的
        profile dict 不带前缀。"""
        from services.workorder import matrix

        # 全空(缺全部画像列)→ 按各字段 DDL 默认回落:sbt_status='none'/
        # filing_disposition='active' 结构性天然算已答(2/8 枚举)+ 3 个恒答字段(3/3)+
        # 3 个条件字段父开关全未打开、隐藏视为已答(3/3)= 8/14。
        self.assertEqual(matrix.profile_completeness({}), 0.57)

        # 6 个真会卡在 unknown 的枚举字段全部答了 + 其余字段维持结构默认 → 满分。
        self.assertEqual(
            matrix.profile_completeness(
                {
                    "has_employees": "yes",
                    "pays_individuals": "no",
                    "pays_juristic": "no",
                    "pays_foreign": "no",
                    "pays_interest_dividend": "yes",
                    "efiling_enrolled": "yes",
                }
            ),
            1.0,
        )

        # 父开关打开却没填条件字段(branch_count 仍是结构默认值 1)→ 该项不算已答;
        # tax_agent_ref 打开且真填了偏离默认值 → 算已答。其余枚举字段维持默认
        # (sbt_status='none'/filing_disposition='active' 已答,另 6 个未答)。
        # 2(枚举)+ 3(恒答)+ 2(条件:sbt_business_type 隐藏已答 + tax_agent_ref 已答,
        # branch_count 未答)= 7/14。
        self.assertEqual(
            matrix.profile_completeness(
                {
                    "has_multi_branch": True,
                    "branch_count": 1,  # 打开了但还是默认值 1 → 未答
                    "tax_agent_authorized": True,
                    "tax_agent_ref": "REF-9",  # 打开且真填了 → 已答
                }
            ),
            0.5,
        )

        # 矩阵行(p_ 前缀)同一份字段表,取值口径不变:has_employees/pays_individuals
        # 非 unknown(2)+ sbt_status/filing_disposition 缺列回落已答(2)= 4/8 枚举
        # + 3 恒答 + 3 条件字段(父开关全缺列回落 False/'none' → 全隐藏已答)= 10/14。
        self.assertEqual(
            matrix.profile_completeness(
                {
                    "p_has_employees": "yes",
                    "p_pays_individuals": "no",
                    "p_pays_juristic": "unknown",
                    "p_pays_foreign": "unknown",
                    "p_pays_interest_dividend": "unknown",
                    "p_efiling_enrolled": "unknown",
                },
                prefix="p_",
            ),
            0.71,
        )

    async def test_client_row_carries_tax_id_and_profile_completeness(self):
        """EN-clients:客户目录复用矩阵响应——tax_id + 完整度必须挂在每个客户行上。"""
        from routes import tax_profile_routes as tr

        rows = [
            {
                "client_id": 5,
                "client_name": "C",
                "client_tax_id": "1234567890123",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": None,
                "order_status": None,
                "display_names": None,
                "p_has_employees": "yes",
                "p_pays_individuals": "yes",
                "p_pays_juristic": "yes",
                "p_pays_foreign": "unknown",
                "p_pays_interest_dividend": "unknown",
                "p_efiling_enrolled": "unknown",
            },
        ]
        cur = _Cur(fetchall_value=rows)
        authz = mock.Mock(scope_mode="all", workspace_ids=None)
        with (
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(tr, "get_authz", return_value=authz),
        ):
            out = await tr.get_tax_profile_matrix(mock.Mock(), period="2569-05")
        self.assertEqual(out["clients"][0]["tax_id"], "1234567890123")
        # 全 14 字段口径(画像卡智能判断批次):3 个枚举已答(has_employees/pays_individuals/
        # pays_juristic)+ sbt_status/filing_disposition 缺列回落已答(2)+ 3 恒答 + 3 条件
        # 字段父开关缺列回落隐藏已答 = 11/14。
        self.assertEqual(out["clients"][0]["profile_completeness"], 0.79)


if __name__ == "__main__":
    unittest.main()
