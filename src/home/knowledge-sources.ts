// ============================================================
// 客户知识 · 来源出处弹窗(KNOWLEDGE feature · 阶段3)
//
// 问答答案里每条 citation 可点 → 本弹窗按 chunk_id 取被引用的原文段落,把命中那段
// 黄底高亮、相邻段落作上下文,让会计一眼核对「AI 这句话从哪来」。用 .modal 体系
// (项目铁律:新 UI 用弹窗不用抽屉)。window._kbOpenSource(citation) 由问答模块共用。
// 注:chunk 不含页码/章节(切片时页边界已丢),故不显示「第 X 页」,只显原文 + 高亮。
// ============================================================
import { kbEsc, kbIcon, kbModalShell, kbRequest, kbT, type KbModal } from './knowledge-api.js';

export interface KbCitation {
    chunk_id?: number;
    document_id?: number;
    filename?: string;
    score?: number;
}

interface KbChunkSegment {
    chunk_index: number;
    text: string;
    matched: boolean;
}

interface KbChunkContext {
    chunk_id: number;
    document_id: number;
    filename: string;
    chunk_index: number;
    segments: KbChunkSegment[];
}

let _shell: KbModal | null = null;

function ensureDom(): void {
    if (_shell) return;

    const st = document.createElement('style');
    st.id = 'kb-src-style';
    st.textContent = `
.kb-src-mask{position:fixed;inset:0;background:rgba(17,17,17,.42);z-index:1200;display:none;align-items:center;justify-content:center;padding:20px}
.kb-src-mask.open{display:flex}
.kb-src-modal{background:#fff;border-radius:16px;width:560px;max-width:100%;max-height:86vh;overflow:auto;box-shadow:0 30px 80px rgba(17,17,17,.3)}
.kb-src-head{display:flex;align-items:flex-start;gap:13px;padding:20px 22px 0}
.kb-src-head .ic{width:42px;height:42px;border-radius:11px;background:var(--bg,#f4f4f0);display:grid;place-items:center;color:var(--ink-2,#555);flex-shrink:0}
.kb-src-head .ic svg{width:20px;height:20px}
.kb-src-head h3{font-size:16px;font-weight:800;margin:0;word-break:break-all}
.kb-src-head .sub{font-size:12px;color:var(--ink-3,#999);margin-top:2px}
.kb-src-head .x{margin-left:auto;color:var(--ink-3,#999);width:30px;height:30px;border-radius:8px;display:grid;place-items:center;cursor:pointer;border:none;background:none;flex-shrink:0}
.kb-src-head .x svg{width:16px;height:16px}
.kb-src-head .x:hover{background:var(--bg,#f4f4f0);color:var(--ink,#111)}
.kb-src-body{padding:16px 22px 22px}
.kb-src-rel{display:inline-flex;align-items:center;gap:6px;margin-bottom:12px;font-size:12px;color:var(--info-ink,#1e40af);background:var(--info-bg,#dbeafe);border-radius:8px;padding:6px 11px}
.kb-src-preview{border:1px solid var(--border,#e8e8e3);border-radius:12px;padding:16px 18px;font-size:13px;line-height:1.8;color:var(--ink-2,#555);background:var(--card,#fff);max-height:44vh;overflow:auto}
.kb-src-preview .seg.hit{background:#fff3c4;border-radius:3px;padding:1px 3px;color:var(--ink,#111);font-weight:600;box-shadow:0 0 0 1px #fde68a}
.kb-src-loading,.kb-src-fail{color:var(--ink-3,#999);font-size:12.5px;line-height:1.6}
.kb-src-foot{font-size:12px;color:var(--ink-3,#999);margin-top:14px;line-height:1.6}
`;
    document.head.appendChild(st);

    _shell = kbModalShell('src');
}

function segHtml(seg: KbChunkSegment): string {
    const body = kbEsc(seg.text).replace(/\n/g, '<br>');
    return `<span class="seg${seg.matched ? ' hit' : ''}">${body}</span>`;
}

function renderSegments(ctx: KbChunkContext): string {
    return ctx.segments.map(segHtml).join('<br><br>');
}

async function open(cit: KbCitation): Promise<void> {
    ensureDom();
    const modal = _shell?.modal;
    if (!modal) return;

    const name = cit.filename || kbT('kb-src-unknown', '未知来源');
    const pct =
        typeof cit.score === 'number'
            ? Math.round(Math.max(0, Math.min(1, cit.score)) * 100)
            : null;
    const hasChunk = typeof cit.chunk_id === 'number';

    modal.innerHTML = `
        <div class="kb-src-head">
            <span class="ic">${kbIcon('file')}</span>
            <div>
                <h3>${kbEsc(name)}</h3>
                <div class="sub">${kbEsc(kbT(hasChunk ? 'kb-src-hit' : 'kb-src-from', hasChunk ? '命中片段已高亮' : '此结论引用自以下文档'))}</div>
            </div>
            <button class="x" data-kb-src-close aria-label="close">${kbIcon('x')}</button>
        </div>
        <div class="kb-src-body">
            ${pct !== null ? `<div class="kb-src-rel">${kbEsc(kbT('kb-src-relevance', '相关度'))} ${pct}%</div>` : ''}
            <div class="kb-src-preview" id="kb-src-preview">${
                hasChunk
                    ? `<div class="kb-src-loading">${kbEsc(kbT('kb-src-loading', '正在取原文…'))}</div>`
                    : `<div class="kb-src-fail">${kbEsc(kbT('kb-src-no-chunk', '可在文档库打开原件核对。'))}</div>`
            }</div>
            <p class="kb-src-foot">${kbEsc(kbT('kb-src-verifiable', '这就是「可核对」:AI 说的每句话都能点回原文这一句,会计自己一眼能确认,不用盲信。'))}</p>
        </div>
    `;
    _shell?.open();

    if (!hasChunk) return;
    const r = await kbRequest<KbChunkContext>('GET', '/chunks/' + cit.chunk_id);
    const el = modal.querySelector('#kb-src-preview');
    if (!el) return;
    if (r.ok && r.data?.segments?.length) {
        el.innerHTML = renderSegments(r.data);
    } else {
        el.innerHTML = `<div class="kb-src-fail">${kbEsc(kbT('kb-src-load-fail', '原文片段暂时取不到,可在文档库打开原件核对。'))}</div>`;
    }
}

window._kbOpenSource = (cit: KbCitation): void => {
    void open(cit);
};
