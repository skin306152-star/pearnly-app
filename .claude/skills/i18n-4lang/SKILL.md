---
name: i18n-4lang
description: 加或改任何用户可见文字时的 4 语规则(泰/英/中/日):真源是 static/i18n-data.js 的 window.I18N、HTML 用 data-i18n 绑定、动态内容必须注册 subscribeI18n、adm-* 超管键只需 zh+th、push 前跑 check_i18n --strict。写文案、加按钮、加提示、加导出表头时用。
---

# 4 语 i18n

Pearnly 是 4 语 SaaS(th / en / zh / ja),4 语都是真产品语言。缺一个 = bug,不许"先发版后面再补"。

## 1. 真源在哪

- 字典:`static/i18n-data.js`(`window.I18N`,2026-05-25 从 home.js 抽出的纯数据 · CRLF · 在 `.prettierignore`,禁 `prettier --write`)
- HTML 绑定:`<button data-i18n="btn-save">` · 占位符 `data-i18n-placeholder="ph-search"`
- JS 动态生成的内容必须注册,否则切语言时该模块不刷新(半中半泰):

```js
if (typeof window.subscribeI18n === 'function') {
  window.subscribeI18n('module-唯一标识', _rerenderAll);
}
```

## 2. 覆盖范围(判断标准:用户眼睛能看到就要 4 语)

按钮 / 标签 / placeholder / tooltip / 错误 / 成功提示 / 空态 / modal 标题正文按钮 / 状态 chip / 菜单 / confirm / 校验提示 / 进度文字 / 引导文案 / 后端错误码对应文案,**以及容易漏的**:下载文件名、Excel sheet 名与表头、邮件 / LINE 通知文案。

例外:`adm-*`(超管后台)只写 `zh` + `th`,不写 en/ja。

## 3. 键顺序

- 新键在各语言块内按 `th → en → zh → ja` 写
- 存量块是 `zh → en → th → ja`(历史原因,重排风险高,**不动**)

## 4. 文案质量

- 4 语并重思考(泰国会计师 / 国际英文 / 中国会计师 / 日本会计师),禁"中文写完谷歌翻译"
- 术语参考:对账 = กระทบยอด · 销项税 = ภาษีขาย · 进项税 = ภาษีซื้อ
- 排版按最长语言(通常泰/日)留宽,4 语切换都不许溢出/折行

## 5. 闸

```powershell
python scripts/check_i18n.py --strict --quiet
```

退出码 0 才能提交。验收时 4 语各切一遍看有没有漏刷新。
