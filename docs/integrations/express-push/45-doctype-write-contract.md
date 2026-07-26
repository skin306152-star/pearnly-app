# 45 · Express 四类单据落表契约(P2-B 施工用)

> 2026-07-27 · 把 40~44 的只读逆向结论收成**可施工契约**,并逐条拿真账套镜像
> `D:\pearnly-erp-lab\_mirror_20260726`(EXP69 全 7 套 + EXP68/BANKREC)复核。
> 复核脚本(只读 `dbf.READ_ONLY` + cp874,零写入)留在本轮 scratchpad `r01_struct.py` … `r08_last.py`。
> **本页与 41~44 冲突处以本页为准** —— 冲突项在 §2 逐条列出,每条附真数据计数。

---

## 1. 四类共通硬口径(先读,四份菜谱都吃)

| 口径 | 事实 | 证据 |
|---|---|---|
| 金额列类型 | 单据/子表/余额表的钱全是 VFP `B`(double);**只有 `GLJNLIT.AMOUNT` 是 `N(13,2)`** | 逐表结构 `r01` |
| 读回比法 | `GLJNLIT.AMOUNT` 可 Decimal 严格比;其余一律 **容差 0.005**(或先 quantize 2 位) | 6902ASC `RE68L12-016` 的 `REMAMT` 实际存 `26319.219999999972`,严格比会把一张好单判失败 |
| 借贷标志 | `TRNTYP` `'0'`=借 `'1'`=贷;`AMOUNT` 恒正 | 16981 行手工分录 0 负数 |
| `SEQIT` | `C(2)` 右对齐带前导空格(`' 2'`);**是角色槽位不是行号,且不可信** | 6902ASC 17 张收款把 AR 腿塞在 `' 2'` 槽 → 认腿只能认 ACCNUM |
| 泰文分隔 | `DESCRP` 里的词间空格是 cp874 `0xA0`(NBSP)不是 `0x20` | 全库 DESCRP |
| 软删 | 判「这单还在不在 / 号被占没被占(幂等)」**只数活行**;判「这个号用没用过(发号)」**要连软删一起数** | 命中已知血泪 `dbf-soft-deleted-rows-fake-success`;6902ASC 3753 个凭证号活行/软删行并存 |
| 日期 | 列存公历;佛历只出现在 DOCNUM 字符串 | 全库 |
| 科目 | 一律从目标账套配置读(ARMAS/APMAS/ISRUN-ZR/ZP/istab55/ISINFO/ISACC),零硬编码 | 见各节 |

### 1.1 🔴 余额年槽(CY vs NY)—— 本轮最重要的新结论

`ARBAL`/`APBAL`/`GLBAL`/`STLOC` 都是「CY 十二个月 + NY 十二个月」双年桶
(`RE1..RE12` + `RE1NY..RE12NY`,`PS*`/`RR*`/`DEBIT*`/`QTY*` 同构)。
**哪一个公历年落 CY、哪一个落 NY,是逐账套的,同一个 `2569\EXP69` 目录里两种映射并存。**

三路独立证据(镜像实测,互相印证):

| 账套 | GLBAL↔GLJNLIT 反推 | ARBAL `RE` 桶实证 | APBAL `RR` 桶实证(现役采购链) |
|---|---|---|---|
| 6902ASC | **CY=2025**(1759/1759) | 2025→CY 264/265;2026→NY 29/29 | 2026→NY 319/349(CY 仅 50/349) |
| 69SINCER | **CY=2025**(1108/1108)、NY=2026(489/505) | 2025→CY 457/458;2026→NY 183/183 | 2026→NY 204/204(CY 仅 7/204) |
| 69MANAC5 | **CY=2026**(646/647) | 2026→CY 1/1 | 2026→CY 15/15 |
| 69MANACC | NY=2026(383/405)→ CY=2025 | — | — |
| 69NATA12 | NY=2026(80/92)→ CY=2025 | — | — |
| 69ASIAMI | **判不出**(GLBAL 陈旧,最高 26%) | 2026→CY 12/12 | — |
| 69ASIAR | **判不出**(最高 24%) | — | APBAL 全线对不上(最高 14/137) |

- `ISINFO` **没有财年字段**(249 列里只有 `YEARTHAI='1'`)—— 不能从配置读。
- 目录名不可信:目录叫 `2569`(BE2569=2026),但 4/7 套的 CY 是 2025。
- **现役采购/销项写入器 `apbal_month_field` / `arbal_month_field` 恒写 CY 桶、根本没有 NY 分支**
  → 对 6902ASC/69SINCER 这类 CY=2025 的账套,2026 年的单一直在写错桶。
  这是既有链路的潜在缺陷(本轮只报不改,老链路在生产跑着,改要单独拍板)。

