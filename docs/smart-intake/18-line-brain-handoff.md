# LINE 记账大脑 · 交接(2026-06-16 收尾 → 下个窗口)

> 本页 = LINE「记账车道」本轮交接。先读 `~/.claude/.../memory/line-ocr-total-and-category-overhaul.md`
> 和 `line-liff-edit-deeplink-complete.md`(全脉络),再读这页(待办 + 注意)。

## ✅ 下一轮(2026-06-16 第二窗口)已交付(prod 真例逐条验过 · 别重做)
- **#4 多图排队**:per-user FIFO 锁(`line_image_ocr.process_line_image_serial`)→ 图按到达顺序
  一张张处理、一张卡发完再下一张;转圈移到轮到该图才发。单图路径不变。(锁进程内 · 覆盖 LINE
  把同批图放进同一 POST events[] 主场景;真机多图顺序待 Zihao 手机验。)
- **#7 收入 vs 支出**:`line_quick_entry.detect_income`(明确收入词【且】无购买动词才判,保守·零误挡
  支出)→ 记账前拦下,回 `exp_income_guide`(不入账·引导网页)。prod 10 收入/12 支出 battery 全对。
- **#8 数量**:`split_qty_price`(图/文共用)→「买2杯咖啡共120」qty=2 单价=60(per-line gross 量化
  吸收·总额不漂,含不整除);多笔 LLM prompt 加 qty 输出、卡片明细显「×N」。prod LLM 实测对。
- **#9 单笔路 date/vendor 平价**:L1 `_extract_vendor`(品牌字典 + 中文「在X买」)+ `_parse_date` 扩
  前天/N天前;大脑 prompt 补 date/vendor 规则。prod L1 + 大脑双验。
- **★大脑救活**:`line_agent.understand` 原用 `best()`=3.5-flash → prod 连续 504 → 大脑形同虚设
  (查账/闲聊/编辑全退哑 L1)。改 `flash()`=2.5-flash → prod 实测 record/query/undo/chat 全答对。
- **#10 /simplify**:抽 `services/line_binding/line_booker`(`book_and_mint` + `ack_key`)三路共用,
  四文件净减;归类/总额/数量 prod 复验不变。**未做(下个窗口·风险较高故缓)**:卡片发射器统一
  (`_reply_card` 收 items/detail override)、`_to_purchase_data` 泛化收 line 列表、category_ai
  `_listing`/`_decode_choice`/prompt 常量抽取——字段形态单/多不同,需带真 booking E2E 再动。
- **坑**:**webhook 偶尔不自动 deploy**(连续两次快推时第二次没触发)→ push 后必查 prod HEAD
  (`ssh root@66.42.49.213 'cd /opt/mrpilot && git rev-parse --short HEAD'`),没跟上就手跑
  `bash git-deploy.sh`(幂等·有健康检查回滚)。

## 0. 本轮已上线(prod 全部真票/真 LLM 验证过,别重做)
- **LIFF 编辑深链**:点卡片「复核/编辑」直达该单可编辑页(治 `liff.state` 包裹坑)。
- **总额修复**(`services/purchase/intake.py`):加油票 qty=积分×price 覆盖正确总额 → 行小计 subtotal 优先 + 多品项与票面对账收敛。7-11/加油/咖啡全对。
- **分类全套**:`category_ai.rule_category`(无歧义高频商户硬规则)+ 2.5-flash(治 3.5-flash 超时返空)+ 科目树扩 **16 大类 73 子类**(`categories.py _PRESET`)+ **全租户 R 重置 10 套账**。
- **文字多项智能拆分**(`category_ai.parse_and_categorize` + `line_expense_multi.do_record_multi`):「电费50 买菜40…」/口语「ฉันซื้อน้ำดื่มราคา10บาท…」→ 一次 LLM 拆干净项目名+额+分类+**日期(解析"昨天/上周三")+卖家(星巴克/7-11)**;金额护栏=必须原文真有。
- **缓存命中出卡**(`line_image_ocr.py`):重发图不再发老 `format_ocr_result_for_line` 纯文字,改重建 ingest 出卡。
- **卡片 UI**:字段/明细 xxs→sm、标签加宽换行防截断、按钮分隔线/footer 收紧(`line_card.py`)。

