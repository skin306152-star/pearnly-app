# -*- coding: utf-8 -*-
"""
ADR-006 S7 守门测试 · AI 低信心自动建议一次(suggest_mapping_with_ai + 解析层接入)。

全部离线(mock genai / patch hook)· 锁定:
  1. hook:无 key / flag 关 → None(不调 API);回值规整(过滤非法键/越界列号);缺 date 或钱列 → None。
  2. hook 缓存:同 signature 第二次不再调 API(含『当时回 None』哨兵)。
  3. 门控(关键安全线):allow_ai 默认 False → 异步 worker 路径『永不』调 AI。
  4. 接入:allow_ai=True + AI 建议过余额链(账单)/形状(GL)校验 → 套用 + save_mapping(source="ai");
     校验不过 → 仍 needs_mapping(不自动套用)。
"""

import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

import bank_recon_v2 as brv2
from services.importer import template_learning as tl


def _xlsx(rows):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# 表头不认识(Col*)· 两钱列方向与列序相反 → 本地形状猜反(余额链不成立 · 低信心)·
# 正确映射(withdrawal=2, deposit=3)余额链成立 → 适合验证『AI 救回』。
_STMT_AI = [
    ["Col1", "Col2", "Col3", "Col4", "Col5"],
    ["2025-11-01", "txn a", "", "5000", "15000"],
    ["2025-11-02", "txn b", "2000", "", "13000"],
    ["2025-11-03", "txn c", "1000", "", "12000"],
    ["2025-11-04", "txn d", "", "3000", "15000"],
    ["2025-11-05", "txn e", "500", "", "14500"],
    ["2025-11-06", "txn f", "", "4000", "18500"],
    ["2025-11-07", "txn g", "1500", "", "17000"],
    ["2025-11-08", "txn h", "", "2000", "19000"],
]
_STMT_AI_CORRECT = {"date": 0, "description": 1, "withdrawal": 2, "deposit": 3, "balance": 4}

# 无余额列 → 余额链不可证 → AI 建议也过不了校验 → 应仍 needs_mapping
_STMT_NO_BALANCE = [
    ["X1", "X2", "X3", "X4"],
    ["2025-11-01", "a", "5000.00", "2000.00"],
    ["2025-11-02", "b", "3000.00", "1000.00"],
    ["2025-11-03", "c", "4000.00", "500.00"],
    ["2025-11-04", "d", "1000.00", "700.00"],
]

# 表头不认识的 GL(C*)· 本地低信心 → needs_mapping;AI 给对借贷 → 形状校验过 → 套用。
_GL_AI = [
    ["C1", "C2", "C3", "C4", "C5"],
    ["2025-11-01", "JV001", "4000", "", "5000"],
    ["2025-11-02", "JV002", "5000", "2000", ""],
    ["2025-11-03", "JV003", "5100", "300", ""],
    ["2025-11-04", "JV004", "4000", "", "1500"],
]
_GL_AI_CORRECT = {"date": 0, "doc_no": 1, "account": 2, "debit": 3, "credit": 4}


class _FakeResp:
    def __init__(self, text):
        self.text = text


class _FakeModel:
    """记录 generate_content 调用次数 · 按预设脚本回 JSON 文本。"""

    def __init__(self, scripted_text):
        self.scripted_text = scripted_text

    def generate_content(self, *a, **k):
        _FakeModel.calls += 1
        return _FakeResp(self.scripted_text)

    calls = 0


def _patch_genai(scripted_text):
    """patch google.generativeai 的 configure/GenerativeModel · 返回 (configure_mock, model)。"""
    _FakeModel.calls = 0
    model = _FakeModel(scripted_text)
    return mock.patch.multiple(
        "google.generativeai",
        configure=mock.DEFAULT,
        GenerativeModel=mock.MagicMock(return_value=model),
    )


