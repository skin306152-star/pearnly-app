// 真浏览器验收 · 两个「状态诚实」缺口(推送日志页真实点击流)。
//   件一 科目组空态分两种成因:小助手没上报过(groups_reported=false)→ 说「等它报上来」,
//        绝不能让会计去 Express 白建;上报过但确实没有合格组 → 才是「去 Express 建一个」。
//   件二 未结转成本:成功单也要显性标出来(徽标 + 提示条),筛选器能把它们捞回来。
// 走真实导航:/home → 点左栏「推送日志」nav-item(禁 routeTo 捷径)→ 桩日志 → 点开修复面板 /
// 点筛选 chip → 抓 getComputedStyle 断言可见(禁 grep 类名)。四语截图。
// 模型抄 scripts/_erp_error_friendly_ui_verify.cjs。产物:tests/visual/_shot/erp-stock-honesty-*.png。
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8826;
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

// 期望文案直接读 static/i18n-data.js(单一源)· 抄第二份进脚本改文案就会漂移(见 _rcx_test.cjs 同法)。
global.window = global.window || {};
require(path.join(ROOT, 'static/i18n-data.js'));
const I18N = global.window.I18N;
const tr = (lang, key) => I18N[lang][key];
// 除了逐字对上,还钉「这句必须提到谁」—— 防两句空态被互换后仍逐字通过。
const KEY_FRAGMENTS = {
    // 未上报:必须提「小助手 / agent」且**不得**出现「去 Express 建」的指引。
    'erp-accgrp-unreported': {
        must: { zh: '小助手', en: 'agent', th: 'Agent', ja: 'アシスタント' },
    },
    'erp-accgrp-nogroups': { must: { zh: 'Express', en: 'Express', th: 'Express', ja: 'Express' } },
};

