# 统一智能入口 + 待归类 + 识别记录门控(F12-14)· 一页施工方案

> 配 `00-unify-and-followups.md`。架构级三动作。**底线(铁律#26):事务所「上传识别 → 识别记录」路径一字不破坏。**
> 进窗口实测发现:`/api/purchase/intake` 分流已建好(judge_direction 判方向 + 落 intake_items inbox),
> 但 ① intake_items **没有 list/resolve 端点 + 没有前端入口**(F13 缺)② 识别记录(上传识别/单据记录)对所有业态显示(F14 缺)。

## 现状(已建,不动)
- 后端分流:`services/purchase/intake.py` `judge_direction`(买方=我→purchase/expense,卖方=我→sales,非票→inbox,低置信→inbox)+ `resolve_image_intake`(建草稿/落 inbox)+ `route_line_image`(LINE 图,firm/未开 expense → 不动识别中心)。
- 后端入口:`routes/purchase_intake_routes.py` `POST /api/purchase/intake`(图/文字)+ `POST /api/purchase/expense`。
- 表:`intake_items`(0033)= tenant_id / workspace_client_id / source / raw / image_url / ai_guess / status('pending') / resolved_doc_id。**字段够用,无需迁移。**
- 前端 onCapture(`purchase-list.ts`):draft→开录入屏;draft=null→toast「手填」+开空表单(待改,见 F12)。

## 识别记录 = 什么(F14 门控对象)
- 「上传识别」`data-route="ocr"`(`page-ocr` · `ocr-recognize.ts`)+「单据记录」`data-route="history"`(`page-history.ts`)= 事务所批量识别客户票的老栈,在 `app-shell-html.ts` 销项管理组内,仅 `data-module="sales"` 门控(默认开)。
- 上传走 `/api/ocr/recognize` → `services/ocr/recognize/persist.py` 落识别历史。**商户在这上传吃饭票 → 进识别历史,没进费用 = 本次根因。**

---

## F14 · 识别记录降级事务所专用(门控)
**门控位**:`src/home/module-nav.ts` `apply()`(已有 business_type 形参,来自 `/api/me/modules`)。
**规则(★保命)**:`business_type ∈ {retail, pharmacy, restaurant, service, b2b}`(显式商户业态)→ 隐藏 `[data-route="ocr"]` + `[data-route="history"]`。
**`null` / `'firm'` → 保持显示**(legacy 事务所从未 onboard,bt=null;与后端 `route_line_image` 的 `bt in (None,"firm")` 同源)。**绝不按"非 firm 就隐",会误杀 legacy firm。**
**默认落地页**:`routeTo` 非法路由回落 `'ocr'`。商户隐藏 ocr 后,改回落 `'dashboard'`(首页);仅当 business_type 为 firm/null 时回落 ocr。改 `core-boot.ts` routeTo 兜底 + 启动初始路由。
- 文件:`module-nav.ts`(加 MERCHANT_TYPES 隐藏逻辑)、`core-boot.ts`(回落路由按业态)。无后端改。

## F13 · 待归类收件箱(★长尾安全网 · 做 UI 入口)
**后端**(`routes/purchase_intake_routes.py` + `services/purchase/intake.py`,无迁移):
- `GET /api/purchase/inbox` → `{items:[{id, source, raw, image_url, ai_guess, created_at}]}`(status='pending' · 套账过滤 · 成员可读)。
- `POST /api/purchase/inbox/{id}/resolve` body `{action}`:
  - `purchase` / `expense` → 用 raw(fields)建**草稿** purchase_doc(复用 `build_draft_from_invoice` / `expense_line`)→ intake_item status='resolved' + resolved_doc_id → 返 `{doc_id}` → 前端开录入屏确认。
  - `dismiss`(不是票)→ status='dismissed'。
  - `sales` / `recon` → status='resolved'(移出收件箱;前端提示去对应模块处理)。
  - 隔离:每句 WHERE tenant_id + workspace_client_id;owner 不要求(成员可归类自己套账)。
**前端**(新 `src/home/purchase-inbox.ts` <500):
- 列表:每条 = 票图缩略 + AI 猜测(kind/置信)+ 关键字段(供应商/金额/日期,缺则「未识别」)+ 一排归类按钮[记进项][记费用][这是销项][银行单·去对账][不是票·忽略]。
- 四态:loading / 空(「暂无待归类」)/ 错误 / 离线。每动作三态反馈(进行中禁连点 + 成功 toast + 失败具体提示)。
- 归类成功 → 进项/费用 跳录入屏(预填)确认入账;其余 toast + 移除该卡。
- 导航:进项管理组加子项「待归类」`data-route="purchase-inbox"` `data-module="expense"`,带未处理计数角标(读 inbox 长度)。`core-boot` 注册 route + loader;`home.html` 加 `page-purchase-inbox`。

## F12 · 统一智能入口(收口 onCapture 分流)
不新建第二个口:**商户隐藏识别记录(F14)后,采购首屏「拍进项票 / 手动记一笔(F3a)/ 待归类(F13)」即统一入口。** 收口 `purchase-list.ts` onCapture 按 route 诚实分流:
- `purchase`/`expense` + draft → 开录入屏(现状)。
- `inbox`(draft=null,含低置信)→ toast「拿不准已放入待归类」+ 跳 `purchase-inbox`(替代现在的「手填空表单」)。
- `sales` → toast「这像你开出的销项票,去销项管理开票」。
- `recon` → toast「这像银行单,去对账中心」。
- i18n 4 语新键。

## 学习(下次同类自动)— 本期范围说明
施工单提「系统记住」。本期**先把安全网做实**(inbox + 一点归类,绝不静默丢),**学习(供应商→科目/方向记忆)留 follow-up**,不做半成品。inbox resolve 已天然积累 resolved 数据,后续可据此自动。

## 验收(架构)
- 事务所(firm/legacy null):识别记录/上传识别照常显示、`/api/ocr/recognize` 闭环不变 = **回归绿**。
- 商户(retail 等):无识别记录入口;拍票/手动/待归类三入口齐;吃饭票 → 费用或待归类,**不进识别历史**。
- 跨套账:inbox list/resolve 带 workspace_client_id,A/B 隔离 E2E。
- 文件清单:后端 `purchase_intake_routes.py`/`intake.py`;前端 `purchase-inbox.ts`(新)/`purchase-list.ts`/`module-nav.ts`/`core-boot.ts`/`app-shell-html.ts`/`home.html`/`i18n-data.js`/`static/dist`(build)。**无迁移。**
