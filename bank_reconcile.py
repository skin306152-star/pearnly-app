"""
Mr.Pilot · v0.18 · M10 银行对账
PDF 解析模块 · 支持 KBank / SCB / BBL 三大泰国银行 · 其他走通用提取

依赖:Gemini 识别(复用 gemini_engine.py 的 vision 能力)
      + pdfminer.six(文本层优先 · 免得跑 OCR)
"""
import logging
import re
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger("mr-pilot.bank_recon")


@dataclass
class BankTransaction:
    """一条银行流水(解析后的标准结构)"""
    row_no: int
    tx_date: Optional[str]          # YYYY-MM-DD 字符串
    value_date: Optional[str]
    direction: str                  # "IN" / "OUT"
    amount: float
    balance_after: Optional[float]
    description: str
    counterparty: Optional[str] = None
    ref_no: Optional[str] = None
    channel: Optional[str] = None


@dataclass
class ParsedStatement:
    """对账单完整解析结果"""
    bank_code: str                  # KBANK / SCB / BBL / OTHER
    account_last4: Optional[str]
    statement_month: Optional[str]  # YYYY-MM-01
    period_start: Optional[str]
    period_end: Optional[str]
    opening_balance: Optional[float]
    closing_balance: Optional[float]
    total_inflow: float
    total_outflow: float
    transactions: List[BankTransaction]
    pages: int
    parse_method: str               # "text_layer" / "gemini_vision"

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["transactions"] = [asdict(t) for t in self.transactions]
        return d


# ============================================================
# 银行识别:从 PDF 首页文字推断是哪家银行
# ============================================================
def detect_bank(full_text: str) -> str:
    """从文本判断银行 · 返回 bank_code"""
    lower = full_text.lower()
    # KBank (กสิกรไทย) · 关键词:KASIKORNBANK / K PLUS / กสิกรไทย
    if any(k in lower for k in ["kasikorn", "kbank", "k plus"]) or "กสิกรไทย" in full_text:
        return "KBANK"
    # SCB (ไทยพาณิชย์) · Siam Commercial Bank
    if "siam commercial" in lower or "scb" in lower or "ไทยพาณิชย์" in full_text:
        return "SCB"
    # BBL (กรุงเทพ) · Bangkok Bank
    if "bangkok bank" in lower or "bbl" in lower or "ธนาคารกรุงเทพ" in full_text:
        return "BBL"
    # KTB (กรุงไทย)
    if "krungthai" in lower or "ktb" in lower or "กรุงไทย" in full_text:
        return "KTB"
    # TMB / TTB
    if "ttb" in lower or "tmb" in lower or "ธนชาต" in full_text:
        return "TTB"
    return "OTHER"


# ============================================================
# 主入口:解析 PDF · 返回 ParsedStatement
# ============================================================
def parse_statement_pdf(pdf_bytes: bytes, filename: str = "") -> ParsedStatement:
    """
    解析银行对账单 PDF
    策略:
      1. 先尝试文本层提取(pdfminer)· 扫描的 PDF 则降级
      2. 根据关键词识别银行
      3. 按银行走专用模板解析 · 未识别银行走通用 Gemini vision
    """
    full_text = _extract_text_layer(pdf_bytes)
    pages = _count_pages(pdf_bytes)

    if full_text and len(full_text) > 200:
        bank_code = detect_bank(full_text)
        logger.info(f"[bank_recon] 文本层提取成功 · {len(full_text)} 字符 · 识别为 {bank_code}")
        try:
            if bank_code == "KBANK":
                return _parse_kbank_text(full_text, pages)
            if bank_code == "SCB":
                return _parse_scb_text(full_text, pages)
            if bank_code == "BBL":
                return _parse_bbl_text(full_text, pages)
            # 其他银行走通用正则
            return _parse_generic_text(full_text, pages, bank_code)
        except Exception as e:
            logger.warning(f"[bank_recon] 文本模板解析失败 · 降级 Gemini: {e}")

    # 文本层太少(扫描件)· 交给 Gemini vision
    logger.info("[bank_recon] 文本层不足 · 走 Gemini vision 解析")
    return _parse_via_gemini(pdf_bytes, pages)


