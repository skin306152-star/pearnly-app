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

## 📍 迁移进度(单一权威源 · 防删错)

**4 步顺序迁移 · 绝不能跳到第 4 步清理**(否则 Doppler 还没接管 · 服务读不到密钥 → 网站挂 → 付费用户受影响):

| 步 | 做什么 | 状态 |
|---|---|---|
| 1️⃣ 收拢 | 生产 39 条密钥导入 Doppler `prd` config | ✅ 2026-05-24 完成 |
| 2️⃣ 验证本地 | 装 doppler CLI · 本地 `doppler run` 跑通应用 | ⏳ 待做 |
| 3️⃣ 验证生产 | 服务器改从 Doppler 取(**动 systemd 启动 = 碰红线 #16 · 必走流程问 Zihao**) | ⏳ 待做 |
| 4️⃣ 清理旧的 | 两边跑通后**才**删:服务器 `/opt/mrpilot/.env` + 本地 `_gemini_key.local/` + `.env.local` 的 MRERP(**删前先备份**) | ⏳ 待做 · ⛔ 不可提前 |

**已收拢的 39 条**(2026-05-24 · 导入 `prd`):DATABASE_URL / GEMINI_API_KEY / JWT_SECRET / PEARNLY_KMS_KEY /
GITHUB_WEBHOOK_SECRET / EMAIL_ENCRYPTION_KEY / LINE 全套 / SMTP 全套 / Google OAuth / Xero / Supabase /
RESEND / NVIDIA / TYPHOON / GPG / OCR 开关 / MRERP 全套。**剔除了 2 条死代码** demo 账号密码(`db.py`
`ensure_demo_account` 用老套餐模型建 · 已登不上 · 待整顿 I2 单独铲)。

**Doppler 账号**:Developer(个人免费)· project `pearnly` · 三环境 config `dev`/`stg`/`prd` · 生产密钥放 `prd`。

> ⚠️ 桌面导入用的明文临时文件(`pearnly_secrets_TEMP.env` / `pearnly_doppler_import.env`)已于
> 2026-05-24 导入成功后删除 · 明文密钥不留本地。

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
