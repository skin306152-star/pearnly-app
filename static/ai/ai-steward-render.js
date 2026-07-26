/*
 * Pearnly AI · ai-steward-render.js · 智能管家(B2-M1)左窗「执行状态」拼装
 *
 * 吃 GET /api/ai/steward/tasks/{tid} 的载荷:
 *   { task_id, title, status, started_at, agent_count,
 *     steps: [{ id, label, state, detail, links: [{label, href}] }],
 *     artifacts: [{ kind, label, href?,
 *                   columns?: [{key, label}], rows?: [{<key>: 值}] }] }
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
    var TASK_STATUSES = ['running', 'done', 'failed', 'waiting_user'];

    // 契约 §左窗:done→成功绿 / running→执行蓝(带脉冲)/ queued→中性灰 /
    // waiting_auth→警告橙 / failed→错误红。
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

    // 轮询收口判据:三个终态之外(含契约外的未知值)都当"还在跑"继续轮询——
    // 未知值停轮询会让真在跑的任务永远停在半路,宁可多拉几次。
    function isTerminalStatus(status) {
        return status === 'done' || status === 'failed' || status === 'waiting_user';
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

    // Agent 数:后端没给或给了非正整数就当 1(至少有管家自己在跑),不显示 "0 个 Agent"。
    function agentCount(task) {
        var n = Math.round(Number(task && task.agent_count));
        return isFinite(n) && n > 0 ? n : 1;
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

    function stepHtml(step) {
        var state = step && step.state;
        var fam = stepFamily(state);
        var badge = AI.statesRender.badgeHtml(fam, at(stepStateKey(state)), {
            pulse: state === 'running',
        });
        var detail =
            step && step.detail ? '<div class="stw-step-d">' + esc(step.detail) + '</div>' : '';
        // 执行中那一步补三点:徽章说"是什么状态",三点说"此刻还活着"(B1 §3 类三)。
        var dots = state === 'running' ? AI.statesRender.dotsHtml('run') : '';
        return (
            '<li class="stw-step"><span class="stw-step-badge">' +
            badge +
            '</span><div class="stw-step-main"><div class="stw-step-t">' +
            esc((step && step.label) || '') +
            dots +
            '</div>' +
            detail +
            linksHtml(step && step.links) +
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

    function artifactHtml(art) {
        if (!art) return '';
        var href = safeHref(art.href);
        var label = esc(art.label || '');
        var title = href
            ? '<a class="stw-link" href="' + esc(href) + '">' + label + '</a>'
            : '<span class="stw-art-t">' + label + '</span>';
        var body = art.kind === 'table' ? tableHtml(art) : '';
        return '<div class="stw-art">' + title + body + '</div>';
    }

    function metaHtml(task) {
        var parts = [at('stw_meta_agents', { n: agentCount(task) })];
        var started = startedLabel(task.started_at);
        if (started) parts.push(at('stw_meta_started', { t: started }));
        return '<div class="stw-meta">' + esc(parts.join(' · ')) + '</div>';
    }

    // 任务面板。stalledNote 由挂载层在轮询自行收口(超时)后传入 —— 面板不猜"还在不在跑"。
    function panelHtml(task, opts) {
        opts = opts || {};
        var counts = stepCounts(task.steps);
        var fam = taskFamily(task.status);
        var steps = (task.steps || []).map(stepHtml).join('');
        var arts = (task.artifacts || []).map(artifactHtml).join('');
        var stalled = opts.stalled
            ? '<div class="stw-stalled">' +
              esc(at('stw_poll_stopped')) +
              '<button type="button" class="btn sm" data-action="stw-poll-again">' +
              esc(at('stw_poll_refresh')) +
              '</button></div>'
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
            (steps ? '<ul class="stw-steps">' + steps + '</ul>' : '') +
            (arts ? '<div class="stw-arts-hd">' + esc(at('stw_arts_hd')) + '</div>' + arts : '') +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardRender = Object.assign({ panelHtml: panelHtml }, pure);
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
