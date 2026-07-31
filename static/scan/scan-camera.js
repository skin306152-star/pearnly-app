/*
 * Pearnly · scan-camera.js · 摄像头扫商品条码引擎(无界面)
 *
 * 职责边界:本文件只管「开相机 → 裁取景框 → 解码 → 回调」和「出错时给出一个能翻译成人话的错误
 * 对象」。弹窗长什么样、错误卡怎么画、重试按钮放哪,全归调用方 —— POS 和主站 SPA 各有一套设计
 * 语言与翻译函数,引擎里写死任何一套都会让另一套变形。
 *
 * 依赖 scan-loader.js(首屏 bundle 里):能力探针 + 同源 loadScript。本文件只可能被 loader 的
 * ensureLoaded() 拉进来,所以那层一定在。错误分档(scanError / withTimeout)在同一个懒加载
 * 产物里的 scan-errors.js,排在本文件之前。
 *
 * 与 Odoo(addons/web/.../barcode_video_scanner.js)的四处刻意不同,都是店员会当场骂人的地方:
 *  1. 它等视频就绪是 `while (!ready) await delay(10)`(源码自带 FIXME)→ 这里 startTimeoutMs
 *     到点就报 timeout,不会转着圈死等。
 *  2. 它报错只丢一个通知、文案是拼英文 message → 这里按 code 分档(权限/没相机/被占用/超时/
 *     解码器拉不下来),每档一个 i18n 键。
 *  3. 它在非 HTTPS 下让扫码按钮静默消失 → insecure_context 是一档明确的错误码,调用方拿
 *     unsupportedReason() 在首屏就能说清「为什么这里没有扫码」。
 *  4. 它原生那条路解全帧再按 boundingBox 过滤取景框 → 这里两条路都只把取景框那块像素画进
 *     canvas 再解,手机上少解掉一多半像素。
 */
