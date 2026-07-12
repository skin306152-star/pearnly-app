# -*- coding: utf-8 -*-
"""F2 对数核对单测(services/accounting/shadow_gl_recon.py + reconcile R5 接线)。

覆盖:F2-主 影子科目 ↔ 上传 GL 文件——完全一致无报警 / 人为制造一科目差额→mismatch 如实列出 /
桥不全→unmapped 不强对 / 合计对平 / 无 GL 上传→no_gl_source 诚实降级;F2-辅 推送逐行成败——
全推成功无报警 / 漏推→报警 / 被拒带原因;接线把对数结果挂 gates.r5_shadow.reconcile_gl 并带
gl_source 三态(T4a:none/parse_failed/ok,解析失败绝不伪装成没上传),对数自身异常隔离不带垮
影子底稿(佐证之佐证,不阻断出包);无 GL 件存量工单 payload 除新增 gl_source 外逐字节钉死。
"""

import json
import unittest
from decimal import Decimal

from services.accounting import shadow_gl_recon as recon
from services.accounting import workorder_shadow_adapter as adapter
from services.recon.bank_recon_types import GlRow
from services.workorder.steps import reconcile


def _acc(code, name, debit, credit):
    return {"code": code, "name": name, "debit": debit, "credit": credit}


def _gl(account_code, debit, credit, doc="D1"):
    return GlRow(
        date=None, doc_no=doc, account_code=account_code, description="", debit=debit, credit=credit
    )


class ImportReportStub:
    def __init__(self, success, failed):
        self.success = success
        self.failed = failed


class FailedRowStub:
    def __init__(self, invoice_no, reasons):
        self.invoice_no = invoice_no
        self.reasons = reasons


# ── F2-主:影子 ↔ GL 对平 ─────────────────────────────────────
class GlReconEqualTests(unittest.TestCase):
    """完全一致(桥全 + 发生额对得上)→ reconciled,无报警。"""

    def test_exact_match_no_alert(self):
        accounts = [
            _acc("5290", "杂项费用", "1000.00", "0"),
            _acc("1140", "进项税", "70.00", "0"),
            _acc("2010", "应付账款", "0", "1070.00"),
        ]
        gl_rows = [_gl("530000", 1000.0, 0.0), _gl("115000", 70.0, 0.0), _gl("210000", 0.0, 1070.0)]
        bridge = {"5290": "530000", "1140": "115000", "2010": "210000"}
        r = recon.reconcile_gl(accounts, gl_rows, bridge)
        self.assertEqual(r.status, "reconciled")
        self.assertFalse(r.alert)
        self.assertEqual(len(r.matched), 3)
        self.assertEqual(r.mismatch, [])
        self.assertTrue(r.totals["balanced"])


class GlReconMismatchTests(unittest.TestCase):
    """人为制造一科目差额 → mismatch 清单如实列出该科目 + 差额值,报警。"""

    def test_manufactured_diff_flags_that_account(self):
        accounts = [
            _acc("5290", "杂项费用", "1000.00", "0"),
            _acc("2010", "应付账款", "0", "1070.00"),
        ]
        # GL 把费用发生额记成 950(差 50)——影子 1000 对 GL 950。
        gl_rows = [_gl("530000", 950.0, 0.0), _gl("210000", 0.0, 1070.0)]
        bridge = {"5290": "530000", "2010": "210000"}
        r = recon.reconcile_gl(accounts, gl_rows, bridge)
        self.assertEqual(r.status, "mismatch")
        self.assertTrue(r.alert)
        self.assertEqual(len(r.mismatch), 1)
        m = r.mismatch[0]
        self.assertEqual(m["local_code"], "5290")
        self.assertEqual(m["erp_code"], "530000")
        self.assertEqual(Decimal(m["debit_diff"]), Decimal("50.00"))

    def test_totals_diff_alone_alerts(self):
        # 逐科目都在容差内,但 GL 多一条桥没指到的科目 → 合计不平 → 报警。
        accounts = [_acc("2010", "应付账款", "0", "1070.00")]
        gl_rows = [_gl("210000", 0.0, 1070.0), _gl("999999", 0.0, 500.0)]
        r = recon.reconcile_gl(accounts, gl_rows, {"2010": "210000"})
        self.assertTrue(r.alert)
        self.assertEqual(r.status, "mismatch")
        self.assertEqual(len(r.gl_only), 1)
        self.assertEqual(r.gl_only[0]["erp_code"], "999999")


