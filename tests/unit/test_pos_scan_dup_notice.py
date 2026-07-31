#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_scan_dup_notice.py

收银台这一侧怎么消费「引擎把这一次当成同一件挡下了」(scan-camera.js 的 onDuplicate)。

引擎那两把尺子 AND 起来必然有个地板(本仓实测:原生 ~1.6s、店里那台 ZXing ~1.8s、
一次采样 400ms 的老机器 ~5.0s;见 test_scan_camera_runtime.py 的地板用例)。地板以下
把 A 拿开再举同款的 B,引擎认不出那是第二件 —— 于是它把这一次报给收银台,由店员裁决。
本测验的就是这条报法在屏上的样子,判据全取真 DOM(行数 / 行里的字 / 按钮点下去车里多没多):

  1. 报出来的那一行必须真出现在失败清单里,并带一颗能把第二件补进车的「+1」。
  2. 「+1」走的是跟扫码同一条取件路 —— 车里真多一件、这一行跟着销账。
  3. 同一个码反复被挡下只留一行,而且不许把已经在清单上、更该处理的那一条顶掉:
     码没建档时清单上写的是「去后台建品」,被一句「按 +1 加进车」换掉之后,店员按那颗
     +1 只会再吃一次 404,而「这件货要建档」这条唯一的线索没有任何地方还记得。
  4. 报不报是引擎的事,收银台不许自己再判一次门槛 —— 门槛只有一处(引擎的 dupNotice*)。
"""

from __future__ import annotations

import shutil
import unittest

from tests.unit._pos_scan_dom import run as run_scan_harness

DICT_ZH = {
    "posui.bscan.count": "已扫 {n} 件",
    "posui.bscan.done": "完成",
    "posui.bscan.added": "已加入 {name}",
    "posui.bscan.fails_n": "{n} 件没加进购物车",
    "posui.bscan.fails_ack": "知道了",
    "posui.bscan.search_code": "用这个码搜商品",
    "posui.bscan.create_where": "让老板在后台把这个码填进「条码」",
    "posui.bscan.same_code": "同一个码 {code} 又读到一次 · 已按同一件算",
    "posui.bscan.same_code_hint": "如果这是第二件同款货,点「+1」把它加进购物车",
    "posui.bscan.add_one": "+1 · 这是第二件",
    "bscan.notfound": "没有条码 {code} 的商品",
    "bscan.manual": "手动输入条码",
    "posui.retry": "重试",
    "pos.unexpected": "出了点问题",
}

NODE_MAIN = r"""
const COLA = '8850999320014';  // 建了档、能进车的货
const GHOST = '8850111000039'; // 柜台上有、后台没建档的那一件

