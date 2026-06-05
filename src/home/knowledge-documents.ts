// ============================================================
// 客户知识 · 文档库 tab(KNOWLEDGE feature · 阶段2)
//
// 接 /api/knowledge/documents:拖拽/选择上传(同步处理,返回即终态)、列表、删除。
// 四态:加载骨架 / 空(引导上传)/ 错误(可重试)/ 列表。文档按当前账套主体隔离
// (kbRequest 自动附 workspace_client_id);未选账套则落 firm-wide 知识库。
// 由 knowledge-center 在进页 / 切到文档库 tab 时调 window._kbRenderDocs。
// ============================================================
/* global escapeHtml, showToast, showConfirm */
import { kbRequest, kbUpload } from './knowledge-api.js';

interface KbDoc {
    id: number;
    filename: string;
    source_type: string;
    status: string;
    error_code: string | null;
    created_at: string;
}

let _shellBuilt = false;
let _docs: KbDoc[] = [];

function dT(key: string, fb: string): string {
    if (typeof window.t === 'function') {
        const s = window.t(key);
        if (s && s !== key) return s;
    }
    return fb;
}

function esc(s: unknown): string {
    return typeof escapeHtml === 'function' ? escapeHtml(String(s ?? '')) : String(s ?? '');
}

function statusBadge(d: KbDoc): string {
    if (d.status === 'ready') {
        return `<span class="kb-badge ready"><span class="kb-bdot"></span>${esc(dT('kb-doc-ready', '已就绪'))}</span>`;
    }
    if (d.status === 'failed') {
        return `<span class="kb-badge failed"><span class="kb-bdot"></span>${esc(dT('kb-doc-failed', '失败'))}</span>`;
    }
    return `<span class="kb-badge parsing"><span class="kb-bdot"></span>${esc(dT('kb-doc-parsing', '解析中'))}</span>`;
}

function errText(code: string | null): string {
    if (code === 'unsupported_document')
        return dT('kb-err-unsupported_document', '不支持的文件类型');
    if (code === 'embedding_failed') return dT('kb-err-embedding_failed', '向量化失败，可重试');
    return code ? dT('kb-doc-failed', '失败') : '';
}

function fmtDate(iso: string): string {
    return (iso || '').slice(0, 10);
}

function rowHtml(d: KbDoc): string {
    const sub =
        d.status === 'failed' && d.error_code
            ? `<div class="kb-doc-sub err">${esc(errText(d.error_code))}</div>`
            : `<div class="kb-doc-sub">${esc((d.source_type || '').toUpperCase())} · ${esc(fmtDate(d.created_at))}</div>`;
    const del = `<button class="btn btn-sm btn-ghost kb-doc-del" data-id="${d.id}">${esc(dT('kb-doc-delete', '删除'))}</button>`;
    return `<div class="kb-doc-row" data-id="${d.id}">
        <div class="kb-doc-ic">${docIcon(d.source_type)}</div>
        <div class="kb-doc-meta"><div class="kb-doc-name">${esc(d.filename)}</div>${sub}</div>
        ${statusBadge(d)}${del}
    </div>`;
}

function docIcon(t: string): string {
    const e = (t || '').toLowerCase();
    if (e === 'pdf') return '📄';
    if (e === 'doc' || e === 'docx') return '📘';
    if (e === 'xls' || e === 'xlsx' || e === 'csv') return '📊';
    if (['png', 'jpg', 'jpeg', 'webp'].includes(e)) return '🖼️';
    return '📄';
}

function listEl(): HTMLElement | null {
    return document.getElementById('kb-doc-list');
}

function renderList(): void {
    const el = listEl();
    if (!el) return;
    if (!_docs.length) {
        el.innerHTML = `<div class="kb-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>
            <h4>${esc(dT('kb-doc-empty-title', '还没有文档'))}</h4>
            <div>${esc(dT('kb-doc-empty', '上传客户合同、采购政策、税务登记等资料，AI 检查发票和问答时引用。'))}</div>
        </div>`;
        return;
    }
    el.innerHTML = _docs.map(rowHtml).join('');
}

function setListState(html: string): void {
    const el = listEl();
    if (el) el.innerHTML = html;
}