**新单契约**:写余额桶前必须先解出该账套的 `cy_year`——
按 GLBAL↔GLJNLIT 对账(某年命中率 ≥90% 即定案),解不出(69ASIAMI/69ASIAR 那种 GLBAL 陈旧)
→ **不写余额桶 + 明确告知会计"余额报表需在 Express 里重算一次"**,不许猜。

### 1.2 🔴 合成表规格与真表的漂移(必须补齐的列)

`bridge/writepath/table_specs.py` 的 `TABLE_SPECS` 与真表逐列比对,缺口如下。
上一轮 `APBAL` 只造 `RR1..RR12` 没造 `HP*`,导致"现购记错桶"在合成栈上永远测不出来;
下面这批缺口是**同一类盲区**,不补齐则新单的桶/库存签名缺陷同样测不出来。

| 表 | 真表列数 | 合成规格现状 | **必须补齐** |
|---|---|---|---|
| `APBAL` | 122 | `SUPCOD` + `RR1..12` + `HP1..12`(25 列) | `BEGBAL`;`RR/HP` 的 `*1NY..*12NY`;整组 `CP1..12(+NY)`、`GR1..12(+NY)`、**`PS1..12(+NY)`** |
| `ARBAL` | 122 | `CUSCOD` + `IV1..12` + `HS1..12`(25 列) | `BEGBAL`;`IV/HS` 的 `*NY`;整组 `DR1..12(+NY)`、`SR1..12(+NY)`、**`RE1..12(+NY)`** |
| `STCRD` | 45 | 24 列 | **`MLOTNUM C(24)`、`LOTBAL B`、`LOTVAL B`、`LUNITPR B`**(⚠️ `dbf_schema.stcrd_no_stock_impact` 正是查这 4 列,合成表没有它们 → `try/except` 静默跳过 → 该闸在合成栈上**恒真**,等于没测);`RDOCNUM C(15)`、`REFNUM C(15)`、`FLAG C(1)`、`FREE C(1)`、`VATCOD C(1)`、`SLMCOD C(10)`、`RETSTK C(1)`、`BALCHG B`、`VALCHG B`、`PSTKCOD C(20)`、`ACCNUMDR C(15)`、`ACCNUMCR C(15)`、`PACKING C(15)`、`JOBCOD C(6)`、`PHASE C(4)`、`COSCOD C(4)`、`REIMBURSE C(1)` |
| `APTRN` | 58 | 29 列 | `CHQPAY B`、`INTPAY B`、`RCVAMT B`、`TAX B`、`AMTRAT0 B`、`ADVNUM C(12)`、`ADVAMT B`、`CHQPAS B`、`POSTGL C(1)`、`BILLBE C(10)`、`VATLATE C(1)`、`VATTYP C(1)` |
| `ARTRN` | 60 | 29 列 | `CHQRCV B`、`INTRCV B`、`CHQPAS B`、`TAX B`、`TAXRAT N(5,2)`、`TAXCOND C(1)`、`BEFTAX B`、`AMTRAT0 B`、`ADVNUM C(12)`、`ADVAMT B`、`COMAMT B`、`POSTGL C(1)`、`SLMCOD C(10)`、`VATLATE C(1)` |
| `APMAS` | 36 | 17 列 | `BALANCE B`、`CHQPAY B`、`TAXDES C(25)`、`TAXRAT N(5,2)`、`TAXTYP C(4)`、`TAXCOND C(1)` |
| `ARMAS` | 39 | 16 列 | `BALANCE B`、`CHQRCV B`、`TAXRAT N(5,2)`、`TAXCOND C(1)` |
| `ISVAT` | 24 | 13 列 | `VATTYP C(1)`、`LATE C(1)`、`NEWNUM C(10)`、`DEPCOD C(4)`、`AMT02 B`、`VAT02 B`、`AMTRAT0 B`、`REMARK C(30)`、`SELF_ADDED C(1)`、`HAD_MODIFY C(1)`、`ORGNUM N(5,0)` |
| `ISRUN` | 41 | 4 列 | `DOCCOD C(2)`、`SHORTNAM C(6)`、`POSDES C(30)`、`JNLEXP C(60)`、`ACCNUM01..12 C(15)` |
| `ISACC` | 14 | 10 列 | 真表只有 `ACCNUM01..06`(合成写了 01..03,别照抄 12) |
| `GLJNL` | 22 | 7 列 | **`SRCJNL C(4)`**(手工凭证判别式)、`BATCH C(6)`、`REFNUM C(12)`、`REVERSE C(1)`、`CREDAT D`、`USERID C(8)`、`CHGDAT D` |
| **整表缺失** | — | — | `ARRCPIT`、`ARRCPCQ`、`APRCPIT`、`APRCPCQ`、`ISTAX`、`BKTRN`、`BKMAS`、`STTRN`、`STLOC`、`GLBAL`、`ISINFO` |

---

## 2. 与 41~44 的冲突项(以本页为准)

