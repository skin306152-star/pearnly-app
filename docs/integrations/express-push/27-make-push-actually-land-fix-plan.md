# Express 推送「真正落地」修复方案(施工单)

> 起于 2026-06-22 Owner 真站实测:测试语料发票推 Express 全失败。Owner 拍板「牵头修通」。
> 现状定性:**不是发票问题**(识别对、方向判定逻辑本身对)——是落地管道三处断点 + 一批误导 UI。
> 铁律:Express 推送 / OCR 识别是主路径,**改前报方案**(本文件即方案,待 Owner 批)。push 即上线。

## 验收总目标(一张票端到端)
上传一张采购票(买方=自家 มานะชัยบริการ/0735527000289)→ 自动判为采购 → 映射成分录 →
排队 → 小助手拉取 → 写进 DATAT 账套 DBF → Express 报表里看得到。销项同理(卖方=自家)。

---

## 修复点 1 · 方向判不出(direction_unknown)——【真 bug · 最高优先 · 最小改动】

**断点**:`services/ocr/recognize/persist.py:333-356`「卖方智能分拣」块。
- insert 时 `persist.py:192-217` 已正确写入 `workspace_client_id=_ws_client_id`(上传带 `X-Workspace-Client-Id` 头,缺失回落 `default_workspace_for_write` 本租户默认套账)。
- 紧接着 `match_workspace_for_seller` 返回 `none/multi` 时 `_ws_assigned=None`,却**无条件** `update_history_workspace_client_id(hid, None, ...)` → 把刚写好的套账**清成 NULL**。
- 后果:`enqueue._own_tax_id` 取不到主体 tax → `detect_by_tax` 返 None → `direction_unknown`。

**改法(一行级)**:`persist.py:340-347` 仅当 `_ws_assigned` 非空才回写;`none/multi` 保留 insert 已写的 `_ws_client_id`,**绝不回写 NULL**。

**存量补**:已上传但 `workspace_client_id=NULL` 的票(如 `RR6812-0220`),给一次性回填脚本按当前主体补上(或让 Owner 重传)。

**验收**:重传/回填后该票方向判为 purchase(不再 direction_unknown);新增单测:match 返回 none/multi 时 workspace_client_id 不被清空。

---

## 修复点 2 · 缺会计科目映射且无 UI(no_revenue_account)

**断点**:
- `sales_mapper.py:95-107` 需 `revenue_acc / ar_acc / vat_output_acc`;`mapper.py:112-124` 需 `fallback_acc / ap_acc / vat_input_acc`(注意进项 VAT 键是 **`vat_input_acc`**)。
- `common.py:104-118` `resolve_account` 先查 `mappings.accounts`(`erp_account_mappings` 表按 `pearnly_category`),再回落 `config` 科目键;**无任何默认兜底** → 全空即 fail。
- 前端 Express 向导 `src/home/erp-express-wizard.ts` 只配 `account_set`(还是小助手上报的)+ `auto_push`,**没有科目输入框**;后端 `routes/erp_endpoints_routes.py` 的 config 是自由 dict、不校验键 → 任何科目键都能存。

**★正式版做法(Owner 2026-06-22 拍板 · 比手填代码强):小助手自动发现科目 → 下拉选名字。**
- 复用现成机制:小助手已能扫账套并上报(`agent_store.store_account_sets` → `config.reported_account_sets` → 向导下拉)。科目表同理:小助手登录 Express 读科目 DBF(如 GLMAS)→ 上报科目清单(代码+名字)到 `config.reported_accounts` → Pearnly 在「科目映射」用**下拉按名字**让客户给 6 个槽位(收入/应收/销项税/采购/应付/进项税)选科目 → 客户全程看名字、不碰代码。
- 更进一步:小助手可直接读 Express **已预设**的单据类型→科目默认配置(人工录入就是靠它),能省掉客户手选。
- 依据:科目表**可自定义(每账套不同)**,故不能写死默认码,必须按账套发现 + 客户确认。companion 侧改动(读 DBF + 上报)在仓库外,交 companion 窗口;云端侧加 `reported_accounts` 接收(对齐 `store_account_sets`)+ 前端下拉。

**临时/最小做法(让 Owner 今天能测通)**:走 **config 科目键**(无需建表/迁移)。在 `erp-express-wizard.ts` `_finish()`(约 387-398,现 PATCH body 仅 `{auto_push}`)加 6 个科目输入(或直接 prod 填 config),并入 PATCH 的 `config`:
- 销项:`revenue_acc`(收入)、`ar_acc`(应收)、`vat_output_acc`(销项税)
- 进项:`fallback_acc`(采购/进货兜底)、`ap_acc`(应付)、`vat_input_acc`(进项税)
- 配「合理默认值」提示:科目码取自该账套真实 GL(Owner/会计给一组;DATAT 测试账套可先用标准码跑通)。
- ⚠️ 科目码必须存在于目标账套 GL,否则 DBF 写出引用无效科目 → Express 报表错。**不准用瞎填码冒充成功**(状态诚实)。

**改 src 必 `npm run build` + 提交 `static/dist`**(改源码不提 dist=prod 跑旧 bundle)。

**验收**:Express 连接「编辑」里能填 6 个科目;填后销项/采购都过 mapper(不再 no_revenue_account)生成借贷平的分录。

---

## 修复点 3 · 小助手账套对齐(写 ASIA-SPORT 而非 DATAT)

**现状**:云端 `config.account_set=DATAT/account_company=มานะชัยบริการ`,但小助手本地日志在写 `ASIA-SPORT`。
- 契约:`routes/erp_agent.py:63-95` heartbeat 只**接收**小助手上报的所选账套(单向镜像);lease(103-134)用 `cfg.account_set` 做白名单,不纠正小助手实际写哪个 DBF。
- **companion 运行时源码不在本仓库**(repo 内只有设计文档 + 安装器路由)。

**即时 workaround(Owner 现在就能做)**:在小助手托盘里把所选账套切回 **DATAT(\\accserver\ACCOUNT\70EXP\TEST · มานะชัยบริการ · 0735527000289 · writable)**,让它重新上报。

**云端侧根治(本仓库可改)**:`erp_agent.py:118` lease 账套不符时**显式拒并回带期望账套**(`account_set_mismatch` + config.account_set),或 heartbeat 响应把云端期望账套下发;**实际切账套须 companion 侧消费**(交 companion 窗口)。

**验收**:小助手日志 `account=บริษัท มานะชัยบริการ`;lease 下发的载荷写进 DATAT。

---

## 次要 track · 误导用户的 UI(5 项 · 见记忆 express-push-sales-blocked-and-misleading-ui)
1. 失败码 `no_revenue_account`/`direction_unknown` 翻人话。
2. 端点卡片「0 已推/待推/失败」计数器对齐真实。
3. 销项失败进不进「推送异常」四桶口径统一。
4. 主体创建页税号非 13 位静默无反馈 → 红字提示。
5. 小助手账套与云端不一致时告警。

---

## 顺序 / 分工
1. **修复点 1**(后端 bug · 最小 · 解锁方向)→ 先做,值最高。
2. **修复点 2**(前端科目输入 + dist · 解锁映射)。
3. **修复点 3 即时 workaround**(Owner 切账套)立即可做;云端根治 + companion 由集成窗口接。
4. 误导 UI 五项随手清。

施工:后端(点1)+ 前端(点2)可由本窗口/施工窗口做;companion(点3 根治)交并行 companion 窗口。PM(本窗)出单 + 验收。
