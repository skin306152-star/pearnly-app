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
