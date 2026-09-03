#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/_pos_scan_dom.py

收银台扫码那条链的共享 node 跑台:最小 DOM 桩 + 扫码地基桩(摄像头 / 楔子)+ 网络桩,
最后按真实加载顺序 eval 四个真源文件(pos-data / pos-cashier / pos-scan-fails / pos-scan)。

为什么收到一处:test_pos_scan_pipeline(取件语义)和 test_pos_scan_fail_ledger(失败清单
这本账)要的是同一套桩,各抄一份就会漂 —— 而漂了之后两边各绿各的,谁都照不出真产品的行为。
下划线开头文件名 · unittest discovery 不收本文件当测试模块。

用法:调用方只写 main()(拼 R 对象 + process.stdout.write),把它交给 run():

    R = run(NODE_MAIN, DICT_ZH)

桩里已经备好的把手(调用方按需改):
  UNSUPPORTED / CAM_API   这台机器能不能开相机 / 解码器拉没拉下来
  LAST_CAM / LAST_CAM_OPTS真 handle / pos-scan.js 交给引擎的那袋回调(onDuplicate 由此触发)
  NEXT / BY_CODE / DELAY  后端怎么答(单一答案 / 按码分答 / 往返耗时)
  gunScan(code)           照楔子真实语义发一次枪扫(有 exclusive 订阅者时只有它收)
  typedScan(code, ...)    楔子判成「人在打字」的那一发(register 的 onTyped · 同一份收件人)
  pressKey(key)           敲一下键 · 文档级 keydown 订阅者全收到(Esc 那条路唯一的入口)
  QS_ONE[选择器]          document.querySelector 的答案(弹窗开着 = 给 '#view-main .mask.show'
                          放一个元素 —— 那是 pos-scan.js 判「有窗开着」的唯一依据)
  SNAP / SNAP_ON          离线快照(POS.offline 由调用方自己按需要装)
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POS_DIR = PROJECT_ROOT / "static" / "pos"
SCAN_DIR = PROJECT_ROOT / "static" / "scan"

# 桩 + 真源加载(到 pos-scan.js 为止);调用方的 main() 直接接在后面。
PRELUDE = r"""
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
// 文档级监听真的记下来:收银主屏的 Esc 由 pos-scan.js 和 pos-cashier.js 各挂一份在 document 上,
// 丢掉它们等于「按 Esc 会发生什么」这条路在测里根本不存在(旧桩是空函数,真出过事的那条
// 「Esc 顺手把失败清单清光」因此照不出来)。
const docOn = {};
global.document = {
    readyState: 'complete',
    getElementById: (id) => (byId[id] = byId[id] || mkEl('div')),
    createElement: (tag) => mkEl(tag),
    createTextNode: (t) => ({ textContent: String(t) }),
    querySelector: (sel) => QS_ONE[sel] || null,
    querySelectorAll: () => [],
    addEventListener: (type, fn) => (docOn[type] = docOn[type] || []).push(fn),
    body: mkEl('body'),
};
// 敲一下键:所有文档级 keydown 订阅者都收到(真页面上它们本来就都在)。
function pressKey(key) {
    (docOn.keydown || []).forEach((fn) => fn({ key: key, preventDefault() {} }));
}
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
// 顺序照 dist/scan.js 的真实拼法(scripts/build-home-js.mjs):错误分档与裁决状态机都排在
// 引擎之前 —— 引擎在加载期就把 scanError/withTimeout 与 PearnlyScanTrack 抓进闭包,
// 晚一步它自己会抛「地基没到齐」。
(0, eval)(fs.readFileSync(scanDir + '/scan-errors.js', 'utf8'));
(0, eval)(fs.readFileSync(scanDir + '/scan-track.js', 'utf8'));
(0, eval)(fs.readFileSync(scanDir + '/scan-camera.js', 'utf8'));
const ENGINE = global.PearnlyScanCamera;

// 真 create() 建真 handle(真 cropRatio、真 video 元素),只把 start() 换成「直接报出帧」:
// 相机开不开得起来在 node 里不可验,那条归真浏览器验收(scripts/_pos_scan_accept.cjs)。
let LAST_CAM = null; // 真 handle · 取景框的期望值只许从它的 cropRatio() 反查
// 引擎回调那一袋原样留一份:onDuplicate 这条路在 node 里没有别的入口(tick 循环要真画面),
// 而它正是「第二件被当成同一件挡下」那一发的唯一出口。留的是 pos-scan.js 真的交给引擎的
// 那个对象 —— 名字对不上、或者根本没接,这里就是 undefined,测跟着红。
let LAST_CAM_OPTS = null;
function camApi(videoW, videoH) {
    return {
        create(opts) {
            const h = ENGINE.create(opts);
            h.video.videoWidth = videoW;
            h.video.videoHeight = videoH;
            LAST_CAM = h;
            LAST_CAM_OPTS = opts;
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
        const entry = { cb, exclusive: !!(opts && opts.exclusive), onTyped: opts && opts.onTyped };
        wedgeSubs.push(entry);
        return () => {
            const i = wedgeSubs.indexOf(entry);
            if (i >= 0) wedgeSubs.splice(i, 1);
        };
    },
};
// 楔子的真实语义:有 exclusive 订阅者时只有它收(scan-wedge.js 的 receivers())。
function receivers() {
    let last = null;
    wedgeSubs.forEach((s) => {
        if (s.exclusive) last = s;
    });
    return last ? [last] : wedgeSubs.slice();
}
// 页面级订阅者不把取件的 promise 传回来(生产里没人 await 它),所以扫完要让在飞的活落地
// 再断状态 —— 真实时间线上两次扫码本来也不在同一毫秒。
function gunScan(code) {
    return Promise.all(receivers().map((s) => s.cb(code, document.body))).then(settle);
}
// 楔子判成「人在打字」的那一发(scan-wedge.js 的 onTyped):走同一份 receivers,没接这一路的
// 订阅者就什么都不发生 —— 这正是要验的那件事,所以由订阅者自己有没有 onTyped 决定,不在这兜底。
function typedScan(code, target, info) {
    receivers().forEach((s) => {
        if (s.onTyped) s.onTyped(code, target || document.body, info || { field: true, before: '' });
    });
    return settle();
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
load('pos-totals.js');
POS.totals = global.POS.totals;
load('pos-cart-math.js');
load('pos-cashier.js');
// 顺序照 dist/pos.js 的真实拼法:失败清单那本账在 pos-scan.js 加载期就被 create()。
load('pos-scan-fails.js');
load('pos-scan.js');
"""


def run(main_js: str, dict_zh: dict, timeout: float = 60) -> dict:
    """真 node 子进程跑 PRELUDE + main_js,拿回 main() 打到 stdout 的那个 JSON。

    字典按语言桩喂进去(每个调用方只放自己断言要用的键,真字典的 4 语完整性归
    test_pos_spa_i18n.py 那道闸)。node 挂了就把 stderr 原样抛出来 —— 吞掉退出码
    会让「跑台自己崩了」长得跟「断言没过」一模一样。
    """
    proc = subprocess.run(
        ["node", "-e", PRELUDE + main_js, "--", str(POS_DIR), json.dumps(dict_zh), str(SCAN_DIR)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise AssertionError("node 跑挂了:\n" + proc.stderr.decode("utf-8", "replace"))
    return json.loads(proc.stdout.decode("utf-8"))
