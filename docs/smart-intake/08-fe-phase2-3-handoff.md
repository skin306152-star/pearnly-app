# 进项采购前端 Phase 2 + 3 · 交接(2026-06-14)

> Phase 1(列表/复核屏/供应商)已上线 master(prod ver 11850841)。后端三阶段已全做完并在 master。
> 本文 = 新窗口直接照做的施工单。事实源:docs/smart-intake/04(交互)+05(契约)+06(UI)+原型
> `桌面/Pearnly_智能录入_UI预览/index.html`(⑤外流 ⑥集成中心 ⑦LINE卡)。配套记忆 [[intake-fe-rebuild-inflight]]。

## 〇、现状(已上线·别重做)
- 列表 `purchase-list.ts`(+`purchase-list-css/filters`)、复核屏 `purchase-form.ts`(+`-types/-css/-bill/-info/-lines/-totals`)、供应商弹窗 `purchase-suppliers.ts` 全上线。
- 复核屏已删报销人/内部付款凭证(决定①);**集成中心页/外流面板/详情凭证 surface/LIFF 尚未做**。
- `globals.d.ts` 已声明 `openPurchaseExport?:()=>void`(列表「⋯→导出/归档」已调它,现兜底「即将上线」)。

## 一、Phase 2(集成中心 + 外流 + 详情凭证)
### 1.1 集成中心页(`page-integrations.ts` 现占位/未建 Google 卡)
- 卡片网格(.modal 规范·线性图标·无黑底):**Google Drive/Sheets 卡**(未连=「连接 Google」按钮 / 已连=显邮箱+「断开」)· **LINE 卡已有不动** · Xero/邮件占位。
- 契约(envelope ok/data·带 `workspace_client_id`,按套账隔离):
  - `GET /api/integrations/google/status?workspace_client_id=` → `{configured, connected, email, scope}`。`configured=false` → 显「未配置」灰态不可点(后端没配 OAuth client)。
  - `GET /api/integrations/google/connect?workspace_client_id=` → 302 跳 Google 授权(**新标签/window.location 打开**,鉴权 fetch 拿不到 302 跳转,直接 `window.location.href` 或 `window.open` 该 URL 带 Bearer 不行→改成后端 connect 走浏览器导航;建议:点连接 = `location.href='/api/integrations/google/connect?...'`,回调后端写凭据再 redirect 回 /home#integration)。
  - `POST /api/integrations/google/disconnect`。
- 入口:左导航「集成」已存在(路由 integration)。在该页加 Google 卡。

### 1.2 外流收拢面板(`window.openPurchaseExport`)
- 列表「⋯→导出/归档」开**收拢面板(.modal,不平铺三按钮)**:导出 Excel(免授权)/ 归档到 Drive / 同步 Sheet + 提示「未连接点击跳集成中心」。
- 契约:`POST /api/purchase/export {workspace_client_id, format:'excel'|'drive'|'sheet', date_from?, date_to?}`
  - `excel` → 返 **xlsx blob**(Content-Disposition attachment)→ 鉴权 fetch 取 blob 下载(参 `purchase-common.ts` 的 `fetchAuthedBlobUrl`/`openPurchasePdf` 套路,改成触发 `<a download>`)。
  - `drive`/`sheet` → 未连 Google 返 **HTTP 412 detail=google_not_connected** → 跳集成中心高亮 Google 卡;已连返 `{job_id, status:'queued'}`。
  - `GET /api/purchase/export/{job_id}` → 轮询任务态 `{status, progress:{drive_url?, sheet_url?, done_n, skip_n, error?}}`(参 recon job 轮询)。完成给 Drive/Sheet 直达链接。
- 范围用列表当前筛选的 date_from/date_to(复用 `purchase-list-filters.dateRangeParams()`)。

### 1.3 详情页凭证 surface(`purchase-detail.ts`)
- 详情页凭证区:无正式票→「生成替代收据」、WHT>0→「生成扣缴凭证」、可下载已挂附件(后端 documents.py 已全:`POST /docs/{id}/substitute-receipt`、`/wht-cert`、`GET /docs/{id}/document.pdf?kind=`)。复用 `openPurchasePdf`。

## 二、Phase 3(LIFF)
- 让 Phase 1 的 `purchase-form` 复核屏能在 LINE webview(LIFF)里跑:`/liff/purchase/{docId}`(后端 line_liff_routes.py 已建端点 + `/api/line/liff/auth` 鉴权)。
- FE:LIFF 入口页签 LIFF token → 进 webview 打开复核屏(鉴权 + 入口);**不把整套重做成 Flex**;**App 内不放 LINE 按钮**(用户自行去 LINE)。
- 真验需真 LINE channel(LINE_LOGIN_CHANNEL_ID + LINE_FLEX_INTAKE=1),留用户配。

## 三、工作树 / 构建 / 推送(铁律)
- worktree `C:\Users\skin3\Desktop\pearnly-fe`(分支 feat/intake-fe·node_modules 是 junction)。开工先 `git fetch origin master && git rebase origin/master`(master 常被别窗口推进)。
- 边界:只动 `src/home/*.ts`+对应 CSS、`static/dist`(build 产物)、`static/i18n-data.js`、`home.html`(只 bump ?v=)、`tests/visual`。**绝不碰 routes/ services/**(后端已做完)。
- 改 src/home 必:`npm run build` + `git add static/dist` + **bump `home.html` 的 `?v=`**(★最大坑:不 bump→同版本化 URL CDN 服旧码用户看不到;当前 11850841,下次 +N)。
- 单文件 <500(prettier 会展开密集单行→易超,超了拆文件/抽 types)。新文件需 commit 写 `RATCHET-EXEMPT: <file> +<N> · 理由`。i18n 4 语(zh/en/th/ja)同增,插值 `{name}`。
- push:`git push origin HEAD:master`(worktree 内·pre-push 全闸兜底·绿才放行→webhook 部署新加坡)。被拒=master 推进了→`git fetch + git rebase origin/master`(dist 冲突→`npm run build` 后 `git add static/dist` 续 rebase)再推。

## 四、自验 / 自推 / 自 E2E 套路(本地反代×真后端)
- 真浏览器验(grep 类名不算):Playwright + 本地 http 反代(serve worktree·`/api`·`/internal` 反代 `https://pearnly.com`)+ 真账号 UI 登录(凭据**只从 env** `PEARNLY_E2E_USER/PASS` 填表单·不入码)→ 选套账门 `.wsg-card[data-wsg-pick]` → routeTo/openX → isVisible+getComputedStyle+截图。模板见本窗口历史(_selfcheck/_prodsmoke 已删·按 docs 描述重写到 tests/visual/_*.cjs·跑完删·临时 .cjs 别留[eslint 会红])。
- 套账门坑:真后端 owner 账号会弹门,点 `.wsg-card[data-wsg-pick]` 选;组件隔离验可 `document.body.classList.remove('workspace-gate-preboot')+移除 #workspace-gate-root`。真 app **无 #content**·滚动容器是 window。
- 守门:tsc/eslint(删临时 .cjs)/prettier(src/home 必格式化)/i18n/file_size<500/ratchet/ui_consistency(D1 抽屉/D2 黑底)/ui_design_lint(emoji 含 ↔ U+2194·max-width:\d{3}px 连 @media 都算→合并 @media 块)/视觉照搬闸(`node tests/visual/test_design_fidelity.spec.js`·新屏入 `tests/visual/design/` 基线·端口 8791)。
- 验收:真账号 `pearnly_e2e_3` 双端 E2E + 跨套账隔离;Excel 导出零授权可验;Google/LINE 真授权留用户配凭据(此环境验不了真 OAuth/LIFF·做 UI + 契约即可)。

## 五、坑速查
- CRLF(autocrlf=true):dist 一堆幻影 M 但 `git diff --quiet` 规整放行;commit 用 `git -c core.autocrlf=true`。home.html/home.js 是 CRLF+.prettierignore·只 Edit 改 ?v= 别 prettier。
- ★merge 陷阱:`git merge` 旧 origin/master 快照可能夹带别窗口已被 master 移除的文件→直推会复活;用 `git rebase origin/master`(本窗口已踩·见记忆)。
- 视觉闸盲区已修(套账门 preboot + recon 孤立映射);新增屏给映射 + 基线 html。
- 署名 Opus 4.8。本次对话沟通用中文。
