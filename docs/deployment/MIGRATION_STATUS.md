# Pearnly 部署与迁移状态账本

更新时间：2026-09-09 01:55（Asia/Bangkok，UTC+7）。状态：**Cloud Run 已接管；DMS 多 OA（legacy + A/B）已发布，A/B webhook 端点已设置并 verify，LINE 控制台 Use webhook 开关待开启**。
2026-09-05 用户暂停后已明确回复“可以继续了”；已完成恢复后的大文件传输和安装包发布验证，历史检查点见[暂停与恢复记录](RESUME_MIGRATION.md)。
本文件是部署状态唯一正本；[CLOUD_RUN.md](CLOUD_RUN.md) 是操作规范。历史 STATE、RUNBOOK 和聊天中的“当前部署”不覆盖本页。每次发布、切流或回退须更新本页；不把配置完成当作已运行或用户验收。

## 当前部署

| 部分 | 已回读的实际状态 |
|---|---|
| Pearnly 源码 | `skin306152-star/pearnly-app`；日常目录 `/Users/skin/Developer/Pearnly/pearnly-app` |
| Pearnly 云项目 | GCP `pearnly` / `112074003592`，新加坡 `asia-southeast1` |
| 正式域名 | `pearnly.com`、`www.pearnly.com` → Cloudflare Worker `pearnly-cloud-run` → Cloud Run Web；不使用 Google 负载均衡器 |
| Web | `pearnly-web`，1 vCPU / 1 GiB，min=0 / max=2，实例并发4，超时1800秒，公开入口 |
| Worker | `pearnly-worker`，1 vCPU / 2 GiB，min=0 / max=2，实例并发1，超时1800秒，IAM 私有入口 |
| 数据库 | 原 Supabase PostgreSQL 保持；业务数据、JWT 与文件加密配置沿用。发布 Job 执行兼容性 schema 初始化 |
| AI | Vertex AI 保持项目 `pearnly`、区域 `asia-southeast1` |
| 文件 | 私有 GCS 文件、临时文件、安装包分桶；临时文件7天过期；原访问权限/加密语义保留 |
| 后台派发 | Cloud Tasks `pearnly-background`，每秒最多1次派发、并行派发1、最多5次尝试；应用有幂等回执及不确定状态 |
| 周期任务 | Scheduler `pearnly-background-recovery`，每5分钟调用私有 Worker recovery；状态 ENABLED，实际执行成功 |
| 密钥和账号 | Secret Manager `pearnly-web-env` / `pearnly-worker-env`；各自独立运行账号，只读取各自密钥 |
| 发布 | GitHub `Manual CD`（当前 `manual-deploy.yml`）→ WIF → Artifact Registry → schema Job → 候选验证 → 两服务切流 |
| 旧 Vultr | `66.42.49.213` / UUID `25a6d7e9-bbcd-4c00-958b-c771f503cdbc` 已于2026-09-05 18:25销毁；控制台回读已终止、No Instances |
| ERPNext | 独立仓库 `/Users/skin/pearnly-erp`，GCP `project-d0fbd530-1ee3-436d-b58`，VM `pearnly-erp-dev`；只读回查 RUNNING，本次未修改 |

Web 使用1 GiB而非早期讨论的512 MiB，max=2而非3；是开发阶段保守配置。min=0允许空闲缩零，并不保证请求结束立即归零；正在运行的小助手轮询和定时探针仍会产生调用。

## 正在服务的发布身份

