---
name: erp-integration
description: 接 ERP / 老 PHP 系统 / 无 API 第三方(MR.ERP、Express DBF、小助手 companion)时的铁律:无 API 走 Playwright 不做 HTTP 反向工程、真样本是唯一 ground truth、响应码≠业务成功、listing 必 retry+失败截图、小助手改动必发版。做 ERP 推送、导入排障、字节级模板、companion 改动时用。
---

# ERP / 老系统集成

## 1. 无开放 API 一律走服务端 Playwright

不再做 HTTP 反向工程(抓包 + hidden field + cookie 重放)。历史:MR.ERP 反向工程 5 步 endpoint 实测通了,但字节级 xlsx 兼容调 3 天、改一个 hidden field 就挂、错误只能 scrape 泰文关键词。Playwright 维护成本约是它的 1/10。

评估新 ERP:先看有没有 OpenAPI / OAuth,没有就直接 Playwright。已知:MR.ERP 无 API(适用)· FlowAccount / Xero 有 API(不适用)。

反向工程的产物**不留废件**:先验信息(URL / 字段名 / 数据格式 / 业务规则)写进 `docs/integrations/<vendor>-known-facts.md`,老代码 `git rm`,不留 `.deprecated` / `_legacy.py` 僵尸,也不在注释里写"参考 xxx_legacy.py"。

## 2. 真样本是唯一 ground truth

碰字节级 / wire-format(xlsx、docx、xml 容器模板、字段顺序敏感的 form),必须拿"已验证导入成功过的真样本"当基准,严禁按文档描述盲调。

1. 取真样本(业务方提供 / SaaS 导出)→ 存 `docs/integrations/templates/<vendor>_sample_*.<ext>` + 记来源和验证日期
2. 直接字节级解构(`zipfile` 解 xlsx / `xxd` 看二进制),不靠文档描述
3. 逐字段对照自己生成的产物
4. known-facts.md 写的只是"我们的理解",**跟真样本冲突时真样本赢**
5. 优先 clone-based 生成:复用真样本 metadata(styles / namespaces / 隐藏字段),只替换业务字段

历史:被拒"数据列数不到 18",本能反应想改空 cell 写法,拿到真样本才发现真因是 `styles.xml` 索引冲突 —— 不对照真样本永远找不到。

## 3. 老系统的"成功"不是成功

`importpc.php` 返 `"2"`、"Delete Success" splash 页,都 ≠ 数据库真写进去了。

- 业务结果只看真出口:报告 xlsx / listing 有没有那行 / 重查 detail 页
- adapter 必须写 verifier 路径(成功路径 + listing 二次确认)
- 错误场景写守门测试(拿整张 fail xlsx 验 adapter 真把 `หมายเหตุ` 翻成 FailedRow)

## 4. 拉外部 listing 必须 retry + 失败留证

- 抓取层:`goto` 后 `wait_for_selector(主结果, ≥10s)`,超时 `page.reload()` 再等一次,仍失败存截图并把路径塞进 exception
- 路由层:transient 错(`ERR_TECHNICAL` / `ERR_UNEXPECTED` / `ERR_NETWORK`)retry ≥1 次间隔 ≥2s;非 transient(`ERR_AUTH` / `ERR_CRED_DECRYPT` / `ERR_BUSINESS` / `ERR_NO_CREDS`)立即 bail 省 quota
- **失败响应不写缓存**(否则用户点两次都是同一个失败)
- 不许一次失败就 fallback 到"无法拉取,请手动输入"

## 5. 小助手 companion:改了不发版 = 白改

源码在独立私有仓 `skin306152-star/pearnly-companion`。发布正本见该仓 `docs/RELEASE.md` 和本仓 `docs/deployment/COMPANION_PUBLICATION.md`：Windows构建 → Ubuntu经WIF发布私有GCS → 正式域名完整回读。`release.ps1 -BuildOnly`仅构建；旧SSH/SCP发布已退役。客户端功能改动须更新VERSION，先完成staging与Windows设备验证，再正式发布并确认真实设备升级；安装包发布流程迁移本身不要求改VERSION或替换生产包。配置、构建、发布与用户升级分别记账。

## 6. Express(真 ERP)落点

`\\accserver\ACCOUNT` · BIT9 编码 · 纯 Python 解 DBF。期初库存只动库存模块(STMAS/STCRD),不产 GL 凭证;碰到"按期初存货 / 漏记采购 / 新客户零期初"三情形先 escalate 不静默落。
