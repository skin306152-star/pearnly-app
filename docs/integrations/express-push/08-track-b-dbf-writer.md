# P2 Track B 施工单 · DBF 直写器(无人值守首选)

> 先读 `06-phase2-revised-companion-and-dbf.md §3` + `07-user-flow-locked.md` + `00-master-plan.md` 真相。在 companion 独立 repo(`D:\pearnly-companion`)做,分支 `feature/express-companion-dbf`。
> 目标:小助手第二种录入法 —— **绕过界面直接写 Express 账套 DBF**,无需开 Express、无需活屏,适合事务所无人值守。**风险高 → 重护栏 + 只碰 DATAT 测试套。**

## 0. 关键现实(别低估)
DBF 直写 = **替 Express 复刻它的过账逻辑**(它是闭源)。写错一个字段/索引,账可能**静默错**(Express 不报、但账本错)。所以:**对着真 DATAT 里【已存在的真实 RR 记录】当"标准答案"逐字段比对**,产出与 Express 自己写的等价才算对。

## 1. 工具与开发数据
- 用 **`dbf` 库**(Ethan Furman·支持 VFP/FoxPro DBF + CDX 维护),别手搓二进制。
- **对 DATAT DBF 的副本开发**(`\\accserver\ACCOUNT\70EXP\test`·只读拷贝到本地工作目录;**开发期绝不写 live**)。本窗口够不到 `\\accserver` 就跟 PM 要副本。
- **标准答案**:DATAT 里已有真 RR(如 `RR581231-002`/PTT·见 00 真相)。我们的写入对同输入须产出**字段等价**的 APTRN/ISVAT/GLJNL/GLJNLIT 行。

## 2. 写一张赊购(RR)要动的表(输入=P1 采购载荷,见 purchase_adapter)
| 表 | 写什么 | 关键列 |
|---|---|---|
| `ISRUN` | 取并 +1 该单别当日序号 → 生成 DOCNUM | RR 前缀·`DOCNUM`(下一号) |
| `APTRN` | 单头 1 行 | RECTYP=3·DOCNUM=RR+佛历YYMMDD+-seq·DOCDAT·REFNUM(供票号)·VATPRD·SUPCOD·VATRAT=7·AMOUNT(税前)·VATAMT·NETAMT(含税)·POSTGL |
| `ISVAT` | 进项税 1 行(喂ภ.พ.30) | VATREC='P'·DOCNUM·REFNUM·TAXID·DESCRP=供应商名·AMT01=税前·VAT01=税额·VATPRD·DOCDAT |
| `GLJNL` | 采购凭证头 1 行 | JNLTYP='04'·VOUCHER=DOCNUM·VOUDAT·DESCRP=「ซื้อเชื่อจาก {供应商}」 |
| `GLJNLIT` | 分录 3 行 | Dr 采购科目+Dr 进项税科目=Cr 应付(TRNTYP 0/0/1·AMOUNT·ACCNUM 取自载荷 lines) |
| `APBAL` | 供应商应付余额累加 | SUPCOD·BALANCE |
| `STCRD` | (是存货时)库存卡变动 | 先做非存货/费用类·存货留增量 |
- 金额一律 **decimal**·借贷必平·**B8 字段是 8 字节 double**(写入用对类型)。
- ACCNUM 用载荷 lines 里的(11-04-02-00/11-05-04-01/21-02-01-00 范式);无供应商默认科目时用 config 兜底。

## 3. 强制护栏(每次写 live 必走)
1. **账套路径白名单**:只允许 `…\70EXP\test`(DATAT);其它路径**直接拒**。
2. **写前自动备份**整个账套目录(拷一份带时间戳)。
3. **单事务语义**:所有表要么全写成功要么全回滚(失败→从备份还原)。
4. **写后校验**:借贷平衡 + 读回刚写的 DOCNUM 各表行齐全 + 关键金额自洽;不过→回滚。
5. **重建 `.CDX` 索引**(每张写过的表)·否则 Express 看不到/报索引错。
6. **幂等**:写前按 REFNUM+SUPCOD 查 APTRN 是否已存在该单→已存在不重写。

## 4. 接小助手 + 方式选择
- 新模块 `src/companion/dbf_writer.py`(+ 必要的 `dbf_schema.py` 描述各表列)。
- 在录入分发处加 `method=='dbf'` 分支(与 RPA 并列):`dbf_writer.write_purchase(payload)` → 成功回 DOCNUM 当 express_docnum 给 ack_success;失败 ack_failure。
- 复用 Track A 的 `purchase_adapter`(它已把 P1 载荷规整 + 守门);DBF 用它产出的字段。

## 5. 验证(写清楚·施工窗口跑·PM 判)
- **headless(对副本·能自测)**:`test_dbf_writer`——
  ① 对 DATAT 副本写一张 RR,**读回与已有真 RR 标准答案字段比对**(APTRN/ISVAT/GLJNLIT 等价);
  ② 借贷平衡;③ ISRUN 序号 +1 正确;④ 白名单拒非 DATAT 路径;⑤ 备份+故意失败→回滚还原;⑥ 幂等不重写;⑦ CDX 重建后用 `dbf` 重新打开记录可见。
- **真机(留 Owner 机器·PM 安排)**:对 **live DATAT**(先备份)写一张 → **打开 Express 看得到该单 + 分录对 + ภ.พ.30/总账报表勾稽**。⚠️ DATAT 账期 2558–2559,测试票日期须落该期。
- 红线:每文件<500·≥1 测试·去 AI 味·不 push·**绝不写 DATAT 以外**。报:headless 测试结果 + 标准答案比对差异 + 改动文件。

## 6. 交付
- `dbf_writer.py`+`dbf_schema.py`+ `method=dbf` 接线 + `test_dbf_writer` + 备份/回滚工具。headless 全绿交 PM 判;真机写 DATAT 留 Owner 机器、PM 安排。
