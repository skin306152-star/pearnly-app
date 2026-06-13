// ============================================================
// REFACTOR-C1-home-batch2 (2026-05-31) · OCR 抽屉「推 ERP」按钮三件套 从 home.js 抽出为独立 ES module
//
// 来源:home.js verbatim 0 改逻辑 · injectOcrPushButton / openOcrPushPicker / pushOcrToErp。
// 加载顺序:home.js(sync)先暴露公共全局(t/escapeHtml/showToast/_results/_drawerIdx/
//   _userInfo/_erpEndpoints/token/window._refreshErpEndpointsCache)→ 本 module(Vite bundle
//   · defer)后跑 · bare 调全局不 import。
// 桥回:window.injectOcrPushButton(ocr-results.js 的 openDrawer 调它)。
// _erpEndpoints 缓存仍在 home.js(每次 loadErpEndpoints 重写 · 经 window._erpEndpoints 读)。
// ============================================================
/* global escapeHtml, _results, _drawerIdx, _erpEndpoints, token */

// 识别页抽屉打开时也注入「推 ERP」按钮 · v105.2 · 改放抽屉头部 · 不再遮内容明细
//
// v118.34.34 (Zihao 2026-05-19 拍板 · 批 2 改动 4) · 推送按钮动态显示:
//   0 个启用 endpoint → 按钮整个不渲染(没必要 tease 用户)
//   1 个启用 endpoint → 按钮 label = "推送到 {name}" · 单击直推
//   ≥2 个启用 endpoint → 按钮 label = "推送到 ERP ▾" · 单击展开 endpoint 选择 popover
//
// 注意:_erpEndpoints 不包含 Xero · Xero 有独立按钮 (btn-xero-push)
// 由 erp-xero IIFE 单独注入 · 我们这里只管 webhook / mrerp / flowaccount 系列.
function injectOcrPushButton() {
    const r = _results[_drawerIdx];
    if (!r || r._historyMode) return;
    if (!_userInfo || !_userInfo.can_push_erp) return;
    if (!r._historyId && !r.history_id) return;
    const historyId = r._historyId || r.history_id;

    const header = document.querySelector('.drawer-header');
    if (!header || document.getElementById('drawer-ocr-push-btn')) return;

    // v118.34.34 · 只展示 enabled 的 endpoint · _erpEndpoints 是全局缓存.
    // DMS(2026-05-31):mrerp_dms 是身份证→订车单适配器 · 绝不出现在发票抽屉的
    // 「推送到 ERP」列表里(发票推 DMS = 数据错投)· 过滤掉。
    const enabledEps = (window._erpEndpoints || _erpEndpoints || []).filter(function (ep: any) {
        return ep && ep.enabled !== false && (ep.adapter || '').toLowerCase() !== 'mrerp_dms';
    });

    // 0 enabled → 不渲染按钮. 用户去 ERP 对接 tab 先连一个再说.
    if (enabledEps.length === 0) return;

    // 创建按钮 · 插在诊断按钮之前(诊断 / 关闭按钮已在 header 末尾)
    const btn = document.createElement('button');
    btn.id = 'drawer-ocr-push-btn';
    btn.className = 'drawer-push-btn';

    // Button label / behavior depends on enabled-endpoint count.
    let label;
    if (enabledEps.length === 1) {
        // Single endpoint · 直接显示推到那个 endpoint 的 name.
        const epName = enabledEps[0].name || enabledEps[0].adapter || 'ERP';
        label = t('btn-push-to-name', { name: epName });
        btn.title = label;
    } else {
        // ≥2 endpoints · 通用 label + 下拉箭头.
        label = t('btn-push-erp') + ' ▾';
        btn.title = t('btn-push-erp-pick-tip');
    }
    btn.innerHTML = `
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(label)}</span>
    `;

    btn.addEventListener('click', function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        if (enabledEps.length === 1) {
            // 单 endpoint · 直推 · 后端按 default 选(只有 1 个 enabled 就是它).
            pushOcrToErp(historyId, enabledEps[0].id);
        } else {
            // 多 endpoint · 打开 picker popover.
            openOcrPushPicker(btn, historyId, enabledEps);
        }
    });

    // 插在第一个 drawer-diagnose 之前
    const diagnose = header.querySelector('.drawer-diagnose');
    if (diagnose) {
        header.insertBefore(btn, diagnose);
    } else {
        header.appendChild(btn);
    }

    // 下载 MR.ERP 表格按钮(路径2 人工导入用)· 仅当有 mrerp 端点时显示
    // (文件是 MR.ERP 专有格式 · 让不想存 MR.ERP 密码的用户自己下载后导入)。
    const hasMrerp = enabledEps.some(function (ep: any) {
        return (ep.adapter || '').toLowerCase() === 'mrerp';
    });
    if (hasMrerp) injectMrerpDownloadButton(header, historyId);
}

function injectMrerpDownloadButton(header: Element, historyId: any) {
    if (document.getElementById('drawer-mrerp-xlsx-btn')) return;
    const dl = document.createElement('button');
    dl.id = 'drawer-mrerp-xlsx-btn';
    dl.className = 'drawer-push-btn';
    dl.title = t('btn-mrerp-xlsx');
    dl.innerHTML = `
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 2v8M5 7l3 3 3-3M3 13h10"/>
        </svg>
        <span>${escapeHtml(t('btn-mrerp-xlsx'))}</span>
    `;
    dl.addEventListener('click', function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        downloadMrerpXlsx(historyId);
    });
    const pushBtn = document.getElementById('drawer-ocr-push-btn');
    if (pushBtn && pushBtn.parentNode) {
        pushBtn.parentNode.insertBefore(dl, pushBtn.nextSibling);
    } else {
        header.appendChild(dl);
    }
}

