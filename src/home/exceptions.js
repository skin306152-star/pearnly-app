// ============================================================
// REFACTOR-C1 (2026-05-27) · 异常栏 阶段2 列表页 exceptions 从 home.js 抽出为 ES module
//
// 来源:home.js L13414-15025 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global escapeHtml, showConfirm, currentLang, humanizeError */
/* eslint-disable no-useless-assignment -- verbatim home.js · 非 bug */

// ============================================================
// v118.20.2 · 异常栏 阶段 2 · 列表页(KPI + chips + 列表)
// 复核交互(抽屉/确认放行/忽略此类)留 阶段 3 · 当前点击行只 toast 提示
// ============================================================
(function () {
    let _excState = {
        statsCache: null,
        listCache: [],
        currentRule: null, // null = 全部 · 否则单 rule_code
        currentClient: '', // v118.21.0 · '' = 全部客户 · 否则 client_id 字符串
        currentStatus: 'pending', // v118.21.1 · 'pending' | 'resolved' | 'ignored'
        loading: false,
        // v118.20.5 · P0-3 / P0-4
        selectedIds: new Set(), // 批量选中的 exception id
        offset: 0,
        pageSize: 50,
        total: 0, // 后端返回的当前筛选下的预估总数(此处用 listCache.length 或追加后累计)
        loadFailed: false,
        listScrollY: 0, // 抽屉关闭后回到列表 scroll 位置
    };

    // v118.20.5 · 简易 i18n 占位替换({n} 等)
    function _tn(key, vars) {
        let s = t(key) || key;
        if (vars)
            for (const k in vars)
                s = s.replace(new RegExp('\\{' + k + '\\}', 'g'), String(vars[k]));
        return s;
    }

    // 红点徽章 · 全局可用 · 路由切换 + 周期刷新都调它
    async function refreshExcBadge() {
        try {
            // v118.21.0 · 徽章数跟随 currentClient · 防切走客户后徽章数和列表不一致
            // v118.21.1 · 徽章固定数 pending(不论用户当前在看哪个状态 tab)
            const cid = _excState.currentClient || '';
            const url =
                '/api/exceptions/stats?status=pending' +
                (cid ? '&client_id=' + encodeURIComponent(cid) : '');
            const resp = await fetch(url, {
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            if (!resp.ok) return;
            const stats = await resp.json();
            const badge = document.getElementById('nav-exc-badge');
            if (!badge) return;
            const n = parseInt(stats.pending || 0, 10);
            if (n > 0) {
                badge.textContent = n > 99 ? '99+' : String(n);
                badge.style.display = '';
            } else {
                badge.style.display = 'none';
            }
        } catch (e) {
            /* 静默 · 不打断主流程 */
        }
    }

    // SVG 小图标(规则严重度)
    function _sevSvg(sev) {
        if (sev === 'high') {
            return `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 1.5L1 12.5h12L7 1.5z"/>
                <line x1="7" y1="6" x2="7" y2="9"/>
                <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
            </svg>`;
        }
        if (sev === 'medium') {
            return `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="7" cy="7" r="5.5"/>
                <line x1="7" y1="4" x2="7" y2="7.5"/>
                <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
            </svg>`;
        }
        return `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="4.5" y1="7" x2="9.5" y2="7"/>
        </svg>`;
    }

    function _emptySvg() {
        return `<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`;
    }

    function _fmtMoney(n) {
        if (n === null || n === undefined) return '—';
        const v = parseFloat(n);
        if (isNaN(v)) return '—';
        return (
            '฿ ' +
            v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        );
    }

    function _shortDate(iso) {
        if (!iso) return '—';
        return iso.slice(0, 10);
    }

    function renderKpis(stats) {
        document.getElementById('exc-kpi-pending').textContent = stats.pending || 0;
        document.getElementById('exc-kpi-high').textContent = stats.high_severity || 0;
        document.getElementById('exc-kpi-resolved').textContent = stats.resolved || 0;
        document.getElementById('exc-kpi-learned').textContent = stats.learned_rules || 0;
        // v118.21.1 · status tab 计数同步
        const cp = document.getElementById('exc-status-tab-count-pending');
        const cr = document.getElementById('exc-status-tab-count-resolved');
        const ci = document.getElementById('exc-status-tab-count-ignored');
        if (cp) cp.textContent = stats.pending || 0;
        if (cr) cr.textContent = stats.resolved || 0;
        if (ci) ci.textContent = stats.ignored || 0;
        // active 态
        const tabs = document.querySelectorAll('#exc-status-tabs .exc-status-tab');
        tabs.forEach((t) => {
            t.classList.toggle(
                'active',
                t.dataset.status === (_excState.currentStatus || 'pending')
            );
        });
    }

    function renderChips(stats) {
        const wrap = document.getElementById('exc-chips');
        if (!wrap) return;
        const byRule = stats.by_rule || {};
        const rules = [
            'confidence_low',
            'duplicate',
            'amount_missing',
            'math_mismatch',
            'tax_id_format_invalid',
        ];

        const allActive = !_excState.currentRule;
        let html = `<button class="exc-chip ${allActive ? 'active' : ''}" data-rule="">
            <span>${escapeHtml(t('exc-chip-all'))}</span>
            <span class="exc-chip-count">${stats.pending || 0}</span>
        </button>`;
        for (const rc of rules) {
            const n = byRule[rc] || 0;
            if (n === 0 && _excState.currentRule !== rc) continue; // 0 数 + 非当前激活 → 隐藏 chip 减杂讯
            const active = _excState.currentRule === rc;
            html += `<button class="exc-chip ${active ? 'active' : ''}" data-rule="${escapeHtml(rc)}">
                <span>${escapeHtml(t('exc-chip-' + rc))}</span>
                <span class="exc-chip-count">${n}</span>
            </button>`;
        }
        wrap.innerHTML = html;
        wrap.querySelectorAll('.exc-chip').forEach((btn) => {
            btn.addEventListener('click', () => {
                const rc = btn.dataset.rule || null;
                _excState.currentRule = rc;
                loadExceptionsList();
            });
        });
    }

    function renderList(items) {
        const wrap = document.getElementById('exc-list');
        if (!wrap) return;
        if (!items || items.length === 0) {
            wrap.innerHTML = `<div class="exc-empty">
                ${_emptySvg()}
                <div class="exc-empty-title">${escapeHtml(t('exc-empty-title'))}</div>
                <div>${escapeHtml(t('exc-empty-desc'))}</div>
            </div>`;
            renderListFoot(); // 空列表也更新底部计数(0/0)
            return;
        }
        const checkSvg = `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>`;
        const showCheckbox = (_excState.currentStatus || 'pending') === 'pending';
        wrap.innerHTML = items
            .map((it) => {
                const sev = it.severity || 'medium';
                const ruleLabel = t('exc-rule-' + it.rule_code) || it.rule_code;
                const seller =
                    it.seller_name && it.seller_name.trim() ? it.seller_name : t('exc-no-seller');
                const filename = it.filename || '—';
                const date = _shortDate(it.invoice_date || it.created_at);
                const isPending = it.status === 'pending';
                const checked = _excState.selectedIds.has(it.id);
                const checkCellVisible = showCheckbox && isPending;
                return `
                <div class="exc-row sev-${escapeHtml(sev)} ${checked ? 'selected' : ''}" data-exc-id="${escapeHtml(String(it.id))}">
                    <div class="exc-row-check ${checked ? 'checked' : ''}" data-check-id="${escapeHtml(String(it.id))}" ${checkCellVisible ? '' : 'style="visibility:hidden;"'}>${checkSvg}</div>
                    <div class="exc-row-sev">${_sevSvg(sev)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(seller)} · ${escapeHtml(filename)}</div>
                        <div class="exc-row-meta">
                            ${it.invoice_no ? `<span><b>${escapeHtml(it.invoice_no)}</b></span>` : ''}
                            <span>${escapeHtml(date)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(sev)}">${escapeHtml(ruleLabel)}</div>
                    <div class="exc-row-amount">${escapeHtml(_fmtMoney(it.total_amount))}</div>
                </div>
            `;
            })
            .join('');
        // 行点击 → 抽屉(checkbox 区域阻断)
        wrap.querySelectorAll('.exc-row').forEach((row) => {
            row.addEventListener('click', (e) => {
                if (e.target.closest('.exc-row-check')) return; // checkbox 自己处理
                const id = row.dataset.excId;
                if (id) openExcDrawer(parseInt(id, 10));
            });
        });
        // checkbox 切换
        wrap.querySelectorAll('.exc-row-check').forEach((box) => {
            box.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(box.dataset.checkId, 10);
                if (!id) return;
                if (_excState.selectedIds.has(id)) {
                    _excState.selectedIds.delete(id);
                    box.classList.remove('checked');
                    box.closest('.exc-row').classList.remove('selected');
                } else {
                    _excState.selectedIds.add(id);
                    box.classList.add('checked');
                    box.closest('.exc-row').classList.add('selected');
                }
                renderBatchBar();
            });
        });
        renderBatchBar();
        renderListFoot();
    }

    // v118.20.5 · 批量栏渲染
    function renderBatchBar() {
        const bar = document.getElementById('exc-batch-bar');
        const cnt = document.getElementById('exc-batch-count');
        if (!bar || !cnt) return;
        const n = _excState.selectedIds.size;
        if (n === 0) {
            bar.style.display = 'none';
        } else {
            bar.style.display = '';
            cnt.textContent = _tn('exc-batch-count', { n });
        }
    }

    // v118.20.5 · 列表底部计数 + 加载更多按钮显示控制
    function renderListFoot() {
        const foot = document.getElementById('exc-list-foot');
        const cnt = document.getElementById('exc-list-count');
        const more = document.getElementById('exc-loadmore');
        if (!foot || !cnt || !more) return;
        const shown = _excState.listCache.length;
        if (shown === 0) {
            foot.style.display = 'none';
            return;
        }
        foot.style.display = '';
        // 当前筛选下的 pending 总数(从 stats 取 · 跟 chip 数同步)
        let total = shown;
        const stats = _excState.statsCache;
        if (stats) {
            if (_excState.currentRule) {
                total = (stats.by_rule || {})[_excState.currentRule] || shown;
            } else {
                total = stats.pending || shown;
            }
        }
        _excState.total = total;
        cnt.textContent = _tn('exc-list-count', { shown, total });
        // 加载更多按钮:还有未加载的 + 没到 500 上限
        const canLoadMore = shown < total && shown < 500;
        more.style.display = canLoadMore ? '' : 'none';
    }

    async function loadExceptionsStats() {
        try {
            if (navigator.onLine === false) throw new Error('offline');
            const cid = _excState.currentClient || '';
            const st = _excState.currentStatus || 'pending';
            const params = new URLSearchParams();
            params.set('status', st);
            if (cid) params.set('client_id', cid);
            const url = '/api/exceptions/stats?' + params.toString();
            const resp = await fetch(url, {
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            const stats = await resp.json();
            _excState.statsCache = stats;
            renderKpis(stats);
            renderChips(stats);
            return stats;
        } catch (e) {
            console.warn('loadExceptionsStats fail', e);
            // 不显式 toast(列表加载会触发 toast · 避免双弹)· 但 KPI 显「—」
            return null;
        }
    }

    function _renderListError(isOffline) {
        const wrap = document.getElementById('exc-list');
        if (!wrap) return;
        const errSvg = `<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`;
        const title = isOffline ? t('exc-offline') : t('exc-error-retry-title');
        const desc = isOffline ? '' : t('exc-error-retry-desc');
        wrap.innerHTML = `
            <div class="exc-error">
                ${errSvg}
                <div class="exc-error-msg">${escapeHtml(title)}${desc ? ' · ' + escapeHtml(desc) : ''}</div>
                <button class="exc-retry-btn" id="exc-retry-btn" type="button">${escapeHtml(t('exc-retry-btn'))}</button>
            </div>`;
        const btn = document.getElementById('exc-retry-btn');
        if (btn)
            btn.addEventListener(
                'click',
                () => window.loadExceptionsPage && window.loadExceptionsPage()
            );
    }

    async function loadExceptionsList(opts) {
        opts = opts || {};
        const append = !!opts.append;
        const wrap = document.getElementById('exc-list');
        if (!append && wrap && _excState.listCache.length === 0) {
            wrap.innerHTML = `<div class="exc-loading">${escapeHtml(t('exc-loading'))}</div>`;
        }
        const params = new URLSearchParams();
        params.set('status', _excState.currentStatus || 'pending');
        if (_excState.currentRule) params.set('rule_code', _excState.currentRule);
        if (_excState.currentClient) params.set('client_id', _excState.currentClient);
        const offset = append ? _excState.listCache.length : 0;
        params.set('limit', String(_excState.pageSize));
        params.set('offset', String(offset));
        try {
            if (navigator.onLine === false) throw new Error('offline');
            const resp = await fetch('/api/exceptions/list?' + params.toString(), {
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            const data = await resp.json();
            const newItems = data.items || [];
            if (append) {
                _excState.listCache = _excState.listCache.concat(newItems);
            } else {
                _excState.listCache = newItems;
                // 切换 chip / 全量重载 · 清空选中(避免选中已不在列表的项)
                _excState.selectedIds.clear();
            }
            _excState.loadFailed = false;
            renderList(_excState.listCache);
            // 重渲 chips · 让 active 状态跟随
            if (_excState.statsCache) renderChips(_excState.statsCache);
        } catch (e) {
            console.warn('loadExceptionsList fail', e);
            _excState.loadFailed = true;
            const isOffline =
                navigator.onLine === false || String(e.message || '').includes('offline');
            // append 失败:仅 toast · 不替换列表(用户已加载的不丢)
            if (append) {
                showToast(t('exc-toast-load-fail'), 'error');
            } else {
                _renderListError(isOffline);
                showToast(isOffline ? t('exc-offline') : t('exc-toast-load-fail'), 'error');
            }
        }
    }

    // v118.20.5 · 分页 · 加载更多
    async function loadMore() {
        if (_excState.loading) return;
        if (_excState.listCache.length >= 500) return;
        _excState.loading = true;
        try {
            await loadExceptionsList({ append: true });
        } finally {
            _excState.loading = false;
        }
    }

    // 主入口 · routeTo 调它
    // v118.21.0 · 把客户缓存灌到下拉里 · 进页 / 客户列表更新后调
    function _refreshExcClientFilter() {
        const sel = document.getElementById('exc-client-filter');
        if (!sel) return;
        const list = window._clientsCache || [];
        const cur = _excState.currentClient || '';
        const allLabel = typeof t === 'function' ? t('history-client-all') : '全部客户';
        sel.innerHTML =
            `<option value="">${escapeHtml(allLabel)}</option>` +
            list.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
        sel.value = cur;
    }

    window.loadExceptionsPage = async function () {
        if (_excState.loading) return;
        _excState.loading = true;
        try {
            _refreshExcClientFilter();
            // ERP 推送异常(独立来源 · 派生自 erp_push_logs)· 先加载 · 与 OCR 异常并存
            // ERP 推送异常块已抽出至 erp-exceptions.js · 经 window 桥接调用
            if (typeof window.loadErpExceptions === 'function') window.loadErpExceptions();
            await loadExceptionsStats();
            await loadExceptionsList();
        } finally {
            _excState.loading = false;
        }
    };

    // ERP 推送异常块(原 L428-1089)已抽出 → src/home/erp-exceptions.js(REFACTOR-WB-C1)

    // 暴露红点刷新 · 启动时 + 周期调用
    window.refreshExcBadge = refreshExcBadge;
    // v118.21.0 · 客户列表加载完毕后给异常栏刷下拉
    window._refreshExcClientFilter = _refreshExcClientFilter;
    // v118.28.0 · 暴露状态给顶栏客户切换器联动
    window._excState = _excState;

    // 切语言时用缓存重渲(不发请求 · 即时无闪烁)
    window._rerenderExceptions = function () {
        // v118.21.0.1 · 客户下拉的「全部客户」选项也是 t() 渲染 · 切语言要刷
        try {
            _refreshExcClientFilter();
        } catch (_) {
            /* silent · 通知下游刷新 */
        }
        if (_excState.statsCache) {
            renderKpis(_excState.statsCache);
            renderChips(_excState.statsCache);
        }
        if (_excState.listCache && _excState.listCache.length) {
            renderList(_excState.listCache);
        }
        // ERP 推送异常块也跟着切语言重渲(用缓存 · 不发请求)
        try {
            if (
                window._erpExcState &&
                window._erpExcState.items &&
                window._erpExcState.items.length &&
                typeof window._rerenderErpExceptions === 'function'
            )
                window._rerenderErpExceptions();
        } catch (_) {}
        // 抽屉打开时也跟着重渲
        if (_drawer.openExcId) renderDrawer();
    };

    // ─────────────────────────────────────────────────────────
    // v118.20.3 · 阶段 3 · 抽屉(详情 + 复核动作 + 学习)
    // ─────────────────────────────────────────────────────────
    let _drawer = {
        openExcId: null, // 当前打开的 exception id
        excRow: null, // 列表里的那条数据(快照)
        history: null, // /api/history/{hid} 拉到的完整字段
        loading: false,
        // v118.20.7 · PDF 预览
        pdfUrl: null, // blob URL · close 时 revoke
        pdfStatus: 'idle', // idle | loading | ready | empty | error
        // v118.21.3 · 字段编辑
        editing: false,
        editFields: null, // 编辑模式下的临时字段 · 保存时写回 history.pages[primary].fields
    };

    function _revokeDrawerPdf() {
        if (_drawer.pdfUrl) {
            try {
                URL.revokeObjectURL(_drawer.pdfUrl);
            } catch (_) {
                /* silent · 已 revoke */
            }
            _drawer.pdfUrl = null;
        }
        _drawer.pdfStatus = 'idle';
    }

    async function _loadDrawerPdf(hid, expectId) {
        _drawer.pdfStatus = 'loading';
        renderDrawer();
        try {
            const resp = await fetch('/api/history/' + encodeURIComponent(hid) + '/pdf', {
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            // 抽屉已切到下一条 · 丢弃这次结果
            if (_drawer.openExcId !== expectId) return;
            if (resp.status === 404) {
                _drawer.pdfStatus = 'empty';
                renderDrawer();
                return;
            }
            if (!resp.ok) throw new Error('http ' + resp.status);
            const blob = await resp.blob();
            if (_drawer.openExcId !== expectId) return; // 切走了
            _revokeDrawerPdf(); // 防上一条 url 残留
            _drawer.pdfUrl = URL.createObjectURL(blob);
            _drawer.pdfStatus = 'ready';
            renderDrawer();
        } catch (e) {
            if (_drawer.openExcId !== expectId) return;
            console.warn('loadDrawerPdf fail', e);
            _drawer.pdfStatus = 'error';
            renderDrawer();
        }
    }

    function openExcDrawer(excId) {
        const row = (_excState.listCache || []).find((r) => r.id === excId);
        if (!row) {
            showToast(t('exc-drawer-error'), 'error');
            return;
        }
        // v118.20.5 · 抽屉关闭后回到原 scroll 位置
        _excState.listScrollY = window.scrollY || document.documentElement.scrollTop || 0;
        // v118.20.7 · 切到新一条 · 释放上一条的 blob URL
        _revokeDrawerPdf();
        // v118.21.3 · 切条目时退出编辑态
        _drawer.editing = false;
        _drawer.editFields = null;
        _drawer.openExcId = excId;
        _drawer.excRow = row;
        _drawer.history = null;
        document.getElementById('exc-drawer-mask').classList.add('show');
        document.getElementById('exc-drawer').classList.add('show');
        renderDrawer(); // 先渲染骨架(showing loading on history section)
        loadHistoryDetail(row.history_id);
        _loadDrawerPdf(row.history_id, excId);
    }

    function closeExcDrawer() {
        _revokeDrawerPdf(); // v118.20.7 · 防内存泄漏
        // v118.21.3 · 关抽屉清编辑态
        _drawer.editing = false;
        _drawer.editFields = null;
        _drawer.openExcId = null;
        _drawer.excRow = null;
        _drawer.history = null;
        document.getElementById('exc-drawer-mask').classList.remove('show');
        document.getElementById('exc-drawer').classList.remove('show');
        // v118.20.5 · 还原 scroll(下一帧 · 等抽屉收起)
        const y = _excState.listScrollY || 0;
        if (y > 0) requestAnimationFrame(() => window.scrollTo(0, y));
    }

    async function loadHistoryDetail(hid) {
        try {
            const resp = await fetch('/api/history/' + encodeURIComponent(hid), {
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            _drawer.history = await resp.json();
        } catch (e) {
            console.warn('loadHistoryDetail fail', e);
            _drawer.history = { _err: true };
        }
        // 只有当抽屉还打开着这条 · 才渲(用户可能已经关了)
        if (_drawer.excRow) renderDrawer();
    }

    // 从 history.pages 抽出主页字段(后端 mergeFields 等价 · 简化版)
    function _extractFields(history) {
        if (!history || !history.pages) return {};
        const pages = history.pages;
        const primary = pages.find((p) => !p.is_duplicate && !p.is_copy) || pages[0];
        return (primary && primary.fields) || {};
    }

    function _v(s) {
        if (s === null || s === undefined || String(s).trim() === '') {
            return `<span class="empty">${escapeHtml(t('exc-empty-val'))}</span>`;
        }
        return escapeHtml(String(s));
    }

    function _money(n) {
        if (n === null || n === undefined) return '—';
        const v = typeof n === 'number' ? n : parseFloat(String(n).replace(/,/g, ''));
        if (isNaN(v)) return escapeHtml(String(n));
        return (
            '฿ ' +
            v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        );
    }

    // 「为什么被拦」详情段 · 根据 rule_code 把 detail_json 渲成人话
    function renderWhyDetail(rule, detail) {
        detail = detail || {};
        if (rule === 'math_mismatch') {
            return `
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-fld-subtotal'))}</b><span>${escapeHtml(_money(detail.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-fld-vat'))}</b><span>${escapeHtml(_money(detail.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-expected'))}</b><span class="v-good">${escapeHtml(_money(detail.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-actual'))}</b><span class="v-bad">${escapeHtml(_money(detail.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-diff'))}</b><span class="v-bad">${escapeHtml(_money(detail.diff))}</span></div>
            `;
        }
        if (rule === 'tax_id_format_invalid') {
            return `
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-fld-seller-tax'))}</b><span class="v-bad">${escapeHtml(detail.tax_id_normalized || detail.tax_id_raw || '—')}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-tax-len'))}</b><span class="v-bad">${escapeHtml(String(detail.actual_length || '?'))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-expected'))}</b><span class="v-good">${escapeHtml(t('exc-detail-tax-expected'))}</span></div>
            `;
        }
        if (rule === 'duplicate') {
            const lvl =
                detail.level === 'exact'
                    ? t('exc-detail-dup-level-exact')
                    : t('exc-detail-dup-level-likely');
            return `
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-dup-match'))}</b><span>${escapeHtml(detail.match_filename || '—')}</span></div>
                ${detail.match_invoice_no ? `<div class="exc-why-detail-row"><b>${escapeHtml(t('exc-fld-invoice-no'))}</b><span>${escapeHtml(detail.match_invoice_no)}</span></div>` : ''}
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-expected'))}</b><span>${escapeHtml(lvl)}</span></div>
            `;
        }
        if (rule === 'confidence_low') {
            return `
                <div class="exc-why-detail-row"><b>${escapeHtml(t('exc-detail-conf-label'))}</b><span class="v-bad">${escapeHtml(detail.confidence || '—')}</span></div>
            `;
        }
        if (rule === 'amount_missing') {
            return `<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t('exc-detail-missing'))}</span></div>`;
        }
        // 兜底:JSON 直出
        return `<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(detail))}</span></div>`;
    }

    function renderDrawer() {
        const row = _drawer.excRow;
        if (!row) return;

        // Header
        const seller =
            row.seller_name && row.seller_name.trim() ? row.seller_name : t('exc-no-seller');
        const filename = row.filename || '—';
        document.getElementById('exc-drawer-title').textContent = filename;

        const statusKey = 'exc-status-' + (row.status || 'pending');
        const statusLabel = t(statusKey) || row.status;
        const statusCls = 's-' + (row.status || 'pending');
        const date = (row.invoice_date || row.created_at || '').slice(0, 10);
        document.getElementById('exc-drawer-sub').innerHTML = `
            <span>${escapeHtml(seller)}</span>
            ${row.invoice_no ? `<span>· ${escapeHtml(row.invoice_no)}</span>` : ''}
            ${date ? `<span>· ${escapeHtml(date)}</span>` : ''}
            <span class="exc-status-chip ${statusCls}">${escapeHtml(statusLabel)}</span>
        `;

        // Body · 两段
        const sev = row.severity || 'medium';
        const ruleLabel = t('exc-rule-' + row.rule_code) || row.rule_code;
        const whyDetail = renderWhyDetail(row.rule_code, row.detail || {});

        const f = _extractFields(_drawer.history);
        const fieldsLoading = _drawer.history === null;
        const fieldsErr = _drawer.history && _drawer.history._err;

        // 标记哪些字段触发了规则(高亮红)
        const flagSet = new Set();
        if (row.rule_code === 'math_mismatch') {
            flagSet.add('subtotal');
            flagSet.add('vat');
            flagSet.add('total_amount');
        } else if (row.rule_code === 'tax_id_format_invalid') {
            flagSet.add('seller_tax');
        } else if (row.rule_code === 'amount_missing') {
            flagSet.add('total_amount');
            flagSet.add('invoice_number');
        }

        const editing = !!_drawer.editing;
        const editF = _drawer.editFields || {};
        const fld = (key, labelKey, isMoney) => {
            if (fieldsLoading) {
                return `<div class="exc-field-row"><label>${escapeHtml(t(labelKey))}</label><span class="val empty">…</span></div>`;
            }
            const v = editing
                ? editF[key] !== undefined
                    ? editF[key]
                    : f[key] !== undefined && f[key] !== null
                      ? f[key]
                      : ''
                : f[key];
            const flagged = flagSet.has(key) ? 'flagged' : '';
            if (editing) {
                const inputType = isMoney ? 'number' : 'text';
                const stepAttr = isMoney ? ' step="0.01" inputmode="decimal"' : '';
                const safeVal =
                    v === null || v === undefined ? '' : String(v).replace(/"/g, '&quot;');
                return `<div class="exc-field-row ${flagged} editing">
                    <label>${escapeHtml(t(labelKey))}</label>
                    <input class="exc-field-input" type="${inputType}"${stepAttr} data-edit-key="${escapeHtml(key)}" value="${safeVal}">
                </div>`;
            }
            const display = isMoney ? _money(v) : v || '';
            const valHtml =
                v === null || v === undefined || v === ''
                    ? `<span class="val empty">${escapeHtml(t('exc-empty-val'))}</span>`
                    : `<span class="val">${escapeHtml(display)}</span>`;
            return `<div class="exc-field-row ${flagged}"><label>${escapeHtml(t(labelKey))}</label>${valHtml}</div>`;
        };

        let fieldsHtml = '';
        if (fieldsErr) {
            fieldsHtml = `<div class="exc-drawer-error">${escapeHtml(t('exc-drawer-error'))}</div>`;
        } else {
            fieldsHtml = `
                <div class="exc-fields">
                    ${fld('invoice_number', 'exc-fld-invoice-no', false)}
                    ${fld('date', 'exc-fld-date', false)}
                    ${fld('seller_name', 'exc-fld-seller', false)}
                    ${fld('seller_tax', 'exc-fld-seller-tax', false)}
                    ${fld('buyer_name', 'exc-fld-buyer', false)}
                    ${fld('buyer_tax', 'exc-fld-buyer-tax', false)}
                    ${fld('subtotal', 'exc-fld-subtotal', true)}
                    ${fld('vat', 'exc-fld-vat', true)}
                    ${fld('total_amount', 'exc-fld-total', true)}
                </div>
            `;
        }

        // v118.20.7 · 左栏 PDF 预览(blob URL · 状态机)
        const pdfPaneHtml = (() => {
            if (_drawer.pdfStatus === 'loading' || _drawer.pdfStatus === 'idle') {
                return `
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t('exc-pdf-loading'))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M18 4v8a14 14 0 1014 14"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t('exc-pdf-loading'))}</div>
                    </div>
                `;
            }
            if (_drawer.pdfStatus === 'empty') {
                return `
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t('exc-pdf-empty-title'))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M9 4h12l6 6v22H9z"/>
                            <path d="M21 4v6h6"/>
                            <line x1="14" y1="20" x2="22" y2="20"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t('exc-pdf-empty'))}</div>
                    </div>
                `;
            }
            if (_drawer.pdfStatus === 'error') {
                return `
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t('exc-pdf-error-title'))}</span>
                        <div class="exc-pdf-toolbar-actions">
                            <button class="exc-pdf-icon-btn" id="exc-pdf-retry" title="${escapeHtml(t('exc-pdf-retry'))}" type="button">
                                <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M2 7a5 5 0 019-3l1.5 1.5M12 7a5 5 0 01-9 3L1.5 8.5M12 2v3h-3M2 12V9h3"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="18" cy="18" r="14"/>
                            <line x1="18" y1="11" x2="18" y2="20"/>
                            <circle cx="18" cy="24" r="0.8" fill="currentColor"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t('exc-pdf-error'))}</div>
                    </div>
                `;
            }
            // ready
            const url = _drawer.pdfUrl;
            return `
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(filename)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${url}" target="_blank" rel="noopener" title="${escapeHtml(t('exc-pdf-open-tab'))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${url}" download="${escapeHtml(filename)}" title="${escapeHtml(t('exc-pdf-download'))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                            </svg>
                        </a>
                    </div>
                </div>
                <iframe class="exc-pdf-frame" src="${url}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
            `;
        })();

        document.getElementById('exc-drawer-body').innerHTML = `
            <div class="exc-pdf-pane">${pdfPaneHtml}</div>
            <div class="exc-fields-pane">
                <div class="exc-section">
                    <div class="exc-section-title">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="7" cy="7" r="5.5"/><line x1="7" y1="4" x2="7" y2="7.5"/>
                            <circle cx="7" cy="9.6" r="0.5" fill="currentColor"/>
                        </svg>
                        <span>${escapeHtml(t('exc-sect-why'))}</span>
                    </div>
                    <div class="exc-why sev-${escapeHtml(sev)}">
                        <div class="exc-why-rule">${escapeHtml(ruleLabel)}</div>
                        <div class="exc-why-detail">${whyDetail}</div>
                    </div>
                </div>
                <div class="exc-section">
                    <div class="exc-section-title">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="2" y="2.5" width="10" height="9" rx="1"/>
                            <line x1="4" y1="5.5" x2="10" y2="5.5"/>
                            <line x1="4" y1="8.5" x2="10" y2="8.5"/>
                        </svg>
                        <span>${escapeHtml(t('exc-sect-fields'))}</span>
                        ${
                            row.status === 'pending' && !fieldsLoading && !fieldsErr
                                ? editing
                                    ? `
                                <span class="exc-section-actions">
                                    <button class="exc-edit-btn ghost" id="exc-fld-cancel" type="button">${escapeHtml(t('exc-fld-cancel'))}</button>
                                    <button class="exc-edit-btn primary" id="exc-fld-save" type="button">${escapeHtml(t('exc-fld-save'))}</button>
                                </span>
                            `
                                    : `
                                <span class="exc-section-actions">
                                    <button class="exc-edit-btn ghost" id="exc-fld-edit" type="button">
                                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M2.5 11.5l1-3 6.5-6.5 2 2-6.5 6.5z"/>
                                            <path d="M9 2.5l2 2"/>
                                        </svg>
                                        <span>${escapeHtml(t('exc-fld-edit'))}</span>
                                    </button>
                                </span>
                            `
                                : ''
                        }
                    </div>
                    ${fieldsHtml}
                </div>
            </div>
        `;

        // v118.21.3 · 编辑模式按钮事件
        const editBtn = document.getElementById('exc-fld-edit');
        if (editBtn)
            editBtn.addEventListener('click', () => {
                _drawer.editing = true;
                _drawer.editFields = { ..._extractFields(_drawer.history) };
                renderDrawer();
            });
        const cancelBtn = document.getElementById('exc-fld-cancel');
        if (cancelBtn)
            cancelBtn.addEventListener('click', () => {
                _drawer.editing = false;
                _drawer.editFields = null;
                renderDrawer();
            });
        const saveBtn = document.getElementById('exc-fld-save');
        if (saveBtn) saveBtn.addEventListener('click', () => actionSaveFields());
        // 输入收集到 _drawer.editFields(逐字符同步 · 防 renderDrawer 重渲丢值)
        const inputs = document.querySelectorAll('.exc-field-input');
        inputs.forEach((inp) => {
            inp.addEventListener('input', () => {
                if (!_drawer.editFields) _drawer.editFields = {};
                _drawer.editFields[inp.dataset.editKey] = inp.value;
            });
        });

        // PDF 重试按钮
        const pdfRetry = document.getElementById('exc-pdf-retry');
        if (pdfRetry && _drawer.openExcId) {
            pdfRetry.addEventListener('click', () => {
                if (_drawer.excRow) _loadDrawerPdf(_drawer.excRow.history_id, _drawer.openExcId);
            });
        }

        // 底部按钮 · 仅 pending 可操作
        const isPending = row.status === 'pending';
        const hasSeller = !!(row.seller_name && row.seller_name.trim());
        const btnResolve = document.getElementById('exc-btn-resolve');
        const btnIgnore = document.getElementById('exc-btn-ignore');
        btnResolve.disabled = !isPending;
        btnIgnore.disabled = !isPending || !hasSeller;
        // 「忽略此类」副提示(在按钮上方 · 用 title attr)
        btnIgnore.title = hasSeller ? t('exc-ignore-hint') : t('exc-ignore-no-seller');
    }

    // v118.21.3 · 保存字段编辑 · 调 PUT /api/history/{id} · 后端会自动重跑规则
    async function actionSaveFields() {
        if (!_drawer.openExcId || !_drawer.history || !_drawer.history.pages) return;
        if (_drawer.loading) return;
        _drawer.loading = true;
        const dismiss = showToast(t('exc-fld-saving'), 'loading', 0);
        try {
            // 把 editFields 写入 primary page 的 fields(数字字段转 number · 空字符串转 null)
            const pages = JSON.parse(JSON.stringify(_drawer.history.pages || []));
            let primaryIdx = pages.findIndex((p) => !p.is_duplicate && !p.is_copy);
            if (primaryIdx < 0) primaryIdx = 0;
            if (!pages[primaryIdx]) pages[primaryIdx] = { fields: {} };
            const oldFields = pages[primaryIdx].fields || {};
            const ef = _drawer.editFields || {};
            const moneyKeys = new Set(['subtotal', 'vat', 'total_amount']);
            const newFields = { ...oldFields };
            for (const k in ef) {
                let v = ef[k];
                if (v === '' || v === undefined) v = null;
                if (moneyKeys.has(k) && v !== null) {
                    const n = parseFloat(v);
                    v = isNaN(n) ? null : n;
                }
                newFields[k] = v;
            }
            pages[primaryIdx].fields = newFields;
            const resp = await fetch('/api/history/' + encodeURIComponent(_drawer.history.id), {
                method: 'PUT',
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ pages }),
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            dismiss();
            showToast(t('exc-fld-save-ok'), 'success');
            // 关抽屉(因为这条异常可能消失了 · 留着也是错的状态)+ 刷列表 + KPI + 徽章
            closeExcDrawer();
            await loadExceptionsStats();
            await loadExceptionsList();
            refreshExcBadge();
        } catch (e) {
            dismiss();
            console.warn('save fields fail', e);
            showToast(t('exc-fld-save-fail'), 'error');
        } finally {
            _drawer.loading = false;
        }
    }

    async function actionResolve() {
        if (!_drawer.openExcId || _drawer.loading) return;
        _drawer.loading = true;
        try {
            const resp = await fetch('/api/exceptions/' + _drawer.openExcId + '/resolve', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            showToast(t('exc-toast-resolved'), 'success');
            closeExcDrawer();
            // 重新拉 stats + list · 列表里这条会消失(默认 status=pending 过滤)
            await loadExceptionsStats();
            await loadExceptionsList();
            refreshExcBadge();
        } catch (e) {
            console.warn('resolve fail', e);
            showToast(t('exc-toast-action-fail'), 'error');
        } finally {
            _drawer.loading = false;
        }
    }

    async function actionIgnore() {
        if (!_drawer.openExcId || _drawer.loading) return;
        _drawer.loading = true;
        try {
            const resp = await fetch('/api/exceptions/' + _drawer.openExcId + '/ignore', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            showToast(t('exc-toast-ignored'), 'success');
            closeExcDrawer();
            await loadExceptionsStats();
            await loadExceptionsList();
            refreshExcBadge();
        } catch (e) {
            console.warn('ignore fail', e);
            showToast(t('exc-toast-action-fail'), 'error');
        } finally {
            _drawer.loading = false;
        }
    }

    // v118.20.5 · 批量复核
    let _batchLoading = false;
    async function actionBatchResolve() {
        if (_batchLoading) return;
        const ids = Array.from(_excState.selectedIds);
        if (ids.length === 0) return;
        const ok = await showConfirm(_tn('exc-batch-confirm-resolve', { n: ids.length }));
        if (!ok) return;
        _batchLoading = true;
        const dismiss = showToast(_tn('exc-batch-count', { n: ids.length }) + ' …', 'loading', 0);
        try {
            const resp = await fetch('/api/exceptions/batch', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ids, action: 'resolve' }),
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            const data = await resp.json();
            dismiss();
            showToast(_tn('exc-toast-batch-resolved', { n: data.processed || 0 }), 'success');
            _excState.selectedIds.clear();
            await loadExceptionsStats();
            await loadExceptionsList();
            refreshExcBadge();
        } catch (e) {
            dismiss();
            console.warn('batch resolve fail', e);
            showToast(t('exc-toast-batch-fail'), 'error');
        } finally {
            _batchLoading = false;
        }
    }

    async function actionBatchIgnore() {
        if (_batchLoading) return;
        const ids = Array.from(_excState.selectedIds);
        if (ids.length === 0) return;
        const ok = await showConfirm(_tn('exc-batch-confirm-ignore', { n: ids.length }), {
            danger: false,
        });
        if (!ok) return;
        _batchLoading = true;
        const dismiss = showToast(_tn('exc-batch-count', { n: ids.length }) + ' …', 'loading', 0);
        try {
            const resp = await fetch('/api/exceptions/batch', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ids, action: 'ignore' }),
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            const data = await resp.json();
            dismiss();
            showToast(
                _tn('exc-toast-batch-ignored', {
                    n: data.processed || 0,
                    wl: data.whitelist_added || 0,
                }),
                'success'
            );
            _excState.selectedIds.clear();
            await loadExceptionsStats();
            await loadExceptionsList();
            refreshExcBadge();
        } catch (e) {
            dismiss();
            console.warn('batch ignore fail', e);
            showToast(t('exc-toast-batch-fail'), 'error');
        } finally {
            _batchLoading = false;
        }
    }

    function clearBatchSelection() {
        _excState.selectedIds.clear();
        // 重渲列表(摘掉 selected 态)· 不发请求
        renderList(_excState.listCache);
    }

    // 抽屉事件接线(deferred · 等 DOM 就绪)
    document.addEventListener('click', (e) => {
        if (e.target.closest('#exc-drawer-close')) closeExcDrawer();
        if (e.target.closest('#exc-drawer-mask')) closeExcDrawer();
        if (e.target.closest('#exc-btn-resolve')) actionResolve();
        if (e.target.closest('#exc-btn-ignore')) actionIgnore();
        // v118.20.5 · 批量栏 + 加载更多
        if (e.target.closest('#exc-batch-resolve')) actionBatchResolve();
        if (e.target.closest('#exc-batch-ignore')) actionBatchIgnore();
        if (e.target.closest('#exc-batch-clear')) clearBatchSelection();
        if (e.target.closest('#exc-loadmore')) loadMore();
    });
    // ESC 关抽屉
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && _drawer.openExcId) closeExcDrawer();
    });

    // 「刷新」按钮(页内)
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('#btn-exc-refresh');
        if (!btn) return;
        if (typeof window.loadExceptionsPage === 'function') window.loadExceptionsPage();
        refreshExcBadge();
    });

    // v118.21.0 · 客户筛选切换 · 重置 chip / 选中 · 重拉数据
    document.addEventListener('change', (e) => {
        if (!e.target.closest('#exc-client-filter')) return;
        const sel = e.target;
        _excState.currentClient = sel.value || '';
        _excState.currentRule = null; // 切客户后还原全部规则 chip
        _excState.selectedIds.clear(); // 清空多选(列表会变)
        _excState.listCache = [];
        if (typeof window.loadExceptionsPage === 'function') window.loadExceptionsPage();
        refreshExcBadge();
    });

    // v118.21.1 · status tab 切换(待复核 / 已处理 / 已忽略)
    document.addEventListener('click', (e) => {
        const tab = e.target.closest('#exc-status-tabs .exc-status-tab');
        if (!tab) return;
        const newStatus = tab.dataset.status || 'pending';
        if (newStatus === _excState.currentStatus) return;
        _excState.currentStatus = newStatus;
        _excState.currentRule = null; // 切状态后还原全部规则 chip
        _excState.selectedIds.clear(); // 清多选
        _excState.listCache = [];
        if (typeof window.loadExceptionsPage === 'function') window.loadExceptionsPage();
    });

    // v118.20.5 · 网络恢复时 · 若上次加载失败 · 自动重试
    window.addEventListener('online', () => {
        if (
            _excState.loadFailed &&
            document.getElementById('page-exceptions')?.classList.contains('show')
        ) {
            window.loadExceptionsPage && window.loadExceptionsPage();
        }
    });

    // 启动后立即拉一次徽章数 · 每 60 秒刷一次
    setTimeout(refreshExcBadge, 1500);
    setInterval(refreshExcBadge, 60000);

    // ============================================================
    // v118.21.2 · 设置页 · 学习规则面板(列出 / 撤销已学的白名单)
    // ============================================================
    function _shortDateTime(iso) {
        if (!iso) return '—';
        try {
            const d = new Date(iso);
            const pad = (n) => String(n).padStart(2, '0');
            return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
        } catch (_) {
            return iso.slice(0, 16).replace('T', ' ');
        }
    }

    async function loadLearnedRules() {
        const wrap = document.getElementById('learned-list');
        if (!wrap) return;
        wrap.innerHTML = `<div class="learned-empty">${escapeHtml(t('set-learned-loading'))}</div>`;
        try {
            const resp = await fetch('/api/exception-whitelist', {
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            const data = await resp.json();
            const items = data.items || [];
            if (items.length === 0) {
                wrap.innerHTML = `<div class="learned-empty">${escapeHtml(t('set-learned-empty'))}</div>`;
                return;
            }
            const trashSvg = `<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;
            wrap.innerHTML = items
                .map((it) => {
                    const ruleLabel = t('exc-rule-' + it.rule_code) || it.rule_code;
                    return `
                    <div class="learned-row" data-wl-id="${escapeHtml(String(it.id))}">
                        <div class="learned-seller" title="${escapeHtml(it.seller_name)}">${escapeHtml(it.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(ruleLabel)}</div>
                        <div class="learned-date">${escapeHtml(_shortDateTime(it.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(it.id))}" title="${escapeHtml(t('set-learned-del'))}" type="button">${trashSvg}</button>
                    </div>
                `;
                })
                .join('');
        } catch (e) {
            console.warn('loadLearnedRules fail', e);
            wrap.innerHTML = `<div class="learned-empty">${escapeHtml(t('exc-toast-load-fail'))}</div>`;
        }
    }
    window.loadLearnedRules = loadLearnedRules;

    // 删除按钮事件(委托)
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('[data-del-wl]');
        if (!btn) return;
        const wlId = parseInt(btn.dataset.delWl, 10);
        if (!wlId) return;
        const row = btn.closest('.learned-row');
        const sellerEl = row && row.querySelector('.learned-seller');
        const sellerName = sellerEl ? sellerEl.textContent.trim() : '';
        const msg = t('set-learned-del-confirm').replace('{seller}', sellerName);
        const ok = await showConfirm(msg, { danger: true });
        if (!ok) return;
        try {
            const resp = await fetch('/api/exception-whitelist/' + wlId, {
                method: 'DELETE',
                headers: {
                    Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                },
            });
            if (!resp.ok) throw new Error('http ' + resp.status);
            showToast(t('set-learned-del-ok'), 'success');
            loadLearnedRules();
            // 异常栏徽章可能不变(只删白名单 · 不复活拦截)· 但学习规则数变 · 刷一次 stats
            if (
                typeof window.loadExceptionsPage === 'function' &&
                document.getElementById('page-exceptions')?.classList.contains('show')
            ) {
                window.loadExceptionsPage();
            }
        } catch (err) {
            console.warn('delete whitelist fail', err);
            showToast(t('set-learned-del-fail'), 'error');
        }
    });
})();
