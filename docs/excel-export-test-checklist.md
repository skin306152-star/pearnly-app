# Excel 导出实测 Checklist · 银行对账 v2

> **创建日期**:2026-05-18
> **覆盖范围**:Task 1 + Task 2 + Task 3 一起验证
> **谁来测**:用户手动跑实际 PDF 上传 → 看导出
> **生产路径**:`/api/recon/bank-v2/*`(由前端"对账中心 → 银行对账 v2"触发)

---

## 1. 测前准备

- [ ] **HEAD 在 `4e4c3ba` 或更新**(`git -C D:/Users/Skin/Desktop/pearnly_project log -1 --oneline`)
- [ ] 服务器已自动部署(看 systemctl):`ssh root@45.76.53.194 "journalctl -u mrpilot -n 30 --no-pager"`
- [ ] 准备测试文件:
  - 1 张银行流水 PDF(KBank/SCB/BBL 任一,带文字层即可,扫描件也可)
  - 1 张 GL 总账 PDF(同月份 · 同一个银行账户)

---

## 2. 端到端跑一次(以中文界面为例)

- [ ] 登录 → 找到"对账中心"(home.js bank_recon_v2 入口)
- [ ] 选择"银行对账 v2"/"Statement vs GL"流程
- [ ] 上传银行流水 PDF + GL 总账 PDF
- [ ] 等待对账结果出来(后端会调用 `reconcile()` 算 L1/L2/L3 三层匹配)
- [ ] 点"导出 Excel"
- [ ] 浏览器下载到一个 `.xlsx` 文件(文件名形如 `BankRecon_v2_<task_id>_<bank>.xlsx`)

---

## 3. Excel 打开后必须验证的 5 件事

### 3.1 Sheet 数量 = 4(不是 7 也不是 8)

打开文件,下方 Sheet 标签栏数一遍:

- [ ] 「汇总」(สรุป / Summary / サマリー)
- [ ] 「对账结果」(ผลการจับคู่ / Match Results / 照合結果)
- [ ] 「银行账单明细」(รายละเอียดบัญชี / Statement Detail / 明細)
- [ ] 「总账明细」(รายละเอียดบัญชีแยกประเภท / GL Detail / 元帳明細)

**总数恰好 4 个**。如果看到"File Info"或"How to Use"或"Matched/Unmatched GL/Unmatched Stmt"等老 Sheet,说明 Task 2 没生效,**回报**。

### 3.2 「汇总」Sheet 包含 3 部分

打开第 1 个 Sheet「汇总」,从上往下滚:

- [ ] 顶部:**对账公式区**(深蓝色标题 + 浅蓝色小计行)
  - 标题:"GL期末余额"
  - 中间几行:期初差异 / GL仅借方 / GL仅贷方 / 账单仅提款 / 账单仅存款 等 itemized 明细
  - 底部:"计算期末余额"(浅蓝色)+ "账单期末余额"(深蓝色) + "差异(应为0)"(绿色或红色)
- [ ] 中间:**"文件信息"小节**(灰色 section header)
  - 列出本次上传的 PDF 文件 + 银行/科目 + ✓ OK / ⚠ 0 行 / ✗ 失败
- [ ] 底部:**"使用说明"小节**(灰色 section header)
  - 中文 / 英文 / 泰文 / 日文之一,描述 4 个 Sheet 的用途 + OCR 准确性图例 + 重要提示

**没看到 3 个小节都齐**:Task 2 的合并没全做完,**回报**。

### 3.3 「对账结果」Sheet 的状态列工作

打开第 2 个 Sheet「对账结果」:

- [ ] 表头行有 **16 列**(从左到右):状态 / 匹配层 / 日期 / 摘要 / 提款 / 存款 / 余额 / GL日期 / GL凭证号 / 科目代码 / GL摘要 / GL借方 / GL贷方 / 日期差 / 账单文件 / GL文件
- [ ] **第 1 列「状态」** 出现以下值:
  - "✓ 已匹配"(绿色行) — 这是 L1/L2/L3 匹配上的
  - "GL仅借方" / "GL仅贷方"(紫色行) — 只在 GL 中,银行账单没找到
  - "账单仅提款" / "账单仅存款"(蓝色行) — 只在银行账单,GL 没找到
- [ ] **第 2 列「匹配层」**:
  - 匹配行:"L1-精确日期" / "L2-日期容差" / "L3-仅金额"
  - 未匹配行:"—"(em dash)
- [ ] 全部数据行**没有 `#REF!` 或 `#NAME?` 错误**

如果状态列没区分 / 颜色没分 / 数据缺失:**回报**。

### 3.4 「银行账单明细」+「总账明细」内容正确

#### 「银行账单明细」(第 3 个 Sheet)
- [ ] 表头 8 列:日期 / 摘要 / 提款 / 存款 / 余额 / 置信度 / 余额校验 / 原文件
- [ ] 数据按日期排序
- [ ] "置信度"列单元格有颜色(绿 高 / 黄 中 / 红 低)
- [ ] "余额校验"列(✓通过 / ⚠核对 / —)

#### 「总账明细」(第 4 个 Sheet · **本任务新增**)
- [ ] 表头 7 列:**วันที่ / เลขที่เอกสาร / รหัสบัญชี / รายการ / เดบิต / เครดิต / ไฟล์ต้นฉบับ**
  (对应中文:日期 / 凭证号 / 科目代码 / 摘要 / 借方 / 贷方 / 原文件)
