# 💻 换电脑无缝迁移指南 · Zihao 专属

> **写给**:Zihao(产品经理 · 不写代码)
> **场景**:买了新电脑(Windows / Mac 都行)· 要把 Pearnly 整个搬过去 · 打开 Claude Code 立刻能继续推项目
> **总耗时**:1-2 小时(80% 是等下载安装 · 你只点几下鼠标)
> **难度**:跟着抄 · 不需要理解
> **最后更新**:2026-05-28

---

## 🎯 总览 · 要搬的 7 样东西

| # | 东西 | 怎么搬 | 重要度 |
|---|------|--------|--------|
| 1 | Pearnly 项目代码 | GitHub 重新 clone(99% 在 git 里) | 🔥 必须 |
| 2 | `.env.local` 文件(本地配置) | U 盘 / 网盘拷过去(不在 git) | 🔥 必须 |
| 3 | SSH 密钥(连服务器 + GitHub) | U 盘 / 网盘拷过去 | 🔥 必须 |
| 4 | 测试账号密码 | 重新 setx 设环境变量 | 🔥 必须 |
| 5 | 装 Claude Code + 登录订阅 | 官网下载 + 浏览器登录 | 🔥 必须 |
| 6 | 装 Git / Node / Python / GitHub CLI | 官网下载 | 🔥 必须 |
| 7 | 浏览器书签(Cloudflare/Supabase 后台) | Chrome 同步账号 | 🟡 推荐 |

---

## 📦 第一步 · 旧电脑准备(在旧电脑上做 · 30 分钟)

### 1.1 确认 Pearnly 代码全部推到 GitHub

打开任何一个 Claude Code 窗口(或新开一个)· 跟它说:

```
帮我确认当前所有本地改动都推到 GitHub master 了 · 跑 git status + git log origin/master..HEAD ·
如果有未推的 commit 列出来 · 如果有未提交的改动也列出来 · 别帮我 push · 让我看看再说。
```

它会告诉你:
- ✅ "干净 · 全推完了" → 进下一步
- ⚠️ "有 X 个 commit 没 push" → 跟它说"那帮我推一下"
- ⚠️ "有未提交改动" → 跟它说"看下能不能 commit · 不能就 stash"

**目标**:GitHub `skin306152-star/pearnly-app` 上 master 分支 = 你电脑上 master 完全一致

### 1.2 准备"必须手动带"的文件清单

打开文件管理器 · 把下面这些**复制到 U 盘 / 网盘**(OneDrive / Google Drive / 微信文件传输都行):

#### 文件清单 A · 项目内本地配置(不在 git 里)

| 路径 | 是啥 | 大小 |
|------|------|------|
| `D:\Users\Skin\Desktop\pearnly_project\.env.local` | 本地环境变量(可能有密钥) | < 1 KB |
| `D:\Users\Skin\Desktop\pearnly_project\.claude\settings.local.json` | Claude 项目本地权限设置 | ~ 14 KB |
| `D:\Users\Skin\Desktop\pearnly_project\.claude\launch.json` | Claude 启动配置 | < 1 KB |

#### 文件清单 B · SSH 密钥(连服务器 + GitHub 用)

整个 `C:\Users\<你的用户名>\.ssh\` 目录拷走 · 里面 9 个文件:

| 文件 | 用途 |
|------|------|
| `config` | SSH 配置(指定哪个 key 连哪个 server) |
| `id_ed25519` + `.pub` | 默认 SSH key |
| `id_ed25519_pearnly` + `.pub` | 连 Pearnly 服务器(45.76.53.194)用 |
| `pearnly` + `.pub` | GitHub 部署 webhook 用 |
| `known_hosts` | 已知服务器指纹 |

**怎么找到这个目录(Windows)**:
1. Win + R → 输入 `%USERPROFILE%\.ssh` → Enter
2. 看到 9 个文件 → Ctrl+A 全选 → 右键复制 → 粘到 U 盘 `ssh_backup\` 文件夹

#### 文件清单 C · 测试账号密码(自己记下)

打开**记事本**新建一个文件 · 抄下:

```
Pearnly 测试账号(loop 跑 E2E 用):
PEARNLY_E2E_USER = <你之前填的邮箱>
PEARNLY_E2E_PASS = <你之前填的密码>

