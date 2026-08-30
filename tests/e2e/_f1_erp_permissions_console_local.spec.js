const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8990;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(__dirname, '_artifacts', 'f1-erp-permissions');
fs.mkdirSync(OUT, { recursive: true });

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT, '/static/dist/console.html');
});

test.afterAll(() => localServer.stop(server));

test('custom-role wizard exposes the four ERP permissions without enabling owner-only manage', async ({
    page,
}) => {
    await page.addInitScript(() => {
        localStorage.clear();
        localStorage.setItem('mrpilot_token', 'console-e2e-token');
        localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.route('**/api/**', (route) => {
        const pathname = new URL(route.request().url()).pathname;
        const bodies = {
            '/api/me/permissions': {
                data: {
                    role_key: 'owner',
                    permissions: ['team.member.view', 'team.member.edit_role'],
                },
            },
            '/api/team/members': {
                members: [],
                seats_max: 10,
                seats_used: 1,
                seats_pending: 0,
            },
            '/api/team/invitations': { invitations: [] },
            '/api/team/roles': { roles: [] },
            '/api/workspace/clients': { clients: [] },
            '/api/team/roles/custom': { roles: [] },
        };
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(bodies[pathname] || {}),
        });
    });
    await page.goto(`${BASE}/static/dist/console.html`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#appShell')).toBeVisible();
    await page.locator('#navRoles').click();
    await page.locator('#btnNewRole').click();
    await page.locator('#wizNext').click();
    const heading = page.locator('[data-wgrp="erp"]');
    await expect(heading).toContainText('ERP 对接');
    const group = heading.locator('..');
    await heading.click();
    await expect(group.locator('.pgcode')).toHaveCount(4);
    await expect(group).toContainText('查看 ERP 连接');
    await expect(group).toContainText('管理 ERP 连接');
    await expect(group).toContainText('推送到 ERP');
    await expect(group).toContainText('查看推送日志');
    const ownerOnly = group.locator('.pgcode.locked').filter({ hasText: '管理 ERP 连接' });
    await expect(ownerOnly).toHaveCount(1);
    await expect(ownerOnly).not.toHaveAttribute('data-wcode');
    await page.screenshot({
        path: path.join(OUT, 'console-erp-permissions-desktop.png'),
        fullPage: true,
        animations: 'disabled',
    });
});
