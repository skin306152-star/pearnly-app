// ============================================================
// REFACTOR-C1-home-batch3 (2026-05-31) · 识别页 Excel 导出 从 home.js 抽出为独立 ES module
//
// 来源:home.js verbatim 0 改逻辑 · _EXPORT_TEMPLATES / _getCurrentExportTpl /
//   _setCurrentExportTpl / _runExport / _renderExportDropdown / _closeExportDropdown /
//   _syncExportArrow + btn-export/arrow/document 点击监听 + setInterval。
// 自包含:定义 + 内部 DOM 事件监听全在本 module · 无外部调用方 · 不需要 window 桥。
// 加载顺序:home.js(sync)先暴露公共全局(t/showToast/escapeHtml/apiPost/_results/currentLang)
//   → 本 module(Vite bundle · defer · DOM 就绪)后跑 · 监听绑 #btn-export 等静态元素。
// ============================================================
/* global escapeHtml, apiPost, _results, currentLang */

// ============================================================
// Excel 导出 · v118.27.6 · 4 模板统一(跟单据记录批量导出对齐 · 砍 ERP 录入格式)
// ============================================================
const _EXPORT_TEMPLATES = [
    {
        id: 'input_vat',
        nameKey: 'tpl-input-vat',
        descKey: 'tpl-input-vat-desc',
        badge: 'recommended',
    },
    { id: 'standard', nameKey: 'tpl-standard', descKey: 'tpl-standard-desc' },
    {
        id: 'sales_detail_th',
        nameKey: 'export-tpl-sales-detail',
        descKey: 'export-tpl-sales-detail-desc',
        badge: 'new',
    },
    { id: 'print', nameKey: 'tpl-print', descKey: 'tpl-print-desc' },
];
function _getCurrentExportTpl() {
    try {
        const v = localStorage.getItem('pn_export_tpl') || 'input_vat';
        // 兼容旧值:erp 已砍 · 老用户存了 erp 的回退到 input_vat
        if (v === 'erp') return 'input_vat';
        return v;
    } catch (e) {
        return 'input_vat';
    }
}
function _setCurrentExportTpl(id: any) {
    try {
        localStorage.setItem('pn_export_tpl', id || 'input_vat');
    } catch (e) {}
}

async function _runExport(templateId?: any) {
    if (_results.length === 0) return;
    templateId = templateId || 'input_vat';

    const btn = document.getElementById('btn-export') as HTMLButtonElement | null;
    if (btn) {
        btn.disabled = true;
        btn.classList.add('loading');
    }

    try {
        let resp;
        let defaultName = `pearnly-export-${Date.now()}.xlsx`;

        if (templateId === 'sales_detail_th') {
            // v118.27.6 · 泰国销售明细走 /api/ocr/export(我自己的模板系统)
            // v118.27.5.1 · 多发票拆分修复 · 一个文件含多张发票时 · 拆 N 行 · 不再合并丢字段
            const flatRecords = [];
            for (const r of _results) {
                const invs: any =
                    r.invoices && (r.invoices as any[]).length > 0 ? r.invoices : null;
                if (invs && invs.length > 1) {
                    for (let i = 0; i < invs.length; i++) {
                        const inv = invs[i] || {};
                        flatRecords.push({
                            filename: r.filename + ' #' + (i + 1) + '/' + invs.length,
                            merged_fields: inv.fields || {},
                        });
                    }
                } else {
                    flatRecords.push({
                        filename: r.filename,
                        merged_fields: r.merged_fields,
                    });
                }
            }
            resp = await apiPost('/api/ocr/export', {
                records: flatRecords,
                lang: currentLang,
                template: 'sales_detail_th',
            });
        } else {
            // input_vat / standard / print → /api/reports/history/batch_export(老接口 · reports_router)
            // 用 _results 里的 history_ids(OCR 完已自动入库)
            const historyIds = [];
            for (const r of _results) {
                if (r.history_ids && Array.isArray(r.history_ids)) {
                    historyIds.push(...r.history_ids);
                } else if (r.history_id) {
                    historyIds.push(r.history_id);
                }
            }
            if (historyIds.length === 0) {
                showToast(t('toast-export-error'), 'error');
                return;
            }
            const tok = localStorage.getItem('mrpilot_token');
            resp = await fetch('/api/reports/history/batch_export', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + tok,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    template: templateId,
                    lang: currentLang,
                    history_ids: historyIds,
                    client_id: null,
                }),
            });
            defaultName = `pearnly-${templateId}-${Date.now()}.xlsx`;
        }

        if (!resp) return;
        if (!resp.ok) {
            let detail = 'HTTP ' + resp.status;
            try {
                const err = await resp.json();
                if (err && err.detail)
                    detail =
                        typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
            } catch (e) {
                console.warn('[export] resp.json err.detail parse failed:', e);
            }
            const key =
                typeof detail === 'string' && detail.indexOf('.') > 0 ? 'err.' + detail : null;
            showToast(key ? t(key) : t('toast-export-error') + ' · ' + detail, 'error');
            return;
        }
        const blob = await resp.blob();
        // 优先从 Content-Disposition / X-Filename 读
        let filename = defaultName;
        const xfn = resp.headers.get('X-Filename');
        if (xfn) filename = xfn;
        else {
            const cd = resp.headers.get('Content-Disposition') || '';
            const m1 = cd.match(/filename\*=UTF-8''([^;]+)/i);
            if (m1) {
                try {
                    filename = decodeURIComponent(m1[1]);
                } catch (_) {
                    /* silent · RFC 5987 decode · 用默认 filename */
                }
            }
        }
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(t('toast-export-success'), 'success');
    } catch (e) {
        console.error(e);
        showToast(t('toast-export-error'), 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.classList.remove('loading');
        }
    }
}

