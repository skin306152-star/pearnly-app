/* Pearnly DMS · 推送记录页 · 恒按 adapter=mrerp_dms 筛(身份证 → DMS 客户的推送历史)。
 * 复用主站既有 /api/erp/logs(DXAPI.pushLogs 已固定 adapter 参数)。四态 UI:加载/空/错/列表。
 * 信息密度取简化版:时间 / 客户 / 方式 / 状态(失败附错误信息)。挂 window.DXRECORDS。 */
(function (root) {
    'use strict';
    function t(k) {
        return typeof root.t === 'function' ? root.t(k) : k;
    }
    function esc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(s == null ? '' : s)
            : String(s);
    }

    function fmtTime(v) {
        if (!v) return '—';
        var d = new Date(v);
        if (isNaN(d.getTime())) return String(v);
        var p = function (n) {
            return (n < 10 ? '0' : '') + n;
        };
        return (
            d.getFullYear() +
            '-' +
            p(d.getMonth() + 1) +
            '-' +
            p(d.getDate()) +
            ' ' +
            p(d.getHours()) +
            ':' +
            p(d.getMinutes())
        );
    }
    function modeLabel(item) {
        var rb = item.request_body;
        if (typeof rb === 'string') {
            try {
                rb = JSON.parse(rb);
            } catch (e) {
                rb = {};
            }
        }
        var mode = (rb && rb.mode) || '';
        if (mode === 'create') return t('dms-rec-mode-create');
        if (mode === 'update') return t('dms-rec-mode-update');
        if (mode === 'overwrite') return t('dms-rec-mode-overwrite');
        return '—';
    }
    function statusBadge(status) {
        if (status === 'success')
            return '<span class="dms-badge ok">' + esc(t('dms-rec-st-success')) + '</span>';
        if (status === 'pending')
            return '<span class="dms-badge pending">' + esc(t('dms-rec-st-pending')) + '</span>';
        return '<span class="dms-badge fail">' + esc(t('dms-rec-st-failed')) + '</span>';
    }

    function shell(inner) {
        return (
            '<div class="dms-page"><div class="dms-page-head"><h1>' +
            esc(t('dms-rec-title')) +
            '</h1><p>' +
            esc(t('dms-rec-sub')) +
            '</p></div>' +
            inner +
            '</div>'
        );
    }
    function stateBox(cls, msg, withRetry) {
        return (
            '<div class="dms-state ' +
            cls +
            '"><p>' +
            esc(msg) +
            '</p>' +
            (withRetry
                ? '<button class="btn" id="dms-rec-retry">' + esc(t('dms-rec-retry')) + '</button>'
                : '') +
            '</div>'
        );
    }
    function rowHtml(item) {
        var cust =
            esc(item.seller_name || '') +
            (item.invoice_no
                ? ' <span class="dms-rec-id">#' + esc(item.invoice_no) + '</span>'
                : '');
        var err =
            item.status !== 'success' && item.error_msg
                ? '<div class="dms-rec-err">' + esc(item.error_msg) + '</div>'
                : '';
        return (
            '<div class="dms-rec-row"><div class="dms-rec-c time">' +
            esc(fmtTime(item.created_at)) +
            '</div><div class="dms-rec-c cust">' +
            cust +
            err +
            '</div><div class="dms-rec-c mode">' +
            esc(modeLabel(item)) +
            '</div><div class="dms-rec-c status">' +
            statusBadge(item.status) +
            '</div></div>'
        );
    }
    function listHtml(items) {
        var head =
            '<div class="dms-rec-row head"><div class="dms-rec-c time">' +
            esc(t('dms-rec-col-time')) +
            '</div><div class="dms-rec-c cust">' +
            esc(t('dms-rec-col-customer')) +
            '</div><div class="dms-rec-c mode">' +
            esc(t('dms-rec-col-mode')) +
            '</div><div class="dms-rec-c status">' +
            esc(t('dms-rec-col-status')) +
            '</div></div>';
        return '<div class="dms-rec-table">' + head + items.map(rowHtml).join('') + '</div>';
    }

    function load(host) {
        host.innerHTML = shell(stateBox('loading', t('dms-rec-loading'), false));
        root.DXAPI.create()
            .pushLogs(100)
            .then(function (data) {
                var items = (data && data.items) || [];
                if (!items.length) {
                    host.innerHTML = shell(stateBox('empty', t('dms-rec-empty'), false));
                    return;
                }
                host.innerHTML = shell(listHtml(items));
            })
            .catch(function () {
                host.innerHTML = shell(stateBox('error', t('dms-rec-error'), true));
                var btn = host.querySelector('#dms-rec-retry');
                if (btn)
                    btn.addEventListener('click', function () {
                        load(host);
                    });
            });
    }

    function mount(hostSel) {
        var host = document.querySelector(hostSel);
        if (host) load(host);
    }

    root.DXRECORDS = { mount: mount };
})(typeof self !== 'undefined' ? self : this);
