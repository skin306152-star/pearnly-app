// POS · 收款设置(老板后台 · 主程序 · 照设计稿 13-收款设置)· window.openPosPayment。
// 配收银台能收哪些钱:现金(恒开)/ PromptPay(开关 + 收款ID)/ 刷卡(开关 · 仅记录)+ 服务费率 + 价格含 VAT。
// 接 GET/PUT /api/pos/admin/payment-settings(owner · 按账套 workspace_client_id 隔离)。
// PromptPay ID 复用账套主体字段(workspace_clients.promptpay_id · 后端处理)。core-boot 满 500 → 弹窗非路由。
// owner 专属(收银员 403 + nav 不显)· 四态(加载/正常/保存中/错)· 信封 body.ok→data · 失败 posErrMsg。
/* global t, token, showToast, escapeHtml */
import { activeWsId, posErrMsg } from './inventory-common';

interface PaySettings {
    promptpay_enabled: boolean;
    card_enabled: boolean;
    service_charge_rate: string;
    price_includes_vat: boolean;
    promptpay_id: string;
}

const URL = '/api/pos/admin/payment-settings';
let ws = 0;

function hdr(): Record<string, string> {
    return {
        Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
        'Content-Type': 'application/json',
    };
}

async function call(method: string, body?: unknown): Promise<PaySettings> {
    const q = method === 'GET' ? `?workspace_client_id=${ws}` : '';
    let env: { ok?: boolean; data?: PaySettings; error?: { code?: string } };
    try {
        const r = await fetch(URL + q, {
            method,
            headers: hdr(),
            body: body !== undefined ? JSON.stringify(body) : undefined,
        });
        env = await r.json();
    } catch (_) {
        throw new Error('pos.unexpected');
    }
    if (env && env.ok === true) return env.data as PaySettings;
    throw new Error((env && env.error && env.error.code) || 'pos.unexpected');
}

const STYLE = `
.rpay-mask{position:fixed;inset:0;background:rgba(17,24,39,.5);backdrop-filter:blur(3px);display:none;align-items:flex-start;justify-content:center;z-index:1200;padding:32px 16px;overflow:auto;}
.rpay-mask.show{display:flex;}
.rpay{width:600px;max-width:96vw;background:#fff;border-radius:18px;padding:24px 26px 22px;position:relative;box-shadow:0 24px 60px rgba(0,0,0,.25);}
.rpay-x{position:absolute;top:16px;right:18px;border:0;background:#f0f0ec;color:#6b7280;width:30px;height:30px;border-radius:8px;font-size:18px;cursor:pointer;line-height:1;}
.rpay h1{font-size:20px;color:#111827;margin:0 0 4px;}
.rpay .sub{color:#6b7280;font-size:13px;margin-bottom:18px;}
.rpay .card{border:1px solid #e8e8e3;border-radius:14px;overflow:hidden;margin-bottom:16px;}
.rpay .ch{padding:12px 16px;border-bottom:1px solid #f0f0ec;font-weight:700;font-size:13.5px;color:#111827;}
.rpay .pm{padding:14px 16px;border-bottom:1px solid #f6f6f3;}
.rpay .pm:last-child{border-bottom:0;}
.rpay .pmtop{display:flex;align-items:center;gap:12px;}
.rpay .pm .ic{width:38px;height:38px;border-radius:10px;background:#f4f4f0;color:#6b7280;display:grid;place-items:center;flex:0 0 38px;}
.rpay .pm.on .ic{background:#DBEAFE;color:var(--btn-blue,#2563EB);}
.rpay .pm .tx{flex:1;min-width:0;}
.rpay .pm .n{font-size:14.5px;font-weight:600;color:#111827;}
.rpay .pm .d{font-size:12px;color:#6b7280;margin-top:2px;}
.rpay .tagb{display:inline-block;font-size:10.5px;color:#b45309;background:#fef3c7;padding:1px 7px;border-radius:5px;margin-left:7px;}
.rpay .sw{width:44px;height:25px;border-radius:999px;flex:0 0 44px;position:relative;cursor:pointer;transition:.15s;background:#d8d8d3;}
.rpay .sw::after{content:"";position:absolute;top:2px;left:2px;width:21px;height:21px;border-radius:50%;background:#fff;transition:.15s;box-shadow:0 1px 3px rgba(0,0,0,.25);}
.rpay .pm.on .sw{background:var(--btn-blue,#2563EB);}.rpay .pm.on .sw::after{left:21px;}
.rpay .pm.lock .sw{background:#bcd0f7;cursor:not-allowed;}.rpay .pm.lock .sw::after{left:21px;}
.rpay .sub-cfg{margin:12px 0 0 50px;}
.rpay .sub-cfg label{display:block;font-size:12px;color:#6b7280;margin-bottom:6px;}
.rpay .fld{height:44px;border:1px solid #e8e8e3;border-radius:10px;padding:0 13px;display:flex;align-items:center;background:#fbfbf9;}
.rpay .fld .pre{color:#9ca3af;font-size:13px;margin-right:8px;}
.rpay .fld input{border:0;outline:0;background:transparent;flex:1;font-size:14.5px;color:#111827;}
.rpay .hint{font-size:11.5px;color:#9ca3af;margin-top:6px;line-height:1.5;}
.rpay .row{display:flex;align-items:center;gap:12px;padding:13px 16px;border-bottom:1px solid #f6f6f3;}
.rpay .row:last-child{border-bottom:0;}
.rpay .row .tx{flex:1;}.rpay .row .n{font-size:14px;font-weight:600;color:#111827;}.rpay .row .d{font-size:12px;color:#6b7280;margin-top:2px;}
.rpay .pctfld{width:90px;height:38px;border:1px solid #e8e8e3;border-radius:9px;display:flex;align-items:center;padding:0 10px;background:#fbfbf9;}
.rpay .pctfld input{border:0;outline:0;background:transparent;width:100%;text-align:right;font-size:14px;font-weight:600;color:#111827;}
.rpay .pctfld span{color:#9ca3af;font-size:13px;}
.rpay .save{width:100%;height:50px;border:0;border-radius:11px;background:var(--btn-blue,#2563EB);color:#fff;font-weight:700;font-size:16px;cursor:pointer;}
.rpay .save:disabled{background:#c7cdd6;cursor:not-allowed;}
.rpay .state{padding:44px 0;text-align:center;color:#9ca3af;font-size:13.5px;}
`;

