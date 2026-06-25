# doc30 · OCR→Express 完整入账闭环:商品明细 + 主档自动建档 + 读回校验

> 目标(一句话):发票/采购单上的**客户、供应商、商品明细**,Express 有就自动匹配录入,没有就自动新建后再录入;最后 **Express 里必须能读回看到完整单据 + 商品明细**,否则不算成功。
>
> 产品定位:这是**老 ERP(FoxPro/DBF·无 API)的自动入账代理**——通过逆向数据结构,做出接近高端 ERP API 的无感自动化。
>
> 状态:设计稿(2026-06-25)。承接 doc28(科目闭环)/doc29(全自动建档 v1)。**Phase 0 受控写盘测试是所有施工的硬前提门,未过不写生产代码。**

---

## 1. 现状与根因(实锤)

当前推送只完成"半张单":表头(ARTRN/APTRN)+ VAT(ISVAT)+ 总账(GLJNL/GLJNLIT 的收入/应收/税三行)+ 往来余额(ARBAL/APBAL)。**商品明细行(STCRD)一行不写**,所以 Express 的 `รายการสินค้า` 永远空。

证据(读真 DATAT,2026-06-25):
- 我们推的 `IV681220-001`:ARTRN 表头有(25000/VAT1750/合计26750),**STCRD 明细 = 0 行**。
- 真实老单 `HS580101-001`:STCRD 有 7 行油品明细;`RR580105-001`:STCRD 有 15 行。
- 小助手代码注释明确:"STCRD 本期非存货不碰"——有意砍掉的范围,非 bug。

---

## 2. 逆向取证:表与字段映射(已逐列读真 DATAT 锁定)

### 2.1 单据明细行 = `STCRD.DBF`(销项/采购共用一张表)
按 `DOCNUM` 挂单头,`SEQNUM` 是行号。真实样本字段语义:

| 字段 | 含义 | 来源 |
|---|---|---|
| DOCNUM | 单号(=ARTRN/APTRN.DOCNUM,也=GLJNL.VOUCHER) | 单头生成 |
| SEQNUM | 行号 1,2,3… | 递增 |
| STKCOD | 商品码(关联 STMAS.STKCOD) | 匹配/新建 |
| STKDES | 商品名(冗余存一份) | STMAS / OCR |
| DOCDAT | 单据日期 | 单头 |
| REFNUM | 外部参考号(采购=供应商单号;销项常空) | OCR ref_no |
| TRNQTY / TQUCOD | 数量 / 单位 | OCR items |
| UNITPR | 单价 | OCR items |
| DISC / DISCAMT | 折扣率 / 折扣额 | OCR items(可空) |
| TRNVAL | 行金额(折前) | OCR / 算 |
| NETVAL | 行净额(折后) | 算 |
| LOCCOD / DEPCOD | 仓库 / 部门 | 单头默认(样本 01 / 02·03) |
| ACCNUMDR/ACCNUMCR | 借贷科目(样本多为空,科目走 STMAS.ACCCOD) | 通常留空 |

### 2.2 商品主档 = `STMAS.DBF`(219 商品)
关键字段:

| 字段 | 含义 | 建档取值 |
|---|---|---|
| STKCOD | 商品码(可泰文可数字,如 `01ดีเซล`/`58402392`) | 新建时 `_next_code` 生成 |
| STKDES / STKDES2 | 商品名 / 副名 | OCR name |
| STKTYP | 类型(0=普通占161, 3=30, 5=22, 4=2) | 默认 '0' |
| STKGRP | 分组(OIL/04/05…) | 默认组 / 配置 |
| **ACCCOD** | **科目映射码 → ISACC → 真 GL** | 关键·见 2.4 |
| QUCOD / SQUCOD / PQUCOD | 单位 / 销售单位 / 采购单位 | OCR unit / 默认 |
| VATCOD | 税码(样本 '1') | 默认 '1' |
| ISINV / ISSAL / ISPUR | 存货控制 / 可销 / 可购 标志(本套全空) | 见 §4 风险 |
| SELLPR1..5 | 售价档 | 可空 |
| STATUS / INACTDAT | 启用状态 | 启用 |

