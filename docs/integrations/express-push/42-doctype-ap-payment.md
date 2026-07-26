# 42 · Express 供应商付款单(จ่ายชำระหนี้ / AP Payment)只读逆向

> 逆向日期 2026-07-26 · **只读逆向产物**:全程 `dbf.Table(..., codepage='cp874')` + `dbf.READ_ONLY`,
> 零写入 / 零 pack / 零删除。结论全部来自真账套样本。
> 脚本与 DBF 只读副本留在逆向窗口 scratchpad:
> `C:\Users\skin3\AppData\Local\Temp\claude\C--Users-skin3-Desktop-pearnly-app\0a2cac22-1395-44cb-909d-b50e60da19d4\scratchpad\doctype_recon\`
> `appay_01_schema.py` … `appay_23_test_set.py`,代表单完整转储在 `appay_samples.txt`,DBF 副本在 `data/6902ASC/`。
> 核心两个:`appay_21_assertions.py`(配平断言表,可直接当验收闸)、`appay_04_dump.py`(跨表单据转储)。

**结论先行:找到了,样本充足(5 个生产账套共 2761 张活单),结构已完整逆向并用 22 条机械断言在 1633 张真单上验过。**
判别键 = **`APTRN.RECTYP = '9'`**(不是靠 DOCNUM 前缀 `PS`——前缀可配置,`69MANAC5/69MANACC` 的 ISRUN 里就有第二本 `PT`)。

---

## 1. 样本盘点

| 账套 | RECTYP=9 物理/活行 | 带预扣税 | 日期跨度 | 单号形态 | ISRUN 计数器 |
|---|---|---|---|---|---|
| 6902ASC(生产大账套) | 1648 / **1633** | 679 | 2018-04-10 → 2026-05-29 | `PS69T05-041`(PREFIX+佛历YY+`T`+MM+`-`+序号) | `0000073` |
| 69SINCER | 627 / **627** | 3 | 2016-10-12 → 2026-06-17 | `PS690529-003`(PREFIX+佛历YYMMDD+`-`序号),另有 2 张 `PS0000027` | `0000034` |
| 69ASIAR | 227 / **227** | 0 | 2025-11-01 → 2026-06-25 | `PS690624-001` | `0000055` |
| 69MANAC5 | 165 / **162** | 0 | 2026-01-01 → 2026-03-31 | `PS690101-001` | `0000031`(两行:PS / PT) |
| 69ASIAMI | 112 / **112** | 13 | 2025-11-05 → 2026-06-16 | `PS681105-001`,另有 `PS0000046` | `0000047` |
| 69MANACC | 0 / 0 | — | — | — | `0000030`(PS/PT) |
| 69NATA12 | 0 / 0 | — | — | — | `0000006` |
| **TEST**(`\\Accserver\d$\ACCOUNT\69EXP\test`) | **0 / 0** | — | — | — | `0000001` |

子表规模(6902ASC):`APRCPIT` 6498/6131、`APRCPCQ` 5885/3480、`ISTAX` 861/835。

**5 张代表单**(完整字段在 `appay_samples.txt`):

**① `PS69T05-002` — 最典型:一票一现金流 + 个人供应商预扣 3%**

```
APTRN   RECTYP=9 DOCNUM=PS69T05-002 DOCDAT=2026-05-15 SUPCOD=SKC BILLBE=SKC1 BILNUM=~
        NETAMT=9200.00 CHQPAY=8924.00 TAX=276.00 RCVAMT=9200.00 PAYAMT=9200.00 REMAMT=0
        AMTRAT0=9200.00 TOTAL=0 VATAMT=0 CMPLAPP=Y DOCSTAT=N USERID=BIT9
APRCPIT RCPNUM=PS69T05-002 DOCNUM=RN202604-054 RECTYP=3 PAYAMT=9200.00 VATAMT=0
APRCPCQ RCPNUM=PS69T05-002 CHQNUM=QP69T05-002 PAYAMT=8924.00
ISTAX   REFNUM=TAXNUM=PS69T05-002 TAXPRD=2026-05-01 PEOPLE=SKC1 PRENAM=นาย
        NAME=พรศักดิ์ เซี่ยงฉิน TAXID=3730200740936 TAXDES=ค่าจ้างทำของ
        AMOUNT=9200.00 TAXRAT=3.00 TAXAMT=276.00 TAXTYP=S03 TAXCOND=1
