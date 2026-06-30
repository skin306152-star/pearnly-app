# WP1 · 插座核心(services/agent/ 全套)

> 给执行窗口:这是最重的一包,**单窗口独做**,WP4/WP5 等你的接口落地。照 `../M1-SOCKET-DESIGN.md` 实现,接口契约不得偏离。

## 背景(读这几样再动手)
- `../MASTER-PLAN.md`(全景 + 为什么是"插座插头")
- `../M1-SOCKET-DESIGN.md`(本包的实现蓝本 · §1~§7 是你要建的全部)
- 项目铁律:`CLAUDE.md/CLAUDE.md`(28 条)· 单文件 <500 · 每新文件 ≥1 测试 · 去 AI 味

## 现状事实(已探查 · 直接用,别重查)
- 网关门面:`services/ai_gateway/transport.py:text_to_json(prompt,text,tier,response_mime,max_tokens,timeout_s,max_retries,task)` → 按 `OCR_LLM_BACKEND` 自动切后端。**不支持 tools 透传**,走 JSON 动作模式。
- 参考骨架:`services/expense/line_agent.py:understand()`(一次调用吐 JSON 的范式)、`may_write()`(L169)、`services/expense/line_l2.py:amount_grounded()`(L33 · slots 闸的种子)。
- 多轮:`services/line_binding/line_chat_memory.py:recent()/note()`(8 条/24h)。

## 要建什么(全部新建在 `services/agent/`,不碰现有文件)
按 `M1-SOCKET-DESIGN.md §1` 的目录:
1. `contracts.py` —— §2 的全部 dataclass(ToolSpec/SlotSpec/AgentAction/SlotCheck/ToolResult/AgentContext)。
2. `manifest.py` —— §3。**M1 只登记 5~8 个 A 档只读工具**(list_history/balance/recon_overview/list_endpoints/push_log_status/count_this_month 选 5~8)。`TOOLS_BY_NAME` 索引。
3. `brain.py` —— §4。`_build_prompt`(从 manifest 自动生成工具表)+ `decide()`(调 transport.text_to_json)+ `_parse_action()`(解析失败兜底 chat)。
4. `slots.py` —— §5。`check_slots()`,泛化 amount_grounded;按 SlotSource 验接地;编造→reject,缺→missing。
5. `executor.py` —— §6。`AgentToolset`,M1 先实现 A 档只读方法(调现成 db.* service)。B 档方法留桩(M3)。
6. `loop.py` —— §7。`handle_turn()` 编排;ask/confirm 走 pending。
7. `copy_map.py` —— error_code→i18n key 映射(WP3 填值,你先建结构)。

## 验收(达标才算完)
- 5 个单测全绿:manifest 自洽、slots 拦编造、brain 解析、loop 分支、executor 只读跑通。
- `manifest.TOOLS` 的每个工具,其功能区在 `agent_registry.json` 必为 A 档(交叉核对测试)。
- 不依赖真 LINE 即可单测(executor 用 mock ctx / mock db)。
- 单文件 <500;executor 若超则拆 `executor_readonly.py` 聚合 re-export。

## 不要碰(防打架)
- ❌ 不改 `services/expense/line_agent.py` / `routes/line_webhook_routes.py`(那是 WP5)。
- ❌ 不改 `services/ai_gateway/*`(网关零改是设计原则)。
- ❌ 不建 platform_settings(那是 WP2)。
- ✅ 只在 `services/agent/` + `tests/unit/test_agent_*.py` 落文件。

## 交接产物
- `services/agent/` 全套 + 测试;一份 `services/agent/README.md` 写明各文件职责 + 加新工具的 3 步(改 manifest → 加 executor 方法 → registry 登记)。
