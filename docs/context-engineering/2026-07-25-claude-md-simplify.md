# CLAUDE.md 瘦身对照表(2026-07-25)

出处:Anthropic 官方博客《[The new rules of context engineering for Claude 5 generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models)》(2026-07-24 · Thariq Shihipar)。文章核心:给 Claude Code 的系统提示词删掉 80%+,编码评测无可测量损失;旧一代模型需要的硬规矩,在 Claude 5 一代上变成枷锁。三条直接适用:CLAUDE.md 只留 repo 说明 + 代码库的坑(别写"显然的事")· 验证类指令做成 skill 从 CLAUDE.md 引 · 长内容渐进披露成一棵按需装载的文件树。

## 结果

| | 之前 | 之后 |
|---|---|---|
| `CLAUDE.md/CLAUDE.md` | 1470 行 / 82.4 KB(自称"每次启动必须完整读完") | 约 90 行 / ~7 KB(按需查) |
| 项目 skills | 0 个(`.claude/skills` 不存在) | 8 个,按需自动装载 |
| 旧全文 | — | 冻结在 `CLAUDE.md/ARCHIVE_CLAUDE_LEGACY.md` |

常驻指令量估算:约 41k token → 约 5k token(其余按需装载)。

## 一、删掉的:已过期 / 历史(约 480 行)

| 段(旧文件行号) | 为什么删得掉 |
|---|---|
| 整顿模式段 L8-30 | 2026-07-01 已解除,文中自认"转历史" |
| #18 整顿期 0 新功能 L380-398 | 同上 |
| #19 必读 4 文档 L401-423 | 整顿期产物;同内容在 AGENTS.md §0、本文件顶部、session banner 共 4 处 |
| #20 commit 必含 `REFACTOR-<id>` L426-455 | 整顿期专属,现走 Conventional Commits |
| #21 整改期不污染 L506-552 | baseline 写 `home.js 33254 行`,该文件已不存在 |
| #23 整顿期 8 条硬门槛 L556-574 | 与 #27 机械闸重叠,权威在 `REFACTOR_MASTER_PLAN.md` |
| #30 目录重组 L724-734 | 2026-06-03 已上线 |
| 屎山治理铁律 L838-857 | "home.js 1.3MB/3 万行"、"Playwright 0 项"全过期 |
| 导航 IA 铁律 L738-796 | 基准文件在 `D:\Users\Skin\...`(D 盘不存在),Phase 0-8 全完成 |
| 当前版本状态 / 已完成 / 正在进行 / 下一个任务 / 历史任务 / 模块优先级 / 版本历史 L1325-1428 | 全是 2026-05-12 快照(比重写日早 2.5 个月);活地图是 STATE 状态卡 |

## 二、删掉的:会主动带错新窗口的硬错(约 90 行)

