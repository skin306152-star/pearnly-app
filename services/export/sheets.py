# -*- coding: utf-8 -*-
"""Google Sheets 同步(主体×年一张表 · 双 tab 全年/当月 · 一行一明细 · 契约 05 §2.2)。

分两层:SheetsClient 真 API 适配器(googleapiclient · 用户验收范围)与 rows_to_matrix
编排(纯逻辑可单测)。列序复用 rows.COLUMNS(与 Excel 同真源)。证据列写 HYPERLINK 公式
回 Drive 原图夹。**比 Paypers 多** 借方/贷方/凭证号/入账状态列(rows 已带)。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from services.export import rows as rows_mod
from services.export.rows import COLUMN_KEYS

ALL_YEAR_TAB = "全年"
_ALL_YEAR_TAB = {"zh": "全年", "en": "Full year", "th": "ทั้งปี", "ja": "通年"}


def all_year_tab(lang: str = "zh") -> str:
    """年汇总 tab 名(按 lang)。"""
    return _ALL_YEAR_TAB.get(lang, _ALL_YEAR_TAB["zh"])


def _cell(key, value, lang: str = "zh"):
    """单元格值:evidence URL → HYPERLINK 公式;Decimal → float;None → ""。"""
    if key == "evidence" and isinstance(value, str) and value.startswith(("http", "/api/")):
        safe = value.replace('"', "%22")
        return f'=HYPERLINK("{safe}","{rows_mod.view_label(lang)}")'
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return "" if value is None else value


def rows_to_matrix(rows: list, *, lang: str = "zh") -> list:
    """导出行 → 二维值矩阵([表头] + 每行按列序)· 表头/证据文案随 lang。喂 values API。"""
    matrix = [rows_mod.headers(lang)]
    for row in rows or []:
        matrix.append([_cell(k, row.get(k), lang) for k in COLUMN_KEYS])
    return matrix


def month_tab(month: int) -> str:
    """当月 tab 名(从 archive_tree 月名派生,保持一致)。"""
    from services.export import archive_tree

    return archive_tree.month_folder(month)


class SheetsClient:
    """googleapiclient Sheets+Drive 适配器(真 API · 用户验收)。"""

    def __init__(self, access_token: str):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials(token=access_token)
        self._sheets = build("sheets", "v4", credentials=creds, cache_discovery=False)
        self._drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    def find_or_create_spreadsheet(self, folder_id: str, title: str) -> str:
        q = (
            f"name='{title}' and '{folder_id}' in parents and "
            "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        )
        res = self._drive.files().list(q=q, fields="files(id)", pageSize=1).execute()
        files = res.get("files") or []
        if files:
            return files[0]["id"]
        body = {
            "name": title,
            "mimeType": "application/vnd.google-apps.spreadsheet",
            "parents": [folder_id],
        }
        return self._drive.files().create(body=body, fields="id").execute()["id"]

    def ensure_tab(self, spreadsheet_id: str, tab: str) -> None:
        meta = self._sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        titles = {s["properties"]["title"] for s in meta.get("sheets", [])}
        if tab in titles:
            return
        self._sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
        ).execute()

    def overwrite_tab(self, spreadsheet_id: str, tab: str, matrix: list) -> None:
        self._sheets.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range=tab
        ).execute()
        self._sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{tab}!A1",
            valueInputOption="USER_ENTERED",
            body={"values": matrix},
        ).execute()


def sync(
    client, *, folder_id: str, subject: str, year: int, month: int, rows: list, lang: str = "zh"
) -> str:
    """主体×年表:写全年 tab + 当月 tab(各 overwrite 成最新明细)。返回 spreadsheet_id。

    编排注入 client → 可单测;真 API 在 SheetsClient。月行 = rows 里该月的子集由调用方传入
    (archive 按月分组),全年 = 整年 rows。列头/枚举值/全年 tab 名随 lang。
    """
    from services.export import archive_tree

    title = archive_tree.sheet_name(subject, year)
    ssid = client.find_or_create_spreadsheet(folder_id, title)
    matrix = rows_to_matrix(rows, lang=lang)
    for tab in (all_year_tab(lang), month_tab(month)):
        client.ensure_tab(ssid, tab)
        client.overwrite_tab(ssid, tab, matrix)
    return ssid
