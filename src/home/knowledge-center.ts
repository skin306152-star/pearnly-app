// ============================================================
// 客户知识中心 · 页面逻辑(KNOWLEDGE feature · 阶段1 地基)
//
// 职责:① flag 探针门控侧栏入口(关闭态零入口,付费用户看不到半成品)
//       ② tab 切换 ③ 顶部账套主体上下文渲染 ④ window.loadKnowledgePage。
// 文档库 / 问答 的数据装填在后续阶段各自模块接手,本文件只搭页面外壳行为。
// 骨架由 page-knowledge.ts 注入 → 本文件 import 须在其后。
// ============================================================
/* global escapeHtml */
import { kbProbe, kbWorkspaceId, kbWorkspaceName } from './knowledge-api.js';

let _tabsBound = false;

function kbT(key: string, fallback: string): string {
    if (typeof window.t === 'function') {
        const s = window.t(key);
        if (s && s !== key) return s;
    }
    return fallback;
}

function renderWorkspaceBar(): void {
    const bar = document.getElementById('kb-ws-bar');
    const label = document.getElementById('kb-ws-label');
    if (!bar || !label) return;
    const id = kbWorkspaceId();
    if (id) {
        bar.classList.remove('kb-ws-empty');
        label.innerHTML =
            kbT('kb-ws-current', '账套主体') + '：<b>' + escapeName(kbWorkspaceName()) + '</b>';
    } else {
        bar.classList.add('kb-ws-empty');
        label.textContent = kbT(
            'kb-ws-none',
            '请先在右上角选择账套主体,再使用客户私有文档与问答。'
        );
    }
}

function escapeName(s: string): string {
    return typeof escapeHtml === 'function' ? escapeHtml(s) : s;
}

function switchTab(tab: string): void {
    document.querySelectorAll<HTMLElement>('.kb-tab-bar .recon-tab-btn').forEach((b) => {
        b.classList.toggle('active', b.dataset.kbTab === tab);
    });
    document.querySelectorAll<HTMLElement>('.kb-pane').forEach((p) => {
        p.classList.toggle('active', p.id === 'kb-pane-' + tab);
    });
    if (tab === 'docs' && typeof window._kbRenderDocs === 'function') window._kbRenderDocs();
    if (tab === 'qa' && typeof window._kbRenderAsk === 'function') window._kbRenderAsk();
}

function bindTabs(): void {
    if (_tabsBound) return;
    const bar = document.querySelector('.kb-tab-bar');
    if (!bar) return;
    bar.addEventListener('click', (e) => {
        const btn = (e.target as HTMLElement).closest<HTMLElement>('.recon-tab-btn');
        if (btn && btn.dataset.kbTab) switchTab(btn.dataset.kbTab);
    });
    const rulesBtn = document.getElementById('kb-open-rules');
    if (rulesBtn) {
        rulesBtn.addEventListener('click', () => {
            if (typeof window.openRulesSettings === 'function') window.openRulesSettings();
        });
    }
    _tabsBound = true;
}

window.loadKnowledgePage = function loadKnowledgePage(): void {
    bindTabs();
    renderWorkspaceBar();
    // 文档库是默认 tab · 进页即拉取(切到其它 tab 再回来由 switchTab 兜底刷新)
    const docsActive = document
        .querySelector('.kb-tab-bar .recon-tab-btn[data-kb-tab="docs"]')
        ?.classList.contains('active');
    if (docsActive && typeof window._kbRenderDocs === 'function') window._kbRenderDocs();
};

// 探针门控:仅当后端知识库开启(flag)才显示侧栏入口。关闭态用户全程零入口。
async function revealNavIfEnabled(): Promise<void> {
    if (window._knowledgeProbed) return;
    window._knowledgeProbed = true;
    try {
        if (await kbProbe()) {
            const nav = document.getElementById('nav-knowledge');
            if (nav) nav.style.display = '';
        }
    } catch {
        /* 关闭态 · 不显示入口 */
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', revealNavIfEnabled);
} else {
    revealNavIfEnabled();
}

// 切语言:重渲账套上下文(data-i18n 静态文案由全局 applyLang 扫描覆盖)
if (!Array.isArray(window.__i18nSubs)) window.__i18nSubs = [];
window.__i18nSubs.push({ name: 'knowledge-center', fn: renderWorkspaceBar });
