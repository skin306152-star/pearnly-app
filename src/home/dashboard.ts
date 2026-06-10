// ============================================================
// REFACTOR-A1.3 (2026-05-22) · 改 ES module · 不再 IIFE
//
// 原 v118.32.5.5.16 · 首页 dashboard 加载逻辑
// 路由进 #/dashboard 时调 · 不动后端 · 复用 /api/me/tenant-usage + /api/history
//
// 文件搬迁:
//   旧 static/home/dashboard.js(IIFE · script src 加载)
//   新 src/home/dashboard.js(ES module · Vite bundle 到 static/dist/main.js)
//
// 加载顺序:home.html 里 <script src=home.js> 同步执行后,
//          <script type=module src=/static/dist/main.js> defer 自动后跑
//          所以 home.js 提供的全局(t / escapeHtml / subscribeI18n / _openTopupModal)
//          在本 module 执行时一定已就绪
// ============================================================

function _t(k: string, fb?: string) {
    try {
        return typeof window.t === 'function' ? window.t(k) : fb;
    } catch (_) {
        return fb;
    }
}
function _fmtNum(n: number) {
    if (n == null || isNaN(n)) return '0';
    try {
        return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    } catch (_) {
        return String(n);
    }
}
function _ago(iso: string) {
    if (!iso) return '';
    try {
        const t = new Date(iso).getTime();
        if (!t) return '';
        const s = Math.floor((Date.now() - t) / 1000);
        if (s < 60) return _t('time-just-now', '刚刚');
        if (s < 3600) return Math.floor(s / 60) + _t('time-min-ago-suffix', ' 分钟前')!;
        if (s < 86400) return Math.floor(s / 3600) + _t('time-hour-ago-suffix', ' 小时前')!;
        return Math.floor(s / 86400) + _t('time-day-ago-suffix', ' 天前')!;
    } catch (_) {
        return '';
    }
}
async function loadDashboard() {
    // v118.35.0.9 · 第二排 credits KPI · 余额 + 用量
    loadCreditsCard();
    const elInv = document.getElementById('dash-kpi-invoices');
    const elPend = document.getElementById('dash-kpi-pending');
    const elExc = document.getElementById('dash-kpi-exceptions');
    const elPlan = document.getElementById('dash-kpi-plan');
    const elPlanSub = document.getElementById('dash-kpi-plan-sub');
    const elList = document.getElementById('dash-recent-list');
    const elExcBadge = document.getElementById('dash-quick-exc-badge');
    // 1. 拿 plan + 最近识别(并行 · 已有 endpoint · 不动后端)
    try {
        const auth = { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
        // 修正: /api/me/plan 不存在 → 用 /api/me/tenant-usage + /api/history
        const [usage, recent, excStats] = await Promise.all([
            fetch('/api/me/tenant-usage', { headers: auth })
                .then((r) => (r.ok ? r.json() : null))
                .catch(() => null),
            fetch('/api/history?limit=20', { headers: auth })
                .then((r) => (r.ok ? r.json() : null))
                .catch(() => null),
            fetch('/api/exceptions/stats?status=pending', { headers: auth })
                .then((r) => (r.ok ? r.json() : null))
                .catch(() => null),
        ]);
        // 本月发票 = tenant-usage 里的 ocr_this_month
        const mInv = (usage && usage.ocr_this_month) || 0;
        // 待处理 = 最近历史里 pending/reviewing 状态
        let pending = 0;
        const rows = (recent && (recent.items || recent.history || recent)) || [];
        const list = Array.isArray(rows) ? rows : [];
        list.forEach((r) => {
            if (r.status === 'pending' || r.status === 'reviewing') pending++;
        });
        // 异常 = exceptions/stats
        const excCount =
            (excStats && (excStats.total || excStats.count || excStats.pending || 0)) || 0;
        if (elInv) elInv.textContent = _fmtNum(mInv);
        if (elPend) elPend.textContent = _fmtNum(pending);
        if (elExc) elExc.textContent = _fmtNum(excCount);
        if (elExcBadge) {
            if (excCount > 0) {
                elExcBadge.style.display = '';
                elExcBadge.textContent = excCount;
            } else {
                elExcBadge.style.display = 'none';
            }
        }
        // 配额显示 · 来自 tenant-usage
        if (elPlan && usage) {
            const used = usage.ocr_this_month || 0;
            const quota = usage.quota || 0;
            elPlan.textContent = _fmtNum(used);
            if (elPlanSub) {
                elPlanSub.textContent = quota
                    ? used + ' / ' + _fmtNum(quota) + ' 张'
                    : _t('dash-kpi-plan-sub', '本月用量')!;
            }
        }
        // 最近 5 条
        if (elList) {
            if (list.length === 0) {
                elList.innerHTML =
                    '<div class="empty"><div class="t">' +
                    _t('dash-recent-empty', '还没有识别记录 · 去上传第一张吧') +
                    '</div></div>';
            } else {
                const html = list
                    .slice(0, 5)
                    .map((r) => {
                        const key = (r.invoice_no || r.filename || r.id || '').toString();
                        const mid = (
                            r.supplier_name ||
                            r.buyer_name ||
                            r.client_name ||
                            r.notes ||
                            ''
                        ).toString();
                        const t = _ago(r.created_at || r.upload_time || r.date);
                        const esc = (s: string) =>
                            String(s).replace(
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
                        return (
                            '<div class="act"><div class="th"><svg class="ic" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>' +
                            '<div style="min-width:0"><div class="nm" title="' +
                            esc(mid || key) +
                            '">' +
                            esc(mid || key) +
                            '</div><div class="mt" title="' +
                            esc(key) +
                            '">' +
                            esc(key ? key + ' · ' : '') +
                            esc(t!) +
                            '</div></div></div>'
                        );
                    })
                    .join('');
                elList.innerHTML = html;
            }
        }
    } catch (e) {
        // 失败静默 · 显示 — · 不打扰用户
        if (elList)
            elList.innerHTML =
                '<div class="empty"><div class="t">' +
                _t('dash-recent-empty', '还没有识别记录 · 去上传第一张吧') +
                '</div></div>';
    }
}
window.loadDashboard = loadDashboard;

// v118.35.0.9 · credits 余额 + 用量 KPI 卡渲染
// 数据源: GET /api/me/credits
// 卡 1 余额:
//   - is_billing_exempt=true → "∞" + "豁免账号"
//   - is_owner=true · 非豁免 → "฿X.XX" · 余额 < 50 红字 + "充值 →" 链接
//   - is_owner=false (员工) → 整张卡 display:none
// 卡 2 用量:
//   - 所有人显示
//   - pages_this_month < 200 → "X" + "{used}/200 张 · ฿1.50/张"
//   - pages_this_month >= 200 → "X" + "{used} 张 · ฿0.75/张"
async function loadCreditsCard() {
    const balCard = document.getElementById('dash-kpi-balance-card');
    const usageCard = document.getElementById('dash-kpi-usage-card');
    const balVal = document.getElementById('dash-kpi-balance');
    const balSub = document.getElementById('dash-kpi-balance-sub');
    const usageVal = document.getElementById('dash-kpi-usage');
    const usageSub = document.getElementById('dash-kpi-usage-sub');
    if (!balCard || !usageCard) return;
    // 充值按钮与余额卡同生死 · 卡隐藏时按钮单飘在信息带顶上
    const topupBtn = document.getElementById('dash-topup-btn');
    const showBalance = (on: boolean) => {
        balCard.style.display = on ? '' : 'none';
        if (topupBtn) topupBtn.style.display = on ? '' : 'none';
    };
    try {
        const auth = { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
        const resp = await fetch('/api/me/credits', { headers: auth, cache: 'no-store' });
        if (!resp.ok) {
            // 鉴权失败或服务异常 · 默认隐藏余额 · 用量显示 "—"
            showBalance(false);
            if (usageVal) usageVal.textContent = '—';
            if (usageSub) usageSub.textContent = '';
            return;
        }
        const data = await resp.json();
        const isOwner = !!data.is_owner;
        const isExempt = !!data.is_billing_exempt;

        // === 卡 1 · 账户余额 ===
        if (!isOwner) {
            showBalance(false);
        } else {
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
            } else {
                const bal = typeof data.balance_thb === 'number' ? data.balance_thb : 0;
                if (balVal) {
                    // ฿ 与数字之间垫窄空格 · 泰铢符号字形偏宽与首位数字贴撞(S8)
                    balVal.textContent = '฿ ' + bal.toFixed(2);
                    balVal.className = bal < 50 ? 'n dash-red' : 'n';
                }
                if (balSub) {
                    // v118.35.0.24 · 充值入口永远显示(老逻辑只在 <50 时显示 · 转化率低)
                    // 低余额红色高亮 · 正常余额灰色低调
                    const linkTxt =
                        typeof window.t === 'function'
                            ? window.t('dash-kpi-balance-topup')
                            : 'Top up →';
                    const linkColor = bal < 50 ? '#dc2626' : '#6b7280';
                    // ES module 不再依赖 IIFE 外的 escapeHtml 词法引用 · 显式走 window.escapeHtml
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
            }
        }

        // === 卡 2 · 本月用量(所有人显示) ===
        const pages =
            typeof data.pages_this_month === 'number'
                ? data.pages_this_month
                : typeof data.my_invoice_count === 'number'
                  ? data.my_invoice_count
                  : 0;
        usageCard.style.display = '';
        if (usageVal) usageVal.textContent = String(pages);
        if (usageSub) {
            const key = pages >= 200 ? 'dash-kpi-usage-sub-high' : 'dash-kpi-usage-sub-low';
            const tpl =
                typeof window.t === 'function' ? window.t(key, { used: pages }) : pages + ' pages';
            usageSub.textContent = tpl;
        }
    } catch (e) {
        console.warn('[credits] loadCreditsCard failed:', e);
        showBalance(false);
        if (usageVal) usageVal.textContent = '—';
    }
}
window.loadCreditsCard = loadCreditsCard;

// 启动时若 hash 落在 #/dashboard,也跑一次(loadAll 后)
document.addEventListener('DOMContentLoaded', function () {
    if ((location.hash || '').replace(/^#\//, '') === 'dashboard') {
        setTimeout(loadDashboard, 500);
    }
});
// 4 语切换重渲染(refresh tooltip + empty state 文案)
if (typeof window.subscribeI18n === 'function') {
    window.subscribeI18n('dashboard', function () {
        if ((location.hash || '').replace(/^#\//, '') === 'dashboard') loadDashboard();
    });
}
