/* REFACTOR-C1-home-batch9a · 泰国 RD 税务 API 调用 · OCR 抽屉内税号核验/同步
 * 从 home.js verbatim 抽出(0 逻辑改):rdFetch / _rdErrKey / _getFieldValue /
 * _setRdStatus / callRdVerify / callRdSync / openRdSyncModal。
 *
 * 桥接说明:
 * - 对外只 window.callRdVerify / window.callRdSync 挂出 —— home.js 的 drawer-body
 *   事件代理(留 home.js · eval 期绑定)在点击 handler 内裸调它们。
 * - rdFetch / openRdSyncModal / _rdErrKey / _getFieldValue / _setRdStatus 仅本模块内部用。
 * - 全部调用点都在事件 / 异步 handler 内 → 无引导期裸调风险。
 * - 读 token/_results/_drawerIdx(home.js 顶层 · 全局解析)· 调 _showSessionRevokedModal/
 *   updateDrawerEditCount/renderResults(经 window 桥)。_results[_drawerIdx] 仅属性 mutation。
 */
/* global token, _showSessionRevokedModal, escapeHtml, _results, _drawerIdx, updateDrawerEditCount */

// 独立 fetch(不走 apiPost · 避免 403 被误踢)
async function rdFetch(url: string, payload: unknown) {
    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (resp.status === 401) {
            localStorage.removeItem('mrpilot_token');
            const _bd = await resp.json().catch(() => ({}));
            const _dc =
                typeof _bd.detail === 'string' ? _bd.detail : (_bd.detail && _bd.detail.code) || '';
            if (_dc === 'auth.session_revoked') {
                _showSessionRevokedModal();
                return null;
            }
            window.location.href = '/login';
            return null;
        }
        return await resp.json();
    } catch (e) {
        return { ok: false, error: 'network' };
    }
}

function _rdErrKey(code: string) {
    const map = {
        invalid_format: 'rd-err-format',
        not_found: 'rd-err-not-found',
        rd_unreachable: 'rd-err-unreachable',
        parse_error: 'rd-err-unknown',
        network: 'rd-err-unreachable',
    };
    return map[code as keyof typeof map] || 'rd-err-unknown';
}

function _getFieldValue(key: string) {
    const el = document.querySelector(`[data-field="${key}"]`) as HTMLInputElement | null;
    return el ? (el.value || '').trim() : '';
}

function _setRdStatus(side: string, html: string, cls?: string) {
    const el = document.querySelector(`[data-rd-status="${side}"]`);
    if (!el) return;
    el.innerHTML = html;
    el.className = 'rd-status' + (cls ? ' ' + cls : '');
}

async function callRdVerify(side: string) {
    const taxField = side === 'seller' ? 'seller_tax' : 'buyer_tax';
    const taxId = _getFieldValue(taxField);
    _setRdStatus(side, t('rd-verifying'), 'loading');
    const r = await rdFetch('/api/rd/verify', { tax_id: taxId });
    if (!r) return;
    if (!r.ok) {
        _setRdStatus(side, t(_rdErrKey(r.error)), 'error');
        return;
    }
    const valid = r.data && r.data.valid;
    if (valid) {
        _setRdStatus(
            side,
            `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t('rd-status-valid'))}`,
            'valid'
        );
    } else {
        _setRdStatus(side, t('rd-status-invalid'), 'invalid');
    }
}

async function callRdSync(side: string) {
    const taxField = side === 'seller' ? 'seller_tax' : 'buyer_tax';
    const taxId = _getFieldValue(taxField);
    _setRdStatus(side, t('rd-syncing'), 'loading');
    const r = await rdFetch('/api/rd/lookup', { tax_id: taxId, branch: 0 });
    if (!r) return;
    if (!r.ok) {
        _setRdStatus(side, t(_rdErrKey(r.error)), 'error');
        return;
    }
    _setRdStatus(
        side,
        `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t('rd-status-valid'))}`,
        'valid'
    );
    openRdSyncModal(side, r.data);
}

