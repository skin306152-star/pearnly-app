# -*- coding: utf-8 -*-
"""
REFACTOR-WA 覆盖补强 · services/ocr/error_format.py 行为单测(OCR 错误单行化 · 纯逻辑·无 DB)

补真实行为/边界(原无专属测试 · 覆盖 ~18%):short_error(任意异常→单行 · 去 pydantic 文档 URL ·
取首行 · 超 160 截断加…· 空→类名)+ _fmt_validation(字段去重/前 3+溢出/loc 去 int 0/空 errors 兜底)。
纯函数 · 无 mock(不打 DB/网络/扣费)。
"""

import unittest

from services.ocr import error_format as ef


class _FakeValidationErr:
    """仿 pydantic ValidationError 的 .errors() 接口(_fmt_validation 接受 Any)。"""

    def __init__(self, errs, raise_on_errors=False):
        self._errs = errs
        self._raise = raise_on_errors

    def errors(self):
        if self._raise:
            raise RuntimeError("boom")
        return self._errs


class ShortErrorTests(unittest.TestCase):
    def test_plain_exception_message(self):
        self.assertEqual(ef.short_error(ValueError("bad thing")), "bad thing")

    def test_multiline_keeps_first_line(self):
        self.assertEqual(ef.short_error(ValueError("line1\nline2\nline3")), "line1")

    def test_strips_pydantic_doc_url(self):
        out = ef.short_error(ValueError("oops see https://errors.pydantic.dev/2.5/v/missing here"))
        self.assertNotIn("pydantic.dev", out)

    def test_long_message_truncated_with_ellipsis(self):
        out = ef.short_error(ValueError("x" * 300))
        self.assertLessEqual(len(out), 160)
        self.assertTrue(out.endswith("…"))

    def test_empty_message_falls_back_to_classname(self):
        class WeirdErr(Exception):
            pass

        self.assertEqual(ef.short_error(WeirdErr("")), "WeirdErr")

    def test_real_validation_error_delegates(self):
        from pydantic import BaseModel

        class M(BaseModel):
            x: int

        try:
            M(x="not-an-int")
            self.fail("expected ValidationError")
        except Exception as ve:
            out = ef.short_error(ve)
        self.assertIn("字段识别失败", out)
        self.assertNotIn("pydantic.dev", out)
        self.assertEqual(out.count("\n"), 0)  # 单行


class FmtValidationTests(unittest.TestCase):
    def test_no_errors_fallback(self):
        self.assertEqual(
            ef._fmt_validation(_FakeValidationErr([])),
            "字段校验失败 · 请确认文件格式与表头是否完整",
        )

    def test_errors_call_raises_fallback(self):
        out = ef._fmt_validation(_FakeValidationErr([], raise_on_errors=True))
        self.assertEqual(out, "字段校验失败 · 请确认文件格式与表头是否完整")

    def test_fields_listed_and_deduped(self):
        errs = [
            {"loc": ("seller_tax",)},
            {"loc": ("seller_tax",)},  # dup → 去重
            {"loc": ("buyer_tax",)},
        ]
        out = ef._fmt_validation(_FakeValidationErr(errs))
        self.assertIn("共 3 项", out)  # n = len(errs)
        self.assertIn("seller_tax", out)
        self.assertIn("buyer_tax", out)
        # 去重后只有 2 个字段 · 不应出现第三个重复
        self.assertEqual(out.count("seller_tax"), 1)

    def test_more_than_three_fields_overflow_marker(self):
        errs = [{"loc": (f"f{i}",)} for i in range(5)]
        out = ef._fmt_validation(_FakeValidationErr(errs))
        self.assertIn("…(+2)", out)  # 5 字段 · 显示前 3 + (+2)

    def test_int_zero_stripped_from_loc(self):
        # loc 里的 int 0(列表索引)被剔除 · 只留字段名
        errs = [{"loc": (0, "items")}]
        out = ef._fmt_validation(_FakeValidationErr(errs))
        self.assertIn("items", out)
        self.assertNotIn("0.items", out)

    def test_no_named_fields_generic_message(self):
        errs = [{"loc": ()}, {"loc": ()}]
        out = ef._fmt_validation(_FakeValidationErr(errs))
        self.assertEqual(out, "字段识别失败 · 共 2 项 · 请确认文件表头是否完整")


if __name__ == "__main__":
    unittest.main()
