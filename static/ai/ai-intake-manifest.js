/*
 * Pearnly AI · ai-intake-manifest.js · IN-0b 收料诚实盘点(文件夹展平/队列态/盘点条+密码卡+
 * 续传横幅的纯逻辑与 HTML 拼装)
 *
 * 上半段(classifyFolderEntry/flattenFileTree/zipExpandedCount/serializeQueueState/
 * parseQueueState/hasResumableQueue)零 DOM 依赖,node(tests/unit/test_ai_pure_modules.py)
 * 直接 require 断言;下半段 HTML 拼装依赖 at()/AI.state.esc,只在浏览器根挂载(同
 * ai-client-import-render.js 的双段先例——guard 只判 root 是否存在,node 里 root=globalThis
 * 也是 truthy,配合测试里 stub 的 global.at/global.AI.state.esc 可直接跑)。
 *
 * 真正联网的批传/隔离重试/密码序列在 ai-intake-queue.js(排在本文件之后加载);
 * DOM 事件接线在 ai-intake.js。三者分工同 ai-recon-render/ai-recon 先例。
 */
(function (root) {
    'use strict';

    // 文件夹拖入(webkitGetAsEntry)绕过 <input accept>,同一份白名单在此把关——与后端
    // intake_prep._MEDIA_EXTS ∪ zip/xlsx/xls 同口径,内容级问题(密码/损坏/伪扩展名)
    // 留给后端权威判定,本层只挡两类前端就能确定的:空文件与扩展名不在白名单内。
    var ALLOWED_EXTS = [
        '.jpg',
        '.jpeg',
        '.png',
        '.gif',
        '.webp',
        '.tif',
        '.tiff',
        '.bmp',
        '.heic',
        '.heif',
        '.pdf',
        '.zip',
        '.xlsx',
        '.xls',
    ];

    function extOf(name) {
        var i = (name || '').lastIndexOf('.');
        return i >= 0 ? name.slice(i).toLowerCase() : '';
    }

    // 单件分类:0 字节 → reason_empty;扩展名不在白名单 → reason_unsupported;其余放行。
    function classifyFolderEntry(file) {
        if (!file || !file.size) return { ok: false, reasonKey: 'intake_reason_empty' };
        if (ALLOWED_EXTS.indexOf(extOf(file.name)) < 0) {
            return { ok: false, reasonKey: 'intake_reason_unsupported' };
        }
        return { ok: true };
    }

    // 目录树递归展平:node 形如 {name, isDir, size, children:[...]}——orchestration 层把
    // 真实 FileSystemEntry(webkitGetAsEntry 异步遍历产物)转成这种可序列化纯对象再喂给
    // 本函数,含任意深度子目录;子目录本身不算「不支持」,只递归展开其叶子件。
    function flattenFileTree(node) {
        var files = [];
        var rejected = [];
        function walk(n) {
            if (!n) return;
            if (n.isDir) {
                (n.children || []).forEach(walk);
                return;
            }
            var v = classifyFolderEntry(n);
            if (v.ok) files.push(n);
            else rejected.push({ name: n.name, reasonKey: v.reasonKey });
        }
        (Array.isArray(node) ? node : [node]).forEach(walk);
        return { files: files, rejected: rejected };
    }

    // zip 解出件数估算:一批里非 zip 输入件必产出恰好 1 个登记项(HEIC 也只登记转换后的
    // 那 1 件),故 registeredCount 超出「非 zip 输入件数」的部分就是 zip 展开贡献的——
    // 幂等去重命中时可能拉低 registeredCount,clamp 到 0 不报负数。
    function zipExpandedCount(batchFiles, registeredCount) {
        var files = batchFiles || [];
        var zipCount = files.filter(function (f) {
            return extOf(f.name) === '.zip';
        }).length;
        var nonZipCount = files.length - zipCount;
        var extra = (registeredCount || 0) - nonZipCount;
        return extra > 0 ? extra : 0;
    }

    // 队列态持久化(A10/A11 队列续传):落 localStorage 的纯净可序列化形态,只留文件名
    // (File 对象含二进制,浏览器刷新后本就拿不回原字节——诚实的续传是「告诉用户还差
    // 哪些名字」,不是假装能悄悄续传字节流)。orchestration 层负责实际读写 localStorage。
    function serializeQueueState(state) {
        return JSON.stringify({
            orderId: state.orderId,
            total: state.total || 0,
            doneNames: state.doneNames || [],
            pendingNames: state.pendingNames || [],
            failedNames: state.failedNames || [],
            ts: state.ts || Date.now(),
        });
    }

    function parseQueueState(raw) {
        if (!raw) return null;
        var v;
        try {
            v = JSON.parse(raw);
        } catch (e) {
            return null;
        }
        if (!v || typeof v !== 'object' || !v.orderId) return null;
        return {
            orderId: String(v.orderId),
            total: Number(v.total) || 0,
            doneNames: Array.isArray(v.doneNames) ? v.doneNames : [],
            pendingNames: Array.isArray(v.pendingNames) ? v.pendingNames : [],
            failedNames: Array.isArray(v.failedNames) ? v.failedNames : [],
            ts: Number(v.ts) || 0,
        };
    }

    function hasResumableQueue(state) {
        return !!(state && (state.pendingNames.length || state.failedNames.length));
    }

    var pure = {
        ALLOWED_EXTS: ALLOWED_EXTS,
        classifyFolderEntry: classifyFolderEntry,
        flattenFileTree: flattenFileTree,
        zipExpandedCount: zipExpandedCount,
        serializeQueueState: serializeQueueState,
        parseQueueState: parseQueueState,
        hasResumableQueue: hasResumableQueue,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为 HTML 拼装(依赖 at()/AI.state.esc,guard 只判 root)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    // 拒收原因文案:服务端结构化件(message 四语内嵌,IN-0a 契约「前端直出不再自翻」)
    // 优先;客户端分类件(reasonKey 走本地 i18n)兜底。
    function reasonText(item) {
        if (item.message) {
            var lang = (root.AII18N && root.AII18N.lang) || 'en';
            return item.message[lang] || item.message.en || item.reasonKey || '';
        }
        return at(item.reasonKey || 'err_generic');
    }

    // 盘点条:每次投料结束(或进行中)出——收进 N 件 / 拒收 M 件(逐件点名)/ zip 解出 K 件。
    // 三者皆零才不渲染(不假成功,也不为空跑一次凭空出个「盘点」壳)。
    function manifestHtml(manifest) {
        if (!manifest) return '';
        var accepted = manifest.accepted || 0;
        var rejected = manifest.rejected || [];
        var zipExpanded = manifest.zipExpanded || 0;
        if (!accepted && !rejected.length && !zipExpanded) return '';
        var chips = [
            '<span class="chip g">' +
                esc(at('intake_manifest_accepted_n', { n: accepted })) +
                '</span>',
        ];
        if (rejected.length) {
            chips.push(
                '<span class="chip b">' +
                    esc(at('intake_manifest_rejected_n', { n: rejected.length })) +
                    '</span>'
            );
        }
        if (zipExpanded) {
            chips.push(
                '<span class="chip n">' +
                    esc(at('intake_manifest_zip_n', { n: zipExpanded })) +
                    '</span>'
            );
        }
        var rows = rejected
            .map(function (item) {
                return (
                    '<tr><td>' + esc(item.name) + '</td><td>' + esc(reasonText(item)) + '</td></tr>'
                );
            })
            .join('');
        var table = rejected.length
            ? '<div class="mx-scroll"><table class="mx-table"><tbody>' +
              rows +
              '</tbody></table></div>'
            : '';
        return (
            '<div class="panel manifest-card"><div class="hd"><h3>' +
            esc(at('intake_manifest_title')) +
            '</h3></div><div class="bd">' +
            '<div class="ci-counts">' +
            chips.join('') +
            '</div>' +
            table +
            '</div></div>'
        );
    }

    // 密码 PDF 供钥卡:四语,输入密码重传同文件;错密码走同一张卡重试(errKey='wrong'
    // 换一句提示);跳过=该件转拒收,不阻塞其余批次。
    function passwordCardHtml(ctx) {
        if (!ctx) return '';
        var err = ctx.errKey
            ? '<div class="intake-err">' + esc(at('intake_pw_wrong')) + '</div>'
            : '';
        return (
            '<div class="panel pw-card"><div class="hd"><h3>' +
            esc(at('intake_pw_title', { name: ctx.filename })) +
            '</h3></div><div class="bd">' +
            '<p class="needs-sub">' +
            esc(at('intake_pw_hint')) +
            '</p>' +
            '<form class="sales-form" id="ikPwForm" novalidate>' +
            '<input class="sf-in" id="ikPwInput" type="password" autocomplete="off" placeholder="' +
            esc(at('intake_pw_input_ph')) +
            '">' +
            err +
            '<div class="sf-btns">' +
            '<button type="submit" class="btn pri" data-action="ik-pw-submit">' +
            esc(at('intake_pw_submit')) +
            '</button>' +
            '<button type="button" class="btn" data-action="ik-pw-skip">' +
            esc(at('intake_pw_skip')) +
            '</button></div></form></div></div>'
        );
    }

    // 续传横幅:刷新页面后,若上次投料还有未完成/失败的文件名,提示用户重新选择继续
    // (浏览器 File 无法跨刷新持久,诚实告知差哪些名字,不假装能自动续传字节)。
    function resumeBannerHtml(state) {
        if (!state) return '';
        var remaining = state.pendingNames.length + state.failedNames.length;
        if (!remaining) return '';
        return (
            '<div class="panel needs-card resume-card"><div class="bd">' +
            '<p class="needs-sub">' +
            esc(at('intake_resume_body', { n: remaining, total: state.total })) +
            '</p>' +
            '<div class="needs-paths">' +
            '<button class="btn pri" data-action="ik-resume-pick">' +
            esc(at('intake_resume_continue')) +
            '</button>' +
            '<button class="btn" data-action="ik-resume-dismiss">' +
            esc(at('intake_resume_dismiss')) +
            '</button></div></div></div>'
        );
    }

    // 失败批横幅(网络级失败,非内容拒收):一键只重传这一批,不牵连已成功/尚未发出的批。
    function failedBatchesHtml(batches) {
        if (!batches || !batches.length) return '';
        var n = batches.reduce(function (s, b) {
            return s + b.files.length;
        }, 0);
        return (
            '<div class="panel needs-card"><div class="bd">' +
            '<p class="needs-sub">' +
            esc(at('intake_failed_batch_n', { n: n })) +
            '</p>' +
            '<button class="btn pri" data-action="ik-retry-failed">' +
            esc(at('intake_retry_failed')) +
            '</button></div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.intakeManifest = {
        ALLOWED_EXTS: ALLOWED_EXTS,
        classifyFolderEntry: classifyFolderEntry,
        flattenFileTree: flattenFileTree,
        zipExpandedCount: zipExpandedCount,
        serializeQueueState: serializeQueueState,
        parseQueueState: parseQueueState,
        hasResumableQueue: hasResumableQueue,
        manifestHtml: manifestHtml,
        passwordCardHtml: passwordCardHtml,
        resumeBannerHtml: resumeBannerHtml,
        failedBatchesHtml: failedBatchesHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
