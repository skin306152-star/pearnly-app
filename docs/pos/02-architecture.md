# POS 项目 · 02 架构

> 入口怎么拆、角色怎么裁、模块怎么开关、离线怎么做、跟现有怎么咬合。技术图纸的地基。

## 1. 入口拆分(为什么收银前台独立)

```
pearnly.com/pos          ← 收银前台 · 独立 SPA · 离线 PWA · 收银员落地 · 平板/收银机
pearnly.com/home         ← 主程序 · 老板/会计 · 多出「库存」「销售报表」模块
pearnly.com/admin        ← 超管 · 不变
```

**收银前台独立成 /pos 的三个硬理由**:
1. **离线 PWA 要小而专** —— 主程序 home 装着 OCR/对账/ERP 一大坨,塞进收银机离线缓存又重又脆;独立入口才能做干净可安装的 PWA。
2. **收银员只看收银** —— cashier 登录直接落 /pos,进不去会计程序。复用已验证的「超管登录只进 /admin、永不进 home」模式(`routes/oauth_routes.py:331` 重定向 + `core-boot.ts:370-390` 双向弹回)。
3. **设备/UX 不同** —— 收银台触屏求快,会计桌面看报表,两种 UX 不混壳。

**库存拆两半**:
- **库存后台**(入库/盘点/调拨/报表)→ 主程序 home 内的模块(会计/老板,桌面)。
- **收银前台**(卖货/收款/小票)→ 独立 /pos(收银员,平板,离线)。
- 两者共享底座:`products` · `inventory_ledger` · `sales_documents`。

**/pos 技术形态**:参考 admin SPA(plain script · 不依赖 home.js),但需 PWA(manifest + service worker + 本地存储)。独立 bundle、独立路由、独立鉴权落地。

## 2. 角色与模块开关

### 2.1 新角色 cashier

现有:`owner` / `member` / `is_super_admin`(`users.role` + `users.is_super_admin`)。
新增 `cashier`,复用现有 role 框架:
- JWT 带 role(`core/auth.py:49-60` 已支持)。
- 登录分流加一条:`role=='cashier'` → 落 `/pos`;偷进 /home/admin → 弹回 /pos。
- 后端守门:POS 写接口校验 role + 模块开关。

### 2.2 模块开关 tenant_modules(愿景表 · 现不存在 · 本项目建)

```sql
tenant_modules(
  id, tenant_id, module_key, enabled, config jsonb,
  UNIQUE(tenant_id, module_key)
)
-- module_key: 'inventory' | 'pos' | 'sales' | 'expense' | 'recon' | 'knowledge' ...
```
- 导航/路由/功能按它显隐(现在是硬编码全显)。
- 业态预设 = 一组 module_key + config 的开关组合(选业态一键写好)。
- POS 功能块(桌台/称重/会员)放 `config` JSON,按业态开。

**开通收银入口设计**(Zihao 2026-06-07 拍板 · 预览 `桌面/Pearnly_POS_UI预览/10-开通收银入口.html`):解决"导航组开通后才出现、可开通入口却要先可见"的鸡蛋问题。
- **主入口**:侧边栏「可开启」区常驻一项「收银 · POS · 可开启 →」(虚线灰显·hover 变蓝·**仅 owner 可见**),点 → 开通页(屏8 = `08-开通收银.html`)。
- **开通后**:该引导项消失,「收银业务」分组出现(库存 / 销售报表 / 切到收银台),由 `tenant_modules` 开关驱动显隐(复用 A4 的 module-nav)。
- **次要入口**:设置页「业务/模块」区(重新配置/关闭·后续)。空状态可二次曝光"开通收银 →"引导卡。

### 2.3 RLS 必须开

现状:员工隔离只靠前端藏,后端 tenant_id 过滤但 RLS 默认关(`core/db.py` `ENABLE_RLS=0`)。POS 涉钱,收银员若直调接口能看全租户数据 → **本项目开 RLS**(基础设施已就绪,`get_cursor_rls` + 5 条穿透测试已在),POS/库存表全部纳入 policy。

## 3. 离线架构(最高风险 · 详见 08-offline-sync-adr)

```
收银前台(/pos PWA)
  ├ Service Worker:缓存 app 外壳 + 商品快照(可离线选品)
  ├ 本地库(IndexedDB):离线开的单 + 库存预扣 排队
  └ 同步引擎:联网 → 按序补传 → 服务端去重/冲突合并 → 回填单号
```
**关键风险点(图纸要钉死)**:
- 单号:离线本地临时号,联网由服务端发正式连号(防撞号)。用 client 端 idempotency_key 去重。
- 库存:离线乐观扣减,联网核对;超卖如何处置(允许负库存 + 告警 vs 拒卖)→ 待定策略。
- 时间:以服务端为准还是本地?收款时间用本地、入账时间用服务端。
- 冲突:同一商品两台机离线都卖 → 联网合并,库存以事务为准。

## 4. 数据咬合(详见 03-data-model)

| 现有(复用) | POS/库存(新建) | 关系 |
|---|---|---|
| products(UUID) | inventory_ledger | 商品的实时库存 |
| workspace_clients(BIGINT, 卖方) | pos 单据 seller | 以哪个主体收银 |
| sales_documents(UUID) | doc_type=receipt / 或独立 pos_sale | 小票/税票 |
| promptpay / payment 字段 | — | 收款复用 |
| — | inventory_transactions | 每次出入库流水 |
| — | pos_shifts | 班次/日结 |
| — | tenant_modules | 模块开关 |

**外键类型对齐铁律**:tenant_id=UUID;products/sales_documents.id=UUID;workspace_clients/clients.id=BIGINT(历史)。新表外键**遵循现有混合模式,不另起炉灶**(参考 sales_documents + workspace_clients)。

## 5. 事件松耦合(模块化六原则#4)

POS 收款成功 → 发"卖出 X"事件 → 库存(若开)扣减;没开库存就没人接,**什么都不发生也不崩**。同理进项入库 → 发"入库 X"→ 库存增加。这是"模块能任意开关"的技术底线。实现:进程内事件/直接调用(初期),不引消息队列。

## 6. 前端工程约束(沿用主项目铁律)

- 单文件 <500;新模块独立(`services/pos/*` `services/inventory/*` `routes/pos_routes.py` `routes/inventory_routes.py`)。
- schema 走 Alembic(`0021_inventory_*` `0022_pos_*` ...);prod 经 ssh+psql 授权应用(现状无自动迁移)。
- 4 语 i18n;钱 Decimal;UTC 时间;每文件 ≥1 测试。
- UI:modal 不用 drawer;按钮品牌蓝 `#2563EB`;线性图标禁 emoji;设计稿先行。
- /pos 若用 plain script(非 Vite),CSS/JS 仍受 <500 与去 AI 味闸约束。
