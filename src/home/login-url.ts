// 登录口单一事实源:退出/踢session/401 等任何要跳"重新登录"的地方都读这一处,
// 不各自写死 /login——POS 独立入口(pos_only)必须落回 /pos,写死 /login 会把
// 收银商户甩去主站猫登录页(2026-07-11 Zihao 真机报障根因:两处退出各自实现分叉)。
export function loginUrl(): string {
    return window._businessType === 'pos_only' ? '/pos' : '/login';
}

window.loginUrl = loginUrl;
