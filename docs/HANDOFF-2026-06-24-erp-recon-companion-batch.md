# 交接 · 2026-06-24 「ERP/对账/companion 多事项批」窗口收尾

> 给下一个窗口。本窗口不是单一 task,是一串真机驱动的 bug 修 + companion 发版 + 数据运维。
> 只写事实与待办。所有 cloud 改动已 push master + 部署 + prod 验证;companion 已发版。

---

## 一、已完成并上线(cloud · pearnly-app)

| commit | 内容 | 验证 |
|---|---|---|
| `278564e1` | **fix(ocr)**:`FieldRef` 内层标量字段(source_text/column/page/confidence)容忍 Gemini 返 null。真因=LINE 清晰收据被误判「读不清」:Gemini 对无表格列的简单收据返 `source_column=null`,显式 null 绕过 `Field(default='')` → ThaiInvoice 校验失败 → ocr_failed 卡。`schemas_layer1.py` 加 `mode=before` 校验器。 | prod 日志实锤 + 325 OCR 测试 + 4783 全量 |
| `d622f41a`+`021c010b` | **fix(express)**:端点连接卡过期快照修复(`erp-express-connect.ts` 可见时自愈轮询 + `erp-express-wizard.ts` `_syncCard` 向导→卡同步)。`021c010b` 把 wizard.ts 从 509 压回 500(`d622f41a` 顶破 size 闸致 CI 红·已修)。 | 真站逻辑 + CI 绿 |
| `68db66ae` | **chore(billing)**:`suthida_chatgpt@outlook.com` 加入计费豁免白名单(`credits_schema.py` ensure 列表 + prod DB 直更 `is_billing_exempt=true`·user `ce43ee27`)。 | prod DB 验证 |
| `3d7902bc` | **fix(recon)**:GL 期初余额按首笔运行余额反推校正(防 OCR 截断千分位)。见下「② GL 截断」。 | prod 端到端 PASS |
| `74b75bf6` | **refactor(/simplify)**:端点卡自愈轮询 20s→60s(在线窗口 3 分钟·减冗余 /logs 拉取)。 | size 闸绿 |

线上前端版本现 `?v=11850970`。

---

## 二、关键 bug 详情(下个窗口若复发先读)

### ① Express 推送慢(companion · 已发版未真机验收)
- 根因:`dbf_writer._backup` 每张票写前 `shutil.copytree` **整账套 255 文件**(还在 `\\accserver` 网络盘)→ 每张 ~1 分钟串行。
- 修(companion commit `12c7313`):`_backup` 加 `tables` 参数,只备 `BACKUP_TABLES` allowlist(采购/销项写表 + APMAS/ARMAS 主档 + STCRD/STBAL)的 `.DBF/.CDX/.FPT` ≈30 文件 → ~8× 提速。`tables=None` 维持整目录复制向后兼容。56 DBF 测试绿。
- **已发版 companion 1.1.9**(`01192da` + `release.ps1`·latest.json 已上 prod)。**另一窗口又 bump 到 1.1.10**(version.py)。
- **⏳ 待办:Owner 真机验收提速**(robocopy 备账套→推 4 票→`activity.log` 时间戳从 ~1 分钟降到秒级→账套行数对 baseline→测一次写失败能回滚)。Owner 重启小助手即自动更新拿到。

### ② GL↔银行对账「GL 期初读错」(cloud · 已修 `3d7902bc`)
- 现象:mrerp 账号今天泰国 10:45/11:10 跑两次,GL **期初 215,228.06→215.00、期末 497,558.06→497.00**(千分位逗号后被砍),交易明细+行运行余额都读对了。
- 根因:**间歇性** pdfplumber 把账户头那行期初截断(直跑 5/5 正确·复现不稳定·非文件/非 Gemini)。**真根因未定位**(偶发),但下面安全网兜住。
- 修:`bank_recon_merge.merge_gl_files` 加 `_reconcile_gl_opening`:用首笔『运行余额 −(借−贷)』反推真期初,**仅当整列运行余额自洽**(反推+Σ借−Σ贷≈末行余额)才采信,否则保留+告警。期初修对→closing 自动算对。
- **已知盲区**:若走 **Gemini 兜底**(行 `balance=0`,无运行余额),此修救不了(`bal_rows` 空→原样返回)。客户那次是 pdfplumber(行余额正确)故被救。Gemini-both-anchors-truncated 仍是裸 case → 留观察。

