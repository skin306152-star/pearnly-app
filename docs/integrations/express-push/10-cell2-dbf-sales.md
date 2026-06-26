# 第 2 格施工单 · 直写 × 销项(DBF Sales · 镜像采购)

> 第 1 格(直写×进项)已**真机端到端证明**(Pearnly 队列→companion→DBF 写 DATAT→ack=success·单号 RR581215-004)。本格把它**镜像到销项**。在 companion 独立 repo(`D:\pearnly-companion`)做,分支 `feature/express-companion-dbf-sales`(off `feature/express-companion-dbf`)。
> 先读 `08-track-b-dbf-writer.md`(采购直写已验)+ `09-direction-and-sales-locked.md`(方向/防错锁)+ `00-master-plan.md`。

## 0. 销项 = 采购的镜像(逐项对照)
| 维度 | 进项采购(已做) | 销项销售(本格) |
|---|---|---|
| 单别 | RR 赊购 | **IV 赊销**(ขายเงินเชื่อ) |
| 菜单(供参考) | `1.ซื้อ→4` | `2.ขาย→4` |
| 主体 | 供应商 APMAS | **客户 ARMAS** |
| 单头表 | APTRN | **ARTRN** |
| 余额表 | APBAL | **ARBAL** |
| 进/销项税 | ISVAT `VATREC='P'` | ISVAT **`VATREC='S'`** |
| 总账日记账 | GLJNL `JNLTYP='04'`(采购) | GLJNL **`JNLTYP='03'`**(销售) |
| 复式分录(反向) | Dr 采购+Dr 进项税=Cr 应付 | **Dr 应收(AR)=Cr 销售收入+Cr 销项税** |
| 库存 | STCRD 入 | STCRD **出**(是商品时) |
| 单号 | ISRUN RR | ISRUN **IV** |

## 1. 标准答案(gold · 不靠猜)
DATAT(`\\accserver\ACCOUNT\70EXP\test`)里有**真实 IV 销售单**(公司 มานะชัยบริการ 有销项)。**先在副本里找一张正常 IV**(ARTRN + ISVAT('S') + GLJNL('03') 齐全的),逐字段当标准答案;写出来须与之等价。⚠️ 注意采购里那种"无 ISVAT 异常单"在销项也可能有,**挑齐全的当 gold**(像采购挑 RR580101-001 不挑 RR581231-002)。

## 2. 做什么
1. **销项载荷适配器** `src/companion/sales_adapter.py`(镜像 `purchase_adapter.py`):P1 销项载荷 → SalesEntry(客户码/名/税号、IV、佛历日期、base/vat/total、lines:Dr AR=Cr 收入+Cr 销项税)。端侧守门:DATAT 白名单 + IV doctype + 佛历日期 + ref_no 必填 + 客户有码或有名 + 金额自洽 + 借贷必平。无客户码 → `customer_new`(防空码当老客户)。
2. **DBF 写销项** `dbf_writer.py` 加 `write_sale()`(镜像 `write_purchase`):写 ARTRN/ISVAT('S')/GLJNL('03')+GLJNLIT/ARBAL(+存货 STCRD),ISRUN IV 增号,重建 CDX。**沿用采购那套护栏**:DATAT 路径白名单、写前整套备份、单事务、写后读回校验(借贷平+读回)、失败回滚、REFNUM+客户 幂等。
3. **方向路由**(防录错):载荷带 `direction`;`direction=='sales'` → `write_sale`,`'purchase'` → `write_purchase`。**写错表族被 gold 比对+借贷当场抓**(09 §2 第三闸)。companion main 的 `_handle_dbf_task` 按 direction 分派。

## 3. 验证(headless · 对副本 · 施工窗口跑 · PM 判)
`test_dbf_writer_sales`:① 对 DATAT 副本写一张 IV,**读回与真实 IV 标准答案字段比对**(ARTRN/ISVAT('S')/GLJNLIT 等价);② 借贷平(Dr AR = Cr 收入+Cr 销项税);③ ISRUN IV 序号+1;④ 白名单拒非 DATAT;⑤ 备份+故意失败→回滚;⑥ 幂等不重写;⑦ CDX 重建后可见;⑧ 方向路由:purchase→APTRN 表族 / sales→ARTRN 表族,不串。
真机写 live DATAT(写一张 IV 看 Express `2.ขาย→4` 见单+分录+ภ.พ.30 销项报表勾稽)留 PM 安排(我有真机闭环法,跟第 1 格一样我来跑)。

## 4. P1 后端配套(销项载荷·另起或并行)
P1 现 `mapper.py`/`enqueue` 只产采购载荷。销项需:载荷带 `direction='sales'` + 销项映射(客户/IV/AR/销项税)。**本格 companion 侧先用"从 DATAT 真 IV 反推的样例销项载荷"自测**(不依赖 P1);P1 销项 mapper 作配套,我另发小单。

## 5. 边界
companion 独立 repo 切分支;每文件<500、≥1 测试、去 AI 味;**绝不写 DATAT 以外**;不 push;真机留 PM。报:headless 测试结果 + gold 比对差异 + 改动文件。
