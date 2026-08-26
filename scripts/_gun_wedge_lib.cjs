/*
 * scripts/_gun_wedge_lib.cjs · 条码枪验收的共用地基(静态服务 / 真键盘 / 跑批)
 *
 * 两个验收脚本(收银主屏 _gun_wedge_pos_verify.cjs、入库弹窗 _gun_wedge_inv_verify.cjs)
 * 共用这一层。抽出来的都是「怎么把浏览器摆到位」,不含任何断言 —— 断言必须留在各自脚本里,
 * 挪到公共层就没人看得出某一绿是断了什么。
 */
const fs = require('fs');
const http = require('http');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const MIME = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' };

const PHONE = { width: 390, height: 780 };
const DESKTOP = { width: 1280, height: 900 };

const BOX = '8850999320014'; // 箱码(ลัง · ฿350)
const BOTTLE = '8850999320007'; // 瓶码(ขวด · ฿15)· 同一件货的另一个单位
// 库里没有这个码。写成 ...994 而不是全 9:楔子把「一串一模一样的字符」当按住键不放挡掉
// (looksLikeGun 的 hasTwoDistinct),全 9 的假码在声明接枪的框里会被静默丢掉 —— 那时验的
// 就不是「未建档怎么指路」,而是这条测试自己造的死角。末位 4 也让它是个校验位对的 EAN-13。
const GHOST = '9999999999994';
const GUN_DELAY = 8; // 枪速:远小于楔子 MAX_GAP_MS=150
const HUMAN_DELAY = 260; // 人手打字:每个字符都超过 150ms → 一串都攒不起来

// 真产物直接从工作树喂给浏览器(dist/*.js、home.html、pos.html 都是本仓真文件)。
// /api/** 落到这里 = 404,由各脚本用 page.route 接管。
function serve() {
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        // cowork / erp / home(以及原 home.html / 空路径)都落到 home.html —— 路由名随 app 走,
        // 但静态地基只认这一个真文件。
        const page = ['cowork', 'erp', 'home', 'home.html'].includes(rel)
            ? 'home.html'
            : rel || 'home.html';
        const fp = path.join(ROOT, page);
        const ok = fp.startsWith(ROOT) && fs.existsSync(fp) && !fs.statSync(fp).isDirectory();
        res.writeHead(ok ? 200 : 404, {
            'content-type': ok ? MIME[path.extname(fp)] || 'application/octet-stream' : 'text/html',
        });
        if (ok) fs.createReadStream(fp).pipe(res);
        else res.end('not found');
    });
    return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

// 焦点不在输入框 = 楔子该收(它唯一的判据)。BODY / BUTTON 都算,别把判据写成某一个 tag。
const notInField = (f) => f.tag !== 'INPUT' && f.tag !== 'TEXTAREA';

/**
 * 枪 = 一串极快的真按键 + 一个 Enter。不用 fill():fill 直接改 value,楔子的 keydown
 * 一个都收不到,那种绿是假的。扫之前先把 activeElement 记下来 —— 事后才说得清这一绿的前提。
 */
async function gun(page, code, delay) {
    const focus = await page.evaluate(() => {
        const el = document.activeElement;
        return { tag: (el && el.tagName) || '', id: (el && el.id) || '' };
    });
    await page.keyboard.type(code, { delay: delay === undefined ? GUN_DELAY : delay });
    await page.keyboard.press('Enter');
    return focus;
}

/**
 * 硬件枪的按键节奏与页面忙不忙无关 —— 键盘照自己的时钟发,页面忙的时候它们在浏览器进程里排队。
 *
 * page.keyboard.type 做不到这件事:它 await 每一发的派发,主线程一卡它自己也跟着停,于是
 * 「长任务」被偷换成「枪打得慢」—— 事件产生时刻跟着一起晚,而楔子量的正是产生时刻,这条
 * 最要命的对抗输入就永远验不出来(实测:同一场景 keyboard.type 的 stampGaps 里也出现 139ms
 * 的坎,CDP 发了就走则是 22.3ms)。凡是要在「主线程被堵住」下验枪的用例,只能走这一条。
 *
 * @param cdp  page.context().newCDPSession(page) 拿到的会话
 * @param delayMs 字符间隔;suffix 是枪的结束符(通常 Enter),跟正文同一个节拍发
 */
async function cdpGun(cdp, text, delayMs, suffix) {
    const send = (p) => cdp.send('Input.dispatchKeyEvent', p).catch(() => {});
    for (const ch of text) {
        const code = ch.charCodeAt(0);
        send({ type: 'keyDown', key: ch, text: ch, windowsVirtualKeyCode: code });
        send({ type: 'keyUp', key: ch, windowsVirtualKeyCode: code });
        await new Promise((r) => setTimeout(r, delayMs === undefined ? GUN_DELAY : delayMs));
    }
    if (suffix) send({ type: 'keyDown', key: suffix, code: suffix, windowsVirtualKeyCode: 13 });
}

