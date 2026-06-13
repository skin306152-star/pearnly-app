// ============================================================
// REFACTOR-C1 (2026-05-27) · ERP 统一推送按钮/连接器下拉 unified-push 从 home.js 抽出为 ES module
//
// 来源:home.js L12285-12684 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

/* global escapeHtml, _results, _drawerIdx */
(function () {
    'use strict';

    let _connectors: any[] | null = null;
    let _connectorsLoadAt = 0;
    let _docBound = false;

    function _esc(s: unknown) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function _toast(msg: string, kind?: string) {
        try {
            if (typeof showToast === 'function') showToast(msg, kind || 'info');
        } catch (e) {}
    }
    // P1-7: toast + 可点击链接(showToast 不支持 HTML，用 DOM 手建)
    // @ts-expect-error TS6133 verbatim 占位
    function _toastWithLink(msg: string, href: string, linkText: string) {
        try {
            let wrap = document.getElementById('mp-toast-wrap');
            if (!wrap) {
                wrap = document.createElement('div');
                wrap.id = 'mp-toast-wrap';
                document.body.appendChild(wrap);
            }
            const toast = document.createElement('div');
            toast.className = 'mp-toast success';
            const svg =
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3 3 7-7"/></svg>';
            const span = document.createElement('span');
            span.textContent = msg + ' ';
            const a = document.createElement('a');
            a.href = href;
            a.target = '_blank';
            a.rel = 'noopener';
            a.textContent = linkText;
            a.style.cssText = 'color:inherit;text-decoration:underline;font-weight:600;';
            span.appendChild(a);
            toast.innerHTML = svg;
            toast.appendChild(span);
            wrap.appendChild(toast);
            requestAnimationFrame(() => toast.classList.add('show'));
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => {
                    try {
                        toast.remove();
                    } catch (e2) {}
                }, 300);
            }, 6000);
        } catch (e) {}
    }

    async function _loadConnectors(force?: boolean) {
        const now = Date.now();
        if (!force && _connectors && now - _connectorsLoadAt < 30000) return _connectors;
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return [];
        try {
            const r = await fetch('/api/erp/connectors/status', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) return [];
            const j = await r.json();
            _connectors = (j && j.connectors) || [];
            _connectorsLoadAt = now;
            return _connectors;
        } catch (e) {
            return [];
        }
    }

    function _getDefaultConnectorId() {
        try {
            return localStorage.getItem('pn_push_default_connector') || '';
        } catch (e) {
            return '';
        }
    }
    function _setDefaultConnectorId(id: string) {
        try {
            localStorage.setItem('pn_push_default_connector', id || '');
        } catch (e) {}
    }

    function _resolveDefault(connectors: any[]) {
        if (!connectors || !connectors.length) return null;
        const def = _getDefaultConnectorId();
        if (def) {
            const found = connectors.find((c: any) => c.id === def);
            if (found) return found;
        }
        // 用户没设过 · 优先 endpoints 表里 is_default · 兜底第一个
        const epDef = connectors.find((c: any) => c.is_default);
        if (epDef) return epDef;
        return connectors[0];
    }

    function _isHistoryExceptional(historyObj: any) {
        if (!historyObj) return false;
        const st = String(historyObj.status || '').toLowerCase();
        return st === 'exception' || st === 'exception_pending' || st === 'rejected';
    }

    function _getCurrentHistory() {
        try {
            const arr = typeof _results !== 'undefined' ? _results : [];
            const idx = typeof _drawerIdx !== 'undefined' ? _drawerIdx : -1;
            return arr[idx] || null;
        } catch (e) {
            return null;
        }
    }

    function _connectorIcon(c: any) {
        const tp = c && (c.type || c.id);
        if (tp === 'xero') {
            return '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>';
        }
        if (tp === 'webhook') {
            return '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>';
        }
        // flowaccount / 其他 · 通用 send 图标
        return '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>';
    }

    async function _pushOne(connector: any, historyId: any) {
        if (!connector || !historyId) return false;
        const btn = document.getElementById('btn-push-default') as HTMLButtonElement | null;
        if (btn) {
            btn.disabled = true;
            btn.classList.add('loading');
        }
        const tk = localStorage.getItem('mrpilot_token');
        try {
            let url,
                opts: any = { method: 'POST', headers: { Authorization: 'Bearer ' + tk } };
            if (connector.type === 'xero') {
                url = '/api/erp/xero/push/' + encodeURIComponent(historyId);
            } else {
                // webhook / flowaccount / 其他 · 走老 /api/erp/push 接口
                url = '/api/erp/push';
                opts.headers['Content-Type'] = 'application/json';
                opts.body = JSON.stringify({
                    history_id: historyId,
                    endpoint_id: connector.endpoint_id || undefined,
                });
            }
            const resp = await fetch(url, opts);

            // A2 (Zihao 2026-05-19 拍板) · single source of truth: the
            // server's body.ok flag (mirrors result["success"] from
            // push_to_endpoint · same value the server writes to
            // erp_push_logs.status and ocr_history.last_push_status).
            // Reading only resp.ok lets the toast lie green when the
            // route returns HTTP 200 + {ok:false} for legitimate
            // business failures (e.g. MR.ERP report.php หมายเหตุ
            // rejection · adapter rejected the row). Parse body
            // upfront so both branches can see body.ok and body.error_msg.
            let body: any = {};
            try {
                body = await resp.json();
            } catch (e) {}

            if (!resp.ok) {
                let detail = (body && body.detail) || 'unknown';
                if (typeof detail === 'object') detail = detail.code || JSON.stringify(detail);
                let friendly = String(detail || 'unknown');
                if (connector.type === 'xero') {
                    const k = friendly.replace(/^xero\./, '').toLowerCase();
                    const tr = t('xero-' + k);
                    if (tr && tr !== 'xero-' + k) friendly = tr;
                }
                _toast(
                    t('unified-push-fail')
                        .replace('{name}', connector.name)
                        .replace('{err}', friendly),
                    'error'
                );
                return false;
            }
            if (body && body.ok === false) {
                // HTTP 200 + business failure · route surfaced ok=false
                // and an error_msg. Show the failure toast, NOT success.
                let err = body.error_msg || body.error_code || 'unknown';
                err = String(err).slice(0, 200);
                _toast(
                    t('unified-push-fail').replace('{name}', connector.name).replace('{err}', err),
                    'error'
                );
                return false;
            }
            _toast(t('unified-push-ok').replace('{name}', connector.name), 'success');
            return true;
        } catch (e) {
            _toast(
                t('unified-push-fail')
                    .replace('{name}', connector.name)
                    .replace('{err}', (e as Error).message || 'network'),
                'error'
            );
            return false;
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.classList.remove('loading');
            }
        }
    }

    async function _pushAll(connectors: any[], historyId: any) {
        // 串行 · 失败不阻塞
        for (const c of connectors) {
            await _pushOne(c, historyId);
        }
    }

    function _renderDropdown(connectors: any[], def: any) {
        const dd = document.createElement('div');
        dd.className = 'pn-push-dropdown';
        dd.id = 'pn-push-dropdown';
        const items = (connectors || [])
            .map((c: any) => {
                const isDef = !!(def && c.id === def.id);
                const tag =
                    c.method === 'download'
                        ? t('unified-push-tag-download')
                        : isDef
                          ? t('unified-push-tag-default')
                          : '';
                return (
                    '' +
                    '<div class="pn-pd-item" data-cid="' +
                    _esc(c.id) +
                    '">' +
                    '<span class="pn-pd-icon">' +
                    _connectorIcon(c) +
                    '</span>' +
                    '<span class="pn-pd-name">' +
                    _esc(c.name) +
                    '</span>' +
                    (tag ? '<span class="pn-pd-tag">' + _esc(tag) + '</span>' : '') +
                    (isDef ? '<span class="pn-pd-check">✓</span>' : '') +
                    '</div>'
                );
            })
            .join('');
        const allItem =
            connectors && connectors.length > 1
                ? '<div class="pn-pd-divider"></div>' +
                  '<div class="pn-pd-item pn-pd-all" data-cid="__all__">' +
                  '<span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span>' +
                  '<span class="pn-pd-name">' +
                  _esc(
                      t('unified-push-all').replace('{n}', connectors.length as unknown as string)
                  ) +
                  '</span>' +
                  '</div>'
                : '';
        dd.innerHTML = items + allItem;
        return dd;
    }

    function _closeDropdown() {
        const old = document.getElementById('pn-push-dropdown');
        if (old) old.remove();
    }

    async function _toggleDropdown() {
        if (document.getElementById('pn-push-dropdown')) {
            _closeDropdown();
            return;
        }
        const connectors = (await _loadConnectors(false)) || [];
        const def = _resolveDefault(connectors);
        const dd = _renderDropdown(connectors, def);
        const wrap = document.getElementById('pn-push-wrap');
        if (wrap) wrap.appendChild(dd);
    }

    async function _onDefaultClick() {
        const connectors = (await _loadConnectors(false)) || [];
        const def = _resolveDefault(connectors);
        if (!def) return;
        const r = _getCurrentHistory();
        const hid = r && (r._historyId || r.history_id);
        if (!hid) return;
        if (_isHistoryExceptional(r)) {
            _toast(t('unified-push-disabled-exc'), 'warn');
            return;
        }
        await _pushOne(def, hid);
    }

    async function _onDropdownItemClick(cid: string) {
        _closeDropdown();
        const connectors = (await _loadConnectors(false)) || [];
        const r = _getCurrentHistory();
        const hid = r && (r._historyId || r.history_id);
        if (!hid) return;
        if (_isHistoryExceptional(r)) {
            _toast(t('unified-push-disabled-exc'), 'warn');
            return;
        }
        if (cid === '__all__') {
            await _pushAll(connectors, hid);
            return;
        }
        const c = connectors.find((x: any) => x.id === cid);
        if (!c) return;
        _setDefaultConnectorId(cid); // 用户选了哪个就 sticky 成默认
        await _pushOne(c, hid);
        _refreshButton(); // 重渲按钮文案
    }

    async function _inject() {
        const saveBar = document.getElementById('drawer-history-save');
        if (!saveBar) return;
        if (saveBar.querySelector('#pn-push-wrap')) return; // 已注入

        // v118.27.5.5 · race-safe placeholder-first
        // guard 通过后立刻同步插入占位 wrap(单线程同步操作不会被打断)
        // 第二次 _inject 进入时 guard 立刻看到 wrap · 直接 return · 防重复注入
        const wrap = document.createElement('div');
        wrap.id = 'pn-push-wrap';
        wrap.className = 'pn-push-wrap';
        wrap.dataset.loading = '1';
        saveBar.insertBefore(wrap, saveBar.firstChild);

        // 1. hide 老 3 按钮(向后兼容 · DOM 留着)· querySelectorAll 防 race 残留多个同 ID
        ['btn-push-erp', 'btn-xero-push'].forEach((id) => {
            saveBar.querySelectorAll('#' + id).forEach((old) => {
                (old as HTMLElement).style.display = 'none';
            });
        });

        // 2. 拿连接器(异步)
        const connectors = (await _loadConnectors(false)) || [];
        const def = _resolveDefault(connectors);
        const hasAny = connectors.length > 0;

        // 3. 填充内容到已占位的 wrap(空状态用 disabled 提示)
        if (!hasAny) {
            wrap.innerHTML =
                '' +
                '<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="' +
                _esc(t('unified-push-empty-tip')) +
                '">' +
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg>' +
                '<span style="margin-left:4px;">' +
                _esc(t('unified-push-empty')) +
                '</span>' +
                '</button>';
        } else {
            const showArrow = connectors.length > 1;
            wrap.innerHTML =
                '' +
                '<div class="pn-push-split">' +
                '<button type="button" class="pn-push-main" id="btn-push-default" title="' +
                _esc(t('unified-push-tip')) +
                '">' +
                _connectorIcon(def) +
                '<span>' +
                _esc(t('unified-push-to').replace('{name}', def ? def.name : '')) +
                '</span>' +
                '</button>' +
                (showArrow
                    ? '<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="' +
                      _esc(t('unified-push-other')) +
                      '">' +
                      '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg>' +
                      '</button>'
                    : '') +
                '</div>';
        }
        delete wrap.dataset.loading;
        // wrap 已在 placeholder 阶段 insertBefore · 这里只填内容 · 不重复插入

        // 下载 MR.ERP 表格(路径2)· 有 mrerp 连接器才显示 · 逻辑在 ocr-push(拥有下载功能)
        (window as any).injectMrerpDownloadIntoBar?.(saveBar, connectors, wrap);

        // 4. 绑事件
        const mainBtn = wrap.querySelector('#btn-push-default');
        if (mainBtn && hasAny) mainBtn.addEventListener('click', _onDefaultClick);
        const arrowBtn = wrap.querySelector('#btn-push-arrow');
        if (arrowBtn)
            arrowBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                _toggleDropdown();
            });

        // 文档级 click(关下拉 + 下拉 item 选中)只绑 1 次
        if (!_docBound) {
            _docBound = true;
            document.addEventListener('click', function (e) {
                const item = (e.target as HTMLElement).closest('.pn-pd-item');
                if (item) {
                    const cid = item.getAttribute('data-cid');
                    _onDropdownItemClick(cid as string);
                    return;
                }
                if ((e.target as HTMLElement).closest('#btn-push-arrow')) return;
                _closeDropdown();
            });
            if (typeof window.subscribeI18n === 'function') {
                window.subscribeI18n('unified-push', _refreshButton);
            }
        }
    }

    function _refreshButton() {
        const wrap = document.getElementById('pn-push-wrap');
        if (!wrap) return;
        wrap.remove();
        _connectors = null;
        _connectorsLoadAt = 0;
        _inject();
    }

    // v118.27.5.2 · 持续清理 race 残留:统一按钮存在时 · 任何老按钮出现就 hide
    // v118.27.5.5 · 升级用 querySelectorAll · 处理 race 导致的多个同 ID 残留
    function _purgeStrayLegacyButtons() {
        const saveBar = document.getElementById('drawer-history-save');
        if (!saveBar) return;
        if (!saveBar.querySelector('#pn-push-wrap')) return;
        // 1. hide 所有旧按钮(querySelectorAll · race 导致 DOM 出现多个相同 ID 时全部 hide)
        ['btn-push-erp', 'btn-xero-push'].forEach((id) => {
            saveBar.querySelectorAll('#' + id).forEach((old) => {
                if ((old as HTMLElement).style.display !== 'none') {
                    (old as HTMLElement).style.display = 'none';
                }
            });
        });
        // 2. 清理多余的 pn-push-wrap(只保留第 1 个 · 防 race 导致的双 split)
        const wraps = saveBar.querySelectorAll('#pn-push-wrap');
        if (wraps.length > 1) {
            for (let i = 1; i < wraps.length; i++) {
                wraps[i].remove();
            }
        }
    }

    // 监听抽屉 saveBar 出现 · 自动注入
    function _bindObserver() {
        try {
            const drawerBody = function () {
                return document.getElementById('drawer-body');
            };
            const ob = new MutationObserver(function () {
                if (
                    document.getElementById('drawer-history-save') &&
                    !document.getElementById('pn-push-wrap')
                ) {
                    _inject();
                }
                // race 兜底 · 老按钮被异步插入后立刻 hide
                _purgeStrayLegacyButtons();
            });
            const target = drawerBody();
            if (target) {
                ob.observe(target, { childList: true, subtree: true });
            } else {
                const bodyOb = new MutationObserver(function () {
                    const b = drawerBody();
                    if (b) {
                        ob.observe(b, { childList: true, subtree: true });
                        bodyOb.disconnect();
                    }
                });
                bodyOb.observe(document.body, { childList: true, subtree: true });
            }
            // 已经有 saveBar(切换到历史抽屉之后才打开本 IIFE)兜底
            setTimeout(function () {
                if (
                    document.getElementById('drawer-history-save') &&
                    !document.getElementById('pn-push-wrap')
                ) {
                    _inject();
                }
                _purgeStrayLegacyButtons();
            }, 200);
        } catch (e) {}
    }

    _bindObserver();
})();
