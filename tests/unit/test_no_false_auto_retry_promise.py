#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_no_false_auto_retry_promise.py

「稍后自动重试」这句话只有一条路上是真的,这道闸把它钉在那条路上。

两条路都会撞上同一个桥端错误码 ACCOUNT_BUSY_LOCKED(Express 正开着账套):

  ① 旧队列(小助手来领 · services/erp/express_push/agent_store.ack 的 waiting_lock 分支)
     保持 status='pending'、放掉租约,下一拍 lease_pending 会把同一行再领走 —— 真的会自动
     重来,而且不烧重试次数。这条路的文案(erp-status-waiting-lock / erp-retry-*)可以承诺,
     本闸不碰。
  ② 桥直写(管家写工具 · services/steward/erp_push_tool)落 status='failed' 且**不设
     next_retry_at**,后台重试队列(push_retry.list_logs_due_for_retry 只扫
     next_retry_at IS NOT NULL)永远扫不到这一行。这条路上说「稍后自动重试」,会计就在等
     一个不会来的重试。

erp-reason-account-busy 只在 ✗ 失败卡的摘要条上渲染(erp-log-card 的 reasonStrip 有
statusClass==='fail' 的门槛),而真会自动重领的那条路是 pending ⟳,根本走不到 —— 所以
这条文案面向的永远是②,旧文案的「稍后自动重试」在它唯一的落点上是假的。

判据只禁**肯定式**承诺:「不会自动重推」这类否定句必须过得去,否则说实话反而被闸拦。
"""

from __future__ import annotations


import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
I18N_DATA = PROJECT_ROOT / "static" / "i18n-data.js"

# 各语肯定式「系统会自己再推一次」的说法。故意不收单独的「อัตโนมัติ / automatically」:
# 那两个词也出现在「自动重连」「自动判定」里,收进来就是把闸变成噪音。
_PROMISES = (
    "自动重试",
    "自动重推",
    "自动再推",
    "自动重领",
    "自动继续",
    "จะลองใหม่อัตโนมัติ",
    "ลองใหม่อัตโนมัติ",
    "จะส่งซ้ำให้เอง",
    "จะทำงานต่อเอง",
    "retry automatically",
    "automatically retry",
    "auto-retry",
    "will retry",
    "自動で再試行",
    "自動再試行",
    "自動的に再試行",
)


# 否定标记。「系统不会自动再推」「ระบบจะไม่ส่งซ้ำให้เอง」是本轮要写的实话,不能被自己的闸拦下。
# 中/泰/英的否定在承诺词之前,日语的否定是词尾(…再試行しません),所以前后各看一个窗口。
_NEG_BEFORE = ("不", "无", "ไม่", "not", "no ", "never", "won't", "n't")
_NEG_AFTER = ("ません", "ない", "ず")


def _promises_in(text: str) -> list[str]:
    """text 里**肯定式**的自动重试承诺。被否定掉的不算 —— 说「不会自动重推」正是本轮的目的。"""
    low = text.lower()
    found = []
    for promise in _PROMISES:
        start = low.find(promise.lower())
        while start != -1:
            before = low[max(0, start - 10) : start]
            after = low[start + len(promise) : start + len(promise) + 6]
            negated = any(n in before for n in _NEG_BEFORE) or any(n in after for n in _NEG_AFTER)
            if not negated:
                found.append(promise)
                break
            start = low.find(promise.lower(), start + 1)
    return found


def _i18n_value(key: str) -> list[str]:
    """从 static/i18n-data.js 逐行抓某个键的所有语言取值(四语各一行,顺序即 zh/en/th/ja)。

    不 import 也不执行那个 715KB 的 JS —— 它是浏览器全局脚本,单测里跑不起来。
    行内正则足够:这份词典每条恒为「'key': '值',」一行。
    """
    src = I18N_DATA.read_text(encoding="utf-8")
    return re.findall(rf"'{re.escape(key)}':\s*'((?:[^'\\]|\\.)*)'", src)


class AccountBusyCopyTests(unittest.TestCase):
    def test_the_key_exists_in_all_four_languages(self):
        """判据自检:抓不到值的话,下面「不含承诺」会因为抓了个空而白绿。"""
        values = _i18n_value("erp-reason-account-busy")
        self.assertEqual(len(values), 4, f"四语没齐(抓到 {len(values)} 条)")
        for v in values:
            self.assertTrue(v.strip())

    def test_no_language_promises_an_automatic_retry(self):
        for value in _i18n_value("erp-reason-account-busy"):
            found = _promises_in(value)
            self.assertEqual(
                found,
                [],
                f"桥直写失败卡上承诺了自动重试({found}),而这条路不设 next_retry_at:{value}",
            )

    def test_every_language_points_at_something_the_accountant_can_do(self):
        """光把假话删掉不算修好 —— 说了不会自动重来,就得告诉她该动哪一下。"""
        # 各语对应「Express」+「关掉/close/ปิด/閉じ」+ 重推按钮的说法。
        wants = (("Express", "关掉", "重试推送"), ("Express", "close", "Retry push"),
                 ("Express", "ปิด", "ลองส่งใหม่"), ("Express", "閉じ", "再送信"))  # fmt: skip
        values = _i18n_value("erp-reason-account-busy")
        for value, want in zip(values, wants):
            for token in want:
                self.assertIn(token, value, f"少了出路里的「{token}」:{value}")


class TruthfulLaneKeepsItsPromiseTests(unittest.TestCase):
    """反向自检:真会自动重领那条路的文案不许被这次收紧误伤。

    没有这一条,上面那道闸会诱使人把「自动重试」四个字从全仓抹掉 —— 而旧队列上它是实话,
    抹掉就等于把一条正确的状态说明也删了。
    """

    def test_the_queue_lane_may_still_say_it_will_retry(self):
        for key in ("erp-retry-next-soon", "erp-retry-exhausted"):
            values = _i18n_value(key)
            self.assertEqual(len(values), 4, key)
            self.assertTrue(
                any(_promises_in(v) for v in values),
                f"{key} 属于真的会自动重试那条路,不该被清成不承诺",
            )


class StewardWriteToolCopyTests(unittest.TestCase):
    """管家写工具(桥直写)自己的对话文案:一句肯定式承诺都不许有。"""

    def test_no_write_tool_copy_promises_an_automatic_retry(self):
        from services.steward import copy_erp_push

        tables = list(copy_erp_push.ERRORS.items()) + list(copy_erp_push.FAIL_REASON.items())
        self.assertTrue(tables, "文案表是空的 —— 判据失效比断言失败更危险")
        for code, table in tables:
            for lang, text in table.items():
                found = _promises_in(text)
                self.assertEqual(found, [], f"{code}/{lang} 承诺了自动重试({found}):{text}")

    def test_the_account_busy_copy_tells_her_to_close_express(self):
        from services.steward import copy_erp_push

        table = copy_erp_push.ERRORS["steward.erp_push_account_busy"]
        self.assertEqual(set(table), {"zh", "th"})
        self.assertIn("关掉", table["zh"])
        self.assertIn("ปิด", table["th"])
        for text in table.values():
            self.assertIn("Express", text)


if __name__ == "__main__":
    unittest.main()
