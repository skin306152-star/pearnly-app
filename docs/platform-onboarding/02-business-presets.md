# 02 · 业态预设 + 关键决策(图纸)

> 依据:`docs/PRODUCT_VISION_MODULAR.md` 业态表 + 桌面 `Pearnly_业态套餐_UI预览/01-注册业态选择.html`(已拍板)。

## 一、业态 → 模块预设(canonical)

可开关模块全集(7):`sales` · `expense` · `recon` · `inventory` · `pos` · `receivable` · `knowledge`。
预设 = 每个业态「默认开」的子集;未列入的可开关模块 onboarding 时显式置关(可在设置里再开)。

| business_type | 中文 | 默认开的 module_key |
|---|---|---|
| `firm` | 会计事务所 | sales · expense · recon · knowledge |
| `retail` | 零售 / 小卖部 | sales · inventory · pos |
| `pharmacy` | 药房 | sales · inventory · pos |
| `restaurant` | 餐厅 | sales · inventory · pos |
| `service` | 服务型公司 | sales · expense |
| `b2b` | 批发贸易 | sales · inventory · receivable · expense |

> `sales`(开票)在所有业态都开 —— 它是平台主线尖刀(对齐愿景「先尖后广」)。

## 二、与 UI 设计稿的差异说明(诚实标注)

- **会员积分(membership)**:UI 屏01 在 retail/pharmacy 预设里画了「会员积分」,但屏03 设置页的可开关清单**没有**它 → 它**不是独立可开关模块**,而是 POS 模块内的能力块(未来)。本期**不纳入** 7 模块,onboarding 不为它写 tenant_modules。屏01 前端实现时,会员积分作为 POS 套餐的视觉附属项展示即可。
- **业态 key `restaurant`**:UI 屏01 `data-t="resto"`;后端 canonical 用 `restaurant`。前端发请求时用 `restaurant`(P 阶段前端按此对齐)。
- **POS 既有预设(`services/pos/onboarding.py` 的 `BUSINESS_PRESETS`)** 是**能力块**预设(multi_unit/track_batch/tables…),与本平台**模块**预设是两层,互不替代:平台预设决定「哪些模块出现」,POS 能力块预设决定「POS 模块内开哪些行为」。两者都按 business_type 索引,语义独立。

## 三、关键决策(规划已定 + 本窗口细化)

- **D1 老租户不破坏(最高优先)**:`tenant_modules` 无显式行的模块回落 `DEFAULT_ENABLED`。本期把 `receivable` 默认值设 **True**(与现状「应收追踪常显」一致),连同既有 sales/expense/recon/knowledge=True、pos/inventory=False。**onboarding 是 opt-in**:只有显式调用才写显式行;从不主动给老租户写行 → 老租户导航维持现状。
- **D2 关 = 隐藏不删数据**:设置页 toggle 只改 `tenant_modules.enabled`,不删任何业务表数据;重开即恢复(对齐愿景原则 #5)。
- **D3 平台 onboarding 只翻模块开关,不做 POS 硬件开通**:`apply_preset` 对 7 个模块逐个 `set_module(enabled=..., config=None)` —— **config=None 只翻开关、不动既有 config**。POS 终端/收银员/默认仓的实建仍走既有 POS 屏8「开通收银台」(`PUT /admin/onboarding`)。理由:松耦合、可逆、不预建硬件。
  → 引申约束(留 P 阶段前端):`pos` 模块「已开关 enabled=true」≠「已开通 provisioned」。前端数据驱动导航要区分二者(未开通仍显「开通收银台 →」引导)。provisioned 判据 = 该账套是否已有终端/收银员(后端可加只读 `provisioned` 字段,见 03 §扩展位)。
- **D4 业态可改 / 切换业态**:设置页「切换业态」= 再调一次 onboarding(同一接口),`apply_preset` 显式覆盖 7 模块开关为新业态组合;之后可逐个微调(toggle)。business_type 持久化以便回显「当前业态」。
- **D5 权限**:onboarding + 模块 toggle = owner 专属(`invited_by is None` 且非收银员);收银员/成员/会计不可改模块配置 → `pos.forbidden`(403)。读 `GET /api/me/modules` 任意已登录租户主体可调(导航需要)。
- **D6 计费按模块**:愿景原则 #6,本期不接(现按额度)。`tenant_modules.config` 预留余量。

## 四、business_type 持久化方案

复用 `tenant_modules` 表(不新增表/迁移):用**保留哨兵行** `module_key = '__business_type__'`,`config = {"value": "<business_type>"}`。
- 专用 DAL:`store.set_business_type` / `store.get_business_type`(显式走哨兵,不经 `set_module` 的 KNOWN_MODULES 白名单)。
- `get_modules` 仍只遍历 `KNOWN_MODULES` → 哨兵行**永不**作为「模块」泄漏到导航。
- 老租户无哨兵行 → `business_type = None`(前端显示「未设置 / 全部开启」legacy 态)。
</content>
