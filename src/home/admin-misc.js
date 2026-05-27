// ============================================================
// REFACTOR-C1 (2026-05-27) · 老 admin 残留入口 + 管理员成本追踪面板 admin-misc 从 home.js 抽出为 ES module
//
// 来源:home.js L8364-8632 · verbatim 0 改逻辑(仅 prettier 重排)· 两个相邻 IIFE。
// IIFE#1 = 顶栏「管理」下拉 click handler;IIFE#2 = 成本追踪面板(暴露 window.loadAdminCostPage,
// 被 ai-balance module 经 window. 包裹 · 故本 module 在 main.js 须 import 在 ai-balance 之前)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

/* global routeTo, escapeHtml */

// ============================================================
// v109.4 · 老的管理后台模块(/admin)已删除 · 改用新的 admin-users(数据更全 · 字段对齐多租户)
// 但右上角顶栏「管理」下拉的点击事件需要单独保留
// ============================================================
(function () {
    'use strict';
    document.addEventListener('click', (e) => {
        // 1. 顶栏「管理」按钮 → 打开下拉
        const adminToggle = e.target.closest && e.target.closest('#admin-toggle');
        if (adminToggle) {
            const dd = document.getElementById('admin-dropdown');
            if (dd) dd.classList.toggle('open');
            e.stopPropagation();
            return;
        }
        // 2. 下拉里的子菜单
        const adminItem = e.target.closest && e.target.closest('[data-admin-route]');
        if (adminItem && !adminItem.disabled) {
            const sub = adminItem.dataset.adminRoute;
            const dd = document.getElementById('admin-dropdown');
            if (dd) dd.classList.remove('open');
            if (sub === 'users') {
                // v109.4 · 跳新的 admin-users 页(不再用老的 admin · 数据更全 · 字段对齐多租户)
                if (typeof routeTo === 'function') routeTo('admin-users');
            } else if (sub === 'logs') {
                // v109.4 · 操作日志暂未实现 · 提示即将推出
                if (typeof showToast === 'function' && typeof t === 'function') {
                    showToast(t('feature-coming-soon'), 'info');
                }
            }
            return;
        }
        // 3. 点其他地方关下拉
        if (!e.target.closest('#admin-dropdown')) {
            const dd = document.getElementById('admin-dropdown');
            if (dd) dd.classList.remove('open');
        }
    });
})();

