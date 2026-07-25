// 使用教程配图批量生成器(入口)。
// 图不手截:界面一改重跑本脚本即全部换新,教程里的图永远和线上一致(手截的图三周后就是假的)。
// 产物 static/guide/shots/*.png → build-home-css.mjs 复制进 static/dist/guide-shots/ 随 dist 部署。
// 跑法: node scripts/_guide_shots.cjs [shotId...]  不带参数=全截
// 分工:_guide_shots_env(服务器/假后端/启动态)· _guide_shots_actions(前置动作)
//      · _guide_shots_list(图清单)· _guide_shots_data(假接口数据)
/* eslint-disable no-undef */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { OUT, VIEWPORT, LANGS, BOOTS, serve, prepareInvoicePng } = require('./_guide_shots_env.cjs');
const { unionClip } = require('./_guide_shots_actions.cjs');
const { SHOTS } = require('./_guide_shots_list.cjs');

async function oneShot(page, s, lang) {
    try {
        // 比一屏还高的区块(复核屏)要先把窗口调够高:否则 Playwright 边滚边拼,
        // sticky 的顶栏会被合成到区块顶部,把它自己的操作条盖掉。
        if (s.viewport) await page.setViewportSize(s.viewport);
        if (s.prep) await s.prep(page);
        let target = null;
        for (const sel of s.sel.split(',').map((x) => x.trim())) {
            target = await page.$(sel);
            if (target) break;
        }
        if (!target) {
            console.log('MISS ', `${s.id}.${lang}`, '· 选择器没命中:', s.sel);
            return false;
        }
        const out = path.join(OUT, `${s.id}.${lang}.png`);
        const clip = s.clip ? await unionClip(page, s.clip) : null;
        if (clip) await page.screenshot({ path: out, clip });
        else await target.screenshot({ path: out });
        if (s.after) await s.after(page);
        console.log('OK   ', `${s.id}.${lang}`);
        return true;
    } catch (e) {
        console.log('FAIL ', `${s.id}.${lang}`, String(e).slice(0, 140));
        return false;
    } finally {
        if (s.viewport) await page.setViewportSize(VIEWPORT);
    }
}

async function run() {
    const only = process.argv.slice(2);
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const ctx = await browser.newContext({
        viewport: VIEWPORT,
        deviceScaleFactor: 2, // 2 倍图经得起放大;页面侧按 naturalWidth/2 还原显示尺寸
    });
    await prepareInvoicePng(ctx);

    let ok = 0;
    let miss = 0;
    for (const lang of LANGS) {
        for (const scene of Object.keys(BOOTS)) {
            const list = SHOTS.filter(
                (s) => (s.scene || 'main') === scene && (!only.length || only.includes(s.id))
            );
            if (!list.length) continue;
            const page = await BOOTS[scene](ctx, lang);
            for (const s of list) {
                const r = await oneShot(page, s, lang);
                if (r) ok++;
                else miss++;
            }
            await page.close();
        }
    }

    await browser.close();
    srv.close();
    console.log(`\n${ok} 张已生成, ${miss} 张未取到 → ${OUT}`);
    process.exit(miss ? 1 : 0);
}

run().catch((e) => {
    console.error(e);
    process.exit(1);
});
