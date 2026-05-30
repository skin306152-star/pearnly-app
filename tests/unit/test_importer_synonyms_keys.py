#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_importer_synonyms_keys.py · REFACTOR-WA-COV1

域:通用导入器叶子模块 services/importer/{synonyms,keys}.py(此前 0 测试)

为啥要这些测试(锁真实不变量 · 非高敏纯逻辑 · 0 逻辑改只加测):
  这两个叶子是「列推断 + AI 校验」共用的地基:
    - synonyms.py:多语(泰/中/英/越/日)表头同义词【集合】· 列推断靠它把
      乱七八糟的表头归到 date/deposit/withdrawal/... 标准列。
    - keys.py:build_header_signature(学习/缓存键)+ _STMT_KEYS/_GL_KEYS(标准字段键)。
  这里锁两类回归:
    1. **存/取(deposit/withdrawal)、借/贷(GL debit/credit)集合必须互斥** ——
       一旦某词同时进两边,银行对账列推断就会把同一列既判存又判取(静默错账)。
    2. **每个同义词必须已是归一化形态**(== _norm(词))—— 消费方拿 _norm(表头)
       去集合里查;若混进 "Date"(大写)这种,归一化表头永远命中不到 → 该语言/词失效。
    3. build_header_signature:确定 / 顺序敏感 / 过滤空表头 / 归一化(大小写/空白不影响) / 16 hex。
    4. _STMT_KEYS / _GL_KEYS 契约锁定(跨列推断 + AI 校验共用 · 改了会静默错位)。

纯逻辑 · 无 DB / 无外部 · CI 必跑不 skip。
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.importer import synonyms, keys  # noqa: E402
from services.importer.coerce import _norm  # noqa: E402

ALL_STMT_SETS = {
    "DATE_H": synonyms.DATE_H,
    "DESC_H": synonyms.DESC_H,
    "DEPOSIT_H": synonyms.DEPOSIT_H,
    "WITHDRAWAL_H": synonyms.WITHDRAWAL_H,
    "BALANCE_H": synonyms.BALANCE_H,
    "AMOUNT_H": synonyms.AMOUNT_H,
}
ALL_GL_SETS = {
    "GL_DEBIT_H": synonyms.GL_DEBIT_H,
    "GL_CREDIT_H": synonyms.GL_CREDIT_H,
    "GL_DOC_H": synonyms.GL_DOC_H,
    "GL_ACCOUNT_H": synonyms.GL_ACCOUNT_H,
}


class SynonymSetShapeTest(unittest.TestCase):
    def test_all_are_nonempty_sets_of_str(self) -> None:
        for name, s in {**ALL_STMT_SETS, **ALL_GL_SETS}.items():
            self.assertIsInstance(s, set, msg=f"{name} 必须是 set(成员判定语义)")
            self.assertTrue(s, msg=f"{name} 不能为空")
            for item in s:
                self.assertIsInstance(item, str, msg=f"{name} 含非字符串项 {item!r}")

    def test_every_entry_is_already_normalized(self) -> None:
        # 消费方用 _norm(表头) 查集合 → 集合里的词必须已是归一化形态,否则永远命中不到
        for name, s in {**ALL_STMT_SETS, **ALL_GL_SETS}.items():
            for item in s:
                self.assertEqual(
                    item,
                    _norm(item),
                    msg=f"{name} 的 {item!r} 非归一化(应 == _norm 结果 {_norm(item)!r})· "
                    f"非归一化词 _norm(表头) 永远命中不到",
                )


class SynonymDisjointnessTest(unittest.TestCase):
    def test_deposit_withdrawal_disjoint(self) -> None:
        overlap = synonyms.DEPOSIT_H & synonyms.WITHDRAWAL_H
        self.assertEqual(
            overlap, set(), msg=f"存/取同义词重叠会让列推断既判存又判取(静默错账):{overlap}"
        )

    def test_gl_debit_credit_disjoint(self) -> None:
        overlap = synonyms.GL_DEBIT_H & synonyms.GL_CREDIT_H
        self.assertEqual(
            overlap, set(), msg=f"GL 借/贷同义词重叠会让科目方向判反(静默错账):{overlap}"
        )


class SynonymMultilingualCoverageTest(unittest.TestCase):
    """锁多语覆盖 · 防重构时悄悄丢某语言/某高频词。"""

    def test_date_languages(self) -> None:
        for w in ("date", "日期", "วันที่", "ngày", "取引日"):
            self.assertIn(w, synonyms.DATE_H, msg=f"DATE_H 丢了 {w!r}")

    def test_deposit_keywords(self) -> None:
        for w in ("deposit", "credit", "存入", "收入", "入金"):
            self.assertIn(w, synonyms.DEPOSIT_H, msg=f"DEPOSIT_H 丢了 {w!r}")

    def test_withdrawal_keywords(self) -> None:
        for w in ("withdrawal", "debit", "支出", "出金"):
            self.assertIn(w, synonyms.WITHDRAWAL_H, msg=f"WITHDRAWAL_H 丢了 {w!r}")

    def test_gl_account_keywords(self) -> None:
        for w in ("account", "科目", "บัญชี"):
            self.assertIn(w, synonyms.GL_ACCOUNT_H, msg=f"GL_ACCOUNT_H 丢了 {w!r}")


class StandardKeysContractTest(unittest.TestCase):
    def test_stmt_keys_locked(self) -> None:
        self.assertEqual(
            keys._STMT_KEYS,
            ("date", "description", "withdrawal", "deposit", "balance", "amount"),
        )

    def test_gl_keys_locked(self) -> None:
        self.assertEqual(
            keys._GL_KEYS,
            ("date", "doc_no", "account", "description", "debit", "credit", "balance", "amount"),
        )


class HeaderSignatureTest(unittest.TestCase):
    def test_returns_16_hex_chars(self) -> None:
        sig = keys.build_header_signature(["Date", "Amount"])
        self.assertEqual(len(sig), 16)
        self.assertTrue(all(c in "0123456789abcdef" for c in sig), msg=f"非 hex:{sig!r}")

    def test_deterministic(self) -> None:
        a = keys.build_header_signature(["date", "amount", "balance"])
        b = keys.build_header_signature(["date", "amount", "balance"])
        self.assertEqual(a, b)

    def test_order_sensitive(self) -> None:
        self.assertNotEqual(
            keys.build_header_signature(["date", "amount"]),
            keys.build_header_signature(["amount", "date"]),
        )

    def test_normalization_case_and_whitespace_insensitive(self) -> None:
        # _norm 小写 + 折叠空白 → 大小写/多空白/前后空白不影响指纹
        base = keys.build_header_signature(["date", "amount"])
        self.assertEqual(keys.build_header_signature(["DATE", "Amount"]), base)
        self.assertEqual(keys.build_header_signature([" date ", "  amount"]), base)

    def test_filters_empty_and_none_headers(self) -> None:
        base = keys.build_header_signature(["date", "amount"])
        self.assertEqual(keys.build_header_signature(["date", "", None, "   ", "amount"]), base)

    def test_empty_headers_signature(self) -> None:
        expected = hashlib.sha1(b"", usedforsecurity=False).hexdigest()[:16]
        self.assertEqual(keys.build_header_signature([]), expected)
        self.assertEqual(keys.build_header_signature([None, "", "  "]), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
