// ============================================================
// v118.28.1.0 · 测试中心 · 全局错误拦截器(必须最早执行 · 才能拦到所有错误)
// ============================================================
(function () {
    'use strict';
    const BUF_MAX = 200;
    const buf = [];
    function _push(entry) {
        try {
            buf.push(Object.assign({ ts: Date.now() }, entry));
            if (buf.length > BUF_MAX) buf.shift();
            // 通知测试中心红点 + 列表(若已渲染)
            try {
                if (typeof window._tcOnNewLog === 'function') window._tcOnNewLog(entry);
            } catch (_) { /* silent · 测试中心 callback 极少 fail */ }
        } catch (_) { /* silent · log entry 处理外层兜底 */ }
    }
    window._pearnlyTcLogs = buf;
    window._pearnlyTcPush = _push;

    // 1) JS 同步错误
    window.addEventListener('error', function (e) {
        // 资源加载错误 e.target 是元素 · 跳过(信噪比低)
        if (e.target && e.target !== window && (e.target.src || e.target.href)) return;
        _push({
            type: 'js_error',
            summary: String(e.message || 'JS Error').slice(0, 200),
            detail: {
                file: e.filename || '',
                line: e.lineno || 0,
                col: e.colno || 0,
                stack: (e.error && e.error.stack) ? String(e.error.stack).slice(0, 2000) : null,
            },
        });
    }, true);

    // 2) Promise 未捕获
    window.addEventListener('unhandledrejection', function (e) {
        const r = e.reason;
        const msg = (r && r.message) ? r.message : String(r || 'Promise rejected');
        _push({
            type: 'promise_error',
            summary: String(msg).slice(0, 200),
            detail: {
                stack: (r && r.stack) ? String(r.stack).slice(0, 2000) : null,
            },
        });
    });

    // 3) fetch 包装(失败 / 4xx / 5xx / 慢请求 都记)
    const _origFetch = window.fetch;
    if (typeof _origFetch === 'function') {
        window.fetch = function () {
            const args = arguments;
            const t0 = Date.now();
            const url = (typeof args[0] === 'string') ? args[0] : (args[0] && args[0].url) || '?';
            const method = (args[1] && args[1].method) || 'GET';
            const urlClean = String(url).split('?')[0];
            return _origFetch.apply(this, args).then(function (resp) {
                const elapsed = Date.now() - t0;
                if (!resp.ok) {
                    // 失败 · 取响应体片段
                    let bodyPreview = '';
                    try {
                        const clone = resp.clone();
                        clone.text().then(function (txt) {
                            bodyPreview = String(txt || '').slice(0, 500);
                            _push({
                                type: 'api_error',
                                summary: method + ' ' + urlClean + ' → ' + resp.status + ' (' + elapsed + 'ms)',
                                detail: {
                                    url: url, method: method,
                                    status: resp.status,
                                    elapsed_ms: elapsed,
                                    body_preview: bodyPreview,
                                },
                            });
                        }).catch(function () {
                            _push({
                                type: 'api_error',
                                summary: method + ' ' + urlClean + ' → ' + resp.status + ' (' + elapsed + 'ms)',
                                detail: { url: url, method: method, status: resp.status, elapsed_ms: elapsed, body_preview: '(read failed)' },
                            });
                        });
                    } catch (_) {
                        _push({
                            type: 'api_error',
                            summary: method + ' ' + urlClean + ' → ' + resp.status + ' (' + elapsed + 'ms)',
                            detail: { url: url, method: method, status: resp.status, elapsed_ms: elapsed },
                        });
                    }
                } else if (elapsed > 2500) {
                    _push({
                        type: 'api_slow',
                        summary: method + ' ' + urlClean + ' → 慢 ' + elapsed + 'ms',
                        detail: { url: url, method: method, status: resp.status, elapsed_ms: elapsed },
                    });
                }
                return resp;
            }).catch(function (err) {
                const elapsed = Date.now() - t0;
                _push({
                    type: 'api_fail',
                    summary: method + ' ' + urlClean + ' → 网络失败 (' + elapsed + 'ms)',
                    detail: {
                        url: url, method: method, elapsed_ms: elapsed,
                        error: String((err && err.message) || err),
                    },
                });
                throw err;
            });
        };
    }

    // 4) console.error / console.warn 拦截(信噪比中 · 仅取摘要)
    ['error', 'warn'].forEach(function (level) {
        const orig = console[level];
        if (typeof orig !== 'function') return;
        console[level] = function () {
            try {
                const parts = [];
                for (let i = 0; i < arguments.length; i++) {
                    const a = arguments[i];
                    if (typeof a === 'string') parts.push(a);
                    else if (a && a instanceof Error) parts.push(a.message);
                    else {
                        try { parts.push(JSON.stringify(a).slice(0, 300)); }
                        catch (_) { parts.push(String(a)); }
                    }
                }
                _push({
                    type: 'console_' + level,
                    summary: parts.join(' ').slice(0, 200),
                    detail: { full: parts.join(' ').slice(0, 1500) },
                });
            } catch (_) { /* silent · log CustomEvent dispatch 极少 fail */ }
            return orig.apply(console, arguments);
        };
    });
})();

