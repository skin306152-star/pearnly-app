/*
 * Pearnly AI · ai-review-queue.js · 人审队列(W3)的过滤/分级/裁决 payload 纯函数
 *
 * 零 DOM、零网络——同 ai-board.js/ai-format.js 先例:浏览器挂 window.AI.reviewQueue,
 * node(测试)走 module.exports。真正的 UI 编排(键盘流/乐观回滚/轮询)在 ai-review.js,
 * 那部分逻辑离不开 DOM/fetch 时序,不适合脱管单测,拆开让「算得对不对」能被机器守住。
 */
(function (root) {
    'use strict';

    var PURCHASE_KIND = 'purchase_invoice';

    // 契约 §1.1:队列 = flagged.filter(kind === 'purchase_invoice')。后端已按 created_at
    // 出稳定序,这里只过滤不重排。
    function filterPurchaseQueue(flagged) {
        return (Array.isArray(flagged) ? flagged : []).filter(function (it) {
            return it && it.kind === PURCHASE_KIND;
        });
    }

    // flag_reason → 红/黄分级(契约 §1.1):数学不自洽 / 整张 OCR 读失败 = 红(crit);
    // 置信度/校验存疑 = 黄(warn)。未知原因保守当红——没把握的异常不该被淡化成黄。
    // 冒号前缀处理同 flagReasonKey:先取冒号前段再比对,两处「怎么拆 flag_reason」写法统一。
    var _WARN_REASONS = { ocr_low_confidence: true, ocr_validation_warning: true };
    function flagSeverity(reason) {
        var head = String(reason || '').split(':')[0];
        return _WARN_REASONS[head] ? 'warn' : 'crit';
    }

    // flag_reason → 人话 i18n key(契约:兜底不许把后端原始英文键糊脸给用户)。
    // 后端全集里 ocr_low_confidence/ocr_error 带冒号后缀(band/异常名),先取冒号前段
    // 再映射;未知/空原因返回 null,调用方据此诚实回退到原始键(总比编个假人话强)。
    var _FLAG_REASON_KEY = {
        amount_math_fail: 'rv_flag_math_fail',
        ocr_validation_warning: 'rv_flag_validation',
        ocr_low_confidence: 'rv_flag_low_conf',
        ocr_error: 'rv_flag_ocr_error',
    };
    function flagReasonKey(reason) {
        var r = String(reason || '');
        if (!r) return null;
        return _FLAG_REASON_KEY[r.split(':')[0]] || null;
    }

    // 人工 VAT 输入串 → 能否解成钱数的前置校验(真正的 Decimal 换算留给后端
    // reconcile_gates,前端绝不重算钱)。去千分位空白,只认「整数.最多两位小数」。
    // 解不出返回 null,调用方据此就地报错、不发请求。
    function parseVat(raw) {
        var s = String(raw == null ? '' : raw)
            .trim()
            .replace(/,/g, '');
        if (!s || !/^-?\d+(\.\d{1,2})?$/.test(s)) return null;
        return s;
    }

    // 一次按键(A 采纳 / E 改数 / X 剔除)→ POST /decisions 的 body(契约 §2)。
    // recalc 缺合法 VAT 时返回 null——调用方不发请求,就地提示「请填有效 VAT」。
    function buildDecisionPayload(itemId, action, vatRaw) {
        if (action === 'accept') return { item_id: itemId, decision: 'face_value' };
        if (action === 'exclude') return { item_id: itemId, decision: 'exclude' };
        if (action === 'recalc') {
            var vat = parseVat(vatRaw);
            if (!vat) return null;
            return { item_id: itemId, decision: 'recalc', values: { vat: vat } };
        }
        return null;
    }

    // 该票最新裁决({decision, values, actor, at} | null)→ chip 的 i18n key。
    // 未裁决 / 未知裁决值一律返回 null(状态诚实:不认识就不硬贴一个终态标签)。
    var _CHIP_KEY = {
        face_value: 'rv_chip_accepted',
        recalc: 'rv_chip_recalc',
        exclude: 'rv_chip_excluded',
    };
    function decisionChipKey(decision) {
        if (!decision || !decision.decision) return null;
        return _CHIP_KEY[decision.decision] || null;
    }

    // file_ref(服务器本地绝对路径,盘符/正反斜杠都可能出现)→ 给人看的文件名。
    function fileName(fileRef) {
        var s = String(fileRef || '');
        var parts = s.split(/[\\/]/);
        return parts[parts.length - 1] || s;
    }

    var api = {
        PURCHASE_KIND: PURCHASE_KIND,
        filterPurchaseQueue: filterPurchaseQueue,
        flagSeverity: flagSeverity,
        flagReasonKey: flagReasonKey,
        parseVat: parseVat,
        buildDecisionPayload: buildDecisionPayload,
        decisionChipKey: decisionChipKey,
        fileName: fileName,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.reviewQueue = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
