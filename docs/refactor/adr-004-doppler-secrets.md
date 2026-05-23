# ADR-004 · Doppler 做 Secrets 集中管理(替代散落 .env)

> **状态**:已采纳方向 · **待 Zihao 注册账号后落地**(2026-05-24 拍板)
> **关联 task**:REFACTOR-A4(Secrets 管理 · `.env` → Doppler)
> **依赖**:A3(环境分级 · 已落地本地 Docker)

---

## 背景

当前密钥散落多处:
- `.env.local`(本地开发 · gitignored)
- `_gemini_key.local/`(Gemini key + Vision 服务账号 · gitignored)
- 生产 systemd 环境变量(真实值只在服务器)

问题:无集中管理 · 无版本/审计 · 无轮换流程 · 多人协作时无法安全分发。

## 决策

**用 Doppler 做 secrets 单一权威源。**

| 方案 | 取舍 | 结论 |
|---|---|---|
| **Doppler** | 开发者**个人免费** · 云端集中 · CLI 注入 · 多 config(dev/staging/prod) | ✅ 选这个 |
| 1Password Secrets | 要付费订阅 | ❌ 仅在已用 1Password 时划算 |
| SOPS/git-crypt | 免费但日常操作繁琐 · 加密文件进 git | ❌ 偏重 |

---

## ⏳ 待 Zihao 做的(只能你做 · AI 无法代办)

1. **注册 Doppler**:https://dashboard.doppler.com/ (个人免费 tier)
2. **建 project**:名字 `pearnly` · 自动带 3 个 config:`dev` / `stg` / `prd`
3. **导入现有密钥**:把 `.env.local` + `_gemini_key.local/` 里的真实值填进对应 config
   (`.env.example` 是字段清单 · 见下方"迁移清单")
4. 告诉我"注册好了" · 我接着做 CLI 集成 + 本地/prod 注入 + 文档

---

## 落地方案(Zihao 注册后 AI 执行)

### 本地

```powershell
# 装 Doppler CLI(Windows · scoop 或 官方安装包)
scoop install doppler
doppler login
doppler setup            # 选 pearnly / dev

# 跑应用(密钥由 doppler 注入 · 不再读 .env.local)
doppler run -- uvicorn app:app --port 7860
```

### 配合 A3 Docker

```powershell
# doppler 把 secrets 导出为 env 注入容器
doppler run -- docker compose up --build
```

### 生产(Vultr · 接 git-deploy)

prod 改用 Doppler service token(只读)· systemd 启动前 `doppler run`。
⚠️ 这步会动启动脚本 = 碰铁律 #16 红线 · 落地时单独走流程问 Zihao。

---

## 迁移清单(.env → Doppler · 哪些密钥要搬)

按 `.env.example` 分区 · 真实值从生产 systemd / `.env.local` / `_gemini_key.local/` 取:

| 区 | 关键密钥 | 来源 |
|---|---|---|
| 必填 | `DATABASE_URL` `JWT_SECRET` | 生产 systemd |
| 安全 | `PEARNLY_KMS_KEY` `GITHUB_WEBHOOK_SECRET` `EMAIL_ENCRYPTION_KEY` | 生产 systemd |
| AI/OCR | `GEMINI_API_KEY` `GOOGLE_API_KEY` `GOOGLE_APPLICATION_CREDENTIALS` | `_gemini_key.local/` |
| OAuth | `GOOGLE_OAUTH_*` `LINE_LOGIN_*` | 生产 systemd |
| LINE Bot | `LINE_CHANNEL_*` | 生产 systemd |
| 邮件 | `SMTP_*` `RESEND_API_KEY` | 生产 systemd |
| Xero | `XERO_CLIENT_*` | 生产 systemd |
| SlipOK | `SLIPOK_*` | 生产 systemd |
| MR.ERP 探测 | `MRERP_*` | `.env.local` |

> 非密钥的配置项(`OCR_MAX_PAGES_PER_UPLOAD` / `CONTACT_PHONE` 等)
> 可留代码默认或进 Doppler 普通变量 · 不强制。

---

## 后续

- A4 落地后 · A 阶段(工具链)10/10 收官。
- key 轮换流程文档化 → H6(API key 轮换)直接受益。
