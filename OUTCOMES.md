# 📋 Zihao 待办结果跟踪(OUTCOMES)· 单一权威

> **这张表跟踪「Zihao 真正要的、看得见的结果」**——验收标准 = **结果做对了**(窗口自检确认 / 必要时 Zihao 确认),**不是**「checker 绿了 / 测试加了多少 / 某一步 ship 了」。
>
> **为什么有这张表**:自主窗口惯于「做完最容易那一刀就宣布完成,把需要判断/看美观的推给『待 attended』→ 然后永远没人做」。结果每个窗口都"成功",但 Zihao 要的结果不闭环。本表把「结果」而非「步骤」作为唯一完成定义。
>
> **铁律**:
> 1. **窗口改完【自己去 UI 看 / 跑字段对比】确认对了,再下一步**——不是每步等 Zihao 验收。自检方式见每行。
> 2. **只在「改对了但确实拿不准」时才问 Zihao**(如某 tab 用哪个变体看着别扭、L3 关思考少数复杂票)。
> 3. **主控(指挥窗口)持有本表 · 盯到每项 Zihao 看得见地完成 · 需要 Zihao 的部分主动端到面前 · 绝不让任何一项烂在 STATE 里。**
> 4. 每完成一项:从「进行中」移到「已完成」并记 commit。

---

## 🔵 进行中

| # | 结果(Zihao 要的) | 设计 | 执行 | 窗口【自检方式】(自己确认·不烦 Zihao) | 窗口 | 状态 |
|---|---|---|---|---|---|---|
| 1 | **全站黑按钮 → 统一变体**(design-preview/ui-consistency-audit.md A 段:收编 30+ 杂牌类到 btn-primary/secondary/ghost/danger/toggle) | ✅ | ⬜ | Playwright 导航到该页 → 截该按钮区 → **窗口读截图肉眼核**:蓝/对应变体/非黑、可点、无 console error。自检过才下一刀。 | B | ⏸️窗口B暂停·主控接管按钮统一(2026-05-30)。窗口B已收编+源级核(prod origin·residual=0·钩子保留·home-38已生效):bank-filter`1288ecd`/异常栏批量栏`3e17cf8`/erp-exc行内重试+ERP弹窗`8c40700`(删6CSS)/异常栏OCR重试`000c146`(删2CSS)/发票记录批量栏图标→btn-icon`d30cd62`(origin源级核3处)。⚠️像素蓝待复核。剩余主控做:email-interval-btn(class钩子保留)/history-pager-btns(查是否已达标)/erp-map-show-advanced-btn(expander慎)/tc-btn系/11内联style/审计B删上传图片/审计C异常栏批量栏选中才现。⚠️曾误报模块4及不存在 hash(4d75847/2150bbf/4cebb67)均已撤回·实际落地=上列5项(真commit)。 |
| 2 | **删桌面「上传图片」按钮**(手机端保留拍照入口)(审计 B 段·home.html L466-481) | ✅ | ⬜ | 截图核:桌面视口无该按钮、手机视口(@media)仍有。 | B | 待跑 |
| 3 | **异常栏批量栏「选中才显示」**(照发票记录 history-batch-bar)(审计 C 段) | ✅ | ⬜ | E2E:未勾选=批量栏隐藏、勾选=出现。窗口自跑自验。 | B | 待跑 |
| 4 | **OCR 提速**(留底后台 + 多页并行 + 图片压缩[A/B] + L3 关思考[Phase2]) | ✅ | 🔵 | 每步:同批真发票(U盘 D:\测试PDF\D:\测试图片)跑【改前 vs 改后字段逐项 diff 必须一致】+ 延迟下降 + 测试账号 E2E。字段不一致=自己查根因修,不上线。 | A | 🔵Step0 观测✅(8ecb33b)· **Step1 PDF 留底后台化✅**(b3c6446+asyncio修5453e23·留底挪出响应主路径→后台 to_thread 生成+回填·新 DAL update_ocr_history_pdf_storage tenant/user锁)· **真账号 E2E 验过**:INV2026030003 字段全对(5070+354.90=5424.90·VAT7%)+ has_pdf 2s 内回填 True ✅ → **Step2 多页 PDF 并行✅**(23cad11·_process_pages·pattern_memory is None+多页 ThreadPoolExecutor(4)·as_completed 按 page_number 还原页序·串行守卫·单页逻辑不改)·单测证 parallel==serial+真并发·真账号 E2E:INV2026030004/05 字段全对 VAT7%·页序[1,2]·2页 5.5-6.2s(vs 串行3页13s)✅ → ⏸️**Step3 图片压缩卡料**:U盘所有图(微信 12 张全 ≤1707px·扫描件=PDF 非图)无 >2400px 图 → 2400px cap 对现有测试集是 no-op·无法按 directive 做 A/B(且现实收益仅对全分辨率相机直传 >2400px·微信/截图类预压缩的不受益也不受影响)→ 需 Zihao 给 1-2 张全分辨率(3000px+)泰票照片做 A/B·或缓做。Step4 L3 关思考=Phase2(需 google-genai SDK 迁移·高风险·待 Phase1 稳后+Zihao 点头)。**✅ Phase1 主要提速(留底后台+多页并行)已上线真账号验过** |

## ⚪ 待排(Zihao 说暂不在本次)

| # | 结果 | 备注 |
|---|---|---|
| 5 | 浅蓝框统一黑(旧设计语言没删干净) | Zihao:不在本次任务内,记着,以后排。 |

## ✅ 已完成

| # | 结果 | commit | 验收 |
|---|---|---|---|
| — | 主按钮蓝色标准 CSS(home-38-buttons.css) | 0c2fc9e | 立了标准(但全站收编未做 → 见进行中 #1) |
| — | UI 一致性检查器 + 设计审计 + design-preview 入库 | 8d32b38 / 52a40b7 | ✅ |
| — | 三层安全防护(pre-push 闸 + 服务器自动回滚 + 闭环) | 7f61be5 / 6e10b72 | ✅ 生产验证 |
