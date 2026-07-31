#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_scan_blocked_input.py

收银台收下了却没进购物车的那一发(static/pos/pos-scan.js 的 notAdded / onTyped)。

两条入口,同一种病:枪响了、灯闪了,而屏上一个字都没变 —— 店员没有任何办法知道这一件没算
进去,那件货就跟着顾客出门了。
  1. 弹窗开着时扫码。**不加进车是对的**(收款中改车会让金额跟已经报给顾客的应付对不上),
     错的是一声不吭:收款窗开着正是最后一件货最容易被补扫的时刻。
  2. 楔子判成「人在打字」的那一发(onTyped)。同上,只是换了个入口。

两个方向都要钉,只钉一侧就是上一轮的错法:
  正向 —— 屏上真有字(toast 的文本 + 清单里那一行的码),不是「函数被调过」。
  反向 —— 说了不许顺手把货加进车(不许发查码请求、不许多一行),不许长得像「已加入」,
         也不许在店员回头补扫时把这条欠账留着说「这件没进车」(那是收两遍钱的开头)。
"""

from __future__ import annotations

import re
import shutil
import unittest
from pathlib import Path

from tests.unit._pos_scan_dom import run as run_scan_harness

POS_DIR = Path(__file__).resolve().parents[2] / "static" / "pos"

# 只放本测断言要用到的键(真字典的 4 语完整性归 test_pos_spa_i18n.py 那道闸)。
DICT_ZH = {
    "posui.bscan.count": "已扫 {n} 件",
    "posui.bscan.added": "已加入 {name}",
    "posui.bscan.fails_n": "{n} 件没加进购物车",
    "posui.bscan.fails_ack": "知道了",
    "posui.bscan.queued": "还有 {n} 件在排队",
    "posui.bscan.modal_busy": "窗口开着 · {code} 没加进购物车",
    "posui.bscan.modal_hint": "关掉这个窗口再扫一次",
    "posui.bscan.typed": "按手打的处理了 · {code} 没当条码读",
    "posui.bscan.typed_hint": "确实是扫的就再扫一次",
    "bscan.notfound": "没有条码 {code} 的商品",
    "pos.unexpected": "出了点问题",
}

NODE_MAIN = r"""
const COLA = '8850999320014';

const COLA_ITEM = {
    id: 'p-cola',
    name: { th: 'โค้ก', en: 'Coke', zh: '可乐', ja: 'コーラ' },
    category_id: 1,
    base_unit: 'ขวด',
    base_price: '15.00',
    image_url: null,
    vat_applicable: true,
    units: [
        { unit_name: 'ขวด', factor: '1.000', barcode: COLA, price: '15.00', default_sell: true },
    ],
    track_batch: false,
    is_weighed: false,
    stock: { qty_base: '48.000', near_expiry: false },
    matched_unit: 'ขวด',
};

const failsBox = () => document.getElementById('bscan-fails');
const failRows = () => failsBox().children.slice(1); // 第 0 个是「N 件没加进购物车 / 知道了」头部
const headText = () => (failsBox().children[0] || { textContent: '' }).textContent;
const cartLines = () =>
    Array.from(
        String(document.getElementById('cart-lines').innerHTML).matchAll(/class="n">([^<]*)</g)
    ).map((m) => m[1]);
const lastToast = () => toasts[toasts.length - 1] || { msg: '', type: '' };

// 「有窗开着」在产品里的唯一依据就是这一个选择器(pos-scan.js 的 modalOpen)。
const MODAL_SEL = '#view-main .mask.show';
const openModal = () => (QS_ONE[MODAL_SEL] = mkEl('div'));
const closeModal = () => delete QS_ONE[MODAL_SEL];

NEXT = { status: 200, body: { ok: true, data: COLA_ITEM } };
POS.state.online = true;
POS.offline = { hasSnapshot: () => false, filterCached: () => [] };
document.getElementById('view-main').classList.add('is-active'); // 店员在收银主屏

const R = {};

