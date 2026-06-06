# 16 · 销项发票 · 后端合规缺口 + 折扣/纸张/留底/打印 设计

> Zihao 2026-06-06 拍板 · 下个窗口实现。本文档**不与 `15-buyer-info-spec.md` 冲突**:
> 15 管「买方类型表单(前端/校验)」,16 管「后端合规硬伤 + 折扣计算 + 纸张/正副本/留底/
> 打印」。两份并列,落点不重叠;凡涉及买方字段一律以 15 为准,本文不重述。
>
> 本文来源:对实际后端代码(`services/sales/document.py`/`pdf.py`/`seller_profile.py`/
> `credit_note.py` + 0006/0008 迁移)的逐文件审查,非空想。

---

## A · 已开单据不可改:买卖双方信息必须冻结快照(合规硬伤)

**现状**:明细行已快照(`unit_price`/`description` 落到 `sales_document_lines`,产品改价不影响已开单)✓。
但 **买方和卖方的 名称/地址/税号/分店/电话 是开票后实时取的**——`routes/sales_routes.py`
出 PDF 时才 `get_buyer`(读 `clients`)、`get_seller`(读 `workspace_clients`)。

**后果**:一张已 `issued` 的税票,事后有人改了客户档案 / 账套主体地址 → **重渲染的 PDF 内容变了**。
泰国 §86/4 已开税票是法律凭证,**买卖双方信息也必须冻结**,不止明细行。

> ⚠️ `15` 第 158 行只把「买方冻结」写成"评估",且**完全没提卖方也有同样问题**。本文把它定死:
> **买方 + 卖方都必须冻结**,且是**必做不是评估**。

**落点**:`issue_document` / `create_note` 开出时,把双方字段快照进 `sales_documents`。
两种实现取其一:
- **方案 1(推荐)**:加一列 `parties_snapshot jsonb`,存
  `{"seller": {...}, "buyer": {...}}`(name/address/tax_id/branch/phone)。PDF 从快照渲染,
  不再实时 join `clients`/`workspace_clients`。
- 方案 2:在 `sales_documents` 平铺 `seller_name/seller_tax_id/.../buyer_name/...` 列。
  字段多、迁移重,但查询友好。

红冲/补开(`credit_note.create_note`)同样要冻结——它现在 `SELECT ... FROM sales_documents`
继承原单,但双方信息当时也没存,需一并补。

### ⚠️ 数据归属:master vs 快照(开写前必须钉死 · 防返工)
`15` 说买方类型/分店"加在 `sales_documents` 或 `clients`"——**本文定死,别二选一犹豫**:
- **master(可改的档案)** = `clients`:`party_type` / `branch` / name / address / tax_id 是客户主数据,长期可维护。买方类型(15)的字段落这里。
- **快照(开票即冻结)** = `sales_documents.parties_snapshot`:开出那一刻把**解析后的买卖双方块**拷进来,此后只读不随 master 变。
- **流向**:`clients`/`workspace_clients`(master)──issue 时拷贝──▶ `parties_snapshot`(冻结)──▶ PDF 从快照渲染。
- 草稿阶段 PDF 预览可实时读 master(还没冻结);**一旦 issued,只认快照**。

这条钉死后,15 的 `buyer_type`/`branch` 全部落 `clients`,16 的冻结全部落 `sales_documents`,两份不打架。

---

## B · 开票时的 §86/4 完整性闸(防开废票)

**现状**:`issue_document` 只校验 `status`,**不校验买方是否填全**。`sales_invoice_sample.pdf`
那张买方 = `-` 的"完整税务发票"能开出,在泰国是张**废票**(买方不能抵扣)。

`15` 给了**前端逐字段**校验(TIN 13 位 / 公司必填分店),但**没有"开出时按单据类型分流"的后端硬闸**。
两者互补,本闸是后端最后一道:

**落点**:`issue_document` 取号前,按 `doc_type` 分流校验(服务端,不信前端):

| doc_type | 开出前必须满足 |
|---|---|
| `tax_invoice`(完整税票) | 买方 name + address + tax_id 齐全;买方类型=公司时还要 branch(见 15) |
| `tax_invoice_simple`(ABB 简易票) | 允许买方空(仅零售 B2C,买方不可抵扣) |
| `receipt` / `quotation` | 按各自最小集 |

校验不过 → 返错误码(如 `buyer_incomplete`),路由层 422,**禁止取号**(避免废票占号)。

---

## C · VAT 价内 / 价外(✅ Zihao 2026-06-06 拍板)

**现状**:`compute_totals` 写死**价外**——VAT 加在单价之上(`vat_amount = vat_base * rate/100`)。

泰国 B2B 多价外没问题,但**零售 / 简易票常是价内含税**(标价已含 7%)。

**✅ 拍板**:
- **默认价外**(不含税,保持现行为,符合主力客户会计事务所 B2B)。
- 开关做在**单据级**(整张发票一个 `price_includes_vat`),**不做行级**(混合价内价外会让用户困惑)。
- 价内时反算:`vat = gross * rate / (100 + rate)`、`net = gross - vat`,其余链路不变。
- 与折扣叠加:先折扣后拆税,保持"VAT 落在折后净额"。
- PDF:价内时票面要标明"价格已含 VAT",并仍**单独列出** VAT 金额(§86/4 要求税额分列)。

