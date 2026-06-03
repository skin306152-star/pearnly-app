# -*- coding: utf-8 -*-
"""
v118.35.0.52 · 合成账单模糊测试(property-based)· 系统性压测银行对账逻辑

思路:随机生成大量"余额自洽"的合成账单(已知正确答案)· 再注入真实 OCR 会犯的错误
· 验证下游逻辑(方向纠正 + 余额验证 + 去重 + 合并)是否正确纠正/标记。
不依赖外部账单 · 无 OCR 成本 · 答案已知 · 专挖逻辑 bug。

锁定的不变式(invariants):
  A 干净账单(方向正确·期初已知)→ 0 误报 · 0 误纠正
  B 方向被读反(金额对)→ 全部自动摆正 · 0 误报
  C 某行金额读错(余额对不上)→ 该行被标 False(不能被"纠正"掩盖)
  D 同日同额但余额不同的两笔 → 不被去重删除
  E 续页(期初未知)干净账单 → 0 误报(首行 None)
"""

import random
import unittest
from datetime import date, timedelta

from services.recon.bank_recon_v2 import (
    StatementRow,
    GlRow,
    _correct_direction_from_balance,
    _verify_row_balances,
    merge_statements,
    reconcile,
    _stmt_bad_ratio,
)

ITERS = 300


def _gen_clean(rng, n, opening):
    """生成余额自洽的 (direction, amount, balance) 序列 · 余额不走负太离谱"""
    out = []
    bal = opening
    for _ in range(n):
        amt = round(rng.uniform(1, 5_000_000), 2)
        # 偏向存款使余额不至于一直为负(但允许偶尔透支)
        is_dep = rng.random() < 0.55 or bal < amt
        if is_dep:
            bal = round(bal + amt, 2)
            out.append(("dep", amt, bal))
        else:
            bal = round(bal - amt, 2)
            out.append(("wd", amt, bal))
    return out


def _to_rows(seq, swap_idx=None, base_day=date(2025, 1, 2)):
    """seq -> StatementRow 列表 · swap_idx 中的行故意把方向放反(模拟 OCR 列错位)"""
    rows = []
    for i, (d, amt, bal) in enumerate(seq):
        dep = wd = 0.0
        flip = swap_idx is not None and i in swap_idx
        real_dep = d == "dep"
        if real_dep != flip:  # flip 时取反
            dep = amt
        else:
            wd = amt
        rows.append(
            StatementRow(
                date=base_day + timedelta(days=i),
                description=f"tx{i}",
                withdrawal=wd,
                deposit=dep,
                balance=bal,
            )
        )
    return rows


