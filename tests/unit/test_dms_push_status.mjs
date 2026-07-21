// 录入工作台步④「本批推送状态」纯函数契约(pushView 状态映射 + pushStatusListHtml 渲染)。
// esbuild 现打包 TS(解析 './x.js'→'./x.ts',与 vite 同款);本地跑:node tests/unit/test_dms_push_status.mjs
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import os from 'node:os';
import fs from 'node:fs';

const ROOT = process.cwd();
const outfile = path.join(os.tmpdir(), `dxp-${process.pid}.mjs`);

const jsToTs = {
    name: 'js-to-ts',
    setup(b) {
        b.onResolve({ filter: /^\.\/.*\.js$/ }, (args) => {
            const ts = path.join(args.resolveDir, args.path.replace(/\.js$/, '.ts'));
            return fs.existsSync(ts) ? { path: ts } : undefined;
        });
    },
};

await build({
    entryPoints: [path.join(ROOT, 'src/home/dms-intake-push-status.ts')],
    bundle: true,
    format: 'esm',
    outfile,
    logLevel: 'silent',
    plugins: [jsToTs],
});
const m = await import(pathToFileURL(outfile).href);
fs.unlinkSync(outfile);

globalThis.window = { _currentLang: 'zh' };
globalThis.localStorage = { getItem: () => null };
// core.esc 委托全局 escapeHtml(生产由 home 提供);测试注入同款以验真转义。
globalThis.escapeHtml = (s) =>
    String(s ?? '').replace(
        /[&<>"']/g,
        (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
    );
const t = (k) =>
    ({
        'erp-logs-filter-ok': '成功',
        'dx-push-pending': '推送中',
        'erp-logs-filter-retrying': '重试中',
        'erp-logs-filter-fail': '失败',
        'erp-exc-retry': '重试推送',
    })[k] || k;

let pass = 0;
const ok = (name, cond) => {
    assert.ok(cond, name);
    pass++;
};

// 折叠态 → 展示态
ok('success→ok', m.pushView({ status: 'success' }) === 'ok');
ok('skipped_dup→ok', m.pushView({ status: 'skipped_dup' }) === 'ok');
ok('pending→pending', m.pushView({ status: 'pending' }) === 'pending');
ok(
    'failed+next_retry→retrying',
    m.pushView({ status: 'failed', next_retry_at: 'x' }) === 'retrying'
);
ok('failed terminal→failed', m.pushView({ status: 'failed', next_retry_at: null }) === 'failed');
ok('unknown→pending(不臆造成功)', m.pushView({ status: 'weird' }) === 'pending');

// 列表渲染
ok('空批→空串', m.pushStatusListHtml([], t) === '');
const html = m.pushStatusListHtml(
    [
        { id: 'a', invoice_no: 'IV-1', status: 'success' },
        {
            id: 'b',
            invoice_no: 'IV-2',
            status: 'failed',
            next_retry_at: null,
            error_friendly: { zh: '缺科目' },
        },
        { id: 'c', invoice_no: 'IV-3', status: 'pending' },
    ],
    t
);
ok('三单都渲染', html.includes('IV-1') && html.includes('IV-2') && html.includes('IV-3'));
ok('失败行带重推按钮(挂 log id)', html.includes('data-dxp-retry="b"'));
ok('成功行无重推', !html.includes('data-dxp-retry="a"'));
ok('失败行显示友好原因', html.includes('缺科目'));
ok(
    '状态类落对',
    /dxp-row ok/.test(html) && /dxp-row failed/.test(html) && /dxp-row pending/.test(html)
);

// XSS:单号转义
const inj = m.pushStatusListHtml([{ id: 'x', invoice_no: '<img src=x>', status: 'success' }], t);
ok('单号 HTML 转义', !inj.includes('<img src=x>') && inj.includes('&lt;img'));

console.log(`✅ dms-intake-push-status 纯函数契约:${pass} passed`);
