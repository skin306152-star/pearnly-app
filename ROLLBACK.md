# 回滚预案 · Credits System Release

> 适用版本:`feature/credits-system` @ `5de6cc5` (2026-05-19)
> 前一个稳定 commit:`1c44166` (Tasks 1-6 之前) / `e02f6de` (Credits 系统初版之前)
> 数据库快照:`/opt/mrpilot/backups/pre_credits_release_20260519_152218.sql` (3.3M)

---

## 何时触发回滚

- /api/health 持续 5xx 超过 60 秒
- 余额扣费明显错误(误扣豁免账号、多扣、负余额)
- 大量用户报告无法登录(非已知 Supabase 瞬态 search_path 抖动)
- 多公司切换导致用户进入错误数据空间

---

## 1. 代码回滚

### 1A. 全量回到 Tasks 1-6 之前

```bash
ssh root@45.76.53.194
cd /opt/mrpilot
systemctl stop mrpilot

# 工作树同步到最近一个稳定 commit
git fetch origin
git checkout feature/credits-system
git reset --hard 1c44166      # Tasks 1-6 之前的最后一个稳定 commit
```

本地仓库同步:

```bash
cd D:\Users\Skin\Desktop\pearnly_project
git fetch
git reset --hard 1c44166
```

### 1B. 单文件回滚(温和方案)

只回滚问题最大的几个文件:

```bash
# 服务器
cd /opt/mrpilot
git checkout 1c44166 -- app.py db.py auth.py
git checkout 1c44166 -- static/home.js static/home.html
git checkout 1c44166 -- static/admin/admin.js static/admin/admin-i18n.js
gzip -9 -k -f static/home.js static/home.html static/admin/admin.js static/admin/admin-i18n.js
systemctl restart mrpilot
```

### 1C. 拷贝部署(无 git 干扰)

```bash
# 本地
cd D:\Users\Skin\Desktop\pearnly_project
git show 1c44166:app.py > /tmp/app.py.rollback
git show 1c44166:db.py > /tmp/db.py.rollback
git show 1c44166:auth.py > /tmp/auth.py.rollback
# 等等
scp /tmp/*.rollback root@45.76.53.194:/opt/mrpilot/
ssh root@45.76.53.194 'cd /opt/mrpilot && mv app.py.rollback app.py && mv db.py.rollback db.py && mv auth.py.rollback auth.py && systemctl restart mrpilot'
```

---

## 2. 数据库回滚

### 风险评估

本次发布对 DB schema 的变更只有 **2 处 ADD COLUMN**:

| 表 | 列 | 类型 | 风险 |
|---|---|---|---|
| `users` | `active_tenant_id` | UUID,可空,FK → tenants | **低**(可空列,不读不影响) |
| `tenant_credits` | `low_balance_notified_at` | TIMESTAMPTZ,可空 | **低**(可空列) |

代码回滚后,这两个列继续存在 **不会** 破坏旧代码(旧代码 `SELECT *` 会带回多余字段,Python dict 忽略即可)。
因此 **通常不需要回滚 DB**,只回滚代码即可。

### 必须回滚 DB 的场景

- 业务数据被错误扣费 / 多扣 / 负余额
- `topup_requests` 表被错误状态污染
- `user_company_roles` 误绑定到错误租户

### 2A. 全量恢复(核选项,会丢失发布后产生的所有数据)

```bash
ssh root@45.76.53.194
cd /opt/mrpilot
. .env
systemctl stop mrpilot

# 备份当前数据库(以防回滚错误)
/usr/lib/postgresql/17/bin/pg_dump --no-owner --no-acl --schema=public --dbname="$DATABASE_URL" \
  > /opt/mrpilot/backups/before_rollback_$(date +%Y%m%d_%H%M%S).sql

# 恢复
/usr/lib/postgresql/17/bin/psql "$DATABASE_URL" -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
/usr/lib/postgresql/17/bin/psql "$DATABASE_URL" < /opt/mrpilot/backups/pre_credits_release_20260519_152218.sql

systemctl start mrpilot
```

### 2B. 仅回滚 schema 变更(保留新数据)

```bash
ssh root@45.76.53.194
cd /opt/mrpilot
. .env

/usr/lib/postgresql/17/bin/psql "$DATABASE_URL" <<'SQL'
-- 删除新加的列(数据丢失,但其他表 / 行不动)
ALTER TABLE users DROP COLUMN IF EXISTS active_tenant_id;
ALTER TABLE tenant_credits DROP COLUMN IF EXISTS low_balance_notified_at;
SQL
```

### 2C. 仅修复特定脏数据(精准方案)

