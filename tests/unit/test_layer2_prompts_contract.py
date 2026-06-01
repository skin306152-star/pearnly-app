#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_layer2_prompts_contract.py · REFACTOR-WA-OCRSPLIT L2-P

锁定 L2-P 纯搬家(prompt 字符串常量 layer2_structure → layer2_prompts)0 逻辑改:
  1. layer2_structure re-export 的 prompt 名与 layer2_prompts 是【同一对象】
     (assertIs · 调用方 + `_DOC_PROMPTS` 字典 0 改动)。
  2. layer2_prompts 是 leaf(不 import layer2_structure → 无循环)。
  3. prompt 字节防漂移:关键 anchor 子串仍在(发送给 Gemini 的 bytes 不变)。

纯 import 契约 · 无 DB/genai。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import layer2_prompts as p  # noqa: E402
from services.ocr import layer2_structure as l2  # noqa: E402

_REEXPORTED = (
    "_RETRY_TRIM_HINT",
    "_GL_SYSTEM_PROMPT",
    "_BANK_STATEMENT_SYSTEM_PROMPT",
    "_VAT_REPORT_SYSTEM_PROMPT",
    "_GENERIC_TABLE_SYSTEM_PROMPT",
    "_SYSTEM_PROMPT",
    "_USER_PROMPT_PREFIX",
)


class Layer2PromptsContractTest(unittest.TestCase):
    def test_reexport_single_source(self) -> None:
        for name in _REEXPORTED:
            self.assertIs(getattr(l2, name), getattr(p, name), f"{name} re-export 漂移(非同一对象)")

    def test_prompts_module_is_leaf(self) -> None:
        # 不 back-import layer2_structure → 无循环
        self.assertIsNone(getattr(p, "layer2_structure", None))

    def test_doc_prompts_dict_uses_same_objects(self) -> None:
        # _DOC_PROMPTS 字典内的 prompt 必须就是 layer2_prompts 里的同一对象
        self.assertIs(l2._DOC_PROMPTS["general_ledger"], p._GL_SYSTEM_PROMPT)
        self.assertIs(l2._DOC_PROMPTS["bank_statement"], p._BANK_STATEMENT_SYSTEM_PROMPT)
        self.assertIs(l2._DOC_PROMPTS["vat_report"], p._VAT_REPORT_SYSTEM_PROMPT)
        self.assertIs(l2._DOC_PROMPTS["generic_table"], p._GENERIC_TABLE_SYSTEM_PROMPT)

    def test_prompt_bytes_anchors_present(self) -> None:
        # 发送给 Gemini 的 bytes 不变 — 关键 anchor 子串防漂移
        self.assertIn("Thai tax invoice text", p._SYSTEM_PROMPT)
        self.assertIn("Extract from this OCR text", p._USER_PROMPT_PREFIX)
        self.assertIn("General Ledger", p._GL_SYSTEM_PROMPT)
        self.assertIn("Bank Statement", p._BANK_STATEMENT_SYSTEM_PROMPT)
        self.assertIn("truncated mid-string", p._RETRY_TRIM_HINT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
