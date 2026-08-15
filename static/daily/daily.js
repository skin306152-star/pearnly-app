/*
 * static/daily/daily.js · Daily 周记账主壳(应用渲染 + 事件 + init)
 *
 * 分层:纯逻辑/状态/API 在 daily-core.js(DailyCore · UMD 导出供 node 单测),
 * 门禁/登录卡/故障态在 daily-gate.js(DailyGate),数据操作在 daily-actions.js,
 * 本文件只保留渲染和交互编排:
 *   - 渲染:appHtml 全量重渲 + data-i18n 绑定
 *   - 事件:appRoot 单一 click 委托(data-* 空属性按 `!= null` 判,防空串假阴性)
 */
(function (root) {
    'use strict';

    var state = root.DailyCore.state;
    var t = root.DailyCore.t;
    var weekBounds = root.DailyCore.weekBounds;
    var sumBy = root.DailyCore.sumBy;
    var inMonth = root.DailyCore.inMonth;
    var inRange = root.DailyCore.inRange;
    var monthName = root.DailyCore.monthName;
    var moneyFormat = root.DailyCore.moneyFormat;
    var entryDateLabel = root.DailyCore.entryDateLabel;
    var escapeHtml = root.DailyCore.escapeHtml;
    var applyStaticI18n = root.DailyGate.applyStaticI18n;
    var renderGate = root.DailyGate.renderGate;

    var actions = root.DailyActions.create({ rerender: rerender, showToast: showToast });
    var loadMonth = actions.loadMonth;
    var saveEntry = actions.saveEntry;
    var deleteEntry = actions.deleteEntry;
    var exportData = actions.exportData;
    var importFile = actions.importFile;

    function showToast(key, vars) {
        state.toast = { key: key, vars: vars };
        rerender();
        setTimeout(function () {
            if (state.toast) state.toast = null;
            rerender();
        }, 2400);
    }

    // ==================== 渲染 ====================

    function rerender() {
        var rootEl = root.document.getElementById('appRoot');
        if (!rootEl) return;
        if (state.gate !== 'app') {
            rootEl.innerHTML = '';
            return;
        }
        rootEl.innerHTML = appHtml();
        bindAppEvents();
        applyStaticI18n();
    }

    function appHtml() {
        var m = state.months.filter(function (x) {
            return x.id === state.monthId;
        })[0];
        if (!m) return '';
        var bounds = weekBounds(m.year, m.month, state.week);
        var monthEntries = state.entries.filter(function (e) {
            return inMonth(e, state.monthId);
        });
        var weekEntries = monthEntries
            .filter(function (e) {
                return inRange(e, bounds.min, bounds.max);
            })
            .sort(function (a, b) {
                return (
                    String(b.entry_date).localeCompare(String(a.entry_date)) ||
                    String(b.created_at).localeCompare(String(a.created_at))
                );
            });
        var weeklyIncome = sumBy(weekEntries, 'income');
        var weeklyExpense = sumBy(weekEntries, 'expense');
        var monthlyIncome = sumBy(monthEntries, 'income');
        var monthlyExpense = sumBy(monthEntries, 'expense');
        var monthlyBalance = monthlyIncome - monthlyExpense;

        var monthOptionsHtml = state.months
            .map(function (opt) {
                var name = monthName(state.lang, opt.year, opt.month) + ' ' + opt.year;
                return (
                    '<option value="' +
                    opt.id +
                    '"' +
                    (opt.id === state.monthId ? ' selected' : '') +
                    '>' +
                    escapeHtml(name) +
                    '</option>'
                );
            })
            .join('');

        var weekButtons = [1, 2, 3, 4, 5]
            .map(function (w) {
                return (
                    '<button type="button" class="week-btn' +
                    (w === state.week ? ' active' : '') +
                    '" data-week="' +
                    w +
                    '">' +
                    w +
                    '</button>'
                );
            })
            .join('');

        var listHtml;
        if (state.loading) {
            listHtml = '<div class="loading-line"></div>';
        } else if (!weekEntries.length) {
            listHtml =
                '<div class="empty-state"><span class="empty-mark">฿</span><p>' +
                escapeHtml(t('daily.list.empty_title')) +
                '</p><small>' +
                escapeHtml(t('daily.list.empty_body')) +
                '</small></div>';
        } else {
            listHtml = weekEntries
                .map(function (e) {
                    var isIncome = e.kind === 'income';
                    return (
                        '<article class="entry-row">' +
                        '<span class="entry-mark ' +
                        escapeHtml(e.kind) +
                        '"></span>' +
                        '<span class="entry-copy"><strong>' +
                        escapeHtml(e.title) +
                        '</strong>' +
                        '<small>' +
                        escapeHtml(entryDateLabel(state.lang, e.entry_date)) +
                        ' · ' +
                        escapeHtml(t(isIncome ? 'daily.type.income' : 'daily.type.expense')) +
                        '</small></span>' +
                        '<span class="entry-amount ' +
                        (isIncome ? 'positive' : 'negative') +
                        '">' +
                        (isIncome ? '+' : '−') +
                        escapeHtml(moneyFormat(state.lang, e.amount)) +
                        '</span>' +
                        '<button type="button" class="delete-button" data-delete="' +
                        escapeHtml(e.id) +
                        '">×</button>' +
                        '</article>'
                    );
                })
                .join('');
        }

        var monthNameFull = escapeHtml(monthName(state.lang, m.year, m.month));

        return (
            '<main class="app-shell">' +
            '<header class="app-header">' +
            '<div><p class="eyebrow">' +
            escapeHtml(t('daily.eyebrow')) +
            '</p><h1>' +
            escapeHtml(t('daily.title')) +
            '</h1></div>' +
            '<div class="header-actions">' +
            '<button type="button" class="tool-button" data-tools>⋯</button>' +
            '<button type="button" class="icon-button" data-add>+</button>' +
            '</div>' +
            '</header>' +
            (state.showDataTools
                ? '<section class="surface data-tools">' +
                  '<div><strong>' +
                  escapeHtml(t('daily.data.title')) +
                  '</strong><small>' +
                  escapeHtml(t('daily.data.note')) +
                  '</small></div>' +
                  '<button type="button" data-export>' +
                  escapeHtml(t('daily.data.export')) +
                  '</button>' +
                  '<button type="button" data-import>' +
                  escapeHtml(t('daily.data.import')) +
                  '</button>' +
                  '<input type="file" id="importFile" accept="application/json,.json" hidden>' +
                  '</section>'
                : '') +
            '<section class="surface filters">' +
            '<label><span>' +
            escapeHtml(t('daily.filter.month')) +
            '</span>' +
            '<select data-month>' +
            monthOptionsHtml +
            '</select></label>' +
            '<div class="week-picker">' +
            weekButtons +
            '</div>' +
            '<p class="date-range">' +
            escapeHtml(
                t('daily.filter.range', { w: state.week, a: bounds.startDay, b: bounds.endDay })
            ) +
            '</p>' +
            '</section>' +
            '<section class="summary-grid">' +
            summaryCard(
                'daily.sum.weekly_income',
                moneyFormat(state.lang, weeklyIncome),
                'income'
            ) +
            summaryCard(
                'daily.sum.weekly_expense',
                moneyFormat(state.lang, weeklyExpense),
                'expense'
            ) +
            summaryCard(
                'daily.sum.month_balance',
                moneyFormat(state.lang, monthlyBalance),
                'balance'
            ) +
            summaryCard('daily.sum.month_income', moneyFormat(state.lang, monthlyIncome), 'month') +
            '</section>' +
            '<section class="surface entries-card">' +
            '<div class="section-heading">' +
            '<div><h2>' +
            escapeHtml(t('daily.list.title')) +
            '</h2><small>' +
            escapeHtml(t('daily.list.count', { n: weekEntries.length })) +
            '</small></div>' +
            '<button type="button" data-add>' +
            escapeHtml(t('daily.list.add')) +
            '</button>' +
            '</div>' +
            '<div class="entry-list">' +
            listHtml +
            '</div>' +
            '</section>' +
            '<section class="surface totals-card">' +
            '<h2>' +
            escapeHtml(t('daily.total.title', { month: monthNameFull })) +
            '</h2>' +
            totalLine('daily.total.income', moneyFormat(state.lang, monthlyIncome), 'positive') +
            totalLine('daily.total.expense', moneyFormat(state.lang, monthlyExpense), 'negative') +
            totalLine('daily.total.balance', moneyFormat(state.lang, monthlyBalance), '') +
            '</section>' +
            '<p class="privacy-note">' +
            escapeHtml(t('daily.privacy')) +
            '</p>' +
            (state.showEntryForm ? entryFormHtml(m, bounds) : '') +
            (state.toast
                ? '<div class="toast" role="status">' +
                  escapeHtml(t(state.toast.key, state.toast.vars)) +
                  '</div>'
                : '') +
            '</main>'
        );
    }

    function summaryCard(labelKey, value, tone) {
        return (
            '<article class="summary-card ' +
            tone +
            '"><span data-i18n="' +
            labelKey +
            '"></span><strong>' +
            value +
            '</strong></article>'
        );
    }

    function totalLine(labelKey, value, tone) {
        return (
            '<div class="total-line"><span data-i18n="' +
            labelKey +
            '"></span><strong class="' +
            tone +
            '">' +
            value +
            '</strong></div>'
        );
    }

    function entryFormHtml(month, bounds) {
        var kindOptions = ['expense', 'income']
            .map(function (k) {
                return (
                    '<button type="button" class="type-btn' +
                    (k === 'expense' ? ' selected expense' : '') +
                    '" data-kind="' +
                    k +
                    '">' +
                    escapeHtml(t(k === 'income' ? 'daily.type.income' : 'daily.type.expense')) +
                    '</button>'
                );
            })
            .join('');
        return (
            '' +
            '<div class="modal-backdrop" data-close>' +
            '<form class="entry-form">' +
            '<div class="form-heading">' +
            '<div><p>' +
            escapeHtml(t('daily.form.week', { w: state.week })) +
            '</p><h2>' +
            escapeHtml(t('daily.form.title')) +
            '</h2></div>' +
            '<button type="button" class="form-close" data-close>×</button>' +
            '</div>' +
            '<label><span>' +
            escapeHtml(t('daily.form.date')) +
            '</span>' +
            '<input type="date" name="date" value="' +
            bounds.min +
            '" min="' +
            bounds.min +
            '" max="' +
            bounds.max +
            '"></label>' +
            '<fieldset><legend>' +
            escapeHtml(t('daily.form.type')) +
            '</legend><div class="type-picker">' +
            kindOptions +
            '</div></fieldset>' +
            '<label><span>' +
            escapeHtml(t('daily.form.item')) +
            '</span>' +
            '<input type="text" name="title" data-i18n-placeholder="daily.form.item_ph" maxlength="100"></label>' +
            '<label><span>' +
            escapeHtml(t('daily.form.amount')) +
            '</span>' +
            '<div class="amount-field"><b>฿</b><input type="text" name="amount" inputmode="decimal" data-i18n-placeholder="daily.form.amount_ph"></div></label>' +
            '<button type="submit" class="save-button" data-i18n="daily.form.save"></button>' +
            '</form>' +
            '</div>'
        );
    }

    // ==================== 事件 ====================

    function bindAppEvents() {
        var rootEl = root.document.getElementById('appRoot');
        rootEl.addEventListener('click', function (ev) {
            var el = ev.target;
            while (el && el !== rootEl && !el.dataset) el = el.parentNode;
            if (!el || el === rootEl) return;
            if (el.dataset.add != null) {
                state.showEntryForm = true;
                rerender();
            } else if (el.dataset.tools != null) {
                state.showDataTools = !state.showDataTools;
                rerender();
            } else if (el.dataset.export != null) {
                exportData();
            } else if (el.dataset.import != null) {
                var input = root.document.getElementById('importFile');
                if (input) input.click();
            } else if (el.dataset.week) {
                state.week = Number(el.dataset.week);
                rerender();
            } else if (el.dataset.delete) {
                deleteEntry(el.dataset.delete);
            } else if (el.dataset.kind) {
                var form = rootEl.querySelector('form.entry-form');
                if (form) form.dataset.kind = el.dataset.kind;
                var btns = rootEl.querySelectorAll('.type-btn');
                for (var i = 0; i < btns.length; i++) {
                    btns[i].className =
                        btns[i].getAttribute('data-kind') === el.dataset.kind
                            ? 'type-btn selected ' + el.dataset.kind
                            : 'type-btn';
                }
            } else if (el.dataset.close != null) {
                state.showEntryForm = false;
                rerender();
            }
        });
        var monthSel = rootEl.querySelector('[data-month]');
        if (monthSel) {
            monthSel.addEventListener('change', function () {
                state.monthId = monthSel.value;
                state.week = 1;
                loadMonth();
            });
        }
        var importInput = rootEl.querySelector('#importFile');
        if (importInput) {
            importInput.addEventListener('change', function () {
                var f = importInput.files && importInput.files[0];
                importInput.value = '';
                if (f) importFile(f);
            });
        }
        var form = rootEl.querySelector('form.entry-form');
        if (form) {
            form.addEventListener('submit', function (ev) {
                ev.preventDefault();
                var fd = new root.FormData(form);
                var kind = form.dataset.kind || 'expense';
                var title = String(fd.get('title') || '').trim();
                var amount = Number(String(fd.get('amount') || '').replace(/,/g, ''));
                if (!title || !Number.isFinite(amount) || amount <= 0) return;
                saveEntry({
                    date: String(fd.get('date') || ''),
                    kind: kind,
                    title: title,
                    amount: amount,
                });
            });
        }
    }

    function init() {
        if (!root.document.getElementById('appRoot')) return;
        var gateHost = root.document.getElementById('gateRoot');
        if (gateHost) {
            gateHost.addEventListener('click', function (ev) {
                var el = ev.target;
                if (!el || !el.dataset) return;
                if (el.dataset.lang) root.DailyGate.setLang(el.dataset.lang);
                if (el.dataset.logout != null) {
                    root.DailyCore.clearToken();
                    state.gate = 'login';
                    renderGate();
                }
                if (el.dataset.retry != null) root.DailyGate.boot();
            });
        }
        if ('serviceWorker' in navigator) {
            root.navigator.serviceWorker.register('/daily-sw.js').catch(function () {
                /* 装不上不影响用 */
            });
        }
        root.DailyGate.boot();
    }

    if (typeof root.document !== 'undefined' && root.document.getElementById) {
        if (root.document.readyState === 'loading') {
            root.document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
    }

    root.DailyApp = {
        rerender: rerender,
        loadMonth: loadMonth,
        saveEntry: saveEntry,
        deleteEntry: deleteEntry,
        exportData: exportData,
        importFile: importFile,
        state: state,
    };
})(typeof window !== 'undefined' ? window : globalThis);
