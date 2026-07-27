/*
 * Pearnly AI · ai-steward-attach-render.js · 万能口(F1)附件的判据与拼装
 *
 * 「吃任何料文件」的那张嘴长什么样:composer 附件盘四态、用户气泡下的只读原件行、
 * 拖拽落区、回执卡上的闭集动作按钮。
 *
 * 上限一律从 GET /status 的 attachments 块读(单一事实源在 services/steward/attachments),
 * 本层【不硬编码任何数字】——读不到就 normalizeLimits() 返 null,调用方据此整块不给附件口,
 * 而不是拿一份自己编的 20MB 去拒用户的文件。
 *
 * 上半段零 DOM 零 i18n 纯函数(限额规整/选文件当下的拒收判据/四态收敛/送出闸/下载链识别),
 * node(tests/unit/test_ai_steward_attach_render.py)直接 require 断言;下半段拼装依赖全局
 * at() 与 AI.state/AI.statesRender —— 同 ai-states-render.js 的双段先例。
 */
(function (root) {
    'use strict';

    // 本地附件盘的态(不是后端字段):queued/uploading 都是「还在路上」(并发 3 路,排队
    // 的那几件同样不许送出),failed 能重传,rejected 是【选文件的当下】就没传过的那些
    // (灰着,点叉去掉),ready 才进得了送出。集合外的值收敛到 ready 是错的方向,故
    // chipState 只做闭集校验,判「在不在路上」一律走 inFlight。
    var CHIP_STATES = ['queued', 'uploading', 'ready', 'failed', 'rejected'];

    // 料的闭集(services/steward/attach_kinds.ALL_KINDS + 工具产出的 converted)。
    // 集合外的值一律落 unknown —— 「认不出是什么」是诚实,回落成「其他」是假装认过。
    var KINDS = [
        'gl_ledger',
        'bank_statement',
        'sales_summary',
        'vat_report',
        'invoice',
        'unsupported',
        'unknown',
        'converted',
    ];

    // 原件下载要带 Bearer 头(/api/ai/steward/* 只认 Authorization,没有 cookie 会话),
    // <a href> 发不了自定义头 —— 后端给的 deeplink 命中这个前缀就换成走 fetch 的按钮。
    var DOWNLOAD_PREFIX = '/api/ai/steward/attachments/';

    var KB = 1024;
    var MB = 1024 * 1024;

    function posInt(v) {
        var n = Math.floor(Number(v));
        return isFinite(n) && n > 0 ? n : 0;
    }

    // 限额契约规整。任一必需项缺失/非正数 = 这个后端还没有万能口,返 null(调用方不给附件口)。
    function normalizeLimits(raw) {
        if (!raw || typeof raw !== 'object') return null;
        var maxFile = posInt(raw.max_file_bytes);
        var maxBatch = posInt(raw.max_batch_bytes);
        var maxFiles = posInt(raw.max_files);
        var accept = (Array.isArray(raw.accept) ? raw.accept : [])
            .map(function (e) {
                return String(e || '').toLowerCase();
            })
            .filter(Boolean);
        if (!maxFile || !maxBatch || !maxFiles || !accept.length) return null;
        return {
            maxFileBytes: maxFile,
            maxBatchBytes: maxBatch,
            maxFiles: maxFiles,
            accept: accept,
            ttlDays: posInt(raw.ttl_days) || null,
        };
    }

    function extOf(name) {
        var s = String(name == null ? '' : name);
        var dot = s.lastIndexOf('.');
        return dot > 0 ? s.slice(dot).toLowerCase() : '';
    }

    function fmtBytes(n) {
        var v = Number(n);
        if (!isFinite(v) || v < 0) return '';
        if (v >= MB) return (v / MB).toFixed(v >= 10 * MB ? 0 : 1) + ' MB';
        if (v >= KB) return Math.round(v / KB) + ' KB';
        return v + ' B';
    }

    // 长文件名省中间不省尾:尾巴是扩展名与期间号(「…2026-06.xlsx」),砍掉尾巴等于把
    // 「这是哪份料」一起砍了。泰文文件名同理(泰文没有词边界,截前半段读不出东西)。
    function shortName(name, max) {
        var s = String(name == null ? '' : name);
        var cap = max || 34;
        if (s.length <= cap) return s;
        var tail = Math.max(8, Math.floor(cap / 2) - 1);
        return s.slice(0, cap - tail - 1) + '…' + s.slice(s.length - tail);
    }

    function kindKey(kind) {
        return KINDS.indexOf(kind) >= 0 ? 'stw_kind_' + kind : 'stw_kind_unknown';
    }

    function chipState(state) {
        return CHIP_STATES.indexOf(state) >= 0 ? state : 'ready';
    }

    // 【选文件的当下】就拒,不传完再拒:省一次白跑的上传,也让人立刻知道哪一件不行。
    // tally 是这一批已被接受的件数与字节数(逐件累加,与后端单批闸同口径)。
    function rejectCode(file, limits, tally) {
        if (!limits) return 'steward.attachment_closed';
        var size = posInt(file && file.size);
        var count = posInt(tally && tally.count);
        var bytes = posInt(tally && tally.bytes);
        if (!size) return 'steward.attachment_empty';
        if (limits.accept.indexOf(extOf(file && file.name)) < 0)
            return 'steward.attachment_bad_ext';
        if (size > limits.maxFileBytes) return 'steward.attachment_too_large';
        if (count + 1 > limits.maxFiles) return 'steward.attachment_too_many';
        if (bytes + size > limits.maxBatchBytes) return 'steward.attachment_batch_too_large';
        return null;
    }

    function readyIds(chips) {
        return (chips || [])
            .filter(function (c) {
                return c && chipState(c.state) === 'ready' && c.attachment_id;
            })
            .map(function (c) {
                return c.attachment_id;
            });
    }

    // 排队中与传输中都算「在路上」:排队的那几件也没有 attachment_id,送出去等于漏带。
    function inFlight(state) {
        var s = chipState(state);
        return s === 'queued' || s === 'uploading';
    }

    function hasUploading(chips) {
        return (chips || []).some(function (c) {
            return c && inFlight(c.state);
        });
    }

    // 送出闸:还在传就不许送(排队送等于把「秒回」变成等 30 秒 —— 契约不能这么改),
    // 一个字没打且一件 ready 都没有也不许送(后端 422 steward.empty_turn,白跑一次)。
    function canSubmit(ctx) {
        ctx = ctx || {};
        if (ctx.busy || hasUploading(ctx.chips)) return false;
        return String(ctx.text || '').trim().length > 0 || readyIds(ctx.chips).length > 0;
    }

    // 413 的机器码 → 词条 key。422 的 detail.message 后端已给四语,直接印那份,不过这里。
    // 词典守门(test_ai_steward_pure)按这个闭集跑一遍真函数取 key —— 手抄一份后缀清单
    // 就会像首版那样:闸绿着,产品里每条被拒的料都印一串 stw_att_err_attachment_*。
    // 后两条只可能从后端回来(413):zip 解开之后才知道装了多少件,而她手上只有一个压缩包
    // ——「先送出一批再传下一批」那句话对着一个 zip 没法执行,得单说一句拆包的话。
    var REJECT_CODES = [
        'steward.attachment_too_many',
        'steward.attachment_too_large',
        'steward.attachment_batch_too_large',
        'steward.attachment_bad_ext',
        'steward.attachment_empty',
        'steward.attachment_closed',
        'steward.attachment_zip_too_many',
        'steward.attachment_zip_too_large',
    ];

    function limitErrKey(code) {
        if (REJECT_CODES.indexOf(code) < 0) return 'stw_att_err_up';
        return 'stw_att_err_' + String(code).replace('steward.attachment_', '');
    }

    // 后端的原件下载 deeplink → 附件 id(命中才换成带鉴权头的下载按钮;别的深链原样走 <a>)。
    function downloadIdOf(href) {
        var s = String(href == null ? '' : href);
        if (s.indexOf(DOWNLOAD_PREFIX) !== 0) return null;
        var rest = s.slice(DOWNLOAD_PREFIX.length).split('/')[0];
        return /^[A-Za-z0-9-]{8,64}$/.test(rest) ? rest : null;
    }

    // 送出前的附件盘只放人自己传的:artifact 是工具产出(转出来的 xlsx),它属于左窗产物,
    // 冒到 composer 里会让人以为自己传过这份表。
    function trayItems(atts) {
        return (atts || []).filter(function (a) {
            return a && a.status !== 'artifact';
        });
    }

    var pure = {
        CHIP_STATES: CHIP_STATES,
        KINDS: KINDS,
        REJECT_CODES: REJECT_CODES,
        DOWNLOAD_PREFIX: DOWNLOAD_PREFIX,
        normalizeLimits: normalizeLimits,
        extOf: extOf,
        fmtBytes: fmtBytes,
        shortName: shortName,
        kindKey: kindKey,
        chipState: chipState,
        inFlight: inFlight,
        rejectCode: rejectCode,
        readyIds: readyIds,
        hasUploading: hasUploading,
        canSubmit: canSubmit,
        limitErrKey: limitErrKey,
        downloadIdOf: downloadIdOf,
        trayItems: trayItems,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器拼装(依赖 at()/AI.state/AI.statesRender,node 不调用)=====
    if (!root || typeof root.document === 'undefined') return;

    function esc(s) {
        return AI.state.esc(s);
    }

    // chip 副行:认成什么 + 页数。kind_source=unknown 时必须写「认不出是什么」——
    // 这一行是会计判断「管家有没有会错意」的唯一线索,回落成一个像样的类型名就是骗人。
    function chipMetaHtml(att) {
        if (!att) return '';
        var parts = [at(kindKey(att.kind))];
        var pages = Number(att.page_count);
        if (isFinite(pages) && pages > 0) parts.push(at('stw_att_pages', { n: pages }));
        if (att.needs_model) parts.push(at('stw_att_needs_model'));
        return '<div class="stw-chip-meta">' + esc(parts.join(' · ')) + '</div>';
    }

    function chipFootHtml(chip) {
        var state = chipState(chip.state);
        if (inFlight(state)) {
            return (
                '<div class="stw-chip-foot">' +
                AI.statesRender.barHtml('run', chip.pct || 0) +
                '</div>'
            );
        }
        if (state === 'failed') {
            return (
                '<div class="stw-chip-foot">' +
                AI.statesRender.badgeHtml('err', at('stw_att_failed')) +
                '<button type="button" class="stw-linkbtn" data-action="stw-att-retry" ' +
                'data-cid="' +
                esc(chip.local_id) +
                '">' +
                esc(at('stw_att_retry')) +
                '</button></div>' +
                (chip.err ? '<div class="stw-chip-err">' + esc(chip.err) + '</div>' : '')
            );
        }
        if (state === 'rejected') {
            return (
                '<div class="stw-chip-foot">' +
                AI.statesRender.badgeHtml('off', at('stw_att_rejected')) +
                '</div>' +
                (chip.err ? '<div class="stw-chip-err">' + esc(chip.err) + '</div>' : '')
            );
        }
        return chipMetaHtml(chip.att);
    }

    function chipHtml(chip) {
        var state = chipState(chip.state);
        return (
            '<li class="stw-att-chip ' +
            state +
            '" data-chip="' +
            esc(chip.local_id) +
            '"><div class="stw-chip-hd"><span class="stw-chip-n" title="' +
            esc(chip.name) +
            '">' +
            esc(shortName(chip.name)) +
            '</span><span class="stw-chip-sz">' +
            esc(fmtBytes(chip.size)) +
            '</span><button type="button" class="stw-chip-x" data-action="stw-att-remove" ' +
            'data-cid="' +
            esc(chip.local_id) +
            '" aria-label="' +
            esc(at('stw_att_remove')) +
            '">×</button></div>' +
            chipFootHtml(chip) +
            '</li>'
        );
    }

    // 加密 PDF 的密码框:后端 422 pdf_password_required 时就地长出来,填完重传这一件。
    // 不做成弹窗 —— 会计手上常有一叠密码不同的银行流水,弹窗会打断她逐件处理的节奏。
    function passwordRowHtml(chip) {
        return (
            '<div class="stw-att-pw"><label for="stwAttPw">' +
            esc(at('stw_att_pw_hint', { name: shortName(chip.name, 24) })) +
            '</label><div class="stw-bar-row"><input id="stwAttPw" class="stw-bar-input" ' +
            'type="password" autocomplete="off" placeholder="' +
            esc(at('stw_att_pw_ph')) +
            '" /><button type="button" class="btn sm" data-action="stw-att-pw-go" data-cid="' +
            esc(chip.local_id) +
            '">' +
            esc(at('stw_att_pw_go')) +
            '</button></div></div>'
        );
    }

    function trayHtml(ctx) {
        ctx = ctx || {};
        var chips = ctx.chips || [];
        var pw = ctx.pwChip ? passwordRowHtml(ctx.pwChip) : '';
        if (!chips.length && !pw) return '';
        return (
            '<div class="stw-att-tray">' +
            (chips.length
                ? '<ul class="stw-att-list">' + chips.map(chipHtml).join('') + '</ul>'
                : '') +
            pw +
            '</div>'
        );
    }

    // 回形针图标走内联 SVG(整站禁 emoji 当图标,见 ui_design_lint 棘轮闸)。
    var CLIP_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M21 11.5l-8.6 8.6a5 5 0 0 1-7-7l8.6-8.6a3.3 3.3 0 0 1 4.7 4.7l-8.6 8.6a1.7 ' +
        '1.7 0 0 1-2.4-2.4l7.9-7.9"/></svg>';

    // 限额读不到(老后端/契约漂了)就整个不给口 —— 给一个点了必失败的按钮更糟。
    function pickerHtml(ctx) {
        ctx = ctx || {};
        if (!ctx.limits) return '';
        return (
            '<button type="button" class="stw-clip" data-action="stw-att-pick"' +
            (ctx.busy ? ' disabled' : '') +
            ' title="' +
            esc(at('stw_att_pick')) +
            '" aria-label="' +
            esc(at('stw_att_pick')) +
            '">' +
            CLIP_SVG +
            '</button><input id="stwAttFile" class="stw-att-file" type="file" multiple accept="' +
            esc(ctx.limits.accept.join(',')) +
            '" />'
        );
    }

    // 用户气泡下的只读原件行:传进来的原件永久留在那条消息下,随时点开下载(只有自己下得到)。
    function bubbleFilesHtml(atts) {
        var list = atts || [];
        if (!list.length) return '';
        return (
            '<div class="stw-msg-files">' +
            list
                .map(function (a) {
                    return (
                        '<button type="button" class="stw-file-pill" data-action="stw-att-dl" ' +
                        'data-aid="' +
                        esc(a.attachment_id || '') +
                        '" title="' +
                        esc(a.name || '') +
                        '"><span class="stw-file-n">' +
                        esc(shortName(a.name, 26)) +
                        '</span><span class="stw-file-k">' +
                        esc(at(kindKey(a.kind))) +
                        '</span></button>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function dropOverlayHtml() {
        return (
            '<div class="stw-drop" id="stwDrop" hidden><div class="stw-drop-in">' +
            esc(at('stw_att_drop_t')) +
            '<span>' +
            esc(at('stw_att_drop_s')) +
            '</span></div></div>'
        );
    }

    // 回执卡上的闭集动作按钮(artifacts kind="actions")。label 后端已按语言渲好,直接当
    // 按钮文字;会过模型的那条标出来(点了才烧钱,不静默)。终态任务把按钮置灰:卡已经死了,
    // 点下去只会拿到一个「这轮不认」的错。
    function actionsHtml(art, opts) {
        var list = (art && art.actions) || [];
        if (!list.length) return '';
        var dead = !!(opts && opts.dead);
        return (
            '<div class="stw-acts">' +
            list
                .map(function (a) {
                    var cost = (a && a.cost) || {};
                    var note = cost.model_call
                        ? '<span class="stw-act-note">' + esc(at('stw_act_model')) + '</span>'
                        : '';
                    return (
                        '<button type="button" class="btn pri sm stw-act" data-action="stw-act" ' +
                        'data-tool="' +
                        esc(a.tool || '') +
                        '" data-aids="' +
                        esc((a.attachment_ids || []).join(',')) +
                        '" data-spend="' +
                        (a.confirm_spend ? '1' : '0') +
                        '"' +
                        (dead ? ' disabled' : '') +
                        '>' +
                        esc(a.label || '') +
                        note +
                        '</button>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.stewardAttachRender = Object.assign(
        {
            trayHtml: trayHtml,
            pickerHtml: pickerHtml,
            bubbleFilesHtml: bubbleFilesHtml,
            dropOverlayHtml: dropOverlayHtml,
            actionsHtml: actionsHtml,
        },
        pure
    );
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
