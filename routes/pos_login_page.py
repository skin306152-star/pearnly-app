# -*- coding: utf-8 -*-
"""POS 老板后台专属登录页(主域路径 /pos)· 内联 HTML 常量(PS-5)。

为什么独立一页而非复用主站 login:POS 拆卖客户后台 = pearnly.com/pos,入口只留「账号 + 密码」
一条路(账号=用户名或邮箱,发放制账号常无邮箱),不给 Google / LINE / 注册 / 忘记密码任何旁路
(2026-07-10 Zihao 拍板:发放制账号不走自助找回,密码问题找发号人 → Earn 后台「重置密码」重发一次性密码)。

老收银设备兼容(metta 已装 PWA):/pos 头部先探本机是否存过收银台设备绑定凭据
(localStorage['pos_store_token'],键名与收银台 SPA 精确一致)。存了 → 立即 location.replace
到 /cashier(收银台新家),不闪一下登录页;没存 → 渲染老板登录页。收银员设备装的旧 PWA 作用域
在 /pos,其 cache-first service worker 会继续吐缓存的老收银壳(照常离线收银),不受本页影响;
一旦缓存被清,回到 /pos 就靠这道 guard 把带绑定凭据的设备接回 /cashier。

为什么内联而非 static 文件:webhook 部署不拾取新增的 static 根文件(同 reset_page 的血泪),
路由内联 HTML 随 routes/*.py 一起可靠上线。鉴权零新增:仍打主站 POST /api/login,拿到
access_token 后按主站同款(localStorage['mrpilot_token'])落地,登录成功进主应用 /home ——
该账号是 pos_only 业态,home 自动渲染 7 项精简后台。

自包含 · 4 语 · noindex。配色对齐 POS Purple v2:页内定义最小 :root 变量,accent/accent-press
的值抄 static/pos/pos.css 的 --accent / --accent-d 令牌,样式引用一律走 var()。注意:本页 CSS
内联在 .py 字符串里,ui_design_lint(只扫 src/home + static)扫不到——这不是通行证,改配色时
人工对着 pos.css 令牌守,两处同步。
"""

POS_LOGIN_HTML = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>POS · Pearnly</title>
<meta name="robots" content="noindex,nofollow" />
<script>
// 老收银设备接回:本机存过收银台设备绑定凭据 → 直接进收银台新家 /cashier(不闪登录页)。
// 放在 head 最前、渲染 body 前执行,键名与收银台 SPA(pos.js STORE_TOKEN_KEY)精确一致。
(function(){try{if(localStorage.getItem('pos_store_token')){location.replace('/cashier'+location.search)}}catch(e){}})();
</script>
<link rel="icon" href="/static/brand/favicon.ico?v=1" sizes="any" />
<link rel="icon" type="image/png" sizes="32x32" href="/static/brand/favicon-32.png?v=1" />
<style>
/* accent/accent-press 值对齐 static/pos/pos.css 的 --accent / --accent-d 令牌(POS Purple v2)·
   改令牌时两处同步。本文件在 .py 里,ui_design_lint 扫不到,靠人工守。 */
