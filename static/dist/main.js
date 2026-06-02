(function(){const n=[];function a(s){try{n.push(Object.assign({ts:Date.now()},s)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(s)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(s){s.target&&s.target!==window&&(s.target.src||s.target.href)||a({type:"js_error",summary:String(s.message||"JS Error").slice(0,200),detail:{file:s.filename||"",line:s.lineno||0,col:s.colno||0,stack:s.error&&s.error.stack?String(s.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(s){const i=s.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const o=window.fetch;typeof o=="function"&&(window.fetch=function(){const s=arguments,i=Date.now(),r=typeof s[0]=="string"?s[0]:s[0]&&s[0].url||"?",c=s[1]&&s[1].method||"GET",m=String(r).split("?")[0];return o.apply(this,s).then(function(p){const u=Date.now()-i;if(p.ok)u>2500&&a({type:"api_slow",summary:c+" "+m+" → 慢 "+u+"ms",detail:{url:r,method:c,status:p.status,elapsed_ms:u}});else{let l="";try{p.clone().text().then(function(f){l=String(f||"").slice(0,500),a({type:"api_error",summary:c+" "+m+" → "+p.status+" ("+u+"ms)",detail:{url:r,method:c,status:p.status,elapsed_ms:u,body_preview:l}})}).catch(function(){a({type:"api_error",summary:c+" "+m+" → "+p.status+" ("+u+"ms)",detail:{url:r,method:c,status:p.status,elapsed_ms:u,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:c+" "+m+" → "+p.status+" ("+u+"ms)",detail:{url:r,method:c,status:p.status,elapsed_ms:u}})}}return p}).catch(function(p){const u=Date.now()-i;throw a({type:"api_fail",summary:c+" "+m+" → 网络失败 ("+u+"ms)",detail:{url:r,method:c,elapsed_ms:u,error:String(p&&p.message||p)}}),p})}),["error","warn"].forEach(function(s){const i=console[s];typeof i=="function"&&(console[s]=function(){try{const r=[];for(let c=0;c<arguments.length;c++){const m=arguments[c];if(typeof m=="string")r.push(m);else if(m&&m instanceof Error)r.push(m.message);else try{r.push(JSON.stringify(m).slice(0,300))}catch{r.push(String(m))}}a({type:"console_"+s,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(o=>o.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function Jo(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function Wo(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function Yo(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function tn(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const o in n)a=a.replace("{"+o+"}",n[o]);return a}function Zo(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function Xo(e,n){n=n||14;const o={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${o}</svg>`}function nn(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},o={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},s=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[s]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[s]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+o[s]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function an(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function Qo(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...an()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),o=a&&a.detail;let s="";if(typeof o=="string"?s=o:o&&typeof o=="object"&&(s=o.code||""),n.status===401||typeof s=="string"&&s.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,o),localStorage.removeItem("mrpilot_token"),s==="auth.session_revoked")nn();else{const c=s==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(tn(c),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=o,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function es(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...an()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.clone().json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")nn();else{const m=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(tn(m),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function ts(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...an()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")nn();else{const m=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(tn(m),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const o=await a.json().catch(()=>({}));return{ok:a.ok&&o.ok!==!1,...o}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=Qo;window.apiPost=es;window.t=tn;window.escapeHtml=Zo;window.svgIcon=Xo;window._showSessionRevokedModal=nn;window._wsHeader=an;window.apiPut=ts;window.getMaxFiles=Jo;window.getMaxPagesPerFile=Wo;window.getMaxMbPerFile=Yo;function ve(e,n){const a=document.getElementById(e);if(!(!a||a.dataset.wbInjected==="1")){a.innerHTML=n,a.dataset.wbInjected="1";try{const o=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",s=window.I18N;if(!s||!s[o])return;a.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");s[o][r]&&(i.textContent=s[o][r])}),a.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");s[o][r]&&(i.placeholder=s[o][r])})}catch{}}}const ns=`
        <!-- v85 · 模块头 · 视觉对齐其他页 -->
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 8V5a1 1 0 011-1h3M16 4h3a1 1 0 011 1v3M20 16v3a1 1 0 01-1 1h-3M8 20H5a1 1 0 01-1-1v-3"/>
                    <path d="M4 12h16"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="ocr-title">上传识别</div>
                <div class="page-head-sub" data-i18n="ocr-sub">把票据一拍 · 数据自动进 Excel 和 ERP</div>
            </div>
            <!-- v118.19.1 · 「归档规则」按钮从这里移除 · 改放到「设置 → 归档规则」tab(低频功能不该占核心工作区右上)-->
        </div>

        <div class="info-bar" id="info-bar"></div>

        <!-- 上传卡片 -->
        <div class="card">
            <div class="section-head">
                <div class="section-title" data-i18n="upload-title">上传 PDF 文件</div>
                <div class="section-sub" id="upload-hint"></div>
            </div>

            <div class="drop-zone" id="drop-zone">
                <svg class="icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 32V16a2 2 0 012-2h12l8 8v10a2 2 0 01-2 2H16a2 2 0 01-2-2z"/>
                    <path d="M28 14v8h8M24 28v-6M20 24l4-4 4 4"/>
                </svg>
                <div class="text" data-i18n="drop-text">点击或拖拽文件到此处</div>
                <div class="hint" data-i18n="drop-hint">支持 PDF / 图片 / Excel / CSV / Word · 系统自动选择 OCR 或直接解析 · 数据不存服务器</div>
            </div>
            <input type="file" id="file-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt" multiple>

            <!-- v113 · 移动端拍照入口 + 上传图片入口 · 桌面端也展示"上传图片" -->
            <div class="upload-alt-row" id="upload-alt-row" style="display:none;">
                <button type="button" class="btn-scan-doc" id="btn-scan-doc">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 7h4l2-2h6l2 2h4a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V8a1 1 0 011-1z"/>
                        <circle cx="12" cy="13" r="4"/>
                    </svg>
                    <span data-i18n="btn-scan-doc">拍摄票据</span>
                </button>
                <button type="button" class="btn-scan-doc btn-upload-pic" id="btn-upload-pic">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="4" width="18" height="16" rx="2"/>
                        <circle cx="9" cy="10" r="1.6" fill="currentColor"/>
                        <path d="M3 17l5-5 4 4 3-3 6 6"/>
                    </svg>
                    <span data-i18n="btn-upload-pic">上传图片</span>
                </button>
            </div>
            <!-- v113 · 拍照 input(每点一次拍 1 张 · 触发原生相机)-->
            <input type="file" id="camera-input" accept="image/*" capture="environment" style="display:none;">
            <!-- v113 · 选图 input(多选 · 支持图片和 PDF 混选)-->
            <input type="file" id="gallery-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt" multiple style="display:none;">

            <ul class="file-list" id="file-list"></ul>

            <div class="btn-row">
                <button class="btn btn-primary" id="btn-start" disabled>
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M6 4l10 6-10 6z"/></svg>
                    <span data-i18n="btn-start">开始识别</span>
                </button>
                <button class="btn btn-danger" id="btn-stop" style="display:none;">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="5" width="10" height="10" rx="1.5"/></svg>
                    <span data-i18n="btn-stop">停止识别</span>
                </button>
                <button class="btn btn-secondary" id="btn-clear" disabled>
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h10M8 3h4M7 7l1 10h4l1-10"/></svg>
                    <span data-i18n="btn-clear">清空</span>
                </button>
                <div class="export-split-wrap" id="export-split-wrap">
                    <button class="btn btn-success export-main" id="btn-export" disabled>
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4M4 15v2h12v-2"/></svg>
                        <span data-i18n="btn-export">导出 Excel</span>
                    </button>
                    <button class="btn btn-success export-arrow" id="btn-export-arrow" disabled aria-label="选模板">
                        <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg>
                    </button>
                </div>
                <button class="btn btn-locked" id="btn-custom-template" style="display:none;">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="14" height="12" rx="1"/><path d="M3 8h14M7 4v12"/></svg>
                    <span data-i18n="btn-custom-tpl">自定义模板</span>
                </button>
            </div>

            <div class="alert alert-info" id="alert-info">
                <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 14a1 1 0 110-2 1 1 0 010 2zm1-4a1 1 0 01-2 0V6a1 1 0 012 0v6z"/></svg>
                <span id="alert-info-text"></span>
            </div>
            <div class="alert alert-warn" id="alert-warn">
                <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2L1 18h18L10 2zm0 14a1 1 0 110-2 1 1 0 010 2zm1-4a1 1 0 01-2 0V8a1 1 0 012 0v4z"/></svg>
                <span id="alert-warn-text"></span>
            </div>
            <div class="alert alert-error" id="alert-error">
                <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a8 8 0 100 16 8 8 0 000-16zm4.24 11.17L13 14.41l-3-3-3 3-1.24-1.24 3-3-3-3L7 4.93l3 3 3-3 1.24 1.24-3 3 3 3z"/></svg>
                <span id="alert-error-text"></span>
            </div>
        </div>

        <!-- 结果卡片 -->
        <div class="card results-card" id="results-card">
            <div class="section-head results-head">
                <div class="results-head-left">
                    <div class="section-title" data-i18n="results-title">识别结果</div>
                    <div class="section-sub" data-i18n="results-sub">点击行查看详情</div>
                </div>
                <div class="results-head-stats" id="results-head-stats"></div>
            </div>

            <!-- v27.8.1.14b.2 · 上传识别页 · 自动保存提示 banner -->
            <div class="results-saved-banner">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <circle cx="10" cy="10" r="8"/>
                    <polyline points="6.5,10.5 9,13 13.5,7.5"/>
                </svg>
                <span data-i18n="results-saved-banner">识别结果会自动保存到「单据记录」 · 关掉本页也不会丢</span>
            </div>

            <div class="search-row">
                <div class="search-wrap">
                    <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/>
                    </svg>
                    <input type="text" class="search-input" id="search-input" data-i18n-placeholder="search-placeholder">
                    <button type="button" class="search-clear" id="search-clear" style="display:none;" aria-label="clear">✕</button>
                </div>
                <span class="search-matches" id="search-matches"></span>
            </div>

            <div class="table-wrap">
                <table class="results-table" id="results-table">
                    <thead>
                        <tr>
                            <th data-sort="no" class="no-sort"><span data-i18n="col-no">序号</span></th>
                            <th data-sort="filename"><span data-i18n="col-filename">文件名</span> <span class="sort-indicator"></span></th>
                            <th data-sort="invoice_no"><span data-i18n="col-invoice">发票号</span> <span class="sort-indicator"></span></th>
                            <th data-sort="invoice_date"><span data-i18n="col-date">日期</span> <span class="sort-indicator"></span></th>
                            <th data-sort="total" class="amount-col"><span data-i18n="col-total">金额</span> <span class="sort-indicator"></span></th>
                            <th data-sort="confidence" id="col-conf-th"><span data-i18n="col-conf">置信度</span> <span class="sort-indicator"></span></th>
                        </tr>
                    </thead>
                    <tbody id="results-tbody"></tbody>
                </table>
            </div>
        </div>
    `;ve("page-ocr",ns);const as=`
    <div class="topbar-left">
        <!-- v86 · 手机端汉堡按钮(桌面端隐藏) -->
        <button class="topbar-hamburger" id="topbar-hamburger" aria-label="Menu">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <line x1="3" y1="6" x2="17" y2="6"/>
                <line x1="3" y1="10" x2="17" y2="10"/>
                <line x1="3" y1="14" x2="17" y2="14"/>
            </svg>
        </button>
        <div class="brand" id="brand">
            <svg class="brand-icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="32" height="32" rx="6" fill="#0f172a"/>
                <path fill-rule="evenodd" clip-rule="evenodd" d="M9 9H16.5C19.5376 9 22 11.4624 22 14.5C22 17.5376 19.5376 20 16.5 20H13V25H9V9ZM13 13V16H16.5C17.3284 16 18 15.3284 18 14.5C18 13.6716 17.3284 13 16.5 13H13Z" fill="#fff"/>
                <path d="M21 13L24.5 9.5M24.5 9.5H21M24.5 9.5V13" stroke="#fbbf24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div class="brand-divider"></div>
            <div class="brand-workspace" id="brand-workspace" data-i18n="brand-workspace-fallback">我的工作台</div>
        </div>
    </div>

    <div class="topbar-right">
        <!-- v117 · 删除原右上角"管理"下拉 · 用户管理已在左下角导航 · 入口唯一化 -->
        <!-- v118.28.5 · 语言切换器从这里移到「设置 → 个人资料」内 · 顶栏右侧腾给客户切换器 -->

        <!-- v118.28.5 · 客户切换器(从 brand 旁迁移到顶栏右侧 · 跟 Linear / Notion workspace switcher 同位置) -->
        <!-- B4 (2026-05-26) · workspace 工作模式切换器(账套主体=在为哪家公司做账)·
             取代旧 ClientSwitcher(买方过滤)。控件由 src/home/workspace-switcher.js 渲染进
             #workspace-switcher-root。外层保留 id=client-switcher 供 admin-mode 隐藏 + 既有定位 CSS。 -->
        <div class="client-switcher cs-right" id="client-switcher">
            <div id="workspace-switcher-root"></div>
        </div>

        <!-- NAV-IA Phase 1 · 顶栏搜索框(2026-05-15 拍板 · 点击/⌘K 弹命令面板) -->
        <div class="topbar-search" id="topbar-search" role="button" tabindex="0"
             aria-label="Open command palette"
             title="搜索 · 快速跳转 (Cmd+K / Ctrl+K)">
            <svg class="topbar-search-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor"
                 stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="9" cy="9" r="6"/>
                <line x1="14" y1="14" x2="17" y2="17"/>
            </svg>
            <span class="topbar-search-text" data-i18n="topbar-search-ph">搜索发票 · 客户 · 跳转...</span>
            <span class="topbar-search-kbd"><span class="topbar-search-kbd-mac">⌘K</span><span class="topbar-search-kbd-win">Ctrl K</span></span>
        </div>

        <!-- NAV-IA Phase 1 · 头像下拉菜单(2026-05-15 拍板 · 收纳账户/设置/管理员入口) -->
        <div class="avatar-wrap" id="avatar-wrap">
            <button type="button" class="avatar" id="avatar-btn" aria-haspopup="menu" aria-expanded="false" title="账户菜单">·</button>
            <div class="avatar-popup" id="avatar-popup" role="menu">
                <div class="avatar-popup-head">
                    <div class="avatar-popup-name" id="avatar-popup-name">—</div>
                    <div class="avatar-popup-email" id="avatar-popup-email">—</div>
                </div>
                <button type="button" class="avatar-popup-item" data-action="settings" id="avatar-menu-settings" role="menuitem">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <circle cx="10" cy="10" r="2.5"/>
                        <path d="M15.3 12a1 1 0 00.2 1.1l.1.1a1.5 1.5 0 11-2.1 2.1l-.1-.1a1 1 0 00-1.1-.2 1 1 0 00-.6.9v.1a1.5 1.5 0 11-3 0v-.1a1 1 0 00-.6-.9 1 1 0 00-1.1.2l-.1.1A1.5 1.5 0 114.8 13.3l.1-.1a1 1 0 00.2-1.1 1 1 0 00-.9-.6h-.1a1.5 1.5 0 110-3h.1a1 1 0 00.9-.6 1 1 0 00-.2-1.1l-.1-.1A1.5 1.5 0 116.9 4.7l.1.1a1 1 0 001.1.2h.1a1 1 0 00.6-.9v-.1a1.5 1.5 0 113 0v.1a1 1 0 00.6.9 1 1 0 001.1-.2l.1-.1a1.5 1.5 0 112.1 2.1l-.1.1a1 1 0 00-.2 1.1 1 1 0 00.9.6h.1a1.5 1.5 0 110 3h-.1a1 1 0 00-.9.6z"/>
                    </svg>
                    <span data-i18n="avatar-menu-settings">设置</span>
                </button>
                <button type="button" class="avatar-popup-item" data-action="team" data-show-if-team="1" id="avatar-menu-team" role="menuitem">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <circle cx="7" cy="8" r="2.5"/>
                        <path d="M3 16c0-2.2 1.8-4 4-4s4 1.8 4 4"/>
                        <circle cx="14" cy="7" r="2"/>
                        <path d="M12 16c0-2 1-3.5 3-3.5s3 1.5 3 3.5"/>
                    </svg>
                    <span data-i18n="avatar-menu-team">团队成员</span>
                </button>
                <button type="button" class="avatar-popup-item" data-action="billing" data-show-if-money="1" id="avatar-menu-billing" role="menuitem">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <rect x="2.5" y="5" width="15" height="11" rx="1.5"/>
                        <line x1="2.5" y1="9" x2="17.5" y2="9"/>
                        <line x1="5.5" y1="13" x2="8" y2="13"/>
                    </svg>
                    <span data-i18n="avatar-menu-billing">账户 &amp; 余额</span>
                </button>
                <button type="button" class="avatar-popup-item" data-action="shortcuts" id="avatar-menu-shortcuts" role="menuitem">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <rect x="2" y="5.5" width="16" height="10" rx="1.5"/>
                        <line x1="5" y1="9" x2="5" y2="9.01"/>
                        <line x1="8" y1="9" x2="8" y2="9.01"/>
                        <line x1="11" y1="9" x2="11" y2="9.01"/>
                        <line x1="14" y1="9" x2="14" y2="9.01"/>
                        <line x1="5.5" y1="12.5" x2="14.5" y2="12.5"/>
                    </svg>
                    <span data-i18n="avatar-menu-shortcuts">键盘快捷键</span>
                </button>
                <div class="avatar-popup-sep" data-show-if-special="1"></div>
                <button type="button" class="avatar-popup-item" data-action="admin" data-show-if-admin="1" id="avatar-menu-admin" role="menuitem" style="display:none">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M10 2.5l6 2v5c0 4-2.8 6.8-6 8-3.2-1.2-6-4-6-8v-5l6-2z"/>
                        <path d="M7.5 10l2 2 3.5-3.5"/>
                    </svg>
                    <span data-i18n="avatar-menu-admin">管理员后台</span>
                    <span class="avatar-pill avatar-pill-admin" data-i18n="avatar-menu-badge-admin">超管</span>
                </button>
                <button type="button" class="avatar-popup-item" data-action="test-center" data-show-if-test="1" id="avatar-menu-test" role="menuitem" style="display:none">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M8 3v5L4 15a1.5 1.5 0 001.4 2h9.2A1.5 1.5 0 0016 15l-4-7V3"/>
                        <line x1="6.5" y1="3" x2="13.5" y2="3"/>
                        <line x1="7" y1="11" x2="13" y2="11"/>
                    </svg>
                    <span data-i18n="avatar-menu-test">测试中心</span>
                </button>
                <div class="avatar-popup-sep"></div>
                <button type="button" class="avatar-popup-item" data-action="help" id="avatar-menu-help" role="menuitem">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <circle cx="10" cy="10" r="8"/>
                        <path d="M7.5 7.5a2.5 2.5 0 015 0c0 1.25-1 1.875-1.875 2.5-.5.36-.625.625-.625 1.25"/>
                        <circle cx="10" cy="14.5" r="0.5" fill="currentColor"/>
                    </svg>
                    <span data-i18n="avatar-menu-help">帮助 &amp; 反馈</span>
                </button>
                <button type="button" class="avatar-popup-item avatar-popup-item-danger" data-action="logout" id="avatar-menu-logout" role="menuitem">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                        <path d="M13 4v2H5v8h8v2a2 2 0 01-2 2H5a2 2 0 01-2-2V4a2 2 0 012-2h6a2 2 0 012 2z"/>
                        <path d="M15 7l3 3-3 3M9 10h9"/>
                    </svg>
                    <span data-i18n="avatar-menu-logout">退出登录</span>
                </button>
            </div>
        </div>

    </div>
`,os=`
    <!-- v22 · 侧栏顶部汉堡(移自原顶栏) -->
    <button class="sidebar-toggle sidebar-toggle-in" id="sidebar-toggle" title="">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="6" x2="17" y2="6"/>
            <line x1="3" y1="10" x2="17" y2="10"/>
            <line x1="3" y1="14" x2="17" y2="14"/>
        </svg>
    </button>

    <!-- v118.33.7.3 · sidebar 顶部 CTA「上传发票」按钮已删 · 对齐 prototype_final(prototype 顶部直接是「首页」· 无 CTA)· 上传发票走「销项管理 → 上传识别」入口 -->

    <!-- v118.33.5 NAV-IA Phase 5 · sidebar 业务流分组(销项▼/进项▼)· prototype_final §3.2 · 云盘同步入口已撤(Phase 7 集成页统一管理) -->

    <!-- 首页(原仪表盘 · 标签改"首页") -->
    <div class="nav-item" data-route="dashboard">
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 10l7-7 7 7v8a1 1 0 01-1 1h-4v-6H8v6H4a1 1 0 01-1-1v-8z"/>
        </svg>
        <span class="nav-label" data-i18n="nav-dashboard">首页</span>
    </div>

    <!-- 销项管理 ▼ 可折叠组(默认展开) -->
    <div class="nav-group nav-collapsible" data-collapsible="sales">
        <div class="nav-group-toggle" data-toggle-group="sales">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 2h8l3 3v13H5z"/>
                <path d="M8 8h5M8 11h5M8 14h3"/>
                <path d="M13 2v3h3"/>
            </svg>
            <span class="nav-label" data-i18n="nav-group-sales">销项管理</span>
            <svg class="nav-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8l4 4 4-4"/>
            </svg>
        </div>
        <div class="nav-sub">
            <div class="nav-item nav-sub-item active" data-route="ocr">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 4h8l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z"/>
                    <path d="M12 4v4h4"/>
                    <path d="M7 12h6M7 15h4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-ocr">上传识别</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="history">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="7"/>
                    <path d="M10 6v4l3 2"/>
                </svg>
                <span class="nav-label" data-i18n="nav-history">单据记录</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="reconcile">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="3" y1="17" x2="17" y2="17"/>
                    <rect x="4" y="11" width="2.5" height="5"/>
                    <rect x="8.75" y="8" width="2.5" height="8"/>
                    <rect x="13.5" y="5" width="2.5" height="11"/>
                </svg>
                <span class="nav-label" data-i18n="nav-reconcile">对账中心</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="sales-invoices">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 2h8l3 3v13H5z"/>
                    <path d="M8 8h5M8 11h5M8 14h3"/>
                    <path d="M13 2v3h3"/>
                </svg>
                <span class="nav-label" data-i18n="nav-sales-invoices">销售发票</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="receivables">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10 3v14"/>
                    <path d="M14 6.5h-5a2.5 2.5 0 000 5h2a2.5 2.5 0 010 5h-5"/>
                </svg>
                <span class="nav-label" data-i18n="nav-receivables">应收追踪</span>
            </div>
        </div>
    </div>

    <!-- 进项管理 ▼ 可折叠组(默认折叠 · Phase 6 才填全 5 子项) -->
    <div class="nav-group nav-collapsible" data-collapsible="expense">
        <div class="nav-group-toggle" data-toggle-group="expense">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 4h7l5 5v7a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z"/>
                <path d="M11 4v5h5"/>
                <path d="M6 13l2 2 4-4"/>
            </svg>
            <span class="nav-label" data-i18n="nav-group-expense">进项管理</span>
            <svg class="nav-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8l4 4 4-4"/>
            </svg>
        </div>
        <div class="nav-sub">
            <div class="nav-item nav-sub-item" data-route="vouchers">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 4h7l5 5v7a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z"/>
                    <path d="M11 4v5h5"/>
                    <path d="M6 13l2 2 4-4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-vouchers">凭证中心</span>
            </div>
        </div>
    </div>

    <!-- v118.33.7.4 · prototype 风格分隔线(销项/进项 ↔ 客户/异常 视觉断开) -->
    <div class="nav-divider"></div>

    <!-- 客户 / 异常栏 / 自动化 独立项(自动化 Phase 7 才合并进集成页) -->
    <div class="nav-item" data-route="clients">
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 17v-1.5a3 3 0 00-3-3H5a3 3 0 00-3 3V17"/>
            <circle cx="8" cy="6.5" r="3"/>
            <path d="M18 17v-1.5a3 3 0 00-2.3-2.9"/>
            <path d="M13 3.6a3 3 0 010 5.8"/>
        </svg>
        <span class="nav-label" data-i18n="nav-clients">客户管理</span>
    </div>

    <div class="nav-item" data-route="exceptions">
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9.1 3.4L2.3 15a1.5 1.5 0 001.3 2.3h12.8A1.5 1.5 0 0017.7 15L10.9 3.4a1.5 1.5 0 00-1.8 0z"/>
            <line x1="10" y1="8" x2="10" y2="12"/>
            <circle cx="10" cy="14.5" r="0.6" fill="currentColor"/>
        </svg>
        <span class="nav-label" data-i18n="nav-exceptions">异常栏</span>
        <span class="nav-badge danger" id="nav-exc-badge" style="display:none;">0</span>
    </div>

    <!-- v118.32.5.5.37 NAV-IA Phase 5 收尾 · 自动化入口已移至集成页右侧抽屉 -->
    <!-- v118.33.3 NAV-IA Phase 3 · sidebar 底部「集成」一级入口 · 空壳路由 · Phase 7 才填内容(Google/LINE/Gmail/文件夹/ERP 第三方授权聚合) -->
    <div class="sidebar-bottom">
        <div class="nav-item" data-route="integrations" id="nav-integrations">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 14L3 17M14 6l3-3"/>
                <path d="M8 4L4 8a2.83 2.83 0 000 4l4 4a2.83 2.83 0 004 0l4-4a2.83 2.83 0 000-4l-4-4a2.83 2.83 0 00-4 0z"/>
            </svg>
            <span class="nav-label" data-i18n="nav-integrations">集成</span>
        </div>
    </div>
`;ve("topbar",as);ve("sidebar",os);function Mn(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const o=document.getElementById("general-lang");o&&(o.value=e);const s=document.getElementById("col-conf-th");s&&s.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&$n(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function ss(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",s=>{s.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(s)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});ss("lang-dropdown",e=>Mn(e.dataset.lang));const qa=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","receivables","reconcile","cloud","test-center"];function Ra(e){qa.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(o=>o.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(o=>{o.classList.toggle("active",o.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function $n(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function za(){try{const[e,n,a,o]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(s=>s.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,o&&(window._planState=o),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const s=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(s&&!i){window.location.replace("/home");return}if(!s&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=s}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,o&&(window._planState=o),window.renderBrandWorkspace(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(s){console.error("[nav-ia phase1] render avatar menu",s)}$n(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const s=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(s&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(s&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(s){console.error("force-pw init",s)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(s){console.error("onboarding init",s)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(s){console.error("settings forms init",s)}}catch(e){console.error(e)}}window.applyLang=Mn;window.routeTo=Ra;window.loadAll=za;window.updateUploadHint=$n;try{Mn(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");Ra(qa.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);za();function is(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){return!i||typeof i!="string"||(i=i.trim(),!i)?null:i.includes("@")&&i.indexOf("@")>0&&i.indexOf(".")>i.indexOf("@")?i.split("@")[0]:i}const o=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let s=null;for(const i of o){const r=a(i);if(r){s=r;break}}s||(s=t("brand-workspace-fallback")||"我的工作台"),e.textContent=s,e.title=s,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",s,"· _userInfo fields:",Object.keys(n))}function rs(){let e=document.getElementById("offline-banner");e||(e=document.createElement("div"),e.id="offline-banner",e.className="offline-banner",e.style.display="none",document.body.insertBefore(e,document.body.firstChild));function n(){navigator.onLine===!1?(e.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",e.classList.remove("is-online"),e.classList.add("is-offline"),e.style.display="flex"):e.classList.contains("is-offline")?(e.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",e.classList.remove("is-offline"),e.classList.add("is-online"),setTimeout(()=>{e.style.display="none",e.classList.remove("is-online")},2e3)):e.style.display="none"}window.addEventListener("online",n),window.addEventListener("offline",n),n()}window.renderBrandWorkspace=is;window.installNetworkBanner=rs;const Na="mrpilot_sidebar_collapsed";localStorage.getItem(Na)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(Na,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const o=document.querySelectorAll("#page-integrations .int-top-tab"),s=document.querySelectorAll("#page-integrations .int-top-panel");if(o.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),s.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),o&&o.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const o=a.target.closest("#page-integrations .int-top-tab");if(o){const i=o.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const o=document.querySelector(".auto-content");o&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(s){s.style.display="",o.appendChild(s)})}window.openIntegrationDrawer=function(a,o){const s=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),c=document.getElementById("int-drawer-body");if(!s||!c)return;e(),s.dataset.currentTab=a||"",r&&(r.textContent=o||""),c.innerHTML="";var m={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},p=m[a]||a;const u=document.querySelector('.auto-panel[data-auto-panel="'+p+'"]');u?(u.style.display="block",c.appendChild(u)):c.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',s.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var l={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(l[a])try{l[a]()}catch(d){console.warn("[int-drawer] loader error",d)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(d){console.warn("[int-drawer] ERP load error",d)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),o&&(o.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),o=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),o&&o.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(s){s.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(s=>{s.addEventListener("click",()=>switchSettingsTab(s.dataset.tab))});let o=null;try{o=localStorage.getItem("mrpilot_settings_tab")}catch{}if(o){const s=document.querySelector(`.settings-tab[data-tab="${o}"]`);if(s&&s.style.display!=="none"){switchSettingsTab(o);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),o=document.getElementById("btn-save-company");if(!a&&!o){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),o&&o.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let Rt=null;function ls(){kn(),Rt=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&kn()}catch{}},1e4)}function kn(){Rt&&(clearInterval(Rt),Rt=null)}window.startEnginePolling=ls;window.stopEnginePolling=kn;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target.closest("[data-rd-action]");if(n){const s=n.dataset.rdAction,i=n.dataset.rdSide;s==="verify"?callRdVerify(i):s==="sync"&&callRdSync(i);return}if(e.target.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=e.target.closest("[data-archive-copy]");if(o){const s=o.dataset.archiveCopy;navigator.clipboard?.writeText(s).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const ra=document.getElementById("btn-custom-template");ra&&ra.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});const cs=`
        <div class="modal" style="max-width:420px;">
            <div class="modal-head">
                <div class="modal-title" id="pearnly-confirm-title" data-i18n="confirm-default-title">请确认</div>
                <button class="modal-close" id="pearnly-confirm-close" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body">
                <div id="pearnly-confirm-msg" class="pearnly-confirm-msg"></div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="pearnly-confirm-cancel" data-i18n="confirm-cancel">取消</button>
                <button class="btn btn-primary" id="pearnly-confirm-ok" data-i18n="confirm-ok">确定</button>
            </div>
        </div>
    `,ds=`
    <div class="modal" style="max-width:420px;">
        <div class="modal-head">
            <div class="modal-title" id="confirm-modal-title" data-i18n="confirm-default-title">请确认</div>
            <button class="modal-close" id="confirm-modal-close" aria-label="close">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
            </button>
        </div>
        <div class="modal-body" id="confirm-modal-body" style="white-space:pre-wrap;line-height:1.55;"></div>
        <div class="modal-foot">
            <button class="btn btn-ghost" id="confirm-modal-cancel" data-i18n="confirm-cancel">取消</button>
            <button class="btn btn-primary" id="confirm-modal-ok" data-i18n="confirm-ok">确定</button>
        </div>
    </div>
`;ve("pearnly-confirm-modal",cs);ve("confirm-modal",ds);window.pearnlyConfirm=function(e,n){return new Promise(function(a){const o=document.getElementById("pearnly-confirm-modal"),s=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),c=document.getElementById("pearnly-confirm-cancel"),m=document.getElementById("pearnly-confirm-close");if(!o||!i||!r||!c){a(window.confirm(e));return}s&&(s.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",o.style.display="flex";function p(v){o.style.display="none",r.removeEventListener("click",u),c.removeEventListener("click",l),m&&m.removeEventListener("click",l),o.removeEventListener("click",d),document.removeEventListener("keydown",f),a(v)}function u(){p(!0)}function l(){p(!1)}function d(v){v.target===o&&p(!1)}function f(v){v.key==="Escape"?p(!1):v.key==="Enter"&&p(!0)}r.addEventListener("click",u),c.addEventListener("click",l),m&&m.addEventListener("click",l),o.addEventListener("click",d),document.addEventListener("keydown",f),setTimeout(function(){try{c.focus()}catch{}},50)})};const ps=`
        <!-- 顶部 page head -->
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 10l9-6 9 6v11H3V10z"/>
                    <path d="M9 21V12h6v9"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" id="recon-main-title" data-i18n="rc-page-title">对账中心</div>
                <div class="page-head-sub" id="recon-main-sub" data-i18n="rc-page-sub">核对账目 · 找出差异 · 关账更快</div>
            </div>
        </div>

        <!-- 顶部横向 tab 条 -->
        <div class="recon-tab-bar">
            <button class="recon-tab-btn active" data-recon-tab="bank" data-i18n="recon-tab-bank">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 6h12M3 6V4a5 5 0 0110 0v2M2 6v7a1 1 0 001 1h10a1 1 0 001-1V6"/><path d="M6 10h4"/></svg>
                银行对账
            </button>
            <button class="recon-tab-btn" data-recon-tab="sale-vat" data-i18n="recon-tab-sale-vat">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M9 1.5H4a1 1 0 00-1 1v11a1 1 0 001 1h8a1 1 0 001-1V5.5L9 1.5z"/><path d="M9 1.5v4h4M5.5 9l1.5 1.5 3-3"/></svg>
                销项税报告核查
            </button>
            <button class="recon-tab-btn" data-recon-tab="gl-vat" data-i18n="recon-tab-gl-vat">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><rect x="1.5" y="1.5" width="13" height="13" rx="1.5"/><path d="M1.5 5.5h13M1.5 9.5h13M5.5 5.5v9M10.5 5.5v9"/></svg>
                收入对账
            </button>
        </div>
        <!-- pane 区(全宽) -->

        <!-- ── 银行对账面板 v2（vex-drop 同款视觉 · v118.33.6.1 UI 重构对齐 GL-VAT） ── -->
        <div id="recon-pane-bank" class="recon-pane active">

            <!-- KPI 3 卡 -->
            <div class="vex-kpi-strip" id="brv2-kpi-strip">
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-ok">✓</div>
                    <div>
                        <div class="vex-kpi-val" id="brv2-kpi-matched">—</div>
                        <div class="vex-kpi-lbl" data-i18n="brv2-stat-matched">完全匹配</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap" id="brv2-kpi-diff-icon" style="background:#f3f4f6;color:#6b7280">△</div>
                    <div>
                        <div class="vex-kpi-val" id="brv2-kpi-diff">—</div>
                        <div class="vex-kpi-lbl" data-i18n="brv2-stat-diff">差额</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-err">!</div>
                    <div>
                        <div class="vex-kpi-val" id="brv2-kpi-unmatched">—</div>
                        <div class="vex-kpi-lbl" data-i18n="brv2-stat-unmatched">未匹配</div>
                    </div>
                </div>
            </div>

            <!-- 主操作区（沿用 vex-main-action 视觉） -->
            <div class="vex-main-action">
                <div class="vex-main-action-tag" data-i18n="vex-main-action-tag">主操作</div>

                <!-- 左右双拖拽区 -->
                <div class="vex-drops">
                    <div class="vex-drop vex-drop-invoice" id="brv2-stmt-zone" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 4h12l6 6v16a2 2 0 01-2 2H8a2 2 0 01-2-2V6a2 2 0 012-2z"/>
                                <path d="M20 4v6h6M10 14h12M10 20h8"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="brv2-stmt-title">① 银行账单 PDF</div>
                        <div class="vex-drop-sub" data-i18n="brv2-stmt-hint">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <div class="vex-drop-filename" id="brv2-stmt-name"></div>
                        <input type="file" id="brv2-stmt-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" multiple style="display:none">
                    </div>

                    <div class="vex-drop-divider" aria-hidden="true"><span>+</span></div>

                    <div class="vex-drop vex-drop-report" id="brv2-gl-zone" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="4" y="6" width="24" height="20" rx="2"/>
                                <line x1="4" y1="13" x2="28" y2="13"/>
                                <line x1="12" y1="6" x2="12" y2="26"/>
                                <line x1="20" y1="6" x2="20" y2="26"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="brv2-gl-title">② 总账 GL</div>
                        <div class="vex-drop-sub" data-i18n="brv2-gl-hint">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <div class="vex-drop-filename" id="brv2-gl-name"></div>
                        <input type="file" id="brv2-gl-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" multiple style="display:none">
                    </div>
                </div>

                <!-- BUG-B v118.35.0.36 (2026-05-22) · OCR 抽 GL/STATEMENT 3 个 anchor 余额不准时
                     用户手动录入兜底 · 防 OCR 错位连锁整张报告废 · Zihao 拍板破例整顿期允许 -->
                <div class="brv2-anchor-row" id="brv2-anchor-row">
                    <div class="brv2-anchor-head">
                        <span class="brv2-anchor-icon" aria-hidden="true">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14">
                                <path d="M8 1.5L14.5 4v4c0 4-3 6.5-6.5 6.5S1.5 12 1.5 8V4L8 1.5z"/>
                                <path d="M6 8l1.5 1.5L10.5 6.5"/>
                            </svg>
                        </span>
                        <span class="brv2-anchor-title" data-i18n="brv2-anchor-title">OCR 抽不准?手动录入 3 个余额(可选 · 留空走 OCR)</span>
                    </div>
                    <div class="brv2-anchor-prefill-banner" id="brv2-anchor-prefill-banner" data-i18n="brv2-anchor-prefill-banner">⚠ 下面带橙色背景的数字是上次 OCR 识别的(浏览器本地缓存)· 不对请点击修改</div>
                    <div class="brv2-anchor-grid">
                        <div class="brv2-anchor-cell">
                            <label for="brv2-anchor-gl-closing" data-i18n="brv2-anchor-gl-closing">GL 期末余额</label>
                            <input type="number" id="brv2-anchor-gl-closing" step="any" inputmode="decimal" placeholder="0.00" autocomplete="off">
                        </div>
                        <div class="brv2-anchor-cell">
                            <label for="brv2-anchor-stmt-closing" data-i18n="brv2-anchor-stmt-closing">Statement 期末余额</label>
                            <input type="number" id="brv2-anchor-stmt-closing" step="any" inputmode="decimal" placeholder="0.00" autocomplete="off">
                        </div>
                        <div class="brv2-anchor-cell">
                            <label for="brv2-anchor-stmt-opening" data-i18n="brv2-anchor-stmt-opening">期初 Statement 余额</label>
                            <input type="number" id="brv2-anchor-stmt-opening" step="any" inputmode="decimal" placeholder="0.00" autocomplete="off">
                        </div>
                        <div class="brv2-anchor-cell">
                            <label for="brv2-anchor-gl-opening" data-i18n="brv2-anchor-gl-opening">GL 期初余额</label>
                            <input type="number" id="brv2-anchor-gl-opening" step="any" inputmode="decimal" placeholder="0.00" autocomplete="off">
                        </div>
                    </div>
                    <div class="brv2-anchor-eq" id="brv2-anchor-eq" style="display:none">
                        <span class="brv2-anchor-eq-lbl" data-i18n="brv2-anchor-eq-lbl">期初差额(Statement 期初 − GL 期初):</span>
                        <span class="brv2-anchor-eq-val" id="brv2-anchor-eq-val">—</span>
                    </div>
                </div>

                <!-- 操作栏 -->
                <div class="vex-action-bar">
                    <button class="btn btn-ghost" id="brv2-reset-btn" type="button" data-i18n="vex-btn-reset">清空</button>
                    <div class="vex-action-info muted" id="brv2-status">
                        <span data-i18n="brv2-hint-need-both">请上传银行账单和 GL 文件</span>
                    </div>
                    <button class="vex-toggle-preview-btn" id="brv2-toggle-preview" type="button" style="display:none">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                        <span id="brv2-toggle-preview-label" data-i18n="vex-toggle-preview-open">查看清单</span>
                    </button>
                    <select class="brv2-acct-select" id="brv2-acct-select" style="display:none">
                        <option value="" data-i18n="brv2-acct-all">全部账户</option>
                    </select>
                    <button class="btn btn-primary" id="brv2-run-btn" type="button" disabled>
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 8l4 4 6-8"/>
                        </svg>
                        <span data-i18n="brv2-run-btn">开始对账</span>
                    </button>
                </div>

                <!-- 查看清单面板（同款 vex-preview-panel 视觉） -->
                <div class="vex-preview-panel" id="brv2-preview-panel" style="display:none">
                    <div class="vex-pp-grid">
                        <div id="brv2-pp-stmt-col"></div>
                        <div id="brv2-pp-gl-col"></div>
                    </div>
                </div>

                <!-- 进度区 -->
                <div class="vex-progress" id="brv2-progress" style="display:none">
                    <div class="spinner"></div>
                    <div>
                        <div class="vex-progress-title" data-i18n="brv2-processing">对账中…</div>
                        <div class="vex-progress-sub" id="brv2-progress-sub"></div>
                    </div>
                </div>

                <!-- 错误提示 -->
                <div class="brv2-error" id="brv2-error" style="display:none"></div>

                <!-- 文件解析诊断表 (失败/部分解析时显示) -->
                <div id="brv2-parse-info-wrap" style="display:none;margin-top:12px">
                    <div id="brv2-parse-info-body"></div>
                </div>

                <!-- 结果 · 对账公式折叠区 -->
                <div class="recon-collapse" id="brv2-summary-collapse" data-collapsed="false" style="display:none;margin-top:14px">
                    <div class="recon-collapse-head" data-toggle="brv2-summary-collapse" tabindex="0" role="button">
                        <svg class="recon-collapse-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="5 7 8 10 11 7"/>
                        </svg>
                        <span class="recon-collapse-title" data-i18n="brv2-formula-title">对账公式</span>
                        <span class="recon-collapse-sub" id="brv2-formula-sub"></span>
                        <div class="glv-section-spacer"></div>
                        <button class="btn btn-ghost btn-small" id="brv2-export-btn" type="button" style="display:none">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" width="13" height="13">
                                <path d="M3 11v2h10v-2M8 2v8M5 7l3 4 3-4"/>
                            </svg>
                            <span data-i18n="brv2-export-excel">导出 Excel</span>
                        </button>
                        <button class="btn btn-ghost btn-small" id="brv2-new-btn" type="button" style="display:none">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" width="13" height="13">
                                <path d="M8 3v10M3 8h10"/>
                            </svg>
                            <span data-i18n="brv2-new-btn">新建</span>
                        </button>
                    </div>
                    <div class="recon-collapse-body">
                        <div class="brv2-formula-grid" id="brv2-formula-grid">
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-gl-close">GL 期末余额</div>
                                <div class="brv2-fcell-val" id="brf-gl-close">—</div>
                            </div>
                            <div class="brv2-fsep">+</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-open-diff">期初差额</div>
                                <div class="brv2-fcell-val" id="brf-open-diff">—</div>
                            </div>
                            <div class="brv2-fsep">−</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-gl-debit-only-short">GL 仅借方</div>
                                <div class="brv2-fcell-val" id="brf-gl-debit-only">—</div>
                            </div>
                            <div class="brv2-fsep">+</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-gl-credit-only-short">GL 仅贷方</div>
                                <div class="brv2-fcell-val" id="brf-gl-credit-only">—</div>
                            </div>
                            <div class="brv2-fsep">−</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-stmt-wd-only-short">账单仅提款</div>
                                <div class="brv2-fcell-val" id="brf-stmt-wd-only">—</div>
                            </div>
                            <div class="brv2-fsep">+</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-stmt-dep-only-short">账单仅存款</div>
                                <div class="brv2-fcell-val" id="brf-stmt-dep-only">—</div>
                            </div>
                            <div class="brv2-fsep">=</div>
                            <div class="brv2-fcell brv2-fcell-result">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-calc-close">计算期末</div>
                                <div class="brv2-fcell-val brv2-fcell-bold" id="brf-calc-close">—</div>
                            </div>
                            <div class="brv2-fsep">vs</div>
                            <div class="brv2-fcell">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-stmt-close">账单期末</div>
                                <div class="brv2-fcell-val" id="brf-stmt-close">—</div>
                            </div>
                            <div class="brv2-fsep">→</div>
                            <div class="brv2-fcell brv2-fcell-diff" id="brv2-fcell-diff">
                                <div class="brv2-fcell-lbl" data-i18n="brv2-diff-label">差额 (应为 0)</div>
                                <div class="brv2-fcell-val brv2-fcell-bold" id="brf-diff">—</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 结果 · 明细折叠区 -->
                <div class="recon-collapse" id="brv2-detail-collapse" data-collapsed="false" style="display:none;margin-top:10px">
                    <div class="recon-collapse-head" data-toggle="brv2-detail-collapse" tabindex="0" role="button">
                        <svg class="recon-collapse-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="5 7 8 10 11 7"/>
                        </svg>
                        <span class="recon-collapse-title" data-i18n="brv2-detail-title">明細</span>
                        <span class="recon-collapse-sub" id="brv2-detail-sub"></span>
                        <div class="glv-section-spacer"></div>
                        <!-- 过滤 tabs（放在折叠头部右侧） -->
                        <div class="brv2-filter-tabs" id="brv2-filter-tabs">
                            <button class="brv2-filter-btn active" data-filter="all" data-i18n="brv2-filter-all">全部</button>
                            <button class="brv2-filter-btn" data-filter="matched" data-i18n="brv2-filter-matched">已匹配</button>
                            <button class="brv2-filter-btn" data-filter="gl_only" data-i18n="brv2-filter-gl-only">GL 未配</button>
                            <button class="brv2-filter-btn" data-filter="stmt_only" data-i18n="brv2-filter-stmt-only">账单未配</button>
                        </div>
                    </div>
                    <div class="recon-collapse-body">
                        <div class="brv2-table-wrap">
                            <table class="brv2-table" id="brv2-detail-table">
                                <thead>
                                    <tr>
                                        <th data-i18n="brv2-th-status">状态</th>
                                        <th data-i18n="brv2-th-stmt-date">账单日期</th>
                                        <th data-i18n="brv2-th-stmt-desc">账单摘要</th>
                                        <th class="num" data-i18n="brv2-th-wd">提款</th>
                                        <th class="num" data-i18n="brv2-th-dep">存款</th>
                                        <th data-i18n="brv2-th-gl-date">GL 日期</th>
                                        <th data-i18n="brv2-th-gl-doc">GL 凭证</th>
                                        <th class="num" data-i18n="brv2-th-gl-debit">借方</th>
                                        <th class="num" data-i18n="brv2-th-gl-credit">贷方</th>
                                        <th data-i18n="brv2-th-layer">层级</th>
                                    </tr>
                                </thead>
                                <tbody id="brv2-tbody"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

            </div><!-- /vex-main-action -->

            <!-- 历史记录（同款 glv-history 视觉） -->
            <div class="glv-history" id="brv2-history">
                <div class="glv-result-head">
                    <div class="glv-result-title" data-i18n="brv2-history-title">近期对账记录</div>
                    <input type="text" class="hist-search-input" id="brv2-hist-search"
                           data-i18n-placeholder="brv2-hist-search-ph" placeholder="搜索..." autocomplete="off">
                </div>
                <div class="glv-history-empty" id="brv2-history-empty" data-i18n="brv2-history-empty">
                    暂无对账记录
                </div>
                <div class="glv-history-table-wrap" id="brv2-history-table-wrap" style="display:none">
                    <table class="glv-history-table" id="brv2-history-table">
                        <thead>
                            <tr>
                                <th data-i18n="brv2-hist-time">时间</th>
                                <th data-i18n="brv2-hist-files">文件</th>
                                <th class="glv-num" data-i18n="brv2-hist-rows">账单/GL行数</th>
                                <th class="glv-num" data-i18n="brv2-hist-matched">已匹配</th>
                                <th class="glv-num" data-i18n="brv2-hist-gl-only">GL仅有</th>
                                <th class="glv-num" data-i18n="brv2-hist-stmt-only">账单仅有</th>
                                <th class="glv-num" data-i18n="brv2-hist-diff">差额</th>
                                <th data-i18n="brv2-hist-actions">操作</th>
                            </tr>
                        </thead>
                        <tbody id="brv2-history-tbody"></tbody>
                    </table>
                    <div class="hist-pager" id="brv2-history-pager" style="display:none">
                        <button class="hist-pager-btn" id="brv2-history-prev" type="button" disabled>&#8592;</button>
                        <span class="hist-pager-info" id="brv2-history-pager-info"></span>
                        <button class="hist-pager-btn" id="brv2-history-next" type="button">&#8594;</button>
                    </div>
                </div>
            </div>

        </div><!-- /recon-pane-bank -->

`,us=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
        <div id="recon-pane-sale-vat" class="recon-pane" style="display:none">


            <!-- v4.10.7 · KPI 3 卡统一视觉 -->
            <div class="vex-kpi-strip" id="vex-kpi-strip">
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-warn">⏱</div>
                    <div>
                        <div class="vex-kpi-val" id="vex-kpi-running-val">—</div>
                        <div class="vex-kpi-lbl" data-i18n="vex-kpi-running">进行中</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-ok">✓</div>
                    <div>
                        <div class="vex-kpi-val" id="vex-kpi-done-val">—</div>
                        <div class="vex-kpi-lbl" data-i18n="vex-kpi-done">已完成</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-err">!</div>
                    <div>
                        <div class="vex-kpi-val" id="vex-kpi-failed-val">—</div>
                        <div class="vex-kpi-lbl" data-i18n="vex-kpi-failed">失败</div>
                    </div>
                </div>
            </div>

            <!-- v4.10.6 · 主操作区(上移到列表上方) -->
            <div class="vex-main-action">
                <div class="vex-main-action-tag" data-i18n="vex-main-action-tag">主操作</div>

            <!-- v118.32.4.10.1 · Excel 对账上传区(全网开放) -->
            <div id="vex-pane">
                <!-- 左右双拖拽区(防呆 · 中间间距) -->
                <div class="vex-drops">
                    <div class="vex-drop vex-drop-invoice" id="vex-drop-invoice" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 4h12l6 6v16a2 2 0 01-2 2H8a2 2 0 01-2-2V6a2 2 0 012-2z"/>
                                <path d="M20 4v6h6M10 16h12M10 21h8"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="vex-drop-invoice-title">销售发票</div>
                        <div class="vex-drop-sub" data-i18n="vex-drop-invoice-sub">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <input type="file" id="vex-input-invoice" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" style="display:none">
                    </div>
                    <div class="vex-drop-divider" aria-hidden="true">
                        <span>+</span>
                    </div>
                    <div class="vex-drop vex-drop-report" id="vex-drop-report" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="5" y="6" width="22" height="20" rx="2"/>
                                <line x1="5" y1="12" x2="27" y2="12"/>
                                <line x1="10" y1="6" x2="10" y2="12"/>
                                <line x1="22" y1="6" x2="22" y2="12"/>
                                <line x1="9" y1="17" x2="16" y2="17"/>
                                <line x1="9" y1="21" x2="14" y2="21"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="vex-drop-report-title">VAT 报告</div>
                        <div class="vex-drop-sub" data-i18n="vex-drop-report-sub">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <input type="file" id="vex-input-report" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" style="display:none">
                    </div>
                </div>

                <!-- 操作栏 -->
                <div class="vex-action-bar">
                    <button class="btn btn-ghost" id="vex-reset" type="button" data-i18n="vex-btn-reset">清空</button>
                    <div class="vex-action-info" id="vex-action-info"></div>
                    <button class="vex-toggle-preview-btn" id="vex-toggle-preview" type="button">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                        <span id="vex-toggle-preview-label" data-i18n="vex-toggle-preview-open">查看清单</span>
                    </button>
                    <button class="btn btn-primary" id="vex-build" type="button" disabled>
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M8 2v9M4 7l4 4 4-4M3 14h10"/>
                        </svg>
                        <span data-i18n="vex-btn-build">开始对账</span>
                    </button>
                </div>

                <!-- v4.10.11 · 上传清单预览面板 -->
                <div class="vex-preview-panel" id="vex-preview-panel" style="display:none">
                    <div class="vex-pp-grid">
                        <div id="vex-pp-invoice-col"></div>
                        <div id="vex-pp-report-col"></div>
                    </div>
                    <div class="vex-pp-guide" id="vex-pp-guide" style="display:none">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                        <span data-i18n="vex-preview-guide-search">文件多(800+ 张)时用搜索框过滤 · 滚动到底自动加载</span>
                    </div>
                </div>

                <!-- 进度区(跑中显示) -->
                <div class="vex-progress" id="vex-progress" style="display:none">
                    <div class="spinner"></div>
                    <div>
                        <div class="vex-progress-title" id="vex-progress-title" data-i18n="vex-progress-running">对账中…</div>
                        <div class="vex-progress-sub" id="vex-progress-sub"></div>
                    </div>
                </div>

                <!-- v118.32.5.5.19 · 对账汇总 折叠区(对齐 GL 风格 · 跑完后显示)-->
                <div class="recon-collapse" id="vex-summary-collapse" data-collapsed="true" style="display:none;margin-top:14px">
                    <div class="recon-collapse-head" data-toggle="vex-summary-collapse" tabindex="0" role="button">
                        <svg class="recon-collapse-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="5 7 8 10 11 7"/>
                        </svg>
                        <span class="recon-collapse-title" data-i18n="vex-summary-title">对账汇总</span>
                        <span class="recon-collapse-sub" id="vex-summary-sub"></span>
                        <div class="glv-section-spacer"></div>
                        <a class="btn btn-ghost btn-small glv-section-action" id="vex-download" href="#" download style="display:none">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2v9M4 7l4 4 4-4M3 14h10"/>
                            </svg>
                            <span data-i18n="glv-btn-export">导出 Excel</span>
                        </a>
                    </div>
                    <div class="recon-collapse-body">
                        <div class="recon-summary-grid" id="vex-summary-grid">
                            <div class="recon-sum-card"><div class="recon-sum-val" id="vex-sum-total">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-total">总笔数</div></div>
                            <div class="recon-sum-card"><div class="recon-sum-val recon-sum-ok" id="vex-sum-matched">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-matched">完全一致</div></div>
                            <div class="recon-sum-card"><div class="recon-sum-val recon-sum-warn" id="vex-sum-diff">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-diff">数据差异</div></div>
                            <div class="recon-sum-card"><div class="recon-sum-val recon-sum-err" id="vex-sum-incomplete">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-incomplete">OCR 漏识别</div></div>
                            <div class="recon-sum-card"><div class="recon-sum-val" id="vex-sum-cash">—</div><div class="recon-sum-lbl" data-i18n="vex-sum-cash">散客无发票</div></div>
                        </div>
                    </div>
                </div>

                <!-- v118.32.5.5.19 · 差异明细 折叠区(列出最新任务的字段差异行)-->
                <div class="recon-collapse" id="vex-detail-collapse" data-collapsed="true" style="display:none;margin-top:10px">
                    <div class="recon-collapse-head" data-toggle="vex-detail-collapse" tabindex="0" role="button">
                        <svg class="recon-collapse-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="5 7 8 10 11 7"/>
                        </svg>
                        <span class="recon-collapse-title" data-i18n="vex-detail-title">差异明细</span>
                        <span class="recon-collapse-sub" id="vex-detail-sub"></span>
                    </div>
                    <div class="recon-collapse-body">
                        <div class="recon-detail-empty" id="vex-detail-empty" data-i18n="vex-detail-empty">本次对账未发现差异</div>
                        <table class="recon-detail-table" id="vex-detail-table" style="display:none">
                            <thead>
                                <tr>
                                    <th data-i18n="vex-detail-h-inv">发票号</th>
                                    <th data-i18n="vex-detail-h-field">差异字段</th>
                                    <th data-i18n="vex-detail-h-rep">报告侧</th>
                                    <th data-i18n="vex-detail-h-inv-side">发票侧</th>
                                    <th data-i18n="vex-detail-h-kind">类型</th>
                                </tr>
                            </thead>
                            <tbody id="vex-detail-tbody"></tbody>
                        </table>
                    </div>
                </div>

                <!-- vex-download 已移至 vex-summary-collapse 头部 -->
            </div><!-- /vex-pane -->
            </div><!-- /vex-main-action -->

            <!-- v4.10.6 · 历史任务列表(移到主操作下方) -->
            <div class="vex-task-section" id="vex-task-section">
                <div class="vex-task-header-wrap">
                    <div class="vex-task-header" data-i18n="sv-recent-tasks">近期对账任务</div>
                    <input type="text" class="hist-search-input" id="vex-task-search" data-i18n-placeholder="hist-search-ph" placeholder="搜索..." autocomplete="off">
                </div>
                <div class="vex-task-table-wrap">
                    <table class="vex-task-table">
                        <thead>
                            <tr>
                                <th data-i18n="vex-col-time">创建时间</th>
                                <th data-i18n="vex-col-client">客户</th>
                                <th data-i18n="vex-col-period">期间</th>
                                <th data-i18n="vex-col-count">笔数</th>
                                <th data-i18n="vex-col-kpi">核对结果</th>
                                <th data-i18n="vex-col-diff">异常金额</th>
                                <th data-i18n="vex-col-status">状态</th>
                                <th data-i18n="vex-col-elapsed">用时</th>
                                <th data-i18n="vex-col-actions">操作</th>
                            </tr>
                        </thead>
                        <tbody id="vex-task-tbody"></tbody>
                    </table>
                    <div class="hist-pager" id="vex-task-pager" style="display:none">
                        <button class="hist-pager-btn" id="vex-task-prev" type="button" disabled>&#8592;</button>
                        <span class="hist-pager-info" id="vex-task-pager-info"></span>
                        <button class="hist-pager-btn" id="vex-task-next" type="button">&#8594;</button>
                    </div>
                </div>
            </div>

            <!-- ── 新建对账抽屉/模态(屏 A 核心) ── -->

        </div><!-- /recon-pane-sale-vat -->

        <!-- ══════════════════════════════════════════════════════════════
             v118.32.5 · GL vs 销项税报告 收入对账面板
             复用 vex-drops / vex-drop / vex-action-bar 现有视觉
             ══════════════════════════════════════════════════════════════ -->
        <div id="recon-pane-gl-vat" class="recon-pane" style="display:none">


            <!-- KPI 3 卡（沿用 vex-kpi-strip 视觉 · 默认可见，跑完更新数字） -->
            <div class="vex-kpi-strip" id="glv-kpi-strip">
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-ok">✓</div>
                    <div>
                        <div class="vex-kpi-val" id="glv-kpi-matched">—</div>
                        <div class="vex-kpi-lbl" data-i18n="glv-kpi-matched">完全匹配</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-warn">⚠</div>
                    <div>
                        <div class="vex-kpi-val" id="glv-kpi-diff">—</div>
                        <div class="vex-kpi-lbl" data-i18n="glv-kpi-diff">有差异</div>
                    </div>
                </div>
                <div class="vex-kpi-card">
                    <div class="vex-kpi-icon-wrap vex-kpi-icon-err">!</div>
                    <div>
                        <div class="vex-kpi-val" id="glv-kpi-unmatched">—</div>
                        <div class="vex-kpi-lbl" data-i18n="glv-kpi-unmatched">GL 未找到</div>
                    </div>
                </div>
            </div>

            <!-- 主操作区(沿用 vex-main-action 视觉) -->
            <div class="vex-main-action">
                <div class="vex-main-action-tag" data-i18n="vex-main-action-tag">主操作</div>

                <!-- 左右双拖拽区 -->
                <div class="vex-drops">
                    <div class="vex-drop vex-drop-invoice" id="glv-drop-vat" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="5" y="6" width="22" height="20" rx="2"/>
                                <line x1="5" y1="12" x2="27" y2="12"/>
                                <line x1="10" y1="6" x2="10" y2="12"/>
                                <line x1="22" y1="6" x2="22" y2="12"/>
                                <line x1="9" y1="17" x2="16" y2="17"/>
                                <line x1="9" y1="21" x2="14" y2="21"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="glv-up-vat-title">① 销项税报告</div>
                        <div class="vex-drop-sub"   data-i18n="glv-up-vat-sub">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <div class="vex-drop-filename" id="glv-vat-name"></div>
                        <input type="file" id="glv-vat-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt" multiple style="display:none">
                    </div>

                    <div class="vex-drop-divider" aria-hidden="true"><span>+</span></div>

                    <div class="vex-drop vex-drop-report" id="glv-drop-gl" role="button" tabindex="0">
                        <div class="vex-drop-icon-wrap">
                            <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M6 6h20v6H6z"/>
                                <path d="M6 14h10v12H6z"/>
                                <path d="M18 14h8v6h-8z"/>
                                <path d="M18 22h8v4h-8z"/>
                            </svg>
                        </div>
                        <div class="vex-drop-title" data-i18n="glv-up-gl-title">② 总账 GL</div>
                        <div class="vex-drop-sub"   data-i18n="glv-up-gl-sub">PDF / 图片 / Excel / CSV / Word · 多文件 · 自动识别</div>
                        <div class="vex-drop-filename" id="glv-gl-name"></div>
                        <input type="file" id="glv-gl-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.bmp,.gif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc,.txt" multiple style="display:none">
                    </div>
                </div>

                <!-- 操作栏 · v5.5.23 加 toggle 查看清单按钮 · 复刻销售税核查同款 -->
                <div class="vex-action-bar">
                    <button class="btn btn-ghost" id="btn-glv-reset" type="button" data-i18n="vex-btn-reset">清空</button>
                    <div class="vex-action-info muted" id="glv-status">
                        <span data-i18n="glv-hint-need-both">请先上传两份文件</span>
                    </div>
                    <button class="vex-toggle-preview-btn" id="glv-toggle-preview" type="button">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                        <span id="glv-toggle-preview-label" data-i18n="vex-toggle-preview-open">查看清单</span>
                    </button>
                    <label class="glv-acct-prefix-wrap">
                        <span class="glv-acct-prefix-lbl" data-i18n="glv-acct-prefix">收入科目前缀</span>
                        <input type="text" id="glv-prefix" value="4" maxlength="3" class="glv-acct-prefix-input">
                    </label>
                    <button class="btn btn-primary" id="btn-glv-run" type="button" disabled>
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 8l4 4 6-8"/>
                        </svg>
                        <span data-i18n="glv-btn-run">开始对账</span>
                    </button>
                </div>

                <!-- v5.5.23 · 查看清单面板(同款 .vex-preview-panel 视觉) -->
                <div class="vex-preview-panel" id="glv-preview-panel" style="display:none">
                    <div class="vex-pp-grid">
                        <div id="glv-pp-vat-col"></div>
                        <div id="glv-pp-gl-col"></div>
                    </div>
                </div>

                <!-- 跑中进度 -->
                <div class="vex-progress" id="glv-progress" style="display:none">
                    <div class="spinner"></div>
                    <div>
                        <div class="vex-progress-title" data-i18n="glv-running">对账中…</div>
                        <div class="vex-progress-sub" id="glv-progress-sub"></div>
                    </div>
                </div>

                <!-- 结果区(默认隐藏) -->
                <div id="glv-result" style="display:none;margin-top:14px;">
                    <!-- 对账汇总 · 可折叠分区（默认收起） -->
                    <div class="glv-section" id="glv-section-summary" data-collapsed="true">
                        <div class="glv-section-head" data-toggle="glv-section-summary" tabindex="0" role="button">
                            <svg class="glv-section-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="5 7 8 10 11 7"/>
                            </svg>
                            <span class="glv-section-title" data-i18n="glv-summary-title">对账汇总</span>
                            <div class="glv-section-spacer"></div>
                            <button class="btn btn-ghost btn-small glv-section-action" id="btn-glv-export" type="button">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M8 2v9M4 7l4 4 4-4M3 14h10"/>
                                </svg>
                                <span data-i18n="glv-btn-export">导出 Excel</span>
                            </button>
                        </div>
                        <div class="glv-section-body">
                            <table class="glv-summary-table" id="glv-summary-table">
                                <tbody></tbody>
                            </table>
                        </div>
                    </div>

                    <!-- 差异明细 · 可折叠分区（默认收起） -->
                    <div class="glv-section" id="glv-section-detail" data-collapsed="true" style="margin-top:10px;">
                        <div class="glv-section-head" data-toggle="glv-section-detail" tabindex="0" role="button">
                            <svg class="glv-section-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="5 7 8 10 11 7"/>
                            </svg>
                            <span class="glv-section-title" data-i18n="glv-detail-title">差异明细</span>
                            <span class="glv-section-count" id="glv-detail-count"></span>
                        </div>
                        <div class="glv-section-body">
                            <div class="glv-table-wrap">
                                <table class="glv-table" id="glv-table">
                                    <thead>
                                        <tr>
                                            <th data-i18n="glv-h-doc">单据号</th>
                                            <th data-i18n="glv-h-date">日期</th>
                                            <th data-i18n="glv-h-customer">客户</th>
                                            <th class="glv-num" data-i18n="glv-h-vat">VAT 金额</th>
                                            <th class="glv-num" data-i18n="glv-h-gl">GL 金额</th>
                                            <th class="glv-num" data-i18n="glv-h-diff">差异</th>
                                            <th data-i18n="glv-h-acct">收入科目</th>
                                        </tr>
                                    </thead>
                                    <tbody id="glv-tbody"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div><!-- /glv-result -->
            </div><!-- /vex-main-action -->

            <!-- 近期对账任务（沿用销项税对账的视觉） -->
            <div class="glv-history" id="glv-history">
                <div class="glv-result-head">
                    <div class="glv-result-title" data-i18n="glv-history-title">近期对账任务</div>
                    <input type="text" class="hist-search-input" id="glv-hist-search" data-i18n-placeholder="hist-search-ph" placeholder="搜索..." autocomplete="off">
                </div>
                <div class="glv-history-empty" id="glv-history-empty" data-i18n="glv-history-empty">
                    暂无对账记录
                </div>
                <div class="glv-history-table-wrap" id="glv-history-table-wrap" style="display:none;">
                <table class="glv-history-table" id="glv-history-table">
                    <thead>
                        <tr>
                            <th data-i18n="glv-hist-time">时间</th>
                            <th data-i18n="glv-hist-files">文件</th>
                            <th class="glv-num" data-i18n="glv-hist-rows">行数 (VAT/GL)</th>
                            <th class="glv-num" data-i18n="glv-hist-matched">匹配</th>
                            <th class="glv-num" data-i18n="glv-hist-diff">差异</th>
                            <th class="glv-num" data-i18n="glv-hist-missing">缺失</th>
                            <th data-i18n="glv-hist-actions">操作</th>
                        </tr>
                    </thead>
                    <tbody id="glv-history-tbody"></tbody>
                </table>
                <div class="hist-pager" id="glv-history-pager" style="display:none">
                    <button class="hist-pager-btn" id="glv-history-prev" type="button" disabled>&#8592;</button>
                    <span class="hist-pager-info" id="glv-history-pager-info"></span>
                    <button class="hist-pager-btn" id="glv-history-next" type="button">&#8594;</button>
                </div>
                </div>
            </div>

        </div><!-- /recon-pane-gl-vat -->


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=ps+us,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 16L4 21M15 8l5-5"/>
                    <path d="M11 5L6 10a3 3 0 000 4l4 4a3 3 0 004 0l5-5a3 3 0 000-4l-4-4a3 3 0 00-4 0z"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="integrations-title">集成</div>
                <div class="page-head-sub" data-i18n="integrations-sub">Google · LINE · 邮箱 · ERP · 文件夹 · 云盘 等第三方授权 · 让 Pearnly 自动同步数据</div>
            </div>
        </div>

        <!-- A4 · 顶部 tab 切换 -->
        <div class="int-top-tabs" role="tablist">
            <button class="int-top-tab active" type="button" data-int-top-tab="cards" data-i18n="int-tab-cards">集成卡片</button>
            <button class="int-top-tab" type="button" data-int-top-tab="logs" data-i18n="int-tab-logs">推送日志</button>
        </div>

        <!-- Tab 1: integration-row 卡片(现有内容不变) -->
        <div class="int-top-panel active" data-int-top-panel="cards">
        <div class="card">
            <!-- Google 一次授权双服务 · 蓝色信息条 -->
            <div class="integrations-info-bar">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="8"/>
                    <line x1="10" y1="6" x2="10" y2="10"/>
                    <circle cx="10" cy="14" r="0.6" fill="currentColor"/>
                </svg>
                <span data-i18n="integrations-google-info">授权一次 Google 账号 · Drive 和 Sheets 均可使用 · 无需重复授权</span>
            </div>

            <!-- 第 1 组 · Google 服务 -->
            <div class="integrations-section-title" data-i18n="integrations-section-google">GOOGLE 服务</div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="google-drive">
                <div class="int-icon ic-g">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L4 16h6l2-4h4l2 4h-6L12 2z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-drive">Google Drive</span></div>
                    <div class="int-desc" data-i18n="int-desc-drive">发票/PV 审核后自动存入 Drive · 按客户和月份归档</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="google-sheets">
                <div class="int-icon ic-gs">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-sheets">Google Sheets</span></div>
                    <div class="int-desc" data-i18n="int-desc-sheets">识别结果实时同步到 Sheets · 老板/会计师在线查看</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="sec-divider"></div>

            <!-- 第 2 组 · 收票渠道(含 Gmail · v118.32.5.5.37 调整) -->
            <div class="integrations-section-title" data-i18n="integrations-section-channels">收票渠道</div>

            <!-- Gmail 抓取移至收票渠道(邮件是收票渠道 · 非 Google 产品功能) -->
            <div class="integration-row" data-int-target="automation" data-int-anchor="gmail">
                <div class="int-icon ic-gm">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="5" width="18" height="14" rx="2"/>
                        <path d="M3 7l9 6 9-6"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-gmail">Gmail 抓取</span></div>
                    <div class="int-desc" data-i18n="int-desc-gmail">客户发来邮件附件自动抓 · 不用手动转发</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="line">
                <div class="int-icon ic-line">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 5.96 2 10.84c0 4.37 3.55 8.04 8.36 8.74.32.07.77.21.88.49.1.25.07.65.03.91l-.14.86c-.04.25-.2.99.87.54 1.07-.46 5.77-3.4 7.87-5.82C21.32 15.04 22 13.05 22 10.84 22 5.96 17.52 2 12 2z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-line">LINE Bot</span></div>
                    <div class="int-desc" data-i18n="int-desc-line">外勤拍照发 LINE · 自动入账 · 单聊群聊都支持</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="folder">
                <div class="int-icon ic-folder">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 7a2 2 0 012-2h4l2 3h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-folder">文件夹监听</span></div>
                    <div class="int-desc" data-i18n="int-desc-folder">指定本地/共享文件夹 · 扔进去就自动识别</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="sec-divider"></div>

            <!-- 第 3 组 · ERP 系统 -->
            <div class="integrations-section-title" data-i18n="integrations-section-erp">ERP 系统</div>

            <div class="integration-row" data-int-target="automation" data-int-anchor="erp">
                <div class="int-icon ic-erp">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M9 9h6v6H9z"/>
                        <path d="M9 3v6M15 3v6M9 15v6M15 15v6M3 9h6M3 15h6M15 9h6M15 15h6"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="int-name-erp">ERP 对接</span></div>
                    <div class="int-desc" data-i18n="int-desc-erp">Xero · MR.ERP · Webhook 等 · 识别完自动推到 ERP</div>
                </div>
                <div class="int-actions">
                    <!-- Bug 4 (Zihao 2026-05-19 拍板 · v118.34.22) · 集成卡片右下「看推送日志」link 删 ·
                         入口收敛: 点「配置」进 ERP 抽屉 → 在抽屉里点「看推送日志 →」 ·
                         或直接点集成主页顶部的「推送日志」tab. -->
                    <button class="int-btn-configure" data-route="automation" data-i18n="btn-configure">配置</button>
                </div>
            </div>

            <div class="sec-divider"></div>

            <!-- v118.32.5.5.37 NAV-IA Phase 5 收尾 · 自动化 & 提醒 区块 -->
            <div class="integrations-section-title" data-i18n="int-section-automation">通知提醒</div>

            <div class="integration-row" data-int-target="drawer" data-int-anchor="alert">
                <div class="int-icon ic-alert">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                        <path d="M10 21a2 2 0 0 0 4 0"/>
                    </svg>
                </div>
                <div class="int-info">
                    <div class="int-name"><span data-i18n="auto-alert-title">智能提醒</span></div>
                    <div class="int-desc" data-i18n="auto-alert-desc">异常 high 或大额发票发生时 · 自动推送到老板/会计的 LINE</div>
                </div>
                <div class="int-actions">
                    <button class="int-btn-configure" data-i18n="btn-configure">配置</button>
                </div>
            </div>
        </div>
        </div>
        <!-- /Tab 1 -->

        <!-- Tab 2: 推送日志(从 auto-panel="erp" subpanel="logs" 搬过来 · A4 · v118.34.19) -->
        <div class="int-top-panel" data-int-top-panel="logs">
            <div class="card">
                <!-- 今日推送统计 -->
                <div id="erp-today-stats" class="erp-today-stats"></div>
                <section class="erp-logs-section" id="erp-logs-section">
                    <div class="erp-logs-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 1"/>
                        </svg>
                        <span data-i18n="erp-logs-title">推送日志</span>
                        <span class="erp-logs-today-stats" id="erp-logs-today-stats"></span>
                    </div>

                    <div class="erp-logs-toolbar">
                        <div class="erp-logs-filters" id="erp-logs-filters">
                            <button class="chip-filter active" data-filter-key="all" data-filter-val=""><span data-i18n="erp-logs-filter-all">全部</span></button>
                            <button class="chip-filter" data-filter-key="status" data-filter-val="success">✓ <span data-i18n="erp-logs-filter-ok">成功</span></button>
                            <button class="chip-filter" data-filter-key="status" data-filter-val="retrying">↻ <span data-i18n="erp-logs-filter-retrying">重试中</span></button>
                            <button class="chip-filter" data-filter-key="status" data-filter-val="failed">✗ <span data-i18n="erp-logs-filter-fail">失败</span></button>
                            <button class="chip-filter" data-filter-key="trigger" data-filter-val="auto"><span data-i18n="erp-logs-filter-auto">自动</span></button>
                            <button class="chip-filter" data-filter-key="trigger" data-filter-val="manual"><span data-i18n="erp-logs-filter-manual">手动</span></button>
                            <!-- DMS 推送可视化闭环(Zihao 2026-06-01)· ERP 系统筛选改【下拉】·
                                 只列真实配置的 ERP 端点(loadErpLogs 运行期填充)· 选一个看一个 · 不再硬编码三件套混在一起. -->
                            <span class="erp-logs-filter-sep" aria-hidden="true">|</span>
                            <select id="erp-logs-erp-select" class="erp-logs-erp-select" aria-label="ERP">
                                <option value="" data-i18n="erp-logs-erp-all">全部 ERP</option>
                            </select>
                        </div>
                        <button class="btn btn-ghost btn-tiny" id="btn-refresh-logs" title="刷新">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                        </button>
                    </div>

                    <div id="erp-logs-batch-bar" class="erp-logs-batch-bar" style="display:none;">
                        <span class="erp-logs-batch-count" id="erp-logs-batch-count" data-i18n="erp-batch-selected" data-i18n-vars='{"n":0}'>已选 0 条</span>
                        <button class="btn btn-primary btn-tiny" id="btn-erp-batch-retry">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                            <span data-i18n="erp-batch-retry-btn">批量重推</span>
                        </button>
                        <!-- Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除按钮 -->
                        <button class="btn btn-ghost btn-tiny btn-danger-ghost" id="btn-erp-batch-delete">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h8M5 4V2.5h4V4M6 7v4M8 7v4M4 4l.5 8h5l.5-8"/></svg>
                            <span data-i18n="erp-batch-delete-btn">批量删除</span>
                        </button>
                        <button class="btn btn-ghost btn-tiny" id="btn-erp-batch-clear">
                            <span data-i18n="erp-batch-clear">取消选择</span>
                        </button>
                    </div>

                    <div id="erp-logs-list" class="erp-logs-list">
                        <div class="erp-logs-empty" data-i18n="erp-logs-loading">加载中…</div>
                    </div>
                </section>
            </div>
        </div>
        <!-- /Tab 2 -->
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-settings");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <!-- v118.27.5.1 · page-head · 视觉对齐自动化页/识别中心 -->
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="set-page-title">设置</div>
                <div class="page-head-sub" data-i18n="set-page-sub">管理你的账户、公司和工作流</div>
            </div>
        </div>

        <!-- v118.27.5.2 · settings-layout wrapper · 跟自动化 .auto-layout 同结构 · 修响应式问题 -->
        <div class="settings-layout">
            <!-- v118.27.4 · 设置左侧 4 大类二级导航 · 参考 Notion / Linear · 替代原顶部水平 tabs -->
            <aside class="settings-side-nav" id="settings-tabs">
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-account">账户</div>
                <button class="settings-tab settings-nav-item active" data-tab="profile" data-i18n="set-tab-profile">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="7" r="3.5"/><path d="M3.5 17a6.5 6.5 0 0113 0"/></svg>
                    <span>个人资料</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="security" data-i18n="set-tab-security">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="8" rx="1.5"/><path d="M7 9V6.5a3 3 0 016 0V9"/></svg>
                    <span>账户安全</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="notifications" data-i18n="set-tab-notifications">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8a5 5 0 0110 0v4l1.5 2h-13l1.5-2V8z"/><path d="M8 17a2 2 0 004 0"/></svg>
                    <span>通知偏好</span>
                </button>
            </div>
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-company">公司</div>
                <button class="settings-tab settings-nav-item" data-tab="company" data-i18n="set-tab-company">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17V7l7-3 7 3v10"/><path d="M3 17h14M8 12h4M8 17v-4"/></svg>
                    <span>公司信息</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="team" data-i18n="set-tab-team">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="14" cy="6.5" r="3"/><circle cx="6" cy="6.5" r="3"/><path d="M2 17v-1.5a3 3 0 013-3h2a3 3 0 013 3V17M11 13a3 3 0 013-3h2a3 3 0 013 3v4"/></svg>
                    <span>团队管理</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="plan" data-i18n="set-tab-plan">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="14" height="10" rx="1.5"/><path d="M3 9h14M7 13h2"/></svg>
                    <span>用量</span>
                </button>
            </div>
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-workflow">工作流</div>
                <button class="settings-tab settings-nav-item" data-tab="archive" data-i18n="set-tab-archive">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="14" height="3" rx="0.5"/><rect x="4" y="8" width="12" height="9" rx="1"/><path d="M8 11h4"/></svg>
                    <span>归档规则</span>
                </button>
                <button class="settings-tab settings-nav-item" data-tab="learned" data-i18n="set-tab-learned">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="6.5"/><path d="M7 10l2 2 4-4"/></svg>
                    <span>学习规则</span>
                </button>
                <!-- v118.35.0.16 · API & 密钥 tab 永久下线 · credits 系统接管 -->
            </div>
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-system">系统</div>
                <button class="settings-tab settings-nav-item" data-tab="general" data-i18n="set-tab-general">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="2.5"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M4.2 15.8l1.4-1.4M14.4 5.6l1.4-1.4"/></svg>
                    <span>通用设置</span>
                </button>
                <!-- v118.28.8 · 仅 owner 可见 · 由 JS 控制显隐 -->
                <button class="settings-tab settings-nav-item set-tab-owner-only" data-tab="access-log" data-i18n="set-tab-access-log" style="display:none;">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="14" height="14" rx="2"/><path d="M7 8h6M7 11h6M7 14h4"/></svg>
                    <span>Pearnly 访问日志</span>
                </button>
            </div>
            <div class="settings-nav-group">
                <div class="settings-nav-group-title" data-i18n="set-group-about">关于</div>
                <button class="settings-tab settings-nav-item" data-tab="about" data-i18n="set-tab-about">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 13V9.5M10 7v0.01"/></svg>
                    <span>联系我们</span>
                </button>
            </div>
        </aside>

        <div class="settings-content">
            <!-- Tab 1 · 个人资料 -->
            <div class="settings-pane active" data-pane="profile">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-profile-title">个人资料</div>
                        <div class="section-sub" data-i18n="set-profile-sub">这些信息只用于个性化体验 · 不会公开</div>
                    </div>
                    <div class="profile-form">
                        <div class="form-row">
                            <label data-i18n="set-profile-username">用户名</label>
                            <input type="text" id="profile-username" class="form-input" disabled>
                            <div class="form-hint" data-i18n="set-profile-username-hint">用户名注册后不可修改</div>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-email">邮箱</label>
                            <input type="email" id="profile-email" class="form-input" disabled>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-fullname">姓名(选填)</label>
                            <input type="text" id="profile-fullname" class="form-input" maxlength="64">
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-phone">电话(选填)</label>
                            <input type="tel" id="profile-phone" class="form-input" maxlength="32">
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-country">国家</label>
                            <select id="profile-country" class="form-input">
                                <option value="TH" data-i18n="country-th">泰国</option>
                                <option value="CN" data-i18n="country-cn">中国</option>
                                <option value="JP" data-i18n="country-jp">日本</option>
                                <option value="US" data-i18n="country-us">美国</option>
                                <option value="EN" data-i18n="country-other">其他</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-profile-line">LINE ID(选填)</label>
                            <input type="text" id="profile-line" class="form-input" maxlength="64" placeholder="@username">
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-primary" id="btn-save-profile" data-i18n="set-save">保存修改</button>
                            <span class="form-msg" id="profile-save-msg"></span>
                        </div>
                    </div>
                </div>

                <!-- v118.28.5.1 · profile pane 不再放语言 · 已迁到 系统 → 通用设置 -->
            </div>

            <!-- Tab 2 · 公司信息 -->
            <div class="settings-pane" data-pane="company">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-company-title">公司信息</div>
                        <div class="section-sub" data-i18n="set-company-sub">显示在工作台顶部和导出文件上 · 让团队成员有归属感</div>
                    </div>
                    <div class="profile-form">
                        <div class="form-row">
                            <label data-i18n="set-company-name">公司名称(选填)</label>
                            <input type="text" id="company-name" class="form-input" maxlength="200" placeholder="例如:ABC 会计事务所">
                            <div class="form-hint" data-i18n="set-company-name-hint">没有公司可留空 · 顶部将显示您的邮箱前缀</div>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-company-volume">月发票量(选填)</label>
                            <select id="company-volume" class="form-input">
                                <option value="" data-i18n="set-company-volume-none">— 选择 —</option>
                                <option value="0-50" data-i18n="vol-0-50">0-50 张</option>
                                <option value="50-200" data-i18n="vol-50-200">50-200 张</option>
                                <option value="200-1000" data-i18n="vol-200-1000">200-1000 张</option>
                                <option value="1000+" data-i18n="vol-1000-plus">1000+ 张</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <label data-i18n="set-company-role">您的身份(选填)</label>
                            <select id="company-role" class="form-input">
                                <option value="" data-i18n="set-company-role-none">— 选择 —</option>
                                <option value="firm_owner" data-i18n="role-firm-owner">事务所老板 / 合伙人</option>
                                <option value="bookkeeper" data-i18n="role-bookkeeper">事务所会计 / 簿记员</option>
                                <option value="biz_owner" data-i18n="role-biz-owner">公司老板</option>
                                <option value="biz_finance" data-i18n="role-biz-finance">公司财务</option>
                                <option value="freelance" data-i18n="role-freelance">自由会计 / 个人</option>
                                <option value="other" data-i18n="role-other">其他</option>
                            </select>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-primary" id="btn-save-company" data-i18n="set-save">保存修改</button>
                            <span class="form-msg" id="company-save-msg"></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 3 · 账户安全(修改密码) -->
            <div class="settings-pane" data-pane="security">
                <!-- v109.4 · 修改密码 -->
                <div class="card" id="change-pw-card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="settings-change-pw-title">修改密码</div>
                        <div class="section-sub" data-i18n="set-security-sub">建议每 90 天更换一次密码</div>
                    </div>
                    <!-- 防 autofill 诱饵字段 · 浏览器会把密码塞到这两个隐藏 input · 而不是真正的输入框 -->
                    <input type="text" name="username" autocomplete="username" style="display:none" tabindex="-1" aria-hidden="true">
                    <input type="password" name="password" autocomplete="current-password" style="display:none" tabindex="-1" aria-hidden="true">
                    <form class="change-pw-form" autocomplete="off" onsubmit="return false;">
                        <div class="cpw-field">
                            <label data-i18n="settings-change-pw-old">当前密码</label>
                            <div class="cpw-input-wrap">
                                <input type="password" id="cpw-old" class="cpw-input"
                                       name="cpw-old-randomname"
                                       autocomplete="off"
                                       autocorrect="off"
                                       autocapitalize="off"
                                       spellcheck="false"
                                       data-lpignore="true"
                                       data-1p-ignore="true"
                                       data-form-type="other"
                                       readonly
                                       value="">
                                <button type="button" class="cpw-eye" data-target="cpw-old" aria-label="show password">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z"/><circle cx="10" cy="10" r="2.5"/></svg>
                                </button>
                            </div>
                            <div class="cpw-forgot-row">
                                <button type="button" class="cpw-forgot-link" id="cpw-forgot-link" data-i18n="settings-change-pw-forgot">忘记当前密码?</button>
                            </div>
                        </div>
                        <div class="cpw-field">
                            <label data-i18n="settings-change-pw-new">新密码</label>
                            <div class="cpw-input-wrap">
                                <input type="password" id="cpw-new" class="cpw-input"
                                       name="cpw-new-randomname"
                                       autocomplete="new-password"
                                       autocorrect="off"
                                       autocapitalize="off"
                                       spellcheck="false"
                                       data-lpignore="true"
                                       data-1p-ignore="true"
                                       readonly
                                       value="">
                                <button type="button" class="cpw-eye" data-target="cpw-new" aria-label="show password">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z"/><circle cx="10" cy="10" r="2.5"/></svg>
                                </button>
                            </div>
                            <div class="cpw-strength" id="cpw-strength"><div class="cpw-strength-bar" id="cpw-strength-bar"></div></div>
                            <div class="cpw-hint" data-i18n="settings-change-pw-hint">至少 8 位 · 包含字母和数字</div>
                        </div>
                        <div class="cpw-field">
                            <label data-i18n="settings-change-pw-confirm">确认新密码</label>
                            <div class="cpw-input-wrap">
                                <input type="password" id="cpw-confirm" class="cpw-input"
                                       name="cpw-confirm-randomname"
                                       autocomplete="new-password"
                                       autocorrect="off"
                                       autocapitalize="off"
                                       spellcheck="false"
                                       data-lpignore="true"
                                       data-1p-ignore="true"
                                       readonly
                                       value="">
                                <button type="button" class="cpw-eye" data-target="cpw-confirm" aria-label="show password">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z"/><circle cx="10" cy="10" r="2.5"/></svg>
                                </button>
                            </div>
                        </div>
                        <div class="cpw-msg" id="cpw-msg"></div>
                        <button type="button" class="btn btn-primary" id="btn-change-pw" data-i18n="settings-change-pw-submit">提交修改</button>
                    </form>
                </div>
            </div>

            <!-- Tab 4 · 通知偏好 -->
            <div class="settings-pane" data-pane="notifications">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-notif-title">通知偏好</div>
                        <div class="section-sub" data-i18n="set-notif-sub">控制智能提醒和检测的行为</div>
                    </div>
                    <div class="settings-prefs-inline">
                        <div class="pref-row">
                            <div class="pref-info">
                                <div class="pref-title" data-i18n="pref-dup-check-title">重复发票检测</div>
                                <div class="pref-desc" data-i18n="pref-dup-check-desc">上传后自动检查发票号或字段组合是否与历史重复 · 弹窗提示</div>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" id="pref-dup-check" checked>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 5 · 用量(CLEANUP-PLAN-03 · 2026-05-22 · 老"套餐 & 用量" 改) -->
            <div class="settings-pane" data-pane="plan">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-plan-title">用量</div>
                    </div>
                    <div id="settings-info"></div>
                </div>
            </div>

            <!-- Tab 6 · 团队管理(老板可见 · 由 JS 控制 tab 显隐) -->
            <div class="settings-pane settings-panel" data-pane="team" data-settings-panel="team">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="team-title">员工管理</div>
                        <div class="section-sub" data-i18n="team-sub">添加员工后 · 他能用自己的账号登录 · 只看到本公司数据</div>
                    </div>

                    <div class="admin-toolbar">
                        <button class="btn btn-primary" id="btn-add-employee">
                            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M10 4v12M4 10h12"/>
                            </svg>
                            <span data-i18n="team-add">添加员工</span>
                        </button>
                        <div class="admin-stats" id="team-count"></div>
                    </div>

                    <div class="admin-table-wrap">
                        <div id="team-loading" class="admin-loading" data-i18n="admin-loading">加载中...</div>
                        <div class="team-list" id="team-list" style="display:none;"></div>
                        <div id="team-empty" class="admin-empty" style="display:none;" data-i18n="team-empty">还没有员工 · 点「添加员工」开始</div>
                    </div>
                </div>
            </div>

            <!-- v118.19.1 · Tab · 归档规则(从识别中心右上角移过来 · 低频功能) -->
            <div class="settings-pane" data-pane="archive">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-archive-title">归档规则</div>
                        <div class="section-sub" data-i18n="set-archive-sub">设置批量下载 ZIP 时的文件命名模板 · 例如 日期_供应商_金额.pdf</div>
                    </div>
                    <button type="button" class="btn btn-primary" id="btn-open-archive-rule-from-settings" style="margin-top: 12px;">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px;vertical-align:-3px;margin-right:6px;">
                            <rect x="3" y="4" width="14" height="12" rx="2"/>
                            <path d="M3 8h14M7 12h6"/>
                        </svg>
                        <span data-i18n="set-archive-open-btn">打开命名规则编辑器</span>
                    </button>
                </div>
            </div>

            <!-- v118.35.0.16 · Tab 7 API & 密钥(BYO Gemini Key)整段永久下线 · credits 系统不再需要用户自带 key -->

            <!-- v118.21.2 · 学习规则(撤销「忽略此类」白名单) -->
            <div class="settings-pane" data-pane="learned">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-learned-title">学习规则</div>
                        <div class="section-sub" data-i18n="set-learned-sub">异常栏点过「永远忽略此类」后 · 系统会记住「该供应商 + 该规则」组合 · 下次自动放行 · 这里可撤销</div>
                    </div>
                    <div class="learned-list" id="learned-list">
                        <div class="learned-empty" data-i18n="set-learned-loading">加载中…</div>
                    </div>
                </div>
            </div>

            <!-- Tab · 通用设置(系统分组) -->
            <div class="settings-pane" data-pane="general">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-general-title">通用设置</div>
                        <div class="section-sub" data-i18n="set-general-sub">语言 · 时区 · 日期 · 数字格式 · 一次设完不再动</div>
                    </div>
                    <div class="profile-form">
                        <div class="form-row form-row-inline">
                            <label data-i18n="set-general-lang">界面语言</label>
                            <select id="general-lang" class="form-input">
                                <option value="th">ไทย (TH)</option>
                                <option value="en">English (EN)</option>
                                <option value="zh">中文 (ZH)</option>
                                <option value="ja">日本語 (JA)</option>
                            </select>
                            <div class="form-hint" data-i18n="set-general-lang-hint">立即生效 · 自动同步到所有设备</div>
                        </div>
                        <div class="form-row form-row-inline">
                            <label data-i18n="set-general-tz">时区</label>
                            <select id="general-tz" class="form-input">
                                <option value="Asia/Bangkok">Asia/Bangkok (UTC+7)</option>
                                <option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</option>
                                <option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</option>
                                <option value="Asia/Singapore">Asia/Singapore (UTC+8)</option>
                                <option value="Asia/Hong_Kong">Asia/Hong_Kong (UTC+8)</option>
                                <option value="Asia/Taipei">Asia/Taipei (UTC+8)</option>
                                <option value="Asia/Kuala_Lumpur">Asia/Kuala_Lumpur (UTC+8)</option>
                                <option value="Asia/Jakarta">Asia/Jakarta (UTC+7)</option>
                                <option value="Asia/Ho_Chi_Minh">Asia/Ho_Chi_Minh (UTC+7)</option>
                                <option value="Asia/Manila">Asia/Manila (UTC+8)</option>
                                <option value="UTC">UTC (UTC+0)</option>
                            </select>
                            <div class="form-hint" data-i18n="set-general-tz-hint">用于报表 / 邮件时间戳 / 周报推送时间</div>
                        </div>
                        <div class="form-row form-row-inline">
                            <label data-i18n="set-general-date">日期格式</label>
                            <select id="general-date" class="form-input">
                                <option value="YYYY-MM-DD">2026-05-09</option>
                                <option value="DD/MM/YYYY">09/05/2026</option>
                                <option value="MM/DD/YYYY">05/09/2026</option>
                                <option value="DD-MM-YYYY">09-05-2026</option>
                                <option value="YYYY/MM/DD">2026/05/09</option>
                            </select>
                            <div class="form-hint" data-i18n="set-general-date-hint">显示在历史 / 异常 / 对账 / 导出 CSV</div>
                        </div>
                        <div class="form-row form-row-inline">
                            <label data-i18n="set-general-number">数字格式</label>
                            <select id="general-number" class="form-input">
                                <option value="comma_dot">1,234,567.89</option>
                                <option value="dot_comma">1.234.567,89</option>
                                <option value="space_dot">1 234 567.89</option>
                                <option value="space_comma">1 234 567,89</option>
                            </select>
                            <div class="form-hint" data-i18n="set-general-number-hint">金额千分位 · 小数点</div>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-primary" id="btn-save-general" data-i18n="set-save">保存修改</button>
                            <span class="form-msg" id="general-save-msg"></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- v118.28.8 · Pearnly 访问日志(owner 可见 · 客户审计 Pearnly 内部员工的访问) -->
            <div class="settings-pane" data-pane="access-log">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="set-access-log-title">Pearnly 访问日志</div>
                        <div class="section-sub" data-i18n="set-access-log-sub">Pearnly 内部员工对您账号的所有操作记录(对齐 Xero / QuickBooks Audit log)</div>
                    </div>
                    <div class="access-log-toolbar">
                        <input type="text" class="form-input" id="access-log-search" data-i18n-placeholder="set-access-log-search-ph" style="max-width:320px;">
                        <button class="btn btn-ghost" type="button" id="access-log-csv-btn">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:4px;">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            <span data-i18n="set-access-log-csv">导出 CSV</span>
                        </button>
                    </div>
                    <div class="access-log-table" id="access-log-table"></div>
                    <div class="access-log-pager" id="access-log-pager"></div>
                </div>
            </div>

            <!-- Tab 8 · 联系我们 -->
            <div class="settings-pane" data-pane="about">
                <div class="card">
                    <div class="section-head">
                        <div class="section-title" data-i18n="settings-about">联系我们</div>
                    </div>
                    <div class="about-desc" data-i18n="about-desc">需要帮助、升级账号或反馈问题 · 欢迎联系我们</div>
                    <div class="contact-grid" id="settings-contact-grid"></div>
                </div>
            </div>
        </div>
        <!-- /settings-layout -->
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const fs=`
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9z"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="auto-title">自动化</div>
                <div class="page-head-sub" data-i18n="auto-sub">让 Pearnly 替你完成重复性工作</div>
            </div>
        </div>

        <!-- Free 用户占位 -->
        <div class="card" id="automation-free-block" style="display:none;">
            <div class="coming-soon">
                <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M26 4L10 26h12l-2 18 16-22H24z"/>
                </svg>
                <div class="cs-title" data-i18n="cs-auto-title">全自动处理流水线</div>
                <div class="cs-desc" data-i18n="cs-no-access">该功能暂未开放 · 如有需要请联系我们</div>
            </div>
        </div>

        <!-- Plus/Pro 用户主界面 · 左侧子菜单 + 右侧内容区(v0.10) -->
        <div id="automation-main" style="display:none;">
            <div class="auto-layout">
                <!-- 左侧子菜单 -->
                <aside class="auto-sidebar">
                    <div class="auto-sidebar-inner">
                        <button class="auto-nav-item active" data-auto-tab="erp">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M4 7h16M4 12h16M4 17h10"/>
                                    <path d="M18 17l3 3m0 0l-3 3m3-3h-5"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-erp-title">ERP 对接</span>
                            <span class="auto-nav-badge" id="auto-nav-erp-badge"></span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="bank">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M3 10l9-6 9 6"/>
                                    <path d="M5 10v9M12 10v9M19 10v9"/>
                                    <path d="M3 20h18"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-bank-title">银行对账</span>
                            <span class="auto-nav-badge" id="auto-nav-bank-badge"></span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="email">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="3" y="5" width="18" height="14" rx="2"/>
                                    <path d="M3 7l9 6 9-6"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-email-title">邮箱抓取</span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="folder">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M3 7a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-folder-title">文件夹监听</span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="linebot">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 3C6.5 3 2 6.6 2 11c0 2.5 1.5 4.8 3.9 6.3-.2.8-.7 2.5-.8 2.9 0 0-.1.2.1.3s.3 0 .3 0c.3 0 3.2-2.1 3.8-2.5.9.1 1.8.2 2.7.2 5.5 0 10-3.6 10-8S17.5 3 12 3z"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-linebot-title">LINE Bot</span>
                            <span class="auto-nav-badge" id="auto-nav-linebot-badge"></span>
                        </button>

                        <button class="auto-nav-item" data-auto-tab="alert" data-auto-soon="1">
                            <span class="auto-nav-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                                    <path d="M10 21a2 2 0 0 0 4 0"/>
                                </svg>
                            </span>
                            <span class="auto-nav-label" data-i18n="auto-alert-title">智能提醒</span>
                        </button>
                    </div>
                </aside>

                <!-- 右侧内容区 -->
                <main class="auto-content">

                    <!-- Tab: ERP 对接 -->
                    <div class="auto-panel active" data-auto-panel="erp">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-erp-title">ERP 对接</div>
                                <div class="auto-panel-desc" data-i18n="auto-erp-desc">把识别结果自动推送到你的 ERP / 会计系统</div>
                            </div>
                            <span id="erp-status-summary" class="auto-status-pill" data-i18n="auto-status-loading">加载中…</span>
                        </div>

                        <!-- v118.34.4 (Zihao 2026-05-19 拍板) · ERP 三级 tab 拆分:
                             连接 / 推送日志 / 字段映射。
                             之前:连接 + 推送日志 挤在同一 subpanel · filter chips
                             和日志 row 被压缩看不清。现在:推送日志独占 subpanel·
                             全宽全屏 · 没有侧栏挤压。
                             ⚠ data-erp-subpanel="connect" 的 panel 同时也是
                             "auto-erp-subtab-connect" data-i18n key 的归宿,旧
                             分类不动 · 仅拆出新的 "logs" tab。
                        -->
                        <!-- v118.34.19 (A4) · 「推送日志」subtab 已移到集成主页面顶部 tab · 这里仅留 连接 / 字段映射 -->
                        <div class="erp-subtabs" role="tablist">
                            <button class="erp-subtab active" type="button" data-erp-subtab="connect" data-i18n="auto-erp-subtab-connect-only">连接</button>
                            <button class="erp-subtab" type="button" data-erp-subtab="mappings" data-i18n="auto-erp-subtab-mappings">字段映射</button>
                        </div>

                        <!-- 子面板 1:连接(纯卡片 · 不含日志、不含 today-stats · v118.34.5) -->
                        <div class="erp-subpanel active" data-erp-subpanel="connect">
                            <!-- P1b · 全局「ERP 自动处理方式」(账户级 · 对所有 ERP 端点统一生效 ·
                                 不是单个端点的设置 · 故放在卡片上方而非某张卡片内)。 -->
                            <div class="erp-global-mode" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 16px;padding:12px 14px;background:#fff;border:1px solid #e8e8e3;border-radius:8px;">
                                <span data-i18n="pref-erp-mode-title" style="font-weight:600;font-size:13px;">ERP 自动处理方式</span>
                                <select id="erp-global-push-mode" class="folder-interval-select">
                                    <option value="smart" data-i18n="pref-erp-mode-smart">智能分拣(推荐)</option>
                                    <option value="fixed" data-i18n="pref-erp-mode-fixed">固定当前账套</option>
                                    <option value="ocr_only" data-i18n="pref-erp-mode-ocr">只识别不推送</option>
                                </select>
                                <span data-i18n="pref-erp-mode-desc" style="font-size:12px;color:#6B7280;flex:1 1 200px;">上传识别后,系统如何把发票推送到 ERP</span>
                            </div>
                            <!-- v118.27.4 · ERP 系统连接卡片区(Xero · MR.ERP) -->
                            <div class="erp-connect-cards" id="erp-connect-cards">
                                <!-- IIFE 渲染 Xero 卡片 + MR.ERP 卡片 -->
                            </div>

                            <div id="erp-endpoints-list"></div>
                            <button class="btn btn-primary btn-add-endpoint" id="btn-add-endpoint">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3v10M3 8h10"/></svg>
                                <span data-i18n="auto-erp-add">新增端点</span>
                            </button>

                            <!-- v118.34.35 · 看推送日志按钮放到底部 · 将来加新 ERP 卡片时按钮自然在最下 -->
                            <div class="erp-connect-logs-link" style="text-align:left;margin:16px 0 0;">
                                <button type="button" class="int-btn-view-logs" data-int-action="view-logs" data-i18n="int-btn-view-logs">看推送日志 →</button>
                            </div>
                        </div>

                        <!-- v118.34.19 (A4) · subpanel="logs" 已删除 · 内容搬到
                             集成主页面顶部 tab 2(全宽全屏)· erp-logs-section /
                             erp-today-stats 等 DOM 节点搬过去后这里清空 ·
                             home.js 的 loadErpLogs() 等通过 id 仍然找得到 ·
                             不需要改. -->

                        <!-- 子面板 2:字段映射(老板可写 / 员工只读 · IIFE 渲染) -->
                        <div class="erp-subpanel" data-erp-subpanel="mappings">
                            <div class="erp-map-sub-desc" data-i18n="erp-map-sub">把 Pearnly 的客户 / 科目 / 税码 翻译成你 ERP 系统的代码 · 后续推送 ERP 时会自动用这里的映射</div>
                            <div class="erp-map-subtabs" id="erp-map-subtabs" role="tablist">
                                <button class="erp-map-subtab active" type="button" data-erp-subtab="clients" data-i18n="erp-map-subtab-clients">客户映射</button>
                                <button class="erp-map-subtab erp-map-subtab-advanced" type="button" data-erp-subtab="accounts" data-i18n="erp-map-subtab-accounts">科目映射</button>
                                <button class="erp-map-subtab erp-map-subtab-advanced" type="button" data-erp-subtab="taxes" data-i18n="erp-map-subtab-taxes">税码映射</button>
                                <button class="erp-map-subtab erp-map-subtab-advanced" type="button" data-erp-subtab="products" data-i18n="erp-map-subtab-products">商品映射</button>
                                <button class="erp-map-show-advanced-btn" type="button" id="erp-map-show-advanced-btn" aria-pressed="false">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                        <line class="erp-map-adv-plus-h" x1="5" y1="10" x2="15" y2="10"/>
                                        <line class="erp-map-adv-plus-v" x1="10" y1="5" x2="10" y2="15"/>
                                    </svg>
                                    <span class="erp-map-adv-btn-label" data-i18n="erp-map-show-advanced">显示高级映射</span>
                                </button>
                            </div>
                            <div class="erp-map-pane-wrap" id="erp-map-pane-wrap"></div>
                        </div>
                    </div>

                    <!-- Tab: 银行对账 (v0.18 · M10) -->
                    <div class="auto-panel" data-auto-panel="bank">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-bank-title">银行对账</div>
                                <div class="auto-panel-desc" data-i18n="bank-panel-desc">上传银行对账单 PDF · 自动和 Pearnly 里的发票做智能匹配 · 3 小时的月末对账压缩到 15 分钟</div>
                            </div>
                            <span id="bank-status-summary" class="auto-status-pill" data-i18n="auto-status-loading">加载中…</span>
                        </div>

                        <!-- 上传区(v118.26.1 · 批量上传) -->
                        <div class="bank-upload-card">
                            <div class="bank-upload-row">
                                <div class="bank-upload-icon">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 3v12M6 9l6-6 6 6"/>
                                        <path d="M5 21h14"/>
                                    </svg>
                                </div>
                                <div class="bank-upload-text">
                                    <div class="bank-upload-title" data-i18n="bank-upload-title">上传银行对账单</div>
                                    <div class="bank-upload-sub" data-i18n="bank-upload-sub-batch">支持多选 · KBank · SCB · BBL · 其他银行也能解析大部分流水</div>
                                </div>
                                <label for="bank-file-input" class="btn btn-primary bank-upload-btn">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3v10M3 8h10"/></svg>
                                    <span data-i18n="bank-btn-upload-batch">选择文件(可多选)</span>
                                </label>
                                <input type="file" id="bank-file-input" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.tif,.xlsx,.xls,.xlsm,.csv,.tsv,.docx,.doc" multiple style="display:none">
                            </div>
                            <!-- 单文件遗留 progress / error · 仅在仅传 1 张时降级显示 · 多文件走下方队列 -->
                            <div id="bank-upload-progress" class="bank-upload-progress" style="display:none">
                                <div class="bank-upload-spinner"></div>
                                <span data-i18n="bank-upload-parsing">正在解析对账单…</span>
                            </div>
                            <div id="bank-upload-error" class="bank-upload-error" style="display:none"></div>
                            <!-- v118.26.1 · 批量上传队列(每文件 1 行 · 进度 + 状态 + 重试) -->
                            <div id="bank-upload-queue" class="bank-upload-queue" style="display:none">
                                <div class="bank-upload-queue-head">
                                    <span class="bank-upload-queue-title" data-i18n="bank-queue-title">上传队列</span>
                                    <span class="bank-upload-queue-summary" id="bank-upload-queue-summary"></span>
                                    <button class="btn btn-ghost btn-tiny" id="btn-bank-queue-clear-done" type="button">
                                        <span data-i18n="bank-queue-clear-done">清除已完成</span>
                                    </button>
                                </div>
                                <div id="bank-upload-queue-list" class="bank-upload-queue-list"></div>
                            </div>
                        </div>

                        <!-- 会话列表(最近上传的对账单)-->
                        <div class="bank-sessions-section">
                            <div class="bank-section-head">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M2 4h12M2 8h12M2 12h8"/>
                                </svg>
                                <span data-i18n="bank-sessions-title">最近对账</span>
                                <!-- v118.26.1.1 · 筛选 chip -->
                                <div class="bank-sessions-filters">
                                    <button class="bank-sessions-chip active" data-sess-filter="all" data-i18n="bank-sess-filter-all">全部</button>
                                    <button class="bank-sessions-chip" data-sess-filter="parsed" data-i18n="bank-sess-filter-parsed">已解析</button>
                                    <button class="bank-sessions-chip" data-sess-filter="failed" data-i18n="bank-sess-filter-failed">失败</button>
                                </div>
                            </div>
                            <div id="bank-sessions-list" class="bank-sessions-list">
                                <div class="bank-empty" data-i18n="bank-sessions-loading">加载中…</div>
                            </div>
                        </div>

                        <!-- 会话详情(选中一个会话后出现)-->
                        <div id="bank-detail" class="bank-detail" style="display:none">
                            <div class="bank-detail-head">
                                <button class="btn btn-ghost btn-small" id="btn-bank-back">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 12L6 8l4-4"/></svg>
                                    <span data-i18n="bank-btn-back">返回列表</span>
                                </button>
                                <div class="bank-detail-title" id="bank-detail-title"></div>
                                <!-- v118.26.2 · 客户徽章 · 显示 session 当前所属客户(老板可改 · 员工只读) -->
                                <button class="bank-client-badge" id="bank-client-badge" type="button" style="display:none">
                                    <span class="bank-client-badge-dot" id="bank-client-badge-dot"></span>
                                    <span class="bank-client-badge-name" id="bank-client-badge-name">-</span>
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" id="bank-client-badge-caret"><path d="M4 6l4 4 4-4"/></svg>
                                </button>
                                <button class="btn btn-ghost btn-small bank-btn-danger" id="btn-bank-delete" title="">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg>
                                </button>
                            </div>

                            <!-- 会话元信息卡 -->
                            <div class="bank-detail-meta">
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-period">对账周期</div>
                                    <div class="bank-meta-value" id="bank-meta-period">-</div>
                                </div>
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-opening">期初余额</div>
                                    <div class="bank-meta-value tabular-nums" id="bank-meta-opening">-</div>
                                </div>
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-inflow">入账</div>
                                    <div class="bank-meta-value tabular-nums bank-in" id="bank-meta-inflow">-</div>
                                </div>
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-outflow">出账</div>
                                    <div class="bank-meta-value tabular-nums bank-out" id="bank-meta-outflow">-</div>
                                </div>
                                <div class="bank-meta-item">
                                    <div class="bank-meta-label" data-i18n="bank-meta-closing">期末余额</div>
                                    <div class="bank-meta-value tabular-nums" id="bank-meta-closing">-</div>
                                </div>
                            </div>

                            <!-- 匹配统计 + 触发按钮 -->
                            <div class="bank-match-bar">
                                <div class="bank-match-stats" id="bank-match-stats">
                                    <span class="bank-stat-chip" data-kind="total">
                                        <span id="bank-stat-total">0</span> <span data-i18n="bank-stat-total">流水</span>
                                    </span>
                                    <span class="bank-stat-chip bank-stat-matched" data-kind="matched">
                                        <span id="bank-stat-matched">0</span> <span data-i18n="bank-stat-matched">已匹配</span>
                                    </span>
                                    <span class="bank-stat-chip bank-stat-suggested" data-kind="suggested">
                                        <span id="bank-stat-suggested">0</span> <span data-i18n="bank-stat-suggested">疑似</span>
                                    </span>
                                    <span class="bank-stat-chip bank-stat-unmatched" data-kind="unmatched">
                                        <span id="bank-stat-unmatched">0</span> <span data-i18n="bank-stat-unmatched">未匹配</span>
                                    </span>
                                </div>
                                <button class="btn btn-primary btn-small" id="btn-bank-run-match">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8a6 6 0 0111-3.5M14 8a6 6 0 01-11 3.5M14 3v3h-3M2 13v-3h3"/></svg>
                                    <span data-i18n="bank-btn-run-match">开始匹配</span>
                                </button>
                            </div>

                            <!-- 流水筛选 -->
                            <div class="bank-filter-bar">
                                <button class="btn btn-sm btn-secondary bank-filter-btn active" data-bank-filter="all" data-i18n="bank-filter-all">全部</button>
                                <button class="btn btn-sm btn-secondary bank-filter-btn" data-bank-filter="matched" data-i18n="bank-filter-matched">已匹配</button>
                                <button class="btn btn-sm btn-secondary bank-filter-btn" data-bank-filter="suggested" data-i18n="bank-filter-suggested">疑似</button>
                                <button class="btn btn-sm btn-secondary bank-filter-btn" data-bank-filter="unmatched" data-i18n="bank-filter-unmatched">未匹配</button>
                            </div>

                            <!-- v118.26.2 · 右半屏对账面板 · 流水表 + 候选发票并排 -->
                            <div class="bank-detail-body" id="bank-detail-body">
                                <!-- 左:流水表 -->
                                <div class="bank-recon-left">
                                    <div class="bank-tx-table-wrap">
                                        <table class="bank-tx-table">
                                            <thead>
                                                <tr>
                                                    <th data-i18n="bank-col-date">日期</th>
                                                    <th data-i18n="bank-col-desc">摘要</th>
                                                    <th class="bank-col-amt" data-i18n="bank-col-amount">金额</th>
                                                    <th data-i18n="bank-col-match">匹配状态</th>
                                                </tr>
                                            </thead>
                                            <tbody id="bank-tx-tbody">
                                                <tr><td colspan="4" class="bank-empty" data-i18n="bank-tx-loading">加载流水…</td></tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                <!-- 右:候选 pane(默认空态 · 选中流水后渲染) -->
                                <aside class="bank-recon-right" id="bank-recon-right">
                                    <div class="bank-cand-pane" id="bank-cand-pane">
                                        <div class="bank-cand-pane-head">
                                            <div>
                                                <div class="bank-cand-pane-title" id="bank-cand-pane-title" data-i18n="bank-cand-pane-empty-title">点左侧任意一笔流水查看候选发票</div>
                                                <div class="bank-cand-pane-sub" id="bank-cand-pane-sub" data-i18n="bank-cand-pane-empty-sub">系统按金额 / 日期 / 商户名打分推荐</div>
                                            </div>
                                            <button class="modal-close" id="btn-bank-cand-pane-close" aria-label="close" style="display:none">
                                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
                                            </button>
                                        </div>
                                        <div class="bank-cand-pane-body" id="bank-cand-pane-body">
                                            <div class="bank-cand-pane-empty">
                                                <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
                                                    <rect x="14" y="10" width="36" height="44" rx="3"/>
                                                    <path d="M22 22h20M22 30h20M22 38h12"/>
                                                </svg>
                                                <div data-i18n="bank-cand-pane-empty-hint">在左边选一笔流水 · 系统会列出最有可能的发票</div>
                                            </div>
                                        </div>
                                        <div class="bank-cand-pane-foot" id="bank-cand-pane-foot" style="display:none">
                                            <button class="btn btn-ghost btn-small" id="btn-bank-cand-ignore-pane">
                                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10"/></svg>
                                                <span data-i18n="bank-cand-ignore">忽略此条流水</span>
                                            </button>
                                        </div>
                                    </div>
                                </aside>
                            </div>
                        </div>
                    </div>

`,ms=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
                    <div class="auto-panel" data-auto-panel="email">
                        <!-- v93 · 已迁 Vultr · 启用完整 UI -->
                        <div id="email-full-ui">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-email-title">邮箱抓取</div>
                                <div class="auto-panel-desc" data-i18n="email-panel-desc">绑定邮箱后 · Pearnly 自动扫收件箱 · PDF 发票附件自动识别入库</div>
                            </div>
                            <span id="email-status-summary" class="auto-status-pill" data-i18n="auto-status-loading">加载中…</span>
                        </div>

                        <!-- 未绑定 · 引导卡片 -->
                        <div id="email-empty" class="email-empty-card" style="display:none;">
                            <div class="email-empty-icon">
                                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="6" y="12" width="36" height="28" rx="3"/>
                                    <path d="M6 15l18 12 18-12"/>
                                </svg>
                            </div>
                            <div class="email-empty-title" data-i18n="email-empty-title">还没绑定邮箱</div>
                            <div class="email-empty-desc" data-i18n="email-empty-desc">绑定后 · Pearnly 会自动扫未读邮件 · 自动识别 PDF 发票附件</div>
                            <button class="btn btn-primary" id="btn-email-bind">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3v10M3 8h10"/></svg>
                                <span data-i18n="email-bind-btn">绑定邮箱</span>
                            </button>
                        </div>

                        <!-- 已绑定 · 账号卡片 -->
                        <div id="email-account-card" class="email-account-card" style="display:none;">
                            <div class="email-account-head">
                                <div class="email-account-icon">
                                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <rect x="2.5" y="5" width="15" height="11" rx="1.5"/>
                                        <path d="M2.5 6.5l7.5 5 7.5-5"/>
                                    </svg>
                                </div>
                                <div class="email-account-info">
                                    <div class="email-account-addr" id="email-account-addr">-</div>
                                    <div class="email-account-meta">
                                        <span id="email-account-host">-</span>
                                        <span class="email-meta-sep">·</span>
                                        <span id="email-account-last" data-i18n="email-last-never">从未抓取</span>
                                    </div>
                                </div>
                                <label class="toggle-switch" title="" id="email-enabled-wrap">
                                    <input type="checkbox" id="email-enabled-toggle">
                                    <span class="toggle-slider"></span>
                                </label>
                            </div>

                            <!-- 上次错误(若有)-->
                            <div id="email-last-error" class="email-last-error" style="display:none;"></div>

                            <div class="email-account-actions">
                                <button class="btn btn-primary btn-small" id="btn-email-trigger">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8a5 5 0 119 3M12 13V9h-4"/></svg>
                                    <span data-i18n="email-btn-trigger">立即抓取</span>
                                </button>
                                <button class="btn btn-ghost btn-small" id="btn-email-edit">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 3l2 2-7 7H4v-2l7-7zM10 4l2 2"/></svg>
                                    <span data-i18n="email-btn-edit">修改配置</span>
                                </button>
                                <div style="flex:1"></div>
                                <button class="btn btn-ghost btn-small email-btn-danger" id="btn-email-unbind">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg>
                                    <span data-i18n="email-btn-unbind">解绑邮箱</span>
                                </button>
                            </div>
                        </div>

                        <!-- 抓取日志折叠区 -->
                        <details class="erp-logs-section" id="email-logs-section" style="display:none;">
                            <summary class="erp-logs-head">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 1"/>
                                </svg>
                                <span data-i18n="email-logs-title">抓取日志</span>
                                <span class="erp-logs-today-stats" id="email-logs-hint"></span>
                            </summary>
                            <div class="erp-logs-toolbar">
                                <div></div>
                                <button class="btn btn-ghost btn-tiny" id="btn-email-refresh-logs" title="">
                                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                                </button>
                            </div>
                            <div id="email-logs-list" class="erp-logs-list">
                                <div class="erp-logs-empty" data-i18n="erp-logs-loading">加载中…</div>
                            </div>
                        </details>
                        </div><!-- /#email-full-ui -->
                    </div>

                    <!-- Tab: 文件夹监听 (v95 · 浏览器 File System Access API · 0 费用网页端方案) -->
                    <div class="auto-panel" data-auto-panel="folder">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-folder-title">文件夹监听</div>
                                <div class="auto-panel-desc" data-i18n="folder-panel-desc">选一个本地文件夹 · Pearnly 自动扫描里面的 PDF 发票</div>
                            </div>
                            <span id="folder-status-summary" class="auto-status-pill" data-i18n="folder-status-init">初始化中…</span>
                        </div>

                        <!-- 浏览器不支持(Firefox / Safari) -->
                        <div id="folder-unsupported" class="folder-card folder-unsupported" style="display:none;">
                            <div class="folder-unsupported-icon">
                                <svg width="64" height="64" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="24" cy="24" r="20"/>
                                    <path d="M24 16v10M24 32h.01"/>
                                </svg>
                            </div>
                            <div class="folder-unsupported-title" data-i18n="folder-unsupported-title">你的浏览器不支持本功能</div>
                            <div class="folder-unsupported-desc" data-i18n="folder-unsupported-desc">文件夹监听需要 Chrome 或 Edge 浏览器(Firefox / Safari 暂不支持)</div>
                            <div class="folder-alt-section">
                                <div class="folder-alt-title" data-i18n="folder-alt-title">替代方案</div>
                                <button class="btn btn-ghost folder-alt-btn" data-tab-jump="email">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="m2 4 6 4 6-4"/></svg>
                                    <span data-i18n="folder-alt-email">改用邮件抓取(任何浏览器)</span>
                                </button>
                                <button class="btn btn-ghost folder-alt-btn" data-tab-jump="upload">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12V3M5 6l3-3 3 3"/><path d="M3 13h10"/></svg>
                                    <span data-i18n="folder-alt-upload">改用拖拽上传</span>
                                </button>
                            </div>
                        </div>

                        <!-- 还没选文件夹(支持的浏览器 · 未配置态) -->
                        <div id="folder-empty" class="folder-card folder-empty" style="display:none;">
                            <div class="folder-empty-icon">
                                <svg width="64" height="64" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M6 14a4 4 0 0 1 4-4h10l4 6h14a4 4 0 0 1 4 4v16a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4V14z"/>
                                </svg>
                            </div>
                            <div class="folder-empty-title" data-i18n="folder-empty-title">还没选监听文件夹</div>
                            <div class="folder-empty-desc" data-i18n="folder-empty-desc">选一个本地文件夹后 · Pearnly 会扫描里面的 PDF / 图片发票 · 自动识别入库</div>
                            <button class="btn btn-primary" id="btn-folder-pick">
                                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 3v10M3 8h10"/></svg>
                                <span data-i18n="folder-pick-btn">选择监听文件夹</span>
                            </button>
                            <div class="folder-info-bar">
                                <span class="folder-info-chip" tabindex="0">
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 5v3.5M8 11h.01"/></svg>
                                    <span data-i18n="folder-info-keep-open-short">需保持页面打开</span>
                                    <span class="folder-info-tooltip" data-i18n="folder-warn-keep-open">本功能需要保持本页面打开 · 浏览器关闭 / 电脑睡眠后停止扫描 · 重新打开会自动继续</span>
                                </span>
                                <button type="button" class="folder-info-chip folder-info-chip-link" data-tab-jump="email">
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="m2 4 6 4 6-4"/></svg>
                                    <span data-i18n="folder-info-email-short">需 7×24 用邮件抓取</span>
                                    <span class="folder-info-tooltip" data-i18n="folder-need-247-tip">需要 7×24 后台运行?推荐改用「邮件抓取」· 把发票转发到绑定邮箱即可 · 任何浏览器都不需要打开</span>
                                </button>
                            </div>
                        </div>

                        <!-- 已配置(主面板) -->
                        <div id="folder-active" class="folder-active" style="display:none;">
                            <!-- 配置卡片 -->
                            <div class="folder-card folder-config-card">
                                <div class="folder-config-head">
                                    <div class="folder-config-info">
                                        <div class="folder-config-icon">
                                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/></svg>
                                        </div>
                                        <div>
                                            <div class="folder-config-path" id="folder-config-path">-</div>
                                            <div class="folder-config-meta">
                                                <span id="folder-status-pulse" class="folder-status-pulse"></span>
                                                <span id="folder-status-text" data-i18n="folder-status-running">正在监听</span>
                                                <span> · </span>
                                                <span data-i18n="folder-scan-every">每</span>
                                                <select id="folder-interval-select" class="folder-interval-select">
                                                    <option value="30" data-i18n="folder-interval-30">30 秒</option>
                                                    <option value="60" data-i18n="folder-interval-60" selected>1 分钟</option>
                                                    <option value="300" data-i18n="folder-interval-300">5 分钟</option>
                                                </select>
                                                <span data-i18n="folder-scan-once">扫一次</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="folder-config-actions">
                                        <button class="btn btn-ghost btn-small" id="btn-folder-pause">
                                            <svg viewBox="0 0 16 16" fill="currentColor"><rect x="4" y="3" width="3" height="10"/><rect x="9" y="3" width="3" height="10"/></svg>
                                            <span data-i18n="folder-btn-pause">暂停</span>
                                        </button>
                                        <button class="btn btn-ghost btn-small" id="btn-folder-resume" style="display:none;">
                                            <svg viewBox="0 0 16 16" fill="currentColor"><path d="M4 3l9 5-9 5z"/></svg>
                                            <span data-i18n="folder-btn-resume">恢复</span>
                                        </button>
                                        <button class="btn btn-ghost btn-small" id="btn-folder-scan-now">
                                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8a6 6 0 0 1 6-6 6.5 6.5 0 0 1 4.5 1.83L14 5"/><path d="M14 2v3h-3"/><path d="M14 8a6 6 0 0 1-6 6 6.5 6.5 0 0 1-4.5-1.83L2 11"/><path d="M2 14v-3h3"/></svg>
                                            <span data-i18n="folder-btn-scan-now">立即扫描</span>
                                        </button>
                                        <button class="btn btn-ghost btn-small folder-btn-danger" id="btn-folder-remove">
                                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 5h10M6 5V3h4v2M5 5v8a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1V5"/></svg>
                                            <span data-i18n="folder-btn-remove">移除</span>
                                        </button>
                                    </div>
                                </div>
                                <div class="folder-stats">
                                    <div class="folder-stat">
                                        <div class="folder-stat-label" data-i18n="folder-stat-last-scan">上次扫描</div>
                                        <div class="folder-stat-value" id="folder-stat-last">-</div>
                                    </div>
                                    <div class="folder-stat">
                                        <div class="folder-stat-label" data-i18n="folder-stat-processed">累计处理</div>
                                        <div class="folder-stat-value" id="folder-stat-processed">0</div>
                                    </div>
                                    <div class="folder-stat">
                                        <div class="folder-stat-label" data-i18n="folder-stat-failed">失败</div>
                                        <div class="folder-stat-value" id="folder-stat-failed">0</div>
                                    </div>
                                    <div class="folder-stat">
                                        <div class="folder-stat-label" data-i18n="folder-stat-queue">队列中</div>
                                        <div class="folder-stat-value" id="folder-stat-queue">0</div>
                                    </div>
                                </div>
                                <div class="folder-warn-row" id="folder-keep-open-warn">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 5v3.5M8 11h.01"/></svg>
                                    <span data-i18n="folder-warn-keep-open">本功能需要保持此页面打开 · 关闭后停止扫描</span>
                                </div>
                                <!-- v118.24 · 子文件夹递归提示 -->
                                <div class="folder-warn-row folder-info-soft">
                                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2 5a1.5 1.5 0 0 1 1.5-1.5h3l1.5 2h4.5A1.5 1.5 0 0 1 14 7v5a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 12V5z"/><path d="M5 8.5h6"/></svg>
                                    <span data-i18n="folder-recursive-info">已自动扫子文件夹</span>
                                </div>
                            </div>

                            <!-- 最近处理 -->
                            <div class="folder-card folder-recent-card">
                                <div class="folder-recent-head">
                                    <div class="folder-recent-title" data-i18n="folder-recent-title">最近处理</div>
                                    <button class="btn btn-tiny" id="btn-folder-clear-recent" data-i18n="folder-clear-recent">清空记录</button>
                                </div>
                                <div id="folder-recent-list" class="folder-recent-list">
                                    <div class="folder-recent-empty" data-i18n="folder-recent-empty">还没处理任何文件</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tab: LINE Bot(v0.19 · T1) -->
                    <div class="auto-panel" data-auto-panel="linebot">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-linebot-title">LINE Bot</div>
                                <div class="auto-panel-desc" data-i18n="auto-linebot-desc">把发票拍照发到 LINE · Pearnly 自动识别入账</div>
                            </div>
                            <span id="linebot-status-summary" class="auto-status-pill" data-i18n="auto-status-loading">加载中…</span>
                        </div>

                        <!-- 未绑定态 -->
                        <div id="linebot-unbound" style="display:none;">
                            <div class="card linebot-card">
                                <div class="linebot-steps">
                                    <div class="linebot-step">
                                        <div class="linebot-step-no">1</div>
                                        <div class="linebot-step-body">
                                            <div class="linebot-step-title" data-i18n="linebot-step1-title">加 Bot 为 LINE 好友</div>
                                            <div class="linebot-step-desc" data-i18n="linebot-step1-desc">扫下面 QR 码 · 或在 LINE 搜索 Bot ID</div>
                                            <div class="linebot-qr-wrap">
                                                <div id="linebot-qr" class="linebot-qr-box"></div>
                                                <div class="linebot-bot-id">
                                                    <span data-i18n="linebot-bot-id-label">Bot ID</span>:
                                                    <span id="linebot-bot-id" class="linebot-bot-id-val">—</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="linebot-step">
                                        <div class="linebot-step-no">2</div>
                                        <div class="linebot-step-body">
                                            <div class="linebot-step-title" data-i18n="linebot-step2-title">把这 6 位数字发给 Bot</div>
                                            <div class="linebot-step-desc" data-i18n="linebot-step2-desc">10 分钟内有效 · 发送后自动绑定</div>
                                            <div class="linebot-code-wrap">
                                                <div id="linebot-code" class="linebot-code">——————</div>
                                                <button id="linebot-code-refresh" class="btn btn-ghost btn-tiny">
                                                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M11.5 7a4.5 4.5 0 11-1.3-3.2M12 2v3h-3"/></svg>
                                                    <span data-i18n="linebot-code-refresh">换一个</span>
                                                </button>
                                            </div>
                                            <div id="linebot-code-expires" class="linebot-code-expires"></div>
                                        </div>
                                    </div>

                                    <div class="linebot-step">
                                        <div class="linebot-step-no">3</div>
                                        <div class="linebot-step-body">
                                            <div class="linebot-step-title" data-i18n="linebot-step3-title">等待绑定完成</div>
                                            <div class="linebot-step-desc" data-i18n="linebot-step3-desc">发送成功后 · 这里会自动变为「已绑定」</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 已绑定态 -->
                        <div id="linebot-bound" style="display:none;">
                            <div class="card linebot-bound-card">
                                <div class="linebot-bound-head">
                                    <img id="linebot-avatar" class="linebot-avatar" src="" alt="" onerror="this.style.display='none'">
                                    <div class="linebot-bound-info">
                                        <div class="linebot-bound-name" id="linebot-bound-name">—</div>
                                        <div class="linebot-bound-sub">
                                            <span data-i18n="linebot-bound-since">已绑定</span>
                                            <span id="linebot-bound-since">—</span>
                                        </div>
                                    </div>
                                    <div class="linebot-bound-badge">
                                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8l4 4 8-8"/></svg>
                                        <span data-i18n="linebot-bound-tag">已绑定</span>
                                    </div>
                                </div>
                                <div class="linebot-bound-tips">
                                    <div class="linebot-tip-title" data-i18n="linebot-tip-title">你现在可以这样用 👇</div>
                                    <ul class="linebot-tip-list">
                                        <li data-i18n="linebot-tip-1">在 LINE 里把发票照片发给 Bot · 自动识别(功能即将上线)</li>
                                        <li data-i18n="linebot-tip-2">多张发票可一次性发出 · Bot 逐张处理</li>
                                        <li data-i18n="linebot-tip-3">识别完成后 · Bot 自动回复结果</li>
                                    </ul>
                                </div>
                                <div class="linebot-bound-actions">
                                    <button id="linebot-unbind" class="btn btn-ghost">
                                        <span data-i18n="linebot-unbind">解绑 LINE</span>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- 错误态 -->
                        <div id="linebot-error" class="linebot-error" style="display:none;"></div>
                    </div>

                    <!-- Tab: 智能提醒 v118.22.2 · 完整面板 -->
                    <div class="auto-panel" data-auto-panel="alert">
                        <div class="auto-panel-head">
                            <div>
                                <div class="auto-panel-title" data-i18n="auto-alert-title">智能提醒</div>
                                <div class="auto-panel-desc" data-i18n="auto-alert-desc">异常 high 或大额发票发生时 · 自动推送到老板/会计的 LINE</div>
                            </div>
                            <button class="btn btn-primary" id="notif-btn-new">
                                <span data-i18n="notif-btn-new">+ 新建规则</span>
                            </button>
                        </div>

                        <!-- 规则列表 -->
                        <div class="card notif-card">
                            <div class="auto-card-head">
                                <div class="auto-card-title" data-i18n="notif-rules-title">我的规则</div>
                                <span id="notif-rules-count" class="auto-status-pill none">0</span>
                            </div>
                            <div id="notif-rules-empty" class="empty-state" style="display:none;">
                                <div class="empty-icon">
                                    <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 16a12 12 0 0 1 24 0c0 14 6 18 6 18H6s6-4 6-18"/>
                                        <path d="M20 42a4 4 0 0 0 8 0"/>
                                    </svg>
                                </div>
                                <div class="empty-title" data-i18n="notif-empty-title">还没有任何提醒规则</div>
                                <div class="empty-desc" data-i18n="notif-empty-desc">点右上角「新建规则」· 选个模板就行 · 老板会立刻在 LINE 收到</div>
                            </div>
                            <div id="notif-rules-list" class="notif-rules-list"></div>
                        </div>

                        <!-- 最近发送 -->
                        <div class="card notif-card">
                            <div class="auto-card-head">
                                <div class="auto-card-title" data-i18n="notif-logs-title">最近推送</div>
                                <button class="btn btn-tiny btn-ghost" id="notif-btn-refresh-logs">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;">
                                        <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>
                                    </svg>
                                    <span data-i18n="notif-btn-refresh">刷新</span>
                                </button>
                            </div>
                            <div id="notif-logs-list" class="notif-logs-list">
                                <div class="notif-logs-empty" data-i18n="notif-logs-empty">还没推送过任何消息</div>
                            </div>
                        </div>
                    </div>

                </main>
            </div>
        </div>
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=fs+ms,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
        <div class="coming-soon">
            <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 14V8M30 14V8M14 40h20"/>
                <rect x="12" y="14" width="24" height="26" rx="2"/>
            </svg>
            <div class="cs-title" data-i18n="cs-int-title">ERP 无缝对接</div>
            <div class="cs-desc" data-i18n="cs-int-desc">把识别结果自动推送到你的 Mr.ERP,告别手动复制粘贴</div>
            <div class="cs-coming" data-i18n="cs-coming-soon">即将上线</div>
        </div>
`,"page-templates":`
        <div class="coming-soon">
            <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="8" y="10" width="32" height="28" rx="2"/>
                <path d="M8 20h32M18 10v28"/>
            </svg>
            <div class="cs-title" data-i18n="cs-tpl-title">自定义 Excel 模板</div>
            <div class="cs-desc" data-i18n="cs-tpl-desc">根据不同客户的 ERP 定制导出列结构</div>
            <div class="cs-coming" data-i18n="cs-coming-soon">即将上线</div>
        </div>
`,"page-api-keys":`
        <div class="coming-soon">
            <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 26l14-14M10 26l-3 12 12-3M24 12l10 10M34 22l7-7a2 2 0 000-3l-3-3a2 2 0 00-3 0l-7 7"/>
            </svg>
            <div class="cs-title" data-i18n="cs-api-title">自动化对接</div>
            <div class="cs-desc" data-i18n="cs-api-desc">未来可通过此功能对接 UiPath、n8n 等自动化工具 · 让识别流程融入您的工作流</div>
            <div class="cs-coming" data-i18n="cs-coming-soon">即将上线</div>
        </div>
`,"page-vouchers":`
        <div class="auto-coming-hero">
            <div class="coming-big-icon">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10 6h18l12 12v22a2 2 0 01-2 2H10a2 2 0 01-2-2V8a2 2 0 012-2z"/>
                    <path d="M28 6v12h12"/>
                    <path d="M15 28l5 5 10-10"/>
                </svg>
            </div>
            <div class="coming-big-title" data-i18n="cs-vouchers-title">凭证中心</div>
            <div class="coming-big-desc" data-i18n="cs-vouchers-desc">识别后自动生成会计凭证 · 借贷科目 AI 推荐 · 审核后一键推 ERP</div>
            <ul class="coming-features">
                <li data-i18n="cs-vouchers-f1">凭证自动生成 · AI 推荐借贷科目和金额分录</li>
                <li data-i18n="cs-vouchers-f2">批量审核 + 单笔修改 · 审计追溯完整 · 所有改动留痕</li>
                <li data-i18n="cs-vouchers-f3">支持中式凭证(借 / 贷)与泰式凭证(ใบสำคัญ)双格式</li>
            </ul>
            <div class="coming-eta" data-i18n="cs-vouchers-eta">预计 v104 上线</div>
        </div>
`,"page-sales-invoices":`
        <div class="auto-coming-hero">
            <div class="coming-big-icon">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 6h18l6 6v30H12z"/>
                    <path d="M30 6v6h6"/>
                    <line x1="18" y1="20" x2="32" y2="20"/>
                    <line x1="18" y1="26" x2="32" y2="26"/>
                    <line x1="18" y1="32" x2="26" y2="32"/>
                </svg>
            </div>
            <div class="coming-big-title" data-i18n="cs-sales-invoices-title">销售发票</div>
            <div class="coming-big-desc" data-i18n="cs-sales-invoices-desc">给客户开发票一键生成 · 进项识别 + 销项开票一站搞定 · ภ.พ.30 报税进销一并汇总</div>
            <ul class="coming-features">
                <li data-i18n="cs-sales-invoices-f1">选客户(已存档)+ 商品行项目 + 自动算 7% VAT · 1 分钟开一张</li>
                <li data-i18n="cs-sales-invoices-f2">生成正规 ใบกำกับภาษี / ใบเสร็จ PDF · 一键发邮件 / LINE 给客户</li>
                <li data-i18n="cs-sales-invoices-f3">销项数据自动汇入 ภ.พ.30 · 不再手抄进销税额对账</li>
            </ul>
            <div class="coming-eta" data-i18n="cs-sales-invoices-eta">预计 v110.1 上线</div>
        </div>
`,"page-receivables":`
        <div class="auto-coming-hero">
            <div class="coming-big-icon">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M24 6v36"/>
                    <path d="M34 14h-13a6 6 0 000 12h5a6 6 0 010 12h-13"/>
                </svg>
            </div>
            <div class="coming-big-title" data-i18n="cs-receivables-title">应收追踪</div>
            <div class="coming-big-desc" data-i18n="cs-receivables-desc">应收未收款一目了然 · 账龄自动分组 · 到期自动提醒客户付款 · DSO 指标实时更新</div>
            <ul class="coming-features">
                <li data-i18n="cs-receivables-f1">账龄分析(30 / 60 / 90 / 90+ 天)· 逾期自动红标</li>
                <li data-i18n="cs-receivables-f2">LINE / 邮件自动催收 · 多模板预设 · 一键群发不失礼</li>
                <li data-i18n="cs-receivables-f3">银行流水回款自动核销 · 不用手动对账 · 收款秒到账</li>
            </ul>
            <div class="coming-eta" data-i18n="cs-receivables-eta">预计 v107 上线</div>
        </div>
`,"page-cloud":`
        <div class="auto-coming-hero">
            <div class="coming-big-icon">
                <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M36 22h-2a12 12 0 10-20 10h22a6 6 0 000-12z"/>
                    <path d="M24 20v10M20 26l4 4 4-4"/>
                </svg>
            </div>
            <div class="coming-big-title" data-i18n="cs-cloud-title">云盘同步</div>
            <div class="coming-big-desc" data-i18n="cs-cloud-desc">Google Drive / OneDrive 指定文件夹监听 · 跨设备远程入账 · 不依赖本地浏览器</div>
            <ul class="coming-features">
                <li data-i18n="cs-cloud-f1">手机拍照 → Drive app 上传 → Pearnly 自动识别推 ERP</li>
                <li data-i18n="cs-cloud-f2">服务器侧轮询 · 浏览器关了照样跑 · 真 24/7 不间断</li>
                <li data-i18n="cs-cloud-f3">多设备协作 · 出纳外勤扫描 + 会计坐班复核分工</li>
            </ul>
            <div class="coming-eta" data-i18n="cs-cloud-eta">预计 v108 上线</div>
        </div>
`},n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;Object.keys(e).forEach(o=>{const s=document.getElementById(o);!s||s.dataset.wbInjected==="1"||(s.innerHTML=e[o],s.dataset.wbInjected="1",a&&a[n]&&s.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");a[n][r]&&(i.textContent=a[n][r])}))})})();(function(){const e=document.getElementById("page-dashboard");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 12l9-9 9 9"/><path d="M5 10v10h14V10"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="dash-title">首页</div>
                <div class="page-head-sub" id="dash-subtitle" data-i18n="dash-sub">今日工作概况</div>
            </div>
        </div>
        <div class="dash-kpi-grid">
            <div class="dash-kpi">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 2h7l3 3v9H3z"/><path d="M10 2v3h3"/></svg><span data-i18n="dash-kpi-month-invoices">本月发票</span></div>
                <div class="dash-kpi-val" id="dash-kpi-invoices">—</div>
                <div class="dash-kpi-sub" data-i18n="dash-kpi-month-invoices-sub">张已识别</div>
            </div>
            <div class="dash-kpi">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="8" cy="8" r="6"/><path d="M8 4v4l2.5 2.5"/></svg><span data-i18n="dash-kpi-pending">待处理</span></div>
                <div class="dash-kpi-val dash-amber" id="dash-kpi-pending">—</div>
                <div class="dash-kpi-sub" data-i18n="dash-kpi-pending-sub">条待审核</div>
            </div>
            <div class="dash-kpi">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 1l7 13H1z"/><path d="M8 6v4"/><circle cx="8" cy="12" r="0.6" fill="currentColor"/></svg><span data-i18n="dash-kpi-exceptions">异常</span></div>
                <div class="dash-kpi-val dash-red" id="dash-kpi-exceptions">—</div>
                <div class="dash-kpi-sub" data-i18n="dash-kpi-exceptions-sub">需立即处理</div>
            </div>
            <div class="dash-kpi">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="M2 7h12"/></svg><span data-i18n="dash-kpi-plan">配额</span></div>
                <div class="dash-kpi-val" id="dash-kpi-plan">—</div>
                <div class="dash-kpi-sub" id="dash-kpi-plan-sub" data-i18n="dash-kpi-plan-sub">本月用量</div>
            </div>
        </div>
        <!-- v118.35.0.9 · credits 第二排 KPI · 账户余额 + 本月用量(分级显示) -->
        <div class="dash-kpi-grid dash-kpi-grid-credits" id="dash-kpi-credits" style="grid-template-columns: repeat(2, 1fr);">
            <div class="dash-kpi" id="dash-kpi-balance-card" style="display:none;">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2" y="4" width="12" height="9" rx="1.5"/><circle cx="11" cy="8.5" r="1.5"/></svg><span data-i18n="dash-kpi-balance">账户余额</span></div>
                <div class="dash-kpi-val" id="dash-kpi-balance">—</div>
                <div class="dash-kpi-sub" id="dash-kpi-balance-sub">&nbsp;</div>
            </div>
            <div class="dash-kpi" id="dash-kpi-usage-card">
                <div class="dash-kpi-label"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 13l4-5 3 3 5-7"/><circle cx="14" cy="4" r="1.2"/></svg><span data-i18n="dash-kpi-usage">本月用量</span></div>
                <div class="dash-kpi-val" id="dash-kpi-usage">—</div>
                <div class="dash-kpi-sub" id="dash-kpi-usage-sub">&nbsp;</div>
            </div>
        </div>
        <div class="dash-grid2">
            <div class="card">
                <div class="section-head">
                    <div class="section-title" data-i18n="dash-quick-title">快速操作</div>
                    <div class="section-sub" data-i18n="dash-quick-sub">3 步进入主流程</div>
                </div>
                <div class="dash-quick-list">
                    <button class="btn dash-quick-btn" onclick="window.routeTo && window.routeTo('ocr')">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 2v9"/><path d="M5 6l3-3 3 3"/><path d="M2 13h12"/></svg>
                        <span data-i18n="dash-quick-upload">上传发票</span>
                    </button>
                    <button class="btn dash-quick-btn" onclick="window.routeTo && window.routeTo('clients')">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="2" y="3" width="12" height="11" rx="1"/><path d="M5 6h6M5 9h6M5 12h3"/></svg>
                        <span data-i18n="dash-quick-clients">查看客户</span>
                    </button>
                    <button class="btn dash-quick-btn" onclick="window.routeTo && window.routeTo('reconcile')">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 4h10M3 8h10M3 12h7"/></svg>
                        <span data-i18n="dash-quick-reconcile">开始对账</span>
                    </button>
                    <button class="btn dash-quick-btn dash-quick-btn-warn" onclick="window.routeTo && window.routeTo('exceptions')">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 1l7 13H1z"/><path d="M8 6v4"/></svg>
                        <span data-i18n="dash-quick-exceptions">处理异常</span>
                        <span class="dash-quick-badge" id="dash-quick-exc-badge" style="display:none">0</span>
                    </button>
                </div>
            </div>
            <div class="card">
                <div class="section-head">
                    <div class="section-title" data-i18n="dash-recent-title">最近动态</div>
                    <div class="section-sub" data-i18n="dash-recent-sub">最近 5 条识别</div>
                </div>
                <div id="dash-recent-list" class="dash-recent-list">
                    <div class="dash-recent-empty" data-i18n="dash-recent-empty">还没有识别记录 · 去上传第一张吧</div>
                </div>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function vs(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function hs(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function gs(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function bs(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function ys(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let c=null;const m=()=>{c&&(clearTimeout(c),c=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(c=setTimeout(m,r)),m}window.showAlert=vs;window.hideAlerts=hs;window._humanizeBackendError=gs;window.humanizeError=bs;window.showToast=ys;function ws(e,n){return n=n||{},new Promise(a=>{const o=document.getElementById("confirm-modal"),s=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),c=document.getElementById("confirm-modal-close"),m=document.getElementById("confirm-modal-title");if(!o||!s||!i||!r){a(!1);return}m.textContent=n.title||t("confirm-default-title");const p=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const f=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),v=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");s.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${f}</div>
                <input type="text" id="${p}" placeholder="${v}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else s.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",o.style.display="flex";const u=f=>{o.style.display="none",i.onclick=null,r.onclick=null,c.onclick=null,o.onclick=null,document.removeEventListener("keydown",d),n.promptInput&&(s.innerHTML=""),r.style.display="",a(f)},l=()=>{const f=p?document.getElementById(p):null;return f?f.value:""},d=f=>{f.key==="Escape"?u(n.promptInput?null:!1):f.key==="Enter"&&u(n.promptInput?l():!0)};i.onclick=()=>u(n.promptInput?l():!0),r.onclick=()=>u(n.promptInput?null:!1),c.onclick=()=>u(n.promptInput?null:!1),o.onclick=f=>{f.target===o&&u(n.promptInput?null:!1)},document.addEventListener("keydown",d),setTimeout(()=>{if(n.promptInput){const f=document.getElementById(p);f&&f.focus()}else i.focus()},50)})}window.showConfirm=ws;function ks(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof xn=="function"&&xn()}catch(n){console.warn("settings tab side effect failed:",n)}}}function xs(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function _s(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function Es(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function xn(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}Bs(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function Bs(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
        <table style="width:100%; font-size:13px; border-collapse: collapse;">
            <tr>
                <td style="color:#a0aec0; padding:8px 0; width:140px;">${escapeHtml(t("settings-username"))}</td>
                <td style="padding:8px 0;">${a}</td>
            </tr>
            <tr>
                <td style="color:#a0aec0; padding:8px 0;">${escapeHtml(t("settings-billing-mode-title"))}</td>
                <td style="padding:8px 0;"><strong>${escapeHtml(t("settings-billing-mode"))}</strong></td>
            </tr>
            <tr>
                <td colspan="2" style="color:#a0aec0; padding:8px 0; font-size:12px;">
                    ${escapeHtml(t("settings-billing-pricing"))}
                </td>
            </tr>
        </table>
    `}window.switchSettingsTab=ks;window.fillSettingsForms=xs;window.saveProfile=_s;window.saveCompany=Es;window.renderSettings=xn;function on(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function Hn(e){return e=e||_userInfo,!!e&&(e.role==="owner"||on(e))}function Oa(e){return e=e||_userInfo,!!e&&e.role==="member"&&!on(e)}function Is(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!on(e)}function Va(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function Ua(e){return Oa(e)}function Ls(e){return Hn(e)}function Cs(e){return Hn(e)&&Va(e)}window.isMoneyHidden=Ua;window.isSuperAdmin=on;window.isOwner=Hn;window.isEmployee=Oa;window.isTrial=Is;window.isLifetime=Va;window.shouldHideMoney=Ua;window.canManageTeam=Ls;window.canManageApiKey=Cs;function Ss(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,c;if(o===0)r="danger",c=t("quota-banner-exhausted");else if(s>=90)r="danger",c=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",c=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(c)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const m=e.querySelector(".quota-banner-close");m&&m.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function Ts(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const c=document.querySelector('.settings-tab[data-tab="team"]');c&&(c.style.display=a?"":"none");const m=document.querySelector('.settings-panel[data-settings-panel="team"]');m&&(m.dataset.permHidden=a?"0":"1");const p=document.querySelector('.settings-tab[data-tab="api"]');p&&(p.style.display=o||isSuperAdmin(e)?"":"none");const u=document.querySelector('.settings-tab[data-tab="plan"]');u&&(u.style.display=n?"none":"");const l=document.querySelector('.settings-tab[data-tab="company"]');l&&(l.style.display=n?"none":"");const d=document.getElementById("info-bar");d&&(d.style.display=n?"none":"");const f=document.getElementById("trial-banner");f&&n&&(f.style.display="none");const v=document.getElementById("plan-banner");v&&n&&(v.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(w=>{w.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const w=document.querySelector(".settings-tab.active");w&&w.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(w){console.warn("[v118.12.3] failed to fix active tab:",w)}if(window.PEARNLY_ADMIN_MODE){const w=document.getElementById("admin-mode-banner");w&&(w.style.display="flex"),document.querySelectorAll(".nav-item").forEach(h=>{h.classList.contains("nav-admin-only")||(h.style.display="none")}),document.querySelectorAll(".nav-group").forEach(h=>{h.classList.contains("nav-group-admin-only")||(h.style.display="none")});const g=document.getElementById("client-switcher");g&&(g.style.display="none"),document.body.classList.add("admin-mode");const b=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(h=>{const E=h.dataset.tab;E&&!b.includes(E)&&(h.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(h=>{const E=h.dataset.pane;E&&!b.includes(E)&&(h.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(h=>{const E=h.querySelectorAll(".settings-tab");Array.from(E).some(_=>_.style.display!=="none")||(h.style.display="none")})}}function Ms(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
                <div class="info-chip">
                    <span class="chip-value chip-value-lifetime">${escapeHtml(t("info-unlimited-own-key"))}</span>
                </div>
            `:a=`
                <div class="info-chip chip-warn">
                    <span class="chip-value">${escapeHtml(t("info-need-api-key"))}</span>
                </div>
            `;else if(o==="admin"||e.is_super_admin)a=`
            <div class="info-chip">
                <span class="chip-value chip-value-lifetime">${escapeHtml(t("info-unlimited-own-key"))}</span>
            </div>
        `;else{const s=e.tenant_used!=null?e.tenant_used:e.used_this_month||0,i=e.tenant_quota!=null&&e.tenant_quota>0?e.tenant_quota:e.monthly_quota||0,r=i>0?Math.min(100,s/i*100):0;let c="";r>=95?c="danger":r>=80&&(c="warn"),i>0?a=`
                <div class="info-chip">
                    <span class="chip-label">${escapeHtml(t("info-monthly"))}</span>
                    <span class="chip-value">${s} / ${i}</span>
                    <div class="mini-bar"><div class="mini-bar-fill ${c}" style="width:${r}%"></div></div>
                </div>
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=Ss;window.applySidebarVisibility=Ts;window.renderInfoBar=Ms;async function Ga(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function Ka(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Ut(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function Oe(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function $s(e){const a=Ut(e==="seller"?"seller_tax":"buyer_tax");Oe(e,t("rd-verifying"),"loading");const o=await Ga("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){Oe(e,t(Ka(o.error)),"error");return}o.data&&o.data.valid?Oe(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):Oe(e,t("rd-status-invalid"),"invalid")}async function Hs(e){const a=Ut(e==="seller"?"seller_tax":"buyer_tax");Oe(e,t("rd-syncing"),"loading");const o=await Ga("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){Oe(e,t(Ka(o.error)),"error");return}Oe(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),As(e,o.data)}}function As(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=Ut(a),i=Ut(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==i&&r.push({field:o,label:t("rd-field-address"),current:i,official:n.address});const c=[];n.branch_label&&c.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&c.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let m=document.getElementById("rd-sync-modal");if(m||(m=document.createElement("div"),m.id="rd-sync-modal",m.className="rd-modal-mask",document.body.appendChild(m)),r.length===0)m.innerHTML=`
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t("rd-modal-title"))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    <div class="rd-modal-no-diff">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 12l5 5 9-9"/></svg>
                        ${escapeHtml(t("rd-modal-no-diff"))}
                    </div>
                    ${c.length?`<div class="rd-modal-extra">${c.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                </div>
            </div>
        `;else{const l=r.map((d,f)=>`
            <label class="rd-diff-row">
                <input type="checkbox" data-rd-apply data-field="${d.field}" data-value="${escapeHtml(d.official)}" checked>
                <div class="rd-diff-label">${escapeHtml(d.label)}</div>
                <div class="rd-diff-col rd-diff-current">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-current"))}</div>
                    <div class="rd-diff-val">${escapeHtml(d.current||"—")}</div>
                </div>
                <div class="rd-diff-arrow">→</div>
                <div class="rd-diff-col rd-diff-official">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-official"))}</div>
                    <div class="rd-diff-val">${escapeHtml(d.official)}</div>
                </div>
            </label>
        `).join("");m.innerHTML=`
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t("rd-modal-title"))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    ${l}
                    ${c.length?`<div class="rd-modal-extra">${c.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t("rd-modal-apply"))}</button>
                </div>
            </div>
        `}m.classList.add("show");const p=()=>m.classList.remove("show");m.querySelector(".rd-modal-close").addEventListener("click",p),m.querySelectorAll("[data-rd-modal-close]").forEach(l=>l.addEventListener("click",p)),m.addEventListener("click",l=>{l.target===m&&p()});const u=m.querySelector("[data-rd-modal-apply]");u&&u.addEventListener("click",()=>{const l=_results[_drawerIdx];if(!l){p();return}m.querySelectorAll("[data-rd-apply]:checked").forEach(d=>{const f=d.dataset.field,v=d.dataset.value;l.edits[f]=v,l.merged_fields[f]=v;const w=document.querySelector(`[data-field="${f}"]`);w&&(w.value=v);const g=document.querySelector(`[data-field-wrap="${f}"]`);g&&g.classList.add("edited")}),updateDrawerEditCount(),renderResults(),p()})}window.callRdVerify=$s;window.callRdSync=Hs;function js(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(s=>!s.is_duplicate&&!s.is_copy),o=a.length>0?a:e;for(const s of o){const i=s.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function Ps(e){const n=e.target.dataset.field,a=e.target.value,o=_results[_drawerIdx],s=o.merged_fields[n];a===(s??"")?delete o.edits[n]:(o.edits[n]=a,o.merged_fields[n]=a);const i=document.querySelector(`[data-field-wrap="${n}"]`);i&&i.classList.toggle("edited",o.edits[n]!==void 0),Ja(),renderResults()}function Ja(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=js;window.onFieldEdit=Ps;window.updateDrawerEditCount=Ja;function Ds(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
        <div class="force-pw-modal">
            <div class="force-pw-head">
                <div class="force-pw-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                </div>
                <div class="force-pw-title">${escapeHtml(t("force-pw-title")||"首次登录 · 请修改初始密码")}</div>
                <div class="force-pw-sub">${escapeHtml(t("force-pw-sub")||"老板设置的临时密码不安全 · 请立即修改")}</div>
            </div>
            <div class="force-pw-body">
                <div class="force-pw-field">
                    <label>${escapeHtml(t("force-pw-old")||"临时密码(老板告知您的)")}</label>
                    <input type="password" class="force-pw-input" id="force-pw-old" autocomplete="current-password">
                </div>
                <div class="force-pw-field">
                    <label>${escapeHtml(t("force-pw-new")||"新密码(至少 8 位 · 字母 + 数字)")}</label>
                    <input type="password" class="force-pw-input" id="force-pw-new" autocomplete="new-password">
                </div>
                <div class="force-pw-field">
                    <label>${escapeHtml(t("force-pw-new2")||"再次输入新密码")}</label>
                    <input type="password" class="force-pw-input" id="force-pw-new2" autocomplete="new-password">
                </div>
                <div class="force-pw-msg" id="force-pw-msg"></div>
            </div>
            <div class="force-pw-foot">
                <button class="btn btn-primary" type="button" id="force-pw-submit">${escapeHtml(t("force-pw-submit")||"修改并继续")}</button>
            </div>
        </div>
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,o=document.getElementById("force-pw-new").value,s=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!o){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(o!==s){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(o.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(o)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(o)&&/\d/.test(o))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(o===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:o})}),c=await r.json().catch(()=>({}));if(!r.ok){const m=c&&c.detail||"unknown",p={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=p[m]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=Ds;(function(){let e=null,n=null,a=null,o=null;function s(h){return document.getElementById(h)}async function i(){v(),g(),await r()}async function r(){try{const h=localStorage.getItem("mrpilot_token"),E=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!E.ok){w(t("linebot-err-status"));return}const y=await E.json();y.bound?c(y):await m()}catch{w(t("linebot-err-status"))}}function c(h){f(),s("linebot-unbound").style.display="none",s("linebot-bound").style.display="block";const E=s("linebot-status-summary");E&&(E.textContent=t("linebot-status-bound"),E.style.background="#D1FAE5",E.style.color="#065F46");const y=s("linebot-bound-name");y&&(y.textContent=h.line_display_name||"(LINE User)");const _=s("linebot-avatar");_&&(h.line_picture_url?(_.src=h.line_picture_url,_.style.display=""):_.style.display="none");const k=s("linebot-bound-since");k&&h.bound_at&&(k.textContent=new Date(h.bound_at).toLocaleString())}async function m(){s("linebot-bound").style.display="none",s("linebot-unbound").style.display="block";const h=s("linebot-status-summary");h&&(h.textContent=t("linebot-status-unbound"),h.style.background="#FEE2E2",h.style.color="#B91C1C"),await p(),d()}async function p(){try{const h=localStorage.getItem("mrpilot_token"),E=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+h}});if(!E.ok){w(t("linebot-err-code"));return}const y=await E.json();a=y.code,o=new Date(y.expires_at).getTime(),u(y)}catch{w(t("linebot-err-code"))}}function u(h){const E=s("linebot-code");E&&(E.textContent=h.code);const y=s("linebot-bot-id");y&&(y.textContent=h.bot_basic_id||t("linebot-bot-id-missing"));const _=s("linebot-qr");if(_)if(h.bot_friend_url){const k="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(h.bot_friend_url);_.classList.remove("empty"),_.innerHTML='<img src="'+k+'" alt="LINE Bot QR">'}else _.classList.add("empty"),_.innerHTML="";l()}function l(){e&&clearInterval(e);const h=s("linebot-code-expires");function E(){if(!o)return;const y=o-Date.now();if(y<=0){h&&(h.textContent=t("linebot-code-expired"),h.classList.add("expiring"));const B=s("linebot-code");B&&(B.style.opacity="0.4"),clearInterval(e),e=null;return}const _=Math.floor(y/1e3),k=Math.floor(_/60),x=_%60;h&&(h.textContent=t("linebot-code-expires-in").replace("{m}",k).replace("{s}",String(x).padStart(2,"0")),y<6e4?h.classList.add("expiring"):h.classList.remove("expiring"))}E(),e=setInterval(E,1e3)}function d(){f(),n=setInterval(async()=>{try{const h=localStorage.getItem("mrpilot_token"),E=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!E.ok)return;const y=await E.json();y.bound&&c(y)}catch{}},4e3)}function f(){n&&(clearInterval(n),n=null)}function v(){e&&(clearInterval(e),e=null),f()}function w(h){const E=s("linebot-error");E&&(E.textContent=h,E.style.display="block")}function g(){const h=s("linebot-error");h&&(h.style.display="none")}async function b(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const E=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+E}})).ok){w(t("linebot-err-unbind"));return}await i()}catch{w(t("linebot-err-unbind"))}}document.addEventListener("click",h=>{if(h.target.closest("#linebot-code-refresh")){h.preventDefault(),g(),p();return}if(h.target.closest("#linebot-unbind")){h.preventDefault(),b();return}}),window._loadLineBotPanel=i})();function sn(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const c=parseFloat(r.merged_fields.total_amount);isNaN(c)||(n+=c)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,c)=>({...r,_idx:c}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(c=>(c.filename||"").toLowerCase().includes(r)||(c.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,c)=>{let m,p;return _sortKey==="filename"?(m=r.filename,p=c.filename):_sortKey==="invoice_no"?(m=r.merged_fields.invoice_number,p=c.merged_fields.invoice_number):_sortKey==="invoice_date"?(m=r.merged_fields.date,p=c.merged_fields.date):_sortKey==="total"?(m=parseFloat(r.merged_fields.total_amount)||0,p=parseFloat(c.merged_fields.total_amount)||0):_sortKey==="confidence"?(m=r.confidence,p=c.confidence):(m="",p=""),m<p?_sortDir==="asc"?-1:1:m>p?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=s.map((r,c)=>{const m=r.merged_fields,p=`<span class="empty-cell">${t("empty-val")}</span>`,u="conf-tip-"+(r.confidence||"low"),l="conf-"+(r.confidence||"low"),d=t(u),f=t(l);return`
            <tr data-idx="${r._idx}">
                <td class="num">${c+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${m.invoice_number?escapeHtml(m.invoice_number):p}</td>
                <td class="date">${m.date?escapeHtml(m.date):p}</td>
                <td class="amount">${m.total_amount?Number(m.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):p}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(d)}">${f}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const c=parseInt(r.dataset.idx,10);Ya(c)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),sn()})});let la=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(la),la=setTimeout(()=>{_searchKeyword=n.trim(),sn(),Wa()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",sn(),Wa(),e.focus()});function Wa(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function Ya(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,i=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,c=document.getElementById("drawer-body"),m=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,p=i?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(c.innerHTML=`
        ${m}

        <!-- v118.19 · 决策区(C 位) · 会计每张发票真正要做的两个决策 -->
        <div class="drawer-decision-zone">
            <div class="drawer-decision-title">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="3.5" cy="3" r="1.4"/>
                    <circle cx="3.5" cy="13" r="1.4"/>
                    <circle cx="12.5" cy="8" r="1.4"/>
                    <path d="M3.5 4.4v7.2"/>
                    <path d="M3.5 8h7.6"/>
                </svg>
                <span>${escapeHtml(t("drawer-decision-title"))}</span>
            </div>
            <div class="drawer-decision-grid">
                <!-- 归属客户(左) -->
                <div class="drawer-client-card" data-field-wrap="client_id">
                    <div class="drawer-client-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 14v-1.2a2.4 2.4 0 00-2.4-2.4H4a2.4 2.4 0 00-2.4 2.4V14"/>
                            <circle cx="6.4" cy="5.2" r="2.4"/>
                        </svg>
                        <span>${escapeHtml(t("drawer-client-label"))}</span>
                    </div>
                    <div class="drawer-client-body">
                        <select class="drawer-client-select" id="drawer-client-select" ${s?"":"disabled"}>
                            <option value="">${escapeHtml(t("drawer-client-none"))}</option>
                        </select>
                        <button class="drawer-client-add" id="drawer-client-add" type="button" title="${escapeHtml(t("client-new"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M7 2v10M2 7h10"/></svg>
                        </button>
                    </div>
                </div>

                <!-- 记账科目(右) · 学过的发亮 -->
                <div class="drawer-suggest-card" data-field-wrap="category_tag">
                    <div class="drawer-suggest-head">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M2 4a1 1 0 011-1h4l2 2h5a1 1 0 011 1v6a1 1 0 01-1 1H3a1 1 0 01-1-1V4z"/>
                        </svg>
                        <span>${escapeHtml(t("drawer-suggest-category"))}</span>
                        ${r.category||n.category_tag?`<span class="drawer-suggest-learned" id="drawer-cat-learned-tag" title="${escapeHtml(t("drawer-suggest-learned-tip"))}">${escapeHtml(t("drawer-suggest-learned"))}</span>`:`<span class="drawer-suggest-empty">${escapeHtml(t("drawer-suggest-empty"))}</span>`}
                    </div>
                    <div class="drawer-suggest-body">
                        <input type="text" class="drawer-suggest-input" id="drawer-cat-input" data-field="category_tag"
                               list="drawer-cat-datalist"
                               placeholder="${escapeHtml(t("drawer-suggest-placeholder"))}"
                               value="${escapeHtml((n.edits&&n.edits.category_tag!==void 0?n.edits.category_tag:r.category||n.category_tag)||"")}"
                               ${s?"":"readonly"}>
                        <datalist id="drawer-cat-datalist"></datalist>
                    </div>
                </div>
            </div>
            <div class="drawer-decision-hint">${escapeHtml(t("drawer-suggest-hint"))}</div>
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 2h8l3 3v13H5z"/><path d="M13 2v3h3"/><path d="M8 10h6M8 13h6"/></svg>
                ${t("drawer-sec-basic")}
            </div>
            ${he("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",s)}
            ${he("date","drawer-lbl-date",r.date,"input",s)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${he("subtotal","drawer-lbl-subtotal",r.subtotal,"input",s)}
            ${he("vat","drawer-lbl-vat",r.vat,"input",s)}
            ${he("total_amount","drawer-lbl-total",r.total_amount,"input",s)}
            ${r.wht_amount||r.wht_rate?`
                ${he("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,Fs(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${he("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${he("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,p,ca("seller"))}
            ${he("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${he("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${he("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,p,ca("buyer"))}
            ${he("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?qs(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${he("notes","drawer-lbl-notes",r.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(u=>`--- Page ${u.page||u.page_number||"?"} ---
${u.raw_text||u.text||""}`).join(`

`))}</pre>
        </details>
    `,s?c.querySelectorAll("[data-field]").forEach(u=>{u.addEventListener("input",onFieldEdit)}):c.querySelectorAll("[data-field]").forEach(u=>{u.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const u=n._historyId||n.history_id||null;window.bindDrawerClient(u,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const u=document.getElementById("drawer-cat-input");u&&!u.value&&!u.readOnly&&u.focus()},80)}function Fs(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function he(e,n,a,o,s,i,r){const c=_results[_drawerIdx],m=c&&c.edits[e]!==void 0?c.edits[e]:a,p=c&&c.edits[e]!==void 0&&c.edits[e]!==a,u=escapeHtml(m??""),l=s?"":"readonly",d=o==="textarea"?`<textarea data-field="${e}" rows="2">${u}</textarea>`:`<input type="text" data-field="${e}" value="${u}">`;return`
        <div class="drawer-field ${p?"edited":""} ${l}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${d}
        </div>
    `}function ca(e){return _userInfo&&_userInfo.can_verify_tax?`
        <button class="rd-btn rd-btn-verify" data-rd-action="verify" data-rd-side="${e}" type="button">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8l3 3 7-7"/></svg>
            ${t("rd-btn-verify")}
        </button>
        <button class="rd-btn rd-btn-sync" data-rd-action="sync" data-rd-side="${e}" type="button">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 8a5 5 0 019-3l1.5 1.5M13 8a5 5 0 01-9 3L2.5 9.5M13 3v3h-3M3 13v-3h3"/></svg>
            ${t("rd-btn-sync")}
        </button>
        <span class="rd-status" data-rd-status="${e}"></span>
    `:`<button class="rd-btn-locked" data-upgrade="plus" type="button" title="${escapeHtml(t("rd-tip-upgrade"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="7" width="10" height="7" rx="1"/><path d="M5 7V5a3 3 0 016 0v2"/></svg>
        </button>`}function qs(e){return`
        <div class="drawer-items-header">
            <div>${t("drawer-item-name")}</div>
            <div>${t("drawer-item-qty")}</div>
            <div>${t("drawer-item-price")}</div>
            <div>${t("drawer-item-sub")}</div>
        </div>
        ${e.map(n=>`
            <div class="drawer-item-row">
                <div>${escapeHtml(n.name||"")}</div>
                <div>${escapeHtml(n.qty||n.quantity||"")}</div>
                <div>${escapeHtml(n.price||n.unit_price||"")}</div>
                <div>${escapeHtml(n.subtotal||n.total||"")}</div>
            </div>
        `).join("")}
    `}function Rs(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=sn;window.openDrawer=Ya;window.closeDrawer=Rs;function zs(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(c){return c&&c.enabled!==!1&&(c.adapter||"").toLowerCase()!=="mrerp_dms"});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let i;if(o.length===1){const c=o[0].name||o[0].adapter||"ERP";i=t("btn-push-to-name",{name:c}),s.title=i}else i=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,s.addEventListener("click",function(c){c.preventDefault(),c.stopPropagation(),o.length===1?Za(n,o[0].id):Ns(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function Ns(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(m=>m.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const i=a.map(function(m){const p=escapeHtml(m.name||m.adapter||"ERP"),u=escapeHtml((m.adapter||"").toLowerCase()),d=m.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(m.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+u+"</span>"+p+d+"</span></button>"}).join("");s.innerHTML=i,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",c,!0)},c=m=>{!s.contains(m.target)&&m.target!==e&&!e.contains(m.target)&&r()};setTimeout(()=>document.addEventListener("click",c,!0),0),s.addEventListener("click",m=>{const p=m.target.closest("[data-ep-id]");if(!p)return;const u=p.getAttribute("data-ep-id");r(),Za(n,u)})}async function Za(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),i=await s.json();if(!s.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=zs;const Os=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function Xa(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function Vs(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function Qa(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const p=[];for(const u of _results){const l=u.invoices&&u.invoices.length>0?u.invoices:null;if(l&&l.length>1)for(let d=0;d<l.length;d++){const f=l[d]||{};p.push({filename:u.filename+" #"+(d+1)+"/"+l.length,engine:u.engine,merged_fields:f.fields||{}})}else p.push({filename:u.filename,engine:u.engine,merged_fields:u.merged_fields})}a=await apiPost("/api/ocr/export",{records:p,lang:currentLang,template:"sales_detail_th"})}else{const p=[];for(const l of _results)l.history_ids&&Array.isArray(l.history_ids)?p.push(...l.history_ids):l.history_id&&p.push(l.history_id);if(p.length===0){showToast(t("toast-export-error"),"error");return}const u=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+u,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:p,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let p="HTTP "+a.status;try{const l=await a.json();l&&l.detail&&(p=typeof l.detail=="string"?l.detail:JSON.stringify(l.detail))}catch(l){console.warn("[export] resp.json err.detail parse failed:",l)}const u=typeof p=="string"&&p.indexOf(".")>0?"err."+p:null;showToast(u?t(u):t("toast-export-error")+" · "+p,"error");return}const s=await a.blob();let i=o;const r=a.headers.get("X-Filename");if(r)i=r;else{const u=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(u)try{i=decodeURIComponent(u[1])}catch{}}const c=URL.createObjectURL(s),m=document.createElement("a");m.href=c,m.download=i,document.body.appendChild(m),m.click(),document.body.removeChild(m),URL.revokeObjectURL(c),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{Qa(Xa())});function Us(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=Xa(),o=Os.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
            <div class="export-dd-item ${i.id===a?"active":""}" data-tpl="${i.id}">
                <div class="export-dd-row">
                    <span class="export-dd-name">${escapeHtml(t(i.nameKey))}</span>
                    ${r}
                    ${i.id===a?'<span class="export-dd-check">✓</span>':""}
                </div>
                <div class="export-dd-desc">${escapeHtml(t(i.descKey))}</div>
            </div>
        `}).join(""),s=`
        <div class="export-dd-divider"></div>
        <div class="export-dd-item export-dd-custom" data-tpl="__custom" title="${escapeHtml(t("tpl-custom-coming"))}">
            <div class="export-dd-row">
                <span class="export-dd-name">+ ${escapeHtml(t("tpl-custom-new"))}</span>
                <span class="export-dd-badge badge-soon">${escapeHtml(t("cs-coming-soon"))}</span>
            </div>
        </div>
    `;n.innerHTML=o+s,e.appendChild(n)}function fn(){const e=document.getElementById("export-dropdown");e&&e.remove()}const mn=document.getElementById("btn-export-arrow");mn&&mn.addEventListener("click",e=>{e.stopPropagation(),!mn.disabled&&Us()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){fn(),showToast(t("cs-coming-soon"),"info");return}Vs(a),fn(),Qa(a);return}e.target.closest("#btn-export-arrow")||fn()});function Gs(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(Gs,300);const Ks=`
        <div class="page-head-clean">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>
                </svg>
            </div>
            <div class="page-head-text">
                <div class="page-head-title" data-i18n="history-title">识别历史</div>
                <div class="page-head-sub" data-i18n="history-sub">保留近 90 天 · 点击行查看详情</div>
            </div>
        </div>

        <div class="card" id="history-free-block" style="display:none;">
            <div class="coming-soon">
                <svg class="cs-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="24" cy="24" r="18"/><path d="M24 14v10l7 5"/>
                </svg>
                <div class="cs-title" data-i18n="cs-history-title">识别历史管理</div>
                <div class="cs-desc" data-i18n="cs-no-access">该功能暂未开放 · 如有需要请联系我们</div>
            </div>
        </div>

        <div class="card" id="history-main" style="display:none;">
            <div class="results-head">
                <div class="results-head-left">
                    <div class="section-title" data-i18n="history-section-title">识别记录</div>
                    <div class="section-sub" data-i18n="history-section-sub">点击行查看详情</div>
                </div>
                <div class="results-head-stats" id="history-stats"></div>
            </div>

            <div class="history-filters">
                <div class="search-wrap">
                    <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/>
                    </svg>
                    <input type="text" class="search-input" id="history-search" data-i18n-placeholder="history-search-placeholder">
                    <button type="button" class="search-clear" id="history-search-clear" style="display:none;" aria-label="clear">✕</button>
                </div>
                <select class="history-range" id="history-range">
                    <option value="7" data-i18n="history-range-7">最近 7 天</option>
                    <option value="30" data-i18n="history-range-30">最近 30 天</option>
                    <option value="90" selected data-i18n="history-range-90">最近 90 天</option>
                </select>
                <span class="search-matches" id="history-search-matches"></span>
            </div>

            <div class="history-table-wrap">
                <!-- v0.16 · 批量操作工具栏 · 有选择时才显示 -->
                <!-- v118.32.3 · 批量栏改 Gmail 风格图标按钮(跟对账中心统一) -->
                <div class="history-batch-bar" id="history-batch-bar" style="display:none;">
                    <span class="history-batch-count" id="history-batch-count">已选 0 条</span>
                    <div class="history-batch-actions">
                        <button class="btn-icon hist-batch-icon-btn" id="history-batch-export" title="批量导出">
                            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4M4 15v2h12v-2"/></svg>
                        </button>
                        <button class="btn-icon hist-batch-icon-btn hist-batch-icon-danger" id="history-batch-delete" title="批量删除">
                            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h14M8 6V4a1 1 0 011-1h2a1 1 0 011 1v2m1 0v10a2 2 0 01-2 2H8a2 2 0 01-2-2V6m3 4v6m4-6v6"/></svg>
                        </button>
                        <button class="btn-icon hist-batch-icon-btn" id="history-batch-cancel" title="取消">
                            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>
                        </button>
                    </div>
                </div>
                <div class="history-table-head">
                    <div class="history-col-check">
                        <input type="checkbox" id="history-check-all" aria-label="select all">
                    </div>
                    <div data-i18n="history-col-date">日期</div>
                    <div data-i18n="history-col-file">文件 · 发票号 · 供应商</div>
                    <div class="history-cell-amount align-right" data-i18n="history-col-amount">金额</div>
                    <div class="history-cell-conf align-center" data-i18n="history-col-conf">置信</div>
                    <div class="history-cell-menu"></div>
                </div>
                <div id="history-tbody"></div>
            </div>

            <div class="history-foot">
                <div id="history-pager-info" class="history-pager-info"></div>
                <div class="history-pager-btns">
                    <button id="history-prev" class="btn btn-ghost">‹</button>
                    <button id="history-next" class="btn btn-ghost">›</button>
                </div>
            </div>
        </div>

        <div class="empty-state" id="history-empty" style="display:none;">
            <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="empty-icon">
                <rect x="8" y="10" width="32" height="30" rx="2"/>
                <path d="M16 20h16M16 28h12M16 36h8"/>
            </svg>
            <div class="empty-title" data-i18n="history-empty-title">还没有记录</div>
            <div class="empty-desc" data-i18n="history-empty-desc">识别的发票会自动出现在这里</div>
        </div>
`;(function(){const e=document.getElementById("page-history");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Ks,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();function An(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const i=s.filter(r=>_historySelected.has(r.id)).length;a.checked=i===s.length,a.indeterminate=i>0&&i<s.length}}}function Js(){_historySelected.clear(),An()}async function jn(){if(!_userInfo){setTimeout(()=>jn(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&s.set("client_id",String(i));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const p=await r.json().catch(()=>({}));if((typeof p.detail=="string"?p.detail:p.detail&&p.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const c=await r.json();_historyState.items=c.items||[],_historyState.total=c.total||0;const m=new Set(_historyState.items.map(p=>p.id));for(const p of Array.from(_historySelected))m.has(p)||_historySelected.delete(p);eo()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function eo(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(p=>{p.confidence==="high"&&s++});const i=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(p=>{const u=new Date(p.created_at),l=String(u.getMonth()+1).padStart(2,"0"),d=String(u.getDate()).padStart(2,"0"),f=String(u.getHours()).padStart(2,"0"),v=String(u.getMinutes()).padStart(2,"0"),w=`${l}-${d} ${f}:${v}`,g=escapeHtml(p.filename||""),b=g.length>50?g.substring(0,50)+"…":g,h=p.invoice_no?escapeHtml(p.invoice_no):b,E=[];p.seller_name&&E.push(escapeHtml(p.seller_name)),p.invoice_no&&p.filename&&E.push(b);const y=E.join(" · ")||"-",_=p.category_tag?`<span class="history-badge category">${escapeHtml(p.category_tag)}</span>`:"",k=p.source_total&&p.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:p.source_index||1,n:p.source_total}))}</span>`:"",x=p.total_amount!==null&&p.total_amount!==void 0?Number(p.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',B=[];(p.total_amount===null||p.total_amount===void 0)&&B.push(t("field-amount")),p.invoice_no||B.push(t("field-invoice-no")),p.invoice_date||B.push(t("field-invoice-date")),p.seller_name||B.push(t("field-seller-name")),B.length>0&&`${escapeHtml(p.id)}${escapeHtml(t("history-needs-review-tip")+" · "+B.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,p.edited&&`${escapeHtml(t("history-edited",{n:p.edit_count||1}))}`;const L=p.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",I=p.confidence==="high"?"high":p.confidence==="medium"?"mid":"low",C=p.confidence==="high"?t("conf-high"):p.confidence==="medium"?t("conf-medium"):t("conf-low"),S=`<span class="history-badge conf-${I}">${escapeHtml(C)}</span>`;let q="";const A=p.source||"manual";return A==="email"?q=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:A==="folder"?q=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:A==="api"&&(q=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(p.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(p.id)}" ${_historySelected.has(p.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${w}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${h} ${_} ${k} ${q} ${L}</div>
                        <div class="history-cell-subtitle">${y}</div>
                    </div>
                    <div class="history-cell-amount">${x}</div>
                    <div class="history-cell-conf">${S}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(p.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),An();const c=a.length>0?_historyState.page*_historyState.pageSize+1:0,m=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:c,to:m,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=jn;window.renderHistoryList=eo;window.updateHistoryBatchBar=An;window.clearHistorySelection=Js;typeof currentRoute<"u"&&currentRoute==="history"&&jn();async function Gt(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),Ys(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),Zs(a.id)}catch(n){console.error("open history detail failed",n)}}async function Ws(e){await Gt(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function Ys(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
        <button class="btn btn-ghost" id="btn-push-erp" title="${escapeHtml(t("btn-push-erp"))}" style="display:none;">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 8h9M8 5l3 3-3 3"/>
                <rect x="11" y="3" width="3" height="10" rx="1"/>
            </svg>
            <span>${escapeHtml(t("btn-push-erp"))}</span>
        </button>
        <span id="drawer-erp-pushed-badge" style="display:none;align-items:center;gap:4px;font-size:12px;font-weight:600;color:#059669;background:#D1FAE5;padding:3px 8px;border-radius:20px;white-space:nowrap;">
            <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:10px;height:10px;flex-shrink:0;"><path d="M2 6l3 3 5-5"/></svg>
            ${escapeHtml(t("erp-pushed-badge"))}
        </span>
        <div style="flex:1"></div>
        <button class="btn btn-primary" id="btn-save-history">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3 3 7-7"/></svg>
            <span>${escapeHtml(t("history-save"))}</span>
        </button>
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",Qs),document.getElementById("btn-push-erp").addEventListener("click",Xs)}async function Zs(e){}async function Xs(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function Qs(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(c=>!c.is_duplicate&&!c.is_copy),s=o>=0?o:0,i=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function ei(e,n){document.querySelectorAll(".history-popover").forEach(p=>p.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(p=>p.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",i=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const c=()=>{r.remove(),document.removeEventListener("click",m,!0)},m=p=>{!r.contains(p.target)&&p.target!==n&&c()};setTimeout(()=>document.addEventListener("click",m,!0),0),r.addEventListener("click",async p=>{const u=p.target.closest("[data-act]");if(!u||u.disabled)return;const l=u.dataset.act;if(c(),l==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const f=document.createElement("textarea");f.value=s,f.style.position="fixed",f.style.opacity="0",document.body.appendChild(f),f.select(),document.execCommand("copy"),document.body.removeChild(f),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(l==="download-pdf"){const d=showToast(t("history-download-pdf-loading"),"loading",0);try{const f=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!f.ok)throw new Error("download failed");const v=await f.blob(),w=URL.createObjectURL(v),g=document.createElement("a");g.href=w,g.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(g),g.click(),document.body.removeChild(g),setTimeout(()=>URL.revokeObjectURL(w),5e3),d(),showToast(t("history-download-pdf-ok"),"success")}catch{d(),showToast(t("history-download-pdf-fail"),"error")}}else if(l==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const c=r.target.closest(".history-row"),m=r.target.closest("[data-hmenu]");if(m){r.stopPropagation(),ei(m.dataset.hmenu,m);return}const p=r.target.closest("[data-review]");if(p){r.stopPropagation(),Gt(p.dataset.review);return}const u=r.target.closest("[data-fill-amount]");if(u){r.stopPropagation(),Ws(u.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||c&&!r.target.closest("[data-hmenu]")&&Gt(c.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const c=r.target.closest(".history-row-check");if(!c)return;const m=c.dataset.hid;c.checked?_historySelected.add(m):_historySelected.delete(m),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const c=r.target.checked;for(const m of _historyState.items)c?_historySelected.add(m.id):_historySelected.delete(m.id);document.querySelectorAll(".history-row-check").forEach(m=>{m.checked=c}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const m=Array.from(_historySelected);try{const p=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:m})});if(!p.ok)throw new Error("batch delete failed");const u=await p.json();showToast(t("history-batch-done",{n:u.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(p){console.error("batch delete",p),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const c=r.target.value;document.getElementById("history-search-clear").style.display=c?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=c.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=Gt;const lt=document.getElementById("drop-zone"),Pn=document.getElementById("file-input");lt.addEventListener("click",()=>Pn.click());Pn.addEventListener("change",e=>to(e.target.files));["dragover","dragenter"].forEach(e=>{lt.addEventListener(e,n=>{n.preventDefault(),lt.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{lt.addEventListener(e,n=>{n.preventDefault(),lt.classList.remove("drag-over")})});lt.addEventListener("drop",e=>{e.preventDefault(),to(e.dataTransfer.files)});const ti=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function _n(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function ni(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function ai(e){return ni(e)||_n(e)||ti.test(e.name)}function to(e){hideAlerts();const n=Array.from(e),a=n.filter(ai);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(c=>!_n(c)),s=a.filter(_n),i=new Set(_selectedFiles.map(c=>c.name+"_"+c.size));for(const c of o){const m=c.name+"_"+c.size;i.has(m)||(_selectedFiles.push({file:c,name:c.name,size:c.size,status:"waiting",errorKey:null,errorParams:null}),i.add(m))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(c){console.error("[upload] image route failed",c)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),rn(),Dn(),Pn.value=""}let Pt=!1;function rn(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(l=>l.status==="processing"||l.status==="retrying").length,o=_selectedFiles.filter(l=>l.status==="success").length,s=_selectedFiles.filter(l=>l.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const c=Pt?t("file-list-collapse"):t("file-list-expand"),m=_selectedFiles.map((l,d)=>{let f=t("status-"+l.status);l.status==="retrying"&&(f=t("status-retrying")),l.status==="error"&&l.errorKey&&(f=t(l.errorKey,l.errorParams||{}));const v=l.status==="processing"||l.status==="retrying"?'<span class="spinner"></span>':"",w=l.status==="error"&&l.canRetry?`<button class="file-retry-btn" data-retry-idx="${d}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",g=l.status==="success"&&l.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(l.name)}">${escapeHtml(l.name)}</span>
                ${g}
                <span class="file-status ${l.status}">${v}${f}</span>
                ${w}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(c)}</button>`:""}
        </div>
        <ul class="file-list-body${Pt?" expanded":""}" id="file-list-body">
            ${m}
        </ul>
    `;const p=document.getElementById("file-list-toggle");p&&p.addEventListener("click",()=>{Pt=!Pt,rn()});const u=document.getElementById("file-list-body");u&&!u.dataset.retryBound&&(u.dataset.retryBound="1",u.addEventListener("click",async l=>{const d=l.target.closest(".file-retry-btn");if(!d)return;const f=parseInt(d.dataset.retryIdx||"-1",10);if(f<0||f>=_selectedFiles.length)return;const v=_selectedFiles[f];!v||v.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(v,!0)}))}function Dn(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],rn(),renderResults(),Dn(),hideAlerts()});window.renderFileList=rn;window.updateStartButton=Dn;const oi=`
    <div class="modal" style="max-width:420px;">
        <div class="modal-head">
            <div class="modal-title camera-tips-title-row">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 7h4l2-2h6l2 2h4a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V8a1 1 0 011-1z"/>
                    <circle cx="12" cy="13" r="4"/>
                </svg>
                <span data-i18n="camera-tips-title">拍摄小贴士</span>
            </div>
        </div>
        <div class="modal-body">
            <ul class="camera-tips-list">
                <li><span class="tip-check"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3.5 3.5L13 5"/></svg></span><span data-i18n="camera-tip-bg">放在深色桌面上 · 与白纸对比明显</span></li>
                <li><span class="tip-check"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3.5 3.5L13 5"/></svg></span><span data-i18n="camera-tip-corners">四角完整露出 · 不要手指遮挡</span></li>
                <li><span class="tip-check"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3.5 3.5L13 5"/></svg></span><span data-i18n="camera-tip-light">避开反光和阴影 · 光线均匀</span></li>
                <li><span class="tip-check"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3.5 3.5L13 5"/></svg></span><span data-i18n="camera-tip-flat">尽量正对票据 · 压平褶皱</span></li>
            </ul>
            <label class="camera-tips-skip-row">
                <input type="checkbox" id="camera-tips-skip">
                <span data-i18n="camera-tips-skip">不再提示</span>
            </label>
        </div>
        <div class="modal-foot">
            <button class="btn btn-ghost" id="camera-tips-cancel" data-i18n="confirm-cancel">取消</button>
            <button class="btn btn-primary" id="camera-tips-ok" data-i18n="camera-tips-ok">开始拍照</button>
        </div>
    </div>
`;ve("camera-tips-modal",oi);async function Kt(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],i=o.naturalWidth,r=o.naturalHeight;(i<1e3||r<1e3)&&s.push("low_res");try{const c=document.createElement("canvas");c.width=64,c.height=64;const m=c.getContext("2d");m.drawImage(o,0,0,64,64);const p=m.getImageData(0,0,64,64).data;let u=0,l=0;for(let f=0;f<p.length;f+=4)u+=.299*p[f]+.587*p[f+1]+.114*p[f+2],l++;const d=l?u/l:128;d<70?s.push("too_dark"):d>235&&s.push("too_bright"),n({warnings:s,width:i,height:r,brightness:d})}catch{n({warnings:s,width:i,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}async function no(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let p=0;p<e.length;p++){const u=e[p],{dataUrl:l,naturalW:d,naturalH:f}=await si(u);p>0&&s.addPage("a4","p");const v=d/f;let w=a-10,g=w/v;g>o-10&&(g=o-10,w=g*v);const b=(a-w)/2,h=(o-g)/2,E=u.type==="image/png"?"PNG":"JPEG";s.addImage(l,E,b,h,w,g,void 0,"FAST")}const i=s.output("blob"),r=new Date,c=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),m=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${c}${m}.pdf`,{type:"application/pdf"})}function si(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await ri()||o.click()}),o.addEventListener("change",async c=>{const m=Array.from(c.target.files||[]);if(c.target.value="",m.length!==0)for(const p of m)await En([p],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=c=>async m=>{const p=Array.from(m.target.files||[]);if(m.target.value="",p.length===0)return;const u=p.filter(d=>d.type==="application/pdf"||/\.pdf$/i.test(d.name)),l=p.filter(d=>!u.includes(d));u.length>0&&await ii(u),l.length>0&&await En(l,c)};a&&a.addEventListener("change",r("gallery"))})();async function ii(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function ri(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const i=c=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(c)},r=c=>{c.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),o&&(o.onclick=()=>i(!1)),n.onclick=c=>{c.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}let _e=[],Ne=null;async function En(e,n){if(hideAlerts(),!(!e||e.length===0)){var a=typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice";if(a==="thai_id_card"){for(const s of e)_selectedFiles.push({file:s,name:s.name,size:s.size,status:"waiting",errorKey:null,errorParams:null});const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton();return}if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let o=0;o<30&&(await new Promise(s=>setTimeout(s,100)),!(window.jspdf&&window.jspdf.jsPDF));o++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const o=e[0];let s={};try{s=await Kt(o)}catch{}_e.push({file:o,quality:s}),Ne="camera",nt();return}if(n==="gallery"&&(e.length>=2||_e.length>0)){for(const o of e){let s={};try{s=await Kt(o)}catch{}_e.push({file:o,quality:s})}Ne="gallery",nt();return}await ao(e)}}async function li(e){const n=new Set;for(const o of e)try{((await Kt(o)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const o=await no(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function nt(){let e=document.getElementById("camera-buffer-bar");if(_e.length===0){e&&e.remove(),Ne=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=_e.length,a=n>=2,o=Ne==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?o?i=`
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="merge">${escapeHtml(t("camera-buffer-done-merge"))}</button>
            <button type="button" class="btn btn-primary btn-sm" data-cbb-action="separate">${escapeHtml(t("camera-buffer-done-separate",{n}))}</button>
        `:i=`
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="separate">${escapeHtml(t("camera-buffer-done-separate",{n}))}</button>
            <button type="button" class="btn btn-primary btn-sm" data-cbb-action="merge">${escapeHtml(t("camera-buffer-done-merge"))}</button>
        `:i=`<button type="button" class="btn btn-primary btn-sm" data-cbb-action="merge">${escapeHtml(t("camera-buffer-done"))}</button>`,e.innerHTML=`
        <div class="cbb-count">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7h4l2-2h6l2 2h4a1 1 0 011 1v11a1 1 0 01-1 1H3a1 1 0 01-1-1V8a1 1 0 011-1z"/>
                <circle cx="12" cy="13" r="4"/>
            </svg>
            <span>${escapeHtml(t("camera-buffer-count",{n}))}</span>
        </div>
        <div class="cbb-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="discard">${escapeHtml(t("camera-buffer-discard"))}</button>
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="more">${escapeHtml(s)}</button>
            ${i}
        </div>
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{_e=[],Ne=null,nt()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const m=o?"gallery-input":"camera-input",p=document.getElementById(m);p&&p.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const m=_e.map(p=>p.file);_e=[],Ne=null,nt(),await li(m)});const c=e.querySelector('[data-cbb-action="separate"]');c&&(c.onclick=async()=>{const m=_e.map(p=>p.file);_e=[],Ne=null,nt(),await ao(m)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{_e.length>0&&nt()});async function ao(e){const n=new Set;let a=0;for(const s of e)try{((await Kt(s)).warnings||[]).forEach(c=>n.add(c));const r=await no([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}window.handleCameraImages=En;(function(){var e="pearnly_ocr_doc_mode",n=!1,a=!1;function o(d){return typeof escapeHtml=="function"?escapeHtml(d==null?"":String(d)):String(d??"")}function s(){try{return localStorage.getItem(e)==="thai_id_card"?"thai_id_card":"invoice"}catch{return"invoice"}}window.getOcrDocumentMode=function(){return n?s():"invoice"};function i(){var d=document.getElementById("drop-zone");return d?d.closest(".card"):null}function r(){var d=i();if(!d)return null;var f=d.querySelector("#ocr-doc-mode");if(f)return f;var v=d.querySelector(".section-head");return f=document.createElement("div"),f.id="ocr-doc-mode",f.className="ocr-doc-mode",f.setAttribute("role","tablist"),f.style.cssText="display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;",v&&v.parentNode?v.parentNode.insertBefore(f,v.nextSibling):d.insertBefore(f,d.firstChild),f}function c(d,f,v){return'<button type="button" class="ocr-doc-seg'+(v?" active":"")+'" data-doc-mode="'+d+'" role="tab" aria-selected="'+(v?"true":"false")+'" style="border:none;background:'+(v?"var(--card,#fff)":"transparent")+";color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:"+(v?"600":"500")+";padding:6px 16px;border-radius:7px;cursor:pointer;box-shadow:"+(v?"0 1px 3px rgba(0,0,0,.08)":"none")+';transition:background .15s;">'+o(t(f))+"</button>"}function m(){var d=r();if(d){if(!n){d.style.display="none";return}var f=s();d.style.display="flex",d.innerHTML=c("invoice","ocr-mode-invoice",f==="invoice")+c("thai_id_card","ocr-mode-id-card",f==="thai_id_card")}}function p(d){try{localStorage.setItem(e,d==="thai_id_card"?"thai_id_card":"invoice")}catch{}m();try{document.dispatchEvent(new CustomEvent("ocr-doc-mode-change",{detail:{mode:window.getOcrDocumentMode()}}))}catch{}}async function u(d){if(!(a&&!d)){var f=localStorage.getItem("mrpilot_token");if(f)try{var v=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+f}});if(!v.ok)return;var w=await v.json(),g=w&&w.items||[];n=g.some(function(b){return b&&(b.adapter||"").toLowerCase()==="mrerp_dms"&&b.enabled!==!1}),a=!0,window._dmsHasEndpoint=n,m()}catch{}}}window._refreshOcrDocMode=function(){u(!0)},document.addEventListener("click",function(d){var f=d.target.closest(".ocr-doc-seg");f&&f.getAttribute("data-doc-mode")&&(d.preventDefault(),p(f.getAttribute("data-doc-mode")))}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("ocr-doc-mode",m);function l(){r(),m(),u(!1)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",l):l(),window.addEventListener("hashchange",function(){((location.hash||"").indexOf("ocr")>=0||location.hash===""||location.hash==="#home")&&setTimeout(function(){r(),u(!1)},60)})})();(function(){function e(i){return typeof escapeHtml=="function"?escapeHtml(i==null?"":String(i)):String(i??"")}function n(){var i=(function(){var c=document.getElementById("drop-zone");return c?c.closest(".card"):null})();if(!i||!i.parentNode)return null;var r=document.getElementById("dms-id-card-result");return r||(r=document.createElement("div"),r.id="dms-id-card-result",r.className="card",r.style.cssText="display:none;margin-top:16px;",i.parentNode.insertBefore(r,i.nextSibling),r)}function a(i,r){return'<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);"><span style="color:var(--muted,#6b6b66);font-size:13px;">'+e(t(i))+'</span><span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">'+e(r||"—")+"</span></div>"}function o(i){if(!i)return"";var r=[i.house_no,i.road,i.subdistrict,i.district,i.province,i.zipcode].filter(function(c){return c});return r.join(" ")||i.address_raw||""}function s(i){var r=i&&i.status||"failed",c,m,p;return r==="success"?(c="#0a7a2c",m="#d6f5e0",p="dms-result-status-success"):r==="needs_review"?(c="#9a6b00",m="#fdf0d0",p="dms-result-status-needs-review"):r==="skipped"?(c="#5d5d57",m="#eee",p="dms-result-status-skipped"):(c="#b3261e",m="#fbe0de",p="dms-result-status-failed"),'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:'+c+";background:"+m+';">'+e(t(p))+"</span>"}window.renderDmsIdCardResult=function(i){var r=n();if(r){i=i||{};var c=i.id_card||{},m=c.address||{},p=i.dms_push||{},u=p.status||(i.ok?"success":"failed"),l="";u==="success"&&(l=a("dms-result-customer",p.customer_id)+a("dms-result-booking",p.booking_no));var d=u==="failed"||u==="needs_review"?'<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">'+e(t("dms-result-retry"))+"</button>":"",f="";if(u==="failed"&&p.error_code){var v="dms-err-"+String(p.error_code).toLowerCase(),w=t(v);(!w||w===v)&&(w=t("dms-err-err_dms_unexpected")),f='<div style="margin-top:8px;color:#b3261e;font-size:12px;">'+e(w)+"</div>"}r.style.display="",r.innerHTML='<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;"><div class="section-title">'+e(t("dms-result-title"))+"</div>"+s(p)+'</div><div style="margin-top:8px;">'+a("dms-result-name",(c.first_name||"")+" "+(c.last_name||""))+a("dms-result-id",c.people_id_masked)+a("dms-result-birthday",c.birthday_be)+a("dms-result-address",o(m))+l+"</div>"+f+d}},window.clearDmsIdCardResult=function(){var i=document.getElementById("dms-id-card-result");i&&(i.style.display="none",i.innerHTML="")},document.addEventListener("click",function(i){i.target.closest("#dms-id-card-retry")&&(i.preventDefault(),typeof window._dmsRetryIdCard=="function"&&window._dmsRetryIdCard())})})();async function oo(e){let n;if(e)n=_selectedFiles.find(a=>a.file===e)||{file:e,name:e.name,status:"waiting"};else{const a=_selectedFiles.filter(o=>o.status==="waiting");if(!a.length)return;n=a[0]}window._dmsLastFile=n.file,n.status="processing",typeof renderFileList=="function"&&renderFileList();try{const a=new FormData;a.append("file",n.file,n.name),a.append("push","true");const o=await fetch("/api/dms/id-card-booking",{method:"POST",headers:{Authorization:"Bearer "+token},body:a});if(o.status===401||o.status===403){const i=await o.clone().json().catch(()=>({})),r=i&&i.detail,c=typeof r=="string"?r:r&&r.code||"";if(!c||c.startsWith("auth.")){localStorage.removeItem("mrpilot_token"),showToast(t("alert-session"),"error"),setTimeout(()=>{window.location.href="/"},1200);return}}const s=await o.json().catch(()=>({}));if(!o.ok){n.status="error";const i=s&&s.detail&&(s.detail.code||s.detail)||"unknown";n.errorKey="err."+i,n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:String(i)}});return}n.status=s.ok||s.dms_push&&s.dms_push.status==="needs_review"?"success":"error",typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult(s),typeof updateStartButton=="function"&&updateStartButton()}catch{n.status="error",n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:"network"}})}}window._dmsRetryIdCard=function(){window._dmsLastFile&&oo(window._dmsLastFile)};document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,(typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice")==="thai_id_card"){try{await oo()}finally{const l=document.getElementById("btn-start");l&&(l.disabled=!1)}return}if(_userInfo&&_userInfo.plan==="free"){const l=await fetch("/api/health").then(d=>d.json()).catch(()=>null);l&&!l.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const n=_selectedFiles.filter(l=>l.status==="waiting"),a=6;async function o(l,d){if(window._ocrAborted)return l.status="cancelled",l.errorKey=null,renderFileList(),{};l.status=d?"retrying":"processing",l.canRetry=!1,renderFileList();const f=new AbortController,v=setTimeout(()=>f.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(f);try{const w=new FormData;w.append("file",l.file,l.name);try{if(typeof window.getCurrentClientId=="function"){const y=window.getCurrentClientId();y!=null&&w.append("client_id",String(y))}}catch{}const g=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:w,signal:f.signal});if(clearTimeout(v),window._ocrCtrls.delete(f),g.status===401||g.status===403){const _=await g.clone().json().catch(()=>({})),k=_&&_.detail,x=typeof k=="string"?k:k&&k.code||"";if(!x||x.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),x==="auth.session_revoked")_showSessionRevokedModal();else{const B=x==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(B),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}x==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!g.ok){const _=(await g.json().catch(()=>({}))).detail;return typeof _=="string"?(l.errorKey="err."+_,l.errorParams=null):_&&_.code?(l.errorKey="err."+_.code,l.errorParams={..._,mb:_quota.max_file_size_mb}):(l.errorKey="err.unknown",l.errorParams=null),(l.errorKey==="err.unknown"||l.errorKey==="err.ocr.engine_error")&&(g.status===429?l.errorKey="err.rate_limit":g.status===502||g.status===503||g.status===504?l.errorKey="err.gemini_overloaded":g.status>=500&&(l.errorKey="err.server")),l.status="error",l.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(l.errorKey||""),renderFileList(),{}}const b=await g.json();l.status="success",l.fromCache=!!b.from_cache;const h=mergeFields(b.pages),E=b.confidence||(h.items&&h.items.length>0?"high":"low");if(_results.push({filename:b.filename,pages:b.pages,page_count:b.page_count,elapsed_ms:b.elapsed_ms,engine:b.engine,merged_fields:h,edits:{},confidence:E,history_id:b.history_id,history_ids:b.history_ids||[],invoice_count:b.invoice_count||1,invoices:b.invoices||[],archive_name:b.archive_name||null,category_tag:b.category_tag||null,auto_pushed:!!b.auto_pushed,typhoon_enhanced:!!b.typhoon_enhanced,typhoon_pages:b.typhoon_pages||[],from_cache:!!b.from_cache}),b.invoice_count&&b.invoice_count>1&&showToast(t("multi-invoice-toast",{file:b.filename,n:b.invoice_count}),"success"),b.missed_invoice_warnings&&b.missed_invoice_warnings.length){const y=b.missed_invoice_warnings.map(function(_){return _.page}).filter(function(_){return _!=null});showToast(t("missed-invoice-warn",{file:b.filename,pages:y.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",b.missed_invoice_warnings)}if(b.typhoon_enhanced&&b.typhoon_pages&&b.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:b.filename,n:b.typhoon_pages.length}),"success"),b.fallback_used){const y=b.engine_chain||[],_=b.engine||"";let k;_==="typhoon_nvidia"?k="fallback-typhoon-nvidia-toast":_==="easyocr"?k="fallback-easyocr-toast":k="fallback-generic-toast",showToast(t(k,{file:b.filename}),"warn"),console.info("[OCR Chain]",y)}if(b.from_cache&&showToast(t("cache-hit-toast",{file:b.filename}),"info"),b.duplicate_warnings&&b.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const y of b.duplicate_warnings)window._dupQueue.push({filename:b.filename,...y})}return b.auto_pushed&&showToast(t("auto-push-fired",{file:b.filename}),"info"),b.quota&&b.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=b.quota.used_this_month,_userInfo.tenant_used=b.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(w){clearTimeout(v);try{window._ocrCtrls&&window._ocrCtrls.delete(f)}catch{}console.error("[Upload] failed for",l.file.name,w);const g=w&&(w.name==="AbortError"||w==="timeout"),b=g&&(f.signal.reason==="timeout"||w==="timeout"),h=w&&w.message&&/NetworkError|Failed to fetch/i.test(w.message);return g&&(f.signal.reason==="user_stop"||window._ocrAborted)?(l.status="cancelled",l.errorKey=null,l.canRetry=!1,renderFileList(),{}):(b?l.errorKey="err.timeout":g?l.errorKey="err.aborted":h?l.errorKey="err.network":(l.errorKey="err.unknown",l.errorParams={msg:w&&w.message?w.message:String(w)}),l.status="error",!d&&!window._ocrAborted&&(h||b)&&navigator.onLine!==!1&&(l.canRetry=!0,renderFileList(),await new Promise(y=>setTimeout(y,2e3)),l.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?o(l,!0):(l.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=o;let s=0,i=!1;async function r(){for(;s<n.length&&!i&&!window._ocrAborted;){const l=s++,d=await o(n[l]);if(d&&d.abort){i=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const c=document.getElementById("btn-start"),m=document.getElementById("btn-stop");c&&(c.style.display="none"),m&&(m.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(n)}catch{}const p=[];for(let l=0;l<Math.min(a,n.length);l++)p.push(r());await Promise.all(p);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}c&&(c.style.display=""),m&&(m.style.display="none");const u=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const l={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const f of n)if(f.status==="success")l.success++;else if(f.status==="cancelled")l.cancelled++;else if(f.status==="error"){const v=f.errorKey||"";v==="err.network"?l.network++:v==="err.timeout"||v==="err.aborted"?l.timeout++:v.indexOf("quota")>=0||v==="err.monthly_limit_exceeded"?l.quota++:v==="err.gemini_overloaded"||v==="err.server"?l.overloaded++:v==="err.rate_limit"?l.rate++:l.other++}const d=n.length;u?showToast(ci(l,d),"warn",4e3):d>1&&l.network+l.timeout+l.quota+l.overloaded+l.rate+l.other>0&&showToast(di(l),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function ci(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function di(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});function so(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=f=>f!=null?Number(f).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",c=f=>f||"—",m=f=>{try{const v=new Date(f);return`${v.getFullYear()}-${String(v.getMonth()+1).padStart(2,"0")}-${String(v.getDate()).padStart(2,"0")}`}catch{return f}},p=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",u=(e.matched_fields||[]).map(f=>{const v=t("dup-field-"+f.replace("_","-"))||f;return`<span class="dup-field-chip">${escapeHtml(v)}</span>`}).join(" "),l=document.createElement("div");l.className="log-detail-modal",l.innerHTML=`
        <div class="log-detail-box dup-dialog">
            <div class="dup-head" style="background:${i};">
                <div class="dup-title" style="color:${s};">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:22px;height:22px;vertical-align:-5px;margin-right:6px;">
                        <path d="M10 2.5L1 17h18L10 2.5z"/><path d="M10 8v4M10 14v0.5"/>
                    </svg>
                    ${escapeHtml(t(a))}
                </div>
                <button class="log-detail-close dup-close" type="button">✕</button>
            </div>
            <div class="dup-body">
                <div class="dup-desc">${escapeHtml(t(o))}</div>
                <div class="dup-source">
                    <div class="dup-source-label">${escapeHtml(t("dup-current-file"))}${escapeHtml(p)}</div>
                    <div class="dup-source-name">${escapeHtml(e.filename)}</div>
                </div>
                <div class="dup-matched-label">${escapeHtml(t("dup-matched-on"))} ${u}</div>
                <table class="dup-compare">
                    <thead>
                        <tr>
                            <th></th>
                            <th>${escapeHtml(t("dup-this-one"))}</th>
                            <th>${escapeHtml(t("dup-existing-one"))}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>${escapeHtml(t("dup-field-invoice-no"))}</td><td>${escapeHtml(e.current.invoice_no||"—")}</td><td>${escapeHtml(e.match.invoice_no||"—")}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-invoice-date"))}</td><td>${escapeHtml(c(e.current.invoice_date))}</td><td>${escapeHtml(c(e.match.invoice_date))}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-seller-name"))}</td><td>${escapeHtml(e.current.seller_name||"—")}</td><td>${escapeHtml(e.match.seller_name||"—")}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-total-amount"))}</td><td>${r(e.current.total_amount)}</td><td>${r(e.match.total_amount)}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-original-file"))}</td><td>—</td><td>${escapeHtml(e.match.filename||"—")}</td></tr>
                        <tr><td>${escapeHtml(t("dup-field-uploaded-at"))}</td><td>—</td><td>${escapeHtml(m(e.match.created_at))}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="dup-actions">
                <button class="btn btn-ghost btn-tiny" data-action="view">${escapeHtml(t("dup-action-view"))}</button>
                <button class="btn btn-danger btn-tiny" data-action="delete">${escapeHtml(t("dup-action-delete"))}</button>
                <button class="btn btn-primary btn-tiny" data-action="keep">${escapeHtml(t("dup-action-keep"))}</button>
            </div>
        </div>
    `,document.body.appendChild(l);const d=()=>{l.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(so,200)};l.querySelector(".dup-close").addEventListener("click",d),l.querySelector('[data-action="view"]').addEventListener("click",()=>{const f=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(f)},400),d()}),l.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const f=e.new_history_id;if(!f){d();return}try{(await fetch(`/api/history/${encodeURIComponent(f)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}d()}),l.querySelector('[data-action="keep"]').addEventListener("click",d)}window.showDuplicateDialog=so;function Ve(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function ht(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function pi(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ve("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ve("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ve("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ve("time-day-ago-suffix"," 天前")}catch{return""}}async function Fn(){io();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const c={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[m,p,u]=await Promise.all([fetch("/api/me/tenant-usage",{headers:c}).then(g=>g.ok?g.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:c}).then(g=>g.ok?g.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:c}).then(g=>g.ok?g.json():null).catch(()=>null)]),l=m&&m.ocr_this_month||0;let d=0;const f=p&&(p.items||p.history||p)||[],v=Array.isArray(f)?f:[];v.forEach(g=>{(g.status==="pending"||g.status==="reviewing")&&d++});const w=u&&(u.total||u.count||u.pending||0)||0;if(e&&(e.textContent=ht(l)),n&&(n.textContent=ht(d)),a&&(a.textContent=ht(w)),r&&(w>0?(r.style.display="",r.textContent=w):r.style.display="none"),o&&m){const g=m.ocr_this_month||0,b=m.quota||0;o.textContent=ht(g),s&&(s.textContent=b?g+" / "+ht(b)+" 张":Ve("dash-kpi-plan-sub","本月用量"))}if(i)if(v.length===0)i.innerHTML='<div class="dash-recent-empty">'+Ve("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const g=v.slice(0,5).map(b=>{const h=(b.invoice_no||b.filename||b.id||"").toString(),E=(b.supplier_name||b.buyer_name||b.client_name||b.notes||"").toString(),y=pi(b.created_at||b.upload_time||b.date),_=k=>String(k).replace(/[&<>"']/g,x=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[x]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+_(h)+'">'+_(h)+'</span><span class="dash-recent-mid" title="'+_(E)+'">'+_(E)+'</span><span class="dash-recent-time">'+_(y)+"</span></div>"}).join("");i.innerHTML=g}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+Ve("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Fn;async function io(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},c=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!c.ok){e.style.display="none",s&&(s.textContent="—"),i&&(i.textContent="");return}const m=await c.json(),p=!!m.is_owner,u=!!m.is_billing_exempt;if(!p)e.style.display="none";else if(e.style.display="",u)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const d=typeof m.balance_thb=="number"?m.balance_thb:0;if(a&&(a.textContent="฿"+d.toFixed(2),a.className=d<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const f=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",v=d<50?"#dc2626":"#6b7280",w=g=>typeof window.escapeHtml=="function"?window.escapeHtml(g):String(g).replace(/[&<>"']/g,b=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[b]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+v+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+w(f)+"</a>"}}const l=typeof m.pages_this_month=="number"?m.pages_this_month:typeof m.my_invoice_count=="number"?m.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(l)),i){const d=l>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",f=typeof window.t=="function"?window.t(d,{used:l}):l+" pages";i.textContent=f}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=io;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Fn,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Fn()});function te(e){return(typeof window.t=="function"?window.t(e):null)||e}function qn(){return localStorage.getItem("mrpilot_token")||""}function X(e){return document.getElementById(e)}var zt=null,xt=null;function ro(){xt||(xt=setInterval(function(){if(!document.hidden){var e=qn();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;zt!==null&&a>zt&&(window.showToast&&window.showToast(te("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),zt=a}}).catch(function(){}))}},3e4))}function ui(){xt&&(clearInterval(xt),xt=null),zt=null}window._startCreditsPoll=ro;window._stopCreditsPoll=ui;ro();var Rn=null,zn=0;function fi(){if(!X("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),mi()}}function lo(){var e=function(n,a){var o=X(n);o&&(o.textContent=a)};e("tv2-title",te("topup-title")),e("tv2-sl1",te("topup-step1")),e("tv2-sl2",te("topup-step2")),e("tv2-sl3",te("topup-step3")),e("tv2-al",te("topup-amount-label")),e("tv2-bl",te("topup-bank-label")),e("tv2-copy",te("topup-copy-account")),e("tv2-dt",te("topup-slip-drop")),e("tv2-pl",te("topup-payer-label")),e("tv2-nl",te("topup-note-label"))}function Tt(e){[1,2,3].forEach(function(s){var i=X("tv2-s"+s);i&&(i.style.display=s===e?"":"none");var r=X("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=X("tv2-back"),a=X("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=te("topup-btn-cancel")):n&&(n.style.display="",n.textContent=te("topup-btn-back")),a&&(a.textContent=te(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=X("tv2-bn");o&&(o.innerHTML=te("topup-bank-note").replace("{amount}","<strong>฿"+Number(zn).toLocaleString()+"</strong>"))}}function Bn(){for(var e=1;e<=3;e++){var n=X("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function Jt(e){var n=X(e);n&&(n.textContent="",n.style.display="none")}function _t(e,n){var a=X(e);a&&(a.textContent=n,a.style.display="")}function da(e){var n=X("tv2-dt");n&&(n.textContent=e.name);var a=X("tv2-drop");a&&a.classList.add("has-file"),Jt("tv2-se")}function mi(){var e=X("topup-v2-ov");X("tv2-close").addEventListener("click",bt),e.addEventListener("click",function(i){i.target===e&&bt()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&bt()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(m){m.classList.remove("active")}),r.classList.add("active");var c=X("tv2-amt");c&&(c.value=r.dataset.val,Jt("tv2-ae"))}});var n=X("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),Jt("tv2-ae")});var a=X("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=te("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var o=X("tv2-drop"),s=X("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(i){i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(i){i.preventDefault(),o.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&da(r)})),s&&s.addEventListener("change",function(){s.files[0]&&da(s.files[0])}),X("tv2-back").addEventListener("click",function(){var i=Bn();if(i<=1){bt();return}Tt(i-1)}),X("tv2-next").addEventListener("click",function(){var i=Bn();i===1?vi():i===2?Tt(3):hi()})}async function vi(){var e=X("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){_t("tv2-ae",te("topup-amount-invalid"));return}if(n>5e5){_t("tv2-ae",te("topup-amount-too-large"));return}zn=n;var a=X("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+qn()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),i=te("topup-submit-fail");try{var r=JSON.parse(s),c=r.detail;if(Array.isArray(c)&&c.length){var m=c[0]&&c[0].type||"";m.indexOf("less_than")>=0?i=te("topup-amount-too-large"):(m.indexOf("greater_than")>=0||m.indexOf("parsing")>=0)&&(i=te("topup-amount-invalid"))}else typeof c=="string"&&(i=c)}catch{}throw new Error(i)}var p=await o.json();Rn=p.request_id,Tt(2)}catch(u){_t("tv2-ae",u.message||te("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=te("topup-btn-next"))}}async function hi(){var e=X("tv2-file");if(!e||!e.files||!e.files[0]){_t("tv2-se",te("topup-slip-required"));return}var n=X("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=X("tv2-payer"),s=X("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+Rn,{method:"POST",headers:{Authorization:"Bearer "+qn()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(te("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(te("topup-pending"),"info"),bt()}catch(c){_t("tv2-ue",te("topup-upload-fail")+" · "+c.message),n&&(n.disabled=!1,n.textContent=te("topup-btn-submit"))}}function bt(){var e=X("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){fi(),Rn=null,zn=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=X(a);o&&(o.value="")});var e=X("tv2-file");e&&(e.value="");var n=X("tv2-drop");n&&n.classList.remove("has-file","drag-over"),X("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){Jt(a)}),lo(),Tt(1),X("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=X("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(lo(),Tt(Bn()))});const gi=`
        <div class="page-head">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 2v3M19 2v3M5 5h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2z"/>
                    <path d="M8 13l2.5 2.5L16 10"/>
                </svg>
            </div>
            <div class="page-head-text">
                <h1 class="page-title" data-i18n="tc-title">测试中心</h1>
                <div class="page-subtitle" data-i18n="tc-sub">勾选测试清单 + 自动收集异常 · 一键复制给 Claude 定位 BUG</div>
            </div>
        </div>

        <!-- 顶部状态条 -->
        <div class="tc-status-bar">
            <div class="tc-status-item">
                <span class="tc-status-label" data-i18n="tc-version">版本</span>
                <span class="tc-status-value" id="tc-version-chip">v118.28.5</span>
            </div>
            <div class="tc-status-item">
                <span class="tc-status-label" data-i18n="tc-account">账号</span>
                <span class="tc-status-value" id="tc-account-chip">—</span>
            </div>
            <div class="tc-status-item">
                <span class="tc-status-label" data-i18n="tc-progress">进度</span>
                <span class="tc-status-value" id="tc-progress-chip">0 / 0</span>
            </div>
            <div class="tc-status-actions">
                <button type="button" class="tc-btn tc-btn-primary" id="tc-btn-copy-all">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="6" y="6" width="11" height="11" rx="2"/>
                        <path d="M14 6V4a2 2 0 00-2-2H5a2 2 0 00-2 2v7a2 2 0 002 2h2"/>
                    </svg>
                    <span data-i18n="tc-copy-all">复制结果给 Claude</span>
                </button>
            </div>
        </div>

        <!-- 区 1 · 测试清单 -->
        <div class="tc-card">
            <div class="tc-card-head">
                <h2 class="tc-card-title" data-i18n="tc-checklist-title">✅ 测试清单</h2>
                <div class="tc-card-actions">
                    <button type="button" class="tc-btn-text" id="tc-btn-reset-checklist">
                        <span data-i18n="tc-reset-checklist">重置勾选</span>
                    </button>
                </div>
            </div>
            <div class="tc-checklist" id="tc-checklist-body">
                <!-- JS 渲染 -->
            </div>
        </div>

        <!-- 区 2 · 异常日志 -->
        <div class="tc-card">
            <div class="tc-card-head">
                <h2 class="tc-card-title">
                    <span data-i18n="tc-logs-title">🔴 异常日志</span>
                    <span class="tc-logs-count" id="tc-logs-count">0</span>
                </h2>
                <div class="tc-card-actions">
                    <div class="tc-filter-group" id="tc-logs-filter">
                        <button type="button" class="tc-filter-chip active" data-filter="all" data-i18n="tc-filter-all">全部</button>
                        <button type="button" class="tc-filter-chip" data-filter="js_error" data-i18n="tc-filter-js">JS 错误</button>
                        <button type="button" class="tc-filter-chip" data-filter="api" data-i18n="tc-filter-api">API 失败</button>
                        <button type="button" class="tc-filter-chip" data-filter="api_slow" data-i18n="tc-filter-slow">慢请求</button>
                        <button type="button" class="tc-filter-chip" data-filter="console" data-i18n="tc-filter-console">Console</button>
                    </div>
                    <button type="button" class="tc-btn-text" id="tc-btn-copy-logs">
                        <span data-i18n="tc-copy-logs">复制最近 30 条</span>
                    </button>
                    <button type="button" class="tc-btn-text tc-btn-danger" id="tc-btn-clear-logs">
                        <span data-i18n="tc-clear-logs">清空</span>
                    </button>
                </div>
            </div>
            <div class="tc-logs" id="tc-logs-body">
                <div class="tc-logs-empty" data-i18n="tc-logs-empty">暂无异常 · 开始测试就会自动捕获 JS 错误 / API 失败 / 慢请求</div>
            </div>
        </div>

        <!-- 区 4 · 一键工具 -->
        <div class="tc-card">
            <div class="tc-card-head">
                <h2 class="tc-card-title" data-i18n="tc-tools-title">🔧 一键工具</h2>
            </div>
            <div class="tc-tools">
                <button type="button" class="tc-tool-btn" id="tc-tool-health">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 11h3l2-6 4 12 2-6h3"/>
                    </svg>
                    <div class="tc-tool-text">
                        <span class="tc-tool-name" data-i18n="tc-tool-health">后端健康检查</span>
                        <span class="tc-tool-desc" data-i18n="tc-tool-health-desc">测后端 API 通不通 · 看延迟</span>
                    </div>
                </button>
                <button type="button" class="tc-tool-btn" id="tc-tool-clear-session">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 6h14M8 6V4a1 1 0 011-1h2a1 1 0 011 1v2"/>
                        <path d="M5 6l1 11a1 1 0 001 1h6a1 1 0 001-1l1-11"/>
                    </svg>
                    <div class="tc-tool-text">
                        <span class="tc-tool-name" data-i18n="tc-tool-clear">清空 session 状态</span>
                        <span class="tc-tool-desc" data-i18n="tc-tool-clear-desc">日志 + 勾选 + 客户切换器选择 全部回到默认</span>
                    </div>
                </button>
                <button type="button" class="tc-tool-btn" id="tc-tool-reload-clients">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M16 10A6 6 0 014 10M4 10l-2-2M4 10l2-2"/>
                        <path d="M4 10A6 6 0 0116 10M16 10l2 2M16 10l-2 2"/>
                    </svg>
                    <div class="tc-tool-text">
                        <span class="tc-tool-name" data-i18n="tc-tool-reload-clients">强制刷新客户缓存</span>
                        <span class="tc-tool-desc" data-i18n="tc-tool-reload-clients-desc">重新拉客户列表 · 切换器立即更新</span>
                    </div>
                </button>
            </div>
        </div>

    `;ve("page-test-center",gi);(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",i=!1,r=!1;function c(T,F,O){let G=typeof t=="function"?t(T):null;return(!G||G===T)&&(G=F),O&&Object.keys(O).forEach(function($){G=String(G).replace("{"+$+"}",String(O[$]))}),G}function m(){try{const T=localStorage.getItem(n);o=T?JSON.parse(T):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function p(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function u(T){const F=new Date(T),O=function(G){return G<10?"0"+G:""+G};return O(F.getHours())+":"+O(F.getMinutes())+":"+O(F.getSeconds())}function l(T){return String(T??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function d(T,F){try{typeof showToast=="function"?showToast(T,F||"info"):alert(T)}catch{}}function f(T){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(T).then(function(){d(c("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){v(T)}):v(T)}catch{v(T)}}function v(T){try{const F=document.createElement("textarea");F.value=T,F.style.position="fixed",F.style.opacity="0",document.body.appendChild(F),F.select();const O=document.execCommand("copy");document.body.removeChild(F),d(O?c("tc-toast-copied","已复制"):c("tc-toast-copy-fail","复制失败"),O?"success":"error")}catch{d(c("tc-toast-copy-fail","复制失败"),"error")}}function w(){const T=document.getElementById("tc-account-chip"),F=document.getElementById("tc-progress-chip");if(T&&(T.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),F){const O=a.length,G=a.filter(function($){return o[$.id]}).length;F.textContent=G+" / "+O}}function g(){const T=document.getElementById("tc-checklist-body");if(!T)return;const F={};a.forEach(function(G){F[G.group]||(F[G.group]=[]),F[G.group].push(G)});const O=[];Object.keys(F).forEach(function(G){O.push('<div class="tc-checklist-group">'),O.push('<div class="tc-checklist-group-title">'+l(G)+"</div>"),F[G].forEach(function($){const H=o[$.id]||"",K=H?"is-"+H:"";O.push('<div class="tc-check-item '+K+'" data-id="'+l($.id)+'"><div class="tc-check-id">'+l($.id)+'</div><div class="tc-check-desc">'+l($.desc)+'</div><div class="tc-check-actions">'+b($.id,"pass",H)+b($.id,"fail",H)+b($.id,"skip",H)+"</div></div>")}),O.push("</div>")}),T.innerHTML=O.join("")}function b(T,F,O){const G=O===F,$={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},H={pass:c("tc-status-pass","通过"),fail:c("tc-status-fail","失败"),skip:c("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(G?"is-active "+F:"")+'" data-id="'+l(T)+'" data-kind="'+F+'" title="'+l(H[F])+'">'+$[F]+"</button>"}function h(T){return s==="all"?!0:s==="js_error"?T.type==="js_error"||T.type==="promise_error":s==="api"?T.type==="api_error"||T.type==="api_fail":s==="api_slow"?T.type==="api_slow":s==="console"?T.type==="console_error"||T.type==="console_warn":!0}function E(){const T=document.getElementById("tc-logs-body"),F=document.getElementById("tc-logs-count");if(!T)return;const O=(window._pearnlyTcLogs||[]).slice().reverse(),G=O.filter(h);if(F&&(F.textContent=String(O.length)),G.length===0){T.innerHTML='<div class="tc-logs-empty">'+l(c("tc-logs-empty","暂无异常"))+"</div>";return}const $=G.slice(0,100).map(function(H){const K=typeof H.detail=="object"?JSON.stringify(H.detail,null,2):String(H.detail||"");return'<div class="tc-log-item t-'+l(H.type)+'" data-ts="'+H.ts+'"><span class="tc-log-time">'+u(H.ts)+'</span><span class="tc-log-type">'+l(H.type)+'</span><div class="tc-log-summary">'+l(H.summary)+'<div class="tc-log-detail">'+l(K)+"</div></div></div>"}).join("");T.innerHTML=$,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(H){H.classList.toggle("active",H.getAttribute("data-filter")===s)})}function y(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&E(),_()},200))}window._tcOnNewLog=y;function _(){const T=document.getElementById("nav-test-badge");if(!T)return;const F=(window._pearnlyTcLogs||[]).filter(function(O){return O.type==="js_error"||O.type==="promise_error"||O.type==="api_error"||O.type==="api_fail"||O.type==="console_error"}).length;F>0?(T.style.display="",T.textContent=F>99?"99+":String(F)):T.style.display="none"}function k(){w(),g(),E(),_()}function x(){const T=[],F=new Date,O=_userInfo&&(_userInfo.email||_userInfo.username)||"—";T.push("# Pearnly "+e+" 测试结果"),T.push("- 账号:"+O),T.push("- 时间:"+F.toISOString().replace("T"," ").slice(0,19));const G=a.length,$=a.filter(function(Q){return o[Q.id]==="pass"}).length,H=a.filter(function(Q){return o[Q.id]==="fail"}).length,K=a.filter(function(Q){return o[Q.id]==="skip"}).length,ae=G-$-H-K;T.push("- 进度:"+($+H+K)+" / "+G+" · ✅ "+$+" · ❌ "+H+" · ⏭ "+K+" · 未测 "+ae),T.push(""),T.push("| ID | 描述 | 状态 |"),T.push("|---|---|---|"),a.forEach(function(Q){const le=o[Q.id],pe=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";T.push("| "+Q.id+" | "+Q.desc.replace(/\|/g,"\\|")+" | "+pe+" |")});const ne=a.filter(function(Q){return o[Q.id]==="fail"});ne.length>0&&(T.push(""),T.push("## ❌ 失败项"),ne.forEach(function(Q){T.push("- **"+Q.id+"** · "+Q.desc)}));const de=(window._pearnlyTcLogs||[]).slice(-30).reverse();return de.length>0&&(T.push(""),T.push("## 🔴 异常日志(最近 "+de.length+" 条)"),de.forEach(function(Q){if(T.push("- `"+u(Q.ts)+"` · **"+Q.type+"** · "+Q.summary),Q.detail){let le;try{le=JSON.stringify(Q.detail)}catch{le=String(Q.detail)}le&&le!=="{}"&&T.push("  - "+le.slice(0,600))}})),T.join(`
`)}function B(T){const F=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(F.length===0)return"(暂无异常日志)";const O=["# Pearnly 异常日志(最近 "+F.length+" 条)"],G=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return O.push("- 账号:"+G),O.push("- 当前页:"+(currentRoute||"?")),O.push("- UA:"+navigator.userAgent),O.push(""),F.forEach(function($){if(O.push("## `"+u($.ts)+"` · "+$.type),O.push("- "+$.summary),$.detail){O.push("```");try{O.push(JSON.stringify($.detail,null,2).slice(0,2e3))}catch{O.push(String($.detail).slice(0,2e3))}O.push("```")}}),O.join(`
`)}function L(){const T=Date.now();fetch("/api/health").then(function(F){const O=Date.now()-T;F.ok?d(c("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:O}),"success"):d(c("tc-toast-health-fail","后端无响应")+" ("+F.status+")","error")}).catch(function(){d(c("tc-toast-health-fail","后端无响应"),"error")})}function I(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}k(),d(c("tc-toast-cleared","session 状态已清空"),"success")}function C(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(T){return T.json()}).then(function(T){window._clientsCache=T.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),d("客户缓存已刷新 · "+(T.clients||[]).length+" 个客户","success")}).catch(function(){d("刷新失败","error")})}catch{}}function S(){if(i||!document.getElementById("page-test-center"))return;i=!0;const F=document.getElementById("tc-checklist-body");F&&F.addEventListener("click",function(le){const pe=le.target.closest(".tc-status-btn");if(!pe)return;const jt=pe.getAttribute("data-id"),un=pe.getAttribute("data-kind");!jt||!un||(o[jt]===un?delete o[jt]:o[jt]=un,p(),g(),w())});const O=document.getElementById("tc-btn-reset-checklist");O&&O.addEventListener("click",function(){o={},p(),g(),w()});const G=document.getElementById("tc-btn-copy-all");G&&G.addEventListener("click",function(){f(x())});const $=document.getElementById("tc-btn-copy-logs");$&&$.addEventListener("click",function(){f(B())});const H=document.getElementById("tc-btn-clear-logs");H&&H.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,E(),_()});const K=document.getElementById("tc-logs-filter");K&&K.addEventListener("click",function(le){const pe=le.target.closest(".tc-filter-chip");pe&&(s=pe.getAttribute("data-filter")||"all",E())});const ae=document.getElementById("tc-logs-body");ae&&ae.addEventListener("click",function(le){const pe=le.target.closest(".tc-log-item");pe&&pe.classList.toggle("expanded")});const ne=document.getElementById("tc-tool-health");ne&&ne.addEventListener("click",L);const de=document.getElementById("tc-tool-clear-session");de&&de.addEventListener("click",I);const Q=document.getElementById("tc-tool-reload-clients");Q&&Q.addEventListener("click",C)}function q(){}window._tcApplyVisibility=q;let A=0;const V=setInterval(function(){A++,_userInfo&&clearInterval(V),A>60&&clearInterval(V)},500);window.loadTestCenterPage=function(){m(),S(),k()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){_(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&k()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(h,E){if(typeof window.t=="function"){const y=window.t(h);if(y&&y!==h)return y}return E}function o(){const h=window._userInfo||{},E=String(h.role||"").toLowerCase(),y=String(h.tenant_role||"").toLowerCase();return h.is_super_admin===!0||h.is_owner===!0||E==="owner"||E==="admin"||y==="owner"||y==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const h=localStorage.getItem(e);if(!h||h==="null"||h==="0"||h==="")return null;const E=parseInt(h,10);return isNaN(E)?null:E}function r(h){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:h,mode:s()}}))}catch{}}function c(h){const E=i();h==null||h===0?localStorage.removeItem(e):(localStorage.setItem(e,String(h)),localStorage.setItem(n,"client")),String(E)!==String(h)&&r(h)}function m(){const h=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),h!=null&&r(null)}async function p(){try{const h=window.apiGet;if(typeof h!="function")return[];const E=await h("/api/workspace/clients");return E&&(E.clients||E.items)||[]}catch{return[]}}async function u(h){if(s()==="client"&&i()!=null)return typeof h=="function"&&h(),!0;const E=a("ws-need-client","这个功能需要先选择工作空间"),y=a("ws-btn-pick","选择工作空间"),_=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(E,{okText:y,cancelText:_})&&l(h):window.confirm(E+`

[`+y+" / "+_+"]")&&l(h),!1}async function l(h){const E=await p();if(typeof h=="function"&&s()!=="personal"&&E.length===1){c(Number(E[0].id)),h();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:E,canCreate:o(),active:i(),onPersonal:m,onPick:function(y){c(Number(y)),typeof h=="function"&&h()},emptyHint:E.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!E.length){const y=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(y,"info")}}function d(h){const E=h||document.getElementById("workspace-switcher-root");if(!E)return;const y=s(),_=i();let k,x;if(y==="client"&&_!=null){const I=(window._workspaceClientsCache||[]).find(C=>Number(C.id)===Number(_));k=v("building"),x=I?I.name:a("ws-current-label","当前工作空间")}else k=v("user"),x=a("ws-personal","个人事务");E.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+k+'<span class="ws-ctrl-label">'+f(x)+"</span></button>";const B=E.querySelector("#ws-ctrl-btn");B&&B.addEventListener("click",()=>l(null))}function f(h){return String(h??"").replace(/[&<>"']/g,function(E){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[E]})}function v(h){const E='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return h==="building"?E+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':E+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function w(h){h=h||{};const E=h.clients||[],y=h.active,_=document.getElementById("ws-modal");_&&_.remove();const k=document.createElement("div");k.id="ws-modal",k.className="ws-modal";const B='<button type="button" class="ws-modal-item'+(s()==="personal"||y==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+v("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+f(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+f(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let L="";if(E.length){const A=['<option value="">'+f(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(E.map(function(V){const T=y!=null&&Number(y)===Number(V.id);return'<option value="'+f(V.id)+'"'+(T?" selected":"")+">"+f(V.name||"#"+V.id)+"</option>"}));L='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+f(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+A.join("")+"</select></div>"}const I=!E.length&&h.emptyHint?'<div class="ws-modal-empty">'+f(h.emptyHint)+"</div>":"",C=h.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+f(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+f(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+f(a("ws-create-submit","创建"))+"</button></div></div>":"";k.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+f(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+f(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+B+L+"</div>"+I+C+"</div>",document.body.appendChild(k);const S=k.querySelector("[data-ws-select]");S&&S.addEventListener("change",function(){const A=S.value;A&&(typeof h.onPick=="function"&&h.onPick(A),q(),d())});function q(){k.remove()}k.addEventListener("click",function(A){if(A.target===k||A.target.closest("[data-ws-close]")){q();return}if(A.target.closest("[data-ws-personal]")){typeof h.onPersonal=="function"&&h.onPersonal(),q(),d();return}const T=A.target.closest("[data-ws-pick]");if(T){const G=T.getAttribute("data-ws-pick");typeof h.onPick=="function"&&h.onPick(G),q(),d();return}if(A.target.closest("[data-ws-create-toggle]")){const G=k.querySelector("[data-ws-create-form]");if(G){G.style.display=G.style.display==="none"?"flex":"none";const $=G.querySelector("[data-ws-create-name]");$&&$.focus()}return}if(A.target.closest("[data-ws-create-submit]")){g(k,h,q);return}})}async function g(h,E,y){const _=h.querySelector("[data-ws-create-name]"),k=_?(_.value||"").trim():"";if(!k){_&&_.focus();return}let x=null;try{if(typeof window.apiPost=="function"){const L=await window.apiPost("/api/workspace/clients",{name:k});x=L&&typeof L.json=="function"?await L.json().catch(()=>null):L}}catch{x=null}const B=x&&(x.id||x.client&&x.client.id);if(!B){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await p(),c(Number(B)),E.onPick,y(),d()}window.openWorkspaceChooserUI=w,window.addEventListener("pearnly:workspace-changed",function(){d()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=c,window.enterPersonalMode=m,window.requireWorkspace=u,window.openWorkspaceChooser=l,window.renderWorkspaceControl=d,window.fetchWorkspaceClients=p;function b(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){l(null)},800)}catch{}}p().then(h=>{window._workspaceClientsCache=h,d(),b()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",d)})();(function(){const e=y=>document.querySelector('[data-num-target="'+y+'"]');function n(y){if(!y)return t("reconcile-last-activity-none");try{const _=new Date(y),k=new Date,x=k-_;if(x/6e4<5)return t("reconcile-last-activity-just-now");if(_.toDateString()===k.toDateString())return t("reconcile-last-activity-today");const L=Math.max(1,Math.floor(x/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",L)}catch{return t("reconcile-last-activity-none")}}function a(y,_,k){const x=e(y);x&&(x.textContent=k?"-":String(_),x.classList.toggle("is-empty",!!k))}function o(y){const _=document.getElementById("reconcile-error");_&&(_.style.display=y?"flex":"none")}function s(y){const _=document.getElementById("reconcile-empty");_&&(_.style.display=y?"flex":"none")}function i(y,_){const k=document.getElementById("reconcile-last-activity");k&&(k.textContent=y,k.classList.toggle("has-data",!!_))}function r(y){const _=!y||(y.total_sessions||0)===0;a("pending",y.pending||0,_),a("matched",y.matched||0,_),a("unmatched",y.unmatched||0,_),i(n(y.last_activity_at),!!y.last_activity_at),o(!1),s(_)}function c(y){const _=y.toUpperCase();return _==="KBANK"?"bank-chip-kbank":_==="SCB"?"bank-chip-scb":_==="BBL"?"bank-chip-bbl":_==="KTB"?"bank-chip-ktb":_==="TTB"?"bank-chip-ttb":"bank-chip-other"}function m(y,_){const k=x=>x?String(x).slice(0,10):"?";return!y&&!_?"":k(y)+" ~ "+k(_)}function p(y){return y==null?"":String(y).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function u(y){const _=document.getElementById("reconcile-recent"),k=document.getElementById("reconcile-recent-list");if(!_||!k)return;const x=(y||[]).slice(0,20);if(x.length===0){_.style.display="none";return}_.style.display="",s(!1),k.innerHTML=x.map(B=>{const L=B.parse_status==="parse_failed",I=B.bank_code||"OTHER",C=B.account_last4?" ···"+p(B.account_last4):"",S=m(B.period_start,B.period_end),q=p(B.source_filename||""),A=Number(B.tx_count||0),V=L?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",A)+"</span>";return'<div class="recon-card" data-session-id="'+p(B.id)+'" data-session-name="'+q+'"><span class="bank-chip '+c(I)+'">'+p(I)+'</span><div class="recon-card-main"><div class="recon-card-title">'+q+C+'</div><div class="recon-card-sub">'+p(S)+'</div></div><div class="recon-card-right">'+V+'</div><button class="recon-card-trash" data-trash="'+p(B.id)+'" title="'+p(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),k.querySelectorAll(".recon-card").forEach(B=>{B.addEventListener("click",L=>{L.target.closest(".recon-card-trash")||(B.dataset.sessionId,l())})}),k.querySelectorAll(".recon-card-trash").forEach(B=>{B.addEventListener("click",L=>{L.stopPropagation();const I=B.dataset.trash,C=B.closest(".recon-card"),S=C&&C.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(I,S)})})}function l(y){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const _=document.querySelector('[data-recon-tab="bank"]');_&&_.click()},150)}function d(){o(!0),s(!1)}function f(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const y=document.querySelector('[data-recon-tab="bank"]');y&&y.click()},150)}async function v(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),o(!1),s(!1);const y=document.getElementById("reconcile-recent");y&&(y.style.display="none");const _={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[k,x]=await Promise.all([fetch("/api/bank-recon/stats",{headers:_}),fetch("/api/bank-recon/sessions?limit=20",{headers:_})]);if(!k.ok)throw new Error("http "+k.status);const B=await k.json(),L=x.ok?await x.json():[];r(B||{}),u(L||[])}catch(k){console.warn("[reconcile] load failed",k),d()}}function w(y){if(!y||!y.length)return;const _="Bearer "+(localStorage.getItem("mrpilot_token")||"");let k=0;const x=y.length;Array.from(y).forEach(function(B){const L=new FormData;L.append("file",B,B.name);const I=new XMLHttpRequest;I.open("POST","/api/bank-recon/upload"),I.setRequestHeader("Authorization",_),I.onload=function(){k++;try{const C=JSON.parse(I.responseText);I.status===200&&C.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",C.tx_count),"success"):showToast(B.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(B.name+" "+(t("upload-failed")||"上传失败"),"error")}k===x&&setTimeout(v,600)},I.onerror=function(){k++,showToast(B.name+" "+(t("upload-failed")||"上传失败"),"error"),k===x&&setTimeout(v,600)},I.send(L)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function g(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const y=document.getElementById("reconcile-bank-file-input");y&&y.addEventListener("change",function(){w(this.files),this.value=""}),document.addEventListener("click",_=>{if(_.target.closest("#btn-reconcile-upload-top")||_.target.closest("#btn-reconcile-upload-empty")){f();return}if(_.target.closest("#btn-reconcile-retry")){v();return}if(_.target.closest("#btn-reconcile-dev-seed")){E();return}})}const b=["468b50c1-5593-4fd6-990d-515ce8085563"];function h(){const y=document.getElementById("btn-reconcile-dev-seed");if(!y)return;const _=typeof _userInfo<"u"?_userInfo:null,k=_&&_.id&&b.indexOf(String(_.id))>=0;y.style.display=k?"":"none"}async function E(){try{const y=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!y.ok)throw new Error("seed:"+y.status);const _=await y.json(),k=(t("reconcile-dev-seed-ok")||"").replace("{n}",_.tx_count||0);showToast(k,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const x=document.querySelector('[data-auto-tab="bank"]');x&&x.click(),_.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(_.session_id)},300)}catch(y){console.warn("[reconcile] dev seed failed",y),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){g(),h(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await v()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&v().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
    <div class="modal" style="max-width:480px">
        <div class="modal-head">
            <div class="modal-title">
                <span data-i18n="assign-modal-title">分配客户</span>
                <span class="modal-title-sub" id="assign-modal-target"></span>
            </div>
            <button type="button" class="modal-close" id="assign-modal-close" aria-label="Close">
                <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l8 8M14 6l-8 8" stroke-linecap="round"/></svg>
            </button>
        </div>
        <div class="modal-body">
            <div class="assign-modal-toolbar">
                <label class="assign-toolbar-checkbox">
                    <input type="checkbox" id="assign-select-all">
                    <span data-i18n="assign-select-all">全选</span>
                </label>
                <span class="assign-toolbar-count" id="assign-selected-count"></span>
            </div>
            <div class="assign-clients-list" id="assign-clients-list">
                <div class="assign-empty" data-i18n="assign-loading">加载中...</div>
            </div>
        </div>
        <div class="modal-foot">
            <button type="button" class="btn btn-ghost" id="assign-modal-cancel" data-i18n="assign-cancel">取消</button>
            <button type="button" class="btn btn-primary" id="assign-modal-save" data-i18n="assign-save">保存</button>
        </div>
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const v=a();if(v){if(!e.clients.length){v.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}v.innerHTML=e.clients.map(w=>{const g=String(w.id),b=e.selected.has(g)?"checked":"",h=escapeHtml(w.name||w.label||"#"+g),E=w.code?'<span class="assign-row-code">'+escapeHtml(w.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(g)+'" '+b+'><span class="assign-row-name">'+h+"</span>"+E+"</label>"}).join(""),c()}}function c(){const v=s();if(v){const g=t("assign-selected-count")||"已选 {n} / {total}";v.textContent=g.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const w=o();w&&(w.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function m(){const v=i();v&&(v.textContent=e.employeeName?" · "+e.employeeName:"")}async function p(v,w){e.employeeId=v,e.employeeName=w||"",e.opened=!0,e.selected=new Set,e.clients=[],m();const g=a();g&&(g.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const b=n();b&&(b.style.display="flex");try{const[h,E]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(v)+"/assignments")]);e.clients=h&&h.clients||[];const y=E&&E.client_ids||[];e.selected=new Set(y.map(String)),r()}catch(h){console.error("[assign-clients] load failed",h);const E=a();E&&(E.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function u(){e.opened=!1;const v=n();v&&(v.style.display="none")}async function l(){if(!e.employeeId)return;const v=Array.from(e.selected).map(g=>parseInt(g,10)).filter(g=>!isNaN(g)),w=document.getElementById("assign-modal-save");w&&(w.disabled=!0);try{const g=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:v});g&&g.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",v.length),"success"),u(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(g){console.error("[assign-clients] save failed",g),showToast(t("assign-save-failed")||"保存失败","error")}finally{w&&(w.disabled=!1)}}function d(){const v=n();if(!v||v.dataset.bound==="1")return;v.dataset.bound="1";const w=document.getElementById("assign-modal-close");w&&w.addEventListener("click",u);const g=document.getElementById("assign-modal-cancel");g&&g.addEventListener("click",u);const b=document.getElementById("assign-modal-save");b&&b.addEventListener("click",l),v.addEventListener("click",function(y){y.target===v&&u()});const h=o();h&&h.addEventListener("change",function(){h.checked?e.selected=new Set(e.clients.map(y=>String(y.id))):e.selected=new Set,r()});const E=a();E&&E.addEventListener("change",function(y){const _=y.target.closest('input[type="checkbox"][data-cid]');if(!_)return;const k=_.dataset.cid;_.checked?e.selected.add(k):e.selected.delete(k),c()})}function f(){e.opened&&(m(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",f),window.openAssignClientsModal=function(v,w){d(),p(v,w)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(u){if(!u)return"";try{return new Date(u).toLocaleString()}catch{return u}}function a(u){const l=document.getElementById("access-log-table");l&&(l.innerHTML='<div class="access-log-empty">'+escapeHtml(u)+"</div>");const d=document.getElementById("access-log-pager");d&&(d.innerHTML="")}function o(){const u=document.getElementById("access-log-table");if(!u)return;const l=e.rows||[];if(!l.length){a(t("set-access-log-empty"));return}const d=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,f=l.map(function(v){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(v.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(v.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(v.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(v.target_name||v.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(v.ip||"-")}</div>
                </div>`}).join("");u.innerHTML=d+f}function s(){const u=document.getElementById("access-log-pager");if(!u)return;const l=e.total||0;if(!l){u.innerHTML="";return}const d=e.page||1,f=e.per_page,v=Math.max(1,Math.ceil(l/f)),w=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",l),g=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",d).replace("{t}",v);u.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(w)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${d-1}" ${d<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(g)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${d+1}" ${d>=v?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(u){const l=localStorage.getItem("mrpilot_token");if(l){e.page=u||1,a(t("set-access-log-loading"));try{const d="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),f=await fetch(d,{headers:{Authorization:"Bearer "+l}});if(f.status===403){a(t("set-access-log-empty"));return}if(!f.ok)throw new Error("http_"+f.status);const v=await f.json();e.rows=v.logs||[],e.total=v.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const u=localStorage.getItem("mrpilot_token");if(u)try{const l="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),d=await fetch(l,{headers:{Authorization:"Bearer "+u}});if(!d.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const f=await d.blob(),v=document.createElement("a"),w=URL.createObjectURL(f);v.href=w,v.download="pearnly_access_log.csv",document.body.appendChild(v),v.click(),setTimeout(function(){URL.revokeObjectURL(w),v.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function c(){const u=document.querySelectorAll(".set-tab-owner-only"),l=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));u.forEach(function(d){d.style.display=l?"":"none"})}document.addEventListener("click",function(u){if(u.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(u.target.closest("#access-log-csv-btn")){u.preventDefault(),r();return}const f=u.target.closest(".access-log-pager-btn[data-access-log-page]");if(f&&!f.disabled){const v=parseInt(f.dataset.accessLogPage,10);i(v)}}),document.addEventListener("input",function(u){u.target&&u.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(u.target.value||"").trim(),i(1)},350))});let m=0;const p=setInterval(function(){m++,_userInfo&&(c(),clearInterval(p)),m>60&&clearInterval(p)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){c(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="modal" style="max-width:520px;">
            <div class="modal-head">
                <div class="modal-title" data-i18n="notif-new-title">新建提醒规则</div>
                <button class="modal-close" id="notif-new-close" type="button" aria-label="close">×</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label" data-i18n="notif-new-template">触发场景</label>
                    <div class="notif-template-options">
                        <label class="notif-template-opt" data-tmpl="exception_high">
                            <input type="radio" name="notif-template" value="exception_high">
                            <div class="notif-template-card">
                                <div class="notif-template-name" data-i18n="notif-tmpl-exception-name">异常栏拦下高危单</div>
                                <div class="notif-template-desc" data-i18n="notif-tmpl-exception-desc">数学不自洽 / 重复发票 / 缺总额 等高严重度异常 · 自动推送</div>
                            </div>
                        </label>
                        <label class="notif-template-opt" data-tmpl="large_invoice">
                            <input type="radio" name="notif-template" value="large_invoice">
                            <div class="notif-template-card">
                                <div class="notif-template-name" data-i18n="notif-tmpl-large-name">单张发票超阈值</div>
                                <div class="notif-template-desc" data-i18n="notif-tmpl-large-desc">总金额 ≥ 你设的金额 · 立刻推 LINE</div>
                            </div>
                        </label>
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label" for="notif-new-name" data-i18n="notif-new-name-label">规则名称</label>
                    <input type="text" id="notif-new-name" class="form-input" maxlength="100" data-i18n-placeholder="notif-new-name-ph" placeholder="例:大额发票推老板">
                </div>

                <div class="form-group" id="notif-new-threshold-row" style="display:none;">
                    <label class="form-label" for="notif-new-threshold" data-i18n="notif-new-threshold-label">金额阈值(฿)</label>
                    <input type="number" id="notif-new-threshold" class="form-input" min="1" step="1" data-i18n-placeholder="notif-new-threshold-ph" placeholder="500000">
                    <div class="form-hint" data-i18n="notif-new-threshold-hint">总额 ≥ 此值 · 才推送</div>
                </div>

                <div id="notif-line-check" class="notif-line-check" style="display:none;"></div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="notif-new-cancel" type="button" data-i18n="btn-cancel">取消</button>
                <button class="btn btn-primary" id="notif-new-save" type="button" data-i18n="notif-new-save">保存规则</button>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=k=>document.getElementById(k);async function n(k,x){return await fetch(k,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(x||{})})}async function a(k){return await fetch(k,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function i(k,x){if(!k)return;k.style.display="",k.className="notif-line-check "+(x?"bound":"unbound");const B=x?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';k.innerHTML=B+"<span>"+escapeHtml(t(x?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(k){if(k==null)return"-";const x=Number(k);return isNaN(x)?String(k):"฿ "+x.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function c(k){if(!k)return"-";try{const x=new Date(k),B=(x.getMonth()+1).toString().padStart(2,"0"),L=x.getDate().toString().padStart(2,"0"),I=x.getHours().toString().padStart(2,"0"),C=x.getMinutes().toString().padStart(2,"0");return`${B}-${L} ${I}:${C}`}catch{return k}}function m(k){const x=e("notif-rules-list"),B=e("notif-rules-empty"),L=e("notif-rules-count");if(!(!x||!B)){if(L.textContent=String(k.length),L.className="auto-status-pill "+(k.length>0?"active":"none"),!k.length){B.style.display="",x.style.display="none",x.innerHTML="";return}B.style.display="none",x.style.display="",x.innerHTML=k.map(I=>{const C=I.template_code==="large_invoice",S=C?"notif-rule-large-tag":"notif-rule-exception-tag",q=C?"large":"";let A=[];if(C){const T=I.params&&I.params.threshold?r(I.params.threshold):"-";A.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+T)}I.enabled||A.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const V=A.length?A.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${I.enabled?"":" disabled"}" data-rule-id="${I.id}">
                    <span class="notif-rule-tmpl-badge ${q}">${escapeHtml(t(S))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(I.name)}</div>
                        <div class="notif-rule-meta">${V}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${I.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function p(k){const x=e("notif-logs-list");if(x){if(!k.length){x.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}x.innerHTML=k.map(B=>{const L=B.status==="sent",I=B.event_type==="exception_high"?"notif-event-exception-high":B.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",C=L?"":" · "+escapeHtml(B.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${L?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(I))}</div>
                        <div class="notif-log-meta">${escapeHtml(B.template_code||"-")}${C}</div>
                    </div>
                    <div class="notif-log-time">${c(B.sent_at)}</div>
                </div>`}).join("")}}async function u(){try{const k=await apiGet("/api/notifications/rules");l=k&&k.items||[],m(l)}catch(k){console.warn("load rules fail",k)}try{const k=await apiGet("/api/notifications/logs?limit=20");d=k&&k.items||[],p(d)}catch(k){console.warn("load logs fail",k)}}let l=null,d=null;function f(){l&&m(l),d&&p(d);const k=e("notif-new-modal");k&&k.style.display!=="none"&&o&&i(e("notif-line-check"),!!(o&&o.bound))}function v(){const k=e("notif-new-modal");k&&(k.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(x=>x.checked=!1),s().then(x=>i(e("notif-line-check"),!!(x&&x.bound))))}function w(){const k=e("notif-new-modal");k&&(k.style.display="none")}function g(){const k=document.querySelector('input[name="notif-template"]:checked'),x=e("notif-new-threshold-row");if(!k){x.style.display="none";return}x.style.display=k.value==="large_invoice"?"":"none";const B=e("notif-new-name");B&&!B.value.trim()&&(B.value=k.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function b(){const k=document.querySelector('input[name="notif-template"]:checked');if(!k){showToast(t("notif-new-template"),"error");return}const x=(e("notif-new-name").value||"").trim();if(!x){showToast(t("notif-name-required"),"error");return}const B={name:x,template_code:k.value,params:{},enabled:!0};if(k.value==="large_invoice"){const L=parseFloat(e("notif-new-threshold").value||"0");if(!L||L<=0){showToast(t("notif-threshold-required"),"error");return}B.params.threshold=L}try{const L=await apiPost("/api/notifications/rules",B);if(L&&L.ok)showToast(t("notif-toast-created"),"success"),w(),u();else{const I=await(L&&L.json&&L.json().catch(()=>({})))||{};showToast(I&&I.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function h(k,x,B){if(k==="toggle"){const L=B.classList.contains("on"),I=await n("/api/notifications/rules/"+x,{enabled:!L});I&&I.ok?(showToast(t(L?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),u()):showToast("toggle failed","error");return}if(k==="test"){const L=await s();if(!L||!L.bound){showToast(t("notif-line-error-bind-first"),"error");return}const I=await apiPost("/api/notifications/rules/"+x+"/test",{});if(I&&I.ok)showToast(t("notif-toast-test-sent"),"success"),u();else{const C=await(I&&I.json&&I.json().catch(()=>({})))||{},S=C&&C.detail||"";showToast(S||t("notif-toast-test-failed"),"error"),u()}return}if(k==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const I=await a("/api/notifications/rules/"+x);I&&I.ok?(showToast(t("notif-toast-deleted"),"success"),u()):showToast("delete failed","error");return}}let E=!1;function y(){if(E)return;E=!0;const k=e("notif-btn-new");k&&k.addEventListener("click",v);const x=e("notif-btn-refresh-logs");x&&x.addEventListener("click",u);const B=e("notif-new-close");B&&B.addEventListener("click",w);const L=e("notif-new-cancel");L&&L.addEventListener("click",w);const I=e("notif-new-save");I&&I.addEventListener("click",b),document.querySelectorAll('input[name="notif-template"]').forEach(q=>{q.addEventListener("change",g)});const C=e("notif-rules-list");C&&C.addEventListener("click",q=>{const A=q.target.closest("button[data-action]");if(!A)return;const V=A.closest("[data-rule-id]");V&&h(A.getAttribute("data-action"),V.getAttribute("data-rule-id"),A)});const S=e("notif-new-modal");S&&S.addEventListener("click",q=>{q.target===S&&w()})}async function _(){y(),await u()}window._loadNotificationsPanel=_,window._rerenderNotifications=f})();(function(){function n(b,h){try{return window.t&&window.t(b)||h}catch{return h}}function a(){var b="";try{b=localStorage.getItem("mrpilot_token")||""}catch{}return b?{Authorization:"Bearer "+b}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var b=document.createElement("style");b.id="recon-batch-style",b.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(b)}}function i(b){return b?b.dataset&&b.dataset.taskId?b.dataset.taskId:b.dataset&&b.dataset.taskid?b.dataset.taskid:"":""}function r(b){var h=document.getElementById(b.tbody);if(!h)return null;var E=h.closest("table");if(!E)return null;var y=E.querySelector("thead");if(!y)return null;if(y._reconReady)return y;var _=y.querySelector("tr");if(!_)return null;if(_.classList.add("recon-thead-default"),!_.querySelector(".recon-master-cb")){var k=document.createElement("th");k.className="recon-sel-cell";var x=document.createElement("input");x.type="checkbox",x.className="recon-master-cb",x.setAttribute("aria-label","select all"),x.addEventListener("change",function(){u(b,x.checked)}),k.appendChild(x),_.insertBefore(k,_.firstElementChild)}var B=_.children[1];B&&!B.classList.contains("recon-time-col")&&B.classList.add("recon-time-col");var L=_.children.length,I=document.createElement("tr");I.className="recon-thead-batch";var C=document.createElement("th");C.className="recon-sel-cell";var S=document.createElement("input");S.type="checkbox",S.className="recon-master-cb",S.checked=!0,S.setAttribute("aria-label","select all"),S.addEventListener("change",function(){u(b,S.checked)}),C.appendChild(S);var q=document.createElement("th");return q.setAttribute("colspan",String(L-1)),q.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',I.appendChild(C),I.appendChild(q),y.appendChild(I),q.querySelector("[data-recon-del]").addEventListener("click",function(){v(b)}),q.querySelector("[data-recon-clear]").addEventListener("click",function(){f(b)}),y._reconReady=!0,d(b),y}function c(b){var h=document.getElementById(b.tbody);if(h){var E=h.querySelectorAll("tr");E.forEach(function(y){var _=i(y);if(_&&!y.querySelector(".recon-sel-cb")){var k=y.querySelector("td");if(k){var x=document.createElement("td");x.className="recon-sel-cell";var B=document.createElement("input");B.type="checkbox",B.className="recon-sel-cb",B.dataset.taskId=_,B.dataset.kind=b.kind,B.addEventListener("click",function(I){I.stopPropagation()}),B.addEventListener("change",function(){l(b)}),x.appendChild(B),y.insertBefore(x,k);var L=y.children[1];L&&!L.classList.contains("recon-time-col")&&L.classList.add("recon-time-col")}}}),l(b)}}function m(b){var h=document.getElementById(b.tbody);return h?Array.prototype.slice.call(h.querySelectorAll(".recon-sel-cb")):[]}function p(b){return m(b).filter(function(h){return h.checked}).map(function(h){return h.dataset.taskId})}function u(b,h){m(b).forEach(function(E){E.checked=!!h}),l(b)}function l(b){var h=p(b),E=m(b),y=document.getElementById(b.tbody);if(y){var _=y.closest("table"),k=_&&_.querySelector("thead");if(k){h.length>0?k.classList.add("recon-batch-mode"):k.classList.remove("recon-batch-mode"),k.querySelectorAll(".recon-master-cb").forEach(function(B){if(E.length===0){B.checked=!1,B.indeterminate=!1;return}h.length===E.length?(B.checked=!0,B.indeterminate=!1):h.length===0?(B.checked=!1,B.indeterminate=!1):(B.checked=!1,B.indeterminate=!0)});var x=k.querySelector("[data-recon-count]");x&&(x.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",h.length))}}}function d(b){var h=document.getElementById(b.tbody);if(h){var E=h.closest("table"),y=E&&E.querySelector("thead");if(y){var _=y.querySelector("[data-recon-del-label]"),k=y.querySelector("[data-recon-clear]");_&&(_.textContent=n("recon-batch-delete","批量删除")),k&&(k.textContent=n("recon-batch-clear","取消")),l(b)}}}function f(b){m(b).forEach(function(h){h.checked=!1}),l(b)}async function v(b){var h=p(b);if(h.length){var E=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",h.length),y=!1;try{typeof window.pearnlyConfirm=="function"?y=await window.pearnlyConfirm(E,n("recon-batch-delete-title","批量删除")):y=window.confirm(E)}catch{y=!1}if(y)try{var _=Object.assign({"Content-Type":"application/json"},a()),k=b.kind==="glv"?h.map(function(I){return parseInt(I,10)}):h,x=await fetch(b.api,{method:"POST",headers:_,body:JSON.stringify({ids:k})});if(!x.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var B=await x.json(),L=B&&(B.deleted!=null?B.deleted:B.count)||h.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",L),"success"),b.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function w(b){r(b),c(b);var h=document.getElementById(b.tbody);if(!(!h||h._reconBatchWatched)){h._reconBatchWatched=!0;var E=new MutationObserver(function(){c(b)});E.observe(h,{childList:!0,subtree:!1})}}function g(){s(),o.forEach(w),document.querySelectorAll(".recon-batch-bar").forEach(function(b){try{b.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",g):g(),setTimeout(g,1500),setTimeout(g,4e3),document.addEventListener("keydown",function(b){b.key==="Escape"&&o.forEach(function(h){p(h).length>0&&f(h)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(d)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(p){};function i(p){n=p;for(let d=1;d<=a;d++){const f=document.getElementById("ob-step-"+d);f&&(f.style.display=d===p?"block":"none")}document.querySelectorAll(".ob-dot").forEach(d=>{const f=parseInt(d.dataset.step,10);d.classList.toggle("active",f===p),d.classList.toggle("done",f<p)});const u=document.getElementById("ob-step-label");u&&(u.textContent=p+" / "+a);const l=document.getElementById("ob-next");if(l&&(l.textContent=p===a?t("ob-finish"):t("ob-next")),p===4){const d=document.getElementById("ob-line-input");d&&(d.value=e.line_id||"")}}function r(p){const u=document.querySelector(".onboarding-modal");if(!u)return;let l=u.querySelector(".ob-feedback");l||(l=document.createElement("div"),l.className="ob-feedback",u.appendChild(l)),l.textContent=p,l.classList.add("show"),setTimeout(()=>l.classList.remove("show"),1800)}document.addEventListener("click",p=>{const u=p.target.closest(".ob-option");if(!u)return;const l=u.parentElement;if(!l||!l.classList.contains("ob-options"))return;l.querySelectorAll(".ob-option").forEach(f=>f.classList.remove("selected")),u.classList.add("selected");const d=u.dataset.value;l.id==="ob-role-options"?e.role=d:l.id==="ob-volume-options"?e.monthly_volume=d:l.id==="ob-country-options"&&(e.country=d)}),document.addEventListener("click",p=>{p.target.id==="ob-skip"&&c()}),document.addEventListener("click",p=>{if(p.target.id==="ob-next"){if(n===4){const u=document.getElementById("ob-line-input");e.line_id=(u&&u.value||"").trim().replace(/^@+/,"")}c()}}),document.addEventListener("click",p=>{if(p.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const u=document.getElementById("onboarding-modal");u&&(u.style.display="none")}});function c(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):m()}async function m(){const p=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const u={};if(e.role&&(u.role=e.role),e.monthly_volume&&(u.monthly_volume=e.monthly_volume),e.country&&(u.country=e.country),e.line_id&&(u.line_id=e.line_id),Object.keys(u).length===0){p&&(p.style.display="none");return}try{const l=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(u)});l.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,u),setTimeout(()=>{p&&(p.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(u)),console.warn("onboarding profile save failed",l.status),r(t("ob-fb-saved-local")),setTimeout(()=>{p&&(p.style.display="none")},1500))}catch(l){console.error("onboarding submit",l),localStorage.setItem("pilot_ob_pending",JSON.stringify(u)),p&&(p.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="modal modal-lg">
            <div class="modal-head">
                <div class="modal-title" data-i18n="settings-archive">归档命名</div>
                <button class="modal-close" id="archive-rule-modal-close" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body">
                <div id="archive-editor-card">
                    <div class="archive-editor-desc" data-i18n="archive-editor-desc">自定义识别后文件的命名规则和归档文件夹结构</div>
                    <!-- 当前规则 -->
                    <div class="archive-section">
                        <div class="archive-section-label" data-i18n="archive-current-rule">当前规则(点字段编辑 · 拖拽排序)</div>
                        <div class="archive-rule-canvas" id="archive-rule-canvas"></div>
                    </div>
                    <!-- 可添加的字段 -->
                    <div class="archive-section">
                        <div class="archive-section-label" data-i18n="archive-add-field">添加字段(点击加入规则)</div>
                        <div class="archive-field-palette" id="archive-field-palette"></div>
                    </div>
                    <!-- 实时预览 -->
                    <div class="archive-section">
                        <div class="archive-section-label" data-i18n="archive-preview">实时预览</div>
                        <div class="archive-preview-box">
                            <code id="archive-preview-name">-</code>
                            <div class="archive-preview-hint" id="archive-preview-hint"></div>
                        </div>
                    </div>
                    <!-- 文件夹策略 -->
                    <div class="archive-section">
                        <div class="archive-section-label" data-i18n="archive-folder-strategy">文件夹策略(批量下载 ZIP 时生效)</div>
                        <div class="archive-folder-options" id="archive-folder-options">
                            <label class="radio-opt"><input type="radio" name="folder-strategy" value="none"><span data-i18n="folder-strategy-none">不分文件夹</span></label>
                            <label class="radio-opt"><input type="radio" name="folder-strategy" value="by_month"><span data-i18n="folder-strategy-month">按月份(2026-04/)</span></label>
                            <label class="radio-opt"><input type="radio" name="folder-strategy" value="by_seller"><span data-i18n="folder-strategy-seller">按供应商(DHL/)</span></label>
                            <label class="radio-opt"><input type="radio" name="folder-strategy" value="by_month_seller"><span data-i18n="folder-strategy-both">按月份+供应商(2026-04/DHL/)</span></label>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="btn-archive-reset" data-i18n="archive-reset">恢复默认</button>
                <button class="btn btn-primary" id="btn-archive-save" data-i18n="archive-save">保存</button>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("archive-token-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="modal" style="max-width:420px;">
            <div class="modal-head">
                <div class="modal-title" data-i18n="archive-token-title">编辑字段</div>
                <button class="modal-close" id="archive-token-close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body" id="archive-token-body"></div>
            <div class="modal-foot">
                <button class="btn btn-danger btn-ghost" id="btn-archive-token-delete" data-i18n="archive-token-delete">删除此字段</button>
                <button class="btn btn-primary" id="btn-archive-token-ok" data-i18n="archive-token-ok">确定</button>
            </div>
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function c(){return"DHL Express (Thailand) Co., Ltd."}function m(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:c(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadArchiveSettings=()=>p();async function p(){const y=!!(_userInfo&&_userInfo.can_customize_archive);o=!y;const _=document.getElementById("archive-upgrade-banner");_&&(_.style.display=y?"none":"");const k=document.getElementById("archive-plus-badge");k&&(k.style.display=y?"none":"");try{const x=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!x.ok)throw new Error("load failed");const B=await x.json();e=Array.isArray(B.name_template)?B.name_template:[],n=B.folder_strategy||"by_month_seller"}catch(x){console.error("load archive settings failed",x),showToast(t("archive-load-failed"),"error");return}u(),l(),d(),f()}function u(){const y=document.getElementById("archive-rule-canvas");if(y){if(e.length===0){y.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}y.innerHTML=e.map((_,k)=>{const x=i[_.type]||{label:_.type},B=s[_.type]||"",L=_.type==="sep"?`"${escapeHtml(_.val||"_")}"`:escapeHtml(t(x.label));return`
                <span class="archive-token ${_.type}"
                      data-token-idx="${k}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${B}</span>
                    <span class="token-label">${L}</span>
                </span>
            `}).join("")}}function l(){const y=document.getElementById("archive-field-palette");if(!y)return;const _=["date","seller","category","amount","invoice","buyer","sep"];y.innerHTML=_.map(k=>{const x=i[k],B=s[k]||"";return`
                <button class="archive-palette-btn ${k}" data-add-field="${k}" ${o?"disabled":""}>
                    <span class="token-icon">${B}</span>
                    <span>${escapeHtml(t(x.label))}</span>
                </button>
            `}).join("")}function d(){document.querySelectorAll('input[name="folder-strategy"]').forEach(y=>{y.checked=y.value===n,y.disabled=o})}async function f(){const y=document.getElementById("archive-preview-name"),_=document.getElementById("archive-preview-hint");if(_&&(_.textContent=t("archive-preview-hint",{category:r()})),!!y){if(e.length===0){y.textContent="-";return}try{const x=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:m().merged_fields,name_template:e})})).json();y.textContent=(x.name||"-")+".pdf"}catch{y.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const y=document.getElementById("archive-rule-modal");!y||y.style.display==="none"||(u(),l(),f())};let v=-1;document.addEventListener("dragstart",y=>{const _=y.target.closest(".archive-token");!_||o||(v=parseInt(_.dataset.tokenIdx,10),_.classList.add("dragging"),y.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",y=>{document.querySelectorAll(".archive-token").forEach(_=>_.classList.remove("dragging","drop-target")),v=-1}),document.addEventListener("dragover",y=>{const _=y.target.closest(".archive-token");_&&(y.preventDefault(),y.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(k=>k.classList.remove("drop-target")),_.classList.add("drop-target"))}),document.addEventListener("drop",y=>{const _=y.target.closest(".archive-token");if(!_||v<0||o)return;y.preventDefault();const k=parseInt(_.dataset.tokenIdx,10);if(k===v)return;const x=e.splice(v,1)[0];e.splice(k,0,x),v=-1,u(),f()}),document.addEventListener("click",y=>{if(y.target.closest("#btn-open-archive-rule")||y.target.closest("#btn-open-archive-rule-from-settings")){const B=document.getElementById("archive-rule-modal");B&&(B.style.display="",p());return}if(y.target.closest("#archive-rule-modal-close")||y.target.id==="archive-rule-modal"){const B=document.getElementById("archive-rule-modal");B&&(B.style.display="none");return}const _=y.target.closest(".settings-nav-item");if(_){switchSettingsTab(_.dataset.settingsTab);return}if(o&&y.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const k=y.target.closest("[data-add-field]");if(k){const B=k.dataset.addField,L=i[B],I={type:B,...L.defaultCfg};e.push(I),u(),f();return}const x=y.target.closest(".archive-token");if(x&&!o){w(parseInt(x.dataset.tokenIdx,10));return}if(y.target.closest("#btn-archive-save"))return h();if(y.target.closest("#btn-archive-reset"))return E();(y.target.closest("#archive-token-close")||y.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),y.target.closest("#btn-archive-token-ok")&&g(),y.target.closest("#btn-archive-token-delete")&&b()}),document.addEventListener("change",y=>{y.target.name==="folder-strategy"&&(n=y.target.value)});function w(y){a=y;const _=e[y];if(!_)return;const k=document.getElementById("archive-token-body");let x="";_.type==="date"?x=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${_.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${_.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${_.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${_.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:_.type==="seller"?x=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${_.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:_.type==="amount"?x=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${_.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:_.type==="sep"?x=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${_.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${_.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${_.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(_.val)?"":escapeHtml(_.val||"")}">
                    </div>
                </div>`:x=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,k.innerHTML=x,document.getElementById("archive-token-modal").style.display="",k.querySelectorAll(".sep-chip").forEach(B=>{B.addEventListener("click",()=>{k.querySelectorAll(".sep-chip").forEach(I=>I.classList.remove("active")),B.classList.add("active");const L=document.getElementById("token-sep-custom");L&&(L.value="")})})}function g(){const y=e[a];if(y){if(y.type==="date")y.format=document.getElementById("token-date-format").value;else if(y.type==="seller")y.short=document.getElementById("token-seller-short").checked;else if(y.type==="amount")y.with_currency=document.getElementById("token-amount-currency").checked;else if(y.type==="sep"){const _=document.querySelector("#archive-token-body .sep-chip.active"),k=document.getElementById("token-sep-custom").value;y.val=k||(_?_.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",u(),f()}}function b(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",u(),f())}async function h(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const _=document.getElementById("archive-rule-modal");_&&(_.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function E(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",u(),d(),f())}})();(function(){window.loadAboutPanel=()=>e(),window.loadPrefsSettings=()=>n();function e(){const o=document.getElementById("settings-contact-grid");if(!o)return;const s=_contact?.phone||"086-889-2228",i=_contact?.line_id||"@Pearnly",r=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",c=_contact?.email||"hello@pearnly.com",m=_contact?.address||"Bangkok, Thailand";o.innerHTML=`
            <a class="contact-item" href="${escapeHtml(r)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(i)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(c)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(c)}</div>
                </div>
            </a>
            <a class="contact-item" href="tel:${escapeHtml(s.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(s)}</div>
                </div>
            </a>
            <div class="contact-item">
                <div class="contact-icon address">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s-7-7.5-7-13a7 7 0 1114 0c0 5.5-7 13-7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-address"))}</div>
                    <div class="contact-value">${escapeHtml(m)}</div>
                </div>
            </div>
        `}async function n(){try{const o=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!o.ok)return;const s=await o.json(),i=document.getElementById("pref-dup-check");i&&(i.checked=!!s.enabled)}catch(o){console.warn("load prefs failed",o)}}const a=document.getElementById("pref-dup-check");a&&!a.dataset.bound&&(a.dataset.bound="1",a.addEventListener("change",async o=>{const s=o.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:s})})).ok?showToast(s?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(o.target.checked=!s,showToast(t("pref-save-failed"),"error"))}catch{o.target.checked=!s,showToast(t("pref-save-failed"),"error")}}))})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,i=null,r=0,c=0,m=!1;function p(h){const E=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return h.preventDefault(),h.returnValue=E,E}function u(){m||(m=!0,window.addEventListener("beforeunload",p))}function l(){m&&(m=!1,window.removeEventListener("beforeunload",p))}function d(){if(document.getElementById("big-batch-progress"))return;const h=document.getElementById("file-list");if(!h||!h.parentNode)return;const E=document.createElement("div");E.id="big-batch-progress",E.className="big-batch-progress",E.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',h.parentNode.insertBefore(E,h);const y=document.getElementById("bbp-text");y&&(y.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function f(){const h=document.getElementById("big-batch-progress");h&&h.remove()}function v(){if(!i)return;let h=0;for(let I=0;I<i.length;I++){const C=i[I].status;(C==="success"||C==="error"||C==="cancelled")&&h++}const E=r,y=E>0?Math.min(100,Math.floor(100*h/E)):0,_=(Date.now()-c)/1e3;let k;if(h>=3&&_>1){const I=_/h;k=(E-h)*I}else k=(E-h)*6/6;const x=Math.max(1,Math.ceil(k/60)),B=document.getElementById("bbp-fill"),L=document.getElementById("bbp-text");B&&(B.style.width=y+"%"),L&&(h>=E?L.textContent=t("big-batch-progress-done").replace("{total}",E):L.textContent=t("big-batch-progress-running").replace("{done}",h).replace("{total}",E).replace("{min}",x))}function w(h){try{if(localStorage.getItem(o)==="1")return}catch{}const E=Math.max(1,Math.ceil(h*6/6/60)),y=t("big-batch-first-tip").replace("{n}",h).replace("{min}",E);typeof showToast=="function"&&showToast(y,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function g(h){!h||h.length<100||(i=h,r=h.length,c=Date.now(),d(),u(),w(r),s&&clearInterval(s),s=setInterval(v,250),v())}function b(){s&&(clearInterval(s),s=null),l(),i&&r>=100?(v(),setTimeout(f,1200)):f(),i=null,r=0}window._bigBatchStart=g,window._bigBatchStop=b,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&v()})})();const ue={status:null,statusLoaded:!1,bound:!1};function ce(e){return typeof escapeHtml=="function"?escapeHtml(e==null?"":String(e)):String(e??"")}function me(e,n){try{typeof showToast=="function"&&showToast(e,n||"info")}catch{}}function pa(){const e=typeof _userInfo<"u"?_userInfo:null;return!!(e&&(e.role==="owner"||e.is_super_admin))}function co(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function bi(e){if(!e)return!1;const n=String(e.status||"").toLowerCase();return n==="exception"||n==="exception_pending"||n==="rejected"}async function Xe(e){if(ue.statusLoaded&&!e)return ue.status;const n=localStorage.getItem("mrpilot_token");if(!n)return null;try{const a=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+n}});if(!a.ok)throw new Error("http_"+a.status);ue.status=await a.json(),ue.statusLoaded=!0}catch{ue.status={configured:!1,connected:!1,organisations:[]},ue.statusLoaded=!1}return ue.status}async function yi(){const e=document.getElementById("drawer-history-save");if(!e||e.querySelector("#btn-xero-push")||e.querySelector("#pn-push-wrap")||(await Xe(!1),e.querySelector("#pn-push-wrap"))||e.querySelector("#btn-xero-push"))return;const n=co();if(!(n&&(n._historyId||n.history_id)))return;let o=!1,s="xero-push-tip";!ue.status||!ue.status.configured?(o=!0,s="xero-err-not_configured"):ue.status.connected?bi(n)&&(o=!0,s="xero-push-disabled-exc"):(o=!0,s="xero-push-disabled-no-conn");const i=document.createElement("button");i.type="button",i.id="btn-xero-push",i.className="btn btn-ghost"+(o?" disabled":""),i.disabled=o,i.title=t(s)||"",i.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+ce(t("xero-push-btn"))+"</span>",i.addEventListener("click",wi);const r=document.getElementById("btn-push-erp");r&&r.parentNode?r.parentNode.insertBefore(i,r.nextSibling):e.insertBefore(i,e.firstChild)}async function wi(){const e=co(),n=e&&(e._historyId||e.history_id);if(!n)return;const a=document.getElementById("btn-xero-push");a&&(a.disabled=!0,a.classList.add("loading"));const o=localStorage.getItem("mrpilot_token");try{const s=await fetch("/api/erp/xero/push/"+encodeURIComponent(n),{method:"POST",headers:{Authorization:"Bearer "+o}});if(!s.ok){let i="unknown";try{i=(await s.json()).detail||"unknown"}catch{}const r=String(i).replace(/^xero\./,"").toLowerCase(),c=t("xero-"+r),m=c&&c!=="xero-"+r?c:i;me(t("xero-push-fail").replace("{err}",m),"error");return}me(t("xero-push-ok"),"success")}catch(s){me(t("xero-push-fail").replace("{err}",s.message||"network"),"error")}finally{a&&(a.disabled=!1,a.classList.remove("loading"))}}async function ki(){const e=document.getElementById("erp-global-push-mode");if(!e)return;const n=localStorage.getItem("mrpilot_token");if(n)try{const a=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+n}});if(a.ok){const o=await a.json();o.mode&&(e.value=o.mode,e.dataset.prev=o.mode)}}catch{}}async function xi(e){const n=e.value,a=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+a,"Content-Type":"application/json"},body:JSON.stringify({mode:n})})).ok?(e.dataset.prev=n,me(t("pref-erp-mode-saved"),"success")):(e.value=e.dataset.prev||"smart",me(t("pref-save-failed"),"error"))}catch{e.value=e.dataset.prev||"smart",me(t("pref-save-failed"),"error")}}(function(){function e(){const l=document.getElementById("erp-connect-cards");if(!l)return;const d=ue.status;let f,v=!1;d?d.configured?d.connected?(v=!0,f='<span class="mrerp-card-pill mrerp-pill-ok">'+ce(t("xero-card-connected"))+"</span>"):f='<span class="mrerp-card-pill mrerp-pill-neutral">'+ce(t("xero-card-not-connected"))+"</span>":f='<span class="mrerp-card-pill mrerp-pill-neutral">'+ce(t("xero-card-not-configured"))+"</span>":f='<span class="mrerp-card-pill mrerp-pill-neutral">'+ce(t("xero-card-not-connected"))+"</span>";let w="";if(!d||!d.configured)w='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+ce(t("xero-connect-btn"))+"</button>";else if(!d.connected)pa()&&(w='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+ce(t("xero-connect-btn"))+"</button>");else{const B=!!d.auto_push,L=B?t("card-btn-disable"):t("card-btn-enable");w='<button type="button" class="'+(B?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(B?"1":"0")+'" title="'+ce(B?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+ce(L)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+ce(t("card-btn-edit"))+"</button>"}const g=d&&d.connected?"xero-card-desc-connected":"xero-card-desc-default",b=d&&d.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",h=(function(){const B=t(g);return B===g?b:B})();let E='<div class="integration-row erp-connect-xero'+(v?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+ce(t("xero-card-title")||"Xero")+"</span>"+f+'</div><div class="int-desc">'+ce(h)+'</div></div><div class="int-actions">'+w+"</div></div>";if(d&&d.configured&&d.connected&&pa()){const B=d.organisations||[];let L="";if(B.length>0){L+='<div class="erp-cc-meta">'+ce((t("xero-org-count")||"").replace("{n}",String(B.length)))+"</div>",L+='<div class="erp-cc-org-label">'+ce(t("xero-default-org"))+":</div>",L+='<div class="erp-cc-orgs">',B.forEach(function(S){L+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+ce(S.id)+'"'+(S.is_default?" checked":"")+'><span class="erp-cc-org-name">'+ce(S.organisation_name||S.organisation_id)+"</span></label>"}),L+="</div>";const I=!!d.auto_push,C=I?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");L+='<div class="erp-cc-auto-push" title="'+ce(C)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(I?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+ce(t("erp-auto-push-label"))+"</span></label></div>",L+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+ce(t("xero-disconnect-btn"))+"</button></div>"}E+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+L+"</div>"}const y=l.querySelector(".erp-connect-xero"),_=l.querySelector("#erp-xero-details");_&&_.remove(),y?y.outerHTML=E:l.insertAdjacentHTML("afterbegin",E);const k=document.getElementById("btn-xero-edit-toggle");k&&k.addEventListener("click",function(B){B.preventDefault();const L=document.getElementById("erp-xero-details");L&&(L.style.display=L.style.display==="none"?"":"none")});const x=document.getElementById("btn-xero-toggle-enabled");x&&x.addEventListener("click",async function(B){if(B.preventDefault(),x.disabled)return;const I=!(x.getAttribute("data-xero-enabled")==="1");if(!I)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}x.disabled=!0,await s(I,null)})}async function n(){const l=localStorage.getItem("mrpilot_token");if(l)try{const d=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+l}});if(!d.ok){let v="unknown";try{v=(await d.json()).detail||"unknown"}catch{}const w=String(v).replace(/^xero\./,"").toLowerCase();me(t("xero-push-fail").replace("{err}",t("xero-err-"+w)||v),"error");return}const f=await d.json();f.redirect_url&&(window.location.href=f.redirect_url)}catch(d){me(t("xero-push-fail").replace("{err}",d.message||"network"),"error")}}async function a(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const d=localStorage.getItem("mrpilot_token");try{const f=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+d}});if(!f.ok)throw new Error("http_"+f.status);await Xe(!0),e()}catch(f){me(t("xero-push-fail").replace("{err}",f.message),"error")}}async function o(l){const d=localStorage.getItem("mrpilot_token");try{const f=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+d,"Content-Type":"application/json"},body:JSON.stringify({token_id:l})});if(!f.ok)throw new Error("http_"+f.status);await Xe(!0),e()}catch(f){me(t("xero-push-fail").replace("{err}",f.message),"error")}}async function s(l,d){const f=localStorage.getItem("mrpilot_token");d&&(d.disabled=!0);try{const v=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+f,"Content-Type":"application/json"},body:JSON.stringify({on:!!l})});if(!v.ok){let w="unknown";try{w=(await v.json()).detail||"unknown"}catch{}throw new Error(w)}me(l?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),ue.statusLoaded=!1,await Xe(!0),e()}catch(v){d&&(d.checked=!l),me(t("erp-auto-push-toggle-fail").replace("{err}",v.message||"network"),"error")}finally{d&&(d.disabled=!1)}}async function i(){await Xe(!0),e(),ki()}function r(){try{const l=String(window.location.hash||"");if(l.indexOf("xero=ok")>=0){const d=l.match(/n=(\d+)/),f=d?d[1]:"1";me((t("xero-toast-redirected-ok")||"").replace("{n}",f),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),Xe(!0).then(e)}else l.indexOf("xero=err")>=0&&(me(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function c(){if(ue.bound)return;ue.bound=!0,document.addEventListener("click",function(d){if(d.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(i,50);return}if(d.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(i,80);return}if(d.target.closest("#btn-xero-connect")){d.preventDefault(),n();return}if(d.target.closest("#btn-xero-disconnect")){d.preventDefault(),a();return}}),document.addEventListener("change",function(d){d.target&&d.target.matches('input[name="xero-default-org"]')&&o(d.target.value),d.target&&d.target.id==="xero-auto-push-toggle"&&s(d.target.checked,d.target),d.target&&d.target.id==="erp-global-push-mode"&&xi(d.target)});const l=function(){return document.getElementById("drawer-body")};try{const d=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&yi()}),f=l();if(f)d.observe(f,{childList:!0,subtree:!0});else{const v=new MutationObserver(function(){const w=l();w&&(d.observe(w,{childList:!0,subtree:!0}),v.disconnect())});v.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(r,500)}function m(){ue.status&&e();const l=document.getElementById("btn-xero-push");if(l){const d=l.querySelector("span");d&&(d.textContent=t("xero-push-btn"))}}c(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",m);async function p(l){const d=Date.now();for(;Date.now()-d<l;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(f=>setTimeout(f,80))}return null}async function u(){await p(5e3);const l=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),d=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');l&&d&&await i()}setTimeout(u,200)})();(function(){var e="https://www.mrerp4sme.com/dms/index.php",n=null,a=!1;function o(g){return typeof escapeHtml=="function"?escapeHtml(g==null?"":String(g)):String(g??"")}function s(g,b){try{typeof showToast=="function"&&showToast(g,b||"info")}catch{}}function i(){return localStorage.getItem("mrpilot_token")}async function r(g){var b=i();if(!b)return null;try{var h=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+b}});if(!h.ok)throw new Error("http_"+h.status);var E=await h.json(),y=E&&E.items||[];n=y.find(function(_){return _&&(_.adapter||"").toLowerCase()==="mrerp_dms"})||null,a=!0}catch{n=null,a=!1}return n}function c(){var g=document.getElementById("erp-connect-cards");if(g){var b=g.querySelector("[data-mrerp-dms-zone]");b||(b=document.createElement("div"),b.setAttribute("data-mrerp-dms-zone","1"),g.appendChild(b));var h=n,E=!!(h&&h.enabled!==!1),y;h?E?y='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("dms-card-connected"))+"</span>":y='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-disabled-pill"))+"</span>":y='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-not-connected"))+"</span>";var _;if(!h)_='<button type="button" class="int-btn-configure" id="btn-dms-connect">'+o(t("dms-card-connect"))+"</button>";else{var k=E?t("dms-card-disable"):t("dms-card-enable");_='<button type="button" class="int-btn-configure" id="btn-dms-edit">'+o(t("dms-card-edit"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-test">'+o(t("dms-card-test"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-toggle">'+o(k)+"</button>"}b.innerHTML='<div class="integration-row erp-connect-mrerp-dms'+(E?" connected":"")+'"><div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/><path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("dms-card-title"))+"</span>"+y+'</div><div class="int-desc">'+o(t("dms-card-desc"))+'</div></div><div class="int-actions">'+_+"</div></div>"}}function m(){var g=document.getElementById("dms-wizard-overlay");g&&g.remove(),document.removeEventListener("keydown",p)}function p(g){g.key==="Escape"&&m()}function u(){m();var g=n,b=g&&g.config&&g.config.booking_defaults&&g.config.booking_defaults.booking_prefix||"PN",h=function(_,k,x,B,L){return'<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">'+o(t(_))+'</span><input id="'+k+'" type="'+x+'" value="'+o(B||"")+'" placeholder="'+o(L||"")+'" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;"></label>'},E=document.createElement("div");E.id="dms-wizard-overlay",E.style.cssText="position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;",E.innerHTML='<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">'+o(t("dms-wizard-title"))+'</div><div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">'+o(t("dms-card-desc"))+"</div>"+h("dms-wizard-username","dms-w-user","text","","")+h("dms-wizard-password","dms-w-pass","password","","")+h("dms-wizard-prefix","dms-w-prefix","text",b,"PN")+'<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div><div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn btn-ghost" id="dms-w-cancel">'+o(t("dms-wizard-cancel"))+'</button><button type="button" class="btn btn-primary" id="dms-w-save">'+o(t("dms-wizard-save"))+"</button></div></div>",document.body.appendChild(E),document.addEventListener("keydown",p),E.addEventListener("click",function(_){_.target===E&&m()});var y=document.getElementById("dms-w-user");y&&y.focus()}function l(g){var b=document.getElementById("dms-w-err");b&&(b.textContent=g,b.style.display=g?"":"none")}async function d(){var g=n&&n.config&&n.config.system_url||e,b=(document.getElementById("dms-w-user")||{}).value||"",h=(document.getElementById("dms-w-pass")||{}).value||"",E=(document.getElementById("dms-w-prefix")||{}).value||"PN";if(g=g.trim(),b=b.trim(),!g||!b||!h){l(t("dms-wizard-required"));return}var y=document.getElementById("dms-w-save");y&&(y.disabled=!0,y.textContent=t("dms-wizard-saving")),l("");var _=i();try{var k=await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+_,"Content-Type":"application/json"},body:JSON.stringify({adapter:"mrerp_dms",config:{system_url:g,username:b,password:h}})}),x=await k.json().catch(function(){return{}});if(!k.ok||!x.ok){var B=x.error_friendly&&(x.error_friendly[window.currentLang]||x.error_friendly.en)||t("dms-connect-fail-generic");l(B),y&&(y.disabled=!1,y.textContent=t("dms-wizard-save"));return}var L={system_url:g,username_enc:b,password_enc:h,id_card_auto_push:!0,booking_defaults:{booking_prefix:E.trim()||"PN"}},I,C;n&&n.id?(I="PATCH",C="/api/erp/endpoints/"+encodeURIComponent(n.id)):(I="POST",C="/api/erp/endpoints");var S=I==="POST"?{name:"MR.ERP DMS",adapter:"mrerp_dms",config:L,is_default:!1,auto_push:!1}:{config:L,auto_push:!1},q=await fetch(C,{method:I,headers:{Authorization:"Bearer "+_,"Content-Type":"application/json"},body:JSON.stringify(S)});if(!q.ok){var A=await q.json().catch(function(){return{}}),V=A&&A.detail&&(A.detail.code||A.detail)||"save_failed";l(t("dms-save-fail")+" ("+o(String(V))+")"),y&&(y.disabled=!1,y.textContent=t("dms-wizard-save"));return}m(),s(t("dms-connect-ok"),"success"),await r(!0),c(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{l(t("dms-connect-fail-generic")),y&&(y.disabled=!1,y.textContent=t("dms-wizard-save"))}}async function f(){if(!(!n||!n.id)){s(t("dms-test-running"),"info");var g=i();try{var b=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id)+"/test-connection?refresh=1",{method:"POST",headers:{Authorization:"Bearer "+g}}),h=await b.json().catch(function(){return{}});s(h&&h.ok?t("dms-test-ok"):t("dms-test-fail"),h&&h.ok?"success":"error")}catch{s(t("dms-test-fail"),"error")}}}async function v(){if(!(!n||!n.id)){var g=n.enabled===!1;if(!g)try{var b=await window.pearnlyConfirm(t("dms-confirm-disable"));if(!b)return}catch{}var h=i();try{var E=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id),{method:"PATCH",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({enabled:g})});if(!E.ok)throw new Error("http_"+E.status);s(g?t("dms-enabled-toast"):t("dms-disabled-toast"),"success"),await r(!0),c(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{s(t("dms-save-fail"),"error")}}}function w(){r().then(c)}document.addEventListener("click",function(g){if(g.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(w,60);return}if(g.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(w,90);return}if(g.target.closest("#btn-dms-connect")||g.target.closest("#btn-dms-edit")){g.preventDefault(),u();return}if(g.target.closest("#dms-w-cancel")){g.preventDefault(),m();return}if(g.target.closest("#dms-w-save")){g.preventDefault(),d();return}if(g.target.closest("#btn-dms-test")){g.preventDefault(),f();return}if(g.target.closest("#btn-dms-toggle")){g.preventDefault(),v();return}}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("mrerp-dms-adapter",c),setTimeout(function(){var g=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),b=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');g&&b&&w()},250)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const p=`
        <div class="report-modal-overlay" id="report-modal" style="display:none;">
            <div class="report-modal">
                <div class="report-modal-head">
                    <span class="report-modal-title" data-i18n="report-modal-title">导出报表</span>
                    <button class="report-modal-close-x" id="report-modal-close-x" aria-label="close">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l8 8M14 6l-8 8"/></svg>
                    </button>
                </div>
                <div class="report-modal-body">
                    <div class="report-section">
                        <div class="report-section-title" data-i18n="report-section-template">选择模板</div>
                        <div class="report-tpl-list" id="report-tpl-list">
                            <!-- 动态填充 -->
                        </div>
                    </div>
                    <div class="report-section" id="report-period-section">
                        <div class="report-section-title" data-i18n="report-section-period">时间范围</div>
                        <div class="report-period-list">
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="all" checked>
                                <span data-i18n="report-range-all">全部</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-month">
                                <span data-i18n="report-range-this-month">本月</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="last-month">
                                <span data-i18n="report-range-last-month">上月</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-quarter">
                                <span data-i18n="report-range-this-quarter">本季度</span>
                            </label>
                            <label class="report-period-item">
                                <input type="radio" name="report-period" value="this-year">
                                <span data-i18n="report-range-this-year">今年</span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="report-modal-foot">
                    <button class="btn btn-ghost" id="report-modal-cancel" data-i18n="report-modal-cancel">取消</button>
                    <button class="btn btn-primary" id="report-modal-download">
                        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4M4 15v2h12v-2"/></svg>
                        <span data-i18n="report-modal-download">下载 Excel</span>
                    </button>
                </div>
            </div>
        </div>`,u=document.createElement("div");u.innerHTML=p,document.body.appendChild(u.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",l=>{l.target.id==="report-modal"&&a()})}function a(){const p=document.getElementById("report-modal");p&&(p.style.display="none"),o=null}let o=null;async function s(p,u){const l=p+":"+(u||"");if(e[l])return e[l];let d;try{const f=localStorage.getItem("mrpilot_token"),v=await fetch(`/api/reports/templates?lang=${encodeURIComponent(p)}`,{headers:{Authorization:"Bearer "+f}});if(!v.ok)throw new Error("templates fetch failed");d=(await v.json()).templates||[]}catch(f){console.error("fetchTemplates fail",f),d=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(d=d.filter(f=>f.code!=="erp"),u==="history-batch"){const f=d.findIndex(w=>w.code==="standard"),v=f>=0?f+1:d.length;d.splice(v,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[l]=d,d}function i(p){const u=document.getElementById("report-tpl-list"),l=p.map((f,v)=>`
            <label class="report-tpl-item${f.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${f.code}" ${f.recommended||v===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${r(f.name)}
                        ${f.recommended?`<span class="report-tpl-badge">${r(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${r(f.desc||"")}</div>
                </div>
            </label>
        `).join(""),d=`
            <label class="report-tpl-item report-tpl-coming" title="${r(t("tpl-custom-coming"))}">
                <input type="radio" name="report-tpl" disabled>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        + ${r(t("tpl-custom-new"))}
                        <span class="report-tpl-badge report-tpl-badge-soon">${r(t("cs-coming-soon"))}</span>
                    </div>
                    <div class="report-tpl-desc">${r(t("tpl-custom-desc"))}</div>
                </div>
            </label>
        `;u.innerHTML=l+d}function r(p){return p==null?"":String(p).replace(/[&<>"']/g,u=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[u])}function c(p){const u=new Date,l=u.getFullYear(),d=u.getMonth()+1;if(p==="all")return"all";if(p==="this-month")return`${l}-${String(d).padStart(2,"0")}`;if(p==="last-month"){const f=new Date(l,d-2,1);return`${f.getFullYear()}-${String(f.getMonth()+1).padStart(2,"0")}`}return p==="this-year"?`${l}`:p==="this-quarter"?`${l}-Q${Math.floor((d-1)/3)+1}`:"all"}window.openReportModal=async function(p){p=p||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(w=>{const g=w.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][g]&&(w.textContent=I18N[currentLang][g])});const u=document.getElementById("report-period-section");u&&(u.style.display=p.mode==="client"?"":"none");const l=document.getElementById("report-tpl-list");l.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const d=await s(currentLang,p&&p.mode);i(d),o=p;const f=document.getElementById("report-modal-download"),v=f.cloneNode(!0);f.parentNode.replaceChild(v,f),v.addEventListener("click",()=>m(o))};async function m(p){if(!p)return;const u=document.querySelector('input[name="report-tpl"]:checked');if(!u){showToast(t("report-toast-no-selection"),"info");return}const l=u.value,d=document.querySelector('input[name="report-period"]:checked'),f=d?d.value:"all",v=c(f),w=document.getElementById("report-modal-download"),g=w.innerHTML;w.disabled=!0,w.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const b=localStorage.getItem("mrpilot_token");let h,E;if(p.mode==="records")h=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:l,lang:currentLang,records:p.records||[],meta:p.meta||{}})}),E=`mrpilot-${l}-${Date.now()}.xlsx`;else if(p.mode==="client"){const I=`/api/reports/clients/${p.clientId}/export?template=${encodeURIComponent(l)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(v)}`;h=await fetch(I,{headers:{Authorization:"Bearer "+b}}),E=`${(p.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${l}.xlsx`}else if(p.mode==="history-batch")l==="sales_detail_th"?(h=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),E=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(h=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:l,lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),E=`mrpilot-batch-${l}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+p.mode);if(!h.ok){let I="HTTP "+h.status;try{const C=await h.json();C&&C.detail&&(I=C.detail)}catch(C){console.warn("[batch-export] resp.json err.detail parse failed:",C)}h.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+I,"error");return}const y=await h.blob();let _=E;const x=(h.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(x)try{_=decodeURIComponent(x[1])}catch{}const B=URL.createObjectURL(y),L=document.createElement("a");L.href=B,L.download=_,document.body.appendChild(L),L.click(),document.body.removeChild(L),URL.revokeObjectURL(B),showToast(t("report-toast-success"),"success"),a()}catch(b){console.error("doDownload fail",b),showToast(t("report-toast-fail")+" · "+(b.message||""),"error")}finally{w.disabled=!1,w.innerHTML=g}}document.addEventListener("DOMContentLoaded",()=>{const p=document.getElementById("btn-export");if(p){const l=p.cloneNode(!0);p.parentNode.replaceChild(l,p),l.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(d=>({filename:d.filename,merged_fields:d.merged_fields||{}}))})})}const u=document.getElementById("history-batch-export");u&&u.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(p,u){openReportModal({mode:"client",clientId:p,clientName:u||""})}})();const _i=/\.(pdf|jpe?g|png|webp)$/i,Ei="mrpilot_folder_watcher",Bi=1;let Dt=null;function ln(){return Dt||(Dt=new Promise((e,n)=>{const a=indexedDB.open(Ei,Bi);a.onupgradeneeded=o=>{const s=o.target.result;s.objectStoreNames.contains("handles")||s.createObjectStore("handles"),s.objectStoreNames.contains("seen")||s.createObjectStore("seen"),s.objectStoreNames.contains("config")||s.createObjectStore("config")},a.onsuccess=o=>e(o.target.result),a.onerror=o=>n(o.target.error)}),Dt)}function yt(e,n){return ln().then(a=>new Promise((o,s)=>{const r=a.transaction(e,"readonly").objectStore(e).get(n);r.onsuccess=()=>o(r.result),r.onerror=()=>s(r.error)}))}function Re(e,n,a){return ln().then(o=>new Promise((s,i)=>{const r=o.transaction(e,"readwrite");r.objectStore(e).put(a,n),r.oncomplete=()=>s(),r.onerror=()=>i(r.error)}))}function gt(e,n){return ln().then(a=>new Promise((o,s)=>{const i=a.transaction(e,"readwrite");i.objectStore(e).delete(n),i.oncomplete=()=>o(),i.onerror=()=>s(i.error)}))}function ua(e){return ln().then(n=>new Promise((a,o)=>{const s=n.transaction(e,"readwrite");s.objectStore(e).clear(),s.oncomplete=()=>a(),s.onerror=()=>o(s.error)}))}async function fa(e){if(!e)return!1;try{const n={mode:"read"};let a=await e.queryPermission(n);return a==="granted"?!0:(a=await e.requestPermission(n),a==="granted")}catch(n){return console.warn("[folder] permission check failed:",n),!1}}async function Ii(e){const n=new FormData;n.append("file",e,e.name),n.append("source","folder");const a=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:n});if(!a.ok){let o="http_"+a.status;try{const s=await a.json();o=s&&s.detail?typeof s.detail=="string"?s.detail:s.detail.code||JSON.stringify(s.detail):o}catch{}throw new Error(o)}return await a.json()}async function Li(e){try{const a=(await e.getFile()).size;return await new Promise(s=>setTimeout(s,3e3)),(await e.getFile()).size===a&&a>0}catch{return!1}}async function po(e,n,a,o){if(o>10)return;let s;try{s=await e.queryPermission({mode:"read"})}catch{s="denied"}if(s==="granted")for await(const i of e.values()){const r=n?`${n}/${i.name}`:i.name;if(i.kind==="file"){if(!_i.test(i.name))continue;let c;try{c=await i.getFile()}catch{continue}const m=`${r}::${c.size}::${c.lastModified}`;if(await yt("seen",m))continue;a.push({entry:i,file:c,seenKey:m,relPath:r})}else if(i.kind==="directory")try{await po(i,r,a,o+1)}catch{}}}(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window;let a=null,o=null,s=60,i=!1,r=!1,c=0,m=0,p=0,u=[],l=null,d=!1;function f($,H){const K=document.getElementById("folder-status-summary");K&&(K.setAttribute("data-i18n",$),K.textContent=t($),K.className="auto-status-pill"+(H?" "+H:""))}function v($){["folder-unsupported","folder-empty","folder-active"].forEach(H=>{const K=document.getElementById(H);K&&(K.style.display=H===$?"":"none")})}function w($){if(!$)return"-";const H=$ instanceof Date?$:new Date($),K=String(H.getHours()).padStart(2,"0"),ae=String(H.getMinutes()).padStart(2,"0"),ne=String(H.getSeconds()).padStart(2,"0");return`${K}:${ae}:${ne}`}function g(){v("folder-active");const $=document.getElementById("folder-config-path");$&&a&&($.textContent=a.name||"-");const H=document.getElementById("folder-interval-select");H&&(H.value=String(s)),document.getElementById("folder-stat-last").textContent=l?w(l):"-",document.getElementById("folder-stat-processed").textContent=String(c),document.getElementById("folder-stat-failed").textContent=String(m),document.getElementById("folder-stat-queue").textContent=String(p);const K=document.getElementById("btn-folder-pause"),ae=document.getElementById("btn-folder-resume");K&&(K.style.display=i?"none":""),ae&&(ae.style.display=i?"":"none"),i?f("folder-status-paused","paused"):f("folder-status-running","running");const ne=document.getElementById("folder-status-text");ne&&(ne.setAttribute("data-i18n",i?"folder-status-paused":"folder-status-running"),ne.textContent=t(i?"folder-status-paused":"folder-status-running"));const de=document.getElementById("folder-status-pulse");de&&(de.className="folder-status-pulse"+(i?" paused":"")),b()}function b(){const $=document.getElementById("folder-recent-list");if($){if(u.length===0){$.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}$.innerHTML=u.slice(0,20).map(H=>{let K;H.status==="ok"?K=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:H.status==="dup"?K=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:H.status==="skip"?K=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:K=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const ae=H.status==="fail"&&H.error?H.error:H.status==="dup"&&H.reason||H.status==="skip"&&H.reason?H.reason:"",ne=ae?`<div class="folder-recent-err">${escapeHtml(ae)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${K}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(H.name)}</div>
                        ${ne}
                    </div>
                    <div class="folder-recent-time">${w(H.time)}</div>
                </div>
            `}).join("")}}function h($){u.unshift($),u.length>50&&(u.length=50),Re("config","recent_list",u).catch(()=>{})}async function E(){if(!(r||i||!a)){r=!0;try{if(await a.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),S(),showToast("warn",t("folder-permission-lost"));return}l=new Date;const H=[];await po(a,"",H,0),p=H.length,g();for(const K of H){if(i)break;if(!await Li(K.entry)){p=Math.max(0,p-1),g();continue}try{let ne;try{ne=await K.entry.getFile()}catch{ne=K.file}const de=await Ii(ne);await Re("seen",K.seenKey,{name:ne.name,relPath:K.relPath,size:ne.size,lastModified:ne.lastModified,processed_at:Date.now()});const Q=de.history_ids||(de.history_id?[de.history_id]:[]),le=de.duplicate_warnings||[],pe=K.relPath||ne.name;Q.length>0?(c+=Q.length,h({name:pe,status:"ok",time:new Date,history_id:Q[0],count:Q.length}),await Re("config","processed_count",c)):le.length>0?h({name:pe,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):h({name:pe,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(ne){m++,h({name:K.relPath||K.file.name,status:"fail",time:new Date,error:String(ne.message||ne)}),await Re("config","failed_count",m)}p=Math.max(0,p-1),g()}}catch($){console.warn("[folder] scan error:",$)}finally{r=!1,g()}}}function y(){o&&clearInterval(o),o=setInterval(E,s*1e3)}function _(){o&&(clearInterval(o),o=null)}function k($){if(!a||i)return;const H=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return $.preventDefault(),$.returnValue=H,H}function x(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",k))}function B(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",k))}function L(){i=!1,y(),x(),g(),E()}function I(){i=!0,_(),B(),g()}function C(){i=!1,y(),x(),g(),E()}function S(){i=!0,_(),B()}async function q(){try{const $=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await fa($)){showToast("warn",t("folder-permission-denied"));return}a=$,await Re("handles","main",$),c=0,m=0,p=0,u=[],await Re("config","processed_count",0),await Re("config","failed_count",0),await ua("seen"),L()}catch($){$&&$.name!=="AbortError"&&console.warn("[folder] pick failed:",$)}}async function A(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(S(),a=null,c=0,m=0,p=0,u=[],await gt("handles","main"),await gt("config","processed_count"),await gt("config","failed_count"),await ua("seen"),v("folder-empty"),f("folder-status-empty",""))}async function V(){u=[];try{await gt("config","recent_list")}catch{}b()}async function T(){if(d)return;if(d=!0,!n){v("folder-unsupported"),f("folder-status-unsupported",""),G();return}F();let $=null;try{$=await yt("handles","main")}catch{}if(!$){v("folder-empty"),f("folder-status-empty","");return}if(!await fa($)){v("folder-empty"),f("folder-status-empty",""),await gt("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}a=$;try{c=await yt("config","processed_count")||0}catch{}try{m=await yt("config","failed_count")||0}catch{}try{const K=await yt("config","recent_list");Array.isArray(K)&&(u=K.map(ae=>({...ae,time:ae.time?new Date(ae.time):new Date})))}catch{}L()}function F(){const $=document.getElementById("btn-folder-pick"),H=document.getElementById("btn-folder-pause"),K=document.getElementById("btn-folder-resume"),ae=document.getElementById("btn-folder-scan-now"),ne=document.getElementById("btn-folder-remove"),de=document.getElementById("btn-folder-clear-recent"),Q=document.getElementById("folder-interval-select");$&&$.addEventListener("click",q),H&&H.addEventListener("click",I),K&&K.addEventListener("click",C),ae&&ae.addEventListener("click",()=>{E()}),ne&&ne.addEventListener("click",A),de&&de.addEventListener("click",V),Q&&Q.addEventListener("change",le=>{s=parseInt(le.target.value,10)||60,i||y()}),O()}function O(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach($=>{$.dataset.tabJumpBound||($.dataset.tabJumpBound="1",$.addEventListener("click",H=>{const K=H.currentTarget.dataset.tabJump;if(K==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(K==="upload"){const ae=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');ae&&ae.click()}}))})}function G(){O()}window._loadFolderWatcherPanel=T})();function Ci(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(n=>/chromium|google chrome|microsoft edge/i.test(n.brand||""))}catch{}const e=navigator.userAgent||"";return!!(/Edg\//.test(e)||/Chrome\//.test(e)&&!/OPR\/|YaBrowser|Opera/.test(e))}function In(){try{if(Ci()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const e=document.getElementById("chrome-only-banner");if(!e)return;const n=e.querySelector('[data-i18n="chrome-banner-msg"]'),a=e.querySelector('[data-i18n="chrome-banner-dismiss"]');n&&typeof t=="function"&&(n.textContent=t("chrome-banner-msg")),a&&typeof t=="function"&&(a.textContent=t("chrome-banner-dismiss")),e.style.display="";const o=document.getElementById("chrome-only-banner-close");o&&!o.dataset.bound&&(o.dataset.bound="1",o.addEventListener("click",()=>{e.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",In):setTimeout(In,0));window._refreshChromeBanner=In;const Si=`
        <div class="modal">
            <div class="modal-head">
                <div class="modal-title" id="email-modal-title" data-i18n="email-modal-title-new">绑定邮箱</div>
                <button class="modal-close" id="email-modal-close" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body">
                <!-- 预设服务商 -->
                <div class="form-group">
                    <label class="form-label" for="email-preset" data-i18n="email-field-preset">邮箱服务商</label>
                    <select id="email-preset" class="form-input"></select>
                    <div class="form-hint" data-i18n="email-preset-hint">选中后自动填 IMAP 服务器 · 选「其它」可手动填</div>
                </div>

                <!-- 邮箱地址 -->
                <div class="form-group">
                    <label class="form-label" for="email-address" data-i18n="email-field-address">邮箱地址</label>
                    <input type="email" id="email-address" class="form-input" placeholder="you@example.com" autocomplete="off" spellcheck="false">
                </div>

                <!-- 密码 -->
                <div class="form-group">
                    <label class="form-label" for="email-password" data-i18n="email-field-password">应用密码</label>
                    <input type="password" id="email-password" class="form-input" data-i18n-placeholder="email-field-password-ph" autocomplete="new-password" spellcheck="false">
                    <!-- v0.17.10 · 应用密码提示卡(两行) -->
                    <div class="email-pwd-help">
                        <div class="email-pwd-help-row">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="7" width="10" height="7" rx="1"/>
                                <path d="M5.5 7V4.5a2.5 2.5 0 015 0V7"/>
                            </svg>
                            <span>
                                <span data-i18n="email-pwd-help-personal">个人邮箱(Gmail · Outlook · iCloud 等)需要「应用专用密码」· 不是登录密码</span>
                                <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener" data-i18n="email-pwd-help-gmail-link">· Gmail 教程</a>
                            </span>
                        </div>
                        <div class="email-pwd-help-row">
                            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M3 6h10v8H3z"/>
                                <path d="M5.5 6V4.5a2.5 2.5 0 015 0V6"/>
                                <circle cx="8" cy="10" r="1"/>
                            </svg>
                            <span data-i18n="email-pwd-help-corp">公司企业邮箱可先用普通密码试 · 失败再问 IT</span>
                        </div>
                        <div class="email-pwd-help-row email-pwd-help-tip">
                            <span data-i18n="email-pwd-help-blank">留空则保留已存密码</span>
                        </div>
                    </div>
                </div>

                <!-- 高级:IMAP 服务器设置 -->
                <details class="email-adv-details" id="email-adv-details">
                    <summary data-i18n="email-advanced">高级(服务器设置)</summary>
                    <div class="form-group" style="margin-top:12px;">
                        <label class="form-label" for="email-imap-host" data-i18n="email-field-host">IMAP 服务器</label>
                        <input type="text" id="email-imap-host" class="form-input" placeholder="imap.gmail.com">
                    </div>
                    <div class="form-group form-row-2">
                        <div>
                            <label class="form-label" for="email-imap-port" data-i18n="email-field-port">端口</label>
                            <input type="number" id="email-imap-port" class="form-input" value="993" min="1" max="65535">
                        </div>
                        <div>
                            <label class="form-label" data-i18n="email-field-ssl">SSL</label>
                            <label class="form-switch-row" style="margin:6px 0 0;">
                                <input type="checkbox" id="email-imap-ssl" checked>
                                <span class="form-switch-label" data-i18n="email-field-ssl-on">启用加密连接</span>
                            </label>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="email-folder" data-i18n="email-field-folder">文件夹</label>
                        <input type="text" id="email-folder" class="form-input" value="INBOX">
                    </div>
                </details>

                <!-- v95 · 抓取过滤器(可选 · 留空 = 全部抓) -->
                <div class="form-group">
                    <label class="form-label" for="email-filter-sender" data-i18n="email-field-filter-sender">发件人白名单 · 选填</label>
                    <textarea id="email-filter-sender" class="form-input" rows="2" data-i18n-placeholder="email-filter-sender-ph" spellcheck="false"></textarea>
                    <div class="form-hint" data-i18n="email-filter-sender-hint">仅抓白名单发件人 · 多个用逗号或换行分隔 · 留空抓全部</div>
                </div>
                <div class="form-group">
                    <label class="form-label" for="email-filter-subject" data-i18n="email-field-filter-subject">主题关键词 · 选填</label>
                    <textarea id="email-filter-subject" class="form-input" rows="2" data-i18n-placeholder="email-filter-subject-ph" spellcheck="false"></textarea>
                    <div class="form-hint" data-i18n="email-filter-subject-hint">仅抓主题含任一关键词的邮件 · 多个用逗号分隔 · 留空抓全部</div>
                </div>

                <!-- 抓取行为 -->
                <div class="form-group">
                    <label class="form-switch-row">
                        <input type="checkbox" id="email-mark-read" checked>
                        <span class="form-switch-label" data-i18n="email-field-mark-read">处理后标记邮件为已读</span>
                    </label>
                    <label class="form-switch-row">
                        <input type="checkbox" id="email-bind-enabled" checked>
                        <span class="form-switch-label" data-i18n="email-field-enabled">绑定后启用自动抓取</span>
                    </label>
                </div>

                <!-- v0.17.9 · 抓取频率(3 档) -->
                <div class="form-group email-interval-row">
                    <label class="form-label" data-i18n="email-field-interval">抓取频率</label>
                    <div class="email-interval-options" id="email-interval-options">
                        <button type="button" class="email-interval-btn" data-interval="5">
                            <div class="email-interval-btn-title" data-i18n="email-interval-fast">快速</div>
                            <div class="email-interval-btn-desc" data-i18n="email-interval-fast-desc">每 5 分钟</div>
                        </button>
                        <button type="button" class="email-interval-btn active" data-interval="15">
                            <div class="email-interval-btn-title" data-i18n="email-interval-normal">标准</div>
                            <div class="email-interval-btn-desc" data-i18n="email-interval-normal-desc">每 15 分钟 · 推荐</div>
                        </button>
                        <button type="button" class="email-interval-btn" data-interval="60">
                            <div class="email-interval-btn-title" data-i18n="email-interval-slow">省资源</div>
                            <div class="email-interval-btn-desc" data-i18n="email-interval-slow-desc">每 60 分钟</div>
                        </button>
                    </div>
                </div>

                <!-- 测试连接结果 -->
                <div class="form-test-result" id="email-test-result" style="display:none;"></div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="btn-email-modal-test">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3 3 7-7"/></svg>
                    <span data-i18n="email-btn-test">测试连接</span>
                </button>
                <div style="flex:1"></div>
                <button class="btn btn-ghost" id="btn-email-modal-cancel" data-i18n="btn-cancel">取消</button>
                <button class="btn btn-primary" id="btn-email-modal-save" data-i18n="btn-save">保存</button>
            </div>
        </div>
    `;ve("email-modal",Si);const U={account:null,presets:null,modalMode:"new",loaded:!1,triggering:!1,autoRefreshTimer:null};function ma(e){U.modalMode=e;const n=document.getElementById("email-modal");if(!n)return;const a=document.getElementById("email-preset");a.innerHTML="";const o=U.presets||{},s=["gmail","outlook","yahoo","icloud","qq","163","custom"],i={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};s.forEach(b=>{if(!o[b])return;const h=document.createElement("option");h.value=b,h.textContent=b==="custom"?t("email-preset-custom"):i[b]||b,a.appendChild(h)});const r=document.getElementById("email-modal-title"),c=document.getElementById("email-address"),m=document.getElementById("email-password"),p=document.getElementById("email-imap-host"),u=document.getElementById("email-imap-port"),l=document.getElementById("email-imap-ssl"),d=document.getElementById("email-folder"),f=document.getElementById("email-mark-read"),v=document.getElementById("email-bind-enabled"),w=document.getElementById("email-test-result"),g=document.getElementById("email-adv-details");if(w&&(w.style.display="none",w.textContent=""),e==="edit"&&U.account){r.setAttribute("data-i18n","email-modal-title-edit"),r.textContent=t("email-modal-title-edit"),c.value=U.account.email_address||"",m.value="",m.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),m.placeholder=t("email-field-password-edit-ph"),p.value=U.account.imap_host||"",u.value=U.account.imap_port||993,l.checked=U.account.imap_use_ssl!==!1,d.value=U.account.folder||"INBOX",f.checked=U.account.mark_as_read!==!1,v.checked=U.account.enabled!==!1;const b=document.getElementById("email-filter-sender"),h=document.getElementById("email-filter-subject");b&&(b.value=U.account.filter_sender||""),h&&(h.value=U.account.filter_subject||""),ha(U.account.interval_min||15),a.value=Mi(U.account.imap_host)||"custom",g&&(g.open=!0)}else{r.setAttribute("data-i18n","email-modal-title-new"),r.textContent=t("email-modal-title-new"),c.value="",m.value="",m.setAttribute("data-i18n-placeholder","email-field-password-ph"),m.placeholder=t("email-field-password-ph"),a.value="gmail",Nn("gmail"),d.value="INBOX",f.checked=!0,v.checked=!0;const b=document.getElementById("email-filter-sender"),h=document.getElementById("email-filter-subject");b&&(b.value=""),h&&(h.value=""),ha(15),g&&(g.open=!1)}$i(),n.style.display="flex",setTimeout(()=>c.focus(),60)}function vn(){const e=document.getElementById("email-modal");e&&(e.style.display="none")}function Nn(e){const n=(U.presets||{})[e];if(!n||e==="custom")return;const a=document.getElementById("email-imap-host"),o=document.getElementById("email-imap-port"),s=document.getElementById("email-imap-ssl");a&&(a.value=n.host||""),o&&(o.value=n.port||993),s&&(s.checked=n.ssl!==!1)}const Ti={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function va(e){if(!e||!e.includes("@"))return;const n=e.split("@")[1].toLowerCase().trim(),a=Ti[n];if(!a)return;const o=document.getElementById("email-preset");if(!o)return;const s=o.value;s&&s!=="custom"&&s!==""&&s===a||(o.value=a,Nn(a))}function Mi(e){if(!e)return null;const n=U.presets||{};for(const a in n)if(a!=="custom"&&n[a]&&n[a].host===e)return a;return null}function uo(){const e=document.querySelector("#email-interval-options .email-interval-btn.active"),n=e?parseInt(e.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(n)?n:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function $i(){const e=document.getElementById("email-interval-options");!e||e._bound||(e._bound=!0,e.addEventListener("click",n=>{const a=n.target.closest(".email-interval-btn");a&&(e.querySelectorAll(".email-interval-btn").forEach(o=>o.classList.remove("active")),a.classList.add("active"))}))}function ha(e){const n=[5,15,60].includes(e)?e:15,a=document.getElementById("email-interval-options");a&&a.querySelectorAll(".email-interval-btn").forEach(o=>{o.classList.toggle("active",parseInt(o.dataset.interval,10)===n)})}function ge(e,n){const a=document.getElementById("email-test-result");a&&(a.style.display="",a.textContent=n,a.className="form-test-result "+(e==="ok"?"ok":e==="running"?"running":"fail"))}async function Hi(){const e=uo();if(!e.email_address){ge("fail",t("email-addr-required"));return}if(!e.password){ge("fail",t("email-password-required"));return}if(!e.imap_host){ge("fail",t("email-host-required"));return}const n=document.getElementById("btn-email-modal-test");n&&(n.disabled=!0),ge("running",t("email-test-running"));try{const a=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,password:e.password,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder})}),o=await a.json().catch(()=>({}));if(a.ok&&o.success)ge("ok",t("email-test-ok",{folder:e.folder,n:o.folder_count??"?"}));else{const s=o.error_msg||"";s==="auth_failed"||/auth/i.test(s)?ge("fail",t("email-test-auth-fail")):ge("fail",t("email-test-fail",{msg:s||a.status}))}}catch(a){ge("fail",t("email-test-fail",{msg:String(a).slice(0,120)}))}finally{n&&(n.disabled=!1)}}(function(){async function e(){const d=document.getElementById("email-empty"),f=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!d||!f))try{const v=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(v.status===401){localStorage.removeItem("mrpilot_token");const g=await v.json().catch(()=>({}));if((typeof g.detail=="string"?g.detail:g.detail&&g.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!v.ok){a("none");return}const w=await v.json();U.account=w.account||null,U.presets=w.presets||{},U.loaded=!0,n(),U.account&&p()}catch(v){console.error("[email-ingest] load failed",v),a("none")}}function n(){const d=document.getElementById("email-empty"),f=document.getElementById("email-account-card"),v=document.getElementById("email-logs-section");if(!U.account){d.style.display="",f.style.display="none",v&&(v.style.display="none"),a("none");return}d.style.display="none",f.style.display="",v&&(v.style.display="");const w=document.getElementById("email-account-addr"),g=document.getElementById("email-account-host"),b=document.getElementById("email-account-last"),h=document.getElementById("email-last-error"),E=document.getElementById("email-enabled-toggle");if(w&&(w.textContent=U.account.email_address||"-"),g&&(g.textContent=`${U.account.imap_host||"-"}:${U.account.imap_port||993}`),b){const y=U.account.last_fetched_at;if(!y)b.textContent=t("email-last-never");else{const _=o(y),k=!U.account.last_error;b.textContent=k?t("email-last-ok",{time:_}):t("email-last-fail",{time:_})}}h&&(U.account.last_error?(h.style.display="",h.textContent=s(U.account.last_error)):h.style.display="none"),E&&(E.checked=!!U.account.enabled),U.account.enabled?U.account.last_error?a("error"):a("on"):a("off")}function a(d){const f=document.getElementById("email-status-summary");if(!f)return;f.classList.remove("none","ready","active","coming");let v="auto-status-loading";d==="none"?(v="email-status-none",f.classList.add("none")):d==="on"?(v="email-status-on",f.classList.add("active")):d==="off"?(v="email-status-off",f.classList.add("coming")):d==="error"&&(v="email-status-error",f.classList.add("none")),f.setAttribute("data-i18n",v),f.textContent=t(v)}function o(d){if(!d)return"";const f=new Date(d);if(isNaN(f.getTime()))return"";const v=w=>String(w).padStart(2,"0");return`${v(f.getMonth()+1)}-${v(f.getDate())} ${v(f.getHours())}:${v(f.getMinutes())}`}function s(d){if(!d)return"";const f=String(d);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(f)?t("email-test-auth-fail"):/timeout|timed out/i.test(f)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(f),f)}async function i(){const d=uo();if(!d.email_address){ge("fail",t("email-addr-required"));return}if(U.modalMode==="new"&&!d.password){ge("fail",t("email-password-required"));return}if(!d.imap_host){ge("fail",t("email-host-required"));return}const f=document.getElementById("btn-email-modal-save");f&&(f.disabled=!0);const v={...d};U.modalMode==="edit"&&!v.password&&delete v.password;try{const w=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(v)}),g=await w.json().catch(()=>({}));if(w.ok&&g.ok)U.account=g.account,showToast(t("email-save-ok"),"success"),vn(),n(),p();else{const h="email."+(g.detail||"").split(".").slice(-1)[0];ge("fail",t(h)!==h?t(h):t("email-save-fail"))}}catch{ge("fail",t("email-save-fail"))}finally{f&&(f.disabled=!1)}}async function r(){if(!(!U.account||!await showConfirm(t("email-unbind-confirm",{email:U.account.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){U.account=null,showToast(t("email-unbind-ok"),"success"),n();const v=document.getElementById("email-logs-list");v&&(v.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function c(){if(!U.account||U.triggering)return;if(!U.account.enabled){showToast(t("email.disabled"),"error");return}U.triggering=!0;const d=document.getElementById("btn-email-trigger"),f=d?d.innerHTML:"";d&&(d.disabled=!0,d.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const v=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),w=await v.json().catch(()=>({}));if(v.ok){const g=w.emails_scanned||0,b=w.ocr_succeeded||0,h=w.ocr_failed||0;g===0&&b===0&&h===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:g,ok:b,fail:h}),h>0?"warn":"success")}else{const b="email."+(w.detail||"").split(".").slice(-1)[0];showToast(t(b)!==b?t(b):t("email-trigger-fail"),"error")}await e()}catch{showToast(t("email-trigger-fail"),"error")}finally{U.triggering=!1,d&&(d.disabled=!1,d.innerHTML=f)}}async function m(){if(!U.account)return;const d=document.getElementById("email-enabled-toggle"),f=!!(d&&d.checked),v=U.account.enabled;try{const w=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:U.account.email_address,imap_host:U.account.imap_host,imap_port:U.account.imap_port,imap_use_ssl:U.account.imap_use_ssl,folder:U.account.folder||"INBOX",filter_subject:U.account.filter_subject||null,filter_sender:U.account.filter_sender||null,mark_as_read:U.account.mark_as_read!==!1,enabled:f})}),g=await w.json().catch(()=>({}));w.ok&&g.ok?(U.account=g.account,n()):(d&&(d.checked=v),showToast(t("email-toggle-fail"),"error"))}catch{d&&(d.checked=v),showToast(t("email-toggle-fail"),"error")}}async function p(){const d=document.getElementById("email-logs-list");if(d){d.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const f=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!f.ok){d.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const v=await f.json();if(!Array.isArray(v)||v.length===0){d.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}d.innerHTML=v.map(u).join("")}catch{d.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function u(d){const f=o(d.created_at),v=d.status||"failed",w=v==="success"?"ok":v==="partial"?"partial":"fail",g=v==="success"?"✓":v==="partial"?"◐":"✗",b=d.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,h=t("email-log-counts",{scanned:d.emails_scanned||0,att:d.attachments_found||0,ok:d.ocr_succeeded||0,fail:d.ocr_failed||0}),E=(d.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${w}">
                <span class="log-time">${escapeHtml(f)}</span>
                <span class="log-status">${g}</span>
                ${b}
                <span class="log-counts">${escapeHtml(h)}</span>
                <span class="log-elapsed">${escapeHtml(E)}</span>
            </div>
        `}function l(){const d=document.getElementById("btn-email-bind");d&&d.addEventListener("click",()=>ma("new"));const f=document.getElementById("btn-email-edit");f&&f.addEventListener("click",()=>ma("edit"));const v=document.getElementById("btn-email-unbind");v&&v.addEventListener("click",r);const w=document.getElementById("btn-email-trigger");w&&w.addEventListener("click",c);const g=document.getElementById("email-enabled-toggle");g&&g.addEventListener("change",m);const b=document.getElementById("email-modal-close");b&&b.addEventListener("click",vn);const h=document.getElementById("btn-email-modal-cancel");h&&h.addEventListener("click",vn);const E=document.getElementById("btn-email-modal-test");E&&E.addEventListener("click",Hi);const y=document.getElementById("btn-email-modal-save");y&&y.addEventListener("click",i);const _=document.getElementById("email-preset");_&&_.addEventListener("change",B=>Nn(B.target.value));const k=document.getElementById("email-address");k&&!k.dataset.autoBound&&(k.dataset.autoBound="1",k.addEventListener("blur",B=>va((B.target.value||"").trim())),k.addEventListener("input",B=>{const L=(B.target.value||"").trim();L.includes("@")&&L.split("@")[1].includes(".")&&va(L)}));const x=document.getElementById("btn-email-refresh-logs");x&&x.addEventListener("click",()=>{x.classList.add("spinning"),setTimeout(()=>x.classList.remove("spinning"),600),p()})}l(),window._loadEmailIngestPanel=e,window._rerenderEmailIngest=function(){if(!U.loaded)return;n();const d=document.getElementById("email-logs-section");U.account&&d&&d.open&&p()},window._startEmailLogAutoRefresh=function(){U.autoRefreshTimer||(U.autoRefreshTimer=setInterval(()=>{U.account&&U.loaded&&p()},3e4))},window._stopEmailLogAutoRefresh=function(){U.autoRefreshTimer&&(clearInterval(U.autoRefreshTimer),U.autoRefreshTimer=null)}})();const Ai=`
    <div class="bank-cand-backdrop" data-bank-cand-close></div>
    <div class="bank-cand-panel">
        <div class="bank-cand-head">
            <div>
                <div class="bank-cand-title" data-i18n="bank-cand-title">匹配候选</div>
                <div class="bank-cand-sub" id="bank-cand-tx-info"></div>
            </div>
            <button class="modal-close" data-bank-cand-close aria-label="close">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
            </button>
        </div>
        <div class="bank-cand-body" id="bank-cand-body">
            <div class="bank-empty" data-i18n="bank-cand-loading">加载中…</div>
        </div>
        <div class="bank-cand-foot">
            <button class="btn btn-ghost btn-small" id="btn-bank-cand-ignore">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10"/></svg>
                <span data-i18n="bank-cand-ignore">忽略此条流水</span>
            </button>
        </div>
    </div>
`;ve("bank-cand-drawer",Ai);const ji=`
    <div class="modal" style="max-width: 420px;">
        <div class="modal-head">
            <div class="modal-title" data-i18n="bank-client-picker-title">绑定客户</div>
            <button class="modal-close" data-bank-client-picker-close aria-label="close">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
            </button>
        </div>
        <div class="modal-body">
            <div class="bank-client-picker-hint" data-i18n="bank-client-picker-hint">把这份对账绑定到客户后 · 只有分到该客户的员工能看见 / 操作</div>
            <div class="bank-client-picker-list" id="bank-client-picker-list">
                <div class="bank-empty" data-i18n="assign-loading">加载中…</div>
            </div>
        </div>
        <div class="modal-foot">
            <button class="btn btn-ghost btn-small" data-bank-client-picker-close>
                <span data-i18n="assign-cancel">取消</span>
            </button>
            <button class="btn btn-primary btn-small" id="btn-bank-client-picker-save">
                <span data-i18n="assign-save">保存</span>
            </button>
        </div>
    </div>
`;ve("bank-client-picker-modal",ji);const j={sessions:[],currentSession:null,currentTxs:[],currentFilter:"all",currentTxForDrawer:null,loaded:!1,queue:[],qSeq:0,sessionFilter:"all",pickerSelected:null};function Pi(e){const n=Number(e||0);let a="score-low";return n>=85?a="score-high":n>=60&&(a="score-mid"),'<span class="bank-cand-score '+a+'">'+n.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Di(e){const n=document.getElementById("bank-upload-progress");n&&(n.style.display="none")}function Fi(){const e=document.getElementById("bank-upload-error");e&&(e.style.display="none")}function qi(e){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[e]||t("bank-err-unknown")+" ("+e+")"}function Ue(e){if(e==null)return"-";const n=Number(e);return isNaN(n)?"-":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function ct(e){if(!e)return"-";const n=String(e);return n.length>=10?n.slice(0,10):n}function fo(e,n){return!e&&!n?"":(ct(e)||"?")+" ~ "+(ct(n)||"?")}function Z(e){return e==null?"":String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}async function Ri(e){j.currentTxForDrawer=e;const n=document.getElementById("bank-detail-body");n&&n.classList.add("has-pane");const a=document.getElementById("bank-cand-pane-title"),o=document.getElementById("bank-cand-pane-sub"),s=document.getElementById("bank-cand-pane-foot");if(a&&(a.textContent=t("bank-cand-pane-current")),o){const r=e.direction==="OUT"?"-":"+",c=e.direction==="OUT"?"bank-out":"bank-in";o.innerHTML=`${Z(ct(e.tx_date))}
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <span>${Z(e.description||"-")}</span>
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <strong class="${c}">${r}${Ue(e.amount)}</strong>`}s&&(s.style.display="");const i=document.getElementById("bank-cand-pane-body");if(i){i.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const r=await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!r.ok)throw new Error("cands:"+r.status);const c=await r.json();Ni(e,c.candidates||[])}catch{i.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function zi(e,n,a){const o=n.history_id,s=n.invoice_no||"-",i=n.vendor||"-",r=n.amount_total!==null&&n.amount_total!==void 0?Ue(n.amount_total):"-",c=n.invoice_date?ct(n.invoice_date):"-",m=n.filename||"",p=!!a&&e.matched_history_id===o,u="bank-cand-card"+(n.is_auto_picked?" is-auto":"")+(p?" is-picked":"");let l="";return p?l='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":l='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+Z(o)+'"><span>'+t(n.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+u+'" data-hid="'+Z(o)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+Z(i)+"</div>"+Pi(n.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+Z(s)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+r+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+Z(c)+"</span></div>"+(m?'<div class="bank-cand-card-file" title="'+Z(m)+'">'+Z(m)+"</div>":"")+(n.reason?'<div class="bank-cand-card-reason">'+Z(n.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+l+"</div></div>"}function Ni(e,n){const a=document.getElementById("bank-cand-pane-body");if(!a)return;const o=n||[];let s="";if(e.match_status==="matched")s='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",o.length)+"</div>";else if(e.match_status==="suggested")s='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",o.length)+"</div>";else if(o.length>0)s='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",o.length)+"</div>";else{a.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const i=e.match_status==="matched",r=o.map(c=>zi(e,c,i)).join("");a.innerHTML=s+'<div class="bank-cand-list">'+r+"</div>",a.querySelectorAll('[data-act="pick"]').forEach(c=>{c.addEventListener("click",()=>{Ui(c.dataset.hid)})}),a.querySelectorAll('[data-act="unmatch"]').forEach(c=>{c.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),Mt(),await ut(j.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function Mt(){const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane");const n=document.getElementById("bank-cand-pane-title"),a=document.getElementById("bank-cand-pane-sub"),o=document.getElementById("bank-cand-pane-body"),s=document.getElementById("bank-cand-pane-foot");n&&(n.textContent=t("bank-cand-pane-empty-title")),a&&(a.textContent=t("bank-cand-pane-empty-sub")),s&&(s.style.display="none"),o&&(o.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const i=document.getElementById("bank-tx-tbody");i&&i.querySelectorAll("tr.is-selected").forEach(r=>r.classList.remove("is-selected")),j.currentTxForDrawer=null}async function ut(e){try{const n="/api/bank-recon/sessions/"+encodeURIComponent(e)+(j.currentFilter!=="all"?"?filter="+j.currentFilter:""),a=await fetch(n,{headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("detail:"+a.status);const o=await a.json();j.currentSession=o.session,j.currentTxs=o.transactions||[],Zi()}catch(n){console.warn("[bank-recon] loadSessionDetail failed",n),showToast(t("bank-load-failed"),"error")}}async function Oi(){if(!j.currentSession)return;const e=document.getElementById("btn-bank-run-match"),n=e.innerHTML;e.disabled=!0,e.innerHTML="<span>"+t("bank-matching")+"</span>";try{const a=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(j.currentSession.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("match:"+a.status);const o=await a.json();showToast(t("bank-match-done").replace("{matched}",o.matched).replace("{suggested}",o.suggested).replace("{unmatched}",o.unmatched),"success"),await ut(j.currentSession.id),await ft()}catch(a){console.warn("[bank-recon] match failed",a),showToast(t("bank-match-failed"),"error")}finally{e.disabled=!1,e.innerHTML=n}}async function Vi(){if(!(!j.currentSession||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const n=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(j.currentSession.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!n.ok)throw new Error("delete:"+n.status);showToast(t("bank-deleted"),"success"),j.currentSession=null,j.currentTxs=[],Un(),await ft()}catch(n){console.warn("[bank-recon] delete failed",n),showToast(t("bank-delete-failed"),"error")}}async function ga(){if(j.currentTxForDrawer)try{const e=await fetch("/api/bank-recon/tx/"+encodeURIComponent(j.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!e.ok)throw new Error("ignore:"+e.status);Mt(),await ut(j.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}async function Ui(e){if(j.currentTxForDrawer)try{const n=await fetch("/api/bank-recon/tx/"+encodeURIComponent(j.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:e})});if(!n.ok)throw new Error("pick:"+n.status);showToast(t("bank-matched-ok"),"success"),Mt(),await ut(j.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}function mo(){if(!j.currentSession)return;const e=j.currentSession;document.getElementById("bank-detail-title").textContent=(e.bank_code||"-")+(e.account_last4?" ···"+e.account_last4:"")+" · "+(e.source_filename||""),document.getElementById("bank-meta-period").textContent=fo(e.period_start,e.period_end)||"-",document.getElementById("bank-meta-opening").textContent=Ue(e.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+Ue(e.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+Ue(e.total_outflow),document.getElementById("bank-meta-closing").textContent=Ue(e.closing_balance);const n=j.currentTxs||[],a=n.length;let o=0,s=0,i=0;for(const r of n){const c=r.match_status||"unmatched";c==="matched"?o++:c==="suggested"?s++:i++}document.getElementById("bank-stat-total").textContent=a,document.getElementById("bank-stat-matched").textContent=o,document.getElementById("bank-stat-suggested").textContent=s,document.getElementById("bank-stat-unmatched").textContent=i}function On(){const e=document.getElementById("bank-tx-tbody");if(!e)return;let n=j.currentTxs||[];if(j.currentFilter!=="all"&&(n=n.filter(a=>j.currentFilter==="matched"?a.match_status==="matched":j.currentFilter==="suggested"?a.match_status==="suggested":j.currentFilter==="unmatched"?a.match_status==="unmatched"||a.match_status==="ignored":!0)),n.length===0){e.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(e.innerHTML=n.map(a=>Gi(a)).join(""),e.querySelectorAll("tr[data-tx-id]").forEach(a=>{a.addEventListener("click",()=>{const o=a.dataset.txId,s=j.currentTxs.find(i=>i.id===o);s&&(e.querySelectorAll("tr.is-selected").forEach(i=>i.classList.remove("is-selected")),a.classList.add("is-selected"),Ri(s))})}),j.currentTxForDrawer){const a=e.querySelector('tr[data-tx-id="'+j.currentTxForDrawer.id+'"]');a&&a.classList.add("is-selected")}}function Gi(e){const n=e.direction==="OUT",a=n?"-":"+",o=n?"bank-out":"bank-in",s=e.match_status||"unmatched",i=t("bank-match-"+s)||s,r=ct(e.tx_date),c=e.channel?`<span class="bank-tx-channel">${Z(e.channel)}</span>`:"";return`
        <tr data-tx-id="${Z(e.id)}">
            <td class="bank-tx-date">${Z(r)}</td>
            <td class="bank-tx-desc">${c}${Z(e.description||"-")}</td>
            <td class="bank-td-amount ${o}">${a}${Ue(e.amount)}</td>
            <td><span class="bank-tx-match mt-${s}">${Z(i)}</span></td>
        </tr>
    `}function Vn(){const e=document.getElementById("bank-client-badge");if(!e||!j.currentSession)return;const n=j.currentSession.client_id,a=document.getElementById("bank-client-badge-dot"),o=document.getElementById("bank-client-badge-name"),s=document.getElementById("bank-client-badge-caret"),i=typeof _userInfo<"u"?_userInfo:null,r=!(i&&i.role==="member");if(n!=null){const c=(window._clientsCache||[]).find(m=>Number(m.id)===Number(n));e.classList.remove("is-empty"),a&&(a.style.background=c&&c.color||"#111111"),o&&(o.textContent=c&&(c.short_name||c.name)||"#"+n)}else e.classList.add("is-empty"),a&&(a.style.background=""),o&&(o.textContent=t("bank-client-none"));r?(e.classList.remove("is-readonly"),e.disabled=!1,s&&(s.style.display="")):(e.classList.add("is-readonly"),e.disabled=!0,s&&(s.style.display="none")),e.style.display=""}function Ki(){if(!j.currentSession)return;const e=typeof _userInfo<"u"?_userInfo:null;if(!!(e&&e.role==="member"))return;j.pickerSelected=j.currentSession.client_id!=null?Number(j.currentSession.client_id):null,ho();const a=document.getElementById("bank-client-picker-modal");a&&(a.style.display="")}function vo(){const e=document.getElementById("bank-client-picker-modal");e&&(e.style.display="none"),j.pickerSelected=null}function ho(){const e=document.getElementById("bank-client-picker-list");if(!e)return;const n=(window._clientsCache||[]).filter(o=>o&&(o.is_active===!0||o.is_active===void 0)),a=[];a.push('<div class="bank-client-picker-row is-none'+(j.pickerSelected==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+Z(t("bank-client-picker-none"))+"</span></div>"),n.forEach(o=>{const s=Number(o.id)===Number(j.pickerSelected)?" is-selected":"";a.push('<div class="bank-client-picker-row'+s+'" data-cid="'+Z(o.id)+'"><span class="bank-cp-dot" style="background:'+Z(o.color||"#111111")+'"></span><span>'+Z(o.short_name||o.name||"#"+o.id)+"</span></div>")}),e.innerHTML=a.join(""),e.querySelectorAll(".bank-client-picker-row").forEach(o=>{o.addEventListener("click",()=>{const s=o.dataset.cid;j.pickerSelected=s?Number(s):null,ho()})})}async function Ji(){if(j.currentSession)try{const e=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(j.currentSession.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:j.pickerSelected})});if(!e.ok)throw new Error("client:"+e.status);j.currentSession.client_id=j.pickerSelected,Vn(),showToast(t("bank-client-changed"),"success"),vo();try{await ft()}catch{}}catch(e){console.warn("[bank-recon] save client failed",e),showToast(t("bank-client-change-failed"),"error")}}async function ft(){try{const e=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!e.ok)throw new Error("sessions:"+e.status);j.sessions=await e.json(),Wt()}catch(e){console.warn("[bank-recon] loadSessions failed",e),j.sessions=[],Wt()}}function ba(){const e=document.getElementById("bank-status-summary");if(!e)return;if(j.sessions.length===0){e.textContent=t("bank-pill-none");return}let a=0;for(const o of j.sessions)o.parse_status==="parsed"&&(o.unmatched_count||0)>0&&a++;e.textContent=a>0?t("bank-pill-pending").replace("{n}",a):t("bank-pill-ok")}function Wt(){const e=document.getElementById("bank-sessions-list");if(!e)return;let n=j.sessions||[];if(j.sessionFilter==="parsed"?n=n.filter(a=>a.parse_status==="parsed"):j.sessionFilter==="failed"&&(n=n.filter(a=>a.parse_status==="parse_failed")),!j.sessions||j.sessions.length===0){e.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(n.length===0){e.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}e.innerHTML=n.map(a=>Wi(a)).join(""),e.querySelectorAll(".bank-session-row").forEach(a=>{a.addEventListener("click",o=>{o.target.closest(".bank-session-trash")||ut(a.dataset.sessionId)})}),e.querySelectorAll(".bank-session-trash").forEach(a=>{a.addEventListener("click",o=>{o.stopPropagation();const s=a.dataset.sessionId,i=a.dataset.sessionName||"";go(s,i)})})}async function go(e,n){if(!e)return;const a=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",n||"");if(await showConfirm(a,{danger:!0}))try{const s=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(e),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!s.ok)throw new Error("delete:"+s.status);showToast(t("bank-deleted"),"success"),j.currentSession&&j.currentSession.id===e&&(j.currentSession=null,j.currentTxs=[],Un()),await ft(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(s){console.warn("[bank-recon] delete failed",s),showToast(t("bank-delete-failed"),"error")}}function Wi(e){const n=(e.bank_code||"OTHER").toUpperCase(),a=fo(e.period_start,e.period_end),o=e.account_last4?"···"+e.account_last4:"",s=Yi(e),i=ct(e.created_at);return`
        <div class="bank-session-row" data-session-id="${Z(e.id)}">
            <div class="bank-session-bank bk-${Z(n)}">${Z(n)}</div>
            <div class="bank-session-info">
                <div class="bank-session-title">${Z(e.source_filename||a||"-")}</div>
                <div class="bank-session-meta">${Z(a)} · ${Z(o)} · ${Z(i)}</div>
            </div>
            <div class="bank-session-counts">${s}</div>
            <button class="bank-session-trash" data-session-id="${Z(e.id)}" data-session-name="${Z(e.source_filename||"")}" title="${Z(t("bank-session-delete-tip")||"删除")}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                </svg>
            </button>
            <div class="bank-session-arrow">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
            </div>
        </div>
    `}function Yi(e){if(e.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(e.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const n=e.tx_count||0,a=e.matched_count||0,o=e.unmatched_count||0,s=[`<span class="bank-session-count">${n} ${t("bank-count-tx")}</span>`];return a>0&&s.push(`<span class="bank-session-count cnt-matched">${a} ${t("bank-count-matched")}</span>`),o>0&&s.push(`<span class="bank-session-count cnt-unmatched">${o} ${t("bank-count-unmatched")}</span>`),s.join("")}function Zi(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",mo(),On(),Vn()}function Un(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane"),j.currentTxForDrawer=null}const Xi=3;function Qi(){return j.qSeq+=1,"q"+j.qSeq+"_"+Date.now()}async function er(e){const n=Array.from(e.target.files||[]);if(e.target.value="",n.length!==0){for(const a of n){const o={id:Qi(),file:a,name:a.name,size:a.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};a.name.toLowerCase().endsWith(".pdf")?a.size>20*1024*1024&&(o.status="failed",o.error_code="bank_recon.file_too_large"):(o.status="failed",o.error_code="bank_recon.only_pdf"),j.queue.push(o)}tr(),we(),Gn()}}function tr(){const e=document.getElementById("bank-upload-queue");e&&(e.style.display=""),Di(),Fi()}function we(){const e=document.getElementById("bank-upload-queue-list"),n=document.getElementById("bank-upload-queue-summary");if(!e)return;if(j.queue.length===0){e.innerHTML="",n&&(n.textContent="");const r=document.getElementById("bank-upload-queue");r&&(r.style.display="none");return}let a=0,o=0,s=0,i=0;for(const r of j.queue)r.status==="ok"?a++:r.status==="failed"?o++:r.status==="uploading"||r.status==="parsing"?s++:i++;n&&(n.textContent=t("bank-queue-summary").replace("{ok}",a).replace("{run}",s).replace("{wait}",i).replace("{fail}",o)),e.innerHTML=j.queue.map(nr).join(""),e.querySelectorAll("[data-q-act]").forEach(r=>{const c=r.dataset.qAct,m=r.dataset.qId;r.addEventListener("click",()=>{c==="retry"&&ar(m),c==="remove"&&or(m)})})}function nr(e){const n=(e.size/1024).toFixed(0)+" KB";let a="",o="";if(e.status==="pending")a='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",o='<button data-q-act="remove" data-q-id="'+Z(e.id)+'" class="bq-act">×</button>';else if(e.status==="uploading")a='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(e.progress||0)+'%"></div></div>';else if(e.status==="parsing")a='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(e.status==="ok")a='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",e.tx_count||0)+"</span>",o='<button data-q-act="remove" data-q-id="'+Z(e.id)+'" class="bq-act">×</button>';else if(e.status==="failed"){const s=qi(e.error_code||"unknown");a='<span class="bq-stat bq-fail" title="'+Z(s)+'">'+Z(s)+"</span>",o='<button data-q-act="retry" data-q-id="'+Z(e.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+Z(e.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+Z(e.id)+'"><div class="bq-name" title="'+Z(e.name)+'">'+Z(e.name)+'</div><div class="bq-size">'+n+'</div><div class="bq-status">'+a+'</div><div class="bq-actions">'+o+"</div></div>"}function ar(e){const n=j.queue.find(a=>a.id===e);n&&(n.status="pending",n.error_code=null,n.progress=0,we(),Gn())}function or(e){const n=j.queue.findIndex(o=>o.id===e);if(n<0)return;const a=j.queue[n];a.status==="uploading"||a.status==="parsing"||(j.queue.splice(n,1),we())}function sr(){j.queue=j.queue.filter(e=>e.status!=="ok"),we()}async function Gn(){for(;;){if(j.queue.filter(a=>a.status==="uploading"||a.status==="parsing").length>=Xi)return;const n=j.queue.find(a=>a.status==="pending");if(!n){j.queue.every(a=>a.status==="ok"||a.status==="failed")&&(await ft(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}ir(n).then(()=>Gn())}}async function ir(e){e.status="uploading",e.progress=0,we();try{const n=new FormData;n.append("file",e.file,e.name);const a=await new Promise((s,i)=>{const r=new XMLHttpRequest;r.open("POST","/api/bank-recon/upload"),r.setRequestHeader("Authorization","Bearer "+token),r.upload.onprogress=c=>{c.lengthComputable&&(e.progress=Math.min(99,Math.round(c.loaded/c.total*100)),we())},r.upload.onload=()=>{e.status="parsing",we()},r.onload=()=>{r.status>=200&&r.status<300?s({status:r.status,text:r.responseText}):s({status:r.status,text:r.responseText})},r.onerror=()=>i(new Error("network")),r.send(n)});let o={};try{o=JSON.parse(a.text||"{}")}catch{o={}}if(a.status>=400){e.status="failed",e.error_code=o&&o.detail||"unknown",we();return}if(o.parse_status==="parse_failed"){e.status="failed",e.error_code=o.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",we();return}e.status="ok",e.tx_count=o.tx_count||0,e.session_id=o.session_id||null,we()}catch(n){console.warn("[bank-recon] upload failed",n),e.status="failed",e.error_code="network",we()}}async function bo(){if(j.loaded){ba();return}j.loaded=!0,rr(),await ft(),ba()}function rr(){const e=document.getElementById("bank-file-input");e&&!e._bound&&(e._bound=!0,e.addEventListener("change",er));const n=document.getElementById("btn-bank-queue-clear-done");n&&!n._bound&&(n._bound=!0,n.addEventListener("click",sr));const a=document.getElementById("btn-bank-back");a&&!a._bound&&(a._bound=!0,a.addEventListener("click",()=>{j.currentSession=null,j.currentTxs=[],Un()}));const o=document.getElementById("btn-bank-delete");o&&!o._bound&&(o._bound=!0,o.addEventListener("click",Vi));const s=document.getElementById("btn-bank-run-match");s&&!s._bound&&(s._bound=!0,s.addEventListener("click",Oi)),document.querySelectorAll(".bank-filter-btn").forEach(u=>{u._bound||(u._bound=!0,u.addEventListener("click",()=>{j.currentFilter=u.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(l=>{l.classList.toggle("active",l===u)}),On()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(u=>{u._bound||(u._bound=!0,u.addEventListener("click",Mt))});const i=document.getElementById("btn-bank-cand-pane-close");i&&!i._bound&&(i._bound=!0,i.addEventListener("click",Mt));const r=document.getElementById("btn-bank-cand-ignore");r&&!r._bound&&(r._bound=!0,r.addEventListener("click",ga));const c=document.getElementById("btn-bank-cand-ignore-pane");c&&!c._bound&&(c._bound=!0,c.addEventListener("click",ga));const m=document.getElementById("bank-client-badge");m&&!m._bound&&(m._bound=!0,m.addEventListener("click",Ki)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(u=>{u._bound||(u._bound=!0,u.addEventListener("click",vo))});const p=document.getElementById("btn-bank-client-picker-save");p&&!p._bound&&(p._bound=!0,p.addEventListener("click",Ji)),document.querySelectorAll(".bank-sessions-chip").forEach(u=>{u._bound||(u._bound=!0,u.addEventListener("click",()=>{j.sessionFilter=u.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(l=>{l.classList.toggle("active",l===u)}),Wt()}))})}window._deleteBankSession=go;window._loadBankReconPanel=bo;window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(Wt(),j.currentSession&&(mo(),On(),Vn(),!j.currentTxForDrawer)){const e=document.getElementById("bank-cand-pane-title"),n=document.getElementById("bank-cand-pane-sub");e&&(e.textContent=t("bank-cand-pane-empty-title")),n&&(n.textContent=t("bank-cand-pane-empty-sub"))}we()}};typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon);window._openBankSession=async function(e){e&&(j.loaded||await bo(),await ut(e))};(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 00-3-3.87"/>
                    <path d="M16 3.13a4 4 0 010 7.75"/>
                </svg>
            </div>
            <div class="page-head-text">
                <h1 class="page-title" data-i18n="clients-title">客户管理</h1>
                <div class="page-subtitle" data-i18n="clients-sub">账套主体 + 买方客户 · 统一归档管理</div>
            </div>
        </div>

        <!-- 顶部横向 tab 条(对账中心同款)· 账套主体 / 买方客户 -->
        <div class="recon-tab-bar cust-tab-bar">
            <button class="recon-tab-btn active" data-cust-tab="seller" data-i18n="cust-tab-seller">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg>
                账套主体
            </button>
            <button class="recon-tab-btn" data-cust-tab="buyer" data-i18n="cust-tab-buyer">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M11 14v-1.2a2.4 2.4 0 00-2.4-2.4H4.4A2.4 2.4 0 002 12.8V14"/><circle cx="6.2" cy="5.2" r="2.4"/><path d="M14 14v-1.2a2.4 2.4 0 00-1.8-2.3"/></svg>
                买方客户
            </button>
        </div>

        <!-- ── 账套主体面板(= 工作空间 · 与右上角切换器/登录弹窗共用同一份)── -->
        <div id="cust-pane-seller" class="cust-pane active">
            <div class="cust-toolbar">
                <div class="search-wrap cust-search-wrap">
                    <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/></svg>
                    <input type="text" id="seller-search" class="search-input" data-i18n-placeholder="seller-search-ph" placeholder="搜索账套主体…">
                    <button class="search-clear" id="seller-search-clear" style="display:none;">&times;</button>
                </div>
                <button class="btn btn-primary" id="btn-seller-new" style="display:none;">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10M3 8h10"/></svg>
                    <span data-i18n="seller-new">新建账套主体</span>
                </button>
            </div>
            <div class="cust-hint" data-i18n="seller-hint">账套主体 = 你的公司(发票卖方 / 开票方)。这里与右上角切换器、登录弹窗共用同一份数据,任意处新建/修改都会同步。</div>
            <div class="cust-table-wrap">
                <div class="cust-table-head seller-grid">
                    <div data-i18n="seller-col-name">账套主体</div>
                    <div data-i18n="seller-col-tax">税号</div>
                    <div class="align-right" data-i18n="seller-col-count">发票数</div>
                    <div class="align-right" data-i18n="seller-col-actions">操作</div>
                </div>
                <div id="seller-tbody"><div class="cust-loading" data-i18n="clients-loading">加载中…</div></div>
            </div>
        </div>

        <!-- ── 买方客户面板(横条列表 · 搜索/多选/批删/翻页 · 识别记录同款)── -->
        <div id="cust-pane-buyer" class="cust-pane">
            <div class="cust-toolbar">
                <div class="search-wrap cust-search-wrap">
                    <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/></svg>
                    <input type="text" id="buyer-search" class="search-input" data-i18n-placeholder="buyer-search-ph" placeholder="搜索买方客户 / 税号…">
                    <button class="search-clear" id="buyer-search-clear" style="display:none;">&times;</button>
                </div>
                <button class="btn btn-primary" id="btn-buyer-new">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10M3 8h10"/></svg>
                    <span data-i18n="buyer-new">新建买方客户</span>
                </button>
            </div>
            <div id="buyer-batch-bar" class="cust-batch-bar" style="display:none;">
                <span class="cust-batch-count" id="buyer-batch-count"></span>
                <div class="cust-batch-actions">
                    <button class="btn btn-ghost btn-sm" id="buyer-batch-cancel" data-i18n="cust-batch-cancel">取消</button>
                    <button class="btn btn-danger btn-sm" id="buyer-batch-delete" data-i18n="cust-batch-delete">批量删除</button>
                </div>
            </div>
            <div class="cust-table-wrap">
                <div class="cust-table-head buyer-grid">
                    <div class="cust-col-check"><input type="checkbox" id="buyer-check-all"></div>
                    <div data-i18n="buyer-col-name">客户名称</div>
                    <div class="align-right" data-i18n="buyer-col-count">发票数</div>
                    <div class="align-right" data-i18n="buyer-col-amount">金额合计</div>
                    <div class="align-right" data-i18n="buyer-col-actions">操作</div>
                </div>
                <div id="buyer-tbody"><div class="cust-loading" data-i18n="clients-loading">加载中…</div></div>
            </div>
            <div class="cust-foot">
                <span class="cust-pager-info" id="buyer-pager-info"></span>
                <div class="cust-pager-btns">
                    <button class="btn btn-ghost btn-sm" id="buyer-prev" data-i18n="cust-prev">上一页</button>
                    <button class="btn btn-ghost btn-sm" id="buyer-next" data-i18n="cust-next">下一页</button>
                </div>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const lr=`
        <div class="modal client-modal" role="dialog">
            <div class="modal-header">
                <div class="modal-title" id="client-modal-title" data-i18n="client-modal-new">新建客户</div>
                <button class="modal-close" id="client-modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-row">
                    <label data-i18n="client-field-name">客户名称 *</label>
                    <input type="text" id="client-input-name" maxlength="200" data-i18n-placeholder="client-field-name-ph">
                </div>
                <div class="form-row form-row-2col">
                    <div>
                        <label data-i18n="client-field-short">简称</label>
                        <input type="text" id="client-input-short" maxlength="80">
                    </div>
                    <div>
                        <label data-i18n="client-field-tax">税号</label>
                        <input type="text" id="client-input-tax" maxlength="20">
                    </div>
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-address">地址</label>
                    <input type="text" id="client-input-address" maxlength="500">
                </div>
                <div class="form-row form-row-2col">
                    <div>
                        <label data-i18n="client-field-contact">联系人</label>
                        <input type="text" id="client-input-contact" maxlength="100">
                    </div>
                    <div>
                        <label data-i18n="client-field-phone">电话</label>
                        <input type="text" id="client-input-phone" maxlength="50">
                    </div>
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-email">邮箱</label>
                    <input type="email" id="client-input-email" maxlength="200">
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-color">标识颜色</label>
                    <div class="color-picker" id="client-color-picker">
                        <span class="color-swatch active" data-color="#111111" style="background:#111111"></span>
                        <span class="color-swatch" data-color="#ef4444" style="background:#ef4444"></span>
                        <span class="color-swatch" data-color="#f59e0b" style="background:#f59e0b"></span>
                        <span class="color-swatch" data-color="#10b981" style="background:#10b981"></span>
                        <span class="color-swatch" data-color="#8b5cf6" style="background:#8b5cf6"></span>
                        <span class="color-swatch" data-color="#ec4899" style="background:#ec4899"></span>
                        <span class="color-swatch" data-color="#06b6d4" style="background:#06b6d4"></span>
                        <span class="color-swatch" data-color="#6b7280" style="background:#6b7280"></span>
                    </div>
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-notes">备注</label>
                    <textarea id="client-input-notes" maxlength="1000" rows="2"></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-danger client-modal-delete-btn" id="client-modal-delete" style="display:none;">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3a1 1 0 011-1h2a1 1 0 011 1v2M5 5l1 9a1 1 0 001 1h2a1 1 0 001-1l1-9"/>
                    </svg>
                    <span data-i18n="client-delete">删除客户</span>
                </button>
                <div class="modal-footer-right">
                    <button class="btn btn-ghost" id="client-modal-cancel" data-i18n="client-cancel">取消</button>
                    <button class="btn btn-primary" id="client-modal-save" data-i18n="client-save">保存</button>
                </div>
            </div>
        </div>
    `,cr=`
        <div class="modal" role="dialog" style="max-width:440px;">
            <div class="modal-header">
                <div class="modal-title" id="wsclient-modal-title" data-i18n="wsclient-modal-new">新建账套主体</div>
                <button class="modal-close" id="wsclient-modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-row">
                    <label data-i18n="wsclient-field-name">账套主体名称 *</label>
                    <input type="text" id="wsclient-input-name" maxlength="200" data-i18n-placeholder="wsclient-field-name-ph" placeholder="公司名称,例如 BAKELAB">
                </div>
                <div class="form-row">
                    <label data-i18n="wsclient-field-tax">税号</label>
                    <input type="text" id="wsclient-input-tax" maxlength="30">
                </div>
                <div class="wsclient-modal-note" data-i18n="wsclient-note">账套主体 = 你的公司(发票卖方)。它和右上角切换器、登录弹窗共用,这里改了那边同步。</div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-danger" id="wsclient-modal-archive" style="display:none;">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h12M4 4v9a1 1 0 001 1h6a1 1 0 001-1V4M6 4V2.5a1 1 0 011-1h2a1 1 0 011 1V4"/></svg>
                    <span data-i18n="wsclient-archive">归档</span>
                </button>
                <div class="modal-footer-right">
                    <button class="btn btn-ghost" id="wsclient-modal-cancel" data-i18n="client-cancel">取消</button>
                    <button class="btn btn-primary" id="wsclient-modal-save" data-i18n="client-save">保存</button>
                </div>
            </div>
        </div>
    `;ve("client-modal-mask",lr);ve("wsclient-modal-mask",cr);const J={clients:[],editingClientId:null,historyClientFilter:"",custTab:"seller",sellerClients:[],editingWsClientId:null,catCache:{fetched:0,items:[],supplier_count:0}},fe={page:0,pageSize:12,keyword:""},Se=new Set,Yt={keyword:""};function dr(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function Ee(e,n={}){const a=await fetch(e,{...n,headers:{"Content-Type":"application/json",...dr(),...n.headers||{}}});if(!a.ok){const o=await a.json().catch(()=>({}));throw new Error(o.detail||"HTTP "+a.status)}return a.json()}function pr(){const e=document.querySelector("#client-color-picker .color-swatch.active");return e?e.dataset.color:"#111111"}function ya(e){const n=document.getElementById("drawer-cat-learned-tag");n&&e>0&&(n.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",e))}async function mt(){try{const e=await Ee("/api/clients");J.clients=e.clients||[],window._clientsCache=J.clients}catch(e){console.error("loadClientsCache fail",e),J.clients=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return J.clients}function ur(){const e=fe.keyword.trim().toLowerCase();return e?J.clients.filter(n=>(n.name||"").toLowerCase().includes(e)||(n.short_name||"").toLowerCase().includes(e)||(n.tax_id||"").toLowerCase().includes(e)):J.clients}function Kn(){const e=ur(),n=fe.pageSize,a=Math.max(0,Math.ceil(e.length/n)-1);fe.page>a&&(fe.page=a);const o=fe.page*n;return{all:e,items:e.slice(o,o+n),start:o,ps:n,total:e.length,maxPage:a}}function Le(){const e=document.getElementById("buyer-tbody");if(!e)return;const{items:n,start:a,ps:o,total:s,maxPage:i}=Kn();s?e.innerHTML=n.map(p=>{const u=Se.has(p.id);return`<div class="cust-row buyer-grid${u?" selected":""}" data-cid="${p.id}">
                <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${p.id}" ${u?"checked":""}></div>
                <div style="min-width:0">
                    <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(p.color||"#111")}"></span><span class="cust-name-text">${escapeHtml(p.name)}</span></div>
                    ${p.tax_id?`<div class="cust-cell-sub">${escapeHtml(p.tax_id)}</div>`:""}
                </div>
                <div class="align-right">${p.invoice_count||0}</div>
                <div class="align-right cust-cell-amount">฿${(p.total_amount||0).toLocaleString(void 0,{maximumFractionDigits:0})}</div>
                <div class="cust-row-actions">
                    <button class="cust-row-btn" data-action="edit" data-cid="${p.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                    <button class="cust-row-btn" data-action="export" data-cid="${p.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t("client-card-export"))}</span></button>
                </div>
            </div>`}).join(""):e.innerHTML=`<div class="cust-empty">${escapeHtml(t(fe.keyword?"cust-no-match":"clients-empty"))}</div>`;const r=document.getElementById("buyer-pager-info");r&&(r.textContent=s?`${a+1}–${Math.min(a+o,s)} / ${s}`:"0");const c=document.getElementById("buyer-prev");c&&(c.disabled=fe.page<=0);const m=document.getElementById("buyer-next");m&&(m.disabled=fe.page>=i),yo()}function yo(){const e=Se.size,n=document.getElementById("buyer-batch-bar");n&&(n.style.display=e?"flex":"none");const a=document.getElementById("buyer-batch-count");a&&(a.textContent=t("cust-selected-n").replace("{n}",e));const o=document.getElementById("buyer-check-all");if(o){const{items:s}=Kn(),i=s.map(c=>c.id),r=i.filter(c=>Se.has(c)).length;o.checked=i.length>0&&r===i.length,o.indeterminate=r>0&&r<i.length}}function fr(){Se.clear(),Le()}async function mr(){const e=Array.from(Se);if(!(!e.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",e.length),{danger:!0})))try{await Ee("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:e})}),showToast(t("client-msg-deleted"),"success"),Se.clear(),await mt(),Le(),cn(),Jn()}catch{showToast(t("client-msg-save-fail"),"fail")}}function Et(e){J.editingClientId=e?e.id:null;const n=!!e;document.getElementById("client-modal-title").textContent=t(n?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=e&&e.name||"",document.getElementById("client-input-short").value=e&&e.short_name||"",document.getElementById("client-input-tax").value=e&&e.tax_id||"",document.getElementById("client-input-address").value=e&&e.address||"",document.getElementById("client-input-contact").value=e&&e.contact_person||"",document.getElementById("client-input-phone").value=e&&e.contact_phone||"",document.getElementById("client-input-email").value=e&&e.contact_email||"",document.getElementById("client-input-notes").value=e&&e.notes||"";const a=e&&e.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(o=>{o.classList.toggle("active",o.dataset.color===a)}),document.getElementById("client-modal-delete").style.display=n?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function Bt(){document.getElementById("client-modal-mask").style.display="none",J.editingClientId=null}async function vr(){const e=document.getElementById("client-input-name").value.trim();if(!e){showToast(t("client-msg-name-required"),"fail");return}const n={name:e,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:pr()};try{J.editingClientId?(await Ee(`/api/clients/${J.editingClientId}`,{method:"PATCH",body:JSON.stringify(n)}),showToast(t("client-msg-updated"),"success")):(await Ee("/api/clients",{method:"POST",body:JSON.stringify(n)}),showToast(t("client-msg-created"),"success")),Bt(),await mt(),currentRoute==="clients"&&Le(),cn(),Jn()}catch(a){console.error("saveClient fail",a);const o=a&&a.message?a.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+o,"fail")}}async function hr(){if(!J.editingClientId)return;const e=J.clients.find(o=>o.id===J.editingClientId);if(!e)return;const n=t("client-delete-confirm").replace("{name}",e.name);if(await showConfirm(n,{danger:!0}))try{await Ee(`/api/clients/${J.editingClientId}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),Bt(),await mt(),currentRoute==="clients"&&Le(),cn(),Jn()}catch(o){console.error(o),showToast(t("client-msg-save-fail"),"fail")}}async function gr(e){const n=J.clients.find(a=>a.id===e);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(e,n?n.name:"");return}try{const a=localStorage.getItem("mrpilot_token"),o=await fetch(`/api/clients/${e}/export?month=all`,{headers:{Authorization:"Bearer "+a}});if(!o.ok){let m="HTTP "+o.status;try{const p=await o.json();p&&p.detail&&(m=p.detail)}catch{}throw new Error(m)}const s=await o.blob();if(s.size<200){showToast(t("client-export-month-empty"),"info");return}const i=n&&n.name?n.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",r=URL.createObjectURL(s),c=document.createElement("a");c.href=r,c.download=`${i}_export.csv`,c.click(),URL.revokeObjectURL(r)}catch(a){console.error("exportClient fail",a),showToast(t("client-msg-save-fail")+" · "+(a.message||""),"fail")}}function cn(){const e=document.getElementById("drawer-client-select");if(!e)return;const n=e.value;e.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+J.clients.map(a=>`<option value="${a.id}">${escapeHtml(a.name)}</option>`).join(""),e.value=n||""}function Jn(){const e=document.getElementById("history-client-filter");if(!e)return;const n=e.value;e.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+J.clients.map(a=>`<option value="${a.id}">${escapeHtml(a.name)}</option>`).join(""),e.value=n||""}function br(e){J.custTab=e==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(o=>o.classList.toggle("active",o.dataset.custTab===J.custTab));const n=document.getElementById("cust-pane-seller"),a=document.getElementById("cust-pane-buyer");n&&n.classList.toggle("active",J.custTab==="seller"),a&&a.classList.toggle("active",J.custTab==="buyer")}function yr(){const e=window._userInfo||{},n=String(e.role||"").toLowerCase(),a=String(e.tenant_role||"").toLowerCase();return e.is_super_admin===!0||e.is_owner===!0||n==="owner"||n==="admin"||a==="owner"||a==="admin"}function wo(){window._workspaceClientsCache=J.sellerClients,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function Wn(){try{const e=await Ee("/api/workspace/clients");J.sellerClients=e&&(e.clients||e.items)||[],window._workspaceClientsCache=J.sellerClients}catch(e){console.error("loadSellerCache fail",e),J.sellerClients=[]}return J.sellerClients}function wr(){const e=Yt.keyword.trim().toLowerCase();return e?J.sellerClients.filter(n=>(n.name||"").toLowerCase().includes(e)||(n.tax_id||"").toLowerCase().includes(e)):J.sellerClients}function Ke(){const e=document.getElementById("seller-tbody");if(!e)return;const n=yr(),a=document.getElementById("btn-seller-new");a&&(a.style.display=n?"":"none");const o=wr(),s=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!o.length){e.innerHTML=`<div class="cust-empty">${escapeHtml(t(Yt.keyword?"cust-no-match":"seller-empty"))}</div>`;return}e.innerHTML=o.map(i=>{const c=s!=null&&Number(s)===Number(i.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${i.id}">${escapeHtml(t("seller-set-current"))}</button>`,m=n?`
            <button class="cust-row-btn" data-saction="edit" data-wid="${i.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
            <button class="cust-row-btn danger" data-saction="archive" data-wid="${i.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${i.id}">
            <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(i.name||"#"+i.id)}</span></div>
            <div class="cust-cell-tax">${escapeHtml(i.tax_id||"—")}</div>
            <div class="align-right">${i.invoice_count||0}</div>
            <div class="cust-row-actions">${c}${m}</div>
        </div>`}).join("")}function wa(e){J.editingWsClientId=e?e.id:null,document.getElementById("wsclient-modal-title").textContent=t(e?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=e&&e.name||"",document.getElementById("wsclient-input-tax").value=e&&e.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=e?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function It(){document.getElementById("wsclient-modal-mask").style.display="none",J.editingWsClientId=null}async function kr(){const e=document.getElementById("wsclient-input-name").value.trim(),n=document.getElementById("wsclient-input-tax").value.trim();if(!e){showToast(t("client-msg-name-required"),"fail");return}try{J.editingWsClientId?(await Ee("/api/workspace/clients/"+J.editingWsClientId,{method:"PATCH",body:JSON.stringify({name:e,tax_id:n})}),showToast(t("client-msg-updated"),"success")):(await Ee("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:e,tax_id:n||null})}),showToast(t("client-msg-created"),"success")),It(),await Wn(),Ke(),wo()}catch(a){const o=a&&a.message?a.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+o,"fail")}}async function ka(){if(!J.editingWsClientId)return;const e=J.sellerClients.find(a=>Number(a.id)===Number(J.editingWsClientId));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",e?e.name:""),{danger:!0}))try{const a=J.editingWsClientId;await Ee("/api/workspace/clients/"+a,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(a)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),It(),await Wn(),Ke(),wo()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const e=document.getElementById("seller-tbody");e&&(e.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const n=document.getElementById("buyer-tbody");n&&(n.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([Wn(),mt()]),Ke(),Le()};window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&Ke()});window.bindDrawerClient=function(e,n){const a=document.getElementById("drawer-client-select");if(!a)return;if(cn(),a.value=n?String(n):"",!e){a.onchange=null;const s=document.getElementById("drawer-client-add");s&&(s.onclick=()=>Et(null));return}a.onchange=async()=>{const s=a.value?parseInt(a.value,10):null;try{await Ee(`/api/history/${e}/assign_client`,{method:"POST",body:JSON.stringify({client_id:s})}),showToast(t("client-msg-updated"),"success");const i=_results[_drawerIdx];i&&(i.client_id=s),await mt()}catch(i){console.error(i),showToast(t("client-msg-save-fail"),"fail"),a.value=n?String(n):""}};const o=document.getElementById("drawer-client-add");o&&(o.onclick=()=>Et(null))};window.fillCategoryDatalist=async function(){try{const e=document.getElementById("drawer-cat-datalist"),n=Date.now();if(n-J.catCache.fetched<300*1e3){e&&(e.innerHTML=J.catCache.items.map(o=>`<option value="${escapeHtml(o)}">`).join("")),ya(J.catCache.supplier_count);return}const a=await Ee("/api/categories",{method:"GET"});J.catCache.fetched=n,J.catCache.items=a&&a.categories||[],J.catCache.supplier_count=a&&a.supplier_count||0,e&&(e.innerHTML=J.catCache.items.map(o=>`<option value="${escapeHtml(o)}">`).join("")),ya(J.catCache.supplier_count)}catch(e){console.warn("fillCategoryDatalist failed",e)}};window.getHistoryClientFilter=function(){return J.historyClientFilter};document.addEventListener("DOMContentLoaded",()=>{const e=document.querySelector(".cust-tab-bar");e&&e.addEventListener("click",I=>{const C=I.target.closest("[data-cust-tab]");C&&br(C.dataset.custTab)});const n=document.getElementById("btn-buyer-new");n&&n.addEventListener("click",()=>Et(null));const a=document.getElementById("buyer-tbody");a&&a.addEventListener("click",I=>{const C=I.target.closest(".buyer-row-check");if(C){const A=parseInt(C.dataset.cid,10);C.checked?Se.add(A):Se.delete(A);const V=C.closest(".cust-row");V&&V.classList.toggle("selected",C.checked),yo();return}const S=I.target.closest(".cust-row-btn");if(S){I.stopPropagation();const A=parseInt(S.dataset.cid,10);if(S.dataset.action==="edit"){const V=J.clients.find(T=>T.id===A);V&&Et(V)}else S.dataset.action==="export"&&gr(A);return}const q=I.target.closest(".cust-row");if(q&&!I.target.closest(".cust-cell-check")){const A=J.clients.find(V=>V.id===parseInt(q.dataset.cid,10));A&&Et(A)}});const o=document.getElementById("buyer-check-all");o&&o.addEventListener("change",()=>{const{items:I}=Kn();I.forEach(C=>{o.checked?Se.add(C.id):Se.delete(C.id)}),Le()});const s=document.getElementById("buyer-batch-cancel");s&&s.addEventListener("click",fr);const i=document.getElementById("buyer-batch-delete");i&&i.addEventListener("click",mr);const r=document.getElementById("buyer-prev");r&&r.addEventListener("click",()=>{fe.page>0&&(fe.page--,Le())});const c=document.getElementById("buyer-next");c&&c.addEventListener("click",()=>{fe.page++,Le()});const m=document.getElementById("buyer-search");if(m){let I;m.addEventListener("input",()=>{clearTimeout(I),I=setTimeout(()=>{fe.keyword=m.value,fe.page=0;const C=document.getElementById("buyer-search-clear");C&&(C.style.display=m.value?"":"none"),Le()},200)})}const p=document.getElementById("buyer-search-clear");p&&p.addEventListener("click",()=>{const I=document.getElementById("buyer-search");I&&(I.value=""),fe.keyword="",fe.page=0,p.style.display="none",Le()});const u=document.getElementById("btn-seller-new");u&&u.addEventListener("click",()=>wa(null));const l=document.getElementById("seller-tbody");l&&l.addEventListener("click",I=>{const C=I.target.closest("[data-saction]");if(!C)return;I.stopPropagation();const S=parseInt(C.dataset.wid,10),q=C.dataset.saction,A=J.sellerClients.find(V=>Number(V.id)===S);q==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(S),Ke(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",A?A.name:""),"success")):q==="edit"?A&&wa(A):q==="archive"&&(J.editingWsClientId=S,ka())});const d=document.getElementById("seller-search");if(d){let I;d.addEventListener("input",()=>{clearTimeout(I),I=setTimeout(()=>{Yt.keyword=d.value;const C=document.getElementById("seller-search-clear");C&&(C.style.display=d.value?"":"none"),Ke()},200)})}const f=document.getElementById("seller-search-clear");f&&f.addEventListener("click",()=>{const I=document.getElementById("seller-search");I&&(I.value=""),Yt.keyword="",f.style.display="none",Ke()});const v=document.getElementById("wsclient-modal-close");v&&v.addEventListener("click",It);const w=document.getElementById("wsclient-modal-cancel");w&&w.addEventListener("click",It);const g=document.getElementById("wsclient-modal-save");g&&g.addEventListener("click",kr);const b=document.getElementById("wsclient-modal-archive");b&&b.addEventListener("click",ka);const h=document.getElementById("wsclient-modal-mask");h&&h.addEventListener("click",I=>{I.target===h&&It()});const E=document.getElementById("client-modal-close");E&&E.addEventListener("click",Bt);const y=document.getElementById("client-modal-cancel");y&&y.addEventListener("click",Bt);const _=document.getElementById("client-modal-save");_&&_.addEventListener("click",vr);const k=document.getElementById("client-modal-delete");k&&k.addEventListener("click",hr);const x=document.getElementById("client-modal-mask");x&&x.addEventListener("click",I=>{I.target===x&&Bt()});const B=document.getElementById("client-color-picker");B&&B.addEventListener("click",I=>{const C=I.target.closest(".color-swatch");C&&(B.querySelectorAll(".color-swatch").forEach(S=>S.classList.remove("active")),C.classList.add("active"))});const L=document.getElementById("history-client-filter");L&&L.addEventListener("change",()=>{J.historyClientFilter=L.value,typeof renderHistoryList=="function"&&renderHistoryList()})});setTimeout(()=>mt(),1e3);(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
        <div class="page-head">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 3.4L3.6 16.5a1.5 1.5 0 001.3 2.3h14.2a1.5 1.5 0 001.3-2.3L13 3.4a1.5 1.5 0 00-2 0z"/>
                    <line x1="12" y1="9" x2="12" y2="14"/>
                    <circle cx="12" cy="16.8" r="0.8" fill="currentColor"/>
                </svg>
            </div>
            <div class="page-head-text">
                <h1 class="page-title" data-i18n="exc-title">异常栏</h1>
                <div class="page-subtitle" data-i18n="exc-sub">所有被规则拦截的单据集中复核 · 系统会从你的判断中学习</div>
            </div>
            <div class="page-head-actions">
                <select class="history-range" id="exc-client-filter">
                    <option value="" data-i18n="history-client-all">全部客户</option>
                </select>
                <button class="btn btn-ghost" id="btn-exc-refresh" type="button">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 8a5 5 0 019-3l1.5 1.5M13 8a5 5 0 01-9 3L2.5 9.5M13 3v3h-3M3 13v-3h3"/>
                    </svg>
                    <span data-i18n="exc-refresh">刷新</span>
                </button>
            </div>
        </div>

        <!-- ERP 推送异常块(独立来源 · Zihao 2026-05-26)· 派生自 erp_push_logs ·
             0 条时隐藏 · 内容(标题/chip/卡片)全由 JS renderErpExceptions 填充 -->
        <div class="erp-exc-block" id="erp-exc-block" hidden></div>

        <!-- 顶部 4 KPI -->
        <div class="exc-kpi-row" id="exc-kpi-row">
            <div class="exc-kpi">
                <div class="exc-kpi-value" id="exc-kpi-pending">—</div>
                <div class="exc-kpi-label" data-i18n="exc-kpi-pending">待复核</div>
            </div>
            <div class="exc-kpi exc-kpi-danger">
                <div class="exc-kpi-value" id="exc-kpi-high">—</div>
                <div class="exc-kpi-label" data-i18n="exc-kpi-high">高危异常</div>
            </div>
            <div class="exc-kpi">
                <div class="exc-kpi-value" id="exc-kpi-resolved">—</div>
                <div class="exc-kpi-label" data-i18n="exc-kpi-resolved">已处理</div>
            </div>
            <div class="exc-kpi">
                <div class="exc-kpi-value" id="exc-kpi-learned">—</div>
                <div class="exc-kpi-label" data-i18n="exc-kpi-learned">已学习规则</div>
            </div>
        </div>

        <!-- v118.21.1 · 状态切换(待复核 / 已处理 / 已忽略) -->
        <div class="exc-status-tabs" id="exc-status-tabs">
            <button class="exc-status-tab active" data-status="pending" type="button">
                <span data-i18n="exc-status-pending">待复核</span>
                <span class="exc-status-tab-count" id="exc-status-tab-count-pending">0</span>
            </button>
            <button class="exc-status-tab" data-status="resolved" type="button">
                <span data-i18n="exc-status-resolved">已处理</span>
                <span class="exc-status-tab-count" id="exc-status-tab-count-resolved">0</span>
            </button>
            <button class="exc-status-tab" data-status="ignored" type="button">
                <span data-i18n="exc-status-ignored">已忽略</span>
                <span class="exc-status-tab-count" id="exc-status-tab-count-ignored">0</span>
            </button>
        </div>

        <!-- 筛选 chips -->
        <div class="exc-chips" id="exc-chips">
            <!-- chips 由 JS 渲染(因为要带计数 · 且要根据 stats by_rule 动态显示) -->
        </div>

        <!-- v118.20.5 · 批量栏(选中 ≥1 时浮现) -->
        <div class="exc-batch-bar" id="exc-batch-bar" style="display:none;">
            <div class="exc-batch-info">
                <button class="exc-batch-clear" id="exc-batch-clear" type="button" aria-label="clear">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 3l8 8M3 11l8-8"/>
                    </svg>
                </button>
                <span class="exc-batch-count" id="exc-batch-count">0</span>
            </div>
            <div class="exc-batch-actions">
                <button class="btn btn-ghost" id="exc-batch-ignore" type="button">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="7" cy="7" r="5.5"/>
                        <line x1="4" y1="4" x2="10" y2="10"/>
                    </svg>
                    <span data-i18n="exc-batch-ignore">全部忽略此类</span>
                </button>
                <button class="btn btn-primary" id="exc-batch-resolve" type="button">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M2.5 7l3 3 6-6"/>
                    </svg>
                    <span data-i18n="exc-batch-resolve">全部放行</span>
                </button>
            </div>
        </div>

        <!-- 列表 -->
        <div class="exc-list" id="exc-list">
            <div class="exc-loading" data-i18n="exc-loading">加载中…</div>
        </div>

        <!-- v118.20.5 · 列表底部:计数 + 加载更多 -->
        <div class="exc-list-foot" id="exc-list-foot" style="display:none;">
            <span class="exc-list-count" id="exc-list-count">—</span>
            <button class="btn btn-ghost" id="exc-loadmore" type="button" style="display:none;">
                <span data-i18n="exc-loadmore">加载更多</span>
            </button>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const R={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0},N={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null},at={batchLoading:!1};function De(e,n){let a=t(e)||e;if(n)for(const o in n)a=a.replace(new RegExp("\\{"+o+"\\}","g"),String(n[o]));return a}function xr(e){return e==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 1.5L1 12.5h12L7 1.5z"/>
            <line x1="7" y1="6" x2="7" y2="9"/>
            <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
        </svg>`:e==="medium"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="7" y1="4" x2="7" y2="7.5"/>
            <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
        </svg>`:`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="7" cy="7" r="5.5"/>
        <line x1="4.5" y1="7" x2="9.5" y2="7"/>
    </svg>`}function _r(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 19l5 5 13-13"/>
        <circle cx="20" cy="20" r="17"/>
    </svg>`}function Er(e){if(e==null)return"—";const n=parseFloat(e);return isNaN(n)?"—":"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function Br(e){return e?e.slice(0,10):"—"}function Qe(e){if(e==null)return"—";const n=typeof e=="number"?e:parseFloat(String(e).replace(/,/g,""));return isNaN(n)?escapeHtml(String(e)):"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function Ir(e){if(!e)return"—";try{const n=new Date(e),a=o=>String(o).padStart(2,"0");return`${n.getFullYear()}-${a(n.getMonth()+1)}-${a(n.getDate())} ${a(n.getHours())}:${a(n.getMinutes())}`}catch{return e.slice(0,16).replace("T"," ")}}function Lr(e,n){if(n=n||{},e==="math_mismatch")return`
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(Qe(n.subtotal))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(Qe(n.vat))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(Qe(n.total_expected))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(Qe(n.total_actual))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(Qe(n.diff))}</span></div>
        `;if(e==="tax_id_format_invalid")return`
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(n.tax_id_normalized||n.tax_id_raw||"—")}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(n.actual_length||"?"))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
        `;if(e==="duplicate"){const a=n.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(n.match_filename||"—")}</span></div>
            ${n.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(n.match_invoice_no)}</span></div>`:""}
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(a)}</span></div>
        `}return e==="confidence_low"?`
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(n.confidence||"—")}</span></div>
        `:e==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(n))}</span></div>`}function He(){const e=N.excRow;if(!e)return;const n=e.seller_name&&e.seller_name.trim()?e.seller_name:t("exc-no-seller"),a=e.filename||"—";document.getElementById("exc-drawer-title").textContent=a;const o="exc-status-"+(e.status||"pending"),s=t(o)||e.status,i="s-"+(e.status||"pending"),r=(e.invoice_date||e.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
        <span>${escapeHtml(n)}</span>
        ${e.invoice_no?`<span>· ${escapeHtml(e.invoice_no)}</span>`:""}
        ${r?`<span>· ${escapeHtml(r)}</span>`:""}
        <span class="exc-status-chip ${i}">${escapeHtml(s)}</span>
    `;const c=e.severity||"medium",m=t("exc-rule-"+e.rule_code)||e.rule_code,p=Lr(e.rule_code,e.detail||{}),u=xa(N.history),l=N.history===null,d=N.history&&N.history._err,f=new Set;e.rule_code==="math_mismatch"?(f.add("subtotal"),f.add("vat"),f.add("total_amount")):e.rule_code==="tax_id_format_invalid"?f.add("seller_tax"):e.rule_code==="amount_missing"&&(f.add("total_amount"),f.add("invoice_number"));const v=!!N.editing,w=N.editFields||{},g=(S,q,A)=>{if(l)return`<div class="exc-field-row"><label>${escapeHtml(t(q))}</label><span class="val empty">…</span></div>`;const V=v?w[S]!==void 0?w[S]:u[S]!==void 0&&u[S]!==null?u[S]:"":u[S],T=f.has(S)?"flagged":"";if(v){const G=A?"number":"text",$=A?' step="0.01" inputmode="decimal"':"",H=V==null?"":String(V).replace(/"/g,"&quot;");return`<div class="exc-field-row ${T} editing">
                <label>${escapeHtml(t(q))}</label>
                <input class="exc-field-input" type="${G}"${$} data-edit-key="${escapeHtml(S)}" value="${H}">
            </div>`}const F=A?Qe(V):V||"",O=V==null||V===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(F)}</span>`;return`<div class="exc-field-row ${T}"><label>${escapeHtml(t(q))}</label>${O}</div>`};let b="";d?b=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:b=`
            <div class="exc-fields">
                ${g("invoice_number","exc-fld-invoice-no",!1)}
                ${g("date","exc-fld-date",!1)}
                ${g("seller_name","exc-fld-seller",!1)}
                ${g("seller_tax","exc-fld-seller-tax",!1)}
                ${g("buyer_name","exc-fld-buyer",!1)}
                ${g("buyer_tax","exc-fld-buyer-tax",!1)}
                ${g("subtotal","exc-fld-subtotal",!0)}
                ${g("vat","exc-fld-vat",!0)}
                ${g("total_amount","exc-fld-total",!0)}
            </div>
        `;const h=(()=>{if(N.pdfStatus==="loading"||N.pdfStatus==="idle")return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M18 4v8a14 14 0 1014 14"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                </div>
            `;if(N.pdfStatus==="empty")return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-empty-title"))}</span>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 4h12l6 6v22H9z"/>
                        <path d="M21 4v6h6"/>
                        <line x1="14" y1="20" x2="22" y2="20"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-empty"))}</div>
                </div>
            `;if(N.pdfStatus==="error")return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-error-title"))}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <button class="exc-pdf-icon-btn" id="exc-pdf-retry" title="${escapeHtml(t("exc-pdf-retry"))}" type="button">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M2 7a5 5 0 019-3l1.5 1.5M12 7a5 5 0 01-9 3L1.5 8.5M12 2v3h-3M2 12V9h3"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="18" cy="18" r="14"/>
                        <line x1="18" y1="11" x2="18" y2="20"/>
                        <circle cx="18" cy="24" r="0.8" fill="currentColor"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-error"))}</div>
                </div>
            `;const S=N.pdfUrl;return`
            <div class="exc-pdf-toolbar">
                <span class="exc-pdf-toolbar-title">${escapeHtml(a)}</span>
                <div class="exc-pdf-toolbar-actions">
                    <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${S}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M8 2h4v4M12 2L7 7"/>
                            <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                        </svg>
                    </a>
                    <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${S}" download="${escapeHtml(a)}" title="${escapeHtml(t("exc-pdf-download"))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                        </svg>
                    </a>
                </div>
            </div>
            <iframe class="exc-pdf-frame" src="${S}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
        `})();document.getElementById("exc-drawer-body").innerHTML=`
        <div class="exc-pdf-pane">${h}</div>
        <div class="exc-fields-pane">
            <div class="exc-section">
                <div class="exc-section-title">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="7" cy="7" r="5.5"/><line x1="7" y1="4" x2="7" y2="7.5"/>
                        <circle cx="7" cy="9.6" r="0.5" fill="currentColor"/>
                    </svg>
                    <span>${escapeHtml(t("exc-sect-why"))}</span>
                </div>
                <div class="exc-why sev-${escapeHtml(c)}">
                    <div class="exc-why-rule">${escapeHtml(m)}</div>
                    <div class="exc-why-detail">${p}</div>
                </div>
            </div>
            <div class="exc-section">
                <div class="exc-section-title">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="2.5" width="10" height="9" rx="1"/>
                        <line x1="4" y1="5.5" x2="10" y2="5.5"/>
                        <line x1="4" y1="8.5" x2="10" y2="8.5"/>
                    </svg>
                    <span>${escapeHtml(t("exc-sect-fields"))}</span>
                    ${e.status==="pending"&&!l&&!d?v?`
                            <span class="exc-section-actions">
                                <button class="exc-edit-btn ghost" id="exc-fld-cancel" type="button">${escapeHtml(t("exc-fld-cancel"))}</button>
                                <button class="exc-edit-btn primary" id="exc-fld-save" type="button">${escapeHtml(t("exc-fld-save"))}</button>
                            </span>
                        `:`
                            <span class="exc-section-actions">
                                <button class="exc-edit-btn ghost" id="exc-fld-edit" type="button">
                                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M2.5 11.5l1-3 6.5-6.5 2 2-6.5 6.5z"/>
                                        <path d="M9 2.5l2 2"/>
                                    </svg>
                                    <span>${escapeHtml(t("exc-fld-edit"))}</span>
                                </button>
                            </span>
                        `:""}
                </div>
                ${b}
            </div>
        </div>
    `;const E=document.getElementById("exc-fld-edit");E&&E.addEventListener("click",()=>{N.editing=!0,N.editFields={...xa(N.history)},He()});const y=document.getElementById("exc-fld-cancel");y&&y.addEventListener("click",()=>{N.editing=!1,N.editFields=null,He()});const _=document.getElementById("exc-fld-save");_&&_.addEventListener("click",()=>Tr()),document.querySelectorAll(".exc-field-input").forEach(S=>{S.addEventListener("input",()=>{N.editFields||(N.editFields={}),N.editFields[S.dataset.editKey]=S.value})});const x=document.getElementById("exc-pdf-retry");x&&N.openExcId&&x.addEventListener("click",()=>{N.excRow&&ko(N.excRow.history_id,N.openExcId)});const B=e.status==="pending",L=!!(e.seller_name&&e.seller_name.trim()),I=document.getElementById("exc-btn-resolve"),C=document.getElementById("exc-btn-ignore");I.disabled=!B,C.disabled=!B||!L,C.title=L?t("exc-ignore-hint"):t("exc-ignore-no-seller")}function Yn(){if(N.pdfUrl){try{URL.revokeObjectURL(N.pdfUrl)}catch{}N.pdfUrl=null}N.pdfStatus="idle"}async function ko(e,n){N.pdfStatus="loading",He();try{const a=await fetch("/api/history/"+encodeURIComponent(e)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(N.openExcId!==n)return;if(a.status===404){N.pdfStatus="empty",He();return}if(!a.ok)throw new Error("http "+a.status);const o=await a.blob();if(N.openExcId!==n)return;Yn(),N.pdfUrl=URL.createObjectURL(o),N.pdfStatus="ready",He()}catch(a){if(N.openExcId!==n)return;console.warn("loadDrawerPdf fail",a),N.pdfStatus="error",He()}}function Cr(e){const n=(R.listCache||[]).find(a=>a.id===e);if(!n){showToast(t("exc-drawer-error"),"error");return}R.listScrollY=window.scrollY||document.documentElement.scrollTop||0,Yn(),N.editing=!1,N.editFields=null,N.openExcId=e,N.excRow=n,N.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),He(),Sr(n.history_id),ko(n.history_id,e)}function dt(){Yn(),N.editing=!1,N.editFields=null,N.openExcId=null,N.excRow=null,N.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const e=R.listScrollY||0;e>0&&requestAnimationFrame(()=>window.scrollTo(0,e))}async function Sr(e){try{const n=await fetch("/api/history/"+encodeURIComponent(e),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);N.history=await n.json()}catch(n){console.warn("loadHistoryDetail fail",n),N.history={_err:!0}}N.excRow&&He()}function xa(e){if(!e||!e.pages)return{};const n=e.pages,a=n.find(o=>!o.is_duplicate&&!o.is_copy)||n[0];return a&&a.fields||{}}async function Tr(){if(!N.openExcId||!N.history||!N.history.pages||N.loading)return;N.loading=!0;const e=showToast(t("exc-fld-saving"),"loading",0);try{const n=JSON.parse(JSON.stringify(N.history.pages||[]));let a=n.findIndex(m=>!m.is_duplicate&&!m.is_copy);a<0&&(a=0),n[a]||(n[a]={fields:{}});const o=n[a].fields||{},s=N.editFields||{},i=new Set(["subtotal","vat","total_amount"]),r={...o};for(const m in s){let p=s[m];if((p===""||p===void 0)&&(p=null),i.has(m)&&p!==null){const u=parseFloat(p);p=isNaN(u)?null:u}r[m]=p}n[a].fields=r;const c=await fetch("/api/history/"+encodeURIComponent(N.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:n})});if(!c.ok)throw new Error("http "+c.status);e(),showToast(t("exc-fld-save-ok"),"success"),dt(),await vt(),await qe(),Te()}catch(n){e(),console.warn("save fields fail",n),showToast(t("exc-fld-save-fail"),"error")}finally{N.loading=!1}}async function Mr(){if(!(!N.openExcId||N.loading)){N.loading=!0;try{const e=await fetch("/api/exceptions/"+N.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-resolved"),"success"),dt(),await vt(),await qe(),Te()}catch(e){console.warn("resolve fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{N.loading=!1}}}async function $r(){if(!(!N.openExcId||N.loading)){N.loading=!0;try{const e=await fetch("/api/exceptions/"+N.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-ignored"),"success"),dt(),await vt(),await qe(),Te()}catch(e){console.warn("ignore fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{N.loading=!1}}}async function Te(){try{const e=R.currentClient||"",n="/api/exceptions/stats?status=pending"+(e?"&client_id="+encodeURIComponent(e):""),a=await fetch(n,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!a.ok)return;const o=await a.json(),s=document.getElementById("nav-exc-badge");if(!s)return;const i=parseInt(o.pending||0,10);i>0?(s.textContent=i>99?"99+":String(i),s.style.display=""):s.style.display="none"}catch{}}function xo(e){document.getElementById("exc-kpi-pending").textContent=e.pending||0,document.getElementById("exc-kpi-high").textContent=e.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=e.resolved||0,document.getElementById("exc-kpi-learned").textContent=e.learned_rules||0;const n=document.getElementById("exc-status-tab-count-pending"),a=document.getElementById("exc-status-tab-count-resolved"),o=document.getElementById("exc-status-tab-count-ignored");n&&(n.textContent=e.pending||0),a&&(a.textContent=e.resolved||0),o&&(o.textContent=e.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(i=>{i.classList.toggle("active",i.dataset.status===(R.currentStatus||"pending"))})}function Zn(e){const n=document.getElementById("exc-chips");if(!n)return;const a=e.by_rule||{},o=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let i=`<button class="exc-chip ${!R.currentRule?"active":""}" data-rule="">
        <span>${escapeHtml(t("exc-chip-all"))}</span>
        <span class="exc-chip-count">${e.pending||0}</span>
    </button>`;for(const r of o){const c=a[r]||0;if(c===0&&R.currentRule!==r)continue;const m=R.currentRule===r;i+=`<button class="exc-chip ${m?"active":""}" data-rule="${escapeHtml(r)}">
            <span>${escapeHtml(t("exc-chip-"+r))}</span>
            <span class="exc-chip-count">${c}</span>
        </button>`}n.innerHTML=i,n.querySelectorAll(".exc-chip").forEach(r=>{r.addEventListener("click",()=>{const c=r.dataset.rule||null;R.currentRule=c,qe()})})}function Xn(e){const n=document.getElementById("exc-list");if(!n)return;if(!e||e.length===0){n.innerHTML=`<div class="exc-empty">
            ${_r()}
            <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
            <div>${escapeHtml(t("exc-empty-desc"))}</div>
        </div>`,Ea();return}const a='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',o=(R.currentStatus||"pending")==="pending";n.innerHTML=e.map(s=>{const i=s.severity||"medium",r=t("exc-rule-"+s.rule_code)||s.rule_code,c=s.seller_name&&s.seller_name.trim()?s.seller_name:t("exc-no-seller"),m=s.filename||"—",p=Br(s.invoice_date||s.created_at),u=s.status==="pending",l=R.selectedIds.has(s.id),d=o&&u;return`
            <div class="exc-row sev-${escapeHtml(i)} ${l?"selected":""}" data-exc-id="${escapeHtml(String(s.id))}">
                <div class="exc-row-check ${l?"checked":""}" data-check-id="${escapeHtml(String(s.id))}" ${d?"":'style="visibility:hidden;"'}>${a}</div>
                <div class="exc-row-sev">${xr(i)}</div>
                <div class="exc-row-main">
                    <div class="exc-row-title">${escapeHtml(c)} · ${escapeHtml(m)}</div>
                    <div class="exc-row-meta">
                        ${s.invoice_no?`<span><b>${escapeHtml(s.invoice_no)}</b></span>`:""}
                        <span>${escapeHtml(p)}</span>
                    </div>
                </div>
                <div class="exc-row-rule r-${escapeHtml(i)}">${escapeHtml(r)}</div>
                <div class="exc-row-amount">${escapeHtml(Er(s.total_amount))}</div>
            </div>
        `}).join(""),n.querySelectorAll(".exc-row").forEach(s=>{s.addEventListener("click",i=>{if(i.target.closest(".exc-row-check"))return;const r=s.dataset.excId;r&&Cr(parseInt(r,10))})}),n.querySelectorAll(".exc-row-check").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation();const r=parseInt(s.dataset.checkId,10);r&&(R.selectedIds.has(r)?(R.selectedIds.delete(r),s.classList.remove("checked"),s.closest(".exc-row").classList.remove("selected")):(R.selectedIds.add(r),s.classList.add("checked"),s.closest(".exc-row").classList.add("selected")),_a())})}),_a(),Ea()}function _a(){const e=document.getElementById("exc-batch-bar"),n=document.getElementById("exc-batch-count");if(!e||!n)return;const a=R.selectedIds.size;a===0?e.style.display="none":(e.style.display="",n.textContent=De("exc-batch-count",{n:a}))}function Ea(){const e=document.getElementById("exc-list-foot"),n=document.getElementById("exc-list-count"),a=document.getElementById("exc-loadmore");if(!e||!n||!a)return;const o=R.listCache.length;if(o===0){e.style.display="none";return}e.style.display="";let s=o;const i=R.statsCache;i&&(R.currentRule?s=(i.by_rule||{})[R.currentRule]||o:s=i.pending||o),R.total=s,n.textContent=De("exc-list-count",{shown:o,total:s});const r=o<s&&o<500;a.style.display=r?"":"none"}async function vt(){try{if(navigator.onLine===!1)throw new Error("offline");const e=R.currentClient||"",n=R.currentStatus||"pending",a=new URLSearchParams;a.set("status",n),e&&a.set("client_id",e);const o="/api/exceptions/stats?"+a.toString(),s=await fetch(o,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!s.ok)throw new Error("http "+s.status);const i=await s.json();return R.statsCache=i,xo(i),Zn(i),i}catch(e){return console.warn("loadExceptionsStats fail",e),null}}function Hr(e){const n=document.getElementById("exc-list");if(!n)return;const a=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="18" cy="18" r="14"/>
        <line x1="18" y1="11" x2="18" y2="19"/>
        <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
    </svg>`,o=e?t("exc-offline"):t("exc-error-retry-title"),s=e?"":t("exc-error-retry-desc");n.innerHTML=`
        <div class="exc-error">
            ${a}
            <div class="exc-error-msg">${escapeHtml(o)}${s?" · "+escapeHtml(s):""}</div>
            <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
        </div>`;const i=document.getElementById("exc-retry-btn");i&&i.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function qe(e){e=e||{};const n=!!e.append,a=document.getElementById("exc-list");!n&&a&&R.listCache.length===0&&(a.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const o=new URLSearchParams;o.set("status",R.currentStatus||"pending"),R.currentRule&&o.set("rule_code",R.currentRule),R.currentClient&&o.set("client_id",R.currentClient);const s=n?R.listCache.length:0;o.set("limit",String(R.pageSize)),o.set("offset",String(s));try{if(navigator.onLine===!1)throw new Error("offline");const i=await fetch("/api/exceptions/list?"+o.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!i.ok)throw new Error("http "+i.status);const c=(await i.json()).items||[];n?R.listCache=R.listCache.concat(c):(R.listCache=c,R.selectedIds.clear()),R.loadFailed=!1,Xn(R.listCache),R.statsCache&&Zn(R.statsCache)}catch(i){console.warn("loadExceptionsList fail",i),R.loadFailed=!0;const r=navigator.onLine===!1||String(i.message||"").includes("offline");n?showToast(t("exc-toast-load-fail"),"error"):(Hr(r),showToast(r?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function Ar(){if(!R.loading&&!(R.listCache.length>=500)){R.loading=!0;try{await qe({append:!0})}finally{R.loading=!1}}}function Qn(){const e=document.getElementById("exc-client-filter");if(!e)return;const n=window._clientsCache||[],a=R.currentClient||"",o=typeof t=="function"?t("history-client-all"):"全部客户";e.innerHTML=`<option value="">${escapeHtml(o)}</option>`+n.map(s=>`<option value="${s.id}">${escapeHtml(s.name)}</option>`).join(""),e.value=a}async function jr(){if(at.batchLoading)return;const e=Array.from(R.selectedIds);if(e.length===0||!await showConfirm(De("exc-batch-confirm-resolve",{n:e.length})))return;at.batchLoading=!0;const a=showToast(De("exc-batch-count",{n:e.length})+" …","loading",0);try{const o=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"resolve"})});if(!o.ok)throw new Error("http "+o.status);const s=await o.json();a(),showToast(De("exc-toast-batch-resolved",{n:s.processed||0}),"success"),R.selectedIds.clear(),await vt(),await qe(),Te()}catch(o){a(),console.warn("batch resolve fail",o),showToast(t("exc-toast-batch-fail"),"error")}finally{at.batchLoading=!1}}async function Pr(){if(at.batchLoading)return;const e=Array.from(R.selectedIds);if(e.length===0||!await showConfirm(De("exc-batch-confirm-ignore",{n:e.length}),{danger:!1}))return;at.batchLoading=!0;const a=showToast(De("exc-batch-count",{n:e.length})+" …","loading",0);try{const o=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"ignore"})});if(!o.ok)throw new Error("http "+o.status);const s=await o.json();a(),showToast(De("exc-toast-batch-ignored",{n:s.processed||0,wl:s.whitelist_added||0}),"success"),R.selectedIds.clear(),await vt(),await qe(),Te()}catch(o){a(),console.warn("batch ignore fail",o),showToast(t("exc-toast-batch-fail"),"error")}finally{at.batchLoading=!1}}function Dr(){R.selectedIds.clear(),Xn(R.listCache)}async function _o(){const e=document.getElementById("learned-list");if(e){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const n=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);const o=(await n.json()).items||[];if(o.length===0){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const s=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
        </svg>`;e.innerHTML=o.map(i=>{const r=t("exc-rule-"+i.rule_code)||i.rule_code;return`
                <div class="learned-row" data-wl-id="${escapeHtml(String(i.id))}">
                    <div class="learned-seller" title="${escapeHtml(i.seller_name)}">${escapeHtml(i.seller_name)}</div>
                    <div class="learned-rule">${escapeHtml(r)}</div>
                    <div class="learned-date">${escapeHtml(Ir(i.created_at))}</div>
                    <button class="learned-del-btn" data-del-wl="${escapeHtml(String(i.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${s}</button>
                </div>
            `}).join("")}catch(n){console.warn("loadLearnedRules fail",n),e.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadExceptionsPage=async function(){if(!R.loading){R.loading=!0;try{Qn(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await vt(),await qe()}finally{R.loading=!1}}};window.refreshExcBadge=Te;window._refreshExcClientFilter=Qn;window._excState=R;window._rerenderExceptions=function(){try{Qn()}catch{}R.statsCache&&(xo(R.statsCache),Zn(R.statsCache)),R.listCache&&R.listCache.length&&Xn(R.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}N.openExcId&&He()};document.addEventListener("click",e=>{e.target.closest("#exc-drawer-close")&&dt(),e.target.closest("#exc-drawer-mask")&&dt(),e.target.closest("#exc-btn-resolve")&&Mr(),e.target.closest("#exc-btn-ignore")&&$r(),e.target.closest("#exc-batch-resolve")&&jr(),e.target.closest("#exc-batch-ignore")&&Pr(),e.target.closest("#exc-batch-clear")&&Dr(),e.target.closest("#exc-loadmore")&&Ar()});document.addEventListener("keydown",e=>{e.key==="Escape"&&N.openExcId&&dt()});document.addEventListener("click",e=>{e.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),Te())});document.addEventListener("change",e=>{if(!e.target.closest("#exc-client-filter"))return;const n=e.target;R.currentClient=n.value||"",R.currentRule=null,R.selectedIds.clear(),R.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),Te()});document.addEventListener("click",e=>{const n=e.target.closest("#exc-status-tabs .exc-status-tab");if(!n)return;const a=n.dataset.status||"pending";a!==R.currentStatus&&(R.currentStatus=a,R.currentRule=null,R.selectedIds.clear(),R.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())});window.addEventListener("online",()=>{R.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()});setTimeout(Te,1500);setInterval(Te,6e4);window.loadLearnedRules=_o;document.addEventListener("click",async e=>{const n=e.target.closest("[data-del-wl]");if(!n)return;const a=parseInt(n.dataset.delWl,10);if(!a)return;const o=n.closest(".learned-row"),s=o&&o.querySelector(".learned-seller"),i=s?s.textContent.trim():"",r=t("set-learned-del-confirm").replace("{seller}",i);if(await showConfirm(r,{danger:!0}))try{const m=await fetch("/api/exception-whitelist/"+a,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!m.ok)throw new Error("http "+m.status);showToast(t("set-learned-del-ok"),"success"),_o(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(m){console.warn("delete whitelist fail",m),showToast(t("set-learned-del-fail"),"error")}});let ie={items:[],q:"",cat:"",adapter:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},Ba=null;function Ce(){return localStorage.getItem("mrpilot_token")||""}function Eo(e){const n=typeof currentLang=="string"&&currentLang||window._currentLang||"th",a=e.error_friendly&&e.error_friendly[n];if(a)return a;if(typeof humanizeError=="function"&&e.error_msg)try{return humanizeError(e.error_msg)}catch{}return t("erp-exc-reason-"+(e.category||"other"))}function Ia(){const e=document.getElementById("erp-exc-batch");if(!e)return;const n=ie.selected.size;e.hidden=n===0;const a=e.querySelector(".erp-exc-batch-count");a&&(a.textContent=String(n))}function ea(){const e=document.getElementById("erp-exc-block");if(!e)return;const n=ie;if(!(n.total>0||!!n.q||!!n.cat)){e.hidden=!0,e.innerHTML="";return}e.hidden=!1;const o=n.categories||{},s=Object.keys(o).reduce((k,x)=>k+o[x],0);let i=`<button class="erp-exc-chip ${n.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${s}</span></button>`;Object.keys(o).forEach(k=>{i+=`<button class="erp-exc-chip ${n.cat===k?"active":""}" data-erpexc-cat="${escapeHtml(k)}"><span>${escapeHtml(t("erp-exc-cat-"+k))}</span><span class="erp-exc-chip-count">${o[k]}</span></button>`});const r=n.items||[],c=r.length>0&&r.every(k=>n.selected.has(k.id)),m=r.map(k=>{const x=k.state==="needs_action"?"needs":k.state==="retrying"?"retry":"fail",B=t("erp-exc-state-"+(k.state||"failed")),L=Eo(k),I=n.selected.has(k.id)?"checked":"",C=k.push_type==="id_card",S=C?`<span class="erp-exc-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span> `:"",q=C?`<span class="ex-inv" title="${escapeHtml(t("erp-log-col-booking"))}">${S}${escapeHtml(k.invoice_no||"—")}</span>`:`<span class="ex-inv" title="${escapeHtml(k.invoice_no||"")}">${escapeHtml(k.invoice_no||"—")}</span>`,A=C?`<span class="ex-seller" title="${escapeHtml(t("erp-log-col-customer"))}">${escapeHtml(k.seller_name||"—")}</span>`:`<span class="ex-seller" title="${escapeHtml(k.seller_name||"")}">${escapeHtml(k.seller_name||"—")}</span>`,V=C?`<span class="ex-buyer" title="${escapeHtml(t("erp-log-col-idcard"))}">${k.id_card_tail?"••••"+escapeHtml(k.id_card_tail):"—"}</span>`:`<span class="ex-buyer" title="${escapeHtml(k.ocr_buyer_name||"")}">${escapeHtml(k.ocr_buyer_name||"—")}</span>`;return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(k.id)}">
            <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(k.id)}" ${I}></span>
            ${q}
            ${A}
            ${V}
            <span class="ex-state"><span class="erp-exc-state ${x}">${escapeHtml(B)}</span></span>
            <span class="ex-reason" title="${escapeHtml(L)}">${escapeHtml(L)}${k.error_code?` <span class="erp-exc-code">${escapeHtml(k.error_code)}</span>`:""}</span>
            <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(k.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
        </div>`}).join(""),p=r.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",u=r.length<n.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${r.length}/${n.total})</button>`:n.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:r.length,total:n.total}))}</div>`:"",l=n.adapter==="mrerp_dms",d=Array.isArray(window._erpEndpoints)?window._erpEndpoints:[],f=new Set;let v=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`;d.forEach(k=>{const x=(k&&k.adapter||"").toLowerCase();!x||f.has(x)||(f.add(x),v+=`<option value="${escapeHtml(x)}"${x===n.adapter?" selected":""}>${escapeHtml(k&&k.name||x)}</option>`)});const w=l?t("erp-log-col-booking"):t("erp-exc-f-invoice"),g=l?t("erp-log-col-customer"):t("erp-exc-f-seller"),b=l?t("erp-log-col-idcard"):t("erp-exc-f-buyer");e.innerHTML=`
        <div class="erp-exc-head">
            <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
            <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
            <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${v}</select>
            <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(n.q)}">
        </div>
        <div class="erp-exc-chips">${i}</div>
        <div class="erp-exc-batch" id="erp-exc-batch" ${n.selected.size?"":"hidden"}>
            <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${n.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
            <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
            <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
            <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
        </div>
        <div class="erp-exc-rows">
            <div class="erp-exc-row erp-exc-row-head">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${c?"checked":""}></span>
                <span class="ex-inv">${escapeHtml(w)}</span>
                <span class="ex-seller">${escapeHtml(g)}</span>
                <span class="ex-buyer">${escapeHtml(b)}</span>
                <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                <span class="ex-act"></span>
            </div>
            ${m}${p}
        </div>
        <div class="erp-exc-foot">${u}</div>`;const h=document.getElementById("erp-exc-search");if(h){if(n.focusSearch){h.focus();try{h.setSelectionRange(n.searchCaret,n.searchCaret)}catch{}}h.addEventListener("input",()=>{n.q=h.value,n.focusSearch=!0,n.searchCaret=h.selectionStart||h.value.length,clearTimeout(Ba),Ba=setTimeout(()=>Ge(!1),350)}),h.addEventListener("blur",()=>{n.focusSearch=!1})}e.querySelectorAll(".erp-exc-chip").forEach(k=>{k.addEventListener("click",()=>{n.cat=k.dataset.erpexcCat||"",Ge(!1)})});const E=document.getElementById("erp-exc-erp-select");E&&E.addEventListener("change",()=>{n.adapter=E.value||"",Ge(!1)}),e.querySelectorAll("[data-erpexc-retry]").forEach(k=>{k.addEventListener("click",x=>{x.stopPropagation(),Nt(k.dataset.erpexcRetry,k)})}),e.querySelectorAll(".erp-exc-cb").forEach(k=>{k.addEventListener("change",()=>{const x=k.dataset.erpexcCb;k.checked?n.selected.add(x):n.selected.delete(x);const B=document.getElementById("erp-exc-cb-all");B&&(B.checked=r.length>0&&r.every(L=>n.selected.has(L.id))),Ia()})});const y=document.getElementById("erp-exc-cb-all");y&&y.addEventListener("change",()=>{r.forEach(k=>{y.checked?n.selected.add(k.id):n.selected.delete(k.id)}),e.querySelectorAll(".erp-exc-cb").forEach(k=>{k.checked=y.checked}),Ia()}),e.querySelectorAll("[data-erpexc-batch]").forEach(k=>{k.addEventListener("click",()=>Fr(k.dataset.erpexcBatch))});const _=document.getElementById("erp-exc-more");_&&_.addEventListener("click",()=>Ge(!0)),e.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(k=>{k.addEventListener("click",x=>{x.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(k.dataset.erpexcId)})})}async function Nt(e,n){if(e){n&&(n.disabled=!0,n.textContent=t("erp-exc-retrying"));try{const a=await fetch("/api/erp/logs/"+encodeURIComponent(e)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+Ce()}}),o=await a.json().catch(()=>({}));showToast(a.ok&&o.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),a.ok&&o.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(ie.selected.delete(e),Ge(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function Fr(e){const n=Array.from(ie.selected);if(e==="clear"){ie.selected.clear(),ea();return}if(n.length!==0){if(e==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:n.length}),{danger:!0}))return;try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+Ce(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:n.slice(0,200)})}),s=await o.json().catch(()=>({}));showToast(o.ok?t("erp-exc-batch-delete-ok",{n:s.deleted||0}):t("erp-exc-retry-fail"),o.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(e==="retry")try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+Ce(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:n.slice(0,50)})}),o=await a.json().catch(()=>({}));showToast(a.ok?t("erp-exc-batch-retry-ok",{ok:o.succeeded||0,fail:(o.failed||0)+(o.skipped||0)}):t("erp-exc-retry-fail"),a.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(ie.selected.clear(),Ge(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function Ge(e){const n=document.getElementById("erp-exc-block");if(!(!n||ie.loading)){ie.loading=!0;try{if(!Array.isArray(window._erpEndpoints)||!window._erpEndpoints.length)try{const r=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+Ce()}});if(r.ok){const c=await r.json();window._erpEndpoints=c&&(c.items||c)||[]}}catch{}const a=new URLSearchParams;ie.q&&a.set("q",ie.q),ie.cat&&a.set("category",ie.cat),ie.adapter&&a.set("adapter",ie.adapter),a.set("limit",String(ie.pageSize)),a.set("offset",String(e?ie.items.length:0));const o=await fetch("/api/erp/exceptions?"+a.toString(),{headers:{Authorization:"Bearer "+Ce()}});if(!o.ok){e||(n.hidden=!0);return}const s=await o.json(),i=s.items||[];ie.items=e?ie.items.concat(i):i,ie.total=s.total||0,ie.categories=s.categories||{},ea()}catch{e||(n.hidden=!0)}finally{ie.loading=!1}}}window._rerenderErpExceptions=ea;window.loadErpExceptions=Ge;window._erpExcState=ie;let Ft={};function Ye(){const e=document.getElementById("erp-exc-modal");e&&e.remove()}window._erpExcOpenEdit=function(e){const n=(ie.items||[]).find(u=>String(u.id)===String(e));if(!n)return;const a=n.push_type==="id_card",o=!!n.history_client_id&&n.category==="customer_mismatch",s=n.category==="product_mismatch"&&!!n.history_id&&!!n.endpoint_id,i=Eo(n),r=n.state==="needs_action"?"needs":n.state==="retrying"?"retry":"fail",c=(u,l)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(u)}</span><span class="erp-exc-m-v">${escapeHtml(l||"—")}</span></div>`;let m="";if(o)m=`
            <div class="erp-exc-m-fix">
                <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                    <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                </div>
            </div>`;else if(s)m=`
            <div class="erp-exc-m-fix">
                <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                    <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                </div>
            </div>`;else{const u="erp-exc-edit-hint-"+(n.category||"other");let l=t(u);(!l||l===u)&&(l=i),m=`<div class="erp-exc-m-hint">${escapeHtml(l)}</div>`}const p=document.createElement("div");if(p.id="erp-exc-modal",p.className="erp-exc-modal-overlay",p.innerHTML=`
        <div class="erp-exc-modal" role="dialog" aria-modal="true">
            <div class="erp-exc-m-head">
                <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
            </div>
            <div class="erp-exc-m-body">
                <div class="erp-exc-m-reason"><span class="erp-exc-state ${r}">${escapeHtml(t("erp-exc-state-"+(n.state||"failed")))}</span> ${escapeHtml(i)}${n.error_code&&!a?` <span class="erp-exc-code">${escapeHtml(n.error_code)}</span>`:""}</div>
                ${c(a?t("erp-log-col-booking"):t("erp-exc-f-invoice"),n.invoice_no)}
                ${c(a?t("erp-log-col-customer"):t("erp-exc-f-seller"),n.seller_name)}
                ${a?c(t("erp-log-col-idcard"),n.id_card_tail?"••••"+n.id_card_tail:"—"):c(t("erp-exc-f-buyer"),n.ocr_buyer_name)+c(t("erp-exc-edit-field-current"),n.client_name)}
                ${m}
            </div>
            <div class="erp-exc-m-foot">
                <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                ${o?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                ${s?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
            </div>
        </div>`,document.body.appendChild(p),p.addEventListener("click",u=>{u.target===p&&Ye()}),document.getElementById("erp-exc-m-close").addEventListener("click",Ye),document.getElementById("erp-exc-m-cancel").addEventListener("click",Ye),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{Ye(),Nt(n.id,null)}),o){let u="";const l=document.getElementById("erp-exc-m-bind"),d=document.getElementById("erp-exc-m-custlist"),f=document.getElementById("erp-exc-m-search"),v=(g,b)=>{const h=(b||"").trim().toLowerCase(),E=h?g.filter(y=>(y.code||"").toLowerCase().includes(h)||(y.name||"").toLowerCase().includes(h)):g;if(E.length===0){d.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}d.innerHTML=E.slice(0,100).map(y=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(y.code||"")}">
                    <span class="erp-exc-m-cust-name">${escapeHtml(y.name||"")}</span>
                    <span class="erp-exc-m-cust-code">${escapeHtml(y.code||"")}</span>
                </div>`).join(""),d.querySelectorAll(".erp-exc-m-cust").forEach(y=>{y.addEventListener("click",()=>{u=y.dataset.custCode||"",d.querySelectorAll(".erp-exc-m-cust").forEach(_=>_.classList.remove("sel")),y.classList.add("sel"),l&&(l.disabled=!u)})})},w=async()=>{const g=n.endpoint_id;if(Ft[g]){v(Ft[g],"");return}try{const b=await fetch("/api/erp/endpoints/"+encodeURIComponent(g)+"/customers",{headers:{Authorization:"Bearer "+Ce()}}),h=await b.json().catch(()=>({}));if(!b.ok||!h.ok){d.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const E=h.customers||[];Ft[g]=E,v(E,"")}catch{d.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};f&&f.addEventListener("input",()=>v(Ft[n.endpoint_id]||[],f.value)),w(),l&&l.addEventListener("click",async()=>{if(u){l.disabled=!0,l.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+Ce(),"Content-Type":"application/json"},body:JSON.stringify({client_id:n.history_client_id,erp_type:n.endpoint_adapter,erp_code:u})})).ok){showToast(t("erp-exc-retry-fail"),"error"),l.disabled=!1,l.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),Ye(),await Nt(n.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),l.disabled=!1,l.textContent=t("erp-exc-edit-bind-retry")}}})}if(s){const u=document.getElementById("erp-exc-m-bind-prod"),l=document.getElementById("erp-exc-m-prodlist"),d={};let f=[];const v=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+f.slice(0,500).map(b=>`<option value="${escapeHtml(b.code||"")}" data-pname="${escapeHtml(b.name||"")}">`+escapeHtml((b.name||"")+" · "+(b.code||""))+"</option>").join(""),w=b=>{if(!b.length){l.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}l.innerHTML=b.map(h=>`<div class="erp-exc-m-cust" style="cursor:default">
                    <span class="erp-exc-m-cust-name" title="${escapeHtml(h)}">${escapeHtml(h)}</span>
                    <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(h)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${v()}</select>
                </div>`).join(""),l.querySelectorAll(".erp-exc-m-prod-sel").forEach(h=>{h.addEventListener("change",()=>{const E=h.dataset.item,y=h.options[h.selectedIndex];h.value?d[E]={code:h.value,name:y&&y.dataset.pname||""}:delete d[E],u&&(u.disabled=Object.keys(d).length===0)})})};(async()=>{try{const h=await(await fetch("/api/history/"+encodeURIComponent(n.history_id),{headers:{Authorization:"Bearer "+Ce()}})).json().catch(()=>({})),E=h&&h.pages||[],y=[],_={};(Array.isArray(E)?E:[]).forEach(B=>{const L=B&&B.fields&&B.fields.items||[];(Array.isArray(L)?L:[]).forEach(I=>{const C=(I&&(I.name||I.description)||"").trim();C&&!_[C]&&(_[C]=1,y.push(C))})});const k=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+Ce()}}),x=await k.json().catch(()=>({}));if(!k.ok||!x.ok){l.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}f=x.products||[],w(y)}catch{l.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),u&&u.addEventListener("click",async()=>{const b=Object.entries(d);if(b.length){u.disabled=!0,u.textContent=t("erp-exc-retrying");try{for(const[h,E]of b)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+Ce(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:n.endpoint_adapter,item_name:h,erp_code:E.code,erp_name:E.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),u.disabled=!1,u.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),Ye(),await Nt(n.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),u.disabled=!1,u.textContent=t("erp-exc-edit-bind-prod-retry")}}})}};const qr=`
    <div class="cmdk">
        <div class="cmdk-input-wrap">
            <svg class="cmdk-input-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="9" cy="9" r="6"/>
                <line x1="14" y1="14" x2="17" y2="17"/>
            </svg>
            <input type="text" class="cmdk-input" id="cmdk-input"
                   data-i18n-placeholder="cmdk-input-ph"
                   placeholder="跳转到页面 / 搜索发票号 / 客户名..." autocomplete="off"
                   aria-label="Command palette search">
            <span class="cmdk-esc" id="cmdk-esc-btn">ESC</span>
        </div>
        <div class="cmdk-body" id="cmdk-body">
            <div class="cmdk-section" data-cmdk-section data-i18n="cmdk-section-jump">跳转</div>

            <!-- 已实现路由 · 正常点击跳 -->
            <div class="cmdk-item" data-cmdk-route="ocr" data-cmdk-text="ocr upload 上传识别 อัปโหลด">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13V4M6 7l4-3 4 3"/><path d="M3.5 13v2.5A1.5 1.5 0 005 17h10a1.5 1.5 0 001.5-1.5V13"/></svg>
                <span data-i18n="nav-ocr">上传识别</span>
            </div>
            <div class="cmdk-item" data-cmdk-route="history" data-cmdk-text="history records 单据记录 ประวัติ">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3.5" width="14" height="13" rx="1.5"/><line x1="6" y1="7" x2="14" y2="7"/><line x1="6" y1="10" x2="14" y2="10"/><line x1="6" y1="13" x2="11" y2="13"/></svg>
                <span data-i18n="nav-history">单据记录</span>
            </div>
            <div class="cmdk-item" data-cmdk-route="reconcile" data-cmdk-text="reconcile vat 对账 销项 ภาษีขาย">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="3" width="12" height="14" rx="1.5"/><line x1="7" y1="6.5" x2="13" y2="6.5"/><line x1="7" y1="9.5" x2="13" y2="9.5"/><line x1="7" y1="12.5" x2="10" y2="12.5"/></svg>
                <span data-i18n="nav-reconcile">对账中心</span>
            </div>
            <div class="cmdk-item" data-cmdk-route="exceptions" data-cmdk-text="exceptions 异常 ข้อผิดพลาด">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 2.5l8 14H2L10 2.5z"/><line x1="10" y1="8" x2="10" y2="12"/><circle cx="10" cy="14.2" r="0.6" fill="currentColor" stroke="none"/></svg>
                <span data-i18n="nav-exceptions">异常栏</span>
            </div>
            <div class="cmdk-item" data-cmdk-route="clients" data-cmdk-text="clients 客户 ลูกค้า">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17V6a1 1 0 011-1h5a1 1 0 011 1v11"/><path d="M10 17V9a1 1 0 011-1h5a1 1 0 011 1v8"/><line x1="3" y1="17" x2="17" y2="17"/></svg>
                <span data-i18n="nav-clients">客户</span>
            </div>
            <div class="cmdk-item" data-cmdk-route="sales-invoices" data-cmdk-text="sales invoices 销售发票 ใบขาย">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 2.5h7l3 3v12H5z"/><path d="M12 2.5v3h3"/><line x1="7.5" y1="10" x2="12.5" y2="10"/><line x1="7.5" y1="13" x2="11" y2="13"/></svg>
                <span data-i18n="nav-sales-invoices">销售发票</span>
            </div>
            <div class="cmdk-item" data-cmdk-route="settings" data-cmdk-text="settings 设置 ตั้งค่า">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="10" cy="10" r="2.5"/><path d="M15.3 12a1 1 0 00.2 1.1l.1.1a1.5 1.5 0 11-2.1 2.1l-.1-.1a1 1 0 00-1.1-.2 1 1 0 00-.6.9v.1a1.5 1.5 0 11-3 0v-.1a1 1 0 00-.6-.9 1 1 0 00-1.1.2l-.1.1A1.5 1.5 0 114.8 13.3l.1-.1a1 1 0 00.2-1.1 1 1 0 00-.9-.6h-.1a1.5 1.5 0 110-3h.1a1 1 0 00.9-.6 1 1 0 00-.2-1.1l-.1-.1A1.5 1.5 0 116.9 4.7l.1.1a1 1 0 001.1.2h.1a1 1 0 00.6-.9v-.1a1.5 1.5 0 113 0v.1a1 1 0 00.6.9 1 1 0 001.1-.2l.1-.1a1.5 1.5 0 112.1 2.1l-.1.1a1 1 0 00-.2 1.1 1 1 0 00.9.6h.1a1.5 1.5 0 110 3h-.1a1 1 0 00-.9.6z"/></svg>
                <span data-i18n="nav-settings">设置</span>
            </div>

            <!-- 占位页 · 灰显 + 即将 -->
            <div class="cmdk-item cmdk-item-locked" data-cmdk-route="dashboard" data-cmdk-text="dashboard 仪表盘 แดชบอร์ด">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="6.5" height="7.5" rx="1"/><rect x="10.5" y="3" width="6.5" height="4" rx="1"/><rect x="10.5" y="8" width="6.5" height="9" rx="1"/><rect x="3" y="11.5" width="6.5" height="5.5" rx="1"/></svg>
                <span data-i18n="nav-dashboard">仪表盘</span>
                <span class="cmdk-soon" data-i18n="badge-soon">即将</span>
            </div>
            <div class="cmdk-item cmdk-item-locked" data-cmdk-route="vouchers" data-cmdk-text="vouchers 费用 凭证 进项 expense">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 3.5l1.5 1.5L7 3.5l1.5 1.5L10 3.5l1.5 1.5L13 3.5l1.5 1.5L16 3.5v13l-1.5-1.5L13 16.5l-1.5-1.5L10 16.5l-1.5-1.5L7 16.5l-1.5-1.5L4 16.5v-13z"/><line x1="7" y1="8" x2="13" y2="8"/><line x1="7" y1="11" x2="11" y2="11"/></svg>
                <span data-i18n="nav-vouchers">费用总览</span>
                <span class="cmdk-soon" data-i18n="badge-soon">即将</span>
            </div>
            <div class="cmdk-item cmdk-item-locked" data-cmdk-route="receivables" data-cmdk-text="receivables 应收 ลูกหนี้">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 2v16M6 5h6a2 2 0 010 4H8a2 2 0 000 4h6"/></svg>
                <span data-i18n="nav-receivables">应收追踪</span>
                <span class="cmdk-soon" data-i18n="badge-soon">即将</span>
            </div>
            <div class="cmdk-item cmdk-item-locked" data-cmdk-route="automation" data-cmdk-text="automation 自动化 อัตโนมัติ">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="10" cy="10" r="2"/><path d="M10 3v2M10 15v2M3 10h2M15 10h2M5.2 5.2l1.4 1.4M13.4 13.4l1.4 1.4M5.2 14.8l1.4-1.4M13.4 6.6l1.4-1.4"/></svg>
                <span data-i18n="nav-automation">自动化</span>
                <span class="cmdk-soon" data-i18n="badge-soon">即将</span>
            </div>

            <!-- 权限项 · 通过 applyRoleVisibility 显隐 -->
            <div class="cmdk-item" data-cmdk-action="open-admin" data-show-if-admin="1" data-cmdk-text="admin 管理员 超管 platform" style="display:none">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 2.5l6 2v5c0 4-2.8 6.8-6 8-3.2-1.2-6-4-6-8v-5l6-2z"/><path d="M7.5 10l2 2 3.5-3.5"/></svg>
                <span data-i18n="avatar-menu-admin">管理员后台</span>
                <span class="avatar-pill avatar-pill-admin" data-i18n="avatar-menu-badge-admin">超管</span>
            </div>
            <div class="cmdk-item" data-cmdk-route="test-center" data-show-if-test="1" data-cmdk-text="test 测试中心 ทดสอบ" style="display:none">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3v5L4 15a1.5 1.5 0 001.4 2h9.2A1.5 1.5 0 0016 15l-4-7V3"/><line x1="6.5" y1="3" x2="13.5" y2="3"/><line x1="7" y1="11" x2="13" y2="11"/></svg>
                <span data-i18n="nav-test-center">测试中心</span>
            </div>

            <div class="cmdk-section" data-cmdk-section data-i18n="cmdk-section-actions">操作</div>
            <div class="cmdk-item" data-cmdk-action="lang-th" data-cmdk-text="ภาษาไทย thai 泰语">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="10" cy="10" r="8"/><line x1="2" y1="10" x2="18" y2="10"/><path d="M10 2c2.5 2 4 5 4 8s-1.5 6-4 8c-2.5-2-4-5-4-8s1.5-6 4-8z"/></svg>
                <span>→ ภาษาไทย</span>
            </div>
            <div class="cmdk-item" data-cmdk-action="lang-en" data-cmdk-text="English 英文 อังกฤษ">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="10" cy="10" r="8"/><line x1="2" y1="10" x2="18" y2="10"/><path d="M10 2c2.5 2 4 5 4 8s-1.5 6-4 8c-2.5-2-4-5-4-8s1.5-6 4-8z"/></svg>
                <span>→ English</span>
            </div>
            <div class="cmdk-item" data-cmdk-action="lang-zh" data-cmdk-text="中文 Chinese จีน">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="10" cy="10" r="8"/><line x1="2" y1="10" x2="18" y2="10"/><path d="M10 2c2.5 2 4 5 4 8s-1.5 6-4 8c-2.5-2-4-5-4-8s1.5-6 4-8z"/></svg>
                <span>→ 中文</span>
            </div>
            <div class="cmdk-item" data-cmdk-action="lang-ja" data-cmdk-text="日本語 Japanese 日语 ญี่ปุ่น">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="10" cy="10" r="8"/><line x1="2" y1="10" x2="18" y2="10"/><path d="M10 2c2.5 2 4 5 4 8s-1.5 6-4 8c-2.5-2-4-5-4-8s1.5-6 4-8z"/></svg>
                <span>→ 日本語</span>
            </div>

            <div class="cmdk-empty" id="cmdk-empty" style="display:none">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="16" y1="16" x2="21" y2="21"/><line x1="8" y1="8" x2="14" y2="14"/></svg>
                <span data-i18n="cmdk-empty">没找到匹配项</span>
            </div>
        </div>
        <div class="cmdk-foot">
            <span><kbd>↑</kbd><kbd>↓</kbd> <span data-i18n="cmdk-foot-move">移动</span></span>
            <span><kbd>Enter</kbd> <span data-i18n="cmdk-foot-select">选择</span></span>
            <span><kbd>ESC</kbd> <span data-i18n="cmdk-foot-close">关闭</span></span>
        </div>
    </div>
`;ve("cmdk-mask",qr);(function(){function e(l){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||l&&l.id&&String(l.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var d=window._userInfo,f=!1,v=!0,w=!1,g=!1;d&&(f=typeof canManageTeam=="function"?canManageTeam(d):!!(d.role==="owner"||d.is_super_admin),v=typeof shouldHideMoney=="function"?shouldHideMoney(d):d.role==="member"&&!d.is_super_admin,w=typeof isSuperAdmin=="function"?isSuperAdmin(d):!!d.is_super_admin,g=e(d)),document.querySelectorAll("[data-show-if-team]").forEach(function(h){h.style.display=f?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(h){h.style.display=v?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(h){h.style.display=w?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(h){h.style.display=g?"":"none"});var b=w||g;document.querySelectorAll("[data-show-if-special]").forEach(function(h){h.style.display=b?"":"none"})},window.renderAvatarMenu=function(d){if(d){var f=document.getElementById("avatar-btn"),v=document.getElementById("avatar-popup-name"),w=document.getElementById("avatar-popup-email");if(!(!f||!v||!w)){var g=(d.username||"").trim(),b=g.split("@")[0]||g||"—",h=(g.charAt(0)||"?").toUpperCase(),E=(d.avatar_url||"").trim();if(E){var y=E.replace(/"/g,"&quot;"),_=h.replace(/'/g,"\\'");f.innerHTML='<img src="'+y+'" alt="'+h+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+_+`'">`}else f.textContent=h;v.textContent=b,w.textContent=g||"—",f.setAttribute("title",g||"")}}};function n(){var l=document.getElementById("avatar-wrap"),d=document.getElementById("avatar-btn"),f=document.getElementById("avatar-popup");if(!l||!d||!f)return;function v(){f.classList.remove("show"),d.setAttribute("aria-expanded","false")}function w(){f.classList.add("show"),d.setAttribute("aria-expanded","true")}d.addEventListener("click",function(g){g.stopPropagation(),f.classList.contains("show")?v():w()}),document.addEventListener("click",function(g){f.classList.contains("show")&&!l.contains(g.target)&&v()}),f.addEventListener("click",function(g){var b=g.target.closest(".avatar-popup-item");if(b){var h=b.dataset.action;switch(v(),h){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var E=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(E||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var y=document.getElementById("help-modal");y&&(y.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=v}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(l){return l.style.display!=="none"})}function o(l){var d=a();d.forEach(function(f){f.classList.remove("focus")}),d[l]&&(d[l].classList.add("focus"),d[l].scrollIntoView({block:"nearest"}))}function s(l){var d=a();if(d.length){var f=d.findIndex(function(w){return w.classList.contains("focus")});f<0&&(f=0);var v=(f+l+d.length)%d.length;o(v)}}function i(l){l=(l||"").toLowerCase().trim();var d=0,f=window._userInfo,v=typeof isSuperAdmin=="function"?isSuperAdmin(f):!!(f&&f.is_super_admin),w=e(f);document.querySelectorAll(".cmdk-item").forEach(function(b){if(b.dataset.showIfAdmin==="1"&&!v){b.style.display="none";return}if(b.dataset.showIfTest==="1"&&!w){b.style.display="none";return}var h=(b.dataset.cmdkText||b.textContent||"").toLowerCase(),E=!l||h.indexOf(l)>=0;b.style.display=E?"":"none",b.classList.remove("focus"),E&&d++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(b){for(var h=b.nextElementSibling,E=!1;h&&!h.hasAttribute("data-cmdk-section");){if(h.classList&&h.classList.contains("cmdk-item")&&h.style.display!=="none"){E=!0;break}h=h.nextElementSibling}b.style.display=E?"":"none"});var g=document.getElementById("cmdk-empty");g&&(g.style.display=d===0?"flex":"none"),o(0)}window.openCmdk=function(){var d=document.getElementById("cmdk-mask");d&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),d.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var f=document.getElementById("cmdk-input");f&&(f.value="",i(""),f.focus(),o(0))},50))},window.closeCmdk=function(){var d=document.getElementById("cmdk-mask");d&&d.classList.remove("show")};function r(l){if(l){if(l.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var d=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(d||"即将上线","info")}return}var f=l.dataset.cmdkRoute,v=l.dataset.cmdkAction;if(window.closeCmdk(),f){typeof routeTo=="function"&&routeTo(f);return}if(v){if(v==="open-admin"){window.location.href="/admin/cost";return}if(v.indexOf("lang-")===0){var w=v.slice(5);typeof applyLang=="function"&&applyLang(w)}}}}function c(){var l=document.getElementById("cmdk-mask"),d=document.getElementById("cmdk-input"),f=document.getElementById("cmdk-body");if(!(!l||!d||!f)){l.addEventListener("click",function(g){g.target===l&&window.closeCmdk()});var v=document.getElementById("cmdk-esc-btn");v&&v.addEventListener("click",function(){window.closeCmdk()}),d.addEventListener("input",function(g){i(g.target.value)}),d.addEventListener("keydown",function(g){g.key==="ArrowDown"?(g.preventDefault(),s(1)):g.key==="ArrowUp"?(g.preventDefault(),s(-1)):g.key==="Enter"?(g.preventDefault(),r(l.querySelector(".cmdk-item.focus"))):g.key==="Escape"&&(g.preventDefault(),window.closeCmdk())}),f.addEventListener("click",function(g){var b=g.target.closest(".cmdk-item");b&&r(b)}),f.addEventListener("mousemove",function(g){var b=g.target.closest(".cmdk-item");!b||b.style.display==="none"||b.classList.contains("cmdk-item-locked")||(a().forEach(function(h){h.classList.remove("focus")}),b.classList.add("focus"))});var w=document.getElementById("topbar-search");w&&(w.addEventListener("click",function(){window.openCmdk()}),w.addEventListener("keydown",function(g){(g.key==="Enter"||g.key===" ")&&(g.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(l){if((l.metaKey||l.ctrlKey)&&(l.key==="k"||l.key==="K")){l.preventDefault(),window.openCmdk();return}if(l.key==="Escape"){var d=document.getElementById("cmdk-mask");if(d&&d.classList.contains("show")){window.closeCmdk();return}var f=document.getElementById("avatar-popup");f&&f.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var m=(navigator.userAgent||"").toLowerCase(),p=m.indexOf("mac")>=0||m.indexOf("iphone")>=0||m.indexOf("ipad")>=0;p||document.body.classList.add("is-windows")}catch{}function u(){n(),c(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",u):u()})();(function(){function n(v){return String(v??"").replace(/[&<>"']/g,function(w){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[w]})}function a(v){if(!v||isNaN(v))return"";var w=Number(v);return w<1024?w+" B":w<1024*1024?(w/1024).toFixed(1)+" KB":(w/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(v){var w=v.target.closest&&v.target.closest(".recon-collapse-head");if(w&&!(v.target.closest("button")||v.target.closest("a"))){var g=w.closest(".recon-collapse");if(g){var b=g.getAttribute("data-collapsed")==="true";g.setAttribute("data-collapsed",b?"false":"true"),b&&(g.id==="vex-summary-collapse"&&u(),g.id==="vex-detail-collapse"&&l())}}}),document.addEventListener("keydown",function(v){if(!(v.key!=="Enter"&&v.key!==" ")){var w=v.target.closest&&v.target.closest(".recon-collapse-head");w&&(v.preventDefault(),w.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){m("vat"),m("gl")}function c(v){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(v)||[]}catch{}var w=document.getElementById(v==="vat"?"glv-vat-input":"glv-gl-input");return w&&w.files?Array.from(w.files):[]}function m(v){var w=document.getElementById(v==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(w){var g=c(v),b=v==="vat"?"glv-up-vat-title":"glv-up-gl-title",h=v==="vat"?"① 销项税报告":"② 总账 GL",E=window.t&&window.t(b)||h,y=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),_=n(window.t&&window.t("vex-preview-clear-all")||"全清"),k=o[v]||"",x=g.length;w.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(E)+' <span class="vex-pp-col-count">'+x+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+v+'" type="text" placeholder="'+y+'" value="'+n(k)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+v+'" type="button">'+_+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+v+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+v+'-pg"></div>';var B=document.getElementById("glv-pp-search-"+v);B&&B.addEventListener("input",function(I){o[v]=I.target.value,p(v)});var L=document.getElementById("glv-pp-clearall-"+v);L&&L.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(v)}),p(v)}}function p(v){var w=document.getElementById("glv-pp-"+v+"-list"),g=document.getElementById("glv-pp-"+v+"-pg");if(w){var b=c(v),h=(o[v]||"").toLowerCase(),E=b.map(function(k,x){return{f:k,i:x}}),y=h?E.filter(function(k){return k.f.name.toLowerCase().indexOf(h)>=0}):E;if(w.innerHTML=y.map(function(k){var x=k.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(x.name)+'">'+n(x.name)+'</span><span class="vex-pp-fi-size">'+a(x.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+v+'" data-idx="'+k.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),w.querySelectorAll(".vex-pp-fi-del").forEach(function(k){k.addEventListener("click",function(){var x=k.dataset.kind,B=parseInt(k.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(x,isNaN(B)?null:B)})}),g){var _=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";g.textContent=_.replace("{n}",y.length).replace("{m}",y.length)}}}function u(){var v=function(g,b){var h=document.getElementById(g);h&&(h.textContent=b==null?"—":String(b))},w=window._vexLastTask||{};v("vex-sum-total",w.total),v("vex-sum-matched",w.matched),v("vex-sum-diff",w.diff),v("vex-sum-incomplete",w.incomplete),v("vex-sum-cash",w.cash),document.getElementById("vex-summary-sub")}function l(){var v=window._vexLastTask&&window._vexLastTask.diff_rows||[],w=document.getElementById("vex-detail-tbody"),g=document.getElementById("vex-detail-table"),b=document.getElementById("vex-detail-empty");if(!(!w||!g||!b)){if(v.length===0){g.style.display="none",b.style.display="";return}b.style.display="none",g.style.display="";var h=v.map(function(y){return'<tr><td class="recon-detail-cell-mono">'+n(y.invoice_no||"")+"</td><td>"+n(y.field||"")+"</td><td>"+n(y.report_value||"")+"</td><td>"+n(y.invoice_value||"")+"</td><td>"+n(y.kind||"")+"</td></tr>"}).join("");w.innerHTML=h;var E=document.getElementById("vex-detail-sub");E&&(E.textContent=String(v.length))}}function d(){var v=document.getElementById("glv-toggle-preview");v&&!v._reconBound&&(v._reconBound=!0,v.addEventListener("click",function(){var w=document.getElementById("glv-preview-panel"),g=document.getElementById("glv-toggle-preview-label"),b=w&&w.style.display!=="none";w&&(w.style.display=b?"none":""),v.classList.toggle("open",!b),g&&(g.textContent=b?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),b||r()})),["glv-vat-input","glv-gl-input"].forEach(function(w){var g=document.getElementById(w);!g||g._reconWatched||(g._reconWatched=!0,g.addEventListener("change",function(){var b=document.getElementById("glv-preview-panel");b&&b.style.display!=="none"&&r()}))})}function f(){var v=document.getElementById("vex-summary-collapse"),w=document.getElementById("vex-detail-collapse");v&&(v.style.display=""),w&&(w.style.display=""),u(),l()}window._fillVexSummary=u,window._fillVexDetail=l,window._onVexResultShown=f,document.addEventListener("DOMContentLoaded",function(){d()}),setTimeout(d,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var v=document.getElementById("glv-preview-panel");v&&v.style.display!=="none"&&r();var w=document.getElementById("glv-toggle-preview-label"),g=document.getElementById("glv-toggle-preview");w&&g&&(w.textContent=g.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:u,fillVexDetail:l}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(c=>{c.addEventListener("click",()=>{i.forEach(d=>d.classList.remove("active")),c.classList.add("active");const m=c.dataset.reconTab,p=document.getElementById("recon-pane-bank"),u=document.getElementById("recon-pane-sale-vat"),l=document.getElementById("recon-pane-gl-vat");p&&(p.style.display=m==="bank"?"":"none"),u&&(u.style.display=m==="sale-vat"?"":"none"),l&&(l.style.display=m==="gl-vat"?"":"none"),m==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),m==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const c=document.createElement("button");return c.id="settings-modal-close",c.className="settings-modal-close",c.setAttribute("aria-label","close"),c.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(c,i.firstChild),c.addEventListener("click",s),r.addEventListener("click",m=>{m.target===r&&s()}),r}function o(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(m){console.warn("renderSettings:",m)}let c=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');c&&c.click()},50)}function s(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();const hn=1e3,gn=30,ta=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,ee=e=>document.getElementById(e);function Je(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function be(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function Bo(e){return e<1024?e+" B":e<1024*1024?(e/1024).toFixed(1)+" KB":(e/1024/1024).toFixed(1)+" MB"}const P={invoiceFiles:[],reportFiles:[],running:!1,vexAllRows:[],previewLimitInv:50,previewLimitRep:50,previewSearchInv:"",previewSearchRep:"",vexPage:1};async function Ot(){try{const e=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:Je()});if(!e.ok)return;const a=(await e.json()).kpi||{};[["vex-kpi-month-val",a.this_month],["vex-kpi-running-val",a.running],["vex-kpi-done-val",a.done],["vex-kpi-failed-val",a.failed]].forEach(([o,s])=>{const i=document.getElementById(o);i&&(i.textContent=s??0)})}catch{}}async function Vt(){try{const e=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:Je()});if(!e.ok)return;const n=await e.json();Zt(n.rows||[])}catch{}}const ot=10;function Io(){var e=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(P.vexPage=1,Zt(P.vexAllRows),!!e){var n=document.getElementById("vex-task-tbody");n&&n.querySelectorAll("tr").forEach(function(a){a.dataset.taskId&&(a.style.display=a.textContent.toLowerCase().indexOf(e)>=0?"":"none")})}}function Zt(e){P.vexAllRows=e||P.vexAllRows;const n=document.getElementById("vex-task-tbody");if(!n)return;if(!P.vexAllRows.length){n.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",La(0);return}const a=Math.ceil(P.vexAllRows.length/ot);P.vexPage>a&&(P.vexPage=a);const o=(P.vexPage-1)*ot;Rr(P.vexAllRows.slice(o,o+ot)),La(P.vexAllRows.length)}function La(e){const n=document.getElementById("vex-task-pager"),a=document.getElementById("vex-task-pager-info"),o=document.getElementById("vex-task-prev"),s=document.getElementById("vex-task-next");if(!n)return;if(e<=ot){n.style.display="none";return}n.style.display="";const i=Math.ceil(e/ot);a&&(a.textContent=P.vexPage+" / "+i),o&&(o.disabled=P.vexPage<=1),s&&(s.disabled=P.vexPage>=i)}function Rr(e){const n=document.getElementById("vex-task-tbody");if(!n)return;const a={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},o={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},s='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',i='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';n.innerHTML=e.map(r=>{const c=r.created_at?new Date(r.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",m=r.period||"—",p=r.matched_count!=null?r.matched_count+" ✓ · "+r.mismatched_count+" ⚠":"—",u=r.mismatch_amount!=null?"฿ "+Number(r.mismatch_amount).toLocaleString():"—",l=r.elapsed_seconds!=null?r.elapsed_seconds.toFixed(1)+" s":"—",d=r.status||"pending",f=r.client_name&&r.client_name!=="client"?r.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${be(r.id)}" style="cursor:pointer">
            <td>${c}</td>
            <td>${be(f)}</td>
            <td>${be(m)}</td>
            <td>${(r.invoice_count||0)+" / "+(r.report_count||0)}</td>
            <td>${p}</td>
            <td>${u}</td>
            <td><span class="badge ${o[d]||"badge-gray"}">${a[d]||d}</span></td>
            <td>${l}</td>
            <td><div class="vex-task-actions">
                <button class="vex-task-dl-btn" data-task-id="${be(r.id)}" title="${t("hist_export")||"导出"}">${s}</button>
                <button class="vex-task-del-btn" data-task-id="${be(r.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${i}</button>
            </div></td>
        </tr>`}).join(""),n.querySelectorAll(".vex-task-dl-btn").forEach(r=>{r.addEventListener("click",async c=>{c.stopPropagation();const m=r.dataset.taskId;try{const p=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(m)+"/download",{credentials:"include",headers:Je()});if(p.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!p.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const u=await p.blob(),d=(p.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),f=d?decodeURIComponent(d[1]):"vat_recon_"+m+".xlsx",v=URL.createObjectURL(u),w=document.createElement("a");w.href=v,w.download=f,w.click(),setTimeout(()=>URL.revokeObjectURL(v),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),n.querySelectorAll(".vex-task-del-btn").forEach(r=>{r.addEventListener("click",c=>{c.stopPropagation(),Nr(r.dataset.taskId)})}),Io()}function zr(){var e=document.getElementById("vex-task-prev"),n=document.getElementById("vex-task-next");e&&!e._vexBound&&(e._vexBound=!0,e.addEventListener("click",function(){P.vexPage>1&&(P.vexPage--,Zt())})),n&&!n._vexBound&&(n._vexBound=!0,n.addEventListener("click",function(){var a=Math.ceil(P.vexAllRows.length/ot);P.vexPage<a&&(P.vexPage++,Zt())}))}async function Nr(e){const n=t("vex-task-delete-confirm-title")||"删除对账任务?",a=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(a,{title:n,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const s=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(e),{method:"DELETE",credentials:"include",headers:Je()});if(!s.ok)throw new Error(s.status);showToast(t("vex-task-delete-ok")||"已删除","success"),Vt(),Ot()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function Lo(e){const n=window._currentLang||"th",a={zh:`已忽略 ${e} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${e} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${e} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${e} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(a[n]||a.th,"warn")}function Or(e){const n=new Set(P.invoiceFiles.map(o=>o.name+"|"+o.size));let a=0;for(const o of e){if(!ta.test(o.name)){a++;continue}const s=o.name+"|"+o.size;if(!n.has(s)&&(n.add(s),P.invoiceFiles.push(o),P.invoiceFiles.length>=hn))break}a>0&&Lo(a),P.invoiceFiles.length>hn&&(P.invoiceFiles=P.invoiceFiles.slice(0,hn),showToast(t("vex-toast-cap-inv"),"warn")),Fe()}function Vr(e){const n=new Set(P.reportFiles.map(o=>o.name+"|"+o.size));let a=0;for(const o of e){if(!ta.test(o.name)){a++;continue}const s=o.name+"|"+o.size;if(!n.has(s)&&(n.add(s),P.reportFiles.push(o),P.reportFiles.length>=gn))break}a>0&&Lo(a),P.reportFiles.length>gn&&(P.reportFiles=P.reportFiles.slice(0,gn),showToast(t("vex-toast-cap-rep"),"warn")),Fe()}function Co(e){P.invoiceFiles.splice(e,1),Fe()}function So(e){P.reportFiles.splice(e,1),Fe()}function Fe(){const e=ee("vex-list-invoice"),n=ee("vex-list-report"),a=ee("vex-count-invoice"),o=ee("vex-count-report");a&&(a.textContent=P.invoiceFiles.length),o&&(o.textContent=P.reportFiles.length);const s=(c,m,p)=>`<div class="vex-fi">
        <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
        <span class="vex-fi-n" title="${be(c.name)}">${be(c.name)}</span>
        <span class="vex-fi-s">${Bo(c.size)}</span>
        <button class="vex-fi-x" type="button" data-vex-kind="${p}" data-vex-idx="${m}" aria-label="remove">×</button>
    </div>`;e&&(e.innerHTML=P.invoiceFiles.map((c,m)=>s(c,m,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),n&&(n.innerHTML=P.reportFiles.map((c,m)=>s(c,m,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(c=>{c.addEventListener("click",m=>{const p=c.dataset.vexKind,u=parseInt(c.dataset.vexIdx,10);p==="inv"?Co(u):So(u)})});const i=P.invoiceFiles.length>0&&P.reportFiles.length>0;ee("vex-build").disabled=!i||P.running;const r=ee("vex-action-info");r&&(!P.invoiceFiles.length||!P.reportFiles.length?(r.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",r.className="vex-action-info muted"):(r.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",P.invoiceFiles.length).replace("{b}",P.reportFiles.length),r.className="vex-action-info ok")),Ln()}const Ur='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',Gr='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',Kr='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function Ln(){const e=ee("vex-preview-panel");if(!e||e.style.display==="none")return;Ca("inv"),Ca("rep");const n=ee("vex-pp-guide");n&&(n.style.display=P.invoiceFiles.length>100?"flex":"none")}function Ca(e){const n=ee(e==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!n)return;const a=e==="inv"?P.invoiceFiles:P.reportFiles,o=e==="inv"?P.previewSearchInv:P.previewSearchRep,s=t(e==="inv"?"vex-preview-invoice":"vex-preview-report")||(e==="inv"?"销售发票":"VAT 报告"),i=be(t("vex-preview-search")||"搜索文件名..."),r=be(t("vex-preview-clear-all")||"全清");n.innerHTML=`
        <div class="vex-pp-col-title">
            <span class="vex-pp-col-name">${be(s)} <span class="vex-pp-col-count">${a.length}</span></span>
        </div>
        <div class="vex-pp-search-row">
            <input class="vex-pp-search" id="vex-pp-search-${e}" type="text"
                   placeholder="${i}" value="${be(o)}" autocomplete="off">
            <button class="vex-pp-clear-btn" id="vex-pp-clearall-${e}" type="button">${r}</button>
        </div>
        <div class="vex-pp-file-list" id="vex-pp-${e}-list"></div>
        <div class="vex-pp-pagination" id="vex-pp-${e}-pg"></div>`;const c=ee("vex-pp-search-"+e);c&&c.addEventListener("input",p=>{e==="inv"?(P.previewSearchInv=p.target.value,P.previewLimitInv=50):(P.previewSearchRep=p.target.value,P.previewLimitRep=50),Cn(e)});const m=ee("vex-pp-clearall-"+e);m&&m.addEventListener("click",()=>{e==="inv"?(P.invoiceFiles=[],P.previewSearchInv="",P.previewLimitInv=50):(P.reportFiles=[],P.previewSearchRep="",P.previewLimitRep=50),Fe()}),Cn(e)}function Cn(e){const n=ee("vex-pp-"+e+"-list"),a=ee("vex-pp-"+e+"-pg");if(!n)return;const o=e==="inv"?P.invoiceFiles:P.reportFiles,s=e==="inv"?P.previewSearchInv:P.previewSearchRep,i=e==="inv"?P.previewLimitInv:P.previewLimitRep,r=e==="inv"?Ur:Gr,c=o.map((u,l)=>({f:u,i:l})),m=s?c.filter(({f:u})=>u.name.toLowerCase().includes(s.toLowerCase())):c,p=m.slice(0,i);if(n.innerHTML=p.map(({f:u,i:l})=>`
        <div class="vex-pp-file-row">
            ${r}
            <span class="vex-pp-fi-name" title="${be(u.name)}">${be(u.name)}</span>
            <span class="vex-pp-fi-size">${Bo(u.size)}</span>
            <button class="vex-pp-fi-del" type="button" data-kind="${e}" data-ridx="${l}" aria-label="remove">${Kr}</button>
        </div>`).join("")+`<div id="vex-pp-sentinel-${e}" style="height:1px;flex-shrink:0"></div>`,n.querySelectorAll(".vex-pp-fi-del").forEach(u=>{u.addEventListener("click",()=>{const l=parseInt(u.dataset.ridx,10);u.dataset.kind==="inv"?Co(l):So(l)})}),a){const u=t("vex-preview-count")||"显示前 {n} / 共 {m}";a.textContent=u.replace("{n}",p.length).replace("{m}",m.length)}Jr(e,m.length)}function Jr(e,n){if((e==="inv"?P.previewLimitInv:P.previewLimitRep)>=n)return;const o=ee("vex-pp-sentinel-"+e),s=ee("vex-pp-"+e+"-list");if(!o||!s)return;const i=new IntersectionObserver(r=>{r[0].isIntersecting&&(i.disconnect(),e==="inv"?P.previewLimitInv+=50:P.previewLimitRep+=50,Cn(e))},{root:s,threshold:.8});i.observe(o)}function Sa(e,n,a,o){const s=ee(e),i=ee(n);!s||!i||(s.addEventListener("click",()=>i.click()),s.addEventListener("keydown",r=>{(r.key==="Enter"||r.key===" ")&&(r.preventDefault(),i.click())}),s.addEventListener("dragover",r=>{r.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",()=>s.classList.remove("drag-over")),s.addEventListener("drop",r=>{r.preventDefault(),s.classList.remove("drag-over");const m=Array.from(r.dataTransfer.files).filter(p=>ta.test(p.name));if(!m.length){showToast(t("vex-toast-bad-ext"),"error");return}a(m)}),i.addEventListener("change",()=>{const r=Array.from(i.files);a(r),i.value=""}))}(function(){async function e(){if(P.running||!P.invoiceFiles.length||!P.reportFiles.length)return;P.running=!0,ee("vex-build").disabled=!0,ee("vex-progress").style.display="flex";var r=document.getElementById("vex-download");r&&(r.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(u){var l=document.getElementById(u);l&&(l.style.display="none")});const c=Date.now();ee("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",ee("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",P.invoiceFiles.length).replace("{b}",P.reportFiles.length);const m=setInterval(()=>{const u=Math.floor((Date.now()-c)/1e3);ee("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",u).replace("{a}",P.invoiceFiles.length).replace("{b}",P.reportFiles.length)},1e3);try{const u=new FormData;for(const I of P.invoiceFiles)u.append("invoices",I);for(const I of P.reportFiles)u.append("reports",I);const l=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";u.append("lang",l);const d=localStorage.getItem("mrpilot_token")||"",f=await fetch("/api/vat_excel/submit",{method:"POST",headers:Je(),body:u});let v=null;try{v=await f.json()}catch{v=null}if(!f.ok||!v||!v.ok||!v.job_id)throw clearInterval(m),new Error(v&&v.detail||"HTTP "+f.status);const w=ee("vex-progress-sub"),g=await window._reconPollJob(v.job_id,d,{onProgress:I=>{w&&(w.textContent=window._reconProgressText(I,l))}});if(clearInterval(m),!g||g.status!=="done"||!g.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const b=g.result_id;let h=0;const E=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(b)+"/download",{headers:Je()});if(!E.ok)throw new Error("HTTP "+E.status);const _=(E.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),k=_&&_[1]||"vat_recon_"+Date.now()+".xlsx",x=await E.blob(),B=URL.createObjectURL(x),L=ee("vex-download");L.href=B,L.download=k;try{const I=document.createElement("a");I.href=B,I.download=k,document.body.appendChild(I),I.click(),setTimeout(()=>I.remove(),100)}catch{}ee("vex-progress").style.display="none";var p=document.getElementById("vex-download");p&&(p.style.display=""),b&&(h=await o(b)),window._onVexResultShown&&window._onVexResultShown(),h>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",h),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),Ot(),setTimeout(Vt,800)}catch(u){clearInterval(m),ee("vex-progress").style.display="none";const l=(t("vex-toast-fail")||"生成失败")+": "+(u.message||u);showToast(l,"error")}finally{P.running=!1,ee("vex-build").disabled=!1}}function n(){P.invoiceFiles=[],P.reportFiles=[];var r=document.getElementById("vex-download");r&&(r.style.display="none"),Fe()}function a(r){if(r==null)return"—";var c=parseFloat(r);return isNaN(c)?"—":c.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function o(r){try{var c=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(r),{headers:Je()});if(!c.ok)throw new Error(c.status);var m=await c.json(),p=m.raw_data_json;if(typeof p=="string")try{p=JSON.parse(p)}catch{p={}}p=p||{};var u=p.rows||[],l=[];u.forEach(function(v){v.kind==="invoice_orphan"?l.push({invoice_no:v.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:a(v.amount_inv),kind:v.kind}):v.kind==="report_orphan"?l.push({invoice_no:v.invoice_no||"",field:"仅报告有",report_value:a(v.amount_rep),invoice_value:"—",kind:v.kind}):v.dims&&Object.keys(v.dims).length>0&&Object.keys(v.dims).forEach(function(w){var g=String(v.dims[w]||""),b=g.split(" ≠ ");l.push({invoice_no:v.invoice_no||"",field:w,report_value:b[0]||g,invoice_value:b.length>1?b[1]:"—",kind:"diff"})})});var d=u.filter(function(v){return v.kind==="matched_cash"}).length,f=Math.max(0,parseInt(p.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:p.n_total||0,matched:p.n_ok||0,diff:p.n_diff||0,incomplete:f,cash:d,diff_rows:l,task_id:r},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),f}catch{return 0}}function s(){const r=document.getElementById("vex-pane");r&&r.querySelectorAll("[data-i18n]").forEach(c=>{const m=t(c.dataset.i18n);m&&(c.textContent=m)}),Fe(),Vt()}function i(){Sa("vex-drop-invoice","vex-input-invoice",Or),Sa("vex-drop-report","vex-input-report",Vr);const r=ee("vex-build"),c=ee("vex-reset");r&&r.addEventListener("click",e),c&&c.addEventListener("click",n),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(u=>{u.addEventListener("click",()=>{Ot(),Vt()})}),zr();const m=document.getElementById("vex-task-search");m&&m.addEventListener("input",Io);const p=document.getElementById("vex-toggle-preview");p&&p.addEventListener("click",()=>{const u=ee("vex-preview-panel"),l=ee("vex-toggle-preview-label"),d=u&&u.style.display!=="none";u&&(u.style.display=d?"none":""),p&&p.classList.toggle("open",!d),l&&(l.textContent=d?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),d||Ln()}),Fe(),Ot()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",i):i(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",s),window.subscribeI18n("vex-preview-panel",Ln))})();const Y={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},W=e=>document.getElementById(e),To=()=>localStorage.getItem("mrpilot_token")||"",pt=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",We=()=>({Authorization:"Bearer "+To()}),Ta={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},se=e=>(Ta[pt()]||Ta.th)[e]||e;function Wr(e){const n=pt(),o={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[e];return o?o[n]||o.th||o.en:se("error")||"Error"}const Lt=e=>e==null||isNaN(e)?"":Number(e).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function na(e){W("glv-kpi-matched")&&(W("glv-kpi-matched").textContent=e&&e.matched!=null?e.matched:"—"),W("glv-kpi-diff")&&(W("glv-kpi-diff").textContent=e&&e.diff!=null?e.diff:"—"),W("glv-kpi-unmatched")&&(W("glv-kpi-unmatched").textContent=e&&e.unmatched!=null?e.unmatched:"—")}function Yr(e){if(!e)return"";try{const n=new Date(e);if(isNaN(n.getTime()))return e;const a=o=>String(o).padStart(2,"0");return n.getFullYear()+"-"+a(n.getMonth()+1)+"-"+a(n.getDate())+" "+a(n.getHours())+":"+a(n.getMinutes())}catch{return e}}function Ma(e,n,a,o){const s=W(e),i=W(n),r=W(a);if(!s||!i||!r)return;const c=m=>{if(!m||!m.length)return;const p=Array.isArray(Y[o])?Y[o].slice():[],u=new Set(p.map(l=>l.name+"|"+l.size));for(const l of m){if(!l)continue;const d=l.name+"|"+l.size;u.has(d)||(p.push(l),u.add(d))}Y[o]=p,Mo(r,p),$t(),At(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};s.addEventListener("click",()=>i.click()),s.addEventListener("keydown",m=>{(m.key==="Enter"||m.key===" ")&&(m.preventDefault(),i.click())}),i.addEventListener("change",()=>{c(Array.from(i.files||[])),i.value=""}),s.addEventListener("dragover",m=>{m.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",()=>s.classList.remove("drag-over")),s.addEventListener("drop",m=>{m.preventDefault(),s.classList.remove("drag-over");const p=m.dataTransfer&&m.dataTransfer.files?Array.from(m.dataTransfer.files):[];c(p)})}function Mo(e,n){if(!e)return;if(!n||n.length===0){e.textContent="";return}const a=n.reduce((o,s)=>o+Math.round(s.size/1024),0);if(n.length===1)e.textContent=n[0].name+"  ("+a+" KB)";else{const o=window.t&&window.t("glv-files-count")||"{n} 个文件";e.textContent=o.replace("{n}",n.length)+"  ("+a+" KB)"}}function Pe(e){const n=Y[e];return Array.isArray(n)?n:n?[n]:[]}function $t(){const e=W("btn-glv-run");if(!e)return;const n=Pe("glFile").length>0&&Pe("vatFile").length>0;e.disabled=!n||Y.running}function At(){const e=W("glv-status");if(!e||Y.running)return;const n=Pe("vatFile").length,a=Pe("glFile").length;n===0&&a===0?(e.className="vex-action-info muted",e.innerHTML="<span>"+se("hint_need_both")+"</span>"):n>0&&a>0?(e.className="vex-action-info ok",e.innerHTML="<span>"+se("hint_ready")+"</span>"):(e.className="vex-action-info muted",e.innerHTML="<span>"+se("hint_need_one_more")+"</span>")}function Zr(e,n){const a=e==="vat"?"vatFile":"glFile",o=e==="vat"?"glv-vat-input":"glv-gl-input",s=e==="vat"?"glv-vat-name":"glv-gl-name",i=Pe(a);n==null?Y[a]=[]:Y[a]=i.filter((c,m)=>m!==n);const r=W(o);r&&(r.value=""),Mo(W(s),Pe(a)),$t(),At(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function Xr(){Y.glFile=[],Y.vatFile=[],Y.currentTaskId=null,Y.lastDetail=[],Y.lastSummary=null;const e=W("glv-vat-input");e&&(e.value="");const n=W("glv-gl-input");n&&(n.value="");const a=W("glv-vat-name");a&&(a.textContent="");const o=W("glv-gl-name");o&&(o.textContent="");const s=W("glv-result");s&&(s.style.display="none");const i=W("glv-kpi-strip");i&&(i.style.display="none"),$t(),At(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function aa(e){const n=W("glv-tbody");if(!n)return;tl(e.length),n.innerHTML="";const a=se("not_found"),o=document.createDocumentFragment();e.forEach(s=>{const i=document.createElement("tr"),r=(l,d)=>{const f=document.createElement("td");return d&&(f.className=d),f.textContent=l,f},c=s.gl_amount===null||s.gl_amount===void 0,m=s.diff;let p="glv-num",u="glv-num";c?(u+=" glv-cell-missing",p+=" glv-cell-missing"):Math.abs(m||0)<.005?p+=" glv-cell-ok":p+=" glv-cell-diff",i.appendChild(r(s.doc_no||"","glv-doc")),i.appendChild(r(s.date||"","")),i.appendChild(r(s.customer_name||"","")),i.appendChild(r(Lt(s.vat_amount),"glv-num")),i.appendChild(r(c?a:Lt(s.gl_amount),u)),i.appendChild(r(c?a:Lt(s.diff),p)),i.appendChild(r(s.account_codes||"","glv-doc")),o.appendChild(i)}),n.appendChild(o)}function oa(e){const n=W("glv-summary-table")&&W("glv-summary-table").querySelector("tbody");if(!n)return;n.innerHTML="",[{label:se("s_gl_total"),amount:e.gl_total,emph:!0,items:[],negate:!1},{label:se("s_minus_gl_cr"),amount:-(e.gl_only_credit||0),emph:!1,items:e.gl_only_credit_items||[],negate:!0},{label:se("s_plus_gl_dr"),amount:e.gl_only_debit||0,emph:!1,items:e.gl_only_debit_items||[],negate:!1},{label:se("s_plus_vat_p"),amount:e.vat_only_positive||0,emph:!1,items:e.vat_only_positive_items||[],negate:!1},{label:se("s_minus_vat_n"),amount:e.vat_only_negative||0,emph:!1,items:e.vat_only_negative_items||[],negate:!1},{label:se("s_vat_total"),amount:e.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:o,amount:s,emph:i,items:r,negate:c})=>{const m=document.createElement("tr");m.className=i?"glv-summary-total":"glv-summary-sect";const p=document.createElement("td"),u=document.createElement("td");p.textContent=o,u.textContent=i?Lt(s):"",m.appendChild(p),m.appendChild(u),n.appendChild(m),(r||[]).forEach(l=>{const d=document.createElement("tr");d.className="glv-summary-item";const f=document.createElement("td"),v=document.createElement("td"),w=[l.doc_no,l.date,l.name].filter(Boolean);f.textContent="· "+w.join("  ·  ");const g=c?-(l.amount||0):l.amount||0;v.textContent=Lt(g),d.appendChild(f),d.appendChild(v),n.appendChild(d)})})}async function Qr(e){try{const a=await(await fetch("/api/recon/gl-vat/"+e,{headers:We()})).json();if(!a||!a.ok)throw new Error("load_failed");Y.currentTaskId=e,Y.lastDetail=a.detail||[],Y.lastSummary=a.summary||{},na(a.stats||{}),aa(Y.lastDetail),oa(Y.lastSummary);const o=W("glv-result");o&&(o.style.display=""),$o(),window.scrollTo({top:o?o.offsetTop-80:0,behavior:"smooth"})}catch(n){console.error("[gl-vat] load task failed:",n),alert(se("error")+": "+(n.message||n))}}function $o(){var e=W("glv-kpi-strip");e&&(e.style.display="");var n=W("glv-section-summary");n&&n.setAttribute("data-collapsed","false");var a=W("glv-section-detail");a&&a.setAttribute("data-collapsed","false")}function el(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(e=>{const n=e.getAttribute("data-toggle"),a=document.getElementById(n);if(!a)return;const o=s=>{if(s.target&&s.target.closest("button")!==null&&!s.target.classList.contains("glv-section-head"))return;const i=a.getAttribute("data-collapsed")==="true";a.setAttribute("data-collapsed",i?"false":"true")};e.addEventListener("click",o),e.addEventListener("keydown",s=>{(s.key==="Enter"||s.key===" ")&&(s.preventDefault(),o(s))})})}function tl(e){const n=W("glv-detail-count");n&&(n.textContent=e!=null?String(e):"")}const wt=10;var et=[],ke=1;function nl(){ke=1,Xt();var e=((W("glv-hist-search")||{}).value||"").trim().toLowerCase();if(e){var n=W("glv-history-tbody");n&&n.querySelectorAll("tr").forEach(function(a){a.dataset.taskId&&(a.style.display=a.textContent.toLowerCase().indexOf(e)>=0?"":"none")})}}function Xt(){const e=W("glv-history-table-wrap"),n=W("glv-history-empty"),a=W("glv-history-tbody"),o=W("glv-history-pager"),s=W("glv-history-pager-info"),i=W("glv-history-prev"),r=W("glv-history-next");if(!a)return;if(a.innerHTML="",!et.length){e&&(e.style.display="none"),n&&(n.style.display=""),o&&(o.style.display="none");return}e&&(e.style.display=""),n&&(n.style.display="none");const c=Math.ceil(et.length/wt);ke>c&&(ke=c);const m=(ke-1)*wt,p=et.slice(m,m+wt);o&&(o.style.display=et.length>wt?"":"none",s&&(s.textContent=ke+" / "+c),i&&(i.disabled=ke<=1),r&&(r.disabled=ke>=c)),p.forEach(l=>{const d=document.createElement("tr");d.dataset.taskId=l.id;const f=document.createElement("td");f.textContent=Yr(l.created_at);const v=document.createElement("td");v.className="glv-history-file",v.title=(l.vat_filename||"")+" + "+(l.gl_filename||""),v.textContent=(l.vat_filename||"?")+" + "+(l.gl_filename||"?");const w=document.createElement("td");w.className="glv-num",w.textContent=(l.vat_row_count||0)+" / "+(l.gl_row_count||0);const g=document.createElement("td");g.className="glv-num",g.textContent=l.matched_count||0;const b=document.createElement("td");b.className="glv-num",b.textContent=l.diff_count||0;const h=document.createElement("td");h.className="glv-num",h.textContent=l.unmatched_count||0;const E=document.createElement("td");E.className="glv-history-actions";const y=(B,L,I,C)=>{const S=document.createElement("button");return S.type="button",I&&(S.className=I),S.title=L,S.setAttribute("aria-label",L),S.innerHTML=B,S.onclick=C,S},_='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',k='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',x='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';E.appendChild(y(_,se("hist_load"),"",()=>Qr(l.id))),E.appendChild(y(k,se("hist_export"),"",()=>ol(l.id))),E.appendChild(y(x,se("hist_delete"),"glv-del",()=>sl(l.id))),[f,v,w,g,b,h,E].forEach(B=>d.appendChild(B)),a.appendChild(d)})}function al(){var e=W("glv-history-prev"),n=W("glv-history-next");e&&!e._glvBound&&(e._glvBound=!0,e.addEventListener("click",function(){ke>1&&(ke--,Xt())})),n&&!n._glvBound&&(n._glvBound=!0,n.addEventListener("click",function(){var a=Math.ceil(et.length/wt);ke<a&&(ke++,Xt())}))}async function st(){try{const n=await(await fetch("/api/recon/gl-vat/tasks",{headers:We()})).json();et=n&&n.tasks||[],ke=1,Xt(),al()}catch(e){console.error("[gl-vat] history load failed:",e)}}async function ol(e){try{const n="/api/recon/gl-vat/"+e+"/export?lang="+encodeURIComponent(pt()),a=await fetch(n,{headers:We()});if(!a.ok)throw new Error("HTTP "+a.status);const o=await a.blob(),s=document.createElement("a");s.href=URL.createObjectURL(o),s.download="GL_VAT_recon_"+e+".xlsx",document.body.appendChild(s),s.click(),setTimeout(()=>{URL.revokeObjectURL(s.href),s.remove()},200)}catch(n){console.error("[gl-vat] exportTask failed:",n),typeof showToast=="function"&&showToast(se("error")+": "+(n.message||n),"error")}}async function sl(e){let n;if(typeof window.showConfirm=="function"?n=await window.showConfirm(se("confirm_delete"),{danger:!0}):n=confirm(se("confirm_delete")),!!n)try{const a=await fetch("/api/recon/gl-vat/"+e,{method:"DELETE",headers:We()});if(!a.ok)throw new Error("HTTP "+a.status);st()}catch(a){console.error("[gl-vat] delete failed:",a),typeof showToast=="function"&&showToast(se("error")+": "+(a.message||a),"error")}}async function il(){if(!Y.glFile||!Y.vatFile){typeof showToast=="function"&&showToast(se("need_files"),"warn");return}Y.running=!0,$t();const e=W("glv-status"),n=W("glv-progress"),a=W("glv-progress-sub");e&&(e.className="vex-action-info muted",e.style.color="",e.innerHTML="<span>"+se("running")+"</span>"),n&&(n.style.display=""),a&&(a.textContent=(Y.vatFile.name||"VAT")+" + "+(Y.glFile.name||"GL"));const o=new FormData,s=Pe("vatFile"),i=Pe("glFile");for(const c of s)o.append("vat_files",c,c.name);for(const c of i)o.append("gl_files",c,c.name);const r=(W("glv-prefix")&&W("glv-prefix").value||"4").trim()||"4";o.append("revenue_prefix",r),o.append("lang",pt());try{const c=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:We(),body:o});let m=null;try{m=await c.json()}catch{m=null}if(!c.ok||!m||!m.ok||!m.job_id)throw new Error(m&&m.detail||m&&m.error||"HTTP "+c.status);const p=W("glv-progress-sub"),u=await window._reconPollJob(m.job_id,To(),{onProgress:v=>{p&&(p.textContent=window._reconProgressText(v,pt()))}});if(!u||u.status!=="done"||!u.result_id)throw u&&u.status==="failed"&&u.error_code?new Error(Wr(u.error_code)):new Error(se("error")||"Error");const l=await fetch("/api/recon/gl-vat/"+encodeURIComponent(u.result_id),{headers:We()});let d=null;try{d=await l.json()}catch{d=null}if(!l.ok||!d||!d.ok)throw new Error(d&&d.detail||d&&d.error||"HTTP "+l.status);Y.currentTaskId=d.task_id,Y.lastDetail=d.detail||[],Y.lastSummary=d.summary||{},na(d.stats||{}),aa(Y.lastDetail),oa(Y.lastSummary);const f=W("glv-result");f&&(f.style.display=""),$o(),e&&(e.className="vex-action-info ok",e.style.color="",e.innerHTML="<span>"+se("done")+" · GL "+(d.gl_row_count||0)+" · VAT "+(d.vat_row_count||0)+"</span>"),st()}catch(c){console.error("[gl-vat] run failed:",c),e&&(e.className="vex-action-info",e.style.color="#ef4444",e.innerHTML="<span>"+se("error")+": "+(c.message||c)+"</span>")}finally{Y.running=!1,n&&(n.style.display="none"),$t()}}async function rl(){if(Y.currentTaskId)try{const e="/api/recon/gl-vat/"+Y.currentTaskId+"/export?lang="+encodeURIComponent(pt()),n=await fetch(e,{headers:We()});if(!n.ok)throw new Error("HTTP "+n.status);const a=await n.blob(),o=document.createElement("a");o.href=URL.createObjectURL(a),o.download="GL_VAT_recon_"+Y.currentTaskId+".xlsx",document.body.appendChild(o),o.click(),setTimeout(()=>{URL.revokeObjectURL(o.href),o.remove()},200)}catch(e){console.error("[gl-vat] export failed:",e),typeof showToast=="function"&&showToast(se("error")+": "+(e.message||e),"error")}}function ll(){Y.running||At(),st(),Y.lastDetail&&Y.lastDetail.length&&aa(Y.lastDetail),Y.lastSummary&&oa(Y.lastSummary)}function cl(){if(Y.inited){st();return}Y.inited=!0,Ma("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),Ma("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const e=W("btn-glv-run");e&&e.addEventListener("click",il);const n=W("btn-glv-export");n&&n.addEventListener("click",rl);const a=W("btn-glv-reset");a&&a.addEventListener("click",Xr);const o=W("glv-hist-search");o&&o.addEventListener("input",nl),el(),na(null),At(),window._loadGlvHistory=st,st(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",ll)}window._glvRemoveFile=Zr;window.GlVatRecon={ensureInit:cl};window._glvPreviewFiles=function(e){return Pe(e==="vat"?"vatFile":"glFile")};const dl=["flowaccount","peak","xero","quickbooks","express"],Ho={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},pl=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],ul=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],fl="468b50c1-5593-4fd6-990d-515ce8085563";let oe={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function qt(){const e=typeof _userInfo<"u"?_userInfo:null;return!!(e&&(e.role==="owner"||e.is_super_admin))}function ml(){const e=typeof _userInfo<"u"?_userInfo:null;return!!(e&&e.id===fl)}function M(e){return typeof escapeHtml=="function"?escapeHtml(e==null?"":String(e)):String(e??"")}function ze(e,n){try{typeof showToast=="function"&&showToast(e,n||"info")}catch{}}function vl(e){return e==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+M(t("erp-map-col-client"))+"</div><div>"+M(t("erp-map-col-erp"))+"</div><div>"+M(t("erp-map-col-erp-code"))+"</div><div>"+M(t("erp-map-col-notes"))+"</div><div>"+M(t("erp-map-col-actions"))+"</div></div>":e==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+M(t("erp-map-col-erp"))+"</div><div>"+M(t("erp-map-col-category"))+"</div><div>"+M(t("erp-map-col-erp-code"))+"</div><div>"+M(t("erp-map-col-erp-name"))+"</div><div>"+M(t("erp-map-col-notes"))+"</div><div>"+M(t("erp-map-col-actions"))+"</div></div>":e==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+M(t("erp-map-col-item-name"))+"</div><div>"+M(t("erp-map-col-erp-product-code"))+"</div><div>"+M(t("erp-map-col-erp-name"))+"</div><div>"+M(t("erp-map-col-notes"))+"</div><div>"+M(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+M(t("erp-map-col-erp"))+"</div><div>"+M(t("erp-map-col-tax"))+"</div><div>"+M(t("erp-map-col-erp-tax-code"))+"</div><div>"+M(t("erp-map-col-notes"))+"</div><div>"+M(t("erp-map-col-actions"))+"</div></div>"}function bn(e,n){let a='<select class="form-input" data-erp-field="'+n+'">';return a+='<option value="">'+M(t("erp-map-pick-erp"))+"</option>",dl.forEach(function(o){const s=o===e?" selected":"";a+='<option value="'+o+'"'+s+">"+M(Ho[o])+"</option>"}),a+="</select>",a}function hl(e){let n='<select class="form-input" data-erp-field="client_id">';return n+='<option value="">'+M(t("erp-map-pick-client"))+"</option>",(oe.clientList||[]).forEach(function(a){const o=String(a.id)===String(e)?" selected":"";n+='<option value="'+a.id+'"'+o+">"+M(a.name||"#"+a.id)+"</option>"}),n+="</select>",n}function gl(e){let n='<select class="form-input" data-erp-field="pearnly_category">';return n+='<option value="">'+M(t("erp-map-pick-cat"))+"</option>",pl.forEach(function(a){const o=a===e?" selected":"";n+='<option value="'+a+'"'+o+">"+M(t("erp-map-cat-"+a))+"</option>"}),n+="</select>",n}function bl(e){let n='<select class="form-input" data-erp-field="pearnly_tax_kind">';return n+='<option value="">'+M(t("erp-map-pick-tax"))+"</option>",ul.forEach(function(a){const o=a===e?" selected":"";n+='<option value="'+a+'"'+o+">"+M(t("erp-map-tax-"+a))+"</option>"}),n+="</select>",n}function yl(e){const n='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+M(t("erp-map-save"))+"</button>";return e==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+M(t("erp-map-col-client"))+'">'+hl("")+'</div><div data-label="'+M(t("erp-map-col-erp"))+'">'+bn("","erp_type")+'</div><div data-label="'+M(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+M(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+M(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+M(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>":e==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+M(t("erp-map-col-erp"))+'">'+bn("","erp_type")+'</div><div data-label="'+M(t("erp-map-col-category"))+'">'+gl("")+'</div><div data-label="'+M(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+M(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+M(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+M(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+M(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+M(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+M(t("erp-map-col-erp"))+'">'+bn("","erp_type")+'</div><div data-label="'+M(t("erp-map-col-tax"))+'">'+bl("")+'</div><div data-label="'+M(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+M(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+M(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+M(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>"}function wl(e,n,a){const o=a?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+M(n.id)+'" title="'+M(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',s='<span class="erp-map-erp-badge">'+M(Ho[n.erp_type]||n.erp_type)+"</span>";if(e==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+M(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+M(n.client_name||"#"+n.client_id)+'</div><div data-label="'+M(t("erp-map-col-erp"))+'">'+s+'</div><div data-label="'+M(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+M(n.erp_code||"")+'</div><div data-label="'+M(t("erp-map-col-notes"))+'">'+M(n.notes||"")+"</div><div>"+o+"</div></div>";if(e==="accounts"){const r=t("erp-map-cat-"+(n.pearnly_category||"other"))||n.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+M(t("erp-map-col-erp"))+'">'+s+'</div><div data-label="'+M(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+M(r)+'</div><div data-label="'+M(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+M(n.erp_code||"")+'</div><div data-label="'+M(t("erp-map-col-erp-name"))+'">'+M(n.erp_name||"")+'</div><div data-label="'+M(t("erp-map-col-notes"))+'">'+M(n.notes||"")+"</div><div>"+o+"</div></div>"}if(e==="products")return'<div class="erp-map-row row-products"><div data-label="'+M(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+M(n.item_name||"")+'</div><div data-label="'+M(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+M(n.erp_code||"")+'</div><div data-label="'+M(t("erp-map-col-erp-name"))+'">'+M(n.erp_name||"")+'</div><div data-label="'+M(t("erp-map-col-notes"))+'">'+M(n.notes||"")+"</div><div>"+o+"</div></div>";const i=t("erp-map-tax-"+(n.pearnly_tax_kind||""))||n.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+M(t("erp-map-col-erp"))+'">'+s+'</div><div data-label="'+M(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+M(i)+'</span></div><div data-label="'+M(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+M(n.erp_code||"")+'</div><div data-label="'+M(t("erp-map-col-notes"))+'">'+M(n.notes||"")+"</div><div>"+o+"</div></div>"}(function(){async function e(u,l){const d=localStorage.getItem("mrpilot_token");if(d&&!(oe.loaded[u]&&!l))try{const f=await fetch("/api/erp/mappings/"+u,{headers:{Authorization:"Bearer "+d}});if(!f.ok)throw new Error("http_"+f.status);const v=await f.json();oe.items[u]=v.items||[],oe.loaded[u]=!0}catch{oe.items[u]=[],oe.loaded[u]=!1}}async function n(u){if(oe.clientLoaded)return;const l=localStorage.getItem("mrpilot_token");if(l)try{const d=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+l}});if(!d.ok)throw new Error("http_"+d.status);const f=await d.json();oe.clientList=(f.clients||f.items||[]).filter(v=>v.is_active!==!1),oe.clientLoaded=!0}catch{oe.clientList=[]}}function a(){const u=document.getElementById("erp-map-pane-wrap");if(!u)return;const l=!qt();let d="";l&&(d+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+M(t("erp-map-readonly-tip"))+"</div>"),d+='<div class="erp-map-toolbar">',!l&&oe.sub!=="products"&&(d+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+M(t("erp-map-add-row"))+"</button>"),d+="</div>",d+='<div class="erp-map-table" id="erp-map-table-host"></div>',u.innerHTML=d,o();const f=document.getElementById("erp-map-dev-bar");f&&(f.style.display=qt()&&ml()?"":"none")}function o(){const u=document.getElementById("erp-map-table-host");if(!u)return;const l=oe.sub,d=oe.items[l]||[],f=oe.addingNew[l],v=!qt();if(!d.length&&!f){u.innerHTML='<div class="erp-map-empty"><strong>'+M(t("erp-map-empty-"+l))+"</strong>"+M(t("erp-map-empty-"+l+"-sub"))+"</div>";return}let w="";w+=vl(l),f&&!v&&(w+=yl(l)),d.forEach(function(g){w+=wl(l,g,v)}),u.innerHTML=w}async function s(u){const l=oe.sub,d={};u.querySelectorAll("[data-erp-field]").forEach(function(g){d[g.dataset.erpField]=(g.value||"").trim()});const f=localStorage.getItem("mrpilot_token");if(!f)return;let v={},w="/api/erp/mappings/"+l;if(l==="clients"){if(!d.client_id||!d.erp_type||!d.erp_code){ze(t("erp-map-save-fail"),"error");return}v={client_id:parseInt(d.client_id,10),erp_type:d.erp_type,erp_code:d.erp_code,notes:d.notes||""}}else if(l==="accounts"){if(!d.erp_type||!d.pearnly_category||!d.erp_code){ze(t("erp-map-save-fail"),"error");return}v={erp_type:d.erp_type,pearnly_category:d.pearnly_category,erp_code:d.erp_code,erp_name:d.erp_name||"",notes:d.notes||""}}else{if(!d.erp_type||!d.pearnly_tax_kind||!d.erp_code){ze(t("erp-map-save-fail"),"error");return}v={erp_type:d.erp_type,pearnly_tax_kind:d.pearnly_tax_kind,erp_code:d.erp_code,notes:d.notes||""}}try{const g=await fetch(w,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+f},body:JSON.stringify(v)});if(!g.ok)throw new Error("http_"+g.status);oe.addingNew[l]=!1,await e(l,!0),o(),ze(t("erp-map-saved-toast"),"success")}catch{ze(t("erp-map-save-fail"),"error")}}async function i(u){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const d=oe.sub,f=localStorage.getItem("mrpilot_token");try{const v=await fetch("/api/erp/mappings/"+d+"/"+encodeURIComponent(u),{method:"DELETE",headers:{Authorization:"Bearer "+f}});if(!v.ok)throw new Error("http_"+v.status);await e(d,!0),o(),ze(t("erp-map-deleted-toast"),"success")}catch{ze(t("erp-map-delete-fail"),"error")}}async function r(){await n(),await e(oe.sub,!1),a()}function c(u){u!==oe.sub&&(oe.sub=u,oe.addingNew[u]=!1,["clients","accounts","taxes","products"].forEach(function(l){l!==u&&(oe.addingNew[l]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(l){l.classList.toggle("active",l.dataset.erpSubtab===u)}),e(u,!1).then(function(){a()}))}function m(){oe.bound||(oe.bound=!0,document.addEventListener("click",function(u){const l=u.target.closest(".erp-subtab[data-erp-subtab]");if(l){u.preventDefault();const g=l.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(b){b.classList.toggle("active",b.dataset.erpSubtab===g)}),document.querySelectorAll(".erp-subpanel").forEach(function(b){b.classList.toggle("active",b.dataset.erpSubpanel===g)}),g==="mappings"&&setTimeout(r,50);return}const d=u.target.closest(".erp-map-subtab[data-erp-subtab]");if(d){u.preventDefault(),c(d.dataset.erpSubtab);return}if(u.target.closest("#erp-map-add-btn")){if(u.preventDefault(),!qt())return;oe.addingNew[oe.sub]=!0,o();return}const v=u.target.closest('[data-erp-save="new"]');if(v){u.preventDefault();const g=v.closest('[data-erp-row="new"]');g&&s(g);return}const w=u.target.closest("[data-erp-del]");if(w){u.preventDefault(),i(w.dataset.erpDel);return}}))}function p(){const u=document.getElementById("erp-map-pane-wrap");u&&u.children.length>0&&a(),document.querySelectorAll(".erp-map-subtab").forEach(function(l){const d="erp-map-subtab-"+l.dataset.erpSubtab,f=t(d);f&&f!==d&&(l.textContent=f)})}m(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",p)})();(function(){let e=null,n=0,a=!1;function o(x){return typeof escapeHtml=="function"?escapeHtml(x==null?"":String(x)):String(x??"")}function s(x,B){try{typeof showToast=="function"&&showToast(x,B||"info")}catch{}}async function i(x){const B=Date.now();if(e&&B-n<3e4)return e;const L=localStorage.getItem("mrpilot_token");if(!L)return[];try{const I=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+L}});if(!I.ok)return[];const C=await I.json();return e=C&&C.connectors||[],n=B,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function c(x){try{localStorage.setItem("pn_push_default_connector",x||"")}catch{}}function m(x){if(!x||!x.length)return null;const B=r();if(B){const I=x.find(C=>C.id===B);if(I)return I}const L=x.find(I=>I.is_default);return L||x[0]}function p(x){if(!x)return!1;const B=String(x.status||"").toLowerCase();return B==="exception"||B==="exception_pending"||B==="rejected"}function u(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function l(x){const B=x&&(x.type||x.id);return B==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':B==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function d(x,B){if(!x||!B)return!1;const L=document.getElementById("btn-push-default");L&&(L.disabled=!0,L.classList.add("loading"));const I=localStorage.getItem("mrpilot_token");try{let C,S={method:"POST",headers:{Authorization:"Bearer "+I}};x.type==="xero"?C="/api/erp/xero/push/"+encodeURIComponent(B):(C="/api/erp/push",S.headers["Content-Type"]="application/json",S.body=JSON.stringify({history_id:B,endpoint_id:x.endpoint_id||void 0}));const q=await fetch(C,S);let A={};try{A=await q.json()}catch{}if(!q.ok){let V=A&&A.detail||"unknown";typeof V=="object"&&(V=V.code||JSON.stringify(V));let T=String(V||"unknown");if(x.type==="xero"){const F=T.replace(/^xero\./,"").toLowerCase(),O=t("xero-"+F);O&&O!=="xero-"+F&&(T=O)}return s(t("unified-push-fail").replace("{name}",x.name).replace("{err}",T),"error"),!1}if(A&&A.ok===!1){let V=A.error_msg||A.error_code||"unknown";return V=String(V).slice(0,200),s(t("unified-push-fail").replace("{name}",x.name).replace("{err}",V),"error"),!1}return s(t("unified-push-ok").replace("{name}",x.name),"success"),!0}catch(C){return s(t("unified-push-fail").replace("{name}",x.name).replace("{err}",C.message||"network"),"error"),!1}finally{L&&(L.disabled=!1,L.classList.remove("loading"))}}async function f(x,B){for(const L of x)await d(L,B)}function v(x,B){const L=document.createElement("div");L.className="pn-push-dropdown",L.id="pn-push-dropdown";const I=(x||[]).map(S=>{const q=!!(B&&S.id===B.id),A=S.method==="download"?t("unified-push-tag-download"):q?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(S.id)+'"><span class="pn-pd-icon">'+l(S)+'</span><span class="pn-pd-name">'+o(S.name)+"</span>"+(A?'<span class="pn-pd-tag">'+o(A)+"</span>":"")+(q?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),C=x&&x.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",x.length))+"</span></div>":"";return L.innerHTML=I+C,L}function w(){const x=document.getElementById("pn-push-dropdown");x&&x.remove()}async function g(){if(document.getElementById("pn-push-dropdown")){w();return}const x=await i()||[],B=m(x),L=v(x,B),I=document.getElementById("pn-push-wrap");I&&I.appendChild(L)}async function b(){const x=await i()||[],B=m(x);if(!B)return;const L=u(),I=L&&(L._historyId||L.history_id);if(I){if(p(L)){s(t("unified-push-disabled-exc"),"warn");return}await d(B,I)}}async function h(x){w();const B=await i()||[],L=u(),I=L&&(L._historyId||L.history_id);if(!I)return;if(p(L)){s(t("unified-push-disabled-exc"),"warn");return}if(x==="__all__"){await f(B,I);return}const C=B.find(S=>S.id===x);C&&(c(x),await d(C,I),y())}async function E(){const x=document.getElementById("drawer-history-save");if(!x||x.querySelector("#pn-push-wrap"))return;const B=document.createElement("div");B.id="pn-push-wrap",B.className="pn-push-wrap",B.dataset.loading="1",x.insertBefore(B,x.firstChild),["btn-push-erp","btn-xero-push"].forEach(A=>{x.querySelectorAll("#"+A).forEach(V=>{V.style.display="none"})});const L=await i()||[],I=m(L),C=L.length>0;if(!C)B.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const A=L.length>1;B.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+l(I)+"<span>"+o(t("unified-push-to").replace("{name}",I?I.name:""))+"</span></button>"+(A?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete B.dataset.loading;const S=B.querySelector("#btn-push-default");S&&C&&S.addEventListener("click",b);const q=B.querySelector("#btn-push-arrow");q&&q.addEventListener("click",function(A){A.stopPropagation(),g()}),a||(a=!0,document.addEventListener("click",function(A){const V=A.target.closest(".pn-pd-item");if(V){const T=V.getAttribute("data-cid");h(T);return}A.target.closest("#btn-push-arrow")||w()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",y))}function y(){const x=document.getElementById("pn-push-wrap");x&&(x.remove(),e=null,n=0,E())}function _(){const x=document.getElementById("drawer-history-save");if(!x||!x.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(L=>{x.querySelectorAll("#"+L).forEach(I=>{I.style.display!=="none"&&(I.style.display="none")})});const B=x.querySelectorAll("#pn-push-wrap");if(B.length>1)for(let L=1;L<B.length;L++)B[L].remove()}function k(){try{const x=function(){return document.getElementById("drawer-body")},B=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&E(),_()}),L=x();if(L)B.observe(L,{childList:!0,subtree:!0});else{const I=new MutationObserver(function(){const C=x();C&&(B.observe(C,{childList:!0,subtree:!0}),I.disconnect())});I.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&E(),_()},200)}catch{}}k()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",c=t(r);c&&c!==r&&(i.textContent=c)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const m=document.getElementById("erp-onboard-title"),p=document.getElementById("erp-onboard-body"),u=document.getElementById("erp-onboard-ok"),l=document.getElementById("erp-onboard-later");m&&(m.textContent=t("erp-onboard-title")),p&&(p.textContent=t("erp-onboard-body")),u&&(u.textContent=t("erp-onboard-ok")),l&&(l.textContent=t("erp-onboard-later"))}r();function c(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}c();try{const m=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');m&&m.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}c()}),i.addEventListener("click",function(m){m.target===i&&c()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),c=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||c)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,i=s[a]||s.th||s.en,r=n.stage_total,c=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const m={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+m.replace("{d}",c||0).replace("{t}",r)}return i},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,i=o.maxMs||1200*1e3,r=Date.now();let c=0;for(;;){let m=null;try{const p=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{m=await p.json()}catch{m=null}(!p.ok||!m||!m.ok)&&(m=null)}catch{m=null}if(m){if(c=0,o.onProgress)try{o.onProgress(m.progress||{},m)}catch{}if(m.status==="done"||m.status==="failed"||m.status==="needs_review"||m.status==="needs_mapping")return m}else if(++c>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(p=>setTimeout(p,s))}}})();const z={initialized:!1,stmtFiles:[],glFiles:[],currentTask:null,currentFilter:"all",allRows:[],brv2Search:{stmt:"",gl:""},cachedHistoryTasks:[],brv2Page:1},D=e=>document.getElementById(e);function Ae(e){if(e==null)return"—";const n=Number(e);return isNaN(n)?"—":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function $a(e){return e?String(e).slice(0,10).split("-").reverse().join("/"):"—"}function re(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function kl(e,n){n=window._currentLang||n||"th";const a={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},o={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},s=a[e]||o;return s[n]||s.th||s.en}function xl(e){return e?e<1024?e+" B":e<1048576?(e/1024).toFixed(1)+" KB":(e/1048576).toFixed(1)+" MB":""}function Ze(e,n){return window.t&&window.t(e)||n}function Me(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function yn(e){return Number.isFinite(+e)?(+e).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}var Ao="pearnly.brv2.lastAnchorOcr";function _l(e){try{var n=e&&e._anchor_ocr;if(!n||typeof n!="object")return;var a={stmt_opening:Number.isFinite(+n.stmt_opening)?+n.stmt_opening:null,gl_opening:Number.isFinite(+n.gl_opening)?+n.gl_opening:null,gl_closing:Number.isFinite(+n.gl_closing)?+n.gl_closing:null,stmt_closing:Number.isFinite(+n.stmt_closing)?+n.stmt_closing:null,ts:Date.now()};localStorage.setItem(Ao,JSON.stringify(a))}catch{}}function El(){try{var e=localStorage.getItem(Ao);if(!e)return null;var n=JSON.parse(e);return!n||typeof n!="object"?null:n}catch{return null}}function Bl(){var e=El();if(e){var n={"brv2-anchor-stmt-opening":e.stmt_opening,"brv2-anchor-gl-opening":e.gl_opening,"brv2-anchor-gl-closing":e.gl_closing,"brv2-anchor-stmt-closing":e.stmt_closing},a=0;Object.keys(n).forEach(function(c){var m=document.getElementById(c);if(m&&m.value===""){var p=n[c];if(Number.isFinite(p)){m.value=p.toFixed(2);var u=m.closest&&m.closest(".brv2-anchor-cell");u&&u.classList.add("is-prefilled"),a+=1}}});var o=document.getElementById("brv2-anchor-eq"),s=document.getElementById("brv2-anchor-eq-val");if(o&&s&&Number.isFinite(e.stmt_opening)&&Number.isFinite(e.gl_opening)){var i=e.stmt_opening-e.gl_opening;s.textContent=i.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),o.style.display=""}if(a>0){var r=document.getElementById("brv2-anchor-prefill-banner");r&&r.classList.add("show")}}}function Il(){var e=document.getElementById("brv2-anchor-prefill-banner");if(e){var n=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(a){var o=document.getElementById(a);if(o){var s=o.closest&&o.closest(".brv2-anchor-cell");s&&s.classList.contains("is-prefilled")&&(n=!0)}}),e.classList.toggle("show",n)}}var Ll=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function Cl(e){var n=document.getElementById("brv2-summary-collapse");if(!(!n||!n.parentNode)){var a=document.getElementById("brv2-anchor-audit"),o=e&&e._anchor_overrides;if(!o||typeof o!="object"||Object.keys(o).length===0){a&&a.parentNode&&a.parentNode.removeChild(a);return}a||(a=document.createElement("div"),a.id="brv2-anchor-audit",a.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",n.parentNode.insertBefore(a,n.nextSibling));var s=Ll.map(function(i){var r=o[i[0]];if(!r)return"";var c=+r.ocr||0,m=+r.user||0,p=m-c,u=p>0?"+":(p<0,""),l=Math.abs(p)<.005?"#6b7280":p>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+Me(Ze(i[1],i[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+Me(yn(c))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+Me(yn(m))+'</td><td style="padding:6px 10px;color:'+l+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+Me(u+yn(p))+"</td></tr>"}).join("");a.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+Me(Ze("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+Me(Ze("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+Me(Ze("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+Me(Ze("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+Me(Ze("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+s+"</tbody></table>"}}function Qt(e){const n=D("brv2-summary-collapse"),a=D("brv2-detail-collapse"),o=D("brv2-export-btn"),s=D("brv2-new-btn"),i=D("brv2-parse-info-wrap");n&&(n.style.display=e?"":"none"),a&&(a.style.display=e?"":"none"),o&&(o.style.display=e?"":"none"),s&&(s.style.display=e?"":"none"),!e&&i&&(i.style.display="none");const r=D("brv2-warnings");!e&&r&&(r.style.display="none",r.innerHTML="")}function Sl(e){const n=D("brv2-parse-info-wrap"),a=D("brv2-parse-info-body");if(!n||!a)return;const o=e.parse_info;if(!o){n.style.display="none";return}const s=window._currentLang||"zh",i={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},r=d=>(i[d]||{})[s]||(i[d]||{}).zh||d,c=[...(o.stmt_files||[]).map(d=>({...d,_type:"stmt",_extra:d.bank_code||""})),...(o.gl_files||[]).map(d=>({...d,_type:"gl",_extra:(d.accounts||[]).join(", ")}))],m={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},p=d=>{const f=String(d||"");return/Cannot detect bank statement column headers/i.test(f)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(f)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(f)?"stmt_no_rows":/unsupported format/i.test(f)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(f)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(f)?"ocr_failed":null},u=d=>{const f=d.error_code||p(d.error);if(f&&m[f]){const v=window._currentLang||"zh";return m[f][v]||m[f].zh}return String(d.error||"").slice(0,80)},l=d=>!d.ok&&d.error?`<span style="color:#dc2626">${r("fail")} — ${re(u(d))}</span>`:d.rows?`<span style="color:#059669">${r("ok")} (${d.rows})</span>`:`<span style="color:#d97706">${r("warn")}</span>`;a.innerHTML=`
        <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${r("title")}</div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
            <thead>
                <tr style="background:#f3f4f6;font-weight:600">
                    <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${r("type")}</th>
                    <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${r("file")}</th>
                    <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${r("rows")}</th>
                    <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${r("bank")}</th>
                    <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${r("status")}</th>
                </tr>
            </thead>
            <tbody>
                ${c.map(d=>`<tr>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${d._type==="stmt"?r("stmt"):r("gl")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${re(d.file||"")}">${re(d.file||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${d.rows||0}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${re(d._extra||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb">${l(d)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`,n.style.display=""}async function jo(e){const n=localStorage.getItem("mrpilot_token")||"",a=window._currentLang||"zh";try{const o=await fetch("/api/recon/bank-v2/"+e+"/export?lang="+a,{headers:{Authorization:"Bearer "+n}});if(!o.ok){const u=await o.json().catch(()=>({}));window.showToast&&window.showToast(u.detail||"Export failed","error");return}const s=await o.blob(),r=(o.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),c=r?r[1].replace(/['"]/g,""):"reconciliation.xlsx",m=URL.createObjectURL(s),p=document.createElement("a");p.href=m,p.download=c,document.body.appendChild(p),p.click(),document.body.removeChild(p),URL.revokeObjectURL(m)}catch(o){window.showToast&&window.showToast("Export error: "+o.message,"error")}}function Tl(e,n){const a=D("brv2-summary-collapse");let o=D("brv2-warnings");const s=window._currentLang||"zh",i={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[s]||"⏭ ",r=[];if((n||[]).forEach(c=>r.push(i+" "+c)),(e||[]).forEach(c=>r.push(c)),!r.length){o&&(o.style.display="none");return}if(!o)if(o=document.createElement("div"),o.id="brv2-warnings",a&&a.parentNode)a.parentNode.insertBefore(o,a);else return;o.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",o.innerHTML=r.map(c=>"<div>"+re(c)+"</div>").join("")}function sa(e){Sl(e),Tl(e.warnings||[],e.skipped_files||[]),!e.ok&&e.error&&window.showToast&&window.showToast(e.error,"error");const n=e.stats||{},a=e.summary||{},o=n.matched||0,s=(n.gl_debit_only||0)+(n.gl_credit_only||0),i=(n.stmt_withdrawal_only||0)+(n.stmt_deposit_only||0),r=Number(a.formula_diff||0),c=Math.abs(r)<.05;D("brv2-kpi-matched")&&(D("brv2-kpi-matched").textContent=o),D("brv2-kpi-diff")&&(D("brv2-kpi-diff").textContent=Ae(r)),D("brv2-kpi-unmatched")&&(D("brv2-kpi-unmatched").textContent=s+i);const m=D("brv2-kpi-diff-icon");m&&(m.style.background=c?"#d1fae5":"#fee2e2",m.style.color=c?"#065f46":"#b91c1c");const p=D("brv2-formula-sub");if(p){const v=window._currentLang||"zh";p.textContent=c?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[v]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[v]||"差 ")+Ae(r)}const u=D("brv2-detail-sub");if(u){const v=window._currentLang||"zh",w={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[v]||"共 {n} 行";u.textContent=w.replace("{n}",z.allRows.length)}function l(v,w,g){const b=D(v);b&&(b.textContent=(g&&w>0?"(":"")+Ae(g?-w:w)+(g&&w>0?")":""))}l("brf-gl-close",a.gl_closing||0),l("brf-open-diff",a.opening_diff||0),l("brf-gl-debit-only",a.gl_debit_only_amount||0,!0),l("brf-gl-credit-only",a.gl_credit_only_amount||0),l("brf-stmt-wd-only",a.stmt_withdrawal_only_amount||0,!0),l("brf-stmt-dep-only",a.stmt_deposit_only_amount||0),l("brf-calc-close",a.formula_stmt_closing||0),l("brf-stmt-close",a.stmt_closing||0),D("brf-diff")&&(D("brf-diff").textContent=Ae(r));const d=D("brv2-fcell-diff");d&&d.classList.toggle("brv2-fcell-diff-ok",c);const f=D("brv2-export-btn");f&&(f.onclick=()=>{z.currentTask&&jo(z.currentTask.task_id)}),Cl(a),Qt(!0),Po()}function Po(){const e=D("brv2-tbody");if(!e)return;const n=z.allRows.filter(i=>z.currentFilter==="all"?!0:z.currentFilter==="matched"?i.match_status==="matched":z.currentFilter==="gl_only"?i.match_status.startsWith("gl_"):z.currentFilter==="stmt_only"?i.match_status.startsWith("stmt_"):!0);if(n.length===0){const i={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";e.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${i}</td></tr>`;return}const a=window._currentLang||"zh",o={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[a],s={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[a];e.innerHTML=n.map(i=>{const r=i.match_status,c=i.match_layer;let m="",p="";r==="matched"?(c===1&&(m="matched",p='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),c===2&&(m="matched-l2",p='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),c===3&&(m="matched-l3",p='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):r==="gl_debit_only"||r==="gl_credit_only"?(m="gl-only",p='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(m="stmt-only",p=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[a]||"账单"}</span>`);let u="";return i.stmt_balance_ok===!1&&(u+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${re(o)}">⚠</span>`,m+=" brv2-row-warn"),i.stmt_confidence==="low"&&(u+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${re(s)}">◌</span>`,m.includes("brv2-row-warn")||(m+=" brv2-row-warn-soft")),`<tr class="${m.trim()}">
          <td>${p}${u}</td>
          <td>${re($a(i.stmt_date))}</td>
          <td title="${re(i.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${re(i.stmt_desc)}</td>
          <td class="num">${i.stmt_withdrawal?Ae(i.stmt_withdrawal):""}</td>
          <td class="num">${i.stmt_deposit?Ae(i.stmt_deposit):""}</td>
          <td>${re($a(i.gl_date))}</td>
          <td title="${re(i.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${re(i.gl_doc_no)}</td>
          <td class="num">${i.gl_debit?Ae(i.gl_debit):""}</td>
          <td class="num">${i.gl_credit?Ae(i.gl_credit):""}</td>
          <td>${c?"L"+c:"—"}</td>
        </tr>`}).join("")}async function Ct(){const e=localStorage.getItem("mrpilot_token")||"";try{const a=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+e}})).json();en(a.tasks||[])}catch{const a=D("brv2-history-empty"),o=window._currentLang||"zh",s={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[o]||"加载失败";a&&(a.textContent=s,a.style.display="");const i=D("brv2-history-table-wrap");i&&(i.style.display="none")}}const it=10;function Ha(){const e=D("brv2-history-pager"),n=D("brv2-history-pager-info"),a=D("brv2-history-prev"),o=D("brv2-history-next");if(!e)return;if(z.cachedHistoryTasks.length<=it){e.style.display="none";return}e.style.display="";const s=Math.ceil(z.cachedHistoryTasks.length/it);n&&(n.textContent=z.brv2Page+" / "+s),a&&(a.disabled=z.brv2Page<=1),o&&(o.disabled=z.brv2Page>=s)}function Ml(){const e=D("brv2-history-prev"),n=D("brv2-history-next");e&&!e._brv2Bound&&(e._brv2Bound=!0,e.addEventListener("click",()=>{z.brv2Page>1&&(z.brv2Page--,en(z.cachedHistoryTasks))})),n&&!n._brv2Bound&&(n._brv2Bound=!0,n.addEventListener("click",()=>{const a=Math.ceil(z.cachedHistoryTasks.length/it);z.brv2Page<a&&(z.brv2Page++,en(z.cachedHistoryTasks))}))}function en(e){e!==void 0&&(z.cachedHistoryTasks=e||[],z.brv2Page=1);const n=z.cachedHistoryTasks,a=D("brv2-history-empty"),o=D("brv2-history-table-wrap"),s=D("brv2-history-tbody");if(!s)return;const i=window._currentLang||"zh";if(!n.length){const f={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[i]||"暂无对账记录";a&&(a.textContent=f,a.style.display=""),o&&(o.style.display="none"),Ha();return}a&&(a.style.display="none"),o&&(o.style.display="");const r=Math.ceil(n.length/it);z.brv2Page>r&&(z.brv2Page=r);const c=(z.brv2Page-1)*it,m=n.slice(c,c+it),p=localStorage.getItem("mrpilot_token")||"",u='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',l='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',d='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';s.innerHTML="",m.forEach(f=>{const v=Number(f.formula_diff||0),w=Math.abs(v)<.05,g=(f.stmt_files||"").split(";").map(F=>F.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),b=(f.gl_files||"").split(";").map(F=>F.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),h=f.created_at?String(f.created_at).slice(0,16).replace("T"," "):"",E=document.createElement("tr");E.dataset.taskId=f.id;const y=document.createElement("td");y.textContent=h;const _=document.createElement("td");_.className="glv-history-file",_.title=g+" + "+b,_.textContent=g+" + "+b;const k=document.createElement("td");k.className="glv-num",k.textContent=(f.stmt_row_count||0)+" / "+(f.gl_row_count||0);const x=document.createElement("td");x.className="glv-num",x.textContent=f.matched_count||0;const B=document.createElement("td");B.className="glv-num",B.textContent=f.unmatched_gl||0;const L=document.createElement("td");L.className="glv-num",L.textContent=f.unmatched_stmt||0;const I=document.createElement("td");I.className="glv-num",I.style.color=w?"#059669":"#dc2626",I.textContent=w?"✓":Ae(v);const C=document.createElement("td");C.className="glv-history-actions";const S=(F,O,G,$)=>{const H=document.createElement("button");return H.type="button",H.title=O,H.setAttribute("aria-label",O),G&&(H.className=G),H.innerHTML=F,H.onclick=K=>{K.stopPropagation(),$()},H},q={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[i]||"删除?",A={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[i]||"加载",V={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[i]||"导出",T={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[i]||"删除";C.appendChild(S(u,A,"",()=>Aa(f.id,p))),C.appendChild(S(l,V,"",()=>jo(f.id))),C.appendChild(S(d,T,"glv-del",async()=>{await showConfirm(q,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+f.id,{method:"DELETE",headers:{Authorization:"Bearer "+p}}),Ct())})),[y,_,k,x,B,L,I,C].forEach(F=>E.appendChild(F)),E.style.cursor="pointer",E.addEventListener("click",async F=>{F.target.closest(".glv-del")||F.target.closest("button")||await Aa(f.id,p)}),s.appendChild(E)}),Ha(),Do()}function Do(){const e=((D("brv2-hist-search")||{}).value||"").trim().toLowerCase(),n=D("brv2-history-tbody");n&&n.querySelectorAll("tr").forEach(a=>{a.dataset.taskId&&(a.style.display=!e||a.textContent.toLowerCase().includes(e)?"":"none")})}async function Aa(e,n){try{const o=await(await fetch("/api/recon/bank-v2/"+e,{headers:{Authorization:"Bearer "+n}})).json();if(!o.ok)return;z.currentTask={task_id:o.task_id,...o},z.allRows=o.detail||[],z.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(s=>s.classList.toggle("active",s.dataset.filter==="all")),sa(z.currentTask)}catch{}}function Ie(e){const n=e==="stmt"?z.stmtFiles:z.glFiles,a=D(`brv2-${e}-name`);if(a)if(n.length===0)a.textContent="";else{const s=window._currentLang||"zh",i={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};a.textContent=n.length+(i[s]||" 个文件")}const o=D("brv2-preview-panel");o&&o.style.display!=="none"&&Sn(e),$l()}function $l(){const e=D("brv2-toggle-preview"),n=D("brv2-preview-panel"),a=z.stmtFiles.length+z.glFiles.length>0;e&&(e.style.display=a?"":"none"),!a&&n&&(n.style.display="none",e&&e.classList.remove("open"))}function Hl(){Sn("stmt"),Sn("gl")}function Sn(e){const n=D(e==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!n)return;const a=e==="stmt"?z.stmtFiles:z.glFiles,o=window._currentLang||"zh",s={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},i=(s[e]||{})[o]||s[e].zh,r=re(window.t&&window.t("vex-preview-search")||"搜索文件名..."),c=re(window.t&&window.t("vex-preview-clear-all")||"全清"),m=z.brv2Search[e]||"";n.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+re(i)+' <span class="vex-pp-col-count">'+a.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+e+'" type="text" placeholder="'+r+'" value="'+re(m)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+e+'" type="button">'+c+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+e+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+e+'-pg"></div>';const p=D("brv2-pp-search-"+e);p&&p.addEventListener("input",function(l){z.brv2Search[e]=l.target.value,ja(e)});const u=D("brv2-pp-clearall-"+e);u&&u.addEventListener("click",function(){e==="stmt"?z.stmtFiles.length=0:z.glFiles.length=0,Ie(e),je()}),ja(e)}function ja(e){const n=D("brv2-pp-"+e+"-list"),a=D("brv2-pp-"+e+"-pg");if(!n)return;const o=e==="stmt"?z.stmtFiles:z.glFiles,s=(z.brv2Search[e]||"").toLowerCase(),i=s?o.filter(m=>m.name.toLowerCase().includes(s)):o.slice(),r='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',c='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(n.innerHTML=i.map((m,p)=>'<div class="vex-pp-file-row">'+r+'<span class="vex-pp-fi-name" title="'+re(m.name)+'">'+re(m.name)+'</span><span class="vex-pp-fi-size">'+xl(m.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+e+'" data-idx="'+o.indexOf(m)+'" aria-label="remove">'+c+"</button></div>").join(""),n.querySelectorAll(".vex-pp-fi-del").forEach(function(m){m.addEventListener("click",function(){const p=parseInt(m.dataset.idx,10);m.dataset.zone==="stmt"?z.stmtFiles.splice(p,1):z.glFiles.splice(p,1),Ie(m.dataset.zone),je()})}),a){const m=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";a.textContent=m.replace("{n}",i.length).replace("{m}",o.length)}}function Al(){const e=D("brv2-toggle-preview");e&&!e._reconBound&&(e._reconBound=!0,e.addEventListener("click",function(){const n=D("brv2-preview-panel"),a=D("brv2-toggle-preview-label"),o=n&&n.style.display!=="none";n&&(n.style.display=o?"none":""),e.classList.toggle("open",!o),a&&(a.textContent=o?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),o||Hl()}))}function je(){const e=D("brv2-run-btn"),n=D("brv2-status"),a=z.stmtFiles.length>0,o=z.glFiles.length>0;if(e&&(e.disabled=!(a&&o)),n){const s=window._currentLang||"zh";if(!a&&!o){const i={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};n.textContent=i[s]||i.zh}else if(a)if(o){const i={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};n.textContent=i[s]||i.zh}}}function Pa(e,n,a){const o=D(e),s=D(n);!o||!s||(o.addEventListener("click",()=>s.click()),o.addEventListener("keydown",i=>{(i.key==="Enter"||i.key===" ")&&(i.preventDefault(),s.click())}),o.addEventListener("dragover",i=>{i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",()=>o.classList.remove("drag-over")),o.addEventListener("drop",i=>{i.preventDefault(),o.classList.remove("drag-over");const r=Array.from(i.dataTransfer.files||[]);a==="stmt"?z.stmtFiles.push(...r):z.glFiles.push(...r),Ie(a),je()}),s.addEventListener("change",()=>{const i=Array.from(s.files||[]);a==="stmt"?z.stmtFiles.push(...i):z.glFiles.push(...i),s.value="",Ie(a),je()}))}function ye(e){const n=D("brv2-progress"),a=D("brv2-run-btn"),o=D("brv2-error");n&&(n.style.display=e?"":"none"),a&&(a.disabled=e),o&&(o.style.display="none")}function Be(e){const n=D("brv2-error");n&&(n.textContent=e,n.style.display="",n.scrollIntoView({behavior:"smooth",block:"nearest"})),ye(!1),je(),window.showToast&&window.showToast(e,"error")}async function Tn(){if(z.stmtFiles.length===0||z.glFiles.length===0)return;const e=localStorage.getItem("mrpilot_token")||"",n=window._currentLang||"zh",a=(D("brv2-acct-select")||{}).value||"";Qt(!1),ye(!0);try{const o=new FormData;z.stmtFiles.forEach(f=>o.append("stmt_files",f)),z.glFiles.forEach(f=>o.append("gl_files",f)),o.append("gl_account",a),o.append("lang",n);const s=parseFloat((D("brv2-anchor-gl-closing")||{}).value),i=parseFloat((D("brv2-anchor-stmt-closing")||{}).value),r=parseFloat((D("brv2-anchor-stmt-opening")||{}).value),c=parseFloat((D("brv2-anchor-gl-opening")||{}).value);Number.isFinite(s)&&o.append("gl_closing_override",s),Number.isFinite(i)&&o.append("stmt_closing_override",i),Number.isFinite(r)&&o.append("stmt_opening_override",r),Number.isFinite(c)&&o.append("gl_opening_override",c);const m=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+e},body:o});let p=null;try{p=await m.json()}catch{p=null}if(p&&p.needs_mapping){ye(!1),window.ReconMapping?window.ReconMapping.show(p,{token:e,lang:n,onConfirmed:function(){Tn()}}):Be(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!m.ok||!p||!p.ok||!p.job_id){ye(!1),p&&(p.detail||p.error)?Be(_humanizeBackendError(p.detail||p.error,"Error "+m.status)):Be(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const u=D("brv2-progress-sub"),l=await window._reconPollJob(p.job_id,e,{onProgress:f=>{u&&(u.textContent=window._reconProgressText(f,n))}});if(l&&l.status==="needs_mapping"&&l.mapping){ye(!1),window.ReconMapping?window.ReconMapping.show(l.mapping,{token:e,lang:n,onConfirmed:function(){Tn()}}):Be(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(l&&l.status==="needs_review"&&l.review){ye(!1),window.ReconReview?window.ReconReview.show(l.review,{token:e,lang:n,jobId:p.job_id,onConfirmed:async function(f){ye(!0);const v=await window._reconPollJob(f,e,{onProgress:w=>{u&&(u.textContent=window._reconProgressText(w,n))}});await d(v)}}):Be(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(l&&l.status==="failed"){ye(!1),Be(kl(l.error_code,n));return}await d(l);async function d(f){try{if(!f||f.status!=="done"||!f.result_id){ye(!1),Be(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const v=await fetch("/api/recon/bank-v2/"+encodeURIComponent(f.result_id),{headers:{Authorization:"Bearer "+e}});let w=null;try{w=await v.json()}catch{w=null}if(!v.ok||w===null||!w.ok){ye(!1),Be(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(w.gl_accounts||[]).length>1&&jl(w.gl_accounts),z.currentTask=w,z.allRows=w.detail||[],z.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(b=>b.classList.toggle("active",b.dataset.filter==="all")),_l(w&&w.summary),ye(!1),sa(w),Ct();const g=D("brv2-summary-collapse");g&&g.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(v){ye(!1),Be(v.message||"Network error")}}}catch(o){Be(o.message||"Network error")}}function jl(e){const n=D("brv2-acct-select");if(!n)return;const a=window._currentLang||"zh",o={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[a]||"全部账户";n.innerHTML=`<option value="">${o}</option>`+e.map(s=>`<option value="${re(s)}">${re(s)}</option>`).join(""),n.style.display=""}function ia(){if(z.initialized){Ct();return}z.initialized=!0,Pa("brv2-stmt-zone","brv2-stmt-input","stmt"),Pa("brv2-gl-zone","brv2-gl-input","gl");const e=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function n(){const c=parseFloat((D("brv2-anchor-stmt-opening")||{}).value),m=parseFloat((D("brv2-anchor-gl-opening")||{}).value),p=D("brv2-anchor-eq"),u=D("brv2-anchor-eq-val");if(!(!p||!u))if(Number.isFinite(c)&&Number.isFinite(m)){const l=c-m;u.textContent=l.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),p.style.display=""}else p.style.display="none"}e.forEach(c=>{const m=D(c);m&&(m.addEventListener("input",n),m.addEventListener("input",()=>{const p=m.closest(".brv2-anchor-cell");p&&p.classList.remove("is-prefilled"),Il()}))}),Bl();const a=D("brv2-run-btn");a&&a.addEventListener("click",Tn);const o=D("brv2-reset-btn");o&&o.addEventListener("click",()=>{z.currentTask=null,z.allRows=[],z.stmtFiles=[],z.glFiles=[],Ie("stmt"),Ie("gl"),je(),Qt(!1);const c=D("brv2-acct-select");c&&(c.style.display="none"),e.forEach(u=>{const l=D(u);if(l){l.value="";const d=l.closest&&l.closest(".brv2-anchor-cell");d&&d.classList.remove("is-prefilled")}});const m=D("brv2-anchor-eq");m&&(m.style.display="none");const p=D("brv2-anchor-prefill-banner");p&&p.classList.remove("show")});const s=D("brv2-new-btn");s&&s.addEventListener("click",()=>{z.currentTask=null,z.allRows=[],z.stmtFiles=[],z.glFiles=[],Ie("stmt"),Ie("gl"),je(),Qt(!1)});const i=D("brv2-filter-tabs");i&&i.addEventListener("click",c=>{c.stopPropagation();const m=c.target.closest(".brv2-filter-btn");m&&(z.currentFilter=m.dataset.filter,i.querySelectorAll(".brv2-filter-btn").forEach(p=>p.classList.toggle("active",p===m)),Po())}),Al(),Ml();const r=D("brv2-hist-search");r&&r.addEventListener("input",Do),Ct(),je(),window._brv2LoadHistory=Ct,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(c=>c.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){je(),Ie("stmt"),Ie("gl"),z.currentTask&&sa(z.currentTask),en()}})}window._loadBankReconV2Panel=function(e){const n=e?document.getElementById(e):null;n&&n.id!=="recon-pane-bank"&&(n.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
            银行对账 v2 · 请前往对账中心使用</div>`),ia()};document.addEventListener("DOMContentLoaded",()=>{D("brv2-run-btn")&&ia()});window._bankReconV2Init=ia;(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const p=document.getElementById("general-tz"),u=document.getElementById("general-date"),l=document.getElementById("general-number");if(!(!p||!u||!l))try{p.value=localStorage.getItem(n)||s.tz,u.value=localStorage.getItem(a)||s.date,l.value=localStorage.getItem(o)||s.number}catch{p.value=s.tz,u.value=s.date,l.value=s.number}}async function r(){const p=document.getElementById("btn-save-general"),u=document.getElementById("general-save-msg");if(!p)return;const l=p.innerHTML;p.disabled=!0,p.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",u&&(u.textContent="",u.classList.remove("error"));try{const d=(document.getElementById("general-tz")||{}).value||s.tz,f=(document.getElementById("general-date")||{}).value||s.date,v=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,d),localStorage.setItem(a,f),localStorage.setItem(o,v)}catch{}window._pearnlyGeneral={tz:d,date_format:f,number_format:v},u&&(u.textContent=t("msg-saved")||"已保存")}catch{u&&(u.textContent=t("msg-save-failed")||"保存失败",u.classList.add("error"))}finally{p.disabled=!1,p.innerHTML=l,setTimeout(function(){u&&(u.textContent="")},3e3)}}function c(){const p=document.getElementById("btn-save-general");if(!p){setTimeout(c,200);return}p._pearnlyGenBound||(p._pearnlyGenBound=!0,p.addEventListener("click",r),i())}function m(){i();const p=document.getElementById("general-lang");if(p){const u=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";p.value=u}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",m)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(c){const m=c.dataset.collapsible;r[m]?c.classList.add("collapsed"):c.classList.remove("collapsed")})}function i(r){const c=a();c[r]=!c[r],o(c),s()}(function(){const c=a();let m=!1;c.sales===void 0&&(c.sales=!1,m=!0),c.expense===void 0&&(c.expense=!0,m=!0),m&&o(c)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const c=n[r];if(!c)return;const m=a();m[c]&&(m[c]=!1,o(m),s())}})();const Pl=`
    <div class="modal" style="max-width:440px">
        <div class="modal-head">
            <div class="modal-title" data-i18n="help-modal-title">帮助反馈</div>
            <button type="button" class="modal-close" id="help-modal-close" aria-label="Close">
                <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6l8 8M14 6l-8 8" stroke-linecap="round"/></svg>
            </button>
        </div>
        <div class="modal-body">
            <p class="help-modal-tip" data-i18n="help-modal-tip">遇到问题或有产品建议?以下方式联系我们 · 通常 24 小时内回复</p>
            <div class="help-contact-list">
                <a class="help-contact-card" href="mailto:hello@pearnly.com">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="5" width="18" height="14" rx="2"/>
                        <path d="M3 7l9 6 9-6"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-email-label">邮箱</div>
                        <div class="help-contact-value">hello@pearnly.com</div>
                    </div>
                </a>
                <a class="help-contact-card" href="tel:+66868892228">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-phone-label">电话</div>
                        <div class="help-contact-value">+66 86-889-2228</div>
                    </div>
                </a>
                <a class="help-contact-card" href="https://line.me/R/ti/p/@059oupmg" target="_blank" rel="noopener">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-line-label">LINE 客服</div>
                        <div class="help-contact-value">@059oupmg</div>
                    </div>
                </a>
            </div>
        </div>
    </div>`;function Da(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=Pl;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,Da();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const i=o.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let xe=[];window._erpEndpoints=xe;let Ht=null;async function dn(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}xe=(await e.json()).items||[],window._erpEndpoints=xe,qo()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return dn()};async function Fo(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const c=[];c.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&c.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&c.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&c.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=c.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function qo(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&xe.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(xe.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=xe.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:xe.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),Fo(),e.innerHTML=xe.map(s=>{const i=s.config||{},r=escapeHtml(i.url||"");i._token_set;const c=s.enabled!==!1,m=[];s.is_default&&m.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&m.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),c||m.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const p=[];return s.success_count>0&&p.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&p.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(s.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(s.name)}</div>
                        <div class="ep-badges">${m.join("")}</div>
                    </div>
                    <div class="ep-url">${r||"-"}</div>
                    <div class="ep-stats">${p.join(" · ")}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(s.id)}">
                        <span>${escapeHtml(t("ep-edit"))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(s.id)}">
                        <span>${escapeHtml(t("ep-delete"))}</span>
                    </button>
                </div>
            </div>
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=xe.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,c=document.createElement("div");c.className="erp-limit-hint",r==="free"?c.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:c.textContent=t("ep-plus-limit-hint",{used:s,limit:i}),e.appendChild(c)}}function Dl(e){Ht=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),c=document.getElementById("ep-auto-push"),m=document.getElementById("ep-test-result");m.style.display="none",m.textContent="";const p=document.getElementById("ep-save-error");if(p&&p.remove(),e){const l=xe.find(d=>d.id===e);if(!l)return;o.value=l.name||"",s.value=(l.config||{}).url||"",i.value=(l.config||{})._token_set&&l.config.token||"",i.placeholder=(l.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!l.is_default,c.checked=!!l.auto_push}else o.value="",s.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=xe.length===0,c.checked=!0;const u=c.closest(".form-switch-row");if(c.disabled=!1,u){u.classList.remove("disabled-plus"),u.title="",u.style.cursor="",u.onclick=null;const l=u.querySelector(".plus-badge");l&&l.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function Ro(){document.getElementById("endpoint-modal").style.display="none",Ht=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function zo(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function No(){const e=document.getElementById("ep-name").value.trim(),n=zo(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:i}}async function Fl(){const{url:e,config:n}=No(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function ql(){const e=No(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){Fa(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let i;if(Ht?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(Ht)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const c=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof c=="string"?c:JSON.stringify(c))}Ro(),showToast(t("ep-save-ok")),dn()}catch(i){Fa(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function Fa(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function Rl(e){const n=xe.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),dn()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=dn;window.loadErpTodayStats=Fo;window.renderErpEndpointsList=qo;window.openEndpointModal=Dl;window.closeEndpointModal=Ro;window.saveEndpoint=ql;window.deleteEndpoint=Rl;window.testEndpointConnection=Fl;window._sanitizeUrl=zo;async function Oo(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function zl(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){Oo(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const i=s.dataset.receiptAction;i==="retry"?window.retryPushLog(s.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(S=>S.id===o.endpoint_id),i=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),c=new Date(o.created_at).toLocaleString(),m=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),p=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),u=o.response_body||t("erp-receipt-no-tech"),l=o.status==="success";let d=typeof u=="string"?u:JSON.stringify(u,null,2);if(l)try{const S=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},q=S.row_count||(Array.isArray(S.imported_rows)?S.imported_rows.length:0);q>0&&(d=t("log-push-rows").replace("{n}",String(q)))}catch{}const f=(o.external_doc_no||"").trim(),v=(o.external_url||"").trim(),w=(o.external_doc_hint||"").trim(),g=(o.ocr_buyer_name||"").trim()||o.client_name||"-",b=o.seller_name||"-",h=o.push_type==="id_card";let E="-";const y=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(y)&&(E=y.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const _=l?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),k=l?"✓":"✗",x=[],B=(S,q)=>{x.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(S)}</span>
                    <span class="erp-receipt-val">${q}</span>
                </div>`)};if(B(h?t("erp-log-col-booking"):t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),B(t("erp-receipt-erp-name"),escapeHtml(i)),l){let S;f?S=`<strong class="erp-receipt-docno">${escapeHtml(f)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(f)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:S=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,B(t("erp-receipt-doc-no"),S)}h||B(t("erp-receipt-client"),escapeHtml(g)),B(h?t("erp-log-col-customer"):t("erp-receipt-seller"),escapeHtml(b)),l&&B(t("erp-receipt-amount"),escapeHtml(E)),B(t("erp-receipt-time"),escapeHtml(c)),B(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let L="";l&&v?L=`<a class="erp-receipt-primary-btn" href="${escapeHtml(v)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:l&&f&&(L=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(f)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let I="";if(l&&f&&w){const S="erp-receipt-hint-"+w,q=t(S);q&&q!==S&&(I=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(q)}</span></div>`)}let C="";if(!l){const S=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),q=S?S[0]:"",A=typeof currentLang=="string"&&currentLang||window._currentLang||"th",T=o.error_friendly&&o.error_friendly[A]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),F=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),O=!!(o.history_id&&o.endpoint_id),G=[];G.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),F&&G.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),O&&G.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),C=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${q?`<div class="erp-receipt-errcode">${escapeHtml(q)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(T)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${G.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${l?"ok":"fail"}">${k}</span>
                    ${escapeHtml(_)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(m)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${x.join("")}
            </div>

            ${I}
            ${L?`<div class="erp-receipt-primary-wrap">${L}</div>`:""}
            ${C}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t("erp-receipt-tech-toggle"))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${o.http_status||"-"}</span>
                    <span>${o.elapsed_ms}ms</span>
                    <span>${escapeHtml(t("log-detail-attempt",{n:o.attempt||1}))}</span>
                </div>
                <div class="log-detail-section" style="margin-top:12px;">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-request-human"))}</div>
                    <pre>${escapeHtml(p)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(d)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=Oo;window.showLogDetail=zl;const Nl=`
        <div class="modal">
            <div class="modal-head">
                <div class="modal-title" id="endpoint-modal-title" data-i18n="ep-modal-title-new">新增 ERP 端点</div>
                <button class="modal-close" id="endpoint-modal-close" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="modal-body">
                <!-- 适配器选择 -->
                <div class="form-group">
                    <label class="form-label" data-i18n="ep-adapter">适配器类型</label>
                    <div class="adapter-picker" id="ep-adapter-picker">
                        <label class="adapter-card" data-adapter="webhook">
                            <input type="radio" name="ep-adapter" value="webhook" checked>
                            <div class="adapter-card-body">
                                <div class="adapter-name" data-i18n="ep-adapter-webhook">自定义 Webhook</div>
                                <div class="adapter-desc" data-i18n="ep-adapter-webhook-desc">HTTP POST 到任意 URL · 最通用</div>
                            </div>
                        </label>
                        <label class="adapter-card disabled" data-adapter="flowaccount" title="即将上线">
                            <input type="radio" name="ep-adapter" value="flowaccount" disabled>
                            <div class="adapter-card-body">
                                <div class="adapter-name">FlowAccount <span class="tag-soon" data-i18n="tag-soon">即将上线</span></div>
                                <div class="adapter-desc" data-i18n="ep-adapter-flow-desc">泰国本地会计 SaaS</div>
                            </div>
                        </label>
                    </div>
                </div>

                <!-- 通用字段 -->
                <div class="form-group">
                    <label class="form-label" for="ep-name" data-i18n="ep-name">端点名称</label>
                    <input type="text" id="ep-name" class="form-input" data-i18n-placeholder="ep-name-ph">
                </div>

                <!-- Webhook 字段 -->
                <div id="ep-fields-webhook">
                    <div class="form-group">
                        <label class="form-label" for="ep-url" data-i18n="ep-url">Webhook URL</label>
                        <input type="text" id="ep-url" class="form-input" placeholder="https://your-erp.com/api/invoice/import">
                        <div class="form-hint" data-i18n="ep-url-hint">识别完成后 Pearnly 会 POST 一个 JSON 到这个地址</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="ep-token" data-i18n="ep-token">Secret Token(选填)</label>
                        <input type="password" id="ep-token" class="form-input" data-i18n-placeholder="ep-token-ph">
                        <div class="form-hint" data-i18n="ep-token-hint">会以 X-Mrpilot-Token 请求头发送 · 让接收端验证来源</div>
                    </div>
                </div>

                <!-- 开关 -->
                <div class="form-group">
                    <label class="form-switch-row">
                        <input type="checkbox" id="ep-is-default">
                        <span class="form-switch-label" data-i18n="ep-is-default">设为默认端点</span>
                    </label>
                    <label class="form-switch-row">
                        <input type="checkbox" id="ep-auto-push">
                        <span class="form-switch-label" data-i18n="ep-auto-push">识别成功后自动推送</span>
                    </label>
                </div>

                <!-- 测试连接结果 -->
                <div class="form-test-result" id="ep-test-result" style="display:none;"></div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="btn-ep-test">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 8l3 3 7-7"/>
                    </svg>
                    <span data-i18n="ep-test-btn">测试连接</span>
                </button>
                <div style="flex:1"></div>
                <button class="btn btn-ghost" id="btn-ep-cancel" data-i18n="btn-cancel">取消</button>
                <button class="btn btn-primary" id="btn-ep-save" data-i18n="btn-save">保存</button>
            </div>
        </div>
    `;ve("endpoint-modal",Nl);let kt={key:"all",val:""},St="",wn=!1,$e=new Set;window._erpSelected=$e;async function Ol(){const e=document.getElementById("erp-logs-erp-select");if(!(!e||wn)){wn=!0;try{let n=window._erpEndpoints;if(!Array.isArray(n)||n.length===0){const s=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(s.ok){const i=await s.json();n=i&&(i.items||i)||[]}}Array.isArray(n)||(n=[]);const a=new Set,o=[];n.forEach(s=>{const i=(s&&s.adapter||"").toLowerCase();!i||a.has(i)||(a.add(i),o.push({val:i,label:s&&s.name||i}))}),e.innerHTML=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`+o.map(s=>`<option value="${escapeHtml(s.val)}"${s.val===St?" selected":""}>${escapeHtml(s.label)}</option>`).join("")}catch{wn=!1}}}async function rt(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats(),Ol();try{const a=new URLSearchParams({limit:"30"});kt.key==="status"&&a.set("status",kt.val),kt.key==="trigger"&&a.set("trigger",kt.val),St&&a.set("adapter",St);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(f){return f.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){rt(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const r=i.filter(function(f){var v=f.status==="failed"&&f.next_retry_at&&new Date(f.next_retry_at).getTime()>Date.now()-6e4;return!v}).map(function(f){return f.id}),c=St==="mrerp_dms",m=c?t("erp-log-col-booking"):t("erp-log-col-invoice"),p=c?t("erp-log-col-customer"):t("erp-log-col-seller"),u=c?t("erp-log-col-idcard"):t("erp-log-col-client"),l='<div class="erp-log-row erp-log-row-header" data-log-header>'+(r.length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(m)}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(u)}</span><span class="log-seller">${escapeHtml(p)}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=l+i.map(f=>{const v=new Date(f.created_at),w=`${String(v.getMonth()+1).padStart(2,"0")}-${String(v.getDate()).padStart(2,"0")} ${String(v.getHours()).padStart(2,"0")}:${String(v.getMinutes()).padStart(2,"0")}`,g=f.status==="failed"&&f.next_retry_at&&new Date(f.next_retry_at).getTime()>Date.now()-6e4;let b,h,E;f.status==="pending"?(b="retrying",h="⟳",E=t("erp-status-pending")):f.status==="success"?(b="ok",h="✓",E=t("erp-status-success")):f.status==="skipped_dup"?(b="skipped",h="⏭",E=t("erp-status-skipped")):g?(b="retrying",h="↻",E=t("erp-status-retrying")):(b="fail",h="✗",E=t("erp-status-failed"));let y;f.trigger==="auto"?y=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:f.trigger==="retry"?y=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:y=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;const _=f.push_type==="id_card",k=_?`<span class="log-tag log-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span>`:"",x=f.error_friendly&&(f.error_friendly[currentLang]||f.error_friendly.en)||"";let B="";const L=f.retry_count||0,I=f.max_retries||3;if(g){const K=new Date(f.next_retry_at).getTime()-Date.now(),ae=Math.max(0,Math.round(K/6e4)),ne=ae<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:ae});B=`${t("erp-retry-attempt",{n:L,max:I})} · ${ne}`}else f.status==="failed"&&L>=I&&!f.next_retry_at&&(B=t("erp-retry-exhausted",{n:L}));const C=f.status==="failed"&&!g?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(f.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",S=!g,q=$e.has(f.id)?"checked":"",A=S?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(f.id)}" ${q}>`:'<span class="erp-log-cb-spacer"></span>',V=(f.ocr_buyer_name||"").trim()||(f.client_name||"").trim(),T=_?`<span class="log-client" title="${escapeHtml(t("erp-log-col-idcard"))}">${f.id_card_tail?"••••"+escapeHtml(f.id_card_tail):"—"}</span>`:V?`<span class="log-client" title="${escapeHtml(V)}">${escapeHtml(V.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,F=_?'<span class="log-workspace log-workspace-unresolved">—</span>':f.workspace_name?`<span class="log-workspace">${escapeHtml((f.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,O=f.endpoint_name?`<span class="log-erp">${escapeHtml((f.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,G=(f.external_doc_no||"").trim(),$=(f.external_url||"").trim();let H;return $?H=`<span class="log-doc"><a href="${escapeHtml($)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(G||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:G?H=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(G)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(G.substring(0,18))}</span>`:f.status==="success"?H=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:H='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${b}" data-log-detail="${escapeHtml(f.id)}">
                    ${A}
                    <span class="log-time">${w}</span>
                    <span class="log-status" title="${escapeHtml(E+(B?" · "+B:"")+(x?" · "+x:""))}">${h}</span>
                    ${y}${k}
                    <span class="log-invoice"${_?` title="${escapeHtml(t("erp-log-col-booking"))}"`:""}>${escapeHtml(f.invoice_no||"-")}</span>
                    ${F}
                    ${T}
                    <span class="log-seller"${_?` title="${escapeHtml(t("erp-log-col-customer"))}"`:""}>${escapeHtml((f.seller_name||"").substring(0,20))}</span>
                    ${O}
                    ${H}
                    <span class="log-http">HTTP ${f.http_status||"-"}</span>
                    <span class="log-elapsed">${f.elapsed_ms}ms</span>
                    <span class="log-actions">${C}</span>
                </div>
            `}).join("");const d=new Set(i.map(f=>f.id));for(const f of Array.from($e))d.has(f)||$e.delete(f);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function Vo(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),rt(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),Vo(s.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const u=i.dataset.logCb;i.checked?$e.add(u):$e.delete(u),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const u=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(d){d.checked=u;const f=d.dataset.logCb;u?$e.add(f):$e.delete(f)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),$e.clear(),document.querySelectorAll(".erp-log-cb").forEach(u=>{u.checked=!1}),window._refreshErpBatchBar();return}const c=n.target.closest("[data-log-detail]");if(c){if(n.target.closest("[data-log-cb]"))return;const u=n.target.closest("[data-copy-doc]");if(u){n.stopPropagation(),window.copyErpDocNo(u.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(c.dataset.logDetail);return}const m=n.target.closest(".chip-filter");if(m){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(u=>u.classList.remove("active")),m.classList.add("active"),kt={key:m.dataset.filterKey,val:m.dataset.filterVal},rt();return}if(n.target.closest("#btn-refresh-logs")){const u=n.target.closest("#btn-refresh-logs");u.classList.add("spinning"),setTimeout(()=>u.classList.remove("spinning"),600),rt();return}const p=n.target.closest(".auto-nav-item");if(p&&p.dataset.autoTab){switchAutomationTab(p.dataset.autoTab);return}}),document.addEventListener("change",n=>{n.target&&n.target.id==="erp-logs-erp-select"&&(St=n.target.value||"",rt())})})();window.loadErpLogs=rt;window.retryPushLog=Vo;function Uo(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function Go(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),i=o.failed&&o.failed>0?"warn":"success";showToast(s,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function Ko(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),Go()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),Ko()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),Uo()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=Uo;window._runErpBatchRetry=Go;window._runErpBatchDelete=Ko;(function(){let e=null,n=!1;function a(){if(e)return e;const c=document.createElement("div");c.id="line-email-modal",c.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",c.innerHTML=`
            <div style="background:#fff;border-radius:16px;padding:28px 24px;max-width:420px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#06C755" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="4" width="20" height="16" rx="2"/>
                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                    </svg>
                    <h3 id="line-email-title-h" style="font-size:18px;font-weight:600;color:#0f172a;margin:0;"></h3>
                </div>
                <p id="line-email-sub-p" style="font-size:14px;color:#64748b;line-height:1.55;margin:0 0 18px;"></p>
                <input id="line-email-input" type="email" autocomplete="email" style="width:100%;padding:12px 14px;border:1px solid #e5e7eb;border-radius:10px;font-size:15px;outline:none;font-family:inherit;" />
                <div id="line-email-err" style="color:#dc2626;font-size:13px;margin-top:8px;min-height:18px;"></div>
                <button id="line-email-submit-btn" type="button" style="width:100%;margin-top:14px;padding:13px 16px;background:#111111;color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;"></button>
            </div>
        `,document.body.appendChild(c),e=c;const m=c.querySelector("#line-email-input"),p=c.querySelector("#line-email-submit-btn"),u=c.querySelector("#line-email-err");async function l(){u.textContent="";const d=(m.value||"").trim().toLowerCase();if(!d||d.indexOf("@")<0||d.split("@")[1].indexOf(".")<0){u.textContent=t("line-email-err-invalid");return}p.disabled=!0,p.style.opacity="0.6";try{const f=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:d})});if(!f.ok)throw new Error("http_"+f.status);const v=await f.json();v.token&&localStorage.setItem("mrpilot_token",v.token),typeof showToast=="function"&&showToast(v.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{u.textContent=t("line-email-err-failed"),p.disabled=!1,p.style.opacity="1"}}return p.addEventListener("click",l),m.addEventListener("keydown",function(d){d.key==="Enter"&&l()}),c}function o(){if(!e)return;const c=e.querySelector("#line-email-title-h"),m=e.querySelector("#line-email-sub-p"),p=e.querySelector("#line-email-input"),u=e.querySelector("#line-email-submit-btn");c&&(c.textContent=t("line-email-title")),m&&(m.textContent=t("line-email-sub")),p&&(p.placeholder=t("line-email-placeholder")),u&&(u.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const c=e.querySelector("#line-email-input");c&&setTimeout(function(){c.focus()},100)}async function i(){const c=localStorage.getItem("mrpilot_token");if(c)try{const m=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+c}});if(!m.ok)return;const p=await m.json();p&&p.needs_email&&s()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(u){let l=0;return u.length>=8&&l++,u.length>=12&&l++,/[a-zA-Z]/.test(u)&&/\d/.test(u)&&l++,/[^a-zA-Z0-9]/.test(u)&&l++,Math.min(3,l)}function n(u,l){const d=document.getElementById("cpw-msg");d&&(d.textContent=u,d.className="cpw-msg "+(l||""))}function a(u){return typeof t=="function"?t(u):u}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(l=>{const d=document.getElementById(l);d&&(d.value="",d.setAttribute("readonly","readonly"))});const u=document.getElementById("cpw-strength-bar");u&&(u.style.width="0%",u.className="cpw-strength-bar"),n("","")}async function i(){const u=document.getElementById("btn-change-pw"),l=document.getElementById("cpw-old"),d=document.getElementById("cpw-new"),f=document.getElementById("cpw-confirm"),v=document.getElementById("cpw-strength-bar");if(!u||!l||!d||!f)return;const w=l.value,g=d.value,b=f.value;if(!w||!g||!b){n(a("settings-change-pw-empty"),"error");return}if(g.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(g)&&/\d/.test(g))){n(a("settings-change-pw-too-weak"),"error");return}if(g!==b){n(a("settings-change-pw-mismatch"),"error");return}u.disabled=!0;const h=u.textContent;u.textContent=a("settings-change-pw-submitting"),n("","");try{const E=localStorage.getItem("mrpilot_token"),y=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+E},body:JSON.stringify({old_password:w,new_password:g})}),_=await y.json().catch(()=>({}));if(y.ok&&_.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),l.value="",d.value="",f.value="",v&&(v.style.width="0%",v.className="cpw-strength-bar");else{const k=_.detail||"";let x=a("settings-change-pw-success");k==="wrong_old_password"?x=a("settings-change-pw-wrong-old"):k==="password_too_short"?x=a("settings-change-pw-too-short"):k==="password_too_weak"?x=a("settings-change-pw-too-weak"):x=k||"Error",n(x,"error")}}catch(E){console.error("change_password",E),n("Network error","error")}finally{u.disabled=!1,u.textContent=h}}function r(){o||(o=!0,document.addEventListener("click",u=>{if(!u.target||!u.target.closest)return;const l=u.target.closest(".cpw-eye");if(l){const d=document.getElementById(l.dataset.target);d&&(d.type=d.type==="password"?"text":"password");return}if(u.target.closest("#cpw-forgot-link")){u.preventDefault(),c();return}if(u.target.closest("#btn-change-pw")){i();return}u.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",u=>{if(u.target&&u.target.id==="cpw-new"){const l=document.getElementById("cpw-strength-bar");if(!l)return;const d=e(u.target.value),f=["0%","33%","66%","100%"],v=["","weak","medium","strong"];l.style.width=f[d],l.className="cpw-strength-bar "+v[d]}}),document.addEventListener("focusin",u=>{u.target&&["cpw-old","cpw-new","cpw-confirm"].includes(u.target.id)&&u.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function c(){const u=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),l=u&&u.username?u.username:"",d=m(l);let f=document.getElementById("cpw-forgot-overlay");f&&f.remove(),f=document.createElement("div"),f.id="cpw-forgot-overlay",f.className="cpw-forgot-overlay",f.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${p(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${p(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${p(d)}</div>
                    <p class="cpw-forgot-tip">${p(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${p(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${p(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(f);const v=()=>f.remove();f.querySelector("#cpw-forgot-close").addEventListener("click",v),f.querySelector("#cpw-forgot-cancel").addEventListener("click",v),f.addEventListener("click",w=>{w.target===f&&v()}),f.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const w=f.querySelector("#cpw-forgot-send"),g=f.querySelector("#cpw-forgot-msg");w.disabled=!0;const b=w.textContent;w.textContent=a("cpw-forgot-sending");try{const h=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:l})}),E=await h.json().catch(()=>({}));h.ok?(g.textContent=a("cpw-forgot-success"),g.className="cpw-forgot-msg success",w.style.display="none",f.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(g.textContent=E.detail||a("cpw-forgot-fail"),g.className="cpw-forgot-msg error",w.disabled=!1,w.textContent=b)}catch{g.textContent=a("cpw-forgot-fail"),g.className="cpw-forgot-msg error",w.disabled=!1,w.textContent=b}})}function m(u){if(!u||!u.includes("@"))return u||"";const[l,d]=u.split("@");return l.length<=2?l+"****@"+d:l.slice(0,2)+"****@"+d}function p(u){return u==null?"":String(u).replace(/[&<>"']/g,l=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[l])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),c=r&&r.detail;let m="";if(typeof c=="string"?m=c:c&&typeof c=="object"&&(m=c.code||""),console.warn("[heartbeat] session revoked",m),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),m==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const p=m==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(p),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function pn(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),i=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const c=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",m=r.is_active===!1?"team-status-off":"team-status-on",p=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",u=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${m}"></span>
                            <span>${escapeHtml(p)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(c)}</span>
                            ${u}
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml((t("team-assigned-clients")||"已分配 {n} 客户").replace("{n}",r.assigned_client_count||0))}</span>
                        </div>
                    </div>
                </div>
                <div class="team-card-actions">
                    <button class="btn btn-ghost btn-small" data-assign-clients="${escapeHtml(r.id)}" data-name="${escapeHtml(r.username||"")}">
                        ${escapeHtml(t("team-assign-clients")||"分配客户")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-reset-pwd-employee="${escapeHtml(r.id)}" data-name="${escapeHtml(r.username||"")}" title="${escapeHtml(t("team-reset-pwd")||"重置密码")}">
                        ${escapeHtml(t("team-reset-pwd")||"重置密码")}
                    </button>
                    <button class="btn btn-ghost btn-small" data-toggle-employee="${escapeHtml(r.id)}" data-active="${r.is_active===!1?"false":"true"}">
                        ${escapeHtml(r.is_active===!1?t("team-enable")||"启用":t("team-disable")||"禁用")}
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger-text" data-remove-employee="${escapeHtml(r.id)}" data-name="${escapeHtml(r.username||"")}">
                        ${escapeHtml(t("team-remove")||"移除")}
                    </button>
                </div>
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Vl(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
        <div class="add-emp-modal">
            <div class="add-emp-head">
                <div class="add-emp-title">${escapeHtml(t("team-add")||"添加员工")}</div>
                <button class="add-emp-close" type="button" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="add-emp-body">
                <div class="add-emp-field">
                    <label>${escapeHtml(t("team-modal-username")||"员工用户名")}</label>
                    <input type="text" class="add-emp-input" id="add-emp-username" placeholder="${escapeHtml(t("team-modal-username-ph")||"employee01")}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t("team-modal-username-hint")||"3-50 位 · 字母 / 数字 / 下划线 / 点 / 横线 · 唯一")}</div>
                </div>
                <div class="add-emp-field">
                    <label>${escapeHtml(t("team-modal-email")||"邮箱(选填)")}</label>
                    <input type="email" class="add-emp-input" id="add-emp-email" placeholder="${escapeHtml(t("team-modal-email-ph")||"employee@example.com")}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t("team-modal-email-hint")||"选填 · 用于忘记密码时邮件重置 · 留空则只能由老板重置")}</div>
                </div>
                <div class="add-emp-field">
                    <label>${escapeHtml(t("team-modal-password")||"初始密码")}</label>
                    <input type="text" class="add-emp-input" id="add-emp-password" placeholder="${escapeHtml(t("team-modal-password-ph")||"至少 8 位 · 字母 + 数字")}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t("team-modal-password-hint")||"员工首次登录后会被强制修改密码")}</div>
                </div>
                <div class="add-emp-msg" id="add-emp-msg"></div>
            </div>
            <div class="add-emp-foot">
                <button class="btn btn-ghost" type="button" id="add-emp-cancel">${escapeHtml(t("btn-cancel")||"取消")}</button>
                <button class="btn btn-primary" type="button" id="add-emp-submit">${escapeHtml(t("team-add")||"添加员工")}</button>
            </div>
        </div>
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),c=document.getElementById("add-emp-submit"),m=(o.value||"").trim(),p=(s.value||"").trim(),u=i.value||"";if(r.textContent="",r.classList.remove("error"),!m||m.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(m)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(p&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(u.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(u)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(u)&&/\d/.test(u))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}c.disabled=!0,c.textContent=t("msg-saving")||"保存中...";try{const l={username:m,password:u};p&&(l.email=p);const d=await apiPost("/api/team/employees",l),f=d?await d.json().catch(()=>({})):{};if(d&&d.ok&&f&&f.ok){showToast(t("team-added")||"员工已添加","success"),n(),pn();return}const v=f&&f.detail||"unknown",w={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=w[v]||(t("team-create-failed")||"创建失败")+" ("+v+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{c.disabled=!1,c.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function Ul(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){pn();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Gl(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),pn();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function Kl(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const c=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",m=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(c.replace("{ch}",m),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Vl();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),Ul(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),Gl(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),Kl(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=pn;function Jl(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=Jl;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
