/*
 * Pearnly · scan-camera.js · 摄像头扫商品条码引擎(无界面)
 *
 * 职责边界:本文件只管「开相机 → 裁取景框 → 解码 → 回调」和「出错时给出一个能翻译成人话
 * 的错误对象」。弹窗长什么样、错误卡怎么画、重试按钮放哪,全归调用方 —— POS 和主站 SPA
 * 各有一套设计语言与翻译函数,引擎里写死任何一套都会让另一套变形。
 *
 * 依赖 scan-loader.js(首屏 bundle 里):能力探针 + 同源 loadScript。本文件只可能被
 * loader 的 ensureLoaded() 拉进来,所以那层一定在。
 *
 * 与 Odoo(addons/web/.../barcode_video_scanner.js)的四处刻意不同 —— 它那四处都是店员
 * 会当场骂人的地方:
 *  1. 它等视频就绪是 `while (!ready) await delay(10)` 且源码自带 FIXME 说该加超时 → 这里
 *     startTimeoutMs 到点就报 timeout,永远不会转着圈死等。
 *  2. 它 detect() 报错只丢一个通知、getUserMedia 报错文案是拼英文 message → 这里错误按
 *     code 分档(权限/没相机/被占用/超时/解码器拉不下来),每档一个 i18n 键。
 *  3. 它在非 HTTPS 下让扫码按钮静默消失 → insecure_context 是一档明确的错误码,调用方拿
 *     PearnlyScanCamera.unsupportedReason() 在首屏就能说清「为什么这里没有扫码」。
 *  4. 它原生那条路解全帧再按 boundingBox 过滤取景框 → 这里两条路都只把取景框那块像素画进
 *     canvas 再解,手机上少解掉一多半像素。
 */
