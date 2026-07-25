// ============================================================
// 使用教程页(#page-guide)· 三层:篇 → 主题下的章节 → 章节正文,靠面包屑回退。
// 目录不占正文旁边一栏:导航在侧栏(父栏「使用教程」→ 子栏主题),页内只留面包屑。
// 侧栏 7 个子项共用 guide 路由,靠 data-gd-sec 区分是哪一篇。
// 正文只做中泰(会计与老板的实际语言),英/日回落中文;配图同样分中泰两套 ——
// 中文正文配泰文界面图读者对不上号。图走 /static/dist/guide-shots/,随 dist 部署
// (新增 static 根文件不会被 webhook 拾取,见 reset.html 那次 404)。
// ============================================================
import { GUIDE_SECTIONS, findChapter } from './guide-content.js';
import type { Bilingual, GuideChapter, GuideSection, Lang } from './guide-content.js';

const SHOT_BASE = '/static/dist/guide-shots/';

interface WinBridge {
    _currentLang?: string;
    subscribeI18n?: (key: string, fn: () => void) => void;
    t?: (k: string) => string;
    routeTo?: (r: string) => void;
}

function T(k: string): string {
    const w = window as unknown as WinBridge;
    return typeof w.t === 'function' ? w.t(k) : k;
}

function lang(): Lang {
    const w = window as unknown as WinBridge;
    return (w._currentLang || localStorage.getItem('mrpilot_lang')) === 'th' ? 'th' : 'zh';
}

const say = (b: Bilingual): string => b[lang()];

