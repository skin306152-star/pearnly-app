# UI 界面层全清单(一个都不许漏)· 2026-06-09 · 代码穷举

> 痛点:自动截图只截顶层屏(~25),弹窗/抽屉/嵌套(~60)是"点进去才看得到"的盲区,反复被漏。
> 用法:设计评审 + 迁移**逐项打勾**;每个层都要:截图看设计 → 判合不合理 → 改 → 保真闸 + 暗夜 + 缩放。

## L0 · 顶层屏(~25)
dashboard · ocr上传识别 · history识别记录 · reconcile对账 · automation · sales-invoices销售工作台 · sales-account账套 · sales-products商品 · sales-report销售报表 · receivables应收 · clients客户 · purchase进项主屏 · purchase-inbox待归类 · purchase-suppliers供应商 · purchase-settings采购设置 · vouchers · inventory库存 · pos-onboarding · pos-cashiers收银员 · pos-tables桌台 · pos-payment收款设置 · knowledge知识库 · exceptions异常 · integrations集成 · settings设置(弹窗形态)

## L1 · 弹窗 modal(~30 · 点按钮才弹)
- **全局**:账套选择 `workspace-switcher`(ws-modal,到处弹)· 设置弹窗 `settings-panels`(多 tab)· 确认/删除 `confirm-modals-html`/`confirm-modal`/`pearnly-confirm` · 帮助 `modal-help`/`help-modal` · 新通知 `modal-notif-new` · 命令面板 Ctrl+K `openCmdk`
- **OCR/进项**:相机贴士 `camera-tips-html` · 重复票 `ocr-duplicate-dialog` · 付款/匹配商品/LINE费用 `purchase-modals` · 库存入库/盘点 `inventory-modals`
- **销项**:单据详情+动作 `sales-detail` · 商品增删 `sales-products` · 开票设置 `sales-settings` · 开票向导(多步)`sales-wizard`
- **客户/归档**:客户编辑 `modal-client-edit` · 分配客户 `modal-assign-clients` · 归档token/rule `modal-archive-token`/`modal-archive-rule`
- **知识库**:`knowledge-api`/`knowledge-ask`/`knowledge-info`/`knowledge-sources` 各弹窗
- **ERP/集成**:端点 `endpoint-modal`/`erp-endpoints` · 异常编辑 `erp-exceptions-edit` · MR.ERP DMS连接 `erp-mrerp-dms-connect` · onboard `erp-onboard` · 邮箱 `email-modal`/`line-email-modal` · RD同步 `openRdSyncModal`
- **POS**:区域/桌台对话框 `openAreaDialog`/`openTableDialog` · 加员工 `showAddEmployeeModal`
- **账户**:强制改密 `force-pw`/`openForgotCurrentPwModal` · 银行客户选择 `bank-client-picker`

## L1 · 抽屉 drawer(~12 · 侧拉)
- **识别结果编辑抽屉** `ocr-results`+`ocr-fields`+`ocr-push`(点识别记录打开 · 核心高频)
- 历史抽屉 `history-drawer` · 异常抽屉 `exceptions-drawer`(+render)· 通知抽屉 `notifications`
- 对账:`bank-recon-drawer`/`recon-drawer`/`bank-recon-detail` · 候选抽屉 `bank-cand-drawer`
- 集成配置抽屉 `integration-drawer`/`integration-config` · LINE面板 `line-panel` · 客户抽屉 `clients`/`clients-buyer` · Xero推送 `erp-xero-push`

## L2/L3 · 嵌套(弹窗里的弹窗 / 抽屉里的弹窗 · 最易漏)
- 识别结果抽屉 →(匹配商品 / 确认入账 / 重复票)弹窗
- 开票向导 →(客户编辑 / 商品选择 / 纸张语言)弹窗
- 客户抽屉 →(买方编辑 / 分配客户)弹窗
- 异常抽屉 →(异常编辑 `erp-exceptions-edit`)弹窗
- 对账抽屉 →(候选选择 / 银行客户选择)弹窗
- ERP 端点弹窗 →(凭据 / onboard)弹窗
- 进项录入 →(付款 / 匹配 / 生成替代收据)弹窗
- 设置弹窗 →(改密 / 各子 tab)

## L0.5 · 流程态 / 动作态 / 系统生成文件(最易漏 · 2026-06-10 Zihao 追加)
> 屏不是静态的:上传→处理→结果→动作,每一步 + 成功态/错误态 + 系统吐出的文件,都要逐个看设计、统一。

**A. 主流程每一步(逐步截图看设计)**
- **OCR 上传识别**:① 上传区(空 / 拖拽悬停 / 上传中带进度)② 识别中(骨架/loading)③ 识别结果(列表 + 单票)④ 结果动作(编辑 / 导出 Excel / 自定义模板 / 推 ERP / 删)⑤ **成功态**(toast/面板)⑥ **错误态**:坏图 422 / 余额不足 402 / 引擎错 500 / 非发票 / 同页多票 / 重复票
- **开票向导**:5 步每步 + 每步校验错 + 开出成功(连号+PDF)+ 合规拦截提示
- **对账**:上传双文件(空/上传中)→ 对账中 → 结果(匹配/差额红)→ 导出 → 成功/失败
- **进项录入**:存草稿 / 确认入账 → 成功 / 校验错 / 重复票拦截
- **付款弹窗**:填 → 提交中 → 成功 / 失败
- **ERP 推送**:推送中 → 成功弹窗 / 重试 / 失败日志
- **LINE 一句话记费用 / 拍票**:每步回执

**B. 四态(每个数据视图都要)**:加载(骨架)/ 空 / 错误(带重试)/ 已载入。
**C. 动作三态(每个按钮)**:成功(toast/inline)/ 失败(具体错+下一步)/ 进行中(禁连点+loading)。
**D. 系统生成的文件(版式也要统一·别忘)**:合规发票 PDF(样票)· 替代收据 PDF · 税票 · 热敏小票 · 导出 Excel/CSV 版式 · 扣缴/凭据 PDF。这些是"呈现给用户的输出",同样按品牌/字体/排版统一。

## 评审/迁移要求(每个层)
每层逐项:① 截图看设计合不合理(布局/层次/位置/密度/空间)② 对标 DESIGN_SYSTEM 改 ③ 保真闸 + 暗夜 + 67/100/150%缩放 ④ **嵌套层必须真的点进去看**(抽屉里再开弹窗、弹窗里再开弹窗)。
> ⚠ 自动截图只覆盖 L0;L1/L2/L3 必须**真浏览器点开**或**模板单独渲染**才看得到。漏掉这 60 个 = "改不完/不一致"的真因。