async function loadList(): Promise<void> {
    setListState(
        `<div class="kb-skel"><div class="kb-skrow"></div><div class="kb-skrow"></div><div class="kb-skrow"></div></div>`
    );
    const r = await kbRequest<{ documents: KbDoc[] }>('GET', '/documents');
    if (!r.ok) {
        setListState(`<div class="kb-empty err">
            <div>${esc(dT('kb-doc-error', '加载失败'))}</div>
            <button class="btn btn-sm kb-doc-reload" style="margin-top:12px">${esc(dT('kb-doc-retry', '重试'))}</button>
        </div>`);
        return;
    }
    _docs = (r.data?.documents || []).filter((d) => d.status !== 'deleted');
    renderList();
}

async function uploadFiles(files: FileList | File[]): Promise<void> {
    const list = Array.from(files);
    if (!list.length) return;
    for (const file of list) {
        const tempId = -Date.now() - Math.floor(Math.random() * 1000);
        _docs.unshift({
            id: tempId,
            filename: file.name,
            source_type: (file.name.split('.').pop() || '').toLowerCase(),
            status: 'uploading',
            error_code: null,
            created_at: new Date().toISOString(),
        } as KbDoc);
        renderUploading(tempId);
        const r = await kbUpload<{ document: KbDoc }>(file);
        const idx = _docs.findIndex((d) => d.id === tempId);
        if (idx < 0) continue;
        if (r.ok && r.data?.document) {
            _docs[idx] = r.data.document;
            if (r.data.document.status === 'failed') {
                showToast(dT('kb-doc-failed', '失败') + '：' + file.name, 'error');
            }
        } else {
            _docs.splice(idx, 1);
            showToast(dT('kb-upload-fail', '上传失败') + '：' + file.name, 'error');
        }
        renderList();
    }
}

function renderUploading(tempId: number): void {
    const el = listEl();
    if (!el) return;
    const d = _docs.find((x) => x.id === tempId);
    if (!d) return;
    if (_docs.length === 1) el.innerHTML = '';
    const div = document.createElement('div');
    div.innerHTML = `<div class="kb-doc-row" data-id="${tempId}">
        <div class="kb-doc-ic">${docIcon(d.source_type)}</div>
        <div class="kb-doc-meta"><div class="kb-doc-name">${esc(d.filename)}</div>
        <div class="kb-doc-sub">${esc(dT('kb-doc-uploading', '上传中…'))}</div></div>
        <span class="kb-badge parsing"><span class="kb-bdot"></span>${esc(dT('kb-doc-uploading', '上传中…'))}</span>
    </div>`;
    el.insertBefore(div.firstElementChild as Node, el.firstChild);
}

async function deleteDoc(id: number): Promise<void> {
    const ok =
        typeof showConfirm === 'function'
            ? await showConfirm(
                  dT('kb-doc-del-confirm', '确定删除这份文档？删除后 AI 将不再引用它。')
              )
            : true;
    if (!ok) return;
    const r = await kbRequest('DELETE', '/documents/' + id);
    if (r.ok) {
        _docs = _docs.filter((d) => d.id !== id);
        renderList();
    } else {
        showToast(dT('kb-doc-del-fail', '删除失败'), 'error');
    }
}

