// ============================================================
// REFACTOR-C1 (2026-05-27) · 智能提醒(Notifications)从 home.js 抽出为 ES module
//
// 来源:home.js L17526-17823(v118.22.2 · 自动化页 alert pillar)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑。
// 入口 window._loadNotificationsPanel(集成抽屉 alert tab · L1069 loaders 惰性读 + L5524
//   typeof 守卫)+ window._rerenderNotifications(i18n 总线 · L655 守卫)· 均经 window 调
//   且惰性/守卫 · 抽成 defer module 后仍安全。
// 依赖的全局(home.js 暴露 · bare 调 · 不 import):见下方 /* global */ 声明。
// verbatim 搬迁 · 0 改逻辑(仅 prettier 重排格式)。
// ============================================================
/* global apiGet, apiPost, escapeHtml, showConfirm, token */
// ============================================================
// v118.22.2 · 智能提醒(Notifications)· 自动化页 alert pillar
// 后端:v118.22.1 (DB+CRUD+测试发送) + v118.22.1.1 (异常 hook + 大额 hook)
// ============================================================
(function () {
    'use strict';

    const $ = (id: string) => document.getElementById(id);

    async function _apiPatch(url: string, data: unknown) {
        const resp = await fetch(url, {
            method: 'PATCH',
            headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify(data || {}),
        });
        return resp;
    }
    async function _apiDelete(url: string) {
        const resp = await fetch(url, {
            method: 'DELETE',
            headers: { Authorization: 'Bearer ' + token },
        });
        return resp;
    }

    let _lineBoundCache: { bound?: boolean } | null = null; // {bound: bool}

    async function _checkLineBound() {
        try {
            _lineBoundCache = await apiGet('/api/line/binding');
        } catch (e) {
            _lineBoundCache = { bound: false };
        }
        return _lineBoundCache;
    }

    function _renderLineCheckBox(target: HTMLElement | null, bound: boolean) {
        if (!target) return;
        target.style.display = '';
        target.className = 'notif-line-check ' + (bound ? 'bound' : 'unbound');
        const icon = bound
            ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>'
            : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';
        target.innerHTML =
            icon +
            '<span>' +
            escapeHtml(t(bound ? 'notif-line-bound' : 'notif-line-not-bound')) +
            '</span>';
    }

    function _fmtTHB(amount: unknown) {
        if (amount == null) return '-';
        const n = Number(amount);
        if (isNaN(n)) return String(amount);
        return (
            '฿ ' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        );
    }

    function _fmtTime(iso: string) {
        if (!iso) return '-';
        try {
            const d = new Date(iso);
            const m = (d.getMonth() + 1).toString().padStart(2, '0');
            const day = d.getDate().toString().padStart(2, '0');
            const h = d.getHours().toString().padStart(2, '0');
            const min = d.getMinutes().toString().padStart(2, '0');
            return `${m}-${day} ${h}:${min}`;
        } catch (e) {
            return iso;
        }
    }

    function _renderRules(rules: any[]) {
        const listEl = $('notif-rules-list');
        const emptyEl = $('notif-rules-empty');
        const countEl = $('notif-rules-count');
        if (!listEl || !emptyEl) return;
        countEl!.textContent = String(rules.length);
        countEl!.className = 'auto-status-pill ' + (rules.length > 0 ? 'active' : 'none');
        if (!rules.length) {
            emptyEl.style.display = '';
            listEl.style.display = 'none';
            listEl.innerHTML = '';
            return;
        }
        emptyEl.style.display = 'none';
        listEl.style.display = '';
        listEl.innerHTML = rules
            .map((r: any) => {
                const isLarge = r.template_code === 'large_invoice';
                const tagKey = isLarge ? 'notif-rule-large-tag' : 'notif-rule-exception-tag';
                const tagClass = isLarge ? 'large' : '';
                let metaParts = [];
                if (isLarge) {
                    const thr = r.params && r.params.threshold ? _fmtTHB(r.params.threshold) : '-';
                    metaParts.push(escapeHtml(t('notif-rule-threshold-prefix')) + ' ' + thr);
                }
                if (!r.enabled)
                    metaParts.push(
                        '<span style="color:#9ca3af;">' +
                            escapeHtml(t('notif-rule-disabled')) +
                            '</span>'
                    );
                const metaHtml = metaParts.length
                    ? metaParts.join(' <span class="dot"></span> ')
                    : '';
                return `
                <div class="notif-rule-row${r.enabled ? '' : ' disabled'}" data-rule-id="${r.id}">
                    <span class="notif-rule-tmpl-badge ${tagClass}">${escapeHtml(t(tagKey))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(r.name)}</div>
                        <div class="notif-rule-meta">${metaHtml}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${r.enabled ? 'on' : ''}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t('notif-action-test'))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t('notif-action-delete'))}</button>
                    </div>
                </div>`;
            })
            .join('');
    }

    function _renderLogs(logs: any[]) {
        const listEl = $('notif-logs-list');
        if (!listEl) return;
        if (!logs.length) {
            listEl.innerHTML =
                '<div class="notif-logs-empty">' + escapeHtml(t('notif-logs-empty')) + '</div>';
            return;
        }
        listEl.innerHTML = logs
            .map((lg: any) => {
                const ok = lg.status === 'sent';
                const evtKey =
                    lg.event_type === 'exception_high'
                        ? 'notif-event-exception-high'
                        : lg.event_type === 'large_invoice'
                          ? 'notif-event-large-invoice'
                          : 'notif-event-test-send';
                const errMeta = ok ? '' : ' · ' + escapeHtml(lg.error || 'failed');
                return `
                <div class="notif-log-row">
                    <span class="notif-log-status ${ok ? '' : 'failed'}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(evtKey))}</div>
                        <div class="notif-log-meta">${escapeHtml(lg.template_code || '-')}${errMeta}</div>
                    </div>
                    <div class="notif-log-time">${_fmtTime(lg.sent_at)}</div>
                </div>`;
            })
            .join('');
    }

    async function _loadRulesAndLogs() {
        try {
            const r = await apiGet('/api/notifications/rules');
            _lastRules = (r && r.items) || [];
            _renderRules(_lastRules!);
        } catch (e) {
            console.warn('load rules fail', e);
        }
        try {
            const r = await apiGet('/api/notifications/logs?limit=20');
            _lastLogs = (r && r.items) || [];
            _renderLogs(_lastLogs!);
        } catch (e) {
            console.warn('load logs fail', e);
        }
    }

    // v118.22.2.1 · 切语言时用缓存重渲染 · 不重发 API
    let _lastRules: any[] | null = null;
    let _lastLogs: any[] | null = null;
    function _rerenderAll() {
        if (_lastRules) _renderRules(_lastRules);
        if (_lastLogs) _renderLogs(_lastLogs);
        // 弹窗里的 LINE 绑定提示也可能需要重渲染(若弹窗开着)
        const modal = $('notif-new-modal');
        if (modal && modal.style.display !== 'none' && _lineBoundCache) {
            _renderLineCheckBox(
                $('notif-line-check'),
                !!(_lineBoundCache && _lineBoundCache.bound)
            );
        }
    }

    // ── 新建弹窗 ────────────────────────────────
    function _openNewModal() {
        const modal = $('notif-new-modal');
        if (!modal) return;
        modal.style.display = '';
        ($('notif-new-name') as HTMLInputElement).value = '';
        ($('notif-new-threshold') as HTMLInputElement).value = '';
        ($('notif-new-threshold-row') as HTMLElement).style.display = 'none';
        document
            .querySelectorAll('input[name="notif-template"]')
            .forEach((r) => ((r as HTMLInputElement).checked = false));
        // 同步 LINE 绑定状态显示
        _checkLineBound().then((b) => _renderLineCheckBox($('notif-line-check'), !!(b && b.bound)));
    }
    function _closeNewModal() {
        const modal = $('notif-new-modal');
        if (modal) modal.style.display = 'none';
    }
    function _onTemplateChange() {
        const sel = document.querySelector(
            'input[name="notif-template"]:checked'
        ) as HTMLInputElement | null;
        const thRow = $('notif-new-threshold-row');
        if (!sel) {
            thRow!.style.display = 'none';
            return;
        }
        thRow!.style.display = sel.value === 'large_invoice' ? '' : 'none';
        // 自动填名称建议
        const nameInput = $('notif-new-name') as HTMLInputElement | null;
        if (nameInput && !nameInput.value.trim()) {
            nameInput.value =
                sel.value === 'large_invoice'
                    ? t('notif-tmpl-large-name')
                    : t('notif-tmpl-exception-name');
        }
    }
    async function _onSaveNew() {
        const sel = document.querySelector(
            'input[name="notif-template"]:checked'
        ) as HTMLInputElement | null;
        if (!sel) {
            showToast(t('notif-new-template'), 'error');
            return;
        }
        const name = (($('notif-new-name') as HTMLInputElement).value || '').trim();
        if (!name) {
            showToast(t('notif-name-required'), 'error');
            return;
        }
        const payload = {
            name,
            template_code: sel.value,
            params: {} as { threshold?: number },
            enabled: true,
        };
        if (sel.value === 'large_invoice') {
            const thr = parseFloat(($('notif-new-threshold') as HTMLInputElement).value || '0');
            if (!thr || thr <= 0) {
                showToast(t('notif-threshold-required'), 'error');
                return;
            }
            payload.params.threshold = thr;
        }
        try {
            const resp = await apiPost('/api/notifications/rules', payload);
            if (resp && resp.ok) {
                showToast(t('notif-toast-created'), 'success');
                _closeNewModal();
                _loadRulesAndLogs();
            } else {
                const body = (await (resp && resp.json && resp.json().catch(() => ({})))) || {};
                showToast((body && body.detail) || 'save failed', 'error');
            }
        } catch (e) {
            showToast('save failed', 'error');
        }
    }

    // ── 行内动作 ────────────────────────────────
    async function _onRuleAction(action: string | null, ruleId: string | null, btn: HTMLElement) {
        if (action === 'toggle') {
            const isOn = btn.classList.contains('on');
            const resp = await _apiPatch('/api/notifications/rules/' + ruleId, { enabled: !isOn });
            if (resp && resp.ok) {
                showToast(
                    t(isOn ? 'notif-toast-toggled-off' : 'notif-toast-toggled-on'),
                    'success'
                );
                _loadRulesAndLogs();
            } else {
                showToast('toggle failed', 'error');
            }
            return;
        }
        if (action === 'test') {
            // 先检查 LINE 是否绑定 · 没绑则提示
            const b = await _checkLineBound();
            if (!b || !b.bound) {
                showToast(t('notif-line-error-bind-first'), 'error');
                return;
            }
            const resp = await apiPost('/api/notifications/rules/' + ruleId + '/test', {});
            if (resp && resp.ok) {
                showToast(t('notif-toast-test-sent'), 'success');
                _loadRulesAndLogs();
            } else {
                const body = (await (resp && resp.json && resp.json().catch(() => ({})))) || {};
                const det = (body && body.detail) || '';
                showToast(det || t('notif-toast-test-failed'), 'error');
                _loadRulesAndLogs();
            }
            return;
        }
        if (action === 'delete') {
            const ok = await showConfirm(t('notif-confirm-delete'), { danger: true });
            if (!ok) return;
            const resp = await _apiDelete('/api/notifications/rules/' + ruleId);
            if (resp && resp.ok) {
                showToast(t('notif-toast-deleted'), 'success');
                _loadRulesAndLogs();
            } else {
                showToast('delete failed', 'error');
            }
            return;
        }
    }

    // ── 事件绑定(只绑一次)────────────────────────
    let _bound = false;
    function _bindOnce() {
        if (_bound) return;
        _bound = true;
        const newBtn = $('notif-btn-new');
        if (newBtn) newBtn.addEventListener('click', _openNewModal);
        const refreshBtn = $('notif-btn-refresh-logs');
        if (refreshBtn) refreshBtn.addEventListener('click', _loadRulesAndLogs);
        const closeBtn = $('notif-new-close');
        if (closeBtn) closeBtn.addEventListener('click', _closeNewModal);
        const cancelBtn = $('notif-new-cancel');
        if (cancelBtn) cancelBtn.addEventListener('click', _closeNewModal);
        const saveBtn = $('notif-new-save');
        if (saveBtn) saveBtn.addEventListener('click', _onSaveNew);
        document.querySelectorAll('input[name="notif-template"]').forEach((r) => {
            r.addEventListener('change', _onTemplateChange);
        });
        // 列表行内动作:事件委托
        const list = $('notif-rules-list');
        if (list) {
            list.addEventListener('click', (e) => {
                const btn = (e.target as HTMLElement).closest(
                    'button[data-action]'
                ) as HTMLElement | null;
                if (!btn) return;
                const row = btn.closest('[data-rule-id]');
                if (!row) return;
                _onRuleAction(
                    btn.getAttribute('data-action'),
                    row.getAttribute('data-rule-id'),
                    btn
                );
            });
        }
        // ESC / 点遮罩关闭
        const modal = $('notif-new-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) _closeNewModal();
            });
        }
    }

    async function load() {
        _bindOnce();
        await _loadRulesAndLogs();
    }
    window._loadNotificationsPanel = load;
    window._rerenderNotifications = _rerenderAll;
})();