(function (root) {
    'use strict';

    var doc = root && root.document;
    var shell = (root && root.PearnlyScanCamera) || null;
    if (!shell || typeof shell.loadScript !== 'function') {
        throw new Error(
            'scan-camera.js 需要 scan-loader.js 先加载(它在 dist/pos.js 与 dist/pre.js 里)'
        );
    }

    var RETAIL_FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'itf'];
    var ZXING_BUNDLE = '/static/dist/zxing.js';

    var DEFAULTS = {
        facingMode: 'environment',
        // 取景框占画面的比例。条码是宽扁的,竖直方向给太多只是多解无用像素。
        // 调用方屏幕上的取景框 CSS 必须跟这个比例对上,否则「框里对准了却读不出」。
        cropRatio: { width: 0.9, height: 0.5 },
        intervalMs: 120,
        // 一个码有这么久没再被解出来 = 它离开了取景框,之后再出现才算新的一次扫描。
        // 为什么量墙钟而不是帧数、1200 这个数是怎么定的:见 sweep() 上方。
        clearAfterMs: 1200,
        // 拿到 stream 之后到画面真的出帧的超时,包住 play() —— Odoo 那个 FIXME 的位置,
        // 而且 play() 本身在「有 stream 却永远不出帧」时也不会 settle(实测拿 captureStream(0)
        // 就能复现),只给等帧那段加超时仍然是死等。
        startTimeoutMs: 8000,
        // getUserMedia 本身的兜底超时。权限弹窗是人在操作,给足 30s;超过就是卡住了,
        // 不能让调用方永远停在「正在打开相机」。
        grantTimeoutMs: 30000,
        // 解码器(dist/zxing.js ~340KB)下载的超时。跟相机那 8s 分开:泰国移动网络上光下载
        // 就可能好几秒,用相机的尺子量它会把「网慢」误判成「相机坏」。
        decoderTimeoutMs: 20000,
    };

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

    // 重试有意义的档:超时/被占用/解码器没拉下来都可能下一次就好了。
    // 没有摄像头、非 HTTPS、权限被拒(要去系统设置改)重试一万次也一样。
    var RETRYABLE = { timeout: 1, camera_busy: 1, decoder_unavailable: 1 };

    // getUserMedia 的 DOMException 名字 → 我们的错误码。分档的意义在于话术不同:
    // 权限被拒要教怎么开权限,设备被占用要说关掉别的应用,没有摄像头只能改手输。
    // 表里的旧名(PermissionDeniedError / DevicesNotFoundError / TrackStartError)是老 WebRTC
    // 时代的叫法,安卓上仍有厂商浏览器在发。NotSupportedError 是策略/系统层把摄像头关了
    // (真 Chromium 拒权限实测发的就是它),对用户等于「这台机器扫不了」。
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

    // 认不出的 DOMException 一律 unknown,但原名会进 detail —— 线上真冒出新名字时,
    // 日志里看得见「该给它单独一档了」,而不是无声吞掉。
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

    // 「这个异常已经是我们自己的 scanError 了吗」。必须连 ERROR_KEYS 一起验:光看有没有
    // .code 会被 DOMException 骗过去 —— 它带一个数字型 legacy code(NotFoundError=8、
    // SecurityError=18、AbortError=20),真机上「没有摄像头」会因此绕过分档掉进 unknown,
    // 店员看到的是一句最没用的通用报错。NotAllowedError 的 legacy code 恰好是 0,所以只测
    // 「权限被拒」时一切正常 —— 这个坑靠单测一档一档验才照得出来。
    function isScanError(e) {
        return !!(e && typeof e.code === 'string' && ERROR_KEYS[e.code]);
    }

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

    // 原生 BarcodeDetector 对不认识的格式名会直接抛,所以先跟它自报的支持集求交集。
    function nativeDetector() {
        var Ctor = root.BarcodeDetector;
        var ask = Ctor.getSupportedFormats ? Ctor.getSupportedFormats() : Promise.resolve(null);
        return Promise.resolve(ask)
            .catch(function () {
                return null;
            })
            .then(function (supported) {
                var formats = supported
                    ? RETAIL_FORMATS.filter(function (f) {
                          return supported.indexOf(f) >= 0;
                      })
                    : RETAIL_FORMATS;
                if (!formats.length) throw scanError('decoder_unavailable');
                return new Ctor({ formats: formats });
            });
    }

    function zxingDetector() {
        return shell.loadScript(ZXING_BUNDLE).then(
            function () {
                if (!root.ZXing || !root.PearnlyScanZXing) throw scanError('decoder_unavailable');
                var Ctor = root.PearnlyScanZXing.build(root.ZXing);
                return new Ctor({ formats: RETAIL_FORMATS });
            },
            function (e) {
                throw scanError('decoder_unavailable', e);
            }
        );
    }

    // 原生优先:安卓 Chrome 上它跑在 native 里,比 ZXing 的 JS 解码省一大截电。
    // 原生存在但建不起来(格式全不支持等)时仍回落 ZXing,别让用户卡死在这。
    function makeDetector() {
        if ('BarcodeDetector' in root) {
            return nativeDetector().catch(function () {
                return zxingDetector();
            });
        }
        return zxingDetector();
    }

    // 漏一条 track 就是相机灯一直亮着、别的应用再也打不开相机。
    function stopTracks(s) {
        if (!s || typeof s.getTracks !== 'function') return;
        s.getTracks().forEach(function (t) {
            t.stop();
        });
    }

    // readyState 到 HAVE_CURRENT_DATA(2)才有像素可解;videoWidth 为 0 时 drawImage 画的是空图。
    function videoReady(video) {
        return video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0;
    }

    // cancelled() 为真时直接 resolve —— 用户按了取消,后续 .then 会按 token 短路,
    // 不该因为超时把一个「用户主动关掉」变成错误卡。超时由调用点统一加(见 start)。
    function waitFrames(video, intervalMs, cancelled) {
        return new Promise(function (resolve) {
            (function poll() {
                if (cancelled() || videoReady(video)) {
                    resolve();
                    return;
                }
                setTimeout(poll, intervalMs);
            })();
        });
    }

    function makeVideo(container) {
        var video = doc.createElement('video');
        // playsinline + muted 缺一个,iOS Safari 就把预览抢成全屏播放器,整个弹窗被顶掉。
        video.setAttribute('playsinline', '');
        video.setAttribute('muted', '');
        video.muted = true;
        video.autoplay = true;
        video.className = 'bscan-video';
        if (container) container.appendChild(video);
        return video;
    }

    function create(opts) {
        var o = opts || {};
        var cfg = {};
        for (var k in DEFAULTS) {
            if (Object.prototype.hasOwnProperty.call(DEFAULTS, k)) {
                cfg[k] = o[k] === undefined ? DEFAULTS[k] : o[k];
            }
        }
        var translate = typeof o.t === 'function' ? o.t : null;
        var ownsVideo = !o.video;
        var video = o.video || makeVideo(o.container);
        var canvas = doc.createElement('canvas');
        // 两条解码路都要把 canvas 的像素读回 JS(ZXing 走 getImageData,原生走 ImageBitmap),
        // 不声明 willReadFrequently 的话 Chrome 会把它当 GPU 纹理用,每帧回读都要同步等 GPU。
        var ctx = canvas.getContext('2d', { willReadFrequently: true });

        var stream = null;
        var detector = null;
        var timer = null;
        var decoding = false; // 互斥:上一帧还没解完就不排下一帧,防两次扫码打架
        var state = 'idle';
        // 当前认为「还在画面里」的码:code → { at: 最后一次解出它的时刻 }
        var seen = Object.create(null);
        var destroyed = false;
        var runToken = 0; // start/stop 交错时用它废掉上一轮的异步尾巴

        function stale(token) {
            return destroyed || token !== runToken;
        }

        function setState(next) {
            if (state === next) return;
            state = next;
            if (o.onState) o.onState(next);
        }

        function releaseCamera() {
            if (timer) {
                clearTimeout(timer);
                timer = null;
            }
            // 画面没了就没有「还在画面里」的码;不清空,重开一轮时第一次扫会被当成重复丢掉。
            seen = Object.create(null);
            if (stream) {
                stopTracks(stream);
                stream = null;
            }
            if (video.srcObject) video.srcObject = null;
        }

        function fail(err) {
            var e = isScanError(err) ? err : scanError('unknown', err);
            if (translate) e.message = translate(e.messageKey);
            releaseCamera();
            setState('error');
            // 只 console.error 就等于用户什么都看不到(Odoo 的原病)。onError 是硬要求,
            // 调用方真没给就退回控制台,至少留下痕迹。
            if (o.onError) o.onError(e);
            else console.error('scan-camera', e.code, e.detail);
        }

        // 取景框那块像素画进 canvas。原生与 ZXing 两条路解的都是这一块,
        // 屏幕上画的框只要跟 cropRatio 对上,「框里」就名副其实。
        function drawCrop() {
            var w = Math.max(1, Math.round(video.videoWidth * cfg.cropRatio.width));
            var h = Math.max(1, Math.round(video.videoHeight * cfg.cropRatio.height));
            if (canvas.width !== w) canvas.width = w;
            if (canvas.height !== h) canvas.height = h;
            var x = Math.round((video.videoWidth - w) / 2);
            var y = Math.round((video.videoHeight - h) / 2);
            ctx.drawImage(video, x, y, w, h, 0, 0, w, h);
        }

        // 「这是不是新的一次扫描」用时间节流答不了 —— 连扫模式下三种真实场景各错一种:
        //  · 整箱货举在框里不动 6 秒:纯时间节流每过一个窗口就再计一次,店员一个动作没做,
        //    客人被收五箱的钱;
        //  · 两瓶真的一样的可乐连着扫:第二瓶落在窗口内,被当重复丢掉,少收一瓶;
        //  · 一件货上贴两个码同时入框:只记「上一个码」的话每帧都被改写,节流全程失效。
        // 判据改成「这个码有多久没再被解出来」,量墙钟不量帧数,两处都要紧:
        //  · 帧不是墙钟。一帧【解不出】的开销随解码器差一个量级(实测:原生几毫秒,ZXing 回落
        //    120ms),「4 帧」在两台机器上就是 0.5 秒和 1 秒两条不同的规则。
        //  · 阈值必须远离抖动量级。解不出是常态(scan-zxing-shim.js:「每秒好几帧都这样」),
        //    反光/曲面/对焦拉扯会连着几帧读不出而货没动过;阈值落进抖动量级,举一箱 ฿350
        //    可乐等后端就被记成两三箱,且屏上不报错。
        // 1200ms = 复现里最长一段抖动(480ms · 反光与对焦各一次)的 2.5 倍;而真换一件货
        // (放下、拿起下一箱、重新对准)在手机上从来不止 1.2 秒。方向刻意偏「宁可少记」:多记是
        // 客人多付钱且没人看得见,少记是屏上数量对不上,店员当场就补。Odoo 靠「扫中就关掉扫描器」
        // 绕开整件事,那等于举着不动每停一次解码就再记一件 —— 我们做了连扫模式,绕不开。
        function sweep(hits) {
            var now = Date.now();
            for (var code in seen) {
                if (hits.indexOf(code) < 0 && now - seen[code].at >= cfg.clearAfterMs) {
                    delete seen[code];
                }
            }
        }

        function accept(code) {
            var now = Date.now();
            var e = seen[code];
            if (e) {
                e.at = now; // last-seen:还在画面里 = 还是刚才那一次扫描
                return;
            }
            seen[code] = { at: now };
            if (root.navigator && typeof root.navigator.vibrate === 'function') {
                root.navigator.vibrate(100);
            }
            if (o.onScan) o.onScan(code);
        }

        function schedule(token) {
            if (stale(token) || !stream) return;
            timer = setTimeout(function () {
                tick(token);
            }, cfg.intervalMs);
        }

        function tick(token) {
            if (stale(token) || !stream || decoding) return;
            if (!videoReady(video)) {
                schedule(token);
                return;
            }
            decoding = true;
            var frame;
            try {
                drawCrop();
                frame = detector.detect(canvas);
            } catch (e) {
                decoding = false;
                fail(scanError('unknown', e));
                return;
            }
            Promise.resolve(frame).then(
                function (codes) {
                    decoding = false;
                    if (stale(token)) return;
                    var hits = [];
                    for (var i = 0; codes && i < codes.length; i++) {
                        var raw = codes[i] && codes[i].rawValue;
                        var v = raw ? String(raw).trim() : '';
                        if (v && hits.indexOf(v) < 0) hits.push(v);
                    }
                    sweep(hits);
                    // 一帧解出两个码 = 两件货各记一次。贴了两个码的同一件货因此会多记一次,
                    // 但止步于一次 —— 只看 codes[0] 的旧写法在这个场景下每帧都记。
                    for (var j = 0; j < hits.length; j++) accept(hits[j]);
                    schedule(token);
                },
                function (e) {
                    decoding = false;
                    if (stale(token)) return;
                    fail(scanError('unknown', e));
                }
            );
        }

        function openStream(token) {
            var granted = root.navigator.mediaDevices.getUserMedia({
                video: { facingMode: cfg.facingMode },
                audio: false,
            });
            return withTimeout(granted, cfg.grantTimeoutMs, 'timeout').then(
                function (s) {
                    if (stale(token)) {
                        stopTracks(s);
                        return null;
                    }
                    stream = s;
                    video.srcObject = s;
                    return s;
                },
                function (e) {
                    // 超时报出去之后用户仍可能点「允许」:那条 MediaStream 会在没人认领的情况下
                    // 兑现 —— stream 变量还是 null,releaseCamera() 无从下手,相机灯亮到关页面,
                    // 重试还会被自己占住的相机顶成 NotReadableError(而那档话术说的是「被别的
                    // 应用占着」,把人指到错的地方)。迟到的兑现照样得收。
                    granted.then(stopTracks, function () {});
                    throw isScanError(e) ? e : scanError(mediaErrorCode(e), e);
                }
            );
        }

        // 画面出帧为止。play() 也包在超时里:拿到了 stream 却永远不出帧时 play() 返回的
        // promise 根本不 settle,只给等帧那段加超时等于还是死等。
        function cameraReady(token) {
            return (
                Promise.resolve(video.play())
                    // iOS 上 play() 被打断会 reject(AbortError),但画面照样出帧 ——
                    // 别为此判失败,交给 waitFrames 用实际帧说话。
                    .catch(function () {})
                    .then(function () {
                        return waitFrames(video, cfg.intervalMs, function () {
                            return stale(token);
                        });
                    })
            );
        }

        function start() {
            if (destroyed) return Promise.resolve(false);
            var blocked = shell.unsupportedReason();
            if (blocked) {
                fail(scanError(blocked));
                return Promise.resolve(false);
            }
            releaseCamera();
            var token = ++runToken;
            setState('starting');
            return openStream(token)
                .then(function (s) {
                    if (!s) return false;
                    // 相机预热与解码器下载并行:两件事互不依赖,串起来只是白等。
                    // 各用自己的超时尺子(见 DEFAULTS 注释),超时话术才不会答非所问。
                    return Promise.all([
                        withTimeout(cameraReady(token), cfg.startTimeoutMs, 'timeout'),
                        withTimeout(makeDetector(), cfg.decoderTimeoutMs, 'decoder_unavailable'),
                    ]).then(function (r) {
                        if (stale(token)) return false;
                        detector = r[1];
                        setState('scanning');
                        if (o.onReady) o.onReady();
                        tick(token);
                        return true;
                    });
                })
                .catch(function (e) {
                    fail(e);
                    return false;
                });
        }

        function stop() {
            runToken += 1;
            decoding = false;
            releaseCamera();
            if (state !== 'idle') setState('stopped');
        }

        function destroy() {
            destroyed = true;
            stop();
            if (ownsVideo && video.parentNode) video.parentNode.removeChild(video);
        }

        return {
            start: start,
            // 重试就是重开一轮:错误卡上的「重试」直接绑这个,调用方不用自己拆状态。
            retry: start,
            stop: stop,
            destroy: destroy,
            video: video,
            isRunning: function () {
                return state === 'scanning';
            },
            state: function () {
                return state;
            },
            // 屏上取景框的唯一事实源:宽高按它现算,CSS 里别再写第二份 —— 两处一漂就是
            // 「框里明明对准了却读不出」,而这种病不报任何错,只会被当成「扫码不好使」。
            cropRatio: function () {
                return { width: cfg.cropRatio.width, height: cfg.cropRatio.height };
            },
        };
    }

    var api = {
        create: create,
        FORMATS: RETAIL_FORMATS,
        ERROR_KEYS: ERROR_KEYS,
        scanError: scanError,
        mediaErrorCode: mediaErrorCode,
        isScanError: isScanError,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    for (var key in api) {
        if (Object.prototype.hasOwnProperty.call(api, key)) shell[key] = api[key];
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