---

## D · 折扣 / 优惠 / 内部价(开具 + 计算能力)

**现状盘点(从代码读出)**:
- ✅ 有**行级绝对值折扣** `discount`:`line_total = qty*price - discount`,VAT 已正确按**折后净额**算
  (符合泰国"VAT 落在实际成交价")。
- ❌ **无百分比折扣**(只能传算好的绝对值)。
- ❌ **无整单折扣**(`discount_total` 只是各行折扣之和,不能整单再打折)。
- ❌ **无促销 / 会员内部价概念**(无价目表、无客户专属价)。
- ❌ **折扣在 PDF 上不显示**——`pdf.py` 明细表只渲染 数量/单价/金额,折扣列缺失,
  买方看不到"原价→折后",透明度不足。

**设计(全兼容)**:

1. **行级折扣**:支持两种输入,二选一,内部统一折算成绝对额再算税:
   - `discount_amount`(现有,绝对值)
   - `discount_pct`(新增,如 10 = 打 9 折);`disc = (qty*price) * pct/100`,quantize 到分。
2. **整单折扣**:`sales_documents` 加 `header_discount_amount` 或 `header_discount_pct`,
   在所有行净额之上再减,**按比例摊回各行**以保证 VAT base 正确(混合应税/免税行时尤其重要),
   或整单折扣只摊到应税净额。摊法写死并测,别让前端传摊好的值。
3. **内部价 / 会员价 / 促销价**:本质是**单价覆盖**——开票时允许操作员覆盖 `unit_price`
   (行已快照单价,覆盖后即冻结)。促销可加可选 `price_label`(如 "ราคาสมาชิก/会员价")
   仅作展示。**不引入复杂价目表引擎**(超纲),用"单价可覆盖 + 折扣字段"覆盖绝大多数场景。
4. **PDF 必须显示折扣**:`pdf.py` 明细表加"折扣"列,或在单价下显示"原价划线→折后";
   整单折扣在合计区单列一行 `ส่วนลด / Discount  -xxx`。让买方看得见。
5. **算税铁律(测试覆盖)**:
   - 折扣后**净额不得为负**(校验 `line_total >= 0`)。
   - VAT 永远落在**折后**应税净额。
   - 促销"买赠/0 元行":赠品行 `unit_price=0` 时是否计 VAT 视性质,默认 0 元行不产生 VAT,
     留 `vat_applicable` 由操作员定。
   - 全程 `Decimal`,分位 quantize(现有 `_CENT` 范式延用)。

---

## E · 纸张适配 / 正副本 / 留底 / 打印机(全兼容)

### E1 · 纸张尺寸可选

**现状**:`pdf.py` 写死 A4(`pagesize=A4`)。

**设计**:`render_invoice_pdf` 接受 `page` 参数,支持:
| 尺寸 | 场景 |
|---|---|
| **A4**(默认) | 完整税票 / 事务所标准 |
| **A5** | 小票据 / 省纸 |
| **80mm 热敏卷纸** | POS 零售简易票(ABB)· 窄版单列布局 |
| **58mm 热敏** | 迷你 POS(可选) |

A4/A5 共用现有 platypus 表格布局;热敏走**窄版单列模板**(不能套 A4 表格,列宽会溢出)。
尺寸由 `doc_type` 给默认(完整票→A4,简易票→80mm),**也允许用户在出票时手选**。

### E2 · 正本 / 副本(泰国强制 ≥2 联)

**合规**:VAT 注册方开票**至少出 2 联**——**正本(ต้นฉบับ)给买方**,**副本(สำเนา)自留作证 ≥5 年**。

**设计**:`render_invoice_pdf` 接受 `copy_kind`,在显著位置加水印/角标:
| copy_kind | 标注(泰/中) |
|---|---|
| `original` | **ต้นฉบับ / 正本**(给买方) |
| `copy` | **สำเนา / 副本**(自留) |

- 出票默认生成 **original + copy 两个 PDF**(或一个多页 PDF,首页正本、次页副本)。
- 当一张单同时充当税票+收据+送货单(合并开)时,加 **`เอกสารออกเป็นชุด` / 出据成套** 标注,
  并明确**仅其中一联是税票正本**(避免重复抵扣)。

**`copies_layout` 排版选项(省纸 · Zihao 2026-06-06 提)**:`render_invoice_pdf` 再加一个参数控制正副本怎么排到纸上:
| copies_layout | 行为 |
|---|---|
| `separate`(默认) | 正本、副本各占一页(或两个 PDF) |
| `two_up`(省纸) | **正本 + 副本印在同一张 A4/A5**:上半正本、下半副本,中间一条**虚线裁切线**(`เอกสารออกเป็นชุด`/出据成套)。打一张、撕开,上联给顾客、下联自留。 |

