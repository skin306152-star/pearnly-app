// ============================================================
// 客户知识 · 来源出处弹窗(KNOWLEDGE feature · 阶段3)
//
// 问答答案里每条 citation 可点 → 本弹窗显示该结论引用自哪份文档 + 相关度。
// 用 .modal 体系(项目铁律:新 UI 用弹窗不用抽屉)。后端 citation 暂不含原文片段,
// 故先呈现文档来源 + 相关度;原文高亮预览待后端补「按 chunk 取文」接口后再加。
// window._kbOpenSource(citation) 由问答模块(tab + 悬浮件)共用。
// ============================================================
/* global escapeHtml */

export interface KbCitation {
    chunk_id?: number;
    document_id?: number;
    filename?: string;
    score?: number;
}

function sT(key: string, fb: string): string {
    if (typeof window.t === 'function') {
        const s = window.t(key);
        if (s && s !== key) return s;
    }
    return fb;
}

function esc(s: unknown): string {
    return typeof escapeHtml === 'function' ? escapeHtml(String(s ?? '')) : String(s ?? '');
}

function ensureDom(): void {
    if (document.getElementById('kb-src-mask')) return;

    const st = document.createElement('style');
    st.id = 'kb-src-style';
    st.textContent = `
.kb-src-mask{position:fixed;inset:0;background:rgba(17,17,17,.42);z-index:1200;display:none;align-items:center;justify-content:center;padding:20px}
.kb-src-mask.open{display:flex}
.kb-src-modal{background:#fff;border-radius:16px;width:480px;max-width:100%;max-height:86vh;overflow:auto;box-shadow:0 30px 80px rgba(17,17,17,.3)}
.kb-src-head{display:flex;align-items:flex-start;gap:13px;padding:20px 22px 0}
.kb-src-head .ic{width:42px;height:42px;border-radius:11px;background:var(--bg,#f4f4f0);display:grid;place-items:center;font-size:20px;flex-shrink:0}
.kb-src-head h3{font-size:16px;font-weight:800;margin:0}
.kb-src-head .sub{font-size:12px;color:var(--ink-3,#999);margin-top:2px}
.kb-src-head .x{margin-left:auto;color:var(--ink-3,#999);font-size:18px;width:30px;height:30px;border-radius:8px;display:grid;place-items:center;cursor:pointer;border:none;background:none}
.kb-src-head .x:hover{background:var(--bg,#f4f4f0);color:var(--ink,#111)}
.kb-src-body{padding:16px 22px 22px}
.kb-src-doc{display:flex;align-items:center;gap:12px;border:1px solid var(--border,#e8e8e3);border-radius:12px;padding:14px 16px}
.kb-src-doc .di{width:38px;height:38px;border-radius:9px;background:var(--bg,#f4f4f0);display:grid;place-items:center;font-size:17px;flex-shrink:0}
.kb-src-doc .dn{font-weight:700;word-break:break-all}
.kb-src-doc .dm{font-size:12px;color:var(--ink-3,#999);margin-top:2px}
.kb-src-rel{display:inline-flex;align-items:center;gap:6px;margin-top:14px;font-size:12px;color:var(--info-ink,#1e40af);background:var(--info-bg,#dbeafe);border-radius:8px;padding:7px 11px}
.kb-src-note{font-size:12px;color:var(--ink-3,#999);margin-top:14px;line-height:1.6}
`;
    document.head.appendChild(st);

    const mask = document.createElement('div');
    mask.id = 'kb-src-mask';
    mask.className = 'kb-src-mask';
    mask.innerHTML = `<div class="kb-src-modal" id="kb-src-modal" role="dialog" aria-modal="true"></div>`;
    document.body.appendChild(mask);

    mask.addEventListener('click', (e) => {
        if (e.target === mask || (e.target as HTMLElement).closest('[data-kb-src-close]')) close();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mask.classList.contains('open')) close();
    });
}

function close(): void {
    document.getElementById('kb-src-mask')?.classList.remove('open');
}

function open(cit: KbCitation): void {
    ensureDom();
    const modal = document.getElementById('kb-src-modal');
    if (!modal) return;
    const name = cit.filename || sT('kb-src-unknown', '未知来源');
    const pct =
        typeof cit.score === 'number'
            ? Math.round(Math.max(0, Math.min(1, cit.score)) * 100)
            : null;
    modal.innerHTML = `
        <div class="kb-src-head">
            <span class="ic">📄</span>
            <div>
                <h3>${esc(sT('kb-src-title', '来源出处'))}</h3>
                <div class="sub">${esc(sT('kb-src-from', '此结论引用自以下文档'))}</div>
            </div>
            <button class="x" data-kb-src-close aria-label="close">✕</button>
        </div>
        <div class="kb-src-body">
            <div class="kb-src-doc">
                <span class="di">📄</span>
                <div><div class="dn">${esc(name)}</div>
                <div class="dm">${esc(sT('kb-src-doc-note', '已就绪 · 已建立向量索引'))}</div></div>
            </div>
            ${pct !== null ? `<div class="kb-src-rel">🎯 ${esc(sT('kb-src-relevance', '相关度'))} ${pct}%</div>` : ''}
            <div class="kb-src-note">${esc(sT('kb-src-explain', 'AI 据此份文档作答 · 你可在文档库打开原件核对。原文片段高亮预览即将上线。'))}</div>
        </div>
    `;
    document.getElementById('kb-src-mask')?.classList.add('open');
}

window._kbOpenSource = open;
