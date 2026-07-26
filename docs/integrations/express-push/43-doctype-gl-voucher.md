# 43 · Express 手工总账凭证(บันทึกรายการบัญชี / Manual GL Voucher)只读逆向

> 逆向日期 2026-07-26 · **只读逆向产物**:分析脚本 `00_struct.py` … `16_final_checks.py`(共 17 个),
> 全部 `READ_ONLY`,无任何写入 / pack / 删除。结论全部来自真账套样本。
> 脚本与 DBF 只读副本留在逆向窗口 scratchpad:
> `C:\Users\skin3\AppData\Local\Temp\claude\C--Users-skin3-Desktop-pearnly-app\0a2cac22-1395-44cb-909d-b50e60da19d4\scratchpad\doctype_recon\`
> 本地只读副本在同目录 `6902ASC/`、`69ASIAMI/` … `TEST/`。

---

## 1. 样本盘点

**判别式(本轮最重要的结论):`GLJNL.SRCJNL == 'GL  '` 就是手工凭证,零误差。**

在 6902ASC 的 11,628 条活头里做双向反证(`03_manual_probe.py`):

- `SRCJNL='GL'` 但 VOUCHER 前缀不在 {JV,PV,RV,SV,UV,PC} 的:**0**
- VOUCHER 前缀是 GL 系列但 `SRCJNL≠'GL'` 的:**0**
- `SRCJNL='GL'` 且 `前缀→JNLTYP` 映射不一致的:**0**

单据自动产生的凭证一律 `SRCJNL='    '`(4 空格)。`BATCH` / `REVERSE` / `POSTID` / `POSDAT` / `PRNDAT` /
`APPROVE` 在全库 11,628 条(含自动)里 **100% 为空**,做不了判别式。

### 样本量(七个生产账套 + 靶场)

| 账套 | GLJNL 物理/活/软删 | 手工凭证(活) | 手工凭证(软删) | 手工分录行(活) | GLJNLIT 物理/活/软删 |
|---|---|---|---|---|---|
| 6902ASC | 19463 / 11628 / 7835 | **920** | 33 | 4281 | 70251 / 34714 / 35537 |
| 69ASIAMI | 1574 / 1570 / 4 | **561** | 0 | 1548 | 4451 / 4389 / 62 |
| 69ASIAR | 1702 / 1669 / 33 | **866** | 1 | 7320 | 9938 / 9773 / 165 |
| 69MANAC5 | 2055 / 1826 / 229 | **567** | 6 | 1984 | 7725 / 6252 / 1473 |
| 69MANACC | 602 / 601 / 1 | **58** | 0 | 140 | 2219 / 2213 / 6 |
| 69NATA12 | 668 / 668 / 0 | **14** | 0 | 39 | 2659 / 2659 / 0 |
| 69SINCER | 6342 / 6316 / 26 | **298** | 2 | 1709 | 19009 / 18640 / 369 |
| TEST(靶场) | 8 / 8 / 0 | **0** | 0 | 0 | 24 / 24 / 0 |

**合计 3,284 张活手工凭证 / 16,981 行分录。样本充足,不是靠一两张脑补。**
TEST 账套里 8 张全是 `IV` 销售自动凭证(`SRCJNL=''`、`CREDAT=None`,像是导入/还原进去的),
**手工凭证一张都没有** —— 靶场造样本时要从零起。

### 代表性单据完整转储

**① JV6801-002 — 最小两行凭证(6902ASC,GLJNL recno 692)**

```
GLJNL.JNLTYP  = '00'          GLJNL.REVERSE = ' '        GLJNL.POSTID  = '        '
GLJNL.BATCH   = '      '      GLJNL.TRNSTAT = 'P'        GLJNL.POSDAT  = None
GLJNL.VOUDAT  = 2025-01-31    GLJNL.DOCSTAT = 'N'        GLJNL.USERPRN = '        '
GLJNL.VOUCHER = 'JV6801-002  ' GLJNL.CREBY  = 'BIT9    ' GLJNL.PRNDAT  = None
GLJNL.REFNUM  = '            ' GLJNL.CREDAT = 2025-02-19 GLJNL.PRNCNT  = None
GLJNL.SRCJNL  = 'GL  '        GLJNL.USERID  = 'BIT9    ' GLJNL.PRNTIM  = '     '
GLJNL.DESCRP  = 'บันทึก\xa0ภงด.53(เพิ่มเติม)\xa0เดือน\xa001/68#DELTAMAX     '
                              GLJNL.CHGDAT  = 2025-02-19 GLJNL.AUTHID  = '        '
                                                         GLJNL.APPROVE = None
