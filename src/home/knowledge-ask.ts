// ============================================================
// 客户知识 · 问答(KNOWLEDGE feature · 阶段3)
//
// 接 /api/knowledge/ask:提问 → AI 答 + citation 出处卡;无来源固定回「资料不足」。
// 答案逻辑做成可复用(_kbWireAsk),问答 tab 与悬浮件(阶段4)两个挂载点共用。
// citation 点开经 knowledge-sources(.modal)。每条答出后端扣 1 credit(no_answer 不扣)。
// ============================================================
/* global showToast */
import { KB_CAT, kbEsc, kbRequest, kbT } from './knowledge-api.js';
import type { KbCitation } from './knowledge-sources.js';

interface AskResult {
    answer: string;
    no_answer: boolean;
    citations: KbCitation[];
    message_key?: string;
}

function userBubble(text: string): string {
    return `<div class="kb-msg user"><div class="kb-bub">${kbEsc(text)}</div></div>`;
}

function citeChip(c: KbCitation): string {
    const name = c.filename || kbT('kb-src-unknown', '未知来源');
    const data = kbEsc(JSON.stringify(c));
    return `<button class="kb-cite" data-cite='${data}'>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>
        ${kbEsc(name)}<span class="ch">›</span></button>`;
}

function aiBubble(data: AskResult): string {
    if (data.no_answer) {
        const msg = kbT(data.message_key || 'ask.no_source', '资料不足，无法判断。');
        return `<div class="kb-msg ai"><div class="kb-ava"><img src="${KB_CAT}" alt=""></div>
            <div class="kb-bub no-src">${kbEsc(msg)}</div></div>`;
    }
    const cites = (data.citations || []).map((c) => citeChip(c)).join('');
    return `<div class="kb-msg ai"><div class="kb-ava"><img src="${KB_CAT}" alt=""></div>
        <div class="kb-bub">${kbEsc(data.answer)}${cites ? `<div class="kb-cites">${cites}</div>` : ''}</div></div>`;
}

async function runAsk(question: string): Promise<AskResult | null> {
    const r = await kbRequest<AskResult>('POST', '/ask', { question });
    if (!r.ok || !r.data) return null;
    return r.data;
}

// 一套问答接线:给定 thread/input/send 三件 → 自带会话状态 · 供 tab 与悬浮件复用
function wireAsk(threadEl: HTMLElement, inputEl: HTMLInputElement, sendBtn: HTMLElement): void {
    if (threadEl.dataset.kbWired === '1') return;
    threadEl.dataset.kbWired = '1';
    let busy = false;

    function append(html: string): HTMLElement {
        const div = document.createElement('div');
        div.innerHTML = html;
        const node = div.firstElementChild as HTMLElement;
        threadEl.appendChild(node);
        threadEl.scrollTop = threadEl.scrollHeight;
        return node;
    }

    async function send(): Promise<void> {
        const q = inputEl.value.trim();
        if (!q || busy) return;
        busy = true;
        inputEl.value = '';
        append(userBubble(q));
        const thinking = append(
            `<div class="kb-msg ai"><div class="kb-ava"><img src="${KB_CAT}" alt=""></div><div class="kb-bub kb-thinking">${kbEsc(kbT('kb-ask-thinking', '思考中…'))}</div></div>`
        );
        const data = await runAsk(q);
        thinking.remove();
        if (!data) {
            append(
                `<div class="kb-msg ai"><div class="kb-ava"><img src="${KB_CAT}" alt=""></div><div class="kb-bub no-src">${kbEsc(kbT('kb-ask-error', '出错了，请稍后重试。'))}</div></div>`
            );
            if (typeof showToast === 'function')
                showToast(kbT('kb-ask-error', '出错了，请稍后重试。'), 'error');
        } else {
            append(aiBubble(data));
        }
        busy = false;
    }

    sendBtn.addEventListener('click', send);
    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    });
    threadEl.addEventListener('click', (e) => {
        const chip = (e.target as HTMLElement).closest<HTMLElement>('.kb-cite');
        if (!chip || !chip.dataset.cite) return;
        try {
            const cit = JSON.parse(chip.dataset.cite) as KbCitation;
            if (typeof window._kbOpenSource === 'function') window._kbOpenSource(cit);
        } catch {
            /* 损坏的 citation 数据 · 忽略 */
        }
    });
}

