# 交接:佛历日期口径全链修复(2026-07-20)

事故起点:冰厂 8 张销项票(一份 PDF),票面 `31/5/2569` 被系统读成 `2559`,4 张带
`2016-05-31` 落库并推进 Express(凭证号 `IV590531-xxx`、税期也错到 2559-05)。

## 根因(逐层实测,不是猜)

1. `route_direct` 页数闸对所有类型一刀切 3 页 → 8 页多票 PDF 被当长表推去 Vision 路。
2. Vision(L1 = Google Cloud Vision)对这批票 **8/8 把 2569 读成 2559**(确定性,三次跑一致)。
3. L2(Gemini)**只收文本不收图**(`layer2_gemini.py` 的 `json_from_text`)→ 唯一信息源是 L1 错文本 → 照抄。
   Gemini 本身没问题:单页/8页一起看图,任何档位包括 flash-lite 都 100% 读对 2569。
4. L3 视觉复读能救,但 prompt 里同摆 Vision 全文 + 上轮 JSON,未点名字段被整段照抄 → 日期 0/4。

★ **查这类问题别拿构造输入当证据**:L3 锚定用手写 5 行简化文本复现不出来(那时它自己读对),
必须喂真实 Vision 全文(960 字符)锚定才够强。第一次实验差点因此下错结论。

## 已上线(主仓,10+ commit,全部 CI 绿)

| commit | 内容 |
|---|---|
| `e3e6603c` | route_direct 分流判据从页数改文档类型(多票 PDF 走直读) |
| `0bbad236` | L3 抗锚定 prompt(独立复读段):实测日期 0/4 → 4/4,金额未被带偏 |
| `79abf4e1` `c3be2438` | 日期合理性闸(早于5年/晚于今天→强制人工),抽独立模块 `services/ocr/date_sanity.py` |
| `4178f7ca` | 日期入口挡佛历年落库(history PUT + workorder recalc 两处后端硬闸) |
| `215bac0e` | 银行两位年 `31/05/69` 不再解成 2069(旧判据 yy<70 当公历 + 死参数 reference) |
| `0ec6ebfa` `df766ebf` `b7b0f581` `17393551` | **日期按票面原样显示与填写**(见下) |
| `41b8f62b`(8929e7c6) | /simplify 收口:回落归数据边界 + SQL 投影下推 + 线程池取消余页 |

**日期按票面显示** = Zihao 拍板"票上什么年就显示什么年"。落地形态:日期字段显示并编辑
`date_raw`(票面那串,泰国印佛历),后端按它反推库里公历 `date`,界面全程不出现公历。
库里 DATE 列仍是公历(税期归属靠 `to_char(doc_date,'YYYY-MM')` 算)。解析在
`core/thai_date.gregorian_from_printed`。四处**可编辑**入口全部真实路径验证过截图为证:
识别记录抽屉 / 录入工作台复核 / 异常抽屉字段区 / 异常列表+副标题。

★ 验前端必须走真实数据入口(真登录→真 API→真点击),**注入 window._results 再调
openDrawer 会绕过 mergeFields,是假验证**——我第一次就栽在这。反代验法:拦本地 bundle,
API 透传 prod;若 prod 未部署新后端,本地起服务跑改的函数+真库,反代把对应 API 指过去。

## 小助手仓(pearnly-companion · 已 clone 到桌面)

- `60d707f` **已保留**:`ISVAT('S').REFNUM` 用真实票号(ภ.พ.30 报税单号,原填自编凭证号)。
- `854e0fa → 1e39934` **已回滚**:`ARTRN.DOCNUM` 改真实票号那个改动。回滚**结论**保留:真实
  Express 的 CDX 索引对含 `/` 的主键怎么处理本地测不出,没验证前不动主键。⚠️ 我当初"止血
  回滚"的**理由是错的**——临时账套 CDX 失败是 `conftest.py` 关了 runner、我脚本没这 patch
  导致,与改动无关。DOCNUM 这条要动,必须先在 Express 测试账套开一张单确认。

## 待办(/simplify 四路审查揪出,本批未动 — 都需要迁移或跨多文件收编)

### P1 · 落 `ocr_history.invoice_date_raw` 列(去规格化)
异常列表现在查询期从 pages 抽 date_raw(`services/exceptions/store.py`),问题:①"主页"判据与
`_extract_summary_fields`(要求该页有 invoice_number/total_amount/seller_name 之一)**不完全一致**,
同一记录理论上可选中不同页;②TOAST 解压成本(已投影下推止血,但没根治)。正解:在
`services/ocr_history/mutations.py::_extract_summary_fields` 加 `invoice_date_raw`,随其余摘要列
一起落库(加列 + 迁移 + 回填),SQL 退回读标量。前端 5 处回落也随之全删。SQL 注释已就地标注。

### P2 · 佛历阈值全站收编到 core/thai_date
现状:`core/thai_date.py` 只接了 2 个调用点,仓库另有十余处独立实现,阈值分 >=2400/>2400/>=2500
三派。**真重复可直接合并**(逐字等价):`summary_import/dates.py::to_ad_year`、`payroll/intake.py::_to_ad_year`、
`knowledge/rules/validity.py`、`field_comparator.py:70`、`importer/coerce.py`(一函数三份)。
两位年真重复:`schemas_invoice.py::_fix_two_digit_year_date`、`purchase/ocr_corrections.py::_year_from_two_digits`。
票面解析真重复:`purchase/ocr_corrections.py::_normalize_date`。
⚠️ 收编前先把 `schemas_invoice.py` 的 2700 上界 + [2000,今年+1] 窗校验语义补进 thai_date,
否则那两处收不进来。docstring 已改成"只是本次路径口径",别再当全站权威。

### P3 · date_sanity 与既有校验合并
`date_sanity.validate_invoice_date` 与 `purchase/ocr_corrections.py::_implausible_doc_date`(同做落窗判定,
窗不同)、`knowledge/rules/validity.py` 的 R-DATE-01(未来日已有规则、有 i18n、前端筛得到)重复。
未来日这条应交给 R-DATE-01,date_sanity 只留"过旧"。

### P4 · AI 控制台复核队列(Zihao 交给别的窗口,主站不碰)
`static/ai/ai-review-suggest-render.js` 用原生 `<input type="date">`,物理装不下票面原文,
且 `ai-review-queue.js:106` 主动拒佛历。三条路(换文本框/标 ค.ศ./保持现状)是产品取舍,未定。

### P5 · _derive_dates_from_printed 下沉(altitude)
`routes/history_routes.py` 在路由层改写 pages,应下沉到 `mutations.py::update_ocr_history_pages`
(与 invoice_date 重算同址),别 mutate 入参。测试也别 import 路由私有函数。

## 事故那 8 张的现状
IV69/00473 已重识别读对 2569;其余在 manual/pending。Express 里的 5 张脏凭证
`IV590531-001~005` 是测试数据,Zihao 说不用动。

## 关键文件/账号
- 生产只读库:`_gemini_key.local/dbq.py` + `_env_lines.txt` 的 DATABASE_URL
- E2E:`pearnly_e2e_1`(404 记录/62 带票面原文,租户 bb0f3981)、`pearnly_e2e_3`(能进 /ai)
- 记忆:`date-pipeline-vision-l1-and-express-docnum.md`