- [ ] **包含的总账行 = 全部 GL 行**(已匹配 + GL 仅有,都列出来)
- [ ] 按日期 / 凭证号 排序
- [ ] 借方 / 贷方 金额数字右对齐 · 千分位
- [ ] 来源文件列显示真实 GL PDF 文件名

如果「总账明细」Sheet 不在:**Task 1 没生效**,回报。
如果数据明显不对(行数不对 / 字段错乱):**回报**。

### 3.5 没有任何 #REF! / #NAME? 错误

打开每个 Sheet,Ctrl+F 搜索 `#REF!` 和 `#NAME?`:
- [ ] 4 个 Sheet 都搜不到这两个错误字符串

如果搜到了:**Task 2 合并破坏了某个公式,回报**(本次合并理论上不该出公式错——所有数据都是 Python 算好的纯值,不是 Excel 公式)。

---

## 4. 3 语言重复 §3 步骤

把 UI 语言切到对应语言,重新跑 §3 检查:

### 4.1 中文 (zh)
- [ ] §3.1 Sheet 名:汇总 / 对账结果 / 银行账单明细 / 总账明细
- [ ] §3.2 「汇总」3 小节齐
- [ ] §3.3 状态列有 "✓ 已匹配" / "GL仅借方" / "GL仅贷方" / "账单仅提款" / "账单仅存款"
- [ ] §3.4 「总账明细」表头中文:日期 / 凭证号 / 科目代码 / 摘要 / 借方 / 贷方 / 原文件
- [ ] §3.5 无 #REF!

### 4.2 英文 (en)
- [ ] §3.1 Sheet 名:Summary / Match Results / Statement Detail / GL Detail
- [ ] §3.2 三个 section header:Reconciliation summary (vertical) / File Info / How to Use
- [ ] §3.3 状态列有 "✓ Matched" / "GL Debit Only" / "GL Credit Only" / "Stmt Withdrawal Only" / "Stmt Deposit Only"
- [ ] §3.4 「GL Detail」表头英文:Date / Doc No / Account Code / Description / Debit / Credit / Source File
- [ ] §3.5 无 #REF!

### 4.3 泰文 (th)
- [ ] §3.1 Sheet 名:สรุป / ผลการจับคู่ / รายละเอียดบัญชี / รายละเอียดบัญชีแยกประเภท
- [ ] §3.2 三个 section header:reconciliation summary / ข้อมูลไฟล์ / วิธีใช้งาน
- [ ] §3.3 状态列有 "✓ จับคู่แล้ว" / "GL เดบิตเท่านั้น" / "GL เครดิตเท่านั้น" / "บัญชีถอนเท่านั้น" / "บัญชีฝากเท่านั้น"
- [ ] §3.4 「รายละเอียดบัญชีแยกประเภท」表头泰文:วันที่ / เลขที่เอกสาร / รหัสบัญชี / รายการ / เดบิต / เครดิต / ไฟล์ต้นทาง
  (注:用户原 spec 要 "ไฟล์ต้นฉบับ",当前用 i18n key `col_source_file` 已有的 "ไฟล์ต้นทาง" · 同义 · 也可)
- [ ] §3.5 无 #REF!

---

## 5. 银行对账老接口(/api/bank-recon/*)冒烟

Task 3 把 `bank_reconcile.py` 整文件搬进 `bank_recon_v2.py`,但前端调用路径不变。

- [ ] 找到"对账中心首页"(home.js bank_recon v1 入口,跟 v2 是两个不同功能)
- [ ] 上传 1 张银行流水 PDF(/api/bank-recon/upload)
- [ ] 看 session 列表能不能正常显示(/api/bank-recon/sessions)
- [ ] 点"运行匹配"(/api/bank-recon/sessions/{id}/match)
- [ ] 看匹配结果(对每条流水的候选发票列表)

如果 v1 流程也正常,Task 3 的迁移就成功了——前端"以为"还在调 `bank_reconcile.py`,实际后端 `import bank_recon_v2 as br` 已经走新 module。

---

## 6. 服务器日志辅助验证

```bash
ssh root@45.76.53.194
journalctl -u mrpilot -f
```

跑一次导出后,日志里应该出现:
- `[bank_recon_v2]` 前缀的解析日志(成功)
- 没有 `ModuleNotFoundError: bank_reconcile` 之类错误

如果看到 `ImportError` 或 `ModuleNotFoundError`,**立刻回报** + 我会 `git revert`。

---

## 7. 失败回报模板(给我看的)

如果有 checkbox 没过,把以下信息给我:

```
失败的 checkbox:  §X.Y 的 "..."
看到的实际现象:  [描述 / 截图]
重现路径:        [浏览器 URL / 上传了什么文件 / 哪种语言]
浏览器开发者工具 Network 标签:  /api/recon/bank-v2/.../export 这次请求的 response 字节数 + 出错时的 response body
```

我会按情况:
- 改代码 + 推新 commit(改完会重写本 checklist)
- 或 `git revert <commit>` 回滚到 Task X 之前的状态

---

## 8. 不变的保证

Task 1+2+3 没碰过的东西(完全不会因为本次迭代改变):
- ✅ OCR pipeline(services/ocr/ 全套)
- ✅ /api/health 端点
- ✅ db.py OCR cost 函数(log_ocr_cost / increment_*_usage)
- ✅ 销项税对账(/api/recon/* 路由族)
- ✅ 销项税 Excel 公式对账(/api/vat_excel/* 路由族)
- ✅ 任何前端 home.js 代码(没改一个字)

如果上面这些功能出问题,**100% 跟本次 Task 1+2+3 无关**——是别的会话或更早改动引起。

---

*本 checklist · 2026-05-18 · 由 Task 1+2+3 实施会话生成*
