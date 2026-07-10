# -*- coding: utf-8 -*-
"""汇总表 → 批量建单 单测(纯函数 · 不连库)。

覆盖:解析(CSV·合计行标注)/ 映射(甲乙方落位·散客归一·单号生成·重号)/ 判定(税号复核方向·
现金赊账·缺字段警告三态)/ commit(只写 ocr_history 记账料·不建账本单据)。真 DB 写入由真账号 E2E 守。
"""

import unittest
from unittest import mock

from services.erp.express_push.common import DOC_TYPE_SOURCE_SYNTHETIC
from services.summary_import import commit as commit_svc
from services.summary_import import dates as dates_svc
from services.summary_import import judge as judge_svc
from services.summary_import import mapping as mapping_svc
from services.summary_import import parse as parse_svc

_OWN_TAX = "0105561234563"  # 账套主体(冰厂)· 13 位
_CP_TAX = "0107537000521"  # 对方(7-11)· 13 位

_CSV = (
    "date,qty,price,subtotal,vat,total\n"
    "2026-06-01,100,6.07,607.00,42.49,649.49\n"
    "2026-06-02,200,6.07,1214.00,84.98,1298.98\n"
    "รวม,,,1821.00,127.47,1948.47\n"
).encode("utf-8")

_COLMAP = {"date": 0, "qty": 1, "unit_price": 2, "subtotal": 3, "vat": 4, "total_amount": 5}
_WORKSPACE = {"name": "Ice Co", "tax_id": _OWN_TAX, "address": "BKK"}


def _sales_constants(**over):
    base = {
        "direction": "sales",
        "counterparty_name": "7-11",
        "counterparty_tax": _CP_TAX,
        "product_name": "Ice Pack",
        "product_code": "ICE-001",
        "doc_no_pattern": "711-2026-06-{seq}",
        "payment_method": "transfer",
        "has_vat": True,
        "cash_walkin": False,
    }
    base.update(over)
    return base


class ParseTests(unittest.TestCase):
    def test_headers_rows_and_summary_flag(self):
        parsed = parse_svc.parse_table(_CSV, "sales.csv")
        self.assertEqual(parsed["headers"][0], "date")
        self.assertEqual(parsed["row_count"], 3)  # 含合计行(标注,不丢)
        self.assertFalse(parsed["rows"][0]["is_summary"])
        self.assertTrue(parsed["rows"][2]["is_summary"])  # รวม 行

    def test_empty_file_returns_empty(self):
        parsed = parse_svc.parse_table(b"", "empty.csv")
        self.assertEqual(parsed["headers"], [])
        self.assertEqual(parsed["row_count"], 0)


class MappingTests(unittest.TestCase):
    def _map(self, constants):
        parsed = parse_svc.parse_table(_CSV, "sales.csv")
        return mapping_svc.map_rows(
            parsed, column_map=_COLMAP, constants=constants, workspace=_WORKSPACE
        )

    def test_skips_summary_row_by_default(self):
        mapped = self._map(_sales_constants())
        self.assertEqual(len(mapped), 2)  # 合计行默认不建单

    def test_sales_party_placement(self):
        f = self._map(_sales_constants())[0]["fields"]
        self.assertEqual(f["seller_tax"], _OWN_TAX)  # 销项:账套=卖方
        self.assertEqual(f["buyer_tax"], _CP_TAX)  # 对方=买方
        self.assertEqual(f["customer_tax"], _CP_TAX)  # 镜像给 sales_mapper
        self.assertEqual(f["_direction"], "sales")

    def test_purchase_party_placement(self):
        f = self._map(_sales_constants(direction="purchase"))[0]["fields"]
        self.assertEqual(f["buyer_tax"], _OWN_TAX)  # 采购:账套=买方
        self.assertEqual(f["seller_tax"], _CP_TAX)

    def test_walkin_normalizes_counterparty_to_cash(self):
        f = self._map(_sales_constants(cash_walkin=True))[0]["fields"]
        self.assertEqual(f["buyer_name"], mapping_svc.CASH_COUNTERPARTY)  # เงินสด
        self.assertEqual(f["buyer_tax"], "")  # 清税号 → 走 MR.ERP/Express 现金兜底
        self.assertTrue(f["_walkin"])

    def test_document_type_source_marked_as_vat_checkbox(self):
        # 合成票种(按「含VAT」勾选框推)必须留痕来源,供付款判定层识别并跳过
        # (不当票面证据摊派现/赊 · 见 services/erp/express_push/common.py::payment_verdict)。
        f = self._map(_sales_constants())[0]["fields"]
        self.assertEqual(f["document_type_source"], DOC_TYPE_SOURCE_SYNTHETIC)

    def test_doc_no_generation_and_dupes(self):
        mapped = self._map(_sales_constants())
        self.assertEqual(mapped[0]["fields"]["invoice_number"], "711-2026-06-001")
        self.assertEqual(mapped[1]["fields"]["invoice_number"], "711-2026-06-002")
        self.assertEqual(mapping_svc.find_duplicate_doc_nos(mapped), [])
        # 无占位符 → 整批同号 → 查重命中
        dup_mapped = self._map(_sales_constants(doc_no_pattern="FIXED-NO"))
        self.assertEqual(mapping_svc.find_duplicate_doc_nos(dup_mapped), ["FIXED-NO"])


