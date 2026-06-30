# 对话文案规范(CONVERSATION-SPEC)

> 你最在意的"细到每个标点":Agent 对用户说的每一句话,口径在这里统一定死,
> 各窗口不许各写各的。所有文案走现成 i18n 机制(`static/i18n-data.js` + 后端 i18n 模板),
> **泰文为主**(LINE 用户是泰国人),中/英齐全(铁律:i18n 齐全)。
>
> 落地铁律:改 `static/i18n-data.js` 后**必 `node --check static/i18n-data.js`**(撇号未转义会崩整个 app,见记忆 [[i18n-data-js-must-node-check]]),值含撇号一律改写规避。

---

## 0. 语气总则(去 AI 味 · 像 Pearnly 的人,不像机器人)

- 简洁、直接、专业;**不堆礼貌废话**、不"ผมสังเกตว่า/我注意到"、不 emoji 刷屏(收据卡可有 1 个状态图标)。
- 一律用"คุณ"称呼,不用机器人腔。失败不甩技术码,给人能懂的下一步。
- 每条回复结构:**结论先行 → 关键数 → 下一步**。不超过 3 短句(收据卡除外)。
- 不确定就反问一句,**绝不替用户假设**(尤其涉及钱/账)。

---

## 1. 六类文案模板(每类给 key + 泰/中/英 + 槽位)

i18n key 前缀统一 `agent.`。`{xxx}` 是运行时填的槽位。本文 TH/ZH/EN 是文案源;**ja 按 4 语铁律由 i18n 补全**(`check_i18n --strict` 守门,与现有 `line_correct_i18n.py` 一致)——WP3 已落 4 语,源表不再逐列列 ja。

### 1.1 反问(ask)—— 缺参数,卡住时
触发:`slots` 闸判某必填参数没接地。

| key | TH | ZH | EN |
|---|---|---|---|
| `agent.ask.which_doc` | ใบไหนคะ ลองพิมพ์เลขใบเสร็จหรือชื่อร้านให้หน่อย | 哪一张?发我单号或店名 | Which document? Send the invoice no. or shop name |
| `agent.ask.amount` | จำนวนเงินเท่าไหร่คะ | 金额多少? | What's the amount? |
| `agent.ask.endpoint` | จะส่งเข้าระบบไหนคะ (มี {endpoints}) | 推到哪个端点?(有 {endpoints}) | Which ERP endpoint? ({endpoints}) |
| `agent.ask.period` | ช่วงไหนคะ เช่น เดือนนี้ หรือ มิถุนายน | 哪个区间?如本月/六月 | Which period? e.g. this month |
| `agent.ask.keyword` | หาคำว่าอะไรคะ เช่น ชื่อร้านหรือเลขใบเสร็จ | 找什么关键词?如店名/单号 | Search for what? e.g. shop name or invoice no. |
| `agent.ask.status` | ดูสถานะไหนคะ: ยืนยันแล้ว / รอดำเนินการ / ล้มเหลว | 看哪个状态?已确认/待处理/失败 | Which status? confirmed / pending / failed |

> 注:`keyword`/`status` 是只读工具的**可选** slot,M1 正常不触发反问(loop 只问必填缺口);
> 补这两 key 是给"结果太多让用户缩小范围"等未来场景兜底,也消除 copy_map 已引用却无 i18n 的 latent 缺口。

> 规则:反问只问**当前缺的那一个**(`chk.missing[0]`),不一次抛一堆。问完记 pending,等用户补。

### 1.2 确认(confirm)—— B 档写操作执行前
触发:`spec.confirm=True`,复述将做的事 + 关键值,等用户回"ยืนยัน"。

| key | TH | ZH |
|---|---|---|
| `agent.confirm.push` | จะส่งใบ {invoice_no} ({amount} บาท) เข้า {endpoint} · พิมพ์ "ยืนยัน" เพื่อดำเนินการ | 将把 {invoice_no}({amount}฿)推进 {endpoint}·回"确认"执行 |
| `agent.confirm.record` | จะบันทึกค่าใช้จ่าย {amount} บาท ({vendor}) · พิมพ์ "ยืนยัน" | 将记一笔 {amount}฿({vendor})·回"确认" |
| `agent.confirm.recon` | จะกระทบยอดไฟล์ {filename} · พิมพ์ "ยืนยัน" | 将对账 {filename}·回"确认" |

