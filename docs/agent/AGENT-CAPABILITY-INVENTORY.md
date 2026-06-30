# Pearnly Agent · 能力总清单（完整 · 从代码机械扒取 · 防漏的单一事实源）

> 目的：Agent（自然语言大脑）能做什么 = 这张清单。**清单从代码自动扒取，不靠人记**。
> 规模：**497 个 API 入口 / 87 个功能区**（2026-06-30 `grep` 实测）。
> 配套防漏机制见末尾「自动核对闸」——任何入口未分类 = 闸红，杜绝"漏了最后才发现"。

## 分类口径（4 桶）
- **A 进·只读**：查/看/算，不改任何数据 → 最安全，第一批接。
- **B 进·要确认**：动账/动钱/写库（推票、建单、改字段、跑对账落库）→ 接，但每次先确认 + 走现有计费/幂等闸。
- **C 不进·App 专属**：POS 收银、团队/角色、端点/映射配置等 → 留在 App 里点，对话不做（独立前端或低频高敏配置）。
- **D 不进·系统/安全**：登录、超管后台、LINE 渠道本身、页面服务、机器对机器 → 不是"用户能力"，永不进。

---

## A · 进·只读（先上，安全）
| 功能区 | 文件 | 入口数 | 说明 |
|---|---|---|---|
| 识别记录·查 | history_routes（读部分） | (13中读) | 列表/详情/PDF/页图 |
| 余额/额度 | billing_credits_routes | 5 | 余额、用量 |
| 账单记录 | billing_records_routes | 3 | |
| 报表 | report_routes | 4 | |
| 账本/总账 | accounting_books_routes | 5 | |
| 库存报表 | inventory_report_routes | 1 | |
| 推送列表/状态 | erp_listing_routes / erp_export_routes / erp_express_account_routes | 5/1/2 | 查推没推、账套 |
| 知识问答 | knowledge_ask_routes / knowledge_risk_routes | 3/2 | 问答、风险检查 |
| 通知 | notification_routes | 6 | |
| 税号查询(RD) | rd_routes | 4 | 税局核验·很适合做工具 |
| 我的信息/元数据 | me_routes / auth_me_routes(读) / meta_aliases_routes | 3/3/3 | |
| 客户/主体·查 | clients_routes(读) | (6中读) | |
| 工作区/账套·查 | workspace_routes(读) / tenant_routes(读) | (读) | |
| OCR 导出 | ocr_export_routes | 4 | |

## B · 进·要确认（动账动钱，带确认闸 + 计费/幂等）
| 功能区 | 文件 | 入口数 | 说明 |
|---|---|---|---|
| **OCR 识别/进票** | ocr_recognize_routes / ocr_jobs_routes / purchase_intake_routes / uploads_routes / email_ingest_routes | 1/2/2/2/6 | 识别=花钱；落库=确认 |
| **身份证/DMS** | dms_routes | 4 | |
| **识别记录·改/删/落库** | history_routes（写部分） | (13中写) | 改字段/删/commit/绑主体 |
| **推 ERP/Express** ★ | erp_push_log_routes / exceptions_routes | 9/8 | 推送、重推、修异常 |
| **对账** ★ | recon_routes / recon_jobs_routes / bank_recon_routes / accounting_bank_routes / vat_excel_routes / vat_excel_tasks_routes | 9/6/9/11/4/4 | 提交/跑/落库 |
| **销售/开票** | sales_routes / sales_send_routes / sales_seller_routes | 15/2/3 | 建单=确认 |
| **采购** ★ | purchase_routes | 19 | |
| **会计/报税** | accounting_routes / tax_routes | 20/11 | |
| **商品/科目/库存** | products_routes / categories_routes / inventory_routes | 11/1/6 | |
| **知识库·写** | knowledge_routes / knowledge_rules_routes | 7/4 | 录入/改规则 |
| **导入** | import_routes | 3 | |
| **订阅/充值** | billing_subscription_routes / billing_topup_routes | 3/6 | 钱·确认或留App |
| **客户/主体·建改** | clients_routes(写) | (写) | |
| **账套切换** | workspace_routes(写) / tenant_routes(写) | (写) | 切当前账套 |

## C · 不进·App 专属（留在 App 里做）
| 功能区 | 文件 | 入口数 | 为什么不进 |
|---|---|---|---|
| POS 收银台 | pos_sales_routes / pos_restaurant_routes / pos_restaurant_admin_routes / pos_payment_routes / pos_modules_routes / pos_report_routes | 17/14/8/2/4/1 | 独立触屏前端，非对话场景 |
| 团队/角色/邀请 | console_team_routes / console_roles_routes / console_invite_routes | 9/5/7 | 高敏权限·低频·留 App |
| ERP 端点/映射配置 | erp_endpoints_routes / erp_mappings_routes / purchase_config_routes / sales_settings_routes / settings_routes / modules_routes | 7/12/10/2/5/3 | 配置类·低频·留 App（其中"查"可选进 A） |

## D · 不进·系统/安全（永不进）
| 功能区 | 文件 | 入口数 | 为什么 |
|---|---|---|---|
| 登录/账号/OAuth | login_routes / auth_password_routes / auth_email_code_routes / oauth_routes / oauth_line_routes / google_oauth_routes / pos_auth_routes | 3/3/2/2/3/5/10 | 安全主路径 |
| 超管后台 | admin_*（logs/cost/diagnostics/users_query/users_mutation/migration） / auth_admin_routes / auth_admin_risk_routes | 4/10/8/6/9/7/4/4 | owner-only |
| LINE 渠道本身 | line_webhook / line_binding / line_liff / line_card_image / line_account_merge | 1/4/3/1/2 | 这是入口管道，不是能力 |
| 页面/安装包/机器通信 | pages_routes / companion_installer_routes / erp_agent | 19/1/4 | serve HTML / 下载 / 小助手对接 |

---

## 防漏机制 · 自动核对闸（关键 · 治"靠人记会漏"）
1. **总清单从代码生成**：脚本 `grep` 所有 `@router.{get,post,...}` → 得到全部 497 入口（本文件即首版快照）。
2. **一张登记表**：每个入口标 `A|B|C|D`（或更细的 `tool_id`）。
3. **CI 闸**：跑核对脚本 → 列出"代码里有、登记表里没分类"的入口 → 有 = 闸红。
   - 新加功能(新路由) → 自动出现在"未分类"里 → 提醒"这条还没决定进不进 Agent"。
   - 已分 A/B 但还没接进 Agent 的 → 标"待接"，看得见进度，不藏。
4. **安全降级**：未接的能力，Agent 答"这个暂时不能在对话里做，请到 App 操作" → 产品照常，不坏。

→ 结论：**漏不了（核对闸红）、漏了不坏（安全降级）、进度看得见（待接清单）。** 不会有"最后去补去修"的折腾。

## 落地顺序建议
1. 先接 **A 桶（只读）** 全部 → 安全、快见效、把"读真实数据再引导"的底座搭好。
2. 再接 **B 桶（写）** ，按价值排：推ERP/对账/OCR进票/采购销售 优先；每条带确认+计费+幂等闸；动手前单独报方案。
3. **C/D 桶** 维持不进；C 里的"查"按需挪进 A。