- `two_up` 仅 A4/A5 适用(热敏卷纸不支持,后端遇 `paper=thermal_80` 时忽略并回落 `separate`)。
- `two_up` 下每联用 A4 的半幅版式渲染(字号/边距收紧),两联内容**完全一致**(同号、同金额),仅角标 `ต้นฉบับ` vs `สำเนา` 不同。
- 落点:`pdf.py` 的 `render_invoice_pdf(doc, seller, buyer, *, paper, copy_kind, copies_layout, doc_lang)` 统一收这几个输出参数。

### E3 · 留底(retention)

**合规**:税票及其副本、报表、佐证 **自申报日起至少留 5 年**(最长 7 年)。电子档:
电子原件需归档 5 年;**纸质打印件视为副本**。

**设计**:
- 开票即**持久化冻结数据**(就是 A 节的 `parties_snapshot` + 已有的行快照 + 金额),
  保证**任何时候能字节级重现这张已开票的正本/副本**(留底的本质是"可重现+不可改")。
- 可选增强:开票时把渲染好的 **PDF bytes 存对象存储 + 存 sha256 哈希**进 `sales_documents`
  (`pdf_url` / `pdf_sha256`),副本永远从存档取,不重渲染——**最强留底**,也方便审计核验未被篡改。
- 接 e-Tax 后(见 0006 占位表 `etax_submissions`),电子原件归档以国税厅回执为准,本地留 ≥5 年。

### E4 · 给用户的 / 自留的

- **给买方**:正本(`original`)→ 下载 / 打印 / 邮件 / 接 e-Tax 后带 QR 推送。
- **自留**:副本(`copy`)→ 进留底存档,不外发。
- 前端出票后给两个动作:「下载正本给客户」+「副本已自动归档」。

### E5 · 打印机接入

- **常规(覆盖 95%)**:出 **打印就绪 PDF**,走**浏览器 / 系统打印对话框**——用户在对话框里
  **选打印机、选纸张、选份数**。这条不用我们接驱动,A4/A5 直接可用。零成本最大兼容。
- **POS 热敏**:80mm/58mm 走 E1 窄版 PDF,多数热敏打印机能直接收 PDF;
  要更顺滑可后续出 **ESC/POS** 或本地打印代理(单独阶段评估,**不在本期**)。
- **不做**:浏览器里直连 USB/网络打印机驱动(跨平台坑深、收益低)。打印机选择交给系统对话框。

---

## F · 开具审批(多模式 · 可开关)

> **✅ Zihao 2026-06-06 拍板**:本期**要做**(原"先不做"已撤)。要点:**默认 `none`(关闭),保持现状**;`approval_mode` 开启后 **approver = 账套老板(`tenant_role=owner`)**,创建人=员工(employee)出草稿;**复用主项目现有 owner/employee 角色,不自造权限体系**。`threshold`(按金额)可作后续,先做 `none` + `single` 两档即可。

会计事务所代多家公司开票,**有的要审批、有的图快直接开**——所以审批是**每租户/每账套可开关的多模式**,不写死。

**状态机扩展**(在现有 `draft`/`issued`/`void` 基础上加):
```
draft ──提交──> pending_approval ──批准──> (取号) issued
                       │
                       └──驳回──> rejected ──改──> draft
```

**三种模式(`approval_mode`,落在租户或账套配置)**:
| 模式 | 行为 |
|---|---|
| `none`(默认) | 草稿可直接开出,无审批(保持现行为) |
| `single` | 必须 approver 批准才能取号开出 |
| `threshold` | 金额 ≥ 阈值才需审批,小额直开 |

**要点**:
- 取号/§86/4 完整性闸(B 节)在**开出那一刻**跑,不在草稿阶段——驳回的草稿不占号。
- 审计:`approved_by`/`approved_at`/`rejected_reason`;可选"不得审批自己创建的单"(配置)。
- 审批与角色权限挂钩(creator vs approver),复用主项目既有 RBAC,别在本模块自造权限体系。

---

## G · 日期与历法(税点 / 时区 / 佛历 / 账期)

**现状**:`issue_date` 开出时设为传入的 `on`,无时区推导、无倒填护栏、无佛历。

### G1 · 开票日 = 税点(จุดความรับผิด)
- 默认开票日 = **当天(Asia/Bangkok 本地日期)**。货物税点=交付或收款孰先;服务=收款。
- ⚠️ **时区坑**:库里时间戳是 UTC(`timestamptz`),但**票面日历日必须按曼谷本地推导**,
  不能直接取 UTC 的 date——临近午夜会差一天(连号期间桶 `period_key` 也会错配)。
  `issue_date`(date)要由曼谷本地 now 取,不是 `utcnow().date()`。

### G2 · 倒填 / 未来日期护栏
- **允许**选过去日期,但**不得跨出当前 VAT 申报期(自然月)**——跨月倒填会让连号与 ภ.พ.30 申报错位;
  按 policy 给 warning 或阻断。
- **禁止**未来日期(税点未到不能开)。
- 红冲/补开单自身用**自己的开票日**,但引用原单日期。

