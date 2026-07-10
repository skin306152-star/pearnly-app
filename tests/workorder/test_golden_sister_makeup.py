# -*- coding: utf-8 -*-
"""工单制 L2 真金标测试(真客户 Sister Makeup 2569-05 · M0 任务包 §6)。

不进 CI:skipUnless(PEARNLY_LOCAL_CORPUS)。真语料不进 git,金标数字锁在
`桌面\\pearnly ai\\施工\\T0-语料盘点.md`(策划窗亲读官方 ภ.พ.30 原件锁定)。本文件只跑真
OCR 一次(classify 是唯一付费步):face_value/recalc 两条人工裁决路径复用同一批已分类
结果,靠 reconcile.run() 单步重跑 + 追加第二条 human_decision 事件(同 item 后者胜)
验证,不二次过 OCR。test_07(断点续跑)独立工单会再烧一次全量 OCR,另设
PEARNLY_L2_RESUME=1 才跑,默认 skip 防双倍烧钱。

语料形态决定的三个必经人工阶段(与 G1R2 产品路径同口径,均走真产品口 api.py):
  1. 批量方向裁决:本语料销项证据全是实物翻拍(Ocha 小票/EDC 结算/银行流水打印件),
     classify 会落一批 kind=unknown 方向票,守恒闸不裁决不放行 → 按答案键逐张
     assign_kind(见 _direction_kind)。
  2. 采信标黄票:NBC 系票 OCR 读出的明细/折扣字段不自洽会触勾稽闸标黄,会计核对原件
     后按票面采信(G1R2 现场「审 5 张裁决 = 4 采信 + 2647 改数」的前一半)。
  3. W4 人工填销项:无数字销项源(客户无 POS 导出),R2 永远 needs(sales_summary) →
     调 api.record_sales_summary 按官方申报数注入(来源=manual_entry,状态诚实标注)。

本地跑法(策划窗):
    set PEARNLY_LOCAL_CORPUS=1
    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://...(真库,workspace_clients 需已有该客户账套记录,
    且该行 tenant_id 必须 = 本文件 TENANT_ID——2026-07-10 首跑 5 败根因即两者不匹配
    导致方向锚取空、104 张全 direction_ambiguous)
    set OCR_LLM_BACKEND=vertex(本地 aistudio 慢到不可用)
    set GEMINI 等密钥按 ocr-local-eval-recipe 配方就位(本文件不读密钥文件,交生产
    OCR 入口自己解析)
    python -m unittest tests.workorder.test_golden_sister_makeup -v

预期首跑(test_01)停在 reconcile,点名两类待裁:IMG_2647 flagged(amount_math_fail)
无人工裁决 + 方向票「未人工裁定」。
"""

from __future__ import annotations

import os
import unittest
from decimal import Decimal
from pathlib import Path

from services.workorder import decisions
from tests.integration._helpers import require_db

CORPUS_ROOT = Path(r"C:\Users\skin3\Desktop\5月")
INTAKE_DIR = CORPUS_ROOT / "A_客户给的原料"
OUT_DIR = CORPUS_ROOT / "_workorder_out"

# 金标常量(T0 语料盘点 · 官方聚合 5 数锁定不许改,真跑对不上是代码的问题不是常量的问题)
GOLDEN_SALES_AMOUNT = Decimal("858780.16")
GOLDEN_OUTPUT_VAT = Decimal("60114.61")
GOLDEN_PURCHASE_AMOUNT = Decimal("418046.86")
GOLDEN_INPUT_VAT = Decimal("29263.28")  # 人工按票面路径(与已申报一致)
GOLDEN_INPUT_VAT_RECALC = Decimal("29254.28")  # 采信 OCR 读值路径(25194.23 + 淡票 OCR 4060.05)
GOLDEN_TAX_DUE = Decimal("30851.33")
# 10 张无争议票票面层真值 = 官方 29263.28 − IMG_2647 印刷面 4069.05。旧值 25194.28/4069.00
# 是 T0 取整反推的错误拆分(T7 当时全绿系两处 ±0.05 OCR 误读互抵);原件行项算术实锤:
# 25,916.00+25,916.00+10,366.40=折后含税 62,198.40,VAT=62,198.40×7/107=4,069.05。
GOLDEN_UNDISPUTED_INPUT_VAT = Decimal("25194.23")
# IMG_2647 折扣淡票印刷税额(汇总区印刷淡,"9"糊成"0"→真机 OCR 读 4060.05;人工按行项
# 算术补正到印刷真值)。真工单 6a4bfbdd(client 94)现场裁决即 recalc vat=4069.05。
DISPUTED_FACE_VAT_CORRECTED = "4069.05"
DISPUTED_TICKET_MARK = "IMG_2647"
# 11 张进项票=IMG_2640~2650(金标锚定,test_03 docstring 同口径)。别名上场
# (B2-c:客户配 "Sister Makeup" 英文商号)+ OCR 读取方差,任一张都可能因
# 双锚冲突(闸5 不猜)或锚缺失落进方向队列等人裁——答案键照 W3 人工看票面:
# 这个文件段的方向票一律裁进项,其余裁销项。金标数字不动。
PURCHASE_DIRECTION_MARKS = tuple(f"IMG_{n}" for n in range(2640, 2651))

