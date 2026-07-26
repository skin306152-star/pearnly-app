# -*- coding: utf-8 -*-
"""git-deploy.sh 模板(从 services/startup.py 抽出 · 内容逐字未改)。

app 启动时把这段脚本写到磁盘供 webhook 调用。它是运维脚本文本,不是应用装配逻辑,
放在 startup.py 里会把「启动序列」这份文件撑过 500 行硬闸。
"""

# v118.33.7 · 健壮版 git-deploy.sh(带回滚 + 健康检查 + 日志)· app 启动时写入磁盘
GIT_DEPLOY_SH = r"""#!/bin/bash
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
