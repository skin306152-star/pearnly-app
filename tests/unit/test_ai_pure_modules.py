#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_pure_modules.py

Pearnly AI(M1-W1/W2)前端纯函数模块的等价/边界守门:ai-format.js / ai-router.js /
ai-state.js / ai-api.js 都走 pos-totals.js 先例的 UMD 双导出,这里用真 node 直接
require 源文件断言输出——不进浏览器,只测无 DOM 依赖的那一半逻辑。node 缺失时跳过
(本地/CI 均装了 node)。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

# ai-intake-render.js 的 parseAmount 转发给 AI.format.parseAmount(照 ai-viewer.js 的
# esc()→AI.state.esc 先例)——node 单测独立进程里没人挂 AI.format,这里先 require
# ai-format.js 把它挂上 globalThis,后续 require 的 ai-intake-render.js 才能真正解析。
_REQUIRE_AI_FORMAT = f'require({json.dumps(str(AI_DIR / "ai-format.js"))});\n'


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiFormatTests(unittest.TestCase):
    def test_money_formats_thousands_and_negative(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.money(60114.61), f.money(0), f.money(-9), f.money('1234567.5'), f.money('abc'),
            ]));
            """)
        self.assertEqual(out, ["฿60,114.61", "฿0.00", "-฿9.00", "฿1,234,567.50", "—"])

    def test_split_period_parses_buddhist_year_month(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([f.splitPeriod('2569-05'), f.splitPeriod('garbage')]));
            """)
        self.assertEqual(out, [{"year": 2569, "month": 5}, None])

    def test_jwt_payload_decodes_or_returns_null(self):
        def _b64url(obj):
            import base64

            raw = json.dumps(obj).encode("utf-8")
            return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

        tok = "h." + _b64url({"sub": "u1", "email": "zihao@example.com"}) + ".s"
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.jwtPayload({json.dumps(tok)}),
                f.jwtPayload('not-a-jwt'),
                f.jwtPayload(null),
            ]));
            """)
        self.assertEqual(out, [{"sub": "u1", "email": "zihao@example.com"}, None, None])

    def test_jwt_display_name_prefers_email_local_part_and_rejects_bare_sub(self):
        def _b64url(obj):
            import base64

            raw = json.dumps(obj).encode("utf-8")
            return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

        tok_with_email = "h." + _b64url({"email": "zihao@example.com", "sub": "u1"}) + ".s"
        tok_sub_only = "h." + _b64url({"sub": "0ac26816-d529-40b2-a5f2-eee9d5d3331f"}) + ".s"
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.jwtDisplayName({json.dumps(tok_with_email)}),
                f.jwtDisplayName({json.dumps(tok_sub_only)}),
                f.jwtDisplayName('not-a-jwt'),
            ]));
            """)
        # 真 token(pearnly_e2e_1)payload 实测只有 sub/jti/typ/iat/exp,无邮箱——
        # 那种情况必须回落 null(状态诚实:不把不透明 UUID 当"姓名"展示)。
        self.assertEqual(out, ["zihao", None, None])

    def test_status_chip_maps_known_and_unknown(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.statusChip('stuck'), f.statusChip('running'), f.statusChip('nope'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"cls": "b", "key": "status_stuck"},
                {"cls": "a", "key": "status_running"},
                {"cls": "n", "key": "status_unknown"},
            ],
        )

    def test_status_chip_stuck_with_needs_overrides_generic_stuck(self):
        # 看板卡片、客户详情页此前各自判"是不是缺料",同一张工单能对不上文案——
        # 统一收进 statusChip(status, detail):谁传了非空 needs 谁就拿到缺料子态。
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.statusChip('stuck'),
                f.statusChip('stuck', {{needs: []}}),
                f.statusChip('stuck', {{needs: ['bank_statement']}}),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"cls": "b", "key": "status_stuck"},
                {"cls": "b", "key": "status_stuck"},
                {"cls": "w", "key": "chip_needs_materials"},
            ],
        )

    def test_chip_html_renders_span_and_shares_stuck_override(self):
        out = _run_node(f"""
            global.at = (k) => ({{status_running: 'AI 在做', chip_needs_materials: '缺料'}})[k] || k;
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.chipHtml('running'),
                f.chipHtml('stuck', {{needs: ['bank_statement']}}),
            ]));
            """)
        self.assertEqual(
            out,
            [
                '<span class="chip a">AI 在做</span>',
                '<span class="chip w">缺料</span>',
            ],
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ActorLabelTests(unittest.TestCase):
    """签批区 actor 展示(2026-07-14 清单 #2):users.username 同源解析,查不到逐级回落
    (邮箱前缀 → sub 短八位),任何分支都不产出 'user:<uuid>' 裸串。"""

    _TOKEN_JS = (
        "const token = 'x.' + Buffer.from(JSON.stringify("
        "{sub: '5effc038-d181-4875-a11f-ec111a979d64'})).toString('base64') + '.y';"
    )

    def test_username_wins_then_email_prefix_then_short_sub(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            {self._TOKEN_JS}
            process.stdout.write(JSON.stringify([
                f.actorLabel({{username: 'somchai', email: 'a@b.co'}}, token),
                f.actorLabel({{email: 'aksara@b.co'}}, token),
                f.actorLabel(null, token),
                f.actorLabel(null, null),
            ]));
            """)
        self.assertEqual(out, ["somchai", "aksara", "5effc038", ""])

    def test_actor_display_shortens_server_uuid_and_passes_names_through(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify([
                f.actorDisplay('user:5effc038-d181-4875-a11f-ec111a979d64'),
                f.actorDisplay('somchai'),
                f.actorDisplay(null),
            ]));
            """)
        self.assertEqual(out, ["5effc038", "somchai", ""])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiRouterTests(unittest.TestCase):
    def test_parse_hash_dashboard_default(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-router.js"))});
            process.stdout.write(JSON.stringify([r.parseHash(''), r.parseHash('#/'), r.parseHash('#garbage')]));
            """)
        self.assertEqual(out, [{"name": "dashboard", "sub": "matrix"}] * 3)

    def test_parse_hash_board_is_secondary_subview(self):
        """C4:矩阵是新默认(sub=matrix),看板降为 #/board 辅助入口(sub=board)。"""
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-router.js"))});
            process.stdout.write(JSON.stringify([
                r.parseHash('#/board'),
                r.buildBoardHash(),
                r.buildDashboardHash(),
            ]));
            """)
        self.assertEqual(
            out,
            [{"name": "dashboard", "sub": "board"}, "#/board", "#/"],
        )

    def test_parse_hash_client_view_and_default_view(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-router.js"))});
            process.stdout.write(JSON.stringify([
                r.parseHash('#/client/42/review'),
                r.parseHash('#/client/42'),
                r.parseHash('#/client/42/not-a-view'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"name": "client", "clientId": "42", "view": "review", "period": None},
                {"name": "client", "clientId": "42", "view": "wo", "period": None},
                {"name": "client", "clientId": "42", "view": "wo", "period": None},
            ],
        )

    def test_build_client_hash_round_trips_through_parse(self):
        # N1-P0-2:buildClientHash 加了第三参 period(全站深链丢账期修复),parseHash
        # 现在总是带 period 键(缺省 null)——period 往返/特殊字符/其它路由不受影响的
        # 专项覆盖见 tests/unit/test_ai_router_pure.py。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-router.js"))});
            const h = r.buildClientHash(7, 'pkg');
            process.stdout.write(JSON.stringify([h, r.parseHash(h)]));
            """)
        self.assertEqual(
            out,
            ["#/client/7/pkg", {"name": "client", "clientId": "7", "view": "pkg", "period": None}],
        )

    def test_clients_reports_settings_are_independent_top_level_routes(self):
        """EN-clients:导航禁用占位收口——三个侧栏入口各自独立顶层路由。"""
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-router.js"))});
            process.stdout.write(JSON.stringify([
                r.parseHash('#/clients'),
                r.parseHash('#/reports'),
                r.parseHash('#/settings'),
                r.buildClientsHash(), r.buildReportsHash(), r.buildSettingsHash(),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"name": "clients"},
                {"name": "reports"},
                {"name": "settings"},
                "#/clients",
                "#/reports",
                "#/settings",
            ],
        )

    def test_client_archive_hash_parses_tab_and_defaults_unknown_to_profile(self):
        # "clients" vs "client" 前缀不重叠——单客户档案页与按期操作页互不误判。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-router.js"))});
            process.stdout.write(JSON.stringify([
                r.parseHash('#/clients/9/supplier'),
                r.parseHash('#/clients/9'),
                r.parseHash('#/clients/9/not-a-tab'),
                r.buildClientArchiveHash(9, 'history'),
                r.parseHash('#/client/9/wo'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"name": "client-archive", "clientId": "9", "tab": "supplier"},
                {"name": "client-archive", "clientId": "9", "tab": "profile"},
                {"name": "client-archive", "clientId": "9", "tab": "profile"},
                "#/clients/9/history",
                {"name": "client", "clientId": "9", "view": "wo", "period": None},
            ],
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiStateTests(unittest.TestCase):
    def test_loading_html_has_no_business_text(self):
        out = _run_node(f"""
            const s = require({json.dumps(str(AI_DIR / "ai-state.js"))});
            process.stdout.write(JSON.stringify(s.loadingHtml()));
            """)
        self.assertIn('data-state="loading"', out)
        self.assertNotIn("<script", out)

    def test_empty_and_error_html_escape_and_carry_state(self):
        out = _run_node(f"""
            const s = require({json.dumps(str(AI_DIR / "ai-state.js"))});
            process.stdout.write(JSON.stringify([
                s.emptyHtml({{title: 'a<b', sub: 's'}}),
                s.errorHtml({{title: 't', sub: 's', retryLabel: 'retry'}}),
            ]));
            """)
        empty_html, error_html = out
        self.assertIn('data-state="empty"', empty_html)
        self.assertIn("a&lt;b", empty_html)  # 转义,不放行原样 HTML 注入
        self.assertIn('data-state="error"', error_html)
        self.assertIn('data-action="retry"', error_html)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiApiPureTests(unittest.TestCase):
    def test_map_api_error_key(self):
        out = _run_node(f"""
            const a = require({json.dumps(str(AI_DIR / "ai-api.js"))});
            process.stdout.write(JSON.stringify([
                a.mapApiErrorKey('workorder.not_found'),
                a.mapApiErrorKey(''),
                a.mapApiErrorKey(null),
            ]));
            """)
        self.assertEqual(out, ["err_workorder_not_found", "err_generic", "err_generic"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FieldLabelTests(unittest.TestCase):
    """fieldLabel 是查表 + 回落型格式化函数,随 W2 简化收口从 ai-board.js 搬来同类
    的 statusChip/money 身边——同一份测试跟着函数搬,断言不变。"""

    def test_known_field_uses_injected_lookup(self):
        out = _run_node(f"""
            global.at = (k) => (k === 'field_tax_due' ? '应缴税额' : k);
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify(f.fieldLabel('tax_due')));
            """)
        self.assertEqual(out, "应缴税额")

    def test_unknown_field_falls_back_to_raw_key(self):
        out = _run_node(f"""
            global.at = (k) => k;
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify(f.fieldLabel('some_future_field')));
            """)
        self.assertEqual(out, "some_future_field")

    def test_no_at_function_falls_back_to_raw_key(self):
        out = _run_node(f"""
            const f = require({json.dumps(str(AI_DIR / "ai-format.js"))});
            process.stdout.write(JSON.stringify(f.fieldLabel('sales_amount')));
            """)
        self.assertEqual(out, "sales_amount")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiIntakeRenderPureTests(unittest.TestCase):
    """收料视图(W4)的纯校验守门:金额解析(非负、两位小数、去千分位)、销项 payload 构造、
    上传前端预检(单文件 20MB;总张数不设上限,交给 splitBatches 分批)。HTML 拼装依赖
    at()/DOM 不在此测(交 W4 E2E)。"""

    def test_parse_amount_normalizes_and_rejects(self):
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            process.stdout.write(JSON.stringify([
                r.parseAmount('858780.16'), r.parseAmount('1,234,567.50'),
                r.parseAmount('  60114.61 '), r.parseAmount('-1'),
                r.parseAmount('1.234'), r.parseAmount('abc'), r.parseAmount(''),
            ]));
            """)
        self.assertEqual(out, ["858780.16", "1234567.50", "60114.61", None, None, None, None])

    def test_build_sales_payload_requires_both_amounts(self):
        out = _run_node(f"""
            {_REQUIRE_AI_FORMAT}
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            process.stdout.write(JSON.stringify([
                r.buildSalesPayload('858780.16', '60114.61', 'ยื่นเอง'),
                r.buildSalesPayload('100', 'bad', 'n'),
                r.buildSalesPayload('bad', '7', 'n'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"sales_amount": "858780.16", "output_vat": "60114.61", "note": "ยื่นเอง"},
                None,
                None,
            ],
        )

    def test_validate_files_allows_large_counts_caps_size(self):
        # G1 遗留 P0-2:后端 splitBatches 已把任意张数切成安全批,前端不再挡总数——
        # 104 张(超过旧 MAX_FILES=50 上限)必须放行;单文件超 20MB 仍被拦。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            const ok = [{{size: 1000}}, {{size: 2000}}];
            const manyFiles = Array.from({{length: 104}}, () => ({{size: 1}}));
            const tooBig = [{{size: r.MAX_BYTES + 1}}];
            process.stdout.write(JSON.stringify([
                r.validateFiles(ok), r.validateFiles(manyFiles), r.validateFiles(tooBig),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"ok": True},
                {"ok": True},
                {"ok": False, "errKey": "err_workorder_file_too_large"},
            ],
        )

    def test_split_batches_empty_and_single_file(self):
        # G1 真机:一次传 25 张 ~55MB 撞 prod nginx 50M 单请求挂死——splitBatches 按总体积/
        # 张数把选中文件切成安全批。边界:0 张不产批;1 张单独成 1 批(不因为"批"而空转)。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            process.stdout.write(JSON.stringify([
                r.splitBatches([]),
                r.splitBatches([{{size: 5}}]).map((b) => b.length),
            ]));
            """)
        self.assertEqual(out, [[], [1]])

    def test_split_batches_respects_byte_cap_exact_boundary(self):
        # 刚好等于字节上限的两文件仍并一批(边界不误切);再加一字节的第三个文件必须另开批。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            const cap = 350;
            const files = [{{size: 200}}, {{size: 150}}, {{size: 1}}];
            process.stdout.write(JSON.stringify(
                r.splitBatches(files, cap, 20).map((b) => b.reduce((s, f) => s + f.size, 0))
            ));
            """)
        self.assertEqual(out, [350, 1])

    def test_split_batches_respects_file_count_cap(self):
        # 张数上限独立于字节上限:每个文件都很小(总字节远不到上限),仍按 capCount 切批。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            const files = Array.from({{length: 45}}, () => ({{size: 1}}));
            process.stdout.write(JSON.stringify(
                r.splitBatches(files, 10 * 1024 * 1024, 20).map((b) => b.length)
            ));
            """)
        self.assertEqual(out, [20, 20, 5])

    def test_split_batches_solo_file_that_would_overflow_running_batch(self):
        # 单张文件本身在 per-file 上限内(≤ 批字节上限),但加进当前累积批会超批字节上限——
        # 不能拆散单文件,必须让它独占下一批,而不是把批撑爆或报错。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            const cap = 100;
            const files = [{{size: 80}}, {{size: 60}}];
            process.stdout.write(JSON.stringify(
                r.splitBatches(files, cap, 20).map((b) => b.map((f) => f.size))
            ));
            """)
        self.assertEqual(out, [[80], [60]])

    def test_merge_files_appends_second_batch_without_replacing_first(self):
        # UI 记债 #4:分两批选择,第二批追加不顶替(此前 setFiles 整份替换,第一批悄悄丢失)。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            const batch1 = [{{name: 'a.jpg', size: 100}}, {{name: 'b.jpg', size: 200}}];
            const batch2 = [{{name: 'c.jpg', size: 300}}];
            process.stdout.write(JSON.stringify(
                r.mergeFiles(batch1, batch2).map((f) => f.name)
            ));
            """)
        self.assertEqual(out, ["a.jpg", "b.jpg", "c.jpg"])

    def test_merge_files_dedupes_by_name_and_size(self):
        # 同名同字节视为同一份重选(浏览器 File 无稳定 id)——不重复计入列表。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-intake-render.js"))});
            const batch1 = [{{name: 'a.jpg', size: 100}}];
            const batch2 = [{{name: 'a.jpg', size: 100}}, {{name: 'b.jpg', size: 200}}];
            process.stdout.write(JSON.stringify(
                r.mergeFiles(batch1, batch2).map((f) => f.name + ':' + f.size)
            ));
            """)
        self.assertEqual(out, ["a.jpg:100", "b.jpg:200"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiIntakeManifestPureTests(unittest.TestCase):
    """IN-0b 收料诚实化(static/ai/ai-intake-manifest.js)的纯逻辑守门:文件夹拖入递归
    展平(含任意深度子目录 + 不支持件拒收点名)、zip 解出件数估算、队列态序列化/恢复。
    HTML 拼装(盘点条/密码卡/续传横幅)另见 AiIntakeManifestHtmlTests(stub at()/AI.state)。
    """

    _MODULE = json.dumps(str(AI_DIR / "ai-intake-manifest.js"))

    def test_flatten_file_tree_recurses_nested_subdirectories(self):
        # A1:文件夹拖入含任意深度子目录——两层子目录里的合规件都要展平出来。
        out = _run_node(f"""
            const r = require({self._MODULE});
            const tree = {{
                isDir: true, name: 'client_may', children: [
                    {{isDir: false, name: 'a.jpg', size: 100}},
                    {{isDir: true, name: 'sub', children: [
                        {{isDir: false, name: 'b.pdf', size: 200}},
                        {{isDir: true, name: 'deeper', children: [
                            {{isDir: false, name: 'c.png', size: 50}},
                        ]}},
                    ]}},
                ],
            }};
            const flat = r.flattenFileTree(tree);
            process.stdout.write(JSON.stringify(flat.files.map((f) => f.name).sort()));
            """)
        self.assertEqual(out, ["a.jpg", "b.pdf", "c.png"])

    def test_flatten_file_tree_rejects_empty_and_unsupported_leaves(self):
        # 0 字节 → reason_empty;扩展名不在白名单(.docx)→ reason_unsupported;不静默吞。
        out = _run_node(f"""
            const r = require({self._MODULE});
            const tree = [
                {{isDir: false, name: 'empty.jpg', size: 0}},
                {{isDir: false, name: 'notes.docx', size: 500}},
                {{isDir: false, name: 'ok.pdf', size: 500}},
            ];
            const flat = r.flattenFileTree(tree);
            process.stdout.write(JSON.stringify({{
                files: flat.files.map((f) => f.name),
                rejected: flat.rejected,
            }}));
            """)
        self.assertEqual(
            out,
            {
                "files": ["ok.pdf"],
                "rejected": [
                    {"name": "empty.jpg", "reasonKey": "intake_reason_empty"},
                    {"name": "notes.docx", "reasonKey": "intake_reason_unsupported"},
                ],
            },
        )

    def test_classify_folder_entry_allows_zip_and_heic(self):
        # IN-0a 已支持 zip 展开 + HEIC 转换,folder-drop 白名单须同口径放行,不能拦成
        # "不支持格式"(那是伪扩展名/损坏留给后端权威判定的两类之外的类别)。
        out = _run_node(f"""
            const r = require({self._MODULE});
            process.stdout.write(JSON.stringify([
                r.classifyFolderEntry({{name: 'bank.zip', size: 10}}).ok,
                r.classifyFolderEntry({{name: 'photo.heic', size: 10}}).ok,
                r.classifyFolderEntry({{name: 'readme.txt', size: 10}}).ok,
            ]));
            """)
        self.assertEqual(out, [True, True, False])

    def test_zip_expanded_count_estimates_extras_beyond_one_to_one(self):
        # 一批里非 zip 输入件必产出恰好 1 个登记项;超出部分即 zip 展开贡献。
        out = _run_node(f"""
            const r = require({self._MODULE});
            const batch = [{{name: 'a.jpg'}}, {{name: 'bank.zip'}}];
            process.stdout.write(JSON.stringify([
                r.zipExpandedCount(batch, 6),
                r.zipExpandedCount([{{name: 'a.jpg'}}, {{name: 'b.jpg'}}], 2),
                r.zipExpandedCount(batch, 0),
            ]));
            """)
        self.assertEqual(out, [5, 0, 0])

    def test_serialize_and_parse_queue_state_round_trips(self):
        out = _run_node(f"""
            const r = require({self._MODULE});
            const state = {{
                orderId: 'wo-1', total: 3,
                doneNames: ['a.jpg'], pendingNames: ['b.jpg', 'c.jpg'],
                failedNames: [], ts: 111,
            }};
            const parsed = r.parseQueueState(r.serializeQueueState(state));
            process.stdout.write(JSON.stringify(parsed));
            """)
        self.assertEqual(
            out,
            {
                "orderId": "wo-1",
                "total": 3,
                "doneNames": ["a.jpg"],
                "pendingNames": ["b.jpg", "c.jpg"],
                "failedNames": [],
                "ts": 111,
            },
        )

    def test_parse_queue_state_rejects_garbage(self):
        # 刷新续传横幅读到损坏/无关的 localStorage 值不能崩,诚实当"没有可续传的队列"。
        out = _run_node(f"""
            const r = require({self._MODULE});
            process.stdout.write(JSON.stringify([
                r.parseQueueState(null), r.parseQueueState('not json'),
                r.parseQueueState('{{}}'), r.parseQueueState('{{"orderId":42}}').orderId,
            ]));
            """)
        self.assertEqual(out, [None, None, None, "42"])

    def test_has_resumable_queue_true_only_with_leftover_names(self):
        out = _run_node(f"""
            const r = require({self._MODULE});
            const done = {{orderId: 'x', total: 2, doneNames: ['a','b'], pendingNames: [], failedNames: []}};
            const partial = {{orderId: 'x', total: 2, doneNames: ['a'], pendingNames: ['b'], failedNames: []}};
            process.stdout.write(JSON.stringify([
                r.hasResumableQueue(null), r.hasResumableQueue(done), r.hasResumableQueue(partial),
            ]));
            """)
        self.assertEqual(out, [False, False, True])


def _intake_at_stub():
    # 同 test_ai_client_import_pure.py::_at_stub 先例:非恒等 at(),证明 HTML 里真出现了
    # 翻译后的文案而不是原样漏 key;AII18N.lang 供 reasonText() 挑后端四语 message。
    return """
        global.window = global;
        global.AII18N = { lang: 'en' };
        global.at = function (key, vars) {
            var s = '[' + key + ']';
            if (vars) Object.keys(vars).forEach((k) => { s += ':' + vars[k]; });
            return s;
        };
        global.AI = { state: { esc: function (s) { return String(s == null ? '' : s); } } };
    """


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiIntakeManifestHtmlTests(unittest.TestCase):
    """盘点条/密码卡/续传横幅 HTML 拼装各态(stub at()/AI.state.esc,同
    ai-client-import-render.js 的 PreviewTableHtmlTests 先例)——不是只测数据结构,
    断言真出现在 HTML 字符串里的文件名/计数/拒收原因。"""

    _MODULE = json.dumps(str(AI_DIR / "ai-intake-manifest.js"))

    def _render(self, expr: str) -> str:
        return _run_node(f"""
            {_intake_at_stub()}
            require({self._MODULE});
            process.stdout.write(JSON.stringify({expr}));
            """)

    def test_manifest_html_empty_when_nothing_happened_yet(self):
        # 不假成功:零收进/零拒收/零 zip 解出时不渲染任何盘点条壳。
        html = self._render(
            "global.AI.intakeManifest.manifestHtml({accepted: 0, rejected: [], zipExpanded: 0})"
        )
        self.assertEqual(html, "")

    def test_manifest_html_shows_accepted_and_rejected_reason(self):
        html = self._render(
            "global.AI.intakeManifest.manifestHtml({accepted: 3, "
            "rejected: [{name: 'bad.docx', reasonKey: 'intake_reason_unsupported'}], "
            "zipExpanded: 0})"
        )
        self.assertIn("chip g", html)
        self.assertIn("3", html)
        self.assertIn("bad.docx", html)
        self.assertIn("[intake_reason_unsupported]", html)

    def test_manifest_html_shows_server_message_in_current_lang(self):
        # IN-0a 契约:后端 message 四语内嵌,前端直出当前语言不再自翻。
        html = self._render(
            "global.AI.intakeManifest.manifestHtml({accepted: 0, "
            "rejected: [{name: 'bank.pdf', "
            "message: {th: 'ผิดพลาด', en: 'Corrupt file', zh: '文件损坏', ja: '破損'}}], "
            "zipExpanded: 2})"
        )
        self.assertIn("Corrupt file", html)
        self.assertNotIn("ผิดพลาด", html)

    def test_password_card_html_shows_filename_and_wrong_hint(self):
        html = self._render(
            "global.AI.intakeManifest.passwordCardHtml("
            "{filename: 'statement.pdf', errKey: 'wrong'})"
        )
        self.assertIn("statement.pdf", html)
        self.assertIn("[intake_pw_wrong]", html)
        self.assertIn("ik-pw-submit", html)
        self.assertIn("ik-pw-skip", html)

    def test_password_card_html_empty_when_no_card(self):
        html = self._render("global.AI.intakeManifest.passwordCardHtml(null)")
        self.assertEqual(html, "")

    def test_resume_banner_html_empty_when_nothing_pending(self):
        html = self._render(
            "global.AI.intakeManifest.resumeBannerHtml("
            "{orderId: 'x', total: 2, doneNames: ['a','b'], pendingNames: [], failedNames: []})"
        )
        self.assertEqual(html, "")

    def test_resume_banner_html_shows_remaining_count(self):
        html = self._render(
            "global.AI.intakeManifest.resumeBannerHtml("
            "{orderId: 'x', total: 5, doneNames: ['a'], pendingNames: ['b','c'], "
            "failedNames: ['d']})"
        )
        self.assertIn("ik-resume-pick", html)
        self.assertIn("ik-resume-dismiss", html)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiPkgRenderPureTests(unittest.TestCase):
    """交付包视图(W5)的纯函数守门:证据文件名是否可当图片打开(状态诚实,xlsx/pdf 等
    非图片文件不硬塞进查看器碎图)、应缴/留抵展示口径(负数=留抵,取绝对值,不 clamp)。
    HTML 拼装依赖 at()/DOM 不在此测(交 W5 E2E)。"""

    def test_is_image_file_name_recognizes_common_photo_extensions_only(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-pkg-render.js"))});
            process.stdout.write(JSON.stringify([
                r.isImageFileName('IMG_2647.jpg'), r.isImageFileName('receipt.PNG'),
                r.isImageFileName('pos_may.xlsx'), r.isImageFileName('note.pdf'),
                r.isImageFileName(null), r.isImageFileName(''),
            ]));
            """)
        self.assertEqual(out, [True, True, False, False, False, False])

    def test_display_file_name_strips_uuid_prefix_only(self):
        # UI 记债 #1:落盘名 `{uuid}__原名` 只该剥壳给人看原名;非 uuid 形态的前缀
        # (CLI 直喂真实路径 IMG_2647.JPG,或用户原名本身含 `__`)不误切,原样返回。
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-pkg-render.js"))});
            process.stdout.write(JSON.stringify([
                r.displayFileName('a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4__IMG_2647.jpg'),
                r.displayFileName('deadbeef__ใบกำกับ.pdf'),
                r.displayFileName('IMG_2647.JPG'),
                r.displayFileName('my__report.xlsx'),
                r.displayFileName(null),
            ]));
            """)
        self.assertEqual(
            out,
            ["IMG_2647.jpg", "ใบกำกับ.pdf", "IMG_2647.JPG", "my__report.xlsx", ""],
        )

    def test_due_display_reports_refund_for_negative_tax_due(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-pkg-render.js"))});
            process.stdout.write(JSON.stringify([
                r.dueDisplay('30851.33'), r.dueDisplay('-120.50'), r.dueDisplay('0'),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"labelKey": "pkg_line_due", "amount": 30851.33},
                {"labelKey": "pkg_line_refund", "amount": 120.5},
                {"labelKey": "pkg_line_due", "amount": 0},
            ],
        )

    def test_kind_order_matches_five_deliverable_kinds(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-pkg-render.js"))});
            process.stdout.write(JSON.stringify(r.KIND_ORDER));
            """)
        self.assertEqual(
            out,
            [
                "pp30_draft",
                "ledger_workpaper",
                "bank_workpaper",
                "shadow_workpaper",
                "missing_doc_memo",
                "evidence_index",
            ],
        )


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiI18nStructureTests(unittest.TestCase):
    """i18n 词典是数据文件(同 console-i18n.js 先例,无 module.exports)——
    直接 eval 后校验四语 key 集合一致,防漏翻(某语言缺 key 会静默回落 zh,不易发现)。
    词典本体按语言拆成 4 个分片(单文件<500 行铁律),装配层 ai-i18n.js 依赖它们先
    挂上 window.__AI_I18N_*__,同 ai.html 里 4 个 <script> 排 ai-i18n.js 之前的顺序。"""

    def test_four_languages_have_identical_key_sets(self):
        # 分片 2(-2 后缀,G1b 起新词条落这里)一并装载——只查分片 1 会漏掉 -2 的漏翻。
        shards = "".join(
            f'require({json.dumps(str(AI_DIR / f"ai-i18n-{lang}.js"))});\n'
            f'require({json.dumps(str(AI_DIR / f"ai-i18n-{lang}-2.js"))});\n'
            for lang in ("zh", "th", "en", "ja")
        )
        out = _run_node(f"""
            global.window = global;
            global.localStorage = {{ getItem: () => null, setItem: () => {{}} }};
            {shards}
            require({json.dumps(str(AI_DIR / "ai-i18n.js"))});
            const d = global.AII18N.dict;
            const keys = Object.fromEntries(
                Object.keys(d).map((lang) => [lang, Object.keys(d[lang]).sort()])
            );
            process.stdout.write(JSON.stringify(keys));
            """)
        zh_keys = out["zh"]
        for lang in ("th", "en", "ja"):
            self.assertEqual(out[lang], zh_keys, f"{lang} 词典 key 集合与 zh 不一致")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class AiGatePureTests(unittest.TestCase):
    """Z1-a 登录卡/邀请制门面的纯函数守门:表单必填校验、登录失败错误 key 解析
    (API 结构化错误 vs 网络失败两类必须分开报,见 ai-gate.js 顶注)。DOM 挂载
    (mountLogin/mountInvited)靠 tests/e2e/_z1a_gate.spec.js 真浏览器覆盖。"""

    def test_validate_login_input_requires_both_fields(self):
        out = _run_node(f"""
            const g = require({json.dumps(str(AI_DIR / "ai-gate.js"))});
            process.stdout.write(JSON.stringify([
                g.validateLoginInput('zihao', 'secret1'),
                g.validateLoginInput('', 'secret1'),
                g.validateLoginInput('zihao', ''),
                g.validateLoginInput('  ', '  '),
                g.validateLoginInput(null, null),
            ]));
            """)
        self.assertEqual(
            out,
            [
                {"ok": True},
                {"ok": False, "errKey": "gate_err_required"},
                {"ok": False, "errKey": "gate_err_required"},
                {"ok": False, "errKey": "gate_err_required"},
                {"ok": False, "errKey": "gate_err_required"},
            ],
        )

    def test_resolve_login_error_key_splits_network_from_api_errors(self):
        out = _run_node(f"""
            const g = require({json.dumps(str(AI_DIR / "ai-gate.js"))});
            process.stdout.write(JSON.stringify([
                g.resolveLoginErrorKey({{status: 401, code: 'auth.invalid_credentials'}}),
                g.resolveLoginErrorKey({{status: 429, code: 'account_locked'}}),
                g.resolveLoginErrorKey({{status: 403, code: 'auth.account_disabled'}}),
                g.resolveLoginErrorKey(new TypeError('Failed to fetch')),
                g.resolveLoginErrorKey(null),
            ]));
            """)
        self.assertEqual(
            out,
            [
                "err_auth_invalid_credentials",
                "err_account_locked",
                "err_auth_account_disabled",
                "gate_err_network",
                "gate_err_network",
            ],
        )


if __name__ == "__main__":
    unittest.main()
