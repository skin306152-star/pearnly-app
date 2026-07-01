# 交接 · LINE 对话 Agent 前门收口 + M3 记账写路径 + 剩余工作(2026-07-01)

面向接手窗口。本页 = 这次做完的 + 现在的真实状态 + M3 还剩什么 + 怎么验。先读,别重做。

## 一、这次做完了什么(全绿上线 prod)

前门倒置早已上线(灰度=全量),但"新前门 + 旧确定性路"没收口 → 情绪句被问价格、几点报 UTC。本次三批收口 + M3 记账写路径开灯 + 缓存修复 + /simplify:

| commit | 内容 |
|---|---|
| `cf8727c0` | **批一·收口止血**:`loop.handle_turn` 返回 `TurnResult(kind,text)` 五态。大脑故障(crash)→ 安全兜底,**绝不掉旧路地雷**;模型主动 defer 记账/改错 → 交旧路(能力不丢)。灰度分流收进新模块 `services/line_binding/line_agent_route.py`。 |
| `318fb998` | **批二·大脑救援**:parse 失败带回 `ProviderOutcome.raw`,`loop._salvage_prose` 把干净人话当回复救回(治"写了安慰话没包 JSON 被吞成故障");`layer2_gemini._parse_json` 抠括号容错(严格路先行·OCR 零影响)。 |
| `8801ecce` | **批三·时区+兜底**:`_today()` 走 `bangkok_now()`(治"几点"报 UTC);`_grounded_fallback` 覆盖到钱工具(balance/summary/usage)。 |
| `af75d29c` | **缓存友好**:易变时间戳移出 persona 头 → ~1.5k token 静态前缀可被供应商前缀缓存命中(批三把分钟级时间戳塞头部会撞碎缓存,已修)。 |
| `4ec117d7` | **/simplify 收口**:`_grounded_fallback` 收成表驱动(`_VALUE_FB`);两处热路懒加载提模块级。 |

**核心不变量**(改任何前门逻辑都别破):
- crash(parse失败/空回复/工具名错/循环空转)→ 安全兜底一句,**不问价格/不静默错入账/不跑第二个大脑**。
- defer_record/defer_edit/无余额 → `route_gated` 返 False → 旧确定性路(记账直录/改错/撤销能力保留)。
- 钱绝不编:记账走 `executor.record_expense` 的 `amount_grounded` 唯一钱闸(模型塞原文没有的金额 → 置空 → 反问)。

## 二、现在的真实状态(接手必知)

- **写子闸 `agent_write_tools` 已全开**(`rollout: all` · enabled · prod platform_settings)。**记账写工具 record_expense 现在对所有用户可见** → 记账消息由前门大脑直接出直录卡(复用现成精致卡 + 暖话 + 撤销),不再 defer 旧路。回退:`store.set_setting("agent_write_tools", {"rollout":"allowlist"}, True)` 或 enabled=False。
- **大脑后端 = qwen-flash**,但**不是自托管**:`AGENT_BRAIN_BACKEND=selfhost` + `SELFHOST_OCR_URL=...aliyuncs.com`(阿里云百炼 MaaS 按量付费)。不是免费自建 GPU。
- **成本**:今日 64 次对话调用,日志记 ฿1.23——但那是 `costing.py` **按 Gemini 单价估的假账**(不管真实模型),真实阿里云 qwen 花费更低。实测:输入 1508 tok/次 vs 输出 40 tok/次(37×),成本几乎全在"重发的静态大提示词"→ 已做缓存友好(前缀稳定,供应商自动前缀缓存能命中)。真实账单看阿里云百炼控制台。
- **验证工具**(scratchpad,可复跑):`line_sim.py`(读/闲聊/故障路 40 条压测·0 问价格 0 崩溃逃逸)、`line_sim_write.py`(写路径 30 条·0 编造入账 0 双记)。跑真实路由代码,只注入模型层(本地无 GCP/真模型跑不了真 Gemini)。

## 三、M3 还剩什么(用户问"只剩 ERP 推送了吗")

