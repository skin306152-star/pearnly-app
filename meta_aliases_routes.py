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
            "zh": "「客户」已升级为「客户管理」。现在可在同一页面分别管理「账套主体」(您自己的公司 / 开票方)与「买方客户」(发票上的买家);买方客户改为列表展示,支持搜索、多选与批量删除。登录后系统会引导您选择当前账套主体。即日生效。",
            "th": "«ลูกค้า» ได้รับการปรับเป็น «จัดการลูกค้า» · ตอนนี้จัดการ «กิจการ» (บริษัทของคุณเอง / ผู้ออกใบกำกับ) และ «ลูกค้าผู้ซื้อ» (ผู้ซื้อในใบกำกับ) ได้ในหน้าเดียว · ลูกค้าผู้ซื้อแสดงเป็นรายการที่ค้นหา เลือกหลายรายการ และลบเป็นชุดได้ · หลังเข้าสู่ระบบจะแนะนำให้เลือกกิจการปัจจุบัน · มีผลทันที",
            "en": '"Clients" has been upgraded to "Customers". You can now manage "Accounting entities" (your own company / the invoice issuer) and "Buyer customers" (the buyer on an invoice) on one page; buyer customers are shown as a searchable list with multi-select and bulk delete. After signing in, you will be guided to choose your current accounting entity. Effective immediately.',
            "ja": "「クライアント」を「顧客管理」に改善しました。同じ画面で「対象会社」(あなたの会社 / 請求書の発行者)と「買い手顧客」(請求書の買い手)を分けて管理できます。買い手顧客は一覧表示になり、検索・複数選択・一括削除に対応しました。ログイン後に現在の対象会社を選ぶ案内が表示されます。即日有効。",
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
