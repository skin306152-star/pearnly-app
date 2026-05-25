# B3 · 员工 workspace 权限迁移设计(设计 · 暂不上线)

> 2026-05-26 · 纯设计。把员工权限从"按发票买方"迁到"按 workspace 账套主体"。
> 不改业务代码、不动 schema、不碰主路径 —— 实现需 Zihao 逐步确认。

## 1. 现状(只读梳理)

- 表 `client_assignments(user_id, client_id, assigned_by)`(v118.28.1)· `client_id` 指向 **`clients`(= 发票买方)**。
- `get_visible_client_ids_for_user(user)`:`owner/super → None`(不加 filter);`member → [client_id...]`(空=没分到)。出错返 `[]`(拒绝访问·不暴露)。
- 各列表接口收 `restrict_client_ids` 由此派生(bank_recon / exceptions / mappings 等),`WHERE client_id IN (...)`。
- 管理:`set_employee_assignments` / `list_assignments_by_employees`。

**问题**:这套是按**买方**维度切的。但在新模型里,员工权限应按 **workspace 账套主体**(在为哪家公司做账)切 —— "员工能处理 BAKELAB 的账" ≠ "员工只能看某些买方"。买方是每张发票的对方,不该用来 gate 员工。

## 2. 目标模型

- 员工被分配到 **workspace 公司**(0/指定/全部)· 默认"指定"(防越权)。
- 员工选 workspace 时只看分到的;只有 1 个自动选;0 个 → 空状态"联系老板分配"。
- 员工的上传/对账/推送/批次/异常/日志,**按 workspace_client_id 过滤**(B1 写入后)。
- 越权:员工传未授权 workspace_client_id → **403**。
- **「新建客户」拆两种权限**:
  - 新建 **buyer**(发票对方/应收客户)= 日常录入 · 员工通常可(由 OCR 自动建或抽屉里加);
  - 新建 **workspace 账套**(新公司主体)= 重大 · **仅 owner/super**(B4 后端 `create_workspace_client` 已用 `_require_owner_or_super` 锁住)。

## 3. 迁移方案(非破坏 · 分步)

### 步骤 1:加 workspace 分配存储(schema · 待确认)
二选一:
- (A) 新表 `workspace_assignments(user_id, workspace_client_id, assigned_by, created_at)`(干净·推荐);
- (B) 给 `client_assignments` 加列 `workspace_client_id`(复用旧表·过渡期双维度共存)。
走 Alembic + 启动 ensure 双跑(同 B0)。**这是 schema 改动 → 先停确认。**

### 步骤 2:加派生函数(纯新增 · 不改旧)
- `get_visible_workspace_ids_for_user(user)`:镜像现有买方版(owner/super→None;member→分配的 workspace_client_id 列表;出错→[] 拒绝)。
- `set_employee_workspaces` / `list_workspace_assignments_by_employees`:镜像现有管理函数。
- **旧 `get_visible_client_ids_for_user`(买方维度)保留不动** —— 两维度正交,互不影响。

### 步骤 3:业务接口接 workspace 过滤(碰主路径 · 待 B1 + 确认)
- 各创建/查询接口在 B1 写入 workspace_client_id 后,member 的列表/详情按 `get_visible_workspace_ids_for_user` 过滤;创建/推送校验 workspace 归属,越权 403。
- **相位**:先只读过滤(非破坏)→ 再写入校验(B1 相 2)→ 强拒。

### 步骤 4:员工管理 UI(前端 · 待确认)
- 老板建/改员工时配"可处理 workspace 公司"多选(全部/指定/暂不分配·默认指定)。
- 复用现有团队/员工管理页 · 新增 workspace 多选控件。

## 4. 验收标准(实现后跑)

1. 老板建员工可分配 workspace 公司(默认指定·非全部)。
2. 员工登录只看到分到的 workspace;1 个自动选;0 个不能进业务页。
3. 员工传未授权 workspace_client_id → 403(不只前端隐藏)。
4. 员工上传发票 → 该发票 workspace_client_id = 当前 workspace(buyer 仍按 OCR 真实买方,不受影响)。
5. 员工只看到当前 workspace 的推送日志/批次/异常/成本明细。
6. 老板切到某 workspace 看到该公司全量(含员工产生的)。
7. 旧买方维度 client_assignments 不被破坏(若仍在用)。

## 5. 红线
- 员工权限按 **workspace**(账套)分,不按 buyer 分;两维度不混。
- 不把 workspace_client_id 写成 buyer client_id。
- 创建 workspace 账套仅 owner;创建 buyer 可员工。
- schema / 主路径过滤 / 前端 / 强校验 —— 每步实现前停下给方案确认。
