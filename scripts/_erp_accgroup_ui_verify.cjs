// 真浏览器验收 · 失败卡「选存货科目组」(B4·车道 D)。
// 走真实点击流:/home → 点左栏「推送日志」nav-item → 桩三条 stock_opening_needed 失败日志
// (needs=acc_group 有候选 / needs=acc_group 无候选 / 老口径无 needs)→ 点卡上按钮展开面板 →
// getComputedStyle 断言面板/下拉/诚实边界句真的可见、四语文案逐字对上 → 选中提交 → 拦截 PATCH
// 断言请求正确;第三条兜住既有补期初卡没被新分支抢走。
// 候选数据取自真账套只读副本 70EXP_c6(ISACC/GLACC/STMAS 逐字·非编造)。
// 模型抄 scripts/_erp_error_friendly_ui_verify.cjs。产物:tests/visual/_shot/erp-accgrp-*.png。
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8827;
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

// stock_fix.acc_groups 的候选(字段名同 agent_reporting._STOCK_ACC_GROUP_KEYS)。
// 数据取 70EXP_c6 真账套 ISACC/GLACC/STMAS,两条故意不同形态:
//   ST01 = 小助手只报了白名单里的字段(无科目名/无用量)→ 缺的段一律不显,不拿占位符冒充;
//   ST10 = 连科目名和用量一起报上来 → 整行信息拼齐。ST01 的 ACCDES 等于 ACCCOD,不显两遍。
const ACC_GROUPS = [
    {
        acccod: 'ST01',
        name: 'ST01',
        method: 'A',
        stock_acc: '11-04-02-00',
        cogs_acc: '51-01-00-00',
        fit: true,
    },
    {
        acccod: 'ST10',
        name: 'สินค้าสำเร็จรูปคงเหลือน้ำมันเครื่อง',
        method: 'A',
        stock_acc: '11-04-04-00',
        stock_acc_name: 'สินค้าสำเร็จรูป(น้ำมันเครื่อง)',
        cogs_acc: '51-01-00-00',
        cogs_acc_name: 'ต้นทุนสินค้าเพื่อขาย',
        used_by: 146,
        fit: true,
    },
];

