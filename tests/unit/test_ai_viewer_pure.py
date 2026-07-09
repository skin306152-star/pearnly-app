#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_viewer_pure.py

Pearnly AI · ai-viewer.js(原件查看器·生产同款交互框架移植)纯函数守门——同
test_ai_pure_modules.py 先例,真 node 直接 require 源文件断言输出,不进浏览器。
只测无 DOM 依赖的那一半:imageViewerHtml(骨架 HTML 生成 + 转义)与 loadUrl/preload
(LRU 缓存 + 在飞请求合并,不重复调 loader)。mountViewer/remountViewer 要真 DOM,
交给 tests/e2e/_w3_review_local.spec.js 的真浏览器用例覆盖。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

# ai-viewer.js 的 esc() 转发给 AI.state.esc(照 ai-format.js escHtml 先例,没挂时退化成
# 不转义直通)——node 单测独立进程里没人挂 AI.state,这里先 require ai-state.js 把它挂上
# globalThis,后续 require 的 ai-viewer.js 才能真正转义(否则下面几条转义断言全假绿)。
_REQUIRE_AI_STATE = f'require({json.dumps(str(AI_DIR / "ai-state.js"))});\n'


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ImageViewerHtmlTests(unittest.TestCase):
    def test_renders_viewer_skeleton_with_text(self):
        out = _run_node(f"""
            {_REQUIRE_AI_STATE}
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            process.stdout.write(JSON.stringify(
                v.imageViewerHtml({{hint: 'H', noimg: 'N', loading: 'L'}})
            ));
            """)
        self.assertIn('class="pv-viewer"', out)
        self.assertIn('class="pv-img"', out)
        self.assertIn('class="pv-hint"', out)
        self.assertIn(">H<", out)
        self.assertIn('class="pv-empty">N<', out)
        self.assertIn('class="pv-spin"', out)
        self.assertIn(">L<", out)
        self.assertIn('class="pv-tools"', out)
        self.assertIn('class="pv-zoom"', out)

    def test_no_pager_markup_single_image_endpoint_has_no_page_count(self):
        # 工单 item 原图端点是单图(无 X-Page-Count)——生产版翻页器整段不该移植进来。
        out = _run_node(f"""
            {_REQUIRE_AI_STATE}
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            process.stdout.write(JSON.stringify(v.imageViewerHtml({{}})));
            """)
        self.assertNotIn("pv-pager", out)
        self.assertNotIn("pv-pgnum", out)
        self.assertNotIn('data-z="prev"', out)
        self.assertNotIn('data-z="next"', out)

    def test_hint_omitted_when_not_provided(self):
        out = _run_node(f"""
            {_REQUIRE_AI_STATE}
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            process.stdout.write(JSON.stringify(v.imageViewerHtml({{noimg: 'N', loading: 'L'}})));
            """)
        self.assertNotIn("pv-hint", out)

    def test_text_is_escaped_against_markup_injection(self):
        out = _run_node(f"""
            {_REQUIRE_AI_STATE}
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            process.stdout.write(JSON.stringify(
                v.imageViewerHtml({{hint: '<b>x</b>', noimg: '"q"', loading: 'a&b'}})
            ));
            """)
        self.assertNotIn("<b>x</b>", out)
        self.assertIn("&lt;b&gt;", out)
        self.assertIn("&quot;q&quot;", out)
        self.assertIn("a&amp;b", out)

    def test_tool_buttons_present_without_pager(self):
        out = _run_node(f"""
            {_REQUIRE_AI_STATE}
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            const html = v.imageViewerHtml({{}});
            process.stdout.write(JSON.stringify(
                ['in', 'out', 'rot', 'reset', 'full'].map(
                    (z) => html.indexOf('data-z="' + z + '"') >= 0
                )
            ));
            """)
        self.assertEqual(out, [True, True, True, True, True])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class LoadUrlCacheTests(unittest.TestCase):
    def test_null_key_resolves_null_without_calling_loader(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            let calls = 0;
            v.loadUrl(null, () => {{ calls++; return Promise.resolve('blob:x'); }}).then((url) => {{
                process.stdout.write(JSON.stringify([url, calls]));
            }});
            """)
        self.assertEqual(out, [None, 0])

    def test_second_call_same_key_hits_cache_loader_called_once(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            let calls = 0;
            const loader = () => {{ calls++; return Promise.resolve('blob:one'); }};
            v.loadUrl('k1', loader).then(() => v.loadUrl('k1', loader)).then((url) => {{
                process.stdout.write(JSON.stringify([url, calls]));
            }});
            """)
        self.assertEqual(out, ["blob:one", 1])

    def test_concurrent_calls_same_key_merge_into_one_loader_call(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            let calls = 0;
            const loader = () => {{ calls++; return Promise.resolve('blob:concurrent'); }};
            Promise.all([v.loadUrl('k2', loader), v.loadUrl('k2', loader)]).then((urls) => {{
                process.stdout.write(JSON.stringify([urls, calls]));
            }});
            """)
        self.assertEqual(out, [["blob:concurrent", "blob:concurrent"], 1])

    def test_loader_rejection_resolves_to_null_not_throw(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            v.loadUrl('k3', () => Promise.reject(new Error('boom'))).then((url) => {{
                process.stdout.write(JSON.stringify(url));
            }});
            """)
        self.assertIsNone(out)

    def test_preload_warms_cache_so_later_loadurl_skips_loader(self):
        out = _run_node(f"""
            const v = require({json.dumps(str(AI_DIR / "ai-viewer.js"))});
            let calls = 0;
            const loader = () => {{ calls++; return Promise.resolve('blob:pre'); }};
            v.preload('k4', loader);
            setTimeout(() => {{
                v.loadUrl('k4', loader).then((url) => {{
                    process.stdout.write(JSON.stringify([url, calls]));
                }});
            }}, 20);
            """)
        self.assertEqual(out, ["blob:pre", 1])


if __name__ == "__main__":
    unittest.main()
