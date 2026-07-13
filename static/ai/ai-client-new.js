/*
 * Pearnly AI · ai-client-new.js · 客户目录页「+新建客户」最小表单(N1 · P0-1)
 *
 * 根治"建客户断头"(/ai 全产品此前零处调用建档接口)。复用现成端点
 * POST /api/workspace/clients(泰文注册名闸/税号查重都在后端,见 routes/workspace_routes.py),
 * 零新增后端业务逻辑,本文件只管表单 UI + 提交编排。
 *
 * 按钮显隐:GET /api/workspace/clients/can-create 探针(settings.workspace.manage 专属),
 * 没权限的员工整个按钮不渲染——不给点了才 403 的假门(state honesty)。
 *
 * 模态外壳复用 .pkg-mask/.pkg-modal(ai-pkg.css 已建立"通用模态外壳"复用先例,
 * 见 ai-recon.css 顶注同款说明),不新起一套弹窗 CSS;表单行复用 .pr-lb/.pr-setup-row
 * (ai-payroll.css,ai-reports-render.js 已有跨文件复用先例)。
 *
 * 体量小、编排与拼装未拆(同 ai-settings.js 先例)。
 */
(function () {
    'use strict';

    var MASK_ID = 'clientNewMask';

    var S = null;

    function esc(s) {
        return AI.state.esc(s);
    }

    function mask() {
        return document.getElementById(MASK_ID);
    }

    function modalHtml() {
        var errHtml = S.errKey ? '<div class="intake-err">' + esc(at(S.errKey)) + '</div>' : '';
        return (
            '<div class="pkg-mask on" id="' +
            MASK_ID +
            '">' +
            '<div class="pkg-modal" role="dialog" aria-modal="true">' +
            '<div class="mh"><div><h3>' +
            esc(at('clients_new_title')) +
            '</h3><p>' +
            esc(at('clients_new_hint')) +
            '</p></div>' +
            '<button class="mclose" type="button" data-action="cn-close" aria-label="' +
            esc(at('pkg_evid_close')) +
            '">&times;</button></div>' +
            '<div class="mb" style="grid-template-columns: 1fr">' +
            '<form id="cnForm">' +
            '<label class="pr-lb" style="display: block; margin-bottom: 12px">' +
            esc(at('clients_new_name_label')) +
            '<input id="cnName" type="text" maxlength="200" value="' +
            esc(S.name) +
            '" autofocus />' +
            '</label>' +
            '<label class="pr-lb" style="display: block; margin-bottom: 12px">' +
            esc(at('clients_new_tax_id_label')) +
            '<input id="cnTaxId" type="text" maxlength="20" value="' +
            esc(S.taxId) +
            '" />' +
            '</label>' +
            errHtml +
            '<div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 6px">' +
            '<button type="button" class="btn" data-action="cn-close">' +
            esc(at('intake_clear')) +
            '</button>' +
            '<button type="submit" class="btn pri" id="cnSubmit"' +
            (S.submitting ? ' disabled' : '') +
            '>' +
            esc(S.submitting ? at('clients_new_submitting') : at('clients_new_submit')) +
            '</button>' +
            '</div>' +
            '</form>' +
            '</div></div></div>'
        );
    }

    function render() {
        var existing = mask();
        var html = modalHtml();
        if (existing) existing.outerHTML = html;
        else document.body.insertAdjacentHTML('beforeend', html);
        var m = mask();
        m.querySelectorAll('[data-action="cn-close"]').forEach(function (btn) {
            btn.onclick = close;
        });
        m.addEventListener('click', function (e) {
            if (e.target === m) close();
        });
        var form = document.getElementById('cnForm');
        form.onsubmit = function (e) {
            e.preventDefault();
            submit();
        };
        var nameInput = document.getElementById('cnName');
        if (nameInput) nameInput.focus();
    }

    function open() {
        S.open = true;
        S.name = '';
        S.taxId = '';
        S.errKey = null;
        S.submitting = false;
        render();
        document.addEventListener('keydown', onKeydown);
    }

    function close() {
        S.open = false;
        var m = mask();
        if (m) m.remove();
        document.removeEventListener('keydown', onKeydown);
    }

    // Canon §7:Esc 关浮层。
    function onKeydown(e) {
        if (e.key === 'Escape') close();
    }

    function mapErrKey(err) {
        var key = AI.api.mapApiErrorKey(err && err.code);
        return at(key) !== key ? key : 'err_generic';
    }

    function submit() {
        if (S.submitting) return;
        var name = (document.getElementById('cnName').value || '').trim();
        var taxId = (document.getElementById('cnTaxId').value || '').trim();
        if (!name) {
            S.errKey = 'clients_new_err_name_required';
            render();
            return;
        }
        S.name = name;
        S.taxId = taxId;
        S.submitting = true;
        S.errKey = null;
        render();
        S.api
            .createWorkspaceClient({ name: name, tax_id: taxId || undefined })
            .then(function (r) {
                close();
                if (S.onCreated) S.onCreated(r.id);
            })
            .catch(function (err) {
                S.submitting = false;
                S.errKey = mapErrKey(err);
                render();
            });
    }

    // 按钮显隐探针:没有 settings.workspace.manage 的员工看不到「+新建客户」——不是
    // 隐藏后靠前端拦截点击(那还是给了一个"看起来能点"的假承诺),是后端权限真实来源。
    function wireButton(api, onCreated) {
        var btn = document.getElementById('clientsNewBtn');
        if (!btn) return;
        btn.style.display = 'none';
        api.canCreateWorkspaceClient()
            .then(function (r) {
                if (!r || !r.allowed) return;
                btn.style.display = '';
                btn.onclick = function () {
                    S = { api: api, onCreated: onCreated };
                    open();
                };
            })
            .catch(function () {
                /* 探针失败按钮保持隐藏(fail-closed,同 P0-1 拍板口径) */
            });
    }

    window.AI = window.AI || {};
    window.AI.clientNew = { wireButton: wireButton };
})();
