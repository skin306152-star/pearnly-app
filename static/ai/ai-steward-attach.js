/*
 * Pearnly AI · ai-steward-attach.js · 万能口(F1)附件动作层:选/拖/粘 → 传 → 送出
 *
 * ai-steward.js 已在 500 行预算线上,把「一份料从进浏览器到进后端」这条线抽到这层。
 * 工厂注入钩子,本文件零模块级状态 —— 状态全落在 ai-steward.js 的 S 上(单一事实源),
 * 这里只读写注入进来的那份。上传走 XHR 不走 fetch:只有 xhr.upload.onprogress 报得出
 * 字节级真进度(同 ai-api-upload.js 的理由)。
 *
 * 三条硬规矩:
 *   ① 附上即传,与送出解耦 —— 会计在挑文件的十几秒里,前一批已经传完了;
 *   ② 逐件独立状态机、并发 3 路 —— 一件失败只这一件红,不连坐整批(旧收料口的老坑);
 *   ③ 还在传就不许送 —— 排队送等于把秒回契约改成等 30 秒。
 *
 * hooks 契约:
 *   state()               → S(读 attLimits/api/sessionId/busy · 写 attChips/attPwFor)
 *   getEl(id)             → element|null
 *   renderRight()         重画右窗(附件盘四态与送出闸都在那里)
 *   sendTurn(body, atts)  送出一轮(body 即 POST /messages 的 JSON;atts 上屏用)
 */
