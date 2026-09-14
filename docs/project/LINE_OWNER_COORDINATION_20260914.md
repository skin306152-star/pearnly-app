# 老板与员工 LINE 工作协调

## 已实现并发布

老板邀请员工 → 同账套员工账号与原生看板成员 → 员工在 LINE 内使用账号密码登录并绑定 → 老板派工 → 员工开始、评论、附件、提交验收 → 老板退回 → 员工修正重提 → 老板确认完成。

工作入口只新增一个，底部 Rich Menu 与呼出菜单同步。功能选择使用 LINE 原生 Quick Reply；预览仅确认、编辑、取消、返回。对话泰语，编辑器支持泰/中/英/日，时间默认泰国且不显示城市，内部 UTC 保存。

复用原生 WeKan 任务、成员、评论、附件与审计；PG 保存 LINE 会话、共享状态映射、幂等回执。每次操作重新验证绑定、账套成员有效性及原生权限；员工仅访问自己的任务，不能派工、验收或重开完成任务。附件下载重新检查身份，有效期五分钟。邀请密码不进入聊天草稿；重试参数不一致拒绝，绑定不静默覆盖其他有效身份。老板手动转发邀请，系统不擅自发送账号密码。

## 发布身份

- 分支 `codex/line-owner-coordination`；隔离目录 `/Users/skin/Developer/Pearnly/pearnly-line-owner-coordination`，基于 `02b01718`。共享主目录的其他任务改动保留。
- 应用 `98bb3ce6c6d5facc6aa33e1cf114052f66781362`；Web/Worker 对应 revision 均 Ready、100% 流量。
- 原生服务源码 `bc1ed19b98ae8326f6a2e2afe99b7280edad0ec3`，运行密钥 v5，health ok。后续应用修复未改原生源码。
- LINE 默认 Rich Menu `richmenu-7ee0e0bb6400cd8446d9f517e1b205a9` 已发布，actions 与图片逐字节回读一致。
- 完整镜像 digest、快照及工作流证据见[部署账本](../deployment/MIGRATION_STATUS.md)。后续纯文档提交不重发容器。

## 验证与发现的修复

- 完整 pre-push 1,187 个模块/6 分片和机械闸通过。
- 真实隔离 PG 验证会话、回执、过期员工通知过滤、邀请同账套、密码哈希、重试冲突、绑定幂等与拒绝覆盖。原生集成验证老板全流程、员工隔离及禁止操作、分页、附件和重复确认。
- CUA 浏览器完成中英文邀请/绑定表单及老板、员工全闭环。最终原生状态为完成，员工只能看历史与附件。36 字节 CSV 下载与上传 SHA256 一致：`5a42412aa4923ebd1740ec38eafcf60e1d612fcf5136e0b2ad787637d0a4d53d`。
- 实测修复原生附件 writeAsync 接口兼容、快速退回重提的过期活动通知、LIFF 配置嵌套读取，以及 LINE 不接受空 fillInText。旧发布在切流前取消；修复后的最终 50 个真实消息 payload 及 Rich Menu 通过官方验证接口，没有发送真实测试消息。
- 最终源码再次跑邀请、绑定、派工、员工附件/回报、等待真实原生活动通知、退回重提和完成；证据 `owner-flow-final.json`、`employee-flow-final.json`、`seed-final-demo.log`、`official-line-validation-final.log` 位于 `/tmp/pearnly-line-owner`。
- 正式域名 health/ready、连接页、LIFF 配置 200；线上连接页 JS 与本地一致；未登录绑定 401。发布工作流成功不等同手机验收。

## 演示与未覆盖边界

演示地址 http://localhost:18099/，可切换老板/员工。`tests/manual/line_owner_demo.py` 使用任务专用 PG 15439、原生 WeKan 18196；仅 LINE SDK/验证/运输与演示登录会话为替身，业务存储为真实隔离实例。没有在生产创建测试员工或任务。

Docker 项目 `pearnly-line-owner`、文件卷 `pearnly-line-owner-files`、运行目录 `/tmp/pearnly-line-owner` 和当前演示服务保留供用户查看。勿清理其他任务资源；PG/Mongo 使用临时存储，重建容器会丢失演示数据。

手机 LINE 真实登录、消息送达、原生按钮与菜单显示尚未验收。不能宣称所有场景绝无错误；已通过上述覆盖范围内的验证。
