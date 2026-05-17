# Pearnly · 进项费用管理模块 PRD
> 对标 Paypers.ai · 一比一复制 + 全面超越
> 版本：v1.0 · 日期：2026-05-14 · 作者：Zihao + Claude

---

## 一句话定位

**Paypers 有的我们全有，Paypers 没有的我们也有。**
会计事务所版进项管理：多客户 · 多语言 · 异常检测 · ERP 直推 · 一站式闭环。

---

## 模块命名

| 语言 | 名称 |
|---|---|
| 中文 | 凭证中心 |
| ไทย | ศูนย์เอกสารจ่าย |
| English | Expense Center |
| 日本語 | 経費センター |

路由：`/expense` · 侧边栏占位已有（「凭证中心」即将上线）

---

## 竞品完整功能清单（Paypers 逐条对照）

### ✅ 第一层：一比一复制（Paypers 有 · 我们必须有）

| # | Paypers 功能 | Pearnly 实现方式 | 底层复用 |
|---|---|---|---|
| 1 | LINE Bot 单聊收票 | ✅ 已有 · 直接复用 | LINE Bot 现有通道 |
| 2 | LINE 群组收票（无限群组）| ✅ 已有 | LINE 群组通道 |
| 3 | Gmail 扫描收票（附件 + 正文）| ✅ 已有 | 邮件自动化通道 |
| 4 | 网页手动上传（PDF/图片）| ✅ 已有 | 上传识别模块 |
| 5 | AI OCR：发票/收据/手写账单 | ✅ 已有（更强）| Gemini OCR 引擎 |
| 6 | AI OCR：Shopee/Lazada 截图 | 🔧 新增支持 | OCR prompt 扩展 |
| 7 | AI OCR：转账单（银行截图）| 🔧 新增支持 | OCR prompt 扩展 |
| 8 | 费用自动分类（餐饮/软件/物流…）| 🔧 新增 | supplier_categories 表已有 |
| 9 | 与泰国公司数据库核对税号 | ✅ 已有（异常栏 Rule 5）| 异常检测引擎 |
| 10 | Google Drive 自动归档（按客户/月）| 🔧 新增（云盘同步模块前置）| 部分底层已有 |
| 11 | Google Sheets 实时同步 | 🔧 新增 | Google OAuth（和 Drive 共用）|
| 12 | 生成代收据（ใบแทนใบเสร็จ）| 🔧 新增 | PDF 生成（weasyprint 已有）|
| 13 | 生成付款凭证 PV（ใบสำคัญจ่าย）| 🔧 新增 | PDF 生成 |
| 14 | 月度支出仪表盘（图表 + 月对比）| 🔧 新增 | 数据已有 · 新建图表 UI |
| 15 | 多公司支持（同账号多公司）| ✅ 已有（多客户体系）| tenant/client 体系 |
| 16 | 购买积分 · 按张计费 | 🔧 新增计费逻辑 | quota 体系扩展 |

---

### 🚀 第二层：超越 Paypers（我们有 · Paypers 没有）

| # | Pearnly 独有功能 | 价值 | Paypers 状态 |
|---|---|---|---|
| **A** | **4 语言完整界面**（泰/中/英/日）| 覆盖日资/中资客户 · Paypers 纯泰文 | ❌ 只有泰文 |
| **B** | **会计事务所多客户管理**（1账号管30家客户）| 事务所核心场景 | ❌ 只支持老板自用 |
| **C** | **异常自动检测**（假票/重票/税号格式/金额矛盾/WHT 异常）| 减少人工复核 | ❌ 只做基础 AI 核对 |
| **D** | **ERP 直推**（发票审核通过后自动推入 FlowAccount/PEAK/ERP）| 完整闭环不断链 | ❌ 止步于 Sheets/Drive |
| **E** | **6 通道收票**（LINE/邮件/文件夹/云盘/网页上传/拍照）| 外勤 + 办公室全覆盖 | ❌ 只有 LINE + Gmail |
| **F** | **批量处理 800 张/月**（异步队列 · 关网页继续跑）| 月底高峰场景 | ❌ 无异步队列 |
| **G** | **进 + 销闭环**（进项管理完成后对接销项 VAT 对账）| 月底一站全搞定 | ❌ 纯进项 |
| **H** | **专业会计师级 PV 模板**（三签名栏 ผู้จัดทำ/ผู้ตรวจสอบ/ผู้อนุมัติ）| 符合泰国事务所标准 | 🟡 有 PV 但较简单 |
| **I** | **操作审计日志**（谁在什么时间改了哪张票）| 审计追溯 · 企业级 | ❌ 没有 |
| **J** | **一页多发票自动拆分**（1个 PDF 含多张票 → 自动拆）| 大客户场景 | ❌ 没有 |

