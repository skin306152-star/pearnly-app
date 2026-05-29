// ============================================================
// REFACTOR-WB-C1 (2026-05-29) · 应用外壳渲染(顶栏 brand/配额 banner/侧栏显隐/info chip/上传提示)从 home.js 抽出
//
// 来源:home.js 顶栏/侧栏/配额渲染函数群。全部纯渲染(读 _userInfo/_quota · 写 DOM)· 0 写共享 let。
// 入口 window.{renderBrandWorkspace,renderQuotaBanner,applySidebarVisibility,renderInfoBar,updateUploadHint}:
//   home.js loadAll(post-await)/ applyLang(_userInfo/_quota 守卫)/ saveProfile/saveCompany / 配额刷新 经全局 bare 调。
//   抽成 defer module 后仍安全:loadAll 在 await 后跑(模块已加载)· applyLang boot 期调时 _userInfo/_quota 为 null 守卫短路。
// 依赖的全局(home.js 暴露 · bare 调 · 不 import):t / _userInfo / _quota / svgIcon / escapeHtml /
//   角色判定 shouldHideMoney/canManageTeam/canManageApiKey/isSuperAdmin/isEmployee/isOwner / switchSettingsTab /
//   getMaxFiles/getMaxPagesPerFile/getMaxMbPerFile / window.PEARNLY_ADMIN_MODE。verbatim 搬迁 · 0 改逻辑(仅 prettier)。
// 同 PR 删 home.js 死码 _planDisplayLabel(升级 modal 已下线 · 全仓 0 调用点)。
// ============================================================
/* global _quota, svgIcon, escapeHtml, shouldHideMoney, canManageTeam, canManageApiKey, isSuperAdmin, isEmployee, isOwner, switchSettingsTab, getMaxFiles, getMaxPagesPerFile, getMaxMbPerFile */
/* eslint-disable no-useless-assignment -- verbatim 防御式初始化(let used/total/usageHtml 先初始化再按分支赋值)· 0 改逻辑 */

// v118.8 · 顶栏 brand-workspace · 显示用户公司名 / 姓名 / fallback
function renderBrandWorkspace() {
    const el = document.getElementById('brand-workspace');
    if (!el || !_userInfo) return;
    const u = _userInfo;
    // v118.8.2 · 智能 cleanup · 防 username/name 字段被设成完整 email 字符串
    function clean(s) {
        if (!s || typeof s !== 'string') return null;
        s = s.trim();
        if (!s) return null;
        // 看起来是 email · 取前缀
        if (s.includes('@') && s.indexOf('@') > 0 && s.indexOf('.') > s.indexOf('@')) {
            return s.split('@')[0];
        }
        return s;
    }
    // v118.8.1 · 多字段 fallback 链 · 防后端字段名不一致 / 注册时未填
    const tryFields = [
        u.company_name,
        u.company,
        u.tenant_name,
        u.organization,
        u.org_name,
        u.name,
        u.full_name,
        u.display_name,
        // 这些可能是 email · 用 clean() 截前缀
        u.username,
        u.email,
    ];
    let name = null;
    for (const f of tryFields) {
        const c = clean(f);
        if (c) {
            name = c;
            break;
        }
    }
    if (!name) name = t('brand-workspace-fallback') || '我的工作台';
    el.textContent = name;
    el.title = name;
    el.removeAttribute('data-i18n');
    // v118.8.1 · 调试用 · 出问题时在 console 看 _userInfo 实际字段
    if (!u.company_name && !u.company) {
        console.debug(
            '[Pearnly] brand-workspace fallback to:',
            name,
            '· _userInfo fields:',
            Object.keys(u)
        );
    }
}

