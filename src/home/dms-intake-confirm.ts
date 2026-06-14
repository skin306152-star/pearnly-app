// ============================================================
// 录入工作台 · 步骤3 资料确认(比对/全字段)+ 步骤4 推送/成功 + 确认弹窗
// 取值模型在 dms-intake-core.ts。比对逐项 new/dms 取值,差异标黄;
// 全字段表单 4 分区(客户资料 + 三套地址·联系/寄送可「与身份证相同」)。
// ============================================================
import { DX_SECTIONS, DX_COMPARE } from './dms-intake-html.js';
import type { DxFormSection } from './dms-intake-html.js';
import {
    S,
    esc,
    lang,
    $,
    authHeaders,
    norm,
    existing,
    showStep,
    initForm,
    syncMirror,
    dmsCompareVal,
    newCompareVal,
    isChanged,
    diffNewCount,
    currentOpt,
    syncFormFromDom,
    buildPayload,
} from './dms-intake-core.js';
import type { Dict } from './dms-intake-core.js';

export async function enterConfirm() {
    if (S.scenario === 'similar') {
        if (!S.selectedId) return showToast(t('dx-pick-cand'), 'warn');
        await loadCustomerFields(S.selectedId);
    }
    initForm();
    S.tab = 'difference';
    renderConfirm();
    showStep(3, 'dx-s-confirm');
}
async function loadCustomerFields(cid: string) {
    try {
        const r = await fetch('/api/dms/customer-fields', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ customer_id: cid }),
        });
        const d = await r.json().catch(() => ({}));
        if (d?.ok) {
            S.dmsVals = (d.current_fields as Dict) || {};
            if (d.prefixes) S.prefixes = d.prefixes;
            if (d.provinces) S.provinces = d.provinces;
        }
    } catch {
        /* dmsVals 留空 → 走新值 */
    }
}

export function renderConfirm() {
    const el = $('dx-s-confirm');
    if (!el) return;
    el.innerHTML =
        '<div class="dx-tabs">' +
        `<button class="dx-tab${S.tab === 'difference' ? ' active' : ''}" data-tab="difference">${esc(t('dx-tab-diff'))}</button>` +
        `<button class="dx-tab${S.tab === 'allfields' ? ' active' : ''}" data-tab="allfields">${esc(t('dx-tab-all'))}</button></div>` +
        `<div class="dx-tabview${S.tab === 'difference' ? ' active' : ''}">${existing() ? diffViewHtml() : noMatchHtml()}</div>` +
        `<div class="dx-tabview${S.tab === 'allfields' ? ' active' : ''}">${formViewHtml()}</div>`;
}
function diffViewHtml() {
    return (
        '<div class="dx-cmp-top">' +
        `<b>${esc(t('dx-cmp-h'))}</b><div class="dx-cmp-act">` +
        `<button class="btn small" id="dx-all-new">${esc(t('dx-all-new'))}</button>` +
        `<button class="btn small" id="dx-all-dms">${esc(t('dx-all-dms'))}</button></div></div>` +
        `<div class="dx-cmp">${cmpHeadHtml()}${DX_COMPARE.map(cmpRowHtml).join('')}</div>` +
        decisionHtml() +
        footerHtml(false)
    );
}
function cmpHeadHtml() {
    return (
        '<div class="dx-row head">' +
        ['dx-col-field', 'dx-col-new', 'dx-col-dms', 'dx-col-res', 'dx-col-keep']
            .map((k) => `<div class="dx-cell">${esc(t(k))}</div>`)
            .join('') +
        '</div>'
    );
}
function cmpRowHtml(c: { key: string; label: string }) {
    const nv = newCompareVal(c.key);
    const dv = dmsCompareVal(c.key);
    const same = norm(nv) === norm(dv);
    const pick = S.pick[c.key] || 'dms';
    // 称谓在 DMS 主档无此选项(如 น.ส. vs 只有 นาย)→ 不可写,标注 + 禁用「用新值」
    const blocked = c.key === 'prefix_name' && S.prefixUnmappable;
    const result = same
        ? `<span class="dx-sbadge">${esc(t('dx-same'))}</span>`
        : blocked
          ? `<span class="dx-dbadge" title="${esc(t('dx-no-dms-opt'))}">${esc(t('dx-no-dms-opt'))}</span>`
          : `<span class="dx-dbadge">${esc(t('dx-diff'))}</span>`;
    const picker = blocked
        ? `<span style="font-size:9px;color:#9a93a6">DMS</span>`
        : `<div class="dx-pick" data-key="${esc(c.key)}">` +
          `<button data-src="new" class="${pick === 'new' ? 'active' : ''}">${esc(t('dx-use-new'))}</button>` +
          `<button data-src="dms" class="${pick === 'dms' ? 'active' : ''}">DMS</button></div>`;
    return (
        `<div class="dx-row${same || blocked ? '' : ' diff'}">` +
        `<div class="dx-cell"><b>${esc(t(c.label))}</b></div>` +
        `<div class="dx-cell val">${esc(nv || '—')}</div>` +
        `<div class="dx-cell val">${esc(dv || '—')}</div>` +
        `<div class="dx-cell">${result}</div>` +
        `<div class="dx-cell">${picker}</div></div>`
    );
}
function decisionHtml() {
    const upd = S.decision === 'update' ? ' active' : '';
    const ovr = S.decision === 'overwrite' ? ' active' : '';
    return (
        `<div class="dx-decision"><h3>${esc(t('dx-save-way'))}</h3><div class="dx-dgrid">` +
        `<div class="dx-dcard rec${upd}" data-rec="${esc(t('dx-recommended'))}" data-decision="update">` +
        `<div class="dx-dic">↻</div><b>${esc(t('dx-dec-update'))}</b><p>${esc(t('dx-dec-update-x'))}</p></div>` +
        `<div class="dx-dcard danger${ovr}" data-decision="overwrite">` +
        `<div class="dx-dic">!</div><b>${esc(t('dx-dec-over'))}</b><p>${esc(t('dx-dec-over-x'))}</p></div></div>` +
        `<div class="dx-warn${S.decision === 'overwrite' ? ' show' : ''}">${esc(t('dx-over-warn'))}</div></div>`
    );
}
function footerHtml(create: boolean) {
    const note = create
        ? esc(t('dx-foot-create'))
        : esc(
              t(S.decision === 'update' ? 'dx-foot-update' : 'dx-foot-over')
                  .replace('{id}', S.selectedId || '')
                  .replace('{n}', String(diffNewCount()))
          );
    const btn = create
        ? t('dx-btn-create')
        : S.decision === 'update'
          ? t('dx-btn-update')
          : t('dx-btn-over');
    return (
        `<div class="dx-foot"><div class="dx-note">${note}</div>` +
        `<button class="btn primary dx-save-btn">${esc(btn)}</button></div>`
    );
}
function noMatchHtml() {
    return (
        '<div class="dx-nomatch"><div class="dx-nomatch-ic">+</div>' +
        `<h3>${esc(t('dx-none-t'))}</h3><p>${esc(t('dx-none-create'))}</p></div>` +
        footerHtml(true)
    );
}

