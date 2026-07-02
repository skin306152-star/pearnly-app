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


if __name__ == "__main__":
    unittest.main()
