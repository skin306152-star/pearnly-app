// 列表面「这次没取回来」的统一脸。
//
// 为什么单独一份:后端 500 被渲染成空态是本仓反复犯的同一个错(识别记录 → 对账中心
// 「最近对账」→ 客户管理「买方客户」,三个月里三次)。空态那句话说的是「你还没有」,
// 用户读完的结论是自己的票/客户/记录没了,于是去查数据而不是重试 —— 状态诚实红线。
// 错误态必须同时给三样:说这是取数失败、说数据还在、给一条重试的出路。
//
// 脸走共享设计系统 static/pearnly-ui.css 的 .pu-error/.pu-btn(静态 HTML 版先例在
// page-history.ts),四处列表面共用本函数,不各写一套。
/* global t, escapeHtml */

const ERR_ICON =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5h.01"/></svg>';

// titleKey 按面给(「没能加载对账记录」比「加载失败」更能让人判断该不该慌);
// retryAttr 是调用方事件委托认的那个 data-* 属性名,由调用方绑重试。
export function listErrorHtml(titleKey: string, retryAttr: string): string {
    return (
        '<div class="pu-error" data-state="error">' +
        `<span class="pu-error__icon" aria-hidden="true">${ERR_ICON}</span>` +
        `<div class="pu-error__title">${escapeHtml(t(titleKey))}</div>` +
        `<p class="pu-error__msg">${escapeHtml(t('list-error-desc'))}</p>` +
        `<button type="button" class="pu-btn pu-btn--primary" ${retryAttr}="1">` +
        `${escapeHtml(t('list-retry'))}</button>` +
        '</div>'
    );
}