:root{--bg:rgb(250,250,248);--panel:rgb(255,255,255);--ink:rgb(26,26,26);--ink-3:rgb(107,114,128);--line:rgb(229,231,235);--accent:#7C4DFF;--accent-press:#6B3FF2;--danger:rgb(220,38,38);--ok:rgb(5,150,105);--inverse:rgb(255,255,255)}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'PingFang SC','Microsoft YaHei',sans-serif;padding:24px}
.brand{font-size:22px;font-weight:700;letter-spacing:-.5px;margin-bottom:6px;color:var(--ink);text-decoration:none}
.tag{font-size:12px;color:var(--ink-3);margin-bottom:20px;letter-spacing:.3px}
.card{width:100%;max-width:400px;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:28px 26px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
h1{font-size:18px;margin:0 0 6px}
.sub{font-size:13px;color:var(--ink-3);margin:0 0 20px;line-height:1.5}
label{display:block;font-size:13px;font-weight:500;margin:14px 0 6px}
.field{position:relative}
input{width:100%;height:42px;padding:0 40px 0 12px;border:1px solid var(--line);border-radius:10px;font-size:14px;outline:none;background:var(--panel);color:var(--ink)}
input:focus{border-color:var(--accent)}
.eye{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--ink-3);padding:6px;line-height:0}
.eye svg{display:block}
button.submit{width:100%;height:44px;margin-top:22px;background:var(--accent);color:var(--inverse);border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer}
button.submit:hover{background:var(--accent-press)}
button.submit:disabled{opacity:.6;cursor:default}
.msg{font-size:13px;margin-top:14px;min-height:18px;line-height:1.5}
.msg.error{color:var(--danger)}
.msg.success{color:var(--ok)}
.langbar{margin-top:18px;display:flex;gap:6px;justify-content:center}
.langbar button{background:none;border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:12px;color:var(--ink-3);cursor:pointer}
.langbar button.active{border-color:var(--accent);color:var(--accent)}
</style>
</head>
<body>
<div class="brand">Pearnly</div>
<div class="tag" id="p-tag"></div>
<div class="card">
<h1 id="p-title"></h1>
<p class="sub" id="p-sub"></p>
<form id="p-form">
<label id="p-label-email" for="p-email"></label>
<div class="field">
<input id="p-email" type="text" autocomplete="username" autocapitalize="none" spellcheck="false" />
</div>
<label id="p-label-pw" for="p-pw"></label>
<div class="field">
<input id="p-pw" type="password" autocomplete="current-password" />
<button class="eye" type="button" data-target="p-pw" aria-label="show/hide"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg></button>
</div>
<button class="submit" id="p-submit" type="submit"></button>
<div class="msg" id="p-msg"></div>
</form>
<div class="langbar" id="p-langbar">
<button data-lang="zh">中文</button><button data-lang="th">ไทย</button><button data-lang="en">EN</button><button data-lang="ja">日本</button>
</div>
</div>
<script>
(function(){
'use strict';
var I18N={
zh:{tag:'POS 老板后台',title:'登录',sub:'用你的账号和密码登录 POS 后台。',email:'账号',pw:'密码',submit:'登录',submitting:'登录中…',empty:'请输入账号和密码',wrong:'账号或密码不正确',locked:'尝试次数过多 · 请 30 分钟后再试',neterr:'网络异常 · 请稍后重试'},
th:{tag:'ระบบหลังร้าน POS',title:'เข้าสู่ระบบ',sub:'เข้าสู่ระบบหลังร้าน POS ด้วยบัญชีและรหัสผ่านของคุณ',email:'บัญชี',pw:'รหัสผ่าน',submit:'เข้าสู่ระบบ',submitting:'กำลังเข้าสู่ระบบ…',empty:'กรุณากรอกบัญชีและรหัสผ่าน',wrong:'บัญชีหรือรหัสผ่านไม่ถูกต้อง',locked:'พยายามหลายครั้งเกินไป · ลองใหม่ใน 30 นาที',neterr:'เครือข่ายมีปัญหา · ลองใหม่อีกครั้ง'},
en:{tag:'POS Back Office',title:'Sign in',sub:'Sign in to the POS back office with your account and password.',email:'Account',pw:'Password',submit:'Sign in',submitting:'Signing in…',empty:'Please enter account and password',wrong:'Incorrect account or password',locked:'Too many attempts · try again in 30 minutes',neterr:'Network error · please try again'},
ja:{tag:'POS 管理画面',title:'ログイン',sub:'アカウントとパスワードで POS 管理画面にログイン。',email:'アカウント',pw:'パスワード',submit:'ログイン',submitting:'ログイン中…',empty:'アカウントとパスワードを入力してください',wrong:'アカウントまたはパスワードが正しくありません',locked:'試行回数が多すぎます · 30 分後に再試行',neterr:'ネットワークエラー · もう一度お試しください'}};
function pick(){var s='';try{s=localStorage.getItem('mrpilot_lang')||''}catch(e){}var n=(navigator.language||'').slice(0,2);var c=s||n;return I18N[c]?c:'zh'}
var lang=pick(),dict=I18N[lang]||I18N.zh;
function $(id){return document.getElementById(id)}
function applyLang(){document.documentElement.lang=lang;$('p-tag').textContent=dict.tag;$('p-title').textContent=dict.title;$('p-sub').textContent=dict.sub;$('p-label-email').textContent=dict.email;$('p-label-pw').textContent=dict.pw;$('p-submit').textContent=dict.submit;document.querySelectorAll('#p-langbar button').forEach(function(b){b.classList.toggle('active',b.dataset.lang===lang)})}
function setMsg(t,k){var e=$('p-msg');e.textContent=t||'';e.className='msg'+(k?' '+k:'')}
async function submit(e){e.preventDefault();var acct=($('p-email').value||'').trim().toLowerCase(),pw=$('p-pw').value;if(!acct||!pw)return setMsg(dict.empty,'error');var b=$('p-submit');b.disabled=true;b.textContent=dict.submitting;setMsg('','');try{var r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:acct,password:pw,remember:true})});var data=await r.json().catch(function(){return{}});if(r.ok&&data.access_token){try{localStorage.setItem('mrpilot_token',data.access_token);localStorage.setItem('mrpilot_lang',lang)}catch(e2){}window.location.href=data.is_super_admin?'/admin/cost':'/home';return}setMsg(data.detail==='account_locked'?dict.locked:dict.wrong,'error')}catch(err){setMsg(dict.neterr,'error')}finally{b.disabled=false;b.textContent=dict.submit}}
function bind(){document.querySelectorAll('.eye').forEach(function(eye){eye.addEventListener('click',function(){var i=$(eye.dataset.target);if(i)i.type=i.type==='password'?'text':'password'})});$('p-form').addEventListener('submit',submit);$('p-langbar').addEventListener('click',function(e){var b=e.target.closest('button[data-lang]');if(!b)return;lang=b.dataset.lang;dict=I18N[lang]||I18N.zh;try{localStorage.setItem('mrpilot_lang',lang)}catch(e2){}applyLang();setMsg('','')})}
applyLang();bind();
})();
</script>
</body>
</html>"""
