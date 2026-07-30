#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/unit/_inventory_scan_dom.py

入库弹窗扫码(src/home/inventory-scan*.ts)在真 node 里跑起来的 harness。

为什么非要这一套(2026-07-31 审查实锤):这批的接缝断言原本全是「源码里有没有这一行」,
把 `unmountInvScan()` 的函数体整个包进 `if (false)`(字面一个字不删)之后,16 条照样
`Ran 16 ... OK` —— 相机灯永远亮着、楔子永不反注册,单测一声不吭。字符串在,行为没了。

所以这里让产品自己跑一遍:
  · 弹窗 DOM 由 inventory-modals.ts 的 `window.openInventoryIn()` 现渲染 —— 断言用的
    id / data-* 全是产品自己吐的,不是这份 harness 编的(踩过:桩造出产品里不存在的对象,
    35 条深链全落空却 16 项全绿)。
  · 条码枪楔子用 static/scan/scan-wedge.js 真件,不打桩 —— `subscriberCount()` 就是真浏览器
    验收里断言的那个量,「关弹窗有没有退订」这件事在这里跟 E2E 看的是同一个数。
  · inventory-common.ts 也是真件(localizedName / isSaneExpiry / invErrMsg 都真跑),
    只把 `invApi.products()` 换成本用例的货架 —— 那是网络,不是判定。

打桩只剩两处,都在本模块职责之外:sales-common 的 salesFetch(后端)、PearnlyScanCamera
(真引擎要 getUserMedia,node 里没有;摄像头画面归 E2E)。

下划线开头 · unittest discovery 不收本文件当测试模块。
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOME_DIR = PROJECT_ROOT / "src" / "home"
SCAN_DIR = PROJECT_ROOT / "static" / "scan"

