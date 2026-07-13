# -*- coding: utf-8 -*-
"""工资进料 DAL(列映射模板 + 月度进料行 · 套账隔离 · 方案 §2.3/P4)。

隔离=每句 WHERE tenant_id;模板 PK (tenant_id, workspace_client_id) 天然幂等 upsert。金额
全程 Decimal 存 numeric(15,2)。月度进料行按 (tenant, client, period) 整体替换(重传即覆盖,
单一事实源,不留半张旧表);只落已通过校验的行(调用方保证),供 ภ.ง.ด.1ก 年度聚合复用。
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Optional

from services.payroll import model


def get_template(cur, *, tenant_id: str, workspace_client_id: int) -> Optional[dict]:
    """读该客户列映射模板(不存在返 None)。column_map/fixed_values 反序列化为 dict。"""
    cur.execute(
        "SELECT column_map, income_code, fixed_values, header_hash "
        "FROM client_payroll_templates WHERE tenant_id = %s AND workspace_client_id = %s",
        (tenant_id, workspace_client_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    row = dict(row)
    return {
        "column_map": _as_dict(row["column_map"]),
        "income_code": row["income_code"],
        "fixed_values": _as_dict(row["fixed_values"]),
        "header_hash": row["header_hash"],
    }


def upsert_template(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    column_map: dict,
    income_code: str = model.DEFAULT_INCOME_CODE,
    fixed_values: Optional[dict] = None,
    header_hash: str = "",
) -> None:
    """存/更新客户列映射模板(PK 幂等)。下月上传同客户表先套此模板自动映射。"""
    cur.execute(
        """
        INSERT INTO client_payroll_templates
            (tenant_id, workspace_client_id, column_map, income_code, fixed_values, header_hash)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id, workspace_client_id) DO UPDATE SET
            column_map = EXCLUDED.column_map,
            income_code = EXCLUDED.income_code,
            fixed_values = EXCLUDED.fixed_values,
            header_hash = EXCLUDED.header_hash,
            updated_at = now()
        """,
        (
            tenant_id,
            workspace_client_id,
            json.dumps(column_map or {}),
            income_code,
            json.dumps(fixed_values or {}),
            header_hash,
        ),
    )


def save_period_rows(
    cur, *, tenant_id: str, workspace_client_id: int, period: str, rows: list
) -> int:
    """整体替换该客户该期进料行(重传即覆盖 · 单一事实源)。返回落库行数。

    只应传已通过校验的 PayrollRow;金额存 Decimal。period 为佛历「YYYY-MM」。
    """
    cur.execute(
        "DELETE FROM client_payroll_rows "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND period = %s",
        (tenant_id, workspace_client_id, period),
    )
    for row in rows:
        cur.execute(
            """
            INSERT INTO client_payroll_rows
                (tenant_id, workspace_client_id, period, seq, employee_id, title,
                 first_name, last_name, income_code, paid_date, paid_amount, wht_amount, condition)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                tenant_id,
                workspace_client_id,
                period,
                row.seq,
                row.employee_id,
                row.title,
                row.first_name,
                row.last_name,
                row.income_code,
                row.paid_date,
                _dec(row.paid_amount),
                _dec(row.wht_amount),
                row.condition,
            ),
        )
    return len(rows)


def load_period_rows(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> list:
    """读某期已落库进料行(供 ภ.ง.ด.1ก 年度聚合)。返回 dict 列表(金额 Decimal)。"""
    cur.execute(
        "SELECT period, seq, employee_id, title, first_name, last_name, income_code, "
        "paid_date, paid_amount, wht_amount, condition "
        "FROM client_payroll_rows "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND period = %s "
        "ORDER BY seq",
        (tenant_id, workspace_client_id, period),
    )
    return [dict(r) for r in cur.fetchall()]


def load_year_rows(cur, *, tenant_id: str, workspace_client_id: int, tax_year: str) -> list:
    """读该客户全年度(佛历 4 位年 · 调用方须先校验格式)已落库月度进料行,供 ภ.ง.ด.1ก
    年度聚合(services/payroll/pnd1a.aggregate_year)。period 形如 "2569-05",按
    (period, seq) 排序——聚合按时间序取「最新月姓名」依赖这个排序。
    """
    cur.execute(
        "SELECT period, seq, employee_id, title, first_name, last_name, income_code, "
        "paid_date, paid_amount, wht_amount, condition "
        "FROM client_payroll_rows "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND period LIKE %s "
        "ORDER BY period, seq",
        (tenant_id, workspace_client_id, f"{tax_year}-%"),
    )
    return [dict(r) for r in cur.fetchall()]


def _as_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if value in (None, ""):
        return {}
    return json.loads(value)


def _dec(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))
