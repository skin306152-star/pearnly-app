# 🔁 自主整顿 Loop · B/C 全阶段拆搬删（含高敏）（AUTONOMOUS_LOOP）

> **怎么用**:开新 Claude Code 窗口 → 粘下面「Loop 指令」整段 → Shift+Tab 切 auto-accept → 它自己跑。
> 配套:CLAUDE.md 铁律 #26(已含「自主 Loop 高敏例外」)+ `BATCH_STRATEGY.md`。
> 范围:**B/C 全部拆搬删**(db.py / app.py / home.js / home.css / home.html)· **含高敏** · 无人值守。
> 前提:Zihao 提供测试账号(凭据走环境变量,绝不提交进 git)。

---

## Loop 指令（粘这整段到新窗口）

```
/loop 自主整顿模式 · B/C 全阶段拆搬删(含高敏)· 无人值守 · 你自己跑别等我:

【范围 · B/C 全部拆搬删】
- B2: db.py 全部域(含 credits/auth/ocr_history/RLS)→ services/<域>/store.py
- B1: app.py 全部路由(含 login/OAuth/email-code/JWT)→ *_routes.py
- C1: home.js 全部块(含 routeTo 中枢/顶层函数群/plans-plg-line/password/line/session)→ src/home/*.js
- C3: home.html → 组件化/模板拆分
- 拆=copy-out 新文件,搬=接线(re-export / main.js import),删=自底向上按行号删 + 字节校验(保 CRLF)。

【铁律 · 高敏块的安全替身(替代"Zihao 在场")】
A. 只做【纯结构性挪代码 · 0 逻辑改】。绝不顺手改任何业务逻辑/判定/字段。
B. 推送部署后,用环境变量里的测试账号跑真账号 E2E(必含:登录 + 这块受影响的流程,如计费块就跑充值申请→审核→扣费全流程)。E2E 通过才算这块完成。
C. CI 红 或 E2E 红 → 立刻 git revert 回滚这个 commit + 单独 push,再诊断重做。绝不把红的留在 master。
D. 计费可自由测(系统无自动支付通道,充值/扣费=改内部台账数字,Earn 随时重置)。唯一边界:只动【测试账号】台账,绝不碰真付费用户(mrerp)余额。

【每一轮】
1. 读 CLAUDE.md/CLAUDE.md(铁律,重点 #26)+ STATE_PEARNLY.md + REFACTOR_MASTER_PLAN.md + docs/refactor/BATCH_STRATEGY.md(§9.5 + §10/§13),找下一个拆搬删块。
2. 抽前必 re-grep 真实行号。做这块:copy-out → 接线 → 删巨石。高敏块按上面 A 纯结构性。
3. 跑全 6 道守门,全绿才继续:npm run format:check、全量 unittest、check_imports、check_i18n、node --check <改的.js>、npm run build。
4. commit(message 含 · REFACTOR-C1/B1/B2/C3)+ 单独一条 git push origin master。
5. 用 gh run list 盯 CI;高敏块还要按 B 跑真账号 E2E。红了按 C 回滚 + 重做,直到真绿 + E2E 过。
6. 更新 STATE_PEARNLY.md + 主计划进度看板 + BATCH_STRATEGY §10/§13(每轮必写 = 持续交接)。
7. 删 home.* 大块:必须 node split('\n')/join('\n') 保 CRLF + 删前 cp 备份 + 删后字节校验(行数对 + 无 \r 的行=0),禁用 sed/python 盲写。

上下文满了会自动压缩,不用管——每轮都写了 STATE,下一轮重新读就接上。一直循环,别停下问我。
```

---

## 这套跟之前的区别

| | 之前(安全区版) | 现在(B/C 全含高敏) |
|---|---|---|
| 高敏块(登录/计费/OCR/auth/RLS) | 停下等 Zihao | **自己做**,但纯结构性 + 真账号 E2E 闸 + 失败回滚 |
| "Zihao 在场" | 必须 | **由测试账号 E2E + 自动回滚替代** |
| 计费测试 | 绝不真付 | **可自由测(无自动支付通道 · 只改测试账号内部台账 · Earn 可重置)** |

---

## 三个限制(没变)

1. 你电脑开着 + 窗口留着才跑(在你机器上,不是云端)。
2. 测试账号凭据放环境变量,**绝不提交进 git**(否则泄露)。
3. 持续用 Opus = 持续耗额度,跑一晚量不小。

---

## 残余风险(老实话 · 看一眼就行)

- 高敏自动推 master = 直接部署给真付费用户。E2E 闸 + 回滚能挡住"改崩了"的大多数,但**测试账号没覆盖到的边角**仍可能漏到生产。这是你选"全自主含高敏"换来的速度,代价在此。
- 缓解全自动:回滚机制保证"红的不留在 master";真账号 E2E 保证"登录/受影响流程是通的"才算数。
- **真实成本只有两笔小钱(非客户金钱)**:① 跑 OCR 测试烧 Gemini token;② 若测试环境配了 `SLIPOK_API_KEY`,每次验截图可能计一笔 SlipOK 小额费。都是运营 pennies,不是真付费用户的钱。

---

*配套铁律 #26(自主 Loop 高敏例外)+ BATCH_STRATEGY · 整顿搞完即归档。*
