// Pearnly AI · IN-0b · 收料诚实化(文件夹拖入/队列续传/密码 PDF 卡/盘点条) · 本地 stub
// 真浏览器验收(非 CI 用例 · 用完即删,同 _in0d_client_import_verify.spec.js 先例)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**:直接开
// #/client/c1/intake,后端全走本文件内的脚本化 mock(网关探针 listOrders/getClient/
// getOrder/materials),真实浏览器驱动 DOM 事件(拖拽/键盘输入/点击),观察真渲染出的
// HTML(isVisible + getComputedStyle + innerText),不是 grep 类名。
//
// 真实乱料:密码 PDF / 嵌套 zip 直接投 tests/fixtures/messy_intake_pack/ 的真文件
// (setInputFiles 走真实 multipart 编码),密码 keyboard.type 真按键(page.fill 假绿教训)。
// 文件夹拖入用真实浏览器 File + 手写 FileSystemEntry 桩(webkitGetAsEntry 只有真实 OS
// 拖拽才会产生原生对象,Playwright 无法发起真 OS 拖拽——桩对象满足与production代码
// 完全相同的 isFile/isDirectory/file()/createReader().readEntries() 接口契约,驱动的是
// static/ai/ai-intake-queue.js 的真实 entryToNode/walkDataTransferItems 递归遍历代码,
// 不是另起一套假逻辑断言"应该对了")。
//
// 起法:npx playwright test tests/e2e/_in0b_intake_honesty_verify.spec.js
/* global document, window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

const ROOT = path.resolve(__dirname, '..', '..');
const PORT = 8985;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'in0b');
const FIXTURES = path.join(ROOT, 'tests', 'fixtures', 'messy_intake_pack');

let server;

function waitUp(url, tries = 40) {
    return new Promise((resolve, reject) => {
        const hit = (n) => {
            http.get(url, (r) => {
                r.resume();
                resolve();
            }).on('error', () => {
                if (n <= 0) return reject(new Error('server not up'));
                setTimeout(() => hit(n - 1), 150);
            });
        };
        hit(tries);
    });
}

test.beforeAll(async () => {
    server = spawn('python', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], {
        cwd: ROOT,
        stdio: 'ignore',
    });
    await waitUp(`${BASE}/static/dist/ai.html`);
});

test.afterAll(() => {
    if (server) server.kill();
});

// materialsHandler(route, request) 每个用例注入自己的 addMaterials 剧本(密码/网络失败/
// 成功次序);缺省即空成功(不测上传结果的用例够用)。seedQueue 供续传横幅用例在导航前
// 塞一份 localStorage 队列残留(同 mrpilot_token/lang 一起进 addInitScript,不必另开
// 一份路由 mock)。
async function bootIntake(
    page,
    { lang = 'en', materialsHandler, orderNeeds = [], seedQueue } = {}
) {
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const p = url.pathname;
        const method = req.method();

        if (p === '/api/workorder/orders' && method === 'GET') {
            return route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ orders: [{ id: 'wo-1', period: '2569-05' }] }),
            });
        }
        if (p === '/api/workorder/orders/wo-1' && method === 'GET') {
            return route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({
                    id: 'wo-1',
                    status: 'stuck',
                    needs: orderNeeds,
                    numbers: {},
                    flagged: [],
                }),
            });
        }
        if (p === '/api/workorder/orders/wo-1/materials' && method === 'POST') {
            if (materialsHandler) return materialsHandler(route, req);
            return route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ registered: [], count: 0 }),
            });
        }
        if (p === '/api/workspace/clients/c1' && method === 'GET') {
            return route.fulfill({
                contentType: 'application/json',
                body: JSON.stringify({ client: { id: 'c1', name: 'Test Client' } }),
            });
        }
        return route.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([l, seed]) => {
            window.localStorage.setItem('mrpilot_token', 'tok-in0b');
            window.localStorage.setItem('mrpilot_lang', l);
            if (seed) window.localStorage.setItem('pearnly_ai_intake_queue_wo-1', seed);
        },
        [lang, seedQueue ? JSON.stringify(seedQueue) : null]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/client/c1/intake`);
    await page.waitForSelector('#v-client.on', { timeout: 15000 });
    await page.waitForSelector('#ikDrop', { timeout: 15000 });
}

// 多部分表单体里取某字段的值(判断真按键最终传上去的密码是什么,不只信调用次序)。
function multipartField(body, field) {
    const re = new RegExp(`name="${field}"\\r?\\n\\r?\\n([^\\r\\n]*)`);
    const m = re.exec(body || '');
    return m ? m[1] : null;
}

// pdf_password_required 422 剧本(供跳过/四语/手机三个用例复用,message 内容对断言无关)。
function passwordRequiredRoute(route) {
    return route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
            detail: {
                code: 'workorder.intake.pdf_password_required',
                message: { en: 'Password required', zh: '需要密码', th: 'x', ja: 'x' },
                filename: 'password_protected.pdf',
            },
        }),
    });
}

test.describe('IN-0b · 收料诚实化(本地 stub 真浏览器)', () => {
    test('文件夹拖入(≥15 件混合子目录)→ 盘点条计数与实际一致', async ({ page }) => {
        await bootIntake(page, {
            materialsHandler: (route) =>
                route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({
                        registered: Array.from({ length: 15 }, (_, i) => ({
                            item_id: `it-${i}`,
                            file_ref: `f-${i}`,
                        })),
                        count: 15,
                    }),
                }),
        });

        // 构造:client_may/(5 图) + client_may/sub_a/(5 pdf) + client_may/sub_a/sub_c/(5 png)
        // = 15 件合规叶子;顶层另有 1 空文件 + 1 不支持格式,拒收清单须逐件点名。
        await page.evaluate(() => {
            function fileEntry(name, byteLen) {
                return {
                    isFile: true,
                    isDirectory: false,
                    name: name,
                    file(success) {
                        success(new File([new Uint8Array(byteLen)], name));
                    },
                };
            }
            function dirEntry(name, children) {
                let served = false;
                return {
                    isFile: false,
                    isDirectory: true,
                    name: name,
                    createReader() {
                        return {
                            readEntries(cb) {
                                if (served) {
                                    cb([]);
                                    return;
                                }
                                served = true;
                                cb(children);
                            },
                        };
                    },
                };
            }
            // client_may/(5 图) + client_may/sub_a/(5 pdf) + client_may/sub_a/sub_c/(5 png)
            // = 15 件合规叶子(两层子目录都要展平);顶层另有 1 空文件 + 1 不支持格式。
            const top = [];
            for (let i = 0; i < 5; i++) top.push(fileEntry(`photo_${i}.jpg`, 200));
            const subA = [];
            for (let i = 0; i < 5; i++) subA.push(fileEntry(`bank_${i}.pdf`, 200));
            const subC = [];
            for (let i = 0; i < 5; i++) subC.push(fileEntry(`scan_${i}.png`, 200));
            const subADir = dirEntry('sub_a', subA.concat([dirEntry('sub_c', subC)]));
            const tree = dirEntry('client_may', [
                ...top,
                subADir,
                fileEntry('empty.jpg', 0),
                fileEntry('notes.docx', 500),
            ]);
            const items = [{ webkitGetAsEntry: () => tree }];
            const dt = { items, files: [] };
            const evt = new Event('drop', { bubbles: true, cancelable: true });
            Object.defineProperty(evt, 'dataTransfer', { value: dt });
            document.getElementById('ikDrop').dispatchEvent(evt);
        });

        // 展开是异步的(readEntries 走 Promise 链)——等文件计数条出现,不硬 sleep。
        await expect(page.locator('.dz-count b')).toHaveText('15', { timeout: 8000 });
        // 拒收清单已经出现(还没点上传就该看到——文件夹里的不支持件不静默吞)。
        const manifestBeforeUpload = page.locator('.manifest-card');
        await expect(manifestBeforeUpload).toBeVisible();
        await expect(manifestBeforeUpload).toContainText('empty.jpg');
        await expect(manifestBeforeUpload).toContainText('notes.docx');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '01-folder-rejected-precheck.png') });

        await page.click('[data-action="ik-upload"]');
        // 时序修法(J-B R2 打回·真诊断非产品坏):拖拽预检阶段(点上传前)盘点条已经在显示
        // 2 件拒收的 chip,`chips.first()` 一开始就满足可见——不是"上传落定"的可靠信号。
        // 落盘 15 件是异步(POST /materials resolve 才回填 manifest.accepted),原来紧跟着的
        // 一次性 innerText() 读在网络慢/CI 更挤时能在 accepted 回填前抢先读到「0 accepted」
        // (400ms 人工延迟本地稳定复现 5/5 次·加浏询等待后 5/5 次绿,证明产品数据本身对,
        // 纯粹是断言没等异步落定)。改自愈轮询断言直接等最终态,不改产品代码。
        const ciCounts = page.locator('.manifest-card .ci-counts');
        await expect(ciCounts).toContainText('15', { timeout: 8000 }); // 收进 15 件
        await expect(ciCounts).toContainText('2', { timeout: 8000 }); // 拒收 2 件(empty + docx)
        await expect
            .poll(
                async () => {
                    const rows = await page.locator('.manifest-card .mx-table tr').allInnerTexts();
                    return {
                        empty: rows.some((r) => r.includes('empty.jpg')),
                        docx: rows.some((r) => r.includes('notes.docx')),
                    };
                },
                { timeout: 8000 }
            )
            .toEqual({ empty: true, docx: true });
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '02-folder-manifest-final.png') });
    });

    test('密码 PDF → 供钥卡(四语)→ 错密码可重试 → 对密码通过', async ({ page }) => {
        let call = 0;
        await bootIntake(page, {
            materialsHandler: async (route, req) => {
                call += 1;
                const buf = req.postDataBuffer();
                const body = buf ? buf.toString('utf8') : '';
                const pw = multipartField(body, 'password');
                if (call === 1) {
                    expect(pw).toBeNull();
                    return route.fulfill({
                        status: 422,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            detail: {
                                code: 'workorder.intake.pdf_password_required',
                                message: {
                                    en: 'Password required',
                                    zh: '需要密码',
                                    th: '',
                                    ja: '',
                                },
                                filename: 'password_protected.pdf',
                            },
                        }),
                    });
                }
                if (call === 2) {
                    expect(pw).toBe('0000');
                    return route.fulfill({
                        status: 422,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            detail: {
                                code: 'workorder.intake.pdf_password_wrong',
                                message: { en: 'Wrong password', zh: '密码错误', th: '', ja: '' },
                                filename: 'password_protected.pdf',
                            },
                        }),
                    });
                }
                expect(pw).toBe('1234'); // 真实乱料包密码(见 _build_fixtures.py PDF_PASSWORD)
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({ registered: [{ item_id: 'p1' }], count: 1 }),
                });
            },
        });

        await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'password_protected.pdf'));
        await expect(page.locator('.dz-count b')).toHaveText('1');
        await page.click('[data-action="ik-upload"]');

        const pwCard = page.locator('.pw-card');
        await expect(pwCard).toBeVisible({ timeout: 8000 });
        await expect(pwCard).toContainText('password_protected.pdf');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '03-password-card.png') });

        // 真按键(page.fill 假绿教训):先点击聚焦,断言 activeElement,再敲键盘。
        const pwInput = page.locator('#ikPwInput');
        await pwInput.click();
        const focusedId = await page.evaluate(
            () => document.activeElement && document.activeElement.id
        );
        expect(focusedId).toBe('ikPwInput');
        await page.keyboard.type('0000');
        await page.click('[data-action="ik-pw-submit"]');

        // 错密码:同一张卡换一句提示,isVisible + 真文本(不是原始 key)。
        await expect(page.locator('.pw-card .intake-err')).toBeVisible({ timeout: 8000 });
        const wrongText = await page.locator('.pw-card .intake-err').innerText();
        expect(wrongText).not.toContain('intake_pw_wrong');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '04-password-wrong.png') });

        await page.locator('#ikPwInput').click();
        await page.keyboard.type('1234');
        await page.click('[data-action="ik-pw-submit"]');

        await expect(page.locator('.pw-card')).toHaveCount(0, { timeout: 8000 });
        await expect(page.locator('.manifest-card .ci-counts')).toContainText('1');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '05-password-unlocked.png') });
    });

    test('密码 PDF → 跳过 → 该件转拒收,不阻塞流程', async ({ page }) => {
        await bootIntake(page, { materialsHandler: passwordRequiredRoute });
        await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'password_protected.pdf'));
        await page.click('[data-action="ik-upload"]');
        await expect(page.locator('.pw-card')).toBeVisible({ timeout: 8000 });
        await page.click('[data-action="ik-pw-skip"]');
        await expect(page.locator('.pw-card')).toHaveCount(0, { timeout: 8000 });
        const rows = await page.locator('.manifest-card .mx-table tr').allInnerTexts();
        expect(rows.some((r) => r.includes('password_protected.pdf'))).toBe(true);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '06-password-skipped.png') });
    });

    test('嵌套 zip 真文件 → 盘点条含 zip 解出计数', async ({ page }) => {
        await bootIntake(page, {
            materialsHandler: (route) =>
                route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({
                        registered: [{ item_id: 'z1' }, { item_id: 'z2' }, { item_id: 'z3' }],
                        count: 3,
                    }),
                }),
        });
        await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'nested_2level.zip'));
        await page.click('[data-action="ik-upload"]');
        const counts = page.locator('.manifest-card .ci-counts');
        await expect(counts).toBeVisible({ timeout: 8000 });
        const text = await counts.innerText();
        expect(text).toContain('3');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '07-zip-manifest.png') });
    });

    test('网络失败批 → 失败横幅 → 一键重试只重传失败件', async ({ page }) => {
        let call = 0;
        await bootIntake(page, {
            materialsHandler: async (route) => {
                call += 1;
                if (call === 1) return route.abort('failed');
                return route.fulfill({
                    contentType: 'application/json',
                    body: JSON.stringify({ registered: [{ item_id: 'r1' }], count: 1 }),
                });
            },
        });
        await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'normal_receipt.jpg'));
        await page.click('[data-action="ik-upload"]');
        await expect(page.locator('[data-action="ik-retry-failed"]')).toBeVisible({
            timeout: 8000,
        });
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '08-failed-batch.png') });

        await page.click('[data-action="ik-retry-failed"]');
        await expect(page.locator('[data-action="ik-retry-failed"]')).toHaveCount(0, {
            timeout: 8000,
        });
        await expect(page.locator('.manifest-card .ci-counts')).toContainText('1');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '09-failed-batch-retried.png') });
    });

    test('刷新后续传横幅:localStorage 残留队列 → 提示继续/忽略', async ({ page }) => {
        await bootIntake(page, {
            seedQueue: {
                orderId: 'wo-1',
                total: 5,
                doneNames: ['a.jpg'],
                pendingNames: ['b.jpg', 'c.jpg'],
                failedNames: ['d.jpg'],
                ts: Date.now(),
            },
        });

        const banner = page.locator('.resume-card');
        await expect(banner).toBeVisible({ timeout: 8000 });
        const st = await banner.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, visibility: s.visibility };
        });
        expect(st.display).not.toBe('none');
        expect(st.visibility).not.toBe('hidden');
        await expect(page.locator('[data-action="ik-resume-pick"]')).toBeVisible();
        await expect(page.locator('[data-action="ik-resume-dismiss"]')).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '10-resume-banner.png') });

        await page.click('[data-action="ik-resume-dismiss"]');
        await expect(page.locator('.resume-card')).toHaveCount(0);
        const left = await page.evaluate(() =>
            window.localStorage.getItem('pearnly_ai_intake_queue_wo-1')
        );
        expect(left).toBeNull();
    });

    for (const lang of ['th', 'zh', 'ja']) {
        test(`四语(${lang}):盘点条/密码卡文案非原始 key`, async ({ page }) => {
            await bootIntake(page, { lang, materialsHandler: passwordRequiredRoute });
            await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'password_protected.pdf'));
            await page.click('[data-action="ik-upload"]');
            await expect(page.locator('.pw-card')).toBeVisible({ timeout: 8000 });
            const title = await page.locator('.pw-card h3').innerText();
            expect(title).not.toContain('intake_pw_title');
            const hint = await page.locator('.pw-card .needs-sub').innerText();
            expect(hint).not.toContain('intake_pw_hint');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `11-lang-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:盘点条/密码卡可见 + IN-0b 新增件不新增横向溢出', async ({ page }) => {
        // 已核实(2026-07-16 排查):#/client/:id/intake 在空态(零 IN-0b 新组件)本身就有
        // 66px 横向溢出——真凶是既有 .ctabs 客户 tab 条(#clientTabs,ai-client.css)在
        // 390px 下不折行/不横滚,「画像」tab 顶出视口。这是 IN-0b 未触碰的既有文件/既有
        // 缺陷(整改前先量基线,不越权代修·只修本单报告范围内的问题)。这里断言 IN-0b
        // 新增的密码卡/盘点条渲染后不比这个基线多出溢出,而不是断言全局零溢出。
        await page.setViewportSize({ width: 390, height: 844 });
        await bootIntake(page, { materialsHandler: passwordRequiredRoute });
        const baseline = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);

        await page.setInputFiles('#ikFileInput', path.join(FIXTURES, 'password_protected.pdf'));
        await page.click('[data-action="ik-upload"]');
        await expect(page.locator('.pw-card')).toBeVisible({ timeout: 8000 });
        const withPwCard = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(withPwCard - baseline, '密码卡不该比空态多出横向溢出').toBeLessThanOrEqual(1);
        // 密码卡本身在视口内完整可见(isVisible + 未被裁到视口外)。
        const box = await page.locator('.pw-card').boundingBox();
        expect(box.x, '密码卡不该起点就在视口外').toBeGreaterThanOrEqual(0);
        expect(box.x + box.width, '密码卡右边不该出视口').toBeLessThanOrEqual(390 + 1);
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '12-mobile-390.png'),
            fullPage: true,
        });
    });
});
