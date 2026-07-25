// 真浏览器验收 ·「单位是系统按账套常用值填的」琥珀标记(推送日志页真实点击流)。
// 桩数据不是手写的:直接跑 services/erp/push_log_meta 的派生,喂给它的又是小助手在真账套上
// 跑出来的回执 —— 前端读的键名与后端派生的键名对不上,这里就渲染不出来(缝上真的压着)。
// 走真实导航:/home → 点左栏「推送日志」nav-item(禁 routeTo 捷径)→ 抓 getComputedStyle 断言
// 可见(禁 grep 类名)· 四语截图。模型抄 scripts/_erp_stock_honesty_ui_verify.cjs。
// 产物:tests/visual/_shot/erp-unit-guessed-*.png。
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8833;
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

// 后端派生真跑一遍:回执 → 列表项字段。手抄一份桩就等于把「键名对不对」这段测没了。
const RECEIPT = {
    ok: true,
    line_modes: [
        {
            seq: 1,
            name: 'PEARNLY PROBE ITEM',
            mode: 'stock_item',
            stkcod: 'PN00054',
            reason: '',
            created: true,
            unit_guessed: true,
            unit_code: 'พค',
        },
    ],
};
const derived = JSON.parse(
    execFileSync(
        'python',
        [
            '-c',
            'import sys,json;sys.path.insert(0,r"' +
                ROOT +
                '");from services.erp import push_log_meta as m;' +
                'print(json.dumps(m._derive_v3_meta(json.loads(sys.stdin.read()))))',
        ],
        {
            input: JSON.stringify(RECEIPT),
            encoding: 'utf8',
            env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
        }
    )
);
if (!derived.unit_guessed_lines) {
    console.error('🔴 后端没派生出 unit_guessed_lines,前端无从渲染:', derived);
    process.exit(2);
}

global.window = global.window || {};
require(path.join(ROOT, 'static/i18n-data.js'));
const I18N = global.window.I18N;
const tr = (lang, key) => I18N[lang][key];

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
// 两条桩:猜了单位的(阳性·字段来自真派生) + 票面给了单位的(阴性对照·绝不许误标)。
const ITEMS = [
    {
        ...BASE,
        id: 'log-unit-guessed',
        status: 'success',
        invoice_no: 'IV69/00911',
        created_at: new Date().toISOString(),
        external_doc_no: 'IV6900911',
        ...derived,
    },
    {
        ...BASE,
        id: 'log-unit-clean',
        status: 'success',
        invoice_no: 'IV69/00912',
        created_at: new Date().toISOString(),
        external_doc_no: 'IV6900912',
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
    await page.setViewportSize({ width: 1320, height: 1000 });

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

    await page.waitForSelector('.nav-item[data-route="push-logs"]', { timeout: 15000 });
    await page.click('.nav-item[data-route="push-logs"]');
    await page.waitForSelector('#erp-logs-list .erp-log-card', { timeout: 15000 });

    const results = [];
    for (const lang of LANGS) {
        await page.evaluate((l) => window.applyLang(l), lang);
        await page.click('.nav-item[data-route="push-logs"]');
        await page.waitForSelector('#erp-logs-list .erp-log-card', { timeout: 8000 });
        const probe = await page.evaluate(() => {
            const cs = (el) => {
                if (!el) return null;
                const s = getComputedStyle(el);
                return {
                    display: s.display,
                    visibility: s.visibility,
                    opacity: s.opacity,
                    color: s.color,
                    bg: s.backgroundColor,
                    h: el.getBoundingClientRect().height,
                    text: (el.textContent || '').trim(),
                };
            };
            const card = (id) => document.querySelector(`.erp-log-card[data-log-detail="${id}"]`);
            const out = {};
            for (const id of ['log-unit-guessed', 'log-unit-clean']) {
                const c = card(id);
                out[id + ':tag'] = cs(c && c.querySelector('.log-tag.unit-guessed'));
                const notes = c ? Array.from(c.querySelectorAll('.erp-log-note')) : [];
                out[id + ':note'] = cs(notes[0]);
                out[id + ':noteCount'] = notes.length;
            }
            const amber = cs(document.querySelector('.log-tag.uncosted, .log-tag.unit-guessed'));
            out.amberRef = amber;
            return out;
        });
        await page.screenshot({ path: path.join(OUT, `erp-unit-guessed-${lang}.png`) });
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
        const tag = probe['log-unit-guessed:tag'];
        const note = probe['log-unit-guessed:note'];
        const wantNote = tr(lang, 'erp-unit-guessed-note')
            .replace('{n}', String(derived.unit_guessed_lines))
            .replace('{u}', derived.unit_guessed_codes.join(' · '));
        check(
            `${lang}/badge`,
            visible(tag) && tag.text === tr(lang, 'erp-unit-guessed-tag'),
            `visible=${visible(tag)} "${tag ? tag.text : ''}"`
        );
        check(
            `${lang}/note-exact`,
            visible(note) && note.text.includes(wantNote),
            `visible=${visible(note)} "${(note && note.text ? note.text : '').slice(0, 70)}…"`
        );
        check(
            `${lang}/note-names-the-unit`,
            !!note && derived.unit_guessed_codes.every((c) => note.text.includes(c)),
            `codes=${derived.unit_guessed_codes.join(',')}`
        );
        check(
            `${lang}/amber-not-a-plain-tag`,
            !!tag && tag.color !== '' && tag.bg !== 'rgba(0, 0, 0, 0)',
            `color=${tag ? tag.color : '-'} bg=${tag ? tag.bg : '-'}`
        );
        check(
            `${lang}/clean-not-marked`,
            !probe['log-unit-clean:tag'] && probe['log-unit-clean:noteCount'] === 0,
            '票面给了单位的成功单没有任何标记'
        );
    }

    console.log(fail === 0 ? `\n✅ ALL PASS (${total}/${total})` : `\n🔴 ${fail}/${total} FAIL`);
    process.exit(fail === 0 ? 0 : 1);
})().catch((e) => {
    console.error(e);
    process.exit(2);
});
