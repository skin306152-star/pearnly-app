#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_scan_fail_ledger.py

收银台扫码失败清单这本账(static/pos/pos-scan.js 的 fails + pos-cashier.js 的 clearCart)。
真 node 跑真源文件 + 真 DOM 桩,断的是屏上到底还剩几行、剩的是哪个码 —— 不是源码里有没有
出现某个函数名。

清单说的是一句话:**这一单还有几件货没进购物车**。店员照它清点柜台,所以它每错一次都对得上
一次钱错:
  1. 命中后不销账 → 码 404 记一笔,老板补录条码,店员重扫,车里真有了这件货,而清单仍白纸
     黑字说它没进车 → 店员照着再补一件 = 收两遍钱。入库侧早有 resolveFail,收银侧漏了。
  2. 同码连扫堆重复行 → 店员以为没扫上就再扫一下,一件货记三笔,「还有 3 件没进车」是假的。
  3. 「搜这个码」和 Esc 清整份 → 按钮上写的是「搜这个码」,干的是「这一轮的失败我全不管了」;
     Esc 是关取景层的手势,却顺手把几件没进车的货静默抹平 —— 抹完没有任何地方还记得它们。
  4. 收完一单不清 → 上一位客人那件没进车的货顶在下一位客人的屏上。

判据一律取真产物:行数从 #bscan-fails 的子节点数,码从渲染出来的文字,车从 renderCart 的
真 HTML。反证一律用「会出事的输入」——同码 + 异码混扫、两条并存时只点其中一条、清单非空时
才结账,只留一条的输入证不出「动的是哪一条」。
"""

from __future__ import annotations

import shutil
import unittest

from tests.unit._pos_scan_dom import run as run_scan_harness

# 只放本测断言要用到的键(真字典的 4 语完整性归 test_pos_spa_i18n.py 那道闸)。
DICT_ZH = {
    "posui.bscan.count": "已扫 {n} 件",
    "posui.bscan.done": "完成",
    "posui.bscan.added": "已加入 {name}",
    "posui.bscan.fails_n": "{n} 件没加进购物车",
    "posui.bscan.fails_ack": "知道了",
    "posui.bscan.search_code": "用这个码搜商品",
    "posui.bscan.create_where": "让老板在后台把这个码填进「条码」",
    "posui.bscan.queued": "还有 {n} 件在排队",
    "bscan.notfound": "没有条码 {code} 的商品",
    "bscan.manual": "手动输入条码",
    "posui.retry": "重试",
    "pos.unexpected": "出了点问题",
    "posui.toast.paid": "已收款",
}

NODE_MAIN = r"""
// ── 语料:两个后台没建档的码 + 一件后来补录好的货 ────────────────────────
const GHOST = '8850111000039'; // 柜台上有货、后台没建档的那一件
const OTHER = '8850111000046'; // 同一轮里另一件也没建档的 —— 用来证「只动了那一条」
const SOLD = '8850999320013';

function product(id, name, unit, code, price) {
    return {
        id: id,
        name: { th: name, en: name, zh: name, ja: name },
        category_id: 1,
        base_unit: unit,
        image_url: null,
        vat_applicable: true,
        units: [
            { unit_name: unit, factor: '1.000', barcode: code, price: price, default_sell: true },
        ],
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '10.000', near_expiry: false },
        matched_unit: unit,
    };
}
const envelope = (d) => ({ status: 200, body: { ok: true, data: d } });
const NOT_FOUND = {
    status: 404,
    body: { ok: false, error: { code: 'pos.product_not_found', detail: null } },
};

const failsBox = () => document.getElementById('bscan-fails');
const failsShown = () => failsBox().classList.contains('show');
const failsText = () => failsBox().textContent;
const failRows = () => failsBox().children.slice(1); // 第 0 个是「N 件没加进购物车 / 知道了」头部
const headText = () => (failsBox().children[0] || { textContent: '' }).textContent;
function descend(el, out) {
    (el.children || []).forEach((c) => {
        out.push(c);
        descend(c, out);
    });
    return out;
}
// 按显示的字找按钮(文案从桩字典取,不在测里另写一份)。找不到回 false 而不是抛错:
// 按钮消失本身就是要验的病灶,崩掉会把整批断言变成一坨看不出病因的 ERROR。
function clickInFails(label) {
    const hit = descend(failsBox(), []).find((e) => e.textContent === label);
    if (hit) hit.click();
    return !!hit;
}
const cartLines = () =>
    Array.from(
        String(document.getElementById('cart-lines').innerHTML).matchAll(/class="n">([^<]*)</g)
    ).map((m) => m[1]);
const subtotal = () => Number(document.getElementById('cart-subtotal').textContent.replace(/,/g, ''));

