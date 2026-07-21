// ERP 推送复核台 · 逐张核对遮罩(左原图 · 右识别读数)
//
// 复用现有原图查看器 image-viewer.ts 的 imageViewerHtml/(A2b 再接 mountImageViewer 拉真图)。
// 键盘流:Enter 确认并下一张 / ←→ 翻页 / E 跳到改字段 / Esc 关闭。数据/文案由调用方注入。
//
// A2a 范围:遮罩骨架 + 两栏 + 可改字段 + 键盘 + 上下张导航。记账去向/商品去向面板(A4)、
// 真图加载(A2b)、复用/新建裁决(A4)另做。图加载经 mountImage 回调外抛,本模块不 fetch。

import { imageViewerHtml } from './image-viewer';
import {
    routingPanelHtml,
    type RoutingInfo,
    type ItemLine,
    type RoutingNote,
    type RoutingLabels,
} from './erp-review-routing';

export interface VerifyField {
    key: string; // 显示标签
    value: string;
    flag?: boolean; // 低置信 → 高亮提示对照原图
    fk?: string; // 写回字段键(改字段回写数据源时用;缺省=key)
}

export interface VerifyRow {
    id: string;
    docno: string;
    dir: 'in' | 'out';
    fields: VerifyField[];
    balanced?: boolean; // 勾稽平 → 显示通过提示
    routing?: RoutingInfo; // 记账去向(方向/单据/科目)· 有则渲染 ② 段
    lines?: ItemLine[]; // 商品去向逐行 · 有则渲染 ③ 段
    note?: RoutingNote; // 系统提示 / 需人工回答的提问
}

export interface VerifyLabels {
    dirIn: string;
    dirOut: string;
    pos: string; // '{i} / {n}'
    imgFrom: string;
    fieldsCap: string;
    balanceOk: string;
    flagHint: string;
    legEnter: string;
    legNav: string;
    legEdit: string;
    legClose: string;
    skip: string;
    confirm: string;
    viewerHint?: string;
    viewerNoimg?: string;
    viewerLoading?: string;
    routing?: RoutingLabels; // ②③ 段文案(有 routing 数据时必给)
    fzResolvedReuse?: string; // 含 {code}
    fzResolvedNew?: string;
}

export interface VerifyOptions {
    rows: VerifyRow[];
    labels: VerifyLabels;
    // 左栏原图加载:A2b 传 (pane,row)=>mountImageViewer(pane,row.id)。返回 cleanup(解绑
    // window 监听 + 停在飞重试)· 翻页/关闭时调用防泄漏。A2a 不传则留查看器空态。
    mountImage?: (pane: HTMLElement, row: VerifyRow) => (() => void) | void;
    onConfirm?: (id: string) => void;
    onClose?: () => void;
    // 改字段实时回写数据源:(当前行 id, 字段键 fk, 新值)。步③(dms-intake)据此写回 IV.results。
    onFieldEdit?: (rowId: string, key: string, value: string) => void;
}

export interface VerifyController {
    open(index: number): void;
    close(): void;
}

const IC_CHECK = '<svg class="rc-ic sm" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>';
const IC_ALERT =
    '<svg class="rc-ic sm" viewBox="0 0 24 24"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h16.9a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/></svg>';
const IC_LEFT = '<svg class="rc-ic" viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"/></svg>';
const IC_RIGHT = '<svg class="rc-ic" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></svg>';
const IC_X = '<svg class="rc-ic" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>';

