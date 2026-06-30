# M1 插座设计 · 万能工具执行器(技术心脏)

> 这是整个 Agent 的核心框架。建一次,之后加功能/换行业/换大脑都不动它。
> 所有接口契约在此定死,执行窗口照此实现,不得偏离(偏离=整合时返工)。
>
> 现状事实带真实文件/行号,均来自 2026-06-30 探查。

---

## 0. 设计三原则(违反即推翻)

1. **网关零改**:大脑走现成 `transport.text_to_json()`,用 JSON 动作模式,不给网关加 tool-calling。理由:网关不支持 `tools` 透传(探查实证),且 JSON 模式三后端(aistudio/vertex/selfhost)通吃、qwen↔gemini env 即换。
2. **不绕安全闸**:工具以**真实用户身份**执行,复用 `get_cursor_rls(tenant_id,user_id)` / `require_perm` / `charge_ocr` / 幂等。Agent 只能做该用户本就有权做的事。
3. **参数不许编**:每个 slot 进确定性闸,来源必须是【锚点 / 端点配置 / 用户原话 / 上一步结果】之一,编造的值一律转反问。泛化现成 `amount_grounded()`。

---

## 1. 目录结构(全部新建在 `services/agent/` · 不碰现有文件)

```
services/agent/
  __init__.py
  manifest.py      # 工具清单:每个工具一个 ToolSpec(名/描述/参数/档/执行器映射)
  brain.py         # 建提示词 + 调网关(JSON 动作模式) + 解析动作
  slots.py         # 参数确定性闸(泛化 amount_grounded);判每个 arg 是否接地
  executor.py      # AgentToolset:每个工具一个方法,带鉴权/租户/计费/幂等
  loop.py          # 单轮编排:消息→大脑→闸→执行→回执;多轮反问状态机
  contracts.py     # 数据类:ToolSpec / AgentAction / ToolResult / SlotCheck
tests/unit/
  test_agent_manifest.py
  test_agent_slots.py
  test_agent_brain_parse.py
  test_agent_loop.py
```

> 每个文件 <500 行(铁律)。`executor.py` 会随工具增多变大 → 按域拆 `executor_readonly.py` / `executor_write.py` 等,`executor.py` 只做聚合 re-export。

---

## 2. 数据契约(`contracts.py`)

```python
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

Bucket = Literal["A", "B", "C", "D"]
SlotSource = Literal["user_text", "anchor", "endpoint_config", "prior_result", "model_freeform"]

@dataclass(frozen=True)
class SlotSpec:
    name: str                       # 参数名,如 "history_id"
    required: bool                  # 缺了能不能办
    source: SlotSource              # 允许的接地来源(model_freeform 仅限纯文本类如 keyword)
    desc_th: str                    # 给大脑看的泰文说明(这个参数是什么)
    desc_zh: str                    # 团队看的中文说明

@dataclass(frozen=True)
class ToolSpec:
    name: str                       # 工具名(大脑选它用),如 "list_history"
    bucket: Bucket                  # A/B/C/D
    title_th: str                   # 给大脑/用户看的人话标题
    desc_th: str                    # 这个工具干嘛(泰文,进提示词)
    slots: tuple[SlotSpec, ...]     # 参数清单
    handler: str                    # executor 上的方法名,如 "list_ocr_history"
    confirm: bool                   # B 档=True,执行前必复述确认

@dataclass
class AgentAction:
    kind: Literal["tool", "ask", "out_of_scope", "chat"]
    tool: Optional[str] = None      # kind=tool 时,选中的工具名
    args: dict[str, Any] = field(default_factory=dict)
    ask_field: Optional[str] = None # kind=ask 时,缺哪个 slot
    message: str = ""               # 给用户的话(ask/out_of_scope/chat 用)

@dataclass
class SlotCheck:
    ok: bool
    grounded: dict[str, Any]        # 通过接地的参数(可信值)
    missing: list[str]              # 必填但没接地 → 要反问的
    rejected: dict[str, str]        # 被判编造的 {slot: 原因}

@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error_code: Optional[str] = None  # 机器码,翻成人话由 CONVERSATION-SPEC
    receipt: str = ""                 # 给用户的人话回执(成功卡/失败说明)
```

---