// ============================================================
// v106 · 管理员成本追踪面板
// ============================================================
(function () {
    function fmt(n, decimals) {
        if (n === null || n === undefined || isNaN(n)) return '—';
        const d = decimals === undefined ? 2 : decimals;
        return Number(n)
            .toFixed(d)
            .replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    function fmtCost(thb) {
        if (!thb || thb === 0) return '<span class="cost-money cost-money-zero">฿ 0</span>';
        return `<span class="cost-money">฿ ${fmt(thb, 4)}</span>`;
    }

    let _lastEngines = [];

    function _renderEngines(engines) {
        const engEl = document.getElementById('kpi-engines');
        if (!engEl) return;
        if (!engines || !engines.length) {
            engEl.innerHTML =
                '<span style="font-size:13px; color:#9ca3af;">' + t('cost-no-engines') + '</span>';
            return;
        }
        const _engNames = {
            gemini: t('adm-engine-ocr'),
            google_vision: t('adm-engine-ocr-backup'),
            text_path: t('adm-engine-epdf'),
            'gemini-vex': t('adm-engine-vex'),
        };
        const sorted = [...engines].sort(function (a, b) {
            return (b.cost_thb || 0) - (a.cost_thb || 0);
        });
        engEl.innerHTML = sorted
            .map(function (e) {
                const name = _engNames[e.engine] || e.engine;
                const cost = e.cost_thb || 0;
                const cnt = e.count || 0;
                const avg = cnt ? cost / cnt : 0;
                return (
                    '<div class="engine-row">' +
                    '<span class="engine-name">' +
                    name +
                    '</span>' +
                    '<span class="engine-stats">' +
                    '<span class="engine-cost">฿' +
                    fmt(cost, 4) +
                    '</span>' +
                    '<span class="engine-cnt">' +
                    cnt +
                    ' · avg ฿' +
                    fmt(avg, 4) +
                    '</span>' +
                    '</span></div>'
                );
            })
            .join('');
    }
    function fmtTime(iso) {
        if (!iso) return t('cost-never-used');
        const d = new Date(iso);
        const now = new Date();
        const diffMs = now - d;
        const diffMin = Math.floor(diffMs / 60000);
        if (diffMin < 1) return 'just now';
        if (diffMin < 60) return diffMin + 'min ago';
        const diffH = Math.floor(diffMin / 60);
        if (diffH < 24) return diffH + 'h ago';
        const diffD = Math.floor(diffH / 24);
        if (diffD < 7) return diffD + 'd ago';
        return d.toISOString().slice(0, 10);
    }

    async function fetchJson(path) {
        const tok = localStorage.getItem('mrpilot_token');
        const r = await fetch(path, {
            headers: { Authorization: 'Bearer ' + tok },
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
    }

    async function loadOverview() {
        try {
            const data = await fetchJson('/api/admin/cost/overview');
            // 今日
            document.getElementById('kpi-today-cost').textContent =
                '฿ ' + fmt(data.today.cost_thb || 0, 2);
            document.getElementById('kpi-today-sub').textContent =
                (data.today.invoices || 0) +
                ' ' +
                t('cost-invoices-suffix') +
                ' · ' +
                (data.today.pages || 0) +
                ' ' +
                t('cost-pages-suffix');
            // 本月
            document.getElementById('kpi-month-cost').textContent =
                '฿ ' + fmt(data.month.cost_thb || 0, 2);
            document.getElementById('kpi-month-sub').textContent =
                (data.month.invoices || 0) +
                ' ' +
                t('cost-invoices-suffix') +
                ' · ' +
                (data.month.pages || 0) +
                ' ' +
                t('cost-pages-suffix');
            // 累计
            document.getElementById('kpi-total-cost').textContent =
                '฿ ' + fmt(data.total.cost_thb || 0, 2);
            document.getElementById('kpi-total-sub').textContent =
                (data.total.invoices || 0) +
                ' ' +
                t('cost-invoices-suffix') +
                ' · ' +
                (data.total.pages || 0) +
                ' ' +
                t('cost-pages-suffix');
            // 引擎明细 · 缓存供切语言时重渲
            _lastEngines = data.engines || [];
            _renderEngines(_lastEngines);
        } catch (e) {
            console.error('cost overview fail', e);
            showToast(t('cost-load-fail'), 'fail');
        }
    }

    async function loadByUser() {
        const tbody = document.getElementById('cost-by-user-tbody');
        tbody.innerHTML = `<tr><td colspan="9" class="cost-table-empty">${t('cost-loading')}</td></tr>`;
        try {
            const data = await fetchJson('/api/admin/cost/by_user');
            const users = data.users || [];
            if (!users.length) {
                tbody.innerHTML = `<tr><td colspan="9" class="cost-table-empty">${t('cost-empty')}</td></tr>`;
                return;
            }
            tbody.innerHTML = users
                .map((u) => {
                    const avg = u.total_invoices ? u.total_cost_thb / u.total_invoices : 0;
                    return `<tr>
                    <td><strong>${escapeHtml(u.username || '—')}</strong></td>
                    <td>${u.plan ? `<span class="cost-plan-badge">${escapeHtml(u.plan)}</span>` : '—'}</td>
                    <td>${fmtCost(u.today_cost_thb)}</td>
                    <td>${fmtCost(u.month_cost_thb)}</td>
                    <td>${fmtCost(u.total_cost_thb)}</td>
                    <td>${u.total_pages}</td>
                    <td>${u.total_invoices}</td>
                    <td>${avg ? '฿ ' + fmt(avg, 4) : '—'}</td>
                    <td>${fmtTime(u.last_used_at)}</td>
                </tr>`;
                })
                .join('');
        } catch (e) {
            console.error('cost by_user fail', e);
            tbody.innerHTML = `<tr><td colspan="9" class="cost-table-empty">${t('cost-load-fail')}</td></tr>`;
        }
    }

    async function loadTrend() {
        const wrap = document.getElementById('cost-trend-chart');
        wrap.innerHTML = `<div class="cost-trend-empty">${t('cost-loading')}</div>`;
        try {
            const data = await fetchJson('/api/admin/cost/daily_trend?days=30');
            const days = data.days || [];
            if (!days.length) {
                wrap.innerHTML = `<div class="cost-trend-empty">${t('cost-empty')}</div>`;
                return;
            }
            // 补齐 30 天(没数据的日期填 0)· 让趋势更直观
            const today = new Date();
            const map = {};
            for (const d of days) map[d.day] = d;
            const filled = [];
            for (let i = 29; i >= 0; i--) {
                const dt = new Date(today);
                dt.setDate(dt.getDate() - i);
                const key = dt.toISOString().slice(0, 10);
                filled.push({
                    day: key,
                    cost_thb: map[key] ? map[key].cost_thb : 0,
                    invoices: map[key] ? map[key].invoices : 0,
                    pages: map[key] ? map[key].pages : 0,
                });
            }
            // 渲染纯 SVG 柱状图
            const W = 800,
                H = 200,
                PAD = 30;
            const innerW = W - PAD * 2;
            const innerH = H - PAD;
            const maxCost = Math.max(...filled.map((d) => d.cost_thb), 0.01);
            const barW = (innerW / filled.length) * 0.7;
            const gap = (innerW / filled.length) * 0.3;
            const bars = filled
                .map((d, i) => {
                    const x = PAD + (innerW / filled.length) * i + gap / 2;
                    const h = (d.cost_thb / maxCost) * innerH;
                    const y = H - h - PAD / 2;
                    return `<rect class="trend-bar" x="${x.toFixed(1)}" y="${y.toFixed(1)}" 
                              width="${barW.toFixed(1)}" height="${h.toFixed(1)}" rx="2">
                    <title>${d.day}: ฿${d.cost_thb.toFixed(4)} · ${d.invoices} ${t('cost-invoices-suffix')}</title>
                </rect>`;
                })
                .join('');
            // x 轴 5 个标签
            const tickIdx = [0, 7, 14, 21, 29];
            const xLabels = tickIdx
                .map((i) => {
                    const x = PAD + (innerW / filled.length) * i + barW / 2 + gap / 2;
                    const day = filled[i].day.slice(5); // MM-DD
                    return `<text class="trend-label" x="${x.toFixed(1)}" y="${H - 4}" text-anchor="middle">${day}</text>`;
                })
                .join('');
            // y 轴 max 标签
            const yMaxLabel = `<text class="trend-label" x="${PAD - 4}" y="${PAD / 2 + 4}" text-anchor="end">฿ ${maxCost.toFixed(2)}</text>`;
            const yMidLabel = `<text class="trend-label" x="${PAD - 4}" y="${PAD / 2 + innerH / 2 + 4}" text-anchor="end">฿ ${(maxCost / 2).toFixed(2)}</text>`;
            // 底线
            const baseline = `<line class="trend-axis" x1="${PAD}" y1="${H - PAD / 2}" x2="${W - PAD}" y2="${H - PAD / 2}"/>`;
            wrap.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
                ${baseline}${bars}${xLabels}${yMaxLabel}${yMidLabel}
            </svg>`;
        } catch (e) {
            console.error('cost trend fail', e);
            wrap.innerHTML = `<div class="cost-trend-empty">${t('cost-load-fail')}</div>`;
        }
    }

    async function exportCsv() {
        try {
            const tok = localStorage.getItem('mrpilot_token');
            const resp = await fetch('/api/admin/cost/export?days=30', {
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mrpilot_cost_${new Date().toISOString().slice(0, 10)}.csv`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error('export fail', e);
            showToast(t('cost-export-fail'), 'fail');
        }
    }

    window.loadAdminCostPage = function () {
        loadOverview();
        loadByUser();
        loadTrend();
    };

    // 切语言时重渲引擎明细(无需重新 fetch)
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('admin-cost-engines', function () {
            _renderEngines(_lastEngines);
        });
    }

    // 绑定按钮
    document.addEventListener('DOMContentLoaded', () => {
        const refreshBtn = document.getElementById('btn-cost-refresh');
        if (refreshBtn) refreshBtn.addEventListener('click', () => window.loadAdminCostPage());
        const exportBtn = document.getElementById('btn-cost-export');
        if (exportBtn) exportBtn.addEventListener('click', exportCsv);
    });
})();