-- GLJNLIT recno 1777: VOUCHER='JV6801-002  ' SEQIT=' 2' VOUDAT=2025-01-31
   ACCNUM='5210-11        ' DEPCOD='    ' JOBCOD='      ' PHASE='    ' COSCOD='    '
   DESCRP=<同头> TRNTYP='0' AMOUNT=18796.79 CHGDAT=2025-02-19 CHGTIM='1509'
   ADJUST=' ' CHGACCFROM='               '
-- GLJNLIT recno 1778: 同上,ACCNUM='2132-03        ' TRNTYP='1' AMOUNT=18796.79
>> DR=18796.79  CR=18796.79  balanced
```

**② JV6902-002 — 多借多贷(4 行,2 借 2 贷,金额不成对)**

```
JNLTYP='00' VOUDAT=2026-02-28 SRCJNL='GL  ' CREDAT=CHGDAT=2026-03-07 CREBY=USERID='BIT9'
DESCRP='ค่าแรง/เงินสมทบประกันสังคมล่าม\xa03\xa0ราย(SPT)#02/69   '
  5140-10  TRNTYP='0' 36000.00   CHGTIM='1640'
  5310-09  TRNTYP='0'  1800.00
  2131-04  TRNTYP='1'  3600.00
  5140-10  TRNTYP='1' 34200.00      >> DR=37800.00 CR=37800.00
```

注意:**同一科目可以在一张凭证里既借又贷**(5140-10 出现两次),不能按科目去重。

**③ PV680604-001 — 付款日记账(JNLTYP=01)**

```
JNLTYP='01' VOUDAT=2025-06-04 CREDAT=CHGDAT=2025-09-10 DESCRP='Bank\xa0fee'
  5360-04 TRNTYP='0' 800.00 CHGTIM='1557' / 1113-12 TRNTYP='1' 800.00
```

**④ RV69T04-001 — 收款日记账(JNLTYP=02)**

```
JNLTYP='02' VOUDAT=2026-04-03 CREDAT=CHGDAT=2026-04-06 CREBY='BIT9'
DESCRP='รับคืนภาษีมูลค่าเพิ่ม(สรรพากรพื้นที่)#01/2569'
  1113-02 TRNTYP='0' 3054551.14 CHGTIM='1418' / 1155-03 TRNTYP='1' 3054551.14
```

**⑤ PV68T01-003 — 带进项税的手工凭证(会同时写 ISVAT)**

```
GLJNL : JNLTYP='01' VOUCHER='PV68T01-003 ' SRCJNL='GL  ' VOUDAT=2025-01-10
        DESCRP='ค่าบริการMOU-SPTฝ่ายผลิต(11/12/24-25/12/24)'
GLJNLIT: 1155-02 '0' 6970.88 / 5140-10 '0' 99584.01 / 1113-02 '1' 103567.37 / 2132-03 '1' 2987.52
ISVAT  : VATREC='P' VATTYP=' ' RECTYP=' ' VATPRD=2025-01-01 VATDAT=2025-01-10
         DOCDAT=2025-01-10 DOCNUM='PV68T01-003 ' REFNUM='68/01 004      '
         DEPCOD='0001' AMT01=99584.01 VAT01=6970.88 AMT02=0.0 VAT02=0.0 AMTRAT0=0.0
         SELF_ADDED=' ' HAD_MODIFY='Y' DOCSTAT='N' TAXID='0105557163165  '
         ORGNUM=0 PRENAM='บจก.           ' NEWNUM='          ' LATE=' '
