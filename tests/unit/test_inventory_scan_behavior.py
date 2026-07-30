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

from tests.unit._inventory_scan_dom import run

# 货架与查码应答:内容是造的(那是网络),但落地的每个字段名都照 routes/products_routes.py
# 的 /lookup 信封写,读它的是产品自己的代码。
_FIXTURE = r"""
const COLA = '8850999320014';
const BOX = '8850999320021';   // 同一件可乐的箱码(挂在 product_units 上)
const MILK = '4901234567894';  // 批次品
const GHOST = '9999999999999'; // 库里没有
const P_COLA = { id: 'p-cola', name_th: 'coke', name_en: 'Coke', name_zh: 'kele', track_batch: false };
const P_MILK = { id: 'p-milk', name_th: 'nom', name_en: 'Milk', name_zh: 'niunai', track_batch: true };
const LOOKUP = {
    [COLA]: { product: P_COLA, matched_by: 'product', matched_unit: 'khuad' },
    [BOX]: { product: P_COLA, matched_by: 'unit', matched_unit: 'lang' },
    [MILK]: { product: P_MILK, matched_by: 'product', matched_unit: 'klong' },
};
reply = (url) => {
    const code = decodeURIComponent(String(url).split('barcode=')[1] || '');
    return LOOKUP[code] ? answer(LOOKUP[code]) : answer({ detail: 'sales.product_not_found' }, 404);
};
shelf = [
    { product_id: 'p-cola', name: { th: 'coke', en: 'Coke', zh: 'kele' }, track_batch: false, batches: [] },
];

// 扫码只从产品自己的入口进:扫码框里回车(mountInvScan 绑的 onkeydown)。
async function feed(code) {
    const input = document.getElementById('inv-in-mask-scan-code');
    input.value = code;
    input.onkeydown({ key: 'Enter', preventDefault() {} });
    await tick();
    await tick();
}
function closeIn() {
    // 走产品自己的关窗按钮(页脚那个「取消」),不直接调 unmountInvScan —— 直接调等于
    // 绕过 closeModal 这条真路,「关窗到底放没放开」就没被验到
    const mask = document.getElementById('inv-in-mask');
    const foot = mask.querySelector('.inv-modal-foot');
    foot.querySelector('[data-inv-close]').click();
}
"""


def scenario(body: str) -> dict:
    return run(_FIXTURE + body)


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


if __name__ == "__main__":
    unittest.main()
