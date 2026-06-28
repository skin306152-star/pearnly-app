// ============================================================
// 订阅与计费 · 首页主体(2026-06-28)
//
// 数据源 GET /api/me/subscription(当前订阅 + 套餐目录 + 余额)+ 账单走
// GET /api/credits/usage-history。订阅/取消走 POST /api/subscription/{subscribe,cancel}。
// 渲染:当前套餐摘要 #sub-summary · 套餐卡 #sub-plans · 最近账单 #sub-records。
// window.loadSubscription 由 dashboard.ts 的 loadDashboard 触发。
// ============================================================

interface SubPlan {
    code: string;
    quota: number;
    fee: number;
    over_rate: number;
}
interface SubState {
    plan_code: string;
    status: string;
    quota: number;
    over_rate: number;
    monthly_fee: number;
    pages_used_this_cycle: number;
    remaining: number;
    auto_renew: boolean;
    cycle_end: string | null;
}

let _plans: SubPlan[] = [];

// 当前套餐卡图标(Lucide crown)· 与账户余额卡的钱包图标对称。
const _CROWN =
    '<svg class="ic" viewBox="0 0 24 24"><path d="M11.562 3.266a.5.5 0 0 1 .876 0L15.39 8.87a1 1 0 0 0 1.516.294L21.183 5.5a.5.5 0 0 1 .798.519l-2.834 10.246a1 1 0 0 1-.956.734H5.81a1 1 0 0 1-.957-.734L2.02 6.02a.5.5 0 0 1 .798-.519l4.276 3.664a1 1 0 0 0 1.516-.294z"/><path d="M5 21h14"/></svg>';