window._kbWireAsk = wireAsk;

function ensureStyle(): void {
    if (document.getElementById('kb-ask-style')) return;
    const st = document.createElement('style');
    st.id = 'kb-ask-style';
    st.textContent = `
.kb-qa{background:var(--card,#fff);border:1px solid var(--border,#e8e8e3);border-radius:12px;display:flex;flex-direction:column;height:460px;max-width:760px}
.kb-qa-thread{flex:1;padding:18px;display:flex;flex-direction:column;gap:16px;overflow:auto}
.kb-msg{max-width:80%;display:flex;gap:9px}
.kb-msg.user{align-self:flex-end}
.kb-msg.user .kb-bub{background:var(--btn-blue,#2563eb);color:#fff;border-radius:14px 14px 4px 14px;padding:9px 13px}
.kb-msg.ai{align-self:flex-start}
.kb-ava{width:28px;height:28px;border-radius:8px;background:#fff7ee;flex-shrink:0;display:grid;place-items:center;overflow:hidden}
.kb-ava img{width:28px;height:28px;object-fit:cover;object-position:center 16%}
.kb-msg.ai .kb-bub{background:var(--bg,#f4f4f0);border-radius:14px 14px 14px 4px;padding:10px 14px;line-height:1.6}
.kb-bub.no-src{border-left:3px solid var(--warn,#d97706);color:var(--ink-2,#555)}
.kb-bub.kb-thinking{color:var(--ink-3,#999)}
.kb-cites{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}
.kb-cite{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid var(--border,#e8e8e3);border-radius:9px;padding:6px 10px;font-size:12px;font-weight:600;color:var(--info-ink,#1e40af);cursor:pointer}
.kb-cite:hover{border-color:var(--btn-blue,#2563eb);box-shadow:0 2px 8px rgba(37,99,235,.12)}
.kb-cite svg{width:13px;height:13px}
.kb-cite .ch{color:var(--ink-3,#999)}
.kb-qa-foot{border-top:1px solid var(--border,#e8e8e3);padding:0}
.kb-qa-ex{display:flex;flex-wrap:wrap;gap:7px;padding:11px 14px 0}
.kb-chip{background:#fff;border:1px solid var(--border,#e8e8e3);border-radius:18px;padding:5px 11px;font-size:12px;color:var(--ink-2,#555);cursor:pointer}
.kb-chip:hover{border-color:var(--btn-blue,#2563eb);color:var(--btn-blue,#2563eb)}
.kb-qa-input{display:flex;gap:9px;align-items:center;padding:12px 14px}
.kb-qa-input input{flex:1;border:1px solid var(--border,#e8e8e3);border-radius:9px;padding:9px 13px;font-size:13px;font-family:inherit;background:var(--bg,#f4f4f0)}
.kb-qa-input input:focus{outline:none;border-color:var(--btn-blue,#2563eb);background:#fff}
.kb-send{width:38px;height:38px;border-radius:9px;background:var(--btn-blue,#2563eb);color:#fff;display:grid;place-items:center;flex-shrink:0;border:none;cursor:pointer}
.kb-send:hover{background:var(--btn-blue-hover,#1d4ed8)}
.kb-send svg{width:17px;height:17px;stroke:#fff;fill:none;stroke-width:2}
.kb-qa-hint{font-size:12px;color:var(--ink-3,#999);margin-top:12px;max-width:760px;line-height:1.6}
.kb-ft{display:flex;align-items:center;gap:13px;background:var(--card,#fff);border:1px solid var(--border,#e8e8e3);border-radius:12px;padding:13px 16px;margin-bottom:16px;max-width:760px}
.kb-ft .ft-cat{width:38px;height:38px;border-radius:10px;background:#fff7ee;display:grid;place-items:center;overflow:hidden;flex-shrink:0}
.kb-ft .ft-cat img{width:34px;height:34px;object-fit:cover;object-position:center 16%}
.kb-ft .ft-txt{flex:1}
.kb-ft .ft-txt b{font-weight:700}
.kb-ft .ft-txt .sub{font-size:11px;color:var(--ink-3,#999);margin-top:1px}
.kb-switch{width:38px;height:22px;border-radius:20px;background:#d6d6d0;position:relative;transition:.18s;flex-shrink:0;cursor:pointer;border:none}
.kb-switch.on{background:var(--btn-blue,#2563eb)}
.kb-switch::after{content:"";position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.18s;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.kb-switch.on::after{left:18px}
`;
    document.head.appendChild(st);
}

