#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/unit/test_inventory_scan_guards.py

入库/盘点弹窗的两道「兜底」在真 DOM 里跑一遍 —— 都是「上一层判据必然有个盲区,盲区里
不能一声不吭」这同一件事的两侧:

  1. 摄像头把第二箱当成「同一件还在画面里」挡下的那一次(scan-camera.js 的 onDuplicate)。
     两把尺子 AND 起来必然有个地板;地板以下,真第二箱与一次长反光在解码结果上同形。
  2. 提交前的数量兜底(isSaneQty)。楔子在框那一层还原得再准,漏一次就是一串条码当数量
     进了库存与成本。

从 test_inventory_scan_behavior.py 拆出来只因行数(单文件 <500)· 用的是同一套 harness
(_inventory_scan_dom.py 的 scenario:弹窗由 inventory-modals.ts 现渲染、楔子与
inventory-common 是真件,只有后端与摄像头引擎是桩)。
"""

from __future__ import annotations

import shutil
import unittest

from tests.unit._inventory_scan_dom import HOME_DIR, PROJECT_ROOT, scenario


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过真 DOM 行为测试")
class CameraSuppressedAScan(unittest.TestCase):
    """摄像头把第二箱挡下的那一次,必须说出来。

    引擎那两把尺子(墙钟 + 采样数 AND)必然有个地板(店里那台 ≈1.6s):地板以下,拿走 A 再
    举 B 与一次长反光在解码结果上完全同形,引擎分不出来。分不出就不能替店员默默决定 ——
    默默决定的那一半是收货单上少一箱,而屏上跟扫成功一模一样。
    """

    def test_the_engine_really_calls_this_hook(self):
        """被回调的名字必须来自真引擎:桩自己造一个名字出来验自己,是这批栽过的那种假绿。"""
        engine = (PROJECT_ROOT / "static" / "scan" / "scan-camera.js").read_text(encoding="utf-8")
        self.assertIn("o.onDuplicate(code, { gapMs: gapMs, misses: misses })", engine)
        self.assertIn(
            "onDuplicate: (code) => host.onDup(code)",
            (HOME_DIR / "inventory-scan-camera.ts").read_text(encoding="utf-8"),
            "入库侧没把这个口接上 —— 引擎喊了没人听",
        )

    def test_a_suppressed_second_box_gets_a_line_and_a_way_back(self):
        got = scenario("""
(async () => {
    openIn();
    document.getElementById('inv-in-mask-scan-cam').onclick();
    await tick();
    camLog.opts.onScan(COLA);                                  // 第一箱:引擎解出来了
    await tick(); await tick();
    const afterFirst = snapshot()[0].qty;
    camLog.opts.onDuplicate(COLA, { gapMs: 1200, misses: 9 }); // 第二箱在地板以下被挡下
    await tick();
    const btn = msgEl().querySelector('[data-scan-dup]');
    const said = msgEl().textContent;
    if (btn) btn.click();                                      // 店员说:是第二件
    await tick(); await tick();
    out({ afterFirst, said, code: btn ? btn.dataset.scanDup : null,
          rows: snapshot(), lookups: lookups.length });
})();
""")
        self.assertEqual("1", got["afterFirst"], "第一箱没进单 · 这轮的前提不成立")
        self.assertIn("inv-scan-dup", got["said"], "被挡下的那一次一声不吭 —— 收货单上少一箱")
        self.assertIn("8850999320014", got["said"], "没带上码 · 店员认不出是哪件货")
        self.assertEqual("8850999320014", got["code"], "没给出路 · 少的那一箱补不回来")
        self.assertEqual("2", got["rows"][0]["qty"], "点了「是第二件」数量没动")
        self.assertEqual(
            ["p-cola", ""],
            [r["product"] for r in got["rows"]],
            "补一件却另起了一行(同一件非批次货只该累加)",
        )
        self.assertEqual(2, got["lookups"], "补那一件没走查码那条真路")

    def test_a_later_real_box_does_not_wipe_the_line_left_by_a_suppressed_one(self):
        """连收 6 箱同款可乐(3 箱真记上、3 箱被挡下):被挡下那几箱的痕迹得留到店员处理。

        这一行说的是【被挡下的那一箱】可能没进单,而后面记上的是【再一箱】—— 拿后者销前者
        等于把没进单的那箱悄悄抹掉,屏上跟 6 箱全收上了一模一样,而收货单只有 3 件:存货
        估值与之后每一笔 COGS 全错。同一个码只欠一笔(清单按码去重),所以留的是一行不是三行。
        真节拍那一跑在 scripts/_inv_guards_verify.cjs::dupNoticeSurvivesMixed(长短空档交替)。
        """
        got = scenario("""
