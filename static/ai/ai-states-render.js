/*
 * Pearnly AI · ai-states-render.js · 状态词典 #/states(B1)组件拼装 + 15 类分节样例
 *
 * 上半段零 DOM 纯函数(徽章/进度/动画/按钮七态/可解释卡的 HTML 构造 + 八色族与 15 类
 * 注册表),node(tests/unit/test_ai_states_pure.py)直接 require 断言;下半段样例页
 * 拼装依赖全局 at(),只在浏览器根挂载——同 ai-desk-render.js 的双段先例。
 *
 * 这里只管「状态长什么脸」,不判定任何业务状态:色族由调用方按
 * docs/design-system/STATE-LANGUAGE.md 的映射表选,组件类名与 ai-states.css 一一对应。
 * 文案全部由调用方喂已翻译好的字符串(同 ai-state.js 先例,纯函数不碰 window.at)。
 */
(function (root) {
    'use strict';

    // 八大色系(ai-states.css 的 .st-<族> 修饰类):ok=正常绿 wait=等待黄 run=执行蓝
    // ai=AI 紫 warn=警告橙 err=错误红 off=禁用灰 empty=空白。
    var FAMILIES = ['ok', 'wait', 'run', 'ai', 'warn', 'err', 'off', 'empty'];

    // 15 类分节的闭集(Zihao 2026-07-26 拍板原话顺序)——样例页与规范文档共用这份 id 表,
    // 少一节/错序都算走样,测试锁死。
    var CATEGORIES = [
        'data',
        'task',
        'ai',
        'flow',
        'system',
        'progress',
        'risk',
        'review',
        'file',
        'notify',
        'perm',
        'button',
        'explain',
        'color',
        'anim',
    ];

    var BTN_STATES = ['default', 'hover', 'active', 'disabled', 'loading', 'success', 'error'];

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }

    function clampPct(p) {
        var n = Number(p);
        if (!isFinite(n)) return 0;
        return Math.max(0, Math.min(100, Math.round(n)));
    }

    // 非法色族一律落空白族——宁可显得「没状态」也不冒充某个具体状态(状态诚实)。
    function famClass(fam) {
        return 'st-' + (FAMILIES.indexOf(fam) >= 0 ? fam : 'empty');
    }

    function badgeHtml(fam, label, opts) {
        opts = opts || {};
        return (
            '<span class="st-badge ' +
            famClass(fam) +
            (opts.bounce ? ' st-badge-bounce' : '') +
            (opts.pulse ? ' st-pulse' : '') +
            '">' +
            esc(label) +
            '</span>'
        );
    }

    function dotsHtml(fam) {
        return '<span class="st-dots ' + famClass(fam) + '"><i></i><i></i><i></i></span>';
    }

    // data-demo="pct" 供样例页的演示计时器(ai-states.js)找到并滚动百分比;业务页面
    // 不传 opts.demo,拿到的是静态值。
    function barHtml(fam, pct, opts) {
        return (
            '<span class="st-bar ' +
            famClass(fam) +
            '" style="--p:' +
            clampPct(pct) +
            '"' +
            (opts && opts.demo ? ' data-demo="pct"' : '') +
            '><i></i></span>'
        );
    }

    function ringHtml(fam, pct, opts) {
        var p = clampPct(pct);
        return (
            '<span class="st-ring ' +
            famClass(fam) +
            '" style="--p:' +
            p +
            '"' +
            (opts && opts.demo ? ' data-demo="pct"' : '') +
            '><b>' +
            p +
            '%</b></span>'
        );
    }

    function stepsHtml(fam, current, total) {
        var t = Math.max(1, Math.round(Number(total) || 1));
        var c = Math.max(0, Math.min(t, Math.round(Number(current) || 0)));
        var segs = '';
        for (var i = 0; i < t; i++) {
            segs += i < c ? '<i class="on"></i>' : '<i></i>';
        }
        return '<span class="st-steps ' + famClass(fam) + '">' + segs + '</span>';
    }

    function countHtml(done, total, unitLabel) {
        return (
            '<span class="st-count"><b>' +
            clampNum(done) +
            '</b>/' +
            clampNum(total) +
            (unitLabel ? ' ' + esc(unitLabel) : '') +
            '</span>'
        );
    }

    function clampNum(n) {
        var v = Number(n);
        return isFinite(v) && v >= 0 ? Math.round(v) : 0;
    }

    function queueHtml(fam, n, label) {
        return (
            '<span class="st-queue ' +
            famClass(fam) +
            '"><b>' +
            clampNum(n) +
            '</b>' +
            esc(label) +
            '</span>'
        );
    }

    function etaHtml(label, value) {
        return '<span class="st-eta">' + esc(label) + ' <b>' + esc(value) + '</b></span>';
    }

    // 按钮七态。hover/active 用 .is-* 镜像类静态展示(样例页无法真悬停);loading 内嵌
    // 三点并 disabled(双保险:pointer-events 关了,键盘触发也进不来)。
    function btnHtml(state, label) {
        var st = BTN_STATES.indexOf(state) >= 0 ? state : 'default';
        var cls = 'st-btn';
        var attrs = '';
        var inner = esc(label);
        if (
            st === 'hover' ||
            st === 'active' ||
            st === 'loading' ||
            st === 'success' ||
            st === 'error'
        ) {
            cls += ' is-' + st;
        }
        if (st === 'disabled' || st === 'loading') attrs = ' disabled';
        if (st === 'loading') inner = dotsHtml('off') + inner;
        return '<button type="button" class="' + cls + '"' + attrs + '>' + inner + '</button>';
    }

    // AI 可解释卡:结论徽章 + 展开「依据」清单(票面/历史/规则)。open 由挂载层管
    // (点按钮切 .on),初始态由调用方给——纯函数不记状态。
    function explainCardHtml(opts) {
        opts = opts || {};
        var srcs = (opts.sources || [])
            .map(function (s) {
                return (
                    '<div class="st-explain-src"><small>' +
                    esc(s.k) +
                    '</small><span>' +
                    esc(s.v) +
                    '</span></div>'
                );
            })
            .join('');
        return (
            '<div class="st-explain' +
            (opts.open ? ' on' : '') +
            '"><div class="st-explain-hd">' +
            badgeHtml('ai', opts.badgeLabel) +
            '<span class="st-explain-verdict">' +
            esc(opts.verdict) +
            '</span><button type="button" class="st-explain-toggle" data-action="sts-explain-toggle">' +
            esc(opts.toggleLabel) +
            '</button></div><div class="st-explain-bd">' +
            srcs +
            '</div></div>'
        );
    }

    var pure = {
        FAMILIES: FAMILIES,
        CATEGORIES: CATEGORIES,
        BTN_STATES: BTN_STATES,
        clampPct: clampPct,
        famClass: famClass,
        badgeHtml: badgeHtml,
        dotsHtml: dotsHtml,
        barHtml: barHtml,
        ringHtml: ringHtml,
        stepsHtml: stepsHtml,
        countHtml: countHtml,
        queueHtml: queueHtml,
        etaHtml: etaHtml,
        btnHtml: btnHtml,
        explainCardHtml: explainCardHtml,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为样例页拼装(依赖全局 at(),node 不调用)=====
    if (!root || typeof root.document === 'undefined') return;

    function item(labelKey, inner) {
        return '<div class="sts-item"><small>' + esc(at(labelKey)) + '</small>' + inner + '</div>';
    }

    function sec(idx, titleKey, body) {
        return (
            '<div class="panel"><div class="hd"><h3>' +
            idx +
            ' · ' +
            esc(at(titleKey)) +
            '</h3></div><div class="bd">' +
            body +
            '</div></div>'
        );
    }

    function row(inner) {
        return '<div class="sts-row">' + inner + '</div>';
    }

    // 纯徽章节(任务/系统/风险/审核/权限)共用一个形状:spec 是空格分隔的
    // 「色族:文案key」紧凑表法,一行胶囊排开。
    function badgesSec(idx, titleKey, spec) {
        return sec(
            idx,
            titleKey,
            row(
                spec
                    .split(' ')
                    .map(function (pair) {
                        var p = pair.split(':');
                        return badgeHtml(p[0], at(p[1]));
                    })
                    .join('')
            )
        );
    }

    // 每节都用真组件演示(不是截图/示意):这里的类名就是新页面该抄的类名。
    var SECTIONS = [
        function dataSec() {
            return sec(
                '一',
                'sts_sec_data',
                row(
                    item('sts_st_ok', badgeHtml('ok', at('sts_data_ok'))) +
                        item(
                            'sts_st_loading',
                            '<span class="st-skeleton sts-skel-demo" aria-hidden="true"></span>'
                        ) +
                        item('sts_st_empty', badgeHtml('empty', at('sts_data_empty'))) +
                        item('sts_st_error', badgeHtml('err', at('sts_data_err')))
                )
            );
        },
        function taskSec() {
            var spec =
                'wait:sts_task_pending run:sts_task_running ok:sts_task_done err:sts_task_failed off:sts_task_cancel';
            return badgesSec('二', 'sts_sec_task', spec);
        },
        function aiSec() {
            return sec(
                '三',
                'sts_sec_ai',
                row(
                    item(
                        'sts_ai_thinking',
                        badgeHtml('ai', at('sts_ai_thinking'), { pulse: true })
                    ) +
                        item('sts_ai_tool', '<span class="st-ai">' + dotsHtml('ai') + '</span>') +
                        item(
                            'sts_ai_ocr',
                            '<span class="sts-demo-file st-shimmer">' +
                                esc(at('sts_file_name')) +
                                '</span>'
                        ) +
                        item(
                            'sts_ai_writing',
                            badgeHtml('ai', at('sts_ai_writing')) + ' ' + dotsHtml('ai')
                        ) +
                        item('sts_ai_idle', badgeHtml('off', at('sts_ai_idle')))
                )
            );
        },
        function flowSec() {
            var stages = [
                'sts_flow_s1',
                'sts_flow_s2',
                'sts_flow_s3',
                'sts_flow_s4',
                'sts_flow_s5',
            ];
            var flow = stages
                .map(function (k, i) {
                    var fam = i < 2 ? 'ok' : i === 2 ? 'run' : 'empty';
                    return badgeHtml(fam, at(k));
                })
                .join('<span class="sts-arrow">&rsaquo;</span>');
            return sec(
                '四',
                'sts_sec_flow',
                '<div class="sts-flow">' +
                    flow +
                    '</div><div class="sts-row" style="margin-top:12px">' +
                    item('sts_prog_steps', stepsHtml('run', 3, 8) + ' ' + countHtml(3, 8)) +
                    '</div>'
            );
        },
        function systemSec() {
            var spec =
                'ok:sts_sys_ok wait:sts_sys_maint warn:sts_sys_degraded err:sts_sys_down off:sts_sys_unlinked';
            return badgesSec('五', 'sts_sec_system', spec);
        },
        function progressSec() {
            return sec(
                '六',
                'sts_sec_progress',
                row(
                    item('sts_prog_bar', barHtml('run', 64, { demo: true })) +
                        item('sts_prog_ring', ringHtml('run', 64, { demo: true })) +
                        item('sts_prog_eta', etaHtml(at('sts_prog_eta'), at('sts_prog_eta_v'))) +
                        item('sts_prog_files', countHtml(27, 128, at('sts_prog_files_unit'))) +
                        item('sts_prog_steps', stepsHtml('run', 3, 8) + ' ' + countHtml(3, 8)) +
                        item('sts_prog_token', barHtml('ai', 72) + ' ' + countHtml(7200, 10000)) +
                        item('sts_prog_queue', queueHtml('wait', 5, at('sts_prog_queue_lb')))
                )
            );
        },
        function riskSec() {
            var spec = 'ok:sts_risk_low wait:sts_risk_mid warn:sts_risk_high err:sts_risk_crit';
            return badgesSec('七', 'sts_sec_risk', spec);
        },
        function reviewSec() {
            var spec =
                'wait:sts_rev_pending run:sts_rev_doing ok:sts_rev_pass err:sts_rev_reject warn:sts_rev_more';
            return badgesSec('八', 'sts_sec_review', spec);
        },
        function fileSec() {
            return sec(
                '九',
                'sts_sec_file',
                row(
                    item('sts_file_uploading', barHtml('run', 38, { demo: true })) +
                        item('sts_file_done', badgeHtml('ok', at('sts_file_done'))) +
                        item(
                            'sts_file_parsing',
                            badgeHtml('ai', at('sts_file_parsing'), { pulse: true })
                        ) +
                        item('sts_file_failed', badgeHtml('err', at('sts_file_failed'))) +
                        item('sts_file_archived', badgeHtml('off', at('sts_file_archived')))
                )
            );
        },
        function notifySec() {
            return sec(
                '十',
                'sts_sec_notify',
                row(
                    item('sts_ntf_new', badgeHtml('warn', at('sts_ntf_new'), { bounce: true })) +
                        item('sts_ntf_unread', queueHtml('warn', 3, at('sts_ntf_unread'))) +
                        item('sts_ntf_read', badgeHtml('off', at('sts_ntf_read')))
                )
            );
        },
        function permSec() {
            var spec = 'ok:sts_perm_ok wait:sts_perm_ro off:sts_perm_no err:sts_perm_locked';
            return badgesSec('十一', 'sts_sec_perm', spec);
        },
        function buttonSec() {
            var labels = {
                loading: at('sts_btn_loading'),
                success: at('sts_btn_success'),
                error: at('sts_btn_error'),
            };
            return sec(
                '十二',
                'sts_sec_button',
                row(
                    BTN_STATES.map(function (st) {
                        return item('sts_st_' + st, btnHtml(st, labels[st] || at('sts_btn_txt')));
                    }).join('')
                )
            );
        },
        function explainSec() {
            return sec(
                '十三',
                'sts_sec_explain',
                explainCardHtml({
                    badgeLabel: at('sts_exp_badge'),
                    verdict: at('sts_exp_verdict'),
                    toggleLabel: at('sts_exp_toggle'),
                    sources: [
                        { k: at('sts_exp_src_face'), v: at('sts_exp_src_face_v') },
                        { k: at('sts_exp_src_hist'), v: at('sts_exp_src_hist_v') },
                        { k: at('sts_exp_src_rule'), v: at('sts_exp_src_rule_v') },
                    ],
                })
            );
        },
        function colorSec() {
            var cards = FAMILIES.map(function (f) {
                return (
                    '<div class="sts-swatch st-' +
                    f +
                    '"><b>' +
                    esc(at('sts_fam_' + f)) +
                    '</b><code>--st-' +
                    f +
                    '-bg / -fg / -line</code></div>'
                );
            }).join('');
            return sec(
                '十四',
                'sts_sec_color',
                '<p class="note" style="margin-bottom:10px">' +
                    esc(at('sts_color_note')) +
                    '</p><div class="sts-swatches">' +
                    cards +
                    '</div>'
            );
        },
        function animSec() {
            return sec(
                '十五',
                'sts_sec_anim',
                row(
                    item(
                        'sts_anim_skel',
                        '<span class="st-skeleton sts-skel-demo" aria-hidden="true"></span>'
                    ) +
                        item(
                            'sts_anim_shimmer',
                            '<span class="sts-demo-file st-shimmer">' +
                                esc(at('sts_file_name')) +
                                '</span>'
                        ) +
                        item(
                            'sts_anim_pulse',
                            badgeHtml('ai', at('sts_ai_thinking'), { pulse: true })
                        ) +
                        item('sts_anim_dots', dotsHtml('run')) +
                        item(
                            'sts_anim_bounce',
                            badgeHtml('warn', at('sts_ntf_new'), { bounce: true })
                        )
                ) +
                    '<p class="note" style="margin-top:10px">' +
                    esc(at('sts_anim_reduced')) +
                    '</p>'
            );
        },
    ];

    function pageHtml() {
        return SECTIONS.map(function (build) {
            return build();
        }).join('');
    }

    root.AI = root.AI || {};
    root.AI.statesRender = {
        FAMILIES: FAMILIES,
        CATEGORIES: CATEGORIES,
        BTN_STATES: BTN_STATES,
        badgeHtml: badgeHtml,
        dotsHtml: dotsHtml,
        barHtml: barHtml,
        ringHtml: ringHtml,
        stepsHtml: stepsHtml,
        countHtml: countHtml,
        queueHtml: queueHtml,
        etaHtml: etaHtml,
        btnHtml: btnHtml,
        explainCardHtml: explainCardHtml,
        pageHtml: pageHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
