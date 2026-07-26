// 使用教程真浏览器验收:侧栏父子导航、三层面包屑、配图真的加载出来、中泰跟随全站语言。
// 图用 naturalWidth 判,不看 src 是否写对 —— 路径写对但 404 的坑就是这么漏过去的。
// 跑法: node scripts/_guide_page_verify.cjs → tests/visual/_shot/guide-*.png
/* eslint-disable no-undef */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { serveStatic, chk, summary, crumbs, bootHome } = require('./_verify_shared.cjs');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8799;

const boot = (ctx, lang, viewport) => bootHome(ctx, { port: PORT, lang, viewport });

const visible = (page, sel) =>
    page.evaluate((s) => {
        const el = document.querySelector(s);
        if (!el) return false;
        let n = el;
        while (n && n !== document.body) {
            if (getComputedStyle(n).display === 'none') return false;
            n = n.parentElement;
        }
        return true;
    }, sel);

async function run() {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serveStatic(PORT);
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ deviceScaleFactor: 2 });

    const { page, errs } = await boot(ctx, 'th', { width: 1440, height: 980 });

    // 入口必须「点得到」,不是「DOM 里有」:会计版白名单漏加就会被 display:none。
    chk('侧栏「使用教程」父栏可见', await visible(page, '[data-collapsible="guide"]'));

    // 侧栏只到手册这一层:使用教程以后还要挂别的手册,篇章不占侧栏。
    const subs = await page.locator('[data-collapsible="guide"] .nav-sub-item').count();
    chk(`子栏只有手册这一层(实得 ${subs})`, subs === 1);
    chk('「Express 推送手册」子栏可见', await visible(page, '[data-gd-book="express"]'));
    chk(
        '默认未折叠',
        !(await page.evaluate(() =>
            document.querySelector('[data-collapsible="guide"]').classList.contains('collapsed')
        ))
    );
    await page.screenshot({ path: path.join(OUT, 'guide-nav-expanded.png') });

    // 收起/展开这一下也得真能用
    await page.click('[data-toggle-group="guide"]');
    await page.waitForTimeout(400);
    chk(
        '点父栏可收起',
        await page.evaluate(() =>
            document.querySelector('[data-collapsible="guide"]').classList.contains('collapsed')
        )
    );
    await page.click('[data-toggle-group="guide"]');
    await page.waitForTimeout(400);
    chk('再点可展开', await visible(page, '[data-gd-book="express"]'));

    // 点手册 → 先看七篇总览,此时不该有面包屑
    await page.click('[data-gd-book="express"]');
    await page.waitForSelector('#page-guide .gd-grid', { timeout: 8000 });
    chk('手册首页列出 7 篇卡片', (await page.locator('.gd-card').count()) === 7);
    chk('手册首页不起面包屑', (await page.locator('.gd-crumb').count()) === 0);
    await page.screenshot({ path: path.join(OUT, 'guide-root.png') });

    // 点某一篇 → 章节列表;点其中一章才进正文,此时才起面包屑
    await page.click('.gd-card[data-gd-sec="daily"]');
    await page.waitForSelector('#page-guide .gd-list', { timeout: 8000 });
    await page.click('.gd-item[data-gd-ch="push-upload-batch"]');
    await page.waitForSelector('#page-guide .gd-steps', { timeout: 8000 });
    let c = await crumbs(page);
    console.log('  面包屑:', c.join(' / '));
    chk('面包屑三级(手册 / 篇 / 章节)', c.length === 3);
    chk('面包屑首级是手册名', /Express/.test(c[0] || ''));
    chk('末级是当前章节', /อัปโหลด/.test(c[2] || ''));

    const steps = await page.locator('.gd-step').count();
    chk(`步骤全渲染(实得 ${steps} 步)`, steps === 6);
    chk('提示块三条', (await page.locator('.gd-note').count()) === 3);
    chk('有一条警示级(计费那条)', (await page.locator('.gd-note.is-warn').count()) === 1);
    chk('页内不再有常驻目录栏', (await page.locator('.gd-toc').count()) === 0);

    await page.waitForTimeout(1200);
    // 指纹与文件名分开看:文件名决定配的是哪套语言的界面图,?v 决定重拍后浏览器/CDN 认不认新图。
    const imgs = await page.evaluate(() =>
        [...document.querySelectorAll('.gd-fig img')].map((i) => {
            const u = new URL(i.getAttribute('src'), location.href);
            return { file: u.pathname, v: u.searchParams.get('v'), w: i.naturalWidth };
        })
    );
    console.log('  配图:', imgs.map((i) => `${i.file.split('/').pop()}=${i.w}px`).join(' '));
    chk(`配图 5 张(实得 ${imgs.length})`, imgs.length === 5);
    chk('每张都真的加载出来(naturalWidth>0)', imgs.length > 0 && imgs.every((i) => i.w > 0));
    chk(
        '泰文正文配的是泰文界面图',
        imgs.every((i) => i.file.endsWith('.th.png'))
    );

    // 图名固定(daily-02-review.zh.png),界面改了重拍必然同名 —— URL 上没指纹的话浏览器和 CDN
    // 一直发旧图,"重拍即换新"这条承诺在缓存层就断了。指纹必须就是页面上 main.js 的那个:
    // 另造一套版本号迟早漂成只 bump 一边。这条防的是以后有人改渲染时又把指纹丢了。
    const pageV = await page.evaluate(() => {
        const el = document.querySelector('script[src*="/dist/main.js"]');
        const m = el && el.src.match(/[?&]v=([^&]+)/);
        return m ? m[1] : '';
    });
    console.log('  页面指纹:', pageV || '(缺)');
    chk('页面 main.js 带指纹', !!pageV);
    chk(
        `每张配图都带 ?v=${pageV}(与正文 JSON 同一指纹)`,
        imgs.length > 0 && !!pageV && imgs.every((i) => i.v === pageV)
    );
    await page.screenshot({ path: path.join(OUT, 'guide-th-desktop.png'), fullPage: true });

    // 面包屑回退:中级 → 该篇章节列表
    await page.click('[data-gd-sec-up]');
    await page.waitForSelector('.gd-list', { timeout: 5000 });
    c = await crumbs(page);
    chk('回退后面包屑两级', c.length === 2);
    const items = await page.locator('.gd-item[data-gd-ch]').count();
    chk(`章节列表列出该篇全部章(实得 ${items})`, items === 27);
    // 全篇写完时不该再出「编写中」占位(planned - 实际 = 0)。
    chk('已写完的篇不留占位', (await page.locator('.gd-item.is-todo').count()) === 0);
    await page.screenshot({ path: path.join(OUT, 'guide-section-list.png') });

    // 面包屑回退:首级 → 七篇总览(回到首页面包屑消失)
    await page.click('[data-gd-root]');
    await page.waitForSelector('.gd-grid', { timeout: 5000 });
    chk('回首页后面包屑消失', (await page.locator('.gd-crumb').count()) === 0);

    // 切中文:正文与配图同步换
    await page.click('.gd-card[data-gd-sec="daily"]');
    await page.waitForSelector('.gd-list', { timeout: 5000 });
    await page.click('.gd-item[data-gd-ch="push-upload-batch"]');
    await page.waitForSelector('.gd-steps', { timeout: 5000 });
    await page.evaluate(() => window.applyLang && window.applyLang('zh'));
    await page.waitForTimeout(800);
    const h1zh = (await page.locator('.gd-h1').innerText()).trim();
    console.log('  中文标题:', h1zh);
    chk('切中文后正文变中文', h1zh === '上传本批票据');
    await page
        .waitForFunction(
            () =>
                [...document.querySelectorAll('.gd-fig img')].every((i) => i.complete) &&
                document.querySelectorAll('.gd-fig img').length === 5,
            { timeout: 8000 }
        )
        .catch(() => {});
    const zhImgs = await page.evaluate(() =>
        [...document.querySelectorAll('.gd-fig img')].map((i) => {
            const u = new URL(i.getAttribute('src'), location.href);
            return { file: u.pathname, v: u.searchParams.get('v'), w: i.naturalWidth };
        })
    );
    chk(
        '配图同步换成中文界面图',
        zhImgs.length === 5 && zhImgs.every((i) => i.file.endsWith('.zh.png'))
    );
    // 带上 ?v 后路径写错就是 404,只看 URL 变了不算数 —— 仍要真的解码出像素。
    chk(
        '中文配图带同一指纹且真的加载出来',
        zhImgs.every((i) => i.v === pageV && i.w > 0)
    );
    await page.screenshot({ path: path.join(OUT, 'guide-zh-desktop.png'), fullPage: true });

    // 深链:报错卡等处直达某一章
    await page.evaluate(() => window.routeTo('dashboard'));
    await page.waitForTimeout(300);
    await page.evaluate(() => window.openGuide('push-upload-batch'));
    await page.waitForSelector('.gd-steps', { timeout: 5000 });
    chk('openGuide 深链直达该章', (await crumbs(page)).length === 3);

    chk('无页面 JS 错误', errs.length === 0);
    if (errs.length) console.log('  pageerror:', errs.slice(0, 3));
    await page.close();

    // 集成已并入主数据折叠组,底部不再单列
    const { page: m0 } = await boot(ctx, 'th', { width: 1440, height: 980 });
    chk(
        '集成在主数据组内',
        await m0.evaluate(
            () => !!document.querySelector('[data-collapsible="master"] #nav-integrations')
        )
    );
    chk(
        '主数据可折叠',
        await m0.evaluate(() => !!document.querySelector('[data-toggle-group="master"]'))
    );
    chk(
        '侧栏底部不再单列集成',
        await m0.evaluate(() => !document.querySelector('.sidebar-bottom #nav-integrations'))
    );
    await m0.screenshot({ path: path.join(OUT, 'guide-nav-master.png') });
    await m0.close();

    // 手机端
    const { page: m } = await boot(ctx, 'th', { width: 390, height: 844 });
    await m.evaluate(() => window.openGuide('push-upload-batch'));
    await m.waitForSelector('.gd-steps', { timeout: 8000 });
    const noHScroll = await m.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth + 1
    );
    chk('手机端不横向滚动', noHScroll);
    await m.screenshot({ path: path.join(OUT, 'guide-th-mobile.png'), fullPage: true });

    await browser.close();
    srv.close();
    process.exit(summary());
}

run().catch((e) => {
    console.error(e);
    process.exit(1);
});
