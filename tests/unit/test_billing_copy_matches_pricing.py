# -*- coding: utf-8 -*-
"""订阅文案里的数字必须等于真实计费常量(四语同锁)。

2026-08-01 真实事故:文案写「每月额度 / ต่อเดือน / monthly quota」,而计费周期是订阅日起
30 天,月费也是订阅当天预扣的。客户照文案自己算账单,算出「月底再扣 60 บาท」——实际
那 40 张在额度内一分不扣,而他余额已经不够下一次续订。文案说的和代码做的是两回事。

这类漂移没法靠人盯:改 SUBSCRIPTION_CYCLE_DAYS 的人不会想起去翻四个语言块。本测把
「屏幕上印的数字」钉在 pricing.py 的常量上,常量一动,四语文案没跟上就红。

只断言数字,不断言措辞——措辞怎么写是产品的事,数字对不上是缺陷。
"""

import re
import unittest
from pathlib import Path

from scripts.check_i18n import _unquote, iter_i18n_entries
from services.billing.pricing import (
    PDF_TIER1_LIMIT_V21,
    PDF_TIER1_PRICE_V21,
    PDF_TIER2_PRICE_V21,
    SUBSCRIPTION_CYCLE_DAYS,
)

ROOT = Path(__file__).resolve().parents[2]
I18N_PATH = ROOT / "static" / "i18n-data.js"
DASHBOARD_TS = ROOT / "src" / "home" / "page-dashboard.ts"
LANGS = ("zh", "en", "th", "ja")
RULE_KEYS = ("sub-rules-title",) + tuple(f"sub-rule-{i}" for i in range(1, 6))

# 值里可能有转义引号,按整段单引号串取,别用 `[^']*`
_VALUE = r"'(?:\\.|[^'\\])*'"


def _values(text: str, want: set) -> dict:
    """{(语言, 键): 值} —— 行号由 check_i18n 的 token 扫描给,值在该行按串取。"""
    lines = text.splitlines()
    out = {}
    for lang, key, line_no in iter_i18n_entries(text):
        if lang not in LANGS or key not in want:
            continue
        line = lines[line_no - 1]
        m = re.search(re.escape(f"'{key}'") + r"\s*:\s*(" + _VALUE + ")", line)
        if m:
            out[(lang, key)] = _unquote(m.group(1))
    return out


class BillingCopyMatchesPricing(unittest.TestCase):
    """文案里的周期天数 / 阶梯价 = pricing.py 的常量。"""

    @classmethod
    def setUpClass(cls):
        cls.text = I18N_PATH.read_text(encoding="utf-8")
        cls.want = {"sub-per-month", "sub-rule-1", "sub-rule-2"}
        cls.vals = _values(cls.text, cls.want)

    def test_every_language_block_has_the_billing_copy(self):
        """先证据齐了再谈内容:少一条就是漏译,后面的断言会假绿地跳过它。"""
        missing = [(l, k) for l in LANGS for k in self.want if (l, k) not in self.vals]
        self.assertEqual([], missing, f"i18n 缺这些订阅文案: {missing}")

    def test_cycle_days_appear_in_period_copy(self):
        """周期天数一改,四语的「/30 天」和规则第 2 条必须同改。"""
        days = str(SUBSCRIPTION_CYCLE_DAYS)
        for lang in LANGS:
            for key in ("sub-per-month", "sub-rule-2"):
                v = self.vals[(lang, key)]
                self.assertIn(
                    days,
                    v,
                    f"{lang}.{key} 没写周期天数 {days}(计费周期=订阅日起 {days} 天): {v}",
                )

    def test_no_calendar_month_claim_in_period_copy(self):
        """价格行不能只写「月」:周期不是自然月,写月就等于告诉客户月底结算。"""
        for lang in LANGS:
            v = self.vals[(lang, "sub-per-month")]
            self.assertNotIn(
                v.strip(),
                {"月", "mo", "month", "เดือน", "รายเดือน"},
                f"{lang}.sub-per-month 写成了自然月口径: {v}",
            )

    def test_payg_tier_numbers_match_pricing(self):
        """按量阶梯(前 N 张 ฿x,之后 ฿y)三个数都得跟 pricing.py 一致。"""
        for lang in LANGS:
            v = self.vals[(lang, "sub-rule-1")]
            for num in (
                str(PDF_TIER1_LIMIT_V21),
                f"{PDF_TIER1_PRICE_V21:.2f}",
                f"{PDF_TIER2_PRICE_V21:.2f}",
            ):
                self.assertIn(num, v, f"{lang}.sub-rule-1 与按量定价不一致(缺 {num}): {v}")


class BillingRulesStayOnThePage(unittest.TestCase):
    """规则那几条必须真挂在页面上,不能只躺在词典里。

    2026-06-28 `c240b84a` 把首页底部「计费规则 + 最近账单」整片换成记录预览框,规则块
    跟着一起没了 —— 提交信息通篇在讲记录框,没人发现规则也被端走了。之后产品里没有任何
    地方讲计费周期,7 个键成了孤儿,而 i18n 引用闸只查「代码引的键有没有定义」,反方向
    (定义了的键还有没有人用)它不管,于是这块少了一年都不会红。
    """

    def test_rules_panel_renders_every_rule_key(self):
        src = DASHBOARD_TS.read_text(encoding="utf-8")
        missing = [k for k in RULE_KEYS if f'data-i18n="{k}"' not in src]
        self.assertEqual(
            [],
            missing,
            f"page-dashboard.ts 不再渲染这些计费规则: {missing} —— 删之前先想清楚"
            "用户从哪知道周期怎么算(上次这么删,客户只能写邮件来问)",
        )


if __name__ == "__main__":
    unittest.main()
