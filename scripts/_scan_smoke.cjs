/*
 * scripts/_scan_smoke.cjs · 扫码地基的真浏览器验收(Chromium + 假摄像头)
 *
 * 为什么要有这个脚本:摄像头这条链路(getUserMedia → 出帧 → 裁取景框 → 解码)在 node 桩里
 * 全是假的,而真机上最容易坏的恰好是它。第一版就是靠它照出两个真 bug ——
 *   · DOMException 的数字型 legacy code(NotFoundError=8)让「没有摄像头」绕过分档掉进
 *     unknown,店员只看到一句最没用的通用报错;
 *   · video.play() 在「有 stream 却永远不出帧」时根本不 settle,只给等帧那段加超时 =
 *     仍然是 Odoo 那个转圈死等。
 * 两条单测都补上了,但下一个人改这层时,还是该拿真浏览器再跑一遍。
 *
 * 用法(仓库根目录):
 *   python scripts/_scan_ean_y4m.py .scan_fixture.y4m
 *   python scripts/_scan_ean_jitter_y4m.py .scan_fixture.jitter.y4m
 *   python scripts/_scan_ean_blink_y4m.py .scan_fixture.blink.y4m
 *   node scripts/_scan_smoke.cjs .scan_fixture.y4m [截图目录]
 * 后两份素材的路径由第一份推出来(同目录 .jitter / .blink),不用另传参。
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/scan_base/。
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const Y4M = path.resolve(process.argv[2] || '.scan_fixture.y4m');
const SHOTS = path.resolve(process.argv[3] || path.join(ROOT, 'tests/e2e/_artifacts/scan_base'));
// 假摄像头素材是浏览器启动参数,一个实例只能喂一段片子 → 三种画面各起一个 browser。
const sibling = (suffix) =>
    path.join(path.dirname(Y4M), path.basename(Y4M).replace(/\.y4m$/i, '') + suffix);
const JITTER = sibling('.jitter.y4m');
const BLINK = sibling('.blink.y4m');
const EXPECT_CODE = '8850999320014';
// 打进 type=date 会变成 49012-03-31 的那一串(date 控件收 6 位年份、提交不拦)。
const SCAN_INTO_DATE = '4901234567894';
const MIME = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' };

// 自带静态服务:懒加载走的是同源 /static/dist/*.js,file:// 下不成立。
function serve() {
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        const fp = path.join(ROOT, rel);
        if (!fp.startsWith(ROOT) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
            res.writeHead(fs.existsSync(fp) ? 200 : 404, { 'content-type': 'text/html' });
            res.end('<!doctype html><title>scan smoke</title><body>');
            return;
        }
        res.writeHead(200, {
            'content-type': MIME[path.extname(fp)] || 'application/octet-stream',
        });
        fs.createReadStream(fp).pipe(res);
    });
    return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

async function fresh(browser, origin, initScript, arg) {
    const page = await browser.newPage({ viewport: { width: 390, height: 780 } });
    // addInitScript 只搬函数源码,闭包变量丢失 → 参数必须显式传第二个实参。
    if (initScript) await page.addInitScript(initScript, arg);
    await page.goto(`${origin}/static/`);
    await page.addScriptTag({ url: '/static/dist/pre.js' });
    return page;
}

// ── ① 真解码 + 相机释放 + 首屏分层 ──────────────────────────────────────
async function liveDecode(browser, origin) {
    const page = await fresh(browser, origin);
    const probe = await page.evaluate(() => ({
        // 只加载了首屏 bundle 时 create() 必须还不存在 —— 「懒加载」不能只是注释里的说法
        createBeforeLoad: typeof (window.PearnlyScanCamera || {}).create,
        hasWedge: !!window.PearnlyScanWedge,
        reason: window.PearnlyScanCamera.unsupportedReason(),
        native: 'BarcodeDetector' in window,
    }));
    const fetched = [];
    page.on('request', (r) => {
        if (/\/static\/dist\/(scan|zxing)\.js/.test(r.url()))
            fetched.push(r.url().split('/').pop());
    });
    const scan = await page.evaluate(async () => {
        const api = await window.PearnlyScanCamera.ensureLoaded();
        const states = [];
        return await new Promise((resolve) => {
            const cam = api.create({
                container: document.body,
                onState: (s) => states.push(s),
                onScan: (code) => {
                    window.__cam = cam;
                    resolve({
                        states,
                        code,
                        videoW: cam.video.videoWidth,
                        playsinline: cam.video.hasAttribute('playsinline'),
                        muted: cam.video.muted,
                    });
                },
                onError: (e) => resolve({ states, err: e }),
            });
            cam.video.style.cssText = 'width:100%;height:100%;object-fit:contain';
            document.body.style.cssText = 'margin:0;background:#000;height:100vh';
            // 按 cropRatio 画出取景框:屏幕上的框跟真正被解码的区域必须是同一块,
            // 截图里能看出条码落在框内,这个契约才算被看见过。
            const r = cam.cropRatio();
            const frame = document.createElement('div');
            frame.style.cssText =
                'position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);' +
                `width:${r.width * 100}%;height:${r.height * 100}%;` +
                'border:2px solid #22d3ee;box-shadow:0 0 0 9999px rgba(0,0,0,.45)';
            document.body.appendChild(frame);
            cam.start();
            setTimeout(() => resolve({ states, timedOut: true, state: cam.state() }), 15000);
        });
    });
    await page.screenshot({ path: path.join(SHOTS, '01-live-scanning.png') }); // 取景中拍
    const released = await page.evaluate(() => {
        const cam = window.__cam;
        cam.stop();
        return {
            srcCleared: !cam.video.srcObject,
            liveTracks: cam.video.srcObject ? cam.video.srcObject.getTracks().length : 0,
            state: cam.state(),
        };
    });
    await page.close();
    const ok =
        probe.createBeforeLoad === 'undefined' &&
        probe.hasWedge &&
        probe.reason === null &&
        scan.code === EXPECT_CODE &&
        scan.playsinline &&
        scan.muted &&
        released.srcCleared &&
        released.liveTracks === 0;
    return { ok, probe, scan, fetched, released };
}

// ── ② 错误分档:每档一个人话键 + 该不该给重试 ────────────────────────────
function stubGum(kind) {
    window.__stub = kind;
    if (kind === 'insecure') {
        Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
    }
    Object.defineProperty(navigator, 'mediaDevices', {
        configurable: true,
        value: Object.assign({}, navigator.mediaDevices || {}, {
            getUserMedia: () => {
                if (window.__stub === 'stall') {
                    // 拿到 stream 却永远不出帧 → 逼出 startTimeoutMs 那一档
                    const c = document.createElement('canvas');
                    c.width = 320;
                    c.height = 240;
                    return Promise.resolve(c.captureStream(0));
                }
                return Promise.reject(new DOMException('stub', window.__stub));
            },
        }),
    });
}

// 每档:[注入的 DOMException 名, 期望错误码, 期望 i18n 键, 该不该能重试]
const BUCKETS = [
    ['NotAllowedError', 'permission_denied', 'bscan.err.permission', false],
    ['NotFoundError', 'no_camera', 'bscan.err.no_camera', false],
    ['NotReadableError', 'camera_busy', 'bscan.err.busy', true],
    ['NotSupportedError', 'no_camera_api', 'bscan.err.unsupported', false],
    ['stall', 'timeout', 'bscan.err.timeout', true],
    ['insecure', 'insecure_context', 'bscan.err.insecure', false],
];

async function errorBuckets(browser, origin) {
    const rows = [];
    for (const [kind, code, key, retry] of BUCKETS) {
        const page = await fresh(browser, origin, stubGum, kind);
        const got = await page.evaluate(async () => {
            const api = await window.PearnlyScanCamera.ensureLoaded();
            const states = [];
            return await new Promise((resolve) => {
                const cam = api.create({
                    container: document.body,
                    startTimeoutMs: 600, // 只为把 stall 那档压到秒级,其余档走不到这里
                    t: (k) => 'TR:' + k,
                    onState: (s) => states.push(s),
                    onScan: () => resolve({ states, unexpectedScan: true }),
                    onError: (e) => {
                        // 把 onError 的载荷原样画出来。这不是产品 UI(那归各 SPA 自己的设计
                        // 语言),是为了让截图证明「错误真能被渲染成人话 + 该不该给重试」——
                        // 只在 JSON 里断言,截出来会是一张什么都没有的白图,等于没有证据。
                        document.body.innerHTML =
                            '<pre id="card" style="font:14px monospace;padding:12px">' +
                            'code      ' +
                            e.code +
                            '\n' +
                            'messageKey ' +
                            e.messageKey +
                            '\n' +
                            'message   ' +
                            e.message +
                            '\n' +
                            'detail    ' +
                            (e.detail || '(none)') +
                            '\n' +
                            'retryable ' +
                            e.retryable +
                            '</pre>' +
                            (e.retryable ? '<button id="retry">重试</button>' : '');
                        resolve({
                            states,
                            err: e,
                            released: !cam.video.srcObject,
                            retryButton: !!document.getElementById('retry'),
                        });
                    },
                });
                cam.start();
                setTimeout(() => resolve({ states, timedOut: true }), 15000);
            });
        });
        await page.screenshot({ path: path.join(SHOTS, `02-err-${code}.png`) });
        await page.close();
        const e = got.err || {};
        rows.push({
            kind,
            code: e.code,
            message: e.message,
            retryable: e.retryable,
            released: got.released,
            states: got.states,
            ok:
                e.code === code &&
                e.messageKey === key &&
                e.message === 'TR:' + key &&
                e.retryable === retry &&
                got.retryButton === retry &&
                got.released === true &&
                got.states.indexOf('error') >= 0,
        });
    }
    return { ok: rows.every((r) => r.ok), rows };
}

// ── ③ 连扫去重:判据是「这个码有多久没再被解出来」 ────────────────────────
// 为什么要两段素材而不是一段:静态条码每帧都解得出,「读不出」那条路根本不会被走到 ——
// 判据改成 1 帧、甚至换回按时间节流,拿静态素材跑照样绿。所以「举着不动」喂会间歇糊掉的
// 抖动素材(jitter · 最长一段读不出 ≈733ms,够旧的 4 帧判据清好几次),「拿走再举回来」
// 喂真的会消失的素材(blink)。两段素材各自的尺子写在生成脚本的文件头里。
async function countScans(browser, origin, ms) {
    const page = await fresh(browser, origin);
    const got = await page.evaluate(async (waitMs) => {
        const api = await window.PearnlyScanCamera.ensureLoaded();
        const at = [];
        const errs = [];
        const cam = api.create({
            container: document.body,
            onScan: () => at.push(Date.now()),
            onError: (e) => errs.push(e.code),
        });
        await cam.start();
        const t0 = Date.now();
        await new Promise((r) => setTimeout(r, waitMs));
        cam.stop();
        return {
            n: at.length,
            errs,
            firstMs: at.length ? at[0] - t0 : null,
            gaps: at.slice(1).map((t, i) => t - at[i]),
        };
    }, ms);
    await page.close();
    return got;
}

// 举着不动 4.2s:反光/对焦让整段整段地读不出(最长 ≈733ms,观测空白被解码耗时撑到约 1.1s),
// 但那件货一次都没离开取景框 → 只能记 1 件。按时间节流的更早那版在这里记 3~4 件 —— 客人被收
// 三四份钱,屏上不报任何错。这一版判「离开」要两把尺子同时够(连着 N 次采样没解出它 + 距最后
// 一次解出它够久),733ms 这一段两把都远没到。判据本身的红证在
// tests/unit/test_scan_camera_runtime.py(那里解码耗时是可控变量,而它正是病根所在)。
async function holdStill(browser, origin) {
    const got = await countScans(browser, origin, 4200);
    return { ok: got.n === 1 && got.errs.length === 0, ...got };
}

// 拿走再举回来:blink 素材举 2s / 空 2s 循环,5.5s 窗口跨过第二次举起(t≈4.1s),
// 离第三次(t=8s)还有 2.5s 余量 → 只能是 2 件。去重要是把「离开」也吞了,这里会是 1。
async function leaveReturn(browser, origin) {
    const got = await countScans(browser, origin, 5500);
    return { ok: got.n === 2, ...got };
}

// ── ④ 条码枪楔子:真键盘事件 + 不抢已聚焦输入框 ──────────────────────────
// 某个框上的某个收尾键有没有被楔子吃掉。找不到那一条就返回 null —— 判据失效必须显形,
// 不能因为「没记到」而默默变成 false 让断言过去。
function endKeyEaten(rows, key, id) {
    const row = rows.filter((r) => r[0] === key && r[1] === id).pop();
    return row ? row[2] : null;
}

async function wedge(browser, origin) {
    const page = await fresh(browser, origin);
    await page.evaluate(() => {
        window.__hits = [];
        document.body.innerHTML =
            '<input id="plain"><input id="optin" data-enable-barcode>' +
            // 效期框那两档并排放:同一串按键,一个声明了 gun、一个没声明。
            '<input id="exp" type="date" data-enable-barcode="gun">' +
            // 人手填日期另起两个框:date 控件的段光标会停在上一次输到的那一段,在扫过的
            // 那个框里接着打就不是「从头填一个日期」了。声明/没声明各一个,好做同题对照。
            '<input id="exp2" type="date" data-enable-barcode="gun">' +
            '<input id="exp2-bare" type="date">' +
            '<input id="exp-bare" type="date">' +
            '<button id="btn">x</button>';
        window.PearnlyScanWedge.register((code, target) =>
            window.__hits.push([code, target && target.id])
        );
        // 冒泡阶段记 defaultPrevented:楔子挂在 capture 阶段,所以这里读到的就是它的决定。
        // 「枪的回车吃没吃掉」只能这么验 —— 靠焦点跑没跑掉去推,会被 date 控件的分段 Tab 骗过去。
        window.__endKeys = [];
        document.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter' || ev.key === 'Tab')
                window.__endKeys.push([ev.key, ev.target.id, ev.defaultPrevented]);
        });
    });
    await page.click('#btn');
    await page.keyboard.type(EXPECT_CODE, { delay: 0 }); // delay:0 = 枪速
    await page.keyboard.press('Enter');
    const fromButton = await page.evaluate(() => window.__hits.slice());

    await page.click('#plain'); // 光标在普通输入框里 → 不许抢(店员在打字)
    await page.keyboard.type('123456', { delay: 0 });
    await page.keyboard.press('Enter');
    const plainValue = await page.inputValue('#plain');
    const afterPlain = await page.evaluate(() => window.__hits.length);

    await page.click('#optin'); // 显式 opt-in 的框里要接枪
    await page.keyboard.type('4901234567894', { delay: 0 });
    await page.keyboard.press('Enter');
    const hits = await page.evaluate(() => window.__hits.slice());

    // 效期框:node 桩里 value 是什么全由桩自己说了算,「浏览器把 4901234567894 吃成什么」
    // 只有真 Chrome 的 date 控件答得出来 —— 所以这三段必须在这里跑。
    // 用 focus() 不用 click():点 date 控件是点在哪一段就从哪一段开始输,月/日/年三段的
    // 起点随机,同一串按键出来的日期就不一样。focus() 一律从第一段起,结果才可复现。
    await page.focus('#exp-bare'); // 没声明:整发被吞(零回调),框里留下一个荒唐的年份
    await page.keyboard.type(SCAN_INTO_DATE, { delay: 0 });
    await page.keyboard.press('Enter');
    const bare = {
        value: await page.inputValue('#exp-bare'),
        hits: await page.evaluate(() => window.__hits.length),
    };

    await page.focus('#exp'); // 声明 gun:枪扫走回调,框还原到扫之前(空)
    await page.keyboard.type(SCAN_INTO_DATE, { delay: 0 });
    await page.keyboard.press('Enter');
    const gunScan = {
        value: await page.inputValue('#exp'),
        hits: await page.evaluate(() => window.__hits.slice()),
    };

    // 人手填日期(8 位,长度这条判据一个都拦不住,全靠速度分开)→ 声明了也不许抢。
    // 判据是「跟没声明的框敲出来一模一样」,不写死某个日期串:date 控件的段顺序跟浏览器
    // 语言走(这台是 YYYY-MM-DD),写死等于在验语言环境,换台机器就假红。
    const humanDate = async (id) => {
        await page.focus(id);
        await page.keyboard.type('20270331', { delay: 90 }); // 90ms/字符:高于枪速上限
        await page.keyboard.press('Tab');
        return page.inputValue(id);
    };
    const typed = {
        gun: await humanDate('#exp2'),
        bare: await humanDate('#exp2-bare'),
        hits: await page.evaluate(() => window.__hits.length),
        endKeys: await page.evaluate(() => window.__endKeys.slice()),
    };
    await page.screenshot({ path: path.join(SHOTS, '03-wedge.png') });
    await page.close();

    const ok =
        fromButton.length === 1 &&
        fromButton[0][0] === EXPECT_CODE &&
        fromButton[0][1] === 'btn' &&
        plainValue === '123456' &&
        afterPlain === 1 &&
        hits.length === 2 &&
        hits[1][0] === '4901234567894' &&
        hits[1][1] === 'optin' &&
        // 没声明那档维持原样(引擎不替使用方做主):零回调 + 框里留着那截垃圾
        bare.hits === 2 &&
        bare.value !== '' &&
        // 声明了 gun:回调到了、目标是那个框、框还原成空
        gunScan.hits.length === 3 &&
        gunScan.hits[2][0] === SCAN_INTO_DATE &&
        gunScan.hits[2][1] === 'exp' &&
        gunScan.value === '' &&
        // 人手填的日期原样留下(声明与否结果一致),一条回调都不许多,
        // Tab 不许被吃(吃了焦点纹丝不动,店员只看到「弹窗卡住了」)
        typed.hits === 3 &&
        typed.gun === typed.bare &&
        typed.gun !== '' && // 两边都空也算"一致" —— 得先证明这串真敲进去了
        endKeyEaten(typed.endKeys, 'Enter', 'exp') === true &&
        endKeyEaten(typed.endKeys, 'Tab', 'exp2') === false;
    return { ok, fromButton, plainValue, afterPlain, hits, bare, gunScan, typed };
}

function launch(file) {
    return chromium.launch({
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            `--use-file-for-fake-video-capture=${file}`,
        ],
    });
}

(async () => {
    const missing = [
        [Y4M, '_scan_ean_y4m.py'],
        [JITTER, '_scan_ean_jitter_y4m.py'],
        [BLINK, '_scan_ean_blink_y4m.py'],
    ].filter(([p]) => !fs.existsSync(p));
    if (missing.length) {
        for (const [p, gen] of missing) {
            console.error(`缺假摄像头素材 ${p} —— 先跑 python scripts/${gen} ${p}`);
        }
        process.exit(2);
    }
    fs.mkdirSync(SHOTS, { recursive: true });
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const report = {};
    for (const [file, run] of [
        [
            Y4M,
            async (b) => {
                report.liveDecode = await liveDecode(b, origin);
                report.errorBuckets = await errorBuckets(b, origin);
                report.wedge = await wedge(b, origin);
            },
        ],
        [
            JITTER,
            async (b) => {
                report.holdStill = await holdStill(b, origin);
            },
        ],
        [
            BLINK,
            async (b) => {
                report.leaveReturn = await leaveReturn(b, origin);
            },
        ],
    ]) {
        const browser = await launch(file);
        try {
            await run(browser);
        } finally {
            await browser.close();
        }
    }
    server.close();

    const failed = Object.keys(report).filter((k) => !report[k].ok);
    console.log(JSON.stringify(report, null, 2));
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : `PASS · 截图在 ${SHOTS}`);
    process.exit(failed.length ? 1 : 0);
})().catch((e) => {
    console.error('SMOKE CRASH', e);
    process.exit(2);
});
