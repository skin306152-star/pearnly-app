// ============================================================
// page-dashboard 骨架 · 运行期注入(home.html 空壳 <section id="page-dashboard">)
//
// 2026-06-28 改版:首页 = 订阅与计费。保留账户余额带(余额卡 + 充值按钮 ·
// billing.ts/dashboard.ts 依赖 dash-kpi-balance-card / dash-topup-btn /
// dash-kpi-balance-sub 三个 id),其下换订阅区:
//   当前套餐摘要 #sub-summary → 套餐卡 #sub-plans → 计费规则 + 最近账单 #sub-records。
// 动态内容由 subscription.ts(window.loadSubscription)填充;静态文案走 data-i18n。
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
            </div>

            <div class="panel box" id="sub-summary" style="margin-top:var(--s4)"></div>

            <div class="panel box" style="margin-top:var(--s4)">
                <div class="ch" data-i18n="sub-plans-title">选择套餐</div>
                <div class="cs" data-i18n="sub-plans-sub">无套餐按量计费 · 订阅后先用套餐额度,超额自动扣余额</div>
                <div class="sub-plans" id="sub-plans"></div>
            </div>

            <div class="cols" style="grid-template-columns:1fr 1fr;margin-top:var(--s4)">
                <div class="panel box">
                    <div class="ch" data-i18n="sub-rules-title">计费规则</div>
                    <div class="cs" data-i18n="sub-rules-sub">把最关心的计费逻辑讲清楚</div>
                    <ol class="sub-rules">
                        <li data-i18n="sub-rule-1">未订阅时,扫描按量计费(前 200 张 ฿1.50/张,之后 ฿0.75/张)。</li>
                        <li data-i18n="sub-rule-2">订阅套餐后,每月优先使用套餐内额度。</li>
                        <li data-i18n="sub-rule-3">套餐额度用完后,超出部分按套餐单价自动从余额扣费。</li>
                        <li data-i18n="sub-rule-4">月费从账户余额扣;到期自动续订,余额不足则套餐失效转按量。</li>
                        <li data-i18n="sub-rule-5">文档(Excel/Word/CSV)按字符成本折算成额度张数。</li>
                    </ol>
                </div>
                <div class="panel box">
                    <div class="ch" data-i18n="sub-records-title">最近账单</div>
                    <div class="cs" data-i18n="sub-records-sub">扫描扣费 · 订阅 · 续订</div>
                    <div id="sub-records">
                        <div class="empty"><div class="t" data-i18n="sub-records-empty">暂无账单记录</div></div>
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
