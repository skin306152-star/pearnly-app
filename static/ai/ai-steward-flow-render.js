/*
 * Pearnly AI · ai-steward-flow-render.js · 对话流拼装(S1 会话流改版核心)
 *
 * 把「左执行窗 + 右对话」双栏折成一条 Claude/GPT 式对话流:
 *   用户轮 = 右对齐浅底气泡 + 附件 pills + 送出三态(sending/failed 可重发);
 *   管家轮 = 头标 + flow(执行过程条 → 正文 markdown → 授权卡 → 完成卡 → 预算条)。
 *
 * 过程条是旧执行状态窗的化身:同一份 GET /tasks/{tid} 投影,live 时逐步点亮,
 * 默认恒折叠成一行摘要(2026-08-07 拍板),点头部随时展开看明细,点开的状态记在
 * S.procOpen[tid] 优先于默认值。历史轮的任务数据按需补拉(ctx.tasks 缓存没有 →
 * 摆一条可点的「查看执行过程」占位,不假装知道内容)。
 *
 * 上半段零 DOM 零 i18n 纯函数(轮分组/折叠默认值/摘要选型),node
 * (tests/unit/test_ai_steward_flow_render.py)直接 require 断言;下半段拼装依赖
 * 全局 at() 与 AI.state/AI.statesRender/AI.stewardRender/AI.stewardMd。
 */
