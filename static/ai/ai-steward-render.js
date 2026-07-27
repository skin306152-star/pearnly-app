/*
 * Pearnly AI · ai-steward-render.js · 智能管家(B2-M1)左窗「执行状态」拼装
 *
 * 吃 GET /api/ai/steward/tasks/{tid} 的载荷:
 *   { task_id, title, status, started_at, agent_count,
 *     steps: [{ id, kind?('tool'|'ask'), label, state, detail, links: [{label, href}] }],
 *     loop?: { calls, tool_calls, asked, wrote, waiting_auth,
 *              question?: { field, text, options: [文本] } },
 *     artifacts: [{ kind, label, href?,
 *                   columns?: [{key, label}], rows?: [{<key>: 值}] }],
 *     error_code?, error_reason?(没跑成时的机器码 + 人话),
 *     cancellable(这条现在能不能取消 · 在跑的写活一律 false),
 *     authorization?(写授权卡 · 拼装在 ai-steward-authz-render.js) }
 *
 * 状态一律从 B1 状态词典取脸(docs/design-system/STATE-LANGUAGE.md · ai-states.css),
 * 本文件只做「业务码 → 色族」的查表(同 ai-matrix-render.js 的 BADGE_CHIP 先例),
 * 不自造任何状态样式;组件 HTML 一律走 AI.statesRender.*,不手抄类名。
 *
 * 上半段零 DOM 零 i18n 纯函数(状态映射/终态判据/深链白名单/载荷规整),
 * node(tests/unit/test_ai_steward_pure.py)直接 require 断言;下半段拼装依赖全局 at()
 * 与 AI.state/AI.statesRender,只在浏览器根挂载 —— 同 ai-states-render.js 的双段先例。
 */