// 全字段表单
function formViewHtml() {
    return DX_SECTIONS.map(sectionHtml).join('') + footerHtml(!existing());
}
function sectionHtml(scn: DxFormSection) {
    const tools =
        scn.addr && scn.sameAs
            ? `<div class="dx-addr-tools"><span>${esc(t('dx-same-addr'))}</span>` +
              `<div class="dx-switch${S.sameAs[scn.addr] ? ' on' : ''}" data-mirror="${esc(scn.addr)}"></div></div>`
            : '';
    return (
        '<div class="dx-fsec"><div class="dx-fsec-h"><div>' +
        `<b>${esc(t(scn.title))}</b><div class="sub">${esc(t(scn.note))}</div></div>${tools}</div>` +
        `<div class="dx-fgrid">${scn.fields.map(fieldHtml).join('')}</div></div>`
    );
}
function fieldHtml(f: { key: string; label: string; type: string }) {
    const v = S.form[f.key] ?? '';
    const full = f.key === 'name' ? ' full' : '';
    let control: string;
    if (f.type.startsWith('select-')) {
        control = selectHtml(f, v);
    } else {
        const det = f.type === 'detected' ? ' detected' : '';
        const changed = existing() && isChanged(f.key) ? ' changed' : '';
        const ro = f.type === 'readonly' ? ' ro' : '';
        const roAttr = f.type === 'readonly' ? ' readonly' : '';
        control = `<input class="dx-in${det}${changed}${ro}" id="dx-f-${esc(f.key)}" data-fk="${esc(f.key)}" value="${esc(v)}"${roAttr}>`;
    }
    return `<div class="dx-field${full}"><label>${esc(t(f.label))}</label>${control}</div>`;
}
function selectHtml(f: { key: string; label: string; type: string }, v: string) {
    const changed = existing() && isChanged(f.key) ? ' changed' : '';
    let opts: Array<[string, string]>;
    if (f.type === 'select-title') opts = S.prefixes;
    else if (f.type === 'select-province')
        opts = S.provinces.length ? S.provinces : currentOpt(f.key, v);
    else opts = currentOpt(f.key, v);
    const body = opts
        .map(
            (o) =>
                `<option value="${esc(o[0])}"${String(o[0]) === String(v) ? ' selected' : ''}>${esc(o[1])}</option>`
        )
        .join('');
    return `<select class="dx-sel${changed}" id="dx-f-${esc(f.key)}" data-fk="${esc(f.key)}" data-geo="${esc(f.type)}">${body}</select>`;
}

