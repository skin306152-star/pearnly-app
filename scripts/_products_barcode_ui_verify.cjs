/*
 * scripts/_products_barcode_ui_verify.cjs · 建品表单条码位的真浏览器验收
 *
 * 验的是真 dist/main.js(不是源码 grep):真 Chromium + 假摄像头(y4m 里举着一张泰国
 * EAN-13)+ 桩 API。被断言的 id/class/元素全来自真产物,只有接口返回的数据是桩。
 * 文案一个字都不注入:期望值现场从页面里的真 window.I18N 取。旧版把自带的一份中文 COPY
 * 无条件写进全部四种语言,又把语言键写成 'lang'(真键是 mrpilot_lang,于是语言从没切过),
 * 结果是泰文界面配中文提示还全绿 —— 拿自己比自己,漏译天然照不出来。
 *
 * 重点验三件在静态断言里验不出来的事:
 *   ① 取景框在屏幕上的真实像素框 ÷ 画面像素框 == 商品引擎 cropRatio(0.8 × 0.44)——
 *      不等就是「框里对准了却读不出」,只有量真盒子才发现;
 *   ② 撞码真的拦住保存(监听有没有发出 POST),不是「红字显示了就算拦了」;
 *   ③ 查不了(500)不冒充「这个码没人用」——两种截然相反的结论不能长得一样。
 *
 * 跑法(仓库根目录):
 *   python scripts/_scan_ean_y4m.py .scan_fixture.y4m
 *   node scripts/_products_barcode_ui_verify.cjs .scan_fixture.y4m
 * 退出码 0 = 全过。截图落 tests/e2e/_artifacts/products_barcode/。
 */
/* eslint-disable no-undef */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const Y4M = path.resolve(process.argv[2] || '.scan_fixture.y4m');
const OUT = path.resolve(
    process.argv[3] || path.join(ROOT, 'tests', 'e2e', '_artifacts', 'products_barcode')
);
const SCAN_CODE = '8850999320014'; // y4m 里那张码
const DUP_CODE = '8851959132074';
const LANG = 'zh'; // 泰文那一屏另有 _sx_barcode_copy_accept.cjs 专验
const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.map': 'application/json',
};

const DUP_PRODUCT = {
    id: 'p-dup-1',
    code: 'C-100',
    barcode: DUP_CODE,
    name_th: 'น้ำอัดลม 325 มล.',
    name_zh: '汽水 325ml',
    unit: 'กระป๋อง',
    unit_price: 15,
    vat_applicable: true,
    track_batch: false,
    image_url: null,
};

