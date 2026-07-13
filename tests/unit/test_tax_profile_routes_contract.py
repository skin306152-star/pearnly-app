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
        # 档案页 0% CTA 消费的完整度(6 个默认 unknown 字段全未答 → 0.0)。
        self.assertEqual(out["completeness"], 0.0)

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
                    "profile_completeness": 0.0,
                }
            ],
        )
        self.assertEqual(out["obligation_codes"], ["pp30"])
        self.assertEqual(out["obligation_labels"]["pp30"]["zh"], "增值税申报(PP30)")
        self.assertEqual(out["cells"][0]["badge"], "pending_order")

    async def test_badge_mapping_covers_all_engine_states(self):
        """状态词汇全部取自 engine.STATUS_*(单一事实源)——C4-R1 教训:首版测试手打
        "archived"/"signed" 臆造词与实现自证自洽,真冻结单(status=archive)错标未评估。"""
        from routes import tax_profile_routes as tr
        from services.workorder import engine
        from services.workorder.obligation_engine import STATUS_NIL

        self.assertEqual(tr._matrix_badge(None, None), "not_evaluated")
        self.assertEqual(tr._matrix_badge(STATUS_NIL, engine.STATUS_ARCHIVE), "no_need")
        self.assertEqual(tr._matrix_badge("due", None), "pending_order")
        self.assertEqual(tr._matrix_badge("due", engine.STATUS_COLLECTING), "missing_materials")
        self.assertEqual(tr._matrix_badge("due", engine.STATUS_RUNNING), "in_progress")
        self.assertEqual(tr._matrix_badge("due", engine.STATUS_STUCK), "pending_review")
        self.assertEqual(tr._matrix_badge("tentative", engine.STATUS_REVIEW), "pending_review")
        self.assertEqual(tr._matrix_badge("due", engine.STATUS_ARCHIVE), "frozen")
        self.assertEqual(tr._matrix_badge("due", "some_future_status"), "not_evaluated")

    async def test_badge_vocabulary_drift_guard(self):
        """引擎词汇全集逐一喂给徽章映射,任何一个落 fallthrough(未评估)即红——
        引擎未来新增/改名 status 时本测试先失败,矩阵必须同步认识新词才能过。"""
        from routes import tax_profile_routes as tr
        from services.workorder import engine
        from services.workorder.archive import _STATUS_ARCHIVE

        for status in engine.ALL_STATUSES:
            badge = tr._matrix_badge("due", status)
            self.assertNotEqual(
                badge,
                "not_evaluated",
                f"引擎状态 {status!r} 未被矩阵徽章映射认识(词汇漂移)",
            )
        # 冻结徽章必须由归档模块真正写库的终态触发(主窗复验点:真冻结单 453b5a8c)。
        self.assertEqual(tr._matrix_badge("due", _STATUS_ARCHIVE), "frozen")

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
                    "profile_completeness": 0.0,
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

    def test_profile_completeness_counts_answered_unknown_defaultable_fields(self):
        """纯函数:6 个默认 unknown 的画像字段答了几个,0..1(EN-clients 客户目录 · 矩阵行
        画像列带 p_ 前缀走 prefix 参数;GET tax-profile 的 profile dict 不带前缀)。"""
        from routes import tax_profile_routes as tr

        self.assertEqual(tr._profile_completeness({}), 0.0)
        self.assertEqual(
            tr._profile_completeness(
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
            0.33,
        )
        self.assertEqual(
            tr._profile_completeness(
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
        self.assertEqual(out["clients"][0]["profile_completeness"], 0.5)


if __name__ == "__main__":
    unittest.main()
