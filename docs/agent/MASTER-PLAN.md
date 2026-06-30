# Pearnly 对话 Agent · 总纲(MASTER-PLAN)

> 一句话:在通用大模型外面套一层"只懂 Pearnly、只能用 Pearnly 功能、卡住会按真实账况反问"的壳,
> 让用户在 LINE / 网页用大白话把 Pearnly 能做的事说出来就办成。
>
> 本文是项目全景 + 里程碑 + 工作包拆分 + 整合顺序。技术细节见 `M1-SOCKET-DESIGN.md`,
> 对话文案见 `CONVERSATION-SPEC.md`,每个窗口的施工任务书见 `work-packages/`。
>
> 现状事实全部来自 2026-06-30 四路只读探查,带真实文件/行号,图纸对得上代码。

---

## 0. 这不是重活 —— 它是"插座 + 插头",不是焊 512 条线

产品有 **91 功能区 / 512 个 API 入口**(见 `agent_registry.json` + 防漏闸)。
错误做法是给每个功能写一套对接,永远做不完。正确做法 = 你那 512 个接口**本来长得一样**
(地址 + JSON 进 / JSON 出),这个统一性就是**插座**;每个功能做成一行**插头**清单。

- **插座建一次**:万能工具执行器 + 大脑 + 参数闸 + 安全壳。建好不动。
- **插头逐个插**:每个能力 = manifest 里一行(干嘛、要哪些参数、哪个安全档)。
- **加新功能** = 加一行插头。**加新行业**(如法律)= 换一套插头清单 + 领域提示词,插座/大脑/参数闸全不动。

> 重活只在 **M1 建插座**这一次。之后全是插插头,增量的。

---

## 1. 架构三层(模型不做账 · 你的代码做账)

```
①  对话窗            ②  大脑(可插拔)            ③  手(现有代码)
LINE webhook   ──►   model via ai_gateway   ──►   services/agent/executor.py
网页输入框           JSON 动作模式               ──►  现有 service 函数(原样)
(只收发文字)         "推这张票" → {tool,args}      带鉴权/租户/计费/幂等
```

- **大脑不改业务**:它只把人话翻译成"调哪个工具、带什么参数"。真干活的是现有代码。
- **大脑可插拔**:qwen3.5(自托管/便宜)↔ gemini(最准),改一个 env(`OCR_LLM_BACKEND`)就换,业务零感知。
- **范围物理锁死**:大脑只能从"工具清单"里选,清单里没有的它**没有手去做**(不是靠提示词劝,是没有那个方法)。

### 现状接得上(探查实证)
- 网关 `services/ai_gateway/transport.py` 的 `text_to_json()` 已能"文本进→JSON 出",**按 `OCR_LLM_BACKEND` 自动切后端** → 大脑直接复用,网关一行不改。
- LINE 大脑 `services/expense/line_agent.py:understand()` 已是"一次调用吐 JSON"的范式 + `may_write()` 写闸 + `amount_grounded()` 参数接地 + `line_chat_memory` 多轮记忆 → **新大脑顺着这个骨架长,不另起炉灶**。
- 路由是薄壳,业务在 service 层 → **Agent 工具挂 service 层**(`services/agent/executor.py`),以用户身份调,复用 `get_cursor_rls` / `require_perm` / `charge_ocr` / `has_recent_successful_push`,**不绕任何安全闸**。

### ★ 两条不可破的能力铁律(Zihao 拍板 2026-07-01 · 每个窗口都守)

1. **能力只增不减(additive-only · 绝不因接 Agent 让用户失去任何已有功能)。**
   现有 LINE 能力(记账 / 撤销 / 改错 / 查汇总 / 查明细 / 闲聊)一律保留。新大脑**只处理它当前有工具的意图**(M1 = 5 个只读),**凡是它还没有工具的意图,必须自动落回现有可用旧路径**(`understand()`+`_dispatch_agent()`),由旧逻辑照常完成 —— **不许回"去 App 做"把已有能力降级**。只有**新旧 LINE 都不做的事**(改密码 / POS 等 C/D 档)才引导去 App。
   - 落地:新 loop 对"非自己工具集"的意图 **返回 defer(`None`)→ 跌落旧路**,而不是 `not_available_yet`。
   - 终态:M3+ 把撤销/改错/记账也做成工具后,Agent 成为旧能力的**超集**;**任何一个里程碑,能力都只多不少**。