function serve() {
    const srv = http.createServer((req, res) => {
        let p = decodeURIComponent(req.url.split('?')[0]);
        if (p === '/home') p = '/home.html';
        const file = path.join(ROOT, p);
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, {
            'content-type': TYPES[path.extname(file)] || 'text/plain',
            'cache-control': 'no-store',
        });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}

const json = (body, status = 200) => ({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
});

// lookup 的回法由每条用例现改(桩里只放「这个码属于谁」这一件事)
let lookupMode = 'free';
const posts = [];

async function boot(browser, origin) {
    const ctx = await browser.newContext({ viewport: { width: 1320, height: 960 } });
    const page = await ctx.newPage();
    await page.addInitScript((lang) => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', lang); // 真语言键 · 写别的键 = 语言压根没切
        window.__scanFeedback = { starts: 0, stops: 0, vibrates: [] };
        class ScanAudioContext {
            constructor() {
                this.state = 'running';
                this.currentTime = 1;
                this.destination = {};
                this.sampleRate = 48000;
            }
            createBuffer(channels, length, rate) {
                const samples = new Float32Array(length);
                return { duration: length / rate, getChannelData: () => samples };
            }
            createBufferSource() {
                return {
                    buffer: null,
                    connect() {},
                    start: () => (window.__scanFeedback.starts += 1),
                    stop: () => (window.__scanFeedback.stops += 1),
                };
            }
        }
        window.AudioContext = ScanAudioContext;
        navigator.vibrate = (value) => window.__scanFeedback.vibrates.push(value);
    }, LANG);
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const u = req.url();
        if (req.method() === 'POST' || req.method() === 'PATCH') {
            posts.push(req.method() + ' ' + u);
            return route.fulfill(json({ ok: true, product: DUP_PRODUCT }));
        }
        if (u.includes('/api/sales/products/lookup')) {
            if (lookupMode === 'dup') return route.fulfill(json({ product: DUP_PRODUCT }));
            if (lookupMode === 'boom') return route.fulfill(json({ detail: 'oops' }, 500));
            return route.fulfill(json({ detail: 'sales.product_not_found' }, 404));
        }
        if (u.includes('/api/sales/products')) return route.fulfill(json({ products: [] }));
        if (u.includes('/api/me/plan')) return route.fulfill(json({ plan: 'lifetime' }));
        if (u.includes('/api/ocr/quota')) return route.fulfill(json({ used: 0, limit: 100 }));
        return route.fulfill(json({ ok: true, items: [] }));
    });
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto(origin + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent = '#ws-modal,#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
        window.routeTo('sales-products');
    });
    await page.waitForSelector('#sx-p-add', { timeout: 15000 });
    // 期望文案现场从页面里的真 window.I18N 取:脚本自带一份副本注进去 = 拿自己比自己,
    // 漏译永远照不出来(旧版就是泰文界面配中文提示还全绿)。
    const lang = await page.evaluate(() => window._currentLang);
    const copy = await page.evaluate((l) => window.I18N[l], lang);
    return { page, errs, lang, copy };
}

async function openNewForm(page) {
    await page.click('#sx-p-add');
    await page.waitForSelector('#sx-pf-barcode', { timeout: 8000 });
    // .modal 有 200ms 淡入:不等它停就截图会拍到半透明面板(看着像渲染坏了)
    await page.waitForFunction(
        () => {
            const box = document.querySelector('#sales-prod-mask .modal');
            return (
                !!box &&
                box.getBoundingClientRect().height > 0 &&
                getComputedStyle(box).opacity === '1'
            );
        },
        { timeout: 8000 }
    );
}

// 状态格里可能是「一句话 + 一个链接按钮」两个节点,innerText 会在中间塞换行 —— 拆开比,
// 别把渲染细节写进期望值(下次换个 <br> 就红,而文案其实没问题)。
async function stateText(page) {
    const st = await page.evaluate(() => {
        const el = document.getElementById('sx-pf-bc-state');
        if (!el) return { text: '', h: 0 };
        const r = el.getBoundingClientRect();
        return { text: el.innerText.trim(), h: r.height, color: getComputedStyle(el).color };
    });
    st.parts = st.text ? st.text.split(/\s*\n\s*/) : [];
    return st;
}

// 等查重落定:既不空也不是「正在检查…」。等它「有字」会抓到中间那一瞬;
// 等某句具体文案会在该文案漏译时超时崩掉,那时该看到的是一条 FAIL 而不是堆栈。
async function settled(page, checking) {
    await page.waitForFunction(
        (c) => {
            const s = (document.getElementById('sx-pf-bc-state')?.innerText || '').trim();
            return !!s && s !== c;
        },
        checking,
        { timeout: 8000 }
    );
}

