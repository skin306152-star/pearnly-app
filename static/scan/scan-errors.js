/*
 * Pearnly · scan-errors.js · 扫码链路的错误分档(把浏览器抛的东西翻译成一档 i18n 键)
 *
 * 从 scan-camera.js 拆出来:那边管的是「开相机 → 解码 → 回调」,这里管的是「什么算失败、
 * 该跟店员怎么说、给不给重试按钮」。两件事的改动理由完全不同 —— 加一档新的 DOMException
 * 名字不该动解码循环,调解码循环也不该碰话术表。拆开之后各自都能单独验。
 * 「相机被系统收走」(watchTracks)因此也归这里:它是一个失败的来源,判据全是平台差异,
 * 引擎只负责在它说话时作废这一轮。
 *
 * 只挂 window.PearnlyScanCamera(与 scan-loader.js 同一个壳对象),不新增全局。壳在 loader
 * 里建、这里补、scan-camera.js 再补 create() —— 三个文件往同一个对象上叠,调用方永远只认
 * 这一个名字。本文件零依赖:loader 到没到都能加载(node 单测直接 require 它)。
 */
(function (root) {
    'use strict';

    var ERROR_KEYS = {
        insecure_context: 'bscan.err.insecure',
        no_camera_api: 'bscan.err.unsupported',
        permission_denied: 'bscan.err.permission',
        no_camera: 'bscan.err.no_camera',
        camera_busy: 'bscan.err.busy',
        timeout: 'bscan.err.timeout',
        decoder_unavailable: 'bscan.err.decoder',
        unknown: 'bscan.err.unknown',
    };

    // 重试有意义的档:超时/被占用/解码器没拉下来可能下次就好;没相机、非 HTTPS、权限被拒一万次也一样。
    var RETRYABLE = { timeout: 1, camera_busy: 1, decoder_unavailable: 1 };

    // getUserMedia 的 DOMException 名字 → 我们的错误码。分档的意义在于话术不同:权限被拒要教
    // 怎么开权限,设备被占用要说关掉别的应用,没有摄像头只能改手输。表里的旧名
    // (PermissionDeniedError / DevicesNotFoundError / TrackStartError)是老 WebRTC 时代的叫法,
    // 安卓上仍有厂商浏览器在发。NotSupportedError 是策略/系统层把摄像头关了(真 Chromium 拒
    // 权限实测发的就是它),对用户等于「这台机器扫不了」。
    var MEDIA_ERRORS = {
        NotAllowedError: 'permission_denied',
        PermissionDeniedError: 'permission_denied',
        SecurityError: 'permission_denied',
        NotFoundError: 'no_camera',
        DevicesNotFoundError: 'no_camera',
        OverconstrainedError: 'no_camera',
        NotSupportedError: 'no_camera_api',
        NotReadableError: 'camera_busy',
        TrackStartError: 'camera_busy',
        AbortError: 'camera_busy',
    };

    // 认不出的 DOMException 一律 unknown,但原名进 detail —— 线上冒出新名字时日志里看得见,不无声吞掉。
    function mediaErrorCode(err) {
        return MEDIA_ERRORS[err && err.name] || 'unknown';
    }

    function scanError(code, cause) {
        var known = ERROR_KEYS[code] ? code : 'unknown';
        var detail = cause && (cause.name || cause.message);
        return {
            code: known,
            messageKey: ERROR_KEYS[known],
            retryable: !!RETRYABLE[known],
            detail: detail ? String(detail) : '',
        };
    }

    // 「这个异常已经是我们自己的 scanError 了吗」。必须连 ERROR_KEYS 一起验:光看有没有 .code
    // 会被 DOMException 骗过去 —— 它带一个数字型 legacy code(NotFoundError=8、SecurityError=18、
    // AbortError=20),真机上「没有摄像头」会因此绕过分档掉进 unknown,店员看到一句最没用的通用
    // 报错。NotAllowedError 的 legacy code 恰好是 0,所以只测「权限被拒」时一切正常。
    function isScanError(e) {
        return !!(e && typeof e.code === 'string' && ERROR_KEYS[e.code]);
    }

    // 超时也是一档错误,所以这把尺子跟错误表放在一起:到点就 reject 一个带 code 的 scanError,
    // 调用方拿到的跟别的失败长得一模一样(话术表因此只有一份)。
    function withTimeout(promise, ms, code) {
        return new Promise(function (resolve, reject) {
            var timer = setTimeout(function () {
                reject(scanError(code));
            }, ms);
            promise.then(
                function (v) {
                    clearTimeout(timer);
                    resolve(v);
                },
                function (e) {
                    clearTimeout(timer);
                    reject(e);
                }
            );
        });
    }

    // ── 轨道生死 ────────────────────────────────────────────────────────────
    // 相机可能在任何时刻被系统收走:来电、切后台、锁屏、另一个 app 开相机、拔掉 USB 摄像头。
    // 收走之后 <video> 停在最后一帧 —— readyState 仍是 4、videoWidth 仍是 640,引擎那句
    // videoReady() 于是恒真,tick 一直在解同一张死图:屏上「对准条码」照旧、取景框还亮着、
    // 件数不涨,店员把货一件件举过去全不算数,零反馈(真浏览器实测:收走后 8 秒里查码 0 次,
    // 同素材对照组 2 次 —— 两跑屏上唯一的差别只有件数不涨)。
    // 归本文件而不是解码循环:这是「什么算失败、该跟店员怎么说」,跟上面的分档同一件事;
    // 而它的判据全是平台差异(哪个系统发 ended、哪个只 mute、stop() 到底发不发事件),
    // 混进 tick 里没人看得清。仍然零加载期依赖:document 只在函数里按需摸。
    var MUTED_GRACE_MS = 3000;

    // 一组轨道的三种活法。ended 与 muted 必须分开:ended 收不回来(设备被拿走 / 拔掉),
    // muted 是画面冻住而轨道还在(切后台 / 锁屏 / 别的应用短暂抢走),它自己会回来 ——
    // 把 muted 当 ended 报错,就是把「切出去接个电话再切回来接着扫」这条正常路径弄坏。
    function trackState(tracks) {
        if (!tracks || !tracks.length) return 'ended';
        var ended = true;
        var muted = true;
        for (var i = 0; i < tracks.length; i++) {
            if (tracks[i].readyState !== 'ended') ended = false;
            if (!tracks[i].muted) muted = false;
        }
        return ended ? 'ended' : muted ? 'muted' : '';
    }

    // 两侧都要有人看着,少一侧就有整类收走方式漏网:
    //  · 事件(ended):还在等第一帧、或解码卡住那会儿也立刻出声,不用等下一拍。
    //  · 每拍轮询 check():track.stop() 按规范【不发】ended,页面外部把轨道收走走的正是
    //    这条 —— 只订事件对它整类全盲(真浏览器实测:撤权后 readyState='ended' 而 ended
    //    事件一声没响)。mute 事件不订:那一刻宽限还没走完,check() 只会回 false,订它等于
    //    挂一个必然空转的监听;muted 由轮询接管。
    // 回调只报「没了」,给哪一档、要不要作废这一轮归引擎 —— 它才知道当前是不是还在这一轮。
    function watchTracks(stream, onLost) {
        var tracks = stream && stream.getTracks ? stream.getTracks() : [];
        var mutedAt = 0;
        var bound = [];

        // 后台期间不计 muted 的时长:那会儿画面本来就该是死的,而且移动端整个页面会被冻住,
        // 拿这段算宽限等于「切出去久一点、回来就说相机坏了」。
        function hidden() {
            var d = root && root.document;
            return !!(d && d.visibilityState === 'hidden');
        }

        function check() {
            var st = trackState(tracks);
            if (st === 'ended') return true;
            if (st !== 'muted' || hidden()) {
                mutedAt = 0;
                return false;
            }
            if (!mutedAt) mutedAt = Date.now();
            return Date.now() - mutedAt >= MUTED_GRACE_MS;
        }

        tracks.forEach(function (t) {
            if (!t || typeof t.addEventListener !== 'function') return;
            var fire = function () {
                if (check()) onLost();
            };
            t.addEventListener('ended', fire);
            bound.push(function () {
                t.removeEventListener('ended', fire);
            });
        });

        return {
            check: check,
            release: function () {
                bound.forEach(function (off) {
                    off();
                });
                bound = [];
            },
        };
    }

    var api = {
        ERROR_KEYS: ERROR_KEYS,
        scanError: scanError,
        mediaErrorCode: mediaErrorCode,
        isScanError: isScanError,
        withTimeout: withTimeout,
        trackState: trackState,
        watchTracks: watchTracks,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.PearnlyScanCamera = root.PearnlyScanCamera || {};
        for (var key in api) {
            if (Object.prototype.hasOwnProperty.call(api, key))
                root.PearnlyScanCamera[key] = api[key];
        }
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