TENANT_ID = "22222222-2222-2222-2222-222222222222"  # 本地测试租户,策划窗按真账套改
CLIENT_TAX_ID = "0105567178203"  # บริษัท ซิสเตอร์ เมคอัพ จำกัด
PERIOD = "2569-05"


def _direction_kind(item: dict) -> str | None:
    """答案键:一件 item 若是待裁方向票,给出该裁的 kind;否则 None(不碰)。

    B/C 堆全是照片,静态核不出 11 张进项票的完整文件名清单,采用稳健式:方向票默认裁
    sales_doc(语料方向票实测全是 Ocha 销售小票/EDC 结算/银行翻拍,G1R2 现场 70 张方向票
    裁决与此一致:66 销项 + 4 非税,进项 0 张漏进方向票在锚生效前);IMG_2647 特判裁
    purchase_invoice 仅防御(锚生效后它该走 amount_math_fail 非方向票)。裁错兜底:金标
    数字断言(29263.28/418046.86)+ R1 计数断言(=11)必红,不会静默。"""
    if item.get("status") != "flagged":
        return None
    if not str(item.get("flag_reason") or "").startswith(decisions.DIRECTION_PREFIXES):
        return None
    ref = item.get("file_ref") or ""
    if any(m in ref for m in PURCHASE_DIRECTION_MARKS):
        return "purchase_invoice"
    return "sales_doc"


class DirectionAnswerKeyTests(unittest.TestCase):
    """答案键纯逻辑守门(不碰库不碰 OCR,任何环境可跑)。"""

    def test_direction_ticket_defaults_to_sales(self):
        it = {
            "status": "flagged",
            "flag_reason": "sales_direction_unhandled",
            "file_ref": "/in/IMG_2600.JPG",
        }
        self.assertEqual(_direction_kind(it), "sales_doc")

    def test_disputed_ticket_defensively_assigned_purchase(self):
        it = {
            "status": "flagged",
            "flag_reason": "direction_ambiguous",
            "file_ref": "/in/IMG_2647.JPG",
        }
        self.assertEqual(_direction_kind(it), "purchase_invoice")

    def test_non_direction_items_untouched(self):
        flagged_math = {
            "status": "flagged",
            "flag_reason": "amount_math_fail",
            "file_ref": "/in/IMG_2647.JPG",
        }
        ok_purchase = {"status": "ok", "flag_reason": None, "file_ref": "/in/IMG_2640.JPG"}
        self.assertIsNone(_direction_kind(flagged_math))
        self.assertIsNone(_direction_kind(ok_purchase))


