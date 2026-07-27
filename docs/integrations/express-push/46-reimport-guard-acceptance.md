# 46 · 重推/防重单验收清单(哪些已成回归测试 · 哪些只能在真账套上验)

2026-07-27。上一轮在 TEST 靶场 `\\Accserver\d$\ACCOUNT\69EXP\test` 真投 8 次(3 次落盘、
5 次零变动),结论是采购路四场景全过、但同一道闸在 `stock_adjust` 上真跑证明缺失。这份清单
把那次验证拆成两半:**能在合成账套上判的已经变成常绿回归测试**,剩下**只有真账套能回答的**
逐条列出判据,下次上真机照着跑。

## 一、已成回归测试(每次 `pytest bridge/tests` 都跑,不需要账套)

| 场景 | 判据 | 测试 |
|---|---|---|
| S1 首推 | APTRN+1 / GLJNL+1 / GLJNLIT+3 / ISVAT+1 / APBAL 桶 +含税额 | `test_purchase_reimport_scenarios::test_s1_...` |
| S2 同载荷重推 | ok skipped · 返回既有号 · 账本零变动 · 带 `duplicate_of` 人话 | 同上 `test_s2_...` |
| S3 改金额重推 | ok skipped · ERP 里仍是旧金额 · 人话里说清"改了也算重复"和怎么办 | 同上 `test_s3_...` |
| S4 软删后重推 | ok · 落新号 · 不复用已用过的号 | 同上 `test_s4_...` |
| P1 prior 指活单 | 拒 `PRIOR_DOC_STILL_IN_ERP` · 零写入 | 同上 `test_p1_...` |
| P2 prior 指软删单 | ok · 落新号 | 同上 `test_p2_...` |
| 库存调整重推 | 拒 · STMAS.TOTBAL 不动 · STTRN 仍 1 行 | `test_prior_doc_guard::test_stock_adjust_reimport_with_live_prior_doc_is_refused` |
| 闸的覆盖面 | 每一类 `DOC_WRITERS` 都调共享件(例外要写理由) | `test_prior_doc_guard::EveryDocTypeConsultsTheGate` |
| 闸序 | 防重单排在幂等之后(重投不该硬失败) | 同上 `test_gate_runs_after_the_idempotency_check` |
| 明细行 | 带明细→行数/行合计/NXTSEQ/REFNUM;表头模式→零行 + NXTSEQ `-1` | `test_purchase_detail_lines` |
| 合成表形状 | 逐列比对真账套表头(需 `PEARNLY_REAL_ACCT`) | `test_table_specs_vs_real` |

## 二、只能在真账套/靶场上验(合成栈答不了)

跑之前:靶场是 Zihao 授权可读写删的唯一目录,共享上的其它一切只读。

1. **Express 认不认这张单** —— 合成表能证明字节写对了,证明不了 Express 的界面/报表会把它
   当成一张正常单据。判据:在 Express 里按单号能查到、明细页行数与 STCRD 一致、进项税报表
   里出现。
2. **CDX 索引真回查** —— 测试里 `cdx_reindex_runner` 是被关掉的(合成表没有 Express 的结构化
   标签),`_verify_index` 走的是回落路径。判据:真账套上写完不 PACK 也能按 DOCNUM seek 到。
3. **NXTSEQ `-1` 的下游行为** —— 我们只证明了真账里表头模式单**从来**写 `-1`(采购 72 张 /
   销项 281 张,`('1', STCRD 零行)` 出现 0 次)。没有证据说明 Express 会因为 `'1'` 而误判。
   判据:靶场写一张表头模式单,在 Express 里打开明细页,看它显示"无明细"而不是报错/串行。
4. **STCRD.REFNUM 的取数面** —— 真账采购行 1982/1989 带供应商票号,我们现在也写了。哪些
   报表按它取数本轮没查。判据:靶场写一张带明细的采购单,跑一遍库存卡/进货明细表看票号列。
5. **软删残骸与账套锁** —— Express 正开着账套时的 `waiting_lock`、以及删单后 CDX 里的残留
   指针,合成栈都造不出来。

## 三、验证脚本自己的坑(这次的根因)

那一轮的靶场脚本报绿而明细一行没写,根因不在写路而在脚本:payload 只带
`doctype/ref_no/supplier/金额/lines`,**没有 `items`/`items_status`/`items_account`**,
`purchase_adapter` 对缺失的 `items_status` 取默认 `"empty"` → 写路整段跳过明细,读回的
`verify_detail` 又只在 `detail_n>0` 时才被调用。同一份报告里另外两条 defect 也同源:断言把
RR 的 `RECTYP` 写成 `'2'`(真值 `'3'`)、幂等重放拿 `YOUREF` 找票号(真列是 `REFNUM`)。

**规矩**:任何对真账套的验证脚本,断言里出现的每一个列名/取值都必须先在真表上核过;
被验证的对象必须来自真实产物,不能来自脚本自己造的桩。写路侧已经补了对应的闸
(`dbf_detail.verify_no_detail`),脚本再漏 `items` 也会被读回拦下。
