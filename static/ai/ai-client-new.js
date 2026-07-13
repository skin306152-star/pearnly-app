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
 * MC1-b0(2026-07-13):税号输满 13 位过 mod-11 预检自动触发 RD 直查(复用主站建档向导
 * 同款端点 GET /api/workspace/tax-lookup,零新增后端),回填泰文注册名(用户已手输过的
 * 不覆盖,给"使用查询结果"确认);查不到/超时诚实降级,表单照常可提交;mod-11 不过
 * 即时黄字提示,不阻断。mod11Check 口径与 services/recon/field_comparator.mod11_check
 * 逐字节一致(前端预检,后端 RD 查询前再判一次,两处独立实现同一算法,不能共享 import)。
 *
 * 体量小、编排与拼装未拆(同 ai-settings.js 先例)。
 */
(function (root) {
    'use strict';

    // ===== 纯函数(零 DOM 依赖,node 直接 require 断言 · tests/unit/test_ai_client_new_pure.py) =====

    function taxDigits(raw) {
        return String(raw || '').replace(/\D/g, '');
    }

    // 13 位税号 Mod-11 校验位。算法口径单一来源:services/recon/field_comparator.mod11_check
    // (前 12 位加权求和,权重 13..2,校验位比对第 13 位)。
    function mod11Check(raw) {
        var digits = taxDigits(raw);
        if (digits.length !== 13) return false;
        var total = 0;
        for (var i = 0; i < 12; i++) {
            total += parseInt(digits.charAt(i), 10) * (13 - i);
        }
        return (11 - (total % 11)) % 10 === parseInt(digits.charAt(12), 10);
    }

    // 是否该发起一次新查询:满 13 位 + mod-11 过检 + 跟上一次查过的号不同(防抖去重,
    // 避免同一税号在防抖窗口内被打字触发的多次 input 事件重复请求)。
    function shouldTriggerLookup(raw, lastQueriedTaxId) {
        var digits = taxDigits(raw);
        return digits.length === 13 && mod11Check(digits) && digits !== lastQueriedTaxId;
    }

    var pure = {
        taxDigits: taxDigits,
        mod11Check: mod11Check,
        shouldTriggerLookup: shouldTriggerLookup,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;
    if (!root || !root.document) return;

    // ===== 以下为浏览器编排(依赖 AI.state/AI.api/DOM)· node 不执行 =====

    var MASK_ID = 'clientNewMask';
    var LOOKUP_DEBOUNCE_MS = 350;

    var S = null;
    var lookupTimer = null;

    function esc(s) {
        return AI.state.esc(s);
    }

    function mask() {
        return document.getElementById(MASK_ID);
    }

    function taxMsgHtml() {
        if (S.mod11Warn) {
            return (
                '<span style="color:var(--warn)">' +
                esc(at('clients_new_tax_mod11_warn')) +
                '</span>'
            );
        }
        if (S.lookupStatus === 'checking') {
            return (
                '<span style="color:var(--mut)">' + esc(at('clients_new_tax_checking')) + '</span>'
            );
        }
        if (S.lookupStatus === 'found') {
            return (
                '<span style="color:var(--good)">' + esc(at('clients_new_tax_found')) + '</span>'
            );
        }
        if (S.lookupStatus === 'notfound') {
            return (
                '<span style="color:var(--mut)">' + esc(at('clients_new_tax_not_found')) + '</span>'
            );
        }
        return '';
    }

    // 用户已手输过名字时,查到的结果不直接覆盖——给一条"使用查询结果"确认(不同名才显示,
    // 名字已经跟查到的一致就没什么好确认的)。
    function nameSuggestHtml() {
        if (S.lookupStatus !== 'found' || !S.nameTouched || !S.lookupName) return '';
        var nameEl = document.getElementById('cnName');
        var current = ((nameEl && nameEl.value) || '').trim();
        if (current === S.lookupName.trim()) return '';
        return (
            '<div style="font-size:11.5px;margin-top:6px;color:var(--mut)">' +
            esc(at('clients_new_tax_use_result_hint', { name: S.lookupName })) +
            ' <button type="button" class="btn" style="padding:2px 8px;font-size:11px" data-action="cn-use-lookup-name">' +
            esc(at('clients_new_tax_use_result_btn')) +
            '</button></div>'
        );
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
            '<div id="cnNameSuggest">' +
            nameSuggestHtml() +
            '</div>' +
            '</label>' +
            '<label class="pr-lb" style="display: block; margin-bottom: 12px">' +
            esc(at('clients_new_tax_id_label')) +
            '<input id="cnTaxId" type="text" maxlength="20" value="' +
            esc(S.taxId) +
            '" />' +
            '<div id="cnTaxMsg" style="min-height: 14px; margin-top: 6px">' +
            taxMsgHtml() +
            '</div>' +
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
        if (nameInput) {
            nameInput.focus();
            nameInput.addEventListener('input', onNameInput);
        }
        var taxInput = document.getElementById('cnTaxId');
        if (taxInput) taxInput.addEventListener('input', onTaxIdInput);
        wireNameSuggestButton();
    }

    function wireNameSuggestButton() {
        var btn = document.querySelector('#cnNameSuggest [data-action="cn-use-lookup-name"]');
        if (btn) btn.onclick = applySuggestedName;
    }

    function open() {
        S.open = true;
        S.name = '';
        S.taxId = '';
        S.errKey = null;
        S.submitting = false;
        S.lookupStatus = 'idle';
        S.lookupName = null;
        S.mod11Warn = false;
        S.nameTouched = false;
        S.lastQueriedTaxId = null;
        S.lookupSeq = 0;
        render();
        document.addEventListener('keydown', onKeydown);
    }

    function close() {
        S.open = false;
        if (lookupTimer) {
            clearTimeout(lookupTimer);
            lookupTimer = null;
        }
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

    // 用户手输过名字 → 后续查询结果不再自动覆盖,改走"使用查询结果"确认路(applySuggestedName)。
    function onNameInput() {
        S.nameTouched = true;
        updateNameSuggest();
    }

    function onTaxIdInput() {
        var el = document.getElementById('cnTaxId');
        var raw = (el && el.value) || '';
        var digits = taxDigits(raw);
        S.mod11Warn = digits.length === 13 && !mod11Check(digits);
        if (digits.length !== 13) {
            // 税号改短/改动过 13 位窗口:清掉旧查询状态,别让上一个号的结果误导当前输入。
            S.lookupStatus = 'idle';
            S.lookupName = null;
            S.lastQueriedTaxId = null;
        }
        updateTaxMsg();
        if (lookupTimer) {
            clearTimeout(lookupTimer);
            lookupTimer = null;
        }
        if (shouldTriggerLookup(raw, S.lastQueriedTaxId)) {
            lookupTimer = setTimeout(function () {
                runLookup(digits);
            }, LOOKUP_DEBOUNCE_MS);
        }
    }

    function runLookup(taxId13) {
        S.lookupStatus = 'checking';
        S.lookupName = null;
        S.lastQueriedTaxId = taxId13;
        var seq = ++S.lookupSeq;
        updateTaxMsg();
        S.api
            .workspaceTaxLookup(taxId13)
            .then(function (r) {
                if (seq !== S.lookupSeq) return; // 竞态:税号又变了,丢弃过期结果
                if (r && r.ok && r.data && r.data.name) {
                    S.lookupStatus = 'found';
                    S.lookupName = r.data.name;
                    applyLookupName();
                } else {
                    S.lookupStatus = 'notfound';
                }
                updateTaxMsg();
                updateNameSuggest();
            })
            .catch(function () {
                if (seq !== S.lookupSeq) return;
                // 超时/网络失败:诚实降级为"未查到"同一条文案——不吞错(状态确实变了),
                // 但也不假装找到了,表单照常可交给用户手填。
                S.lookupStatus = 'notfound';
                updateTaxMsg();
                updateNameSuggest();
            });
    }

    function applyLookupName() {
        if (S.nameTouched) return; // 用户已手输过,交给 nameSuggestHtml() 走确认路
        var nameEl = document.getElementById('cnName');
        if (nameEl) nameEl.value = S.lookupName;
        S.name = S.lookupName;
    }

    function applySuggestedName() {
        var nameEl = document.getElementById('cnName');
        if (nameEl) nameEl.value = S.lookupName;
        S.name = S.lookupName;
        S.nameTouched = true; // 应用后视为用户已确认,后续查询不再自动覆盖
        updateNameSuggest();
    }

    function updateTaxMsg() {
        var el = document.getElementById('cnTaxMsg');
        if (el) el.innerHTML = taxMsgHtml();
    }

    function updateNameSuggest() {
        var el = document.getElementById('cnNameSuggest');
        if (el) el.innerHTML = nameSuggestHtml();
        wireNameSuggestButton();
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

    root.AI = root.AI || {};
    root.AI.clientNew = { wireButton: wireButton };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
