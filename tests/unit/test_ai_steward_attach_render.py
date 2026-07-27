#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_steward_attach_render.py

万能口(F1 · 前端)判据与拼装守门:ai-steward-attach-render.js 的纯函数(限额规整/
选文件当下的拒收判据/送出闸/料名闭集/下载链识别)与四块 HTML(附件盘四态、气泡下的
原件行、落区、回执卡动作按钮),外加 ai-steward-attach.js 动作层的状态迁移(假钩子 +
假 api 跑真代码)。同 test_ai_billing_render.py 的 node subprocess require 手法。

盯死的三条产品判据(都是「不猜/不假绿」那一类,机械闸抓不到才写在这里):
  1. 限额读不到 → normalizeLimits 返 null → 不给附件口(不拿自己编的 20MB 去拒文件);
  2. 认不出的料在 chip 副行必须写 stw_kind_unknown,不许回落成一个像样的类型名;
  3. 还有件在传 → canSubmit=false(排队送等于把「立即应承」改成等 30 秒)。

node 侧无 window.at → 测试注入 at=(k)=>k,HTML 断言直接认 key 字符串。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

RENDER = str(AI_DIR / "ai-steward-attach-render.js")
ATTACH = str(AI_DIR / "ai-steward-attach.js")
STATE = str(AI_DIR / "ai-state.js")
STATES_RENDER = str(AI_DIR / "ai-states-render.js")

# 纯函数段:require 即可,不需要 AI 全局(双段结构的上半段零依赖)。
PURE = f"const r = require({json.dumps(RENDER)});"

# 拼装段:先造一个带 document 的假 root 让下半段挂载,再补 AI.state/AI.statesRender 与 at()。
HTML_PRELUDE = f"""
    global.self = global;
    global.document = {{}};
    require({json.dumps(STATE)});
    global.at = (k, v) => (v ? k + ':' + JSON.stringify(v) : k);
    require({json.dumps(STATES_RENDER)});
    require({json.dumps(RENDER)});
    const R = global.AI.stewardAttachRender;
    """

