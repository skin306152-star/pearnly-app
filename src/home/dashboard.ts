// ============================================================
// 首页(订阅与计费)数据装载 · 路由进 #/dashboard 时调。
//
// 2026-06-28 改版:dashboard 主体换成订阅与计费。本模块只管账户余额卡
// (loadCreditsCard · 复用 GET /api/me/credits),套餐/用量/账单由 subscription.ts
// (window.loadSubscription)负责。loadDashboard 串起两者;window.loadDashboard 名
// 保留(billing.ts 充值关闭后调它刷新余额)。
// ============================================================

function _t(k: string, fb?: string) {
    try {
        return typeof window.t === 'function' ? window.t(k) : fb;
    } catch (_) {
        return fb;
    }
}

async function loadDashboard() {
    loadCreditsCard();
    if (typeof window.loadSubscription === 'function') window.loadSubscription();
}
window.loadDashboard = loadDashboard;

// 账户余额卡 · 数据源 GET /api/me/credits
//   - is_billing_exempt → "∞" + 豁免
//   - is_owner 非豁免 → "฿X.XX"(<50 红字)+ 充值链接
//   - 员工(非 owner)→ 整张卡 + 充值按钮隐藏
async function loadCreditsCard() {
    const balCard = document.getElementById('dash-kpi-balance-card');
    const balVal = document.getElementById('dash-kpi-balance');
    const balSub = document.getElementById('dash-kpi-balance-sub');
    if (!balCard) return;
    const topupBtn = document.getElementById('dash-topup-btn');
    const showBalance = (on: boolean) => {
        balCard.style.display = on ? '' : 'none';
        if (topupBtn) topupBtn.style.display = on ? '' : 'none';
    };
    try {
        const auth = { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
        const resp = await fetch('/api/me/credits', { headers: auth, cache: 'no-store' });
        if (!resp.ok) {
            showBalance(false);
            return;
        }
        const data = await resp.json();
        const isOwner = !!data.is_owner;
        const isExempt = !!data.is_billing_exempt;

        if (!isOwner) {
            showBalance(false);
            return;
        }
        showBalance(true);
        if (isExempt) {
            if (balVal) {
                balVal.textContent = '∞';
                balVal.className = 'n dash-green';
            }
            if (balSub) {
                balSub.textContent =
                    typeof window.t === 'function'
                        ? window.t('dash-kpi-balance-exempt')
                        : 'Billing exempt';
            }
            return;
        }
        const bal = typeof data.balance_thb === 'number' ? data.balance_thb : 0;
        if (balVal) {
            // ฿ 与数字间垫窄空格 · 泰铢符号字形偏宽与首位数字贴撞
            balVal.textContent = '฿ ' + bal.toFixed(2);
            balVal.className = bal < 50 ? 'n dash-red' : 'n';
        }
        if (balSub) {
            const linkTxt =
                typeof window.t === 'function' ? window.t('dash-kpi-balance-topup') : 'Top up →';
            const linkColor = bal < 50 ? '#dc2626' : '#6b7280';
            const esc = (s: string) =>
                typeof window.escapeHtml === 'function'
                    ? window.escapeHtml(s)
                    : String(s).replace(
                          /[&<>"']/g,
                          (c) =>
                              ({
                                  '&': '&amp;',
                                  '<': '&lt;',
                                  '>': '&gt;',
                                  '"': '&quot;',
                                  "'": '&#39;',
                              })[c as '&' | '<' | '>' | '"' | "'"]
                      );
            balSub.innerHTML =
                '<a href="#" id="kpi-balance-topup-link" style="color:' +
                linkColor +
                ';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">' +
                esc(linkTxt) +
                '</a>';
        }
    } catch (e) {
        showBalance(false);
    }
}
window.loadCreditsCard = loadCreditsCard;

// 启动时若 hash 落在 #/dashboard,也跑一次(loadAll 后)
document.addEventListener('DOMContentLoaded', function () {
    if ((location.hash || '').replace(/^#\//, '') === 'dashboard') {
        setTimeout(loadDashboard, 500);
    }
});
// 4 语切换重渲染
if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('dashboard', function () {
        if ((location.hash || '').replace(/^#\//, '') === 'dashboard') loadDashboard();
    });
}