| # | 出处 | 原结论 | 真数据复核 | 契约取值 |
|---|---|---|---|---|
| X1 | 44 §4 `D6` | `NET>0 → 借存货/贷对方;NET<0 → 反之` | OU/ZZ 出库行 `TRNVAL` **存正数**,193/193 张真单是 **借 `ACCNUMDR`(费用)/ 贷 存货**;按 D6 写会完全写反 | 方向由**单头 `POSOPR`** 定:`6`→借对方/贷存货;`8`/`5` 才看 `sign(NET)` |
| X2 | 44 §4 `A9` | `MLOTNUM[:8] == DOCDAT` 全行成立 | 出库行 MLOTNUM 指**来源批**:69SINCER 6/98、69ASIAMI 0/74、69ASIAR 0/50 | A9 只对**增加行**(`POSOPR='1'`)成立 |
| X3 | 42 §4 `A2` | `NETAMT == Σ APRCPCQ + TAX` 1633/1633 | 435/2761 张付款单**根本没有 APRCPCQ 行**(69SINCER 327/627、69ASIAR 71/227、69ASIAMI 25/112);有 cq 行时 6902ASC 1621/1621、69SINCER 229/300 | A2 改成**条件断言**:有 cq 行才验 |
| X4 | 42 §4 `A5` | `AMTRAT0 == NETAMT − TOTAL − VATAMT`,新写按公式写 | 语义逐账套不同:6902ASC `==NETAMT` 1366 / 公式 183;69SINCER `==0` 565/627;69ASIAR `==0` 203/227;**69MANAC5 `==0` 162/162** | **写 `0`**,不按公式派生;FX 账套(6902ASC 式)单列并 escalate |
| X5 | 42 §2 | APBAL `PS{月}` 累加,"2025 年 930/931" | 6902ASC 2025→CY 仅 635/931;**69ASIAR 全线失败(最高 14/137)**;6902ASC 288 个供应商有重复 APBAL 档 | v1 **不写 APBAL**,写完提示会计重算(见 §1.1) |
| X6 | 42 §5 | 预扣科目 `istab(55, TAXTYP).SHORTNAM` 1633/1633 | `SHORTNAM` 只有 6902ASC 填了;**69SINCER / 69ASIAMI / TEST 全空**;69SINCER 3 张预扣单全靠 `ISINFO.ACCNUM09` 命中 | 取值链 `istab55.SHORTNAM → ISINFO.ACCNUM09 → ISRUN(ZP, 前缀 TS/TA).ACCNUM01 → escalate` |
| X7 | 43 §3 | ISRUN GL 行提供前缀 | GL 行的 **`JNLTYP` 列是空的**,本账代码在 **`DOCCOD`** 列 | 读 `DOCCOD` 不读 `JNLTYP` |
| X8 | 41 §4 `C3` | 违反 2/1077 | 严格 Decimal 比得 6/1077;4 例是 double 表示误差(`REMAMT=26319.219999999972`),真反例只有 2 张无明细挂账收款 | C3 带 0.005 容差 |

---

## 3. 逐类落表契约

四类的完整字段/取号/分录/桶/读回/载荷/风险,见本轮交付的结构化契约(与本页 §1/§2 同源)。
下面只留每类的**一句话骨架 + 各自的 P0 闸**,细则不在本页重复:

| 单据 | 骨架 | P0 闸 |
|---|---|---|
| 收款 `ar_receipt` | ARTRN(1)+ARRCPIT(n)+ARRCPCQ(0..n)+GLJNL(1)+GLJNLIT(2..n)+BKTRN(0..n)+ISVAT(0..1);反写被冲 ARTRN;ARBAL `RE` 桶;ISRUN `RE` 计数器 | 反写发票的 `RCVAMT/REMAMT/CMPLAPP/CMPLDAT` 必须进同一备份回滚集;`FLGVAT='2'` v1 拒收 |
| 付款 `ap_payment` | APTRN(1)+APRCPIT(n)+APRCPCQ(0..n)+ISTAX(0..2)+ISVAT(0..n)+BKTRN(0..n)+GLJNL(1)+GLJNLIT(2..9);反写被结清 APTRN;APBAL `PS` 桶(v1 不写);ISRUN `PS` | 分配额 `≤` 票面 `REMAMT` 先读后写再读回;预扣科目取不到就拒写 |
| 手工凭证 `gl_journal` | GLJNL(1)+GLJNLIT(≥2)[+ISVAT];**其余表一张不碰** | `SRCJNL='GL  '` 常量;凭证号活行唯一;写后反向闸验 APTRN/ARTRN/APBAL/ARBAL/STTRN/ISRUN 行数与 mtime 未变 |
| 库存调整 `stock_adjust`(OU/ZZ) | STTRN(1)+STCRD(n)+GLJNL(1)+GLJNLIT(**恒 2**)+STMAS;ISRUN 对应前缀 | `ISINFO.ISPERPETUA≠'Y'` → 只写库存不写 GL;`MLOTNUM` 必须指真实来源批 |
