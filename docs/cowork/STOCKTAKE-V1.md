# Cowork 库存盘点第一版

## 入口与操作

网页入口是 `/cowork#/stocktake`，位于 Cowork「对账中心」下面。网页只包含列表、新建弹窗和详情。新建时上传统一 `.xlsx` 模板，校验通过后立即开始；不提供覆盖账面数据的接口。导入失败整批不落库。

LINE 在现有 Cowork 菜单卡「上传单据到 ERP」之后增加「库存盘点」跳转按钮。沿用 `LINE_COWORK_LIFF_ID`（以及现有 `LINE_LIFF_ID` 回落）和已绑定的 Cowork 成员身份；无需新增 LIFF 应用。菜单 URI 为既有 LIFF ID 加 `flow=cowork-stocktake&draft=list`，既有 `/home`、`/login` 主重定向选择手机盘点壳。没有修改或发布 LINE Rich Menu 图片，也没有向客户发送消息。

手机选择公司和盘点任务，扫描条形码或搜索商品编号，选择商品所在仓库／库位，输入数量后保存并继续。同码多库位必须选定具体记录；成功盘点后记住当前仓库／库位。商品记录匹配仅使用本次导入的数据，不访问 POS 商品或 ERP 库存。二维码不在本版范围。

相机使用现有 `PearnlyScanCamera`（POS 同一共享引擎），没有修改 `static/scan/**` 或 `static/pos/**`。不能启用摄像头时可手动搜索。POS 登录、公司体系和界面没有用于盘点；网页复用 Cowork 壳，手机复用 Cowork LINE 登录流程与主词典、公共按钮和设计令牌。

## Excel 约定

模板表头固定为：

| 字段 | 内容 | 必填 |
| --- | --- | --- |
| product_code | 商品编号，Excel 文本格式，保留前导零 | 是 |
| product_name | 商品名称 | 是 |
| barcode | 条形码，Excel 文本格式 | 否 |
| warehouse | 仓库 | 是 |
| location | 库位；空值代表未细分库位 | 否 |
| unit | 单位 | 是 |
| book_qty | 账面数量，可负数，最多 6 位小数 | 是 |

表头批注提供中、泰、英、日说明。单次最大 5 MB、10,000 行，解压总量上限 40 MB；拒绝公式、无效数量、数字格式的编号和条码，以及重复的「商品编号＋仓库＋库位」。匹配保留大小写，不模糊归一化商品身份。

实盘数量必须大于等于 0，最多 6 位小数。未盘点保存为 NULL；差异仅在实盘有值时计算 `实盘－账面`。导出包含全部记录，实盘与差异在未盘点项中为空；表头按网页当前语言显示。导出的文字显式作为文本，避免公式注入；超过 Excel 15 位有效数字的数量以文本保留精度。

## 权限、并发与数据边界

沿用 Cowork 现有权限：`recon.view` 查看，`recon.create` 新建、盘点与结束，`recon.export` 导出。公司权限沿用现有成员分配范围，所有业务查询绑定 `tenant_id + workspace_client_id`；缺少公司头拒绝。LINE 每次 API 调用重新检查活跃绑定与成员权限，盘点令牌不会用于其他业务 API。

盘点任务、明细、计数历史分别保存于 `cowork_stocktakes`、`cowork_stocktake_items`、`cowork_stocktake_counts`，均有租户／账套 RLS。账面数据不会流入库存更新或 ERP 推送逻辑。

新建请求使用客户端 UUID 和原文件摘要保证重试不重复创建，不能用同一请求 ID 替换快照。保存使用记录版本检查；重复提交同一值只记一次，不同值的旧版本写入返回冲突。每次修改保留前值、后值、版本、操作者和 UTC 时间。

保存与结束均锁定盘点任务行，避免结束后继续写入。结束动作幂等，保留结束人和时间。结束允许保留未盘点项，弹窗会显示未盘点数量并明确这些项不会变成 0。

## 本地验证与交付边界

- 单元与真实 PostgreSQL 定向验证覆盖模板、公式、前导零、Decimal、NULL／0、租户与账套隔离、RLS、导入重试、计数重试、并发冲突、结束锁定，以及真实 HTTP 导入／保存／导出链。
- 现有 POS 扫码流水线、共享引擎纯逻辑、页面路由与外壳、Cloud schema 导入边界回归通过。另已重跑 cowork／ERP 入口隔离浏览器检查，60 项通过。
- `scripts/_stocktake_verify.cjs` 在本地真实页面路由和生产构建产物中验证首次深链、导航位置、新建弹窗、筛选、冲突输入保留、零数量、结束、导出、中泰语言、手机布局、真实 EAN 视频解码、相机释放及拒绝权限回落。业务 API 与 LINE SDK 在浏览器测试中使用桩；后端 SQL 和 HTTP 由独立 PostgreSQL 用例验证。
- 浏览器截图在 `tests/e2e/_artifacts/stocktake/`。扫码视频用 `venv/bin/python scripts/_scan_ean_y4m.py /tmp/stocktake-camera.y4m` 生成。

代码包含 `0123_cowork_stocktake` 迁移，以及现有 Cloud Run 串行 schema job 的接入。本次没有执行线上迁移、推送或部署。发布时应遵循现有 Cloud Run 流程。LINE iOS／Android 真机相机与实际成员登录验收仍待发布后完成。