class JudgeTests(unittest.TestCase):
    def _fields(self, constants):
        parsed = parse_svc.parse_table(_CSV, "sales.csv")
        return mapping_svc.map_rows(
            parsed, column_map=_COLMAP, constants=constants, workspace=_WORKSPACE
        )[0]["fields"]

    def test_direction_tax_confirmed(self):
        d = judge_svc.judge_direction_row(self._fields(_sales_constants()), _OWN_TAX)
        self.assertEqual(d["direction"], "sales")
        self.assertEqual(d["source"], "tax_confirmed")

    def test_direction_human_declared_when_own_tax_missing(self):
        # 账套无税号 → 无法用税号复核 → 按用户选择走(human_declared)。
        d = judge_svc.judge_direction_row(self._fields(_sales_constants()), "")
        self.assertEqual(d["source"], "human_declared")

    def test_payment_cash_vs_credit_vs_default(self):
        paid = judge_svc.judge_payment_row(self._fields(_sales_constants(payment_method="cash")))
        self.assertEqual(paid["target"], "cash")
        self.assertEqual(paid["source"], "auto")
        default = judge_svc.judge_payment_row(self._fields(_sales_constants(payment_method="")))
        self.assertEqual(default["target"], "credit")
        self.assertEqual(default["source"], "default")

    def test_payment_default_not_leaked_by_synthetic_receipt_doc_type(self):
        # has_vat=False → 合成 document_type="receipt";票种语义单看这值本应=已付,但它是
        # 「含VAT」勾选框代理值非票面证据,无真实付款信号时必须仍兜底 default/credit,
        # 不能被票种层误判成 auto/cash(证伪 payment_verdict 的 vat_checkbox 跳层生效)。
        f = self._fields(_sales_constants(has_vat=False, payment_method=""))
        self.assertEqual(f["document_type"], "receipt")
        default = judge_svc.judge_payment_row(f)
        self.assertEqual(default["target"], "credit")
        self.assertEqual(default["source"], "default")

    def test_warnings_bad_date_and_no_doc_no(self):
        f = self._fields(_sales_constants(doc_no_pattern=""))
        f["date"] = "not-a-date"
        w = judge_svc.row_warnings(f, dup_doc_nos=[])
        self.assertIn(judge_svc.W_NO_DOC_NO, w)
        self.assertIn(judge_svc.W_BAD_DATE, w)

    def test_walkin_suppresses_no_tax_warning_but_named_no_tax_warns(self):
        walkin = self._fields(_sales_constants(cash_walkin=True))
        self.assertNotIn(
            judge_svc.W_NO_TAX_NOT_WALKIN, judge_svc.row_warnings(walkin, dup_doc_nos=[])
        )
        named = self._fields(_sales_constants(counterparty_tax="", cash_walkin=False))
        self.assertIn(judge_svc.W_NO_TAX_NOT_WALKIN, judge_svc.row_warnings(named, dup_doc_nos=[]))

    def test_blocked_on_hard_missing(self):
        parsed = parse_svc.parse_table(_CSV, "sales.csv")
        mapped = mapping_svc.map_rows(
            parsed,
            column_map=_COLMAP,
            constants=_sales_constants(doc_no_pattern=""),
            workspace=_WORKSPACE,
        )
        judged = judge_svc.judge_rows(mapped, own_tax_id=_OWN_TAX, dup_doc_nos=[])
        self.assertTrue(all(j["blocked"] for j in judged))  # 无单号 = 硬阻断


class CommitHelperTests(unittest.TestCase):
    def test_clean_fields_strips_internal(self):
        cleaned = commit_svc._clean_fields(
            {"buyer_tax": _CP_TAX, "_direction": "sales", "_walkin": False}
        )
        self.assertIn("buyer_tax", cleaned)
        self.assertNotIn("_direction", cleaned)

    def test_commit_writes_ocr_history_only_no_ledger_draft(self):
        # 记账推 ERP,不开票:commit 只写 ocr_history(source_ref 留空·剥内部字段),绝不建账本单据。
        calls = []

        def _fake_insert(**kw):
            calls.append(kw)
            return "ocr-1"

        with mock.patch.object(commit_svc.db, "insert_ocr_history", _fake_insert):
            rows = [{"row_index": 0, "fields": {"buyer_tax": _CP_TAX, "_direction": "sales"}}]
            res = commit_svc.commit_rows(
                tenant_id="t", workspace_client_id=9, created_by="u", rows=rows, batch_ref="b"
            )
        self.assertEqual(res[0]["status"], "created")
        self.assertEqual(res[0]["ocr_history_id"], "ocr-1")
        self.assertEqual(len(calls), 1)
        self.assertIsNone(calls[0]["source_ref"])  # 无账本单据可反指
        self.assertEqual(calls[0]["source"], commit_svc._SUMMARY_SOURCE)
        self.assertNotIn("_direction", calls[0]["pages"][0]["fields"])  # 内部字段已剥


