# ERP 内部录入：实施与验收

范围仅限 Pearnly 自身 `/erp`，与 ERPNext 无关。网页和 ERP LINE 数据只保存到 Pearnly，第三方推送在服务端拦截；Cowork 原有流程保留。移除销售发票、开票资料入口及对应开票操作，保留销售记录和历史数据。采购、销售的“记一笔”沿用原上传工作台、识别控制器、原图预览和字段编辑；ERP 将四步删减为上传识别、编辑、保存，保存复用原正式单转换接口。手工录入是单独入口，不再用新表单替代上传识别。

工作树 `/Users/skin/Developer/Pearnly/pearnly-erp-internal-entry`，分支 `codex/erp-internal-entry`，基础 `e4505459`。主工作树及其他任务的改动未动。

## 验收入口

- 网页：`http://127.0.0.1:7869/erp`
- 本地账号：`erp-local`；密码：`Pearnly-local-2026`；选择“本地验收公司”。这是隔离测试库账号。
- LINE 模拟对话：`http://127.0.0.1:7869/__line_sim`。菜单→采购/销售→手填或上传→打开独立 LIFF 编辑窗口→确认保存。
- 上传模拟器可明确勾选“固定识别样本”。只替换外部模型结果；实际 webhook、会话、OCR 入库、留底、编辑、确认及数据库均走真实代码。它不证明 OCR 准确率。

## 已验证

- 密码登录，从采购、销售列表进入原上传工作台；销售发票、开票资料入口移除。
- 网页手动采购带 PDF 附件保存；上传固定识别结果通过真实 `/api/ocr/recognize` 接口进入销售记录。
- LINE 手动采购、手动销售；手机宽度无横向溢出；模拟确认 503 后内容保留，显式重试保存成功。
- LINE 上传固定样本→识别草稿→编辑→内部采购保存，税前 200、税额 14、合计 214。
- 真实 PostgreSQL：内部建单、重复确认不重复建单、租户/方向限制、金额/公司校验、失败批次回滚、保留草稿、无第三方推送日志。
- 两套 Companion 队列拒绝领取 `erp_web` / `line_erp` 来源；Cowork 原有队列及托管推送测试保留并通过。
- PostgreSQL 定向测试 27 项通过；全量单元测试 1160 模块通过。TypeScript、构建、权限覆盖及相关前端机械检查通过。CI 未运行。

## 2026-09-15 用户纠正后的验证

- 实际生产 Web、Worker 的 OCR_LLM_BACKEND 均为 vertex。本地搭建漏复制该参数，错误回落 AI Studio。旧 AI Studio key 的 HTTP 429 文本是 prepayment credits depleted，不能用它判断用户的 Vertex 后付费账单。
- 本地已补 OCR_LLM_BACKEND=vertex；本地专用凭据适配通过现有 gcloud 身份取得短期访问令牌，不修改生产配置或用户全局 ADC，不落地服务账号私钥。
- 测试 PDF 的本公司税号校验位错误也已在本地样本和本地测试账套中修正；没有放宽业务税号校验。
- 未勾选固定样本，真实 PDF 经 Vertex 识别后，从 LINE 模拟对话完成内部采购保存。
- 网页采购、销售各用独立测试票据，经原 /api/ocr/recognize、原编辑组件、/api/ocr/convert-documents 保存成功；来源均为 erp_web。本地库 erp_push_logs 总数为 0。
- 手工录入单独入口保存后返回原上传工作台通过；中文桌面原图预览、390px 手机无横向溢出已检查。
- 8 项定向浏览器回归通过：采购/销售原入口、无第三方端点仍可识别保存、保留修改并显式重试、已确认不重复写入、明细声明及 Cowork 成功/失败路径。30 项 Python 测试（另 9 子测试）、2 项明细类型 Node 测试通过。
- TypeScript、构建、文件大小、词典引用、打包检查通过；lint 0 错误，177 条存量警告。
- 本机 Vision 备用通道仍未配置服务账号文件，未声称已验收该备用通道；已验收的是实际 Vertex 主识别和内部保存链路。

## 运行与隔离

专用 Colima profile `erp-internal`，容器 `erp-internal-db`，Postgres 127.0.0.1:55439。Docker 默认 context 已恢复为原 `colima`，操作任务库必须显式指定 `--context colima-erp-internal`。

工作树 `.local/env` 存本地配置，`.local/run.py` 用 `venv/bin/python .local/run.py` 启动真实 app（lifespan off，避免无关后台任务）。日志 `/tmp/erp-internal-server.log`。Python 修改后需重启；截图及浏览器验收脚本在 `.local/`。`.local`、依赖符号链接均不提交。