- 完整 SHA：`ffc4bf091acd9c1ae8969a8576540a4ac89fa441`（PR #86 rebase 并入 master）。
- 镜像：`asia-southeast1-docker.pkg.dev/pearnly/pearnly-app/app@sha256:12817198e7295278ac211b2c965c2ccf4965ee1a2e063b7b4152e259e62ade5f`。
- Web revision：`pearnly-web-ffc4bf091acd-s2`，100%流量；Worker revision：`pearnly-worker-ffc4bf091acd-s2`，100%流量；两者同一镜像摘要。
- DMS 多 OA 绑定发布：[Manual CD 34264466160](https://github.com/skin306152-star/pearnly-app/actions/runs/34264466160) 成功；schema execution `pearnly-schema-7hq2v` 于 18:44:40 UTC 成功（`PEARNLY_RUNTIME_ROLE=schema` → `_boot_schema_ddl()` 含 DMS 多 OA 列/约束/会话 PK/账号表与登录票据列），Job 失败即阻断切流。候选与正式流量两服务都通过精确 SHA、镜像摘要、健康、就绪、`/internal/runtime-version` 和安装包完整下载校验后才切流。
- 发布身份独立回读：正式域名 `/api/health`、`/api/ready` 200（db/gemini/smtp/line 均 ok）；Web 运行期 `/internal/runtime-version` 返回 `ffc4bf09…`/`pearnly-web-ffc4bf091acd-s2`/`web`；Worker 匿名 403（IAM 私有），由 CD 用 ID token 验证同一 SHA/镜像/revision。切流后两服务无 ERROR 级日志。
- A/B 凭据挂载进入声明式 render：`deployment/cloud-run/render_service.py` 为 Web、Worker 和 schema Job 声明 `LINE_DMS_A_CREDENTIALS=pearnly-line-dms-a:1`、`LINE_DMS_B_CREDENTIALS=pearnly-line-dms-b:1`（`secretKeyRef`，版本钉死），避免 `gcloud run services replace` 抹掉手工 `--update-secrets`。两个 secret 的 `roles/secretmanager.secretAccessor` 只授 `pearnly-web`/`pearnly-worker` 两个运行账号；未改动 `pearnly-web-env`/`pearnly-worker-env` 与其他 runtime secrets。
- 生产只读 schema 核对：`line_dms_bindings`/`line_dms_binding_codes`/`dms_line_sessions`/`line_dms_login_tickets` 均有 `channel_key`，票据另有 `binding_id`；`dms_account_line_channels` 存在；`dms_line_sessions` 主键 `(tenant_id, channel_key, line_user_id)`；唯一索引 `ux_line_dms_bindings_channel_line(channel_key, line_user_id)`。现有 4 条绑定全部 `channel_key='dms'`，账号 OA 分配 0 行，登录票据 0 行——未新建真实业务单据、未改真实账号密码/余额/OA 分配。
- A/B webhook 端点经官方 API 设置并回读：A `https://pearnly.com/api/line/dms/webhook/a`、B `…/webhook/b`，`POST /v2/bot/channel/webhook/test` 两次均 `success:true, statusCode:200`。`GET …/webhook/endpoint` 仍 `active=false`：**Use webhook 开关只能在 LINE Developers Console/OA Manager 打开，Messaging API 无对应写接口**，是本次唯一剩余外部配置。空 `events` 签名请求实测 legacy/A/B 正确 secret 均 200，跨 OA secret 与错误签名 400 `line_dms.bad_signature`，未知 OA 路径 404。
- A/B 富菜单已发布并回读：`pearnly-dms-basic-v3-liff-dms_a` = `richmenu-c97def834b597a1c2dd2761956df3341`、`pearnly-dms-query-v3-liff-dms_a` = `richmenu-16e37a4db26738a89deee9a821a967c8`；`…-dms_b` = `richmenu-2bf651f21047bdf138a94eb85eba4f84` / `richmenu-1575d12fa340d3025c35a9a879f28a92`；两个 OA 默认菜单均为各自 basic 菜单，图片与仓库源 MD5 一致。A/B 未配 LIFF，菜单入口按实现降级到 `https://pearnly.com/dms`（`/api/line/dms-booking/config` 对 `dms_a`/`dms_b` 返回 `available:false` 且不回落 legacy LIFF，未知 channel 404/403 失败关闭）。
- legacy OA 兼容保持：webhook 仍为 `https://pearnly.com/api/line/dms/webhook` 且 `active=true`；`pearnly-dms-basic-v3-liff`=`richmenu-4fabd60b180dd4e0dd08cc0d5bbc05ae`、`pearnly-dms-query-v3-liff`=`richmenu-db70029ab3bef9b815913432746bac78` 与默认菜单未变，旧 v1/v2 菜单仍在。正式域名 `/dms/`、`/home/dms-booking`、`/api/health`、`/api/ready` 200，`dist/dms.js`、`dist/dms.css`、`dms-i18n-th.js`、`dms-roster.js`、`admin.js`、`admin-i18n.js`、`dms-booking-api.js`、`dms-booking-edit.js`、`dms-booking-i18n.js`、`dms-credentials.js` 与发布源字节一致；operator/roster/records API 无身份 401 `auth.missing_token`。
- 本地验证：pre-push 机械闸全绿（含生产 Python 全量分片单测、prettier/eslint/vite build/dist 一致/cachebust/UI 与防屎山棘轮；`services/line_platform/liff.py` 的 +15 行按 `RATCHET-EXEMPT` 记录）。真库 pg smoke `test_line_dms_binding_pg_smoke.py` 因本机 Docker/Colima 不可达**未执行**，改为发布后对生产库只读核对上述列/约束。**A/B 的 LIFF 与手机真机绑定/回复验收未做**，A/B 无 LIFF 时入口降级到 `/dms`，不得声称手机自动登录已验收。详见[DMS 多 OA 记录](../dms/MULTI_LINE_OA_2026_09_08.md)。
- 上一版本（历史）：SHA `3a9db541e7b16345212c485a05989a97f02c65b2`，镜像 `…@sha256:13ded394f281b9415485832a7f052e38171e065746e3f56abef70692acaf8f74`，Web/Worker revision `pearnly-{web,worker}-3a9db541e7b1-s2`，已不再服务流量。
- LINE DMS 菜单4手机恢复LINE内打开：[发布34115905413](https://github.com/skin306152-star/pearnly-app/actions/runs/34115905413)成功，schema execution `pearnly-schema-k4qzk`成功，两服务候选/正式SHA、镜像、健康、就绪及完整安装包校验通过，均接管100%流量。完整pre-push含1163模块通过，定向16项单测和6项跨平台浏览器测试通过。LINE两个v3-liff菜单创建并回读，默认四项；现有4个绑定同步后为1个四项、3个五项，与实时权限一致。菜单3外部地址、桌面入口、登录回跳及此前保存修复保留。正式LINE内回跳200/no-store；手机LINE真机打开和实际保存仍待用户验收。详见[菜单4记录](../dms/BINDING_INTEGRITY_2026_09_07.md)。
- LINE DMS 密码保存与认证恢复发布 [34111323561](https://github.com/skin306152-star/pearnly-app/actions/runs/34111323561) 成功；schema execution `pearnly-schema-l7x6v` 成功，两服务候选/正式身份、健康、就绪及完整安装包验证通过，各接管100%流量。补齐保存事务的绑定租户 RLS 上下文；无效 LINE 身份返回独立401，页面提供有界登录恢复与手动重试。完整 pre-push 1,163模块通过，325项 DMS 测试（含真实 PostgreSQL HTTP 保存、加密落库、读回与旧绑定拒绝）及27项浏览器回归通过。正式域名三份脚本与发布源字节一致、页面版本引用正确、空 LINE token 返回401 `dms_booking.line_auth_required`。当前用户绑定仍存在但 active_jti 为空，未签发替代会话，因此发布后带身份 GET 核验未完成；未写真实密码，用户重新登录和真机改密验收待确认。详见[后续修复记录](../dms/BINDING_INTEGRITY_2026_09_07.md)。
- LINE DMS 修复发布 [34104299567](https://github.com/skin306152-star/pearnly-app/actions/runs/34104299567) 成功；schema execution `pearnly-schema-vhlzn` 成功，Web/Worker 候选和正式服务的版本、健康/就绪、流量及安装包完整校验通过。本地完整 pre-push 含 1,162 个测试模块通过，DMS 浏览器回归 19 项通过，另有真实 PostgreSQL 重绑与并发确认测试。正式凭据和草稿 API 拒绝旧令牌/旧绑定（401），当前绑定可只读取得自身配置（200）；三份关键前端脚本与候选字节一致。默认底部菜单四项，当前三个绑定的四项/五项/五项分配与实时权限一致。用户手机及真实 DMS 写单未验收；原测试 A/B 已停用解绑，未恢复或猜测密码。详见 [绑定修复记录](../dms/BINDING_INTEGRITY_2026_09_07.md)。
- Cowork 入口与盘点删除发布 [34029239117](https://github.com/skin306152-star/pearnly-app/actions/runs/34029239117)：schema execution `pearnly-schema-955g8` 成功，两端候选验证及正式 Worker 验证通过并各切到 100%。最后正式 Web 的 `/api/ready` 探针发生 TLS 握手 `Connection reset by peer`，因此 workflow 状态为失败；随后对同一 SHA／digest 使用仓库原 `verify_release.py` 分别复跑正式 Web、Worker，两次均 exit 0，完整版本／镜像／流量／健康／就绪／安装包大小和 MD5 校验通过，无放宽条件或重新部署。正式域名 readiness 200，`cowork_delete=1856fdbe316a` 命中新 Web；Cowork 与 home HTML 引用新版 landing26／main12060027，ui4／CSS4／词典stocktake4和 bundle 字节一致。Cowork 超管快捷进入和新登录不再强制跳 Earn，也不覆盖管理后台会话；盘点网页卡片可确认后永久删除该任务及全部关联记录，权限为 recon.create，事务锁与租户／账套隔离保持。74 项定向单元和真库测试、67 项入口浏览器、5 项会话隔离、盘点删除与扫描浏览器、1159 模块完整推送闸通过。未删除真实用户盘点；普通 Chrome 与用户实际删除验收待确认。
- 账面位置映射与对比发布 [34027810317](https://github.com/skin306152-star/pearnly-app/actions/runs/34027810317) 成功，schema execution `pearnly-schema-8fxjl` 成功，候选与正式身份／就绪／完整下载检查通过。每次扫码重新带出该商品账面仓库／位置，空值保留空白，不沿用上一笔；历史修改仍保留该笔实际值。泰语汇总新增账面／实际仓库和位置及各自对比，逐笔明细保留配对；撤销记录不参与汇总，未盘点和账面未提供分别标记。修正手机表单横向溢出。17 项定向单元、真实 EAN／QR 浏览器、1158 模块完整推送闸通过。本次无 SQL／schema 变更；沿用已有权限与逐笔记录。正式域名 health／ready 200，`stocktake_places=30afc1a3a3f9` 日志命中新 Web；counter.js?v=3、CSS?v=3、词典 stocktake-3、main.js?v=12060026 与 main.css stocktake-3 回读字节一致。真实 LINE 真机验收仍待用户确认。
- 数量显示修正 [34025488705](https://github.com/skin306152-star/pearnly-app/actions/runs/34025488705) 成功；schema execution `pearnly-schema-slgdb` 成功，两端候选与正式身份／就绪／完整下载检查通过。盘点网页与手机、新旧任务的账面、实盘、差异、逐笔数量及修改输入去掉末尾补零，10.000000 显示 10，2.500000 显示 2.5；保留实际小数精度和编号前导零，不改数据库数值。定向浏览器与前端推送闸通过。正式域名 readiness 200，`stocktake_numbers=b816f291146f` 日志命中新 Web，ui.js?v=3、counter.js?v=2、main.js?v=12060025 回读字节一致。
- 扫描逐笔盘点发布 [34024627136](https://github.com/skin306152-star/pearnly-app/actions/runs/34024627136) 成功；schema execution `pearnly-schema-rzxsq` 于 09:29:56 UTC 成功，新 Web／Worker 候选与正式版本的精确 SHA、镜像、健康／就绪和完整安装包检查通过。两服务已各接管 100% 流量；正式域名 `stocktake_v2=1741b99b9c79` readiness 请求日志命中新 Web revision，HTTP 200。手机壳内容一致（Cloudflare 追加的统计脚本单独识别），camera.js、counter.js、ui.js、CSS、共享扫码 bundle、main.js 与词典按页面实际缓存参数回读字节一致。
- 本次新增 0124 逐笔记录与审计结构，新任务一行一个商品、条形码或内部 QR 精确匹配、实际仓库库位自由选择／输入、累计与修改撤销、泰语商品汇总／位置明细导出。旧任务保留 legacy 数据与行为。修正 WASM 同步初始化返回值兼容并同步 POS 离线缓存版本；真实 EAN／QR、连续扫码、网络重试、修改撤销、位置记忆、语言草稿、POS 扫码与离线回归通过，独立 PostgreSQL 验证累计、审计、并发和 RLS。最终完整 pre-push 1157 模块与所有静态／构建闸通过。此前缓存版本格式与离线缓存指纹闸曾拦截，修正后重新通过；没有绕过检查。发布运行 34024613313 因输入 SHA 错误在云端变更前取消，实际成功运行以上述 34024627136 为准。
- 泰语结果导出修正 [34020406001](https://github.com/skin306152-star/pearnly-app/actions/runs/34020406001) 成功；schema execution `pearnly-schema-vj7fk` 成功，两端候选及正式版本/健康/就绪/完整安装包检查通过。正式域名 readiness 200。结果导出接口统一泰语，旧网页发送 `lang=zh/en/ja` 也不改变表头；定向 15 项通过，其中实际 HTTP 响应 XLSX 验证全部 11 列泰语及差异数值，完整 pre-push 1156 个模块通过。真实用户再次导出验收待用户确认。
- 菜单与泰语模板发布 [34019557598](https://github.com/skin306152-star/pearnly-app/actions/runs/34019557598) 成功；schema execution `pearnly-schema-k2s7s` 成功，两端候选及正式版本/健康/就绪/安装包完整下载检查通过。正式域名 readiness 200，`stocktake_menu=c96e24294d56` 日志命中新 revision；浏览器回读两种新菜单图标均 200 且字节一致。LINE 默认 Rich Menu 已更新为 `richmenu-0aa42f054b8a47a8d1d9e7db9012e8be`，两个区域和图片回读一致，旧 v1 菜单保留；四语 Flex validate API 通过。模板默认泰语，保留英文列标识兼容；本地五条真实条码测试模板通过实际导入解析器。前一运行 34019375397 在镜像构建阶段取消，以合并新增的泰语表头要求，未进入生产变更。
- 首版盘点发布 [34018589884](https://github.com/skin306152-star/pearnly-app/actions/runs/34018589884) 成功；schema execution `pearnly-schema-sxww8` 成功，两端候选与正式服务的健康、就绪、精确 SHA/镜像及安装包完整下载校验通过。正式域名 health/ready 200，`stocktake_release=ea1d3e1607cc` 请求日志命中新 Web revision；手机入口壳、mobile.js、ui.js 与本地发布字节一致。本地 pre-push 1156 个测试模块及静态闸通过。网页入口 `/cowork#/stocktake`，LINE 沿用现有 Cowork 菜单；实际成员登录、真实业务与 iOS/Android 相机验收由用户自行进行，见 [盘点记录](../cowork/STOCKTAKE-V1.md)。
- 上一 OCR 发布 [33974005122](https://github.com/skin306152-star/pearnly-app/actions/runs/33974005122) 成功，schema execution `pearnly-schema-m6928`、两端候选/正式安装包完整校验通过。正式域名 health/ready 均 200，nonce `ocr_release=7dc72a755075` 的请求日志命中新 Web revision。旧镜像 674909a0 为迁移基线，以下记录保留作历史证据。
- 22:19:52 Bangkok 原子更新 OCR 策略并写操作审计：invoice=economy（3.1-lite→3.8 LOW）；其余现有 OCR task=enterprise。银行/GL/VAT 扫描件使用冻结 Enterprise 财务适配器；ID、SalesVAT 发票、通用网格保留专用 Schema 使用 3.8；结构化文件保留原生解析。不能将选 A 档解读为每个文件都会收费调用 Document AI。
- Web/Worker 各自 runtime secret v2 新增 Enterprise 四项配置：项目112074003592、处理器6c7dfffac937fcd9、新加坡、共享9 RPM；代码固定 v2.1.1，不用处理器默认 v1.0。两 SA 新增 Document AI API User，其他运行配置不变。Worker 身份单页合成探针成功；不代表全部业务文件人工验收。详细边界见 [OCR 记录](../ocr-integration-progress-2026-09-05.md)。
- [成功的 GitHub 发布运行33962463833](https://github.com/skin306152-star/pearnly-app/actions/runs/33962463833)。同镜像schema execution `pearnly-schema-mmsws`于11:11:11 UTC确认完成；Web/Worker候选及正式流量均通过完整安装包校验，18:13 Bangkok完成切流回读。上一已验证版本为85cc56b4（CD33956960191）；它尚有大文件传输限制，不作为当前传输能力基线。
- 服务地址：`https://pearnly-web-112074003592.asia-southeast1.run.app`；私有 Worker `https://pearnly-worker-112074003592.asia-southeast1.run.app`。
- 2026-09-05 15:28 左右切流。正式域名 readiness nonce `cutover-20260905-0828` 的 Cloud Run 请求日志确认命中初次接管的 `pearnly-web-c3797e182785-s1`，HTTP 200；www health 也为200。
- 当前版本已补齐四项Express进程内schema-ready：每次启动只读验证列、约束、RLS、策略、函数与触发器，失败阻止启动。85cc56b4阶段在09:13:51 UTC以nonce `final-readiness`回读无token heartbeat恢复401；674909a0已保留该修复并再次回读401，直接匿名Worker仍为403。
- 历史85cc56b4发布曾因错误SHA输入取消33956937444，未进入云端变更；随后33956960191成功。当前674909a0的发布记录为33962463833，两者不可混用。
- 账本/CI文档提交可能晚于线上镜像SHA；文档更新不自动重发容器，不能据仓库HEAD推断线上版本。

## 域名与旧发布入口

2026-09-07 18:02 Cloudflare Worker 最终限定修复：Dashboard 版本 `bd70ddb6` Active Latest。此前本任务发布的全局禁缓存版本 `efb574fb` 及保留源站头的全局版本 `1b4f4fab` 已撤回；**仅 DMS 密码页面三个别名、带 credentials=dms 的 /home 与 /login LIFF 回跳、DMS auth/config/credentials 三个 API 路径使用 no-store**。其他路径恢复到本任务前 `c2d015f8` 的转发和缓存逻辑，未修改域名 Cache Rules 或 Browser Cache TTL 配置。正式 DMS 页/config/回跳均 DYNAMIC/no-store，AI/ERP/Cowork/Daily/POS/cashier/首页和健康接口已回读原缓存行为，均200。687条非DMS路由声明的离线差分测试确认转发请求、cache选项、响应头/体与旧Worker相同；这不是687项真实业务验收。该次边缘修复完成时Cloud Run镜像为 `bc6ce06f574a`。详见[诊断与范围纠正](../dms/BINDING_INTEGRITY_2026_09_07.md)。


Cloudflare Worker 两条 route 为 `pearnly.com/*` 和 `www.pearnly.com/*`，均 fail closed。没有新增 `*.pearnly.com/*`，避免接管其他租户子域名。源站在 Worker 中明确指定 Cloud Run Web。

2026-09-05 DNS 回读：主域名由旧 A `66.42.49.213` 改成 proxied CNAME `pearnly-web-112074003592.asia-southeast1.run.app`；www 保持 proxied CNAME `pearnly.com`。原有 MX、SPF、DKIM 保留。旧 IP 不再是网站 DNS 源站。

小助手安装包来自独立仓库`pearnly-companion`。旧SSH workflow已替换，新流程提交`ed48b1a1295f01e2f9d8b4ed7afbe0eb39f3e5ce`已推送，workflow331277700已重新启用，staging验证[33961319994，第2次attempt](https://github.com/skin306152-star/pearnly-companion/actions/runs/33961319994)已成功：Windows构建、WIF、GCS完整回读和正式域名完整下载均通过。第1次attempt发现HTTP/1大响应限制并正确阻断；应用674909a0修复后只重跑publish job，沿用原Windows artifact，未重建或替换生产包。生产仍为1.1.77，未替换安装包；操作见[安装包发布](COMPANION_PUBLICATION.md)。

通用CI仍停用，ci.yml已移除旧VM deploy job并保留所有验证job，避免未来恢复CI时误触发历史部署。

旧 GitHub webhook `625195648`（`/internal/deploy`）已 inactive；Cloudflare 阻断 `/internal/`，新应用也不提供旧 VM 发布路径。旧实例已销毁，SSH别名 `pearnly-prod` 已退役；旧IP可能重新分配，不得再连接或发布。不要重新建立第二套周期消费者。

## 数据与恢复证据

- 旧应用停用后，本地源文件与 GCS **1448个业务文件逐一 MD5 核对，0不一致**；最终 rsync 因重复复制已相同对象被中断，以独立完整哈希复核为准。
- 安装包 `PearnlyCompanion-Setup.exe` 为62,905,102字节，云端 MD5 与源文件一致；latest.json 可从正式域名读取。
- Supabase 初始备份 `supabase-before.dump` 4,518,313字节，SHA256 `69dbb6d5c80c38397f4bdb9213d044cccb220aaca96a0380e96ed0395e7c92cd`；在隔离 PostgreSQL17+pgvector 容器中严格恢复 public schema/数据并执行新 schema 成功。5张原有零策略 RLS 表保持启用，未为迁移全局关闭 RLS。
- 切流前另存 `supabase-pre-cutover.dump`（4,518,312字节）；已上传。恢复试验针对初始备份，未把第二份声称为另一次完整恢复试验。
- 完整旧文件归档 `legacy-files-complete.tar.gz`，6,521,306,807字节，gzip 完整性通过；GCS 对象已在08:29:57 UTC创建，CRC32C `Uz0lgg==`，独立本地CRC32C计算与云对象匹配。完整归档包括历史安装包备份。
- 旧 nginx、systemd和环境配置存于私有 `legacy-server-config.tar.gz`，4,777字节；不把密钥写入 Git。
- 私有云备份前缀 `gs://pearnly-app-backups-112074003592/20260905/`；本机受限目录 `/Users/skin/.config/pearnly-migration/20260905/`。失败的`.partial`中间文件已移入本机废纸篓，不能用于恢复。
- 真实 Cloud Run 独立 Job 完成三处挂载的跨实例写入/读取哈希验证、Chromium启动和测试对象清理；不是仅本地单元测试。测试Job已删除，两只专用PG验证容器已停止；ERPNext管理后台容器未清理。

| GCS bucket | 用途 |
|---|---|
| `pearnly-app-files-112074003592` | 持久业务文件与 uploads 前缀 |
| `pearnly-app-temp-112074003592` | var 临时任务文件，7天过期 |
| `pearnly-app-installers-112074003592` | 当前安装包与 latest.json，由应用转发下载 |
| `pearnly-app-backups-112074003592` | 迁移备份，版本保留；旧版本30天清理 |
| `pearnly-app-build-112074003592` | 构建临时源，7天过期 |

所有桶均新加坡、统一桶级权限、阻止公共访问。业务文件桶启用7天soft-delete保护。Cloud Run 本地临时磁盘不是备份。

## 验证与告警边界

- 启动修复：40个聚焦测试及24个subtest通过；真实PG副本12种安全结构破坏均阻断启动，只读线上目录预检通过。
- 本地：当前发布的完整 pre-push 已通过（1156个测试模块与静态闸）；定向真实 PostgreSQL 任务状态测试与备份恢复分别执行。GitHub通用CI仍停用，不把本地通过写成远程CI通过。
- 远程：上述 GitHub CD成功；镜像内 Python compileall、Chromium启动、schema Job、候选健康/就绪/精确版本及最终流量检查通过。
- 线上：正式域名健康/就绪、页面与静态文件检查通过；保留登录态的管理后台可读取；真实历史记录详情和迁移前PDF在浏览器中正确渲染，未保存修改或推送ERP。真实 Cloud Tasks OIDC 探针到私有 Worker 返回200。
- Scheduler启用后，数据库已回读 `maintenance`、`queue.ocr`、`queue.recon`、`queue.steward` 各10次 succeeded。这里只证明调度/消费；无待处理业务时不等于完成一次真实OCR或外部ERP交易。
- 原有小助手每3秒 lease 返回401，旧 Vultr 日志也存在；不能通过迁移放宽认证。真实设备需使用有效绑定验收。历史 ERP retrying 记录（2026-06-20）保留，不冒充已修复。
- 邮件通知渠道已配置为用户指定的 `skinzihao@gmail.com`，channel `9342288420654696611`；4条告警已启用：公开readiness、内存85%、队列积压、任务失败/不确定日志。没有主动发送测试邮件，未确认邮件实收。
- Uptime每15分钟，至少两个地点失败触发；15:45回读六个探测地点的最近样本均为true。任务日志规则不是所有LINE/ERP业务失败的全覆盖。详见 [监控配置](../../deployment/cloud-run/monitoring/README.md)。
- 预算实际为 **300 THB/月**，50%/90%/100%实际用量及100%预测告警；仅项目pearnly的Run、Storage、Artifact Registry、Tasks、Scheduler、Secret Manager，排除Vertex和Supabase。预算不是硬停机或总费用上限。
- 项目 `_Default` 日志保留14天。历史“$1–3/月”等仅初步估算；真实支出受任务时长、客户端轮询、存储、流量和构建影响。
- **用户手机 LINE、OCR 文件处理和实际 ERP 写后回查仍未验收，不标记 USER_ACCEPTED。**

## 恢复后补齐的传输与安装包验证

- 原HTTP/1容器的约63MB安装包下载被平台限制为500；同时原业务支持100MiB单文件和超过32MiB的多文件批次，不能把迁移后的上限降到32MiB。
- 当前Web/Worker均为Hypercorn单进程ASGI、h2c容器入口，Web→Worker强制HTTP/2。保留原代理头处理；HTTP/1大响应使用流式传输，HTTP/2和HEAD保留长度。Cloudflare原有额度和应用自身上传限制仍适用。
- 新增发布检查会对Web/Worker候选及正式流量完整下载安装包，核对GCS大小/MD5，并验证generation未变；任一步失败阻断切流。本次四次检查均实际通过。
- 本地38个聚焦测试与20个subtests通过；34MiB（35,651,584字节）在直接Hypercorn与Web代理的HTTP/1、HTTP/2链路均完整回读。
- 使用同一已发布镜像在两个临时IAM私有CloudRun服务上做真实34MiB验证：直接Worker和经Web→Worker，各用HTTP/1与HTTP/2客户端，共四条链路；容器均回读HTTP/2、正确大小及SHA256 `23dfbc08258fa16e92089de9eeedd0d199590c6983c0deebeca11b3baffab7b2`。无业务写入。首次新IAM授权传播期间转发返回403/503，授权不变的后续完整验证通过。两服务已删除，匿名调用曾分别验证403。
- Companion构建来源`ed48b1a1295f01e2f9d8b4ed7afbe0eb39f3e5ce`，VERSION/ProductVersion=1.1.77，staging包62,904,235字节，SHA256 `5e6b3d1e3bb98c98cf2f961d336c75148d38a02c64d70fc500cc78eea4d3cc6d`。这是测试构建，不是新的正式客户端发布。
- 生产原安装包仍62,905,102字节、generation `1788593866085056`；latest.json仍86字节、generation `1788593862422782`。两者MD5/大小/generation与staging前逐项一致。仅清理本次`staging/33961319994-1/`和`-2/`对象，未清理生产releases或其他发布。
- Companion本地发布/更新相关17 tests和5 subtests通过；1项PySide6 UI测试在Mac缺依赖跳过，未冒称Windows用户设备验收。真实Windows构建及ProductVersion检查由上述GitHub run完成。

## 退役与回退规则

用户明确回复“销毁”后，2026-09-05约11:25 UTC（18:25 Bangkok）在Vultr控制台核对IP及UUID并执行Destroy。回读显示“Your VPS has been terminated”和“No Instances”。此前已核查无快照、附加磁盘、对象存储、保留IP，自动备份未启用。旧实例不再新增实例使用费；已产生账单及余额退款另行结算，本次没有提交退款回复，也没有获得退款批准。

销毁后正式域名 `/api/ready` 回读ready=true，db/gemini/smtp/line均ok；GCP项目pearnly仅保留Web/Worker两个服务，latestReady均为674909a0bd51-s1。独立ERPNext VM `pearnly-erp-dev` 回读RUNNING，未修改。

后续 Cloud Run 回退只切到已验证、与当前schema/持久文件兼容的 revision。施工用 preflight revision不是验收基线。数据库/文件破坏性变更需配套恢复，不能只换旧镜像。

旧VM已不存在，不能再通过旧IP或systemd回退。未来如需恢复VM部署，必须另行建立新资源、暂停Scheduler并处理在途任务，验证兼容数据库和完整文件恢复，再协调单一消费者及流量；不得使用迁移前文件覆盖切流后的新增数据。备份恢复须在隔离环境验证后单独决策，禁止覆盖现有Supabase来“试一下”。
