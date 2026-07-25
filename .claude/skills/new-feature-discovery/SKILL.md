---
name: new-feature-discovery
description: 动手写码前的两步 —— 先做 discovery(真实场景 + 市场对标 + 实用性判断),再答落地 4 问(哪个领域 / 新建哪个文件 / 测试在哪 / 删什么旧的)。加新功能、改产品逻辑、派单、或任务板上的条目要开工时用。
---

# 写码之前

## 1. Discovery:先写「场景 + 对标」,再给设计

拿到需求别直接开码。响应里先写一小段,回答三问:

1. **真实场景(JTBD)**:谁、在什么情境下、为解决什么痛点用它。别从代码结构倒推产品逻辑。
2. **实用性(RICE / Kano)**:真需要还是自嗨?警惕 feature creep 和镀金。**任务板上已列的条目,开工前也要重过一遍 RICE —— 列过 ≠ 值得做。**
3. **便利性**:高频动作点击最少 / 手机端优先 / 危险操作有确认 / 四态诚实 / 减认知负荷。

产品逻辑落在真实场景 + 市场成熟范式上。成熟产品验证过的 design pattern 照抄降学习成本(Jakob's Law):POS 看 Loyverse / Square / StoreHub / SumUp,收银台交互照搬 Odoo POS(施工图纸在 `docs/pos/odoo-ux-port/`),记账看竞品。

设计必须从"用户手里的东西长什么样"往回推(客户真会丢一个 zip 或一整个文件夹进来),不是从"说明书上应该怎么用"往前推。

**技术选型自己定**,不要把技术方案的岔路抛给 Zihao 拍板 —— 他是产品视角、非技术。给结论 + 理由,他要么点头要么否。

## 2. 落地 4 问(30 秒,答不出来不许开写)

1. **领域**:billing / auth / OCR / recon / erp / line / pos / dms / archive / settings / …?答不出来说明跨领域设计没想清。
2. **新建哪个文件**(写确切路径,不准说"放 utils 吧"):
   - 后端 API → `routes/<名>_routes.py`(不进 `app.py`)
   - 后端业务 → `services/<领域>/<feature>.py`(不进 `core/db.py`)
   - 前端 → `src/home/<feature>/*.ts|js`(不进巨石)
   - 新 CSS → 独立文件
3. **测试在哪**(确切路径 + 至少一个用例名):契约 `tests/unit/test_<名>_contract.py` · 集成 `tests/integration/test_<feature>.py` · 前端 `tests/e2e/<NN>-<name>.spec.js`。每个新文件 ≥1 测试。
4. **删什么旧的**:替换实现的必须同一个 commit 删干净(`git rm` 旧文件 / 删老函数)。全新功能写 `N/A`。**禁止两套并存"先观察一阵子"** —— 那一阵子永远不到。留 re-export shim 必须写 `# 兼容 re-export · 删除 deadline = <日期>`。

## 3. 硬约束(机械闸会拦)

- 单文件 <500 行 · 单一职责 · 无循环依赖
- 新功能藏 feature flag(rollout 默认关 → 验过再放量;**不搞金丝雀长期灰度,做完测完就全开**)
- schema 走迁移不走 ad-hoc · 写操作幂等 · 敏感操作留审计
- 修 bug 时:同一个 pattern 一次性全项目修完(grep 同类),但**不主动捎带别的 bug 类** —— 那属于另开一单
