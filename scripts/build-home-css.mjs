// 把 home / admin 两个 SPA 的 component CSS 合并压缩成各自单个 bundle
// (static/dist/{home,admin}.css)· view-source 只见一个 link · 大厂成品形态。
//
// 清单顺序 = 原 home.html / admin.html 的 DOM 顺序固化而来(整顿期 CSS 已冻结)。
// CSS 层叠 / !important 收口依赖顺序,改动这两个数组前务必核对 DOM 顺序。
// home.css 是历史死链(C2 拆空)已剔除;内联 modal override 已抽成 home-modal-override.css。
//
// 用法: node scripts/build-home-css.mjs [--check]

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { transform } from 'esbuild';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const HOME_CSS = [
    'home-01-base.css',
    'home-02-switcher.css',
    'home-03-layout.css',
    'home-04-results.css',
    'home-05-overlays.css',
    'home-06-responsive-rd.css',
    'home-07-history-automation.css',
    'home-08-pagehead-toast.css',
    'home-09-badges-locks.css',
    'home-10-push-logs.css',
    'home-11-automation-settings.css',
    'home-12-drawer-search.css',
    'home-13-upgrade-dup-prefs.css',
    'home-14-gemini-admin.css',
    'home-15-team-folder.css',
    'home-16-cost-clients.css',
    'home-17-aibalance-reports-trial.css',
    'home-19-exceptions-alerts.css',
    'home-20-banners-pushlogs.css',
    'home-21-recon-center.css',
    'home-22-settings-mobile.css',
    'home-23-test-center.css',
    'home-24-logs-access-assign.css',
    'home-25-bankrecon-erpmapping.css',
    'home-26-erp-cards.css',
    'home-27-erp-credentials.css',
    'home-28-erp-banners-batch.css',
    'home-29-vat-recon-clients.css',
    'home-30-settings-modal.css',
    'home-31-navia-topbar.css',
    'home-32-recon-folding.css',
    'home-33-dashboard.css',
    'home-34-navia-config-drawer.css',
    'home-35-bankrecon-v2.css',
    'home-36-topup.css',
    'home-modal-override.css',
    'home-37-html-inline.css',
    'home-38-buttons.css',
    'erp-mrerp-connect.css',
];

const ADMIN_CSS = [
    'home-01-base.css',
    'home-02-switcher.css',
    'home-03-layout.css',
    'home-04-results.css',
    'home-05-overlays.css',
    'home-06-responsive-rd.css',
    'home-07-history-automation.css',
    'home-08-pagehead-toast.css',
    'home-09-badges-locks.css',
    'home-10-push-logs.css',
    'home-11-automation-settings.css',
    'home-12-drawer-search.css',
    'home-13-upgrade-dup-prefs.css',
    'home-14-gemini-admin.css',
    'home-15-team-folder.css',
    'home-16-cost-clients.css',
    'home-17-aibalance-reports-trial.css',
    'home-18-admin-users.css',
    'home-19-exceptions-alerts.css',
    'home-20-banners-pushlogs.css',
    'home-21-recon-center.css',
    'home-22-settings-mobile.css',
    'home-23-test-center.css',
    'home-24-logs-access-assign.css',
    'home-25-bankrecon-erpmapping.css',
    'home-26-erp-cards.css',
    'home-27-erp-credentials.css',
    'home-28-erp-banners-batch.css',
    'home-29-vat-recon-clients.css',
    'home-30-settings-modal.css',
    'home-31-navia-topbar.css',
    'home-32-recon-folding.css',
    'home-33-dashboard.css',
    'home-34-navia-config-drawer.css',
    'home-35-bankrecon-v2.css',
    'home-36-topup.css',
    'home-37-html-inline.css',
    'home-38-buttons.css',
    'admin/admin.css',
];

const LANDING_CSS = [
    'landing/landing.css',
    'landing/landing-auth.css',
    'landing/auth-sso.css',
    'landing/auth-modal.css',
    'landing/mascot.css',
    'landing/mascot-effects.css',
    'landing/responsive.css',
    'landing/landing-static-bg.css',
    'landing/landing-static-bg-mobile.css',
    'landing/landing-interactions.css',
];

const BUNDLES = [
    { list: HOME_CSS, out: 'static/dist/home.css' },
    { list: ADMIN_CSS, out: 'static/dist/admin.css' },
    { list: LANDING_CSS, out: 'static/dist/landing.css' },
];

async function buildOne(list, out, check) {
    const chunks = list.map((f) => {
        const fp = path.join(ROOT, 'static', f);
        if (!fs.existsSync(fp)) throw new Error(`CSS 源缺失: ${f}`);
        // strip BOM:文件开头的 BOM 独立 link 时浏览器忽略,但合并到 bundle 中间
        // 就是非法字符,会破坏紧跟的那条 CSS 规则(landing-auth.css 的 .auth-card 中招过)
        let css = fs.readFileSync(fp, 'utf8').replace(/^\uFEFF/, '');
        // 相对 url('./x') 跟着源文件目录走;移进 dist/ 后须改成绝对路径,否则资源 404
        const dir = path.dirname(f); // 'landing' 或 '.'
        if (dir !== '.') {
            css = css.replace(/url\((['"]?)\.\//g, `url($1/static/${dir}/`);
        }
        return css;
    });
    const merged = chunks.join('\n');
    const { code } = await transform(merged, { loader: 'css', minify: true });
    if (check) {
        console.log(`[${out}] ${list.length} 片段 · ${merged.length}→${code.length} 字节`);
        return;
    }
    fs.mkdirSync(path.join(ROOT, path.dirname(out)), { recursive: true });
    fs.writeFileSync(path.join(ROOT, out), code);
    console.log(`✅ ${out} · ${list.length} 片段 → ${code.length} 字节`);
}

async function main() {
    const check = process.argv.includes('--check');
    for (const b of BUNDLES) await buildOne(b.list, b.out, check);
}

main().catch((e) => {
    console.error('❌', e.message);
    process.exit(1);
});