@unittest.skipUnless(
    os.environ.get("PEARNLY_LOCAL_CORPUS"), "requires-local-corpus(见文件头运行说明)"
)
class GoldenSisterMakeupTests(unittest.TestCase):
    """七条断言对应任务包 §6,不许放水。测试方法按编号顺序执行(unittest 默认按名字母
    序跑同一 TestCase 的方法),同一工单 test_01 完成的 classify 结果被后续测试复用。"""

    work_order_id = None

    @classmethod
    def setUpClass(cls):
        require_db()
        if not INTAKE_DIR.is_dir():
            raise unittest.SkipTest(f"语料目录不存在:{INTAKE_DIR}")

        from core import db
        from services.workorder import engine, store
        from services.workorder.steps import real_handlers

        cls.db, cls.store, cls.engine = db, store, engine
        # 函数直接存类属性会走描述符协议绑成方法(self 误作首参 TypeError),staticmethod
        # 保住「self.real_handlers() 取到的就是原函数」。
        cls.real_handlers = staticmethod(real_handlers)
        OUT_DIR.mkdir(exist_ok=True)

    def _client_id(self, cur) -> int:
        cur.execute("SELECT id FROM workspace_clients WHERE tax_id = %s", (CLIENT_TAX_ID,))
        row = cur.fetchone()
        if not row:
            raise unittest.SkipTest(f"workspace_clients 无税号 {CLIENT_TAX_ID} 的账套,先建/核对")
        return row["id"]

    def _items(self, cur):
        return self.store.list_items(
            cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
        )

    def _events(self, cur):
        return self.store.list_events(
            cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
        )

    def _assign_direction_tickets(self, cur, work_order_id) -> int:
        """批量方向裁决:按答案键(_direction_kind)对每张待裁方向票走真产品口
        api.record_decision(与 W3 UI 同 payload:{item_id, decision:"assign_kind", kind}),
        不手拼事件。返回裁决张数。"""
        from services.workorder import api

        count = 0
        items = self.store.list_items(cur, tenant_id=TENANT_ID, work_order_id=work_order_id)
        for it in items:
            kind = _direction_kind(it)
            if kind is None:
                continue
            api.record_decision(
                cur,
                tenant_id=TENANT_ID,
                work_order_id=work_order_id,
                item_id=it["id"],
                decision="assign_kind",
                values=None,
                kind=kind,
                actor="user:cli",
            )
            count += 1
        return count

    def _fill_manual_sales(self, cur, work_order_id) -> None:
        """W4 人工填销项(真产品口 record_sales_summary,落与直读同构的 item_classified
        事件解锁 R2)。语料无数字销项源(全实物翻拍),按官方申报数注入——与 G1R2 现场
        操作同口径,note 留金标注入痕迹。"""
        from services.workorder import api

        api.record_sales_summary(
            cur,
            tenant_id=TENANT_ID,
            work_order_id=work_order_id,
            sales_amount=str(GOLDEN_SALES_AMOUNT),
            output_vat=str(GOLDEN_OUTPUT_VAT),
            note="金标注入:官方 ภ.พ.30 销项(银行流水+EDC结算+Ocha小票倒推·L2 测试)",
            actor="user:cli",
        )

    def _accept_flagged_purchases(self, cur, work_order_id) -> int:
        """按票面采信非 IMG_2647 的 math-fail 进项票(真产品口 api.record_decision
        face_value)。镜像 G1R2 现场的「4 采信」:这批 NBC 系票会计核对过原件,票面金额
        正确,是 OCR 读出的别的字段(明细行/折扣)不自洽触勾稽闸——闸标黄要人看,人看完
        采信票面,与静默吞掉是两回事。返回采信张数(OCR 非确定性下张数可浮动,金标数字
        断言兜底,不写死)。"""
        from services.workorder import api

        count = 0
        items = self.store.list_items(cur, tenant_id=TENANT_ID, work_order_id=work_order_id)
        for it in items:
            if it["kind"] != "purchase_invoice" or it["status"] != "flagged":
                continue
            if DISPUTED_TICKET_MARK in (it["file_ref"] or ""):
                continue
            api.record_decision(
                cur,
                tenant_id=TENANT_ID,
                work_order_id=work_order_id,
                item_id=it["id"],
                decision="face_value",
                values=None,
                actor="user:cli",
            )
            count += 1
        return count

    def test_01_first_run_stops_at_reconcile_on_disputed_ticket(self):
        """跑到 reconcile:IMG_2647 折扣淡票必须 flagged 停下,静默吃掉即测试失败。"""
        files = sorted(str(p) for p in INTAKE_DIR.iterdir() if p.is_file())
        with self.db.get_cursor(commit=True) as cur:
            wo = self.store.open_work_order(
                cur, tenant_id=TENANT_ID, workspace_client_id=self._client_id(cur), period=PERIOD
            )
            type(self).work_order_id = wo["id"]
            ctx = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=wo["id"],
                data={"intake_files": files, "deliverables_dir": str(OUT_DIR)},
            )
            out = self.engine.run_work_order(ctx, handlers=self.real_handlers())

        self.assertEqual(out.stopped_at, "reconcile")
        self.assertTrue(any("无人工裁决" in r for r in out.result.reasons))
        # 守恒语义:方向票(Ocha 小票/EDC/银行翻拍等 kind=unknown)必须被逐张点名待裁,
        # 不许静默漏出 R1(G1/G1R2 黑洞的回归断言)。
        self.assertGreaterEqual(sum(1 for r in out.result.reasons if "未人工裁定" in r), 1)

    def test_02_disputed_ticket_flagged_amount_math_fail(self):
        with self.db.get_cursor() as cur:
            target = next(
                it for it in self._items(cur) if DISPUTED_TICKET_MARK in (it["file_ref"] or "")
            )
        self.assertEqual(target["status"], "flagged")
        self.assertEqual(target["flag_reason"], "amount_math_fail")

    def test_03_undisputed_tickets_face_vat_sums_exactly(self):
        """非争议 10 张进项票的 OCR 票面 vat 合计精确重现票面层金标——不分 ok/flagged。

        「无争议」是金标口径(票面金额对、无需改数),不是闸口径:勾稽闸更严后部分无争议
        票会被标黄再由人采信(ok 张数是闸松紧的函数,不是金标,不断言具体值)。断言:
        进项票恰 11 张(锚定 IMG_2640~2650),其中非 IMG_2647 的 10 张票面 vat 合计
        = 25194.23。"""
        from services.workorder import evidence

        with self.db.get_cursor() as cur:
            items = self._items(cur)
            events = self._events(cur)
        classified = evidence.replay_items_by_type(events, "item_classified")
        # 按文件锚计数(IMG_2640~2650=金标锚定的 11 张进项票),不看 items.kind:
        # 别名上场 + OCR 读取方差下,任一张可能停在方向队列等人裁(闸5 不猜是设计),
        # 裁决是事件溯源不改 items.kind——票面层金标只关心「这 11 张的 OCR 钱字段」,
        # 与它此刻停在哪个队列无关。方向裁决后的税额金标由 test_04/05 事件重放兜底。
        purchases = [
            it for it in items if any(m in (it["file_ref"] or "") for m in PURCHASE_DIRECTION_MARKS)
        ]
        undisputed = [it for it in purchases if DISPUTED_TICKET_MARK not in (it["file_ref"] or "")]
        total = sum(
            (Decimal(str((classified[it["id"]]["payload"]["money"] or {}).get("vat") or "0")))
            for it in undisputed
        )
        self.assertEqual(len(purchases), 11)
        self.assertEqual(len(undisputed), 10)
        self.assertEqual(total, GOLDEN_UNDISPUTED_INPUT_VAT)

    def test_04_face_value_then_recalc_decision_paths(self):
        """人工四阶段(方向裁决 → 采信标黄票 → W4 填销项 → IMG_2647 补正)后完整走完,
        官方全字段对齐;再追加「采信 OCR 读值」裁决(同 item 后者胜)单步重跑 reconcile
        验证折后终值——不二次过 OCR。镜像 G1R2 真机「审 5 张裁决 = 4 采信 + 2647 改数」。

        补正走 recalc(而非 face_value):face_value 采信 OCR 读的 4060.05 达不到官方 line7;
        且本步顺带验采购税基根治——补正后可抵扣基按修正税额反推(base=vat/7%),整单税基
        精确重现官方 418046.86(修前沿用 OCR 旧净会短 80.89)。"""
        from services.workorder import evidence
        from services.workorder.steps import pp30_form, reconcile

        with self.db.get_cursor(commit=True) as cur:
            wo_id = type(self).work_order_id
            # 阶段 1:批量方向裁决(语料必有方向票——Ocha 小票/EDC/银行翻拍,0 张=形态不对)。
            assigned = self._assign_direction_tickets(cur, wo_id)
            self.assertGreaterEqual(assigned, 1)
            # 阶段 2:按票面采信非 2647 的标黄票(G1R2 现场实测 4 张,张数不写死)。
            self.assertGreaterEqual(self._accept_flagged_purchases(cur, wo_id), 1)
            # 阶段 3:W4 人工填销项(无数字销项源,R2 needs 的产品解法)。
            self._fill_manual_sales(cur, wo_id)
            # 阶段 4:IMG_2647 按印刷面补正。
            disputed = next(
                it for it in self._items(cur) if DISPUTED_TICKET_MARK in (it["file_ref"] or "")
            )
            self.store.append_event(
                cur,
                tenant_id=TENANT_ID,
                work_order_id=type(self).work_order_id,
                step="reconcile",
                event_type="human_decision",
                actor="user:cli",
                payload={
                    "item_id": disputed["id"],
                    "decision": "recalc",
                    "values": {"vat": DISPUTED_FACE_VAT_CORRECTED},
                },
            )
            ctx = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=type(self).work_order_id,
                data={"deliverables_dir": str(OUT_DIR)},
            )
            out = self.engine.run_work_order(ctx, handlers=self.real_handlers())
            self.assertTrue(out.completed, f"人工四阶段后应完整走完:{out.status}")

            # R1 恰好计入 11 张进项(10 auto-ok + IMG_2647 裁决保留)——方向票裁销项后
            # 一张不多(销项/银行没混进来)、一张不少(进项没漏)。
            reconcile_done = evidence.replay_step_done(self._events(cur), "reconcile") or {}
            self.assertEqual(reconcile_done["gates"]["r1_input_vat"]["counted"], 11)

            pp30 = next(
                d
                for d in self.store.list_deliverables(
                    cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
                )
                if d["kind"] == "pp30_draft"
            )
            self.assertEqual(Decimal(pp30["numbers"]["input_vat"]), GOLDEN_INPUT_VAT)
            self.assertEqual(Decimal(pp30["numbers"]["sales_amount"]), GOLDEN_SALES_AMOUNT)
            self.assertEqual(Decimal(pp30["numbers"]["output_vat"]), GOLDEN_OUTPUT_VAT)
            self.assertEqual(Decimal(pp30["numbers"]["purchase_amount"]), GOLDEN_PURCHASE_AMOUNT)
            self.assertEqual(Decimal(pp30["numbers"]["tax_due"]), GOLDEN_TAX_DUE)

            # 全字段 ภ.พ.30 契约逐字段 = 官方申报数(锁定不许放宽)。
            amounts = pp30_form.amounts(pp30["numbers"]["pp30_form"])
            self.assertEqual(Decimal(amounts["sales_total"]), GOLDEN_SALES_AMOUNT)
            self.assertEqual(Decimal(amounts["sales_taxable"]), GOLDEN_SALES_AMOUNT)
            self.assertEqual(Decimal(amounts["output_vat"]), GOLDEN_OUTPUT_VAT)
            self.assertEqual(Decimal(amounts["purchase_creditable"]), GOLDEN_PURCHASE_AMOUNT)
            self.assertEqual(Decimal(amounts["input_vat"]), GOLDEN_INPUT_VAT)
            self.assertEqual(Decimal(amounts["tax_payable"]), GOLDEN_TAX_DUE)
            self.assertEqual(Decimal(amounts["net_tax_due"]), GOLDEN_TAX_DUE)
            self.assertEqual(Decimal(amounts["total_payable"]), GOLDEN_TAX_DUE)
            # 本期无独立数据源的字段诚实置 0,不编造。
            for zero_key in (
                "sales_zero_rated",
                "sales_exempt",
                "prior_credit",
                "surcharge",
                "penalty",
                "tax_overpaid",
            ):
                self.assertEqual(Decimal(amounts[zero_key]), Decimal("0"), zero_key)

            # 追加「采信 OCR 读值」裁决(同一票),reconcile 回放取最新一条 → 单步重跑验证折后终值。
            self.store.append_event(
                cur,
                tenant_id=TENANT_ID,
                work_order_id=type(self).work_order_id,
                step="reconcile",
                event_type="human_decision",
                actor="user:cli",
                payload={"item_id": disputed["id"], "decision": "face_value", "values": {}},
            )
            recalced = reconcile.run(ctx)
            self.assertEqual(Decimal(recalced.payload["input_vat_total"]), GOLDEN_INPUT_VAT_RECALC)

    def test_05_tax_due_diff_only_explained_by_disputed_ticket(self):
        """应缴(按票面裁决路径)与官方一致,且这是唯一差异来源——用 03 的无争议合计
        佐证:金标 = 无争议合计 + IMG_2647 票面 VAT(印刷面 4069.05),差额可枚举解释。"""
        disputed_face_vat = GOLDEN_INPUT_VAT - GOLDEN_UNDISPUTED_INPUT_VAT
        self.assertEqual(disputed_face_vat, Decimal(DISPUTED_FACE_VAT_CORRECTED))
        self.assertEqual(GOLDEN_OUTPUT_VAT - GOLDEN_INPUT_VAT, GOLDEN_TAX_DUE)

    def test_06_idempotent_rerun_keeps_events_and_deliverables_stable(self):
        with self.db.get_cursor(commit=True) as cur:
            events_before = len(self._events(cur))
            deliverables_before = self.store.list_deliverables(
                cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
            )
            ctx = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=type(self).work_order_id,
                data={"deliverables_dir": str(OUT_DIR)},
            )
            out = self.engine.run_work_order(ctx, handlers=self.real_handlers())
            events_after = len(self._events(cur))
            deliverables_after = self.store.list_deliverables(
                cur, tenant_id=TENANT_ID, work_order_id=type(self).work_order_id
            )

        self.assertTrue(out.completed)
        self.assertEqual(events_before, events_after)
        self.assertEqual(len(deliverables_before), len(deliverables_after))

    @unittest.skipUnless(
        os.environ.get("PEARNLY_L2_RESUME"),
        "PEARNLY_L2_RESUME=1 才跑:独立工单再烧一次全量真 OCR(约 43 分钟+付费),"
        "默认跳过防金标角复跑双倍烧钱",
    )
    def test_07_resume_after_kill_mid_classify_matches_uninterrupted_run(self):
        """断点续跑:人为在 classify 后、reconcile 真正跑之前切断(模拟进程被杀),续跑
        重建的数字须与常规流程(test_01→04)完全一致。开独立 intent 的工单,避免复用
        已完成工单;续跑侧同样要过人工三阶段(方向裁决/填销项/补正)才可能 completed。"""
        from services.workorder.engine import StepResult

        files = sorted(str(p) for p in INTAKE_DIR.iterdir() if p.is_file())
        paused = {"once": False}
        handlers = dict(self.real_handlers())
        real_reconcile = handlers["reconcile"]

        def _pause_once_then_real(ctx):
            if not paused["once"]:
                paused["once"] = True
                return StepResult.needs(["manual_pause_after_classify"])
            return real_reconcile(ctx)

        handlers["reconcile"] = _pause_once_then_real

        with self.db.get_cursor(commit=True) as cur:
            wo = self.store.open_work_order(
                cur,
                tenant_id=TENANT_ID,
                workspace_client_id=self._client_id(cur),
                period=PERIOD,
                intent="monthly_vat_resume_check",
            )
            ctx = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=wo["id"],
                data={"intake_files": files, "deliverables_dir": str(OUT_DIR / "resume_check")},
            )
            out1 = self.engine.run_work_order(ctx, handlers=handlers)
            self.assertEqual(out1.stopped_at, "reconcile")
            self.assertEqual(out1.result.missing, ("manual_pause_after_classify",))

            # 续跑前的人工四阶段(与 test_04 同口径:方向裁决 → 采信标黄票 → 填销项 → 补正)。
            self.assertGreaterEqual(self._assign_direction_tickets(cur, wo["id"]), 1)
            self.assertGreaterEqual(self._accept_flagged_purchases(cur, wo["id"]), 1)
            self._fill_manual_sales(cur, wo["id"])
            disputed = next(
                it
                for it in self.store.list_items(cur, tenant_id=TENANT_ID, work_order_id=wo["id"])
                if DISPUTED_TICKET_MARK in (it["file_ref"] or "")
            )
            self.store.append_event(
                cur,
                tenant_id=TENANT_ID,
                work_order_id=wo["id"],
                step="reconcile",
                event_type="human_decision",
                actor="user:cli",
                payload={
                    "item_id": disputed["id"],
                    "decision": "recalc",
                    "values": {"vat": DISPUTED_FACE_VAT_CORRECTED},
                },
            )
            ctx2 = self.engine.StepContext(
                cur=cur,
                tenant_id=TENANT_ID,
                work_order_id=wo["id"],
                data={"deliverables_dir": str(OUT_DIR / "resume_check")},
            )
            out2 = self.engine.run_work_order(ctx2, handlers=handlers)

            pp30 = next(
                d
                for d in self.store.list_deliverables(
                    cur, tenant_id=TENANT_ID, work_order_id=wo["id"]
                )
                if d["kind"] == "pp30_draft"
            )

        self.assertTrue(out2.completed)
        self.assertEqual(Decimal(pp30["numbers"]["input_vat"]), GOLDEN_INPUT_VAT)


if __name__ == "__main__":
    unittest.main()
