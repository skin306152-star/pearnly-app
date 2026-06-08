# 餐厅 POS · 03 逐 PO 施工计划

> ⚠️ 状态更正(2026-06-08):餐厅后端 PO-R1~R3 + 前端 4 屏(PO-R4)均【已施工并上线 prod】
> (见 git log `feat(pos)` 餐厅前后端)。下行"前端 4 屏待…再做"是旧状态、已过时。以代码为准。

> 餐厅 = POS 第二业态,后端全新独立(不碰零售 POS 前端/服务)。复用 `products`/`pos_sales`/班次/连号/
> totals/promptpay/pdf_thermal。库存原料扣减(BOM)先不做,菜品当成品。每 PO 自含、做完即按 02 §7 + docs/pos/10 验收。

## 阶段 R · 餐厅后端

### PO-R1 · schema + 桌台/区域 CRUD + 总览
- 目标:5 表(areas/tables/sessions/lines/kot)+ `pos_sales.service_charge` 加列;桌台/区域 CRUD(owner)+
  桌台总览(派生状态机)。
- 新建:`alembic 0027_restaurant_core` + `services/pos/restaurant/{schema,store,tables}.py` +
  `routes/pos_restaurant_routes.py`(总览)+ `routes/pos_restaurant_admin_routes.py`(CRUD)+
  `services/pos_schema` 加双跑步 + app.py include + 测试(迁移/DAL/总览派生/契约)。
- 验收:开/关区域桌台显隐;总览空桌=free;无 session 时不报错四态。

### PO-R2 · 开台 + 点单 append + 送厨房 KOT + 逐项状态机
- 目标:开台 session(一桌一活动)+ 加菜草稿 append + 改/删草稿 + 送厨房生成 KOT + 后厨板 +
  整单/逐项 kitchen_status 流转(pending→cooking→done/void)。
- 新建:`services/pos/restaurant/{sessions,kitchen}.py` + 路由扩 `pos_restaurant_routes` + 测试
  (append/草稿锁/KOT 生成/状态派生/逐项与整单一致)。
- 验收:开台→点单→送厨房→加菜(第二张 KOT)→后厨流转;总览态随之 seat/cook 切换;真账号 E2E 串起。

### PO-R3 · 埋单(整桌/分单/AA + 服务费 + 复用 pos_sale + 税票)
- 目标:请结(open→billing)+ 账单预览 + 埋单落 `pos_sales`(复用连号/收款/报表)+ 服务费 10% + VAT
  单次取整 + 整桌/按项分单/AA;结清 → session closed + 桌空闲;升级税票/热敏/QR 复用零售接口。
- 新建:`services/pos/restaurant/checkout.py` + 路由扩 + 测试(算价对齐 UI 484/31.66 · 分单余行留台 ·
  幂等不双开 · 不扣库存 · session 结清转空闲)。
- 验收:核心流程 E2E(开台→点单→送厨房→加菜→埋单分单)+ B6 报表含餐厅单。

### PO-R4 · 前端 4 屏(待启 · `/pos` SPA 已收口可起)
- 目标:屏 01 桌台总览 / 屏 02 点单 / 屏 03 厨房单 KOT / 屏 04 埋单结账,照定稿稿逐字搬(09 §H)+ 接真接口 +
  四态 + i18n(此时补餐厅专用错误码 4 语,不再撞 i18n WIP)。
- 新建:`/pos` SPA 餐厅 4 屏(作用域隔离防跨屏同名类)+ 餐厅错误码进 06 + i18n-data。
- 验收:屏按钮全通 + 像素照搬比对 + 流程 E2E + 离线非必需(堂食在线)。

## 顺序
```
R1 → R2 → R3        (后端,本窗口)
        ↓
R4(前端,/pos 收完后另窗口)
```

## 守门(每 PO)
- 文件 <500 · 新文件 RATCHET-EXEMPT · 新 ensure_* NEW-DEBT-EXEMPT。
- 四窗口共用 .git:**绝不 `git add -A`**,只 `commit -- <自己后端文件>`;撞推则 stash 别窗口 WIP + rebase。
- ruff 过 ≠ black 过,push 前补 `black`;署名 Opus 4.8;commit 带 `POS-R<n>`。
- 真账号 E2E(`pearnly_e2e_3`)是硬闸:开台→点单→送厨房→加菜→埋单分单,断言落 pos_sale + 桌转空闲 + 库存不变。
- 隔离:每句 `WHERE tenant_id`(+ ws),A 取不到 B;RLS policy 加(BYPASSRLS 仅兜底)。