// v102 · 顶部配额预警 banner 渲染
// v109.4 · 统一用 tenant_used/tenant_quota · 跟顶栏 chip / 设置页 / 用户管理表对齐
function renderQuotaBanner() {
    const el = document.getElementById('quota-banner');
    if (!el) return;
    if (!_userInfo) {
        el.style.display = 'none';
        return;
    }

    // 超管 / 自带 key 用户:不显示 banner
    if (
        _userInfo.is_super_admin ||
        _userInfo.tenant_type === 'admin' ||
        _userInfo.tenant_type === 'byo_api'
    ) {
        el.style.display = 'none';
        return;
    }

    let used = 0,
        total = 0;
    if (_userInfo.plan === 'free' && _quota && _quota.ip_daily_limit) {
        used = _quota.ip_used_today || 0;
        total = _quota.ip_daily_limit;
    } else if (_userInfo.tenant_quota != null && _userInfo.tenant_quota > 0) {
        // v109.4 · 优先 tenant 字段
        used = _userInfo.tenant_used || 0;
        total = _userInfo.tenant_quota;
    } else if (_userInfo.monthly_quota && _userInfo.monthly_quota > 0) {
        // v109.4 · 兜底用 user 表字段
        used = _userInfo.used_this_month || 0;
        total = _userInfo.monthly_quota;
    } else {
        // 没配额信息 · 不显示 banner
        el.style.display = 'none';
        return;
    }

    if (total <= 0) {
        el.style.display = 'none';
        return;
    }

    const remaining = Math.max(0, total - used);
    const pct = (used / total) * 100;

    // 用户主动关闭过当天的 banner · 不再弹(localStorage 当日 key)
    const todayKey = 'quota_banner_dismiss_' + new Date().toISOString().slice(0, 10);
    if (localStorage.getItem(todayKey)) {
        el.style.display = 'none';
        return;
    }

    let cls, msg;
    if (remaining === 0) {
        cls = 'danger';
        msg = t('quota-banner-exhausted');
    } else if (pct >= 90) {
        cls = 'danger';
        msg = t('quota-banner-very-low', { n: remaining });
    } else if (pct >= 70) {
        cls = 'warn';
        msg = t('quota-banner-low', { n: remaining });
    } else {
        el.style.display = 'none';
        return;
    }

    el.className = 'quota-banner ' + cls;
    el.innerHTML = `
        <span class="quota-banner-icon">${svgIcon('alert', 18)}</span>
        <span class="quota-banner-msg">${escapeHtml(msg)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t('quota-banner-dismiss'))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `;
    el.style.display = 'flex';
    const closeBtn = el.querySelector('.quota-banner-close');
    if (closeBtn)
        closeBtn.addEventListener('click', () => {
            localStorage.setItem(todayKey, '1');
            el.style.display = 'none';
        });
}

// v118.35.0.9 · renderTrialBanner 函数从 home.js 完全删除(v0.8 noop · v0.9 物理移除)·
// 没有调用站还在调它 · 函数不存在也不会报错 · trial-banner div 由 CSS 默认 display:none 兜底

