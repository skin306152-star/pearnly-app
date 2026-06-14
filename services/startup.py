# -*- coding: utf-8 -*-
"""
Pearnly · 应用启动 / 关闭序列(REFACTOR-WA-B1 · 2026-05-29 从 app.py lifespan 抽出)

纯搬家 · 0 逻辑改 · app.py 留瘦 lifespan 壳:
    @asynccontextmanager
    async def lifespan(app):
        tasks = await run_startup()
        yield
        await run_shutdown(tasks)

run_startup():启动自检 + 各域 db.ensure_* 建表/列(全 try/except 不阻断)+ 写 git-deploy.sh
  + playwright 自举(detached)+ users profile 列 + 中断任务恢复 + 起后台 task(邮箱抓取/
  ERP 重试/对账 embedded worker)· 返回 {email_task, erp_retry_task} 供 shutdown cancel。
run_shutdown(tasks):停 embedded 对账 worker + cancel 两个后台 task。
"""

import os
import asyncio
import logging

from services.playwright_bootstrap import ensure_playwright_installed
from services.background_loops import email_ingest_loop, erp_retry_loop
from services.startup_lock import startup_ddl_lock
from services.users.columns import ensure_user_profile_columns

logger = logging.getLogger("mr-pilot")


# v118.33.7 · 健壮版 git-deploy.sh(带回滚 + 健康检查 + 日志)· app 启动时写入磁盘
_GIT_DEPLOY_SH = r"""#!/bin/bash
# ============================================================
# git-deploy.sh  v118.33.10.1
# 由 app.py 启动时自动写入 · 请勿手动修改（重启会覆盖）
# 流程：fetch → reset hard → cp static → restart → health check
# 失败时回滚到上一个 GitHub commit（不会回滚到本地旧 commit）
# ============================================================
LOG=/var/log/mrpilot-deploy.log
REPO=/opt/mrpilot
REMOTE=pearnly
BRANCH=master
HEALTH_URL=http://localhost:7860/api/health
MAX_WAIT=180  # 等待服务启动的最大秒数 (v118.34.8 拉到 3 分钟 · 兜底 pip+chromium 慢网络)

echo "======================================" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') git-deploy start" >> "$LOG"

cd "$REPO" || { echo "cd failed" >> "$LOG"; exit 1; }

# 1. 记录 GitHub 上一个已知的好版本作为回滚目标
#    用远端追踪分支（不是本地 HEAD），避免回滚到比 GitHub 更老的本地 commit
PREV_HEAD=$(git rev-parse "$REMOTE/$BRANCH" 2>/dev/null || echo "")
echo "prev GitHub HEAD: $PREV_HEAD" >> "$LOG"

# 2. Fetch
if ! git fetch "$REMOTE" "$BRANCH" >> "$LOG" 2>&1; then
    echo "git fetch FAILED" >> "$LOG"
    exit 1
fi

NEW_HEAD=$(git rev-parse FETCH_HEAD 2>/dev/null || echo "")
echo "new HEAD:  $NEW_HEAD" >> "$LOG"

if [ "$PREV_HEAD" = "$NEW_HEAD" ]; then
    echo "already up to date — skipping restart" >> "$LOG"
    exit 0
fi

# 3. reset --hard 到最新 GitHub commit（同时移动本地 HEAD 指针）
if ! git reset --hard FETCH_HEAD >> "$LOG" 2>&1; then
    echo "git reset failed — abort" >> "$LOG"
    exit 1
fi

# 4. 复制静态资源
mkdir -p static
cp -f home.html home.js home.css login.html static/ 2>> "$LOG" || true

# 4.5. v118.34.9 · 极简版 · 只装 playwright(用 mrpilot 的 venv python
#     如果存在,否则用 system python3)· 每步 timeout 防止卡死
PY=/opt/mrpilot/venv/bin/python
if [ ! -x "$PY" ]; then PY=/usr/bin/python3; fi
echo "using python: $PY" >> "$LOG"

echo "pip install playwright..." >> "$LOG"
timeout 60 "$PY" -m pip install playwright >> "$LOG" 2>&1 || \
    timeout 60 "$PY" -m pip install playwright --break-system-packages \
        >> "$LOG" 2>&1 || \
    echo "pip install playwright non-fatal failure" >> "$LOG"

# 4.6. v118.34.9 · chromium 已装时跳过(idempotent)
echo "playwright install chromium..." >> "$LOG"
timeout 120 "$PY" -m playwright install chromium >> "$LOG" 2>&1 || \
    echo "playwright install chromium non-fatal failure" >> "$LOG"

# 4.7. v118.34.11 · 装 chromium 运行时系统依赖 (apt install libnss3 libgbm1 ...)
#     没这步 BrowserType.launch 立刻 TargetClosedError · 因为 chromium
#     二进制 ≠ chromium 能跑 · 还需要十几个 .so · install-deps 用 apt 装齐
echo "playwright install-deps chromium..." >> "$LOG"
timeout 180 "$PY" -m playwright install-deps chromium >> "$LOG" 2>&1 || \
    echo "playwright install-deps chromium non-fatal failure" >> "$LOG"

# 4.8. v118.35.0.57 · 装齐 requirements.txt 全部依赖(防新依赖漏装 · 如 xlrd 这次就漏了)
#     幂等(已装的 pip 自动跳过)· 非致命(pip 失败不挡部署)· timeout 防卡死
#     用同一个 $PY(venv 优先)· 保证装到服务真正用的 python
echo "pip install -r requirements.txt..." >> "$LOG"
if [ -f requirements.txt ]; then
    timeout 240 "$PY" -m pip install -r requirements.txt >> "$LOG" 2>&1 || \
        timeout 240 "$PY" -m pip install -r requirements.txt --break-system-packages >> "$LOG" 2>&1 || \
        echo "pip install -r requirements.txt non-fatal failure" >> "$LOG"
fi

# 4.9. v118.35.0.68 · 清 pip/playwright 解压临时残渣(铁律 #24 · 2026-05-24 血泪根因)
#     pip 装大包(torch ~2.7G)往 /tmp 解压 · 装完不清会累积撑爆硬盘 →
#     Nginx 写不下上传 body → 对账 500(mrerp 真因)。删了下次自建 · 顺带磁盘体检。
echo "cleaning /tmp/pip-* residue..." >> "$LOG"
rm -rf /tmp/pip-* >> "$LOG" 2>&1 || true
DISK_USE=$(df --output=pcent / 2>/dev/null | tail -1 | tr -dc '0-9')
echo "disk usage after cleanup: ${DISK_USE}%" >> "$LOG"
if [ "${DISK_USE:-0}" -ge 85 ]; then
    echo "WARNING: disk >= 85% after cleanup — investigate /tmp /root /var/log" >> "$LOG"
fi

# 5. 重启服务
echo "restarting mrpilot..." >> "$LOG"
systemctl restart mrpilot >> "$LOG" 2>&1

# 6. 健康检查（等服务起来）
echo "waiting for health check..." >> "$LOG"
for i in $(seq 1 $MAX_WAIT); do
    sleep 1
    HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP" = "200" ]; then
        echo "health check OK after ${i}s (new HEAD: $NEW_HEAD)" >> "$LOG"
        rm -f /opt/mrpilot/.deploy_rollback 2>/dev/null || true  # 部署成功 · 清旧回滚 marker
        exit 0
    fi
done

# 7. 服务未恢复 → ① 回滚运行版本到上一个 GitHub 好版本(保命 · 绝不回滚到更老本地 commit)
#    ② 写 marker 记录坏 commit → loop 每轮读它 → revert bad commit + 重做直到真绿(闭环"直到搞好")
echo "health check FAILED after ${MAX_WAIT}s — rolling back to $PREV_HEAD (bad=$NEW_HEAD)" >> "$LOG"
if [ -n "$PREV_HEAD" ]; then
    git reset --hard "$PREV_HEAD" >> "$LOG" 2>&1
    cp -f home.html home.js home.css login.html static/ 2>> "$LOG" || true
    systemctl restart mrpilot >> "$LOG" 2>&1
    echo "rollback done — waiting for service..." >> "$LOG"
    sleep 5
    HTTP2=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    echo "post-rollback health: $HTTP2" >> "$LOG"
    # marker:谁回滚了什么(loop / 主控读它即知上次部署被回滚 → 去 revert+重做)
    printf '%s rolled_back bad=%s good=%s post_rollback_health=%s\n' \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$NEW_HEAD" "$PREV_HEAD" "$HTTP2" \
        > /opt/mrpilot/.deploy_rollback 2>/dev/null || true
fi
exit 1
"""