function renderAsk(): void {
    const pane = document.getElementById('kb-pane-qa');
    if (!pane) return;
    if (pane.dataset.kbBuilt === '1') return;
    ensureStyle();

    const ex1 = kbEsc(kbT('kb-ask-ex1', '这家客户有金额上限吗？'));
    const ex2 = kbEsc(kbT('kb-ask-ex2', '合同约定的付款周期是多久？'));
    const ex3 = kbEsc(kbT('kb-ask-ex3', '哪些供应商需要人工复核？'));
    const fabOn = typeof window._kbFabEnabled === 'function' && window._kbFabEnabled();
    pane.innerHTML = `
        <div class="kb-ft">
            <span class="ft-cat"><img src="${KB_CAT}" alt=""></span>
            <div class="ft-txt">
                <b>${kbEsc(kbT('kb-fab-toggle', '桌面悬浮问答助手'))}</b>
                <div class="sub">${kbEsc(kbT('kb-fab-toggle-sub', '打开后任意页面右下角常驻一只猫，随手就能问，可长按拖到屏幕任意一边。'))}</div>
            </div>
            <button class="kb-switch${fabOn ? ' on' : ''}" id="kb-fab-switch" role="switch" aria-checked="${fabOn}"></button>
        </div>
        <div class="kb-qa">
            <div class="kb-qa-thread" id="kb-qa-thread">
                <div class="kb-msg ai"><div class="kb-ava"><img src="${KB_CAT}" alt=""></div>
                <div class="kb-bub">${kbEsc(kbT('kb-ask-empty', '问点关于这家客户的事，答案都带合同原文出处；查不到时如实说「资料不足」。'))}</div></div>
            </div>
            <div class="kb-qa-foot">
                <div class="kb-qa-ex">
                    <button class="kb-chip" data-q="${ex1}">${ex1}</button>
                    <button class="kb-chip" data-q="${ex2}">${ex2}</button>
                    <button class="kb-chip" data-q="${ex3}">${ex3}</button>
                </div>
                <div class="kb-qa-input">
                    <input id="kb-qa-input" data-i18n-placeholder="kb-ask-placeholder" placeholder="${kbEsc(kbT('kb-ask-placeholder', '问点关于这家客户的事…'))}">
                    <button class="kb-send" id="kb-qa-send"><svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button>
                </div>
            </div>
        </div>
        <p class="kb-qa-hint">🔒 ${kbEsc(kbT('kb-ask-disclaimer', 'AI 的每个结论都带可点开的出处；查不到依据时固定回答「资料不足」，绝不编。'))}</p>
    `;
    pane.dataset.kbBuilt = '1';

    const thread = pane.querySelector('#kb-qa-thread') as HTMLElement;
    const input = pane.querySelector('#kb-qa-input') as HTMLInputElement;
    const send = pane.querySelector('#kb-qa-send') as HTMLElement;
    wireAsk(thread, input, send);
    pane.querySelectorAll<HTMLElement>('.kb-chip').forEach((chip) => {
        chip.addEventListener('click', () => {
            input.value = chip.dataset.q || '';
            send.click();
        });
    });
    const fabSwitch = pane.querySelector('#kb-fab-switch') as HTMLElement;
    fabSwitch?.addEventListener('click', () => {
        const next = !fabSwitch.classList.contains('on');
        fabSwitch.classList.toggle('on', next);
        fabSwitch.setAttribute('aria-checked', String(next));
        if (typeof window._kbFabSetEnabled === 'function') window._kbFabSetEnabled(next);
    });
}

window._kbRenderAsk = renderAsk;
