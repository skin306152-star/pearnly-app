# 图文一体入口 · 设计侦察 + 方案(待 Zihao 拍板)

> 2026-07-03 · P2 backlog 第二件。目标:用户「发图 + 一句话说这张怎么处理」一步到位。
> 只读侦察已完成(零代码改动),本文=事实 + 三档方案 + 推荐。**动图片主路径,拍板后才施工。**

## 现状事实(带 file:line·2026-07-03 核实)

- LINE 平台 image message **不带文字**(只有 id/contentProvider)——「图+话一次发」到服务端
  必是**两个独立 event**(`line_webhook_routes.py:474` 逐个 `await`),图片 OCR 还是
  `asyncio.create_task` 入队(`:229`),**图与文实际并发,无先后保证**。
- **「话先图后」已通**:文本经 `plan_incoming_doc` 存 `line_pending_intents`
  (TTL 15min·`line_intent_store.py:19`),下一张图 `decide` 时 `take_intent`
  原子取走执行(`line_image_route.py:287`)。闸 `agent_image_intent` prod=all。
- **「图先话后」是缺口**:图先被默认路记账出卡后,紧跟的裸文本("这张只推ERP别记")
  不带 quotedMessageId → 强锚定不接管(`line_anchored.py:30`),落文本大脑,只有
  聊天记忆(软文本)可用。图片路**完全不写** `line_agent_anchors`(全仓唯一写点是
  `line_agent_bridge.py:305`,文本 agent 轮专用)。
- **「同发」现状=靠 race**:文本意图若先落库,飞行中的图 `take_intent` 能吃到(≈已通);
  但 OCR 若先完成,意图落晚 → **粘住之后 15 分钟内的下一张图**(错图执行,stale 意图
  booby-trap)。现状没有"这条意图是给刚才那张还是下一张"的判定。

## 三档方案

### S(最小·防呆):stale 意图防错配
`plan_incoming_doc` 落意图时,若同用户**有图片正在处理/刚处理完(≤60s)**,回执改问
「是说刚才那张,还是下一张?」——不猜。另:意图 TTL 15min 内没图,过期自动失效(已有)。
改动面:bridge sink 一处 + 一个"最近图片时间戳"查询。**不动图片主路径。**

### M(推荐):图先话后 · 回溯到「刚才那张」
1. **图片路写锚点**:图片单落账/出卡后,把 doc 句柄写进 `line_agent_anchors`
   (复用刚上线的 anchor 底座,同一闸 `agent_anchor_memory`,fail-safe 吞错,
   挂点=`line_image_ocr._push_result_card` 后一行)。
2. **plan 意图带回溯问询**:用户说"这张只推ERP别记"时,若锚点里有 ≤45min 的图片单,
   出确认卡「是指刚才那张(卖家/金额)吗?」→ 确认后按终端执行(推=走现成
   push_confirm 确认卡;"别记"=走现成撤销流对冲);不确认 → 当"下一张"存意图(现状)。
   拆分/执行全走现成确定性流,大脑零新权力。
3. 「同发」自然被 2 兜住:race 输了也能回溯问询,不再错配下一张。

### L(完整·重):图文配对窗口
图片到达先挂起 N 秒等可能的同批文本,配对后一次决策。改 webhook 事件时序 + 挂起队列,
动记账主路时延,风险大收益比 M 增量小。**不建议本轮做。**

## 推荐:M(S 含在 M 的问询逻辑里)

- 复用刚上线的 anchor 底座 + 现成 push_confirm/撤销流/intent 表,新代码面小;
- 全程 confirm-first,不猜目标(绝不猜红线);闸 `agent_anchor_memory` + `agent_image_intent`
  双 gated,关=现状逐字节不变。

## 风险闸(施工时必做)

- 图片路写锚点必须 fail-safe(锚点层任何故障不挡记账主路,同 line_anchor_store 现约定)。
- 回溯执行前**读时复核** doc 仍活(复用 resolve_card_state/_is_live,死单诚实拒)。
- "别记"=撤销已入账单,走现成对冲流(`purchase-void-reversal`),绝不物理删。
- 验收:真机 163——①同发图+话 ②图先话后 ③"别记+推" 三场景;闸关回归逐字节现状。

## 不做什么

- 不改 webhook 事件时序、不挂起图片(L 档否决);不给大脑任何直接写库/拆分权;
- 不动 OCR 热路径与计费。
