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
const GHOST = '9999999999999'; // 库里没有这个码
const GUN_DELAY = 8; // 枪速:远小于楔子 MAX_GAP_MS=150
const HUMAN_DELAY = 260; // 人手打字:每个字符都超过 150ms → 一串都攒不起来

// 真产物直接从工作树喂给浏览器(dist/*.js、home.html、pos.html 都是本仓真文件)。
// /api/** 落到这里 = 404,由各脚本用 page.route 接管。
function serve() {
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        const fp = path.join(ROOT, rel || 'home.html');
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
    shotter,
    runCases,
};
