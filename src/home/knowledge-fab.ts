// ============================================================
// 客户知识 · 悬浮猫问答助手(KNOWLEDGE feature · 阶段4)
//
// 全局右下角一只猫(纯角色无背景框)· 长按可拖到任意位置 · 松手自动吸最近的边。
// 点开 = 磨砂玻璃问答卡,复用 _kbWireAsk(与问答 tab 同一套答案/出处逻辑)。
// 显隐由问答 tab 的开关控制(localStorage 持久),仅知识库 flag 开 + 用户开启才出现。
// ============================================================
import { KB_CAT, kbProbe, kbT, kbWorkspaceName } from './knowledge-api.js';

const LS_KEY = 'pearnly_kb_fab';
const CAT = KB_CAT;
const M = 14; // 离边距离
let built = false;
let wired = false;

function ensureStyle(): void {
    if (document.getElementById('kb-fab-style')) return;
    const st = document.createElement('style');
    st.id = 'kb-fab-style';
    st.textContent = `
.kb-fab{position:fixed;left:0;top:62%;z-index:1100;touch-action:none;display:none}
.kb-fab.on{display:block}
.kb-fab.snapping{transition:left .26s cubic-bezier(.3,.85,.3,1),top .26s cubic-bezier(.3,.85,.3,1)}
.kb-fab-btn{position:relative;width:56px;height:56px;background:none;border:none;padding:0;display:grid;place-items:center;cursor:grab;animation:kbBob 3.4s ease-in-out infinite}
.kb-fab-btn.jump{animation:kbJump .7s cubic-bezier(.3,1.5,.5,1)}
.kb-fab-btn.cheer{animation:kbCheer .6s ease}
.kb-fab.lifted .kb-fab-btn{cursor:grabbing;animation:none}
.kb-fab-btn img{width:56px;height:56px;object-fit:contain;pointer-events:none;filter:drop-shadow(0 6px 6px rgba(17,17,17,.22));transition:filter .15s,transform .15s;transform-origin:50% 90%}
.kb-fab-btn:hover img{transform:translateY(-2px) scale(1.05)}
.kb-fab.lifted .kb-fab-btn img{filter:drop-shadow(0 18px 14px rgba(17,17,17,.3));transform:scale(1.08) rotate(-3deg)}
@keyframes kbBob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
@keyframes kbJump{0%{transform:translateY(0)}30%{transform:translateY(-16px) rotate(-4deg)}55%{transform:translateY(0) scaleY(.92) scaleX(1.06)}75%{transform:translateY(-5px)}100%{transform:translateY(0)}}
@keyframes kbCheer{0%{transform:translateY(0)}25%{transform:translateY(-10px) rotate(6deg)}50%{transform:translateY(0) scaleY(.9) scaleX(1.08)}70%{transform:translateY(-6px) rotate(-5deg)}100%{transform:translateY(0)}}
.kb-say{position:absolute;bottom:60px;left:50%;transform:translateX(-50%) scale(.6);transform-origin:bottom center;background:#111;color:#fff;font-size:11px;font-weight:700;padding:5px 11px;border-radius:13px;white-space:nowrap;opacity:0;pointer-events:none;transition:.18s;box-shadow:0 4px 12px rgba(17,17,17,.2)}
.kb-say::after{content:"";position:absolute;bottom:-5px;left:50%;transform:translateX(-50%);border:5px solid transparent;border-top-color:#111;border-bottom:0}
.kb-say.show{opacity:1;transform:translateX(-50%) scale(1)}
.kb-spark{position:absolute;left:50%;top:8px;font-size:15px;pointer-events:none;animation:kbFloat 1s ease-out forwards}
@keyframes kbFloat{0%{opacity:0;transform:translate(-50%,0) scale(.4)}25%{opacity:1}100%{opacity:0;transform:translate(var(--dx,0),-46px) scale(1.1)}}
.kb-card{position:fixed;width:380px;height:520px;z-index:1101;display:none;flex-direction:column;background:rgba(255,255,255,.86);backdrop-filter:blur(22px) saturate(1.5);-webkit-backdrop-filter:blur(22px) saturate(1.5);border:1px solid rgba(255,255,255,.78);border-radius:18px;box-shadow:0 24px 60px rgba(17,17,17,.24);overflow:hidden}
.kb-card.open{display:flex;animation:kbPop .22s cubic-bezier(.2,.9,.3,1.2)}
@keyframes kbPop{from{opacity:0;transform:translateY(20px) scale(.96)}to{opacity:1;transform:none}}
.kb-card-top{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid rgba(17,17,17,.07)}
.kb-card-top .tt{font-weight:700;display:flex;align-items:center;gap:8px;font-size:13px}
.kb-card-top .tt .mini{width:26px;height:26px;border-radius:8px;background:#fff7ee;overflow:hidden;display:grid;place-items:center}
.kb-card-top .tt .mini img{width:26px;height:26px;object-fit:cover;object-position:center 16%}
.kb-card-top .ws{font-size:11px;color:var(--ink-2,#555);background:rgba(255,255,255,.6);border:1px solid var(--border,#e8e8e3);border-radius:7px;padding:3px 8px;font-weight:600;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kb-card-x{width:26px;height:26px;border-radius:7px;display:grid;place-items:center;color:var(--ink-3,#999);border:none;background:none;cursor:pointer}
.kb-card-x:hover{background:rgba(17,17,17,.06);color:var(--ink,#111)}
.kb-card .kb-qa-thread{background:transparent}
.kb-card .kb-qa-input{border-top:1px solid rgba(17,17,17,.07)}
@media(max-width:820px){.kb-card{right:0!important;left:0!important;bottom:0!important;top:auto!important;width:100%;height:78vh;border-radius:18px 18px 0 0}}
`;
    document.head.appendChild(st);
}

