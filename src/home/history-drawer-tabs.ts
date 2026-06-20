// 识别记录抽屉 · 销项重做(对齐草稿)· 把共享 openDrawer 渲好的单滚动 body 重排成
// 4-tab(概览与编辑 / 商品明细 / 原始文件 / 修改记录)+ 顶部汇总条(买方/总额/状态)。
//
// 只在 history 模式由 openHistoryDrawer 调一次 · 纯 DOM 搬运(节点连同事件/状态一起 append ·
// 字段编辑/RD 校验/保存/推送逻辑全不改)· 共享抽屉的其它消费方(对账中心)完全不受影响。
/* global escapeHtml, token, t, showToast */

type HistDetail = {
    id?: string;
    filename?: string;
    page_count?: number;
    confidence?: string;
    created_at?: string;
    fields_edited_at?: string | null;
    edit_count?: number;
    [k: string]: unknown;
};

function _fieldVal(body: HTMLElement, key: string): string {
    const el = body.querySelector(`[data-field="${key}"]`) as HTMLInputElement | null;
    return (el && el.value ? el.value : '').trim();
}

// 与后端 list_status 同口径派生三态(抽屉无后端 status · 读已渲染字段算)
function _deriveStatus(body: HTMLElement, conf: string | undefined): string {
    const total = _fieldVal(body, 'total_amount');
    const inv = _fieldVal(body, 'invoice_number');
    const seller = _fieldVal(body, 'seller_name');
    if (!total && !inv && !seller) return 'failed';
    if (conf === 'high' && total && inv) return 'confirmed';
    return 'pending';
}

