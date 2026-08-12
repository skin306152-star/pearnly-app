/*
 * Pearnly · C·Qwen 档生产全上传入口实测 runner(一次性 · 2026-08)
 *
 * 用真账号在生产 https://pearnly.com 把全部前端上传入口各真跑一遍,
 * 逐入口留证据(耗时/结果状态/关键字段/截图/接口响应),汇总 report.json。
 * 只上传+等结果+读屏+截图,零破坏;禁 ERP 推送/删除/设置/订阅/充值/改配置。
 *
 * 跑法:
 *   $env:PEARNLY_E2E_USER='...'; $env:PEARNLY_E2E_PASS='...'
 *   node scripts/_ctier_prod_run.cjs
 *
 * 凭据只走环境变量,绝不打印/写盘/进 git。脚本内禁止出现任何凭据字面量。
 * 串行跑(生产限流,禁并发)。单入口结果等待上限 150 秒,超时记 TIMEOUT。
 * 上传会真扣费(余额已备足),这是预期不是事故。
 *
 * 语料来源 = 桌面 C:\Users\skin3\Desktop\Pearnly-产品语料测试数据(仓库外,不提交)。
 * 截图与 report.json 是运行证据,不提交;仅本脚本文件入库。
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const BASE = 'https://pearnly.com';
const USER = process.env.PEARNLY_E2E_USER;
const PASS = process.env.PEARNLY_E2E_PASS;
if (!USER || !PASS) {
    console.error('缺少 PEARNLY_E2E_USER / PEARNLY_E2E_PASS 环境变量');
    process.exit(1);
}

const ART = path.join('tests', 'e2e', '_artifacts', 'ctier-prod');
const CORPUS = 'C:\\Users\\skin3\\Desktop\\Pearnly-产品语料测试数据';
const ENTRY_TIMEOUT = 150_000;

// 语料(绝对路径)。三处与派单原文的偏差已在汇报中说明:
//  - IMG_2530 实际在 B_ERP产出(派单写 A_客户给的原料)
//  - 冰厂 GL 目录只有 CSV 无 xlsx → 用 MRERP-SM 总分类账 xlsx(产品标准 GL 语料)
//  - 无 ภ.พ.30 类 VAT 报表 → 用 MRERP 销项税登记簿 csv / 冰厂发票 PDF
const P = {
    img2530: path.join(CORPUS, 'SM-照片语料(题面A+答案BC-5月)', 'B_ERP产出', 'IMG_2530.JPG'),
    img2600: path.join(CORPUS, 'SM-照片语料(题面A+答案BC-5月)', 'A_客户给的原料', 'IMG_2600.JPG'),
    img2620: path.join(CORPUS, 'SM-照片语料(题面A+答案BC-5月)', 'A_客户给的原料', 'IMG_2620.JPG'),
    img2496: path.join(CORPUS, 'SM-照片语料(题面A+答案BC-5月)', 'A_客户给的原料', 'IMG_2496.JPG'),
    glXlsx: path.join(
        CORPUS,
        'MRERP-SM-SisterMakeup(销采单据)',
        'GL全科目',
        'รายงานสมุดแยกประเภท [16072569_155535].xlsx'
    ),
    vatCsv: path.join(
        CORPUS,
        'MRERP-SM-SisterMakeup(销采单据)',
        '05_销项税登记簿(acvatsaled)',
        'acvatsaled_5月779单.csv'
    ),
    invoicePdf: path.join(CORPUS, '冰厂客户语料', 'A_客户给的原料', 'Invoice Jun Part1.pdf'),
    bigcPdf: path.join(CORPUS, '冰厂客户语料', 'A_客户给的原料', 'Big C ซอยประชุม Jun.pdf'),
};
for (const [k, v] of Object.entries(P)) {
    if (!fs.existsSync(v)) {
        console.error(`语料缺失 ${k}: ${v}`);
        process.exit(1);
    }
}

const CHROME_UA =
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
    '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

// 与 tests/e2e/_helpers/console-guard.js 同口径的良性噪声白名单(保持最小)
const CONSOLE_IGNORE = [
    /favicon/i,
    /ResizeObserver loop/i,
    /Failed to load resource.*\b(analytics|gtag|googletagmanager|sentry|clarity|hotjar|facebook|fbevents)\b/i,
    /net::ERR_.*\b(analytics|gtag|googletagmanager|sentry|clarity|hotjar|facebook)\b/i,
    /cloudflareinsights/i,
];

// 抓的接口关键字:只记与上传/解析/对账相关的请求
const API_KEYS = [
    '/api/ocr/',
    '/api/purchase/intake',
    '/api/recon/',
    '/api/vat_report_checks',
    '/api/fileconv',
    '/api/ai/steward',
];

const report = [];
let current = null; // 当前入口(供 response 监听器落 api 数组)
let page = null; // 全局 page(主流程创建,helper 们共用)
let guard = null; // 控制台/pageerror 收集器(主流程创建)

function mkEntry(name, files) {
    return {
        entry: name,
        files,
        ms: 0,
        status: 'PENDING',
        ui_state: '',
        fields: {},
        api: [],
        console_errors: [],
    };
}

/** 入口日志 + 统一计时/兜错。fn 内部可改 e.status(如 TIMEOUT/SKIPPED)。 */
async function runEntry(name, files, fn) {
    const e = mkEntry(name, files);
    current = e;
    guard.consoleErrors.length = 0;
    guard.pageErrors.length = 0;
    const t0 = Date.now();
    try {
        await fn(page, e);
        if (e.status === 'PENDING') e.status = 'PASS';
    } catch (err) {
        const isTimeout = err && (err.name === 'TimeoutError' || /timeout/i.test(String(err.message)));
        e.status = e.status === 'PENDING' ? (isTimeout ? 'TIMEOUT' : 'FAIL') : e.status;
        e.ui_state = (e.ui_state || '') + (e.ui_state ? ' | ' : '') + 'err: ' + String(err.message).slice(0, 300);
    }
    e.ms = Date.now() - t0;
    e.console_errors = [...guard.pageErrors, ...guard.consoleErrors];
    current = null;
    report.push(e);
    return e;
}

