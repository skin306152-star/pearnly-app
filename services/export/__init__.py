# -*- coding: utf-8 -*-
"""进项外流(导出/归档)· Excel 内存流(零授权)+ Drive/Sheets(Google OAuth)。

docs/smart-intake/05 阶段二。当前已建可验证部分:
  entries.py  按 source_id 反查做账分录(借/贷/凭证号/入账状态)· 复用 accounting.vouchers
  rows.py     进项明细 → 一行一明细导出行(纯转换)
  excel.py    导出行 → xlsx 内存流(openpyxl · 零授权兜底)
Google OAuth + drive.py/sheets.py 见后续(需产品 OAuth client + 真授权验收)。
"""
