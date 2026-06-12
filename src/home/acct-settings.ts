// 自动做账 · 屏5 做账设置(照搬设计稿 05-做账设置 · 配置后台)。
// 自动化(全局开关 + 门槛 + R1-R9 粒度 · 安全带③ · 开自动二次确认)→ 记账(准则/存货法/
// 本位币/启用期)→ 科目映射(摘要 + 调整弹窗)→ 自动记账规则(learned 可见可删)→ 保存。
/* global t, escapeHtml, showToast */
import {
    aapi,
    acctConfirm,
    acctErrMsg,
    injectAcctBase,
    injectStyle,
    openAcctModal,
    periodLabel,
    withWs,
    type Account,
} from './acct-common.js';
import { fetchAccounts } from './acct-modals.js';

interface AcctSettings {
    auto_post: boolean;
    auto_post_threshold: number;
    auto_post_rules: Record<string, boolean>;
    accounting_standard: string;
    inventory_method: string;
    base_currency: string;
    start_period: string | null;
    closed_through: string | null;
}

interface LearnedRule {
    id: string;
    scope_key: string;
    decision: Record<string, unknown>;
}

const RULE_KEYS = ['R1', 'R2', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9'];

const PAGE_CSS = `
.acct.as .grp{padding:11px 22px;font-size:11.5px;color:var(--ink3);font-weight:600;letter-spacing:.3px;background:var(--line2);border-bottom:1px solid var(--line2);}
.acct.as .item{display:flex;align-items:center;gap:14px;padding:15px 22px;border-bottom:1px solid var(--line2);}
.acct.as .item .l{min-width:0;}
.acct.as .item .t2{font-size:13.5px;font-weight:600;}
.acct.as .item .d{color:var(--ink2);font-size:12px;margin-top:3px;}
.acct.as .item .ctl{margin-left:auto;display:flex;align-items:center;gap:10px;flex-shrink:0;}
.acct.as .sw{width:42px;height:24px;border-radius:999px;background:var(--line);position:relative;cursor:pointer;flex:0 0 42px;}
.acct.as .sw.on{background:var(--accent);}
.acct.as .sw i{position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:var(--card);transition:.15s;}
.acct.as .sw.on i{left:21px;}
.acct.as .inp{height:36px;min-width:90px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;padding:0 12px;font-size:13px;background:var(--card);}
.acct.as .inp input{border:0;outline:0;background:transparent;width:54px;font:inherit;color:var(--ink);text-align:right;}
.acct.as .seg{display:inline-flex;gap:2px;border:1px solid var(--line);border-radius:9px;padding:3px;}
.acct.as .seg .o{height:30px;padding:0 13px;border-radius:7px;display:flex;align-items:center;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.acct.as .seg .o.on{background:var(--accent-weak);color:var(--accent-deep);font-weight:600;}
.acct.as .pill{font-size:11.5px;background:var(--line2);color:var(--ink2);padding:4px 11px;border-radius:8px;}
.acct.as .rules{padding:6px 22px 12px;border-bottom:1px solid var(--line2);}
.acct.as .rule{display:flex;align-items:center;gap:10px;padding:8px 0;font-size:12.5px;color:var(--ink2);}
.acct.as .rule .nm{flex:1;}
.acct.as .map{padding:14px 22px;border-bottom:1px solid var(--line2);font-size:12.5px;color:var(--ink2);line-height:1.9;}
.acct.as .map b{color:var(--ink);} .acct.as .map .link{color:var(--accent);cursor:pointer;}
.acct.as .learned-row{display:flex;align-items:center;gap:12px;padding:10px 22px;border-bottom:1px solid var(--line2);font-size:12.5px;}
.acct.as .learned-row .k{flex:1;min-width:0;color:var(--ink);}
.acct.as .learned-row .del{color:var(--red);cursor:pointer;font-size:12px;}
.acct.as .foot{display:flex;justify-content:flex-end;padding:14px 22px;}
@media(max-width:600px){
  .acct.as .item{flex-wrap:wrap;}
  .acct.as .item .ctl{margin-left:0;width:100%;justify-content:flex-end;}
}
`;

let settings: AcctSettings | null = null;
let learned: LearnedRule[] = [];
let dirty: Record<string, unknown> = {};

function swHtml(id: string, on: boolean): string {
    return `<div class="sw ${on ? 'on' : ''}" id="${id}"><i></i></div>`;
}

function ruleEnabled(s: AcctSettings, key: string): boolean {
    const rules = s.auto_post_rules || {};
    if (key in rules) return !!rules[key];
    return !!s.auto_post;
}

function shellHtml(s: AcctSettings): string {
    const rules = RULE_KEYS.map(
        (k) => `<div class="rule"><span class="nm">${escapeHtml(t('acct-rule-' + k))}</span>
            ${swHtml('acct-rule-sw-' + k, ruleEnabled(s, k))}</div>`
    ).join('');
    const learnedRows = learned.length
        ? learned
              .map(
                  (r) => `<div class="learned-row" data-id="${escapeHtml(r.id)}">
                <span class="k">${escapeHtml(r.scope_key)}${r.decision && r.decision.confirmed_rule ? ` → ${escapeHtml(t('acct-rule-' + r.decision.confirmed_rule))}` : ''}</span>
                <span class="del">${escapeHtml(t('acct-learned-del'))}</span></div>`
              )
              .join('')
        : `<div class="learned-row" style="color:var(--ink3);">${escapeHtml(t('acct-learned-empty'))}</div>`;
    return `<div class="acct as"><div class="wrap">
        <div class="ph"><div><div class="t">${escapeHtml(t('acct-set-title'))}</div><div class="sub">${escapeHtml(t('acct-set-subtitle'))}</div></div></div>
        <div class="panel">
            <div class="grp">${escapeHtml(t('acct-set-grp-auto'))}</div>
            <div class="item">
                <div class="l"><div class="t2">${escapeHtml(t('acct-set-autopost'))}</div><div class="d">${escapeHtml(t('acct-set-autopost-d'))}</div></div>
                <div class="ctl">${swHtml('acct-sw-auto', s.auto_post)}</div>
            </div>
            <div class="item">
                <div class="l"><div class="t2">${escapeHtml(t('acct-set-threshold'))}</div><div class="d">${escapeHtml(t('acct-set-threshold-d'))}</div></div>
                <div class="ctl"><div class="inp tnum"><input id="acct-threshold" type="number" min="50" max="100" value="${Number(s.auto_post_threshold) || 90}"> %</div></div>
            </div>
            <div class="item" style="border-bottom:0;padding-bottom:6px;">
                <div class="l"><div class="t2">${escapeHtml(t('acct-set-rules'))}</div><div class="d">${escapeHtml(t('acct-set-rules-d'))}</div></div>
            </div>
            <div class="rules">${rules}</div>
            <div class="grp">${escapeHtml(t('acct-set-grp-book'))}</div>
            <div class="item">
                <div class="l"><div class="t2">${escapeHtml(t('acct-set-standard'))}</div><div class="d">${escapeHtml(t('acct-set-standard-d'))}</div></div>
                <div class="ctl"><span class="pill">TFRS for NPAEs</span></div>
            </div>
            <div class="item">
                <div class="l"><div class="t2">${escapeHtml(t('acct-set-inventory'))}</div><div class="d">${escapeHtml(t('acct-set-inventory-d'))}</div></div>
                <div class="ctl"><div class="seg" id="acct-inv-seg">
                    <div class="o ${s.inventory_method === 'perpetual' ? 'on' : ''}" data-v="perpetual">${escapeHtml(t('acct-inv-perpetual'))}</div>
                    <div class="o ${s.inventory_method !== 'perpetual' ? 'on' : ''}" data-v="periodic">${escapeHtml(t('acct-inv-periodic'))}</div>
                </div></div>
            </div>
            <div class="item">
                <div class="l"><div class="t2">${escapeHtml(t('acct-set-currency'))}</div><div class="d">${escapeHtml(t('acct-set-currency-d'))}</div></div>
                <div class="ctl"><span class="pill">${escapeHtml(s.base_currency || 'THB')}</span>
                ${s.start_period ? `<span class="pill tnum">${escapeHtml(periodLabel(s.start_period))} ${escapeHtml(t('acct-set-since'))}</span>` : ''}
                ${s.closed_through ? `<span class="pill tnum">${escapeHtml(t('acct-set-closed-through'))} ${escapeHtml(periodLabel(s.closed_through))}</span>` : ''}</div>
            </div>
            <div class="grp">${escapeHtml(t('acct-set-grp-map'))}</div>
            <div class="map">${escapeHtml(t('acct-set-map-d'))}<br>
                <span class="link" id="acct-map-edit">${escapeHtml(t('acct-set-map-edit'))}</span> · <span class="link" id="acct-map-coa">${escapeHtml(t('acct-acc-title'))}</span></div>
            <div class="grp">${escapeHtml(t('acct-set-grp-learned'))}</div>
            <div id="acct-learned">${learnedRows}</div>
            <div class="foot"><button class="btn primary" id="acct-set-save" style="height:40px;padding:0 22px;">${escapeHtml(t('acct-save'))}</button></div>
        </div>
    </div></div>`;
}

function bind(sec: HTMLElement): void {
    const s = settings!;
    const swAuto = sec.querySelector<HTMLElement>('#acct-sw-auto');
    if (swAuto)
        swAuto.onclick = () => {
            const turnOn = !swAuto.classList.contains('on');
            // 安全带③:开自动是放权动作,二次确认;关回建议模式直接生效。
            if (turnOn) {
                confirmAuto(() => {
                    swAuto.classList.add('on');
                    dirty.auto_post = true;
                });
            } else {
                swAuto.classList.remove('on');
                dirty.auto_post = false;
            }
        };
    RULE_KEYS.forEach((k) => {
        const sw = sec.querySelector<HTMLElement>('#acct-rule-sw-' + k);
        if (sw)
            sw.onclick = () => {
                const turnOn = !sw.classList.contains('on');
                const apply = () => {
                    sw.classList.toggle('on', turnOn);
                    const rules = {
                        ...(s.auto_post_rules || {}),
                        ...((dirty.auto_post_rules as Record<string, boolean>) || {}),
                    };
                    rules[k] = turnOn;
                    dirty.auto_post_rules = rules;
                };
                if (turnOn) confirmAuto(apply);
                else apply();
            };
    });
    const threshold = sec.querySelector<HTMLInputElement>('#acct-threshold');
    if (threshold)
        threshold.onchange = () => {
            dirty.auto_post_threshold = Number(threshold.value) || 90;
        };
    sec.querySelectorAll<HTMLElement>('#acct-inv-seg .o').forEach((el) => {
        el.onclick = () => {
            sec.querySelectorAll<HTMLElement>('#acct-inv-seg .o').forEach((o) =>
                o.classList.toggle('on', o === el)
            );
            dirty.inventory_method = el.dataset.v;
        };
    });
    const mapEdit = sec.querySelector<HTMLElement>('#acct-map-edit');
    if (mapEdit) mapEdit.onclick = () => openMappings();
    const mapCoa = sec.querySelector<HTMLElement>('#acct-map-coa');
    if (mapCoa) mapCoa.onclick = () => window.routeTo?.('acct-accounts');
    sec.querySelectorAll<HTMLElement>('.learned-row .del').forEach((el) => {
        el.onclick = async () => {
            const row = el.closest<HTMLElement>('.learned-row');
            const id = row?.dataset.id;
            if (!id) return;
            try {
                await aapi('DELETE', withWs(`/api/accounting/learned/${id}`));
                showToast(t('acct-learned-deleted'), 'success');
                load();
            } catch (e) {
                showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
            }
        };
    });
    const save = sec.querySelector<HTMLButtonElement>('#acct-set-save');
    if (save)
        save.onclick = async () => {
            try {
                await withLoading(save, () =>
                    aapi('PUT', withWs('/api/accounting/settings'), dirty)
                );
                showToast(t('acct-save-ok'), 'success');
                dirty = {};
                load();
            } catch (e) {
                showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
            }
        };
}

// 开自动过账 = 放权动作 → 二次确认(04 §五)。
function confirmAuto(onOk: () => void): void {
    acctConfirm(t('acct-set-autopost'), t('acct-autopost-confirm'), onOk);
}

// 科目映射弹窗:role → 科目下拉,改即 PUT(单条生效 · 不攒)。
async function openMappings(): Promise<void> {
    const inner = `<div class="acctm w560"><div class="mh"><div class="t">${escapeHtml(t('acct-set-map-edit'))}</div><div class="x" data-close>×</div></div>
        <div class="mb"><div id="acctm-maps">${escapeHtml(t('acct-loading'))}</div></div>
        <div class="mf"><button class="btn" data-close>${escapeHtml(t('acct-close'))}</button></div></div>`;
    const mask = openAcctModal(inner);
    if (!mask) return;
    try {
        const [accounts, mapData] = await Promise.all([
            fetchAccounts(),
            aapi('GET', withWs('/api/accounting/mappings')) as Promise<{
                mappings?: Record<string, unknown>[];
            }>,
        ]);
        const rows = mapData.mappings || [];
        const box = mask.querySelector<HTMLElement>('#acctm-maps');
        if (!box) return;
        const opts = (sel: string) =>
            accounts
                .filter((a: Account) => a.is_active)
                .map(
                    (a: Account) =>
                        `<option value="${escapeHtml(a.id)}" ${a.id === sel ? 'selected' : ''}>${escapeHtml(a.code)} ${escapeHtml(a.name_zh)}</option>`
                )
                .join('');
        box.innerHTML = rows
            .map((m) => {
                const role = String(m.role || '');
                const roleLabel = t('acct-role-' + role);
                return `<div class="field"><label>${escapeHtml(roleLabel !== 'acct-role-' + role ? roleLabel : role)}</label>
                <select class="inp" data-role="${escapeHtml(role)}">${opts(String(m.account_id || ''))}</select></div>`;
            })
            .join('');
        box.querySelectorAll<HTMLSelectElement>('select[data-role]').forEach((sel) => {
            sel.onchange = async () => {
                try {
                    await aapi('PUT', withWs('/api/accounting/mappings'), {
                        role: sel.dataset.role,
                        account_id: sel.value,
                    });
                    showToast(t('acct-save-ok'), 'success');
                } catch (e) {
                    showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
                }
            };
        });
    } catch (e) {
        const box = mask.querySelector<HTMLElement>('#acctm-maps');
        if (box) box.textContent = acctErrMsg(e, 'acct.unexpected');
    }
}

async function load(): Promise<void> {
    const sec = document.getElementById('page-acct-settings');
    if (!sec) return;
    sec.innerHTML = `<div class="acct as"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(t('acct-loading'))}</div></div></div></div>`;
    try {
        const [setData, learnedData] = await Promise.all([
            aapi('GET', withWs('/api/accounting/settings')) as Promise<{
                settings?: AcctSettings;
            }>,
            aapi('GET', withWs('/api/accounting/learned')) as Promise<{
                items?: Record<string, unknown>[];
            }>,
        ]);
        settings = setData.settings || null;
        learned = (learnedData.items || []).map((r) => ({
            id: String(r.id),
            scope_key: String(r.scope_key || ''),
            decision: (r.decision as Record<string, unknown>) || {},
        }));
        dirty = {};
        if (!settings) throw new Error('no settings');
        sec.innerHTML = shellHtml(settings);
        bind(sec);
    } catch (e) {
        sec.innerHTML = `<div class="acct as"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(acctErrMsg(e, 'acct.unexpected'))}<br><button class="btn" id="acct-set-retry" style="margin-top:12px;">${escapeHtml(t('acct-retry'))}</button></div></div></div></div>`;
        const retry = document.getElementById('acct-set-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadAcctSettings = function () {
    const sec = document.getElementById('page-acct-settings');
    if (!sec) return;
    injectAcctBase();
    injectStyle('acct-settings-css', PAGE_CSS);
    load();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('acct-settings', () => {
        if (document.getElementById('page-acct-settings')?.querySelector('.acct.as'))
            window.loadAcctSettings?.();
    });
}
