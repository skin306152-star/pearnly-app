# -*- coding: utf-8 -*-
"""商品收发存报表(Stock Card)· 事务所端按客户账套出进销存流水(泰国 VAT 商户法定台账)。

模块地图:grouping(明细行归组)· rolling(移动加权平均纯算法)· schema(建表 dual-run)·
opening(期初 CRUD)· merge(商品归并回填)· report(查询装配 · summary/card/excluded)。
"""

from __future__ import annotations