function esc(s: string): string {
    return String(s == null ? '' : s).replace(
        /[&<>"']/g,
        (c) =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string
    );
}

function fill(tpl: string, vars: Record<string, string | number>): string {
    return tpl.replace(/\{(\w+)\}/g, (_, k) => esc(String(vars[k] ?? '')));
}

function fieldHtml(f: VerifyField, L: VerifyLabels): string {
    const numeric = /^[\d.,\-—]+$/.test(f.value) || /VAT|税前|合计|税号/.test(f.key);
    return (
        `<div class="rcv-field${f.flag ? ' flag' : ''}"><label>${esc(f.key)}</label>` +
        `<input class="rcv-val${numeric ? ' num' : ''}" data-fk="${esc(f.fk || f.key)}" value="${esc(f.value)}" spellcheck="false" />` +
        (f.flag ? `<div class="rcv-hint">${IC_ALERT}${esc(L.flagHint)}</div>` : '') +
        '</div>'
    );
}

export function createVerifyOverlay(root: HTMLElement, opts: VerifyOptions): VerifyController {
    const L = opts.labels;
    const rows = opts.rows;
    let idx = 0;
    let keyHandler: ((e: KeyboardEvent) => void) | null = null;
    let imgCleanup: (() => void) | null = null; // 上一张原图查看器的解绑器(防监听/重试泄漏)

    root.classList.add('rcv-ov');
    root.innerHTML =
        '<div class="rcv-sheet">' +
        '<div class="rcv-head">' +
        '<span class="rcv-doc"></span><span class="rcv-dir"></span><div class="rc-sp"></div>' +
        '<div class="rcv-nav"><button class="rcv-navbtn" data-nav="prev">' +
        IC_LEFT +
        '</button><span class="rcv-pos"></span><button class="rcv-navbtn" data-nav="next">' +
        IC_RIGHT +
        '</button></div><button class="rcv-x" data-nav="close">' +
        IC_X +
        '</button></div>' +
        '<div class="rcv-body"><div class="rcv-img"><div class="rcv-imgbar">' +
        `<span class="rc-muted rcv-imgfrom"></span></div><div class="rcv-imgpane"></div></div>` +
        '<div class="rcv-fields"></div></div>' +
        '<div class="rcv-foot"><div class="rcv-legend"></div><div class="rc-sp"></div>' +
        '<button class="rc-btn" data-nav="skip"></button>' +
        '<button class="rc-btn ok" data-nav="confirm"></button></div>' +
        '</div>';

    const q = (s: string) => root.querySelector(s) as HTMLElement;
    const docEl = q('.rcv-doc');
    const dirEl = q('.rcv-dir');
    const posEl = q('.rcv-pos');
    const imgFromEl = q('.rcv-imgfrom');
    const imgPane = q('.rcv-imgpane');
    const fieldsEl = q('.rcv-fields');
    const legendEl = q('.rcv-legend');

    imgFromEl.textContent = L.imgFrom;
    (q('[data-nav="skip"]') as HTMLElement).textContent = L.skip;
    (q('[data-nav="confirm"]') as HTMLElement).innerHTML = `${esc(L.confirm)} <kbd>Enter</kbd>`;
    legendEl.innerHTML = [
        `<span><kbd>Enter</kbd> ${esc(L.legEnter)}</span>`,
        `<span><kbd>←</kbd><kbd>→</kbd> ${esc(L.legNav)}</span>`,
        `<span><kbd>E</kbd> ${esc(L.legEdit)}</span>`,
        `<span><kbd>Esc</kbd> ${esc(L.legClose)}</span>`,
    ].join('');

    function paint(): void {
        const r = rows[idx];
        docEl.textContent = r.docno;
        dirEl.className = 'rcv-dir';
        dirEl.innerHTML =
            r.dir === 'in'
                ? `<span class="rc-dir in">${esc(L.dirIn)}</span>`
                : `<span class="rc-dir out">${esc(L.dirOut)}</span>`;
        posEl.textContent = fill(L.pos, { i: idx + 1, n: rows.length });

        if (imgCleanup) imgCleanup();
        imgCleanup = null;
        imgPane.innerHTML = imageViewerHtml({
            hint: L.viewerHint,
            noimg: L.viewerNoimg,
            loading: L.viewerLoading,
        });
        if (opts.mountImage) {
            const c = opts.mountImage(imgPane, r);
            imgCleanup = typeof c === 'function' ? c : null;
        }

        let fh = `<p class="rcv-cap">${esc(L.fieldsCap)}</p>`;
        fh += r.fields.map((f) => fieldHtml(f, L)).join('');
        if (r.balanced) fh += `<div class="rcv-ok">${IC_CHECK}${esc(L.balanceOk)}</div>`;
        if (r.routing && L.routing) fh += routingPanelHtml(r.routing, r.lines, r.note, L.routing);
        fieldsEl.innerHTML = fh;
    }

    function move(n: number): void {
        idx = (idx + n + rows.length) % rows.length;
        paint();
    }

    function commitRow(): void {
        if (opts.onConfirm) opts.onConfirm(rows[idx].id);
        move(1);
    }

    // 拿不准的商品行:R=复用 / N=新建 → 替换裁决块为「已记住」,并把该行定型(翻回来不再问)。
    function resolveFuzzy(reuse: boolean): void {
        const fz = root.querySelector('.rcv-fuzzy') as HTMLElement | null;
        if (!fz) return;
        const line = rows[idx].lines?.find((x) => x.kind === 'fuzzy');
        const msg = reuse
            ? fill(L.fzResolvedReuse || '{code}', { code: line?.guess || '' })
            : L.fzResolvedNew || '';
        fz.innerHTML = `<div class="rcv-resolved">${IC_CHECK}${esc(msg)}</div>`;
        if (line) line.kind = reuse ? 'reuse' : 'new';
    }

    function close(): void {
        if (imgCleanup) imgCleanup();
        imgCleanup = null;
        root.classList.remove('on');
        if (keyHandler) document.removeEventListener('keydown', keyHandler);
        keyHandler = null;
        if (opts.onClose) opts.onClose();
    }

    function onKey(e: KeyboardEvent): void {
        const typing =
            document.activeElement && (document.activeElement as HTMLElement).tagName === 'INPUT';
        if (e.key === 'Escape') {
            close();
        } else if (e.key === 'Enter' && !typing) {
            commitRow();
            e.preventDefault();
        } else if (e.key === 'ArrowRight' && !typing) {
            move(1);
        } else if (e.key === 'ArrowLeft' && !typing) {
            move(-1);
        } else if ((e.key === 'r' || e.key === 'R') && !typing) {
            resolveFuzzy(true);
        } else if ((e.key === 'n' || e.key === 'N') && !typing) {
            resolveFuzzy(false);
        } else if ((e.key === 'e' || e.key === 'E') && !typing) {
            const first = root.querySelector('.rcv-val') as HTMLElement | null;
            if (first) {
                first.focus();
                e.preventDefault();
            }
        }
    }

    root.addEventListener('click', (e) => {
        const fz = (e.target as HTMLElement).closest('[data-fz]') as HTMLElement | null;
        if (fz) {
            resolveFuzzy(fz.dataset.fz === 'reuse');
            return;
        }
        const nav = (e.target as HTMLElement).closest('[data-nav]') as HTMLElement | null;
        if (!nav) return;
        const a = nav.dataset.nav;
        if (a === 'prev') move(-1);
        else if (a === 'next' || a === 'skip') move(1);
        else if (a === 'confirm') commitRow();
        else if (a === 'close') close();
    });

    // 改字段实时回写(委托在 fieldsEl · paint 换 innerHTML 不掉监听)。
    fieldsEl.addEventListener('input', (e) => {
        const inp = (e.target as HTMLElement).closest('.rcv-val') as HTMLInputElement | null;
        if (inp && opts.onFieldEdit)
            opts.onFieldEdit(rows[idx].id, inp.dataset.fk || '', inp.value);
    });

    function open(i: number): void {
        idx = Math.max(0, Math.min(i, rows.length - 1));
        root.classList.add('on');
        paint();
        keyHandler = onKey;
        document.addEventListener('keydown', keyHandler);
    }

    return { open, close };
}
