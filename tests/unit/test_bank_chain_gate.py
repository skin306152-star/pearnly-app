# -*- coding: utf-8 -*-
"""银行对账单余额链代码闸(bank_chain_gate)单测 · F17 行级确定性修复 + F20 链推定覆写。

闸是确定性验算:逐行 prev + deposit − withdrawal == balance(opening 起算,容差 ≤0.01)。
正常向不符而翻转向 prev + withdrawal − deposit == bal(且 dep≠wd)唯一命中 →
判定存取互换,确定性翻正列归属(算术不是推断);两向都不符且模型恰一侧非空、
implied=bal−prev 与模型读数 X 的偏差在安全带带内(≤ max(20%×X, 容差))→ 用印刷
余额链推定该侧真值并覆写(值基本对只是方向/列归属错或小幅偏差,数学纠回);带外
(余额读错或金额大错)→ 不可解升档,绝不用可能错的余额杜撰金额。
双侧非零 / implied≈0 / X 近 0 / 金额不可解析 / 余额缺失 → 不可解,返回 reason 由
调用方升档。dep==wd 的非零行两向方程恒同,无唯一解 → 保守裁定按不可解处理,不猜方向。
四级判据顺序不可乱:正常向 > 翻转向 > 链推定覆写 > 不可解。
"""

from __future__ import annotations

import unittest
from decimal import Decimal

from services.ocr.bank_chain_gate import _dec, repair_bank_chain


class _Row:
    def __init__(self, deposit="", withdrawal="", balance="", direction=""):
        self.deposit = deposit
        self.withdrawal = withdrawal
        self.balance = balance
        self.direction = direction
        self.chain_repaired = False
        self.chain_amount_imputed = False
        self.review_required = False


def _reasons(rows, opening):
    return repair_bank_chain(rows, opening)[1]


def _out(rows, opening):
    return repair_bank_chain(rows, opening)[0]


