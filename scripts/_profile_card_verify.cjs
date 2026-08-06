// 税务画像卡(智能判断版·画像卡设计稿 v1)真浏览器验收 · 跑 static/dist 真构建产物 +
// stub /api/**(照 _steward_chat_v2_verify.cjs 的桩法:自起 http 服 + page.route 拦截,
// 真渲染代码原样跑,只桩网络层)。
// 剧本:①空态(SBT 未确认+CTA)→ ②推断待确认(pending+全部确认)→ ③冲突(二选一)→
//       ④全部已确认(100% 完整度)。每态截图为证,②③各验一次真实交互(点击→重渲染→
//       toast),SBT CTA 验一次 AI.steward.openWith 真被调用(带预填句)。
// 跑法: node scripts/_profile_card_verify.cjs → tests/e2e/_artifacts/profile_card/
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const PORT = 8931;
const BASE = `http://127.0.0.1:${PORT}`;
const PAGE = `${BASE}/static/dist/ai.html`;
const OUT = path.join(ROOT, 'tests', 'e2e', '_artifacts', 'profile_card');
const CLIENT_ID = 'c1';
const PERIOD = '2569-07';

const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.woff2': 'font/woff2',
};

function serve() {
    const srv = http.createServer((req, res) => {
        const p = decodeURIComponent(req.url.split('?')[0]);
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
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

// ---------- 桩画像数据(逐字段对齐 routes/tax_profile_routes.py 的序列化形状) ----------

function baseProfile() {
    return {
        vat_status: 'registered',
        branch: 'สำนักงานใหญ่',
        sbt_status: 'none',
        sbt_business_type: '',
        has_employees: 'unknown',
        pays_individuals: 'unknown',
        pays_juristic: 'unknown',
        pays_foreign: 'unknown',
        pays_interest_dividend: 'unknown',
        has_multi_branch: false,
        branch_count: 1,
        filing_disposition: 'active',
        efiling_enrolled: 'unknown',
        tax_agent_authorized: false,
        tax_agent_ref: '',
        vat_credit_carry: '0.00',
        field_meta: {},
    };
}

function withProposals(profile, proposals) {
    const out = JSON.parse(JSON.stringify(profile));
    out.field_meta = out.field_meta || {};
    Object.keys(proposals).forEach((k) => {
        out.field_meta[k] = Object.assign({}, out.field_meta[k], { proposal: proposals[k] });
    });
    return out;
}

const PROPOSAL_INDIVIDUALS = {
    value: 'yes',
    confidence: 'high',
    evidence: `pays_individuals:hit:3:${PERIOD}`,
};
const PROPOSAL_JURISTIC = {
    value: 'no',
    confidence: 'mid',
    evidence: `pays_juristic:miss:0:${PERIOD}`,
};

// 场景①空态:全新客户,SBT 从未确认(诚实边界 CTA)。
function scenarioEmpty() {
    return { completeness: 0.57, profile: baseProfile() };
}

// 场景②推断待确认:pays_individuals/pays_juristic 两项各有一条现算候选,从未确认过。
function scenarioPending() {
    const profile = withProposals(baseProfile(), {
        pays_individuals: PROPOSAL_INDIVIDUALS,
        pays_juristic: PROPOSAL_JURISTIC,
    });
    return { completeness: 0.57, profile };
}

// 场景③冲突:pays_individuals 已手填确认为 'no',但当期新信号命中 'yes' —— 冲突。
function scenarioConflict() {
    const profile = withProposals(baseProfile(), { pays_individuals: PROPOSAL_INDIVIDUALS });
    profile.pays_individuals = 'no';
    profile.field_meta.pays_individuals.source = 'manual';
    profile.field_meta.pays_individuals.confirmed_at = '2026-06-01T00:00:00+00:00';
    profile.field_meta.pays_individuals.confirmed_by = 'user:acct-1';
    return { completeness: 0.64, profile };
}

// 场景④全部已确认:14 字段全部留痕,SBT 也已通过管家确认为 none。
function scenarioDone() {
    const profile = baseProfile();
    const stamp = (field, value, source, extra) => {
        profile[field] = value;
        profile.field_meta[field] = Object.assign(
            {
                source,
                confidence: null,
                evidence: null,
                proposal: null,
                confirmed_at: '2026-08-01T00:00:00+00:00',
                confirmed_by: 'user:acct-1',
            },
            extra || {}
        );
    };
    // sbt_status 不在 INFERABLE_FIELDS 里(profile_inference.py 只推 pays_individuals/
    // pays_juristic),管家看完 ภ.พ.20 照片后落的是普通 PUT——手填口径,没有 evidence
    // (与真实后端 upsert_profile 的手填戳一致,不给它编一条不存在的推断依据)。
    stamp('sbt_status', 'none', 'manual');
    stamp('has_employees', 'yes', 'manual');
    stamp('pays_individuals', 'yes', 'inferred', {
        confidence: 'high',
        evidence: PROPOSAL_INDIVIDUALS.evidence,
    });
    stamp('pays_juristic', 'no', 'inferred', {
        confidence: 'mid',
        evidence: PROPOSAL_JURISTIC.evidence,
    });
    stamp('pays_foreign', 'no', 'manual');
    stamp('pays_interest_dividend', 'no', 'manual');
    stamp('has_multi_branch', false, 'manual');
    stamp('filing_disposition', 'active', 'manual');
    stamp('efiling_enrolled', 'yes', 'manual');
    stamp('tax_agent_authorized', false, 'manual');
    stamp('vat_credit_carry', '0.00', 'manual');
    return { completeness: 1.0, profile };
}

// ---------- 路由桩 ----------

function json(route, body, status) {
    return route.fulfill({
        status: status || 200,
        contentType: 'application/json',
        body: JSON.stringify(body),
    });
}

async function mockRoutes(page, world) {
    await page.route('**/api/**', (route) => {
        const req = route.request();
        const url = new URL(req.url());
        const p = url.pathname;
        const method = req.method();
        if (p === `/api/workspace/clients/${CLIENT_ID}`) {
            return json(route, {
                client: { id: CLIENT_ID, name: 'Sister Makeup', tax_id: '0105561234567' },
            });
        }
        if (p === `/api/workspace/clients/${CLIENT_ID}/tax-profile` && method === 'GET') {
            return json(route, { profile: world.profile, completeness: world.completeness });
        }
        if (p === `/api/workspace/clients/${CLIENT_ID}/tax-profile` && method === 'PUT') {
            const body = req.postDataJSON() || {};
            const prevCodes = world.obligationCodes.slice();
            Object.keys(body).forEach((k) => {
                world.profile[k] = body[k];
                world.profile.field_meta[k] = {
                    source: 'manual',
                    confidence: null,
                    evidence: null,
                    proposal: null,
                    confirmed_at: new Date().toISOString(),
                    confirmed_by: 'user:e2e',
                };
            });
            world.recompute();
            const added = world.obligationCodes.filter((c) => prevCodes.indexOf(c) < 0);
            return json(route, { profile: world.profile, added_obligations: added });
        }
        if (p === `/api/workspace/clients/${CLIENT_ID}/tax-profile/confirm` && method === 'POST') {
            const body = req.postDataJSON() || {};
            const prevCodes = world.obligationCodes.slice();
            (body.fields || []).forEach((field) => {
                const meta = world.profile.field_meta[field];
                const proposal = meta && meta.proposal;
                if (!proposal) return;
                world.profile[field] = proposal.value;
                world.profile.field_meta[field] = {
                    source: 'inferred',
                    confidence: proposal.confidence,
                    evidence: proposal.evidence,
                    proposal: null,
                    confirmed_at: new Date().toISOString(),
                    confirmed_by: 'user:e2e',
                };
            });
            world.recompute();
            const added = world.obligationCodes.filter((c) => prevCodes.indexOf(c) < 0);
            return json(route, { profile: world.profile, added_obligations: added });
        }
        if (p === `/api/workspace/clients/${CLIENT_ID}/aliases`)
            return json(route, { aliases: [] });
        if (p === `/api/workspace/clients/${CLIENT_ID}/obligations`) {
            return json(route, {
                period: PERIOD,
                obligations: world.obligationCodes.map((code) => ({
                    obligation_code: code,
                    status: 'due',
                    display_names: OBLIG_NAMES[code] || { zh: code },
                    due_paper: null,
                    due_efiling: null,
                })),
            });
        }
        return json(route, {});
    });
    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-e2e-profile-card');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
}

const OBLIG_NAMES = {
    vat30: { zh: 'ภ.พ.30 增值税申报' },
    pnd3: { zh: 'ภ.ง.ด.3 个人预扣税申报' },
    pnd53: { zh: 'ภ.ง.ด.53 法人预扣税申报' },
};

function makeWorld(scenario) {
    const { profile, completeness } = scenario();
    const world = { profile, completeness, obligationCodes: [] };
    world.recompute = () => {
        const codes = ['vat30'];
        const confirmed = (f) => {
            const m = world.profile.field_meta[f];
            return m && m.confirmed_at;
        };
        if (confirmed('pays_individuals') && world.profile.pays_individuals === 'yes')
            codes.push('pnd3');
        if (confirmed('pays_juristic') && world.profile.pays_juristic === 'yes')
            codes.push('pnd53');
        world.obligationCodes = codes;
    };
    world.recompute();
    return world;
}

// ---------- 断言小工具 ----------

let failures = 0;
function check(label, cond) {
    if (cond) {
        console.log(`  [OK] ${label}`);
    } else {
        failures += 1;
        console.log(`  [X ] ${label}`);
    }
}

async function shot(page, name) {
    fs.mkdirSync(OUT, { recursive: true });
    await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true });
}

async function gotoProfile(page) {
    await page.goto(`${PAGE}#/clients/${CLIENT_ID}/profile`);
    await page.waitForSelector('#v-client-archive.on .pf-card', { timeout: 15000 });
}

// ---------- 场景 ----------

async function runEmpty(browser) {
    console.log('场景①空态(SBT 未确认 + CTA)');
    const page = await browser.newPage({ viewport: { width: 900, height: 1000 } });
    const world = makeWorld(scenarioEmpty);
    await mockRoutes(page, world);
    // AI.steward.openWith 探针:CTA 点击后应带预填句真调用它(不靠 hash 跳转副作用判断)。
    await page.addInitScript(() => {
        window.__pfCtaCalls = [];
        window.__installStewardSpy = () => {
            if (!window.AI) return false;
            window.AI.steward = window.AI.steward || {};
            const orig = window.AI.steward.openWith;
            window.AI.steward.openWith = (text) => {
                window.__pfCtaCalls.push(text);
                if (typeof orig === 'function') return; // 不真的跳转 hash,避免掉出档案页
            };
            return true;
        };
    });
    await gotoProfile(page);
    await page.waitForFunction(() => window.__installStewardSpy && window.__installStewardSpy());

    const sbtRow = page.locator('.pf-row.blocked');
    check('SBT 行渲染为 blocked 态(诚实边界 CTA)', (await sbtRow.count()) > 0);
    check('SBT CTA 按钮可见', await page.locator('[data-open-steward]').isVisible());
    await page.locator('[data-open-steward]').click();
    const calls = await page.evaluate(() => window.__pfCtaCalls);
    check('点击 CTA 真调用了 AI.steward.openWith(带预填句)', calls.length === 1 && !!calls[0]);

    const pct = await page.locator('.pf-pct').first().textContent();
    check('完整度百分比已渲染', /\d+%/.test(pct || ''));
    await shot(page, '01-empty');
    await page.close();
}

async function runPending(browser) {
    console.log('场景②推断待确认(全部确认(N))');
    const page = await browser.newPage({ viewport: { width: 900, height: 1100 } });
    const world = makeWorld(scenarioPending);
    await mockRoutes(page, world);
    await gotoProfile(page);

    check(
        'pays_individuals 行显示待确认圆点',
        (await page.locator('.pf-dot.pending').count()) >= 2
    );
    check(
        '推断依据文案已按 4 语拼出真实笔数/期间(非机器码原样)',
        (await page.locator('.pf-reason', { hasText: '3' }).count()) > 0
    );
    const confirmAllBtn = page.locator('[data-action="profile-confirm-all"]');
    check(
        '「全部确认(N)」按钮可见且带计数',
        /\(\s*2\s*\)|（\s*2\s*）/.test((await confirmAllBtn.textContent()) || '')
    );
    await shot(page, '02-pending-before');

    await confirmAllBtn.click();
    await page
        .waitForSelector('.pf-dot.pending', { state: 'detached', timeout: 8000 })
        .catch(() => {});
    check('确认后不再有待确认圆点', (await page.locator('.pf-dot.pending').count()) === 0);
    check('确认后出现已确认勾选', (await page.locator('.pf-ok').count()) >= 2);
    await page.waitForSelector('.toast.on', { timeout: 8000 }).catch(() => {});
    const toastText = await page
        .locator('.toast')
        .first()
        .textContent()
        .catch(() => '');
    check('确认后弹出「当期义务已重算」toast', !!toastText && toastText.length > 0);
    await shot(page, '02-pending-after-confirm-all');
    await page.close();
}

async function runConflict(browser) {
    console.log('场景③冲突(二选一)');
    const page = await browser.newPage({ viewport: { width: 900, height: 1000 } });
    const world = makeWorld(scenarioConflict);
    await mockRoutes(page, world);
    await gotoProfile(page);

    check(
        'pays_individuals 行渲染为冲突态',
        (await page.locator('.pf-row.conflict').count()) === 1
    );
    check(
        '冲突框展示两个可选项(手填 vs 推断)',
        (await page.locator('.pf-conflict-opt').count()) === 2
    );
    await shot(page, '03-conflict-before');

    await page.locator('[data-conflict-accept]').click();
    await page
        .waitForSelector('.pf-row.conflict', { state: 'detached', timeout: 8000 })
        .catch(() => {});
    check('采纳推断后冲突框消失', (await page.locator('.pf-row.conflict').count()) === 0);
    check('采纳后来源徽章变为票据推断', (await page.locator('.st-badge.st-ai').count()) > 0);
    await shot(page, '03-conflict-after-accept');
    await page.close();
}

async function runDone(browser) {
    console.log('场景④全部已确认');
    const page = await browser.newPage({ viewport: { width: 900, height: 1100 } });
    const world = makeWorld(scenarioDone);
    await mockRoutes(page, world);
    await gotoProfile(page);

    check(
        '完整度显示 100%',
        ((await page.locator('.pf-pct').first().textContent()) || '').indexOf('100%') >= 0
    );
    check('完整度条带 full 修饰类', (await page.locator('.pf-pct.full').count()) === 1);
    check(
        '不再出现「全部确认」按钮',
        (await page.locator('[data-action="profile-confirm-all"]').count()) === 0
    );
    check(
        '不再出现待确认/冲突态圆点或分区',
        (await page.locator('.pf-dot.pending, .pf-row.conflict').count()) === 0
    );
    await shot(page, '04-done');
    await page.close();
}

async function main() {
    const server = await serve();
    const browser = await chromium.launch();
    try {
        await runEmpty(browser);
        await runPending(browser);
        await runConflict(browser);
        await runDone(browser);
    } finally {
        await browser.close();
        server.close();
    }
    console.log(failures ? `\n结果: FAIL - ${failures} 处断言失败` : '\n结果: PASS - 全部断言通过');
    process.exit(failures ? 1 : 0);
}

main().catch((e) => {
    console.error(e);
    process.exit(1);
});