// i18n-data.js 里的四语文案逐字副本(渲染出来的必须是这些字,不是 key 也不是别的语言)。
const I18N = {
    zh: {
        open: '选存货科目组',
        hint: '这个账套还没指定新建库存品记进哪个存货科目组。选一个,之后系统在这个账套建的库存品都用它。',
        label: '存货科目组',
        pick: '请选择…',
        inv: '存货',
        cogs: '销货成本',
        usedBy: '{n} 个商品在用',
        warn: '这个选择决定该账套所有新建库存品记进哪个存货科目 · 选错要到 Express 里逐个改商品档,系统不会替你纠正',
        submit: '保存',
        needPick: '请先选一个存货科目组',
        ok: '已保存 · 现在可以重推这张单了',
        noGroups:
            '这个账套里还没有能拿来建库存品的存货科目组 · 请先在 Express 建一个(存货科目 + 销货成本科目),再回来选',
    },
    en: {
        open: 'Choose inventory account group',
        hint: 'This account set has not been told which inventory account group new stock items belong to. Pick one and every stock item the system creates here will use it.',
        label: 'Inventory account group',
        pick: 'Select…',
        inv: 'Inventory',
        cogs: 'COGS',
        usedBy: 'used by {n} items',
        warn: 'This choice decides which inventory account every new stock item in this account set is booked to. Get it wrong and each item has to be corrected by hand in Express — the system will not fix it for you.',
        submit: 'Save',
        needPick: 'Pick an inventory account group first',
        ok: 'Saved · you can re-push this document now',
        noGroups:
            'This account set has no usable inventory account group yet. Create one in Express first (inventory account + COGS account), then come back and pick it.',
    },
    th: {
        open: 'เลือกกลุ่มบัญชีสินค้าคงคลัง',
        hint: 'ชุดบัญชีนี้ยังไม่ได้ระบุว่าสินค้าคงคลังที่สร้างใหม่จะผูกกับกลุ่มบัญชีใด เลือกหนึ่งกลุ่ม แล้วสินค้าคงคลังที่ระบบสร้างในชุดบัญชีนี้จะใช้กลุ่มนั้นทั้งหมด',
        label: 'กลุ่มบัญชีสินค้าคงคลัง',
        pick: 'เลือก…',
        inv: 'สินค้าคงเหลือ',
        cogs: 'ต้นทุนขาย',
        usedBy: 'มีสินค้าใช้อยู่ {n} รายการ',
        warn: 'ตัวเลือกนี้กำหนดว่าสินค้าคงคลังที่สร้างใหม่ทุกตัวในชุดบัญชีนี้จะลงบัญชีสินค้าคงเหลือบัญชีใด หากเลือกผิดต้องเข้าไปแก้ทะเบียนสินค้าทีละตัวใน Express ระบบไม่แก้ให้อัตโนมัติ',
        submit: 'บันทึก',
        needPick: 'กรุณาเลือกกลุ่มบัญชีสินค้าคงคลังก่อน',
        ok: 'บันทึกแล้ว · ส่งเอกสารนี้ใหม่ได้เลย',
        noGroups:
            'ชุดบัญชีนี้ยังไม่มีกลุ่มบัญชีที่ใช้สร้างสินค้าคงคลังได้ กรุณาสร้างใน Express ก่อน (บัญชีสินค้าคงเหลือ + บัญชีต้นทุนขาย) แล้วกลับมาเลือก',
    },
    ja: {
        open: '在庫勘定グループを選択',
        hint: 'この帳簿セットでは、新規作成する在庫品をどの在庫勘定グループに紐付けるかが未指定です。1 つ選ぶと、以後システムがこの帳簿セットで作成する在庫品はすべてそのグループを使います。',
        label: '在庫勘定グループ',
        pick: '選択してください…',
        inv: '棚卸資産',
        cogs: '売上原価',
        usedBy: '{n} 品目が使用中',
        warn: 'この選択は、この帳簿セットで新規作成する在庫品すべての棚卸資産勘定を決めます。誤って選ぶと Express で商品マスタを 1 件ずつ手作業で直す必要があり、システムは自動修正しません。',
        submit: '保存',
        needPick: '在庫勘定グループを選択してください',
        ok: '保存しました · この伝票を再送信できます',
        noGroups:
            'この帳簿セットには在庫品の作成に使える勘定グループがまだありません。先に Express で作成し(棚卸資産勘定 + 売上原価勘定)、戻って選択してください。',
    },
};

// 期望的下拉选项文字(独立算一遍 · 不复用实现的拼装函数,免得实现错了测试跟着错)。
function expectOption(lang, g) {
    const L = I18N[lang];
    const parts = [g.acccod];
    if (g.name && g.name !== g.acccod) parts.push(g.name);
    if (g.stock_acc)
        parts.push(`${L.inv} ${g.stock_acc}${g.stock_acc_name ? ' ' + g.stock_acc_name : ''}`);
    if (g.cogs_acc)
        parts.push(`${L.cogs} ${g.cogs_acc}${g.cogs_acc_name ? ' ' + g.cogs_acc_name : ''}`);
    if (typeof g.used_by === 'number') parts.push(L.usedBy.replace('{n}', String(g.used_by)));
    return parts.join(' · ');
}

