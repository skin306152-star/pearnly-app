# 🛠️ Pearnly · 运维手册（RUNBOOK）

> **整顿 REFACTOR-G2 · 2026-05-27 初版**
> 把散在 `CLAUDE.md/CLAUDE.md` 里的部署 / 回滚 / 紧急排查知识 consolidate 成一份可操作手册。
> 出事时**先翻这里**,再动手。权威事实仍以 `CLAUDE.md/CLAUDE.md` 对应铁律为准。

---

## 0. 30 秒速查

| 我要… | 跳到 | 一句话 |
|---|---|---|
| 上线代码 | [§2 部署](#2-部署) | `git push origin master` → webhook 自动部署 → 等 ~15s |
| 撤回刚上线的改动 | [§3 回滚](#3-回滚) | `git revert <hash>` + push(**不要** force / reset) |
| 看 CI 红没红 | [§4 CI 状态](#4-ci-状态查看) | `gh run list --branch master --limit 5` |
| 站点报 500 / 上传炸 | [§6 紧急排查](#6-紧急排查) | **第一反应查磁盘** `df -h /`(铁律 #24) |
| 确认新码真生效 | [§5 健康检查](#5-健康检查--诊断) | `systemctl show mrpilot -p ActiveEnterTimestamp` ≥ push 时间 |

---

## 1. 基础设施清单

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com |
| 服务器 | `root@45.76.53.194` · Vultr Tokyo · Ubuntu 24.04 · `/opt/mrpilot/` |
| 进程 | systemd unit `mrpilot`(uvicorn `app:app`) |
| 数据库 | Supabase PostgreSQL · AWS ap-southeast-1 |
| 部署机制 | GitHub webhook → `POST /internal/deploy` → `/opt/mrpilot/git-deploy.sh` |
| 私库 | `github.com/skin306152-star/pearnly-app`(本地 remote 名 `origin` · 分支 `master`) |
| 密钥 | 生产 `/opt/mrpilot/.env`(整顿 A4 收拢进 Doppler `prd`) |
| 前端版本探针 | `GET /api/version` → `cache_bust` 数字 + 4 语 `release_notes` |

SSH 免密已配(`id_ed25519`)。只读诊断 Claude 自己跑;**生产写操作**(装包 / 重启 / 改数据)走安全闸或请 Zihao 点一下(铁律 #25)。

---

## 2. 部署

### 正常流程（C 档位 · Claude 写完自测后可直接推 · 铁律 #16）

```bash
# 1. 确认在 master(铁律 #14 · 每窗口开工必查)
git -C "D:\Users\Skin\Desktop\pearnly_project" branch --show-current   # 必须 master

# 2. 5 道守门全绿才推
python scripts/check_imports.py --quiet          # EXIT 0
python scripts/check_i18n.py --strict            # 0 missing 0 extra
python -m unittest discover -s tests/unit        # all OK
npx playwright test                              # all passed(改了前端时)
node --check <changed.js>                        # 改了 JS 时

# 3. 提交 + 推(显式写 master · 不是当前分支)
git add -A
git commit -m "<type>(<scope>): <subject> · REFACTOR-<id>"
git push origin master
```

push 后 GitHub webhook 触发服务器 `git pull` + `cp 到 static/` + `systemctl restart mrpilot`。

### 部署前必做（铁律 #24 · 血泪根因）

```bash
ssh root@45.76.53.194 "df -h /"     # 用量 > 85% 必须先清理再部署,别等 100% 崩
```

### 每次部署写 4 语 release_notes（铁律 #6）

`app.py` 的 `/api/version` `release_notes` 字段必须 4 语(zh/th/en/ja)**完全覆盖**(不 prepend 老版本)· 标准官方语言 · 无技术词。

### 验证（push 后)

```bash
sleep 15
curl https://pearnly.com/api/version          # 看 cache_bust 翻新
# 后端改动:确认是新进程(部署慢 · 200 ≠ 新码生效 · 铁律 #25)
ssh root@45.76.53.194 "systemctl show mrpilot -p ActiveEnterTimestamp"   # ≥ push 时间
```

---

## 3. 回滚

> 🔴 **红线**:`git push --force` / `git reset --hard` / 删 tag/branch 到 master **必须先问 Zihao**(铁律 #16)。回滚优先用 `revert`(新增反向 commit · 不改历史)。

```bash
# 1. 找到要撤的 commit
git log --oneline -10

# 2. 生成反向 commit(安全 · 不改历史)
git revert <bad_hash> --no-edit

# 3. 推上线(同部署流程)
git push origin master
```

紧急且 revert 冲突时,可临时 checkout 上一个 good commit 的文件,但**不要** force-push master。

---

## 4. CI 状态查看（铁律 #22 · gh 已登录 `skin306152-star`）

> 优先用 PowerShell 调(bash PATH 未刷新到 gh)。绝对路径:`C:\Program Files\GitHub CLI\gh.exe`

```powershell
$gh = "C:\Program Files\GitHub CLI\gh.exe"
# 最近 5 个 run(push 后查绿没绿)
& $gh run list --repo skin306152-star/pearnly-app --branch master --limit 5
# 某 run 失败详情
& $gh run view <RUN_ID> --repo skin306152-star/pearnly-app --log-failed
# transient 失败(git exit 128 / 网络抖)重跑
& $gh run rerun <RUN_ID> --repo skin306152-star/pearnly-app
```

---

## 5. 健康检查 / 诊断

```bash
# 服务状态 + 最近重启时间
ssh root@45.76.53.194 "systemctl status mrpilot --no-pager | head -20"
ssh root@45.76.53.194 "systemctl show mrpilot -p ActiveEnterTimestamp"

# 抓真实错误栈(报 500 / 异常时 · 不猜根因 · 铁律 #25)
ssh root@45.76.53.194 "journalctl -u mrpilot --since '5 min ago' | grep -iE 'Error|Traceback'"

# 磁盘 / 谁吃光
ssh root@45.76.53.194 "df -h /"
ssh root@45.76.53.194 "du -sh /tmp/* | sort -rh | head"
```

> 注:`/health` + `/ready` 端点是整顿 B4 待落地项(目标:DB/Gemini/SMTP/LINE 任一挂 → `/ready` 返非 200 · 硬门槛 #7)。当前以上面的 journalctl + df 为主。

---

## 6. 紧急排查

### 🥇 头号嫌疑:磁盘满（铁律 #24 · 2026-05-24 真实事故）

**症状**:上传 / 银行对账报 `Unexpected token '<', "<html>..." is not valid JSON`。

**根因链**:`/` 100% 满 → Nginx 写不下上传请求体(`/var/lib/nginx/body/` `No space left on device`)→ 返 HTML 500 → 前端 `res.json()` 解析 HTML 抛错。罪魁通常是 `/tmp` 堆的 `pip-*` 残渣(部署 pip 解压 torch ~2.7G 不清理累积)。

**处置**:
```bash
ssh root@45.76.53.194 "df -h /"                  # 确认满了
ssh root@45.76.53.194 "rm -rf /tmp/pip-*"        # 清 pip 残渣(下次自建)
ssh root@45.76.53.194 "systemctl restart mrpilot"
```

**排障经验值**:
- 500 而非 504 = 不是超时;uvicorn 日志查不到那个 POST = 卡在 Nginx 没到应用。
- nginx 半夜 logrotate 后 `error.log` 可能 0 字节 · 真错误在 `error.log.1`。

### 后端改动「上了但没生效」

部署慢 → `/api/version`=200 ≠ 新码跑起来。用 `ActiveEnterTimestamp ≥ push 时间` 确认是新进程(铁律 #25)。

### 删后端字段后 `/api/me` 等 500（铁律 #15）

改 dict 返回字段必须同步改 Pydantic `response_model`(`UserInfo` 等)· 删字段先 `Optional + default None` 一版再真删。报「前端数据空」第一步 `curl -H "Authorization: Bearer $TOKEN" /api/<endpoint>` 看 HTTP 状态,别 grep CSS。

---

## 7. 部署后磁盘卫生（根治 · 铁律 #24）

- `git-deploy.sh` 末尾 `rm -rf /tmp/pip-*`
- 每日 cron 清 1 天前 `pip-*` 残留
- 磁盘 85% 告警

---

## 8. 别做什么（红线 · 铁律 #16）

- ❌ `git push --force` / `--force-with-lease` 到 master
- ❌ `git reset --hard` / 删 tag / 删 branch（破坏历史)
- ❌ `--no-verify` 绕 pre-commit hook
- ❌ > 30 文件的重构级 commit 不让 Zihao 先 review
- ❌ `db.py` schema migration / `DROP` 任何东西
- ❌ 关键路径(登录/注册/OCR/计费)大改不先口头汇报

以上任意一条 → **停下问 Zihao**。

---

*配套:`CLAUDE.md/CLAUDE.md`(铁律权威源)· `CLAUDE.md/REFACTOR_MASTER_PLAN.md`(G 阶段 · 整顿主计划)· `CONTRIBUTING.md`(协作者卡)。*
