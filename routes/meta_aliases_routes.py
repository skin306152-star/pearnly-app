"""
meta_aliases_routes.py · /api/version + /api/v1/ocr/* 别名(REFACTOR-B1)

从 app.py 抽出的轻量路由:
    GET  /api/version            前端版本检测 · 4 语 release_notes
    GET  /api/v1/ocr/quota       v1 alias → v0 get_quota
    POST /api/v1/ocr/recognize   v1 alias → v0 ocr_recognize
    POST /api/v1/ocr/export      v1 alias → v0 ocr_export

v1 别名通过 lazy `from app import ...` 解循环 import(app.py 顶部 include 本 router · 本
module 顶部不能 import app)。

E2E 闸:smoke spec 间接触发 /api/version · spec 16 用 v0 路由(v1 同实现);v1 别名是
未来升级用 · 当前是路由转发。
"""

from __future__ import annotations

import time as _time
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile

router = APIRouter()


@router.get("/api/version")
async def get_frontend_version():
    """v118.27.5.4 · 前端版本检测接口 · 前端定时轮询 · 不一致弹横幅
    v118.32.5.5.17 · release_notes 4 语字段 · version-banner.js 拿来显示更新内容
    v118.35.0.28 · 公开接口只返回 version/ts/release_notes 三个公开字段"""
    # lazy import:PEARNLY_FRONTEND_VERSION 在 app.py 模块级 · app 加载完后可拿
    from app import PEARNLY_FRONTEND_VERSION

    return {
        "version": PEARNLY_FRONTEND_VERSION,
        "ts": int(_time.time()),
        "release_notes": {
            "zh": "本次为稳定性与性能优化更新,改进了部分页面的加载与运行表现,日常使用更顺畅。功能与操作方式保持不变,即日生效。",
            "th": "การอัปเดตนี้เน้นความเสถียรและประสิทธิภาพ ปรับปรุงการโหลดและการทำงานของบางหน้าให้ลื่นไหลยิ่งขึ้น โดยฟังก์ชันและวิธีใช้งานยังคงเดิม มีผลทันที",
            "en": "This update focuses on stability and performance, improving how some pages load and run for a smoother day-to-day experience. Features and workflows are unchanged. Effective immediately.",
            "ja": "今回は安定性とパフォーマンスの向上を目的とした更新で、一部ページの読み込みと動作を改善し、日々の操作をより快適にしました。機能や操作方法に変更はありません。即日有効。",
        },
    }


# ============================================================
# /api/v1/ 别名(未来升级用,当前只是路由别名)· lazy import 解 v0 调用
# ============================================================


@router.get("/api/v1/ocr/quota")
async def v1_quota(request: Request):
    from app import get_quota  # noqa: E402 · lazy 解循环 import

    return await get_quota(request)


@router.post("/api/v1/ocr/recognize")
async def v1_recognize(
    request: Request,
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),
):
    from routes.ocr_recognize_routes import (  # noqa: E402 · v1 别名转发 v0 实现(REFACTOR-WB-app)
        ocr_recognize,
    )

    return await ocr_recognize(request, file, client_id)


# /api/v1/ocr/export 跳过抽取(ExportRequest model 与 app.py 紧耦合 · FastAPI signature
# 需要在 route 注册时拿到 class · lazy import 不行)· 留 app.py 后续专门一轮处理。
