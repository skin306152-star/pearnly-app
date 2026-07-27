# -*- coding: utf-8 -*-
"""销售票四表账簿配方 —— 拿金标那三张 Ocha 小票的真数据当尺子(金标见 _ledger_golden)。

金标有三处**故意不照抄**,这里逐条守着:
  ① 科目码:金标 1010=银行 / 2010=销项税,本仓 1010 是现金、2010 是应付账款 → 必须 1020 / 2030
  ② 跨表引用:金标用绝对单元格,删行即 #REF! → 必须按票号 SUMIF
  ③ 日期:金标 02000139 取的是 Time in(同月无害,跨月会挪错申报期)→ 必须取 Time out

表里公式算出来的数与权威值逐格对,在 test_ledger_workbook_math.py。
"""

import re
import unittest
from decimal import Decimal

from services.ledger import accounts as acct
from services.ledger import fields as fld
from services.ledger.doc_date import (
    DATE_FROM_PRINTED,
    DATE_FROM_TIME_OUT,
    REASON_CROSS_MONTH,
    REASON_NO_DATE,
)
from services.ledger.models import (
    REASON_DUPLICATE_INVOICE,
    REASON_NO_INVOICE_NUMBER,
    REASON_NO_SETTLEMENT,
    SETTLE_BANK,
    SETTLE_CASH,
    parse_sales_doc,
    parse_sales_docs,
)
from services.ledger.recipes import sales_books
from services.ledger.registry import get_recipe, list_recipes
from services.ledger.sheets import detail as detail_sheet
from services.ledger.sheets.journal import SHEET_JOURNAL
from services.ledger.sheets.ledger import SHEET_LEDGER
from services.ledger.sheets.pending import SHEET_PENDING
from services.ledger.sheets.trial_balance import SHEET_TRIAL_BALANCE
from tests.unit._ledger_golden import (
    GOLDEN_DOC_TOTALS,
    GOLDEN_GROSS,
    GOLDEN_LINES,
    GOLDEN_NET,
    GOLDEN_SESSION_RAW,
    GOLDEN_VAT,
    build_golden,
    formulas,
    golden_records,
    load,
    record,
)

D = Decimal


class GoldenNumbersTests(unittest.TestCase):
    """四表的每个数字与金标一致。表里的格子是公式,权威值取 result.numbers。"""

    def setUp(self):
        self.docs, self.result = build_golden()

    def test_per_document_totals_match_golden(self):
        by_invoice = {d.invoice_number: d for d in self.docs}
        for invoice, (gross, vat, net) in GOLDEN_DOC_TOTALS.items():
            doc = by_invoice[invoice]
            self.assertEqual(doc.gross, gross, invoice)
            self.assertEqual(doc.vat, vat, invoice)
            self.assertEqual(doc.net, net, invoice)
            self.assertEqual(doc.gross, doc.vat + doc.net, f"{invoice} 拆不回毛额")

    def test_batch_totals_match_golden(self):
        n = self.result.numbers
        self.assertEqual(n["doc_count"], 3)
        self.assertEqual(n["line_count"], 15)
        self.assertEqual(n["gross_total"], GOLDEN_GROSS)
        self.assertEqual(n["vat_total"], GOLDEN_VAT)
        self.assertEqual(n["net_total"], GOLDEN_NET)

    def test_journal_balances_on_authoritative_numbers(self):
        n = self.result.numbers
        self.assertEqual(n["debit_total"], GOLDEN_GROSS)
        self.assertEqual(n["credit_total"], GOLDEN_GROSS)
        self.assertTrue(self.result.balanced)

    def test_money_stays_decimal(self):
        for key in ("gross_total", "vat_total", "net_total", "debit_total", "credit_total"):
            self.assertIsInstance(self.result.numbers[key], Decimal, key)
        for doc in self.result.documents:
            for key in ("gross", "vat", "net"):
                self.assertIsInstance(doc[key], Decimal, f"{doc['invoice_number']}.{key}")
        for doc in self.docs:
            for line in doc.lines:
                self.assertIsInstance(line.amount, Decimal)
                self.assertIsInstance(line.qty, Decimal)

    def test_detail_sheet_lines_match_golden(self):
        ws = load(self.result)[detail_sheet.SHEET_DETAIL]
        rows = [
            r
            for r in ws.iter_rows(min_row=5, max_row=19, values_only=True)
            if r[detail_sheet.COL_INVOICE - 1]
        ]
        self.assertEqual(len(rows), 15)
        expected = [(inv, n, q, a) for inv in GOLDEN_LINES for n, q, a in GOLDEN_LINES[inv]]
        got = [
            (
                r[detail_sheet.COL_INVOICE - 1],
                r[detail_sheet.COL_ITEM - 1],
                r[detail_sheet.COL_QTY - 1],
                r[detail_sheet.COL_AMOUNT - 1],
            )
            for r in rows
        ]
        self.assertEqual(got, expected)

    def test_buddhist_year_converted_and_time_out_wins(self):
        by_invoice = {d.invoice_number: d for d in self.docs}
        self.assertEqual(by_invoice["02000138"].doc_date.isoformat(), "2026-05-27")
        self.assertEqual(by_invoice["02000143"].doc_date.isoformat(), "2026-05-28")
        # 02000139 喂的是上游真会给的形状:date=模型挑的那个时刻(27,即 Time in),
        # date_raw=票面原样。口径钉的是 Time out,所以必须盖过 date 那个 27。
        session = by_invoice["02000139"]
        self.assertEqual(session.doc_date.isoformat(), "2026-05-28")
        self.assertEqual(session.date_source, DATE_FROM_TIME_OUT)


