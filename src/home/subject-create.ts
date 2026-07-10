// 引导闭环 · 主体登记(向导步②)· 三分支:企业税号带出 / 未注册手动填 / 个人主体。
// 纯渲染 + 状态 + 提交;DOM 事件由 onboarding-flow 统一委托(它持有 SubjectState 并重渲)。
// 建主体走 POST /api/workspace/clients(带 subject_type);税号带出走 GET /api/workspace/tax-lookup。
/* global t, escapeHtml */
import { apiClient } from './clients-helpers.js';
import { onbIcon } from './onboarding-flow-html.js';

export interface SubjectState {
    mode: 'company' | 'person';
    manual: boolean; // 企业分支下「无税号手动填」
    taxId: string;
    pulled: { name: string; address: string; branch: string } | null;
    vat: boolean;
    name: string;
    address: string;
}

export function newSubjectState(): SubjectState {
    return {
        mode: 'company',
        manual: false,
        taxId: '',
        pulled: null,
        vat: true,
        name: '',
        address: '',
    };
}

const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));

// 税局返回归一:优先用后端归一字段(name/address/branch),否则从 RD 原始字段兜底拼装。
// 后端若尚未归一,绿卡仍能显出可用信息,名称缺失时留空待用户补(状态诚实 · 不阻塞)。
function normLookup(d: Record<string, unknown>): { name: string; address: string; branch: string } {
    const g = (...keys: string[]): string => {
        for (const k of keys) {
            const v = d[k];
            if (v != null && String(v).trim()) return String(v).trim();
        }
        return '';
    };
    const name = g('name', 'company_name', 'BranchTitleName', 'BranchName', 'TitleName');
    let address = g('address', 'full_address');
    if (!address) {
        address = [
            g('HouseNumber'),
            g('VillageName'),
            g('BuildingName'),
            g('RoomNumber'),
            g('FloorNumber'),
            g('MooNumber') && t('subj-moo') + g('MooNumber'),
            g('SoiName') && t('subj-soi') + g('SoiName'),
            g('StreetName') && t('subj-road') + g('StreetName'),
            g('ThumbolName'),
            g('AmphurName'),
            g('ProvinceName'),
            g('PostCode'),
        ]
            .filter(Boolean)
            .join(' ');
    }
    const branch = g('branch', 'branch_label', 'BranchTitleName', 'BranchNumber');
    return { name, address, branch };
}

// 13 位税号带出。命中 → 填 s.pulled + s.vat;未命中/格式错 → 返回 false(调用方降级手填)。
export async function subjectLookup(s: SubjectState): Promise<{ ok: boolean; code?: string }> {
    const tax = (s.taxId || '').replace(/\D/g, '');
    if (tax.length !== 13) return { ok: false, code: 'subj-tax-len' };
    let body: { ok?: boolean; data?: Record<string, unknown>; error?: string };
    try {
        body = await apiClient('/api/workspace/tax-lookup?tax_id=' + encodeURIComponent(tax));
    } catch (_) {
        return { ok: false, code: 'subj-lookup-fail' };
    }
    if (!body || body.ok !== true || !body.data) return { ok: false, code: 'subj-lookup-none' };
    s.taxId = tax;
    s.pulled = normLookup(body.data);
    if (body.data.vat_registered === true) s.vat = true;
    return { ok: true };
}

export function subjectNextEnabled(s: SubjectState): boolean {
    if (s.mode === 'person') return true;
    if (s.manual) return true; // 名称在提交前校验
    return s.pulled != null;
}

export function subjectPayload(s: SubjectState): Record<string, unknown> {
    if (s.mode === 'person') {
        return {
            name: s.name.trim(),
            subject_type: 'personal',
            tax_id: null,
            vat_registered: false,
        };
    }
    if (s.manual) {
        return {
            name: s.name.trim(),
            subject_type: 'company',
            tax_id: null,
            address: s.address.trim() || null,
            vat_registered: false,
        };
    }
    return {
        name: (s.pulled && s.pulled.name) || s.name.trim(),
        subject_type: 'company',
        tax_id: s.taxId,
        address: (s.pulled && s.pulled.address) || null,
        branch: (s.pulled && s.pulled.branch) || null,
        vat_registered: s.vat,
    };
}