## 3. 工具清单(`manifest.py`)—— 插头目录

每个工具一个 `ToolSpec`。**M1 只登记 5~8 个 A 档只读工具**(下表),B 档留到 M3。

```python
from services.agent.contracts import ToolSpec, SlotSpec

TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="list_history",
        bucket="A",
        title_th="ดูประวัติการสแกนเอกสาร",
        desc_th="ดูรายการเอกสาร/ใบเสร็จที่เคยสแกน เดือนนี้หรือช่วงที่ระบุ",
        slots=(
            SlotSpec("keyword", required=False, source="model_freeform",
                     desc_th="คำค้น เช่น ชื่อร้านหรือเลขใบเสร็จ", desc_zh="关键词(卖家/单号)"),
            SlotSpec("status", required=False, source="user_text",
                     desc_th="สถานะ: confirmed/pending/failed", desc_zh="状态过滤"),
        ),
        handler="list_ocr_history",
        confirm=False,
    ),
    ToolSpec(
        name="balance",
        bucket="A",
        title_th="ดูยอดเครดิตคงเหลือ",
        desc_th="ดูยอดเงิน/เครดิตที่เหลือ และจำนวนหน้าที่ใช้เดือนนี้",
        slots=(),
        handler="get_balance",
        confirm=False,
    ),
    # ... recon_overview / list_endpoints / push_log_status / count_this_month ...
)

# 闭集:大脑只能从这里选。与 agent_registry.json 的 A 档交叉核对(防漏闸保证不漏挂)。
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
```

> **铁律**:`manifest.TOOLS` 必须与 `agent_registry.json` 一致 —— manifest 里登记的工具,其对应功能区在 registry 必为相同档;有 A 档功能区却没进 manifest → 防漏闸(端点级,M4 开)报"已分类未挂工具"。这就是"插头都在册、漏不掉"的机械保证。

---

## 4. 大脑(`brain.py`)—— JSON 动作模式

### 4.1 系统提示词(范围锁 + 工具表 + 输出契约)

```
คุณคือผู้ช่วยของ Pearnly (ระบบบัญชี/สแกนเอกสาร) ทำได้เฉพาะงานในรายการเครื่องมือด้านล่างเท่านั้น
ถ้าผู้ใช้ขอสิ่งที่อยู่นอกรายการ ให้ตอบ kind="out_of_scope" พร้อมแนะนำสิ่งที่ทำได้
ห้ามเดา/แต่งค่าพารามิเตอร์เด็ดขาด ถ้าข้อมูลไม่พอ ให้ตอบ kind="ask" เพื่อถามกลับ

เครื่องมือที่ใช้ได้:
- list_history: ดูประวัติการสแกน (พารามิเตอร์: keyword?, status?)
- balance: ดูยอดเครดิตคงเหลือ (ไม่มีพารามิเตอร์)
- ... (จาก manifest.TOOLS อัตโนมัติ) ...

ตอบเป็น JSON เท่านั้น:
{"kind":"tool|ask|out_of_scope|chat","tool":"...","args":{...},"ask_field":"...","message":"..."}
```

> 工具表**从 `manifest.TOOLS` 自动生成**(名 + `desc_th` + slot 名),不手写 → 加工具=改 manifest,提示词自动跟着变。这是"插座"的体现。

### 4.2 调网关(复用现成 · 零改)

```python
from services.ai_gateway import transport
from services.agent import manifest, contracts

def decide(user_text: str, history: list[dict], *, today: str) -> contracts.AgentAction:
    """一次网关调用,把人话翻译成动作。后端按 OCR_LLM_BACKEND 自动切(qwen/gemini)。"""
    prompt = _build_prompt(manifest.TOOLS, history, today)
    outcome = transport.text_to_json(
        prompt=prompt, text=user_text,
        tier="flash",                 # 轻量快;成本见 §8
        response_mime="application/json",
        max_tokens=512, timeout_s=18, max_retries=1,
        task="agent_decide",
    )
    return _parse_action(outcome)     # outcome.data → AgentAction;解析失败→ kind="chat" 兜底
```

> 注:Gemini 2.5/3.x 思考模型经网关已处理(`reasoning_effort:none` 等),qwen3 混合模型非流式需 `enable_thinking:false` —— 这些 provider 层已封装,brain 不操心。

