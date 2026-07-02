# -*- coding: utf-8 -*-
"""图片意图分流决策核(services/agent/image_intent)· 语料驱动回归 + 红线守门。

语料 suite="image" 逐条驱动 route_image(scripted 大脑,零真模型零 DB):
终端/端点/套账/dropped_push 全断言。红线单测另锁:大脑永远拿不到 push 权、
决策核永远不抛(fail-safe default)、闸关=default。
"""

import json
import unittest
from pathlib import Path

from services.agent.image_intent import ImageRoute, route_image

_CORPUS = Path(__file__).resolve().parents[1] / "agent_corpus" / "corpus.jsonl"


def _image_cases():
    for line in _CORPUS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        case = json.loads(line)
        if case.get("suite") == "image":
            yield case


def _scripted_decide(script):
    """语料 script → decide 注入:列表=依次吐 dict;"raise"=模拟大脑炸。"""
    if script == "raise":

        def _boom(summary, lang="th"):
            raise RuntimeError("brain down")

        return _boom
    steps = list(script or [])

    def _decide(summary, lang="th"):
        return steps.pop(0) if steps else {}

    return _decide


class TestImageIntentCorpus(unittest.TestCase):
    def test_corpus_image_suite(self):
        cases = list(_image_cases())
        self.assertGreaterEqual(len(cases), 16, "image 语料只增不删")
        for case in cases:
            with self.subTest(case["id"]):
                route = route_image(
                    case.get("summary") or {},
                    pending=case.get("pending"),
                    gates=frozenset(case.get("gates") or []),
                    decide=_scripted_decide(case["script"]) if "script" in case else None,
                    lang=case.get("lang") or "th",
                )
                exp = case["expect"]
                self.assertEqual(route.terminal, exp["terminal"], case["probe"])
                if "endpoint" in exp:
                    self.assertEqual(route.endpoint_name, exp["endpoint"])
                if "workspace" in exp:
                    self.assertEqual(route.workspace, exp["workspace"])
                if "question" in exp:
                    self.assertEqual(route.question, exp["question"])
                self.assertIs(route.dropped_push, bool(exp.get("dropped_push", False)))


class TestImageIntentRedlines(unittest.TestCase):
    """红线:语料之外的死守(实现改了这些也不许破)。"""

    _AMBIG = {"doc_kind": "unknown", "confidence": "high"}
    _GATES = frozenset({"image", "push"})

    def test_brain_can_never_reach_push(self):
        # 大脑吐什么都到不了 push/both:不可逆动作必须来自用户原话。
        for overreach in ({"terminal": "push"}, {"terminal": "both"}, {"terminal": "delete"}):
            route = route_image(
                self._AMBIG, gates=self._GATES, decide=lambda s, lang="th", d=overreach: d
            )
            self.assertNotIn(route.terminal, ("push", "both"))
            self.assertEqual(route.terminal, "ask")

    def test_brain_garbage_never_raises(self):
        # 各种畸形输出都不许把图搞丢:统一 fail-safe(default 或 ask,绝不抛)。
        for garbage in (None, "text", 42, [], {"say": "no kind"}):
            route = route_image(
                self._AMBIG, gates=self._GATES, decide=lambda s, lang="th", g=garbage: g
            )
            self.assertIsInstance(route, ImageRoute)

    def test_gate_off_is_default(self):
        # image 闸不在 gates → 永远 default(接线层双保险,守 byte-identical)。
        route = route_image({"doc_kind": "id_card"}, pending={"goals": ["push"]}, gates=frozenset())
        self.assertEqual(route.terminal, "default")

    def test_clear_invoice_never_consults_brain(self):
        # 主流量(清晰票+没意图)绝不问大脑——问了就是打扰+延迟+成本。
        def _forbidden(summary, lang="th"):
            raise AssertionError("brain consulted on clear invoice")

        route = route_image(
            {"doc_kind": "invoice", "confidence": "high"}, gates=self._GATES, decide=_forbidden
        )
        self.assertEqual(route.terminal, "default")


class TestImageIntentFuzz(unittest.TestCase):
    """确定性混沌(种子固定·进 CI):随机意图/摘要/闸/大脑行为轰决策核,三不变量恒真。"""

    def test_invariants_hold_under_chaos(self):
        import random

        rng = random.Random(42)
        goals_pool = ["record", "push", "archive_only", "nothing", "fly", ""]
        kinds = ["invoice", "id_card", "unknown", "", None]
        brains = [
            None,
            lambda s, lang="th": {
                "terminal": rng.choice(["push", "both", "ask", "record", "junk"])
            },
            lambda s, lang="th": (_ for _ in ()).throw(RuntimeError("boom")),
            lambda s, lang="th": rng.choice([None, "prose", 42, [], {}]),
        ]
        for i in range(500):
            pending = (
                None
                if rng.random() < 0.4
                else {
                    "goals": rng.sample(goals_pool, rng.randint(0, 3)),
                    "push_to": rng.choice([None, "MR.ERP", ""]),
                    "book_to_id": rng.choice([None, 84]),
                }
            )
            gates = frozenset(
                g for g in ("image", "push") if rng.random() < (0.7 if g == "image" else 0.5)
            )
            summary = {"doc_kind": rng.choice(kinds), "confidence": rng.choice(["high", "low", ""])}
            route = route_image(
                summary, pending=pending, gates=gates, decide=rng.choice(brains), lang="th"
            )
            # 不变量一:永不炸、必有合法终端。
            self.assertIsInstance(route, ImageRoute, i)
            # 不变量二:image 闸关 = 恒 default(现状契约)。
            if "image" not in gates:
                self.assertEqual(route.terminal, "default", i)
            # 不变量三:push/both 只可能来自用户明说(pending 含 push)且 push 闸开。
            if route.terminal in ("push", "both"):
                self.assertIn("push", gates, i)
                self.assertIn("push", (pending or {}).get("goals") or [], i)


if __name__ == "__main__":
    unittest.main()
