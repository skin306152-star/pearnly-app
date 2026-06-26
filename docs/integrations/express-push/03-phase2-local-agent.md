# P2 施工单 · Express 本地 Agent(出站拉取 + 录入 Express)

> 状态:**STAGED** —— P1.1 转绿 + P1 合并后再发给施工窗口。先读 `00-master-plan.md` + `02-phase1-backend.md`(后端契约已定)。
> 本棒目标:做出客户本地跑的小程序 Agent —— heartbeat → lease → **把单子录进 Express DATAT** → ack,**打通真机闭环**。
> 拆两步:**P2a = Agent 骨架 + RPA 录入(主路径,先打通)**;**P2b = DBF 直写(高级,带护栏)**。本单先做 P2a,P2b 末尾列要点。

## 0. 边界
- Agent 是**独立程序**,放新目录 `tools/express-agent/`(Python),**不是** FastAPI app 的一部分、不进 `services/`、不碰云端代码。
- 只通过 P1 的 Agent 接口说话:`POST /api/erp/agent/{heartbeat,lease,ack}`(Bearer token)。**Agent 不直连云端 DB**。
- **账套白名单**:Agent 端再钉一道 —— 只允许录入 `config.account_set` 且 ∈ `{DATAT}`;载荷 account_set 不符直接 ack failed 并告警,**绝不录入其它账套**。
- 单文件 <500、单一职责、去 AI 味、每模块≥1 测试(可 mock Express 交互)。

## 1. Agent 架构(P2a)
```
循环(默认 5s):
  heartbeat ──→ 在线/拿到 account_set,method
  lease(max=N) ──→ 取待录入载荷列表
  for job in jobs:
     白名单校验(account_set)
     幂等预检:按 ref_no 查 Express 该账套是否已有此单 → 有则 ack success(带已存在单号)跳过
     注入(RPA / DBF 按 config.method)
     读回确认(铁律 #9:操作成功 ≠ 真写入,必读回)
     ack(success + express_docnum  /  failed + error)
```
- **配置**(P2a 用本地配置文件 `agent.toml`,完整设置 UI 是 P3):`server_url`、`token`、`account_set`、`method`、`express_path`(ExpressI.exe)、`express_login`(账号/密码,本地加密存)。
- **健壮性**:网络断/Express 没开 → 不崩,等下个循环;lease 到的单做不完留给租约到期重领(P1 已支持);连续失败上报 ack failed(P1 累计 3 次转 manual)。

## 2. RPA 录入(P2a 核心)
- 用 Windows UI 自动化(pywinauto / 键盘流)驱动 ExpressI.exe;Express 自己算单号/税额/过账/库存/索引 —— **零账套损坏**。
- 流程:登录(BIT9)→ 选账套 DATAT → 菜单 `1.ซื้อ` → 按 `doctype` 选 赊购(RR)/现购(HP)→ 填 供应商(`supplier_new` 则先建 APMAS)/票号/日期(佛历)/明细金额/VAT → 保存 → **读回拿 Express 真单号**回 ack。
- ⚠️ **第一步先做 RPA 录入流程勘探**:在 DATAT 用 Agent 录一张样例 RR 单走通、记下精确按键序列(Express 是键盘驱动,F 键 + Tab,跨版本稳),把序列写进 `rpa_flow.md` 再固化成脚本。勘探就在 DATAT(测试账套,允许写),录完可在 Express 里作废该测试单。
- **幂等**:录入前按 `ref_no`+供应商查 DATAT 是否已存在该采购单,存在则不重录(防 Agent 重启/重领导致重复记账)。

## 3. 兜底/安全(P2a)
- 账套白名单双钉(云端 lease 已钉 + Agent 端再钉)。
- 幂等预检(按 ref_no 查重)。
- 读回确认(不读回不算成功)。
- token 本地加密存(DPAPI / 同 kms 思路);日志不落 token/密码/原始票面。
- 干跑模式 `--dry-run`:走完 lease + 映射校验 + 打印将录入的分录,但**不真写 Express**(给无 Express 环境做冒烟)。

## 4. 验证(写清楚,施工窗口跑齐交 PM 判 · PM 不自己跑)
1. **可 headless 跑的**(施工窗口跑,附结果):Agent 单测(mock Express 交互层)= lease 解析 / 白名单拒非 DATAT / 幂等跳过 / ack 回填单号 / 断网不崩。`--dry-run` 对一条样例 lease 打印正确分录。
2. **真机闭环(Owner 真机,PM 给清单)**:Owner 在装有 Express 的机器上:① 配 `agent.toml`(token 从 P3 或 P1 token 接口拿)② 起 Agent ③ 从 Pearnly 推一张样例发票 → 看 Agent lease 到 → **DATAT 里真出现一张 RR 单、分录与预览一致、Pearnly 状态翻 success 带 Express 单号**。Owner 跑这步,结果交 PM 判。

## 5. P2b · DBF 直写(高级 · 后做)
- 直接写 `APTRN/ISVAT/GLJNL/GLJNLIT/APBAL`(+ 存货则 `STCRD`)→ 重建 `.CDX` → 推进 `ISRUN` 单号。
- 护栏(强制):写前**自动备份该账套** → 单事务 → 写后**校验借贷平衡 + 读回** → 失败**回滚**。账套路径白名单只允许 DATAT。
- 仅 `config.method='dbf'` 且用户在 P3 勾选风险后启用;默认 RPA。
- 单独施工单 `04-phase2b-dbf-write.md`(P2a 真机闭环过了再起)。

## 6. 交付(P2a)
- `tools/express-agent/`(轮询循环 / RPA 注入 / 配置 / 白名单 / 幂等 / dry-run）+ 单测 + `rpa_flow.md`(真键序记录)。
- 不 push master(未验收)。汇报含:单测数 + dry-run 输出 + RPA 勘探键序;真机闭环留 Owner 跑、PM 判。
