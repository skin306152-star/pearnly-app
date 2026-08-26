# 🛠️ Pearnly · 运维手册（RUNBOOK）

> **整顿 REFACTOR-G2 · 2026-05-27 初版 · 2026-08-26 部署链路改版**（webhook 停用 → CI 精确部署）
> 把散在 `CLAUDE.md/CLAUDE.md` 里的部署 / 回滚 / 紧急排查知识 consolidate 成一份可操作手册。
> 出事时**先翻这里**,再动手。权威事实仍以 `CLAUDE.md/CLAUDE.md` 对应铁律为准。

---

## 0. 30 秒速查

| 我要… | 跳到 | 一句话 |
|---|---|---|
| 上线代码 | [§2 部署](#2-部署) | `git push origin master` → CI 全闸绿 → **deploy job** 精确部署(≈10 min) |
| 撤回刚上线的改动 | [§3 回滚](#3-回滚) | `git revert <hash>` + push(**不要** force / reset) |
| 看 CI 红没红 | [§4 CI 状态](#4-ci-状态查看) | `gh run list --branch master --limit 5` |
| 站点报 500 / 上传炸 | [§6 紧急排查](#6-紧急排查) | **第一反应查磁盘** `df -h /`(铁律 #24) |
| 确认新码真生效 | [§5 健康检查](#5-健康检查--诊断) | 生产 `git rev-parse HEAD` == 你 push 的 commit(不是看 200) |

---

## 1. 基础设施清单

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com |
| 服务器 | `root@66.42.49.213` · Vultr **Singapore** · Ubuntu 24.04 · `/opt/mrpilot/` · **SSH 别名 `pearnly-prod`**(key 在 `~/.ssh/id_ed25519_pearnly_prod` · 只 key 登录) |
| 进程 | systemd unit `mrpilot`(uvicorn `app:app`) |
| 数据库 | Supabase PostgreSQL(Pooler) |
| 部署机制 | push → GitHub CI(`unit` + `e2e` 并行 + 全部 FAIL 闸绿)→ **`deploy` job**(仅 master push)带 `sha=${{ github.sha }}` + `secrets.DEPLOY_TOKEN` 调 `GET /internal/deploy/manual` → `/opt/mrpilot/git-deploy.sh`(`TARGET_SHA` 精确守卫 + `flock` 串行化) |
| GitHub webhook | **永久停用**(`625195648` · `active=false` · 2026-08-26)· 历史遗留机制 · 不再是部署入口 · 不提供复启命令 |
| 私库 | `github.com/skin306152-star/pearnly-app`(本地 remote 名 `origin` · 分支 `master` · 服务器 remote 名 `pearnly`) |
| 密钥 | 生产 `/opt/mrpilot/.env`;部署令牌 repo secret `DEPLOY_TOKEN`(= 服务器 `GITHUB_WEBHOOK_SECRET` 原值) |
| 前端版本探针 | `GET /api/version` → `cache_bust` 数字 |

SSH 免密已配(`pearnly-prod`)。只读诊断 Claude 自己跑;**生产写操作**(装包 / 重启 / 改数据)走安全闸或请 Zihao 点一下(铁律 #25)。

---

## 2. 部署

### 正常流程（C 档位 · Claude 写完自测后可直接推 · 铁律 #16）

```bash
# 1. 确认在 master(铁律 #14 · 每窗口开工必查)
git branch --show-current   # 必须 master

# 2. 本地机械闸全绿才推(等价 pre-push · 不用真推)
PYTHONUTF8=1 sh scripts/git-hooks/pre-push

# 3. 提交 + 推(显式写 master · 不是当前分支)
git add <自己的 pathspec>
git commit -m "<type>(<scope>): <subject> · why 不是 what"
git push origin master
```

push 后**不再是 webhook 秒级部署**。新链路(2026-08-26 起):

```
git push origin master
  → GitHub CI 起跑(unit 与 e2e 并行 · lint* 全闸并行 · pg-smoke)
  → 全部 FAIL 闸 + unit + e2e + pg-smoke 绿
  → deploy job(master push 专属 · needs 全绿才触发)
      curl -H "X-Internal-Token: $DEPLOY_TOKEN" \
           "https://pearnly.com/internal/deploy/manual?sha=${{ github.sha }}"
  → 服务器 _launch_deploy → git-deploy.sh:
      flock 串行化(锁等待 ≤900s)→ fetch → TARGET_SHA 精确守卫
      → reset --hard 到该 SHA → cp static → pip/playwright 幂等 → systemctl restart → 健康检查
```

关键性质:
- **服务器只部署「CI 验过的那一个 commit」**(`TARGET_SHA = ${{ github.sha }}`);fetch 后发现 master 已被更新的 push 取代 → 记 `SUPERSEDED` 并跳过,不静默部署未审查 commit。
- **flock 串行化**:同一时刻只有一个 `git-deploy.sh` 在跑,排队的更新 push 等锁不丢。
- 紧急手动救援可调 `GET /internal/deploy/manual?sha=<40-hex>`(**必须带 SHA · 不带 SHA 已禁止**)。需 Zihao 明确授权。
- `curl /internal/deploy/log` 看最近部署日志;`/internal/deploy/status` 只读回滚 marker。

### 拆分实测（2026-08-26 · 迁移前后量到的墙钟）

| 阶段 | 跑法 | 墙钟 | 说明 |
|---|---|---|---|
| 改版前单体 test job | 旧 CI run `32877623122`(c635a5bf) | **13m42s**(test job 内 unit 201s + e2e 484s **串行** = 818s) | e2e 起本地 uvicorn 的依赖由同一 job 装 |
| 改版后全链路 | 新 CI run `32890654052`(429f1da6 · 含 deploy) | **10m13s**(unit 357s ∥ e2e 604s · deploy 4s) | e2e job 现在自装 `requirements.lock.txt`(多 ~120s)· 但 unit 全程并行 → 整体 -25% |

> e2e 604s > 旧 484s 是**诚实代价**:本地 spec(`ps5_cashier_route` 等)spawn `python -m uvicorn app:app`,拆 job 后必须自己装应用依赖;这 ~120s 换来了「unit 与 e2e 永不互相阻塞」。CI 结构性契约由 `tests/unit/test_ci_workflow_contract.py` 锁住。

> 2026-08-26 首次文档同步 run 暴露 checkout 浪费:`lint-debt` 为拿 `HEAD~1` 拉完整约 243MB 历史,撞 5 分钟 timeout 被取消,deploy 因 required job 不完整而正确跳过。现已改为 push 只取最近 2 commit、PR 保留全历史,并由 workflow contract 防回归。

### 部署前必做（铁律 #24 · 血泪根因）

```bash
ssh pearnly-prod "df -h /"     # 用量 > 85% 必须先清理再部署,别等 100% 崩
```

### 验证（push 后 · 别只看 200）

```bash
# 部署被 deploy job 接管 → 线上变码要等 CI 全绿(≈10 min)· 判据 = 生产 HEAD == 你推的 SHA
ssh pearnly-prod "git -C /opt/mrpilot rev-parse HEAD"
ssh pearnly-prod "systemctl show mrpilot -p ActiveEnterTimestamp"   # ≥ 那次部署时间
```

---

## 3. 回滚

> 🔴 **红线**:`git push --force` / `git reset --hard` / 删 tag/branch 到 master **必须先问 Zihao**(铁律 #16)。回滚优先用 `revert`(新增反向 commit · 不改历史)。

```bash
# 1. 找到要撤的 commit
git log --oneline -10

# 2. 生成反向 commit(安全 · 不改历史)
git revert <bad_hash> --no-edit

# 3. 推上线(正常走 deploy job · 会先跑 CI)
git push origin master
```

紧急且 revert 冲突时,可临时 checkout 上一个 good commit 的文件,但**不要** force-push master。

### 紧急时:等不及 CI / CI 红着也要部署

> 🔴 **以下操作必须 Zihao 明确授权后才可执行。** 未经授权不得手动触发部署。

CI 全红时 `deploy` job 不会触发(它 needs 全部 FAIL 闸)。**优先重跑同一 CI run 的 deploy job**:

```bash
gh run rerun <RUN_ID> --repo skin306152-star/pearnly-app
```

若重跑仍失败且 Zihao 已明确授权,可用手动端点(**必须带显式 40-hex SHA · 绝不允许不带 SHA**):

```bash
# 手动端点(Zihao 授权后 · 必须带精确 40-hex SHA · DEPLOY_TOKEN 在 gh secret)
curl -H "X-Internal-Token: $DEPLOY_TOKEN" \
     "https://pearnly.com/internal/deploy/manual?sha=<40-hex-SHA>"
```

> ⚠️ **旧 GitHub webhook `625195648` 已于 2026-08-26 永久停用。** 它是历史遗留机制,不再是部署入口。不提供复启命令——若极端情况确需复启,必须由 Zihao 亲自决策并手动操作。

服务器侧部署失败有 byte-for-byte 保住的健康检查回滚(`.deploy_rollback` marker · `GET /internal/deploy/status` 读)。

---

## 4. CI 状态查看（铁律 #22 · gh 已登录 `skin306152-star`）

> 直接用 `gh`(在 PATH · 旧 PowerShell 绝对路径 `C:\Program Files\GitHub CLI\gh.exe` 已失效)。

```bash
# 最近 5 个 run(push 后查绿没绿)
gh run list --repo skin306152-star/pearnly-app --branch master --limit 5
# 某 run 失败详情
gh run view <RUN_ID> --repo skin306152-star/pearnly-app --log-failed
# 判绿只认 conclusion == success(cancelled 对 gh run watch 也返回 0)
gh run view <RUN_ID> --repo skin306152-star/pearnly-app --json status,conclusion --jq '.status + "/" + (.conclusion // "null")'
# transient 失败(git exit 128 / 网络抖)重跑
gh run rerun <RUN_ID> --repo skin306152-star/pearnly-app
```

---

## 5. 健康检查 / 诊断

```bash
# 服务状态 + 最近重启时间
ssh pearnly-prod "systemctl status mrpilot --no-pager | head -20"
ssh pearnly-prod "systemctl show mrpilot -p ActiveEnterTimestamp"

# 抓真实错误栈(报 500 / 异常时 · 不猜根因 · 铁律 #25)
ssh pearnly-prod "journalctl -u mrpilot --since '5 min ago' | grep -iE 'Error|Traceback'"

# 磁盘 / 谁吃光
ssh pearnly-prod "df -h /"
ssh pearnly-prod "du -sh /tmp/* | sort -rh | head"
```

> 注:`/health` + `/ready` 端点是整顿 B4 待落地项(目标:DB/Gemini/SMTP/LINE 任一挂 → `/ready` 返非 200 · 硬门槛 #7)。当前以上面的 journalctl + df 为主。

---

## 6. 紧急排查

### 🥇 头号嫌疑:磁盘满（铁律 #24 · 2026-05-24 真实事故）

**症状**:上传 / 银行对账报 `Unexpected token '<', "<html>..." is not valid JSON`。

**根因链**:`/` 100% 满 → Nginx 写不下上传请求体(`/var/lib/nginx/body/` `No space left on device`)→ 返 HTML 500 → 前端 `res.json()` 解析 HTML 抛错。罪魁通常是 `/tmp` 堆的 `pip-*` 残渣(部署 pip 解压 torch ~2.7G 不清理累积)。

**处置**:
```bash
ssh pearnly-prod "df -h /"                  # 确认满了
ssh pearnly-prod "rm -rf /tmp/pip-*"        # 清 pip 残渣(下次自建)
ssh pearnly-prod "systemctl restart mrpilot"
```

**排障经验值**:
- 500 而非 504 = 不是超时;uvicorn 日志查不到那个 POST = 卡在 Nginx 没到应用。
- nginx 半夜 logrotate 后 `error.log` 可能 0 字节 · 真错误在 `error.log.1`。

### 后端改动「上了但没生效」

部署走 deploy job(≈10 min)不是秒级 → `/api/version`=200 ≠ 新码跑起来。判据:生产 `git rev-parse HEAD` == 你推的精确 SHA,且 `ActiveEnterTimestamp ≥ 部署时间`(铁律 #25)。`/internal/deploy/log` 看部署日志;fetch 撞 GitHub 超时会让 git-deploy 静默留在旧 commit → 优先 `gh run rerun <RUN_ID>` 重跑 deploy job;反复失败再 SSH 带精确 SHA 重跑:`bash /opt/mrpilot/git-deploy.sh <40-hex-SHA>`(**禁止不带 SHA**)。

### 删后端字段后 `/api/me` 等 500（铁律 #15）

改 dict 返回字段必须同步改 Pydantic `response_model`(`UserInfo` 等)· 删字段先 `Optional + default None` 一版再真删。报「前端数据空」第一步 `curl -H "Authorization: Bearer $TOKEN" /api/<endpoint>` 看 HTTP 状态,别 grep CSS。

---

## 7. 部署后磁盘卫生（根治 · 铁律 #24）

- `git-deploy.sh` 末尾 `rm -rf /tmp/pip-*`
- 每日 cron 清 1 天前 `pip-*` 残留
- 磁盘 85% 告警

---

## 8. 本地机械闸（clone-local hook · 2026-07-31 Zihao 拍板装）

- 本 clone 已设 `core.hooksPath=scripts/git-hooks` → 每次 push 本地先跑全套闸,全绿才放行。
- **是 clone-local 配置**(写在 `.git/config` 不是全局):共享同一 `.git` 的所有 worktree 一起生效;**新 clone 不会自带**,要装:

```bash
git config core.hooksPath scripts/git-hooks
git config --get core.hooksPath      # 有输出 = 装上了
git hook run pre-push                # 空跑验证
```

- 路径按「谁在 push」各自解析(A worktree push 跑 A 的钩子);`git push --dry-run` 也会触发钩子,可拿来空跑。
- 想要逐 worktree 单独开关:先 `git config extensions.worktreeConfig` 再 `git config --worktree ...`。
- 详细 31 道闸清单 / 逐道自查命令 / 豁免语法:`docs/GATES.md`。

---

## 9. 别做什么（红线 · 铁律 #16）

- ❌ `git push --force` / `--force-with-lease` 到 master
- ❌ `git reset --hard` / 删 tag / 删 branch（破坏历史)
- ❌ `--no-verify` 绕 pre-commit hook(AI 窗口永远不许用)
- ❌ > 30 文件的重构级 commit 不让 Zihao 先 review
- ❌ `db.py` schema migration / `DROP` 任何东西
- ❌ 关键路径(登录/注册/OCR/计费)大改不先口头汇报

以上任意一条 → **停下问 Zihao**。

---

*配套:`CLAUDE.md/CLAUDE.md`(铁律权威源)· `CLAUDE.md/REFACTOR_MASTER_PLAN.md`(G 阶段 · 整顿主计划)· `CONTRIBUTING.md`(协作者卡)· `docs/GATES.md`(机械闸清单)。*
