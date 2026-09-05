# OCR integration — active work, not released

## Scope and latest constraint

User authorized implementation after Cloud Run migration. B keeps 3.1 Flash-Lite and replaces OCR 3.5 upgrade arms with 3.8 Flash LOW. A uses Enterprise OCR and tested local reconstruction / pinned image-schema processing; no extra 3.1 layer. Admin engine page is in scope.

Latest instruction: fastest targeted validation only; do not enlarge the test corpus or run unnecessary/full-repository tests. Reuse passed evidence. No additional paid calls are needed for the current local integration checks.

## Workspace

- Worktree: `/Users/skin/Developer/Pearnly/pearnly-ocr-integration`
- Branch: `codex/ocr-enterprise-integration`, base `534e2fbd`.
- Changes are uncommitted. Nothing pushed, deployed, or switched in production.
- Main workspace has unrelated changes; do not touch them.
- `node_modules` is a task-created symlink to the main workspace dependencies, not a source artifact to commit.

## Implemented candidate code

- Frozen evaluation schemas/prompts in `enterprise_contract.py`, shared request builder and hashes.
- Document AI provider pins `pretrained-ocr-v2.1.1-2025-01-31`; no premium OCR switches. The existing processor's default is v1.0, so never call its unversioned endpoint.
- Raw geometry is retained. Local bank/GL parsers were extracted from the pilot without presets or gold answers.
- Reconstruction checks page coverage, arithmetic, cross-page boundaries and bank date-anchor counts. Arithmetic consistency is NOT transcription accuracy. Local repairs retain review/audit metadata.
- Shared PostgreSQL request spacing uses namespaced rows in existing `cloud_task_locks`, defaults to 9 requests/minute. No new schema, no per-process quota fallback.
- Metered OCR reader estimates paid basic cost without free tier/credits. Queue time is separate from provider time.
- Candidate Enterprise pipeline: OCR once per chunk (maximum 15 pages); local bank/GL schema when arithmetic passes; otherwise frozen original-image + transcript + 3.8 LOW per page. Provider failure does not silently invoke the old prompt path.
- Pipeline integration for explicit Enterprise bank/GL/VAT types; refuses silently truncated PDFs.
- Dedicated recon adapter consumes all pages and does not apply the legacy balance repair again. Bank/GL impl entrypoints call it when explicitly selected.
- Legacy ParsedStatement PDF dispatch and multipage adapter now preserve all pages, final closing balance and review/audit. GL-VAT PDF flavor is connected to the candidate pipeline without old-prompt fallback on failure.
- Nested usage contexts retain an already-consumed page slot, preventing a fallback from counting the same document pages twice.
- VAT image/scanned-PDF branch can consume the same candidate pipeline; successful native table parsing stays native.
- B economy map now explicitly pins all upgrade/flash arms to 3.8 and first read to 3.1-lite. Agent defaults not changed.
- Vertex 3.8 is pinned global/LOW for text and vision. Usage includes thoughts and preceding failed parse attempts. MAX_TOKENS cannot be accepted as successful JSON.
- Admin reads resolved current-service model configuration rather than static model strings. Stale hardcoded metric numbers are not displayed. P50 is labeled provider-call latency, not whole-document latency. Chinese/Thai copy and admin built HTML updated.

`enterprise` is now selectable after adapter completion. Existing `direct35` configuration has NOT been reinterpreted or replaced in the DB. Production selection must be switched only after both new service revisions are ready.

## Latest continuation

- Fileconv financial images/PDFs now share the frozen pipeline; PDF renders at 200 DPI and raw PDF is chunked by 15 pages. Generic grids and ID cards keep their specialized schemas on 3.8, not financial schemas. Native structured inputs remain native.
- Nested engine contexts re-resolve a different task and restore the outer selection; same-task nesting retains plan context. Regression test passes.
- Backend admin snapshot now resolves actual global backend, not the routing matrix default label. Task effective selections are shown; obsolete bank 3.5 benchmark hint removed.
- Targeted policy/fileconv/admin checks: 91 passed; after helper extraction, fileconv 20 passed. No new cloud OCR calls.
- Browser actual built admin shell with real backend policy snapshot and mocked authentication/cost API: Chinese rendering and actual Thai language selection passed; Vertex LOW labels checked. Screenshots stay local under tests/e2e/_artifacts/ocr-integration. Not production authentication acceptance.
- Existing saved bank/GL parity evidence above reused. Cloud IAM/config and release remain pending; no production switch yet.

