// ============================================================
// 首页 · 账单记录预览框(扣费 / 充值 / 识别 三 tab + 按天/月/年筛选 + 导出全量明细)· 2026-06-28
//
// 数据实时:每次进入/切 tab/改筛选都 cache:'no-store' 重新拉,无缓存延迟。
// 筛选:period=all/day/month/year · 三个 tab 共享同一筛选,切到哪个都按当前筛选拉(同步)。
//   未筛选(all)按 created_at 最新在前。
// 状态如实:扣费区分「实扣 / 套餐内免费 / 月费」· 识别派生三态「成功 / 待复核 / 失败」·
//   充值审核态「待审核 / 已到账 / 已驳回」——不混淆已扣未扣、成功失败、到没到账。
// 导出:GET /api/credits/billing-export?lang=<系统语言> → 三 sheet 全量 xlsx(表头随语言 · 始终全量)。
// 充值是租户级(含余额信息)→ 仅 owner 可见该 tab 与导出。
// 统一取数:GET /api/credits/records?tab=&period=&date=&limit=。
// window.loadBillingRecords 由 subscription.ts 的 loadSubscription 触发。
// ============================================================

type RecTab = 'usage' | 'topup' | 'ocr';
type Period = 'all' | 'day' | 'month' | 'year';

const PREVIEW = 10;
let _tab: RecTab = 'usage';
let _period: Period = 'all';
let _date = ''; // YYYY-MM-DD 锚点(period!=all 时有效)
let _owner = true;
let _exporting = false;
let _page = 1; // 1-based · 翻页
let _total = 0; // 总条数(仅首页 offset=0 时由后端 COUNT 给,翻页沿用不重复 COUNT)

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
    const s = String(iso).replace('T', ' ');
    return s.length >= 16 ? s.slice(0, 16) : s;
}
function _pad(n: number): string {
    return String(n).padStart(2, '0');
}
function _todayStr(): string {
    const d = new Date();
    return d.getFullYear() + '-' + _pad(d.getMonth() + 1) + '-' + _pad(d.getDate());
}
function _curLang(): string {
    return window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
}

interface RecRow {
    title: string;
    meta: string;
    badge: string;
    badgeCls: string; // ok | warn | bad | free | neutral
    amount: string;
    receiptId?: string; // 有值 → 行末渲染「下载凭证 PDF」图标(仅充值记录)
}

// 下载箭头(与 history 批量导出同款 path)· 充值行末「下载凭证」按钮用。
const _DL_ICON =
    '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4M4 15v2h12v-2"/></svg>';

// 空态「发票/文档」插画(带折角 · 复用 history 风格)。
const _EMPTY_ICON =
    '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" class="rec-empty-ico"><path d="M12 6h16l8 8v28H12z"/><path d="M28 6v8h8"/><path d="M18 24h12M18 31h12M18 38h7"/></svg>';

async function loadBillingRecords() {
    const box = document.getElementById('rec-box');
    if (!box) return;
    _owner = typeof window.isOwner === 'function' ? !!window.isOwner() : true;
    if (!_owner && _tab === 'topup') _tab = 'usage';
    if (!_date) _date = _todayStr();
    _page = 1;
    renderTabs();
    renderFilter();
    renderExportBtn();
    await loadActive();
}
window.loadBillingRecords = loadBillingRecords;

function _tabDefs(): { key: RecTab; label: string }[] {
    const all: { key: RecTab; label: string }[] = [
        { key: 'usage', label: _t('rec-tab-usage', '扣费记录') },
        { key: 'ocr', label: _t('rec-tab-ocr', '识别记录') },
        { key: 'topup', label: _t('rec-tab-topup', '充值记录') },
    ];
    return _owner ? all : all.filter((t) => t.key !== 'topup');
}

function renderTabs() {
    const el = document.getElementById('rec-tabs');
    if (!el) return;
    el.innerHTML = _tabDefs()
        .map(
            (t) =>
                '<button class="rec-tab' +
                (t.key === _tab ? ' active' : '') +
                '" data-rec="' +
                t.key +
                '">' +
                _esc(t.label) +
                '</button>'
        )
        .join('');
    el.querySelectorAll('.rec-tab[data-rec]').forEach((b) => {
        const btn = b as HTMLButtonElement;
        btn.onclick = () => {
            const next = btn.getAttribute('data-rec') as RecTab;
            if (next === _tab) return;
            _tab = next;
            _page = 1;
            renderTabs();
            loadActive();
        };
    });
}

