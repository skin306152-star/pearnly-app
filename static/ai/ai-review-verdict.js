/*
 * Pearnly AI · ai-review-verdict.js · 判据人话渲染 + 批量建议裁决(MC1-b2)纯函数
 *
 * 零 DOM/网络(同 ai-review-queue.js 先例):浏览器挂 window.AI.reviewVerdict,node
 * (测试)走 module.exports。confidence 直接读后端 verdict_hint.confidence(services/
 * workorder/verdict.py 单一事实源,前端不重算置信度,只做展示 class/i18n key 映射)。
 *
 * 批量建议(「全部按建议处理」的建议动作)是本文件独有的前端业务决策——backend 只给
 * 判据人话+置信度,不给"批量该套哪个裁决"。表随 verdict.py 的 narrative_key 命名空间
 * 手工对齐:只给高/中置信度且有明确安全默认动作的 flag_reason 配建议,其余(低置信/
 * 自身冲突)一律不给建议,逼人工逐张审——置信度不是装饰,直接决定这组能不能一键批量。
 */
(function (root) {
    'use strict';

    var CONFIDENCE_CHIP_CLASS = { high: 'g', mid: 'w', low: 'b' };
    var CONFIDENCE_ORDER = { high: 2, mid: 1, low: 0 };

    function confidenceChipClass(confidence) {
        return CONFIDENCE_CHIP_CLASS[confidence] || 'b';
    }

    function confidenceLabelKey(confidence) {
        return CONFIDENCE_ORDER[confidence] != null ? 'riq_conf_' + confidence : 'riq_conf_low';
    }

    // 判据人话:narrative_key 有值 → {key, vars} 交给 at() 渲染;未识别(narrative_key
    // 为 null,verdict.hint() 对未知 flag_reason 的诚实回退)→ {key:null, fallbackText}
    // 退回原始 flag_reason(总比编个假人话强,与后端 verdict.py 顶注同一约定)。vars 逐
    // 键把 None/undefined 清成空串——verdict.py 的 params 构造器(如 _seller_params 的
    // vendor)有些字段现阶段 OCR 读不出恒为 None,at() 的 replace 不做 falsy 判断,
    // null 会被 String() 成字面 "null" 糊脸给用户(同 pool_answer_raw 的 `|| ''` 惯例)。
    function narrativeOf(hint, flagReason) {
        hint = hint || {};
        if (hint.narrative_key) return { key: hint.narrative_key, vars: sanitizeVars(hint.params) };
        return { key: null, fallbackText: flagReason || '' };
    }

    function sanitizeVars(params) {
        var out = {};
        Object.keys(params || {}).forEach(function (k) {
            var v = params[k];
            out[k] = v == null ? '' : v;
        });
        return out;
    }

    // flag_reason 冒号前缀 → 批量「全部按建议处理」该套的裁决模板(不含 item_id,调用方
    // 拼上)。随 services/workorder/verdict.py 的 _MAP 命名空间手工对齐(前端无法 import
    // python):只给高/中置信度且有安全默认动作的三类配建议。
    var _BULK_TEMPLATES = {
        // 税号精确判本方销项(高置信)→ 建议确认为销项。
        sales_direction_unhandled: { decision: 'assign_kind', kind: 'sales_doc' },
        // 已自动判本方销项待复核(中置信)→ 建议确认原判。
        sales_doc_review: { decision: 'assign_kind', kind: 'sales_doc' },
        // 指纹精确命中复件(高置信)→ 建议剔除。
        duplicate_of: { decision: 'exclude' },
    };

    function bulkDecisionTemplate(flagReason) {
        var head = String(flagReason || '').split(':')[0];
        return _BULK_TEMPLATES[head] || null;
    }

    // 一组 flagged 件能否「全部按建议处理」:该 flag_reason 有建议模板,且组内每张的
    // verdict_hint.confidence 都不是 low(低置信的个别件混进同组也不放行整组批量,
    // 保守优先——宁可多一次人工逐张审,不多一次误批)。
    function groupCanBulk(items) {
        var template = items.length ? bulkDecisionTemplate(items[0].flag_reason) : null;
        if (!template) return false;
        return items.every(function (it) {
            var c = it.verdict_hint && it.verdict_hint.confidence;
            return c === 'high' || c === 'mid';
        });
    }

    var api = {
        confidenceChipClass: confidenceChipClass,
        confidenceLabelKey: confidenceLabelKey,
        narrativeOf: narrativeOf,
        bulkDecisionTemplate: bulkDecisionTemplate,
        groupCanBulk: groupCanBulk,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.reviewVerdict = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