# ============================================================
# 辅助:pdf 文本 + 页数提取
# ============================================================
def _extract_text_layer(pdf_bytes: bytes) -> str:
    """用 pdfminer 提文本层 · 无文本返回空串"""
    try:
        from io import BytesIO
        from pdfminer.high_level import extract_text
        return extract_text(BytesIO(pdf_bytes)) or ""
    except Exception as e:
        logger.warning(f"[bank_recon] pdfminer 提取失败: {e}")
        return ""


def _count_pages(pdf_bytes: bytes) -> int:
    try:
        from io import BytesIO
        from pypdf import PdfReader
        return len(PdfReader(BytesIO(pdf_bytes)).pages)
    except Exception:
        return 0


# ============================================================
# KBank 模板 · 列顺序:Date | Description | Cheque No | Deposit | Withdrawal | Balance
# ============================================================
# 示例行:01/12/24  TRANSFER FROM XXXX1234  5,000.00  123,456.78
# KBank 对账单一般是 DD/MM/YY 或 DD/MM/YYYY
_KBANK_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"       # date
    r"(.+?)\s+"                            # description
    r"(?:([\d,]+\.\d{2})\s+)?"             # deposit (optional)
    r"(?:([\d,]+\.\d{2})\s+)?"             # withdrawal (optional)
    r"([\d,]+\.\d{2})"                     # balance
)


def _parse_kbank_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening  # 用余额差推方向

    for i, line in enumerate(text.split("\n")):
        line = line.strip()
        if not line:
            continue
        m = _KBANK_ROW.search(line)
        if not m:
            continue
        d_str, desc, dep, wdr, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        deposit = _parse_amount(dep)
        withdraw = _parse_amount(wdr)
        balance = _parse_amount(bal)

        # 先按"存款/取款"列判断(两列都有时用金额非零的那个)
        amount_pool = [v for v in (deposit, withdraw) if v and v > 0]
        if not amount_pool:
            continue

        # 当有 2 个非零金额 · 或只有 1 个金额 · 用"余额差"兜底推方向
        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                # 余额没变 · 看金额列
                direction = "IN" if deposit and deposit > 0 else "OUT"
                amount = amount_pool[0]
        else:
            # 首行没有 prev_balance · 用关键词 + 金额列
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif deposit and deposit > 0 and not (withdraw and withdraw > 0):
                direction = "IN"
                amount = deposit
            elif withdraw and withdraw > 0 and not (deposit and deposit > 0):
                direction = "OUT"
                amount = withdraw
            else:
                # 都有金额,默认按第一个
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(BankTransaction(
            row_no=len(txs) + 1,
            tx_date=tx_date,
            value_date=tx_date,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=desc.strip(),
            channel=_guess_channel(desc),
        ))
        prev_balance = balance

    return ParsedStatement(
        bank_code="KBANK",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


def _looks_like_outflow(desc: str) -> bool:
    """从描述判断是否为出账流水"""
    if not desc:
        return False
    u = desc.upper()
    out_kw = ["WITHDRAW", "WDRL", "FEE", "CHARGE", "PAY", "PAYMENT",
              "OUT", "DEBIT", "PURCHASE", "BUY",
              "ถอน", "ค่าธรรมเนียม", "ชำระ"]
    return any(k in u or k in desc for k in out_kw)


# ============================================================
# SCB 模板 · 列顺序:Date | Time | Code | Channel | Description | Debit | Credit | Balance
# ============================================================
_SCB_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"                 # date
    r"(?:\d{1,2}:\d{2}\s+)?"                         # time (optional)
    r"(?:([A-Z]{2,}\d*)\s+)?"                        # code (optional, like X0)
    r"(.+?)\s+"                                      # description
    r"(?:([\d,]+\.\d{2})\s+)?"                       # debit
    r"(?:([\d,]+\.\d{2})\s+)?"                       # credit
    r"([\d,]+\.\d{2})"                               # balance
)