测试库从仓库 schema 快照及现有领域 ensure 初始化；没有生产数据，没有执行 alembic。快照缺少的 sales line classification、POS source receipt、授权和 shared Express 列已用现有 ensure 补齐。不相关 knowledge vector 在此本地库转数组并省略 hnsw。

模拟器及固定样本仅由 `.local/run.py` 安装，生产 app 不注册这些路由。网页验收脚本可通过本地 runner 的测试请求头选择固定结果，该能力同样不在生产 app。

用户尚未验收，未推送、未部署。下一步由用户本地验证；收到“没问题”后再准备统一部署。

## 类型选择与录入切换修正

按用户要求，ERP 上传复核和手填去掉库存/服务类型控件及内部保存的类型必填条件；仍校验方向、名称、数量等必要信息。现有历史类型字段保留，Cowork 和第三方推送自身的类型判断不变。两页顶部中间均为“手动录入 / 上传附件”，当前入口高亮。

本次定向验证：53 项单元测试（另 9 子测试）、7 项真实 PostgreSQL 测试、8 项浏览器回归通过；数据库测试明确省略 posting_kind 仍完成内部保存。构建、TypeScript、文件大小、词典引用、ruff 通过，lint 0 错误。仍待用户本地验收，未部署。

## 发布候选

用户于本次客户导航调整时授权整批直接上线。已合并 origin/master 的现有 DMS/LINE 改动，保留其上线行为。ERP/POS 客户列表复用原 DOM 和事件，独立为“客户”；公司主档只留账套主体，Cowork 不变。合并后 11 项定向入口回归、1192 模块全量单测、盘点 EAN/QR 浏览器回归通过。共享词典缓存及其手机页构建产物已同步。新增薄适配和保存编排属于本次明确需求，代码增长在提交说明中逐文件登记。


## 已上线（2026-09-15 16:09 UTC+7）

用户已授权整批上线，部署 SHA e342486d7deb214200b78de5e50f03f789a08ae4，Manual CD 34950160763 success。Web/Worker revision 为 pearnly-web-e342486d7deb-s3 / pearnly-worker-e342486d7deb-s3，均 100% 流量；schema pearnly-schema-7dqzr成功。完整 digest 与验证记录见部署账本。正式 ERP/POS/LINE 壳和关键资源已回读一致，用户线上实际操作与 LINE 真机验收待确认。前文“未部署”为当时本地阶段记录。本地服务继续保留，未清理用户验收数据。

## 2026-09-15 LINE 真机反馈后的修复候选

用户指出已部署版本并未沿用旧编辑器/卡片，且 iPhone 日期溢出、原生控件语言混排、草稿阻断菜单、内部 REC 编号外露。此前 Chromium 模拟结果不等于 iPhone LINE 验收；原“验证通过”范围不足。

- 删除新 LINE 简化编辑器和 Vite 入口，采购/销售、手动/OCR 共用存量 ERP batch-review 编辑器；移除目标选择与推送完成分支，只保留最终保存、丢弃。日期沿用旧字段文本编辑，不再使用新表单的原生日期/文件输入。
- 预览复用 Cowork 的既有 renderer，不修改 Cowork 文件；ERP footer 按 59e96ae1 历史样式恢复：主确定按钮、下一行 secondary 编辑及红色 link 丢弃，保留采购绿色/销售红色。确定与编辑保存均调用同一内部确认服务。
- 未完成草稿的菜单、采购、销售、重复手动和新附件路径重新发可操作卡片；成功后清 session、发送订单回执。回执运输失败不回滚已提交订单。
- 手动记录的内部备用 REC-UUID 在编辑投影隐藏，存量正式记录不批量重写。按钮/成功提示改为保存/已保存。
- 真库补测发现原采购判据把无税票手动采购归为 expense，导致收发存遗漏。只针对 erp_web/line_erp 内部采购使用 merchandise 单据，外部/Cowork 判据不变。
- 本地 WebKit + Chromium 375px：采购/销售手动编辑保存、反复菜单及采购销售操作恢复、日期输入框边界通过。两方向 OCR 固定样本直接确定/编辑保存/丢弃共六路径通过。固定样本税号改为本地验收公司的真实测试税号 0105559999996，先前不同税号被正确拒绝。
- 真实 Vertex PDF（VERIFY-164310）：识别 Notebook 数量2、税前200、税14、总额214；旧编辑器保存注入503，保留内容并显式重试成功，捕获 LINE 已保存回执。测试均是隔离本地库，无真实用户业务写入。
- PostgreSQL 回滚测试验证正式采购/销售均进入同一 stockcard movements，草稿不进入、第三方推送日志0；定向17项通过。最终全量闸与部署身份待后续追加。
- 真机 LINE 外观与实际送达仍需用户上线后确认，不能以模拟器代替；本地证据在 .local/restored-*.png 和 /tmp/erp-*-restored.log。