## Evidence obtained

- Cached pilot parity: bank 18 pages / 761 rows, GL 7 pages / 403 rows. Schema and audit exactly match old saved results.
- New recon adapter using cached OCR + actual PDF rendering: 761/403 rows, aggregate debit/credit or deposit/withdrawal, opening/closing balances match; review audit retained. No cloud calls for this check.
- Live pinned Document AI call with local gcloud user identity: 3-page saved bank PDF, success, 13.19 seconds. This was connectivity evidence, not Worker acceptance or new gold accuracy.
- Live frozen schema call with local user identity: original IMG_2575 + matching saved OCR transcript, Gemini 3.8 Flash LOW success, 5474 ms, 2718 input and 457 billed output tokens. No application billing writes.
- New core tests: request/quota guards/pipeline adapter 15 passed; Vertex 3.8 tests passed as part of targeted run.
- Existing model/routing regression set: 72 passed before adding candidate mode; changed routing set subsequently 59 passed.
- Latest targeted admin/API/pipeline/VAT set: 60 passed in 0.636 seconds after fixes.
- Real disposable PostgreSQL: eight concurrent reservations share exactly one slot; separate quota key independent; expired slot usable. Passed, no production DB touched.
- Black and Ruff on task Python files passed before the most recent adapter/UI edits; final changed-file formatting still required.
- `npm run build` passed; only generated tracked change is `static/dist/admin.html`.
- `git diff --check` passed. Real browser UI acceptance not yet performed.
- After the user's speed constraint: reused prior checks; targeted updated admin/API/pipeline/VAT set passed (60); new recon adapter cached check passed (761/403 rows and money); usage-context checks passed (22 in 0.002s); legacy 2-page rows/balances/audit assertion passed. No additional paid requests.
- The task-owned disposable PostgreSQL container was stopped and automatically removed; no customer data was involved.

## Runtime/IAM findings

- Cloud Run Worker observed revision: `pearnly-worker-674909a0bd51-s1`.
- Worker SA: `pearnly-worker@pearnly.iam.gserviceaccount.com`.
- Project-level worker bindings observed: aiplatform.user and cloudtasks.enqueuer; no Document AI API role seen. This is a permission gap to verify, not a proved worker 403.
- Local ADC absent. Existing local user gcloud credential can call both providers without persisting credentials.
- Local worker impersonation unavailable. No IAM policy was changed.
- Processor: project `pearnly` / `asia-southeast1` / `6c7dfffac937fcd9`, enabled; pin version above. Production Enterprise environment has not been set.
- `roles/documentai.apiUser` was inspected read-only and includes processor/version processOnline and processBatch permissions.
- Runtime admin snapshot explicitly describes the current service, NOT independently verified Worker configuration.

## Required remaining implementation, not optional extra testing

1. Evaluate remaining fileconv/id-card/Sales VAT-specific boundaries from the preflight before selecting their new policies. Legacy ParsedStatement and GL-VAT adapter code is now connected, but not production-accepted. Do not claim all entrances are switched.
2. Ensure review/audit reaches each final consumer rather than only intermediate result dicts. Resolve nested engine contexts and cache version behavior where necessary.
3. Verify B's real fallback wiring uses the new LOW provider path; avoid accidentally changing Agent or a legacy AI Studio path without corresponding config support.
4. Complete admin effective task mapping and actual Worker/source scope. One focused browser verification, not a broad UI suite.
5. Confirm/configure Worker Document AI permissions and Enterprise environment as part of authorized release. No credentials in reports or logs.
6. Targeted checks on newly changed paths only, then release preparation per Cloud Run docs. No shadow/gray traffic or expanded corpus. Do not bypass mandatory push/release gates.

No full OCR completion, production acceptance, or user acceptance is claimed.
