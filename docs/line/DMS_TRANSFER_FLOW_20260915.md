# DMS 转账流程统一（2026-09-15）

用户要求：删除买方银行采集和收方银行补填规则，三个 OA 共用“金额 → 收款银行 → 凭证”。不按缺字段追加提问。

## 实现

隔离工作树 `/Users/skin/Developer/Pearnly/pearnly-dms-transfer-flow`，分支 `codex/dms-transfer-flow`，基于远端 `c437b479`。未改共享主工作目录的其他任务文件，未提交、推送或部署。

删除来源银行选择、来源资料解析、收款资料补问、旧手工来源标记修补和编辑器银行资料输入。旧会话的已删除步骤统一迁移到 `pay_dst`，不再解释旧资料或执行旧提问。转账保留银行 ID 选择和提交前当前目录核对；未知或已删除收款银行仍拒绝。账号/分行由目录提供，缺失不阻断本地转账校验。凭证要求、其他支付渠道及 OA 会话隔离保留。

## 生产只读诊断

- LINE 官方接口回读三 OA webhook 均 active：默认 `/api/line/dms/webhook`、A `/api/line/dms/webhook/a`、B `/api/line/dms/webhook/b`，同为 `pearnly.com`。
- Cloud Run Web 实时回读为 `pearnly-web-bf19d3c0df2b-s3`、100% 流量。三入口通过同一注册表进入共用处理器。
- 当日生产会话快照：A OA 的四条银行行都有账号/分行；默认 OA 的十四条银行行都缺账号/分行。旧代码按资料完整度决定是否补问，解释了两个 OA 的步骤差异。此证据是当时会话快照，不是对所有账套主档的实时全量结论。B OA 未找到可核对的订车会话。
- 生产数据库查询只读，事务回滚并关闭；输出仅 OA、步骤、银行 ID 与字段有无，不保存客户或账户明文。

## 验证

- 全量单测：1,189 模块 / 6 分片通过，`/tmp/dms-transfer-full-unit-final.log`。
- 新增三 OA × 三种银行行（完整、账号/分行皆空、只有分行）的真实处理器模拟，验证金额直接到银行、选择直接到凭证、上传到支付结束；发送桩核对每次 OA key，编辑器归一化与原生字段映射均通过。
- CUA 浏览器操作三个对话面板：默认选 BBL（资料皆空）、A 选 SCB（完整）、B 选 TTB（缺账号），均直接要求凭证。演示使用假会话、假银行、模拟凭证和 LINE 出站捕获，执行实际 booking handlers。
- 实际编辑器资源在本地桩 API 下只出现方式、金额、收款银行。390px 无横向溢出，模拟保存请求 `extra` 只有 `dst_id`。不代表向 LINE 真正发送预览。
- 构建、Black、Ruff、ESLint（0 errors，4 条既有未使用变量 warnings）、导入、多语言引用、文件大小、权限覆盖、测试 Git 隔离、E2E 桩契约通过。未变更 SQL/schema；没有进行真实数据库业务写入验收。
- 截图：`/tmp/dms-transfer-evidence/three-oa-dialogue.png`、`/tmp/dms-transfer-evidence/editor-mobile.png`。
- 编辑器 E2E 断言已按新输入契约更新；本轮浏览器操作由 CUA 完成，未宣称整套 Playwright E2E 已运行。

## 交付与剩余边界

本地模拟：`http://127.0.0.1:18109`。启动：仓库虚拟环境 Python 执行 `tests/manual/dms_transfer_demo.py`。服务仅监听 loopback，保留供用户查看。

未部署、未做真实 LINE 真机验收、未向真实 DMS 创建测试单。因此不能宣称外部 DMS 已验证接受账号/分行为空的订车单；发布和外部业务验收仍是独立步骤。