```sql
-- 例:取消所有 active_tenant_id(让所有用户回到 JWT 里的 tenant_id)
UPDATE users SET active_tenant_id = NULL;

-- 例:清空低余额通知时间戳(让邮件 24h 防抖重置)
UPDATE tenant_credits SET low_balance_notified_at = NULL;

-- 例:回滚特定误批准的充值
UPDATE topup_requests SET status = 'pending', reviewed_by = NULL, reviewed_at = NULL
WHERE id = ?;
```

---

## 3. 关键回滚检查点

### 余额数据 · tenant_credits
```sql
SELECT tenant_id, balance_thb, updated_at FROM tenant_credits ORDER BY updated_at DESC LIMIT 10;
```

### 充值申请 · topup_requests
```sql
SELECT id, status, amount_thb, reviewed_at, created_at
FROM topup_requests
WHERE created_at >= '2026-05-19'
ORDER BY id DESC;
```

### 员工关系 · user_company_roles
```sql
SELECT user_id, tenant_id, role, is_active, joined_at
FROM user_company_roles
WHERE joined_at >= '2026-05-19';
```

### active_tenant_id 用户数
```sql
SELECT COUNT(*) FROM users WHERE active_tenant_id IS NOT NULL;
```

### 月度用量(本月)
```sql
SELECT tenant_id, year_month, pages_used
FROM monthly_page_usage
WHERE year_month = TO_CHAR(NOW() AT TIME ZONE 'Asia/Bangkok', 'YYYY-MM');
```

---

## 4. 验证回滚成功

### 服务健康
```bash
curl https://pearnly.com/api/health    # 期望 200
ssh root@45.76.53.194 systemctl is-active mrpilot    # 期望 active
```

### 路由层面(回滚到 1c44166 后,新路由应不存在)
```bash
curl -o /dev/null -w "%{http_code}\n" https://pearnly.com/api/my-companies
# 回滚成功:404 · 仍存在:401 → 说明代码未真正回滚
```

### 数据完整性
```bash
ssh root@45.76.53.194 'cd /opt/mrpilot && . .env && /usr/lib/postgresql/17/bin/psql "$DATABASE_URL" -c "
SELECT
  (SELECT COUNT(*) FROM users) AS users,
  (SELECT COUNT(*) FROM tenants) AS tenants,
  (SELECT COUNT(*) FROM tenant_credits) AS wallets,
  (SELECT COUNT(*) FROM topup_requests) AS topups,
  (SELECT SUM(balance_thb) FROM tenant_credits) AS total_balance;
"'
```

预期值(快照时间 2026-05-19 15:22):
- users: 9
- tenants: 9
- tenant_credits: 9
- 余额总和:与快照一致或大于(小于 → 异常)

### 真实用户测试
- 用 `skin306152@gmail.com` 登录
- 上传 1 张测试发票
- 看是否能扫单(豁免账号应跳过扣费)
- 看「使用明细」是否能正常打开

---

## 5. 联系人 · 升级路径

- 服务器:Vultr 45.76.53.194 · root SSH
- 数据库:Supabase Project `aydjsgmirjpkjaqknmlg` · region `ap-southeast-1` · pooler 6543
- 部署目录:`/opt/mrpilot/`
- 静态文件目录:`/opt/mrpilot/static/`(nginx 直接服务)
- systemd:`mrpilot.service`
- 备份目录:`/opt/mrpilot/backups/`
- 日志:`journalctl -u mrpilot -f`

---

## 6. 不要做的事

- ❌ 不要 `rm -rf /opt/mrpilot/static/.gz` 后忘记重启 — nginx 会 404
- ❌ 不要在 production DB 上跑 `DROP TABLE` — 用 `ALTER TABLE DROP COLUMN`
- ❌ 不要 `git push --force` 已发布的分支
- ❌ 不要直接在服务器上 `vim` 编辑代码 — 走 scp 流程,代码留在本地 git
- ❌ 不要禁用 SMTP 配置 — 邮件发送是 try/except 兜底,失败不影响主流程

---

## 附:回滚命令清单(快速参考)

```bash
# 1. 代码回滚(温和)
ssh root@45.76.53.194 'cd /opt/mrpilot && git checkout 1c44166 -- app.py db.py auth.py static/home.js static/home.html static/admin/admin.js static/admin/admin-i18n.js && gzip -9 -k -f static/home.js static/home.html static/admin/admin.js static/admin/admin-i18n.js && systemctl restart mrpilot'

# 2. DB schema 仅回滚新列
ssh root@45.76.53.194 'cd /opt/mrpilot && . .env && /usr/lib/postgresql/17/bin/psql "$DATABASE_URL" -c "ALTER TABLE users DROP COLUMN IF EXISTS active_tenant_id; ALTER TABLE tenant_credits DROP COLUMN IF EXISTS low_balance_notified_at;"'

# 3. 健康验证
curl -o /dev/null -w "%{http_code}\n" https://pearnly.com/api/health
```
