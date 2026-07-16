/*
 * Pearnly AI · ai-desk-render.js · FD-0d 总台(#/desk)纯逻辑 + 消息卡 HTML 拼装
 *
 * 消息流不建聊天表(施工总册 §2.2):流内容由合同状态服务端重建,本文件只管「一份合同
 * 现在该出哪张卡」的判定(deriveCard,纯函数)+ 六种系统卡里 FD-0 开的四种(盘点/合同/
 * 进度/拒绝)+ 降级卡的 HTML 拼装。输入区/手动开单面板拆到 ai-desk-compose-render.js
 * (单文件 <500 行铁律,同 ai-profile-render.js/ai-profile-panels-render.js 先例)。
 *
 * intent 的人话名/需料/交付物是 services/front_desk/intents.py 闭集的前端镜像(该文件
 * 是唯一事实源,浏览器不能 import python,新增/开放意图必须两处同步——同 ai-format.js
 * STATUS_MAP 镜像 engine.py ALL_STATUSES 的先例)。
 *
 * 上半段(deriveCard/needCoverage/confirmReady/INTENT_META/ENABLED_INTENT_IDS)零 DOM
 * 依赖,node(tests/unit/test_ai_pure_modules.py)直接 require 断言;下半段 HTML 拼装
 * 依赖 at()/AI.state/AI.format/AI.board,只在浏览器根挂载——同 ai-payroll-render.js
 * 的双段先例。
 */
