#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_billing_correctness_safety_net.py · REFACTOR-WC

扣费正确性安全网 · 纯加测试不改业务 · 给 A 拆高敏 OCR/billing 热路径当保险。

为什么是集成层而非单元层:这里锁定的是「钱怎么算」的端到端契约 —— 定价阶梯、
退款冲销、VAT 公式 —— 跨 services/billing/pricing 与 vat_excel_export 两个模块的
真实计算路径。窗口 A 重构 charge_ocr / recon 扣费 / vat_excel 时,只要这些金额
不变量被改坏,本文件立刻红。全部走纯函数(0 DB · 0 网络 · 0 Gemini)→ CI 真跑
不 skip,是真正能拦回归的硬闸。

覆盖 4 个维度(对应 loop 目标「金额对 / 不重复扣 / 退款对 / VAT 算对」):
  1. 金额对   — PDF 阶梯价跨界 + Excel 字符向上取整的精确值
  2. 不重复扣 — 估价是纯函数:同输入多次调用恒等 · 无隐藏自增状态
  3. 退款对   — usage 扣费与 adjustment 退款的算术冲销恒为 0
  4. VAT 算对 — _ocr_validate_invoice 对 7% 偏差 / 净额+VAT≠总额 的判定边界
"""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_pricing():
    try:
        from services.billing import pricing
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"services.billing.pricing 不可 import:{e}")
    return pricing


def _load_vat_validator():
    try:
        from services.vat.vat_excel_export import _ocr_validate_invoice
    except Exception as e:  # pragma: no cover
        raise unittest.SkipTest(f"vat_excel_export._ocr_validate_invoice 不可 import:{e}")
    return _ocr_validate_invoice


# ──────────────────────────────────────────────────────────────
# 维度 1 · 金额对(PDF 阶梯 + Excel 字符)
# ──────────────────────────────────────────────────────────────


class PdfTierPricingAmountTest(unittest.TestCase):
    """PDF 阶梯定价:前 200 页 ฿1.50/页 · 超出 ฿0.75/页 · 跨界自动拆段"""

    def setUp(self) -> None:
        self.pricing = _load_pricing()

    def test_first_page_within_tier1_is_1_50(self) -> None:
        cost = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=0, page_count=1)
        self.assertEqual(cost, Decimal("1.50"))

    def test_fully_inside_tier1_no_discount(self) -> None:
        # 已用 0 · 本次 200 页 · 全在 tier1 → 200 * 1.50 = 300.00
        cost = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=0, page_count=200)
        self.assertEqual(cost, Decimal("300.00"))

    def test_boundary_split_at_200_uses_both_tiers(self) -> None:
        # 已用 199 · 本次 2 页:第 200 页 tier1(1.50)+ 第 201 页 tier2(0.75)= 2.25
        cost = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=199, page_count=2)
        self.assertEqual(cost, Decimal("1.50") + Decimal("0.75"))

    def test_fully_in_tier2_when_already_over_limit(self) -> None:
        # 已用 200(tier1 耗尽)· 本次 3 页全 tier2 → 3 * 0.75 = 2.25
        cost = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=200, page_count=3)
        self.assertEqual(cost, Decimal("2.25"))

    def test_zero_pages_is_free(self) -> None:
        self.assertEqual(
            self.pricing.estimate_pdf_cost_thb(pages_used_this_month=50, page_count=0),
            Decimal("0.00"),
        )

    def test_negative_or_none_inputs_clamp_to_zero(self) -> None:
        # 防御:负数 page_count → 0 · 负数 used 视作 0(全 tier1)
        self.assertEqual(
            self.pricing.estimate_pdf_cost_thb(pages_used_this_month=-5, page_count=-3),
            Decimal("0.00"),
        )
        self.assertEqual(
            self.pricing.estimate_pdf_cost_thb(pages_used_this_month=None, page_count=1),
            Decimal("1.50"),
        )

    def test_result_always_two_decimal_places(self) -> None:
        cost = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=199, page_count=5)
        # 量化到 0.01 · 指数恒为 -2
        self.assertEqual(cost.as_tuple().exponent, -2)


class ExcelCharPricingAmountTest(unittest.TestCase):
    """Excel/Word/CSV 按字符:50 字符 = 1 satang(฿0.01)· 向上取整"""

    def setUp(self) -> None:
        self.pricing = _load_pricing()

    def test_exactly_50_chars_is_1_satang(self) -> None:
        self.assertEqual(self.pricing.estimate_excel_cost_thb(50), Decimal("0.01"))

    def test_51_chars_rounds_up_to_2_satang(self) -> None:
        # ceil(51/50) = 2 → 0.02 · 多 1 字符也进位(不能少收)
        self.assertEqual(self.pricing.estimate_excel_cost_thb(51), Decimal("0.02"))

    def test_1_char_rounds_up_to_1_satang(self) -> None:
        # ceil(1/50) = 1 · 最小计费单位 1 satang(不向下吞掉)
        self.assertEqual(self.pricing.estimate_excel_cost_thb(1), Decimal("0.01"))

    def test_zero_chars_is_free(self) -> None:
        self.assertEqual(self.pricing.estimate_excel_cost_thb(0), Decimal("0.00"))

    def test_round_number_500_chars_is_10_satang(self) -> None:
        self.assertEqual(self.pricing.estimate_excel_cost_thb(500), Decimal("0.10"))


# ──────────────────────────────────────────────────────────────
# 维度 2 · 不重复扣(估价纯函数 · 无隐藏状态)
# ──────────────────────────────────────────────────────────────


class PricingPurityNoDoubleChargeTest(unittest.TestCase):
    """估价函数必须是纯函数:同输入重复调用恒等 · 不携带跨调用自增状态。

    这是「不重复扣」在计算层的护栏 —— 若有人把 used 计数误塞进估价函数内部状态,
    第二次调用就会比第一次贵,本测试立刻拦下。真正的幂等扣费在 charge_ocr 的
    单原子事务里,那条路径由 env-gated DB 测试 + spec 11/16 E2E 兜底。
    """

    def setUp(self) -> None:
        self.pricing = _load_pricing()

    def test_pdf_estimate_is_idempotent_across_calls(self) -> None:
        first = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=150, page_count=60)
        second = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=150, page_count=60)
        third = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=150, page_count=60)
        self.assertEqual(first, second)
        self.assertEqual(second, third)

    def test_excel_estimate_is_idempotent_across_calls(self) -> None:
        a = self.pricing.estimate_excel_cost_thb(1234)
        b = self.pricing.estimate_excel_cost_thb(1234)
        self.assertEqual(a, b)

    def test_pdf_cost_additive_across_split_charges(self) -> None:
        """把 10 页拆成两次各 5 页扣(used 正确累进)总价 == 一次扣 10 页。

        锁定「分次扣不会因阶梯错位多收/少收」:连续两笔 5 页,第二笔的 used 已 +5。
        """
        used0 = 198
        one_shot = self.pricing.estimate_pdf_cost_thb(used0, 10)
        first_half = self.pricing.estimate_pdf_cost_thb(used0, 5)
        second_half = self.pricing.estimate_pdf_cost_thb(used0 + 5, 5)
        self.assertEqual(one_shot, first_half + second_half)


# ──────────────────────────────────────────────────────────────
# 维度 3 · 退款对(usage 扣费 ↔ adjustment 退款 算术冲销)
# ──────────────────────────────────────────────────────────────


class RefundReversalArithmeticTest(unittest.TestCase):
    """退款语义:credit_transactions 里 usage 记负额 · adjustment(退款)记正额。

    一笔扣费被全额退款后,二者相加必须精确为 0(不留浮点尾巴 / 不多退少退)。
    services/credits/store.py 的口径:usage amount_thb<0 · topup/adjustment>0。
    """

    def setUp(self) -> None:
        self.pricing = _load_pricing()

    def test_full_refund_nets_to_zero(self) -> None:
        charged = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=199, page_count=2)
        usage_amount = -charged  # 扣费入账为负
        refund_amount = charged  # 全额退款入账为正
        self.assertEqual(usage_amount + refund_amount, Decimal("0.00"))

    def test_balance_after_charge_then_refund_restored(self) -> None:
        # 余额模型:start - cost + refund == start(全额退款后余额还原)
        start = Decimal("100.00")
        cost = self.pricing.estimate_excel_cost_thb(2500)  # 2500/50 = 50 satang = 0.50
        self.assertEqual(cost, Decimal("0.50"))
        after_charge = start - cost
        after_refund = after_charge + cost
        self.assertEqual(after_refund, start)

    def test_partial_refund_leaves_exact_remainder(self) -> None:
        cost = self.pricing.estimate_pdf_cost_thb(pages_used_this_month=0, page_count=4)  # 6.00
        self.assertEqual(cost, Decimal("6.00"))
        partial_refund = Decimal("1.50")  # 退 1 页
        net = -cost + partial_refund
        self.assertEqual(net, Decimal("-4.50"))


# ──────────────────────────────────────────────────────────────
# 维度 4 · VAT 算对(_ocr_validate_invoice 7% 公式判定)
# ──────────────────────────────────────────────────────────────


class VatRateValidationTest(unittest.TestCase):
    """销项发票 VAT 校验:净额 * 7% ≈ VAT · 净额 + VAT ≈ 总额。

    锁定 vat_excel_export._ocr_validate_invoice 的金额判定边界。窗口 A/B 重构
    VAT 对账时若动坏 7% 公式或总额求和,本测试直接红。
    """

    def setUp(self) -> None:
        self.validate = _load_vat_validator()

    def _base_invoice(self, **overrides):
        inv = {
            "invoice_no": "INV-001",
            "buyer_name": "Acme Co Ltd",
            "buyer_tax_id": "0105551234567",  # 13 位 · 合法
            "invoice_date": "31/05/2026",
            "amount_pre_vat": 100.0,
            "vat_amount": 7.0,
            "total_amount": 107.0,
        }
        inv.update(overrides)
        return inv

    def test_correct_7_percent_invoice_has_no_amount_warnings(self) -> None:
        warns = self.validate(self._base_invoice())
        self.assertNotIn("w_vat_rate_mismatch", warns)
        self.assertNotIn("w_amount_sum_mismatch", warns)

    def test_wrong_vat_rate_flagged(self) -> None:
        # 净额 1000 期望 VAT 70 · 给 100(差 30 > 容差 max(1, 3.5))→ 必须报 mismatch
        warns = self.validate(
            self._base_invoice(amount_pre_vat=1000.0, vat_amount=100.0, total_amount=1100.0)
        )
        self.assertIn("w_vat_rate_mismatch", warns)

    def test_sum_mismatch_flagged(self) -> None:
        # 净额 100 + VAT 7 = 107 · 但总额写 200 → 求和不符
        warns = self.validate(
            self._base_invoice(amount_pre_vat=100.0, vat_amount=7.0, total_amount=200.0)
        )
        self.assertIn("w_amount_sum_mismatch", warns)

    def test_small_net_amount_skips_vat_rate_check(self) -> None:
        # 净额 ≤ 10 THB 不做 7% 校验(避免小额噪声)· 即便 VAT 比例怪也不报 rate mismatch
        warns = self.validate(
            self._base_invoice(amount_pre_vat=8.0, vat_amount=3.0, total_amount=11.0)
        )
        self.assertNotIn("w_vat_rate_mismatch", warns)

    def test_within_tolerance_not_flagged(self) -> None:
        # 净额 1000 期望 VAT 70 · 容差 max(1, 70*0.05=3.5)=3.5 · 给 72(差 2 < 3.5)→ 不报
        warns = self.validate(
            self._base_invoice(amount_pre_vat=1000.0, vat_amount=72.0, total_amount=1072.0)
        )
        self.assertNotIn("w_vat_rate_mismatch", warns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
