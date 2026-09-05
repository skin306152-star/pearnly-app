# Codex 换机恢复

项目规则和四项按需技能已随 Git 保存。新电脑克隆本仓库的 `master`，以及独立 `pearnly-erp` 的 `main`，即可获得各自 `AGENTS.md` 和项目文档。

## 本机设置

1. 安装当前支持该功能的 Codex 客户端，使用自己的 ChatGPT 账号登录并选择可用的 Astra 模型。模型可用性与实验资格分别由账号和客户端决定。
2. 将 [全局协作约定](global-instructions.md) 合并到 `~/.codex/AGENTS.md`；文件不存在时直接复制，已有内容时保留个人约定并处理冲突。
3. 将 [配置片段](config.example.toml) 合并到 `~/.codex/config.toml`。已有 `[features.context_management]` 时只修改 `experimental_mode = true`，不要重复创建同名段，也不要覆盖整个配置文件。
4. 新建任务，使用实验性上下文管理。该开关让受支持的 Astra 任务使用跨窗口笔记及同任务历史检索，不是扩大模型上下文窗口，也不是跨任务记忆开关。

官方模型页说明发布初期支持 ChatGPT Plus/Pro 登录，配置参考另列 Pro Lite；Business、Enterprise 和 API Key 登录初期不支持。以实际客户端和账号能力为准。

官方依据：[模型说明](https://learn.chatgpt.com/docs/models#experimental-context-management)、[配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。

这里仅保存协作约定和无密钥配置片段。登录凭据、API Key、数据库连接、本机授权和会话数据不进入仓库；在新电脑登录并独立配置。开发环境和依赖按各仓库 `CONTRIBUTING.md` 设置。无需恢复已经移除的旧开发工具配置。