(function (root) {
    'use strict';

    // 六种系统卡(施工总册 §2.3)FD-0 只做前四种 + 降级卡;result 卡是 FD-1 才有的交付物
    // 呈现,本批不产出该 kind。
    var TERMINAL_PROGRESS = ['confirmed', 'executing', 'delivered', 'archive', 'archived'];

    // 前门意图闭集的前端镜像(services/front_desk/intents.py 单一事实源)。needs/
    // deliverables 存 i18n key,合同卡/拒绝卡按 key 渲染人话。ENABLED_INTENT_IDS 与
    // Python intents.enabled_ids() 同步——首发只开 monthly_vat,其余在册未开放。
    var INTENT_META = {
        monthly_vat: {
            nameKey: 'fd_intent_name_monthly_vat',
            needs: ['fd_need_purchase_invoices', 'fd_need_sales_summary', 'fd_need_bank_statement'],
            deliverables: ['fd_deliver_pp30_draft', 'fd_deliver_workpaper'],
        },
        digitize: {
            nameKey: 'fd_intent_name_digitize',
            needs: ['fd_need_raw_files'],
            deliverables: ['fd_deliver_organized_excel'],
        },
        vat_report_check: {
            nameKey: 'fd_intent_name_vat_report_check',
            needs: ['fd_need_sales_vat_report'],
            deliverables: ['fd_deliver_report_check_result'],
        },
        payroll_filing: {
            nameKey: 'fd_intent_name_payroll_filing',
            needs: ['fd_need_payroll_sheet'],
            deliverables: ['fd_deliver_pnd1_draft'],
        },
        bank_match: {
            nameKey: 'fd_intent_name_bank_match',
            needs: ['fd_need_bank_statement', 'fd_need_purchase_invoices'],
            deliverables: ['fd_deliver_match_result', 'fd_deliver_missing_slips'],
        },
    };
    var ENABLED_INTENT_IDS = ['monthly_vat'];

    // 需料 key → 盘点分组(services/front_desk/inventory.py 的展示分组)的粗对照:零成本
    // 信号本就是「像不像」,这里只给合同卡一个 ✓/✗ 提示,不是权威判定(真正的缺料判据
    // 在工单 classify/reconcile 步)。
    var NEED_GROUP_MAP = {
        fd_need_purchase_invoices: ['image', 'pdf_unidentified'],
        fd_need_sales_summary: ['spreadsheet'],
        fd_need_bank_statement: ['bank_statement'],
        fd_need_raw_files: [
            'image',
            'pdf_unidentified',
            'spreadsheet',
            'gl_ledger',
            'bank_statement',
        ],
        fd_need_sales_vat_report: ['spreadsheet', 'pdf_unidentified'],
        fd_need_payroll_sheet: ['spreadsheet'],
    };

    function needCoverage(needKeys, inventoryGroups) {
        var present = {};
        (inventoryGroups || []).forEach(function (g) {
            if (g && g.count > 0) present[g.group] = true;
        });
        return (needKeys || []).map(function (need) {
            var groups = NEED_GROUP_MAP[need] || [];
            var satisfied = groups.some(function (g) {
                return !!present[g];
            });
            return { need: need, satisfied: satisfied };
        });
    }

    // 确认开工可点的前置校验(账套红线:三值都要有,且意图须为已开放闭集)——按钮
    // disabled 态与真正提交前的二次校验共用同一份判据,不各写一套。
    function confirmReady(selection) {
        var sel = selection || {};
        return !!(
            sel.clientId &&
            sel.period &&
            sel.intent &&
            ENABLED_INTENT_IDS.indexOf(sel.intent) >= 0
        );
    }

    // 一份合同(public_view · 含 FD-0d 补的 brain_suggestion)+ 本次会话内的即时结果
    // (liveExtra:刚 create/interpret 拿到的 inventory/suggestion/degraded,尚未落库或
    // 落库后不下发)→ 判定当前该出哪张卡。degraded 只活在当次会话(不持久化,刷新后
    // 该合同退回按 brain_suggestion 或盘点判定,诚实反映"降级是临时状态")。
    function deriveCard(contract, liveExtra) {
        contract = contract || {};
        liveExtra = liveExtra || {};
        if (TERMINAL_PROGRESS.indexOf(contract.status) >= 0) {
            return { kind: 'progress', contract: contract };
        }
        if (contract.status === 'rejected') {
            return { kind: 'dismissed', contract: contract };
        }
        if (liveExtra.degraded) {
            return { kind: 'degraded', contract: contract, reason: liveExtra.reason || null };
        }
        var suggestion = liveExtra.suggestion || contract.brain_suggestion;
        if (suggestion && suggestion.intent) {
            if (suggestion.intent === 'unsupported' || !INTENT_META[suggestion.intent]) {
                return { kind: 'rejected', contract: contract };
            }
            return { kind: 'contract', contract: contract, suggestion: suggestion };
        }
        var invTotal = liveExtra.inventory && liveExtra.inventory.total;
        var fileCount = Array.isArray(contract.files) ? contract.files.length : 0;
        if ((invTotal && invTotal > 0) || fileCount > 0) {
            return {
                kind: 'inventory',
                contract: contract,
                inventory: liveExtra.inventory || null,
                fileCount: fileCount,
            };
        }
        return { kind: 'empty', contract: contract };
    }

    var pure = {
        INTENT_META: INTENT_META,
        ENABLED_INTENT_IDS: ENABLED_INTENT_IDS,
        NEED_GROUP_MAP: NEED_GROUP_MAP,
        needCoverage: needCoverage,
        confirmReady: confirmReady,
        deriveCard: deriveCard,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.format/AI.board,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    var GROUP_LABEL_KEYS = {
        image: 'fd_group_image',
        bank_statement: 'fd_group_bank_statement',
        spreadsheet: 'fd_group_spreadsheet',
        gl_ledger: 'fd_group_gl_ledger',
        pdf_unidentified: 'fd_group_pdf_unidentified',
        unrecognized: 'fd_group_unrecognized',
    };

    var DEGRADED_REASON_KEYS = {
        flag_off: 'fd_degraded_flag_off',
        brain_timeout: 'fd_degraded_timeout',
        brain_error: 'fd_degraded_error',
        bad_output: 'fd_degraded_error',
    };

    function welcomeCardHtml() {
        var chips = ['fd_chip_1', 'fd_chip_2', 'fd_chip_3']
            .map(function (k) {
                var text = at(k);
                return (
                    '<button type="button" class="chip n fd-chip" data-action="desk-chip" data-text="' +
                    esc(text) +
                    '">' +
                    esc(text) +
                    '</button>'
                );
            })
            .join('');
        return (
            '<div class="panel fd-card fd-welcome"><div class="bd">' +
            '<p class="fd-lead">' +
            esc(at('fd_welcome_lead')) +
            '</p><div class="fd-chips">' +
            chips +
            '</div></div></div>'
        );
    }

    function inventoryCardHtml(turn) {
        var inv = turn.inventory;
        var body;
        if (inv) {
            var rows = (inv.groups || [])
                .map(function (g) {
                    return (
                        '<div class="fd-inv-row"><span>' +
                        esc(at(GROUP_LABEL_KEYS[g.group] || g.group)) +
                        '</span><b class="fd-inv-count">' +
                        g.count +
                        '</b></div>'
                    );
                })
                .join('');
            var unrec =
                inv.unrecognized > 0
                    ? '<p class="fd-inv-note">' +
                      esc(at('fd_inv_unrecognized', { n: inv.unrecognized })) +
                      '</p>'
                    : '';
            body =
                '<p class="fd-inv-total">' +
                esc(at('fd_inv_total', { n: inv.total })) +
                '</p><div class="fd-inv-groups">' +
                rows +
                '</div>' +
                unrec;
        } else {
            body =
                '<p class="fd-inv-total">' +
                esc(at('fd_inv_total', { n: turn.fileCount || 0 })) +
                '</p>';
        }
        return (
            '<div class="panel fd-card fd-inventory"><div class="hd"><h3>' +
            esc(at('fd_inventory_title')) +
            '</h3></div><div class="bd">' +
            body +
            '<p class="fd-inv-prompt">' +
            esc(at('fd_inventory_prompt')) +
            '</p></div></div>'
        );
    }

    // placeholder key 由调用方给(合同/手动面板用「请选择客户」,上下文条用「全部客户」)。
    // 供 ai-desk-compose-render.js(手动面板/上下文条)共用,故挂在 AI.deskRender 上导出。
    function clientOptionsHtml(clients, selectedId, placeholderKey) {
        var opts = '<option value="">' + esc(at(placeholderKey)) + '</option>';
        (clients || []).forEach(function (c) {
            opts +=
                '<option value="' +
                esc(c.id) +
                '"' +
                (String(c.id) === String(selectedId) ? ' selected' : '') +
                '>' +
                esc(c.name) +
                '</option>';
        });
        return opts;
    }

    function periodOptionsHtml(selected) {
        return root.AI.state.optionsHtml(root.AI.board.periodOptions(), selected, function (p) {
            return p;
        });
    }

    function intentOptionsHtml(selected) {
        var opts = '<option value="">' + esc(at('fd_pick_intent')) + '</option>';
        ENABLED_INTENT_IDS.forEach(function (id) {
            var meta = INTENT_META[id] || {};
            opts +=
                '<option value="' +
                id +
                '"' +
                (id === selected ? ' selected' : '') +
                '>' +
                esc(at(meta.nameKey || id)) +
                '</option>';
        });
        return opts;
    }

    // 合同卡:客户(大脑建议高亮但必须人点下拉才算数)/期间/意图/需料对照/交付物清单 +
    // 确认开工/修改两键(施工总册 §2.3②)。ctx = { clients, selection, confirming, errKey,
    // inventoryGroups }。
    function contractCardHtml(turn, ctx) {
        ctx = ctx || {};
        var meta = INTENT_META[turn.suggestion.intent] || {};
        var sel = ctx.selection || {};
        var needs = needCoverage(meta.needs, ctx.inventoryGroups);
        var needsHtml = needs
            .map(function (n) {
                return (
                    '<li class="' +
                    (n.satisfied ? 'ok' : 'missing') +
                    '">' +
                    (n.satisfied ? '✓ ' : '✗ ') +
                    esc(at(n.need)) +
                    '</li>'
                );
            })
            .join('');
        var deliversHtml = (meta.deliverables || [])
            .map(function (d) {
                return '<li>' + esc(at(d)) + '</li>';
            })
            .join('');
        var errHtml = ctx.errKey ? '<div class="intake-err">' + esc(at(ctx.errKey)) + '</div>' : '';
        var ready = confirmReady(sel);
        var cid = esc(turn.contract.id);
        return (
            '<div class="panel fd-card fd-contract"><div class="hd"><h3>' +
            esc(at('fd_contract_title')) +
            '</h3><span class="chip a">' +
            esc(at(meta.nameKey || turn.suggestion.intent)) +
            '</span></div><div class="bd">' +
            (sel.clientId
                ? '<p class="fd-suggest-note">' + esc(at('fd_suggested_client_note')) + '</p>'
                : '') +
            '<div class="fd-row">' +
            '<label class="fd-lb">' +
            esc(at('fd_field_client')) +
            '<select class="fd-client-sel" data-contract="' +
            cid +
            '">' +
            clientOptionsHtml(ctx.clients, sel.clientId, 'fd_pick_client') +
            '</select></label>' +
            '<label class="fd-lb">' +
            esc(at('fd_field_period')) +
            '<select class="fd-period-sel" data-contract="' +
            cid +
            '">' +
            periodOptionsHtml(sel.period) +
            '</select></label></div>' +
            '<div class="fd-needs"><b>' +
            esc(at('fd_needs_title')) +
            '</b><ul class="fd-need-list">' +
            needsHtml +
            '</ul></div>' +
            '<div class="fd-delivers"><b>' +
            esc(at('fd_delivers_title')) +
            '</b><ul class="fd-deliver-list">' +
            deliversHtml +
            '</ul></div>' +
            errHtml +
            '<div class="fd-actions">' +
            '<button type="button" class="btn pri" data-action="desk-confirm" data-contract="' +
            cid +
            '"' +
            (ready && !ctx.confirming ? '' : ' disabled') +
            '>' +
            esc(ctx.confirming ? at('fd_confirming') : at('fd_confirm_btn')) +
            '</button>' +
            '<button type="button" class="btn" data-action="desk-modify" data-contract="' +
            cid +
            '">' +
            esc(at('fd_modify_btn')) +
            '</button></div></div></div>'
        );
    }

    function progressCardHtml(turn) {
        var c = turn.contract;
        var statusKey = c.status === 'archive' || c.status === 'archived' ? 'archive' : c.status;
        var chip = root.AI.format.chipHtml(statusKey);
        var noteKey =
            c.status === 'delivered'
                ? 'fd_progress_delivered'
                : c.status === 'confirmed'
                  ? 'fd_progress_confirmed'
                  : 'fd_progress_running';
        var link =
            c.work_order_id && c.workspace_client_id
                ? '<a class="btn sm" href="#/client/' +
                  encodeURIComponent(c.workspace_client_id) +
                  '/wo">' +
                  esc(at('fd_progress_view_btn')) +
                  '</a>'
                : '';
        return (
            '<div class="panel fd-card fd-progress"><div class="hd"><h3>' +
            esc(at('fd_progress_title')) +
            '</h3>' +
            chip +
            '</div><div class="bd"><p class="fd-progress-note">' +
            esc(at(noteKey)) +
            '</p>' +
            link +
            '</div></div>'
        );
    }

    function rejectedCardHtml() {
        var list = ENABLED_INTENT_IDS.map(function (id) {
            var meta = INTENT_META[id] || {};
            return '<li>' + esc(at(meta.nameKey || id)) + '</li>';
        }).join('');
        return (
            '<div class="panel fd-card fd-rejected"><div class="hd"><h3>' +
            esc(at('fd_rejected_title')) +
            '</h3></div><div class="bd"><p>' +
            esc(at('fd_rejected_lead')) +
            '</p><ul class="fd-enabled-list">' +
            list +
            '</ul></div></div>'
        );
    }

    function degradedCardHtml(reason) {
        var key = DEGRADED_REASON_KEYS[reason] || 'fd_degraded_generic';
        return (
            '<div class="panel fd-card fd-degraded"><div class="hd"><h3>' +
            esc(at('fd_degraded_title')) +
            '</h3></div><div class="bd"><p>' +
            esc(at(key)) +
            '</p><button type="button" class="btn pri" data-action="desk-open-manual">' +
            esc(at('fd_degraded_manual_btn')) +
            '</button></div></div>'
        );
    }

    function dismissedCardHtml() {
        return (
            '<div class="panel fd-card fd-dismissed"><div class="bd"><p class="fd-dismissed-note">' +
            esc(at('fd_dismissed_note')) +
            '</p></div></div>'
        );
    }

    function emptyCardHtml() {
        return (
            '<div class="panel fd-card fd-dismissed"><div class="bd"><p class="fd-dismissed-note">' +
            esc(at('fd_empty_note')) +
            '</p></div></div>'
        );
    }

    function turnCardHtml(turn, contractCtxById) {
        switch (turn.kind) {
            case 'inventory':
                return inventoryCardHtml(turn);
            case 'contract':
                return contractCardHtml(turn, (contractCtxById || {})[turn.contract.id] || {});
            case 'progress':
                return progressCardHtml(turn);
            case 'rejected':
                return rejectedCardHtml();
            case 'degraded':
                return degradedCardHtml(turn.reason);
            case 'dismissed':
                return dismissedCardHtml();
            default:
                return emptyCardHtml();
        }
    }

    function feedHtml(turns, contractCtxById) {
        if (!turns || !turns.length) return welcomeCardHtml();
        return turns
            .map(function (t) {
                return turnCardHtml(t, contractCtxById);
            })
            .join('');
    }

    root.AI = root.AI || {};
    root.AI.deskRender = {
        INTENT_META: INTENT_META,
        ENABLED_INTENT_IDS: ENABLED_INTENT_IDS,
        needCoverage: needCoverage,
        confirmReady: confirmReady,
        deriveCard: deriveCard,
        clientOptionsHtml: clientOptionsHtml,
        periodOptionsHtml: periodOptionsHtml,
        intentOptionsHtml: intentOptionsHtml,
        welcomeCardHtml: welcomeCardHtml,
        inventoryCardHtml: inventoryCardHtml,
        contractCardHtml: contractCardHtml,
        progressCardHtml: progressCardHtml,
        rejectedCardHtml: rejectedCardHtml,
        degradedCardHtml: degradedCardHtml,
        dismissedCardHtml: dismissedCardHtml,
        turnCardHtml: turnCardHtml,
        feedHtml: feedHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
