# 套账隔离 · 04 逐 PO 施工单

> 风险 低→高。每 PO 独立可上、独立 E2E、独立回滚。涉钱模块(对账/销项)按铁律先报方案。
> 通用每 PO 验收闸:守门全绿 + 单测全绿 + 真账号跨套账 E2E(A/B 两套账互不串)+ prod 库 dry-run。

## 依赖图

```
PO-0 地基/上下文 ──► PO-1 回填(数据) ──► PO-2 顶栏套账切换器
                                              │
        ┌─────────────────────────────────────┤(切换器到位后才切读路径)
        ▼            ▼            ▼            ▼            ▼
   PO-3 商品   PO-4 进项读侧  PO-5 库存批次  PO-6 对账(多子PO) PO-7 销项(高敏·最后)
        └──────────────┴────────────┴────────────┴────────────┘
                                  ▼
                       PO-8 机械闸切硬门 + 全模块跨套账 E2E
```

## PO-0 · 地基与请求上下文(无行为变化)

- 统一/推广 `resolve_workspace(request)` 依赖(基于 POS 既有 `require_workspace`)+ `WorkspaceScope` 上下文对象。
- 加 `X-Workspace-Client-Id` 解析 + 归属校验 + fail-closed(但**先只挂在已隔离模块**做验证,不碰未改模块)。
- 落 CI 闸**骨架**(warning 模式):`test_workspace_sql_isolation.py`(运营表名单先空跑)、`test_operational_endpoints_require_workspace.py`。
- 错误码:`workspace.required` / `workspace.forbidden`(4 语)。
- 出口:上下文机制能跑,未改模块零影响。

## PO-1 · 默认套账回填(纯数据 · 见 03)

- 回填脚本(分类 A/B/C → 建默认套账 → 加可空列 + 回填 + 加索引),幂等可回滚。
- **不切任何读路径**。老查询照跑。
- 出口:每租户一个默认套账;待回填表零 NULL;prod dry-run 通过;老用户数据零变化。

## PO-2 · 顶栏套账切换器(前端 · 与买方切换器分层)

- 顶层套账切换器:切换→设 header、持久化、重拉当前页;单套账自动隐藏。
- 第二层买方筛选器:保留原 `client_id` 语义,文案与套账区分清楚。
- 启动:无选中套账→默认/弹选择。
- 出口:能切套账(此时后端读路径还没按它过滤,切换暂只设上下文)。可与 PO-3 合并上,避免"能切但没反应"的空窗——按实现节奏定。

## PO-3 · 商品(练手 · 低风险)

- `products` / `product_units`:读写全切带 workspace_client_id;catalog/products store 站点(~25)逐个改;收 NOT NULL。
- 注意:POS catalog、销项选商品、库存引用商品都读 products → 一并验证四态不空。
- 把商品纳入 `test_workspace_sql_isolation` fail 名单 + 一条跨套账 E2E。
- 出口:套账 A 的商品在套账 B 不可见;商户(单套账)无感。

## PO-4 · 进项识别读侧(改动最小)

- `ocr_history`:列已有、写已对、回填已做 → **仅给读路径加过滤**:`list_ocr_history` / detail / pdf / find_by_hash / check_duplicate 全部带 workspace_client_id(取自上下文)。
- history 路由传入当前套账;`restrict_client_ids`(买方)保留为套账内的二级筛选。
- 上传识别:已带 workspace_client_id 写入,复核取值改自上下文(非请求体可选)。
- 纳入闸 + 跨套账 E2E。
- 出口:切套账,识别记录列表只剩本套账;不再靠买方混筛。

## PO-5 · 库存批次补缺

- `inventory_batches`:加列+回填+读写过滤+收 NOT NULL。
- 复核 FEFO/近效期查询(services/inventory/fefo.py, queries.py)挂上 workspace_client_id。
- 出口:批次/效期按套账隔离,与已隔离的 stock/transactions 对齐。

## PO-6 · 对账(面最大 · 涉钱 · 拆多子 PO · 先报方案)

> ~130+ 站点,跨 v1/v2/vat/jobs 多套 store。**拆开做,别一 PO 吞**。每子 PO 真账号 E2E。

- **PO-6a** `bank_recon_v1`:sessions/transactions(transactions 经 session 派生)。sessions 现按 user_id → 补 tenant+ws。`bank_recon_v1_store`(~20)。
- **PO-6b** `bank_recon_v2`:`bank_recon_v2_store`(~26)+ `bank_recon_match`(~7)+ run/helpers 路由。注意 DATE_TOL_DAYS 等运行时常量别碰坏(见 [[date-tol-days-shadowing]])。
- **PO-6c** `vat_recon_tasks`:`vat_recon_tasks_store`(~26)+ vat_excel 路由/任务。
- **PO-6d** `recon_jobs`:`recon_jobs/store`(~23)+ worker/handlers + 异步任务里的上下文传递(worker 不在请求上下文里 → 套账要随 job 行存,worker 从 job 读,不靠 request)。
- ⚠️ **异步 worker 是隐患点**:后台任务没有 request,套账必须**持久化在任务行**,worker 从行里取,**不能**漏成"看全租户"。
- 出口:每子 PO 跨套账 E2E;对账数据按套账隔离。

## PO-7 · 销项(最敏感 · 连号合规 · 压最后 · 先报方案 + Zihao 在场)

- `sales_documents`:启用 `seller_workspace_client_id` 为过滤键;`list_documents` 等(~30 站点,document.py 15)全切。lines 经 document 派生,复核直查点。
- **连号按主体**(见 03):`document_number_sequences` 改 (tenant, ws, doc_type) 计号;迁移按主体建 sequence、初值对齐各主体历史最大号;跨主体撞号自检。**已 issue 票连号冻结不动。**
- `etax_submissions` / `etax_channel_settings` 按主体。
- credit_note / quotation / share / approval / archive 一并切。
- 红冲补开(CN/DN 独立连号)同样按主体。
- 出口:切套账只见本主体发票;连号每主体独立连续(RD 合规);税票/电子税票按主体。

## PO-8 · 机械闸切硬门 + 全量验收

- `test_workspace_sql_isolation` 全运营表纳入、翻 **fail** 模式,进 pre-push + CI。
- `test_operational_endpoints_require_workspace` 全运营路由覆盖、fail 模式。
- `_e2e_ws_isolation.py` 全模块跑:一租户两套账,逐模块断言零跨套账行。
- 出口:以后任何新运营表/接口漏套账隔离,机械闸直接拦。

## 跨 PO 注意(本仓特有坑)

- **多窗口共享工作树**:只 `git add` 自己 pathspec,别 `add -A` 卷别窗口 WIP(见 STATE/memory 反复踩)。
- **回填(数据)与切读(代码)永远分 PO**;列先可空、模块切完再收 NOT NULL。
- **异步 worker 套账随行存**,不靠 request 上下文。
- **连号/已开票快照绝不重编**;改造只动新取号。
- 改对账/销项/进项主路径**先报方案**(铁律),销项 Zihao 在场。
- prod 无 alembic 钩子:迁移走 ensure_*/手动 apply,先 prod 库事务内 dry-run + rollback。

## 验收总闸(项目收官)

1. 一租户两套账 A/B,八模块逐一:A 上下文看不到任何 B 的行。
2. 商户(单套账)全程无感,功能不退化。
3. 老用户:默认套账下数据 = 改造前全部(零丢)。
4. 销项连号:每主体独立连续,跨主体不撞,历史票号不变。
5. 三道机械闸 fail 模式全绿;新增漏隔离能被拦。
6. 守门 6 道 + 全量单测全绿;prod 真账号冒烟。
