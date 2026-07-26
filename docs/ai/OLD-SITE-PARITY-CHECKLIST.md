# 老站功能对齐清单(/home 会计壳 → /ai 智能管家)

> **退役闸:本清单未全绿,/home 老站不得下线。**(老板拍板 · 2026-07-26)
>
> 本文是**能力账本 + 退役验收门,不是 UI 迁移单**。事实全部来自真代码
> (`src/home/route-table.ts` 路由表 / `src/home/app-shell-sidebar-html.ts` 侧栏 / 服务层),
> 每条带关键文件;拿不准的标「待核」。

## 0. 对齐原则(先读 · 防误读)

**对齐的是能力,不是界面;老站 UI 一寸不搬。** 每条能力在新世界的吸收方式按优先级四选一(可多选):

1. **自动** — 后台自动,不需要任何界面(如方向税号自动判、防重单、自动重试)。
2. **配置** — 客户配置单一次签(如管不管库存、服务/库存的默认走向)。
3. **对话** — 管家对话 / 授权卡 / 裁决队列(查状态、授权、单票裁量、失败补答)。
4. **界面** — 仅必要时保留专用界面(如大批量逐票复核的队列页),**且只用 /ai 现有页面,不新增**。

「落点」= /ai 已有位置,或排期批次:**B2 管家M1 / B3 授权与主动汇报 / 桥P0只读 / 桥P2写路 / 待排**。
「验收态」三档口径见 §1 表头下一行说明。

服务层(`services/`)是入口无关的:方向判定 / 过账去向 / 防重单 / 现赊漏斗等全在后端,
桥P2 接通写路后 /ai **免费继承**,不存在"逻辑搬家"。

## 1. 主清单

「验收态」口径:**老站在用** = /ai 侧尚无对应物;**未验** = /ai 已有对应物但未真机验收;**—** = 已判定无需对齐 / 不入退役闸。

