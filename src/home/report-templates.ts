// ============================================================
// REFACTOR-C1 (2026-05-27) · 报表模板/统一导出弹窗 report-templates 从 home.js 抽出为 ES module
//
// 来源:home.js L11655-12065 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* global applyLang, currentLang, I18N, openReportModal, _historySelected */
// ============================================================
// v109.1 · 报表模板系统 · 统一导出弹窗 · 4 处复用
// ============================================================
(function () {
    'use strict';

    // 模板列表缓存(每语言一份)
    const _tplCache = {};

    // 注入弹窗 HTML(只注入一次)
    function ensureModal() {
        if (document.getElementById('report-modal')) return;
        const html = `
        <div class="report-modal-overlay" id="report-modal" style="display:none;">
            <div class="report-modal">
                <div class="report-modal-head">
                    <span class="report-modal-title" data-i18n="report-modal-title">导出报表</span>
                    <button class="report-modal-close-x" id="report-modal-close-x" aria-label="close">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l8 8M14 6l-8 8"/></svg>
                    </button>
                </div>
                <div class="report-modal-body">
                    <div class="report-section">
                        <div class="report-section-title" data-i18n="report-section-template">选择模板</div>
                        <div class="report-tpl-list" id="report-tpl-list">
                            <!-- 动态填充 -->
                        </div>
                    </div>
                    <div class="report-section" id="report-period-section">
                        <div class="report-section-title" data-i18n="report-section-period">时间范围</div>
                        <div class="report-period-list">
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="all" checked>
                                <span data-i18n="report-range-all">全部</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-month">
                                <span data-i18n="report-range-this-month">本月</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="last-month">
                                <span data-i18n="report-range-last-month">上月</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-quarter">
                                <span data-i18n="report-range-this-quarter">本季度</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-year">
                                <span data-i18n="report-range-this-year">今年</span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="report-modal-foot">
                    <button class="btn btn-ghost" id="report-modal-cancel" data-i18n="report-modal-cancel">取消</button>
                    <button class="btn btn-primary" id="report-modal-download">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4M4 15v2h12v-2"/></svg>
                        <span data-i18n="report-modal-download">下载 Excel</span>
                    </button>
                </div>
            </div>
        </div>`;
        const wrap = document.createElement('div');
        wrap.innerHTML = html;
        document.body.appendChild(wrap.firstElementChild as Node);

        // 事件:关闭
        document
            .getElementById('report-modal-close-x')!
            .addEventListener('click', closeReportModal);
        document.getElementById('report-modal-cancel')!.addEventListener('click', closeReportModal);
        document.getElementById('report-modal')!.addEventListener('click', (e) => {
            if ((e.target as HTMLElement).id === 'report-modal') closeReportModal();
        });
    }

    function closeReportModal() {
        const m = document.getElementById('report-modal');
        if (m) m.style.display = 'none';
        // 清理状态
        _modalCtx = null;
    }

    // 模态状态
    let _modalCtx: any = null;

    // 加载模板列表(带缓存)· v118.27.7 · 第 2 个参数 ctxMode 决定是否加 sales_detail_th
    async function fetchTemplates(lang: string, ctxMode?: string) {
        const cacheKey = lang + ':' + (ctxMode || '');
        if ((_tplCache as Record<string, any>)[cacheKey])
            return (_tplCache as Record<string, any>)[cacheKey];
        let result;
        try {
            const tok = localStorage.getItem('mrpilot_token');
            const r = await fetch(`/api/reports/templates?lang=${encodeURIComponent(lang)}`, {
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (!r.ok) throw new Error('templates fetch failed');
            const data = await r.json();
            result = data.templates || [];
        } catch (e) {
            console.error('fetchTemplates fail', e);
            // 兜底:用前端 i18n 拼一份(3 模板 · 已砍 erp)
            result = [
                {
                    code: 'input_vat',
                    name: t('tpl-input-vat'),
                    desc: t('tpl-input-vat-desc'),
                    recommended: true,
                },
                {
                    code: 'standard',
                    name: t('tpl-standard'),
                    desc: t('tpl-standard-desc'),
                    recommended: false,
                },
                {
                    code: 'print',
                    name: t('tpl-print'),
                    desc: t('tpl-print-desc'),
                    recommended: false,
                },
            ];
        }
        // v118.27.6 · 砍 ERP 录入格式(被 ERP 适配器取代 · 向后兼容老服务器仍返回 erp)
        result = result.filter((tpl: any) => tpl.code !== 'erp');
        // v118.27.7 · sales_detail_th 在「单据记录批量」入口也支持(走 /api/ocr/export-by-history-ids)
        // 客户卡片导出暂不支持 · 只在 history-batch 模式加
        if (ctxMode === 'history-batch') {
            // 插在 standard 之后(跟识别中心下拉顺序一致)
            const stdIdx = result.findIndex((x: any) => x.code === 'standard');
            const insertAt = stdIdx >= 0 ? stdIdx + 1 : result.length;
            result.splice(insertAt, 0, {
                code: 'sales_detail_th',
                name: t('export-tpl-sales-detail'),
                desc: t('export-tpl-sales-detail-desc'),
                recommended: false,
                is_new: true,
            });
        }
        (_tplCache as Record<string, any>)[cacheKey] = result;
        return result;
    }

    // 渲染模板列表
    function renderTemplates(templates: any[]) {
        const wrap = document.getElementById('report-tpl-list');
        const itemsHtml = templates
            .map(
                (tpl: any, idx: number) => `
            <label class="report-tpl-item${tpl.recommended ? ' is-recommended' : ''}">
                <input type="radio" name="report-tpl" value="${tpl.code}" ${tpl.recommended ? 'checked' : idx === 0 ? 'checked' : ''}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${escapeHtmlSafe(tpl.name)}
                        ${tpl.recommended ? `<span class="report-tpl-badge">${escapeHtmlSafe(t('report-recommended'))}</span>` : ''}
                    </div>
                    <div class="report-tpl-desc">${escapeHtmlSafe(tpl.desc || '')}</div>
                </div>
            </label>
        `
            )
            .join('');
        // v118.27.6 · 自定义模板入口收列表底部 · disabled · 标"即将上线"
        const customHtml = `
            <label class="report-tpl-item report-tpl-coming" title="${escapeHtmlSafe(t('tpl-custom-coming'))}">
                <input type="radio" name="report-tpl" disabled>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        + ${escapeHtmlSafe(t('tpl-custom-new'))}
                        <span class="report-tpl-badge report-tpl-badge-soon">${escapeHtmlSafe(t('cs-coming-soon'))}</span>
                    </div>
                    <div class="report-tpl-desc">${escapeHtmlSafe(t('tpl-custom-desc'))}</div>
                </div>
            </label>
        `;
        wrap!.innerHTML = itemsHtml + customHtml;
    }

    function escapeHtmlSafe(s: unknown) {
        if (s === null || s === undefined) return '';
        return String(s).replace(
            /[&<>"']/g,
            (ch) =>
                (
                    ({
                        '&': '&amp;',
                        '<': '&lt;',
                        '>': '&gt;',
                        '"': '&quot;',
                        "'": '&#39;',
                    }) as Record<string, string>
                )[ch]
        );
    }

    // 计算时间范围 → YYYY-MM 或 all
    function periodToMonth(period: string) {
        const now = new Date();
        const y = now.getFullYear();
        const m = now.getMonth() + 1;
        if (period === 'all') return 'all';
        if (period === 'this-month') return `${y}-${String(m).padStart(2, '0')}`;
        if (period === 'last-month') {
            const d = new Date(y, m - 2, 1);
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        }
        if (period === 'this-year') return `${y}`; // 后端按前缀匹配 · 暂用 all 兜底
        if (period === 'this-quarter') {
            // 本季度起始月
            // @ts-expect-error TS6133 verbatim 占位
            const qs = Math.floor((m - 1) / 3) * 3 + 1;
            return `${y}-Q${Math.floor((m - 1) / 3) + 1}`; // 后端不支持 · 实际 fallback all
        }
        return 'all';
    }

    // ============================================================
    // 主入口:打开弹窗
    // ============================================================
    // 用法:
    //   openReportModal({
    //     mode: 'client' | 'history-batch',
    //     clientId:   N     (mode=client 时)
    //     historyIds: [...] (mode=history-batch 时)
    //     clientName: 'X'   (可选 · 显示用)
    //     showPeriod: true  (mode=client 时建议 true · 其他 false)
    //   })
    window.openReportModal = async function (opts) {
        opts = opts || {};
        ensureModal();

        // 重新应用 i18n(切语言后再打开也保证更新)
        if (typeof applyLang === 'function') applyLang(currentLang);
        else {
            document.querySelectorAll('#report-modal [data-i18n]').forEach((el) => {
                const k = el.getAttribute('data-i18n');
                if (I18N[currentLang] && I18N[currentLang][k as string])
                    el.textContent = I18N[currentLang][k as string];
            });
        }

        // 时间范围:仅 client mode 显示 · 其他模式藏起
        const periodSection = document.getElementById('report-period-section');
        if (periodSection) periodSection.style.display = opts.mode === 'client' ? '' : 'none';

        // 初始 placeholder
        const listWrap = document.getElementById('report-tpl-list');
        listWrap!.innerHTML = `<div class="report-tpl-loading">${escapeHtmlSafe(t('report-modal-loading'))}</div>`;

        // 显示
        document.getElementById('report-modal')!.style.display = '';

        // 异步拉模板列表 · v118.27.7 · 传 ctx.mode 决定是否加 sales_detail_th(只 history-batch 支持)
        const templates = await fetchTemplates(currentLang, opts && opts.mode);
        renderTemplates(templates);

        _modalCtx = opts;

        // 绑定下载按钮(每次都重新绑 · 因为 ctx 变了)
        const dlBtn = document.getElementById('report-modal-download');
        // 移除旧监听 · 用 cloneNode 替换
        const newBtn = dlBtn!.cloneNode(true);
        dlBtn!.parentNode!.replaceChild(newBtn, dlBtn as Node);
        newBtn.addEventListener('click', () => doDownload(_modalCtx));
    };

    // ============================================================
    // 下载
    // ============================================================
    async function doDownload(ctx: any) {
        if (!ctx) return;
        const tplInput = document.querySelector('input[name="report-tpl"]:checked');
        if (!tplInput) {
            showToast(t('report-toast-no-selection'), 'info');
            return;
        }
        const template = (tplInput as HTMLInputElement).value;
        const periodInput = document.querySelector('input[name="report-period"]:checked');
        const period = periodInput ? (periodInput as HTMLInputElement).value : 'all';
        const month = periodToMonth(period);

        const dlBtn = document.getElementById('report-modal-download') as HTMLButtonElement;
        const origHTML = dlBtn.innerHTML;
        dlBtn.disabled = true;
        dlBtn.innerHTML = `<span>${escapeHtmlSafe(t('report-modal-loading'))}</span>`;

        try {
            const tok = localStorage.getItem('mrpilot_token');
            let resp, defaultName;

            if (ctx.mode === 'client') {
                // 客户导出
                const url = `/api/reports/clients/${ctx.clientId}/export?template=${encodeURIComponent(template)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(month)}`;
                resp = await fetch(url, {
                    headers: { Authorization: 'Bearer ' + tok },
                });
                defaultName = `${(ctx.clientName || 'client').replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g, '_').slice(0, 40)}-${template}.xlsx`;
            } else if (ctx.mode === 'history-batch') {
                // 单据记录批量 · v118.27.7 · sales_detail_th 走新接口(我自己的模板系统)
                if (template === 'sales_detail_th') {
                    resp = await fetch('/api/ocr/export-by-history-ids', {
                        method: 'POST',
                        headers: {
                            Authorization: 'Bearer ' + tok,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            template: 'sales_detail_th',
                            lang: currentLang,
                            history_ids: ctx.historyIds || [],
                            client_id: ctx.clientId || null,
                        }),
                    });
                    defaultName = `Pearnly_SalesDetail_${Date.now()}.xlsx`;
                } else {
                    // input_vat / standard / print → reports_router 老接口
                    resp = await fetch('/api/reports/history/batch_export', {
                        method: 'POST',
                        headers: {
                            Authorization: 'Bearer ' + tok,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            template,
                            lang: currentLang,
                            history_ids: ctx.historyIds || [],
                            client_id: ctx.clientId || null,
                        }),
                    });
                    defaultName = `mrpilot-batch-${template}-${Date.now()}.xlsx`;
                }
            } else {
                throw new Error('unknown mode: ' + ctx.mode);
            }

            if (!resp.ok) {
                let detail = 'HTTP ' + resp.status;
                try {
                    const err = await resp.json();
                    if (err && err.detail) detail = err.detail;
                } catch (e) {
                    console.warn('[batch-export] resp.json err.detail parse failed:', e);
                }
                if (resp.status === 404) {
                    showToast(t('report-toast-empty'), 'info');
                } else {
                    showToast(t('report-toast-fail') + ' · ' + detail, 'error');
                }
                return;
            }

            const blob = await resp.blob();
            // 从响应头读文件名(后端用 RFC 5987)
            let filename = defaultName;
            const cd = resp.headers.get('Content-Disposition') || '';
            const m1 = cd.match(/filename\*=UTF-8''([^;]+)/i);
            if (m1) {
                try {
                    filename = decodeURIComponent(m1[1]);
                } catch (_) {}
            }

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast(t('report-toast-success'), 'success');
            closeReportModal();
        } catch (e) {
            console.error('doDownload fail', e);
            showToast(t('report-toast-fail') + ' · ' + ((e as Error).message || ''), 'error');
        } finally {
            dlBtn.disabled = false;
            dlBtn.innerHTML = origHTML;
        }
    }

    // ============================================================
    // 单据记录批量导出(上传识别页导出按钮已交还 export.ts 的下拉 · 那个带 MR.ERP 模板)
    // ============================================================
    document.addEventListener('DOMContentLoaded', () => {
        const batchExportBtn = document.getElementById('history-batch-export');
        if (batchExportBtn) {
            batchExportBtn.addEventListener('click', () => {
                if (typeof _historySelected === 'undefined' || _historySelected.size === 0) {
                    showToast(t('report-toast-no-selection'), 'info');
                    return;
                }
                openReportModal({
                    mode: 'history-batch',
                    historyIds: Array.from(_historySelected),
                });
            });
        }
    });

    // ============================================================
    // 暴露给客户卡片调用(老 exportClient 保留为 fallback · 新走弹窗)
    // ============================================================
    window.openClientExportModal = function (clientId, clientName) {
        openReportModal({
            mode: 'client',
            clientId: clientId,
            clientName: clientName || '',
        });
    };
})();
