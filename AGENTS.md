# AGENTS.md · Pearnly AI Coding Agent 入口规则

> 所有 AI coding agent(Claude Code / Codex / 其它)进入本仓库**先读本文件**。
> 这是协作宪法的执行版;完整业务宪法见 `CLAUDE.md/CLAUDE.md`,本文件优先用于"怎么干活"。
> 最后更新:2026-05-26。

---

## 0. 进窗口 60 秒必做

```
1. git branch --show-current          # 不是 master 立刻 git checkout master(铁律 #14)
2. 读 CLAUDE.md/CLAUDE.md(铁律段)+ CLAUDE.md/STATE_PEARNLY.md(头部当前状态)
3. 读本文件 + docs/agent/TASK_MODES.md(识别 Zihao 要哪种活)
4. 看 git log --oneline -15 + git status(有没有本地未 push 的 commit)
```

## 1. 五条最高红线(违反=事故)

1. **workspace_client_id ≠ history.client_id**。前者=在为哪家公司做账(账套主体);后者=发票买方(→MR.ERP 应收客户)。**永不混用同一字段**。详见 `docs/agent/BUSINESS_GLOSSARY.md`。
2. **`erp_push_logs` 是推送状态的唯一来源**。不许新建第二套推送状态表/字段(铁律 #12)。批次展示态从它**派生**(`services/erp/batch_view.py`),不加新 status。
3. **rows=0 / needs_mapping / failed / blocked / retrying / ERR_NO_CUSTOMER_MAPPING 绝不显示"完成/成功"**。详见 `docs/agent/ERROR_CODES_AND_STATES.md`。
4. **未验收不 push 到 master**。push=自动部署上线(webhook)。改登录/注册/OCR/计费/推送主路径,改前先口头报方案(铁律 #16)。
5. **schema 改动只走 Alembic + 启动 ensure 双跑**(生产不跑 `alembic upgrade`,见 §5);不新增 `ensure_*` 偷渡是理想态,现实双跑——改 schema 前先确认。

## 2. 测试 / 守门命令(改完必跑对应项)

```bash
# Python 单元(本地无 DB · 702+ 测试 · ~30s)
python -m pytest tests/unit -q
# 格式 + lint(py311 目标 · 本地可能 py310)
python -m black --check --target-version py310 <改的.py>
python -m ruff check <改的.py>
python scripts/check_imports.py            # 导入健康
python scripts/check_i18n.py static/home.js --strict   # 改前端文案必跑
# 前端(src/** · Vite)
npx prettier --check src/home/<file>.js
npx eslint src/home/<file>.js              # 必须 0 error
# MR.ERP 集成(打真沙箱 · 需 .env.local 凭据 · ~30s · 会在 test01 建测试数据)
python -m pytest tests/integration/test_mrerp_adapter_happy.py -q
```

守门基线:ruff/black/check_imports 0 报错;新增/改动代码**必带契约或集成测试**(铁律 #21.7)。

## 3. push / 部署(确认放行后)

```bash
git push origin master      # 必须显式 master(铁律 #14)· webhook 自动 pull+重启
# 验证(铁律 #25.3:确认是"重启后的新进程"):
ssh root@45.76.53.194 "systemctl show mrpilot -p ActiveEnterTimestamp"   # ≥ push 时间
curl -s -o /dev/null -w '%{http_code}\n' https://pearnly.com/api/version  # 200(启动 ~30s 内可能 502)
ssh root@45.76.53.194 "journalctl -u mrpilot --since '2 min ago' | grep -iE 'startup complete|ImportError|Traceback'"
```
- 纯后端修复无 UI 改 → 不动 release_notes/版本(有先例);改 UI → 必写 4 语 release_notes(铁律 #6)。
- 后端 deploy 会重启服务 → **别在他人/Codex 验收中途 push**(重启会打断)。

## 4. 线上排障入口(只读优先 · 不先改代码)

```bash
ssh root@45.76.53.194 "df -h /"                                  # 头号嫌疑:磁盘满(铁律 #24)
ssh root@45.76.53.194 "journalctl -u mrpilot --since '24 hours ago' | grep -iE 'AutoPush|ERR_|Traceback|mrerp-lock'"
# DB 只读/写、装包/重启等 prod 写操作:被安全闸拦时停下请 Zihao 点
```
排障方法论详见 `docs/agent/TASK_MODES.md` §线上排障 + `docs/agent/ACCEPTANCE_PLAYBOOKS.md`。

## 5. 关键基础设施事实(少踩坑)

- 服务器:`root@45.76.53.194` · `/opt/mrpilot/` · systemd unit `mrpilot` · uvicorn `--workers 2`(老 PHP 单会话场景要跨进程串行 · 见 `services/erp/session_lock.py`)。
- DB:Supabase Postgres(Pooler)· **生产部署不跑 `alembic upgrade`** → schema 靠启动 `ensure_*`(app.py lifespan)应用 · alembic/versions 仅留档(双跑范式见 002/005)。
- 部署:`git push origin master` → GitHub webhook → `git-deploy.sh` pull+cp+restart。
- gh CLI:`C:\Program Files\GitHub CLI\gh.exe`(看 CI:`gh run list --repo skin306152-star/pearnly-app --branch master`)。

## 6. 巨石封锁(整顿期铁律 #17/#21/#23)

- 新后端路由 → `*_routes.py` + `app.include_router`(**不进 app.py**)。
- 新前端业务 → `src/home/*`(Vite ES module · **不进 home.js**)。
- 新 DB 业务函数 → `services/<domain>/*.py`(**不进 db.py 尾部**)。
- 新 CSS → 独立文件(不进 home.css)。

## 7. 交接硬规则(上下文 ~80% 或换窗口)

更新 `CLAUDE.md/STATE_PEARNLY.md`,写清:**本地已提交但未 push 的 commit 列表** / 测试命令 / 剩余风险 / 下一步 / 哪些在等 Zihao 确认。当前未 push 的本地 commit 见 STATE 头部。

## 8. 任务模式 → 见 `docs/agent/TASK_MODES.md`

Zihao 说「继续」时先识别:**测试项目 / 重整长跑 / 线上排障 / 产品方案 / UI 验收**,按对应模式干。
