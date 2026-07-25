// 真浏览器验收 · 存货科目组三档(推送日志页真实点击流)。
//   1 个合格候选 → 系统自动选,不 fail、不弹卡,成功卡上标出用的是哪个组(码 + 科目号 + 名);
//   0 个        → 弹「先去 Express 建一个」的卡(reason 用 stock_acc_group_missing 的文案);
//   ≥2 个       → 弹下拉卡,选项数 = 候选数(不替客户拍板)。
// 走真实导航:/home → 点左栏「推送日志」nav-item(禁 routeTo 捷径)→ 桩日志 → 点修复按钮 →
// 抓 getComputedStyle 断言可见(禁 grep 类名)。四语截图。
// 模型抄 scripts/_erp_stock_honesty_ui_verify.cjs。产物:tests/visual/_shot/erp-accgrp-tier-*.png。
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8832;
const LANGS = ['th', 'zh', 'en', 'ja'];
const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.map': 'application/json',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff2': 'font/woff2',
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
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

// 期望文案直接读 static/i18n-data.js(单一源)· 抄第二份进脚本改文案就会漂移。
global.window = global.window || {};
require(path.join(ROOT, 'static/i18n-data.js'));
const I18N = global.window.I18N;
const tr = (lang, key) => I18N[lang][key];

const GROUP_DM = {
    acccod: 'DM',
    name: 'วัตถุดิบ',
    stock_acc: '11-04-01-00',
    stock_acc_name: 'วัตถุดิบคงเหลือ',
    cogs_acc: '51-01-00-00',
    used_by: 17,
    fit: true,
};
const GROUP_ST01 = {
    acccod: 'ST01',
    stock_acc: '11-04-02-00',
    cogs_acc: '51-01-00-00',
    used_by: 19,
    fit: true,
};
const GROUP_LABEL = 'DM · 11-04-01-00 · วัตถุดิบคงเหลือ';

const BASE = {
    trigger: 'manual',
    push_type: 'invoice',
    endpoint_id: 'e1',
    endpoint_name: 'Express',
    ocr_buyer_name: 'บจก. ตัวอย่าง',
    http_status: 200,
    retry_count: 0,
    max_retries: 3,
    created_at: new Date().toISOString(),
};
const ITEMS = [
    // 档① 唯一候选 → 后端自动选,推送成功;卡上标出新建了库存品 + 挂的组。
    {
        ...BASE,
        id: 'log-auto',
        status: 'success',
        invoice_no: 'IV69/00911',
        external_doc_no: 'IV6900911',
        stock_created: 1,
        stock_acccod: GROUP_DM.acccod,
        stock_acc: GROUP_DM.stock_acc,
        stock_acc_name: GROUP_DM.stock_acc_name,
    },
    // 档⓪ 一个合格候选都没有 → 新码 + 空下拉,卡说「去 Express 建」。
    {
        ...BASE,
        id: 'log-missing',
        status: 'failed',
        invoice_no: 'IV69/00912',
        error_msg: 'EXPRESS_MANUAL: stock_acc_group_missing',
        category: 'stock_opening_needed',
        stock_fix: {
            needs: 'acc_group',
            items: [{ name: 'น้ำมันเครื่อง', stkcod: '' }],
            acc_groups: [],
            groups_reported: true,
        },
    },
    // 档② 两个合格候选 → 旧码 + 下拉,让会计选一次(系统不替他拍板)。
    {
        ...BASE,
        id: 'log-pick',
        status: 'failed',
        invoice_no: 'IV69/00913',
        error_msg: 'EXPRESS_MANUAL: stock_acc_group_required',
        category: 'stock_opening_needed',
        stock_fix: {
            needs: 'acc_group',
            items: [{ name: 'น้ำมันเครื่อง', stkcod: '' }],
            acc_groups: [GROUP_DM, GROUP_ST01],
            groups_reported: true,
        },
    },
];
const EPS = {
    items: [{ id: 'e1', adapter: 'express', name: 'Express', enabled: true, config: {} }],
};