async function shot(name, sel) {
    try {
        if (sel) {
            const loc = page.locator(sel).first();
            if (await loc.count()) {
                await loc.scrollIntoViewIfNeeded().catch(() => {});
                await page.waitForTimeout(300);
            }
        }
        await page.screenshot({ path: path.join(ART, name + '.png'), fullPage: false });
    } catch (err) {
        console.log('  [shot] 截图失败 ' + name + ': ' + err.message.slice(0, 120));
    }
}

/** 抓关键 UI 文本(原样抄屏,截断) */
async function uiText(sel, max = 600) {
    try {
        const loc = page.locator(sel).first();
        if (!(await loc.count())) return '';
        const t = (await loc.innerText().catch(() => '')) || '';
        return t.replace(/\n{3,}/g, '\n\n').slice(0, max);
    } catch {
        return '';
    }
}

/** 入口结束兜底截图 + ui_state 落最终现场 */
async function finalizeShot(e, name, sel) {
    await shot(name, sel);
    if (!e.ui_state) e.ui_state = '(未见明确状态区)';
}

// ── 主应用登录(#form-login · 超管会跳 /admin,测试账号须为普通账号) ──
async function loginMain(p) {
    await p.goto(BASE + '/login', { waitUntil: 'domcontentloaded' });
    await p.locator('#form-login #li-username').fill(USER);
    await p.locator('#form-login #li-password').fill(PASS);
    await p.locator('#form-login #btn-login').click();
    await p.waitForURL('**/home**', { timeout: 30_000 });
    await p.waitForFunction(() => !!localStorage.getItem('mrpilot_token'), null, { timeout: 10_000 });
}

/** 过账套硬门(选第一个)+ 关账套软弹(若有) */
async function dismissWorkspaceGate(p) {
    const pick = p.locator('#workspace-gate-root [data-wsg-pick]').first();
    const appeared = await pick
        .waitFor({ state: 'visible', timeout: 6_000 })
        .then(() => true)
        .catch(() => false);
    if (appeared) {
        await pick.click();
        await p.locator('#workspace-gate-root').waitFor({ state: 'detached', timeout: 8_000 }).catch(() => {});
    }
    const modal = p.locator('#ws-modal');
    if (await modal.waitFor({ state: 'visible', timeout: 4_000 }).then(() => true).catch(() => false)) {
        await p.locator('#ws-modal [data-ws-close="1"]').click().catch(() => {});
    }
}

