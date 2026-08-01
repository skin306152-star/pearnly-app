# 交接单 · POS 条码扫码(2026-08-01 上线)

> 六轮施工 + 一轮 /simplify 收口。**已上线**:`master = b4515b22` · CI conclusion=success ·
> 线上 `/api/version = 12044201`。下一个窗口从 §3 开始读。

---

## §0 一句话状态

三处扫码(建品 / 入库 / 收银台)上线,条码枪与手机摄像头共用一套地基。
**一条没有结论的风险悬着**(见 §4 第一顺位),在它有结论前**不要对外说「去重验过了」**。

---

## §1 交付了什么

三件功能,每件都同时吃条码枪和手机摄像头:

- **新增商品** — 扫码填条码 + 撞码当场拦(指出这个码已经是哪个商品的,避免建出两个同码
  商品让收银台永远扫错货)
- **入库** — 扫码加行,同码连扫 +1,**批次品另起一行**(不合并 —— 否则第二箱的效期被第一箱
  吃掉,FEFO 按错日期排)
- **收银台** — 扫码取件,箱码按箱算钱、按箱扣库存

**地基**:`static/scan/` 一套引擎两个 SPA 共用。安卓走系统原生 `BarcodeDetector`,iPhone
懒加载 vendored ZXing(1.2MB,安卓一个字节都不下);条码枪走键盘楔子,判据用
`KeyboardEvent.timeStamp` 而非主线程时钟(主线程一卡,真枪会被误判成人手)。

**六轮的主线其实只有一件事**:让「引擎判对了但店员看不见」的静默失败全部出声。

---

## §2 明确不做 / 做不到

| | 状态 |
|---|---|
| 箱码 / 单位维护界面 | **Zihao 拍板不做**。后端能力、唯一索引、僵尸码释放全部留着,以后接是接线的事 |
| 开票向导扫码 | **Zihao 拍板不做**(「销售」只指收银台) |
| 新增商品自动带出名字价格 | **物理做不到** —— EAN-13 本身不含这些。产品内文案已四语照实说明。Odoo 社区版写了同样的承诺也没实现 |

---

## §3 待办(按该做的顺序)

### 3.1 后端条码匹配规则抽成一份 — 性价比最高
`services/sales/products.py:286` 的 `_find_by_barcode` 与 `services/pos/catalog.py:154` 的
`product_by_barcode` 是**逐行同构**的三查询算法,只有 SELECT 列不同。四路 review 有三路
独立点名。

**为什么急**:两处 docstring 自己写着「两边曾分叉……绿字骗人还放行重码」—— 那是六轮里
真出过的 P1。这次用**复制**重新收敛,下次改还是同一个失败模式。下一次改已经能看见:
`products.py:279` 写了「跨表撞码(A 的单位码 = B 的主码)两条索引都表达不了,靠 find_by
两表都查在 UX 层兜」。

**做法**:抽 `resolve_barcode(cur, *, tenant_id, workspace_client_id, code, cols)` 进
`services/products/barcode.py`。**半径**:2 个调用点 + 1 新模块 + 2 个测试。不碰 DB、不碰
前端、不重建 dist。

### 3.2 启动路径加「已经做过了」探针 — 风险最高
新增的启动期 schema 双跑没有探针,每个 worker 每次开机付一遍:
`ensure_unit_visibility_column` 全表 hash join · `barcode_conflicts` 两条无索引
`GROUP BY btrim()` seq scan · 两条 `SET barcode=nullif(btrim())` 再各扫一遍 ·
`ALTER TABLE products DROP DEFAULT/DROP NOT NULL`(**列早就是那状态照样发、照样拿
ACCESS EXCLUSIVE**)· `CREATE UNIQUE INDEX` 非 CONCURRENTLY。

这整段被 `services/startup_lock.py` 跨 worker 串行,挡在服务可用前面。部署撞上一笔长事务
会堵住 products 的锁队列。

**现成范式**:`services/startup.py:31` 的 `_flip_auto_book_default_on` 读 `pg_attrdef`、
已生效直接 return。

> ⚠️ **动手前先拍一件事**:`ensure_unit_visibility_column` 里那条回填,是 0093 的一次性
> 修复,还是当「持续自愈 `product_active` 漂移」用的?若是后者,跳过就改行为 —— 那它该进
> 定时任务,不该挡在 readiness 前面。

