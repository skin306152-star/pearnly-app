# 44 · Express 库存调整(ปรับปรุงสินค้า)只读逆向

> 逆向日期 2026-07-26 · **只读逆向产物**:全程 `dbf.Table(path, codepage='cp874')` + `t.open(dbf.READ_ONLY)`,
> 无写入 / 无 pack / 无删除;所有解析都在本地只读副本上进行。
> 脚本与副本留在逆向窗口 scratchpad:
> `C:\Users\skin3\AppData\Local\Temp\claude\C--Users-skin3-Desktop-pearnly-app\0a2cac22-1395-44cb-909d-b50e60da19d4\scratchpad\doctype_recon\`
> (脚本清单见文末附录)

**结论先行**:库存调整**有独立单头表 `STTRN`**(不是往 STCRD 裸追行)。全家族共 4 个文档类,
由 `STTRN.POSOPR` 区分;方向由**行级** `STCRD.POSOPR` 区分。调整单**会产 GL 凭证**——
但只在 `ISINFO.ISPERPETUA='Y'`(永续盘存)且**单据净值 ≠ 0** 时。
已知的「期初库存不产 GL」结论**不能外推到调整单**(下面有反证:同一批账套,期初不产 GL、调整产 GL;
而 `ISPERPETUA='N'` 的账套 2917 张调整单一张 GL 都没有)。

---

## 1. 样本盘点

### 1.1 勘察范围

| 根目录 | 账套数 | 方法 |
|---|---|---|
| `\\192.168.0.212\pas212\2569\EXP69\` | 7(6902ASC / 69ASIAMI / 69ASIAR / 69MANAC5 / 69MANACC / 69NATA12 / 69SINCER) | 逐套开 STTRN+STCRD+STMAS+STLOC+STTRN+ISRUN+ISACC+ISINFO+GLJNL+GLJNLIT |
| `\\192.168.0.212\pas212\2568\EXP68\` | 目录内全部 40+ 套,`s13_sweep.py` 扫 STTRN | 命中 26 套有单;深挖 6 套 |
| `\\Accserver\d$\ACCOUNT\69EXP\test` | 1(靶场) | 全表 |

表清单先用 `s01_structs.py` 打全结构,候选表
`STCRD / STMAS / STLOC / STTAK / STTRN / STCOD / STMIN / STPRI / STSTA / STBOM / ISRUN / ISACC / ISINFO / ISPRD / ISSN / ISSNIT / GLJNL / GLJNLIT / GLBAL / GLINV / istab`,逐个验证是否参与。

### 1.2 找到多少张(物理/活行)

`STTRN` 是单头表,`POSOPR` 是文档类。全量见 `s25_inventory.py` 输出:

| 账套 | 文档类 (STTRN.POSOPR) | 单头物理 | 单头活行 | 明细活行 | 有 GL 的单 | 前缀分布 |
|---|---|---|---|---|---|---|
| **6808GIZE** | `8` 数量调整 JU/TK/JG | 354 | 354 | 2119 | 205 | JG 210 / **JU 139** / **TK 5** |
| **6808GIZE** | `5` 成本调整 CA | 119 | 119 | 377 | 119 | CA 119 |
| **6808GIZE** | `6` 内部领用 OU | 222 | 222 | 370 | 201 | OU 141 / **ZZ 33**(报废)/ OR 26 / XC 13 / XS 8 / ED 1 |
| **6808GIZE** | `4` 仓间调拨 RL | 818 | 818 | 5590 | 1 | RL 818 |
| **68GIZE** | 8 / 5 / 6 / 4 | 242/100/146/590 | 同 | 1095/322/236/6332 | 109/100/134/1 | JU 85 / TK 1 / CA 100 / ZZ 57 |
| **68POLYM** | 8 / 6 / 4 | 116/2596/206 | 115/2596/206 | 2776/9360/1660 | **0/0/0** | JU 115 / OU 2595 |
| 68ASIM | 8 / 6 | 20/12 | 20/12 | 317/177 | 0/11 | JU 17 / JB 3 / OO 12 |
| 68MANA06 | 8 / 5 | 4/1 | 4/1 | 36/1 | 3/1 | JU 4 / CA 1 |
| **69SINCER**(生产 2569) | `6` 内部领用 | 85 | 84 | 98 | 84 | PM 49 / PB 10 / PL 6 / SP 5 / FC 3 / XS 3 / FB 2 / FP 2 / RP 2 / FR 1 / **ZZ 1** |
| **69ASIAMI**(生产 2569) | `6` | 59 | 59 | 74 | 59 | 8 个自定义前缀,均 DOCTYP=OU |
| **69ASIAR**(生产 2569) | `6` | 50 | 50 | 50 | 50 | 同上 |
| 6902ASC / 69MANAC5 / 69MANACC / 69NATA12 / TEST | — | **0** | 0 | — | — | 无 STTRN 行 |

**重要现实**:任务提示里点名的三个生产账套里,**6902ASC 一张调整单都没有**
(`ISPERPETUA='N'` 定期盘存,且 STTRN 空);69ASIAMI / 69ASIAR / 69SINCER **只有 OU 内部领用**(冰厂领原料),
**没有 JU/TK/CA**。真正的盘盈盘亏(TK)/数量调整(JU)/成本调整(CA)样本全部来自 `2568\EXP68` 下的
**6808GIZE / 68GIZE**(医疗器械经销商,多仓、多单位、FIFO)。

`STTAK`(盘点工作底稿)只在 6902ASC(731 行)和 6808GIZE(4494 行)有量,详见 §5。

### 1.3 代表性单据全字段转储

> 金额保留原值。转储只打印非空字段;完整原始输出在 `trace_*.txt`。

#### 样本 A — 盘盈(TK 库存增加)`6808GIZE :: TK67071001`

```
STTRN[626]  DOCNUM='TK67071001' DOCDAT=2024-07-10 POSOPR='8'
            REMARK='ปรับปรุงการตรวจนับสต็อก-สวนป่าน' LOCCOD='18' TRNVAL=36.24
            NXTSEQ='  2' ACCNUMCR='5110-00' DEPCOD='ขายB' DOCSTAT='N'
            USERID='KHWAN' CHGDAT=2025-04-02
