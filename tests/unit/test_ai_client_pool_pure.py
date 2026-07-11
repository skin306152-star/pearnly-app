# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_client_pool_pure.py

D2-S8+S9(LINE 待问客户池会计端 UI)前端纯函数守门:ai-review-queue.js 的
suggestQuestionType/buildStagePayload、ai-client-pool-render.js 的状态词/问题类型
标签映射、ai-review-pool.js 的第四动作状态机(toggle/forItem 纯状态 + stage 网络
落地两态)。同 test_ai_pure_modules.py 先例走真 node 子进程 require 源文件断言,
不进浏览器。node 缺失时跳过。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SuggestQuestionTypeTests(unittest.TestCase):
    def test_direction_ticket_suggests_direction(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify([
                q.suggestQuestionType({{flag_reason: 'direction_ambiguous'}}),
                q.suggestQuestionType({{flag_reason: 'sales_direction_unhandled:x'}}),
                q.suggestQuestionType({{flag_reason: 'amount_math_fail'}}),
                q.suggestQuestionType({{flag_reason: 'ocr_low_confidence:band'}}),
                q.suggestQuestionType(null),
            ]));
            """)
        self.assertEqual(out, ["direction", "direction", "amount", "freeform", "freeform"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BuildStagePayloadTests(unittest.TestCase):
    def test_shape_carries_item_id_and_ocr_fields(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            const entry = {{
                item_id: 'it-1',
                flag_reason: 'amount_math_fail',
                ocr_read: {{
                    seller_tax: '0105555167627',
                    invoice_number: 'IN26-00575',
                    total_amount: '62108.40',
                }},
            }};
            process.stdout.write(JSON.stringify(q.buildStagePayload(entry, 'amount')));
            """)
        self.assertEqual(
            out,
            {
                "item_id": "it-1",
                "question_type": "amount",
                "payload": {
                    "supplier": "0105555167627",
                    "invno": "IN26-00575",
                    "amount": "62108.40",
                    "note": "amount_math_fail",
                },
            },
        )

    def test_null_entry_returns_null(self):
        out = _run_node(f"""
            const q = require({json.dumps(str(AI_DIR / "ai-review-queue.js"))});
            process.stdout.write(JSON.stringify(q.buildStagePayload(null, 'drop')));
            """)
        self.assertIsNone(out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ClientPoolRenderPureTests(unittest.TestCase):
    def test_status_order_and_question_type_label_key(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-client-pool-render.js"))});
            process.stdout.write(JSON.stringify([
                r.STATUS_ORDER,
                r.questionTypeLabelKey('direction'),
                r.questionTypeLabelKey('amount'),
                r.questionTypeLabelKey('drop'),
                r.questionTypeLabelKey('freeform'),
                r.questionTypeLabelKey('bogus'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                ["staged", "pending", "manual_review"],
                "pool_qtype_direction",
                "pool_qtype_amount",
                "pool_qtype_drop",
                "pool_qtype_freeform",
                "pool_qtype_freeform",
            ],
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ReviewPoolStateMachineTests(unittest.TestCase):
    """ai-review-pool.js 不是纯 UMD(用 window.AI 直挂,同 ai-review.js 惯例),
    node 里 shim window=global 后可直接跑其状态机(toggle/forItem 是纯状态;stage
    传入的 fake api 是普通 Promise,node 原生支持,不需要浏览器)。"""

    def _harness(self, body: str) -> dict:
        review_queue = json.dumps(str(AI_DIR / "ai-review-queue.js"))
        api_js = json.dumps(str(AI_DIR / "ai-api.js"))
        pool_js = json.dumps(str(AI_DIR / "ai-review-pool.js"))
        return _run_node(f"""
            global.window = global;
            // 非恒等变换(模拟真有翻译):at(key)!==key 时 mapApiErrorKey 才命中具体错误码,
            // 否则退化 err_generic——同 ai-review.js decide().catch 的判定口径。
            global.at = function (key) {{ return '[' + key + ']'; }};
            require({review_queue});
            require({api_js});
            require({pool_js});
            {body}
            """)

    def test_toggle_flips_open_and_ignores_when_busy_or_done(self):
        out = self._harness("""
            const pool = global.AI.reviewPool.create();
            const r1 = pool.toggle('it-1');
            const s1 = pool.forItem('it-1').open;
            const r2 = pool.toggle('it-1');
            const s2 = pool.forItem('it-1').open;
            pool.forItem('it-2').busy = true;
            const r3 = pool.toggle('it-2');
            process.stdout.write(JSON.stringify([r1, s1, r2, s2, r3]));
            """)
        self.assertEqual(out, [True, True, True, False, False])

    def test_stage_success_marks_done_and_closes_panel(self):
        out = self._harness("""
            const pool = global.AI.reviewPool.create();
            const entry = { item_id: 'it-3', flag_reason: 'amount_math_fail', ocr_read: {} };
            const fakeApi = { stageQuestion: () => Promise.resolve({ ok: true }) };
            const events = [];
            pool.stage(fakeApi, 'wo-1', entry, 'amount', function () {
                events.push(JSON.parse(JSON.stringify(pool.forItem('it-3'))));
            });
            setTimeout(() => {
                process.stdout.write(JSON.stringify(events));
            }, 50);
            """)
        self.assertEqual(len(out), 2)
        self.assertTrue(out[0]["busy"])
        self.assertFalse(out[1]["busy"])
        self.assertTrue(out[1]["done"])
        self.assertFalse(out[1]["open"])

    def test_stage_failure_sets_generic_error_key(self):
        out = self._harness("""
            const pool = global.AI.reviewPool.create();
            const entry = { item_id: 'it-4', flag_reason: 'amount_math_fail', ocr_read: {} };
            const err = new Error('boom');
            err.code = 'client_pool.stage_failed';
            const fakeApi = { stageQuestion: () => Promise.reject(err) };
            const events = [];
            pool.stage(fakeApi, 'wo-1', entry, 'amount', function () {
                events.push(JSON.parse(JSON.stringify(pool.forItem('it-4'))));
            });
            setTimeout(() => {
                process.stdout.write(JSON.stringify(events));
            }, 50);
            """)
        self.assertEqual(len(out), 2)
        self.assertFalse(out[1]["busy"])
        self.assertFalse(out[1]["done"])
        # global.at() 原样回传 key(不是 'err_generic')→ mapApiErrorKey 命中即用该 key。
        self.assertEqual(out[1]["errKey"], "err_client_pool_stage_failed")


if __name__ == "__main__":
    unittest.main()
