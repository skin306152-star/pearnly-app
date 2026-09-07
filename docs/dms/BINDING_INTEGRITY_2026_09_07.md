# LINE DMS 重新绑定身份修复

菜单 4 曾复用浏览器的共享 Pearnly JWT：LINE 已绑定到操作员 B，浏览器仍以 A 保存凭据。菜单 3 也走同样的旧令牌路径。底部 Rich Menu 使用全局五项菜单，与聊天菜单的查询权限判断不一致。

## 修复范围

- 菜单 3、4 与订车编辑页每次用当前 LINE 身份换取独立的内存令牌。令牌签入绑定 UUID；服务端逐请求核对绑定、用户、租户和操作员启用状态。旧令牌和重新绑定前的表单拒绝提交，不自动换身份重试密码写入。
- 重新绑定轮换 UUID；解绑与重绑在事务内撤销会话及登录票据。状态和凭据更新与绑定变更使用相同的事务锁，旧任务无法覆盖新操作员的草稿或凭据。确认 nonce 改为单条 SQL 原子消费。
- 后台任务进入时及外部 DMS 登录等待后复核身份；查询和审批复核对应权限。已开始的外部系统写入无法由解绑回滚，本次不宣称提供跨系统事务。
- 默认 Rich Menu 为四项；有查询权限的操作员分配五项。绑定、解绑和权限修改触发持久任务同步，周期维护补偿。菜单服务未发布时同步报错，不降级到全局开放查询。旧菜单保留以便回退。

## 已取得的验证

- DMS 单元及真实 PostgreSQL 测试 319 项通过，覆盖旧浏览器令牌、旧任务、撤权、会话/票据撤销和并发确认。最后补充的当前身份 HTTP 保存与外部登录期间重绑测试亦通过。
- PostgreSQL 在独立本地测试容器运行：20 个并发确认只有一个取得 nonce；旧凭据事务无法写入；重绑与旧草稿写入并发后无旧草稿残留。
- 浏览器新回归 7 项、原页面回归 12 项通过。新回归覆盖桌面/移动页面、四语失效提示和不自动重试。LINE SDK 与 API 使用测试桩，不等同于用户手机验收。
- 前端产物已构建，缓存版本与源码同批变更。完整推送闸和生产结果在发布完成后追加。

操作员 A 的原密码没有可恢复的审计值；用户已确认自行重新录入。不会猜测或复制其他操作员的密码。生产验收不往真实账套写测试单据，不主动发送测试 LINE 消息。

## 发布验证

- 候选源码：`efaff0d51fdee2d7f83e5f24dd6196f710f193a1`。完整 pre-push 通过，包含 1,162 个测试模块、格式/权限/产物检查；通用 GitHub CI 未启用。
- 2026-09-07 生产回查：原 A、B 用户记录均已停用，操作员档案移除，原 LINE 绑定已解除；没有向这两个旧账号回填或猜测凭据。
- LINE 菜单已发布：默认四项 `richmenu-0414060aa04e7164370495af0576e440`，有查询权限的五项 `richmenu-a24f1195b1706ebd34c899c5477b2fe0`。三个当前绑定回读结果为四项/五项/五项，与实时权限全部相符。旧默认菜单 `richmenu-a60183b2d306faaf15ca3ee90537573b` 保留。