### 2.3 单头与 GL / VAT(已有逻辑,保持)
- 销项头 `ARTRN`(DOCNUM/CUSCOD/YOUREF/TOTAL/VATAMT/NETAMT/FLGVAT/RECTYP…)
- 采购头 `APTRN`(对应)
- VAT 子账 `ISVAT`(VATREC=S 销项/P 进项·DOCNUM/REFNUM/AMT01/VAT01/TAXID/PRENAM…)
- 总账 `GLJNL`(VOUCHER=单号·JNLTYP 03销/04购)+ `GLJNLIT`(VOUCHER/SEQIT/ACCNUM/TRNTYP 0借1贷/AMOUNT)
- 往来余额 `ARBAL`/`APBAL`(按月桶)、`ISRUN`(增号)

### 2.4 科目映射 = `ACCCOD → ISACC.DBF`
STMAS.ACCCOD 不是直接 GL 号,是映射码。ISACC 把它展开到真 GL:
- 例 `ST01`(METHOD='A' 平均成本):ACCNUM01=`11-04-02-00`(存货资产)/ ACCNUM02=`51-01-00-00`(销货成本)。
- 这正是真实销售单 GL 里的成本/存货两行的来源(见 §4)。

---

## 3. OCR 数据源:已具备,唯缺商品码

逐行商品在 `ocr_history.pages[].fields.items`(前端 `merged_fields.items`),每行稳定有 **name / qty / price / subtotal**;销项采购同一套 schema(`ThaiInvoice.items`,layer2 对油品逐行专门处理)。

**唯一硬缺口:OCR 没有商品编码/SKU。** → 匹配只能按"商品名 + 单位 + 单价 + 税码 + 历史"综合,新建时由 ERP 侧生成编码。数值是字符串、空值为 `""`、热敏小票折行偶有缺值 → mapper 须容错。

---

## 4. ★账务安全:核心发现 + 风险(整个方案最硬的一块)

实测真单 GL 分录(读 GLJNLIT):

```
真实销项 HS580101-001(有 STCRD 7 行):
  借 11-01-01-00 现金/应收(含税)   1,000,204.84
  贷 41-01-00-00 销售收入(税前)      934,770.88
  贷 11-05-04-02 销项税               65,433.96
  借 51-01-00-00 销货成本(COGS)      890,156.34   ← 由 STCRD 明细驱动
  贷 11-04-02-00 存货                 890,156.34   ← 由 STCRD 明细驱动

我们推的 IV681220-001(无 STCRD):
  借 11-02-01-00 应收                 26,750
  贷 41-01-00-00 收入                 25,000
  贷 11-05-04-02 销项税               1,750
  (无成本、无存货)
```

**结论:这个账套是永续存货(平均成本法),真实销售单会自动记 COGS+存货。** 与规格里"非永续→明细只作单据行"的假设**相反**。

风险点:
1. **子账 vs 总账打架**:只写 STCRD(子账动)却不写 COGS/存货 GL(总账不动)→ 存货子账与 GL 存货科目分离,存货/利润虚高。
2. **成本数据缺失**:销项 COGS 需存货成本,OCR 只有售价没有成本 → 我们**无法自行算正确 COGS**(真单的 890,156 来自 Express 内部平均成本估值)。
3. **不能双重记 GL**:若写 STCRD 又让 Express 重算 GL,会和我们手写的 GLJNLIT 撞车。
4. **采购侧相对友好**:采购明细的 TRNVAL=进货成本=OCR 能拿到,写明细=增存货(借存货/贷应付),成本数据齐;但仍动 STMAS 余额。