function esc(s: string): string {
    return s.replace(
        /[&<>"']/g,
        (c) =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string
    );
}

let secId = '';
let chId = '';

const findSection = (id: string): GuideSection | undefined =>
    GUIDE_SECTIONS.find((s) => s.id === id);

function crumbHtml(): string {
    const parts = [
        `<button type="button" class="gd-crumb-b" data-gd-root>${esc(T('gd-title'))}</button>`,
    ];
    const sec = secId ? findSection(secId) : undefined;
    if (sec) {
        const last = !chId;
        parts.push('<span class="gd-crumb-sep">/</span>');
        parts.push(
            last
                ? `<span class="gd-crumb-cur">${esc(say(sec.title))}</span>`
                : `<button type="button" class="gd-crumb-b" data-gd-sec-up="${esc(sec.id)}">${esc(say(sec.title))}</button>`
        );
    }
    if (chId) {
        const c = findChapter(chId);
        if (c) {
            parts.push('<span class="gd-crumb-sep">/</span>');
            parts.push(`<span class="gd-crumb-cur">${esc(say(c.title))}</span>`);
        }
    }
    return `<nav class="gd-crumb">${parts.join('')}</nav>`;
}

// 篇总览:没选主题时的落地页,也是面包屑第一级点回来的地方。
function rootHtml(): string {
    const cards = GUIDE_SECTIONS.map((s) => {
        const done = s.chapters.length;
        const meta = done
            ? `${done} / ${s.planned}`
            : `<span class="gd-todo">${esc(T('gd-soon'))}</span>`;
        return (
            `<button type="button" class="gd-card${done ? '' : ' is-todo'}" data-gd-sec="${esc(s.id)}">` +
            `<b>${esc(say(s.title))}</b><span class="gd-card-n">${meta}</span></button>`
        );
    }).join('');
    return (
        `<h1 class="gd-h1">${esc(T('gd-title'))}</h1>` +
        `<p class="gd-intro">${esc(T('gd-sub'))}</p>` +
        `<div class="gd-grid">${cards}</div>`
    );
}

// 主题下的章节列表。未开工的章按定稿章数占位,读者知道这篇还有多少。
function sectionHtml(s: GuideSection): string {
    const items = s.chapters
        .map(
            (c) =>
                `<button type="button" class="gd-item" data-gd-ch="${esc(c.id)}">` +
                `<b>${esc(say(c.title))}</b><span>${esc(say(c.intro))}</span></button>`
        )
        .join('');
    const restCount = s.planned - s.chapters.length;
    const rest =
        restCount > 0
            ? `<div class="gd-item is-todo"><b>${esc(T('gd-soon'))}</b><span>${restCount}</span></div>`
            : '';
    return (
        `<h1 class="gd-h1">${esc(say(s.title))}</h1>` +
        `<p class="gd-intro">${s.chapters.length} / ${s.planned}</p>` +
        `<div class="gd-list">${items}${rest}</div>`
    );
}

function figureHtml(shot: string, caption?: Bilingual): string {
    const cap = caption ? `<figcaption>${esc(say(caption))}</figcaption>` : '';
    return (
        `<figure class="gd-fig" data-gd-fig>` +
        `<img alt="" loading="lazy" src="${SHOT_BASE}${esc(shot)}.${lang()}.png">` +
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
    const notes = c.notes
        .map(
            (n) =>
                `<div class="gd-note is-${n.kind}">` +
                `<span class="gd-note-k">${esc(T(n.kind === 'warn' ? 'gd-note-warn' : 'gd-note-info'))}</span>` +
                `<p>${esc(say(n.text))}</p></div>`
        )
        .join('');
    return (
        `<h1 class="gd-h1">${esc(say(c.title))}</h1>` +
        `<p class="gd-intro">${esc(say(c.intro))}</p>` +
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

// 侧栏子项高亮跟着当前主题走(共用 guide 路由,通用高亮逻辑认不出是哪一篇)。
function syncNav(): void {
    document.querySelectorAll<HTMLElement>('[data-gd-sec]').forEach((el) => {
        if (el.classList.contains('nav-sub-item'))
            el.classList.toggle('active', el.dataset.gdSec === secId);
    });
}

function render(): void {
    const page = document.getElementById('page-guide');
    if (!page) return;
    const sec = secId ? findSection(secId) : undefined;
    const c = chId ? findChapter(chId) : null;
    let body: string;
    if (c) body = chapterHtml(c);
    else if (sec) body = sectionHtml(sec);
    else body = rootHtml();
    page.innerHTML = `<div class="gd">${crumbHtml()}<article class="gd-body">${body}</article></div>`;
    guardImages(page);
    syncNav();
    page.scrollTop = 0;
}

function goSection(id: string): void {
    secId = id;
    // 该篇只有一章时直接进正文,省掉一次点击。
    const s = findSection(id);
    chId = s && s.chapters.length === 1 ? s.chapters[0].id : '';
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
        const up = t.closest<HTMLElement>('[data-gd-sec-up]');
        if (up) {
            chId = '';
            render();
            return;
        }
        const card = t.closest<HTMLElement>('[data-gd-sec]');
        if (card && !card.classList.contains('is-todo')) {
            goSection(card.dataset.gdSec || '');
            return;
        }
        const ch = t.closest<HTMLElement>('[data-gd-ch]');
        if (ch) {
            chId = ch.dataset.gdCh || '';
            render();
        }
    });
}

// 侧栏子项:通用导航只认 data-route,认不出点的是哪一篇 —— 这里补上。
document.addEventListener('click', (e) => {
    const item = (e.target as HTMLElement).closest<HTMLElement>('.nav-sub-item[data-gd-sec]');
    if (!item) return;
    const w = window as unknown as WinBridge;
    goSection(item.dataset.gdSec || '');
    if (typeof w.routeTo === 'function') w.routeTo('guide');
});

// 全站切语言即重渲(整页文本都来自数据,不走 [data-i18n] 那套)。
const w = window as unknown as WinBridge;
if (typeof w.subscribeI18n === 'function') {
    w.subscribeI18n('guide-page', () => {
        if (document.getElementById('page-guide')?.classList.contains('active')) render();
    });
}

// 报错卡等处深链某一章:window.openGuide('push-upload-batch')。
(window as unknown as Record<string, unknown>).openGuide = function openGuide(id: string): void {
    const sec = GUIDE_SECTIONS.find((s) => s.chapters.some((c) => c.id === id));
    if (!sec) return;
    secId = sec.id;
    chId = id;
    const bridge = window as unknown as WinBridge;
    if (typeof bridge.routeTo === 'function') bridge.routeTo('guide');
    bindPage();
    render();
};

(window as unknown as Record<string, unknown>).loadGuidePage = function loadGuidePage(): void {
    bindPage();
    render();
};
