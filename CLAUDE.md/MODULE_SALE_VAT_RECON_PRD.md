# Pearnly · MODULE_SALE_VAT_RECON_PRD.md

> **模块归属**:对账中心(`reconcile`)→ 第一个子模块上线
> **业务名称**:销项税对账(Output VAT Reconciliation)· การกระทบยอดภาษีขาย
> **来源**:Korn(高级会计师)PDF SOP + Excel PROMT 工作表 + UI 草稿迭代 · BAKELAB 真实样本验证
> **目标用户**:泰国注册 VAT 经营者(VAT-registered entity)的代理记账事务所
> **最后更新**:2026-05-12

---

## 1. 模块定位

| 项 | 内容 |
|---|---|
| 中文 | 销项税对账 |
| ไทย | การกระทบยอดใบกำกับภาษีขายกับรายงานภาษีขาย |
| English | Output VAT Reconciliation against Sale VAT Report |
| 简称 | VAT 对账 |
| 所属一级模块 | 对账中心(`reconcile`) |
| 模块路由 | `reconcile/sale-vat` |
| 优先级 | P1(月度刚需 · 排在 v118.30 浏览器扩展之前) |
| 估时 | 14-18 天(分 5 个子版本递进) |

### 1.1 与原路线图的承接关系

一级模块「对账中心」(`reconcile`)早在 `MODULE_ROADMAP.md` 第 9 个一级模块占位 · 实现度 0% · 原规划重点是「ภ.พ.30 / ภงด.3 PDF 一键生成 + 银行流水 vs 发票自动匹配」(L5 报表层导出)。

Korn 老师的 PDF SOP 让我们看到比"生成报告"更早一步的刚需:**客户系统里的 VAT 报告本身需要被逐行核对**(L3 对账层)。本模块作为「对账中心」的第一个真正子模块上线 · 填补这层缺口。

完成后承接关系:**销项税对账(L3 · 本模块)→ ภ.พ.30 PDF 一键生成(L5 · 原路线图规划)** —— 对账后数据干净 · 报告生成水到渠成。
---

## 2. 业务背景与法规依据

### 2.1 法规框架

依据《泰国税收法典》(ประมวลรัษฎากร · Revenue Code)第 86-90 条 · 所有 VAT 注册经营者(ผู้ประกอบการจดทะเบียน)月度义务:

1. **编制销售税报告**(จัดทำรายงานภาษีขาย · Output VAT Report)· 汇总当月所有已开具的税务发票(ใบกำกับภาษี · Tax Invoice)
2. **提交 ภ.พ.30**(Monthly VAT Return Form)· 截止次月第 15 个工作日(网上申报延至第 23 日)
3. **保存税务发票正副本**(Tax Invoice Copy)· 至少 5 年

报告中的销项税总额(ภาษีขายรวม · Total Output VAT)必须 = 当月所有税务发票销项税额之和。**差额需在备注栏说明 · 否则触发税局(กรมสรรพากร · Revenue Department)核查(ตรวจสอบ)**,最严重情形可处发票金额 1-2 倍滞纳金(เบี้ยปรับ · Penalty)+ 月息 1.5% 利息(เงินเพิ่ม · Surcharge)。

### 2.2 事务所角色

代理记账事务所(สำนักงานบัญชี · Accounting Firm)对客户(经营者)的报告准确性负**连带审核责任**(Joint review liability)。月末标准 SOP:

| 步骤 | 当前耗时 | 痛点 |
|---|---|---|
| 收集客户当月所有税务发票副本 | 0.5 天 | 邮件/纸质/LINE 多渠道混杂 |
| 收集客户 ERP/POS 系统导出的销售税报告 | 0.5 天 | 格式多样 · 多份分散 |
| 逐张发票与报告行项目核对(9 字段) | **2-4 小时/客户** | 人工肉眼 · 易漏 · 易疲劳 |
| 异常项追溯并发邮件让客户更正 | 0.5-1 天 | 来回邮件耗时 |
| 出具《销项税审计报告》交客户 | 0.5 天 | 手工排版 |