→ **Phase 0 必须用受控写盘实测,确定每账套的策略**(候选:A=明细只作单据/VAT 子账行不动存货 GL;B=含 COGS/存货完整永续)。默认走能"GL 不打架"的安全策略,按账套永续/定期属性分流。**绝不在未实测前写生产代码。**

---

## 5. 闭环状态机(成功的新定义 = 读回校验通过)

```
上传 → OCR 识别(判方向+抽表头+抽明细)
  ↓
ready_to_push      OCR+前置资料齐
  ↓ 缺主档?
needs_master_data  缺客户/供应商/商品 → 系统自动建
  ↓ 歧义?
needs_review       匹配多候选/低置信 → 人工一次确认 → 回到建档
  ↓
posting            写 ERP(主档→单头→明细→VAT→GL→往来)
  ↓ 读回校验
posted_verified    单头/单号/金额/VAT/往来/总账/明细行数/逐行 全对
posted_partial     写了但明细或账务校验不全 ← 明确标注,绝不冒充成功
failed             写失败 + 明确原因
```

**铁律:明细没进去 / 读回不齐,绝不显示"完整成功"。**

---

## 6. 商品匹配引擎(确定性·分级)

输入:OCR 行(name/qty/unit/price)。候选:STMAS 全表。
**为什么必须谨慎**:实测同一名字片段在 STMAS 有 3~11 个候选(如 `PERFORMA SEMI`→11 个),瞎选=错商品/错价/错科目。

打分维度(综合,非单靠模糊名):
1. 商品名归一相似度(去声调/空格/全角·复用客户去重的 `_norm_match` 教训:别用 isalnum 删泰文声调致误并)
2. 单位一致(OCR unit vs STMAS QUCOD/SQUCOD)
3. 单价接近(OCR price vs STMAS 售价/历史成交价)
4. 税码一致(VATCOD)
5. 历史记账记忆(该供应商/客户该商品曾匹配过的 STKCOD)

判定:
- **唯一高置信** → 自动复用 STKCOD。
- **多候选 / 低置信** → `needs_review`,人工选一次(选完记忆,下次自动)。
- **零命中** → 自动建 STMAS 新商品(§7)。

---

## 7. 主档自动建档(客户/供应商/商品 统一范式)

复用现成 `master_create.ensure_customer/ensure_supplier`(ARMAS/APMAS)的 find-or-create + `_next_code` 编码自增 + 疑似重复转人工 + `_verify_row` 读回校验。

**新增 `ensure_item`(STMAS)**:
- find:按 §6 匹配引擎。
- create:写 STMAS 最小字段集(STKCOD=_next_code / STKDES=OCR name / STKTYP=0 / STKGRP=默认 / **ACCCOD=按方向取默认收入或存货映射码** / QUCOD=OCR unit 或默认 / VATCOD=1 / 启用),建前无写盘、建后 `_verify_row` 读回拿到 STKCOD 才写明细。
- 疑似重复(同名不同关键属性)→ `needs_review` 不擅自建。

**用户全程不碰 ERP**:不知道缺什么字段、不自己建客户/供应商/商品、不手工补明细。系统能自动就自动;不确定只给一个确认动作;确认后系统继续跑完建档+推送。兜底=人工确认,**不是失败后甩锅用户**。

---

## 8. 明细推送(写表顺序·销项/采购)

**销项 IV**:ARTRN(头) → STCRD(逐行·先 ensure_item) → ISVAT(销项) → GLJNL/GLJNLIT(按 Phase 0 策略·至少收入/应收/税;COGS 视策略) → ARBAL → ISRUN。
**采购 RR**:APTRN(头) → STCRD(逐行·先 ensure_item) → ISVAT(进项) → GLJNL/GLJNLIT(采购/进项税/应付;存货视策略) → APBAL → ISRUN。

全程在小助手现有**备份→写→失败回滚**事务框架内(写盘前全量备份受影响表;任一步失败整单回滚)。账套三重一致性闸保留。

