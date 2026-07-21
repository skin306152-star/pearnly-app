// 把 home / admin 两个 SPA 的 component CSS 合并压缩成各自单个 bundle
// (static/dist/{home,admin}.css)· view-source 只见一个 link · 大厂成品形态。
//
// 清单顺序 = 原 home.html / admin.html 的 DOM 顺序固化而来(整顿期 CSS 已冻结)。
// CSS 层叠 / !important 收口依赖顺序,改动这两个数组前务必核对 DOM 顺序。
// home.css 是历史死链(C2 拆空)已剔除;内联 modal override 已抽成 home-modal-override.css。
//
// 用法: node scripts/build-home-css.mjs

import fs from 'fs';
import path from 'path';
import { transform } from 'esbuild';
import { ROOT, readSource, writeDist } from './build-lib.mjs';

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
    'home-56-posting-editor.css',
    'home-57-erp-review.css',
    'home-58-erp-verify.css',
    'home-59-dx-push-status.css',
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
    // ai-gate.css(Z1-a 登录卡/邀请制门面)吃 ai-theme 令牌 + ai-shell 的 .btn 系统,排在
    // 两者之后、看板/客户页样式之前——门面与工作台视图互斥显示,层叠顺序对彼此零影响。
    'ai/ai-gate.css',
    'ai/ai-dashboard.css',
    // ai-matrix.css(C4 · 工作台新默认视图)吃 ai-theme 令牌 + ai-shell 的 .btn/.chip/.dot,
    // 排在 ai-dashboard.css 之后即可(矩阵/看板是同一工作台页的两个互斥子视图)。
    'ai/ai-matrix.css',
    'ai/ai-client.css',
    'ai/ai-client-empty.css',
    // ai-review-jc.css(J-C · 客户页审核队列已判折叠/批量确认横幅/建议值三字段改数表单)
    // 只补这三块 J-C 独有的 .rv-* 细节,吃 ai-client.css 已有的 .rv-edit/.rv-vat-input/
    // .chip 原子,排在其后即可;ai-client.css 已逼近 500 行预算线,新增样式不再塞进去。
    'ai/ai-review-jc.css',
    'ai/ai-intake.css',
    // ai-bank-sales.css(SA-3b · 收料 tab 银行流水倒推销项确认清单)吃 ai-recon.css 的
    // .brx-* 折叠列表原子 + ai-fileconv.css 的 .fc-banner 降级横幅 + ai-shell.css 的
    // .panel/.chip/.btn,故排在 ai-recon.css/ai-fileconv.css 之后单独引不现实(那两个
    // 排更后面)——.brx-*/.fc-banner 类名与具体声明顺序无关(纯附加类,非覆盖关系),
    // 排在 ai-intake.css 之后即可,不影响其余视图。
    'ai/ai-bank-sales.css',
    'ai/ai-pkg.css',
    // ai-recon.css(E2 · 银行对账四清单)复用 ai-pkg.css 的 .pkg-mask/.pkg-modal 原图
    // 模态外壳,排在其后即可;与工单详情 .wosum/.needs-list(ai-client.css)同屏但
    // 各管各的类名,层叠顺序对彼此零影响。
    'ai/ai-recon.css',
    // ai-corrob.css(MC1-c.1 · 销项佐证卡)吃 .panel/.chip(ai-shell.css)外壳,只补 crb-* 行
    // 布局/点名色,排在 ai-recon.css 之后即可;与其余工单详情只读区块类名各自独立,层叠零影响。
    'ai/ai-corrob.css',
    // ai-shadow.css(F3 · 影子底稿三分区折叠)吃 .panel/.chip(ai-shell.css)+ .mx-scroll/
    // .mx-table(ai-matrix.css,科目余额表复用宽表格容器内横滑原子),排在两者之后即可;
    // 与银行对账区(ai-recon.css)同屏但类名各自独立,层叠顺序对彼此零影响。
    'ai/ai-shadow.css',
    // ai-financials.css(G1b · 月度报表包五分区折叠)吃 .panel/.chip(ai-shell.css)+
    // .mx-scroll/.mx-table(ai-matrix.css/ai-vatcheck.css,科目金额表复用宽表格容器内横滑 +
    // 数字右对齐原子),排在两者之后即可;与影子底稿区(ai-shadow.css)同屏但类名各自独立,
    // 层叠顺序对彼此零影响。
    'ai/ai-financials.css',
    // ai-profile.css(B2-e 画像/别名/义务清单)吃 .sf-*(ai-intake.css)/.panel/.chip
    // (ai-shell.css)原子,排在两者之后即可;与 pkg 视图互斥显示,顺序对彼此零影响。
    'ai/ai-profile.css',
    'ai/ai-viewer.css',
    // ai-client-pool.css(D2-S8 客户池页)只吃 ai-theme 令牌 + ai-shell 的 .panel/.chip/.btn,
    // 排最后即可(与其余视图互斥显示,层叠顺序对彼此零影响)。
    'ai/ai-client-pool.css',
    // ai-review-inbox.css(MC1-b2 · 全所审核收件箱三分区聚合页)吃 ai-theme 令牌 +
    // ai-shell.css 的 .panel/.chip/.btn/.fldt + ai-client-pool.css 的 .cp-section 间距
    // 惯例,排在其后即可;与其余视图互斥显示,层叠顺序对彼此零影响。
    'ai/ai-review-inbox.css',
    // ai-vatcheck.css(N1 · 销项税报告三查)复用 ai-intake.css 的 .dropzone/.dz-* 上传区 +
    // ai-matrix.css 的 .mx-scroll/.mx-table 宽表格容器,排在两者之后即可;与其余视图
    // 互斥显示,层叠顺序对彼此零影响。
    'ai/ai-vatcheck.css',
    // ai-fileconv.css(K1b · 财务文件转换)复用 ai-intake.css 的 .dropzone/.dz-* 上传区,
    // 横幅/结果条布局同构 ai-vatcheck.css 但类名独立(fc-*),排最后即可;与其余视图
    // 互斥显示,层叠顺序对彼此零影响。
    'ai/ai-fileconv.css',
    // ai-payroll.css(H1b · 工资表 ภ.ง.ด.1 工具卡)复用 ai-intake.css 的 .dropzone/.dz-*
    // 上传区 + ai-fileconv.css 的 .fc-*(横幅/统计行/issue 行),排在两者之后即可;只补
    // 列映射表格 + 手工加行表单这两块 H1b 独有的 .pr-* 结构,与其余视图互斥显示,层叠
    // 顺序对彼此零影响。
    'ai/ai-payroll.css',
    // ai-clients.css(EN-clients · 客户目录/单客户档案页)只补 .mx-table 系没有的两处细节
    // (税号列数字对齐 + 义务徽章列换行容器);档案页/报表中心/设置三视图其余全复用既有
    // .chead/.ctabs/.cview(ai-client.css)、.pr-setup-row/.pr-lb(ai-payroll.css)、
    // .pkg-files/.pfile(ai-pkg.css)、.view-toggle/.vt-btn(ai-matrix.css)——零新增文件。
    'ai/ai-clients.css',
    // ai-client-import.css(IN-0d · 客户名录批量导入模态)只补计数条/操作按钮行/行内错误
    // 原因文案三处布局细节,模态外壳/上传区/表格/徽章全复用既有 .pkg-*/.dropzone/.dz-*/
    // .mx-table/.chip,排最后即可,与其余视图互斥显示,层叠顺序对彼此零影响。
    'ai/ai-client-import.css',
    // ai-desk.css(FD-0d · 总台 #/desk)复用 ai-intake.css 的 .dropzone/.dz-*/.file-strip/
    // .fchip/.intake-err 上传区原子 + ai-shell.css 的 .panel/.chip/.btn,只补对话流布局
    // (上下文条/消息卡/输入条 sticky)这块总台独有的 .fd-* 结构,排最后即可,与其余
    // 视图互斥显示,层叠顺序对彼此零影响。
    'ai/ai-desk.css',
];

