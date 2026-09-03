#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/unit/test_inventory_scan_behavior.py

入库弹窗扫码的【真行为】守门 —— 产品自己在 node 里跑一遍,断言看的是跑完之后的状态,
不是源码里有没有那一行。

为什么另起这一份(2026-07-31 审查实锤):同一批的接缝断言原本是 16 条字符串断言。审查方
把 `unmountInvScan()` 的函数体整个包进 `if (false)` —— 字面一个字没删 —— 单测照样
`Ran 16 ... OK`。而那一改在真机上就是:关了收货弹窗,相机灯还亮着、条码枪还在往一张已经
不存在的弹窗上送码,全站扫码从此进不来。字符串在,行为没了,闸一声不吭。

所以这里每一条都落在「跑完之后能读出来的量」上,且优先选**只有走目标路径才会变**的那个量:
关弹窗验的不是「相机关了」(stopCamera 也会关,两条路都变),而是
`PearnlyScanWedge.subscriberCount() === 0` —— 只有 unmountInvScan 会动它。

harness 见 `_inventory_scan_dom.py`:弹窗 DOM 由 inventory-modals.ts 现渲染、楔子是
static/scan/scan-wedge.js 真件、inventory-common.ts 真件;只有后端(salesFetch)与摄像头
引擎(要 getUserMedia)是桩。
"""

from __future__ import annotations

import shutil
import unittest

from tests.unit._inventory_scan_dom import scenario

# 货架/查码应答与 scenario() 在 _inventory_scan_dom.py(两份用例文件共用一份,见那边 FIXTURE)。
# 「摄像头把第二箱挡下」与「提交前的数量兜底」两组在 test_inventory_scan_guards.py。


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过真 DOM 行为测试")
class ScanMountLifecycle(unittest.TestCase):
    """开窗挂上、关窗真放开 —— 这一组就是「函数体被架空」照得出来的那一组。"""

    def test_closing_the_modal_unsubscribes_the_gun_and_frees_the_camera(self):
        got = scenario("""
(async () => {
    openIn();
    const mounted = wedgeSubs();
    document.getElementById('inv-in-mask-scan-cam').onclick();
    await tick();
    const camOpen = camLog.created;
    closeIn();
    out({ mounted, camOpen, subsAfter: wedgeSubs(), destroyed: camLog.destroyed,
          maskOpen: document.getElementById('inv-in-mask').classList.contains('show') });
})();
""")
        self.assertEqual(1, got["mounted"], "开收货弹窗没把楔子挂上 —— 枪扫进来没人接")
        self.assertEqual(1, got["camOpen"], "点摄像头按钮没把引擎开起来")
        # 判别量:subscriberCount 只有走 unmountInvScan 才会归零(stopCamera 不动它)
        self.assertEqual(0, got["subsAfter"], "关窗没退订楔子 —— 枪还在往已经没了的弹窗送码")
        self.assertGreaterEqual(got["destroyed"], 1, "关窗没放相机 —— 相机灯一直亮着")
        self.assertFalse(got["maskOpen"])

    def test_reopening_does_not_leak_a_second_subscriber(self):
        """连开两次收货弹窗:楔子只能有一个订阅者,漏一个就是同一个码被处理两遍。"""
        got = scenario("""
openIn(); const first = wedgeSubs();
openIn(); const second = wedgeSubs();
closeIn();
out({ first, second, after: wedgeSubs() });
""")
        self.assertEqual([1, 1, 0], [got["first"], got["second"], got["after"]])

    def test_count_modal_does_not_arm_the_gun(self):
        """盘点是「数现有的」,扫码加行没意义 —— 它不该挂楔子,也不该有扫码条。"""
        got = scenario("""
document.body.innerHTML = '<div id="inv-count-mask"></div>';
window.openInventoryCount();
out({ subs: wedgeSubs(), bar: !!document.getElementById('inv-count-mask-scan-code') });
""")
        self.assertEqual(0, got["subs"], "盘点弹窗把楔子挂上了")
        self.assertFalse(got["bar"], "盘点弹窗渲染了扫码条")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过真 DOM 行为测试")
class ScanLandsOnARow(unittest.TestCase):
    """码 → 行:落在哪一行、数量怎么加、单位与批次格跟不跟上。"""

    def test_lookup_hits_the_real_endpoint_with_the_scanned_code(self):
        got = scenario("(async () => { openIn(); await feed(COLA); out({ lookups }); })();")
        self.assertEqual(
            ["/api/sales/products/lookup?barcode=8850999320014"],
            got["lookups"],
            "查码没走 routes/products_routes.py 的 /lookup(按 barcode 精确查)",
        )

    def test_same_code_twice_bumps_one_row_instead_of_adding_two(self):
        got = scenario("""
