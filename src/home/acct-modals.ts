// 自动做账 · 共享弹窗:改科目选择器(主屏/逐笔审共用)+ 加/改科目(科目表)。
// 站内 .modal · 不用浏览器原生对话框(DESIGN_LANGUAGE)。
/* global t, escapeHtml, showToast */
import {
    aapi,
    acctErrMsg,
    closeAcctModal,
    openAcctModal,
    withWs,
    type Account,
    type Voucher,
} from './acct-common.js';
import { fmtMoney } from './purchase-common.js';

export async function fetchAccounts(): Promise<Account[]> {
    const data = (await aapi('GET', withWs('/api/accounting/accounts'))) as {
        accounts?: Record<string, unknown>[];
        items?: Record<string, unknown>[];
    };
    const raw = (data && (data.accounts || data.items)) || [];
    return raw.map((a) => ({
        id: String(a.id),
        code: String(a.code || ''),
        name_zh: String(a.name_zh || ''),
        name_th: (a.name_th as string) || null,
        acct_type: (a.acct_type as Account['acct_type']) || 'expense',
        is_preset: !!a.is_preset,
        is_active: a.is_active !== false,
    }));
}

function accountOptions(accounts: Account[], selected: string): string {
    return accounts
        .filter((a) => a.is_active)
        .map(
            (a) =>
                `<option value="${escapeHtml(a.id)}" ${a.id === selected ? 'selected' : ''}>${escapeHtml(a.code)} ${escapeHtml(a.name_zh)}</option>`
        )
        .join('');
}

// 改科目:每行一个下拉(金额不动 · 平衡不变)→ onPick({line_id: account_id})。
export function openAcctAccountPicker(
    v: Voucher,
    onPick: (overrides: Record<string, string>) => void
): void {
    const lines = v.lines || [];
    const inner = `<div class="acctm w560"><div class="mh"><div class="t">${escapeHtml(t('acct-change-account'))}</div><div class="x" data-close>×</div></div>
        <div class="mb"><div id="acctm-lines">${escapeHtml(t('acct-loading'))}</div></div>
        <div class="mf"><button class="btn" data-close>${escapeHtml(t('acct-cancel'))}</button>
        <button class="btn primary" id="acctm-apply" disabled>${escapeHtml(t('acct-apply-confirm'))}</button></div></div>`;
    const mask = openAcctModal(inner);
    if (!mask) return;
    fetchAccounts()
        .then((accounts) => {
            const box = mask.querySelector<HTMLElement>('#acctm-lines');
            if (!box) return;
            box.innerHTML = lines
                .map(
                    (l) => `<div class="field">
                    <label>${escapeHtml(t(l.dr_cr === 'debit' ? 'acct-dr' : 'acct-cr'))} · ฿${fmtMoney(l.amount)}${l.memo ? ' · ' + escapeHtml(l.memo) : ''}</label>
                    <select class="inp" data-line="${escapeHtml(l.id)}">${accountOptions(accounts, l.account_id)}</select>
                </div>`
                )
                .join('');
            const apply = mask.querySelector<HTMLButtonElement>('#acctm-apply');
            if (apply) {
                apply.disabled = false;
                apply.onclick = () => {
                    const overrides: Record<string, string> = {};
                    mask.querySelectorAll<HTMLSelectElement>('select[data-line]').forEach((sel) => {
                        const orig = lines.find((l) => l.id === sel.dataset.line);
                        if (orig && sel.value !== orig.account_id)
                            overrides[sel.dataset.line!] = sel.value;
                    });
                    apply.disabled = true;
                    onPick(overrides);
                };
            }
        })
        .catch((e) => {
            const box = mask.querySelector<HTMLElement>('#acctm-lines');
            if (box) box.textContent = acctErrMsg(e, 'acct.unexpected');
        });
}

// 加/改科目(科目表):名/泰文名/类型/编号 · 预置只能改名不可删 · 可停用。
export function openAcctAccountForm(acct: Account | null, onDone: () => void): void {
    const isEdit = !!acct;
    const types: [Account['acct_type'], string][] = [
        ['asset', 'acct-type-asset'],
        ['liability', 'acct-type-liability'],
        ['equity', 'acct-type-equity'],
        ['revenue', 'acct-type-revenue'],
        ['expense', 'acct-type-expense'],
    ];
    const typeOpts = types
        .map(
            ([k, key]) =>
                `<option value="${k}" ${acct && acct.acct_type === k ? 'selected' : ''}>${escapeHtml(t(key))}</option>`
        )
        .join('');
    const inner = `<div class="acctm"><div class="mh"><div class="t">${escapeHtml(t(isEdit ? 'acct-edit-account' : 'acct-add-account'))}</div><div class="x" data-close>×</div></div>
        <div class="mb">
            <div class="field"><label>${escapeHtml(t('acct-f-code'))}</label><input class="inp tnum" id="acctm-code" value="${escapeHtml(acct?.code || '')}" ${isEdit && acct?.is_preset ? 'disabled' : ''}></div>
            <div class="field"><label>${escapeHtml(t('acct-f-name'))}</label><input class="inp" id="acctm-name" value="${escapeHtml(acct?.name_zh || '')}"></div>
            <div class="field"><label>${escapeHtml(t('acct-f-name-th'))}</label><input class="inp" id="acctm-name-th" value="${escapeHtml(acct?.name_th || '')}"></div>
            <div class="field"><label>${escapeHtml(t('acct-f-type'))}</label><select class="inp" id="acctm-type" ${isEdit && acct?.is_preset ? 'disabled' : ''}>${typeOpts}</select></div>
            ${
                isEdit
                    ? `<div class="field"><label>${escapeHtml(t('acct-f-active'))}</label><select class="inp" id="acctm-active">
                        <option value="1" ${acct!.is_active ? 'selected' : ''}>${escapeHtml(t('acct-active-on'))}</option>
                        <option value="0" ${!acct!.is_active ? 'selected' : ''}>${escapeHtml(t('acct-active-off'))}</option></select></div>`
                    : ''
            }
        </div>
        <div class="mf"><button class="btn" data-close>${escapeHtml(t('acct-cancel'))}</button>
        <button class="btn primary" id="acctm-save">${escapeHtml(t('acct-save'))}</button></div></div>`;
    const mask = openAcctModal(inner);
    if (!mask) return;
    const save = mask.querySelector<HTMLButtonElement>('#acctm-save');
    if (!save) return;
    save.onclick = async () => {
        const val = (id: string) =>
            (mask.querySelector<HTMLInputElement>('#' + id)?.value || '').trim();
        const payload: Record<string, unknown> = {
            code: val('acctm-code'),
            name_zh: val('acctm-name'),
            name_th: val('acctm-name-th') || null,
            acct_type: (mask.querySelector<HTMLSelectElement>('#acctm-type')?.value ||
                'expense') as string,
        };
        if (isEdit) {
            const act = mask.querySelector<HTMLSelectElement>('#acctm-active');
            if (act) payload.is_active = act.value === '1';
        }
        if (!payload.code || !payload.name_zh) {
            showToast(t('acct-form-required'), 'error');
            return;
        }
        try {
            await withLoading(save, async () => {
                if (isEdit)
                    await aapi('PATCH', withWs(`/api/accounting/accounts/${acct!.id}`), payload);
                else await aapi('POST', withWs('/api/accounting/accounts'), payload);
            });
            showToast(t('acct-save-ok'), 'success');
            closeAcctModal();
            onDone();
        } catch (e) {
            showToast(acctErrMsg(e, 'acct.unexpected'), 'error');
        }
    };
}
