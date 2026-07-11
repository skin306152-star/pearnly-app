# -*- coding: utf-8 -*-
"""PC-1b 前端接线守门(静态断言 · 无 JS runner · 同 RouteWiring 范式)。

锁三处防回归被摘:① 收银员管理页 caps 配置 + 绑主账号只读;② 收银台建单捕获
pos.approval_required → 弹店长授权窗带 approval 重发;③ 授权窗把重试结果回传 done
(建单成交面板需 res);④ i18n 四语齐;⑤ 改动已进 build(dist bundle 含标记)。"""

import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read(*parts: str) -> str:
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


class CashierAdminCapsUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = _read("src", "home", "pos-cashiers.ts")

    def test_caps_modal_and_button(self):
        self.assertIn("openCapsModal", self.src)
        self.assertIn("csh-cap-op", self.src)
        self.assertIn("data-act=\"caps\"", self.src)

    def test_saves_caps_via_put(self):
        # 保存并入既有 PUT /admin/cashiers/{id},body 带 caps
        self.assertIn("/api/pos/admin/cashiers/", self.src)
        self.assertIn("caps", self.src)
        for k in ("discount_limit_pct", "can_refund", "can_void", "can_override_price", "cost_visible"):
            self.assertIn(k, self.src)

    def test_bound_cashier_read_only(self):
        # 绑主账号(has_approver)→ 只读提示,不给编辑
        self.assertIn("has_approver", self.src)
        self.assertIn("csh-cap-bound", self.src)


class FrontCounterApprovalWiringTests(unittest.TestCase):
    def test_create_sale_gate_opens_manager_window(self):
        src = _read("static", "pos", "pos-cashier.js")
        self.assertIn("pos.approval_required", src)
        self.assertIn("POS.approve.open", src)
        self.assertIn("approval: creds", src)

    def test_approve_window_passes_result_to_done(self):
        # 建单成交面板需要重试的 res → done 必须回传结果
        src = _read("static", "pos", "pos-approve.js")
        self.assertIn("done(res)", src)


class CapsI18nParityTests(unittest.TestCase):
    def test_four_languages_each_key(self):
        data = _read("static", "i18n-data.js")
        for key in (
            "csh-cap-op",
            "csh-perm-title",
            "csh-cap-discount",
            "csh-cap-refund",
            "csh-cap-void",
            "csh-cap-price",
            "csh-cap-cost",
            "csh-cap-hint",
            "csh-cap-bound",
            "csh-err-cap-pct",
            "pos.caps_invalid",
        ):
            self.assertEqual(data.count(f"'{key}'"), 4, f"{key} not in all 4 languages")


class BuiltBundlesTests(unittest.TestCase):
    """改 src/**、static/pos/** 必须把 dist 一起提交(prod 不重建 dist)。"""

    def test_main_bundle_has_caps_ui(self):
        dist = _read("static", "dist", "main.js")
        self.assertIn("csh-cap-op", dist)
        self.assertIn("has_approver", dist)

    def test_pos_bundle_has_sale_approval(self):
        dist = _read("static", "dist", "pos.js")
        # 退货(既有)+ 建单(本片新增)各一处授权闸捕获
        self.assertGreaterEqual(dist.count("approval_required"), 2)


if __name__ == "__main__":
    unittest.main()
