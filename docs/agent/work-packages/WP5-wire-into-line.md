# WP5 · 接进 LINE(整合窗口 · 最后做)

> 给执行窗口:**依赖 WP1+WP2+WP4 全部落地**。这是唯一碰现有 LINE 链路的窗口,把插座接到真实入口,跑真机端到端。改的是登录/OCR/推送外的对话入口,但仍属主路径 —— **动手前对照本包,有疑问先报 Zihao**。

## 背景
- `../MASTER-PLAN.md §3 M1/M2` + `../M1-SOCKET-DESIGN.md §7`(loop 编排)。
- 目标:LINE 收到消息 → 先过钥匙闸(WP2)→ 开且命中灰度 → 走新 Agent loop;否则走现状(`line_agent.understand` 旧行为)。**关掉=逐字节回退现状**。

## 现状事实(已探查)
- webhook 入口:`routes/line_webhook_routes.py:line_webhook()`(L437)→ `_handle_line_text()`(L258)→ `services/line_binding/line_expense.py:handle_expense_text()`(L14)。
- 现大脑:`services/expense/line_agent.py:understand()`(L127)一次调用吐 JSON;`_dispatch_agent()`(line_expense.py L171)按 intent 分发到 9 个处理器。
- 多轮:`line_chat_memory.recent()/note()`;pending:`conversation.save_pending()`。
- 写闸:`may_write()`(line_agent.py L169)—— 新 loop 的 B 档确认是它的超集,保留哲学。

## 要建什么
1. 在 `handle_expense_text()` 入口(或 `_handle_line_text`)加**钥匙闸**:`feature_flags.agent_enabled_for(user_id)`。
   - 关/未命中 → 原样走现状 `understand()` + `_dispatch_agent()`(一行不改旧路径)。
   - 开且命中 → 走新 `services/agent/loop.handle_turn(text, ctx)`。
2. 构造 `AgentContext`:从现有 user dict 取 user/tenant_id/workspace_client_id(复用 `_tid` / `wc.active_workspace_for_request`)。
3. 回复经现成 `line_reply.reply_text_context()` 发回 LINE。
4. 多轮 pending:新 loop 与旧 `conversation.save_pending` 兼容(同一会话态存储)。
5. (M2)旧记账意图(record/query/undo/edit)作为工具并进 manifest;最终统一走 Agent,`understand()` 退役为其中一个工具。**M1 阶段先并存**:只读新工具走 Agent,记账等仍走旧路,逐步迁。

## 验收(真机 · 不是 grep)
- 灰度账号(skin)LINE 真发"查本月识别几张"→ 新 Agent 查到真数 → 人话回。
- 真发"帮我改密码"→ out_of_scope 引导。
- 编造场景 → slots 拦 → 反问。
- **关掉超管开关 → 同样消息逐字节回到旧行为**(集成测试 + 真机各一遍)。
- 非灰度账号 → 始终走现状,无任何变化。
- 大脑 env 切 qwen3.5 ↔ gemini → 上述全过。
- CI 6 闸 + 防漏闸绿;改 i18n 必 node --check;未真机验收不 push master。

## 不要碰
- ❌ 不改旧路径 `understand()/_dispatch_agent()` 的现有行为(只在前面加分流闸)。
- ❌ 不动网页入口(M5,LINE 验稳后)。
- ✅ 改动集中在 `line_expense.py` 入口分流 + `loop.py` 对接;旧逻辑作为 flag 关时的回退,保持可用。

## 上线
- 整合分支真机端到端过 → 超管后台 `agent_enabled` 默认关上线 → allowlist 只加 skin 灰度 → 跑稳放量 → 出问题一秒关。
