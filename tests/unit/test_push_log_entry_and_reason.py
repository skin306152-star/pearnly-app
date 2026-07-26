# -*- coding: utf-8 -*-
"""推送日志入口 + 转人工原因人话(Zihao 2026-07-26 报的两处)。

一、推送日志早已从集成页拆成独立页(nav「Pearnly Cowork → 推送日志」),但录入工作台
    第 4 步结果页的「查看推送日志」按钮一直还往集成页跳 —— 点了看不到日志。
二、Express 转人工码 posting_needs_review:<inventory_usage> 没有人话映射,列表卡与详情
    抽屉都裸露 "EXPRESS_MANUAL: posting_needs_review:perpetual",泰国会计看不懂也不
    知道下一步该做什么。真实的下一步是在录入工作台【上传页右侧】的「过账去向 · 本批」
    指定 —— sideHtml() 只被 renderInvoiceUpload() 调用,且 posting_kind 在识别请求就要
    带上(见 dms-intake-invoice-recognize.ts 的注释),第 4 步只是把它带去推送。

顺带钉住教程:手册里原本把这两件当「已知现象」教用户绕行,修好后那些话必须同步改,
否则教程反过来教错(见 static/guide/content/{daily,overview}.json)。
"""

from __future__ import annotations

import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

POSTING_REVIEW_KEYS = (
    "erp-reason-posting-review",
    "erp-reason-posting-review-perpetual",
    "erp-reason-posting-review-mixed",
)


def _read(rel: str) -> str:
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


class PushLogEntryTests(unittest.TestCase):
    def test_result_page_button_goes_to_push_logs(self):
        text = _read("src/home/dms-intake-invoice.ts")
        self.assertTrue(
            "if (hit('dx-inv-view-push')) return (go('push-logs'), true);" in text,
            "结果页「查看推送日志」又跳回集成页了",
        )

    def test_push_logs_is_a_real_route(self):
        # 跳一个不在 VALID_ROUTES 的名字会被 routeTo 回落,按钮等于哑火。
        self.assertTrue("'push-logs'," in _read("src/home/route-table.ts"))

    def test_submit_hint_no_longer_points_at_integrations(self):
        # 第 4 步底部那句提示原本写「集成 → 推送日志」,路径已不成立。
        text = _read("static/i18n-data.js")
        self.assertEqual(text.count("'dxi-submit-hint':"), 4, "dxi-submit-hint 不是 4 语齐")
        self.assertFalse("集成 → 推送日志" in text, "提示里又出现「集成 → 推送日志」")
        self.assertFalse("Integrations → push log" in text)
        self.assertFalse("ศูนย์เชื่อมต่อ → บันทึกการส่ง" in text)
        self.assertFalse("連携センター → 送信ログ" in text)


class PostingReviewReasonTests(unittest.TestCase):
    def test_card_translates_posting_needs_review(self):
        text = _read("src/home/erp-log-card.ts")
        self.assertTrue("code === 'posting_needs_review'" in text, "转人工码的特判没了")
        # 后缀(perpetual/mixed)决定该跟会计说哪一句,合成一句就丢了可操作信息。
        self.assertTrue("perpetual: 'erp-reason-posting-review-perpetual'" in text)
        self.assertTrue("mixed: 'erp-reason-posting-review-mixed'" in text)

    def test_detail_drawer_shares_the_same_wording(self):
        # 后端 error_friendly 只覆盖 ERR_* 码,详情不接这份表就跟列表卡两个说法。
        text = _read("src/home/erp-log-detail.ts")
        self.assertTrue("_expressFriendlyReason" in text, "详情抽屉又裸露原始码了")

    def test_all_three_keys_are_four_language(self):
        text = _read("static/i18n-data.js")
        for key in POSTING_REVIEW_KEYS:
            needle = "'" + key + "':"  # 带收尾引号+冒号,免得前缀键互相误撞
            self.assertEqual(text.count(needle), 4, f"i18n 键 {key} 不是 4 语齐")


class GuideMatchesShippedBehaviourTests(unittest.TestCase):
    """手册不能再教「按钮会跳错、请走侧栏绕行」——那是修好之前的事。"""

    def test_guide_no_longer_teaches_the_workaround(self):
        daily = _read("static/guide/content/daily.json")
        overview = _read("static/guide/content/overview.json")
        self.assertFalse("并非推送日志页" in daily, "手册还在说「查看推送日志」跳集成页")
        self.assertFalse("给出的路径与实际位置不符" in daily, "手册还在说底部提示路径不符")
        self.assertFalse("有两个按钮会跳转到其他页面" in overview, "手册还在说两个按钮都跳集成页")


if __name__ == "__main__":
    unittest.main()
