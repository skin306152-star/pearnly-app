# Pearnly 品牌源资产

全站品牌素材的单一来源。通用品牌素材供页面、图标和社交预览接线；LINE Rich Menu 只保留当前 Cowork 与 DMS 两套 v1 成品。

| 文件                                          | 用途                                |
| --------------------------------------------- | ----------------------------------- |
| `logo-full.png` / `logo-full-transparent.png` | 完整横版 logo(着陆页 / 邮件 / 文档) |
| `logo-square.png`                             | 方形 logo                           |
| `app-icon-1024.png`                           | 应用商店图标母版                    |
| `favicon.ico` / `favicon-32.png`              | 浏览器页签图标                      |
| `apple-touch-icon-180.png`                    | iOS 主屏图标                        |
| `pwa-icon-192.png` / `pwa-icon-512.png`       | PWA manifest 图标                   |
| `social-preview-1200x630.png`                 | Open Graph / 社交分享卡             |
| `line-richmenu-cowork-v1-2500x1686.png`      | Pearnly Cowork LINE Rich Menu       |
| `line-richmenu-dms-v1-2500x1686.png`         | Pearnly DMS LINE Rich Menu          |

接线时:页面 `<link rel="icon">` / `apple-touch-icon` / web manifest 指向 `/static/brand/<file>`,并按需 bump `?v=`。