// ============================================================
// Pearnly · I18N Dictionary (zh/en/th/ja)
// ============================================================
const I18N = window.I18N;  // REFACTOR-C1(2026-05-25)· I18N 字典已抽到 static/i18n-data.js · home.html 在 home.js 前 sync 加载 window.I18N
// ============================================================
// Pearnly · Home JS (v0.3.5)
// 侧栏 + Hash 路由 + 套餐对比弹窗 + 权限控制
// ============================================================

// I18N 字典会被另外 concat 进来
// ============================================================
// v118.26.1.2 · i18n 订阅总线(根治"切语言不刷新"反复出现的 bug)
// ============================================================
//
// 背景:Pearnly 的 i18n 是"声明式 + 命令式"两套机制:
//   1) HTML 标签 data-i18n 静态文案 → applyLang() 自动扫 DOM 替换 ✓
//   2) JS 用 t() 拼 innerHTML 动态文案 → 切语言后字符串已经写死了 · 必须模块自己重渲
//
// 历史方案(分散注册):每个模块暴露 window._rerenderXXX · applyLang 里散落 try 块逐个调
// 痛点:写新模块时 ① 暴露 _rerender ② 在 applyLang 加 try 钩子 ③ 钩子内调全部
//       3 步任意 1 步漏 = 切语言新 bug(已经发生 ≥ 5 次)
//
// 新方案(订阅总线):
//   模块加载时调 subscribeI18n('模块名', _rerenderAll)
//   切语言时 applyLang 末尾统一遍历 __i18nSubs · 自动通知所有订阅者
//
// 铁律(写进 DESIGN_SYSTEM.md):
//   任何用 t() 函数动态生成 innerHTML 的 IIFE 模块 · 必须在加载时调用
//   window.subscribeI18n('模块名', 重渲函数) · 否则切语言 = 旧文案残留
//
// 配套:scripts/check_i18n.py(发版前 lint · 扫漏注册)
// ============================================================
window.__i18nSubs = window.__i18nSubs || [];
window.subscribeI18n = function(name, fn) {
    if (typeof fn !== 'function') {
        console.warn('[i18n] subscribeI18n: fn must be function · name=' + name);
        return;
    }
    // 同名只注册一次(防 IIFE 重复执行 · 重复挂钩)
    const exist = window.__i18nSubs.find(s => s.name === name);
    if (exist) { exist.fn = fn; return; }
    window.__i18nSubs.push({ name: String(name || '?'), fn: fn });
};

// ============================================================
// 状态
// ============================================================
let currentLang = localStorage.getItem('mrpilot_lang') || 'th';
window._currentLang = currentLang;  // expose to IIFEs that can't access closure variable
let currentRoute = 'ocr';
let _userInfo = null;
let _quota = null;
let _contact = null;
let _selectedFiles = [];
let _results = [];
let _sortKey = null;
let _sortDir = 'asc';
let _searchKeyword = '';
let _drawerIdx = -1;
let _drawerAlreadyPushed = false;
let _engineCheckTimer = null;



const token = localStorage.getItem('mrpilot_token');
if (!token) window.location.href = '/';






// v0.15 · 删除顶部套餐下拉 · 所有用户权限一致


// v118.33.2 NAV-IA Phase 2 · adm-lang-bar IIFE 已删 · admin/超管走「设置 → 通用设置」或 Cmd+K 切 4 语