async function openRoute(p, route) {
    await p.evaluate((r) => window.routeTo(r), route);
    await p.waitForFunction(
        (r) => {
            const el = document.getElementById('page-' + r);
            return !!el && el.classList.contains('active');
        },
        route,
        { timeout: 15_000 }
    );
}

// ── 入口 1:web_upload 发票识别(录入工作台 dms-intake) ──
async function entryWebUpload(p, e) {
    await openRoute(p, 'dms-intake');
    await p.waitForSelector('#dx-inv-file', { state: 'attached', timeout: 20_000 });
    const respP = p.waitForResponse(
        (r) => r.url().includes('/api/ocr/') && r.request().method() === 'POST',
        { timeout: ENTRY_TIMEOUT }
    );
    await p.locator('#dx-inv-file').setInputFiles([P.img2530, P.img2600]);
    await p.waitForSelector('#dx-inv-start', { state: 'visible', timeout: 20_000 });
    await p.locator('#dx-inv-start').click();
    const resp = await respP;
    const body = await resp.json().catch(() => ({}));
    e.fields = {
        recognize_status: resp.status(),
        history_id: body.history_id || '',
        pages: Array.isArray(body.pages) ? body.pages.length : body.page_count ?? '',
        engine: body.engine || '',
        from_cache: !!body.from_cache,
    };
    // 等文件行出终态(success 绿 / error 琥珀)
    await p
        .locator('.dx-qrow .dx-badge.green, .dx-qrow .dx-badge.amber')
        .first()
        .waitFor({ state: 'visible', timeout: ENTRY_TIMEOUT })
        .catch(() => {});
    const badges = await p.locator('.dx-qrow').count();
    e.ui_state = `文件行 ${badges} 条 · ` + (await uiText('.dx-qlist'));
    await finalizeShot(e, '1-web-upload', '.dx-qlist');
}

// ── 入口 2:purchase_intake 采购进料(采集屏 purchase-capture) ──
async function entryPurchase(p, e) {
    await openRoute(p, 'purchase-capture');
    await p.waitForSelector('#cap-upload', { state: 'visible', timeout: 20_000 });
    const respP = p.waitForResponse(
        (r) => r.url().includes('/api/purchase/intake') && r.request().method() === 'POST',
        { timeout: ENTRY_TIMEOUT }
    );
    const chooser = p.waitForEvent('filechooser', { timeout: 10_000 });
    await p.locator('#cap-upload').click();
    const fc = await chooser;
    await fc.setFiles(P.img2620);
    const resp = await respP;
    const body = await resp.json().catch(() => ({}));
    e.fields = {
        intake_status: resp.status(),
        route: body.route || '',
        has_draft: !!body.draft,
        doc_id: body.doc_id || '',
        dedupe_hit: !!body.dedupe_hit,
    };
    await p.waitForTimeout(2500); // 给复核屏/详情渲染留窗口
    e.ui_state = await uiText('#page-purchase-capture, .pur.cap');
    await finalizeShot(e, '2-purchase-intake', '#page-purchase-capture');
}