(async () => { openIn(); await feed(COLA); const one = snapshot(); await feed(COLA);
               out({ one, two: snapshot() }); })();
""")
        self.assertEqual("p-cola", got["one"][0]["product"])
        self.assertEqual("1", got["one"][0]["qty"])
        self.assertEqual("2", got["two"][0]["qty"], "同一个码再扫一次没累加")
        self.assertEqual(
            [r["product"] for r in got["two"]],
            ["p-cola", ""],
            "一箱一箱扫同一件货加出了第二行",
        )

    def test_batch_item_gets_its_own_row_and_the_batch_cell_shows(self):
        """两箱牛奶批号/效期不同:合成一行 = 第二箱的效期被换成第一箱的,FEFO 从此按错日期算。"""
        got = scenario("""
(async () => { openIn(); await feed(MILK); await feed(MILK); out({ rows: snapshot() }); })();
""")
        milk = [r for r in got["rows"] if r["product"] == "p-milk"]
        self.assertEqual(2, len(milk), "批次品第二箱被并进了第一箱那一行")
        for row in milk:
            self.assertEqual("1", row["qty"])
            self.assertTrue(row["batchShown"], "批次格没露出来 —— 这箱的批号无处可写")

    def test_non_batch_row_keeps_the_batch_cell_hidden(self):
        got = scenario(
            "(async () => { openIn(); await feed(COLA); out({ rows: snapshot() }); })();"
        )
        self.assertFalse(got["rows"][0]["batchShown"], "非批次品露出了批号/效期格")

    def test_unit_code_lands_the_unit_and_never_merges_with_the_base_code(self):
        """扫箱码 = 这一行按箱入库(1 箱 ≠ 1 瓶)· 单位既要写进字段也要显在屏上。"""
        got = scenario("""
(async () => { openIn(); await feed(BOX); await feed(COLA); out({ rows: snapshot() }); })();
""")
        box, bottle = got["rows"][0], got["rows"][1]
        self.assertEqual("lang", box["unit"], "单位没随行写进 unit_name(后端换算的凭据)")
        self.assertEqual("lang", box["unitText"], "屏上看不见单位 —— 还是一个没有单位的 1")
        self.assertFalse(box["unitHidden"])
        self.assertEqual("p-cola", bottle["product"])
        self.assertEqual("", bottle["unit"], "瓶码被并进了箱那一行")

    def test_main_barcode_hit_does_not_stamp_a_unit_on_the_row(self):
        """主码命中时后端会把 base_unit 填进 matched_unit,照单全收 = 每行都贴个没用的单位。"""
        got = scenario(
            "(async () => { openIn(); await feed(COLA); out({ rows: snapshot() }); })();"
        )
        self.assertEqual("", got["rows"][0]["unit"])
        self.assertTrue(got["rows"][0]["unitHidden"])

    def test_receive_cost_prefers_current_average_over_reference(self):
        got = scenario(
            "(async () => { openIn(); await feed(COLA); out({ rows: snapshot() }); })();"
        )
        self.assertEqual("8.5", got["rows"][0]["cost"])

    def test_uncached_scan_prefills_the_reference_cost(self):
        got = scenario(
            "(async () => { openIn(); await feed(MILK); out({ rows: snapshot() }); })();"
        )
        self.assertEqual("6.2", got["rows"][0]["cost"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过真 DOM 行为测试")
class UnmatchedCode(unittest.TestCase):
    """未命中:码要显出来,「去建这个商品」要真按跨页带码桥的契约调。"""

    def test_not_found_card_carries_the_scanned_code(self):
        got = scenario("""
(async () => {
    openIn(); await feed(GHOST);
    const btn = msgEl().querySelector('[data-scan-create]');
    out({ code: btn ? btn.dataset.scanCreate : null, text: msgEl().textContent,
          rows: snapshot().length });
})();
""")
        self.assertEqual(
            "9999999999999", got["code"], "未命中卡没带上扫到的码 —— 店员分不清码贴错了还是没建档"
        )
        self.assertIn("bscan.notfound", got["text"])
        self.assertEqual(2, got["rows"], "未命中不该加行")

    def test_create_button_calls_the_bridge_with_overlay(self):
        got = scenario("""