// v118.34.34 · 多 endpoint picker · 简单 popover · 复用 history-popover CSS.
function openOcrPushPicker(anchor: HTMLElement, historyId: any, enabledEps: any[]) {
    // 先关掉已有 popover
    document.querySelectorAll('.drawer-push-picker').forEach((n) => n.remove());

    const rect = anchor.getBoundingClientRect();
    const pop = document.createElement('div');
    pop.className = 'drawer-push-picker history-popover';
    pop.style.position = 'fixed';
    pop.style.top = rect.bottom + 6 + 'px';
    pop.style.left = Math.max(8, rect.right - 240) + 'px';
    pop.style.minWidth = '220px';
    pop.style.zIndex = '12000';

    const rows = enabledEps
        .map(function (ep: any) {
            const name = escapeHtml(ep.name || ep.adapter || 'ERP');
            const adapter = escapeHtml((ep.adapter || '').toLowerCase());
            const isDef = ep.is_default;
            const defBadge = isDef
                ? '<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">' +
                  escapeHtml(t('ep-default')) +
                  '</span>'
                : '';
            return (
                '<button type="button" data-ep-id="' +
                escapeHtml(ep.id) +
                '" ' +
                'style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;">' +
                '<span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">' +
                adapter +
                '</span>' +
                name +
                defBadge +
                '</span>' +
                '</button>'
            );
        })
        .join('');
    pop.innerHTML = rows;
    document.body.appendChild(pop);

    const closePop = () => {
        pop.remove();
        document.removeEventListener('click', onDoc, true);
    };
    const onDoc = (e: Event) => {
        if (
            !pop.contains(e.target as Node) &&
            e.target !== anchor &&
            !anchor.contains(e.target as Node)
        )
            closePop();
    };
    setTimeout(() => document.addEventListener('click', onDoc, true), 0);

    pop.addEventListener('click', (e) => {
        const b = (e.target as HTMLElement).closest('[data-ep-id]');
        if (!b) return;
        const epId = b.getAttribute('data-ep-id');
        closePop();
        pushOcrToErp(historyId, epId);
    });
}

async function pushOcrToErp(historyId: any, endpointId: any) {
    const btn = document.getElementById('drawer-ocr-push-btn') as HTMLButtonElement;
    if (btn) btn.disabled = true;
    try {
        const body: { history_id: any; endpoint_id?: any } = { history_id: historyId };
        if (endpointId) body.endpoint_id = endpointId;
        const resp = await fetch('/api/erp/push', {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (!resp.ok) {
            const code = data && data.detail ? data.detail : 'err.unknown';
            if (code === 'erp.no_default_endpoint') {
                showToast(t('erp-push-no-endpoint'), 'warn');
            } else if (code === 'erp.endpoint_disabled') {
                // v118.34.34 · endpoint 在 click 和 push 之间被另一个 tab 停用了 ·
                // 提示用户去 ERP 对接 tab 启用 + 刷新 endpoints 缓存.
                showToast(
                    t('erp-push-disabled-tip') || t('card-disabled-tip') || 'Endpoint disabled',
                    'warn'
                );
                if (typeof window._refreshErpEndpointsCache === 'function') {
                    window._refreshErpEndpointsCache();
                }
            } else {
                showToast(t('erp-push-fail', { err: code }), 'fail');
            }
            return;
        }
        if (data.ok) {
            showToast(t('erp-push-ok', { name: data.endpoint_name || '' }));
        } else {
            showToast(t('erp-push-fail', { err: data.error_msg || 'unknown' }), 'fail');
        }
    } catch (e) {
        showToast(t('erp-push-fail', { err: (e as Error).message }), 'fail');
    } finally {
        if (btn) btn.disabled = false;
    }
}

// 下载 MR.ERP 批量导入 Excel · 带鉴权 fetch 取 blob 触发下载(普通 <a> 带不了 token)。
// preflight 不合格后端回 422 + 错误码 → 提示用户缺什么(同推送那套友好文案)。
async function downloadMrerpXlsx(historyId: any) {
    const btn = document.getElementById('drawer-mrerp-xlsx-btn') as HTMLButtonElement;
    if (btn) btn.disabled = true;
    try {
        const resp = await fetch('/api/erp/mrerp-xlsx/' + encodeURIComponent(historyId), {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) {
            let code = 'err.unknown';
            try {
                const data = await resp.json();
                if (data && data.detail) code = data.detail;
            } catch (_e) {
                /* 非 JSON 错误体 · 用默认码 */
            }
            showToast(t('mrerp-xlsx-fail', { err: code }), 'fail');
            return;
        }
        const blob = await resp.blob();
        let fname = 'mrerp.xlsx';
        const cd = resp.headers.get('Content-Disposition') || '';
        const m = /filename\*=UTF-8''([^;]+)/.exec(cd);
        if (m) fname = decodeURIComponent(m[1]);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fname;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        showToast(t('mrerp-xlsx-ok'));
    } catch (e) {
        showToast(t('mrerp-xlsx-fail', { err: (e as Error).message }), 'fail');
    } finally {
        if (btn) btn.disabled = false;
    }
}

// 桥回 home.js:ocr-results.js 的 openDrawer 抽屉打开时调
window.injectOcrPushButton = injectOcrPushButton;
