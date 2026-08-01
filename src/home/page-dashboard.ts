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
import { BAHT } from './money.js';

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
                        <div class="sub-card-hint" id="dash-kpi-balance-sub" data-i18n="topup-pricing-note">未订阅按量计费:每月前 200 张 ${BAHT}1.50/张 · 超出 ${BAHT}0.75/张;文档(Excel/Word/CSV)按字符量折算计费。</div>
                        <div class="sub-card-foot" id="dash-kpi-balance-foot" style="display:none">
                            <span class="sub-foot-hint" data-i18n="dash-balance-low-hint">余额不足时将影响超额扣费</span>
                            <button class="btn pri sub-topup-btn" id="dash-topup-btn" data-i18n="dash-topup">去充值</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="panel box" style="margin-top:var(--s4)">
                <div class="sub-plans-head">
                    <div>
                        <div class="ch" data-i18n="sub-plans-title">选择套餐</div>
                        <div class="cs" data-i18n="sub-plans-sub">无套餐按量计费 · 订阅后先用套餐额度,超额自动扣余额</div>
                    </div>
                    <div class="sub-rules" id="sub-rules">
                        <button type="button" class="btn sub-rules-btn" id="sub-rules-btn"
                                aria-expanded="false" aria-controls="sub-rules-pop">
                            <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                 stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>
                            </svg>
                            <span data-i18n="sub-rules-title">计费规则</span>
                        </button>
                        <div class="sub-rules-pop" id="sub-rules-pop" role="tooltip">
                            <div class="sub-rules-pop-h" data-i18n="sub-rules-sub">把最关心的计费逻辑讲清楚</div>
                            <ul>
                                <li data-i18n="sub-rule-1">未订阅时,扫描按量计费(前 200 张 ฿ 1.50/张,之后 ฿ 0.75/张)。</li>
                                <li data-i18n="sub-rule-2">一个周期 = 订阅日起 30 天,不是自然月;周期内先用套餐额度,没用完不结转到下个周期。</li>
                                <li data-i18n="sub-rule-3">套餐额度用完后,超出部分按套餐单价自动从余额扣费。</li>
                                <li data-i18n="sub-rule-4">套餐费在订阅当天从余额预扣;周期到期自动续订并重置额度,余额不足则套餐失效转按量。</li>
                                <li data-i18n="sub-rule-5">文档(Excel/Word/CSV)按字符成本折算成额度张数。</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="sub-plans" id="sub-plans"></div>
            </div>

            <div class="panel box rec-box" id="rec-box" style="margin-top:var(--s4)">
                <div class="rec-head">
                    <div>
                        <div class="ch" data-i18n="rec-title">记录明细</div>
                        <div class="cs" data-i18n="rec-sub">扣费 · 充值 · 识别 · 切换查看,导出全部明细</div>
                    </div>
                    <button class="btn rec-export" id="rec-export-btn">导出明细</button>
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

    // 计费规则浮层:展开靠 CSS 的 :hover/:focus-within,这里只补手指——手机没有 hover,
    // 只挂 hover 等于规则在手机上不存在,而客户十有八九是在手机上看账单的。
    const rules = sec.querySelector('.sub-rules') as HTMLElement | null;
    const rulesBtn = sec.querySelector('.sub-rules-btn') as HTMLButtonElement | null;
    if (rules && rulesBtn) {
        const setOpen = (open: boolean) => {
            rules.classList.toggle('open', open);
            rulesBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        };
        rulesBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // 不让下面这条 document 监听同一次点击又立刻关上
            setOpen(!rules.classList.contains('open'));
        });
        document.addEventListener('click', (e) => {
            if (!rules.contains(e.target as Node)) setOpen(false);
        });
        document.addEventListener('keydown', (e) => {
            if ((e as KeyboardEvent).key === 'Escape') setOpen(false);
        });
    }
})();
