// ============================================================
// REFACTOR-C1 (2026-05-27) · 邮箱抓取 email-ingest 从 home.js 抽出为 ES module
//
// 来源:home.js L6760-7418 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global token, escapeHtml, showConfirm, _showSessionRevokedModal */
// ============================================================
// v0.17 · M6 · 邮箱抓取 (Email Ingest)
// ============================================================
import { S } from './email-ingest-store.js'; // REFACTOR-WB-modularize · 共享状态
import {
    openModal,
    closeModal,
    applyPreset,
    autoDetectPresetByAddress,
    readModalForm,
    showTestResult,
    testFromModal,
} from './email-ingest-form.js'; // REFACTOR-WB-modularize · 绑定 modal/表单拆出
(function () {
    async function load() {
        const emptyEl = document.getElementById('email-empty');
        const cardEl = document.getElementById('email-account-card');
        const logsEl = document.getElementById('email-logs-section');
        if (!emptyEl || !cardEl) return;
        try {
            const resp = await fetch('/api/email-ingest/account', {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (resp.status === 401) {
                localStorage.removeItem('mrpilot_token');
                const _bd = await resp.json().catch(() => ({}));
                const _dc =
                    typeof _bd.detail === 'string'
                        ? _bd.detail
                        : (_bd.detail && _bd.detail.code) || '';
                if (_dc === 'auth.session_revoked') {
                    _showSessionRevokedModal();
                    return;
                }
                window.location.href = '/';
                return;
            }
            if (!resp.ok) {
                setStatus('none');
                return;
            }
            const data = await resp.json();
            S.account = data.account || null;
            S.presets = data.presets || {};
            S.loaded = true;
            render();
            if (S.account) loadLogs();
        } catch (e) {
            console.error('[email-ingest] load failed', e);
            setStatus('none');
        }
    }

    function render() {
        const emptyEl = document.getElementById('email-empty');
        const cardEl = document.getElementById('email-account-card');
        const logsEl = document.getElementById('email-logs-section');

        if (!S.account) {
            emptyEl.style.display = '';
            cardEl.style.display = 'none';
            if (logsEl) logsEl.style.display = 'none';
            setStatus('none');
            return;
        }

        emptyEl.style.display = 'none';
        cardEl.style.display = '';
        if (logsEl) logsEl.style.display = '';

        const addrEl = document.getElementById('email-account-addr');
        const hostEl = document.getElementById('email-account-host');
        const lastEl = document.getElementById('email-account-last');
        const errEl = document.getElementById('email-last-error');
        const tgl = document.getElementById('email-enabled-toggle');

        if (addrEl) addrEl.textContent = S.account.email_address || '-';
        if (hostEl)
            hostEl.textContent = `${S.account.imap_host || '-'}:${S.account.imap_port || 993}`;

        if (lastEl) {
            const last = S.account.last_fetched_at;
            if (!last) {
                lastEl.textContent = t('email-last-never');
            } else {
                const timeStr = formatTime(last);
                const ok = !S.account.last_error;
                lastEl.textContent = ok
                    ? t('email-last-ok', { time: timeStr })
                    : t('email-last-fail', { time: timeStr });
            }
        }

        if (errEl) {
            if (S.account.last_error) {
                errEl.style.display = '';
                errEl.textContent = humanizeEmailError(S.account.last_error);
            } else {
                errEl.style.display = 'none';
            }
        }

        if (tgl) tgl.checked = !!S.account.enabled;

        // 状态 pill
        if (!S.account.enabled) setStatus('off');
        else if (S.account.last_error) setStatus('error');
        else setStatus('on');
    }

    function setStatus(kind) {
        const pill = document.getElementById('email-status-summary');
        if (!pill) return;
        pill.classList.remove('none', 'ready', 'active', 'coming');
        let key = 'auto-status-loading';
        if (kind === 'none') {
            key = 'email-status-none';
            pill.classList.add('none');
        } else if (kind === 'on') {
            key = 'email-status-on';
            pill.classList.add('active');
        } else if (kind === 'off') {
            key = 'email-status-off';
            pill.classList.add('coming');
        } else if (kind === 'error') {
            key = 'email-status-error';
            pill.classList.add('none');
        }
        pill.setAttribute('data-i18n', key);
        pill.textContent = t(key);
    }

    function formatTime(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '';
        const pad = (n) => String(n).padStart(2, '0');
        return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }

    function humanizeEmailError(raw) {
        if (!raw) return '';
        const r = String(raw);
        if (/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(r))
            return t('email-test-auth-fail');
        if (/timeout|timed out/i.test(r)) return t('email.timeout');
        if (/ENOTFOUND|getaddrinfo/i.test(r)) return r;
        return r;
    }

    async function save() {
        const form = readModalForm();
        if (!form.email_address) {
            showTestResult('fail', t('email-addr-required'));
            return;
        }
        if (S.modalMode === 'new' && !form.password) {
            showTestResult('fail', t('email-password-required'));
            return;
        }
        if (!form.imap_host) {
            showTestResult('fail', t('email-host-required'));
            return;
        }

        const btn = document.getElementById('btn-email-modal-save');
        if (btn) btn.disabled = true;

        const body = { ...form };
        // edit 模式 · 空密码表示保留原密码
        if (S.modalMode === 'edit' && !body.password) delete body.password;

        try {
            const resp = await fetch('/api/email-ingest/account', {
                method: 'PUT',
                headers: {
                    Authorization: 'Bearer ' + token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body),
            });
            const data = await resp.json().catch(() => ({}));
            if (resp.ok && data.ok) {
                S.account = data.account;
                showToast(t('email-save-ok'), 'success');
                closeModal();
                render();
                loadLogs();
            } else {
                const detail = data.detail || '';
                const key = 'email.' + detail.split('.').slice(-1)[0];
                showTestResult('fail', t(key) !== key ? t(key) : t('email-save-fail'));
            }
        } catch (e) {
            showTestResult('fail', t('email-save-fail'));
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    async function unbind() {
        if (!S.account) return;
        const ok = await showConfirm(
            t('email-unbind-confirm', { email: S.account.email_address }),
            { danger: true, okText: t('email-btn-unbind') }
        );
        if (!ok) return;
        try {
            const resp = await fetch('/api/email-ingest/account', {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + token },
            });
            if (resp.ok) {
                S.account = null;
                showToast(t('email-unbind-ok'), 'success');
                render();
                const listEl = document.getElementById('email-logs-list');
                if (listEl) listEl.innerHTML = '';
            } else {
                showToast(t('email-unbind-fail'), 'error');
            }
        } catch (e) {
            showToast(t('email-unbind-fail'), 'error');
        }
    }

    async function trigger() {
        if (!S.account || S.triggering) return;
        if (!S.account.enabled) {
            showToast(t('email.disabled'), 'error');
            return;
        }
        S.triggering = true;
        const btn = document.getElementById('btn-email-trigger');
        const origLabel = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span>${escapeHtml(t('email-trigger-running'))}</span>`;
        }
        try {
            const resp = await fetch('/api/email-ingest/trigger', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token },
            });
            const data = await resp.json().catch(() => ({}));
            if (!resp.ok) {
                const detail = data.detail || '';
                const key = 'email.' + detail.split('.').slice(-1)[0];
                showToast(t(key) !== key ? t(key) : t('email-trigger-fail'), 'error');
            } else {
                const scanned = data.emails_scanned || 0;
                const ok = data.ocr_succeeded || 0;
                const fail = data.ocr_failed || 0;
                if (scanned === 0 && ok === 0 && fail === 0) {
                    showToast(t('email-trigger-empty'), 'success');
                } else {
                    showToast(
                        t('email-trigger-result', { scanned, ok, fail }),
                        fail > 0 ? 'warn' : 'success'
                    );
                }
            }
            await load();
        } catch (e) {
            showToast(t('email-trigger-fail'), 'error');
        } finally {
            S.triggering = false;
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = origLabel;
            }
        }
    }

    async function toggleEnabled() {
        if (!S.account) return;
        const tgl = document.getElementById('email-enabled-toggle');
        const newVal = !!(tgl && tgl.checked);
        const prev = S.account.enabled;
        try {
            const resp = await fetch('/api/email-ingest/account', {
                method: 'PUT',
                headers: {
                    Authorization: 'Bearer ' + token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email_address: S.account.email_address,
                    imap_host: S.account.imap_host,
                    imap_port: S.account.imap_port,
                    imap_use_ssl: S.account.imap_use_ssl,
                    folder: S.account.folder || 'INBOX',
                    filter_subject: S.account.filter_subject || null,
                    filter_sender: S.account.filter_sender || null,
                    mark_as_read: S.account.mark_as_read !== false,
                    enabled: newVal,
                }),
            });
            const data = await resp.json().catch(() => ({}));
            if (resp.ok && data.ok) {
                S.account = data.account;
                render();
            } else {
                if (tgl) tgl.checked = prev;
                showToast(t('email-toggle-fail'), 'error');
            }
        } catch (e) {
            if (tgl) tgl.checked = prev;
            showToast(t('email-toggle-fail'), 'error');
        }
    }

    // ---------- logs ----------
    async function loadLogs() {
        const listEl = document.getElementById('email-logs-list');
        if (!listEl) return;
        listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-loading'))}</div>`;
        try {
            const resp = await fetch('/api/email-ingest/logs?limit=20', {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) {
                listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
                return;
            }
            const logs = await resp.json();
            if (!Array.isArray(logs) || logs.length === 0) {
                listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('email-logs-empty'))}</div>`;
                return;
            }
            listEl.innerHTML = logs.map(renderLogRow).join('');
        } catch (e) {
            listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
        }
    }

    function renderLogRow(log) {
        const time = formatTime(log.created_at);
        const status = log.status || 'failed';
        const cls = status === 'success' ? 'ok' : status === 'partial' ? 'partial' : 'fail';
        const icon = status === 'success' ? '✓' : status === 'partial' ? '◐' : '✗';
        const tag =
            log.trigger === 'manual'
                ? `<span class="log-tag manual">${escapeHtml(t('email-log-tag-manual'))}</span>`
                : `<span class="log-tag auto">${escapeHtml(t('email-log-tag-auto'))}</span>`;
        const counts = t('email-log-counts', {
            scanned: log.emails_scanned || 0,
            att: log.attachments_found || 0,
            ok: log.ocr_succeeded || 0,
            fail: log.ocr_failed || 0,
        });
        const elapsed = (log.elapsed_ms || 0) + 'ms';
        return `
            <div class="email-log-row ${cls}">
                <span class="log-time">${escapeHtml(time)}</span>
                <span class="log-status">${icon}</span>
                ${tag}
                <span class="log-counts">${escapeHtml(counts)}</span>
                <span class="log-elapsed">${escapeHtml(elapsed)}</span>
            </div>
        `;
    }

    // ---------- wire ----------
    function wire() {
        const bindBtn = document.getElementById('btn-email-bind');
        if (bindBtn) bindBtn.addEventListener('click', () => openModal('new'));

        const editBtn = document.getElementById('btn-email-edit');
        if (editBtn) editBtn.addEventListener('click', () => openModal('edit'));

        const unbindBtn = document.getElementById('btn-email-unbind');
        if (unbindBtn) unbindBtn.addEventListener('click', unbind);

        const triggerBtn = document.getElementById('btn-email-trigger');
        if (triggerBtn) triggerBtn.addEventListener('click', trigger);

        const toggle = document.getElementById('email-enabled-toggle');
        if (toggle) toggle.addEventListener('change', toggleEnabled);

        const closeBtn = document.getElementById('email-modal-close');
        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        const cancelBtn = document.getElementById('btn-email-modal-cancel');
        if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

        const testBtn = document.getElementById('btn-email-modal-test');
        if (testBtn) testBtn.addEventListener('click', testFromModal);

        const saveBtn = document.getElementById('btn-email-modal-save');
        if (saveBtn) saveBtn.addEventListener('click', save);

        const presetSel = document.getElementById('email-preset');
        if (presetSel) presetSel.addEventListener('change', (e) => applyPreset(e.target.value));

        // v95 · 邮箱输入框自动检测域名 · 触发 preset
        const addrEl = document.getElementById('email-address');
        if (addrEl && !addrEl.dataset.autoBound) {
            addrEl.dataset.autoBound = '1';
            addrEl.addEventListener('blur', (e) =>
                autoDetectPresetByAddress((e.target.value || '').trim())
            );
            addrEl.addEventListener('input', (e) => {
                const v = (e.target.value || '').trim();
                // 输入到域名后(包含 . 至少 2 段)立刻触发
                if (v.includes('@') && v.split('@')[1].includes('.')) {
                    autoDetectPresetByAddress(v);
                }
            });
        }

        const refreshLogsBtn = document.getElementById('btn-email-refresh-logs');
        if (refreshLogsBtn)
            refreshLogsBtn.addEventListener('click', () => {
                refreshLogsBtn.classList.add('spinning');
                setTimeout(() => refreshLogsBtn.classList.remove('spinning'), 600);
                loadLogs();
            });
    }

    wire();

    // 对外挂载:switchAutomationTab 首次进入 'email' 时调用
    window._loadEmailIngestPanel = load;
    // applyLang 切语言时重渲染
    window._rerenderEmailIngest = function () {
        if (!S.loaded) return;
        render();
        const logsSection = document.getElementById('email-logs-section');
        if (S.account && logsSection && logsSection.open) loadLogs();
    };

    // v95 · 30s 自动刷新日志(用户在邮箱 tab 时才跑)
    window._startEmailLogAutoRefresh = function () {
        if (S.autoRefreshTimer) return;
        S.autoRefreshTimer = setInterval(() => {
            if (S.account && S.loaded) loadLogs();
        }, 30000);
    };
    window._stopEmailLogAutoRefresh = function () {
        if (S.autoRefreshTimer) {
            clearInterval(S.autoRefreshTimer);
            S.autoRefreshTimer = null;
        }
    };
})();
