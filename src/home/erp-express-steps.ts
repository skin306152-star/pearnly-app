// ============================================================
// src/home/erp-express-steps.js · Express 接通向导「单屏内容」构建器
//
// 从 erp-express-wizard 拆出(单文件 <500)· 纯 HTML 构建,无副作用、不发请求。
// 一屏:装小助手 → 填配对码(生成/复制/等连上)→ 连上选账套(读心跳上报的账套·连上后常显
// 「夜间保持开机」提示)→「直录是怎么工作的?」折叠说明 → 自动推送(默认开)→ 高级设置
// (录入方式:直录启用 / 模拟录入占位)。线性图标 · 无 emoji · 复用 exp-* 类(暗夜随令牌)。
// 暴露 (window).ExpressSteps.render(ctx) · ctx = { S, t, esc }(向导注入状态与桥)。
// ============================================================
(function () {
    'use strict';

    // 线性图标(stroke · 跟随 currentColor · 非 emoji)。
    var IC_HELP =
        '<svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M6.3 6.1a1.7 1.7 0 0 1 3.2.6c0 1.1-1.4 1.4-1.5 2.3"/><circle cx="8" cy="11.6" r="0.5" fill="currentColor" stroke="none"/></svg>';
    var IC_MOON =
        '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M13.2 9.6A5.4 5.4 0 0 1 6.4 2.8 5.4 5.4 0 1 0 13.2 9.6z"/></svg>';
    var IC_GEAR =
        '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="2.1"/><path d="M8 1.6v1.6M8 12.8v1.6M3.1 3.1l1.1 1.1M11.8 11.8l1.1 1.1M1.6 8h1.6M12.8 8h1.6M3.1 12.9l1.1-1.1M11.8 4.2l1.1-1.1"/></svg>';
    function chevron(open: boolean) {
        var d = open ? 'M4 10l4-4 4 4' : 'M4 6l4 4 4-4';
        return (
            '<svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" style="margin-left:auto"><path d="' +
            d +
            '"/></svg>'
        );
    }

    function render(ctx: any) {
        var S = ctx.S;
        var _t = ctx.t;
        var _esc = ctx.esc;

        function _h(n: string, key: string) {
            return '<div class="exp-step-h">' + n + '. ' + _esc(_t(key)) + '</div>';
        }
        function _sub(key: string) {
            return '<div class="exp-step-sub">' + _esc(_t(key)) + '</div>';
        }
        function _gap() {
            return '<div style="height:18px"></div>';
        }
        function _line(key: string) {
            return '<div style="margin-top:3px">· ' + _esc(_t(key)) + '</div>';
        }
        function _subh(key: string, first: boolean) {
            return (
                '<div style="font-weight:600' +
                (first ? '' : ';margin-top:11px') +
                '">' +
                _esc(_t(key)) +
                '</div>'
            );
        }
        // 折叠头(线性图标 + 标题 + 收展 chevron)。
        function _toggle(id: string, icon: string, key: string, open: boolean) {
            return (
                '<div class="exp-step-h" id="' +
                id +
                '" style="cursor:pointer;display:flex;align-items:center;gap:8px;margin:0">' +
                icon +
                '<span>' +
                _esc(_t(key)) +
                '</span>' +
                chevron(open) +
                '</div>'
            );
        }

        // 1. 装小助手(装在能打开 Express 的那台电脑 · 只装一次)
        var sec1 =
            _h('1', 'exp-s2-h') +
            _sub('exp-install-hint') +
            '<button type="button" class="btn btn-ghost" id="exp-dl-agent">' +
            _esc(_t('exp-download-agent')) +
            '</button>';

        // 2. 填配对码(先生成 · 复制进小助手 · 等它回连)
        var sec2body;
        if (S.token) {
            var waitCls = S.online ? 'exp-wait online' : 'exp-wait';
            var waitTxt = S.online ? _t('exp-agent-online') : _t('exp-agent-waiting');
            sec2body =
                '<div class="exp-token-box"><span class="exp-token-val">' +
                _esc(S.token) +
                '</span><button type="button" class="btn btn-ghost btn-tiny" id="exp-copy-token">' +
                _esc(_t('exp-copy')) +
                '</button></div>' +
                '<div class="exp-notice info">' +
                _esc(_t('exp-token-once')) +
                '</div><div id="exp-agent-notice"></div><div class="' +
                waitCls +
                '"><span class="exp-wait-dot"></span>' +
                _esc(waitTxt) +
                '</div>';
        } else {
            sec2body =
                '<button type="button" class="btn btn-primary" id="exp-gen-token">' +
                _esc(_t('exp-gen-token')) +
                '</button><div id="exp-agent-notice"></div>';
        }
        var sec2 = _h('2', 'exp-pair-h') + _sub('exp-pair-hint') + sec2body;

        // 3. 连上选账套(显小助手心跳上报的账套 · 暂无则识别中占位 · 连上后常显夜间提示)
        var sec3body;
        if (!S.online) {
            sec3body = _sub('exp-acct-pending');
        } else if (S.accounts && S.accounts.length) {
            sec3body =
                '<div class="exp-acct-list">' +
                S.accounts
                    .map(function (code: string) {
                        var sel = code === S.accountSet;
                        return (
                            '<div class="exp-acct-opt' +
                            (sel ? ' selected' : '') +
                            '" data-acct="' +
                            _esc(code) +
                            '"><span class="exp-acct-name">' +
                            _esc(code) +
                            '</span></div>'
                        );
                    })
                    .join('') +
                '</div>';
        } else {
            sec3body =
                '<div class="exp-wait"><span class="exp-wait-dot"></span>' +
                _esc(_t('exp-acct-detecting')) +
                '</div>';
        }
        // 夜间保持开机:连上后常显一句(线性月亮图标 + 一行小字),不只藏在折叠里。
        var nightHint = S.online
            ? '<div class="exp-notice info" style="display:flex;align-items:flex-start;gap:8px;margin-bottom:0">' +
              IC_MOON +
              '<span>' +
              _esc(_t('exp-night-hint')) +
              '</span></div>'
            : '';
        var sec3 = _h('3', 'exp-s3-h') + sec3body + nightHint;

        // 「直录是怎么工作的?」折叠说明(这是什么 / 怎么工作 / 注意事项)。
        var howBody = S.explainerOpen
            ? '<div class="exp-notice info" style="margin-top:8px">' +
              _subh('exp-how-what-h', true) +
              '<div style="margin-top:2px">' +
              _esc(_t('exp-how-what')) +
              '</div>' +
              _subh('exp-how-work-h', false) +
              _line('exp-how-work-1') +
              _line('exp-how-work-2') +
              _line('exp-how-work-3') +
              _subh('exp-how-note-h', false) +
              _line('exp-how-note-1') +
              _line('exp-how-note-2') +
              _line('exp-how-note-3') +
              _line('exp-how-note-4') +
              '</div>'
            : '';
        var explainer =
            _toggle('exp-how-toggle', IC_HELP, 'exp-how-title', S.explainerOpen) + howBody;

        // 自动推送(默认开 · 随时能在连接卡上暂停)
        var autopush =
            '<div class="exp-finish-toggle"><div><div class="exp-finish-toggle-label">' +
            _esc(_t('exp-autopush-label')) +
            '</div><div class="exp-finish-toggle-hint">' +
            _esc(_t('exp-autopush-hint')) +
            '</div></div><label class="form-switch-row"><input type="checkbox" id="exp-autopush"' +
            (S.autoPush ? ' checked' : '') +
            '><span class="form-switch-label"></span></label></div>';

        // 高级设置(默认折叠):录入方式 — 直录(启用)/ 模拟录入(占位 · 即将支持)。
        var advBody = S.advancedOpen
            ? '<div class="exp-notice info" style="margin-top:8px">' +
              '<div style="font-weight:600;margin-bottom:8px">' +
              _esc(_t('exp-method-label')) +
              '</div><div class="exp-method-grid">' +
              '<div class="exp-method-card selected"><div class="exp-method-name">' +
              _esc(_t('exp-method-direct')) +
              '</div><div class="exp-method-desc">' +
              _esc(_t('exp-method-direct-desc')) +
              '</div></div>' +
              '<div class="exp-method-card" data-method="rpa-soon" style="opacity:.55;cursor:not-allowed"><div class="exp-method-name">' +
              _esc(_t('exp-method-sim')) +
              ' <span class="exp-acct-tag">' +
              _esc(_t('exp-erp-soon')) +
              '</span></div><div class="exp-method-desc">' +
              _esc(_t('exp-method-sim-desc')) +
              '</div></div></div></div>'
            : '';
        var advanced =
            _toggle('exp-adv-toggle', IC_GEAR, 'exp-adv-title', S.advancedOpen) + advBody;

        return (
            sec1 +
            _gap() +
            sec2 +
            _gap() +
            sec3 +
            _gap() +
            explainer +
            _gap() +
            autopush +
            _gap() +
            advanced
        );
    }

    (window as any).ExpressSteps = { render: render };
})();
