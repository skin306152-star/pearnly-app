/*
 * Pearnly AI · ai-purge.js · 按账套清空数据(客户页「清除数据」按钮)
 *
 * 三步:选账套 → 看清警告后确认 → 跑清除。清除走 NDJSON 流式端点
 * (POST /api/workspace/clients/{id}/purge),读一行画一格 —— 进度是真到了第几张表,
 * 不是定时器编出来的假动画。跑完回调让客户页重拉列表。
 *
 * 模态外壳复用 .pkg-mask/.pkg-modal(ai-pkg.css · 同 ai-client-import.js 先例),
 * 不为这一个弹窗再画一套。不可撤销,所以确认步单独一屏,不跟选择挤在一起。
 *
 * 依赖全局 at() 与 AI.state.esc / AI.token,排在 ai-clients.js 之前加载。
 */
(function () {
    'use strict';

    var MASK_ID = 'purgeMask';
    var S = null;

    function esc(s) {
        return AI.state.esc(s);
    }

    function mask() {
        return document.getElementById(MASK_ID);
    }

    function close() {
        var el = mask();
        if (el) el.remove();
        S = null;
    }

    function pickHtml() {
        var rows = (S.clients || [])
            .map(function (c) {
                return (
                    '<label class="pg-opt"><input type="radio" name="pg-ws" value="' +
                    esc(c.id) +
                    '"><span><b>' +
                    esc(c.name) +
                    '</b><small>' +
                    esc(c.tax_id || at('purge_no_tax')) +
                    '</small></span></label>'
                );
            })
            .join('');
        return (
            '<div class="pg-list">' +
            (rows || '<div class="pg-empty">' + esc(at('purge_no_client')) + '</div>') +
            '</div>' +
            '<div class="pkg-actions"><button type="button" class="btn" data-action="pg-close">' +
            esc(at('purge_cancel')) +
            '</button><button type="button" class="btn pri" data-action="pg-next" disabled>' +
            esc(at('purge_next')) +
            '</button></div>'
        );
    }

    function confirmHtml() {
        var c = S.picked || {};
        return (
            '<div class="pg-warn">' +
            esc(at('purge_warn_title')) +
            '</div>' +
            '<div class="pg-target"><b>' +
            esc(c.name) +
            '</b><small>' +
            esc(c.tax_id || at('purge_no_tax')) +
            '</small></div>' +
            '<p class="pg-note">' +
            esc(at('purge_warn_body')) +
            '</p>' +
            '<div class="pkg-actions"><button type="button" class="btn" data-action="pg-back">' +
            esc(at('purge_back')) +
            '</button><button type="button" class="btn pg-danger" data-action="pg-run">' +
            esc(at('purge_confirm')) +
            '</button></div>'
        );
    }

    function runningHtml() {
        return (
            '<div class="pg-bar"><i id="pgBarFill"></i></div>' +
            '<div class="pg-status" id="pgStatus">' +
            esc(at('purge_running')) +
            '</div>'
        );
    }

    function doneHtml() {
        var r = S.result || {};
        var leftover = (r.leftover || []).length;
        return (
            '<div class="pg-done">' +
            esc(leftover ? at('purge_done_partial') : at('purge_done')) +
            '</div>' +
            '<div class="pg-status">' +
            esc(
                at('purge_done_stat')
                    .replace('{rows}', String(r.deleted_total || 0))
                    .replace('{files}', String(r.files_removed || 0))
            ) +
            '</div>' +
            (leftover
                ? '<p class="pg-note pg-leftover">' +
                  esc(at('purge_leftover').replace('{tables}', (r.leftover || []).join(', '))) +
                  '</p>'
                : '') +
            '<div class="pkg-actions"><button type="button" class="btn pri" data-action="pg-finish">' +
            esc(at('purge_finish')) +
            '</button></div>'
        );
    }

    function bodyHtml() {
        if (S.step === 'confirm') return confirmHtml();
        if (S.step === 'running') return runningHtml();
        if (S.step === 'done') return doneHtml();
        return pickHtml();
    }

    function render() {
        var el = mask();
        if (!el) return;
        el.querySelector('.pg-body').innerHTML = bodyHtml();
    }

    function modalHtml() {
        return (
            '<div class="pkg-mask on" id="' +
            MASK_ID +
            '"><div class="pkg-modal pg-modal" role="dialog" aria-modal="true">' +
            '<div class="mh"><div><h3>' +
            esc(at('purge_title')) +
            '</h3><p>' +
            esc(at('purge_hint')) +
            '</p></div>' +
            '<button class="mclose" type="button" data-action="pg-close" aria-label="' +
            esc(at('purge_cancel')) +
            '">&times;</button></div>' +
            '<div class="mb pg-body" style="grid-template-columns: 1fr">' +
            bodyHtml() +
            '</div></div></div>'
        );
    }

    function setProgress(evt) {
        var fill = document.getElementById('pgBarFill');
        var status = document.getElementById('pgStatus');
        if (fill && evt.total) {
            fill.style.width = Math.round((evt.done / evt.total) * 100) + '%';
        }
        if (status && evt.label) {
            status.textContent = at('purge_progress')
                .replace('{done}', String(evt.done))
                .replace('{total}', String(evt.total))
                .replace('{table}', evt.label);
        }
    }

    function handle(line) {
        if (!line.trim()) return;
        var evt;
        try {
            evt = JSON.parse(line);
        } catch (e) {
            return;
        }
        if (evt.step === 'finished') {
            S.result = evt;
            S.step = 'done';
            render();
            if (S.onDone) S.onDone();
            return;
        }
        setProgress(evt);
    }

    // NDJSON:一行一个事件。按行切分,最后一段可能是半行,留到下一块再拼。
    // flush=true(流已结束)时把残段也当完整一行处理 —— 末行没带换行符就丢掉的话,
    // finished 事件永远收不到,弹窗会一直停在「正在清除…」。
    function consume(text, carry, flush) {
        var lines = (carry + text).split('\n');
        var rest = lines.pop();
        lines.forEach(handle);
        if (flush && rest) {
            handle(rest);
            return '';
        }
        return rest;
    }

    function run() {
        S.step = 'running';
        render();
        var token = AI.token.get();
        window
            .fetch('/api/workspace/clients/' + encodeURIComponent(S.picked.id) + '/purge', {
                method: 'POST',
                headers: token ? { Authorization: 'Bearer ' + token } : {},
            })
            .then(function (r) {
                if (!r.ok || !r.body) throw new Error('purge_failed');
                var reader = r.body.getReader();
                var decoder = new TextDecoder();
                var carry = '';
                function pump() {
                    return reader.read().then(function (chunk) {
                        if (chunk.done) {
                            consume('', carry, true);
                            return;
                        }
                        carry = consume(
                            decoder.decode(chunk.value, { stream: true }),
                            carry,
                            false
                        );
                        return pump();
                    });
                }
                return pump();
            })
            .catch(function () {
                var status = document.getElementById('pgStatus');
                if (status) status.textContent = at('purge_failed');
            });
    }

    function onClick(e) {
        var radio = e.target.closest('input[name="pg-ws"]');
        if (radio) {
            S.picked = (S.clients || []).filter(function (c) {
                return String(c.id) === String(radio.value);
            })[0];
            var next = mask().querySelector('[data-action="pg-next"]');
            if (next) next.disabled = !S.picked;
            return;
        }
        var act = e.target.closest('[data-action]');
        if (!act) return;
        var name = act.getAttribute('data-action');
        if (name === 'pg-close') return close();
        if (name === 'pg-next' && S.picked) {
            S.step = 'confirm';
            return render();
        }
        if (name === 'pg-back') {
            S.step = 'pick';
            return render();
        }
        if (name === 'pg-run') return run();
        if (name === 'pg-finish') return close();
    }

    // clients:[{id,name,tax_id}] · onDone:清完回调(客户页重拉列表)
    function open(clients, onDone) {
        close();
        S = { clients: clients || [], picked: null, step: 'pick', result: null, onDone: onDone };
        var host = document.createElement('div');
        host.innerHTML = modalHtml();
        var el = host.firstChild;
        document.body.appendChild(el);
        el.addEventListener('click', onClick);
    }

    window.AI = window.AI || {};
    window.AI.purge = { open: open, close: close };
})();