---

## 5. 参数确定性闸(`slots.py`)—— 安全核心

泛化现成 `services/expense/line_l2.py:amount_grounded()`。**大脑给的每个参数,执行前必须证明它"接地"**,否则转反问。

```python
def check_slots(action: AgentAction, *, user_text: str, history: list[dict],
                ctx: AgentContext) -> SlotCheck:
    """
    逐 slot 验接地来源:
      user_text      → 值能在用户原话/近期对话找到对应(数字/关键词/状态枚举)
      anchor         → 从 line_anchored 锚定的 doc_id 取(用户"这张/上一张"指代)
      endpoint_config→ 从该用户端点配置取(account_set 等),不让模型说
      prior_result   → 从上一步工具返回里取(如刚 list 出的某条 id)
      model_freeform → 仅放行纯文本检索类(keyword);其余编造一律 reject
    必填且无法接地 → 进 missing(反问);非法枚举/编造 → 进 rejected。
    """
```

- **铁证(记忆里钉的)**:连满分模型都会在边角编造单号/金额。所以接地闸**不靠模型自觉**。
- `doc_id` 永远从锚点(`line_anchored`)或 `prior_result` 取,**绝不采信大脑凭空说的 id**。
- `account_set` / `endpoint_id` 从该用户端点配置读,大脑无权指定。
- 数字类(金额/数量)沿用 `amount_grounded` 逻辑:原文找不到对应数 → 置空 → 反问。

---

## 6. 执行器(`executor.py`)—— 以用户身份调现成 service

每个 `handler` 一个方法。**全程真实身份,复用现成闸,不 bypass。**

```python
@dataclass
class AgentContext:
    user: dict           # get_current_user_from_request 的产物(含 id/tenant_id/role/is_super_admin)
    tenant_id: Optional[str]
    workspace_client_id: Optional[Any]

class AgentToolset:
    def list_ocr_history(self, ctx: AgentContext, *, keyword=None, status=None) -> ToolResult:
        # A 档只读:直接调现成 service,带租户隔离
        rows = db.list_ocr_history(
            user_id=str(ctx.user["id"]), tenant_id=ctx.tenant_id,
            keyword=keyword, status_filter=status,
            workspace_client_id=ctx.workspace_client_id, limit=20, offset=0,
            retention_days=_retention(ctx.user),
            restrict_client_ids=db.get_visible_client_ids_for_user(ctx.user),
        )
        return ToolResult(ok=True, data=rows, receipt=_render_history(rows))

    def get_balance(self, ctx: AgentContext) -> ToolResult:
        b = db.get_billing_status_combined(str(ctx.user["id"]), ctx.tenant_id)
        return ToolResult(ok=True, data=b, receipt=_render_balance(b))

    # ---- B 档(M3 才开)样板:写操作,带确认前置 + 幂等 ----
    def push_to_erp(self, ctx: AgentContext, *, history_id, endpoint_id=None) -> ToolResult:
        history = db.get_ocr_history_detail(ctx.user["id"], history_id, tenant_id=ctx.tenant_id)
        if not history:
            return ToolResult(ok=False, error_code="history_not_found")
        endpoint = db.get_erp_endpoint(ctx.user["id"], endpoint_id) or db.get_default_erp_endpoint(ctx.user["id"])
        if not endpoint:
            return ToolResult(ok=False, error_code="no_endpoint")
        # 幂等:已成功推过 → 不双推
        prior = db.has_recent_successful_push(history_id, endpoint["id"], ctx.user["id"])
        if prior:
            return ToolResult(ok=True, error_code="skipped_dup", receipt=_render_dup(prior))
        result = erp_push.push_to_endpoint(endpoint, history)
        db.insert_push_log(...)  # 同现有路由
        return ToolResult(ok=result["success"], data=result, receipt=_render_push(result))
```

> **权限对齐**:B/写工具在执行前还要过 `require_perm` 等价检查(该用户有没有 `erp.push`/`recon.create`)。
> 做法:executor 方法内复用 `services/authz/deps._check(user, code)`,无权→`ToolResult(ok=False, error_code="forbidden")`→翻成人话引导。

---

## 7. 单轮编排 + 多轮反问(`loop.py`)