STCRD[17870] STKCOD='6003050000001' LOCCOD='18' DOCNUM='TK67071001' SEQNUM='  1'
            DOCDAT=2024-07-10 DEPCOD='ขายB' POSOPR='1'          <-- 行级=1 表示「调整增加」
            TRNQTY=1.0 TQUCOD='อน' TFACTOR=1.0 UNITPR=36.24 TRNVAL=36.24
            XTRNQTY=1.0 XUNITPR=36.24 XTRNVAL=36.24 NETVAL=36.24
            MLOTNUM='202407101TK67071001    1' MREMBAL=1.0 MREMVAL=36.24
            LOTBAL=1.0 LOTVAL=36.24 LUNITPR=36.24 ACCNUMCR='5110-00'
            STKDES='ปรับปรุงการตรวจนับสต็อก-สวนป่าน'
STCRD[17871] STKCOD='6012050000002' SEQNUM='  2' POSOPR='1' TRNQTY=3.0
            (UNITPR/TRNVAL 全 0 —— 零成本商品盘盈,不进 GL 金额)
GLJNL[35934] JNLTYP='00' VOUDAT=2024-07-10 VOUCHER='TK67071001'
            DESCRP='ปรับปรุงการตรวจนับสต็อก-สวนป่าน' TRNSTAT='P' DOCSTAT='N'
            CREBY='KHWAN' CREDAT=2024-08-01
GLJNLIT[120586] VOUCHER='TK67071001' SEQIT=' 1' ACCNUM='1140-03' TRNTYP='0' AMOUNT=36.24  <-- 借 存货
GLJNLIT[120587] VOUCHER='TK67071001' SEQIT=' 1' ACCNUM='5110-00' TRNTYP='1' AMOUNT=36.24  <-- 贷 调整科目
```

#### 样本 B — 盘点单同时盘盈+盘亏,净盘亏 `6808GIZE :: TK67042701`

```
STTRN[363]  DOCNUM='TK67042701' DOCDAT=2024-04-27 POSOPR='8' LOCCOD='12'
            TRNVAL=-1059.78 NXTSEQ=' 13' ACCNUMCR='5110-00' DEPCOD='ขายD'
            DOCSTAT='N' USERID='KHWAN' CHGDAT=2024-07-06
STCRD  12 行:SEQNUM '  1'..' 12' 全 POSOPR='1' 正数(盘盈,但 UNITPR 多为 0)
STCRD[16250] SEQNUM=' 13' POSOPR='8'  <-- 行级=8 表示「调整减少」
            STKCOD='6001040301001' TRNQTY=-2.0 UNITPR=529.89 TRNVAL=-1059.78
            XTRNQTY=-2.0 XTRNVAL=-1059.78     <-- 唯一存负值的类型
            MLOTNUM='202311091TK66110901   11'(指向被扣的那批)
            MREMBAL=2.0 MREMVAL=1059.78 ACCNUMCR='5110-00'
GLJNLIT[120584] ACCNUM='5110-00' TRNTYP='0' AMOUNT=1059.78   <-- 净亏 → 借 调整科目
GLJNLIT[120585] ACCNUM='1140-03' TRNTYP='1' AMOUNT=1059.78   <-- 贷 存货
```

#### 样本 C — 数量调整净值为 0 → **完全不产 GL** `6808GIZE :: JU6800002`

```
STTRN[969]  DOCNUM='JU6800002' DOCDAT=2025-01-13 POSOPR='8' LOCCOD='01'
            TRNVAL=(0) REMARK='ปรับปรุงรายการสินค้าไนโตรเจนเหลว'
            NXTSEQ='  2' ACCNUMCR='5110-01' DOCSTAT='N' USERID='KHWAN'
STCRD[28436] STKCOD='6019000000006' SEQNUM='  1' POSOPR='8'
            TRNQTY=-50000.0 TQUCOD='ม3' TFACTOR=1.408
            UNITPR=10.38 TRNVAL=-518815.30
            XTRNQTY=-70400.0 XUNITPR=7.37 XTRNVAL=-518815.30   <-- X* 是基本单位
            MLOTNUM='202401120RR3001564     1' LOTBAL=70400.0
STCRD[28437] STKCOD='6019000000005' SEQNUM='  2' POSOPR='1'
            TRNQTY=50000.0 TQUCOD='กก' TFACTOR=1.25
            TRNVAL=518815.30 XTRNQTY=62500.0 XUNITPR=8.3 NETVAL=518815.30
GLJNL / GLJNLIT: 无(净值 0 → 不建凭证)
```

#### 样本 D — 成本调整(只调金额不动数量)`6808GIZE :: CARR2024031`

```
STTRN[540]  DOCNUM='CARR2024031' DOCDAT=2024-06-01 POSOPR='5' LOCCOD='01'
            TRNVAL=19223.11 NXTSEQ='  1' ACCNUMCR='5132-07'
            REMARK='PO.P24013 EL.PA SAS  Lot.1  24G00012' DOCSTAT='N'