// ============================================================
// 侧栏 + 路由
// ============================================================
const SIDEBAR_COLLAPSED_KEY = 'mrpilot_sidebar_collapsed';
if (localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1') {
    document.body.classList.add('sidebar-collapsed');
}
document.getElementById('sidebar-toggle').addEventListener('click', () => {
    if (window.innerWidth <= 768) {
        document.body.classList.toggle('sidebar-open');
    } else {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY,
            document.body.classList.contains('sidebar-collapsed') ? '1' : '0');
    }
});

// v86 · 顶栏汉堡按钮(手机端打开侧栏)
document.getElementById('topbar-hamburger')?.addEventListener('click', () => {
    document.body.classList.toggle('sidebar-open');
});
// v86 · 点击遮罩关闭侧栏
document.getElementById('sidebar-overlay')?.addEventListener('click', () => {
    document.body.classList.remove('sidebar-open');
});


window.addEventListener('hashchange', () => {
    const r = (location.hash || '#/ocr').replace(/^#\//, '');
    routeTo(r);
});

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        // v0.15 · 「即将」菜单项(data-locked="1")给 toast · 不切路由
        if (item.dataset.locked === '1') {
            showToast(t('feature-coming-soon'), 'info');
            return;
        }
        routeTo(item.dataset.route);
    });
});

// v118.33.7.3 · sidebar-cta-upload 已删 · 对齐 prototype_final(prototype sidebar 无 CTA)



// A4 (v118.34.19 · Zihao 2026-05-19 拍板) · 集成主页面顶部 tab 切换
// + "看推送日志 →" 链接(从 ERP 卡片 / 也可来自其他地方)
(function () {
    function _activateIntTopTab(targetKey) {
        const tabs = document.querySelectorAll('#page-integrations .int-top-tab');
        const panels = document.querySelectorAll('#page-integrations .int-top-panel');
        tabs.forEach(t => {
            const k = t.dataset.intTopTab;
            t.classList.toggle('active', k === targetKey);
        });
        panels.forEach(p => {
            const k = p.dataset.intTopPanel;
            p.classList.toggle('active', k === targetKey);
        });
        // 切到 logs · 触发一次 fetch 让用户立刻看到数据
        if (targetKey === 'logs' && typeof loadErpLogs === 'function') {
            try { loadErpLogs(); } catch (e) {}
            if (typeof loadErpTodayStats === 'function') {
                try { loadErpTodayStats(); } catch (e) {}
            }
        }
    }
    // 暴露给 ERP 抽屉「看推送日志 →」按钮调用
    window.activateIntegrationsLogsTab = function () {
        // 如果集成抽屉打开了 · 关掉
        try {
            const drawer = document.getElementById('int-drawer');
            const overlay = document.getElementById('int-drawer-overlay');
            if (drawer) drawer.classList.remove('open');
            if (overlay) overlay.classList.remove('open');
            // 调用现有的关闭逻辑(若存在)清理 panel 归还
            if (typeof window.closeIntegrationDrawer === 'function') {
                window.closeIntegrationDrawer();
            }
        } catch (e) {}
        // 切到集成页 + logs tab
        if (typeof window.navigateTo === 'function') {
            try { window.navigateTo('integrations'); } catch (e) {}
        } else {
            try { location.hash = '#/integrations'; } catch (e) {}
        }
        _activateIntTopTab('logs');
        // 滚顶
        try {
            const page = document.getElementById('page-integrations');
            if (page) page.scrollIntoView({ block: 'start', behavior: 'smooth' });
        } catch (e) {}
    };

    document.addEventListener('click', function (e) {
        // tab 切换
        const tab = e.target.closest('#page-integrations .int-top-tab');
        if (tab) {
            const k = tab.dataset.intTopTab;
            if (k) _activateIntTopTab(k);
            return;
        }
        // 「看推送日志 →」按钮(集成页 ERP 卡片 OR ERP 抽屉内 ERP 连接卡片)
        const logsBtn = e.target.closest('[data-int-action="view-logs"], .int-btn-view-logs');
        if (logsBtn) {
            e.preventDefault();
            e.stopPropagation();
            window.activateIntegrationsLogsTab();
        }
    });

    // 路由切到 #/integrations 时 · 如果 hash 带 ?tab=logs · 自动切 logs
    function _onRouteToIntegrations() {
        const h = (location.hash || '').toLowerCase();
        if (h.includes('integrations') && h.includes('tab=logs')) {
            setTimeout(() => _activateIntTopTab('logs'), 50);
        }
    }
    window.addEventListener('hashchange', _onRouteToIntegrations);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        _onRouteToIntegrations();
    } else {
        document.addEventListener('DOMContentLoaded', _onRouteToIntegrations);
    }
})();

