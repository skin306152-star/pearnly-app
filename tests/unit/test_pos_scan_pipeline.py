#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_pos_scan_pipeline.py

收银台扫码取件(static/pos/pos-scan.js + pos-data.js 的 by-barcode 层 + pos-cashier.js 的加货)
守门。真 node 子进程加载三个源文件 + 一套最小 DOM 桩,跑完整链路再断结果 —— 不是断源码里有没有
某个字符串(那种断言 grep 一下就"绿"了,产品里可能什么都没发生)。

钉死店里真会出事的几条:
  1. 条码精确等值匹配:前缀/子串绝不算命中(扫 12 位前缀命中 13 位的货 = 收错钱)。
  2. matched_unit 落到价上:同一商品扫瓶码按瓶价、扫箱码按箱价,断的是购物车小计。
  3. 未命中把扫到的码显示出来 + 指路怎么建品(店员才知道是码印错了还是货没建档)。
  4. 离线不冒充「没建档」:查过快照没有 / 连快照都没有,两句话不同,都不说成没这个货。
  5. 相机用不了时不静默隐藏入口(Odoo 的病):先说清原因,再把手输弹窗摆上来。
  6. 条码枪只在收银主屏且没有弹窗开着时才加货;摄像头层开着时它独占,不会一件货加两次。
  7. 串行化不丢码:后端还没回来时进来的码排队,一件都不许少(枪比后端快是常态)。
  8. 加不进车必须出声:单位没设价不许按 ฿0 加,扫中的单位不在资料里不许静默换单位。
  9. 取景框 = 真被解码的那块:框按画面盒子 × 引擎 cropRatio() 算,框不许越出画面。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from decimal import Decimal
from pathlib import Path

from services.pos import catalog as pos_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POS_DIR = PROJECT_ROOT / "static" / "pos"
SCAN_DIR = PROJECT_ROOT / "static" / "scan"
LANGS = ("th", "en", "zh", "ja")

# 桩字典只放本测断言要用到的键(真字典的 4 语完整性归 test_pos_spa_i18n.py 那道闸)。
DICT_ZH = {
    "posui.bscan.count": "已扫 {n} 件",
    "posui.bscan.done": "完成",
    "posui.bscan.added": "已加入 {name}",
    "posui.bscan.fails_n": "{n} 件没加进购物车",
    "posui.bscan.fails_ack": "知道了",
    "posui.bscan.search_code": "用这个码搜商品",
    "posui.bscan.create_where": "让老板在后台把这个码填进「条码」",
    "posui.bscan.offline_miss": "离线 · 本机目录里没有 {code}",
    "posui.bscan.offline_nocatalog": "离线 · 这台设备还没有商品目录",
    "posui.bscan.queued": "还有 {n} 件在排队",
    "posui.cart.unit_no_price": "「{unit}」这个单位还没设售价 · {name} 没加进购物车",
    "posui.cart.unit_unknown": "扫到的码对应单位「{unit}」,但 {name} 的商品资料里没有这个单位",
    "posui.cart.fix_in_backoffice": "让老板在后台核对这个商品的单位",
    "bscan.notfound": "没有条码 {code} 的商品",
    "bscan.manual": "手动输入条码",
    "bscan.err.unsupported": "这台设备用不了应用内相机",
    "posui.retry": "重试",
    "pos.unexpected": "出了点问题",
}

