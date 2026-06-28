// ============================================================
// 客户知识 · 文档库 tab(KNOWLEDGE feature · 阶段2)
//
// 接 /api/knowledge/documents:拖拽/选择上传(同步处理,返回即终态)、列表、删除。
// 四态:加载骨架 / 空(引导上传)/ 错误(可重试)/ 列表。文档按当前账套主体隔离
// (kbRequest 自动附 workspace_client_id);未选账套则落 firm-wide 知识库。
// 由 knowledge-center 在进页 / 切到文档库 tab 时调 window._kbRenderDocs。
// ============================================================
/* global showToast, showConfirm */
import { kbEsc, kbIcon, kbRequest, kbT, kbUpload } from './knowledge-api.js';

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

function statusBadge(d: KbDoc): string {
    if (d.status === 'ready') {
        return `<span class="kb-badge ready"><span class="kb-bdot"></span>${kbEsc(kbT('kb-doc-ready', '已就绪'))}</span>`;
    }
    if (d.status === 'failed') {
        return `<span class="kb-badge failed"><span class="kb-bdot"></span>${kbEsc(kbT('kb-doc-failed', '失败'))}</span>`;
    }
    const label =
        d.status === 'uploading'
            ? kbT('kb-doc-uploading', '上传中…')
            : kbT('kb-doc-parsing', '解析中');
    return `<span class="kb-badge parsing"><span class="kb-bdot"></span>${kbEsc(label)}</span>`;
}

function errText(code: string | null): string {
    if (code === 'unsupported_document')
        return kbT('kb-err-unsupported_document', '不支持的文件类型');
    if (code === 'embedding_failed') return kbT('kb-err-embedding_failed', '向量化失败，可重试');
    if (code === 'processing_failed')
        return kbT('kb-err-processing_failed', '文件无法解析，可能已损坏或加密');
    return code ? kbT('kb-doc-failed', '失败') : '';
}

function fmtDate(iso: string): string {
    return (iso || '').slice(0, 10);
}

function rowHtml(d: KbDoc): string {
    let sub: string;
    if (d.status === 'failed' && d.error_code) {
        sub = `<div class="kb-doc-sub err">${kbEsc(errText(d.error_code))}</div>`;
    } else if (d.status === 'uploading') {
        sub = `<div class="kb-doc-sub">${kbEsc(kbT('kb-doc-uploading', '上传中…'))}</div>`;
    } else {
        sub = `<div class="kb-doc-sub">${kbEsc((d.source_type || '').toUpperCase())} · ${kbEsc(fmtDate(d.created_at))}</div>`;
    }
    // 上传中的临时行(负 id)不给删除入口,避免删到一笔还没落库的占位。
    const del =
        d.status === 'uploading'
            ? ''
            : `<button class="btn btn-sm btn-ghost kb-doc-del" data-id="${d.id}">${kbEsc(kbT('kb-doc-delete', '删除'))}</button>`;
    return `<div class="kb-doc-row" data-id="${d.id}">
        <div class="kb-doc-ic">${docIcon(d.source_type)}</div>
        <div class="kb-doc-meta"><div class="kb-doc-name">${kbEsc(d.filename)}</div>${sub}</div>
        ${statusBadge(d)}${del}
    </div>`;
}

function docIcon(t: string): string {
    const e = (t || '').toLowerCase();
    if (e === 'doc' || e === 'docx') return kbIcon('file-text');
    if (e === 'xls' || e === 'xlsx' || e === 'csv') return kbIcon('sheet');
    if (['png', 'jpg', 'jpeg', 'webp'].includes(e)) return kbIcon('image');
    return kbIcon('file');
}

function listEl(): HTMLElement | null {
    return document.getElementById('kb-doc-list');
}

function renderList(): void {
    const el = listEl();
    if (!el) return;
    if (!_docs.length) {
        // 空态:只留上传区(已含引导文案)· 不再多框一个空盒(去「双框」· 收拢不悬空)。
        el.style.display = 'none';
        el.innerHTML = '';
        return;
    }
    el.style.display = '';
    el.innerHTML = _docs.map(rowHtml).join('');
}

function setListState(html: string): void {
    const el = listEl();
    if (el) {
        el.style.display = ''; // 骨架/错误态要可见(仅空态隐藏 · 见 renderList)
        el.innerHTML = html;
    }
}

