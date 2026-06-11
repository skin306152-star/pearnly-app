# 自动做账 · 03 接口契约(前后端唯一源)

> 信封同 POS:`{ok,data}`/`{ok,error{code,message_key}}`。全接口要 `workspace_client_id`(上下文/套账切换器),缺=`workspace.required`(fail-closed)。前缀 `/api/accounting/*`。
> 写接口(审/改/过账/科目/设置)= `require_account_owner` 或会计角色。

## 1. 凭证(主屏)
- **GET /api/accounting/vouchers?period=&source_type=&status=&method=&q=** — 列表 + 汇总(本月 X 笔已自动做账 / 已过账 / 待审数)。`method` 筛自动/建议/人工(安全带①)。`data:{summary,items[]}`。
- **GET /api/accounting/vouchers/{id}** — 详情(头 + 借贷行 + human_note + source 链接)。
- **POST /api/accounting/vouchers/{id}/review** — 逐笔审定夺 `{choice|account_overrides, remember:true}` → 过账 + 写 `review_learned`。`choice`(`goods`/`service`)= 纯重分类(改科目归类),WHT 沿用业务单已算好的 `wht_amount` 不重算(见 02)。`data:{voucher}`。错误:`acct.unbalanced`(借贷不平·422)。
- **PATCH /api/accounting/vouchers/{id}** — 改科目/分录(仅 pending_review 或权限内·posted 改走调整分录)→ 重断言平。
- **POST /api/accounting/vouchers/{id}/void** — 作废(反向调整凭证·留痕)。
- **POST /api/accounting/vouchers/{id}/unpost** — 撤销重做(安全带②):原凭证置 void + 同 source 重新跑引擎(吃最新映射/记忆)。`data:{voucher}`(重判结果)。错误:`acct.period_closed`。
- **POST /api/accounting/vouchers/manual** — 手工凭证(少见·借贷自填·断言平)。

## 2. 待审队列(逐笔审)
- **GET /api/accounting/review?period=** — 待审列表(pending_review·按 source 排)。`data:{count,items[]}`。
- 复用 `/vouchers/{id}/review` 逐笔定夺。

## 3. 科目表(配置后台)
- **GET /api/accounting/accounts?type=&q=** — 科目(树·按 acct_type)。
- **POST/PATCH /api/accounting/accounts** — 加/改(预置不可删·可停)。
- **GET/PUT /api/accounting/mappings** — 科目映射(role→account·改去向)。

## 4. 做账设置
- **GET/PUT /api/accounting/settings** — auto_post(全局·默认 false=建议模式)/auto_post_rules(按 R1-R9 粒度·安全带③)/门槛/准则/存货法/本位币/启用期。

## 5. 出账本 / 报税包(月末出口)
- **GET /api/accounting/books?period=&kind=** — kind ∈ `gl`(总账)/`subsidiary`(明细账)/`trial_balance`(试算表) → 数据 + PDF。
- **GET /api/accounting/tax-reports?period=&kind=** — kind ∈ `vat`(进/销项税报告·PP30 附)/`wht`(预扣税明细+扣缴凭证)。
- **GET /api/accounting/financials?period=** — 损益表 / 资产负债表(年末)。
- **POST /api/accounting/close-period** — 月末结账(跑 R9 VAT 结转 + 锁期·借贷平校验)。`data:{closed,vat_payable}`。
- **GET /api/accounting/export-package?period=** — 打包(账本+报税材料 zip)。

## 6. 引擎(内部 · 业务模块 hook 调)
- `enqueue_posting(source_type, source_id, workspace_client_id)` — 业务 post/issue/settle 时调(非 HTTP·服务层)。幂等。

## 错误码(4 语)
`acct.unbalanced · acct.mapping_missing · acct.period_closed · acct.not_pending · acct.forbidden · workspace.required · acct.unexpected`

## 契约测试(每端点 ≥1)
信封一致 · 列表汇总 · 逐笔审过账+记忆 · 借贷不平拒绝 · 缺映射提示 · 月末结账跑 VAT 结转 · 账本/报税导出 · 套账隔离(A 拿不到 B)· 角色 403。