(可选)Pearnly 超管账号:
PEARNLY_ADMIN_USER = <Earn 的邮箱>
PEARNLY_ADMIN_PASS = <Earn 的密码>
```

不知道当前值是啥?在旧电脑跑这个查:

```powershell
echo "USER: $env:PEARNLY_E2E_USER"
echo "PASS: $env:PEARNLY_E2E_PASS"
```

显示出来抄下保存 · **不要存到 U 盘里跟代码一起**(分开存 · 不上网)

### 1.3 浏览器书签同步

打开 Chrome / Edge · 登你的 Google 账号 / Microsoft 账号 · 开"同步"开关。
新电脑装同一个浏览器登同样账号 → 书签自动同步。

确认这几个后台你能从书签找到:
- https://dash.cloudflare.com(域名 + CDN)
- https://supabase.com/dashboard(数据库)
- https://github.com/skin306152-star/pearnly-app(代码仓库)
- https://console.anthropic.com(Claude API 后台)
- https://pearnly.com(产品本身)

### 1.4 确认你的 Anthropic 账号能在新电脑登录

打开 https://claude.ai · 看你用啥邮箱登的(skin306152@gmail.com 还是别的)
确保你记得密码 · 或者绑定了 Google OAuth(更省事)

---

## 💾 第二步 · 旧电脑物理打包(15 分钟)

**最简方案 · 一个 U 盘搞定**:

```
U 盘/
├── pearnly_backup_2026-05-28/
│   ├── .env.local              ← 项目根的本地配置
│   ├── settings.local.json     ← Claude 项目设置
│   ├── launch.json             ← Claude 启动配置
│   └── README.txt              ← 写一句"放回 D:\Users\Skin\Desktop\pearnly_project\ 对应位置"
│
├── ssh_backup/
│   └── (整个 .ssh 目录 9 个文件)
│
└── accounts_2026-05-28.txt     ← 测试账号密码(分开存 · 别忘 U 盘)
```

可选 · 整个项目目录也带一份(防 GitHub 哪天挂了):
- `D:\Users\Skin\Desktop\pearnly_project\` 整个 zip 一下塞 U 盘(注意:**排除** `node_modules` / `__pycache__` / `dist` / `.venv` · 这些重装会生成 · 不带省 GB 级空间)

---

## 🖥️ 第三步 · 新电脑装软件(60 分钟 · 大部分时间在下载)

### 3.1 装 Git

下载:https://git-scm.com/download/win(Windows)或 https://git-scm.com/download/mac
点 Next 一路装完 · 用默认设置就行。

装完打开 PowerShell(Win + R 输入 `pwsh` 或 `powershell`)验证:
```powershell
git --version
```
出现 `git version 2.x.x` = OK

### 3.2 装 Node.js(给前端 build + Playwright E2E 用)

下载 LTS 版本(绿色那个 · 别选 Current):https://nodejs.org/
一路 Next 默认安装。

验证:
```powershell
node --version    # 应显示 v20.x.x 或 v22.x.x
npm --version     # 应显示 10.x.x
```

### 3.3 装 Python 3.11

下载:https://www.python.org/downloads/
⚠️ **重要**:第一个安装界面**必须勾** "Add Python to PATH" 选项 · 否则后面用不了

验证:
```powershell
python --version    # 应显示 Python 3.11.x
pip --version       # 应显示 pip 24.x
```

### 3.4 装 GitHub CLI

下载:https://cli.github.com/
默认装到 `C:\Program Files\GitHub CLI\gh.exe`(路径要跟旧电脑一样 · 因为铁律 #22 写死了这个路径)

验证 + 登录:
```powershell
& "C:\Program Files\GitHub CLI\gh.exe" --version
& "C:\Program Files\GitHub CLI\gh.exe" auth login
```

登录走浏览器 OAuth · 跟着提示选:
- GitHub.com
- HTTPS
- Login with web browser
- 浏览器弹窗 · 登 skin306152-star 账号 · 点 Authorize

### 3.5 装 Claude Code 本身

下载:https://claude.com/claude-code
按官网指引安装。

装完打开 Claude Code · 登录你的 Anthropic 账号(用旧电脑同样邮箱)· 订阅会自动跟过来。

### 3.6 装 VS Code(可选 · 看代码用)

下载:https://code.visualstudio.com/
装完打开就行 · Claude Code 会自动检测到。

---

## 🔑 第四步 · 恢复 SSH 密钥(10 分钟)

### 4.1 把 U 盘里的 ssh_backup 放回新电脑

1. Win + R → 输入 `%USERPROFILE%` → Enter(打开你的用户目录)
2. 如果**没有** `.ssh` 文件夹:右键 → 新建文件夹 → 命名 `.ssh`
3. 把 U 盘 `ssh_backup\` 里 9 个文件全部复制进新建的 `.ssh\` 目录

### 4.2 修 Windows 权限(SSH 严格要求只你能读)

打开 PowerShell:

```powershell
# 给 .ssh 目录加权限
$sshDir = "$env:USERPROFILE\.ssh"
icacls $sshDir /inheritance:r
icacls $sshDir /grant:r "${env:USERNAME}:(F)"

