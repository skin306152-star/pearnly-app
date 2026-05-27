// ============================================================
// REFACTOR-C1 (2026-05-27) · 对账历史多选批量删 recon-batch 从 home.js 抽出为 ES module
//
// 来源:home.js L21710-21990 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* eslint-disable no-useless-assignment -- verbatim home.js · 防御式初始化(var ok=false 后被覆盖)· 非 bug · 同 eslint.config 对 static 的判定 */
// ============================================================
// v118.32.5.5.22 · Gmail 风格 thead 就地切换 · 对账历史多选 + 批量删
// 默认 thead: 列标签 + master checkbox(最左)
// 选中 ≥1 → thead 整行替换为操作栏("已选 N 条 · 批量删除")· 同行高 · 不在表外
// 选中 0 → 还原默认 thead
// 销售税核查 (vex-task-table) + 收入对账 (glv-history-table) 共用同一套
// ============================================================
(function _reconBatchDeleteIIFE() {
    'use strict';
    function _t(k, fb) {
        try {
            return (window.t && window.t(k)) || fb;
        } catch (_) {
            return fb;
        }
    }
    function _esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function _authH() {
        var t = '';
        try {
            t = localStorage.getItem('mrpilot_token') || '';
        } catch (_) {}
        return t ? { Authorization: 'Bearer ' + t } : {};
    }

    var SELECTORS = [
        {
            tbody: 'vex-task-tbody',
            api: '/api/recon/tasks/batch_delete',
            reload: function () {
                try {
                    window.loadRecentTasks && window.loadRecentTasks();
                } catch (_) {}
            },
            kind: 'vex',
        },
        {
            tbody: 'glv-history-tbody',
            api: '/api/recon/gl-vat/tasks/batch_delete',
            reload: function () {
                try {
                    window._loadGlvHistory && window._loadGlvHistory();
                } catch (_) {}
            },
            kind: 'glv',
        },
        {
            tbody: 'brv2-history-tbody',
            api: '/api/recon/bank-v2/tasks/batch_delete',
            reload: function () {
                try {
                    window._brv2LoadHistory && window._brv2LoadHistory();
                } catch (_) {}
            },
            kind: 'brv2',
        },
    ];

    function _injectStyle() {
        if (document.getElementById('recon-batch-style')) return;
        var s = document.createElement('style');
        s.id = 'recon-batch-style';
        s.textContent =
            // checkbox 列(thead + tbody 共用)
            '.recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}' +
            '.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}' +
            // 时间列防压缩
            'th.recon-time-col,td.recon-time-col{white-space:nowrap}' +
            // Gmail thead 切换:default vs batch 互斥显示
            'tr.recon-thead-batch{display:none}' +
            'thead.recon-batch-mode tr.recon-thead-default{display:none}' +
            'thead.recon-batch-mode tr.recon-thead-batch{display:table-row}' +
            // batch 行视觉(浅暖灰底 · 同行高 · 内嵌按钮)
            'tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}' +
            'tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}' +
            'tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}' +
            'tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}' +
            'tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}' +
            'tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}' +
            'tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}' +
            // 隐藏老 banner(v5.5.20 残留 · 不再渲染但兼容老 DOM)
            '.recon-batch-bar{display:none!important}';
        document.head.appendChild(s);
    }

    function _getRowTaskId(tr) {
        if (!tr) return '';
        if (tr.dataset && tr.dataset.taskId) return tr.dataset.taskId;
        // vex-task 行另一个属性名
        if (tr.dataset && tr.dataset.taskid) return tr.dataset.taskid;
        return '';
    }

    // 给 thead 默认 tr 加 master checkbox 列 + 给"时间"列加 .recon-time-col(防压缩)
    function _injectThead(cfg) {
        var tbodyEl = document.getElementById(cfg.tbody);
        if (!tbodyEl) return null;
        var table = tbodyEl.closest('table');
        if (!table) return null;
        var thead = table.querySelector('thead');
        if (!thead) return null;
        if (thead._reconReady) return thead;
        var defaultTr = thead.querySelector('tr');
        if (!defaultTr) return null;
        defaultTr.classList.add('recon-thead-default');
        // master checkbox <th> 在最左
        if (!defaultTr.querySelector('.recon-master-cb')) {
            var th = document.createElement('th');
            th.className = 'recon-sel-cell';
            var cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.className = 'recon-master-cb';
            cb.setAttribute('aria-label', 'select all');
            cb.addEventListener('change', function () {
                _onMasterChange(cfg, cb.checked);
            });
            th.appendChild(cb);
            defaultTr.insertBefore(th, defaultTr.firstElementChild);
        }
        // "时间"列加 nowrap class(第 2 列 · 紧接 master checkbox)
        var timeTh = defaultTr.children[1];
        if (timeTh && !timeTh.classList.contains('recon-time-col'))
            timeTh.classList.add('recon-time-col');
        // batch tr(同 thead 内 · 默认 CSS 隐藏 · 切换时显示)
        var colsTotal = defaultTr.children.length; // 含 master 后总列数
        var batchTr = document.createElement('tr');
        batchTr.className = 'recon-thead-batch';
        var batchSelTh = document.createElement('th');
        batchSelTh.className = 'recon-sel-cell';
        // batch 行也放一个 master checkbox(联动)
        var bcb = document.createElement('input');
        bcb.type = 'checkbox';
        bcb.className = 'recon-master-cb';
        bcb.checked = true;
        bcb.setAttribute('aria-label', 'select all');
        bcb.addEventListener('change', function () {
            _onMasterChange(cfg, bcb.checked);
        });
        batchSelTh.appendChild(bcb);
        var actTh = document.createElement('th');
        actTh.setAttribute('colspan', String(colsTotal - 1));
        actTh.innerHTML =
            '<div class="recon-batch-inline">' +
            '<span class="recon-batch-count-inline" data-recon-count></span>' +
            '<button type="button" class="recon-batch-del-inline" data-recon-del>' +
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>' +
            '<span data-recon-del-label></span>' +
            '</button>' +
            '<button type="button" class="recon-batch-clear-inline" data-recon-clear></button>' +
            '</div>';
        batchTr.appendChild(batchSelTh);
        batchTr.appendChild(actTh);
        thead.appendChild(batchTr);
        actTh.querySelector('[data-recon-del]').addEventListener('click', function () {
            _doBatchDelete(cfg);
        });
        actTh.querySelector('[data-recon-clear]').addEventListener('click', function () {
            _clearSelection(cfg);
        });
        thead._reconReady = true;
        _refreshTheadLang(cfg);
        return thead;
    }

    // 给 tbody 每行加 row checkbox(最左)+ 给"时间"列(第 2 列)加 nowrap class
    function _injectTbodyCheckboxes(cfg) {
        var tbodyEl = document.getElementById(cfg.tbody);
        if (!tbodyEl) return;
        var rows = tbodyEl.querySelectorAll('tr');
        rows.forEach(function (tr) {
            var taskId = _getRowTaskId(tr);
            if (!taskId) return; // empty-state row
            // 已注入过 checkbox
            if (tr.querySelector('.recon-sel-cb')) return;
            var firstTd = tr.querySelector('td');
            if (!firstTd) return;
            var td = document.createElement('td');
            td.className = 'recon-sel-cell';
            var cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.className = 'recon-sel-cb';
            cb.dataset.taskId = taskId;
            cb.dataset.kind = cfg.kind;
            cb.addEventListener('click', function (e) {
                e.stopPropagation();
            });
            cb.addEventListener('change', function () {
                _refreshAfterChange(cfg);
            });
            td.appendChild(cb);
            tr.insertBefore(td, firstTd);
            // "时间"列 nowrap
            var timeTd = tr.children[1];
            if (timeTd && !timeTd.classList.contains('recon-time-col'))
                timeTd.classList.add('recon-time-col');
        });
        _refreshAfterChange(cfg);
    }

    function _getCheckboxes(cfg) {
        var tbodyEl = document.getElementById(cfg.tbody);
        if (!tbodyEl) return [];
        return Array.prototype.slice.call(tbodyEl.querySelectorAll('.recon-sel-cb'));
    }

    function _getSelectedIds(cfg) {
        return _getCheckboxes(cfg)
            .filter(function (cb) {
                return cb.checked;
            })
            .map(function (cb) {
                return cb.dataset.taskId;
            });
    }

    function _onMasterChange(cfg, checked) {
        _getCheckboxes(cfg).forEach(function (cb) {
            cb.checked = !!checked;
        });
        _refreshAfterChange(cfg);
    }

    function _refreshAfterChange(cfg) {
        var ids = _getSelectedIds(cfg);
        var all = _getCheckboxes(cfg);
        var tbodyEl = document.getElementById(cfg.tbody);
        if (!tbodyEl) return;
        var table = tbodyEl.closest('table');
        var thead = table && table.querySelector('thead');
        if (!thead) return;
        if (ids.length > 0) {
            thead.classList.add('recon-batch-mode');
        } else {
            thead.classList.remove('recon-batch-mode');
        }
        // 同步 master checkbox 状态(全选 / 部分 / 未选)
        thead.querySelectorAll('.recon-master-cb').forEach(function (mcb) {
            if (all.length === 0) {
                mcb.checked = false;
                mcb.indeterminate = false;
                return;
            }
            if (ids.length === all.length) {
                mcb.checked = true;
                mcb.indeterminate = false;
            } else if (ids.length === 0) {
                mcb.checked = false;
                mcb.indeterminate = false;
            } else {
                mcb.checked = false;
                mcb.indeterminate = true;
            }
        });
        // 更新计数文案
        var cntEl = thead.querySelector('[data-recon-count]');
        if (cntEl)
            cntEl.textContent = _t('recon-batch-selected-n', '已选 {n} 条').replace(
                '{n}',
                ids.length
            );
    }

    function _refreshTheadLang(cfg) {
        var tbodyEl = document.getElementById(cfg.tbody);
        if (!tbodyEl) return;
        var table = tbodyEl.closest('table');
        var thead = table && table.querySelector('thead');
        if (!thead) return;
        var delLbl = thead.querySelector('[data-recon-del-label]');
        var clearBtn = thead.querySelector('[data-recon-clear]');
        if (delLbl) delLbl.textContent = _t('recon-batch-delete', '批量删除');
        if (clearBtn) clearBtn.textContent = _t('recon-batch-clear', '取消');
        _refreshAfterChange(cfg);
    }

    function _clearSelection(cfg) {
        _getCheckboxes(cfg).forEach(function (cb) {
            cb.checked = false;
        });
        _refreshAfterChange(cfg);
    }

    async function _doBatchDelete(cfg) {
        var ids = _getSelectedIds(cfg);
        if (!ids.length) return;
        var msg = _t(
            'recon-batch-delete-confirm',
            '确定删除选中的 {n} 条对账任务?此操作不可恢复'
        ).replace('{n}', ids.length);
        var ok = false;
        try {
            if (typeof window.pearnlyConfirm === 'function') {
                ok = await window.pearnlyConfirm(msg, _t('recon-batch-delete-title', '批量删除'));
            } else {
                ok = window.confirm(msg);
            }
        } catch (_) {
            ok = false;
        }
        if (!ok) return;
        try {
            var headers = Object.assign({ 'Content-Type': 'application/json' }, _authH());
            var payloadIds =
                cfg.kind === 'glv'
                    ? ids.map(function (v) {
                          return parseInt(v, 10);
                      })
                    : ids;
            var resp = await fetch(cfg.api, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ ids: payloadIds }),
            });
            if (!resp.ok) {
                if (typeof window.showToast === 'function')
                    window.showToast(_t('recon-batch-delete-fail', '批量删除失败'), 'error');
                return;
            }
            var data = await resp.json();
            var del = (data && (data.deleted != null ? data.deleted : data.count)) || ids.length;
            if (typeof window.showToast === 'function')
                window.showToast(
                    _t('recon-batch-delete-ok', '已删除 {n} 条').replace('{n}', del),
                    'success'
                );
            cfg.reload();
        } catch (e) {
            if (typeof window.showToast === 'function')
                window.showToast(_t('recon-batch-delete-fail', '批量删除失败'), 'error');
        }
    }

    function _setupOne(cfg) {
        _injectThead(cfg);
        _injectTbodyCheckboxes(cfg);
        var tbodyEl = document.getElementById(cfg.tbody);
        if (!tbodyEl || tbodyEl._reconBatchWatched) return;
        tbodyEl._reconBatchWatched = true;
        var mo = new MutationObserver(function () {
            _injectTbodyCheckboxes(cfg);
        });
        mo.observe(tbodyEl, { childList: true, subtree: false });
    }

    function _setupAll() {
        _injectStyle();
        SELECTORS.forEach(_setupOne);
        // 清掉 v5.5.20 残留的独立 banner(如果之前部署过)
        document.querySelectorAll('.recon-batch-bar').forEach(function (el) {
            try {
                el.remove();
            } catch (_) {
                /* silent · 已移除 */
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _setupAll);
    } else {
        _setupAll();
    }
    setTimeout(_setupAll, 1500);
    setTimeout(_setupAll, 4000);

    // ESC 清选
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape') return;
        SELECTORS.forEach(function (cfg) {
            if (_getSelectedIds(cfg).length > 0) _clearSelection(cfg);
        });
    });

    // 4 语切换 → 刷新 thead 文案
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('recon-batch-thead', function () {
            SELECTORS.forEach(_refreshTheadLang);
        });
    }
})();
