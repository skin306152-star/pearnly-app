# -*- coding: utf-8 -*-
"""LINE 改错状态机回放压测器(P1E-2 收口 · 本地模拟多轮对话 · 不碰真 LINE/OCR/DB)。

在内存里模拟单据库 + pending + 消息引用,驱动真实 `line_correct_flow.route` 状态机跑批量场景,
断言:动作类型(直接改/问缺失/确认/详情页/取消/删除/交大脑)、字段最终值、禁止文案不出现
(请长按回复 / 找不到记录 / 重新拍照)、pending 不串线。__main__ 打 scenario 报告。
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

if __package__ in (None, ""):  # 允许 `python tests/unit/..._replay.py` 直接出报告
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.expense import (  # noqa: E402
    conversation,
    line_classify,
    line_correct,
    line_correct_data,
    line_correct_flow as flow,
)
from services.line_binding import line_client, line_message_refs, line_reply
from services.purchase import correct as correct_svc
from services.purchase import docs as docs_svc
from services.purchase import posting as posting_svc
from services.purchase import settings as settings_svc

# 同一会话 active_doc_id 内绝不该再吐的泛化指引(中泰双语·按真实 i18n 取)。
_FORBIDDEN = {
    line_client.t_line(lg, key)
    for lg in ("th", "zh")
    for key in ("line_need_reply_record", "guide_detail_list", "photo_failed")
}


class _Cur:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Sim:
    """内存账本:docs(单据)+ pending(会话态)+ refs(消息→单据)+ replies(机器人回复)。"""

    def __init__(self):
        self.docs: dict = {}
        self.pending: dict = {}
        self.refs: dict = {}
        self.replies: list = []
        self._seq = 0

    def seed(self, doc_id, *, status="draft", lines=1, **doc):
        base = {
            "id": doc_id,
            "status": status,
            "grand_total": "70.00",
            "doc_date": "2026-06-01",
            "payment_method": None,
            "category_id": None,
        }
        base.update(doc)
        self.docs[doc_id] = {
            "doc": base,
            "supplier": {"name": doc.get("seller", "ร้านเดิม"), "tax_id": None},
            "lines": [
                {"unit_price": "70", "qty": "1", "description": f"x{i}"} for i in range(lines)
            ],
        }
        self.refs[f"MID_{doc_id}"] = (1, doc_id)

    # ---- conversation 桩(签名对齐真函数:cur 位置参 + 关键字) ----
    def peek(self, cur, *, line_user_id, **k):
        return self.pending.get(line_user_id)

    def save(self, cur, *, line_user_id, tenant_id, workspace_client_id, draft, missing):
        self.pending[line_user_id] = {
            "missing": missing,
            "draft": draft,
            "tenant_id": tenant_id,
            "workspace_client_id": workspace_client_id,
        }

    def clear(self, cur, *, line_user_id):
        self.pending.pop(line_user_id, None)

    # ---- docs/posting 桩 ----
    def get_doc(self, cur, *, tenant_id, workspace_client_id, doc_id):
        d = self.docs.get(doc_id)
        return (
            {k: (v.copy() if isinstance(v, dict) else list(v)) for k, v in d.items()} if d else None
        )

    def update_draft(
        self, cur, *, tenant_id, workspace_client_id, created_by, doc_id, data, settings
    ):
        d = self.docs[doc_id]
        if data.get("doc_date"):
            d["doc"]["doc_date"] = data["doc_date"]
        if data.get("supplier"):
            d["supplier"]["name"] = data["supplier"]["name"]
        if "payment_method" in data:
            d["doc"]["payment_method"] = data["payment_method"]
        if data.get("category_id"):
            d["doc"]["category_id"] = data["category_id"]
        if data.get("lines"):
            d["lines"] = data["lines"]
            d["doc"]["grand_total"] = str(
                data["lines"][0].get("unit_price") or d["doc"]["grand_total"]
            )
        return self.get_doc(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=doc_id
        )

    def delete_doc(self, cur, *, tenant_id, workspace_client_id, doc_id):
        self.docs.pop(doc_id, None)

    def void_doc(self, cur, *, tenant_id, workspace_client_id, doc_id, created_by):
        self.docs[doc_id]["doc"]["status"] = "void"
        return self.docs[doc_id]

    def correct_doc(self, cur, *, tenant_id, workspace_client_id, doc_id, created_by):
        # 真 correct_doc:作废原单 + 克隆为新草稿(更正审计链)。
        self._seq += 1
        nid = f"{doc_id}_c{self._seq}"
        self.docs[nid] = {
            k: (v.copy() if isinstance(v, dict) else list(v)) for k, v in self.docs[doc_id].items()
        }
        self.docs[nid]["doc"] = dict(self.docs[doc_id]["doc"], id=nid, status="draft")
        self.docs[doc_id]["doc"]["status"] = "void"  # 原单作废(再引用应跟随 active 到克隆)
        return self.get_doc(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=nid
        )

    def _active_doc_date(self):
        """当前 active 续接态指向那张单的日期(测续接命中)。"""
        m = self.pending.get("u1", {}).get("missing", "")
        if m.startswith("correctactive:"):
            did = m.split(":")[-1]
            return self.docs.get(did, {}).get("doc", {}).get("doc_date")
        return None

    def resolve_target(self, cur, *, tenant_id, ws, line_user_id, quoted_message_id, text):
        if quoted_message_id and quoted_message_id in self.refs:
            w, d = self.refs[quoted_message_id]
            return {"ws": w, "doc_id": d, "error": None}
        return {"ws": ws, "doc_id": None, "error": "ambiguous"}


def _run(sim, turns):
    """驱动一串用户消息 → 真 flow.route(每条返回是否被改错路由接管)。返回 [(text, handled)]。"""
    bound = {"id": "u1", "tenant_id": "t"}
    out = []
    with (
        mock.patch.object(flow.db, "get_cursor_rls", return_value=_Cur()),
        mock.patch.object(line_correct.db, "get_cursor_rls", return_value=_Cur()),
        mock.patch.object(conversation, "peek_pending", side_effect=sim.peek),
        mock.patch.object(conversation, "save_pending", side_effect=sim.save),
        mock.patch.object(conversation, "clear_pending", side_effect=sim.clear),
        mock.patch.object(docs_svc, "get_doc", side_effect=sim.get_doc),
        mock.patch.object(docs_svc, "update_draft", side_effect=sim.update_draft),
        mock.patch.object(docs_svc, "delete_doc", side_effect=sim.delete_doc),
        mock.patch.object(posting_svc, "void_doc", side_effect=sim.void_doc),
        mock.patch.object(posting_svc, "post_doc", side_effect=lambda *a, **k: None),
        mock.patch.object(correct_svc, "correct_doc", side_effect=sim.correct_doc),
        mock.patch.object(settings_svc, "get_settings", return_value={"auto_book": False}),
        mock.patch.object(line_correct_data, "_resolve_category", return_value=("cat1", "sub1")),
        mock.patch.object(line_message_refs, "resolve_target", side_effect=sim.resolve_target),
        mock.patch.object(
            line_reply,
            "reply_text_context",
            side_effect=lambda tok, body, **k: sim.replies.append(body),
        ),
        mock.patch.object(
            line_reply,
            "reply_messages_context",
            side_effect=lambda tok, msgs, **k: sim.replies.extend(
                m.get("altText", "") for m in msgs
            ),
        ),
    ):
        for text, quoted in turns:
            sim.replies.clear()
            norm = line_classify.normalize_user_text(text)
            ctx = {"quote_token": "q", "line_user_id": "u1", "tenant_id": "t"}
            handled = flow.route(bound, "tok", "u1", norm, "th", "t", 1, quoted, ctx)
            out.append((text, handled, list(sim.replies)))
    return out


class ReplayScenarioTests(unittest.TestCase):
    def setUp(self):
        self.sim = Sim()
        self.sim.seed("D1", lines=1)  # 草稿单行
        self.sim.seed("D2", lines=3)  # 草稿多行
        self.sim.seed("D3", lines=1, status="posted")  # 已入账

    def _last_reply(self, steps):
        return steps[-1][2][-1] if steps[-1][2] else ""

    def _no_forbidden(self, steps):
        for _, _, replies in steps:
            for r in replies:
                self.assertNotIn(r, _FORBIDDEN, f"会话内吐了泛化指引:{r}")

    def test_date_wrong_then_value(self):
        steps = _run(self.sim, [("วันที่ผิด", "MID_D1"), ("2026/6/18", None)])
        self.assertTrue(steps[0][1] and steps[1][1])
        self.assertEqual(self.sim.docs["D1"]["doc"]["doc_date"], "2026-06-18")
        self._no_forbidden(steps)

    def test_date_today_one_shot(self):
        steps = _run(self.sim, [("เปลี่ยนวันที่เป็นวันนี้", "MID_D1")])
        self.assertTrue(steps[0][1])
        from services.expense.line_quick_entry import _today

        self.assertEqual(self.sim.docs["D1"]["doc"]["doc_date"], _today().isoformat())

    def test_seller_one_shot(self):
        steps = _run(self.sim, [("ร้านค้าเป็น 7-11", "MID_D1")])
        self.assertEqual(self.sim.docs["D1"]["supplier"]["name"], "7-11")

    def test_seller_fullwidth_colon(self):
        steps = _run(self.sim, [("แก้ร้านค้าเป็น：7-11", "MID_D1")])  # 全角冒号
        self.assertEqual(self.sim.docs["D1"]["supplier"]["name"], "7-11")

    def test_field_switch_date_to_seller(self):
        steps = _run(self.sim, [("วันที่ผิด", "MID_D1"), ("ร้านค้าเป็น 7-11", None)])
        self.assertEqual(self.sim.docs["D1"]["supplier"]["name"], "7-11")  # 切到卖家
        self.assertEqual(self.sim.docs["D1"]["doc"]["doc_date"], "2026-06-01")  # 日期未动
        self._no_forbidden(steps)

    def test_category_thai_and_zh(self):
        _run(self.sim, [("หมวดหมู่เป็น ค่าอาหาร", "MID_D1")])
        self.assertEqual(self.sim.docs["D1"]["doc"]["category_id"], "cat1")
        self.sim.docs["D1"]["doc"]["category_id"] = None
        _run(self.sim, [("分类改成餐饮", "MID_D1")])
        self.assertEqual(self.sim.docs["D1"]["doc"]["category_id"], "cat1")

    def test_payment_one_shot(self):
        _run(self.sim, [("付款方式改成 PromptPay", "MID_D1")])
        self.assertEqual(self.sim.docs["D1"]["doc"]["payment_method"], "promptpay")

    def test_amount_single_line_confirms_then_applies(self):
        steps = _run(self.sim, [("จำนวนเงินเป็น 110", "MID_D1"), ("ใช่", None)])
        self.assertEqual(self.sim.docs["D1"]["doc"]["grand_total"], "110")

    def test_amount_multiline_opens_detail_no_change(self):
        steps = _run(self.sim, [("จำนวนเงินรวมเปลี่ยนเป็น 110", "MID_D2")])
        self.assertIn("Pearnly", self._last_reply(steps))  # MULTILINE_EDIT 引导详情页
        self.assertEqual(self.sim.docs["D2"]["doc"]["grand_total"], "70.00")  # 没乱改

    def test_line_level_opens_detail(self):
        steps = _run(self.sim, [("ข้อที่ 2 เปลี่ยนเป็น 90", "MID_D2")])
        self.assertEqual(self.sim.docs["D2"]["doc"]["grand_total"], "70.00")  # 行级不乱改

    def test_split_opens_detail(self):
        steps = _run(self.sim, [("แยกเป็น 3 รายการ", "MID_D2")])
        self.assertTrue(steps[0][1])
        self.assertEqual(len(self.sim.docs["D2"]["lines"]), 3)  # 行数没被动

    def test_yes_does_not_hit_stale_pending(self):
        # 改完一笔(确认执行)后只剩 active 续接态(非待确认);再单说「ใช่」不命中旧确认动作。
        _run(self.sim, [("จำนวนเงินเป็น 110", "MID_D1"), ("ใช่", None)])
        self.assertTrue(self.sim.pending["u1"]["missing"].startswith("correctactive:"))
        steps = _run(self.sim, [("ใช่", None)])
        self.assertFalse(steps[0][1])  # active 态下「ใช่」非改错形 → 不接管(交闲聊/大脑)

    def test_cancel_aborts_pending(self):
        steps = _run(self.sim, [("จำนวนเงินเป็น 110", "MID_D1"), ("ยกเลิก", None)])
        self.assertNotIn("u1", self.sim.pending)
        self.assertEqual(self.sim.docs["D1"]["doc"]["grand_total"], "70.00")  # 未改

    def test_no_swallowed_as_yes_at_confirm(self):
        steps = _run(self.sim, [("จำนวนเงินเป็น 110", "MID_D1"), ("ไม่ใช่", None)])
        self.assertEqual(self.sim.docs["D1"]["doc"]["grand_total"], "70.00")  # 「否」未执行

    def test_delete_quoted_draft(self):
        steps = _run(self.sim, [("ลบ", "MID_D1")])
        self.assertNotIn("D1", self.sim.docs)  # 草稿被删

    def test_delete_in_session(self):
        steps = _run(self.sim, [("วันที่ผิด", "MID_D1"), ("删除", None)])
        self.assertNotIn("D1", self.sim.docs)

    def test_vague_then_field_no_forbidden(self):
        # 笼统「识别错了」→ 列字段;答「卖家」→ 问新值;给「7-11」→ 改。全程无泛化指引。
        steps = _run(self.sim, [("识别错了", "MID_D1"), ("卖家", None), ("7-11", None)])
        self.assertEqual(self.sim.docs["D1"]["supplier"]["name"], "7-11")
        self._no_forbidden(steps)

    def test_noop_posted_no_rebuild(self):
        # 验收 #3:已入账单日期已是 2026-06-18,再「วันที่เป็น 2026/6/18」→ no-op,不 void 不重建。
        self.sim.seed("D4", lines=1, status="posted", doc_date="2026-06-18")
        steps = _run(self.sim, [("วันที่เป็น 2026/6/18", "MID_D4")])
        self.assertTrue(steps[0][1])
        self.assertNotIn("D4_c1", self.sim.docs)  # 没 correct_doc 克隆重建
        self.assertEqual(self.sim.docs["D4"]["doc"]["status"], "posted")  # 原单没动

    def test_active_session_continues(self):
        # 验收 #2:改完卖家后,无引用再「วันที่เป็น 2026/6/18」→ 续命中同一张(active)。
        steps = _run(self.sim, [("ร้านค้าเป็น 7-11", "MID_D1"), ("วันที่เป็น 2026/6/18", None)])
        self.assertTrue(steps[1][1])
        self.assertEqual(self.sim.docs["D1"]["doc"]["doc_date"], "2026-06-18")
        self._no_forbidden(steps)

    def test_posted_requote_voided_original_follows_active(self):
        # 真机 bug:已入账票改卖家(void+克隆)后,再次「引用原卡」改日期 → 原卡已作废,须跟随 active
        # 续到克隆,不得回「ไม่มีรายการ…ให้แก้」(exp_correct_none)。
        none_msg = line_client.t_line("th", "exp_correct_none")
        steps = _run(
            self.sim,
            [
                ("ร้านค้าเป็น 7-11", "MID_D3"),  # 已入账 → void+克隆,active=克隆
                ("วันที่เป็น 2026/6/1", "MID_D3"),  # 再引用原卡(已作废)→ 跟随 active
                ("วันที่เป็น 2026/6/18", "MID_D3"),  # 再来一次
            ],
        )
        self.assertTrue(all(s[1] for s in steps))
        for _, _, replies in steps:
            self.assertNotIn(none_msg, replies)  # 绝不回「找不到记录」
        self.assertEqual(self.sim._active_doc_date(), "2026-06-18")  # 续接那张日期改对

    def test_posted_low_risk_chain_no_break(self):
        # 已入账单:seller -> date -> category -> payment 连续低风险字段都续命中,不断。
        none_msg = line_client.t_line("th", "exp_correct_none")
        steps = _run(
            self.sim,
            [
                ("ร้านค้าเป็น 7-11", "MID_D3"),
                ("วันที่เป็น 2026/6/18", None),
                ("หมวดหมู่เป็น ค่าอาหาร", None),
                ("วิธีชำระเป็นเงินสด", None),
            ],
        )
        self.assertTrue(all(s[1] for s in steps))
        for _, _, replies in steps:
            self.assertNotIn(none_msg, replies)

    def test_active_new_expense_not_hijacked(self):
        # active 续接态收到新记账「กาแฟ 70」→ route 放行(不接管、不劫持)。
        steps = _run(self.sim, [("ร้านค้าเป็น 7-11", "MID_D1"), ("กาแฟ 70", None)])
        self.assertFalse(steps[1][1])

    def test_chain_seller_date_seller_delete_multiline(self):
        # 串联(Zihao 指定):seller -> date -> seller(no-op) -> delete -> 另一张多行总额拦截。
        self.sim.seed("D5", lines=1)
        steps = _run(
            self.sim,
            [
                ("ร้านค้าเป็น 7-11", "MID_D5"),  # ① 改卖家(active D5)
                ("วันที่เป็น 2026/6/18", None),  # ② 续接改日期(D5)
                ("ร้านค้าเป็น 7-11", None),  # ③ 已是 7-11 → no-op,不重建
                ("ลบ", None),  # ④ 删当前 active 草稿 D5
                ("จำนวนเงินรวมเปลี่ยนเป็น 110", "MID_D2"),  # ⑤ 另一张多行 → 详情页
            ],
        )
        self.assertTrue(all(s[1] for s in steps))  # 五步全被改错路由接管
        self.assertNotIn("D5", self.sim.docs)  # ④ 真删了
        self.assertEqual(self.sim.docs["D2"]["doc"]["grand_total"], "70.00")  # ⑤ 多行没乱改
        self._no_forbidden(steps)


class SafetyGateTests(unittest.TestCase):
    """账务红线:correction-like 文本绝不进 auto_book 记账(P1E-2 真机事故复现)。"""

    def setUp(self):
        self.sim = Sim()
        self.sim.seed("D2", lines=3)  # 多行草稿(供详情页 + 续接用)
        self.reply_key = line_client.t_line("th", "line_need_reply_record")

    def test_seller_correction_no_target_never_records(self):
        # 真机事故:无 active/引用「ร้านค้าเป็น 7-11」→ 绝不新建 11 THB,只提示回复记录。
        before = set(self.sim.docs)
        steps = _run(self.sim, [("ร้านค้าเป็น 7-11", None)])
        self.assertTrue(steps[0][1])  # 被改错路由拦下(没落记账)
        self.assertEqual(set(self.sim.docs), before)  # 没新建任何单
        self.assertIn(self.reply_key, steps[0][2])  # 提示「回复要改的记录」

    def test_date_correction_no_target_never_records(self):
        before = set(self.sim.docs)
        steps = _run(self.sim, [("วันที่เป็น 2026/6/18", None)])
        self.assertTrue(steps[0][1])
        self.assertEqual(set(self.sim.docs), before)

    def test_multiline_total_no_target_never_records(self):
        before = set(self.sim.docs)
        steps = _run(self.sim, [("จำนวนเงินรวมเปลี่ยนเป็น 110", None)])
        self.assertTrue(steps[0][1])
        self.assertEqual(set(self.sim.docs), before)

    def test_correction_like_batch_never_records(self):
        # 一批 correction-like 语句(含数字)→ 全部不得落记账(route 接管 = 不进 auto_book)。
        for t in [
            "ร้านค้าเป็น 7-11",
            "วันที่เป็น 2026/6/18",
            "จำนวนเงินรวมเปลี่ยนเป็น 110",
            "หมวดหมู่เป็น ค่าอาหาร",
            "ยกเลิก",
            "ลบ",
        ]:
            sim = Sim()  # 空账本·无 active·无引用
            steps = _run(sim, [(t, None)])
            self.assertTrue(steps[0][1], f"{t} 未被拦截 → 会落记账!")
            self.assertEqual(sim.docs, {}, f"{t} 竟新建了单!")

    def test_normal_expense_still_records(self):
        # 普通记账「กาแฟ 70」非 correction → route 放行(False),交记账流。
        steps = _run(self.sim, [("กาแฟ 70", None)])
        self.assertFalse(steps[0][1])

    def test_multiline_detail_keeps_active_then_seller(self):
        # 验收 #6:多行总额→详情页后 active 仍保留,后续「ร้านค้าเป็น 7-11」继续命中同一张。
        steps = _run(
            self.sim,
            [("จำนวนเงินรวมเปลี่ยนเป็น 110", "MID_D2"), ("ร้านค้าเป็น 7-11", None)],
        )
        self.assertTrue(all(s[1] for s in steps))
        self.assertEqual(self.sim.docs["D2"]["supplier"]["name"], "7-11")  # 续命中 D2 改卖家
        self.assertEqual(len(self.sim.docs["D2"]["lines"]), 3)  # 多行明细原样保留(没乱改/没拆)

    def test_seller_value_tops_not_truncated(self):
        # 验收 #5:店名「tops」不得被拉丁连接词「to」吃成「ps」。
        steps = _run(self.sim, [("ร้านค้าเป็น tops", "MID_D2")])
        self.assertEqual(self.sim.docs["D2"]["supplier"]["name"], "tops")


def _report() -> str:
    """跑全部 scenario,产出 通过/失败 + 实际回复 报告(给人看)。"""
    load = unittest.TestLoader().loadTestsFromTestCase
    suite = unittest.TestSuite([load(ReplayScenarioTests), load(SafetyGateTests)])
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = unittest.TextTestRunner(stream=buf, verbosity=2).run(suite)
    lines = [
        "== LINE 改错回放压测报告 ==",
        f"场景 {result.testsRun} · 失败 {len(result.failures)} · 错误 {len(result.errors)}",
    ]
    for t, e in result.failures + result.errors:
        lines.append(f"  ✗ {t._testMethodName}")
    if not (result.failures or result.errors):
        lines.append("  ✓ 全部场景通过")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_report())