```

---

## 2. 落表清单

**手工凭证只碰 2 张表(必写),外加 1 张可选。跟采购/销售相比,少了整整一条子账链。**

### 2.1 必写:GLJNL(凭证头,恰好 1 行)

| 表 → 字段 | 值来源 | 证据 |
|---|---|---|
| GLJNL.JNLTYP | 常量,取自 ISRUN `DOCTYP='GL'` 行的 DOCCOD;`前缀→JNLTYP` 强绑定 | 920/920 一致,0 例外 |
| GLJNL.BATCH | 恒 `'      '` | 11628/11628 空 |
| GLJNL.VOUDAT | 派生:凭证日期(公历 date),= 会计要记账的那天 | 与行 VOUDAT 100% 相等 |
| GLJNL.VOUCHER | **调用方自定字符串**(见 §3),C(12) | ISRUN GL 行 DOCNUM 全空 |
| GLJNL.REFNUM | 恒 `'            '` | 手工 0/920 非空;自动 0/10708 非空 |
| GLJNL.SRCJNL | **常量 `'GL  '`** —— 手工凭证唯一标记 | 判别式,双向 0 误差 |
| GLJNL.DESCRP | 用户输入,C(50);泰文词间空格是 cp874 `0xA0` 不是 `0x20` | 3284/3284 非空 |
| GLJNL.REVERSE | 恒 `' '`(全库无样本,见 §5) | 3284/3284 |
| GLJNL.TRNSTAT | 常量 `'P'` | 11628/11628 |
| GLJNL.DOCSTAT | 常量 `'N'`;`'C'` = 已作废 | 3282 个 N + 2 个 C |
| GLJNL.CREBY / USERID | Express 登录用户名 C(8),如 `'BIT9    '`/`'BIT5    '` | 每套 1–2 个值 |
| GLJNL.CREDAT / CHGDAT | 系统当天(**不是** VOUDAT);312/3284 张 VOUDAT < CREDAT(补记) | |
| GLJNL.POSTID / POSDAT / USERPRN / PRNDAT / PRNCNT / AUTHID / APPROVE | 全空/NULL,Express 从不写 | 11628/11628 |
| GLJNL.PRNTIM | 恒 `'     '` | |

### 2.2 必写:GLJNLIT(分录行,N ≥ 2 行)

| 表 → 字段 | 值来源 | 证据 |
|---|---|---|
| GLJNLIT.VOUCHER | 抄头 | |
| GLJNLIT.SEQIT | **不是行序号**,是过账角色槽位码 C(2);手工凭证同一账套内恒定(6902ASC/69ASIAR=`' 2'`,69ASIAMI/69MANAC5/69MANACC/69NATA12=`' 1'`,69SINCER 混) | 一张凭证内 3284/3284 恒定 |
| GLJNLIT.VOUDAT | 抄头,必须逐行相等 | 16981 行 0 不等 |
| GLJNLIT.ACCNUM | 用户选,C(15),必须是 GLACC 里 `ACCTYP='0'`、`STATUS='A'`、非任何账户的 PARENT | 手工行 0 违例 |
| GLJNLIT.DEPCOD / JOBCOD / PHASE / COSCOD | 手工凭证 16981 行里 16975 行全空(仅 69SINCER 6 行 DEPCOD='MIN ') | |
| GLJNLIT.DESCRP | 默认抄头;可逐行改(6902ASC 3954/4281 与头相同,327 行被改过);**从不为空** | |
| GLJNLIT.TRNTYP | `'0'`=借 / `'1'`=贷 | 只有这两个值 |
| GLJNLIT.AMOUNT | N(13,2),**恒正**,方向只看 TRNTYP | 16981/16981 ≥ 0,0 个负数 |
| GLJNLIT.CHGDAT / CHGTIM | 存盘时间;CHGTIM = `'HHMM'` 4 位数字,同一凭证内一致 | 4281/4281 长度 4 全数字 |
| GLJNLIT.ADJUST / CHGACCFROM | 恒空 | 手工行 100% |

### 2.3 可选:ISVAT(带税的手工凭证才写)

**6902ASC:153/920 = 16.6% 的手工凭证带 ISVAT 行,共 192 行**,其中 152 张是 JNLTYP='01'(付款日记账 → 进项税)。

| 表 → 字段 | 值来源 |
|---|---|
| ISVAT.DOCNUM | = GLJNL.VOUCHER |
| ISVAT.VATREC | `'P'`=进项 / `'S'`=销项(手工样本 192/192 全 `'P'`) |
| ISVAT.VATTYP / RECTYP / LATE / SELF_ADDED | **全 `' '` 空白** —— 这正是与单据产生的 VAT 行的区分点(单据行 RECTYP='3'/'9'/'5'/'0',SELF_ADDED='N'/'Y') |
| ISVAT.VATPRD | 申报所属月的 **1 号**(192/192 day=1);117 张 = VOUDAT 同月,74 张跨月(补报) |
| ISVAT.VATDAT / DOCDAT | 税票日期 / 单据日期,可与 VOUDAT 不同 |
| ISVAT.REFNUM | 对方票号,192 个全不重复 |
| ISVAT.AMT01 / VAT01 | 税基 / 税额;AMT02/VAT02/AMTRAT0 基本为 0 |
| ISVAT.TAXID / PRENAM / ORGNUM / DEPCOD | 对方税号/称谓/分支/部门 |
| ISVAT.HAD_MODIFY | `'Y'`(175)/`' '`(17) |
| ISVAT.NEWNUM / DOCSTAT | `'          '` / `'N'` |

### 2.4 明确不碰的表(已逐表反证)

对 920 个手工凭证号扫全表(`11_templates_isolation.py`):

```
APTRN(8455行,DOCNUM+REFNUM): 0 命中     ARTRN(1179行): 0
BKTRN(2360行): 0     APRCPIT(6498行): 0     ARRCPIT(470行): 0     STTRN: 0
APBAL / ARBAL:根本没有 DOCNUM 列,与凭证号无关
ISRUN:GL 行的 DOCNUM 全空(8 个账套一致),不取号
```

文件 mtime 交叉印证:6902ASC 最后一张手工凭证 CHGDAT=2026-05-18,`GLJNL.DBF`/`GLJNLIT.DBF`
mtime = 2026-05-18 19:47,而 **`ISRUN.DBF` mtime = 2026-03-20 13:17**(早两个月)。
69ASIAMI/69ASIAR/69SINCER 同样是 ISRUN 明显更旧。**存手工凭证不写 ISRUN,实锤。**

### 2.5 GLBAL(月桶)——不必写,但要知道它会脏

- **内容确实等于 GLJNLIT 的聚合**:6902ASC 的 CY 桶(DEBIT1..12/CREDIT1..12)对 2025 年分录,
  1323/1323 个非零格 **100% 相等,0 差异**;69SINCER 同样 862/862 = 100%。手工凭证的金额也在里面。
- **但它不是每次存盘递增维护的**:69ASIAMI `GLBAL.DBF` mtime 10:13 比 `GLJNL.DBF` 13:32 **早 3 小时 19 分**,
  69ASIAR 早 21 分。若每笔存盘都 bump,GLBAL.mtime 不可能早于 GLJNL.mtime。
- 与之吻合:GLBAL 越「新鲜」对得越准 —— 6902ASC/69SINCER(GLBAL mtime ≥ GLJNL)CY 100%;
  69ASIAMI(GLBAL 更旧)CY 仅 13.1%。
- **NY(次年)桶烂得更厉害**:6902ASC 的 2026 年分录 vs NY 桶,709 个格对不上(69SINCER 只差 16 格)。
- GLBAL 按 (ACCNUM, DEPCOD, JOBCOD) 建行;`DEPCOD=''` 那 291 行才是有数的(174 行非零),其余部门行几乎全零。
  **分录用到的每个 (ACC,DEP,JOB) 组合在 GLBAL 里都已有行,0 缺失**(三个账套均如此)。
- `CALSTA` 是逐期「已计算」标志串(长度 12/13/14/15/16/17/22 都出现过),值几乎全 `'1'`,
  偶见 `'111111111111101'` 这种带 `0` 的。语义未证实。

**结论(诚实边界)**:GLBAL 是可重算缓存;推手工凭证**大概率不需要**自己维护它。
但「Express 报表是读 GLBAL 还是读 GLJNLIT」这一点数据上判不出来,必须靠 §6 的金样本实测定案。

---

## 3. 取号规则

**手工总账凭证没有机器取号 —— 凭证号是会计手打的自由文本。**

三条独立证据:

1. ISRUN 里 `DOCTYP='GL'` 的行,`DOCNUM` 字段在 **8 个账套全部为 10 空格**
   (而 RR=`'0000050'`、IV=`'0000020'`、PS=`'0000073'` 都在正常递增)。
2. ISRUN.DBF mtime 明显早于 GLJNL.DBF mtime(§2.4)。
3. 号码形态发散:6902ASC 920 张手工凭证有 **21 种不同形状**,包括 `JV6801-004`、`JV680118-04`、
   `JV680131-001`、`JVIN0004470`、`JVRE67L02009`、`JVRN68080706`、`JVVR6801-002`、`PV9L01-003`。
   机器取号做不出这个。

### ISRUN 里对应的行(只提供前缀,不提供流水)

| DOCTYP | DOCCOD | PREFIX | SHORTNAM | POSDES2 | DOCNUM |
|---|---|---|---|---|---|
| GL | 00 | JV | ทั่วไป | General Journal | (空) |
| GL | 01 | PV | จ่าย | Payment Journal | (空) |
| GL | 02 | RV | รับ | Receive Journal | (空) |
| GL | 03 | SV | ขาย | Sales Journal | (空) |
| GL | 04 | UV | ซื้อ | Purchase Journal | (空) |
| GL | 05 | PC / JO / JB | เงินสดย่อย 等 | Petty Cash | (空) |

`DOCCOD` **就是** `JNLTYP`。00–04 是 Express 固定的五本账,05 起是各账套自建
(69MANAC5/69MANACC 还有 06=JC、07=JD、08=JE、10=PC、11=RD;69ASIAMI 有 `DOCCOD='A'`→AV)。
**取号前必须读目标账套的 ISRUN,不能硬编码前缀表。**

### 各套实际用了哪几本账(手工凭证)

| 账套 | JNLTYP 分布 |
|---|---|
| 6902ASC | 01=698, 00=181, 02=41 |
| 69ASIAMI | 03=242, 01=159, 00=146, 02=14 |
| 69ASIAR | 03=484, 02=243, 01=95, 00=44 |
| 69MANAC5 | 02=457, 00=72, 01=38 |
| 69SINCER | 01=141, 00=84, 05=65, 02=7, 04=1 |

### 实际编号惯例(6902ASC,821/920 匹配)

`{前缀}{佛历年后两位}{可选标记}{月}-{流水}`,例:`PV68T09-031` = 付款日记账 · BE2568 · 标记 T · 09 月 · 第 031 号。
标记位是人为分组(出现过 `T`/`L`/`A`/`M`,含义未知,不是机器语义)。**87/101 组内流水从 001 连续,14 组有断号。**

### 写入方该怎么取号

自己生成、自己保唯一。可机械执行的取号算法:

```python
prefix = ISRUN[DOCTYP='GL', DOCCOD=jnltyp].PREFIX          # 'JV'/'PV'/'RV'/...
be_yy  = f"{voudat.year + 543 - 2500:02d}"                  # 2026 -> '69'
mm     = f"{voudat.month:02d}"
stem   = f"{prefix}{be_yy}{mm}-"
used   = {v[len(stem):] for v in live_vouchers if v.startswith(stem)}
serial = max((int(x) for x in used if x.isdigit()), default=0) + 1
voucher = f"{stem}{serial:03d}"                             # 补空格到 C(12)
```

**唯一性是硬约束且 Express 在守**:8 个账套的活头 VOUCHER **全部无重复**
(6902ASC 11628 条 = 11628 个不同号)。

**⚠️ 软删陷阱(直接命中 `dbf-soft-deleted-rows-fake-success` 那条血泪)**:
6902ASC 有 **3753 个凭证号同时存在于活行和软删行**。因为 Express 改单 = 软删旧头旧行 + 追加新头新行
(6902ASC 有 35,024 行软删分录的头还活着)。所以:

- 判「这个号已被占用」→ **只数活行**。带上软删行会误报「已存在」而拒写。
- 判「我上次推的那张还在不在」→ **只数活行**。

---

## 4. 配平校验(可机械执行)

设 `H` = 一条 GLJNL 活行(`SRCJNL=='GL  '`),`L` = `GLJNLIT` 中 `VOUCHER==H.VOUCHER` 的全部**活**行。

```python
S   = lambda v: v.strip() if isinstance(v, str) else v
D   = lambda x: Decimal(str(x if x is not None else 0))
dr  = sum(D(l.AMOUNT) for l in L if S(l.TRNTYP) == '0')
cr  = sum(D(l.AMOUNT) for l in L if S(l.TRNTYP) == '1')

