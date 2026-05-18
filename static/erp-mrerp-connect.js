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
        'wiz-seed-loading': {
            zh: '正在拉取客户列表…',
            en: 'Loading customer list…',
            th: 'กำลังโหลดรายชื่อลูกค้า…',
            zh_TW: '正在拉取客戶列表…',
            ja: '顧客リストを読み込み中…',
        },
        'wiz-seed-fallback': {
            zh: '⚠ 无法拉取客户列表 · 请手动输入客户码',
            en: '⚠ Could not fetch the customer list — please type the code manually',
            th: '⚠ ไม่สามารถดึงรายชื่อลูกค้าได้ — กรุณาพิมพ์รหัสด้วยตนเอง',
            zh_TW: '⚠ 無法拉取客戶列表 · 請手動輸入客戶碼',
            ja: '⚠ 顧客リストを取得できません — コードを手動で入力してください',
        },
        'wiz-seed-placeholder': {
            zh: '请选择一个现有客户作模板',
            en: 'Pick an existing customer as the template',
            th: 'เลือกลูกค้าที่มีอยู่เพื่อใช้เป็นแม่แบบ',
            zh_TW: '請選擇一個現有客戶作範本',
            ja: '既存の顧客をテンプレートとして選択',
        },
        'wiz-seed-input-placeholder': {
            zh: '输入客户码(如 0006)',
            en: 'Customer code (e.g. 0006)',
            th: 'รหัสลูกค้า (เช่น 0006)',
            zh_TW: '輸入客戶碼(如 0006)',
            ja: '顧客コード (例: 0006)',
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
        // C-5 · conditional hide of the 字段映射 sub-tab.
        _applyMappingsTabVisibility(endpoints);
    }

    // ─────────────────────────────────────────────────────────────
    // C-5 (Zihao 2026-05-18 拍板) · "字段映射" sub-tab conditional
    // hide. Rule:
    //   • zero endpoints OR ALL endpoints adapter='mrerp' → hide
    //   • any non-mrerp endpoint (xero / webhook / flowaccount /
    //     other) → leave tab + advanced toolbar VISIBLE for the
    //     legacy mapping workflow
    //   • client-mapping sub-tab inside is hidden when MR.ERP-only
    //     (sync preflight covers it)
    // Adapter-aware; safe to run repeatedly.
    // ─────────────────────────────────────────────────────────────
    function _applyMappingsTabVisibility(endpoints) {
        const eps = (endpoints || []).filter(function (e) {
            return e && (e.enabled !== false);
        });
        const adapters = eps.map(function (e) {
            return (e.adapter || '').toLowerCase();
        });
        const hasNonMrerp = adapters.some(function (a) {
            return a && a !== 'mrerp';
        });

        // Tab pill in .erp-subtabs
        const mappingsTabPill = document.querySelector(
            '.erp-subtabs [data-erp-subtab="mappings"]'
        );
        // Sub-panel
        const mappingsPanel = document.querySelector(
            '.erp-subpanel[data-erp-subpanel="mappings"]'
        );
        if (!mappingsTabPill || !mappingsPanel) return;

        const shouldHide = !hasNonMrerp;
        mappingsTabPill.style.display = shouldHide ? 'none' : '';
        mappingsPanel.style.display = shouldHide ? 'none' : '';
        if (shouldHide) {
            // If the mappings tab was active, switch back to connect.
            const connectTab = document.querySelector(
                '.erp-subtabs [data-erp-subtab="connect"]'
            );
            const connectPanel = document.querySelector(
                '.erp-subpanel[data-erp-subpanel="connect"]'
            );
            if (mappingsPanel.classList.contains('active')) {
                if (connectTab) {
                    connectTab.classList.add('active');
                    mappingsTabPill.classList.remove('active');
                }
                if (connectPanel) {
                    connectPanel.classList.add('active');
                    mappingsPanel.classList.remove('active');
                }
            }
        }

        // Inside the mappings tab, hide the "客户映射" sub-tab when
        // mrerp endpoints are present (sync preflight makes it
        // redundant). Other sub-tabs (accounts / taxes / products)
        // are kept because Xero still needs them.
        const clientsSubTab = document.querySelector(
            '.erp-map-subtabs [data-erp-subtab="clients"]'
        );
        if (clientsSubTab) {
            const hideClients = adapters.indexOf('mrerp') >= 0;
            clientsSubTab.style.display = hideClients ? 'none' : '';
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


    // =============================================================
    // C-3 · 3-step connect wizard (Zihao 2026-05-18 拍板)
    //
    // Loaded inline in this same file (not the originally suggested
    // static/erp-connect-wizard.html) so we don't need a separate
    // fetch — the modal DOM is built in-memory and inserted on first
    // open. Keeps the network footprint to 1 CSS + 1 JS.
    //
    // Modal lifecycle:
    //   _mrerpOpenWizard(endpoint | null)
    //     - endpoint=null → new connection (Step 1 blank)
    //     - endpoint=<obj> → edit (preload from endpoint.config)
    //
    // Step 3 includes the new "新客户模板" (seed_customer_code)
    // dropdown that ties Customer auto-create to a known-good seed
    // (e.g. 0006). Empty selection disables auto-create entirely.
    // =============================================================

    let _wizardEl = null;
    let _wizardState = null;

    function _ensureWizardDom() {
        if (_wizardEl) return _wizardEl;
        const wrap = document.createElement('div');
        wrap.className = 'mrerp-wizard-overlay';
        wrap.setAttribute('role', 'dialog');
        wrap.setAttribute('aria-modal', 'true');
        wrap.innerHTML = (
            '<div class="mrerp-wizard">' +
              '<div class="mrerp-wizard-head">' +
                '<div class="mrerp-wizard-title" data-mw-title></div>' +
                '<div class="mrerp-wizard-progress">' +
                  '<span class="mrerp-wizard-step-dot is-active" data-mw-dot="1"></span>' +
                  '<span class="mrerp-wizard-step-sep"></span>' +
                  '<span class="mrerp-wizard-step-dot" data-mw-dot="2"></span>' +
                  '<span class="mrerp-wizard-step-sep"></span>' +
                  '<span class="mrerp-wizard-step-dot" data-mw-dot="3"></span>' +
                '</div>' +
                '<button class="mrerp-wizard-close" data-mw-close type="button" aria-label="close">' +
                  '<svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>' +
                '</button>' +
              '</div>' +
              '<div class="mrerp-wizard-body">' +
                _buildStep1Html() +
                _buildStep2Html() +
                _buildStep3Html() +
              '</div>' +
              '<div class="mrerp-wizard-foot">' +
                '<button class="btn btn-ghost" data-mw-cancel type="button"></button>' +
                '<div class="mrerp-wizard-foot-spacer"></div>' +
                '<button class="btn btn-ghost" data-mw-prev type="button" style="display:none;"></button>' +
                '<button class="btn btn-primary" data-mw-next type="button"></button>' +
              '</div>' +
            '</div>'
        );
        document.body.appendChild(wrap);
        _wizardEl = wrap;
        _bindWizardEvents();
        return wrap;
    }

    function _buildStep1Html() {
        return (
            '<div class="mrerp-wizard-step is-active" data-mw-step="1">' +
              '<h3 class="mrerp-wizard-step-h" data-mw-step1-h></h3>' +
              '<p class="mrerp-wizard-hint" data-mw-step1-hint></p>' +
              '<div class="mrerp-wizard-checkboxes" data-mw-clients>' +
                '<div class="mrerp-card-empty">—</div>' +
              '</div>' +
            '</div>'
        );
    }

    function _buildStep2Html() {
        return (
            '<div class="mrerp-wizard-step" data-mw-step="2">' +
              '<h3 class="mrerp-wizard-step-h" data-mw-step2-h></h3>' +
              '<div class="mrerp-wizard-field">' +
                '<label class="mrerp-wizard-label" data-mw-user-label></label>' +
                '<input type="text" class="mrerp-wizard-input" data-mw-user autocomplete="username">' +
              '</div>' +
              '<div class="mrerp-wizard-field">' +
                '<label class="mrerp-wizard-label" data-mw-pass-label></label>' +
                '<input type="password" class="mrerp-wizard-input" data-mw-pass autocomplete="new-password">' +
                '<div class="mrerp-wizard-hint" data-mw-pwd-hint></div>' +
              '</div>' +
              '<div class="mrerp-wizard-test-row">' +
                '<button class="btn btn-ghost btn-tiny" type="button" data-mw-test></button>' +
                '<span class="mrerp-wizard-test-status" data-mw-test-status></span>' +
              '</div>' +
              '<div class="mrerp-wizard-test-error" data-mw-test-error style="display:none;">' +
                '<div data-mw-test-error-friendly></div>' +
                '<div class="mrerp-wizard-test-error-raw" data-mw-test-error-raw></div>' +
              '</div>' +
            '</div>'
        );
    }

    function _buildStep3Html() {
        // The seed field is dual-rendered: a <select> filled from
        // GET /api/erp/endpoints/:id/customers when editing an
        // existing endpoint (so the user picks from the live list),
        // OR a text input as fallback when creating a new endpoint
        // (no id yet) or when the fetch fails.
        return (
            '<div class="mrerp-wizard-step" data-mw-step="3">' +
              '<h3 class="mrerp-wizard-step-h" data-mw-step3-h></h3>' +
              '<div class="mrerp-wizard-field">' +
                '<label class="mrerp-wizard-label" data-mw-company-label></label>' +
                '<select class="mrerp-wizard-select" data-mw-company></select>' +
              '</div>' +
              '<div class="mrerp-wizard-field">' +
                '<label class="mrerp-wizard-label" data-mw-mode-label></label>' +
                '<div class="mrerp-wizard-radio-group">' +
                  '<label class="mrerp-wizard-radio-row">' +
                    '<input type="radio" name="mrerp-mode" value="auto" checked>' +
                    '<span data-mw-mode-auto></span>' +
                  '</label>' +
                  '<label class="mrerp-wizard-radio-row">' +
                    '<input type="radio" name="mrerp-mode" value="manual">' +
                    '<span data-mw-mode-manual></span>' +
                  '</label>' +
                '</div>' +
              '</div>' +
              '<div class="mrerp-wizard-field">' +
                '<label class="mrerp-wizard-label" data-mw-seed-label></label>' +
                '<select class="mrerp-wizard-select" data-mw-seed style="display:none;">' +
                  '<option value="" data-mw-seed-empty></option>' +
                '</select>' +
                '<input type="text" class="mrerp-wizard-input" data-mw-seed-input style="display:none;" autocomplete="off">' +
                '<div class="mrerp-wizard-hint" data-mw-seed-hint></div>' +
                '<div class="mrerp-wizard-hint" data-mw-seed-fallback-hint style="display:none;color:#8a5a00;"></div>' +
              '</div>' +
            '</div>'
        );
    }

    function _bindWizardEvents() {
        const w = _wizardEl;
        w.querySelector('[data-mw-close]').addEventListener('click', _closeWizard);
        w.querySelector('[data-mw-cancel]').addEventListener('click', _closeWizard);
        w.querySelector('[data-mw-prev]').addEventListener('click', _wizardPrev);
        w.querySelector('[data-mw-next]').addEventListener('click', _wizardNext);
        w.querySelector('[data-mw-test]').addEventListener('click', _wizardRunTest);
        w.addEventListener('click', function (e) {
            // click outside the modal body closes
            if (e.target === w) _closeWizard();
        });
        document.addEventListener('keydown', function (e) {
            if (!_wizardEl || !_wizardEl.classList.contains('is-open')) return;
            if (e.key === 'Escape') _closeWizard();
        });
    }

    function _applyWizardI18n() {
        const w = _wizardEl;
        w.querySelector('[data-mw-title]').textContent = t('wiz-title-connect');
        // Step 1
        w.querySelector('[data-mw-step1-h]').textContent = t('wiz-step-1-h');
        w.querySelector('[data-mw-step1-hint]').textContent = t('wiz-step-1-hint');
        // Step 2
        w.querySelector('[data-mw-step2-h]').textContent = t('wiz-step-2-h');
        w.querySelector('[data-mw-user-label]').textContent = t('wiz-username');
        w.querySelector('[data-mw-pass-label]').textContent = t('wiz-password');
        w.querySelector('[data-mw-pwd-hint]').textContent = t('wiz-pwd-hint');
        w.querySelector('[data-mw-test]').textContent = t('wiz-test-btn');
        w.querySelector('[data-mw-test-status]').textContent = t('wiz-test-pending');
        // Step 3
        w.querySelector('[data-mw-step3-h]').textContent = t('wiz-step-3-h');
        w.querySelector('[data-mw-company-label]').textContent = t('wiz-company');
        w.querySelector('[data-mw-mode-label]').textContent = t('wiz-mode');
        w.querySelector('[data-mw-mode-auto]').textContent = t('wiz-mode-auto');
        w.querySelector('[data-mw-mode-manual]').textContent = t('wiz-mode-manual');
        w.querySelector('[data-mw-seed-label]').textContent = t('wiz-seed');
        w.querySelector('[data-mw-seed-hint]').textContent = t('wiz-seed-hint');
        // Reset the seed select to its initial single-option state so
        // _populateSeedSelector has a consistent starting point. (On
        // subsequent _openWizard calls, the previous run may have
        // populated the select with N customer options + wiped the
        // data-mw-seed-empty option.)
        const seedSelEl = w.querySelector('[data-mw-seed]');
        if (seedSelEl) {
            seedSelEl.innerHTML =
                '<option value="" data-mw-seed-empty>' +
                _esc(t('wiz-seed-empty')) + '</option>';
        }
        const seedInput = w.querySelector('[data-mw-seed-input]');
        if (seedInput) seedInput.placeholder = t('wiz-seed-input-placeholder');
        const fbHint = w.querySelector('[data-mw-seed-fallback-hint]');
        if (fbHint) fbHint.textContent = t('wiz-seed-fallback');
        // Foot
        w.querySelector('[data-mw-cancel]').textContent = t('btn-cancel');
        w.querySelector('[data-mw-prev]').textContent = t('btn-prev');
        w.querySelector('[data-mw-next]').textContent = t('btn-next');
    }

    // Fetch the seed-customer list for the wizard's Step-3 dropdown.
    // Returns null when no endpoint id is available (new wizard) OR
    // when the fetch errors — caller falls back to a text input.
    async function _fetchSeedCustomers(endpointId) {
        if (!endpointId) return null;
        try {
            const r = await fetch(
                '/api/erp/endpoints/' + encodeURIComponent(endpointId)
                + '/customers',
                { headers: _authHeaders() },
            );
            if (!r.ok) return null;
            const data = await r.json();
            if (!data || !data.ok) return null;
            return Array.isArray(data.customers) ? data.customers : [];
        } catch (e) {
            return null;
        }
    }

    async function _populateSeedSelector(currentSeedCode) {
        const w = _wizardEl;
        const selectEl = w.querySelector('[data-mw-seed]');
        const inputEl = w.querySelector('[data-mw-seed-input]');
        const fbHintEl = w.querySelector('[data-mw-seed-fallback-hint]');

        // Default both hidden until we know which one to show.
        selectEl.style.display = 'none';
        inputEl.style.display = 'none';
        fbHintEl.style.display = 'none';

        const endpointId = _wizardState && _wizardState.endpoint
            ? _wizardState.endpoint.id : null;

        // Stage 1: loading
        if (endpointId) {
            selectEl.innerHTML =
                '<option value="">' + _esc(t('wiz-seed-loading')) + '</option>';
            selectEl.style.display = '';
            selectEl.disabled = true;
        } else {
            // No endpoint persisted yet — go straight to text fallback.
            inputEl.style.display = '';
            inputEl.value = currentSeedCode || '';
            return;
        }

        const customers = await _fetchSeedCustomers(endpointId);
        selectEl.disabled = false;

        if (customers === null || customers.length === 0) {
            // Fetch failed (or empty listing) → degrade to text input.
            selectEl.style.display = 'none';
            inputEl.style.display = '';
            inputEl.value = currentSeedCode || '';
            fbHintEl.style.display = '';
            return;
        }

        // Populate the dropdown.
        const opts = ['<option value="">' + _esc(t('wiz-seed-empty')) + '</option>'];
        customers.forEach(function (c) {
            const label = (c.prefix ? c.prefix + ' ' : '')
                + (c.name || '') + ' (' + c.code + ')';
            opts.push(
                '<option value="' + _esc(c.code) + '">' +
                _esc(label) + '</option>'
            );
        });
        selectEl.innerHTML = opts.join('');
        if (currentSeedCode && customers.some(function (c) {
            return c.code === currentSeedCode;
        })) {
            selectEl.value = currentSeedCode;
        }
    }

    function _readSeedValue() {
        const w = _wizardEl;
        const selectEl = w.querySelector('[data-mw-seed]');
        const inputEl = w.querySelector('[data-mw-seed-input]');
        if (selectEl && selectEl.style.display !== 'none') {
            return (selectEl.value || '').trim();
        }
        if (inputEl && inputEl.style.display !== 'none') {
            return (inputEl.value || '').trim();
        }
        return '';
    }

    function _gotoStep(n) {
        _wizardState.step = n;
        const w = _wizardEl;
        w.querySelectorAll('.mrerp-wizard-step').forEach(function (el) {
            el.classList.toggle('is-active', el.getAttribute('data-mw-step') === String(n));
        });
        w.querySelectorAll('[data-mw-dot]').forEach(function (el) {
            const dn = parseInt(el.getAttribute('data-mw-dot'), 10);
            el.classList.remove('is-active', 'is-done');
            if (dn < n) el.classList.add('is-done');
            else if (dn === n) el.classList.add('is-active');
        });
        w.querySelector('[data-mw-prev]').style.display = n > 1 ? '' : 'none';
        w.querySelector('[data-mw-next]').textContent = (n === 3) ? t('btn-finish') : t('btn-next');
    }

    function _closeWizard() {
        if (!_wizardEl) return;
        _wizardEl.classList.remove('is-open');
        _wizardState = null;
    }

    async function _openWizard(endpoint) {
        _ensureWizardDom();
        _applyWizardI18n();
        _wizardState = {
            step: 1,
            endpoint: endpoint || null,
            client_ids: ((endpoint && endpoint.config && endpoint.config.client_ids) || []),
            companies: [],
        };
        // Reset inputs
        const w = _wizardEl;
        w.querySelector('[data-mw-user]').value = '';
        w.querySelector('[data-mw-pass]').value = '';
        w.querySelector('[data-mw-test-status]').textContent = t('wiz-test-pending');
        w.querySelector('[data-mw-test-error]').style.display = 'none';
        const seedSel = w.querySelector('[data-mw-seed]');
        seedSel.innerHTML = '<option value="">' + _esc(t('wiz-seed-empty')) + '</option>';

        // Step 1 — load Pearnly clients
        const clientsBox = w.querySelector('[data-mw-clients]');
        clientsBox.innerHTML = '<div class="mrerp-card-empty">…</div>';
        try {
            const r = await fetch('/api/clients?limit=200', { headers: _authHeaders() });
            if (r.ok) {
                const data = await r.json();
                const items = (data && (data.items || data.clients)) || [];
                const preSelected = new Set((_wizardState.client_ids || []).map(String));
                if (items.length === 0) {
                    clientsBox.innerHTML = '<div class="mrerp-card-empty">—</div>';
                } else {
                    clientsBox.innerHTML = items.map(function (c) {
                        const id = String(c.id || c.client_id || '');
                        const checked = preSelected.has(id) ? ' checked' : '';
                        return (
                            '<label class="mrerp-wizard-checkbox-row">' +
                              '<input type="checkbox" data-mw-client value="' + _esc(id) + '"' + checked + '>' +
                              '<span>' + _esc(c.name || c.client_name || ('#' + id)) + '</span>' +
                            '</label>'
                        );
                    }).join('');
                }
            } else {
                clientsBox.innerHTML = '<div class="mrerp-card-empty">—</div>';
            }
        } catch (e) {
            clientsBox.innerHTML = '<div class="mrerp-card-empty">—</div>';
        }

        _gotoStep(1);
        _wizardEl.classList.add('is-open');
        // Focus the username on Step 2 entry; for now nothing special
        // until user clicks Next.
    }

    function _wizardPrev() {
        if (_wizardState.step > 1) _gotoStep(_wizardState.step - 1);
    }

    async function _wizardNext() {
        if (_wizardState.step === 1) {
            // Collect selected clients
            const ids = [].slice.call(_wizardEl.querySelectorAll('[data-mw-client]:checked'))
                .map(function (cb) { return cb.value; });
            _wizardState.client_ids = ids;
            _gotoStep(2);
            setTimeout(function () { _wizardEl.querySelector('[data-mw-user]').focus(); }, 30);
            return;
        }
        if (_wizardState.step === 2) {
            // Move to step 3; populate company + seed dropdown.
            const companies = _wizardState.companies || [];
            const sel = _wizardEl.querySelector('[data-mw-company]');
            sel.innerHTML = companies.length
                ? companies.map(function (c) {
                    return '<option value="' + _esc(c.comidyear) + ':' + _esc(c.seldb) +
                        '">' + _esc(c.label) + '</option>';
                  }).join('')
                : '<option value="6:1">' + _esc('TEST2019') + '</option>';

            _gotoStep(3);
            // Seed customer dropdown (Task 1) — async populate from
            // /api/erp/endpoints/:id/customers when editing an
            // existing endpoint. Falls back to text input on new
            // wizard or fetch failure.
            const currentSeed = (_wizardState.endpoint
                && _wizardState.endpoint.config
                && _wizardState.endpoint.config.seed_customer_code) || '';
            _populateSeedSelector(currentSeed);
            return;
        }
        // Step 3 → finish
        await _wizardFinish();
    }

    async function _wizardRunTest() {
        const w = _wizardEl;
        const username = w.querySelector('[data-mw-user]').value.trim();
        const password = w.querySelector('[data-mw-pass]').value;
        const statusEl = w.querySelector('[data-mw-test-status]');
        const errBox = w.querySelector('[data-mw-test-error]');
        errBox.style.display = 'none';
        if (!username || !password) {
            statusEl.textContent = t('wiz-test-pending');
            return;
        }
        statusEl.textContent = t('wiz-test-running');

        // Use the legacy /api/erp/test-connection endpoint for the
        // wizard (the per-endpoint route only works for already-
        // persisted endpoints; this one tests config in-memory).
        try {
            const r = await fetch('/api/erp/test-connection', {
                method: 'POST',
                headers: _authHeaders(),
                body: JSON.stringify({
                    adapter: 'mrerp',
                    config: {
                        system_url: 'https://www.mrerp4sme.com',
                        username_enc: username,  // legacy route accepts plain
                        password_enc: password,
                        comidyear: '6', seldb: '1',
                    },
                }),
            });
            const data = r.ok ? await r.json() : { ok: false, error_code: 'ERR_HTTP_' + r.status };
            if (data.ok || data.success) {
                _wizardState.companies = data.companies || [];
                statusEl.textContent = t('wiz-test-ok', { n: (data.companies || []).length || 1 });
            } else {
                const f = data.error_friendly || {};
                statusEl.textContent = '✗';
                errBox.style.display = '';
                w.querySelector('[data-mw-test-error-friendly]').textContent =
                    f[_activeLang()] || f.en || data.raw_error || data.error_code || '';
                w.querySelector('[data-mw-test-error-raw]').textContent = data.raw_error || '';
            }
        } catch (e) {
            statusEl.textContent = '✗';
            errBox.style.display = '';
            w.querySelector('[data-mw-test-error-friendly]').textContent = String(e).slice(0, 200);
            w.querySelector('[data-mw-test-error-raw]').textContent = '';
        }
    }

    async function _wizardFinish() {
        const w = _wizardEl;
        const username = w.querySelector('[data-mw-user]').value.trim();
        const password = w.querySelector('[data-mw-pass]').value;
        const companyChoice = w.querySelector('[data-mw-company]').value || '6:1';
        const [comidyear, seldb] = companyChoice.split(':');
        const mode = w.querySelector('input[name="mrerp-mode"]:checked').value;
        const seed = _readSeedValue();

        if (!username || !password) {
            _toast('请先填入用户名和密码', 'warn');
            _gotoStep(2);
            return;
        }

        const config = {
            system_url: 'https://www.mrerp4sme.com',
            // Server-side encrypts on receive (the route layer accepts
            // plaintext for in-wizard creation; storage layer encrypts
            // before writing to db). NOTE: this contract is enforced
            // by the C-1 backend update — see app.py.
            username_enc: username,
            password_enc: password,
            comidyear: comidyear,
            seldb: seldb,
            client_ids: _wizardState.client_ids || [],
            seed_customer_code: seed || null,
        };
        const body = {
            name: 'MR.ERP',
            adapter: 'mrerp',
            config: config,
            is_default: false,
            auto_push: mode === 'auto',
        };

        try {
            const url = _wizardState.endpoint
                ? '/api/erp/endpoints/' + encodeURIComponent(_wizardState.endpoint.id)
                : '/api/erp/endpoints';
            const method = _wizardState.endpoint ? 'PATCH' : 'POST';
            const r = await fetch(url, {
                method: method,
                headers: _authHeaders(),
                body: JSON.stringify(body),
            });
            if (!r.ok) {
                _toast('保存失败 · 状态 ' + r.status, 'error');
                return;
            }
            _toast('已保存', 'success');
            _closeWizard();
            setTimeout(_bootstrap, 100);
        } catch (e) {
            _toast(String(e).slice(0, 200), 'error');
        }
    }

    // Replace the no-op stub with the real handler.
    window._mrerpOpenWizard = _openWizard;
})();
