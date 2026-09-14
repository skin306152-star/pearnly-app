# 老板 LINE 工作协调集成

目标：一个新增工作入口，在 LINE 内完成老板派发、查看、编辑、评论、状态调整和验收。底部 Rich Menu 与呼出菜单同步；功能选择使用 LINE 原生 Quick Reply，预览只保留确认、编辑、取消、返回。系统对话固定泰语，编辑选项支持 th/zh/en/ja。

## 实现

- 分支 `codex/line-owner-coordination`，基于 `02b01718`。隔离目录 `/Users/skin/Developer/Pearnly/pearnly-line-owner-coordination`。
- 复用原生 WeKan 看板、列表、任务、成员、评论、附件及审计。Pearnly PostgreSQL 仅保存独立 LINE 草稿和通知回执。
- 每次操作核对当前 Pearnly owner、有效 LINE 绑定和原生看板管理员权限；签名限定方法、路径、正文、有效期。
- 明确确认后才写入；原生操作回执防止重复创建，不确定结果保留草稿。
- 日期按曼谷输入、UTC 保存。原生附件接口保留上传校验和 afterUpload 审计；下载重新核对当前绑定和看板权限，链接五分钟有效。
- 原生状态活动触发老板待验收/阻塞通知；通知使用稳定回执和 LINE retry key。没有在真实 LINE 发送验收消息。

## 验收环境

`tests/manual/line_owner_demo.py` + `.html` 为交互模拟器，默认端口 18099。真实业务处理器连接任务专用 PostgreSQL（15439）与正式 Dockerfile 构建的 WeKan（18196）。LINE 发送与测试员工 SSO 是替身，所有业务存储是真实隔离实例。

任务临时目录 `/tmp/pearnly-line-owner`。Docker compose 项目 `pearnly-line-owner`；文件卷 `pearnly-line-owner-files`。勿动其他任务资源。

## 当前验证与剩余工作

- Cowork LINE 单测 132 项通过，4 个 PG 测试在未提供数据库时跳过；随后专用 PG 4 项单独实际运行通过。
- 真实 native 集成覆盖创建、编辑、附件、评论、提交验收、确认完成和重复确认。附件实测发现的 write/writeAsync 版本差异已经修正。
- 四语言预览保持泰语、原生快捷按钮和旧按钮失效已有回归测试。
- 本机正式 Dockerfile 镜像已构建，继续核对下载字节、员工回报和老板通知，再完成机械闸及发布。
- 准备候选提交，尚未推送或部署。不得把模拟验收当作手机 LINE 真机验收。

- 浏览器实测：员工原生提交、老板退回、员工补充、老板接受，最终原生状态为完成；36 字节 CSV 下载与上传 SHA256 一致。
- 快速回退再提交时发现旧活动误触发通知，已增加最新活动与目标列表核验及回归测试。历史/附件已补原生分页。
