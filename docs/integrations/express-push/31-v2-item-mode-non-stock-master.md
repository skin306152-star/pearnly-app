# V2 · 三层 item_mode + 非库存主档默认闭环

> 状态:方案锁定(2026-06-25)。V1(direct_account)已上线 prod / companion 1.1.12。
> 本文 = V2 施工纲。基于 \\accserver\ACCOUNT 真账套只读取证,非臆造。

## 1. 背景与决策

V1 把明细当"直接科目行"(STCRD.STKCOD=账码,X 字段=0)写,能看到明细、不动库存,
最安全但不是 Express 原生主流用法。V2 改成**三层 item_mode**,默认走 Express 原生的
**非库存商品主档**,把"商品明细"与"库存成本"解耦:

- `direct_account`:STCRD.STKCOD=收入/费用账码。最安全,V1 已实现,保留为兜底。
- `non_stock_item`:**默认**。匹配/新建 STKTYP=3/4/5 非库存主档,STCRD 引用其 STKCOD。
  有商品主档 → "有就匹配、没有就建";不动库存、不产生 COGS。
- `stock_item`:真实进销存。STKTYP=0,扣库存、算成本、产 COGS、批次。**开关后才走**。

**硬约束**:默认绝不新建 STKTYP=0;stock_item 必须显式开关 + 确认客户真用 Express 管库存
+ 校验采购成本/库存余额/批次。单据允许混合行(库存行走 stock,运费/服务/杂项走非库存)。

## 2. 取证事实(DATAT 真账套,只读)

STMAS 219 主档:STKTYP=0 库存 161、**3/4/5 非库存共 54**、空 4。非库存原生大量在用。

非库存主档关键字段(模板):
- `STKCOD` 标识码(可是账码样式 `53-03-06-00`,也可是名字 `ค่าเช่า`)
- `STKDES/STKDES2` 泰文品名
- **`ACCCOD` = GL 联动键**(`0015`/`003K`/`0018`…,经 ISACC 映射真实科目)
- `QUCOD` 单位 · `VATCOD` 税码 · `STKGRP` 分组 · `ISSAL/ISPUR` 销/购标志
- 库存字段 TOTBAL/OPNBAL/TOTVAL… 全 0

非库存 STCRD 明细行(HP580101-001 / HP580108-004 实据):
- `STKCOD` = 主档码(引用主档)
- **`LOTBAL/LOTVAL/LUNITPR/MLOTNUM/MREMBAL/MREMVAL/PHYBAL` = 0** ← 真·无库存签名
- `XTRNVAL/XSALVAL` = 净额(ex-VAT),**非零**(与 V1 direct_account 的 X=0 不同)
- `ACCNUMDR/ACCNUMCR` 借贷科目字段存在

## 3. 设计

### 3.1 行级 item_mode 解析(云端 mapper)
每行 OCR item 解析 mode:
- 显式 stock 开关 ON 且行可判定为库存品 → `stock_item`
- 运费/服务/杂项关键词 或 不确定 → `non_stock_item`(默认)
- 主档/科目解析全失败的极端兜底 → `direct_account`

payload 每行带 `item_mode` + `account`(科目)+ `name/qty/price/amount`。
对账闸(line_sum≈base)沿用 V1,不通过整单回落 header-only。

### 3.2 ensure_item(companion · 匹配或新建非库存主档)
1. 归一品名(复用泰文归一·去声调符·trim)。
2. 匹配:STMAS 中 STKTYP∈{3,4,5} 且 STKDES 归一==目标 → 复用其 STKCOD。
3. 无匹配 → 新建非库存主档:**★禁硬编码字段**。从**同账套**一条真实非库存主档(STKTYP∈{3,4,5})
   **克隆**结构字段(STKTYP/ISSAL/ISPUR/STKGRP/QUCOD/CQUCOD/CFACTOR/VATCOD/STKLEV/NEGALLOW… 全照模板),
   仅覆写本单据特有项:
   - `STKDES/STKDES2`=品名 · `STKCOD`=生成唯一码 · 审计 CREBY/CREDAT/USERID/CHGDAT
   - `ACCCOD` = ISACC 解析(销项→收入科目 / 采购→采购或费用科目)得到的短码(见
     [[express-account-resolution-closed-loop]]·每账套不同必按账套读 ISINFO/ISACC)
   - ★取证修正:`ISSAL/ISPUR` 是字符字段·DATAT+63/59/61EXP 全部非库存主档均为**空**——
     非销/购准入开关,空着照样在单据用。故克隆任一同账套非库存主档结构即可,
     ISSAL/ISPUR 照模板(留空),不按方向筛模板,方向只体现在 ACCCOD 解析。