(function (root) {
    'use strict';

    // 消息流 → 轮列表:user 轮单条,连续的 steward 消息聚成一轮(ack 与收尾答复是
    // 同一件事的两截,拆成两个头标读起来像两个人)。taskIds 按首现顺序去重 ——
    // 过程条挂在第一条引用它的正文之前,一条任务只画一次。
    function groupTurns(messages) {
        var turns = [];
        (messages || []).forEach(function (msg) {
            if (!msg) return;
            if (msg.role === 'user') {
                turns.push({ kind: 'user', msg: msg });
                return;
            }
            var last = turns[turns.length - 1];
            if (!last || last.kind !== 'steward') {
                last = { kind: 'steward', msgs: [], taskIds: [] };
                turns.push(last);
            }
            last.msgs.push(msg);
            if (msg.task_id && last.taskIds.indexOf(msg.task_id) < 0) {
                last.taskIds.push(msg.task_id);
            }
        });
        return turns;
    }

    // 折叠默认值:恒折叠(信息已在摘要/正文/授权卡里,过程条只留一行摘要不占屏)。
    // 用户手动点开的那条不受影响 —— procHtml() 的 opts.open(读 S.procOpen[tid])
    // 优先于本函数,这里只管"没人点过时"的默认态。
    function defaultCollapsed(status) {
        return true;
    }

    // 摘要选型(纯):返回 {key, vars} 交给调用方过词典。running 时优先用正在跑的
    // 那一步的 label(比「正在执行」多一层真信息);没有就回落通用句。
    function summarySpec(task) {
        var steps = (task && task.steps) || [];
        var status = task && task.status;
        var done = steps.filter(function (s) {
            return s && s.state === 'done';
        }).length;
        if (status === 'done') return { key: 'stw_proc_done_sum', vars: { n: steps.length } };
        if (status === 'failed') return { key: 'stw_proc_failed_sum', vars: {} };
        if (status === 'cancelled') return { key: 'stw_proc_cancelled_sum', vars: { n: done } };
        if (status === 'waiting_user') return { key: 'stw_proc_waiting_sum', vars: {} };
        var running = steps.filter(function (s) {
            return s && s.state === 'running';
        })[0];
        if (running && running.label) return { key: null, text: String(running.label) };
        return { key: 'stw_proc_running_sum', vars: {} };
    }

    var pure = {
        groupTurns: groupTurns,
        defaultCollapsed: defaultCollapsed,
        summarySpec: summarySpec,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器拼装(依赖 at()/AI.state/AI.statesRender 等,node 不调用)=====
    if (!root || typeof root.document === 'undefined') return;

    function esc(s) {
        return AI.state.esc(s);
    }

    var CHEV_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" ' +
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M6 9l6 6 6-6"/></svg>';
    var SPARK_SVG =
        '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
        '<path d="M12 2l2.2 6.6L21 11l-6.8 2.4L12 20l-2.2-6.6L3 11l6.8-2.4z"/></svg>';
    var CHECK_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" ' +
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M20 6L9 17l-5-5"/></svg>';

    // ---------- 欢迎屏(空态:能干什么 + 三条示例问法 + 附件提示) ----------
    var PROMPT_KEYS = [
        ['stw_prompt_missing', 'stw_prompt_missing_s'],
        ['stw_prompt_pushfail', 'stw_prompt_pushfail_s'],
        ['stw_prompt_export', 'stw_prompt_export_s'],
    ];
    // 末位是能力自述(写入须批准):键沿用 stw_note —— 能力承诺与注册表一致性的闸
    // (CopyMatchesCapabilityTests)认这个键,别另起一个逃出它的视野。
    var CAP_KEYS = [
        'stw_cap_ocr',
        'stw_cap_missing',
        'stw_cap_recon',
        'stw_cap_report',
        'stw_note',
    ];

    function welcomeHtml() {
        var caps = CAP_KEYS.map(function (k) {
            return '<span><i></i>' + esc(at(k)) + '</span>';
        }).join('');
        var prompts = PROMPT_KEYS.map(function (pair) {
            var label = at(pair[0]);
            return (
                '<button type="button" class="stw-w-prompt" data-action="stw-quick" data-text="' +
                esc(label) +
                '">' +
                esc(label) +
                '<small>' +
                esc(at(pair[1])) +
                '</small></button>'
            );
        }).join('');
        return (
            '<div class="stw-welcome"><h1>' +
            esc(at('stw_welcome_t')) +
            '</h1><div class="stw-w-sub">' +
            esc(at('stw_welcome_s')) +
            '</div><div class="stw-w-caps">' +
            caps +
            '</div><div class="stw-w-prompts">' +
            prompts +
            '</div><div class="stw-w-note">' +
            esc(at('stw_welcome_note')) +
            '</div></div>'
        );
    }

    // ---------- 用户轮 ----------
    function userFootHtml(msg) {
        var state = AI.stewardChatRender.sendState(msg.state);
        if (state === 'sending') {
            return (
                '<div class="stw-msg-foot">' +
                AI.statesRender.dotsHtml('off') +
                esc(at('stw_msg_sending')) +
                '</div>'
            );
        }
        if (state === 'failed') {
            return (
                '<div class="stw-msg-foot">' +
                AI.statesRender.badgeHtml('err', at('stw_msg_failed')) +
                '<button type="button" class="stw-linkbtn" data-action="stw-resend" data-mid="' +
                esc(msg.local_id || '') +
                '">' +
                esc(at('stw_msg_resend')) +
                '</button></div>'
            );
        }
        return '';
    }

    function userTurnHtml(msg) {
        var files = AI.stewardAttachRender.bubbleFilesHtml(msg.attachments);
        var bubble = msg.text ? '<div class="stw-bubble">' + esc(msg.text) + '</div>' : '';
        return '<div class="stw-msg me">' + files + bubble + userFootHtml(msg) + '</div>';
    }

    // ---------- 过程条 ----------
    function summaryText(task) {
        var spec = summarySpec(task);
        return spec.key ? at(spec.key, spec.vars) : spec.text;
    }

    function procHtml(task, opts) {
        opts = opts || {};
        var status = task.status;
        var fam = AI.stewardRender.taskFamily(status);
        var open = opts.open != null ? opts.open : !defaultCollapsed(status);
        var badge = AI.statesRender.badgeHtml(fam, at(AI.stewardRender.taskStatusKey(status)), {
            pulse: status === 'running',
        });
        var meta =
            '<div class="stw-meta">' +
            esc(
                [at('stw_meta_agents', { n: AI.stewardRender.agentCount(task) })]
                    .concat(
                        AI.stewardRender.startedLabel(task.started_at)
                            ? [
                                  at('stw_meta_started', {
                                      t: AI.stewardRender.startedLabel(task.started_at),
                                  }),
                              ]
                            : []
                    )
                    .join(' · ')
            ) +
            '</div>';
        var stalled = opts.stalled
            ? '<div class="stw-stalled">' +
              esc(at('stw_poll_stopped')) +
              '<button type="button" class="btn sm" data-action="stw-poll-again">' +
              esc(at('stw_poll_refresh')) +
              '</button></div>'
            : '';
        return (
            '<div class="stw-proc' +
            (open ? '' : ' collapsed') +
            '" data-proc="' +
            esc(task.task_id) +
            '"><button type="button" class="stw-proc-hd" data-action="stw-proc-toggle" data-tid="' +
            esc(task.task_id) +
            '" aria-expanded="' +
            (open ? 'true' : 'false') +
            '">' +
            badge +
            '<span class="stw-proc-sum">' +
            esc(summaryText(task)) +
            '</span><span class="stw-proc-chev">' +
            CHEV_SVG +
            '</span></button><div class="stw-proc-bd">' +
            meta +
            stalled +
            AI.stewardRender.stepListHtml(task, { busy: opts.busy }) +
            '</div></div>'
        );
    }

    // 缓存里还没有的历史任务:一条可点的占位(点了才拉,不假装知道内容)。
    function procPlaceholderHtml(taskId, loading) {
        return (
            '<div class="stw-proc collapsed"><button type="button" class="stw-proc-hd" ' +
            'data-action="stw-proc-load" data-tid="' +
            esc(taskId) +
            '"' +
            (loading ? ' disabled' : '') +
            '>' +
            (loading
                ? AI.statesRender.dotsHtml('run')
                : AI.statesRender.badgeHtml('off', at('stw_proc_view'))) +
            '<span class="stw-proc-sum">' +
            esc(at(loading ? 'stw_loading' : 'stw_proc_view_s')) +
            '</span><span class="stw-proc-chev">' +
            CHEV_SVG +
            '</span></button></div>'
        );
    }

    // ---------- 收尾卡(完成 + 产物/深链;产物在非终态也如实摆,如回执卡按钮) ----------
    function artifactsCardHtml(task, opts) {
        var arts = AI.stewardRender.artifactsHtml(task, opts);
        if (!arts) return '';
        if (task.status === 'done') {
            return (
                '<div class="stw-donecard"><div class="stw-donecard-hd">' +
                CHECK_SVG +
                esc(at('stw_done_hd')) +
                '</div>' +
                arts +
                '</div>'
            );
        }
        return '<div class="stw-arts">' + arts + '</div>';
    }

    // 一条任务在 flow 里的全部卡片(过程条之外的部分)。
    function taskCardsHtml(task, ctx) {
        var html = '';
        if (task.authorization) {
            html += AI.stewardAuthzRender.cardHtml(task.authorization, { busy: ctx.authzBusy });
        }
        html += AI.stewardRender.reasonHtml(task, ctx.reasonEchoed);
        if (ctx.actionErr) html += '<div class="stw-err">' + esc(ctx.actionErr) + '</div>';
        html += artifactsCardHtml(task, { dead: task.status !== 'waiting_user' || !!ctx.busy });
        return html;
    }

    function stewardTurnHtml(turn, ctx) {
        var flow = '';
        var seenTasks = {};
        turn.msgs.forEach(function (msg) {
            var tid = msg.task_id;
            if (tid && !seenTasks[tid]) {
                seenTasks[tid] = true;
                var task = ctx.tasks[tid];
                if (task) {
                    var isCurrent = tid === ctx.currentTaskId;
                    flow += procHtml(task, {
                        open: ctx.procOpen[tid],
                        busy: ctx.busy,
                        stalled: isCurrent && ctx.stalled,
                    });
                } else {
                    flow += procPlaceholderHtml(tid, ctx.taskLoading[tid]);
                }
            }
            if (msg.text) {
                flow +=
                    '<div class="stw-ai-body">' +
                    AI.stewardMd.render(msg.text, { codeCopyLabel: at('stw_code_copy') }) +
                    '</div>';
            }
            if (msg.budget) flow += AI.stewardAuthzRender.budgetHtml(msg.budget);
        });
        // 卡片挂在轮尾:授权卡/失败原因/产物属于任务收口,不该插在两段正文中间。
        turn.taskIds.forEach(function (tid) {
            var task = ctx.tasks[tid];
            if (!task) return;
            flow += taskCardsHtml(task, {
                authzBusy: tid === ctx.currentTaskId ? ctx.authzBusy : false,
                actionErr: tid === ctx.currentTaskId ? ctx.actionErr : null,
                reasonEchoed: AI.stewardRender.reasonIsEchoed(task, turn.msgs),
                busy: ctx.busy,
            });
        });
        return (
            '<div class="stw-msg agent"><div class="stw-ai-head"><span class="stw-ai-dot">' +
            SPARK_SVG +
            '</span>' +
            esc(at('stw_agent')) +
            '</div><div class="stw-ai-flow">' +
            flow +
            '</div></div>'
        );
    }

    // ---------- 消息流 ----------
    function feedHtml(messages, ctx) {
        ctx = ctx || {};
        if (!messages || !messages.length) return welcomeHtml();
        var earlier = ctx.hasMore
            ? '<div class="stw-earlier"><button type="button" class="btn sm" ' +
              'data-action="stw-load-earlier"' +
              (ctx.loadingEarlier ? ' disabled' : '') +
              '>' +
              esc(at(ctx.loadingEarlier ? 'stw_loading' : 'stw_load_earlier')) +
              '</button></div>'
            : '';
        return (
            earlier +
            groupTurns(messages)
                .map(function (turn) {
                    return turn.kind === 'user'
                        ? userTurnHtml(turn.msg)
                        : stewardTurnHtml(turn, ctx);
                })
                .join('')
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardFlowRender = Object.assign(
        {
            feedHtml: feedHtml,
            welcomeHtml: welcomeHtml,
            procHtml: procHtml,
            PROMPT_KEYS: PROMPT_KEYS,
            CAP_KEYS: CAP_KEYS,
        },
        pure
    );
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
