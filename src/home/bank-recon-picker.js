// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 M10 · 客户绑定 modal · 从 bank-recon.js 抽出
// verbatim 0 改逻辑。
// ============================================================
/* global token, showConfirm */
import { S } from './bank-recon-store.js';
import { esc } from './bank-recon-helpers.js';
import { refreshSessions } from './bank-recon-sessions.js';

// v118.26.2 · 客户徽章渲染 · 老板可点改 / 员工只读
function _renderClientBadge() {
    const badge = document.getElementById('bank-client-badge');
    if (!badge || !S.currentSession) return;
    const cid = S.currentSession.client_id;
    const dot = document.getElementById('bank-client-badge-dot');
    const name = document.getElementById('bank-client-badge-name');
    const caret = document.getElementById('bank-client-badge-caret');
    // v118.26.2.1 · _userInfo 是文件顶层 let · 不在 window 上 · 直接读
    const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
    const isOwnerLike = !(u && u.role === 'member');

    if (cid != null) {
        const c = (window._clientsCache || []).find((x) => Number(x.id) === Number(cid));
        badge.classList.remove('is-empty');
        if (dot) dot.style.background = (c && c.color) || '#111111';
        if (name) name.textContent = (c && (c.short_name || c.name)) || '#' + cid;
    } else {
        badge.classList.add('is-empty');
        if (dot) dot.style.background = '';
        if (name) name.textContent = t('bank-client-none');
    }

    // 员工只读 · 老板可点
    if (isOwnerLike) {
        badge.classList.remove('is-readonly');
        badge.disabled = false;
        if (caret) caret.style.display = '';
    } else {
        badge.classList.add('is-readonly');
        badge.disabled = true;
        if (caret) caret.style.display = 'none';
    }
    badge.style.display = '';
}

function _openClientPicker() {
    if (!S.currentSession) return;
    const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
    const isOwnerLike = !(u && u.role === 'member');
    if (!isOwnerLike) return; // 员工没权限 · 直接 noop
    S.pickerSelected =
        S.currentSession.client_id != null ? Number(S.currentSession.client_id) : null;
    _renderClientPickerList();
    const m = document.getElementById('bank-client-picker-modal');
    if (m) m.style.display = '';
}

function _closeClientPicker() {
    const m = document.getElementById('bank-client-picker-modal');
    if (m) m.style.display = 'none';
    S.pickerSelected = null;
}

function _renderClientPickerList() {
    const list = document.getElementById('bank-client-picker-list');
    if (!list) return;
    const clients = (window._clientsCache || []).filter(
        (c) => c && (c.is_active === true || c.is_active === undefined)
    );
    const rows = [];
    // 「不绑定」一行
    rows.push(
        '<div class="bank-client-picker-row is-none' +
            (S.pickerSelected == null ? ' is-selected' : '') +
            '" data-cid="">' +
            '<span class="bank-cp-dot"></span>' +
            '<span>' +
            esc(t('bank-client-picker-none')) +
            '</span>' +
            '</div>'
    );
    clients.forEach((c) => {
        const sel = Number(c.id) === Number(S.pickerSelected) ? ' is-selected' : '';
        rows.push(
            '<div class="bank-client-picker-row' +
                sel +
                '" data-cid="' +
                esc(c.id) +
                '">' +
                '<span class="bank-cp-dot" style="background:' +
                esc(c.color || '#111111') +
                '"></span>' +
                '<span>' +
                esc(c.short_name || c.name || '#' + c.id) +
                '</span>' +
                '</div>'
        );
    });
    list.innerHTML = rows.join('');
    list.querySelectorAll('.bank-client-picker-row').forEach((row) => {
        row.addEventListener('click', () => {
            const cid = row.dataset.cid;
            S.pickerSelected = cid ? Number(cid) : null;
            _renderClientPickerList();
        });
    });
}

async function _saveClientPicker() {
    if (!S.currentSession) return;
    try {
        const resp = await fetch(
            '/api/bank-recon/sessions/' + encodeURIComponent(S.currentSession.id) + '/client',
            {
                method: 'PATCH',
                headers: {
                    Authorization: 'Bearer ' + token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ client_id: S.pickerSelected }),
            }
        );
        if (!resp.ok) throw new Error('client:' + resp.status);
        S.currentSession.client_id = S.pickerSelected;
        _renderClientBadge();
        showToast(t('bank-client-changed'), 'success');
        _closeClientPicker();
        // 顺手刷新会话列表(让列表也带新 client_id)
        try {
            await refreshSessions();
        } catch (_) {
            /* silent · 顺手刷新会话列表 */
        }
    } catch (e) {
        console.warn('[bank-recon] save client failed', e);
        showToast(t('bank-client-change-failed'), 'error');
    }
}

export { _renderClientBadge, _openClientPicker, _closeClientPicker, _saveClientPicker };
