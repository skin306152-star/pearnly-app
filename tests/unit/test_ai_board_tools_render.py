#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_board_tools_render.py

看板工具条(2026-07-27 从事务所矩阵搬进看板的三样能力)纯函数守门:
  1. 三个筛选(缺料/待审/风险)的判据 —— 徽章码与逾期口径,含"顺延日优先"和
     "无需申报/已冻结不算逾期"两条易被忽略的分支;
  2. 「本期还缺哪几张单」—— pending_order 徽章 → 义务名清单(本期已开过单的客户不进表);
  3. 批量条 / 缺单条的 HTML —— 账期与义务名必须真进文案(只说"批量开单"等于让人猜期)。
  4. ai-i18n-board.js 分片 zh/th key 集合一致 + 每个 kb_ 词条都真被引用(分片不在主四语
     一致性测试的装载清单里,自己的闸自己带 · 同 ai-i18n-fail.js 先例)。

同 test_ai_billing_render.py 的 node subprocess require 手法——真 node 跑源文件。
node 侧无 window.at → t() 回退「key + 插值参数」,HTML 断言直接认 key 与参数值。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest
from pathlib import Path

from tests.unit._node_harness import AI_DIR, _run_node

TOOLS = str(AI_DIR / "ai-board-tools-render.js")
STATE = str(AI_DIR / "ai-state.js")

PRELUDE = f"""
    require({json.dumps(STATE)});
    const b = require({json.dumps(TOOLS)});
    """