# ── 迷你 DOM:只实现产品真用到的那些面 ────────────────────────────────────
_DOM = r"""
const VOID = new Set(['input', 'img', 'br', 'hr', 'meta', 'link', 'source', 'path', 'circle', 'rect']);

class El {
    constructor(tag) {
        this.tagName = String(tag).toUpperCase();
        this.childNodes = [];
        this.parentNode = null;
        this.attributes = {};
        this.dataset = {};
        this.style = {};
        this.id = '';
        this.value = '';
        this.hidden = false;
        this.disabled = false;
        this.focused = 0;
        this._class = '';
        this._html = '';
        this.onclick = null;
        this.onkeydown = null;
        this.onchange = null;
    }
    get children() { return this.childNodes.filter((n) => n instanceof El); }
    get lastElementChild() { const k = this.children; return k[k.length - 1] || null; }
    get className() { return this._class; }
    set className(v) { this._class = String(v == null ? '' : v); }
    get classList() {
        const self = this;
        const list = () => self._class.split(/\s+/).filter(Boolean);
        return {
            contains: (c) => list().indexOf(c) >= 0,
            add: (c) => { if (list().indexOf(c) < 0) self._class = (self._class + ' ' + c).trim(); },
            remove: (c) => { self._class = list().filter((x) => x !== c).join(' '); },
            toggle: (c, on) => (on ? self.classList.add(c) : self.classList.remove(c)),
        };
    }
    setAttribute(name, value) {
        const v = value == null ? '' : String(value);
        this.attributes[name] = v;
        if (name === 'id') this.id = v;
        else if (name === 'class') this.className = v;
        else if (name === 'value') this.value = v;
        else if (name === 'hidden') this.hidden = true;
        else if (name === 'disabled') this.disabled = true;
        else if (name === 'style')
            // 行内 style 必须真解析:批号/效期格的初始 display:none 就写在标记里,
            // 不解析的话「批次格默认藏着」这条断言会永远绿(读到的是 undefined ≠ 'none')
            v.split(';').forEach((d) => {
                const at = d.indexOf(':');
                if (at > 0)
                    this.style[d.slice(0, at).trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase())] =
                        d.slice(at + 1).trim();
            });
        else if (name.startsWith('data-'))
            this.dataset[name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = v;
    }
    getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; }
    appendChild(node) { node.parentNode = this; this.childNodes.push(node); return node; }
    remove() {
        const p = this.parentNode;
        if (!p) return;
        p.childNodes = p.childNodes.filter((n) => n !== this);
        this.parentNode = null;
    }
    get innerHTML() { return this._html; }
    set innerHTML(html) { this.childNodes = []; this._html = String(html); parseInto(this._html, this); }
    insertAdjacentHTML(_pos, html) { parseInto(String(html), this); }
    get textContent() {
        return this.childNodes
            .map((n) => (n instanceof El ? n.textContent : n.text))
            .join('');
    }
    set textContent(v) { this.childNodes = [{ text: String(v == null ? '' : v) }]; }
    get options() { return this.children.filter((c) => c.tagName === 'OPTION'); }
    matches(sel) { return parseSel(sel).some((conds) => conds.every((f) => f(this))); }
    querySelectorAll(sel) {
        const groups = parseSel(sel);
        const out = [];
        const walk = (el) => el.children.forEach((c) => {
            if (groups.some((conds) => conds.every((f) => f(c)))) out.push(c);
            walk(c);
        });
        walk(this);
        return out;
    }
    querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
    closest(sel) {
        let el = this;
        while (el) { if (el.matches(sel)) return el; el = el.parentNode; }
        return null;
    }
    contains(el) { let n = el; while (n) { if (n === this) return true; n = n.parentNode; } return false; }
    focus() { this.focused += 1; document.activeElement = this; }
    scrollIntoView() {}
    addEventListener() {}
    removeEventListener() {}
    // 冒泡是真的:产品把 onclick 绑在【消息块】上,靠 ev.target.closest() 认出点的是哪个按钮
    //(事件委托)。不冒泡的话「点未命中卡上的『去建这个商品』」这条永远调不到,测试会绿得莫名。
    click() {
        let el = this;
        while (el) {
            if (el.onclick) el.onclick({ target: this });
            el = el.parentNode;
        }
    }
}
class HTMLInputElement extends El {}
class HTMLSelectElement extends El {}

function makeEl(tag) {
    const t = String(tag || 'div').toLowerCase();
    const el = t === 'input' ? new HTMLInputElement(t) : t === 'select' ? new HTMLSelectElement(t) : new El(t);
    el.tagName = t.toUpperCase();
    return el;
}

// 选择器:标签 / #id / .class / [attr] / [attr="v"],逗号分组。产品里只用到这些,
// 后代组合子一处都没有(取件全走 getElementById 或行内 querySelector)。
const SEL_PART = /(^[a-zA-Z][\w-]*)|#([\w-]+)|\.([\w-]+)|\[([\w-]+)(?:=\s*["']?([^\]"']*)["']?)?\]/g;
function parseSel(sel) {
    return String(sel).split(',').map((s) => s.trim()).filter(Boolean).map((part) => {
        const conds = [];
        let m;
        SEL_PART.lastIndex = 0;
        while ((m = SEL_PART.exec(part))) {
            const [, tag, id, cls, attr, val] = m;
            const wanted = val;
            const exact = m[0].indexOf('=') >= 0;
            if (tag) conds.push((el) => el.tagName === tag.toUpperCase());
            else if (id) conds.push((el) => el.id === id);
            else if (cls) conds.push((el) => el.classList.contains(cls));
            else conds.push((el) => attr in el.attributes && (!exact || el.attributes[attr] === wanted));
        }
        return conds;
    });
}

const TAG_OPEN = /^([a-zA-Z][\w-]*)/;
const ATTRS = /([a-zA-Z_:][-\w:.]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;
function parseInto(html, parent) {
    const stack = [parent];
    let i = 0;
    while (i < html.length) {
        const lt = html.indexOf('<', i);
        const top = stack[stack.length - 1];
        if (lt < 0) { if (html.slice(i).trim()) top.childNodes.push({ text: html.slice(i) }); break; }
        if (lt > i && html.slice(i, lt).trim()) top.childNodes.push({ text: html.slice(i, lt) });
        if (html.startsWith('<!--', lt)) { i = html.indexOf('-->', lt) + 3; continue; }
        if (html.startsWith('</', lt)) { if (stack.length > 1) stack.pop(); i = html.indexOf('>', lt) + 1; continue; }
        let j = lt + 1;
        let quote = '';
        while (j < html.length) {
            const c = html[j];
            if (quote) { if (c === quote) quote = ''; }
            else if (c === '"' || c === "'") quote = c;
            else if (c === '>') break;
            j++;
        }
        const raw = html.slice(lt + 1, j);
        const selfClose = raw.trimEnd().endsWith('/');
        const body = selfClose ? raw.trimEnd().slice(0, -1) : raw;
        const name = TAG_OPEN.exec(body);
        if (!name) { i = j + 1; continue; }
        const el = makeEl(name[1]);
        ATTRS.lastIndex = name[1].length;
        let a;
        while ((a = ATTRS.exec(body))) el.setAttribute(a[1], a[2] ?? a[3] ?? a[4] ?? '');
        top.appendChild(el);
        if (!selfClose && !VOID.has(name[1].toLowerCase())) stack.push(el);
        i = j + 1;
    }
}

const document = {
    body: makeEl('body'),
    head: makeEl('head'),
    activeElement: null,
    createElement: makeEl,
    getElementById(id) { return document.body.querySelectorAll('#' + id)[0] || null; },
    querySelector(sel) { return document.body.querySelector(sel); },
    querySelectorAll(sel) { return document.body.querySelectorAll(sel); },
    addEventListener() {},
    removeEventListener() {},
};
global.document = document;
global.HTMLInputElement = HTMLInputElement;
global.HTMLSelectElement = HTMLSelectElement;
global.navigator = { maxTouchPoints: 0, userAgent: 'node' };
global.self = globalThis;
global.window = globalThis;
"""

