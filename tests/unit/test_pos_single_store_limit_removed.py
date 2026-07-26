# -*- coding: utf-8 -*-
"""「一号一店」已撤销(Zihao 2026-07-26)防回潮钉。

原规则(2026-07-12):business_type=='pos_only' 且已有 ≥1 个套账 → 建主体报 403
pos.workspace_single_store。2026-07-26 拍板整条撤销,POS / AI 两侧一视同仁,账套主体
数量不设上限。本文件钉住"它没回来",替代原 test_pos_single_store_gate.py。

主钉是行为级(不起真库):pos_only 租户带 99 个既有套账走 create 路由仍然建档成功——
证明是真没闸,而不是"闸还在只是这次没触发"。四个静态钉盯剩余痕迹(后端判据/前端两处
入口/四语死键),防有人按旧注释把它抄回来。

POS 真正的付费额度闸(services/pos/entitlements.check_limit · 门店取码路)是另一套,
不在本文件管辖内,撤销一号一店不影响它。
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


class PosOnlyTenantCanCreateMoreSubjectsTests(unittest.IsolatedAsyncioTestCase):
    """行为铁证:pos_only + 已有套账,建主体照样成功(不再 403)。"""

    async def test_pos_only_with_existing_stores_still_creates(self):
        from routes import workspace_routes as wr

        req = wr.WorkspaceClientCreate(name="ACME 2")
        with (
            mock.patch.object(wr, "require_perm", return_value={"id": "u1"}),
            mock.patch.object(wr, "_tid", return_value="tenant-pos"),
            mock.patch.object(wr, "pearnly_ai_m1_enabled_for", return_value=False),
            mock.patch.object(wr.db, "tax_id_in_use", return_value=False),
            mock.patch.object(wr.db, "create_workspace_client", return_value=42),
            mock.patch.object(wr, "_log_op", return_value=None),
        ):
            out = await wr.create_workspace_client(req, mock.Mock())
        self.assertEqual(out, {"ok": True, "id": 42})

    async def test_create_path_never_reads_business_type(self):
        """建主体不再按业态分叉:整条路径不该再碰 get_business_type。"""
        from routes import workspace_routes as wr

        self.assertFalse(
            hasattr(wr, "get_business_type"),
            "workspace_routes 不该再导入 get_business_type(一号一店是它唯一用途)",
        )


class PosSingleStoreLimitGoneSourceTests(unittest.TestCase):
    """静态钉:四处旧痕迹都不许留。"""

    def test_backend_helper_and_error_code_gone(self):
        text = _read("routes/workspace_routes.py")
        self.assertNotIn("_pos_single_store_blocked", text)
        self.assertNotIn("pos.workspace_single_store", text)

    def test_switcher_no_longer_hides_create_by_business_type(self):
        text = _read("src/home/workspace-switcher.ts")
        self.assertNotIn("window._businessType === 'pos_only'", text)
        self.assertIn('data-orgcreate="1"', text, "「新建主体」入口必须对老板恒在")

    def test_subject_create_no_longer_maps_dead_error_code(self):
        text = _read("src/home/subject-create.ts")
        self.assertNotIn("pos.workspace_single_store", text)

    def test_dead_i18n_keys_purged_from_both_dictionaries(self):
        self.assertNotIn("pos.workspace_single_store", _read("static/i18n-data.js"))
        for lang in ("zh", "en", "th", "ja"):
            self.assertNotIn(
                "err_pos_workspace_single_store",
                _read(f"static/ai/ai-i18n-{lang}-2.js"),
                f"ai-i18n-{lang}-2.js 仍留着死翻译键",
            )


if __name__ == "__main__":
    unittest.main()