```python
def handle_turn(user_text: str, ctx: AgentContext) -> str:
    """一条消息进,一段回复出。多轮靠 line_chat_memory + pending 状态。"""
    history = line_chat_memory.recent(line_user_id=..., tenant_id=ctx.tenant_id)

    action = brain.decide(user_text, history, today=_today())

    if action.kind == "out_of_scope":
        return copy.out_of_scope(action.message)          # 引导回能做的事
    if action.kind == "chat":
        return copy.chat(action.message)                  # 闲聊/问候,走 i18n 模板

    if action.kind == "ask":
        conversation.save_pending(ctx, action)            # 记住缺什么
        return copy.ask(action.ask_field)                 # 反问

    # kind == "tool"
    spec = manifest.TOOLS_BY_NAME.get(action.tool)
    if not spec:                                          # 大脑选了不存在的工具 → 当超范围
        return copy.out_of_scope()

    chk = slots.check_slots(action, user_text=user_text, history=history, ctx=ctx)
    if not chk.ok:
        if chk.rejected:
            log.warning("slot_fabricated", extra=chk.rejected)   # 审计:模型试图编值
        conversation.save_pending(ctx, action)
        return copy.ask(chk.missing[0])                   # 缺/编 → 反问,绝不带编造值执行

    if spec.confirm and not _user_confirmed(ctx, action): # B 档:先复述确认
        conversation.save_pending(ctx, action)
        return copy.confirm(spec, chk.grounded)           # "จะ...ใช่ไหม? พิมพ์ ยืนยัน"

    result = getattr(AgentToolset(), spec.handler)(ctx, **chk.grounded)
    return result.receipt if result.ok else copy.failure(result.error_code)
```

- **多轮**:`ask`/`confirm` 时 `save_pending`;用户下一条消息先看有没有 pending,把补充值并进去再跑(沿用现有 `conversation.save_pending` 机制)。
- **确认词**:用户回"ยืนยัน/确认/ok"才执行 B 档;回别的=取消。

---

## 8. 成本(给 Zihao 的账)

- Agent 唯一新增花费 = **大脑的对话调用**(每条消息 1 次 `text_to_json`,~512 tokens 输出)。
  - qwen3.5-flash:$0.07/$0.26 每百万 token → 一条消息约 **¥0.001 量级**,可忽略。
  - 切 gemini 同量级。
- OCR/推送等**贵活本就有余额闸**(`charge_ocr` 402),Agent 走的是同一条计费路,不新增绕过。
- → 结论:**开关不是为省钱**(对话费可忽略),是【一秒关掉防抽风】+【灰度名单先行】的安全阀。

---

## 9. 换大脑 / 换行业 = 插座不动

| 要换的 | 改哪 | 插座(本文件全部)动不动 |
|---|---|---|
| 大脑 qwen3.5 ↔ gemini | `OCR_LLM_BACKEND` env + provider 配置 | **不动** |
| 加一个会计新功能 | `manifest.py` 加 1 个 ToolSpec + `executor` 加 1 方法 + registry 登记 | **不动** |
| 扩到法律行业 | 换一套 `manifest`(法律工具) + 领域提示词;executor 接法律 service | brain/slots/loop/contracts **不动** |

> 这就是"插头插座":插座(brain+slots+loop+executor 框架)建一次,插头(manifest 条目)随便插。

---

## 10. M1 验收清单(达标才算插座通电)

1. LINE 真发"ดูประวัติเดือนนี้"(查本月历史)→ 大脑选 `list_history` → 以本人身份查 → 人话回结果。✅
2. 真发"ยอดเงินเหลือเท่าไหร่"(余额多少)→ `balance` 工具 → 回真实余额。✅
3. 真发"ช่วยรีเซ็ตรหัสผ่าน"(帮我改密码,D 档)→ `out_of_scope` → 引导"请到 App"。✅
4. 构造编造场景(大脑给个不存在的 history_id)→ slots 闸拦下 → 反问,不执行。✅
5. 关掉超管 `agent_enabled` → LINE 行为逐字节回到现状(M0 集成测试证)。✅
6. 大脑后端 env 从 gemini 切 qwen3.5 → 上述 1~4 全过(证明可插拔)。✅
7. 每个新文件 ≥1 单测;CI 6 闸绿;防漏闸绿。✅