function _t(k: string, fb?: string): string {
    try {
        return (typeof window.t === 'function' ? window.t(k) : fb) || fb || k;
    } catch (_) {
        return fb || k;
    }
}
function _auth() {
    return { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
}
function _money(n: number): string {
    return '฿ ' + Number(n || 0).toFixed(2);
}
function _esc(s: unknown): string {
    return typeof window.escapeHtml === 'function'
        ? window.escapeHtml(s)
        : String(s == null ? '' : s).replace(
              /[&<>"']/g,
              (c) =>
                  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[
                      c as '&' | '<' | '>' | '"' | "'"
                  ]
          );
}
function _toast(msg: string, type?: string) {
    if (typeof window.showToast === 'function') window.showToast(msg, type);
}
function _fmtDate(iso: string | null): string {
    if (!iso) return '';
    try {
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '';
        const p = (n: number) => String(n).padStart(2, '0');
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
    } catch (_) {
        return '';
    }
}

async function loadSubscription() {
    let data: { plans?: SubPlan[]; subscription?: SubState | null } | null = null;
    try {
        const resp = await fetch('/api/me/subscription', { headers: _auth(), cache: 'no-store' });
        if (resp.ok) data = await resp.json();
    } catch (_) {
        /* 静默 · 下方渲染空态 */
    }
    _plans = (data && data.plans) || [];
    renderSummary((data && data.subscription) || null);
    renderPlans((data && data.subscription) || null);
    loadRecords();
}
window.loadSubscription = loadSubscription;

function renderSummary(sub: SubState | null) {
    const el = document.getElementById('sub-summary');
    if (!el) return;
    if (!sub) {
        el.innerHTML =
            '<div class="sub-card-ico">' +
            _CROWN +
            '</div><div class="sub-card-bd">' +
            '<div class="sub-card-l">' +
            _esc(_t('sub-current', '当前套餐')) +
            '</div><div class="sub-card-n">' +
            _esc(_t('sub-none', '未订阅')) +
            '</div><div class="sub-card-hint">' +
            _esc(_t('sub-none-sub', '当前按量计费 · 订阅套餐更省 · 在下方选择套餐')) +
            '</div><a class="sub-link" id="sub-jump-plans">' +
            _esc(_t('sub-view-plans', '查看套餐 →')) +
            '</a></div>';
        bindJumpPlans();
        return;
    }
    const used = sub.pages_used_this_cycle || 0;
    const quota = sub.quota || 0;
    const remaining = Math.max(0, quota - used);
    const pct = quota ? Math.min(100, Math.round((used / quota) * 100)) : 0;
    const sheet = _esc(_t('sub-sheet', '张'));
    const cancelledNote =
        sub.status === 'cancelled'
            ? '<div class="sub-note">' +
              _esc(_t('sub-cancelled-note', '已取消 · 当前周期额度可用到到期')) +
              '</div>'
            : '';
    el.innerHTML =
        '<div class="sub-card-ico">' +
        _CROWN +
        '</div><div class="sub-card-bd">' +
        '<div class="sub-card-l">' +
        _esc(_t('sub-current', '当前套餐')) +
        '</div><div class="sub-card-n">Package ' +
        _esc(sub.plan_code) +
        '</div><div class="sub-card-hint">' +
        _esc(_t('sub-over-rate', '超额单价')) +
        ' ' +
        _money(sub.over_rate) +
        '/' +
        sheet +
        ' · ' +
        _esc(_t('sub-cycle-ends', '周期至')) +
        ' ' +
        _esc(_fmtDate(sub.cycle_end)) +
        '</div>' +
        '<div class="sub-prog"><span style="width:' +
        pct +
        '%"></span></div>' +
        '<div class="sub-usage-line">' +
        _esc(_t('sub-used-this-cycle', '本周期已用')) +
        ' <b>' +
        used +
        '</b> / ' +
        quota +
        ' ' +
        sheet +
        ' · ' +
        _esc(_t('sub-remaining', '剩余')) +
        ' <b>' +
        remaining +
        '</b></div>' +
        cancelledNote +
        '<a class="sub-link sub-link-danger" id="sub-cancel-btn">' +
        _esc(_t('sub-cancel', '取消订阅')) +
        '</a></div>';
    const cb = document.getElementById('sub-cancel-btn');
    if (cb) (cb as HTMLAnchorElement).onclick = onCancel;
}

function bindJumpPlans() {
    const j = document.getElementById('sub-jump-plans');
    if (j)
        j.onclick = () => {
            const p = document.getElementById('sub-plans');
            if (p) p.scrollIntoView({ behavior: 'smooth', block: 'center' });
        };
}

function renderPlans(sub: SubState | null) {
    const el = document.getElementById('sub-plans');
    if (!el) return;
    if (!_plans.length) {
        el.innerHTML = '';
        return;
    }
    const sheet = _esc(_t('sub-sheet', '张'));
    const perMonth = _esc(_t('sub-per-month', '月'));
    el.innerHTML = _plans
        .map((p) => {
            const isCur = !!sub && sub.plan_code === p.code;
            const btnTxt = isCur
                ? _t('sub-current-plan', '当前套餐')
                : sub
                  ? _t('sub-change', '切换到此套餐')
                  : _t('sub-subscribe', '订阅此套餐');
            return (
                '<div class="sub-plan' +
                (isCur ? ' cur' : '') +
                '"><div class="sub-plan-top"><span class="sub-plan-letter">' +
                _esc(p.code) +
                '</span><div><div class="sub-plan-name">Package ' +
                _esc(p.code) +
                '</div><div class="sub-plan-price">' +
                Number(p.fee).toFixed(0) +
                '<span>฿/' +
                perMonth +
                '</span></div></div></div>' +
                '<ul class="sub-plan-feats"><li>' +
                _esc(_t('sub-feat-quota', '每月额度')) +
                ' ' +
                p.quota +
                ' ' +
                sheet +
                '</li><li>' +
                _esc(_t('sub-feat-over', '超额')) +
                ' ' +
                _money(p.over_rate) +
                '/' +
                sheet +
                '</li></ul>' +
                '<button class="btn ' +
                (isCur ? '' : 'pri') +
                ' sub-plan-btn" data-plan="' +
                _esc(p.code) +
                '"' +
                (isCur ? ' disabled' : '') +
                '>' +
                _esc(btnTxt) +
                '</button></div>'
            );
        })
        .join('');
    el.querySelectorAll('.sub-plan-btn[data-plan]').forEach((b) => {
        const btn = b as HTMLButtonElement;
        if (btn.disabled) return;
        btn.onclick = () => onSubscribe(btn.getAttribute('data-plan') || '');
    });
}

async function onSubscribe(code: string) {
    const plan = _plans.find((p) => p.code === code);
    if (!plan) return;
    const msg =
        _t('sub-confirm', '确认订阅') +
        ' Package ' +
        code +
        ' · ' +
        _money(plan.fee) +
        '/' +
        _t('sub-per-month', '月') +
        '?';
    const ok =
        typeof window.showConfirm === 'function'
            ? await window.showConfirm(msg)
            : window.confirm(msg);
    if (!ok) return;
    try {
        const resp = await fetch('/api/subscription/subscribe', {
            method: 'POST',
            headers: { ..._auth(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan_code: code }),
        });
        if (resp.ok) {
            _toast(_t('sub-subscribed', '订阅成功'));
            loadSubscription();
            if (typeof window.loadDashboard === 'function') window.loadDashboard();
            return;
        }
        if (resp.status === 402) {
            _toast(_t('sub-insufficient', '余额不足 · 请先充值'), 'error');
            if (typeof window._openTopupModal === 'function') window._openTopupModal();
            return;
        }
        _toast(_t('sub-failed', '订阅失败 · 请稍后再试'), 'error');
    } catch (_) {
        _toast(_t('sub-failed', '订阅失败 · 请稍后再试'), 'error');
    }
}

async function onCancel() {
    const msg = _t('sub-cancel-confirm', '确认取消订阅?当前周期额度仍可用到到期,之后不再续订。');
    const ok =
        typeof window.showConfirm === 'function'
            ? await window.showConfirm(msg, { danger: true })
            : window.confirm(msg);
    if (!ok) return;
    try {
        const resp = await fetch('/api/subscription/cancel', { method: 'POST', headers: _auth() });
        if (resp.ok) {
            _toast(_t('sub-cancelled', '已取消订阅'));
            loadSubscription();
        } else {
            _toast(_t('sub-failed', '操作失败 · 请稍后再试'), 'error');
        }
    } catch (_) {
        _toast(_t('sub-failed', '操作失败 · 请稍后再试'), 'error');
    }
}

interface BillRow {
    date: string | null;
    type: string;
    description: string;
    filename: string;
    pages: number;
    cost_thb: number;
}

async function loadRecords() {
    const el = document.getElementById('sub-records');
    if (!el) return;
    let rows: BillRow[] = [];
    try {
        const resp = await fetch('/api/credits/usage-history?per_page=8', {
            headers: _auth(),
            cache: 'no-store',
        });
        if (resp.ok) {
            const data = await resp.json();
            rows = (data && data.rows) || [];
        }
    } catch (_) {
        /* 静默 · 渲染空态 */
    }
    if (!rows.length) {
        el.innerHTML =
            '<div class="empty"><div class="t">' +
            _esc(_t('sub-records-empty', '暂无账单记录')) +
            '</div></div>';
        return;
    }
    el.innerHTML = rows.map(recordRow).join('');
}

function recordRow(r: BillRow): string {
    const isSub = r.type === 'subscription';
    let desc: string;
    if (isSub) {
        desc = r.description || _t('sub-rec-subscription', '订阅月费');
    } else {
        desc =
            r.filename ||
            (r.pages ? r.pages + ' ' + _t('sub-sheet', '张') : _t('sub-rec-scan', '扫描扣费'));
    }
    const cost = Number(r.cost_thb || 0);
    const free = !isSub && cost === 0;
    const amtTxt = free ? _t('sub-rec-free', '套餐内 · 免费') : _money(Math.abs(cost));
    return (
        '<div class="sub-rec"><div class="sub-rec-main"><div class="sub-rec-desc" title="' +
        _esc(desc) +
        '">' +
        _esc(desc) +
        '</div><div class="sub-rec-time">' +
        _esc(_fmtDate(r.date)) +
        '</div></div><div class="sub-rec-amt' +
        (free ? ' free' : '') +
        '">' +
        _esc(amtTxt) +
        '</div></div>'
    );
}
