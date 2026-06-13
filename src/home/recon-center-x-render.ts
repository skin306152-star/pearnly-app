// 对账中心重设计 · 工作区表现层:上传卡四态 / 余额预检 / 就绪态 / 状态机 A–G 显隐(2026-06-14)
import {
    RX,
    rxCfg,
    rxEsc,
    rxFmtSize,
    rxFmt,
    tt,
    type RxSide,
    type RxFile,
} from './recon-center-x-store.js';

const $ = (id: string) => document.getElementById(id);

// 卡片标题按 tab+side(同一 doc_type 在不同 tab 显示名不同:vat 在收入对账叫「税表（VAT 报告）」、
// 在销项税核查叫「销项税报告」)。
const TAB_TITLES: Record<string, { left: [string, string]; right: [string, string] }> = {
    bank: { left: ['rcx-doc-statement', '银行账单'], right: ['rcx-doc-gl', '总账（GL）'] },
    income: { left: ['rcx-doc-gl', '总账（GL）'], right: ['rcx-doc-vat', '税表（VAT 报告）'] },
    tax: { left: ['rcx-doc-vatreport', '销项税报告'], right: ['rcx-doc-invoice', '销售发票明细'] },
};
const METHOD: Record<
    RxFile['method'],
    { key: string; zh: string; chipKey: string; chipZh: string }
> = {
    standard: {
        key: 'rcx-method-std',
        zh: '标准模板读取',
        chipKey: 'rcx-recommend',
        chipZh: '推荐',
    },
    table: {
        key: 'rcx-method-table',
        zh: '普通表格读取',
        chipKey: 'rcx-chip-table',
        chipZh: '导入前检查',
    },
    scan: {
        key: 'rcx-method-file',
        zh: '文件内容读取',
        chipKey: 'rcx-chip-scan',
        chipZh: '导入前检查',
    },
};

function docTitle(side: RxSide): string {
    const [k, zh] = TAB_TITLES[RX.tab][side];
    return tt(k, zh);
}

const FILE_SVG =
    '<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4"/><path d="M9 12h6M9 16h4"/></svg>';

// ── 上传卡:空态 / 已加载态 ───────────────────────────────────────
export function renderCard(side: RxSide) {
    const card = $('rcx-card-' + side);
    if (!card) return;
    const data = RX[side];
    if (!data) {
        card.className = 'rcx-upload-card';
        card.innerHTML = `
      <div class="rcx-drop-icon">${FILE_SVG}</div>
      <h3>${rxEsc(docTitle(side))}</h3>
      <div class="rcx-hint">${tt('rcx-drop-hint', '拖拽文件到这里，或从本地选择文件')}</div>
      <div class="rcx-upload-actions">
        <button class="rcx-btn rcx-primary rcx-sm" data-rcx-choose="${side}" type="button">${tt('rcx-choose-file', '选择文件')}</button>
        <button class="rcx-btn rcx-sm" data-rcx-dl-side="${side}" type="button">${tt('rcx-dl-template', '下载标准模板')}</button>
      </div>
      <div class="rcx-recommend">
        <div class="rcx-spark">✦</div>
        <div>
          <b>${tt('rcx-reco-title', '推荐标准模板：更快、更准、更少确认')}</b>
          <span>${tt('rcx-reco-sub', '直接按字段读取，并在导入前检查格式完整性')}</span>
        </div>
      </div>
      <div class="rcx-format-line">${tt('rcx-format-line', '支持 PDF / 图片 / Excel / CSV / Word · 支持多文件')}</div>
      <input data-rcx-input="${side}" type="file" hidden accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.xlsx,.xls,.csv,.doc,.docx" />`;
        return;
    }
    const m = METHOD[data.method];
    card.className = 'rcx-upload-card rcx-loaded';
    card.innerHTML = `
    <div class="rcx-file-head">
      <div class="rcx-file-type">${rxEsc(data.ext)}</div>
      <div class="rcx-file-meta">
        <b title="${rxEsc(data.file.name)}">${rxEsc(data.file.name)}</b>
        <span>${rxEsc(rxFmtSize(data.size))} · ${tt('rcx-uploaded', '上传完成')}</span>
      </div>
      <button class="rcx-file-remove" data-rcx-remove="${side}" type="button" aria-label="${tt('rcx-remove', '移除文件')}">✕</button>
    </div>
    <div class="rcx-method-box">
      <div class="rcx-method-top">
        <b>${tt(m.key, m.zh)}</b>
        <span class="rcx-method-chip ${data.method}">${tt(m.chipKey, m.chipZh)}</span>
      </div>
      <div class="rcx-check-list">
        <div class="rcx-check-row"><span>${tt('rcx-read-method', '读取方式')}</span><strong>${tt(m.key, m.zh)}</strong></div>
        <div class="rcx-check-row"><span>${tt('rcx-format', '文件格式')}</span><strong>${rxEsc(data.ext)}</strong></div>
        <div class="rcx-check-row"><span>${tt('rcx-check-state', '导入前检查')}</span><strong>${tt('rcx-check-on-start', '开始对账时执行')}</strong></div>
      </div>
    </div>
    <div class="rcx-file-cta">
      <button class="rcx-btn rcx-sm" data-rcx-preview="${side}" type="button">${tt('rcx-preview', '预览文件')}</button>
    </div>`;
}

