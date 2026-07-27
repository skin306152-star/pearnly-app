/*
 * Pearnly AI · ai-fail-render.js · 失败态出路(哪一步失败 / 为什么 / 现在能做什么)
 *
 * 全站失败卡共用一份判读:后端错误码 + HTTP 状态 → 一句人话原因 + 至多一个下一步。
 * 「至多一个」是刻意的:调用方通常自己已经有重试入口(开单按钮回可点、失败批「重传」),
 * 这里只补它给不出的那种出路(去充值),不再摆第二个按钮让人挑。
 *
 * 错误契约取自 ai-api.js handleResponse 与 ai-api-upload.js parseUploadError 抛出的
 * Error(code/status);两者皆缺 = 请求根本没出去(fetch TypeError / xhr onerror)。
 * 不碰 DOM,只拼字符串;UMD 同 ai-billing-render.js 先例,
 * tests/unit/test_ai_fail_render.py 用真 node 跑本文件断言。
 */
(function (root) {
    'use strict';

    // 余额不足的出路落点:设置页计费区(B5 的 OCR 余额/充值面板)。?focus=billing 由
    // ai-router.js 解析、ai-settings.js 落地时滚过去——只送到设置页不够,得直接看见充值。
    var TOPUP_HASH = '#/settings?focus=billing';

    // 浏览器走 at()(ai-i18n.js 必先加载);node(单测)无词典 → 回退原 key,
    // 让"映射到了哪条文案"在 node 里可断言(同 ai-billing-render.js 的 t() 先例)。
    function t(k) {
        return typeof root.at === 'function' ? root.at(k) : k;
    }

    function esc(s) {
        if (root && root.AI && root.AI.state && typeof root.AI.state.esc === 'function') {
            return root.AI.state.esc(s);
        }
        return String(s == null ? '' : s);
    }

    // 已有 err_* 词条的错误码走 ai-api.js 的既有映射,不在这里抄第二份码表。
    function mappedKey(code) {
        if (root && root.AI && root.AI.api && typeof root.AI.api.mapApiErrorKey === 'function') {
            return root.AI.api.mapApiErrorKey(code);
        }
        return code ? 'err_' + String(code).replace(/\./g, '_') : 'err_generic';
    }

    /**
     * (code, status) → { reasonKey, actionKey, href }。actionKey/href 为 null =
     * 这一类失败没有"换个地方点"的出路,原地重试就是全部出路。
     *
     * insufficient_balance 是全站计费闸的统一码(services/billing/account_status.py
     * 单一事实源,recon/vat_excel/knowledge 等端点以 402 + detail.code 出线)。
     *
     * 休眠分支,别当它在工作:本模块的两个调用点当前都不可能收到 402。
     * routes/workorder_routes.py::create_order 只有鉴权+归属校验(开单本身永远不计费);
     * ::add_materials 只有 413/422,OCR 计费发生在 _auto_advance 的后台续跑里,不以上传
     * 响应的形式回到前端。余额耗尽时收料页得到的仍是后台 stuck / 转人工。契约先接好,
     * 收料真上计费闸的那天不用再改前端 —— 但在那之前,任何「去充值出路已生效」的说法都不成立。
     * 闸:tests/unit/test_ai_fail_render.py::DormantTopupBranchTests(收料上计费闸即报红,
     * 提醒把这段注释和 E2E 的说明一起改掉)。
     */
    function failureView(code, status) {
        var c = code == null ? '' : String(code);
        var s = Number(status) || 0;
        if (c === 'insufficient_balance' || s === 402) {
            return { reasonKey: 'fail_credits', actionKey: 'fail_topup_btn', href: TOPUP_HASH };
        }
        if (s === 401) return { reasonKey: 'fail_auth', actionKey: null, href: null };
        if (s >= 500) return { reasonKey: 'fail_server', actionKey: null, href: null };
        if (!c && !s) return { reasonKey: 'fail_network', actionKey: null, href: null };
        // 越权/闸关/单已删都收在这个码上(routes/workorder_routes.py 不泄漏存在性),
        // 对用户是同一件事:这条路你现在走不了,回工作台重新进。
        if (c === 'workorder.not_found') {
            return { reasonKey: 'fail_no_access', actionKey: null, href: null };
        }
        return { reasonKey: mappedKey(c), actionKey: null, href: null };
    }

    // 这次失败是不是「某一件料的问题」。只有 422 是(IN-0a 两段法:整批 422 时该批零落盘,
    // 拿掉后端点名的那件重传其余才安全)。别的状态码也可能带结构化 detail —— 计费闸的 402
    // 就是 {code:'insufficient_balance'} —— 只看 detail.code 就分派会把整批当成一件件坏料
    // 逐个剥,用户收获一串莫名其妙的拒收,真原因反而没人说。
    function isPerFileReject(status, detail) {
        return Number(status) === 422 && !!detail && typeof detail === 'object' && !!detail.code;
    }

    // 原因行:徽章点名哪一步失败,后面接为什么。role=alert 让读屏器在原地播报,
    // 不是悄悄改一段 DOM(静默失败的另一种形态)。
    //
    // reasonKey 可由调用方覆盖:失败发生在「已经做成的一步之后」时,(code,status) 推出来的
    // 那句「服务器出错了」是误导——用户要知道的是那件事已经成了、只是没刷出来。
    function reasonHtml(stepKey, code, status, reasonKey) {
        return (
            '<p class="needs-sub" role="alert"><span class="st-badge st-err">' +
            esc(t(stepKey)) +
            '</span> ' +
            esc(t(reasonKey || failureView(code, status).reasonKey)) +
            '</p>'
        );
    }

    // 出路按钮:只有"换个地方点才解得开"的失败才出,其余返空串(调用方自己的重试按钮就够)。
    function actionHtml(code, status) {
        var v = failureView(code, status);
        if (!v.actionKey || !v.href) return '';
        return '<a class="btn pri" href="' + esc(v.href) + '">' + esc(t(v.actionKey)) + '</a>';
    }

    // 原因 + 出路的成套版:给本来什么都没有的失败点用(如开单失败),调用方直接 innerHTML。
    // opts.reasonKey 覆盖原因时不出出路按钮:覆盖的场景(前一步已成功)出路写在文案里,
    // 再挂一个按 (code,status) 算出来的按钮只会指错地方。
    function noteHtml(stepKey, code, status, opts) {
        var reasonKey = (opts || {}).reasonKey;
        var action = reasonKey ? '' : actionHtml(code, status);
        return (
            reasonHtml(stepKey, code, status, reasonKey) +
            (action ? '<div class="needs-paths">' + action + '</div>' : '')
        );
    }

    var api = {
        TOPUP_HASH: TOPUP_HASH,
        failureView: failureView,
        isPerFileReject: isPerFileReject,
        reasonHtml: reasonHtml,
        actionHtml: actionHtml,
        noteHtml: noteHtml,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.failRender = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