> 确认词白名单:`ยืนยัน` / `ok` / `โอเค` / `ใช่` / `确认` → 执行;其余 → `agent.confirm.cancelled`(ยกเลิกแล้ว / 已取消)。

### 1.3 成功回执(success receipt)—— 工具干完
结构:✅ 一句结论 + 关键数 + 可选下一步。各工具一个 key。

M1 上线的 5 个 A 档只读工具,每个一个 `agent.ok.*`(前 5 行);push/recon 等 B 档留 M3。

| key | 对应工具(M1) | TH 模板 |
|---|---|---|
| `agent.ok.history` | list_history | เดือนนี้สแกนไป {count} ใบ · ยอดรวม {total} บาท{top_list} |
| `agent.ok.history_summary` | history_summary | สรุปเดือนนี้: {count} ใบ · ยอดรวม {total} บาท{by_category} |
| `agent.ok.balance` | balance | เครดิตคงเหลือ {balance} บาท · ใช้ไปเดือนนี้ {pages} หน้า |
| `agent.ok.usage_this_month` | usage_this_month | เดือนนี้ใช้ไป {pages} หน้า · {docs} เอกสาร |
| `agent.ok.notifications` | list_notifications | มีแจ้งเตือน {count} รายการ{top_list} |
| `agent.ok.push` | (M3) | ✅ ส่งเข้า {endpoint} แล้ว · เลขเอกสาร {bill_no} |
| `agent.ok.push_dup` | (M3) | ใบนี้ส่งเข้า {endpoint} ไปแล้ว (เลข {bill_no}) ไม่ส่งซ้ำ |
| `agent.ok.recon` | (M3) | กระทบยอดเสร็จ · ตรงกัน {matched} รายการ ไม่ตรง {unmatched} |

### 1.4 超范围引导(out_of_scope)—— C/D 档或非业务
触发:`kind=out_of_scope`。**不只是拒绝,要指路。**

| key | TH | ZH |
|---|---|---|
| `agent.oos.app_only` | เรื่องนี้ทำในแอปจะสะดวกกว่า เปิดที่ {app_link} ได้เลย | 这个在 App 里做更方便:{app_link} |
| `agent.oos.security` | เรื่องบัญชี/รหัสผ่าน ต้องทำในแอปเพื่อความปลอดภัย | 账号/密码相关请到 App,保安全 |
| `agent.oos.capability` | ช่วยได้เรื่อง: ดูประวัติสแกน, เช็คยอดเครดิต, ส่งเข้า ERP, กระทบยอด · ลองพิมพ์มาได้เลยค่ะ | 我能帮:查识别历史、查余额、推 ERP、对账·说一句试试 |

> 超范围必带"我能做什么"的出口,别让用户撞墙。

### 1.5 失败(failure)—— 工具报错,翻成人话
**禁止把 error_code 原样吐给用户**(记忆铁律:no_revenue_account 这种用户看不懂)。`error_code → 人话` 映射:

