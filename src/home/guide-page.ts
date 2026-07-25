// ============================================================
// 使用教程页(#page-guide)· 左目录 + 右正文
// 教程正文只做中泰两种(会计与老板的实际语言),全站另有英/日 —— 那两种回落中文,
// 并在页内给出独立的语种切换,不劫持全站语言设置。
// 图走 /static/dist/guide-shots/<shot>.png:随 dist 一起部署(新增 static 根文件不会被
// webhook 拾取,见 reset.html 那次 404)。图缺失时降级成占位条,不留裂图。
// ============================================================
import { GUIDE_SECTIONS, findChapter, firstChapterId } from './guide-content.js';
import type { Bilingual, GuideChapter, Lang } from './guide-content.js';

const SHOT_BASE = '/static/dist/guide-shots/';

interface WinBridge {
    _currentLang?: string;
    subscribeI18n?: (key: string, fn: () => void) => void;
    t?: (k: string) => string;
}

function T(k: string): string {
    const w = window as unknown as WinBridge;
    return typeof w.t === 'function' ? w.t(k) : k;
}

// 正文只备中泰两种:全站切到泰文出泰文,其余语种(中/英/日)一律出中文。
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

let active = '';

function tocHtml(): string {
    const secs = GUIDE_SECTIONS.map((s) => {
        const items = s.chapters.length
            ? s.chapters
                  .map(
                      (c) =>
                          `<button type="button" class="gd-ch${c.id === active ? ' is-on' : ''}" data-gd-ch="${esc(c.id)}">${esc(say(c.title))}</button>`
                  )
                  .join('')
            : `<div class="gd-ch is-todo">${esc(T('gd-soon'))}</div>`;
        return (
            `<div class="gd-sec">` +
            `<div class="gd-sec-t">${esc(say(s.title))}<span class="gd-sec-n">${s.planned}</span></div>` +
            items +
            `</div>`
        );
    }).join('');
    return (
        `<div class="gd-toc-head">${esc(T('gd-title'))}</div>` +
        `<div class="gd-toc-sub">${esc(T('gd-sub'))}</div>` +
        secs
    );
}

// 图分语种:中文正文配中文界面图,泰文配泰文,否则读者对不上号。
function figureHtml(shot: string, caption?: Bilingual): string {
    const cap = caption ? `<figcaption>${esc(say(caption))}</figcaption>` : '';
    return (
        `<figure class="gd-fig" data-gd-fig>` +
        `<img alt="" loading="lazy" src="${SHOT_BASE}${esc(shot)}.${lang()}.png">` +
        cap +
        `</figure>`
    );
}

function bodyHtml(c: GuideChapter): string {
    const steps = c.steps
        .map(
            (s, i) =>
                `<li class="gd-step">` +
                `<div class="gd-step-n">${i + 1}</div>` +
                `<div class="gd-step-b">` +
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

// 配图是 2 倍图,按 naturalWidth/2 还原成设计尺寸 —— 否则小图按物理像素铺开,
// 大图被容器压缩,同一页里图的比例乱掉。
// 图未生成时不留裂图:换成一条占位,读者知道这里应该有图而不是页面坏了。
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
    if (!active) active = firstChapterId();
    const c = active ? findChapter(active) : null;
    page.innerHTML =
        `<div class="gd">` +
        `<aside class="gd-toc">${tocHtml()}</aside>` +
        `<article class="gd-body">${c ? bodyHtml(c) : ''}</article>` +
        `</div>`;
    guardImages(page);
    page.querySelector('.gd-body')?.scrollTo?.(0, 0);
}

function bind(): void {
    const page = document.getElementById('page-guide');
    if (!page || page.dataset.gdBound) return;
    page.dataset.gdBound = '1';
    page.addEventListener('click', (e) => {
        const t = e.target as HTMLElement;
        const ch = t.closest<HTMLElement>('[data-gd-ch]');
        if (ch) {
            active = ch.dataset.gdCh || '';
            render();
        }
    });
}

// 全站切语言即重渲(整页文本都来自数据,不走 [data-i18n] 那套)。
const w = window as unknown as WinBridge;
if (typeof w.subscribeI18n === 'function') {
    w.subscribeI18n('guide-page', () => {
        if (document.getElementById('page-guide')?.classList.contains('active')) render();
    });
}

(window as unknown as Record<string, unknown>).loadGuidePage = function loadGuidePage(): void {
    bind();
    render();
};
