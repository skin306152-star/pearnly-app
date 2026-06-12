// 平台业态套餐 · PO-PP2 · 业态选择器弹窗(照设计稿 01-注册业态选择)· window.openBusinessPicker
// 复用入口:① 侧栏「可开启功能 →」(nav-enroll)② 设置·切换业态(future 屏C)③ 新注册首次(future 自动触发)。
// 选业态 → 右侧实时镜像预设(02 §1 · 诚实展示将开的模块)→「应用」PUT /api/me/onboarding → applyModuleNav 重渲导航。
// 视觉照搬设计稿令牌(主蓝 var(--btn-blue))· 作用域 .pbiz · 信封 body.ok→data · 失败 posErrMsg。owner 专属。
/* global t, token, showToast, escapeHtml */
import { posErrMsg } from './inventory-common';

// 业态 → 默认开的 module_key(docs/platform-onboarding/02 §1 的前端镜像 · 诚实预设)。
// 引导闭环向导步① 复用 TYPES(同一份业态卡数据 · 单一来源 · 防漂移)。
export const PRESETS: Record<string, string[]> = {
    firm: ['sales', 'expense', 'recon', 'knowledge'],
    retail: ['sales', 'inventory', 'pos'],
    pharmacy: ['sales', 'inventory', 'pos'],
    restaurant: ['sales', 'inventory', 'pos'],
    service: ['sales', 'expense'],
    b2b: ['sales', 'inventory', 'receivable', 'expense'],
};
const ALL_MODULES = ['sales', 'expense', 'recon', 'inventory', 'pos', 'receivable', 'knowledge'];
const BASE = ['product', 'client', 'workbench', 'ai'];
export const TYPES: { id: string; icon: string }[] = [
    { id: 'firm', icon: 'M3 21h18M5 21V7l8-4v18M19 21V11l-6-4' },
    { id: 'retail', icon: 'M3 9l1-5h16l1 5M4 9v11a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V9M9 21v-6h6v6' },
    { id: 'pharmacy', icon: 'M10.5 20.5 3.5 13.5a5 5 0 0 1 7-7l7 7a5 5 0 0 1-7 7zM8.5 8.5l7 7' },
    { id: 'restaurant', icon: 'M3 2v7a3 3 0 0 0 6 0V2M6 9v13M18 2v20M18 9c2 0 3-1 3-4s-1-3-3-3' },
    { id: 'service', icon: 'M12 7a4 4 0 1 0 0 0M5.5 21a6.5 6.5 0 0 1 13 0' },
    {
        id: 'b2b',
        icon: 'M1 3h15v13H1zM16 8h4l3 3v5h-7M5.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
    },
];

let selected = 'retail';
let onDone: (() => void) | null = null;

const PB = '.pbiz';

function renderPanel(): void {
    const on = PRESETS[selected] || [];
    const presetEl = document.querySelector(PB + ' #pbiz-preset');
    if (presetEl) presetEl.textContent = t('biz.' + selected) + ' ' + t('onb.preset_suffix');
    const row = (label: string, kind: 'base' | 'on' | 'off') =>
        `<div class="mod ${kind}"><span class="sw"></span>${escapeHtml(label)}<span class="tag">${
            kind === 'base' ? t('onb.base_tag') : kind === 'on' ? t('onb.tag_on') : t('onb.tag_off')
        }</span></div>`;
    const mods = document.querySelector(PB + ' #pbiz-mods');
    if (mods)
        mods.innerHTML =
            `<div class="grp">${escapeHtml(t('onb.base'))}</div>` +
            BASE.map((m) => row(t('mod.' + m), 'base')).join('') +
            `<div class="grp">${escapeHtml(t('onb.biz_mods'))}</div>` +
            ALL_MODULES.map((m) => row(t('mod.' + m), on.includes(m) ? 'on' : 'off')).join('');
}

function renderCards(): string {
    return TYPES.map(
        (ty) =>
            `<div class="type${ty.id === selected ? ' on' : ''}" data-id="${ty.id}">
        <div class="ico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="${ty.icon}"/></svg></div>
        <div class="nm">${escapeHtml(t('biz.' + ty.id))}</div>
        <div class="ds">${escapeHtml(t('biz.' + ty.id + '.desc'))}</div>
      </div>`
    ).join('');
}

