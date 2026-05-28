# -*- coding: utf-8 -*-
"""
Pearnly · 启动期前端静态资源工具(REFACTOR-WA-B1 · 2026-05-29 从 app.py 抽出)

纯搬家 · 0 逻辑改 · app.py 模块加载时调:
  · read_frontend_version()  — 从 static/home.html 抓 home.js?v=NNN 版本号(设 PEARNLY_FRONTEND_VERSION)
  · purge_stale_static_gz()  — 删 static/**/*.gz 陈旧预压缩文件 · 让 nginx 退回动态 gzip
"""

import logging

logger = logging.getLogger("mr-pilot")


def read_frontend_version() -> str:
    import re

    try:
        with open("static/home.html", "r", encoding="utf-8") as _f:
            _content = _f.read()
        m = re.search(r"home\.js\?v=(\d+)", _content)
        if m:
            return m.group(1)
        m = re.search(r"home\.css\?v=(\d+)", _content)
        if m:
            return m.group(1)
    except Exception as e:
        logger.warning(f"read_frontend_version 读取失败: {e}")
    return "0"


# ============================================================
# v118.34.37 · 启动时清掉 static/**/*.gz 强制 nginx 动态 gzip
# ============================================================
# 根因(2026-05-20 调试发现): nginx gzip_static on 服务 pre-gzipped .gz
# 文件 · 但 deploy.sh 只 cp 源 .css/.js 不更新 .gz · 导致:
#   - curl 不带 Accept-Encoding: gzip → 拿到新源文件
#   - 浏览器带 Accept-Encoding: gzip → 拿到陈旧 .gz (mtime 跟最近源文件相差几小时)
#   - 即使 URL 加 ?v=NNN cache-bust 也没用 · nginx 静态文件忽略 query string
# 修: 每次 app 启动时删掉 static 下所有 .gz · 让 nginx 退回到 gzip on the fly
# 性能影响: 微小 (CSS/JS 文件本来就有 nginx 自身的 in-memory cache)
def purge_stale_static_gz():
    import os as _os
    import glob as _glob

    try:
        deleted = 0
        for fp in _glob.glob("static/**/*.gz", recursive=True):
            try:
                _os.remove(fp)
                deleted += 1
            except Exception:
                pass
        if deleted:
            logger.info(
                f"🧹 启动清除 static/**/*.gz · 删了 {deleted} 个陈旧预压缩文件 · nginx 将动态 gzip 当前源文件"
            )
    except Exception as _e:
        logger.warning(f"purge_stale_static_gz 失败: {_e}")