(async () => {
    openIn();
    document.getElementById('inv-in-mask-scan-cam').onclick();
    await tick();
    const dupRows = () => msgEl().querySelectorAll('[data-scan-dup]').length;
    const box = async (kind) => {
        if (kind === 'seen') camLog.opts.onScan(COLA);
        else camLog.opts.onDuplicate(COLA, { gapMs: 1200, misses: 9 }); // 地板以下:引擎分不出
        await tick(); await tick();
    };
    await box('seen');                       // 第 1 箱:引擎解出来了
    await box('blocked');                    // 第 2 箱:被当成「同一件还在画面里」挡下
    const trail = [];
    await box('seen');  trail.push(dupRows()); // 第 3 箱记上 —— 第 2 箱那行还在吗
    await box('blocked');                      // 第 4 箱
    await box('seen');  trail.push(dupRows()); // 第 5 箱记上 —— 第 4 箱那行还在吗
    await box('blocked');                      // 第 6 箱
    out({ trail, endRows: dupRows(), rows: snapshot(), text: msgEl().textContent });
})();
""")
        self.assertEqual("3", got["rows"][0]["qty"], "真记上的三箱没进单 · 这轮的前提不成立")
        self.assertEqual([1, 1], got["trail"], "后面真记上的那一箱把被挡下那箱的唯一线索顺手销掉了")
        self.assertEqual(1, got["endRows"], "同一个码欠了不止一笔 · 清单按码去重这条破了")
        self.assertIn("inv-scan-fails-n", got["text"], "那一行没进累积清单(还占着瞬时行)")

    def test_an_ordinary_second_item_is_not_nagged_about(self):
        """反向:引擎认下的第二件(码真离开过画面)照旧直接加数量,不该冒这句问话 ——
        每扫一件都问一句「这是不是第二件」,店员三分钟后就不看这一格了。"""
        got = scenario("""
(async () => {
    openIn();
    document.getElementById('inv-in-mask-scan-cam').onclick();
    await tick();
    camLog.opts.onScan(COLA);
    await tick(); await tick();
    camLog.opts.onScan(COLA);      // 引擎判它离开过画面 → 这是实打实的第二件
    await tick(); await tick();
    out({ rows: snapshot(), text: msgEl().textContent,
          nag: !!msgEl().querySelector('[data-scan-dup]') });
})();
""")
        self.assertEqual("2", got["rows"][0]["qty"], "真的第二件没加上 —— 修一头把另一头弄坏了")
        self.assertFalse(got["nag"], "正常连扫也冒问话 · 这句话很快就没人看了")
        self.assertIn("inv-scan-bumped", got["text"], "第二件的状态不是「又加了一件」")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过真 DOM 行为测试")
class FocusRaceWithTheGun(unittest.TestCase):
    """枪比网络快:上一件的查码还在路上,下一发已经在往扫码框里打了。

    查码一回来 applyHit 就把光标抢到数量框 —— 后半串于是落进数量格。真浏览器实测
    (查码 220ms):数量变成 167894 且照样提交得出去,而第二箱那个码一次都没查过。
    楔子救不了这一档:扫码框没声明接枪,它在那里一个键都不收,拿不到前半串就无从还原。
    """

    def test_focus_is_not_stolen_while_the_scan_box_is_being_typed_into(self):
        got = scenario("""
(async () => {
    openIn();
    const box = document.getElementById('inv-in-mask-scan-code');
    document.getElementById('inv-in-mask-scan-cam').onclick();
    await tick();
    box.value = '49012';            // 下一发的前半截已经落在扫码框里了
    camLog.opts.onScan(COLA);       // 上一件的查码这时候才回来
    await tick(); await tick();
    out({ qty: rowField(0, 'qty').value, boxAfter: box.value,
          stolen: document.activeElement === rowField(0, 'qty') });
})();
""")
        self.assertEqual("1", got["qty"], "这一件没落行 · 这轮的前提不成立")
        self.assertFalse(got["stolen"], "扫码框正在被输入却把光标抢走 —— 后半串会落进数量格")
        self.assertEqual("49012", got["boxAfter"], "扫码框里已经打进去的半截被动过了")

    def test_an_idle_scan_box_still_hands_the_cursor_to_the_quantity(self):
        """反向:扫码框空着时照旧把光标交给数量框 —— 那是「扫完就能改数」的便利,不能顺手弄丢。"""
        got = scenario("""
