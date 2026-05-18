# Pearnly 部署流程现状 + 防失同步建议

> **生成日期**:2026-05-18
> **生成会话**:屎山清理会话 阶段 1.5++(deploy 调研专项)
> **状态**:**只调研、不动手**。任何 deploy 脚本本身都未修改。

---

## 0. 一句话结论

部署流程**已经从 scp 升级到 git push + webhook**(2026-05-17 拍板),但有 **3 个潜在风险**让"幽灵模块再发生"还有机会:服务器有未跟踪文件不会被 git 抓到、deploy 流程不验 import、新依赖不会自动 `pip install`。建议加 1 个**部署前自检脚本** + 1 次**服务器残留扫描**,30 分钟就能堵死类似问题。

---

## 1. 当前部署流程(已经梳清楚)

### 1.1 部署有 2 条触发路径

```
[用户/Claude]   git push origin master
       ↓
[GitHub]        webhook POST → https://pearnly.com/internal/deploy
       ↓                       (HMAC-SHA256 验签 · 见 app.py:4392-4419)
[服务器 app.py]  spawn detached bash: sleep 3 && bash /opt/mrpilot/git-deploy.sh
       ↓
[git-deploy.sh] 执行实际部署(下节详述)
```

**备用路径**(webhook 失败时):
- 浏览器直接打开 `https://pearnly.com/internal/deploy/manual?token=$GITHUB_WEBHOOK_SECRET` → 同样触发 git-deploy.sh
- 还可看部署日志:`/internal/deploy/log?token=...&lines=50`(app.py:4422-4456)

### 1.2 git-deploy.sh 实际做的事

**关键源头**:这个脚本在 **app.py:208-293** 里硬编码,**每次 mrpilot 重启都会重写覆盖** `/opt/mrpilot/git-deploy.sh`(注释:"请勿手动修改 · 重启会覆盖")。

实际流程(7 步):

| 步 | 动作 | 命令 |
|---|---|---|
| 1 | 记录上一个 GitHub HEAD 作为回滚目标 | `PREV_HEAD=$(git rev-parse pearnly/master)` |
| 2 | Fetch 最新代码 | `git fetch pearnly master` |
| 3 | 已是最新?跳过 | 比对 PREV_HEAD 与 FETCH_HEAD |
| 4 | **强制对齐到 GitHub** | **`git reset --hard FETCH_HEAD`** ← ⚠️ 关键 |
| 5 | 拷前端文件到 static/ | `cp home.html home.js home.css login.html static/` |
| 6 | 重启服务 | `systemctl restart mrpilot` |
| 7 | 健康检查 30s + 失败自动回滚 | `curl /api/health` · 失败则 `git reset --hard $PREV_HEAD` |

### 1.3 deploy.sh(根目录那个)是什么

是**老 tar.gz 部署方式**的服务器侧脚本,本地保留一份副本。流程:`tar.gz → 解压 → cp 文件 → systemctl restart`。

**现在已经不用了**(CLAUDE.md:349 "永久替代 scp")— 仅作 git push 失败时的紧急回退方案。

---

## 2. 为什么 4 个文件能上服务器但没在 git 里(真相还原)

### 2.1 git 历史的关键 3 个 commit

```
51 个 commits · 跨度 2026-05-13 → 2026-05-18(只有 5 天)

2026-05-13 master 第一个 commit (667fce9)            ← 仓库新建
        ↓
2026-05-17 f1cddca "v11841133 · Git 部署上线"        ← 13 个后端 .py 入 git
        ↓
2026-05-17 2531718 "fix: include 19 backend modules  ← 又补 19 个
                    previously only in mrpilot
                    legacy repo"
        ↓
2026-05-18 90c1271 "rescue: pull production-only     ← 今天的修复:再补 4 个
                    modules into git (were
                    missing locally)"
```

### 2.2 真相

1. **Pearnly 项目原本用另一个 git 仓库**(commit message 显式说 "mrpilot legacy repo")
2. **2026-05-13 起,迁移到新仓库 `pearnly-app`**
3. **2026-05-17 从老仓库一次性搬 19 个 .py 模块进新仓库**(commit 2531718)
4. **那次搬迁漏了 4 个文件**:`pdf_storage` / `pdf_searchable` / `excel_template_th` / `xero_pusher`
5. 但**生产服务器 `/opt/mrpilot/` 一直有这 4 个文件**(从更早的 scp tar.gz 时代留下来)
6. **`git reset --hard FETCH_HEAD` 只覆盖 git 跟踪的文件**,未跟踪文件原样保留 → 服务器永远不会因此挂掉
7. 今天(2026-05-18)用户从服务器 scp 回这 4 个 + git commit 90c1271 → **修复完成**