事务所平均同时服务 20-100 家客户 · 每月底固定 3-5 天专做销项税对账 · 是事务所**最大的人时黑洞**。

### 2.3 Pearnly 介入点

Pearnly 已具备:
- 多渠道发票自动归档(邮件/Drive/LINE/文件夹)
- 多语言 OCR(泰中日英)· 9 字段已自动提取
- 异常栏自动识别假票/重票/算错/税号无效
- MR.ERP 推送(销售税报告导出格式已通)

**唯一缺口**:把"已归档发票" ↔ "客户 VAT 报告" 两边的逐行核对自动化。本模块填补此缺口。

---

## 3. 用户故事

| 角色 | 故事 |
|---|---|
| 事务所记账员(บัญชีของสำนักงาน) | 我把客户给的销售税报告拖进 Pearnly · 系统自动跟当月已归档的税务发票逐行核对 · 我**只复核差异行**,不浪费时间在合格的 95% 上 |
| 事务所所长(หัวหน้าสำนักงาน) | 月底我把 30 个客户的混合文件全丢进 Pearnly · 系统自动按 (税号, 纳税期间) 分组建任务 · 我**一次确认全部启动**,不再 30 次重复建任务 |
| 复核师(ผู้ตรวจสอบ) | 在差异行我看到 AI 解释「日期晚 1 天 · 可能客户录入手误」+ 一键起草客户邮件按钮 · **1 分钟搞定一行** |
| 申报员(ผู้ยื่นแบบ) | 我导出的对账报告 Excel 跟 Korn 老师传统模板 100% 一致 · 客户老板拿到不需要重新学读法 |
| 事务所合伙人 | 对账结果跟 MR.ERP 直推闭环 · **对账完成的发票自动入账**,不再有"对完了忘记推 ERP"的脱节 |

---

## 4. 数据模型

### 4.1 实体表(新增 3 张)

```sql
-- 对账任务表
CREATE TABLE reconciliation_task (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER,
    client_id INTEGER REFERENCES clients(id),
    period_year INTEGER,                    -- 西历年(如 2026)
    period_month INTEGER,                   -- 1-12
    vat_report_id INTEGER REFERENCES vat_report(id),
    invoice_count_archived INTEGER,         -- 期间内已归档发票数
    invoice_count_supplement INTEGER,       -- 补传发票数
    report_row_count INTEGER,               -- 报告行数
    status TEXT,                            -- created/running/completed/failed
    matched_count INTEGER,
    mismatched_count INTEGER,
    invoice_orphan_count INTEGER,           -- 发票侧孤儿
    report_orphan_count INTEGER,            -- 报告侧孤儿
    confidence_score REAL,                  -- 整体配对置信度
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 对账明细行表
CREATE TABLE reconciliation_row (
    id INTEGER PRIMARY KEY,
    task_id INTEGER REFERENCES reconciliation_task(id),
    invoice_id INTEGER REFERENCES ocr_history(id),  -- NULL = 报告孤儿
    report_row_no INTEGER,                          -- NULL = 发票孤儿
    pair_confidence REAL,                           -- 配对置信度 0-1
    status TEXT,                                    -- matched/mismatched/invoice_orphan/report_orphan
    diff_fields JSON,                               -- {date: {invoice:"01/03/2026", report:"02/03/2569", delta:"+1d"}}
    diff_categories TEXT,                           -- date_diff,invoice_no_prefix,vat_precision (逗号分隔)
    ai_analysis TEXT,                               -- 一句话原因解释
    accountant_action TEXT,                         -- pending/resolved/customer_issue/accepted_diff
    notes TEXT,
    updated_at TIMESTAMP
);

-- VAT 报告表(原始 + 解析后结构化)
CREATE TABLE vat_report (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER,
    client_id INTEGER,
    period_year INTEGER,
    period_month INTEGER,
    issuer_tax_id TEXT,                     -- 报告发布主体的 13 位税号
    issuer_name TEXT,
    issuer_branch TEXT,                     -- 总部 = '00000' / 分支 = 5 位编码
    source_file_ids TEXT,                   -- JSON 数组 · 支持多文件多页合并
    parsed_rows JSON,                       -- 解析出的 N 行数据
    total_amount_pre_vat REAL,
    total_vat REAL,
    total_amount REAL,
    parser_version TEXT,                    -- 解析器版本(模板自学习)
    created_at TIMESTAMP
);
```

