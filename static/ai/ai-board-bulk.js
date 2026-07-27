/*
 * Pearnly AI · ai-board-bulk.js · 看板批量开单(选择态 + 浮出操作条 + 执行)
 *
 * 从矩阵搬来的唯一批量动作(2026-07-27 · 矩阵那边照旧保留):对勾选的「本期缺单客户」逐个调
 * 既有 POST /api/workorder/orders(幂等开单,后端零改),Promise.allSettled 收尾——
 * 失败的允许重选重试,幂等不会重复开单。勾选框只长在「本期缺单」条上(见
 * ai-board-tools-render.js::missingStripHtml),已开单的卡不给勾选框。
 *
 * 选择态存在本模块(不存 DOM):看板会因开单/轮询整块重渲染,存 DOM 的勾选会随之丢。
 * 重渲染后调 sync() 把已消失的客户从选择集里摘掉,不留幽灵选中项。
 */
(function () {
    'use strict';

    var S = {
        selected: {}, // clientId(字符串) → true
        note: '', // 上一次批量执行的结果文案(已翻译),下次改选即清
        busy: false,
        wired: false,
        ctx: null, // { bar, body, getApi, getPeriod, onDone }
    };

    function esc(s) {
        return AI.state.esc(s);
    }

    function selectedIds() {
        return Object.keys(S.selected);
    }

    function renderBar() {
        var bar = S.ctx.bar;
        var n = selectedIds().length;
        if (!n && !S.note) {
            bar.style.display = 'none';
            bar.innerHTML = '';
            return;
        }
        bar.style.display = '';
        bar.innerHTML = n
            ? AI.boardTools.bulkBarHtml({
                  count: n,
                  period: S.ctx.getPeriod(),
                  busy: S.busy,
                  note: S.note,
              })
            : '<span class="kb-bulk-note">' + esc(S.note) + '</span>';
    }

    // 重渲染后:选择集只保留仍在看板上的客户(开完单的卡不再有勾选框),再把勾选态
    // 回写到新 DOM 上——不回写的话选择集与用户看到的勾选框会当场打架。
    function sync() {
        var live = {};
        S.ctx.body.querySelectorAll('.kb-check').forEach(function (el) {
            var id = el.getAttribute('data-client-id');
            live[id] = true;
            el.checked = !!S.selected[id];
        });
        Object.keys(S.selected).forEach(function (id) {
            if (!live[id]) delete S.selected[id];
        });
        renderBar();
    }

    function clear() {
        S.selected = {};
        S.note = '';
        sync();
    }

    function resultNote(ok, fail) {
        var msg = at('kb_bulk_result_ok', { n: ok });
        if (fail > 0) msg += ' · ' + at('kb_bulk_result_fail', { n: fail });
        return msg;
    }

    function runBulk() {
        var ids = selectedIds();
        if (!ids.length || S.busy) return;
        var api = S.ctx.getApi();
        var period = S.ctx.getPeriod();
        S.busy = true;
        S.note = '';
        renderBar();
        Promise.allSettled(
            ids.map(function (id) {
                return api.createOrder({
                    workspace_client_id: Number(id),
                    period: period,
                    intent: 'monthly_vat',
                });
            })
        ).then(function (results) {
            var ok = results.filter(function (r) {
                return r.status === 'fulfilled';
            }).length;
            S.busy = false;
            S.selected = {};
            S.note = resultNote(ok, results.length - ok);
            renderBar();
            S.ctx.onDone();
        });
    }

    function wire() {
        S.ctx.body.addEventListener('change', function (e) {
            if (!e.target.classList || !e.target.classList.contains('kb-check')) return;
            var id = e.target.getAttribute('data-client-id');
            if (e.target.checked) S.selected[id] = true;
            else delete S.selected[id];
            S.note = '';
            renderBar();
        });
        // 勾选框在卡片里而卡片整体点击=进客户页,"勾选不把人导航走"由 ai-kanban-render.js
        // 的 activate() 统一让路(同一容器上的两个 click 监听器,stopPropagation 拦不住彼此)。
        S.ctx.bar.addEventListener('click', function (e) {
            if (e.target.closest('[data-action="bulk-clear"]')) clear();
            else if (e.target.closest('[data-action="bulk-open"]')) runBulk();
        });
    }

    // ctx.getPeriod() 给的是矩阵响应里的当期(批量开单开的就是这一期,按钮文案上写明);
    // ctx.onDone() 由调用方刷新整块看板。
    function mount(ctx) {
        S.ctx = ctx;
        if (!S.wired) {
            wire();
            S.wired = true;
        }
        sync();
    }

    window.AI = window.AI || {};
    window.AI.boardBulk = { mount: mount, sync: sync, clear: clear };
})();
