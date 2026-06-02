# -*- coding: utf-8 -*-
"""mrerp_dms_client · 错误类型 + Excel 日期序列/佛历日期工具 leaf(破 facade↔mixin 循环 import)。"""

from datetime import date


class DMSClientError(RuntimeError):
    """Generic DMS business/transport failure raised by the client.

    Carries an `error_code` (ERR_* taxonomy) so the adapter/route can map to a
    friendly message without string-matching.
    """

    def __init__(self, message: str, error_code: str = "ERR_DMS_TECHNICAL"):
        super().__init__(message)
        self.error_code = error_code


# Excel stores dates as a serial day count from 1899-12-30 (the Lotus-1-2-3
# epoch Excel inherited). DMS' import template uses these serials in C2/F2.
_EXCEL_EPOCH = date(1899, 12, 30)


def excel_serial(d: date) -> int:
    return (d - _EXCEL_EPOCH).days


def to_be_date(d: date) -> str:
    """Gregorian date -> Thai Buddhist-era dd/mm/yyyy (year + 543)."""
    return f"{d.day:02d}/{d.month:02d}/{d.year + 543}"
