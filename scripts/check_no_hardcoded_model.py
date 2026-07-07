#!/usr/bin/env python3
"""闸-Q4:业务逻辑里禁止硬编码大模型名(依赖倒置 CQ-1 的机械部分)。

模型名(claude-*/gemini-N/gpt-N)只允许出现在【网关 / 模型选择 / 路由配置 / 测试】里;
业务逻辑一旦写死具体模型 = 换大脑要改一堆地方 = 违反依赖倒置。

用法:
    python scripts/check_no_hardcoded_model.py           # warn:列违规,exit 0(默认·存量未清完前用)
    python scripts/check_no_hardcoded_model.py --fail     # 硬门:有违规 exit 1(存量清完后切)

设计见 docs/CODE_QUALITY_CANON.md 闸-Q4。白名单 = 模型名合法归属地。
"""

from __future__ import annotations

import argparse
import os
import re
import sys

try:  # Windows 控制台默认非 UTF-8(cp874/GBK)· 强制 UTF-8 防中文崩
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 模型名合法归属地:网关 / 中心化模型选择 / 路由矩阵 / 成本价表 / 引擎档位策略。
ALLOW = (
    os.path.join("services", "ai_gateway"),  # 供应商适配 + 路由矩阵 = 抽象层本身
    os.path.join("services", "ocr", "gemini_models.py"),  # 中心化模型选择
    os.path.join("services", "ocr", "cost.py"),  # 官方单价表(按模型名计价)
    os.path.join("services", "ocr", "engine_policy.py"),  # OCR_MODE→模型档位策略
    os.path.join("scripts", "agent_brain_ab.py"),  # A/B 工具:本就要点名对比模型
)

# 只扫业务代码目录(测试天然引用模型名,不算违规)。
SCAN_DIRS = ("services", "routes", "core")

MODEL_RE = re.compile(
    r"""(['"])(?:
        claude-(?:opus|sonnet|haiku|fable)[\w.\-]* |
        claude-[0-9][\w.\-]* |
        gemini-[0-9][\w.\-]* |
        gpt-[0-9o][\w.\-]*
    )\1""",
    re.VERBOSE,
)


def _allowed(rel: str) -> bool:
    # 白名单条目既有文件也有目录:文件走精确匹配,目录走「前缀 + 分隔符」(不误放同前缀邻居)。
    return any(rel == a or rel.startswith(a + os.sep) for a in ALLOW)


def scan() -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for d in SCAN_DIRS:
        for dirpath, _, files in os.walk(os.path.join(ROOT, d)):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT)
                if _allowed(rel):
                    continue
                try:
                    lines = open(full, encoding="utf-8").read().splitlines()
                except (OSError, UnicodeDecodeError):
                    continue
                for i, line in enumerate(lines, 1):
                    if MODEL_RE.search(line):
                        hits.append((rel, i, line.strip()[:100]))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail", action="store_true", help="有违规则 exit 1(存量清完后切硬门)")
    args = ap.parse_args()

    hits = scan()
    if not hits:
        print("check_no_hardcoded_model: OK(业务逻辑无硬编码模型名)")
        return 0

    print(f"check_no_hardcoded_model: {len(hits)} 处硬编码模型名(应走 gemini_models/gateway):")
    for rel, ln, txt in hits:
        print(f"  {rel}:{ln}: {txt}")
    print("\n修法:模型名从 services.ocr.gemini_models 或 ai_gateway 取,别写死进业务逻辑。")
    if args.fail:
        return 1
    print("(warn 模式:暂不拦。存量清完后在 CI 加 --fail 切硬门。见 docs/CODE_QUALITY_CANON.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