# 给所有 key 文件加权限
Get-ChildItem $sshDir -File | ForEach-Object {
    icacls $_.FullName /inheritance:r
    icacls $_.FullName /grant:r "${env:USERNAME}:(R)"
}
```

### 4.3 测连接

```powershell
# 测连 Pearnly 服务器
ssh root@45.76.53.194 "echo OK; df -h /"

# 测连 GitHub
ssh -T git@github.com
```

如果出现 "Welcome to Vultr" 或 "Hi skin306152-star!" = 成功 ✅

如果报 "Permission denied" → 权限没修对 · 重跑 4.2

---

## 📂 第五步 · 拉项目代码(5 分钟)

### 5.1 决定放哪

旧电脑:`D:\Users\Skin\Desktop\pearnly_project\`

新电脑建议放同样路径(很多文档里写死了这个路径)· 或者改成你的新桌面路径(后面文档里 Search & Replace)。

### 5.2 克隆

```powershell
# 先建上级目录
cd $env:USERPROFILE\Desktop
mkdir -Force pearnly_project_parent
cd pearnly_project_parent

# 克隆
git clone https://github.com/skin306152-star/pearnly-app.git pearnly_project
cd pearnly_project
```

如果走 HTTPS · 会弹浏览器让你登 GitHub 授权(已经 4.1 配过 SSH 也可以用 `git@github.com:skin306152-star/pearnly-app.git` 走 SSH)

### 5.3 配 git 用户名(commit 用)

```powershell
git config --global user.name "ZIHAO"
git config --global user.email "skin306152@gmail.com"
```

---

## 🔧 第六步 · 还原本地配置(5 分钟)

### 6.1 把 U 盘 `pearnly_backup_2026-05-28/` 里的 3 个文件放回去

| 文件 | 放到 |
|------|------|
| `.env.local` | `pearnly_project\.env.local`(项目根) |
| `settings.local.json` | `pearnly_project\.claude\settings.local.json` |
| `launch.json` | `pearnly_project\.claude\launch.json` |

⚠️ `.claude\` 目录新电脑上可能不存在 · 先 `mkdir .claude` 再放

### 6.2 设测试账号环境变量

打开 PowerShell · 替换尖括号里的内容跑:

```powershell
# 永久存到 Windows 注册表(setx 写 HKCU)
setx PEARNLY_E2E_USER "<你的测试账号邮箱>" > $null
setx PEARNLY_E2E_PASS "<你的测试账号密码>" > $null
setx PEARNLY_ADMIN_USER "<Earn 超管邮箱>" > $null
setx PEARNLY_ADMIN_PASS "<Earn 超管密码>" > $null

# 当前 session 也立即生效
$env:PEARNLY_E2E_USER = "<你的测试账号邮箱>"
$env:PEARNLY_E2E_PASS = "<你的测试账号密码>"
$env:PEARNLY_ADMIN_USER = "<Earn 超管邮箱>"
$env:PEARNLY_ADMIN_PASS = "<Earn 超管密码>"

# 验证(应该输出账号)
echo "USER: $env:PEARNLY_E2E_USER"
```

⚠️ 设完关掉 PowerShell · 重开一个新窗口 · setx 才永久生效(新进程才继承)。

---

## 📦 第七步 · 装项目依赖(20 分钟 · 大部分在下载)

打开 PowerShell · cd 到项目目录:

```powershell
cd $env:USERPROFILE\Desktop\pearnly_project_parent\pearnly_project
```

### 7.1 装 Python 依赖

```powershell
pip install -r requirements.txt
```

如果有 requirements-dev.txt 也装:
```powershell
pip install -r requirements-dev.txt
```

### 7.2 装 Node 依赖

```powershell
npm install
```

### 7.3 装 Playwright 浏览器(给 E2E 用)

```powershell
npx playwright install chromium
```

### 7.4 跑一次 build 验证

```powershell
npm run build
```

出现 "✓ built in Xms" + 没红色 ERROR = OK

---

## ✅ 第八步 · 验收(10 分钟)

打开 Claude Code · cd 到 pearnly_project · 跟它说:

```
读 docs/refactor/MIGRATION_TO_NEW_COMPUTER.md · 我刚迁完电脑 · 帮我验证一切就绪:
1. git status 干净
2. git log 显示最新 commit 跟 GitHub 一致
3. echo $env:PEARNLY_E2E_USER 显示有账号
4. ssh root@45.76.53.194 "echo OK" 通
5. & "C:\Program Files\GitHub CLI\gh.exe" auth status 显示已登
6. npm run build 通
7. python -c "import db; print('db OK')" 通
全 ✅ 就告诉我 "可以接着推项目了" · 任一不通就告诉我哪里挂了。
```

它会一项一项跑 + 报告。全绿 → 你迁完了 ✅

---

## 🚀 接着推项目 · 告诉 Claude 怎么继续

迁完后打开新电脑 Claude Code · 第一句话发:

```
读 docs/refactor/ZIHAO_RECOVERY_GUIDE.md(救命指南)+ CLAUDE.md/STATE_PEARNLY.md 头部 ·
我刚迁完电脑 · 告诉我整顿期现在跑到哪一步了 · 我下一步该做什么。
```

它会自动接上 · 告诉你窗口 A/C 跑到哪 · 接下来贴 Loop 2 还是 Loop 3 指令。

---

## 🆘 常见坑(踩到再看)

### 坑 1 · `ssh root@45.76.53.194` 报 Permission denied

→ SSH key 权限没修对(第四步 4.2 跑漏了 · 重跑)
→ 或者 key 没放对位置(在 `%USERPROFILE%\.ssh\` 下 · 不在 Desktop)

### 坑 2 · `git push` 报 401 / 权限错

→ GitHub CLI 没登 · 跑 `& "C:\Program Files\GitHub CLI\gh.exe" auth login` 重新登
→ 或者本地 remote 还指向 SSH 但 SSH key 没设 · 跑 `git remote set-url origin https://github.com/skin306152-star/pearnly-app.git` 改 HTTPS