// 后端把库存路两支失败都归 category=stock_opening_needed,靠 stock_fix.needs 分卡。
const base = {
    status: 'failed',
    trigger: 'manual',
    push_type: 'invoice',
    endpoint_id: 'e1',
    endpoint_name: 'Express',
    ocr_buyer_name: 'บจก. ตัวอย่าง',
    error_msg: 'EXPRESS_MANUAL: stock_acc_group_required',
    http_status: 200,
    retry_count: 3,
    max_retries: 3,
    category: 'stock_opening_needed',
};
const LOGS = {
    total: 3,
    items: [
        {
            ...base,
            id: 'log-accgrp',
            invoice_no: 'IV69/00481',
            created_at: new Date().toISOString(),
            stock_fix: { needs: 'acc_group', items: [], acc_groups: ACC_GROUPS },
        },
        {
            ...base,
            id: 'log-accgrp-none',
            invoice_no: 'IV69/00482',
            created_at: new Date().toISOString(),
            stock_fix: { needs: 'acc_group', items: [], acc_groups: [] },
        },
        // 老口径行(2026-07-25 前入库的日志没有 needs)· 必须还是走补期初卡,不能被新分支抢走。
        {
            ...base,
            id: 'log-open',
            invoice_no: 'IV69/00483',
            created_at: new Date().toISOString(),
            error_msg: 'STOCK_ITEM_NOT_FOUND',
            stock_fix: { items: [{ name: 'น้ำมันเครื่อง 15W-40', stkcod: '58402392' }] },
        },
    ],
};
const EPS = {
    items: [{ id: 'e1', adapter: 'express', name: 'Express', enabled: true, config: {} }],
};

