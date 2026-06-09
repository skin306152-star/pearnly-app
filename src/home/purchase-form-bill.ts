// 进项表单左栏(票图 + 凭据)+ 票图鉴权加载 + 放大查看。
// 从 purchase-form.ts 拆出(单一职责 · 守 <500 闸)· t/escapeHtml 走全局桥。
/* global t, escapeHtml */
import { fetchAuthedBlobUrl } from './purchase-common.js';
import type { FormState } from './purchase-form.js';

const ICON_DOC =
    '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="13" y2="16"/></svg>';

// 左栏 HTML:票图卡(有图 <img>/无图占位)+ 凭据卡。
export function leftColHtml(st: FormState): string {
    const aiMark = st.aiFields
        ? `<span class="aimark">${escapeHtml(t('pur-ai-read'))} ${st.aiFields}</span>`
        : '';
    const billInner = st.billUrl
        ? `<img id="pur-bill-img" class="billimg" alt="${escapeHtml(t('pur-bill'))}" />`
        : ICON_DOC;
    const zoomBtn = st.billUrl
        ? `<button class="btn sm" id="pur-zoom">${escapeHtml(t('pur-zoom'))}</button>`
        : '';
    return `<div class="col">
        <div class="card"><div class="hd">${escapeHtml(t('pur-bill'))}</div><div class="bd">
            <div class="img" id="pur-bill-box">${billInner}${aiMark}</div>
            <div class="seg2"><button class="btn sm" id="pur-reshoot">${escapeHtml(t('pur-reshoot'))}</button>${zoomBtn}</div>
        </div></div>
        <div class="card"><div class="hd">${escapeHtml(t('pur-vouchers-hd'))}</div><div class="bd">
            <div class="hint">${escapeHtml(t('pur-sub-receipt-hint'))}</div>
            <button class="btn full ghost mt" id="pur-gen-receipt" style="margin-bottom:8px;">+ ${escapeHtml(t('pur-gen-receipt'))}</button>
            <button class="btn full ghost" id="pur-attach">+ ${escapeHtml(t('pur-attach'))}</button>
            <div class="field mt"><label>${escapeHtml(t('pur-requester'))}</label><div class="inp"><input class="fin" data-fld="requester" value="${escapeHtml(st.requester)}" placeholder="—"></div></div>
        </div></div>
    </div>`;
}

// 加载票图:本地 blob 直接用;鉴权 url 取 blob 显示。写 dataset.viewSrc 供放大复用,
// 点票图本身也开原生看图器。
export async function mountBillImage(billUrl: string): Promise<void> {
    const img = document.getElementById('pur-bill-img') as HTMLImageElement | null;
    if (!img || !billUrl) return;
    let src = billUrl;
    if (!src.startsWith('blob:')) {
        try {
            src = await fetchAuthedBlobUrl(billUrl);
        } catch (_) {
            return; // 取图失败 · 保持占位图标
        }
    }
    img.src = src;
    img.dataset.viewSrc = src;
    img.onclick = () => window.open(src, '_blank');
}

// 「放大看」→ blob 新标签 = 浏览器原生缩放/旋转/拖动查看器。
export function wireBillZoom(): void {
    const btn = document.getElementById('pur-zoom');
    if (!btn) return;
    btn.onclick = () => {
        const img = document.getElementById('pur-bill-img') as HTMLImageElement | null;
        const src = (img && img.dataset.viewSrc) || '';
        if (src) window.open(src, '_blank');
    };
}
