# -*- coding: utf-8 -*-
"""银行对账金标语料校验(E1 验收断言 1 · vision_ablation_v2/bank)。

KBANK×8 + SCB×8 的 ground_truth 逐行:余额链零断裂(balance_chain_violations=0)、
勾稽汇总(期初/期末)经 recon_scorer.score_recon 通过,且每条 entry 经工单对账适配器
tx_from_gt_entry 能正确映射成打分引擎流水(金额>0、方向 IN/OUT)。语料随仓库,进 CI。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

import recon_scorer as rs  # noqa: E402

from services.recon import workorder_recon_adapter as adapter  # noqa: E402

_GT_DIR = (
    Path(__file__).resolve().parents[1] / "eval" / "vision_ablation_v2" / "bank" / "ground_truth"
)
_BANKS = ("kbank", "scb")


def _gt_files() -> list[Path]:
    files: list[Path] = []
    for bank in _BANKS:
        files.extend(sorted(_GT_DIR.glob(f"bank_{bank}_*.json")))
    return files


class BankCorpusChainTests(unittest.TestCase):
    def setUp(self):
        self.files = _gt_files()
        if not self.files:
            self.skipTest(f"缺银行金标语料:{_GT_DIR}")

    def test_kbank_and_scb_each_have_eight(self):
        for bank in _BANKS:
            n = len(list(_GT_DIR.glob(f"bank_{bank}_*.json")))
            self.assertEqual(n, 8, f"{bank} 应有 8 份金标,实得 {n}")

    def test_balance_chain_zero_violations(self):
        for f in self.files:
            gt = json.loads(f.read_text(encoding="utf-8"))
            chain = rs.balance_chain_violations(gt, cat="bank")
            self.assertEqual(chain["violations"], 0, f"{f.name} 余额链断:{chain['rows']}")
            self.assertGreater(chain["checked"], 0, f"{f.name} 无衔接可校验")

    def test_score_recon_passes_on_opening_closing(self):
        for f in self.files:
            gt = json.loads(f.read_text(encoding="utf-8"))
            actual = rs.aggregate_doc("bank", gt)
            score = rs.score_recon("bank", gt, actual)
            self.assertEqual(score["score"], 1.0, f"{f.name} 勾稽未过:{score['miss']}")

    def test_entries_map_to_scoring_tx(self):
        for f in self.files:
            gt = json.loads(f.read_text(encoding="utf-8"))
            for entry in gt.get("entries") or []:
                tx = adapter.tx_from_gt_entry(entry)
                self.assertIn(tx["direction"], ("IN", "OUT"), f"{f.name} 方向异常")
                self.assertGreater(tx["amount"], 0, f"{f.name} 金额非正:{entry}")
                self.assertTrue(tx["tx_date"], f"{f.name} 缺交易日期")


if __name__ == "__main__":
    unittest.main()