// v118.32.5.5.37 · 集成配置抽屉核心函数
(function () {
    'use strict';

    // 把 .auto-panel 从 drawer body 归还到 .auto-content
    function _returnPanel() {
        const body = document.getElementById('int-drawer-body');
        if (!body) return;
        const autoContent = document.querySelector('.auto-content');
        if (!autoContent) return;
        Array.from(body.querySelectorAll('.auto-panel')).forEach(function (el) {
            el.style.display = '';
            autoContent.appendChild(el);
        });
    }

    window.openIntegrationDrawer = function (tab, title) {
        const drawer = document.getElementById('int-drawer');
        const overlay = document.getElementById('int-drawer-overlay');
        const titleEl = document.getElementById('int-drawer-title');
        const body = document.getElementById('int-drawer-body');
        if (!drawer || !body) return;

        // 先归还上一个 panel
        _returnPanel();

        drawer.dataset.currentTab = tab || '';
        if (titleEl) titleEl.textContent = title || '';
        body.innerHTML = '';

        // anchor → data-auto-panel ID 映射(自动化页面里的 panel 名)
        var _panelIds = { line: 'linebot', folder: 'folder', email: 'email', alert: 'alert', erp: 'erp', bank: 'bank' };
        var panelId = _panelIds[tab] || tab;

        // 把对应的 auto-panel 移入抽屉(DOM move · 保留事件监听)
        const panel = document.querySelector('.auto-panel[data-auto-panel="' + panelId + '"]');
        if (panel) {
            panel.style.display = 'block';
            body.appendChild(panel);
        } else {
            body.innerHTML = '<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>';
        }

        // 打开动画
        drawer.classList.add('open');
        if (overlay) overlay.style.display = 'block';
        document.body.style.overflow = 'hidden';

        // 触发数据加载(panel 已在 DOM 里 · loader 按固定 ID 渲染)
        var loaders = {
            line:   window._loadLineBotPanel,
            folder: window._loadFolderWatcherPanel,
            email:  window._loadEmailIngestPanel,
            alert:  window._loadNotificationsPanel,
            bank:   window._loadBankReconPanel,
        };
        if (loaders[tab]) {
            try { loaders[tab](); } catch (e) { console.warn('[int-drawer] loader error', e); }
        } else if (tab === 'erp') {
            try {
                if (typeof loadErpEndpoints === 'function') loadErpEndpoints();
                if (typeof loadErpLogs === 'function') loadErpLogs();
            } catch (e) { console.warn('[int-drawer] ERP load error', e); }
        }
    };

    window.closeIntegrationDrawer = function () {
        _returnPanel();
        var drawer = document.getElementById('int-drawer');
        var overlay = document.getElementById('int-drawer-overlay');
        if (drawer) {
            drawer.classList.remove('open');
            drawer.dataset.currentTab = '';
        }
        if (overlay) overlay.style.display = 'none';
        document.body.style.overflow = '';
    };

    // 绑定关闭事件
    function _initDrawerEvents() {
        var closeBtn = document.getElementById('int-drawer-close');
        var overlay = document.getElementById('int-drawer-overlay');
        if (closeBtn) closeBtn.addEventListener('click', window.closeIntegrationDrawer);
        if (overlay) overlay.addEventListener('click', window.closeIntegrationDrawer);
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') window.closeIntegrationDrawer();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _initDrawerEvents);
    } else {
        _initDrawerEvents();
    }
})();


// v118.33.2 NAV-IA Phase 2 · _initSidebarUserMenu / renderSidebarUser 已删 · 替代品在右上角头像菜单(avatar-popup · Phase 1 上线)· 设置 / 帮助 / 退出全部从那里走