POS.state.online = true;
POS.offline = { hasSnapshot: () => false, filterCached: () => [] };
// 收款设置这一层归 POS.pay(本测不验它)· 结账要走完必须有它。
POS.pay = { inclVat: () => false, settings: () => ({}), applyMethods() {}, refresh() {}, ensure() {} };
// 挂单存本地(clearCart 的三条真实来路之一);node 里没有 localStorage。
const LS = {};
global.localStorage = {
    getItem: (k) => (k in LS ? LS[k] : null),
    setItem: (k, v) => (LS[k] = String(v)),
    removeItem: (k) => delete LS[k],
};
// 真绑事件:cart-clear / cart-hold / 收款确认都是 init() 里挂上去的,不 init 就只能去戳内部函数。
POS.cashier.init();

const R = {};

async function main() {
    // ── 1. 同一个码连扫三次:一件货一行 ────────────────────────────────
    // 敌意输入:中间插一个不同的码。只扫同一个码证不出去重是「按码」还是「只留最新一条」。
    NEXT = NOT_FOUND;
    await POS.scan.submit(GHOST);
    await POS.scan.submit(OTHER);
    await POS.scan.submit(GHOST);
    await POS.scan.submit(GHOST);
    R.dedupe_rows = failRows().length;
    R.dedupe_head = headText();
    R.dedupe_keeps_other = failsText().indexOf(OTHER) >= 0;
    R.dedupe_keeps_ghost = failsText().indexOf(GHOST) >= 0;

    // ── 2. 老板补录了条码,店员回来重扫:那笔待办要销掉 ──────────────────
    // 敌意输入:清单上同时挂着另一件仍然没建档的货。只留一条时「销掉这一条」和「整份清光」
    // 长得一模一样 —— 三轮报的正是这种分不开的输入。
    NEXT = envelope(product('p1', 'ขนมปัง', 'ถุง', GHOST, '25.00'));
    const linesBefore = cartLines().length;
    const subBefore = subtotal();
    await POS.scan.submit(GHOST);
    R.resolve_cart_new_lines = cartLines().length - linesBefore;
    R.resolve_cart_adds = subtotal() - subBefore;
    R.resolve_rows = failRows().length;
    R.resolve_ghost_gone = failsText().indexOf(GHOST) < 0;
    R.resolve_other_stays = failsText().indexOf(OTHER) >= 0;
    R.resolve_head = headText();

    // ── 3.「用这个码搜商品」只销那一条 ─────────────────────────────────
    // 清单上此刻是 OTHER 一条;再记一件,凑成两条才分得出「动一条」和「清整份」。
    const THIRD = '8850111000053';
    NEXT = NOT_FOUND;
    await POS.scan.submit(THIRD);
    R.search_rows_before = failRows().length;
    R.search_btn_found = clickInFails(DICT['posui.bscan.search_code']);
    R.search_box = document.getElementById('main-search').value;
    R.search_rows_after = failRows().length;
    R.search_other_stays = failsText().indexOf(OTHER) >= 0;

    // ── 4. Esc:只关取景层,不动这本账 ─────────────────────────────────
    // 4a 取景层没开时按 Esc(店员想取消眼前别的什么)· 清单一行都不许少。
    R.esc_rows_before = failRows().length;
    pressKey('Escape');
    R.esc_rows_after = failRows().length;
    R.esc_other_stays = failsText().indexOf(OTHER) >= 0;
    // 4b 取景层开着时按 Esc:层关了,账还在(店员正要拿这个码去后台建品)。
    await POS.scan.open(); // 解码器在 node 里拉不下来 → 停在错误卡,层已开着
    R.esc_layer_open = document.getElementById('bscan-mask').classList.contains('show');
    pressKey('Escape');
    R.esc_layer_closed = !document.getElementById('bscan-mask').classList.contains('show');
    R.esc_rows_after_layer = failRows().length;

    // ── 5. 收完一单:这本账归零,不许挂到下一位客人头上 ──────────────────
    // 走真结账路:填卡机金额 → 点确认 → submitSale → createSale → onOk → clearCart。
    R.sale_rows_before = failRows().length;
    R.sale_cart_before = cartLines().length;
    NEXT = envelope({
        sale: {
            id: 's1',
            receipt_no: 'RCP-1',
            grand_total: subtotal().toFixed(2),
            paid_total: subtotal().toFixed(2),
            change_amount: '0.00',
            status: 'completed',
        },
    });
    document.getElementById('pay-card-amt').value = String(subtotal());
    document.getElementById('pay-card-confirm').click();
    await new Promise((r) => setTimeout(r, 0));
    await new Promise((r) => setTimeout(r, 0));
    R.sale_cart_after = cartLines().length;
    R.sale_rows_after = failRows().length;
    R.sale_fails_shown = failsShown();

    // ── 6. 下一位客人:新的失败照常记 —— 清空不是把这本账关掉 ─────────────
    NEXT = NOT_FOUND;
    await POS.scan.submit(SOLD);
    R.next_customer_rows = failRows().length;
    R.next_customer_text = failsText();

    process.stdout.write(JSON.stringify(R));
}
main().catch((e) => {
    process.stderr.write(String((e && e.stack) || e));
    process.exit(1);
});
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端链路测试")
class PosScanFailLedgerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = run_scan_harness(NODE_MAIN, DICT_ZH)

    # ── 1. 同码去重 ──
    def test_the_same_code_scanned_again_refreshes_one_row_instead_of_stacking(self):
        # 店员看不到反应就会再扫一下 —— 那是最常见的动作,不是异常操作。
        # 一件货记三笔,「还有 3 件没进购物车」这个数就是假的,而他正照着这个数清点柜台。
        self.assertEqual(self.r["dedupe_rows"], 2, "同一个码扫三次堆出了重复行")
        self.assertEqual(self.r["dedupe_head"], "2 件没加进购物车知道了")
        self.assertTrue(self.r["dedupe_keeps_ghost"])
        self.assertTrue(self.r["dedupe_keeps_other"], "去重把另一个码也一起吃掉了")

    # ── 2. 命中销账 ──
    def test_a_code_that_finally_makes_it_into_the_cart_leaves_the_ledger(self):
        # 老板在后台补录条码 → 店员回来重扫 → 车里真有了这件货。清单还说它没进车,
        # 店员照着再补一件就是收两遍钱,而屏上、小票上都看不出异常。
        self.assertEqual(self.r["resolve_cart_new_lines"], 1, "重扫没能把货加进车 · 判据前提不成立")
        self.assertEqual(self.r["resolve_cart_adds"], 25.0)
        self.assertTrue(self.r["resolve_ghost_gone"], "货已经在车里了,清单还挂着它没进车")
        self.assertEqual(self.r["resolve_rows"], 1)

    def test_resolving_one_code_does_not_wipe_the_rest_of_the_ledger(self):
        # 「命中就把清单清光」是修这条最省事的写法,而它会把另一件真没进车的货一起抹掉。
        self.assertTrue(self.r["resolve_other_stays"], "销一笔账顺手把别人的也销了")
        self.assertEqual(self.r["resolve_head"], "1 件没加进购物车知道了")

    # ── 3.「搜这个码」只动那一条 ──
    def test_search_this_code_settles_only_that_row(self):
        self.assertEqual(self.r["search_rows_before"], 2, "判据失效:只剩一条时分不出动了几条")
        self.assertTrue(self.r["search_btn_found"], "未命中那行没有「用这个码搜商品」= 死胡同")
        self.assertEqual(self.r["search_box"], "8850111000053")
        self.assertEqual(self.r["search_rows_after"], 1, "按钮上写「搜这个码」,干的是清整份")
        self.assertTrue(self.r["search_other_stays"])

    # ── 4. Esc ──
    def test_escape_never_silently_wipes_the_ledger(self):
        # 旧写法:取景层没开时 Esc = clearFails()。店员想取消眼前别的什么,几件没进车的货
        # 就这么静默消失了 —— 之后没有任何地方还记得它们。清单头上本来就有「知道了」这个出口。
        self.assertEqual(self.r["esc_rows_before"], 1)
        self.assertEqual(self.r["esc_rows_after"], 1, "Esc 把没处理完的货抹掉了")
        self.assertTrue(self.r["esc_other_stays"])

    def test_escape_still_closes_the_camera_layer_and_the_ledger_outlives_it(self):
        # 只保留「Esc 关层」这一半:关层正是店员要拿这个码去后台建品的时候。
        self.assertTrue(self.r["esc_layer_open"], "判据失效:取景层压根没开起来")
        self.assertTrue(self.r["esc_layer_closed"], "Esc 关不掉取景层了")
        self.assertEqual(self.r["esc_rows_after_layer"], 1)

    # ── 5. 一单结束 ──
    def test_finishing_a_sale_clears_the_ledger_for_the_next_customer(self):
        # 走的是真结账路(点收款确认 → createSale → 成交)。不清 = 上一位客人那件没进车的货
        # 顶在下一位客人的屏上,店员照着它补一件根本不属于这一单的货。
        self.assertEqual(self.r["sale_rows_before"], 1, "判据失效:结账前清单是空的,证不出清没清")
        self.assertGreater(self.r["sale_cart_before"], 0, "判据失效:车是空的,这笔单没真成交")
        self.assertEqual(self.r["sale_cart_after"], 0, "判据失效:车没清 = 这单根本没走完")
        self.assertEqual(self.r["sale_rows_after"], 0, "上一位客人的欠账挂到了下一位头上")
        self.assertFalse(self.r["sale_fails_shown"])

    def test_clearing_the_ledger_does_not_switch_it_off_for_the_next_customer(self):
        # 「清空」最省事的写法是把清单藏起来不再画 —— 那样下一位客人的失败就再也不出声了。
        self.assertEqual(self.r["next_customer_rows"], 1)
        self.assertIn("8850999320013", self.r["next_customer_text"])


if __name__ == "__main__":
    unittest.main()