### 4.2 九个对账字段(严格遵循 Korn PDF SOP)

| # | 中文 | 泰文 | English | 类型 | 容差规则 | 备注 |
|---|---|---|---|---|---|---|
| 1 | 税务发票字样 | คำว่า "ใบกำกับภาษี" | "Tax Invoice" wording | bool | 严格 | **发票自检** · 不参与双边对比 |
| 2.1 | 卖方名称 | ชื่อผู้ขาย | Vendor name | string | 严格 + 模糊 ≥95% | 发票自检 |
| 2.2 | 卖方地址 | ที่อยู่ผู้ขาย | Vendor address | string | 严格 | 发票自检 |
| 2.3 | 卖方税号 | เลขประจำตัวผู้เสียภาษีผู้ขาย | Vendor TIN | string(13) | 严格 + Mod-11 校验 | 发票自检 |
| 2.4 | 卖方分支 | สาขาที่ออกใบกำกับ | Vendor branch | string(5) | 总部 ↔ "00000" ↔ "สำนักงานใหญ่" 视为同 | 发票自检 |
| 3 | 文件日期 | วันที่เอกสาร | Document date | date | ±0 天(可放宽到 ±1) | 佛历↔西历自动转换(-543) |
| 4 | 文件编号 | เลขที่เอกสาร | Document number | string | 容前缀差(INV vs IV)/ 空格 / 大小写 | 标准化算法 |
| 5 | 买方名称 | ชื่อผู้ซื้อ | Buyer name | string | 模糊匹配 ≥ 95% | Levenshtein 距离 |
| 6 | 买方税号 | เลขประจำตัวผู้เสียภาษีผู้ซื้อ | Buyer TIN | string(13) | 严格 + Mod-11 校验 | 个人买家可为空 |
| 7 | 买方分支 | สาขาผู้ซื้อ | Buyer branch | string(5) | 同 2.4 | 个人买家跳过 |
| 8 | 不含税金额 | ยอดก่อน VAT (มูลค่าสินค้าหรือบริการก่อน VAT) | Net amount(pre-VAT base) | decimal(2) | ±0.01 | |
| 9 | 销项税额 7% | จำนวนภาษีมูลค่าเพิ่ม | Output VAT (7%) | decimal(2) | ±0.01 | 含计算精度容忍 |

---

## 5. 核心算法

### 5.1 三轮配对算法(Three-pass Matching)

```
第一轮 · 主键配对(Primary Key Match)
  └─ 标准化 invoice_no(去前缀差 / 去空格 / 统一大小写)
  └─ 命中 → pair_confidence = 1.0

第二轮 · 复合键配对(Composite Key Match)· 第一轮未命中的
  └─ (date, buyer_tax_id, total) 三键完全一致
  └─ 命中 → pair_confidence = 0.95

第三轮 · 模糊配对(Fuzzy Match)· 前两轮未命中的
  └─ (date ±1, buyer_name Levenshtein ≥ 90%, total)
  └─ 命中 → pair_confidence = 0.75 · 需人工二次确认

未配上 → 标记为孤儿(orphan)
```

### 5.2 字段级对比

每对配对成功的行 · 逐字段调用 `compare_field(field_name, invoice_value, report_value)` · 返回 `{matched: bool, delta: str, category: str}`。

