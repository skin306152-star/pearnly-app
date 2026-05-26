# 卖方智能分拣 + 按账套路由(Phase 1)· 设计

> Zihao 2026-05-26 拍板。目标:大批量混合卖方/买方发票智能推送 ERP。
> 用户只负责上传;系统按**每张发票的卖方**自动分拣到对应 workspace(账套主体)+
> 其绑定的 ERP 端点,按卖方分组分别推送。没把握的进异常队列(Phase 2)。

## 核心语义(摆正)
- **销项发票上「卖方」= 账套主体 = workspace_client = 绑定某个 ERP 公司/年度账套**。
- 买方 = 应收客户 = ERP customer(已由 resolve_or_create_buyer_client + _sync_master_data + P2/P3 反查实现)。
- 不再要求用户上传前选账套;右上角切换器**降为「查看过滤器」**(只过滤历史/日志视图,不影响上传路由)。

## 现状(已就绪 / 已做)
- `workspace_clients` 已有 `tax_id` + `erp_endpoint_id`(B0)→ `seller_tax → workspace → endpoint` 查找链数据结构就绪。
- 买方/商品 tax 优先匹配创建 + 反查 + skipped_dup 显示,均已上线(858baca / 014c57f / 上会话 P2/P3)。
- 推送日志已有 卖方列 / OCR 买方列(ocr_buyer_name) / 工作空间列(join workspace_clients) / ERP 单号列。

## Phase 1 范围(本阶段)
1. **卖方匹配器** `services/workspace/store.match_workspace_for_seller(seller_tax, seller_name, user_id, tenant_id)`
   → `{action, workspace_client_id, endpoint_id, reason}`:
   - `seller_tax`(归一 13 位)精确命中 workspace_clients.tax_id:
     - 唯一 + 该 workspace 绑了 endpoint → `assigned`(返 workspace_client_id + endpoint_id)
     - 唯一但未绑 endpoint → `unbound`(未绑定 ERP 账套)
     - 多条同 tax → `multi`(多候选 · 异常)
   - 无 tax 命中 → seller_name 精确(忽略大小写)命中 → 同上判定
   - 都没命中 → `none`(无匹配账套)
2. **OCR 落库自动分配 workspace_client_id**(`app.py` · 没手动 override 时):匹配器 `assigned`
   → `update_history_workspace_client_id(hid, workspace_client_id)`。日志「工作空间」列即显卖方账套。
3. **按账套路由推送**(`app.py` auto-push 段 + `_auto_push_history`):每张 history 只推它
   workspace 绑定的那个 endpoint(不再推给所有 auto-push 端点)。
   - **兼容兜底(回滚安全线)**:匹配不到 workspace/endpoint 的 history → **暂回退现有行为**
     (推给现有 auto_push 端点),不阻断 → 现用户 mrerp 即使未回填绑定也照常工作。
     Phase 2 异常队列上线后收紧为「未绑定→进异常待处理」。
4. **seller→workspace 记忆**(规则2):用户给未匹配卖方绑定一次 → 把 seller_tax 写到该
   workspace_clients.tax_id(下次自动命中)。Phase 1 走税号记忆;名字别名记忆延后。
5. **单张异常不卡整批**:推送 per-invoice 隔离(已是 per-history 循环 · 确认一张失败不影响其余)。

## 不在 Phase 1(后续)
- 异常队列 + 批次中心四态 UI(规则9)= Phase 2(需 erp_push_logs.batch_id schema + 新 UI)。
- 名字别名/模糊卖方记忆表。
- 严格模式(未绑定卖方硬进异常)→ 等 Phase 2 队列能接住后再开。

## 迁移 / 回滚
- 迁移:现用户 mrerp 的 workspace 需填上其卖方主体 tax_id + endpoint 绑定(否则走兼容兜底)。
- 回滚:路由是加法 + 兜底 · 出问题把"按账套路由"开关关掉即回退全推 auto-push 端点(现行为)。

## 守门
- 匹配器全分支单测;路由单测(单卖方=现行为 / 多卖方=各推各的 / 未匹配=兜底);
  per-invoice 隔离测试(1 张异常其余继续)。

---

## 🔒 Zihao 2026-05-26 二次拍板(确认 · 通用化 + 规模 + 3 模式)

整套必须是**通用 ERP 能力**,不为 MR.ERP 写死。抽象模型:
`workspace_client`(账套主体/卖方)· `erp_endpoint`(MR.ERP/Xero/Webhook/未来)·
`seller_route`(seller_tax/name→workspace→endpoint)· `buyer_master` · `product_master`。