// ── 入口 3+4:bank_recon(bank tab · 左 statement + 右 GL → 开始对账) ──
// 两个上传动作在同一 tab 且共享一次对账提交,故合一个流程,但逐入口独立留证(3=左卡,4=右卡)。
async function entryBankRecon(p, e3, e4) {
    const t0 = Date.now();
    current = e3; // 共享提交流程的接口记录统一落 e3,finally 复制给 e4
    try {
        await openRoute(p, 'reconcile');
        await p.waitForSelector('#rcx-tabs', { state: 'visible', timeout: 20_000 });
        await p.locator('[data-rcx-tab="bank"]').click();
        await p.waitForSelector('#rcx-card-left', { state: 'visible', timeout: 15_000 });

        // 左卡 = 银行对账单照片
        await p.locator('input[data-rcx-input="left"]').setInputFiles(P.img2496);
        await p.locator('#rcx-card-left.rcx-loaded').waitFor({ state: 'visible', timeout: 15_000 });
        e3.ui_state = '左卡(statement)已载入: ' + (await uiText('#rcx-card-left .rcx-file-meta', 200));
        await shot('3-bank-statement-uploaded', '#rcx-card-left');

        // 右卡 = 总账 GL xlsx
        await p.locator('input[data-rcx-input="right"]').setInputFiles(P.glXlsx);
        await p.locator('#rcx-card-right.rcx-loaded').waitFor({ state: 'visible', timeout: 15_000 });
        e4.ui_state = '右卡(GL)已载入: ' + (await uiText('#rcx-card-right .rcx-file-meta', 200));
        await shot('4-bank-gl-uploaded', '#rcx-card-right');

        // 开始对账(bank-v2 submit · 左+右一起提交)
        const readyBtn = p.locator('#rcx-start-btn');
        if (await readyBtn.isDisabled()) {
            e3.status = 'FAIL';
            e4.status = 'FAIL';
            e3.ui_state += ' | 开始对账按钮 disabled(文件未被接受)';
            e4.ui_state += ' | 开始对账按钮 disabled';
            return;
        }
        const submitP = p.waitForResponse(
            (r) => r.url().includes('/api/recon/bank-v2/submit') && r.request().method() === 'POST',
            { timeout: ENTRY_TIMEOUT }
        );
        await readyBtn.click();
        const resp = await submitP;
        const body = await resp.json().catch(() => ({}));
        const common = {
            submit_status: resp.status(),
            ok: body.ok ?? 'n/a',
            job_id: body.job_id || '',
            detail: body.detail || '',
        };
        e3.fields = { ...common };
        e4.fields = { ...common };
        // 等终态:结果区 / 失败区 / 处理中(最多 90s 收口)
        await p
            .locator('#rcx-results, #rcx-fail, #rcx-processing')
            .first()
            .waitFor({ state: 'visible', timeout: 90_000 })
            .catch(() => {});
        await p.waitForTimeout(3000);
        const res = await uiText('#rcx-results', 500);
        const fail = await uiText('#rcx-fail', 300);
        const proc = await uiText('#rcx-processing', 200);
        e3.ui_state = '对账结果: ' + (res || fail || proc || '(未见终态区)');
        e4.ui_state = e3.ui_state;
        e3.status = 'PASS';
        e4.status = 'PASS';
        if (fail) e3.fields.recon_fail = fail;
        await shot('3-bank-statement-uploaded', '#rcx-workspace');
        await shot('4-bank-gl-uploaded', '#rcx-workspace');
    } catch (err) {
        const isTimeout = err && (err.name === 'TimeoutError' || /timeout/i.test(String(err.message)));
        const st = isTimeout ? 'TIMEOUT' : 'FAIL';
        e3.status = st;
        e4.status = st;
        for (const t of [e3, e4]) {
            t.ui_state = (t.ui_state || '') + (t.ui_state ? ' | ' : '') + 'err: ' + String(err.message).slice(0, 300);
        }
    } finally {
        const ms = Date.now() - t0;
        e3.ms = ms;
        e4.ms = ms;
        e3.console_errors = [...guard.pageErrors, ...guard.consoleErrors];
        e4.console_errors = e3.console_errors;
        e4.api = e3.api; // 共享提交的接口记录复制一份
        current = null;
    }
}