## 2026-09-15 手动录入参考布局（本地，未部署）

- 用户撤回本轮上线指示，要求先调整字段并本地验收。发布任务 34954484453 已取消，迁移、部署、切流均未执行；生产仍为 e342486d7deb214200b78de5e50f03f789a08ae4。当前工作树 codex/erp-internal-entry，基于 2d0c9cc4，本段对应其后的未提交布局修改。
- 按 PE/SI 截图组织上方单据/往来资料、中间商品表与页签、下方备注/金额。LINE 存量编辑器的手动记录分支与网页手动录入共用 src/erp/manual-document.ts；上传 OCR 分支仍使用原来的编辑框和预览卡。网页订单详情用同一布局只读回显。
- 字段保存在原记录 JSON；金额、数量、单位写入原采购/销售单据。参考图中的付款、部门、项目等是资料字段，没有新增支付、第三方 ERP、部门或仓库管理模块。Cowork 未改。
- 本地 PostgreSQL 10 项通过，覆盖两方向内部保存、幂等、隔离、收发存、无第三方推送及新增字段/金额：15 × 1 + 7% = 16.05；折扣 3、扣定金 2 后 10.70。
- Chromium 网页采购/销售均完成手动保存、附件上传、订单详情字段与附件预览回看。WebKit 390px LINE 两方向手动录入完成保存，随后在网页端读取同一订单，字段和金额一致；无整页横向溢出。测试输入只写入本地验收账套。
- LINE OCR 固定样本采购/销售的确定、编辑保存、丢弃六路径通过。本轮此项为固定样本回归，不冒充新增真实 OCR 调用或真机验收。
- npm run build、npm run typecheck、定向 Ruff 和 diff whitespace 检查通过。证据：/tmp/manual-pg.log、/tmp/manual-layout-browser.log、/tmp/manual-layout-other.log、/tmp/manual-ocr-regression.log，截图 .local/manual-layout-*.png。浏览器脚本仅本地验收使用，未进入生产。
- 本地服务 http://127.0.0.1:7869/erp，模拟 LINE /__line_sim。真实 LINE 手机验收、用户布局验收和新版本部署尚未完成。

## 2026-09-15 泰国日期（本地，未部署）

- 用户确认：业务日期保存/显示佛历文本，同时保留标准日期用于排序、期间与报表计算。ERP 内部记录 pages.fields 的 date/due_date/delivery_date/bill_date 保存为 DD/MM/佛历年，invoice_date 与正式单据 DATE 列保留标准历日。仅 erp_web/line_erp 转换；Cowork 不变。
- 共用佛历日期选择器覆盖手动四个日期、LINE/OCR 编辑日期及 ERP 原生日期筛选框；泰文月份/星期、佛历年、可选闰日。筛选参数仍用标准日期。只读订单日期按佛历展示。今天按曼谷日期生成。
- 内部采购导出行（Excel/Sheet）与凭证 PDF 的业务日期格式同步佛历；原始附件内容保持原样。标准日期排序与期间查询不改成年份文本比较。
- 本地验收账套 65 条旧记录转换前备份于 .local/before-business-dates.json，仅调整日期 JSON，不动金额和正式单据计算日期。生产历史记录未执行转换；未来发布需复用 business_fields 做限定来源、幂等转换并先备份。
- PG 11 项通过，包含佛历 29/02/2567 保存、对应标准闰日 2024-02-29、四个业务日期及真实 Excel 单元格 2567-02-29；导出/转换 39 项通过。Chromium 四日期选择及 390px 弹窗通过；网页/LINE 保存回显和 OCR 六路径通过。构建、类型检查、定向 Ruff、whitespace 通过。
- 本轮未执行云端 Drive/Sheet 写入或真机 LINE 验收。证据 /tmp/thai-date-pg.log、/tmp/thai-export-tests.log、/tmp/thai-date-check.log、/tmp/thai-manual-save.log、/tmp/thai-ocr.log。本地服务仍为 7869，未部署。

