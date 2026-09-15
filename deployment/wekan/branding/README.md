# Pearnly branding assets

Installed into the pinned WeKan build by `install.mjs`; none of them contain
third-party code.

| File | Installed as | Used by |
| --- | --- | --- |
| `pearnly-header-logo.png` | `pearnly-header-logo.png` | `customTopLeftCornerLogoImageUrl` (top bar, 28px high, 56px @2x) |
| `pearnly-login-logo.png` | `pearnly-login-logo.png` | `customLoginLogoImageUrl` (sign-in page, 300px wide, 600px @2x) |
| `favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png` | same names | replaces the stock WeKan tab icon |
| `apple-touch-icon.png` | `apple-touch-icon.png` | replaces the stock iOS home-screen icon |

The header mark is the cat from `static/brand/logo-square.png` (mark crop,
`y 98..656`) on a white rounded tile; the sign-in lockup is that file's mark and
wordmark (`y 98..870`) as one image. Both were rendered from the single source
asset, so no logo was redrawn by hand.