// 建主体。成功返回 {id};名称空 → 抛 code(调用方提示)。
export async function createSubject(s: SubjectState): Promise<{ id: number }> {
    const payload = subjectPayload(s);
    if (!String(payload.name || '').trim()) throw new Error('subj-name-required');
    const r = await apiClient('/api/workspace/clients', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
    return { id: r && r.id };
}

// 建主体失败 → 人话文案。422 结构化错误(apiClient 附的 i18nMessage,如泰文注册名必填/
// 锁定)后端已给四语原文,直接挑当前语言渲染,不再吞成通用 toast;已知业务码(税号重复/
// 名称必填)本地兜底;其余诚实退化成通用失败文案(不编造具体原因)。
export function subjectErrorText(e: unknown): string {
    const err = e as { message?: string; i18nMessage?: Record<string, string> } | null;
    if (err && err.i18nMessage) {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        return err.i18nMessage[lang] || err.i18nMessage.en || err.i18nMessage.zh || '';
    }
    const code = err && err.message;
    if (code === 'subj-name-required') return t('subj-name-required');
    if (code === 'workspace.tax_id_duplicate') return t('workspace.tax_id_duplicate');
    return t('subj-create-fail');
}

// 步②面板内层(seg + 当前分支字段 + note);动作行由 onboarding-flow 渲染。
export function subjectPaneInner(s: SubjectState): string {
    const seg =
        '<div style="display:flex;justify-content:center">' +
        '<div class="onb-seg">' +
        `<button class="${s.mode === 'company' ? 'on' : ''}" data-act="subj-mode" data-m="company">${esc(t('subj-seg-company'))}</button>` +
        `<button class="${s.mode === 'person' ? 'on' : ''}" data-act="subj-mode" data-m="person">${esc(t('subj-seg-person'))}</button>` +
        '</div></div>';

    if (s.mode === 'person') return seg + personBranch(s);
    if (s.manual) return seg + manualBranch(s);
    return seg + taxBranch(s);
}

function personBranch(s: SubjectState): string {
    return (
        '<div class="onb-fgrid"><div class="onb-fld">' +
        `<label>${esc(t('subj-person-name'))}</label>` +
        `<input class="onb-inp" id="onb-subj-name" value="${esc(s.name)}" placeholder="${esc(t('subj-person-ph'))}">` +
        '</div></div>' +
        note(t('subj-person-note'))
    );
}

function manualBranch(s: SubjectState): string {
    return (
        '<div class="onb-fgrid">' +
        `<div class="onb-fld"><label>${esc(t('subj-store-name'))}</label>` +
        `<input class="onb-inp" id="onb-subj-name" value="${esc(s.name)}" placeholder="${esc(t('subj-store-ph'))}"></div>` +
        `<div class="onb-fld"><label>${esc(t('subj-address'))}<span class="opt">· ${esc(t('subj-optional'))}</span></label>` +
        `<input class="onb-inp" id="onb-subj-addr" value="${esc(s.address)}" placeholder="${esc(t('subj-address-ph'))}"></div>` +
        '</div>' +
        note(t('subj-store-note')) +
        // 不填税号的直接后果(G1 两轮实锤:税号是分拣方向判定的保命字段)——不阻断建档,
        // 但必须把降级说清楚,别让用户在不知情的情况下选了一条更脆的路。
        note(t('subj-no-tax-warn'), 'warn')
    );
}

function taxBranch(s: SubjectState): string {
    const pulledCard = s.pulled
        ? '<div class="onb-pulled">' +
          onbIcon('check', 'ic') +
          `<div><div class="nm">${esc(s.pulled.name || t('subj-name-unknown'))}</div>` +
          `<div class="ad">${esc([s.pulled.address, s.pulled.branch].filter(Boolean).join(' · '))}</div></div>` +
          `<button class="re" data-act="subj-retax">${esc(t('subj-edit'))}</button></div>`
        : `<div style="margin-top:11px"><button class="onb-lnk" data-act="subj-manual">${esc(t('subj-to-manual'))} ${onbIcon('chev')}</button></div>`;
    const vatRow = s.pulled
        ? `<div class="onb-switch" data-act="subj-vat"><span class="onb-sw ${s.vat ? 'on' : ''}"></span>` +
          `<div><div style="font-weight:600;font-size:13px">${esc(t('subj-vat-label'))}</div>` +
          `<div style="color:var(--ink2);font-size:11.5px;margin-top:2px">${esc(t('subj-vat-hint'))}</div></div></div>`
        : '';
    return (
        '<div class="onb-fgrid"><div class="onb-fld">' +
        `<label>${esc(t('subj-tax-label'))}<span class="opt">· ${esc(t('subj-tax-hint'))}</span></label>` +
        `<input class="onb-inp tnum" id="onb-subj-tax" maxlength="13" inputmode="numeric" placeholder="0 1055 61000 12 3" value="${esc(s.taxId)}">` +
        pulledCard +
        '</div></div>' +
        vatRow
    );
}

function note(text: string, variant?: 'warn'): string {
    const cls = variant ? ` ${variant}` : '';
    const icon = variant === 'warn' ? 'warn' : 'info';
    return (
        `<div class="onb-note${cls}">` + onbIcon(icon, 'ic') + '<div>' + esc(text) + '</div></div>'
    );
}

// 共享控制器(向导步② + 套账门新建专屏共用 · 防逻辑重复)。
// 重渲前把当前输入收进状态(rerender 会重建 DOM)。
export function syncSubjectInputs(s: SubjectState): void {
    const tax = document.getElementById('onb-subj-tax') as HTMLInputElement | null;
    if (tax) s.taxId = tax.value;
    const name = document.getElementById('onb-subj-name') as HTMLInputElement | null;
    if (name) s.name = name.value;
    const addr = document.getElementById('onb-subj-addr') as HTMLInputElement | null;
    if (addr) s.address = addr.value;
}

// 处理主体分支动作(纯状态变更)。返回 'rerender' 需重渲 / 'lookup' 需异步带出 / null 未处理。
export function handleSubjectAct(
    act: string,
    dataM: string | undefined,
    s: SubjectState
): 'rerender' | 'lookup' | null {
    switch (act) {
        case 'subj-mode':
            s.mode = dataM === 'person' ? 'person' : 'company';
            s.manual = false;
            s.pulled = null;
            return 'rerender';
        case 'subj-manual':
            s.manual = true;
            return 'rerender';
        case 'subj-haveTax':
            s.manual = false;
            return 'rerender';
        case 'subj-retax':
            s.pulled = null;
            return 'rerender';
        case 'subj-vat':
            s.vat = !s.vat;
            return 'rerender';
        case 'subj-pulltax':
            return 'lookup';
        default:
            return null;
    }
}

// 主体表单的动作行(税号带出 → 「获取企业信息」,否则主按钮 label 由调用方给)。
// 供新建专屏复用(向导有自己的 stepper 壳,这里只给纯表单动作区可选用)。
export function subjectActionsHtml(s: SubjectState, primaryLabel: string, busy: boolean): string {
    const taxFetch = s.mode === 'company' && !s.manual && !s.pulled;
    const manualLink =
        s.mode === 'company' && s.manual
            ? `<button class="onb-lnk" data-act="subj-haveTax">${esc(t('subj-to-tax'))} ${onbIcon('chev')}</button>`
            : '';
    const primary = taxFetch
        ? `<button class="onb-btn pri" data-act="subj-pulltax" ${busy ? 'disabled' : ''}>${esc(t('subj-fetch'))}</button>`
        : `<button class="onb-btn pri" data-act="subj-confirm" ${subjectNextEnabled(s) && !busy ? '' : 'disabled'}>${esc(primaryLabel)}</button>`;
    return `<div class="grp">${manualLink}${primary}</div>`;
}
