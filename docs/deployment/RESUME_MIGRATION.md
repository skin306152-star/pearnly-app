# 2026-09-05 迁移暂停与恢复点

用户明确要求暂停以便关闭Mac外出。**停止新的实施、构建、发布和销毁；用户回来要求继续后再恢复。** 这是暂停，不是迁移全体验收完成。正式服务依赖云端，关Mac不会关闭Pearnly网站。

## 已上线与回读

- Pearnly应用仓：`/Users/skin/Developer/Pearnly/pearnly-app`；施工worktree：`/Users/skin/Developer/Pearnly/pearnly-app-cloud-run`，分支`codex/pearnly-cloud-run`。
- Cloud Run项目`pearnly`、Singapore `asia-southeast1`；Web/Worker均100%运行完整SHA `85cc56b465bfad8e0293174dfc7ecfc0d46e36a2`。成功CD：33956960191。镜像digest和配置见[MIGRATION_STATUS.md](MIGRATION_STATUS.md)。
- 正式域名Cloudflare已切，健康/就绪正常，登录后台和历史PDF已实际打开。Scheduler每5分钟ENABLED，四类维护/队列任务各10次succeeded。最后回读16:20 Bangkok后正常。
- Web1CPU/1GiB min0 max2；Worker1CPU/2GiB min0 max2 并发1。Supabase未搬，文件私有GCS，Vertex Singapore保持。告警邮件skinzihao@gmail.com已配置，300THB限定基础设施预算，日志14天；未验证邮件实收。
- 全部业务文件1448个MD5核对无误；数据库、完整6.52GB文件归档和服务器配置已备份到私有GCS及本机，完整归档CRC32C匹配；数据库恢复/新版schema已在隔离PG验证。
- ERPNext仓`/Users/skin/pearnly-erp`及GCP `project-d0fbd530-1ee3-436d-b58`未改，VM保持RUNNING；其本机管理后台容器未停。只停止了本任务两只PG测试容器，删除了临时CloudRun存储探针Job。

## 旧实例边界

Vultr `66.42.49.213`，UUID `25a6d7e9-bbcd-4c00-958b-c771f503cdbc`。应用mrpilot已inactive、disabled；旧GitHub部署webhook inactive。**VM仍存在、仍计费、未Destroy，用户尚未确认销毁。** 核查无快照、附加磁盘、对象存储、保留IP，自动备份未启用。恢复后完成剩余验证，再给用户具体销毁确认；不得把“继续迁移”当作已经确认不可逆删除。

## 小助手安装包发布：剩余工作

独立仓`skin306152-star/pearnly-companion`，repo ID1301765903，原master `33af0fd5e381e87802c95655dc35e7709eb2a233`，VERSION仍1.1.77。现有生产安装包和latest.json保持可用，未替换安装包。

旧workflow `.github/workflows/release.yml` ID331277700已由主控disabled_manually，因为它仍向Vultr做SSH/SCP。**新流程未提交、未推送、未启用、未实际跑Windows构建或GCS发布；不可声称已完成。** 没有运行中的companion发布。

隔离worktree：`/Users/skin/Developer/Pearnly/pearnly-companion-cloud-storage-release`，分支`codex/cloud-storage-release`。保留以下WIP：release.yml、release.ps1、packaging/publish_gcs.py、tests/test_gcs_publication.py。子任务暂停说明在`/tmp/pearnly-companion-release-review/PAUSE.md`（需复制到持久工作树保存）；原始证据在同目录对应路径，不能调用旧脚本上传。

最小目标：Windows只构建并校验ProductVersion，Ubuntu下载同run artifact校验SHA/hash/size，经WIF发布私有GCS。dispatch默认staging只验证独立前缀，prod先immutable安装包、回读公开URL及哈希，再CAS发布manifest/兼容固定文件；保留可恢复旧版本。不改VERSION，不发新生产安装包，仅跑staging真实验证。

云权限已创建：

- WIF provider `projects/112074003592/locations/global/workloadIdentityPools/pearnly-github/providers/github-companion`。
- SA `pearnly-companion-publisher@pearnly.iam.gserviceaccount.com`，只获安装包bucket级objectUser；无CloudRun/DB/其他bucket权限。
- 条件严格repo ID1301765903、owner277622039、master或v标签、该仓release.yml的workflow_ref。
- 安装包桶`pearnly-app-installers-112074003592`的staging/前缀7天过期；不会清理生产manifest或releases。
- 公开URL探针要使用明确User-Agent（如Pearnly-Release-Check/1.0），默认Python-urllib会被Cloudflare拒绝，不要关闭安全设置。

## 恢复顺序

1. 读取当前状态和两个worktree的git status，确认没有其他窗口新增工作。应用线上85cc56b4无需重复发布。
2. 审阅companion WIP、完成聚焦测试与README/docs/RELEASE.md更新，检查其当前master是否前进。按无覆盖方式提交/推送；重新启用替换后的workflow，仅dispatch staging验证Windows构建、WIF、GCS完整性及公开下载，记录run证据并清理本次唯一staging前缀。
3. 应用worktree还有已通过16个定向测试的CI旧deploy-job删除（`.github/workflows/ci.yml`、`tests/unit/test_ci_workflow_contract.py`）和installers-lifecycle.json未提交；提交时不要带生成的docs/ui/UI_LINT_REPORT.txt。通用CI仍保持禁用，只移除未来误启的旧VM发布路径。
4. 更新应用安装包发布说明、MIGRATION_STATUS和STATE为最终实际状态，推送checkpoint/剩余变更并快进同步主目录。主目录11个已有WIP文件已逐一哈希确认保留，不能reset/stash/清掉。
5. 新链路验证及备份齐备后，再询问用户是否Destroy具体旧Vultr实例。只有明确确认后执行，回读实例消失/其他费用资源；退款回复是另一事项，未获发信授权。
6. 用户手机LINE/OCR与实际ERP业务验收仍单独记录，不能把HTTP200/CD绿当作USER_ACCEPTED。原有失效小助手密钥401保留，需真实设备有效绑定验收。

本机私有备份：`/Users/skin/.config/pearnly-migration/20260905/`（含敏感配置，勿提交）；云备份`gs://pearnly-app-backups-112074003592/20260905/`。主目录UI扫描报告WIP另有受限副本`main-checkout-wip/`，其他WIP未改动。
