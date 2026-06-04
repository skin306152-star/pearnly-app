// ============================================================
// REFACTOR-C1 (2026-05-27) · 客户访问日志 tab(Pearnly 访问日志)从 home.js 抽出为 ES module
//
// 来源:home.js L17971-18161(v118.28.8 · 仅 owner 可见)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑。
// 自包含:在 IIFE 内经 document 事件委托 / settings tab hook 自绑(renderSettings 模拟
//   click active tab 触发)· 无外部按名同步调用 · 抽成 defer module 后仍安全。
// 依赖的全局(home.js 暴露 · bare 调 · 不 import):见下方 /* global */ 声明。
// verbatim 搬迁 · 0 改逻辑(仅 prettier 重排格式)。
// ============================================================
/* global escapeHtml */
// ============================================================
// v118.28.8 · 客户老板 · Pearnly 访问日志 tab
// 仅 owner 可见(JS 控制 nav 项显隐)· 数据来自 /api/me/access_log
// ============================================================
(function () {
    'use strict';

    const _state = { page: 1, per_page: 50, q: '', total: 0, rows: [], loaded: false };

    function _fmtTime(iso: string) {
        if (!iso) return '';
        try {
            return new Date(iso).toLocaleString();
        } catch (e) {
            return iso;
        }
    }

    function _renderEmpty(msg: string) {
        const tbl = document.getElementById('access-log-table');
        if (tbl) tbl.innerHTML = '<div class="access-log-empty">' + escapeHtml(msg) + '</div>';
        const pg = document.getElementById('access-log-pager');
        if (pg) pg.innerHTML = '';
    }

    function _renderTable() {
        const tbl = document.getElementById('access-log-table');
        if (!tbl) return;
        const rows = _state.rows || [];
        if (!rows.length) {
            _renderEmpty(t('set-access-log-empty'));
            return;
        }
        const head = `
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t('set-access-log-col-time'))}</div>
                <div>${escapeHtml(t('set-access-log-col-actor'))}</div>
                <div>${escapeHtml(t('set-access-log-col-action'))}</div>
                <div>${escapeHtml(t('set-access-log-col-target'))}</div>
                <div>${escapeHtml(t('set-access-log-col-ip'))}</div>
            </div>`;
        const body = rows
            .map(function (l: any) {
                return `
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t('set-access-log-col-time'))}">${escapeHtml(_fmtTime(l.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t('set-access-log-col-actor'))}">${escapeHtml(l.actor_username || '-')}</div>
                    <div data-label="${escapeHtml(t('set-access-log-col-action'))}"><span class="access-log-action">${escapeHtml(l.action || '-')}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t('set-access-log-col-target'))}">${escapeHtml(l.target_name || l.target_type || '-')}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t('set-access-log-col-ip'))}">${escapeHtml(l.ip || '-')}</div>
                </div>`;
            })
            .join('');
        tbl.innerHTML = head + body;
    }

    function _renderPager() {
        const wrap = document.getElementById('access-log-pager');
        if (!wrap) return;
        const total = _state.total || 0;
        if (!total) {
            wrap.innerHTML = '';
            return;
        }
        const page = _state.page || 1;
        const per = _state.per_page || 50;
        const totalPages = Math.max(1, Math.ceil(total / per));
        const info = (t('set-access-log-pager-total') || 'Total {n}').replace(
            '{n}',
            total as unknown as string
        );
        const pageStr = (t('set-access-log-pager-page') || 'Page {p} / {t}')
            .replace('{p}', page as unknown as string)
            .replace('{t}', totalPages as unknown as string);
        wrap.innerHTML = `
            <div class="access-log-pager-info">${escapeHtml(info)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>← ${escapeHtml(t('set-access-log-pager-prev'))}</button>
                <span class="access-log-pager-page">${escapeHtml(pageStr)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${page + 1}" ${page >= totalPages ? 'disabled' : ''}>${escapeHtml(t('set-access-log-pager-next'))} →</button>
            </div>`;
    }

    async function _load(page: number) {
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        _state.page = page || 1;
        _renderEmpty(t('set-access-log-loading'));
        try {
            const url =
                '/api/me/access_log?page=' +
                _state.page +
                '&per_page=' +
                _state.per_page +
                '&q=' +
                encodeURIComponent(_state.q || '');
            const r = await fetch(url, { headers: { Authorization: 'Bearer ' + tk } });
            if (r.status === 403) {
                _renderEmpty(t('set-access-log-empty'));
                return;
            }
            if (!r.ok) throw new Error('http_' + r.status);
            const data = await r.json();
            _state.rows = data.logs || [];
            _state.total = data.total || 0;
            _state.loaded = true;
            _renderTable();
            _renderPager();
        } catch (e) {
            _renderEmpty(t('set-access-log-fail'));
        }
    }

    async function _csvExport() {
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        try {
            const url = '/api/me/access_log.csv?q=' + encodeURIComponent(_state.q || '');
            const r = await fetch(url, { headers: { Authorization: 'Bearer ' + tk } });
            if (!r.ok) {
                showToast(t('set-access-log-csv-fail') || 'Export failed', 'error');
                return;
            }
            const blob = await r.blob();
            const a = document.createElement('a');
            const objUrl = URL.createObjectURL(blob);
            a.href = objUrl;
            a.download = 'pearnly_access_log.csv';
            document.body.appendChild(a);
            a.click();
            setTimeout(function () {
                URL.revokeObjectURL(objUrl);
                a.remove();
            }, 100);
            showToast(t('set-access-log-csv-ok') || 'Exported', 'success');
        } catch (e) {
            showToast(t('set-access-log-csv-fail') || 'Export failed', 'error');
        }
    }

    // 显隐控制 · 仅 owner / super admin 可见
    function _applyVisibility() {
        const items = document.querySelectorAll('.set-tab-owner-only');
        const isOwner = !!(_userInfo && (_userInfo.role === 'owner' || _userInfo.is_super_admin));
        items.forEach(function (el: Element) {
            (el as HTMLElement).style.display = isOwner ? '' : 'none';
        });
    }

    // tab 切换钩子 · 监听 settings tab 切换
    document.addEventListener('click', function (ev) {
        const tabBtn = (ev.target as HTMLElement).closest('.settings-tab[data-tab="access-log"]');
        if (tabBtn) {
            // 进入 access-log tab · 加载首页
            setTimeout(function () {
                if (!_state.loaded || _state.page !== 1) {
                    _load(1);
                }
            }, 50);
            return;
        }
        const csvBtn = (ev.target as HTMLElement).closest('#access-log-csv-btn');
        if (csvBtn) {
            ev.preventDefault();
            _csvExport();
            return;
        }
        const pgBtn = (ev.target as HTMLElement).closest(
            '.access-log-pager-btn[data-access-log-page]'
        ) as HTMLButtonElement | null;
        if (pgBtn && !pgBtn.disabled) {
            const tp = parseInt(pgBtn.dataset.accessLogPage!, 10);
            _load(tp);
        }
    });

    // 搜索 · debounce
    document.addEventListener('input', function (ev) {
        if (ev.target && (ev.target as HTMLElement).id === 'access-log-search') {
            clearTimeout(window.__accessLogSearchTimer);
            window.__accessLogSearchTimer = setTimeout(function () {
                _state.q = ((ev.target as HTMLInputElement).value || '').trim();
                _load(1);
            }, 350);
        }
    });

    // 等用户信息就绪后再控制显隐
    let _checkN = 0;
    const _vTimer = setInterval(function () {
        _checkN++;
        if (_userInfo) {
            _applyVisibility();
            clearInterval(_vTimer);
        }
        if (_checkN > 60) clearInterval(_vTimer);
    }, 500);

    // i18n 订阅 · 切语言重渲(若已加载)
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('me-access-log', function () {
            _applyVisibility();
            if (_state.loaded) {
                _renderTable();
                _renderPager();
            }
        });
    }
})();