def _boot_schema_ddl() -> None:
    """启动期全部建表/补列(幂等)· 调用方负责套 startup_ddl_lock 跨 worker 串行。"""
    # 各域建表/补列:全部幂等 · 逐个独立 try/except(一处失败不拦其余)· 与 alembic 双跑兜底
    # (prod 无 alembic 钩子)。erp adapter/status CHECK 白名单含 mrerp/skipped_dup —— 历史漏
    # migration 致 500,函数幂等,已含则跳过。
    boot_ensures = [
        (db.ensure_ocr_cost_log_table, "ocr_cost_log 建表"),
        (db.ensure_clients_table, "clients 建表"),
        (db.ensure_workspace_tables, "workspace_clients 建表"),
        (db.ensure_seller_route_table, "seller_workspace_routes 建表"),
        (db.ensure_supplier_categories_table, "supplier_categories 建表"),
        (db.ensure_buyer_to_client_table, "buyer_to_client_memory 建表"),
        (db.ensure_google_sub_column, "google_sub 列"),
        (db.ensure_line_uid_column, "line_uid 列"),
        (db.ensure_password_changed_at_column, "password_changed_at 列"),
        (db.ensure_email_codes_table, "email_codes 建表"),
        (db.ensure_gl_vat_task_table, "gl_vat_task 建表"),
        (db.ensure_membership_tables, "membership 建表"),
        (db.ensure_billing_balance_table, "billing_balance_log 建表"),
        (db.ensure_exceptions_tables, "exceptions 建表"),
        (db.ensure_notification_tables, "notification 建表"),
        (db.ensure_erp_retry_columns, "erp_push_logs retry 列"),
        (db.ensure_erp_endpoints_adapter_constraint, "erp_endpoints adapter constraint"),
        (db.ensure_erp_push_logs_adapter_constraint, "erp_push_logs adapter constraint"),
        (db.ensure_erp_push_logs_status_constraint, "erp_push_logs status constraint"),
        (db.ensure_bank_recon_client_id_column, "bank_reconcile_sessions.client_id 列"),
        (db.ensure_erp_mapping_tables, "erp_mapping 建表"),
        (db.ensure_erp_oauth_tables, "erp_oauth 建表"),
        (db.ensure_vat_recon_tables, "vat_recon 建表"),
        (db.ensure_vat_recon_tasks_table, "vat_recon_tasks 建表"),
        (db.ensure_bank_recon_v2_table, "bank_recon_v2 建表"),
    ]
    for ensure_fn, label in boot_ensures:
        try:
            ensure_fn()
        except Exception as e:
            logger.warning(f"启动 {label} 失败: {e}")

    # P1.1 BUG-FIX-P1.1 v118.35.0.41 · 4 模块 task/row 表加 field_overrides JSONB
    # 跟 alembic/versions/002_field_overrides_4_modules.py 双跑(prod 启动兼容)
    # 铁律 #21 ✅:新 schema 函数独立 services/db_migrations/ · 不进 db.py
    try:
        from services.db_migrations.field_overrides import ensure_field_overrides_columns

        ensure_field_overrides_columns()
    except Exception as e:
        logger.warning(f"启动 field_overrides 列就绪失败 (等 alembic 002): {e}")

    # credits · 按量付费系统表结构初始化
    try:
        db.ensure_credits_tables()
    except Exception as e:
        logger.warning(f"启动 credits 建表失败: {e}")

    # 套账隔离 PO-7b · 连号计数器按主体(建 uq_dns_ws + 回填 + 守门式 drop 旧 PK)
    # 铁律 #21:新 schema 独立 services/db_migrations/ · 见 06-po7b-numbering-proposal
    try:
        from services.db_migrations.numbering_workspace_key import (
            ensure_numbering_workspace_key,
        )

        ensure_numbering_workspace_key()
    except Exception as e:
        logger.warning(f"启动 连号按主体迁移失败: {e}")

    # POS 项目 schema 双跑(A1 tenant_modules / A2 product_units / ...)· 集中在 services/pos_schema
    try:
        from services.pos_schema import bootstrap_pos_schema

        bootstrap_pos_schema()
    except Exception as e:
        logger.warning(f"启动 POS schema 失败: {e}")

    # 权限整顿批1 schema(roles 激活+种子 / memberships 加列+回填 / member_scopes /
    # invitations · docs/permissions/01)。NEW-DEBT-EXEMPT: 启动自愈式迁移同上口径。
    try:
        from services.db_migrations.authz_schema import ensure_authz_schema

        ensure_authz_schema()
    except Exception as e:
        logger.warning(f"启动 authz schema 失败: {e}")

    # 自动做账 schema(科目/映射/凭证/分录/设置/学习记忆 6 表 · docs/accounting/01)。
    # NEW-DEBT-EXEMPT: 启动自愈式迁移,prod 无 alembic 钩子,与守门豁免口径一致。
    try:
        from services.accounting.schema import ensure_accounting_schema

        ensure_accounting_schema()
    except Exception as e:
        logger.warning(f"启动 accounting schema 失败: {e}")

    # 自动报税 schema(税表/明细/设置 3 表 · docs/tax-filing/01)。
    # NEW-DEBT-EXEMPT: 启动自愈式迁移,口径同 accounting。
    try:
        from services.tax.schema import ensure_tax_schema

        ensure_tax_schema()
    except Exception as e:
        logger.warning(f"启动 tax schema 失败: {e}")

    # 商户采购(进项)schema 双跑(suppliers / purchase_docs+lines / categories+settings+
    # intake+attachments)· 与 alembic 0031-0033 同源幂等 DDL(docs/purchasing/01)。
    try:
        from services.purchase.schema import ensure_purchase_schema

        ensure_purchase_schema()
    except Exception as e:
        logger.warning(f"启动 采购 schema 失败(等 alembic 0031-0033): {e}")

    # 进项外流(Google 归档)schema + 注册 export 异步 handler(复用 recon_jobs worker)。
    try:
        from services.export.schema import ensure_export_schema

        ensure_export_schema()
        from services.export import archive as _export_archive

        _export_archive.register()
    except Exception as e:
        logger.warning(f"启动 外流 schema/handler 失败: {e}")