A1  len(L) >= 2                                        # 3284/3284 通过
A2  dr == cr                                           # 3284/3284 通过,Decimal 相等,不留容差
A3  dr > 0                                             # 3282/3284(2 例外 = DOCSTAT='C' 作废单,AMOUNT 全 NULL)
A4  all(S(l.TRNTYP) in ('0','1') for l in L)           # 16981/16981
A5  all(D(l.AMOUNT) >= 0 for l in L)                   # 16981/16981 —— 方向只看 TRNTYP,不看正负
A6  all(l.VOUDAT == H.VOUDAT for l in L)               # 16981/16981
A7  all(S(l.VOUCHER) == S(H.VOUCHER) for l in L)
A8  len({repr(l.SEQIT) for l in L}) == 1               # 3284/3284,一张凭证内 SEQIT 恒定
A9  all(S(l.DESCRP) != '' for l in L) and S(H.DESCRP) != ''
A10 S(H.SRCJNL) == 'GL' and S(H.TRNSTAT) == 'P' and S(H.DOCSTAT) == 'N'
A11 S(H.JNLTYP) == ISRUN[DOCTYP='GL', PREFIX==S(H.VOUCHER)[:2]].DOCCOD   # 920/920
A12 all(S(l.CHGTIM).isdigit() and len(S(l.CHGTIM)) == 4 for l in L)
A13 GLACC[S(l.ACCNUM)] 存在 ∧ ACCTYP=='0' ∧ STATUS=='A' ∧ ACCNUM 不是任何账户的 PARENT   # 0 违例
A14 (S(l.ACCNUM), S(l.DEPCOD), S(l.JOBCOD)) ∈ GLBAL 主键集合                            # 0 缺失
A15 若带税:sum(ISVAT[DOCNUM==VOUCHER].VAT01+VAT02) 应等于某一/若干条进项税科目行的 AMOUNT
    (PV68T01-003:VAT01=6970.88 = 1155-02 借方行 6970.88 ✓)
