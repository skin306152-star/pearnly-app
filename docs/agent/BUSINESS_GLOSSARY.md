# BUSINESS_GLOSSARY.md · Pearnly 业务词典(防混淆)

> 目的:让每个 AI 进项目不再猜业务概念。**词义以本文件 + 代码为准**,不以散落注释为准。
> 最后更新:2026-05-26。

## ⭐ 最易混的两个"客户"(必背)

| 概念 | 字段 | 是什么 | 谁决定 | 在 MR.ERP 对应 |
|---|---|---|---|---|
| **workspace 客户**(账套主体) | `workspace_client_id`(B0 新增 · 表 `workspace_clients`) | **在为哪家公司做账**。账套主体 / 数据归属 / 权限范围 / 用哪个 ERP endpoint。登录时选。 | 用户登录后选「当前客户」 | 一个 ERP **公司/账套**(comidyear+seldb)· workspace 绑一个**已有** endpoint |
| **发票买方**(应收客户/对方) | `history.client_id`(表 `clients`) | **这张发票卖给谁**。每张发票 OCR 出 buyer_name/buyer_tax 后解析/学习归属。 | OCR + `buyer_to_client_memory` 自动认 | 一个 **应收客户(ลูกหนี้การค้า / debtor)**· 不存在则自动创建 |

**铁规**:
- 选 workspace = BAKELAB **不代表**每张发票买方都是 BAKELAB。
- **绝不**把所有发票的 `client_id` 覆盖成 workspace_client_id —— 那会把所有发票记到一个应收客户名下(账错)。
- 这两个是**两个独立字段**,历史上曾被一个 `client_id` 同时当用,是混乱根源(已由 B0 拆开)。
- ⚠️ `clients` 表的旧注释写"事务所给多家公司做账·把发票归属到客户",但代码实际把 `clients`/`history.client_id` 当**买方**用(见 `buyer_to_client_memory`、`mrerp_customer_sync._extract_buyer`)。**信代码,不信旧注释。**

## 核心实体 / 表

| 名 | 表 / 位置 | 说明 |
|---|---|---|
| tenant(租户) | `tenants` / `users.tenant_id` | 一个账号/事务所。老板+员工同 tenant 共享数据。 |
| workspace 客户 | `workspace_clients`(B0) | 见上。`erp_endpoint_id` 列 = 绑定的已有 ERP endpoint(可空)。 |
| 发票买方 | `clients` + `buyer_to_client_memory` | 见上。买方名/税号 → client_id 的学习与解析(`try_resolve_buyer_to_client`,税号优先)。 |
| ocr_history | `ocr_history` | 一张识别后的发票。`client_id`=买方;`workspace_client_id`=账套(B0 加·可空·暂无路由消费)。 |
| ERP endpoint | `erp_endpoints` | 一个 ERP 连接(MR.ERP/Xero)。含 system_url/账套(comidyear/seldb)/加密凭据/adapter/enabled/auto_push/seed_customer_code。 |
| mapping(映射) | `erp_*_mappings`(`get_mrerp_mappings_bundle`) | 买方 client_id → MR.ERP customer_code;商品/科目/税率映射。 |
| 推送日志 | `erp_push_logs` | **推送状态唯一来源**(见 `ERROR_CODES_AND_STATES.md`)。 |
| 员工分配 | `client_assignments(user_id, client_id)` | v118.27.7 · 现按**买方 client_id** 过滤(`restrict_client_ids`)。⚠️ B3 要迁到按 **workspace** 分(账套维度)· 两维度正交。 |

## MR.ERP 集成事实(无 API · 走 Playwright)

- 站点 `https://www.mrerp4sme.com`(老 PHP)· 登录 `/login/login.php` → 选账套 `/login/selectdb.php` → 主菜单。
- 沙箱账套:**TEST2019**(comidyear=6) / **TEST2020**(comidyear=15)· 测试账号 test01/test01。
- 客户列表 `/armas/allview.php`:**分页·每页 ~30 条** → 必须用搜索框 `#txtsearch`(onkeyup=`searchdata(1)` / `#btnsearch`=`searchdata(2)`)查全量,否则第 31+ 个客户匹配不上(假 ERR_NO_CUSTOMER_MAPPING)。**搜索只覆盖 码/类型/名,不含税号**。
- 自动建买方 = **copy-from-seed**(克隆一个现有客户继承主数据引用 · 没配 seed 则自动挑一个应收类型客户)· 见 `services/erp/mrerp_customer_sync.py`。
- 老 PHP **单账号单会话**:2 worker 同账号同时登录会互踢 → ERR_AUTH → 必须跨进程串行(`services/erp/session_lock.py` · pg advisory xact lock)。
- 返码 ≠ 真写库(铁律 #9):`importpc.php` 返 '1'/'2' 不等于成功 → 以报表/listing/bill_no 为准。

## 批次(batch)

- 一次上传 N 张发票 = 一个批次。聚合显示在「批次中心」(B5 设计中)。
- 展示态从 `erp_push_logs` **派生**(`services/erp/batch_view.py`),不新增状态源。
- 聚合需要 `erp_push_logs.batch_id`(尚未加 · schema 改动待确认)。

## 计费(credits)

- 2026-05-24 起纯 credits 按量扣费(单一套餐)· OCR 准入只看余额>0 或豁免。
- 改计费/余额/套餐 = 高敏红线,必须 Zihao 在场。
