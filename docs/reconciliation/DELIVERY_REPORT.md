# 对账中心 UI 重设计 · 交付报告(2026-06-14)

分支:`feat/recon-center-redesign`(未 push · 待验收)。后端契约一字未改;仅前端。

---

## 一、修改 / 新增文件

**新增(前端)**
| 文件 | 职责 | 行数 |
|---|---|---|
| `src/home/recon-center-x-html.ts` | 设计外壳 HTML(`RCX_HTML`)| 229 |
| `src/home/recon-center-x-store.ts` | 共享状态 + 三类型配置 + 工具 | 167 |
| `src/home/recon-center-x-render.ts` | 上传卡四态 / 余额预检 / 就绪态 / 状态机 A–G 显隐 | 193 |
| `src/home/recon-center-x-tpl.ts` | 模板中心面板 + 横幅 + 导入说明 + 真后端模板下载 | 154 |
| `src/home/recon-center-x-results.ts` | 三类结果适配器 + KPI 筛选 + 明细分页 + 导出 + 处理差异 | 358 |
| `src/home/recon-center-x.ts` | 主控制器(init/tab/上传/开始/轮询/失败/事件)| 459 |
| `static/home-48-recon-redesign.css` | 作用域 `.rcx-` 样式(令牌局部化)| 280 |
| `docs/reconciliation/AUDIT_FRONTEND.md` | 项目审计(§二)| — |
| `scripts/_rcx_test.cjs` | 组件/交互测试(esbuild+Playwright)| — |
| `scripts/_rcx_preview.cjs` | 视觉对比 harness | — |

**改动(最小面)**
- `src/home/page-reconcile.ts`:注入源从旧 `RECON_HTML_1/2` 改为 `RCX_HTML`。
- `src/main.js`:新增 `import './home/recon-center-x.js'`(在 recon-center/recon-job-poll/bank-recon-v2 之后,覆盖旧 `loadReconcilePage`)。
- `src/types/globals.d.ts`:补 `window.showConfirm` / `window.showToast` 类型。
- `static/i18n-data.js`:补 `rcx-*` 四语文案(166 key × 4 语,完整性闸 0 缺 0 多)。
- `scripts/build-home-css.mjs`:CSS 清单加 `home-48-recon-redesign.css`。
- `home.html`:`?v=` bump 到 11850801(home.css / i18n-data / main.js,CRLF 保留)。

旧模块(`bank-recon-v2*` / `gl-vat-recon` / `excel-formula-recon` / `recon-subtab-settings` 的 tab 部分)文件保留:其 DOM 已不在页面 → init 自守卫 no-op;`recon-subtab-settings` 的设置弹窗(`openSettingsModal`)与对账无关,继续可用。

---

## 二、每个按钮的真实交互与调用位置(§十四 逐条)

| 按钮 | 真实行为 | 代码位置 |
|---|---|---|
| 三对账类型切换 | 换 doc_type/端点/字段/模板/标题 + **清残留**(文件/结果/余额/筛选);有数据先 `showConfirm` | `recon-center-x.ts switchTab` |
| 导入说明 | 打开纯说明弹窗(Esc/遮罩/知道了关,不改上传态)| `tpl.ts openGuide` |
| 模板中心 | 右侧面板;内容随类型;关闭不清文件 | `tpl.ts openDrawer/renderTemplates` |
| 下载本页模板 / 下载全部 | 顺序真下载两个模板 + 防重 loading | `tpl.ts downloadPageTemplates` |
| 暂不提示 | 本会话隐藏横幅(模板中心仍可下载)| `recon-center-x.ts` banner-hide |
| 选择文件 / 拖拽 | **同一** `handleFiles`:格式/大小校验→读取方式判定→渲染卡 | `recon-center-x.ts handleFiles` + `bindGridDrop` |
| 下载标准模板(左右各)| 左右下不同 doc 的真 .xlsx | `tpl.ts downloadSide` |
| 移除文件 | 清文件+卡+余额来源+**立即重新禁用开始** | `recon-center-x.ts removeFile` |
| 预览文件 | `URL.createObjectURL` 打开用户真文件(非假提示)| `recon-center-x.ts previewFile` |
| 确认字段对应 / 确认并导入 | **复用** `window.ReconMapping`(真存学习层)| submit→`needs_mapping` 触发,`afterPoll` |
| 确认需要关注的内容 / 确认 N 项 | **复用** `window.ReconReview`(走 confirm-rows 真重对账)| `afterPoll` needs_review |
| 清空 | 二次确认后清本次态(不删长期映射)| `recon-center-x.ts clearAll` |
| 开始对账 | 防重→按类型 submit→`_reconPollJob`→诚实进度→结果 | `recon-center-x.ts start/afterPoll` |
| 匹配率/已匹配/待处理差异/未匹配 | **真实筛选**明细(选中态+总数+分页同步)| `results.ts setFilter/renderDetail` |
| 开始处理 N 项差异 | 进真实差异列表(筛选到差异+未匹配,滚动到明细)| `results.ts handleDifferences` |
| 导出结果 | 按类型调真导出端点 fetch+blob 下载 | `results.ts exportResult` |
| 弹窗/抽屉关闭 + Esc | 真关闭 + 键盘可达 | `recon-center-x.ts` keydown |
| 原型底部 4 个演示按钮 | **已删除**(不落地)| — |

