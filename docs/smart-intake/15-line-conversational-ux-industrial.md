# 15 · LINE 对话体验产业级重做(置信驱动入账 + 数据卡 + 引用/转圈 + 智能回复)

> 2026-06-15 Zihao 拍板「123 全做完」。定位术语:Pearnly = SMB **Autonomous Accounting**,
> 以**对话式智能录入**为入口,**STP(高置信直通入账)+ HITL(低置信人工复核)**。
> 本文是施工正本;主路径(OCR/LINE/计费/做账)改动,先文档后码。
>
> **⚠️ 2026-06-16 更新:「待归类(inbox)」整模块已下线。** 识别完一律建草稿(ฉบับร่าง)落采购
> 列表,用户在列表改方向/补金额/删,不再单独兜待归类桶。下文 §1 的 inbox 档已并入 confirm
> (糊图/฿0/方向不明 → 建草稿请确认),其余三态(post/confirm/dup)不变。

## 0. 一句话目标

拍票/发一句话 → **能自动入账分类的直接入正式账**(可一键撤销),拿不准的也建成草稿落列表让用户定;
回复用**引用 + 转圈 + 数据卡**,闲聊不复读。让用户「看到的、知道的能指示;没触发的、多状态的都被照顾到」。

## 1. 置信驱动入账(核心)

录入后按置信分路(待归类已下线·糊图/฿0/方向不明改建草稿):

| 档 | 判据(全满足) | 动作 | 卡片状态 | 按钮 |
|---|---|---|---|---|
| **post 直接入账** | OCR 高置信 + 金额>0 + 卖家有 + (税票则发票号有) + 方向=purchase/expense + **非重复** | `create_doc(draft)`→`post_doc()`(正式 posted + 做账 enqueue) | ✅ 已入账(绿) | ↩️撤销 · ✏️复核 |
| **confirm 请确认** | 其余(低置信字段 / 无分类命中 / 简式·缺号 / 金额≤0 糊图 / 方向不明) | `create_doc(status=draft)` 落列表 | ⏳ 请确认(琥珀) | ✅确认入账 · ✏️改 |
| **dup 疑似重复** | dedupe_key 命中已有单 | 不自动入账,落 confirm | ⚠️ 可能重复(红) | ✅仍要记 · ✏️查看 |
| ~~inbox 待归类~~ | ~~建不出草稿 / 金额≤0(糊图) / 方向不明~~ | **已下线** → 并入 confirm | — | — |

判级模块:`services/expense/confidence.py`(纯函数 `grade()`,图/文共用,可单测)。
做账安全带(铁律):① post 前强制 dedupe ② 撤销=`void_doc`(反过账+反库存,不删数据) ③ 撤销/改动回喂 `expense_learned`(越用越准)。

## 2. 三个 LINE 原生能力(回答「看起来要智能」)

| 能力 | LINE API | 用途 | 落点 |
|---|---|---|---|
| **转圈** | `POST /v2/bot/chat/loading/start`(≤60s,仅 1:1) | 收图/调 L2 立即转圈,识别完出结果 | `line_client.start_loading()` |
| **引用回复** | 消息事件带 `message.quoteToken`;回复消息对象塞 `quoteToken` | 结果引用用户那张照片/那句话,连发多张不乱 | webhook 抓 token → 透传到回执文本 |
| **数据卡** | Flex Message | 识别结果卡(字段表+存疑琥珀标+状态头+动作钮) | `line_card.result_card()` |

> quoteToken 只支持 text/sticker,**Flex 不能被引用** → 故每条结果 = 【引用文本回执】+【Flex 数据卡】两条(与 Paypers 一致)。

## 3. 数据卡(`services/line_binding/line_card.py`)

Flex bubble:
- **头**:状态条(已入账绿 / 请确认琥珀 / 需补全灰 / 重复红)+ 金额大字 `฿{amount}`
- **体**:单据类型 / 支出类型(商品·服务)/ 日期 / 分类 / 子分类 / 卖家 / 发票号 / 明细 —— 逐字段;低置信字段值标琥珀 `#D97706` + `(请核对)`
- **脚**:按状态出按钮(见 §1 表)。postback 钮 = 撤销/确认;uri 钮 = 深链网页复核(`pearnly.com/home` 进项)
- 4 语标签内联(LINE 域,不进 home.js i18n)

## 4. postback 重新引入(最小 · 仅卡片动作)

`services/line_binding/line_postback.py`:`ACTION_UNDO` / `ACTION_CONFIRM`,`parse/undo_data/confirm_data`。
webhook 收 postback → `line_card_actions.handle()`:
- undo:`void_doc(doc_id)` → 回执「已撤销」(卡更新为灰)
- confirm:草稿 `post_doc(doc_id)` → 回执「已入账」(卡更新为绿)

> 与上轮删的「去采购还是费用」路由问询卡**不同**:那是问路(已废),这是卡上动作钮(撤销/确认)。

## 5. 智能回复(`services/expense/replies.py` · 治复读)

意图(复用 `line_l2.intent_of`:expense/query/question/other + 新增 greeting/thanks):
- greeting(你好/สวัสดี/hi)→ 问候 + 一句能力提示(**从池里轮选,不复读**)
- thanks(谢谢/ขอบคุณ)→ 不客气(轮选)
- query(本月花多少)→ 真数 + 迷你分类 Top3
- question → 知识中心带出处 / 诚实没找到
- other 跑题 → 礼貌带回 + Quick Reply 引导(轮选,不复读)

轮选:按 `hash(text)%N` 选池中一条(确定但不复读;同句换池靠不同 N)。

## 6. 全状态矩阵(都要有得体回复)

未绑定(图/文)/ 识别中(转圈)/ post / confirm / dup / 连发多张(各自引用)/ 缺金额追问 /
查账 / 知识问答 / 取 Drive·Sheet / 问候 / 谢谢 / 跑题 / 不支持文件 / 额度尽·无Key·欠费 / 系统异常(不静默吞)。

## 7. 模块清单与铁律

| 文件 | 动作 | 测试 |
|---|---|---|
| services/expense/confidence.py | 新 置信分级 | confidence_test |
| services/line_binding/line_card.py | 新 Flex 数据卡 | line_card_test |
| services/line_binding/line_postback.py | 新(最小) 撤销/确认 | line_postback_test |
| services/line_binding/line_card_actions.py | 新 postback 落地(void/post) | line_card_actions_test |
| services/expense/replies.py | 新 智能回复轮选 | replies_test |
| services/line_binding/line_client.py | 加 start_loading | (boot) |
| services/ocr/line_image_ocr.py | 改 图路接置信分流+卡+引用 | — |
| services/line_binding/line_expense.py | 改 文路接置信分流+卡+引用 | 既有 |
| routes/line_webhook_routes.py | 改 抓 quoteToken+转圈+postback 分发 | — |
| services/line_binding/line_i18n.py | 加 卡/钮/智能回复/撤销确认/dup 键×4语 | check_i18n |

铁律:单文件 <500 · 每新文件 ≥1 测 · 金额 Decimal · i18n 齐 · 参数化 SQL · 多租户隔离 · 去 AI 味。
真机渲染(转圈/引用/Flex)= Zihao 手机验收(我无真 channel);我交单测 + boot + 直推。
