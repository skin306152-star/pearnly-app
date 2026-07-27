# -*- coding: utf-8 -*-
"""配方注册表 —— 「加一个配方」= 加一个文件,不是改一堆。

services/ledger/recipes/ 下每个模块在 import 时调 register() 把自己挂上来;
recipes/__init__ 遍历包内模块自动 import。所以新增进项台账/银行流水/费用明细时,
要动的只有一个新文件,注册表、调用方、路由都不用改。

配方的 build 签名故意不统一:销售票配方吃 SalesDoc,银行流水配方吃对账行,硬捏成同一个
参数包只会逼出一个什么都装的 dict。统一的是**产出**(RecipeResult)—— 消费方(下一批的
管家工具)只认这个契约。
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable, Dict, Mapping, Tuple

_REGISTRY: Dict[str, "RecipeSpec"] = {}
_LOADED = False


@dataclass(frozen=True)
class RecipeResult:
    """配方产出。字节之外的每一项都是给调用方直接用的,不必再开一次工作簿去数。

    numbers 是**权威值**:表里对应的格子写的是公式,openpyxl 读不到公式的结果。
    回执里报的、闸判的都取这里,不取表里那个自检格(那格只给眼睛看)。
    """

    code: str
    filename: str
    content: bytes
    sheets: Tuple[str, ...]
    numbers: Mapping[str, Any]
    documents: Tuple[Mapping[str, Any], ...] = ()
    pending: Tuple[Mapping[str, Any], ...] = ()
    chart_source: str = ""
    chart_unresolved: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()

    @property
    def balanced(self) -> bool:
        debit = self.numbers.get("debit_total", Decimal("0"))
        credit = self.numbers.get("credit_total", Decimal("0"))
        return debit == credit


@dataclass(frozen=True)
class RecipeSpec:
    """一个配方的元信息 + 入口。sheets 是产出表名,给 UI 在下载前说清里面有什么。"""

    code: str
    title_th: str
    title_zh: str
    sheets: Tuple[str, ...]
    build: Callable[..., RecipeResult]
    input_kind: str = ""
    notes: Tuple[str, ...] = field(default_factory=tuple)


def register(spec: RecipeSpec) -> RecipeSpec:
    """注册配方。重名直接抛 —— 两个配方抢一个 code 时静默覆盖会让人查半天。"""
    if spec.code in _REGISTRY:
        raise ValueError(f"配方 code 重复: {spec.code}")
    _REGISTRY[spec.code] = spec
    return spec


def _load() -> None:
    global _LOADED
    if _LOADED:
        return
    _LOADED = True  # 先置位:配方模块 import 期回调 list_recipes 也不会递归重入
    package = importlib.import_module("services.ledger.recipes")
    for module in pkgutil.iter_modules(package.__path__):
        if not module.name.startswith("_"):
            importlib.import_module(f"{package.__name__}.{module.name}")


def get_recipe(code: str) -> RecipeSpec:
    _load()
    try:
        return _REGISTRY[code]
    except KeyError:
        raise KeyError(f"未知配方: {code!r}(已注册: {sorted(_REGISTRY)})") from None


def list_recipes() -> Tuple[RecipeSpec, ...]:
    _load()
    return tuple(_REGISTRY[c] for c in sorted(_REGISTRY))