BKTRN   BKTRNTYP=QP CHQNUM=QP69T05-002 CUSCOD=SKC AMOUNT=NETAMT=8924.00
        CHQSTAT=05 BNKACC=S2 JNLTRNTYP=1 VOUCHER=PS69T05-002 REFDOC=~
GLJNL   JNLTYP=01 VOUCHER=PS69T05-002 VOUDAT=2026-05-15 TRNSTAT=P DOCSTAT=N
        DESCRP=ชำระหนี้ให้   นาย พรศักดิ์ เซี่ยงฉิน
GLJNLIT SEQIT=2 Dr 2120-01  9200.00     ← 应付(取自 APMAS.ACCNUM)
        SEQIT=5 Cr 2120-06  8924.00     ← 支票待付(ZP/01 前缀 QP)
        SEQIT=7 Cr 2132-02   276.00     ← 预扣税 ภ.ง.ด.3(个人 → S03)
```

**② `PS68T01-003` — 服务票:预扣 + 「付款时才认列进项税」 + 银行手续费 + 预付冲抵**

```
APTRN   REFNUM=RE25-01-0093 VATPRD=2025-01-01 VATDAT=2024-12-31 FLGVAT=2
        TOTAL=37712.86 VATAMT=2639.90 NETVAL=37712.86 NETAMT=40352.76
        CHQPAY=39221.37 TAX=1131.39 CHQPAS=39221.37 DOCSTAT=M
APRCPIT RN671231-04 RECTYP=3 PAYAMT=40352.76 VATAMT=2639.90
APRCPCQ QP68T01-003 +39134.36 | Q2PS68T01-00 +87.01 | Q4PS68T01-00 −12.00 | TTPS68T01-00 +12.00
ISTAX   TAXTYP=S53 TAXDES=ค่าบริการ AMOUNT=37712.86 TAXRAT=3 TAXAMT=1131.39
ISVAT   VATREC=P RECTYP=9 DOCNUM=PS68T01-003 REFNUM=RE25-01-0093 AMT01=37712.86 VAT01=2639.90
GLJNLIT SEQIT=2 Dr 2120-01 40352.76 | SEQIT=5 Dr 5360-04 12.00 | SEQIT=5 Cr 1113-02 12.00
        SEQIT=5 Cr 1151-07 87.01 | SEQIT=5 Cr 2120-06 39134.36 | SEQIT=6 Cr 2132-03 1131.39
        SEQIT=8 Dr 1155-02 2639.90 | SEQIT=9 Cr 1155-01 2639.90
```

**③ `PS68T02-029` — 采购退货/贷项冲抵(付款额 ≠ 明细面额之和)**

```
APTRN   NETAMT=9760.64 CHQPAY=9760.64 TAX=0
APRCPIT GR450/22466 RECTYP=5 PAYAMT=24289.17   ← 退货,记 −
        RR451/22549 RECTYP=3 PAYAMT=34049.81   ← 赊购,记 +
        34049.81 − 24289.17 = 9760.64 = NETAMT ✔
GLJNLIT SEQIT=2 Dr 2120-01 9760.64 | SEQIT=5 Cr 2120-06 9760.64
```

**④ `PS68L01-001` — 预付款冲抵 + 汇兑损益(净额为负)**

```
APTRN   ADVNUM=AE68L01-007 ADVAMT=1533032.06 NETAMT=−26480.54 CHQPAY=−26480.54
APRCPIT RR445/22221 RECTYP=3 +736646.21 | RR451/22522 RECTYP=3 +769905.31
        AE68L01-007 RECTYP=0 1533032.06(记 −)  → 合计 −26480.54 = NETAMT ✔
