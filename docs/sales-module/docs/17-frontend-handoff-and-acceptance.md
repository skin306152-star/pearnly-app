# 17 · 销项开票 · 前端交付与验收(按图施工 · 防漏功能/死按钮)

> Zihao 2026-06-06 的硬要求:**每个按钮、每个颜色、每个位置都按草稿做**;不许漏功能、漏按钮,不许"有按钮点了不能用"。本文把"按图施工"变成**可机械检查的闸**——不过闸不算完成。

## 0 · 四个担心 → 四道闸(逐一兜住)
| 担心 | 兜住的闸 |
|---|---|
| 漏功能 / 漏按钮 | §3 全量「按钮→动作→接口」矩阵 + §4 每屏元素清单(逐项打勾,少一个=不过) |
| 有按钮点了不能用(死按钮) | §5 验收 E2E:**真浏览器自动点每个按钮**,断言"触发了正确接口 + 返回非错误 + 无 console 报错";死按钮=红 |
| 前后端路由不通 | §3 每个按钮标了精确 `METHOD /path`;🔧待建接口先建(§6);E2E 真打接口验证 |
| 颜色/位置跑偏 | §2 设计令牌锁死(复用项目现有 `--btn-blue` 等)+ §5 真浏览器截图比对草稿 |

## 1 · 施工唯一基准(不许另起)
- `桌面/Pearnly开票UI预览/app.html` —— 模块工作台(列表/详情/商品/账套+模板/设置弹窗)+ 导航 IA。
- `桌面/Pearnly开票UI预览/index.html` —— 开票向导(5 步 + 输出设置 + 省纸 + 成功面板)。
- `桌面/sales-buyer-block-draft.html` —— 买方状态机逻辑。
> 实现 PO-10 **照这三份**;布局/按钮/文案/四态以草稿为准。草稿与本文冲突时,**以草稿的视觉 + 本文的接口契约为准**。

## 2 · 设计令牌(锁死 · 复用项目现有 · 不许自定义新色)
| 用途 | 值(= 项目 `home-38-buttons.css` / DESIGN_SYSTEM) |
|---|---|
| 主按钮/主色 | `--btn-blue` **#2563EB**(hover #1D4ED8) |
| 危险(作废/删除) | #DC2626 | 成功(已开/已收) #16A34A·#166534 | 强调(充值类) #D97706 |
| 背景 / 卡片 / 边框 | #F4F4F0 / #FFFFFF / #E8E8E3 |
| 文字主 / 次 | #111827 / #6B7280 |
| 侧栏 | 白底 · **当前项黑底 #111 白字**(只导航栏可黑 · 铁律) |
| 正文字号 / 圆角 | 13px / 8–12px |
> 颜色硬闸:`check_ui_consistency.py` D1(禁抽屉·用 .modal)+ D2(按钮黑底基线 0,只导航黑)已在 pre-push,新前端同样受管。

## 3 · 全量「按钮 → 动作 → 接口」矩阵(核心 · 防漏/防死按钮)
图例:✅ 接口已有 · 🔧 待建(§6 先建) · 🖥 纯前端无接口

### 工作台(发票列表)
| 元素 | 动作 | 接口 |
|---|---|---|
| 「开票」(右上) | 进开票向导 | (前端路由) → 见向导 |
| 齿轮「开票设置」(右上) | 打开设置弹窗 | 🔧 `GET /api/sales/settings` |
| 筛选 全部/草稿/已开/已作废 | 过滤列表 | ✅ `GET /api/sales/documents?status=` |
| 搜索框 | 搜号码/客户 | ✅ `GET /api/sales/documents?q=` |
| 汇总卡(本月/金额/草稿/待收) | 统计 | ✅ 同 list 派生(或 🔧 summary) |
| 行点击 / 末列箭头 | 打开详情 | ✅ `GET /api/sales/documents/{id}` |

### 发票详情
| 元素 | 动作 | 接口 |
|---|---|---|
| 下载 PDF 正本 | 下载 | ✅ `GET /api/sales/documents/{id}/pdf` |
| 打印 | 系统打印对话框 | 🖥 用 PDF·无接口 |
| 邮件 | 发买方 | 🔧 `POST /api/sales/documents/{id}/send` (channel=email) |
| LINE | 发买方(**高敏**) | 🔧 `POST …/send` (channel=line) |
| 付款二维码(未收款) | PromptPay QR | 🔧 `GET /api/sales/documents/{id}/promptpay-qr` |
| 复制再开 | 预填新草稿 | ✅ `POST /api/sales/documents`(带源) |
| 红冲 | 开 credit note | ✅ `POST /api/sales/documents/{id}/credit-note` |
| 补开 | 开 debit note | ✅ `POST /api/sales/documents/{id}/debit-note` |
| 转为发票(报价单) | 报价转开票 | 🔧 `POST /api/sales/documents/{id}/convert` |
| 作废 | 作废留痕 | ✅ `POST /api/sales/documents/{id}/void` |

