# -*- coding: utf-8 -*-
"""「确认放行的推送没等到回执」这条诚实收尾,从队列一路到卡面都得接得上。

带 duplicate_confirmed 的推送关掉了写侧幂等闸,所以队列对它是至多一次(agent_store)。
至多一次就必须有收尾:租约过期还没回执,行落 manual + 一个原因码,而不是躺回 pending 装作
还在排队。这个码要能一路走到会计眼前 —— 上两次(PRIOR_DOC_STILL_IN_ERP、
DUPLICATE_CONTENT_DIFFERS)都是「后端产了码、前端不认」,卡上于是只剩一串英文,两次都是
上线以后才发现。这里把「产码的地方」与「翻码的地方」钉在同一个用例里。

桥那条腿的同一件事另有一个码(write_gate.CONFIRMED_UNACKED_CODE),它走管家文案层
(copy_erp_push),不走这张卡 —— 两条腿的收尾语义一致性也在本文件里比一次。
"""

import re
import unittest
from pathlib import Path

from services.erp.bridge import write_gate
from services.erp.express_push import agent_store
from services.steward import copy_erp_push, erp_push_tool

PROJECT_ROOT = Path(__file__).resolve().parents[2]

I18N_KEY = "erp-reason-confirmed-unacked"


def _card_source() -> str:
    return (PROJECT_ROOT / "src" / "home" / "erp-log-card.ts").read_text(encoding="utf-8")


def _i18n_texts(key: str) -> list:
    raw = (PROJECT_ROOT / "static" / "i18n-data.js").read_text(encoding="utf-8")
    return re.findall(rf"'{key}':\s*'([^']+)'", raw)


class ExpressQueueCloseoutSeam(unittest.TestCase):
    def test_the_reason_code_the_queue_writes_is_the_one_the_card_translates(self):
        """后端产的码与前端表里的键必须是同一个串 —— 这一族病根就是两头各写各的。"""
        self.assertEqual(agent_store.REASON_CONFIRMED_UNACKED, "confirmed_push_unacked")
        self.assertIn(
            f"{agent_store.REASON_CONFIRMED_UNACKED}: '{I18N_KEY}'",
            _card_source(),
        )

    def test_all_four_languages_exist_and_name_the_invoice(self):
        """四语齐 + 每句都留 {doc}:不点名核对哪一张,等于让她把整月的票翻一遍。"""
        texts = _i18n_texts(I18N_KEY)
        self.assertEqual(len(texts), 4, f"四语不齐:{texts}")
        for text in texts:
            self.assertIn("{doc}", text)
            self.assertIn("Express", text)

    def test_the_card_actually_substitutes_that_placeholder(self):
        """光有 {doc} 不算数 —— 这一支此前不做替换,占位符会原样印到屏幕上。"""
        card = _card_source()
        hit = re.search(
            r"const key = _EXPRESS_REASON_I18N\[code\];.*?\n\s*(?://[^\n]*\n\s*)*return[^\n]*\n",
            card,
            re.S,
        )
        self.assertIsNotNone(hit, "_expressFriendlyReason 的 EXPRESS 分支找不到了")
        self.assertIn("{doc}", hit.group(0))
        self.assertIn("invoice_no", hit.group(0))

    def test_the_copy_never_claims_it_was_or_was_not_written(self):
        """系统分不出写没写。说死任何一头都是撒谎,而「没写」这一头会直接导致她再推一次。"""
        for text in _i18n_texts(I18N_KEY):
            self.assertNotIn("duplicate_confirmed", text)
            self.assertNotIn("confirmed_push_unacked", text)

    def test_the_row_is_left_in_a_terminal_state_not_pending(self):
        """收尾 SQL 写的是 manual —— 留在 pending 就是「不重投也不说话」,最坏的一种。"""
        import inspect

        src = inspect.getsource(agent_store.close_unacked_confirmed)
        self.assertIn("SET status = 'manual'", src)
        self.assertIn("lease_owner = NULL", src)


class BridgeQueueCloseoutSeam(unittest.TestCase):
    def test_the_bridge_code_has_its_own_steward_copy_in_both_languages(self):
        """桥那条腿的收尾走管家文案层。缺一门语言,泰国会计拿到的是 KeyError 或中文。"""
        table = copy_erp_push.ERRORS[erp_push_tool.ERR_PUSH_UNCERTAIN]
        self.assertEqual(set(table), {"zh", "th"})
        for text in table.values():
            self.assertIn("{ref_no}", text)
            self.assertIn("{job_id}", text)
            self.assertIn("Express", text)

    def test_it_does_not_reuse_the_never_leased_wording(self):
        """「没人来领」那句写着「上线后再说一次」——对这条路照做就是账上两张。"""
        expired = copy_erp_push.ERRORS[erp_push_tool.ERR_PUSH_EXPIRED]
        uncertain = copy_erp_push.ERRORS[erp_push_tool.ERR_PUSH_UNCERTAIN]
        self.assertNotEqual(expired["zh"], uncertain["zh"])
        self.assertNotEqual(expired["th"], uncertain["th"])

    def test_the_two_legs_agree_on_the_confirm_key(self):
        """两条队列判「这是确认过的推送」用的是同一个载荷位,只是各查各的表。"""
        self.assertIn("duplicate_confirmed", agent_store._CONFIRMED)
        self.assertIn("duplicate_confirmed", write_gate._CONFIRMED)
        for sql in (agent_store._CONFIRMED, write_gate._CONFIRMED):
            for falsy in ("'false'", "'0'", "'null'"):
                self.assertIn(falsy, sql)


if __name__ == "__main__":
    unittest.main()
