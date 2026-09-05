---
name: erp-integration
description: 开发或排查 Pearnly 外部 ERP 推送、导入模板、Express DBF 和 Companion 集成，核对账套、真实样本与外部业务结果。
---

# ERP 集成

- 接入先核对当前公开 API；已有 API 沿用其契约，MR.ERP 等无公开 API 的既有适配使用服务端 Playwright。不要重新引入抓包、hidden field、cookie 重放的旧实现。
- 账套主体、发票买方、连接工作区与单据工作区保持各自语义；推送状态以 `erp_push_logs` 为准。先读 `docs/agent/BUSINESS_GLOSSARY.md` 与受影响 adapter。
- 对字段顺序或容器格式敏感的 xlsx/docx/xml，以已验证导入成功的真实样本对照。记录样本来源和日期；优先复用其 styles、namespaces、隐藏字段，只替换业务数据，不把真实客户数据提交到仓库。
- HTTP 200、`importpc.php` 返回值或成功提示不能证明入账；adapter 保留 verifier，通过 report/listing/detail 回查目标单据，并验证失败响应的识别。
- listing 的瞬时网络/技术错误可有限重试：等待主结果，超时可重载一次；认证、凭据解密或业务拒绝立即返回。失败不写缓存，保留脱敏错误和必要截图。
- 重试外部写入前先用单据标识/幂等键回查结果；无法排除已写入时停止重发并说明歧义，避免重复单据。
- async 路由调用同步 Playwright 等阻塞库时检查事件循环边界，按 `docs/agent/VERIFICATION.md` 验证真实异步调用路径。
- 测试使用明确的测试账套；校验网页、LINE 与 Companion 等本次涉及的实际消费者，不用某个 API 的通过代替所有入口通过。

## Companion 与 Express

Companion 是独立仓库。涉及客户端发布时读该仓 `docs/RELEASE.md` 和本仓 `docs/deployment/COMPANION_PUBLICATION.md`；客户端功能变化更新 VERSION，区分构建、staging、正式发布及真实 Windows 设备升级。仅迁移安装包发布流程不要求替换客户端版本。旧 SSH/SCP 发布已退役。

Express DBF 使用现有 BIT9 编码与 Python 适配。期初库存仅涉及 STMAS/STCRD、不生成 GL；“期初存货、漏记采购、新客户零期初”等会改变会计含义的歧义需要用户明确，不能静默选择。
