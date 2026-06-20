// ============================================================
// src/home/erp-express-steps.js · Express 接通向导「右栏步骤内容」构建器
//
// 从 erp-express-wizard 拆出(单文件 <500)· 纯 HTML 构建,无副作用、不发请求。
// 渲染逻辑与类名零改:七步内容 + 步骤标题(_h)+ 账套白名单(锁 DATAT/真账套灰)。
// 暴露 (window).ExpressSteps.render(step, ctx) · ctx = { S, t, esc }(向导注入状态与桥)。
// ============================================================
(function () {
    'use strict';

    var ACCOUNT_SETS = [
        { code: 'DATAT', name: '9.ข้อมูลทดสอบ (DATAT)', locked: false },
        { code: 'PDATAT', name: '58ASIA-SPORT (PDATAT)', locked: true },
        { code: 'DATAZ', name: 'Z.ข้อมูลเปล่า (DATAZ)', locked: true },
    ];

    function render(step: number, ctx: any) {
        var S = ctx.S;
        var _t = ctx.t;
        var _esc = ctx.esc;

        function _h(hKey: string, subKey: string) {
            return (
                '<div class="exp-step-h">' +
                _esc(_t(hKey)) +
                '</div><div class="exp-step-sub">' +
                _esc(_t(subKey)) +
                '</div>'
            );
        }

        function _stepErp() {
            var opts = [
                { id: 'express', name: 'Express', tag: _t('exp-erp-tag-main'), soon: false },
                { id: 'flowaccount', name: 'FlowAccount', tag: _t('exp-erp-soon'), soon: true },
                { id: 'peak', name: 'PEAK', tag: _t('exp-erp-soon'), soon: true },
                { id: 'xero', name: 'Xero', tag: _t('exp-erp-soon'), soon: true },
            ];
            var grid = opts
                .map(function (o) {
                    return (
                        '<div class="exp-erp-opt' +
                        (o.id === 'express' ? ' selected' : o.soon ? ' soon' : '') +
                        '"><div class="exp-erp-name">' +
                        _esc(o.name) +
                        '</div><div class="exp-erp-tag">' +
                        _esc(o.tag) +
                        '</div></div>'
                    );
                })
                .join('');
            return _h('exp-s1-h', 'exp-s1-sub') + '<div class="exp-erp-grid">' + grid + '</div>';
        }

        function _stepAgent() {
            var tokenHtml = S.token
                ? '<div class="exp-token-box"><span class="exp-token-val">' +
                  _esc(S.token) +
                  '</span><button type="button" class="btn btn-ghost btn-tiny" id="exp-copy-token">' +
                  _esc(_t('exp-copy')) +
                  '</button></div><div class="exp-notice info">' +
                  _esc(_t('exp-token-once')) +
                  '</div>'
                : '<button type="button" class="btn btn-primary" id="exp-gen-token">' +
                  _esc(_t('exp-gen-token')) +
                  '</button>';
            var waitCls = S.online ? 'exp-wait online' : 'exp-wait';
            var waitTxt = S.online ? _t('exp-agent-online') : _t('exp-agent-waiting');
            return (
                _h('exp-s2-h', 'exp-s2-sub') +
                '<button type="button" class="btn btn-ghost" id="exp-dl-agent">' +
                _esc(_t('exp-download-agent')) +
                '</button><div style="height:12px"></div>' +
                tokenHtml +
                '<div id="exp-agent-notice"></div><div class="' +
                waitCls +
                '"><span class="exp-wait-dot"></span>' +
                _esc(waitTxt) +
                '</div>'
            );
        }

        function _stepAccount() {
            var list = ACCOUNT_SETS.map(function (a) {
                var sel = a.code === S.accountSet && !a.locked;
                return (
                    '<div class="exp-acct-opt' +
                    (sel ? ' selected' : '') +
                    (a.locked ? ' locked' : '') +
                    '" data-acct="' +
                    _esc(a.code) +
                    '"><span class="exp-acct-name">' +
                    _esc(a.name) +
                    '</span><span class="exp-acct-tag">' +
                    _esc(a.locked ? _t('exp-acct-locked') : _t('exp-acct-test')) +
                    '</span></div>'
                );
            }).join('');
            return (
                _h('exp-s3-h', 'exp-s3-sub') +
                '<div class="exp-acct-list">' +
                list +
                '</div><div class="exp-notice warn">' +
                _esc(_t('exp-acct-warn')) +
                '</div>'
            );
        }

        function _stepMethod() {
            var card = function (m: string, nameK: string, descK: string) {
                return (
                    '<div class="exp-method-card' +
                    (S.method === m ? ' selected' : '') +
                    '" data-method="' +
                    m +
                    '"><div class="exp-method-name">' +
                    _esc(_t(nameK)) +
                    '</div><div class="exp-method-desc">' +
                    _esc(_t(descK)) +
                    '</div></div>'
                );
            };
            return (
                _h('exp-s4-h', 'exp-s4-sub') +
                '<div class="exp-method-grid">' +
                card('rpa', 'exp-method-rpa', 'exp-method-rpa-desc') +
                card('dbf', 'exp-method-dbf', 'exp-method-dbf-desc') +
                '</div>'
            );
        }

        function _stepMapping() {
            return (
                _h('exp-s5-h', 'exp-s5-sub') +
                '<div class="exp-notice info">' +
                _esc(_t('exp-map-auto')) +
                '</div><button type="button" class="btn btn-ghost" id="exp-open-mappings">' +
                _esc(_t('exp-map-advanced')) +
                '</button>'
            );
        }

        function _stepTest() {
            var rowFn = function (key: string, ok: boolean) {
                return (
                    '<div class="exp-check-row"><span class="exp-check-mark' +
                    (ok ? '' : ' pending') +
                    '">' +
                    (ok ? '✓' : '○') +
                    '</span>' +
                    _esc(_t(key)) +
                    '</div>'
                );
            };
            return (
                _h('exp-s6-h', 'exp-s6-sub') +
                '<div class="exp-checklist">' +
                rowFn('exp-test-agent', S.online) +
                rowFn('exp-test-account', true) +
                rowFn('exp-test-mapping', true) +
                '</div>'
            );
        }

        function _stepFinish() {
            return (
                _h('exp-s7-h', 'exp-s7-sub') +
                '<div class="exp-finish-toggle"><div><div class="exp-finish-toggle-label">' +
                _esc(_t('exp-autopush-label')) +
                '</div><div class="exp-finish-toggle-hint">' +
                _esc(_t('exp-autopush-hint')) +
                '</div></div><label class="form-switch-row"><input type="checkbox" id="exp-autopush"' +
                (S.autoPush ? ' checked' : '') +
                '><span class="form-switch-label"></span></label></div>'
            );
        }

        if (step === 1) return _stepErp();
        if (step === 2) return _stepAgent();
        if (step === 3) return _stepAccount();
        if (step === 4) return _stepMethod();
        if (step === 5) return _stepMapping();
        if (step === 6) return _stepTest();
        return _stepFinish();
    }

    (window as any).ExpressSteps = { render: render };
})();
