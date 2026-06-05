# 12 · e-Tax 可插拔架构(全档位 + 留接口 · 为未来铺垫)

> Zihao 2026-06-05:e-Tax 直报先把框架写进去、留个接口,未来拿到证书/选定中介就接通。
> 核心:**开票现在就能用;"报不报税局、怎么报"是背后一个可插拔通道**。同 ERP 适配器(Mr.ERP/Xero)套路。
> 衔接:决策见 `docs/09`(e-Tax"可行才做")· 合规见 `docs/03` · schema 见 `docs/02`。

## 设计原则:开票 ⊥ 报税局(解耦)

发票照常开 → 出合规 PDF。**是否上报、走哪条通道,是开票之后一个独立、可替换的步骤**。
开票主流程**永远不变**;换通道 = 换一个适配器 + 一份配置。

## 一个接口(seam)+ 四个实现(全档位)

```python
# services/sales/etax/channel.py（迁回时落点 · 现为设计草案）
class ETaxChannel(Protocol):
    key: str                                  # noop | email | provider:<name> | self_hosted
    def submit(self, doc: SalesDocument) -> ETaxResult: ...
    def status(self, rd_ref: str) -> ETaxStatus: ...

@dataclass
class ETaxResult:
    ok: bool
    channel: str
    rd_ref: str | None        # 税局/中介回执号
    receipt_url: str | None   # 可查看链接
    error: str | None
```

| 实现 | 是什么 | 何时上 | 依赖 |
|---|---|---|---|
| `NoopETax` | 不报税局,只出合规 PDF | **Phase 1 默认** | 无 |
| `EmailETax` | e-Tax by Email:PDF 发买方 + 抄送 ETDA 盖时间戳(平替①) | Phase 2(小客户 ≤3000万) | 无证书 · 复用邮件通道 |
| `ServiceProviderETax` | 推数据给持牌中介 API,它签名+报税局(中介路线) | Phase 3 | 中介 API 凭证 |
| `SelfHostedETax` | 自建:XML+证书签名+直连 RD(自建路线) | Phase 3+ | 电子证书 + 税局服务商登记 |

> 选哪个 = 按**租户/客户配置** `etax_channel`(见下)。不同客户可不同档(小客户走 Email,大客户走 Provider/Self)。

## 开票流程里唯一的对接点(hook)

```python
def issue_sales_document(doc):
    allocate_running_number(doc)              # 连号(事务内 FOR UPDATE)
    doc.status = "issued"; doc.issued_at = now_utc()
    channel = get_etax_channel(doc.tenant_id, doc.client_id)   # 配置决定 · 没配=None
    if channel:                               # ← 未来接通的唯一入口
        result = channel.submit(doc)
        record_etax_submission(doc, result)   # 写 etax_submissions
    return doc
```

没配 channel(或 `NoopETax`)→ 只出 PDF,不报。开票照常。**框架天然在,通道后插。**

## 现在(Phase 1)就铺的"铺垫"——四件事

1. **留表**:`etax_submissions`(见 `docs/02` · channel/rd_ref/status/receipt_url/payload/error/submitted_at)+ 租户/客户 `etax_channel` 配置字段 + `etax_credentials`(加密 · 复用 `core/kms_helper`)。
2. **发票模型一次性带全 e-Tax XML 需要的字段**(避免以后重建模):卖方/买方 名称+地址+13位税号+分支码、doc_type、连号、开具日期、行项目(描述/数量/单价/金额/税)、VAT 分列、合计、备注。**Phase 1 开票就把这些都收齐**,e-Tax 接通时直接喂。
3. **接口 + `NoopETax` 先实现**;`EmailETax` 可早做(成本低)。
4. **`ServiceProviderETax` / `SelfHostedETax` = 文档化的桩**:

```python
class ServiceProviderETax:
    key = "provider"
    def submit(self, doc):
        raise ETaxNotConfigured("待选定持牌中介 + 填 API 凭证 · 见 docs/12 接通清单")

class SelfHostedETax:
    key = "self_hosted"
    def submit(self, doc):
        raise ETaxNotConfigured("待取得电子证书 + 税局服务商登记 · 见 docs/12 接通清单")
```

## 未来"接通"清单(拿到文件后只做这些 · 不动开票)

**走中介(Provider):**
- [ ] 选定一家税局认证中介,拿到其 API 文档 + 凭证
- [ ] 在 `ServiceProviderETax.submit` 里实现:组装请求 → 调中介 API → 解析回执 → 返回 `ETaxResult`
- [ ] 租户配置 `etax_channel="provider:<name>"` + 存凭证(加密)

**走自建(Self-hosted):**
- [ ] 客户取得电子证书(.p12/.pfx)+ 完成税局 e-Tax 登记(+ 我方服务商资质,待确认)
- [ ] 实现:发票 → RD 标准 XML → 用证书 XAdES 签名 → 报送 RD → 收回执
- [ ] 上传/加密保管证书(`core/kms_helper`)· 配置 `etax_channel="self_hosted"`

两条都只是**填一个适配器实现 + 一份配置**。开票主流程、数据库、UI 全不动。

## 一句话

> 最全最齐 = 一个 `ETaxChannel` 接口罩住 4 档(不报 / Email / 中介 / 自建);
> 现在 Phase 1 把**接口 + 表 + 全字段发票模型 + 桩**铺好,e-Tax 是"插上去"的,不是"重做"。
> 合作者那个"自建 vs 中介"的回复,只决定**未来填哪个桩**,完全不卡 Phase 1。
