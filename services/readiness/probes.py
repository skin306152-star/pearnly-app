# -*- coding: utf-8 -*-
"""
services/readiness/probes.py · REFACTOR-WA-B4 · /ready 真探活探针

背景(审计漏洞 #3 · DISPATCH_V2_FULLSCOPE §A):
  铁律 #23.7「/ready 必须能真实失败 · 任一依赖挂 → 返非 200」。
  此前只有 /api/health · 它永远返 ok · 不查 DB → "健康检查等于没有"。
  本模块给 /api/ready 提供真探针:DB 真跑 SELECT 1 · Gemini/SMTP/LINE 探凭据就绪。

设计铁律:
  - 每个探针【绝不抛异常】· 自己 try/except · 返 {"ok": bool, "detail": str}。
    (探针抛了会让 /ready 路由 500 · 那就退化成"探活本身挂了" · 违背初衷)
  - DB 探针是核心:真 SELECT 1 · DB 挂 → ok=False(这是 /health 缺的那一刀)。
  - Gemini/SMTP/LINE 探"配置就绪"(env 在场)· 不打真网络请求:
      真网络探针会给每次探活加延迟 + 烧 OCR/邮件配额 · 且第三方瞬时抖动
      不该把整台实例踢出轮转。配置缺失才是真正可判定的"未就绪"。
  - 0 业务逻辑改 · 纯新增只读探针(不碰扣费/auth/RLS)。
"""

from __future__ import annotations

import os

import db


def probe_db() -> dict:
    """真探 DB:跑 SELECT 1。DB 挂 / 连接池起不来 → ok=False(/health 缺的那一刀)。"""
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        ok = bool(row) and (row.get("ok") == 1)
        return {"ok": ok, "detail": "SELECT 1" if ok else f"unexpected result: {row!r}"}
    except Exception as e:  # 探针绝不抛
        return {"ok": False, "detail": str(e)[:200]}


def probe_gemini() -> dict:
    """探 Gemini OCR 凭据就绪:GEMINI_API_KEY / GOOGLE_API_KEY 任一 · 或 service account 文件。"""
    try:
        key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
        if key:
            return {"ok": True, "detail": "api key set"}
        creds = (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
        if creds and os.path.isfile(creds):
            return {"ok": True, "detail": "service account file"}
        return {
            "ok": False,
            "detail": "no GEMINI_API_KEY/GOOGLE_API_KEY and no service account file",
        }
    except Exception as e:  # 探针绝不抛
        return {"ok": False, "detail": str(e)[:200]}


def probe_smtp() -> dict:
    """探 Gmail SMTP 发信配置就绪:SMTP_HOST / SMTP_USER / SMTP_PASSWORD 齐全。"""
    try:
        fields = {
            "SMTP_HOST": (os.environ.get("SMTP_HOST") or "").strip(),
            "SMTP_USER": (os.environ.get("SMTP_USER") or "").strip(),
            "SMTP_PASSWORD": (os.environ.get("SMTP_PASSWORD") or "").strip(),
        }
        missing = [name for name, val in fields.items() if not val]
        if missing:
            return {"ok": False, "detail": "missing " + ",".join(missing)}
        return {"ok": True, "detail": fields["SMTP_HOST"]}
    except Exception as e:  # 探针绝不抛
        return {"ok": False, "detail": str(e)[:200]}


def probe_line() -> dict:
    """探 LINE Bot 配置就绪:LINE_CHANNEL_ACCESS_TOKEN + LINE_CHANNEL_SECRET 齐全。"""
    try:
        fields = {
            "LINE_CHANNEL_ACCESS_TOKEN": (
                os.environ.get("LINE_CHANNEL_ACCESS_TOKEN") or ""
            ).strip(),
            "LINE_CHANNEL_SECRET": (os.environ.get("LINE_CHANNEL_SECRET") or "").strip(),
        }
        missing = [name for name, val in fields.items() if not val]
        if missing:
            return {"ok": False, "detail": "missing " + ",".join(missing)}
        return {"ok": True, "detail": "configured"}
    except Exception as e:  # 探针绝不抛
        return {"ok": False, "detail": str(e)[:200]}


# 探针注册表 · 顺序固定(给输出稳定 key 集)
PROBES = {
    "db": probe_db,
    "gemini": probe_gemini,
    "smtp": probe_smtp,
    "line": probe_line,
}


def run_readiness() -> dict:
    """跑全部探针 · 任一 ok=False → ready=False(铁律 #23.7「任一依赖挂返非 200」)。

    返回 {"ready": bool, "checks": {name: {"ok", "detail"}, ...}}。
    本函数自身也绝不抛(探针 fn 万一被替换成会抛的 · 这里再兜一层)。
    """
    checks: dict = {}
    all_ok = True
    for name, fn in PROBES.items():
        try:
            res = fn()
            if not isinstance(res, dict):
                res = {"ok": False, "detail": f"probe returned {type(res).__name__}"}
        except Exception as e:  # 双保险:探针约定绝不抛 · 这里再兜一层
            res = {"ok": False, "detail": f"probe error: {str(e)[:200]}"}
        checks[name] = res
        if not res.get("ok"):
            all_ok = False
    return {"ready": all_ok, "checks": checks}