### 日期选择器最终构建后的样式回归修复

用户截图揭示最终构建重分包将 erp-manual-document.css 改名为 manual-document.css，HTML 仍引用旧名（本地实际 HTTP 404），导致表单与日历全无样式。此前只在最后构建前做视觉验收，不足以支持最终产物通过的表述。Vite 现在固定该 CSS 输出名，网页/LINE 引用版本更新为 manual-layout-4。修复后的最终构建再次验证 CSS HTTP 200、采购/销售 header computed display=grid、日期弹窗七列 grid、LINE WebKit，并重新查看截图 .local/fixed-css-*.png。此次未上线。

## 2026-09-15 收发存样式与内部单据编号（本地，未部署）

- 用户要求保留参考表的 11 列业务结构，整体改用 Pearnly 商业界面。商品默认折叠，白底、细分隔线、浅紫色表头；表头和内容共享列宽与对齐。
- 采购 PE、销售 SI：保存时生成 `前缀-佛历年月日-流水号`，租户内按日分配，事务 advisory lock 串行化。原始 `invoice_number` 保留，`bill_number` 用于票据号，`document_number` 用于业务号。LINE、网页共用转换层；Cowork 不使用此分支。
- 本地 62 张既有内部测试单补齐新业务号；备份 `.local/before-business-numbers.json`，仅本地固定测试租户。未修改线上单据。
- 真库 12 项内部录入测试通过，包含重复确认不重编、第二张递增、原票据号保留。转换与成本 21 项测试通过。
- Chromium/WebKit：真实报表 API、展开收起、11 列坐标与对齐、佛历、390px 横向滚动通过。网页采购保存、LINE WebKit 销售保存并回查网页详情通过。截图 `.local/stock-reference-{chromium,webkit}.png`。
- 原金额误差：入库先舍入单价再乘数量导致 3 件净额 1.00 变 0.99。ERP 分支保留原始净额；最后出清吸收舍入差额；未知历史成本不造负均价。旧 Cowork 计算分支保留。
- **未完成边界**：IR/IS 入出库单据入口与业务链路尚未实现，不能把已约定前缀说成已接通；OCR 无编码商品的唯一关联/新编码方案尚未实现。商品、库存管理页面继续暂停。生产历史编号迁移未执行，仍禁止部署。

## 2026-09-15 本轮完成：搜索、框线、IR/IS、本地商品身份

- 本轮用户明确要求：完整框线、去掉底部整块总计、日期筛选改商品模糊搜索，然后接完入库/出库。ERP 搜索按名称/编码子串、大小写及 NFKC 归一筛选显示；查询全部业务日期，不修改商品身份。每个商品保留期初、明细、小计，取消跨商品底部总汇总。
- 新 IR/IS 独立单据存于 `erp_stock_documents`；只计入 ERP 收发存派生流水，不伪造采购/销售单据。登记行、单位、部门、项目、仓库、备注与 PDF/图片附件；取消不写单据，保存后只读。SQL 迁移 `0130_erp_stock_documents`，本地已建表，未执行线上迁移。
- IR 按录入净额入账；IS 由结存成本计算，原始未知成本保留未知。出库详情重放与报表同源，补录早期入库后详情/报表成本一致。客户端 UUID 幂等，事务锁，租户/账套及入口校验，附件下载有鉴权。
- 内部采购、销售、IR、IS 保存时统一关联商品。有编码按编码匹配；无编码仅名称与单位完全一致且唯一才关联，否则新建最小商品身份并生成 P-流水号。不同单位不合并，编码/单位不符与歧义拒绝；不新增商品管理/库存页面。Cowork 不调用此逻辑。
- 本地旧测试记录已关联商品身份，备份 `.local/before-item-identities.json`。8 条用户在本地填写的期初记录按唯一名称关联对应商品，数量、成本、日期保留，备份 `.local/before-opening-identities.json`。线上历史数据未改，未来发布需安排受控历史身份回填，不能只建新表即宣称线上数据迁移完成。
- 验证：6 项 stock PostgreSQL 测试（四种来源、重试不重复、拒绝异常量/外账套、未知成本、名称/单位身份、Cowork 入口拒绝、回溯成本）；12 项原内部录入真库测试复用通过；63 项转换/滚存/报表/团队定向单测通过。TypeScript、Ruff、构建、diff whitespace 通过；alembic 单 head 为 0130。鉴权覆盖检查通过。
- Chromium + WebKit 真实本地页面：IR 保存、附件下载、IS 成本、名称和编码搜索、无匹配、取消总汇总、手机不溢出通过。两套采购/销售方向的网页及 LINE WebKit 手动保存与网页详情回读通过（脚本最后固定日志文案仍写 sales，实际第二套返回 doc_type=purchase；以响应为准）。截图 `.local/stock-flow-report.png`、`.local/stock-flow-mobile.png`、`.local/stock-in-form.png`，以及 WebKit 后缀版本。
- 例：IR 10×20=200；IS 3×20=60；结存 7 / 20 / 140。后端另测 PE+IR+SI+IS 四来源按序且只有一张采购、一张销售，出入库不会重复建购销单。
- 运行仍为工作树 `.local/run.py`，127.0.0.1:7869。未提交/推送/部署；没有真机 LINE 验收结论。前一节“IR/IS与商品身份未完成”已由本节覆盖。