### 2.3 为什么 2531718 漏了这 4 个

无法 100% 还原,但合理推测(基于 commit message + 文件命名规律):
- 那次搬迁用了某种"扫服务器 /opt/mrpilot/*.py"的列表方式
- 这 4 个文件的某个属性导致被漏掉(可能是 `.gitignore` 误伤、可能是手动列表打字漏、可能是某次老 ls 输出缓存)
- 4 个名字都不符合常见模式(无前缀如 `vat_*` / `bank_*` / `*_routes` / `*_engine`)、命名孤立 → 容易在视觉清点时漏

**根本原因**:**没有任何机制验证"app.py 的 import 全部能解析到本地文件"**,所以漏了也没人察觉,直到本会话用 `importlib.util.find_spec` 静态扫才发现。

---

## 3. 当前流程的 3 个潜在风险

### 风险 1:服务器还可能有其他"未跟踪文件"

`git reset --hard` 不会动未跟踪文件。今天我们补了 4 个,**但服务器 `/opt/mrpilot/` 可能还有别的未跟踪 .py / 配置文件**,我们不知道。

**验证方法**(用户在服务器上跑一次即可):
```bash
ssh root@45.76.53.194 'cd /opt/mrpilot && git status --short | grep "^??" '
```
输出的 `??` 开头都是未跟踪文件。如果还有 `.py`,就是新的"幽灵候选"。

**潜在炸弹**:如果哪天有人在服务器跑 `git clean -fdx`(清理工作区),所有未跟踪文件会被删 → app 起不来 → 自动回滚也救不了(回滚到旧 commit 不能恢复被删的未跟踪文件)。

### 风险 2:deploy 流程**不验 import**

git-deploy.sh 流程是:`git reset --hard → cp static → systemctl restart → health check`。

**注意**:health check 只是 `curl /api/health` 看 HTTP 200。如果新代码有 import 错误,app 起不来,health check 失败,**才**触发回滚。

**问题**:回滚发生在**服务挂了之后**。用户已经看到 502/503 一段时间(最多 30 秒 + 回滚耗时)。

**更好的做法**:`git reset --hard` 完成后、`systemctl restart` 之前,加一行**纯静态 import 检查**:
```bash
python3 -c "
import ast, importlib.util, os
for f in [x for x in os.listdir('.') if x.endswith('.py')]:
    tree = ast.parse(open(f).read())
    # ... check each import resolves
"
```
失败就直接 abort,**不重启服务**,用户完全无感知。

### 风险 3:新依赖不会自动 `pip install`

`requirements.txt` 现在在 git 里了,但 git-deploy.sh **不会**自动跑 `pip install -r requirements.txt`。

唯一的 pip 调用是 deploy.sh(老脚本)的 line 70:
```bash
pip3 install pypdf pdfminer.six --break-system-packages -q
```
**只装这 2 个**。如果以后加新依赖,**必须手动 SSH 服务器 pip install**,否则部署后 app 起不来。

---

## 4. 防失同步建议(优先级排序)

### 🔥 P0(15 分钟搞定 · 强烈建议)

#### P0-1:服务器跑一次未跟踪文件扫描

```bash
ssh root@45.76.53.194 'cd /opt/mrpilot && git status --short | grep -E "^\?\? .*\.py$"'
```

- 输出**为空** → 已没有其他幽灵 .py,可以安心
- 输出**有内容** → 每个都判断是否要 git add(或确认它是日志/缓存类的)

**强烈建议**:除了 .py 也扫一遍 `.env.example`、`*.sh`、`scripts/` 等,把所有"长期需要的、未跟踪"文件都梳一遍。

#### P0-2:把 import 检查脚本永久放进项目

我在本会话用了 `C:\Users\skin3\_audit_pearnly_imports_check.py`(临时位置)。建议:
- 移到 `scripts/check_imports.py`(项目内,git 跟踪)
- 这样 deploy 流程、CI、本机开发都能复用同一个工具

> ⚠️ 本会话**不动手**,只建议。等用户决定后单独做。

### 🟡 P1(30 分钟搞定 · 建议但不紧急)

#### P1-1:在 git-deploy.sh 加 import 预检 + abort

让 app.py 嵌入的 git-deploy.sh 在 `git reset --hard` 之后、`systemctl restart` 之前增加一步:
```bash
# 4.5 静态 import 检查 — 不过就不重启
if ! python3 scripts/check_imports.py --strict; then
    echo "import check FAILED — abort deploy (not restarting)" >> "$LOG"
    git reset --hard "$PREV_HEAD" >> "$LOG" 2>&1
    exit 1
fi
```