function visible(cs) {
    return (
        !!cs &&
        cs.display !== 'none' &&
        cs.visibility !== 'hidden' &&
        parseFloat(cs.opacity) > 0 &&
        cs.h > 0
    );
}

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newContext().then((c) => c.newPage());
    await page.setViewportSize({ width: 1320, height: 1200 });

    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', 'th');
    });
    await page.route('**/api/**', async (route) => {
        const u = route.request().url();
        if (u.includes('/api/erp/logs'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ total: ITEMS.length, items: ITEMS }),
            });
        if (u.includes('/api/erp/endpoints'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(EPS),
            });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, items: [] }),
        });
    });

    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window._userInfo = Object.assign(window._userInfo || {}, {
            can_push_erp: true,
            plan: 'lifetime',
        });
        document.body.classList.remove('workspace-gate-preboot');
        const g = document.getElementById('workspace-gate-root');
        if (g) g.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important;}#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
    });

    // 真实点击流:点左栏「推送日志」nav-item(不用 routeTo)。
    await page.waitForSelector('.nav-item[data-route="push-logs"]', { timeout: 15000 });
    await page.click('.nav-item[data-route="push-logs"]');
    await page.waitForSelector('#erp-logs-list .erp-log-card', { timeout: 15000 });

    const results = [];
    for (const lang of LANGS) {
        await page.evaluate((l) => window.applyLang(l), lang);
        await page.click('.nav-item[data-route="push-logs"]'); // 重渲染当前语言
        await page.waitForSelector('#erp-logs-list .erp-log-card', { timeout: 8000 });
        for (const id of ['log-missing', 'log-pick']) {
            const btn = await page.$(`[data-erpexc-acctfix="${id}"]`);
            if (btn) await btn.click();
        }
        const probe = await page.evaluate(() => {
            const cs = (el) => {
                if (!el) return null;
                const s = getComputedStyle(el);
                return {
                    display: s.display,
                    visibility: s.visibility,
                    opacity: s.opacity,
                    h: el.getBoundingClientRect().height,
                    text: (el.textContent || '').trim(),
                };
            };
            const card = (id) => document.querySelector(`.erp-log-card[data-log-detail="${id}"]`);
            const q = (id, sel) => card(id) && card(id).querySelector(sel);
            const sel = q('log-pick', '.erp-exc-accgrp [data-accgrp-select]');
            return {
                autoTag: cs(q('log-auto', '.log-tag.stock-new')),
                autoNote: cs(q('log-auto', '.erp-log-note.stock-new')),
                autoRepairBtn: cs(q('log-auto', '[data-erpexc-acctfix]')),
                autoReason: cs(q('log-auto', '.erp-log-reason')),
                missingPanel: cs(q('log-missing', '.erp-exc-accgrp .erp-exc-acctfix-nochart')),
                missingReason: cs(q('log-missing', '.erp-log-reason span')),
                missingSelect: cs(q('log-missing', '[data-accgrp-select]')),
                pickSelect: cs(sel),
                pickOptions: sel ? Array.from(sel.options).map((o) => o.value) : [],
                pickHint: cs(q('log-pick', '.erp-exc-accgrp-hint')),
                pickReason: cs(q('log-pick', '.erp-log-reason span')),
            };
        });
        await page.screenshot({ path: path.join(OUT, `erp-accgrp-tier-${lang}.png`) });
        results.push({ lang, probe });
    }

    await browser.close();
    srv.close();

    let fail = 0;
    let total = 0;
    const check = (name, ok, detail) => {
        total++;
        if (!ok) fail++;
        console.log(`[${ok ? 'PASS' : 'FAIL'}] ${name} :: ${detail}`);
    };
    for (const { lang, probe } of results) {
        // 档① 自动选:不弹卡(没有修复按钮、没有失败摘要),但把用的组标出来。
        const wantNote = tr(lang, 'erp-stock-new-note')
            .replace('{n}', '1')
            .replace('{g}', GROUP_LABEL);
        check(
            `${lang}/tier1-no-card`,
            !probe.autoRepairBtn && !probe.autoReason,
            '唯一候选自动选 → 成功卡上没有修复按钮也没有失败摘要'
        );
        check(
            `${lang}/tier1-tag`,
            visible(probe.autoTag) && probe.autoTag.text === tr(lang, 'erp-stock-new-tag'),
            `visible=${visible(probe.autoTag)} "${probe.autoTag ? probe.autoTag.text : ''}"`
        );
        check(
            `${lang}/tier1-group-shown`,
            visible(probe.autoNote) &&
                probe.autoNote.text.includes(wantNote) &&
                probe.autoNote.text.includes(GROUP_LABEL),
            `visible=${visible(probe.autoNote)} "${(probe.autoNote && probe.autoNote.text ? probe.autoNote.text : '').slice(0, 70)}…"`
        );
        // 档⓪ 零候选:卡是「去 Express 建」那句,且没有下拉可选(没得选就别摆一个空下拉)。
        check(
            `${lang}/tier0-build-in-express`,
            visible(probe.missingPanel) &&
                probe.missingPanel.text === tr(lang, 'erp-accgrp-nogroups') &&
                !probe.missingSelect,
            `visible=${visible(probe.missingPanel)} "${(probe.missingPanel && probe.missingPanel.text ? probe.missingPanel.text : '').slice(0, 50)}…"`
        );
        check(
            `${lang}/tier0-reason-text`,
            visible(probe.missingReason) &&
                probe.missingReason.text === tr(lang, 'erp-reason-stock-acc-group-missing'),
            `"${(probe.missingReason && probe.missingReason.text ? probe.missingReason.text : '').slice(0, 50)}…"`
        );
        // 档② 多候选:真下拉 + 选项数 = 候选数,文案还是「选一个」那句(不是「去建」)。
        check(
            `${lang}/tier2-dropdown`,
            visible(probe.pickSelect) &&
                probe.pickOptions.join(',') === ',DM,ST01' &&
                visible(probe.pickHint),
            `visible=${visible(probe.pickSelect)} options=${JSON.stringify(probe.pickOptions)}`
        );
        check(
            `${lang}/tier2-reason-text`,
            visible(probe.pickReason) &&
                probe.pickReason.text === tr(lang, 'erp-reason-stock-acc-group') &&
                probe.pickReason.text !== tr(lang, 'erp-reason-stock-acc-group-missing'),
            `"${(probe.pickReason && probe.pickReason.text ? probe.pickReason.text : '').slice(0, 50)}…"`
        );
    }

    console.log(fail === 0 ? `\n✅ ALL PASS (${total}/${total})` : `\n🔴 ${fail}/${total} FAIL`);
    process.exit(fail === 0 ? 0 : 1);
})().catch((e) => {
    console.error(e);
    process.exit(2);
});