async function loadList(): Promise<void> {
    setListState(
        `<div class="kb-skel"><div class="kb-skrow"></div><div class="kb-skrow"></div><div class="kb-skrow"></div></div>`
    );
    const r = await kbRequest<{ documents: KbDoc[] }>('GET', '/documents');
    if (!r.ok) {
        setListState(`<div class="kb-empty err">
            <div>${kbEsc(kbT('kb-doc-error', '加载失败'))}</div>
            <button class="btn btn-sm kb-doc-reload" style="margin-top:12px">${kbEsc(kbT('kb-doc-retry', '重试'))}</button>
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
        renderList(); // 乐观行立即入列表(任何前态:空/骨架/列表都走同一渲染路径)
        const r = await kbUpload<{ document: KbDoc }>(file);
        const idx = _docs.findIndex((d) => d.id === tempId);
        if (idx < 0) continue;
        if (r.ok && r.data?.document) {
            _docs[idx] = r.data.document;
            if (r.data.document.status === 'failed') {
                showToast(kbT('kb-doc-failed', '失败') + '：' + file.name, 'error');
            }
        } else {
            _docs.splice(idx, 1);
            showToast(kbT('kb-upload-fail', '上传失败') + '：' + file.name, 'error');
        }
        renderList();
    }
}

async function deleteDoc(id: number): Promise<void> {
    const ok =
        typeof showConfirm === 'function'
            ? await showConfirm(
                  kbT('kb-doc-del-confirm', '确定删除这份文档？删除后 AI 将不再引用它。')
              )
            : true;
    if (!ok) return;
    const r = await kbRequest('DELETE', '/documents/' + id);
    if (r.ok) {
        _docs = _docs.filter((d) => d.id !== id);
        renderList();
    } else {
        showToast(kbT('kb-doc-del-fail', '删除失败'), 'error');
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
/* 框 skin(虚线 / hover / 拖拽 / 整框可点)统一走 .up-dz(home-55)· 此处只留布局与文字 */
.kb-up{padding:22px;text-align:center;color:var(--ink-3,#999);margin-bottom:16px}
.kb-up svg{width:26px;height:26px;stroke:currentColor;fill:none;stroke-width:1.5;margin-bottom:6px}
.kb-up b{color:var(--btn-blue,var(--accent))}
.kb-up .kb-up-types{font-size:11px;color:var(--ink-3,#999);margin-top:4px}
.kb-doc-list{background:var(--card,var(--card));border:1px solid var(--line,var(--line));border-radius:12px;overflow:hidden;min-height:80px}
.kb-doc-row{display:flex;align-items:center;gap:13px;padding:13px 16px;border-bottom:1px solid var(--line,var(--line))}
.kb-doc-row:last-child{border-bottom:none}
.kb-doc-ic{width:34px;height:34px;border-radius:8px;background:var(--bg,var(--line2));display:grid;place-items:center;flex-shrink:0;color:var(--ink-2,#555)}
.kb-doc-ic svg{width:17px;height:17px}
.kb-doc-meta{flex:1;min-width:0}
.kb-doc-name{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kb-doc-sub{font-size:11px;color:var(--ink-3,#999);margin-top:1px}
.kb-doc-sub.err{color:var(--danger,var(--red))}
.kb-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:600;flex-shrink:0}
.kb-bdot{width:6px;height:6px;border-radius:50%}
.kb-badge.ready{background:var(--green-weak);color:var(--green)}.kb-badge.ready .kb-bdot{background:var(--green)}
.kb-badge.parsing{background:var(--accent-weak);color:var(--accent-deep)}.kb-badge.parsing .kb-bdot{background:var(--accent)}
.kb-badge.failed{background:var(--red-weak);color:var(--red)}.kb-badge.failed .kb-bdot{background:var(--red)}
.kb-doc-del{color:var(--ink-3,#999)!important}
.kb-doc-del:hover{color:var(--danger,var(--red))!important}
.kb-empty{text-align:center;padding:42px 20px;color:var(--ink-3,#999)}
.kb-empty.err{color:var(--danger,var(--red))}
.kb-empty svg{width:38px;height:38px;stroke:var(--ink-4,#cbd5e0);fill:none;stroke-width:1.4;margin-bottom:10px}
.kb-empty h4{color:var(--ink-2,#555);font-size:14px;margin:0 0 6px}
.kb-skel{padding:14px}
.kb-skrow{height:46px;border-radius:8px;margin-bottom:10px;background:linear-gradient(90deg,var(--line2) 25%,var(--line) 50%,var(--line2) 75%);background-size:200% 100%;animation:kbShine 1.3s infinite}
.kb-skrow:last-child{margin-bottom:0}
@keyframes kbShine{to{background-position:-200% 0}}
`;
        document.head.appendChild(st);
    }

    pane.innerHTML = `
        <div class="kb-up up-dz" id="kb-up">
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
            up.classList.add('up-over');
        })
    );
    ['dragleave', 'drop'].forEach((ev) =>
        up.addEventListener(ev, (e) => {
            e.preventDefault();
            up.classList.remove('up-over');
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

// 切语言:已渲染的文档行用 kbT() 取的是当时语言 · 重渲一遍跟上(静态壳走全局 applyLang)
if (!Array.isArray(window.__i18nSubs)) window.__i18nSubs = [];
window.__i18nSubs.push({
    name: 'knowledge-documents',
    fn: () => {
        if (_shellBuilt) renderList();
    },
});