APRCPCQ E4PS68L01-00 PAYAMT=−26480.54(ZP 前缀 E4 → 4200-24 汇兑损益)
GLJNLIT SEQIT=2 Dr 2120-02 1506551.52 | SEQIT=5 Dr 4200-24 26480.54 | SEQIT=7 Cr 1151-01 1533032.06
        (无 BKTRN:没有支票行)
```

**⑤ `PS69T05-041` — 49 张进项票一次付 + 预付冲抵 + 预扣**:`NETAMT=1405823.72`、`TAX=7571.58`、
`ADVNUM=AO69T04-002 ADVAMT=264038.34`,`APRCPIT` 49 行(48 张 RN RECTYP=3 + 1 张 AO RECTYP=0),
`GLJNLIT` 5 行(应付借 / 支票贷 / 预扣贷 / 预付贷)。最大一张 `PS69T01-080` 挂 80 张票。

---

## 2. 落表清单(一张付款单一次写这些)

**新增行**

| 表 | 行数 | 字段 | 值来源 |
|---|---|---|---|
| **APTRN** | 1(单头) | `RECTYP` | 常量 `'9'` |
| | | `DOCNUM` | 取号(见 §3) |
| | | `DOCDAT` / `DUEDAT` | 付款日(公历,两者实测恒等) |
| | | `SUPCOD` | 供应商码(APMAS 主键) |
| | | `BILLBE` | 实际收款/开预扣凭证对象,默认空;非空时预扣凭证抬头用它 |
| | | `REFNUM` | 仅服务票认列进项税时=供应商开的税票号;否则空 |
| | | `BILNUM` | 常量 `'~'`(1633/1633,哨兵值,非空字符串) |
| | | `NETAMT` / `RCVAMT` / `PAYAMT` | 三者=本次结清净额(见 §4 A1/A2/A4) |
| | | `TAX` | 本次预扣税合计 |
| | | `CSHPAY`/`CHQPAY`/`INTPAY` | 现金/支票·转账/其他,三者和 = `NETAMT − TAX` |
| | | `TOTAL` / `NETVAL` / `VATAMT` | 付款时认列进项税的税基/税基/税额;无则 0 |
| | | `AMTRAT0` | `NETAMT − TOTAL − VATAMT` |
| | | `ADVNUM` / `ADVAMT` | 冲抵的预付单号与金额(可空) |
| | | `VATPRD`/`VATDAT`/`FLGVAT` | 有认列进项税时:税期首日 / 税票日 / `'2'` |
| | | `REMAMT` | 常量 `0`(1633/1633) |
| | | `CMPLAPP` | 常量 `'Y'`;`DOCSTAT`='N';`SRV_VATTYP`/`PVATPRORAT`='-' |
| | | `USERID`/`CHGDAT` | 操作者 / 落库日 |
| **APRCPIT** | 每张被结清单据 1 行 | `RCPNUM` | =付款单号 |
| | | `DOCNUM` | 被结清单据号(RR/RN 赊购、GR 退货、AE/AO 预付、CP) |
| | | `RECTYP` | **被结清单据自己的 RECTYP**(3/4 计正、5/0 计负) |
| | | `PAYAMT` | 本次分配到该单的金额(部分付款=部分额) |
| | | `VATAMT` | 该单随付款认列的进项税额 |
| **APRCPCQ** | 每条收付/扣减方式 1 行 | `RCPNUM` | =付款单号 |
| | | `CHQNUM` | 支票行(ZP/01,前缀 QP)= `前缀+DOCNUM[2:]`,多张支票追加 `A/B/C…`;其余行 = `(前缀+DOCNUM)[:12]` |
| | | `PAYAMT` | **正=贷记该科目(付出去)/负=借记该科目(手续费、汇兑损)** |
| **ISTAX** | 预扣时 1(极少 2) | `REFNUM`/`TAXNUM` | 均=付款单号(806/835);`REFDAT`/`TAXDAT`=DOCDAT |
| | | `TAXPRD` | DOCDAT 所在月 1 号(685/685) |
| | | `PEOPLE` | `BILLBE` 非空取它,否则 `SUPCOD`(679/685) |
| | | `PRENAM`/`NAME`/`ADDR`/`TAXID` | APMAS 该 payee 档(TAXID 685/685 一致) |
| | | `TAXDES`/`TAXRAT`/`TAXTYP`/`TAXCOND` | APMAS 默认(可被操作员改),TAXTYP∈{S03 个人,S53 法人} |
| | | `AMOUNT` / `TAXAMT` | 税基 / `round(AMOUNT×TAXRAT/100, 2)`(685/685) |
| **ISVAT** | 付款认列进项税时 n 行 | `VATREC`/`RECTYP` | 常量 `'P'` / `'9'`(1633/1633) |
| | | `DOCNUM` | =付款单号;`REFNUM`=供应商税票号 |
| | | `VATPRD`/`VATDAT`/`DOCDAT` | 税期首日 / 税票日 / 付款日 |
| | | `AMT01`/`VAT01` | 税基 / 税额;`TAXID`/`PRENAM`/`DESCRP` 取 APMAS |
| **BKTRN** | 每张支票 1 行(1549/1549 恰好对上支票行) | `BKTRNTYP` | =ZP 前缀(`QP`) |
| | | `CHQNUM` | =APRCPCQ 的 CHQNUM;`VOUCHER`=付款单号;`REFDOC`=`'~'` |
| | | `TRNDAT`/`CHQDAT`/`GETDAT` | 付款日(GETDAT 1549/1549) |
| | | `CUSCOD`/`NAME` | 供应商码/名(1549/1549) |
| | | `AMOUNT`=`NETAMT` | 该支票金额;`CHARGE`=0 |
| | | `BNKACC` | 支票所属银行户(BKMAS.BNKACC) |
| | | `CHQSTAT` | `'05'`=已开未过账(istab TABTYP=02:05=เช็คจ่าย,10=เช็คผ่าน) |
| | | `JNLTRNTYP` | 常量 `'1'`;`CMPLAPP`='Y' |
| **GLJNL** | 1 | `JNLTYP` | =ISRUN(DOCTYP='PS').JNLTYP,实测 `'01'` 付款日记账(= ISINFO.APRCPJNL) |
| | | `VOUCHER`/`VOUDAT` | =DOCNUM / =DOCDAT(1630/1630) |
| | | `DESCRP` | 按 ISRUN.JNLEXP 求值:`'ชำระหนี้ให้   ' + APMAS.PRENAM + NBSP(0xA0) + APMAS.SUPNAM` |
| | | `TRNSTAT`/`DOCSTAT` | 常量 `'P'` / `'N'`;`BATCH`/`REFNUM`/`SRCJNL` 留空 |
| **GLJNLIT** | 2~9 行 | `SEQIT` | **固定槽位**:`2`=应付借、`5`=收付/扣减行、`6`=预扣 ภ.ง.ด.53、`7`=预扣 ภ.ง.ด.3 与预付冲抵、`8`=进项税借、`9`=待认列进项税贷 |
| | | `ACCNUM` | 槽 2 = **APMAS.ACCNUM**(逐供应商,1630/1630);槽 5 = ISRUN(DOCTYP='ZP',按 CHQNUM 前缀).ACCNUM01;槽 6/7 预扣 = `istab(TABTYP='55', TYPCOD=TAXTYP).SHORTNAM`(1633/1633),回落 ISINFO.ACCNUM09;槽 7 预付 = 预付单的 ZP 科目(1151-01/1151-07);槽 8/9 = ISINFO.ACCNUM06 / ACCNUM28 |
| | | `TRNTYP` | `'0'`=借 `'1'`=贷 |
| | | `AMOUNT` | 见 §4;`DESCRP` 同 GLJNL.DESCRP;`VOUDAT`=DOCDAT |

**就地改行(这是本单据类型最危险的部分——前面做过的采购/销售单全是纯 append)**

| 表 | 改什么 | 规则(实测通过率) |
|---|---|---|
| **APTRN(被结清的那些票)** | `PAYAMT` 累加本次分配额;`REMAMT = NETAMT − PAYAMT`(5952/5952);`CMPLAPP` 结清后置 `'Y'`(5947/5952);`CMPLDAT` 置结清日 | 部分付款实证:`RN660829-08` NETAMT 40,446,000 / PAYAMT 38,835,514.25 / REMAMT 1,610,485.75 / CMPLAPP='N',由 `PS68T01-001`+`PS68T10-111` 两次付 |
| **APBAL** | 该供应商 `PS{月}` 桶累加 = **(赊购票 − 退货票)之和**(非 NETAMT):2025 年 930/931、2026 年 314/316 | ⚠️ **第一年用 `PS1..PS12`,第二年用 `PS1NY..PS12NY`**;288 个供应商有多行 APBAL(重复档),写错行就双计 |
| **APMAS** | `BALANCE` = 该供应商未结清 REMAMT 之和(693/717);`CHQPAY` = 未过账支票(BKTRN.CHQSTAT='05')之和(699/717) | 两个都是缓存字段 |
| **ISRUN** | 用默认流水号时把 `DOCNUM` 计数器 +1 | 实证 69ASIAMI 存在 `PS0000046` 且计数器停在 `0000047` |
| **GLBAL** | 按科目×月的借贷合计缓存(`DEBIT{m}` / `CREDIT{m}` / `*LY` / `*NY`,键=ACCNUM+DEPCOD+JOBCOD,3245 行) | Express 自己维护;不更新则试算表/科目余额落后 |

---

## 3. 取号规则

- 注册行:`ISRUN` 里 `DOCTYP='PS'`,`SHORTNAM` 空,`DOCCOD` 空,`POSDES='จ่ายชำระหนี้'`,`JNLTYP='01'`,
  `PREFIX='PS'`,`DOCNUM` = 7 位下一号,`ACCNUM01..12` **全空**(不像别的类型带默认科目)。
  ⚠️ **同一 DOCTYP 可能有多行**(多本账簿):`69MANAC5` / `69MANACC` 各有 `PS` 和 `PT` 两行。选行必须按前缀,不能 `first()`。
- **默认号** = `PREFIX + ISRUN.DOCNUM`(7 位),例 `PS0000046`;取号后把 `ISRUN.DOCNUM` 加一回写。
- **真实账套几乎都手改成日期式**,两种方言:
  - `PREFIX + 佛历YY + MMDD + '-' + 序号` → `PS690624-001`(69SINCER/69ASIAR/69MANAC5/69ASIAMI,共 1123/1128 张)
  - `PREFIX + 佛历YY + 'T' + MM + '-' + 序号` → `PS69T05-041`(6902ASC 1631/1633,月内序号从 001 起)

  佛历年 = 公历 + 543 取末两位(`2026 → 69`)。
- 字段宽 12 字符;佛历只出现在号码字符串里,`DOCDAT` 存公历。
- **取号后不回写别的地方**:`GLJNL.VOUCHER`、`BKTRN.VOUCHER`、`ISTAX.REFNUM/TAXNUM`、`APRCPIT.RCPNUM`、
  `APRCPCQ.CHQNUM`(前缀+号)、`ISVAT.DOCNUM` 全部直接引用这个号 —— **单号 = 全套联表的唯一外键**,一处写错整单散架。
- 支票号 `APRCPCQ.CHQNUM` 不是银行真实支票号,是 `ZP前缀 + 单号`;多张支票加 `A/B/C…` 后缀。
  **非支票行(手续费/汇兑/转账)用 `(前缀+单号)[:12]` 会被截断,不同单撞号 266 次 —— 别拿 CHQNUM 当唯一键。**

---

## 4. 配平校验(可机械执行,`appay_21_assertions.py` 直接跑)

在 6902ASC 1633 张单上的实测通过率(记号:`Σit`=APRCPIT,`Σcq`=APRCPCQ,`sign(RECTYP)`: 3/4→+1,5/0→−1):

| # | 断言 | 通过 |
|---|---|---|
| A1 | `NETAMT == Σ sign(it.RECTYP) × it.PAYAMT` | **1633/1633** |
| A2 | `NETAMT == Σ cq.PAYAMT + TAX` | **1633/1633** |
| A3 | `CSHPAY + CHQPAY + INTPAY == NETAMT − TAX` | **1633/1633** |
| A4 | `RCVAMT == NETAMT` | **1633/1633** |
| A6 | `NETVAL == TOTAL` | **1633/1633** |
| A7 | `REMAMT == 0`(付款单头) | **1633/1633** |
| A17 | `ISTAX.TAXAMT == round(AMOUNT × TAXRAT / 100, 2)` | **1633/1633** |
| A18 | 预扣 GL 科目 `== istab(55, TAXTYP).SHORTNAM` | **1633/1633** |
| A22 | `ISVAT.VATREC=='P' and RECTYP=='9'` | **1633/1633** |
| A8 | `Σ GLJNLIT 借 == Σ 贷` | 1630/1633(3 张无 GL:1 张 2018 遗留 + 2 张零收付行) |
| A9/A10 | 恰好 1 个 GLJNL 头 且 `VOUDAT==DOCDAT` | 1630/1633(同上 3 张) |
| A11 | `SEQIT=2` 借方科目 `==APMAS.ACCNUM` 且金额 `== Σ(赊购) − Σ(退货)` | 1630/1633 |
| A14/A15/A16 | 预扣贷方合计 == `TAX`;`ISTAX` 存在 ⟺ `TAX≠0`;`Σ TAXAMT(+2) == TAX` | 1632/1633(仅 2018 遗留单) |
| A19/A20/A21 | `ISVAT` 存在 ⟺ `VATAMT≠0`;`Σ VAT01 == VATAMT`;`Σ AMT01 == TOTAL` | 1625 / 1627 / 1621(差额=人工在 VAT 报表里手改过的行,`HAD_MODIFY='Y'`/`SELF_ADDED='Y'`) |
| A12/A13 | `SEQIT=5` 行数 == APRCPCQ 行数、方向随 `sign(PAYAMT)` | 1582/1633 —— **不是缺陷:GL 侧按科目合并**(5 张支票 → 一条 2120-06 贷),50/50 全是同前缀重复 |
| A5 | `AMTRAT0 == NETAMT − TOTAL − VATAMT` | 1546/1633 —— 失败的 87 张里 69 张 `AMTRAT0 == PAYAMT`,且 86 张 `PAYAMT ≠ NETAMT`:**这两个字段在被反复编辑的旧单上会累加变脏**,新写按公式写即可(干净单 1476/1546 满足 `PAYAMT==NETAMT`) |

写单侧的等价「必须成立」清单:

```
NETAMT = Σ sign×APRCPIT.PAYAMT = Σ APRCPCQ.PAYAMT + TAX = RCVAMT = PAYAMT
CSHPAY + CHQPAY + INTPAY = NETAMT − TAX ;  REMAMT = 0 ;  AMTRAT0 = NETAMT − TOTAL − VATAMT
Σ GLJNLIT(TRNTYP='0').AMOUNT = Σ GLJNLIT(TRNTYP='1').AMOUNT
GL: Dr APMAS.ACCNUM (Σ赊购−Σ退货) + Dr|Cr 各 ZP 科目(按 PAYAMT 符号,按科目合并)
    + Cr 预扣科目 TAX + Cr 预付科目 Σ预付 + [Dr 进项税 VATAMT / Cr 待认列进项税 VATAMT]
