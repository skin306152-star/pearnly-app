// 平台业态套餐 · PO-PP3 · 设置「业务/模块」页(照设计稿 03-设置-业务模块)。
// page-settings.ts 只注入一个空壳 pane(data-pane="modules")+ tab 按钮;逻辑全在本模块,
// 防 page-settings 破 500。owner 专属(tab 复用 .set-tab-owner-only 显隐机制)。
//
// 进 tab → GET /api/me/modules → 渲 bizbar(当前业态只读展示)+ 底座常开卡 + 7 模块 toggle。
// toggle → 乐观更新 + PUT /api/me/modules/{key} + 失败回滚 + posErrMsg → applyModuleNav 刷新导航。
// 「切换业态」自选入口已下架(Zihao 2026-07-11 拍板 · 平台业态套餐不再自选);业态只能靠
// 运营侧(Earn 开通 / 注册流默认 firm)变更,本页只展示当前值。
// 视觉照搬设计稿(主蓝 var(--btn-blue))· 作用域 .modset · 信封 body.ok→data。
/* global t, showToast, escapeHtml, apiGet, apiPut */
import { posErrMsg } from './inventory-common';

// 业务模块 toggle 列表(顺序照 03 设计稿)· 图标内嵌 SVG path(stroke currentColor)。
const MODULES: { key: string; svg: string }[] = [
    {
        key: 'sales',
        svg: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    },
    { key: 'inventory', svg: '<path d="M20 7L12 3 4 7m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10"/>' },
    {
        key: 'pos',
        svg: '<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
    },
    {
        key: 'expense',
        svg: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>',
    },
    {
        key: 'recon',
        svg: '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    },
    {
        key: 'receivable',
        svg: '<path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    },
    {
        key: 'knowledge',
        svg: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    },
];

// 业态 → bizbar 图标(零售购物袋为缺省 · 与 PP2 卡片图标语义对齐)。
const BIZ_ICONS: Record<string, string> = {
    firm: 'M3 21h18M5 21V7l8-4v18M19 21V11l-6-4',
    retail: 'M3 9l1-5h16l1 5M4 9v11a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V9M9 21v-6h6v6',
    pharmacy: 'M10.5 20.5 3.5 13.5a5 5 0 0 1 7-7l7 7a5 5 0 0 1-7 7zM8.5 8.5l7 7',
    restaurant: 'M3 2v7a3 3 0 0 0 6 0V2M6 9v13M18 2v20M18 9c2 0 3-1 3-4s-1-3-3-3',
    service: 'M12 7a4 4 0 1 0 0 0M5.5 21a6.5 6.5 0 0 1 13 0',
    b2b: 'M1 3h15v13H1zM16 8h4l3 3v5h-7M5.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
};

const STYLE = `
.modset{max-width:680px;}
.modset .bizbar{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:16px;}
.modset .bizbar .ico{width:40px;height:40px;border-radius:11px;background:var(--blue-weak);color:var(--btn-blue,#0E7C66);display:grid;place-items:center;flex:0 0 40px;}
.modset .bizbar .info{flex:1;min-width:0;}
.modset .bizbar .info .a{font-size:12px;color:var(--ink2);}
.modset .bizbar .info .b{font-weight:700;font-size:15px;color:var(--ink);}
.modset .mcard{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-bottom:16px;}
.modset .mcard .h{padding:12px 16px;border-bottom:1px solid var(--line2);font-weight:700;font-size:13.5px;color:var(--ink);}
.modset .mod{display:flex;align-items:center;gap:12px;padding:13px 16px;border-bottom:1px solid var(--line2);}
.modset .mod:last-child{border-bottom:0;}
.modset .mod .mi{width:34px;height:34px;border-radius:9px;background:var(--line2);color:var(--ink2);display:grid;place-items:center;flex:0 0 34px;}
.modset .mod .tx{flex:1;min-width:0;}
.modset .mod .tx .n{font-size:14px;font-weight:600;color:var(--ink);}
.modset .mod .tx .d{font-size:12px;color:var(--ink2);margin-top:2px;}
.modset .mod .tag{font-size:10.5px;color:var(--ink3);flex:0 0 auto;}
.modset .sw{width:42px;height:24px;border-radius:999px;flex:0 0 42px;position:relative;cursor:pointer;transition:.15s;background:var(--ink-4);}
.modset .sw::after{content:"";position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;background:var(--card);transition:.15s;box-shadow:0 1px 3px rgba(0,0,0,.25);}
.modset .mod.on .sw{background:var(--btn-blue,#0E7C66);}.modset .mod.on .sw::after{left:20px;}
.modset .mod.lock .sw{background:var(--blue-200);cursor:not-allowed;}.modset .mod.lock .sw::after{left:20px;}
.modset .mod.lock .tx,.modset .mod.off .tx .n{color:var(--ink2);}
.modset .sw.busy{opacity:.5;pointer-events:none;}
.modset .note{font-size:12.5px;color:var(--ink2);background:#f8f8f5;border:1px solid var(--line);border-radius:10px;padding:11px 13px;line-height:1.7;}
.modset .note b{color:var(--ink);}
.modset .modset-load{padding:30px 0;text-align:center;color:var(--ink3);font-size:13px;}
`;

function ensureStyle(): void {
    if (document.getElementById('modset-style')) return;
    const st = document.createElement('style');
    st.id = 'modset-style';
    st.textContent = STYLE;
    document.head.appendChild(st);
}

function icon(svg: string): string {
    return `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${svg}</svg>`;
}

function modRow(key: string, enabled: boolean): string {
    const m = MODULES.find((x) => x.key === key)!;
    return `<div class="mod ${enabled ? 'on' : 'off'}" data-module-key="${key}">
        <div class="mi">${icon(m.svg)}</div>
        <div class="tx"><div class="n">${escapeHtml(t('mod.' + key))}</div><div class="d">${escapeHtml(
            t('modset.' + key + '.d')
        )}</div></div>
        ${enabled ? '' : `<span class="tag">${escapeHtml(t('onb.tag_off'))}</span>`}
        <span class="sw" role="switch" aria-checked="${enabled}"></span>
    </div>`;
}

function bizLabel(bt: string | null): string {
    return bt ? t('biz.' + bt) : t('set.biz_none');
}

function render(
    pane: HTMLElement,
    data: { modules: Record<string, { enabled?: boolean }>; business_type: string | null }
): void {
    const bt = data.business_type;
    const ipath = (bt && BIZ_ICONS[bt]) || BIZ_ICONS.retail;
    const rows = MODULES.map((m) =>
        modRow(m.key, !!(data.modules[m.key] && data.modules[m.key].enabled))
    ).join('');
    pane.innerHTML = `<div class="modset">
        <div class="bizbar">
            <div class="ico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="${ipath}"/></svg></div>
            <div class="info"><div class="a">${escapeHtml(t('set.cur_biz'))}</div><div class="b" id="modset-biz">${escapeHtml(
                bizLabel(bt)
            )}</div></div>
        </div>
        <div class="mcard">
            <div class="h">${escapeHtml(t('set.base_section'))}</div>
            <div class="mod lock">
                <div class="mi"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
                <div class="tx"><div class="n">${escapeHtml(t('set.base_locked_title'))}</div><div class="d">${escapeHtml(
                    t('set.base_locked_sub')
                )}</div></div>
                <span class="tag">${escapeHtml(t('onb.base_tag'))}</span><span class="sw"></span>
            </div>
        </div>
        <div class="mcard"><div class="h">${escapeHtml(t('set.biz_mods'))}</div>${rows}</div>
        <div class="note">${t('set.module_note')}</div>
    </div>`;
}

async function toggle(row: HTMLElement, sw: HTMLElement): Promise<void> {
    const key = row.dataset.moduleKey;
    if (!key || sw.classList.contains('busy')) return;
    const wasOn = row.classList.contains('on');
    const next = !wasOn;
    // 乐观更新
    setRowState(row, next);
    sw.classList.add('busy');
    const res = await apiPut('/api/me/modules/' + encodeURIComponent(key), { enabled: next });
    sw.classList.remove('busy');
    if (res && res.ok === true) {
        if (typeof window.applyModuleNav === 'function') window.applyModuleNav();
    } else {
        setRowState(row, wasOn); // 回滚
        const code = (res && res.detail && res.detail.code) || (res && res.error && res.error.code);
        showToast(posErrMsg(code || 'pos.unexpected', 'pos.unexpected'), 'error');
    }
}

function setRowState(row: HTMLElement, on: boolean): void {
    row.classList.toggle('on', on);
    row.classList.toggle('off', !on);
    const sw = row.querySelector('.sw');
    if (sw) sw.setAttribute('aria-checked', String(on));
    let tag = row.querySelector('.tag');
    if (on && tag) tag.remove();
    if (!on && !tag) {
        tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = t('onb.tag_off');
        row.insertBefore(tag, row.querySelector('.sw'));
    }
}

let bound = false;

async function loadModuleSettings(): Promise<void> {
    const pane = document.querySelector<HTMLElement>('.settings-pane[data-pane="modules"]');
    if (!pane) return;
    ensureStyle();
    pane.innerHTML = `<div class="modset"><div class="modset-load">${escapeHtml(t('set.loading'))}</div></div>`;
    let data: { modules: Record<string, { enabled?: boolean }>; business_type: string | null };
    try {
        const body = await apiGet('/api/me/modules');
        data = (body && body.data) || { modules: {}, business_type: null };
    } catch (_) {
        pane.innerHTML = `<div class="modset"><div class="modset-load">${escapeHtml(
            t('set.load_failed')
        )}</div></div>`;
        return;
    }
    render(pane, data);
    if (bound) return;
    bound = true;
    // 委托:toggle 开关(pane 常驻 · 绑一次)。
    pane.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        const sw = target.closest('.sw') as HTMLElement | null;
        const row = target.closest('.mod:not(.lock)') as HTMLElement | null;
        if (sw && row) toggle(row, sw);
    });
}

window.loadModuleSettings = loadModuleSettings;