let dock: HTMLElement;
let catBtn: HTMLButtonElement;
let sayEl: HTMLElement;
let card: HTMLElement;

function build(): void {
    if (built) return;
    ensureStyle();

    dock = document.createElement('div');
    dock.className = 'kb-fab';
    dock.id = 'kb-fab';
    dock.innerHTML = `
        <span class="kb-say" id="kb-say">${kbT('kb-fab-hi', '喵~')}</span>
        <button class="kb-fab-btn" id="kb-fab-btn" aria-label="${kbT('kb-fab-aria', '问 AI')}"><img src="${CAT}" alt=""></button>`;
    document.body.appendChild(dock);

    card = document.createElement('div');
    card.className = 'kb-card';
    card.id = 'kb-card';
    card.innerHTML = `
        <div class="kb-card-top">
            <div class="tt"><span class="mini"><img src="${CAT}" alt=""></span> ${kbT('kb-fab-title', '客户知识助手')}</div>
            <div style="display:flex;align-items:center;gap:8px">
                <span class="ws" id="kb-card-ws"></span>
                <button class="kb-card-x" id="kb-card-x" aria-label="close">✕</button>
            </div>
        </div>
        <div class="kb-qa-thread" id="kb-card-thread" style="flex:1;padding:15px;display:flex;flex-direction:column;gap:14px;overflow:auto"></div>
        <div class="kb-qa-input">
            <input id="kb-card-input" placeholder="${kbT('kb-fab-ph', '随处可问，不跳页…')}">
            <button class="kb-send" id="kb-card-send"><svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button>
        </div>`;
    document.body.appendChild(card);

    catBtn = dock.querySelector('#kb-fab-btn') as HTMLButtonElement;
    sayEl = dock.querySelector('#kb-say') as HTMLElement;
    document.getElementById('kb-card-x')?.addEventListener('click', closeCard);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeCard();
    });

    setupDrag();
    setupPersonality();
    park();
    built = true;
}

// ---------- 展开卡 ----------
function openCard(): void {
    const thread = document.getElementById('kb-card-thread') as HTMLElement;
    const input = document.getElementById('kb-card-input') as HTMLInputElement;
    const send = document.getElementById('kb-card-send') as HTMLElement;
    if (!wired && typeof window._kbWireAsk === 'function') {
        thread.innerHTML = `<div class="kb-msg ai"><div class="kb-ava"><img src="${CAT}" alt=""></div><div class="kb-bub">${kbT('kb-ask-empty', '问点关于这家客户的事，答案都带出处；查不到时如实说「资料不足」。')}</div></div>`;
        window._kbWireAsk(thread, input, send);
        wired = true;
    }
    const ws = document.getElementById('kb-card-ws');
    if (ws) ws.textContent = kbWorkspaceName() || kbT('kb-fab-no-ws', '未选账套');
    positionCard();
    card.classList.add('open');
    catCheer();
    burst(['💛', '✨', '💙', '🐾']);
}
function closeCard(): void {
    card?.classList.remove('open');
}
function positionCard(): void {
    const r = dock.getBoundingClientRect();
    const ch = 520;
    const onLeft = r.left + r.width / 2 < window.innerWidth / 2;
    const top = Math.min(Math.max(M, r.top + r.height / 2 - ch / 2), window.innerHeight - ch - M);
    card.style.top = top + 'px';
    if (onLeft) {
        card.style.left = r.right + 12 + 'px';
        card.style.right = 'auto';
    } else {
        card.style.right = window.innerWidth - r.left + 12 + 'px';
        card.style.left = 'auto';
    }
}