class HookUnitTests(unittest.TestCase):
    def setUp(self):
        # 每个用例独立临时缓存目录 · 避免相互命中 + 不污染工程
        self._cache_dir = tempfile.mkdtemp(prefix="ai_map_test_")
        self._orig_dir = tl._AI_MAPPING_CACHE_DIR
        tl._AI_MAPPING_CACHE_DIR = self._cache_dir

    def tearDown(self):
        tl._AI_MAPPING_CACHE_DIR = self._orig_dir
        shutil.rmtree(self._cache_dir, ignore_errors=True)

    def test_no_api_key_returns_none_no_call(self):
        with _patch_genai('{"date":0}'):
            out = tl.suggest_mapping_with_ai(
                "statement", "s", ["a", "b"], [["1", "2"]], api_key=""
            )
        self.assertIsNone(out)
        self.assertEqual(_FakeModel.calls, 0)  # 无 key · 根本不调 API

    def test_flag_off_returns_none_no_call(self):
        with mock.patch.dict(os.environ, {"RECON_AI_MAPPING": "0"}):
            with _patch_genai('{"date":0,"amount":1}'):
                out = tl.suggest_mapping_with_ai(
                    "statement", "s", ["a", "b"], [["1", "2"]], api_key="k"
                )
        self.assertIsNone(out)
        self.assertEqual(_FakeModel.calls, 0)

    def test_parses_and_filters_indices(self):
        # 合法键留 · 非法键(foo)丢 · 越界列号(99)丢
        headers = ["d", "desc", "wd", "dep", "bal"]
        script = '{"date":0,"description":1,"withdrawal":2,"deposit":3,"balance":4,"foo":1,"amount":99}'
        with _patch_genai(script):
            out = tl.suggest_mapping_with_ai(
                "statement", "s", headers, [["x"] * 5], api_key="k", signature="sig1"
            )
        self.assertEqual(out, {"date": 0, "description": 1, "withdrawal": 2, "deposit": 3, "balance": 4})
        self.assertEqual(_FakeModel.calls, 1)

    def test_missing_date_or_money_returns_none(self):
        with _patch_genai('{"description":1,"balance":4}'):  # 没 date 也没钱列
            out = tl.suggest_mapping_with_ai(
                "statement", "s", ["a"] * 5, [["x"] * 5], api_key="k", signature="sig2"
            )
        self.assertIsNone(out)

    def test_garbage_returns_none(self):
        with _patch_genai("not json at all"):
            out = tl.suggest_mapping_with_ai(
                "gl", "s", ["a"] * 5, [["x"] * 5], api_key="k", signature="sig3"
            )
        self.assertIsNone(out)

    def test_cache_hit_skips_second_call(self):
        headers = ["d", "desc", "wd", "dep", "bal"]
        script = '{"date":0,"withdrawal":2,"deposit":3,"balance":4}'
        with _patch_genai(script):
            out1 = tl.suggest_mapping_with_ai(
                "statement", "s", headers, [["x"] * 5], api_key="k", signature="same"
            )
            out2 = tl.suggest_mapping_with_ai(
                "statement", "s", headers, [["x"] * 5], api_key="k", signature="same"
            )
        self.assertEqual(out1, out2)
        self.assertEqual(_FakeModel.calls, 1)  # 第二次命中缓存 · 不再烧钱

    def test_cache_none_sentinel_skips_second_call(self):
        # AI 回垃圾 → None · 也要缓存哨兵,防同模板反复重试烧钱
        with _patch_genai("garbage"):
            out1 = tl.suggest_mapping_with_ai(
                "gl", "s", ["a"] * 5, [["x"] * 5], api_key="k", signature="nonesig"
            )
            out2 = tl.suggest_mapping_with_ai(
                "gl", "s", ["a"] * 5, [["x"] * 5], api_key="k", signature="nonesig"
            )
        self.assertIsNone(out1)
        self.assertIsNone(out2)
        self.assertEqual(_FakeModel.calls, 1)


class WorkerPathNeverCallsAITests(unittest.TestCase):
    """安全线:默认 allow_ai=False(异步 worker 路径)· 绝不触发 AI。"""

    def test_stmt_worker_path_no_ai(self):
        with mock.patch(
            "services.importer.template_learning.suggest_mapping_with_ai"
        ) as m:
            res = brv2.parse_bank_stmt_xlsx_direct(_xlsx(_STMT_AI), "w.xlsx")  # allow_ai 默认 False
        m.assert_not_called()
        self.assertFalse(res.get("ok"))  # 本地低信心 + 无 AI → needs_mapping
        self.assertEqual(res.get("error_code"), "needs_mapping")

    def test_gl_worker_path_no_ai(self):
        with mock.patch(
            "services.importer.template_learning.suggest_mapping_with_ai"
        ) as m:
            res = brv2.parse_gl_excel(_xlsx(_GL_AI), "w.xlsx")  # allow_ai 默认 False
        m.assert_not_called()
        self.assertEqual(res.get("error_code"), "needs_mapping")


