// 截图前置动作:把界面点到目标状态(路由、勾选、开弹窗、跑完识别),以及 clip 计算。
// 拆分自 _guide_shots.cjs —— 供 _guide_shots_list.cjs 的 prep/after 复用。
/* eslint-disable no-undef */

// 有些块是撑满高度的容器(抽屉面板),内容只占上半截 —— 整元素截图会带一大片空白。
// clip 拍的仍是真页面,只是把并集之外的空白切掉。
async function unionClip(page, sels) {
    const r = await page.evaluate((ss) => {
        const rects = ss
            .map((s) => document.querySelector(s))
            .filter(Boolean)
            .map((el) => el.getBoundingClientRect());
        if (!rects.length) return null;
        const x = Math.min(...rects.map((v) => v.left));
        const y = Math.min(...rects.map((v) => v.top));
        return {
            x,
            y,
            width: Math.max(...rects.map((v) => v.right)) - x,
            height: Math.max(...rects.map((v) => v.bottom)) - y,
        };
    }, sels);
    if (!r) return null;
    const pad = 12;
    return {
        x: Math.max(0, r.x - pad),
        y: Math.max(0, r.y - pad),
        width: r.width + pad * 2,
        height: r.height + pad * 2,
    };
}

// 路由到目标页并等它把数据渲染完 —— 空壳期截到的是「加载中…」。
async function goRoute(page, route, readySel) {
    await page.evaluate((r) => window.routeTo(r), route);
    if (readySel) await page.waitForSelector(readySel, { timeout: 15000 });
    await page.waitForTimeout(400);
}

// 批量条只有勾了行才浮出来,所以每张「批量条」图都得先真的去点复选框。
async function selectHistoryRows(page, n) {
    await goRoute(page, 'history', '#history-tbody .history-row');
    const boxes = await page.$$('.history-row-check');
    for (let i = 0; i < Math.min(n, boxes.length); i++) {
        if (!(await boxes[i].isChecked())) await boxes[i].click();
    }
    await page.waitForSelector('#history-batch-bar:visible', { timeout: 5000 });
    await page.waitForTimeout(300);
}

// 「导出报表」弹窗走真实路径:勾行 → 批量条下箭头 → 选中「泰国销售明细」(教程两处都指这一项)。
async function openExportModal(page) {
    await selectHistoryRows(page, 2);
    await page.click('#history-batch-export');
    const tpl = '#report-tpl-list input[value="sales_detail_th"]';
    await page.waitForSelector(tpl, { timeout: 10000 });
    await page.check(tpl);
    await page.waitForTimeout(300);
}

async function closeExportModal(page) {
    await page.evaluate(() => document.getElementById('report-modal-cancel')?.click());
    await page.waitForTimeout(200);
}

// 录入工作台底部的 Express 连接卡:等端点状态回来(is-connected)再截,否则拍到「检查连接中」。
async function expressCard(page) {
    await goRoute(page, 'dms-intake', '#dx-erp-cards [data-erp="express"].is-connected');
}

// 第 3 / 4 步的界面只有跑完识别才存在:传两个文件 → 开始 → 假后端回两张票 → 落到复核屏。
async function enterReview(page) {
    const pdf = (n) => ({
        name: `INV-2569-${n}.pdf`,
        mimeType: 'application/pdf',
        buffer: Buffer.from(`%PDF-1.4 demo ${n}`),
    });
    await page.setInputFiles('#dx-inv-file', [pdf('07-01'), pdf('07-02')]);
    await page.waitForTimeout(400);
    await page.click('#dx-inv-start');
    await page.waitForSelector('.dx-acc-item.open .dx-review-grid', { timeout: 20000 });
    await page.waitForTimeout(1500); // 等右侧原图查看器把 page/1.png 拉回来
}

module.exports = {
    unionClip,
    goRoute,
    selectHistoryRows,
    openExportModal,
    closeExportModal,
    expressCard,
    enterReview,
};