### 开票向导(index.html · 5 步)
| 元素 | 动作 | 接口 |
|---|---|---|
| 卖方(账套)下拉 | 带出卖方 | ✅ `GET /api/sales/sellers` |
| 买方:搜/选客户 | 选已有买方 | ✅ `GET /api/clients?q=` |
| 买方:新建 | 就地建客户 | ✅ `POST /api/clients` |
| 买方税号「验真」 | 校验真伪(绿勾/红叉) | ✅ `POST /api/rd/verify` |
| 公司税号「验真·带出」 | **输税号→自动填名称/地址/分店** | ✅ `POST /api/rd/lookup`(返 17 字段·已有)|
| 商品:**菜单式图卡点选**(像餐厅点单·`docs/06`§A) | 点图卡加一行 | ✅ `GET /api/sales/products`(必带图)· `GET …/products/lookup`(扫码) |
| 加自定义行 | 临时行(不在库) | 🖥 仅本单 |
| 自定义行「☐ 存入商品库」 | 勾选→顺手入库 | ✅ `POST /api/sales/products`(仅勾选时)|
| 存草稿 | 存草稿(不占号) | ✅ `POST /api/sales/documents` / `PATCH …/{id}` |
| 开出发票 | 取号+冻结 | ✅ `POST /api/sales/documents/{id}/issue` |
| 成功面板:下载/打印/发送/QR | 同详情 | ✅/🔧/🖥 同上 |

### 商品管理
| 列表 | ✅ `GET /api/sales/products` | 新增/编辑 | ✅ `POST` / `PATCH /{id}` |
| 删除 | ✅ `DELETE /{id}` | Excel 导入 | ✅ `POST /api/sales/products/import` | 搜索/扫码 | ✅ `?q=` / `/lookup` |

### 客户管理(= 现有页 · 补字段)
| 列表 | ✅ `GET /api/clients` | 新增/编辑(买方类型/分店/promptpay) | ✅ `POST` / `PATCH /api/clients/{id}` |
| 删除 / 批量删 / 导出 | ✅ `DELETE` · `batch-delete` · `{id}/export` |
> ⚠️ 后端需在 clients 上**补字段** `party_type`/`branch`/`promptpay_id`(否则编辑弹窗里的这些控件无处可存 = 死按钮)。

### 账套 · 开票资料
| 选账套 | ✅ `GET /api/sales/sellers` | 保存资料 | ✅ `PUT /api/sales/sellers/{id}` |
| 模板(6 套)/主色/logo/印章/签名/页脚 | 存账套 | ✅ `PUT …`(🔧 需补字段 `template_id`/`brand_color`/`logo_url`/`seal_url`/`signature_url`/`footer_text`/`promptpay_id`) |

### 开票设置(右上齿轮弹窗)
| 连号前缀/重置/起始号 · 审批模式 · 价内外默认 · WHT 档 · 默认语言/纸张/省纸 | 读/存租户默认 | 🔧 `GET`/`PUT /api/sales/settings` |

## 4 · 每屏元素清单(逐项打勾 · 少一个=不过)
施工窗口实现后,对每屏逐条勾:① 元素在不在 ② 位置对不对 ③ 文案 4 语齐 ④ 四态(加载/空/错/正常)⑤ 该调的接口调没调。清单按 §3 矩阵逐行展开,每行一个勾。**矩阵每一行都必须有对应实现 + 对应测试。**

## 5 · 验收 = 真浏览器自动点每个按钮(防死按钮)
**Playwright E2E**(对标项目现有 `tests/e2e/`),对 §3 矩阵**每个按钮**写一条:
1. 点它 → **断言触发了矩阵里那个 `METHOD /path`**(拦截 network),且响应非 4xx/5xx;
2. 全程 **0 console error**;
3. 关键流程跑真账号(开票→详情→红冲/作废)端到端。
> 凡矩阵里有、E2E 没覆盖的按钮 = 视为未交付。"点了没反应/报错" = E2E 红 = 不算完成。
> 视觉:真浏览器 `getComputedStyle` 验主色/位置 + **截图比对 `app.html`/`index.html` 草稿**(项目惯例:grep 类名不算数,必须真浏览器)。

## 6 · 🔧 待建接口清单(前端要调但后端还没有 → 先建,否则必出死按钮)
1. `GET/PUT /api/sales/settings` —— 开票设置存储(§16 §N · `sales_settings` 表)。
2. `POST /api/sales/documents/{id}/send` —— 发送(email 先;line 高敏后)。
3. `GET /api/sales/documents/{id}/promptpay-qr` —— PromptPay(§16 L1)。
4. `POST /api/sales/documents/{id}/convert` —— 报价转发票(§16 L3)。
5. clients 补 `party_type`/`branch`/`promptpay_id`;workspace_clients 补品牌/模板字段。
> **顺序铁律**:这些接口**先于**对应前端按钮做完;前端做某屏前,先确认该屏矩阵里的接口全是 ✅(🔧 的已转 ✅),否则那屏先别做(防做出死按钮)。

## 7 · 完成判定(Definition of Done · 不过不算完成)
一屏"做完"= 全部满足:
- [ ] §4 该屏元素清单逐条勾全(无漏按钮/漏功能)
- [ ] §3 该屏每个按钮都有 E2E 覆盖且全绿(无死按钮 · 路由真通)
- [ ] §2 颜色/位置过真浏览器 `getComputedStyle` + 截图比对草稿
- [ ] i18n 4 语齐(`check_i18n --strict`)+ 四态齐
- [ ] 0 console error · pre-push 6 道守门绿
> 任一未过 = 该屏未交付。验收以"真浏览器点一遍每个按钮 + 比对草稿截图"为准,不看口头汇报。
