# B6 · 老数据 workspace 归属补齐设计(设计 · 暂不上线)

> 2026-05-26 · 纯设计。老业务数据没有 workspace_client_id,需要"未归属队列 + 批量分配",
> 且新数据不再产生未归属。不改业务代码、不动数据、不碰主路径 —— 实现需 Zihao 确认。

## 1. 现状

- B0 给 `ocr_history` 加了 `workspace_client_id`(可空)· **历史行全为 NULL**(没回填)。
- 老 `ocr_history.client_id`(买方)有值或 NULL —— 那是**买方维度**,与 workspace 无关,**保持不动**。
- 其它业务表(bank session / recon task 等)同理:B0/后续才加 workspace_client_id,老行为 NULL。

**"未归属" 的定义**:`workspace_client_id IS NULL`(不是 client_id 为空)。

## 2. 目标

- 老板能看到 **"未归属"队列**(workspace_client_id 为空的业务数据),并**批量分配**到某个 workspace 公司。
- 员工默认**看不到**未归属数据(除非该数据是员工自己产生且老板允许)。
- **新数据不再产生未归属**(由 B1 在创建时写入 workspace_client_id 保证 · B1 相 2 强校验后彻底杜绝)。

## 3. 方案(非破坏 · 只读优先)

### 步骤 1:未归属查询(纯新增只读 · 不改老行为)
- `services/workspace/store.py` 加 `list_unassigned_history(tenant_id, limit, offset)`:`WHERE workspace_client_id IS NULL`(tenant 隔离)· 只读。
- 同模式可扩展到其它业务表(按需)。

### 步骤 2:批量分配(写操作 · 待确认)
- `assign_history_to_workspace(history_ids, workspace_client_id, tenant_id)`:批量 `UPDATE ocr_history SET workspace_client_id=%s WHERE id = ANY(%s) AND tenant_id=%s`。
- **只写 workspace_client_id,绝不动 client_id(买方)**。
- 幂等 · tenant 隔离 · 越权拒绝。

### 步骤 3:UI(前端 · 待确认)
- 老板侧"未归属"页/标签:列出未归属发票 · 多选 · 一键"分配到 [workspace 下拉]"。
- 员工侧:列表默认过滤掉未归属(`get_visible_workspace_ids_for_user` 为 member 时,NULL 不在其可见集 → 自然不显示)。

### 步骤 4:回填策略(可选 · 一次性 · 待确认)
- 若某 tenant 历史上只服务一家公司:可一次性把该 tenant 的 NULL 行回填为那家 workspace(脚本 · 一次性 · 先 dry-run 计数再执行)。
- 多公司 tenant:不自动猜 · 留给老板在"未归属队列"手动批量分配(避免分错账)。

## 4. 与 B1 的关系(顺序)

- B1 相 1(创建时**可写** workspace_client_id 不强制)上线后 → 新数据**大多**带 workspace,但允许暂空。
- B6 处理"相 1 之前的老数据" + "相 1 期间漏填的"。
- B1 相 2(强校验)上线后 → 新数据**必带** workspace → 未归属只剩纯历史存量,B6 队列逐步清零。

## 5. 验收标准(实现后)

1. 老板能看到未归属队列(workspace_client_id IS NULL)· 分页。
2. 老板批量分配后,这些发票 workspace_client_id = 选定公司;client_id(买方)不变。
3. 员工默认看不到未归属数据。
4. B1 相 2 上线后,新上传不再产生未归属(强校验保证)。
5. 回填脚本(若用)先 dry-run 计数 · 多公司 tenant 不自动猜。

## 6. 红线
- "未归属" = workspace_client_id 空,**不是** client_id(买方)空 —— 两者别混。
- 批量分配只写 workspace_client_id,不碰买方。
- 不自动猜多公司 tenant 的归属(会分错账)。
- 写操作 / UI / 回填脚本 —— 每步实现前停下给方案确认。
