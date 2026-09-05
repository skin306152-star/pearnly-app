# -*- coding: utf-8 -*-
"""部署流程文档契约(2026-08-27 · 防换窗口回退旧部署流程)。

锁住当前 Cloud Run 部署入口与保留的历史操作文档口径,防止新窗口无意中恢复已废弃的流程:
  · 禁止旧东京 IP 45.76.53.194 作为可执行 SSH 目标(历史警告语境放行)
  · 禁止可复制的 webhook active=true 复启命令(历史说明放行)
  · 禁止不带参数的 git-deploy.sh 调用(必须带 SHA)
  · 当前入口必须指向迁移状态与 Cloud Run 正本，保留候选镜像、readiness、流量回读门槛
  · 历史 VM 手册仍保留精确 SHA 与旧主机诊断约束，不反向要求新发布使用 SSH

扫描范围仅限活跃文档;archive/history/legacy 路径自动跳过。
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

ACTIVE_DOCS = {
    "SKILL.md": REPO_ROOT / ".claude" / "skills" / "deploy-release" / "SKILL.md",
    "RUNBOOK.md": REPO_ROOT / "docs" / "RUNBOOK.md",
    "CLOUD_RUN.md": REPO_ROOT / "docs" / "deployment" / "CLOUD_RUN.md",
    "TASK_MODES.md": REPO_ROOT / "docs" / "agent" / "TASK_MODES.md",
    "ACCEPTANCE_PLAYBOOKS.md": REPO_ROOT / "docs" / "agent" / "ACCEPTANCE_PLAYBOOKS.md",
    "AGENTS.md": REPO_ROOT / "AGENTS.md",
    "CLAUDE.md": REPO_ROOT / "CLAUDE.md" / "CLAUDE.md",
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
            ".github/workflows/manual-deploy.yml",
            "GitHub WIF",
            "Artifact Registry",
            "镜像 digest",
            "readiness",
            "流量",
            "真机",
        ):
            self.assertIn(required, text)
        self.assertIn("同名文件的历史 VM 版本已退役", text)
        self.assertNotRegex(text, r"gh\s+api[^\n]*/internal/deploy/manual")

    def test_runbook_has_sha_verification(self):
        text = self.docs["RUNBOOK.md"]
        self.assertIn("rev-parse HEAD", text)
        self.assertIn("github.sha", text)

    def test_acceptance_playbooks_has_sha_verification(self):
        text = self.docs["ACCEPTANCE_PLAYBOOKS.md"]
        self.assertIn("rev-parse HEAD", text)
        self.assertIn("pearnly-prod", text)

    def test_task_modes_has_pearnly_prod(self):
        text = self.docs["TASK_MODES.md"]
        self.assertIn("pearnly-prod", text)

    def test_agents_md_has_canonical_deploy_chain(self):
        text = self.docs["AGENTS.md"]
        for required in (
            "docs/deployment/MIGRATION_STATUS.md",
            "docs/deployment/CLOUD_RUN.md",
            "Cloud Run",
            "Supabase",
            "ERPNext",
            "revision/digest/流量回读",
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
        self.assertIn("历史 Vultr 单机运维手册", self.docs["RUNBOOK.md"])

    def test_claude_md_references_deploy_skill(self):
        text = self.docs["CLAUDE.md"]
        self.assertIn("deploy-release", text)

    # ── 5. RUNBOOK 紧急部署必须有 Zihao 授权门槛 ──────────────────

    def test_runbook_emergency_requires_zihao_authorization(self):
        text = self.docs["RUNBOOK.md"]
        self.assertIn("Zihao", text)
        emergency_section = text[text.find("紧急时:") :]
        self.assertIn("Zihao", emergency_section[:500])

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