2. **前后端同源 · 显示与实际不许矛盾(single-source · honest surface)。**
   对话(LINE)和按钮(App / 网页)是**同一套后端 service 的两扇门**,调的是同一批函数 → 能力天然一致,不存在"两套各说各话"。文案/状态用 **contract 测试**(前端 `i18n-data.js` 的 `agent.*` key 必须 ⊆ Python 端 `agent_i18n`,对不上=CI 红)+ **状态诚实闸**(失败显失败,绝不把没成功渲染成成功,绝不吐裸 key)双重盯死。

---

## 2. 四个安全档(决定一个功能进不进 Agent、怎么进)

来自 `AGENT-CAPABILITY-INVENTORY.md` 的 A/B/C/D,防漏闸 `agent_capability_audit.py` 已机械核对全 512 入口。

| 档 | 含义 | Agent 怎么对待 | 例 |
|---|---|---|---|
| **A 进·只读** | 查询、列表、统计 | 直接执行,无需确认 | 查识别历史、查余额、查对账概览 |
| **B 进·要确认** | 写操作、花钱、改账 | **先复述+让用户确认**,再执行;带幂等 | 推 ERP、跑对账、记一笔账 |
| **C 不进·App专属** | POS 收银台、复杂表单向导 | 大脑不挂;引导"请到 App 操作" | POS 点单、采购向导 |
| **D 不进·系统/安全** | 登录、鉴权、超管、计费后台 | 永不挂工具 | 改密码、超管删用户 |

> M1 只上 **A 档**(只读,最安全),把闭环跑通;B 档进 M3;C/D 永不进对话。

---

## 3. 里程碑(解封后施工 · 每步有验收闸)

| 里程碑 | 做什么 | 验收(达标才算完) | 依赖 |
|---|---|---|---|
| **M0 钥匙闸** | `platform_settings` 表 + 超管开关 UI + Agent 入口闸(默认关) | 关=走现状用户无感;开=进 Agent;灰度 allowlist 生效;集成测试证明"关掉=旧行为逐字节不变" | 无 |
| **M1 插座** | `services/agent/`:manifest + brain + slots + executor;**5~8 个 A 档只读工具** 上 LINE | 真机:LINE 说"查我这个月识别了几张票"→大脑选对工具→以本人身份查→人话回结果;说"帮我改密码"→引导超范围;参数编造→反问不执行 | M0 |
| **M2 换脑** | LINE 的窄大脑 `understand()` 升级为工具大脑;旧记账意图作为工具之一 | 原有记账/查询/撤销/编辑全回归通过(业务零改);大脑后端 env 可在 qwen3.5↔gemini 间切 | M1 |
| **M3 写工具** | B 档逐个插:推 ERP、跑对账、记账,带强制确认 + 幂等 + 计费闸 | 真机:LINE 说"把刚识别那张推进 ERP"→复述确认→执行→幂等(再说一次不双推);余额不足→402 友好提示 | M2 |
| **M4 铺满** | manifest 扩到覆盖 A/B 全部能力;防漏闸翻 FAIL 模式 | `agent_capability_audit.py` 端点级核对全绿;LINE 能办 Pearnly 大部分日常 | M3 |
| **M5 上网页** | 网页输入框接同一套 Agent(LINE 验稳后) | 网页输入框等价于 LINE 体验,共用 executor/manifest/slots | M3 |

> 顺序铁律:**先 LINE 后网页**(LINE 已有现成骨架,省一半);**先只读后写**(A 验稳再放 B);**先单工具后多工具**。

---

## 4. 工作包拆分(可多窗口并行 · 边界不打架)

每个工作包 = 一份自包含任务书(`work-packages/WP*.md`),含背景、现状事实、要做什么、验收、**不要碰什么**。