字符串字段先做标准化:
- 去首尾空格 / 全角半角统一
- 大小写折叠(case folding)
- 佛历日期统一转西历(年份 -543)
- 税号去连字符(0-1255-59013-48-9 → 0125559013489)

### 5.3 差异自动归类(Diff Categorization)

| Category | 触发条件 | UI 颜色 |
|---|---|---|
| `date_diff` | 字段 3 不一致(差 1-7 天) | warning |
| `date_period_mismatch` | 跨纳税期间(超出本月) | danger |
| `invoice_no_prefix` | 字段 4 仅前缀差(INV vs IV) | warning(可一键忽略) |
| `name_fuzzy` | 字段 5 模糊匹配 < 100% 但 ≥ 95% | info |
| `tax_id_mismatch` | 字段 6 不一致 | danger |
| `branch_mismatch` | 字段 7 不一致 | warning |
| `amount_diff` | 字段 8 差异 > 0.01 | danger |
| `vat_precision` | 字段 9 差异 ≤ 0.10(7% 计算精度) | info(自动接受) |
| `vat_calc_wrong` | VAT ≠ 7% × 净额(误差超 1 บาท) | danger |
| `invoice_orphan` | 发票存在 · 报告无 | danger |
| `report_orphan` | 报告有行 · 发票库无 | danger |

### 5.4 AI 分析层

每个 mismatched 行喂给 LLM(已有 Gemini 集成):
```
输入:diff_fields + 客户历史相似案例 + 法规上下文
输出:
  - 一句话原因推断("报告日期晚发票 1 天 · 可能客户录入时手误")
  - 建议操作(更正报告 / 接受差异 / 让客户重开发票)
  - 起草邮件草稿(已有 LLM 邮件模板可复用)
```

---

## 6. 用户旅程(User Journey)

### 6.1 入口位置

```
主导航
└─ 对账中心(原占位)
   ├─ 销项税对账(本模块 · v118.32 上线)
   ├─ 进项税对账(Input VAT · v118.34 · 跟随同样模式)
   └─ 银行对账(原自动化下迁移 · v118.35)
```

### 6.2 三屏流程

**屏 A · 单客户对账创建页**(80% 日常场景)
- 选客户(含色块头像)+ 纳税期间
- 系统立即显示该期间已归档发票数 · 总销售额 · 数据源分布
- 拖拽虚线区上传 VAT 报告(支持 .xlsx / .xls / .pdf · 也支持从邮件附件直接抓)
- 可选折叠区:补传未归档发票
- 点"开始对账" → 跳屏 C

**屏 B · 批量智能识别确认页**(月底场景)
- 单一大拖拽区"丢入本月所有要对账的文件"(发票/报告/混合)
- 上传完成 → 系统自动 OCR 分类 + 按 (issuer_tax_id, period) 分组
- 显示识别结果:
  - 顶部 4 统计卡(上传文件 / 识别为发票 / 识别为报告 / 无法识别)
  - 列表:每个对账任务 1 行(客户色块 · 期间 · 发票数 + 报告页数 · 置信度徽章)
  - 低置信度行警告 + "查看明细"按钮支持手动调整
- 勾选 N 个任务 → "全部启动对账"

**屏 C · 对账结果详情页**
- 顶部 4 KPI(总数 / 完全匹配 / 字段差异 / 单边孤儿)+ 匹配率进度条
- 差异类型 chip 筛选(全部 / 已匹配 / 日期差 / VAT 精度差 / 单边孤儿 …)
- 列表 · 颜色编码每行状态 · 点击展开看字段级 diff
- 展开后:左右双栏对比 · 差异字段红底高亮 · 旁标 `差 +1 天` / `少前缀 N`
- 底部 AI 分析卡 + 三个动作按钮(起草邮件 / 标记问题 / 接受差异)
- 顶部右上角:导出 PDF · 导出 Excel · 提交客户 · 推送 MR.ERP