def _parse_scb_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _SCB_ROW.search(line)
        if not m:
            continue
        d_str, code, desc, debit, credit, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        dr = _parse_amount(debit)
        cr = _parse_amount(credit)
        balance = _parse_amount(bal)

        amount_pool = [v for v in (cr, dr) if v and v > 0]
        if not amount_pool:
            continue

        # 余额差兜底(当 PDF 文本空白被压缩导致列错位时尤为重要)
        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                direction = "IN" if cr and cr > 0 else "OUT"
                amount = amount_pool[0]
        else:
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif cr and cr > 0 and not (dr and dr > 0):
                direction = "IN"
                amount = cr
            elif dr and dr > 0 and not (cr and cr > 0):
                direction = "OUT"
                amount = dr
            else:
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(BankTransaction(
            row_no=len(txs) + 1,
            tx_date=tx_date,
            value_date=tx_date,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=desc.strip(),
            channel=code or _guess_channel(desc),
        ))
        prev_balance = balance

    return ParsedStatement(
        bank_code="SCB",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# BBL 模板 · 列顺序和 KBank 接近
# ============================================================
_BBL_ROW = re.compile(
    r"(\d{1,2}/\d{1,2}/\d{2,4})\s+"
    r"([A-Z]{2,5})?\s*"                              # channel code(可选)
    r"(.+?)\s+"
    r"(?:([\d,]+\.\d{2})\s+)?"                       # withdrawal
    r"(?:([\d,]+\.\d{2})\s+)?"                       # deposit
    r"([\d,]+\.\d{2})"                               # balance
)


def _parse_bbl_text(text: str, pages: int) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0
    prev_balance = opening

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _BBL_ROW.search(line)
        if not m:
            continue
        d_str, channel, desc, wdr, dep, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        withdraw = _parse_amount(wdr)
        deposit = _parse_amount(dep)
        balance = _parse_amount(bal)

        amount_pool = [v for v in (deposit, withdraw) if v and v > 0]
        if not amount_pool:
            continue

        if prev_balance is not None and balance is not None:
            delta = round(balance - prev_balance, 2)
            if abs(delta) > 0.001:
                direction = "IN" if delta > 0 else "OUT"
                amount = abs(delta)
            else:
                direction = "IN" if deposit and deposit > 0 else "OUT"
                amount = amount_pool[0]
        else:
            if _looks_like_outflow(desc):
                direction = "OUT"
                amount = amount_pool[0]
            elif deposit and deposit > 0 and not (withdraw and withdraw > 0):
                direction = "IN"
                amount = deposit
            elif withdraw and withdraw > 0 and not (deposit and deposit > 0):
                direction = "OUT"
                amount = withdraw
            else:
                direction = "IN"
                amount = amount_pool[0]

        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(BankTransaction(
            row_no=len(txs) + 1,
            tx_date=tx_date,
            value_date=tx_date,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=desc.strip(),
            channel=channel or _guess_channel(desc),
        ))
        prev_balance = balance

    return ParsedStatement(
        bank_code="BBL",
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# 其他银行 · 通用正则(找 日期 + 金额 + 余额 的行)
# ============================================================
_GENERIC_ROW = re.compile(
    r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s+"
    r"(.+?)\s+"
    r"(-?[\d,]+\.\d{2})\s+"                          # 金额(可带负号)
    r"([\d,]+\.\d{2})"                                # 余额
)


def _parse_generic_text(text: str, pages: int, bank_code: str) -> ParsedStatement:
    account_last4 = _find_account_last4(text)
    period_start, period_end = _find_period(text)
    opening, closing = _find_opening_closing(text)

    txs: List[BankTransaction] = []
    total_in, total_out = 0.0, 0.0

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = _GENERIC_ROW.search(line)
        if not m:
            continue
        d_str, desc, amt_str, bal = m.groups()
        tx_date = _normalize_thai_date(d_str, period_end or period_start)
        amt = _parse_amount(amt_str)
        balance = _parse_amount(bal)
        if not amt:
            continue

        direction = "OUT" if amt < 0 else "IN"
        amount = abs(amt)
        if direction == "IN":
            total_in += amount
        else:
            total_out += amount

        txs.append(BankTransaction(
            row_no=len(txs) + 1,
            tx_date=tx_date,
            value_date=tx_date,
            direction=direction,
            amount=amount,
            balance_after=balance,
            description=desc.strip(),
            channel=_guess_channel(desc),
        ))

    return ParsedStatement(
        bank_code=bank_code,
        account_last4=account_last4,
        statement_month=_month_of(period_start or period_end),
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening,
        closing_balance=closing,
        total_inflow=round(total_in, 2),
        total_outflow=round(total_out, 2),
        transactions=txs,
        pages=pages,
        parse_method="text_layer",
    )


# ============================================================
# 扫描件 · Gemini vision 兜底(M10 轮 2 会真接通 · 本轮留 placeholder)
# ============================================================
def _parse_via_gemini(pdf_bytes: bytes, pages: int) -> ParsedStatement:
    """
    TODO M10 轮 2:接入 gemini_engine.recognize_pdf 的 vision 模式
    用一个专用 prompt 让 Gemini 输出 JSON:
    {
      "bank_code": "...",
      "account_last4": "...",
      "period_start": "YYYY-MM-DD",
      "transactions": [{"tx_date":"...","direction":"IN","amount":1000,"description":"..."}]
    }
    本轮:返回空结果 + 错误提示 · 让前端显示"扫描件暂不支持 · 请上传带文字层的 PDF"
    """
    return ParsedStatement(
        bank_code="OTHER",
        account_last4=None,
        statement_month=None,
        period_start=None,
        period_end=None,
        opening_balance=None,
        closing_balance=None,
        total_inflow=0.0,
        total_outflow=0.0,
        transactions=[],
        pages=pages,
        parse_method="gemini_vision_pending",
    )


# ============================================================
# 工具函数
# ============================================================
def _parse_amount(s: Optional[str]) -> Optional[float]:
    """'1,234.56' → 1234.56 · None / 空 → None"""
    if not s:
        return None
    try:
        return float(s.replace(",", "").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


def _normalize_thai_date(s: str, reference: Optional[str] = None) -> Optional[str]:
    """
    DD/MM/YY 或 DD/MM/YYYY → YYYY-MM-DD
    泰国银行对账单年份经常用佛历(+543)· 自动转公历
    若年份只有 2 位 · 用 reference 年推断
    """
    if not s:
        return None
    # 支持 / 和 -
    parts = re.split(r"[/\-]", s.strip())
    if len(parts) != 3:
        return None
    try:
        dd, mm, yy = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    # 年份归一化
    if yy < 100:
        # 2 位 · 推测:> 50 归 19xx,其余归 20xx · 泰国一般都是近期
        yy = 2000 + yy if yy < 70 else 1900 + yy
    elif yy > 2400:
        # 佛历 → 公历
        yy -= 543
    # 基本验证
    if not (1 <= mm <= 12 and 1 <= dd <= 31 and 2000 <= yy <= 2099):
        return None
    try:
        return date(yy, mm, dd).isoformat()
    except ValueError:
        return None


def _find_account_last4(text: str) -> Optional[str]:
    """从对账单头部找账号末 4 位"""
    # 匹配如 "Account No. xxx-x-xxxx1234" 或 "Acct XXX1234"
    patterns = [
        r"[Aa]ccount\s*(?:No|Number|#)?\.?\s*[:\s]*\S*?(\d{4})\b",
        r"[Aa]cct\.?\s*[:\s]*\S*?(\d{4})\b",
        r"เลขที่บัญชี\s*[:\s]*\S*?(\d{4})\b",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def _find_period(text: str) -> Tuple[Optional[str], Optional[str]]:
    """找对账周期起止 · 英文 'Period' / 泰文 'ประจำเดือน'"""
    # 'Period: 01/12/2024 - 31/12/2024'
    m = re.search(
        r"(?:Period|Statement\s*Period|Date\s*Range)[:\s]*"
        r"(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:-|to|ถึง)\s*(\d{1,2}/\d{1,2}/\d{2,4})",
        text, re.IGNORECASE
    )
    if m:
        return _normalize_thai_date(m.group(1)), _normalize_thai_date(m.group(2))
    # 泰文格式:ตั้งแต่วันที่ X ถึง Y
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:-|ถึง|to)\s*(\d{1,2}/\d{1,2}/\d{2,4})", text)
    if m:
        return _normalize_thai_date(m.group(1)), _normalize_thai_date(m.group(2))
    return None, None


def _find_opening_closing(text: str) -> Tuple[Optional[float], Optional[float]]:
    """找期初 / 期末余额"""
    opening = None
    closing = None
    for pat in [
        r"[Oo]pening\s*[Bb]alance[:\s]*([\d,]+\.\d{2})",
        r"[Bb]rought\s*[Ff]orward[:\s]*([\d,]+\.\d{2})",
        r"ยอดยกมา[:\s]*([\d,]+\.\d{2})",
    ]:
        m = re.search(pat, text)
        if m:
            opening = _parse_amount(m.group(1))
            break
    for pat in [
        r"[Cc]losing\s*[Bb]alance[:\s]*([\d,]+\.\d{2})",
        r"[Cc]arried\s*[Ff]orward[:\s]*([\d,]+\.\d{2})",
        r"ยอดคงเหลือ[:\s]*([\d,]+\.\d{2})",
    ]:
        m = re.search(pat, text)
        if m:
            closing = _parse_amount(m.group(1))
            break
    return opening, closing


def _month_of(d_str: Optional[str]) -> Optional[str]:
    """'2024-12-15' → '2024-12-01'"""
    if not d_str:
        return None
    try:
        d = date.fromisoformat(d_str)
        return d.replace(day=1).isoformat()
    except ValueError:
        return None


def _guess_channel(desc: str) -> str:
    """根据描述猜测渠道类型"""
    if not desc:
        return ""
    u = desc.upper()
    if "ATM" in u:
        return "ATM"
    if "TRANSFER" in u or "TRF" in u or "โอน" in desc:
        return "TRANSFER"
    if "FEE" in u or "CHARGE" in u or "ค่าธรรมเนียม" in desc:
        return "FEE"
    if "CHEQUE" in u or "CHQ" in u or "เช็ค" in desc:
        return "CHEQUE"
    if "INTEREST" in u or "ดอกเบี้ย" in desc:
        return "INTEREST"
    if "SALARY" in u or "PAYROLL" in u or "เงินเดือน" in desc:
        return "SALARY"
    if "BILL" in u or "PAY" in u:
        return "BILLPAY"
    return ""


# ============================================================
# v0.18 · 匹配算法
# ============================================================

# 权重配置(总和 100)
_W_AMOUNT    = 50
_W_DATE      = 30
_W_DIRECTION = 15
_W_KEYWORD   = 5

# 阈值
THRESH_AUTO     = 85  # 自动选中
THRESH_SUGGEST  = 60  # 可显示为疑似

# 发票金额/日期误差容忍
AMOUNT_TOL_EQUAL    = 0.01    # 小于这个差值 = 金额精确一致
AMOUNT_TOL_SMALL    = 1.00    # 1 泰铢内
AMOUNT_TOL_MEDIUM   = 10.00   # 10 泰铢内(手续费差 / 汇率小差)
DATE_TOL_DAYS       = 7       # 超过 7 天不计候选


def score_amount(bank_amount: float, invoice_amount: float) -> float:
    """金额接近度 → 0..50"""
    if not bank_amount or not invoice_amount:
        return 0.0
    diff = abs(float(bank_amount) - float(invoice_amount))
    if diff <= AMOUNT_TOL_EQUAL:
        return float(_W_AMOUNT)                     # 完全一致
    if diff <= AMOUNT_TOL_SMALL:
        return float(_W_AMOUNT) - 5                 # 1 泰铢内:45
    if diff <= AMOUNT_TOL_MEDIUM:
        return float(_W_AMOUNT) - 15                # 10 泰铢内:35
    # 更大差距:按比例打分(误差 ≤ 1% 给 20 分,≤ 5% 给 10 分)
    pct = diff / max(float(invoice_amount), 0.01)
    if pct <= 0.01:
        return 20.0
    if pct <= 0.05:
        return 10.0
    return 0.0


def score_date(bank_date: Optional[str], invoice_date: Optional[str]) -> float:
    """日期接近度 → 0..30"""
    if not bank_date or not invoice_date:
        return 0.0
    try:
        d1 = date.fromisoformat(bank_date)
        d2 = date.fromisoformat(invoice_date)
    except (ValueError, TypeError):
        return 0.0
    days = abs((d1 - d2).days)
    if days == 0:
        return float(_W_DATE)                       # 同日:30
    if days <= 1:
        return 25.0
    if days <= 3:
        return 20.0
    if days <= 7:
        return 10.0
    return 0.0


def score_direction(bank_direction: str, invoice_meta: Dict[str, Any]) -> float:
    """方向一致性 → 0 或 15
    银行 OUT = 付出去钱 = 对应 采购/费用 发票(应付)
    银行 IN  = 收到钱    = 对应 销售/收入 发票(应收)
    判断依据:ocr_history 里的 category_tag / vendor 字段
    """
    if not bank_direction:
        return 0.0
    cat = (invoice_meta.get("category_tag") or "").lower()
    # 简单分类:销售/收入类 vs 采购/费用类
    income_words = ["sale", "sales", "revenue", "income", "销售", "收入"]
    expense_words = ["purchase", "expense", "cost", "fee",
                     "采购", "费用", "开支"]
    is_income = any(w in cat for w in income_words)
    is_expense = any(w in cat for w in expense_words)

    if bank_direction == "IN" and is_income:
        return float(_W_DIRECTION)
    if bank_direction == "OUT" and is_expense:
        return float(_W_DIRECTION)
    if bank_direction == "OUT" and not is_income:
        # 大多数 OCR 历史是采购发票(默认场景)
        return float(_W_DIRECTION) * 0.7            # 约 10 分
    # 其他情况:不扣分但不加分
    return float(_W_DIRECTION) * 0.3                # 约 4.5 分


def score_keyword(bank_desc: str, invoice_meta: Dict[str, Any]) -> float:
    """描述关键词相似 → 0..5 · 软加分"""
    if not bank_desc:
        return 0.0
    desc_lower = bank_desc.lower()
    vendor = (invoice_meta.get("vendor") or "").lower()
    ref = (invoice_meta.get("invoice_no") or "").lower()

    score = 0.0
    # 供应商名在描述里出现(取前 6 字符以上的片段)
    if vendor and len(vendor) >= 3:
        # 拆 vendor 单词 · 任一个在 desc 中出现就给分
        for w in re.findall(r"[A-Za-z\u0E00-\u0E7F\u4e00-\u9fff]{3,}", vendor):
            if w in desc_lower:
                score += 3.0
                break
    # 发票号在描述里
    if ref and ref in desc_lower:
        score += 2.0
    return min(score, float(_W_KEYWORD))


def match_one_tx(bank_tx: Dict[str, Any],
                 candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """对一条银行流水 · 在候选发票集合中打分排序 · 返回 [{history_id, score, reason, breakdown}, ...]"""
    scored: List[Dict[str, Any]] = []
    for inv in candidates:
        s_amt = score_amount(bank_tx.get("amount") or 0,
                              inv.get("amount_total") or inv.get("total") or 0)
        if s_amt <= 0:
            continue                                 # 金额差太大 · 直接跳过
        s_date = score_date(bank_tx.get("tx_date"), inv.get("invoice_date"))
        s_dir  = score_direction(bank_tx.get("direction") or "", inv)
        s_kw   = score_keyword(bank_tx.get("description") or "", inv)
        total = round(s_amt + s_date + s_dir + s_kw, 2)

        # 生成人类可读原因
        parts = []
        if s_amt >= _W_AMOUNT - 0.5:
            parts.append("金额精确")
        elif s_amt >= _W_AMOUNT - 5.5:
            parts.append("金额接近")
        if s_date >= _W_DATE - 0.5:
            parts.append("同日")
        elif s_date >= 25:
            parts.append("日期差 1 天")
        elif s_date >= 20:
            parts.append("日期差 3 天内")
        elif s_date >= 10:
            parts.append("日期差 7 天内")
        if s_kw > 0:
            parts.append("描述匹配")
        reason = " + ".join(parts) if parts else "低置信"

        scored.append({
            "history_id": inv["id"],
            "score": total,
            "reason": reason,
            "breakdown": {
                "amount":    s_amt,
                "date":      s_date,
                "direction": s_dir,
                "keyword":   s_kw,
            },
        })
    # 按分降序
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:5]                                # 最多留 5 个候选


# ============================================================
# Session 级匹配:遍历所有流水 · 查候选 · 写结果
# ============================================================
def run_matching_for_session(session_id: str, user_id: str) -> Dict[str, Any]:
    """
    对一个对账会话下的所有流水跑匹配
    返回统计:{tx_total, matched, suggested, unmatched, elapsed_ms}
    """
    import time
    import db

    t0 = time.time()
    txs = db.list_bank_recon_transactions(session_id, user_id, limit=2000)
    if not txs:
        return {"tx_total": 0, "matched": 0, "suggested": 0, "unmatched": 0,
                "elapsed_ms": 0, "error": "no_transactions"}

    stat = {"matched": 0, "suggested": 0, "unmatched": 0}

    for tx in txs:
        # 只处理 unmatched / suggested(已被用户确认的 matched 跳过)
        if tx.get("match_status") == "matched":
            stat["matched"] += 1
            continue

        amt = tx.get("amount")
        tx_date = tx.get("tx_date")
        if not amt or not tx_date:
            stat["unmatched"] += 1
            continue

        # 预筛选候选
        if hasattr(tx_date, "isoformat"):
            tx_date_str = tx_date.isoformat()
        else:
            tx_date_str = str(tx_date)

        candidates = db.find_invoice_candidates_for_tx(
            user_id=user_id,
            amount=float(amt),
            tx_date=tx_date_str,
            amount_tol=AMOUNT_TOL_MEDIUM,
            date_tol_days=DATE_TOL_DAYS,
        )

        if not candidates:
            db.save_match_result(tx["id"], [],
                                  THRESH_AUTO, THRESH_SUGGEST)
            stat["unmatched"] += 1
            continue

        # 打分
        tx_for_score = {
            "amount":      float(amt),
            "tx_date":     tx_date_str,
            "direction":   tx.get("direction") or "",
            "description": tx.get("description") or "",
        }
        scored = match_one_tx(tx_for_score, candidates)

        # 写结果(算法内只保留 ≥ THRESH_SUGGEST 的)
        scored_kept = [s for s in scored if s["score"] >= THRESH_SUGGEST]
        final_status = db.save_match_result(
            tx["id"], scored_kept, THRESH_AUTO, THRESH_SUGGEST
        )
        stat[final_status] = stat.get(final_status, 0) + 1

    # 更新 session 头统计
    db.update_session_match_stats(session_id)

    elapsed = int((time.time() - t0) * 1000)
    return {
        "tx_total":   len(txs),
        "matched":    stat.get("matched", 0),
        "suggested":  stat.get("suggested", 0),
        "unmatched":  stat.get("unmatched", 0),
        "elapsed_ms": elapsed,
    }
