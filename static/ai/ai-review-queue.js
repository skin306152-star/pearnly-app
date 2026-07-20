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

    // 自动判本方销项票(kind=sales_doc · MC1-c.1):flagged 留人工过目,卡上走同一套 P/S/X
    // 定向键(默认按 S 确认销项;客户拍错票可 P 改进项 / X 非税)。随 decisions.SALES_DOC 同步。
    var SALES_DOC_KIND = 'sales_doc';

    // 方向不明票必须人工定向,否则进项被静默漏掉(G1/G1R2 黑洞)。本方销项票 sales_doc 也走同一套
    // P/S/X 卡(留人工过目/一键确认)。卡上切换成方向裁决三键,不走 A/E/X。
    function isDirectionTicket(it) {
        if (!it) return false;
        if (it.kind === SALES_DOC_KIND) return true;
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
        sales_doc_review: 'rv_flag_sales_doc',
        discount_inferred: 'rv_flag_discount_inferred',
        totals_rescued: 'rv_flag_totals_rescued',
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
    // 不发请求,就地提示格式错误。fullValues 传入时统一提交票号、日期及三项金额；省略时
    // 保留旧调用方的 VAT-only 兼容路径。VAT 必填
    // (reconcile_gates.py 的权威校验底线);net/grand_total 留空则不带这两个键,后端按票面
    // 等式自行兜底(reconcile_gates.py L64-66:net 缺省从 vat 反推,grand 缺省 = net+vat)。
    function buildDecisionPayload(itemId, action, vatRaw, fullValues) {
        if (action === 'accept') return { item_id: itemId, decision: 'face_value' };
        if (action === 'exclude') return { item_id: itemId, decision: 'exclude' };
        if (_ASSIGN_KIND[action]) {
            return { item_id: itemId, decision: 'assign_kind', kind: _ASSIGN_KIND[action] };
        }
        if (action === 'recalc') {
            if (fullValues) {
                var v = parseVat(fullValues.vat);
                if (!v) return null;
                var values = { vat: v };
                var net = parseVat(fullValues.net);
                if (net) values.net = net;
                var grand = parseVat(fullValues.grand);
                if (grand) values.grand_total = grand;
                if (fullValues.invoice_number != null) {
                    values.invoice_number = String(fullValues.invoice_number).trim();
                }
                if (fullValues.invoice_date != null) {
                    var invoiceDate = String(fullValues.invoice_date).trim();
                    if (invoiceDate) {
                        if (!/^\d{4}-\d{2}-\d{2}$/.test(invoiceDate)) return null;
                        // 年份 >= 2400 只可能是佛历(2400 BE = 1857 AD)。这里收的是公历,
                        // 放行会让佛历年落进 DATE 列,推 ERP 时再加 543 直接跑飞。
                        if (parseInt(invoiceDate.slice(0, 4), 10) >= 2400) return null;
                        var parsedDate = new Date(invoiceDate + 'T00:00:00Z');
                        if (
                            Number.isNaN(parsedDate.getTime()) ||
                            parsedDate.toISOString().slice(0, 10) !== invoiceDate
                        )
                            return null;
                    }
                    values.invoice_date = invoiceDate;
                }
                return { item_id: itemId, decision: 'recalc', values: values };
            }
            var vat = parseVat(vatRaw);
            if (!vat) return null;
            return { item_id: itemId, decision: 'recalc', values: { vat: vat } };
        }
        return null;
    }

    // 该票是否已有裁决(latest-wins:session-local 乐观态优先于后端已落库的裁决)。
    // J-C 未判/已判两分与计数器都靠它判断,单一事实源不各写一套 truthy 判断。
    function isDecided(entry, local) {
        return !!((local && local.decision) || (entry && entry.decision));
    }

    // 未判/已判两分(J-C · 客户页队列记忆修复 + 收件箱异常票据折叠共用):localByItem 缺省
    // 只用 entry.decision(后端已落库的最新裁决)——客户页队列 mount 时会话尚无 local,分流
    // 只算一次把主聚焦流收窄到真正待办的票(本次会话新裁决靠 undecidedCount 动态扣减计数器,
    // 不改数组结构,详见 ai-review.js::revisitDecided);收件箱每次渲染都传 session-local
    // (ai-review-inbox-render.js::groupHtml),两处共用同一份判断,不各写一套。
    function splitByDecision(queue, localByItem) {
        localByItem = localByItem || {};
        var undecided = [],
            decided = [];
        (queue || []).forEach(function (e) {
            (isDecided(e, localByItem[e.item_id]) ? decided : undecided).push(e);
        });
        return { undecided: undecided, decided: decided };
    }

    // 三段计数器的待处理数(J-C):localByItem 是当前会话乐观态(item_id -> {decision}),
    // 与 isDecided 同一份判断口径,不重复写一套 truthy 逻辑。
    function undecidedCount(queue, localByItem) {
        localByItem = localByItem || {};
        return (queue || []).filter(function (e) {
            return !isDecided(e, localByItem[e.item_id]);
        }).length;
    }

    // J-A 建议值消费(J-C):order_detail.alerts 里按 item_id 取确定性读数解歧建议(J-13,
    // 每 item_id 至多一条)。找不到返回 null——调用方据此诚实回退现状单字段改数表单。
    function suggestionForItem(alerts, itemId) {
        return (
            (alerts || []).filter(function (a) {
                return a.type === 'amount_read_suggested' && a.item_id === itemId;
            })[0] || null
        );
    }

    // 改数(E)态统一生成五字段初值。金额有确定性建议时优先建议，改判时优先上次人工值；
    // 票号和日期回落 OCR 原值。纯函数,编排层不重复判断。
    function editStartValues(alerts, entry, priorDecision) {
        var suggestion = suggestionForItem(alerts, entry.item_id);
        var priorVat =
            priorDecision &&
            priorDecision.decision === 'recalc' &&
            priorDecision.values &&
            priorDecision.values.vat;
        var read = entry.ocr_read || {};
        var priorValues =
            (priorDecision && priorDecision.decision === 'recalc' && priorDecision.values) || {};
        var suggested = suggestion
            ? suggestion.suggestion
            : { net: read.subtotal, vat: read.vat, grand: read.total_amount };
        return {
            suggestion: suggestion,
            editValue: null,
            suggestValues: {
                net: priorValues.net || suggested.net || '',
                vat: priorVat || suggested.vat || '',
                grand: priorValues.grand_total || suggested.grand || '',
                invoice_number:
                    priorValues.invoice_number != null
                        ? priorValues.invoice_number
                        : read.invoice_number || '',
                invoice_date:
                    priorValues.invoice_date != null
                        ? priorValues.invoice_date
                        : read.invoice_date || '',
            },
        };
    }

    // 批量模板的 decision 词 → decide() 用的 ui action 词(ai-review.js::_stateForAction
    // 复用同一张映射,不为批量另写一套终态标签)。bulkDecisionTemplate 只可能产出
    // face_value/exclude/recalc(verdict.py 的 suggested_decision 策略),映射外无兜底——
    // 真出现未知词宁可显式 undefined 暴露,不静默套错标签。
    var _DECISION_TO_ACTION = { face_value: 'accept', exclude: 'exclude', recalc: 'recalc' };
    function actionOfDecision(template) {
        return template && _DECISION_TO_ACTION[template.decision];
    }

    // 改数裁决值 vs OCR 原读数比对(J-C · fieldRows「最新裁决值 + 已人工修正」徽标用):
    // effectiveDecision.values 里有该键且与原读数不同 → 已人工修正;没有该键(如仍是老单
    // 字段裁决只填了 vat)→ 诚实回落原读数,不假装其余字段被改过。
    function decidedValue(effectiveDecision, key, fallback) {
        var values =
            effectiveDecision &&
            effectiveDecision.decision === 'recalc' &&
            effectiveDecision.values;
        var value = values && values[key] != null ? values[key] : fallback;
        var corrected = !!(
            values &&
            values[key] != null &&
            String(values[key]) !== String(fallback)
        );
        return { value: value, corrected: corrected };
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

    // D2-S9:「推 LINE 待问」按票面已知信息猜一个默认 question_type,会计仍可在选择面板
    // 改选——方向不明票天然该问买/卖;数学不自洽票天然该问金额;其余保守落 freeform
    // (不替会计瞎猜「该不该计这月」,那是 drop 专属场景,没有信号不硬凑)。
    function suggestQuestionType(entry) {
        if (isDirectionTicket(entry)) return 'direction';
        var reason = String((entry && entry.flag_reason) || '').split(':')[0];
        if (reason === 'amount_math_fail') return 'amount';
        return 'freeform';
    }

    // 暂挂请求体(不含 work_order_id——那是调用方已知的当前工单,同 buildDecisionPayload
    // 不带 order id 一个道理)。question_payload 只喂票面已有的原始读数,不代会计填空。
    function buildStagePayload(entry, questionType) {
        if (!entry) return null;
        var read = entry.ocr_read || {};
        return {
            item_id: entry.item_id,
            question_type: questionType,
            payload: {
                supplier: read.seller_tax || '',
                invno: read.invoice_number || '',
                amount: read.total_amount || read.vat || '',
                note: entry.flag_reason || '',
            },
        };
    }

    function blockedInfo(detail, hasQueue) {
        detail = detail || {};
        var needs = Array.isArray(detail.needs) ? detail.needs : [];
        var reasons = Array.isArray(detail.blocked_reasons) ? detail.blocked_reasons : [];
        if (!needs.length && !reasons.length && !hasQueue) return null;
        return {
            reasons: reasons.concat(needs),
            needs: needs,
            hasQueue: !!hasQueue,
            system: reasons.length > 0 && !needs.length && !hasQueue,
        };
    }

    var api = {
        PURCHASE_KIND: PURCHASE_KIND,
        isDirectionTicket: isDirectionTicket,
        filterPurchaseQueue: filterPurchaseQueue,
        flagReasonKey: flagReasonKey,
        parseVat: parseVat,
        buildDecisionPayload: buildDecisionPayload,
        decisionChipKey: decisionChipKey,
        fileName: fileName,
        suggestQuestionType: suggestQuestionType,
        buildStagePayload: buildStagePayload,
        isDecided: isDecided,
        splitByDecision: splitByDecision,
        undecidedCount: undecidedCount,
        suggestionForItem: suggestionForItem,
        editStartValues: editStartValues,
        actionOfDecision: actionOfDecision,
        decidedValue: decidedValue,
        blockedInfo: blockedInfo,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.reviewQueue = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