/** 在这一串的第 nth 个 keydown 上让主线程同步忙 ms —— 与真实重渲/GC/同步写 localStorage 同形。
 *  挂 window 捕获(早于 document 捕获)→ 楔子拿到这一发之前主线程已经被堵住了。 */
async function armLongTask(page, nth, ms) {
    await page.evaluate(
        ([atNth, blockMs]) => {
            window.__lt = { n: 0, blocked: 0 };
            window.__ltProbe = () => {
                window.__lt.n += 1;
                if (window.__lt.n !== atNth) return;
                const end = Date.now() + blockMs;
                while (Date.now() < end) {
                    /* 同步长任务 */
                }
                window.__lt.blocked = blockMs;
            };
            window.addEventListener('keydown', window.__ltProbe, true);
        },
        [nth, ms]
    );
}

/** 两把尺子一起量:stamp = 事件产生的时刻(楔子用的那把),perf = 处理器真被调用的时刻。 */
async function armTwoRulers(page) {
    await page.evaluate(() => {
        window.__log = [];
        // repeat 一起记:键盘自动重复能打进枪速区间,那一路只有这个标志分得开(不靠速度)
        window.__probe = (ev) =>
            window.__log.push({
                stamp: ev.timeStamp,
                perf: performance.now(),
                repeat: !!ev.repeat,
            });
        document.addEventListener('keydown', window.__probe, true);
    });
}

async function readTwoRulers(page) {
    const log = await page.evaluate(() => {
        document.removeEventListener('keydown', window.__probe, true);
        if (window.__ltProbe) window.removeEventListener('keydown', window.__ltProbe, true);
        return { log: window.__log, blocked: (window.__lt || {}).blocked || 0 };
    });
    const gaps = (k) =>
        log.log.slice(1).map((e, i) => Math.round((e[k] - log.log[i][k]) * 10) / 10);
    const stamp = gaps('stamp');
    const perf = gaps('perf');
    return {
        n: log.log.length,
        blockedMs: log.blocked,
        stampGaps: stamp,
        perfGaps: perf,
        stampMax: stamp.length ? Math.max(...stamp) : 0,
        perfMax: perf.length ? Math.max(...perf) : 0,
        repeats: log.log.filter((e) => e.repeat).length,
    };
}

/**
 * 人手往 <input type=date> 里填一个日期。
 *
 * 不能直接打 8 位数字:段的顺序跟浏览器 locale 走,同一串 '12312027' 在 en-US 下是 12/31/2027,
 * 在 ISO 那一档里年份段会一口气吃掉六位,留下 123120-02-07 —— 断言于是在验 locale,不在验产品。
 * 顺序现场从 Intl.DateTimeFormat 取,段间按 ArrowRight(那不是可打印键,楔子会跳过它,
 * 这一串在楔子眼里仍是一发)。
 */
async function typeDateByHand(page, iso, delayMs) {
    const order = await page.evaluate(() =>
        new Intl.DateTimeFormat()
            .formatToParts(new Date())
            .map((p) => p.type)
            .filter((t) => t === 'year' || t === 'month' || t === 'day')
    );
    const seg = { year: iso.slice(0, 4), month: iso.slice(5, 7), day: iso.slice(8, 10) };
    for (let i = 0; i < order.length; i++) {
        await page.keyboard.type(seg[order[i]], { delay: delayMs });
        if (i < order.length - 1) await page.keyboard.press('ArrowRight');
    }
}

function shotter(dir) {
    fs.mkdirSync(dir, { recursive: true });
    return (page, name) => page.screenshot({ path: path.join(dir, name) });
}

/** 一例崩了不影响后面几例:崩的那例记 crash 并算 FAIL,最后按退出码给结论。 */
async function runCases(cases, run, reportPath) {
    const report = {};
    for (const [name, fn] of cases) {
        try {
            report[name] = await run(fn);
        } catch (e) {
            report[name] = { ok: false, crash: String(e && e.message ? e.message : e) };
        }
        console.log(`${report[name].ok ? 'PASS' : 'FAIL'} ${name}`);
    }
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    const failed = Object.keys(report).filter((k) => !report[k].ok);
    console.log(JSON.stringify(report, null, 2));
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : `PASS · 报告 ${reportPath}`);
    return failed.length;
}

module.exports = {
    ROOT,
    PHONE,
    DESKTOP,
    BOX,
    BOTTLE,
    GHOST,
    GUN_DELAY,
    HUMAN_DELAY,
    serve,
    notInField,
    gun,
    cdpGun,
    armLongTask,
    armTwoRulers,
    readTwoRulers,
    typeDateByHand,
    shotter,
    runCases,
};
