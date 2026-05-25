# Workspace 工作台改造 · B 阶段规划(设计 · 暂不上线)

> 2026-05-25 · A1/A3/B0 已上线。本文件是 B1–B5 的设计与最小改动清单,**不含任何上线动作**。
> 红线(明确不上线):登录强制弹窗 / 右上角切换器改造 / workspace 强校验 / 推送主流程 / push log 状态机。
> 概念锁定:`workspace_client_id`(账套主体=在做谁的账)与 `history.client_id`(发票买方→MR.ERP 应收客户)**两个独立字段**。

## 0. 只读扫描结论:谁还没接 workspace_client_id

`workspace_client_id` 目前**零路由消费**(仅 B0 新文件 services/workspace/store.py + alembic/005)。需要接它的「创建业务数据」接口:

| 接口 | 文件:行 | 创建什么 | 现取的归属 |
|---|---|---|---|
| `POST /api/ocr/recognize` | app.py:1822 | ocr_history【核心】 | client_id(买方·OCR 解析) |
| `POST /api/bank-recon/upload` | bank_recon_routes.py:41 | bank session | 后绑 client_id |
| `POST /api/recon/bank-v2/submit` | recon_jobs_routes.py:170 | 对账任务 | tenant/user |
| `POST /api/recon/gl-vat/submit` | recon_jobs_routes.py:226 | 对账任务 | tenant/user |
| `POST /api/vat_excel/submit` | recon_jobs_routes.py:277 | 销项税任务 | tenant/user |
| `POST /api/erp/push` | erp_routes.py:698 | 推送 | endpoint_id |

员工分配现状:`client_assignments(user_id, client_id, assigned_by)`(v118.27.7),`client_id`→clients(买方)。`restrict_client_ids` 由它派生(db.py:2632 起)。

---

## 1. B1 / B4 最小改动清单

**核心顺序铁律:B1 强校验必须晚于 B4 选择器上线**(否则没选 workspace 就全卡死)。分两相:

### B4 · workspace 切换器(前端 + 读 API)
- 新 `workspace_routes.py`:`GET /api/workspace/clients`(列出当前用户可见账套·员工按分配过滤)、`POST /api/workspace/clients`(建·仅老板)、`PUT /api/workspace/clients/{id}/endpoint`(绑已有 endpoint)。复用 B0 的 services/workspace/store.py。
- 新 `src/home/workspace-switcher.js`(Vite·铁律 #23.3)——repoint 现有 ClientSwitcher 到 workspace_clients;localStorage 新键 `active_workspace_client_id`;切换派发事件刷新页面数据。**不删旧 ClientSwitcher,先并存**。
- 业务请求带 `X-Workspace-Client-Id` 头(或 query)。

### B1 · 后端强校验(两相·防卡死)
- 新 helper `resolve_workspace(request)`:读头/参 active_workspace_client_id → 校验访问权(老板:同 tenant 任意;员工:在 client_assignments 的 workspace 版里)→ 返 id 或 400「请先选择当前客户」/ 403 越权。
- **相 1(非破坏)**:create 路由把 workspace_client_id **写入**新记录(可空·缺失不拒)。
- **相 2(强校验·B4 全量上线后)**:缺 workspace_client_id → 400 拒绝。
- 落点:ocr/recognize、bank-recon/upload、3 个 recon submit。erp/push 校验 endpoint 属当前 workspace。

---

## 2. B2 · 登录后选 workspace 产品方案(红线·上线前需再确认)

登录成功 → `GET /api/workspace/clients` 分流:
- **0 个**:老板→引导「创建第一个账套客户」;员工→空状态「尚未被分配客户,请联系老板」。
- **1 个**:自动选中,**不弹窗**(避免单公司用户每次摩擦)。
- **>1 个**:弹窗「选择本次处理的客户」(选已有 / 新建[仅老板] / 稍后)。
- 选中前**只放行**:账号设置 / 客户管理 / 帮助;其余创建类业务页 gating。
- 实现:`src/home/*`(铁律 #23.3);**改登录流=影响所有用户=铁律 #16 红线 → 上线前把交互方案给 Zihao 过 + 浏览器实测**。

---

## 3. 员工权限迁移方案(client_assignments → workspace)

- **现状**:client_assignments 按 client_id(买方)分;员工列表过滤用 restrict_client_ids(买方维度)。
- **目标**:员工权限按 **workspace_client_id**(账套主体)分。
- **迁移(非破坏)**:
  1. 加表/列:`workspace_assignments(user_id, workspace_client_id, assigned_by)`(或给 client_assignments 加 workspace_client_id 列并双写过渡)。
  2. 老板建员工时配「可处理 workspace 公司」(全部/指定/暂不分配·默认指定)。
  3. 员工 workspace 列表 + 业务数据按 workspace_assignments 过滤;越权传 id → 403。
  4. **「新建客户」权限拆两种**:建买方(日常·员工常需)vs 建 workspace 账套(重大·默认仅老板)。
  5. 旧 client_assignments(买方过滤)**保留不动**——那是另一维度(员工能看哪些买方的对账),与 workspace 范围正交。

---

## 4. 批次中心复用 erp_push_logs 设计(设计·不上线状态机)

- **不另建 erp_push_jobs**(避免双状态源·铁律 #12)。给 erp_push_logs 加 `batch_id TEXT`(Alembic + 启动 ensure 双跑·加法)。
- 一次上传 = 一个 batch_id,该批所有 push log 共享。
- 读 API:`GET /api/erp/batches`(GROUP BY batch_id 聚合:总/成功/失败/blocked 数)+ `GET /api/erp/batches/{id}`(明细行)。
- 前端:上传后**只弹一个批次提示**(不弹 N 次 toast),点进看四类列表 + 一键重推。
- ⚠️ **涉及状态机的部分(入队即写 queued / 加 queued·running·blocked 到 status CHECK)= 用户明确不上线** → 本期仅做 batch_id 聚合 + 单 toast,状态扩展等解禁后再做。

---

## 5. 上线门槛回顾(本期严禁)
登录强制弹窗 / 切换器改造 / workspace 强校验 / 推送主流程改动 / push log 状态机改动 —— **全部仅设计,等 Zihao 解禁 + B2 交互方案确认后再分相上线**。