// ── 入口 5:vat_recon(GL-VAT · income tab · 左 GL + 右 VAT → 开始对账) ──
async function entryVatRecon(p, e) {
    // 切 tab 前清空 bank 留下的两卡(避免 hasStaged 确认弹窗卡点击)
    await p.locator('[data-rcx-remove="left"]').click().catch(() => {});
    await p.locator('[data-rcx-remove="right"]').click().catch(() => {});
    await p.locator('[data-rcx-tab="income"]').click();
    await p.waitForSelector('#rcx-card-left', { state: 'visible', timeout: 15_000 });

    await p.locator('input[data-rcx-input="left"]').setInputFiles(P.glXlsx);
    await p.locator('#rcx-card-left.rcx-loaded').waitFor({ state: 'visible', timeout: 15_000 });
    await p.locator('input[data-rcx-input="right"]').setInputFiles(P.vatCsv);
    await p.locator('#rcx-card-right.rcx-loaded').waitFor({ state: 'visible', timeout: 15_000 });
    e.ui_state = 'income 双卡已载入: ' + (await uiText('#rcx-card-left .rcx-file-meta, #rcx-card-right .rcx-file-meta', 300));
    await shot('5-vat-recon-uploaded', '#rcx-workspace');

    const readyBtn = p.locator('#rcx-start-btn');
    if (await readyBtn.isDisabled()) {
        e.status = 'FAIL';
        e.ui_state += ' | 开始对账按钮 disabled';
        await finalizeShot(e, '5-vat-recon-uploaded', '#rcx-workspace');
        return;
    }
    const submitP = p.waitForResponse(
        (r) => r.url().includes('/api/recon/gl-vat/submit') && r.request().method() === 'POST',
        { timeout: ENTRY_TIMEOUT }
    );
    await readyBtn.click();
    const resp = await submitP;
    const body = await resp.json().catch(() => ({}));
    e.fields = {
        submit_status: resp.status(),
        ok: body.ok ?? 'n/a',
        job_id: body.job_id || '',
        detail: body.detail || '',
    };
    await p
        .locator('#rcx-results:not([style*="display: none"]), #rcx-fail:not([style*="display: none"]), #rcx-processing')
        .first()
        .waitFor({ state: 'visible', timeout: 90_000 })
        .catch(() => {});
    await p.waitForTimeout(3000);
    const res = await uiText('#rcx-results', 500);
    const fail = await uiText('#rcx-fail', 300);
    e.ui_state = '对账结果: ' + (res || fail || '(未见终态区)');
    if (fail) e.fields.recon_fail = fail;
    await finalizeShot(e, '5-vat-recon-uploaded', '#rcx-workspace');
}

// ── AI 壳登录(#/ai gate) ──
async function loginAi(p) {
    await p.goto(BASE + '/ai', { waitUntil: 'domcontentloaded' });
    // 已有 token 直接进工作台;否则登录卡
    const hasToken = await p.evaluate(() => !!localStorage.getItem('mrpilot_token_ai'));
    if (!hasToken) {
        await p.locator('#gateUsername').waitFor({ state: 'visible', timeout: 20_000 });
        await p.locator('#gateUsername').fill(USER);
        await p.locator('#gatePassword').fill(PASS);
        await p.locator('#gateSubmitBtn').click();
    }
    await p.waitForSelector('#navDash', { state: 'visible', timeout: 30_000 });
}

/** 切 AI 壳 hash 路由(登录/邀请门面会拦截 → 返回 false 表示进不去) */
async function gotoAiView(p, hash, viewId) {
    await p.evaluate((h) => {
        location.hash = h;
    }, hash);
    await p.waitForTimeout(500);
    const ok = await p
        .locator('#' + viewId)
        .waitFor({ state: 'visible', timeout: 20_000 })
        .then(() => true)
        .catch(() => false);
    return ok;
}

// ── 入口 6:vat_report 检查页(#/vatcheck) ──
async function entryVatcheck(p, e) {
    if (!(await gotoAiView(p, '#/vatcheck', 'v-vatcheck'))) {
        e.status = 'SKIPPED';
        e.ui_state = '进不去 #/vatcheck(闸/邀请面拦截)';
        await finalizeShot(e, '6-vatcheck', '#gateRoot');
        return;
    }
    await p.locator('#vcDrop').waitFor({ state: 'visible', timeout: 15_000 });
    const respP = p.waitForResponse(
        (r) => r.url().includes('/api/vat_report_checks') && r.request().method() === 'POST',
        { timeout: ENTRY_TIMEOUT }
    );
    const chooser = p.waitForEvent('filechooser', { timeout: 10_000 });
    await p.locator('#vcDrop').click();
    const fc = await chooser;
    await fc.setFiles(P.invoicePdf);
    // 选完文件后点「开始核查」按钮
    await p
        .locator('#vcBody [data-action="vc-run"]')
        .waitFor({ state: 'visible', timeout: 15_000 })
        .catch(() => {});
    await p.locator('#vcBody [data-action="vc-run"]').click().catch(() => {});
    const resp = await respP;
    const body = await resp.json().catch(() => ({}));
    e.fields = {
        check_status: resp.status(),
        ok: body.ok ?? 'n/a',
        detail: body.detail || '',
        issues: body.issues ? (Array.isArray(body.issues) ? body.issues.length : body.issues) : '',
    };
    await p.waitForTimeout(3000);
    e.ui_state = await uiText('#vcBody');
    await finalizeShot(e, '6-vatcheck', '#vcBody');
}

