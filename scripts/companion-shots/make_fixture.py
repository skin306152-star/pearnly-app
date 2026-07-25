# -*- coding: utf-8 -*-
"""造配图专用的虚构 Express 数据根:三个账套 + 一张十行科目表。

为什么需要它
    配对窗的「选择账套」下拉和高级设置里的六个科目下拉,内容全部来自 Express 的 DBF:
    secure/SCCOMP.DBF 给账套清单,各账套目录下的 ISINFO.DBF 给默认科目、GLACC.DBF 给可选
    科目。没有数据根 = 下拉全空,截出来的是空壳,对会计零信息量。

为什么不指向真账套
    真账套里是客户的公司名和税号,配图会公开发布。这里的公司名刻意写成
    ตัวอย่าง/ทดสอบ/สาธิต(示例/测试/演示),税号也是不可能存在的号段,读者一眼看出是演示数据。

只写传入的 scratch 目录,由 orchestrate.ps1 通过 PEARNLY_EXPRESS_ROOT 只喂给截图子进程;
在用小助手的配置、注册表、真 Express 共享一概不碰。

用法: make_fixture.py <root>
"""

import shutil
import sys
from pathlib import Path

import dbf

ROOT = Path(sys.argv[1])
CP = "cp874"

COMPANIES = [
    ("1. บริษัท ตัวอย่าง เทรดดิ้ง จำกัด", "DEMO1", "DEMO1", "0105560000011"),
    ("2. บริษัท ทดสอบการค้า จำกัด", "DEMO2", "DEMO2", "0105560000022"),
    ("3. ห้างหุ้นส่วนจำกัด สาธิตบริการ", "DEMO3", "DEMO3", "0105560000033"),
]

# ACCTYP='0' 可记账 / STATUS='A' 启用 —— 两者都对才会进配对窗的科目下拉
CHART = [
    ("11-01-01-00", "เงินสด", "1"),
    ("11-02-01-00", "ลูกหนี้การค้า", "1"),
    ("11-05-01-00", "สินค้าคงเหลือ", "1"),
    ("11-06-01-00", "ภาษีซื้อ", "1"),
    ("21-01-01-00", "เจ้าหนี้การค้า", "2"),
    ("21-05-01-00", "ภาษีขาย", "2"),
    ("41-01-01-00", "รายได้จากการขาย", "4"),
    ("41-02-01-00", "รายได้อื่น", "4"),
    ("51-01-01-00", "ซื้อสินค้า", "5"),
    ("53-01-01-00", "ค่าใช้จ่ายในการขาย", "5"),
]

DEFAULTS = {
    "ACCNUM02": "11-02-01-00",  # 应收
    "ACCNUM04": "51-01-01-00",  # 采购/进货
    "ACCNUM06": "11-06-01-00",  # 进项税
    "ACCNUM07": "21-01-01-00",  # 应付
    "ACCNUM10": "21-05-01-00",  # 销项税
    "ACCNUM11": "41-01-01-00",  # 收入
}


def build() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    (ROOT / "secure").mkdir(parents=True)

    reg = dbf.Table(
        str(ROOT / "secure" / "SCCOMP.DBF"),
        "COMPNAM C(60); COMPCOD C(8); PATH C(80); GENDAT C(8); CANDEL C(1)",
        codepage=CP,
    )
    reg.open(dbf.READ_WRITE)
    for name, code, path, _tax in COMPANIES:
        reg.append((name, code, path, "20260101", "Y"))
    reg.close()

    info_spec = "THINAM C(80); TAXID C(13); " + "; ".join(f"{k} C(20)" for k in sorted(DEFAULTS))
    acc_spec = "ACCNUM C(20); ACCNAM C(60); ACCNAM2 C(60); ACCTYP C(1); STATUS C(1); GROUP C(2)"
    for name, _code, path, tax in COMPANIES:
        d = ROOT / path
        d.mkdir(parents=True, exist_ok=True)
        info = dbf.Table(str(d / "ISINFO.DBF"), info_spec, codepage=CP)
        info.open(dbf.READ_WRITE)
        info.append((name.split(". ", 1)[-1], tax) + tuple(DEFAULTS[k] for k in sorted(DEFAULTS)))
        info.close()

        glacc = dbf.Table(str(d / "GLACC.DBF"), acc_spec, codepage=CP)
        glacc.open(dbf.READ_WRITE)
        for code_, nm, grp in CHART:
            glacc.append((code_, nm, nm, "0", "A", grp))
        glacc.close()
    print("fixture built:", ROOT)


build()
