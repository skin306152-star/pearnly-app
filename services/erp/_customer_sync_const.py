# -*- coding: utf-8 -*-
"""MR.ERP 客户同步 · 默认值/上限常量 leaf。"""

CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT = 0.82  # Zihao 2026-05-18 拍板

# Per [mrerp-master-data-sync-design.md §3.4](../../docs/integrations/mrerp-master-data-sync-design.md):
# Default customer code template is P{YYMM}{SEQ4} = 9 chars (well under
# the 20-char ceiling). 'P' = Pearnly-created so admins can spot
# auto-created rows in MR.ERP.
DEFAULT_CUSTOMER_CODE_PREFIX = "P"

# Default values for required MR.ERP fields the OCR doesn't provide.
# Tunable per-tenant in a future settings table (see design §8). The
# values here mirror what Zihao manually set when creating customer 0006.
DEFAULT_CUSTOMER_TYPE_CODE = "1-11"  # ลูกหนี้การค้า
DEFAULT_CUSTOMER_TYPE_LABEL = "ลูกหนี้การค้า"
DEFAULT_BRANCH_CODE = "00000"  # สำนักงานใหญ่
DEFAULT_BRANCH_LABEL = "สำนักงานใหญ่"
DEFAULT_COUNTRY = "ไทย"

# checknull() on armas/allform.php demands every "required" cell be
# non-empty. The list below mirrors the JS alert text discovered during
# Phase 3 integration testing (2026-05-18) — Zihao's manual 0006 setup
# only filled 4 fields because the master-data picker prefilled the
# other defaults. Our auto-create skips the picker, so we have to plant
# placeholders for every cell checknull() inspects.
DEFAULT_NUMERIC_TEXT = "0.00"
DEFAULT_PLACEHOLDER = "0000"
# Discovered via bshlistboxdata.php: the txtacfile picker's first valid
# account code on TEST2019 is "1111-01" / เงินสด. Different tenants
# will likely need to override this via tenant_settings — see open
# questions in mrerp-master-data-sync-design.md §9.
TENANT_VALID_ACCOUNT_CODE = "1111-01"
DEFAULT_CREDIT_TERM = "0"
DEFAULT_EXCHANGE_RATE = "1.00"
DEFAULT_CUSTOMER_RANK = "-"

CUSTOMER_NAME_MAX = 100  # MR.ERP UI accepts up to ~100; conservative
