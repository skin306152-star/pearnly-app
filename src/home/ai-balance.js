// ============================================================
// REFACTOR-C1 (2026-05-27) · Google AI 余额追踪 ai-balance 从 home.js 抽出为 ES module
//
// 来源:home.js L12155-12337 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global escapeHtml */
// ============================================================
// v108 · Google AI Studio 余额追踪 · 半自动校准
// ============================================================
(function () {
    function authH() {
        return { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
    }
    function fmtMoney(n, d) {
        if (n === null || n === undefined || isNaN(n)) return '—';
        const dec = d === undefined ? 2 : d;
        return Number(n)
            .toFixed(dec)
            .replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    function fmtTime(iso) {
        if (!iso) return '—';
        try {
            const d = new Date(iso);
            const now = new Date();
            const diffMin = Math.floor((now - d) / 60000);
            if (diffMin < 60) return diffMin + ' min ago';
            const diffH = Math.floor(diffMin / 60);
            if (diffH < 24) return diffH + 'h ago';
            const diffD = Math.floor(diffH / 24);
            if (diffD < 7) return diffD + 'd ago';
            return d.toISOString().slice(0, 10);
        } catch (e) {
            return iso.slice(0, 16);
        }
    }

    async function loadBilling() {
        const body = document.getElementById('billing-card-body');
        if (!body) return null;
        body.innerHTML = `<div class="billing-loading">${escapeHtml(t('billing-loading'))}</div>`;
        try {
            const r = await fetch('/api/admin/billing/balance', { headers: authH() });
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const data = await r.json();
            renderBilling(data);
            // 更新 Google 链接
            const linkEls = ['btn-billing-google', 'billing-modal-google-link'];
            for (const id of linkEls) {
                const el = document.getElementById(id);
                if (el)
                    el.href = data.google_billing_url || 'https://aistudio.google.com/app/billing';
            }
            return data;
        } catch (e) {
            console.error('loadBilling fail', e);
            body.innerHTML = `<div class="billing-empty-hint">${escapeHtml(t('billing-msg-fail'))}</div>`;
            return null;
        }
    }

    function renderBilling(d) {
        const body = document.getElementById('billing-card-body');
        if (!body) return;
        if (!d.has_balance) {
            body.innerHTML = `
                <div class="billing-empty-hint">
                    <strong>${escapeHtml(t('billing-empty'))}</strong>
                    ${escapeHtml(t('billing-empty-hint'))}
                </div>`;
            return;
        }
        // 准确度徽章
        let accBadge = '';
        if (d.accuracy_pct !== null && d.accuracy_pct !== undefined) {
            const cls = d.accuracy_pct >= 95 ? 'good' : d.accuracy_pct >= 80 ? 'fair' : 'poor';
            const label =
                d.accuracy_pct >= 95
                    ? t('billing-accuracy-good')
                    : d.accuracy_pct >= 80
                      ? t('billing-accuracy-fair')
                      : t('billing-accuracy-poor');
            accBadge = `<span class="billing-accuracy-badge ${cls}">${escapeHtml(label)} ${d.accuracy_pct}%</span>`;
        }
        const calibration = d.calibration_factor || 1.0;
        body.innerHTML = `
            <div class="billing-stat-block">
                <div class="billing-stat-label">${escapeHtml(t('billing-stat-balance'))}</div>
                <div class="billing-stat-value big">฿ ${fmtMoney(d.current_estimated_balance_thb, 2)}</div>
                <div class="billing-stat-sub">${escapeHtml(t('billing-stat-real'))}: ฿ ${fmtMoney(d.real_balance_thb, 2)} · ${escapeHtml(t('billing-stat-last-updated'))}: ${escapeHtml(fmtTime(d.last_updated_at))}</div>
            </div>
            <div class="billing-stat-block">
                <div class="billing-stat-label">${escapeHtml(t('billing-stat-since-real'))}</div>
                <div class="billing-stat-value">฿ ${fmtMoney(d.estimated_since_last, 4)}</div>
                <div class="billing-stat-sub">${escapeHtml(t('billing-stat-month-used'))}: ฿ ${fmtMoney(d.month_estimated_thb, 2)}</div>
            </div>
            <div class="billing-stat-block">
                <div class="billing-stat-label">${escapeHtml(t('billing-stat-accuracy'))}</div>
                <div class="billing-stat-value">${d.accuracy_pct !== null ? d.accuracy_pct + '%' : '—'}</div>
                <div class="billing-stat-sub">${accBadge}</div>
            </div>
            <div class="billing-stat-block">
                <div class="billing-stat-label">${escapeHtml(t('billing-stat-calibration'))}</div>
                <div class="billing-stat-value">×${calibration.toFixed(3)}</div>
                <div class="billing-stat-sub">${calibration > 1 ? '+' : ''}${((calibration - 1) * 100).toFixed(1)}% adj.</div>
            </div>
        `;
    }

    // 弹窗
    function openBillingModal() {
        document.getElementById('billing-input-balance').value = '';
        document.getElementById('billing-input-notes').value = '';
        const ci = document.getElementById('billing-input-calib');
        if (ci) ci.value = '';
        document.getElementById('billing-modal-mask').style.display = 'flex';
        setTimeout(() => document.getElementById('billing-input-balance').focus(), 50);
    }
    function closeBillingModal() {
        document.getElementById('billing-modal-mask').style.display = 'none';
    }

    async function saveBilling() {
        const balance = parseFloat(document.getElementById('billing-input-balance').value);
        if (isNaN(balance) || balance < 0) {
            showToast(t('billing-msg-balance-required'), 'fail');
            return;
        }
        const notes = document.getElementById('billing-input-notes').value.trim();
        const calibInput = document.getElementById('billing-input-calib');
        const calibRaw = calibInput ? calibInput.value.trim() : '';
        let calibFactor = null;
        if (calibRaw !== '') {
            calibFactor = parseFloat(calibRaw);
            if (isNaN(calibFactor) || calibFactor < 0.5 || calibFactor > 2.0) {
                showToast(t('adm-billing-calib-invalid'), 'fail');
                return;
            }
        }
        try {
            const r = await fetch('/api/admin/billing/balance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authH() },
                body: JSON.stringify({
                    real_balance_thb: balance,
                    notes: notes || null,
                    ...(calibFactor !== null ? { calibration_factor: calibFactor } : {}),
                }),
            });
            if (!r.ok) {
                const err = await r.json().catch(() => ({}));
                throw new Error(err.detail || 'HTTP ' + r.status);
            }
            showToast(t('billing-msg-saved'), 'success');
            closeBillingModal();
            await loadBilling();
        } catch (e) {
            console.error('saveBilling fail', e);
            showToast(t('billing-msg-fail') + ' · ' + (e.message || ''), 'fail');
        }
    }

    // 钩子:成本面板加载时也加载余额
    if (typeof window.loadAdminCostPage === 'function') {
        const _orig = window.loadAdminCostPage;
        window.loadAdminCostPage = function () {
            _orig();
            loadBilling();
        };
    } else {
        // 还没定义 · 等成本面板的 IIFE 定义后再 wrap
        setTimeout(() => {
            if (typeof window.loadAdminCostPage === 'function') {
                const _orig = window.loadAdminCostPage;
                window.loadAdminCostPage = function () {
                    _orig();
                    loadBilling();
                };
            }
        }, 200);
    }

    document.addEventListener('DOMContentLoaded', () => {
        const updBtn = document.getElementById('btn-billing-update');
        if (updBtn) updBtn.addEventListener('click', openBillingModal);

        const closeBtn = document.getElementById('billing-modal-close');
        if (closeBtn) closeBtn.addEventListener('click', closeBillingModal);
        const cancelBtn = document.getElementById('billing-modal-cancel');
        if (cancelBtn) cancelBtn.addEventListener('click', closeBillingModal);
        const saveBtn = document.getElementById('billing-modal-save');
        if (saveBtn) saveBtn.addEventListener('click', saveBilling);
        const mask = document.getElementById('billing-modal-mask');
        if (mask)
            mask.addEventListener('click', (e) => {
                if (e.target === mask) closeBillingModal();
            });

        // 初始 google 链接
        const linkBtn = document.getElementById('btn-billing-google');
        if (linkBtn && !linkBtn.href) linkBtn.href = 'https://aistudio.google.com/app/billing';
        const linkBtn2 = document.getElementById('billing-modal-google-link');
        if (linkBtn2 && !linkBtn2.href) linkBtn2.href = 'https://aistudio.google.com/app/billing';
    });
})();