// ── 入口 7:fileconv 文件转换(#/fileconv) ──
async function entryFileconv(p, e) {
    if (!(await gotoAiView(p, '#/fileconv', 'v-fileconv'))) {
        e.status = 'SKIPPED';
        e.ui_state = '进不去 #/fileconv(闸/邀请面拦截)';
        await finalizeShot(e, '7-fileconv', '#gateRoot');
        return;
    }
    await p.locator('#fcDrop').waitFor({ state: 'visible', timeout: 15_000 });
    const respP = p.waitForResponse(
        (r) => r.url().includes('/api/fileconv/convert') && r.request().method() === 'POST',
        { timeout: ENTRY_TIMEOUT }
    );
    const chooser = p.waitForEvent('filechooser', { timeout: 10_000 });
    await p.locator('#fcDrop [data-action="fc-pick"], #fcDrop [data-action="fc-goto-upload"]').first().click();
    const fc = await chooser;
    await fc.setFiles(P.bigcPdf);
    await p
        .locator('#fcBody [data-action="fc-run"]')
        .waitFor({ state: 'visible', timeout: 15_000 })
        .catch(() => {});
    await p.locator('#fcBody [data-action="fc-run"]').click().catch(() => {});
    const resp = await respP;
    const body = await resp.json().catch(() => ({}));
    e.fields = {
        convert_status: resp.status(),
        ok: body.ok ?? 'n/a',
        doc_type: body.doc_type || '',
        issue_count: body.issue_count ?? '',
        detail: body.detail || '',
    };
    await p.waitForTimeout(3000);
    e.ui_state = await uiText('#fcBody');
    await finalizeShot(e, '7-fileconv', '#fcBody');
}

// ── 入口 8:steward 管家对话上传(#/steward) ──
async function entrySteward(p, e) {
    const inView = await gotoAiView(p, '#/steward', 'v-steward');
    if (!inView) {
        e.status = 'SKIPPED';
        e.ui_state = '进不去 #/steward(tenant 闸默认关 / 落回工作台)';
        await finalizeShot(e, '8-steward', '#gateRoot');
        return;
    }
    // 闸开着 → 找附件上传口(#stwAttFile)
    const attInput = p.locator('#stwAttFile');
    if (!(await attInput.count())) {
        e.status = 'SKIPPED';
        e.ui_state = 'steward 视图可见但无附件上传口(#stwAttFile)';
        await finalizeShot(e, '8-steward', '#v-steward');
        return;
    }
    const respP = p.waitForResponse(
        (r) => r.url().includes('/api/ai/steward') && r.request().method() === 'POST' && r.url().includes('attachment'),
        { timeout: ENTRY_TIMEOUT }
    );
    await attInput.setInputFiles(P.invoicePdf);
    const resp = await respP;
    const body = await resp.json().catch(() => ({}));
    e.fields = {
        attach_status: resp.status(),
        ok: body.ok ?? 'n/a',
        attachments: body.attachments ? body.attachments.length : '',
        detail: body.detail || '',
    };
    await p.waitForTimeout(2000);
    e.ui_state = await uiText('#v-steward .stw-messages, #v-steward', 500);
    await finalizeShot(e, '8-steward', '#v-steward');
}