### G3 · 佛历(พ.ศ. · 强烈建议)
泰国官方单据常用**佛历 BE = 公历 + 543**(或佛历/公历并列)。PDF 日期标签按模板支持
`พ.ศ.` / `ค.ศ.` 显示选项(数据仍存公历,仅展示层换算)。

### G4 · 账期 / 付款条款
- 账单类单据加 `due_date` / `payment_terms`(如 net 30 天)——B2B 赊销常用。
- 与 H 模板的"付款方式/银行账号"页脚联动。

---

## H · 模板(多公司品牌 · 多场景)

**现状**:`pdf.py` 是**单一硬布局**,所有租户所有单据长一样。会计事务所代 N 家公司开票,
**每家卖方要自己的品牌**——必须模板化。

**模板要素(每个卖方/账套一套)**:
- Logo、抬头色、页脚(银行账号 / 条款 / 联系方式)。
- **公司印章图 + 授权签字行**(泰国票面惯例:ผู้รับเงิน/ผู้มีอำนาจลงนาม 签字 + 盖章位)。
- 语言模式:纯泰 / 泰+英(现行) / 泰+中……(i18n 铁律 4 语)。
- 自定义字段、备注、页脚条款。

**选择优先级**:每卖方默认模板 → 按 `doc_type` 覆盖 → 出票时可临时换。

**落点**:`pdf.py` 把硬布局抽成**配置驱动**——`template_id` 落在卖方/单据,渲染时读模板配置 + 卖方资产(logo/印章/签名/页脚)。
**不做可视化模板编辑器**(超纲);先做 **2–3 套预设布局 + 每卖方可换品牌资产**,覆盖绝大多数。

---

## I · 完整性清单(还没考虑到的 · 按优先级 · 防漏)

调研窗口对"多场景多模式"做的完整性扫描。分级标优先级,**下个窗口据此决定本期做哪些**,别默默漏掉。

### P0 · 合规/正确性硬伤(本期或紧随)
- ✅ **合并"税票 + 收据" + 收款状态** → **已纳入本期**(Zihao 2026-06-06 拍板),独立成 **J 节**。
- **外币 → THB 折算**:`currency != THB` 时,RD 要求票面显示**汇率 + THB 等值**(VAT 必须以 THB 计税)。
  现有 `currency` 字段但**无 FX 汇率、无 THB 等值**。
- **金额大写**(จำนวนเงินตัวอักษร · บาทถ้วน):泰国收据/发票**标配**,泰文 +(可选)英文大写。
- **印章 + 授权签字行**:见 H,泰国票面惯例。

### P1 · 强烈建议
- **报价单 → 发票转换**:`quotation` doc_type 已有,缺一键转开票流。
- **发送 / 投递**(PO-7):email 带 PDF + 投递日志(接 e-Tax 后带 QR 推送)。
- **完整审计轨**:补 `voided_by`/`approved_by` + 操作日志(现有 `created_by`/`issued_at`)。
- **作废规则细化**:开错票 = 保留原票标 `ยกเลิก`(cancelled)+ 重开 / 红冲,不物删、不复用号(号不复用已 ✓)。
- **WHT 多档**:现单一 `wht_rate` → 按服务类型多档(1/2/3/5%);并定是否出 **WHT 抵扣凭证 หนังสือรับรองการหักภาษี ณ ที่จ่าย**。
- **PromptPay 付款 QR**:票面加扫码付款(便利,非合规)。
- **分支连号系列**:多 branch 卖方按 branch 分号(`numbering` 键加 branch 维度)。

### P2 · 规模化 / 后续
- 周期性 / 订阅发票(recurring)。
- 附件(佐证文件挂单)。
- 批量开票 / 导入开票。
- 印花税 อากรแสตมป์(特定文书;多数收据已豁免,标注即可)。

### 边界(不在本模块 · 归其他 PRD)
- **ภ.พ.30 销项汇总申报** → `MODULE_SALE_VAT_RECON_PRD`,不在开票模块做。
- 进项 / 费用录入 → `MODULE_EXPENSE_PRD_v2`(Paypers 对标)。

---

## J · 税票 + 收据合并单 + 收款状态(本期做 · Zihao 2026-06-06 拍板)

泰国 SME **最常见**的单据 = 一张纸既是税票又是收据(**ใบกำกับภาษี/ใบเสร็จรับเงิน**),收钱当场开。本期一并做。

### J1 · 单据类型
`doc_type` 新增 `tax_invoice_receipt`(税票+收据合并)。三者并存、语义不同:
| doc_type | 含义 | 是否税票 | 是否已收款 |
|---|---|---|---|
| `tax_invoice` | 赊销税票(账单) | 是 | 不一定(可赊) |
| `receipt` | 纯收据 | 否 | 是 |
| `tax_invoice_receipt` | **合并单** | **是** | **是** |

