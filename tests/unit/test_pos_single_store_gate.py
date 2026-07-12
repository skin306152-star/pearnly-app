# -*- coding: utf-8 -*-
"""POS 一号一店闸(Zihao 2026-07-12 拍板)防回潮钉。

需求:一个 pos_only 账号只能有 1 个套账(店),仅在首次开通/首个套账时能建,之后
禁止新增。闸只对 business_type=='pos_only' 生效,firm/其它业态零影响(会计站核心
功能不容有失)。见 routes/workspace_routes.py::_pos_single_store_blocked +
create_workspace_client。

行为级验证(不起真库):假游标喂 get_business_type/count(*) 两种输入,直接断言
_pos_single_store_blocked 的返回值——比纯 grep 源码更硬,能证明"firm 即便已有 N 个
套账也绝不触发 count 查询"这条隔离边界。另附源码/i18n/前端三处静态钉,照
test_business_picker_removed.py 范式。
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


class _FakeCursor:
    """假游标:记录 execute 调用 + 回放固定 fetchone 结果(count(*) 查询用)。"""

    def __init__(self, count: int):
        self.count = count
        self.executed: list = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return {"n": self.count}


class _FakeCursorCtx:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor

    def __enter__(self):
        return self._cursor

    def __exit__(self, *exc):
        return False


class PosSingleStoreBlockedBehaviorTests(unittest.TestCase):
    """_pos_single_store_blocked 纯函数行为(假游标,不连真库)。"""

    def test_pos_only_with_existing_store_blocks(self):
        from routes import workspace_routes as wr

        fake_cur = _FakeCursor(count=1)
        with (
            mock.patch.object(wr.db, "get_cursor_rls", return_value=_FakeCursorCtx(fake_cur)),
            mock.patch.object(wr, "get_business_type", return_value="pos_only"),
        ):
            self.assertTrue(wr._pos_single_store_blocked("tenant-1"))

    def test_pos_only_with_zero_stores_allows_first(self):
        """首个套账(count==0)必须放行——闸只挡"再建",不挡首次开通。"""
        from routes import workspace_routes as wr

        fake_cur = _FakeCursor(count=0)
        with (
            mock.patch.object(wr.db, "get_cursor_rls", return_value=_FakeCursorCtx(fake_cur)),
            mock.patch.object(wr, "get_business_type", return_value="pos_only"),
        ):
            self.assertFalse(wr._pos_single_store_blocked("tenant-1"))

    def test_firm_business_type_never_blocked_regardless_of_store_count(self):
        """隔离铁证:business_type='firm' 时即便该租户已有 99 个套账也绝不阻拦——
        count(*) 查询压根不会被触发(firm 走不进 pos_only 分支,零影响)。"""
        from routes import workspace_routes as wr

        fake_cur = _FakeCursor(count=99)
        with (
            mock.patch.object(wr.db, "get_cursor_rls", return_value=_FakeCursorCtx(fake_cur)),
            mock.patch.object(wr, "get_business_type", return_value="firm"),
        ):
            self.assertFalse(wr._pos_single_store_blocked("tenant-1"))
        self.assertEqual(fake_cur.executed, [], "firm 业态不该跑 count(*) 查询")

    def test_no_business_type_never_blocked(self):
        """未 onboarding(get_business_type 返 None)—— 恒放行,存量/未选业态零影响。"""
        from routes import workspace_routes as wr

        fake_cur = _FakeCursor(count=5)
        with (
            mock.patch.object(wr.db, "get_cursor_rls", return_value=_FakeCursorCtx(fake_cur)),
            mock.patch.object(wr, "get_business_type", return_value=None),
        ):
            self.assertFalse(wr._pos_single_store_blocked("tenant-1"))

    def test_no_tenant_id_never_touches_db(self):
        from routes import workspace_routes as wr

        with mock.patch.object(wr.db, "get_cursor_rls") as m:
            self.assertFalse(wr._pos_single_store_blocked(None))
        m.assert_not_called()


class PosSingleStoreGateRouteWiringTests(unittest.IsolatedAsyncioTestCase):
    """create 路由确实接了这道闸:命中 → 对外抛 403 + detail=pos.workspace_single_store
    (照本文件既有 HTTPException+detail code 范式,与 workspace.tax_id_duplicate 同款,
    前端 apiClient 读 err.detail 映射四语);未命中 → 原样放行到既有建档流程。"""

    async def test_route_raises_http_exception_when_gate_blocks(self):
        from fastapi import HTTPException
        from routes import workspace_routes as wr

        req = wr.WorkspaceClientCreate(name="ACME")
        with (
            mock.patch.object(wr, "require_perm", return_value={"id": "u1"}),
            mock.patch.object(wr, "_pos_single_store_blocked", return_value=True),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await wr.create_workspace_client(req, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "pos.workspace_single_store")

    async def test_route_proceeds_when_gate_allows(self):
        from routes import workspace_routes as wr

        req = wr.WorkspaceClientCreate(name="ACME")
        with (
            mock.patch.object(wr, "require_perm", return_value={"id": "u1"}),
            mock.patch.object(wr, "_pos_single_store_blocked", return_value=False),
            mock.patch.object(wr, "pearnly_ai_m1_enabled_for", return_value=False),
            mock.patch.object(wr.db, "tax_id_in_use", return_value=False),
            mock.patch.object(wr.db, "create_workspace_client", return_value=42),
            mock.patch.object(wr, "_log_op", return_value=None),
        ):
            out = await wr.create_workspace_client(req, mock.Mock())
        self.assertEqual(out, {"ok": True, "id": 42})


class PosSingleStoreGateSourceTests(unittest.TestCase):
    """源码钉:闸判据字面量存在(防有人悄悄改字符串/挪出条件)。"""

    def test_helper_checks_pos_only_and_raises_correct_code(self):
        text = _read("routes/workspace_routes.py")
        self.assertIn('!= "pos_only"', text)
        self.assertIn('raise HTTPException(403, detail="pos.workspace_single_store")', text)
        self.assertIn("_pos_single_store_blocked(tenant_id)", text)


class PosSingleStoreGateI18nTests(unittest.TestCase):
    def test_four_languages_have_the_key(self):
        text = _read("static/i18n-data.js")
        self.assertEqual(
            text.count("'pos.workspace_single_store':"),
            4,
            "pos.workspace_single_store 应有四语(zh/en/th/ja)各一份",
        )


class PosSingleStoreGateFrontendTests(unittest.TestCase):
    """src/home/workspace-switcher.ts:pos_only 藏「新建主体」(data-orgcreate)入口。"""

    def test_switcher_hides_orgcreate_for_pos_only(self):
        text = _read("src/home/workspace-switcher.ts")
        self.assertIn("window._businessType === 'pos_only'", text)

    def test_switcher_keeps_orgmanage_regardless_of_business_type(self):
        # 「管理全部客户」不受此判据约束,pos_only 也照常渲染。
        text = _read("src/home/workspace-switcher.ts")
        self.assertIn('data-orgmanage="1"', text)

    def test_subject_create_maps_error_code_to_i18n_text(self):
        # 后端闸兜底命中时(理论上前端已藏入口,不该摸到)仍要有人话文案,不退化成通用失败。
        text = _read("src/home/subject-create.ts")
        self.assertIn("code === 'pos.workspace_single_store'", text)


if __name__ == "__main__":
    unittest.main()
