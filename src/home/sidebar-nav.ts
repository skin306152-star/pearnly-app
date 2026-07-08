// REFACTOR-C1-home-batch9g1 · 从 home.js verbatim 抽出(0 逻辑改)
// 侧栏折叠/汉堡/遮罩 + hashchange 路由 + nav-item 点击(routeTo 经 window 延迟解析)
/* global routeTo */

// ============================================================
// 侧栏 + 路由
// ============================================================
const SIDEBAR_COLLAPSED_KEY = 'mrpilot_sidebar_collapsed';
if (localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1') {
    document.body.classList.add('sidebar-collapsed');
}
document.getElementById('sidebar-toggle')!.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
        document.body.classList.toggle('sidebar-open');
    } else {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem(
            SIDEBAR_COLLAPSED_KEY,
            document.body.classList.contains('sidebar-collapsed') ? '1' : '0'
        );
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
    const r = (location.hash || '#/dms-intake').replace(/^#\//, '');
    routeTo(r);
});

document.querySelectorAll<HTMLElement>('.nav-item').forEach((item) => {
    item.addEventListener('click', () => {
        // v0.15 · 「即将」菜单项(data-locked="1")给 toast · 不切路由
        if (item.dataset.locked === '1') {
            showToast(t('feature-coming-soon'), 'info');
            return;
        }
        // POS · 跨 SPA 入口(切到收银台 → 独立 /pos · 整页跳转,非 hash 路由)
        // 先清设备绑定(pos_store_*),否则 /pos 优先认旧设备绑定,盖过老板当前选的套账。
        if (item.dataset.href) {
            if (item.id === 'nav-pos-switch') {
                try {
                    localStorage.removeItem('pos_store_token');
                    localStorage.removeItem('pos_store_ws');
                    localStorage.removeItem('pos_store_name');
                    localStorage.removeItem('pos_store_addr');
                } catch (_) {
                    /* no-op */
                }
            }
            window.location.href = item.dataset.href;
            return;
        }
        routeTo(item.dataset.route!);
    });
});

// v118.33.7.3 · sidebar-cta-upload 已删 · 对齐 prototype_final(prototype sidebar 无 CTA)