- PDF 抬头:`ใบกำกับภาษี/ใบเสร็จรับเงิน / Tax Invoice / Receipt`(加进 `pdf.py:_DOC_LABEL`)。
- 合并单**本质是完整税票** → §86/4 完整性闸(B 节)按 `tax_invoice` 同等对待(买方须齐全;B2C 零售走简易合并另说)。
- 连号:`tax_invoice_receipt` 走**自己的序列**(`DEFAULT_PREFIX` 加一项,默认前缀按业务定,如 `INV`),不与纯税票/纯收据混号。

### J2 · 收款状态(新增字段 · 落 `sales_documents`)
```
payment_status   text   -- 'unpaid' | 'partial' | 'paid'(默认 unpaid)
paid_amount      numeric(14,2)  default 0
payment_method   text   -- 'cash'|'transfer'|'cheque'|'card'|'promptpay'|其他
payment_date     date
```

### J3 · 开票校验(接 B 节闸)
- `receipt` 与 `tax_invoice_receipt` **开出时必须已收款**:`payment_status != 'unpaid'` 且
  `payment_method`/`payment_date` 齐全,否则返 `payment_required`,**禁止取号**(收据=收钱凭证,无款不开)。
- `tax_invoice`(赊销)允许 `unpaid` 开出。
- `partial`(部分收款)= 合法,票面标已收/未收金额。

### J4 · PDF 渲染
合并单在常规税票块之上,**加一个"收款"区**:收款方式 / 收款日 / 已收金额 / (partial 时)未收余额 +
收款人签字行(归 H 模板)。复用 E2 正副本:正本给买方、副本自留。

### J5 · 落点
- 迁移 `0009`:`sales_documents` 加 J2 四列。
- `document.py`:`DEFAULT_PREFIX` 加 `tax_invoice_receipt`;`issue_document` 接 J3 收款校验;
  建草稿/开票收 `payment_*` 字段并归一化(服务端不信前端)。
- `pdf.py`:`_DOC_LABEL` 加合并单;收款区渲染。

---

## K · 前端能力 ↔ 后端归属(防"前端做了后端调不动" · Zihao 2026-06-06)

开票页样稿(桌面 `Pearnly开票UI预览/index.html`)已设计的每个能力,后端是否本期具备,**前端实现窗口照此对齐,别给后端没有的功能做真按钮**:

### ✅ 本期后端具备(15/16 已规划)
单据类型(含合并单 J)· 买方类型动态(15)· 折扣 行/整单/百分比(D)· VAT 价内外(C)· 收款状态(J)· 日期/佛历/账期(G)· 纸张 A4/A5/80mm(E1)· 文档语言 泰/泰英/泰中(H)· 正本/副本 + **省纸两联同页**(E2)· 留底归档(E3)· 开具审批(F)· §86/4 合规闸(B)· 金额大写(I-P0)· 下载 PDF(`pdf.py` 已有)。

### 🖥 纯前端 · 不需要后端
**打印**:点按钮 → 浏览器/系统打印对话框,用户自选打印机/份数。后端只产出打印就绪 PDF,不接驱动(E5)。

### 🕒 未来期 · 本期后端【没有】→ 前端按钮标"即将"或先不做
| 前端按钮 | 归属 | 说明 |
|---|---|---|
| **邮件发送** | **PO-7 发送**(单独期) | 本期无发送服务,前端不接真调用 |
| **LINE 发送给买方** | **PO-7 + LINE 集成** | 同上;依赖现有 LINE 通道改造 |
| **PromptPay 付款二维码** | **I-P1(下一期)** | 本期不生成 QR |

> 规则:上面🕒三项,前端可保留入口占位(置灰/标「即将」),**但不得调后端**——否则前端做了、后端调不动。等 PO-7 / P1 落地再接真调用。