function ensureShell(): void {
    const pane = document.getElementById('kb-pane-docs');
    if (!pane) return;
    if (_shellBuilt && pane.querySelector('#kb-doc-list')) return;

    if (!document.getElementById('kb-docs-style')) {
        const st = document.createElement('style');
        st.id = 'kb-docs-style';
        st.textContent = `
.kb-up{border:1.5px dashed var(--border,#e8e8e3);border-radius:12px;background:var(--card,#fff);padding:22px;text-align:center;color:var(--ink-3,#999);margin-bottom:16px;cursor:pointer;transition:.15s}
.kb-up:hover,.kb-up.drag{border-color:var(--brand,#111);color:var(--ink-2,#555);background:var(--bg,#f4f4f0)}
.kb-up svg{width:26px;height:26px;stroke:currentColor;fill:none;stroke-width:1.5;margin-bottom:6px}
.kb-up b{color:var(--btn-blue,#2563eb)}
.kb-up .kb-up-types{font-size:11px;color:var(--ink-3,#999);margin-top:4px}
.kb-doc-list{background:var(--card,#fff);border:1px solid var(--border,#e8e8e3);border-radius:12px;overflow:hidden;min-height:80px}
.kb-doc-row{display:flex;align-items:center;gap:13px;padding:13px 16px;border-bottom:1px solid var(--border,#e8e8e3)}
.kb-doc-row:last-child{border-bottom:none}
.kb-doc-ic{width:34px;height:34px;border-radius:8px;background:var(--bg,#f4f4f0);display:grid;place-items:center;flex-shrink:0;font-size:15px}
.kb-doc-meta{flex:1;min-width:0}
.kb-doc-name{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kb-doc-sub{font-size:11px;color:var(--ink-3,#999);margin-top:1px}
.kb-doc-sub.err{color:var(--danger,#dc2626)}
.kb-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:600;flex-shrink:0}
.kb-bdot{width:6px;height:6px;border-radius:50%}
.kb-badge.ready{background:#ecfdf3;color:#067647}.kb-badge.ready .kb-bdot{background:#16a34a}
.kb-badge.parsing{background:#dbeafe;color:#1e40af}.kb-badge.parsing .kb-bdot{background:#2563eb}
.kb-badge.failed{background:#fef3f2;color:#b42318}.kb-badge.failed .kb-bdot{background:#dc2626}
.kb-doc-del{color:var(--ink-3,#999)!important}
.kb-doc-del:hover{color:var(--danger,#dc2626)!important}
.kb-empty{text-align:center;padding:42px 20px;color:var(--ink-3,#999)}
.kb-empty.err{color:var(--danger,#dc2626)}
.kb-empty svg{width:38px;height:38px;stroke:var(--ink-4,#cbd5e0);fill:none;stroke-width:1.4;margin-bottom:10px}
.kb-empty h4{color:var(--ink-2,#555);font-size:14px;margin:0 0 6px}
.kb-skel{padding:14px}
.kb-skrow{height:46px;border-radius:8px;margin-bottom:10px;background:linear-gradient(90deg,#f0f0ec 25%,#f7f7f3 50%,#f0f0ec 75%);background-size:200% 100%;animation:kbShine 1.3s infinite}
.kb-skrow:last-child{margin-bottom:0}
@keyframes kbShine{to{background-position:-200% 0}}
`;
        document.head.appendChild(st);
    }

    pane.innerHTML = `
        <div class="kb-up" id="kb-up">
            <svg viewBox="0 0 24 24"><path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>
            <div><span data-i18n="kb-upload-hint">把文档拖到这里，或</span> <b data-i18n="kb-upload">点击上传</b></div>
            <div class="kb-up-types" data-i18n="kb-upload-types">支持 PDF · Word · Excel · 图片 — 合同 / 政策 / 税务登记等客户私有资料</div>
            <input type="file" id="kb-file" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.png,.jpg,.jpeg,.webp" style="display:none">
        </div>
        <div class="kb-doc-list" id="kb-doc-list"></div>
    `;

    // 注入的 data-i18n 元素须立即补译(本壳在 page-knowledge 翻译扫描之后才建 · 否则显默认中文)
    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            pane.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n') as string;
                if (I[lang][k]) el.textContent = I[lang][k];
            });
        }
    } catch {
        /* 初译失败不致命 · 切语言会补 */
    }

    const up = pane.querySelector('#kb-up') as HTMLElement;
    const input = pane.querySelector('#kb-file') as HTMLInputElement;
    up.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).closest('input')) return;
        input.click();
    });
    input.addEventListener('change', () => {
        if (input.files) uploadFiles(input.files);
        input.value = '';
    });
    ['dragenter', 'dragover'].forEach((ev) =>
        up.addEventListener(ev, (e) => {
            e.preventDefault();
            up.classList.add('drag');
        })
    );
    ['dragleave', 'drop'].forEach((ev) =>
        up.addEventListener(ev, (e) => {
            e.preventDefault();
            up.classList.remove('drag');
        })
    );
    up.addEventListener('drop', (e) => {
        const dt = (e as DragEvent).dataTransfer;
        if (dt?.files?.length) uploadFiles(dt.files);
    });

    pane.addEventListener('click', (e) => {
        const t = e.target as HTMLElement;
        const del = t.closest<HTMLElement>('.kb-doc-del');
        if (del?.dataset.id) {
            deleteDoc(Number(del.dataset.id));
            return;
        }
        if (t.closest('.kb-doc-reload')) loadList();
    });

    _shellBuilt = true;
}

function renderDocs(): void {
    // 未选账套时落 firm-wide 知识库;账套上下文由页头 kb-ws-bar 明示。
    ensureShell();
    void loadList();
}

window._kbRenderDocs = renderDocs;

// 切语言:已渲染的文档行用 dT() 取的是当时语言 · 重渲一遍跟上(静态壳走全局 applyLang)
if (!Array.isArray(window.__i18nSubs)) window.__i18nSubs = [];
window.__i18nSubs.push({
    name: 'knowledge-documents',
    fn: () => {
        if (_shellBuilt) renderList();
    },
});
