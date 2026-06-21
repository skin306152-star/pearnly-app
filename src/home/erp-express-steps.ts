// ============================================================
// src/home/erp-express-steps.js · Express 接通向导「双栏 body 骨架」构建器(重设计 v2)
//
// 照搬 pearnly_express_modal_redesign_v2.html 的结构/布局/分步/文案,只换设计令牌 + 线性
// SVG 图标 + exp- 前缀类名。纯 HTML 构建,无副作用、不发请求;状态由 wizard 的 updateUI
// 定点更新(非整体重渲染 · 保平滑滚动)。暴露 (window).ExpressSteps.render(ctx)。
// ============================================================
(function () {
    'use strict';

    // 线性图标(stroke · currentColor · 非 emoji)。
    var IC_GEAR =
        '<svg class="exp-chev-ic" viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="2.1"/><path d="M8 1.6v1.6M8 12.8v1.6M3.1 3.1l1.1 1.1M11.8 11.8l1.1 1.1M1.6 8h1.6M12.8 8h1.6M3.1 12.9l1.1-1.1M11.8 4.2l1.1-1.1"/></svg>';
    var IC_CHEV =
        '<svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10l4-4 4 4"/></svg>';

    function render(ctx: any) {
        var _t = ctx.t;
        var _esc = ctx.esc;
        var t = function (k: string) {
            return _esc(_t(k));
        };

        function railStep(n: string, target: string, id: string, nameK: string, descK: string) {
            return (
                '<div class="exp-step-link" data-target="' +
                target +
                '" id="' +
                id +
                '"><div class="exp-step-num">' +
                n +
                '</div><div><div class="exp-step-name">' +
                t(nameK) +
                '</div><div class="exp-step-desc">' +
                t(descK) +
                '</div></div></div>'
            );
        }

        var rail =
            '<aside class="exp-rail">' +
            '<p class="exp-rail-title">' +
            t('exp-rail-title') +
            '</p>' +
            railStep('1', 'exp-step1', 'exp-rail1', 'exp-s2-h', 'exp-rail-s1-desc') +
            railStep('2', 'exp-step2', 'exp-rail2', 'exp-rail-s2-name', 'exp-rail-s2-desc') +
            railStep('3', 'exp-step3', 'exp-rail3', 'exp-s3-h', 'exp-rail-s3-desc') +
            '<div class="exp-rail-card">' +
            '<b id="exp-progress-title"></b>' +
            '<p id="exp-progress-text"></p>' +
            '<div class="exp-progress"><div class="exp-bar" id="exp-bar"></div></div>' +
            '</div></aside>';

        // step1 装小助手
        var step1 =
            '<section class="exp-sec" id="exp-step1"><div class="exp-sec-head">' +
            '<h3 class="exp-sec-title"><span>1.</span> ' +
            t('exp-s2-h') +
            '</h3><span class="exp-badge waiting" id="exp-badge1"></span></div>' +
            '<div class="exp-sec-copy"><div>' +
            t('exp-install-hint') +
            '</div><div class="exp-action-row">' +
            '<button class="exp-primary" id="exp-download">' +
            t('exp-download-agent') +
            '</button><span class="exp-help-text" id="exp-download-hint">' +
            t('exp-download-hint-1') +
            '</span></div></div></section>';

        // step2 配对码
        var step2 =
            '<section class="exp-sec" id="exp-step2"><div class="exp-sec-head">' +
            '<h3 class="exp-sec-title"><span>2.</span> ' +
            t('exp-pair-h') +
            '</h3><span class="exp-badge todo" id="exp-badge2"></span></div>' +
            '<div class="exp-sec-copy"><div>' +
            t('exp-pair-hint') +
            '</div><div class="exp-code-box" id="exp-codebox" style="display:none">' +
            '<div><div class="exp-code-value" id="exp-codeval">PEX-----</div>' +
            '<div class="exp-code-note">' +
            t('exp-code-note') +
            '</div></div>' +
            '<button class="exp-secondary" id="exp-copy">' +
            t('exp-copy') +
            '</button></div>' +
            '<div class="exp-action-row"><button class="exp-primary" id="exp-generate">' +
            t('exp-gen-token') +
            '</button><div id="exp-agent-notice"></div></div></div></section>';

        // step3 选账套
        var step3 =
            '<section class="exp-sec" id="exp-step3"><div class="exp-sec-head">' +
            '<h3 class="exp-sec-title"><span>3.</span> ' +
            t('exp-s3-h') +
            '</h3><span class="exp-badge todo" id="exp-badge3"></span></div>' +
            '<div class="exp-sec-copy"><div>' +
            t('exp-acct-pending') +
            '</div><div class="exp-empty-account" id="exp-empty-account">' +
            t('exp-empty-account') +
            '</div><div class="exp-account-list" id="exp-acctlist" style="display:none"></div>' +
            '</div></section>';

        // 自动推送
        var toggle =
            '<section class="exp-toggle-card"><div><b>' +
            t('exp-autopush-label') +
            '</b><span>' +
            t('exp-autopush-hint') +
            '</span></div><label class="exp-switch" aria-label="' +
            t('exp-autopush-label') +
            '"><input type="checkbox" id="exp-pushtoggle"><span class="exp-slider"></span></label></section>';

        // 高级设置(录入方式:直录 + 查看说明 / 模拟录入占位)· 照搬源初始展开
        var help =
            '<div class="exp-choice-help-panel" id="exp-direct-help" aria-hidden="true">' +
            '<p><b>' +
            t('exp-how-what-h') +
            '</b><br>' +
            t('exp-how-what') +
            '</p><p><b>' +
            t('exp-how-work-h') +
            '</b><br>· ' +
            t('exp-how-work-1') +
            '<br>· ' +
            t('exp-how-work-2') +
            '<br>· ' +
            t('exp-how-work-3') +
            '</p><p><b>' +
            t('exp-how-note-h') +
            '</b><br>· ' +
            t('exp-how-note-1') +
            '<br>· ' +
            t('exp-how-note-2') +
            '<br>· ' +
            t('exp-how-note-3') +
            '<br>· ' +
            t('exp-how-note-4') +
            '</p></div>';
        var advanced =
            '<section class="exp-info-panel" id="exp-advanced">' +
            '<button class="exp-fold-head" type="button" data-fold="exp-advanced">' +
            '<span class="exp-fold-title">' +
            IC_GEAR +
            ' ' +
            t('exp-adv-title') +
            '</span><span class="exp-chev">' +
            IC_CHEV +
            '</span></button>' +
            '<div class="exp-fold-body"><div class="exp-answer-box"><p><b>' +
            t('exp-method-label') +
            '</b></p><div class="exp-settings-grid">' +
            '<div class="exp-choice active direct-choice" id="exp-direct-choice"><div class="exp-choice-main">' +
            '<div><b>' +
            t('exp-method-direct') +
            '</b><span>' +
            t('exp-method-direct-desc') +
            '</span></div>' +
            '<button class="exp-choice-help-btn" type="button" id="exp-direct-help-btn">' +
            t('exp-direct-help-show') +
            '</button></div>' +
            help +
            '</div>' +
            '<div class="exp-choice disabled"><b>' +
            t('exp-method-sim') +
            ' ' +
            t('exp-erp-soon') +
            '</b><span>' +
            t('exp-method-sim-desc') +
            '</span></div>' +
            '</div></div></div></section>';

        return (
            '<div class="exp-modal-body">' +
            rail +
            '<main class="exp-scroll" id="exp-scroll">' +
            step1 +
            step2 +
            step3 +
            toggle +
            advanced +
            '</main></div>'
        );
    }

    (window as any).ExpressSteps = { render: render };
})();