async function run() {
    if (!fs.existsSync(Y4M)) {
        console.log(
            `缺假摄像头素材 ${Y4M} · 先跑 python scripts/_scan_ean_y4m.py .scan_fixture.y4m`
        );
        process.exit(2);
    }
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const origin = 'http://127.0.0.1:' + srv.address().port;
    const browser = await chromium.launch({
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            `--use-file-for-fake-video-capture=${Y4M}`,
        ],
    });
    let pass = 0;
    let fail = 0;
    const chk = async (k, cond) => {
        const ok = await cond;
        ok ? pass++ : fail++;
        console.log((ok ? 'PASS' : 'FAIL').padEnd(5), k);
    };

    const { page, errs, lang, copy } = await boot(browser, origin);
    await chk(`界面语言真的切成了 ${LANG}`, lang === LANG);

    // ① 条码位:扫码按钮真的画出来了 + 预期管理文案在旁边
    lookupMode = 'free';
    await openNewForm(page);
    const field = await page.evaluate(() => {
        const btn = document.getElementById('sx-pf-bc-scan');
        const row = btn && btn.closest('.sx-bc-row');
        const hint = row && row.parentElement.querySelector('.sx-field-hint');
        const b = btn && btn.getBoundingClientRect();
        return {
            btnVisible:
                !!btn && b.width > 20 && b.height > 20 && getComputedStyle(btn).display !== 'none',
            hint: hint ? hint.innerText.trim() : '',
            optIn: document.getElementById('sx-pf-barcode')?.hasAttribute('data-enable-barcode'),
        };
    });
    await chk('扫码按钮可见且够大(≥20px)', field.btnVisible);
    await chk('旁边写的是真词典里那句「只填条码」', field.hint === copy['sx-p-bc-hint']);
    await chk('条码框对条码枪 opt-in(data-enable-barcode)', field.optIn === true);
    await page.screenshot({ path: path.join(OUT, '01-field-desktop.png') });

    // ② 撞码:红字 + 「去编辑那个商品」出路,并且真的拦住保存(没有 POST 发出)
    lookupMode = 'dup';
    await page.fill('#sx-pf-barcode', '');
    await page.type('#sx-pf-barcode', DUP_CODE, { delay: 30 });
    await page.waitForSelector('#sx-bc-goedit', { timeout: 8000 });
    const dup = await stateText(page);
    await chk('撞码提示画出来了(有高度)', dup.h > 14);
    await chk(
        '撞码提示是真词条 + 带撞上的那个商品名 + 给出路',
        dup.parts.join('|') ===
            [
                copy['sx-p-bc-dup'].replace('{name}', DUP_PRODUCT.name_th),
                copy['sx-p-bc-dup-open'],
            ].join('|')
    );
    await page.screenshot({ path: path.join(OUT, '02-dup-blocked.png') });
    posts.length = 0;
    await page.fill('#sx-pf-th', 'ทดสอบ');
    await page.click('#sx-p-save');
    await page.waitForTimeout(600);
    await chk('撞码时保存被拦(零 POST/PATCH)', posts.length === 0);
    await chk('弹窗没关(还能改)', await page.isVisible('#sx-pf-barcode'));

    // ③ 「去编辑那个商品」→ 换成那个商品的编辑态(码变成它的,状态变「这是它自己的」)
    await page.click('#sx-bc-goedit');
    await page.waitForFunction(() => document.getElementById('sx-pf-code')?.value === 'C-100', {
        timeout: 8000,
    });
    await settled(page, copy['sx-p-bc-checking']);
    const self = await stateText(page);
    await chk('切到撞码那个商品的编辑态', (await page.inputValue('#sx-pf-barcode')) === DUP_CODE);
    await chk('自己的码不当撞码(不再显示「去编辑」)', !(await page.isVisible('#sx-bc-goedit')));
    await chk('明说这是它自己的码(真词条)', self.text === copy['sx-p-bc-self']);
    await page.screenshot({ path: path.join(OUT, '03-goto-that-product.png') });

    // ④ 查不了(500)≠ 没撞码:必须说查不了 + 给重查,不能长成「可用」
    lookupMode = 'boom';
    await page.click('#sx-p-close');
    await openNewForm(page);
    await page.type('#sx-pf-barcode', '9990000000001', { delay: 30 });
    await page.waitForSelector('#sx-bc-recheck', { timeout: 8000 });
    const boom = await stateText(page);
    await chk(
        '查不了时说的是真词条「查不了」+ 重查',
        boom.parts.join('|') === [copy['sx-p-bc-check-fail'], copy['sx-p-bc-recheck']].join('|')
    );
    await chk('查不了时不冒充「没人用」', !boom.text.includes(copy['sx-p-bc-free']));
    await chk('给了重查按钮', await page.isVisible('#sx-bc-recheck'));
    await page.screenshot({ path: path.join(OUT, '04-check-failed-honest.png') });
    // 重查一次(这次通)→ 状态自己纠正过来
    lookupMode = 'free';
    await page.click('#sx-bc-recheck');
    await page.waitForSelector('#sx-bc-recheck', { state: 'detached', timeout: 8000 });
    await settled(page, copy['sx-p-bc-checking']);
    await chk(
        '重查通了 → 状态改成真词条「没人用」',
        (await stateText(page)).text === copy['sx-p-bc-free']
    );
    await page.screenshot({ path: path.join(OUT, '05-free.png') });

    // ⑤a 摄像头:真解出 y4m 里那张 EAN-13 → 自动填进框 → 窗自己关 → 相机释放
    await page.click('#sx-pf-bc-scan');
    await page.waitForFunction(
        (code) => document.getElementById('sx-pf-barcode')?.value === code,
        SCAN_CODE,
        { timeout: 30000 }
    );
    await chk('真解出 y4m 里那张 EAN-13 并填进框', true);
    const feedback = await page.evaluate(() => window.__scanFeedback);
    await chk('扫中只响一次短滴声', feedback.starts === 1 && feedback.stops === 1);
    await chk('扫中只请求一次 60ms 短震动', feedback.vibrates.join(',') === '60');
    await chk('扫中后扫码弹窗自己关掉', !(await page.isVisible('#sx-bcm')));
    await chk(
        '相机已释放(video 摘掉 / srcObject 清空)',
        page.evaluate(() => {
            const v = document.querySelector('.bscan-video');
            return !v || !v.srcObject;
        })
    );
    await page.waitForFunction(
        () => (document.getElementById('sx-pf-bc-state')?.innerText || '').trim().length > 0,
        { timeout: 8000 }
    );
    await chk('扫完立刻查了一次重', true);
    await page.locator('[data-scan-success-fly]').waitFor({ state: 'attached' });
    const productVisual = await page.evaluate(() => {
        const fly = document.querySelector('[data-scan-success-fly]');
        return {
            label: fly?.querySelector('.scan-success-name')?.textContent || '',
            increment: !!fly?.querySelector('.scan-success-amount'),
            pointerEvents: fly ? getComputedStyle(fly).pointerEvents : '',
        };
    });
    await chk(
        '建品扫码有独立视觉确认且不冒充数量 +1',
        !!productVisual.label && !productVisual.increment
    );
    await chk('建品扫码动画不拦下一次输入', productVisual.pointerEvents === 'none');
    await page.screenshot({ path: path.join(OUT, '07-scanned-filled.png') });

    // ⑤b 取景框几何量真盒子。假摄像头第一帧就有码,整条链(拉包→授权→出帧→解码)不到 200ms
    // 就把窗关了,真机上是一秒多 —— 所以量之前先把 onScan 掉空,让预览停在开着的状态。
    // 被量的 video / 取景框 / CSS 全是真产物,只是不让它「扫中即关」。
    await page.evaluate(() => {
        const api = window.PearnlyScanCamera;
        const orig = api.create;
        api.create = (opts) => orig(Object.assign({}, opts, { onScan: () => {} }));
        window.__restoreCreate = () => {
            api.create = orig;
        };
    });
    await page.click('#sx-pf-bc-scan');
    let camera = null;
    try {
        const h = await page.waitForFunction(
            () => {
                const video = document.querySelector('#sx-bcm-view .bscan-video');
                if (!video || !video.videoWidth) return null;
                const vb = video.getBoundingClientRect();
                if (vb.height <= 0) return null;
                const fb = document.querySelector('.sx-bcm-frame').getBoundingClientRect();
                const controls = document.querySelector('#sx-bcm-view [data-scan-view-controls]');
                const motion = controls?.querySelector('[data-scan-motion-toggle]');
                const torch = controls?.querySelector('.scan-view-torch');
                return {
                    // 屏幕上的取景框 ÷ 画面 == 引擎 cropRatio,才叫「框里」
                    frameW: fb.width / vb.width,
                    frameH: fb.height / vb.height,
                    centeredX: Math.abs(fb.left + fb.width / 2 - (vb.left + vb.width / 2)),
                    centeredY: Math.abs(fb.top + fb.height / 2 - (vb.top + vb.height / 2)),
                    msg: document.getElementById('sx-bcm-msg').innerText.trim(),
                    manual: (document.getElementById('sx-bcm-manual')?.innerText || '').trim(),
                    tracksLive: video.srcObject.getTracks().filter((t) => t.readyState === 'live')
                        .length,
                    controls: {
                        exists: !!controls,
                        motionChecked: !!motion?.checked,
                        motionLabel: motion?.parentElement?.textContent?.trim() || '',
                        pointerEvents: controls ? getComputedStyle(controls).pointerEvents : '',
                        torchHidden: !!torch?.hidden,
                    },
                };
            },
            null,
            { timeout: 15000, polling: 60 }
        );
        camera = await h.jsonValue();
    } catch (_) {
        console.log('FAIL  摄像头预览没量到(取景框/画面盒子)');
        fail++;
        camera = {
            frameW: 0,
            frameH: 0,
            centeredX: 99,
            centeredY: 99,
            msg: '',
            manual: '',
            tracksLive: 0,
            controls: {},
        };
    }
    await chk('取景框宽占缩放画面 80%(±2%)', Math.abs(camera.frameW - 0.8) < 0.02);
    await chk('取景框高占缩放画面 44%(±2%)', Math.abs(camera.frameH - 0.44) < 0.02);
    await chk('取景框居中(与画面中心差 <3px)', camera.centeredX < 3 && camera.centeredY < 3);
    await chk('相机正常出画时给的是真词条「对准框」不是转圈', camera.msg === copy['sx-p-bc-aim']);
    await chk('扫码弹窗给了手动输入的出路(真词条)', camera.manual === copy['bscan.manual']);
    await chk('相机真开着(live track ≥1)', camera.tracksLive >= 1);
    await chk(
        '建品取景框有默认开启的扫码动画开关',
        camera.controls.exists &&
            camera.controls.motionChecked &&
            camera.controls.motionLabel === copy['scan-controls.animation'] &&
            camera.controls.pointerEvents === 'auto'
    );
    await chk('假摄像头不支持补光时不显示无效手电筒按钮', camera.controls.torchHidden);
    await page.screenshot({ path: path.join(OUT, '06-camera-scanning.png') });
    await page.click('#sx-bcm-x');
    await page.evaluate(() => window.__restoreCreate());
    await chk(
        '手动关窗后相机也释放',
        page.evaluate(() => !document.querySelector('.bscan-video'))
    );

    // ⑥ 条码枪:焦点不在输入框上时,枪速输入也进条码框
    await page.click('#sx-p-close');
    await openNewForm(page);
    await page.evaluate(() => document.querySelector('.modal-title').focus());
    for (const ch of '8859999000015') await page.keyboard.press(ch, { delay: 8 });
    await page.keyboard.press('Enter');
    await page.waitForFunction(
        () => document.getElementById('sx-pf-barcode')?.value === '8859999000015',
        { timeout: 5000 }
    );
    await chk('条码枪(快键入+回车)填进条码框', true);
    await chk('枪的回车没把弹窗顶掉', await page.isVisible('#sx-pf-barcode'));

    // ⑦ 跨页带码:别处扫到未建档 → 跳商品页 + 新建表单已带码
    await page.click('#sx-p-close');
    await page.evaluate(() => window.routeTo('dashboard'));
    await page.evaluate((code) => window.openProductFormWithBarcode(code), '8850000000992');
    await page.waitForSelector('#sx-pf-barcode', { timeout: 10000 });
    await chk('落在商品页', (await page.evaluate(() => location.hash)) === '#/sales-products');
    await chk('新建表单已带码', (await page.inputValue('#sx-pf-barcode')) === '8850000000992');
    await chk('带码进来也立刻查了重', (await stateText(page)).text.length > 0);
    await page.screenshot({ path: path.join(OUT, '08-handoff-prefilled.png') });

    // ⑧ 这台设备扫不了(非 HTTPS / 浏览器没接口):按钮不显示,但原因必须写出来 —— Odoo 在这
    // 一档让按钮静默消失,用户只觉得「功能没了」。探针改成非 HTTPS,看这一屏怎么说。
    await page.click('#sx-p-close');
    await page.evaluate(() => {
        const cam = window.PearnlyScanCamera;
        window.__origReason = cam.unsupportedReason;
        cam.unsupportedReason = () => 'insecure_context';
    });
    await openNewForm(page);
    const noCam = await page.evaluate(() => {
        const cell = document.getElementById('sx-pf-barcode').closest('.sx-bc-row').parentElement;
        const hints = Array.from(cell.querySelectorAll('.sx-field-hint'));
        return {
            btn: !!document.getElementById('sx-pf-bc-scan'),
            texts: hints.map((h) => h.innerText.trim()),
            visible: hints.every((h) => h.getBoundingClientRect().height > 0),
        };
    });
    await chk('扫不了时不显示摄像头按钮', noCam.btn === false);
    // 产品把两句拼在一格里:「为什么点不动」·「还能怎么扫」。分开断,漏哪句都看得出来。
    const why = copy['bscan.err.insecure'] + ' · ' + copy['sx-p-bc-gun'];
    await chk('把原因 + 其他出路写出来了(真词条 · 不静默隐藏)', noCam.texts.includes(why));
    await chk('原因文字真画出来了(非零高度)', noCam.visible);
    await page.screenshot({ path: path.join(OUT, '10-no-camera-reason.png') });
    await page.evaluate(() => {
        window.PearnlyScanCamera.unsupportedReason = window.__origReason;
    });
    await page.click('#sx-p-close');
    await openNewForm(page);

    // ⑨ 手机 390:两列塌成一列,条码位与提示不被裁
    await page.setViewportSize({ width: 390, height: 780 });
    await page.waitForTimeout(300);
    const mob = await page.evaluate(() => {
        const inp = document.getElementById('sx-pf-barcode');
        const btn = document.getElementById('sx-pf-bc-scan');
        const st = document.getElementById('sx-pf-bc-state');
        const r = inp.getBoundingClientRect();
        const b = btn.getBoundingClientRect();
        return {
            inRow: Math.abs(r.top - b.top) < 6,
            noOverflow: b.right <= window.innerWidth + 1 && r.left >= -1,
            stateVisible: st.getBoundingClientRect().width > 100,
            tap: Math.min(b.width, b.height),
        };
    });
    await chk('手机端按钮与输入框同一行不换行', mob.inRow);
    await chk('手机端不溢出屏幕', mob.noOverflow);
    await chk('手机端状态区仍有宽度', mob.stateVisible);
    await chk('扫码按钮触控目标 ≥36px', mob.tap >= 36);
    await page.screenshot({ path: path.join(OUT, '09-mobile-390.png'), fullPage: true });

    await chk('零 console pageerror', errs.length === 0);
    if (errs.length) console.log('pageerror:', errs.slice(0, 3));

    await browser.close();
    srv.close();
    console.log(`\n${pass} pass / ${fail} fail · 截图 ${OUT}`);
    process.exit(fail ? 1 : 0);
}
run().catch((e) => {
    console.error(e);
    process.exit(1);
});