---

## 7. Excel 导出规范

### 7.1 列结构(严格遵循 Korn 模板克隆 · 铁律候选)

固定 20 列 + N 个 / 标记列:

| 段 | 列 | 字段 |
|---|---|---|
| **发票侧** | 1 | ลำดับ(序号) |
| | 2 | วันที่ |
| | 3 | เลขที่ใบกำกับ |
| | 4 | ชื่อผู้ซื้อ |
| | 5 | เลขประจำตัวผู้เสียภาษี |
| | 6 | สาขาผู้ซื้อ |
| | 7 | ยอดก่อน VAT |
| | 8 | ภาษี 7% |
| | 9 | ยอดรวม |
| | 10 | หมวดหมู่ |
| | 11 | แหล่งที่มา |
| **标记栏** | 12-20 | 9 个 `/` 核对栏(逐字段) |
| **报告侧** | 21 | วันที่(报告) |
| | 22 | เลขที่(报告) |
| | 23 | ชื่อ(报告) |
| | 24 | เลขภาษี(报告) |
| | 25 | สาขา(报告) |
| | 26 | ยอดก่อน VAT(报告) |
| | 27 | ภาษี 7%(报告) |
| **备注** | 28 | หมายเหตุ(差异说明) |

### 7.2 一发票多差异行展开

UI 上为 1 行可折叠 · 导出 Excel 时按 Korn 样本传统拆为 N 行(每差异一行 · 同发票号重复):
- 第一行:第一个差异(如"ชื่อผู้ซื้อไม่ถูกต้อง"),9 个 `/` 全打,หมายเหตุ 写第一项问题
- 第二行:第二个差异(如"สาขาผู้ซื้อไม่ถูกต้อง"),9 个 `/` 全打,หมายเหตุ 写第二项

### 7.3 标记栏语义

每一项都打 `/` 表示"已核对过"(*Reviewed*)· 实际差异写在 `หมายเหตุ` 备注列。这是泰国会计师传统读法 · **不可改为 ✓/✗ 双值**(会破坏老会计师阅读习惯)。

### 7.4 底部签字栏

固定输出三栏:
```
ผู้จัดทำ: ____________    ผู้ตรวจสอบ: ____________    ผู้อนุมัติ: ____________
(制作人)              (审核人)              (批准人)
```

### 7.5 表头与尾部

固定输出 6 行表头(参考 Korn 样本):
```
ชื่อผู้ประกอบการ(经营者名称)
ที่อยู่สถานประกอบการ(经营场所地址)
เลขประจำตัวผู้เสียภาษี(纳税人识别号) · 13 位
สาขา(分支) · 总部/分支 X
เดือน ปี งวดภาษี(纳税期间) · เช่น 03/2569
รายงานภาษีขาย(标题:销售税报告)
```

尾部输出 `รวมยอดทั้งสิ้น`(总计行)· 含 净额合计 + 销项税合计 + 总额合计。

---

## 8. 边界场景与处理(Edge Cases)

| 场景 | 业务定义 | 处理逻辑 |
|---|---|---|
| 个人买家(บุคคลธรรมดา) | 买方为自然人 · 无税号 · 无分支 | 字段 6、7 跳过 · 不算差异 |
| 同税号多分支 | 同一法人有总部 + 多分支 · 各自开票 | 必须 (税号, 分支码) 联合配对 · 仅按税号配对会错位 |
| 已废止发票(ใบกำกับยกเลิก) | 客户开错后作废重开 | 报告侧标 "ยกเลิก" · 对账时跳过且单列 |
| 跨期发票(Cross-period invoice) | 本期开具 · 客户报告归下月 | 标 `cross_period_orphan` · 不强制对账 · 提示会计判定 |
| 多页报告合并 | 大客户报告分 N 页 PDF 或 N 个 Excel sheet | 同 (issuer_tax_id, period) 自动归并为 1 份逻辑报告 |
| 报告侧多买家合并行(罕见) | 单行汇总多买家 · 非标准格式 | 标"复合行" · 强制人工拆分 |
| OCR 失败的发票 | 提取置信度过低 | 走异常栏现有规则引擎 · 不进对账 |
| 重复发票号 | 客户系统真实错误 · 同号开 2 次 | 标 `duplicate_invoice_no` · 单列警告 |
| VAT = 0 的零税率发票 | 出口销售(ส่งออก)· 国际服务 | 标 `zero_rated` · 字段 9 跳过对比 |
| 含税开票(VAT-inclusive) | 总额已含税 · 反算 net | 系统自动反算:net = total / 1.07 |

