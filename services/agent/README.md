# services/agent · Agent 插座(M1)

通用大脑外面的一层壳:只懂 Pearnly、只能用 Pearnly 的工具、参数卡住会按真实账况反问。
插座(brain/slots/loop/executor/contracts)建一次不动;插头(manifest 里一行)随能力增量插。

设计蓝本:`docs/agent/M1-SOCKET-DESIGN.md`。施工任务书:`docs/agent/work-packages/WP1-socket-core.md`。

## 各文件职责

| 文件 | 干啥 |
|---|---|
| `contracts.py` | 数据契约:`SlotSpec`/`ToolSpec`/`AgentAction`/`SlotCheck`/`ToolResult`/`AgentContext`。各层只认这些类型。 |
| `manifest.py` | 工具清单(闭集)。大脑只能从 `TOOLS` 选。`REGISTRY_AREA` 把每个工具绑到 `agent_registry.json` 的功能区,交叉核对必为 A 档。 |
| `brain.py` | JSON 动作模式。`build_prompt`(从 manifest 自动生成工具表)+ `decide`(调 `ai_gateway.transport.text_to_json`)+ `_parse_action`(解析失败兜底 chat)。 |
| `slots.py` | 参数确定性闸。逐 slot 验接地来源,编造→reject、必填缺→missing,绝不带编造值执行。泛化自 `expense/line_l2.amount_grounded`。 |
| `executor.py` | `AgentToolset`:每个 handler 一个方法,以真实用户身份调 `core.db` 门面(复用 RLS/计费/权限,不 bypass)。M1 只实 A 档,B 档留桩。 |
| `loop.py` | 单轮编排:消息→大脑→闸→(B 档确认)→执行→回执。依赖可注入以便单测。 |
| `copy_map.py` | 唯一产出用户可见文本处:错误码→i18n key 映射 + 回执/反问渲染。M1 占位串,WP3 落 4 语 i18n(调用点不变)。 |

## 加一个新工具(3 步)

1. **改 manifest**:加一个 `ToolSpec`(名/档/泰文描述/slots/handler),并在 `REGISTRY_AREA` 绑定它的功能区。
2. **加 executor 方法**:在 `AgentToolset` 上加 `handler` 同名方法,以 `ctx` 身份调现成 service,返回 `ToolResult`。
3. **registry 登记**:确认该功能区在 `docs/agent/agent_registry.json` 的档与工具档一致(A 档工具必挂 A 档功能区),否则 `test_agent_manifest` / 防漏闸红。

提示词、闭集校验、参数闸自动跟着 manifest 走,无需改 brain/slots/loop。

## 当前工具(M1 · 全 A 档只读)

`list_history` · `history_summary` · `balance` · `usage_this_month` · `list_notifications`

## 测试

`tests/unit/test_agent_{manifest,slots,brain_parse,loop,executor}.py` —— 不依赖真 LINE / 真网关 / 真 DB(均可注入或 mock)。