function _fmtTime(iso?: string): string {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return escapeHtml(iso);
    const p = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function _filePanel(detail: HistDetail): string {
    const fname = escapeHtml(detail.filename || '');
    const pages = detail.page_count
        ? `<div class="hd-file-meta">${escapeHtml(t('hd-file-pages', { n: detail.page_count }))}</div>`
        : '';
    return `
        <div class="hd-file">
            <svg class="hd-file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4"/><path d="M9 12h6M9 16h4"/></svg>
            <div class="hd-file-name">${fname}</div>
            ${pages}
            <button class="btn btn-ghost" id="hd-file-dl" data-hd-dl="${escapeHtml(detail.id || '')}" type="button">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v8M5 7l3 3 3-3M3 13h10"/></svg>
                <span>${escapeHtml(t('hd-file-download'))}</span>
            </button>
            <div class="hd-file-hint">${escapeHtml(t('hd-file-hint'))}</div>
        </div>`;
}

function _timelinePanel(detail: HistDetail): string {
    const items: string[] = [];
    const recDetail = detail.page_count
        ? ' · ' + escapeHtml(t('hd-file-pages', { n: detail.page_count }))
        : '';
    items.push(
        `<div class="hd-tl-item"><div class="hd-tl-dot">✓</div><div class="hd-tl-copy"><b>${escapeHtml(t('hd-tl-recognized'))}</b><span>${_fmtTime(detail.created_at)}${recDetail}</span></div></div>`
    );
    if (detail.fields_edited_at) {
        items.push(
            `<div class="hd-tl-item"><div class="hd-tl-dot">✎</div><div class="hd-tl-copy"><b>${escapeHtml(t('hd-tl-edited', { n: detail.edit_count || 1 }))}</b><span>${_fmtTime(detail.fields_edited_at)}</span></div></div>`
        );
    }
    items.push(
        `<div class="hd-tl-item"><div class="hd-tl-dot">↑</div><div class="hd-tl-copy"><b>${escapeHtml(t('hd-tl-uploaded'))}</b><span>${_fmtTime(detail.created_at)}</span></div></div>`
    );
    return `<div class="hd-timeline">${items.join('')}</div>`;
}

function historizeDrawer(detail: HistDetail) {
    const body = document.getElementById('drawer-body');
    if (!body || body.querySelector('.hd-tabs')) return; // 每次 open 都重建 body · 有 .hd-tabs 即已处理

    const decision = body.querySelector('.drawer-decision-zone');
    const sections = Array.from(body.querySelectorAll('.drawer-section'));
    const rawText = body.querySelector('details.raw-text');
    const saveBar = document.getElementById('drawer-history-save');
    const itemsSec = sections.find((s) =>
        s.querySelector('.drawer-items-header, .drawer-items-empty')
    );

    // 顶部汇总条:买方 / 总金额 / 状态(状态客户端派生 · 与后端同口径)
    const buyer = _fieldVal(body, 'buyer_name');
    const total = _fieldVal(body, 'total_amount');
    const st = _deriveStatus(body, detail.confidence);
    const stKey =
        st === 'confirmed'
            ? 'history-st-confirmed'
            : st === 'failed'
              ? 'history-st-failed'
              : 'history-st-pending';
    const strip = document.createElement('div');
    strip.className = 'hd-summary';
    strip.innerHTML = `
        <div class="hd-stat"><label>${escapeHtml(t('hd-sum-buyer'))}</label><strong>${buyer ? escapeHtml(buyer) : '—'}</strong></div>
        <div class="hd-stat"><label>${escapeHtml(t('hd-sum-total'))}</label><strong>${total ? '฿' + escapeHtml(total) : '—'}</strong></div>
        <div class="hd-stat"><label>${escapeHtml(t('hd-sum-status'))}</label><strong><span class="hist-status-pill ${st}">${escapeHtml(t(stKey))}</span></strong></div>`;

    // tab 条
    const TABS: Array<[string, string]> = [
        ['overview', 'hd-tab-overview'],
        ['items', 'hd-tab-items'],
        ['file', 'hd-tab-file'],
        ['history', 'hd-tab-history'],
    ];
    const tabsBar = document.createElement('div');
    tabsBar.className = 'hd-tabs';
    tabsBar.innerHTML = TABS.map(
        ([v, k], i) =>
            `<button class="hd-tab${i === 0 ? ' active' : ''}" data-hd-view="${v}" type="button">${escapeHtml(t(k))}</button>`
    ).join('');

    // 4 个面板
    const panels: Record<string, HTMLElement> = {};
    const panelWrap = document.createElement('div');
    panelWrap.className = 'hd-panels';
    for (const [v] of TABS) {
        const p = document.createElement('div');
        p.className = 'hd-panel' + (v === 'overview' ? ' active' : '');
        p.dataset.hdPanel = v;
        panels[v] = p;
        panelWrap.appendChild(p);
    }

    // 搬运:概览=决策区+基本/卖方/买方/备注;明细=商品+完整识别文本;原始文件/修改记录新建
    if (decision) panels.overview.appendChild(decision);
    sections.forEach((s) => {
        (s === itemsSec ? panels.items : panels.overview).appendChild(s);
    });
    if (rawText) panels.items.appendChild(rawText);
    panels.file.innerHTML = _filePanel(detail);
    panels.history.innerHTML = _timelinePanel(detail);

    // 组装:summary + tabs + panels 插在 saveBar 前(saveBar 仍是末尾页脚)
    const root = document.createElement('div');
    root.className = 'hd-root';
    root.append(strip, tabsBar, panelWrap);
    if (saveBar) body.insertBefore(root, saveBar);
    else body.appendChild(root);

    // tab 切换
    tabsBar.addEventListener('click', (e) => {
        const btn = (e.target as HTMLElement).closest('.hd-tab') as HTMLElement | null;
        if (!btn) return;
        const v = btn.dataset.hdView;
        tabsBar
            .querySelectorAll('.hd-tab')
            .forEach((b) => b.classList.toggle('active', b === btn));
        panelWrap
            .querySelectorAll('.hd-panel')
            .forEach((p) => p.classList.toggle('active', (p as HTMLElement).dataset.hdPanel === v));
    });

    // 原始文件下载(带鉴权 · blob)
    const dl = panels.file.querySelector('#hd-file-dl') as HTMLButtonElement | null;
    if (dl) {
        dl.addEventListener('click', async () => {
            const id = dl.dataset.hdDl;
            if (!id) return;
            dl.disabled = true;
            try {
                const resp = await fetch(`/api/history/${encodeURIComponent(id)}/pdf`, {
                    headers: { Authorization: 'Bearer ' + token },
                });
                if (!resp.ok) throw new Error('no pdf');
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = (detail.filename || 'invoice').replace(/(\.pdf)?$/i, '.pdf');
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(url), 5000);
                showToast(t('history-download-pdf-ok'), 'success');
            } catch (_e) {
                showToast(t('history-download-pdf-fail'), 'error');
            } finally {
                dl.disabled = false;
            }
        });
    }
}

window.historizeDrawer = historizeDrawer;
