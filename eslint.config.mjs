// REFACTOR-A5 · ESLint flat config(起步规则集)
//
// 范围:只 lint "会存活 / 已模块化" 的 JS —— src/home/*.js(ES 模块)、
//       static/*.js(IIFE 脚本)、E2E 测试、构建配置。
// 不 lint 巨石(home.js 等):它们是阶段 C 拆解目标 · 33k 行前模块时代 IIFE ·
//       全量 ESLint 会爆出成千上万 no-undef 假阳性 · 待阶段 C 拆成模块后自然纳入。
// 格式交给 Prettier(唯一权威)· ESLint 只抓"真 bug"类规则。

import js from '@eslint/js';
import globals from 'globals';

export default [
    {
        // 巨石 + 构建产物 + 第三方 + 临时目录 —— 不 lint
        ignores: [
            'node_modules/**',
            'static/dist/**',
            '_pkg/**',
            '_pkg_tmpstatic/**',
            'probes/**',
            // 逆向工程抓取的 MR.ERP 页面 JS + 一次性探针(非本项目源码 · 铁律 #8 不改抓取样本)
            'scripts/probe/**',
            '_dms_probe/**', // probe-dms.py 抓取产物(DMS 页面 HTML/JS 样本 · 非源码)
            'scripts/_mock/**', // UI 标准化实物源 + 截图助手(设计参照 · 非交付源码)
            'scripts/_ui_audit/**', // 逐屏视觉审计产物(gitignored · 非源码)
            'tests/eval/**/generate.cjs', // 对抗语料生成器(Node 脚本 · 非交付前端源码 · 同 corpus generate.py 策略)
            'scripts/_*.cjs', // 截图/探针等一次性脚本(下划线前缀 = 临时 · 非交付源码 · 同 _mock 策略)
            'scripts/_*.js',
            'scripts/_ui_audit_full/**',
            '_uitest/**', // 本地真站点 UI 实测脚本(gitignore · 非交付源码)
            'home.js', // REFACTOR-C1 拆解目标
            // REFACTOR-C1(2026-05-25)· 从 home.js verbatim 抽出的 4 语 i18n 数据 ·
            // 继承 home.js 既有的重复 key 债(no-dupe-keys · 后者覆盖前者 · 运行期无害)·
            // 跟 home.js 同策略豁免 · 重复 key 去重留后续专项(verbatim 抽家阶段不动数据)
            'static/i18n-data.js',
            'home.html',
            'login.html',
            'pearnly_nav_prototype_final.html',
        ],
    },

    js.configs.recommended,

    {
        // ES 模块:Vite 前端入口 + 已抽出的 home 子模块 + .mjs 配置
        files: ['src/**/*.js', '**/*.mjs'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'module',
            globals: {
                ...globals.browser,
                ...globals.node,
                // REFACTOR-C1 · home.js(sync · 先于本 bundle 执行)暴露的跨文件全局 ·
                // 阶段 C src/home 模块按需引用(共享 realm 全局环境 · 运行期解析得到)·
                // home.js 完全模块化后逐步退出。t/showToast 是 window 函数 · _userInfo/currentRoute
                // 是 home.js 顶层 let(不在 window 上 · 不能写成 window.X)· 故声明为全局。
                // _userInfo 标 writable:batch7 起 settings-core.js 的 saveProfile/saveCompany
                // 重新赋值它(home.js 顶层 let 是跨 realm 可写的词法绑定)· 否则 no-global-assign 红。
                t: 'readonly',
                showToast: 'readonly',
                withLoading: 'readonly',
                _userInfo: 'writable',
                // currentRoute 标 writable:batch9f 起 core-boot.js 的 routeTo 重新赋值它
                // (同 _userInfo · home.js 顶层 let 是跨 realm 可写的词法绑定)· 否则 no-global-assign 红。
                currentRoute: 'writable',
            },
        },
        rules: {
            // 存量未用变量较多 · 起步只 warn 不 fail(后续 stage 收紧)
            'no-unused-vars': 'warn',
            'no-empty': ['warn', { allowEmptyCatch: true }],
            // 防御式初始化(let x=0,y=0; 各分支再赋值)· verbatim 自 home.js 巨石 · 非 bug ·
            // 跟 static/**/*.js 块同口径降为提示(否则 batch8 layout.js verbatim 块红)
            'no-useless-assignment': 'warn',
        },
    },

    {
        // 经典浏览器脚本(IIFE · 引用 home.js 暴露的跨文件全局)
        files: ['static/**/*.js'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'script',
            globals: { ...globals.browser },
        },
        rules: {
            // IIFE 引用跨文件全局(window.subscribeI18n / t 等)· no-undef 误报多 · 关
            'no-undef': 'off',
            'no-unused-vars': 'warn',
            'no-empty': ['warn', { allowEmptyCatch: true }],
            // 防御式初始化(let x=false; try{x=..}catch{x=..})· 非 bug · 降为提示
            'no-useless-assignment': 'warn',
        },
    },

    {
        // Playwright E2E + Node 配置
        files: ['tests/e2e/**/*.js', 'playwright.config.js'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'module',
            globals: { ...globals.node },
        },
        rules: {
            'no-unused-vars': 'warn',
            // 字符集判定正则故意含控制字符范围(\x00-\x7f 判 ASCII)· 关
            'no-control-regex': 'off',
        },
    },
];