STCRD[15891] STKCOD='6004000000009' SEQNUM='  1' POSOPR='5' FLAG='2'
            RDOCNUM='RR2024031     1'   <-- 被调成本的原收货单 DOCNUM(12)+SEQNUM(3)
            TRNQTY=(0)  TRNVAL=19223.11 XTRNVAL=19223.11 NETVAL=19223.11
            MLOTNUM='202403230RR2024016     1' MREMBAL=46.0 MREMVAL=47028.99
            ACCNUMCR='5132-07'
GLJNLIT  DR '1140-03' 19223.11 / CR '5132-07' 19223.11(SEQIT 均=' 1')
```

#### 样本 E — 报损/内部领用(生产账套真样本)`69SINCER :: ZZ680930-001`

```
STTRN[38]   DOCNUM='ZZ680930-001' DOCDAT=2025-09-30 POSOPR='6' LOCCOD='01'
            TRNVAL=5500.0 NXTSEQ='  1' ACCNUMDR='51-03-04-18'  <-- OU 填 DR 不填 CR
            DOCSTAT='N' USERID='BIT5' CHGDAT=2026-04-09
STCRD[3302] STKCOD='DM-HYDROPERSE' LOCCOD='01' SEQNUM='  1' POSOPR='6'
            TRNQTY=1.0 TQUCOD='ถ' TFACTOR=1.0 UNITPR=5500.0 TRNVAL=5500.0
            XTRNQTY=1.0 XUNITPR=5500.0 XTRNVAL=5500.0    <-- 出库类存正数,方向靠 POSOPR
            MLOTNUM='202509020RR680902-002  1' MREMBAL=1.0 MREMVAL=5500.0
            ACCNUMDR='51-03-04-18' STKDES='HYDROPERSE PREMIUM MD901@25 KG'
GLJNL[4682] JNLTYP='00' VOUCHER='ZZ680930-001' DESCRP='จ่ายสินค้าภายใน ZZ680930-001'
            TRNSTAT='P' DOCSTAT='N'
