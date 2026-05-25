# ERROR_CODES_AND_STATES.md · 错误码与状态机

> 什么能显示"完成",什么必须显示失败/需处理,什么必须弹核对。**显示错=信任崩**。
> 最后更新:2026-05-26。

## 1. 推送状态唯一来源:`erp_push_logs`

**所有推送状态只从 `erp_push_logs` 取**(铁律 #12)· 不许第二套源(`ocr_history.last_push_status` 等只能从它派生)。前端只读 `body.ok`,不靠 HTTP 状态码判业务结果(200 + ok:false 是有效失败)。

`status` 白名单(CHECK):`success / failed / skipped_dup / pending / retrying`(主路径实际只产生前三个)。

retry 字段:`retry_count / max_retries / next_retry_at`(技术错才排重试)。

## 2. 批次中心展示态(从上面**派生** · 不新增 status)

由 `services/erp/batch_view.classify_push_log(row)` 派生:

| 展示态 | 派生条件 | 能否显示"完成" |
|---|---|---|
| ✅ success(已推送) | `status='success'` | ✅ 可 |
| ⏭ skipped(已推过·去重) | `status='skipped_dup'` | ✅ 可(标"已存在") |
| 🔄 retrying(重试中) | `status='failed'` + `next_retry_at` 有 + `retry_count<max` | ❌ 不可 |
| ⚠️ needs_action(需人工) | `status='failed'` + `is_user_data_error(error_msg)` | ❌ 不可 |
| ❌ failed(终态失败) | `status='failed'` 其余 | ❌ 不可 |

## 3. ⛔ 绝不能显示"完成/成功"的状态

- `status='failed'`(任何子类:retrying / needs_action / 技术终态)。
- 任何 `ERR_*` 错误码(见 §4)。
- 推送返码 '1'/'2' 但未经报表/bill_no 二次确认(铁律 #9)。
- **对账侧**:`rows=0`(整侧 0 行)、`needs_mapping`(列映射缺失)、`failed` —— 必须失败分流,**不许吞成"完成"**(踩过:GL/VAT 任一侧 0 收入行被吞成"完成")。
- OCR:低置信度 / 金额不平(净额+VAT≠总额)/ 税号非 13 位 —— 必须 ⚠️ 标"识别不完整·请核对",**不许瞎填一个错值塞进去**(P0-VAT 哲学:宁可标不完整,不可识别错)。

## 4. MR.ERP 错误码分类(决定是否重试 / 是否进异常)

### 用户数据错(`USER_DATA_ERROR_CODES`)→ 不重试 · 进"需处理"
重试没用(用户没改数据前再推还是失败):
`ERR_NO_CLIENT` / `ERR_NO_CUSTOMER_MAPPING` / `ERR_NO_INVOICE_NO` / `ERR_NO_INVOICE_DATE` / `ERR_NO_TOTAL_AMOUNT` / `ERR_NEGATIVE_AMOUNT` / `ERR_TAX_ID_INVALID` / `ERR_DATE_FUTURE` / `ERR_INVOICE_NO_TOO_LONG` 等。
→ status 留 `failed`,前端展示 **needs_action**,给明确原因 + 一键修(绑客户/补字段)+ 重推。

权威判定:`db.is_user_data_error(error_msg)`(单一来源 · `batch_view` 也用它)。

### 业务拒绝 `ERR_BUSINESS` → 进异常给用户
发票号重复 / 账期关闭 / 字段超限 / MR.ERP 返回业务错。

### 技术错 → 自动重试 ≥1 次(60s/5min/30min)
`ERR_TECHNICAL`(超时/浏览器自动化失败)/ `ERR_NETWORK` / `ERR_UNEXPECTED`。
→ `schedule_log_retry` 设 `next_retry_at`,展示 **retrying**。listing 拉取类必 retry ≥1 + 失败截图(铁律 #11)。

### 认证 / 凭据 → 立即 bail(不重试)
`ERR_AUTH`(登录被弹回 · **注意**:2 worker 同账号互踢也会 ERR_AUTH → 已由 session_lock 修)/ `ERR_CRED_DECRYPT` / `ERR_NO_CREDS`。

### 种子 / 创建
`ERR_NO_SEED_CUSTOMER`(无可克隆模板 · 仅当 MR.ERP 客户主数据全空才真失败 · 否则自动挑种子)。

## 5. 历史真实案例(理解状态语义)

- 发票 `INV2026030212`:2026-05-19 `failed · ERR_NO_CUSTOMER_MAPPING`(列表只读 30 条没匹配到买方)→ 2026-05-26 修复后 `success · bill_no SI690319-706687`。同一张,修前**不能**显示完成,修后才能。
- 商品自动建侧疑似仍有"列表只读 30 条"同类 bug(`product auto-create did not appear in listing`)· fail-soft 没炸推送但属误判 · 已记录待修。

## 6. 排障时的状态自检清单

1. 推送结果只信 `erp_push_logs`(`/api/erp/logs/{id}`)· 不信前端乐观态。
2. failed 先看 error_msg 分类(用户数据 / 业务 / 技术 / 认证)→ 决定重试 or 进异常。
3. "成功"务必看 `response_body.mrerp_bill_no` 是否真有 + 必要时查 MR.ERP 报表(铁律 #9)。
4. 对账"完成"务必确认 rows>0 且无 needs_mapping。