(function (root) {
    'use strict';

    var MAX_PARALLEL = 3;

    function create(hooks) {
        var seq = 0;
        var R = function () {
            return AI.stewardAttachRender;
        };

        function chips() {
            var S = hooks.state();
            return (S && S.attChips) || [];
        }

        function view() {
            var S = hooks.state();
            var pwFor = S && S.attPwFor;
            return {
                chips: chips(),
                limits: S && S.attLimits,
                busy: !!(S && S.busy),
                pwChip: pwFor ? byId(pwFor) : null,
            };
        }

        function byId(cid) {
            return chips().filter(function (c) {
                return c.local_id === cid;
            })[0];
        }

        // ── 选文件的当下就判 ────────────────────────────────

        // 逐件按同一份上限累加判据(与后端单批闸同口径)。被拒的也进盘,灰着写明为什么 ——
        // 静默丢掉一件,会计会以为她拖进来的 12 份都传上去了。
        function addFiles(list) {
            var S = hooks.state();
            if (!S || !S.attLimits) return;
            var tally = { count: 0, bytes: 0 };
            chips().forEach(function (c) {
                if (R().chipState(c.state) !== 'rejected') {
                    tally.count += 1;
                    tally.bytes += c.size || 0;
                }
            });
            for (var i = 0; i < list.length; i++) {
                var file = list[i];
                var code = R().rejectCode(file, S.attLimits, tally);
                seq += 1;
                var chip = {
                    local_id: 'a' + seq,
                    name: file.name || '',
                    size: file.size || 0,
                    file: file,
                    state: code ? 'rejected' : 'queued',
                    pct: 0,
                    err: code
                        ? at(R().limitErrKey(code), R().limitErrVars(code, file, S.attLimits))
                        : null,
                    att: null,
                    attachment_id: null,
                };
                if (!code) {
                    tally.count += 1;
                    tally.bytes += chip.size;
                }
                S.attChips.push(chip);
            }
            hooks.renderRight();
            pump();
        }

        // ── 上传 ────────────────────────────────────────────

        function pump() {
            var running = chips().filter(function (c) {
                return c.state === 'uploading';
            }).length;
            chips()
                .filter(function (c) {
                    return c.state === 'queued';
                })
                .slice(0, Math.max(0, MAX_PARALLEL - running))
                .forEach(upload);
        }

        function upload(chip) {
            var S = hooks.state();
            if (!S || !S.sessionId) return;
            chip.state = 'uploading';
            chip.pct = 0;
            chip.err = null;
            hooks.renderRight();
            var session = S;
            S.api
                .uploadStewardAttachments(S.sessionId, [chip.file], chip.password, function (a, b) {
                    if (hooks.state() !== session || chip.state !== 'uploading') return;
                    chip.pct = b > 0 ? Math.round((a / b) * 100) : 0;
                    paintProgress(chip);
                })
                .then(function (resp) {
                    if (hooks.state() !== session) return;
                    var att = ((resp && resp.attachments) || [])[0];
                    // 200 但没给附件行 = 契约漂了。当没传成功处理并留下重传入口,不摆一个
                    // 送出时才发现 id 是空的 ready chip。
                    if (!att) {
                        landFailed(chip, at('stw_att_err_up'));
                        return;
                    }
                    chip.state = 'ready';
                    chip.att = att;
                    chip.attachment_id = att.attachment_id;
                    chip.password = null;
                    hooks.renderRight();
                    pump();
                })
                .catch(function (err) {
                    if (hooks.state() !== session) return;
                    landFailed(chip, errText(err, chip.file), needsPassword(err));
                });
        }

        // 进度条每 XHR 事件重画整个输入条 = 打断正在打字的输入框。只改那一件的 --p。
        function paintProgress(chip) {
            var host = hooks.getEl('stwComposer');
            var bar = host && host.querySelector('[data-chip="' + chip.local_id + '"] .st-bar');
            if (bar) bar.style.setProperty('--p', chip.pct);
        }

        function landFailed(chip, text, askPassword) {
            var S = hooks.state();
            chip.state = 'failed';
            chip.pct = 0;
            chip.err = text;
            if (askPassword && S) S.attPwFor = chip.local_id;
            hooks.renderRight();
            pump();
        }

        // 密码错也要把密码行留着:只认 required 的话,第一次填错之后密码框就再也不出现,
        // 会计唯一的出路是叉掉重拖 —— 而这条线正是为「一叠密码各不相同的银行流水」建的。
        var PASSWORD_CODES = [
            'workorder.intake.pdf_password_required',
            'workorder.intake.pdf_password_wrong',
        ];

        function needsPassword(err) {
            var code = (err && err.detail && err.detail.code) || '';
            return PASSWORD_CODES.indexOf(code) >= 0;
        }

        // 422 的 detail.message 后端已是四语,直接取当前语言印(不再过前端 i18n);
        // 413 与网络级失败才落词条。
        function errText(err, file) {
            var detail = err && err.detail;
            var msg = detail && detail.message;
            if (msg && typeof msg === 'object') {
                var lang = (root.AII18N && root.AII18N.lang) || 'zh';
                if (msg[lang] || msg.zh) return msg[lang] || msg.zh;
            }
            var S = hooks.state();
            var code = err && err.code;
            return at(R().limitErrKey(code), R().limitErrVars(code, file, S && S.attLimits));
        }

        // ── 盘上的动作 ──────────────────────────────────────

        function openPicker() {
            var el = hooks.getEl('stwAttFile');
            if (el) el.click();
        }

        function remove(cid) {
            var S = hooks.state();
            if (!S) return;
            var chip = byId(cid);
            S.attChips = chips().filter(function (c) {
                return c.local_id !== cid;
            });
            if (S.attPwFor === cid) S.attPwFor = null;
            // 已传上去的一并从服务端删(S1 新端点)。失败静默:盘上已经拿掉、送出不会带它,
            // 服务端那份最坏活到 30 天 TTL 清扫 —— 为一次删除失败打断会计不值。
            if (chip && chip.attachment_id) {
                S.api.deleteStewardAttachment(chip.attachment_id).catch(function () {});
            }
            hooks.renderRight();
            pump();
        }

        function retry(cid) {
            var chip = byId(cid);
            if (!chip || chip.state !== 'failed') return;
            // 重传前扔掉上一次那个密码:密码填错时它还留在 chip 上,pump 会拿着同一个错密码
            // 再传一次、回同一个 422,会计只能把这件叉掉重拖一遍。
            chip.password = null;
            requeue(chip);
        }

        function requeue(chip) {
            chip.state = 'queued';
            chip.err = null;
            hooks.renderRight();
            pump();
        }

        // 加密 PDF:密码只随这一件重传上去解密,不落任何本地存储(同收料口口径)。
        function submitPassword(cid) {
            var S = hooks.state();
            var chip = byId(cid);
            var input = hooks.getEl('stwAttPw');
            if (!S || !chip || !input || !input.value || chip.state !== 'failed') return;
            chip.password = input.value;
            S.attPwFor = null;
            requeue(chip);
        }

        // ── 送出 ────────────────────────────────────────────

        // 送出那一刻把 ready 的件从盘里搬进气泡:被拒/失败的留在盘上等处理,不静默带走。
        function submit(text) {
            var S = hooks.state();
            if (!S) return;
            if (!R().canSubmit({ text: text, chips: chips(), busy: S.busy })) return;
            var ids = R().readyIds(chips());
            var taken = chips()
                .filter(function (c) {
                    return c.attachment_id && ids.indexOf(c.attachment_id) >= 0;
                })
                .map(function (c) {
                    return c.att;
                });
            S.attChips = chips().filter(function (c) {
                return ids.indexOf(c.attachment_id) < 0;
            });
            hooks.sendTurn({ text: text, attachment_ids: ids }, taken);
        }

        // 回执卡上的按钮:歧义已被这一次点击解决,参数原样回传(后端那一轮不再过模型)。
        function act(el) {
            var ids = (el.getAttribute('data-aids') || '').split(',').filter(Boolean);
            hooks.sendTurn({
                text: '',
                action: {
                    tool: el.getAttribute('data-tool') || '',
                    attachment_ids: ids,
                    confirm_spend: el.getAttribute('data-spend') === '1',
                },
            });
        }

        // 原件下载:/api/ai/steward/* 只认 Bearer 头,<a href> 发不了自定义头 —— 走 fetch
        // 取 blob 再存盘(同 downloadFinancialsReport 先例)。
        function download(aid) {
            var S = hooks.state();
            if (!S || !aid) return;
            S.api
                .downloadStewardAttachment(aid)
                .then(AI.api.saveBlob)
                .catch(function () {
                    S.errText = at('stw_att_err_dl');
                    hooks.renderRight();
                });
        }

        // ── 三种入口的接线(回形针 / 拖拽 / 粘贴)────────────

        // dragenter/dragleave 在子元素之间穿梭时成对乱飞,用计数器判「整块是不是还被悬停」。
        function wire(host) {
            var depth = 0;
            function paint(on) {
                var el = hooks.getEl('stwDrop');
                if (el) el.hidden = !on;
            }
            host.addEventListener('dragenter', function (e) {
                if (!hasFiles(e)) return;
                e.preventDefault();
                depth += 1;
                paint(true);
            });
            host.addEventListener('dragover', function (e) {
                if (hasFiles(e)) e.preventDefault();
            });
            host.addEventListener('dragleave', function () {
                depth = Math.max(0, depth - 1);
                if (!depth) paint(false);
            });
            host.addEventListener('drop', function (e) {
                if (!hasFiles(e)) return;
                e.preventDefault();
                depth = 0;
                paint(false);
                addFiles(e.dataTransfer.files);
            });
            host.addEventListener('change', function (e) {
                if (e.target && e.target.id === 'stwAttFile' && e.target.files.length) {
                    addFiles(e.target.files);
                    e.target.value = '';
                }
            });
            // 粘贴挂 document:截图刚复制完时焦点常不在输入框上,挂 host 会漏掉一半。
            root.document.addEventListener('paste', function (e) {
                var S = hooks.state();
                var view = hooks.getEl('v-steward');
                if (!S || !S.attLimits || !view || !view.classList.contains('on')) return;
                var files = (e.clipboardData && e.clipboardData.files) || [];
                if (!files.length) return;
                e.preventDefault();
                addFiles(files);
            });
        }

        // 附件盘上的六个动作自己认(ai-steward.js 的 onClick 只转一次手,不逐条抄一遍)。
        function onClick(action, el) {
            var cid = el.getAttribute('data-cid');
            if (action === 'stw-act') act(el);
            else if (action === 'stw-att-pick') openPicker();
            else if (action === 'stw-att-remove') remove(cid);
            else if (action === 'stw-att-retry') retry(cid);
            else if (action === 'stw-att-pw-go') submitPassword(cid);
            else if (action === 'stw-att-dl') download(el.getAttribute('data-aid'));
            else return false;
            return true;
        }

        function hasFiles(e) {
            var types = (e.dataTransfer && e.dataTransfer.types) || [];
            return Array.prototype.indexOf.call(types, 'Files') >= 0;
        }

        return {
            view: view,
            addFiles: addFiles,
            // 会话建好后补一脚:在 sessionId 落地前拖进来的件卡在 queued,没人踢就永远不传。
            resume: pump,
            submit: submit,
            submitPassword: submitPassword,
            onClick: onClick,
            wire: wire,
        };
    }

    var api = { create: create, MAX_PARALLEL: MAX_PARALLEL };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.stewardAttach = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