async def run_startup() -> dict:
    """app 启动序列 · 返回 {email_task, erp_retry_task} 供 run_shutdown cancel。"""
    logger.info("🚀 Pearnly 启动中...")

    # v118.35.0.28 P0 安全 self-check (体检 2026-05-21)
    # /internal/deploy 现在 fail-closed · secret 缺失会拒服务 ·
    # 启动时早期告警 · 不要等到 GitHub webhook 来才发现没配。
    if not os.environ.get("GITHUB_WEBHOOK_SECRET"):
        logger.critical(
            "⚠️ GITHUB_WEBHOOK_SECRET missing — /internal/deploy will return 503 · "
            "auto-deploy via GitHub webhook is DISABLED until env var is set"
        )

    # v0.15.1 · 不再自动创建 demo 账号 · 账号由 Supabase 管理
    #   (REFACTOR-I2 2026-05-28:已删 db.ensure_demo_account 死码 + 此处下线注释)
    # v0.8.1 · 启动时清理过期历史
    try:
        cleaned = db.cleanup_expired_history(free_days=7, plus_days=90, pro_days=365)
        if cleaned > 0:
            logger.info(f"🧹 已清理 {cleaned} 条过期历史")
    except Exception as e:
        logger.warning(f"启动清理过期历史失败(不影响运行): {e}")

    # 2026-06-11 · 启动 DDL 跨 worker 串行(文件锁):4-worker 并发 ensure 撞 Postgres
    # 死锁(ensure_erp_oauth_tables · cef351bf 回退),串行化后 workers=4 才安全。
    with startup_ddl_lock():
        _boot_schema_ddl()

    # v118.34.4 · MR.ERP test-connection cache flush
    # On every restart, drop any cached test-connection entries so users
    # don't see stale "stub" responses from before the v118.34.x dispatch
    # fixes. The cache is per-(user_id, endpoint_id) and TTLs at 60 s
    # anyway, so this is at most a 1-minute extra cost the first time
    # someone clicks 重新测试 right after a deploy.
    try:
        # REFACTOR-B1(2026-05-25):3 个缓存随 erp 路由搬到 erp_routes.py · 调封装函数清
        from routes.erp_routes import flush_test_connection_caches

        flush_test_connection_caches()
        logger.info("[startup] flushed ERP test-connection caches")
    except Exception as e:
        logger.warning(f"startup cache flush failed: {e}")

    # v118.33.7 · 写入健壮版 git-deploy.sh（带回滚 + 健康检查 + 日志）
    # v118.34.6 拍板:这一段移到 ensure_playwright_installed() 之前
    # · 保证就算 playwright 这步出问题,新 git-deploy.sh 也已经落到磁盘
    # · 这样下次部署的 deploy.sh 已经会自己 pip install + 装 chromium
    try:
        _deploy_sh = "/opt/mrpilot/git-deploy.sh"
        with open(_deploy_sh, "w") as _f:
            _f.write(_GIT_DEPLOY_SH)
        os.chmod(_deploy_sh, 0o755)
        logger.info("[v118.33.7] git-deploy.sh updated (with rollback + health check)")
    except Exception as e:
        logger.warning(f"git-deploy.sh update failed: {e}")

    # v118.34.6 · 现在再 ensure playwright。NON-BLOCKING (detached spawn)
    # · git-deploy.sh 已经写到磁盘 · 下次部署的 deploy.sh 也会自己装。
    # 之前 v118.34.5 的 sync 版本卡 lifespan > 30 s · 旧 deploy.sh
    # 健康检查超时把整个版本回滚了 · 现在恢复 detached spawn 路径。
    # v118.34.12 · 必须用 asyncio.to_thread · 否则内部 probe_chromium_launch
    # 跑在 lifespan 的 event loop 里 · Playwright sync_api 检测到 loop 拒绝
    # start · chromium_can_launch 假阴性(实际能起,但探测炸)。
    try:
        await asyncio.to_thread(ensure_playwright_installed)
    except Exception as e:
        logger.warning(
            f"[playwright-bootstrap] failed (will surface as "
            f"ERR_PLAYWRIGHT_MISSING in wizard): {e}"
        )

    # v110.7 · 启动确保 users 表有欢迎向导用的 profile 字段(幂等 · 已有字段无影响)
    try:
        with startup_ddl_lock():
            ensure_user_profile_columns()
    except Exception as e:
        logger.warning(f"启动 users profile 字段补齐失败: {e}")

    # v118.32.5.5.18 · 部署 graceful 第 3 层 · 长任务中断恢复
    # 启动时扫 3 张任务表中 status=running 的"被打断"任务 · 标 interrupted
    # 用户进对应页能看到 toast "上次更新时被打断 · 点重试"
    try:
        with db.get_cursor(commit=True) as cur:
            recovered = 0
            for tbl in ["ocr_history", "reconciliation_task", "gl_vat_task"]:
                try:
                    cur.execute(f"UPDATE {tbl} SET status='interrupted' " f"WHERE status='running'")
                    recovered += cur.rowcount or 0
                except Exception as _inner:
                    logger.warning(f"启动恢复 {tbl} 中断任务失败(表可能不存在): {_inner}")
            if recovered > 0:
                logger.info(f"🔄 重启恢复 · 共 {recovered} 个 running 任务标 interrupted")
    except Exception as e:
        logger.warning(f"启动 _recover_interrupted_tasks 失败(不影响运行): {e}")

    # v0.17 · M6 · 启动邮箱抓取定时任务(每 tick 扫到期账号)
    # v0.17.11 · HF Space 禁止 IMAP 993 出站 · 环境变量控制
    email_task = None
    if os.environ.get("EMAIL_INGEST_ENABLED", "0") == "1":
        email_task = asyncio.create_task(email_ingest_loop())
        logger.info("[email_ingest] 定时抓取已启用")
    else:
        logger.info(
            "[email_ingest] 定时抓取已禁用(HF Space 不支持 IMAP 出站 · 迁 VPS 后设 EMAIL_INGEST_ENABLED=1)"
        )

    # v118.25 · ERP 推送自动重试后台 worker(每 30 秒扫到期失败 log)
    # PEARNLY_SKIP_HEAVY_INIT=1 时不启动 · 防止 unit test 用 TestClient
    # 进 lifespan 时若再全局 patch asyncio.sleep,会把 30 秒 sleep 短路成
    # CPU 死循环 → list_logs_due_for_retry 每秒被调几万次 → stderr 缓冲爆
    # 内存(本机 OOM)。CI/生产不设这个 env,正常启动。
    erp_retry_task = None
    if os.environ.get("PEARNLY_SKIP_HEAVY_INIT", "").lower() not in ("1", "true", "yes"):
        erp_retry_task = asyncio.create_task(erp_retry_loop())
        logger.info("[erp_retry] 自动重试后台 worker 已启动")
    else:
        logger.info("[erp_retry] 跳过启动(PEARNLY_SKIP_HEAVY_INIT=1)")

    # ADR-005 #15 · 对账异步后台工人(embedded)· 启动建表 + 起轮询任务
    # RECON_ASYNC!=1 时 start_embedded 自己跳过(可秒回滚)· PEARNLY_SKIP_HEAVY_INIT 下不起
    if os.environ.get("PEARNLY_SKIP_HEAVY_INIT", "").lower() not in ("1", "true", "yes"):
        try:
            from services.recon_jobs import store as _recon_store, worker as _recon_worker

            with startup_ddl_lock():
                _recon_store.ensure_table()
            _recon_worker.start_embedded()
            # ADR-006 · 模板学习层映射表(启动自动建 · 失败自愈)
            try:
                from services.importer import template_store as _tmpl_store

                with startup_ddl_lock():
                    _tmpl_store.ensure_table()
            except Exception as _te:
                logger.warning(f"[importer] ensure_table 失败(不影响主服务): {_te}")
        except Exception as e:
            logger.warning(f"[recon-worker] embedded 启动失败(不影响主服务): {e}")

    logger.info("✅ Pearnly 已就绪 v0.21.0-v108 (Google 余额追踪 · 半自动校准)")
    return {"email_task": email_task, "erp_retry_task": erp_retry_task}


async def run_shutdown(tasks: dict):
    """app 关闭序列 · 停 embedded 对账 worker + cancel 后台 task。"""
    tasks = tasks or {}
    # ADR-005 #15 · 停 embedded 工人
    try:
        from services.recon_jobs import worker as _recon_worker

        await _recon_worker.stop_embedded()
    except Exception:
        pass
    # 关闭时停定时
    email_task = tasks.get("email_task")
    if email_task is not None:
        email_task.cancel()
        try:
            await email_task
        except asyncio.CancelledError:
            pass  # 任务取消 · 正常退出
    erp_retry_task = tasks.get("erp_retry_task")
    if erp_retry_task is not None:
        erp_retry_task.cancel()
        try:
            await erp_retry_task
        except asyncio.CancelledError:
            pass  # 任务取消 · 正常退出
    logger.info("👋 Pearnly 关闭")


# ⚠️ `import db` 放 def 之后(解循环 import · 见 services/billing/charge.py 注释)
from core import db  # noqa: E402
