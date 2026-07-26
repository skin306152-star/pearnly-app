// ============================================================
// 使用教程页(#page-guide)· 手册 → 篇 → 章节正文。
// 侧栏只到手册这一层(父栏「使用教程」→ 子栏「Express 推送手册」)—— 使用教程以后还要
// 挂别的手册,手册内部的篇章不占侧栏。进手册先看七篇总览(无面包屑),点进某一篇才起面包屑。
// 正文只做中泰(会计与老板的实际语言),英/日回落中文;配图同样分中泰两套 ——
// 中文正文配泰文界面图读者对不上号。
// ============================================================
import {
    esc,
    T,
    loadIndex,
    loadSection,
    loadedIndex,
    loadedSection,
    findLoadedChapter,
    findChapterAcrossBook,
} from './guide-content.js';
import type { Bilingual, GuideChapter, Lang, SectionMeta } from './guide-content.js';
import { withFingerprint } from './asset-fingerprint.js';

const SHOT_BASE = '/static/dist/guide-shots/';

interface WinBridge {
    _currentLang?: string;
    subscribeI18n?: (key: string, fn: () => void) => void;
    routeTo?: (r: string) => void;
}

function lang(): Lang {
    const w = window as unknown as WinBridge;
    return (w._currentLang || localStorage.getItem('mrpilot_lang')) === 'th' ? 'th' : 'zh';
}

const say = (b: Bilingual): string => b[lang()];

let secId = '';
let chId = '';

const meta = (id: string): SectionMeta | undefined =>
    loadedIndex()?.sections.find((s) => s.id === id);

const bookTitle = (): string => {
    const idx = loadedIndex();
    return idx ? say(idx.book) : T('gd-book-express');
};

// 三层页面同一套页头(标题 + 副行);副行省略时只出标题。
function pageHead(title: string, sub?: string): string {
    return (
        `<h1 class="gd-h1">${esc(title)}</h1>` +
        (sub === undefined ? '' : `<p class="gd-intro">${esc(sub)}</p>`)
    );
}

// 七篇总览页不起面包屑(它就是手册首页);进了某一篇才需要回退路径。
function crumbHtml(): string {
    if (!secId) return '';
    const parts = [
        `<button type="button" class="gd-crumb-b" data-gd-root>${esc(bookTitle())}</button>`,
    ];
    const s = meta(secId);
    if (s) {
        parts.push('<span class="gd-crumb-sep">/</span>');
        parts.push(
            chId
                ? `<button type="button" class="gd-crumb-b" data-gd-sec-up="${esc(s.id)}">${esc(say(s.title))}</button>`
                : `<span class="gd-crumb-cur">${esc(say(s.title))}</span>`
        );
    }
    if (chId) {
        const c = findLoadedChapter(chId);
        if (c) {
            parts.push('<span class="gd-crumb-sep">/</span>');
            parts.push(`<span class="gd-crumb-cur">${esc(say(c.title))}</span>`);
        }
    }
    return `<nav class="gd-crumb">${parts.join('')}</nav>`;
}

function rootHtml(): string {
    const idx = loadedIndex();
    if (!idx) return pageHead(T('gd-book-express'));
    const cards = idx.sections
        .map((s) => {
            const label = s.done
                ? `${s.done} / ${s.planned}`
                : `<span class="gd-todo">${esc(T('gd-soon'))}</span>`;
            return (
                `<button type="button" class="gd-card${s.done ? '' : ' is-todo'}" data-gd-sec="${esc(s.id)}">` +
                `<b>${esc(say(s.title))}</b><span class="gd-card-n">${label}</span></button>`
            );
        })
        .join('');
    return pageHead(say(idx.book), T('gd-sub')) + `<div class="gd-grid">${cards}</div>`;
}

function sectionHtml(s: SectionMeta): string {
    const list = loadedSection(s.id) || [];
    const items = list
        .map(
            (c) =>
                `<button type="button" class="gd-item" data-gd-ch="${esc(c.id)}">` +
                `<b>${esc(say(c.title))}</b><span>${esc(say(c.intro))}</span></button>`
        )
        .join('');
    const rest = s.planned - list.length;
    const todo =
        rest > 0
            ? `<div class="gd-item is-todo"><b>${esc(T('gd-soon'))}</b><span>${rest}</span></div>`
            : '';
    return (
        pageHead(say(s.title), `${list.length} / ${s.planned}`) +
        `<div class="gd-list">${items}${todo}</div>`
    );
}

// 图名固定(daily-02-review.zh.png),界面改了重拍必然同名 —— URL 上不带指纹的话浏览器与
// CDN 会一直发旧图,而「图跟着界面走、不会变成旧图误导会计」正是这套教程存在的理由。
// 指纹与正文 JSON 同一个(asset-fingerprint),不另造版本号。
function figureHtml(shot: string, caption?: Bilingual): string {
    const cap = caption ? `<figcaption>${esc(say(caption))}</figcaption>` : '';
    const src = withFingerprint(`${SHOT_BASE}${esc(shot)}.${lang()}.png`);
    return (
        `<figure class="gd-fig" data-gd-fig>` +
        `<img alt="" loading="lazy" src="${src}">` +
        cap +
        `</figure>`
    );
}

