# WP3 · 对话文案(CONVERSATION-SPEC 落 i18n)

> 给执行窗口:可与 WP1/WP2 **并行**(只动 i18n + 文档)。把 `../CONVERSATION-SPEC.md` 的全部文案落成 i18n key。

## 背景
- `../CONVERSATION-SPEC.md` 是唯一事实源(六类模板 + 红线)。本包把它落地。
- 用户最在意"细到每个标点":口径必须统一,泰文自然,中/英齐全。

## 现状事实
- i18n 数据:`static/i18n-data.js`(独立 `<script>`,不进 Vite,pytest 碰不到)。
- 服务端自然语气层:`services/line_binding/line_voice.py` + `line_expense_qa.reply_pool()`(闲聊复用,不新造)。
- ★铁律(踩过坑):改 `i18n-data.js` 后**必 `node --check static/i18n-data.js`**;撇号未转义崩整个 app(记忆 [[i18n-data-js-must-node-check]])。

## 要建什么
1. 在 `static/i18n-data.js` 加全部 `agent.*` key(CONVERSATION-SPEC §1 的 ask/confirm/ok/oos/failure/chat),**TH/ZH/EN 三语齐全**。
2. `services/agent/copy_map.py`(WP1 建了结构)填值:`error_code → agent.failure.* i18n key` 映射表。
3. 槽位占位 `{xxx}` 与 executor 回执字段对齐(invoice_no/amount/endpoint/bill_no/balance/...)。
4. 闲聊类沿用现有池,只补必要的 `agent.chat.*`。

## 验收
- `node --check static/i18n-data.js` 通过;含撇号的值已改写规避。
- 三语无缺漏(写个小脚本核对 TH/ZH/EN key 集合一致)。
- bump `home.html` 两处 `?v=`(破缓存)。
- 人审:抽 5 条泰文给懂泰语的人看自然度,非机翻腔。
- 红线自查(CONVERSATION-SPEC §4):无 error_code 直吐、一次只问一个、B 档必确认、超范围带出口。

## 不要碰
- ❌ 不碰 `services/agent/*.py` 的逻辑(WP1)、不碰 LINE 链路(WP5)。
- ✅ 只动 `static/i18n-data.js` + `services/agent/copy_map.py` 的值 + 本目录文档。