# ── 全局桩 + 模块装载 ─────────────────────────────────────────────────────
_BOOT = r"""
const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');
const HOME = process.argv[1];
const SCAN = process.argv[2];

// t() 回「键 + 各插值位」:断言钉住的是【用了哪一句 + 哪个值填了进去】,不钉某一种语言的
// 字面量(那会让改文案就红)。插值位必须留着 —— 产品有几处是 t('k').replace('{code}', code),
// 回一个不含 {code} 的串会让「码有没有显在卡上」永远断不出来(真词典里那句是带 {code} 的)。
const PLACEHOLDERS = '{code}{name}{unit}{n}';
global.t = (key, params) => {
    let s = key + PLACEHOLDERS;
    for (const k in params || {}) s = s.split('{' + k + '}').join(String(params[k]));
    return s;
};
global.escapeHtml = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => '&#' + c.charCodeAt(0) + ';');
global.showToast = () => {};
global.currentLang = () => 'zh';
global.token = () => 'harness';
global.getActiveWorkspaceClientId = () => 1;

// 条码枪楔子:共享地基的真件(subscriberCount 就是 E2E 断言的那个量)
require(path.join(SCAN, 'scan-wedge.js'));

// 摄像头引擎在 node 里跑不了(要 getUserMedia)· 只记「谁被调用了」;画面归 E2E
const camLog = { created: 0, destroyed: 0, started: 0, blocked: null };
global.PearnlyScanCamera = {
    unsupportedReason: () => camLog.blocked,
    ensureLoaded: async () => global.PearnlyScanCamera,
    create: () => {
        camLog.created += 1;
        return {
            start: async () => { camLog.started += 1; return true; },
            retry: async () => true,
            destroy: () => { camLog.destroyed += 1; },
            cropRatio: () => ({ width: 0.9, height: 0.5 }),
        };
    },
};

// 唯一的网络出口:在 salesFetch 这一层截断,别的都跑真代码
const lookups = [];
let reply = () => ({ status: 404, ok: false, json: async () => ({ detail: 'sales.product_not_found' }) });
const SALES_COMMON = {
    salesFetch: (url) => { lookups.push(String(url)); return Promise.resolve(reply(String(url))); },
    salesErrMsg: (d, fb) => String(d || fb),
};
function answer(body, status) {
    const st = status || 200;
    return { status: st, ok: st >= 200 && st < 300, json: async () => body };
}

const cache = {};
function load(name) {
    if (cache[name]) return cache[name];
    const src = fs.readFileSync(path.join(HOME, name + '.ts'), 'utf8');
    const { code } = esbuild.transformSync(src, { loader: 'ts', format: 'cjs' });
    const mod = { exports: {} };
    cache[name] = mod.exports;
    new Function('module', 'exports', 'require', code)(mod, mod.exports, (spec) => {
        const base = path.basename(spec).replace(/\.js$/, '');
        return base === 'sales-common' ? SALES_COMMON : load(base);
    });
    cache[name] = mod.exports;
    return mod.exports;
}

const common = load('inventory-common');
load('inventory-modals'); // 挂 window.openInventoryIn
const scan = load('inventory-scan');
const ui = load('inventory-scan-ui');

// 货架:invApi.products() 是网络的产物,换掉它;localizedName / isSaneExpiry 等仍是真件
let shelf = [];
common.invApi.products = () => shelf;

const tick = () => new Promise((r) => setTimeout(r, 5));
const out = (o) => process.stdout.write(JSON.stringify(o));

// 弹窗由产品自己渲染:断言用的 id / data-* 全来自 inventory-modals 吐的那段 HTML
function openIn() {
    document.body.innerHTML = '<div id="inv-in-mask"></div>';
    window.openInventoryIn();
    return document.getElementById('inv-in-mask');
}
const rows = () => document.getElementById('inv-in-mask-rows').querySelectorAll('[data-row]');
const field = (row, k) => row.querySelector('[data-k="' + k + '"]');
function snapshot() {
    return rows().map((r) => ({
        product: field(r, 'product_id').value,
        qty: field(r, 'qty').value,
        unit: field(r, 'unit_name').value,
        unitText: r.querySelector('[data-runit]').textContent,
        unitHidden: r.querySelector('[data-runit]').hidden,
        batchShown: r.querySelector('[data-batchcell]').style.display !== 'none',
    }));
}
const wedgeSubs = () => window.PearnlyScanWedge.subscriberCount();
const msgEl = () => document.getElementById('inv-in-mask-scan-msg');
"""

PRELUDE = _DOM + _BOOT


def run(body: str) -> dict:
    """PRELUDE + body 在 node 里跑一遍,返回 body 用 out() 吐的 JSON。"""
    proc = subprocess.run(
        ["node", "-e", PRELUDE + body, str(HOME_DIR), str(SCAN_DIR)],
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