function applySidebarVisibility() {
    // REFACTOR-C1 · 老套餐 v109.3 IIFE 已删(计费迁移收尾 step2)· renderTrialBanner 不复存在 ·
    //   原 window.renderTrialBanner 兜底赋值随之移除(否则引用已删函数会 ReferenceError)。
    // v0.15 · 扁平权限 · 所有用户看到相同的侧栏
    // v118.12 · 全部改用 6 原子函数(isSuperAdmin / isOwner / isEmployee / shouldHideMoney / canManageTeam / canManageApiKey)
    const u = _userInfo;
    if (!u) return;
    const _hideMoney = shouldHideMoney(u);
    const _canTeam = canManageTeam(u);
    const _canApiKey = canManageApiKey(u);

    // 模板 / API Key 主导航 · 目前还没实现 · 保持"即将上线"样式
    const tplNav = document.querySelector('.nav-item[data-route="templates"]');
    if (tplNav) {
        tplNav.classList.remove('locked-for-plan');
        tplNav.removeAttribute('data-locked-target');
    }
    const apiNav = document.querySelector('.nav-item[data-route="api-keys"]');
    if (apiNav) {
        apiNav.classList.remove('locked-for-plan');
        apiNav.removeAttribute('data-locked-target');
    }
    const tplBtn = document.getElementById('btn-custom-template');
    if (tplBtn) {
        tplBtn.style.display = '';
        tplBtn.classList.remove('locked-for-plan');
    }

    // v118.33.2 NAV-IA Phase 2 · sidebar 底部「成本追踪 / 用户管理 / 测试 / adm-lang-bar」整体已删 · 显隐逻辑搬到头像菜单 applyRoleVisibility
    // REFACTOR-C1 · 顶栏超管下拉(#admin-dropdown)+ 老 home.html admin 布局已下线 · 超管走独立 /admin SPA

    // ============================================================
    // v118.12 · 设置页 6 个 tab 显隐(原子函数驱动)
    // ============================================================
    // 团队管理:仅 owner / 超管
    const teamTab = document.querySelector('.settings-tab[data-tab="team"]');
    if (teamTab) teamTab.style.display = _canTeam ? '' : 'none';
    const teamPanel = document.querySelector('.settings-panel[data-settings-panel="team"]');
    if (teamPanel) teamPanel.dataset.permHidden = _canTeam ? '0' : '1';

    // API & 密钥:仅买断 owner / 超管
    const apiTab = document.querySelector('.settings-tab[data-tab="api"]');
    if (apiTab) apiTab.style.display = _canApiKey || isSuperAdmin(u) ? '' : 'none';

    // 套餐 & 用量:员工隐藏
    const planTab = document.querySelector('.settings-tab[data-tab="plan"]');
    if (planTab) planTab.style.display = _hideMoney ? 'none' : '';

    // v118.12 · 公司信息 tab:员工隐藏(公司是事务所属性 · 跟员工无关)
    const companyTab = document.querySelector('.settings-tab[data-tab="company"]');
    if (companyTab) companyTab.style.display = _hideMoney ? 'none' : '';

    // ============================================================
    // v118.12 · 顶栏 / 全局 banner / 升级按钮 · 员工全部隐藏
    // ============================================================
    // info-bar 配额 chip(顶栏右侧 "X/Y 张")
    const infoBar = document.getElementById('info-bar');
    if (infoBar) infoBar.style.display = _hideMoney ? 'none' : '';

    // trial-banner(7 天试用倒计时横幅)
    const trialBanner = document.getElementById('trial-banner');
    if (trialBanner && _hideMoney) trialBanner.style.display = 'none';

    // plan-banner(v109.3 IIFE 那个 fixed 顶部横幅)
    const planBanner = document.getElementById('plan-banner');
    if (planBanner && _hideMoney) {
        planBanner.style.display = 'none';
        document.body.classList.remove('has-plan-banner');
    }

    // v118.35.0.9 · 升级按钮全局 click 绑定永久下线 · 直接隐藏所有 .btn-upgrade / .topbar-upgrade / [data-upgrade-cta]
    document.querySelectorAll('[data-upgrade-cta], .btn-upgrade, .topbar-upgrade').forEach((el) => {
        el.style.display = 'none';
    });

    // body class · 让 CSS 可以基于角色做额外样式收尾(比如员工进设置默认 active 不在公司信息)
    document.body.classList.toggle('role-employee', isEmployee(u));
    document.body.classList.toggle('role-owner', isOwner(u));
    document.body.classList.toggle('role-super', isSuperAdmin(u));

    // v118.12.3 · 关键修复:如果当前 active tab 是被隐藏的(localStorage 恢复了员工无权访问的 tab)
    // 强制切回 profile · 否则员工会看到 team panel 内容 + 调 API 被 403
    try {
        const activeTab = document.querySelector('.settings-tab.active');
        if (activeTab && activeTab.style.display === 'none') {
            if (typeof window.switchSettingsTab === 'function') {
                window.switchSettingsTab('profile');
            } else if (typeof switchSettingsTab === 'function') {
                switchSettingsTab('profile');
            }
        }
    } catch (e) {
        console.warn('[v118.12.3] failed to fix active tab:', e);
    }

    // ============================================================
    // v118.28.2 · 超管 /admin 视图模式
    //   - 显示红色顶部 banner
    //   - 砍所有非超管 nav(普通用户那一套 OCR / 历史 / 设置 全隐)
    //   - 砍顶栏客户切换器(平台管理员视角不需要切租户)
    // ============================================================
    if (window.PEARNLY_ADMIN_MODE) {
        const banner = document.getElementById('admin-mode-banner');
        if (banner) banner.style.display = 'flex';

        document.querySelectorAll('.nav-item').forEach((item) => {
            if (!item.classList.contains('nav-admin-only')) {
                item.style.display = 'none';
            }
        });
        document.querySelectorAll('.nav-group').forEach((group) => {
            if (!group.classList.contains('nav-group-admin-only')) {
                group.style.display = 'none';
            }
        });
        const cs = document.getElementById('client-switcher');
        if (cs) cs.style.display = 'none';
        document.body.classList.add('admin-mode');

        // v118.28.2.1 · 设置页里只保留超管自己用得上的 tab
        // 砍掉:公司信息 / 团队管理 / 套餐 / 归档规则 / 学习规则 / API 密钥 / 通用设置 / 访问日志
        // 保留:个人资料 / 账户安全 / 通知偏好 / 联系我们
        const _adminSettingsAllowed = ['profile', 'security', 'notifications', 'about'];
        document.querySelectorAll('.settings-tab').forEach((tab) => {
            const name = tab.dataset.tab;
            if (name && !_adminSettingsAllowed.includes(name)) {
                tab.style.display = 'none';
            }
        });
        document.querySelectorAll('.settings-pane').forEach((pane) => {
            const name = pane.dataset.pane;
            if (name && !_adminSettingsAllowed.includes(name)) {
                pane.style.display = 'none';
            }
        });
        // 隐藏所有 tab 都被砍掉的分组标题(防止"公司"标题下空荡荡)
        document.querySelectorAll('.settings-nav-group').forEach((group) => {
            const visibleTabs = group.querySelectorAll('.settings-tab');
            const anyVisible = Array.from(visibleTabs).some((t) => t.style.display !== 'none');
            if (!anyVisible) group.style.display = 'none';
        });
    }
}

