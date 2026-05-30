#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ocr_text_path.py · REFACTOR-WA-COV2

域:services/ocr/text_path.py(Layer 0 · pypdf 电子发票文本快路径 · 此前 0 测试)

为啥要这些测试(OCR 热路径安全网 · 0 逻辑改只加测):
  try_extract 是省钱快路径:PDF 有真文本层(e-Tax 电子发票)就直接 pypdf 抽文本 ·
  跳过 Vision API(占管道 ~70% 成本)。**它的阈值判定是正确性关键**:
    - 误 HIT(对扫描件返文本)→ 跳过 Vision · 拿到垃圾文本 → 发票字段错 → 扣费/对账受损。
    - 误 MISS → 只是多花 Vision 钱(不损正确性)。
  本文件锁:空/坏/0页/低于阈值 → None(安全回退 Vision)· 达阈值 → Layer1Result 正确形状 ·
  max_pages 截断 · 单页抽取异常算空仍计入均值 · 自定义阈值 · engine/dpi/conf 占位值。

纯逻辑 · mock pypdf.PdfReader(不碰真 PDF / 不改模块)· CI 必跑不 skip。
依据 2026-05-30 实读 services/ocr/text_path.py 真实 API(R39 教训:先 Read 再写测)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.ocr import text_path  # noqa: E402


class _FakePage:
    def __init__(self, text, raise_on_extract=False):
        self._text = text
        self._raise = raise_on_extract

    def extract_text(self):
        if self._raise:
            raise RuntimeError("boom extract_text")
        return self._text


class _FakeReader:
    def __init__(self, pages):
        self.pages = pages


def _reader_returning(pages):
    """factory → callable matching pypdf.PdfReader(io.BytesIO(...)) usage."""

    def _ctor(_stream):
        return _FakeReader(pages)

    return _ctor


def _reader_raising(exc):
    def _ctor(_stream):
        raise exc

    return _ctor


# 非空 pdf_bytes:try_extract 只看 len(pdf_bytes) 真假 · 内容由 mock 的 reader 决定
_PDF = b"%PDF-1.4 fake-bytes"


class TextPathGuardTest(unittest.TestCase):
    def test_empty_bytes_returns_none(self) -> None:
        self.assertIsNone(text_path.try_extract(b""))
        self.assertIsNone(text_path.try_extract(None))  # type: ignore[arg-type]

    def test_parse_error_returns_none(self) -> None:
        with patch("pypdf.PdfReader", _reader_raising(ValueError("corrupt"))):
            self.assertIsNone(text_path.try_extract(_PDF))

    def test_zero_pages_returns_none(self) -> None:
        with patch("pypdf.PdfReader", _reader_returning([])):
            self.assertIsNone(text_path.try_extract(_PDF))

    def test_pypdf_not_installed_returns_none(self) -> None:
        # sys.modules['pypdf']=None → `import pypdf` 抛 ImportError → 安全回退 None
        with patch.dict(sys.modules, {"pypdf": None}):
            self.assertIsNone(text_path.try_extract(_PDF))


class TextPathThresholdTest(unittest.TestCase):
    def test_below_threshold_returns_none(self) -> None:
        with patch("pypdf.PdfReader", _reader_returning([_FakePage("x" * 50)])):
            self.assertIsNone(text_path.try_extract(_PDF))  # 50 < 200

    def test_at_threshold_hits(self) -> None:
        # avg == min_text_per_page 不算 below(条件是 avg < threshold 才回退)
        with patch("pypdf.PdfReader", _reader_returning([_FakePage("x" * 200)])):
            res = text_path.try_extract(_PDF)
        self.assertIsNotNone(res)

    def test_above_threshold_hit_shape(self) -> None:
        text = "y" * 300
        with patch("pypdf.PdfReader", _reader_returning([_FakePage(text)])):
            res = text_path.try_extract(_PDF)
        self.assertIsNotNone(res)
        self.assertEqual(res.engine, "text_path")
        self.assertEqual(res.dpi, 0)
        self.assertEqual(res.page_count, 1)
        self.assertEqual(len(res.pages), 1)
        p = res.pages[0]
        self.assertEqual(p.page_number, 1)
        self.assertEqual(p.full_text, text)
        self.assertEqual(p.avg_confidence, 1.0)  # pypdf 直抽 · 占位 1.0
        self.assertEqual(p.blocks, [])  # 无词级结构
        self.assertEqual(p.width, 0)
        self.assertEqual(p.height, 0)
        self.assertGreaterEqual(res.elapsed_ms, 0)

    def test_custom_threshold(self) -> None:
        page = _FakePage("z" * 100)
        with patch("pypdf.PdfReader", _reader_returning([page])):
            self.assertIsNone(text_path.try_extract(_PDF))  # 100 < 200 默认
        with patch("pypdf.PdfReader", _reader_returning([_FakePage("z" * 100)])):
            self.assertIsNotNone(text_path.try_extract(_PDF, min_text_per_page=50))  # 100 >= 50


class TextPathMultiPageTest(unittest.TestCase):
    def test_per_page_extract_error_counts_as_empty(self) -> None:
        # page0 抽取异常→""(计入均值 0)· page1 有 500 字 → avg=(0+500)/2=250 >=200 → HIT
        pages = [_FakePage("", raise_on_extract=True), _FakePage("a" * 500)]
        with patch("pypdf.PdfReader", _reader_returning(pages)):
            res = text_path.try_extract(_PDF)
        self.assertIsNotNone(res)
        self.assertEqual(res.page_count, 2)
        self.assertEqual(res.pages[0].full_text, "")  # 异常页空但仍在
        self.assertEqual(res.pages[1].full_text, "a" * 500)

    def test_extract_text_none_treated_as_empty(self) -> None:
        # extract_text() 返 None → `or ""` → "" · 配一页够阈值的让整体 HIT
        pages = [_FakePage(None), _FakePage("b" * 500)]
        with patch("pypdf.PdfReader", _reader_returning(pages)):
            res = text_path.try_extract(_PDF)
        self.assertIsNotNone(res)
        self.assertEqual(res.pages[0].full_text, "")

    def test_max_pages_cap(self) -> None:
        # 5 页各 300 字 · max_pages=2 → 只处理 2 页(avg=300>=200 HIT · page_count=2)
        pages = [_FakePage("c" * 300) for _ in range(5)]
        with patch("pypdf.PdfReader", _reader_returning(pages)):
            res = text_path.try_extract(_PDF, max_pages=2)
        self.assertIsNotNone(res)
        self.assertEqual(res.page_count, 2)
        self.assertEqual([p.page_number for p in res.pages], [1, 2])

    def test_avg_across_pages_below_threshold_returns_none(self) -> None:
        # 一页满 · 一页空 → avg=(400+0)/2=200 >=200 HIT;再加一空页 avg=400/3≈133 <200 → None
        with patch("pypdf.PdfReader", _reader_returning([_FakePage("d" * 400), _FakePage("")])):
            self.assertIsNotNone(text_path.try_extract(_PDF))
        with patch(
            "pypdf.PdfReader",
            _reader_returning([_FakePage("d" * 400), _FakePage(""), _FakePage("")]),
        ):
            self.assertIsNone(text_path.try_extract(_PDF))


if __name__ == "__main__":
    unittest.main(verbosity=2)
