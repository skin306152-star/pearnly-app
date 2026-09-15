# DMS 客户网页编辑器与称谓修复

用户授权：客户卡“修改”改为订车同款编辑器；保存后发新卡，再点击更新才写 DMS。同步修复女性称谓。删除旧逐字段修改并部署。慢队列问题暂不处理。

## 实现

- 共用 LIFF shell、OA 身份绑定、客户字段与地址级联；`editor=customer` 只载入客户表单。
- 保存实时复核 DMS 主档和客户，重算差异/审批权限；更新 nonce 后同步确认 LINE 接收新版卡。发送失败恢复原草稿，旧 nonce 与跨 OA 更新被拒。
- OCR `นางสาว` 与 DMS `น.ส.` 映射至同一编号；称谓、生日参与原有客户差异确认。
- 删除 `edit_flow.py`、旧字段菜单/提示/文字校验/应用和重查重入口。历史 edit/field/cancel 事件只转网页；遗留 editing 会话忽略新文本，保留原草稿并换新 nonce。
- 不改变 Cloud Tasks 队列、DMS 实时读取要求、ERPNext 或其他任务文件。

## 本地证据

- DMS 定向单测 430 项通过，2 项既有环境跳过；客户路由真实异步 HTTP 验证未阻塞事件循环。
- 隔离 PostgreSQL 13 项通过，含客户 review nonce/CAS、state 与三个 OA 隔离；测试容器已删除。
- Playwright 4 项通过：三个 OA 客户页输入/保存与订车转账编辑回归。未向真实 LINE 或 DMS 写入测试资料。
- 新建/差异卡使用 LINE 官方 validate/reply，只验证载荷，不发送消息。
- 前端已构建，同批更新编辑 JS/i18n 缓存引用及 dist HTML。

## 发布

2026-09-15 12:54（UTC+7）发布完成。应用 SHA `328b90e426eb2099ee9dd5c36c9a08995f9687a6`，Manual CD [34933957608](https://github.com/skin306152-star/pearnly-app/actions/runs/34933957608) success。完整 pre-push 1,190 模块/6 分片通过。

Web `pearnly-web-328b90e426eb-s3` / Worker `pearnly-worker-328b90e426eb-s3`，均 Ready、各 100%，同镜像 digest `sha256:3ca4a4c48ba01fc4db53b06c9dcf0b6cb78aff938dbd251c03c629083665d628`。schema `pearnly-schema-qzl9s` 成功，候选和正式 SHA/健康/就绪/完整安装包下载验证通过。

正式域名 HTML/JS/i18n 与本地候选逐字节一致；三个 OA available；health/ready 200。最初 urllib 资源探针 403，改用 curl 对公开同源资源回读成功，没有改动访问控制。证据 `/tmp/customer-release-readback.json`、`/tmp/customer-deploy-complete.log`、`/tmp/customer-release-push.log`；手机布局截图 `/tmp/dms-customer-evidence/`。

未向真实 DMS 写测试资料，未发送真实 LINE 测试消息。真实手机和外部业务验收仍待用户确认。


## 按钮外观回归修复

2026-09-15 用户真机发现修改按钮变高：新 URI 按钮没有继承旧 height=sm。已改为复用 `_btn` 后只替换 action；新增测试锁定其余所有属性一致，并检查整张差异卡三个按钮高度与样式。

版本 `9cbe603e49c5788e39e650a4c163371e679f890d` 已发布，Manual CD `34935332766` success，Web/Worker 各 100% Ready。全量 1,191 模块通过，三个 OA 的官方载荷验证通过；未发送测试卡，实际 LINE 新卡视觉验收仍待用户。旧聊天卡不会因部署而重绘。


## 收工清理

用户授权只清理本任务工作树与残留。代码、发布身份和验证结论已归档并推送；线上仍为 `9cbe603e49c5788e39e650a4c163371e679f890d`，记录提交晚于应用镜像。

停止本任务 18109/18110 模拟服务，移除工作树 `pearnly-dms-transfer-flow` 与本地分支 `codex/dms-transfer-flow`。清理本任务 `/tmp` 脚本、日志、截图、生产只读摘录和忽略测试缓存；上文 `/tmp` 路径仅作历史取证索引，收工后不再保留。测试 PostgreSQL 容器先前已删除，匿名卷经创建时间与 `pearnly_ci_dms_attempts` 标记核实后清理。通用 PostgreSQL 镜像、其他任务容器/卷和共享主目录的 ERP 改动保留。

部署成功与真实新卡手机验收仍分别记录，未伪造用户验收。清理不更改生产服务、Cloud Tasks 或真实 DMS 数据。
