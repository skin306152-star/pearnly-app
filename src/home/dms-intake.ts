// ============================================================
// 录入工作台(身份证 → DMS 客户)· 4 步向导主控
// 步骤1 上传 + 步骤2 识别/匹配 + 事件委托 + 导航 + window.loadDmsIntake。
// 步骤3-4(资料确认/推送)见 dms-intake-confirm.ts;状态/取值模型见 dms-intake-core.ts。
// 上传 → /api/dms/id-card/recognize → 三场景 → 资料确认 → /api/dms/id-card/push。
// ============================================================
import { dxShell, DX_COMPARE } from './dms-intake-html.js';
import type { Dict, Cand } from './dms-intake-core.js';
import {
    S,
    esc,
    sec,
    $,
    authHeaders,
    norm,
    showStep,
    buildNewVals,
    applyDecisionToForm,
    syncMirror,
    syncFormFromDom,
    newCompareVal,
    dmsCompareVal,
} from './dms-intake-core.js';
import {
    enterConfirm,
    renderConfirm,
    openModal,
    closeModal,
    doSave,
    onGeoChange,
} from './dms-intake-confirm.js';
import {
    IV,
    renderInvoiceUpload,
    resetInvoice,
    rerenderInvoice,
    onInvoiceClick,
    onInvoiceChange,
    onInvoiceDrop,
} from './dms-intake-invoice.js';
import { readStep } from './step-resume.js';

// ── 步骤 1:上传 ──────────────────────────────────────────────
function renderUpload() {
    const el = $('dx-s-upload');
    if (!el) return;
    el.innerHTML =
        '<div class="dx-two"><div class="dx-panel">' +
        `<div class="dx-panel-h"><b>${esc(t('dx-up-title'))}</b><span>${esc(t('dx-up-formats'))}</span></div>` +
        (S.file ? uploadedHtml() : dropHtml()) +
        '</div>' +
        sideHtml([t('dx-side-flow1'), t('dx-side-flow2'), t('dx-side-flow3')], t('dx-side-tip')) +
        '</div>' +
        '<input type="file" id="dx-file" accept="image/*,application/pdf" style="display:none">';
}
function dropHtml() {
    return (
        '<div class="dx-drop up-dz" id="dx-drop">' +
        `<div><div class="dx-drop-g">↑</div><h3>${esc(t('dx-up-title'))}</h3>` +
        `<p>${esc(t('dx-up-hint'))}</p>` +
        `<button class="btn primary" id="dx-pick">${esc(t('dx-up-pick'))}</button>` +
        `<div class="dx-hint" style="margin-top:10px">${esc(t('dx-up-drag'))}</div></div></div>`
    );
}
function uploadedHtml() {
    const f = S.file!;
    return (
        '<div class="dx-file"><div class="dx-file-ic">📄</div>' +
        `<div class="dx-file-c"><b>${esc(f.name)}</b><span>${(f.size / 1048576).toFixed(1)} MB</span></div>` +
        `<span class="dx-badge green">${esc(t('dx-up-ready'))}</span></div>` +
        `<div class="dx-bar"><div class="dx-note">${esc(t('dx-up-next'))}</div><div style="display:flex;gap:8px">` +
        `<button class="btn" id="dx-replace">${esc(t('dx-up-replace'))}</button>` +
        `<button class="btn primary" id="dx-start">${esc(t('dx-up-start'))}</button></div></div>`
    );
}
function sideHtml(items: string[], tip: string) {
    return (
        '<div class="dx-side"><div class="dx-side-box">' +
        `<b>${esc(t('dx-side-cur'))}</b><ul>${items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul></div>` +
        `<div class="dx-side-box"><b>${esc(t('dx-side-rule'))}</b><p>${esc(tip)}</p></div></div>`
    );
}
function pickFile() {
    ($('dx-file') as HTMLInputElement)?.click();
}
function onFile(f: File | null) {
    if (!f) return;
    S.file = f;
    renderUpload();
}

