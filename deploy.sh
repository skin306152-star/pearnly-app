#!/bin/bash
# ============================================================
# Pearnly · 一键部署脚本(deploy.sh)
# 路径:/opt/mrpilot/deploy.sh
# 用法:bash /opt/mrpilot/deploy.sh /tmp/pearnly_v[VER].tar.gz
# 功能:备份 + 解压 + 覆盖 + 重启 + 验证 + 失败自动回滚 + 清理
# ============================================================

PACKAGE="$1"

# === 参数检查 ===
if [ -z "$PACKAGE" ]; then
    echo ""
    echo "📖 Pearnly 一键部署脚本"
    echo "用法:bash /opt/mrpilot/deploy.sh /tmp/pearnly_v[版本号].tar.gz"
    echo "例如:bash /opt/mrpilot/deploy.sh /tmp/pearnly_v118_20_1.tar.gz"
    echo ""
    exit 0
fi

if [ ! -f "$PACKAGE" ]; then
    echo "❌ 找不到包:$PACKAGE"
    exit 1
fi

echo ""
echo "🚀 部署开始:$(basename "$PACKAGE")"
echo "═══════════════════════════════════════════"

# === 路径定义 ===
APP_DIR="/opt/mrpilot"
BACKUP_DIR="/opt/mrpilot_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
TEMP_DIR="/tmp/pearnly_deploy_${TIMESTAMP}"

mkdir -p "$BACKUP_DIR" "$TEMP_DIR"

# === 第 1 步:备份当前版本 ===
echo "📦 [1/6] 备份当前版本 → backup_${TIMESTAMP}.tar.gz"
tar --exclude='venv' --exclude='__pycache__' --exclude='*.log' --exclude='*.pyc' \
    -czf "$BACKUP_FILE" -C "$APP_DIR" . 2>/dev/null
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 备份失败 · 终止部署"
    rm -rf "$TEMP_DIR"
    exit 1
fi
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "   备份大小:${BACKUP_SIZE}"

# === 第 2 步:解压新包 ===
echo "📂 [2/6] 解压新版本"
if ! tar -xzf "$PACKAGE" -C "$TEMP_DIR"; then
    echo "❌ 解压失败 · tar 包可能损坏"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# === 第 3 步:部署文件 ===
echo "🔄 [3/6] 部署文件 → ${APP_DIR}"
# 同步 static 目录(如果包内有 static/ 子目录)
if [ -d "$TEMP_DIR/static" ]; then
    cp -rf "$TEMP_DIR/static/"* "$APP_DIR/static/" 2>/dev/null || true
fi
# 同步根目录所有顶层文件(.py / .md / .html 等)
find "$TEMP_DIR" -maxdepth 1 -type f -exec cp -f {} "$APP_DIR/" \;

# === 第 3.5 步:确保 PDF 解析库 ===
echo "📚 [3.5] 检查 PDF 解析库"
pip3 install pypdf pdfminer.six --break-system-packages -q 2>/dev/null || true

# === 第 4 步:重启服务 ===
echo "🔃 [4/6] 重启 mrpilot 服务"
systemctl restart mrpilot
sleep 3

# === 第 5 步:验证 + 失败自动回滚 ===
if systemctl is-active --quiet mrpilot; then
    echo "✅ [5/6] 服务运行正常"
    DEPLOY_OK=1
else
    echo "❌ [5/6] 服务启动失败! 自动回滚到上个版本..."
    tar -xzf "$BACKUP_FILE" -C "$APP_DIR"
    systemctl restart mrpilot
    sleep 2
    if systemctl is-active --quiet mrpilot; then
        echo "✅ 已回滚到上个版本 · 服务恢复正常"
    else
        echo "🔥 回滚后仍失败! 请 SSH 上来人工排查"
    fi
    DEPLOY_OK=0
fi

# === 第 6 步:看日志 ===
echo ""
echo "📋 [6/6] 最近 15 行日志:"
echo "───────────────────────────────────────────"
journalctl -u mrpilot -n 15 --no-pager
echo "───────────────────────────────────────────"

# === 收尾:清理 ===
rm -rf "$TEMP_DIR" "$PACKAGE"

# === 收尾:保留最近 10 个备份(清掉更旧的) ===
ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
BACKUP_COUNT=$(ls "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | wc -l)

echo ""
echo "🧹 已清理临时包 · 备份目录共 ${BACKUP_COUNT} 份(自动保留最近 10 份)"

if [ "$DEPLOY_OK" = "1" ]; then
    echo ""
    echo "═══════════════════════════════════════════"
    echo "🎉 部署成功:$(basename "$PACKAGE")"
    echo "🌐 访问:https://pearnly.com"
    echo "═══════════════════════════════════════════"
    exit 0
else
    echo ""
    echo "═══════════════════════════════════════════"
    echo "💥 部署失败 · 已自动回滚 · 检查上面日志找原因后再部署"
    echo "═══════════════════════════════════════════"
    exit 1
fi