// 筛选条:粒度(全部/日/月/年)+ 对应取值控件 · 改任何一项都按当前 tab 实时重拉。
function renderFilter() {
    const el = document.getElementById('rec-filter');
    if (!el) return;
    const periods: { key: Period; label: string }[] = [
        { key: 'all', label: _t('rec-period-all', '全部') },
        { key: 'day', label: _t('rec-period-day', '日') },
        { key: 'month', label: _t('rec-period-month', '月') },
        { key: 'year', label: _t('rec-period-year', '年') },
    ];
    let valueCtrl = '';
    if (_period === 'day') {
        valueCtrl =
            '<input type="date" class="rec-date" id="rec-date-input" value="' + _esc(_date) + '">';
    } else if (_period === 'month') {
        valueCtrl =
            '<input type="month" class="rec-date" id="rec-date-input" value="' +
            _esc(_date.slice(0, 7)) +
            '">';
    } else if (_period === 'year') {
        const cur = new Date().getFullYear();
        const y = Number(_date.slice(0, 4)) || cur;
        let opts = '';
        for (let yr = cur; yr >= cur - 6; yr--) {
            opts +=
                '<option value="' +
                yr +
                '"' +
                (yr === y ? ' selected' : '') +
                '>' +
                yr +
                '</option>';
        }
        valueCtrl = '<select class="rec-date" id="rec-date-input">' + opts + '</select>';
    }
    el.innerHTML =
        '<select class="rec-period" id="rec-period-sel">' +
        periods
            .map(
                (p) =>
                    '<option value="' +
                    p.key +
                    '"' +
                    (p.key === _period ? ' selected' : '') +
                    '>' +
                    _esc(p.label) +
                    '</option>'
            )
            .join('') +
        '</select>' +
        valueCtrl;

    const sel = document.getElementById('rec-period-sel') as HTMLSelectElement | null;
    if (sel)
        sel.onchange = () => {
            _period = sel.value as Period;
            if (_period !== 'all' && !_date) _date = _todayStr();
            _page = 1;
            renderFilter();
            loadActive();
        };
    const inp = document.getElementById('rec-date-input') as
        | HTMLInputElement
        | HTMLSelectElement
        | null;
    if (inp)
        inp.onchange = () => {
            const v = inp.value;
            if (_period === 'day') _date = v;
            else if (_period === 'month') _date = v + '-01';
            else if (_period === 'year') _date = v + '-01-01';
            _page = 1;
            loadActive();
        };
}

function renderExportBtn() {
    const btn = document.getElementById('rec-export-btn') as HTMLButtonElement | null;
    if (!btn) return;
    const label = _exporting ? _t('rec-exporting', '导出中…') : _t('rec-export', '导出明细');
    btn.innerHTML = (_exporting ? '' : _DL_ICON) + '<span>' + _esc(label) + '</span>';
    btn.disabled = _exporting;
    btn.onclick = onExport;
}

async function loadActive() {
    const body = document.getElementById('rec-body');
    const foot = document.getElementById('rec-foot');
    if (!body) return;
    body.innerHTML = '<div class="rec-loading">' + _esc(_t('rec-loading', '加载中…')) + '</div>';
    if (foot) foot.innerHTML = '';
    const tabAtFetch = _tab;
    let raw: Record<string, unknown>[] = [];
    let total = 0;
    try {
        const qs = new URLSearchParams({
            tab: _tab,
            period: _period,
            limit: String(PREVIEW),
            offset: String((_page - 1) * PREVIEW),
        });
        if (_period !== 'all') qs.set('date', _date);
        const resp = await fetch('/api/credits/records?' + qs.toString(), {
            headers: _auth(),
            cache: 'no-store',
        });
        if (!resp.ok) throw new Error('http');
        const data = await resp.json();
        raw = (data && data.rows) || [];
        total = data && typeof data.total === 'number' ? data.total : raw.length;
    } catch (_) {
        body.innerHTML =
            '<div class="rec-empty">' +
            _esc(_t('rec-load-failed', '加载失败 · 请稍后再试')) +
            '</div>';
        return;
    }
    if (tabAtFetch !== _tab) return; // 期间已切走 · 丢弃过期结果
    const mapper = _tab === 'usage' ? mapUsage : _tab === 'topup' ? mapTopup : mapOcr;
    const rows = raw.map(mapper);
    if (!rows.length) {
        body.innerHTML =
            '<div class="rec-empty">' +
            _EMPTY_ICON +
            '<div class="rec-empty-t">' +
            _esc(_t('rec-empty', '暂无记录')) +
            '</div><div class="rec-empty-d">' +
            _esc(_t('rec-empty-sub', '当前筛选条件下暂无任何记录')) +
            '</div></div>';
    } else {
        body.innerHTML = rows.map(recRow).join('');
        wireReceiptButtons();
        body.scrollTop = 0; // 翻页后回到列表顶部
    }
    if (total >= 0) _total = total; // 翻页时后端略过 COUNT 返 -1 → 沿用首页统计
    renderFoot();
}