const BASE = {
    trigger: 'manual',
    push_type: 'invoice',
    endpoint_id: 'e1',
    endpoint_name: 'Express',
    ocr_buyer_name: 'บจก. ตัวอย่าง',
    http_status: 200,
    retry_count: 0,
    max_retries: 3,
};
const STOCK_FIX_BASE = {
    needs: 'acc_group',
    items: [{ name: 'น้ำมันเครื่อง', stkcod: '' }],
    acc_groups: [],
};
// 四条桩:两种空态 + 已结转成功(阴性对照) + 未结转成本(含新建库存品)。
const ITEMS = [
    {
        ...BASE,
        id: 'log-unreported',
        status: 'failed',
        invoice_no: 'IV69/00901',
        created_at: new Date().toISOString(),
        error_msg: 'EXPRESS_MANUAL: stock_acc_group_required',
        category: 'stock_opening_needed',
        stock_fix: { ...STOCK_FIX_BASE, groups_reported: false },
    },
    {
        ...BASE,
        id: 'log-nogroups',
        status: 'failed',
        invoice_no: 'IV69/00902',
        created_at: new Date().toISOString(),
        error_msg: 'EXPRESS_MANUAL: stock_acc_group_required',
        category: 'stock_opening_needed',
        stock_fix: { ...STOCK_FIX_BASE, groups_reported: true },
    },
    {
        ...BASE,
        id: 'log-clean',
        status: 'success',
        invoice_no: 'IV69/00903',
        created_at: new Date().toISOString(),
        external_doc_no: 'IV6900903',
    },
    {
        ...BASE,
        id: 'log-uncosted',
        status: 'success',
        invoice_no: 'IV69/00904',
        created_at: new Date().toISOString(),
        external_doc_no: 'IV6900904',
        uncosted_lines: 2,
        uncosted_created: true,
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
    await page.setViewportSize({ width: 1320, height: 1100 });

    // 后端筛选是真事:status=uncosted 只回未结转成本那条(证明 chip 真的走了服务端筛选)。
    let lastLogsUrl = '';
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', 'th');
    });
    await page.route('**/api/**', async (route) => {
        const u = route.request().url();
        if (u.includes('/api/erp/logs')) {
            lastLogsUrl = u;
            const only = /[?&]status=uncosted(&|$)/.test(u);
            const items = only ? ITEMS.filter((i) => i.uncosted_lines) : ITEMS;
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ total: items.length, items }),
            });
        }
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
        // 两张失败卡各点开自己的修复面板(委托绑定的真实按钮,不手动改 hidden)。
        for (const id of ['log-unreported', 'log-nogroups']) {
            const btn = await page.$(`[data-erpexc-acctfix="${id}"]`);
            if (btn) await btn.click();
        }
        // 真悬停到「未结转成本」徽章上 —— 解释现在挂在它的提示里,不悬停就该是隐藏的。
        await page.hover('.erp-log-card[data-log-detail="log-uncosted"] .log-tag.uncosted');
        await page.waitForTimeout(200);
        const probe = await page.evaluate(() => {
            const cs = (el) => {
                if (!el) return null;
                const s = getComputedStyle(el);
                return {
                    display: s.display,
                    visibility: s.visibility,
                    opacity: s.opacity,
                    h: el.getBoundingClientRect().height,
                    w: el.getBoundingClientRect().width,
                    // 徽章里嵌了提示元素 —— 优先取它自己的文本节点,否则标签名会拖着整段解释;
                    // 标签藏在子元素里的(筛选 chip)自身没有文本节点,退回整体 textContent。
                    text:
                        Array.from(el.childNodes)
                            .filter((n) => n.nodeType === 3)
                            .map((n) => n.nodeValue)
                            .join('')
                            .trim() || (el.textContent || '').trim(),
                };
            };
            const card = (id) => document.querySelector(`.erp-log-card[data-log-detail="${id}"]`);
            const out = {};
            for (const id of ['log-unreported', 'log-nogroups']) {
                const p =
                    card(id) && card(id).querySelector('.erp-exc-accgrp .erp-exc-acctfix-nochart');
                out[id] = cs(p);
            }
            for (const id of ['log-clean', 'log-uncosted']) {
                const c = card(id);
                const tag = c && c.querySelector('.log-tag.uncosted');
                out[id + ':tag'] = cs(tag);
                // 解释改挂徽章的悬停提示:伪元素没有 rect,故读它的计算样式 + data-tip 原文。
                out[id + ':note'] = tag ? cs(tag.querySelector('.log-tip')) : null;
            }
            out['strip-count'] = document.querySelectorAll('.erp-log-note').length;
            out['chip'] = cs(
                document.querySelector('#erp-logs-filters [data-filter-val="uncosted"]')
            );
            return out;
        });
        await page.screenshot({ path: path.join(OUT, `erp-stock-honesty-${lang}.png`) });
        results.push({ lang, probe });
    }

    // 筛选器:点「未结转成本」chip → 请求带 status=uncosted → 列表只剩那一条。
    await page.evaluate((l) => window.applyLang(l), 'th');
    await page.click('#erp-logs-filters [data-filter-val="uncosted"]');
    await page.waitForFunction(
        () => document.querySelectorAll('#erp-logs-list .erp-log-card').length === 1,
        { timeout: 8000 }
    );
    const filtered = await page.evaluate(() =>
        Array.from(document.querySelectorAll('#erp-logs-list .erp-log-card')).map((c) => ({
            id: c.getAttribute('data-log-detail'),
            tipped: !!c.querySelector('.log-tag.uncosted .log-tip'),
        }))
    );
    await page.screenshot({ path: path.join(OUT, 'erp-stock-honesty-filter.png') });

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
        for (const [id, key] of [
            ['log-unreported', 'erp-accgrp-unreported'],
            ['log-nogroups', 'erp-accgrp-nogroups'],
        ]) {
            const p = probe[id];
            const want = tr(lang, key);
            const other = tr(
                lang,
                key === 'erp-accgrp-nogroups' ? 'erp-accgrp-unreported' : 'erp-accgrp-nogroups'
            );
            const frag = KEY_FRAGMENTS[key].must[lang];
            const ok = visible(p) && p.text === want && p.text !== other && p.text.includes(frag);
            check(
                `${lang}/${id}`,
                ok,
                `visible=${visible(p)} exactKey=${p && p.text === want} "${(p && p.text ? p.text : '').slice(0, 46)}…"`
            );
        }
        // 未结转成本:该标的标了,没有的绝不误标(阴性对照)。
        const tag = probe['log-uncosted:tag'];
        const note = probe['log-uncosted:note'];
        const wantNote =
            tr(lang, 'erp-uncosted-note').replace('{n}', '2') +
            ' · ' +
            tr(lang, 'erp-uncosted-created');
        check(
            `${lang}/uncosted-badge`,
            visible(tag) && tag.text === tr(lang, 'erp-uncosted-tag'),
            `visible=${visible(tag)} "${tag ? tag.text : ''}"`
        );
        // 解释挂在徽章的悬停提示里(此前是每张卡下方一条整宽横幅,一屏 8 张就把同一段话印 8 遍)。
        check(
            `${lang}/uncosted-tip-text`,
            !!note && note.text.includes(wantNote),
            `"${(note && note.text ? note.text : '').slice(0, 50)}…"`
        );
        check(
            `${lang}/uncosted-tip-shown-on-hover`,
            visible(note),
            `visibility=${note && note.visibility} opacity=${note && note.opacity} h=${note && note.h}`
        );
        // 换行,不是拖成一长条 —— 这是这次改动被点名要的
        check(
            `${lang}/uncosted-tip-wraps`,
            !!note && note.h > 26 && note.w <= 344,
            `真实高度=${note && Math.round(note.h)}px(一行约 17)· 宽=${note && Math.round(note.w)}`
        );
        check(
            `${lang}/no-fullwidth-strip`,
            !probe['strip-count'],
            `整宽提示条已删除(实剩 ${probe['strip-count']} 条)`
        );
        check(
            `${lang}/clean-not-marked`,
            !probe['log-clean:tag'] && !probe['log-clean:note'],
            '正常结转的成功单没有任何未结转标记'
        );
        check(
            `${lang}/filter-chip`,
            visible(probe.chip) && probe.chip.text === tr(lang, 'erp-uncosted-tag'),
            `visible=${visible(probe.chip)} "${probe.chip ? probe.chip.text : ''}"`
        );
    }
    check(
        'filter/server-side',
        /[?&]status=uncosted(&|$)/.test(lastLogsUrl),
        `lastLogsUrl=${lastLogsUrl.replace(/^.*\/api/, '/api')}`
    );
    check(
        'filter/only-uncosted-rows',
        filtered.length === 1 && filtered[0].id === 'log-uncosted' && filtered[0].tipped,
        JSON.stringify(filtered)
    );

    console.log(fail === 0 ? `\n✅ ALL PASS (${total}/${total})` : `\n🔴 ${fail}/${total} FAIL`);
    process.exit(fail === 0 ? 0 : 1);
})().catch((e) => {
    console.error(e);
    process.exit(2);
});