| error_code | TH | ZH |
|---|---|---|
| `insufficient_balance` | เครดิตไม่พอ (เหลือ {balance} บาท) · เติมเงินที่ {topup_link} | 余额不足(剩 {balance}฿)·充值:{topup_link} |
| `no_endpoint` | ยังไม่ได้ตั้งค่าปลายทาง ERP · ตั้งในแอปก่อนนะ | 还没配 ERP 端点·先去 App 配 |
| `forbidden` | สิทธิ์ของคุณยังเข้าถึงเมนูนี้ไม่ได้ · ติดต่อแอดมินของบริษัท | 你暂无此权限·找公司管理员 |
| `history_not_found` | หาเอกสารใบนั้นไม่เจอ · ลองส่งเลขใบเสร็จอีกครั้ง | 找不到那张·重发单号 |
| `no_tenant` | ยังไม่ได้ผูกบัญชีบริษัท · เปิดในแอปก่อนนะ | 还没绑定公司账套·先到 App 开 |
| `query_failed` | ดึงข้อมูลไม่สำเร็จ ลองใหม่อีกครั้งนะคะ | 查询失败,稍后再试 |
| `not_available_yet` | ฟังก์ชันนี้ยังทำผ่านแชทไม่ได้ ทำในแอปได้เลย {app_link} | 这个还不能在对话里做·到 App 操作:{app_link} |
| `unknown` | ระบบมีปัญหาชั่วคราว ลองใหม่อีกครั้งนะคะ | 系统临时问题,稍后再试 |
| `_default` | ระบบมีปัญหาชั่วคราว ลองใหม่อีกครั้งนะคะ | 系统临时问题,稍后再试 |

> **★ key 命名锁定(裁判定论 · 两窗口对齐唯一源)**:失败类前缀一律 `agent.failure.*`(**不是 `agent.err.*`**)。
> `copy_map.py`(WP1 持有)的 `error_code → i18n key` 必须用上表的 `agent.failure.<code>`;`i18n-data.js`(WP3 持有)按上表登记。两边都抄本表,不互改对方文件。
> **人设锁定**:全站语气一律女性 `ค่ะ/คะ`,§1.4 `agent.oos.capability` 原 "ผม" 已废,改 `ดิฉัน`/省略主语,与全站及 ask 模板一致。

### 1.6 闲聊/问候(chat)
复用现成 `services/line_binding/line_voice.py` + `line_expense_qa.reply_pool()` 的自然语气层,不新造。新增仅 `agent.chat.greeting` 等少量,沿用现有池。

---

## 2. 多轮反问的对话流(范例 · 泰文)

```
用户: ส่งใบเมื่อกี้เข้า ERP ให้หน่อย              (把刚才那张推进 ERP)
Agent: [slots: history_id 从 anchor 取到 ✓; endpoint 缺]
       จะส่งเข้าระบบไหนคะ (มี MR.ERP, Express)        ← agent.ask.endpoint
用户: MR.ERP
Agent: [pending 补全; spec.confirm=True]
       จะส่งใบ INV-001 (1,070 บาท) เข้า MR.ERP · พิมพ์ "ยืนยัน"   ← agent.confirm.push
用户: ยืนยัน
Agent: ✅ ส่งเข้า MR.ERP แล้ว · เลขเอกสาร B123456              ← agent.ok.push
```

> 注意:`history_id` 从锚点接地(用户"刚才那张"= `line_anchored`),**大脑不编 id**;`endpoint` 缺 → 反问;写前 → 确认。三道都在 `loop.py`。

---

## 3. 文案落地清单(WP3 窗口照此做)

1. 在 `static/i18n-data.js` 加 `agent.*` 全部 key 的 TH/ZH/EN 三语(本文件 §1 是源)。
2. 后端若有服务端模板(如 `line_voice`),对应补 key。
3. **改完必 `node --check static/i18n-data.js`**;含撇号的值改写规避(don't→do not)。
4. bump `home.html` 两处 `?v=`(破缓存,铁律)。
5. 每条文案**人审泰文自然度**(别机翻腔);中/英齐全。
6. error_code→人话映射做成一张表 `services/agent/copy_map.py`,executor 的 `error_code` 经它翻译,不散落。

---

## 4. 红线(违反即返工)

- ❌ 把 error_code / 技术词吐给用户。 ✅ 一律过 §1.5 映射。
- ❌ 一次反问抛多个问题。 ✅ 一次只问一个缺口。
- ❌ B 档不确认直接执行。 ✅ 必复述+等"ยืนยัน"。
- ❌ 超范围只说"做不了"。 ✅ 必带"我能做什么"出口。
- ❌ 大脑凭空说的 id/金额直接用。 ✅ 必过 slots 接地,缺/编→反问。
- ❌ emoji 满天 / 礼貌废话 / 机器人腔。 ✅ 结论先行,3 短句内。
