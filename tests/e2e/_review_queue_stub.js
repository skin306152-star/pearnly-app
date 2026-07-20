// 审核收件箱(#/pool)的本地 stub 引导 —— 给「一张异常票在队列里长什么样」这类验收共用。
// ============================================================
// 桩响应形状逐字段对齐后端源码(review.review_queue() / review_feed.enrich() /
// verdict.hint()),真 DOM / 真 CSS / 真渲染,只桩网络层。_mc1b2_review_inbox_verify.spec.js
// 那份 fixture 覆盖三分区与批量路径,本模块只管「单张异常票」这条最小切面,不与之合并。
/* global window */
const path = require('path');
const localServer = require('./_local_static_server');

const CLIENT = {
    workspace_client_id: 1,
    client_name: 'Sister Makeup',
    client_tax_id: '0105555167627',
};

function fakeToken(sub) {
    const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
    return (
        b64({ alg: 'none' }) +
        '.' +
        b64({ sub: sub || 'u-stub', email: 'reviewer@pearnly.test' }) +
        '.sig'
    );
}

// 一张 flagged 票 → review-queue 的完整响应。severity/count 取自该票的 verdict_hint,
// 免得夹具里两处严重度各写一份、悄悄劈叉。
function queueFixture(item, orderId) {
    const severity = (item.verdict_hint && item.verdict_hint.severity) || 'crit';
    return {
        period: null,
        clients: [
            Object.assign({}, CLIENT, {
                pool_pending: 0,
                orders: [
                    {
                        work_order_id: orderId,
                        workspace_client_id: CLIENT.workspace_client_id,
                        client_name: CLIENT.client_name,
                        client_tax_id: CLIENT.client_tax_id,
                        period: item.period,
                        status: 'stuck',
                        current_step: 'reconcile',
                        updated_at: '2026-07-20T10:00:00+07:00',
                        next_due_efiling: '2569-06-15',
                        next_due_paper: '2569-06-07',
                        pool_pending: 0,
                        is_rework: false,
                        flagged_groups: [
                            { flag_reason: item.flag_reason, severity: severity, count: 1 },
                        ],
                        flagged_total: 1,
                        top_severity: severity,
                    },
                ],
            }),
        ],
        flagged_items: [item],
        counts: { clients: 1, orders: 1, flagged: 1 },
    };
}

async function wireApi(page, item, orderId) {
    await page.route('**/api/**', (route) => {
        const p = new URL(route.request().url()).pathname;
        if (p === '/api/ai/session') return route.fulfill({ json: { ok: true } });
        if (p === '/api/me')
            return route.fulfill({ json: { id: 'u-stub', username: 'reviewer', role: 'owner' } });
        if (p === '/api/workorder/orders')
            return route.fulfill({ json: { orders: [], count: 0, limit: 1, offset: 0 } });
        if (p === '/api/workorder/review-queue')
            return route.fulfill({ json: queueFixture(item, orderId) });
        if (p === '/api/ai/client-pool') return route.fulfill({ json: { groups: [] } });
        return route.fulfill({ status: 404, json: { detail: 'not_stubbed:' + p } });
    });
}

async function gotoPool(page, pageUrl, lang) {
    await page.addInitScript(
        ({ token, lang }) => {
            window.localStorage.setItem('mrpilot_token_ai', token);
            window.localStorage.setItem('mrpilot_lang', lang || 'zh');
        },
        { token: fakeToken(), lang }
    );
    await page.goto(pageUrl);
    await page.waitForFunction(() => !!window.AI && !!window.AI.router);
    await page.evaluate(() => {
        window.location.hash = '#/pool';
    });
    await page.waitForSelector('#v-pool.on', { timeout: 15000 });
    await page.waitForSelector('.riq-item', { timeout: 10000 });
}

// port → { PAGE, ART(artifacts 子目录), start/stop, boot(page, lang) }
function harness(port, artifactDir, item, orderId) {
    const base = `http://127.0.0.1:${port}`;
    return {
        PAGE: base + '/static/dist/ai.html',
        ART: path.join(__dirname, '_artifacts', artifactDir),
        start: () => localServer.start(port),
        stop: (server) => localServer.stop(server),
        boot: async function (page, lang) {
            await wireApi(page, item, orderId);
            await gotoPool(page, this.PAGE, lang);
        },
    };
}

module.exports = { harness, queueFixture, fakeToken };