// 作用域样式(注入式 · 不进 .css 打包管线 · 主蓝走 var(--btn-blue) 对齐全站按钮规范)。
const STYLE = `
.pbiz-mask{position:fixed;inset:0;background:rgba(17,24,39,.5);backdrop-filter:blur(3px);display:none;align-items:center;justify-content:center;z-index:1200;padding:20px;}
.pbiz-mask.show{display:flex;}
.pbiz{width:880px;max-width:96vw;max-height:92vh;overflow:auto;background:var(--card);border-radius:18px;padding:26px 28px 22px;position:relative;box-shadow:0 24px 60px rgba(0,0,0,.25);}
.pbiz-x{position:absolute;top:16px;right:18px;border:0;background:var(--line2);color:var(--ink2);width:30px;height:30px;border-radius:8px;font-size:18px;cursor:pointer;line-height:1;}
.pbiz h1{font-size:21px;margin:0 0 4px;color:var(--ink);}
.pbiz .sub{color:var(--ink2);font-size:13px;margin-bottom:20px;}
.pbiz .cols{display:grid;grid-template-columns:1.35fr 1fr;gap:20px;align-items:start;}
.pbiz .types{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.pbiz .type{border:1.5px solid var(--line);border-radius:14px;padding:14px;cursor:pointer;transition:.12s;}
.pbiz .type:hover{border-color:var(--blue-200);}
.pbiz .type.on{border-color:var(--btn-blue,#0E7C66);background:var(--blue-weak);}
.pbiz .type .ico{width:38px;height:38px;border-radius:11px;background:var(--card);border:1px solid var(--line);display:grid;place-items:center;color:var(--btn-blue,#0E7C66);margin-bottom:9px;}
.pbiz .type.on .ico{background:var(--btn-blue,#0E7C66);color:#fff;border-color:var(--btn-blue,#0E7C66);}
.pbiz .type .nm{font-weight:700;font-size:14px;color:var(--ink);}
.pbiz .type .ds{font-size:11.5px;color:var(--ink2);margin-top:4px;line-height:1.5;}
.pbiz .panel{border:1px solid var(--line);border-radius:16px;overflow:hidden;position:sticky;top:0;}
.pbiz .panel .h{padding:13px 16px;border-bottom:1px solid var(--line2);font-weight:700;font-size:14px;color:var(--ink);}
.pbiz .panel .h .s{color:var(--ink2);font-weight:400;font-size:12px;margin-top:2px;}
.pbiz .mods{padding:4px 16px;max-height:300px;overflow:auto;}
.pbiz .mod{display:flex;align-items:center;gap:11px;padding:8px 0;border-bottom:1px solid var(--line2);font-size:13.5px;color:var(--ink);}
.pbiz .mod:last-child{border-bottom:0;}
.pbiz .mod .sw{width:34px;height:20px;border-radius:999px;flex:0 0 34px;position:relative;}
.pbiz .mod .sw::after{content:"";position:absolute;top:2px;width:16px;height:16px;border-radius:50%;background:var(--card);box-shadow:0 1px 3px rgba(0,0,0,.2);}
.pbiz .mod.on .sw{background:var(--btn-blue,#0E7C66);}.pbiz .mod.on .sw::after{left:16px;}
.pbiz .mod.off .sw{background:var(--ink-4);}.pbiz .mod.off .sw::after{left:2px;}
.pbiz .mod.off{color:var(--ink3);}
.pbiz .mod.base .sw{background:var(--blue-200);}.pbiz .mod.base{color:var(--ink2);}
.pbiz .mod .tag{margin-left:auto;font-size:10.5px;color:var(--ink3);}
.pbiz .grp{font-size:11px;color:var(--ink3);text-transform:uppercase;letter-spacing:.5px;padding:10px 0 4px;}
.pbiz .go{margin:14px 16px 16px;width:calc(100% - 32px);height:46px;border:0;border-radius:11px;background:var(--btn-blue,#0E7C66);color:#fff;font-weight:700;font-size:15px;cursor:pointer;}
.pbiz .go:disabled{background:#c7cdd6;cursor:not-allowed;}
@media(max-width:720px){.pbiz .cols{grid-template-columns:1fr;}.pbiz .types{grid-template-columns:1fr 1fr;}}
`;

