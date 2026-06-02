// ============================================================
// REFACTOR-WB-modularize · 引导期 UI 助手(顶栏工作台名 + 断网横幅)从 core-boot.js 拆出
//
// renderBrandWorkspace(loadAll/settings-core 调)· installNetworkBanner(misc-bindings 调)。
// 均 window 桥暴露 · 与核心编排(applyLang/routeTo/loadAll)解耦。
// ============================================================
/* global svgIcon, escapeHtml */
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

// v92 · Bug 7 · 断网横幅初始化
function installNetworkBanner() {
    let banner = document.getElementById('offline-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'offline-banner';
        banner.className = 'offline-banner';
        banner.style.display = 'none';
        document.body.insertBefore(banner, document.body.firstChild);
    }
    function updateBanner() {
        if (navigator.onLine === false) {
            banner.innerHTML =
                svgIcon('wifiOff', 14) + '<span>' + escapeHtml(t('offline-banner')) + '</span>';
            banner.classList.remove('is-online');
            banner.classList.add('is-offline');
            banner.style.display = 'flex';
        } else {
            // 先展示"已恢复" 2 秒 · 再隐藏
            if (banner.classList.contains('is-offline')) {
                banner.innerHTML =
                    svgIcon('wifiOn', 14) +
                    '<span>' +
                    escapeHtml(t('online-reconnected')) +
                    '</span>';
                banner.classList.remove('is-offline');
                banner.classList.add('is-online');
                setTimeout(() => {
                    banner.style.display = 'none';
                    banner.classList.remove('is-online');
                }, 2000);
            } else {
                banner.style.display = 'none';
            }
        }
    }
    window.addEventListener('online', updateBanner);
    window.addEventListener('offline', updateBanner);
    updateBanner(); // 页面加载时立即检查
}

window.renderBrandWorkspace = renderBrandWorkspace;
window.installNetworkBanner = installNetworkBanner;
