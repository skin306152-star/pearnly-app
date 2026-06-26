# 自动报税 · 03 接口契约(前后端唯一源)

> 信封同 POS:`{ok,data}`/`{ok,error{code,message_key}}`。全接口要 `workspace_client_id`,缺=`workspace.required`。前缀 `/api/tax/*`。写/提交 = `require_account_owner` 或会计。

## 1. 报税中心(主屏)
- **GET /api/tax/filings?period=** — 本期要报的税清单 + 汇总(本月要交税合计/最近截止)。`data:{summary,items[]}`(每项:kind/status/net_amount/due_date)。

## 2. 税表复核
- **GET /api/tax/filings/{id}** — 详情:PP30=output/input/net + 异常 + 可追溯链接;PND=逐笔 filing_lines + 扣缴凭证态 + 异常。
- **POST /api/tax/filings/{id}/recompute** — 重算本期(从做账/进项重新汇总·覆盖 prepared)。
- **POST /api/tax/filings/{id}/file** — 提交:`{method:etax|manual}`。etax→连 RD e-filing 回执;manual→返导出文件 + 置 filed。**二次确认 + 报前体检过才放行**。错误:`tax.has_anomaly`(硬异常未解)·`tax.period_not_closed`(未结账)·`tax.already_filed`。
- **POST /api/tax/filings/{id}/mark-filed** — 手报后标记已报(填回执号)。
- **GET /api/tax/filings/{id}/export?fmt=** — 导出 RD 官方格式(PP30/PND)。

## 3. 扣缴凭证(PND)
- **POST /api/tax/wht-certs/{line_id}/issue** — (复用进项已生成)关联/补开扣缴凭证。
- **POST /api/tax/wht-certs/send** — 一键发收款方(邮件/LINE)。

## 4. 报税设置
- **GET/PUT /api/tax/settings** — VAT登记/总分公司/e-Tax接入态/提醒天数/0额也报。
- **POST /api/tax/efiling/connect** — 接入 RD e-filing(凭据·不存明文·引用)。

## 5. 引擎(内部)
- `generate_filings(period, workspace_client_id)` — 做账 close-period 后调,生成本期 prepared 税表。幂等(UNIQUE period,kind)。

## 错误码(4 语)
`tax.has_anomaly · tax.period_not_closed · tax.missing_tax_id · tax.already_filed · tax.efiling_failed · tax.forbidden · workspace.required · tax.unexpected`

## 契约测试
清单+汇总 · PP30/PND 复核数 · 重算 · 提交(etax回执/导出)+体检拦 · 已报不可改 · 扣缴凭证 · 套账隔离 · 角色 403。
