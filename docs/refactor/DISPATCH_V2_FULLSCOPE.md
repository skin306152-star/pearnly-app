# 🔀 全任务并行 Loop 派工 V2(DISPATCH_V2_FULLSCOPE)

> 2026-05-30 重制 · Zihao 拍板:**全权放行高敏 + 无人值守全自动 + 范围=所有整顿计划 + 按钮全换**。
> 前置安全网:pre-push 机械闸(`scripts/git-hooks/pre-push`)已上线 · 坏码(语法/漏 import/测试红/build 坏)推送前被本地拦下 · 永不上 master。
> 配套权威:`CLAUDE.md/REFACTOR_MASTER_PLAN.md`(9 阶段全任务)· 铁律 #26/#27 · 本文 §A 审计 = 要补的"纸面规矩"。

---

## §A · 执行差距审计("立了规矩没真做" · 本轮最重要发现)

CI 三个 job:`lint`(硬拦)· `lint-size`(**warning · 不拦**)· `test`(硬拦)。

| # | 铁律/门槛 | 应该 | 真实状态 | 谁补 |
|---|---|---|---|---|
| 1 | #27.1 超 500 行 push 失败 | CI 拦 | 🟡 **warning · 根本不拦**(`ci.yml:89 continue-on-error:true`)· 现 22 文件超标 | C(等 A/B 拆完或调豁免后切 fail) |
| 2 | #27.2 棘轮只减不增 | CI 拦 | 🟡 **warning · 不拦**(同上)· 净增长这半可先切 fail | C |
| 3 | #23.7 `/ready` 必须能真失败 | 依赖挂返非 200 | 🔴 **根本没这端点**(只有 `/api/health` 永远返 ok · 不查 DB) | A |
| 4 | #5/#21.5 新 schema 只走 Alembic | 封死 ensure_* | 🟡 Alembic 装了但 15+ ensure_* 仍每次启动跑 · 无机械闸拦新增 | A(迁)+ C(加 diff 闸) |
| 5 | #23.6 覆盖率棘轮 | 降了 CI 红 | 🟢 有效但**隐式**(靠 pyproject `fail_under=21`)· 改配置能悄悄关掉 | C(改成显式 `--fail-under`) |
| 6 | #6 部署写 4 语 release_notes | 缺一不部署 | 🟢 **已有单测拦**(`test_release_notes_no_history.py`) | — |
| 7 | check_ui_consistency 接 CI | 机械闸 | 🔴 **从没接进 CI**(脚本头自己写"未来接")· 现 1787 违规 | C |
| 8 | #28/#27.3 新功能必带测试 | 机械拦 | 🔴 纯靠 PR 模板自觉(规则自己也承认难机械化) | C(部分:新 *_routes.py 必带契约测试) |
| 9 | #23 安全扫描 bandit/pip-audit/npm audit | 硬拦 | 🟢 **已硬拦**(lint job 无 continue-on-error) | — |
| 10 | i18n 4 语完整 check_i18n | 硬拦 | 🟢 **已硬拦**(test job + pre-push) | — |

**Top 5 要补**:① `/ready` 真探活(A · 唯一"健康检查等于没有"的硬伤)② lint-size 切 fail(C · 头号"纸面规矩")③ 新 ensure_*/@app. 路由 diff 闸(C)④ 覆盖率闸改显式(C)⑤ check_ui_consistency 接 CI(C)。**好消息:安全扫描 / i18n / release_notes 三条是真在执行的。**

---

## §B · 怎么执行(关键 · 先做这一步)

**🔴 解锁"高敏无人值守"的唯一前置 = Layer 2 服务器自动回滚(强烈建议先做)。**
pre-push 闸(Layer 1)挡住"代码本身坏"。但高敏(扣费/OCR)还有一种:代码本地全过、上线后运行期才崩。当前这种崩会触发 **webhook 自愈死锁 → 502 等人手动 SSH 救**(就是上次那次)。Layer 2 = 在服务器 `git-deploy.sh` 加"部署后探 `/api/health`,不活就自动 `git reset --hard` 回上个好版本 + 重启"。**有了它,"错了自己解决"才真成立**(自动回滚,不用人救)。→ 这步要 Zihao 点头 SSH 改服务器脚本。

**串行铁律(不串行 = 撞车返工)**:
- **C9 状态管理是 B 窗口的钥匙**:home.js→<200 / home.html→<1000 剩余块全卡 C9;C9 又撞"同时拆 home.js"。home.js 已到安全地板 → **C9 现在能启动 · 但它最高风险(改发票状态=VAT 钱)· 建议 Zihao 瞄一眼第一个 C9 部署**。
- **按钮统一 + UI 一致性 + C4 Design System = 同一批文件 · 合并成 B 窗口一条串行轨**(别分给不同执行者)。
- **E7 minify / C5 TS** 碰 vite.config/所有 .js → 等 home.js/home.html 拆到地板再做。

**高敏安全模型(三窗口通用 · 替代"Zihao 在场")**:① 纯结构搬家 0 逻辑改(绝不改扣费/OCR/对账算法)② push(Layer 1 拦语法/测试)③ 部署后真账号 E2E(测试账号台账 · 绝不碰 mrerp 真余额)④ E2E 红 → 自动 revert(有 Layer 2 则自动回滚)。

---

## §C · Layer 2 已上线(2026-05-30 · 已验证)+ 闭环回滚跟进协议

**已落地(commit `7f81792`/`f41da7e`/`6e10b72`)**:
- ✅ **systemd-run 起独立 cgroup** 启动 git-deploy.sh → 重启服务杀不到它 → 第 6/7 步健康检查+回滚**真生效**(根治"自愈死锁 502")。实测日志出现 `health check OK after 26s`(旧版到 `restarting` 就自杀)。
- ✅ 健康检查失败 → 自动回滚到上个好版本 + 写 `/opt/mrpilot/.deploy_rollback` marker(记坏 commit)。
- ✅ 部署成功 → 自动删 marker。
- ✅ `GET /internal/deploy/status`(无鉴权)→ `{rolled_back, detail}`,实测 `{"ok":true,"rolled_back":false}`。

**🔁 闭环跟进协议(三段 dispatch 每轮 step 0 · 兑现"崩了去解决直到搞好")**:
> 每轮**开头先**:`curl -s https://pearnly.com/internal/deploy/status`
> - `rolled_back:false` → 正常干活。
> - `rolled_back:true` 且 `detail` 里 `bad=<sha>` 是**本窗口 owns 的文件改的 commit** → **先停下修它**:`git fetch` → 若 master 顶端仍是该坏 commit 则 `git revert --no-edit <sha>` + push;把那次的活**重做对**(找出运行期为何崩:`curl /internal/deploy/log` 看 health 失败原因 / ssh 看 journalctl)→ 重新 push(pre-push 闸把关)→ 部署成功后 marker 自动清(status 回 false)= 修好了。**没清干净=还没修好,继续**。再做新活。
> - 坏 commit 不是本窗口的 → 在 STATE 记一行知会,不抢修。

三段 dispatch 全文见 chat（2026-05-30）· 各窗口 step 1 之前补上面这条 step 0。
