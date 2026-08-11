/* Pearnly DMS · 操作员花名册视图 · 逻辑层(挂 window.DXROSTER · 模板在 dms-roster-html.js)。
 * owner-only(nav 由 boot 按 is_owner 藏);非 owner 直调后端 403(此视图正常触达不到)。
 * 职责:拉 /api/dms/operators 四态渲染;新增操作员 / 发绑定码(大字码+倒计时)/ 编辑操作员
 * (DMS 用户名·密码各改各 + 提成归属钉死 · 体系内模态)/ 删除操作员(红键确认)/ 停用·启用
 * (pearnlyConfirm)。事件委托一次性挂 host,重渲不掉。 */
(function (root) {
    'use strict';
    function H() {
        return root.DXROSTERHTML;
    }
    function api() {
        return root.DXAPI.create();
    }
    function t(k, v) {
        return typeof root.t === 'function' ? root.t(k, v) : k;
    }
    function toast(msg, kind) {
        if (typeof root.showToast === 'function') root.showToast(msg, kind);
    }
    function showErr(el, msg) {
        if (!el) return;
        el.textContent = msg;
        el.style.display = '';
    }
    function createErrKey(code) {
        if (code === 'dms_roster.no_endpoint') return 'dms-op-err-no-endpoint';
        if (code === 'dms_roster.required_fields') return 'dms-op-err-required';
        if (code === 'dms_roster.invalid_advisor') return 'dms-op-adv-invalid';
        if (code === 'dms_roster.advisors_unavailable') return 'dms-op-adv-err';
        return 'dms-op-err-generic';
    }

    var S = {
        host: null,
        busy: false,
        items: [],
        modal: null,
        timer: null,
        expiresAt: null,
        // 顾问名单四态:loading / ok / err(code 分「没连 DMS」与「取数失败」)。
        adv: { state: 'loading', items: [], code: '' },
    };

    function clearTimer() {
        if (S.timer) {
            clearInterval(S.timer);
            S.timer = null;
        }
    }
    function remainLabel(expiresAt) {
        var ms = expiresAt.getTime() - Date.now();
        if (ms <= 0) return null;
        var sec = Math.floor(ms / 1000);
        var m = Math.floor(sec / 60);
        var s = sec % 60;
        return m + ':' + (s < 10 ? '0' : '') + s;
    }
    function byId(id) {
        return document.getElementById(id);
    }
    function opById(userId) {
        for (var i = 0; i < S.items.length; i++) {
            if (String(S.items[i].user_id) === String(userId)) return S.items[i];
        }
        return null;
    }

    function load() {
        var host = S.host;
        host.innerHTML = H().page(H().state('loading', t('dms-op-loading'), false));
        api()
            .listOperators()
            .then(function (data) {
                S.items = (data && data.items) || [];
                render();
            })
            .catch(function () {
                host.innerHTML = H().page(H().state('error', t('dms-op-error'), true));
            });
    }
    function render() {
        S.host.innerHTML = H().page(
            H().formCard() + (S.items.length ? H().listCard(S.items) : H().listEmpty())
        );
        loadAdvisors(false);
    }

    // ── 提成归属下拉(建号表单 + 编辑弹窗共用一份名单)──
    function loadAdvisors(force) {
        if (!force && S.adv.state === 'ok') return void paintAdvisors();
        S.adv = { state: 'loading', items: [], code: '' };
        paintAdvisors();
        api()
            .listAdvisors()
            .then(function (d) {
                S.adv =
                    d && d.ok
                        ? { state: 'ok', items: d.advisors || [], code: '' }
                        : { state: 'err', items: [], code: (d && d.code) || 'fetch_failed' };
                paintAdvisors();
            })
            .catch(function (err) {
                S.adv = { state: 'err', items: [], code: (err && err.code) || 'fetch_failed' };
                paintAdvisors();
            });
    }
    function paintAdvisors() {
        var boxes = document.querySelectorAll('[data-adv-field]');
        for (var i = 0; i < boxes.length; i++) paintAdvisorField(boxes[i]);
    }
    function paintAdvisorField(box) {
        var sel = box.querySelector('select');
        var hint = box.querySelector('[data-adv-hint]');
        if (!sel || !hint) return;
        if (S.adv.state !== 'ok') {
            // 名单不可信时锁住下拉,原样显示当前归属(加载中显示进度)——绝不冒充「自动」。
            var frozen =
                S.adv.state === 'loading'
                    ? t('dms-op-adv-loading')
                    : box.getAttribute('data-adv-label') || '';
            sel.innerHTML = H().frozenOption(frozen);
            sel.disabled = true;
            hint.innerHTML =
                S.adv.state === 'err'
                    ? H().advisorHint(
                          t(
                              S.adv.code === 'no_endpoint'
                                  ? 'dms-op-err-no-endpoint'
                                  : 'dms-op-adv-err'
                          ),
                          true
                      )
                    : '';
            var retry = hint.querySelector('[data-adv-retry]');
            if (retry)
                retry.addEventListener('click', function () {
                    loadAdvisors(true);
                });
            return;
        }
        sel.innerHTML = H().advisorOptions(
            S.adv.items,
            sel.value || box.getAttribute('data-adv-selected') || ''
        );
        sel.disabled = false;
        hint.innerHTML = S.adv.items.length ? '' : H().advisorHint(t('dms-op-adv-empty'), false);
    }
    // 只有名单可信(ok)且真被改过才带进请求:取数失败时下拉里只剩一个占位项,照发等于
    // 把老板钉好的归属静默清成自动 —— 提成算给谁不能这么漂。返回 null = 本次不带该字段。
    function advisorPayload(selectId) {
        var sel = byId(selectId);
        if (!sel || S.adv.state !== 'ok') return null;
        var box = sel.closest('[data-adv-field]');
        var was = (box && box.getAttribute('data-adv-selected')) || '';
        return sel.value === was ? null : sel.value;
    }

    // ── 新增操作员 ──
    function doCreate() {
        if (S.busy) return;
        var host = S.host;
        var name = (byId('dms-op-name') || {}).value || '';
        var user = (byId('dms-op-user') || {}).value || '';
        var pass = (byId('dms-op-pass') || {}).value || '';
        var roleEl = host.querySelector('input[name="dms-op-role"]:checked');
        var role = roleEl ? roleEl.value : 'sales';
        var errEl = byId('dms-op-form-err');
        if (!name.trim() || !user.trim() || !pass) {
            return void showErr(errEl, t('dms-op-err-required'));
        }
        S.busy = true;
        var btn = byId('dms-op-create');
        if (btn) btn.disabled = true;
        var payload = {
            display_name: name.trim(),
            dms_username: user.trim(),
            dms_password: pass,
            dms_role: role,
        };
        var advisor = advisorPayload('dms-op-advisor');
        if (advisor) payload.dms_advisor_id = advisor; // 空 = 自动匹配 = 不必钉
        api()
            .createOperator(payload)
            .then(function () {
                S.busy = false;
                toast(t('dms-op-add-ok'), 'success');
                load(); // 重渲清空全部输入(含密码)
            })
            .catch(function (err) {
                S.busy = false;
                if (btn) btn.disabled = false;
                showErr(errEl, t(createErrKey(err && err.code)));
            });
    }

    // ── 停用 / 启用 ──
    function doToggle(userId, activate) {
        var op = opById(userId);
        if (!op) return;
        var msg = activate
            ? t('dms-op-confirm-activate', { name: op.display_name })
            : t('dms-op-confirm-deactivate', { name: op.display_name });
        root.pearnlyConfirm(msg).then(function (ok) {
            if (!ok) return;
            api()
                .setOperatorStatus(userId, activate ? 'active' : 'inactive')
                .then(function () {
                    toast(activate ? t('dms-op-activated') : t('dms-op-deactivated'), 'success');
                    load();
                })
                .catch(function () {
                    toast(t('dms-op-err-generic'), 'error');
                });
        });
    }

    // ── 模态壳(绑定码 / 换密码共用挂载/卸载) ──
    function openModal(html) {
        closeModal();
        var ov = document.createElement('div');
        ov.className = 'dms-op-modal-host';
        ov.innerHTML = html;
        document.body.appendChild(ov);
        S.modal = ov;
        ov.addEventListener('click', function (e) {
            if (e.target === ov || e.target.classList.contains('dms-op-modal')) closeModal();
        });
        return ov;
    }
    function closeModal() {
        clearTimer();
        S.expiresAt = null;
        if (S.modal) {
            S.modal.remove();
            S.modal = null;
        }
    }

    // ── 发绑定码(大字码 + 倒计时) ──
    function openBindCode(userId) {
        var op = opById(userId);
        if (!op) return;
        openModal(H().codeOverlay(op.display_name));
        var close = byId('dms-op-code-close');
        if (close) close.addEventListener('click', closeModal);
        var regen = byId('dms-op-code-regen');
        if (regen)
            regen.addEventListener('click', function () {
                requestCode(userId);
            });
        requestCode(userId);
    }
    function requestCode(userId) {
        var regen = byId('dms-op-code-regen');
        if (regen) regen.disabled = true;
        api()
            .operatorBindCode(userId)
            .then(function (d) {
                if (regen) regen.disabled = false;
                var valEl = byId('dms-op-code-val');
                if (valEl) {
                    valEl.textContent = d.code || '······';
                    valEl.classList.remove('expired');
                }
                S.expiresAt = d.expires_at ? new Date(d.expires_at) : null;
                startCountdown();
            })
            .catch(function () {
                if (regen) regen.disabled = false;
                toast(t('dms-op-code-fail'), 'error');
            });
    }
    function startCountdown() {
        clearTimer();
        tick();
        S.timer = setInterval(tick, 1000);
    }
    function tick() {
        var el = byId('dms-op-code-cd');
        if (!el || !S.expiresAt) {
            clearTimer();
            return;
        }
        var label = remainLabel(S.expiresAt);
        if (!label) {
            clearTimer();
            var valEl = byId('dms-op-code-val');
            if (valEl) valEl.classList.add('expired');
            el.textContent = t('dms-op-code-expired');
            return;
        }
        el.textContent = t('dms-op-code-expires') + ' ' + label;
    }

    // ── 编辑操作员(DMS 用户名/密码各改各 · 提成归属下拉 · 都没动则拦下)──
    function openAcc(userId) {
        var op = opById(userId);
        if (!op) return;
        openModal(H().accModal(op));
        loadAdvisors(false);
        var cancel = byId('dms-op-pw-cancel');
        if (cancel) cancel.addEventListener('click', closeModal);
        var save = byId('dms-op-pw-save');
        if (save)
            save.addEventListener('click', function () {
                saveAcc(userId);
            });
    }
    function saveAcc(userId) {
        var userEl = byId('dms-op-acc-user-input');
        var pwEl = byId('dms-op-pw-input');
        var errEl = byId('dms-op-pw-err');
        var user = ((userEl && userEl.value) || '').trim();
        var pw = (pwEl && pwEl.value) || '';
        var payload = {};
        if (user) payload.dms_username = user; // 留空字段不进 PATCH body → 后端不动该配置
        if (pw) payload.dms_password = pw;
        var advisor = advisorPayload('dms-op-acc-advisor');
        if (advisor !== null) payload.dms_advisor_id = advisor; // 空串 = 清除钉死回自动匹配
        if (!Object.keys(payload).length) {
            return void showErr(errEl, t('dms-op-edit-nochange'));
        }
        var save = byId('dms-op-pw-save');
        if (save) save.disabled = true;
        api()
            .updateOperator(userId, payload)
            .then(function () {
                toast(t('dms-op-edit-saved'), 'success');
                closeModal();
                load(); // 归属列要跟着变
            })
            .catch(function (err) {
                if (save) save.disabled = false;
                showErr(errEl, t(createErrKey(err && err.code)));
            });
    }

    // ── 删除操作员 ──
    function doDelete(userId) {
        var op = opById(userId);
        if (!op) return;
        openModal(H().deleteModal(op.display_name));
        var cancel = byId('dms-op-del-cancel');
        if (cancel) cancel.addEventListener('click', closeModal);
        var confirm = byId('dms-op-del-confirm');
        if (confirm)
            confirm.addEventListener('click', function () {
                confirmDelete(userId);
            });
    }
    function confirmDelete(userId) {
        var confirm = byId('dms-op-del-confirm');
        if (confirm) confirm.disabled = true;
        api()
            .deleteOperator(userId)
            .then(function () {
                toast(t('dms-op-deleted'), 'success');
                closeModal();
                load(); // 重渲 → 该行消失
            })
            .catch(function () {
                if (confirm) confirm.disabled = false;
                toast(t('dms-op-err-generic'), 'error');
            });
    }

    function onClick(e) {
        if (e.target.closest('#dms-op-retry')) return void load();
        if (e.target.closest('#dms-op-create')) return void doCreate();
        var act = e.target.closest('[data-op-act]');
        if (!act) return;
        var id = act.getAttribute('data-op-id');
        var kind = act.getAttribute('data-op-act');
        if (kind === 'code') return void openBindCode(id);
        if (kind === 'pw') return void openAcc(id);
        if (kind === 'deactivate') return void doToggle(id, false);
        if (kind === 'activate') return void doToggle(id, true);
        if (kind === 'del') return void doDelete(id);
    }

    function mount(hostSel) {
        var host = document.querySelector(hostSel);
        if (!host) return;
        S.host = host;
        S.busy = false;
        closeModal();
        if (!host._rosterWired) {
            host.addEventListener('click', onClick);
            host._rosterWired = true;
        }
        load();
    }

    root.DXROSTER = { mount: mount };
})(typeof self !== 'undefined' ? self : this);
