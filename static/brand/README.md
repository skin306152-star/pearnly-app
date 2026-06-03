# Pearnly 品牌源资产

全站品牌素材的单一来源。**当前未接线**,供将来替换 logo / favicon / PWA 图标 / 社交预览时取用。

| 文件                                          | 用途                                |
| --------------------------------------------- | ----------------------------------- |
| `logo-full.png` / `logo-full-transparent.png` | 完整横版 logo(着陆页 / 邮件 / 文档) |
| `logo-square.png`                             | 方形 logo                           |
| `app-icon-1024.png`                           | 应用商店图标母版                    |
| `favicon.ico` / `favicon-32.png`              | 浏览器页签图标                      |
| `apple-touch-icon-180.png`                    | iOS 主屏图标                        |
| `pwa-icon-192.png` / `pwa-icon-512.png`       | PWA manifest 图标                   |
| `social-preview-1200x630.png`                 | Open Graph / 社交分享卡             |
| `line-richmenu-2500x1686.png`                 | LINE 官方账号 rich menu             |

接线时:页面 `<link rel="icon">` / `apple-touch-icon` / web manifest 指向 `/static/brand/<file>`,并按需 bump `?v=`。
