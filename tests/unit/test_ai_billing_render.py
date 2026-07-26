#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_billing_render.py

Pearnly AI(B5 老站对齐 #16)设置页计费区守门:ai-billing-render.js 的金额校验/状态
色族/日期与整数金额格式/四块 HTML(余额面板双视角、记录面板空态与行、三步弹窗、收尾态),
以及 ai-api-billing.js 薄层的端点契约(方法/路径/body,含 multipart 空值不上传)。
同 test_ai_desk_render_pure.py 的 node subprocess require 手法——真 node 跑源文件。

node 侧无 window.at → t() 回退原 key,HTML 断言直接认 key 字符串(与
_settings_entry_local.spec.js 的"不露原始 key"E2E 互补:这里反过来利用 key 做锚点)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

RENDER = str(AI_DIR / "ai-billing-render.js")
API = str(AI_DIR / "ai-api-billing.js")
STATE = str(AI_DIR / "ai-state.js")
FORMAT = str(AI_DIR / "ai-format.js")

# balancePanelHtml/historyPanelHtml 借 AI.state(esc/emptyHtml)与 AI.format(money)拼装,
# 先 require 两个依赖挂上 global.AI,再 require 被测文件(同 ai.html 的加载顺序)。
PRELUDE = f"""
    require({json.dumps(STATE)});
    require({json.dumps(FORMAT)});
    const b = require({json.dumps(RENDER)});
    """


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class TopupAmountErrorTests(unittest.TestCase):
    def _err(self, raw):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.topupAmountError({json.dumps(raw)})));
            """)

    def test_below_min_invalid(self):
        self.assertEqual(self._err("9"), "bill_amt_invalid")

    def test_min_boundary_ok(self):
        self.assertIsNone(self._err("10"))

    def test_max_boundary_ok(self):
        self.assertIsNone(self._err("500000"))

    def test_above_max_rejected(self):
        # 后端 le=500000 会 422;前端先挡免白跑一次网络(老站 billing.ts 同款兜底)
        self.assertEqual(self._err("500001"), "bill_amt_max")

    def test_non_numeric_invalid(self):
        self.assertEqual(self._err("abc"), "bill_amt_invalid")

    def test_empty_invalid(self):
        self.assertEqual(self._err(""), "bill_amt_invalid")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class StatusAndFormatTests(unittest.TestCase):
    def test_status_chip_cls_maps_review_states(self):
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify([
                b.statusChipCls('pending'), b.statusChipCls('approved'),
                b.statusChipCls('rejected'), b.statusChipCls('weird'),
            ]));
            """)
        self.assertEqual(out, ["st-wait", "st-ok", "st-err", "st-off"])

    def test_fmt_date_iso_and_garbage(self):
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify([
                b.fmtDate('2026-07-27T10:30:00+07:00'), b.fmtDate('not-a-date'), b.fmtDate(null),
            ]));
            """)
        self.assertEqual(out[0], "2026-07-27")
        self.assertEqual(out[1:], ["—", "—"])

    def test_fmt_baht_int_thousands(self):
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.fmtBahtInt(2000)));
            """)
        self.assertEqual(out, "฿2,000")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BalancePanelTests(unittest.TestCase):
    def test_owner_sees_balance_rate_and_topup_button(self):
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.balancePanelHtml(
                {{balance_thb: 1234.5, pages_this_month: 42, current_rate: 1.5}}
            )));
            """)
        self.assertIn("฿1,234.50", out)
        self.assertIn('data-action="bill-topup"', out)
        self.assertIn("฿1.50", out)

    def test_exempt_owner_gets_badge(self):
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.balancePanelHtml(
                {{balance_thb: 0, pages_this_month: 0, current_rate: 1.5, is_billing_exempt: true}}
            )));
            """)
        self.assertIn("bill_exempt", out)
        self.assertIn("st-badge st-ok", out)

    def test_employee_sees_hint_not_money_or_topup(self):
        # 后端员工视角本就无 balance_thb —— 前端不猜不编钱数,也不给会 403 的充值按钮
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.balancePanelHtml(
                {{has_tenant: true, is_owner: false, my_invoice_count: 7}}
            )));
            """)
        self.assertIn("bill_employee_hint", out)
        self.assertIn("bill_employee_count", out)
        self.assertNotIn('data-action="bill-topup"', out)
        self.assertNotIn("฿", out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class HistoryPanelTests(unittest.TestCase):
    def test_empty_history_is_empty_state_that_points_the_way(self):
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.historyPanelHtml([])));
            """)
        self.assertIn('data-state="empty"', out)
        self.assertIn("bill_history_empty_s", out)

    def test_rows_render_amount_status_and_rejection_note(self):
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.historyPanelHtml([
                {{created_at: '2026-07-01T09:00:00', amount_thb: 500, status: 'approved', review_note: ''}},
                {{created_at: '2026-07-02T09:00:00', amount_thb: 300, status: 'rejected', review_note: 'ยอดไม่ตรง'}},
            ])));
            """)
        self.assertIn("฿500.00", out)
        self.assertIn("st-badge st-ok", out)
        self.assertIn("st-badge st-err", out)
        self.assertIn("ยอดไม่ตรง", out)

    def test_approved_note_not_shown(self):
        # 审核备注只在驳回时对用户有行动价值(为何没过);通过件的内部备注不糊脸
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.historyPanelHtml([
                {{created_at: '2026-07-01T09:00:00', amount_thb: 500, status: 'approved',
                  review_note: 'SlipOK auto-approved'}},
            ])));
            """)
        self.assertNotIn("SlipOK", out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ModalTests(unittest.TestCase):
    def _modal(self, m):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.modalHtml({json.dumps(m)})));
            """)

    def test_step1_has_quick_amounts_and_input(self):
        out = self._modal({"step": 1, "amount": ""})
        for amt in (100, 500, 1000, 2000):
            self.assertIn(f'data-bill-amt="{amt}"', out)
        self.assertIn('id="billAmt"', out)
        self.assertIn("bill_btn_cancel", out)

    def test_step2_shows_bank_account_and_exact_amount_warning(self):
        out = self._modal({"step": 2, "amount": 500})
        self.assertIn("230-0-91368-4", out)
        self.assertIn("ธนาคาร กรุงเทพ", out)
        self.assertIn("bill_bank_note", out)
        self.assertIn("฿500.00", out)

    def test_step3_has_dropzone_and_optional_fields_and_submit(self):
        out = self._modal({"step": 3, "amount": 500, "fileName": ""})
        self.assertIn('id="billDz"', out)
        self.assertIn('id="billPayer"', out)
        self.assertIn('id="billNote"', out)
        self.assertIn("bill_btn_submit", out)

    def test_selected_file_name_survives_rerender(self):
        # 步骤切换整体重渲染,文件选择存 S.modal 不存 <input> —— 渲染层要把名字带回来
        out = self._modal({"step": 3, "amount": 500, "fileName": "slip.jpg"})
        self.assertIn("slip.jpg", out)
        self.assertIn("has-file", out)

    def test_done_states_are_honest(self):
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify([b.doneHtml(true), b.doneHtml(false)]));
            """)
        self.assertIn("bill_auto_ok", out[0])
        self.assertIn("bill-done ok", out[0])
        self.assertIn("bill_manual", out[1])
        self.assertIn("bill-done wait", out[1])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ApiBillingContractTests(unittest.TestCase):
    """ai-api-billing.js 薄层契约:方法/路径/body 与 routes/billing_*_routes.py 对齐。"""

    def test_json_endpoints_method_path_body(self):
        out = _run_node(f"""
            const mod = require({json.dumps(API)});
            const calls = [];
            const api = mod.create(null, () => ({{}}), (r) => r,
                (method, path, body) => {{ calls.push([method, path, body || null]); return Promise.resolve({{}}); }});
            api.getCredits();
            api.topupRequest(500);
            api.getTopupHistory();
            process.stdout.write(JSON.stringify(calls));
            """)
        self.assertEqual(
            out,
            [
                ["GET", "/api/me/credits", None],
                ["POST", "/api/credits/topup/request", {"amount_thb": 500}],
                ["GET", "/api/credits/topup/history", None],
            ],
        )

    def test_upload_slip_multipart_skips_empty_optional_fields(self):
        out = _run_node(f"""
            const mod = require({json.dumps(API)});
            let captured = null;
            const fakeRoot = {{
                fetch: (url, opts) => {{
                    captured = {{ url, method: opts.method, keys: [...opts.body.keys()] }};
                    return Promise.resolve('resp');
                }},
            }};
            const api = mod.create(fakeRoot, () => ({{Authorization: 'Bearer x'}}), (r) => r, null);
            api.uploadTopupSlip(12, new Blob(['x']), 'สมชาย', '').then(() => {{
                process.stdout.write(JSON.stringify(captured));
            }});
            """)
        self.assertEqual(out["url"], "/api/credits/topup/upload-slip/12")
        self.assertEqual(out["method"], "POST")
        self.assertIn("file", out["keys"])
        self.assertIn("payer_name", out["keys"])
        self.assertNotIn("note", out["keys"])


if __name__ == "__main__":
    unittest.main()
