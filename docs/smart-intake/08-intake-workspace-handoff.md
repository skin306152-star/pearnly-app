# 录入工作台(身份证→DMS + 发票OCR融合)· 交接单

> 2026-06-14 · 当前 prod ver 11850839 · commit a2c27a83
> 记忆:[[dms-intake-wizard-shipped]]

## 一、已完成且上线(别重做)

**身份证 → DMS 客户** 独立页「录入工作台」(route `dms-intake`,`src/home/dms-intake{,-core,-confirm,-html}.ts` + `static/home-49-dms-intake.css`,作用域 `.dmsx`):

- 4 步向导:上传 → 识别 → 三场景匹配(精确/相似按姓名搜+打分/未匹配)→ 资料确认(只看差异 + 全部DMS字段双 tab)→ 推送。
- 后端**全部完成且真账号 dmstest 验过**:`recognize`(出 scenario/candidates/geo/prefixes)、`/api/dms/customer-fields`、`/api/dms/id-card/push`(create/overwrite/update)、`/api/dms/geo` 级联。`services/erp/{erp_dms_intake,mrerp_dms_client_intake}.py` + `routes/dms_routes.py`。
- 「**所见即所存**」保存语义(已修+真账号验):全字段表单初值来自 DMS,**没动的字段原样回写=保留;手动改/清的字段=真写进 DMS**(后端 `_apply_customer_fields`:键存在就写、空串=清空、键缺省才保留)。
- i18n 全四语(去中泰双语字面量,字段名走 `dxf-*`/`dxs-*` 键)。暗夜走全站令牌自动翻面。
- 称谓缩写归一(`น.ส.→นางสาว`,`services/ocr/id_card_extract.py:_normalize_thai_prefix`)。地址邮编从级联补全。
- 导航:事务所工具 → 采购系统(ระบบซื้อ)→ 销售系统(ระบบขาย)→ 做账(分组已改名+排序)。
- **旧 OCR 页内联面板三件套已删**(ocr-document-mode/ocr-dms-idcard/dms-id-card-results)。

## 二、终端用户已拍板的需求(5 条 · 照此做)

1. 客户**已存在**于 DMS:**只更新身份证有的字段**(称谓/姓名/证号/生日/地址),**保留其它原有字段**(电话/邮箱/Line)。→ 自动流程空值不动 DMS(已实现)。
2. 「全部DMS字段」表单**可编辑可保存**:手动改/清 → 按用户改的写进 DMS(已实现 WYSIWYG)。
3. **新建客户:手机号必填**(已实现校验)。
4. 称谓走 DMS 下拉选择(系统有什么选什么;dmstest 只有 นาย 是测试系统局限,正式 DMS 称谓主档齐全就正常)。
5. 字段非必填可空(手机号除外)。

## 三、剩余工作(几乎全是前端/UI · 后端已齐)

按 v1 设计稿 `C:\Users\skin3\Downloads\pearnly_intake_workspace_redesign_v1 (1).html` 走。"有的覆盖,没有的新增,桌面功能零删减"。

### A. 把发票/收据 OCR 融进录入工作台(任务选择器)
v1 = 统一页 + 任务选择器:**发票/收据录入 | 身份证订车录入**。发票走 上传→整理内容→结果确认→导出/推送 四步。**复用现有发票 OCR 全套接口,不重写**:
- 识别 `POST /api/ocr/recognize`(`src/home/ocr-recognize.ts`)· 结果 `renderResults`(`ocr-results.ts`)
- 上传/相机/相册 `upload-files.ts`/`upload-camera.ts`(`#drop-zone`/`#file-input`/`#camera-input`/`#gallery-input`)· 上限 `getMaxFiles`(`core.ts`)
- 导出 `POST /api/ocr/export` · `/api/erp/mrerp-xlsx-batch` · `/api/reports/history/batch_export`(`export.ts`)
- ERP 推送 `POST /api/erp/push`(录入工作台第 4 步提交链路,排除 mrerp_dms)

### B. 推送目标 ERP 动态(发票流的「导出/推送」步)
读 `GET /api/erp/endpoints`(`erp-endpoints.ts`,返回 `items:[{id,adapter,enabled,name}]`)。已配置且 enabled 的**非 mrerp_dms** adapter(mrerp/xero/webhook/flowaccount)**亮起可选**;没配/没启用 → 灰黑文案指引,点击 `routeTo('integration')` 跳集成页配置。

### C. 查看记录跳转
发票任务点「查看记录」→ `routeTo('history')`(识别记录);身份证任务点记录 → 跳推送日志(`routeTo('integration')` + 集成页 ERP tab,筛 `adapter=mrerp_dms`,`GET /api/erp/logs`)。

### D. 侧栏文案
**去掉「也可以从 LINE 录入」块**(终端用户拍:LINE 只做采购文字备注,不做发票OCR)。"处理流程"用真实统计可选(本月发票 `tenant-usage`、最近识别 `/api/history`)。

### E. 地址逐字段比对(身份证流的优化)
现在「完整地址」是一整串比对(house+moo+soi+road+...拼串),用户看不清哪个子字段差。改成**逐字段比对行**(DX_COMPARE 拆 house_no/road/subdistrict/district/province/zipcode 等),`dmsCompareVal('house_no')` 直接返回 `S.dmsVals.house_no`。(/simplify 审查标的 altitude 项 · 后端写入已逐字段就绪。)

### F. 完整手机端重做(15 条硬要求 · 核心)
现在是桌面缩小版,不合格。要重排(桌面功能零删减):
1. 简洁步骤条「第 2/4 步 + 当前步骤名」,不横向挤四项 2. 左右栏改上下 3. 宽比对表→一字段一卡片(新值/DMS值/最终选择/差异标黄)4. 全字段表单按分组折叠(客户资料/联系地址/身份证地址/文件联系地址)5. 底部固定操作栏 6. 点击区≥44px 不依赖 hover 7. 拍照/相册/文件/更换/删除/重试 8. 切换页/开菜单/预览图不丢已填 9. 320~430px + 平板竖屏 10. 完成后输出功能对照表 + 手机端测试结果。

## 四、坑(血泪)
- **改 src/*.ts 必 `npm run build` + add static/dist + bump 三个 `?v=`**(home.html 用 node latin1 改保换行,别 sed)。**`npx vite build` 单跑会清空 dist 的 home.css**,必走完整 `npm run build`。
- **共享 git 树**:别的窗口(进项采购 purchase-*)会推 origin。push 前 `git fetch + rebase origin/master`;**视觉照搬闸**只在改 `static/pos/`、`src/home/{pos,inventory,purchase}-`、`tests/visual/design/` 时触发——若 push 范围被别窗口的 purchase-* 污染会误触发,rebase 到最新 origin 即可。
- **行数棘轮** `origin/master..HEAD` 全 diff:新文件/增长文件逐个 `RATCHET-EXEMPT: <path>`(commit message 里)。
- **ui_design_lint 裸hex**:概念稿 CSS 走全站令牌(`var(--card/--ink/--line)`)别裸 hex;真要裸 hex 跑 `node scripts/ui_design_lint.mjs --update-baseline`。
- **真账号验证**:`$env:DMS_USERNAME='dmstest';$env:DMS_PASSWORD='dmstest'` · 真浏览器 harness `scripts/_dms_intake_ui_verify.cjs`(stub DMS 三场景 + 暗夜截图)。
- **dmstest 称谓只有 นาย**(测试系统数据局限,非 bug)。**OCR 把「ถ.โชคชัย 4」放进了 soi 而非 road**(extract 路/巷归类小问题,可在 id_card_extract/layer2 顺手修)。
