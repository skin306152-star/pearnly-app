# OCR integration — released 2026-09-05

## Release and scope

- User authorized implementation after Cloud Run migration; latest constraint: reuse evidence, no expanded OCR corpus or unnecessary repeated tests.
- Runtime SHA: `7dc72a7550755d88784f48682854757294bb542e`.
- [Successful release 33974005122](https://github.com/skin306152-star/pearnly-app/actions/runs/33974005122).
- Image digest: `sha256:2fd9ffa9f94a2aabbe126789fa418030fe36c67bd7f3b74ede35e54b9d4b25aa`.
- Web/Worker revisions: `pearnly-web-7dc72a755075-s2` / `pearnly-worker-7dc72a755075-s2`, both 100% traffic.
- Worktree: `/Users/skin/Developer/Pearnly/pearnly-ocr-integration`, branch `codex/ocr-enterprise-integration`. Main workspace and unrelated changes preserved.
- This document-only follow-up does not require another image deployment.

## Active routing

| Task | Active policy and implementation |
|---|---|
| Invoice / purchase / thermal | B economy: original first-read 3.1 Flash-Lite, existing hard-gate upgrade arms now 3.8 Flash LOW |
| Bank / GL images and PDFs | A Enterprise: pinned OCR geometry, tested local reconstruction when checks pass, otherwise frozen original-image plus transcript schema on 3.8 LOW |
| VAT report scans | A Enterprise plus frozen VAT schema on 3.8 LOW |
| ID / SalesVAT invoices / generic fileconv grids | A policy selects 3.8 LOW with specialty schemas; not forced into a bank schema |
| Native CSV / Excel / successfully parsed native tables | Preserve native reading; no gratuitous Document AI call |

A adds no 3.1 layer. Agent model defaults and optional legacy direct35 mode are unchanged. Production stored policy explicitly selects invoice=economy and all seven other registered OCR tasks=enterprise; update at 2026-09-05 15:19:52 UTC was atomic with an operation_logs audit containing old/new policy and release SHA.

## Behavioral safeguards

- Processor `6c7dfffac937fcd9`, project `112074003592`, location `asia-southeast1`, pinned `pretrained-ocr-v2.1.1-2025-01-31`. Its default v1.0 is never used. No premium OCR options.
- Original image and frozen schema/prompt shared with evaluation; PDF 200 DPI rendering and original-PDF chunks up to 15 pages, no silent truncated PDF acceptance.
- Local bank/GL parsers have no benchmark presets/gold answers. Check row/page coverage, arithmetic, direction, cross-page boundaries and printed totals when available.
- Arithmetic consistency is NOT transcription accuracy. Repairs/provenance/review indicators survive recon, legacy, VAT and fileconv adapters. No second legacy balance repair on Enterprise output.
- Provider failures do not silently invoke a different old-prompt pipeline. Native formats retain their own parsers.
- Different nested tasks re-resolve their policy; same-task nesting preserves plan context. Returning from a financial child restores the outer invoice mode.
- Shared PostgreSQL quota spacing at 9 RPM across processors of the same project/region/type; no per-process unlimited fallback. Current 10 RPM quota was not raised.
- Costs estimate paid usage before free tier or credits, include thought tokens and failed parse attempts. Nested page slots prevent fallback double-counting.
- Admin now displays current-service model/backend/LOW facts and effective task selection. Unknown current-version quality/cost/speed metrics show dashes, not old benchmark numbers. P50 is provider-call latency, not whole-document latency.

## Evidence (reused where already passed)

- Cached pilot parity: bank 18 pages / 761 rows; GL 7 pages / 403 rows. Schema and audit match saved pilot outputs.
- New recon adapter with cached OCR plus real PDF rendering preserves those counts, aggregate money, opening/closing balance and review audit. No paid API calls for this check.
- Earlier live local-user checks: pinned Document AI 3-page bank PDF 13.19s; frozen 3.8 LOW IMG_2575 plus matching transcript 5474ms, 2718 input / 457 billed output tokens. Connectivity only, not Worker acceptance.
- Core contract/guard tests, model routing, VAT/admin/pipeline checks passed during implementation; changed policy/fileconv/admin set 91 passed, fileconv helper extraction 20 passed, explicit legacy ladder fixtures 16 passed.
- Mandatory pre-push: 1154 modules / 6 shards / 33 seconds, then all formatting/import/frontend/cache/size gates passed. No manually repeated full suite.
- Real disposable PostgreSQL: 8 concurrent reservations share one quota slot; separate key independent; expired slot reusable. Container removed. No production DB tested destructively.
- Built real admin shell in browser with real backend snapshot and mocked auth/cost responses: Chinese and actual Thai switching verified, Vertex LOW labels checked. Local screenshots `tests/e2e/_artifacts/ocr-integration/`. Not production user-login acceptance.
- ERP invite E2E has an explicit one-day stale acknowledgement until September 6: only shared admin cache/OCR text changed, invitation implementation untouched, user requested no expanded tests.
- Web/Worker runtime SAs received roles/documentai.apiUser; runtime secrets v2 preserve other values and add only four Enterprise configuration keys.
- Worker identity probe: existing immutable runtime image, exact candidate request body/version, one synthetic page, HTTP 200 and text/page verified. Execution `pearnly-ocr-runtime-probe-20260905-cqph7` passed. One paid OCR page, no app billing/customer document write.
- Exact released image plus Worker SA plus runtime secret v2: config probe `pearnly-ocr-config-probe-20260905-tq47s` read production policy and verified all task modes, B 3.1 first read / Vertex 3.8 LOW fallback and frozen bank/GL/VAT hashes. Passed with no model calls.
- Both task-only Cloud Run probe jobs deleted after completion.
- Cloud Run schema job `pearnly-schema-m6928` and required full installer download checks passed. Formal domain health/ready 200; request nonce `ocr_release=7dc72a755075` logged on new Web revision. Python urllib was initially rejected (403); normal browser User-Agent returned 200; no protection was disabled.
- Attempt `33973973696` had an incorrect SHA, failed at checkout and was cancelled before cloud authentication/mutation; successful correct-SHA release is `33974005122`.

## Acceptance boundary

Implementation, mandatory checks, deployment and runtime configuration verification are complete. No enlarged corpus, shadow traffic or gray rollout. Actual user document/device acceptance remains separate; no claim of 100% bank transcription or universal three-axis superiority. Both local reconstruction and schema transcription can require review.
