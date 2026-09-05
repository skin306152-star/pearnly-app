# Companion 安装包分发状态与发布入口

2026-09-05已验证：独立仓发布代码ed48b1a，GitHub staging运行33961319994 attempt2成功，原Windows构建产物经WIF/GCS/正式域名完整回读；生产1.1.77安装包和manifest保持不变。首次attempt发现的大文件平台限制已由应用674909a0修复，详见[MIGRATION_STATUS.md](MIGRATION_STATUS.md)。

Pearnly Web 的 Cloud Run 迁移同时改变了 Windows 小助手的安装包存储位置。客户端源码在独立仓库 `skin306152-star/pearnly-companion`，不在 ERPNext 仓库，也不随 Pearnly Web 容器自动构建。

## 当前下载位置

| 项目 | 当前值 |
| --- | --- |
| 私有存储 | `gs://pearnly-app-installers-112074003592`，项目 `pearnly` / 新加坡 |
| Web/Worker 文件挂载 | `/app/static/companion`，只读 GCSFUSE，支持子目录 |
| 更新检查 | `https://pearnly.com/static/companion/latest.json` |
| 固定安装包兼容 URL | `https://pearnly.com/static/companion/PearnlyCompanion-Setup.exe` |
| 登录后下载 API | `/api/companion/installer`，继续读取固定文件名 |
| 新版本不可变路径 | `/static/companion/releases/<version>/<source_sha>/PearnlyCompanion-Setup.exe` |

bucket 保持私有，安装包通过应用静态路由公开下载。不要在该 bucket 写入密钥、客户端配置或用户数据。文件元数据缓存禁用；Cloudflare 对 `latest.json` 返回 `Cache-Control: no-store`，带 `v` 的版本化静态 URL 可缓存。

## 独立发布链

Companion 正本为独立仓库 [docs/RELEASE.md](https://github.com/skin306152-star/pearnly-companion/blob/master/docs/RELEASE.md)。新工作流 `.github/workflows/release.yml` 拆为 Windows 纯构建和 Ubuntu WIF 发布：

1. Windows 从该 run 的精确 commit 构建，校验 `ProductVersion == version.py`，输出 `dist/PearnlyCompanion-Setup.exe` 和 `dist/release.json`（版本、source SHA、SHA-256、字节数）。Windows 无云发布凭据。
2. Ubuntu 获取同一个 build job 的 artifact，重新验证 source SHA、SHA-256 和大小。
3. 默认 staging 只写 `staging/<run_id>-<attempt>/<source_sha>/`，验证 GCS 回读及正式域名完整下载，不改生产 manifest 或固定文件名。`staging/` 前缀已有 7 天过期清理策略；生产文件和 `releases/` 不受影响。
4. 生产先上传和验证 `releases/<version>/<source_sha>/` 不可变文件，保留旧 manifest/安装包，再使用 generation 条件更新 `latest.json`，最后更新兼容固定文件名并回读。每一步失败即停止。

发布账号为 `pearnly-companion-publisher@pearnly.iam.gserviceaccount.com`，仅具安装包 bucket 对象权限；WIF provider 为 `projects/112074003592/locations/global/workloadIdentityPools/pearnly-github/providers/github-companion`，限制到 Companion 仓库及发布工作流。

先执行 staging：

```bash
gh workflow run release.yml --repo skin306152-star/pearnly-companion --ref master -f target=staging
gh run list --repo skin306152-star/pearnly-companion --workflow release.yml --limit 5
```

使用返回的准确 run ID 检查 Windows 构建和 Ubuntu 公开下载验证。正式发布另选 `target=prod`；`v<version>` 标签也会触发生产发布，不可用于测试。状态账本须分别记录“代码已改”“Windows 构建通过”“staging 上传/公开回读通过”“生产发布”和“用户设备已升级”，不得混称完成。

## updater 兼容契约

`latest.json` 保留 `version`、`url` 两个字段。当前 updater 接受相对 URL，按数字版本比较，只提示更高版本；额外 SHA-256 字段不会被客户端执行验证。新的 `url` 指向含 version 与完整 source SHA 的不可变对象，旧客户端无需修改即可下载。

`packaging/release.ps1` 新入口为 `-BuildOnly`；它只生成安装包与元数据，没有 `SkipUpload` 参数。不加 `-BuildOnly` 会立即报错。不要再使用 `RELEASE_PROD` / `RELEASE_PDIR` 或向旧 Vultr 执行 SCP。

## 旧状态与本次迁移边界

2026-09-05 只读核查到 Companion 基线 `33af0fd5e381e87802c95655dc35e7709eb2a233`、VERSION `1.1.77`。旧 `packaging/release.ps1` 没有 BuildOnly/SkipUpload，第 4/5 步直接 SSH/SCP `root@66.42.49.213`；旧 workflow `331277700` 的 tag/prod 和 staging 都依赖该机器，staging 仅换旧机目录。该旧发布方式必须停用，不能因 Web 已迁移而继续使用。

迁移保留原生产安装包和客户端版本。本次发布链替换不 bump VERSION，也不等于发布或安装一个新客户端版本。独立仓库新流程的实际验证 run/SHA、旧 workflow 切换及生产安装包是否保持不变，统一记录在 [MIGRATION_STATUS.md](MIGRATION_STATUS.md)。

回退安装包使用独立仓库发布文档的 generation 条件与归档；不要启动旧 Vultr 作为分发源。指针回退不会让已升级的客户端自动降级。