function ensureStyle(): void {
    if (document.getElementById('rpay-style')) return;
    const s = document.createElement('style');
    s.id = 'rpay-style';
    s.textContent = STYLE;
    document.head.appendChild(s);
}

function ensureShell(): HTMLElement {
    let m = document.getElementById('rpay-mask');
    if (m) return m;
    ensureStyle();
    m = document.createElement('div');
    m.id = 'rpay-mask';
    m.className = 'rpay-mask';
    m.innerHTML = `<div class="rpay">
        <button class="rpay-x" id="rpay-close" aria-label="close">&times;</button>
        <h1>${escapeHtml(t('rpay.title'))}</h1>
        <div class="sub">${escapeHtml(t('rpay.sub'))}</div>
        <div id="rpay-body"><div class="state">${escapeHtml(t('rpay.loading'))}</div></div>
    </div>`;
    document.body.appendChild(m);
    m.addEventListener('click', (e) => {
        if (e.target === m) m!.classList.remove('show');
    });
    m.querySelector('#rpay-close')!.addEventListener('click', () => m!.classList.remove('show'));
    return m;
}

function pmRow(
    id: string,
    ic: string,
    name: string,
    desc: string,
    on: boolean,
    tag?: string
): string {
    return `<div class="pm ${on ? 'on' : ''}" data-pm="${id}">
        <div class="pmtop">
            <div class="ic">${ic}</div>
            <div class="tx"><div class="n">${escapeHtml(name)}${tag ? `<span class="tagb">${escapeHtml(tag)}</span>` : ''}</div><div class="d">${escapeHtml(desc)}</div></div>
            <div class="sw" data-toggle="${id}"></div>
        </div>__SUB_${id}__</div>`;
}

