// ============================================================
// REFACTOR-C1 (2026-05-27) · 归档命名规则编辑器 archive-settings 从 home.js 抽出为 ES module
//
// 来源:home.js L7970-8470 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* eslint-disable no-useless-assignment -- verbatim home.js · 防御式初始化(let html='' 后被覆盖)· 非 bug · 同 eslint.config 对 static 的判定 */
/* global currentLang, escapeHtml, token, switchSettingsTab, showConfirm */
// ============================================================
// v0.10 · 设置页 tab + 归档命名规则编辑器
// ============================================================
(function () {
    type ArchiveTokenAS = {
        type: string;
        format?: string;
        short?: boolean;
        with_currency?: boolean;
        val?: string;
    };
    let _archiveTemplate: ArchiveTokenAS[] = [];
    let _archiveFolderStrategy = 'by_month_seller';
    let _archiveEditingIdx = -1;
    let _archiveReadOnly = false;

    // 字段元数据(类型 / 图标 / 默认配置)· v0.10 · line SVG
    const ICONS = {
        date: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',
        seller: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',
        category:
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',
        amount: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',
        invoice:
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',
        buyer: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',
        sep: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>',
    };
    const FIELD_META = {
        date: { label: 'field-date', defaultCfg: { format: 'YYYY-MM-DD' } },
        seller: { label: 'field-seller', defaultCfg: { short: true } },
        category: { label: 'field-category', defaultCfg: {} },
        amount: { label: 'field-amount', defaultCfg: { with_currency: true } },
        invoice: { label: 'field-invoice', defaultCfg: {} },
        buyer: { label: 'field-buyer', defaultCfg: {} },
        sep: { label: 'field-sep', defaultCfg: { val: '_' } },
    };

    // 预览用的示例数据(category 按语言切换)· v0.10
    function getSampleCategory() {
        const map = { zh: '运费', en: 'Shipping', th: 'ค่าขนส่ง', ja: '送料' };
        return map[currentLang as keyof typeof map] || 'Shipping';
    }
    function getSampleSellerName() {
        return 'DHL Express (Thailand) Co., Ltd.';
    }
    function getSample() {
        return {
            merged_fields: {
                invoice_date: '2026-04-15',
                seller_name: getSampleSellerName(),
                category: getSampleCategory(),
                total_amount: 1250,
                currency: 'THB',
                invoice_no: 'INV-2026030002',
                buyer_name: 'Mr.ERP Co., Ltd.',
            },
        };
    }

    // ====== v118.10 · 设置页 tab 切换由新版 switchSettingsTab 接管 ======
    // (旧版 window.switchSettingsTab 已删除 · 防覆盖新版)
    // 暴露 load 函数给新 switchSettingsTab 调用
    window.loadArchiveSettings = () => loadArchiveSettings();

    // ====== 加载归档设置 ======
    async function loadArchiveSettings() {
        const canEdit = !!(_userInfo && _userInfo.can_customize_archive);
        _archiveReadOnly = !canEdit;

        // v0.15 · 元素已从 HTML 删除 · 兼容性兜底
        const upgradeBanner = document.getElementById('archive-upgrade-banner');
        if (upgradeBanner) upgradeBanner.style.display = canEdit ? 'none' : '';
        const plusBadge = document.getElementById('archive-plus-badge');
        if (plusBadge) plusBadge.style.display = canEdit ? 'none' : '';

        try {
            const resp = await fetch('/api/archive/settings', {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) throw new Error('load failed');
            const data = await resp.json();
            _archiveTemplate = Array.isArray(data.name_template) ? data.name_template : [];
            _archiveFolderStrategy = data.folder_strategy || 'by_month_seller';
        } catch (e) {
            console.error('load archive settings failed', e);
            showToast(t('archive-load-failed'), 'error');
            return;
        }
        renderArchiveCanvas();
        renderArchivePalette();
        renderArchiveFolderStrategy();
        updateArchivePreview();
    }

    // ====== 规则画布 ======
    function renderArchiveCanvas() {
        const canvas = document.getElementById('archive-rule-canvas');
        if (!canvas) return;
        if (_archiveTemplate.length === 0) {
            canvas.innerHTML = `<div class="archive-empty">${escapeHtml(t('archive-rule-empty'))}</div>`;
            return;
        }
        canvas.innerHTML = _archiveTemplate
            .map((tok, idx) => {
                const meta = FIELD_META[tok.type as keyof typeof FIELD_META] || { label: tok.type };
                const icon = ICONS[tok.type as keyof typeof ICONS] || '';
                const label =
                    tok.type === 'sep'
                        ? `"${escapeHtml(tok.val || '_')}"`
                        : escapeHtml(t(meta.label));
                return `
                <span class="archive-token ${tok.type}"
                      data-token-idx="${idx}"
                      draggable="${_archiveReadOnly ? 'false' : 'true'}">
                    <span class="token-icon">${icon}</span>
                    <span class="token-label">${label}</span>
                </span>
            `;
            })
            .join('');
    }

    // ====== 可添加字段 ======
    function renderArchivePalette() {
        const p = document.getElementById('archive-field-palette');
        if (!p) return;
        const fields = ['date', 'seller', 'category', 'amount', 'invoice', 'buyer', 'sep'];
        p.innerHTML = fields
            .map((type) => {
                const meta = FIELD_META[type as keyof typeof FIELD_META];
                const icon = ICONS[type as keyof typeof ICONS] || '';
                return `
                <button class="archive-palette-btn ${type}" data-add-field="${type}" ${_archiveReadOnly ? 'disabled' : ''}>
                    <span class="token-icon">${icon}</span>
                    <span>${escapeHtml(t(meta.label))}</span>
                </button>
            `;
            })
            .join('');
    }

    // ====== 文件夹策略 radio ======
    function renderArchiveFolderStrategy() {
        document.querySelectorAll('input[name="folder-strategy"]').forEach((r) => {
            (r as HTMLInputElement).checked =
                (r as HTMLInputElement).value === _archiveFolderStrategy;
            (r as HTMLInputElement).disabled = _archiveReadOnly;
        });
    }

    // ====== 实时预览 ======
    async function updateArchivePreview() {
        const out = document.getElementById('archive-preview-name');
        const hint = document.getElementById('archive-preview-hint');
        if (hint) hint.textContent = t('archive-preview-hint', { category: getSampleCategory() });
        if (!out) return;
        if (_archiveTemplate.length === 0) {
            out.textContent = '-';
            return;
        }
        try {
            const resp = await fetch('/api/archive/rename-preview', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    merged_fields: getSample().merged_fields,
                    name_template: _archiveTemplate,
                }),
            });
            const data = await resp.json();
            out.textContent = (data.name || '-') + '.pdf';
        } catch (e) {
            out.textContent = '(' + t('archive-preview-error') + ')';
        }
    }

    // v0.10 · 暴露给全局 applyLang 调用 · v117 · 改成检查 modal 是否打开
    window._rerenderArchiveAll = function () {
        const modal = document.getElementById('archive-rule-modal');
        if (!modal || modal.style.display === 'none') return;
        renderArchiveCanvas();
        renderArchivePalette();
        updateArchivePreview();
    };

    // ====== 拖拽排序 ======
    let _dragFromIdx = -1;
    document.addEventListener('dragstart', (e) => {
        const tok = (e.target as HTMLElement).closest('.archive-token') as HTMLElement | null;
        if (!tok || _archiveReadOnly) return;
        _dragFromIdx = parseInt(tok.dataset.tokenIdx!, 10);
        tok.classList.add('dragging');
        e.dataTransfer!.effectAllowed = 'move';
    });
    document.addEventListener('dragend', (_e) => {
        document
            .querySelectorAll('.archive-token')
            .forEach((t) => t.classList.remove('dragging', 'drop-target'));
        _dragFromIdx = -1;
    });
    document.addEventListener('dragover', (e) => {
        const tok = (e.target as HTMLElement).closest('.archive-token');
        if (tok) {
            e.preventDefault();
            e.dataTransfer!.dropEffect = 'move';
            document
                .querySelectorAll('.archive-token')
                .forEach((t) => t.classList.remove('drop-target'));
            tok.classList.add('drop-target');
        }
    });
    document.addEventListener('drop', (e) => {
        const tok = (e.target as HTMLElement).closest('.archive-token') as HTMLElement | null;
        if (!tok || _dragFromIdx < 0 || _archiveReadOnly) return;
        e.preventDefault();
        const toIdx = parseInt(tok.dataset.tokenIdx!, 10);
        if (toIdx === _dragFromIdx) return;
        const moved = _archiveTemplate.splice(_dragFromIdx, 1)[0];
        _archiveTemplate.splice(toIdx, 0, moved);
        _dragFromIdx = -1;
        renderArchiveCanvas();
        updateArchivePreview();
    });

    // ====== 添加字段 / 点 token 编辑 ======
    document.addEventListener('click', (e) => {
        // v117 · 归档 modal 打开 / 关闭
        // v118.19.1 · 触发源:旧识别中心顶部按钮 #btn-open-archive-rule(已移除 · 兼容)+ 新设置页按钮 #btn-open-archive-rule-from-settings
        if (
            (e.target as HTMLElement).closest('#btn-open-archive-rule') ||
            (e.target as HTMLElement).closest('#btn-open-archive-rule-from-settings')
        ) {
            const modal = document.getElementById('archive-rule-modal');
            if (modal) {
                modal.style.display = '';
                // v118 · 改调 loadArchiveSettings · 包含 fetch + render 全套
                loadArchiveSettings();
            }
            return;
        }
        if (
            (e.target as HTMLElement).closest('#archive-rule-modal-close') ||
            (e.target as HTMLElement).id === 'archive-rule-modal'
        ) {
            const modal = document.getElementById('archive-rule-modal');
            if (modal) modal.style.display = 'none';
            return;
        }

        // v117 · settings 页已经无 sidebar tab · 这段保留为兼容(querySelector 返回 null 时无害)
        const sNav = (e.target as HTMLElement).closest('.settings-nav-item') as HTMLElement | null;
        if (sNav) {
            switchSettingsTab(sNav.dataset.settingsTab);
            return;
        }

        if (_archiveReadOnly) {
            // v0.15 · 只读模式提示(扁平权限下此分支不会触发 · 保留作安全兜底)
            if (
                (e.target as HTMLElement).closest(
                    '.archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset'
                )
            ) {
                showToast(t('feature-contact-us'), 'info');
                return;
            }
        }

        // 添加字段
        const addBtn = (e.target as HTMLElement).closest('[data-add-field]') as HTMLElement | null;
        if (addBtn) {
            const type = addBtn.dataset.addField;
            const meta = FIELD_META[type as keyof typeof FIELD_META];
            const cfg = { type, ...meta.defaultCfg };
            _archiveTemplate.push(cfg as ArchiveTokenAS);
            renderArchiveCanvas();
            updateArchivePreview();
            return;
        }

        // 点 token 编辑
        const tok = (e.target as HTMLElement).closest('.archive-token') as HTMLElement | null;
        if (tok && !_archiveReadOnly) {
            openArchiveTokenModal(parseInt(tok.dataset.tokenIdx!, 10));
            return;
        }

        // 保存 / 重置
        if ((e.target as HTMLElement).closest('#btn-archive-save')) return saveArchiveSettings();
        if ((e.target as HTMLElement).closest('#btn-archive-reset')) return resetArchiveSettings();

        // Token modal
        if (
            (e.target as HTMLElement).closest('#archive-token-close') ||
            (e.target as HTMLElement).id === 'archive-token-modal'
        ) {
            document.getElementById('archive-token-modal')!.style.display = 'none';
        }
        if ((e.target as HTMLElement).closest('#btn-archive-token-ok')) saveArchiveTokenEdit();
        if ((e.target as HTMLElement).closest('#btn-archive-token-delete')) deleteArchiveToken();
    });

    // 文件夹 radio
    document.addEventListener('change', (e) => {
        if ((e.target as HTMLInputElement).name === 'folder-strategy') {
            _archiveFolderStrategy = (e.target as HTMLInputElement).value;
        }
    });

    // ====== Token 编辑对话框 ======
    function openArchiveTokenModal(idx: number) {
        _archiveEditingIdx = idx;
        const tok = _archiveTemplate[idx];
        if (!tok) return;
        const body = document.getElementById('archive-token-body');
        let html = '';
        if (tok.type === 'date') {
            html = `
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t('archive-date-format'))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${tok.format === 'YYYY-MM-DD' ? 'selected' : ''}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${tok.format === 'YYYYMMDD' ? 'selected' : ''}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${tok.format === 'YY.MM' ? 'selected' : ''}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${tok.format === 'YYYY年MM月' ? 'selected' : ''}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`;
        } else if (tok.type === 'seller') {
            html = `
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${tok.short ? 'checked' : ''}> ${escapeHtml(t('archive-seller-short'))}</label>
                    <div class="form-hint">${escapeHtml(t('archive-seller-short-hint'))}</div>
                </div>`;
        } else if (tok.type === 'amount') {
            html = `
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${tok.with_currency ? 'checked' : ''}> ${escapeHtml(t('archive-amount-currency'))}</label>
                    <div class="form-hint">${escapeHtml(t('archive-amount-currency-hint'))}</div>
                </div>`;
        } else if (tok.type === 'sep') {
            html = `
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t('archive-sep-val'))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${tok.val === '_' ? 'active' : ''}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${tok.val === '-' ? 'active' : ''}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${tok.val === ' ' ? 'active' : ''}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t('archive-sep-custom'))}" value="${['_', '-', ' '].includes(tok.val as string) ? '' : escapeHtml(tok.val || '')}">
                    </div>
                </div>`;
        } else {
            html = `<div class="form-hint">${escapeHtml(t('archive-token-no-option'))}</div>`;
        }
        body!.innerHTML = html;
        document.getElementById('archive-token-modal')!.style.display = '';

        // 分隔符 chip 交互
        body!.querySelectorAll('.sep-chip').forEach((chip) => {
            chip.addEventListener('click', () => {
                body!.querySelectorAll('.sep-chip').forEach((c) => c.classList.remove('active'));
                chip.classList.add('active');
                const custom = document.getElementById('token-sep-custom');
                if (custom) (custom as HTMLInputElement).value = '';
            });
        });
    }

    function saveArchiveTokenEdit() {
        const tok = _archiveTemplate[_archiveEditingIdx];
        if (!tok) return;
        if (tok.type === 'date') {
            tok.format = (document.getElementById('token-date-format') as HTMLInputElement).value;
        } else if (tok.type === 'seller') {
            tok.short = (document.getElementById('token-seller-short') as HTMLInputElement).checked;
        } else if (tok.type === 'amount') {
            tok.with_currency = (
                document.getElementById('token-amount-currency') as HTMLInputElement
            ).checked;
        } else if (tok.type === 'sep') {
            const activeChip = document.querySelector(
                '#archive-token-body .sep-chip.active'
            ) as HTMLElement | null;
            const custom = (document.getElementById('token-sep-custom') as HTMLInputElement).value;
            tok.val = custom || (activeChip ? activeChip.dataset.sep : '_');
        }
        document.getElementById('archive-token-modal')!.style.display = 'none';
        renderArchiveCanvas();
        updateArchivePreview();
    }

    function deleteArchiveToken() {
        if (_archiveEditingIdx < 0) return;
        _archiveTemplate.splice(_archiveEditingIdx, 1);
        document.getElementById('archive-token-modal')!.style.display = 'none';
        renderArchiveCanvas();
        updateArchivePreview();
    }

    // ====== 保存 / 重置 ======
    async function saveArchiveSettings() {
        if (_archiveTemplate.length === 0) {
            showToast(t('archive-rule-cannot-empty'), 'error');
            return;
        }
        try {
            const resp = await fetch('/api/archive/settings', {
                method: 'PUT',
                headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name_template: _archiveTemplate,
                    folder_strategy: _archiveFolderStrategy,
                }),
            });
            if (!resp.ok) throw new Error('save failed');
            showToast(t('archive-save-ok'), 'success');
            // v118 · 保存成功后自动关闭 modal(原 tab 模式不需要 · modal 模式必需)
            const modal = document.getElementById('archive-rule-modal');
            if (modal) modal.style.display = 'none';
        } catch (e) {
            showToast(t('archive-save-fail'), 'error');
        }
    }

    async function resetArchiveSettings() {
        const ok = await showConfirm(t('archive-reset-confirm'), { danger: true });
        if (!ok) return;
        // 默认模板 · 和后端 DEFAULT_TEMPLATE 同步
        _archiveTemplate = [
            { type: 'date', format: 'YYYY-MM-DD' },
            { type: 'sep', val: '_' },
            { type: 'seller', short: true },
            { type: 'sep', val: '_' },
            { type: 'category' },
            { type: 'sep', val: '_' },
            { type: 'amount', with_currency: true },
        ];
        _archiveFolderStrategy = 'by_month_seller';
        renderArchiveCanvas();
        renderArchiveFolderStrategy();
        updateArchivePreview();
    }
})();