class GlReconUnmappedTests(unittest.TestCase):
    """桥不全 → unmapped 如实标,不强对不臆造。"""

    def test_unbridged_account_is_unmapped_not_forced(self):
        accounts = [
            _acc("2010", "应付账款", "0", "1070.00"),
            _acc("1130", "应收账款", "5350.00", "0"),  # 桥里没有
        ]
        gl_rows = [_gl("210000", 0.0, 1070.0)]
        r = recon.reconcile_gl(accounts, gl_rows, {"2010": "210000"})
        unmapped_codes = [u["local_code"] for u in r.unmapped]
        self.assertIn("1130", unmapped_codes)
        # 1130 没被强行对到任何 GL 科目(matched/mismatch 里都不含它)。
        touched = [row["local_code"] for row in r.matched + r.mismatch]
        self.assertNotIn("1130", touched)

    def test_no_gl_source_when_no_rows(self):
        r = recon.reconcile_gl([_acc("2010", "应付账款", "0", "1070")], [], {"2010": "210000"})
        self.assertEqual(r.status, "no_gl_source")
        self.assertFalse(r.alert)


# ── F2-辅:推送逐行成败 presence 核对 ────────────────────────────
class PushPresenceTests(unittest.TestCase):
    def test_all_pushed_no_alert(self):
        report = ImportReportStub(success=["INV-1", "INV-2"], failed=[])
        r = recon.reconcile_push(["INV-1", "INV-2"], report)
        self.assertEqual(r.status, "all_pushed")
        self.assertFalse(r.alert)
        self.assertEqual(r.pushed_ok, ["INV-1", "INV-2"])

    def test_missing_invoice_alerts(self):
        report = ImportReportStub(success=["INV-1"], failed=[])
        r = recon.reconcile_push(["INV-1", "INV-2"], report)
        self.assertEqual(r.status, "incomplete")
        self.assertTrue(r.alert)
        self.assertEqual(r.missing, ["INV-2"])

    def test_rejected_invoice_carries_reasons(self):
        report = ImportReportStub(
            success=["INV-1"], failed=[FailedRowStub("INV-2", ["ไม่พบลูกค้า"])]
        )
        r = recon.reconcile_push(["INV-1", "INV-2"], report)
        self.assertTrue(r.alert)
        self.assertEqual(r.rejected[0]["invoice_no"], "INV-2")
        self.assertEqual(r.rejected[0]["reasons"], ["ไม่พบลูกค้า"])

    def test_no_report_is_honest_downgrade(self):
        r = recon.reconcile_push(["INV-1"], None)
        self.assertEqual(r.status, "no_report")
        self.assertFalse(r.alert)


# ── 接线:reconcile R5 挂 reconcile_gl ─────────────────────────
class _FakeStore:
    def __init__(self, items, events):
        self.items = items
        self.events = events

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)


def _money_evt(item_id, net, vat, grand):
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "purchase_invoice",
            "status": "ok",
            "money": {"subtotal": net, "vat": vat, "total_amount": grand, "invoice_number": "IV"},
        },
    }


def _sales_evt():
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": "s1",
            "kind": "sales_summary",
            "status": "ok",
            "sales_read": {
                "headers": ["วันที่", "ยอดขาย", "ภาษีขาย"],
                "rows": [{"cells": ["01/05/2569", "5000.00", "350.00"], "is_summary": False}],
            },
        },
    }


def _store():
    from services.workorder.engine import StepContext

    items = [{"id": "p1", "kind": "purchase_invoice", "status": "ok", "flag_reason": None}]
    events = [_money_evt("p1", "1000.00", "70.00", "1070.00"), _sales_evt()]
    ctx = StepContext(
        cur=None, tenant_id="t-1", work_order_id="wo-1", store=_FakeStore(items, events), data={}
    )
    return ctx


