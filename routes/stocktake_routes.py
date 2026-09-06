"""Cowork inventory counts: import immutable snapshots, count, compare, export."""

import hashlib
from decimal import Decimal
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from services.stocktake import access as stocktake_access
from services.stocktake import excel, store

router = APIRouter(prefix="/api/cowork/stocktakes", tags=["stocktake"])


def output(value):
    return JSONResponse(jsonable_encoder(value, custom_encoder={Decimal: str}))


def download(data, name):
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{name}.xlsx"'},
    )


class LineLogin(BaseModel):
    id_token: str = Field(max_length=10000)


class Count(BaseModel):
    quantity: str = Field(max_length=40)
    version: int = Field(ge=0)


@router.post("/line/auth")
def line_auth(body: LineLogin):
    return stocktake_access.line_login(body.id_token)


@router.get("/workspaces")
def workspaces(request: Request):
    return stocktake_access.workspaces(request)


@router.get("/template")
def template(request: Request):
    stocktake_access.authorize(request, "recon.create")
    return download(excel.workbook(), "stocktake-template")


@router.get("")
def listing(request: Request):
    return output(store.listing(stocktake_access.scope_for(request, "recon.view")))


@router.post("")
def create(
    request: Request,
    name: str = Form(...),
    request_id: UUID = Form(...),
    file: UploadFile = File(...),
):
    scope = stocktake_access.scope_for(request, "recon.create")
    if not name.strip() or len(name.strip()) > 120:
        raise HTTPException(422, detail="stocktake.name_invalid")
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(422, detail="stocktake.file_invalid")
    data = file.file.read(excel.MAX_BYTES + 1)
    items = excel.parse(data)
    return store.create(scope, name.strip(), items, request_id, hashlib.sha256(data).hexdigest())


@router.get("/{task_id}")
def detail(task_id: UUID, request: Request):
    return output(store.detail(stocktake_access.scope_for(request, "recon.view"), task_id))


@router.put("/{task_id}/items/{item_id}")
def count(task_id: UUID, item_id: UUID, body: Count, request: Request):
    scope = stocktake_access.scope_for(request, "recon.create")
    return store.count(
        scope, task_id, item_id, excel.quantity(body.quantity, nonnegative=True), body.version
    )


@router.post("/{task_id}/close")
def close(task_id: UUID, request: Request):
    return store.close(stocktake_access.scope_for(request, "recon.create"), task_id)


@router.get("/{task_id}/export")
def export(task_id: UUID, request: Request, lang: Literal["en", "th", "zh", "ja"] = "en"):
    task = store.detail(stocktake_access.scope_for(request, "recon.export"), task_id)
    return download(excel.workbook(task["items"], lang=lang), f"stocktake-{task_id}")
