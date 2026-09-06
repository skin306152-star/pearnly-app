"""Cowork inventory counts: import immutable snapshots, count, compare, export."""

import hashlib
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from services.stocktake import access as stocktake_access
from services.stocktake import excel, store, entries, reports

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


class Entry(BaseModel):
    request_id: UUID
    quantity: str = Field(max_length=40)
    warehouse: str = Field(min_length=1, max_length=300)
    location: str = Field(default="", max_length=300)


class EntryEdit(Entry):
    version: int = Field(ge=0)
    voided: bool = False


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


@router.delete("/{task_id}")
def delete_task(task_id: UUID, request: Request):
    return store.delete_task(stocktake_access.scope_for(request, "recon.create"), task_id)


@router.put("/{task_id}/items/{item_id}")
def count(task_id: UUID, item_id: UUID, body: Count, request: Request):
    scope = stocktake_access.scope_for(request, "recon.create")
    return store.count(
        scope, task_id, item_id, excel.quantity(body.quantity, nonnegative=True), body.version
    )


@router.post("/{task_id}/close")
def close(task_id: UUID, request: Request):
    return store.close(stocktake_access.scope_for(request, "recon.create"), task_id)


@router.post("/{task_id}/items/{item_id}/entries")
def add_entry(task_id: UUID, item_id: UUID, body: Entry, request: Request):
    scope = stocktake_access.scope_for(request, "recon.create")
    return entries.write(
        scope, task_id, item_id, body.request_id, body.quantity, body.warehouse, body.location
    )


@router.get("/{task_id}/entries")
def list_entries(
    task_id: UUID,
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return output(
        entries.listing(stocktake_access.scope_for(request, "recon.view"), task_id, limit, offset)
    )


@router.patch("/{task_id}/entries/{entry_id}")
def edit_entry(task_id: UUID, entry_id: UUID, body: EntryEdit, request: Request):
    scope = stocktake_access.scope_for(request, "recon.create")
    return entries.write(
        scope,
        task_id,
        entry_id,
        body.request_id,
        body.quantity,
        body.warehouse,
        body.location,
        version=body.version,
        voided=body.voided,
    )


@router.get("/{task_id}/export")
def export(task_id: UUID, request: Request):
    task = store.detail(stocktake_access.scope_for(request, "recon.export"), task_id, export=True)
    data = (
        reports.workbook(task)
        if task.get("count_mode") == "scan"
        else excel.workbook(task["items"])
    )
    return download(data, f"stocktake-{task_id}")