A16 唯一性:count(活 GLJNL where VOUCHER==v) == 1     # 8/8 账套通过
```

**GLBAL 层的对账(报表级,不是单据级)**:

```python
# 对某年 Y、账户 a、月 m
sum(GLBAL[a, dep, job].DEBITm  for all dep,job) == sum(l.AMOUNT for l in 全部活分录
                                                       if l.ACCNUM==a and l.VOUDAT.year==Y
                                                       and l.VOUDAT.month==m and l.TRNTYP=='0')
# 6902ASC CY vs 2025:1323/1323 格通过;69SINCER:862/862 通过(浮点,容差 0.005)
```

注意 GLBAL 字段是 VFP `'B'`(double),必须带 `0.005` 容差比;GLJNLIT.AMOUNT 是 `N(13,2)`,可以用 Decimal 严格比。

**反例验证已做**:上表 A1–A16 是在 3284 张真凭证上跑出来的,不是照着代码猜的;
`16_final_checks.py` 输出的异常只有 `chgdat_mismatch:28`(头行 CHGDAT 微差)、`voudat_after_credat:312`(补记,正常)、
`no_lines:8`(69SINCER 有 8 张 DOCSTAT='N' 的头**没有任何分录行** —— Express 自己不保证头行完整性,读取方要防这个空)、
`zero_total:2`(作废单)。

---

## 5. 与采购/销售单的异同

### 少了什么(这是它简单的原因)

| 采购 RR / 销售 IV 要写 | 手工凭证 |
|---|---|
| ISRUN 取号 + 回写 DOCNUM | **不做**(GL 行 DOCNUM 恒空) |
| APTRN / ARTRN 单头 | **不写** |
| APBAL / ARBAL 供应商/客户月桶 | **不写** |
| STTRN / STCRD 库存流水 | **不写** |
| APMAS / ARMAS 主档余额联动 | **不碰** |
| ISVAT 进/销项税 | **可选**(6902ASC 16.6% 才写) |
| 对手方档案(供应商/客户码)必填 | **无对手方概念** |
| RECTYP 现金/赊账分流 | **无此字段** |
| 库存成本/COGS 结转 | **不涉及** |

### 多了/不一样的

1. **`SRCJNL='GL  '`** —— 唯一由手工凭证使用的值。单据链绝不能被污染:推手工凭证时这个字段必须写 `'GL  '`,
   推单据时必须留空。
2. **JNLTYP 由调用方选**。单据的 JNLTYP 是 ISINFO 配死的(`CREPURJNL='04'`、`CRESALJNL='03'`、
   `OTHEXPJNL='01'`、`ARRCPJNL='02'`、`BNKMOVJNL='00'` …);手工凭证由会计自己挑哪本账。
3. **凭证号自由文本**,没有系统计数器给你抢锁 —— 唯一性由写入方保证。
4. **借贷可多对多**,不像单据那样有固定的 2–4 行配方。样本里最多 25 行,283 张是最小的 2 行。
5. **ISVAT 行的指纹不同**:手工凭证产生的 VAT 行 `RECTYP=' '` 且 `SELF_ADDED=' '`;
   单据产生的 `RECTYP∈{'3','9','5','0'}`、`SELF_ADDED∈{'N','Y'}`。别混。

### 坑

- **`SRCJNL=''` ≠「来自 ISRUN 单据」**。6902ASC 有 24 张 `FA` 开头的凭证(`FA68010001`,
  DESCRP=`คิดค่าเสื่อมสินทรัพย์ถาวร` 计提折旧),`SRCJNL=''`、`JNLTYP='00'`,但 `FA` 不在 ISRUN 里
  —— 固定资产模块是第三个自动来源。判「手工」只能正向用 `SRCJNL=='GL'`,不能用 `SRCJNL==''` 取反。
- **`SEQIT` 不是行号**。它是过账角色槽位码(C(2),值域 `0-9a-f`):IV 恒 `'2'`→应收 1130-01、`'5'`→收入 4100-10;
  RR 用 `'0'`(费用)/`'3'`(进项税 1155-02)/`'6'`(应付 2120-01)/`'8'`(预扣 1151-01)。
  **手工凭证没有配方,Express 写一个每账套恒定的常量**(`' 1'` 或 `' 2'`)。同一账套内为何有两种值
  (69SINCER 282 张用 `' 2'`、8 张用 `' 1'`),**数据上判不出来 —— 未证实**。
  写入方照抄目标账套现有手工凭证的众数值即可,别自己发明。
- **对齐方式不一致**:6902ASC 写右对齐 `' 2'`,TEST 的自动单写左对齐 `'2 '`。别把 SEQIT 当可比较的键。
- **泰文空格是 `0xA0` 不是 `0x20`**。DESCRP 里 `'บันทึก\xa0ภงด.53'` —— Express 泰文输入法打出的是 cp874 不换行空格。
  做去重/指纹匹配时会咬人。
- **改单 = 软删+追加**,不是原地改。6902ASC 35,537 行软删分录里 35,024 行的头还活着。
  任何「这单存在吗/推过吗」的判断都必须 `dbf.is_deleted(r)` 过滤。
- **作废 = `DOCSTAT='C'` + AMOUNT 置 NULL**,凭证号保留占位(69SINCER 2 例)。
  读取方要防 `AMOUNT is None`(69SINCER 就有 NULL 导致 `float()` 抛 TypeError)。
- **CY/NY 年桶映射不能靠目录名猜**。目录叫 `2569`(BE2569=2026),但 6902ASC 的 CY 桶对的是 **2025** 年;
  69MANACC 的 NY 桶才对 2026(93.9%)。要判「当前年」只能靠 GLBAL 与 GLJNLIT 的对账反推,
  或从 Express 公司注册表读。ISINFO 里**没有**财年字段(只有 `YEARTHAI='1'`)。
- ISINFO 的 `TAKADJJNL='30'` 指向一个 ISRUN 里不存在的 JNLTYP —— 配置可以指错,别假设 ISINFO 的值一定合法。

---

## 6. P2-B 施工建议

### 难度评级:**低–中**(明显低于采购/销售)

理由:必写表只有 2 张(GLJNL + GLJNLIT),可选 1 张(ISVAT);无取号回写、无子账余额联动、无库存、无对手方档案;
配平规则简单到能写成一行断言;CDX 后台重建这条最硬的路已经在
`docs/integrations/express-push/32-v3-background-cdx-closed-loop.md` 打通(Harbour DBFCDX + GTNUL 编译的
`cdx_reindex_runner`),GLJNL/GLJNLIT 已在 V3 Step A 的 9 表清单里跑过 REINDEX 0 失败。

### 最大风险点(按严重度排序)

1. **凭证号冲突 / 幂等**(P0)。没有 ISRUN 计数器,两个并发写入方会撞号,而 Express 靠唯一性维持账本可读。
   必须:① 写前在**活行**里查号(排除软删,否则 3753 个复用号会让你误判「已存在」而拒写);
   ② 写后**读回校验**确认恰好一条活行;③ 幂等钥匙用 `(账套目录, VOUCHER)`。
2. **GLBAL 脏导致「推成功但报表看不见」**(P0 风险,未证)。GLBAL 不随存盘更新(mtime 反证),
   但 Express 报表读哪一边未知。若报表读 GLBAL,推完不重算 = 典型的假成功。**必须在金样本实验里定案**。
3. **科目非法**(P1)。挑到 `ACCTYP='1'` 的汇总科目或某科目的父节点,Express 报表会错乱。
   写前必须过 A13/A14 两道闸。
4. **期间已关账**(P1)。数据里看不出 Express 的关账锁在哪(`CALSTA` 疑似但未证)。
   往已申报月补记会污染 ภ.พ.30。
5. **JNLTYP 硬编码**(P1)。各账套的 GL 本账配置不同(69MANAC5 有 11 本),硬编码 `'00'..'05'` 会在别家账套错本账。
   必须每次读目标 ISRUN。
6. **cp874 / `0xA0` 编码**(P2)。写 DESCRP 用普通空格不会崩,但和 Express 里手打的记录长得不一样,做去重会漏。

### 验证方案(TEST 账套:`\\Accserver\d$\ACCOUNT\69EXP\test`)

**第 0 步 · 金样本(先做,不写一行代码)**

真样本是唯一 ground truth。让 Owner/会计在 **Express UI 里手工录一张 JV**(2 行,如 借 53-xx / 贷 11-xx,金额 100.00)。
录之前把 TEST 目录整目录快照,录之后再快照,**逐表 diff**。
这一步同时定案三件事:① 到底动了哪几张 DBF(验证「只有 GLJNL+GLJNLIT」这个结论);
② **GLBAL 会不会被创建/更新**(TEST 现在 GLBAL 物理 0 行,信号极干净 —— 如果录完 GLBAL 长出行,
就是存盘时写;不长,就是重算缓存);③ 新账套里 Express 自己写的 SEQIT 是 `' 1'` 还是 `' 2'`。

**第 1 步 · 造(小助手写)**

按 §2 的三列表填字段,VOUCHER 用 §3 算法生成,追加 1 行 GLJNL + N 行 GLJNLIT → 跑 `cdx_reindex_runner`
重建 `GLJNL.CDX` / `GLJNLIT.CDX`(+ 带税时 `ISVAT.CDX`)→ 索引回查 `DbSeek(VOUCHER)` 命中才算写成功。

**第 2 步 · 读回验(机械闸,不看代码「应该对了」)**

```
① dbf 重开 → VOUCHER 在活行里恰好 1 条,且 SRCJNL=='GL  '
② N 行分录全部回读到,A1–A16 全绿(直接复用 16_final_checks.py 的断言)
③ 反向闸:APTRN/ARTRN/APBAL/ARBAL/STTRN/ISRUN 的行数与 mtime 与写前完全一致(证明没污染单据链)
④ ISRUN.DOCNUM 逐行与写前 byte-identical
⑤ 真 Express.exe UI 里按凭证号能查到,借贷合计与录入一致 —— 截图为证(参照 V3 Step A 已用过的验收口径)
```

**第 3 步 · 回滚**

写之前对 TEST 目录做整目录副本(`GLJNL.DBF/.CDX`、`GLJNLIT.DBF/.CDX`、`ISVAT.DBF/.CDX`、`GLBAL.DBF/.CDX`)。
回滚 = 拷回副本。**不要用软删回滚**(会留下 §3 那个「号被占用」的判断陷阱),也**绝不 pack**。

**第 4 步 · 反证(防假绿)**

故意造 4 张坏单,确认写入方拒绝而不是写进去:借贷不平 / AMOUNT 为负 / ACCNUM 指到 ACCTYP='1' 的汇总科目 /
VOUCHER 与已有活行重号。四条全被拦才算闸有效。