---

## ❌ 不做什么（MVP 阶段明确排除）

- ❌ 手机 App（网页响应式已够）
- ❌ WhatsApp 通道（泰国用 LINE · 不值得）
- ❌ 自动催款提醒（属于应收模块）
- ❌ 银行账户直连（属于银行对账模块）
- ❌ 多货币汇率换算（泰铢为主 · 先不做）
- ❌ OCR 自定义模板编辑器（P2 才做）

---

## 版本拆分（3 个子版本递进）

### v118.40 · MVP — 「能用」（8-10 天）
**目标**：和 Paypers 核心功能对齐 · 事务所能开始用

| 功能 | 估时 |
|---|---|
| 费用分类逻辑（15 个标准类别 · AI 自动 + 可手改）| 1.5 天 |
| 付款凭证 PV 生成（标准泰国模板 · 三签名栏）| 2 天 |
| 代收据生成（ใบแทนใบเสร็จ · 合规格式）| 1 天 |
| 月度支出仪表盘（总额/分类饼图/月对比）| 2 天 |
| 多客户费用视图（按客户筛 · 按月筛）| 1 天 |
| Google Drive 归档（按客户/月自动分文件夹）| 2 天 |
| 4 语 i18n 全覆盖 | 0.5 天 |

### v118.41 · 提升 — 「好用」（5-7 天）
**目标**：超越 Paypers · 建立差异化壁垒

| 功能 | 估时 |
|---|---|
| Google Sheets 实时同步 | 2 天 |
| Shopee/Lazada/转账单 OCR 支持 | 1.5 天 |
| ERP 直推集成（复用现有 webhook）| 1 天 |
| 批量 PV 生成（一次审核多张）| 1 天 |
| 操作审计日志 | 0.5 天 |

### v118.42 · 专业 — 「超越」（3-5 天）
**目标**：大客户 · 事务所规模化

| 功能 | 估时 |
|---|---|
| 月底批量报告（一键导出当月全部凭证包）| 1.5 天 |
| 费用预算管理（设上限 · 超额提醒）| 2 天 |
| 费用审批流（员工提交 → 会计审核 → 批准）| 2 天 |

---

## 数据模型（新增 2 张表）

```sql
-- 费用记录表（进项）
CREATE TABLE expense_records (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    client_id INTEGER REFERENCES clients(id),
    ocr_history_id INTEGER REFERENCES ocr_history(id), -- 关联原始 OCR
    expense_date DATE,
    vendor_name TEXT,
    vendor_tax_id TEXT,
    amount_pre_vat NUMERIC(12,2),
    vat_amount NUMERIC(12,2),
    wht_amount NUMERIC(12,2),          -- 预扣税
    total_amount NUMERIC(12,2),
    category TEXT,                      -- 费用分类
    category_confirmed BOOLEAN DEFAULT FALSE, -- AI 分类是否人工确认
    doc_type TEXT,                      -- invoice/receipt/slip/receipt_substitute
    payment_voucher_id INTEGER,
    drive_file_url TEXT,
    sheets_row_id TEXT,
    status TEXT DEFAULT 'pending',      -- pending/approved/rejected
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 付款凭证表
CREATE TABLE payment_vouchers (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    client_id INTEGER REFERENCES clients(id),
    pv_number TEXT UNIQUE,              -- PV-YYYY-NNNN
    period_year INTEGER,
    period_month INTEGER,
    payee_name TEXT,
    total_amount NUMERIC(12,2),
    expense_ids INTEGER[],              -- 关联的 expense_records
    status TEXT DEFAULT 'draft',        -- draft/approved/paid
    prepared_by TEXT,                   -- ผู้จัดทำ
    reviewed_by TEXT,                   -- ผู้ตรวจสอบ
    approved_by TEXT,                   -- ผู้อนุมัติ
    pdf_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP
);
```