- [Manual CD 34104299567](https://github.com/skin306152-star/pearnly-app/actions/runs/34104299567) 成功。schema execution `pearnly-schema-vhlzn` 成功；Web/Worker revision 分别为 `pearnly-web-efaff0d51fde-s2`、`pearnly-worker-efaff0d51fde-s2`，两端 Ready 且 100% 流量。
- 两端镜像 digest 相同：`sha256:9722166534e520dbf830f101dcda347dfd55520767b31c72c228423ee8f5e276`。发布流程对候选/正式服务的 runtime SHA、健康/就绪和安装包完整下载均验证通过。
- 正式域名 health/ready 成功，凭据页 API、凭据脚本、四语词典与候选逐字节一致。线上只读探针：旧共享令牌及旧绑定令牌访问凭据/草稿均 401；当前有效绑定读取自身凭据配置为 200。探针没有轮换用户会话、修改用户行或发送 LINE 消息。
- 用户手机上的 LINE 登录、重新绑定及真实 DMS 写单仍未验收，不标记 USER_ACCEPTED。临时本地 HTTP 服务和 PostgreSQL 测试容器已回收。
- 新版本的周期维护已产生并完成 3 个 `dms.menu_sync` 任务，均为 `succeeded`；菜单同步不只是在本机调用 API 成功。

## 17:06 密码页失败的后续修正

- 用户手机请求在 17:05:11、17:05:26 的凭据 GET 返回 403，17:05:32 的 LINE 身份交换也为 403；当时没有成功进入密码表单。旧前端丢掉身份交换错误码，且加载异常复用了“保存失败”，没有恢复按钮。历史日志未区分 LINE 票据失效与未绑定，不能断言这次 403 的具体身份原因。
- 另用生产只读查询确认：在实际 `pearnly_app` 角色下，仅设置 `app.current_user_id` 无法读取自己的绑定；同时设置正确 `app.current_tenant_id` 后可以。上一轮在 endpoint 保存事务加入绑定检查，却遗漏租户上下文，会令实际保存返回失败。现补齐当前绑定的租户上下文，保留用户归属与绑定 UUID 校验。
- 新增真实 PostgreSQL RLS 测试，走凭据 HTTP GET → PUT → 加密落库 → GET 回读，另一个操作员配置不变。相同测试换回上一版写入函数必然得到 500；新实现为 200。测试使用隔离数据库与本地临时加密密钥，未修改真实用户凭据。
- LINE 身份验证失效改为独立错误码；外部浏览器最多自动重新登录一次，重复失败显示四语“重新验证 LINE”按钮。绑定、停用、加载失败与保存失败分别显示；重新验证会清空旧表单，不能自动重发密码。
- 本地 325 项 DMS 测试（含真实 PostgreSQL）、8 项 LIFF 测试、15 项身份/恢复浏览器测试、12 项原页面浏览器测试通过。新回归包含登录过期、重复失败不循环、明确恢复、错误码保留和旧表单清空；真实手机 LINE 验收仍需用户执行。

## 17:34 密码保存与认证恢复发布

- 发布源码 `bc6ce06f574ac34392285efecef2206f92a4b4d4`，Manual CD [34111323561](https://github.com/skin306152-star/pearnly-app/actions/runs/34111323561) 成功，schema `pearnly-schema-l7x6v` 成功。
- 镜像 digest `sha256:b131901e702fb9f1810859a13c5bc0fc22d325fa1d66ef86766bf20f099be58c`；Web/Worker revision 分别为 `pearnly-web-bc6ce06f574a-s2`、`pearnly-worker-bc6ce06f574a-s2`，均 Ready 且100%流量。流水线候选和正式版本/健康/就绪/安装包校验通过。
- 完整推送闸1,163模块通过；325项 DMS 测试、27项浏览器回归通过。正式域名 api6/credentials4/i18n3 脚本字节及 HTML 引用一致，空 LINE token 实测401和明确的重新认证错误码。
- 发布后只读确认用户仍 active 且仍绑定，但 active_jti 为空；没有可复用会话，带身份 GET 探针因此停止，未签发新会话或写真实密码。此前生产只读 RLS 诊断与本次真库保存回归证明修复路径，实际手机重新登录与改密仍待用户验收。

## 17:50 Cloudflare 缓存阻止手机取得认证恢复修复

- 用户继续报告失败。17:37、17:41 iPhone Chrome 的真实请求均停在 `/api/line/dms-booking/auth` 401 `line_token_invalid`，未进入密码保存 PUT。17:31最后一次旧页面加载命中 `efaff0d51fde-s2`；后续重复只有认证请求，不能把这一阶段认定为保存事务失败。
- LINE Server API 只读回读确认当前 LIFF `2010411313-K4TWQwYo` 的 endpoint 为 `https://pearnly.com/home`，scope 包含 `openid` 和 `profile`。电脑当前 LINE 会话真实登录后，认证和配置读取均200，表单可见；未填写/提交真实密码。
- 对同一正式入口实测：Cloud Run 源站 `Cache-Control: no-cache, no-store, must-revalidate`，正式域名却返回 `CF-Cache-Status: EXPIRED` 和 `Cache-Control: max-age=14400`；认证 config GET 同样被改成4小时浏览器缓存。线上 Worker `c2d015f8` 的非静态分支使用 `cf.cacheTtl: 0`，这不是禁止存储，导致手机可继续加载旧页面。
- 已将非版本静态资源的请求改为 `fetch(..., {cache: 'no-store'})`，响应也设置 `Cache-Control: no-store`。仅 `/static/` 下有版本参数且非 `latest.json` 的 GET 保留原缓存行为。Cloudflare Dashboard 发布版本 `efb574fb`，回读 Active Latest；Cloud Run 镜像保持 `bc6ce06f574a`。
- 正式域名回读密码页面、认证配置、未认证配置读取均为 `DYNAMIC` / `no-store`，版本脚本仍为 HIT。`node --test deployment/cloudflare/worker.test.mjs` 两组测试通过，涵盖页面/API/POST/latest.json、静态缓存和禁止路径。Node 的流式 Request 需要 duplex，仅测试适配，未改生产传输逻辑。
- 为避开手机已保存的旧 URL，提供带 `refresh=20260907-1750` 的当前页面链接。17:51:17 UTC+7 手机实际认证200，17:51:18配置读取200；保存结果继续以真实 PUT/用户反馈为准。
