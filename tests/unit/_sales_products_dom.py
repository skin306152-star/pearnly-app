#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/_sales_products_dom.py

建品表单(src/home/sales-products*.ts)在真 node 里跑起来的 harness。

为什么要这么一套:这一批的三个 P0/P1 全在「静态断言照不到」的地方 —— 楔子碎片会不会把
框里打好的位数吃掉、贴上码 400ms 内点保存拦不拦得住、桥回 true/false 准不准,都得让代码
真跑一遍才看得出来。断言的对象全是产品源码自己的导出与自己渲染出来的 id,不造产品里不存在
的对象:DOM 只是宿主(同 test_scan_wedge_pure 那份 document 桩),元素由产品自己 innerHTML
里的 id="…" 现注册,网络在 salesFetch 那一层截断。

下划线开头 · unittest discovery 不收本文件当测试模块。
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCAN_TS = PROJECT_ROOT / "src" / "home" / "sales-products-scan.ts"
CAM_TS = PROJECT_ROOT / "src" / "home" / "sales-products-scan-cam.ts"
PRODUCTS_TS = PROJECT_ROOT / "src" / "home" / "sales-products.ts"
WEDGE_JS = PROJECT_ROOT / "static" / "scan" / "scan-wedge.js"

# ── 宿主桩 + 模块装载(所有场景共用)───────────────────────────────────────
PRELUDE = """
const esbuild = require('esbuild');
const fs = require('fs');

const nodes = {};
const TAG_WITH_ID = /<[a-z][^>]*\sid="([^"]+)"[^>]*>/gi;
const DATA_ATTR = /\s(data-[a-z0-9-]+)="([^"]*)"/gi;
const camel = (name) => name.replace(/^data-/, '').replace(/-([a-z])/g, (_, c) => c.toUpperCase());
// 元素表由产品自己吐的 HTML 现建:id / value / checked / data-* 都读它写的那一份,
// 浏览器会把这些属性同步成属性值和 dataset,桩也照做 —— 楔子的 declaresGun 正是读这两样,
// 桩不同步就等于「产品声明了接枪」这件事在测试里从来没成立过。
function registerIds(html) {
    let m;
    while ((m = TAG_WITH_ID.exec(html))) {
        const tag = m[0];
        const el = nodes[m[1]] || makeEl(m[1]);
        const v = /\svalue="([^"]*)"/.exec(tag);
        if (v) el.value = v[1];
        if (/\schecked[\s>]/.test(tag)) el.checked = true;
        const name = /^<([a-z]+)/i.exec(tag);
        if (name) el.tagName = name[1].toUpperCase();
        let d;
        DATA_ATTR.lastIndex = 0;
        while ((d = DATA_ATTR.exec(tag))) {
            el.attrs[d[1]] = d[2];
            el.dataset[camel(d[1])] = d[2];
        }
    }
}
function makeEl(id) {
    let html = '';
    const el = {
        id,
        tagName: 'DIV',
        value: '',
        textContent: '',
        className: '',
        disabled: false,
        checked: false,
        focused: 0,
        style: {},
        attrs: {},
        dataset: {},
        options: [],
        kids: [],
        get innerHTML() { return html; },
        // 产品自己渲染的 HTML 就是元素表的来源:断言的 id 只可能来自真实产物
        set innerHTML(v) { html = String(v); registerIds(html); },
        // 楔子 declaresGun 先看 dataset 再回落 getAttribute:两条都得在,不然只验到了一条
        getAttribute(k) { return Object.prototype.hasOwnProperty.call(el.attrs, k) ? el.attrs[k] : null; },
        setAttribute(k, v) { el.attrs[k] = v; },
        focus() { el.focused += 1; },
        remove() { delete nodes[el.id]; },
        appendChild(c) { if (c && c.id) nodes[c.id] = c; el.kids.push(c); return c; },
        querySelector() { return null; },
        querySelectorAll() { return []; },
        closest() { return null; },
    };
    if (id) nodes[id] = el;
    return el;
}
const keyHandlers = [];
global.document = {
    getElementById: (id) => nodes[id] || null,
    createElement: (tag) => {
        const e = makeEl('');
        e.tagName = String(tag || 'div').toUpperCase();
        return e;
    },
    addEventListener: (type, fn) => { if (type === 'keydown') keyHandlers.push(fn); },
    removeEventListener: (type, fn) => {
        const i = keyHandlers.indexOf(fn);
        if (i >= 0) keyHandlers.splice(i, 1);
    },
    head: makeEl('head'),
    body: makeEl('body'),
    querySelectorAll: () => [],
};
const routed = [];
global.window = {
    setTimeout: (fn, ms) => setTimeout(fn, ms),
    routeTo: (r) => routed.push(r),
};
// t() 回 key|params:断言就能钉住「用了哪一句」,而不是钉住某一种语言的字面量
global.t = (key, params) => (params ? key + '|' + JSON.stringify(params) : key);
global.escapeHtml = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => '&#' + c.charCodeAt(0) + ';');
const toasts = [];
global.showToast = (msg, kind) => toasts.push([String(msg), kind || '']);
global.apiGet = async () => ({ products: [] });

// salesFetch 是唯一的网络出口:在这里截断,别的都跑真代码
const calls = [];
let answer = () => ({ status: 404, ok: false, json: async () => null });
function salesFetch(url, opts) {
    // body 原样留着:「表单到底发了什么」是好几条反证的断言对象(发 0 还是 null、发不发得出"清空")
    calls.push({
        url: String(url),
        method: (opts && opts.method) || 'GET',
        body: opts && typeof opts.body === 'string' ? JSON.parse(opts.body) : null,
    });
    const r = answer(String(url), opts);
    return r instanceof Promise ? r : Promise.resolve(r);
}
function reply(body, status) {
    const st = status || 200;
    return { status: st, ok: st >= 200 && st < 300, json: async () => body };
}

const COMMON = {
    salesFetch,
    htmlVal: (v) => (v == null ? '' : String(v)),
    // 照 sales-common.fmtMoney 的核心写(Number(v || 0) 再补两位):桩要是把 null 显示成
    // 「null」,「没设价被画成 ฿0.00」这条就永远被桩藏起来了
    fmtMoney: (v) => Number(v || 0).toFixed(2),
    salesErrMsg: (d, fb) => String(d || fb),
    imageFieldHtml: (id) => '<input id="' + id + '">',
    bindImageField: () => {},
    loadAuthedImg: async () => {},
    // 飞入反馈由自己的 DOM/并发测试覆盖;本 harness 只验建品表单业务状态机。
    showScanSuccessVisual: () => false,
    IC_X: '<svg></svg>',
};

function loadTs(file, resolve) {
    const src = fs.readFileSync(file, 'utf8');
    const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });
    const mod = { exports: {} };
    new Function('module', 'exports', 'require', code)(mod, mod.exports, resolve);
    return mod.exports;
}
const CAM = loadTs(process.argv[1], () => COMMON);
const SCAN = loadTs(process.argv[2], (id) =>
    id.indexOf('scan-cam') >= 0 ? CAM : COMMON
);
function loadProducts() {
    return loadTs(process.argv[3], (id) => (id.indexOf('-scan.js') >= 0 ? SCAN : COMMON));
}
const tick = () => new Promise((r) => setTimeout(r, 5));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// 忙等:枪速那几毫秒不能交给调度器(setTimeout 在负载下会漂到 50ms 以上,那就不是枪了)
const spin = (ms) => { const until = Date.now() + ms; while (Date.now() < until) {} };
const out = (o) => process.stdout.write(JSON.stringify(o));

// ── 真楔子(不是桩)────────────────────────────────────────────────────
// 装上 static/scan/scan-wedge.js 本体,让建品表单像在浏览器里那样从它那里收回调。
// 用桩楔子只能验「产品收到 X 时怎么办」;而这一批要验的恰恰是【X 会不会发生】——
// 判据只有一份、在楔子里,桩楔子直接喂碎片等于绕过判据自问自答。
function installRealWedge() {
    const wedge = require(process.argv[4]);
    global.window.PearnlyScanWedge = wedge;
    return wedge;
}
// 一次按键:先跑 keydown 处理器(楔子挂在这),再照浏览器的顺序把字符落进框 + 发 input 事件。
// stamp = 事件【产生】的时刻(KeyboardEvent.timeStamp)· 楔子的尺子量的就是它,不是墙钟。
function press(key, target, stamp) {
    let prevented = 0;
    keyHandlers.forEach((h) =>
        h({ key, target, timeStamp: stamp, repeat: false, preventDefault: () => { prevented += 1; } })
    );
    if (key.length === 1 && target && typeof target.value === 'string') {
        target.value += key;
        if (typeof target.oninput === 'function') target.oninput();
    }
    return prevented;
}
/** 按 gapMs 一个字符地把 code 打进 target;真 sleep,让楔子那只 150ms 计时器照常跑。 */
async function typeAt(code, target, gapMs, t0) {
    let stamp = t0 === undefined ? 1000 : t0;
    for (const ch of code) {
        press(ch, target, stamp);
        stamp += gapMs;
        await sleep(gapMs);
    }
    return stamp;
}
"""


def run(body: str) -> dict:
    """PRELUDE + body 在 node 里跑一遍,返回 body 用 out() 吐的 JSON。"""
    proc = subprocess.run(
        ["node", "-e", PRELUDE + body, str(CAM_TS), str(SCAN_TS), str(PRODUCTS_TS), str(WEDGE_JS)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        timeout=90,
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    if proc.returncode != 0:
        raise AssertionError(f"node 退出码 {proc.returncode}\n{stderr}")
    raw = proc.stdout.decode("utf-8", "replace")
    if not raw.strip():
        raise AssertionError(f"node 没有输出 JSON\n{stderr}")
    return json.loads(raw)
