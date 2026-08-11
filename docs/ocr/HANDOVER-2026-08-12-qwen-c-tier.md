# 交接 · C·Qwen 引擎档上生产 + 逐入口成本归因(2026-08-12)

一夜四批(qwen 后端 / 成本归因 / 引擎页前端 / simplify 收口),23 笔提交全部上线,
CI 绿,生产 91d4ed5d 健康。本文是欠账账本与运维要点;实测数据与踩坑全档在记忆
`qwen-family-ocr-replacement-trial`。

## 现在生产长什么样

- 引擎档:direct35 / economy(现役全局)/ selfhost / **qwen(新)**;
  qwen 档只对 `overrides_by_account` 名单生效(现仅 skin306152@gmail.com),
  优先级 env > 账号 > 任务 > 全局 > 套餐。
- qwen 档发票页编排(`services/ocr/qwen_direct.py`):flash 直读 + vl-ocr 转写
  → 勾稽 / 现金-找零 / 税号 mod-11 / 转写落地 四类触发器 → 命中过
  `escalation_budget` 闸后升 max 夹心重读。异常整页回落 Vision 路。
- 成本:`GET /api/admin/ocr-engine/costs` 按 入口×单据 实时聚合 `ai_usage`
  (entry_point / doc_type / pages 三列,页数一次性消费槽)。
- 全局键保险:`PARTIAL_MODES={"qwen"}`,写全局/套餐档被 400
  (`ocr_engine.partial_mode_account_only`)。

## 欠账账本(simplify 四角审查,2026-08-12 凌晨)

### A. 高敏亲做(主控方案+验收,机械子步照派)
1. **qwen 编排补 document_type**(解锁全局键的唯一钥匙):两臂 prompt +
   `to_invoice_fields` 都出该字段,金标 51 格复测不掉分,ABB/贷记单专项加考,
   过了才把 qwen 移出 PARTIAL_MODES。
2. `_PageSlot` 页数不变量下沉落账层(用 trace_id/request_id 去重,写入成功才算
   消费;现实现取值与写入不原子,DB 抖动会丢分母)。

### B. 主控先定方案,拆机械子步派 worker
3. direct_read 的 qwen 分流改「档位能力注册表」(MODE_PAGE_READER 式声明,
   消 `_qwen_active()` 三处特判;顺手把 DirectReadFallback 挪 contracts 解惰性 import 环)。
4. routing_matrix 后端分支泛化(provider 公开 model_for_tier 约定,矩阵不再
   import provider 私有名)。
5. `submit_ctx` 并发助手收 6 处 `copy_context().run` 样板 + 机械闸
   (裸 submit/map 即红)。
6. 任务级覆写补 partial 档保险(`overrides_by_task.invoice=qwen` 与全局同风险,
   现在只挡了全局与套餐两处)。

### C. 直派 DeepSeek worker(自包含工单,并行)
7. 泰/英月份名表四合一收进 `core/thai_date.gregorian_from_printed`
   (qwen_direct / bank_recon_utils / summary_import / archive_tree)。
8. provider 重试→ProviderOutcome 循环三合一下沉 http_common(qwen/selfhost/openai)。
9. `_base`/`_headers` 与 Bearer 头三份拷贝收 http_common。
10. 前端 `_t`/`_label`/`_stateBox` 双文件重复收拢单一 owner。
11. admin 四态样式三套(.eng-state/.adm-empty/.pu-*)合一,重试按钮进公共层。
12. ECharts 收编 admin.js 旧手写 SVG 成本趋势图,配色进 admin-viz.css 令牌。
13. 死代码:/api/admin/ocr-engine/metrics + store.get_ocr_engine_metrics
    (新面板已替代,仅契约测试在养)——删或重挂,二选一。
14. alembic 0100 与 ensure 的 4 条 DDL 去重(`_ATTRIBUTION_MIGRATIONS` 单源)。
15. `ensure_ai_usage_table` 挪出请求路径进启动自检(首请求 DDL 锁风险)。
16. 语言切换只重画不重查(admin-engine-cost 暴露 rerender;顺手治
    `_loadPolicy` 刷新覆盖灰度区未保存编辑)。
17. 售价 1.5 铢改走后端计费单源(costs 响应带 price_thb_per_page,
    前端/i18n 文案吃它;现在三处硬编,调价即说谎)。
18. 引擎三 JS(36KB)改 _renderEnginePage 按需注入(七页只有一页用)。
19. echarts 懒加载登记 check_cachebust 懒加载闸(升级换文件名那天会漏)。
20. 验收脚本 `_admin_engine_ui_verify.cjs` 的 chk/summary 改用 `_verify_shared.cjs`。
21. i18n 死键清理(adm-eng-doc-voucher / generated_table 等 4 条无写入方)。
22. fileconv 页数口径(现记 entry 不记页,cost_per_page 显「—」;若要页数需
    在转换层数真实页)。

### 运维要点
- 生产 QWEN_OCR_URL/KEY 在 /opt/mrpilot/.env(备份 .env.bak-keyswap);
  key 只认 ws-8kzdbt2a1dukixgg 专属域名。
- LINE webhook 与独立 worker 无登录态,吃不到账号灰度(回落全局档),
  全局解锁前属预期行为。
- 未归因行 = 归因上线前历史 + 无打点调用(line_dms 身份证入口待隔壁窗口加 wrap)。
