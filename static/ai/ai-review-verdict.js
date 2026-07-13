/*
 * Pearnly AI · ai-review-verdict.js · 判据人话渲染 + 批量建议裁决(MC1-b2)纯函数
 *
 * 零 DOM/网络(同 ai-review-queue.js 先例):浏览器挂 window.AI.reviewVerdict,node
 * (测试)走 module.exports。confidence/severity/suggested_decision 全直接读后端
 * verdict_hint(services/workorder/verdict.py 的 _MAP 单一事实源,前端不重算政策,只做
 * 展示 class/i18n key 映射 + 组级批量放行判定)。MC2-A3 前本文件曾自持一张 _BULK_TEMPLATES
 * 政策副本,已删——建议裁决随 verdict_hint.suggested_decision 下发,前端纯渲染。
 *
 * 置信度不是装饰:只有后端给了安全默认动作(suggested_decision)且组内每张都非 low 置信,
 * 才放行「全部按建议处理」;有一张 low 混入即禁整组批量,逼人工逐张审。
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

    // 批量「全部按建议处理」该套的裁决模板(不含 item_id,调用方拼上)= 后端下发的
    // verdict_hint.suggested_decision(政策单一事实源在 services/workorder/verdict.py 的 _MAP)。
    // null = 该件无安全默认动作,禁一键批量(前端不再持 _BULK_TEMPLATES 副本)。
    function bulkDecisionTemplate(item) {
        return (item && item.verdict_hint && item.verdict_hint.suggested_decision) || null;
    }

    // 一组 flagged 件能否「全部按建议处理」:组内首张有后端建议动作,且每张的
    // verdict_hint.confidence 都不是 low(低置信的个别件混进同组也不放行整组批量,
    // 保守优先——宁可多一次人工逐张审,不多一次误批)。
    function groupCanBulk(items) {
        if (!items.length || !bulkDecisionTemplate(items[0])) return false;
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
