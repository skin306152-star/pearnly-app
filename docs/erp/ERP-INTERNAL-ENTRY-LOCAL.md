# ERP 内部录入：本地验收

范围仅限 Pearnly 自身 `/erp`，与 ERPNext 无关。网页和 ERP LINE 数据只保存到 Pearnly，第三方推送在服务端拦截；Cowork 原有流程保留。移除销售发票、开票资料入口及对应开票操作，保留销售记录和历史数据。采购、销售的“记一笔”支持手动填写及上传识别，共用内部保存服务。

工作树 `/Users/skin/Developer/Pearnly/pearnly-erp-internal-entry`，分支 `codex/erp-internal-entry`，基础 `e4505459`。主工作树及其他任务的改动未动。

## 验收入口

- 网页：`http://127.0.0.1:7869/erp`
- 本地账号：`erp-local`；密码：`Pearnly-local-2026`；选择“本地验收公司”。这是隔离测试库账号。
- LINE 模拟对话：`http://127.0.0.1:7869/__line_sim`。菜单→采购/销售→手填或上传→打开独立 LIFF 编辑窗口→确认保存。
- 上传模拟器可明确勾选“固定识别样本”。只替换外部模型结果；实际 webhook、会话、OCR 入库、留底、编辑、确认及数据库均走真实代码。它不证明 OCR 准确率。

## 已验证

- 密码登录，从采购列表进入新表单；销售发票、开票资料入口移除。
- 网页手动采购带 PDF 附件保存；上传固定识别结果通过真实 `/api/ocr/recognize` 接口进入销售记录。
- LINE 手动采购、手动销售；手机宽度无横向溢出；模拟确认 503 后内容保留，显式重试保存成功。
- LINE 上传固定样本→识别草稿→编辑→内部采购保存，税前 200、税额 14、合计 214。
- 真实 PostgreSQL：内部建单、重复确认不重复建单、租户/方向限制、金额/公司校验、失败批次回滚、保留草稿、无第三方推送日志。
- 两套 Companion 队列拒绝领取 `erp_web` / `line_erp` 来源；Cowork 原有队列及托管推送测试保留并通过。
- PostgreSQL 定向测试 27 项通过；全量单元测试 1160 模块通过。TypeScript、构建、权限覆盖及相关前端机械检查通过。CI 未运行。

## 本地 OCR 限制

真实 PDF 识别试跑：现有 Gemini 密钥返回 quota，回落 Vision 因本机没有服务账号凭据而失败。没有修改生产 OCR 模型或配置。固定样本只证明接入和保存流程；真实图片/PDF OCR 尚未验收。本地网页正常上传不启用固定样本，仍需要有效的本地 OCR 凭据/额度。

## 运行与隔离

专用 Colima profile `erp-internal`，容器 `erp-internal-db`，Postgres 127.0.0.1:55439。Docker 默认 context 已恢复为原 `colima`，操作任务库必须显式指定 `--context colima-erp-internal`。

工作树 `.local/env` 存本地配置，`.local/run.py` 用 `venv/bin/python .local/run.py` 启动真实 app（lifespan off，避免无关后台任务）。日志 `/tmp/erp-internal-server.log`。Python 修改后需重启；截图及浏览器验收脚本在 `.local/`。`.local`、依赖符号链接均不提交。

测试库从仓库 schema 快照及现有领域 ensure 初始化；没有生产数据，没有执行 alembic。快照缺少的 sales line classification、POS source receipt、授权和 shared Express 列已用现有 ensure 补齐。不相关 knowledge vector 在此本地库转数组并省略 hnsw。

模拟器及固定样本仅由 `.local/run.py` 安装，生产 app 不注册这些路由。网页验收脚本可通过本地 runner 的测试请求头选择固定结果，该能力同样不在生产 app。

用户尚未验收，未推送、未部署。下一步由用户本地验证；收到“没问题”后再准备统一部署。