| 段(旧行号) | 错的内容 | 真相 |
|---|---|---|
| 本地文件结构 L882-899 · 路径规则 L1093-1101 | `D:\Users\Skin\Desktop\pearnly_project\` | `C:\Users\skin3\Desktop\pearnly-app`(D 盘已验证不存在) |
| 部署流程 L1043-1052 | `git push origin main` | 分支是 `master`(同文件 L1055 自己又写了 master,自相矛盾) |
| scp 备用方案 L1057-1064 | `root@45.76.53.194`(东京) | 现役 `66.42.49.213`(新加坡) |
| i18n 实现方式 L1207-1210 | "home.js translations 对象里补齐" | 真源 `static/i18n-data.js` 的 `window.I18N`(2026-05-25 抽出) |
| 版本号规则 L1088-1091 | `v118.主模块.子任务.微版本` | 已停用 |

## 三、删掉的:互相打架的指令(文章点名的 conflicting messages)

| 冲突 | 打架双方 | 裁决 |
|---|---|---|
| 要不要通读 | L2「每次启动必须完整读完本文件」 vs AGENTS.md「别一上来啃大文件」 | 删 L2,改"按需查" |
| push 授权 | #16 C 档位(6 条红线含"db.py migration 必问") vs #26「所有改动自做自检即 push」 | 删 #16,只留 #26 |
| 收尾格式 | §5 ASCII 框收尾报告 vs #29「先 /simplify 再重写状态卡」 | 统一进 `wrapup` skill |
| 开工姿势 | 沟通规则 #0「默认 Plan Mode 等确认」 vs #26 自做自检即 push | 删 Plan Mode 条 |
| 修多少 | #1「修一类不修一处」 vs 记忆「只修我发现的」 | 保留并写清边界:同一 pattern 一次修完 = 要;跨到别的 bug 类 = 另开一单 |
| 闸有几道 | #26/GATES.md 写 13 道 vs AGENTS.md §4 与 banner 写"守门 6 道" vs GATES.md 表里实际 21 行 | 唯一源 = `docs/GATES.md`,计数已改 21;其余全部改成指针 |

## 四、下沉成 skill 的(约 500 行 → `.claude/skills/`)

| 旧位置 | 新 skill |
|---|---|
| #25 自跑闭环 · #13 不许 sync mock 证明 async · #10 async tripwire · 真浏览器验收硬门 · #22 gh CLI 盯 CI | `verification` |
| 前端提交纪律 · CRLF 禁忌 · 色板/图标/手机端 · UI 闸 · 先确认生产真实路径 | `frontend-change` |
| #7 无 API 走 Playwright · #8 真样本 ground truth · #9 响应码≠成功 · #11 listing retry · companion 发版 | `erp-integration` |
| 部署流程 · #6 release_notes 4 语规则与示例 · commit 规范 · 共享树纪律 | `deploy-release` |
| #24 磁盘卫生 · nginx/journalctl 分层定位 · 部署没生效 | `debug-prod-500` |
| i18n 17 项清单 · subscribeI18n · adm-* 例外 · check_i18n 闸 | `i18n-4lang` |
| discovery 三问 · 市场对标 · #28 落地 4 问 · #17 巨石封锁 | `new-feature-discovery` |
| §5 收尾模式 · #29 收尾跑 simplify · 报告口径 | `wrapup` |

## 五、留在轻量 CLAUDE.md 的(约 90 行)

只留两类:**代码库的坑**(`get_cursor(commit=True)`、Pydantic response_model、dist 同提交、`?v=` 破缓存、CRLF 禁忌、只认 CSS 令牌、`body.ok` 单一事实源)和**业务红线**(`workspace_client_id` ≠ `client_id`、`erp_push_logs` 唯一源、四态诚实、核对表不判定、不碰真余额),外加硬线 4 条 + skills 索引 + 文档地图。

## 六、顺手修的三个真缺陷

1. **本地 pre-push 闸没生效**:`git config core.hooksPath` 指向 `.git/hooks`(只有 `.sample`),真钩子在 `scripts/git-hooks/pre-push` 从未挂上 —— 而 GATES.md 与旧铁律 #26 都写"pre-push 本地硬拦"。已改 `core.hooksPath = scripts/git-hooks`(每台机器/每个 worktree 需各自设一次)。
2. `docs/GATES.md` 标题写"13 道闸",表里实际 21 道 → 已改。
3. `scripts/session_banner.sh` 每个新窗口注入的尾行仍是"整顿封锁期 0 新功能 · 守门 6 道 · 署名 Opus 4.8 · 28 铁律" → 已改成当前事实。

## 七、维护约定

- 新增的"坑"进轻量 CLAUDE.md(一两行,写 why);新增的"做法"进对应 skill,不要回流到 CLAUDE.md
- skill 超长就拆成多文件(渐进披露),别把一个 SKILL.md 写成第二块巨石
- 每次有铁律级决定,先问:这是坑(→CLAUDE.md)、做法(→skill)、还是当时的状态(→STATE 状态卡)?