// ── 步骤 2:识别 + 匹配 ───────────────────────────────────────
async function startRecognize() {
    if (!S.file || S.busy) return;
    S.busy = true;
    renderSearching();
    showStep(2, 'dx-s-searching');
    try {
        const form = new FormData();
        form.append('file', S.file, S.file.name);
        const r = await fetch('/api/dms/id-card/recognize', {
            method: 'POST',
            headers: authHeaders(),
            body: form,
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) {
            const code = (d?.detail?.code || d?.detail || 'unknown') as string;
            const k = 'dms-err-' + String(code).toLowerCase();
            const m = t(k);
            showToast(m && m !== k ? m : t('dic-recognize-fail'), 'error');
            return backToUpload();
        }
        if (d.needs_review) {
            showToast(t('dic-needs-review'), 'warn');
            return backToUpload();
        }
        ingestRecognize(d);
        renderMatch();
        showStep(2, 'dx-s-match');
    } catch {
        showToast(t('dic-recognize-fail'), 'error');
        backToUpload();
    } finally {
        S.busy = false;
    }
}
function ingestRecognize(d: Record<string, unknown>) {
    S.ocr = (d.id_card || {}) as Dict;
    const dms = (d.dms || {}) as Record<string, unknown>;
    S.scenario = (dms.scenario as typeof S.scenario) || 'none';
    S.candidates = (dms.candidates || []) as Cand[];
    S.geo = (dms.geo || {}) as Record<string, unknown>;
    S.prefixes = (dms.prefixes || []) as Array<[string, string]>;
    S.provinces = ((S.geo.provinces as Array<[string, string]>) || []).slice();
    S.selectedId = S.scenario === 'exact' ? S.candidates[0]?.customer_id || null : null;
    const match = (dms.match || {}) as Record<string, unknown>;
    S.dmsVals = S.scenario === 'exact' ? (match.current_fields as Dict) || {} : {};
    buildNewVals();
}
function renderSearching() {
    const el = $('dx-s-searching');
    if (!el) return;
    const ic = (S.ocr || {}) as Dict;
    el.innerHTML =
        '<div class="dx-searching"><div class="dx-spin"></div>' +
        `<h3>${esc(t('dx-searching'))}</h3><p>${esc(t('dx-searching-sub'))}</p><div class="dx-schips">` +
        (ic.people_id ? `<span class="dx-schip">${esc(ic.people_id)}</span>` : '') +
        (ic.name ? `<span class="dx-schip">${esc(ic.name)}</span>` : '') +
        '<span class="dx-schip">MR.ERP DMS</span></div></div>';
}
function renderMatch() {
    const el = $('dx-s-match');
    if (!el) return;
    el.innerHTML =
        '<div class="dx-two"><div>' +
        bannerHtml() +
        `<div class="dx-cands">${candsHtml()}</div>` +
        '<div class="dx-panel"><div class="dx-panel-h">' +
        `<b>${esc(t('dx-next-h'))}</b><span>${esc(t('dx-next-s'))}</span></div>` +
        `<div style="font-size:11px;color:#7d768e;line-height:1.65">${esc(matchHint())}</div><div class="dx-actions">` +
        `<button class="btn" id="dx-back-up">${esc(t('dx-back'))}</button>` +
        `<button class="btn primary" id="dx-go-confirm">${esc(t('dx-go-confirm'))}</button></div></div></div>` +
        sideHtml([t('dx-mrule1'), t('dx-mrule2'), t('dx-mrule3')], t('dx-mrule-why')) +
        '</div>';
}
function bannerHtml() {
    const sc = S.scenario;
    const cls = sc === 'exact' ? '' : sc === 'similar' ? ' similar' : ' none';
    const sym = sc === 'exact' ? '✓' : sc === 'similar' ? '!' : '0';
    const badge =
        sc === 'exact'
            ? `<span class="dx-badge green">${esc(t('dx-b-exact'))}</span>`
            : sc === 'similar'
              ? `<span class="dx-badge amber">${esc(t('dx-b-similar'))}</span>`
              : `<span class="dx-badge blue">${esc(t('dx-b-none'))}</span>`;
    const title =
        sc === 'exact'
            ? t('dx-exact-t').replace('{id}', S.selectedId || '')
            : sc === 'similar'
              ? t('dx-similar-t').replace('{n}', String(S.candidates.length))
              : t('dx-none-t');
    const text =
        sc === 'exact' ? t('dx-exact-x') : sc === 'similar' ? t('dx-similar-x') : t('dx-none-x');
    return (
        `<div class="dx-rbanner${cls}"><div class="dx-rsym">${sym}</div>` +
        `<div class="dx-rc"><b>${esc(title)}</b><p>${esc(text)}</p></div>${badge}</div>`
    );
}
function candsHtml() {
    return S.candidates
        .map((c) => {
            const on = S.selectedId === c.customer_id ? ' active' : '';
            return (
                `<div class="dx-cand${on}" data-cid="${esc(c.customer_id)}"><div class="dx-cand-av">C</div>` +
                `<div class="dx-cand-c"><b>DMS #${esc(c.customer_id)} · ${esc(c.name || '')}</b>` +
                `<span>${esc(t('dx-c-id'))} ${esc(c.people_id || '—')} · ${esc(t('dx-c-score'))} ${esc(c.score ?? '')}%</span></div>` +
                '<div class="dx-radio"></div></div>'
            );
        })
        .join('');
}
function matchHint() {
    return S.scenario === 'exact'
        ? t('dx-hint-exact')
        : S.scenario === 'similar'
          ? t('dx-hint-similar')
          : t('dx-hint-none');
}

// ── 导航 / 重置 ──────────────────────────────────────────────
function backToUpload() {
    renderUpload();
    showStep(1, 'dx-s-upload');
}
function resetFlow() {
    S.file = null;
    S.ocr = null;
    S.selectedId = null;
    S.decision = 'update';
    S.tab = 'difference';
    S.sameAs = { _ct: true, _sd: true };
    if (S.task === 'invoice') {
        resetInvoice();
        renderInvoiceUpload();
    } else {
        renderUpload();
    }
    showStep(1, 'dx-s-upload');
}

// 任务切换:重渲整壳(任务选择器高亮 + 标题/步骤条按任务)· 委托监听挂在 section 上,innerHTML 重写不丢
function selectTask(task: 'invoice' | 'identity') {
    if (S.task === task) return;
    S.task = task;
    const el = sec();
    if (!el) return;
    el.innerHTML = dxShell(t, S.task);
    resetFlow();
}

// 查看记录:发票任务→识别记录;身份证任务→集成中心「推送日志」并按 DMS 适配器(mrerp_dms)筛选
function openRecords() {
    if (S.task === 'invoice') {
        if (typeof window.routeTo === 'function') window.routeTo('history');
        return;
    }
    if (typeof window.activateIntegrationsLogsTab === 'function') {
        window.activateIntegrationsLogsTab();
        // 等 logs tab + 下拉渲染好再设筛选(activateIntegrationsLogsTab 内部 loadErpLogs 异步)
        setTimeout(() => window.setErpLogAdapter?.('mrerp_dms'), 80);
    } else if (typeof window.routeTo === 'function') {
        window.routeTo('integrations');
    }
}

// ── 事件委托 ──────────────────────────────────────────────────
function bind() {
    const el = sec();
    if (!el || (el as HTMLElement).dataset.dxBound) return;
    (el as HTMLElement).dataset.dxBound = '1';

    el.addEventListener('click', (ev) => {
        const tg = ev.target as HTMLElement;
        const hit = (id: string) => tg.closest('#' + id);
        // 任务选择器 + 查看记录(两任务共用)
        const taskCard = tg.closest('[data-task]') as HTMLElement | null;
        if (taskCard) return selectTask(taskCard.dataset.task as 'invoice' | 'identity');
        if (hit('dx-records')) return openRecords();
        // 发票任务:全部交给发票模块,不落入身份证处理器
        if (S.task === 'invoice') {
            onInvoiceClick(tg);
            return;
        }
        if (hit('dx-pick') || (tg.closest('#dx-drop') && !S.file)) return pickFile();
        if (hit('dx-replace')) {
            S.file = null;
            return renderUpload();
        }
        if (hit('dx-start')) return void startRecognize();
        if (hit('dx-back-up')) return backToUpload();
        if (hit('dx-go-confirm')) return void enterConfirm();
        if (hit('dx-restart')) return resetFlow();
        if (tg.closest('.dx-save-btn')) return openModal();
        if (hit('dx-m-cancel')) return closeModal();
        if (hit('dx-m-ok')) return void doSave();
        if (hit('dx-all-new')) {
            DX_COMPARE.filter(
                (c) => norm(newCompareVal(c.key)) !== norm(dmsCompareVal(c.key))
            ).forEach((c) => (S.pick[c.key] = newCompareVal(c.key) ? 'new' : 'dms'));
            applyDecisionToForm();
            syncMirror();
            return renderConfirm();
        }
        if (hit('dx-all-dms')) {
            DX_COMPARE.forEach((c) => (S.pick[c.key] = 'dms'));
            applyDecisionToForm();
            syncMirror();
            return renderConfirm();
        }
        const cand = tg.closest('[data-cid]') as HTMLElement | null;
        if (cand) {
            S.selectedId = cand.dataset.cid!;
            el.querySelectorAll('.dx-cand').forEach((x) =>
                x.classList.toggle('active', x === cand)
            );
            return;
        }
        const tab = tg.closest('[data-tab]') as HTMLElement | null;
        if (tab) {
            S.tab = tab.dataset.tab as typeof S.tab;
            syncFormFromDom();
            return renderConfirm();
        }
        const dec = tg.closest('[data-decision]') as HTMLElement | null;
        if (dec) {
            S.decision = dec.dataset.decision as typeof S.decision;
            applyDecisionToForm();
            syncMirror();
            return renderConfirm();
        }
        const pickBtn = tg.closest('.dx-pick [data-src]') as HTMLElement | null;
        if (pickBtn) {
            const key = (pickBtn.closest('[data-key]') as HTMLElement).dataset.key!;
            S.pick[key] = pickBtn.dataset.src as 'new' | 'dms';
            applyDecisionToForm();
            syncMirror();
            return renderConfirm();
        }
        const mir = tg.closest('[data-mirror]') as HTMLElement | null;
        if (mir) {
            const sfx = mir.dataset.mirror!;
            S.sameAs[sfx] = !S.sameAs[sfx];
            syncFormFromDom();
            return renderConfirm();
        }
        // 全字段表单分组折叠(F)· switch 已在上面优先处理,这里只接标题区其余点击
        const fsecH = tg.closest('.dx-fsec-h') as HTMLElement | null;
        if (fsecH) {
            const secEl = fsecH.closest('[data-sec]') as HTMLElement | null;
            if (secEl) {
                syncFormFromDom();
                const id = secEl.dataset.sec!;
                S.openSec[id] = !S.openSec[id];
                return renderConfirm();
            }
        }
    });

    el.addEventListener('change', (ev) => {
        const tg = ev.target as HTMLElement;
        if (S.task === 'invoice') {
            onInvoiceChange(tg);
            return;
        }
        if (tg.id === 'dx-file') return onFile((tg as HTMLInputElement).files?.[0] || null);
        if (tg.matches('select[data-geo]')) return void onGeoChange(tg as HTMLSelectElement);
        const fk = (tg as HTMLElement).dataset?.fk;
        if (fk) S.form[fk] = (tg as HTMLInputElement).value;
    });

    el.addEventListener('dragover', (ev) => {
        if (S.step !== 1) return;
        ev.preventDefault();
        el.querySelector('.dx-drop')?.classList.add('drag-over');
    });
    el.addEventListener('dragleave', () =>
        el.querySelector('.dx-drop')?.classList.remove('drag-over')
    );
    el.addEventListener('drop', (ev) => {
        if (S.step !== 1) return;
        ev.preventDefault();
        el.querySelector('.dx-drop')?.classList.remove('drag-over');
        const files = (ev as DragEvent).dataTransfer?.files;
        if (S.task === 'invoice') return void onInvoiceDrop(files);
        onFile(files?.[0] || null);
    });
}

// 续步:软导航回来时复原到离开的那一步。只在内存态够复原该步时才复原,否则回落第 1 步
// (硬刷新后内存态已空 → 守门不通过 → 干净从头)。成功页不复原。
function resumeFlow(): boolean {
    const memo = readStep('dms-intake');
    if (!memo || (memo.ctx && memo.ctx !== S.task)) return false;
    if (S.task === 'invoice') {
        if (IV.view !== 'review' && IV.view !== 'submit') return false;
        rerenderInvoice();
        return true;
    }
    if (!S.ocr) return false; // 身份证步 2/3 都依赖识别结果
    if (memo.step === 2) {
        renderMatch();
        showStep(2, 'dx-s-match');
        return true;
    }
    if (memo.step === 3) {
        renderConfirm();
        showStep(3, 'dx-s-confirm');
        return true;
    }
    return false;
}

window.loadDmsIntake = function () {
    const el = sec();
    if (!el) return;
    el.innerHTML = dxShell(t, S.task);
    bind();
    if (!resumeFlow()) resetFlow();
};

if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('dms-intake', () => {
        if (!sec()?.querySelector('.dmsx')) return;
        sec()!.innerHTML = dxShell(t, S.task);
        if (S.task === 'invoice') return rerenderInvoice();
        const map: Record<number, string> = {
            1: 'dx-s-upload',
            2: 'dx-s-match',
            3: 'dx-s-confirm',
            4: 'dx-s-success',
        };
        if (S.step === 1) renderUpload();
        else if (S.step === 2) renderMatch();
        else if (S.step === 3) renderConfirm();
        showStep(S.step, map[S.step] || 'dx-s-upload');
    });
}
