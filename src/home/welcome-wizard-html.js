// src/home/welcome-wizard-html.js
// REFACTOR-WB-C3 · 登录后欢迎向导(onboarding)4 步骨架 HTML · 从 home.html #onboarding-modal 抽出。
//
// welcome-wizard.js 的 showOnboarding() 懒注入本串到 #onboarding-modal 空壳。wizard 现暂下架
// (maybeShowOnboarding 顶部 early return)→ showOnboarding 永不触发 → 永不注入 → 行为零变化;
// 复活(删那行 return)即按原样注入显示。事件全是 document 委托 · 注入后即生效。verbatim · 0 改结构。
export const ONBOARDING_HTML = `
    <div class="modal onboarding-modal">
        <!-- 顶部装饰渐变带 -->
        <div class="ob-deco">
            <div class="ob-deco-icon">
                <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M16 4l11 6v12l-11 6L5 22V10z"/>
                    <path d="M11 13l5 5 5-5M16 18v8"/>
                </svg>
            </div>
            <button class="ob-close" id="ob-close" aria-label="close">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
            </button>
        </div>

        <!-- 进度圆点 -->
        <div class="ob-progress">
            <span class="ob-dot active" data-step="1"></span>
            <span class="ob-dot" data-step="2"></span>
            <span class="ob-dot" data-step="3"></span>
            <span class="ob-dot" data-step="4"></span>
            <span class="ob-step-label" id="ob-step-label">1 / 4</span>
        </div>

        <!-- Step 1 · 角色 -->
        <div class="ob-step" id="ob-step-1">
            <div class="ob-step-eyebrow" data-i18n="ob-eyebrow">完善资料 · 解锁个性化体验</div>
            <h2 class="ob-step-title" data-i18n="ob-s1-title">您在事务所的角色是?</h2>
            <p class="ob-step-sub" data-i18n="ob-s1-sub">我们将根据角色推荐最合适的功能和模板</p>
            <div class="ob-options" id="ob-role-options">
                <button type="button" class="ob-option" data-value="owner">
                    <span class="ob-option-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 18l3-9 5 4 2-7 2 7 5-4 3 9z"/><path d="M3 21h18"/></svg>
                    </span>
                    <span class="ob-option-text" data-i18n="ob-role-owner">事务所老板 / 合伙人</span>
                </button>
                <button type="button" class="ob-option" data-value="accountant">
                    <span class="ob-option-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><rect x="7" y="5" width="10" height="3" rx="0.5"/><circle cx="8" cy="12" r="0.5" fill="currentColor"/><circle cx="12" cy="12" r="0.5" fill="currentColor"/><circle cx="16" cy="12" r="0.5" fill="currentColor"/><circle cx="8" cy="16" r="0.5" fill="currentColor"/><circle cx="12" cy="16" r="0.5" fill="currentColor"/><circle cx="16" cy="16" r="0.5" fill="currentColor"/></svg>
                    </span>
                    <span class="ob-option-text" data-i18n="ob-role-accountant">注册会计师</span>
                </button>
                <button type="button" class="ob-option" data-value="bookkeeper">
                    <span class="ob-option-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5V21h16"/><path d="M8 7h8M8 11h8M8 15h5"/></svg>
                    </span>
                    <span class="ob-option-text" data-i18n="ob-role-bookkeeper">记账员</span>
                </button>
                <button type="button" class="ob-option" data-value="auditor">
                    <span class="ob-option-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><circle cx="11" cy="14" r="2"/><path d="m13.5 16.5 2 2"/></svg>
                    </span>
                    <span class="ob-option-text" data-i18n="ob-role-auditor">审计师</span>
                </button>
                <button type="button" class="ob-option" data-value="cfo">
                    <span class="ob-option-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><path d="M2 13h20"/></svg>
                    </span>
                    <span class="ob-option-text" data-i18n="ob-role-cfo">CFO / 财务经理</span>
                </button>
                <button type="button" class="ob-option" data-value="business">
                    <span class="ob-option-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><circle cx="9" cy="7" r="0.5" fill="currentColor"/><circle cx="15" cy="7" r="0.5" fill="currentColor"/><circle cx="9" cy="11" r="0.5" fill="currentColor"/><circle cx="15" cy="11" r="0.5" fill="currentColor"/><circle cx="12" cy="7" r="0.5" fill="currentColor"/><circle cx="12" cy="11" r="0.5" fill="currentColor"/></svg>
                    </span>
                    <span class="ob-option-text" data-i18n="ob-role-business">企业主</span>
                </button>
            </div>
        </div>

        <!-- Step 2 · 月单据量 -->
        <div class="ob-step" id="ob-step-2" style="display:none;">
            <div class="ob-step-eyebrow" data-i18n="ob-eyebrow">完善资料 · 解锁个性化体验</div>
            <h2 class="ob-step-title" data-i18n="ob-s2-title">每月大约处理多少张单据?</h2>
            <p class="ob-step-sub" data-i18n="ob-s2-sub">我们会推荐合适的方案 · 不会自动扣费</p>
            <div class="ob-options ob-options-cols-2" id="ob-volume-options">
                <button type="button" class="ob-option" data-value="<100">
                    <span class="ob-option-text"><strong>&lt; 100</strong><span data-i18n="ob-vol-1-tip">小型业务</span></span>
                </button>
                <button type="button" class="ob-option" data-value="100-500">
                    <span class="ob-option-text"><strong>100 - 500</strong><span data-i18n="ob-vol-2-tip">中型事务所</span></span>
                </button>
                <button type="button" class="ob-option" data-value="500-1000">
                    <span class="ob-option-text"><strong>500 - 1000</strong><span data-i18n="ob-vol-3-tip">大型事务所</span></span>
                </button>
                <button type="button" class="ob-option" data-value="1000+">
                    <span class="ob-option-text"><strong>1000+</strong><span data-i18n="ob-vol-4-tip">超大规模</span></span>
                </button>
            </div>
        </div>

        <!-- Step 3 · 国家 -->
        <div class="ob-step" id="ob-step-3" style="display:none;">
            <div class="ob-step-eyebrow" data-i18n="ob-eyebrow">完善资料 · 解锁个性化体验</div>
            <h2 class="ob-step-title" data-i18n="ob-s3-title">主要服务哪个国家的客户?</h2>
            <p class="ob-step-sub" data-i18n="ob-s3-sub">用于自动选择税号验证和发票格式规则</p>
            <div class="ob-options ob-options-cols-2" id="ob-country-options">
                <button type="button" class="ob-option" data-value="TH">
                    <span class="ob-country-badge ob-country-th">TH</span>
                    <span class="ob-option-text" data-i18n="ob-country-th">泰国</span>
                </button>
                <button type="button" class="ob-option" data-value="CN">
                    <span class="ob-country-badge ob-country-cn">CN</span>
                    <span class="ob-option-text" data-i18n="ob-country-cn">中国</span>
                </button>
                <button type="button" class="ob-option" data-value="JP">
                    <span class="ob-country-badge ob-country-jp">JP</span>
                    <span class="ob-option-text" data-i18n="ob-country-jp">日本</span>
                </button>
                <button type="button" class="ob-option" data-value="OTHER">
                    <span class="ob-country-badge ob-country-other">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                    </span>
                    <span class="ob-option-text" data-i18n="ob-country-other">其他</span>
                </button>
            </div>
        </div>

        <!-- Step 4 · LINE ID -->
        <div class="ob-step" id="ob-step-4" style="display:none;">
            <div class="ob-step-eyebrow" data-i18n="ob-eyebrow">完善资料 · 解锁个性化体验</div>
            <h2 class="ob-step-title" data-i18n="ob-s4-title">您的 LINE ID(可选)</h2>
            <p class="ob-step-sub" data-i18n="ob-s4-sub">填了之后我们会通过 LINE 给您发送使用周报、配额提醒和重要更新</p>
            <div class="ob-input-wrap">
                <span class="ob-input-prefix">@</span>
                <input type="text" class="ob-input" id="ob-line-input" placeholder="line_id">
            </div>
            <div class="ob-final-tip">
                <svg class="ob-final-tip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/>
                </svg>
                <span data-i18n="ob-final-tip">填完所有信息 · Pearnly 将根据您的角色和规模推荐最合适的工作流</span>
            </div>
        </div>

        <!-- 底部按钮 -->
        <div class="ob-foot">
            <button type="button" class="ob-btn-skip" id="ob-skip" data-i18n="ob-skip">跳过这一步</button>
            <button type="button" class="ob-btn-next" id="ob-next" data-i18n="ob-next">下一步 →</button>
        </div>
    </div>`;
