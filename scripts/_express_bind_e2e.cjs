// E2E: Express direction_unknown 异常卡「绑定主体」面板 · 真站 pearnly.com · pearnly_e2e_3。
// 验:卡渲染 + 下拉填充账套主体 + 点开面板可见 + 选主体提交时 POST express-bind-subject 带 workspace_client_id。
/* eslint-disable no-undef */
const { chromium } = require('playwright');
const path = require('path');
const OUT = path.resolve(__dirname, '..', 'outputs', 'express-bind');
const BASE = 'https://pearnly.com';
const A = { username: 'pearnly_e2e_3', password: 'Pe@rnly-E2E-3p4' };

(async () => {
    const b = await chromium.launch();
    const p = await b.newPage();
    const bindReqs = [];
    p.on('request', (r) => {
        if (r.url().includes('express-bind-subject'))
            bindReqs.push({ method: r.method(), body: r.postData() });
    });

    const tok = (await (await p.request.post(BASE + '/api/login', { data: A })).json()).token;
    await p.addInitScript((t) => {
        localStorage.setItem('mrpilot_token', t);
        localStorage.setItem('pearnly_active_workspace_client_id', '70');
    }, tok);
    await p.goto(BASE + '/home', { waitUntil: 'domcontentloaded' });
    await p.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 25000 });
    await p.evaluate(() => {
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const s = document.createElement('style');
        s.textContent =
            '#workspace-gate-root{display:none!important;pointer-events:none!important}';
        document.head.appendChild(s);
    });
    await p.waitForTimeout(2500);
    for (let i = 0; i < 4; i++) {
        await p.evaluate(() => window.routeTo('integrations'));
        const ok = await p
            .waitForFunction(
                () => document.getElementById('page-integrations')?.classList.contains('active'),
                { timeout: 4000 }
            )
            .then(() => 1)
            .catch(() => 0);
        if (ok) break;
    }
    // 切到「推送异常」tab(页面内 .click() 触发 document 监听 → 面板加 active),等面板真显示
    for (let i = 0; i < 5; i++) {
        await p.evaluate(() =>
            document.querySelector('#page-integrations [data-int-top-tab="push-exc"]')?.click()
        );
        const ok = await p
            .waitForFunction(
                () =>
                    document
                        .querySelector('.int-top-panel[data-int-top-panel="push-exc"]')
                        ?.classList.contains('active'),
                { timeout: 2000 }
            )
            .then(() => 1)
            .catch(() => 0);
        if (ok) break;
    }
    await p.evaluate(async () => {
        if (window.loadErpExceptions) await window.loadErpExceptions();
    });
    await p.waitForTimeout(2500);

    let pass = 0,
        fail = 0;
    const chk = (k, c) => {
        c ? pass++ : fail++;
        console.log((c ? 'PASS' : 'FAIL').padEnd(5), k);
    };

    // 1) 绑主体卡渲染(data-bindfix-submit 仅绑主体卡有)
    const card = await p.evaluate(() => {
        const sub = document.querySelector('[data-bindfix-submit]');
        if (!sub) return null;
        const id = sub.getAttribute('data-bindfix-submit');
        const cardEl = document.querySelector(`.erp-exc-card[data-erpexc-id="${CSS.escape(id)}"]`);
        const openBtn = cardEl?.querySelector('[data-erpexc-acctfix]');
        return { id, openLabel: openBtn?.textContent?.trim() || '', hasOpen: !!openBtn };
    });
    chk('绑主体卡渲染(有 data-bindfix-submit)', !!card);
    if (!card) {
        console.log(`\n结果: ${pass} PASS · ${fail} FAIL`);
        await b.close();
        process.exit(1);
    }
    console.log('  卡 id=', card.id, '· 主操作按钮文案=', JSON.stringify(card.openLabel));
    chk('卡有展开按钮(绑主体主操作)', card.hasOpen);

    // 2) 点开面板 → 可见 + 下拉填充账套主体
    await p.click(`[data-erpexc-acctfix="${card.id}"]`);
    await p.waitForTimeout(600);
    const panel = await p.evaluate((id) => {
        const pl = document.querySelector(`[data-acctfix-panel="${CSS.escape(id)}"]`);
        if (!pl) return { none: true };
        const cs = getComputedStyle(pl);
        const sel = pl.querySelector('[data-bindfix-select]');
        const opts = sel
            ? Array.from(sel.options)
                  .map((o) => o.value)
                  .filter(Boolean)
            : [];
        return {
            hidden: pl.hidden,
            display: cs.display,
            visible: cs.display !== 'none' && !pl.hidden,
            hasSelect: !!sel,
            optCount: opts.length,
            opts,
        };
    }, card.id);
    console.log('  面板=', JSON.stringify(panel));
    chk('面板点开后可见(getComputedStyle)', panel.visible === true);
    chk('下拉是账套主体 select', panel.hasSelect === true);
    chk('下拉填充 ≥1 个主体', panel.optCount >= 1);

    // 3) 选主体 + 提交 → POST express-bind-subject 带 workspace_client_id
    if (panel.optCount >= 1) {
        await p.selectOption(
            `[data-acctfix-panel="${card.id}"] [data-bindfix-select]`,
            panel.opts[panel.opts.length - 1]
        );
        await p.click(`[data-bindfix-submit="${card.id}"]`);
        await p.waitForTimeout(3000);
        chk('提交触发 POST express-bind-subject', bindReqs.length >= 1);
        if (bindReqs.length) {
            console.log('  请求=', JSON.stringify(bindReqs[0]));
            let body = {};
            try {
                body = JSON.parse(bindReqs[0].body || '{}');
            } catch (_) {}
            chk('POST method=POST', bindReqs[0].method === 'POST');
            chk(
                'body 带 workspace_client_id(数字)',
                typeof body.workspace_client_id === 'number' && body.workspace_client_id > 0
            );
        }
    }

    await p
        .screenshot({ path: path.join(OUT, 'express-bind-panel.png'), fullPage: true })
        .catch(() => {});
    console.log(`\n结果: ${pass} PASS · ${fail} FAIL`);
    await b.close();
    process.exit(fail ? 1 : 0);
})();