// 页脚:条数统计 + 翻页器(上一页 / p · tp / 下一页)· 单页时只显条数。
function renderFoot() {
    const foot = document.getElementById('rec-foot');
    if (!foot) return;
    const totalPages = Math.max(1, Math.ceil(_total / PREVIEW));
    if (_page > totalPages) _page = totalPages;
    const count =
        '<span class="rec-count">' +
        _esc(_t('rec-total', '共') + ' ' + _total + ' ' + _t('rec-items', '条')) +
        '</span>';
    if (totalPages <= 1) {
        foot.innerHTML = count;
        return;
    }
    foot.innerHTML =
        count +
        '<div class="rec-pages">' +
        '<button class="rec-page-btn" data-pg="prev"' +
        (_page <= 1 ? ' disabled' : '') +
        ' aria-label="' +
        _esc(_t('rec-prev', '上一页')) +
        '">‹</button>' +
        '<span class="rec-page-ind">' +
        _page +
        ' / ' +
        totalPages +
        '</span>' +
        '<button class="rec-page-btn" data-pg="next"' +
        (_page >= totalPages ? ' disabled' : '') +
        ' aria-label="' +
        _esc(_t('rec-next', '下一页')) +
        '">›</button>' +
        '</div>';
    // 禁用态的按钮不绑事件 → 无需再判边界,翻页方向由 data-pg 决定。
    foot.querySelectorAll('.rec-page-btn[data-pg]').forEach((b) => {
        const btn = b as HTMLButtonElement;
        if (btn.disabled) return;
        btn.onclick = () => {
            _page += btn.getAttribute('data-pg') === 'next' ? 1 : -1;
            loadActive();
        };
    });
}

function recRow(r: RecRow): string {
    const dl = r.receiptId
        ? '<button class="rec-dl" data-receipt="' +
          _esc(r.receiptId) +
          '" title="' +
          _esc(_t('rec-receipt', '下载凭证')) +
          '">' +
          _DL_ICON +
          '</button>'
        : '';
    return (
        '<div class="rec-row"><div class="rec-row-l"><div class="rec-row-title" title="' +
        _esc(r.title) +
        '">' +
        _esc(r.title) +
        '</div><div class="rec-row-meta">' +
        _esc(r.meta) +
        '</div></div><div class="rec-row-r">' +
        (r.badge ? '<span class="rec-badge ' + r.badgeCls + '">' + _esc(r.badge) + '</span>' : '') +
        (r.amount ? '<span class="rec-amt">' + _esc(r.amount) + '</span>' : '') +
        dl +
        '</div></div>'
    );
}

// 充值行末「下载凭证 PDF」· 单笔走 /api/credits/topup/{id}/receipt.pdf(带系统语言)。
function wireReceiptButtons() {
    document.querySelectorAll('.rec-dl[data-receipt]').forEach((b) => {
        const btn = b as HTMLButtonElement;
        btn.onclick = () => downloadReceipt(btn.getAttribute('data-receipt') || '', btn);
    });
}