### 3.3 类型声明收敛 + 它引出的真缺陷
`window.PearnlyScanCamera` / `PearnlyScanWedge` 被手写了 **5 份**接口,已经漂:
`ScanError` 一处有必填 `detail` 一处没有 · `CameraApi.create` 一边全类型一边
`Record<string,unknown>` · **wedge 的 `register` 在 sales 侧少声明了第三个参数**。

后果在 `src/home/sales-products-scan.ts:322`:拿不到 `info.before`,只好字符串手术反推
```ts
const before = now.endsWith(code) ? now.slice(0, -code.length) : now;
```
走到 `: now` 那一支时 before = 整框内容,还原就还原错了。而 wedge 在字符落进 DOM **之前**
拍的快照才准,入库侧(`inventory-scan.ts:360`)用的正是它。

`src/types/globals.d.ts`(421 行,专收这类全局)目前**零** `Pearnly*` 声明。
**半径**:globals.d.ts 加一段 + 4 文件删本地接口 + tsc + dist 重建。

### 3.4 离线扫主码那段修复是照 mock 写的,对真数据是死代码
`static/pos/pos-data.js:391` 那个循环 + `filterCatalog` 里的 `p.barcode` 分支 ——
`services/pos/catalog.py:73` 的 `_row_to_item` **从来不发顶层 `barcode`**,而离线快照就是
`/api/pos/products` 的 items 原样缓存,所以缓存里也没有。**只有 `MOCK_PRODUCTS`
(pos-data.js:228)才有那个字段。**

它注释里写的场景(「少这一遍,离线扫主码会被说成本机目录里没有」)**今天照旧成立**。
撞的正是记忆里 `verify-target-must-be-real-content` 那条。

### 3.5 一道闸名字比它做的事大
`tests/unit/test_scan_assets.py:223` 的 `test_error_keys_and_ui_keys_share_one_namespace`
只断言 `len(keys) >= 8`。而 `bscan.*` **不是**共享命名空间 —— 两本字典措辞已分叉
(`bscan.notfound` 一本是「扫到 {code},但这个条码还没建成商品」、另一本是「没有条码
{code} 的商品」)。加第 9 个错误码闸照绿,而其中一个 SPA 会把原始键印给店员。
**改法**:从 `scan-errors.js` 读出 `ERROR_KEYS`,断言每个键在**两本字典的四种语言里都在**。

### 3.6 结构性的(半径较大,建议单独排)
- **失败清单两份状态机**(`static/pos/pos-scan-fails.js` vs `src/home/inventory-scan-ui.ts`)
  —— 连那条 14.1 秒真浏览器实测换来的豁免规则都写了两份,字段名还不一样(`addOne` vs
  `dup`)。且 POS 存 i18n 键能跟随切语言,home 侧存**已翻好的 HTML** 且没进
  `src/home/core-boot.ts` 的 `applyLang` 花名册 —— POS 那份注释里写的「标题泰文、正文中文」
  失败模式,另一份还没修。**落点**:下沉成 `static/scan/scan-fails.js`,挂进
  `scripts/build-home-js.mjs` 的 `SCAN_RESIDENT`(两个 bundle 都进得去,楔子就是这么共享的)
- **i18n key 映射抄 4 份**且已漂(`pos-scan.js:22` 那份缺 fallback)。根因是分层:
  `ERROR_KEYS` 在懒加载的 `dist/scan.js` 里,而 `unsupportedReason()` 必须首屏回答 →
  该把表挪进常驻的 `scan-loader.js`
- **POS 目录信封把「单位」建模成不完整的** → 三处特例来补(其中一处就是 3.4)。让
  `units` 永远发基本单位那一行,三处特例自己消失。**但这会改货架瓷砖显示价,要单独一批**
- **「没挂牌价不许卖」两份后端实现判的不是同一个东西** —— `services/pos/sale.py:142`
  判解析后的 `list_price`,`services/pos/restaurant/sessions.py:109` 只看
  `prod["unit_price"]` 从不看 `product_units.price`,且 `unit_factor` 硬编码为 1
