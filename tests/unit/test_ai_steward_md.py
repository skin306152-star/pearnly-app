# -*- coding: utf-8 -*-
"""管家正文迷你 markdown(static/ai/ai-steward-md.js)。

锁:①所有文本先 esc 再套标记(后端回复里的 <script> 永远是字面量);②表格数字列
标 num 且整表包横滚容器;③代码块不传复制文案就不摆按钮(没字的按钮更糟);
④段落单换行折 <br>、粗体/行内码只在成对标记时生效。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_MD = json.dumps(str(AI_DIR / "ai-steward-md.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class StewardMdTests(unittest.TestCase):
    def _render(self, src, opts="{}"):
        return _run_node(f"""
            const md = require({_MD});
            process.stdout.write(JSON.stringify(md.render({json.dumps(src)}, {opts})));
            """)

    def test_html_is_escaped_before_markup(self):
        out = self._render("**加粗** 与 <script>alert(1)</script> 与 `code<b>`")
        self.assertIn("<b>加粗</b>", out)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("<code>code&lt;b&gt;</code>", out)

    def test_table_marks_numeric_columns_and_wraps_scroll(self):
        out = self._render(
            "| 商户 | 金额 |\n| --- | --- |\n| 7-Eleven | ฿428.50 |\n| Makro | 856.00 |"
        )
        self.assertIn('class="stw-md-tblwrap"', out)
        self.assertIn('<th class="num">金额</th>', out)
        self.assertIn('<td class="num">฿428.50</td>', out)
        self.assertIn("<th>商户</th>", out)
        self.assertNotIn('<td class="num">Makro</td>', out)

    def test_code_block_copy_button_only_with_label(self):
        src = "```sql\nSELECT 1\n```"
        bare = self._render(src)
        self.assertIn("<pre>SELECT 1</pre>", bare)
        self.assertNotIn("stw-copy-md-code", bare)
        labeled = self._render(src, json.dumps({"codeCopyLabel": "复制"}))
        self.assertIn("stw-copy-md-code", labeled)
        self.assertIn(">复制</button>", labeled)

    def test_paragraph_linebreak_list_and_heading(self):
        out = self._render("### 标题\n第一行\n第二行\n\n- 甲\n- 乙")
        self.assertIn("<h4>标题</h4>", out)
        self.assertIn("第一行<br>第二行", out)
        self.assertIn("<ul><li>甲</li><li>乙</li></ul>", out)

    def test_empty_and_null_render_to_empty_string(self):
        self.assertEqual(self._render(""), "")
        out = _run_node(f"""
            const md = require({_MD});
            process.stdout.write(JSON.stringify(md.render(null)));
            """)
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