GLJNLIT  DR '51-03-04-18'(费用)5500 / CR '11-04-01-00'(存货)5500
```

---

## 2. 落表清单

一张调整单一次写 **5 张表**(有 GL 时;无 GL 时 3 张),另加 2 张余额表 Express 自己维护。

| 表 | 字段 | 值来源 |
|---|---|---|
| **ISRUN**(取号)1 行更新 | `DOCTYP`+`DOCCOD` | 定位键:JU/TK/JG→`DOCTYP='JU'`,CA→`'CA'`,OU/ZZ/XS→`'OU'`,RL→`'RL'`;`DOCCOD=''` |
| | `PREFIX` | 单别前缀(每账套自定义,同 DOCTYP 可有多行) |
| | `DOCNUM` C(10) | 自增流水种子;取号后 +1 回写(**详见 §3,不可靠**) |
| | `JNLTYP` | 恒 `'00'`(总账日记账);同时被 `ISINFO.INTISSJNL/TAKADJJNL/COSADJJNL` 覆盖确认 |
| | `ACCNUM01` | 该单别的**对方科目**默认值(JU/TK→5110-xx,CA→5132-07 类,OU→费用科目) |
| **STTRN**(单头)**1 行**(新增) | `DOCNUM` C(12) | 取号结果 |
| | `DOCDAT` D | 公历日期(佛历只出现在 DOCNUM 字符串) |
| | `POSOPR` C(1) | **常量按文档类**:`8`=数量调整(JU/TK/JG)、`5`=成本调整(CA)、`6`=内部领用/报损(OU/ZZ/XS/OR/XC/ED)、`4`=仓间调拨(RL) |
| | `LOCCOD` C(4) | 仓库码;默认 `ISINFO.MAINLOC`(全库均为 `'01'`) |
| | `TRNVAL` B | Σ 明细 `TRNVAL`(录入时刻快照,**会漂**,见 §4) |
| | `NXTSEQ` C(3) | 明细行数,右对齐空格填充 `'  1'`;删过行时会比实际行数大 |
| | `ACCNUMDR` C(15) | **仅 POSOPR=6 填**(费用科目=借方);其余留空 |
| | `ACCNUMCR` C(15) | **POSOPR=8/5 填**(调整对方科目);OU/RL 留空 |
| | `REMARK` C(50) | 用户摘要;会被复制进 STCRD.STKDES 和 GLJNL.DESCRP |
| | `DEPCOD` C(4) | 部门码(可空);会传到费用侧 GLJNLIT |
| | `REFNUM`/`REFDAT`/`PEOPLE` | 可空(RL 用 PEOPLE 记对方仓/领用人) |
| | `DOCSTAT` C(1) | `'N'` 正常 / `'C'` 已作废 |
| | `USERID` C(8) / `CHGDAT` D | 写入者 / 写入日 |
| **STCRD**(明细)**每商品 1 行** | `STKCOD` C(20) | 商品码(**注意 STMAS 可能有重复 STKCOD,见 §5**) |
| | `LOCCOD` C(4) | 同单头 |
| | `DOCNUM` / `SEQNUM` C(3) | 单号 / `'  1'`,`'  2'`…右对齐空格填充 |
| | `DOCDAT` D | 同单头 |
| | `POSOPR` C(1) | **行级方向**:`1`=调整增加、`8`=调整减少、`5`=成本调整(数量 0)、`6`=内部领用出、`3`/`4`=调拨进/出 |
| | `TRNQTY` B | **录入单位**数量。仅 `POSOPR='8'` 存负数,其余全存正数(方向靠 POSOPR) |
| | `TQUCOD` C(2) / `TFACTOR` B | 录入单位 / 换算到基本单位的倍数 |
| | `XTRNQTY` B | `= TRNQTY × TFACTOR`,**基本单位数量,余额靠它移动** |
| | `UNITPR` / `XUNITPR` B | 每录入单位单价 / 每基本单位单价 |
| | `TRNVAL` = `XTRNVAL` B | 行金额(含符号) |
| | `NETVAL` B | 录入时刻的行金额(重算成本后**不跟着变**,可与 TRNVAL 不等) |
| | `MLOTNUM` C(24) | **批次键 = `YYYYMMDD`(8)+`POSOPR`(1)+`DOCNUM`(12,右补空格)+`SEQNUM`(3)**;增加行指自己,减少行指被扣的来源批 |
| | `MREMBAL` / `MREMVAL` B | 移动均价法下该行**之前**的结存量/结存值快照 |
| | `LOTBAL`/`LOTVAL`/`LUNITPR` B | FIFO/批次法下的批次结存 |
| | `ACCNUMDR` / `ACCNUMCR` | 从单头复制下来 |
| | `STKDES` C(50) | 摘要(调整单里通常= STTRN.REMARK,不是商品名) |
| | `RDOCNUM` C(15) | **仅 CA**:被调成本的原收货单 `DOCNUM(12)+SEQNUM(3)` |
| | `DEPCOD`/`JOBCOD`/`PHASE`/`COSCOD` | 可空维度 |
| **GLJNL**(凭证头)**1 行** | `VOUCHER` C(12) | **= DOCNUM 原样**(不另取号) |
| | `JNLTYP` C(2) | 恒 `'00'` |
| | `VOUDAT` D | = DOCDAT |
| | `DESCRP` C(50) | JU/TK/CA→ STTRN.REMARK;OU→ `'จ่ายสินค้าภายใน ' + DOCNUM` |
| | `TRNSTAT` C(1) | `'P'`(已过账)——6808GIZE 36419 张凭证 100% 为 P |
| | `DOCSTAT` C(1) | `'N'` / 作废后 `'C'` |
| | `CREBY`/`CREDAT`/`USERID`/`CHGDAT` | 过账者/过账日(**可能晚于单据日很久,过账是独立动作**) |
| **GLJNLIT**(分录)**恒 2 行**(净值≠0 时) | `VOUCHER` | = DOCNUM |
| | `SEQIT` C(2) | **两行都是 `' 1'`**(不是 1/2) |
| | `VOUDAT` | = DOCDAT |
| | `ACCNUM` C(15) | 存货侧 = `ISACC[('S', STMAS[STKCOD].ACCCOD)].ACCNUM01`;对方侧 = STTRN.`ACCNUMDR`/`ACCNUMCR` |
| | `TRNTYP` C(1) | `'0'`=借 / `'1'`=贷 |
| | `AMOUNT` N(13,2) | `abs(Σ 明细 TRNVAL)` |
| | `DEPCOD` | 仅费用/调整侧带部门 |
| | `DESCRP` | 与 GLJNL.DESCRP 同 |
| | `CHGDAT`/`CHGTIM` C(4) | 过账时间戳 `'1438'` |
| **STMAS**(商品主档)每商品 1 行更新 | `TOTBAL` += Σ `XTRNQTY`(带符号);`TOTVAL` += Σ `TRNVAL`;`MLOTNUM`/`MREMBAL`/`MREMVAL` 推进;`UNITPR` 重算;`LASUPD` | Express 自维护 |
| **STLOC**(分仓余额)每(商品,仓)1 行更新 | `LOCBAL` += Σ `XTRNQTY`;`QTY1..12`/`VAL1..12`/`*NY` 月度桶按期间加;`LMOVDAT` | Express 自维护;**现有小助手推送根本没写这张**(TEST 账套 8 张 IV 单后 STLOC 仍 0 行) |
| **GLBAL**(科目月度桶)每科目 1 行更新 | `DEBIT{1..12}` / `CREDIT{1..12}`(+ `*LY`/`*NY`/`*CLS`)按凭证月份加 | Express 自维护;**现有推送也没写**(TEST 里 0 行) |

**不参与**的表(已验证):`ISVAT`(调整不涉税)、`APTRN`/`ARTRN`/`APBAL`/`ARBAL`(无往来方)、
`ISSN`/`ISSNIT`(全库 0 行,未用序列号)、`ISPRD`、`GLINV`(6 行,是存货科目月末余额报表缓存,重算时才刷)、
`STTAK`(可选上游底稿,见 §5)。

---

## 3. 取号规则

**DOCNUM = 前缀(2) + 自由体(≤10),C(12)。**

`ISRUN` 里的对应行(6902ASC 实测,泰/英描述原文):

| DOCTYP | DOCCOD | PREFIX | POSDES | ACCNUM01 | JNLTYP |
|---|---|---|---|---|---|
| `JU` | `''` | `JU` | ปรับปรุงเพิ่ม/ลดสินค้า / Quantity Adjustment | 5110-00 | 00 |
| `JU` | `''` | `TK` | ปรับปรุงจากการตรวจนับ / Physical Count Adjustment | 5110-00 | 00 |
| `JU` | `''` | `PI` | รับส/คสำเร็จรูปจากการผลิต / Finished Goods from Process | 1140-20 | 00 |
| `CA` | `''` | `CA` | เพิ่ม/ลดต้นทุนสินค้า / Cost Adjustment | 5110-00 | 00 |
| `CA` | `''` | `CF` | ปรับค่าขนส่งสินค้า / Freight Adjustment | 5200-05 | 00 |
| `CA` | `''` | `CI` | ปรับปรุงค่าประกันภัย / Insurance Adjustment | 5200-07 | 00 |
| `OU` | `''` | `OU` | จ่ายสินค้าใช้ภายใน / Internal Issue | 5320-03 | 00 |
| `OU` | `''` | `XS` | จ่ายสินค้าเป็นตัวอย่าง / Issue for Sample | 5200-03 | 00 |
| `OU` | `''` | `ZZ` | **ตัดสินค้าชำรุด / Defect Stock**(报损) | 5110-00 | 00 |
| `OU` | `''` | `PD` | จ่ายวัตถุดิบเพื่อผลิต / Material Issue for Processing | — | 00 |
| `RL` | `''` | `RL` | โอนย้ายระหว่างคลัง / Relocate Stock | — | 00 |

**一个 DOCTYP 可挂多个 PREFIX 行**,每个 PREFIX 自带默认对方科目——这就是各账套自定义单别的方式
(69SINCER 把 OU 拆成 PM/PB/PL/SP/FC/FB/FP/RP/FR/XS/ZZ 11 个前缀,每个绑不同费用科目)。

**回写机制与真实性(实测,别信文档)**:

- `ISRUN.DOCNUM` C(10) 是**自增种子**,Express 用 `PREFIX + 该数字` 预填录入框,用户可覆盖。
- 6808GIZE 实测:`JU` 种子='0000005',文件里正好有 `JU0000001..JU0000005`(还有一张用户手打的 `JU0000047`);
  `TK` 种子='0000002' 但只剩 `TK0000001`(另一张被作废)。**种子既不等于「文件里的最大号」,也不保证连续**。
- 用户绝大多数覆盖成自己的方案,三种并存:
  - 佛历日期式:`PM680106-001` = 前缀 + 佛历 `YYMMDD`(68=2568) + `-` + 3 位当日序
  - 佛历年+流水:`JU6800039` / `ZZ6800014` = 前缀 + 佛历年 2 位 + 5 位年内流水
  - 业务号式:`CARR2024031`(挂原 PO/收货单)
- **DOCDAT 存公历,佛历只在 DOCNUM 字符串里**——与已知采购/销售一致。
- 唯一性靠 `.CDX` 索引(`STTRN1` = DOCNUM;`STCRD` 有 DOCNUM+SEQNUM 复合标签),DBF 本身不约束。

> **P2-B 取号做法**:不能只读 ISRUN 造号。必须 ① 读该账套该前缀现存单号,识别出它用的是哪种方案;
> ② 按方案生成;③ **写前用 CDX 探针 DbSeek 查重**;④ 用了种子才把 `ISRUN.DOCNUM` +1 回写。

---

## 4. 配平校验(可机械执行)

记 `L` = 该单 STCRD 活行集合,`H` = STTRN 单头,`J` = GLJNLIT 活行集合。

```python
# --- A. 单头 / 明细 ---
A1  len(L) >= 1
A2  all(l.DOCDAT == H.DOCDAT and l.LOCCOD == H.LOCCOD for l in L)
A3  {l.SEQNUM for l in L} == {f"{i:>3}" for i in range(1, len(L)+1)}     # 右对齐空格填充
A4  int(H.NXTSEQ) >= len(L)                                              # 删过行时会更大
A5  all(abs(l.XTRNQTY - l.TRNQTY * l.TFACTOR) <= 1e-6 for l in L)
A6  all(abs(l.TRNVAL - l.XTRNVAL) <= 0.005 for l in L)
A7  all((l.TRNQTY < 0) == (l.POSOPR == '8') for l in L if l.POSOPR != '5')
A8  all(l.TRNQTY == 0 for l in L if l.POSOPR == '5')                     # 成本调整不动量
A9  all(l.MLOTNUM[:8] == l.DOCDAT.strftime('%Y%m%d') for l in L if l.MLOTNUM)
A10 all(l.MLOTNUM[8] == l.POSOPR for l in L if l.MLOTNUM and l.POSOPR in '18')