class AccountCodeTests(unittest.TestCase):
    """科目命中 / 未命中 / 退回预置三条路,且表头如实写明用的是哪套码。"""

    def test_preset_fallback_uses_repo_codes_not_golden_codes(self):
        _, result = build_golden()
        labels = self._journal_accounts(result)
        self.assertIn("1020 เงินฝากธนาคาร", labels)
        self.assertIn("2030 ภาษีขาย", labels)
        self.assertIn("4010 รายได้จากการขาย", labels)
        joined = " ".join(labels)
        self.assertNotIn("1010", joined, "1010 是现金,不是银行 —— 照抄金标就是把转账记成现金")
        self.assertNotIn("2010", joined, "2010 是应付账款,不是销项税")

    def test_preset_banner_on_every_sheet(self):
        _, result = build_golden()
        self.assertEqual(result.chart_source, acct.SOURCE_PRESET)
        wb = load(result)
        for ws in wb.worksheets:
            self.assertIn("未接账套", str(ws["A2"].value), ws.title)
            self.assertIn("科目码待确认", str(ws["A2"].value), ws.title)

    def test_bridge_hit_prints_real_client_codes(self):
        chart = acct.resolve_chart(
            bridge={"1010": "1101-01", "1020": "1102-03", "4010": "4101-00", "2030": "2103-02"},
            bridge_names={"1102-03": "ignored", "2030": "ภาษีขายรอนำส่ง"},
            erp_type="express",
        )
        self.assertEqual(chart.source, acct.SOURCE_BRIDGE)
        self.assertEqual(chart.unresolved, ())
        self.assertEqual(chart.of(acct.ROLE_BANK).code, "1102-03")
        self.assertEqual(chart.of(acct.ROLE_OUTPUT_VAT).label, "2103-02 ภาษีขายรอนำส่ง")
        _, result = build_golden(chart=chart)
        labels = self._journal_accounts(result)
        self.assertIn("1102-03 เงินฝากธนาคาร", labels)
        self.assertNotIn("未接账套", str(load(result)[SHEET_JOURNAL]["A2"].value))

    def test_bridge_miss_falls_back_and_lists_role_for_human(self):
        chart = acct.resolve_chart(
            bridge={"1010": "1101-01", "1020": "1102-03", "4010": "4101-00"},
            erp_type="express",
        )
        self.assertEqual(chart.source, acct.SOURCE_PARTIAL)
        self.assertEqual(chart.unresolved, (acct.ROLE_OUTPUT_VAT,))
        # 没映到的角色退回预置码,但必须在横幅里点名交人裁,不静默顶上。
        self.assertEqual(chart.of(acct.ROLE_OUTPUT_VAT).code, "2030")
        self.assertIn("2030 ภาษีขาย", chart.banner)
        _, result = build_golden(chart=chart)
        self.assertEqual(result.chart_unresolved, (acct.ROLE_OUTPUT_VAT,))
        self.assertTrue(result.warnings)

    def test_unknown_role_fails_loud(self):
        with self.assertRaises(KeyError):
            acct.resolve_chart(roles=("no_such_role",))

    @staticmethod
    def _journal_accounts(result):
        ws = load(result)[SHEET_JOURNAL]
        return [c.value for c in ws["D"] if c.row >= 5 and c.value]