LIMITS = {
    "max_file_bytes": 20971520,
    "max_batch_bytes": 36700160,
    "max_files": 20,
    "accept": [".pdf", ".xlsx", ".jpg"],
    "ttl_days": 30,
}


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class LimitsTests(unittest.TestCase):
    def _norm(self, raw):
        return _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify(r.normalizeLimits({json.dumps(raw)})));
            """)

    def test_full_payload_normalizes(self):
        out = self._norm(LIMITS)
        self.assertEqual(out["maxFileBytes"], 20971520)
        self.assertEqual(out["maxFiles"], 20)
        self.assertEqual(out["accept"], [".pdf", ".xlsx", ".jpg"])

    def test_missing_payload_is_null_not_a_hardcoded_default(self):
        """老后端 / 契约漂了 → 前端不许自己编一份上限,整块不给附件口才是诚实。"""
        for raw in (None, {}, {"max_file_bytes": 100}, {**LIMITS, "accept": []}):
            self.assertIsNone(self._norm(raw), raw)

    def test_accept_is_lowercased(self):
        out = self._norm({**LIMITS, "accept": [".PDF", ".XlsX"]})
        self.assertEqual(out["accept"], [".pdf", ".xlsx"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class RejectAtPickTimeTests(unittest.TestCase):
    def _reject(self, file, tally=None):
        return _run_node(f"""
            {PURE}
            const lim = r.normalizeLimits({json.dumps(LIMITS)});
            process.stdout.write(JSON.stringify(
                r.rejectCode({json.dumps(file)}, lim, {json.dumps(tally or {})})));
            """)

    def test_good_file_passes(self):
        self.assertIsNone(self._reject({"name": "gl.pdf", "size": 1024}))

    def test_zero_byte_and_bad_extension_and_oversize(self):
        self.assertEqual(self._reject({"name": "a.pdf", "size": 0}), "steward.attachment_empty")
        self.assertEqual(
            self._reject({"name": "a.zip", "size": 10}), "steward.attachment_bad_ext"
        )
        self.assertEqual(
            self._reject({"name": "a.pdf", "size": 20971521}), "steward.attachment_too_large"
        )

    def test_batch_ceilings_use_running_tally(self):
        self.assertEqual(
            self._reject({"name": "a.pdf", "size": 10}, {"count": 20, "bytes": 0}),
            "steward.attachment_too_many",
        )
        self.assertEqual(
            self._reject({"name": "a.pdf", "size": 1024}, {"count": 1, "bytes": 36700160}),
            "steward.attachment_batch_too_large",
        )

    def test_no_limits_means_no_intake(self):
        out = _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify(
                r.rejectCode({{name: 'a.pdf', size: 10}}, null, {{}})));
            """)
        self.assertEqual(out, "steward.attachment_closed")

    def test_every_reject_code_maps_to_its_own_copy_key(self):
        """六个码各有各的话:统一回落成「上传失败」等于不告诉人是哪道上限卡住了。"""
        out = _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify([
                'steward.attachment_too_many', 'steward.attachment_too_large',
                'steward.attachment_batch_too_large', 'steward.attachment_bad_ext',
                'steward.attachment_empty', 'steward.attachment_closed', 'whatever',
            ].map(r.limitErrKey)));
            """)
        self.assertEqual(len(set(out[:6])), 6)
        self.assertEqual(out[6], "stw_att_err_up")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SubmitGateTests(unittest.TestCase):
    def _can(self, ctx):
        return _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify(r.canSubmit({json.dumps(ctx)})));
            """)

    def test_uploading_blocks_send(self):
        ctx = {"text": "转成 Excel", "chips": [{"state": "uploading"}], "busy": False}
        self.assertFalse(self._can(ctx))

    def test_queued_blocks_send_too(self):
        """并发 3 路,第 4 件还排着队 —— 它同样没有 attachment_id,送出去就是漏带。"""
        ctx = {
            "text": "",
            "chips": [
                {"state": "ready", "attachment_id": "u1"},
                {"state": "queued"},
            ],
            "busy": False,
        }
        self.assertFalse(self._can(ctx))

    def test_pure_file_gesture_with_no_text_is_sendable(self):
        ctx = {"text": "", "chips": [{"state": "ready", "attachment_id": "u1"}], "busy": False}
        self.assertTrue(self._can(ctx))

    def test_nothing_at_all_is_not_sendable(self):
        self.assertFalse(self._can({"text": "  ", "chips": [], "busy": False}))
        # 被拒/失败的件不算数(它们没有 attachment_id,后端会 422 empty_turn)
        self.assertFalse(
            self._can({"text": "", "chips": [{"state": "rejected"}], "busy": False})
        )

    def test_in_flight_turn_blocks_send(self):
        ctx = {"text": "hi", "chips": [], "busy": True}
        self.assertFalse(self._can(ctx))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SmallPureTests(unittest.TestCase):
    def test_kind_key_closed_set_falls_back_to_unknown(self):
        out = _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify(
                ['gl_ledger', 'converted', 'other', ''].map(r.kindKey)));
            """)
        self.assertEqual(
            out, ["stw_kind_gl_ledger", "stw_kind_converted", "stw_kind_unknown", "stw_kind_unknown"]
        )

    def test_short_name_keeps_the_tail(self):
        out = _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify(
                r.shortName('รายงานภาษีขายประจำเดือนมิถุนายน-2569.xlsx', 24)));
            """)
        self.assertTrue(out.endswith("2569.xlsx"), out)
        self.assertIn("…", out)
        self.assertLessEqual(len(out), 24)

    def test_download_id_only_matches_the_steward_attachment_route(self):
        out = _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify([
                '/api/ai/steward/attachments/8f14e45f-ea11-4c1e-9b2a-000000000001/download',
                '/api/workorder/orders/1/items/2/image',
                '/ai#/intake', 'javascript:alert(1)', '',
            ].map(r.downloadIdOf)));
            """)
        self.assertEqual(out[0], "8f14e45f-ea11-4c1e-9b2a-000000000001")
        self.assertEqual(out[1:], [None, None, None, None])

    def test_tray_hides_tool_artifacts(self):
        out = _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify(r.trayItems([
                {{attachment_id: 'a', status: 'ready'}},
                {{attachment_id: 'b', status: 'artifact'}},
            ]).map((a) => a.attachment_id)));
            """)
        self.assertEqual(out, ["a"])

    def test_fmt_bytes_units(self):
        out = _run_node(f"""
            {PURE}
            process.stdout.write(JSON.stringify([512, 2048, 3145728].map(r.fmtBytes)));
            """)
        self.assertEqual(out, ["512 B", "2 KB", "3.0 MB"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class TrayHtmlTests(unittest.TestCase):
    def _tray(self, ctx):
        return _run_node(f"""
            {HTML_PRELUDE}
            process.stdout.write(JSON.stringify(R.trayHtml({json.dumps(ctx)})));
            """)

    def test_uploading_chip_has_progress_bar_and_no_retry(self):
        out = self._tray(
            {"chips": [{"local_id": "a1", "name": "gl.pdf", "size": 2048, "state": "uploading",
                        "pct": 42}]}
        )
        self.assertIn("st-bar", out)
        self.assertIn("--p:42", out)
        self.assertNotIn("stw-att-retry", out)

    def test_ready_chip_shows_what_it_was_recognised_as(self):
        out = self._tray(
            {"chips": [{"local_id": "a1", "name": "gl.pdf", "size": 2048, "state": "ready",
                        "att": {"kind": "gl_ledger", "page_count": 3}}]}
        )
        self.assertIn("stw_kind_gl_ledger", out)
        self.assertIn("stw_att_pages", out)

    def test_unrecognised_file_says_so_and_does_not_fall_back_to_other(self):
        out = self._tray(
            {"chips": [{"local_id": "a1", "name": "x.pdf", "size": 10, "state": "ready",
                        "att": {"kind": "unknown", "kind_source": "unknown"}}]}
        )
        self.assertIn("stw_kind_unknown", out)

    def test_failed_chip_offers_retry_with_its_own_reason(self):
        out = self._tray(
            {"chips": [{"local_id": "a1", "name": "x.pdf", "size": 10, "state": "failed",
                        "err": "ไฟล์เสียหาย"}]}
        )
        self.assertIn('data-action="stw-att-retry"', out)
        self.assertIn('data-cid="a1"', out)
        self.assertIn("ไฟล์เสียหาย", out)

    def test_rejected_chip_stays_visible_with_its_reason(self):
        """静默丢掉被拒的件 = 让人以为拖进来的 12 份都传上去了。"""
        out = self._tray(
            {"chips": [{"local_id": "a1", "name": "x.zip", "size": 10, "state": "rejected",
                        "err": "格式吃不了"}]}
        )
        self.assertIn("stw-att-chip rejected", out)
        self.assertIn("格式吃不了", out)
        self.assertIn('data-action="stw-att-remove"', out)

    def test_password_row_appears_for_the_named_file(self):
        out = self._tray(
            {"chips": [], "pwChip": {"local_id": "a7", "name": "kbank.pdf"}}
        )
        self.assertIn('id="stwAttPw"', out)
        self.assertIn('data-action="stw-att-pw-go"', out)
        self.assertIn('data-cid="a7"', out)

    def test_picker_is_absent_without_limits(self):
        empty = _run_node(f"""
            {HTML_PRELUDE}
            process.stdout.write(JSON.stringify(R.pickerHtml({{limits: null}})));
            """)
        self.assertEqual(empty, "")
        limits = json.dumps({"accept": [".pdf", ".jpg"]})
        with_limits = _run_node(f"""
            {HTML_PRELUDE}
            process.stdout.write(JSON.stringify(R.pickerHtml({{limits: {limits}}})));
            """)
        self.assertIn('data-action="stw-att-pick"', with_limits)
        self.assertIn('accept=".pdf,.jpg"', with_limits)
        self.assertIn('id="stwAttFile"', with_limits)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BubbleAndActionsHtmlTests(unittest.TestCase):
    def test_bubble_files_are_download_buttons_not_naked_links(self):
        """/api/ai/steward/* 只认 Bearer 头,<a href> 会拿到 401 —— 必须走带头的下载。"""
        out = _run_node(f"""
            {HTML_PRELUDE}
            process.stdout.write(JSON.stringify(R.bubbleFilesHtml([
                {{attachment_id: 'u1', name: 'gl.pdf', kind: 'gl_ledger'}},
            ])));
            """)
        self.assertIn('data-action="stw-att-dl"', out)
        self.assertIn('data-aid="u1"', out)
        self.assertNotIn("<a ", out)

    def test_actions_carry_tool_ids_and_spend_flag_back_verbatim(self):
        out = _run_node(f"""
            {HTML_PRELUDE}
            process.stdout.write(JSON.stringify(R.actionsHtml({{
                kind: 'actions', label: 'x',
                actions: [{{tool: 'file_convert', label: '转成 Excel · gl.pdf',
                           attachment_ids: ['u1'], confirm_spend: true,
                           cost: {{wallet_charge: false, model_call: true, page_count: 3}}}}],
            }}, {{dead: false}})));
            """)
        self.assertIn('data-tool="file_convert"', out)
        self.assertIn('data-aids="u1"', out)
        self.assertIn('data-spend="1"', out)
        self.assertIn("转成 Excel · gl.pdf", out)
        self.assertIn("stw_act_model", out)
        self.assertNotIn("disabled", out)

    def test_actions_are_greyed_out_once_the_card_is_dead(self):
        out = _run_node(f"""
            {HTML_PRELUDE}
            process.stdout.write(JSON.stringify(R.actionsHtml({{
                actions: [{{tool: 't', label: 'l', attachment_ids: [], cost: {{}}}}],
            }}, {{dead: true}})));
            """)
        self.assertIn("disabled", out)

    def test_no_actions_renders_nothing(self):
        out = _run_node(f"""
            {HTML_PRELUDE}
            process.stdout.write(JSON.stringify(R.actionsHtml({{actions: []}}, {{}})));
            """)
        self.assertEqual(out, "")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端动作层测试")
class AttachActionsTests(unittest.TestCase):
    """ai-steward-attach.js:假钩子 + 假 api 跑真代码,断言状态迁移不是断言函数存在。"""

    SETUP = f"""
        global.self = global;
        global.document = {{ addEventListener: () => {{}} }};
        require({json.dumps(STATE)});
        global.at = (k) => k;
        require({json.dumps(STATES_RENDER)});
        require({json.dumps(RENDER)});
        const mod = require({json.dumps(ATTACH)});
        const flush = () => new Promise((r) => setImmediate(r));
        function harness(api) {{
            const S = {{
                api: api, sessionId: 's1', busy: false, errText: null,
                attChips: [], attPwFor: null,
                attLimits: global.AI.stewardAttachRender.normalizeLimits({json.dumps(LIMITS)}),
            }};
            const sent = [];
            const box = {{ S: S }};
            const a = mod.create({{
                state: () => box.S,
                getEl: () => null,
                renderRight: () => {{}},
                sendTurn: (body, atts) => sent.push({{ body, atts }}),
            }});
            return {{ a, S, box, sent }};
        }}
        """

    def test_rejected_files_never_hit_the_network(self):
        out = _run_node(f"""
            {self.SETUP}
            (async () => {{
                let hits = 0;
                const h = harness({{
                    uploadStewardAttachments: () => {{ hits += 1; return new Promise(() => {{}}); }},
                }});
                h.a.addFiles([
                    {{ name: 'a.zip', size: 10 }},
                    {{ name: 'b.pdf', size: 0 }},
                    {{ name: 'c.pdf', size: 100 }},
                ]);
                await flush();
                process.stdout.write(JSON.stringify({{
                    hits, states: h.S.attChips.map((c) => c.state),
                }}));
            }})();
            """)
        self.assertEqual(out["hits"], 1)
        self.assertEqual(out["states"], ["rejected", "rejected", "uploading"])

    def test_concurrency_is_capped_at_three(self):
        out = _run_node(f"""
            {self.SETUP}
            (async () => {{
                let live = 0;
                const h = harness({{
                    uploadStewardAttachments: () => {{ live += 1; return new Promise(() => {{}}); }},
                }});
                h.a.addFiles([1, 2, 3, 4, 5].map((i) => ({{ name: 'f' + i + '.pdf', size: 10 }})));
                await flush();
                process.stdout.write(JSON.stringify({{ live }}));
            }})();
            """)
        self.assertEqual(out["live"], 3)

    def test_a_200_without_an_attachment_row_is_treated_as_failure(self):
        """契约漂了不许留下一个 id 是空的 ready chip —— 送出时才炸更难查。"""
        out = _run_node(f"""
            {self.SETUP}
            (async () => {{
                const h = harness({{
                    uploadStewardAttachments: () => Promise.resolve({{ attachments: [] }}),
                }});
                h.a.addFiles([{{ name: 'a.pdf', size: 10 }}]);
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{
                    state: h.S.attChips[0].state, err: h.S.attChips[0].err,
                }}));
            }})();
            """)
        self.assertEqual(out["state"], "failed")
        self.assertEqual(out["err"], "stw_att_err_up")

    def test_encrypted_pdf_opens_the_password_row_for_that_file(self):
        out = _run_node(f"""
            {self.SETUP}
            (async () => {{
                const h = harness({{
                    uploadStewardAttachments: () => Promise.reject({{
                        status: 422,
                        detail: {{
                            code: 'workorder.intake.pdf_password_required',
                            message: {{ zh: '这份 PDF 有密码', th: 'ไฟล์นี้มีรหัสผ่าน' }},
                        }},
                    }}),
                }});
                h.a.addFiles([{{ name: 'kbank.pdf', size: 10 }}]);
                await flush(); await flush();
                process.stdout.write(JSON.stringify({{
                    pwFor: h.S.attPwFor, cid: h.S.attChips[0].local_id,
                    err: h.S.attChips[0].err,
                }}));
            }})();
            """)
        self.assertEqual(out["pwFor"], out["cid"])
        # 422 的四语 message 直接印,不再过前端 i18n
        self.assertEqual(out["err"], "这份 PDF 有密码")

    def test_submit_moves_only_ready_files_into_the_turn(self):
        out = _run_node(f"""
            {self.SETUP}
            (async () => {{
                let n = 0;
                const h = harness({{
                    uploadStewardAttachments: () => {{
                        n += 1;
                        return Promise.resolve({{ attachments: [{{ attachment_id: 'u' + n }}] }});
                    }},
                }});
                h.a.addFiles([
                    {{ name: 'a.pdf', size: 10 }},
                    {{ name: 'b.zip', size: 10 }},
                ]);
                await flush(); await flush(); await flush();
                h.a.submit('把这份转成 Excel');
                process.stdout.write(JSON.stringify({{
                    sent: h.sent, left: h.S.attChips.map((c) => c.state),
                }}));
            }})();
            """)
        self.assertEqual(out["sent"][0]["body"]["attachment_ids"], ["u1"])
        self.assertEqual(out["sent"][0]["body"]["text"], "把这份转成 Excel")
        # 被拒的那件留在盘上等处理,不静默带走
        self.assertEqual(out["left"], ["rejected"])

    def test_submit_is_a_no_op_while_a_file_is_still_uploading(self):
        out = _run_node(f"""
            {self.SETUP}
            (async () => {{
                const h = harness({{
                    uploadStewardAttachments: () => new Promise(() => {{}}),
                }});
                h.a.addFiles([{{ name: 'a.pdf', size: 10 }}]);
                await flush();
                h.a.submit('转一下');
                process.stdout.write(JSON.stringify({{ sent: h.sent.length }}));
            }})();
            """)
        self.assertEqual(out["sent"], 0)

    def test_files_dropped_before_the_session_exists_are_picked_up_on_resume(self):
        """建会话要几百毫秒;这段时间拖进来的件卡在 queued,没人踢就永远不传(静默失败)。"""
        out = _run_node(f"""
            {self.SETUP}
            (async () => {{
                let hits = 0;
                const h = harness({{
                    uploadStewardAttachments: () => {{ hits += 1; return new Promise(() => {{}}); }},
                }});
                h.S.sessionId = null;
                h.a.addFiles([{{ name: 'a.pdf', size: 10 }}]);
                await flush();
                const before = {{ hits, state: h.S.attChips[0].state }};
                h.S.sessionId = 's1';
                h.a.resume();
                await flush();
                process.stdout.write(JSON.stringify({{
                    before, after: {{ hits, state: h.S.attChips[0].state }},
                }}));
            }})();
            """)
        self.assertEqual(out["before"], {"hits": 0, "state": "queued"})
        self.assertEqual(out["after"], {"hits": 1, "state": "uploading"})

    def test_action_button_replays_its_parameters_verbatim(self):
        out = _run_node(f"""
            {self.SETUP}
            (async () => {{
                const h = harness({{}});
                const attrs = {{
                    'data-tool': 'file_convert', 'data-aids': 'u1,u2', 'data-spend': '1',
                }};
                const el = {{ getAttribute: (k) => attrs[k] }};
                const handled = h.a.onClick('stw-act', el);
                const unknown = h.a.onClick('stw-nope', el);
                process.stdout.write(JSON.stringify({{
                    handled, unknown, body: h.sent[0].body,
                }}));
            }})();
            """)
        self.assertTrue(out["handled"])
        self.assertFalse(out["unknown"])
        self.assertEqual(
            out["body"]["action"],
            {"tool": "file_convert", "attachment_ids": ["u1", "u2"], "confirm_spend": True},
        )


if __name__ == "__main__":
    unittest.main()
