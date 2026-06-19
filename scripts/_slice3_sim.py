# -*- coding: utf-8 -*-
"""真机场景离线模拟(Slice 3 锚点契约 + 加油票总额)— 驱动真实代码,打印 before/after 报告。

不连真 LINE/Vision/DB:加油走真实 normalize+build_draft;锚点走改错回放 Sim 驱动真实
line_anchored.dispatch(引用 = sim.refs 里有锚点 = 发卡时已登记)。复现两张真机截图的序列。
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.expense import line_anchored  # noqa: E402
from services.purchase import intake as ik  # noqa: E402
from services.purchase import totals as totals_svc  # noqa: E402
from tests.unit.test_line_correct_replay import Sim, _drive  # noqa: E402


def _grand(fields, kind="expense"):
    d = ik.build_draft_from_invoice(fields, kind=kind)
    return totals_svc.compute_purchase_totals(
        d["lines"], rounding=Decimal(str(d.get("rounding", 0) or 0))
    )["grand_total"]


def sim_fuel():
    print("\n=== 加油票总额(Bangchak 真票:净额 1,780 · 升 44.67 · 单价 39.85 · 积分 22/785)===")
    misread = {
        "document_type": "tax_invoice",
        "seller_name": "BANGCHAK BGN-CHAARANSAN",
        "total_amount": "1000",  # 真机误读
        "items": [
            {"name": "ไฮดีเซล S", "qty": "44.67", "price": "39.85", "subtotal": "1780"},
            {"name": "คะแนนสะสม", "qty": "22", "price": "39.85", "subtotal": "785"},
        ],
    }
    before = misread["total_amount"]
    fixed = ik.normalize_ocr_fields(misread)
    print(f"  OCR 读到 total_amount = {before}(真机卡片显示 ฿1000)")
    print(f"  确定性兜底后 total_amount = {fixed['total_amount']}  corrections={fixed.get('_corrections')}")
    print(f"  入账 grand_total = {_grand(fixed)}  (期望 1780.00·永不 1000·积分 22 不计)")


def _run_anchored(sim, turns):
    bound = {"id": "u1", "tenant_id": "t"}
    return _drive(
        sim,
        turns,
        lambda norm, quoted, ctx: line_anchored.dispatch(
            bound, "tok", "u1", norm, "th", "t", 1, quoted, ctx
        ),
    )


def sim_anchor():
    print("\n=== 可引用卡片契约:拍票出草稿卡 → 引用它操作(真机截图序列)===")
    print("[修复前] 图片卡走裸 push,没登记锚点 → 引用任何话 = ANCHOR_EXPIRED(真机三连失败)")
    sim = Sim()  # 不 seed → 模拟"卡未登记锚点"
    for msg in ("กาแฟ 65", "ขอบคุณ", "เดือนนี้ใช้จ่ายเท่าไหร่"):
        steps = _run_anchored(sim, [(msg, "MID_OCRCARD")])
        reply = steps[0][2][-1] if steps[0][2] else ""
        print(f"  引用卡 + 「{msg}」→ {reply[:48]}")

    print("\n[修复后] 图片卡发出即 anchor_card 登记锚点(sim.seed 即代表已登记)→ 引用按当前状态处理")
    sim = Sim()
    sim.seed("OCR1", lines=1, status="draft", seller="BANGCHAK")  # 拍票出的草稿卡(已登记)
    cases = [
        ("กาแฟ 65", "像新记账 → 不另记,建议改这张"),
        ("ขอบคุณ", "闲聊 → 锚定追问,不跑题"),
        ("จำนวนเงินเป็น 1780", "改金额 → 进确认(再「ใช่」落值)"),
    ]
    for msg, expect in cases:
        steps = _run_anchored(sim, [(msg, "MID_OCR1")])
        reply = steps[0][2][-1] if steps[0][2] else ""
        anchored = "ANCHOR_EXPIRED" not in reply and "หมดอายุ" not in reply
        print(f"  引用卡 + 「{msg}」→ {'锚定✓' if anchored else 'EXPIRED✗'} | {expect}")
        print(f"      回复: {reply[:60]}")

    print("\n[修复后] 引用已撤销终态卡说「恢复」→ 重建(终态卡也登记了锚点)")
    sim = Sim()
    sim.seed("V1", lines=1, status="posted", seller="BANGCHAK")
    steps = _run_anchored(sim, [("ลบ", "MID_V1"), ("กู้คืน", "MID_V1")])
    for (msg, _, replies) in steps:
        print(f"  引用卡 + 「{msg}」→ {(replies[-1] if replies else '')[:56]}")
    restored = [d for d in sim.docs.values() if d["doc"].get("restored_from") == "V1"]
    print(f"  恢复结果:重建活单 {len(restored)} 张(原死单状态={sim.docs['V1']['doc']['status']})")


if __name__ == "__main__":
    sim_fuel()
    sim_anchor()
    print("\n（离线模拟·驱动真实 normalize/build_draft 与 line_anchored.dispatch）")
