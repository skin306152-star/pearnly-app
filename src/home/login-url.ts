// 登录口单一事实源:退出/踢session/401 等任何要跳"重新登录"的地方都读这一处,
// 不各自写死 /login——POS 独立入口(pos_only)必须落回 /pos,写死 /login 会把
// 收银商户甩去主站猫登录页(2026-07-11 Zihao 真机报障根因:两处退出各自实现分叉)。
// 2026-07-12 改判据:壳跟登录入口走(_entry),业态标签退居无入口记号时的老会话回落
// (landing.js/pos-login.html 登录成功写 pearnly_entry,module-nav.apply 每次登录后同步 window._entry)。
// 2026-07-13 冷启动回落:module-nav.apply 只在鉴权成功后才 seed window._entry,冷进入/
// 会话过期 401 直跳时 _entry 尚空 → 此处自读入口记号。注意:新增 entry 分支须同步 home.html:9 preboot 门(物理拷贝,它跑在 main.js 之前调不到这里)。
export function loginUrl(): string {
    if (!window._entry) window._entry = localStorage.getItem('pearnly_entry') || '';
    if (window._entry === 'pos') return '/pos';
    if (window._entry === 'main') return '/login';
    return window._businessType === 'pos_only' ? '/pos' : '/login';
}

window.loginUrl = loginUrl;
