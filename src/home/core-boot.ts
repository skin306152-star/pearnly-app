// REFACTOR-C1-home-batch9f · 真核心编排+引导层 cutover(从 home.js verbatim 抽出 · 0 逻辑改)
// applyLang/setupDropdown/routeTo/loadAll + 引导期 render 助手 + bootstrap(尾部 import 自执行)。
// main.js 第 2 个 import(紧随 core.js):裸调 t/apiGet/escapeHtml/getMax* 经全局对象解析到 core.js 已挂的 window.X。
// bootstrap 仍先于其余 sibling 模块 eval · typeof window.fn 守卫 + 模块自举范式照旧成立。
/* global I18N, currentLang:writable, _quota:writable, _contact:writable, escapeHtml, svgIcon, apiGet, getMaxFiles, getMaxPagesPerFile, getMaxMbPerFile, renderErpEndpointsList, loadErpLogs, loadErpTodayStats, renderHistoryList, applyRoleVisibility, renderAvatarMenu */

// ============================================================
// 语言切换
// ============================================================
function applyLang(lang?: any) {
    // v117 · 防止切语言时看到"左侧先变 / 右侧后变"的分帧顺序
    // 加 class → 同步替换 DOM → 双 rAF 后移除 class · 让所有 i18n 文字一起淡入
    document.body.classList.add('lang-switching');

    // v118.2 · 全局 overlay · 覆盖动态 render 滞后(admin 表格 / 套餐 modal 等)
    const _langOverlay = document.getElementById('lang-switching-overlay');
    if (_langOverlay) _langOverlay.classList.add('show');

    currentLang = lang;
    window._currentLang = lang; // sync to global so all IIFEs read correct language
    localStorage.setItem('mrpilot_lang', lang);
    document.documentElement.lang = lang;

    // v0.19 · T1 · 同步偏好语言到后端(LINE Bot 等场景用)
    // v118.28.1.1 · debounce 200ms + AbortController · 防用户连续切语言时多次并发
    //   - 之前问题:用户测试 4 语连点 → 4 次 fetch 排队 · 最后到的等 16 秒
    //   - 现在:200ms 内多次切语言 · 只发最新一次 · 旧请求 abort
    try {
        const token = localStorage.getItem('mrpilot_token');
        if (token) {
            // 取消上一次未完成的请求
            if (window.__langSyncCtrl) {
                try {
                    window.__langSyncCtrl.abort();
                } catch (_) {
                    /* silent · 已 abort / race */
                }
            }
            // 取消上一次 debounce timer
            if (window.__langSyncTimer) {
                clearTimeout(window.__langSyncTimer);
            }
            window.__langSyncTimer = setTimeout(function () {
                window.__langSyncCtrl = new AbortController();
                fetch('/api/me/lang', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: 'Bearer ' + token,
                    },
                    body: JSON.stringify({ lang: lang }),
                    signal: window.__langSyncCtrl.signal,
                }).catch(function () {});
            }, 200);
        }
    } catch (e) {}

    document.querySelectorAll('[data-i18n]').forEach((el) => {
        const key = el.getAttribute('data-i18n') as string;
        if (I18N[lang] && I18N[lang][key]) el.textContent = I18N[lang][key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
        const key = el.getAttribute('data-i18n-placeholder') as string;
        if (I18N[lang] && I18N[lang][key]) (el as HTMLInputElement).placeholder = I18N[lang][key];
    });

    // v118.28.5 · 顶栏 lang-current / lang-dropdown 已删除 · 改为兜防御 + 同步设置页
    const _langCurrent = document.getElementById('lang-current');
    if (_langCurrent) _langCurrent.textContent = I18N[lang]['lang-name'];
    document.querySelectorAll('#lang-dropdown .dd-item').forEach((item) => {
        item.classList.toggle('active', (item as HTMLElement).dataset.lang === lang);
    });
    // v118.28.5.1 · 设置 → 系统 → 通用设置:同步语言 select 当前选中项
    const _genLangSel = document.getElementById('general-lang');
    if (_genLangSel) (_genLangSel as HTMLSelectElement).value = lang;

    // 置信度列 tooltip · 原生 title(自定义 data-tip 在 overflow-x 表格里撑滚动条+盖字)
    const th = document.getElementById('col-conf-th');
    if (th) th.setAttribute('title', t('col-conf-tip'));

    if (_userInfo && typeof window.renderInfoBar === 'function') window.renderInfoBar();
    if (_quota) updateUploadHint();
    if (currentRoute === 'settings' && typeof window.renderSettings === 'function')
        window.renderSettings();

    // v0.10 · 切语言后重渲染所有动态 innerHTML 区(避免残留旧语言)
    // 用 window.xxx 访问避免 TDZ(变量可能还没声明到)
    try {
        if (
            typeof renderErpEndpointsList === 'function' &&
            window._erpEndpoints &&
            window._erpEndpoints.length
        ) {
            renderErpEndpointsList();
        }
    } catch (e) {}
    try {
        // 推送日志独立页(2026-07-01 · 从集成页抽出)· 切语言刷新
        if (
            typeof loadErpLogs === 'function' &&
            (currentRoute === 'automation' || currentRoute === 'push-logs')
        ) {
            loadErpLogs();
            if (typeof loadErpTodayStats === 'function') loadErpTodayStats();
        }
    } catch (e) {}
    // v0.17 · M6 · 邮箱抓取 panel 重渲染
    try {
        if (typeof window._rerenderEmailIngest === 'function' && currentRoute === 'automation') {
            window._rerenderEmailIngest();
        }
    } catch (e) {}
    // 归档编辑器(设置页打开着的话)
    try {
        if (typeof window._rerenderArchiveAll === 'function') {
            window._rerenderArchiveAll();
        }
    } catch (e) {}
    // v118.20.2.1 · 异常栏 chips + list 切语言重渲(不重新发请求 · 用缓存)
    try {
        if (typeof window._rerenderExceptions === 'function' && currentRoute === 'exceptions') {
            window._rerenderExceptions();
        }
    } catch (e) {}
    // v118.22.2.1 · 智能提醒 chips/列表/日志/弹窗切语言重渲
    try {
        if (typeof window._rerenderNotifications === 'function' && currentRoute === 'automation') {
            window._rerenderNotifications();
        }
    } catch (e) {}
    // 历史行
    try {
        if (typeof renderHistoryList === 'function' && currentRoute === 'history') {
            renderHistoryList();
        }
    } catch (e) {}
    // REFACTOR-C1 · 老 home.html admin 布局(admin-users / admin-cost)已整体下线
    //   超管走独立 /admin SPA · home.html admin 路由对所有角色不可达 · 切语言重渲块随之删除
    // v107 · 客户管理页切语言重渲染
    try {
        if (currentRoute === 'clients' && typeof window.loadClientsPage === 'function') {
            window.loadClientsPage();
        }
    } catch (e) {}

    // v118.26.1.2 · 统一通知所有用 subscribeI18n 注册的模块
    // (新模块走这条路径 · 不再加散落的 try 块)
    if (Array.isArray(window.__i18nSubs)) {
        for (const sub of window.__i18nSubs as any[]) {
            try {
                sub.fn();
            } catch (e) {
                console.warn('[i18n] sub "' + sub.name + '" rerender failed:', e);
            }
        }
    }

    // v117 · 双 rAF 等浏览器绘制完同步替换的 DOM 后,统一淡入新文字
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            document.body.classList.remove('lang-switching');
        });
    });

    // v118.2 · 等 400ms 后隐藏 overlay · 给异步 fetch (admin 表格 / 套餐 modal) 一点时间完成
    // 比看到 5 秒撕裂体验好很多
    setTimeout(() => {
        const ov = document.getElementById('lang-switching-overlay');
        if (ov) ov.classList.remove('show');
    }, 400);
}