# --- B. 方向 / 类型一致性 ---
B1  H.POSOPR in {'4','5','6','8'}
B2  H.POSOPR == '8' -> all(l.POSOPR in {'1','8'} for l in L)
    H.POSOPR == '5' -> all(l.POSOPR == '5'       for l in L)
    H.POSOPR == '6' -> all(l.POSOPR == '6'       for l in L)
    H.POSOPR == '4' -> {l.POSOPR for l in L} == {'3','4'}   # 调拨成对
B3  H.POSOPR == '6' -> H.ACCNUMDR != '' and H.ACCNUMCR == ''
    H.POSOPR in {'5','8'} -> H.ACCNUMCR != '' and H.ACCNUMDR == ''
B4  all(l.ACCNUMDR == H.ACCNUMDR and l.ACCNUMCR == H.ACCNUMCR for l in L)

# --- C. GL 存在性(核心) ---
NET = sum(l.TRNVAL for l in L)
C1  bool(J) == (ISINFO.ISPERPETUA == 'Y' and abs(NET) > 0.005)
      # 6808GIZE: 690/696 命中;68ASIM: 32/32 命中;68POLYM(ISPERPETUA='N'): 2917 单 0 GL

# --- D. 借贷平衡 ---
INV    = ISACC[('S', STMAS[l.STKCOD].ACCCOD)].ACCNUM01     # 存货科目
OFFSET = H.ACCNUMDR or H.ACCNUMCR                          # 对方科目
D1  len(J) == 2
D2  {j.SEQIT for j in J} == {' 1'}
D3  sum(j.AMOUNT for j in J if j.TRNTYP=='0') == sum(j.AMOUNT for j in J if j.TRNTYP=='1')
D4  sum(j.AMOUNT for j in J if j.TRNTYP=='0') == round(abs(NET), 2)
D5  {j.ACCNUM for j in J} == {INV} | {OFFSET}              # 716/719 精确命中
D6  NET > 0 -> (借方科目 == INV and 贷方科目 == OFFSET)     # 库存增加
    NET < 0 -> (借方科目 == OFFSET and 贷方科目 == INV)     # 库存减少
