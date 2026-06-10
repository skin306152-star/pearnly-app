// ============================================================
// 客户知识中心 · 页面骨架注入(KNOWLEDGE feature · 阶段1 地基)
//
// home.html <section id="page-knowledge"> 为空壳,本模块 eval 期注入骨架 innerHTML
// (R6 机制,镜像 page-clients)。三 tab:文档库 / 问答 / 规则。复用既有设计语言
// (.page-head / .recon-tab-bar / .btn),只补少量知识库专属 CSS。tab 切换与数据
// 装填由 knowledge-center.ts 负责,本文件只搭静态壳。import 置于 knowledge-center 前。
// ============================================================
(function () {
    'use strict';
    const sec = document.getElementById('page-knowledge');
    if (!sec || sec.dataset.wbInjected === '1') return;

    if (!document.getElementById('kb-center-style')) {
        const st = document.createElement('style');
        st.id = 'kb-center-style';
        st.textContent = `
.kb-ws-bar{display:flex;align-items:center;gap:9px;background:var(--card);border:1px solid var(--line,var(--line));border-radius:9px;padding:8px 13px;font-size:13px;margin-bottom:16px}
.kb-ws-bar .kb-ws-dot{width:8px;height:8px;border-radius:50%;background:var(--green);flex-shrink:0}
.kb-ws-bar.kb-ws-empty .kb-ws-dot{background:var(--amber)}
.kb-ws-bar b{font-weight:600}
.kb-pane{display:none}
.kb-pane.active{display:block}
.kb-soon{background:var(--card);border:1px dashed var(--line,var(--line));border-radius:12px;padding:46px 20px;text-align:center;color:var(--ink-3,#999)}
.kb-soon h3{color:var(--ink-2,#555);font-size:15px;margin:0 0 6px}
.kb-rules-intro{background:var(--card);border:1px solid var(--line,var(--line));border-radius:12px;padding:20px}
.kb-rules-intro p{color:var(--ink-2,#555);font-size:13px;margin:0 0 14px;line-height:1.6}
.kb-info-btn{margin-left:auto;align-self:center;display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:var(--accent);background:var(--accent-weak);border:none;border-radius:18px;padding:6px 13px;cursor:pointer}
.kb-info-btn:hover{background:var(--accent-weak)}
.kb-info-btn svg{width:14px;height:14px}
`;
        document.head.appendChild(st);
    }

    sec.innerHTML = `
        <div class="page-head">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 3a9 9 0 100 18 9 9 0 000-18z"/>
                    <path d="M9.5 9a2.5 2.5 0 115 0c0 1.5-2.5 2-2.5 3.5"/>
                    <line x1="12" y1="17" x2="12" y2="17.01"/>
                </svg>
            </div>
            <div class="page-head-text">
                <h1 class="page-title" data-i18n="kb-title">客户知识</h1>
                <div class="page-subtitle" data-i18n="kb-sub">合同 / 政策 / 规矩按账套主体隔离 · AI 检查发票与问答均带出处</div>
            </div>
            <button class="kb-info-btn" id="kb-info-btn" type="button">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>
                <span data-i18n="kb-info-btn">功能介绍 · 费用</span>
            </button>
        </div>

        <div class="kb-ws-bar" id="kb-ws-bar">
            <span class="kb-ws-dot"></span>
            <span id="kb-ws-label"></span>
        </div>

        <div class="recon-tab-bar kb-tab-bar">
            <button class="recon-tab-btn active" data-kb-tab="docs">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M9.5 1.5H4a1 1 0 00-1 1v11a1 1 0 001 1h8a1 1 0 001-1V5z"/><path d="M9.5 1.5V5H13"/></svg>
                <span data-i18n="kb-tab-docs">文档库</span>
            </button>
            <button class="recon-tab-btn" data-kb-tab="qa">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M14 10a1.5 1.5 0 01-1.5 1.5H5L2 14V3.5A1.5 1.5 0 013.5 2h9A1.5 1.5 0 0114 3.5z"/></svg>
                <span data-i18n="kb-tab-qa">问答</span>
            </button>
            <button class="recon-tab-btn" data-kb-tab="rules">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 4h12M5 8h6M7 12h2"/></svg>
                <span data-i18n="kb-tab-rules">规则</span>
            </button>
        </div>

        <div id="kb-pane-docs" class="kb-pane active">
            <div class="kb-soon">
                <h3 data-i18n="kb-docs-soon-title">文档库</h3>
                <div data-i18n="kb-docs-soon">上传客户合同、采购政策、税务登记等资料,AI 检查发票和问答时引用。</div>
            </div>
        </div>

        <div id="kb-pane-qa" class="kb-pane">
            <div class="kb-soon">
                <h3 data-i18n="kb-qa-soon-title">问答</h3>
                <div data-i18n="kb-qa-soon">问关于这家客户的事,答案都带合同原文出处;查不到时如实说「资料不足」。</div>
            </div>
        </div>

        <div id="kb-pane-rules" class="kb-pane">
            <div class="kb-rules-intro">
                <p data-i18n="kb-rules-intro">客户规矩(供应商白名单 / 金额上限 / 强制人工复核 / 会计期间)直接喂给发票异常检测引擎,增删改即时生效。</p>
                <button class="btn btn-primary" id="kb-open-rules">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><path d="M2 4h12M5 8h6M7 12h2"/></svg>
                    <span data-i18n="kb-manage-rules">管理客户规矩</span>
                </button>
            </div>
        </div>
`;
    sec.dataset.wbInjected = '1';

    try {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        const I = window.I18N;
        if (I && I[lang]) {
            sec.querySelectorAll('[data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n') as string;
                if (I[lang][k]) el.textContent = I[lang][k];
            });
        }
    } catch {
        /* 初译失败不致命 · 切语言会补 */
    }
})();