// ============================================================
// 下拉菜单通用
// ============================================================
function setupDropdown(id?: any, onSelect?: any) {
    const dd = document.getElementById(id);
    if (!dd) return;
    const toggle = dd.querySelector('.dd-btn');
    toggle!.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.dropdown.open').forEach((el) => {
            if (el !== dd) el.classList.remove('open');
        });
        dd.classList.toggle('open');
    });
    dd.querySelectorAll('.dd-item').forEach((item) => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            dd.classList.remove('open');
            onSelect(item);
        });
    });
}
document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown.open').forEach((el) => el.classList.remove('open'));
});
setupDropdown('lang-dropdown', (item: any) => applyLang(item.dataset.lang));

// 路由表抽 route-table.ts(纯数据 · 控本文件行数):加新页改那边,这里只消费。
import { VALID_ROUTES, ROUTE_LOADERS } from './route-table.js';

function routeTo(route?: any) {
    // REFACTOR-C1 · 老 admin/admin-users/admin-cost 路由已下线(超管走独立 /admin SPA)· 落到 ocr
    if (!VALID_ROUTES.includes(route)) route = 'dms-intake';
    currentRoute = route;
    // v118.33.5 NAV-IA Phase 5 · 进子项路由 · 自动展开所在折叠组(销项/进项)
    if (typeof window.expandNavGroupForRoute === 'function') {
        window.expandNavGroupForRoute(route);
    }
    // 切页
    document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
    const pageId = 'page-' + route;
    const pageEl = document.getElementById(pageId);
    if (pageEl) pageEl.classList.add('active');
    // 侧栏激活
    document.querySelectorAll('.nav-item').forEach((item) => {
        item.classList.toggle('active', (item as HTMLElement).dataset.route === route);
    });
    // URL hash
    if (location.hash !== '#/' + route) {
        history.replaceState(null, '', '#/' + route);
    }
    // 移动端收起侧栏
    if (window.innerWidth <= 768) document.body.classList.remove('sidebar-open');

    // 特殊页面加载:route → 页面加载函数名(window.* · 进路由即调,缺失则守卫跳过)。
    // 数据驱动表替原 if 链(同行为 · 腾 core-boot 空间)。各页加载器自身幂等/四态。
    const loader = ROUTE_LOADERS[route];
    const winFns = window as unknown as Record<string, () => void>;
    if (loader && typeof winFns[loader] === 'function') winFns[loader]();
}