// ---------- 卖萌 ----------
let sayTimer: ReturnType<typeof setTimeout>;
function say(txt: string, ms = 1500): void {
    sayEl.textContent = txt;
    sayEl.classList.add('show');
    clearTimeout(sayTimer);
    sayTimer = setTimeout(() => sayEl.classList.remove('show'), ms);
}
function catCheer(): void {
    catBtn.classList.remove('jump');
    catBtn.classList.add('cheer');
    setTimeout(() => catBtn.classList.remove('cheer'), 650);
}
function catJump(): void {
    if (dock.classList.contains('lifted')) return;
    catBtn.classList.remove('cheer');
    catBtn.classList.add('jump');
    setTimeout(() => catBtn.classList.remove('jump'), 720);
}
function burst(set: string[]): void {
    for (let i = 0; i < 5; i++) {
        const s = document.createElement('span');
        s.className = 'kb-spark';
        s.textContent = set[i % set.length];
        s.style.setProperty('--dx', i * 14 - 28 + 'px');
        s.style.left = 30 + i * 10 + '%';
        s.style.animationDelay = i * 40 + 'ms';
        dock.appendChild(s);
        setTimeout(() => s.remove(), 1100);
    }
}
function setupPersonality(): void {
    const HELLO = [kbT('kb-fab-hi', '喵?'), kbT('kb-fab-ask', '问我呀!'), '🐾'];
    catBtn.addEventListener('mouseenter', () => {
        if (!dock.classList.contains('lifted'))
            say(HELLO[((Date.now() / 1000) | 0) % HELLO.length], 1400);
    });
    setInterval(() => {
        if (
            !dock.classList.contains('on') ||
            dock.classList.contains('lifted') ||
            card.classList.contains('open')
        )
            return;
        if (((Date.now() / 1000) | 0) % 2 === 0) {
            catJump();
            burst(['✨', '🐾']);
        }
    }, 5400);
}

// ---------- 拖拽 + 吸边 ----------
function clampTop(t: number): number {
    return Math.min(Math.max(M, t), window.innerHeight - dock.offsetHeight - M);
}
function park(): void {
    dock.classList.add('snapping');
    dock.style.left = window.innerWidth - 56 - M + 'px';
    dock.style.top = '62%';
}
function setupDrag(): void {
    let holdTimer: ReturnType<typeof setTimeout>;
    let dragging = false,
        moved = false,
        startX = 0,
        startY = 0,
        baseLeft = 0,
        baseTop = 0;
    function down(e: PointerEvent): void {
        startX = e.clientX;
        startY = e.clientY;
        moved = false;
        dragging = false;
        const r = dock.getBoundingClientRect();
        baseLeft = r.left;
        baseTop = r.top;
        dock.classList.remove('snapping');
        holdTimer = setTimeout(() => {
            dock.classList.add('lifted');
        }, 180);
        window.addEventListener('pointermove', move);
        window.addEventListener('pointerup', up);
        e.preventDefault();
    }
    function move(e: PointerEvent): void {
        const dx = e.clientX - startX,
            dy = e.clientY - startY;
        if (!dragging && Math.hypot(dx, dy) > 6) {
            dragging = true;
            dock.classList.add('lifted');
            clearTimeout(holdTimer);
        }
        if (dragging) {
            moved = true;
            dock.style.left = baseLeft + dx + 'px';
            dock.style.top = clampTop(baseTop + dy) + 'px';
        }
    }
    function up(): void {
        clearTimeout(holdTimer);
        window.removeEventListener('pointermove', move);
        window.removeEventListener('pointerup', up);
        dock.classList.remove('lifted');
        if (!moved) {
            openCard();
            return;
        }
        snapToEdge();
    }
    function snapToEdge(): void {
        const r = dock.getBoundingClientRect();
        dock.classList.add('snapping');
        dock.style.top = clampTop(r.top) + 'px';
        dock.style.left =
            (r.left + r.width / 2 < window.innerWidth / 2
                ? M
                : window.innerWidth - dock.offsetWidth - M) + 'px';
    }
    catBtn.addEventListener('pointerdown', down);
    window.addEventListener('resize', () => {
        if (!built) return;
        const r = dock.getBoundingClientRect();
        dock.style.top = clampTop(r.top) + 'px';
        dock.style.left =
            (r.left + r.width / 2 < window.innerWidth / 2
                ? M
                : window.innerWidth - dock.offsetWidth - M) + 'px';
    });
}

// ---------- 开关 / 门控 ----------
function setEnabled(on: boolean): void {
    build();
    localStorage.setItem(LS_KEY, on ? '1' : '0');
    dock.classList.toggle('on', on);
    if (!on) closeCard();
}
window._kbFabSetEnabled = setEnabled;
window._kbFabEnabled = () => localStorage.getItem(LS_KEY) === '1';

// 启动:用户曾开启 + 知识库 flag 开 → 自动悬浮
async function init(): Promise<void> {
    if (localStorage.getItem(LS_KEY) !== '1') return;
    try {
        if (await kbProbe()) setEnabled(true);
    } catch {
        /* flag 关 · 不显示 */
    }
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else void init();