```
WP1  插座核心(services/agent/ 全套)        ← 最重 · 单窗口独做 · 别人等它
WP2  钥匙闸(platform_settings + 超管开关)   ← 可与 WP1 并行(不碰同文件)
WP3  对话文案(CONVERSATION-SPEC 落 i18n)    ← 可与 WP1 并行(只动 i18n + 文档)
WP4  A 档只读工具(5~8 个 executor 方法)     ← 依赖 WP1 的插座骨架先落地
WP5  接进 LINE(understand 升级 + 入口闸)    ← 依赖 WP1+WP2+WP4,最后整合
```

### 并行/串行依赖图
```
        WP1 插座核心 ─────────────┐
        WP2 钥匙闸  ──────────────┤
        WP3 对话文案 ─────────────┤
                                  ▼
                         WP4 只读工具(需 WP1 骨架)
                                  ▼
                         WP5 接进 LINE(整合 WP1~WP4)→ 真机验收 → 灰度开关放量
```

- **可同时开 3 窗口**:WP1 / WP2 / WP3 互不碰文件,并行起跑。
- **WP4 等 WP1** 的 manifest/executor 骨架定下接口再插工具(否则接口对不上要返工)。
- **WP5 是整合窗口**,把前面拼起来,跑真机端到端,最后由你在超管后台开灰度。

### 防打架边界(每个 WP 任务书会重申)
- WP1 只在 `services/agent/` 新建文件,不改现有 service。
- WP2 只在 `services/platform_settings/` + `routes/admin_settings_routes.py`(新) + `static/admin/*`。
- WP3 只动 `static/i18n-data.js` + `CONVERSATION-SPEC.md`(改 i18n 必 `node --check`,见铁律)。
- WP4 只在 `services/agent/executor.py` 加方法 + `agent_registry`/manifest 登记。
- WP5 改 `services/expense/line_agent.py` + `routes/line_webhook_routes.py` 入口闸,**这是唯一碰现有 LINE 链路的窗口**,放最后单独做。

---

## 5. 整合 + 上线流程

1. WP1~WP4 各自分支完成 + 自带测试绿(每个新文件 ≥1 测试,铁律)。
2. WP5 在整合分支把四件拼起,跑**真机端到端**(LINE 真发消息,不是 grep 类名)。
3. 防漏闸 `agent_capability_audit.py` 绿;CI 6 闸绿。
4. 超管后台 `agent_enabled` **默认关**上线 → 先只把 skin / 指定账号加进 allowlist 灰度。
5. 灰度跑稳 → 放量;出问题一秒关开关回退现状(用户无感)。

---

## 6. 风险与铁律(施工窗口必读)

- **整顿封锁期已由 Zihao 解封**做此项目(2026-06-30),但仍守 6 道闸 + 单文件 <500 + 去 AI 味 + Conventional Commits。
- **push 即上线**:改 src/*.js 必 `npm run build` + 提交 `static/dist`;改 i18n-data.js 必 `node --check`;未真机验收不 push master。
- **参数绝不让模型编**:所有 slot 必过确定性闸(`slots.py`,泛化 `amount_grounded`),编造的值一律转反问,不流到写函数。这是 `may_write` 同款哲学,安全核心。
- **工具以用户身份执行**:executor 用真实 `user_id/tenant_id` 走 `get_cursor_rls`,**绝不 bypass RLS、绝不绕计费**。Agent 只能做该用户本就有权做的事。
- **钥匙先关后开**:任何阶段 prod 默认关,灰度名单先行,验稳才放量。

---

## 7. 一句话给执行窗口

> 你不是在发明 AI。你在给一个现成大脑**装上 Pearnly 的手**(闭集工具)、**圈进 Pearnly 的脾气**(领域提示词)、**焊死安全闸**(参数接地 + 鉴权 + 计费 + 幂等)。
> 大脑保持通用、可随时换;Pearnly 味全在外壳。照 `M1-SOCKET-DESIGN.md` 的接口契约做,不偏离,不返工。