- POS 货架瓷砖 units 无价时仍回落 `{price:'0'}` 印 `฿0.00`,跟后端新加的零元闸口径不一致
- `services/products/units.py:179` 的 `create_unit`:`RETURNING` 带的是 UPDATE 前的旧值
  (今天没出事只因为 `product_active` 不在 `_UCOLS` 里)
- 按条码取件走 2~3 次远程往返,一条 UNION ALL 就够(Supabase pooler 每次 execute 一个 RTT,
  这是热路径:收银台每件货一次)
- 两处 `ensureStyle` 收敛成 `acct-common.ts` 的 `injectStyle`(全仓已 11 份)——
  ⚠️ **不是纯替换**:`tests/unit` 的 node harness stub 掉了 `acct-common`,直接 import 会
  `TypeError`,13 条测试当场红。真半径是「两个文件 + harness」

### 3.7 存量(与扫码无关,顺带发现)
- `sales_document_lines.unit_price` 是 `NOT NULL DEFAULT 0` → 开票草稿往返会把「没设价」
  洗成 0。**这是 ฿0 那条 P0 最后一段尾巴**,要 schema 迁移
- `/pos` 老 PWA 外壳现在是**老板登录页**,且没有东西接回 `/cashier` → 老收银设备联网重装
  SW 后打不开收银台
- `sale_caps._has_price_override` 在挂牌价 None 时不判改价
- 入库页 390 宽横向溢出(线上 `d7b34f56` 同款,实测证明是存量)

### 3.8 要 Zihao 拍板的口径
**4 语 release_notes 这批没写** —— 不是漏了:`/api/version` 的 `release_notes` payload
已随「更新通知横幅下线」退役(`routes/meta_aliases_routes.py:30` 明写不再返回)。要么认
「机制已退役、本条不适用」,要么另找一个用户看得见的更新说明位置。

### 3.9 收尾杂项
- worktree `.claude/worktrees/pos-barcode-scan` 与分支 `feat/pos-barcode-scan` 还在,
  代码已进 master,可以清
- POS 搜索框扫码那条路完全没测

---

## §4 真机验(只有 Zihao 能做)

### 🔴 第一顺位 — 可能错钱,而且**没有结论**

**最便宜那台安卓机,举一箱可乐在镜头前不动 10 秒,看购物车是不是只加 1 件。**

六轮终审原话:*「既不能判真 bug 也不能判 harness 噪音,现状是没结论。」* 它在压满负载的
机器上出现过双计次(查码 2 次、车 2 件)。机制上说得通:去重是「墙钟 `clearAfterMs` +
连续失败次数 `clearAfterMisses`」两把尺子 AND,解码越慢两个条件越容易同时满足,同一件货
就被当成「拿走又换了一件」。触发素材是「条码只有一半的帧读得出」—— 也就是**反光、斜拿
时的常态**,而真实目标机就是便宜安卓机。

2026-08-01 收工时 26 支 E2E 串行重跑(机器空闲)它绿了 —— **这不改变结论**,因为便宜安卓机
的解码速度就相当于「机器被压住」。

**在这条有结论之前,不要对外说「去重已经验过了」。**

配套:故意让条码反光、或斜着拿,重复同一动作。

**2026-08-01 补:同一个判据往反方向也会偏。** 当天改计费文案时机器被压住,
`_inv_guards_verify.cjs` 的 `secondBoxAboveFloor` 红了一次:间隔 2.0 秒(远在去重地板之上)
的第二件货,**数量记对了,却同时弹出「刚才这一下当成同一件了」**。空闲重跑 9/9 全绿,所以
不是代码回归 —— 但它证明慢解码时**去重会先抑制一次不该抑制的扫描**。也就是说真机上要看
两个方向:① 同一件被记两次(钱多收)② 真实的第二件被抑制(钱少收 / 少发货)。两次都在
「解码慢」这一个根因上,别只验一边就收工。

### 🟡 功能可用性
- **iPhone**:iOS 走 ZXing 兜底路。重点看 **video 会不会被 Safari 抢成全屏播放器** ——
  代码加了 `playsinline`,只能真机确认
- **安卓 Chrome 的原生解码分支**:桌面 Chromium 根本没有 `BarcodeDetector`,六轮全程走的是
  iPhone 那条 ZXing 路。**安卓会走原生,那条分支一次都没跑过**