**记账写工具(M3 前半)= 代码完成 + 闸已开 + 模拟器验过**。剩:
- ⚠️ **真机验证**:模拟器注入模型层,**没证"真 qwen-flash 在'咖啡50'时会正确调 record_expense(而非 defer/闲聊)"**。需 Zihao 用绑了 LINE 的号真机发几条(咖啡50→出卡金额对撤销可用 / 缺金额→反问不入账 / 情绪句→不误记)。skin 那个号没绑 LINE。

**推 ERP 写工具(M3 后半)= 完全没建**,这是主要剩余工程:
- `executor.push_to_erp` 还是 `not_implemented_m1` 桩。
- `loop.py` **完全没消费 `ToolSpec.confirm`** → "先复述+确认"的多轮确认状态机不存在。推 ERP 不可逆,必须走 confirm-first(设计见 `docs/agent/M3-write-tools-confirm-plan.md`,但那份把记账也设计成先确认,**修订②已改成记账直录、确认只留给推 ERP**)。
- 要建:loop 的 confirm 档(接地后不执行 → 持久化待办 + 出确认卡 → 用户点确认按钮 postback → 执行)。**复用现成零件**:`line_card_actions` 的草稿卡+按钮+nonce、`line_pending_entry` 待办存储、`line_correct` 的确认握手范式。别自己造。
- push_to_erp 真实实现 = 接现有 ERP 推送能力(Express DBF 直写 / MR.ERP HTTP 直写——**注意 MR.ERP 那套是另一个窗口在做,见 [[mrerp-directwrite-rebuild]],别撞**)+ 计费/幂等/审计 + 动手前**报方案**(碰钱+不可逆)。

**所以:M3 剩 = ①记账真机验证(Zihao)②推 ERP confirm-first 全套(主要工程·先报方案)。** "只剩 ERP 推送"基本对,但推 ERP 是从零建 confirm 状态机,不是简单接线。

## 四、/simplify 记下、本次没做的收口(接手可选做)
1. **四语兜底 dict 迁进 `agent_i18n`**:`loop._FALLBACK/_FB_BALANCE/_FB_SUMMARY/_FB_USAGE` + `line_agent_route._SAFE_FALLBACK` 现为内联 dict,应进 `services/agent/agent_i18n.py._T` 走 `render()`(已有 `agent.ok.balance` 等键)。**受 `i18n-data.js` key-parity CI 闸约束**(check_i18n strict),跨文件,单独开一轮别顺手。
2. **`TurnResult.kind` 提 `TurnKind` enum**(现字符串·5 种/2 处·低价值,taxonomy 涨到 7+ 或散到 5+ 处再做)。
3. **成本估价按真实模型**:`costing.py` 写死 Gemini 单价,可让 qwen 按真实价算(纯观测·非计费)。

## 五、坑(血泪)
- **共享工作树**:另一窗口在做 MR.ERP(services/erp/*)。提交**必用显式 pathspec**:`git commit -F msg.txt -- <只你的文件>`,否则 `git commit` 会把它暂存的 erp 文件卷进你的提交(本次第一批就中招了)。别碰 services/erp/*。
- 改受监控文件(routes/core/services/src/home)净增行 → commit message 写 `RATCHET-EXEMPT: <文件> · <原因>`(逐文件),提交后立即 watch CI 到绿。
- 单文件硬上限 500 行(`line_quick_entry.py` 已在 499,别再加)。
- push=上线;master 禁强推/amend。

## 六、关键文件
- `services/agent/loop.py` — agent 循环 + TurnResult + 救援 + 兜底 + 提示词。
- `services/line_binding/line_agent_route.py` — 灰度前门分流(reply/card/crash 接管·defer 交旧路)。
- `services/line_binding/line_agent_bridge.py` — 钥匙闸 + record_sink 装配。
- `services/agent/executor.py` — 工具实现(record_expense 真实建草稿·push_to_erp 是桩)。
- `services/agent/manifest.py` — 工具登记(ToolSpec.writes/confirm)。
- 记忆:[[line-agent-frontdoor-hardening]] [[pearnly-line-agent-model-selection]] [[ocr-llm-backend-gateway]]。
