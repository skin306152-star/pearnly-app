# WeKan branding and entry flash — released 2026-09-14

## What changed

Entering 工作协作 used to paint WeKan's own sign-in page and the stock WeKan logo
for a moment before the Pearnly handshake finished. The embedded app also said
WeKan in WeKan's blue.

Only the logo, the product name and the palette changed: no native screen,
permission or workflow was rewritten, and no data was migrated.

- The Pearnly boot cover now stands in for that moment. Its stylesheet is linked
  in the server-rendered `<head>`, so it is render-blocking and in force on the
  first paint; the native UI stays invisible until `client.js` has authenticated
  the Pearnly session. The cover lifts on success, on a failed login (showing the
  existing retry message) and on a 12-second safety timeout.
- Header and sign-in logos, favicons and the iOS home-screen icon are Pearnly
  images. The header mark and the sign-in lockup were derived from
  `static/brand/logo-square.png`; nothing was redrawn by hand.
- The product name is the native `productName` setting, seeded by the bridge at
  startup, so `<title>`, the header alt text and the page-title template all
  follow natively. The two hardcoded `application-name` metas and the tab title
  are rewritten in `client.js`.
- The palette is the app's own accent (`#7C4DFF`): both header bars, the
  primary/sidebar fills and the controls that read `--theme-accent`.

## Exact identities

- Addon source: `c6c116846ceb47f32796e28c4b147c5cbd5eedc9` (pushed to `master`).
- Image: `asia-southeast1-docker.pkg.dev/pearnly/pearnly-app/wekan@sha256:0827370c3508aa7984bfd84df3e45493d9de69e57b56143ccb43cdca4b004042`
  (`linux/amd64`, revision label verified in the running container).
- `pearnly-work-env` version 3 pins that digest; the running wekan and gateway
  containers both report it.
- Pearnly Cloud Run was **not** redeployed — the change is entirely inside the
  independent service.

## Evidence

- 12 Node tests pass, including the new boot-cover reveal, title/meta rename and
  the brand-asset installer's fail-closed paths. Repo pre-push gates passed.
- A local throwaway stack (image + gateway + stub identity service + MongoDB)
  proved the served page, the linked branding sheet, both logo URLs and the
  seeded settings document before anything was deployed.
- Production readback: `/pearnly...` logo bytes and `branding.css` inside both
  containers hash-match the repository; the running container's `favicon.ico`
  hash-matches too. The settings document holds `productName: Pearnly` and both
  logo paths.
- Real browser, signed-in entry: a screenshot at ~260 ms after a reload shows the
  Pearnly cover, not the native sign-in page; the settled page reports
  `<html class="pearnly-ready">`, title `Pearnly - 全部看板 / 已星标`, header bar
  `rgb(124, 77, 255)`, `--theme-accent: #7c4dff`, the Pearnly mark in the header,
  and no `WeKan`/`Wekan` text anywhere in the page.

## Second round: Thai text, language picker, header logo (2026-09-14, later)

Three follow-ups on the same service. Source `c401672f`, image
`…/wekan@sha256:fe78f03cea422e3ae7f3754fa09a789eb3d1875327a28c8917828dd03d2f1e50`,
`pearnly-work-env` version 4. Pearnly Cloud Run was not redeployed and no host
configuration file changed.

- **The header logo is gone.** `branding.css` hides the slot; it sat beside the
  board name and added nothing. The native custom-logo setting still points at
  the Pearnly mark, so the upstream logo can never appear.
- **The language picker offers ไทย / English / 简体中文.** The client bundle's
  `getSupportedLanguages()` result is filtered, not the language table, so a
  profile that already chose another language keeps loading it.
- **Thai is treated as product content.** 49 upstream "Thai" values are
  Vietnamese - the create-board dialog offered "Mẫu" for Template, the board-view
  menu offered "Lịch" for Calendar, plus card/yes/day/hour/minute/second and the
  rule editor's `r-*`/operator/predicate set. 26 keys the UI asks for are missing
  from every language file, so a raw key was shown as the text (the card fold
  control read `collapse-card`, the sort menu `date-created-newest-first`).
  Corrections must exist in the bundle and additions must not, so an upstream fix
  or a stale entry stops the build.

The audit behind that list: all 2417 keys are present in Thai; 49 values were
another language; 47 matched English and all but one (`Bytes` → ไบต์) were
product names or abbreviations; the single placeholder mismatch is an example
JSON whose Thai version translates the example itself. The two templates with
hardcoded English (`originalPositionsView`, `originalPosition`) are unreachable -
no template includes them.

Evidence: 14 Node tests pass; the running production containers carry the patched
values (`"template":"เทมเพลต"`, `"collapse-card":"ย่อการ์ด"`,
`"date-created-newest-first":"วันที่สร้าง (ใหม่สุดก่อน)"`) and the filtered
language function; on the formal domain, signed in, the header logo computes to
`display: none`, the bar is `rgb(124, 77, 255)`, the tab title is `Pearnly - …`,
no `WeKan`/`Wekan` text is present, and the picker shows exactly three languages.
The Thai rendering and the added keys were walked screen by screen on a local
stack running the identical image.

## Limits

- The favicon may stay cached in a browser that already loaded the old one;
  nothing else about the icons is versioned. Traditional Chinese was removed from
  the picker along with the rest of the list, and the 26 added keys exist in Thai
  only - the English and Chinese interfaces still show those raw keys upstream.
- Only the app's own surfaces were branded. WeKan's maintenance pages take the
  bundled `PRODUCT_NAME`, which the deployed compose now sets; that path was not
  exercised by a real maintenance page.
- Board colours remain per-board data. The branding sheet paints the shared
  chrome and controls, so a board that carries its own custom colour keeps its own
  background while the bars and buttons stay Pearnly.
- The sign-in page is still reachable in principle (expired session); it now
  shows the Pearnly lockup, verified from the seeded setting rather than by
  visiting it with a real expired session.

## Workspace

- Worktree `/Users/skin/Developer/Pearnly/pearnly-wekan-branding`, branch
  `codex/wekan-branding`; the code was pushed to `master` as `c6c11684` and then
  `c401672f`. Other windows' changes in the shared checkout were left alone.
- Local verification containers, networks and images were removed after the
  checks, including the throwaway Pearnly stand-in used to render the app locally.