D7  GLJNL.VOUCHER == H.DOCNUM and GLJNL.JNLTYP == '00'
    GLJNL.VOUDAT == H.DOCDAT and GLJNL.TRNSTAT == 'P'

# --- E. 余额读回(delta 断言,写前后各拍一次快照) ---
E1  ΔSTMAS[k].TOTBAL == Σ signed(XTRNQTY) over lines of item k
E2  ΔSTMAS[k].TOTVAL == Σ TRNVAL          over lines of item k
E3  ΔSTLOC[(k,loc)].LOCBAL == Σ signed(XTRNQTY) over lines of (k,loc)
      # signed(): POSOPR ∈ {0,1,2,3} → +;{4,6,7,9} → −;{8} → 已带符号;{5,''} → 0
      # 全量验证:69ASIAMI 159/159 stock item 精确对上;69SINCER 34/35(唯一失败项含跨年残留行)
```

**已知会假红的两条**(不是 bug,是 Express 行为):

- `H.TRNVAL` 与 `Σ L.TRNVAL` **会漂**。Express 重算成本后刷新 `STCRD.TRNVAL` 但**不刷 STTRN.TRNVAL**
  (69SINCER 42/84 单漂、69ASIAMI 13/59 单漂)。**永远以明细为准,别拿单头总额做校验基准。**
- `GLJNLIT.AMOUNT` 与 `abs(NET)` 也会漂(6808GIZE 28/1513 ≈ 1.9%),因为 GL 是**过账那一刻的快照**,
  之后重算成本不回头改凭证。`GLJNL.CREDAT` 早于 `STTRN.CHGDAT` 的单基本都是这种。

---

## 5. 与采购/销售单的异同

### 多了什么

1. **独立单头表 `STTRN`**,采购/销售没有(它们用 APTRN/ARTRN)。字段极简(11 个业务列)。
2. **行级 `POSOPR` 与单头 `POSOPR` 不同**。采购/销售是单一方向,行级 POSOPR 恒等于类型;
   调整单一张单里 `1`(增)和 `8`(减)可以并存,GL 只认净额。**只看单头 POSOPR 会把盘亏当盘盈。**
3. **净额为零 → 一张凭证都不建**。6808GIZE 里 JU 有 148/354、JG 有 80/210 是零净额(拆套/换码/串货纠正)。
   校验脚本若断言「必有 GL」会大面积假红。
4. **`STTRN.ACCNUMDR` / `ACCNUMCR` 二选一填**,填哪个决定了科目角色:OU 填 DR、JU/TK/CA 填 CR、RL 两个都空。
5. **`RDOCNUM`(仅 CA)**指回被调成本的原收货行,是唯一的跨单溯源字段。
6. **`STTAK` 盘点底稿**是可选上游:`TAKFLG='1'` = 已点未转单(DOCNUM 空),
   `TAKFLG='6'` = 已转单(DOCNUM/SEQNUM 指向生成的 TK 单明细行)。6902ASC 731 行里 657 行停在 `'1'` 从没转成单。
   **要写 TK 单不必先写 STTAK**——TK 单本身完全活在 STTRN+STCRD。
7. **作废语义不同**:采购/销售靠软删行;调整单作废 = `STTRN.DOCSTAT='C'` + `TRNVAL=0` + `NXTSEQ=''`,
   **明细行被物理移除**(不是软删,连删除标志都不留),GLJNL 保留但 `DOCSTAT='C'`。6808GIZE 有 10 张这种壳。

### 少了什么

- **无 `ISVAT`**(不涉税)、**无 `APTRN`/`ARTRN`/`APBAL`/`ARBAL`**(无往来方)、
  **无 `PEOPLE` 必填**(只有 RL 用它记对方仓)。
- **GLJNLIT 恒 2 行**,不像采购的 3 行(采购/进项税/应付)或销售的 3 行。
  **`SEQIT` 两行都是 `' 1'`**,不是 1/2 —— 与现在小助手写销售单时用 `'2'/'5'/'6'` 的做法不一样。

### 坑(全部实测,不是推测)

1. **🛑 `ISPERPETUA='N'` 的账套调整单一张 GL 都不产。** 68POLYM(定期盘存)2917 张调整单 → 0 张凭证;
   6902ASC 也是 `'N'`。**必须先读 `ISINFO.ISPERPETUA` 再决定要不要写 GL**,写错就是凭空造账。
   这条同时**推翻了「期初库存不产 GL 所以调整单也不产」的类推**——在永续账套里调整单是产 GL 的。
2. **🛑 余额靠 `XTRNQTY` 移动,不是 `TRNQTY`。** 6808GIZE 有 TFACTOR = 12 / 50 / 100 / 1.408 的商品
   (如 `6019000000006`:基本单位 `ลต` 升,录入单位 `ม3` 立方米,`CFACTOR=1.408`)。
   按 TRNQTY 加减 = 库存差几十倍。
3. **🛑 只有 `POSOPR='8'` 存负数。** 其余出库类型(`4`/`6`/`7`/`9`)一律存正数,方向靠 POSOPR。
   写入时若给内部领用写负数,Express 会当成「负出库=入库」。
4. **🛑 `STMAS` 的 `STKCOD` 不保证唯一。** 69SINCER 有两行 `DM-ถุงพลาสติก`。按商品码单行查会取错。
5. **`NETVAL` ≠ `TRNVAL`** 时不是错:NETVAL 是录入快照,TRNVAL 是重算后现值。
6. **一张单跨多个存货科目组时 Express 只出一对分录**(6808GIZE `JG6800062`:商品分属 `1140-03` 和 `1410-14`,
   凭证只用了 `1140-03`)。Express 自己都不拆——复刻时要照抄这个行为,不能「更正确」地拆成 4 行,否则报表对不上。
7. **`GLJNL.CREDAT` 可以晚于 `DOCDAT` 好几个月**(PM680106-001:单据 2025-01-06,凭证 2025-09-06)。
   过账是独立批量动作。写入时若照抄现有单的 CREDAT 逻辑会产生「未来凭证」。
8. **`MLOTNUM` 编码固定**:`YYYYMMDD` + `POSOPR` + `DOCNUM`(12,右补空格)+ `SEQNUM`(3)。
   减少行必须指向**被扣的那一批**的 MLOTNUM,不是自己的。写错批号 → FIFO 成本链断,
   后续所有出库成本全错且 Express 不报错。
9. **负库存是常态且被允许**:全部 8 个受检账套 `NEGALLOW='Y'`(GIZE 系 `'N'`),`CHKNEGLEV='0'`。
   调整减少可以把余额打到负数,不会被拦。
10. **现有小助手推送不写 `STLOC` 和 `GLBAL`。** TEST 账套跑完 8 张 IV 单后 STLOC 仍 0 行、GLBAL 0 行。
    销售单能糊弄过去(用户主要看总账),但调整单用户会去看「分仓库存报表」和「科目余额表」,
    这两张空着 = 用户看不见自己刚做的调整。

---

## 6. P2-B 施工建议

### 难度评级:**中**

拆开看:

| 维度 | 评级 | 依据 |
|---|---|---|
| 表结构复刻 | **低** | 只多一张 `STTRN`(11 个业务列),其余表现有推送已在写;`STTRN.CDX` 已存在(标签 `STTRN1`=DOCNUM),Harbour REINDEX 管线现成 |
| GL 生成 | **低** | 恒 2 行、SEQIT 恒 `' 1'`、科目推导只有一条规则(`ISACC.ACCNUM01` + 单头对方科目) |
| 方向/单位/批次语义 | **高** | 行级 POSOPR × 符号约定 × TFACTOR × MLOTNUM 四个正交陷阱,任一错都静默错账 |
| 取号 | **中** | ISRUN 种子不可信,必须按账套观察到的方案生成 + 索引查重 |
| 余额与月度桶 | **中→高** | STMAS 现有推送已维护;STLOC / GLBAL **完全没写过**,是新债 |

### 最大风险点(按严重度)

1. **🔴 在 `ISPERPETUA='N'` 账套里误写 GL**。目标生产账套 6902ASC 正是 `'N'`。写了 = 凭空造凭证污染总账。
   **闸:写入前读 ISINFO.ISPERPETUA,`'N'` 时只写库存三表并在 UI 明说「此账套为定期盘存,本单不产生凭证」。**
2. **🔴 批次键 `MLOTNUM` 写错导致成本链静默断裂**。减少行必须指向真实的来源批(要先读 STCRD 找该商品该仓的可用批)。
   错了不报错,几个月后成本全歪。**闸:写完读回该商品后续所有 STCRD 行的 LOTBAL/MREMBAL 连续性。**
3. **🟠 单位换算**:UI 收的是用户单位,落库要 `XTRNQTY = TRNQTY × TFACTOR`,
   且 `TFACTOR` 要从 `STMAS.CQUCOD/CFACTOR` 查。
4. **🟠 STLOC/GLBAL 不写导致「报表里看不见」**。这是现有推送的既有债,但调整单会把它暴露给用户。
   建议本批一并补上(至少 STLOC.LOCBAL + 对应月度桶)。
5. **🟠 号码撞车**。前缀 + 佛历日期 + 序号的方案在多人同日操作时会撞;必须索引查重后重试。

### 验证方案

**造单(TEST 账套 `\\Accserver\d$\ACCOUNT\69EXP\test`)**

- 现状:`ISPERPETUA='Y'`、`COSMTD='A'`、`NEGALLOW='Y'`、`MAINLOC='01'`;已有 2 个商品
  `PN00001`(TOTBAL=-497)/`PN00002`(-19)、8 张 IV 单、STTRN **0 行**、STLOC/GLBAL **0 行**。
  ISRUN 完整(与 6902ASC 同一套单别定义)。
- 造 4 张覆盖全部分支:
  1. **JU 盘盈**:1 行 `POSOPR='1'`、正 XTRNQTY、有单价 → 期望 GL `DR 存货 / CR 5110-00`
  2. **JU 盘亏**:1 行 `POSOPR='8'`、**负** TRNQTY/TRNVAL → 期望 GL `DR 5110-00 / CR 存货`
  3. **JU 混合净零**:一增一减等额 → 期望 **不产 GL**(这是最容易做错的分支)
  4. **ZZ 报损**:`POSOPR='6'`、单头填 `ACCNUMDR` → 期望 GL `DR 费用 / CR 存货`
- 单据日期落在 TEST 现有账期(现有 IV 单 DOCDAT=2026-05-31),别落到期外。

**读回验证(全部机械化,不靠肉眼)**

1. 跑 §4 的 A/B/C/D 全部断言。
2. **写前后 delta**:对 touched 商品拍 `STMAS.TOTBAL/TOTVAL/MLOTNUM/MREMBAL` 与 `STLOC.LOCBAL/QTY{month}` 快照,
   断言 E1/E2/E3。
3. **CDX 回查**:Harbour `cdx_reindex_runner` 对 `STTRN`(`STTRN1`=DOCNUM)、`STCRD`(DOCNUM+SEQNUM)、
   `GLJNL`(VOUCHER)、`GLJNLIT`(VOUCHER+SEQIT)、`STMAS`(STKCOD)、`STLOC`(STKCOD+LOCCOD)、
   `GLBAL`(ACCNUM+DEPCOD)REINDEX + DbSeek 命中才算成功。
4. **对标真样本**:把造出的 4 张单逐字段与本文 §1.3 的 A/B/C/E 五个真实单据比对
   (`s07_trace.py <set> <docnum>` 可直接产出同格式转储做 diff)。这是唯一能证明「和 Express 自己写的等价」的方法。
5. **真机门**:打开 Express UI 按单号查得到该单 + 明细 + 分录;
   再跑「รายงานสินค้าคงเหลือ」(库存余额表)与「งบทดลอง」(试算表)看勾稽。

**回滚**

- **首选:恢复备份**。写前备份 touched tables 的 `.DBF/.CDX/.FPT`(现有推送已有此机制),失败即整体还原。
  这是唯一干净的路。
- **次选(已写成功但要撤):照抄 Express 的作废语义**——`STTRN.DOCSTAT='C'` + `TRNVAL=0` + `NXTSEQ=''`,
  物理移除 STCRD 明细行,`GLJNL.DOCSTAT='C'` + 移除 GLJNLIT,**并把 STMAS/STLOC 余额反向扣回**。
  注意 Express 是**物理删明细**不是软删,若只打删除标志,`dbf.is_deleted` 过滤得掉但 Express 的 CDX 遍历不一定,
  会出现「报表里还在」。
- **绝不做**:写反向调整单来抵消。会在 STCRD 里留下两条真实 movement,污染批次链和月度桶,
  且用户在报表里会看到两笔莫名其妙的调整。

**建议施工顺序**:先做 OU/ZZ(单方向、单头填 DR、生产账套有 84+59+50 张真样本可对标)
→ 再做 JU/TK(双方向 + 净零分支)→ CA 成本调整最后(需要先解决 RDOCNUM 溯源到原收货行)。
RL 仓间调拨可单独一批(它不产 GL,风险最低但明细成对写)。

---

## 附录 · 留在 scratchpad 的脚本

| 文件 | 作用 |
|---|---|
| `lib_dbf.py` | 只读打开封装(cp874 + READ_ONLY + 本地缓存 + 坏日期容错)、账套路径表 |
| `s01_structs.py` | 打印库存/GL 相关表结构与物理/活行数 |
| `s02_posopr.py` / `s16_signs.py` | STCRD.POSOPR 分布、符号约定统计 |
| `s03_isrun.py` / `s04_isrun_slim.py` / `s06_prefix_map.py` | ISRUN 全量/精简转储、前缀→单别映射 |
| `s05_scan.py` / `s13_sweep.py` | 单账套 / 跨根目录批量扫 STTRN 找样本 |
| `s07_trace.py` | **主力**:给账套+单号,跨 10 张表全字段转储 |
| `s08_sttrn_list.py` / `s25_inventory.py` | STTRN 单头清单 / 最终样本盘点表 |
| `s09_isacc.py` / `s10_acct_src.py` / `s11_isinfo_cfg.py` | 科目组映射、存货科目来源、ISINFO 开关矩阵 |
| `s12_validate.py` / `s14_posopr_xtab.py` / `s15_adj_recon.py` | 单据级配平校验、单头×行级 POSOPR 交叉表、调整族勾稽 |
| `s17_numbering.py` | ISRUN 种子 vs 实际单号对照 |
| `s18_balance.py` / `s19_balance2.py` / `s20_buckets.py` | 余额勾稽(粗/精)、STLOC/GLBAL 月度桶 |
| `s21_sttak.py` / `s22_misc.py` / `s23_test_state.py` / `s24_cdx_tags.py` | 盘点底稿、GLINV/istab、TEST 账套现状、CDX 索引标签 |
| `trace_TK.txt` `trace_TK2.txt` `trace_JU.txt` `trace_CA.txt` `sttrn_6808GIZE.txt` `isrun_*.txt` `validate_asia.txt` `adj_recon_6808GIZE.txt` | 原始输出 |
| `_cache/` `_sweep/` | 只读拷贝的 DBF 副本(全程未回写任何生产文件) |
