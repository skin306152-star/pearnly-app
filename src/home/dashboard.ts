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
    // 余额卡整张随 owner 显隐(员工看不到余额)· 充值入口=卡内 #dash-kpi-balance-sub 的「充值 →」链接
    const showBalance = (on: boolean) => {
        balCard.style.display = on ? '' : 'none';
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
        const foot = document.getElementById('dash-kpi-balance-foot');
        if (isExempt) {
            if (balVal) {
                balVal.textContent = '∞';
                balVal.className = 'n sub-card-n dash-green';
            }
            if (balSub) {
                balSub.textContent = _t('dash-kpi-balance-exempt', 'Billing exempt') as string;
            }
            if (foot) foot.style.display = 'none'; // 豁免账号无需充值
            return;
        }
        const bal = typeof data.balance_thb === 'number' ? data.balance_thb : 0;
        const low = bal < 50;
        if (balVal) {
            // ฿ 与数字间垫窄空格 · 泰铢符号字形偏宽与首位数字贴撞
            balVal.textContent = '฿ ' + bal.toFixed(2);
            balVal.className = 'n sub-card-n' + (low ? ' dash-red' : '');
        }
        // 副标题固定说明用途(对齐设计稿);低余额提示 + 去充值钮在卡底 footer。
        if (balSub)
            balSub.textContent = _t('dash-balance-use', '用于超额扣费 · 按量计费') as string;
        if (foot) {
            foot.style.display = '';
            const hint = foot.querySelector('.sub-foot-hint') as HTMLElement | null;
            if (hint) hint.style.visibility = low ? 'visible' : 'hidden'; // 仅低余额示警
            const btn = document.getElementById('dash-topup-btn') as HTMLButtonElement | null;
            if (btn)
                btn.onclick = () => {
                    if (typeof window._openTopupModal === 'function') window._openTopupModal();
                };
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