function render(s: PaySettings): void {
    const body = document.getElementById('rpay-body');
    if (!body) return;
    const icCash =
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/></svg>';
    const icPP =
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><line x1="14" y1="14" x2="21" y2="21"/></svg>';
    const icCard =
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>';
    const ppSub = `<div class="sub-cfg" id="rpay-pp-cfg"${s.promptpay_enabled ? '' : ' style="display:none;"'}>
        <label>${escapeHtml(t('rpay.pp_id'))}</label>
        <div class="fld"><span class="pre">฿</span><input id="rpay-ppid" maxlength="40" value="${escapeHtml(s.promptpay_id)}" placeholder="${escapeHtml(t('rpay.pp_ph'))}"></div>
        <div class="hint">${escapeHtml(t('rpay.pp_hint'))}</div></div>`;
    const cardSub = `<div class="sub-cfg"><div class="hint">${escapeHtml(t('rpay.card_hint'))}</div></div>`;
    const cash = `<div class="pm on lock"><div class="pmtop"><div class="ic">${icCash}</div><div class="tx"><div class="n">${escapeHtml(t('rpay.cash'))}</div><div class="d">${escapeHtml(t('rpay.cash_d'))}</div></div><div class="sw"></div></div></div>`;
    const methods =
        cash +
        pmRow(
            'promptpay',
            icPP,
            t('rpay.promptpay'),
            t('rpay.promptpay_d'),
            s.promptpay_enabled
        ).replace('__SUB_promptpay__', ppSub) +
        pmRow(
            'card',
            icCard,
            t('rpay.card'),
            t('rpay.card_d'),
            s.card_enabled,
            t('rpay.card_tag')
        ).replace('__SUB_card__', cardSub);
    body.innerHTML = `<div class="card"><div class="ch">${escapeHtml(t('rpay.methods'))}</div>${methods}</div>
        <div class="card"><div class="ch">${escapeHtml(t('rpay.other'))}</div>
            <div class="row"><div class="tx"><div class="n">${escapeHtml(t('rpay.service'))}</div><div class="d">${escapeHtml(t('rpay.service_d'))}</div></div>
                <div class="pctfld"><input id="rpay-svc" type="number" min="0" max="100" value="${escapeHtml(s.service_charge_rate)}"><span>%</span></div></div>
            <div class="row" data-pm="vat"><div class="tx"><div class="n">${escapeHtml(t('rpay.vat'))}</div><div class="d">${escapeHtml(t('rpay.vat_d'))}</div></div>
                <div class="pm ${s.price_includes_vat ? 'on' : ''}" style="padding:0;border:0;"><div class="sw" data-toggle="vat"></div></div></div>
        </div>
        <button class="save" id="rpay-save">${escapeHtml(t('rpay.save'))}</button>`;
    body.querySelectorAll('.sw[data-toggle]').forEach((sw) =>
        sw.addEventListener('click', () => {
            const pm = sw.closest('.pm');
            if (!pm || pm.classList.contains('lock')) return;
            const onNow = pm.classList.toggle('on');
            const which = (sw as HTMLElement).dataset.toggle;
            if (which === 'promptpay') {
                const cfg = document.getElementById('rpay-pp-cfg');
                if (cfg) cfg.style.display = onNow ? '' : 'none';
            }
        })
    );
    (body.querySelector('#rpay-save') as HTMLElement).addEventListener('click', save);
}

async function save(): Promise<void> {
    const btn = document.getElementById('rpay-save') as HTMLButtonElement;
    btn.disabled = true;
    const ppOn = !!document.querySelector('.pm[data-pm="promptpay"]')?.classList.contains('on');
    const cardOn = !!document.querySelector('.pm[data-pm="card"]')?.classList.contains('on');
    const vatOn = !!document.querySelector('.row[data-pm="vat"] .pm')?.classList.contains('on');
    const payload = {
        workspace_client_id: ws,
        promptpay_enabled: ppOn,
        card_enabled: cardOn,
        price_includes_vat: vatOn,
        service_charge_rate:
            Number((document.getElementById('rpay-svc') as HTMLInputElement).value) || 0,
        promptpay_id:
            (document.getElementById('rpay-ppid') as HTMLInputElement | null)?.value || '',
    };
    try {
        const s = await call('PUT', payload);
        render(s);
        showToast(t('rpay.saved'), 'success');
    } catch (e) {
        btn.disabled = false;
        showToast(
            posErrMsg(e instanceof Error ? e.message : 'pos.unexpected', 'pos.unexpected'),
            'error'
        );
    }
}

async function load(): Promise<void> {
    const body = document.getElementById('rpay-body');
    if (body) body.innerHTML = `<div class="state">${escapeHtml(t('rpay.loading'))}</div>`;
    try {
        render(await call('GET'));
    } catch (_) {
        if (body) body.innerHTML = `<div class="state">${escapeHtml(t('rpay.load_failed'))}</div>`;
    }
}

window.openPosPayment = function () {
    const isOwner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    if (!isOwner) {
        showToast(t('rpay.owner_only'), 'error');
        return;
    }
    const id = activeWsId();
    if (!id) {
        showToast(t('rpay.no_workspace'), 'error');
        return;
    }
    ws = id;
    ensureShell().classList.add('show');
    load();
};

document.addEventListener('click', (e) => {
    if (
        (e.target as HTMLElement).closest('#nav-pos-payment') &&
        typeof window.openPosPayment === 'function'
    )
        window.openPosPayment();
});