| 项 | 文件 | 改动 |
|---|---|---|
| A 双方冻结 | `0009` 迁移 + `document.py`/`credit_note.py`/`seller_profile.py`/`sales_routes.py` | 加 `parties_snapshot jsonb`;issue/create_note 时写入;PDF 从快照渲染 |
| B 完整性闸 | `document.py:issue_document` | 取号前按 doc_type 校验买方完整性,返 `buyer_incomplete` |
| C 价内/价外 | `0009` 迁移 + `document.py:compute_totals` | 加 `price_includes_vat`(产品定调后) |
| D 折扣 | `0009` 迁移 + `document.py:compute_totals` + `pdf.py` | 加 `discount_pct`/整单折扣;PDF 显示折扣列 |
| E1 纸张 | `pdf.py:render_invoice_pdf` | 加 `page` 参数(A4/A5/80mm/58mm) |
| E2 正副本 | `pdf.py` | 加 `copy_kind`(original/copy)角标 + 成套标注 + `copies_layout`(separate/**two_up 省纸两联同页**) |
| E3 留底 | `0009` 迁移 + 出票流程 | 冻结数据持久化;可选存 `pdf_url`/`pdf_sha256` |
| E5 打印 | 前端 | 浏览器打印对话框出 PDF,本期不接驱动 |
| F 审批 | `0009` 迁移 + `document.py` + 状态机 | 加 `approval_mode` + `pending_approval`/`rejected` 状态 + `approved_by/at` |
| G 日期历法 | `document.py:issue_document` + `pdf.py` | 曼谷本地日推导 + 倒填/未来护栏 + 佛历展示 + `due_date` |
| H 模板 | `0009` 迁移 + `pdf.py` | `template_id` 落卖方/单据;布局抽成配置;卖方品牌资产(logo/印章/签名/页脚) |
| I 完整性清单 | — | P0/P1/P2 分级,下个窗口选本期范围 |
| **J 合并单+收款** | `0009` 迁移 + `document.py` + `pdf.py` | 加 `tax_invoice_receipt` 类型 + `payment_status/paid_amount/method/date`;收据/合并单开出须已收款 |

> 迁移统一新建一个 `0009_sales_compliance_output.py`(承 A/C/D/E3/F/G/H/J 的列),别拆成多个零碎迁移。

---

## L · 后续功能规格(补齐"图纸" · 让下一棒有图施工)

原本只在 §I 列了一行的几项,这里补成可直接实现的规格。

### L1 · PromptPay 付款二维码(便利 · 非合规)
泰国标准付款方式。给**未收款**的票(或当付款请求)在票面/界面放一个 PromptPay QR,买方扫码即付。
- **卖方加字段**:`workspace_clients.promptpay_id`(手机号 / 身份证号 / 税号之一,EMVCo PromptPay 标准支持)。
- **生成**:新建 `services/sales/promptpay.py` —— 按 PromptPay EMV 格式拼 payload(含 `promptpay_id` + 金额=`grand_total`)→ 用 `qrcode` 生成图。
- **出口**:① 界面成功面板「生成付款二维码」按钮调它;② 可选嵌进 PDF(未收款票)。
- **条件**:仅 `payment_status='unpaid'` 或显式"出付款请求"时显示;已收款不出。
- **落点**:`promptpay.py`(payload+QR)· seller 加列(并入新迁移)· 路由 `GET /sales/documents/{id}/promptpay-qr`。

### L2 · WHT 多档(预扣税按服务类型)
现状 `wht_rate` 单一自由值。泰国 WHT 按服务类型分档:**1%**(运输)/**2%**(广告)/**3%**(服务·专业费)/**5%**(租金)等。
- **设计**:把自由 `wht_rate` 换成**预设档下拉**(0/1/2/3/5% + 自定义),**保持单据级**(与现状一致;**per-line 留后续**)。
- **票面**:WHT 行已显示(§D),补档位说明(如 `หัก ณ ที่จ่าย 3%`)。
- **边界**:销项票上 WHT 只是"应收的扣减项";**WHT 抵扣凭证(หนังสือรับรองการหักภาษี ณ ที่จ่าย)由付款方=买方出**,不在本模块出。
- **落点**:`compute_totals` 不变(已按 `wht_rate` 算)· 前端/校验把自由值改预设 + 存档位标签。

### L3 · 报价单 → 发票转换
`quotation` doc_type 已有,缺一键转开票。
- **设计**:`convert_quotation(quote_id, target_doc_type)` —— 复制报价单买卖双方 + 明细行,新建一张**草稿**(`tax_invoice`/`tax_invoice_receipt`),`references_document_id` 指原报价单;报价单本身不变。
- **取号**:转出的新票按自己类型,**开出时**才取连号(报价单不占发票号)。
- **落点**:`services/sales/document.py` 加 `convert_quotation` · 路由 `POST /sales/documents/{id}/convert`。

### L5 · 发送(PO-7 · ✅ Zihao 2026-06-06 拍板 · **只做两档·已上线**)
发票发给买家,**只做这两档**(都已实现上线 prod);**私人 Gmail / LINE 官号推送 = 已砍**(太麻烦·不做)。
| 渠道 | 机制 | 状态 |
|---|---|---|
| **邮件(Pearnly 代发)** | 从 `hello@pearnly.com` 发 PDF 附件;`From` 显示卖方名、`Reply-To` 卖方邮箱(买家回信回卖方) | ✅ 已上线(`services/sales/send.py`) |
| **LINE(生成链接·自己转)** | 生成不可猜分享 token → 公开 `GET /shared/{token}/pdf`,卖方用**自己 LINE** 转给买家 · 适配所有买家 | ✅ 已上线(`services/sales/share.py`) |

**❌ 已砍(2026-06-06 · 不做)**:
- **私人 Gmail 发信**(OAuth + Google 审核那套)—— 太麻烦,删空壳,不做。
- **LINE 官号推送**(@pearnly 自动推)—— 受 LINE 好友限制 + 计费,不做。
- 后端清理:删 `oauth_routes` 里 `gmail.send` 相关空壳/501 桩;`/send` 只保留 email + line(share)两档。前端发送弹窗只留这两档。

### L4 · H 模板(✅ 策略已定 · Zihao 2026-06-06)
**做法 = 多套精选模板 + 每家自定义品牌**(不做"上传任意模板让系统学习")。
- **为什么不做 upload-and-learn**:任意旧票图/Word 像素级复现极不稳;§86/4 强制字段必须每张都在,自由模板易漏字段=废票。大厂(Xero/QuickBooks/FlowAccount)都是"精选模板 + 换 logo/颜色/印章/页脚"。
- **精选模板**:内置 **6 套**(经典/简约/品牌色/紧凑/泰式官方/极简黑白,见 `app.html` 账套页)。
- **每家自定义**:`workspace_clients` 加 `template_id` + `brand_color` + 品牌资产 `logo_url`/`seal_url`/`signature_url`/`footer_text`(+ §L1 `promptpay_id`)。
- **绑定关系**:**配置一次/每个账套** → 该账套开的每张票**自动套这套模板+品牌**(渲染时 `pdf.py` 读账套 `template_id`+资产+`brand_color`)。单据可临时改模板(覆盖)。
- **"真要复刻某张特定旧版式"** = 一次性定制模板服务(人工加一套预设),不是自动学习。
- **落点**:`pdf.py` 渲染按 `template_id` 选布局 + 套 `brand_color`/资产;迁移加上述列。**视觉已定稿(6 套预设),后端可照做,不再 Zihao-gated。**

---

## M · 执行顺序到闭环(下一棒按此逐一做 · 每块"做完即验")

> 原则:**每做一块就验一块**(本地全量 unittest + 真账号 E2E),不攒批;高敏步骤(prod 迁移 / LINE)需 Zihao 授权或在场。

1. **C 价内外**(§C · 默认价外·单据级开关·不做行级)
2. **省纸·正本+副本同页**(§E2 `copies_layout=two_up`)
3. **F 审批**(§F · 默认 `none`·开启则 owner=审批人·复用现有角色·先 none+single)
4. **E3 `pdf_sha256` 留底增强**(§E3) + **热敏 80/58mm 窄版模板**(§E1)
5. **L1 PromptPay** / **L2 WHT 多档** / **L3 报价转换**(§L)
6. **L4 H 模板后端管道**(§L4 · 视觉留待设计稿)
7. **开票设置存储 + 主数据补字段**(§N 契约缺口):建 `sales_settings`(连号默认/审批/价内外/WHT/模板/语言/纸张/省纸)· `clients` 补 `party_type/branch/promptpay_id` · `workspace_clients` 补品牌资产+`template_id`。
8. **PO-7 发送**:**邮件**先做;**LINE 发送 = 高敏,留 Zihao 在场**
9. **PO-10 全模块前端**(§N 8 屏):按桌面整套样稿 **`Pearnly开票UI预览/app.html`**(工作台/详情/商品/客户/账套+模板/设置)+ **`index.html`**(开票向导)+ `sales-buyer-block-draft.html`(买方逻辑)→ i18n 4 语 → 真账号 E2E → **上线闭环**

> 卡口提醒:**H 视觉**与 **LINE 发送**不要无人值守闷头做——前者等设计稿、后者等 Zihao 在场(铁律 #26)。其余 1–6 + 邮件 + PO-10 可按序推进,逐块验证。每块涉及 prod 迁移的,走既定 ssh+psql 通道并经 Zihao 授权。

---

## N · 全模块界面地图 + 前后端契约(整套图纸 · Zihao 2026-06-06)

> 设计原则(Zihao):像修房子——**先把整套图纸出完**(结构+水电+装修),施工窗口照图建,建完用户直接能用。开票向导只是其中一屏;整个模块要下面 8 屏才闭环。
>
> **设计稿(桌面·施工依据)**:`Pearnly开票UI预览/app.html`(模块工作台:列表/详情/商品/账套+模板)+ `index.html`(开票向导:整流程+输出设置+省纸+成功面板)+ `sales-buyer-block-draft.html`(买方状态机逻辑)。**实现 PO-10 照这三份;视觉别另起。**
>
> **导航归属(Zihao 2026-06-06 拍板 · 贴现有左栏 IA · 别新建导航)**:
> - **开票相关屏进「销项管理 ▸ 销售发票 ▸ {发票工作台 / 账套·开票资料}」子导航**(点"销售发票"展开下拉)。
> - **商品管理 = 顶层「主数据」区**(挨着客户管理),**不放销售发票子菜单下**——商品是**共享主数据底座**(开票/未来 POS/库存都复用同一份·见 `docs/PRODUCT_VISION_MODULAR.md`),与客户管理同级。`products_routes` 已有。
> - **客户管理 = 复用现有顶层「客户管理」**(`clients_routes` + 现有页),**不新建**;本模块只给它**补字段** `party_type`/`branch`/`promptpay_id`。
> - **开票设置 = 右上角「开票」按钮旁的齿轮(弹窗)**,不占导航项。

### 屏幕清单 ↔ 后端就绪度
| 屏 | 作用 | 后端接口 | 状态 |
|---|---|---|---|
| **发票工作台**(列表) | 看所有票·筛选·搜索·汇总·入口 | `GET /sales` | ✅ 有 |
| **发票详情** | 查看 + 下载PDF/打印/发送/作废/红冲/补开/转换/复制 | `GET /{id}`·`/pdf`·`/void`·`/credit-note`·`/debit-note` | ✅ 有 |
| **开票向导** | 开一张票(5 步) | `POST /sales`·`PATCH`·`/issue` | ✅ 有(向导已设计) |
| **草稿继续** | 列表筛"草稿"→ 进向导改 | `PATCH /{id}`·`/issue` | ✅ 有 |
| **商品管理** | 列表/增改/Excel导入/商品图 | `products_routes` 全 CRUD+import | ✅ 有 |
| **客户管理** | 买方档案(**加 party_type/分店/promptpay**) | `clients_routes` CRUD(已存在) | ⚠️ 有页·**缺新字段** |
| **账套/开票资料** | 卖方资料 + 品牌资产 + **模板选择**(H 视觉) | `sales_seller_routes` PUT | ⚠️ 有·**缺品牌/模板字段** |
| **开票设置** | 连号前缀/重置/**起始号**·审批模式·价内外默认·WHT档·默认模板/语言/纸张/省纸 | — | ❌ **缺设置存储** |

### 前后端契约缺口(两边都要补 · 下一棒先做)
1. **开票设置存储(后端 gap)**:现在连号/审批/价内外都是"开票时传参",**没有租户默认设置的存储**。需建 `sales_settings`(tenant 级:`number_prefix`/`number_reset`/`number_start`/`approval_mode`/`price_includes_vat_default`/`default_wht_rate`/`default_template_id`/`default_doc_lang`/`default_paper`/`default_copies_layout`)+ 读写接口。开票时读默认、可单据覆盖。**起始号**用于接旧账本(设 `number_start` = 旧末号+1)。
2. **买方 = 从客户档案选/建**:向导买方步骤不是裸填,而是**搜 `clients` 选已有,或就地新建**(新建走客户管理同一套 party_type 状态机);选定后**冻结进 `parties_snapshot`**(§A)。
3. **客户管理加字段**:现有 `clients` UI 补 `party_type`/`branch`/`promptpay_id`(对齐 15)。
4. **账套加字段**:`workspace_clients` 补品牌资产(`logo_url`/`seal_url`/`signature_url`/`footer_text`/`promptpay_id`)+ `template_id`(§L4)。

### 税号验真 + 一键带出(✅ Zihao 2026-06-06 · Phase 1 · 后端已有)
买方填税号这步加"更智能"两档(治客户痛点"填错被税局退"):
- **验真**:任意类型税号 → `POST /api/rd/verify` 校验真伪(绿勾/红叉)。
- **一键带出(仅公司)**:输 13 位公司税号 → `POST /api/rd/lookup`(税局 VAT Service · **返 17 字段:登记名称/地址/分店**)→ **自动填买方名称/地址/分店**(填后可改)。
- **范围**:仅**公司(法人)**可带出;**个人(身份证)/外国(护照)无此服务**(隐私·只验真或手填)。
- **兜底**:税局服务慢/查不到 → 回退手填,不阻断。`rd_cache` 已做缓存(见 `services/rd/rd_api.py`)。
- **落点**:后端接口**全已有**(`routes/rd_routes.py`),前端在买方步骤 + 客户管理弹窗各加一个「验真·带出」按钮。

### H 模板视觉(已出设计 · 不再 Zihao-gated)
`app.html` 账套页已给 **3 套预设模板**(经典表格线 / 简约 / 品牌色)+ 品牌资产位 + 实时预览。后端按 §L4 搭管道(存 template_id + 资产);渲染按选定模板出 PDF。**视觉已定稿,后端可照做。**

---

## 合规依据(留档)

- **双方信息冻结**:§86/4 已开税票为法律凭证,信息须固定;明细已冻结,双方信息同理。
- **§86/4 完整性**:13 项强制字段缺一即废票,完整票必须买方齐全;ABB 简易票方可省买方。
- **正本/副本 ≥2 联**:VAT 注册方至少出 2 联,正本(ต้นฉบับ)给买方、副本(สำเนา)自留。
- **留底 5 年**:税票及副本自申报日起留 ≥5 年(最长 7 年);电子原件电子归档,纸质打印件视为副本。
- **折扣计税**:VAT 落在折后实际成交净额(现行 `compute_totals` 已符合,扩展时保持)。

### 信源(调研窗口核实)

- [Revenue Code §86 — Tax Invoice / Debit / Credit Note (Siam Legal)](https://library.siam-legal.com/thai-law/revenue-code-tax-invoice-debit-note-credit-note-section-86/)
- [Types of tax invoices & paper issuance — THAILAND.GO.TH](https://www.thailand.go.th/issue-focus-detail/006_124)
- [Thailand e-Tax & e-Receipt 2025 compliance checklist (retention)](https://www.gentlelawibl.com/post/thailand-e-tax-invoice-and-e-receipt-2025-a-compliance-checklist-for-smes)
- [Thailand Tax Invoice Requirements: Full vs Abbreviated](https://invoicedataextraction.com/blog/thailand-tax-invoice-requirements)