async function main() {
    // ── 1. 弹窗开着时扫一发:不加进车,但屏上必须有字 ──────────────────────
    openModal();
    const callsBefore = CALLS;
    await gunScan(COLA);
    R.blocked_calls = CALLS - callsBefore; // 0 = 连查码都没发(不许偷偷加进车)
    R.blocked_cart = cartLines().length;
    R.blocked_toast = lastToast().msg;
    R.blocked_toast_type = lastToast().type;
    R.blocked_rows = failRows().length;
    R.blocked_row_text = failRows().length ? failRows()[0].textContent : '';
    R.blocked_head = headText();

    // ── 2. 同一件货再扫一遍(店员以为没扫上):仍然只欠一笔 ─────────────────
    await gunScan(COLA);
    R.blocked_rows_twice = failRows().length;
    R.blocked_head_twice = headText();

    // ── 3. 店员关掉窗口回头补扫:货进车,那笔欠账跟着销 ─────────────────────
    closeModal();
    const callsBeforeRetry = CALLS;
    await gunScan(COLA);
    R.retry_calls = CALLS - callsBeforeRetry;
    R.retry_cart = cartLines().length;
    R.retry_rows = failRows().length;
    R.retry_toast = lastToast().msg;

    // ── 4. 楔子判成「人在打字」的那一发:同样要有字,同样不许进车 ────────────
    const TYPED = '8850111000039';
    const callsBeforeTyped = CALLS;
    const cartBeforeTyped = cartLines().length;
    await typedScan(TYPED);
    R.typed_calls = CALLS - callsBeforeTyped;
    R.typed_cart_delta = cartLines().length - cartBeforeTyped;
    R.typed_toast = lastToast().msg;
    R.typed_toast_type = lastToast().type;
    R.typed_rows = failRows().length;
    R.typed_row_text = failRows().length ? failRows()[0].textContent : '';

    // ── 5. 一单结束:这两笔都归零,不许挂到下一位客人头上 ────────────────────
    POS.scan.saleEnded();
    R.sale_end_rows = failRows().length;

    process.stdout.write(JSON.stringify(R));
}
main().catch((e) => {
    process.stderr.write(String((e && e.stack) || e));
    process.exit(1);
});
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端链路测试")
class PosScanBlockedInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = run_scan_harness(NODE_MAIN, DICT_ZH)

    # ── 1. 弹窗开着 ──
    def test_a_scan_during_an_open_modal_is_announced_instead_of_swallowed(self):
        # 旧写法 `if (!isMainActive() || modalOpen()) return;` 一声不吭。收款窗开着正是最后
        # 一件货最容易被补扫的时刻:枪响了、灯闪了,屏上什么都没变,那件货就跟着顾客出门。
        self.assertEqual(self.r["blocked_toast"], "窗口开着 · 8850999320014 没加进购物车")
        self.assertEqual(self.r["blocked_rows"], 1, "屏上没留下这个码 · 回头没人知道欠的是哪一件")
        self.assertIn("8850999320014", self.r["blocked_row_text"])
        self.assertIn("关掉这个窗口再扫一次", self.r["blocked_row_text"], "只报状态不指路")
        self.assertEqual(self.r["blocked_head"], "1 件没加进购物车知道了")

    def test_announcing_it_never_smuggles_the_item_into_the_cart(self):
        # 反向:说一声不等于办了。查码请求都不许发 —— 收款中改车会让金额跟已经报给顾客的
        # 应付对不上,那是比静默更糟的一种错。
        self.assertEqual(self.r["blocked_calls"], 0, "弹窗开着时把码发去查了 = 差一步就加进车")
        self.assertEqual(self.r["blocked_cart"], 0, "弹窗开着时把货加进车了")

    def test_the_message_cannot_be_mistaken_for_a_successful_add(self):
        # 「已加入」是默认档 toast。这一条要是也长成默认档,店员扫完一眼扫过就当加上了。
        self.assertEqual(self.r["blocked_toast_type"], "error")
        self.assertNotIn("已加入", self.r["blocked_toast"])

    def test_the_same_code_scanned_twice_still_owes_exactly_one(self):
        # 店员看不到反应就再扫一下(最常见的动作)。一件货记两笔,「还有几件没进车」这个数
        # 就是假的 —— 而他正照着这个数清点柜台。
        self.assertEqual(self.r["blocked_rows_twice"], 1)
        self.assertEqual(self.r["blocked_head_twice"], "1 件没加进购物车知道了")

    # ── 2. 回头补扫 ──
    def test_rescanning_after_the_modal_closes_adds_it_and_settles_the_debt(self):
        # 反向的另一半:欠账留着说「这件没进车」而车里明明有它,店员照着再补一件就是收两遍钱。
        self.assertEqual(self.r["retry_calls"], 1, "关掉窗口后这一发没去查码 = 补扫这条路断了")
        self.assertEqual(self.r["retry_cart"], 1, "关掉窗口后补扫仍然进不了车")
        self.assertEqual(self.r["retry_rows"], 0, "货已经在车里了,清单还挂着它没进车")
        self.assertEqual(self.r["retry_toast"], "已加入 可乐")

    # ── 3. 判成「人在打字」的那一发 ──
    def test_a_burst_judged_as_typing_is_announced_too(self):
        # 楔子判不出是枪打的就交还给人:不回调、不动框里的内容 —— 屏上于是什么都没有。
        # 入库侧实测过这一幕:慢枪扫的第二箱整箱从收货单消失,店员以为枪没响。
        self.assertEqual(self.r["typed_toast"], "按手打的处理了 · 8850111000039 没当条码读")
        self.assertEqual(self.r["typed_toast_type"], "error")
        self.assertEqual(self.r["typed_rows"], 1)
        self.assertIn("8850111000039", self.r["typed_row_text"])
        self.assertIn("确实是扫的就再扫一次", self.r["typed_row_text"])

    def test_a_burst_judged_as_typing_is_not_treated_as_a_barcode(self):
        # 反向:这一路不是第二个判据出口。判据只有 looksLikeGun 一份,这里只负责让屏上有字 ——
        # 顺手当条码查就等于把「人在打字」这个结论推翻了,店员填的东西会被当成货加进车。
        self.assertEqual(self.r["typed_calls"], 0, "把判成手打的那一串又拿去查码了")
        self.assertEqual(self.r["typed_cart_delta"], 0)

    # ── 4. 一单结束 ──
    def test_both_kinds_of_debt_are_cleared_when_the_sale_ends(self):
        # 不清 = 上一位客人那两笔顶在下一位客人的屏上,店员照着补一件不属于这单的货。
        self.assertEqual(self.r["sale_end_rows"], 0)