---

## 9. 集成接口

### 9.1 与现有 Pearnly 管道复用

| 现有能力 | 复用方式 |
|---|---|
| OCR 管道(`ocr_history` 表) | 直接 query by (client_id, period) 拉发票 |
| 异常栏(`exceptions` 表) | 发票自检失败的项目自动进异常栏 |
| 客户表(`clients` 表) | 任务关联 client_id |
| LINE Bot 通道 | 对账完成推老板 LINE |
| MR.ERP webhook | 对账完成的发票批量推 ERP(铁律 59 Korn 模板克隆) |

### 9.2 新增 API 端点

```
POST /api/recon/task                  创建对账任务
POST /api/recon/upload_report         上传 VAT 报告 → 返回 parsed_rows
POST /api/recon/intake_bulk           批量智能识别入口(屏 B)
POST /api/recon/run/{task_id}         触发对账执行
GET  /api/recon/result/{task_id}      拉取结果
POST /api/recon/row/{row_id}/action   单行复核动作
POST /api/recon/draft_email/{row_id}  AI 起草客户邮件
GET  /api/recon/export/{task_id}.xlsx 导出 Excel(Korn 模板克隆)
GET  /api/recon/export/{task_id}.pdf  导出 PDF
POST /api/recon/push_erp/{task_id}    推 MR.ERP
```

### 9.3 VAT Report 解析器(新增子组件)

```python
class VATReportParser:
    """支持 .xlsx / .xls / .pdf 三种输入 · 输出标准化 JSON"""
    
    def parse(file) -> ParsedReport:
        format = detect_format(file)
        if format == 'xlsx': return XlsxParser().parse(file)
        if format == 'pdf':  return PdfTableParser().parse(file)
        raise UnsupportedFormat
    
    # PDF 表格识别走 PaddleOCR + 表格结构识别
    # Excel 用 openpyxl + 模板自学习(记住每个客户首列偏移 / 列序)
```

---

## 10. 验收标准(Acceptance Criteria)

| 指标 | 目标值 | 测试方法 |
|---|---|---|
| 单客户 33 张发票对账总耗时 | < 10 秒 | BAKELAB 2026/03 样本 |
| 300 张发票 + 多报告批量识别 | < 60 秒 · 准确率 > 95% | 模拟数据集 |
| 9 字段对比准确率 | 100%(已知样本) | Korn 提供样本 + 人工 100 行抽样 |
| Excel 导出与传统模板一致度 | 像素级(单元格位置/字体/边框) | Korn 验收 + 截图比对 |
| 用户操作步骤(单任务) | ≤ 3 次点击 | UX 录屏 |
| 用户操作步骤(批量) | ≤ 5 次点击 | UX 录屏 |
| 4 语 UI 同步覆盖 | 中泰英日 100% data-i18n | i18n lint check_i18n.py |
| 个人买家(无税号) | 字段 6/7 不报差异 | 单元测试 |
| 佛历日期 | 自动 -543 转西历 · 反向显示按用户语言 | 单元测试 |
| 多页报告合并 | 同 (税号, 期间) PDF/Excel 自动并 1 份 | 集成测试 |

---

## 11. 优先级 + 估时(版本分解)

