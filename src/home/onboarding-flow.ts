// 用户引导闭环 · 注册后向导壳(全屏 · 业态 → 主体 → 账务 → 完成清单)。
// 由 module-nav 的 needs_onboarding 触发(window.startOnboardingFlow);owner 专属。
// 步① 复用 onboarding-business 的业态卡数据(TYPES/PRESETS · DRY)→ PUT /api/me/onboarding 应用预设。
// 步② 复用 subject-create 三分支。步③ 账务设置当前无 per-主体 持久化字段 → 只读默认值确认(状态诚实)。
/* global t, token, escapeHtml, showToast */
import { TYPES } from './onboarding-business.js';
import { ONB_CSS, onbIcon, onbBizIcon } from './onboarding-flow-html.js';
import type { SubjectState } from './subject-create.js';
import {
    newSubjectState,
    subjectPaneInner,
    subjectLookup,
    subjectNextEnabled,
    createSubject,
} from './subject-create.js';
import { injectStyle } from './acct-common.js';
import { apiClient } from './clients-helpers.js';
import { WSG_CSS, wsgListHtml } from './workspace-gate-html.js';

type PickSubject = { id: number; name?: string; tax_id?: string; subject_type?: string };

interface FlowState {
    step: 1 | 2 | 3 | 4 | 5; // 4=选套账(硬门) 5=完成清单
    biz: string;
    subject: SubjectState;
    createdId: number | null;
    createdName: string;
    fy: number; // 财年起始月 1-12
    prefix: string; // 单据前缀(空=自动)
    pickSubjects: PickSubject[];
    pickSelectedId: number | null;
    busy: boolean;
}

let S: FlowState | null = null;
const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));

function root(): HTMLElement {
    let el = document.getElementById('onboarding-flow-root');
    if (!el) {
        injectStyle('onb-flow-css', ONB_CSS);
        injectStyle('wsg-css', WSG_CSS);
        el = document.createElement('div');
        el.id = 'onboarding-flow-root';
        el.className = 'onb-root';
        document.body.appendChild(el);
        el.addEventListener('click', onClick);
    }
    return el;
}

function close(): void {
    const el = document.getElementById('onboarding-flow-root');
    if (el) el.remove();
    S = null;
}

function brandLogo(): string {
    // 真品牌资产(紫 P 底猫)· 暗夜垫白底见 ONB_CSS :root.dark .onb-logo(同 home S2-bis)。
    return '<span class="onb-brand"><img class="onb-logo" src="/static/brand/pwa-icon-192.png?v=1" alt="" />Pearnly</span>';
}

function topBar(showSkip: boolean): string {
    const skip = showSkip
        ? `<button class="onb-skip" data-act="skip-all">${esc(t('onbf-skip'))} ${onbIcon('chev')}</button>`
        : '';
    return `<div class="onb-top">${brandLogo()}${skip}</div>`;
}

function stepper(active: 0 | 1 | 2 | 3): string {
    const labels = [
        t('onbf-step-biz'),
        t('onbf-step-subject'),
        t('onbf-step-acct'),
        t('onbf-step-pick'),
    ];
    let h = '<div class="onb-steps">';
    labels.forEach((lb, i) => {
        const st = i < active ? 'done' : i === active ? 'on' : '';
        const inner = i < active ? onbIcon('check') : String(i + 1);
        h += `<div class="onb-step ${st}"><div class="dot">${inner}</div>`;
        h += i === active ? `<span class="lb">${esc(lb)}</span>` : '';
        h += '</div>';
        if (i < 3) h += `<div class="onb-bar ${i < active ? 'done' : ''}"></div>`;
    });
    return h + '</div>';
}

// 步④ · 选套账(硬门 · 渲染步②建的主体 + 新建 → 选 → 下一步进系统)。
function step4(): string {
    const list = wsgListHtml(S!.pickSubjects, S!.pickSelectedId);
    return (
        stepper(3) +
        `<div class="onb-h1">${esc(t('onbf-pick-title'))}</div>` +
        `<div class="onb-sub">${esc(t('onbf-pick-sub'))}</div>` +
        list +
        '<div class="onb-acts"><div class="grp">' +
        `<button class="onb-btn pri" data-act="step4-next" ${S!.pickSelectedId != null ? '' : 'disabled'}>${esc(t('onbf-next'))}</button>` +
        '</div></div>'
    );
}

