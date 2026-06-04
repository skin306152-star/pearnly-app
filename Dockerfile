# ============================================================
# Pearnly · 应用镜像(REFACTOR-A3 · 环境分级 prod/staging/dev)
# ============================================================
# 目标:把 prod 同款运行环境容器化 · 本地能完整跑一遍再 push。
# 不碰生产部署链(git-deploy.sh / webhook)· prod 仍是 git pull + systemctl。
# 本镜像只供 本地 staging / dev 用(docker compose)· 与 CI 装依赖方式一致。
#
# Python 版本与 CI 对齐(.github/workflows/ci.yml · 3.11)· lock 文件由
# pip-compile 在 3.10 生成 · CI 用 3.11 装且全绿 · 这里沿用 3.11。
#
# 体积:2026-06-04 删 easyocr 死栈(全仓库零 import · 经它拽进 torch/torchvision/
#    opencv/scipy/numpy 整棵 ML 栈)→ 镜像 5-7 GB 降到数百 MB。OCR 走 Gemini 云端。
# 现存依赖全是 manylinux 预编译 wheel(lxml/pillow/cryptography/psycopg2-binary 等
#    自带运行时库)· 无需任何系统 apt 包 · 也无需编译工具链。
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# ── 依赖层(单独 COPY · 利用 Docker layer cache · 改代码不重装依赖)──
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt

# ── 应用代码 ────────────────────────────────────────────────
# .dockerignore 已排除 node_modules / _pkg / 本地样本 / 缓存等。
# static/dist/main.js(Vite 产物 · A1)已 commit 在仓库 · 随 COPY 进镜像 ·
# 因此镜像内不需要 Node。
COPY . .

# ── prod 同款:home.* → static/ ─────────────────────────────
# 生产 git-deploy.sh 部署后会 cp home.* 到 static/ · 这里 build 时做掉 ·
# 让运行期 static/home.html 等可被读到(_read_frontend_version 等用)。
RUN cp home.html home.js home.css static/

# ── playwright chromium(MR.ERP 集成 · 默认不装 · 体积大)────
# prod 是通过 /internal/install-playwright 端点单独装。本地若要测 ERP 推送 ·
# 进容器跑:python -m playwright install --with-deps chromium
# 或在下面解开注释重 build。
# RUN python -m playwright install --with-deps chromium

# ── 运行期 ──────────────────────────────────────────────────
ENV PORT=7860 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
EXPOSE 7860

# 生产模式:不开 --reload(app.py __main__ 里的 reload=True 仅供裸跑调试)。
# dev 环境在 docker-compose.dev 用 command 覆盖开 --reload。
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