// ── 余额预检(仅银行;其余类型隐藏)──────────────────────────────
export function renderBalance() {
    const panel = $('rcx-balance');
    if (!panel) return;
    if (!rxCfg().balance) {
        panel.classList.add('rcx-hidden');
        return;
    }
    panel.classList.remove('rcx-hidden');
    // 4 个真实手动录入(喂 *_override),期初差额实时算。值为可选,留空即不覆盖。
    const cell = (id: string, ph: string) =>
        `<input class="rcx-bal-input" id="${id}" inputmode="decimal" placeholder="${ph}" aria-label="${ph}" />`;
    const setVal = (id: string, html: string) => {
        const el = $(id);
        if (el) el.innerHTML = html;
    };
    setVal('rcx-gl-end', cell('rcx-in-gl-closing', tt('rcx-optional', '可选')));
    setVal('rcx-st-end', cell('rcx-in-stmt-closing', tt('rcx-optional', '可选')));
    setVal('rcx-st-start', cell('rcx-in-stmt-opening', tt('rcx-optional', '可选')));
    setVal('rcx-gl-start', cell('rcx-in-gl-opening', tt('rcx-optional', '可选')));
    ['rcx-in-stmt-opening', 'rcx-in-gl-opening'].forEach((id) => {
        const el = $(id);
        if (el) el.addEventListener('input', updateOpeningDiff);
    });
    updateOpeningDiff();
}

function inNum(id: string): number {
    const el = $(id) as HTMLInputElement | null;
    return el ? parseFloat(el.value) : NaN;
}

export function updateOpeningDiff() {
    const so = inNum('rcx-in-stmt-opening');
    const go = inNum('rcx-in-gl-opening');
    const el = $('rcx-opening-diff');
    if (!el) return;
    el.textContent = Number.isFinite(so) && Number.isFinite(go) ? rxFmt(so - go) : '—';
}

// 收集 anchor override(银行)→ 仅填了的才回传
export function collectOverrides(fd: FormData) {
    if (!rxCfg().balance) return;
    const map: Array<[string, string]> = [
        ['rcx-in-gl-closing', 'gl_closing_override'],
        ['rcx-in-stmt-closing', 'stmt_closing_override'],
        ['rcx-in-stmt-opening', 'stmt_opening_override'],
        ['rcx-in-gl-opening', 'gl_opening_override'],
    ];
    for (const [id, field] of map) {
        const v = inNum(id);
        if (Number.isFinite(v)) fd.append(field, String(v));
    }
}

// ── 就绪态 + 开始按钮(状态机 B/C/D 的判定)─────────────────────
export function updateReady() {
    const both = !!(RX.left && RX.right);
    const startBtn = $('rcx-start-btn') as HTMLButtonElement | null;
    const ready = $('rcx-ready-text');
    if (startBtn) startBtn.disabled = !both || RX.running;
    if (ready) {
        ready.textContent = both
            ? tt('rcx-ready-go', '两份文件已就绪，可开始对账')
            : RX.left || RX.right
              ? tt('rcx-ready-one', '请再上传另一份文件')
              : tt('rcx-ready-await', '请上传两份文件后开始对账');
    }
    // 余额来源标签
    const glS = $('rcx-gl-source');
    const stS = $('rcx-st-source');
    if (glS)
        glS.textContent = RX.right
            ? tt('rcx-source-loaded', '已上传')
            : tt('rcx-await-upload', '待上传');
    if (stS)
        stS.textContent = RX.left
            ? tt('rcx-source-loaded', '已上传')
            : tt('rcx-await-upload', '待上传');
}

// ── 状态机 A–G 显隐 ───────────────────────────────────────────────
export type RxView = 'workspace' | 'processing' | 'results' | 'fail';
export function showView(view: RxView, bannerHidden: boolean) {
    const ws = $('rcx-workspace');
    const pf = document.querySelector('.rcx-preflight') as HTMLElement | null;
    const banner = $('rcx-banner');
    const proc = $('rcx-processing');
    const res = $('rcx-results');
    const fail = $('rcx-fail');
    const history = $('rcx-history');
    const wsShow = view === 'workspace';
    if (ws) ws.classList.toggle('rcx-hidden', !wsShow);
    if (pf) pf.style.display = wsShow ? '' : 'none';
    if (history) history.classList.toggle('rcx-hidden', !wsShow);
    if (banner) banner.classList.toggle('rcx-hidden', !wsShow || bannerHidden);
    if (proc) proc.classList.toggle('rcx-show', view === 'processing');
    if (res) res.classList.toggle('rcx-show', view === 'results');
    if (fail) fail.classList.toggle('rcx-show', view === 'fail');
}

export function setTaskTitle() {
    const el = $('rcx-task-title');
    if (!el) return;
    const map: Record<string, [string, string]> = {
        bank: ['rcx-task-bank', '银行对账 · 主操作'],
        income: ['rcx-task-income', '收入对账 · 主操作'],
        tax: ['rcx-task-tax', '销项税报告核查 · 主操作'],
    };
    const [k, zh] = map[RX.tab];
    el.textContent = tt(k, zh);
}
