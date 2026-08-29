# -*- coding: utf-8 -*-
"""CI workflow 结构契约(2026-08-26 拆 unit/e2e + 精确部署 job)。

防未来回归把拆分并回去 / deploy job 条件漂掉 / 秘密换成别的名字:
  · unit 与 e2e 必须并存(并行 · 谁也不吞谁)
  · deploy job 只跑 push 到 master · needs = 全部 FAIL 闸 + unit/e2e/pg-smoke ·
    不含 WARN 闸(lint-routes / lint-model)
  · deploy 调 /internal/deploy/manual 必须带 sha=${{ github.sha }} + secrets.DEPLOY_TOKEN
  · concurrency 必须 cancel-in-progress(同 ref 新 push 取消旧 run → 旧 deploy job 不触发)
  · push diff 闸只拉最近 2 commit;PR 保留全历史拿 origin/base,避免 243MB 全历史 fetch 超时
  · Playwright retries 不允许在这轮迁移里被调低(迁移纪律:不动 E2E 稳定性参数)

本契约故意用纯文本断言(不依赖 PyYAML):CI unit job 不装 pyyaml,测试若 import yaml
会在干净 runner 上 ModuleNotFoundError —— 那比被测的问题先红,契约本身就不诚实。
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WF_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PW_CONFIG_PATH = REPO_ROOT / "playwright.config.js"

FAIL_JOBS = {
    "lint",
    "lint-size",
    "lint-ui",
    "lint-guide",
    "lint-debt",
    "lint-agent",
    "pg-smoke",
}
WARN_JOBS = {"lint-routes", "lint-model"}


def _jobs_block(text: str) -> dict[str, str]:
    """把每个 job 的原始文本块抽出来(key → 该 key 行到下一 job 之间的文本)。"""
    lines = text.splitlines()
    jobs: dict[str, str] = {}
    start = None
    current = None
    for i, line in enumerate(lines):
        m = re.match(r"^  ([A-Za-z][A-Za-z0-9_-]*):\s*(#.*)?$", line)
        if m:
            if current:
                jobs[current] = "\n".join(lines[start:i])
            current = m.group(1)
            start = i
    if current:
        jobs[current] = "\n".join(lines[start:])
    return jobs


def _block_needs(block: str) -> list[str]:
    """取 job 文本块里 needs: 后的 job 名列表。"""
    m = re.search(r"^    needs:\s*$", block, re.M)
    if not m:
        return []
    items = []
    for line in block[m.end() :].splitlines():
        if not line.strip():
            continue
        line = line.strip()
        if not line.startswith("- "):
            break
        items.append(line[len("- ") :].strip())
    return items


class CiWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WF_PATH.read_text(encoding="utf-8")
        cls.jobs = _jobs_block(cls.text)

    def test_unit_and_e2e_jobs_both_exist(self):
        # 拆分必须并存:unit(单元/构建)与 e2e(Playwright)并行 · 谁也不吞谁
        for name in ("unit", "e2e"):
            self.assertIn(name, self.jobs, f"job '{name}' missing from ci.yml")

    def test_unit_job_keeps_full_unit_coverage(self):
        self.assertIn("coverage run -m unittest discover -s tests/unit -p", self.jobs["unit"])
        self.assertIn("coverage report --fail-under=40", self.jobs["unit"])

    def test_unit_job_keeps_vite_build_and_dist_gates(self):
        self.assertIn("npm run build", self.jobs["unit"])
        self.assertIn("git diff --exit-code static/dist/", self.jobs["unit"])
        self.assertIn("check_asset_bundling", self.jobs["unit"])

    def test_e2e_job_keeps_smoke_and_high_sensitive(self):
        self.assertIn("npx playwright test", self.jobs["e2e"])
        self.assertIn("11-billing-security.spec.js", self.jobs["e2e"])
        self.assertIn("12-rls-isolation.spec.js", self.jobs["e2e"])
        self.assertIn("26-entrance-token-isolation.spec.js", self.jobs["e2e"])
        self.assertIn("PEARNLY_E2E_USER", self.jobs["e2e"])

    def test_e2e_job_installs_app_python_deps(self):
        # 2026-08-25 拆 job 踩的坑:e2e 只装 python 没装应用依赖,ps5_cashier_route 等本地
        # spec 起 `python -m uvicorn app:app` 全量导入直接 "server not up" 全红。本地 spec
        # spawn 真 FastAPI app 是 e2e 的显式依赖 —— 拆/改 job 时不许再丢锁文件安装。
        e2e = self.jobs["e2e"]
        self.assertIn("pip install -r requirements.lock.txt", e2e)
        self.assertIn("cache: pip", e2e)
        self.assertIn("cache-dependency-path: requirements.lock.txt", e2e)

    def test_e2e_job_installs_cross_platform_browser_engines(self):
        e2e = self.jobs["e2e"]
        self.assertIn("playwright install chromium webkit firefox", e2e)
        self.assertIn("playwright install-deps chromium webkit firefox", e2e)
        self.assertIn("playwright-all-browsers-v1-", e2e)

    def test_deploy_job_exists_and_master_only(self):
        self.assertIn("deploy", self.jobs)
        deploy = self.jobs["deploy"]
        self.assertIn(
            "if: github.event_name == 'push' && github.ref == 'refs/heads/master'",
            deploy,
        )

    def test_deploy_needs_all_fail_jobs_plus_unit_e2e_pg(self):
        need = set(_block_needs(self.jobs["deploy"]))
        self.assertEqual(need, FAIL_JOBS | {"unit", "e2e"}, "deploy needs 集合漂了")

    def test_deploy_needs_excludes_warn_jobs(self):
        need = set(_block_needs(self.jobs["deploy"]))
        self.assertFalse(WARN_JOBS & need, "deploy 不该 depends on WARN 闸(lint-routes/lint-model)")

    def test_deploy_calls_manual_with_pinned_sha_and_token(self):
        deploy = self.jobs["deploy"]
        self.assertIn("/internal/deploy/manual?sha=${{ github.sha }}", deploy)
        self.assertIn("X-Internal-Token: ${{ secrets.DEPLOY_TOKEN }}", deploy)

    def test_concurrency_cancels_older_master_runs(self):
        self.assertIn("cancel-in-progress: true", self.text)
        self.assertIn("${{ github.workflow }}-${{ github.ref }}", self.text)

    def test_push_diff_jobs_do_not_fetch_full_history(self):
        conditional_depth = "github.event_name == 'pull_request' && '0' || '2'"
        for name in ("lint-size", "lint-debt", "lint-routes"):
            self.assertIn(conditional_depth, self.jobs[name], f"{name} push 应只拉 2 个 commit")
        self.assertIn("fetch-depth: 2", self.jobs["unit"])

    def test_playwright_retries_not_reduced(self):
        # 迁移纪律:不动 E2E 稳定性参数 —— CI retries 必须是 2(迁移前原值)
        cfg = PW_CONFIG_PATH.read_text(encoding="utf-8")
        self.assertIn("retries: IS_CI ? 2 : 0", cfg)


if __name__ == "__main__":
    unittest.main()
