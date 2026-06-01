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
            "zh": "本次更新优化了菜单名称与推送记录的查看体验。「上传发票」「发票记录」已更名为「上传识别」「识别记录」,以涵盖更多单据类型;推送记录现可按对接系统分类筛选查看,信息更清晰。即日生效。",
            "th": "การอัปเดตนี้ปรับชื่อเมนูและปรับปรุงการดูบันทึกการส่งข้อมูล โดยเปลี่ยน「อัปโหลดใบกำกับ」และ「บันทึกใบกำกับ」เป็น「อัปโหลดและสแกน」และ「บันทึกการสแกน」เพื่อรองรับเอกสารหลากหลายประเภทมากขึ้น และสามารถกรองบันทึกการส่งตามระบบที่เชื่อมต่อได้ ทำให้ข้อมูลชัดเจนยิ่งขึ้น มีผลทันที",
            "en": 'This update refines several menu names and improves how push records are viewed. "Upload Invoice" and "Invoice Records" are now "Upload & Scan" and "Scan Records" to cover more document types, and push records can be filtered by connected system for a clearer view. Effective immediately.',
            "ja": "今回の更新では、一部メニュー名を整理し、送信記録の表示を改善しました。「請求書アップロード」「請求書記録」を「アップロード・読取」「読取記録」に変更し、より多くの書類に対応します。送信記録は連携システムごとに絞り込めるようになりました。即日有効。",
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
    from app import ocr_recognize  # noqa: E402 · lazy 解循环 import

    return await ocr_recognize(request, file, client_id)


# /api/v1/ocr/export 跳过抽取(ExportRequest model 与 app.py 紧耦合 · FastAPI signature
# 需要在 route 注册时拿到 class · lazy import 不行)· 留 app.py 后续专门一轮处理。