总估时 **14-18 天** · 排在 v118.30 浏览器扩展之前(月度刚需 > nice-to-have)。

| 版本 | 主题 | 内容 | 估时 |
|---|---|---|---|
| **v118.32.0** | 数据底座 + 单客户对账核心 | 3 张表 schema · API 骨架 · 9 字段对比引擎 · 屏 A UI | 4 d |
| **v118.32.1** | 结果详情页 · AI 分析 | 屏 C UI · 双栏 diff · 差异分类筛选 · AI 接 Gemini · 起草邮件 | 3 d |
| **v118.32.2** | Excel 导出 · Korn 模板克隆 | xlsx 模板克隆(参考铁律 59 MR.ERP 经验)· 多差异行展开 · 签字栏 | 2 d |
| **v118.33.0** | 批量智能识别 | 屏 B UI · OCR 分类引擎 · 自动分组 · 置信度系统 · 多页合并 | 4 d |
| **v118.33.1** | 边界场景 · 异常栏联动 · 验收 | 个人买家 / 同税号多分支 / 跨期 / 零税率 · 接异常栏 · Korn 验收测试 | 2 d |

---

## 12. 对标分析与差异化

| 产品 | 他们的销项税对账 | Pearnly 差距 / 超越 |
|---|---|---|
| **Xero · VAT Return** | 仅按 Xero 自家发票汇总成报告 · 不接外部 ERP 报告 | **超** — Pearnly 跨 ERP / 跨账本 · 不强制客户用某一家系统 |
| **QuickBooks · Sales Tax** | 同 Xero · 封闭系统内 | **超** — 同上 |
| **FlowAccount · รายงานภาษีขาย** | 生成报告但不做对账 · 假设客户全用 FlowAccount 开票 | **超** — Pearnly 适配任意客户 ERP/POS 导出的报告 |
| **用友 T+ · 销项税核算** | 中国增值税逻辑 · 不适配泰国佛历/13 位税号/Mod-11 校验 | **超** — 泰国本土化深度 |
| **Excel + VLOOKUP** | 会计常用 · 但手工搬数据 + 易抄错 | **超** — 自动 OCR + AI 分析 + 模糊匹配 |
| **CodaPro · Tax Reconciliation** | 泰国本土 SaaS · 仅做手工导入 + 简单 diff | **追平 + 超** — 我们走自动 OCR + 智能识别批量场景 |

---

## 13. Pearnly 护城河(本模块新增)

1. **跨 ERP 中立**(Cross-ERP neutrality)— 客户用任何 ERP/POS 都能对账 · 这是封闭 SaaS(Xero/QB)永远做不到的
2. **OCR 自动归档 + 自动对账闭环** — 月初到月末零人工干预 · 别人是"手动导出 + 手动对账"
3. **泰国本土合规深度** — 佛历转换 / Mod-11 税号校验 / ภ.พ.30 流程 / 总部分支编码 · QB/Xero 不接
4. **多语言 UI**(中泰英日)+ **多语言 OCR**(泰中日) — 中资/日资客户在泰国必备
5. **AI 解释 + 一键邮件** — 用户改完字段后异常自动消失 · 改完一键发邮件让客户更正 · QB 只告诉你"有差异",不告诉你"为什么"

---

## 14. 风险与缓解

| 风险 | 概率 | 影响 | 缓解策略 |
|---|---|---|---|
| VAT 报告格式多样(各 ERP 不同) | 高 | 解析失败 | 渐进式:先支持 BAKELAB + Korn 模板 + 常见 4 家 ERP(FlowAccount / Express / Business Plus / MR.ERP) · 其他走"模板自学习"(用户首次手动映射列序,系统记住) |
| 模糊匹配错配 | 中 | 误报差异 / 漏报真问题 | 置信度 < 95% 强制弹"人工确认"模态 · 不直接走完 |
| 多差异行展开导致 Excel 行数膨胀 | 中 | 客户读不顺 | 提供"折叠视图(每发票 1 行)" + "展开视图(每差异 1 行)" 两种导出模式 |
| 跨期发票边界 | 中 | 漏对账 | 强制标记 `cross_period_orphan` · 给会计选择是否本期入对账 |
| Mod-11 税号校验过严 | 低 | 误拦合法税号 | 提供"放宽校验"开关 · 用户可关 |
| 客户报告里含中性税(零税率/免税) | 中 | 字段 9 误报差异 | 按发票类型(`zero_rated` / `tax_exempt` / `taxable`)分类对比 |