// Pearnly DMS SPA:壳令牌/原子/门面在前(dms-shell.css 定义 :root 令牌),身份证向导内容区
// 样式在后(dms-intake.css · .dmsx 按前者令牌解析)。固化 dms.html 引用顺序。
// dms-billing.css(波1 · 套餐与余额)复用 dms-shell.css 的令牌 + .btn/.dms-state/.dms-badge,
// 只补计费视图独有的卡片/套餐格/充值区布局,排最后即可,与其余视图互斥显示,层叠零影响。
const DMS_CSS = [
    'dms/dms-shell.css',
    'dms/dms-gate.css',
    'dms/dms-intake.css',
    'dms/dms-billing.css',
    // dms-roster.css(波3 · 操作员花名册)复用 dms-shell 令牌 + .btn/.dms-state/.dms-badge +
    // dms-billing.css 的 .dms-bill-card/.dms-bill-input;只补花名册独有的表单网格/操作员表/角色
    // 徽标/弹层 + 记录页 owner 视角(C6)的 .with-op 列扩展,排最后即可,与其余视图互斥零影响。
    'dms/dms-roster.css',
];

const BUNDLES = [
    { list: HOME_CSS, out: 'static/dist/home.css' },
    { list: ADMIN_CSS, out: 'static/dist/admin.css' },
    { list: LANDING_CSS, out: 'static/dist/landing.css' },
    { list: CONSOLE_CSS, out: 'static/dist/console.css' },
    { list: POS_CSS, out: 'static/dist/pos.css' },
    { list: AI_CSS, out: 'static/dist/ai.css' },
    { list: DMS_CSS, out: 'static/dist/dms.css' },
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

// 自托管字体(UI-Canon v5 §6.6 · Sarabun woff2)源在 static/ai/fonts/,部署只拾
// dist,而 vite emptyOutDir 每次清空 static/dist —— 故随 CSS 打包一并复制回 dist。
function copyFonts() {
    const srcDir = path.join(ROOT, 'static/ai/fonts');
    const outDir = path.join(ROOT, 'static/dist/fonts');
    fs.mkdirSync(outDir, { recursive: true });
    for (const f of fs.readdirSync(srcDir).filter((n) => n.endsWith('.woff2'))) {
        fs.copyFileSync(path.join(srcDir, f), path.join(outDir, f));
        console.log(`✅ static/dist/fonts/${f}`);
    }
}

async function main() {
    for (const b of BUNDLES) await buildOne(b.list, b.out);
    copyFonts();
}

main().catch((e) => {
    console.error('❌', e.message);
    process.exit(1);
});