function step1(): string {
    const cards = TYPES.map((ty) => {
        const on = S!.biz === ty.id ? ' on' : '';
        return (
            `<button class="onb-biz${on}" data-act="biz-pick" data-id="${ty.id}">` +
            `<span class="ic">${onbBizIcon(ty.icon)}</span>` +
            `<div><div class="t">${esc(t('biz.' + ty.id))}</div>` +
            `<div class="d">${esc(t('biz.' + ty.id + '.desc'))}</div></div>` +
            '<span class="chk"></span></button>'
        );
    }).join('');
    return (
        stepper(0) +
        `<div class="onb-h1">${esc(t('onbf-biz-title'))}</div>` +
        `<div class="onb-sub">${esc(t('onbf-biz-sub'))}</div>` +
        `<div class="onb-grid">${cards}</div>` +
        '<div class="onb-acts"><div class="grp">' +
        `<button class="onb-btn pri" data-act="step1-next" ${S!.biz ? '' : 'disabled'}>${esc(t('onbf-next'))}</button>` +
        '</div></div>'
    );
}

function step2(): string {
    const s = S!.subject;
    const taxFetch = s.mode === 'company' && !s.manual && !s.pulled;
    const manualLink =
        s.mode === 'company' && s.manual
            ? `<button class="onb-lnk" data-act="subj-haveTax">${esc(t('subj-to-tax'))} ${onbIcon('chev')}</button>`
            : '';
    const primary = taxFetch
        ? `<button class="onb-btn pri" data-act="subj-pulltax" ${S!.busy ? 'disabled' : ''}>${esc(t('subj-fetch'))}</button>`
        : `<button class="onb-btn pri" data-act="step2-next" ${subjectNextEnabled(s) && !S!.busy ? '' : 'disabled'}>${esc(t('onbf-next'))}</button>`;
    return (
        stepper(1) +
        `<div class="onb-h1">${esc(t('onbf-subj-title'))}</div>` +
        `<div class="onb-sub">${esc(t('onbf-subj-sub'))}</div>` +
        subjectPaneInner(s) +
        '<div class="onb-acts">' +
        `<button class="onb-lnk" data-act="back-1">${onbIcon('chev')}${esc(t('onbf-back'))}</button>` +
        `<div class="grp">${manualLink}${primary}</div></div>`
    );
}

// 账务设置:财年起始月 / 本位币(THB 锁定)/ 单据前缀(自动)均为默认值,可在设置中修改。
// 当前无 per-主体 持久化字段,故只读确认 + 可跳过,不放假装能存的输入(状态诚实)。
function step3(): string {
    const opts = Array.from({ length: 12 }, (_, i) => i + 1)
        .map((m) => `<option value="${m}"${m === S!.fy ? ' selected' : ''}>${m}</option>`)
        .join('');
    return (
        stepper(2) +
        `<div class="onb-h1">${esc(t('onbf-acct-title'))}</div>` +
        `<div class="onb-sub">${esc(t('onbf-acct-sub'))}</div>` +
        '<div class="onb-fgrid">' +
        `<div class="onb-fld"><label>${esc(t('onbf-acct-fy'))}</label>` +
        `<select class="onb-inp" id="onb-acct-fy">${opts}</select></div>` +
        `<div class="onb-fld"><label>${esc(t('onbf-acct-prefix'))}<span class="opt">· ${esc(t('subj-optional'))}</span></label>` +
        `<input class="onb-inp" id="onb-acct-prefix" value="${esc(S!.prefix)}" placeholder="${esc(t('onbf-acct-prefix-auto'))}"></div>` +
        `<div class="onb-fld"><label>${esc(t('onbf-acct-cur'))}</label>` +
        `<input class="onb-inp" value="THB (฿)" disabled></div>` +
        '</div>' +
        '<div class="onb-acts">' +
        `<button class="onb-lnk" data-act="step3-skip">${esc(t('onbf-skip-step'))}</button>` +
        `<div class="grp"><button class="onb-btn pri" data-act="step3-done" ${S!.busy ? 'disabled' : ''}>${esc(t('onbf-acct-done'))}</button></div></div>`
    );
}

