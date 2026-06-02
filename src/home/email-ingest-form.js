// ============================================================
// REFACTOR-WB-modularize · 邮箱抓取「绑定 modal + 表单」从 email-ingest.js 拆出
//
// openModal/preset 预设/读表单/连接测试。共享状态经 store 的 S · email-ingest.js ESM import。
// ============================================================
/* global token */
import { S } from './email-ingest-store.js';
// ---------- modal ----------
function openModal(mode) {
    S.modalMode = mode;
    const overlay = document.getElementById('email-modal');
    if (!overlay) return;

    // 填 preset select
    const sel = document.getElementById('email-preset');
    sel.innerHTML = '';
    const presets = S.presets || {};
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

    if (mode === 'edit' && S.account) {
        titleEl.setAttribute('data-i18n', 'email-modal-title-edit');
        titleEl.textContent = t('email-modal-title-edit');
        addrEl.value = S.account.email_address || '';
        pwdEl.value = '';
        pwdEl.setAttribute('data-i18n-placeholder', 'email-field-password-edit-ph');
        pwdEl.placeholder = t('email-field-password-edit-ph');
        hostEl.value = S.account.imap_host || '';
        portEl.value = S.account.imap_port || 993;
        sslEl.checked = S.account.imap_use_ssl !== false;
        folderEl.value = S.account.folder || 'INBOX';
        markEl.checked = S.account.mark_as_read !== false;
        enaEl.checked = S.account.enabled !== false;
        // v95 · 编辑时回填过滤器
        const fSenderEl = document.getElementById('email-filter-sender');
        const fSubjectEl = document.getElementById('email-filter-subject');
        if (fSenderEl) fSenderEl.value = S.account.filter_sender || '';
        if (fSubjectEl) fSubjectEl.value = S.account.filter_subject || '';
        // v0.17.9 · 高亮当前 interval
        setIntervalUI(S.account.interval_min || 15);
        // 尝试按 host 匹配 preset
        sel.value = matchPreset(S.account.imap_host) || 'custom';
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
    const preset = (S.presets || {})[key];
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
    const presets = S.presets || {};
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
    const intervalMin = activeIntervalBtn ? parseInt(activeIntervalBtn.dataset.interval, 10) : 15;
    return {
        email_address: (document.getElementById('email-address').value || '').trim(),
        password: document.getElementById('email-password').value || '',
        imap_host: (document.getElementById('email-imap-host').value || '').trim(),
        imap_port: parseInt(document.getElementById('email-imap-port').value || '993', 10) || 993,
        imap_use_ssl: document.getElementById('email-imap-ssl').checked,
        folder: (document.getElementById('email-folder').value || 'INBOX').trim() || 'INBOX',
        mark_as_read: document.getElementById('email-mark-read').checked,
        enabled: document.getElementById('email-bind-enabled').checked,
        interval_min: [5, 15, 60].includes(intervalMin) ? intervalMin : 15,
        // v95 · 过滤器
        filter_sender: (document.getElementById('email-filter-sender').value || '').trim() || null,
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
        opts.querySelectorAll('.email-interval-btn').forEach((b) => b.classList.remove('active'));
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

export {
    openModal,
    closeModal,
    applyPreset,
    autoDetectPresetByAddress,
    readModalForm,
    showTestResult,
    testFromModal,
};
