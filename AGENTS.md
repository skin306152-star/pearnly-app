# AGENTS.md · Pearnly 唯一入口(所有 AI 窗口先读这一页)

> **这是唯一的"必读"。** 故意保持一页。完整宪法在 `CLAUDE.md/CLAUDE.md`(铁律细节),业务概念在 `docs/agent/`,但**进窗口先把这页 + STATE 状态卡读完 + 跑一次进度脚本**就能开工,别一上来啃 7000 行。
> 最后更新:2026-06-01(MR.ERP DMS UI 实测回归:4 缺陷已修已上线 11850050 · DMS-UI-004 待 live · 等 Codex 复测 · 整顿主线暂停)

---

## 0. 进窗口 60 秒必做(顺序别乱)

```
1. git branch --show-current        # 不是 master 立刻 git checkout master(铁律 #14)
2. python scripts/refactor_progress.py   # ← 看【实时】数字。永不信任何文档里手写的行数!
3. 读 CLAUDE.md/STATE_PEARNLY.md 顶部「状态卡」(分割线以上 · ≤30 行 · 当前 task/最后 commit/未 push)
4. 读本文件 §2(今天敲定的认知)+ §8(文档地图)+ docs/agent/TASK_MODES.md(识别 Zihao 要哪种活)
5. git log --oneline -10 + git status   # 有没有本地未 push 的 commit
```

> **数字只信脚本**:STATE / 主计划 / 任何文档里手写的"home.js 多少行"都可能 stale。要数字 = 跑 `scripts/refactor_progress.py`。这条是治漂移的第一招。

---

## 1. 当前在干啥(整顿期 · 2026-05 起)

