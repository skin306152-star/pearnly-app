#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_table_path_safety_net.py · REFACTOR-WC

表格 OCR 路径安全网 · 纯加测试不改业务 · 给 A 拆/覆盖 ocr/table_path 当保险。

锁定 services/ocr/table_path —— 表格文件(CSV/TXT/Excel/docx)→ 结构化 Layer1Result。
这条路是 Excel 计费的上游(同一批表格文件先走这里出结构,再按字符扣费),也是 OCR
非图像分支。契约写坏 → 结构错 → 下游扣费/对账拿到错数据。

背景:A 的 ocr/table_path 单测因「API 假设错误」已 revert(WA R39 作废订正)。本文件在
集成层把真实 API 焊死(engine 名 / Layer1Result 字段 / table_rows 是按表头键的 dict /
空与不支持扩展名抛 ValueError),给 A 重试时一份对的 API 参照。CSV/TXT 走标准库
(0 网络 · 0 DB · 0 Gemini)→ CI 真跑不 skip。

覆盖维度(对应 loop「给 A 新拆模块补集成测试」):
  1. CSV → Layer1Result 契约:engine / page_count / table_headers / table_rows(dict) / full_text
  2. TXT → engine 名
  3. 边界:空 bytes 抛 ValueError · 不支持扩展名抛 ValueError
  4. 纯 helper:_decode_bytes(BOM / 泰文 cp874 / 兜底)· _normalize_header · _render_grid_text
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load():
    try:
        import services.ocr.table_path as mod
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"services.ocr.table_path 不可 import:{e}")
    return mod


class CsvExtractionContractTest(unittest.TestCase):
    """CSV → Layer1Result 结构契约(A 单测假设错的就是这层 API)"""

    def setUp(self) -> None:
        self.t = _load()
        self.res = self.t.extract_from_table_file(b"name,amount\nAcme,100\nBeta,200", "data.csv")

    def test_engine_is_table_path_csv(self) -> None:
        self.assertEqual(self.res.engine, "table_path_csv")

    def test_single_page(self) -> None:
        self.assertEqual(self.res.page_count, 1)
        self.assertEqual(len(self.res.pages), 1)

    def test_headers_extracted(self) -> None:
        self.assertEqual(self.res.pages[0].table_headers, ["name", "amount"])

    def test_rows_are_dicts_keyed_by_header(self) -> None:
        # 关键契约:table_rows 是按表头键的 dict 列表(不是 list-of-list)
        rows = self.res.pages[0].table_rows
        self.assertEqual(rows[0], {"name": "Acme", "amount": "100"})
        self.assertEqual(rows[1], {"name": "Beta", "amount": "200"})

    def test_full_text_is_pipe_grid(self) -> None:
        self.assertEqual(
            self.res.pages[0].full_text, "[csv]\nname | amount\nAcme | 100\nBeta | 200"
        )


class TxtAndBoundaryTest(unittest.TestCase):
    """TXT engine 名 + 空/不支持扩展名的抛错契约"""

    def setUp(self) -> None:
        self.t = _load()

    def test_txt_engine_name(self) -> None:
        res = self.t.extract_from_table_file(b"hello world line", "note.txt")
        self.assertEqual(res.engine, "table_path_txt")

    def test_empty_bytes_raises_value_error(self) -> None:
        # 空文件不静默出空结果 · 抛 ValueError 让上游明确失败(防扣费拿到空结构)
        with self.assertRaises(ValueError):
            self.t.extract_from_table_file(b"", "empty.csv")

    def test_unsupported_extension_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.t.extract_from_table_file(b"whatever", "file.bin")


class DecodeBytesTest(unittest.TestCase):
    """_decode_bytes · 多编码兜底(泰文发票常见 cp874/tis-620)"""

    def setUp(self) -> None:
        self.t = _load()

    def test_utf8_sig_bom_stripped(self) -> None:
        self.assertEqual(self.t._decode_bytes(b"\xef\xbb\xbfhi"), "hi")

    def test_plain_ascii(self) -> None:
        self.assertEqual(self.t._decode_bytes(b"abc"), "abc")

    def test_thai_cp874_roundtrip(self) -> None:
        # 泰文用 cp874 编码 · _decode_bytes 应能还原(不乱码)
        thai = "สวัสดี"
        self.assertEqual(self.t._decode_bytes(thai.encode("cp874")), thai)

    def test_never_raises_falls_back(self) -> None:
        # 任意字节都能解(兜底 utf-8 replace)· 不抛 UnicodeDecodeError
        out = self.t._decode_bytes(b"\xff\xfe\x00bad")
        self.assertIsInstance(out, str)


class NormalizeHeaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.t = _load()

    def test_strips_whitespace(self) -> None:
        self.assertEqual(self.t._normalize_header("  Date  "), "Date")

    def test_none_becomes_empty(self) -> None:
        self.assertEqual(self.t._normalize_header(None), "")


class RenderGridTextTest(unittest.TestCase):
    """_render_grid_text · [label] + 表头 + 行 · 管道分隔 · None 单元格空"""

    def setUp(self) -> None:
        self.t = _load()

    def test_label_headers_rows(self) -> None:
        out = self.t._render_grid_text("Sheet1", ["A", "B"], [["1", "2"], ["3", None]])
        self.assertEqual(out, "[Sheet1]\nA | B\n1 | 2\n3 | ")

    def test_no_headers_only_label_and_rows(self) -> None:
        out = self.t._render_grid_text("X", [], [["a", "b"]])
        self.assertEqual(out, "[X]\na | b")


if __name__ == "__main__":
    unittest.main(verbosity=2)
