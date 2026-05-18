/**
 * static/erp-mrerp-connect.js
 *
 * C-2 + C-3 + C-4 (Zihao 2026-05-18 拍板).
 *
 * Adds MR.ERP / FlowAccount cards into #erp-connect-cards (alongside
 * the existing Xero card IIFE) + the 3-step connect wizard modal +
 * the sidebar push-log scaffold.
 *
 * Self-contained:
 *   - Does NOT touch home.js translations dict. All i18n lives in a
 *     local `T` map below.
 *   - Does NOT modify any existing #endpoint-modal / #btn-add-endpoint
 *     logic (those die in C-6 once the legacy webhook flow is
 *     deprecated).
 *
 * 4-lang i18n: th / en / zh / zh_TW (Zihao swapped ja → zh_TW for the
 * MR.ERP-adjacent surface — see services/erp/mrerp_business_friendly.py
 * docstring). Falls back to en when the active lang has no entry, then
 * to the key itself.
 */
(function () {
    'use strict';

    // ─────────────────────────────────────────────────────────────
    // Local i18n (does NOT touch home.js translations)
    // ─────────────────────────────────────────────────────────────
    const T = {
        // Card labels
        'mrerp-card-name': {
            zh: 'MR.ERP', en: 'MR.ERP', th: 'MR.ERP', zh_TW: 'MR.ERP', ja: 'MR.ERP',
        },
        'flow-card-name': {
            zh: 'FlowAccount', en: 'FlowAccount', th: 'FlowAccount', zh_TW: 'FlowAccount', ja: 'FlowAccount',
        },
        'card-coming-soon': {
            zh: '即将上线', en: 'Coming soon', th: 'เร็วๆ นี้', zh_TW: '即將上線', ja: '近日公開',
        },
        'card-not-configured': {
            zh: '未连接', en: 'Not connected', th: 'ยังไม่เชื่อม', zh_TW: '未連接', ja: '未接続',
        },
        'card-connected': {
            zh: '已连接', en: 'Connected', th: 'เชื่อมแล้ว', zh_TW: '已連接', ja: '接続済み',
        },
        'card-checking': {
            zh: '检查中…', en: 'Checking…', th: 'กำลังตรวจสอบ…', zh_TW: '檢查中…', ja: '確認中…',
        },
        'card-needs-attention': {
            zh: '需关注', en: 'Needs attention', th: 'ต้องตรวจสอบ', zh_TW: '需關注', ja: '要確認',
        },
        'card-btn-connect': {
            zh: '连接', en: 'Connect', th: 'เชื่อมต่อ', zh_TW: '連接', ja: '接続',
        },
        'card-btn-edit': {
            zh: '修改', en: 'Edit', th: 'แก้ไข', zh_TW: '修改', ja: '編集',
        },
        'card-btn-retest': {
            zh: '重新测试', en: 'Re-test', th: 'ทดสอบใหม่', zh_TW: '重新測試', ja: '再テスト',
        },
        'card-stat-last-push': {
            zh: '上次推送', en: 'Last push', th: 'ส่งล่าสุด', zh_TW: '上次推送', ja: '最終送信',
        },
        'card-stat-month-pushed': {
            zh: '本月已推', en: 'This month', th: 'เดือนนี้', zh_TW: '本月已推', ja: '今月',
        },
        'card-stat-month-failed': {
            zh: '失败', en: 'Failures', th: 'ล้มเหลว', zh_TW: '失敗', ja: '失敗',
        },
        'card-stat-mode-auto': {
            zh: '自动推送', en: 'Auto push', th: 'ส่งอัตโนมัติ', zh_TW: '自動推送', ja: '自動送信',
        },
        'card-stat-mode-manual': {
            zh: '手动推送', en: 'Manual push', th: 'ส่งด้วยตนเอง', zh_TW: '手動推送', ja: '手動送信',
        },
        'card-stat-mode-none': {
            zh: '未配置', en: 'Not set', th: 'ยังไม่ตั้งค่า', zh_TW: '未設定', ja: '未設定',
        },
        // Empty state
        'empty-banner-title': {
            zh: '还没有连接任何 ERP · 点上面的卡片开始连接',
            en: 'No ERP connected yet — pick a card above to connect',
            th: 'ยังไม่ได้เชื่อม ERP — เลือกการ์ดด้านบนเพื่อเริ่ม',
            zh_TW: '尚未連接任何 ERP · 點上面的卡片開始連接',
            ja: 'まだ ERP に接続していません · 上のカードから接続を開始',
        },
        'empty-banner-hint': {
            zh: '推送是自动的 · 设置一次,日常使用不再来这页',
            en: "Pushes are automatic — set up once and you won't need to come back",
            th: 'การส่งเป็นอัตโนมัติ — ตั้งครั้งเดียวก็ใช้งานต่อได้เลย',
            zh_TW: '推送是自動的 · 設定一次,日常使用不再來這頁',
            ja: '送信は自動 · 一度設定すれば、戻る必要はありません',
        },
        // Wizard
        'wiz-title-connect': {
            zh: '连接 MR.ERP', en: 'Connect MR.ERP', th: 'เชื่อมต่อ MR.ERP', zh_TW: '連接 MR.ERP', ja: 'MR.ERP に接続',
        },
        'wiz-step-1-h': {
            zh: '这个连接用于哪些客户?',
            en: 'Which Pearnly clients does this connection cover?',
            th: 'การเชื่อมต่อนี้ครอบคลุมลูกค้าใดบ้าง?',
            zh_TW: '此連線適用於哪些客戶?',
            ja: 'この接続はどの取引先をカバーしますか?',
        },
        'wiz-step-1-hint': {
            zh: '这些客户的发票将被推送到 MR.ERP',
            en: 'Invoices for these clients will be pushed to MR.ERP',
            th: 'ใบกำกับของลูกค้าเหล่านี้จะถูกส่งไป MR.ERP',
            zh_TW: '這些客戶的發票將被推送到 MR.ERP',
            ja: 'これらの取引先の請求書を MR.ERP に送信します',
        },
        'wiz-step-1-select-all': {
            zh: '全选', en: 'Select all', th: 'เลือกทั้งหมด', zh_TW: '全選', ja: 'すべて選択',
        },
        'wiz-step-2-h': {
            zh: '填入 MR.ERP 登录信息',
            en: 'Enter your MR.ERP login',
            th: 'กรอกข้อมูลเข้าสู่ระบบ MR.ERP',
            zh_TW: '填入 MR.ERP 登入資訊',
            ja: 'MR.ERP のログイン情報を入力',
        },
        'wiz-username': {
            zh: '用户名', en: 'Username', th: 'ชื่อผู้ใช้', zh_TW: '使用者名稱', ja: 'ユーザー名',
        },
        'wiz-password': {
            zh: '密码', en: 'Password', th: 'รหัสผ่าน', zh_TW: '密碼', ja: 'パスワード',
        },
        'wiz-pwd-hint': {
            zh: '密码会用我们的密钥加密 · 数据库里不存明文',
            en: "Password is encrypted with our key — we never store it in plain text",
            th: 'รหัสผ่านถูกเข้ารหัสด้วยคีย์ของเรา — ไม่เก็บเป็น plain text',
            zh_TW: '密碼會用我們的金鑰加密 · 資料庫不存明文',
            ja: 'パスワードは弊社のキーで暗号化されます · 平文では保存しません',
        },
        'wiz-test-btn': {
            zh: '测试连接', en: 'Test connection', th: 'ทดสอบการเชื่อม', zh_TW: '測試連線', ja: '接続テスト',
        },
        'wiz-test-pending': {
            zh: '尚未测试', en: 'Not tested yet', th: 'ยังไม่ได้ทดสอบ', zh_TW: '尚未測試', ja: '未テスト',
        },
        'wiz-test-running': {
            zh: '正在测试…', en: 'Testing…', th: 'กำลังทดสอบ…', zh_TW: '正在測試…', ja: 'テスト中…',
        },
        'wiz-test-ok': {
            zh: '✓ 已连接 · 看到 {n} 个公司',
            en: '✓ Connected — saw {n} companies',
            th: '✓ เชื่อมแล้ว — พบ {n} บริษัท',
            zh_TW: '✓ 已連接 · 看到 {n} 個公司',
            ja: '✓ 接続済み — {n} 社が見つかりました',
        },
        'wiz-step-3-h': {
            zh: '选公司 + 推送模式',
            en: 'Pick the company and push mode',
            th: 'เลือกบริษัทและโหมดการส่ง',
            zh_TW: '選公司 + 推送模式',
            ja: '会社と送信モードを選択',
        },
        'wiz-company': {
            zh: '公司', en: 'Company', th: 'บริษัท', zh_TW: '公司', ja: '会社',
        },
        'wiz-mode': {
            zh: '推送模式', en: 'Push mode', th: 'โหมดการส่ง', zh_TW: '推送模式', ja: '送信モード',
        },
        'wiz-mode-auto': {
            zh: '识别后自动推送(不需要手动)',
            en: 'Auto-push after OCR (hands-off)',
            th: 'ส่งอัตโนมัติหลัง OCR เสร็จ',
            zh_TW: '辨識後自動推送(不需手動)',
            ja: 'OCR 完了後に自動送信(手動不要)',
        },
        'wiz-mode-manual': {
            zh: '我手动点「推送」才推',
            en: "Only push when I click the 'Push' button",
            th: 'ส่งเมื่อกดปุ่ม "Push" เท่านั้น',
            zh_TW: '我手動點「推送」才推',
            ja: '「送信」ボタンを押したときのみ送信',
        },
        'wiz-seed': {
            zh: '新客户模板(可选)',
            en: 'New customer template (optional)',
            th: 'แม่แบบลูกค้าใหม่ (ทางเลือก)',
            zh_TW: '新客戶範本(可選)',
            ja: '新規顧客テンプレート(任意)',
        },
        'wiz-seed-hint': {
            zh: '自动建新客户时拿这个作模板 · 不选 = 关闭自动建',
            en: "When auto-creating a customer, clone this row's master-data refs. Leave blank to disable auto-create.",
            th: 'ใช้ลูกค้านี้เป็นแม่แบบตอนสร้างอัตโนมัติ · เว้นว่าง = ปิดการสร้างอัตโนมัติ',
            zh_TW: '自動建新客戶時拿這個作範本 · 不選 = 關閉自動建',
            ja: '自動作成時にこの行のマスターデータを継承します · 空欄 = 自動作成を無効化',
        },
        'wiz-seed-empty': {
            zh: '— 不自动建(默认) —',
            en: '— do not auto-create (default) —',
            th: '— ไม่สร้างอัตโนมัติ (ค่าเริ่มต้น) —',
            zh_TW: '— 不自動建立(預設) —',
            ja: '— 自動作成しない(デフォルト) —',
        },
        'btn-cancel': {
            zh: '取消', en: 'Cancel', th: 'ยกเลิก', zh_TW: '取消', ja: 'キャンセル',
        },
        'btn-prev': {
            zh: '← 上一步', en: '← Previous', th: '← ก่อนหน้า', zh_TW: '← 上一步', ja: '← 前へ',
        },
        'btn-next': {
            zh: '下一步 →', en: 'Next →', th: 'ถัดไป →', zh_TW: '下一步 →', ja: '次へ →',
        },
        'btn-finish': {
            zh: '完成 ✓', en: 'Finish ✓', th: 'เสร็จสิ้น ✓', zh_TW: '完成 ✓', ja: '完了 ✓',
        },
    };

    function _activeLang() {
        try {
            if (typeof window.currentLang === 'string' && window.currentLang) return window.currentLang;
            const ls = localStorage.getItem('mrpilot_lang');
            if (ls) return ls;
        } catch (e) {}
        return 'zh';
    }

    function t(key, vars) {
        const lang = _activeLang();
        const entry = T[key] || {};
        let v = entry[lang] || entry.en || entry.zh || key;
        if (vars && typeof v === 'string') {
            Object.keys(vars).forEach(function (k) {
                v = v.replace(new RegExp('\\{' + k + '\\}', 'g'), String(vars[k]));
            });
        }
        return v;
    }

    function _esc(s) {
        return (typeof window.escapeHtml === 'function')
            ? window.escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }

    function _toast(msg, kind) {
        try { if (typeof window.showToast === 'function') window.showToast(msg, kind || 'info'); } catch (e) {}
    }

    function _tk() {
        try { return localStorage.getItem('mrpilot_token') || ''; } catch (e) { return ''; }
    }

    function _authHeaders() {
        const h = { 'Content-Type': 'application/json' };
        const tk = _tk();
        if (tk) h['Authorization'] = 'Bearer ' + tk;
        return h;
    }

    function _fmtRelativeTime(iso) {
        if (!iso) return '—';
        const d = new Date(iso);
        const diffMs = Date.now() - d.getTime();
        if (diffMs < 0) return d.toLocaleString();
        const s = Math.floor(diffMs / 1000);
        if (s < 60) return s + 's';
        if (s < 3600) return Math.floor(s / 60) + 'm';
        if (s < 86400) return Math.floor(s / 3600) + 'h';
        return Math.floor(s / 86400) + 'd';
    }

    // ─────────────────────────────────────────────────────────────
    // Data layer — fetches endpoints + test-connection
    // ─────────────────────────────────────────────────────────────
    async function _loadEndpoints() {
        try {
            const r = await fetch('/api/erp/endpoints', { headers: _authHeaders() });
            if (!r.ok) return [];
            const data = await r.json();
            return Array.isArray(data.items) ? data.items : [];
        } catch (e) { return []; }
    }

    async function _testConnection(endpointId, refresh) {
        try {
            const q = refresh ? '?refresh=1' : '';
            const r = await fetch('/api/erp/endpoints/' + encodeURIComponent(endpointId) + '/test-connection' + q, {
                method: 'POST', headers: _authHeaders(),
            });
            if (!r.ok) return { ok: false, error_code: 'ERR_HTTP_' + r.status };
            return await r.json();
        } catch (e) { return { ok: false, error_code: 'ERR_NETWORK', raw_error: String(e).slice(0, 200) }; }
    }

    // ─────────────────────────────────────────────────────────────
    // Card rendering (C-2)
    // ─────────────────────────────────────────────────────────────
    function _renderCards(host, mrerpEp) {
        // Cards row. Renders MR.ERP card + FlowAccount-soon card.
        // (Xero card is rendered by the existing IIFE upstream of this
        // host; we coexist with it.)
        const cardsHtml = [
            _renderMrerpCard(mrerpEp),
            _renderFlowAccountCard(),
        ].join('');

        let row = host.querySelector('.mrerp-cards-row');
        if (!row) {
            row = document.createElement('div');
            row.className = 'mrerp-cards-row';
            host.appendChild(row);
        }
        row.innerHTML = cardsHtml;

        _bindCardEvents(row, mrerpEp);
    }

    function _renderMrerpCard(ep) {
        const configured = !!ep;
        let pill = '<span class="mrerp-card-pill mrerp-pill-neutral">' + _esc(t('card-not-configured')) + '</span>';
        let pillTitle = '';
        if (configured) {
            pill = '<span class="mrerp-card-pill mrerp-pill-testing" data-mrerp-test-pill="' + _esc(ep.id) + '">' +
                _esc(t('card-checking')) + '</span>';
            pillTitle = t('card-btn-retest');
        }

        // Stats from endpoint or defaults
        const cfg = ep && ep.config ? ep.config : {};
        const lastIso = ep && ep.last_push_at ? ep.last_push_at : null;
        const monthPushed = (ep && typeof ep.month_pushed === 'number') ? ep.month_pushed : (ep ? '—' : '—');
        const monthFailed = (ep && typeof ep.month_failed === 'number') ? ep.month_failed : (ep ? '—' : '—');
        const mode = !ep ? t('card-stat-mode-none')
                         : (ep.auto_push ? t('card-stat-mode-auto') : t('card-stat-mode-manual'));

        const statsHtml = configured ? (
            '<div class="mrerp-card-stats">' +
              '<div class="mrerp-card-stat-row">' +
                '<span class="mrerp-card-stat-label">' + _esc(t('card-stat-last-push')) + '</span>' +
                '<span class="mrerp-card-stat-value">' + _esc(_fmtRelativeTime(lastIso)) + '</span>' +
              '</div>' +
              '<div class="mrerp-card-stat-row">' +
                '<span class="mrerp-card-stat-label">' + _esc(t('card-stat-month-pushed')) + '</span>' +
                '<span class="mrerp-card-stat-value">' + _esc(String(monthPushed)) + '</span>' +
              '</div>' +
              '<div class="mrerp-card-stat-row">' +
                '<span class="mrerp-card-stat-label">' + _esc(t('card-stat-month-failed')) + '</span>' +
                '<span class="mrerp-card-stat-value">' + _esc(String(monthFailed)) + '</span>' +
              '</div>' +
              '<div class="mrerp-card-stat-row">' +
                '<span class="mrerp-card-stat-label">' + _esc(t('wiz-mode')) + '</span>' +
                '<span class="mrerp-card-stat-value">' + _esc(mode) + '</span>' +
              '</div>' +
            '</div>'
        ) : (
            '<div class="mrerp-card-empty">' +
                _esc(t('wiz-step-1-hint')) +
            '</div>'
        );

        const actionsHtml = configured ? (
            '<div class="mrerp-card-actions">' +
              '<button class="btn btn-ghost btn-tiny" type="button" data-mrerp-card-action="edit">' +
                _esc(t('card-btn-edit')) +
              '</button>' +
              '<button class="btn-link" type="button" data-mrerp-card-action="retest" title="' + _esc(pillTitle) + '">' +
                _esc(t('card-btn-retest')) +
              '</button>' +
            '</div>'
        ) : (
            '<div class="mrerp-card-actions">' +
              '<button class="btn btn-primary btn-tiny" type="button" data-mrerp-card-action="connect">' +
                _esc(t('card-btn-connect')) +
              '</button>' +
            '</div>'
        );

        return (
            '<div class="mrerp-card mrerp-card-mrerp" data-mrerp-card="mrerp"' +
                (ep ? ' data-mrerp-endpoint-id="' + _esc(ep.id) + '"' : '') + '>' +
              '<div class="mrerp-card-head">' +
                '<span class="mrerp-card-name">' + _esc(t('mrerp-card-name')) + '</span>' +
                pill +
              '</div>' +
              statsHtml +
              actionsHtml +
            '</div>'
        );
    }

    function _renderFlowAccountCard() {
        return (
            '<div class="mrerp-card is-coming-soon" data-mrerp-card="flowaccount">' +
              '<div class="mrerp-card-head">' +
                '<span class="mrerp-card-name">' + _esc(t('flow-card-name')) + '</span>' +
                '<span class="mrerp-card-pill mrerp-pill-info">' + _esc(t('card-coming-soon')) + '</span>' +
              '</div>' +
              '<div class="mrerp-card-empty">' +
                _esc('Thai-local SaaS · 即将上线') +
              '</div>' +
            '</div>'
        );
    }

    function _bindCardEvents(row, mrerpEp) {
        // Card-level "Connect" / "Edit" → open wizard
        row.querySelectorAll('[data-mrerp-card-action="connect"], [data-mrerp-card-action="edit"]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                window._mrerpOpenWizard(mrerpEp || null);
            });
        });
        // Re-test
        row.querySelectorAll('[data-mrerp-card-action="retest"]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (!mrerpEp) return;
                _refreshCardHealth(mrerpEp.id, true);
            });
        });
    }

    async function _refreshCardHealth(endpointId, force) {
        const pill = document.querySelector('[data-mrerp-test-pill="' + CSS.escape(endpointId) + '"]');
        if (!pill) return;
        pill.className = 'mrerp-card-pill mrerp-pill-testing';
        pill.textContent = t('card-checking');
        pill.setAttribute('data-mrerp-test-pill', endpointId);
        const result = await _testConnection(endpointId, !!force);
        if (result.ok) {
            pill.className = 'mrerp-card-pill mrerp-pill-ok';
            pill.textContent = t('card-connected');
            pill.title = '';
        } else {
            pill.className = 'mrerp-card-pill mrerp-pill-err';
            pill.textContent = t('card-needs-attention');
            const friendly = result.error_friendly || {};
            pill.title = (friendly[_activeLang()] || friendly.en || result.error_code || '').toString();
        }
        pill.setAttribute('data-mrerp-test-pill', endpointId);
    }

    // ─────────────────────────────────────────────────────────────
    // Bootstrap
    // ─────────────────────────────────────────────────────────────
    async function _bootstrap() {
        const host = document.getElementById('erp-connect-cards');
        if (!host) return;
        const endpoints = await _loadEndpoints();
        const mrerpEp = endpoints.find(function (e) {
            return (e.adapter || '').toLowerCase() === 'mrerp';
        }) || null;
        _renderCards(host, mrerpEp);
        if (mrerpEp) {
            // Fire-and-forget initial health check.
            _refreshCardHealth(mrerpEp.id, false);
        }
    }

    // Expose so home.js can re-invoke after page navigation.
    window._mrerpRenderCards = _bootstrap;

    // Public hook for the wizard module (defined further below in
    // the same file — C-3).
    window._mrerpOpenWizard = window._mrerpOpenWizard || function () {
        console.log('[mrerp] wizard not yet attached');
    };

    // ─────────────────────────────────────────────────────────────
    // Auto-bind: render on initial load + whenever the ERP tab
    // becomes visible (subscribed via DOM mutation).
    // ─────────────────────────────────────────────────────────────
    function _scheduleBootstrap() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', _bootstrap, { once: true });
        } else {
            // Already past DOMContentLoaded — defer a tick so
            // home.js's own IIFEs finish first.
            setTimeout(_bootstrap, 0);
        }
    }
    _scheduleBootstrap();

    // Re-bootstrap when the ERP tab is shown (the existing tab
    // switcher just toggles CSS; we listen to the same hash / class
    // mutation home.js uses).
    document.addEventListener('click', function (e) {
        const tabEl = e.target.closest && e.target.closest('[data-auto-panel="erp"], .auto-tab[data-tab="erp"]');
        if (!tabEl) return;
        setTimeout(_bootstrap, 80);
    }, true);

    // Expose i18n / fetch helpers for the wizard module to share.
    window._mrerpConnectShared = { T, t, _esc, _toast, _tk, _authHeaders, _loadEndpoints, _testConnection, _activeLang };
})();
