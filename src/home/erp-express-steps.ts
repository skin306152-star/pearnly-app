// ============================================================
// src/home/erp-express-steps.js · Express 接通向导「双栏 body 骨架」构建器(重设计 v2)
//
// 照搬 pearnly_express_modal_redesign_v2.html 的结构/布局/分步/文案,只换设计令牌 + 线性
// SVG 图标 + exp- 前缀类名。纯 HTML 构建,无副作用、不发请求;状态由 wizard 的 updateUI
// 定点更新(非整体重渲染 · 保平滑滚动)。暴露 (window).ExpressSteps.render(ctx)。
// ============================================================
(function () {
    'use strict';

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
            '<button class="btn exp-primary" id="exp-download">' +
            t('exp-download-agent') +
            '</button><button class="btn exp-secondary" id="exp-skip-download">' +
            t('exp-skip-download') +
            '</button><span class="exp-help-text" id="exp-download-hint">' +
            t('exp-download-hint-1') +
            '</span></div></div></section>';

        // step2 配对码
        var step2 =
            '<section class="exp-sec" id="exp-step2"><div class="exp-sec-head">' +
            '<h3 class="exp-sec-title"><span>2.</span> ' +
            t('exp-pair-h') +
            '</h3><span class="exp-badge todo" id="exp-badge2"></span></div>' +
            '<div class="exp-sec-copy"><div id="exp-pair-hint">' +
            t('exp-pair-hint') +
            '</div><div class="exp-code-box" id="exp-codebox" style="display:none">' +
            '<div><div class="exp-code-value" id="exp-codeval">PEX-••••</div>' +
            '<div class="exp-code-note" id="exp-code-note">' +
            t('exp-code-note') +
            '</div></div>' +
            '<button class="exp-iconbtn exp-eye" id="exp-eye" type="button" style="display:none"></button>' +
            '<button class="btn exp-secondary" id="exp-copy">' +
            t('exp-copy') +
            '</button></div>' +
            '<div class="exp-action-row"><button class="btn exp-primary" id="exp-generate">' +
            t('exp-gen-token') +
            '</button><div id="exp-agent-notice"></div></div></div></section>';

        // step3 选账套(只读状态镜像 · 账套只在小助手里选,网页同步显示)
        var step3 =
            '<section class="exp-sec" id="exp-step3"><div class="exp-sec-head">' +
            '<h3 class="exp-sec-title"><span>3.</span> ' +
            t('exp-s3-h') +
            '</h3><span class="exp-badge todo" id="exp-badge3"></span></div>' +
            '<div class="exp-sec-copy"><div>' +
            t('exp-acct-mirror-hint') +
            '</div><div class="exp-account-mirror waiting" id="exp-acct-mirror"></div>' +
            '</div></section>';

        // 自动推送
        var _mc = function (v: string, lk: string, dk: string) {
            return (
                '<label class="exp-toggle-card exp-mode-card"><div><b>' +
                t(lk) +
                '</b><span>' +
                t(dk) +
                '</span></div><input type="radio" name="exp-pushmode" class="exp-mode-radio" value="' +
                v +
                '"></label>'
            );
        };
        var toggle =
            '<div class="exp-pushmode-group">' +
            _mc('manual', 'exp-pushmode-manual', 'exp-pushmode-manual-d') +
            _mc('full', 'exp-pushmode-full', 'exp-pushmode-full-d') +
            '</div>';

        return (
            '<div class="exp-modal-body">' +
            rail +
            '<main class="exp-scroll" id="exp-scroll">' +
            step1 +
            step2 +
            step3 +
            toggle +
            '</main></div>'
        );
    }

    // ── 模态外壳 + 定点更新用的展示辅助(从 wizard 抽出 · 编排/展示分离 · wizard 只管流程)──
    var IC_CLOSE =
        '<svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4l8 8M12 4l-8 8"/></svg>';
    // 小眼睛(显/隐密钥)· SVG 非 emoji(过 lint-ui 棘轮)。
    var IC_EYE =
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>';
    var IC_EYE_OFF =
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.9 17.9A10.5 10.5 0 0 1 12 19c-7 0-11-7-11-7a18.4 18.4 0 0 1 5.1-5.9M9.9 4.2A10.5 10.5 0 0 1 12 4c7 0 11 7 11 7a18.5 18.5 0 0 1-2.2 3.2M9.9 9.9a3 3 0 0 0 4.2 4.2M1 1l22 22"/></svg>';

    function _g(id: string) {
        return document.getElementById(id);
    }

    function renderShell(ctx: any) {
        var _t = ctx.t;
        var _esc = ctx.esc;
        return (
            '<section class="exp-modal" role="dialog" aria-modal="true" aria-labelledby="exp-modal-title">' +
            '<header class="exp-modal-header"><div class="exp-mh-title">' +
            '<div class="exp-mh-icon">Ex</div><div>' +
            '<h2 class="exp-mh-h2" id="exp-modal-title">' +
            _esc(_t('exp-wizard-title')) +
            '</h2><p class="exp-mh-lead">' +
            _esc(_t('exp-s1-sub')) +
            '</p></div></div><div class="exp-mh-actions">' +
            '<div class="exp-topstatus" id="exp-topstatus"><span class="exp-pulse"></span><span class="exp-ts-text"></span></div>' +
            '<button class="exp-iconbtn" id="exp-close" aria-label="' +
            _esc(_t('exp-cancel')) +
            '">' +
            IC_CLOSE +
            '</button></div></header>' +
            render(ctx) +
            '<footer class="exp-footer"><div class="exp-footer-note" id="exp-footer-note"></div>' +
            '<div class="exp-footer-actions">' +
            '<button class="btn exp-secondary" id="exp-cancel">' +
            _esc(_t('exp-cancel')) +
            '</button><button class="btn exp-primary" id="exp-done" disabled>' +
            _esc(_t('exp-done')) +
            '</button></div></footer></section>'
        );
    }

    // 密钥区(标准做法):刚生成=整串可显隐+复制+仅此一次;已配过=只掩码(只存哈希·无法再看)+重置;
    // 从未配=显示「生成密钥」主按钮。已连接时配对说明改「已连接·无需操作」。
    function renderKeyArea(S: any, t: any) {
        var cb = _g('exp-codebox');
        var gen = _g('exp-generate');
        var eye = _g('exp-eye');
        var copy = _g('exp-copy');
        var val = _g('exp-codeval');
        var note = _g('exp-code-note');
        var hint = _g('exp-pair-hint');
        var masked = 'PEX-••••' + (S.tail ? '-' + S.tail : '');
        if (hint) hint.textContent = t(S.connected ? 'exp-pair-connected' : 'exp-pair-hint');
        if (S.token) {
            if (cb) cb.style.display = 'grid';
            if (val) val.textContent = S.keyRevealed ? S.token : masked;
            if (eye) {
                eye.style.display = '';
                eye.innerHTML = S.keyRevealed ? IC_EYE_OFF : IC_EYE;
                eye.setAttribute('title', t(S.keyRevealed ? 'exp-key-hide' : 'exp-key-reveal'));
            }
            if (copy) copy.style.display = '';
            if (note) note.textContent = t('exp-key-once');
            if (gen) {
                gen.textContent = t('exp-key-reset');
                gen.className = 'btn exp-secondary exp-danger';
            }
        } else if (S.hasKey) {
            if (cb) cb.style.display = 'grid';
            if (val) val.textContent = masked;
            if (eye) eye.style.display = 'none';
            if (copy) copy.style.display = 'none';
            if (note) note.textContent = t('exp-key-set-once');
            if (gen) {
                gen.textContent = t('exp-key-reset');
                gen.className = 'btn exp-secondary exp-danger';
            }
        } else {
            if (cb) cb.style.display = 'none';
            if (gen) {
                gen.textContent = t('exp-gen-token');
                gen.className = 'btn exp-primary';
            }
        }
    }

    function fillAcctMirror(S: any, t: any) {
        var el = _g('exp-acct-mirror');
        if (!el) return;
        if (S.account) {
            el.className = 'exp-account-mirror selected';
            var shown = S.accountName || S.account;
            el.textContent = t('exp-acct-selected-mirror').replace('{x}', String(shown)) + ' ✓';
        } else {
            el.className = 'exp-account-mirror waiting';
            el.textContent = t('exp-acct-wait-select');
        }
    }

    function scrollToStep(target: string) {
        var scroller = _g('exp-scroll');
        var el = _g(target);
        if (scroller && el) scroller.scrollTo({ top: el.offsetTop - 18, behavior: 'smooth' });
        var links = document.querySelectorAll('.exp-step-link');
        for (var i = 0; i < links.length; i++) links[i].classList.remove('active');
        var active = document.querySelector('[data-target="' + target + '"]');
        if (active) active.classList.add('active');
    }

    (window as any).ExpressSteps = {
        render: render,
        renderShell: renderShell,
        renderKeyArea: renderKeyArea,
        fillAcctMirror: fillAcctMirror,
        scrollToStep: scrollToStep,
    };
})();
