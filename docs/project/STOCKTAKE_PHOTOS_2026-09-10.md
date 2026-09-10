# LINE 盘点图片与差异导出

状态：本地实现及定向验证完成，未合并、未推送、未部署。工作树 `pearnly-stocktake-photos`，分支 `codex/stocktake-photo-export`，基于 `e4505459`。

## 本次行为

- LINE 内的现有 Cowork 盘点页面和桌面复用上传组件。数量下方增加选图、拍照、预览和保存前移除；每条盘点记录最多 5 张，图片可选。
- 图片与数量在同一事务保存，操作回执包含图片摘要，响应丢失后的同请求重试不重复计数。更正时可追加图片，已保存的证据保留；作废图片仍可从明细查看，商品汇总不计入作废附件。
- 服务端重新解码、转正、缩放并重编码 JPEG，去除原始元数据。归一化图片存于有租户和账套 RLS 的 `cowork_stocktake_photos`，避免依赖实例临时磁盘；任务删除通过外键级联清理图片。
- 原始选图上限 25 MB，浏览器压缩到长边 1280；服务端每张输入及保存上限 1 MiB，5 张/记录，导出图片总量上限 80 MiB，超限明确失败。
- Excel 商品汇总的数量、仓库、位置差异分别标黄；记录明细标黄仓库/位置差异，未盘点及作废记录不冒充数量差异。
- 汇总和明细新增泰语“查看图片”内部链接，跳到同一 XLSX 中的图片页，并可返回汇总或明细。不使用外网 URL、临时签名或宏。

## 验证

- 隔离 PostgreSQL 16 临时容器中验证回执重放、事务回滚、五图上限、更正保留、作废、删除、直接 RLS、跨账套拒绝及 HTTP 附件读取权限。
- `test_stocktake`、`test_stocktake_location_report`、`test_stocktake_entries_pg_smoke`、`test_stocktake_delete_pg_smoke`、`test_stocktake_photos_pg_smoke` 通过；新 HTTP 用例增加后单独复验受影响模块。
- 现有 `_stocktake_verify.cjs` 在真实页面路由和发布产物上通过：手机相册/拍照 input、预览、移除、六图拒绝、切语言保留、保存后查看，以及原有扫码、响应丢失重试、更正和作废流程。LINE SDK 和业务 API 为 fixture，浏览器不等于真机 LINE 验收。
- Excel 使用真实 `reports.workbook` 输出，经 openpyxl 重新读取确认媒体数量、内部链接目标、标黄范围和作废排除；无桌面 Excel 原生打开证据。Artifact Tool 能预览表格文字与标黄，但该次导入预览未显示内嵌图片，因此不把它记成图片视觉验收。
- build、ESLint（存量警告，无错误）、TypeScript、ruff、black、四语/引用、权限覆盖、页面路由/压缩壳、附件入口缓存映射测试通过。未执行推送前全量分片测试及发布候选检查。

## 发布时剩余

发布需按当前 Cloud Run 规范执行。`services.cloud_runtime.schema` 已调用 stocktake schema gate，新 gate 追加图片表；独立迁移记录为 `0125_stocktake_photos`。先执行串行 schema gate，再切新代码流量。此次没有运行生产迁移。

发布后需要真实 LINE（尤其 iPhone）拍照/相册与保存确认，以及用户常用 Excel 客户端点击附件、离线查看内嵌图片确认。
