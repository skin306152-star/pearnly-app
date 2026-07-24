# B2 · 缺库存票补期初闭环(小助手侧落地)

> 2026-07-24 · 状态:**代码+验证完成,停在发版前(等 Zihao 拍板)**
> 配套:B1(Pearnly 侧 UI + 补期初卡,已上生产 · commit fc2d2547 + ba8368b3)

## 1. 这是什么(B-loop)

「选库存」的销售票,若客户账里此商品**存在但零库存**,小助手过账时算不出成本、拒绝静默造负库存 →
失败码 `STOCK_ITEM_NOT_FOUND` → Pearnly 推送日志弹「补期初卡」。会计据真单填 数量/单位成本/日期 →
重推 → **小助手先把期初垫进库存,本票随即复用①真扣库存 + 移动均价 COGS**。

B1 只到「卡 + 载荷契约」;B2 是**真正把期初写进 Express + 把两侧接通**。

## 2. 关键认知(推翻上窗口判断 · 全库取证)

**Express 期初库存 = 只动库存模块(STMAS/STCRD),不产 GL 凭证。** GL 里的存货期初是**科目级期初
余额(ยอดยกมา)**,会计一次性录、和库存模块对账,不走日记账。

取证:`\\accserver\ACCOUNT` 全库 30+ 真账套(米/油/化妆品/五金/服装)一致 —— 金标 `59EXP\test`
期初货值合计 4,744,859.25(全 ST02→存货科目 1140-02),但该科目 31,284 行 GLJNLIT **全是日常
进销货,无一张期初凭证**。所以 B2 期初**不写 GL** 是对的(不是缺口);上窗口「必补借存货/贷期初
权益」判断作废。详见记忆 `express-opening-stock-is-stock-module-only-no-gl`。

## 3. 改了什么

### Pearnly 侧(主站 · webhook 部署)
- `services/erp/express_push/preflight.py`:mapper 从 flat 构造 payload 时不读 `merged_fields`,
  期初被丢弃(**断点根因**)。在 `pf.payload` 就绪后显式透传 `merged_fields.opening_stock` 进 payload。
- `static/i18n-data.js`(四语)+ `home.html` ?v bump:补期初卡加**诚实边界**提示 ——「仅用于客户
  期初已持有的存货;若是漏记采购请改走采购推送」。
- `tests/unit/test_express_enqueue.py`:+2 测试(期初注入 payload / 常规票不带该键)。

### 小助手侧(独立发版 · git/webhook 都不部署)
- `worker.py`:`_handle_dbf_task` 按方向拆路由,销项传 `opening_stock=_opening_items(payload)`;
  新增 `_opening_items` 把 Pearnly 的 `{key,qty,unit_cost,date}` 映射成 `{name,...}`(键名对齐 + 日期解析)。
- `dbf_sales.py`:`write_sale` 加 `opening_stock` 参 —— 在**同一备份-回滚事务内**(STMAS/STCRD 已在
  BACKUP_TABLES)先调 `set_opening_stock` 垫库存,再 `_write_all`。期初与销售**原子成败**。
- `stock_sale.py`:`set_opening_stock` 支持逐行期初日期(缺则回落单据日期)。
- `tests/`:+2 集成测试(补期初让零库存品可卖 / 销售失败期初一并回滚)+2 映射测试。

## 4. 验证(headless 能验的全验了)

| 层 | 手段 | 结果 |
|---|---|---|
| 真表·核心 | `set_opening_stock`+`write_stock_lines` 跑真 Express 表(70EXP\test 本地副本) | ✅ 期初→可卖→卖10 COGS45→对账一致 |
| 真表·全链 | **完整 `write_sale(payload, opening_stock=[...])`** 跑真表 | ✅ 全新品→期初50@12→卖30→结存20/240,GL 借贷平(1002=1002),COGS360,ARTRN 落库,复用非空壳 |
| 合成·全链 | `write_sale` + 期初(AR/GL/COGS/原子回滚) | ✅ 2 测 |
| 映射 | `_opening_items`(key→name/日期/空态) | ✅ 2 测 |
| Pearnly 注入 | `enqueue_express` 透传 opening_stock | ✅ 2 测 |
| 回归 | 小助手全套 275 测 · Pearnly enqueue+ERP 路由 49 测 | ✅ 全绿 |
| lint | black + ruff(两仓库)· check_i18n(4×4928 齐)· ruff/black | ✅ |

## 5. 诚实残留(headless 验不了 · 归真机验收)

期初 STCRD 行用 **POSOPR=9**(继承销售出行的操作位);真 Express 期初是 **POSOPR=3/4 的 lot 对**。
小助手的销售/采购**本就用简化模型(单行 POSOPR=9 + STMAS 移动均价),不复刻 Express 原生 lot 机器**
—— B2 期初与之一致。余额字段(MREMBAL 绝对值)Express 直接显示,数值正确;但**期初行在 Express
GUI 里会呈现为一笔出库类操作而非「期初结转批」**,这属于呈现保真度,headless 验不了 → **真机需在
Express 里开一眼期初卡确认无碍**。

## 6. 发版清单(等拍板 · 两件一起上)

1. **Pearnly**:提交上述 Pearnly 改动 → push master → 盯 CI 到绿(webhook 自动部署)。
2. **小助手**:把 scratchpad 草稿改动落到真仓库 `skin306152-star/pearnly-companion` →
   bump `src/companion/version.py` VERSION → `packaging/release.ps1`(打包 + scp prod 66.42.49.213 +
   写 latest.json)→ **验在用小助手真更新到最新版**。
3. **真机验收**:指一个**真管库存、有真实进价**的账套(非冰厂),跑一张真库存票走完补期初 → 在
   Express 里开期初卡 + 库存卡 + GL 各看一眼,确认无碍。命中三情形判断(期初存货 / 漏记采购 /
   新客户零 GL 期初)按卡上诚实提示走。

> 两侧不接通则半吊子:只发 Pearnly → 期初到小助手但旧版忽略,重推照样失败;只发小助手 → 期初根本
> 到不了。**必须同批上线。**
