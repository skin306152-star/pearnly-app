# ACCEPTANCE_PLAYBOOKS.md · 固定验收剧本

> 改完某模块就跑对应剧本,输出 PASS/FAIL 清单 + 真实证据。命令可直接复制。
> 真账号 token「用完即弃」· 不提交 · 不打印全文。最后更新:2026-05-26。

## 通用:登录拿 token

```bash
curl -s -X POST https://pearnly.com/api/login -H "Content-Type: application/json" \
  -d '{"username":"<邮箱>","password":"<密码>"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['token'])" > /tmp/ptok.txt
TOK=$(cat /tmp/ptok.txt)
# 用完:rm -f /tmp/ptok.txt
```

---

## 剧本 A · MR.ERP 推送(本会话已实证)

**前提**:endpoint 必须 `enabled=true`(否则 `/api/erp/push` 返 400 `erp.endpoint_disabled`)· 只推 **sandbox**(TEST2019,comidyear=6),**绝不推付费用户真账套**。

```bash
# 1. 看账号 + endpoints(确认账套是沙箱)
curl -s https://pearnly.com/api/me -H "Authorization: Bearer $TOK"
curl -s https://pearnly.com/api/erp/endpoints -H "Authorization: Bearer $TOK"
# 2. test-connection(确认凭据/会话 · 返 companies 看账套)
curl -s -X POST "https://pearnly.com/api/erp/endpoints/<EP_ID>/test-connection" -H "Authorization: Bearer $TOK"
# 3. 找一张发票 history
curl -s "https://pearnly.com/api/history?limit=5" -H "Authorization: Bearer $TOK"
# 4. 推送
curl -s -X POST https://pearnly.com/api/erp/push -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"history_id":"<HISTORY_ID>","endpoint_id":"<EP_ID>"}' --max-time 200
# 5. 取日志详情(bill_no 在 response_body 里)
curl -s "https://pearnly.com/api/erp/logs/<LOG_ID>" -H "Authorization: Bearer $TOK"
```

**必收集的 8 项**:Pearnly 账号/tenant · history_id · endpoint_id · push log_id · 匹配已有 or 自动建买方 · status · 失败时 error_msg/response_body · 成功时 `mrerp_bill_no`。

**PASS 判定**:`erp_push_logs.status=success` + `response_body.mrerp_bill_no` 有值 + **MR.ERP 报表/listing 真查到该 bill**(铁律 #9 · 这步常交 Codex 独立核)。

**判匹配 vs 自动建**:看 prod 日志 —— 有 `auto-created customer` 行=自动建;无客户创建行且无 `ERR_NO_CUSTOMER_MAPPING`=匹配已有。
```bash
ssh root@45.76.53.194 "journalctl -u mrpilot --since '<push时间前1min>' | grep -iE 'mrerp-lock|customer|auto.?creat|bill|importpc|<INVOICE_NO>'"
```

**收尾**:测试 endpoint 用完恢复 `enabled=false`;**别让测试账号长期开自动推送**(红线)。

---

## 剧本 B · 银行对账

```bash
python -m pytest tests/unit -q -k "bank"           # 单元
# 真账号:POST /api/bank-recon/upload(对账单文件)→ session_id
#         POST /api/bank-recon/sessions/{id}/match → 看匹配结果
```
**PASS**:session 建成 + 匹配结果有行;**rows=0 / 整侧失败必须显式失败,不许显示完成**(踩过 GL CSV 整侧吞成完成)。

---

## 剧本 C · 收入对账 / 销项税(GL·VAT·Excel)

```bash
python -m pytest tests/unit -q -k "recon or vat or glvat"
python -m pytest tests/unit/test_recon_gl_csv_preflight.py -q
# 真账号:POST /api/recon/gl-vat/submit · /api/vat_excel/submit · /api/recon/bank-v2/submit
```
**PASS**:任务建成 + 成功后「近期任务」即时刷新;失败说明具体原因(科目前缀错/报告 0 行),不只"出错了";跨月报告不静默合并;**任一侧 0 行 → needs_mapping/failed,不显示完成**。

---

## 剧本 D · OCR 识别 + 扣费

> ⚠️ 烧真额度(铁律 #25.1)· 用测试账号 · 塞 nonce 防文件指纹缓存命中导致复验失真(铁律 #25.4)。

```bash
# 真账号:POST /api/ocr/recognize(上传发票)· 前查余额 /api/me 或 /api/ocr/quota,后再查 → 差额=扣费
```
**PASS**:识别返字段 + 余额按量减(图片/PDF 按 OCR 页 · Excel 按字符);缓存命中不重复扣;余额 0 拦准入(除豁免)。**识别不准/不全标"请核对",不瞎填**。

---

## 剧本 E · 充值 / 扣费 / 员工用量

> 🔴 改计费/余额/套餐 = 高敏红线 · 必须 Zihao 在场。验收只读为主。

```bash
# 超管:/api/admin/cost/overview · /api/admin/credits/overview · /api/admin/cost/by_user
```
**PASS**:充值后余额增;扣费记账正确;员工用量计入老板额度(seats 不增配额·铁律 PLG)。

---

## 剧本 F · 重整长跑收尾(每次拆文件后)

```bash
python -m pytest tests/unit -q
python -m black --check --target-version py310 <改的文件>
python -m ruff check <改的文件>
python scripts/check_imports.py
python scripts/check_i18n.py static/home.js --strict     # 若动前端文案
npx eslint src/home/<file>.js                            # 若动 src/**
```
**PASS**:全绿 + 新代码带契约测试 + commit message 含 `REFACTOR-<id>`。

---

## 部署后冒烟(任何 push 后)

```bash
ssh root@45.76.53.194 "systemctl show mrpilot -p ActiveEnterTimestamp"   # ≥ push 时间(新进程)
curl -s -o /dev/null -w '%{http_code}\n' https://pearnly.com/api/version  # 200
ssh root@45.76.53.194 "journalctl -u mrpilot --since '2 min ago' | grep -ciE 'Application startup complete'"  # =2(两 worker)
ssh root@45.76.53.194 "journalctl -u mrpilot --since '2 min ago' | grep -iE 'ImportError|Traceback'"          # 应为空
```
搬出的路由抽查返 401/422(非 404/500)= 零丢路由。
