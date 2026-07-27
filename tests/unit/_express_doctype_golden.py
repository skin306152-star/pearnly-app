# -*- coding: utf-8 -*-
"""四类手录单据的 golden 载荷:由 `build_*_payload` **真产出**,不是手抄的样例。

存在的理由只有一个 —— 让契约测试拿到云端的真实产物去喂桥端自己的 `doc_*.validate`。
P2-B 的假绿正是两边各照自己的镜子照出来的:云端断言"产物 ⊆ 云端自己的常量",桥端断言
"白名单 == 桥端自己的副本",谁也没见过对面的东西,而四类下行路径实测一类都走不通。
手抄一份样例进桥仓等于把同一个错误抄两遍,所以这里必须现产。

选形态的准则是**恒等式尽量都走到**,不是最简单的那张:收款一张同时踩 C3/C4 + 代扣税腿
+ 预收腿,付款踩 A3/W1 + 支票行,凭证带 VAT 块与显式凭证号,库存调整带来源批与换算单位。
只走最简形态的 golden 会让"条件键根本没出现"这种假绿再来一次。

产物落盘成 `tests/fixtures/express_doctype_golden.json` —— 桥仓装不了云端这套依赖,只能读
文件,所以磁盘上这份是跨仓唯一的交接物。它由 `--write` 现产、不手改;
`test_express_bridge_contract` 每次跑都拿它和现产的比一次,改了组装却忘了刷新当场红,
桥仓不会拿到一份过期的"真产物"。

用法:
  python -m tests.unit._express_doctype_golden            打印 JSON
  python -m tests.unit._express_doctype_golden --write    刷新落盘 fixture
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

GOLDEN_JSON = PROJECT_ROOT / "tests" / "fixtures" / "express_doctype_golden.json"

from services.erp.express_push.doctypes import (  # noqa: E402
    build_journal_payload,
    build_payment_payload,
    build_receipt_payload,
    build_stock_adjust_payload,
)

# 桥端 validate 的 account_set 白名单只比字符串,与真账套目录无关。
BOOK = "DATAT"
_CONFIG = {"account_set": BOOK}


def _built(result) -> Dict[str, Any]:
    if not result.ok:
        raise AssertionError(f"golden 载荷组装失败: {result.reason}")
    return result.payload


def receipt_req(**over) -> Dict[str, Any]:
    """转账进钱 1040 + 客户代扣 30 + 动用预收 70,结清一张 1140 的赊销发票。

    NETAMT=1070(Σ渠道+代扣),C3:1140 == 1070+70+0;C4:预收明细 70 == ADVAMT。
    """
    return {
        "receipt_date": "2026-01-15",
        "customer_code": "C001",
        "channels": [{"isrun_zr_prefix": "TR", "kind": "transfer", "amount": "1040.00"}],
        "wht_amount": "30.00",
        "wht_isrun_zr_prefix": "TX",
        "allocations": [
            {"doc_no": "IV690101-001", "rectyp": "3", "amount": "1140.00", "vat_amount": "70.00"},
            {"doc_no": "AD-001", "rectyp": "0", "amount": "70.00"},
        ],
        "advance": {"doc_no": "AD-001", "amount": "70.00", "isrun_zr_prefix": "M1"},
        "prior_docnum": "RE0001",
        "userid": "ACC1",
        **over,
    }


def payment_req(**over) -> Dict[str, Any]:
    """结清一张赊购票 1000:开支票 970 + 代扣 3% 法人预扣税 30(A3/W1 都走到)。"""
    return {
        "payment_date": "2026-01-15",
        "supplier_code": "S001",
        "settlements": [
            {"doc_no": "RR690101-01", "rectyp": "3", "amount": "1000.00", "vat_amount": "65.42"}
        ],
        # bank_account 是 BKMAS.BNKACC 银行档编码 C(2),不是银行账号。
        "channels": [
            {
                "isrun_zp_prefix": "QP",
                "kind": "cheque",
                "amount": "970.00",
                "bank_account": "01",
            }
        ],
        "withholding": {
            "tax_type": "S53",
            "tax_rate": "3",
            "base_amount": "1000.00",
            "tax_amount": "30.00",
            "tax_desc": "ค่าบริการ",
        },
        "prior_docnum": "PS0001",
        "userid": "ACC1",
        **over,
    }


def journal_req(**over) -> Dict[str, Any]:
    return {
        "voucher_date": "2026-01-15",
        "journal_code": "00",
        "voucher_no": "JV6901-004",
        "description": "ปรับปรุงค่าใช้จ่ายค้างจ่าย",
        "lines": [
            {"account": "5140-10", "side": "D", "amount": "500.00", "depcod": "01"},
            {"account": "2130-01", "side": "C", "amount": "500.00"},
        ],
        "vat": {
            "vat_rec": "P",
            "vat_period": "2026-01-01",
            "base_amount": "500.00",
            "vat_amount": "35.00",
            "ref_no": "INV-9",
        },
        "userid": "ACC1",
        **over,
    }


def stock_req(**over) -> Dict[str, Any]:
    return {
        "doc_date": "2026-01-15",
        "isrun_prefix": "ZZ",
        "loccod": "01",
        "remark": "ตัดสินค้าชำรุด",
        "lines": [
            {
                "stock_code": "SKU-001",
                "qty": "2",
                "unit": "PC",
                "tfactor": "12",
                "unit_price": "250.00",
                "source_lot": "202512016OU690101-001  1",
            }
        ],
        "prior_docnum": "ZZ0001",
        "userid": "ACC1",
        **over,
    }


def golden_payloads() -> Dict[str, Dict[str, Any]]:
    """四类各一张能真正落地的单(direction → 载荷)。"""
    return {
        "ar_receipt": _built(build_receipt_payload(receipt_req(), config=_CONFIG)),
        "ap_payment": _built(build_payment_payload(payment_req(), config=_CONFIG)),
        "gl_journal": _built(build_journal_payload(journal_req(), config=_CONFIG)),
        "stock_adjust": _built(build_stock_adjust_payload(stock_req(), config=_CONFIG)),
    }


def _serialize(payloads: Dict[str, Dict[str, Any]]) -> str:
    # 序列化必须是确定性的:同一份产物重跑两次要逐字节相同,否则 --write 会刷出一堆
    # 只有排版差异的 diff,真正的键名改动被淹在里面没人看得见。不排序 = 保留组装顺序,
    # 让 diff 读起来跟 build_*_payload 里的落键顺序对得上。
    return json.dumps(payloads, ensure_ascii=False, indent=2) + "\n"


def load_golden() -> Dict[str, Dict[str, Any]]:
    """读磁盘上那份 —— 桥仓拿到的就是它,断言必须针对它而不是内存里现产的。"""
    return json.loads(GOLDEN_JSON.read_text(encoding="utf-8"))


def write_golden() -> Path:
    GOLDEN_JSON.write_text(_serialize(golden_payloads()), encoding="utf-8", newline="\n")
    return GOLDEN_JSON


if __name__ == "__main__":
    if "--write" in sys.argv[1:]:
        print(f"written: {write_golden()}")
    else:
        print(_serialize(golden_payloads()), end="")