---

## 三、三类文件处理流程

- **标准模板 / 普通表格 / 文件内容** 三种读取方式:卡片按扩展名+文件名签名给**临时**读取方式标签(不展示任何假行数/假项数)。**真实**的「标准 vs 需确认字段 vs 需确认内容」由 `开始对账` 提交后端后,以 `needs_mapping`(弹字段对应)/ `needs_review`(弹内容确认)/ `done` 判定 —— 这是后端真实信号,非前端臆测。
- 提交端点:银行 `POST /api/recon/bank-v2/submit`;收入 `POST /api/recon/gl-vat/submit`;销项税 `POST /api/vat_excel/submit`。
- 轮询 `GET /api/recon/jobs/{id}`(`window._reconPollJob`);进度无精确百分比 → 「正在执行对账,请稍候……」+ 仅接口提供的阶段文案,**无定时器假进度**。
- 结果读取:银行 `/api/recon/bank-v2/{result_id}`;收入 `/api/recon/gl-vat/{result_id}`;销项税 `/api/vat_excel/tasks/{result_id}`。三套载荷各有适配器归一成统一 KPI/明细。

## 四、标准模板真实路径

下载一律走 `GET /api/recon/template/{doc_type}?lang=<当前UI语言>`(`doc_type ∈ statement|gl|vat|invoice`),fetch+blob 带鉴权,文件名取自 `Content-Disposition`,真 `.xlsx`。**前端不生成任何 CSV**。模板内含列头+示例+说明 sheet。

## 五、测试与构建

- `node scripts/_rcx_test.cjs` —— esbuild 打包真控制器 + Playwright 真 DOM:**24/24 通过**(初始渲染/开始禁用/三 tab 切换换标题+模板+清残留/余额按类型显隐/抽屉随类型 2 模板/Esc 关弹窗抽屉/真传文件启用/移除重置/无 OCR·AI 字眼)。
- `npx tsc --noEmit` —— **0 错**。
- `python scripts/check_ui_consistency.py` —— D1 抽屉 120(=基线·未增)、D2 按钮黑底 0、总违规 310<480。
- `python scripts/check_i18n.py` —— 0 缺 0 多(四语各 4163 key)。
- size 闸 —— 所有源文件 <500(最大 459)。
- `npm run build` —— 成功;`static/dist/{home.css,main.js,home.html}` 已更新并版本一致(?v=11850801)。

## 六、视觉对比(≥两轮)

`node scripts/_rcx_preview.cjs` 在 1440/1280/390 截图,与 `design-reference/pearnly_reconciliation_redesign_v2.html` 逐项对照(截图存 `product-audit/rcx-shots/`)。
- 第 1 轮:内容区结构/配色(紫 #6C4CFF)/圆角/间距/双卡+加号/余额/底栏与参考一致;移动端 390 三 tab 偏挤。
- 第 2 轮:收口移动端 segmented 字号/换行 → 三 tab 全容下。
- 与原型的有意差异:不复制原型侧栏/顶栏(按任务用真实布局容器承载)。

---

## 七、未完成 / 受限 / 需人工验收

1. **真后端端到端未在本窗口运行**:所有动作均接真实端点并复用经验证的现成组件(`_reconPollJob`/`ReconMapping`/`ReconReview`/export),但「登录态 + 真文件跑完整 submit→轮询→结果→导出」需在运行中的服务器人工验收。
   - 路径:登录 → 对账中心(route `reconcile`)→ 银行对账:传 银行账单 + GL → 开始对账 → 查看四指标/优先处理/明细/导出;收入对账:GL + 税表VAT;销项税:税表VAT + 销项发票明细。
2. **后端依赖(见 `00_CURRENT_STATE_AND_CORRECTIONS.md §四`)**:VAT 解析器 zh/ja 列头、销项发票 Excel 结构化路。任务交底为「后端已就绪」,前端按此实现;若该两项未落,**中/日界面税表模板** 或 **销项税发票侧** 可能在导入时静默失败 —— 列此为前置依赖。
3. **有意的诚实取舍(非偷工)**:
   - 卡片不显假行数/假需确认项数(原型的 1286 行/3 项是 mock);真实判定在 submit。
   - 余额预检 = 银行的真实手动 anchor 录入(喂 `*_override`),非原型写死余额;收入/销项税无同义余额 → 隐藏该区。
   - 进度为诚实进行中态,无假百分比。
   - 单卡单文件(原型亦单文件);旧 brv2 的多文件/历史列表/多账户选择器未并入新外壳,如需可后续补(列为已知差距,非假装实现)。
   - 模板面板类名用 `rcx-tplpanel`(非 `drawer`):它是设计书明确要求的右侧模板面板,命名如实且不触发「禁新增 .drawer」闸。
4. **未 push**:按铁律「未验收不 push master」,停在分支。