| # | 能力(老站入口) | 老站现状(关键文件) | 吸收方式 | 落点 | 验收态 |
|---|---|---|---|---|---|
| 1 | 录入工作台 · 逐张识别四步(#/dms-intake) | 传票→OCR→复核→推ERP;`src/home/dms-intake-core.ts`、`dms-intake-invoice*.ts` | 自动+界面 | 收料/复核 /ai 已有:客户页 intake 视图(`static/ai/ai-intake-queue.js`、`ai-api-upload.js`)+ 复核队列(`ai-review*.js`);推 ERP → **桥P2写路** | 未验 |
| 2 | 本批裁量控件(方向 / 过账去向) | 见 §2 逐控件细目;`src/home/dms-intake-invoice.ts`、`services/erp/express_push/{direction,posting_kind,posting_profile}.py` | 自动+配置+对话 | 方向自动判已在服务层;去向 → 配置单一次签(雏形已有 `static/ai/ai-profile.js` 画像+供应商过账档案)+ 单票裁量走裁决队列;生效面随**桥P2写路** | 未验 |
| 3 | Express/MR.ERP 连接卡 + 启停闸(#/dms-intake、#/integrations) | 状态卡+启用/停用,停用 = 第四步不显示该端点 + 自动推按 enabled 过滤;`src/home/dms-intake-erp-cards.ts`、`services/erp/push_store.py` | 配置+对话(启停=授权卡) | 连接状态灯 → **桥P0只读**;启停授权 → **B3 授权与主动汇报** | 老站在用 |
| 4 | 识别记录台账(#/history) | 搜索/日期段/批量导出/批量删除,近 90 天;`src/home/page-history.ts`、`history-list.ts` | 对话(问"那张票")+界面(工单历史) | **B2 管家M1**(近亲已有:客户档案 history tab,`static/ai/ai-client-archive.js`) | 老站在用 |
| 5 | 复核工作簿四表导出 | ขาย(销项逐商品行)/ ซื้อ(进项逐票)/ รอจำแนก(待判+原因)/ สรุป(本批新建主档清单);`services/excel/erp_workbook.py` | 自动(推完自动出)+对话(管家递交) | **桥P2写路**(推完才有产物) | 老站在用 |
| 6 | 工作簿回导重推 | 表头指纹命中→确定性逐格解析不喂大模型;「挪行=改分类」落 `fields.direction`;`services/ocr/roundtrip_intake.py`、`services/excel/erp_roundtrip_reader.py`、`services/erp/express_push/direction.py` | 自动 | **桥P2写路** | 老站在用 |
| 7 | 推送日志(#/push-logs) | 成功/失败/重试中筛选、批量重推、失败就地修复;`src/home/page-push-logs.ts`、表 `erp_push_logs` | 自动(重试)+对话(失败主动汇报、补答后重推) | **B3 授权与主动汇报**;重推写路随**桥P2** | 老站在用 |
| 8 | 对账中心三页签(#/reconcile) | 银行对账 / 销项税报告核查 / 收入对账;`src/home/page-reconcile.ts`、`recon-center-x-html.ts` | 自动+界面 | 银行对账已有(`static/ai/ai-recon.js` 工单内只读)+ 销项税三查已有(#/vatcheck,`ai-vatcheck.js`)+ 销项佐证卡(`ai-corrob.js`);收入对账页签 → 待排(待核:是否被佐证卡覆盖) | 未验 |
| 9 | 采购/进项台账 + 导出(#/purchase、#/purchase-export) | 台账/明细/报表导出 + Google Sheet 连接卡(`/api/integrations/google/*`);`src/home/purchase-export.ts`、`purchase-export-google.ts` | 自动(进报表包)+对话 | 待排(近亲已有:报表包 `static/ai/ai-pkg.js`) | 老站在用 |
| 10 | 客户管理(#/clients) | 建档/买卖方档案;`src/home/clients.ts`、`page-clients.ts` | 界面(已有) | 已有:#/clients 目录 + 单客户档案 + 批量导入名录(`static/ai/ai-clients.js`、`ai-client-archive.js`、`ai-client-import.js`) | 未验 |
| 11 | 公司资料(#/company) | 账套主体开票/申报信息行内编辑;`src/home/company-profile.ts` | 配置 | 部分已有:税务画像/义务清单(`static/ai/ai-profile.js`);开票资料字段覆盖度 **待核** | 未验 |
| 12 | 异常栏(#/exceptions) | **2026-07-26 已下线**(`route-table.ts` 注释:路由摘除、侧栏恒隐、后端开关关) | — | 无需对齐;其职能由 /ai 异常票据裁决队列吸收(`ai-review-inbox-flagged.js`) | — |
| 13 | 报表导出 | 报表模板/统一导出弹窗(`src/home/report-templates.ts`);出账本/报税包(#/acct-books,`acct-books.ts`,做账模块门控) | 自动+界面 | 已有近亲:报表包 + BS/PL/TB 三件套 + #/reports(`static/ai/ai-pkg.js`、`ai-financials-render.js`、`ai-reports.js`);逐项覆盖度 **待核** | 未验 |
| 14 | 集成页(#/integrations、#/cloud、#/api-keys) | 小助手下载/配对向导 + ERP 日志区(`src/home/page-integrations.ts`);#/cloud、#/api-keys 是 coming-soon 占位(`src/home/page-placeholders.ts`) | — | **无需对齐**。① 小助手下载/配对 → **随老站一同退役**:新桥是装在 Express 数据所在文件服务器(192.168.0.212)的独立程序,自己直读 DBF,端点身份 / 密钥 / 发布通道全独立,不需要小助手在线也不经过它(桥P0只读已完工:`pearnly-companion` 仓 `bridge/`,commit a558f45,7 个真账套只读冒烟通过);老站退役=小助手退役,分发/配对页随之作废。② 云盘 → 占位页,无需对齐。③ API keys → 同为占位页,**今天无消费方**(`route-table.ts` 的 `ROUTE_LOADERS` 无 `api-keys` 项、`static/dist/home.html` 无 `data-route="api-keys"` 侧栏入口、后端 0 个 API key 端点),无需对齐 | — |
| 15 | 使用教程(#/guide) | Express 推送手册,中泰双语,按篇 JSON 懒加载;`src/home/guide-page.ts`、`guide-content.ts` | 对话(管家就地答)+界面 | 待排(管家问答可吸收大部分「怎么做」类查询) | 老站在用 |
| 16 | OCR 余额 / 充值 | 充值弹窗三步流 + 余额实时轮询;`src/home/billing.ts`、`billing-records.ts` | 界面 | 待排(计费钱路径,或保留全局入口不随壳走 · **待核**) | 老站在用 |
| 17 | 汇总表 → 批量建单(#/dms-intake 第三卡) | 两种录入模式之二(逐张识别 vs 汇总表批量),见 §3;`src/home/dms-intake-batch*.ts`、`services/summary_import/` | 自动+对话 | **桥P2写路**(建单+推全链);近亲已有:银行倒推日销(`static/ai/ai-intake-bank-sales.js`) | 老站在用 |

## 2. 录入工作台「本批裁量」控件细目(老板点名 · 逐控件)

老站在向导 step① 侧栏放两个批级声明卡(`src/home/dms-intake-invoice.ts` 的
`directionHtml()` / `postingKindHtml()`),识别请求就带上(`dms-intake-invoice-recognize.ts`:
开自动推的客户识别完即推,走不到第 4 步传参)。

### 2.1 方向声明(进项 / 销项 · 单选可取消)

| 选法 | 语义(真代码) |
|---|---|
| 选「进项」/「销项」 | 按用户选的做,不再拿税号猜(税号读错=方向判反);落 `fields.direction`,`explicit_direction` 最高优先(`services/erp/express_push/direction.py`) |
| 不选(默认) | 税号锚点自动判:自家税号=票面卖方→销项、=买方→进项;对不上/都命中/没读到 → ambiguous 留人工,不硬猜(`direction.py::detect_by_tax`,税号经 `clean_tax_id` 归一防脏匹配) |
| 与回导的关系 | 批级声明**不覆盖**已有值:回导行的方向是会计逐行裁决(行在哪张 Sheet),比整批选更具体(`direction.py::apply_batch_direction`) |

新世界吸收:税号锚点判定本来就是**自动**兜底,无需任何界面;ambiguous 走**裁决队列**问一句。开关 UI 不搬。

### 2.2 过账去向(服务 / 库存 · 仅有启用的 Express 端点才出现,MR.ERP 无此拆分)

| 选法 | 语义与落 ERP 落点(真代码) |
|---|---|
| 服务(service) | 非库存路径:销项走收入式入账 + 建/复用**非库存服务档**(`sales_mapper.py` → `ITEM_MODE_NONSTOCK`);采购明细行非库存、不动库存(`mapper.py::_goods_item_mode`) |
| 库存(stock) | 采购:建/复用 **STKTYP=0 库存品(STMAS)真入库、移动均价**;销项:`stock_sale` **扣库存 + 结转 COGS**,与采购入库合成闭环;零主档账套由 ISACC 存货科目组从零建档(`stock_acc_group.py::resolve_stock_acc_group`,合格组唯一则自动过);「选了库存就一定能落」——品不在账/负库存照落,无成本基础不结转(`sales_mapper.py` 2026-07-25) |
| 不选(默认) | 沿用账套既有记法 = 记账画像(`posting_profile.py`:non_stock / direct_account / stock / manual_review,由 Express 记账指纹推断+会计确认一次);**永续客户+库存路未开 → escalate 交会计,绝不静默按周期制落**(防双重计成本) |
| 声明的载体 | **跟票走不跟推送走**:上传时写 `ocr_history.posting_kind`,手动推/自动推/失败重试/批量分拣四条腿都读到(`posting_kind.py`);**故意没有账套级默认**——常驻默认等于把 escalate 安全网长期关掉 |
| 显式声明的效力 | 显式选了即绕过「永续→交会计」的自动 escalate(`mapper.py` / `sales_mapper.py`);费用票不受此开关影响(进项税不可抵、计入成本,与库存无关) |

新世界吸收:「这家客户管不管库存」是**配置单一次签**(②,/ai 画像+供应商过账档案已有雏形);
单票例外与 escalate 补答走**对话/裁决队列**(③);两个开关 UI 都不搬。生效面随桥P2写路。

## 3. 已上线细能力(服务层佐证 · 桥P2 接通即免费继承)

| 能力 | 佐证(关键文件) |
|---|---|
| 汇总表→批量建单全链 | `services/summary_import/`(parse/mapping/judge/commit 四层):xlsx/csv 表头+行解析、列映射+批次常量(散客 cash_walkin、固定单价、佛历年月拼日期)、判方向复用税号锚点、逐行独立建单不连坐;前端四步 `src/home/dms-intake-batch*.ts`,后端 `/api/summary-import/{parse,validate,commit}` |
| 采购逐行预扣税 WHT 可编辑 | `services/purchase/totals.py`(每行 `wht_rate` 独立计税累计)、`src/home/purchase-form.ts`(服务默认率 `default_wht_service_rate`,默认 3%,采购设置页可改) |
| 散客现金票归一 เงินสด | MR.ERP 无对手方票自动归现金对手方(`services/erp/mrerp_http/routing.py`、`autocreate.py`);汇总表批次常量 cash_walkin 同语义(`services/summary_import/mapping.py`) |
| 现/赊六级漏斗(HS/IV 单别) | 人工裁决 > 票面显式字段 > 票种语义 > 银行佐证 > 无信号默认赊销(`services/erp/express_push/payment.py`、`common.py::payment_verdict`) |
| 防重单/幂等闸 | 重推前查既有单据,软删行也算(2026-07-25 三堵墙);`services/erp/express_push/prior_doc.py` |
| 供应商自动建档 | 未映射供应商 `supplier_new=True`,小助手在 APMAS 建档带税号/地址(`mapper.py::_resolve_supplier`) |

## 4. 初盘遗漏 · 本轮补录(未入 16 项初盘的老站路由)

| 能力(入口) | 老站现状 | 吸收方式 / 落点 | 验收态 |
|---|---|---|---|
| 商品数据 / 费用数据主档(#/sales-products、#/expense-data) | 商品库 + 费用两级 CRUD/关键词规则;`src/home/sales-products.ts`、`expense-data.ts` | 配置+自动;落点 **待排**(推送建档已自动化,见 §3 供应商建档) | 老站在用 |
| 供应商档案(#/purchase-suppliers) | 采购供应商台账;`route-table.ts` | 配置;/ai 已有近亲:供应商过账档案(`ai-profile.js` Z3-b)· 覆盖度 **待核** | 未验 |
| 采购设置(#/purchase-settings) | WHT 默认率等;`src/home/purchase-settings.ts` | 配置(并入客户配置单);**待排** | 老站在用 |
| 拍照采集(#/purchase-capture) | 手机拍票直录;`src/home/purchase-capture.ts` | 界面(/ai 收料口已收全格式,覆盖度 **待核**) | 未验 |
| 首页仪表盘(#/dashboard) | 余额/统计卡;`src/home/dashboard.ts` | 已有:/ai 工作台矩阵默认首页(`static/ai/ai-matrix.js`) | 未验 |
| 设置页(#/settings) | 语言/账号;`src/home/page-settings.ts` | 已有:#/settings(`static/ai/ai-settings.js`) | 未验 |
| 客户知识(#/knowledge,flag 门控) | 知识中心问答;`src/home/knowledge-ask.ts` | 对话(管家天然吸收);**B2 管家M1 · 待核** | 老站在用 |
| 做账模块群(#/vouchers、#/acct-*、#/tax-*) | 自动凭证/逐笔审/科目表/银行对账/出账本/报税中心;`route-table.ts` MAIN_ENTRY_ROUTES。门控 = `accounting` 模块:`services/modules/store.py` 的 `DEFAULT_ENABLED` 里默认 `False`(opt-in),后端 `routes/accounting_common.py::gate` 未开即 403,侧栏 `data-module="accounting"` 由 `/api/me/modules` 显隐(`src/home/module-nav.ts`) | **不入退役闸**:默认关闭,且**无外部租户在用**——2026-07-26 生产只读核(`_gemini_key.local/dbq.py`):40 个租户里 17 个开着 `accounting`,但全是内部号(老板本人 skin306152 / 18685123459、mrerp、PEARNLY、E2E Test Co 1–3、parked 测试号);`journal_vouchers` 219 张同样只出自这 8 个内部号,近 14 天 33 张里 22 张来自老板 dev 账号,`acct_bank_accounts` / `acct_bank_lines` 0 行。事务所实际走 Express 记账;/ai 侧影子底稿(`ai-shadow.js`)+ 财务三件套(`ai-financials-render.js`)已覆盖同类需求。**若将来有外部租户启用,需重新入表** | — |
| 报表模板(#/templates) | 统一导出弹窗;`src/home/report-templates.ts`(ROUTE_LOADERS 无独立 loader,**待核**) | 界面;**待排** | 老站在用 |

## 5. 明确排除(不入退役闸)

- **销售开票**(#/sales-invoices 发票工作台、#/sales-account 账套/开票资料)与 **POS 全组**
  (#/inventory、#/sales-report、#/pos-*):非事务所日常,老板拍板排除。
  注:老站壳级「套账切换器」(全局唯一事实源)在 /ai 由「客户」一级概念替代(#/clients),不单列。

## 6. 超越项(新路比老站强的点)

- **选择前移 · 客户配置单**:税务画像 + 供应商过账档案把「这家客户怎么记」一次签好(`static/ai/ai-profile.js`),不再每批向导里问。
- **escalate 可补答重推**:老站 posting_kind 未选转人工后产品内是死胡同(重试不带 posting_kind、识别记录页无推送入口,只能重传重扣费);新路把异常票收进跨工单裁决队列(`static/ai/ai-review-inbox-flagged.js`),补上裁决即可重走(重推接线随桥P2)。
- **状态灯绑真账证据**:矩阵与佐证卡的状态来自聚合真数(`static/ai/ai-matrix.js`、`ai-corrob.js`),不是人手标的灯。
- **对话式派工**:总台上传 + 说目标即开工(`static/ai/ai-desk.js`),替代「先找到那个页、再找到那个按钮」。

---

维护约定:任何一行状态变化(已验/覆盖度核清/批次交付)须同 PR 更新本表;
「待核」项核清后就地改写,不另开文件。
