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
class AiRouterTests(unittest.TestCase):
    def test_parse_hash_dashboard_default(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-router.js"))});
            process.stdout.write(JSON.stringify([r.parseHash(''), r.parseHash('#/'), r.parseHash('#garbage')]));
            """)
        self.assertEqual(out, [{"name": "dashboard"}] * 3)

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
                {"name": "client", "clientId": "42", "view": "review"},
                {"name": "client", "clientId": "42", "view": "wo"},
                {"name": "client", "clientId": "42", "view": "wo"},
            ],
        )

    def test_build_client_hash_round_trips_through_parse(self):
        out = _run_node(f"""
            const r = require({json.dumps(str(AI_DIR / "ai-router.js"))});
            const h = r.buildClientHash(7, 'pkg');
            process.stdout.write(JSON.stringify([h, r.parseHash(h)]));
            """)
        self.assertEqual(
            out, ["#/client/7/pkg", {"name": "client", "clientId": "7", "view": "pkg"}]
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
class AiI18nStructureTests(unittest.TestCase):
    """i18n 词典是数据文件(同 console-i18n.js 先例,无 module.exports)——
    直接 eval 后校验四语 key 集合一致,防漏翻(某语言缺 key 会静默回落 zh,不易发现)。"""

    def test_four_languages_have_identical_key_sets(self):
        out = _run_node(f"""
            global.window = global;
            global.localStorage = {{ getItem: () => null, setItem: () => {{}} }};
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


if __name__ == "__main__":
    unittest.main()
