# -*- coding: utf-8 -*-
"""
BUG-FIX-RECON-GLCSV(2026-05-25)回归 · 委托银行对账回归 P0-1/P0-2。

锁定根因 + 失败分流(对应 2026-05-25 委托测试的两个 GL CSV 失败):
  P0-1 gl_missing_date_account_unbalanced.csv:缺日期/科目 → 必须弹列映射(needs_mapping)·
       不能 done。此前 _GL_EXTS 不含 .csv → GL CSV 跳过 submit 预检 → 异步 worker 静默存
       done 0 行任务。
  P0-2 gl_valid_weird_headers_shape_OK.csv:怪表头但形状完整 → 能 AI/本地推断则 done+rows>0;
       推不准也必须 needs_mapping(有 headers/preview 可弹面板)· 绝不 done+0 行。

本测试只验:① 预检覆盖 GL CSV(_GL_EXTS 含 .csv/.tsv)② GL CSV 读到表格但不认识列时
走 needs_mapping(带 mapping_request · 有 headers/preview)而非静默 0 行。
识别准确率由 bank_recon_v2 自己的测试负责;这里不依赖 Gemini(无 key → 本地路径)。
"""

import os
import tempfile
import unittest

from routes import recon_jobs_routes as RR
from services.recon.bank_recon_v2 import parse_gl, parse_gl_excel

# 委托素材的最小内嵌复刻(同形状 · 不依赖桌面外部文件)
GL_MISSING_DATE = (  # A,B,C,D:无日期、无科目列 · 只有凭证/摘要/借/贷
    "A,B,C,D\n"
    "JV-001,Customer receipt A,5000.00,\n"
    "JV-001,Customer receipt A,,5000.00\n"
    "PV-001,Supplier payment B,1200.00,\n"
    "PV-001,Supplier payment B,,999.99\n"
    "JV-002,Bank fee,300.00,\n"
).encode("utf-8")

GL_WEIRD_HEADERS = (  # X1..X7:怪表头但日期/凭证/科目/名称/摘要/借/贷形状完整
    "X1,X2,X3,X4,X5,X6,X7\n"
    "2026-01-02,JV-001,1112-10,Bank KTB 8258,Customer receipt A,5000.00,\n"
    "2026-01-02,JV-001,4100-00,Sales revenue,Customer receipt A,,5000.00\n"
    "2026-01-03,PV-001,5100-00,Office expense,Supplier payment B,1200.00,\n"
    "2026-01-03,PV-001,1112-10,Bank KTB 8258,Supplier payment B,,1200.00\n"
    "2026-01-04,JV-002,5300-00,Bank fee,Bank service charge,300.00,\n"
    "2026-01-04,JV-002,1112-10,Bank KTB 8258,Bank service charge,,300.00\n"
).encode("utf-8")


def _gl_outcome(result):
    """把 parse 结果归一成可断言的三态:'ok_rows' / 'needs_mapping' / 'silent_empty'。"""
    if result.get("ok") and len(result.get("rows") or []) > 0:
        return "ok_rows"
    if result.get("needs_mapping"):
        return "needs_mapping"
    # ok=True 但 0 行,或 ok=False 但无 needs_mapping/无 mapping_request → 就是被禁止的隐藏失败
    return "silent_empty"


class GlCsvPreflightCoverage(unittest.TestCase):
    def test_gl_exts_now_covers_csv_tsv(self):
        # 根因:此前 _GL_EXTS 只含 Excel → GL CSV 跳过同步预检。修复后必须含 csv/tsv(与 stmt 侧对称)。
        self.assertIn(".csv", RR._GL_EXTS)
        self.assertIn(".tsv", RR._GL_EXTS)


class GlCsvNeverSilentEmpty(unittest.TestCase):
    """两个委托用例:绝不能 'silent_empty'(0 行却像完成)· 只能 ok_rows 或 needs_mapping。"""

    def test_missing_date_csv_needs_mapping_not_silent(self):
        # P0-1:无日期/科目 → 读到表格(有 headers/preview)→ needs_mapping(可弹面板),不静默。
        r = parse_gl(GL_MISSING_DATE, "gl_missing_date.csv", "", "", tenant_id="t-test")
        self.assertEqual(_gl_outcome(r), "needs_mapping")
        self.assertTrue(r.get("mapping_request"))  # 有 headers/preview 可弹

    def test_weird_headers_csv_not_silent(self):
        # P0-2:怪表头形状完整 · 无 Gemini key(本地)→ 至少 needs_mapping(带 mapping_request)·
        #   绝不 silent_empty(此前 worker 路径的隐藏失败)。
        r = parse_gl(GL_WEIRD_HEADERS, "gl_weird.csv", "", "", tenant_id="t-test")
        self.assertNotEqual(_gl_outcome(r), "silent_empty")
        if r.get("needs_mapping"):
            self.assertTrue(r.get("mapping_request"))


class GlCsvPreflightSurfacesMapping(unittest.TestCase):
    """submit 同步预检(_preflight_stmt_mapping)现在必须对 GL CSV 返回 needs_mapping 响应。"""

    def _ref(self, d, name, data):
        p = os.path.join(d, name)
        with open(p, "wb") as f:
            f.write(data)
        return {"path": p, "filename": name, "role": "gl"}

    def test_preflight_returns_needs_mapping_for_gl_csv(self):
        with tempfile.TemporaryDirectory() as d:
            input_ref = [self._ref(d, "gl_missing_date.csv", GL_MISSING_DATE)]
            nm = RR._preflight_stmt_mapping(input_ref, "t-test", api_key="")
        self.assertIsNotNone(nm)  # 此前 GL CSV 被 _GL_EXTS 排除 → 返回 None(漏检)
        self.assertTrue(nm.get("needs_mapping"))
        self.assertEqual(nm.get("file"), "gl_missing_date.csv")


if __name__ == "__main__":
    unittest.main()
