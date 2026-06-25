# UI 整顿 · 实时进度与交接清单 · 2026-06-09(基于 git+grep 客观核查,非窗口自报)

> 读法:这是"还剩什么"的唯一可信清单。新窗口接手照此做。标准见 `DESIGN_SYSTEM.md`,照搬源 `scripts/_mock/kit-final.html`。

## ✅ 已完成(commit 为证)
- 基座 `a61650ab`:双套令牌(浅+暗)、组件 kit、**暗夜模式**、外壳(logo+Pearnly、头像菜单收用户名)、formatDate、6 模板。
- A 组 8 屏迁 emerald + 流式:dashboard `1f719983` / OCR `71c25cfd` / history `f1f22b91` / 对账 `48d4f601` / 销售工作台·客户·应收·销售报表 `6e8d8a54`。
- B 组令牌化 `3d12be6c/71c25cfd`:进项主屏/待归类/供应商/采购设置/库存/POS/知识库/异常 换全局 emerald token、删本地 token、max-width→流式。
- OCR 日期消歧 `61fa7e05`(24/08/25 不再读成 2023)。暗夜实测可用(OCR/history/对账)。

## ❌ 未完成 · 收尾 punch list(新窗口的活)
**P1 · 漏迁的屏(还在旧蓝 #2563EB/--blue,grep 实证)**
- `module-settings.ts`(模块设置,max-width:680 也要改流式)
- `onboarding-business.ts`(注册选业态)
- `pos-cashiers.ts`(收银员)
- 复核 `app-shell-html.ts` 有无旧蓝残留(A 独占的共享文件)

**P1 · 弹窗未迁 kit(用户实测"弹窗内不一致")**
- `sales-detail.ts`(内联 `.modal max-width:640`)、`sales-settings.ts`(`max-width:720`)→ 改用 kit `.modal`/令牌。
- 逐个排查并迁:`purchase-modals.ts`(付款/匹配/LINE)、`confirm-modal.ts`、`email-modal-html.ts`、`workspace-switcher.ts`(账套选择 ws-modal)。
- 标准:弹窗 = kit `.ov/.ovh/.ovb/.ovf`,按钮底部右(次左主右),危险=红+确认。

**P1 · 图标换 Lucide(还在 emoji,grep 实证 · 用户实测"图标不一致")**
- 文件:`inventory.ts` · `pos-tables.ts` · `purchase-detail.ts` · `page-integrations.ts` · `bank-recon-v2-results.ts` · `excel-recon-tasklist.ts` · `recon-job-poll.ts` · `workspace-switcher.ts` · `test-center.ts`
- 全部 emoji 图标 → kit 的 Lucide inline svg(见 kit-final 图标注入器)。

**P2 · 按钮分类 retrofit(§4-bis · 用户实测"按钮/全选不一致")**
- 每屏按 3 轴重排:主(1个实心)/次(描边)/三级(幽灵)/危险(红+确认);作用域(页头/工具条/行尾/批量条/卡内);**一排 ≥4 个按钮 = 收进 `⋯ 更多`**。
- 表格"全选"复选 + 批量条统一成 kit 样式(见 kit-final 批量条)。

**P2 · 文案 / 细节**
- `page-reconcile-panes-1.ts:106` 删自曝文案"OCR 抽不准?手动录入 3 个余额" → 改中性(如"手动校正余额(可选)")。i18n 键 `brv2-anchor-title` 四语一并改。
- `knowledge-ask.ts` 760→流式;确认知识库"双框"是否合一。
- dashboard 最近活动若仍有 i18n 原始键(`*-ago-suffix`)一并修。

## 验收(每屏 + 每弹窗)
保真闸绿(浅+暗)· 暗夜一键翻无残留浅 · 67/100/150% 缩放贴满 · **逐个弹窗点开看** · 一排无 ≥4 裸按钮 · 0 console error · 全站任意两屏并排组件/色/图标一致。

## 🔬 全量扫描 triage(2026-06-09 · `scripts/ui_design_lint.mjs` · 报告 `UI_LINT_REPORT.txt`)
> 原始命中数有水分,以下是**真违规**(已剔除注释/@media/弹窗合法宽度/着陆页)。

**🔴 根因(最重要):本轮迁移是「叠加」不是「替换」。** 旧 CSS 包 `static/home-01..44-*.css` 仍在加载、仍定义并大量使用蓝色调色板(`--blue`/`--blue-100..800`,238 处)+ 1478 处裸 hex。新 kit(`home-45-kit.css`)只是加在旁边。所以很多屏(尤其旧屏/弹窗/抽屉)视觉上还是蓝的。
- **最省力高影响修法**:在 `static/home-01-base.css` 的 `:root` 把 `--blue/--blue-50..800` 的**值**直接改成 emerald 系 → 238 处引用 + 大量 badge/hint **一次性翻绿**(令牌威力,不用逐屏改)。⚠ 注意 `home-45-kit.css:482` 自己也引了 `--blue`,一并对齐。

**真 punch list(按影响排):**
1. **退役/重调旧蓝调色板**(根因·见上)——改 `home-01-base.css` --blue* 值为 emerald;复核 kit 里 --blue 残留。
2. **漏迁的 src 屏(还在旧蓝/裸hex)**:`module-settings`(680 max-width也改流式)、`onboarding-business`、`pos-cashiers`、`rules-settings(-data)`、`sales-account`(COLORS 数组)。
3. **弹窗/抽屉系统没统一**:① 旧 `.drawer` 应迁 `.modal`(`ocr-results`/exceptions drawer 等,home-05/08/12/16/18 的 .drawer-* 类)② 全站弹窗存在两套(旧 `.modal` vs kit `.ov`)——定一套、retone 对齐 kit(modal 自带 max-width 是对的,别动宽度,动的是视觉)。
4. **真 emoji 当 UI 图标**(非注释/非i18n文本的少数):`page-reconcile-panes-2`(⏱/⚠ kpi图标)、`bank-recon-v2-results`、`excel-recon-tasklist` → Lucide。(注:i18n 文案里的 ✅/⚠ 多数是文字强调,非图标,可不动。)
5. **原生弹窗**(真调用,非注释):`glv-history:168 confirm`、`glv-results:139 alert`、`sales-detail:436 confirm`、`sales-products:223 confirm`、`session-heartbeat:52 alert`、`test-center-base:171 alert` → kit modal/toast。
6. **文案**:`OCR 抽不准` 在 `i18n-data.js:2883`(键 `brv2-anchor-title`,四语)+ `page-reconcile-panes-1:106` → 改中性。
7. **z-index 散乱**(9999/99999,11文件)→ 收进 z 标度(低优先,先不崩就行)。
8. **dashboard** `time-*-ago-suffix`:键已存在 i18n-data,确认运行时渲染"X小时前"非原始键。
9. **knowledge-ask** 760→流式。

**虚高/可忽略(别浪费工夫):** @media 断点的 max-width(响应式,对的)· 弹窗的 max-width(弹窗就该有上限)· 注释里的 emoji/alert(不渲染)· **POS(`static/pos/*`)与 admin(`static/admin/*`)是独立 SPA、自带蓝调色板——本轮主 app 不含,要不要迁单独定** · 着陆页 `static/landing/*` 明确排除。

**永久防回潮**:`node scripts/ui_design_lint.mjs` 每次改完 UI 重跑;清零后挂进 pre-push/CI(扩 `check_ui_consistency`),以后"零碎没改完"机器直接拦。

## 注
- 两窗口已停、工作树应 clean(接手前先 `git status` + `git pull`)。
- Weekly 额度曾 99%,接手前确认已重置。
- 剩活以"收尾/细节"为主,**单窗口即可**(无需再并行);机械活用 Sonnet。