class SyntheticFuzzTests(unittest.TestCase):

    def test_A_clean_no_false_no_overcorrect(self):
        rng = random.Random(1)
        for _ in range(ITERS):
            opening = round(rng.uniform(1000, 5_000_000), 2)
            seq = _gen_clean(rng, rng.randint(1, 20), opening)
            rows = _to_rows(seq)
            _correct_direction_from_balance(rows, opening)
            _verify_row_balances(rows, opening)
            self.assertEqual([r for r in rows if r.balance_ok is False], [], "干净账单不应有误报")
            self.assertEqual(
                [r for r in rows if r.direction_autocorrected], [], "干净账单不应被误纠正"
            )

    def test_B_direction_swap_fully_corrected(self):
        rng = random.Random(2)
        for _ in range(ITERS):
            opening = round(rng.uniform(1000, 5_000_000), 2)
            n = rng.randint(2, 20)
            seq = _gen_clean(rng, n, opening)
            # 随机挑若干行把方向放反
            k = rng.randint(1, n)
            swap = set(rng.sample(range(n), k))
            rows = _to_rows(seq, swap_idx=swap)
            _correct_direction_from_balance(rows, opening)
            _verify_row_balances(rows, opening)
            self.assertEqual(
                [i for i, r in enumerate(rows) if r.balance_ok is False],
                [],
                "方向反但金额对 → 应被全部摆正 · 不该有误报",
            )

    def test_C_wrong_amount_is_flagged(self):
        rng = random.Random(3)
        flagged_ok = 0
        for _ in range(ITERS):
            opening = round(rng.uniform(1000, 5_000_000), 2)
            n = rng.randint(2, 15)
            seq = _gen_clean(rng, n, opening)
            rows = _to_rows(seq)
            k = rng.randrange(n)
            # 篡改第 k 行金额(余额保持不变 → 金额对不上余额涨跌)
            bad = round(rows[k].withdrawal or rows[k].deposit, 2)
            delta = round(bad + rng.uniform(10, 1000), 2)
            if rows[k].withdrawal > 0:
                rows[k].withdrawal = delta
            else:
                rows[k].deposit = delta
            _correct_direction_from_balance(rows, opening)
            _verify_row_balances(rows, opening)
            # 被篡改的行必须被标 False(不能被掩盖)· 续页首行(k==0且opening可靠这里opening可靠)
            self.assertFalse(rows[k].balance_ok, f"金额读错的行(idx={k})必须被标 False")
            flagged_ok += 1
        self.assertEqual(flagged_ok, ITERS)

    def test_D_distinct_same_amount_not_deduped(self):
        rng = random.Random(4)
        for _ in range(ITERS):
            opening = round(rng.uniform(1000, 5_000_000), 2)
            amt = round(rng.uniform(10, 100000), 2)
            b1 = round(opening - amt, 2)
            b2 = round(b1 - amt, 2)
            a = StatementRow(
                date=date(2025, 3, 30), description="FEE", withdrawal=amt, deposit=0, balance=b1
            )
            b = StatementRow(
                date=date(2025, 3, 30), description="FEE", withdrawal=amt, deposit=0, balance=b2
            )
            merged, _o, _c, _bc = merge_statements(
                [{"ok": True, "bank_code": "x", "rows": [a, b], "opening": opening, "closing": b2}]
            )
            self.assertEqual(len(merged), 2, "同额不同余额的两笔不应被去重")

    def test_E_continuation_clean_no_false(self):
        rng = random.Random(5)
        for _ in range(ITERS):
            # 续页:opening 未知(0)· 第一行从某个真实余额开始
            start_bal = round(rng.uniform(100000, 5_000_000), 2)
            n = rng.randint(2, 15)
            seq = []
            bal = start_bal
            seq.append(
                ("wd" if rng.random() < 0.5 else "dep", round(rng.uniform(1, 100000), 2), bal)
            )
            for _ in range(n - 1):
                amt = round(rng.uniform(1, 500000), 2)
                if rng.random() < 0.55 or bal < amt:
                    bal = round(bal + amt, 2)
                    seq.append(("dep", amt, bal))
                else:
                    bal = round(bal - amt, 2)
                    seq.append(("wd", amt, bal))
            rows = _to_rows(seq)
            _correct_direction_from_balance(rows, 0.0)  # opening 未知
            _verify_row_balances(rows, 0.0)
            self.assertEqual(
                [i for i, r in enumerate(rows) if r.balance_ok is False],
                [],
                "续页干净账单不应有误报",
            )

    def test_F_mixed_swap_and_wrong_amount(self):
        """混合:部分行方向反(金额对)+ 1 行金额错 → 方向反的全纠正 · 金额错的被标 False · 不互相污染"""
        rng = random.Random(6)
        for _ in range(ITERS):
            opening = round(rng.uniform(1000, 5_000_000), 2)
            n = rng.randint(3, 18)
            seq = _gen_clean(rng, n, opening)
            bad_idx = rng.randrange(n)
            swap = set(i for i in rng.sample(range(n), rng.randint(1, n)) if i != bad_idx)
            rows = _to_rows(seq, swap_idx=swap)
            # 篡改 bad_idx 金额(余额不变)
            orig = rows[bad_idx].withdrawal or rows[bad_idx].deposit
            newv = round(orig + rng.uniform(10, 1000), 2)
            if rows[bad_idx].withdrawal > 0:
                rows[bad_idx].withdrawal = newv
            else:
                rows[bad_idx].deposit = newv
            _correct_direction_from_balance(rows, opening)
            _verify_row_balances(rows, opening)
            false_idx = [i for i, r in enumerate(rows) if r.balance_ok is False]
            self.assertIn(bad_idx, false_idx, "金额错的行必须被标")
            self.assertEqual(
                [i for i in false_idx if i != bad_idx],
                [],
                "除金额错的行外不应有其它误报(方向反的应已纠正)",
            )

    def test_G_dropped_row_is_flagged(self):
        """OCR 漏掉中间一笔 → 缺口处下一行余额对不上 → 被标 False(不被掩盖)"""
        rng = random.Random(7)
        caught = 0
        for _ in range(ITERS):
            opening = round(rng.uniform(1000, 5_000_000), 2)
            n = rng.randint(4, 18)
            seq = _gen_clean(rng, n, opening)
            drop = rng.randrange(1, n - 1)  # 不删首尾
            kept = seq[:drop] + seq[drop + 1 :]
            rows = _to_rows(kept)
            _correct_direction_from_balance(rows, opening)
            _verify_row_balances(rows, opening)
            # 删行后 · 缺口处那行(原 drop+1 → 现在 index=drop)余额跳变 · 应被标
            # 除非巧合 |delta|==amount(极少)· 统计大多数被标
            if rows[drop].balance_ok is False:
                caught += 1
        # 漏行绝大多数应被标(允许极少数巧合)
        self.assertGreater(caught, ITERS * 0.9, f"漏行应绝大多数被标 · 实际 {caught}/{ITERS}")

    def test_H_reconcile_matches_clean(self):
        """对账配对:干净的 stmt+GL(金额/日期/方向都对)→ 全部 matched · 无孤立项"""
        rng = random.Random(8)
        for _ in range(ITERS):
            n = rng.randint(1, 12)
            stmt_rows, gl_rows = [], []
            bal = 1_000_000.0
            for i in range(n):
                amt = round(rng.uniform(10, 500000), 2)
                d = date(2025, 6, 1) + timedelta(days=i)
                is_dep = rng.random() < 0.5
                if is_dep:
                    bal = round(bal + amt, 2)
                    stmt_rows.append(
                        StatementRow(
                            date=d, description=f"s{i}", withdrawal=0, deposit=amt, balance=bal
                        )
                    )
                    # 存款(钱进银行)= GL 借方
                    gl_rows.append(
                        GlRow(
                            date=d,
                            doc_no=f"G{i}",
                            account_code="1111",
                            description=f"g{i}",
                            debit=amt,
                            credit=0,
                        )
                    )
                else:
                    bal = round(bal - amt, 2)
                    stmt_rows.append(
                        StatementRow(
                            date=d, description=f"s{i}", withdrawal=amt, deposit=0, balance=bal
                        )
                    )
                    gl_rows.append(
                        GlRow(
                            date=d,
                            doc_no=f"G{i}",
                            account_code="1111",
                            description=f"g{i}",
                            debit=0,
                            credit=amt,
                        )
                    )
            recon_rows, summary = reconcile(stmt_rows, gl_rows)
            unmatched = [r for r in recon_rows if r.match_status != "matched"]
            self.assertEqual(unmatched, [], "干净对齐的 stmt+GL 应全部匹配")