---

## 9. 读回校验(成功 = 这一关全过)

写完从 Express DBF 读回逐项核对:
- 单据存在(ARTRN/APTRN by DOCNUM)、单号正确
- 金额 / VAT / 合计(对 ISVAT + 头)
- 客户 / 供应商(CUSCOD/SUPCOD → ARMAS/APMAS)
- **明细行数 = OCR 行数**(STCRD by DOCNUM 计数)
- 逐行 商品码/数量/单价/金额 一致
- 总账平(GLJNLIT 借贷相等)、往来余额已更新

任一不符 → `posted_partial` 或 `failed` + 明确原因。读回结果写进推送日志。

---

## 10. 状态/日志诚实化(对接现有云端)

- 云端 push_logs status 扩到 §5 七态;companion ack 码携带:**匹配了什么 / 新建了什么 / 写入了什么 / 读回结果**(结构化,前端不解析裸串)。
- erp-log-card / 详情抽屉:展示主档动作(匹配/新建客户·供应商·商品)+ 明细行数 + 读回核对清单。
- `posted_partial` 必须可视(不进"全部成功"桶)。

---

## 11. 分阶段施工计划

| 阶段 | 内容 | 门 |
|---|---|---|
| **P0** | 受控写盘真相测试(§4):DATAT 写带明细销项+采购,核 GL/VAT/往来/库存/COGS、Express 显示、双重记账。定账务策略。 | **Owner 关 Express+退小助手·我先备份。硬门。** |
| P1 | 云端:payload 加 items[](复刻多页合并)+ preflight 明细校验。 | P0 过 |
| P2 | 小助手:`ensure_item` 匹配+建档+读回(STMAS)。 | P0 过 |
| P3 | 小助手:写 STCRD 明细行(销项+采购)+ 按 P0 策略处理 GL/库存。 | P2 |
| P4 | 读回校验模块 + 七态状态机(云端+小助手)。 | P3 |
| P5 | UI 诚实化(状态/日志/明细行数/读回清单)+ i18n 四语。 | P4 |
| P6 | 全语料真机回归 + 验收用例(§12)逐条过。 | P5 |

---

## 12. 验收标准(逐条可测)

1. 销项 + ERP 无客户 → 自动建客户 + 推成功。
2. 采购 + ERP 无供应商 → 自动建供应商 + 推成功。
3. 销项含明细 + ERP 有商品 → 匹配并写入明细。
4. 采购含明细 + ERP 有商品 → 匹配并写入明细。
5. ERP 无商品 → 自动建商品 + 写明细。
6. 商品多候选 → 不乱选,进 `needs_review` 人工确认。
7. 推送后 Express 页面能看到商品明细。
8. 明细缺失 → 不标完整成功(`posted_partial`)。
9. 每次推送有日志:匹配/新建/写入/读回结果。
10. 账务安全:GL/VAT/应收应付/库存成本无重复、无错乱(P0 + P6 实测)。

---

## 13. 决策门(需 Owner)

1. **破整顿封锁期做此功能**:Owner 已拍板 ✅。
2. **P0 受控写盘测试授权**:需 Owner 关 Express + 退小助手(文件锁),我备份后实测。**唯一硬前提。**
3. **匹配歧义兜底**:多候选/低置信 → 人工确认(默认这么做,绝不瞎选)✅(Owner 已定)。
4. **账务策略**:依 P0 结果定(永续含 COGS vs 明细只作单据行);可能按账套属性分流。P0 后回报选型。

---

## 14. 坑/纪律(接手必读)

