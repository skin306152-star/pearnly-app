# 34 · 对手方税号/地址落档(与真账套录入一致)

2026-06-26。起于「我们的自动录入是否符合真实客户/ERP 要求」的核对。拿服务器上正在用的
真账套(`P:\68EXP\test`,当期 2026-05 仍在开票)逐项对照 companion 自动建档的产物。

## 核对结论(对照真账套)

| 维度 | 真账套做法 | 我们(改前) | 判定 |
|---|---|---|---|
| 单据有效性/金额/VAT/应收应付 | RECTYP=3 等 | 一致 | ✅ 达标 |
| 销售收入科目 | `411000` 等真收入科目 | `41-01-00-00 รายได้จากการขาย` | ✅ 达标(国内店单一收入科目合理) |
| 会计期间/日期 | 当期账套→单号/日期自动当年 | 测试套期间 2558→日期落 2015 | ✅ 机制无误(换当期真账套即正确) |
| 对手方税号 TAXID | 客户/供应商主档填 13 位 | **建档已写**(`1ee0a449` 起) | ✅ 已有 |
| 对手方地址 ADDR01/02/03 | 主档填地址(全额税票要) | **未写** | ❌ → 本次补齐 |
| 库存跟踪(STKTYP=0 / COGS) | 实体货真库存 | 全 STKTYP=5 非库存 | ⚠️ Owner 拍板:不管库存,保持非库存 |

## 本次改动:地址端到端落档

税号本就在写,缺的只是地址。补齐后自建客户/供应商与真账套全额税票录入一致。

- **云端**(`services/erp/express_push/{sales_mapper,mapper}.py`):customer/supplier 块新增
  `address` = `clean_address(buyer_addr)`(销项)/ `clean_address(seller_addr)`(采购)。
  现金/散客客户不带地址(简易税票无须买方地址);乱码/过短地址被 `clean_address` 清空。
- **companion**(`master_create.py` + `{sales,purchase}_adapter.py` + `dbf_schema.py`):
  payload.address → `SalesEntry.customer_address` / `PurchaseEntry.supplier_address` →
  建 ARMAS/APMAS 时按真表列宽 `ADDR01/02 C50 · ADDR03 C30` 分行落档。`_split_address`
  按词断行不切词、未超容量原文可重组;超容量末段硬截断。
- **稳健性**:`ensure_customer` 补建档读回校验(镜像 `ensure_supplier`,建完读不回则抛错由
  writer 备份回滚)。

## 验证

- companion 197 单测全过 + ruff clean(新增 `_split_address` 边界 + 供应商/客户地址落档读回)。
- 云端 4973 单测全过(新增 B2B 地址进 payload / 现金客户不带地址 / 乱码地址清空 / 采购供应商地址)。

## 仍是 backlog(非本次)

- 库存:Owner 已拍板维持非库存(STKTYP=5),不做 COGS/库存跟踪。
- 上线真账套前仍需确认:账套会计期间为当年、收入科目按客户习惯(是否拆品类)。
