/**
 * static/erp-log-enhance.js  · C-4 (Zihao 2026-05-18 拍板)
 *
 * Augments the existing push-log section (#erp-logs-list inside
 * #erp-logs-section) with two additions on top of home.js's renderer:
 *
 *   1. Friendly-message overlay for failure rows.
 *      Watches the log list for new rows; when a row contains raw
 *      Thai/English MR.ERP rejection text, prepends a translated
 *      bubble using the same 4-lang catalog the wizard uses.
 *
 *   2. "查看原文" toggle.
 *      Adds an unobtrusive link under the friendly bubble that
 *      reveals the raw text on click. Single-row state only — no
 *      cross-row persistence needed.
 *
 * Non-goals for C-4:
 *   - Layout-level sidebar promotion (the existing details section
 *     is inside the connect-subpanel; promoting it to a side column
 *     would require home.html DOM surgery which we explicitly defer
 *     until C-6's regression-protected deletion pass).
 *   - Per-card today-stats migration (rendering already covered by
 *     C-2 stats grid; the panel-level #erp-today-stats stays during
 *     transition).
 *
 * Self-contained · no edits to home.js's translations dict.
 */
(function () {
    'use strict';

    function _shared() {
        return window._mrerpConnectShared || null;
    }

    // v118.34.4 · i18n for the strings this file owns. Reuses the
    // shared t() helper from erp-mrerp-connect.js when available, but
    // keeps its own local dict + fallback so this file works
    // standalone even if loading order ever flips.
    const _LOCAL_T = {
        'log-view-raw': {
            zh: '查看原文',
            en: 'View raw',
            th: 'ดูข้อความดิบ',
            zh_TW: '查看原文',
            ja: '原文を表示',
        },
        'log-hide-raw': {
            zh: '隐藏原文',
            en: 'Hide raw',
            th: 'ซ่อนข้อความดิบ',
            zh_TW: '隱藏原文',
            ja: '原文を隠す',
        },
    };
    function _t(key) {
        const sh = _shared();
        const lang = sh && typeof sh._activeLang === 'function' ? sh._activeLang() : 'zh';
        const entry = _LOCAL_T[key] || {};
        return entry[lang] || entry.en || entry.zh || key;
    }

    function _matchRawError(rowEl) {
        // The existing renderer puts the raw response/error somewhere
        // inside the row. We grep visible text for known Thai keywords
        // from mrerp_business_friendly.py.
        const txt = (rowEl.textContent || '').slice(0, 600);
        // Light-touch: only enhance when we see a Thai MR.ERP signature
        // (avoids messing with Xero / webhook rows).
        const hints = [
            'ไม่พบข้อมูลรหัสลูกค้า',
            'ไม่พบข้อมูลรหัสสินค้า',
            'ไม่พบข้อมูลพนักงานขาย',
            'เลขที่ดังกล่าวมีอยู่ในระบบแล้ว',
            'รหัสลูกค้าต้องไม่เกิน',
            'เลขที่ต้องไม่เกิน',
        ];
        for (const h of hints) {
            const i = txt.indexOf(h);
            if (i >= 0) {
                // Extract a useful chunk for friendly translation —
                // up to the next newline or 200 chars.
                let snippet = txt.slice(i);
                const nl = snippet.search(/[\r\n]/);
                if (nl > 0) snippet = snippet.slice(0, nl);
                return snippet.trim().slice(0, 200);
            }
        }
        return null;
    }

    function _friendlyFor(raw) {
        const sh = _shared();
        if (!sh) return null;
        // We don't have a direct JS port of get_friendly; instead, do
        // a tiny substring-match table here mirroring the Python catalog.
        const lang = sh._activeLang();
        const table = [
            {
                match: 'ไม่พบข้อมูลรหัสลูกค้า (บิล)',
                en: 'Customer billing code not found in MR.ERP — create the customer first',
                zh: 'MR.ERP 主数据找不到客户账单码 · 需先创建客户',
                th: 'ไม่พบรหัสลูกค้า (บิล) ในระบบ — สร้างลูกค้าก่อน',
                zh_TW: 'MR.ERP 主資料找不到客戶帳單碼 · 需先建立客戶',
            },
            {
                match: 'ไม่พบข้อมูลรหัสลูกค้า',
                en: 'Customer code not found in MR.ERP — create the customer first',
                zh: 'MR.ERP 主数据找不到客户码 · 需先创建客户',
                th: 'ไม่พบรหัสลูกค้าในระบบ — สร้างลูกค้าก่อน',
                zh_TW: 'MR.ERP 主資料找不到客戶碼 · 需先建立客戶',
            },
            {
                match: 'ไม่พบข้อมูลรหัสสินค้า',
                en: 'Product code not found in MR.ERP — create the product first',
                zh: 'MR.ERP 主数据找不到商品码 · 需先创建商品',
                th: 'ไม่พบรหัสสินค้าในระบบ — สร้างสินค้าก่อน',
                zh_TW: 'MR.ERP 主資料找不到商品碼 · 需先建立商品',
            },
            {
                match: 'ไม่พบข้อมูลพนักงานขาย',
                en: 'Salesman not found in MR.ERP master data',
                zh: 'MR.ERP 主数据找不到销售员',
                th: 'ไม่พบพนักงานขายในระบบ',
                zh_TW: 'MR.ERP 主資料找不到業務員',
            },
            {
                match: 'เลขที่ดังกล่าวมีอยู่ในระบบแล้ว',
                en: 'This invoice number already exists in MR.ERP',
                zh: '该发票号已存在于 MR.ERP',
                th: 'เลขที่ใบกำกับมีอยู่ในระบบแล้ว',
                zh_TW: '該發票號已存在於 MR.ERP',
            },
            {
                match: 'รหัสลูกค้าต้องไม่เกิน 20',
                en: 'Customer code exceeds the 20-character limit',
                zh: '客户码超过 20 字符限制',
                th: 'รหัสลูกค้ายาวเกิน 20 ตัวอักษร',
                zh_TW: '客戶碼超過 20 字元限制',
            },
            {
                match: 'เลขที่ต้องไม่เกิน 18',
                en: 'Invoice number exceeds the 18-character limit',
                zh: '发票号超过 18 字符限制',
                th: 'เลขที่ใบกำกับยาวเกิน 18 ตัวอักษร',
                zh_TW: '發票號超過 18 字元限制',
            },
        ];
        for (const row of table) {
            if (raw.indexOf(row.match) >= 0) {
                return row[lang] || row.en || raw;
            }
        }
        return null;
    }

    function _enhanceRow(rowEl) {
        if (rowEl.dataset.mrerpEnhanced === '1') return;
        const raw = _matchRawError(rowEl);
        if (!raw) return;
        const friendly = _friendlyFor(raw);
        if (!friendly) return;

        const block = document.createElement('div');
        block.className = 'mrerp-logs-row-friendly';
        block.textContent = friendly;

        const toggle = document.createElement('a');
        toggle.className = 'mrerp-logs-row-raw-toggle';
        toggle.href = '#';
        toggle.textContent = _t('log-view-raw');
        const rawBox = document.createElement('div');
        rawBox.className = 'mrerp-logs-row-raw';
        rawBox.style.display = 'none';
        rawBox.textContent = raw;
        toggle.addEventListener('click', function (e) {
            e.preventDefault();
            const hidden = rawBox.style.display === 'none';
            rawBox.style.display = hidden ? '' : 'none';
            toggle.textContent = hidden ? _t('log-hide-raw') : _t('log-view-raw');
        });

        // Append at the end of the row's clickable area; if the row
        // has a body container use that, else just append to the row.
        const target = rowEl.querySelector('.erp-log-row-body, .log-row-body, .row-body') || rowEl;
        target.appendChild(block);
        target.appendChild(toggle);
        target.appendChild(rawBox);
        rowEl.dataset.mrerpEnhanced = '1';
    }

    function _scan() {
        const list = document.getElementById('erp-logs-list');
        if (!list) return;
        list.querySelectorAll('.erp-log-row, .log-row, [data-log-id], [data-erp-log-row]').forEach(
            _enhanceRow
        );
    }

    function _observe() {
        const list = document.getElementById('erp-logs-list');
        if (!list || !window.MutationObserver) return;
        const obs = new MutationObserver(function () {
            // Debounce: schedule a microtask scan.
            queueMicrotask(_scan);
        });
        obs.observe(list, { childList: true, subtree: true });
        _scan();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _observe);
    } else {
        setTimeout(_observe, 500);
    }
})();