class PreflightAIIntegrationTests(unittest.TestCase):
    """allow_ai=True(submit 预检路径)· AI 建议经本地校验把关后才套用。"""

    def test_stmt_ai_hit_applies_and_saves(self):
        saved = {}

        def _fake_save(tenant, doc, sig, cm, **k):
            saved["doc"] = doc
            saved["cm"] = cm
            saved["source"] = k.get("source")

        with mock.patch(
            "services.importer.template_learning.suggest_mapping_with_ai",
            return_value=dict(_STMT_AI_CORRECT),
        ) as m, mock.patch(
            "services.importer.template_store.save_mapping", side_effect=_fake_save
        ):
            res = brv2.parse_bank_stmt_xlsx_direct(
                _xlsx(_STMT_AI), "ai.xlsx", tenant_id="t1", allow_ai=True, api_key="k"
            )
        m.assert_called_once()
        self.assertTrue(res.get("ok"), res.get("error_code"))
        self.assertGreaterEqual(res.get("row_count", 0), 5)
        # 过余额链 → 自动存 source="ai"
        self.assertEqual(saved.get("source"), "ai")
        self.assertEqual(saved.get("doc"), "statement")

    def test_stmt_ai_fails_validation_still_needs_mapping(self):
        # AI 给了余额链对不上的映射(把存取列读反)→ 校验不过 → 不套用 → needs_mapping
        bad = {"date": 0, "description": 1, "withdrawal": 3, "deposit": 2, "balance": 4}
        with mock.patch(
            "services.importer.template_learning.suggest_mapping_with_ai", return_value=bad
        ):
            res = brv2.parse_bank_stmt_xlsx_direct(
                _xlsx(_STMT_AI), "ai.xlsx", tenant_id="t1", allow_ai=True, api_key="k"
            )
        self.assertFalse(res.get("ok"))
        self.assertEqual(res.get("error_code"), "needs_mapping")

    def test_stmt_ai_none_still_needs_mapping(self):
        # 无余额列 · AI 返 None(校验不可能过)→ needs_mapping
        with mock.patch(
            "services.importer.template_learning.suggest_mapping_with_ai", return_value=None
        ):
            res = brv2.parse_bank_stmt_xlsx_direct(
                _xlsx(_STMT_NO_BALANCE), "ai.xlsx", tenant_id="t1", allow_ai=True, api_key="k"
            )
        self.assertFalse(res.get("ok"))
        self.assertEqual(res.get("error_code"), "needs_mapping")

    def test_gl_ai_hit_applies_and_saves(self):
        saved = {}

        def _fake_save(tenant, doc, sig, cm, **k):
            saved["doc"] = doc
            saved["source"] = k.get("source")

        with mock.patch(
            "services.importer.template_learning.suggest_mapping_with_ai",
            return_value=dict(_GL_AI_CORRECT),
        ) as m, mock.patch(
            "services.importer.template_store.save_mapping", side_effect=_fake_save
        ):
            res = brv2.parse_gl_excel(
                _xlsx(_GL_AI), "ai.xlsx", tenant_id="t1", allow_ai=True, api_key="k"
            )
        m.assert_called_once()
        self.assertTrue(res.get("ok"), res.get("error_code"))
        self.assertGreaterEqual(res.get("row_count", 0), 3)
        self.assertEqual(saved.get("source"), "ai")
        self.assertEqual(saved.get("doc"), "gl")

    def test_gl_ai_none_still_needs_mapping(self):
        with mock.patch(
            "services.importer.template_learning.suggest_mapping_with_ai", return_value=None
        ):
            res = brv2.parse_gl_excel(
                _xlsx(_GL_AI), "ai.xlsx", tenant_id="t1", allow_ai=True, api_key="k"
            )
        self.assertEqual(res.get("error_code"), "needs_mapping")


if __name__ == "__main__":
    unittest.main()