const patchCalls = [];

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newContext().then((c) => c.newPage());
    await page.setViewportSize({ width: 1320, height: 1080 });

    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', 'th');
    });
    await page.route('**/api/**', async (route) => {
        const req = route.request();
        const u = req.url();
        if (u.includes('/express-stock-acc-group')) {
            patchCalls.push({ url: u, method: req.method(), body: req.postData() });
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ ok: true, stock_acccod: 'ST10' }),
            });
        }
        if (u.includes('/api/erp/logs'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(LOGS),
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
    await page.waitForSelector('#erp-logs-list .erp-log-card.fail', { timeout: 15000 });

    const checks = [];
    const warns = [];
    const ck = (name, ok, detail) => checks.push({ name, ok: !!ok, detail: detail || '' });
    // WARN 记存量缺陷:本车道无权修、但验收要如实报出来,不当没看见。
    const warn = (name, ok, detail) => warns.push({ name, ok: !!ok, detail: detail || '' });

    // 存量缺陷探针:.erp-exc-acctfix 只写了 display:flex、没配 [hidden]{display:none} →
    // hidden 属性被无条件压过,四张修复卡(补科目/绑主体/补期初/选存货科目组)一渲染就是展开的,
    // 按钮点了没有视觉变化。CSS 属主修一行 `.erp-exc-acctfix[hidden]{display:none}` 即可
    // (同文件的 .erp-exc-batch[hidden] 早就这么修过)。
    const collapsed = await page.evaluate(() => {
        const p = document.querySelector('[data-acctfix-panel="log-accgrp"]');
        return p
            ? { hiddenAttr: p.hasAttribute('hidden'), display: getComputedStyle(p).display }
            : null;
    });
    ck(
        'panel/hidden-attr-before-click',
        collapsed && collapsed.hiddenAttr,
        JSON.stringify(collapsed)
    );
    warn(
        'panel/collapsed-before-click',
        collapsed && collapsed.display === 'none',
        `存量 CSS 缺陷:.erp-exc-acctfix 缺 [hidden]{display:none} · 实测 display=${collapsed && collapsed.display}`
    );

    async function runLang(lang) {
        const L = I18N[lang];
        await page.evaluate((l) => window.applyLang(l), lang);
        await page.click('.nav-item[data-route="push-logs"]'); // 重渲染当前语言
        await page.waitForSelector('[data-erpexc-acctfix="log-accgrp"]', { timeout: 8000 });

        // ① 卡上按钮:文案 + 真可见
        const btn = await page.evaluate(() => {
            const b = document.querySelector('[data-erpexc-acctfix="log-accgrp"]');
            if (!b) return null;
            const cs = getComputedStyle(b);
            const r = b.getBoundingClientRect();
            return {
                text: b.textContent.trim(),
                display: cs.display,
                visibility: cs.visibility,
                opacity: cs.opacity,
                w: r.width,
                h: r.height,
            };
        });
        ck(
            `${lang}/open-btn`,
            btn &&
                btn.text === L.open &&
                btn.display !== 'none' &&
                btn.visibility !== 'hidden' &&
                parseFloat(btn.opacity) > 0 &&
                btn.w > 0 &&
                btn.h > 0,
            JSON.stringify(btn)
        );

        // ② 展开面板 → 下拉 / 说明 / 诚实边界句 全部真渲染出来
        await page.click('[data-erpexc-acctfix="log-accgrp"]');
        await page.waitForSelector('[data-acctfix-panel="log-accgrp"] select[data-accgrp-select]', {
            timeout: 8000,
        });
        const panel = await page.evaluate(() => {
            const vis = (el) => {
                if (!el) return null;
                const cs = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return {
                    text: (el.textContent || '').trim(),
                    display: cs.display,
                    visibility: cs.visibility,
                    opacity: cs.opacity,
                    w: r.width,
                    h: r.height,
                };
            };
            const p = document.querySelector('[data-acctfix-panel="log-accgrp"]');
            const sel = p && p.querySelector('select[data-accgrp-select]');
            return {
                panel: vis(p),
                hint: vis(p && p.querySelector('.erp-exc-accgrp-hint')),
                warn: vis(p && p.querySelector('.erp-exc-accgrp-warn')),
                label: vis(p && p.querySelector('.erp-exc-acctfix-slot span')),
                submit: vis(p && p.querySelector('[data-acctfix-submit]')),
                select: vis(sel),
                options: sel
                    ? Array.from(sel.options).map((o) => ({ v: o.value, t: o.textContent }))
                    : [],
                fixKind: p ? p.getAttribute('data-fix-kind') : null,
                endpoint: p ? p.getAttribute('data-accgrp-endpoint') : null,
            };
        });
        const visible = (v) =>
            !!v &&
            v.display !== 'none' &&
            v.visibility !== 'hidden' &&
            parseFloat(v.opacity) > 0 &&
            v.h > 0 &&
            v.w > 0;

        ck(
            `${lang}/panel-visible`,
            visible(panel.panel),
            JSON.stringify(panel.panel && panel.panel.display)
        );
        ck(`${lang}/select-visible`, visible(panel.select), JSON.stringify(panel.select));
        ck(
            `${lang}/hint-text`,
            visible(panel.hint) && panel.hint.text === L.hint,
            panel.hint && panel.hint.text
        );
        ck(
            `${lang}/warn-text`,
            visible(panel.warn) && panel.warn.text === L.warn,
            panel.warn && panel.warn.text
        );
        ck(
            `${lang}/label-text`,
            visible(panel.label) && panel.label.text === L.label,
            panel.label && panel.label.text
        );
        ck(
            `${lang}/submit-text`,
            visible(panel.submit) && panel.submit.text === L.submit,
            panel.submit && panel.submit.text
        );
        ck(
            `${lang}/panel-kind`,
            panel.fixKind === 'accgroup' && panel.endpoint === 'e1',
            `${panel.fixKind}/${panel.endpoint}`
        );

        const wantOpts = [
            { v: '', t: L.pick },
            { v: 'ST01', t: expectOption(lang, ACC_GROUPS[0]) },
            { v: 'ST10', t: expectOption(lang, ACC_GROUPS[1]) },
        ];
        ck(
            `${lang}/options`,
            JSON.stringify(panel.options) === JSON.stringify(wantOpts),
            JSON.stringify(panel.options)
        );

        // ③ 空候选卡:显「先去 Express 建一个」· 不给死胡同的空下拉
        await page.click('[data-erpexc-acctfix="log-accgrp-none"]');
        const none = await page.evaluate(() => {
            const p = document.querySelector('[data-acctfix-panel="log-accgrp-none"]');
            if (!p) return null;
            const cs = getComputedStyle(p);
            return {
                text: p.textContent.trim(),
                display: cs.display,
                visibility: cs.visibility,
                opacity: cs.opacity,
                h: p.getBoundingClientRect().height,
                w: p.getBoundingClientRect().width,
                hasSelect: !!p.querySelector('select'),
            };
        });
        ck(
            `${lang}/nogroups`,
            visible(none) && none.text === L.noGroups && !none.hasSelect,
            none && none.text
        );

        // ④ 老口径行:仍渲染补期初三格,没被存货科目组卡抢走
        const legacy = await page.evaluate(() => {
            const p = document.querySelector('[data-acctfix-panel="log-open"]');
            return p
                ? {
                      kind: p.getAttribute('data-fix-kind'),
                      rows: p.querySelectorAll('.erp-exc-stockopen-row').length,
                      hasQty: !!p.querySelector('[data-stockopen-qty]'),
                      hasAccGrpSelect: !!p.querySelector('[data-accgrp-select]'),
                  }
                : null;
        });
        ck(
            `${lang}/legacy-opening-card`,
            legacy && !legacy.kind && legacy.rows === 1 && legacy.hasQty && !legacy.hasAccGrpSelect,
            JSON.stringify(legacy)
        );

        await page.screenshot({ path: path.join(OUT, `erp-accgrp-${lang}.png`), fullPage: false });
    }

    for (const lang of ['th', 'zh', 'en', 'ja']) await runLang(lang);

    // ④ 提交路径(在 ja 之后回到主用户语言泰文再走一遍真实操作)
    await page.evaluate(() => window.applyLang('th'));
    await page.click('.nav-item[data-route="push-logs"]');
    await page.waitForSelector('[data-erpexc-acctfix="log-accgrp"]', { timeout: 8000 });
    await page.click('[data-erpexc-acctfix="log-accgrp"]');
    await page.waitForSelector('[data-acctfix-panel="log-accgrp"] select[data-accgrp-select]');

    // 没选就提交 → 只提示,不发请求(不静默写坏配置)
    await page.click('[data-acctfix-panel="log-accgrp"] [data-acctfix-submit]');
    const toastEmpty = await page
        .waitForSelector('#mp-toast-wrap .mp-toast.error span', { timeout: 5000 })
        .then((h) => h.textContent())
        .catch(() => null);
    ck('submit/need-pick-toast', toastEmpty === I18N.th.needPick, String(toastEmpty));
    ck('submit/no-request-when-empty', patchCalls.length === 0, JSON.stringify(patchCalls));

    // 选一个 → 提交 → 断言真发出了正确的 PATCH
    await page.selectOption('[data-acctfix-panel="log-accgrp"] select[data-accgrp-select]', 'ST10');
    await page.screenshot({ path: path.join(OUT, 'erp-accgrp-picked.png') });
    await page.click('[data-acctfix-panel="log-accgrp"] [data-acctfix-submit]');
    const toastOk = await page
        .waitForSelector('#mp-toast-wrap .mp-toast.success span', { timeout: 8000 })
        .then((h) => h.textContent())
        .catch(() => null);
    await page.screenshot({ path: path.join(OUT, 'erp-accgrp-saved.png') });

    const call = patchCalls[0];
    ck('submit/one-request', patchCalls.length === 1, JSON.stringify(patchCalls));
    ck('submit/method', call && call.method === 'PATCH', call && call.method);
    ck(
        'submit/url',
        call &&
            /\/api\/erp\/endpoints\/e1\/express-stock-acc-group$/.test(new URL(call.url).pathname),
        call && call.url
    );
    ck(
        'submit/body',
        call && call.body === JSON.stringify({ stock_acccod: 'ST10' }),
        call && call.body
    );
    ck('submit/ok-toast', toastOk === I18N.th.ok, String(toastOk));

    await browser.close();
    srv.close();

    let fail = 0;
    for (const c of checks) {
        if (!c.ok) fail++;
        console.log(`[${c.ok ? 'PASS' : 'FAIL'}] ${c.name} :: ${c.detail}`);
    }
    for (const w of warns) if (!w.ok) console.log(`[WARN] ${w.name} :: ${w.detail}`);
    console.log(fail === 0 ? `\nALL PASS (${checks.length}/${checks.length})` : `\n${fail} FAIL`);
    process.exit(fail === 0 ? 0 : 1);
})().catch((e) => {
    console.error(e);
    process.exit(2);
});