**决策 1 · 按 endpoint 分组「批量」seam(解 1000 张规模)**:上层按 seller/workspace/endpoint
分组 → 每组调一次 `adapter.process_batch(endpoint, histories, mode) → 统一 per-invoice 结果`。
买方/商品/反查/推送留在 adapter 内部(MR.ERP 已在 `upload_invoice_batch`)。**绝不逐张循环推 1000 张**
(MR.ERP=Playwright+会话锁串行,逐张几小时)。上层不写 `if adapter=='mrerp'`,只认 seller_route +
统一状态(success/skipped_dup/needs_action/retrying/failed)+ 结构化异常原因。
不现在抽 5 个离散方法(YAGNI · 等第 2 个 ERP 真复用买方/商品逻辑再抽)。

**决策 2 · 处理模式 = 账户/租户级默认 + 每批可覆盖**(落 user/tenant 设置 · 对所有 endpoint 生效):
- 智能分拣(新用户默认推荐)· 固定当前账套 · 只识别不推送
- 上传时可临时覆盖本批。存量用户先沿用「固定当前账套 / 智能分拣+兜底」不破坏,最终目标智能分拣。

**决策 3 · seller 路由记忆 = 独立表 `seller_workspace_routes`**(seller_tax/seller_name →
workspace_client_id)· 用户绑一次下次自动命中 · 一个 workspace 可多卖方抬头/名字变体 ·
不污染 workspace_clients.tax_id。匹配顺序:routes 记忆 → workspace_clients.tax_id → name。

**UI 要求(通用层文案 · 不暴露技术词)**:
- 「ERP 自动处理方式」:智能分拣(推荐)/ 固定当前账套 / 只识别不推送
- 上传后批次结果四态:自动成功 / 已存在 / 待处理 / 技术失败可重试
- 通用层叫「ERP 买方 / ERP 客户」· per-ERP 特殊字段(MR.ERP seed customer/product)只在「高级设置」

## 🔁 ERP 推送异常 闭环交互逻辑(Zihao 2026-05-26 三问拍死)

