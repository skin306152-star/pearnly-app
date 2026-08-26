// 登录口单一事实源:退出/踢session/401 等任何要跳"重新登录"的地方都读这一处,
// 不各自写死 /login——POS 独立入口(pos_only)必须落回 /pos,写死 /login 会把
// 收银商户甩去主站猫登录页(2026-07-11 Zihao 真机报障根因:两处退出各自实现分叉)。
// 2026-07-12 改判据:壳跟登录入口走(_entry),业态标签退居无入口记号时的老会话回落
// (landing.js/pos-login.html 登录成功写 pearnly_entry,module-nav.apply 每次登录后同步 window._entry)。
// 2026-07-13 冷启动回落:module-nav.apply 只在鉴权成功后才 seed window._entry,冷进入/
// 会话过期 401 直跳时 _entry 尚空 → 此处自读入口记号。
// 2026-08-26 定版(主控拍板):/cowork /erp 未登录直接呈现同一套登录 UI(浏览器地址就是 /cowork|/erp,
// 不再露 /login?entry=)。故 cowork/main 一律落 /cowork,erp 落 /erp,其它独立门回各自登录页。
// 改此分支必须同步 home.html 头部 preboot 门 + static/landing/landing.js(两处都是物理拷贝,
// preboot 早于 main.js 调不到这里)。
export function loginUrl(): string {
    if (!window._entry) window._entry = localStorage.getItem('pearnly_entry') || '';
    if (window._entry === 'pos') return '/pos';
    if (window._entry === 'dms') return '/dms';
    if (window._entry === 'ai') return '/ai';
    if (window._entry === 'daily') return '/daily';
    if (window._entry === 'erp') return '/erp';
    if (window._entry === 'cowork') return '/cowork';
    if (window._entry === 'main') return '/cowork'; // 默认主壳(普通默认用户 canonical=/cowork)
    return window._businessType === 'pos_only' ? '/pos' : '/cowork';
}

window.loginUrl = loginUrl;
