# 41 · Express 客户收款单(รับชำระหนี้ / AR Receipt)只读逆向

> 逆向日期 2026-07-26 · **只读逆向产物**:全程 `dbf.Table(..., codepage='cp874')` + `dbf.READ_ONLY`,
> 零写入 / 零 pack / 零删除。结论全部来自真账套样本,不是照代码或文档推测。
> 脚本与 DBF 只读副本留在逆向窗口 scratchpad:
> `C:\Users\skin3\AppData\Local\Temp\claude\C--Users-skin3-Desktop-pearnly-app\0a2cac22-1395-44cb-909d-b50e60da19d4\scratchpad\doctype_recon\`
> - `introspect.py` 表结构 / `deep_dump.py` 单据跨表全字段转储(UTF-8,泰文可读)
> - `isrun_dump.py` + `cq_analysis.py` 取号表与收款渠道解码
> - `receipt_recon.py` 全账套盘点 / `roles.py` SEQIT 槽位与 ARBAL 桶校验
> - `invariants.py`(v1,已被证伪的假设) → `invariants_v2.py`(修正版断言电池,第 4 节即它的输出)
> - `data/<账套>/*.DBF` 为本地只读副本,`out/*.txt` 为分析产物

---

## 1. 样本盘点

**结论:样本充足,不是「无样本」。** 8 个账套里 4 个有收款单,共 **1077 张活单 + 3 张软删单**。

| 账套 | 收款单(活/软删) | ARTRN 物理/活 | ARRCPIT 物理/活 | ARRCPCQ 物理/活 | 备注 |
|---|---|---|---|---|---|
| 6902ASC | **330 / 3** | 1179/1167 | 470/448 | 1852/1023 | 外币出口商,带汇兑损益/手续费/预收冲抵 |
| 69SINCER | **728 / 0** | 3388/3388 | 2159/2159 | 885/885 | 内销零售,单发票为主,120 张部分收款 |
| 69ASIAMI | **16 / 0** | 33/33 | 16/16 | 18/1 | 服务业:**代扣税 WHT + 收款基础销项税** |
| 69MANAC5 | **3 / 0** | 495/493 | 4/3 | 798/341 | 收款单少,ARRCPCQ 大量属于 OI 其他收入单 |
| 69MANACC / 69NATA12 / 69ASIAR | 0 / 0 | — | 0/0 | 有行但属别的单据类型 | 无收款单 |
| TEST 靶场 | 0 / 0 | 8/8 | 0/0 | 0/0 | 科目表 = SINCER 同构,可做对照/施工靶场 |

**代表性单据(全字段已转储,见 `out/deep_*.txt`)**

**① 最简形态 6902ASC / RE68L01-001**(一张收款冲三张发票,银行进账 + 手续费 + 汇兑收益)

```
ARTRN:  RECTYP='9' DOCNUM='RE68L01-001' DOCDAT=2025-01-15 CUSCOD='AME3' SLMCOD='WILSON'
        DUEDAT=2025-01-15 BILNUM='~' AMTRAT0=12565677.28 NETAMT=12565677.28
        CHQRCV=12565677.28 CHQPAS=12565677.28 IVCAMT=12565677.28 CSHRCV=0 TAX=0 VATAMT=0
        CMPLAPP='Y' CMPLDAT=2025-01-15 DOCSTAT='M' SRV_VATTYP='-' POSTGL='' FLGVAT=''
        USERID='BIT9' CHGDAT=2025-02-15   (其余 30+ 字段全空)
ARRCPIT: (RE68L01-001, IV0004371, '3', 9105618.07) (…, IV0004367, '3', 2130712.40) (…, IV0004370, '3', 1329346.81)
ARRCPCQ: ('L4RE68L01-00', 12612357.72) ('F1RE68L01-00', 365.90) ('R0RE68L01-00', -47046.34)
GLJNL:   JNLTYP='02' VOUCHER='RE68L01-001' VOUDAT=2025-01-15 TRNSTAT='P' DOCSTAT='N'
         DESCRP='รับชำระหนี้   \xa0AMER SPORTS EUROPEAN CENTER AG'
GLJNLIT: 1113-09 DR 12612357.72 | 5360-04 DR 365.90 | 1130-01 CR 12565677.28 | 4200-20 CR 47046.34
BKTRN:   BKTRNTYP='bR' CHQNUM='L4RE68L01-00' BNKACC='F2' CHQSTAT='19' AMOUNT=12612357.72
         VOUCHER='RE68L01-001' REFDOC='~' JNLTRNTYP='0' CUSCOD='AME3'
```

**② 代扣税 + 收款基础销项税 69ASIAMI / REMB6811-002**(泰国服务业最常见形态)

```
ARTRN:  NETAMT=160500 TOTAL=150000 VATAMT=10500 NETVAL=150000 FLGVAT='2' VATDAT=2025-11-01
        CHQRCV=156000 CHQPAS=156000 TAX=4500(客户代扣 3%) IVCAMT=160500 CMPLAPP='Y' DOCSTAT='M'
ARRCPIT: (REMB6811-002, IV681031-001, '3', 160500.00, VATAMT=10500)
ARRCPCQ: ('CHREMB6811-0', 156000)
GLJNLIT: SEQIT' 2' 11-01-01-01 DR 156000 | ' 3' 11-05-01-02 DR 4500(ภาษีถูกหัก ณ ที่จ่าย)
         ' 6' 11-05-03-00 CR 160500(该客户 ARMAS.ACCNUM) | ' 8' 11-05-04-03 DR 10500 | ' 9' 11-05-04-02 CR 10500
ISVAT:   VATREC='S' RECTYP='9' DOCNUM='REMB6811-002' REFNUM='MB 68-11-002' AMT01=150000 VAT01=10500
```

**③ 纯预收冲抵(不动钱)6902ASC / RE68L01-012**

```
ARTRN:  NETAMT=0 ADVNUM='AI0004393' ADVAMT=5866134.57 CMPLAPP='Y' DOCSTAT='N'(无 ARRCPCQ / 无 BKTRN)
ARRCPIT: (…, 'AI0004393', RECTYP='0', 5866134.57)   ← 消耗预收
         (…, 'IV0004393', RECTYP='3', 5866134.57)   ← 冲销发票
GLJNLIT: ' 4' 2133-01 DR 5866134.57(เงินรับล่วงหน้า) | ' 6' 1130-01 CR 5866134.57
```

**④ 收款不足额(单头挂欠)6902ASC / RE68L11-041**

```
ARTRN:  IVCAMT=6274225.20 NETAMT=124888.04 REMAMT=6149337.16 CMPLAPP='N' DOCSTAT='R'
ARRCPIT: (…, IV0004279, '3', 6274225.20)  ← 记的是「选中的发票全额」
GLJNLIT: AR 只贷 124888.04(实收) —— 子账(发票 RCVAMT=全额/CMPLAPP='Y')与 GL 差 REMAMT
```

**⑤ 不挂发票的挂账收款 6902ASC / RE69L02-018**:有 ARTRN + ARRCPCQ + GL(AR 贷 3,460,380.30),
**ARRCPIT 0 行**——钱进来但没指定冲哪张票,客户 AR 直接变贷方。

---

## 2. 落表清单(一张收款单 touches 的表)

| 表 | 行数 | 字段 → 值来源 |
|---|---|---|
| **ARTRN**(单头) | 1 | `RECTYP='9'`常量 · `DOCNUM`取号 · `DOCDAT/DUEDAT/CMPLDAT`=收款日(三者相同,1077 张仅 7 例外) · `CUSCOD`客户 · `BILNUM='~'`常量(1077/1077) · `SRV_VATTYP='-'`常量 · `NETAMT`=实收+代扣 · `CSHRCV`(现金渠道)/`CHQRCV`(其余渠道)/`CHQPAS`=CHQRCV · `TAX`=客户代扣 WHT · `IVCAMT`=本单冲销总额 · `ADVNUM/ADVAMT`=动用的预收单号/金额 · `REMAMT`=选中额-实收(不足额时) · `CMPLAPP`='Y'(REMAMT=0)/'N' · `DOCSTAT`='M'完成/'N'/'R'有欠/'C'作废 · `FLGVAT='2'+TOTAL/VATAMT/NETVAL/VATDAT`仅收款基础销项税账套 · `SLMCOD/DEPCOD`可选 · `USERID/CHGDAT`审计 · `POSTGL=''` · `AMTRAT0` 仅 6902ASC(外币)使用 · 其余 30+ 字段全空 |
| **ARRCPIT**(冲销明细) | 每张被冲单据 1 行 | `RCPNUM`=收款单号 · `DOCNUM`=被冲单号 · `RECTYP`='3' 赊销发票 / '0' 预收单(AI)· `RCVAMT`=本次冲销额(不足额收款时为发票全额)· `VATAMT` 仅收款基础 VAT 填 |
| **ARRCPCQ**(收款方式行) | 每个渠道 1 行,**可 0 行** | `RCPNUM` · `CHQNUM`= ZR 渠道 PREFIX(2 位)+ RCPNUM 截到 10 位(**非唯一**,1023 行只有 458 个不同值)· `RCVAMT` 正=借方(进钱/手续费)、负=贷方(汇兑收益/折让)。ASIAMI 15/16 张单完全没有此表行 → **此表不是 GL 的事实源,是收款方式明细** |
| **GLJNL**(凭证头) | 1 | `VOUCHER`=DOCNUM · `VOUDAT`=DOCDAT · `JNLTYP`=ISRUN['RE'].JNLTYP='02' · `DESCRP`=ISRUN.JNLEXP 求值 = `'รับชำระหนี้   ' + PRENAM + chr(0xA0) + CUSNAM` · `TRNSTAT='P'` · `DOCSTAT='N'` · `CREBY/USERID`=操作员 · `CREDAT/CHGDAT`=录入日(**≠单据日**)· BATCH/SRCJNL/REVERSE/POSTID 空 |
| **GLJNLIT**(凭证行) | 2~n | `VOUCHER/VOUDAT` 同上 · `ACCNUM`:AR 腿=**ARMAS[CUSCOD].ACCNUM**;渠道腿=ISRUN(DOCTYP='ZR', PREFIX=渠道).ACCNUM01,**若该行 ACCNUM01 为空则取 BKMAS[ISRUN.SHORTNAM].ACCNUM**;WHT 腿=ZR 'TX' 渠道科目;预收腿=ZR 'M1/R' 类科目(2133-01)· `TRNTYP`='0' 借 / '1' 贷(**不是 'D'/'C'**)· `AMOUNT` N(13,2) 恒正 · `SEQIT` CHAR(2) 右对齐带前导空格:`' 2'`渠道腿 `' 3'`代扣税 `' 4'`预收 `' 6'`AR腿 `' 8'/' 9'`销项税转出对 · `DESCRP` 同凭证头 · `CHGTIM`='HHMM' · DEPCOD/JOBCOD/PHASE/COSCOD 空 |
| **BKTRN**(银行本票) | 0~n(仅当渠道 ISRUN.SHORTNAM 指向 BKMAS) | `BKTRNTYP='bR'` · `CHQNUM`=同 ARRCPCQ · `BNKACC`=ISRUN.SHORTNAM · `CHQSTAT='19'` · `JNLTRNTYP='0'` · `VOUCHER`=收款单号 · `REFDOC='~'` · `CUSCOD/NAME` · `TRNDAT/CHQDAT/GETDAT`=收款日 · `AMOUNT/NETAMT`=该渠道金额 · **(CHQNUM,BNKACC) 在两个账套里 100% 唯一** |
| **ISVAT** | 0~1(仅 FLGVAT='2') | `VATREC='S'` `RECTYP='9'` `DOCNUM`=收款单号 `REFNUM`=对应税单号 `AMT01/VAT01`=TOTAL/VATAMT `VATPRD/VATDAT` `TAXID/PRENAM`来自 ARMAS |
| **ARTRN(被冲发票行)** | 每张被冲发票 1 次 UPDATE | `RCVAMT` += 冲销额 · `REMAMT` = NETAMT-RCVAMT · `CMPLAPP`='Y'(全清)/'N' · `CMPLDAT`=收款日 |
| **ARBAL**(客户月桶) | 1 次 UPDATE | `RE<月>` / `RE<月>NY` += **NETAMT + ADVAMT**(实收+动用预收;不含 REMAMT) |
| **ISRUN** | 1 次 UPDATE | DOCTYP='RE' 行的 `DOCNUM` 计数器推进(见第 3 节) |
| **GLBAL** | 可选 | 派生缓存表(3245 行全零 + `CALSTA` 脏标志位串)。写者把 touched 科目的 CALSTA 对应位置 '1' 让 Express 重算即可,不必自己算余额 |
| 不参与 | — | ARTRNRM(备注,只见于发票)、ARBIL/ARBILIT(收款通知单)、STTRN/STCRD(收款不动库存)、ISTAX |

---

## 3. 取号规则

**ISRUN 里的那一行**(6902ASC 实测):

```
DOCTYP='RE' DOCCOD='' PREFIX='RE' DOCNUM='0000012' JNLTYP='02'
POSDES='รับชำระหนี้' POSDES2='Receipt'
JNLEXP="'รับชำระหนี้   ' + (ARMAS->PRENAM - '\xa0' - ARMAS->CUSNAM)"
ACCNUM01..12 全空(收款单的科目不由 ISRUN 定,由客户主档 + 渠道定)
```

- **自动号格式** = `PREFIX(2) + DOCNUM(7 位补零)`,例:69SINCER 里真实存在 `RE0000024`、`RE0000025`,
  而该账套 ISRUN 计数器 = `0000026` → **计数器语义是「下一个待用号」,不是「最后用过的号」**。
- **现实是人工号占绝对多数**:6902ASC 330 张全是 `RE{BE年2}{系列字母L/T/M}{月2}-{序3}`(如 RE68L01-001);
  69SINCER 726/728 是 `RE{BE年}{月}{日}-{序}`;69ASIAMI 用 `REMB6811-002`。
  ISRUN 计数器因此长期滞后(6902ASC 计数器停在 12,实际单号已到 RE69L02-036)。
- 收款单号本身**不含佛历/公历转换风险**:DOCDAT 存公历,佛历只出现在号码字符串里。
- **另一处「取号」**:ARRCPCQ.CHQNUM 与 BKTRN.CHQNUM = `渠道PREFIX + 收款单号截 10 位`;
  因 BKTRN 要求 (CHQNUM,BNKACC) 唯一,Express 会自行挪一位避撞(`RE68L01-005` → `L4RE68L01-05`),
  规则不稳定,写者应自己保证 BKTRN 唯一。
- **回写**:取号后把 ISRUN 该行 DOCNUM 推进到下一个值。人工号模式下 Express 也不回写(计数器滞后即证据),
  所以**写者必须以「ARTRN 里 DOCNUM 不存在」为唯一防撞判据**,ISRUN 只作兜底。

---

## 4. 配平校验(可机械执行 · 已在 1077 张真单上跑过)

`invariants_v2.py` 输出(违反数 / 总数,4 个有单账套合计):

| 断言(可直接当 companion 写后回读闸) | 违反 |
|---|---|
| **C1** `Σ ARRCPCQ.RCVAMT == CSHRCV+CHQRCV+INTRCV`(该表有行时) | 0 |
| **C2** `NETAMT == CSHRCV+CHQRCV+INTRCV+TAX` | 0 |
| **C3** `Σ ARRCPIT[RECTYP≠'0'].RCVAMT == NETAMT+ADVAMT+REMAMT` | 2/1077(两张无明细的挂账收款) |
| **C4** `Σ ARRCPIT[RECTYP='0'].RCVAMT == ADVAMT` | 0 |
| **C5** `Σ GLJNLIT[TRNTYP='0'] == Σ GLJNLIT[TRNTYP='1']`(借=贷) | **0 / 1077** |
| **C6** `GL 在 ARMAS[CUSCOD].ACCNUM 上的净贷方 == NETAMT+ADVAMT` | **0 / 1077** |
| **C7** 有冲销就必有 GLJNL+GLJNLIT(VOUCHER=单号) | 2(2024 年跨年结转单) |
| **C8** `REMAMT>0 ⇔ CMPLAPP='N'`(且 DOCSTAT='R') | 0 |
| **C9** `CHQPAS == CHQRCV` | 1 |
| **C10** `IVCAMT == Σ 冲销额`(纯预收单允许 0) | 4(预收混合单只存现金额) |
| **C11** `FLGVAT='2'` 时 `SEQIT' 8' 腿 == VATAMT` 且与 `' 9'` 腿等额反向 | 0 |
| **D1** 被冲发票 `RCVAMT == Σ 引用它的 ARRCPIT.RCVAMT` | 0 |
| **D2** 被冲发票 `REMAMT == NETAMT-RCVAMT` | 0 |
| **D3** 被冲发票 `CMPLAPP='Y' ⇔ 已全额分配` | 0 |
| **E1** `ARBAL.RE<月> == Σ(NETAMT+ADVAMT)`(按客户/月) | 4/948 |
| **E2**(渠道解析)ARRCPCQ 每行 → ISRUN[ZR,PREFIX] → ACCNUM01 或 BKMAS[SHORTNAM].ACCNUM,金额绝对值命中 GL,**符号(正=借/负=贷)与 TRNTYP 一致** | 0/968 |

推荐的**最小回读闸**(写完必须全过,否则回滚):C5、C6、D1、D2、D3、C2、C3
+ 索引 seek 命中(ARTRN 按 DOCNUM、GLJNLIT 按 VOUCHER、ARRCPIT 按 RCPNUM)。

---

## 5. 与已啃下的采购(RR/HP)/销售(IV/HS)单的异同

**多出来的**

1. **两张专属子表**:ARRCPIT(冲销明细,挂到被冲单号)+ ARRCPCQ(收款方式行)。
   发票/采购单没有「指向别的单据」的明细。
2. **反向更新别人的单头**:必须回写被冲发票的 `RCVAMT/REMAMT/CMPLAPP/CMPLDAT`——发票/采购单只写自己。
   这是收款单最大的一处「跨单据副作用」。
3. **收款渠道体系**:ISRUN `DOCTYP='ZR'` 是一整套收款渠道字典(现金/支票/各银行户/手续费/汇兑损益/代扣税/折让),
   科目要么直接在 `ACCNUM01`,要么经 `SHORTNAM → BKMAS.BNKACC → ACCNUM` 拐一道。采购/销售的科目取自商品/科目映射,
   不走这套。ZR 表每家账套完全不同(SINCER 20 条、MANAC5 60+ 条,后者几十个渠道全是不同客户的代扣税科目)。
4. **BKTRN 银行模块**:只有走 SHORTNAM 指向 BKMAS 的渠道才写(6902ASC 313 张有,SINCER 728 张一张都没有)。
5. **ARBAL 用 RE1..RE12/RE1NY..RE12NY 桶**(发票走 IV*,现销走 HS*,折让走 SR*,借项走 DR*)。
6. **收款基础销项税**(FLGVAT='2'):收款时才认列销项税,GL 多一对「销项税待认列→销项税」转出腿
   + 写 ISVAT(VATREC='S', RECTYP='9')。采购/销售单的 ISVAT 是开票时点写的。

**少掉的**:不写 STTRN/STCRD/STMAS(不动库存)、不写商品主档、发票号/税号栏位大量留空
(FLGVAT/VATRAT/DISC/PAYTRM 等 30+ 字段空)。

**坑(踩过才知道)**

- `TRNTYP` 是 `'0'/'1'` 不是 `'D'/'C'`;`SEQIT` 是 **CHAR(2) 带前导空格**(`' 2'`),且**不可信**:
  6902ASC 有 17 张(2025 年 1 月那批)把 AR 腿也塞在 `' 2'` 槽。**认腿要认科目(ARMAS.ACCNUM),不能认 SEQIT。**
- Express 自己在编辑过程中会写 `ACCNUM='9999-99'` 的临时挂账腿再软删——读回校验必须排除软删行,
  否则借贷会算歪(已被 `dbf.is_deleted` 兜住)。
- **删单不删干净**:6902ASC 三张软删收款单里,RE69L02-011 的 ARRCPIT/ARRCPCQ/GLJNL/GLJNLIT/BKTRN
  **仍有活行**。作废单的特征是单头 `DOCSTAT='C'` + 金额清零 + 软删,子表可能留活行
  → 与已知的「DBF 软删行当有效行」P0 同源。
- 69SINCER 的 ISVAT 里有 **8 个日期字节损坏**(`b'S460'`),`dbf` 读取直接抛 ValueError;
  任何全表扫描必须逐字段 try/except。
- ARRCPCQ.CHQNUM **不唯一**(1023 行 458 个不同值),不能当键;BKTRN 的 (CHQNUM,BNKACC) 才唯一。

**三个具体问题的答案**

- **怎么关联被冲发票**:明细行逐张挂 DOCNUM(ARRCPIT),不是按余额冲;同时反写发票单头的 RCVAMT/REMAMT/CMPLAPP。
- **部分收款**:两种,(a) 明细行金额改小 → ARRCPIT.RCVAMT=部分额,发票 REMAMT=差额、CMPLAPP='N'(SINCER 120 张);
  (b) 选整张票但钱没到齐 → ARRCPIT 记全额,差额挂在**收款单头** REMAMT、单头 CMPLAPP='N'/DOCSTAT='R',
  而**发票被标记为已全清**(6902ASC 6 张)——(b) 会让子账与 GL 差 REMAMT,是个真实的对账陷阱。
- **预收**:两条路,(a) 先开 AI 预收单,收款时 ARRCPIT 加一条 RECTYP='0' 指向 AI + 单头 ADVNUM/ADVAMT,
  GL 借 2133-01;(b) 收款不挂任何发票(ARRCPIT 0 行),AR 直接贷成负数。
- **现金/支票/转账**:本质只是不同的 ZR 渠道行 → 决定 GL 科目 + 决定钱落 `CSHRCV`(现金渠道)还是 `CHQRCV`;
  渠道若绑了 BKMAS 银行户才额外写 BKTRN。**四个账套里没有一张「客户支票待托收」的活样本**
  (BKTRN 收款行清一色 `bR/CHQSTAT='19'`,即钱已在银行);**支票托收状态机(BQ/DEQ 入托单)未取到证据,不能编**。

---

## 6. P2-B 施工建议

**难度:中**(比销项发票高一档,比库存闭环低)。理由:表多但都无库存/成本逻辑;
真正的复杂度在「跨单据反写」和「每家账套自定义的 ZR 渠道字典」。

**最大风险点(按严重度)**

1. **反写别人的发票单头**——写一半崩 = 发票显示已收款但没有收款单,或反过来。
   必须把被冲发票的 `RCVAMT/REMAMT/CMPLAPP/CMPLDAT` 纳入同一事务的备份/回滚集。
2. **ZR 渠道字典每家不同**:不能硬编码「现金=CH、银行=TR」。必须开工前从客户账套 ISRUN 读出 ZR 全表 + BKMAS,
   做成「收款方式」下拉给会计确认一次(同 posting 科目映射的做法)。渠道 ACCNUM01 为空时**必须**走
   SHORTNAM→BKMAS 兜底,否则科目取空。
3. **AR 科目按客户走**(ARMAS.ACCNUM),同一账套可能出现 1130-01 / 1130-20 / 11-05-03-00 多种;不能取账套默认。
4. **不足额/预收两种形态**导致「settled ≠ 实收」,把 C3/C6 写死成 `settled==NETAMT` 会在真账套上误报失败。
5. **收款基础销项税**(FLGVAT='2'):若客户账套是服务业按收付实现制,漏写 ISVAT + 那对税转腿 = 税表少申报。
   **第一版建议直接拒收 FLGVAT='2' 场景**(escalate 转人工),不要半懂就写。
6. CDX 与并发:沿用 doc32 已上线的 Harbour DBFCDX 后台重建 + 独占锁 `waiting_lock` 路径,
   新增 touched 表 = ARRCPIT / ARRCPCQ / BKTRN / ARBAL / 被冲的 ARTRN 行。

**验证方案(TEST 账套 `\\Accserver\d$\ACCOUNT\69EXP\test`)**

- 靶场现状:8 张 ARTRN 全是 CMPLAPP='Y' 的已清发票、ARRCPIT/ARRCPCQ/BKTRN 全空、ISRUN RE 计数器 `0000001`、
  ZR 渠道与 BKMAS 与 69SINCER 同构 → **先用现有销项发票写入器造一张未收款的 IV,再造收款单**,
  不要拿现成已清发票试(会污染 D3 判据)。
- 造单矩阵(最少 4 例):① 单发票全额现金收款 ② 一张收款冲两张发票 + 银行渠道(验 BKTRN 与 (CHQNUM,BNKACC) 唯一)
  ③ 部分收款(验发票 REMAMT/CMPLAPP='N')④ 带客户代扣 WHT(验 TAX 腿与 C2)。
- 回读验收 = 第 4 节 C5/C6/C2/C3/D1/D2/D3 + Harbour 索引 seek(ARTRN.DOCNUM、GLJNLIT.VOUCHER、ARRCPIT.RCPNUM)
  全命中才 ack success;并且**跑完把 TEST 账套整体 diff 一遍**,确认没有第 2 节清单之外的表被动过。
- 回滚:沿用现有「写前备份 touched 表 DBF/CDX/FPT → 任一步失败恢复备份」。
  注意备份集必须包含**被冲发票所在的 ARTRN** 和 **ARBAL**——这两张是本单据类型独有的「改旧数据」目标,
  漏备份 = 回滚不干净。
- 幂等:防重单钥匙用 `(账套, DOCNUM)` 先在 ARTRN 里 seek;**同时必须扫软删行**——软删的同号单会让
  Express 端「报成功但看不到」(已知 P0 同款),写前遇到同号软删行应判 needs_review 而不是覆盖。