## 1. 待办功能(Zihao 已拍板"做",按序)
1. **#4 多图排队**:用户一次发多张图 → 排队、一张张处理、出一张卡再下一张,不乱序。LINE 多图 = 多个 webhook event(`routes/line_webhook_routes.py`),现各自异步处理可能交错。需 per-user 串行队列/锁。
2. **#7 收入 vs 支出**:「收到货款500/ขายได้/รับเงิน」是收入,别当费用记进采购。**保守做**:强收入标记 + 无购买动词才拦,回执引导(怕把正常买东西误判挡掉)。注:LINE 暂无销项/收入流(`销项分类后期单独做`),所以先"识别+不误记+引导",别强行建收入单。
3. **#8 数量**:「买2杯咖啡共120」→ qty=2、单价=60。单笔 `parse_expense` 有 `_extract_qty`;多笔 `parse_and_categorize` 可在 prompt 加 qty 输出。
4. **单笔路 date/vendor 平价**:本轮 date/vendor 智能识别只加在**多笔路**(`parse_and_categorge`)。单笔「昨天在星巴克买咖啡60」走的是 `parse_expense`(quick)/`line_agent`(大脑),卖家可能仍空、相对日期可能没解析。需把同等智能补到单笔路(查 `line_agent.understand` 抽不抽 date/vendor;`line_quick_entry._parse_date` 支不支持"昨天")。

## 2. /simplify 收口待办(本轮验证过的路径·下个窗口带验证地做·别盲改)
本轮 4-agent /simplify 发现:**多项路 `do_record_multi` 是单笔路的平行实现**,可抽共享。**我收尾没动**(怕回归刚验好的归类/下单)。下个窗口重构后必须再跑 prod 真例验证归类/总额不变:
- **抽共享 booker**:`do_record_multi` 与 `line_expense._do_record` 的 `grade → book_by_confidence → nonce.mint → 发卡` 编排重复。抽 `book_purchase(cur,tid,ws,*,data,...)→(doc_id,state,token)`,单笔=N=1。
- **统一卡片发射器**:`_reply_card`/`_card_fields_from_draft`(line_expense.py)与 `do_record_multi` 末尾的 ack+result_card 重复;**ack-key 表 `{"posted":...,"dup":...}` 在 3 处**(line_image_ocr/line_expense/line_expense_multi)。让 `_reply_card` 收可选 `items/detail` override 作唯一发卡口。
- **泛化 `_to_purchase_data`** 收 line 列表(单=单元素),消除 multi 路硬编码 `payment_status="paid"`、漏 `doc_no` 的漂移。
- **category_ai 共享小工具**:`_listing(options)` 渲染编号列表 + `_decode_choice(ch,options)→(cid,sid)` 边界查,`suggest_category`/`categorize_items`/`parse_and_categorize` 三处复用;两 prompt(`_BATCH_PROMPT`/`_PARSE_PROMPT`)的分类规则文案重复 → 抽常量(**改 prompt 后必复验归类准确率**)。
- 小:`line_expense_multi._WEB_PURCHASE_URL` 与 `line_expense.py:19` 重声明;`do_record_multi` 解析 cat_name/sub_name 的树遍历可抽 `category_names(tree,cid,sid)`。

## 3. 关键事实/坑(下个窗口必读)
- **prod 诊断/验证手法**(无本地 Vision/Gemini/DB):`ssh root@66.42.49.213` → `cd /opt/mrpilot && set -a && . ./.env && set +a && export GOOGLE_APPLICATION_CREDENTIALS=/etc/pearnly/pearnly-vision-key.json && ./venv/bin/python /dev/stdin <<脚本`(venv 有 psycopg2/pipeline·系统 python 没有)。改 LLM/分类/总额**必这样拿真例验**,别只信单测。
- **push=上线**;改完自跑守门(全量单测 + black + check_imports + check_file_size 硬 500 + check_line_ratchet 净增写 RATCHET-EXEMPT + ai_smell)。**单文件破 500 会被 pre-push 硬拦**(本轮 `line_expense.py` 顶到 500 才拆出 `line_expense_multi.py`)。
- **共享工作目录坑**:别的窗口可能和你同改主树同一批文件(本轮"删待归类"窗口的半成品一度把 ~40 测试拖红挡所有 push)。push 被拦先 `git status` 看是不是别窗口未提交改动 / 跑全量定位红的是不是自己。**别碰别窗口未提交的改动**。
- **100% 抽准不可能**:揉皱热敏票逐行明细(7-11「2 美式 90」读成「12…845」)是 OCR 硬上限;总额/发票号/分类已对,明细那行用户可改。Zihao 接受,但要诚实说。
- **prod LIFF_ID** `2010411313-K4TWQwYo`(env);**Gemini 余额**那把 key 在用(Anthropic 余额 0,大脑用 Gemini)。
- 温度=0 → 同输入确定性;「每次不一样」多是用户每次拍不同照片,非模型随机。

## 4. Zihao 的诉求(基调)
Zihao 非技术,要 LINE 大脑**真智能不智障**,让你"把他没想到的也做好"。本轮已把多项/日期/卖家做智能。继续保持:① 改完 prod 真例验证再说"好了" ② 诚实说做不到的(如逐行 OCR 上限)③ 主动补缺口不只做他点名的。
