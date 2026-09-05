# -*- coding: utf-8 -*-
"""部署流程文档契约(2026-08-27 · 防换窗口回退旧部署流程)。

锁住当前 Cloud Run 部署入口与保留的历史操作文档口径,防止新窗口无意中恢复已废弃的流程:
  · 禁止旧东京 IP 45.76.53.194 作为可执行 SSH 目标(历史警告语境放行)
  · 禁止可复制的 webhook active=true 复启命令(历史说明放行)
  · 禁止不带参数的 git-deploy.sh 调用(必须带 SHA)
  · 当前入口必须指向迁移状态与 Cloud Run 正本，保留候选镜像、readiness、流量回读门槛
  · 当前运维与验收文档不得保留可执行旧VM上线/诊断命令

扫描范围仅限活跃文档;archive/history/legacy 路径自动跳过。
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

ACTIVE_DOCS = {
    "SKILL.md": REPO_ROOT / ".agents" / "skills" / "deploy-release" / "SKILL.md",
    "DEBUG_SKILL.md": REPO_ROOT / ".agents" / "skills" / "debug-prod-500" / "SKILL.md",
    "RUNBOOK.md": REPO_ROOT / "docs" / "RUNBOOK.md",
    "CLOUD_RUN.md": REPO_ROOT / "docs" / "deployment" / "CLOUD_RUN.md",
    "TASK_MODES.md": REPO_ROOT / "docs" / "agent" / "TASK_MODES.md",
    "ACCEPTANCE_PLAYBOOKS.md": REPO_ROOT / "docs" / "agent" / "ACCEPTANCE_PLAYBOOKS.md",
    "AGENTS.md": REPO_ROOT / "AGENTS.md",
}

OLD_TOKYO_IP = "45.76.53.194"


def _read_doc(name: str) -> str:
    path = ACTIVE_DOCS[name]
    return path.read_text(encoding="utf-8")


class DeployProcessContractTests(unittest.TestCase):
    """机械契约:活跃部署文档不得回退到旧流程。"""

    @classmethod
    def setUpClass(cls):
        cls.docs = {name: _read_doc(name) for name in ACTIVE_DOCS}

    # ── 1. 禁止旧东京 IP 作为可执行 SSH 目标 ──────────────────────

    def test_no_old_tokyo_ip_as_ssh_target(self):
        """旧 IP 不能出现在 ssh 命令行里(历史警告语境如'别再往那台推'放行)。"""
        ssh_with_old_ip = re.compile(r"ssh\s+(?:root@)?" + re.escape(OLD_TOKYO_IP))
        for name, text in self.docs.items():
            matches = ssh_with_old_ip.findall(text)
            self.assertEqual(
                len(matches),
                0,
                f"{name}: 发现可执行的旧东京 IP SSH 命令: {matches}",
            )

    # ── 2. 禁止可复制的 webhook active=true 复启命令 ────────────────

    def test_no_executable_webhook_reenable_command(self):
        """不允许出现可直接复制执行的 webhook active=true 命令。

        历史说明(如 'active=false' / '已停用' / '永久停用')放行;
        只拦 active=true 这种可执行的复启动作。
        """
        webhook_active_true = re.compile(
            r"gh\s+api.*hooks/\d+.*-F\s+active=true",
            re.IGNORECASE,
        )
        for name, text in self.docs.items():
            matches = webhook_active_true.findall(text)
            self.assertEqual(
                len(matches),
                0,
                f"{name}: 发现可复制的 webhook 复启命令(active=true): {matches}",
            )

    # ── 3. 禁止不带参数的 git-deploy.sh ──────────────────────────

    def test_no_bare_git_deploy_sh_without_sha(self):
        """git-deploy.sh 必须带 SHA 参数;禁止裸调或暗示'不带 sha'是有效选项。

        允许的语境:
          · git-deploy.sh <40-hex-SHA> / git-deploy.sh $1 / git-deploy.sh TARGET_SHA
          · 明确标注'禁止不带 SHA'的说明文字
        禁止的语境:
          · bash /opt/mrpilot/git-deploy.sh (后面没跟参数或占位符)
          · '不带 sha = ...旧语义' 当作有效选项描述(非禁止说明)
        """
        bare_invoke = re.compile(
            r"bash\s+/opt/mrpilot/git-deploy\.sh\s*(?:>>|$|\s*[^<\$\w])",
            re.MULTILINE,
        )
        for name, text in self.docs.items():
            for m in bare_invoke.finditer(text):
                context_start = max(0, m.start() - 40)
                context_end = min(len(text), m.end() + 40)
                context = text[context_start:context_end].replace("\n", " ")
                if "禁止" in context or "**禁止" in context:
                    continue
                self.fail(f"{name}: 发现不带 SHA 的 git-deploy.sh 调用: ...{context}...")

    def test_no_old_semantics_without_sha_as_valid_option(self):
        """'不带 sha = 部署当前 master 的旧语义' 不能作为有效选项呈现。"""
        old_semantics_as_option = re.compile(
            r"不带\s*sha\s*=\s*部署当前\s*master",
            re.IGNORECASE,
        )
        for name, text in self.docs.items():
            matches = old_semantics_as_option.findall(text)
            self.assertEqual(
                len(matches),
                0,
                f"{name}: '不带 sha' 仍被描述为有效选项: {matches}",
            )

    # ── 4. canonical 流程关键字必须存在 ───────────────────────────

    def test_skill_uses_current_cloud_run_workflow_and_retains_release_gates(self):
        text = self.docs["SKILL.md"]
        for required in (
            "docs/deployment/MIGRATION_STATUS.md",
            "docs/deployment/CLOUD_RUN.md",
            "镜像 digest",
            "readiness",
            "流量",
            "真机",
        ):
            self.assertIn(required, text)
        self.assertIn("发布流程已退役", text)
        canonical = self.docs["CLOUD_RUN.md"]
        for required in ("manual-deploy.yml", "Workload Identity Federation", "Artifact Registry"):
            self.assertIn(required, canonical)
        self.assertNotRegex(text, r"gh\s+api[^\n]*/internal/deploy/manual")

    def test_runbook_has_sha_verification(self):
        text = self.docs["RUNBOOK.md"]
        self.assertIn("rev-parse HEAD", text)
        self.assertIn("commits/master --jq .sha", text)
        self.assertIn("status.latestReadyRevisionName,status.traffic", text)

    def test_acceptance_playbooks_has_sha_verification(self):
        text = self.docs["ACCEPTANCE_PLAYBOOKS.md"]
        self.assertIn("rev-parse HEAD", text)
        self.assertIn("--project=pearnly", text)

    def test_task_modes_uses_current_cloud_diagnostics(self):
        self.assertIn("生产诊断技能", self.docs["TASK_MODES.md"])
        text = self.docs["DEBUG_SKILL.md"]
        self.assertIn("docs/RUNBOOK.md", text)
        self.assertIn("gcloud logging read", self.docs["RUNBOOK.md"])

    def test_agents_md_has_canonical_deploy_chain(self):
        text = self.docs["AGENTS.md"]
        for required in (
            "docs/deployment/MIGRATION_STATUS.md",
            "docs/deployment/CLOUD_RUN.md",
            "Cloud Run",
            "Supabase",
            "ERPNext",
        ):
            self.assertIn(required, text)
        canonical = self.docs["CLOUD_RUN.md"]
        for required in (
            "GitHub",
            "Workload Identity Federation",
            "完整 commit SHA",
            "镜像 digest",
            "readiness",
            "再切换流量",
            "Worker",
            "Web",
        ):
            self.assertIn(required, canonical)
        self.assertIn("历史版本", self.docs["RUNBOOK.md"])

    def test_agents_md_references_deploy_skill(self):
        self.assertIn(".agents/skills/deploy-release/SKILL.md", self.docs["AGENTS.md"])

    def test_current_runbooks_never_send_work_to_the_retired_vm(self):
        for name in ("RUNBOOK.md", "TASK_MODES.md", "ACCEPTANCE_PLAYBOOKS.md"):
            self.assertNotRegex(self.docs[name], r"ssh\s+pearnly-prod")
            self.assertNotRegex(self.docs[name], r"systemctl\s+(restart|start)\s+mrpilot")
        self.assertIn("失败不得手工跳过门禁来切流", self.docs["RUNBOOK.md"])

    # ── 6. 所有活跃文档不含旧 IP 作为当前服务器地址 ────────────────

    def test_no_old_ip_as_current_server(self):
        """旧 IP 不能在'服务器 ='/'server:'等当前定义语境中出现。"""
        current_server_pattern = re.compile(
            r"(?:服务器|server|host)\s*[:=]\s*.*" + re.escape(OLD_TOKYO_IP),
            re.IGNORECASE,
        )
        for name, text in self.docs.items():
            matches = current_server_pattern.findall(text)
            self.assertEqual(
                len(matches),
                0,
                f"{name}: 旧 IP 出现在当前服务器定义中: {matches}",
            )


if __name__ == "__main__":
    unittest.main()