### 坑 3 · Claude Code 不认订阅

→ 退出登录 → 重新登 Anthropic 账号(skin306152@gmail.com)
→ 订阅信息在云端 · 不在电脑本地 · 重登就回来

### 坑 4 · `npm install` 报 node-gyp / Python 错

→ 一般是 Node 版本不对 · 装 LTS(20.x 或 22.x · 不要 odd 版本)
→ 或者老的 lock 文件冲突 · 删 `node_modules` + `package-lock.json` 后重 `npm install`

### 坑 5 · 测试账号环境变量设了但不生效

→ setx 必须**关掉当前 PowerShell 重开**才永久生效(子进程不继承父进程设的环境变量)
→ 验证:重开 PowerShell 后跑 `echo $env:PEARNLY_E2E_USER` · 还空就 setx 没成功

### 坑 6 · home.css 不存在 / 部分文件缺

→ Pearnly 用了 vite + 拆切片 · `home.css` 已经拆成 36 个 `static/home-*.css` · 不是 bug
→ 跑 `npm run build` 会自动生成 dist/

### 坑 7 · 旧电脑能跑的脚本新电脑不行

→ 路径硬编码问题(Pearnly 历史包袱有些 hardcoded `D:\Users\Skin\Desktop\pearnly_project`)
→ 跟 Claude 说:"扫一下项目里硬编码的 `D:\Users\Skin` 路径 · 列出来 · 我看哪些要改"

---

## 📋 最简版"换电脑 60 秒概览"(打印这一张就够)

```
旧电脑 ─────────────────────────────────────────────────────
1. 让 Claude 跑 git status 确认全推 GitHub
2. U 盘备份:
   - .env.local
   - .claude/settings.local.json + launch.json
   - 整个 C:\Users\<你>\.ssh\
   - 记事本记下 4 个测试账号密码

新电脑 ─────────────────────────────────────────────────────
3. 装:Git / Node 20 LTS / Python 3.11 / GitHub CLI / Claude Code
4. SSH key 放回 %USERPROFILE%\.ssh\ + 改权限
5. git clone https://github.com/skin306152-star/pearnly-app.git pearnly_project
6. U 盘 3 个本地配置文件放回项目对应位置
7. setx 设 4 个 PEARNLY_* 环境变量
8. cd 项目 → pip install -r requirements.txt + npm install + npx playwright install
9. 打开 Claude Code → 让它验收(第八步)
10. 全绿 → 跟它说"接着推项目"
```

---

## 💡 终极方案 · 备份你不想再走一遍这个流程

如果你觉得这个流程太长 · 强烈建议**新电脑装完后立刻**:

1. 用 Windows 自带"备份和还原(Windows 7)"做一次系统镜像 · 存外置硬盘
2. 或者用 Macrium Reflect Free / Acronis 做全盘 clone

下次再换电脑 · 直接还原镜像 · 5 分钟所有软件 + 配置 + Claude 登录全回来。

---

## 🎯 一句话总结

**所有"代码 + 文档"都在 GitHub** · 换电脑 = 装软件 + 拷 4 样东西(.env.local + SSH key + .claude 配置 + 测试账号密码)+ git clone。**1-2 小时搞定 · 比想象中简单**。

最大坑不是技术 · 是**忘了带 SSH key 和测试账号密码**。这两样**现在就备份**到 U 盘 + 网盘双保险 · 防你电脑突然挂掉。

---

*本文档由 Claude(对话窗口)在 2026-05-28 撰写。下次更新触发条件:Pearnly 装了新依赖 / 新增本地配置文件 / 服务器迁移。*
