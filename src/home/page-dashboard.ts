// ============================================================
// page-dashboard 骨架 · 运行期注入(home.html 空壳 <section id="page-dashboard">)
//
// PO-UI 迁移(2026-06-09)· 套概览模板 + kit · 照搬 scripts/_mock/dashboard-final.html:
//   信息带 .band(北极星=账户余额 + kpi 条)→ .cols(快捷 .qa | 最近动态 .act)。
// 作用域 .ui(挂到 section)吃 kit 组件 + 模板原语。dashboard.ts 读写的 id 全保留:
//   dash-kpi-{invoices,pending,exceptions,balance,usage} / dash-kpi-balance-card /
//   dash-kpi-usage-card / dash-recent-list / dash-quick-exc-badge。
// 注入后对子树补译(镜像 applyLang)· 切语言由 applyLang 全文扫描覆盖。
// ============================================================
(function () {
    'use strict';
    const sec = document.getElementById('page-dashboard');
    if (!sec || sec.dataset.wbInjected === '1') return;
    sec.classList.add('ui');
    sec.innerHTML = `
        <div class="wrap">
            <div class="pagehead">
                <div>
                    <div class="h1" data-i18n="dash-title">首页</div>
                    <div class="sub" id="dash-subtitle" data-i18n="dash-sub">今日工作概况</div>
                </div>
            </div>

            <div class="panel band" style="margin-top:var(--s4)">
                <div class="bandtop">
                    <div id="dash-kpi-balance-card" style="display:none">
                        <div class="l" data-i18n="dash-kpi-balance">账户余额</div>
                        <div class="n" id="dash-kpi-balance">—</div>
                        <div class="help" id="dash-kpi-balance-sub" style="margin-top:4px">&nbsp;</div>
                    </div>
                    <button class="btn pri" id="dash-topup-btn" style="display:none" onclick="window._openTopupModal&&window._openTopupModal()">
                        <svg class="ic" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        <span data-i18n="dash-topup">充值</span>
                    </button>
                </div>
                <div class="kpis">
                    <div class="kpi"><div class="l" data-i18n="dash-kpi-month-invoices">本月发票</div><div class="n" id="dash-kpi-invoices">0</div></div>
                    <div class="kpi"><div class="l" data-i18n="dash-kpi-pending">待处理</div><div class="n dash-amber" id="dash-kpi-pending">0</div></div>
                    <div class="kpi"><div class="l" data-i18n="dash-kpi-exceptions">异常</div><div class="n dash-red" id="dash-kpi-exceptions">0</div></div>
                    <div class="kpi" id="dash-kpi-usage-card"><div class="l" data-i18n="dash-kpi-usage">本月用量</div><div class="n" id="dash-kpi-usage">0</div><div class="help" id="dash-kpi-usage-sub">&nbsp;</div></div>
                </div>
            </div>

            <div class="cols" style="grid-template-columns:360px 1fr;margin-top:var(--s4)">
                <div class="panel box">
                    <div class="ch" data-i18n="dash-quick-title">快速操作</div>
                    <div class="cs" data-i18n="dash-quick-sub">3 步进入主流程</div>
                    <div class="qa">
                        <div class="qb" onclick="window.routeTo && window.routeTo('dms-intake')">
                            <span class="qi"><svg class="ic" viewBox="0 0 24 24"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M3 19h18"/></svg></span>
                            <span data-i18n="dash-quick-upload">上传发票</span>
                        </div>
                        <div class="qb" onclick="window.routeTo && window.routeTo('clients')">
                            <span class="qi"><svg class="ic" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/></svg></span>
                            <span data-i18n="dash-quick-clients">查看客户</span>
                        </div>
                        <div class="qb" onclick="window.routeTo && window.routeTo('reconcile')">
                            <span class="qi"><svg class="ic" viewBox="0 0 24 24"><line x1="12" y1="3" x2="12" y2="21"/><path d="M5 7h14"/><path d="M2 12l3-5 3 5a3 3 0 0 1-6 0z"/><path d="M16 12l3-5 3 5a3 3 0 0 1-6 0z"/></svg></span>
                            <span data-i18n="dash-quick-reconcile">开始对账</span>
                        </div>
                        <div class="qb qb-warn" onclick="window.routeTo && window.routeTo('exceptions')">
                            <span class="qi"><svg class="ic" viewBox="0 0 24 24"><path d="M10.3 3.8 1.8 18a2 2 0 0 0 1.7 3h16.9a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0Z"/><line x1="12" y1="9" x2="12" y2="13"/></svg></span>
                            <span data-i18n="dash-quick-exceptions">处理异常</span>
                            <span class="qb-badge" id="dash-quick-exc-badge" style="display:none">0</span>
                        </div>
                    </div>
                </div>
                <div class="panel box">
                    <div class="ch" data-i18n="dash-recent-title">最近动态</div>
                    <div class="cs" data-i18n="dash-recent-sub">最近 5 条识别</div>
                    <div id="dash-recent-list">
                        <div class="empty"><div class="t" data-i18n="dash-recent-empty">还没有识别记录 · 去上传第一张吧</div></div>
                    </div>
                </div>
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
    } catch (e) {
        /* silent · 初译失败不致命 · 切语言会补 */
    }
})();
