# -*- coding: utf-8 -*-
"""明细行归组(双轨 key · P2C item_name.clean 复用)。

有 product_id 归到商品主档(key=p:<id>);否则用清洗后的品名当归组身份(key=n:<name_key>)
—— 商户很多票没建商品档,只能靠"洗过的名字写法一致"当同一件货的替身,不做模糊匹配、
不猜测、不跨语言归并(泰文/英文品名各自成组,宁可拆细也不错并)。
"""

from __future__ import annotations

from typing import Optional

from services.purchase import item_name

PRODUCT_PREFIX = "p:"
NAME_PREFIX = "n:"


def name_key(description) -> str:
    """归组身份用的清洗名(与展示清洗同一套规则 · P2C item_name.clean)。"""
    return item_name.clean(description)


def group_key(*, product_id: Optional[str], description) -> Optional[str]:
    """算一行的归组钥匙。product_id 优先;否则清洗名非空才归组,整名不可读(清洗后空)不归
    任何组 —— 调用方按此把该行归入「未入账清单」,不硬凑一个空钥匙的组。"""
    if product_id:
        return f"{PRODUCT_PREFIX}{product_id}"
    key = name_key(description)
    return f"{NAME_PREFIX}{key}" if key else None


def is_product_key(key: str) -> bool:
    return key.startswith(PRODUCT_PREFIX)


def key_product_id(key: str) -> Optional[str]:
    """key 是 p: 轨才有意义,否则 None。"""
    return key[len(PRODUCT_PREFIX):] if is_product_key(key) else None


def key_name(key: str) -> Optional[str]:
    """key 是 n: 轨才有意义,否则 None。"""
    return key[len(NAME_PREFIX):] if key.startswith(NAME_PREFIX) else None
