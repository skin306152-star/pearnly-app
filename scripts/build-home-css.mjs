// 把 home / admin 两个 SPA 的 component CSS 合并压缩成各自单个 bundle
// (static/dist/{home,admin}.css)· view-source 只见一个 link · 大厂成品形态。
//
// 清单顺序 = 原 home.html / admin.html 的 DOM 顺序固化而来(整顿期 CSS 已冻结)。
// CSS 层叠 / !important 收口依赖顺序,改动这两个数组前务必核对 DOM 顺序。
// home.css 是历史死链(C2 拆空)已剔除;内联 modal override 已抽成 home-modal-override.css。
//
// 用法: node scripts/build-home-css.mjs

import path from 'path';
import { transform } from 'esbuild';
import { readSource, writeDist } from './build-lib.mjs';

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
    'home-39-sales.css',
    'home-40-sales-wizard.css',
    'home-41-inventory.css',
    'home-42-pos-onboarding.css',
    'home-43-pos-report.css',
    'home-44-pos-cashiers.css',
    'erp-mrerp-connect.css',
    'home-45-kit.css',
    'home-46-acct-bankmj.css',
    'home-48-recon-redesign.css',
    'home-49-dms-intake.css',
    'home-50-express.css',
    'home-51-express-detail.css',
    'home-52-image-viewer.css',
    'home-53-subscription.css',
    'home-54-records.css',
    'home-55-upload-zone.css',
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
    'home-45-kit.css',
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
    'landing/landing-tour.css',
    'landing/landing-tour-phone.css',
    'landing/landing-tour-cards.css',
];

// 管理控制台 SPA + 邀请页:主题令牌在前,组件样式在后(固化原 DOM 顺序)。
const CONSOLE_CSS = ['console/console-theme.css', 'console/console.css'];

// POS 收银 SPA:零售/药房基础样式在前,餐厅作用域样式在后(固化原 pos.html 顺序)。
const POS_CSS = ['pos/pos.css', 'pos/pos-restaurant.css'];

// Pearnly AI SPA(M1-W1 · 独立工作台):令牌源在前,骨架/选客户层/客户页依次叠加
// (固化原 ai.html 引用顺序)。ai-viewer.css(原件查看器 .pv-*)排最后——挂载点
// .rv-imgwrap 在 ai-client.css 定义,查看器样式晚到不影响其令牌解析(CSS 变量按用时解析)。
const AI_CSS = [
    'ai/ai-theme.css',
    'ai/ai-shell.css',
    'ai/ai-dashboard.css',
    'ai/ai-client.css',
    'ai/ai-viewer.css',
];

const BUNDLES = [
    { list: HOME_CSS, out: 'static/dist/home.css' },
    { list: ADMIN_CSS, out: 'static/dist/admin.css' },
    { list: LANDING_CSS, out: 'static/dist/landing.css' },
    { list: CONSOLE_CSS, out: 'static/dist/console.css' },
    { list: POS_CSS, out: 'static/dist/pos.css' },
    { list: AI_CSS, out: 'static/dist/ai.css' },
];

async function buildOne(list, out) {
    const chunks = list.map((f) => {
        let css = readSource(`static/${f}`);
        // 相对 url('./x') 跟着源文件目录走;移进 dist/ 后须改成绝对路径,否则资源 404
        const dir = path.dirname(f); // 'landing' 或 '.'
        if (dir !== '.') {
            css = css.replace(/url\((['"]?)\.\//g, `url($1/static/${dir}/`);
        }
        return css;
    });
    const { code } = await transform(chunks.join('\n'), { loader: 'css', minify: true });
    writeDist(out, code);
}

async function main() {
    for (const b of BUNDLES) await buildOne(b.list, b.out);
}

main().catch((e) => {
    console.error('❌', e.message);
    process.exit(1);
});
