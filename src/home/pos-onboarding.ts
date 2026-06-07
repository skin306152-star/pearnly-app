// POS 项目 · PO-B1 前端 · 开通收银(屏8)· window.loadPosOnboardingPage
// 视觉照搬概念稿 08-开通收银.html(令牌 + 结构移植 home-42-pos-onboarding.css · 作用域 .posob)。
// 只改三处:假数据→PUT /api/pos/admin/onboarding(04 §2)· 写死文案→i18n(4 语)· 补四态。
// 业态卡 data-bt = 发后端的 business_type;预设面板按业态显【真会开】的能力(诚实 · 非概念稿装饰列)。
// 仅老板可开通(后端 require_owner)· 非 owner 显诚实态;未选账套引导先选账套。
/* global t, token, showToast, routeTo, escapeHtml */
import { posErrMsg, activeWsId } from './inventory-common';

// 业态预设 = 后端 services/pos/onboarding.BUSINESS_PRESETS 的前端镜像(诚实展示将开的能力块)。
const PRESETS: Record<string, string[]> = {
    retail: ['multi_unit'],
    pharmacy: ['multi_unit', 'track_batch', 'track_expiry', 'prescription'],
    restaurant: ['tables', 'kitchen'],
    service: [],
};
const ALL_CAPS = ['multi_unit', 'track_batch', 'track_expiry', 'prescription', 'tables', 'kitchen'];

interface BizType {
    id: string;
    bt: string; // 发后端的 business_type(批发暂回落 retail · 后端无 b2b 预设)
    icon: string;
}
const TYPES: BizType[] = [
    {
        id: 'retail',
        bt: 'retail',
        icon: 'M3 9l1-5h16l1 5M4 9v11a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V9M9 21v-6h6v6',
    },
    {
        id: 'pharmacy',
        bt: 'pharmacy',
        icon: 'M10.5 20.5 3.5 13.5a5 5 0 0 1 7-7l7 7a5 5 0 0 1-7 7zM8.5 8.5l7 7',
    },
    {
        id: 'restaurant',
        bt: 'restaurant',
        icon: 'M3 2v7a3 3 0 0 0 6 0V2M6 9v13M18 2v20M18 9c2 0 3-1 3-4s-1-3-3-3',
    },
    { id: 'service', bt: 'service', icon: 'M12 7a4 4 0 1 0 0 0M5.5 21a6.5 6.5 0 0 1 13 0' },
    {
        id: 'b2b',
        bt: 'retail',
        icon: 'M1 3h15v13H1zM16 8h4l3 3v5h-7M5.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM18.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
    },
];

let selected = 'retail';
let cashierOpen = false;

function capLabel(cap: string): string {
    return t('posob-cap-' + cap.replace(/_/g, '-'));
}

function renderPanel(): void {
    const ty = TYPES.find((x) => x.id === selected) || TYPES[0];
    const caps = PRESETS[ty.bt] || [];
    const presetEl = document.getElementById('posob-preset');
    if (presetEl) presetEl.textContent = t('posob-type-' + ty.id) + ' ' + t('posob-preset-suffix');
    // 永远开:库存 + POS 收银 + 商品(基座)· 业态能力按 preset 开 · 其余能力列为「未开·可手动」
    const onBase = [t('posob-mod-product'), t('posob-mod-inventory'), t('posob-mod-pos')];
    const onCaps = caps.map(capLabel);
    const offCaps = ALL_CAPS.filter((c) => !caps.includes(c)).map(capLabel);
    const row = (label: string, on: boolean) =>
        `<div class="mod ${on ? 'on' : 'off'}"><span class="sw"></span>${escapeHtml(label)}<span class="tag">${
            on ? t('posob-tag-on') : t('posob-tag-off')
        }</span></div>`;
    const mods = document.getElementById('posob-mods');
    if (mods)
        mods.innerHTML =
            onBase.map((l) => row(l, true)).join('') +
            onCaps.map((l) => row(l, true)).join('') +
            offCaps.map((l) => row(l, false)).join('');
}

function renderCards(): string {
    return TYPES.map(
        (ty) =>
            `<div class="type${ty.id === selected ? ' on' : ''}" data-id="${ty.id}">
        <div class="ico"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="${ty.icon}"/></svg></div>
        <div class="nm">${escapeHtml(t('posob-type-' + ty.id))}</div>
        <div class="ds">${escapeHtml(t('posob-type-' + ty.id + '-desc'))}</div>
      </div>`
    ).join('');
}