class PaymentMethodTests(unittest.TestCase):
    """付款方式决定分录借方 —— 从票面读,不写死。"""

    def _debit_account(self, payment):
        """借方那一腿挂的科目 —— 日记账第一行就是它(三腿顺序固定:借收款 / 贷收入 / 贷税)。"""
        docs = parse_sales_docs([record("02000138", dates={"date": "27/05/2569"}, payment=payment)])
        ws = load(sales_books.build(docs, title="SM", period_label="2569-05"))[SHEET_JOURNAL]
        self.assertIsNotNone(ws.cell(row=5, column=5).value, "第一腿必须落在借方")
        return ws.cell(row=5, column=4).value

    def test_transfer_debits_bank(self):
        self.assertEqual(self._debit_account("transfer"), "1020 เงินฝากธนาคาร")
        self.assertEqual(self._debit_account("qr"), "1020 เงินฝากธนาคาร")

    def test_cash_debits_cash(self):
        self.assertEqual(self._debit_account("cash"), "1010 เงินสด")
        self.assertEqual(self._debit_account("เงินสด"), "1010 เงินสด")

    def test_settlement_recorded_on_document_summary(self):
        docs = parse_sales_docs([record("02000139", dates={"date": "27/05/2569"}, payment="cash")])
        result = sales_books.build(docs, title="SM", period_label="2569-05")
        self.assertEqual(result.documents[0]["settlement"], SETTLE_CASH)
        self.assertEqual(parse_sales_docs(golden_records())[0].settlement, SETTLE_BANK)


class PendingTests(unittest.TestCase):
    """待判:跨月场次、读不出付款方式、票号缺失或撞车的票不入账,但要看得见。"""

    def test_cross_month_session_goes_pending(self):
        docs = parse_sales_docs(
            [
                record(
                    "02000139",
                    dates={"date_raw": "Time In 30/04/2569 22:40 Time Out 01/05/2569 00:20"},
                )
            ]
        )
        self.assertEqual(docs[0].pending_reason, REASON_CROSS_MONTH)
        result = sales_books.build(docs, title="SM", period_label="2569-05")
        self.assertEqual(result.numbers["doc_count"], 0)
        self.assertEqual(len(result.pending), 1)
        ws = load(result)[SHEET_PENDING]
        self.assertEqual(ws["B5"].value, "02000139")
        self.assertIn("ข้ามเดือน", str(ws["F5"].value))

    def test_unreadable_payment_method_goes_pending(self):
        docs = parse_sales_docs([record("02000138", dates={"date": "27/05/2569"}, payment="card")])
        self.assertEqual(docs[0].pending_reason, REASON_NO_SETTLEMENT)
        result = sales_books.build(docs, title="SM", period_label="2569-05")
        self.assertEqual(result.numbers["doc_count"], 0)

    def test_missing_invoice_number_goes_pending(self):
        """票号是全表的主键:空票号时 SUMIF 的 criteria 也空,三张派生表全显示 0。"""
        rec = record("02000138", dates={"date": "27/05/2569"})
        rec["merged_fields"]["invoice_number"] = ""
        docs = parse_sales_docs([rec])
        self.assertEqual(docs[0].pending_reason, REASON_NO_INVOICE_NUMBER)
        result = sales_books.build(docs, title="SM", period_label="2569-05")
        self.assertEqual(result.numbers["doc_count"], 0)
        self.assertEqual(result.numbers["gross_total"], D("0"))

    def test_duplicate_invoice_number_sends_both_to_pending(self):
        """重号会让两张票的分录互相灌进对方,借贷仍相等 —— 自检格照样绿,必须拦在入账前。"""
        first = record("02000138", dates={"date": "27/05/2569"})
        second = record("02000143", dates={"date": "28/05/2569"})
        second["merged_fields"]["invoice_number"] = "02000138"
        second["history_id"] = "h-dup"
        docs = parse_sales_docs([first, second])
        self.assertEqual(len(docs), 2)
        for doc in docs:
            self.assertIn("02000138", doc.pending_reason)
            self.assertEqual(doc.pending_reason, REASON_DUPLICATE_INVOICE.format(inv="02000138"))
        result = sales_books.build(docs, title="SM", period_label="2569-05")
        self.assertEqual(result.numbers["doc_count"], 0)
        self.assertEqual(len(result.pending), 2)

    def test_build_flags_duplicates_even_when_docs_were_not_parsed_together(self):
        """docs 也可能是别处拼出来的 —— 守住工作簿的是 build,不能只靠解析侧。"""
        fields = record("02000138", dates={"date": "27/05/2569"})["merged_fields"]
        docs = [parse_sales_doc(fields), parse_sales_doc(fields)]
        self.assertTrue(all(d.bookable for d in docs), "单张解析时看不见重号,这是前提")
        result = sales_books.build(docs, title="SM", period_label="2569-05")
        self.assertEqual(result.numbers["doc_count"], 0)
        self.assertEqual(len(result.pending), 2)

    def test_pending_sheet_written_even_when_empty(self):
        _, result = build_golden()
        self.assertEqual(result.pending, ())
        self.assertIn(SHEET_PENDING, load(result).sheetnames)