// ============================================================
// RD 同步对比弹窗
// ============================================================
function openRdSyncModal(side: string, official: any) {
    const nameKey = side === 'seller' ? 'seller_name' : 'buyer_name';
    const addrKey = side === 'seller' ? 'seller_addr' : 'buyer_addr';
    const curName = _getFieldValue(nameKey);
    const curAddr = _getFieldValue(addrKey);

    // 对比行:只有「官方有值 且 与当前不同」才纳入对比
    const rows = [];
    if (official.name && official.name !== curName) {
        rows.push({
            field: nameKey,
            label: t('rd-field-name'),
            current: curName,
            official: official.name,
        });
    }
    if (official.address && official.address !== curAddr) {
        rows.push({
            field: addrKey,
            label: t('rd-field-address'),
            current: curAddr,
            official: official.address,
        });
    }
    // branch_label 和 postcode 当作提示信息,不自动覆盖
    const extraInfo = [];
    if (official.branch_label)
        extraInfo.push(
            `<strong>${t('rd-field-branch')}:</strong> ${escapeHtml(official.branch_label)}`
        );
    if (official.post_code)
        extraInfo.push(
            `<strong>${t('rd-field-postcode')}:</strong> ${escapeHtml(official.post_code)}`
        );

    let modal = document.getElementById('rd-sync-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'rd-sync-modal';
        modal.className = 'rd-modal-mask';
        document.body.appendChild(modal);
    }

    if (rows.length === 0) {
        modal.innerHTML = `
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t('rd-modal-title'))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    <div class="rd-modal-no-diff">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12l5 5 9-9"/></svg>
                        ${escapeHtml(t('rd-modal-no-diff'))}
                    </div>
                    ${extraInfo.length ? `<div class="rd-modal-extra">${extraInfo.join(' · ')}</div>` : ''}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-close>${escapeHtml(t('rd-modal-cancel'))}</button>
                </div>
            </div>
        `;
    } else {
        const rowsHtml = rows
            .map(
                (row, _i) => `
            <label class="rd-diff-row">
                <input type="checkbox" data-rd-apply data-field="${row.field}" data-value="${escapeHtml(row.official)}" checked>
                <div class="rd-diff-label">${escapeHtml(row.label)}</div>
                <div class="rd-diff-col rd-diff-current">
                    <div class="rd-diff-col-label">${escapeHtml(t('rd-modal-current'))}</div>
                    <div class="rd-diff-val">${escapeHtml(row.current || '—')}</div>
                </div>
                <div class="rd-diff-arrow">→</div>
                <div class="rd-diff-col rd-diff-official">
                    <div class="rd-diff-col-label">${escapeHtml(t('rd-modal-official'))}</div>
                    <div class="rd-diff-val">${escapeHtml(row.official)}</div>
                </div>
            </label>
        `
            )
            .join('');
        modal.innerHTML = `
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t('rd-modal-title'))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    ${rowsHtml}
                    ${extraInfo.length ? `<div class="rd-modal-extra">${extraInfo.join(' · ')}</div>` : ''}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t('rd-modal-cancel'))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t('rd-modal-apply'))}</button>
                </div>
            </div>
        `;
    }

    modal.classList.add('show');

    const closeModal = () => modal.classList.remove('show');
    modal.querySelector('.rd-modal-close')!.addEventListener('click', closeModal);
    modal
        .querySelectorAll('[data-rd-modal-close]')
        .forEach((b) => b.addEventListener('click', closeModal));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    const applyBtn = modal.querySelector('[data-rd-modal-apply]');
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            const r = _results[_drawerIdx];
            if (!r) {
                closeModal();
                return;
            }
            modal.querySelectorAll('[data-rd-apply]:checked').forEach((cb) => {
                const field = (cb as HTMLElement).dataset.field!;
                const value = (cb as HTMLElement).dataset.value!;
                r.edits[field] = value;
                r.merged_fields[field] = value;
                const input = document.querySelector(
                    `[data-field="${field}"]`
                ) as HTMLInputElement | null;
                if (input) input.value = value;
                const wrap = document.querySelector(`[data-field-wrap="${field}"]`);
                if (wrap) wrap.classList.add('edited');
            });
            updateDrawerEditCount();
            closeModal();
        });
    }
}

// ── window 桥(home.js drawer-body 事件代理点击 handler 裸调)──
window.callRdVerify = callRdVerify;
window.callRdSync = callRdSync;