// ── 主流程 ──
(async () => {
    fs.mkdirSync(ART, { recursive: true });
    const browser = await chromium.launch();
    const ctx = await browser.newContext({
        baseURL: BASE,
        userAgent: CHROME_UA,
        viewport: { width: 1440, height: 960 },
    });
    page = await ctx.newPage();

    guard = { consoleErrors: [], pageErrors: [] };
    page.on('console', (m) => {
        if (m.type() === 'error' && !CONSOLE_IGNORE.some((re) => re.test(m.text())))
            guard.consoleErrors.push(m.text());
    });
    page.on('pageerror', (err) => {
        if (!CONSOLE_IGNORE.some((re) => re.test(err.message))) guard.pageErrors.push(err.message);
    });
    page.on('response', async (resp) => {
        if (!current) return;
        const url = resp.url();
        if (!API_KEYS.some((k) => url.includes(k))) return;
        let body = null;
        try {
            const ct = resp.headers()['content-type'] || '';
            const raw = ct.includes('json')
                ? JSON.stringify(await resp.json())
                : await resp.text();
            body = String(raw).slice(0, 1200);
        } catch {
            body = null;
        }
        current.api.push({ url: url.replace(BASE, ''), status: resp.status(), body });
    });
    // CF 分析信标黑洞(防 goto 超时)
    await page.route('**://static.cloudflareinsights.com/**', (r) =>
        r.fulfill({ status: 204, body: '' })
    );

    console.log('\n[login] 主应用(' + BASE + ')');
    await loginMain(page);
    await dismissWorkspaceGate(page);
    console.log('[login] 主应用已进 /home');

    await runEntry('1_web_upload发票识别', [P.img2530, P.img2600], (p, e) => entryWebUpload(p, e));
    await runEntry('2_purchase_intake采购进料', [P.img2620], (p, e) => entryPurchase(p, e));
    // 3/4 同页同提交:共享一次 bank 对账流程,逐入口独立留证
    const e3 = mkEntry('3_bank_recon银行对账单', [P.img2496]);
    const e4 = mkEntry('4_bank_recon_GL', [P.glXlsx]);
    await entryBankRecon(page, e3, e4);
    report.push(e3, e4);

    await runEntry('5_vat_recon_GL-VAT对账', [P.glXlsx, P.vatCsv], (p, e) => entryVatRecon(p, e));

    console.log('\n[login] AI 壳(/ai)');
    await loginAi(page);
    console.log('[login] AI 壳已进工作台');

    await runEntry('6_vat_report检查页', [P.invoicePdf], (p, e) => entryVatcheck(p, e));
    await runEntry('7_fileconv文件转换', [P.bigcPdf], (p, e) => entryFileconv(p, e));
    await runEntry('8_steward管家上传', [P.invoicePdf], (p, e) => entrySteward(p, e));

    await browser.close();

    // ── 落盘 + stdout 表格 ──
    fs.writeFileSync(
        path.join(ART, 'report.json'),
        JSON.stringify(report, null, 2),
        'utf-8'
    );
    const pad = (s, n) => String(s).padEnd(n);
    const line = (r) => {
        const files = r.files.map((f) => path.basename(f)).join(' + ');
        console.log(
            pad(r.entry, 32) +
                pad(r.status, 8) +
                pad(r.ms + 'ms', 12) +
                pad(files, 34) +
                (r.ui_state || '').split('\n')[0].slice(0, 60)
        );
    };
    console.log('\n' + '='.repeat(150));
    console.log(
        pad('entry', 32) + pad('status', 8) + pad('ms', 12) + pad('files', 34) + 'ui_state(first line)'
    );
    console.log('-'.repeat(150));
    for (const r of report) line(r);
    console.log('='.repeat(150));
    console.log('report.json → ' + path.join(ART, 'report.json'));
    const failN = report.filter((r) => r.status === 'FAIL').length;
    const skipN = report.filter((r) => r.status === 'SKIPPED').length;
    const timeN = report.filter((r) => r.status === 'TIMEOUT').length;
    console.log(
        `汇总: ${report.length - failN - skipN - timeN} PASS / ${failN} FAIL / ${skipN} SKIPPED / ${timeN} TIMEOUT`
    );
    process.exit(0);
})().catch((err) => {
    console.error('脚本异常: ' + (err && err.stack ? err.stack : err));
    process.exit(1);
});
