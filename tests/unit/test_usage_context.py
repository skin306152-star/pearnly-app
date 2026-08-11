# -*- coding: utf-8 -*-
"""services/cost/usage_context.py · 成本归因上下文行为单测。

锁定:① 设/读/reset 干净还原;② 嵌套时入口外层优先、doc_type/pages 内层补齐;
③ 页数归一(0/负数/垃圾值 → None,绝不落 0 污染每页成本的分母);
④ 未登记入口照原样落账不抛;⑤ 线程 fan-out 按 copy_context 传播(页级并发的真实写法)。
"""

import contextvars
import unittest
from concurrent.futures import ThreadPoolExecutor

from services.cost import usage_context as uc


class SetResetTests(unittest.TestCase):
    def test_set_then_reset_restores_empty(self):
        self.assertIsNone(uc.current())
        token = uc.set_usage_context("web_upload", doc_type="invoice", pages=3)
        self.assertEqual(
            uc.current(), {"entry_point": "web_upload", "doc_type": "invoice", "pages": 3}
        )
        uc.reset_usage_context(token)
        self.assertIsNone(uc.current())

    def test_context_manager_resets_on_exception(self):
        with self.assertRaises(ValueError):
            with uc.usage_context("line", doc_type="receipt"):
                raise ValueError("boom")
        self.assertIsNone(uc.current())

    def test_blank_entry_point_stays_none(self):
        with uc.usage_context("   "):
            self.assertIsNone(uc.current()["entry_point"])


class NestingTests(unittest.TestCase):
    def test_outer_entry_point_wins(self):
        # 路由(外)才是真正的产品入口,内层管线不许把它掀翻
        with uc.usage_context("web_upload", doc_type="auto"):
            with uc.usage_context("bank_recon", doc_type="bank_statement"):
                self.assertEqual(uc.current()["entry_point"], "web_upload")

    def test_inner_fills_fields_outer_left_empty(self):
        # 路由知道入口不知道页数,页数要到渲染完才有
        with uc.usage_context("web_upload"):
            with uc.usage_context("web_upload", doc_type="invoice", pages=7):
                self.assertEqual(uc.current()["doc_type"], "invoice")
                self.assertEqual(uc.current()["pages"], 7)

    def test_inner_doc_type_refines_outer(self):
        with uc.usage_context("email", doc_type="auto"):
            with uc.usage_context("email", doc_type="invoice"):
                self.assertEqual(uc.current()["doc_type"], "invoice")

    def test_exiting_inner_restores_outer(self):
        with uc.usage_context("web_upload", doc_type="auto"):
            with uc.usage_context("web_upload", pages=4):
                pass
            self.assertIsNone(uc.current()["pages"])
            self.assertEqual(uc.current()["doc_type"], "auto")


class PagesNormalizationTests(unittest.TestCase):
    def test_zero_and_negative_and_garbage_become_none(self):
        for bad in (0, -3, None, "", "abc", object()):
            with uc.usage_context("web_upload", pages=bad):
                self.assertIsNone(uc.current()["pages"], f"pages={bad!r} 应归 None")

    def test_numeric_string_coerced(self):
        with uc.usage_context("web_upload", pages="12"):
            self.assertEqual(uc.current()["pages"], 12)


class UnknownEntryPointTests(unittest.TestCase):
    def test_unregistered_value_kept_and_warned(self):
        # 吞掉会让成本悄悄消失在「未归因」里,留下则在面板上现形
        with self.assertLogs("services.cost.usage_context", level="WARNING"):
            with uc.usage_context("typo_entry"):
                self.assertEqual(uc.current()["entry_point"], "typo_entry")

    def test_registered_values_do_not_warn(self):
        for name in uc.ENTRY_POINTS:
            with uc.usage_context(name):
                self.assertEqual(uc.current()["entry_point"], name)


class ThreadPropagationTests(unittest.TestCase):
    def test_copy_context_carries_attribution_into_worker(self):
        # 页级并发(ocr/page_runner · ocr/direct_read)就是这个写法,归因必须跟进子线程
        with uc.usage_context("web_upload", doc_type="invoice", pages=5):
            with ThreadPoolExecutor(max_workers=2) as ex:
                futs = [ex.submit(contextvars.copy_context().run, uc.current) for _ in range(2)]
                got = [f.result() for f in futs]
        self.assertTrue(all(g["entry_point"] == "web_upload" for g in got))
        self.assertTrue(all(g["pages"] == 5 for g in got))

    def test_plain_submit_loses_attribution(self):
        # 反证:不 copy_context 的 fan-out 子线程读不到 —— 新增并发点必须照抄上面的写法
        with uc.usage_context("web_upload", doc_type="invoice"):
            with ThreadPoolExecutor(max_workers=1) as ex:
                got = ex.submit(uc.current).result()
        self.assertIsNone(got)


if __name__ == "__main__":
    unittest.main()
