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

待候选 pre-push、Manual CD 与生产身份回读后补充。真实手机和外部业务验收不由单测/HTTP 200 代替。
