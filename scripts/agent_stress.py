# -*- coding: utf-8 -*-
"""LINE 对话 Agent 混沌压测(离线·确定性 seed·真实路由代码)。

模拟 LINE 对话:消息池 = 语料全集 + 变异;模型层 = 随机脚本(合法回复/随机工具带
编造参数/defer/坏 JSON/复读/空——模型最坏情况);闸组合随机。逐轮断言四不变量:
  ① 入口永不把异常抛给用户(handle_expense_text 不炸)
  ② 单一出口:消费的轮恰一个用户可见出口
  ③ 无据入账:每笔入账草稿的金额要么为空要么出现在用户原文(钱路铁律)
  ④ 单一决策者:m3 开的轮 understand() 恒零

用法:python scripts/agent_stress.py [--rounds 500] [--seed 42]
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.unit import _agent_entry_harness as harness  # noqa: E402
from services.agent import loop, manifest  # noqa: E402

_CORPUS_DIR = Path(__file__).resolve().parents[1] / "tests" / "agent_corpus"

_FLAG_COMBOS = [
    {"enabled": False, "write": False},
    {"enabled": True, "write": False},
    {"enabled": True, "write": True},
    {"enabled": True, "write": True, "m3": True},
    {"enabled": True, "write": True, "m3": True, "push": True},
]


def _texts() -> list:
    pool = []
    for path in sorted(_CORPUS_DIR.glob("*.jsonl")):
        for ln in path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln:
                text = json.loads(ln).get("text")
                if text:
                    pool.append(str(text))
    return pool


def _mutate(rng: random.Random, text: str) -> str:
    roll = rng.random()
    if roll < 0.15:
        return text + " 😊"
    if roll < 0.25:
        return "  " + text + "  "
    if roll < 0.3:
        return text + " 5555"
    return text


def _chaos_script(rng: random.Random, rounds: int = 6) -> list:
    """随机模型行为序列(不看消息内容=最坏模型)。保证有限步内可终止。"""
    tools = [t.name for t in manifest.TOOLS] + ["ghost_tool"]
    script = []
    for _ in range(rounds):
        roll = rng.random()
        if roll < 0.30:
            script.append(
                {
                    "step": {
                        "kind": "reply",
                        "message": rng.choice(
                            ["ได้เลยค่ะ", "好的,帮你看看", "Here you go", "อยู่ตรงนี้นะคะ"]
                        ),
                    }
                }
            )
        elif roll < 0.55:
            args = {}
            if rng.random() < 0.5:
                args["amount"] = rng.choice([50, 80, 999, 711, 5555])
            if rng.random() < 0.3:
                args["keyword"] = rng.choice(["7-11", "makro", "ghost"])
            if rng.random() < 0.2:
                args["name"] = "สยามวัสดุ"
            script.append({"step": {"kind": "tool", "tool": rng.choice(tools), "args": args}})
        elif roll < 0.7:
            script.append(
                {"step": {"kind": "defer", "reason": rng.choice(["record", "edit", "x"])}}
            )
        elif roll < 0.8:
            script.append(
                {
                    "outcome": {
                        "ok": False,
                        "raw": rng.choice(["", '{"kind":"rep', "อยู่ตรงนี้เสมอนะคะ", "1" * 700]),
                    }
                }
            )
        elif roll < 0.9:
            script.append({"step": {"kind": "reply", "message_repeat": ["1", 600]}})
        else:
            script.append({"step": {"kind": "reply", "message": ""}})
    return script


def _make_decide_factory(script):
    """混沌 decide:脚本轮转,轮空后恒回一句(保证有限步)。数据面由 _db_patches 钉住。"""
    items = list(script)
    calls = []

    def decide(user_text, history, *, observations, lang, **kw):
        calls.append(lang)
        if not items:
            return loop.LoopStep(kind="reply", message="ค่ะ")
        it = items.pop(0)
        if "outcome" in it:
            from types import SimpleNamespace

            o = it["outcome"]
            return loop._parse_step(
                SimpleNamespace(ok=o.get("ok", False), data=o.get("data"), raw=o.get("raw", ""))
            )
        d = dict(it["step"])
        msg = d.get("message", "")
        if d.get("message_repeat"):
            frag, n = d["message_repeat"]
            msg = frag * int(n)
        return loop.LoopStep(
            kind=d.get("kind", ""),
            tool=d.get("tool"),
            args=d.get("args") or {},
            message=msg,
            say=d.get("say", ""),
        )

    return decide, calls


def _db_patches(cards):
    """钉住只读工具的数据面(canned·真 executor 代码全程跑)+ 捕获卡片类出口。"""
    from unittest.mock import patch

    return [
        patch(
            "core.db.list_ocr_history",
            return_value={
                "total": 2,
                "items": [
                    {"id": "h1", "seller_name": "7-11", "total_amount": 120, "invoice_no": "IV1"}
                ],
            },
        ),
        patch(
            "core.db.docs_overview",
            return_value={"doc_count": 2, "amount_total": 240, "by_category": []},
        ),
        patch(
            "core.db.get_billing_status_combined",
            return_value={"balance_thb": 100, "pages_used_this_month": 3, "allowed": True},
        ),
        patch("core.db.list_notification_logs", return_value=[]),
        patch("core.db.get_visible_client_ids_for_user", return_value=None),
        patch("core.db.list_push_logs", return_value={"items": []}),
        patch("core.db.counts_as_endpoint_success", return_value=False),
        patch(
            "core.db.list_erp_endpoints",
            return_value=[{"id": "e1", "name": "MR.ERP", "enabled": True}],
        ),
        patch(
            "core.db.get_default_erp_endpoint",
            return_value={"id": "e1", "name": "MR.ERP", "enabled": True},
        ),
        patch("core.db.has_recent_successful_push", return_value=None),
        patch("services.rd.rd_api.lookup_vat", return_value={"ok": False, "error": "not_found"}),
        patch("services.billing.subscription.get_active_subscription", return_value=None),
        patch(
            "services.line_binding.line_workspace.list_active",
            lambda cur, **k: [{"id": 1, "name": "สยามวัสดุ"}],
        ),
        patch("services.line_binding.line_workspace.current_workspace_id", lambda cur, **k: 1),
        patch("services.line_binding.line_workspace.set_current", lambda cur, **k: True),
        patch(
            "services.line_binding.line_workspace.match_by_name",
            lambda cur, **k: {"id": 1, "name": "สยามวัสดุ"},
        ),
        patch(
            "services.line_binding.line_reply.reply_messages_context",
            lambda rt, msgs, **k: cards.append(msgs),
        ),
    ]


def main() -> int:
    logging.disable(logging.CRITICAL)
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    texts = _texts()

    outcome_stats: Counter = Counter()
    violations = []
    for i in range(args.rounds):
        text = _mutate(rng, rng.choice(texts))
        flags = dict(rng.choice(_FLAG_COMBOS))
        case = {
            "id": f"stress-{i}",
            "lang": rng.choice(["th", "zh", "en", "ja"]),
            "text": text,
            "flags": flags,
            "script": _chaos_script(rng),
            "understand": None,
            "skip_correct_flow": rng.random() < 0.3,
        }
        cards: list = []
        try:
            from contextlib import ExitStack

            with ExitStack() as stack:
                for pt in _db_patches(cards):
                    stack.enter_context(pt)
                r = harness.run_entry(case, lambda c: _make_decide_factory(c.get("script") or []))
        except Exception as e:  # 不变量①:入口不许炸
            violations.append((case["id"], f"EXCEPTION {type(e).__name__}: {e}", text))
            continue
        outs = (
            len(r.says)
            + len(r.pools)
            + len(r.do_records)
            + len(r.multis)
            + len(r.undos)
            + len(r.edits)
            + len(cards)
        )
        if r.consumed and outs != 1:
            violations.append((case["id"], f"出口数 {outs}", text))
        if not r.consumed and outs != 0:
            violations.append((case["id"], f"未消费却有出口 {outs}", text))
        for rec in r.do_records:
            draft = rec[0][5]
            amt = getattr(draft, "amount", None)
            if amt is not None and str(amt) not in text and f"{amt:,}" not in text:
                violations.append((case["id"], f"无据入账 amount={amt}", text))
        if flags.get("m3") and r.understand_calls:
            violations.append((case["id"], "m3 开却调了旧 LLM", text))
        outcome_stats["consumed" if r.consumed else "fallthrough"] += 1
        for name in ("says", "pools", "do_records", "multis", "undos", "edits"):
            if getattr(r, name):
                outcome_stats[name] += 1
        if cards:
            outcome_stats["cards"] += 1
        if (i + 1) % 100 == 0:
            print(f"  ... {i + 1}/{args.rounds} 轮 · 违例 {len(violations)}")

    print("\n== agent_stress 结果 ==")
    print(f"轮数 {args.rounds} · seed {args.seed}")
    for k, v in sorted(outcome_stats.items()):
        print(f"  {k:<12} {v}")
    if violations:
        print(f"\n[FAIL] 不变量违例 {len(violations)} 条:")
        for vid, why, text in violations[:20]:
            print(f"  - {vid}: {why} · text={text[:40]!r}")
        return 1
    print("\n[OK] 四不变量全轮通过(不炸/单出口/无据不入账/单一决策者)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