## 2026-09-16：列表与商品输入匹配（本地，未发布）

- 期初位置仅做方案 `.local/opening-layout-proposal.png`：商品标题下信息栏；未修改实际收发存期初行，等用户看图。
- ERP 入库/出库列表左侧增加物料名称、编码、数量/单位；多物料单据按物料行显示金额，单据号重复链接同一详情。搜索物料名/编码/单据号。
- ERP 导航“采购 / 进项”改“采购记录”，Cowork 未改。
- 商品候选查询 tenant + workspace 权限隔离，名称/编码关键词匹配（最多20条，SQL参数化、通配符按字面）；候选选中回填编码/名称/单位，价格保留。共享手动编辑器、网页 OCR 原编辑框、LINE OCR 原编辑框接入。手动改名称清旧关联。
- 验证：stock_documents PG 7 passed（含商品搜索及跨账套拒绝），typecheck/build/Ruff/authz coverage通过。Chromium IR/IS/采购及 WebKit LINE销售候选选择通过；网页采购销售 OCR + LINE OCR 固定样本原编辑框候选选择通过。未做真实手机验收或发布。
- 当前本地服务 `.local/run.py` 7869，日志 `/tmp/erp-0916-server.log`。
- 全工作树 diff whitespace 检查发现此前 purchase-detail.ts CRLF 行提示，本轮改动路径 whitespace 检查通过；不对其他已有文件做换行重写。

### 期初位置已确认并落地
用户确认期初位置方案后，期初数量/单价/金额移至商品标题下独立浅色栏，流水表不再渲染期初行。沿用原期初值、流水计算和合计，不改后端。typecheck/build通过；浏览器验证期初栏、无重复期初行、结存140.00不变及390px无页面溢出。截图 `.local/opening-position-desktop.png` / `opening-position-mobile.png`。本地未发布。

## 2026-09-16 发布准备（用户已授权全部上线）
- 串行 Cloud Run schema Job 加入 `services/erp/history_upgrade.py`：仅 erp_web/line_erp 历史，原始行保存 tenant RLS 备份表；佛历 JSON、内部业务号、商品身份及唯一匹配期初；不改原生数量/金额/计算日期。歧义或行数异常阻断并回滚。
- 线上事务回滚演练通过：12 条记录、51 份原始行备份；事务已回滚未持久修改。受限备份 `.local/production-history-before-release.json`，不入 Git。
- 真库 24 tests passed（内部录入、库存成本、迁移幂等及保留金额），完整 pre-push 与云端发布待执行。
- 发布范围的净增长按原有 RATCHET-EXEMPT 机制逐文件记录：新增独立 IR/IS、日期、单据号、商品身份、历史迁移模块及 ERP 入口适配。未修改闸门阈值或关闭检查。临时本地浏览器脚本归档至 `/tmp/pearnly-erp-validation-20260916`，截图保留 `.local`。


## 2026-09-16 正式发布完成
- 已部署 `d307b5fdfd2eaf92fc0c6a3b48dbaf6c429b8f00`，Manual CD 35069660879 success，schema dzkvl success；Web/Worker d307b5fdfd2e-s3 Ready 各100%。digest 711a450e46f03154f3eeb7653ace08da40b32eca3a2eed6c727ea76c5cb7e381。
- 生产历史51份备份、12条佛历历史；39行数量/金额/计算日期不变；商品关联完整；6个正式健康/页面入口200、5个运行资源字节一致。
- `/tmp/erp-release-push.log` 完整闸通过；`/tmp/erp-cloud-deploy-final.log` 远程发布；`/tmp/erp-production-final-readback.log` 正式只读验证。真实手机业务验收不在自动发布结论中。