# 一份贴着后端 /api/tax-profile/matrix 出参形状的矩阵响应(services/workorder/matrix.py::build)。
MATRIX = {
    "period": "2569-07",
    "clients": [
        {"id": 1, "name": "บริษัท เอ", "missing_order": True},
        {"id": 2, "name": "บริษัท บี", "missing_order": False},
    ],
    "obligation_codes": ["pnd1", "pp30"],
    "obligation_labels": {
        "pp30": {"zh": "增值税", "th": "ภ.พ.30"},
        "pnd1": {"zh": "预扣税", "th": "ภ.ง.ด.1"},
    },
    "cells": [
        {
            "client_id": 1,
            "obligation_code": "pp30",
            "badge": "pending_order",
            "due_efiling": "2569-08-23",
            "due_efiling_deferred": "2569-08-25",
        },
        {
            "client_id": 1,
            "obligation_code": "pnd1",
            "badge": "pending_order",
            "due_efiling": "2569-08-07",
            "due_efiling_deferred": "2569-08-07",
        },
        {
            "client_id": 2,
            "obligation_code": "pp30",
            "badge": "pending_review",
            "due_efiling": "2569-08-23",
            "due_efiling_deferred": "2569-08-25",
        },
    ],
}


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class OverdueTests(unittest.TestCase):
    def _overdue(self, cell, today):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.isOverdue({json.dumps(cell)}, {json.dumps(today)})));
            """)

    def test_deferred_due_wins_over_raw_due(self):
        # 周末/假日顺延:原始日已过但顺延日没到 → 不算逾期(拿原始日判会冤枉一批单)
        cell = {
            "badge": "missing_materials",
            "due_efiling": "2569-08-23",
            "due_efiling_deferred": "2569-08-25",
        }
        self.assertFalse(self._overdue(cell, "2569-08-24"))
        self.assertTrue(self._overdue(cell, "2569-08-26"))

    def test_falls_back_to_raw_due_when_deferred_missing(self):
        cell = {"badge": "missing_materials", "due_efiling": "2569-08-23"}
        self.assertTrue(self._overdue(cell, "2569-08-24"))

    def test_settled_badges_are_never_overdue(self):
        for badge in ("no_need", "frozen"):
            cell = {"badge": badge, "due_efiling_deferred": "2569-08-01"}
            self.assertFalse(self._overdue(cell, "2569-09-01"), badge)

    def test_no_due_date_is_not_overdue(self):
        self.assertFalse(self._overdue({"badge": "missing_materials"}, "2569-09-01"))

    def test_today_is_bangkok_calendar_not_utc(self):
        # UTC 的"今天"在曼谷 00:00-07:00 还停在昨天 —— 拿 UTC 当尺子,刚过期的单要晚
        # 7 小时才标红。2026-07-27T18:30Z = 曼谷 07-28 01:30。
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(
                b.todayIsoBangkok(new Date('2026-07-27T18:30:00Z'))
            ));
            """)
        self.assertEqual(out, "2026-07-28")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class MatchesFiltersTests(unittest.TestCase):
    def _match(self, cells, filters, today="2569-08-01"):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(
                b.matchesFilters({json.dumps(cells)}, {json.dumps(filters)}, {json.dumps(today)})
            ));
            """)

    def test_no_filter_keeps_everything(self):
        self.assertTrue(self._match([], []))

    def test_missing_and_review_read_backend_badges(self):
        missing = [{"badge": "missing_materials"}]
        review = [{"badge": "pending_review"}]
        self.assertTrue(self._match(missing, ["missing"]))
        self.assertFalse(self._match(missing, ["review"]))
        self.assertTrue(self._match(review, ["review"]))

    def test_any_cell_hit_keeps_the_card(self):
        # 筛选问的是「这个客户本期有没有这类事」,不是逐格隐藏
        cells = [{"badge": "no_need"}, {"badge": "missing_materials"}]
        self.assertTrue(self._match(cells, ["missing"]))

    def test_multiple_filters_are_or_not_and(self):
        self.assertTrue(self._match([{"badge": "pending_review"}], ["missing", "review"]))

    def test_risk_filter_uses_overdue_judgement(self):
        cells = [{"badge": "missing_materials", "due_efiling_deferred": "2569-07-25"}]
        self.assertTrue(self._match(cells, ["risk"]))
        self.assertFalse(self._match(cells, ["risk"], today="2569-07-20"))

    def test_client_without_cells_is_filtered_out(self):
        # 本期一格义务都没物化的客户,在任何筛选下都不该冒充命中
        self.assertFalse(self._match([], ["missing"]))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class MissingByClientTests(unittest.TestCase):
    def _missing(self, lang="zh"):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(
                b.missingByClient({json.dumps(MATRIX)}, {json.dumps(lang)})
            ));
            """)

    def test_answers_which_orders_are_missing_this_period(self):
        out = self._missing()
        self.assertEqual(sorted(out.keys()), ["1"])  # 本期已开过单的客户 2 不进表
        self.assertEqual(out["1"]["period"], "2569-07")
        # 截止日早的排前面(先到期的先开单)
        self.assertEqual(out["1"]["names"], ["预扣税", "增值税"])

    def test_names_follow_current_language(self):
        self.assertEqual(self._missing("th")["1"]["names"], ["ภ.ง.ด.1", "ภ.พ.30"])

    def test_unknown_obligation_code_degrades_to_the_code(self):
        matrix = {
            "period": "2569-07",
            "clients": [{"id": 3, "name": "C", "missing_order": True}],
            "cells": [{"client_id": 3, "obligation_code": "pnd53", "badge": "pending_order"}],
        }
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.missingByClient({json.dumps(matrix)}, 'zh')));
            """)
        self.assertEqual(out["3"]["names"], ["pnd53"])

    def test_client_with_no_materialized_obligations_gets_empty_names(self):
        # 一格义务都没物化 → 只知道"没开单",不知道缺哪几张:names 为空,渲染层退成一句话
        matrix = {
            "period": "2569-07",
            "clients": [{"id": 9, "name": "D", "missing_order": True}],
            "cells": [],
        }
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.missingByClient({json.dumps(matrix)}, 'zh')));
            """)
        self.assertEqual(out["9"], {"period": "2569-07", "names": []})

    def test_null_matrix_yields_empty_map(self):
        # 矩阵端点失败(权限/网络)时看板要能照常渲染,不是整块炸掉
        out = _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.missingByClient(null, 'zh')));
            """)
        self.assertEqual(out, {})


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class MissingStripHtmlTests(unittest.TestCase):
    def _strip(self, missing, client):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.missingStripHtml(
                {json.dumps(missing)}, {json.dumps(client)}
            )));
            """)

    def test_lists_the_missing_obligations_with_a_checkbox(self):
        out = self._strip(
            {"period": "2569-07", "names": ["增值税", "预扣税"]}, {"id": 7, "name": "A"}
        )
        self.assertIn("kb_missing_list", out)
        self.assertIn("2569-07", out)
        self.assertIn("增值税、预扣税", out)
        self.assertIn('data-client-id="7"', out)
        self.assertIn('type="checkbox"', out)

    def test_unknown_obligations_degrade_to_one_honest_line(self):
        out = self._strip({"period": "2569-07", "names": []}, {"id": 7, "name": "A"})
        self.assertIn("kb_missing_unknown", out)
        self.assertNotIn("kb_missing_list", out)

    def test_no_missing_info_renders_nothing(self):
        self.assertEqual(self._strip(None, {"id": 7, "name": "A"}), "")

    def test_client_name_is_escaped_in_the_aria_label(self):
        out = self._strip(
            {"period": "2569-07", "names": []}, {"id": 7, "name": '<img src=x onerror="1">'}
        )
        self.assertNotIn("<img", out)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BulkBarHtmlTests(unittest.TestCase):
    def _bar(self, state):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(b.bulkBarHtml({json.dumps(state)})));
            """)

    def test_shows_selected_count_and_the_period_it_will_open(self):
        out = self._bar({"count": 3, "period": "2569-07"})
        self.assertIn("kb_bulk_selected 3", out)
        self.assertIn("kb_bulk_open 2569-07", out)
        self.assertIn('data-action="bulk-open"', out)
        self.assertIn('data-action="bulk-clear"', out)

    def test_busy_state_disables_the_button_and_swaps_the_label(self):
        out = self._bar({"count": 3, "period": "2569-07", "busy": True})
        self.assertIn("kb_bulk_open_busy", out)
        self.assertIn("disabled", out)

    def test_result_note_is_rendered_when_present(self):
        out = self._bar({"count": 2, "period": "2569-07", "note": "已开出 2 张单"})
        self.assertIn("已开出 2 张单", out)

    def test_no_note_no_empty_note_slot(self):
        self.assertNotIn("kb-bulk-note", self._bar({"count": 2, "period": "2569-07"}))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class BoardI18nShardTests(unittest.TestCase):
    """zh/th key 一致 + 被引用 key 必须真实存在(分片不在主四语一致性测试的装载清单里,
    自己的闸自己带 · 同 ai-i18n-fail.js 先例)。"""

    def _shard_keys(self):
        return _run_node(f"""
            global.window = global;
            global.__AI_I18N_ZH__ = {{}};
            global.__AI_I18N_TH__ = {{}};
            require({json.dumps(str(AI_DIR / "ai-i18n-board.js"))});
            process.stdout.write(JSON.stringify({{
                zh: Object.keys(global.__AI_I18N_ZH__).sort(),
                th: Object.keys(global.__AI_I18N_TH__).sort(),
            }}));
            """)

    def test_zh_and_th_key_sets_identical(self):
        keys = self._shard_keys()
        self.assertTrue(keys["zh"], "分片 zh 词条为空")
        self.assertEqual(keys["zh"], keys["th"], "th 词典 key 集合与 zh 不一致")

    def test_every_kb_key_is_referenced_and_every_reference_exists(self):
        zh = set(self._shard_keys()["zh"])
        referenced = set()
        for name in ("ai-board-tools-render.js", "ai-board-bulk.js", "ai-dashboard.js"):
            text = (AI_DIR / name).read_text(encoding="utf-8")
            referenced |= set(re.findall(r"\bkb_[a-z0-9_]+", text))
        missing = sorted(k for k in referenced if k not in zh)
        self.assertEqual(missing, [], f"代码引用了词典里不存在的 key: {missing}")
        unused = sorted(k for k in zh if k not in referenced)
        self.assertEqual(unused, [], f"词典里有没人引用的死 key: {unused}")


class BoardToolsWiringTests(unittest.TestCase):
    """新模块不进 bundle / 新词典不进 ai.html / 工具条锚点不在 HTML 里 = 上线即死代码。"""

    def setUp(self):
        self.root = Path(AI_DIR).parents[1]
        self.html = (AI_DIR / "ai.html").read_text(encoding="utf-8")

    def test_new_modules_are_in_the_ai_bundle(self):
        text = (self.root / "scripts" / "build-home-js.mjs").read_text(encoding="utf-8")
        for f in ("ai/ai-board-tools-render.js", "ai/ai-board-bulk.js"):
            self.assertIn(f"'{f}'", text)

    def test_board_dictionary_is_loaded_and_cache_busted(self):
        self.assertIn("ai-i18n-board.js", self.html)
        gate = (self.root / "scripts" / "check_cachebust.py").read_text(encoding="utf-8")
        self.assertIn("/static/ai/ai-i18n-board.js", gate)

    def test_board_section_carries_the_filter_chips_and_bulk_bar(self):
        # 三个筛选与批量条的锚点必须真在看板段落里(矩阵自己那三颗 chip 原样留着)
        for anchor in ('id="boardTools"', 'id="boardFilters"', 'id="boardBulkBar"'):
            self.assertIn(anchor, self.html)
        for f in ("missing", "review", "risk"):
            self.assertIn(f'class="kb-chip" data-filter="{f}"', self.html)

    def test_board_owns_its_styles_instead_of_borrowing_the_matrix_sheet(self):
        # 看板新样式必须落在 ai-dashboard.css:借 ai-matrix.css 的 .mf-chip/.mx-* 会把
        # 两个长期并存的视图焊死,改矩阵间距顺手改坏看板。
        css = (AI_DIR / "ai-dashboard.css").read_text(encoding="utf-8")
        for cls in (".kb-tools", ".kb-chip", ".kmiss", ".kb-bulkbar", ".kb-noresults"):
            self.assertIn(cls, css)
        dash = (AI_DIR / "ai-dashboard.js").read_text(encoding="utf-8")
        self.assertNotIn("mx-noresults", dash)
        self.assertNotIn("mf-chip", dash)


if __name__ == "__main__":
    unittest.main()