function render(sec: HTMLElement): void {
    sec.innerHTML = `<div class="posob">
    <h1>${escapeHtml(t('posob-title'))}</h1>
    <div class="sub">${escapeHtml(t('posob-sub'))}</div>
    <div class="cols">
      <div>
        <div class="q">${escapeHtml(t('posob-q'))}</div>
        <div class="types" id="posob-types">${renderCards()}</div>
      </div>
      <div class="panel">
        <div class="h">${escapeHtml(t('posob-panel-h'))}<div class="s" id="posob-preset"></div></div>
        <div class="mods" id="posob-mods"></div>
        <div class="foot">
          <div class="cashier" id="posob-cashier-toggle">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>
            <span>${escapeHtml(t('posob-cashier-add'))}</span>
          </div>
          <div class="cashier-form" id="posob-cashier-form" style="display:none;">
            <input type="text" id="posob-cashier-name" maxlength="80" placeholder="${escapeHtml(t('posob-cashier-name-ph'))}" />
            <input type="text" id="posob-cashier-pin" inputmode="numeric" maxlength="6" placeholder="${escapeHtml(t('posob-cashier-pin-ph'))}" />
          </div>
          <button class="go" id="posob-go">${escapeHtml(t('posob-go'))}</button>
        </div>
      </div>
    </div>
  </div>`;
    bind(sec);
    renderPanel();
}

function bind(sec: HTMLElement): void {
    sec.querySelectorAll<HTMLElement>('.type[data-id]').forEach((el) => {
        el.addEventListener('click', () => {
            selected = el.dataset.id || 'retail';
            sec.querySelectorAll('.type').forEach((t2) => t2.classList.toggle('on', t2 === el));
            renderPanel();
        });
    });
    const toggle = document.getElementById('posob-cashier-toggle');
    const form = document.getElementById('posob-cashier-form');
    if (toggle && form)
        toggle.addEventListener('click', () => {
            cashierOpen = !cashierOpen;
            form.style.display = cashierOpen ? 'flex' : 'none';
            if (cashierOpen) document.getElementById('posob-cashier-name')?.focus();
        });
    const go = document.getElementById('posob-go') as HTMLButtonElement | null;
    if (go) go.addEventListener('click', () => onboard(go));
}

interface OnboardPayload {
    workspace_client_id: number;
    business_type: string;
    warehouse_name: string | null;
    first_cashier: { display_name: string; pin: string } | null;
}

async function putOnboard(payload: OnboardPayload): Promise<void> {
    let body: { ok?: boolean; error?: { code?: string } };
    try {
        const r = await fetch('/api/pos/admin/onboarding', {
            method: 'PUT',
            headers: {
                Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });
        body = await r.json();
    } catch (_) {
        throw new Error('pos.unexpected');
    }
    if (body && body.ok === true) return;
    const e = new Error('onboard-failed') as Error & { code?: string };
    e.code = (body && body.error && body.error.code) || 'pos.unexpected';
    throw e;
}

async function onboard(btn: HTMLButtonElement): Promise<void> {
    const wsId = activeWsId();
    if (!wsId) {
        // 未选账套(个人模式)· 开通按账套走 · 引导先选账套
        if (typeof window.requireWorkspace === 'function')
            window.requireWorkspace(() => onboard(btn));
        else showToast(t('posob-need-workspace'), 'error');
        return;
    }
    const ty = TYPES.find((x) => x.id === selected) || TYPES[0];
    const nameEl = document.getElementById('posob-cashier-name') as HTMLInputElement | null;
    const pinEl = document.getElementById('posob-cashier-pin') as HTMLInputElement | null;
    const name = (nameEl?.value || '').trim();
    const pin = (pinEl?.value || '').trim();
    if (cashierOpen && name && pin.length < 4) {
        showToast(t('posob-pin-short'), 'error');
        return;
    }
    const firstCashier =
        cashierOpen && name && pin.length >= 4 ? { display_name: name, pin } : null;
    btn.disabled = true;
    try {
        await putOnboard({
            workspace_client_id: wsId,
            business_type: ty.bt,
            warehouse_name: null,
            first_cashier: firstCashier,
        });
        if (typeof window.applyModuleNav === 'function') window.applyModuleNav();
        showToast(t('posob-done'), 'success');
        if (typeof routeTo === 'function') routeTo('inventory'); // 落到刚开通的库存后台
    } catch (e) {
        const code = (e as { code?: string }).code;
        showToast(posErrMsg(code, 'pos.unexpected'), 'error');
        btn.disabled = false;
    }
}

window.loadPosOnboardingPage = function () {
    const sec = document.getElementById('page-pos-onboarding');
    if (!sec) return;
    // 仅老板可开通(后端 require_owner)· 非 owner 显诚实态,不留死按钮
    const isOwner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    if (!isOwner) {
        sec.innerHTML = `<div class="posob"><div class="posob-blocked">${escapeHtml(t('posob-owner-only'))}</div></div>`;
        return;
    }
    selected = 'retail';
    cashierOpen = false;
    render(sec);
};
