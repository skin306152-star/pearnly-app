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
        var S = ctx.S || {};
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
            '</button><button class="exp-secondary" id="exp-skip-download">' +
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
            '<button class="exp-secondary" id="exp-copy">' +
            t('exp-copy') +
            '</button></div>' +
            '<div class="exp-action-row"><button class="exp-primary" id="exp-generate">' +
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
            _mc('standard', 'exp-pushmode-standard', 'exp-pushmode-standard-d') +
            _mc('full', 'exp-pushmode-full', 'exp-pushmode-full-d') +
            '</div>';

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

        // 科目映射(销项 收入/应收/销项税 + 采购 采购/应付/进项税)。
        // 有小助手上报的科目表 → 下拉按名字选;没有 → 文本兜底手填科目码。
        var accts = S.accounts && S.accounts.length ? S.accounts : [];
        var ROW = 'style="display:flex;align-items:center;gap:10px;margin:7px 0"';
        var LBL = 'style="min-width:128px;font-size:13px;color:var(--ink2)"';
        // 只读镜像:科目在小助手里选(和账套一样),这里只显示当前配置。code→name 由上报科目表查。
        function _nameForCode(code: string) {
            for (var i = 0; i < accts.length; i++) {
                if (String((accts[i] || {}).code) === String(code)) return accts[i].name || '';
            }
            return '';
        }
        function accField(key: string, labelK: string) {
            var cur = (S.acc && S.acc[key]) || '';
            var nm = _nameForCode(cur);
            var val = cur ? (nm ? _esc(nm) + ' (' + _esc(cur) + ')' : _esc(cur)) : '—';
            return (
                '<div ' +
                ROW +
                '><span ' +
                LBL +
                '>' +
                t(labelK) +
                '</span><b style="flex:1;font-size:13px">' +
                val +
                '</b></div>'
            );
        }
        var accmap =
            '<section class="exp-sec" id="exp-step-accmap"><div class="exp-sec-head">' +
            '<h3 class="exp-sec-title">' +
            t('exp-accmap-title') +
            '</h3></div><div class="exp-sec-copy">' +
            '<div class="exp-help-text">' +
            t('exp-accmap-mirror-hint') +
            '</div>' +
            // 小助手未连/未上报科目表 → 科目无法解析,显式提示(别让用户以为配好了)。
            (accts.length
                ? ''
                : '<div class="exp-help-text"><svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="vertical-align:-2px;margin-right:4px"><path d="M8 1.8L1.5 13.5h13L8 1.8z"/><path d="M8 6.3v3.4M8 11.6h.01"/></svg>' +
                  t('exp-accmap-offline-hint') +
                  '</div>') +
            '<div style="margin-top:10px"><b style="font-size:13px">' +
            t('exp-accmap-sales') +
            '</b>' +
            accField('revenue_acc', 'exp-acc-revenue') +
            accField('ar_acc', 'exp-acc-ar') +
            accField('vat_output_acc', 'exp-acc-vat-out') +
            '</div><div style="margin-top:10px"><b style="font-size:13px">' +
            t('exp-accmap-purchase') +
            '</b>' +
            accField('fallback_acc', 'exp-acc-purchase') +
            accField('ap_acc', 'exp-acc-ap') +
            accField('vat_input_acc', 'exp-acc-vat-in') +
            '</div></div></section>';

        return (
            '<div class="exp-modal-body">' +
            rail +
            '<main class="exp-scroll" id="exp-scroll">' +
            step1 +
            step2 +
            step3 +
            accmap +
            toggle +
            advanced +
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
            '<button class="exp-secondary" id="exp-cancel">' +
            _esc(_t('exp-cancel')) +
            '</button><button class="exp-primary" id="exp-done" disabled>' +
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
                gen.className = 'exp-secondary exp-danger';
            }
        } else if (S.hasKey) {
            if (cb) cb.style.display = 'grid';
            if (val) val.textContent = masked;
            if (eye) eye.style.display = 'none';
            if (copy) copy.style.display = 'none';
            if (note) note.textContent = t('exp-key-set-once');
            if (gen) {
                gen.textContent = t('exp-key-reset');
                gen.className = 'exp-secondary exp-danger';
            }
        } else {
            if (cb) cb.style.display = 'none';
            if (gen) {
                gen.textContent = t('exp-gen-token');
                gen.className = 'exp-primary';
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