---

## 费用分类标准（15 类 · 符合泰国会计准则）

| 代码 | 中文 | ไทย | English |
|---|---|---|---|
| `software` | 软件/订阅 | ค่าซอฟต์แวร์ | Software |
| `food` | 餐饮 | ค่าอาหาร | Food & Beverage |
| `transport` | 交通 | ค่าเดินทาง | Transportation |
| `utilities` | 水电网络 | ค่าสาธารณูปโภค | Utilities |
| `office` | 办公用品 | ค่าเครื่องใช้สำนักงาน | Office Supplies |
| `rent` | 租金 | ค่าเช่า | Rent |
| `marketing` | 营销广告 | ค่าโฆษณา | Marketing |
| `salary` | 薪资 | ค่าจ้าง | Salary |
| `insurance` | 保险 | ค่าประกัน | Insurance |
| `repair` | 维修 | ค่าซ่อม | Repair |
| `professional` | 专业服务 | ค่าบริการวิชาชีพ | Professional Service |
| `logistics` | 物流快递 | ค่าขนส่ง | Logistics |
| `tax` | 税费 | ค่าภาษี | Tax & Duties |
| `bank` | 银行手续费 | ค่าธนาคาร | Bank Charges |
| `other` | 其他 | อื่นๆ | Other |

---

## 用户故事（核心 5 条）

| 角色 | 故事 |
|---|---|
| **记账员** | 月底把30家客户的收据全丢进 Pearnly，系统自动分类 + 生成 PV，我只复核差异，**从2天压到2小时** |
| **外勤员工** | 出差拍照发 LINE，下午回办公室已经全部入账归档，**不用再收集纸质票** |
| **会计事务所老板** | 一个账号管理30家客户，每家单独出报告，月底一键打包所有客户 PV，**交付时间减半** |
| **SME 老板** | 看仪表盘知道这个月花了多少、花在哪里，导出 Excel 发给会计师，**不用自己整理 Excel** |
| **审计师** | 每张票都有操作日志，谁审核、什么时候、改了什么，**审计全程可追溯** |

---

## Paypers vs Pearnly 最终对比

| 维度 | Paypers | Pearnly 凭证中心 |
|---|---|---|
| 目标用户 | SME 老板个人 | 会计事务所（管 N 家客户）|
| 语言 | 🇹🇭 纯泰文 | 🇹🇭🇨🇳🇬🇧🇯🇵 4 语言 |
| 收票通道 | LINE + Gmail | LINE + 邮件 + 文件夹 + 云盘 + 网页 + 拍照 |
| 异常检测 | 基础 AI 核对 | 5 类规则引擎（假票/重票/税号/金额/WHT）|
| ERP 推送 | ❌ | ✅ FlowAccount/PEAK/任意 ERP |
| 批量处理 | 无异步队列 | 月底 800 张异步跑 |
| PV 模板 | 基础 | 专业三签名（符合事务所标准）|
| 进销闭环 | 纯进项 | 进项 + 销项 VAT 对账 + ภ.พ.30 |
| 审计日志 | ❌ | ✅ |
| 多页 PDF 拆分 | ❌ | ✅ |

---

## 开发启动条件

- [ ] Zihao 确认 PRD 方向
- [ ] Claude Code 读取本文件 + CLAUDE.md
- [ ] 从 v118.40 MVP 开始 · Plan mode 确认再动手
- [ ] 估时 8-10 天（v118.40）+ 5-7 天（v118.41）+ 3-5 天（v118.42）
- [ ] **总计约 3 周出完整版**

---

*文档结束 · 版本 1.0 · 2026-05-14*