(function (root) {
    'use strict';

    var doc = root && root.document;
    var shell = (root && root.PearnlyScanCamera) || null;
    if (!shell || typeof shell.loadScript !== 'function' || typeof shell.scanError !== 'function') {
        throw new Error(
            'scan-camera.js 需要 scan-loader.js(dist/pos.js 与 dist/pre.js)与 scan-errors.js' +
                '(dist/scan.js 里排在本文件之前)先加载'
        );
    }
    var scanError = shell.scanError;
    var isScanError = shell.isScanError;
    var mediaErrorCode = shell.mediaErrorCode;
    var withTimeout = shell.withTimeout;

    var RETAIL_FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'itf'];
    var ZXING_BUNDLE = '/static/dist/zxing.js';

    var DEFAULTS = {
        facingMode: 'environment',
        // 取景框占画面的比例。条码是宽扁的,竖直方向给太多只是多解无用像素。
        cropRatio: { width: 0.9, height: 0.5 },
        // 常态采样间隔:没有码在跟踪、或跟踪中的码这一拍解出来了 —— 不急,省电。
        intervalMs: 120,
        // 「跟踪中的码这一拍没解出来」时改用的间隔:这段里每一拍都是一次证据,空等一个完整的
        // intervalMs 等于把证据尺的刻度调粗一倍(见 sweep 上方)。不取 0 是给主线程留口气。
        probeIntervalMs: 15,
        // 判「离开取景框」的两把尺子,两把都够才算离开(为什么要两把:见 sweep 上方)。1600 ≈ 实测
        // 最长一次反光(800ms)的两倍。12 次采样这个数由最慢的那台定:一次采样 400ms 的老机器上,
        // p=0.5 抖动素材(8 个 seed)最长一次连着没解出走到 10 次 —— 12 只剩两次余量,再往下调
        // 那台机器就会把一次持握记成两件。两个数落在不同机器上才分得出谁在挡:快的那台墙钟挡
        // (原生 12 次采样只要 ≈200ms),慢的那台采样数挡(老机器 12 次采样 ≈5s)。
        // 代价是地板跟着机器走。按引擎自己的墙钟是 ≈1.6s / ≈1.8s / ≈5.0s;换成店员看得见的
        // 「货真的离开画面多久」,真浏览器三档机器逐档扫出来是:原生与店里那台一样落在
        // 1.4~1.6s(快的这两台都是墙钟先到点,采样数只在老机器上才轮得到它挡)、老机器 4~6s。
        // 地板以下的真离开认不出来 —— 那一段交给 dupNotice* 出声,见下。逐档数字与跑法在
        // scripts/_r5_cam_floor_by_speed_verify.cjs;要动这两个数,先把那份报告重跑一遍。
        clearAfterMs: 1600,
        clearAfterMisses: 12,
        // 「够不到上面那两把尺子、于是被当成同一件挡下」的告警门槛(见 accept)。门槛按【人的
        // 动作】定,不按机器速度定:同一句提示在三台机器上说的是同一件事,才谈得上排障。
        //  · 800ms:人把 A 拿开再举 B 的物理下限。
        //  · 2 次采样:只挡「一帧没解出来」这种单点噪声。别按 clearAfterMisses 的比例取 ——
        //    一次采样 400ms 的老机器上 6 次就是 2.4 秒,它的静默区(0~5s)于是有一半照不到,
        //    而那台机器恰恰是静默丢货最凶的。真正定门槛的是墙钟,采样数只兜最退化的情形。
        // 误报是明码标价买来的:p=0.5 抖动素材上举着不动,一次没解出的最长空档实测原生 ≤598ms
        // (零误报)、店里那台 ≤1185ms、老机器 ≤4255ms —— 后两台会喊。买到的是它们的静默区
        // (1.8s / 5.0s)不再一声不吭。误报的话术是条件句(「若是第二件…」),而且调用方按码
        // 只留一行:一次持握最多摊上一行,店员点掉就是了。
        // 门槛底下那一段仍然一声不吭,宽度同一份报告里量过:真空档 ≤400ms(店里那台)、
        // ≤600ms(原生 / 老机器)—— 人把 A 拿开再举 B 快不到那个份上。反过来说,这两个数
        // 只要往上调,静默区就爬进人手够得到的区间了。
        dupNoticeMs: 800,
        dupNoticeMisses: 2,
        // 拿到 stream 之后到画面真的出帧的超时,包住 play()(为什么必须包住:见 cameraReady)。
        startTimeoutMs: 8000,
        // 权限弹窗是人在操作,给足 30s;再久就是卡住了,不能永远停在「正在打开相机」。
        grantTimeoutMs: 30000,
        // 解码器(dist/zxing.js ~340KB)下载超时,跟相机那 8s 分开:泰国移动网络上光下载就好
        // 几秒,合用一把尺子会把「网慢」误判成「相机坏」。
        decoderTimeoutMs: 20000,
    };

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

    // 原生优先(安卓 Chrome 上跑在 native 里,比 ZXing 省一大截电);建不起来时仍回落 ZXing,别卡死。
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

    // cancelled() 为真直接 resolve:用户主动关掉不该被超时变成错误卡;超时由调用点统一加(见 start)。
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
        // 两条解码路都要把 canvas 像素读回 JS,不声明 willReadFrequently 的话 Chrome 当它 GPU 纹理用,每帧回读同步等 GPU。
        var ctx = canvas.getContext('2d', { willReadFrequently: true });

        var stream = null;
        var watch = null; // 轨道生死看门人(scan-errors.js 的 watchTracks)· 拿到 stream 才有
        var detector = null;
        var timer = null;
        var decoding = false; // 互斥:上一帧还没解完就不排下一帧,防两次扫码打架
        var state = 'idle';
        // 「还在画面里」的码:code → { at: 最后一次解出它的时刻, missed: 之后连着几次采样没见它 }
        var seen = Object.create(null);
        var probing = false; // 有跟踪中的码上一拍没解出来 → 下一拍别空等(见 schedule)
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
            // 作废这一轮:srcObject 置空后 readyState 回 0,waitFrames 等不到帧又只认 stale 退场;
            // 不作废就每 intervalMs 空转、把 video/canvas/回调吊到下次 start。start/stop 的 bump 不受影响。
            runToken += 1;
            if (timer) {
                clearTimeout(timer);
                timer = null;
            }
            // 画面没了就没有「还在画面里」的码;不清空,重开一轮时第一次扫会被当成重复丢掉。
            seen = Object.create(null);
            probing = false;
            if (watch) watch.release();
            watch = null;
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
            // 只 console.error 就等于用户什么都看不到(Odoo 的原病);onError 是硬要求,没给才退控制台。
            if (o.onError) o.onError(e);
            else console.error('scan-camera', e.code, e.detail);
        }

        // 取景框那块像素画进 canvas:两条解码路解的都是这一块,屏上的框跟 cropRatio 对上就名副其实。
        function drawCrop() {
            var w = Math.max(1, Math.round(video.videoWidth * cfg.cropRatio.width));
            var h = Math.max(1, Math.round(video.videoHeight * cfg.cropRatio.height));
            if (canvas.width !== w) canvas.width = w;
            if (canvas.height !== h) canvas.height = h;
            var x = Math.round((video.videoWidth - w) / 2);
            var y = Math.round((video.videoHeight - h) / 2);
            ctx.drawImage(video, x, y, w, h, 0, 0, w, h);
        }

        // 「这是不是新的一次扫描」= 「这个码离开过取景框没有」。三种真实场景否掉了别的写法:举一箱
        // 不动 6 秒(纯时间节流每过一个窗口就再收一次钱)、两瓶一样的可乐连着扫(第二瓶落在窗口内
        // 被当重复丢掉)、一件货贴两个码同时入框(只记「上一个码」则每帧改写,节流全程失效)。难在
        // 【拿什么量】—— 单独任何一把尺子都会被它要量的东西污染,所以要两把,AND:
        //  · missed = 连着几次【采样】没解出它。一次采样记一次,不管这次采样花了 2ms 还是 400ms,
        //    解码器再慢也推不动它。只量墙钟就栽在这:要数的正是「解不出的帧」,而 ZXing 每解不出
        //    一帧就往墙钟里塞 114~121ms(本仓实测),失败采样周期 ≈240ms,连 5 帧就吃满 1200ms;
        //    真浏览器实测(p=0.5、货全程没离开)一件可乐记成 2~3 件。
        //  · at = 距最后一次解出它的墙钟毫秒。它同样会被解码耗时撑大,但在 AND 里撑大只让它更容易
        //    点头,点不点头由 missed 兜着;它管另一头 —— 原生 BarcodeDetector 一帧几毫秒,半秒就
        //    攒够 missed,一次扫过箱面的反光会被判成「货走了」。
        // 两把尺子失效方向相反(墙钟被慢解码器撑大、采样数被快解码器缩水),AND 起来谁慢听谁的。
        // 方向刻意偏「宁可少记」:多记是客人多付钱且没人看得见,少记是屏上数量对不上,店员当场就
        // 补。Odoo 靠「扫中就关掉扫描器」绕开整件事,那等于举着不动每停一次解码就再记一件。
        function sweep(hits) {
            var now = Date.now();
            var doubt = false;
            for (var code in seen) {
                if (hits.indexOf(code) >= 0) continue;
                var e = seen[code];
                e.missed += 1;
                if (e.missed >= cfg.clearAfterMisses && now - e.at >= cfg.clearAfterMs) {
                    delete seen[code];
                } else {
                    doubt = true; // 悬而未决 → 下一拍走 probeIntervalMs 去补证据
                }
            }
            probing = doubt;
        }

        // 被挡下的那一次必须说出去。上面两把尺子只把「别记成两件」这一侧量得很细,另一侧
        // (同款第二件还认不认)是有代价的:AND 起来的地板实测 ≈1.6s(原生)/ ≈1.8s(店里那台)
        // / ≈5.0s(老机器),地板以下拿走 A 再举 B 会一声不吭 —— 没震动、没查码、件数不动,
        // 屏上跟成功扫码一模一样,顾客拿两件付一件的钱。
        // 地板降不下来:1.2 秒的真空档跟 1.2 秒的反光在解码结果上是同一串「连着 N 次没解出」,
        // 信息上就分不开。两条压地板的路都真跑过(R5_LOWFLOOR=1 那份报告,每条都配同机同素材
        // 的对照组,不然多记赖不到门槛头上):
        //  · 门槛压到 1.2s(clearAfterMs 1200 / clearAfterMisses 8):一次 1.2 秒的反光就被判成
        //    「货走了」,一箱可乐记成 3 件(对照组不动门槛:1 件)。
        //  · 给采样尺加「墙钟到点就放行」的封顶来砍老机器那 5 秒:封顶 ≈2.5s 时,老机器上一次
        //    2.8 秒的糊把一次持握记成 2 件(对照组不封顶:1 件)。那台机器举着不动实测糊得出
        //    3.0 秒的空档,任何低于它的封顶都是拿多记货去赌。
        // 多记一件屏上小票上报表上全看不出来,所以这个方向宁可不动。
        // 分不开就交给唯一分得开的人:够到告警门槛的那次压制报给调用方,店员当场点掉或补一件。
        function accept(code) {
            var now = Date.now();
            var e = seen[code];
            if (e) {
                var gapMs = now - e.at; // 归零之前先取证据:这次压制是贴着地板还是刚扫完一秒
                var misses = e.missed;
                e.at = now; // 还在画面里 = 还是刚才那一次扫描,两把尺子一起归零
                e.missed = 0;
                // gapMs 是墙钟,含引擎自己解码烧掉的时间 —— 它比「画面真的糊了多久」系统性地
                // 多出最多一次采样(店里那台 ≈135ms、老机器 ≈415ms)。方向是安全的(宁可早喊
                // 一点也别漏),但调用方拿它做二次判断前得知道这条偏差。
                if (o.onDuplicate && misses >= cfg.dupNoticeMisses && gapMs >= cfg.dupNoticeMs) {
                    o.onDuplicate(code, { gapMs: gapMs, misses: misses });
                }
                return;
            }
            seen[code] = { at: now, missed: 0 };
            if (root.navigator && typeof root.navigator.vibrate === 'function') {
                root.navigator.vibrate(100);
            }
            if (o.onScan) o.onScan(code);
        }

        // 相机被系统收走 = 这一轮到此为止。走 camera_busy 那一档:它说的就是「相机在别人手上,
        // 处理掉再试」,而且已经标了可重试 —— 店员挂掉电话点「重试」就接着扫,不用关层重开。
        // 事件与轮询两条路都进这里,后到的那条看见 stream 已是 null(fail 里已经收摊)直接退。
        function lost(token) {
            if (stale(token) || !stream || !watch || !watch.check()) return false;
            fail(scanError('camera_busy'));
            return true;
        }

        function schedule(token) {
            if (stale(token) || !stream) return;
            var wait = probing ? cfg.probeIntervalMs : cfg.intervalMs;
            timer = setTimeout(function () {
                tick(token);
            }, wait);
        }

        function tick(token) {
            if (stale(token) || !stream || decoding) return;
            if (lost(token)) return; // 死图照样满足 videoReady(),所以必须排在它前面
            if (!videoReady(video)) {
                // 没像素就采不到样,催也是空转;码留在 seen 里 —— 没证据不判它走,「卡住」≠「走了」。
                probing = false;
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
                    // 轨道自己死掉不在 start/stop/destroy/onError 这四条路里 —— 没人盯着它,
                    // 相机被收走之后屏上会一直说在扫(见 scan-errors.js 的 watchTracks)。
                    watch = shell.watchTracks(s, function () {
                        lost(token);
                    });
                    video.srcObject = s;
                    return s;
                },
                function (e) {
                    // 超时报出去之后用户仍可能点「允许」:那条 MediaStream 会在没人认领的情况下兑现
                    // —— stream 变量还是 null,releaseCamera() 无从下手,相机灯亮到关页面,重试还会
                    // 被自己占住的相机顶成 NotReadableError(那档话术说的是「被别的应用占着」,把人
                    // 指到错的地方)。迟到的兑现照样得收。
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
                    // 相机预热与解码器下载并行(互不依赖),各用自己的超时尺子,话术才不会答非所问。
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
            // 屏上取景框的唯一事实源,CSS 里别写第二份 —— 两处一漂就是「对准了却读不出」,
            // 而这种病不报任何错,只会被当成「扫码不好使」。
            cropRatio: function () {
                return { width: cfg.cropRatio.width, height: cfg.cropRatio.height };
            },
        };
    }

    // 错误分档那几样原样转出去:调用方(POS / 主站 SPA / 单测)一直只认 PearnlyScanCamera
    // 这一个名字,拆文件是内部事,不该逼它们改引用。
    var api = {
        create: create,
        FORMATS: RETAIL_FORMATS,
        ERROR_KEYS: shell.ERROR_KEYS,
        scanError: scanError,
        mediaErrorCode: mediaErrorCode,
        isScanError: isScanError,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    for (var key in api) {
        if (Object.prototype.hasOwnProperty.call(api, key)) shell[key] = api[key];
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