NODE_HARNESS = r"""
const fs = require('fs');
const dir = process.argv[1];
const DICT = JSON.parse(process.argv[2]);
const scanDir = process.argv[3];

// ── 最小 DOM 桩:只做被测代码真正用到的那几样 ──────────────────────────
function mkEl(tag) {
    const el = {
        tagName: (tag || 'div').toUpperCase(),
        children: [],
        style: {},
        dataset: {},
        value: '',
        className: '',
        innerHTML: '',
        disabled: false,
        _text: '',
        _cls: new Set(),
        _on: {},
        get firstChild() {
            return this.children.length ? this.children[0] : null;
        },
        appendChild(c) {
            this.children.push(c);
            return c;
        },
        removeChild(c) {
            const i = this.children.indexOf(c);
            if (i >= 0) this.children.splice(i, 1);
            return c;
        },
        set textContent(v) {
            this._text = String(v);
            this.children = [];
        },
        get textContent() {
            if (this.children.length) return this.children.map((c) => c.textContent).join('');
            return this._text;
        },
        addEventListener(t, f) {
            (this._on[t] = this._on[t] || []).push(f);
        },
        // 真引擎(static/scan/scan-camera.js)建 video/canvas 时会用到这两样;node 里没有
        // 布局与画布,给最小实现即可 —— 本测不验解码,只验取景框算得对不对。
        setAttribute(n, v) {
            this[n] = v;
        },
        getContext() {
            return { drawImage() {} };
        },
        clientWidth: 0,
        clientHeight: 0,
        click() {
            (this._on.click || []).forEach((f) => f({ currentTarget: this }));
        },
        querySelectorAll() {
            return [];
        },
        closest() {
            return null;
        },
    };
    el.classList = {
        add: (c) => el._cls.add(c),
        remove: (c) => el._cls.delete(c),
        contains: (c) => el._cls.has(c),
        toggle: (c, on) => {
            const want = on === undefined ? !el._cls.has(c) : !!on;
            if (want) el._cls.add(c);
            else el._cls.delete(c);
            return want;
        },
    };
    return el;
}

const byId = {};
let QS_ONE = {}; // document.querySelector(选择器) → 元素 / null
global.document = {
    readyState: 'complete',
    getElementById: (id) => (byId[id] = byId[id] || mkEl('div')),
    createElement: (tag) => mkEl(tag),
    createTextNode: (t) => ({ textContent: String(t) }),
    querySelector: (sel) => QS_ONE[sel] || null,
    querySelectorAll: () => [],
    addEventListener: () => {},
    body: mkEl('body'),
};
const win = { addEventListener: () => {} };
global.window = win;
win.POS_I18N = { zh: DICT };

// 扫码地基桩:摄像头那层在 node 里没有可测的东西(真浏览器验收归 scan_base),这里只需要
// 「能不能开」的答复 + 记下楔子是怎么被订阅的。
let UNSUPPORTED = null;
let CAM_API = null; // 非空 = 解码器"拉下来了";默认 null → 走「解码器拉不下来」那张卡
const wedgeSubs = [];
win.PearnlyScanCamera = {
    unsupportedReason: () => UNSUPPORTED,
    ensureLoaded: () =>
        CAM_API
            ? Promise.resolve(CAM_API)
            : Promise.reject(new Error('camera layer not loaded in node')),
};

// 摄像头引擎用真的(static/scan/scan-camera.js):取景框比例必须来自真产物 —— 在测里自己写
// 一个 0.9/0.5 的桩等于拿桩验桩,引擎改了比例这条闸照样绿。引擎挂 globalThis(它自己找
// self/globalThis),与上面那份 win.PearnlyScanCamera 分开:后者是「解码器拉没拉下来」的开关。
global.PearnlyScanCamera = {
    loadScript: () => Promise.resolve(),
    unsupportedReason: () => null,
};
(0, eval)(fs.readFileSync(scanDir + '/scan-camera.js', 'utf8'));
const ENGINE = global.PearnlyScanCamera;

// 真 create() 建真 handle(真 cropRatio、真 video 元素),只把 start() 换成「直接报出帧」:
// 相机开不开得起来在 node 里不可验,那条归真浏览器验收(scripts/_pos_scan_accept.cjs)。
let LAST_CAM = null; // 真 handle · 取景框的期望值只许从它的 cropRatio() 反查
function camApi(videoW, videoH) {
    return {
        create(opts) {
            const h = ENGINE.create(opts);
            h.video.videoWidth = videoW;
            h.video.videoHeight = videoH;
            LAST_CAM = h;
            return Object.assign({}, h, {
                start() {
                    opts.onState('starting');
                    opts.onState('scanning');
                    return Promise.resolve(true);
                },
            });
        },
    };
}
win.PearnlyScanWedge = {
    MIN_LENGTH: 3,
    register(cb, opts) {
        const entry = { cb, exclusive: !!(opts && opts.exclusive) };
        wedgeSubs.push(entry);
        return () => {
            const i = wedgeSubs.indexOf(entry);
            if (i >= 0) wedgeSubs.splice(i, 1);
        };
    },
};
// 楔子的真实语义:有 exclusive 订阅者时只有它收(scan-wedge.js 的 receivers())。
// 页面级订阅者不把取件的 promise 传回来(生产里没人 await 它),所以扫完要让在飞的活落地
// 再断状态 —— 真实时间线上两次扫码本来也不在同一毫秒。
function gunScan(code) {
    let last = null;
    wedgeSubs.forEach((s) => {
        if (s.exclusive) last = s;
    });
    const targets = last ? [last] : wedgeSubs.slice();
    return Promise.all(targets.map((s) => s.cb(code, document.body))).then(settle);
}
function settle() {
    return new Promise((r) => setTimeout(r, 0));
}

// ── 网络桩 ────────────────────────────────────────────────────────────
let LAST_URL = null;
let CALLS = 0;
let NEXT = null; // {status, body} 或 'network'
let BY_CODE = null; // code → {status, body}(连扫多个不同码时按码回不同商品)
let DELAY = 0; // 后端往返耗时(ms)· 连扫要复现的正是「上一件还没回来」
global.fetch = (url) => {
    LAST_URL = url;
    CALLS += 1;
    if (NEXT === 'network') return Promise.reject(new Error('offline'));
    const m = String(url).match(/[?&]code=([^&]*)/);
    const ans = (BY_CODE && BY_CODE[m ? decodeURIComponent(m[1]) : '']) || NEXT;
    return new Promise((r) =>
        setTimeout(() => r({ status: ans.status, json: () => Promise.resolve(ans.body) }), DELAY)
    );
};

function load(name) {
    (0, eval)(fs.readFileSync(dir + '/' + name, 'utf8'));
}
load('pos-data.js');
const POS = win.POS;
POS.state.lang = 'zh';
POS.state.workspaceClientId = 7; // 真租户(不是纯本地预览 → 不走 mock 目录)
const toasts = [];
POS.toast = (msg, type) => toasts.push({ msg: msg, type: type || '' });
load('pos-cashier.js');
load('pos-scan.js');

// ── 语料:同一商品两个单位两个码(瓶 15 / 箱 350)──────────────────────
function coke() {
    return {
        id: 'p1',
        name: { th: 'โค้ก 325ml', en: 'Coke 325ml', zh: '可乐 325ml', ja: 'コーラ' },
        category_id: 1,
        base_unit: 'ขวด',
        image_url: null,
        vat_applicable: true,
        units: [
            {
                unit_name: 'ขวด',
                factor: '1.000',
                barcode: '8851959131013',
                price: '15.00',
                default_sell: true,
            },
            {
                unit_name: 'ลัง',
                factor: '24.000',
                barcode: '18851959131010',
                price: '350.00',
                default_sell: false,
            },
        ],
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '48.000', near_expiry: false },
    };
}
const BOTTLE = '8851959131013';
const BOX = '18851959131010';

// 连扫要的是三件不同的货:同一个码扫两次本来就该加两件,证不出「第二个码没被丢掉」。
function oneUnit(id, name, unitName, barcode, price) {
    return {
        id: id,
        name: { th: name, en: name, zh: name, ja: name },
        category_id: 1,
        base_unit: unitName,
        image_url: null,
        vat_applicable: true,
        units: [
            {
                unit_name: unitName,
                factor: '1.000',
                barcode: barcode,
                price: price,
                default_sell: true,
            },
        ],
        track_batch: false,
        is_weighed: false,
        stock: { qty_base: '10.000', near_expiry: false },
    };
}
const WATER = '8850999320013';
const BREAD = '8853474091201';
const MILK = '8851234567895';
const MASTER = '8858888100022'; // 商品主码(products.barcode)· 不在任何 units[].barcode 上
const MASTER2 = '8858888100039';
const water = () => Object.assign(oneUnit('p2', 'น้ำเปล่า', 'ขวด', WATER, '10.00'), {
    matched_unit: 'ขวด',
});
const bread = () => Object.assign(oneUnit('p3', 'ขนมปัง', 'ถุง', BREAD, '25.00'), {
    matched_unit: 'ถุง',
});
const milk = () => Object.assign(oneUnit('p5', 'นมจืด', 'กล่อง', MILK, '18.00'), {
    matched_unit: 'กล่อง',
});
// 只建了「箱」一条单位行的商品:主码印在瓶上 → 后端靠 products.barcode 命中,
// matched_unit 回的是基本单位「ขวด」,而 units 里根本没有这一行。
function boxOnly() {
    const p = oneUnit('p4', 'โค้กยกลัง', 'ลัง', BOX, '350.00');
    p.base_unit = 'ขวด';
    p.barcode = MASTER;
    return p;
}
// 同款建档,但基本单位挂了牌价(products.unit_price → 载荷里的 base_price)。后端本来就认
// base_unit(services/pos/sale.py 的 _resolve_unit),缺的只是这一行下发。
function boxOnlyPriced() {
    const p = boxOnly();
    p.id = 'p9';
    p.base_price = '15.00';
    return p;
}
// 主码印在包装上、单位行的条码栏空着(店里最常见的一种建档法)。离线快照下发时主码只在
// products.barcode 上 —— 「主码以 units[0].barcode 下发」只在一条单位行都没有时才成立。
function snack() {
    const p = oneUnit('p6', 'ขนมถุง', 'ถุง', '', '20.00');
    p.barcode = MASTER2;
    return p;
}
// 加「ลัง」只为库存换算(24 瓶一箱),售价栏空着。另起一个商品而不是复用可乐:车里已经有
// 一行可乐箱,复用的话 ฿0 会并进那一行,证不出「฿0 的整箱货新进了车」。
function unpricedBox() {
    const p = coke();
    p.id = 'p7';
    p.name = { th: 'เป๊ปซี่ 325ml', en: 'Pepsi 325ml', zh: '百事 325ml', ja: 'ペプシ' };
    p.units[1].price = null;
    p.matched_unit = 'ลัง';
    return p;
}

let SNAP = [];
let SNAP_ON = false;
POS.offline = {
    hasSnapshot: () => SNAP_ON,
    filterCached: (q, cat) => POS.filterCatalog(SNAP, q, cat),
};

const card = () => document.getElementById('bscan-card');
const mask = () => document.getElementById('bscan-mask');
const acts = () => document.getElementById('bscan-acts').children.map((b) => b.textContent);

// 失败清单(累积)· 头部一行 + 每件失败一行。
const failsBox = () => document.getElementById('bscan-fails');
const failsShown = () => failsBox().classList.contains('show');
const failsText = () => failsBox().textContent;
const failRows = () => failsBox().children.slice(1); // 第 0 个是「N 件没加进购物车 / 知道了」头部
function descend(el, out) {
    (el.children || []).forEach((c) => {
        out.push(c);
        descend(c, out);
    });
    return out;
}
// 清单里的按钮按它显示的字找(文案从桩字典取,不在测里另写一份)。找不到时回 false 而不是
// 抛错:清单被抹掉正是要验的病灶,让 setUpClass 崩掉会把 39 条断言一起变成一坨 ERROR,
// 看不出到底哪一条判据失守。
function clickInFails(label) {
    const hit = descend(failsBox(), []).find((e) => e.textContent === label);
    if (hit) hit.click();
    return !!hit;
}
function cartTotals() {
    return {
        subtotal: document.getElementById('cart-subtotal').textContent,
        grand: document.getElementById('cart-grand').textContent,
        items: document.getElementById('cart-sub').textContent,
    };
}
// 购物车是累加的(测里不清空:clearCart 不对外),按小计增量断"这一扫加了多少钱"。
function subtotal() {
    return Number(cartTotals().subtotal.replace(/,/g, ''));
}
// 车里每一行的商品名(renderCart 的真产物)· 连扫要断的是「三件都在,且顺序等于扫的顺序」。
function cartNames() {
    const html = document.getElementById('cart-lines').innerHTML;
    return Array.from(String(html).matchAll(/class="n">([^<]*)</g)).map((m) => m[1]);
}
function envelope(data) {
    return { status: 200, body: { ok: true, data: data } };
}
function failure(code, detail) {
    return { status: 404, body: { ok: false, error: { code: code, detail: detail || null } } };
}

const R = {};

async function main() {
    // ── 1. 纯匹配语义 ────────────────────────────────────────────────
    const snapshot = [coke()];
    R.match_bottle = POS.matchBarcode(snapshot, BOTTLE).matched_unit;
    R.match_box = POS.matchBarcode(snapshot, BOX).matched_unit;
    R.match_prefix = POS.matchBarcode(snapshot, BOTTLE.slice(0, 12));
    R.match_empty = POS.matchBarcode(snapshot, '');
    R.match_pads_nothing = snapshot[0].matched_unit === undefined;

    // ── 2. 在线命中:扫瓶码 = 瓶价,扫箱码 = 箱价(同一商品)────────────
    POS.state.online = true;
    NEXT = envelope(Object.assign(coke(), { matched_unit: 'ขวด' }));
    await POS.scan.submit(BOTTLE);
    R.url = LAST_URL;
    R.bottle_adds = subtotal();
    R.after_bottle = cartTotals();

    NEXT = envelope(Object.assign(coke(), { matched_unit: 'ลัง' }));
    await POS.scan.submit(BOX);
    R.box_adds = subtotal() - R.bottle_adds;
    R.after_box = cartTotals();
    R.count_text_no_layer = document.getElementById('bscan-count').textContent;
    R.hit_toast = toasts.length ? toasts[toasts.length - 1].msg : null;

    // ── 3. 串行化不丢码:三件不同的货在上一件查回来之前连着进来 ────────
    // 枪扫一件不到 100ms,后端往返 300ms~1s+ —— 后两件必然落在「上一件还在飞」的窗口里。
    // 布尔互斥在这里直接 return:零 toast 零卡片,顾客付一件的钱拿走三件。
    const before = CALLS;
    const beforeBurst = subtotal();
    const linesBeforeBurst = cartNames().length;
    BY_CODE = {};
    BY_CODE[WATER] = envelope(water());
    BY_CODE[BREAD] = envelope(bread());
    BY_CODE[MILK] = envelope(milk());
    DELAY = 30;
    toasts.length = 0;
    await Promise.all([
        POS.scan.submit(WATER),
        POS.scan.submit(BREAD),
        POS.scan.submit(MILK),
    ]);
    DELAY = 0;
    BY_CODE = null;
    R.burst_calls = CALLS - before;
    R.burst_adds = subtotal() - beforeBurst;
    R.burst_lines = cartNames().slice(linesBeforeBurst);
    R.burst_toasts = toasts.map((t) => t.msg);

    // ── 3b. 队列里非最后一件失败:那件的提示不许被下一件抹掉 ────────────
    // 敌意输入:五个码一齐进来,没建档的那个排第 3(不是最后),后面还有两件会命中。
    // 「三个码全命中」或「失败排最后」都复现不出这条 —— 提示是被"下一件"抹掉的,
    // 没有下一件就什么也不会发生,旧代码在那两种输入下照样绿。
    const Q1 = '8850111000015';
    const Q2 = '8850111000022';
    const GHOST = '8850111000039'; // 柜台上有货、后台没建档的那一件
    const Q3 = '8850111000046';
    const Q4 = '8850111000053';
    const mk = (id, name, unit, code, price) =>
        Object.assign(oneUnit(id, name, unit, code, price), { matched_unit: unit });
    const beforeMid = subtotal();
    const linesBeforeMid = cartNames().length;
    BY_CODE = {};
    BY_CODE[Q1] = envelope(mk('p10', 'สบู่', 'ก้อน', Q1, '32.00'));
    BY_CODE[Q2] = envelope(mk('p11', 'ยาสีฟัน', 'หลอด', Q2, '45.00'));
    BY_CODE[GHOST] = failure('pos.product_not_found');
    BY_CODE[Q3] = envelope(mk('p12', 'ผงซักฟอก', 'ถุง', Q3, '59.00'));
    BY_CODE[Q4] = envelope(mk('p13', 'ทิชชู่', 'ห่อ', Q4, '25.00'));
    DELAY = 30;
    await Promise.all([Q1, Q2, GHOST, Q3, Q4].map((c) => POS.scan.submit(c)));
    DELAY = 0;
    BY_CODE = null;
    R.mid_adds = subtotal() - beforeMid;
    R.mid_new_lines = cartNames().length - linesBeforeMid;
    R.mid_fail_shown = failsShown();
    R.mid_fail_text = failsText();
    R.mid_fail_rows = failRows().length;
    // 店员按「完成」离开取景层后,那件失败仍得在屏上(他正要拿这个码去后台建品)
    POS.scan.close();
    R.mid_fail_after_close = failsShown();
    R.mid_ack_found = clickInFails(DICT['posui.bscan.fails_ack']);
    R.mid_fail_after_ack = failsShown();

    // ── 4. 未命中(后端说没有这个条码)───────────────────────────────
    NEXT = failure('pos.product_not_found');
    await POS.scan.submit('9999999999999');
    R.notfound_text = failsText();
    R.notfound_shown = failsShown();
    R.notfound_rows = failRows().length;
    // 「用这个码搜商品」真把码填进搜索框(已建档但没录条码的货靠这条救回来)
    R.search_btn_found = clickInFails(DICT['posui.bscan.search_code']);
    R.search_box_value = document.getElementById('main-search').value;
    R.closed_after_search = mask().classList.contains('show');
    R.fails_cleared_after_search = failsShown();

    // ── 5. 离线:有快照 → 不打网络也能取件 ───────────────────────────
    POS.state.online = false;
    SNAP = [coke()];
    SNAP_ON = true;
    const callsBeforeOffline = CALLS;
    const beforeOfflineSub = subtotal();
    await POS.scan.submit(BOX);
    R.offline_calls = CALLS - callsBeforeOffline;
    R.offline_box_adds = subtotal() - beforeOfflineSub;

    // ── 6. 离线且快照里没有这个码 → 说「查不了」不说「没建档」───────────
    await POS.scan.submit('7777777777777');
    R.offline_miss_msg = failsText();

    // ── 7. 离线且这台机器还没有目录 ──────────────────────────────────
    // 上一件的失败还在清单上时又扫一下:第二条追加,第一条不许被顶掉。
    SNAP_ON = false;
    await POS.scan.submit('6666666666666');
    R.offline_nocatalog_text = failsText();
    R.two_misses_stack = failRows().length;

    // ── 7b. 清单撑着时扫中了下一件:命中不许把上一件的失败抹掉 ─────────
    POS.state.online = true;
    NEXT = envelope(Object.assign(coke(), { matched_unit: 'ขวด' }));
    toasts.length = 0;
    await POS.scan.submit(BOTTLE);
    R.hit_keeps_fails = failRows().length;
    R.hit_after_card_toast = toasts.length ? toasts[0].msg : null;

    // ── 8. 相机用不了:说清原因 + 手输摆上来,入口不静默消失 ──────────
    clickInFails(DICT['posui.bscan.fails_ack']);
    POS.scan.close();
    UNSUPPORTED = 'no_camera_api';
    toasts.length = 0;
    await POS.scan.open();
    R.unsupported_note = document.getElementById('pad-label').textContent;
    R.unsupported_toasts = toasts.length;
    R.manual_pad_open = document.getElementById('pad-mask').classList.contains('show');
    R.overlay_not_forced = mask().classList.contains('show');
    UNSUPPORTED = null;

    // ── 9. 条码枪:只在收银主屏、没有弹窗开着时才加货 ─────────────────
    POS.state.online = true;
    POS.scan.close();
    const mainView = document.getElementById('view-main');
    NEXT = envelope(Object.assign(coke(), { matched_unit: 'ขวด' }));

    mainView.classList.remove('is-active');
    let c0 = CALLS;
    await gunScan(BOTTLE);
    R.gun_off_main = CALLS - c0;

    mainView.classList.add('is-active');
    QS_ONE['#view-main .mask.show'] = mkEl('div'); // 收款弹窗开着
    c0 = CALLS;
    await gunScan(BOTTLE);
    R.gun_with_modal = CALLS - c0;

    QS_ONE = {};
    c0 = CALLS;
    await gunScan(BOTTLE);
    R.gun_on_main = CALLS - c0;

    // ── 10. 摄像头层开着时楔子独占:枪扫一下只加一件 ──────────────────
    UNSUPPORTED = null;
    await POS.scan.open(); // ensureLoaded 在 node 里必然失败 → 停在解码器错误卡,层已开着
    R.open_registers_exclusive = wedgeSubs.some((s) => s.exclusive);
    R.done_label = document.getElementById('bscan-done').textContent;
    R.decoder_card_msg = document.getElementById('bscan-card-msg').textContent;
    R.decoder_acts = acts();
    c0 = CALLS;
    await gunScan(BOTTLE);
    R.gun_while_overlay = CALLS - c0;
    // 层开着时的反馈落在层里:件数条 + 最后一件(不是身后看不见的 toast)
    R.count_text_in_layer = document.getElementById('bscan-count').textContent;
    R.last_line_in_layer = document.getElementById('bscan-last').textContent;
    POS.scan.close();
    R.exclusive_gone_after_close = wedgeSubs.some((s) => s.exclusive);

    // ── 11. 加不进车必须出声(两条静默的钱错)────────────────────────
    // 11a 单位没设价:Number(null) 是 0 → 整箱 ฿0.00 进车、฿0 出门。后端 SaleLine 允许 0、
    // 改价闸也不拦,小票和报表上一样看不出异常 —— 只有店员当场被拦住才救得回来。
    POS.state.online = true;
    const noPrice = unpricedBox();
    NEXT = envelope(noPrice);
    const beforeZero = subtotal();
    const linesBeforeZero = cartNames().length;
    await POS.scan.submit(BOX);
    R.zero_price_adds = subtotal() - beforeZero;
    R.zero_price_new_lines = cartNames().length - linesBeforeZero;
    R.zero_price_text = failsText();
    R.zero_price_shown = failsShown();

    // 11b 扫中的单位不在商品资料里:后端靠 products.barcode 命中时把 matched_unit 填成基本
    // 单位,而这个商品只建了「箱」一条 unit 行 → 静默回落默认单位 = 一瓶收一箱 ฿350 的钱,
    // 库存还按箱扣 24 瓶,屏上一个字都没有。
    POS.scan.close();
    NEXT = envelope(Object.assign(boxOnly(), { matched_unit: 'ขวด' }));
    const beforeSwap = subtotal();
    const linesBeforeSwap = cartNames().length;
    await POS.scan.submit(MASTER);
    R.unit_swap_adds = subtotal() - beforeSwap;
    R.unit_swap_new_lines = cartNames().length - linesBeforeSwap;
    R.unit_swap_text = failsText();
    POS.scan.close();

    // 11d P1-H「找不到 matched_unit 就拒收」修过头的那一面:base_unit=ขวด 的货另建了 ลัง 单位行
    // → 扫主码被拒 = 这瓶水在收银台卖不出去(收银台只能改数量)。基本单位挂了牌价就按它卖。
    clickInFails(DICT['posui.bscan.fails_ack']);
    const beforeBase = subtotal();
    const linesBeforeBase = cartNames().length;
    BY_CODE = {};
    BY_CODE[MASTER] = envelope(Object.assign(boxOnlyPriced(), { matched_unit: 'ขวด' }));
    BY_CODE[BOX] = envelope(Object.assign(boxOnlyPriced(), { matched_unit: 'ลัง' }));
    await POS.scan.submit(MASTER);
    R.base_unit_adds = subtotal() - beforeBase;
    R.base_unit_new_lines = cartNames().length - linesBeforeBase;
    R.base_unit_fails = failRows().length;
    // 同一件货紧接着扫箱码:落成两行才证明上一扫真挂在「瓶」上。并成一行 = 悄悄按箱卖了,
    // 而按箱卖的库存要扣 24 瓶 —— 只看小计涨了多少证不出单位。
    await POS.scan.submit(BOX);
    R.base_then_box_adds = subtotal() - beforeBase;
    R.base_then_box_lines = cartNames().length - linesBeforeBase;
    BY_CODE = null;

    // 11c 网格点选那条路吃的是同一个返回值(那条路的 DOM 在 node 里立不起来,
    // 真浏览器那侧归 scripts/_pos_scan_accept.cjs)。回 null = 加进去了,不许骗调用方。
    const beforeDirect = subtotal();
    R.refuse_no_price = POS.cashier.addToCart(noPrice);
    R.refuse_unknown = POS.cashier.addToCart(Object.assign(boxOnly(), { matched_unit: 'ขวด' }));
    R.refuse_ok = POS.cashier.addToCart(water());
    R.direct_adds = subtotal() - beforeDirect;

    // ── 12. 取景框 = 真被解码的那块像素 ────────────────────────────────
    // 预览按 object-fit: contain 缩进舞台:390×772 的屏配 640×480 的摄像头,画面实占 390×292.5,
    // 舞台底下那 479px 是黑边。框按舞台画会算出 386px 高 —— 越出画面,而店员以为框住的就是
    // 要卖的那件货。参照系差这一层,紧挨着的另一件货被解出来直接进购物车。
    UNSUPPORTED = null;
    CAM_API = camApi(640, 480);
    const stage = document.getElementById('bscan-stage');
    stage.clientWidth = 390;
    stage.clientHeight = 772;
    await POS.scan.open();
    R.crop = LAST_CAM.cropRatio();
    R.frame_w = document.getElementById('bscan-frame').style.width;
    R.frame_h = document.getElementById('bscan-frame').style.height;
    R.frame_live = document.getElementById('bscan-frame').classList.contains('live');
    POS.scan.close();
    CAM_API = null;

    // ── 13. 离线扫商品主码 ────────────────────────────────────────────
    // 「主码以 units[0].barcode 下发」只在这个商品一条 product_units 行都没有时才成立。
    // 有单位行、而条码栏空着(店里最常见)时主码只在 products.barcode 上:只比 units 就会
    // 把一件明明在本机目录里的货说成「查过了没有」。
    POS.state.online = false;
    SNAP = [snack()];
    SNAP_ON = true;
    R.master_match = (POS.matchBarcode(SNAP, MASTER2) || {}).matched_unit || null;
    R.master_filter = POS.filterCatalog(SNAP, MASTER2, null).length;
    const beforeMaster = subtotal();
    const callsBeforeMaster = CALLS;
    const failsBeforeMaster = failRows().length; // 只算这一扫自己记了几笔(清单是累积的)
    await POS.scan.submit(MASTER2);
    R.master_adds = subtotal() - beforeMaster;
    R.master_calls = CALLS - callsBeforeMaster;
    R.master_fails = failRows().length - failsBeforeMaster;
    POS.scan.close();

    process.stdout.write(JSON.stringify(R));
}
main().catch((e) => {
    process.stderr.write(String((e && e.stack) || e));
    process.exit(1);
});
"""


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端链路测试")
class PosScanPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc = subprocess.run(
            ["node", "-e", NODE_HARNESS, "--", str(POS_DIR), json.dumps(DICT_ZH), str(SCAN_DIR)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            timeout=60,
        )
        if proc.returncode != 0:
            raise AssertionError("node 跑挂了:\n" + proc.stderr.decode("utf-8", "replace"))
        cls.r = json.loads(proc.stdout.decode("utf-8"))

    # ── 1. 精确等值匹配 ──
    def test_unit_barcode_wins_over_product_barcode(self):
        self.assertEqual(self.r["match_bottle"], "ขวด")
        self.assertEqual(self.r["match_box"], "ลัง")

    def test_prefix_is_not_a_hit(self):
        # 包含匹配会让 12 位前缀命中 13 位的货 → 卖错商品收错钱,比查不到糟得多。
        self.assertIsNone(self.r["match_prefix"])

    def test_empty_code_is_not_a_hit(self):
        self.assertIsNone(self.r["match_empty"])

    def test_match_does_not_mutate_the_cached_catalog(self):
        # 连扫会反复查同一份快照;往里写 matched_unit 会让下一次扫别的码读到上一次的单位。
        self.assertTrue(self.r["match_pads_nothing"])

    # ── 2. matched_unit 落到价上 ──
    def test_lookup_calls_the_exact_barcode_endpoint(self):
        self.assertIn("/api/pos/products/by-barcode", self.r["url"])
        self.assertIn("code=8851959131013", self.r["url"])
        self.assertNotIn("q=", self.r["url"], "别退回模糊搜那条口")

    def test_bottle_code_adds_bottle_price(self):
        self.assertEqual(self.r["bottle_adds"], 15.0)

    def test_box_code_adds_box_price_not_bottle_price(self):
        # 同一个商品,扫箱码就得按箱价进车;按默认售卖单位算 = 一箱货收一瓶的钱。
        self.assertEqual(self.r["box_adds"], 350.0)
        self.assertEqual(self.r["after_box"]["subtotal"], "365.00")
        self.assertEqual(self.r["after_box"]["grand"], "365.00")

    def test_added_feedback_is_a_toast_when_the_camera_layer_is_closed(self):
        # 枪/手输那条路上取景层没开:反馈必须是 toast,且不去画层里的件数条(那时它看不见)。
        self.assertIn("可乐 325ml", self.r["hit_toast"])
        self.assertEqual(self.r["count_text_no_layer"], "")

    def test_added_feedback_lands_inside_the_camera_layer(self):
        self.assertEqual(self.r["count_text_in_layer"], "已扫 1 件")
        self.assertIn("可乐 325ml", self.r["last_line_in_layer"])

    # ── 3. 串行化不丢码 ──
    def test_burst_of_three_different_codes_all_land(self):
        # 布尔互斥版在这里只会打一次后端、只加一件:第二三件零反馈地消失,
        # 顾客付一件的钱拿走三件。队列版一件不许少。
        self.assertEqual(self.r["burst_calls"], 3)
        self.assertEqual(self.r["burst_adds"], 53.0)  # 10 + 25 + 18

    def test_burst_lands_in_scan_order(self):
        self.assertEqual(self.r["burst_lines"], ["น้ำเปล่า", "ขนมปัง", "นมจืด"])

    def test_backlog_is_visible_while_the_queue_drains(self):
        # 看不到「还有几件在排队」的店员会当成没扫上,同一件再扫一遍 —— 那就是多收钱。
        tpl = DICT_ZH["posui.bscan.queued"]
        self.assertIn(tpl.replace("{n}", "1"), self.r["burst_toasts"])
        self.assertIn(tpl.replace("{n}", "2"), self.r["burst_toasts"])

    # ── 3b. 队列中间那件失败的提示不许被下一件抹掉 ──
    def test_a_failure_in_the_middle_of_the_burst_survives_the_rest(self):
        # 五件一齐进来、没建档的排第 3:后面两件命中之后,那件失败仍要在屏上。
        # 旧版 lookup() 第一句就是 dropCard(),第 4 件几个 microtask 后就把它抹了 ——
        # 车里四行钱、toast 四条「已加入」,顾客第三件货没进账而店员零提示。
        self.assertEqual(self.r["mid_adds"], 161.0)  # 32 + 45 + 59 + 25(失败那件不进车)
        self.assertEqual(self.r["mid_new_lines"], 4)
        self.assertTrue(self.r["mid_fail_shown"], "队列中间那件的失败提示被后面的货抹掉了")
        self.assertEqual(self.r["mid_fail_rows"], 1)
        self.assertIn("8850111000039", self.r["mid_fail_text"], "看不到是哪个码 = 没法补救")
        self.assertIn("1", self.r["mid_fail_text"])

    def test_failure_list_outlives_the_camera_layer_and_only_the_clerk_clears_it(self):
        # 按「完成」离开取景层正是店员要拿这个码去后台建品的时候,提示不能跟着层一起消失。
        self.assertTrue(self.r["mid_fail_after_close"])
        self.assertTrue(self.r["mid_ack_found"], "清单上没有「知道了」= 店员没法把它收掉")
        self.assertFalse(self.r["mid_fail_after_ack"], "点了「知道了」还挂着 = 清不掉的横幅")

    # ── 4. 未命中 ──
    def test_notfound_shows_the_scanned_code(self):
        self.assertIn("9999999999999", self.r["notfound_text"])
        self.assertTrue(self.r["notfound_shown"])
        self.assertEqual(self.r["notfound_rows"], 1)

    def test_notfound_tells_where_to_create_the_product(self):
        self.assertIn(DICT_ZH["posui.bscan.create_where"], self.r["notfound_text"])

    def test_search_action_fills_the_search_box_and_clears_the_list(self):
        self.assertTrue(self.r["search_btn_found"], "未命中那行没有「用这个码搜商品」= 死胡同")
        self.assertEqual(self.r["search_box_value"], "9999999999999")
        self.assertFalse(self.r["closed_after_search"])
        # 这一件已经被带去搜索框处理了,留在清单上只会让店员以为还有一件没管。
        self.assertFalse(self.r["fails_cleared_after_search"])

    # ── 5/6/7. 离线诚实 ──
    def test_offline_hit_uses_local_catalog_without_network(self):
        self.assertEqual(self.r["offline_calls"], 0)
        # 离线也得认单位码:快照里箱码命中 → 按箱价进车。
        self.assertEqual(self.r["offline_box_adds"], 350.0)

    def test_offline_miss_says_it_could_not_check_not_that_it_does_not_exist(self):
        self.assertIn("离线", self.r["offline_miss_msg"])
        self.assertIn("7777777777777", self.r["offline_miss_msg"])
        self.assertNotIn("没有条码", self.r["offline_miss_msg"])

    def test_offline_without_catalog_has_its_own_wording(self):
        self.assertIn(DICT_ZH["posui.bscan.offline_nocatalog"], self.r["offline_nocatalog_text"])
        # 这一档原先连码都不显示,店员事后无从知道漏的是哪一件。
        self.assertIn("6666666666666", self.r["offline_nocatalog_text"])

    def test_a_hit_does_not_wipe_earlier_failures(self):
        # 「下一件扫中就把上一件的提示收掉」正是这轮要根治的病:失败的那件货还没处理完。
        self.assertEqual(self.r["hit_keeps_fails"], 2)
        self.assertIn("可乐 325ml", self.r["hit_after_card_toast"])

    def test_two_misses_stack_instead_of_replacing_each_other(self):
        self.assertEqual(self.r["two_misses_stack"], 2, "第二件未命中把第一件顶掉了")
        self.assertIn("7777777777777", self.r["offline_nocatalog_text"])

    # ── 8. 相机用不了 ──
    def test_unsupported_camera_explains_then_falls_back_to_manual(self):
        # 原因写在手输弹窗里(遮罩会把身后的 toast 压暗,而店员这时眼睛在弹窗上)。
        self.assertEqual(self.r["unsupported_note"], DICT_ZH["bscan.err.unsupported"])
        self.assertEqual(self.r["unsupported_toasts"], 0, "改成弹窗内提示后不该再飘 toast")
        self.assertTrue(self.r["manual_pad_open"], "没给手输出路 = 死胡同")
        self.assertFalse(self.r["overlay_not_forced"], "相机开不了却把取景层摆出来 = 状态不诚实")

    # ── 9/10. 条码枪 ──
    def test_gun_ignored_off_main_screen_and_behind_modals(self):
        self.assertEqual(self.r["gun_off_main"], 0)
        self.assertEqual(self.r["gun_with_modal"], 0)
        self.assertEqual(self.r["gun_on_main"], 1)

    def test_done_button_gets_its_label(self):
        # HTML 里是空壳,文案由 open() 按当前语言画;漏了就是一个没字的紫方块(真出过)。
        self.assertEqual(self.r["done_label"], DICT_ZH["posui.bscan.done"])

    def test_camera_layer_takes_the_gun_exclusively(self):
        self.assertTrue(self.r["open_registers_exclusive"])
        # 独占 = 只有层里那份回调收到;页面级订阅者不再收 → 一次枪扫只加一件。
        self.assertEqual(self.r["gun_while_overlay"], 1)
        self.assertFalse(self.r["exclusive_gone_after_close"], "关层没退订 → 底下页面永远收不到枪")

    def test_decoder_failure_offers_retry_and_manual(self):
        self.assertEqual(self.r["decoder_acts"], ["重试", "手动输入条码"])
        self.assertTrue(self.r["decoder_card_msg"].strip())

    # ── 11. 加不进车必须出声 ──
    def test_unpriced_unit_never_enters_the_cart_at_zero(self):
        # 靠"小计没涨"证不了 —— ฿0 行涨的也是 0。断的是车里有没有多出这一行。
        self.assertEqual(self.r["zero_price_new_lines"], 0, "฿0.00 的整箱货进车了")
        self.assertEqual(self.r["zero_price_adds"], 0.0)

    def test_unpriced_unit_says_which_unit_and_where_to_fix_it(self):
        want = (
            DICT_ZH["posui.cart.unit_no_price"]
            .replace("{unit}", "ลัง")
            .replace("{name}", "百事 325ml")
        )
        self.assertIn(want, self.r["zero_price_text"])
        self.assertIn(DICT_ZH["posui.cart.fix_in_backoffice"], self.r["zero_price_text"])
        self.assertIn("18851959131010", self.r["zero_price_text"], "话里没嵌码就得单独摆出来")
        self.assertTrue(self.r["zero_price_shown"])

    def test_unknown_matched_unit_does_not_silently_swap_units(self):
        # 静默回落默认单位 = 扫一瓶按箱价 ฿350 收、库存按箱扣 24 瓶,屏上一个字都没有。
        # 这一件的基本单位没挂牌价 → 无从确定该收多少,只能拦(分界的第 ③ 种)。
        self.assertEqual(self.r["unit_swap_adds"], 0.0, "按别的单位收钱了")
        self.assertEqual(self.r["unit_swap_new_lines"], 0)
        want = (
            DICT_ZH["posui.cart.unit_unknown"]
            .replace("{unit}", "ขวด")
            .replace("{name}", "โค้กยกลัง")
        )
        self.assertIn(want, self.r["unit_swap_text"])

    # ── 11d. 基本单位可售(P1-H 修过头的那一面)──
    def test_base_unit_is_sellable_when_it_carries_a_price(self):
        # 一律拒收 = 这瓶水在收银台卖不出去(收银台只能改数量)。后端本来认 base_unit。
        self.assertEqual(self.r["base_unit_adds"], 15.0, "扫主码被拒 → 货卖不出去")
        self.assertEqual(self.r["base_unit_new_lines"], 1)
        self.assertEqual(self.r["base_unit_fails"], 0, "能卖的货还报了错")

    def test_base_unit_fallback_does_not_secretly_become_the_box(self):
        # 紧接着扫箱码:落成两行才证明上一扫真挂在「瓶」上。并成一行 = 那一扫其实按箱卖了,
        # 库存要扣 24 瓶。只看金额证不出单位 —— 15 也可能是箱价被改过。
        self.assertEqual(self.r["base_then_box_adds"], 365.0)
        self.assertEqual(self.r["base_then_box_lines"], 2, "瓶和箱并成了一行 = 单位被换掉了")

    def test_add_to_cart_reports_refusals_to_its_caller(self):
        # 网格点选那条路靠这个返回值出声(它自己弹 toast);回 null 就是"加进去了"。
        self.assertEqual(
            self.r["refuse_no_price"], {"key": "posui.cart.unit_no_price", "unit": "ลัง"}
        )
        self.assertEqual(
            self.r["refuse_unknown"], {"key": "posui.cart.unit_unknown", "unit": "ขวด"}
        )
        self.assertIsNone(self.r["refuse_ok"])
        self.assertEqual(self.r["direct_adds"], 10.0, "被拒的两件不许留下任何金额")

    # ── 12. 取景框 = 真被解码的那块 ──
    def test_viewfinder_matches_the_decoded_crop_of_the_visible_picture(self):
        crop = self.r["crop"]
        self.assertTrue(
            0 < crop["width"] <= 1 and 0 < crop["height"] <= 1, f"cropRatio 异常 {crop}"
        )
        # 舞台 390×772 · 摄像头 640×480 · contain → 画面实占 390×292.5,底下是黑边。
        box_w = 390.0
        box_h = 480.0 * (390.0 / 640.0)
        self.assertEqual(self.r["frame_w"], f"{round(box_w * crop['width'])}px")
        self.assertEqual(self.r["frame_h"], f"{round(box_h * crop['height'])}px")

    def test_viewfinder_never_reaches_outside_the_visible_picture(self):
        # 按舞台画会算出 386px 高:框越过画面边缘,框外那一段里的另一件货照样在解码区里。
        box_h = 480.0 * (390.0 / 640.0)
        self.assertLessEqual(float(self.r["frame_h"][:-2]), box_h)
        self.assertLessEqual(float(self.r["frame_w"][:-2]), 390.0)
        self.assertTrue(self.r["frame_live"], "出帧了框还没点亮 = 四态没走到 scanning")

    # ── 13. 离线主码 ──
    def test_offline_matches_the_product_barcode_not_only_unit_barcodes(self):
        self.assertEqual(self.r["master_match"], "ถุง")
        self.assertEqual(self.r["master_filter"], 1, "主码连粗筛都过不去 → 后面再准也白搭")

    def test_offline_master_code_sells_instead_of_reporting_snapshot_miss(self):
        self.assertEqual(self.r["master_calls"], 0)
        self.assertEqual(self.r["master_adds"], 20.0, "货就在本机目录里却没能取件")
        self.assertEqual(self.r["master_fails"], 0, "命中了还往清单里记一笔「本机目录里没有」")


class ViewfinderStyleContractTests(unittest.TestCase):
    """框的尺寸算法(pos-scan.js)只有在预览真是 contain 时才成立 —— node 里没有排版引擎,
    这一层只能盯住 CSS 那一行。真浏览器那侧归 scripts/_pos_scan_accept.cjs。"""

    def setUp(self):
        raw = (POS_DIR / "pos-scan.css").read_text(encoding="utf-8")
        # 注释里正写着「为什么不能 cover」,不剥掉就会自己把自己判红。
        self.css = re.sub(r"/\*.*?\*/", "", raw, flags=re.S)

    def test_preview_is_contain_so_visible_equals_decodable(self):
        rule = re.search(r"\.bscan-video\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(rule, ".bscan-video 规则没了 · 判据失效比断言失败更危险")
        self.assertIn("object-fit: contain", rule.group(1))
        self.assertNotRegex(
            self.css, r"object-fit:\s*cover", "cover 会把原生帧裁掉一半,而引擎解的仍是整帧"
        )

    def test_frame_size_is_not_hand_copied_into_css(self):
        # 比例的唯一事实源是引擎的 cropRatio();CSS 里再写一份,两处一漂就是
        # 「框里明明对准了却读不出」——而这种病不报任何错。
        rule = re.search(r"\.bscan-frame\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(rule)
        self.assertNotRegex(rule.group(1), r"\b(width|height)\s*:")


_PRODUCT_ROW = {
    "id": "aaaaaaaa-0000-0000-0000-000000000009",
    "name_th": "โค้ก 325ml",
    "name_en": None,
    "name_zh": None,
    "category_id": None,
    "barcode": "8850001",
    "base_unit": "ขวด",
    "image_url": None,
    "vat_applicable": True,
    "track_batch": False,
    "is_weighed": False,
    "unit_price": Decimal("15"),
}
_BOX_UNIT = {
    "product_id": _PRODUCT_ROW["id"],
    "unit_name": "ลัง",
    "factor_to_base": Decimal("24"),
    "barcode": "18850001",
    "price": Decimal("350"),
    "is_default_sell": True,
}


class _FakeCursor:
    """按语句形态分发。product_by_barcode 一次要走 4~5 条查询,按调用次序喂死答案分不出
    「命中单位行」和「命中主码」两条分支 —— 这里要的正是后者(码印在瓶上,只建了箱)。"""

    def __init__(self, product, unit_rows):
        self._product = product
        self._unit_rows = unit_rows
        self._one = None
        self._all = []

    def execute(self, sql, params=None):
        if "FROM product_units" in sql and "AND barcode = %s" in sql:
            self._one = None  # 主码这条路上单位码查不到任何行
        elif "FROM products" in sql:
            self._one = self._product
        elif "FROM product_units" in sql:
            self._all = self._unit_rows
        else:
            self._all = []  # inventory_stock 那两条

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class ByBarcodePayloadTests(unittest.TestCase):
    """扫主码那条路下发的载荷。基本单位的挂牌价一个字都不下发,前端就只能一律拒收 ——
    这瓶货在收银台卖不出去,而后端本来认 base_unit(sale.py 的 _resolve_unit)。
    前端那一半的反证在上面的 base_unit_* 两条。"""

    def _item(self, unit_price):
        row = dict(_PRODUCT_ROW, unit_price=unit_price)
        return pos_catalog.product_by_barcode(
            cur=_FakeCursor(row, [_BOX_UNIT]),
            tenant_id="t",
            workspace_client_id=1,
            code=_PRODUCT_ROW["barcode"],
        )

    def test_base_price_ships_with_the_item_the_units_list_cannot_carry(self):
        item = self._item(Decimal("15"))
        self.assertEqual(item["matched_unit"], "ขวด", "主码命中要回基本单位")
        self.assertEqual([u["unit_name"] for u in item["units"]], ["ลัง"])
        self.assertEqual(item["base_price"], "15.00", "基本单位的价没下发 → 前端只能拒收")

    def test_base_price_is_null_when_the_product_carries_no_price(self):
        # 没设价却下发一个数(比如 0)就是让前端照着它收钱 —— ฿0 出门在报表上看不出异常。
        self.assertIsNone(self._item(None)["base_price"])


if __name__ == "__main__":
    unittest.main()
