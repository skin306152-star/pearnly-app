# ADR-003 · 本地 Docker 做环境分级(不开第二台 Vultr)

> **状态**:已采纳(2026-05-24 · Zihao 拍板)
> **关联 task**:REFACTOR-A3(环境分级 prod / staging / dev)
> **关联铁律**:#21(整改期不污染未来整顿)· 8 硬门槛 #7(/ready 真实失败 · B4 落地)

---

## 背景

整顿前 Pearnly 只有一套环境:`git push origin master` → webhook 直接上生产。
没有缓冲区 —— 任何改动只能在 prod 上验证,风险高。A3 目标是补上
**prod / staging / dev 三级**,让改动在上生产前能在隔离环境完整跑一遍。

## 决策

**用本地 Docker 做 staging / dev,不开第二台 Vultr。**

| 方案 | 取舍 | 结论 |
|---|---|---|
| 开第二台 Vultr | ~$6-12/月 · 真远程 staging · **但要改 git-deploy/webhook(碰红线)+ 维护两套环境** | ❌ 对单人项目偏重 |
| **本地 Docker** | 免费 · 把 prod 同款环境容器化 · 本地完整跑一遍再 push · **不碰生产部署链** | ✅ 选这个 |

**prod 部署链完全不动**:生产仍是真服务器(45.76.53.194)git pull + `systemctl restart mrpilot`。
Docker 只服务本地 staging / dev。

## 落地交付

| 文件 | 作用 |
|---|---|
| `Dockerfile` | python:3.11-slim(与 CI 对齐)+ lock 依赖 + prod 同款 `cp home.* static/` |
| `.dockerignore` | 缩小 build context · 排除密钥 / 缓存 / 样本 / node_modules |
| `docker-compose.yml` | staging:app(build)+ 本地 PostgreSQL 16 · 生产同款不热重载 |
| `docker-compose.dev.yml` | dev override:挂源码 + uvicorn `--reload` |

## 三环境对照

| 环境 | 在哪 | DB | 部署方式 | 用途 |
|---|---|---|---|---|
| **prod** | Vultr 45.76.53.194 | Supabase | git push → webhook → systemctl | 真用户 |
| **staging** | 本地 Docker | 容器内 postgres | `docker compose up --build` | push 前完整验证 |
| **dev** | 本地 Docker | 容器内 postgres | `docker compose -f ... -f docker-compose.dev.yml up` | 改代码热重载调试 |

---

## 用法

### 首次准备

```powershell
# 1. 装 Docker Desktop(Windows 10 Home · WSL2 backend · 已有 wsl)
#    https://www.docker.com/products/docker-desktop/
# 2. 准备本地环境变量(真实第三方密钥从这里带入容器)
copy .env.example .env.local
#    填 GEMINI_API_KEY / JWT_SECRET / PEARNLY_KMS_KEY 等(DATABASE_URL 不用填 · compose 会覆盖)
```

### staging(生产同款 · 不热重载)

```powershell
docker compose up --build
# 访问 http://localhost:7860
```

### dev(挂源码 + 热重载)

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
# 改 .py 立即生效;改 home.* 后:
docker compose exec app cp home.html home.js home.css static/
```

### 关掉 / 清数据

```powershell
docker compose down            # 停容器(保留 DB 数据卷)
docker compose down -v         # 连数据卷一起删(重置本地 DB)
```

---

## ✅ 验证清单(装好 Docker Desktop 后跑一遍 · A3 完成判定)

> 本机当前未装 Docker · 以下未验证 · Zihao 装 Docker Desktop 后逐项跑。
> 任一步失败 → 贴报错 · 我接着调。

- [ ] `docker compose config` —— compose 语法无误(秒级 · 不 build)
- [ ] `docker compose build` —— 镜像能构建(首次慢 · 见下方"已知坑")
- [ ] `docker compose up` 后 `curl http://localhost:7860/api/version` 返 JSON
- [ ] 容器内 `import app` 不崩(`docker compose exec app python -c "import app"`)
- [ ] postgres 起来(`docker compose exec db pg_isready -U pearnly`)
- [ ] dev override 热重载:改一行 .py · 看日志是否 reload

---

## ⚠️ 已知坑 / 约束

1. **镜像大(~5-7 GB)**:依赖含 `torch / torchvision / easyocr / opencv / scipy` ML 栈 ·
   首次 build 要下载数 GB · 慢属正常。这是 OCR 引擎的代价 · 与 prod 一致。
2. **CPU torch 减体积(可选进阶)**:lock 钉死 `torch==2.12.0`(PyPI manylinux 含 CUDA)。
   若要瘦身可改用 PyTorch CPU index(`https://download.pytorch.org/whl/cpu`)·
   但 CPU wheel 版本号带 `+cpu` 后缀 · 与 lock pin 不完全匹配 · 需单独处理 ·
   暂不做(CI 已验证 CUDA 版能跑 CPU 推理)。
3. **playwright chromium 默认不装**:MR.ERP 集成需要 · 与 prod 一致(prod 走
   `/internal/install-playwright` 单独装)。本地要测 ERP 推送:
   `docker compose exec app python -m playwright install --with-deps chromium`。
4. **不在 CI 加 docker build**:首次 build 下载数 GB · 每次 CI 跑会爆配额 + 拖慢 ·
   故 docker 验证留本地手动(本清单)· CI 仍是 import/i18n/unit/vite/e2e 五关。
5. **Python 版本**:Dockerfile 用 3.11(与 CI 对齐)· 本机是 3.10 · lock 由 3.10 生成 ·
   CI 用 3.11 装 lock 且全绿 · 故镜像沿用 3.11。

---

## 后续

- B4(`/health` + `/ready`)落地后 · 本地 Docker 可直接验证 `/ready` 真实失败
  (停掉 db 容器看 `/ready` 是否返非 200)· 正好落实硬门槛 #7。
- 真要远程 staging(多人协作时)再评估开第二台 Vultr · 届时改 git-deploy 走流程。