function chapterHtml(c: GuideChapter): string {
    const steps = c.steps
        .map(
            (s, i) =>
                `<li class="gd-step"><div class="gd-step-n">${i + 1}</div><div class="gd-step-b">` +
                `<p>${esc(say(s.text))}</p>` +
                (s.shot ? figureHtml(s.shot, s.caption) : '') +
                `</div></li>`
        )
        .join('');
    const notes = (c.notes || [])
        .map(
            (n) =>
                `<div class="gd-note is-${n.kind}">` +
                `<span class="gd-note-k">${esc(T(n.kind === 'warn' ? 'gd-note-warn' : 'gd-note-info'))}</span>` +
                `<p>${esc(say(n.text))}</p></div>`
        )
        .join('');
    return (
        pageHead(say(c.title), say(c.intro)) +
        `<ol class="gd-steps">${steps}</ol>` +
        (notes ? `<div class="gd-notes">${notes}</div>` : '')
    );
}

// 配图是 2 倍图,按 naturalWidth/2 还原成设计尺寸,否则小图按物理像素铺开、大图被容器
// 压缩,同一页里比例乱掉。图缺失时降级成占位条,不留裂图。
function guardImages(root: HTMLElement): void {
    root.querySelectorAll<HTMLImageElement>('.gd-fig img').forEach((img) => {
        const fit = (): void => {
            if (img.naturalWidth) img.style.width = img.naturalWidth / 2 + 'px';
        };
        if (img.complete && img.naturalWidth) fit();
        else img.addEventListener('load', fit);
        img.addEventListener('error', () => {
            const fig = img.closest<HTMLElement>('[data-gd-fig]');
            if (fig) fig.classList.add('is-missing');
        });
    });
}

function render(): void {
    const page = document.getElementById('page-guide');
    if (!page) return;
    const s = secId ? meta(secId) : undefined;
    const c = chId ? findLoadedChapter(chId) : null;
    let body: string;
    if (c) body = chapterHtml(c);
    else if (s) body = sectionHtml(s);
    else body = rootHtml();
    page.innerHTML = `<div class="gd">${crumbHtml()}<article class="gd-body">${body}</article></div>`;
    guardImages(page);
    page.scrollTop = 0;
}

// 进教程页的共同前置:绑一次委派 + 拿目录(1 KB)。首页七张卡的章数就在目录里,
// 正文按篇懒加载 —— 点进哪篇才拉哪篇。
async function enterBook(): Promise<void> {
    bindPage();
    await loadIndex();
}

async function goSection(id: string): Promise<void> {
    secId = id;
    const list = await loadSection(id);
    // 该篇只有一章时直接进正文,省掉一次点击。
    chId = list.length === 1 ? list[0].id : '';
    render();
}

function bindPage(): void {
    const page = document.getElementById('page-guide');
    if (!page || page.dataset.gdBound) return;
    page.dataset.gdBound = '1';
    page.addEventListener('click', (e) => {
        const t = e.target as HTMLElement;
        if (t.closest('[data-gd-root]')) {
            secId = '';
            chId = '';
            render();
            return;
        }
        if (t.closest('[data-gd-sec-up]')) {
            chId = '';
            render();
            return;
        }
        const card = t.closest<HTMLElement>('[data-gd-sec]');
        if (card && !card.classList.contains('is-todo')) {
            void goSection(card.dataset.gdSec || '');
            return;
        }
        const ch = t.closest<HTMLElement>('[data-gd-ch]');
        if (ch) {
            chId = ch.dataset.gdCh || '';
            render();
        }
    });
}

// 侧栏点「Express 推送手册」→ 回该手册首页,不停在上次看的那一章。
document.addEventListener('click', (e) => {
    const item = (e.target as HTMLElement).closest<HTMLElement>('.nav-sub-item[data-gd-book]');
    if (!item) return;
    secId = '';
    chId = '';
    const w = window as unknown as WinBridge;
    if (typeof w.routeTo === 'function') w.routeTo('guide');
    void loadGuidePage();
});

// 全站切语言即重渲(整页文本都来自数据,不走 [data-i18n] 那套)。
const bridge = window as unknown as WinBridge;
if (typeof bridge.subscribeI18n === 'function') {
    bridge.subscribeI18n('guide-page', () => {
        if (document.getElementById('page-guide')?.classList.contains('active')) render();
    });
}

async function loadGuidePage(): Promise<void> {
    await enterBook();
    render();
}

// hint = 调用方已知的所属篇(失败码映射表里写着)→ 只拉那一篇;篇里没有再全书兜底。
async function sectionOf(id: string, hint?: string): Promise<string | null> {
    if (hint && (await loadSection(hint)).some((c) => c.id === id)) return hint;
    const hit = await findChapterAcrossBook(id);
    return hit ? hit.sectionId : null;
}

// 报错卡等处深链某一章:window.openGuide('push-upload-batch', 'daily')。
async function openGuide(id: string, sec?: string): Promise<void> {
    const w = window as unknown as WinBridge;
    if (typeof w.routeTo === 'function') w.routeTo('guide');
    await enterBook();
    // 深链的章可能还没写(失败卡上的入口先接线、内容后补)。找不到就回手册首页 ——
    // 不清位置的话会停在上次看的那一章,读者以为点错了。
    const found = await sectionOf(id, sec);
    secId = found || '';
    chId = found ? id : '';
    render();
}

const api = window as unknown as Record<string, unknown>;
api.loadGuidePage = loadGuidePage;
api.openGuide = openGuide;
