#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pdsplit_contract.py · REFACTOR-WB-modularize P-D

锁定 P-D verbatim 搬家(per-page 编排 + 多页调度 pipeline → page_runner)0 逻辑改:
  1. pipeline re-export 的 _process_one_page / _process_pages / OCR_PDF_PAGE_WORKERS
     与 page_runner 是【同一对象】(assertIs · run_on_* 调用方 0 改动)。
  2. page_runner 是 leaf —— 不 back-import pipeline → 无循环。
  3. run_on_image_bytes / run_on_table_bytes 仍经 pipeline 命名空间解析
     _process_one_page(故 Step3 单测 patch pipeline 命名空间仍生效);
     _process_pages 内部经 page_runner 命名空间解析(故 Step2 单测 patch page_runner)。

纯 import 契约 · 无 DB/Gemini/网络。CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import page_runner as pr  # noqa: E402
from services.ocr import pipeline as pl  # noqa: E402

_REEXPORTED = (
    "_process_one_page",
    "_process_pages",
    "OCR_PDF_PAGE_WORKERS",
)


class PDSplitContractTest(unittest.TestCase):
    def test_reexport_single_source(self) -> None:
        for name in _REEXPORTED:
            self.assertIs(
                getattr(pl, name), getattr(pr, name), f"{name} re-export 漂移(非同一对象)"
            )

    def test_page_runner_is_leaf(self) -> None:
        # 不 back-import pipeline → 无循环
        self.assertIsNone(getattr(pr, "pipeline", None))

    def test_callables_present(self) -> None:
        self.assertTrue(callable(pr._process_one_page))
        self.assertTrue(callable(pr._process_pages))
        self.assertIsInstance(pr.OCR_PDF_PAGE_WORKERS, int)

    def test_run_on_image_resolves_via_pipeline_namespace(self) -> None:
        # Step3 单测 patch pipeline._process_one_page 必须能拦住 run_on_image_bytes 的调用
        # → 该名字必须是 pipeline 模块的全局(而非 page_runner 内部硬绑定)。
        self.assertIn("_process_one_page", vars(pl))


if __name__ == "__main__":
    unittest.main(verbosity=2)