- DATAT 写盘:原生 Win 进程访问不了 `\\accserver`(无 SMB 认证);**bash(MSYS)能读写** `//accserver/ACCOUNT/70EXP/test`。链接键:ARTRN/APTRN/ISVAT/STCRD by DOCNUM;GLJNL/GLJNLIT by VOUCHER(=单号);ARMAS/APMAS by CUSCOD/SUPCOD;STMAS by STKCOD。源发票号在 REFNUM。
- cp874 读 STMAS 偶遇坏字节(0x99)→ 逐字段 try/except 容错;泰文输出走 UTF-8 文件别直接打终端。
- 商品名归一别用 isalnum(删泰文声调致误并·见 doc29 `_norm_match` 血泪)。
- 小助手仓在 `D:\pearnly-companion`(独立 repo·发版走 release.ps1·Owner 协调·别单独发)。
- 写盘必备份→写→失败回滚;测完还原干净基线 + 删测试残留 + verify_baseline。
- 共享树:只 add 自己文件;改监控文件净增加 RATCHET-EXEMPT。

---

## 15. P0 实测结果(2026-06-25 · Express 亲手建 IV0000004 取证)

让 Express GUI 自建一张带 3 行明细的 IV(今天日期),逐表 diff 锁死"标准答案":

- **明细落 `STCRD`**(按 DOCNUM 挂单头)。**`ARTRN.NXTSEQ` 必须 = 明细行数**——否则 Express 视作 0 行、清掉孤儿明细(这正是早先注入"消失"的根因)。
- **两种明细行**:① 真实存货码 → Express 自动记 **COGS+存货**(借 51-01/贷 11-04,成本取库存平均成本 XUNITPR);② **直接科目码**(如 42-15-00-00)→ 只贷该科目,**XUNITPR=0/XTRNVAL=0,无 COGS、不动库存**。
- **V1 采用②直接科目行**:`STCRD.STKCOD`=收入/采购科目码,`STKDES`=商品名,`POSOPR='9'`,`PEOPLE`=客户/供应商码,X 成本列全 0(= 无成本签名)。
- **账务安全验证**:直接科目行不触发 COGS/库存,GL 维持现有 收入/应收/税(销)或 采购/进项/应付(购)三/四行,与现状一致 → 账不乱、不重复记。

### ★ 仍未验证(需真机 · 见 §16)
- 直接科目行 `STKDES` 写商品名后,Express 重开会不会用"科目名"覆盖(gap #6)。
- 受控写盘期间发现 **accserver 共享中途回退到 2016 旧基线**(大文件写入被回退)——读回校验走此共享会失真,真机上线前须查清。

## 16. V1 已实现(2026-06-25 · 代码 + 单测;真机验收待定)

- **云端**(`common.extract_line_items` + sales/purchase mapper):OCR 行 → `items[]`,**对账闸**(行合计≈税前额才 `items_status=ok`,否则 empty/incomplete/mismatch 诚实退回表头)。payload 加 `items/items_status/items_account/items_line_sum`。单测 `test_express_line_items`(11)+ mapper 扩充。
- **小助手**(`dbf_schema.stcrd_detail_row` + dbf_sales/dbf_writer + 两 adapter):仅 `items_status==ok` 落 STCRD 直接科目行 + 设 `NXTSEQ`=行数;**读回校验** `_verify_detail`(行数==NXTSEQ、行合计≈税前、每行 XUNITPR/XTRNVAL=0 证明无 COGS),不符则整单回滚。销项 PEOPLE=客户码、采购=供应商码。单测:销项 23 / 采购+adapter 全绿。
- **单位映射** `unit_to_tqucod`:常见单位→2 字符码,未识别留空(不乱填无效码)。

### 待办(V1 收尾)
- **状态诚实化**:`items_status≠ok` → `posted_partial`(明细未完整不冒充成功)· companion ack 带状态 + 云端 push_logs/卡片。
- **真机验收**:§15 两项(STKDES 覆盖 + 共享回退)+ 全语料回归。
- HS/HP 现单价含税时行净额(税前)与表头(含税)显示口径差异(账正确·仅展示)——V1 接受,记此。

见 [[express-full-auto-provision-design]] [[express-account-resolution-closed-loop]] [[express-rpa-second-entry-handoff]]
