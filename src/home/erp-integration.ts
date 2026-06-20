// Pearnly home · ERP 集成页(推送日志+端点)· REFACTOR-C1 copy-out
// ============================================================
// 来源:home.js 的「ERP 集成页函数群」(推送日志 + 端点管理)
//   推送日志:loadErpLogs / _refreshErpBatchBar / _runErpBatchRetry /
//     _runErpBatchDelete / copyErpDocNo / showLogDetail / retryPushLog
//   端点管理:loadErpEndpoints / loadErpTodayStats / renderErpEndpointsList /
//     openEndpointModal / closeEndpointModal / _sanitizeUrl / readEndpointForm /
//     testEndpointConnection / saveEndpoint / showEpSaveError / deleteEndpoint
//
// 加载顺序:home.html <script src=home.js>(sync)先跑 → 本 module(Vite bundle ·
//   type=module defer)后跑 · 所以 home.js 暴露的全局(t / escapeHtml / token /
//   showToast / showConfirm / humanizeError / currentLang / _userInfo /
//   routeTo / switchAutomationTab / _showSessionRevokedModal)在本 module 执行时已就绪。
//
// 自带内存(只被本组用 · 随函数搬进模块):
//   _erpEndpoints / _epEditingId / _logFilter / _erpSelected
//   注:home.js 核心 + injectOcrPushButton 经 window._erpEndpoints 读取缓存 ·
//   本模块每次 loadErpEndpoints 都写 window._erpEndpoints = _erpEndpoints 保持桥接。
// ============================================================

/* global escapeHtml, token, showConfirm, humanizeError, currentLang, routeTo, switchAutomationTab, _showSessionRevokedModal */

let _logFilter = { key: 'all', val: '' };
// DMS 推送可视化闭环(Zihao 2026-06-01)· ERP 系统筛选 = 下拉(adapter)· 独立于 status/trigger chip ·
// 选中 mrerp_dms(身份证订车)时表头/行切到 DMS 字段(订车单号/客户)· 不再用发票字段框。
let _erpAdapter = '';
let _erpLogBusiness = ''; // 业务类型下拉(全部业务 / id_card / invoice)
let _erpLogKeyword = ''; // 日志搜索(单据号 / 卖方)
let _erpSelectReady = false;
// v118.25.1 · 推送日志多选状态(批量重推)
let _erpSelected = new Set();
window._erpSelected = _erpSelected;