// ── 确认弹窗 + 推送 + 成功 ────────────────────────────────────
export function openModal() {
    syncFormFromDom();
    const create = !existing();
    const items = create
        ? [t('dx-m-c1'), t('dx-m-c2'), t('dx-m-c3')]
        : S.decision === 'overwrite'
          ? [t('dx-m-o1'), t('dx-m-o2'), t('dx-m-o3')]
          : [
                t('dx-m-u1').replace('{id}', S.selectedId || ''),
                t('dx-m-u2').replace('{n}', String(diffNewCount())),
                t('dx-m-u3'),
            ];
    const title = create
        ? t('dx-m-create-t')
        : S.decision === 'overwrite'
          ? t('dx-m-over-t')
          : t('dx-m-update-t');
    const text = create
        ? t('dx-m-create-x')
        : S.decision === 'overwrite'
          ? t('dx-m-over-x')
          : t('dx-m-update-x');
    const mask = $('dx-modal-mask');
    if (!mask) return;
    mask.innerHTML =
        '<div class="modal dmsx" style="max-width:480px"><div class="modal-head"><b>' +
        esc(title) +
        '</b></div><div class="modal-body"><p style="font-size:12px;color:#6f687d;line-height:1.6;margin:0">' +
        esc(text) +
        `</p><ul class="dx-mlist">${items.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>` +
        '<div class="modal-foot" style="display:flex;justify-content:flex-end;gap:8px;padding:13px 18px">' +
        `<button class="btn" id="dx-m-cancel">${esc(t('dx-cancel'))}</button>` +
        `<button class="btn primary" id="dx-m-ok">${esc(t('dx-confirm-save'))}</button></div></div>`;
    mask.style.display = 'flex';
}
export function closeModal() {
    const mask = $('dx-modal-mask');
    if (mask) {
        mask.style.display = 'none';
        mask.innerHTML = '';
    }
}
export async function doSave() {
    if (S.busy) return;
    const { fields, addresses } = buildPayload();
    if (!fields.people_id || !fields.name) return showToast(t('dic-need-fields'), 'error');
    const mode = !existing() ? 'create' : S.decision;
    S.busy = true;
    const okBtn = $('dx-m-ok') as HTMLButtonElement | null;
    if (okBtn) okBtn.disabled = true;
    try {
        const r = await fetch('/api/dms/id-card/push', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify({ fields, addresses, mode, customer_id: S.selectedId }),
        });
        const d = await r.json().catch(() => ({}));
        closeModal();
        if (d?.ok) {
            renderSuccess(d.dms_push || {}, mode);
            showStep(4, 'dx-s-success');
            return;
        }
        const fr = (d?.dms_push?.error_friendly || {}) as Dict;
        showToast(fr[lang()] || fr.en || t('dic-push-fail'), 'error');
    } catch {
        closeModal();
        showToast(t('dic-push-fail'), 'error');
    } finally {
        S.busy = false;
    }
}
function renderSuccess(push: Record<string, unknown>, mode: string) {
    const el = $('dx-s-success');
    if (!el) return;
    const create = mode === 'create';
    const cid = (push.customer_id as string) || S.selectedId || '';
    const modeTxt = create
        ? t('dx-mode-new')
        : mode === 'overwrite'
          ? t('dx-mode-over')
          : t('dx-mode-update');
    el.innerHTML =
        '<div class="dx-success"><div class="dx-suc-ic">✓</div>' +
        `<h3>${esc(create ? t('dx-suc-create') : t('dx-suc-save'))}</h3>` +
        `<p>${esc(t('dx-suc-sub'))}</p><div class="dx-sgrid">` +
        `<div class="dx-sitem"><label>${esc(t('dx-result-customer'))}</label><strong>#${esc(cid)} · ${esc(S.form.name || '')}</strong></div>` +
        `<div class="dx-sitem"><label>${esc(t('dx-result-mode'))}</label><strong>${esc(modeTxt)}</strong></div>` +
        `<div class="dx-sitem"><label>${esc(t('dx-result-res'))}</label><strong>${esc(create ? t('dx-res-created') : t('dx-res-saved'))}</strong></div></div>` +
        `<div class="dx-sact"><button class="btn primary" id="dx-restart">${esc(t('dx-next-id'))}</button></div></div>`;
}

// 地址级联(府→县→区→邮编)· ID 块/联系/寄送各自联动
export async function onGeoChange(selEl: HTMLSelectElement) {
    const fk = selEl.dataset.fk!;
    S.form[fk] = selEl.value;
    const chain: Record<string, [string, string]> = {
        province_id: ['districts', 'district_id'],
        district_id: ['subdistricts', 'subdistrict_id'],
        subdistrict_id: ['zipcodes', 'zipcode_id'],
    };
    const base = fk.replace(/_ct$|_sd$/, '');
    const sfx = fk.slice(base.length);
    const next = chain[base];
    if (!next) return syncMirror();
    try {
        const r = await fetch(
            `/api/dms/geo?level=${next[0]}&parent_id=${encodeURIComponent(selEl.value)}`,
            { headers: authHeaders() }
        );
        const d = await r.json().catch(() => ({}));
        const opts = (d?.options || []) as Array<[string, string]>;
        const tgt = $('dx-f-' + next[1] + sfx) as HTMLSelectElement | null;
        if (tgt && opts.length) {
            tgt.innerHTML = opts
                .map((o) => `<option value="${esc(o[0])}">${esc(o[1])}</option>`)
                .join('');
            S.form[next[1] + sfx] = tgt.value;
            tgt.dispatchEvent(new Event('change', { bubbles: true }));
        }
    } catch {
        /* 忽略级联失败 */
    }
    syncMirror();
}
