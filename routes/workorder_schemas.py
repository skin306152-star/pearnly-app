# -*- coding: utf-8 -*-
"""工单 HTTP API 的请求体契约(routes/workorder_routes 的入参模型)。

只放 Pydantic 模型:字段名/长度上限即对外契约,与路由的鉴权/编排分开,改契约不用翻整个路由文件。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    workspace_client_id: int = Field(..., description="账套主体 id")
    period: str = Field(..., min_length=1, max_length=20, description="申报期,如 2569-05")
    intent: str = Field("monthly_vat", max_length=40, description="工单意图(默认月度 VAT)")


class DecisionIn(BaseModel):
    item_id: str = Field(..., description="被裁决的 work_order_item id")
    decision: str = Field(..., description="face_value | recalc | exclude | assign_kind | waive")
    values: Optional[dict] = Field(None, description="recalc 时的人工补正数(如 {vat: '35.00'})")
    kind: Optional[str] = Field(None, description="assign_kind kind(含 bank_statement)")
    reason: Optional[str] = Field(
        None, max_length=500, description="waive 豁免理由(必填):谁豁免·为何放行出包"
    )


class SalesSummaryIn(BaseModel):
    sales_amount: str = Field(..., max_length=40, description="销项销售额(十进制字符串)")
    output_vat: str = Field(..., max_length=40, description="销项税额(十进制字符串)")
    note: str = Field("", max_length=500, description="凭据备注(人工申报来源)")
    # 来源标识:一个月的销项常来自多张表(自开票 / 7-11 / Big C),各占一条件相加。
    # 空 = 不分来源的单槽,重填覆盖(向后兼容现状)。
    source_label: str = Field("", max_length=60, description="来源标识,如 7-11;空=单槽覆盖")


class ReviewSignoffIn(BaseModel):
    note: str = Field("", max_length=500, description="复核备注(可选)")