class AmountDerivationTests(unittest.TestCase):
    """只填数量 + 固定单价 → 金额自动算(直接填模式 / 汇总表只有数量列)。"""

    def test_qty_times_fixed_price(self):
        parsed = {"rows": [{"index": 0, "cells": ["2026-06-01", "100"], "is_summary": False}]}
        consts = _sales_constants(cash_walkin=True, unit_price="6.50")
        mapped = mapping_svc.map_rows(
            parsed, column_map={"date": 0, "qty": 1}, constants=consts, workspace=_WORKSPACE
        )
        f = mapped[0]["fields"]
        self.assertEqual(f["subtotal"], "650.00")  # 100 × 6.50
        self.assertEqual(f["vat"], "45.50")  # 650 × 7%
        self.assertEqual(f["total_amount"], "695.50")
        judged = judge_svc.judge_rows(mapped, own_tax_id=_OWN_TAX, dup_doc_nos=[])
        self.assertFalse(judged[0]["blocked"])  # 金额自洽 → 不阻断

    def test_sheet_amounts_win_over_derivation(self):
        # 表里已给金额 → 用表里的,不重算。
        mapped = mapping_svc.map_rows(
            parse_svc.parse_table(_CSV, "s.csv"),
            column_map=_COLMAP,
            constants=_sales_constants(unit_price="999"),
            workspace=_WORKSPACE,
        )
        self.assertEqual(mapped[0]["fields"]["total_amount"], "649.49")  # 取表内,非 100×999


class DateResolutionTests(unittest.TestCase):
    """真实泰国汇总表日期:佛历年 / 只有日号 / DD/MM/YYYY。"""

    def test_be_year_to_ad(self):
        self.assertEqual(dates_svc.to_ad_year(2569), 2026)
        self.assertEqual(dates_svc.to_ad_year(2026), 2026)  # 已是公历不动

    def test_parse_full_date_be_and_dmy(self):
        self.assertEqual(dates_svc.parse_full_date("2569-06-01"), "2026-06-01")  # 佛历转公历
        self.assertEqual(dates_svc.parse_full_date("01/06/2569"), "2026-06-01")  # DD/MM/YYYY
        self.assertIsNone(dates_svc.parse_full_date("1"))  # 光日号非完整日期

    def test_resolve_day_number_with_period(self):
        self.assertEqual(dates_svc.resolve_date("3", (2026, 6)), "2026-06-03")
        self.assertIsNone(dates_svc.resolve_date("3", None))  # 无年月无法拼
        self.assertIsNone(dates_svc.resolve_date("", (2026, 6)))

    def test_detect_period_from_thai_title(self):
        self.assertEqual(dates_svc.detect_period("สรุปยอดขาย 7-11 เดือน มิถุนายน 2569"), (2026, 6))
        self.assertIsNone(dates_svc.detect_period("no month here"))

    def test_detect_period_ignores_tax_id_digits(self):
        # 标题含税号 3101888669:年份必须认独立的 2569(=2026),不能被税号头部 "3101" 污染成 2558。
        title = "สรุปยอดขาย บริษัท ทดสอบ จำกัด (เลขภาษี 3101888669) เดือน มิถุนายน 2569"
        self.assertEqual(dates_svc.detect_period(title), (2026, 6))


class RealSheetShapeTests(unittest.TestCase):
    """真表结构:标题行在前 + 光日号日期 + 佛历。跳过前言认表头 + 拼日期。"""

    _REAL = (
        "สรุปยอดขาย 7-11 เดือน มิถุนายน 2569,,,,,\n"
        "วันที่,ยอด,ราคา,ก่อน vat,vat,รวมเงิน\n"
        "1,19220,6.07,116665.40,8166.58,124831.98\n"
        "2,20200,6.07,122614.00,8582.98,131196.98\n"
    ).encode("utf-8")

    def test_skips_title_locates_header_and_period(self):
        parsed = parse_svc.parse_table(self._REAL, "real.csv")
        self.assertEqual(parsed["headers"][0], "วันที่")  # 跳过标题行
        self.assertEqual(parsed["row_count"], 2)
        self.assertEqual(parsed["suggested_period"], [2026, 6])  # 自动认年月

    def test_day_number_dates_composed_via_period(self):
        parsed = parse_svc.parse_table(self._REAL, "real.csv")
        yr, mo = parsed["suggested_period"]
        consts = _sales_constants(cash_walkin=True, period_year=yr, period_month=mo)
        mapped = mapping_svc.map_rows(
            parsed, column_map=_COLMAP, constants=consts, workspace=_WORKSPACE
        )
        self.assertEqual(mapped[0]["fields"]["date"], "2026-06-01")  # 日号1 → 完整公历日期
        judged = judge_svc.judge_rows(mapped, own_tax_id=_OWN_TAX, dup_doc_nos=[])
        self.assertFalse(judged[0]["blocked"])  # 日期拼成 → 不再 bad_date 阻断


if __name__ == "__main__":
    unittest.main()