# 跨表引用长这样才安全:'表名'!$C$起:$C$止 —— 删行只让区间缩小,不产生 #REF!
_CROSS_SHEET_REF = re.compile(r"'([^']+)'!(\$[A-Z]+\$\d+)(:\$[A-Z]+\$\d+)?")
_ANY_RANGE = re.compile(r"\$?[A-Z]{1,2}\$?\d+:\$?[A-Z]{1,2}\$?\d+")
_LOCAL_REF = re.compile(r"\$?([A-Z]{1,2})\$?(\d+)")


class FormulaSafetyTests(unittest.TestCase):
    """公式策略:全链公式 + 删行不炸 + 自检格不当闸。"""

    def setUp(self):
        self.docs, self.result = build_golden()
        self.wb = load(self.result)

    def test_no_single_cell_cross_sheet_reference(self):
        """金标那个 ='สมุดรายวันทั่วไป'!$E$13 一删行就 #REF! —— 全仓禁掉这种形状。"""
        offenders = [
            (sheet, coord, formula)
            for sheet, coord, formula in formulas(self.wb)
            for match in _CROSS_SHEET_REF.finditer(formula)
            if match.group(3) is None
        ]
        self.assertEqual(offenders, [], "跨表引用必须是区间,不能是单格")

    def test_cross_sheet_refs_point_at_existing_sheets(self):
        names = set(self.wb.sheetnames)
        for _sheet, _coord, formula in formulas(self.wb):
            for match in _CROSS_SHEET_REF.finditer(formula):
                self.assertIn(match.group(1), names, formula)

    def test_nothing_points_at_a_single_detail_data_cell(self):
        """会计删的是明细行。没有任何公式指向明细数据区的单格 = 删行不可能 #REF!。"""
        ws = self.wb[detail_sheet.SHEET_DETAIL]
        data_rows = set()
        for r in range(5, ws.max_row + 1):
            if not ws.cell(row=r, column=1).value:
                break  # 数据区到第一个空行为止,下面是汇总块
            data_rows.add(r)
        for sheet, coord, formula in formulas(self.wb):
            if sheet != detail_sheet.SHEET_DETAIL:
                continue
            # 先去掉区间(区间删行会缩不会炸),剩下的才是真正的单格引用
            body = _ANY_RANGE.sub("", _CROSS_SHEET_REF.sub("", formula))
            for _col, row in _LOCAL_REF.findall(body):
                self.assertNotIn(int(row), data_rows, f"{coord}: {formula} 指向明细数据行")

    def test_vat_is_a_formula_not_a_constant(self):
        """金标把 VAT 写死,改了行金额 VAT 不动,试算平衡照样显示 Balanced —— 断链必须补上。"""
        ws = self.wb[detail_sheet.SHEET_DETAIL]
        vat_cells = [
            ws.cell(row=r, column=3).value
            for r in range(5, ws.max_row + 1)
            if str(ws.cell(row=r, column=1).value or "") in GOLDEN_DOC_TOTALS
            and str(ws.cell(row=r, column=2).value or "").startswith("=")  # 汇总块,不是明细行
        ]
        self.assertEqual(len(vat_cells), 3)
        for value in vat_cells:
            self.assertIsInstance(value, str)
            self.assertIn("ROUND(", value)
            self.assertIn("7/107", value)

    def test_journal_amounts_are_sumif_back_to_detail(self):
        ws = self.wb[SHEET_JOURNAL]
        amounts = [
            ws.cell(row=r, column=c).value
            for r in range(5, 14)
            for c in (5, 6)
            if ws.cell(row=r, column=c).value is not None
        ]
        self.assertEqual(len(amounts), 9, "三张票各三腿")
        for value in amounts:
            self.assertIn("SUMIF(", value)
            self.assertIn(detail_sheet.SHEET_DETAIL, value)
        # 三腿的口径各不相同,得分开验:销项税必须是内含 7/107,净额必须是毛额减它。
        # 写成外加 7% 时借贷两侧一起变、仍然相等,试算平衡照样 Balanced —— 只扫「有没有
        # SUMIF」看不出来。
        gross_legs = [v for v in amounts if "ROUND(" not in v]
        vat_legs = [v for v in amounts if v.startswith("=ROUND(")]
        net_legs = [v for v in amounts if v.startswith("=SUMIF(") and "-ROUND(" in v]
        self.assertEqual([len(gross_legs), len(vat_legs), len(net_legs)], [3, 3, 3])
        for value in vat_legs + net_legs:
            self.assertIn("*7/107,2)", value)

    def test_detail_amount_column_is_source_data_not_a_formula(self):
        """行金额写成 =ROUND(数量*单价,2):票面单价被四舍五入过时(3×33.33)表里算 99.99,
        而回执和推 ERP 的是票面的 100.00 —— 「她看的那份 = 推的那份」在第一格就断。"""
        docs = parse_sales_docs(
            [
                record(
                    "02000139",
                    dates={"date": "27/05/2569"},
                    items=[{"name": "ค่าบริการ", "qty": "3", "price": "33.33", "subtotal": "100"}],
                )
            ]
        )
        result = sales_books.build(docs, title="SM", period_label="2569-05")
        ws = load(result)[detail_sheet.SHEET_DETAIL]
        amount = ws.cell(row=5, column=detail_sheet.COL_AMOUNT).value
        self.assertNotIsInstance(amount, str, f"行金额不能是公式: {amount!r}")
        self.assertEqual(D(str(amount)), D("100"))
        self.assertEqual(ws.cell(row=5, column=detail_sheet.COL_PRICE).value, 33.33)
        self.assertEqual(result.numbers["gross_total"], D("100"))

    def test_add_row_hint_tells_her_where_to_put_a_missed_item(self):
        ws = self.wb[detail_sheet.SHEET_DETAIL]
        self.assertIn("แถวว่าง", str(ws.cell(row=3, column=1).value))

    def test_self_check_cell_is_labelled_advisory(self):
        ws = self.wb[SHEET_TRIAL_BALANCE]
        check = [
            c.value for c in ws["B"] if isinstance(c.value, str) and c.value.startswith("=IF(")
        ]
        self.assertEqual(len(check), 1)
        note = " ".join(str(c.value) for c in ws["A"] if c.value)
        self.assertIn("自检格仅供参考", note)
        self.assertIn("以系统回执为准", note)

    def test_derived_sheets_are_protected_from_stray_edits(self):
        for name in (SHEET_JOURNAL, SHEET_LEDGER, SHEET_TRIAL_BALANCE):
            self.assertTrue(self.wb[name].protection.sheet, name)
        self.assertFalse(self.wb[detail_sheet.SHEET_DETAIL].protection.sheet)


class RegistryTests(unittest.TestCase):
    """配方注册表:加一个配方 = 加一个文件。"""

    def test_recipe_is_discoverable_without_explicit_import(self):
        codes = [spec.code for spec in list_recipes()]
        self.assertIn(sales_books.RECIPE_CODE, codes)
        spec = get_recipe(sales_books.RECIPE_CODE)
        self.assertEqual(spec.build, sales_books.build)
        self.assertEqual(
            spec.sheets[:4],
            (
                detail_sheet.SHEET_DETAIL,
                SHEET_JOURNAL,
                SHEET_LEDGER,
                SHEET_TRIAL_BALANCE,
            ),
        )

    def test_unknown_recipe_fails_loud(self):
        with self.assertRaises(KeyError):
            get_recipe("no_such_recipe")

    def test_result_carries_filename_and_sheets(self):
        _docs, result = build_golden()
        self.assertTrue(result.filename.endswith(".xlsx"))
        self.assertIn("Sister_Makeup", result.filename)
        self.assertEqual(load(result).sheetnames, list(result.sheets))


if __name__ == "__main__":
    unittest.main()
