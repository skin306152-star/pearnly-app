/*
 * Pearnly AI · ai-intake-queue.js · IN-0b 收料队列联网编排:文件夹拖入递归展开、批级
 * 隔离重试(整批 422 只点名一个坏件 → 拿掉重传其余)、密码 PDF 串行确认、队列态持久化。
 *
 * 依赖 window.AI.api(addMaterials 带 password)/AI.intakeRender(splitBatches)/
 * AI.intakeManifest(flattenFileTree 等纯逻辑),排在三者之后、ai-intake.js(DOM 事件接线,
 * 唯一调用方)之前加载。本文件不碰 DOM,只管网络时序与 localStorage,故不必挂
 * window.AI.state.esc 那一套——纯编排层,同 ai-intake-bank-sales.js 的分工先例。
 */
(function () {
    'use strict';

    var QUEUE_KEY_PREFIX = 'pearnly_ai_intake_queue_';

    function names(files) {
        return (files || []).map(function (f) {
            return f.name;
        });
    }

    // ============ 队列态持久化(A10/A11 队列续传) ============

    function saveQueueState(orderId, partial) {
        try {
            var raw = AI.intakeManifest.serializeQueueState(
                Object.assign({ orderId: orderId }, partial)
            );
            localStorage.setItem(QUEUE_KEY_PREFIX + orderId, raw);
        } catch (e) {
            /* localStorage 不可用(隐私模式等)不阻断上传,只是刷新后无法提示续传 */
        }
    }

    function loadQueueState(orderId) {
        try {
            var raw = localStorage.getItem(QUEUE_KEY_PREFIX + orderId);
            var state = AI.intakeManifest.parseQueueState(raw);
            return state && state.orderId === String(orderId) ? state : null;
        } catch (e) {
            return null;
        }
    }

    function clearQueueState(orderId) {
        try {
            localStorage.removeItem(QUEUE_KEY_PREFIX + orderId);
        } catch (e) {
            /* 同上,读写失败不影响上传主流程 */
        }
    }

    // ============ 文件夹拖入:webkitGetAsEntry 递归展开(含任意深度子目录) ============

    // Chrome 等浏览器 readEntries() 单次最多回 ~100 条,须反复调用直到空数组才算读完
    // 一层目录(FileSystemDirectoryReader 的既定契约,非本层臆造)。
    function readAllEntries(reader) {
        return new Promise(function (resolve, reject) {
            var all = [];
            function readBatch() {
                reader.readEntries(function (entries) {
                    if (!entries.length) {
                        resolve(all);
                        return;
                    }
                    all = all.concat(entries);
                    readBatch();
                }, reject);
            }
            readBatch();
        });
    }

    // 真实 FileSystemEntry → 纯对象节点(name/isDir/size/children/_file),供
    // AI.intakeManifest.flattenFileTree 同步分类(异步遍历与同步分类分层,后者才是
    // node 可测的那部分——见该文件顶注)。读文件失败(权限/已被移动)按 0 字节记,
    // 交 flattenFileTree 的 reason_empty 诚实拒收,不静默丢弃整个节点。
    function entryToNode(entry) {
        if (entry.isFile) {
            return new Promise(function (resolve) {
                entry.file(
                    function (file) {
                        resolve({ isDir: false, name: file.name, size: file.size, _file: file });
                    },
                    function () {
                        resolve({ isDir: false, name: entry.name, size: 0, _file: null });
                    }
                );
            });
        }
        if (entry.isDirectory) {
            return readAllEntries(entry.createReader()).then(function (entries) {
                return Promise.all(entries.map(entryToNode)).then(function (children) {
                    return { isDir: true, name: entry.name, children: children };
                });
            });
        }
        return Promise.resolve(null);
    }

    // 拖入的 DataTransferItemList → {files:[File...], rejected:[{name,reasonKey}]}。
    // 无可用 entry(极旧浏览器)返回 null,调用方回落到既有 dataTransfer.files 直传路径。
    function walkDataTransferItems(items) {
        var list = Array.prototype.slice.call(items || []);
        var entries = list
            .map(function (it) {
                return it.webkitGetAsEntry && it.webkitGetAsEntry();
            })
            .filter(Boolean);
        if (!entries.length) return Promise.resolve(null);
        return Promise.all(entries.map(entryToNode)).then(function (nodes) {
            var flat = AI.intakeManifest.flattenFileTree(nodes);
            return {
                files: flat.files
                    .map(function (n) {
                        return n._file;
                    })
                    .filter(Boolean),
                rejected: flat.rejected,
            };
        });
    }

    // ============ 批级隔离重试(整批 422 只点名一个坏件) ============

    // 两段法契约(IN-0a):单批 422 时该批零落盘,故拿掉点名的那一件重传其余是安全的
    // ——不会把已落盘的成功件又送一遍。密码类错误串行转给 onPasswordNeeded 决议
    // (Promise 挂起等用户输入/跳过,不影响其它已排队批次的先后顺序)。
    function handleReject(api, orderId, files, detail, onOutcome, onPasswordNeeded) {
        var idx = -1;
        for (var i = 0; i < files.length; i++) {
            if (files[i].name === detail.filename) {
                idx = i;
                break;
            }
        }
        var culprit = idx >= 0 ? files[idx] : files[0];
        var rest = files.slice();
        rest.splice(idx >= 0 ? idx : 0, 1);

        var isPassword =
            detail.code === 'workorder.intake.pdf_password_required' ||
            detail.code === 'workorder.intake.pdf_password_wrong';

        var settled;
        if (isPassword && onPasswordNeeded) {
            settled = onPasswordNeeded(culprit, detail).then(function (decision) {
                if (decision && decision.password) {
                    return runBatch(
                        api,
                        orderId,
                        [culprit],
                        decision.password,
                        onOutcome,
                        onPasswordNeeded
                    );
                }
                onOutcome({
                    type: 'reject',
                    name: culprit.name,
                    reasonKey: 'intake_reason_skipped',
                });
                return Promise.resolve();
            });
        } else {
            onOutcome({ type: 'reject', name: culprit.name, message: detail.message });
            settled = Promise.resolve();
        }
        return settled.then(function () {
            return runBatch(api, orderId, rest, null, onOutcome, onPasswordNeeded);
        });
    }

    function runBatch(api, orderId, files, password, onOutcome, onPasswordNeeded) {
        if (!files.length) return Promise.resolve();
        return api
            .addMaterials(orderId, files, password)
            .then(function (res) {
                onOutcome({ type: 'success', files: files, count: (res && res.count) || 0 });
            })
            .catch(function (err) {
                var detail = err && err.detail;
                if (detail && typeof detail === 'object' && detail.code) {
                    return handleReject(api, orderId, files, detail, onOutcome, onPasswordNeeded);
                }
                onOutcome({
                    type: 'network_fail',
                    files: files,
                    errKey: AI.api.mapApiErrorKey(err && err.code),
                });
            });
    }

    // ============ 整趟投料:按安全批切分,逐批跑;单批失败不停后续批 ============

    function run(api, orderId, allFiles, handlers) {
        handlers = handlers || {};
        var batches = AI.intakeRender.splitBatches(allFiles);
        var pendingNames = names(allFiles);
        var doneNames = [];
        var failedNames = [];
        var total = allFiles.length;

        function without(list, removeNames) {
            return list.filter(function (n) {
                return removeNames.indexOf(n) < 0;
            });
        }

        function persist() {
            saveQueueState(orderId, {
                total: total,
                doneNames: doneNames,
                pendingNames: pendingNames,
                failedNames: failedNames,
            });
        }
        persist();

        function settle(evt) {
            if (evt.type === 'success') {
                var ns = names(evt.files);
                pendingNames = without(pendingNames, ns);
                doneNames = doneNames.concat(ns);
            } else if (evt.type === 'reject') {
                pendingNames = without(pendingNames, [evt.name]);
            } else if (evt.type === 'network_fail') {
                var nf = names(evt.files);
                pendingNames = without(pendingNames, nf);
                failedNames = failedNames.concat(nf);
            }
            persist();
            handlers.onOutcome && handlers.onOutcome(evt);
        }

        var chain = Promise.resolve();
        batches.forEach(function (batch, i) {
            // 每批独立 try:某批网络失败只把该批记进 failedBatches,链条继续跑下一批
            // (单批失败不停后续批 · A10/A11)。
            chain = chain.then(function () {
                handlers.onBatchStart && handlers.onBatchStart(i + 1, batches.length);
                return runBatch(api, orderId, batch, null, settle, handlers.onPasswordNeeded);
            });
        });
        return chain.then(function () {
            if (!pendingNames.length && !failedNames.length) clearQueueState(orderId);
            handlers.onDone && handlers.onDone();
        });
    }

    // ============ create(getS, render):挂进 ai-intake.js 会话态的动作工厂 ============
    //
    // 同 ai-intake-bank-sales.js 的 create(getS, render) 先例(单文件<500 行铁律拆分,
    // 不是独立视图):getS() 取当前会话态(换客户/换单时旧回调靠 getS() !== session 卫哨
    // 自认失效,不污染新会话),render() 是 ai-intake.js 的重绘函数。

    function create(getS, render) {
        function runQueue(files) {
            var session = getS();
            session.uploading = true;
            session.uploadErrKey = null;
            session.uploadDone = 0;
            session.uploadTotal = files.length;
            session.uploadBatchIndex = 0;
            session.uploadBatchTotal = AI.intakeRender.splitBatches(files).length;
            render();
            run(session.api, session.orderId, files, {
                onBatchStart: function (index, total) {
                    if (getS() !== session) return;
                    session.uploadBatchIndex = index;
                    session.uploadBatchTotal = total;
                    render();
                },
                onPasswordNeeded: function (file, detail) {
                    return new Promise(function (resolve) {
                        if (getS() !== session) {
                            resolve({ skip: true });
                            return;
                        }
                        session.passwordCard = {
                            filename: file.name,
                            errKey:
                                detail.code === 'workorder.intake.pdf_password_wrong'
                                    ? 'wrong'
                                    : null,
                            resolve: resolve,
                        };
                        render();
                    });
                },
                onOutcome: function (evt) {
                    if (getS() !== session) return;
                    if (evt.type === 'success') {
                        session.uploadDone += evt.files.length;
                        session.manifest.accepted += evt.count;
                        session.manifest.zipExpanded += AI.intakeManifest.zipExpandedCount(
                            evt.files,
                            evt.count
                        );
                    } else if (evt.type === 'reject') {
                        session.manifest.rejected.push({
                            name: evt.name,
                            message: evt.message,
                            reasonKey: evt.reasonKey,
                        });
                    } else if (evt.type === 'network_fail') {
                        session.failedBatches.push({ files: evt.files });
                    }
                    session.passwordCard = null;
                    render();
                },
            }).then(function () {
                if (getS() !== session) return;
                session.uploading = false;
                session.dirty = session.manifest.accepted > 0 || session.dirty;
                session.rerunErrKey = null;
                render();
            });
        }

        // 网络级失败批(非内容拒收)一键只重传这些批,不牵连已成功/已确认拒收的件。
        function retryFailedBatches() {
            var session = getS();
            if (!session.failedBatches.length || session.uploading) return;
            var files = session.failedBatches.reduce(function (acc, b) {
                return acc.concat(b.files);
            }, []);
            session.failedBatches = [];
            runQueue(files);
        }

        function resumeDismiss() {
            var session = getS();
            clearQueueState(session.orderId);
            session.resumeBanner = null;
            render();
        }

        function submitPassword(password) {
            var session = getS();
            if (!session.passwordCard || !password) return;
            session.passwordCard.resolve({ password: password });
        }

        function skipPassword() {
            var session = getS();
            if (!session.passwordCard) return;
            session.passwordCard.resolve({ skip: true });
        }

        return {
            upload: runQueue,
            retryFailedBatches: retryFailedBatches,
            resumeDismiss: resumeDismiss,
            submitPassword: submitPassword,
            skipPassword: skipPassword,
        };
    }

    window.AI = window.AI || {};
    window.AI.intakeQueue = {
        loadQueueState: loadQueueState,
        clearQueueState: clearQueueState,
        walkDataTransferItems: walkDataTransferItems,
        hasDirectoryEntry: function (items) {
            var list = Array.prototype.slice.call(items || []);
            for (var i = 0; i < list.length; i++) {
                var entry = list[i].webkitGetAsEntry && list[i].webkitGetAsEntry();
                if (entry && entry.isDirectory) return true;
            }
            return false;
        },
        create: create,
    };
})();