(async () => {
    openIn();
    document.getElementById('inv-in-mask-scan-cam').onclick();
    await tick();
    camLog.opts.onScan(COLA);
    await tick(); await tick();
    out({ qty: rowField(0, 'qty').value,
          onQty: document.activeElement === rowField(0, 'qty') });
})();
""")
        self.assertEqual("1", got["qty"])
        self.assertTrue(got["onQty"], "扫完光标没落到数量框 · 整箱 24 支得先自己点一下才能改")


_SUBMIT = r"""
// 提交那一段:后端换成记账本(网络不在这条判定链上),别的照旧走产品自己的 doSubmit。
const posted = { in: [], count: [] };
common.invApi.postIn = async (_ws, lines) => { posted.in.push(lines); };
common.invApi.postCount = async (_ws, lines) => { posted.count.push(lines); };
function fillIn(qty) {
    const row = rows()[0];
    field(row, 'product_id').value = 'p-cola';
    field(row, 'qty').value = qty;
}
const clickSubmit = (maskId) => document.getElementById(maskId + '-submit').onclick();
// 提交成功会把弹窗整块清空 → 那时 err 格已经不在页面上。分开读:err 是「被拦住了」,
// still 是「弹窗还开着」—— 合在一起才说得清这一次到底是过了还是被挡了。
const errOf = (maskId) => {
    const el = document.getElementById(maskId + '-err');
    return el ? el.textContent : '';
};
const stillOpen = (maskId) => document.getElementById(maskId).classList.contains('show');
// 这个全局在真页面上由 src/home/with-loading.ts 挂(按钮转圈),harness 没装 —— 盘点提交
// 会死在 ReferenceError,而那跟「被兜底拦住」长得一模一样(都是没提交上去),绿得莫名。
global.withLoading = async (_btn, fn) => fn();
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过真 DOM 行为测试")
class QuantityBackstopAtSubmit(unittest.TestCase):
    """提交前的数量兜底:楔子在框那一层漏一次,19 亿件就跟着整张单子进库存与成本。

    两侧都得量 —— 拦得住整串条码,又挡不着真实的大批量入库(上限怎么定见
    inventory-common.ts 的 MAX_QTY_DIGITS)。只量前一侧就是四轮那个跟头。
    """

    def test_a_barcode_in_the_qty_box_never_reaches_the_backend(self):
        got = scenario(_SUBMIT + """
(async () => {
    openIn();
    fillIn('1' + COLA);   // 「1」后面接上整串条码 —— 楔子漏一次,数量框里就是这个样子
    // 元素先拿在手上:兜底一旦失效,提交会成功并把弹窗整块清空,后面再按 id 找就是
    // 一句 TypeError —— 那种红说的是 harness 崩了,不是「19 亿件进了后端」。
    const qty = rowField(0, 'qty');
    clickSubmit('inv-in-mask');
    await tick();
    out({ posted: posted.in, err: errOf('inv-in-mask'), value: qty.value,
          focused: document.activeElement === qty, selected: qty.selected || 0,
          open: stillOpen('inv-in-mask') });
})();
""")
        self.assertEqual([], got["posted"], "19 亿件跟着整张收货单进库存了")
        self.assertIn("inv-err-bad-qty", got["err"], "拦住了却不说为什么 · 店员只看到点了没反应")
        self.assertTrue(got["focused"], "没指到是哪一行 · 十几行的单子等于让他自己找")
        self.assertGreaterEqual(got["selected"], 1, "那串数字没被选中 · 改起来还得先删干净")
        self.assertEqual("18850999320014", got["value"], "偷偷把数量改掉了 · 静默改数比拦住更坏")
        self.assertTrue(got["open"], "拦下之后把弹窗关了 · 半张收货单跟着没了")

    def test_a_real_bulk_receipt_still_goes_through(self):
        """反向:这道闸不许挡住真实的大批量。十万件、上限那一格、拆零小数、空行,全要过。"""
        got = scenario(_SUBMIT + """
(async () => {
    const done = [];
    for (const q of ['250000', '9999999', '1234.567']) {
        openIn();          // 默认两行空行,只填第一行 —— 空行不许把整张单子卡住
        fillIn(q);
        clickSubmit('inv-in-mask');
        await tick(); await tick();
        done.push({ q, err: errOf('inv-in-mask'), open: stillOpen('inv-in-mask') });
    }
    out({ done, lines: posted.in.map((ls) => ls.map((l) => l.qty)) });
})();
""")
        self.assertEqual(["", "", ""], [d["err"] for d in got["done"]], "真实大批量被这道闸挡了")
        self.assertEqual([False] * 3, [d["open"] for d in got["done"]], "提交没走完 · 弹窗还开着")
        self.assertEqual([["250000"], ["9999999"], ["1234.567"]], got["lines"])

    def test_the_count_sheet_gets_the_same_backstop(self):
        """盘点这一侧连楔子都没有(counted_qty 不声明接枪,枪打的字符原样落进框),
        而它写的是「架上就是这么多」—— 一次就把这件货的库存改成天文数字。"""
        got = scenario(_SUBMIT + """
(async () => {
    document.body.innerHTML = '<div id="inv-count-mask"></div>';
    window.openInventoryCount();
    // 同上:元素先拿在手上,兜底失效时这一格已经不在页面上了
    const row = document.getElementById('inv-count-mask-rows').querySelectorAll('[data-row]')[0];
    const send = document.getElementById('inv-count-mask-submit');
    const cell = (k) => row.querySelector('[data-k="' + k + '"]');
    cell('product_id').value = 'p-cola';
    cell('counted_qty').value = MILK;      // 枪扫进盘点数量框
    send.onclick();
    await tick();
    const blocked = posted.count.length, err = errOf('inv-count-mask');
    cell('counted_qty').value = '0';       // 反向:0 是「架上真没有」这个合法答案
    send.onclick();
    await tick(); await tick();
    out({ blocked, err, counted: posted.count });
})();
""")
        self.assertEqual(0, got["blocked"], "一串条码被当成盘点结果写进库存了")
        self.assertIn("inv-err-bad-qty", got["err"])
        self.assertEqual([[{"product_id": "p-cola", "counted_qty": "0"}]], got["counted"])


if __name__ == "__main__":
    unittest.main()