(async () => {
    openIn();
    const calls = [];
    window.openProductFormWithBarcode = (code, opts) => { calls.push({ code, opts }); return true; };
    await feed(GHOST);
    msgEl().querySelector('[data-scan-create]').click();
    out({ calls, maskStillOpen: document.getElementById('inv-in-mask').classList.contains('show'),
          rows: snapshot().length });
})();
""")
        self.assertEqual(1, len(got["calls"]), "点「去建这个商品」没调跨页带码桥")
        self.assertEqual("9999999999999", got["calls"][0]["code"])
        self.assertEqual(
            {"overlay": True},
            got["calls"][0]["opts"],
            "没要求叠在入库弹窗之上 —— 跳走会丢半张入库单",
        )
        self.assertTrue(got["maskStillOpen"])
        self.assertEqual(2, got["rows"], "已扫进去的行被清掉了")

    def test_a_failed_code_survives_the_next_scan(self):
        """后一件的「已加入」不许把前一件的「这个码没建档」盖掉 —— 被盖掉的那件就是
        「扫了、没进单、也没人告诉他」的货,店员按屏上反馈收货,一整箱凭空消失。"""
        got = scenario("""
(async () => { openIn(); await feed(GHOST); await feed(COLA);
               out({ text: msgEl().textContent,
                     cards: msgEl().querySelectorAll('[data-scan-create]').length }); })();
""")
        self.assertIn("bscan.notfound", got["text"], "没建档那条被下一件的「已加入」盖掉了")
        self.assertIn("9999999999999", got["text"], "盖掉之后连是哪个码都看不见了")
        self.assertIn("inv-scan-added", got["text"], "最新那件的状态也得在")
        self.assertEqual(1, got["cards"])

    def test_bridge_saying_no_falls_back_honestly(self):
        """桥没接上/它说打不开 → 不许假装成功,得给一句带着那串码的人话。"""
        got = scenario("""
(async () => {
    openIn();
    window.openProductFormWithBarcode = () => false;
    await feed(GHOST);
    msgEl().querySelector('[data-scan-create]').click();
    await tick();
    out({ text: msgEl().textContent });
})();
""")
        self.assertIn("inv-scan-create-manual", got["text"], "桥打不开时没给诚实回落")
        self.assertIn("9999999999999", got["text"], "回落文案里没有那串码")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过真 DOM 行为测试")
class GunIntoARowField(unittest.TestCase):
    """枪扫进行内那几个框(数量/批号)。按键是真的:楔子挂在 document 上,这里按物理节拍发。"""

    def test_gun_into_the_batch_field_lands_a_row_and_leaves_the_field_clean(self):
        """批号框对枪 opt-in 的实际效果 —— 不 opt-in 就是整发被吞(零回调、行不出现),
        而那串数字照旧留在批号框里。5ms/字符 = 枪速。"""
        got = scenario("""
(async () => {
    openIn();
    await feed(MILK);                                  // 批次品 → 批号格露出来
    const batch = rowField(0, 'batch_no');
    typeInto(COLA, batch, 5, 'Enter');
    await tick(); await tick();
    out({ lookups, batch: batch.value, rows: snapshot(), prevented });
})();
""")
        self.assertEqual(
            [
                "/api/sales/products/lookup?barcode=4901234567894",
                "/api/sales/products/lookup?barcode=8850999320014",
            ],
            got["lookups"],
            "枪扫进批号框整发被吞 —— 这一箱货没进单也没人知道",
        )
        self.assertEqual("", got["batch"], "码留在批号框里 · 楔子没把框还原成扫之前")
        self.assertEqual(["p-milk", "p-cola"], [r["product"] for r in got["rows"]])
        self.assertEqual(1, got["prevented"], "枪的回车没吃掉 · 半张入库单会被顺手提交")

    def test_the_open_modal_takes_the_gun_away_from_the_page_underneath(self):
        """独占:弹窗开着时底下页面的订阅者收不到(不然枪扫的货会同时进两个地方),
        关了弹窗才轮到它。探针用真 wedge 注册,不替换实现。"""
        got = scenario("""
(async () => {
    const probe = [];
    const off = window.PearnlyScanWedge.register((code) => probe.push(code));
    openIn();
    typeInto(COLA, null, 5, 'Enter');                  // 框外的一串 · 楔子该收
    await tick(); await tick();
    const during = probe.slice();
    const landed = snapshot()[0].product;
    closeIn();
    typeInto(COLA, null, 5, 'Enter');
    await tick();
    const after = probe.slice();
    off();
    out({ during, after, landed });
})();
""")
        self.assertEqual([], got["during"], "弹窗开着时底下那一页也收到了同一发枪")
        self.assertEqual("p-cola", got["landed"], "弹窗自己没收到 · 这组断言没有区分力")
        self.assertEqual(["8850999320014"], got["after"], "关了弹窗独占没撤 · 全站扫码从此进不来")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过真 DOM 行为测试")
class BurstJudgedAsTyping(unittest.TestCase):
    """判成「人在打字」的那一发也必须看得见。

    三轮实测的那一幕:慢枪扫的第二箱被判成人打字 → 楔子不回调 → 屏上零字、消息还停在上一件
    的「已加入」→ 店员以为枪没响,再扫一次又被吞,整箱货从收货单上消失且没人看得见。
    判据本身是对的(慢枪与打字快的人分不开,只能偏向人手),错的是不吭声。
    """

    LINE = "inv-scan-typed{code}{name}{unit}{n}"  # t() 桩的回值:钉住用的是哪一句

    def test_a_slow_burst_in_the_qty_field_says_so_instead_of_vanishing(self):
        got = scenario("""