function done(): string {
    const items: [boolean, string, string, string][] = [
        [true, t('onbf-cl-subject'), t('onbf-cl-subject-d'), ''],
        [false, t('onbf-cl-invoice'), t('onbf-cl-invoice-d'), 'sales-invoices'],
        [false, t('onbf-cl-expense'), t('onbf-cl-expense-d'), 'purchase'],
        [false, t('onbf-cl-invite'), t('onbf-cl-invite-d'), 'console'],
    ];
    const list = items
        .map(
            ([dn, ct, cd, to]) =>
                `<div class="onb-cli"><span class="ck ${dn ? 'done' : 'todo'}">${dn ? onbIcon('check') : ''}</span>` +
                `<div style="flex:1"><div class="ct">${esc(ct)}</div><div class="cd">${esc(cd)}</div></div>` +
                (to
                    ? `<button class="onb-lnk" data-act="goto" data-to="${to}">${esc(t('onbf-cl-go'))} ${onbIcon('chev')}</button>`
                    : '') +
                '</div>'
        )
        .join('');
    return (
        '<div style="text-align:center">' +
        `<div class="onb-done-ic">${onbIcon('check')}</div>` +
        `<div class="onb-h1" style="font-size:20px">${esc(t('onbf-done-title').replace('{name}', S!.createdName))}</div>` +
        `<div class="onb-sub">${esc(t('onbf-done-sub'))}</div></div>` +
        `<div class="onb-checklist">${list}</div>` +
        '<div class="onb-acts" style="justify-content:center">' +
        `<button class="onb-btn pri" data-act="go-system">${esc(t('onbf-done-enter'))}</button></div>`
    );
}

function render(): void {
    if (!S) return;
    const el = root();
    // 业态/账务可跳过(skip→直奔选套账);选套账(步④)与完成页不给跳。
    const showSkip = S.step === 2 || S.step === 3;
    const pane =
        S.step === 1
            ? step1()
            : S.step === 2
              ? step2()
              : S.step === 3
                ? step3()
                : S.step === 4
                  ? step4()
                  : done();
    el.innerHTML =
        topBar(showSkip) + `<div class="onb-body"><div class="onb-pane">${pane}</div></div>`;
}

// 重渲前把当前输入框的值收进状态(rerender 会重建 DOM)。
function syncInputs(): void {
    if (!S) return;
    const tax = document.getElementById('onb-subj-tax') as HTMLInputElement | null;
    if (tax) S.subject.taxId = tax.value;
    const name = document.getElementById('onb-subj-name') as HTMLInputElement | null;
    if (name) S.subject.name = name.value;
    const addr = document.getElementById('onb-subj-addr') as HTMLInputElement | null;
    if (addr) S.subject.address = addr.value;
    const fy = document.getElementById('onb-acct-fy') as HTMLSelectElement | null;
    if (fy) S.fy = parseInt(fy.value, 10) || 1;
    const prefix = document.getElementById('onb-acct-prefix') as HTMLInputElement | null;
    if (prefix) S.prefix = prefix.value;
}

async function onClick(e: Event): Promise<void> {
    if (!S) return;
    const t0 = e.target as HTMLElement;
    // 步④ 选套账:卡片选中 / 新建(走全站统一专屏)。
    const pickEl = t0.closest('[data-wsg-pick]') as HTMLElement | null;
    if (pickEl) {
        S.pickSelectedId = Number(pickEl.dataset.wsgPick);
        return render();
    }
    if (t0.closest('[data-wsg-new]')) return openCreateFromStep4();
    const target = t0.closest('[data-act]') as HTMLElement | null;
    if (!target) return;
    const act = target.dataset.act;
    const s = S.subject;
    syncInputs();
    switch (act) {
        case 'biz-pick':
            S.biz = target.dataset.id || '';
            return render();
        case 'step1-next':
            return applyPresetThenNext();
        case 'subj-mode':
            s.mode = target.dataset.m === 'person' ? 'person' : 'company';
            s.manual = false;
            s.pulled = null;
            return render();
        case 'subj-manual':
            s.manual = true;
            return render();
        case 'subj-haveTax':
            s.manual = false;
            return render();
        case 'subj-retax':
            s.pulled = null;
            return render();
        case 'subj-vat':
            s.vat = !s.vat;
            return render();
        case 'subj-pulltax':
            return doLookup();
        case 'back-1':
            S.step = 1;
            return render();
        case 'step2-next':
            return doCreate();
        case 'step3-skip':
            return goToPick();
        case 'step3-done':
            return saveAcctThenPick();
        case 'step4-next':
            return pickAndDone();
        case 'goto':
            return gotoAndClose(target.dataset.to || '');
        case 'go-system':
            return finish();
        case 'skip-all':
            return goToPick(); // 业态/账务可跳,但仍要过选套账硬门
    }
}

async function fetchSubjects(): Promise<PickSubject[]> {
    if (typeof window.fetchWorkspaceClients !== 'function') return [];
    return (await window.fetchWorkspaceClients()) as PickSubject[];
}

