# -*- coding: utf-8 -*-
"""图片歧义问询大脑适配器(services/agent/image_brain)· 通电守门。

一击式 JSON:合法 dict 原样透传(终端合法性在 image_intent._consult_brain 再守),
outcome 坏/非 dict → {} 让上层 fail-safe 回 default。
"""

import unittest
from unittest.mock import MagicMock, patch

from services.agent import image_brain as b


def _outcome(ok, data):
    o = MagicMock()
    o.ok = ok
    o.data = data
    return o


class TestDecideImage(unittest.TestCase):
    def _run(self, outcome):
        with patch("services.ai_gateway.transport.text_to_json", return_value=outcome) as t:
            out = b.decide_image({"doc_kind": "invoice", "confidence": "low"}, lang="zh")
        return out, t

    def test_valid_dict_passes_through(self):
        out, t = self._run(_outcome(True, {"terminal": "ask", "say": "问句"}))
        self.assertEqual(out["terminal"], "ask")
        # prompt 必带摘要与目标语言;只读终端白名单写死在提示词里。
        prompt = t.call_args.args[0]
        self.assertIn("confidence", prompt)
        self.assertIn("中文", prompt)
        self.assertIn("ห้ามเลือกส่งเข้า ERP", prompt)

    def test_bad_outcome_returns_empty(self):
        for o in (
            _outcome(False, {"terminal": "ask"}),
            _outcome(True, "junk"),
            _outcome(True, None),
        ):
            out, _ = self._run(o)
            self.assertEqual(out, {})


if __name__ == "__main__":
    unittest.main()