(async () => {
    openIn();
    await feed(COLA);                                  // 第一箱进单 · 光标停在数量框
    const was = msgEl().textContent;
    typeInto(MILK, rowField(0, 'qty'), 90, 'Enter');    // 90ms/字符:过不了 50ms 那条
    await tick();
    const btn = msgEl().querySelector('[data-scan-typed]');
    const line = msgEl().querySelector('.c');
    out({ was, line: line ? line.textContent : '', text: msgEl().textContent,
          lookups: lookups.length, btnCode: btn ? btn.dataset.scanTyped : null,
          milk: MILK, prevented });
})();
""")
        self.assertIn("inv-scan-added", got["was"], "第一箱没进单 · 这轮的前提不成立")
        self.assertEqual(1, got["lookups"], "慢枪那一发被当成扫码收了 · 这轮验的不是这件事")
        self.assertEqual(0, got["prevented"], "人手打的回车被吃掉 · 表单再也提交不了")
        self.assertEqual(self.LINE, got["line"], "屏上一个字都没有 —— 这一发去哪了没人知道")
        self.assertNotIn("inv-scan-added", got["text"], "消息还停在上一件的「已加入」")
        self.assertIn(got["milk"], got["text"], "没带上那串字符 · 店员认不出是自己刚才那一枪")
        self.assertEqual(got["milk"], got["btnCode"], "没给出路 · 慢枪扫的这箱货补不回来")

    def test_the_way_out_restores_the_field_and_looks_the_code_up(self):
        """店员说「这一串确实是扫的」:码要真查、框要还原 ——
        不还原就是数量 = 1 + 一串条码跟着整张收货单提交上去。"""
        got = scenario("""
(async () => {
    openIn();
    await feed(COLA);
    const qty = rowField(0, 'qty');
    typeInto(MILK, qty, 90, 'Enter');
    await tick();
    const dirty = qty.value;                           // 楔子没动过框:码还留在里面
    const way = msgEl().querySelector('[data-scan-typed]');
    if (way) way.click();
    await tick(); await tick();
    out({ dirty, qty: rowField(0, 'qty').value, rows: snapshot(), lookups, milk: MILK });
})();
""")
        self.assertEqual("1" + got["milk"], got["dirty"], "码没真落进数量框 · 这轮证明不了还原")
        self.assertEqual("1", got["qty"], "点了「当条码用」却把那串码留在数量框里")
        self.assertEqual(2, len(got["lookups"]), "点了没去查这个码 · 出路是假的")
        self.assertEqual(["p-cola", "p-milk"], [r["product"] for r in got["rows"]])

    def test_typing_a_quantity_says_nothing(self):
        """不打扰的另一半:数量框里打个 240 不值得说什么,一有按键就冒一句话等于噪音。"""
        got = scenario("""
(async () => {
    openIn();
    await feed(COLA);
    typeInto('240', rowField(0, 'qty'), 90, 'Tab');
    await tick();
    out({ text: msgEl().textContent, qty: rowField(0, 'qty').value,
          typed: !!msgEl().querySelector('[data-scan-typed]') });
})();
""")
        self.assertFalse(got["typed"], "人打三位数量也弹一句 · 这句话很快就没人看了")
        self.assertIn("inv-scan-added", got["text"], "上一件的状态被一句打字提示顶掉了")
        self.assertEqual("1240", got["qty"], "楔子动了人手打进去的数量")

    def test_a_real_gun_in_the_same_field_still_just_scans(self):
        """防修过头:同一个框、同一串码,5ms/字符照旧当扫码 —— 不该冒那句打字提示。"""
        got = scenario("""
(async () => {
    openIn();
    await feed(COLA);
    typeInto(BOX, rowField(0, 'qty'), 5, 'Enter');
    await tick(); await tick();
    out({ rows: snapshot(), lookups: lookups.length, qty: rowField(0, 'qty').value,
          typed: !!msgEl().querySelector('[data-scan-typed]'), prevented });
})();
""")
        self.assertEqual(2, got["lookups"], "真枪打进数量框被吞了")
        self.assertFalse(got["typed"], "枪速的一串也被说成「按手输处理」")
        self.assertEqual("1", got["qty"], "枪扫的码留在了数量框里")
        self.assertEqual(1, got["prevented"], "枪的回车没吃掉")
        self.assertEqual("lang", got["rows"][1]["unit"], "箱码没落成按箱入库的那一行")


if __name__ == "__main__":
    unittest.main()
