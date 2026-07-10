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
    // 后端判不出进/销方向的两类票(sort.bin_ocr_fields · kind=unknown):锚点全然不明
    // (direction_ambiguous),或自家==卖方=疑似本方销项票(sales_direction_unhandled)。
    // 随 services/workorder/decisions.py 的 DIRECTION_PREFIXES 同步(前端无法 import,手工对齐)。
    var DIRECTION_PREFIXES = ['direction_ambiguous', 'sales_direction_unhandled'];

    // 方向不明票必须人工定向,否则进项被静默漏掉(G1/G1R2 黑洞)。卡上切换成方向裁决三键,
    // 不走 A/E/X。按 flag_reason 前缀判(两类同一套 P/S/X 定向流程)。
    function isDirectionTicket(it) {
        if (!it) return false;
        var reason = String(it.flag_reason || '');
        return DIRECTION_PREFIXES.some(function (p) {
            return reason.indexOf(p) === 0;
        });
    }

    // 契约 §1.1:队列 = flagged 里的进项票 + 方向不明票(后者收编进队列由人定向,
    // 不再隐形)。后端已按 created_at 出稳定序,这里只过滤不重排。
    function filterPurchaseQueue(flagged) {
        return (Array.isArray(flagged) ? flagged : []).filter(function (it) {
            return it && (it.kind === PURCHASE_KIND || isDirectionTicket(it));
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
        direction_ambiguous: 'rv_flag_direction',
        sales_direction_unhandled: 'rv_flag_sales_direction',
    };
    function flagReasonKey(reason) {
        var r = String(reason || '');
        if (!r) return null;
        return _FLAG_REASON_KEY[r.split(':')[0]] || null;
    }

    // 人工 VAT 输入串 → 能否解成钱数的前置校验(真正的 Decimal 换算留给后端
    // reconcile_gates,前端绝不重算钱)。去千分位空白,只认「整数.最多两位小数」,
    // 认负号(recalc 改数可能是冲正)。共享解析在 ai-format.js(同 ai-intake-render.js
    // 的 parseAmount 先例,两处曾各自写同一条正则)。
    function parseVat(raw) {
        return root.AI.format.parseAmount(raw, true);
    }

    // 方向裁决三键(进项 P / 销项 S / 非税 X)→ 后端 assign_kind 的裁定 kind。方向票模式下
    // X 语义从「剔除」切换成「非税票」(卡上明示),不与金额票的 A/E/X 混。
    var _ASSIGN_KIND = {
        assign_purchase: 'purchase_invoice',
        assign_sales: 'sales_doc',
        assign_nontax: 'non_tax',
    };

    // 一次按键 → POST /decisions 的 body(契约 §2)。金额票:A 采纳 / E 改数 / X 剔除;
    // 方向票:P 进项 / S 销项 / X 非税(assign_kind)。recalc 缺合法 VAT 时返回 null——调用方
    // 不发请求,就地提示「请填有效 VAT」。
    function buildDecisionPayload(itemId, action, vatRaw) {
        if (action === 'accept') return { item_id: itemId, decision: 'face_value' };
        if (action === 'exclude') return { item_id: itemId, decision: 'exclude' };
        if (_ASSIGN_KIND[action]) {
            return { item_id: itemId, decision: 'assign_kind', kind: _ASSIGN_KIND[action] };
        }
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
    // 方向裁决落定后的 chip:按裁定 kind 显进项/销项/非税(assign_kind 的裁定方向)。
    var _ASSIGN_CHIP_KEY = {
        purchase_invoice: 'rv_chip_dir_purchase',
        sales_doc: 'rv_chip_dir_sales',
        non_tax: 'rv_chip_dir_nontax',
    };
    function decisionChipKey(decision) {
        if (!decision || !decision.decision) return null;
        if (decision.decision === 'assign_kind') return _ASSIGN_CHIP_KEY[decision.kind] || null;
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
        isDirectionTicket: isDirectionTicket,
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