// v118.10 · 设置页 · tab 点击绑定 + 持久化恢复
(function initSettingsTabs() {
    function bind() {
        const tabs = document.querySelectorAll('.settings-tab');
        if (!tabs.length) { setTimeout(bind, 200); return; }
        tabs.forEach(t => {
            t.addEventListener('click', () => switchSettingsTab(t.dataset.tab));
        });
        // 恢复上次 tab(若 tab 因权限隐藏 · 退回 profile)
        let saved = null;
        try { saved = localStorage.getItem('mrpilot_settings_tab'); } catch(e){}
        if (saved) {
            const target = document.querySelector(`.settings-tab[data-tab="${saved}"]`);
            if (target && target.style.display !== 'none') {
                switchSettingsTab(saved);
                return;
            }
        }
        switchSettingsTab('profile');
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else { bind(); }
})();


// v118.10 · 绑定保存按钮
(function bindSettingsForms() {
    function bind() {
        const p = document.getElementById('btn-save-profile');
        const c = document.getElementById('btn-save-company');
        if (!p && !c) { setTimeout(bind, 200); return; }
        if (p) p.addEventListener('click', saveProfile);
        if (c) c.addEventListener('click', saveCompany);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bind);
    } else { bind(); }
})();

// v118.28.5.1 · 设置 → 系统 → 通用设置(语言 + 时区 + 日期格式 + 数字格式)



// v0.15 · renderPlanDropdown 已废弃 · 顶部套餐下拉删除



// ============================================================
// 升级弹窗(对比表)
// ============================================================
function _planDisplayLabel(plan) {
    // v0.12 · plan 的显示名(不直接用 plan.toUpperCase)
    if (plan === 'monthly')  return t('plan-monthly-name') || 'Monthly';
    if (plan === 'lifetime') return t('plan-lifetime-name') || 'Lifetime';
    if (plan === 'free')     return t('plan-free-name') || 'Free';
    if (plan === 'plus')     return 'Plus';
    if (plan === 'pro')      return 'Pro';
    return plan.charAt(0).toUpperCase() + plan.slice(1);
}

// v118.35.0.9 · 升级 modal 已永久下线 · 函数从 home.js 物理移除 · 相关 DOM 监听器也删干净

// 全局 data-upgrade 按钮 · v0.15 不再触发升级窗 · 静默忽略
document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-upgrade]');
    if (el) {
        e.preventDefault();
        // no-op · 以前会弹升级窗
    }
});


// ============================================================
// 侧栏锁定项点击
// ============================================================
document.querySelectorAll('.nav-item[data-locked]').forEach(item => {
    item.addEventListener('click', (e) => {
        const route = item.dataset.route;
        const badge = item.querySelector('.nav-badge');
        const text = badge ? badge.textContent.toLowerCase() : '';
        // 已经在 routeTo 里了,锁定的页面会显示占位和升级按钮
    });
});

// ============================================================
// 文件选择
// ============================================================



function startEnginePolling() {
    stopEnginePolling();
    _engineCheckTimer = setInterval(async () => {
        try {
            const h = await fetch('/api/health').then(r => r.json());
            if (h.ocr_ready) stopEnginePolling();
        } catch {}
    }, 10000);
}
function stopEnginePolling() {
    if (_engineCheckTimer) { clearInterval(_engineCheckTimer); _engineCheckTimer = null; }
}






// 事件代理:抽屉内 RD 按钮点击(校验 / 同步 / 锁图标升级提示)
document.getElementById('drawer-body').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-rd-action]');
    if (btn) {
        const action = btn.dataset.rdAction;
        const side = btn.dataset.rdSide;
        if (action === 'verify') callRdVerify(side);
        else if (action === 'sync') callRdSync(side);
        return;
    }
    const lockBtn = e.target.closest('.rd-btn-locked');
    if (lockBtn) {
        showToast(t('feature-contact-us'), 'info');
        return;
    }
    // v0.8.1 · 归档名一键复制
    const copyBtn = e.target.closest('[data-archive-copy]');
    if (copyBtn) {
        const name = copyBtn.dataset.archiveCopy;
        navigator.clipboard?.writeText(name).then(() => {
            showToast(t('copied'), 'success');
        }).catch(() => {
            showToast(t('copy-failed'), 'error');
        });
    }
});

document.getElementById('drawer-close').addEventListener('click', () => closeDrawer());
document.getElementById('drawer-mask').addEventListener('click', () => closeDrawer());
// v118.17 · drawer-diagnose 按钮已删 · 此处监听器同步移除(否则 getElementById 返 null · addEventListener 报错卡死整个 home.js)