4. 防呆:疑似重复主档守卫(复用 S4 dedup·泰文归一去声调符);
   **新建失败 → 该行回落 direct_account 且记 mode+reason(不静默)**,不阻断整单。

### 3.3 写 STCRD(companion)
非库存行:`STKCOD`=主档码 · **LOT 全字段(LOTBAL/LOTVAL/LUNITPR/MLOTNUM/MREMBAL/MREMVAL/PHYBAL)=0**
(真·无库存签名)· `XTRNVAL/XSALVAL`=净额(非零·按 Express 原生) · `STKDES`=品名。
NXTSEQ=明细行数。`ACCNUMDR/ACCNUMCR` 留空(实证 HP580101-001 真账非库存行就空)。
★GL 联动取证:STCRD 行不带借贷科目,**真账由 GLJNLIT 决定·companion 显式写**(V1 已正确写
收入/应收/销项税)。主档 `ACCCOD→ISACC.ACCNUM01` 只供 Express 自身报表派生,**账务正确性
不依赖主档**——故建档 ACCCOD 解析失败也不毁账(GL 仍对),最坏 Express 报表归类不准,可回落
direct_account。非库存行不产 COGS/库存贷方。
ISACC:`ACCCOD→ACCNUM01`(点号账码)·METHOD='A' 为库存型(ACCNUM01=库存/ACCNUM02=COGS)。
ISINFO(账套配置 1 行)给角色默认科目:ACCNUM11=收入 / 07=应付 / 02=应收 / 10=销项税…。

### 3.4 ★ 索引闭环(requirement #4/#5 · 承重)
DBF 写完 ≠ 成功。Express 界面/报表靠 CDX 索引导航,新写行不重建索引看不见。
- **用 Express 原生 Reindex(非 PACK)**:`8.อื่นๆ`(Others)菜单 → Reindex → 选销项/采购系统
  (重建 ARTRN/APTRN/ISVAT/STCRD 的 CDX)→ F5 确认 → 等完成。实证 help eng/202、284:
  Reindex 只重建索引、不删记录不重整,远轻于 PACK。
- **后台/批触发**:`reindex_runner`(仿 pack_runner·驱动 Express GUI·账套硬闸同款)。
  录完一批空闲时跑一次 Reindex(非每单)。**PACK 退回夜间/周期,绝不当每单默认动作**。
- **Reindex 仍需 Express 独占**(launch→login→reindex→close)·有人用则 EXIT_OCCUPIED 跳过下轮重试。

### 3.5 ★ 状态模型(requirement #2/#3/#6 · 失败不显示成功)
单据/行级状态,UI/日志诚实:
- `posted`:DBF 写入 + Reindex + 读回校验(页面/DBF/CDX/GL)全过 = 唯一的"成功"。
- `pending_review`(待确认):**金额对账失败(line_sum≠base)→ 不 header-only、不冒充成功**,转人工确认。
- `posted_fallback_direct`:某行主档建/配失败,回落 direct_account 成功写入 → 带 reason(非静默)。
- `failed`:写入/Reindex/校验任一不过 → 明确失败 + 码。
行级 `item_mode` + `mode_reason` 落库,供前端 chip 展示"为什么这行走了兜底"。

### 3.6 stock_item(V2-b · 开关后)
STKTYP=0 主档 + LOT/成本/批次 + COGS 分录。独立施工,本期不做,仅留接口位。
**前置闸**:显式开关 + 确认客户真用 Express 管库存 + 校验采购成本/库存余额/批次,缺一不开。

## 4. 验收标准(每条都要真机过 · 失败不显示成功)
- ERP 页面真机看到完整商品明细(行数=OCR 行数)。
- ARTRN/APTRN.NXTSEQ == STCRD 行数 == OCR 行数(三者一致)。
- 非库存行 LOT 字段全 0,不产生库存影响 · 不产生 COGS。
- 库存行(若启用)产生正确库存/成本/批次。
- GL Dr/Cr 平、不重复、不漏税(税额对)。
- **索引闭环**:Reindex 后页面/DBF/CDX/GL 四者一致才标 posted。
- 对账失败 → pending_review(不冒充成功);兜底 → 带 reason。

## 5. 施工分期
- **V2-a**(本期·完整闭环非 easy path):
  ① 同账套模板克隆建非库存主档(ensure_item)② 非库存 STCRD 写盘 ③ 混合行路由
  ④ direct_account 兜底带状态/原因 ⑤ 对账失败→待确认 ⑥ **reindex_runner 索引闭环**
  ⑦ 读回四验(页面/DBF/CDX/GL)。真 DATAT E2E + Reindex + 用户真机看明细 → 上线。
- **V2-b**(后续):stock_item 开关 + 进销存/成本/批次校验。
