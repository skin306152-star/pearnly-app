# -*- coding: utf-8 -*-
"""变形 harness(P4)纯函数守门:扰动确定性 + 不变量判定三态。跑批部分在 prod 执行不进 CI。"""

import io
import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

from metamorphic_harness import BLUR_LADDER, perturbations, verdict  # noqa: E402


def _seed_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (200, 120), "white").save(buf, format="JPEG")
    return buf.getvalue()


class PerturbationTests(unittest.TestCase):
    def test_deterministic_and_complete(self):
        raw = _seed_jpeg()
        a, b = perturbations(raw), perturbations(raw)
        self.assertEqual(sorted(a), sorted(b))
        self.assertEqual({k: v for k, v in a.items()}, b)  # 同输入同输出(可复现)
        self.assertEqual(len([k for k in a if k.startswith("blur")]), len(BLUR_LADDER))
        for k, v in a.items():
            self.assertGreater(len(v), 100, k)


class VerdictTests(unittest.TestCase):
    def test_ok_when_invariants_hold(self):
        base = {"total_amount": "749.00", "invoice_number": "IV71/10053"}
        got = {"total_amount": "749.00", "invoice_number": "IV71/10053"}
        self.assertEqual(verdict(base, got, review=False), "ok")

    def test_silent_when_total_changes_without_review(self):
        base = {"total_amount": "749.00", "invoice_number": "A"}
        got = {"total_amount": "759.00", "invoice_number": "A"}
        self.assertEqual(verdict(base, got, review=False), "SILENT")

    def test_review_is_honest_degradation(self):
        base = {"total_amount": "749.00", "invoice_number": "A"}
        got = {"total_amount": "", "invoice_number": "A"}
        self.assertEqual(verdict(base, got, review=True), "review")

    def test_total_amount_comparison_reuses_recon_scorer_money_close(self):
        # verdict 的钱字段比对复用 recon_scorer.money_close(不再自造 float 解析)
        base = {"total_amount": "1,200.00", "invoice_number": "A"}
        got = {"total_amount": "1200.00", "invoice_number": "A"}
        self.assertEqual(verdict(base, got, review=False), "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
