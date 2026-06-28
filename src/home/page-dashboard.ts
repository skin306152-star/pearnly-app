// ============================================================
// page-dashboard 骨架 · 运行期注入(home.html 空壳 <section id="page-dashboard">)
//
// 2026-06-28 改版:首页 = 订阅与计费。顶部两张并排卡片:
//   当前套餐 #sub-summary(subscription.ts 渲染)| 账户余额 #dash-kpi-balance-card
//   (dashboard.ts loadCreditsCard 渲染 · 充值入口=卡内 #dash-kpi-balance-sub 的「充值 →」链接)。
//   其下:套餐卡 #sub-plans → 计费规则 + 最近账单 #sub-records。
// 余额卡 id(dash-kpi-balance-card / dash-kpi-balance / dash-kpi-balance-sub)被
// dashboard.ts 依赖;充值弹窗经 window._openTopupModal(billing.ts)。静态文案走 data-i18n。
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
                    <div class="h1" data-i18n="sub-title">订阅与计费</div>
                    <div class="sub" data-i18n="sub-subtitle">管理套餐 · 用量 · 余额</div>
                </div>
            </div>

            <div class="sub-top" style="margin-top:var(--s4)">
                <div class="panel sub-card" id="sub-summary"></div>
                <div class="panel sub-card" id="dash-kpi-balance-card" style="display:none">
                    <div class="sub-card-ico">
                        <svg class="ic" viewBox="0 0 24 24"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>
                    </div>
                    <div class="sub-card-bd">
                        <div class="sub-card-l" data-i18n="dash-kpi-balance">账户余额</div>
                        <div class="n sub-card-n" id="dash-kpi-balance">—</div>
                        <div class="sub-card-hint" id="dash-kpi-balance-sub" data-i18n="dash-balance-use">用于超额扣费 · 按量计费</div>
                        <div class="sub-card-foot" id="dash-kpi-balance-foot" style="display:none">
                            <span class="sub-foot-hint" data-i18n="dash-balance-low-hint">余额不足时将影响超额扣费</span>
                            <button class="btn pri sub-topup-btn" id="dash-topup-btn" data-i18n="dash-topup">去充值</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="panel box" style="margin-top:var(--s4)">
                <div class="ch" data-i18n="sub-plans-title">选择套餐</div>
                <div class="cs" data-i18n="sub-plans-sub">无套餐按量计费 · 订阅后先用套餐额度,超额自动扣余额</div>
                <div class="sub-plans" id="sub-plans"></div>
            </div>

            <div class="panel box rec-box" id="rec-box" style="margin-top:var(--s4)">
                <div class="rec-head">
                    <div>
                        <div class="ch" data-i18n="rec-title">记录明细</div>
                        <div class="cs" data-i18n="rec-sub">扣费 · 充值 · 识别 · 切换查看,导出全部明细</div>
                    </div>
                    <button class="btn rec-export" id="rec-export-btn" data-i18n="rec-export">导出明细</button>
                </div>
                <div class="rec-bar">
                    <div class="rec-tabs" id="rec-tabs"></div>
                    <div class="rec-filter" id="rec-filter"></div>
                </div>
                <div class="rec-body" id="rec-body"></div>
                <div class="rec-foot" id="rec-foot"></div>
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
