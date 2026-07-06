# -*- coding: utf-8 -*-
"""P6 锁闸 · 每 push 免费跑的确定性资产闸(行为回归的另一半在 scripts/ocr_regression_gate.py)。

守三样:① 语料真值完整性(税号 mod-11——#4 语料 bug 不许再犯);② 提示词契约锚点
(4b/4d/4e/7c 这些实测换来的钱面规则,谁删谁红);③ 回归闸自身的判定逻辑。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests" / "eval"))

from id_card_scorer import thai_citizen_id_checkdigit_ok  # noqa: E402
from services.ocr import layer2_prompts as lp  # noqa: E402
from services.ocr.id_card_extract import _ID_CARD_PROMPT  # noqa: E402
from services.ocr.money import valid_thai_tax_id  # noqa: E402


class CorpusGroundTruthTests(unittest.TestCase):
    def test_all_gt_tax_ids_pass_mod11(self):
        # 台账 #4:假校验位税号会把生产 sanity 闸打爆、污染回落率——重生成永远不许倒退
        bad = []
        for gt in ROOT.glob("tests/eval/vision_ablation*/**/ground_truth/*.json"):
            d = json.loads(gt.read_text(encoding="utf-8"))
            for k in ("seller_tax", "buyer_tax"):
                v = str(d.get(k) or "")
                if len(v) == 13 and v.isdigit() and not valid_thai_tax_id(v):
                    bad.append(f"{gt.name}:{k}={v}")
        self.assertEqual(bad, [])

    def test_manifests_reference_existing_gt(self):
        for mf in ROOT.glob("tests/eval/vision_ablation*/manifest*.jsonl"):
            for line in mf.read_text(encoding="utf-8").splitlines():
                m = json.loads(line)
                gt_rel = m.get("gt") or m.get("ground_truth")
                if gt_rel:
                    self.assertTrue((mf.parent / gt_rel).exists(), f"{mf.name} → {gt_rel} 缺失")

    def test_p3_decoy_corpus_locked(self):
        # 台账#1 收官(P3 实弹 20/20 全拒):重折痕预交易单据拒收集不许被掏空/翻标
        decoys = list(
            (ROOT / "tests/eval/vision_ablation_p3/ground_truth").glob("pretx_heavy_*.json")
        )
        self.assertEqual(len(decoys), 20, "重折痕 decoy 语料数被改")
        for f in decoys:
            gt = json.loads(f.read_text(encoding="utf-8"))
            self.assertTrue(gt.get("is_not_invoice"), f"{f.name} 丢了 is_not_invoice")

    def test_p3_id_card_people_ids_pass_checksum(self):
        # 身份证号走泰国校验位(≠税号 mod-11)——语料自身不许有非法号(#4 的镜像)
        bad = []
        idc = ROOT / "tests/eval/vision_ablation_p3/id_card/ground_truth"
        for gt in idc.glob("*.json"):
            pid = json.loads(gt.read_text(encoding="utf-8")).get("people_id")
            if not thai_citizen_id_checkdigit_ok(pid):
                bad.append(f"{gt.name}:{pid}")
        self.assertEqual(bad, [])

    def test_baseline_shape(self):
        base = json.loads(
            (ROOT / "tests/eval/regression_baseline.json").read_text(encoding="utf-8")
        )
        for k in ("avg_score_min", "silent_pass_max", "fallback_share_max"):
            self.assertIn(k, base["invoice"])
        self.assertIn("bank_avg_min", base["recon"])


class PromptContractTests(unittest.TestCase):
    # 每个锚点背后是一条实测换来的钱面规则;删掉/改名必须让这里红,逼出显式决策。
    _INVOICE_ANCHORS = (
        "4b. TOTAL vs PAYMENT",  # 找零陷阱(总额≠现金≠找零)
        "4d. CREDIT NOTES",  # 贷记单负号保真(台账#8)
        "4e. SUBTOTAL SEMANTICS",  # VAT 内含填法(台账#7·回落率 26%→19%)
        "7c. PRE-TRANSACTION DOCUMENTS",  # PO/报价单诱饵拒收(台账#1)
        "ใบส่งของ/ใบกำกับภาษี",  # 二合一真票防误杀例外
        "NEVER flip a printed negative",
    )

    def test_invoice_prompt_anchors(self):
        for anchor in self._INVOICE_ANCHORS:
            self.assertIn(anchor, lp._SYSTEM_PROMPT, f"发票提示词锚点丢失: {anchor}")

    def test_id_card_prompt_anchors(self):
        # #14(P3):身份证发证/到期日抽取 + 终身证 LIFETIME —— 过期语义不许被悄悄撤回
        for anchor in ("issue_date_be", "expiry_date_be", "LIFETIME"):
            self.assertIn(anchor, _ID_CARD_PROMPT, f"身份证提示词锚点丢失: {anchor}")

    def test_recon_prompt_anchors(self):
        self.assertIn("PROVENANCE", lp._GL_SYSTEM_PROMPT)  # GL 金额溯源(描述列数字不当金额)
        # 台账#10 堆叠版式:页脚合计入 doc 级字段(首行方向唯一消歧源)+ 合并列不猜方向
        self.assertIn("total_debit", lp._GL_SYSTEM_PROMPT)
        self.assertIn('MERGED "Debit/Credit" column', lp._GL_SYSTEM_PROMPT)
        self.assertIn(
            "Negative numbers stay negative", lp._BANK_STATEMENT_SYSTEM_PROMPT
        )  # 透支负号


class GateLogicTests(unittest.TestCase):
    def _base(self):
        return json.loads(
            (ROOT / "tests/eval/regression_baseline.json").read_text(encoding="utf-8")
        )

    def _good_inv(self):
        # 2026-07-05 第4轮 + 2026-07-06 台账#6/#10 修后复验 —— 基线必须放行自己的出生数据
        return {
            "n": 181,
            "avg_score": 0.8532,
            "total_amount_miss": 10,
            "silent_pass": 0,
            "silent_files": [],
            "fallback_share": 0.193,
        }

    def test_baseline_passes_its_own_birth_data(self):
        from ocr_regression_gate import check

        good_rec = {
            "bank_v1": 0.992,
            "gl_v1": 0.55,
            "vat_v1": 0.979,
            "bank_v2": 0.968,
            "gl_v2": 1.0,
            "vat_v2": 1.0,
        }
        self.assertEqual(check(self._good_inv(), good_rec, self._base()), [])

    def test_regressions_go_red(self):
        from ocr_regression_gate import check

        base = self._base()
        for field, bad_val in (
            ("avg_score", 0.70),
            ("silent_pass", 1),
            ("fallback_share", 0.40),
            ("total_amount_miss", 30),
        ):
            inv = {**self._good_inv(), field: bad_val}
            self.assertTrue(check(inv, {}, base), f"{field}={bad_val} 应触红")
        self.assertTrue(check(self._good_inv(), {"bank_v2": 0.80}, base))
        self.assertTrue(check(self._good_inv(), {"gl_v1": 0.45}, base))
        # gl_v1 已知弱版式有独立地板 0.5(2026-07-06 棘轮),不吃 v2 的 0.95 门槛
        self.assertEqual(check(self._good_inv(), {"gl_v1": 0.55}, base), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
