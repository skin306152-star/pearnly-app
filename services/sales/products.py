# -*- coding: utf-8 -*-
"""销项商品主数据 DAL(PO-2 · docs/sales-module/docs/13)。

纯参数化 SQL 叶子:每个函数收路由层传入的 cursor + tenant_id。租户隔离双保险——
db.get_cursor_rls 设 app.current_tenant_id,这里每条语句再 WHERE tenant_id(镜像
services/knowledge/dal.py)。列名只来自内部白名单,值一律占位符,杜绝注入。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

_COLS = (
    "id, tenant_id, code, barcode, qr_payload, name_th, name_en, name_zh, "
    "unit, unit_price, vat_applicable, image_url, category_id, "
    "base_unit, track_batch, track_expiry, is_weighed, min_stock, default_cost, "
    "is_active, created_at, updated_at"
)

# create 可写列;update 额外允许 is_active(软删/恢复)。
# 末 6 列为 POS PO-A2 库存地基(base_unit/批次效期/称重/低库存阈值/参考成本)。
_WRITABLE = (
    "code",
    "barcode",
    "qr_payload",
    "name_th",
    "name_en",
    "name_zh",
    "unit",
    "unit_price",
    "vat_applicable",
    "image_url",
    "category_id",
    "base_unit",
    "track_batch",
    "track_expiry",
    "is_weighed",
    "min_stock",
    "default_cost",
)
_UPDATABLE = _WRITABLE + ("is_active",)

# 可空列:PATCH 收到显式 None 才可能是"清空"这个真意图,得真写 NULL。NOT NULL 列(name_th /
# vat_applicable / is_active / base_unit / track_*)的 None 只可能是"这次没传",写下去必炸,照旧忽略。
# 路由层用 exclude_unset 保证传进来的键都是客户端真发过的 —— 少了这一步,"没传"和"传了空"
# 在这里分不开,清空就只能静默变成不改(P1-⑪)。
NULLABLE_FIELDS = {
    "code",
    "barcode",
    "qr_payload",
    "name_en",
    "name_zh",
    "unit",
    "unit_price",
    "image_url",
    "category_id",
    "min_stock",
    "default_cost",
}

# numeric 列经 str→Decimal 存(避免 float 精度)。
_NUMERIC = {"unit_price", "min_stock", "default_cost"}

# 查找键 → 列名白名单(值参数化 · 键不入 SQL 字符串拼接前先经此映射)。
_LOOKUP_COLS = {"code": "code", "barcode": "barcode", "qr": "qr_payload"}


def _money(v: Any) -> Any:
    """金额经 str 转 Decimal 存(避免 float 精度);非金额原样。"""
    return Decimal(str(v)) if v is not None else None


def _blank_to_null(fields: dict, key: str) -> dict:
    """唯一键留空归一为 NULL:部分唯一索引的谓词是 `... IS NOT NULL`,空串照样进索引,
    于是几个"没填"的商品会互相撞约束。非空则去首尾空白(扫码枪常带尾随空白/回车)。"""
    value = fields.get(key)
    if not isinstance(value, str):
        return fields
    out = dict(fields)
    out[key] = value.strip() or None
    return out


# products 上带部分唯一索引的两个键:code(uq_products_tenant_code)与
# barcode(uq_products_ws_barcode · 迁移 0092)。两者都得留空落 NULL。
_UNIQUE_KEYS = ("code", "barcode")


def _norm_unique_keys(fields: dict) -> dict:
    for key in _UNIQUE_KEYS:
        fields = _blank_to_null(fields, key)
    return fields


def _revive_soft_deleted(
    cur, *, tenant_id: str, workspace_client_id: int, fields: dict
) -> Optional[dict]:
    """新建商品的编码撞到一条【已软删】(is_active=FALSE)同编码记录时复活它并用新内容覆盖。

    软删保留已开票引用,但 uq_products_tenant_code(WHERE code IS NOT NULL)跨 active+inactive
    去重 → 同编码全表至多 1 条,故撞到软删的必无在售同码,复活安全。否则用户删了某编码后
    永远无法再用该编码(列表又看不到死记录,提示"已存在"令人困惑)。无编码或撞在售时返 None,
    走正常 INSERT(在售冲突由唯一约束 → 路由翻 product_code_exists)。"""
    code = fields.get("code")
    if not code:
        return None
    cur.execute(
        "SELECT id FROM products WHERE tenant_id = %s AND code = %s AND is_active = FALSE",
        (tenant_id, code),
    )
    dead = cur.fetchone()
    if not dead:
        return None
    # 复活时归到当前套账(code 唯一约束是租户级 · 死记录全租户至多 1 条 · 移到当前套账安全)。
    sets = ["is_active = TRUE", "workspace_client_id = %s"]
    vals: list = [workspace_client_id]
    for k in _WRITABLE:
        if fields.get(k) is not None:
            sets.append(f"{k} = %s")
            vals.append(_money(fields[k]) if k in _NUMERIC else fields[k])
    sets.append("updated_at = now()")
    cur.execute(
        f"UPDATE products SET {', '.join(sets)} WHERE tenant_id = %s AND id = %s RETURNING {_COLS}",
        vals + [tenant_id, dead["id"]],
    )
    row = cur.fetchone()
    if row is not None:
        _revive_units(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            product_id=dead["id"],
        )
    return row


def create_product(cur, *, tenant_id: str, workspace_client_id: int, fields: dict) -> dict:
    fields = _norm_unique_keys(fields)
    revived = _revive_soft_deleted(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, fields=fields
    )
    if revived is not None:
        return revived
    cols = ["tenant_id", "workspace_client_id"]
    vals: list = [tenant_id, workspace_client_id]
    for k in _WRITABLE:
        if fields.get(k) is not None:
            cols.append(k)
            vals.append(_money(fields[k]) if k in _NUMERIC else fields[k])
    placeholders = ", ".join(["%s"] * len(vals))
    cur.execute(
        f"INSERT INTO products ({', '.join(cols)}) VALUES ({placeholders}) RETURNING {_COLS}",
        vals,
    )
    return cur.fetchone()


def get_product(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str
) -> Optional[dict]:
    cur.execute(
        f"SELECT {_COLS} FROM products WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, product_id),
    )
    return cur.fetchone()


def list_products(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    include_inactive: bool = False,
    query: Optional[str] = None,
    limit: int = 200,
) -> list:
    sql = f"SELECT {_COLS} FROM products WHERE tenant_id = %s AND workspace_client_id = %s"
    params: list = [tenant_id, workspace_client_id]
    if not include_inactive:
        sql += " AND is_active = TRUE"
    if query:
        sql += " AND (name_th ILIKE %s OR name_en ILIKE %s OR name_zh ILIKE %s OR code ILIKE %s)"
        like = f"%{query}%"
        params += [like, like, like, like]
    sql += " ORDER BY name_th LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    return cur.fetchall()


def _set_unit_visibility(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str, active: bool
) -> None:
    """商品上/下架时同步它各售卖单位的"所属商品在售"标记(箱码/瓶码跟着让位或收回)。

    主码靠 products 唯一索引的 is_active 谓词自动让位——值还在,复活即生效;单位码曾经是
    把 barcode 抹成 NULL,值一去不回:季节性下架再上架,商品和主码都回来了,三条单位码全空,
    扫箱码 404「商品不存在」而商品就在列表里,无提示无审计,只能一条条重录。软删的契约是
    "保留引用、可复活",抹值破的正是这条,所以单位码也改走谓词。

    标记必须落在 product_units 本表:该表没有 is_active(删单位是硬删),而部分唯一索引的
    谓词只能引用本表列,引用不到 products.is_active。不加触发器(全仓无触发器,新起一套没人
    记得),改由四条写路径维护:本文件的 deactivate / update / revive,加上新建单位行时
    services/products/units._sync_product_active(挂到停用商品上的新行不许自带"在售")。
    """
    cur.execute(
        "UPDATE product_units SET product_active = %s, updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND product_id = %s "
        "AND product_active IS DISTINCT FROM %s",
        (active, tenant_id, workspace_client_id, product_id, active),
    )


def _revive_units(cur, *, tenant_id: str, workspace_client_id: int, product_id: str) -> None:
    """复活商品时收回它的单位码,并把单位行跟着挪到当前套账。

    ws 写在 SET 不在 WHERE:复活会把商品移到当前套账(见 _revive_soft_deleted),单位行不跟着
    走就成孤儿——list_units 按 ws 查,它们从界面上消失,码却还占着。租户隔离仍由 tenant_id 兜,
    product_id 是全局唯一的 uuid 主键,跨租户拿不到别人的行。
    """
    cur.execute(
        "UPDATE product_units SET product_active = TRUE, workspace_client_id = %s, "
        "updated_at = now() WHERE tenant_id = %s AND product_id = %s",
        (workspace_client_id, tenant_id, product_id),
    )


def update_product(
    cur, *, tenant_id: str, workspace_client_id: int, product_id: str, fields: dict
) -> Optional[dict]:
    fields = _norm_unique_keys(fields)
    # 键在不在 fields 里 = 客户端这次改没改它(路由用 exclude_unset 保证);值是不是 None =
    # 改成空还是改成某个值。可空列的 None 照写 NULL,否则"清空条码"静默变成不改(还回 ok:true),
    # 而写空串又会撞部分唯一索引(空串不是 NULL)。
    updates = {
        k: fields[k]
        for k in _UPDATABLE
        if k in fields and (fields[k] is not None or k in NULLABLE_FIELDS)
    }
    if not updates:
        return get_product(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, product_id=product_id
        )
    sets = ", ".join(f"{k} = %s" for k in updates) + ", updated_at = now()"
    params = [_money(v) if k in _NUMERIC else v for k, v in updates.items()]
    params += [tenant_id, workspace_client_id, product_id]
    cur.execute(
        f"UPDATE products SET {sets} "
        f"WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s RETURNING {_COLS}",
        params,
    )
    row = cur.fetchone()
    # PATCH is_active 两个方向都得同步:false 是 DELETE 之外的另一条软删路径,true 是从
    # 商品列表(含停用)直接重新上架 —— 只跟 false 就成了"下架让码、上架不收回"。
    if row is not None and "is_active" in updates:
        _set_unit_visibility(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            product_id=product_id,
            active=bool(updates["is_active"]),
        )
    return row


def deactivate_product(cur, *, tenant_id: str, workspace_client_id: int, product_id: str) -> bool:
    """软删:置 is_active=FALSE(不物删 · 保留已开票引用)。"""
    cur.execute(
        "UPDATE products SET is_active = FALSE, updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, product_id),
    )
    if cur.rowcount <= 0:
        return False
    _set_unit_visibility(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        product_id=product_id,
        active=False,
    )
    return True


def _find_by_barcode(cur, *, tenant_id: str, workspace_client_id: int, value: str) -> tuple:
    """扫码命中口径与 POS(services/pos/catalog.product_by_barcode)同一套:先配单位码
    (箱码/瓶码 ≠ 主码),再配商品主码。两边曾分叉——主 SPA 只查 products.barcode,于是
    POS 认得的箱码在入库/建品查重这边显示"没人用",绿字骗人还放行重码。

    单位码查询带 product_active:停用商品的单位行现在保留 barcode 值(见 _set_unit_visibility),
    不筛就会有多条同码行,`LIMIT 1` 无 ORDER BY 挑中哪条全看运气 —— 挑中停用那条就把在售的
    单位码报成"没这个货"。加上谓词后唯一索引保证至多一条,结果确定。
    仍保留"命中单位但商品已停用 → 回落主码":老库里可能还有 product_active 回填之前的残留行。
    返回 (row, matched_by, unit)。
    """
    cur.execute(
        "SELECT product_id, unit_name FROM product_units "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND barcode = %s "
        "AND product_active LIMIT 1",
        (tenant_id, workspace_client_id, value),
    )
    unit = cur.fetchone()
    if unit:
        cur.execute(
            f"SELECT {_COLS} FROM products WHERE tenant_id = %s AND workspace_client_id = %s "
            f"AND id = %s AND is_active = TRUE",
            (tenant_id, workspace_client_id, str(unit["product_id"])),
        )
        row = cur.fetchone()
        if row:
            return row, "unit", unit["unit_name"]
    cur.execute(
        f"SELECT {_COLS} FROM products WHERE tenant_id = %s AND workspace_client_id = %s "
        f"AND barcode = %s AND is_active = TRUE LIMIT 1",
        (tenant_id, workspace_client_id, value),
    )
    return cur.fetchone(), "product", None


def find_by(
    cur, *, tenant_id: str, workspace_client_id: int, key: str, value: str
) -> Optional[dict]:
    """按 code/barcode/qr 精确查在售商品(POS 点单/扫码快速带出)。

    命中行外加两个字段:matched_by = product(商品自己的编码/主码/QR)或 unit(某售卖单位
    的条码),matched_unit = unit 命中时的单位名。调用方靠它说清"这码是箱码还是主码",
    不然撞码提示只能含糊说"已被占用"。
    """
    col = _LOOKUP_COLS.get(key)
    if not col or not value:
        return None
    if key == "barcode":
        row, matched_by, unit_name = _find_by_barcode(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, value=value
        )
    else:
        cur.execute(
            f"SELECT {_COLS} FROM products WHERE tenant_id = %s AND workspace_client_id = %s "
            f"AND {col} = %s AND is_active = TRUE LIMIT 1",
            (tenant_id, workspace_client_id, value),
        )
        row, matched_by, unit_name = cur.fetchone(), "product", None
    if not row:
        return None
    return dict(row) | {"matched_by": matched_by, "matched_unit": unit_name}


# ── 条码唯一约束(迁移 0092 与启动双跑共用同一份 SQL · 生产不跑 alembic)──────────
# 前端撞码提示只是 UX 层:Excel 导入(services/sales/product_import.py)和直调 API 都绕得过,
# 建出的重码要到收银台扫出错商品才暴露,那时改不动。唯一性只有数据库拦得住。
# product_units.barcode 一并收:POS 的 product_by_barcode 对单位码是 `LIMIT 1` 无 ORDER BY,
# 两条同码单位存在时扫出哪个商品不确定 —— 那是钱路径。
# 跨表撞码(A 的单位码 = B 的主码)两条索引都表达不了,靠 find_by 两表都查在 UX 层兜。

_BARCODE_SCOPES = (("products", " AND is_active = TRUE"), ("product_units", " AND product_active"))

# product_active 让位标记(0093):停用商品的单位行留着 barcode 值但退出索引。老索引名不带这个
# 谓词,`IF NOT EXISTS` 撞上同名旧索引会当没事发生 —— 改名 + 显式 DROP 旧名,才不会留个
# "看着建好了、其实还是老谓词"的索引在生产上。
_UNIT_VISIBILITY_DDL = (
    "ALTER TABLE product_units ADD COLUMN IF NOT EXISTS product_active boolean NOT NULL DEFAULT TRUE",
    "UPDATE product_units pu SET product_active = p.is_active FROM products p "
    "WHERE p.id = pu.product_id AND pu.product_active IS DISTINCT FROM p.is_active",
)

_BARCODE_UNIQUE_DDL = (
    # 老索引跟新的只差谓词,同名 `IF NOT EXISTS` 会当没事发生 —— 必须先按旧名 DROP 再按新名建,
    # 否则生产上留个"看着建好了、其实还是老谓词"的索引,停用商品照旧占着单位码。
    "DROP INDEX IF EXISTS uq_product_units_ws_barcode",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_products_ws_barcode ON products "
    "(tenant_id, workspace_client_id, barcode) WHERE barcode IS NOT NULL AND is_active = TRUE",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_product_units_live_barcode ON product_units "
    "(tenant_id, workspace_client_id, barcode) WHERE barcode IS NOT NULL AND product_active",
)


def ensure_unit_visibility_column(cur) -> None:
    """product_units.product_active 补列 + 从 products 回填(迁移 0093 与启动双跑共用)。

    必须早于 barcode_conflicts:体检查询按新谓词(只看在售商品的单位行)归组,列不在就直接报错。
    """
    for ddl in _UNIT_VISIBILITY_DDL:
        cur.execute(ddl)


# 迁移 0093 与启动双跑共用。DROP NOT NULL / DROP DEFAULT 对已经是这个状态的列是无声成功,
# 幂等。存量 0 不回填成 NULL:分不清哪些是真的 ฿0(赠品)、哪些是老默认值顶上的,
# 一刀切改成 NULL 会让今天卖得好好的商品明天在收银台被零元闸拦下。
_PRICE_NULLABLE_DDL = (
    "ALTER TABLE products ALTER COLUMN unit_price DROP DEFAULT",
    "ALTER TABLE products ALTER COLUMN unit_price DROP NOT NULL",
)


def relax_price_not_null(cur) -> None:
    """products.unit_price 去掉 NOT NULL + DEFAULT 0(P0-① · 迁移 0093 与启动双跑共用)。

    带着 `NOT NULL DEFAULT 0`,"没设价"进库就变成 0,和真的 ฿0 在数据层完全一样:收银台的
    零元闸只拦得住 null,拦不住 0,于是"扫码→就地建品"建出来的商品全部 ฿0 可售。
    """
    for ddl in _PRICE_NULLABLE_DDL:
        cur.execute(ddl)


def barcode_conflicts(cur, *, limit: int = 50) -> dict:
    """建索引前的存量体检:同 (租户, 套账) 下重复的条码分组,按表分组返回。

    有脏数据时 CREATE UNIQUE INDEX 会直接报错炸在生产库上,所以先查后建。按 btrim 归组——
    索引创建前会把空白/空串归一,` 8850` 与 `8850` 归一后才撞上,体检必须用归一后的值。
    两张表都只看"在售"的行,与各自索引谓词一致:products 看 is_active,product_units 看
    product_active(所属商品在售 · 见 _set_unit_visibility)。
    """
    out: dict = {}
    for table, active in _BARCODE_SCOPES:
        cur.execute(
            f"SELECT tenant_id, workspace_client_id, btrim(barcode) AS barcode, count(*) AS n "
            f"FROM {table} WHERE btrim(coalesce(barcode, '')) <> ''{active} "
            f"GROUP BY tenant_id, workspace_client_id, btrim(barcode) "
            f"HAVING count(*) > 1 ORDER BY count(*) DESC LIMIT %s",
            (limit,),
        )
        out[table] = [dict(r) for r in cur.fetchall()]
    return out


def create_barcode_unique_indexes(cur) -> None:
    """归一存量条码 + 建部分唯一索引(幂等 · 迁移 0092/0093 与启动双跑共用)。

    先归一是必须的:空串不是 NULL,照样进 `WHERE barcode IS NOT NULL` 的索引,几个
    "没填条码"的老商品会互撞;首尾空白同理(扫码枪带回车,老数据里存过)。
    调用方须自己先跑 ensure_unit_visibility_column + barcode_conflicts —— 这里不吞错,
    有真重复就让 CREATE 报出来。
    """
    for table, _ in _BARCODE_SCOPES:
        cur.execute(
            f"UPDATE {table} SET barcode = nullif(btrim(barcode), '') "
            f"WHERE barcode IS DISTINCT FROM nullif(btrim(barcode), '')"
        )
    for ddl in _BARCODE_UNIQUE_DDL:
        cur.execute(ddl)
