# 权限管理整顿 · 02 权限点全集 + 角色矩阵(★核心)

> 这是整套系统的"规则目录"。权限码合法集合的单一来源 = `services/authz/registry.py`(代码),本页是它的设计稿;改一处必同步另一处(施工时加一致性单测钉死)。

## 权限码命名

`<模块>.<资源>.<动作>`,全小写点分(GCP IAM `service.resource.verb` 惯例)。动作动词收敛成 8 个,禁止自造:

| 动词 | 含义 | 备注 |
|---|---|---|
| `view` | 读(列表+详情) | |
| `create` | 建草稿/录入(可逆) | |
| `edit` | 改未定稿的 | |
| `delete` | 删可逆对象(草稿) | |
| `approve` | 审批/开出/过账(**不可逆动作统一归这档**) | 含 issue/void/红冲/submit |
| `export` | 导出/下载报表 | 只读角色可有(拍板点#4) |
| `manage` | 模块配置后台(设置/主数据) | |
| `operate` | POS 收银动作(售卖/开班) | 仅 pos 模块用 |

依据:QBO Advanced 自定义角色的 view/create/edit/delete/approve 五动作是行业最标准实现;Xero Draft only vs Approve and pay 证明 create 与 approve 必须分档(NIST RBAC2 职责分离同构)。

## 权限点全集(registry · 56 个)

### 横切域(不挂模块开关)

```
team.member.view        team.member.invite      team.member.edit_role
team.member.scope       team.member.remove      team.member.toggle
billing.view            billing.manage          ownership.transfer
settings.org.view       settings.org.edit       settings.modules.manage
settings.workspace.manage                       audit.log.view
```

### 业务模块(模块关 ⇒ 整组不可用,见 03 联动规则)

```
sales:      sales.doc.view  sales.doc.create  sales.doc.edit  sales.doc.delete
            sales.doc.approve   # 开出/红冲/补开/作废(不可逆全在这)
            sales.doc.export    sales.product.view  sales.product.manage
            sales.settings.manage
expense:    purchase.doc.view  purchase.doc.create  purchase.doc.edit  purchase.doc.delete
            purchase.doc.approve  # 审批/付款确认/WHT 入账
            purchase.supplier.manage  purchase.settings.manage
accounting: acct.entry.view  acct.entry.review   # 逐笔审例外
            acct.entry.approve  # 过账/关账(不可逆)
            acct.coa.manage  acct.ledger.export  acct.settings.manage
tax:        tax.filing.view  tax.filing.create   # 生成税表草稿
            tax.filing.approve  # 提交(不可逆·已报不可改)
            tax.settings.manage
recon:      recon.view  recon.create  recon.approve  recon.export
receivable: ar.view  ar.create  ar.edit
knowledge:  kb.doc.view  kb.doc.create  kb.doc.delete  kb.ask
inventory:  inv.view  inv.create   # 入库/盘点录入
            inv.approve  # 盘点过账/调整确认
            inv.report.view
pos:        pos.admin.manage   # 商品/收银员/桌台/收款设置/店铺码(老板后台)
            pos.report.view  pos.sale.operate  pos.shift.operate
            pos.refund.approve  # 退货/作废(POS 端不可逆)
intake:     intake.upload   # 统一智能入口(识别完建草稿落列表·待归类已下线)
```

注:`accounting/tax` 是已封板待施工模块(docs/accounting、docs/tax-filing),权限点现在就进 registry 占位——施工时直接 `require_perm`,不再返工加门。

## 预设角色 × 权限矩阵

6 个系统角色,**单角色制**(P1 不做 Stripe 式叠加)。矩阵记号:✔=有;─=无。

| 权限组 | 老板 owner | 管理员 admin | 会计 accountant | 录入员 clerk | 只读 viewer | 收银员 cashier |
|---|---|---|---|---|---|---|
| **all(短路)** | ✔ `{"all":true}` | ─ | ─ | ─ | ─ | ─ |
| team.member.* | ✔ | ✔ | ─ | ─ | ─ | ─ |
| billing.view / manage | ✔ | view | ─ | ─ | ─ | ─ |
| ownership.transfer | ✔(仅发起) | ─(可被指定接收) | ─ | ─ | ─ | ─ |
| settings.org / modules / workspace | ✔ | ✔ | ─ | ─ | ─ | ─ |
| audit.log.view | ✔ | ✔ | ─ | ─ | ─ | ─ |
| *.view(全业务模块) | ✔ | ✔ | ✔ | ✔ | ✔ | ─ |
| *.create / edit / delete(草稿层) | ✔ | ✔ | ✔ | ✔ | ─ | ─ |
| *.approve(不可逆层) | ✔ | ✔ | ✔ | ─ | ─ | ─ |
| *.export | ✔ | ✔ | ✔ | ─ | ✔(拍板点#4) | ─ |
| *.settings.manage / *.manage(模块配置) | ✔ | ✔ | ✔(仅 acct.coa / sales.product / purchase.supplier 主数据) | ─ | ─ | ─ |
| intake.upload | ✔ | ✔ | ✔ | ✔ | ─ | ─ |
| pos.admin.manage / pos.report.view | ✔ | ✔ | report.view | ─ | report.view | ─ |
| pos.sale.operate / shift.operate | ✔ | ✔ | ─ | ─ | ─ | ✔ |
| pos.refund.approve | ✔ | ✔ | ─ | ─ | ─ | ─(P2:经理输码放行) |

角色一句话(UI 角色说明卡用,permission-role review·NIST RBAC3):

- **老板**:一切 + 计费 + 转移所有权。每租户至少 1 人,不可被他人移除。
- **管理员**:除计费管理和所有权外的一切(Stripe Administrator / Canopy Admin (No Billing) 同构)。给合伙人/二把手。
- **会计**:全业务读写 + 审批/开票/过账/报税 + 业务主数据(科目表/商品/供应商)。不碰团队、计费、模块开关。给专职会计/事务所做账员工。
- **录入员**:录票/建草稿/上传,**不能做任何不可逆动作**(开票/审批/过账/报税/导出)。给实习生/前台。对应 Xero Draft only 档。
- **只读**:看 + 导出。给投资人/外部顾问/老板娘。对应 Xero Read Only + Stripe View Only(可导出)。
- **收银员**:只存在于 POS 令牌体系(typ=pos),只有收银操作面;不进主程序登录。现行体系一字不动,registry 收录它只为矩阵完整 + POS 门将来同源取码。

## 作用域(正交维度 · 角色之外独立配)

| scope_mode | 语义 | 谁可用 |
|---|---|---|
| `all` | 全租户所有套账(默认) | 任何角色 |
| `assigned` | 仅 member_scopes 列出的套账主体 | accountant / clerk / viewer(owner/admin 强制 all) |

- 事务所场景 = 会计角色 + assigned 若干客户套账(Canopy Staff (Assigned Contacts) 的产品化标准答案)。
- SME 多主体场景 = 同机制天然支持(老板全见,员工只见被分配主体)。
- 执行语义:assigned 成员对未分配套账 = **404 不是 403**(防 IDOR 枚举,OWASP "Lookup IDs not accessible even when guessed")。
- 不带 workspace 维度的资源(团队/计费/设置)不受 scope 影响——它们本来就是 owner/admin 专属。

## 职责分离(SoD · P1 轻量)

- 录入员建的销项草稿,自己**永远开不出去**(没有 approve)——静态 SSD 由矩阵天然保证。
- 审批工作流(§F·已上线)叠加在权限之上:有 sales.doc.approve 仍可能被流程要求"他人复核"。权限管"有没有资格",流程管"这单要不要双人"。两层别混。

## 超管(平台层 · RBAC 之上)

is_super_admin 不进角色矩阵,在 `require_perm()` 里最先短路放行(现状不变);超管动作照旧落 operation_logs(actor_is_super)。分级(只读超管)= P2。