const COLA_ITEM = {
    id: 'p-cola',
    name: { th: 'โค้ก', en: 'Coke', zh: '可乐', ja: 'コーラ' },
    category_id: 1,
    base_unit: 'ขวด',
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
const OK = { status: 200, body: { ok: true, data: COLA_ITEM } };
const NOT_FOUND = {
    status: 404,
    body: { ok: false, error: { code: 'pos.product_not_found', detail: null } },
};

const failsBox = () => document.getElementById('bscan-fails');
const failRows = () => failsBox().children.slice(1); // 第 0 个是头部
const failsText = () => failsBox().textContent;
function descend(el, out) {
    (el.children || []).forEach((c) => {
        out.push(c);
        descend(c, out);
    });
    return out;
}
function clickInFails(label) {
    const hit = descend(failsBox(), []).find((e) => e.textContent === label);
    if (hit) hit.click();
    return !!hit;
}
const hasBtn = (label) => !!descend(failsBox(), []).find((e) => e.textContent === label);
const cartQtys = () =>
    Array.from(
        String(document.getElementById('cart-lines').innerHTML).matchAll(
            /data-qi="\d+"[^>]*>([^<]*)</g
        )
    ).map((m) => m[1]);

POS.state.online = true;
POS.offline = { hasSnapshot: () => false, filterCached: () => [] };
POS.pay = { inclVat: () => false, settings: () => ({}), applyMethods() {}, refresh() {}, ensure() {} };
const LS = {};
global.localStorage = {
    getItem: (k) => (k in LS ? LS[k] : null),
    setItem: (k, v) => (LS[k] = String(v)),
    removeItem: (k) => delete LS[k],
};
POS.cashier.init();

// 取景层要真开一次,pos-scan.js 才会把回调交给引擎 —— 这一袋正是被测的契约。
CAM_API = camApi(1280, 720);

const R = {};

async function main() {
    await POS.scan.open();
    await settle();
    R.wired = typeof (LAST_CAM_OPTS && LAST_CAM_OPTS.onDuplicate) === 'function';

    // ── 1. 一件可乐真进了车,第二件在地板以下被挡下 ─────────────────────
    NEXT = OK;
    await POS.scan.submit(COLA);
    R.first_qtys = cartQtys().join(',');
    R.rows_before_notice = failRows().length;

    LAST_CAM_OPTS.onDuplicate(COLA, { gapMs: 1200, misses: 9 });
    await settle();
    R.notice_rows = failRows().length;
    R.notice_has_code = failsText().indexOf(COLA) >= 0;
    R.notice_text = failsText();
    R.notice_has_plus = hasBtn(DICT['posui.bscan.add_one']);

    // ── 2. 同一个码反复被挡下(举着不动也会走到这):只留一行 ──────────────
    LAST_CAM_OPTS.onDuplicate(COLA, { gapMs: 900, misses: 7 });
    LAST_CAM_OPTS.onDuplicate(COLA, { gapMs: 1500, misses: 11 });
    await settle();
    R.repeat_rows = failRows().length;

    // ── 3. 那颗「+1」真把第二件补进车,这一行跟着销账 ─────────────────────
    R.plus_clicked = clickInFails(DICT['posui.bscan.add_one']);
    await settle();
    await settle();
    R.after_plus_qtys = cartQtys().join(',');
    R.after_plus_rows = failRows().length;
    R.after_plus_code_gone = failsText().indexOf(COLA) < 0;

    // ── 4. 码没建档时:清单上那条「去建品」不许被一句「按 +1」顶掉 ──────────
    // 这一件从头到尾没进过车,+1 按下去只会再吃一次 404;而「这个码要建档」这条线索
    // 一旦被换掉,屏上、清单上、别处都没有第二个地方还记得它。
    NEXT = NOT_FOUND;
    await POS.scan.submit(GHOST);
    R.ghost_rows = failRows().length;
    R.ghost_says_create = failsText().indexOf(DICT['posui.bscan.create_where']) >= 0;

    LAST_CAM_OPTS.onDuplicate(GHOST, { gapMs: 1300, misses: 10 });
    await settle();
    R.ghost_rows_after = failRows().length;
    R.ghost_still_says_create = failsText().indexOf(DICT['posui.bscan.create_where']) >= 0;
    R.ghost_search_btn = hasBtn(DICT['posui.bscan.search_code']);
    R.ghost_plus_btn = hasBtn(DICT['posui.bscan.add_one']);

    // ── 5. 被挡下那一件的账,不许由后来真记上的那一件替它销掉 ───────────────
    // 连着扫三瓶一样的可乐:第二瓶手快了点被挡下(清单挂上一行),第三瓶手慢了点真记上 ——
    // 那一下若顺手把第二瓶那一行也销了,屏上就跟三瓶全扫上一模一样,而车里只有两瓶。
    NEXT = OK;
    LAST_CAM_OPTS.onDuplicate(COLA, { gapMs: 1200, misses: 9 });
    await settle();
    R.owed_rows = failRows().length;
    R.owed_qtys = cartQtys().join(',');
    await POS.scan.submit(COLA); // 第三瓶:空档够大,引擎真记一件
    await settle();
    await settle();
    R.after_real_hit_qtys = cartQtys().join(',');
    R.after_real_hit_rows = failRows().length;
    R.after_real_hit_keeps_cola = failsText().indexOf(COLA) >= 0;

    process.stdout.write(JSON.stringify(R));
}
main().catch((e) => {
    process.stderr.write(String((e && e.stack) || e));
    process.exit(1);
});
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端链路测试")
class PosScanDupNoticeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = run_scan_harness(NODE_MAIN, DICT_ZH)

    def test_the_camera_layer_really_hands_the_engine_a_duplicate_listener(self):
        # 没接 = 被挡下的那一发在收银台这侧原地消失,屏上跟成功扫码一模一样。
        self.assertTrue(self.r["wired"])

    def test_a_suppressed_second_item_shows_up_on_screen_with_a_way_to_add_it(self):
        self.assertEqual(self.r["first_qtys"], "1")
        self.assertEqual(self.r["rows_before_notice"], 0)
        self.assertEqual(self.r["notice_rows"], 1)
        self.assertTrue(self.r["notice_has_code"], self.r["notice_text"])
        # 只报「读重了」而没有出口,店员除了重扫一遍没别的办法,而重扫大概率又被挡下。
        self.assertTrue(self.r["notice_has_plus"])

    def test_being_suppressed_over_and_over_still_owes_exactly_one_row(self):
        # 举着不动同样走这条路(引擎分不出反光和换货),一次持握摊上三行就是在喊狼来了。
        self.assertEqual(self.r["repeat_rows"], 1)

    def test_pressing_plus_one_really_puts_the_second_item_in_the_cart(self):
        self.assertTrue(self.r["plus_clicked"])
        self.assertEqual(self.r["after_plus_qtys"], "2")
        # 补进车了还挂着这笔欠账,店员照清单再补一次就是收两遍钱(收银侧 resolveFail 的原病)。
        self.assertEqual(self.r["after_plus_rows"], 0)
        self.assertTrue(self.r["after_plus_code_gone"])

    def test_a_later_real_scan_of_the_same_code_does_not_settle_the_owed_one(self):
        # 病灶:resolveFail 按码销账,把「刚才那件可能没进车」当成同一笔债 —— 后来真记上的
        # 那一件替它销了,于是屏上不再有任何痕迹,而柜台上那件货就跟着顾客出门了。
        # 那两件是两件货:第三瓶进车不代表第二瓶进了车。这一行只有店员销得掉。
        self.assertEqual(self.r["owed_rows"], 2)  # 没建档那条 + 这条重读
        self.assertEqual(self.r["owed_qtys"], "2")
        self.assertEqual(self.r["after_real_hit_qtys"], "3")
        self.assertEqual(self.r["after_real_hit_rows"], 2)
        self.assertTrue(self.r["after_real_hit_keeps_cola"])

    def test_a_code_that_never_made_it_into_the_cart_keeps_its_own_reason(self):
        self.assertEqual(self.r["ghost_rows"], 1)
        self.assertTrue(self.r["ghost_says_create"])
        self.assertEqual(self.r["ghost_rows_after"], 1)
        # 病灶:重读提示把「去后台建品」整条换成「按 +1 加进车」——
        # 那颗 +1 走的是同一条取件路,按下去只会再吃一次 404。
        self.assertTrue(self.r["ghost_still_says_create"])
        self.assertTrue(self.r["ghost_search_btn"])
        self.assertFalse(self.r["ghost_plus_btn"])