function openDiagnoseDialog() {
    const r = _results[_drawerIdx];
    if (!r) return;
    // 收集能展示的所有原始数据
    const data = {
        filename: r.filename,
        engine: r.engine,
        page_count: r.page_count,
        elapsed_ms: r.elapsed_ms,
        confidence: r.confidence,
        archive_name: r.archive_name,
        category_tag: r.category_tag,
        merged_fields: r.merged_fields,
        pages: r.pages,  // 完整的 Gemini 原始返回
    };
    const json = JSON.stringify(data, null, 2);

    const modal = document.createElement('div');
    modal.className = 'log-detail-modal';
    modal.innerHTML = `
        <div class="log-detail-box" style="max-width:780px;">
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px;vertical-align:-4px;"><circle cx="10" cy="10" r="7"/><path d="M10 7v4M10 13v0.5"/></svg>
                    ${escapeHtml(t('diagnose-title'))}
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>
            <div style="padding: 6px 0 12px; font-size:12px; color: var(--ink-3);">
                ${escapeHtml(t('diagnose-hint'))}
            </div>
            <div class="diagnose-actions">
                <button class="btn btn-ghost btn-tiny" id="btn-diag-copy">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="4" width="8" height="8" rx="1"/><path d="M10 2H3a1 1 0 00-1 1v7" stroke-linecap="round"/></svg>
                    <span>${escapeHtml(t('diagnose-copy'))}</span>
                </button>
            </div>
            <pre class="diagnose-json">${escapeHtml(json)}</pre>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.classList.contains('log-detail-close')) {
            modal.remove();
        }
    });
    document.getElementById('btn-diag-copy').addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(json);
            showToast(t('diagnose-copied'), 'success');
        } catch (e) {
            showToast(t('diagnose-copy-fail'), 'error');
        }
    });
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // v118.35.0.9 · 升级 modal 已下线 · 只剩 drawer 处理
        if (document.getElementById('drawer').classList.contains('show')) closeDrawer();
    }
});

// v0.15 · 自定义模板 · 扁平权限下解锁 · 功能还没做 · 先显示 toast
// v118.27.5.3 · 占位按钮已 hidden(被 split 下拉取代)· 留事件防 JS 报错
const _btnCustomTpl = document.getElementById('btn-custom-template');
if (_btnCustomTpl) _btnCustomTpl.addEventListener('click', () => {
    showToast(t('cs-coming-soon'), 'info');
});




// v118.35.0.16 · BYO Gemini Key 全套(loadGeminiKeyInfo/saveGeminiKey/testGeminiKey/clearGeminiKey + setApiKeyMsg) 物理删除


// 事件绑定(页面加载时只绑一次)
document.addEventListener('DOMContentLoaded', () => {
    // v118.35.0.16 · BYO Gemini Key 按钮事件绑定永久下线

    // v92 · Bug 7 · 断网横幅
    installNetworkBanner();
});





// ============================================================
// 第 5.3 批 · 历史记录页
// ============================================================

const _historyState = {
    page: 0,
    pageSize: 20,
    total: 0,
    keyword: '',
    range: 90,
    items: [],
    loading: false,
};

// 通用:渲染页头右侧的信息条(Plan 徽章 + 月用量进度)· 参考识别页风格
function renderPageHeadInfo(containerId) {
    const el = document.getElementById(containerId);
    if (!el || !_userInfo) return;

    const plan = _userInfo.plan || 'free';
    const planLabel = plan.charAt(0).toUpperCase() + plan.slice(1);

    let usageHtml = '';
    if (plan === 'free' && _quota && _quota.ip_daily_limit) {
        const used = _quota.ip_used_today || 0;
        const total = _quota.ip_daily_limit;
        const pct = Math.min(100, (used / total) * 100);
        const cls = pct >= 90 ? 'danger' : (pct >= 70 ? 'warn' : '');
        usageHtml = `
            <div class="info-chip">
                <span class="chip-label">${t('info-daily')}</span>
                <span class="chip-value">${used} / ${total}</span>
                <div class="mini-bar"><div class="mini-bar-fill ${cls}" style="width:${pct}%"></div></div>
            </div>
        `;
    } else if (_userInfo.tenant_quota) {
        // v109.4 · 改用 tenant_used/tenant_quota · 跟其他组件对齐
        const used = _userInfo.tenant_used || 0;
        const total = _userInfo.tenant_quota;
        const pct = Math.min(100, (used / total) * 100);
        const cls = pct >= 90 ? 'danger' : (pct >= 70 ? 'warn' : '');
        usageHtml = `
            <div class="info-chip">
                <span class="chip-label">${t('info-monthly')}</span>
                <span class="chip-value">${used} / ${total}</span>
                <div class="mini-bar"><div class="mini-bar-fill ${cls}" style="width:${pct}%"></div></div>
            </div>
        `;
    }

    el.innerHTML = `
        <div class="info-chip">
            <span class="chip-value plan-${plan}">${planLabel}</span>
        </div>
        ${usageHtml}
    `;
}

// v0.16 · 历史记录多选删除状态(页面级 · 切页/搜索/刷新都会清空)
const _historySelected = new Set();




// ============================================================
// v0.6.1 · 自动化页(ERP 端点管理)
// ============================================================
let _erpEndpoints = [];
window._erpEndpoints = _erpEndpoints;


















// ============================================================
// v109.1 END
// ============================================================




// v113 · expose I18N · 给将来可能的外部脚本用
try { window.I18N = I18N; } catch(e) {}






// ============================================================
// B4 (2026-05-26) · 旧顶栏客户切换器(ClientSwitcher · 全 app 买方过滤器)已移除 ·
//   被 workspace 工作模式切换器取代(src/home/workspace-switcher.js · 右上角唯一入口)。
//   - window.getCurrentClientId 不再定义 · 余下消费者(history 2987 / dashboard 4872)
//     均有 typeof===function 守卫 → 自动降级"显示全部"· 不崩。
//   - 旧 'pearnly:client-changed' 事件的派发/监听随 IIFE 一起删除(自包含)。
//   - 旧 cs-* DOM 标签 + CSS 成为死代码(harmless · C2 清 home.css 时一并删)。
// ============================================================

// ============================================================
// REFACTOR-C1(2026-05-25)· 测试中心(Test Center)已抽到 src/home/test-center.js
//   (ES module · Vite bundle → static/dist/main.js · 经 window.loadTestCenterPage 入口)
// ============================================================




// ============================================================
// v118.27.0.1 · 全局确认弹窗(替代原生 confirm · 跟 Pearnly 整体 UI 一致)
// 用法:pearnlyConfirm(消息, 标题?).then(ok => { if (ok) { ... } })
// ============================================================
window.pearnlyConfirm = function (message, title) {
    return new Promise(function (resolve) {
        const overlay = document.getElementById('pearnly-confirm-modal');
        const titleEl = document.getElementById('pearnly-confirm-title');
        const msgEl = document.getElementById('pearnly-confirm-msg');
        const okBtn = document.getElementById('pearnly-confirm-ok');
        const cancelBtn = document.getElementById('pearnly-confirm-cancel');
        const closeBtn = document.getElementById('pearnly-confirm-close');
        if (!overlay || !msgEl || !okBtn || !cancelBtn) {
            // 兜底:DOM 不在时退回原生 confirm
            resolve(window.confirm(message));
            return;
        }
        if (titleEl) {
            titleEl.textContent = title || (typeof t === 'function' ? t('confirm-default-title') : 'Please confirm');
        }
        msgEl.textContent = message || '';
        overlay.style.display = 'flex';
        function cleanup(result) {
            overlay.style.display = 'none';
            okBtn.removeEventListener('click', onOk);
            cancelBtn.removeEventListener('click', onCancel);
            if (closeBtn) closeBtn.removeEventListener('click', onCancel);
            overlay.removeEventListener('click', onBgClick);
            document.removeEventListener('keydown', onKey);
            resolve(result);
        }
        function onOk()     { cleanup(true); }
        function onCancel() { cleanup(false); }
        function onBgClick(ev) { if (ev.target === overlay) cleanup(false); }
        function onKey(ev) {
            if (ev.key === 'Escape') cleanup(false);
            else if (ev.key === 'Enter') cleanup(true);
        }
        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
        if (closeBtn) closeBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onBgClick);
        document.addEventListener('keydown', onKey);
        // 焦点放到「取消」上(避免误触确定)
        setTimeout(function () { try { cancelBtn.focus(); } catch (e) {} }, 50);
    });
};







// ============================================================
// v118.32.5.5.24 · 屎山清理:删除 v118.27.5.4 老版本检测横幅(pn-version-banner)
// 已被 static/version-banner.js 替代(顶部弹窗 · 4 语 release_notes)
// 整段移除 · IIFE / DOM / 配套 CSS / 行为全删
// ============================================================



// ============================================================
// v27.8.1.14b.3 · 删 14b.2 加的 banner / 历史页死下拉
// 顶栏客户切换器是 Single Source of Truth · 不再多入口
// ============================================================