**核心:异常队列与推送日志是同一份数据(`erp_push_logs`,铁律 #12),不是两套。**
异常队列 = "每个 (history×endpoint) 最近一条仍 failed 的 log" 的过滤视图;日志 = 全量视图。
所以**永远不会不同步** —— 不需要任何手动 sync。

**Q1:处理好异常后还要回日志点重试吗?→ 不用。** 修复 + 重试**都在异常卡片里**完成,
不跳日志页。日志页的重试按钮只是给高级用户的等价入口,不是必经路径。

**Q2:异常处理好后日志同步吗?→ 自动同步(单一源)。** 重试成功 → 写一条新 success log →
该 (history×endpoint) 的"最近一条"变 success → **卡片自动从异常队列消失**,日志页也显示成功。
前端只需在重试后**重新拉一次列表**(数据本就一致)。

**Q3:点重试就能正常推送吗?→ 能,因为重试是"重新解析"不是"重发旧件"。**
`POST /api/erp/logs/{id}/retry`(erp_routes.py:957)重试时**重新拉 history+endpoint → 重新跑
push_to_endpoint → upload_invoice_batch → _sync_master_data(重新找/建 ERP 买方+商品)+
_verify_resolved_master_data(重新反查)**。所以用户在卡片里"选对 ERP 客户 / 新建 / 确认映射"
写库后,重试会带上新映射,推送就对了。

**完整闭环(一处完成 · 不来回跳)**:
```
推送失败(如 ERR_CUSTOMER_NAME_MISMATCH)
  → log.status=failed → 同时出现在【日志:needs_action】和【异常队列:卡片】
  → 用户在异常卡片看到:为什么失败 / 哪个字段冲突(当前 ERP 客户 vs 发票买方)/ 去哪修
  → 在卡片里修:[选择正确 ERP 客户] / [新建 ERP 客户] / [确认映射]  (写映射/主数据 · picker 阶段)
  → 在卡片里点 [重试推送]  → 同一个 /retry 端点 · 重新解析+反查+推送
       ├─ 成功 → 新 success log → 卡片自动消失 + 日志显示成功(单一源 · 自动同步)
       └─ 仍失败 → 卡片用新原因刷新 → 可再修再试
```

**前端同步要求**:重试返回后,刷新异常队列(成功的卡片消失);若日志页也开着,一并刷新。
不做乐观态、不维护第二份状态(铁律 #12)。

**当前阶段(先可见+重试)**:卡片先给 [重试推送](复用 /retry)+ 可见性(为什么/哪字段/去哪修)。
[选择/新建 ERP 客户] picker 是紧接着的下一块(通用 adapter 接口 · 写映射后重试闭环同上)。

## 🔧 P1b+P1c+P1d 实现蓝图(文件级 · 下一轮照做 · 危险段必 diff 过目 + 沙箱测)

> 已读透推送内部(2026-05-26):`push_to_endpoint`(erp_push.py:492)mrerp 早路由到
> `push_mrerp_history`(244),每张 `with adapter: upload_invoice_batch([one], mappings)`
> = **每张一次浏览器登录**。ImportResult 映射现假设单张(`result.success[0]/failed[0]`)。
> auto-push(app.py:2560+)对每张 history 循环推**所有** auto_push 端点。

### P1b 处理模式存储(安全 · 先行)
- schema:`users.erp_push_mode TEXT DEFAULT 'smart'`(mirror `dup_check_enabled` · 在 users 现有
  ensure 里加列 · 不新增 ensure_*)。值:`smart`(智能分拣)/ `fixed`(固定当前账套)/ `ocr_only`(只识别)。
- DAL:`get_erp_push_mode(user_id)` / `set_erp_push_mode(user_id, mode)`(mirror dup_check)。
- 路由:`GET/PUT /api/settings/erp-push-mode`(settings_routes.py)。
- 上传覆盖:`/api/ocr/recognize` 加 Form `push_mode`(可空 · 覆盖本批)。
- **门(本轮可安全先上)**:auto-push 块开头 `mode = push_mode or get_erp_push_mode(user)`;
  `mode=='ocr_only'` → 跳过 auto-push + Xero 触发(纯跳过 · 零风险)。`smart/fixed` 暂走现状。
- UI:ERP 配置页/设置加「ERP 自动处理方式」三选(通用文案 · 默认智能分拣)。

### P1c 批量 seam(erp_push.py 重构 + 新 dispatch)
- 抽 3 个 helper(行为不变 · push_mrerp_history 改调它们 · 跑 async tripwire/contract 测试验证):
  `build_mrerp_adapter(config)`(cred enc/plain 启发式 + construct)· `flatten_history_for_mrerp(h)`
  · `load_mrerp_mappings(tenant_id)`。
- 新 `services/erp/push_dispatch.py: dispatch_endpoint_batch(endpoint, histories) -> List[result]`:
  - mrerp:build adapter **一次** → flatten 全部 → `upload_invoice_batch(flats, mappings)` **一次** →
    按 `invoice_no` 把 `result.success/failed` 回映射到每张 history → 每张一个 result dict(与
    push_to_endpoint 同 shape)。
  - 非 mrerp:循环 `push_to_endpoint`(无批量也统一接口)。
  - 统一状态词汇 + 不写 `if adapter=='mrerp'`(分支只在 dispatch 内一处)。
- 守门:dispatch 契约测试(mock upload_invoice_batch 返多行 ImportResult → 验回映射)。

### P1d 编排重写(app.py auto-push 块 · **唯一危险点** · diff + 沙箱)
- 取 mode(P1b)。`ocr_only` → 不推。
- `smart`:每张 history 已带 seller 分拣的 `workspace_client_id`(P1a 已落库)→ 取其 endpoint →
  **按 endpoint 分组** → 每组 `dispatch_endpoint_batch(endpoint, histories)` 一次 →
  写 push 日志(每张)。未匹配/未绑端点的 history → **兼容兜底**:推现有 auto_push 端点(不阻断)。
- `fixed`:全部 → 当前 workspace(切换器)绑定的 endpoint → 一组 dispatch。
- per-invoice 隔离:一张 FailedRow 不影响同批其余(upload_invoice_batch 本就 per-row 报)。
- 回滚:加 `ERP_SELLER_ROUTING` 开关(env / 配置)· 关掉即回退现"全推 auto_push 端点"。
- 守门:路由单测(单端点=现状 / 多端点=各推各 / 未匹配=兜底)· 沙箱真账号:重开 dad6fb0f
  推一张新卖方发票验路由到对账套 + 验不误杀现用户。

## 构建阶段(确认后)
- **P1a 路由记忆层**:`seller_workspace_routes` 表 + DAL(match/learn)+ 整合进 match_workspace_for_seller。
- **P1b 处理模式存储**:user/tenant 默认模式 setting + 上传 Form 覆盖参数。
- **P1c 通用 seam**:定义 `process_batch(endpoint, histories, mode)` + MR.ERP(包 upload_invoice_batch)
  + Xero(包 xero_pusher)包装 · ImportResult→统一 per-invoice 结果。
- **P1d 编排重写**:OCR 批 → 每张 seller 匹配 workspace → 按 endpoint 分组 → 每组 process_batch →
  写 push 日志(统一状态)· 模式门(只识别跳过/固定账套/智能分拣+兜底)· per-invoice 隔离。
- **P2 异常队列 + 批次中心**(四态 UI · 需 erp_push_logs.batch_id schema · 一键绑定/重推)。
- **P3 配置页通用 UI + 通用文案**(自动处理方式选择器 · ERP 买方/客户正名 · 高级设置)。
