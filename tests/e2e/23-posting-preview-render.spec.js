// Pearnly E2E · 23 步4 推送前预览(记账画像 gate)四态真浏览器渲染 + 截图为证
// ============================================================
// 纯渲染验收(不需登录/baseURL):加载真 static/dist/home.css,渲染四态 gate HTML,
// 抓 getComputedStyle 断言视觉(ok 蓝底 / escalate 琥珀左框 3px / confirm 双按钮 / decide 例外行),
// 截图落 _artifacts/。全流程数据驱动(真 companion 目录 → preview)属真客户验收门,见交接。
// ============================================================
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const CSS = path.resolve(__dirname, '../../static/dist/home.css');
const GATES = `<div class="dmsx" style="padding:24px;max-width:520px;display:flex;flex-direction:column;gap:16px;background:var(--bg,#f6f5fb)">
  <div class="dx-pp"><div class="dx-pp-ok">3 项复用现有 · 2 项新建</div></div>
  <div class="dx-pp"><div class="dx-pp-warn">这家按永续库存记账 · 商品行需人工录入 · 本批留人工</div></div>
  <div class="dx-pp"><div class="dx-pp-confirm"><p>这家客户在 Express 里管库存吗？</p><div class="dx-pp-btns"><button class="btn">不管 · 自动记账</button><button class="btn">管库存 · 逐单人工</button></div></div></div>
  <div class="dx-pp"><div class="dx-pp-decide"><p>以下商品需你确认落点：</p><div class="dx-pp-row"><b>น้ำแข็งหลอด</b><span>已在库存目录 · 默认另建非库存</span></div><div class="dx-pp-note">默认按 firm-safe 另建独立非库存档</div></div></div>
</div>`;

test('步4 推送前预览四态真浏览器渲染 + 截图为证', async ({ page }) => {
    await page.setContent(
        `<!doctype html><html><head><meta charset="utf-8"></head><body>${GATES}</body></html>`
    );
    await page.addStyleTag({ path: CSS });
    await page.waitForTimeout(150);

    // gate=ok:蓝底(非透明)
    const okBg = await page.$eval('.dx-pp-ok', (e) => getComputedStyle(e).backgroundColor);
    expect(okBg).not.toBe('rgba(0, 0, 0, 0)');
    // gate=escalate:琥珀左边框 3px(#f59e0b)
    expect(await page.$eval('.dx-pp-warn', (e) => getComputedStyle(e).borderLeftColor)).toBe(
        'rgb(245, 158, 11)'
    );
    expect(await page.$eval('.dx-pp-warn', (e) => getComputedStyle(e).borderLeftWidth)).toBe('3px');
    // gate=confirm_profile:两按钮可见
    await expect(page.locator('.dx-pp-confirm .btn')).toHaveCount(2);
    await expect(page.locator('.dx-pp-confirm .btn').first()).toBeVisible();
    // gate=decide_items:例外行可见
    await expect(page.locator('.dx-pp-row')).toBeVisible();

    const outDir = path.resolve(__dirname, '_artifacts');
    fs.mkdirSync(outDir, { recursive: true });
    await page.screenshot({
        path: path.join(outDir, 'posting-preview-gates.png'),
        fullPage: true,
    });
});
