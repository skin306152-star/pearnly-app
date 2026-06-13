// 对账中心重设计 · 视觉对比 harness(dev only · 非产物)
// 抽取 RCX_HTML + 真 dist/home.css + zh 文案,填充初始工作区 / 结果两态,
// Playwright 三宽(1440/1280/390)截图;并截参考稿做对比。
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'product-audit', 'rcx-shots');
fs.mkdirSync(OUT, { recursive: true });

// 1) 抽取 RCX_HTML(纯模板字面量 · 无插值)
const htmlTs = fs.readFileSync(path.join(ROOT, 'src/home/recon-center-x-html.ts'), 'utf8');
const m = htmlTs.match(/export const RCX_HTML = `([\s\S]*?)`;/);
if (!m) throw new Error('RCX_HTML not found');
let RCX = m[1];

// 2) i18n zh 文案
global.window = {};
require(path.join(ROOT, 'static/i18n-data.js'));
const ZH = global.window.I18N.zh;
RCX = RCX.replace(/data-i18n="([^"]+)"/g, (full, k) => full).replace(
    /<([a-z0-9]+)([^>]*?)data-i18n="([^"]+)"([^>]*)>([\s\S]*?)<\/\1>/gi,
    (full, tag, pre, key, post, inner) => `<${tag}${pre}data-i18n="${key}"${post}>${ZH[key] || inner}</${tag}>`
);

// 3) 填充卡片 / 余额 / 结果(预览态 · 仅 harness)
const cardEmpty = (side, title) => `
  <div class="rcx-drop-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.8"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4"/><path d="M9 12h6M9 16h4"/></svg></div>
  <h3>${title}</h3>
  <div class="rcx-hint">${ZH['rcx-drop-hint']}</div>
  <div class="rcx-upload-actions">
    <button class="rcx-btn rcx-primary rcx-sm">${ZH['rcx-choose-file']}</button>
    <button class="rcx-btn rcx-sm">${ZH['rcx-dl-template']}</button>
  </div>
  <div class="rcx-recommend"><div class="rcx-spark">✦</div><div><b>${ZH['rcx-reco-title']}</b><span>${ZH['rcx-reco-sub']}</span></div></div>
  <div class="rcx-format-line">${ZH['rcx-format-line']}</div>`;
RCX = RCX.replace('<div class="rcx-upload-card" id="rcx-card-left" data-side="left"></div>',
    `<div class="rcx-upload-card" id="rcx-card-left" data-side="left">${cardEmpty('left', ZH['rcx-doc-statement'])}</div>`);
RCX = RCX.replace('<div class="rcx-upload-card" id="rcx-card-right" data-side="right"></div>',
    `<div class="rcx-upload-card" id="rcx-card-right" data-side="right">${cardEmpty('right', ZH['rcx-doc-gl'])}</div>`);
// 余额输入
['rcx-gl-end', 'rcx-st-end', 'rcx-st-start', 'rcx-gl-start'].forEach((id) => {
    RCX = RCX.replace(`<div class="rcx-balance-value" id="${id}">—</div>`,
        `<div class="rcx-balance-value" id="${id}"><input class="rcx-bal-input" placeholder="${ZH['rcx-optional']}" /></div>`);
});

const css = fs.readFileSync(path.join(ROOT, 'static/dist/home.css'), 'utf8');
const page = (extra) => `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style>
<style>body{margin:0;background:#f7f5fb}.wrap{padding:28px 30px}</style></head>
<body><section id="page-reconcile" class="ui"><div class="wrap">${RCX}</div></section>${extra || ''}</body></html>`;

(async () => {
    const browser = await chromium.launch();
    const widths = [1440, 1280, 390];
    // A) 我方:初始工作区态
    for (const w of widths) {
        const ctx = await browser.newContext({ viewport: { width: w, height: 900 }, deviceScaleFactor: 1 });
        const p = await ctx.newPage();
        await p.setContent(page(), { waitUntil: 'networkidle' });
        await p.screenshot({ path: path.join(OUT, `rcx-${w}.png`), fullPage: true });
        await ctx.close();
    }
    // B) 参考稿
    const refUrl = 'file://' + path.join(ROOT, 'design-reference/pearnly_reconciliation_redesign_v2.html').replace(/\\/g, '/');
    for (const w of widths) {
        const ctx = await browser.newContext({ viewport: { width: w, height: 900 }, deviceScaleFactor: 1 });
        const p = await ctx.newPage();
        await p.goto(refUrl, { waitUntil: 'networkidle' });
        await p.screenshot({ path: path.join(OUT, `ref-${w}.png`), fullPage: true });
        await ctx.close();
    }
    await browser.close();
    console.log('shots →', OUT);
})();