效果:**坏代码不会触发服务重启**,用户完全无感知。

> ⚠️ 这意味着改 app.py 里的嵌入字符串 → 改 app.py 就要 deploy → 风险递归。建议**先用 P1-2 解耦**,再做这条。

#### P1-2:把 git-deploy.sh 从 app.py 字符串里拆出来

现在 git-deploy.sh 是 app.py:212-287 一段 70+ 行的字符串。改 deploy 流程要改 app.py + push + deploy(本身就引入风险)。

建议改成:
- 项目根加 `scripts/git-deploy.sh`(git 跟踪)
- app.py 启动时不再写硬编码字符串,而是把这个脚本 `cp` 到 `/opt/mrpilot/git-deploy.sh`
- 改 deploy 流程 = 改 scripts/git-deploy.sh + push + 下次部署自动生效

#### P1-3:requirements.txt 加入部署流程

git-deploy.sh 在 `git reset --hard` 后加:
```bash
# 4.6 装新依赖 (幂等 · pip 自己判断需不需要)
pip3 install -r requirements.txt --break-system-packages -q
```

这样以后 `requirements.txt` 加了新包,push 一下就装上,不用 SSH。

### 🟢 P2(进阶 · 等项目稳定再做)

#### P2-1:GitHub Actions CI 在 push 时跑 import 检查

加 `.github/workflows/ci.yml`:
```yaml
on: [push, pull_request]
jobs:
  import-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.10'}
      - run: pip install -r requirements.txt
      - run: python scripts/check_imports.py --strict
```

效果:有 import 问题在 GitHub Actions 阶段就拦下,根本不到服务器。

#### P2-2:每周服务器自检 cron

定时跑(比如每周一上午):
```bash
ssh root@45.76.53.194 'cd /opt/mrpilot && git status --short | grep "^??" | tee /tmp/untracked.txt'
# 如果非空 → 邮件 / LINE 通知运维
```

---

## 5. 本调研未触及的事

按用户指示,只调研不动手。以下事项**已识别但未做**:

| 事项 | 现状 | 建议归属 |
|---|---|---|
| 服务器 `/opt/mrpilot/` 是否还有其他未跟踪 .py | 未知 · 需 SSH 核查 | 用户单独跑 P0-1 即可 |
| scripts/check_imports.py 是否要永久化 | 工具放在 `C:\Users\skin3\` 临时位置 | 用户拍板后单独做 |
| git-deploy.sh 拆出 app.py | 仍嵌入字符串 | P1-2 |
| CI/CD 是否要加 | 当前完全没有 | P2-1(项目稳定后) |
| deploy.sh 老脚本是否要保留 | 仍在 git 里,作 emergency fallback | 维持现状 |
| 4 个新归位文件与服务器版本是否一致 | 应该一致(用户今天从服务器 scp 回来) | 下次 deploy 后看 `/internal/deploy/log` 确认 |

---

## 6. 调研用到的证据(给后续审计者)

| 检查项 | 命令 / 文件 | 关键结果 |
|---|---|---|
| 是否有 CI/CD | `ls .github/` | 不存在 |
| 是否有 git hooks | `ls .git/hooks/` | 只有空目录(sample 已删) |
| 部署脚本清单 | `find . -maxdepth 2 -name "*.sh"` | 仅 `deploy.sh` |
| webhook 实现位置 | `grep -n "internal/deploy" app.py` | 4392-4456 |
| git-deploy.sh 源 | `app.py:208-293` | 启动时写入 `/opt/mrpilot/git-deploy.sh` |
| 历史 commit 时间跨度 | `git rev-list --count master` | 51 commits / 2026-05-13 → 2026-05-18 |
| 4 个文件 git 历史 | `git log --diff-filter=A -- pdf_storage.py` | 只有 90c1271 一次(今天) |
| 大批量补漏 commit | `git log --pretty=format:"%h %s" master` | `2531718` 补 19 个,`90c1271` 补 4 个 |
| tar.gz 内容 | `tar -tzf deploy_v*.tar.gz` | 都只含 2-4 个改动文件(增量包) |
| 服务器残留 | `ssh + git status --short` | **未做** — 需用户自跑 |

---

*本调研报告 v1 · 生成于 2026-05-18 · 本会话 阶段 1.5++*
*只读 · 任何 deploy 脚本未修改 · 仅产出本文档*