---

## 15. 铁律候选(本模块沉淀)

> 上线后写入 `CORE_PEARNLY_PLAN.md` 铁律列表

- **铁律候选 60** · VAT 对账 Excel 输出永远用 Korn 模板克隆 · 不许 openpyxl 直接 save(沿用铁律 59 MR.ERP 经验)
- **铁律候选 61** · 个人买家(无 tax_id)对账时字段 6/7 必须跳过 · 否则全部个人买家发票误报"分支不一致"
- **铁律候选 62** · 佛历日期统一 -543 转西历存库 · UI 显示按用户语言切换(泰语显示佛历 · 其他显示西历)
- **铁律候选 63** · 配对置信度 < 0.95 强制人工确认 · 不允许系统自动判定
- **铁律候选 64** · 跨纳税期间(超出本月 ±0 天)的孤儿单据 · 一律标 `cross_period` 不参与本期对账 · 不可自动接受

---

## 16. 上线后跟踪指标

| 指标 | 监控频率 | 目标值 |
|---|---|---|
| 对账任务月活客户 | 每月 | 上线后第 3 月 ≥ 当前 OCR 用户的 50% |
| 单任务平均耗时 | 每周 | < 30 秒(从拖文件到看到结果) |
| 配对一次命中率(第一轮主键) | 每周 | > 80% |
| Korn 模板导出错配次数 | 每周 | = 0(任何错配立即 hotfix) |
| AI 解释采纳率(用户点"接受 AI 建议"比例) | 每月 | > 60% |
| 起草邮件按钮使用率 | 每月 | > 30% 的差异行 |

---

## 附录 A · 泰国 VAT 申报关键术语对照表

| 中文 | ไทย | English | 缩写 |
|---|---|---|---|
| 增值税 | ภาษีมูลค่าเพิ่ม | Value Added Tax | VAT |
| 销项税 | ภาษีขาย | Output VAT | OV |
| 进项税 | ภาษีซื้อ | Input VAT | IV |
| 税务发票 | ใบกำกับภาษี | Tax Invoice | TI |
| 销售税报告 | รายงานภาษีขาย | Output VAT Report | OVR |
| 采购税报告 | รายงานภาษีซื้อ | Input VAT Report | IVR |
| 月度 VAT 申报表 | แบบแสดงรายการภาษีมูลค่าเพิ่ม | Monthly VAT Return | ภ.พ.30 |
| 纳税人识别号 | เลขประจำตัวผู้เสียภาษีอากร | Taxpayer Identification Number | TIN |
| 纳税期间 | งวดภาษี | Tax Period | — |
| 滞纳金 | เบี้ยปรับ | Penalty | — |
| 利息 | เงินเพิ่ม | Surcharge | — |
| 经营者 | ผู้ประกอบการ | VAT-registered entity | — |
| 总部 | สำนักงานใหญ่ | Head Office | HO |
| 分支机构 | สาขา | Branch | — |
| 零税率 | ภาษีศูนย์ | Zero-rated | — |
| 免税 | ยกเว้นภาษี | Tax-exempt | — |
| 税局 | กรมสรรพากร | Revenue Department | RD |
| 法定查账 | การตรวจสอบ | Audit | — |
| 已废止发票 | ใบกำกับยกเลิก | Voided invoice | — |
| 反算净额 | คำนวณกลับ ฐานภาษี | Reverse-calculate net | — |