(function (root) {
    'use strict';

    // 契约闭集。后端给了集合外的值 = 契约漂了,统一落 'empty' 族显示「状态未知」,
    // 绝不猜成某个具体状态(状态诚实:宁可承认不知道,也不点一盏假绿灯)。
    var STEP_STATES = ['done', 'running', 'queued', 'waiting_auth', 'failed'];
    var TASK_STATUSES = ['running', 'done', 'failed', 'waiting_user', 'cancelled'];

    // 契约 §左窗:done→成功绿 / running→执行蓝(带脉冲)/ queued→中性灰 /
    // waiting_auth→警告橙 / failed→错误红;任务 cancelled→禁用灰(人主动停的,不是错)。
    var STEP_FAMILY = {
        done: 'ok',
        running: 'run',
        queued: 'off',
        waiting_auth: 'warn',
        failed: 'err',
    };
    var TASK_FAMILY = {
        running: 'run',
        done: 'ok',
        failed: 'err',
        waiting_user: 'wait',
        cancelled: 'off',
    };

    function stepFamily(state) {
        return STEP_FAMILY[state] || 'empty';
    }

    function taskFamily(status) {
        return TASK_FAMILY[status] || 'empty';
    }

    function stepStateKey(state) {
        return STEP_STATES.indexOf(state) >= 0 ? 'stw_step_' + state : 'stw_step_unknown';
    }

    function taskStatusKey(status) {
        return TASK_STATUSES.indexOf(status) >= 0 ? 'stw_status_' + status : 'stw_status_unknown';
    }

    // 轮询收口判据:终态与 waiting_user(等人批卡,批完由决断响应重启轮询)都停;
    // 契约外的未知值当"还在跑"继续轮询 —— 停了会让真在跑的任务永远停在半路。
    function isTerminalStatus(status) {
        return (
            status === 'done' ||
            status === 'failed' ||
            status === 'waiting_user' ||
            status === 'cancelled'
        );
    }

    // 深链白名单:只放 SPA 内 hash 深链与同源绝对路径(附件下载)。javascript:/data:/
    // 协议相对('//evil')与外站一律丢掉整条链接,不渲染一个点了没反应的假出口。
    function safeHref(href) {
        var s = String(href == null ? '' : href).trim();
        if (!s) return null;
        if (s.indexOf('#/') === 0) return s;
        if (s.charAt(0) === '/' && s.charAt(1) !== '/') return s;
        return null;
    }

    function safeLinks(links) {
        return (links || [])
            .map(function (l) {
                var href = safeHref(l && l.href);
                return href ? { label: (l && l.label) || href, href: href } : null;
            })
            .filter(Boolean);
    }

    function stepCounts(steps) {
        var list = steps || [];
        var done = list.filter(function (s) {
            return s && s.state === 'done';
        }).length;
        return { done: done, total: list.length };
    }

    // 查询次数:后端没给或给了非正整数就当 1(至少查过一次),不显示 "查询 0 次"。
    function agentCount(task) {
        var n = Math.round(Number(task && task.agent_count));
        return isFinite(n) && n > 0 ? n : 1;
    }

    // 追问的候选按钮最多摆几个。多于此照旧可以打字回答 —— 一排按钮铺满两行比没有更难挑。
    var MAX_OPTIONS = 8;

    // 追问投影:loop.question 规整成 { text, options }。没问题、问题为空、或候选全是空串
    // 一律 null(调用方据此整块不渲染)——摆一排空按钮比不摆更糟。
    function loopQuestion(task) {
        var q = task && task.loop && task.loop.question;
        var text = q ? String(q.text == null ? '' : q.text).trim() : '';
        if (!text) return null;
        var seen = {};
        var options = ((q && q.options) || [])
            .map(function (o) {
                return String(o == null ? '' : o).trim();
            })
            .filter(function (o) {
                if (!o || seen[o]) return false;
                seen[o] = true;
                return true;
            })
            .slice(0, MAX_OPTIONS);
        return { field: String((q && q.field) || ''), text: text, options: options };
    }

    // 候选只在「还等着她回答」时可点:终态后那一轮后端不认,点下去只会拿到一个错。
    function optionsEnabled(task, busy) {
        return task && task.status === 'waiting_user' && !busy;
    }

    // 后端把「没跑成的原因」同时写进三处:任务 error_reason(左窗红条)、失败步的 detail、
    // 会话里那条回复(右窗气泡)—— 一字不差,一屏印三遍(泰文更长,三块各折三行)。分工:
    //   气泡  = 结论 + 出路(会计读答复的地方,那句话的家)
    //   步骤  = 这一步发生了什么(与红条同句时留白,由 stepHtml 判)
    //   红条  = 只在气泡里没有这句时才出现(深链直接开左窗、或消息还没回来)
    // 这里判「气泡里有没有」:同一条任务的管家消息正文与原因逐字相同即算已印过。
    function reasonIsEchoed(task, messages) {
        var reason = String((task && task.error_reason) || '').trim();
        if (!reason) return false;
        var tid = String((task && task.task_id) || '');
        return (messages || []).some(function (m) {
            if (!m || m.role === 'user') return false;
            if (m.task_id && tid && String(m.task_id) !== tid) return false;
            return String(m.text == null ? '' : m.text).trim() === reason;
        });
    }

    // 开始时间 → 本地 HH:MM。解析不了回空串,调用方据此整块不显示(不臆造时间)。
    function startedLabel(iso) {
        var t = Date.parse(String(iso || ''));
        if (!isFinite(t)) return '';
        var d = new Date(t);
        return (
            String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
        );
    }

    var pure = {
        STEP_STATES: STEP_STATES,
        TASK_STATUSES: TASK_STATUSES,
        stepFamily: stepFamily,
        taskFamily: taskFamily,
        stepStateKey: stepStateKey,
        taskStatusKey: taskStatusKey,
        isTerminalStatus: isTerminalStatus,
        safeHref: safeHref,
        safeLinks: safeLinks,
        stepCounts: stepCounts,
        agentCount: agentCount,
        startedLabel: startedLabel,
        reasonIsEchoed: reasonIsEchoed,
        loopQuestion: loopQuestion,
        optionsEnabled: optionsEnabled,
        MAX_OPTIONS: MAX_OPTIONS,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器拼装(依赖 at()/AI.state/AI.statesRender,node 不调用)=====
    if (!root || typeof root.document === 'undefined') return;

    function esc(s) {
        return AI.state.esc(s);
    }

    function linksHtml(links) {
        var list = safeLinks(links);
        if (!list.length) return '';
        return (
            '<div class="stw-links">' +
            list
                .map(function (l) {
                    return (
                        '<a class="stw-link" href="' + esc(l.href) + '">' + esc(l.label) + '</a>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    // 追问那一步(kind='ask')底下的候选按钮。点一下 = 把这句话当作回答送出去,后端
    // 接回同一条任务续跑。挂在步骤行上而不是另起一块:问题和答法要在同一处。
    function optionsHtml(q, enabled) {
        if (!q || !q.options.length) return '';
        return (
            '<div class="stw-chips stw-ask-opts">' +
            q.options
                .map(function (o) {
                    return (
                        '<button type="button" class="chip stw-chip" data-action="stw-ask-pick" ' +
                        'data-text="' +
                        esc(o) +
                        '"' +
                        (enabled ? '' : ' disabled') +
                        '>' +
                        esc(o) +
                        '</button>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function stepHtml(step, opts) {
        var state = step && step.state;
        var fam = stepFamily(state);
        var badge = AI.statesRender.badgeHtml(fam, at(stepStateKey(state)), {
            pulse: state === 'running',
        });
        // 失败步的 detail 就是任务级 error_reason 那一句(store.fail_steps 复制过去的)。
        // 上面的红条已经印过它,这里再印一遍 = 同一屏同一句话两遍。
        var text = step && step.detail ? String(step.detail) : '';
        if (opts && opts.reason && text === opts.reason) text = '';
        var detail = text ? '<div class="stw-step-d">' + esc(text) + '</div>' : '';
        // 执行中那一步补三点:徽章说"是什么状态",三点说"此刻还活着"(B1 §3 类三)。
        var dots = state === 'running' ? AI.statesRender.dotsHtml('run') : '';
        // 候选只挂在最后一次追问那一步上:调用方只给那一步传 question,别的步骤拿不到。
        var options =
            step && step.kind === 'ask' && opts
                ? optionsHtml(opts.question, opts.optionsEnabled)
                : '';
        return (
            '<li class="stw-step"><span class="stw-step-badge">' +
            badge +
            '</span><div class="stw-step-main"><div class="stw-step-t">' +
            esc((step && step.label) || '') +
            dots +
            '</div>' +
            detail +
            linksHtml(step && step.links) +
            options +
            '</div></li>'
        );
    }

    // 表格产物形状由后端定契约(services/steward/copy.py _table):
    //   columns = [{key, label}] · rows = [{<key>: 值}]
    // 取值一律按 columns 的 key 走,列顺序即表头顺序;缺 key 给空格子,不印 undefined。
    // (首版按「columns 是字符串数组 + 行是数组」渲染,dict 行整个进一个 td 印成
    //  [object Object] —— 五个工具的表格全废;E2E 的桩当时抄了那套不存在的形状,自证自洽。)
    function tableHtml(art) {
        var rows = art.rows || [];
        var cols = art.columns || [];
        if (!rows.length || !cols.length) return '';
        var head =
            '<thead><tr>' +
            cols
                .map(function (c) {
                    return '<th>' + esc((c && (c.label || c.key)) || '') + '</th>';
                })
                .join('') +
            '</tr></thead>';
        var body = rows
            .map(function (r) {
                return (
                    '<tr>' +
                    cols
                        .map(function (c) {
                            var v = r && c ? r[c.key] : null;
                            return '<td>' + esc(v == null ? '' : v) + '</td>';
                        })
                        .join('') +
                    '</tr>'
                );
            })
            .join('');
        return (
            '<div class="stw-scroll"><table class="stw-table">' +
            head +
            '<tbody>' +
            body +
            '</tbody></table></div>'
        );
    }

    // 产物三种 kind:deeplink(一条链接)/ table(已渲好的人话与数字)/ actions(闭集按钮)。
    // 原件与转出物的下载链要带 Bearer 头,<a href> 发不了自定义头 —— 命中下载前缀的换成
    // 走 fetch 的按钮,不摆一个点了 401 的假出口。
    function artifactHtml(art, opts) {
        if (!art) return '';
        var label = esc(art.label || '');
        var aid = AI.stewardAttachRender.downloadIdOf(art.href);
        var href = aid ? null : safeHref(art.href);
        var title = aid
            ? '<button type="button" class="stw-linkbtn" data-action="stw-att-dl" data-aid="' +
              esc(aid) +
              '">' +
              label +
              '</button>'
            : href
              ? '<a class="stw-link" href="' + esc(href) + '">' + label + '</a>'
              : '<span class="stw-art-t">' + label + '</span>';
        var body =
            art.kind === 'table'
                ? tableHtml(art)
                : art.kind === 'actions'
                  ? AI.stewardAttachRender.actionsHtml(art, opts)
                  : '';
        return '<div class="stw-art">' + title + body + '</div>';
    }

    function metaHtml(task) {
        var parts = [at('stw_meta_agents', { n: agentCount(task) })];
        var started = startedLabel(task.started_at);
        if (started) parts.push(at('stw_meta_started', { t: started }));
        return '<div class="stw-meta">' + esc(parts.join(' · ')) + '</div>';
    }

    // 没跑成的任务把原因摆在脸上(error_reason 是后端按任务语言写好的人话,error_code
    // 小字随行给排障用)。cancelled 是人主动停的,用中性灰,不套错误红。
    // echoed = 这句话已经在右窗气泡里了:徽章已经说了「失败」,红条再印一遍只是把同一屏
    // 的字数翻倍(见 reasonIsEchoed)。
    function reasonHtml(task, echoed) {
        if (echoed) return '';
        if (!task.error_reason && !task.error_code) return '';
        return (
            '<div class="stw-reason' +
            (task.status === 'cancelled' ? ' off' : '') +
            '">' +
            esc(task.error_reason || '') +
            (task.error_code ? '<code>' + esc(task.error_code) + '</code>' : '') +
            '</div>'
        );
    }

    // 执行中给「取消」出口(取消是幂等端点,连点不炸);终态不摆一个点了没意义的按钮。
    // 在跑的写活取消不了(后端 409:已投单,只能去对账)—— 摆一个点下去必报错的按钮更糟。
    function cancelHtml(task, busy) {
        if (task.status !== 'running' || task.cancellable === false) return '';
        return (
            '<div class="stw-cancel-row"><button type="button" class="btn sm" ' +
            'data-action="stw-cancel"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(at('stw_cancel_task')) +
            '</button></div>'
        );
    }

    // 任务面板。stalled/授权卡的 busy 与错误由挂载层传入 —— 面板不猜"还在不在跑"。
    function panelHtml(task, opts) {
        opts = opts || {};
        var counts = stepCounts(task.steps);
        var fam = taskFamily(task.status);
        // 候选只挂在最后一次追问上:更早那次的候选已经被回答过,再摆一遍等于让人重答旧题。
        var list = task.steps || [];
        var lastAsk = -1;
        list.forEach(function (s, i) {
            if (s && s.kind === 'ask') lastAsk = i;
        });
        var reason = String(task.error_reason || '');
        var stepOpts = {
            question: loopQuestion(task),
            optionsEnabled: optionsEnabled(task, opts.busy),
        };
        var steps = list
            .map(function (s, i) {
                var o = i === lastAsk ? stepOpts : {};
                return stepHtml(s, Object.assign({ reason: reason }, o));
            })
            .join('');
        // 卡还活着才让按钮可点(waiting_user + actions 块);终态后置灰 —— 后端那一轮不认,
        // 点下去只会拿到一个错。busy 是本地送出在途,连点会开出两个任务。
        var dead = { dead: task.status !== 'waiting_user' || !!opts.busy };
        var arts = (task.artifacts || [])
            .map(function (a) {
                return artifactHtml(a, dead);
            })
            .join('');
        var stalled = opts.stalled
            ? '<div class="stw-stalled">' +
              esc(at('stw_poll_stopped')) +
              '<button type="button" class="btn sm" data-action="stw-poll-again">' +
              esc(at('stw_poll_refresh')) +
              '</button></div>'
            : '';
        var authz = task.authorization
            ? AI.stewardAuthzRender.cardHtml(task.authorization, { busy: opts.authzBusy })
            : '';
        var actionErr = opts.actionErr
            ? '<div class="stw-err">' + esc(opts.actionErr) + '</div>'
            : '';
        return (
            '<div class="panel stw-task"><div class="hd"><h3>' +
            esc(task.title || '') +
            AI.statesRender.badgeHtml(fam, at(taskStatusKey(task.status)), {
                pulse: task.status === 'running',
            }) +
            '</h3></div><div class="bd">' +
            metaHtml(task) +
            '<div class="stw-prog">' +
            AI.statesRender.stepsHtml(fam, counts.done, counts.total || 1) +
            AI.statesRender.countHtml(counts.done, counts.total, at('stw_steps_hd')) +
            '</div>' +
            stalled +
            reasonHtml(task, opts.reasonEchoed) +
            actionErr +
            authz +
            (steps ? '<ul class="stw-steps">' + steps + '</ul>' : '') +
            (arts ? '<div class="stw-arts-hd">' + esc(at('stw_arts_hd')) + '</div>' + arts : '') +
            cancelHtml(task, opts.cancelBusy) +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardRender = Object.assign({ panelHtml: panelHtml }, pure);
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