document.getElementById('btn-export')!.addEventListener('click', () => {
    _runExport(_getCurrentExportTpl());
});

// ─── 模板下拉 ──────────────────
function _renderExportDropdown() {
    const wrap = document.getElementById('export-split-wrap');
    if (!wrap) return;
    let dd = document.getElementById('export-dropdown');
    if (dd) {
        dd.remove();
        return;
    }
    dd = document.createElement('div');
    dd.id = 'export-dropdown';
    dd.className = 'export-dropdown';
    const cur = _getCurrentExportTpl();
    const items = _EXPORT_TEMPLATES
        .map((tpl) => {
            const badgeHtml =
                tpl.badge === 'recommended'
                    ? `<span class="export-dd-badge badge-rec">${escapeHtml(t('report-recommended'))}</span>`
                    : tpl.badge === 'new'
                      ? `<span class="export-dd-badge badge-new">${escapeHtml(t('tpl-badge-new'))}</span>`
                      : '';
            return `
            <div class="export-dd-item ${tpl.id === cur ? 'active' : ''}" data-tpl="${tpl.id}">
                <div class="export-dd-row">
                    <span class="export-dd-name">${escapeHtml(t(tpl.nameKey))}</span>
                    ${badgeHtml}
                    ${tpl.id === cur ? '<span class="export-dd-check">✓</span>' : ''}
                </div>
                <div class="export-dd-desc">${escapeHtml(t(tpl.descKey))}</div>
            </div>
        `;
        })
        .join('');
    // v118.27.6 · 自定义模板入口收下拉底部 · disabled 标"即将"
    const customRow = `
        <div class="export-dd-divider"></div>
        <div class="export-dd-item export-dd-custom" data-tpl="__custom" title="${escapeHtml(t('tpl-custom-coming'))}">
            <div class="export-dd-row">
                <span class="export-dd-name">+ ${escapeHtml(t('tpl-custom-new'))}</span>
                <span class="export-dd-badge badge-soon">${escapeHtml(t('cs-coming-soon'))}</span>
            </div>
        </div>
    `;
    dd.innerHTML = items + customRow;
    wrap.appendChild(dd);
}
function _closeExportDropdown() {
    const dd = document.getElementById('export-dropdown');
    if (dd) dd.remove();
}
const _btnExpArrow = document.getElementById('btn-export-arrow') as HTMLButtonElement | null;
if (_btnExpArrow) {
    _btnExpArrow.addEventListener('click', (e) => {
        e.stopPropagation();
        if (_btnExpArrow.disabled) return;
        _renderExportDropdown();
    });
}
document.addEventListener('click', (e) => {
    const item = (e.target as HTMLElement).closest('.export-dd-item');
    if (item) {
        const tplId = item.getAttribute('data-tpl');
        // v118.27.6 · 自定义模板入口 · 暂未开放 · toast 「即将上线」 · 不切模板不导出
        if (tplId === '__custom') {
            _closeExportDropdown();
            showToast(t('cs-coming-soon'), 'info');
            return;
        }
        _setCurrentExportTpl(tplId);
        _closeExportDropdown();
        _runExport(tplId);
        return;
    }
    if ((e.target as HTMLElement).closest('#btn-export-arrow')) return;
    _closeExportDropdown();
});

// 当 _results 变化时(开始识别 / 清空)同步 disable arrow
function _syncExportArrow() {
    const arrow = document.getElementById('btn-export-arrow') as HTMLButtonElement | null;
    const main = document.getElementById('btn-export') as HTMLButtonElement | null;
    if (arrow && main) arrow.disabled = main.disabled;
}
// 监听 export 主按钮的 disabled 变化(简单 polling · 兼容老逻辑)
setInterval(_syncExportArrow, 300);
