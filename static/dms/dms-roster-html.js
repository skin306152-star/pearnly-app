/* Pearnly DMS · 操作员花名册视图 · HTML 模板层(挂 window.DXROSTERHTML)。
 * 纯字符串构建,不含事件/请求(逻辑在 dms-roster.js · 同 dms-billing-html 分片先例)。
 * 所有文案走 t()(四语);角色徽标销售=ผู้ขาย / 管理员=ผู้อนุมัติ(泰语地道)。 */
(function (root) {
    'use strict';
    function t(k, v) {
        return typeof root.t === 'function' ? root.t(k, v) : k;
    }
    function esc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(s == null ? '' : s)
            : String(s);
    }
    function fmtDate(v) {
        if (!v) return '—';
        var d = new Date(v);
        if (isNaN(d.getTime())) return String(v);
        var p = function (x) {
            return (x < 10 ? '0' : '') + x;
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

    function page(inner) {
        return (
            '<div class="dms-page-head"><h1>' +
            esc(t('dms-op-title')) +
            '</h1><p>' +
            esc(t('dms-op-sub')) +
            '</p></div><div class="dms-roster">' +
            inner +
            '</div>'
        );
    }
    function state(cls, msg, withRetry) {
        return (
            '<div class="dms-state ' +
            cls +
            '"><p>' +
            esc(msg) +
            '</p>' +
            (withRetry
                ? '<button type="button" class="btn" id="dms-op-retry">' +
                  esc(t('dms-op-retry')) +
                  '</button>'
                : '') +
            '</div>'
        );
    }

    // 新增操作员表单:显示名 / DMS 用户名 / DMS 密码 / 角色单选。提交后清空密码(见逻辑层)。
    function formCard() {
        return (
            '<div class="dms-bill-card dms-op-form"><h2>' +
            esc(t('dms-op-add-title')) +
            '</h2><p class="sub">' +
            esc(t('dms-op-add-sub')) +
            '</p><div class="dms-op-grid">' +
            field('dms-op-name', t('dms-op-f-name'), 'text', t('dms-op-f-name-ph')) +
            field('dms-op-user', t('dms-op-f-user'), 'text', t('dms-op-f-user-ph')) +
            field('dms-op-pass', t('dms-op-f-pass'), 'password', t('dms-op-f-pass-ph')) +
            roleRadio() +
            '</div><div class="dms-op-err" id="dms-op-form-err" style="display:none"></div>' +
            '<div class="dms-op-form-actions"><button type="button" class="btn primary" id="dms-op-create">' +
            esc(t('dms-op-add-btn')) +
            '</button></div></div>'
        );
    }
    function field(id, label, type, ph) {
        return (
            '<label class="dms-op-field"><span>' +
            esc(label) +
            '</span><input type="' +
            type +
            '" id="' +
            id +
            '" class="dms-bill-input" placeholder="' +
            esc(ph) +
            '"' +
            (type === 'password' ? ' autocomplete="new-password"' : '') +
            '></label>'
        );
    }
    function roleRadio(selected) {
        var sel = selected || 'sales';
        function opt(v, labelKey) {
            return (
                '<label class="dms-op-radio"><input type="radio" name="dms-op-role" value="' +
                v +
                '"' +
                (sel === v ? ' checked' : '') +
                '><span>' +
                esc(t(labelKey)) +
                '</span></label>'
            );
        }
        return (
            '<div class="dms-op-field"><span>' +
            esc(t('dms-op-f-role')) +
            '</span><div class="dms-op-radios">' +
            opt('sales', 'dms-op-role-sales') +
            opt('admin', 'dms-op-role-admin') +
            '</div></div>'
        );
    }

    function roleBadge(role) {
        var cls = role === 'admin' ? 'admin' : 'sales';
        var key = role === 'admin' ? 'dms-op-role-admin' : 'dms-op-role-sales';
        return '<span class="dms-op-badge ' + cls + '">' + esc(t(key)) + '</span>';
    }
    function lineBadge(item) {
        if (item.line_bound) {
            var who = item.line_display_name ? ' · ' + esc(item.line_display_name) : '';
            return '<span class="dms-badge ok">' + esc(t('dms-op-line-bound')) + '</span>' + who;
        }
        return '<span class="dms-badge pending">' + esc(t('dms-op-line-unbound')) + '</span>';
    }
    function statusBadge(status) {
        if (status === 'inactive')
            return '<span class="dms-badge fail">' + esc(t('dms-op-st-inactive')) + '</span>';
        return '<span class="dms-badge ok">' + esc(t('dms-op-st-active')) + '</span>';
    }

    function rowActions(item) {
        var isActive = item.status !== 'inactive';
        var toggle = isActive
            ? '<button type="button" class="btn small" data-op-act="deactivate" data-op-id="' +
              esc(item.user_id) +
              '">' +
              esc(t('dms-op-act-deactivate')) +
              '</button>'
            : '<button type="button" class="btn small primary" data-op-act="activate" data-op-id="' +
              esc(item.user_id) +
              '">' +
              esc(t('dms-op-act-activate')) +
              '</button>';
        return (
            '<div class="dms-op-actions">' +
            '<button type="button" class="btn small primary" data-op-act="code" data-op-id="' +
            esc(item.user_id) +
            '">' +
            esc(t('dms-op-act-code')) +
            '</button>' +
            '<button type="button" class="btn small" data-op-act="pw" data-op-id="' +
            esc(item.user_id) +
            '">' +
            esc(t('dms-op-act-pw')) +
            '</button>' +
            toggle +
            '</div>'
        );
    }
    function rowHtml(item) {
        return (
            '<div class="dms-op-row' +
            (item.status === 'inactive' ? ' off' : '') +
            '"><div class="dms-op-c name"><b>' +
            esc(item.display_name) +
            '</b><span class="dms-op-user-mono">' +
            esc(item.username) +
            '</span></div>' +
            '<div class="dms-op-c role">' +
            roleBadge(item.dms_role) +
            '</div><div class="dms-op-c line">' +
            lineBadge(item) +
            '</div><div class="dms-op-c status">' +
            statusBadge(item.status) +
            '</div><div class="dms-op-c acts">' +
            rowActions(item) +
            '</div></div>'
        );
    }
    function listCard(items) {
        var head =
            '<div class="dms-op-row head"><div class="dms-op-c name">' +
            esc(t('dms-op-col-name')) +
            '</div><div class="dms-op-c role">' +
            esc(t('dms-op-col-role')) +
            '</div><div class="dms-op-c line">' +
            esc(t('dms-op-col-line')) +
            '</div><div class="dms-op-c status">' +
            esc(t('dms-op-col-status')) +
            '</div><div class="dms-op-c acts">' +
            esc(t('dms-op-col-acts')) +
            '</div></div>';
        return (
            '<div class="dms-bill-card"><h2>' +
            esc(t('dms-op-list-title')) +
            '</h2><div class="dms-op-table">' +
            head +
            items.map(rowHtml).join('') +
            '</div></div>'
        );
    }
    function listEmpty() {
        return (
            '<div class="dms-bill-card"><h2>' +
            esc(t('dms-op-list-title')) +
            '</h2><div class="dms-state empty"><p>' +
            esc(t('dms-op-empty')) +
            '</p></div></div>'
        );
    }

    // 绑定码大字弹层(照 dms-line 样式:大字码 + 倒计时);逻辑层填 code/countdown 并驱动过期。
    function codeOverlay(name) {
        return (
            '<div class="dms-op-modal" role="dialog" aria-modal="true"><div class="dms-op-modal-card">' +
            '<div class="dms-op-modal-h">' +
            esc(t('dms-op-code-title')) +
            '</div><div class="dms-op-modal-who">' +
            esc(name) +
            '</div><ol class="dms-line-steps"><li>' +
            esc(t('dms-op-code-step1')) +
            '</li><li>' +
            esc(t('dms-op-code-step2')) +
            '</li></ol>' +
            '<div class="dms-line-code" id="dms-op-code-val">······</div>' +
            '<div class="dms-line-countdown" id="dms-op-code-cd"></div>' +
            '<div class="dms-op-modal-actions"><button type="button" class="btn" id="dms-op-code-close">' +
            esc(t('dms-op-modal-close')) +
            '</button><button type="button" class="btn primary" id="dms-op-code-regen">' +
            esc(t('dms-op-code-regen')) +
            '</button></div></div></div>'
        );
    }
    // 换 DMS 密码模态(体系内 · 非原生弹窗)。
    function pwModal(name) {
        return (
            '<div class="dms-op-modal" role="dialog" aria-modal="true"><div class="dms-op-modal-card">' +
            '<div class="dms-op-modal-h">' +
            esc(t('dms-op-pw-title')) +
            '</div><div class="dms-op-modal-who">' +
            esc(name) +
            '</div><label class="dms-op-field"><span>' +
            esc(t('dms-op-pw-new')) +
            '</span><input type="password" id="dms-op-pw-input" class="dms-bill-input" autocomplete="new-password" placeholder="' +
            esc(t('dms-op-pw-ph')) +
            '"></label><div class="dms-op-err" id="dms-op-pw-err" style="display:none"></div>' +
            '<div class="dms-op-modal-actions"><button type="button" class="btn" id="dms-op-pw-cancel">' +
            esc(t('dms-op-modal-cancel')) +
            '</button><button type="button" class="btn primary" id="dms-op-pw-save">' +
            esc(t('dms-op-pw-save')) +
            '</button></div></div></div>'
        );
    }

    root.DXROSTERHTML = {
        page: page,
        state: state,
        formCard: formCard,
        listCard: listCard,
        listEmpty: listEmpty,
        codeOverlay: codeOverlay,
        pwModal: pwModal,
        fmtDate: fmtDate,
    };
})(typeof self !== 'undefined' ? self : this);
