/*
 * static/daily/daily-core.js · Daily 周记账纯逻辑 + 状态 + API(UI 层在 daily.js)
 *
 * 与 UI 分离:纯函数(node 可测 · UMD 导出)、状态、后端薄层。月份/周界/汇总语义
 * 移植自独立 PWA app/page.tsx;数据唯一源在服务端(每用户独立租户 + RLS)。
 */
(function (root) {
  'use strict';

  var TOKEN_KEY = 'mrpilot_token';
  var LANG_KEY = 'daily-lang';
  var LANGS = ['th', 'en', 'zh', 'ja'];

  // ==================== 纯函数(node 可测 · 零 DOM 依赖) ====================

  function monthId(year, month) {
    return year + '-' + String(month).padStart(2, '0');
  }

  function monthOptions(now) {
    var out = [];
    for (var i = 12; i >= 0; i--) {
      var d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      out.push({ id: monthId(d.getFullYear(), d.getMonth() + 1), year: d.getFullYear(), month: d.getMonth() + 1 });
    }
    return out;
  }

  function daysInMonth(year, month) {
    return new Date(year, month, 0).getDate();
  }

  function weekBounds(year, month, week) {
    var startDay = [1, 8, 15, 22, 29][week - 1];
    var endDay = Math.min(startDay + 6, daysInMonth(year, month));
    var prefix = monthId(year, month);
    return {
      startDay: startDay,
      endDay: endDay,
      min: prefix + '-' + String(startDay).padStart(2, '0'),
      max: prefix + '-' + String(endDay).padStart(2, '0'),
    };
  }

  function sumBy(entries, kind) {
    var total = 0;
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].kind === kind) total += Number(entries[i].amount) || 0;
    }
    return total;
  }

  function inMonth(entry, month) {
    return String(entry.entry_date || '').indexOf(month) === 0;
  }

  function inRange(entry, min, max) {
    var d = String(entry.entry_date || '');
    return d >= min && d <= max;
  }

  function localeOf(lang) {
    return lang === 'th' ? 'th-TH' : lang;
  }

  function moneyFormat(lang, value) {
    return new Intl.NumberFormat(localeOf(lang), {
      style: 'currency',
      currency: 'THB',
      minimumFractionDigits: 2,
    }).format(Number(value) || 0);
  }

  function monthName(lang, year, month) {
    return new Intl.DateTimeFormat(localeOf(lang), { month: 'long' }).format(new Date(year, month - 1, 1));
  }

  function entryDateLabel(lang, value) {
    var parts = String(value).split('-').map(Number);
    if (parts.length !== 3 || parts.some(isNaN)) return value;
    return new Intl.DateTimeFormat(localeOf(lang), { day: 'numeric', month: 'short' }).format(
      new Date(parts[0], parts[1] - 1, parts[2])
    );
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ==================== 状态与 API ====================

  var state = {
    lang: null,
    gate: 'loading',
    loading: false,
    entries: [],
    months: [],
    monthId: null,
    week: 1,
    toast: null,
    showDataTools: false,
    showEntryForm: false,
    saving: false,
  };

  var dict = (root.DAILY_I18N || { th: {}, en: {}, zh: {}, ja: {} });

  function t(key, vars) {
    var block = dict[state.lang] || dict.th || {};
    var text = block[key] != null ? block[key] : key;
    if (vars) {
      Object.keys(vars).forEach(function (k) {
        text = text.split('{' + k + '}').join(String(vars[k]));
      });
    }
    return text;
  }

  function api(path, opts) {
    var headers = Object.assign({}, opts && opts.headers);
    if (state.token) headers.Authorization = 'Bearer ' + state.token;
    if (opts && opts.json != null) headers['Content-Type'] = 'application/json';
    return fetch(path, Object.assign({}, opts, { headers: headers, body: opts && opts.json != null ? JSON.stringify(opts.json) : opts && opts.body }))
      .then(function (resp) {
        return resp.json().catch(function () {
          return null;
        }).then(function (body) {
          return { status: resp.status, body: body };
        });
      })
      .catch(function () {
        return { status: null, body: null };
      });
  }

  function saveToken(token) {
    state.token = token;
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch (e) { /* 隐私模式吞掉 */ }
  }

  function clearToken() {
    state.token = null;
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch (e) { /* ignore */ }
  }

  function readToken() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch (e) {
      return null;
    }
  }

  function readLang() {
    try {
      return localStorage.getItem(LANG_KEY);
    } catch (e) {
      return null;
    }
  }

  function persistLang(lang) {
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch (e) { /* ignore */ }
  }

  root.DailyCore = {
    state: state,
    t: t,
    api: api,
    saveToken: saveToken,
    clearToken: clearToken,
    readToken: readToken,
    readLang: readLang,
    persistLang: persistLang,
    LANGS: LANGS,
    monthId: monthId,
    monthOptions: monthOptions,
    weekBounds: weekBounds,
    sumBy: sumBy,
    inMonth: inMonth,
    inRange: inRange,
    monthName: monthName,
    moneyFormat: moneyFormat,
    entryDateLabel: entryDateLabel,
    escapeHtml: escapeHtml,
  };

  // UMD:node 单测 require 纯函数
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      monthOptions: monthOptions,
      weekBounds: weekBounds,
      sumBy: sumBy,
      inMonth: inMonth,
      inRange: inRange,
      monthName: monthName,
      moneyFormat: moneyFormat,
      entryDateLabel: entryDateLabel,
      escapeHtml: escapeHtml,
      monthId: monthId,
    };
  }
})(typeof window !== 'undefined' ? window : globalThis);
