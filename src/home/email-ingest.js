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
(function () {
    let _emailAccount = null; // 已绑定的账号(或 null)
    let _emailPresets = null; // {gmail: {host,port,ssl}, ...}
    let _emailModalMode = 'new'; // 'new' | 'edit'
    let _emailLoaded = false; // 避免重复拉
    let _emailTriggering = false;

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
            _emailAccount = data.account || null;
            _emailPresets = data.presets || {};
            _emailLoaded = true;
            render();
            if (_emailAccount) loadLogs();
        } catch (e) {
            console.error('[email-ingest] load failed', e);
            setStatus('none');
        }
    }

    function render() {
        const emptyEl = document.getElementById('email-empty');
        const cardEl = document.getElementById('email-account-card');
        const logsEl = document.getElementById('email-logs-section');

        if (!_emailAccount) {
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

        if (addrEl) addrEl.textContent = _emailAccount.email_address || '-';
        if (hostEl)
            hostEl.textContent = `${_emailAccount.imap_host || '-'}:${_emailAccount.imap_port || 993}`;

        if (lastEl) {
            const last = _emailAccount.last_fetched_at;
            if (!last) {
                lastEl.textContent = t('email-last-never');
            } else {
                const timeStr = formatTime(last);
                const ok = !_emailAccount.last_error;
                lastEl.textContent = ok
                    ? t('email-last-ok', { time: timeStr })
                    : t('email-last-fail', { time: timeStr });
            }
        }

        if (errEl) {
            if (_emailAccount.last_error) {
                errEl.style.display = '';
                errEl.textContent = humanizeEmailError(_emailAccount.last_error);
            } else {
                errEl.style.display = 'none';
            }
        }

        if (tgl) tgl.checked = !!_emailAccount.enabled;

        // 状态 pill
        if (!_emailAccount.enabled) setStatus('off');
        else if (_emailAccount.last_error) setStatus('error');
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

    // ---------- modal ----------
    function openModal(mode) {
        _emailModalMode = mode;
        const overlay = document.getElementById('email-modal');
        if (!overlay) return;

        // 填 preset select
        const sel = document.getElementById('email-preset');
        sel.innerHTML = '';
        const presets = _emailPresets || {};
        const order = ['gmail', 'outlook', 'yahoo', 'icloud', 'qq', '163', 'custom'];
        const labels = {
            gmail: 'Gmail',
            outlook: 'Outlook / Office365',
            yahoo: 'Yahoo Mail',
            icloud: 'iCloud',
            qq: 'QQ 邮箱',
            163: '网易 163',
        };
        order.forEach((k) => {
            if (!presets[k]) return;
            const opt = document.createElement('option');
            opt.value = k;
            opt.textContent = k === 'custom' ? t('email-preset-custom') : labels[k] || k;
            sel.appendChild(opt);
        });

        const titleEl = document.getElementById('email-modal-title');
        const addrEl = document.getElementById('email-address');
        const pwdEl = document.getElementById('email-password');
        const hostEl = document.getElementById('email-imap-host');
        const portEl = document.getElementById('email-imap-port');
        const sslEl = document.getElementById('email-imap-ssl');
        const folderEl = document.getElementById('email-folder');
        const markEl = document.getElementById('email-mark-read');
        const enaEl = document.getElementById('email-bind-enabled');
        const testResult = document.getElementById('email-test-result');
        const advDetails = document.getElementById('email-adv-details');

        if (testResult) {
            testResult.style.display = 'none';
            testResult.textContent = '';
        }

        if (mode === 'edit' && _emailAccount) {
            titleEl.setAttribute('data-i18n', 'email-modal-title-edit');
            titleEl.textContent = t('email-modal-title-edit');
            addrEl.value = _emailAccount.email_address || '';
            pwdEl.value = '';
            pwdEl.setAttribute('data-i18n-placeholder', 'email-field-password-edit-ph');
            pwdEl.placeholder = t('email-field-password-edit-ph');
            hostEl.value = _emailAccount.imap_host || '';
            portEl.value = _emailAccount.imap_port || 993;
            sslEl.checked = _emailAccount.imap_use_ssl !== false;
            folderEl.value = _emailAccount.folder || 'INBOX';
            markEl.checked = _emailAccount.mark_as_read !== false;
            enaEl.checked = _emailAccount.enabled !== false;
            // v95 · 编辑时回填过滤器
            const fSenderEl = document.getElementById('email-filter-sender');
            const fSubjectEl = document.getElementById('email-filter-subject');
            if (fSenderEl) fSenderEl.value = _emailAccount.filter_sender || '';
            if (fSubjectEl) fSubjectEl.value = _emailAccount.filter_subject || '';
            // v0.17.9 · 高亮当前 interval
            setIntervalUI(_emailAccount.interval_min || 15);
            // 尝试按 host 匹配 preset
            sel.value = matchPreset(_emailAccount.imap_host) || 'custom';
            if (advDetails) advDetails.open = true;
        } else {
            titleEl.setAttribute('data-i18n', 'email-modal-title-new');
            titleEl.textContent = t('email-modal-title-new');
            addrEl.value = '';
            pwdEl.value = '';
            pwdEl.setAttribute('data-i18n-placeholder', 'email-field-password-ph');
            pwdEl.placeholder = t('email-field-password-ph');
            sel.value = 'gmail';
            applyPreset('gmail');
            folderEl.value = 'INBOX';
            markEl.checked = true;
            enaEl.checked = true;
            // v95 · 新增时清空过滤器
            const fSenderEl = document.getElementById('email-filter-sender');
            const fSubjectEl = document.getElementById('email-filter-subject');
            if (fSenderEl) fSenderEl.value = '';
            if (fSubjectEl) fSubjectEl.value = '';
            // v0.17.9 · 默认标准档(15 分钟)
            setIntervalUI(15);
            if (advDetails) advDetails.open = false;
        }

        // v0.17.9 · 绑按钮组点击事件(只绑一次)
        bindIntervalOptions();

        overlay.style.display = 'flex';
        setTimeout(() => addrEl.focus(), 60);
    }

    function closeModal() {
        const overlay = document.getElementById('email-modal');
        if (overlay) overlay.style.display = 'none';
    }

    function applyPreset(key) {
        const preset = (_emailPresets || {})[key];
        if (!preset || key === 'custom') return;
        const hostEl = document.getElementById('email-imap-host');
        const portEl = document.getElementById('email-imap-port');
        const sslEl = document.getElementById('email-imap-ssl');
        if (hostEl) hostEl.value = preset.host || '';
        if (portEl) portEl.value = preset.port || 993;
        if (sslEl) sslEl.checked = preset.ssl !== false;
    }

    // v95 · 域名 → preset key 映射(智能预设)
    const _DOMAIN_TO_PRESET = {
        'gmail.com': 'gmail',
        'googlemail.com': 'gmail',
        'outlook.com': 'outlook',
        'hotmail.com': 'outlook',
        'live.com': 'outlook',
        'office365.com': 'outlook',
        'msn.com': 'outlook',
        'yahoo.com': 'yahoo',
        'yahoo.co.jp': 'yahoo',
        'icloud.com': 'icloud',
        'me.com': 'icloud',
        'mac.com': 'icloud',
        'qq.com': 'qq',
        'foxmail.com': 'qq',
        '163.com': '163',
        '126.com': '163',
        'yeah.net': '163',
    };

    // v95 · 输入邮箱时自动检测后缀 · 选 preset · 应用 IMAP
    function autoDetectPresetByAddress(addr) {
        if (!addr || !addr.includes('@')) return;
        const domain = addr.split('@')[1].toLowerCase().trim();
        const key = _DOMAIN_TO_PRESET[domain];
        if (!key) return;
        const sel = document.getElementById('email-preset');
        if (!sel) return;
        // 只有用户没手动改过 preset 时才自动覆盖
        const currentPreset = sel.value;
        if (currentPreset && currentPreset !== 'custom' && currentPreset !== '') {
            // 已经是某个 preset · 不打扰
            if (currentPreset === key) return;
        }
        sel.value = key;
        applyPreset(key);
    }

    function matchPreset(host) {
        if (!host) return null;
        const presets = _emailPresets || {};
        for (const k in presets) {
            if (k === 'custom') continue;
            if (presets[k] && presets[k].host === host) return k;
        }
        return null;
    }

    function readModalForm() {
        // v0.17.9 · 抓取频率(从 active 按钮读)
        const activeIntervalBtn = document.querySelector(
            '#email-interval-options .email-interval-btn.active'
        );
        const intervalMin = activeIntervalBtn
            ? parseInt(activeIntervalBtn.dataset.interval, 10)
            : 15;
        return {
            email_address: (document.getElementById('email-address').value || '').trim(),
            password: document.getElementById('email-password').value || '',
            imap_host: (document.getElementById('email-imap-host').value || '').trim(),
            imap_port:
                parseInt(document.getElementById('email-imap-port').value || '993', 10) || 993,
            imap_use_ssl: document.getElementById('email-imap-ssl').checked,
            folder: (document.getElementById('email-folder').value || 'INBOX').trim() || 'INBOX',
            mark_as_read: document.getElementById('email-mark-read').checked,
            enabled: document.getElementById('email-bind-enabled').checked,
            interval_min: [5, 15, 60].includes(intervalMin) ? intervalMin : 15,
            // v95 · 过滤器
            filter_sender:
                (document.getElementById('email-filter-sender').value || '').trim() || null,
            filter_subject:
                (document.getElementById('email-filter-subject').value || '').trim() || null,
        };
    }

    // v0.17.9 · 间隔按钮组点击切换 · 委托到容器
    function bindIntervalOptions() {
        const opts = document.getElementById('email-interval-options');
        if (!opts || opts._bound) return;
        opts._bound = true;
        opts.addEventListener('click', (e) => {
            const btn = e.target.closest('.email-interval-btn');
            if (!btn) return;
            opts.querySelectorAll('.email-interval-btn').forEach((b) =>
                b.classList.remove('active')
            );
            btn.classList.add('active');
        });
    }

    // v0.17.9 · 把 modal 当前的 interval 高亮(open modal 时调)
    function setIntervalUI(intervalMin) {
        const v = [5, 15, 60].includes(intervalMin) ? intervalMin : 15;
        const opts = document.getElementById('email-interval-options');
        if (!opts) return;
        opts.querySelectorAll('.email-interval-btn').forEach((b) => {
            b.classList.toggle('active', parseInt(b.dataset.interval, 10) === v);
        });
    }

    function showTestResult(kind, text) {
        const el = document.getElementById('email-test-result');
        if (!el) return;
        el.style.display = '';
        el.textContent = text;
        el.className =
            'form-test-result ' + (kind === 'ok' ? 'ok' : kind === 'running' ? 'running' : 'fail');
    }

    async function testFromModal() {
        const form = readModalForm();
        if (!form.email_address) {
            showTestResult('fail', t('email-addr-required'));
            return;
        }
        if (!form.password) {
            showTestResult('fail', t('email-password-required'));
            return;
        }
        if (!form.imap_host) {
            showTestResult('fail', t('email-host-required'));
            return;
        }

        const btn = document.getElementById('btn-email-modal-test');
        if (btn) btn.disabled = true;
        showTestResult('running', t('email-test-running'));
        try {
            const resp = await fetch('/api/email-ingest/test', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email_address: form.email_address,
                    password: form.password,
                    imap_host: form.imap_host,
                    imap_port: form.imap_port,
                    imap_use_ssl: form.imap_use_ssl,
                    folder: form.folder,
                }),
            });
            const data = await resp.json().catch(() => ({}));
            if (resp.ok && data.success) {
                showTestResult(
                    'ok',
                    t('email-test-ok', { folder: form.folder, n: data.folder_count ?? '?' })
                );
            } else {
                const err = data.error_msg || '';
                if (err === 'auth_failed' || /auth/i.test(err)) {
                    showTestResult('fail', t('email-test-auth-fail'));
                } else {
                    showTestResult('fail', t('email-test-fail', { msg: err || resp.status }));
                }
            }
        } catch (e) {
            showTestResult('fail', t('email-test-fail', { msg: String(e).slice(0, 120) }));
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    async function save() {
        const form = readModalForm();
        if (!form.email_address) {
            showTestResult('fail', t('email-addr-required'));
            return;
        }
        if (_emailModalMode === 'new' && !form.password) {
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
        if (_emailModalMode === 'edit' && !body.password) delete body.password;

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
                _emailAccount = data.account;
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
        if (!_emailAccount) return;
        const ok = await showConfirm(
            t('email-unbind-confirm', { email: _emailAccount.email_address }),
            { danger: true, okText: t('email-btn-unbind') }
        );
        if (!ok) return;
        try {
            const resp = await fetch('/api/email-ingest/account', {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + token },
            });
            if (resp.ok) {
                _emailAccount = null;
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
        if (!_emailAccount || _emailTriggering) return;
        if (!_emailAccount.enabled) {
            showToast(t('email.disabled'), 'error');
            return;
        }
        _emailTriggering = true;
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
            _emailTriggering = false;
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = origLabel;
            }
        }
    }

    async function toggleEnabled() {
        if (!_emailAccount) return;
        const tgl = document.getElementById('email-enabled-toggle');
        const newVal = !!(tgl && tgl.checked);
        const prev = _emailAccount.enabled;
        try {
            const resp = await fetch('/api/email-ingest/account', {
                method: 'PUT',
                headers: {
                    Authorization: 'Bearer ' + token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email_address: _emailAccount.email_address,
                    imap_host: _emailAccount.imap_host,
                    imap_port: _emailAccount.imap_port,
                    imap_use_ssl: _emailAccount.imap_use_ssl,
                    folder: _emailAccount.folder || 'INBOX',
                    filter_subject: _emailAccount.filter_subject || null,
                    filter_sender: _emailAccount.filter_sender || null,
                    mark_as_read: _emailAccount.mark_as_read !== false,
                    enabled: newVal,
                }),
            });
            const data = await resp.json().catch(() => ({}));
            if (resp.ok && data.ok) {
                _emailAccount = data.account;
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
        if (!_emailLoaded) return;
        render();
        const logsSection = document.getElementById('email-logs-section');
        if (_emailAccount && logsSection && logsSection.open) loadLogs();
    };

    // v95 · 30s 自动刷新日志(用户在邮箱 tab 时才跑)
    let _autoRefreshTimer = null;
    window._startEmailLogAutoRefresh = function () {
        if (_autoRefreshTimer) return;
        _autoRefreshTimer = setInterval(() => {
            if (_emailAccount && _emailLoaded) loadLogs();
        }, 30000);
    };
    window._stopEmailLogAutoRefresh = function () {
        if (_autoRefreshTimer) {
            clearInterval(_autoRefreshTimer);
            _autoRefreshTimer = null;
        }
    };
})();
