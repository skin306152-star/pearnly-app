# 主项目契约事实(只读核对 · 2026-06-03)

P0 窗口对 `C:\Users\skin3\Desktop\pearnly-app` 只读核对的结果,供 `host/contract.py`
对齐、迁移(P-MIG)接线、P1~P5 建表/SQL 参考。**别猜类型,以此为准。**

## ID 类型(最易炸的点)
- `ocr_history.id` = **UUID** 主键(代码里以 `str` 形式流转,SQL 用 `%s::uuid`)。
- `workspace_clients.id` = **BIGSERIAL(bigint)** 主键。
- `ocr_history.workspace_client_id` = **BIGINT**(可空,账套归属)。
- `workspace_clients.tenant_id` = UUID(可空)、`user_id` = UUID(非空)。
- 结论:沙盒里 `OcrHistoryRow.id` 用 str(UUID)、`workspace_client_id` 用 int。已落入 `host/contract.py`。

## 数据库访问(db.py 镜像来源:core/db.py)
- `psycopg2` + `SimpleConnectionPool(minconn=2, maxconn=30, connect_timeout=10, sslmode="require")`。
- `@contextmanager get_cursor(commit=False)`,`cursor_factory=RealDictCursor`,异常 rollback。
- 连接串环境变量:`DATABASE_URL`(prod 是 Supabase Pooler)。
- 建表风格:`ensure_*()` 函数 + `db.get_cursor(commit=True)`(DDL 必须 commit)+ 幂等
  `CREATE TABLE/INDEX IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`,启动时在 `services/startup.py` 调。

## 鉴权 + 租户(contract.get_current_identity 镜像来源)
- `core/auth.py::get_current_user_from_request(request: Request) -> Dict[str, Any]`。
- 关键字段:`id`(user UUID)、`tenant_id`、`active_tenant_id`(**多公司切换时优先用此**)、
  `role`(`"owner"` | `"member"`)、`is_super_admin`。

## workspace 权限(contract.get_accessible_workspace_client_ids 镜像来源)
- `services/workspace/store.py::list_workspace_clients(user_id, tenant_id=None, restrict_ids=None, active_only=True)`。
- `services/membership/assignments.py::get_visible_client_ids_for_user` 三态:
  `None`=无限制(super_admin/owner)、`List[int]`=member 可见客户、`[]`=member 无分配。
  沙盒 stub 的 owner 返回 None 即对齐此语义。

## 存储(contract.storage_* 镜像来源)
- **本地文件系统**,非 S3/Supabase Storage。`services/ocr/pdf_storage.py`:
  `save_pdf(user_id, content) -> (rel_path, bytes)`、`get_pdf_abs_path(rel_path) -> Path`、`delete_pdf(rel_path) -> bool`。
- 环境变量 `PDF_STORAGE_DIR`,路径规则 `{DIR}/{user_id前8位}/{YYYY-MM}/{uuid}.pdf`。
- 迁移启示:contract 的字节进/出语义可直接接 `pdf_storage`;签名 URL/content-type 是 P4/P5 扩展点。