// 进步④:拉主体列表,预选刚建的(或唯一一个)。
async function goToPick(): Promise<void> {
    if (!S) return;
    S.step = 4;
    S.pickSubjects = await fetchSubjects();
    if (S.pickSelectedId == null) {
        if (S.createdId != null) S.pickSelectedId = S.createdId;
        else if (S.pickSubjects.length === 1) S.pickSelectedId = Number(S.pickSubjects[0].id);
    }
    render();
}

// 步④「新建」→ 全站统一专屏;建好回来刷新列表 + 选中新建的。
function openCreateFromStep4(): void {
    if (typeof window.openSubjectCreate !== 'function') return;
    window.openSubjectCreate({
        onCreated: async (id) => {
            if (!S) return;
            S.pickSubjects = await fetchSubjects();
            S.pickSelectedId = id;
            render();
        },
    });
}

// 步④确认:设为当前账套 → 完成清单。
function pickAndDone(): void {
    if (!S || S.pickSelectedId == null) return;
    const selId = S.pickSelectedId;
    if (typeof window.setActiveWorkspaceClientId === 'function')
        window.setActiveWorkspaceClientId(selId);
    const sel = S.pickSubjects.find((x) => Number(x.id) === Number(selId));
    if (sel && sel.name) S.createdName = sel.name;
    S.step = 5;
    render();
}

async function applyPresetThenNext(): Promise<void> {
    if (!S || !S.biz || S.busy) return;
    S.busy = true;
    try {
        await fetch('/api/me/onboarding', {
            method: 'PUT',
            headers: {
                Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ business_type: S.biz }),
        });
    } catch (_) {
        /* 预设失败不阻塞建主体 · 用户可在设置补 */
    }
    S.busy = false;
    S.step = 2;
    render();
}

async function doLookup(): Promise<void> {
    if (!S || S.busy) return;
    S.busy = true;
    render();
    const res = await subjectLookup(S.subject);
    S.busy = false;
    if (!res.ok) showToast(t(res.code || 'subj-lookup-fail'), 'info');
    render();
}

async function doCreate(): Promise<void> {
    if (!S || S.busy || !subjectNextEnabled(S.subject)) return;
    S.busy = true;
    render();
    try {
        const created = await createSubject(S.subject);
        const p = S.subject;
        S.createdId = created.id;
        S.createdName = (p.pulled && p.pulled.name) || p.name.trim();
        S.busy = false;
        S.step = 3;
        render();
    } catch (e) {
        S.busy = false;
        const code = e instanceof Error ? e.message : 'subj-create-fail';
        showToast(
            t(code === 'subj-name-required' ? 'subj-name-required' : 'subj-create-fail'),
            'fail'
        );
        render();
    }
}

// 步③完成:把财年起始月 + 单据前缀存到刚建的主体(PATCH)→ 进步④选套账。
async function saveAcctThenPick(): Promise<void> {
    if (!S || S.busy) return;
    if (S.createdId != null) {
        S.busy = true;
        render();
        try {
            await apiClient('/api/workspace/clients/' + S.createdId, {
                method: 'PATCH',
                body: JSON.stringify({
                    fiscal_year_start_month: S.fy,
                    doc_prefix: S.prefix.trim() || null,
                }),
            });
        } catch (_) {
            showToast(t('cprof-save-fail'), 'info');
        }
        S.busy = false;
    }
    await goToPick();
}

function gotoAndClose(to: string): void {
    finish();
    if (to === 'console') window.location.href = '/console';
    else if (typeof window.routeTo === 'function') window.routeTo(to);
}

// 完成/跳过:关向导 → 刷新导航与右上角切换器,让新主体即时可用。
function finish(): void {
    close();
    if (typeof window.applyModuleNav === 'function') window.applyModuleNav();
    if (typeof window.fetchWorkspaceClients === 'function') {
        window.fetchWorkspaceClients().then((l: unknown) => {
            window._workspaceClientsCache = l as [];
            if (typeof window.renderWorkspaceControl === 'function')
                window.renderWorkspaceControl();
        });
    }
}

window.startOnboardingFlow = function () {
    const owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    if (!owner) return;
    S = {
        step: 1,
        biz: '',
        subject: newSubjectState(),
        createdId: null,
        createdName: '',
        fy: 1,
        prefix: '',
        pickSubjects: [],
        pickSelectedId: null,
        busy: false,
    };
    render();
};