function ensureModal(): HTMLElement {
    let m = document.getElementById('pbiz-mask');
    if (m) return m;
    if (!document.getElementById('pbiz-style')) {
        const st = document.createElement('style');
        st.id = 'pbiz-style';
        st.textContent = STYLE;
        document.head.appendChild(st);
    }
    m = document.createElement('div');
    m.id = 'pbiz-mask';
    m.className = 'pbiz-mask';
    m.innerHTML = `<div class="pbiz">
    <button class="pbiz-x" id="pbiz-close" aria-label="close">&times;</button>
    <h1 id="pbiz-title"></h1>
    <div class="sub" id="pbiz-sub"></div>
    <div class="cols">
      <div class="types" id="pbiz-types"></div>
      <div class="panel">
        <div class="h">${escapeHtml(t('onb.will_open'))}<div class="s" id="pbiz-preset"></div></div>
        <div class="mods" id="pbiz-mods"></div>
        <button class="go" id="pbiz-go"></button>
      </div>
    </div>
  </div>`;
    document.body.appendChild(m);
    m.addEventListener('click', (e) => {
        if (e.target === m) close();
    });
    m.querySelector('#pbiz-close')!.addEventListener('click', close);
    m.querySelector('#pbiz-types')!.addEventListener('click', (e) => {
        const card = (e.target as HTMLElement).closest('.type[data-id]') as HTMLElement | null;
        if (!card) return;
        selected = card.dataset.id || 'retail';
        m!.querySelectorAll('.type').forEach((c) => c.classList.toggle('on', c === card));
        renderPanel();
    });
    m.querySelector('#pbiz-go')!.addEventListener('click', () =>
        apply(m!.querySelector('#pbiz-go')!)
    );
    return m;
}

function close(): void {
    const m = document.getElementById('pbiz-mask');
    if (m) m.classList.remove('show');
}

async function apply(btn: Element): Promise<void> {
    (btn as HTMLButtonElement).disabled = true;
    let body: { ok?: boolean; error?: { code?: string } };
    try {
        const r = await fetch('/api/me/onboarding', {
            method: 'PUT',
            headers: {
                Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ business_type: selected }),
        });
        body = await r.json();
    } catch (_) {
        body = { ok: false, error: { code: 'pos.unexpected' } };
    }
    if (body && body.ok === true) {
        showToast(t('onb.done'), 'success');
        close();
        if (onDone) onDone();
        // 业态套餐改了整组模块开关 → 整页重载,保证导航/路由/各页都按新模块组合重渲(避免散点刷新漏角)。
        setTimeout(() => window.location.reload(), 500);
    } else {
        showToast(
            posErrMsg((body.error && body.error.code) || 'pos.unexpected', 'pos.unexpected'),
            'error'
        );
        (btn as HTMLButtonElement).disabled = false;
    }
}

window.openBusinessPicker = function (opts?: { businessType?: string; onDone?: () => void }) {
    const isOwner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    if (!isOwner) {
        showToast(t('onb.owner_only'), 'error');
        return;
    }
    onDone = (opts && opts.onDone) || null;
    selected = (opts && opts.businessType) || 'retail';
    const m = ensureModal();
    (m.querySelector('#pbiz-title') as HTMLElement).textContent = t('onb.title');
    (m.querySelector('#pbiz-sub') as HTMLElement).textContent = t('onb.sub');
    (m.querySelector('#pbiz-go') as HTMLElement).textContent = t('onb.enter');
    (m.querySelector('#pbiz-types') as HTMLElement).innerHTML = renderCards();
    renderPanel();
    m.classList.add('show');
};

// 侧栏「可开启功能 →」点击 → 弹业态选择器(owner · module-nav 控其显隐)。
document.addEventListener('click', (e) => {
    const enroll = (e.target as HTMLElement).closest('#nav-enroll');
    if (enroll && typeof window.openBusinessPicker === 'function') window.openBusinessPicker();
});