class RepairBankChainTests(unittest.TestCase):
    def test_valid_chain_passes(self):
        out, reasons = repair_bank_chain(
            [
                _Row(deposit="500.00", balance="1500.00"),
                _Row(withdrawal="200.00", balance="1300.00"),
                _Row(deposit="50.25", balance="1350.25"),
            ],
            "1000.00",
        )
        self.assertEqual(reasons, [])
        self.assertFalse(any(e.chain_repaired for e in out))  # 无互换行 → 无修复标记

    def test_column_swap_repaired(self):
        # 印刷行是存款 500(余额 1000→1500),flash 误读成取款 → 正向 1000-500=500 ≠ 1500,
        # 翻转向 1000+500-0=1500 唯一命中 → 翻正为存款,不再是拒绝。
        rows = [_Row(withdrawal="500.00", balance="1500.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].deposit, "500.00")
        self.assertEqual(out[0].withdrawal, "")
        self.assertTrue(out[0].chain_repaired)

    def test_swap_other_direction_repaired(self):
        # 印刷行是取款 500(余额 1000→500),flash 误读成存款 → 翻转向 1000+0-500=500 命中
        rows = [_Row(deposit="500.00", balance="500.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].deposit, "")
        self.assertEqual(out[0].withdrawal, "500.00")
        self.assertTrue(out[0].chain_repaired)

    def test_swap_repaired_in_mixed_multi_row_page(self):
        # 正常行 + 互换行 + 正常行混合:只翻正互换行,正常行原样,全页放行
        rows = [
            _Row(deposit="500.00", balance="1500.00"),
            _Row(deposit="200.00", balance="1300.00"),  # 印刷是取款,被误读成存款
            _Row(deposit="50.25", balance="1350.25"),
        ]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertFalse(out[0].chain_repaired)
        self.assertEqual(out[0].deposit, "500.00")  # 正常行原样
        self.assertEqual(out[0].withdrawal, "")
        self.assertTrue(out[1].chain_repaired)
        self.assertEqual(out[1].deposit, "")
        self.assertEqual(out[1].withdrawal, "200.00")
        self.assertFalse(out[2].chain_repaired)
        self.assertEqual(out[2].deposit, "50.25")

    def test_normal_rows_untouched(self):
        rows = [_Row(deposit="500.00", balance="1500.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].deposit, "500.00")
        self.assertEqual(out[0].withdrawal, "")
        self.assertFalse(out[0].chain_repaired)

    def test_wrong_amount_rejected(self):
        # 500/300 与印刷 1600 正向(1200)、翻转向(1800)都对不上,且双侧非零不落覆写
        # (列归属读乱无基准)→ 不可解
        reasons = _reasons(
            [_Row(deposit="500.00", withdrawal="300.00", balance="1600.00")], "1000.00"
        )
        self.assertTrue(reasons)

    def test_empty_page_passes(self):
        # 0 行 = 无链可验,放行:拒绝只会让空页白烧一次 max 重读,而重读空页仍返回空
        self.assertEqual(repair_bank_chain([], ""), ([], []))

    def test_tolerance_boundary(self):
        # 1000 + 500 = 1500;印刷 1500.01 差恰 0.01 ≤ 容差 → 过;1500.02 超容差 → 拒
        # (双侧非零不落覆写,容差外仍真不可解,边界语义不被覆写吞掉)
        self.assertEqual(_reasons([_Row(deposit="500.00", balance="1500.01")], "1000.00"), [])
        self.assertTrue(
            _reasons(
                [_Row(deposit="500.00", withdrawal="10.00", balance="1500.02")],
                "1000.00",
            )
        )

    def test_flipped_tolerance_boundary(self):
        # 翻转向容差同口径:互换行 1000-500=500,印刷 500.01 → 差 0.01 修复;500.02 超容差
        # 且双侧非零不落覆写 → 拒(翻转向容差不被覆写吞掉)
        out, reasons = repair_bank_chain([_Row(deposit="500.00", balance="500.01")], "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].withdrawal, "500.00")
        self.assertTrue(out[0].chain_repaired)
        self.assertTrue(
            _reasons(
                [_Row(deposit="500.00", withdrawal="10.00", balance="500.02")],
                "1000.00",
            )
        )

    def test_single_row_with_opening_verifiable(self):
        # 单行页有 opening 即完整可验(与多行同规则,不单列豁免)
        self.assertEqual(_reasons([_Row(withdrawal="250.00", balance="750.00")], "1000.00"), [])

    def test_single_row_without_opening_rejected(self):
        # 单行无 opening:链起点不可起算 → 拒绝(单页对账单期初必印,缺失是读数缺陷)
        reasons = _reasons([_Row(deposit="500.00", balance="1500.00")], "")
        self.assertTrue(reasons)

    def test_missing_opening_rejected(self):
        reasons = _reasons(
            [
                _Row(deposit="500.00", balance="1500.00"),
                _Row(withdrawal="200.00", balance="1300.00"),
            ],
            "",
        )
        self.assertTrue(reasons)
        self.assertIn("opening_balance", reasons[0])

    def test_both_amounts_empty_with_shift_rejected(self):
        # 均空且余额未承接上行(1000 → 1500)→ 拒;承转行仅余额不变才放行
        reasons = _reasons([_Row(balance="1500.00")], "1000.00")
        self.assertTrue(reasons)

    def test_carry_forward_first_row_passes(self):
        # 首行承转(ยอดยกมา):无发生额、余额=opening → 放行并继续验后续行
        reasons = _reasons(
            [
                _Row(balance="1000.00"),
                _Row(deposit="500.00", balance="1500.00"),
            ],
            "1000.00",
        )
        self.assertEqual(reasons, [])

    def test_carry_forward_middle_row_passes(self):
        # 中间插一行无发生额、余额不变(结转/合计行)→ 放行
        reasons = _reasons(
            [
                _Row(deposit="500.00", balance="1500.00"),
                _Row(balance="1500.00"),
                _Row(withdrawal="200.00", balance="1300.00"),
            ],
            "1000.00",
        )
        self.assertEqual(reasons, [])

    def test_carry_forward_balance_shift_rejected(self):
        # 无发生额但余额跳变(1500 → 1400)= 丢了发生额或读错余额 → 拒
        reasons = _reasons(
            [
                _Row(deposit="500.00", balance="1500.00"),
                _Row(balance="1400.00"),
            ],
            "1000.00",
        )
        self.assertTrue(reasons)
        self.assertIn("行 2", reasons[0])

    def test_missing_balance_rejected(self):
        reasons = _reasons([_Row(deposit="500.00")], "1000.00")
        self.assertTrue(reasons)

    def test_unparseable_amount_rejected(self):
        reasons = _reasons([_Row(deposit="abc", balance="1500.00")], "1000.00")
        self.assertTrue(reasons)
        reasons = _reasons([_Row(withdrawal="1,2x0", balance="500.00")], "1000.00")
        self.assertTrue(reasons)

    def test_stops_at_first_break(self):
        # 断一处即停:链自断点起 prev 不可推进,后续行失去基准,报更多断点只是重复
        # (首行取双侧非零,量级不可被链推定吞掉,仍是真不可解断点)
        rows = [
            _Row(deposit="500.00", withdrawal="100.00", balance="1600.00"),  # 首行就断
            _Row(withdrawal="200.00", balance="1400.00"),  # 若首行对则此行走得上
        ]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(len(reasons), 1)
        self.assertIn("行 1", reasons[0])
        self.assertFalse(any(e.chain_repaired for e in out))
        self.assertFalse(any(e.chain_amount_imputed for e in out))

    def test_thousands_comma_parsed(self):
        reasons = _reasons(
            [
                _Row(deposit="1,234.56", balance="2,234.56"),
                _Row(withdrawal="1,000.00", balance="1,234.56"),
            ],
            "1,000.00",
        )
        self.assertEqual(reasons, [])

    def test_dep_eq_wd_nonzero_not_flipped(self):
        # dep==wd 非零行:正向与翻转向方程恒同(prev+100-100 == prev+100-100),无唯一解
        # → 保守裁定按不可解处理,宁整页升档不猜方向;列字段保持原样(没被翻正)
        rows = [_Row(deposit="100.00", withdrawal="100.00", balance="1200.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertTrue(reasons)
        self.assertEqual(out[0].deposit, "100.00")
        self.assertEqual(out[0].withdrawal, "100.00")
        self.assertFalse(out[0].chain_repaired)

    def test_dep_eq_wd_when_chain_passes_stays_pass(self):
        # dep==wd 且余额承接上行(1000+100-100=1000):正常向即过,无修复也无拒
        rows = [_Row(deposit="100.00", withdrawal="100.00", balance="1000.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertFalse(out[0].chain_repaired)

    def test_repaired_row_direction_flipped(self):
        # direction 是语义派生字段,列归属翻正后必须跟着翻(状态诚实)
        rows = [_Row(deposit="500.00", withdrawal="", balance="500.00", direction="deposit")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].direction, "withdrawal")
        self.assertTrue(out[0].chain_repaired)

    def test_misread_amount_imputed_deposit_side(self):
        # 量级误读:印刷存款 5900(1000 → 6900),flash 读成 5840。正向 1000+5840=6840
        # ≠6900、翻转向 1000-5840=-4840≠6900,两向都断;恰一侧非空 + implied=6900-1000
        # =5900 非零 → 覆写 deposit=5900.00,标记 chain_amount_imputed,放行。
        rows = [_Row(deposit="5840.00", balance="6900.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].deposit, "5900.00")
        self.assertEqual(out[0].withdrawal, "")
        self.assertTrue(out[0].chain_amount_imputed)
        self.assertFalse(out[0].chain_repaired)

    def test_misread_amount_imputed_withdrawal_side(self):
        # withdrawal 侧同口径(小偏差):印刷取款 600(5000 → 4400),flash 读成 610。正向
        # 5000-610=4390≠4400、翻转向 5000+610=5610≠4400;implied=4400-5000=-600<0,
        # |implied−X|=10 ≤ max(0.2×610, 容差) → 覆写 withdrawal=600.00、deposit 置空,
        # 标记,放行;direction 无值不凭空造。
        rows = [_Row(withdrawal="610.00", balance="4400.00")]
        out, reasons = repair_bank_chain(rows, "5000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].withdrawal, "600.00")
        self.assertEqual(out[0].deposit, "")
        self.assertEqual(out[0].direction, "")
        self.assertTrue(out[0].chain_amount_imputed)
        self.assertFalse(out[0].chain_repaired)

    def test_misread_withdrawal_big_deviation_rejected(self):
        # 大偏差不可覆写:印刷取款 600,flash 读成 4900 → |implied−X|=5500 > 0.2×4900
        # =980,读数或余额至少一个错,不许用可能错的余额杜撰 → 不可解升档
        rows = [_Row(withdrawal="4900.00", balance="4400.00")]
        out, reasons = repair_bank_chain(rows, "5000.00")
        self.assertTrue(reasons)
        self.assertEqual(out[0].withdrawal, "4900.00")
        self.assertFalse(out[0].chain_amount_imputed)
        self.assertFalse(out[0].chain_repaired)

    def test_imputed_direction_synced(self):
        # direction 有值就按覆写方向同步(与 _flip_entry 同口径):印刷存款 80(1000→
        # 1080)被读成 75(带内)且 direction 错标 withdrawal → 覆写为 deposit=80.00,
        # direction 同步为 deposit,行内不自相矛盾。
        rows = [_Row(deposit="75.00", balance="1080.00", direction="withdrawal")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].deposit, "80.00")
        self.assertEqual(out[0].withdrawal, "")
        self.assertEqual(out[0].direction, "deposit")
        self.assertTrue(out[0].chain_amount_imputed)

    def test_big_deviation_sentinel_escalates(self):
        # F20 哨兵 ฿28,363:模型读 deposit 8137,链推定 implied=28363,偏差 20226 ≫
        # 0.2×8137=1627.4 → 余额读错或金额大错,带外不可解 → 升档,不再静默覆写。
        rows = [_Row(deposit="8137.00", balance="38363.00")]
        out, reasons = repair_bank_chain(rows, "10000.00")
        self.assertTrue(reasons)
        self.assertEqual(out[0].deposit, "8137.00")
        self.assertFalse(out[0].chain_amount_imputed)
        self.assertFalse(out[0].chain_repaired)

    def test_impute_flips_side_when_sign_opposite(self):
        # 符号相反但值在带内 → 翻侧:印刷存款 490(1000→1490),flash 读成取款 500。正向
        # 1000-500=500≠1490、翻转向 1000+500=1500 差 10 > 容差(非精确互换);implied=
        # 490>0 与取款侧反号,|490−500|=10 ≤ max(0.2×500, 容差) → 翻侧 deposit=490.00,
        # 值近而列错,等价互换修复。
        rows = [_Row(withdrawal="500.00", balance="1490.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].deposit, "490.00")
        self.assertEqual(out[0].withdrawal, "")
        self.assertTrue(out[0].chain_amount_imputed)
        self.assertFalse(out[0].chain_repaired)

    def test_impute_band_boundary_20pct(self):
        # 20% 带边界:X=1000,带=0.2×1000=200。implied=1200(差恰 200)→ 带内覆写;
        # implied=1200.01(差 200.01)→ 带外不可解升档,不覆写。
        out, reasons = repair_bank_chain([_Row(deposit="1000.00", balance="2200.00")], "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].deposit, "1200.00")
        self.assertTrue(out[0].chain_amount_imputed)
        out, reasons = repair_bank_chain([_Row(deposit="1000.00", balance="2200.01")], "1000.00")
        self.assertTrue(reasons)
        self.assertEqual(out[0].deposit, "1000.00")
        self.assertFalse(out[0].chain_amount_imputed)

    def test_impute_x_near_zero_rejected(self):
        # X≈0 退化为不可解(除零防护):模型读 deposit 0.005(≤容差)而余额大动,
        # implied=4000 —— 无锚可信、20% 带退化,按不可解处理,不覆写不猜。
        rows = [_Row(deposit="0.005", balance="5000.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertTrue(reasons)
        self.assertEqual(out[0].deposit, "0.005")
        self.assertFalse(out[0].chain_amount_imputed)
        self.assertFalse(out[0].chain_repaired)

    def test_implied_zero_not_imputed(self):
        # implied=bal−prev≈0 不覆写:余额未动却带发生额 = 读数缺陷,无增量信息 → 不可解
        rows = [_Row(deposit="500.00", balance="1000.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertTrue(reasons)
        self.assertEqual(out[0].deposit, "500.00")
        self.assertFalse(out[0].chain_amount_imputed)

    def test_double_sided_not_imputed(self):
        # 双侧非零 = 模型连列归属都读乱,无可信基准 → 不覆写,不可解(宁整页升档不猜)
        rows = [_Row(deposit="500.00", withdrawal="300.00", balance="1500.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertTrue(reasons)
        self.assertEqual(out[0].deposit, "500.00")
        self.assertEqual(out[0].withdrawal, "300.00")
        self.assertFalse(out[0].chain_amount_imputed)

    def test_wrong_balance_impute_cascades_to_next_row_break(self):
        # 余额带内读错兜底:本行印刷余额 1900 被读成 1820(偏差 80 ≤ 0.2×900=180,带内
        # 覆写值随错为 820),下一行双侧非零不可覆写(真发生额 800/200,1900→2500),对错
        # 基准 1820+800-200=2420≠2500 → 断链报 reason,整页照样升档,不会带错放行。
        rows = [
            _Row(deposit="900.00", balance="1820.00"),  # 印刷 1900,读成 1820
            _Row(deposit="800.00", withdrawal="200.00", balance="2500.00"),
        ]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertTrue(reasons)
        self.assertIn("行 2", reasons[0])
        self.assertTrue(out[0].chain_amount_imputed)
        self.assertEqual(out[0].deposit, "820.00")

    def test_wrong_balance_big_deviation_escalates_at_row(self):
        # 余额读错大偏差(旧判据静默写错账的实弹形态):印刷 1900 读成 1400 → implied=400
        # 与模型读数 900 偏差 500 > 0.2×900=180,带外 → 本行即不可解升档,不再靠下一行
        # 兜底(哨兵 ฿28,363 即此形态:链内自洽但值错)。
        rows = [
            _Row(deposit="900.00", balance="1400.00"),  # 印刷 1900,读成 1400
            _Row(deposit="800.00", withdrawal="200.00", balance="2500.00"),
        ]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertTrue(reasons)
        self.assertIn("行 1", reasons[0])
        self.assertFalse(out[0].chain_amount_imputed)
        self.assertEqual(out[0].deposit, "900.00")

    def test_normal_direction_beats_impute(self):
        # 四级顺序·正常向优先于覆写:单侧行正常向命中(1000+500=1500)原样过,绝不落
        # 覆写(否则每行正常行都被"覆写一遍同值",标记泛滥且无意义)。
        rows = [_Row(deposit="500.00", balance="1500.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].deposit, "500.00")
        self.assertFalse(out[0].chain_amount_imputed)
        self.assertFalse(out[0].chain_repaired)

    def test_reversal_beats_impute(self):
        # 四级顺序·翻转向优先于覆写:单侧行翻转向唯一命中(印刷取款 500,1000→500)走
        # 交换标记 chain_repaired,不落 chain_amount_imputed —— 方向翻转是方程唯一解,
        # 比金额覆写更确定的修复,先走它。
        rows = [_Row(deposit="500.00", balance="500.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertEqual(out[0].withdrawal, "500.00")
        self.assertTrue(out[0].chain_repaired)
        self.assertFalse(out[0].chain_amount_imputed)

    def test_input_list_not_aliased(self):
        # 返回浅拷贝列表:调用方替换 document.entries 不影响原容器(元素对象本身就地翻正)
        rows = [_Row(deposit="500.00", balance="500.00")]
        out, _ = repair_bank_chain(rows, "1000.00")
        self.assertIsNot(out, rows)
        self.assertIs(out[0], rows[0])


class DecParsingTests(unittest.TestCase):
    def test_dec(self):
        self.assertEqual(_dec("1,234.56"), Decimal("1234.56"))
        self.assertIsNone(_dec(""))
        self.assertIsNone(_dec(None))
        self.assertIsNone(_dec("abc"))
        self.assertEqual(_dec(" 42.50 "), Decimal("42.50"))


class ReviewRequiredTests(unittest.TestCase):
    """P0:链推定覆写金额无第二份图像证据 → 待复核;F17 翻正数学可证 → 不复核。"""

    def test_imputed_row_requires_review(self):
        # 单侧行带内覆写(opening 1000,读 deposit 500,印刷余额 1400 → implied 400,
        # 偏差 100 ≤ 20%×500)→ imputed 且 review_required
        rows = [_Row(deposit="500.00", balance="1400.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertTrue(out[0].chain_amount_imputed)
        self.assertTrue(out[0].review_required)

    def test_flipped_row_not_review_required(self):
        rows = [_Row(withdrawal="500.00", balance="1500.00")]
        out, reasons = repair_bank_chain(rows, "1000.00")
        self.assertEqual(reasons, [])
        self.assertTrue(out[0].chain_repaired)
        self.assertFalse(out[0].review_required)

    def test_normal_row_not_review_required(self):
        rows = [_Row(deposit="500.00", balance="1500.00")]
        out, _ = repair_bank_chain(rows, "1000.00")
        self.assertFalse(out[0].review_required)


class _FakeOutcome:
    def __init__(self, data):
        self.ok = True
        self.data = data
        self.model = "qwen3.8-max"
        self.input_tokens = 10
        self.output_tokens = 20
        self.error_kind = None


class RereadAuditTests(unittest.TestCase):
    """P0:max 重读过链只打标不升档;残断/推定覆写转 warnings。"""

    def _doc(self, entries, opening="1000.00"):
        from services.ocr.schemas_documents import BankStatementDocument

        return BankStatementDocument(
            opening_balance=opening,
            entries=[
                dict(
                    transaction_date="2026-05-01",
                    description="t",
                    deposit=e[0],
                    withdrawal=e[1],
                    balance=e[2],
                )
                for e in entries
            ],
        )

    def test_max_reread_audited_once_no_loop(self):
        from services.ocr.bank_chain_gate import reread_bank_page
        from services.ocr.schemas_documents import BankStatementDocument

        calls = []

        def read_max(ib, ak):
            calls.append(1)
            # max 读数也带不可解断链(两侧非零)→ 审计后仍有 reasons,只 warning 不二次重读
            return _FakeOutcome(
                {
                    "opening_balance": "1000.00",
                    "entries": [
                        {
                            "transaction_date": "2026-05-01",
                            "description": "t",
                            "deposit": "500.00",
                            "withdrawal": "300.00",
                            "balance": "1600.00",
                        }
                    ],
                }
            )

        doc = self._doc([("500.00", "300.00", "1600.00")])
        out_doc, outcome, warns = reread_bank_page(
            doc, b"img", 1, None, read_max, BankStatementDocument
        )
        self.assertEqual(len(calls), 1)  # read_max 恰一次,无升档循环
        self.assertIsNotNone(outcome)
        self.assertTrue(any("max 重读链校验" in w for w in warns))
        self.assertTrue(any("待复核" in w for w in warns))

    def test_max_reread_imputed_flagged_review(self):
        from services.ocr.bank_chain_gate import reread_bank_page
        from services.ocr.schemas_documents import BankStatementDocument

        def read_max(ib, ak):
            # max 读数单侧带内错 → 审计覆写 + review_required + warning
            return _FakeOutcome(
                {
                    "opening_balance": "1000.00",
                    "entries": [
                        {
                            "transaction_date": "2026-05-01",
                            "description": "t",
                            "deposit": "500.00",
                            "withdrawal": "",
                            "balance": "1400.00",
                        }
                    ],
                }
            )

        doc = self._doc([("499.00", "", "1400.00")])  # flash 读断链 → 升档
        out_doc, outcome, warns = reread_bank_page(
            doc, b"img", 1, None, read_max, BankStatementDocument
        )
        self.assertTrue(out_doc.entries[0].chain_amount_imputed)
        self.assertTrue(out_doc.entries[0].review_required)
        self.assertTrue(any("待复核" in w for w in warns))

    def test_no_escalate_branch_returns_imputed_warnings(self):
        from services.ocr.bank_chain_gate import reread_bank_page
        from services.ocr.schemas_documents import BankStatementDocument

        def read_max(ib, ak):  # 不应被调用
            raise AssertionError("flash 放行路径不许升档")

        doc = self._doc([("500.00", "", "1400.00")])  # 带内覆写,flash 路径放行
        out_doc, outcome, warns = reread_bank_page(
            doc, b"img", 1, None, read_max, BankStatementDocument
        )
        self.assertIsNone(outcome)
        self.assertTrue(any("待复核" in w for w in warns))


if __name__ == "__main__":
    unittest.main(verbosity=2)
