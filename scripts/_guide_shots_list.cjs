// 教程配图清单。每张图 = 一个选择器 + 可选的前置动作。element 截图而非整页:教程里要的是那一块。
// scene 决定这张图在哪种启动态下拍(缺省 main = 已进系统的录入工作台);同 scene 的图共用一次
// 启动、按数组顺序连拍。复核流程与列表页各自要干净的起点,故各占一个 scene。
/* eslint-disable no-undef */
const {
    goRoute,
    selectHistoryRows,
    openExportModal,
    closeExportModal,
    expressCard,
    enterReview,
} = require('./_guide_shots_actions.cjs');

const SHOTS = [
    {
        id: 'upload-01-nav',
        sel: '#sidebar .nav-group, #sidebar',
        prep: async (page) => {
            // 折叠组默认可能是收起的,展开后才拍得到四个入口。
            await page.evaluate(() => {
                document
                    .querySelectorAll('[data-collapsible="firm"] .nav-group-head')
                    .forEach((h) => {
                        const g = h.closest('[data-collapsible]');
                        if (g && !g.classList.contains('open')) h.click();
                    });
            });
            await page.waitForTimeout(400);
        },
    },
    { id: 'upload-02-task', sel: '.dx-task' },
    { id: 'upload-03-dropzone', sel: '#dx-inv-drop' },
    {
        id: 'upload-04-queue',
        sel: '.dx-qlist',
        prep: async (page) => {
            // 文件体积要像真的:1 字节会渲染成「0.0 MB」,会计看图时会以为文件是空的。
            await page.setInputFiles('#dx-inv-file', [
                // 文件名不带语种:中泰两套图共用,也更像会计真实的扫描件命名。
                {
                    name: 'INV-2569-07-01.pdf',
                    mimeType: 'application/pdf',
                    buffer: Buffer.alloc(Math.round(1.2 * 1048576)),
                },
                {
                    name: 'RECEIPT-2569-07-02.jpg',
                    mimeType: 'image/jpeg',
                    buffer: Buffer.alloc(Math.round(0.8 * 1048576)),
                },
            ]);
            await page.waitForTimeout(700);
        },
    },
    { id: 'upload-05-start', sel: '.dx-bar' },

    // ── 核对与回导 ──────────────────────────────────────────────
    {
        id: 'review-01-batchbar',
        // 批量条在表头之上,单截条本身看不出「勾了哪几行」→ 连表头与已勾的行一起拍。
        sel: '.history-table-wrap',
        prep: (page) => selectHistoryRows(page, 2),
    },
    {
        // 中性 id:「核对与回导」和「维护与安全」两篇讲的是同一个导出模板弹窗,
        // 各留一条同体定义就是白截一遍(×2 语言),两篇的 shot 都指这一张。
        id: 'export-template-modal',
        sel: '.report-modal',
        prep: openExportModal,
        after: closeExportModal,
    },
    {
        id: 'review-03-declare',
        sel: '.dx-side',
        prep: async (page) => {
            await goRoute(page, 'dms-intake', '.dx-side [data-iv-posting]');
            // 两组声明都不预选,图要拍的正是「选完之后」的样子。
            await page.click('[data-iv-dir="purchase"]');
            await page.click('[data-iv-posting="stock"]');
            await page.waitForTimeout(300);
        },
    },

    // ── 维护与安全 ──────────────────────────────────────────────
    { id: 'maintain-01-erp-card', sel: '#dx-erp-cards [data-erp="express"]', prep: expressCard },
    {
        id: 'maintain-02-disable-confirm',
        sel: '#pearnly-confirm-modal .modal',
        prep: async (page) => {
            await expressCard(page);
            await page.click('[data-erp="express"] [data-erp-toggle]');
            await page.waitForSelector('#pearnly-confirm-modal .modal', { timeout: 5000 });
            await page.waitForTimeout(300);
        },
        // 截完必须撤销,否则端点真被停用、后面的卡片图变成「已停用」。
        after: (page) => page.click('#pearnly-confirm-cancel'),
    },
    {
        id: 'maintain-03-key-masked',
        sel: '#exp-step2',
        prep: async (page) => {
            await expressCard(page);
            await page.click('[data-erp="express"] [data-erp-config]');
            await page.waitForSelector('#exp-step2 #exp-codebox', { timeout: 8000 });
            await page.waitForTimeout(400);
        },
        after: (page) => page.click('#exp-close'),
    },
    {
        id: 'maintain-04-batch-bar',
        sel: '#history-batch-bar',
        prep: (page) => selectHistoryRows(page, 3),
    },
    {
        id: 'maintain-06-drawer-file',
        sel: '.hd-root',
        clip: ['.hd-summary', '.hd-tabs', '.hd-panel.active'],
        prep: async (page) => {
            await goRoute(page, 'history', '#history-tbody .history-row');
            await page.click('.history-row .history-cell-file');
            await page.waitForSelector('.hd-tabs [data-hd-view="file"]', { timeout: 10000 });
            await page.click('.hd-tabs [data-hd-view="file"]');
            await page.waitForTimeout(400);
        },
        after: (page) => page.evaluate(() => window.closeDrawer && window.closeDrawer()),
    },

    // ── 推不进去怎么办 ──────────────────────────────────────────
    {
        id: 'stuck-01-nav',
        sel: '#sidebar [data-collapsible="firm"]',
        prep: async (page) => {
            // 进「推送日志」路由本身就展开所在折叠组并点亮该项 —— 图要的正是那个高亮态。
            await goRoute(page, 'push-logs', '#erp-logs-filters');
            await page.waitForTimeout(300);
        },
    },
    {
        id: 'stuck-02-filters',
        sel: '#erp-logs-filters',
        prep: (page) => goRoute(page, 'push-logs', '#erp-logs-list .erp-log-card'),
    },
    {
        id: 'stuck-03-exceptions',
        sel: '#page-exceptions',
        prep: (page) => goRoute(page, 'exceptions', '#exc-list .exc-row'),
    },

    // ── 总览篇 · 登录页(landing.js 独立渲染)──────────────────────
    { id: 'overview-01-login', scene: 'login', sel: '.auth-shell' },
    { id: 'overview-02-support', scene: 'login', sel: '.support-card' },

    // ── 总览篇 · 选账套硬门(不拆门的启动变体)────────────────────
    {
        id: 'overview-03-gate',
        scene: 'gate',
        // 门是撑满整屏的,卡片只占上半截 —— 直接截整个 root 会带一大片空白。
        sel: '#workspace-gate-root',
        clip: ['.onb-top', '.wsg-new'],
    },

    // ── 总览篇 / 概念篇 · 录入工作台第 ① 步 ───────────────────────
    { id: 'overview-05-sidebar', scene: 'wb', sel: '#sidebar' },
    { id: 'overview-06-workbench', scene: 'wb', sel: '.dx-task' },
    { id: 'overview-07-declare', scene: 'wb', sel: '.dx-side' },
    { id: 'daily-01-direction', scene: 'wb', sel: '.dx-side-box:nth-of-type(1)' },
    { id: 'concept-01-direction-cards', scene: 'wb', sel: '.dx-side-box:nth-of-type(1)' },
    { id: 'concept-02-posting-cards', scene: 'wb', sel: '.dx-side-box:nth-of-type(2)' },
    {
        id: 'concept-03-workspace-switcher',
        scene: 'wb',
        // 下拉是绝对定位的浮层,不算在切换器自身的盒子里 —— 两块一起 clip 才拍得全。
        sel: '#workspace-switcher-root',
        clip: ['#workspace-switcher-root .wsw', '.orgsw-pop'],
        prep: async (page) => {
            await page.click('#ws-ctrl-btn');
            await page.waitForSelector('.orgsw-pop .orgsw-item', { timeout: 8000 });
            await page.waitForTimeout(300);
        },
        after: (page) => page.evaluate(() => document.getElementById('orgsw-pop')?.remove()),
    },
    {
        id: 'overview-04-cmdk',
        scene: 'wb',
        sel: '.cmdk',
        prep: async (page) => {
            await page.evaluate(() => window.openCmdk());
            await page.waitForTimeout(400);
            // 四行语言项在「操作」段、列表最底下 —— 滚到底才四行齐全(这张图要的就是那四行,
            // 顶上「跳转」标题被裁掉一线是可以接受的代价)。
            await page.evaluate(() => {
                const b = document.getElementById('cmdk-body');
                if (b) b.scrollTop = b.scrollHeight;
            });
            await page.waitForTimeout(300);
        },
        after: (page) => page.evaluate(() => window.closeCmdk()),
    },
    {
        id: 'daily-11-summarytask',
        scene: 'wb',
        sel: '.dx-wrap',
        clip: ['.dx-task', '.dx-stepper'],
        prep: async (page) => {
            await page.click('[data-task="summary_batch"]');
            await page.waitForTimeout(600);
        },
    },

    // ── 日常推送篇 · 第 ③ 步复核 + 第 ④ 步输出 ────────────────────
    {
        id: 'daily-02-review',
        scene: 'review',
        sel: '#dx-s-inv-review',
        viewport: { width: 1440, height: 2600 },
        prep: enterReview,
    },
    {
        id: 'daily-03-corefields',
        scene: 'review',
        sel: '.dx-acc-item.open .dx-inv-grp .dx-review-grid',
    },
    {
        id: 'daily-04-confirm-all',
        scene: 'review',
        // 图注要的是「操作条 + 状态标记」两样:先收起手风琴,两行文件的状态药丸才和操作条同框。
        sel: '.dx-rv-bar',
        clip: ['.dx-rv-bar', '.dx-acc'],
        prep: async (page) => {
            await page.click('#dx-inv-collapse-all');
            await page.waitForTimeout(400);
        },
    },
    {
        id: 'daily-05-output',
        scene: 'review',
        sel: '#dx-s-inv-submit',
        clip: ['#dx-s-inv-submit .dx-panel', '#dx-s-inv-submit .dx-scan'],
        prep: async (page) => {
            await page.click('#dx-inv-rev-next');
            await page.waitForSelector('#dx-s-inv-submit .dx-ogrid', { timeout: 10000 });
            await page.waitForTimeout(500);
        },
    },
    {
        id: 'daily-06-erptarget',
        scene: 'review',
        sel: '.dx-erps',
        prep: async (page) => {
            await page.click('[data-iv-out="erp"]');
            await page.waitForSelector('.dx-erps .dx-erp', { timeout: 10000 });
            await page.waitForTimeout(400);
        },
    },
    {
        id: 'daily-07-template',
        scene: 'review',
        sel: '.dx-tpl-row',
        prep: async (page) => {
            await page.click('[data-iv-out="excel"]');
            await page.waitForSelector('#dx-inv-tpl', { timeout: 10000 });
            await page.waitForTimeout(400);
        },
    },

    // ── 日常推送篇 / 总览篇 · 列表页与详情抽屉 ─────────────────────
    {
        id: 'daily-08-pushlogs',
        scene: 'pages',
        sel: '#erp-logs-section',
        prep: (page) => goRoute(page, 'push-logs', '#erp-logs-list .erp-log-card'),
    },
    {
        id: 'daily-09-history',
        scene: 'pages',
        sel: '#page-history .wrap',
        clip: ['#history-summary', '.history-filters'],
        prep: (page) => goRoute(page, 'history', '#history-tbody .history-row'),
    },
    {
        id: 'daily-10-drawertabs',
        scene: 'pages',
        // 光一条页签带太空:连汇总条一起拍,读者才知道这四个页签长在抽屉的什么位置。
        sel: '.hd-tabs',
        clip: ['.hd-summary', '.hd-tabs'],
        prep: async (page) => {
            await page.click('.history-row .history-cell-file');
            await page.waitForSelector('.hd-tabs .hd-tab', { timeout: 10000 });
            await page.waitForTimeout(600);
        },
        after: (page) => page.evaluate(() => window.closeDrawer && window.closeDrawer()),
    },
    {
        id: 'overview-09-integrations',
        scene: 'pages',
        sel: '#page-integrations .card',
        prep: (page) => goRoute(page, 'integrations', '#page-integrations .integration-row'),
    },
    {
        id: 'overview-08-balance',
        scene: 'pages',
        sel: '#dash-kpi-balance-card',
        prep: (page) => goRoute(page, 'dashboard', '#dash-kpi-balance-card'),
    },
];

module.exports = { SHOTS };
