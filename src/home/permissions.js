/* REFACTOR-C1-home-batch8 · 用户角色原子判断(全局唯一来源)
 * 从 home.js verbatim 抽出(0 逻辑改):isSuperAdmin / isOwner / isEmployee /
 * isTrial / isLifetime / shouldHideMoney / canManageTeam / canManageApiKey
 * + isMoneyHidden 兼容别名。
 *
 * 所有 UI 显隐 / 权限判断都基于这几个原子函数 · 不再散落写 if (role==='xxx')。
 * 参数 u 默认用 _userInfo(config 全局 · 只读)· 可传别人(超管查别人时用)。
 * 被 layout.js(applySidebarVisibility/renderInfoBar)+ topbar-avatar /
 * settings-core 等模块 + home.js 裸调 → 全部 window.X=X 挂出供运行期全局作用域解析。
 * 全部纯函数 · 调用点都在函数 / handler 内 · 无引导期裸调风险。
 */

function isSuperAdmin(u) {
    u = u || _userInfo;
    return !!(u && u.is_super_admin);
}
function isOwner(u) {
    u = u || _userInfo;
    return !!u && (u.role === 'owner' || isSuperAdmin(u));
}
function isEmployee(u) {
    u = u || _userInfo;
    return !!u && u.role === 'member' && !isSuperAdmin(u);
}
function isTrial(u) {
    u = u || _userInfo;
    return !!u && (u.effective_plan === 'trial' || u.plan === 'trial') && !isSuperAdmin(u);
}
function isLifetime(u) {
    u = u || _userInfo;
    return !!u && u.tenant_type === 'byo_api';
}
// 钱相关 UI 是否应该隐藏(员工就该看不到)· 这是核心铁律 · v118.12 主菜
function shouldHideMoney(u) {
    return isEmployee(u);
}
function canManageTeam(u) {
    return isOwner(u);
}
function canManageApiKey(u) {
    return isOwner(u) && isLifetime(u);
}

// 兼容旧代码 · 老的 isMoneyHidden 别处可能用 · 保留别名
window.isMoneyHidden = shouldHideMoney;

// ── window 桥(home.js + layout.js + 其它模块裸调时全局作用域解析)──
window.isSuperAdmin = isSuperAdmin;
window.isOwner = isOwner;
window.isEmployee = isEmployee;
window.isTrial = isTrial;
window.isLifetime = isLifetime;
window.shouldHideMoney = shouldHideMoney;
window.canManageTeam = canManageTeam;
window.canManageApiKey = canManageApiKey;
