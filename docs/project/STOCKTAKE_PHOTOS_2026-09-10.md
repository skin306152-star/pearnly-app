# LINE 盘点图片与差异导出

状态：2026-09-10 17:58 Bangkok 已上线。工作树 `pearnly-stocktake-photos`，分支 `codex/stocktake-photo-export`；原基于 `e4505459`，发布前合入最新主线 `c1ac00cf`。上线完整 SHA 为 `4f7aa0bd048c5c0306820178195137c9c3aedb70`。

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
- build、ESLint（存量警告，无错误）、TypeScript、ruff、black、四语/引用、权限覆盖、页面路由/压缩壳、附件入口缓存映射测试通过。发布时完整 pre-push 1169 模块/6 片及所有机械闸通过。

## 发布与验收

[Manual CD 34468147393](https://github.com/skin306152-star/pearnly-app/actions/runs/34468147393) 成功。schema execution `pearnly-schema-6czdf` 于 10:54:12 UTC 完成，Web/Worker 候选及正式校验均成功，包含安装包完整下载。两端各 100% 流量到 `pearnly-{web,worker}-4f7aa0bd048c-s2`；digest `sha256:185d2a4a3f09b145b39f86a6837c1a824fa85ef9255ff0359842a98dca446df2`。

生产 6 个 JS/CSS/词典文件与发布字节一致，LINE/桌面壳的版本引用正确，ready=true，正式域名探针日志命中新 Web。匿名照片读取 401。没有写入真实账套测试图片/数量。

发布后需要真实 LINE（尤其 iPhone）拍照/相册与保存确认，以及用户常用 Excel 客户端点击附件、离线查看内嵌图片确认。

## 18:22 导出边框修正

用户反馈黄色单元格没有横竖线，原因是此前只设置填充，没有显式 Border。现汇总、明细全表及图片页文字信息行设置四边细线，保留标黄及附件链接。

17 项定向测试验证实际序列化后的 XLSX 边框与标黄，导出预览通过；完整 pre-push 1169 模块/6 片通过。[Manual CD 34470260139](https://github.com/skin306152-star/pearnly-app/actions/runs/34470260139) 成功，当前线上 SHA `2a954babe1471af869a7f69eb1d3fdb6bdf37fac`，镜像 `sha256:37ef28c5e4e3aae18570ddc50ff1a1f071dac4dbef0305c370978bbfc203af12`，两端 `pearnly-{web,worker}-2a954babe147-s2` 各 100% 流量；候选/正式检查及正式域名回读通过。用户重新导出后的查看器验收待确认。
