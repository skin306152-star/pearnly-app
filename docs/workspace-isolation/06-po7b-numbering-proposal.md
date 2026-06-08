# PO-7b · 连号按主体(document_number_sequences)· 已施工

> **状态:已施工(2026-06-08 · Zihao 授权"全做完不必报方案")。** 计号键扩到
> (tenant, ws, doc_type, prefix, period);三个取号点(开票 / 红冲补开 / POS 小票)全传主体;
> 红冲单继承原单卖方主体(补 PO-7a 的 notes 漏继承)。迁移做成**启动自愈 ensure**
> (`services/db_migrations/numbering_workspace_key.py` · startup 调):建唯一索引 `uq_dns_ws`
> + NULL 主体回填 + **守门式 drop 旧 PK**(仅当全表零 NULL 主体才落地,否则保留兜底)。
> 部署即随重启迁移,代码与迁移同上(不会"代码先行")。机械闸 `document_number_sequences`
> 已从 DEFERRED 移入 CONVERTED。**单主体租户号序逐张不变;多主体各自独立连续、跨主体不撞。**
> 待办:部署后跑 `_e2e_ws_isolation.py` 验连号独立(uq_dns_ws 上线后才有)。
>
> 下为原方案记录(已落地,留档对照)。

## 现状
`document_number_sequences` 主键 = `(tenant_id, doc_type, prefix, period)`,即**每租户一条连号**。
`numbering.allocate()` 事务内 `INSERT ... ON CONFLICT (tenant_id, doc_type, prefix, period) DO NOTHING`
→ `SELECT ... FOR UPDATE` → `+1`。PO-1 已给本表加可空 `workspace_client_id` 列并回填到各租户默认套账。

## 问题(RD 合规)
事务所代多公司做账时,多主体共用一条连号 → 同一发票号跨主体重复 / 单主体号不连续 →
**泰国 RD 要求每法人主体发票号独立连续**,现状违规。当前每租户≈1 活跃套账,**暂未触发**。

## 方案(rollout-safe · 单主体零变化)
1. **取号键加主体**:`allocate(..., workspace_client_id)`;键改 `(tenant_id, workspace_client_id,
   doc_type, prefix, period)`;`ON CONFLICT` 指向新 5 列唯一索引。
2. **迁移(prod · Zihao apply)**:
   - `CREATE UNIQUE INDEX CONCURRENTLY uq_dns_ws ON document_number_sequences
     (tenant_id, workspace_client_id, doc_type, prefix, period);`(单主体下与旧 PK 等价 · 安全建)
   - `ALTER TABLE document_number_sequences DROP CONSTRAINT document_number_sequences_pkey;`
     (不丢数据 · 由新唯一索引继续保证唯一;**不 drop 则第二主体首次开票撞旧 PK 报错**)
   - 多主体历史拆号:为已有主体把 `next_number` 初值对齐各主体历史最大号(单主体无需 · 现状即此)。
3. **冻结**:已 issue 票的 `doc_number` 不动(本改只影响"下一个取号")。

## 上线顺序(防 prod 破)
迁移(建索引 + drop 旧 PK)**必须先于或同事务于**代码部署——否则 `ON CONFLICT (5 列)` 无匹配唯一约束
→ 开票即 500。故**代码与迁移须 Zihao 一并上**(不可代码先行)。

## dry-run 自检(apply 前)
- 每租户每 (doc_type, prefix, period) 现有行数 = 1(确认单主体);
- 建 uq_dns_ws 无重复冲突(旧 PK 保证);
- A/B 跨套账 E2E(硬闸):一租户两套账各开票 → 号各自从设定起点连续、互不撞。

## 验收
单主体租户:号序与改造前逐张一致(零变化)。多主体:每主体独立连续 · 跨主体不撞 · 历史号不变。