// 重载当前路由(不切页/不改 hash)· 复用:① 初始 hash 兜底 ② 切账套后拉对应套账数据。
function reloadCurrentRoute(): void {
    const loader = ROUTE_LOADERS[currentRoute];
    const winFns = window as unknown as Record<string, () => void>;
    if (loader && typeof winFns[loader] === 'function') winFns[loader]();
}

function updateUploadHint() {
    if (!_quota) return;
    const _hintEl = document.getElementById('upload-hint');
    if (!_hintEl) return; // #page-ocr(上传识别页)已删 · 无此元素则跳过
    _hintEl.textContent = t('upload-hint', {
        pages: getMaxPagesPerFile(), // v111.2 · 用 plan limits
        mb: getMaxMbPerFile(), // v111.2 · 用 plan limits
        files: getMaxFiles(),
    });
}

// ============================================================
// 用户信息 + 配额 + 联系方式
// ============================================================
async function loadAll() {
    try {
        // 套账硬门:登录即盖屏(门的 loading 壳)· 不等下面一串 /api/me 等请求(手机端 1-3s)
        // 才弹门 → 否则系统 UI 先渲染、门后到 = 闪一下别的界面。超管布局(admin.html)不起门;
        // 新注册向导起来时会顶掉门壳(maybeAutoOnboard 里移除)。本会话已选过则 enforce 自放行。
        if (!window.PEARNLY_ADMIN_LAYOUT && typeof window.enforceWorkspaceGate === 'function')
            window.enforceWorkspaceGate();
        const [u, q, c, p] = await Promise.all([
            apiGet('/api/me'),
            apiGet('/api/ocr/quota'),
            fetch('/api/contact')
                .then((r) => r.json())
                .catch(() => null),
            // v111.2 · 启动时拉 plan limits · 让 getMaxFiles 立即可用
            apiGet('/api/me/plan').catch(() => null),
        ]);
        if (!u || !q) return;
        _userInfo = u;
        // B4 修 (2026-05-26) · 必须同步暴露到 window · workspace-switcher.js(bundle 模块)
        // 的 _isOwner() 读 window._userInfo 判 owner/员工。漏了它 → owner 被当成员工 →
        // 工作模式弹窗错显"你还没有被分配客户,请联系老板分配"(应显示"新建客户")。
        try {
            window._userInfo = u;
        } catch (_) {
            /* silent */
        }
        // POS PO-B1 · 用户就绪后重应用模块导航(owner 门控「开通收银台」引导项需 _userInfo)
        if (typeof window.applyModuleNav === 'function') window.applyModuleNav();

        // ============================================================
        // v118.44.0 · NAV-IA Phase 8 · admin layout 独立 SPA 早退分支
        // 当 admin.html 加载时设置 PEARNLY_ADMIN_LAYOUT=true · 此处填充全局态后立即 return
        // 不调任何 home 渲染函数 · 所有 UI 由 admin.js 接管
        // ============================================================
        if (window.PEARNLY_ADMIN_LAYOUT) {
            _quota = q;
            _contact = c;
            if (p) window._planState = p;
            window.PEARNLY_ADMIN_MODE = true;
            // 暴露 _userInfo 给 admin.js / 业务模块用
            try {
                window._userInfoForAdmin = u;
            } catch (_) {
                /* silent · window 属性赋值 */
            }
            return;
        }

        // ============================================================
        // v118.28.2 · 超管 /admin URL 独立(对齐 Stripe / Xero / QuickBooks)
        // 规则:
        //   - 普通用户 → 只能进 /home · 偷偷输 /admin 自动弹回
        //   - 超管 → 永远只看 /admin · 误进 /home 自动跳走
        // v118.44.0 · _isAdminPath 加 startsWith('/admin/')· 新 /admin/cost · /admin/users 也算 admin path
        // ============================================================
        try {
            const _isAdminPath =
                location.pathname === '/admin' || location.pathname.startsWith('/admin/');
            const _isSuper = !!u.is_super_admin;
            if (_isAdminPath && !_isSuper) {
                window.location.replace('/home');
                return;
            }
            if (!_isAdminPath && _isSuper) {
                // v118.44.0 · 超管默认跳新 admin layout(独立 SPA)· 不再跳 /admin(老 home.html 兜底)
                window.location.replace('/admin/cost');
                return;
            }
            window.PEARNLY_ADMIN_MODE = _isAdminPath;
            // REFACTOR-C1 · 老 home.html admin 布局(_isAdminPath 强制 #/admin-users)已下线 ·
            //   home.js 永不在 /admin* 加载(server: /admin/* → admin.html SPA)· _isAdminPath 恒 false ·
            //   仅保留上面「超管误进 /home → 弹回 /admin/cost」的活逻辑。
        } catch (_e) {
            window.PEARNLY_ADMIN_MODE = false;
        }

        _quota = q;
        _contact = c;
        if (p) window._planState = p;
        // v118.33.2 NAV-IA Phase 2 · renderSidebarUser 已删 · 头像菜单 renderAvatarMenu 接管(下面 Phase 1 块)
        // v0.15 · 顶部套餐下拉已删 · 不再设置 plan-current-label
        // v118.8 · 顶栏归属感 · 显示用户公司名(归属感 · 不再是 Pearnly 大字)
        window.renderBrandWorkspace();
        if (typeof window.renderInfoBar === 'function') window.renderInfoBar();
        if (typeof window.renderQuotaBanner === 'function') window.renderQuotaBanner(); // v102 · 配额低/耗尽顶部预警
        // v118.35.0.8 · renderTrialBanner 已废 · credits 系统接管
        if (typeof window.applySidebarVisibility === 'function') window.applySidebarVisibility();
        // NAV-IA Phase 1 · 头像菜单角色显隐 + 渲染(顶栏三件套)
        try {
            if (typeof applyRoleVisibility === 'function') applyRoleVisibility();
            if (typeof renderAvatarMenu === 'function') renderAvatarMenu(u);
        } catch (e) {
            console.error('[nav-ia phase1] render avatar menu', e);
        }
        updateUploadHint();
        // v110.7 · 检查是否需要弹欢迎向导(B 方案)
        try {
            if (typeof window.maybeShowOnboarding === 'function') window.maybeShowOnboarding(u);
        } catch (e) {
            console.error('onboarding init', e);
        }
        // v118.10 · 设置页表单数据预填充
        try {
            if (typeof window.fillSettingsForms === 'function') window.fillSettingsForms(u);
        } catch (e) {
            console.error('settings forms init', e);
        }
    } catch (e) {
        console.error(e);
    }
}