// v0.15 · renderPlanDropdown 已废弃 · 顶部套餐下拉删除

function renderInfoBar() {
    const user = _userInfo;
    const bar = document.getElementById('info-bar');
    // v118.12 · 员工:配额 chip 是钱相关 · 短路返回(applySidebarVisibility 也设了 display:none 双保险)
    if (!user || shouldHideMoney(user)) {
        if (bar) bar.innerHTML = '';
        return;
    }

    // v87 · 用多租户正确字段 tenant_type 判断(之前用的 account_type 是老字段 · 建号时可能错)
    // shared_api = 月付共用 key · byo_api = 买断自带 key · admin = 超管
    let usageHtml = '';
    const tt = user.tenant_type;
    if (tt === 'byo_api') {
        // 买断自带 key
        if (user.has_own_gemini_key) {
            // 已填 key · 不限
            usageHtml = `
                <div class="info-chip">
                    <span class="chip-value chip-value-lifetime">${escapeHtml(t('info-unlimited-own-key'))}</span>
                </div>
            `;
        } else {
            // 未填 key · 提示
            usageHtml = `
                <div class="info-chip chip-warn">
                    <span class="chip-value">${escapeHtml(t('info-need-api-key'))}</span>
                </div>
            `;
        }
    } else if (tt === 'admin' || user.is_super_admin) {
        // 超管 · 无配额概念
        usageHtml = `
            <div class="info-chip">
                <span class="chip-value chip-value-lifetime">${escapeHtml(t('info-unlimited-own-key'))}</span>
            </div>
        `;
    } else {
        // shared_api · 月付共用 key(默认分支 · trial 也走这条)
        // v109.4 · 优先 tenant 字段 · 缺失回退 user 字段
        const used = user.tenant_used != null ? user.tenant_used : user.used_this_month || 0;
        const total =
            user.tenant_quota != null && user.tenant_quota > 0
                ? user.tenant_quota
                : user.monthly_quota || 0;
        const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0;
        let cls = '';
        if (pct >= 95) cls = 'danger';
        else if (pct >= 80) cls = 'warn';
        if (total > 0) {
            usageHtml = `
                <div class="info-chip">
                    <span class="chip-label">${escapeHtml(t('info-monthly'))}</span>
                    <span class="chip-value">${used} / ${total}</span>
                    <div class="mini-bar"><div class="mini-bar-fill ${cls}" style="width:${pct}%"></div></div>
                </div>
            `;
        } else {
            // 完全无配额信息 · 不显示 chip
            usageHtml = '';
        }
    }

    if (bar) bar.innerHTML = usageHtml;
}

function updateUploadHint() {
    if (!_quota) return;
    document.getElementById('upload-hint').textContent = t('upload-hint', {
        pages: getMaxPagesPerFile(), // v111.2 · 用 plan limits
        mb: getMaxMbPerFile(), // v111.2 · 用 plan limits
        files: getMaxFiles(),
    });
}

// home.js loadAll/applyLang/saveProfile/saveCompany/配额刷新 经全局 bare 调 · 暴露之
window.renderBrandWorkspace = renderBrandWorkspace;
window.renderQuotaBanner = renderQuotaBanner;
window.applySidebarVisibility = applySidebarVisibility;
window.renderInfoBar = renderInfoBar;
window.updateUploadHint = updateUploadHint;