class ToastGlyphContractTest(unittest.TestCase):
    """「没加进购物车」旁边画的那个字形,由三个文件拼出来。

    上面那条 `assertEqual(blocked_toast_type, "error")` 断的是标记挂上了没有,不是店员看见了
    什么 —— 真浏览器实测过一次:红档只换底色不换字形,两句话旁边立着的都是同一枚对勾
    (d="M20 6L9 17l-5-5"),抬头一瞥仍是「办好了」。字形现在挂在 pos.html 的 data-ok/data-err
    上、由 pos.js 挑,谁改一边名字都不会报错:setAttribute('d', undefined) 只是把图标画没了,
    屏上安安静静少一个符号。这道闸就守这条跨文件引用。
    """

    @classmethod
    def setUpClass(cls):
        cls.html = (POS_DIR / "pos.html").read_text(encoding="utf-8")
        cls.js = (POS_DIR / "pos.js").read_text(encoding="utf-8")
        cls.path_tag = re.search(r"<path\b[^>]*id=\"pos-toast-ic\"[^>]*/?>", cls.html, re.S)

    def _attr(self, name: str) -> str:
        self.assertIsNotNone(self.path_tag, "pos.html 里没有 id=pos-toast-ic 的 <path>")
        # 前面钉个空白:属性名 d 是 id 的后缀,不钉就把 id="pos-toast-ic" 当成 d 读回来了
        m = re.search(rf'\s{name}="([^"]+)"', self.path_tag.group(0))
        self.assertIsNotNone(m, f"pos-toast-ic 上没有 {name}")
        return m.group(1)

    def test_both_glyphs_are_declared_and_are_not_the_same_drawing(self):
        ok, err = self._attr("data-ok"), self._attr("data-err")
        self.assertNotEqual(ok, err, "两档画的是同一个字形 · 换了底色也还是那句「办好了」")

    def test_the_glyph_on_first_paint_is_the_success_one(self):
        # toast 没弹过之前 d 就是标记里写死的那条。写成 err 那条 = 页面一打开就挂着个叉。
        self.assertEqual(self._attr("d"), self._attr("data-ok"))

    def test_the_js_reads_exactly_the_two_keys_the_markup_declares(self):
        # dataset.err ←→ data-err · 改名任一边都不报错,只是把图标画没了。
        self.assertRegex(self.js, r"\$\(['\"]pos-toast-ic['\"]\)")
        for key in ("err", "ok"):
            self.assertIn(f"dataset.{key}", self.js, f"pos.js 没读 dataset.{key}")
            self._attr(f"data-{key}")

    def test_the_pick_is_driven_by_the_same_flag_that_paints_the_bar_red(self):
        # 两处各判一次 type==='error' 就会漂:底色红了而字形还是勾,正是本轮实测到的那一幕。
        block = re.search(r"POS\.toast = function[\s\S]{0,900}?\n    \};", self.js)
        self.assertIsNotNone(block, "找不到 POS.toast 的函数体")
        body = block.group(0)
        self.assertEqual(
            len(re.findall(r"type === 'error'", body)),
            1,
            "'type === error' 在 POS.toast 里判了不止一次 · 底色与字形迟早各走各的",
        )
        self.assertRegex(body, r"err \? ic\.dataset\.err : ic\.dataset\.ok")


if __name__ == "__main__":
    unittest.main()