- **真蓝牙/USB 条码枪**:怪癖没在真设备上过 —— GS1 分隔符发 Alt/Control 组合、有的枪用
  Shift 打数字、末尾发 Tab 不发 Enter、**安卓蓝牙报 `key='Unidentified'`**(最后这条正是
  `scan-wedge.js` 里那个隐藏 sink 兜底存在的理由,而 Playwright 造不出来)

### 🟢 体验
热敏纸糊码 · 暗光 · 快速晃动 · 390px 真机手感(截图验过,手感没验)

---

## §5 给下一个窗口的警告

### 5.1 `static/scan/scan-camera.js` 现在 **499/500 行**
下一个往里加东西的人**必须先拆**。拆分点见 §3.6 第一条(失败清单那一坨)。
2026-08-01 我加 1 行代码 + 5 行注释就撞红了闸,压了两轮注释才塞进去。

### 5.2 判据里的数字是量出来的,不是拍的
`clearAfterMs=1600` / `clearAfterMisses=12` / `probeIntervalMs=15` / `GUN_MAX_GAP_MS=50` /
`MIN_LEN_IN_FIELD=8` —— 每个都有注释写来历(真浏览器逐档实测)。**动它们等于推翻六轮验收**,
动之前先重跑 `_r5_cam_floor_by_speed_verify.cjs`(它的 covers 里就有 `scan-camera.js`,
台账闸会提醒你)。

### 5.3 bump `?v` 的连带动作
改了 `pos.html` 的 `pos.js?v` → **必须同步 `static/pos/{pos-sw,cashier-sw}.js` 的
`const V`**,否则装过 SW 的收银设备永不换代。
扫码的懒加载产物(`dist/scan.js` / `dist/zxing.js`)不写在任何 HTML 里,URL 由
`scan-loader.js` 的 `assetVersion()` 运行时从页面上常驻 bundle 的 `?v` 抠指纹现拼:
**主站借 `pre.js`、POS 借 `pos.js`**。

### 5.4 diff 类闸的绿两个方向都会骗人
commit 前跑扫的是上一笔;**push 后跑范围变空,同样报 PASS**。判绿要用**推之前的 master**
当 base。2026-08-01 因此让一笔「产物变了没 bump ?v」推上了 master —— 后果不是晚生效而是
**永远不生效**(CDN immutable 缓存一直发旧 bundle)。

### 5.5 那 26 支 E2E 保的东西单测保不了
摄像头真解码 · 真键盘时序 · 轨道 ended · 取景框映射 —— 台账 `only_e2e` 里写着。改了它们
covers 的源码就要重跑,**串行跑**(并行会互相抢 CPU,这些脚本在机器被压住时会假红)。
素材由 `tests/e2e/e2e_ledger.json` 的 `fixtures` 命令现生成,`.y4m` 在 gitignore 里。

---

## §6 关键文件地图

```
static/scan/                引擎(两个 SPA 共用)
  scan-loader.js            首屏常驻:能力探针 + 懒加载入口 + assetVersion()
  scan-camera.js            摄像头解码循环、去重判据、错误分档   ⚠️ 499/500 行
  scan-wedge.js             条码枪键盘楔子、looksLikeGun 唯一判据
  scan-errors.js            错误码 → i18n 键 → retryable
  scan-zxing-shim.js        ZXing 包成 BarcodeDetector 形状
static/vendor/zxing/        vendored zxing-js 0.21.3 (Apache-2.0)

static/pos/pos-scan.js      收银台消费方   pos-scan-fails.js 失败清单
src/home/inventory-scan*.ts 入库消费方(scan / scan-ui / scan-camera)
src/home/sales-products-scan*.ts 建品消费方(scan / scan-cam)

services/pos/catalog.py     by-barcode(POS 侧)
services/sales/products.py  lookup(主站侧)+ 撞码 + 软删让位
alembic/versions/0092,0093  条码唯一索引 / unit_price 可空

tests/e2e/e2e_ledger.json   E2E 台账:covers / artifacts / fixtures / only_e2e
scripts/_*.cjs              26 支扫码验收脚本(见台账)
```
