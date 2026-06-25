// ============================================================
// src/home/erp-express-connect.js · Express 连接卡(P3a)
//
// 渲染:自动化 → ERP 对接 → 连接 sub-tab 顶部 #erp-connect-cards · 独立 zone
//   [data-express-zone] · 复用 integration-row / int-* / mrerp-card-pill(四态)样式系统。
// 四态徽章(已连接 ok / Agent离线 warn / 异常 err / 未完成 neutral)—— 颜色走令牌 pill 类,无 emoji。
// Agent 在线靠 config.agent_last_seen_at(近 3 分钟有心跳=在线)。迷你统计取 /api/erp/logs?adapter=express
// 按 status 派生(排队中 pending 不算已推 · 状态诚实)。点连接/编辑 → window.ExpressWizard.open(ep)。
// 全局桥:t / escapeHtml · token 经 localStorage。
// ============================================================
/* global escapeHtml */
(function () {
    'use strict';

    var ONLINE_MS = 180000; // 3 分钟内有心跳算在线
    var _ep: any = null;
    var _stats = { success: 0, pending: 0, failed: 0 };

    function _esc(s: any) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function _t(k: string) {
        try {
            var v = typeof t === 'function' ? t(k) : k;
            return v || k;
        } catch (e) {
            return k;
        }
    }
    function _tk() {
        return localStorage.getItem('mrpilot_token');
    }

    function _isOnline(ep: any) {
        var seen = ep && ep.config && ep.config.agent_last_seen_at;
        if (!seen) return false;
        var ts = new Date(seen).getTime();
        return !isNaN(ts) && Date.now() - ts < ONLINE_MS;
    }

    async function _load() {
        var tk = _tk();
        if (!tk) return;
        try {
            var r = await fetch('/api/erp/endpoints', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) throw new Error('http_' + r.status);
            var d = await r.json();
            _ep =
                ((d && d.items) || []).find(function (e: any) {
                    return e && (e.adapter || '').toLowerCase() === 'express';
                }) || null;
        } catch (e) {
            _ep = null;
        }
        await _loadStats();
    }

    async function _loadStats() {
        _stats = { success: 0, pending: 0, failed: 0 };
        if (!_ep) return;
        var tk = _tk();
        try {
            // 计数跟随当前账套(与推送日志/识别记录同口径):带账套头,避免跨账套串数。
            var r = await fetch('/api/erp/logs?adapter=express&limit=200', {
                headers: Object.assign(
                    { Authorization: 'Bearer ' + tk },
                    typeof window._wsHeader === 'function' ? window._wsHeader() : {}
                ),
            });
            if (!r.ok) return;
            var d = await r.json();
            ((d && d.items) || []).forEach(function (it: any) {
                var s = (it && it.status) || '';
                if (s === 'success') _stats.success++;
                else if (s === 'pending') _stats.pending++;
                else if (s === 'failed' || s === 'manual') _stats.failed++;
            });
        } catch (e) {}
    }

    // 连接徽章 = 纯连接真相(心跳新鲜度),不再被推送失败染红。推送失败单独成行(_render 里)。
    //   未配对 neutral / 停用 neutral / 已连接 ok / 离线·自动重连中 warn。
    function _state() {
        if (!_ep) return { pill: 'mrerp-pill-neutral', key: 'exp-pill-incomplete' };
        if (_ep.enabled === false) return { pill: 'mrerp-pill-neutral', key: 'exp-pill-disabled' };
        if (_isOnline(_ep)) return { pill: 'mrerp-pill-ok', key: 'exp-pill-connected' };
        return { pill: 'mrerp-pill-warn', key: 'exp-pill-offline' };
    }

    function _render() {
        var host = document.getElementById('erp-connect-cards');
        if (!host) return;
        var zone = host.querySelector('[data-express-zone]');
        if (!zone) {
            zone = document.createElement('div');
            zone.setAttribute('data-express-zone', '1');
            host.appendChild(zone);
        }

        var st = _state();
        var pill = '<span class="mrerp-card-pill ' + st.pill + '">' + _esc(_t(st.key)) + '</span>';

        var configured = !!_ep;
        var acct = (configured && _ep.config && _ep.config.account_set) || 'DATAT';
        var metaHtml = configured
            ? '<div class="exp-mini-stats">' +
              '<span><b>' +
              _stats.success +
              '</b> ' +
              _esc(_t('exp-stat-pushed')) +
              '</span>' +
              '<span><b>' +
              _stats.pending +
              '</b> ' +
              _esc(_t('exp-stat-pending')) +
              '</span>' +
              '<span><b>' +
              _stats.failed +
              '</b> ' +
              _esc(_t('exp-stat-failed')) +
              '</span></div>'
            : '';

        var offlineBar =
            configured && !_isOnline(_ep) && _stats.pending > 0
                ? '<div class="exp-offline-bar">' +
                  _esc(_t('exp-offline-wait').replace('{n}', String(_stats.pending))) +
                  '</div>'
                : '';

        // 推送失败单独成行(与连接徽章分离·连接好也可能有失败票要处理)。
        var failedBar =
            configured && _stats.failed > 0
                ? '<div class="exp-failed-bar">' +
                  _esc(_t('exp-conn-failed-line').replace('{n}', String(_stats.failed))) +
                  '</div>'
                : '';

        var enabled = !configured || _ep.enabled !== false;
        var actions;
        if (!configured) {
            actions =
                '<button type="button" class="int-btn-configure" id="btn-express-connect">' +
                _esc(_t('exp-card-connect')) +
                '</button>';
        } else {
            // 停用 → 编辑禁用(卡片不可改)· 启用/停用按钮对齐 MR.ERP DMS 卡。
            actions =
                '<button type="button" class="int-btn-configure" id="btn-express-edit"' +
                (enabled ? '' : ' disabled') +
                '>' +
                _esc(_t('exp-card-edit')) +
                '</button>' +
                '<button type="button" class="int-btn-configure" id="btn-express-toggle">' +
                _esc(_t(enabled ? 'exp-card-disable' : 'exp-card-enable')) +
                '</button>';
        }

        zone.innerHTML =
            '<div class="integration-row erp-connect-express' +
            (configured ? ' connected' : '') +
            (configured && !enabled ? ' is-disabled' : '') +
            '">' +
            '<div class="int-icon ic-express">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
            '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M8 14h8"/></svg>' +
            '</div>' +
            '<div class="int-info">' +
            '<div class="int-name"><span>' +
            _esc(_t('exp-card-title')) +
            '</span>' +
            pill +
            '</div>' +
            '<div class="int-desc">' +
            _esc(_t('exp-card-desc')) +
            (configured ? ' · ' + _esc(acct) : '') +
            (configured && _isOnline(_ep) && _ep.config && _ep.config.agent_device_name
                ? ' · ' + _esc(_ep.config.agent_device_name)
                : '') +
            '</div>' +
            metaHtml +
            offlineBar +
            failedBar +
            '</div>' +
            '<div class="int-actions">' +
            actions +
            '</div>' +
            '</div>';
    }

    async function _refresh() {
        await _load();
        _render();
    }

    function _open() {
        if (_ep && _ep.enabled === false) return; // 停用 → 不可编辑
        var w = (window as any).ExpressWizard;
        if (w && w.open) w.open(_ep);
    }

    async function _toggle() {
        if (!_ep || !_ep.id) return;
        var enabling = _ep.enabled === false;
        if (!enabling) {
            try {
                var ok = await window.pearnlyConfirm(_t('exp-confirm-disable'));
                if (!ok) return;
            } catch (e) {}
        }
        try {
            var r = await fetch('/api/erp/endpoints/' + encodeURIComponent(_ep.id), {
                method: 'PATCH',
                headers: { Authorization: 'Bearer ' + _tk(), 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enabling }),
            });
            if (!r.ok) throw new Error('http_' + r.status);
            // 同步全局端点缓存 → OCR 推送 picker 立刻反映启停(铁律 #12 单一源)。
            if (typeof window._refreshErpEndpointsCache === 'function')
                window._refreshErpEndpointsCache();
            try {
                if (typeof showToast === 'function')
                    showToast(_t(enabling ? 'exp-enabled-toast' : 'exp-disabled-toast'), 'success');
            } catch (e) {}
            await _refresh();
        } catch (e) {
            try {
                if (typeof showToast === 'function') showToast(_t('exp-token-fail'), 'error');
            } catch (e2) {}
        }
    }

    document.addEventListener('click', function (ev) {
        var tg = ev.target as HTMLElement;
        if (tg.closest('.erp-subtab[data-erp-subtab="connect"]')) {
            setTimeout(_refresh, 60);
            return;
        }
        if (tg.closest('.auto-nav-item[data-auto-tab="erp"]')) {
            setTimeout(_refresh, 90);
            return;
        }
        if (tg.closest('#btn-express-toggle')) {
            ev.preventDefault();
            _toggle();
            return;
        }
        if (tg.closest('#btn-express-connect') || tg.closest('#btn-express-edit')) {
            ev.preventDefault();
            _open();
            return;
        }
    });

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('express-adapter', _render);
    }

    (window as any).ExpressConnect = { refresh: _refresh };

    function _visible() {
        return (
            !!document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]') &&
            !!document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]')
        );
    }

    setTimeout(function () {
        if (_visible()) _refresh();
    }, 260);

    // 在线状态自愈:卡片无自轮询(只 tab 点击刷新)会冻结过期快照→显「离线」但向导/托盘已在线。
    // 可见时每 60s 重探心跳(在线窗口 3 分钟·余量足;向导翻转另有 _syncCard 即时同步)·铁律#12。
    setInterval(function () {
        if (_visible()) _refresh();
    }, 60000);

    // 刚打开/小助手刚启动那阵:可见时前 ~30s 快查(每 5s),让网页几秒内自己变绿,不用等 60s 那拍。
    var _fastN = 0;
    var _fast = setInterval(function () {
        if (!_visible()) return;
        _refresh();
        if (++_fastN >= 6) clearInterval(_fast); // 6×5s=30s 后回落常速
    }, 5000);
})();