∀被结清票: 票.PAYAMT(新) = 票.PAYAMT(旧) + 本次分配额 ; 票.REMAMT = 票.NETAMT − 票.PAYAMT
           票.CMPLAPP = 'Y' ⟺ 票.REMAMT == 0
APBAL[供应商].PS{月|月NY} += (Σ赊购 − Σ退货)
BKTRN 行数 = APRCPCQ 中支票行数;  ISTAX 行 ⟺ TAX≠0;  ISVAT 行 ⟺ VATAMT≠0
```

---

## 5. 与已知类型(采购 RR/HP、销售 IV/HS)的异同

**多出来的**

1. **两张单据体表而不是一张明细表**:`APRCPIT`(结清分配)+ `APRCPCQ`(收付/扣减方式)。采购单只有单头+分录(+库存卡)。
2. **会改别的单据**:第一次出现「写入即修改既有 APTRN 行(PAYAMT/REMAMT/CMPLAPP/CMPLDAT)」。
   之前的类型全是 append-only。幂等/回滚复杂度是数量级差异。
3. **预扣税整条链**:`APTRN.TAX` + `ISTAX` 凭证 + GL 贷方 —— 采购/销售单完全没有。
4. **支票登记簿 `BKTRN`**:每张支票一行,带 `CHQSTAT` 生命周期(05 已开 → 10 已过账 → 20 退票),
   `APMAS.CHQPAY` 是它的缓存。
5. **付款时才认列的进项税**(泰国服务票范式):`ISVAT(VATREC='P', RECTYP='9')` + `Dr 1155-02 / Cr 1155-01`,
   192/1633 张单命中。采购单的 ISVAT 是开票即认列,这里是「付款月才进 ภ.พ.30」。
6. **GLJNLIT 的 SEQIT 是固定槽位**(2/5/6/7/8/9),不是自增序号;同槽可多行。
7. **应付控制科目逐供应商**(APMAS.ACCNUM,实测 2120-01 / 2120-02 / 2120-05 / 2131-05/06/07/14/17 八种),
   不是单据类型默认科目。

**少掉的**:无库存联动(不写 STCRD/STMAS/STTRN)、无商品主档、无 `POSTGL` 值(1633/1633 为空)、
`ISRUN` 里也不带默认科目。

**坑(都有实证)**

- `APRCPCQ.PAYAMT` **有正负**,符号定借贷;`NETAMT` 也可能是负数(`PS68L01-001` = −26,480.54,
  预付大于欠款、差额走汇兑)。
- `APRCPIT.RECTYP` 是**被结清单据的类型**,不是付款单的类型;算净额必须带符号。
- `BILNUM` 恒为 `'~'`、`BKTRN.REFDOC` 恒为 `'~'`:是哨兵字符串,不是空。
- 软删单据的**子行会留活**(`PS68T10-109` 单头已删、APRCPIT 还有 1 行活),而且**单号会被复用**
  (15 张软删单里 4 个号后来被新单占用)。幂等键不能只看单号,必须「活行 + 单号 + 供应商 + 金额」。
- 字段类型:`APTRN`/`APRCPIT`/`APRCPCQ`/`ISTAX`/`ISVAT` 金额是 VFP `'B'` double;`GLJNLIT.AMOUNT` 是 `N(13,2)`;
  泰文里的分隔符是 **NBSP `0xA0`**(cp874),不是空格 —— 拼 `GLJNL.DESCRP` 要照抄。
- 生产数据里有脏值:TEST 账套 `APMAS` 某数值字段是 `b'.'`,`dbf` 直接抛 `ValueError`。逐字段容错读,别整行读。
- 预扣税**不是自动的**:260/717 供应商配了 TAXRAT>0,但其中 278 张付款单没扣(货款票不扣、服务票才扣)。
  `ISINFO.MINTAXAMT=1000 / MINTAXRAT=3.0` 是门槛配置,但数据证明「扣不扣、扣多少基数」是操作员逐单决定
  —— **预扣必须作为推送载荷的显式输入,不能由代码推导**。
- 预扣科目映射在 **`istab` TABTYP='55'**(`S03→2132-02`、`S53→2132-03`、`S02→2132-01`),
  TEST 账套这张表 `SHORTNAM` 全空 → 只能回落 `ISINFO.ACCNUM09`,两处都空时必须拒绝写入而不是猜。

---

## 6. P2-B 施工建议

**难度:高。** 比已上线的采购 RR 高一档,不是「再写几张表」的量变。理由:
① 唯一一个要 **UPDATE 既有单据行**的类型(回滚要能撤销别人票上的 PAYAMT/REMAMT/CMPLAPP);
② 3 张缓存表(APBAL 双年桶 / APMAS.BALANCE+CHQPAY / GLBAL)必须同步或另想办法;
③ 预扣税是法定凭证(ภ.ง.ด.3/53 要报税),算错=真金白银的税务风险;
④ 科目来源分散在 4 个配置表(APMAS / ISRUN-ZP / istab-55 / ISINFO.ACCNUMxx),硬编码必炸。

**最大风险点(按严重度)**

1. **改别人的票**。同一张进项票可被多张付款单分次结清(实证 16 张票被 ≥2 张付款单结)。
   并发或重推会把 `PAYAMT` 累加两次 → 票被误判「已付清」,应付账凭空消失。
   **必须:先读回票的当前 PAYAMT/REMAMT → 校验 `本次分配额 ≤ REMAMT` → 写 → 再读回校验**,任一步不符立即整单回滚。
2. **APBAL 双年桶 + 重复档**。第 2 年要写 `PS{m}NY`,且 288 个供应商有多行 APBAL。
   写错桶/写错行 = 供应商对账单错但试算表对,是最难被发现的一类错。
   **建议第一版不碰 APBAL/GLBAL,改为写完后调 Express 自己的余额重算,或明确告知会计「余额报表需重算一次」——
   诚实优于假装写对**(这条要 Zihao 拍板)。
3. **预扣税科目/税种选错**。个人(S03→ภ.ง.ด.3)vs 法人(S53→ภ.ง.ด.53)走不同科目、不同申报表。
   取值链:载荷给 TAXTYP/TAXRAT/基数 → APMAS 兜底 → istab55 定科目 → ISINFO.ACCNUM09 回落 → 都没有就 escalate。
4. **单号复用 + 软删残留**导致幂等闸失效(见 §5)。这是已经踩过一次的坑(记忆 `dbf-soft-deleted-rows-fake-success`),
   这里叠加了单号复用,更毒。
5. GL 侧「按科目合并 SEQIT=5 行」——照抄 Express 的合并行为,否则复核台按行对不上。

**验证方案(TEST 账套 `\\Accserver\d$\ACCOUNT\69EXP\test`)**

- **现状**:`APTRN` 0 行、`APRCPIT/APRCPCQ/ISTAX` 全 0、`ISRUN(PS)` 计数器 `0000001`、691 个供应商、8 个银行户、
  `ISINFO` 科目齐全(4 段码:应付 `21-02-01-00`、支票 `21-02-02-00`、预扣53 `21-03-03-00`、进项税 `11-05-04-01`、
  待认列 `11-05-04-04`、预付 `11-05-01-01`)。**空到刚好可做净起点**,但 `istab55` 无科目映射
  —— 正好用来验「配置缺失要 escalate 而不是猜」。
- **造单顺序**:① 用已上线的 RR 采购菜谱推 2 张赊购票给同一供应商(制造应付余额)→ ② 推一张 PS 全额结清其中 1 张
  → ③ 推一张 PS 部分结清另一张(验 REMAMT/CMPLAPP='N')→ ④ 推一张带预扣的 PS(供应商先配 TAXRAT/TAXTYP)
  → ⑤ 推一张带退货冲抵/预付冲抵的 PS。
- **读回验**:跑 `appay_21_assertions.py` 指向 TEST(22 条断言必须全绿)+ Harbour `cdx_reindex_runner`
  重建 CDX 后按 `APTRN1=DOCNUM` / `GLJNL` 索引回查命中 + **真 Express.exe UI 打开该付款单截图**
  (照 doc32 Step A 的验收口径,别只信 DBF 回读)。
- **回滚**:沿用现有「写前备份 touched tables 的 DBF/CDX/FPT → 单事务 → 失败还原」;
  但本类型必须**额外记录被改票的 (DOCNUM, PAYAMT旧, REMAMT旧, CMPLAPP旧, CMPLDAT旧)** 到回滚日志,
  否则回滚只删得掉新行、改不回旧行。软删(打删除标记)不算回滚 —— Express 会把这些行当活行读(已知坑)。
- **建议第一版范围收窄**:只做「单一供应商 + 单一银行/支票 + 全额或部分结清赊购票 + 可选预扣」;
  **退货冲抵、预付冲抵、汇兑损益、付款时认列进项税(ISVAT)四类先 escalate 转人工**,
  它们合计只占 6902ASC 的 ~19%(预付 104 张 / VAT 192 张 / 退货与汇兑各几十张),
  但吃掉一半以上的实现复杂度和全部税务风险。
