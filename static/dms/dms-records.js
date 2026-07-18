/* Pearnly DMS · 推送记录页 · 恒按 adapter=mrerp_dms 筛(身份证 → DMS 客户的推送历史)。
 * 员工/普通视角走 /api/erp/logs(user 隔离,DXAPI.pushLogs 已固定 adapter);owner 视角(波3 C6·
 * __dmsIsOwner)走 /api/dms/records 拉【全租户】推送并加「操作员」归属列(显示名取档案,无档案=
 * 老板本人)。四态 UI:加载/空/错/列表。信息密度:时间 /(操作员)/ 客户 / 方式 / 状态。挂 window.DXRECORDS。 */
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
    // 操作员归属(owner 视角):有档案显示名取之;无档案=老板本人发起,显示「老板」。
    function operatorLabel(item) {
        if (item.operator_name) return item.operator_name;
        if (item.operator_role === 'owner') return t('dms-rec-op-owner');
        return '—';
    }
    function opCell(item, owner) {
        return owner ? '<div class="dms-rec-c op">' + esc(operatorLabel(item)) + '</div>' : '';
    }
    function rowHtml(item, owner) {
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
            '</div>' +
            opCell(item, owner) +
            '<div class="dms-rec-c cust">' +
            cust +
            err +
            '</div><div class="dms-rec-c mode">' +
            esc(modeLabel(item)) +
            '</div><div class="dms-rec-c status">' +
            statusBadge(item.status) +
            '</div></div>'
        );
    }
    function listHtml(items, owner) {
        var opHead = owner
            ? '<div class="dms-rec-c op">' + esc(t('dms-rec-col-operator')) + '</div>'
            : '';
        var head =
            '<div class="dms-rec-row head"><div class="dms-rec-c time">' +
            esc(t('dms-rec-col-time')) +
            '</div>' +
            opHead +
            '<div class="dms-rec-c cust">' +
            esc(t('dms-rec-col-customer')) +
            '</div><div class="dms-rec-c mode">' +
            esc(t('dms-rec-col-mode')) +
            '</div><div class="dms-rec-c status">' +
            esc(t('dms-rec-col-status')) +
            '</div></div>';
        return (
            '<div class="dms-rec-table' +
            (owner ? ' with-op' : '') +
            '">' +
            head +
            items
                .map(function (it) {
                    return rowHtml(it, owner);
                })
                .join('') +
            '</div>'
        );
    }

    function load(host) {
        var owner = !!root.__dmsIsOwner;
        host.innerHTML = shell(stateBox('loading', t('dms-rec-loading'), false));
        var req = owner
            ? root.DXAPI.create().tenantRecords(100)
            : root.DXAPI.create().pushLogs(100);
        req.then(function (data) {
            var items = (data && data.items) || [];
            if (!items.length) {
                host.innerHTML = shell(stateBox('empty', t('dms-rec-empty'), false));
                return;
            }
            host.innerHTML = shell(listHtml(items, owner));
        }).catch(function () {
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
