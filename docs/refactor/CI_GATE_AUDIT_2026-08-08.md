# CI Gate Audit · 2026-08-08

## Scope

This audit covers `scripts/git-hooks/pre-push`, `.github/workflows/ci.yml`,
`docs/GATES.md`, and the E2E ledger gate. The objective is to remove repeated
work without weakening the rule that a bad commit must not reach `master`.

## Decisions

| Area | Local hook | CI | Decision |
|---|---|---|---|
| Python lint, import smoke, unit tests | Changed Python only; `impact.py` targets test-only changes and keeps production Python full | Full repository | Keep both layers. CI is the clean-clone fallback. |
| Frontend lint, build, asset/cache checks | Changed frontend only | Full repository | Keep both layers. A committed dist mismatch must be caught before deployment. |
| File size and line ratchet | Every push | Full history | Keep both. They answer different questions: absolute ceiling vs diff growth. |
| Test git writes and destructive DB tests | Every push | Dedicated CI checks | Keep both. A local test can damage the shared development database before CI starts. |
| Authz, E2E stub contracts, UI/theme gates | Relevant local changes; full CI | Full repository or dedicated job | Keep the CI copy. Local trigger reduction is safe only when the changed-path classifier is tested. |
| E2E ledger completeness | E2E/ledger changes | Unit suite and CI | Keep. `*.spec.js` is now declared in the same ledger as CJS browser checks. |

## Findings

1. **Not every duplicate is waste.** Removing the CI copy because the local hook
   passed would turn `--no-verify`, clean-clone differences, and missing local
   tooling into deployment paths.
2. **The previous waste was unclassified execution.** The hook ran the full unit
   suite for a test-only Python edit even though no production dependency
   changed. `scripts/impact.py` now makes that one safe cut and explicitly
   falls back to full unit for production Python.
3. **The E2E ledger had two different universes.** CJS browser checks were
   declared, while Playwright `*.spec.js` files were not. The ledger now has
   103 spec entries, and `test_e2e_ledger_gate` fails on a missing declaration,
   empty `covers`, or empty `only_e2e`.
4. **E2E execution must not be blindly inserted into pre-push.** Several specs
   require a local database, a real account, or a real backend. The impact
   planner reports the exact spec/CJS set; the responsible verification step
   runs it with the correct environment.

## Deliberately Not Merged

- `check_file_size` and its unit tests are not one gate to delete: the script
  enforces the repository rule, while the tests prove the detector has teeth.
- Screenshot freshness is not enabled for all newly registered specs yet. The
  existing specs do not share one artifact convention, and enabling mtime
  checks before each entry has a unique artifact contract would create false
  reds. This remains a P4 follow-up, not a silent exemption.
- No gate is removed solely because it is fast. Removal requires a measured
  replacement with the same changed-path coverage and a negative test proving
  the gate still fires on a relevant diff.

## Acceptance Status

- P1 planner and ledger selection: implemented and covered by unit tests.
- P2 stale bytecode cleanup: implemented and covered by hook environment tests.
- P3 simplify, re-verification, and push-train rules: written into the existing
  skills.
- P4 audit: this report is complete; gate deletion is intentionally not claimed.
- The `<=30 minute` end-to-end closeout target is not yet proven. It needs one
  committed strong-intensity day measured from task completion through green CI.

## Verification Snapshot

- Focused P1/P2 regression set: **88 tests passed** after the final hook wiring.
- Full local shard run: **1120 modules / 6 shards · green in 307s**. The only
  red was a Windows runtime-selection defect: `shutil.which("bash")` resolved
  the dead WSL launcher instead of installed Git Bash. The test now probes and
  selects a runnable Git Bash on Windows; `tests.unit.test_ops_backup` is 9/9.
- Direct shell, JSON, Black, Ruff, file-size, git-write, destructive-DB,
  E2E-stub, authz, and ledger checks passed. The uncommitted new files are not
  yet in `HEAD`, so clean-clone tracked-import validation must be repeated after
  the batch is committed.