async function downloadReceipt(id: string, btn: HTMLButtonElement) {
    if (!id || btn.disabled) return;
    btn.disabled = true;
    btn.classList.add('busy');
    try {
        const resp = await fetch(
            '/api/credits/topup/' +
                encodeURIComponent(id) +
                '/receipt.pdf?lang=' +
                encodeURIComponent(_curLang()),
            { headers: _auth(), cache: 'no-store' }
        );
        if (!resp.ok) throw new Error('http');
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'pearnly_topup_' + id + '.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (_) {
        _toast(_t('rec-receipt-failed', '凭证下载失败 · 请稍后再试'), 'error');
    } finally {
        btn.disabled = false;
        btn.classList.remove('busy');
    }
}

function mapUsage(r: Record<string, unknown>): RecRow {
    const isSub = r.type === 'subscription';
    const cost = Number(r.cost_thb || 0);
    let badge: string;
    let badgeCls: string;
    if (isSub) {
        badge = _t('rec-b-monthly', '月费');
        badgeCls = 'neutral';
    } else if (cost === 0) {
        badge = _t('rec-b-free', '套餐内免费');
        badgeCls = 'free';
    } else {
        badge = _t('rec-b-charged', '实扣');
        badgeCls = 'bad';
    }
    const title = isSub
        ? String(r.description || _t('rec-t-sub', '订阅 / 续订'))
        : String(r.filename || r.description || _t('rec-t-scan', '扫描扣费'));
    const meta =
        _fmtDate(r.date as string) +
        (!isSub && r.pages ? ' · ' + r.pages + ' ' + _t('sub-sheet', '张') : '');
    return { title, meta, badge, badgeCls, amount: cost === 0 ? '' : _money(Math.abs(cost)) };
}

function mapTopup(r: Record<string, unknown>): RecRow {
    const map: Record<string, [string, string]> = {
        approved: [_t('rec-tp-approved', '已到账'), 'ok'],
        rejected: [_t('rec-tp-rejected', '已驳回'), 'bad'],
        pending: [_t('rec-tp-pending', '待审核'), 'warn'],
    };
    const st = map[String(r.status || 'pending')] || map.pending;
    return {
        title: String(r.payer_name || _t('rec-topup', '充值')),
        meta: _fmtDate(r.created_at as string),
        badge: st[0],
        badgeCls: st[1],
        amount: '+ ' + _money(Number(r.amount_thb || 0)),
        receiptId: r.id != null ? String(r.id) : undefined,
    };
}

function mapOcr(r: Record<string, unknown>): RecRow {
    const map: Record<string, [string, string]> = {
        confirmed: [_t('rec-o-confirmed', '识别成功'), 'ok'],
        failed: [_t('rec-o-failed', '识别失败'), 'bad'],
        pending: [_t('rec-o-pending', '待复核'), 'warn'],
    };
    const st = map[String(r.status || 'pending')] || map.pending;
    const total = r.total_amount;
    const inv = r.invoice_no ? ' · ' + r.invoice_no : '';
    return {
        title: String(r.filename || r.seller_name || _t('rec-o-untitled', '识别记录')),
        meta: _fmtDate(r.created_at as string) + inv,
        badge: st[0],
        badgeCls: st[1],
        amount: total != null ? _money(Number(total)) : '',
    };
}

// 点导出 → 先弹区间选择(年月日 ~ 年月日 · 默认近一个月截止今天 · billing-export-modal.ts)· 选定再下载。
async function onExport() {
    if (_exporting) return;
    if (typeof window._pickExportRange !== 'function') return;
    const range = await window._pickExportRange();
    if (!range || !range.from || !range.to) return; // 取消
    _exporting = true;
    renderExportBtn();
    try {
        const qs = new URLSearchParams({
            lang: _curLang(),
            date_from: range.from,
            date_to: range.to,
        });
        const resp = await fetch('/api/credits/billing-export?' + qs.toString(), {
            headers: _auth(),
            cache: 'no-store',
        });
        if (!resp.ok) throw new Error('http');
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const d = new Date();
        a.download =
            'pearnly_billing_' +
            d.getFullYear() +
            _pad(d.getMonth() + 1) +
            _pad(d.getDate()) +
            '.xlsx';
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        _toast(_t('rec-export-ok', '导出成功'), 'success');
    } catch (_) {
        _toast(_t('rec-export-failed', '导出失败 · 请稍后再试'), 'error');
    } finally {
        _exporting = false;
        renderExportBtn();
    }
}
