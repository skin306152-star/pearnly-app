# -*- coding: utf-8 -*-
"""商户采购(进项)模块服务层(B 路线 Phase 1 · docs/purchasing)。

进货 / 费用录入、供应商、两级费用科目、采购设置、智能分流(intake)、凭据生成。
全部按 workspace_client_id 套账隔离(fail-closed)。复用销项 totals/pdf、库存 ledger、OCR pipeline。
"""