class ReconWiringTests(unittest.TestCase):
    def setUp(self):
        self._prev_gate = reconcile._shadow_draft_enabled
        reconcile._shadow_draft_enabled = lambda ctx: True
        self.addCleanup(setattr, reconcile, "_shadow_draft_enabled", self._prev_gate)

    def test_default_no_source_downgrade(self):
        out = reconcile.run(_store())
        rg = out.payload["gates"]["r5_shadow"]["reconcile_gl"]
        self.assertEqual(rg["status"], "no_gl_source")
        self.assertEqual(rg["gl_source"], reconcile.GL_SOURCE_NONE)
        self.assertNotIn("gl_source_note", rg)
        self.assertEqual(rg["push"]["status"], "no_report")

    def test_no_gl_payload_frozen_except_gl_source(self):
        # 回归钉死(闸已 rollout=all):无 GL 件存量工单的 reconcile_gl payload 与 T4a 改前
        # 逐字节一致,唯一新增 gl_source=none(改前快照 2026-07-13 捕获)。
        out = reconcile.run(_store())
        rg = dict(out.payload["gates"]["r5_shadow"]["reconcile_gl"])
        self.assertEqual(rg.pop("gl_source"), "none")
        frozen = {
            "alert": False,
            "gl_only": [],
            "matched": [],
            "mismatch": [],
            "push": {
                "alert": False,
                "expected_count": 0,
                "missing": [],
                "pushed_ok": [],
                "rejected": [],
                "status": "no_report",
            },
            "status": "no_gl_source",
            "totals": {},
            "unmapped": [],
        }
        self.assertEqual(json.dumps(rg, sort_keys=True), json.dumps(frozen, sort_keys=True))

    def test_injected_gl_and_push_flow_through(self):
        self._inject(
            gl_src={"rows": [_gl("530000", 1000.0, 0.0)], "source": "ok", "note": None},
            bridge={"5290": "530000"},
            push=(["INV-1"], ImportReportStub(success=["INV-1"], failed=[])),
        )
        out = reconcile.run(_store())
        rg = out.payload["gates"]["r5_shadow"]["reconcile_gl"]
        # 费用 5290 桥到 530000,发生额 1000 逐科目对上(无 mismatch),其余科目 unmapped 如实标。
        # GL 文件只含这一科目 → 合计不平,alert 如实为 True(不虚构对平),push 侧全推成功。
        self.assertEqual(rg["gl_source"], reconcile.GL_SOURCE_OK)
        self.assertEqual(rg["mismatch"], [])
        self.assertIn("5290", [m["local_code"] for m in rg["matched"]])
        self.assertTrue(any(u["local_code"] == "2010" for u in rg["unmapped"]))
        self.assertEqual(rg["push"]["status"], "all_pushed")

    def test_parse_failed_never_masquerades_as_no_source(self):
        # 有件但解析失败:rows 空 → reconcile_gl 契约仍报 no_gl_source(签名/逻辑一行不改),
        # 但 gl_source=parse_failed + note 把「读不出」与「没上传」分开,绝不伪装。
        self._inject(
            gl_src={
                "rows": [],
                "source": "parse_failed",
                "note": "gl_may.pdf: no_text_layer",
            },
            bridge={},
            push=([], None),
        )
        out = reconcile.run(_store())
        rg = out.payload["gates"]["r5_shadow"]["reconcile_gl"]
        self.assertEqual(rg["status"], "no_gl_source")
        self.assertEqual(rg["gl_source"], reconcile.GL_SOURCE_PARSE_FAILED)
        self.assertEqual(rg["gl_source_note"], "gl_may.pdf: no_text_layer")

    def test_recon_exception_isolated_keeps_shadow(self):
        def _boom(ctx):
            raise RuntimeError("bridge blew up")

        # 桥仅在有 GL 行时才建(省 DB 空跑),故先注入非空 gl_rows 让异常路径可达。
        self._prev_rows = reconcile._shadow_gl_rows
        reconcile._shadow_gl_rows = lambda ctx: {"rows": [object()], "source": "ok", "note": None}
        self.addCleanup(setattr, reconcile, "_shadow_gl_rows", self._prev_rows)
        self._prev_bridge = reconcile._shadow_account_bridge
        reconcile._shadow_account_bridge = _boom
        self.addCleanup(setattr, reconcile, "_shadow_account_bridge", self._prev_bridge)
        out = reconcile.run(_store())
        shadow = out.payload["gates"]["r5_shadow"]
        # 对数炸了但影子底稿三件套还在,step 仍 ok(佐证之佐证,不阻断)。
        self.assertEqual(out.status, "ok")
        self.assertIn("trial_balance", shadow)
        self.assertEqual(shadow["reconcile_gl"]["status"], "reconcile_gl_skipped")

    def _inject(self, *, gl_src, bridge, push):
        prev_rows = reconcile._shadow_gl_rows
        prev_bridge = reconcile._shadow_account_bridge
        prev_push = reconcile._shadow_push_report
        reconcile._shadow_gl_rows = lambda ctx: gl_src
        reconcile._shadow_account_bridge = lambda ctx: bridge
        reconcile._shadow_push_report = lambda ctx: push
        self.addCleanup(setattr, reconcile, "_shadow_gl_rows", prev_rows)
        self.addCleanup(setattr, reconcile, "_shadow_account_bridge", prev_bridge)
        self.addCleanup(setattr, reconcile, "_shadow_push_report", prev_push)


# ── 断言 1:真月份 Σ借=Σ贷(F1 影子在真数金标上成立,F2 对数建立其上)──
class ShadowTrialBalanceGoldenTests(unittest.TestCase):
    def test_golden_month_debit_equals_credit(self):
        # L2 金标销项税 60114.61(不动)。影子试算平衡 Σ借=Σ贷,diff≤0.01。
        r = adapter.build_shadow(
            purchase_entries=[
                {
                    "net": Decimal("58128.57"),
                    "vat": Decimal("4069.05"),
                    "grand": Decimal("62197.62"),
                }
            ],
            sales_amount=Decimal("858780.16"),
            output_vat=Decimal("60114.61"),
        )
        tb = r.trial_balance
        self.assertTrue(tb["balanced"])
        self.assertEqual(Decimal(tb["debit"]), Decimal(tb["credit"]))
        self.assertLessEqual(Decimal(tb["diff"]), Decimal("0.01"))


if __name__ == "__main__":
    unittest.main()