- **⏳ 当前实况(2026-06-01)**:**整顿主线暂停**。在做 **Zihao 例外任务:MR.ERP DMS 汽车销售 身份证→订车单集成**(adapter=`mrerp_dms`·已上线 prod 版本 `11850050`(commit 733b3a9)。**UI 实测首轮已修 4 缺陷上线**:003 身份证不转PDF+后端栅格化 / 005 DMS不入发票推送列表 / TC1.4 测试按钮POST / 006 i18n兜底+4语补键;**DMS-UI-004 新建客户失败 ERR_DMS_CUSTOMER_CREATE 待 dmstest live 探查**(疑点:地理主档 ID 空)。**状态=等 Codex 复测**。计划 `docs/integrations/mrerp-dms-ui-test-plan.md`(本地未 commit)· 全貌见 STATE 状态卡 + 记忆 [[mrerp-dms-integration]] + `docs/integrations/mrerp-dms-integration-handoff.md`。例外任务 commit 走 `MRERP-DMS-INTEGRATION` tag(非 REFACTOR-)。
- **模式**:整顿封锁期(铁律 #18)· **0 新功能** · 只做 `REFACTOR_MASTER_PLAN.md` 的 9 阶段 task(**当前因例外任务暂停·待 Zihao 拍板恢复**)。
- **当前打法**:**3 窗口并行 loop**(ADR-011 + `docs/refactor/PARALLEL_LOOP_DISPATCH.md`)· A 后端 / B 前端 / C 文档测试 · 按文件 ownership 切不撞车。
- **找下一个 task**:`REFACTOR_MASTER_PLAN.md` 顶部「当前进度看板」。
- **你的身份**:整顿主控/指挥官 · Zihao 非技术零代码 → 你全包(研究/派工/守门/E2E自测/查CI/上线/更文档)· Zihao 只:① 点权限框 ② 像用户验收 ③ 涉钱/登录拍板。

---

## 2. 今天敲定的认知(2026-05-29 · 防新窗口再踩 / 再讨论)

1. **行数:源码"拆"不"压" · 成品才压。**
   - 大厂(Chrome/Claude)你看到的小行数 = **成品**(HTML 外壳 + minify 后的 bundle)· 真源码是几千个小文件。
   - 目标 = **没有单个源文件 > 500 行**(拆成 50-100 个小模块),**不是**把某个文件写短。
   - "home.js < 200 行"指的是**入口/bootstrap 源文件**,业务全在 `src/home/*`。
   - 成品体积靠 **Vite build + minify**(= 计划 E7),不是手写。**别再问"能不能把 home.js 压到极致"——答案永远是:拆,不压。**
2. **防屎山靠 CI 机械闸,不靠自律。** check_file_size + check_line_ratchet(行数只降不升)+ CI lint-size。Loop 1 拆完切 fail 模式(铁律 #27)。
3. **改动三标准**:加新功能=新模块(不进巨石,铁律 #17);改旧功能=先有测试再改;推翻重做=`git rm` 旧的不留 `.deprecated/.legacy` 僵尸(铁律 #7)。
4. **守门 6 道**(铁律统一 2026-05-29):format:check / 全量 unittest / check_imports / check_i18n / node --check / npm run build(E2E 按需单独跑)。
5. **commit 署名 = Opus 4.8 (1M context)** · message 含 `· REFACTOR-<task-id>` · 铁律共 **28** 条。
6. **代码像资深工程师写的,不像 AI 生成的**:源码(新旧都要)**去 AI 味** —— 无过度注释/无 emoji/无防御冗余/无泛化命名(`data`/`temp`)/无调试残留(console.log/print)/DRY/用语言惯用法。拆模块时顺手清,I6 收尾审计。**全套大厂标准(源码→产品→流程→审核→测试→CI/CD→验收→安全→文档)= `docs/ENGINEERING_STANDARD.md`**,那是"拿得上台面"的 Definition of Done。

## 3. 五条最高红线(违反=事故)

1. **workspace_client_id ≠ history.client_id**(账套主体 ≠ 发票买方)· 永不混用同字段 · 见 `docs/agent/BUSINESS_GLOSSARY.md`。
2. **`erp_push_logs` 是推送状态唯一源**(铁律 #12)· 不建第二套状态表/字段 · 批次态从它派生。
3. **rows=0 / needs_mapping / failed / blocked / retrying / ERR_* 绝不显示"完成/成功"** · 见 `docs/agent/ERROR_CODES_AND_STATES.md`。
4. **未验收不 push master**(push=自动部署上线)· 改登录/注册/OCR/计费/推送主路径先报方案(铁律 #16)。
5. **schema 改动只走 Alembic + 启动 ensure 双跑**(生产不跑 `alembic upgrade` · 见 §5)。

## 4. 守门 6 道(改完必跑全绿才 commit)

```bash
npm run format:check                              # prettier(最易漏)
python -m unittest discover -s tests/unit         # 全量(不是只跑改的)
python scripts/check_imports.py --quiet
python scripts/check_i18n.py --strict
node --check <改的.js>                            # 改了 JS 才需
npm run build                                     # 改前端才需(Vite)
# E2E:npx playwright test —— 按需单独跑,非每 commit 强制
```

## 5. 关键基础设施(少踩坑)

- 服务器 `root@45.76.53.194` · `/opt/mrpilot/` · systemd `mrpilot` · uvicorn `--workers 2`。
- DB:Supabase Postgres(Pooler)· **生产不跑 `alembic upgrade`** → schema 靠启动 `ensure_*` 应用 · alembic/versions 仅留档。
- 部署:`git push origin master` → GitHub webhook → `git-deploy.sh` pull+cp+restart(~20s)· 验证 `curl https://pearnly.com/api/version`(200)。
- gh CLI:`C:\Program Files\GitHub CLI\gh.exe`(`gh run list --repo skin306152-star/pearnly-app --branch master`)。

## 6. 巨石封锁(铁律 #17/#21/#23)

- 新后端路由 → `*_routes.py` + `app.include_router`(不进 app.py)· 新前端业务 → `src/home/*`(不进 home.js)· 新 DB 业务 → `services/<域>/*.py`(不进 db.py 尾)· 新 CSS → 独立文件(不进 home.css)。

## 7. 交接 / 长跑上下文(治漂移第二招)

- **收尾 / 上下文 ~80% / 换窗口**:**重写**(不是无脑追加)STATE 顶部「状态卡」:当前 task / 最后 commit / 未 push commit / 剩余风险 / 下一步 / 在等 Zihao 啥。
- 历史明细往「分割线以下」追加。状态卡保持 ≤30 行,永远最新。
- 长跑 loop:每轮跑脚本看真数字 + 抽代码前 re-grep 真实行号(别信文档行号)+ 每轮写状态卡 → 压缩后重读 = 一页 + 脚本,永不漂。

## 8. 文档地图(别全读 · 按需取)

| 想干啥 | 读哪个 |
|---|---|
| **每窗口必读** | 本文件 + STATE 状态卡 + 跑 `refactor_progress.py` |
| 识别 Zihao 要哪种活 | `docs/agent/TASK_MODES.md` |
| 找下一个整顿 task | `REFACTOR_MASTER_PLAN.md` 进度看板 |
| **大厂全流程标准 / 什么算"完成"** | `docs/ENGINEERING_STANDARD.md`(Definition of Done · 含去 AI 味) |
| 3 窗口并行 loop 指令 | `docs/refactor/PARALLEL_LOOP_DISPATCH.md` |
| 拆巨石作战手册 | `docs/refactor/BATCH_STRATEGY.md` |
| 业务概念 / 状态机 / 验收剧本 | `docs/agent/BUSINESS_GLOSSARY · ERROR_CODES_AND_STATES · ACCEPTANCE_PLAYBOOKS` |
| 为啥这么决策 | `docs/refactor/adr-*.md`(ADR-001~011) |
| 铁律全文细节 | `CLAUDE.md/CLAUDE.md`(28 铁律) |
| 远古历史 | STATE 分割线以下 / `CLAUDE.md/BACKLOG.md` |
