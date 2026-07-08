# -*- coding: utf-8 -*-
"""汇总表 → 批量建单 单测(纯函数 · 不连库)。

覆盖:解析(CSV·合计行标注)/ 映射(甲乙方落位·散客归一·单号生成·重号)/ 判定(税号复核方向·
现金赊账·缺字段警告三态)/ commit 纯组装(买方块·销项行)。真 DB 建单由真账号 E2E 守。
"""

import unittest

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
    def test_buyer_block_company_vs_anonymous(self):
        company = commit_svc._buyer_block({"buyer_name": "7-11", "buyer_tax": _CP_TAX})
        self.assertEqual(company["type"], "company")
        self.assertEqual(company["tax_id"], _CP_TAX)
        walkin = commit_svc._buyer_block({"buyer_name": "เงินสด", "buyer_tax": ""})
        self.assertEqual(walkin["type"], "anonymous")

    def test_sales_lines_from_items(self):
        lines = commit_svc._sales_lines({"items": [{"name": "Ice", "qty": "100", "price": "6.07"}]})
        self.assertEqual(lines[0]["description"], "Ice")
        self.assertEqual(lines[0]["qty"], "100")
        self.assertTrue(lines[0]["vat_applicable"])

    def test_clean_fields_strips_internal(self):
        cleaned = commit_svc._clean_fields(
            {"buyer_tax": _CP_TAX, "_direction": "sales", "_walkin": False}
        )
        self.assertIn("buyer_tax", cleaned)
        self.assertNotIn("_direction", cleaned)


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