// REFACTOR-C1-home-batch9f · window 挂出
window.applyLang = applyLang;
window.routeTo = routeTo;
window.loadAll = loadAll;
window.updateUploadHint = updateUploadHint;

// ============================================================
// 启动
// ============================================================
// v118.44.0.5 · 顶层调用包 try-catch · 防 admin layout 下 applyLang/routeTo 抛错让后续 IIFE 不被注册
//   (现象:home.js L13585 applyLang null.classList → JS 引擎停止解析后续顶层语句 → admin-cost IIFE 不跑 → window.loadAdminCostPage 不存在)
try {
    applyLang(currentLang);
} catch (e) {
    console.warn('[boot] applyLang failed', e);
}

// LIFF 深链 resume(home.html preboot 据 sessionStorage 待处理项置)→ 由 purchase-liff.liffResume
// 独自驱动路由到对应单/待归类;core-boot 不抢默认路由,否则跳 dms-intake 通用页(backlog #5)。
const _liffResume = !!(window as unknown as { __LIFF_RESUME__?: boolean }).__LIFF_RESUME__;

// hash 路由初始化
try {
    if (!_liffResume) {
        const initialRoute = (location.hash || '#/dms-intake').replace(/^#\//, '');
        routeTo(VALID_ROUTES.includes(initialRoute) ? initialRoute : 'dms-intake');
    }
} catch (e) {
    console.warn('[boot] routeTo failed', e);
}

// LIFF 引导期(?liff=purchase 且尚无 token):整个 home 引导交给 purchase-liff —— 它签 token 后
// location.replace('/home') 重进走正常流。此处必须不跑 loadAll/路由加载,否则无 token 的
// /api/me 先 401 → 跳登录页,把还在异步鉴权的 LIFF 流踢走(套账门也在 loadAll 内,一并跳过)。
const _liffBootstrapping = !!window.__LIFF_BOOTSTRAP__; // home.html 早期置(?liff=purchase 且无 token)

// defer 模块的 loader 注册晚于此处同步执行 → 初始进非首屏路由会空白(只剩侧栏);
// 微任务后 sibling 已 eval,补调一次。原仅 reconcile 兜底,现泛化到所有路由。
if (!_liffBootstrapping && !_liffResume) setTimeout(reloadCurrentRoute, 0);

// 切账套(右上角切换器 / 表单「切换公司」)→ 重载当前模块。单一收口,替代原各页分散订阅。
window.addEventListener('pearnly:workspace-changed', reloadCurrentRoute);

if (!_liffBootstrapping) loadAll();