---

## 三、数据运维(本窗口在 prod/accserver 上做的)

1. **Express 测试套账清 4 张票**(Owner 要重测):`\\accserver\ACCOUNT\70EXP\test` 删 RR681214-001/RR681215-001/IV681220-001/IV681221-001 + 3 个自动建主体(供应商 ส081·客户 ล007/เ001),标删+PACK+reindex。**安全快照** `\\accserver\ACCOUNT\70EXP\test_pearnly_precleanup_20260624-093218`(9 表·可回滚·确认重测 OK 后可删)。脚本 `scratchpad/cleanup_tickets.py`(dry-run 默认)。**重要发现**:server 上 6 个旧 `TEST_pearnly_bak_*` 的 GL 表比当前 test 多 ~1700 行(PACK 已清残留)→ **不能用任何旧快照整套 /MIR 还原**(会灌回残留),只能精准删行。
2. **账套放开调研**:代码层**早已不锁 DATAT**(2026-06-22 T2-A `dc7dc1f1` 去写死)。`account_set_allowed`=只放行「==端点配置的 account_set」(防串账套安全闸·非 DATAT 锁);companion `allowed_account_sets(st.account_set)`=按配对所选账套;`writable` 只是 `os.access(W_OK)`。mapper.py/erp_agent.py 里「只允许 DATAT」是**过时注释**。**正式上线只需在小助手里选真账套**·三重安全闸(账套名+目录+公司)保留。**未做(可选)**:清那几处过时注释。

---

## 四、坑提醒(本窗口踩的)
- **push 前必跑 `python scripts/check_file_size.py`**(本 clone 无 pre-push hook)。`d622f41a` 没跑→把 500 顶格的 wizard.ts 顶到 509→CI 红连累并行窗口·`021c010b` 压注释修回。
- 改 `src/home/*` → `npm run build` + bump `home.html` 三处 `?v=`(home.css/i18n-data.js/main.js 同号)+ `git add` **dist/home.html + dist/main.js 两个**。纯注释改 minify 后 bundle 不变·不用 bump(`021c010b` 即此类)。
- 共享树并发:别窗口高频提交·HEAD 乱跳·OneDrive 致 Bash-git 偶发看到旧文件视图(用 PowerShell git/Read 交叉核)。push 前 `git fetch` 查 behind。只 `git add` 自己的文件。
- prod 查/跑:`ssh root@66.42.49.213` → `cd /opt/mrpilot && set -a && . ./.env && set +a` → `PYTHONUTF8=1 PYTHONPATH=/opt/mrpilot venv/bin/python`。GEMINI_API_KEY 在 .env。
- 银行对账管线:`parse_bank_statement_pdf`/`parse_gl`(`bank_recon_v2`)→ `merge_statements`/`merge_gl_files`(`bank_recon_merge`)→ `reconcile`(`bank_recon_reconcile`)→ Excel(`bank_gl_excel`/`bank_recon_excel_summary`)。GL PDF 走 `bank_gl_pdf`:先 pdfplumber(`bank_gl_pdf_mrerp`)·失败落 Gemini(`bank_gl_gemini`·**行无运行余额**)。任务存 `bank_recon_v2_task`(gl_opening/detail_json/summary_json/created_at)。

---

## 五、给 Owner 的待办
1. **重启小助手**拿 1.1.9/1.1.10 提速版 → 重推 4 票验「秒级」(②①验收)。
2. **在小助手里选真账套**即可正式推送真客户账套(账套锁早开·三重闸保留)。
3. GL 对账让客户**重新跑**——期初即使再偶发截断,会按运行余额自动纠正。