class QualityGateTests(unittest.TestCase):
    """v118.35.0.52 · _stmt_bad_ratio 质量闸门 · 决定免费解析是否回退 Gemini"""

    def test_clean_low_ratio(self):
        """干净自洽账单 → bad_ratio ≈ 0 · 不触发 Gemini"""
        rng = random.Random(11)
        seq = _gen_clean(rng, 12, 100000.0)
        rows = _to_rows(seq)
        self.assertLess(_stmt_bad_ratio(rows, 100000.0), 0.30)

    def test_zero_balances_high_ratio(self):
        """余额列读成 0(BAY/KBank 真实失败)→ bad_ratio 高 · 触发 Gemini"""
        rows = [
            StatementRow(
                date=date(2025, 1, i + 1), description="x", withdrawal=700.0, deposit=0, balance=0.0
            )
            for i in range(10)
        ]
        self.assertGreater(_stmt_bad_ratio(rows, 0.0), 0.30)

    def test_direction_only_wrong_stays_low(self):
        """只是方向反、余额正确(SCB)→ bad_ratio 低 · 不浪费 Gemini(交给 v0.50 纠正)"""
        rng = random.Random(12)
        seq = _gen_clean(rng, 12, 100000.0)
        n = len(seq)
        rows = _to_rows(seq, swap_idx=set(range(n)))  # 全部方向反 · 但余额对
        self.assertLess(_stmt_bad_ratio(rows, 100000.0), 0.30)

    def test_id_as_amount_high_ratio(self):
        """把交易ID当金额(KBank 20位数)→ 金额对不上余额 → bad_ratio 高"""
        rows = [
            StatementRow(
                date=date(2025, 1, 1), description="x", withdrawal=0, deposit=0, balance=100000.0
            ),
            StatementRow(
                date=date(2025, 1, 2),
                description="id",
                withdrawal=2.026e19,
                deposit=0,
                balance=99000.0,
            ),
            StatementRow(
                date=date(2025, 1, 3),
                description="id",
                withdrawal=1.5e18,
                deposit=0,
                balance=98000.0,
            ),
            StatementRow(
                date=date(2025, 1, 4),
                description="id",
                withdrawal=9.9e18,
                deposit=0,
                balance=97000.0,
            ),
        ]
        self.assertGreater(_stmt_bad_ratio(rows, 100000.0), 0.30)


if __name__ == "__main__":
    unittest.main()