// DMS 推送可视化闭环(Zihao 2026-06-01)· 推送日志 ERP 筛选 = 下拉「真实配置的 ERP 端点」·
// 不再硬编码 adapter 列表。按 adapter 去重(后端按 adapter 过滤)· 标签用端点名。
// 懒填一次(loadErpLogs 首次调)· 失败回滚允许重试。
async function _ensureErpSelectOptions() {
    const sel = document.getElementById('erp-logs-erp-select');
    if (!sel || _erpSelectReady) return;
    _erpSelectReady = true;
    try {
        let eps = window._erpEndpoints;
        if (!Array.isArray(eps) || eps.length === 0) {
            const r = await fetch('/api/erp/endpoints', {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (r.ok) {
                const d = await r.json();
                eps = (d && (d.items || d)) || [];
            }
        }
        if (!Array.isArray(eps)) eps = [];
        const seen = new Set();
        const opts: { val: string; label: string }[] = [];
        (eps as any[]).forEach((e) => {
            const ad = (((e && e.adapter) || '') as string).toLowerCase();
            if (!ad || seen.has(ad)) return;
            seen.add(ad);
            opts.push({ val: ad, label: (e && e.name) || ad });
        });
        sel.innerHTML =
            `<option value="">${escapeHtml(t('erp-logs-erp-all'))}</option>` +
            opts
                .map(
                    (o) =>
                        `<option value="${escapeHtml(o.val)}"${o.val === _erpAdapter ? ' selected' : ''}>${escapeHtml(o.label)}</option>`
                )
                .join('');
    } catch (e) {
        _erpSelectReady = false; // 允许下次重试
    }
}

async function loadErpLogs(silent?: boolean) {
    const listEl = document.getElementById('erp-logs-list');
    if (!listEl) return;

    // v0.10 · 立即显示 loading 态 · 让用户知道点到了(silent=自动轮询刷新·不闪 loading)
    if (!silent)
        listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-loading'))}</div>`;

    // 今日统计同步刷新(不等)
    window.loadErpTodayStats();
    // ERP 系统下拉(真实配置端点)· 懒填一次
    _ensureErpSelectOptions();

    try {
        const params = new URLSearchParams({ limit: '30' });
        if (_logFilter.key === 'status') params.set('status', _logFilter.val);
        if (_logFilter.key === 'trigger') params.set('trigger', _logFilter.val);
        // DMS 推送可视化闭环 · ERP 系统筛选改下拉(_erpAdapter)· 与 status/trigger chip 独立组合
        if (_erpAdapter) params.set('adapter', _erpAdapter);
        if (_erpLogBusiness) params.set('push_type', _erpLogBusiness);
        if (_erpLogKeyword) params.set('keyword', _erpLogKeyword);
        const resp = await fetch(`/api/erp/logs?${params}`, {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) {
            listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
            return;
        }
        const data = await resp.json();
        const items = data.items || [];
        // 有「推送中(pending)」行 → 4s 后静默再拉一次 · 让状态原地翻成 ✓/✗(2026-05-26)·
        // 无 pending 或离开页面(下次 listEl 不在直接 return)即自动停。
        if (window._erpLogPollTimer) {
            clearTimeout(window._erpLogPollTimer);
            window._erpLogPollTimer = null;
        }
        if (
            items.some(function (l: any) {
                return l.status === 'pending';
            })
        ) {
            window._erpLogPollTimer = setTimeout(function () {
                loadErpLogs(true);
            }, 4000);
        }
        if (items.length === 0) {
            listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-empty'))}</div>`;
            return;
        }
        // 销项重做:日志行 → 草稿卡片(渲染搬到 erp-log-card.buildErpLogCard · data-log-* 不变)
        listEl.innerHTML = items
            .map((log: any) =>
                typeof window.buildErpLogCard === 'function' ? window.buildErpLogCard(log) : ''
            )
            .join('');
        // v118.25.1 · 重新渲染后 · 修剪掉已经不在列表里的选中项 + 刷新批量栏
        const visibleIds = new Set(items.map((x: any) => x.id));
        for (const id of Array.from(_erpSelected)) {
            if (!visibleIds.has(id)) _erpSelected.delete(id);
        }
        window._refreshErpBatchBar();
    } catch (e) {
        console.error('load erp logs failed', e);
        listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
    }
}

async function retryPushLog(logId: any) {
    try {
        const resp = await fetch(`/api/erp/logs/${encodeURIComponent(logId)}/retry`, {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token },
        });
        const data = await resp.json().catch(() => ({}));
        if (resp.ok && data.ok) {
            showToast(t('log-retry-ok'), 'success');
        } else {
            showToast(
                t('log-retry-fail') + ' · HTTP ' + (data.http_status || resp.status),
                'error'
            );
        }
        loadErpLogs();
        window.loadErpEndpoints();
    } catch (e) {
        showToast(t('log-retry-fail'), 'error');
    }
}

// 事件绑定
(function initAutomationPage() {
    // 点新增按钮
    document
        .getElementById('btn-add-endpoint')!
        .addEventListener('click', () => window.openEndpointModal(null));

    // 对话框关闭
    document
        .getElementById('endpoint-modal-close')!
        .addEventListener('click', window.closeEndpointModal);
    document.getElementById('btn-ep-cancel')!.addEventListener('click', window.closeEndpointModal);

    // 点遮罩不关闭(避免误触丢失填写的内容 · 只能通过关闭按钮/取消按钮关闭)

    // 测试连接
    document
        .getElementById('btn-ep-test')!
        .addEventListener('click', window.testEndpointConnection);

    // 保存
    document.getElementById('btn-ep-save')!.addEventListener('click', window.saveEndpoint);

    // v0.9.1 · URL 输入框失焦自动清理"Copy to clipboard"等粘贴糟粕
    document.getElementById('ep-url')!.addEventListener('blur', (e) => {
        const cleaned = window._sanitizeUrl((e.target as HTMLInputElement).value);
        if (cleaned !== (e.target as HTMLInputElement).value.trim()) {
            (e.target as HTMLInputElement).value = cleaned;
        }
    });

    // 列表里的编辑/删除按钮(事件委托)
    document.addEventListener('click', (e) => {
        const editBtn = (e.target as HTMLElement).closest('[data-ep-edit]') as HTMLElement | null;
        const delBtn = (e.target as HTMLElement).closest('[data-ep-del]') as HTMLElement | null;
        if (editBtn) window.openEndpointModal(editBtn.dataset.epEdit);
        if (delBtn) window.deleteEndpoint(delBtn.dataset.epDel);

        // v0.9.1 · 推送日志交互
        const retryBtn = (e.target as HTMLElement).closest('[data-log-retry]') as HTMLElement;
        if (retryBtn) {
            e.stopPropagation();
            retryPushLog(retryBtn.dataset.logRetry);
            return;
        }
        // v118.25.1 · 批量勾选
        const cb = (e.target as HTMLElement).closest('[data-log-cb]') as HTMLInputElement | null;
        if (cb) {
            e.stopPropagation();
            const id = cb.dataset.logCb;
            if (cb.checked) _erpSelected.add(id);
            else _erpSelected.delete(id);
            window._refreshErpBatchBar();
            return;
        }
        // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 表头全选 checkbox
        const selectAllCb = (e.target as HTMLElement).closest(
            '[data-log-select-all]'
        ) as HTMLInputElement | null;
        if (selectAllCb) {
            e.stopPropagation();
            const checkAll = selectAllCb.checked;
            const allCbs = document.querySelectorAll('[data-log-cb]');
            allCbs.forEach(function (rowCb: any) {
                rowCb.checked = checkAll;
                const id = rowCb.dataset.logCb;
                if (checkAll) _erpSelected.add(id);
                else _erpSelected.delete(id);
            });
            window._refreshErpBatchBar();
            return;
        }
        // v118.25.1 · 批量重推按钮
        if ((e.target as HTMLElement).closest('#btn-erp-batch-retry')) {
            e.stopPropagation();
            window._runErpBatchRetry();
            return;
        }
        // v118.25.1 · 取消选择
        if ((e.target as HTMLElement).closest('#btn-erp-batch-clear')) {
            e.stopPropagation();
            _erpSelected.clear();
            document.querySelectorAll('.erp-log-cb').forEach((x: any) => {
                x.checked = false;
            });
            window._refreshErpBatchBar();
            return;
        }
        const logRow = (e.target as HTMLElement).closest('[data-log-detail]') as HTMLElement | null;
        if (logRow) {
            // 点 checkbox 不算点 row
            if ((e.target as HTMLElement).closest('[data-log-cb]')) return;
            // 临时任务 (Zihao 2026-05-26) · 点 ERP 单号 → 复制 · 不打开详情
            const copyDocEl = (e.target as HTMLElement).closest(
                '[data-copy-doc]'
            ) as HTMLElement | null;
            if (copyDocEl) {
                e.stopPropagation();
                window.copyErpDocNo(copyDocEl.dataset.copyDoc);
                return;
            }
            // 点「打开」链接 → 让 <a> 默认在新标签打开 · 不打开详情
            if ((e.target as HTMLElement).closest('.log-doc-open')) return;
            window.showLogDetail(logRow.dataset.logDetail);
            return;
        }
        const filterChip = (e.target as HTMLElement).closest('.chip-filter') as HTMLElement | null;
        if (filterChip) {
            document
                .querySelectorAll('#erp-logs-filters .chip-filter')
                .forEach((c: Element) => c.classList.remove('active'));
            filterChip.classList.add('active');
            _logFilter = {
                key: filterChip.dataset.filterKey as string,
                val: filterChip.dataset.filterVal as string,
            };
            loadErpLogs();
            return;
        }
        if ((e.target as HTMLElement).closest('#btn-refresh-logs')) {
            const btn = (e.target as HTMLElement).closest('#btn-refresh-logs')!;
            btn.classList.add('spinning');
            setTimeout(() => btn.classList.remove('spinning'), 600);
            loadErpLogs();
            return;
        }

        // v0.10 · 自动化子菜单切换(guard: 只处理有 data-auto-tab 的按钮，防止对账中心等共用 .auto-nav-item 类名的按钮触发 switchAutomationTab(undefined))
        const autoNav = (e.target as HTMLElement).closest('.auto-nav-item') as HTMLElement | null;
        if (autoNav && autoNav.dataset.autoTab) {
            switchAutomationTab(autoNav.dataset.autoTab);
            return;
        }
    });

    // ERP 系统下拉 / 业务类型下拉切换 → 重新拉日志
    document.addEventListener('change', (e) => {
        const el = e.target as HTMLElement;
        if (el && el.id === 'erp-logs-erp-select') {
            _erpAdapter = (el as HTMLInputElement).value || '';
            loadErpLogs();
        } else if (el && el.id === 'erp-logs-business-select') {
            _erpLogBusiness = (el as HTMLInputElement).value || '';
            loadErpLogs();
        }
    });
    // 日志搜索框(草稿「搜索单据号、客户或任务」)· debounce
    let _logSearchTimer: ReturnType<typeof setTimeout> | null = null;
    document.addEventListener('input', (e) => {
        const el = e.target as HTMLElement;
        if (el && el.id === 'erp-logs-search') {
            _erpLogKeyword = (el as HTMLInputElement).value || '';
            if (_logSearchTimer) clearTimeout(_logSearchTimer);
            _logSearchTimer = setTimeout(() => loadErpLogs(), 350);
        }
    });
})();

// ============================================================
// 模块外调用入口(home.js routeTo / 核心 / 其它模块经 window 调)·
// 参照 test-center.js 末尾 window 暴露范式。
// ============================================================
window.loadErpLogs = loadErpLogs;
window.retryPushLog = retryPushLog;
// 深链:外部(如录入工作台身份证「查看记录」)按 adapter 筛推送日志(如 mrerp_dms)· 设值+同步下拉UI+刷新
window.setErpLogAdapter = function (adapter: string) {
    _erpAdapter = adapter || '';
    const sel = document.getElementById('erp-logs-erp-select') as HTMLSelectElement | null;
    if (sel) sel.value = _erpAdapter;
    loadErpLogs();
};
