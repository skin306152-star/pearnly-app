(function(){const n=[];function a(s){try{n.push(Object.assign({ts:Date.now()},s)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(s)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(s){s.target&&s.target!==window&&(s.target.src||s.target.href)||a({type:"js_error",summary:String(s.message||"JS Error").slice(0,200),detail:{file:s.filename||"",line:s.lineno||0,col:s.colno||0,stack:s.error&&s.error.stack?String(s.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(s){const i=s.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const o=window.fetch;typeof o=="function"&&(window.fetch=function(){const s=arguments,i=Date.now(),r=typeof s[0]=="string"?s[0]:s[0]&&s[0].url||"?",d=s[1]&&s[1].method||"GET",m=String(r).split("?")[0];return o.apply(this,s).then(function(p){const f=Date.now()-i;if(p.ok)f>2500&&a({type:"api_slow",summary:d+" "+m+" → 慢 "+f+"ms",detail:{url:r,method:d,status:p.status,elapsed_ms:f}});else{let c="";try{p.clone().text().then(function(u){c=String(u||"").slice(0,500),a({type:"api_error",summary:d+" "+m+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:f,body_preview:c}})}).catch(function(){a({type:"api_error",summary:d+" "+m+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:f,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:d+" "+m+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:f}})}}return p}).catch(function(p){const f=Date.now()-i;throw a({type:"api_fail",summary:d+" "+m+" → 网络失败 ("+f+"ms)",detail:{url:r,method:d,elapsed_ms:f,error:String(p&&p.message||p)}}),p})}),["error","warn"].forEach(function(s){const i=console[s];typeof i=="function"&&(console[s]=function(){try{const r=[];for(let d=0;d<arguments.length;d++){const m=arguments[d];if(typeof m=="string")r.push(m);else if(m&&m instanceof Error)r.push(m.message);else try{r.push(JSON.stringify(m).slice(0,300))}catch{r.push(String(m))}}a({type:"console_"+s,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(o=>o.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function So(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function To(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function Mo(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function Xt(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const o in n)a=a.replace("{"+o+"}",n[o]);return a}function $o(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function Ho(e,n){n=n||14;const o={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${o}</svg>`}function Zt(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},o={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},s=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[s]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[s]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+o[s]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function Qt(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function Ao(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...Qt()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),o=a&&a.detail;let s="";if(typeof o=="string"?s=o:o&&typeof o=="object"&&(s=o.code||""),n.status===401||typeof s=="string"&&s.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,o),localStorage.removeItem("mrpilot_token"),s==="auth.session_revoked")Zt();else{const d=s==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xt(d),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=o,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function jo(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...Qt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.clone().json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Zt();else{const m=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xt(m),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function Po(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...Qt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Zt();else{const m=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xt(m),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const o=await a.json().catch(()=>({}));return{ok:a.ok&&o.ok!==!1,...o}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=Ao;window.apiPost=jo;window.t=Xt;window.escapeHtml=$o;window.svgIcon=Ho;window._showSessionRevokedModal=Zt;window._wsHeader=Qt;window.apiPut=Po;window.getMaxFiles=So;window.getMaxPagesPerFile=To;window.getMaxMbPerFile=Mo;function ke(e,n){const a=document.getElementById(e);if(!(!a||a.dataset.wbInjected==="1")){a.innerHTML=n,a.dataset.wbInjected="1";try{const o=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",s=window.I18N;if(!s||!s[o])return;a.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");s[o][r]&&(i.textContent=s[o][r])}),a.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");s[o][r]&&(i.placeholder=s[o][r])})}catch{}}}const Do=`
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
    `;ke("page-ocr",Do);const qo=`
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
`,Ro=`
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
`;ke("topbar",qo);ke("sidebar",Ro);function _n(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const o=document.getElementById("general-lang");o&&(o.value=e);const s=document.getElementById("col-conf-th");s&&s.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&En(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function Fo(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",s=>{s.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(s)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});Fo("lang-dropdown",e=>_n(e.dataset.lang));const Ia=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","receivables","reconcile","cloud","test-center"];function La(e){Ia.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(o=>o.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(o=>{o.classList.toggle("active",o.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function En(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function Ca(){try{const[e,n,a,o]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(s=>s.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,o&&(window._planState=o),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const s=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(s&&!i){window.location.replace("/home");return}if(!s&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=s}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,o&&(window._planState=o),window.renderBrandWorkspace(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(s){console.error("[nav-ia phase1] render avatar menu",s)}En(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const s=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(s&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(s&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(s){console.error("force-pw init",s)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(s){console.error("onboarding init",s)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(s){console.error("settings forms init",s)}}catch(e){console.error(e)}}window.applyLang=_n;window.routeTo=La;window.loadAll=Ca;window.updateUploadHint=En;try{_n(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");La(Ia.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);Ca();function zo(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){return!i||typeof i!="string"||(i=i.trim(),!i)?null:i.includes("@")&&i.indexOf("@")>0&&i.indexOf(".")>i.indexOf("@")?i.split("@")[0]:i}const o=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let s=null;for(const i of o){const r=a(i);if(r){s=r;break}}s||(s=t("brand-workspace-fallback")||"我的工作台"),e.textContent=s,e.title=s,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",s,"· _userInfo fields:",Object.keys(n))}function No(){let e=document.getElementById("offline-banner");e||(e=document.createElement("div"),e.id="offline-banner",e.className="offline-banner",e.style.display="none",document.body.insertBefore(e,document.body.firstChild));function n(){navigator.onLine===!1?(e.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",e.classList.remove("is-online"),e.classList.add("is-offline"),e.style.display="flex"):e.classList.contains("is-offline")?(e.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",e.classList.remove("is-offline"),e.classList.add("is-online"),setTimeout(()=>{e.style.display="none",e.classList.remove("is-online")},2e3)):e.style.display="none"}window.addEventListener("online",n),window.addEventListener("offline",n),n()}window.renderBrandWorkspace=zo;window.installNetworkBanner=No;const Sa="mrpilot_sidebar_collapsed";localStorage.getItem(Sa)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(Sa,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const o=document.querySelectorAll("#page-integrations .int-top-tab"),s=document.querySelectorAll("#page-integrations .int-top-panel");if(o.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),s.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),o&&o.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const o=a.target.closest("#page-integrations .int-top-tab");if(o){const i=o.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const o=document.querySelector(".auto-content");o&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(s){s.style.display="",o.appendChild(s)})}window.openIntegrationDrawer=function(a,o){const s=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),d=document.getElementById("int-drawer-body");if(!s||!d)return;e(),s.dataset.currentTab=a||"",r&&(r.textContent=o||""),d.innerHTML="";var m={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},p=m[a]||a;const f=document.querySelector('.auto-panel[data-auto-panel="'+p+'"]');f?(f.style.display="block",d.appendChild(f)):d.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',s.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var c={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(c[a])try{c[a]()}catch(l){console.warn("[int-drawer] loader error",l)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(l){console.warn("[int-drawer] ERP load error",l)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),o&&(o.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),o=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),o&&o.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(s){s.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(s=>{s.addEventListener("click",()=>switchSettingsTab(s.dataset.tab))});let o=null;try{o=localStorage.getItem("mrpilot_settings_tab")}catch{}if(o){const s=document.querySelector(`.settings-tab[data-tab="${o}"]`);if(s&&s.style.display!=="none"){switchSettingsTab(o);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),o=document.getElementById("btn-save-company");if(!a&&!o){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),o&&o.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let Ft=null;function Oo(){vn(),Ft=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&vn()}catch{}},1e4)}function vn(){Ft&&(clearInterval(Ft),Ft=null)}window.startEnginePolling=Oo;window.stopEnginePolling=vn;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target.closest("[data-rd-action]");if(n){const s=n.dataset.rdAction,i=n.dataset.rdSide;s==="verify"?callRdVerify(i):s==="sync"&&callRdSync(i);return}if(e.target.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=e.target.closest("[data-archive-copy]");if(o){const s=o.dataset.archiveCopy;navigator.clipboard?.writeText(s).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const ea=document.getElementById("btn-custom-template");ea&&ea.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});const Vo=`
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
    `,Uo=`
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
`;ke("pearnly-confirm-modal",Vo);ke("confirm-modal",Uo);window.pearnlyConfirm=function(e,n){return new Promise(function(a){const o=document.getElementById("pearnly-confirm-modal"),s=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),d=document.getElementById("pearnly-confirm-cancel"),m=document.getElementById("pearnly-confirm-close");if(!o||!i||!r||!d){a(window.confirm(e));return}s&&(s.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",o.style.display="flex";function p(v){o.style.display="none",r.removeEventListener("click",f),d.removeEventListener("click",c),m&&m.removeEventListener("click",c),o.removeEventListener("click",l),document.removeEventListener("keydown",u),a(v)}function f(){p(!0)}function c(){p(!1)}function l(v){v.target===o&&p(!1)}function u(v){v.key==="Escape"?p(!1):v.key==="Enter"&&p(!0)}r.addEventListener("click",f),d.addEventListener("click",c),m&&m.addEventListener("click",c),o.addEventListener("click",l),document.addEventListener("keydown",u),setTimeout(function(){try{d.focus()}catch{}},50)})};const Go=`
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

`,Ko=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Go+Ko,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Jo=`
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

`,Wo=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Jo+Wo,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function Yo(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function Xo(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function Zo(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function Qo(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function es(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let d=null;const m=()=>{d&&(clearTimeout(d),d=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(d=setTimeout(m,r)),m}window.showAlert=Yo;window.hideAlerts=Xo;window._humanizeBackendError=Zo;window.humanizeError=Qo;window.showToast=es;function ts(e,n){return n=n||{},new Promise(a=>{const o=document.getElementById("confirm-modal"),s=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),d=document.getElementById("confirm-modal-close"),m=document.getElementById("confirm-modal-title");if(!o||!s||!i||!r){a(!1);return}m.textContent=n.title||t("confirm-default-title");const p=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const u=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),v=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");s.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${u}</div>
                <input type="text" id="${p}" placeholder="${v}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else s.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",o.style.display="flex";const f=u=>{o.style.display="none",i.onclick=null,r.onclick=null,d.onclick=null,o.onclick=null,document.removeEventListener("keydown",l),n.promptInput&&(s.innerHTML=""),r.style.display="",a(u)},c=()=>{const u=p?document.getElementById(p):null;return u?u.value:""},l=u=>{u.key==="Escape"?f(n.promptInput?null:!1):u.key==="Enter"&&f(n.promptInput?c():!0)};i.onclick=()=>f(n.promptInput?c():!0),r.onclick=()=>f(n.promptInput?null:!1),d.onclick=()=>f(n.promptInput?null:!1),o.onclick=u=>{u.target===o&&f(n.promptInput?null:!1)},document.addEventListener("keydown",l),setTimeout(()=>{if(n.promptInput){const u=document.getElementById(p);u&&u.focus()}else i.focus()},50)})}window.showConfirm=ts;function ns(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof hn=="function"&&hn()}catch(n){console.warn("settings tab side effect failed:",n)}}}function as(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function os(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function ss(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function hn(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}is(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function is(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
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
    `}window.switchSettingsTab=ns;window.fillSettingsForms=as;window.saveProfile=os;window.saveCompany=ss;window.renderSettings=hn;function en(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function Bn(e){return e=e||_userInfo,!!e&&(e.role==="owner"||en(e))}function Ta(e){return e=e||_userInfo,!!e&&e.role==="member"&&!en(e)}function rs(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!en(e)}function Ma(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function $a(e){return Ta(e)}function ls(e){return Bn(e)}function cs(e){return Bn(e)&&Ma(e)}window.isMoneyHidden=$a;window.isSuperAdmin=en;window.isOwner=Bn;window.isEmployee=Ta;window.isTrial=rs;window.isLifetime=Ma;window.shouldHideMoney=$a;window.canManageTeam=ls;window.canManageApiKey=cs;function ds(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,d;if(o===0)r="danger",d=t("quota-banner-exhausted");else if(s>=90)r="danger",d=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",d=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(d)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const m=e.querySelector(".quota-banner-close");m&&m.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function ps(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const d=document.querySelector('.settings-tab[data-tab="team"]');d&&(d.style.display=a?"":"none");const m=document.querySelector('.settings-panel[data-settings-panel="team"]');m&&(m.dataset.permHidden=a?"0":"1");const p=document.querySelector('.settings-tab[data-tab="api"]');p&&(p.style.display=o||isSuperAdmin(e)?"":"none");const f=document.querySelector('.settings-tab[data-tab="plan"]');f&&(f.style.display=n?"none":"");const c=document.querySelector('.settings-tab[data-tab="company"]');c&&(c.style.display=n?"none":"");const l=document.getElementById("info-bar");l&&(l.style.display=n?"none":"");const u=document.getElementById("trial-banner");u&&n&&(u.style.display="none");const v=document.getElementById("plan-banner");v&&n&&(v.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(w=>{w.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const w=document.querySelector(".settings-tab.active");w&&w.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(w){console.warn("[v118.12.3] failed to fix active tab:",w)}if(window.PEARNLY_ADMIN_MODE){const w=document.getElementById("admin-mode-banner");w&&(w.style.display="flex"),document.querySelectorAll(".nav-item").forEach(h=>{h.classList.contains("nav-admin-only")||(h.style.display="none")}),document.querySelectorAll(".nav-group").forEach(h=>{h.classList.contains("nav-group-admin-only")||(h.style.display="none")});const b=document.getElementById("client-switcher");b&&(b.style.display="none"),document.body.classList.add("admin-mode");const g=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(h=>{const I=h.dataset.tab;I&&!g.includes(I)&&(h.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(h=>{const I=h.dataset.pane;I&&!g.includes(I)&&(h.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(h=>{const I=h.querySelectorAll(".settings-tab");Array.from(I).some(x=>x.style.display!=="none")||(h.style.display="none")})}}function us(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
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
        `;else{const s=e.tenant_used!=null?e.tenant_used:e.used_this_month||0,i=e.tenant_quota!=null&&e.tenant_quota>0?e.tenant_quota:e.monthly_quota||0,r=i>0?Math.min(100,s/i*100):0;let d="";r>=95?d="danger":r>=80&&(d="warn"),i>0?a=`
                <div class="info-chip">
                    <span class="chip-label">${escapeHtml(t("info-monthly"))}</span>
                    <span class="chip-value">${s} / ${i}</span>
                    <div class="mini-bar"><div class="mini-bar-fill ${d}" style="width:${r}%"></div></div>
                </div>
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=ds;window.applySidebarVisibility=ps;window.renderInfoBar=us;async function Ha(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function Aa(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Nt(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function We(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function fs(e){const a=Nt(e==="seller"?"seller_tax":"buyer_tax");We(e,t("rd-verifying"),"loading");const o=await Ha("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){We(e,t(Aa(o.error)),"error");return}o.data&&o.data.valid?We(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):We(e,t("rd-status-invalid"),"invalid")}async function ms(e){const a=Nt(e==="seller"?"seller_tax":"buyer_tax");We(e,t("rd-syncing"),"loading");const o=await Ha("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){We(e,t(Aa(o.error)),"error");return}We(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),vs(e,o.data)}}function vs(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=Nt(a),i=Nt(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==i&&r.push({field:o,label:t("rd-field-address"),current:i,official:n.address});const d=[];n.branch_label&&d.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&d.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let m=document.getElementById("rd-sync-modal");if(m||(m=document.createElement("div"),m.id="rd-sync-modal",m.className="rd-modal-mask",document.body.appendChild(m)),r.length===0)m.innerHTML=`
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
                    ${d.length?`<div class="rd-modal-extra">${d.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                </div>
            </div>
        `;else{const c=r.map((l,u)=>`
            <label class="rd-diff-row">
                <input type="checkbox" data-rd-apply data-field="${l.field}" data-value="${escapeHtml(l.official)}" checked>
                <div class="rd-diff-label">${escapeHtml(l.label)}</div>
                <div class="rd-diff-col rd-diff-current">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-current"))}</div>
                    <div class="rd-diff-val">${escapeHtml(l.current||"—")}</div>
                </div>
                <div class="rd-diff-arrow">→</div>
                <div class="rd-diff-col rd-diff-official">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-official"))}</div>
                    <div class="rd-diff-val">${escapeHtml(l.official)}</div>
                </div>
            </label>
        `).join("");m.innerHTML=`
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t("rd-modal-title"))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    ${c}
                    ${d.length?`<div class="rd-modal-extra">${d.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t("rd-modal-apply"))}</button>
                </div>
            </div>
        `}m.classList.add("show");const p=()=>m.classList.remove("show");m.querySelector(".rd-modal-close").addEventListener("click",p),m.querySelectorAll("[data-rd-modal-close]").forEach(c=>c.addEventListener("click",p)),m.addEventListener("click",c=>{c.target===m&&p()});const f=m.querySelector("[data-rd-modal-apply]");f&&f.addEventListener("click",()=>{const c=_results[_drawerIdx];if(!c){p();return}m.querySelectorAll("[data-rd-apply]:checked").forEach(l=>{const u=l.dataset.field,v=l.dataset.value;c.edits[u]=v,c.merged_fields[u]=v;const w=document.querySelector(`[data-field="${u}"]`);w&&(w.value=v);const b=document.querySelector(`[data-field-wrap="${u}"]`);b&&b.classList.add("edited")}),updateDrawerEditCount(),renderResults(),p()})}window.callRdVerify=fs;window.callRdSync=ms;function hs(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(s=>!s.is_duplicate&&!s.is_copy),o=a.length>0?a:e;for(const s of o){const i=s.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function gs(e){const n=e.target.dataset.field,a=e.target.value,o=_results[_drawerIdx],s=o.merged_fields[n];a===(s??"")?delete o.edits[n]:(o.edits[n]=a,o.merged_fields[n]=a);const i=document.querySelector(`[data-field-wrap="${n}"]`);i&&i.classList.toggle("edited",o.edits[n]!==void 0),ja(),renderResults()}function ja(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=hs;window.onFieldEdit=gs;window.updateDrawerEditCount=ja;function bs(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,o=document.getElementById("force-pw-new").value,s=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!o){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(o!==s){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(o.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(o)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(o)&&/\d/.test(o))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(o===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:o})}),d=await r.json().catch(()=>({}));if(!r.ok){const m=d&&d.detail||"unknown",p={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=p[m]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=bs;(function(){let e=null,n=null,a=null,o=null;function s(h){return document.getElementById(h)}async function i(){v(),b(),await r()}async function r(){try{const h=localStorage.getItem("mrpilot_token"),I=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!I.ok){w(t("linebot-err-status"));return}const y=await I.json();y.bound?d(y):await m()}catch{w(t("linebot-err-status"))}}function d(h){u(),s("linebot-unbound").style.display="none",s("linebot-bound").style.display="block";const I=s("linebot-status-summary");I&&(I.textContent=t("linebot-status-bound"),I.style.background="#D1FAE5",I.style.color="#065F46");const y=s("linebot-bound-name");y&&(y.textContent=h.line_display_name||"(LINE User)");const x=s("linebot-avatar");x&&(h.line_picture_url?(x.src=h.line_picture_url,x.style.display=""):x.style.display="none");const E=s("linebot-bound-since");E&&h.bound_at&&(E.textContent=new Date(h.bound_at).toLocaleString())}async function m(){s("linebot-bound").style.display="none",s("linebot-unbound").style.display="block";const h=s("linebot-status-summary");h&&(h.textContent=t("linebot-status-unbound"),h.style.background="#FEE2E2",h.style.color="#B91C1C"),await p(),l()}async function p(){try{const h=localStorage.getItem("mrpilot_token"),I=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+h}});if(!I.ok){w(t("linebot-err-code"));return}const y=await I.json();a=y.code,o=new Date(y.expires_at).getTime(),f(y)}catch{w(t("linebot-err-code"))}}function f(h){const I=s("linebot-code");I&&(I.textContent=h.code);const y=s("linebot-bot-id");y&&(y.textContent=h.bot_basic_id||t("linebot-bot-id-missing"));const x=s("linebot-qr");if(x)if(h.bot_friend_url){const E="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(h.bot_friend_url);x.classList.remove("empty"),x.innerHTML='<img src="'+E+'" alt="LINE Bot QR">'}else x.classList.add("empty"),x.innerHTML="";c()}function c(){e&&clearInterval(e);const h=s("linebot-code-expires");function I(){if(!o)return;const y=o-Date.now();if(y<=0){h&&(h.textContent=t("linebot-code-expired"),h.classList.add("expiring"));const k=s("linebot-code");k&&(k.style.opacity="0.4"),clearInterval(e),e=null;return}const x=Math.floor(y/1e3),E=Math.floor(x/60),_=x%60;h&&(h.textContent=t("linebot-code-expires-in").replace("{m}",E).replace("{s}",String(_).padStart(2,"0")),y<6e4?h.classList.add("expiring"):h.classList.remove("expiring"))}I(),e=setInterval(I,1e3)}function l(){u(),n=setInterval(async()=>{try{const h=localStorage.getItem("mrpilot_token"),I=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!I.ok)return;const y=await I.json();y.bound&&d(y)}catch{}},4e3)}function u(){n&&(clearInterval(n),n=null)}function v(){e&&(clearInterval(e),e=null),u()}function w(h){const I=s("linebot-error");I&&(I.textContent=h,I.style.display="block")}function b(){const h=s("linebot-error");h&&(h.style.display="none")}async function g(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const I=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+I}})).ok){w(t("linebot-err-unbind"));return}await i()}catch{w(t("linebot-err-unbind"))}}document.addEventListener("click",h=>{if(h.target.closest("#linebot-code-refresh")){h.preventDefault(),b(),p();return}if(h.target.closest("#linebot-unbind")){h.preventDefault(),g();return}}),window._loadLineBotPanel=i})();function tn(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const d=parseFloat(r.merged_fields.total_amount);isNaN(d)||(n+=d)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,d)=>({...r,_idx:d}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(d=>(d.filename||"").toLowerCase().includes(r)||(d.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,d)=>{let m,p;return _sortKey==="filename"?(m=r.filename,p=d.filename):_sortKey==="invoice_no"?(m=r.merged_fields.invoice_number,p=d.merged_fields.invoice_number):_sortKey==="invoice_date"?(m=r.merged_fields.date,p=d.merged_fields.date):_sortKey==="total"?(m=parseFloat(r.merged_fields.total_amount)||0,p=parseFloat(d.merged_fields.total_amount)||0):_sortKey==="confidence"?(m=r.confidence,p=d.confidence):(m="",p=""),m<p?_sortDir==="asc"?-1:1:m>p?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=s.map((r,d)=>{const m=r.merged_fields,p=`<span class="empty-cell">${t("empty-val")}</span>`,f="conf-tip-"+(r.confidence||"low"),c="conf-"+(r.confidence||"low"),l=t(f),u=t(c);return`
            <tr data-idx="${r._idx}">
                <td class="num">${d+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${m.invoice_number?escapeHtml(m.invoice_number):p}</td>
                <td class="date">${m.date?escapeHtml(m.date):p}</td>
                <td class="amount">${m.total_amount?Number(m.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):p}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(l)}">${u}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const d=parseInt(r.dataset.idx,10);Da(d)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),tn()})});let ta=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(ta),ta=setTimeout(()=>{_searchKeyword=n.trim(),tn(),Pa()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",tn(),Pa(),e.focus()});function Pa(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function Da(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,i=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,d=document.getElementById("drawer-body"),m=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,p=i?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(d.innerHTML=`
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
            ${_e("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",s)}
            ${_e("date","drawer-lbl-date",r.date,"input",s)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${_e("subtotal","drawer-lbl-subtotal",r.subtotal,"input",s)}
            ${_e("vat","drawer-lbl-vat",r.vat,"input",s)}
            ${_e("total_amount","drawer-lbl-total",r.total_amount,"input",s)}
            ${r.wht_amount||r.wht_rate?`
                ${_e("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,ys(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${_e("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${_e("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,p,na("seller"))}
            ${_e("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${_e("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${_e("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,p,na("buyer"))}
            ${_e("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?ws(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${_e("notes","drawer-lbl-notes",r.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(f=>`--- Page ${f.page||f.page_number||"?"} ---
${f.raw_text||f.text||""}`).join(`

`))}</pre>
        </details>
    `,s?d.querySelectorAll("[data-field]").forEach(f=>{f.addEventListener("input",onFieldEdit)}):d.querySelectorAll("[data-field]").forEach(f=>{f.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const f=n._historyId||n.history_id||null;window.bindDrawerClient(f,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const f=document.getElementById("drawer-cat-input");f&&!f.value&&!f.readOnly&&f.focus()},80)}function ys(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function _e(e,n,a,o,s,i,r){const d=_results[_drawerIdx],m=d&&d.edits[e]!==void 0?d.edits[e]:a,p=d&&d.edits[e]!==void 0&&d.edits[e]!==a,f=escapeHtml(m??""),c=s?"":"readonly",l=o==="textarea"?`<textarea data-field="${e}" rows="2">${f}</textarea>`:`<input type="text" data-field="${e}" value="${f}">`;return`
        <div class="drawer-field ${p?"edited":""} ${c}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${l}
        </div>
    `}function na(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function ws(e){return`
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
    `}function ks(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=tn;window.openDrawer=Da;window.closeDrawer=ks;function xs(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(d){return d&&d.enabled!==!1&&(d.adapter||"").toLowerCase()!=="mrerp_dms"});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let i;if(o.length===1){const d=o[0].name||o[0].adapter||"ERP";i=t("btn-push-to-name",{name:d}),s.title=i}else i=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,s.addEventListener("click",function(d){d.preventDefault(),d.stopPropagation(),o.length===1?qa(n,o[0].id):_s(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function _s(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(m=>m.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const i=a.map(function(m){const p=escapeHtml(m.name||m.adapter||"ERP"),f=escapeHtml((m.adapter||"").toLowerCase()),l=m.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(m.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+f+"</span>"+p+l+"</span></button>"}).join("");s.innerHTML=i,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",d,!0)},d=m=>{!s.contains(m.target)&&m.target!==e&&!e.contains(m.target)&&r()};setTimeout(()=>document.addEventListener("click",d,!0),0),s.addEventListener("click",m=>{const p=m.target.closest("[data-ep-id]");if(!p)return;const f=p.getAttribute("data-ep-id");r(),qa(n,f)})}async function qa(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),i=await s.json();if(!s.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=xs;const Es=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function Ra(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function Bs(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function Fa(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const p=[];for(const f of _results){const c=f.invoices&&f.invoices.length>0?f.invoices:null;if(c&&c.length>1)for(let l=0;l<c.length;l++){const u=c[l]||{};p.push({filename:f.filename+" #"+(l+1)+"/"+c.length,engine:f.engine,merged_fields:u.fields||{}})}else p.push({filename:f.filename,engine:f.engine,merged_fields:f.merged_fields})}a=await apiPost("/api/ocr/export",{records:p,lang:currentLang,template:"sales_detail_th"})}else{const p=[];for(const c of _results)c.history_ids&&Array.isArray(c.history_ids)?p.push(...c.history_ids):c.history_id&&p.push(c.history_id);if(p.length===0){showToast(t("toast-export-error"),"error");return}const f=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+f,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:p,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let p="HTTP "+a.status;try{const c=await a.json();c&&c.detail&&(p=typeof c.detail=="string"?c.detail:JSON.stringify(c.detail))}catch(c){console.warn("[export] resp.json err.detail parse failed:",c)}const f=typeof p=="string"&&p.indexOf(".")>0?"err."+p:null;showToast(f?t(f):t("toast-export-error")+" · "+p,"error");return}const s=await a.blob();let i=o;const r=a.headers.get("X-Filename");if(r)i=r;else{const f=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(f)try{i=decodeURIComponent(f[1])}catch{}}const d=URL.createObjectURL(s),m=document.createElement("a");m.href=d,m.download=i,document.body.appendChild(m),m.click(),document.body.removeChild(m),URL.revokeObjectURL(d),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{Fa(Ra())});function Is(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=Ra(),o=Es.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
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
    `;n.innerHTML=o+s,e.appendChild(n)}function cn(){const e=document.getElementById("export-dropdown");e&&e.remove()}const dn=document.getElementById("btn-export-arrow");dn&&dn.addEventListener("click",e=>{e.stopPropagation(),!dn.disabled&&Is()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){cn(),showToast(t("cs-coming-soon"),"info");return}Bs(a),cn(),Fa(a);return}e.target.closest("#btn-export-arrow")||cn()});function Ls(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(Ls,300);const Cs=`
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
`;(function(){const e=document.getElementById("page-history");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Cs,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();function In(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const i=s.filter(r=>_historySelected.has(r.id)).length;a.checked=i===s.length,a.indeterminate=i>0&&i<s.length}}}function Ss(){_historySelected.clear(),In()}async function Ln(){if(!_userInfo){setTimeout(()=>Ln(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&s.set("client_id",String(i));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const p=await r.json().catch(()=>({}));if((typeof p.detail=="string"?p.detail:p.detail&&p.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const d=await r.json();_historyState.items=d.items||[],_historyState.total=d.total||0;const m=new Set(_historyState.items.map(p=>p.id));for(const p of Array.from(_historySelected))m.has(p)||_historySelected.delete(p);za()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function za(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(p=>{p.confidence==="high"&&s++});const i=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(p=>{const f=new Date(p.created_at),c=String(f.getMonth()+1).padStart(2,"0"),l=String(f.getDate()).padStart(2,"0"),u=String(f.getHours()).padStart(2,"0"),v=String(f.getMinutes()).padStart(2,"0"),w=`${c}-${l} ${u}:${v}`,b=escapeHtml(p.filename||""),g=b.length>50?b.substring(0,50)+"…":b,h=p.invoice_no?escapeHtml(p.invoice_no):g,I=[];p.seller_name&&I.push(escapeHtml(p.seller_name)),p.invoice_no&&p.filename&&I.push(g);const y=I.join(" · ")||"-",x=p.category_tag?`<span class="history-badge category">${escapeHtml(p.category_tag)}</span>`:"",E=p.source_total&&p.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:p.source_index||1,n:p.source_total}))}</span>`:"",_=p.total_amount!==null&&p.total_amount!==void 0?Number(p.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',k=[];(p.total_amount===null||p.total_amount===void 0)&&k.push(t("field-amount")),p.invoice_no||k.push(t("field-invoice-no")),p.invoice_date||k.push(t("field-invoice-date")),p.seller_name||k.push(t("field-seller-name")),k.length>0&&`${escapeHtml(p.id)}${escapeHtml(t("history-needs-review-tip")+" · "+k.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,p.edited&&`${escapeHtml(t("history-edited",{n:p.edit_count||1}))}`;const B=p.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",L=p.confidence==="high"?"high":p.confidence==="medium"?"mid":"low",C=p.confidence==="high"?t("conf-high"):p.confidence==="medium"?t("conf-medium"):t("conf-low"),S=`<span class="history-badge conf-${L}">${escapeHtml(C)}</span>`;let M="";const $=p.source||"manual";return $==="email"?M=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:$==="folder"?M=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:$==="api"&&(M=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(p.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(p.id)}" ${_historySelected.has(p.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${w}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${h} ${x} ${E} ${M} ${B}</div>
                        <div class="history-cell-subtitle">${y}</div>
                    </div>
                    <div class="history-cell-amount">${_}</div>
                    <div class="history-cell-conf">${S}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(p.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),In();const d=a.length>0?_historyState.page*_historyState.pageSize+1:0,m=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:d,to:m,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=Ln;window.renderHistoryList=za;window.updateHistoryBatchBar=In;window.clearHistorySelection=Ss;typeof currentRoute<"u"&&currentRoute==="history"&&Ln();async function Ot(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),Ms(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),$s(a.id)}catch(n){console.error("open history detail failed",n)}}async function Ts(e){await Ot(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function Ms(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",As),document.getElementById("btn-push-erp").addEventListener("click",Hs)}async function $s(e){}async function Hs(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function As(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(d=>!d.is_duplicate&&!d.is_copy),s=o>=0?o:0,i=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function js(e,n){document.querySelectorAll(".history-popover").forEach(p=>p.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(p=>p.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",i=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const d=()=>{r.remove(),document.removeEventListener("click",m,!0)},m=p=>{!r.contains(p.target)&&p.target!==n&&d()};setTimeout(()=>document.addEventListener("click",m,!0),0),r.addEventListener("click",async p=>{const f=p.target.closest("[data-act]");if(!f||f.disabled)return;const c=f.dataset.act;if(d(),c==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const u=document.createElement("textarea");u.value=s,u.style.position="fixed",u.style.opacity="0",document.body.appendChild(u),u.select(),document.execCommand("copy"),document.body.removeChild(u),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(c==="download-pdf"){const l=showToast(t("history-download-pdf-loading"),"loading",0);try{const u=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!u.ok)throw new Error("download failed");const v=await u.blob(),w=URL.createObjectURL(v),b=document.createElement("a");b.href=w,b.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(b),b.click(),document.body.removeChild(b),setTimeout(()=>URL.revokeObjectURL(w),5e3),l(),showToast(t("history-download-pdf-ok"),"success")}catch{l(),showToast(t("history-download-pdf-fail"),"error")}}else if(c==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const d=r.target.closest(".history-row"),m=r.target.closest("[data-hmenu]");if(m){r.stopPropagation(),js(m.dataset.hmenu,m);return}const p=r.target.closest("[data-review]");if(p){r.stopPropagation(),Ot(p.dataset.review);return}const f=r.target.closest("[data-fill-amount]");if(f){r.stopPropagation(),Ts(f.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||d&&!r.target.closest("[data-hmenu]")&&Ot(d.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const d=r.target.closest(".history-row-check");if(!d)return;const m=d.dataset.hid;d.checked?_historySelected.add(m):_historySelected.delete(m),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const d=r.target.checked;for(const m of _historyState.items)d?_historySelected.add(m.id):_historySelected.delete(m.id);document.querySelectorAll(".history-row-check").forEach(m=>{m.checked=d}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const m=Array.from(_historySelected);try{const p=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:m})});if(!p.ok)throw new Error("batch delete failed");const f=await p.json();showToast(t("history-batch-done",{n:f.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(p){console.error("batch delete",p),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const d=r.target.value;document.getElementById("history-search-clear").style.display=d?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=d.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=Ot;const dt=document.getElementById("drop-zone"),Cn=document.getElementById("file-input");dt.addEventListener("click",()=>Cn.click());Cn.addEventListener("change",e=>Na(e.target.files));["dragover","dragenter"].forEach(e=>{dt.addEventListener(e,n=>{n.preventDefault(),dt.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{dt.addEventListener(e,n=>{n.preventDefault(),dt.classList.remove("drag-over")})});dt.addEventListener("drop",e=>{e.preventDefault(),Na(e.dataTransfer.files)});const Ps=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function gn(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function Ds(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function qs(e){return Ds(e)||gn(e)||Ps.test(e.name)}function Na(e){hideAlerts();const n=Array.from(e),a=n.filter(qs);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(d=>!gn(d)),s=a.filter(gn),i=new Set(_selectedFiles.map(d=>d.name+"_"+d.size));for(const d of o){const m=d.name+"_"+d.size;i.has(m)||(_selectedFiles.push({file:d,name:d.name,size:d.size,status:"waiting",errorKey:null,errorParams:null}),i.add(m))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(d){console.error("[upload] image route failed",d)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),nn(),Sn(),Cn.value=""}let Dt=!1;function nn(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(c=>c.status==="processing"||c.status==="retrying").length,o=_selectedFiles.filter(c=>c.status==="success").length,s=_selectedFiles.filter(c=>c.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const d=Dt?t("file-list-collapse"):t("file-list-expand"),m=_selectedFiles.map((c,l)=>{let u=t("status-"+c.status);c.status==="retrying"&&(u=t("status-retrying")),c.status==="error"&&c.errorKey&&(u=t(c.errorKey,c.errorParams||{}));const v=c.status==="processing"||c.status==="retrying"?'<span class="spinner"></span>':"",w=c.status==="error"&&c.canRetry?`<button class="file-retry-btn" data-retry-idx="${l}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",b=c.status==="success"&&c.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</span>
                ${b}
                <span class="file-status ${c.status}">${v}${u}</span>
                ${w}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(d)}</button>`:""}
        </div>
        <ul class="file-list-body${Dt?" expanded":""}" id="file-list-body">
            ${m}
        </ul>
    `;const p=document.getElementById("file-list-toggle");p&&p.addEventListener("click",()=>{Dt=!Dt,nn()});const f=document.getElementById("file-list-body");f&&!f.dataset.retryBound&&(f.dataset.retryBound="1",f.addEventListener("click",async c=>{const l=c.target.closest(".file-retry-btn");if(!l)return;const u=parseInt(l.dataset.retryIdx||"-1",10);if(u<0||u>=_selectedFiles.length)return;const v=_selectedFiles[u];!v||v.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(v,!0)}))}function Sn(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],nn(),renderResults(),Sn(),hideAlerts()});window.renderFileList=nn;window.updateStartButton=Sn;const Rs=`
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
`;ke("camera-tips-modal",Rs);async function Vt(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],i=o.naturalWidth,r=o.naturalHeight;(i<1e3||r<1e3)&&s.push("low_res");try{const d=document.createElement("canvas");d.width=64,d.height=64;const m=d.getContext("2d");m.drawImage(o,0,0,64,64);const p=m.getImageData(0,0,64,64).data;let f=0,c=0;for(let u=0;u<p.length;u+=4)f+=.299*p[u]+.587*p[u+1]+.114*p[u+2],c++;const l=c?f/c:128;l<70?s.push("too_dark"):l>235&&s.push("too_bright"),n({warnings:s,width:i,height:r,brightness:l})}catch{n({warnings:s,width:i,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}async function Oa(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let p=0;p<e.length;p++){const f=e[p],{dataUrl:c,naturalW:l,naturalH:u}=await Fs(f);p>0&&s.addPage("a4","p");const v=l/u;let w=a-10,b=w/v;b>o-10&&(b=o-10,w=b*v);const g=(a-w)/2,h=(o-b)/2,I=f.type==="image/png"?"PNG":"JPEG";s.addImage(c,I,g,h,w,b,void 0,"FAST")}const i=s.output("blob"),r=new Date,d=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),m=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${d}${m}.pdf`,{type:"application/pdf"})}function Fs(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await Ns()||o.click()}),o.addEventListener("change",async d=>{const m=Array.from(d.target.files||[]);if(d.target.value="",m.length!==0)for(const p of m)await bn([p],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=d=>async m=>{const p=Array.from(m.target.files||[]);if(m.target.value="",p.length===0)return;const f=p.filter(l=>l.type==="application/pdf"||/\.pdf$/i.test(l.name)),c=p.filter(l=>!f.includes(l));f.length>0&&await zs(f),c.length>0&&await bn(c,d)};a&&a.addEventListener("change",r("gallery"))})();async function zs(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function Ns(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const i=d=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(d)},r=d=>{d.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),o&&(o.onclick=()=>i(!1)),n.onclick=d=>{d.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}let Se=[],Je=null;async function bn(e,n){if(hideAlerts(),!(!e||e.length===0)){var a=typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice";if(a==="thai_id_card"){for(const s of e)_selectedFiles.push({file:s,name:s.name,size:s.size,status:"waiting",errorKey:null,errorParams:null});const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton();return}if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let o=0;o<30&&(await new Promise(s=>setTimeout(s,100)),!(window.jspdf&&window.jspdf.jsPDF));o++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const o=e[0];let s={};try{s=await Vt(o)}catch{}Se.push({file:o,quality:s}),Je="camera",st();return}if(n==="gallery"&&(e.length>=2||Se.length>0)){for(const o of e){let s={};try{s=await Vt(o)}catch{}Se.push({file:o,quality:s})}Je="gallery",st();return}await Va(e)}}async function Os(e){const n=new Set;for(const o of e)try{((await Vt(o)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const o=await Oa(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function st(){let e=document.getElementById("camera-buffer-bar");if(Se.length===0){e&&e.remove(),Je=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=Se.length,a=n>=2,o=Je==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?o?i=`
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
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{Se=[],Je=null,st()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const m=o?"gallery-input":"camera-input",p=document.getElementById(m);p&&p.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const m=Se.map(p=>p.file);Se=[],Je=null,st(),await Os(m)});const d=e.querySelector('[data-cbb-action="separate"]');d&&(d.onclick=async()=>{const m=Se.map(p=>p.file);Se=[],Je=null,st(),await Va(m)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{Se.length>0&&st()});async function Va(e){const n=new Set;let a=0;for(const s of e)try{((await Vt(s)).warnings||[]).forEach(d=>n.add(d));const r=await Oa([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}window.handleCameraImages=bn;(function(){var e="pearnly_ocr_doc_mode",n=!1,a=!1;function o(l){return typeof escapeHtml=="function"?escapeHtml(l==null?"":String(l)):String(l??"")}function s(){try{return localStorage.getItem(e)==="thai_id_card"?"thai_id_card":"invoice"}catch{return"invoice"}}window.getOcrDocumentMode=function(){return n?s():"invoice"};function i(){var l=document.getElementById("drop-zone");return l?l.closest(".card"):null}function r(){var l=i();if(!l)return null;var u=l.querySelector("#ocr-doc-mode");if(u)return u;var v=l.querySelector(".section-head");return u=document.createElement("div"),u.id="ocr-doc-mode",u.className="ocr-doc-mode",u.setAttribute("role","tablist"),u.style.cssText="display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;",v&&v.parentNode?v.parentNode.insertBefore(u,v.nextSibling):l.insertBefore(u,l.firstChild),u}function d(l,u,v){return'<button type="button" class="ocr-doc-seg'+(v?" active":"")+'" data-doc-mode="'+l+'" role="tab" aria-selected="'+(v?"true":"false")+'" style="border:none;background:'+(v?"var(--card,#fff)":"transparent")+";color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:"+(v?"600":"500")+";padding:6px 16px;border-radius:7px;cursor:pointer;box-shadow:"+(v?"0 1px 3px rgba(0,0,0,.08)":"none")+';transition:background .15s;">'+o(t(u))+"</button>"}function m(){var l=r();if(l){if(!n){l.style.display="none";return}var u=s();l.style.display="flex",l.innerHTML=d("invoice","ocr-mode-invoice",u==="invoice")+d("thai_id_card","ocr-mode-id-card",u==="thai_id_card")}}function p(l){try{localStorage.setItem(e,l==="thai_id_card"?"thai_id_card":"invoice")}catch{}m();try{document.dispatchEvent(new CustomEvent("ocr-doc-mode-change",{detail:{mode:window.getOcrDocumentMode()}}))}catch{}}async function f(l){if(!(a&&!l)){var u=localStorage.getItem("mrpilot_token");if(u)try{var v=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+u}});if(!v.ok)return;var w=await v.json(),b=w&&w.items||[];n=b.some(function(g){return g&&(g.adapter||"").toLowerCase()==="mrerp_dms"&&g.enabled!==!1}),a=!0,window._dmsHasEndpoint=n,m()}catch{}}}window._refreshOcrDocMode=function(){f(!0)},document.addEventListener("click",function(l){var u=l.target.closest(".ocr-doc-seg");u&&u.getAttribute("data-doc-mode")&&(l.preventDefault(),p(u.getAttribute("data-doc-mode")))}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("ocr-doc-mode",m);function c(){r(),m(),f(!1)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),window.addEventListener("hashchange",function(){((location.hash||"").indexOf("ocr")>=0||location.hash===""||location.hash==="#home")&&setTimeout(function(){r(),f(!1)},60)})})();(function(){function e(i){return typeof escapeHtml=="function"?escapeHtml(i==null?"":String(i)):String(i??"")}function n(){var i=(function(){var d=document.getElementById("drop-zone");return d?d.closest(".card"):null})();if(!i||!i.parentNode)return null;var r=document.getElementById("dms-id-card-result");return r||(r=document.createElement("div"),r.id="dms-id-card-result",r.className="card",r.style.cssText="display:none;margin-top:16px;",i.parentNode.insertBefore(r,i.nextSibling),r)}function a(i,r){return'<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);"><span style="color:var(--muted,#6b6b66);font-size:13px;">'+e(t(i))+'</span><span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">'+e(r||"—")+"</span></div>"}function o(i){if(!i)return"";var r=[i.house_no,i.road,i.subdistrict,i.district,i.province,i.zipcode].filter(function(d){return d});return r.join(" ")||i.address_raw||""}function s(i){var r=i&&i.status||"failed",d,m,p;return r==="success"?(d="#0a7a2c",m="#d6f5e0",p="dms-result-status-success"):r==="needs_review"?(d="#9a6b00",m="#fdf0d0",p="dms-result-status-needs-review"):r==="skipped"?(d="#5d5d57",m="#eee",p="dms-result-status-skipped"):(d="#b3261e",m="#fbe0de",p="dms-result-status-failed"),'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:'+d+";background:"+m+';">'+e(t(p))+"</span>"}window.renderDmsIdCardResult=function(i){var r=n();if(r){i=i||{};var d=i.id_card||{},m=d.address||{},p=i.dms_push||{},f=p.status||(i.ok?"success":"failed"),c="";f==="success"&&(c=a("dms-result-customer",p.customer_id)+a("dms-result-booking",p.booking_no));var l=f==="failed"||f==="needs_review"?'<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">'+e(t("dms-result-retry"))+"</button>":"",u="";if(f==="failed"&&p.error_code){var v="dms-err-"+String(p.error_code).toLowerCase(),w=t(v);(!w||w===v)&&(w=t("dms-err-err_dms_unexpected")),u='<div style="margin-top:8px;color:#b3261e;font-size:12px;">'+e(w)+"</div>"}r.style.display="",r.innerHTML='<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;"><div class="section-title">'+e(t("dms-result-title"))+"</div>"+s(p)+'</div><div style="margin-top:8px;">'+a("dms-result-name",(d.first_name||"")+" "+(d.last_name||""))+a("dms-result-id",d.people_id_masked)+a("dms-result-birthday",d.birthday_be)+a("dms-result-address",o(m))+c+"</div>"+u+l}},window.clearDmsIdCardResult=function(){var i=document.getElementById("dms-id-card-result");i&&(i.style.display="none",i.innerHTML="")},document.addEventListener("click",function(i){i.target.closest("#dms-id-card-retry")&&(i.preventDefault(),typeof window._dmsRetryIdCard=="function"&&window._dmsRetryIdCard())})})();async function Ua(e){let n;if(e)n=_selectedFiles.find(a=>a.file===e)||{file:e,name:e.name,status:"waiting"};else{const a=_selectedFiles.filter(o=>o.status==="waiting");if(!a.length)return;n=a[0]}window._dmsLastFile=n.file,n.status="processing",typeof renderFileList=="function"&&renderFileList();try{const a=new FormData;a.append("file",n.file,n.name),a.append("push","true");const o=await fetch("/api/dms/id-card-booking",{method:"POST",headers:{Authorization:"Bearer "+token},body:a});if(o.status===401||o.status===403){const i=await o.clone().json().catch(()=>({})),r=i&&i.detail,d=typeof r=="string"?r:r&&r.code||"";if(!d||d.startsWith("auth.")){localStorage.removeItem("mrpilot_token"),showToast(t("alert-session"),"error"),setTimeout(()=>{window.location.href="/"},1200);return}}const s=await o.json().catch(()=>({}));if(!o.ok){n.status="error";const i=s&&s.detail&&(s.detail.code||s.detail)||"unknown";n.errorKey="err."+i,n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:String(i)}});return}n.status=s.ok||s.dms_push&&s.dms_push.status==="needs_review"?"success":"error",typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult(s),typeof updateStartButton=="function"&&updateStartButton()}catch{n.status="error",n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:"network"}})}}window._dmsRetryIdCard=function(){window._dmsLastFile&&Ua(window._dmsLastFile)};document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,(typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice")==="thai_id_card"){try{await Ua()}finally{const c=document.getElementById("btn-start");c&&(c.disabled=!1)}return}if(_userInfo&&_userInfo.plan==="free"){const c=await fetch("/api/health").then(l=>l.json()).catch(()=>null);c&&!c.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const n=_selectedFiles.filter(c=>c.status==="waiting"),a=6;async function o(c,l){if(window._ocrAborted)return c.status="cancelled",c.errorKey=null,renderFileList(),{};c.status=l?"retrying":"processing",c.canRetry=!1,renderFileList();const u=new AbortController,v=setTimeout(()=>u.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(u);try{const w=new FormData;w.append("file",c.file,c.name);try{if(typeof window.getCurrentClientId=="function"){const y=window.getCurrentClientId();y!=null&&w.append("client_id",String(y))}}catch{}const b=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:w,signal:u.signal});if(clearTimeout(v),window._ocrCtrls.delete(u),b.status===401||b.status===403){const x=await b.clone().json().catch(()=>({})),E=x&&x.detail,_=typeof E=="string"?E:E&&E.code||"";if(!_||_.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),_==="auth.session_revoked")_showSessionRevokedModal();else{const k=_==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(k),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}_==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!b.ok){const x=(await b.json().catch(()=>({}))).detail;return typeof x=="string"?(c.errorKey="err."+x,c.errorParams=null):x&&x.code?(c.errorKey="err."+x.code,c.errorParams={...x,mb:_quota.max_file_size_mb}):(c.errorKey="err.unknown",c.errorParams=null),(c.errorKey==="err.unknown"||c.errorKey==="err.ocr.engine_error")&&(b.status===429?c.errorKey="err.rate_limit":b.status===502||b.status===503||b.status===504?c.errorKey="err.gemini_overloaded":b.status>=500&&(c.errorKey="err.server")),c.status="error",c.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(c.errorKey||""),renderFileList(),{}}const g=await b.json();c.status="success",c.fromCache=!!g.from_cache;const h=mergeFields(g.pages),I=g.confidence||(h.items&&h.items.length>0?"high":"low");if(_results.push({filename:g.filename,pages:g.pages,page_count:g.page_count,elapsed_ms:g.elapsed_ms,engine:g.engine,merged_fields:h,edits:{},confidence:I,history_id:g.history_id,history_ids:g.history_ids||[],invoice_count:g.invoice_count||1,invoices:g.invoices||[],archive_name:g.archive_name||null,category_tag:g.category_tag||null,auto_pushed:!!g.auto_pushed,typhoon_enhanced:!!g.typhoon_enhanced,typhoon_pages:g.typhoon_pages||[],from_cache:!!g.from_cache}),g.invoice_count&&g.invoice_count>1&&showToast(t("multi-invoice-toast",{file:g.filename,n:g.invoice_count}),"success"),g.missed_invoice_warnings&&g.missed_invoice_warnings.length){const y=g.missed_invoice_warnings.map(function(x){return x.page}).filter(function(x){return x!=null});showToast(t("missed-invoice-warn",{file:g.filename,pages:y.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",g.missed_invoice_warnings)}if(g.typhoon_enhanced&&g.typhoon_pages&&g.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:g.filename,n:g.typhoon_pages.length}),"success"),g.fallback_used){const y=g.engine_chain||[],x=g.engine||"";let E;x==="typhoon_nvidia"?E="fallback-typhoon-nvidia-toast":x==="easyocr"?E="fallback-easyocr-toast":E="fallback-generic-toast",showToast(t(E,{file:g.filename}),"warn"),console.info("[OCR Chain]",y)}if(g.from_cache&&showToast(t("cache-hit-toast",{file:g.filename}),"info"),g.duplicate_warnings&&g.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const y of g.duplicate_warnings)window._dupQueue.push({filename:g.filename,...y})}return g.auto_pushed&&showToast(t("auto-push-fired",{file:g.filename}),"info"),g.quota&&g.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=g.quota.used_this_month,_userInfo.tenant_used=g.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(w){clearTimeout(v);try{window._ocrCtrls&&window._ocrCtrls.delete(u)}catch{}console.error("[Upload] failed for",c.file.name,w);const b=w&&(w.name==="AbortError"||w==="timeout"),g=b&&(u.signal.reason==="timeout"||w==="timeout"),h=w&&w.message&&/NetworkError|Failed to fetch/i.test(w.message);return b&&(u.signal.reason==="user_stop"||window._ocrAborted)?(c.status="cancelled",c.errorKey=null,c.canRetry=!1,renderFileList(),{}):(g?c.errorKey="err.timeout":b?c.errorKey="err.aborted":h?c.errorKey="err.network":(c.errorKey="err.unknown",c.errorParams={msg:w&&w.message?w.message:String(w)}),c.status="error",!l&&!window._ocrAborted&&(h||g)&&navigator.onLine!==!1&&(c.canRetry=!0,renderFileList(),await new Promise(y=>setTimeout(y,2e3)),c.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?o(c,!0):(c.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=o;let s=0,i=!1;async function r(){for(;s<n.length&&!i&&!window._ocrAborted;){const c=s++,l=await o(n[c]);if(l&&l.abort){i=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const d=document.getElementById("btn-start"),m=document.getElementById("btn-stop");d&&(d.style.display="none"),m&&(m.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(n)}catch{}const p=[];for(let c=0;c<Math.min(a,n.length);c++)p.push(r());await Promise.all(p);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}d&&(d.style.display=""),m&&(m.style.display="none");const f=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const c={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const u of n)if(u.status==="success")c.success++;else if(u.status==="cancelled")c.cancelled++;else if(u.status==="error"){const v=u.errorKey||"";v==="err.network"?c.network++:v==="err.timeout"||v==="err.aborted"?c.timeout++:v.indexOf("quota")>=0||v==="err.monthly_limit_exceeded"?c.quota++:v==="err.gemini_overloaded"||v==="err.server"?c.overloaded++:v==="err.rate_limit"?c.rate++:c.other++}const l=n.length;f?showToast(Vs(c,l),"warn",4e3):l>1&&c.network+c.timeout+c.quota+c.overloaded+c.rate+c.other>0&&showToast(Us(c),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function Vs(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function Us(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});function Ga(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=u=>u!=null?Number(u).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",d=u=>u||"—",m=u=>{try{const v=new Date(u);return`${v.getFullYear()}-${String(v.getMonth()+1).padStart(2,"0")}-${String(v.getDate()).padStart(2,"0")}`}catch{return u}},p=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",f=(e.matched_fields||[]).map(u=>{const v=t("dup-field-"+u.replace("_","-"))||u;return`<span class="dup-field-chip">${escapeHtml(v)}</span>`}).join(" "),c=document.createElement("div");c.className="log-detail-modal",c.innerHTML=`
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
                <div class="dup-matched-label">${escapeHtml(t("dup-matched-on"))} ${f}</div>
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
                        <tr><td>${escapeHtml(t("dup-field-invoice-date"))}</td><td>${escapeHtml(d(e.current.invoice_date))}</td><td>${escapeHtml(d(e.match.invoice_date))}</td></tr>
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
    `,document.body.appendChild(c);const l=()=>{c.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(Ga,200)};c.querySelector(".dup-close").addEventListener("click",l),c.querySelector('[data-action="view"]').addEventListener("click",()=>{const u=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(u)},400),l()}),c.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const u=e.new_history_id;if(!u){l();return}try{(await fetch(`/api/history/${encodeURIComponent(u)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}l()}),c.querySelector('[data-action="keep"]').addEventListener("click",l)}window.showDuplicateDialog=Ga;function Ye(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function bt(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function Gs(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ye("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ye("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ye("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ye("time-day-ago-suffix"," 天前")}catch{return""}}async function Tn(){Ka();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const d={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[m,p,f]=await Promise.all([fetch("/api/me/tenant-usage",{headers:d}).then(b=>b.ok?b.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:d}).then(b=>b.ok?b.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:d}).then(b=>b.ok?b.json():null).catch(()=>null)]),c=m&&m.ocr_this_month||0;let l=0;const u=p&&(p.items||p.history||p)||[],v=Array.isArray(u)?u:[];v.forEach(b=>{(b.status==="pending"||b.status==="reviewing")&&l++});const w=f&&(f.total||f.count||f.pending||0)||0;if(e&&(e.textContent=bt(c)),n&&(n.textContent=bt(l)),a&&(a.textContent=bt(w)),r&&(w>0?(r.style.display="",r.textContent=w):r.style.display="none"),o&&m){const b=m.ocr_this_month||0,g=m.quota||0;o.textContent=bt(b),s&&(s.textContent=g?b+" / "+bt(g)+" 张":Ye("dash-kpi-plan-sub","本月用量"))}if(i)if(v.length===0)i.innerHTML='<div class="dash-recent-empty">'+Ye("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const b=v.slice(0,5).map(g=>{const h=(g.invoice_no||g.filename||g.id||"").toString(),I=(g.supplier_name||g.buyer_name||g.client_name||g.notes||"").toString(),y=Gs(g.created_at||g.upload_time||g.date),x=E=>String(E).replace(/[&<>"']/g,_=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[_]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+x(h)+'">'+x(h)+'</span><span class="dash-recent-mid" title="'+x(I)+'">'+x(I)+'</span><span class="dash-recent-time">'+x(y)+"</span></div>"}).join("");i.innerHTML=b}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+Ye("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Tn;async function Ka(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},d=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!d.ok){e.style.display="none",s&&(s.textContent="—"),i&&(i.textContent="");return}const m=await d.json(),p=!!m.is_owner,f=!!m.is_billing_exempt;if(!p)e.style.display="none";else if(e.style.display="",f)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const l=typeof m.balance_thb=="number"?m.balance_thb:0;if(a&&(a.textContent="฿"+l.toFixed(2),a.className=l<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const u=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",v=l<50?"#dc2626":"#6b7280",w=b=>typeof window.escapeHtml=="function"?window.escapeHtml(b):String(b).replace(/[&<>"']/g,g=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[g]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+v+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+w(u)+"</a>"}}const c=typeof m.pages_this_month=="number"?m.pages_this_month:typeof m.my_invoice_count=="number"?m.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(c)),i){const l=c>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",u=typeof window.t=="function"?window.t(l,{used:c}):c+" pages";i.textContent=u}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=Ka;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Tn,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Tn()});function de(e){return(typeof window.t=="function"?window.t(e):null)||e}function Mn(){return localStorage.getItem("mrpilot_token")||""}function le(e){return document.getElementById(e)}var zt=null,Et=null;function Ja(){Et||(Et=setInterval(function(){if(!document.hidden){var e=Mn();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;zt!==null&&a>zt&&(window.showToast&&window.showToast(de("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),zt=a}}).catch(function(){}))}},3e4))}function Ks(){Et&&(clearInterval(Et),Et=null),zt=null}window._startCreditsPoll=Ja;window._stopCreditsPoll=Ks;Ja();var $n=null,Hn=0;function Js(){if(!le("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),Ws()}}function Wa(){var e=function(n,a){var o=le(n);o&&(o.textContent=a)};e("tv2-title",de("topup-title")),e("tv2-sl1",de("topup-step1")),e("tv2-sl2",de("topup-step2")),e("tv2-sl3",de("topup-step3")),e("tv2-al",de("topup-amount-label")),e("tv2-bl",de("topup-bank-label")),e("tv2-copy",de("topup-copy-account")),e("tv2-dt",de("topup-slip-drop")),e("tv2-pl",de("topup-payer-label")),e("tv2-nl",de("topup-note-label"))}function $t(e){[1,2,3].forEach(function(s){var i=le("tv2-s"+s);i&&(i.style.display=s===e?"":"none");var r=le("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=le("tv2-back"),a=le("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=de("topup-btn-cancel")):n&&(n.style.display="",n.textContent=de("topup-btn-back")),a&&(a.textContent=de(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=le("tv2-bn");o&&(o.innerHTML=de("topup-bank-note").replace("{amount}","<strong>฿"+Number(Hn).toLocaleString()+"</strong>"))}}function yn(){for(var e=1;e<=3;e++){var n=le("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function Ut(e){var n=le(e);n&&(n.textContent="",n.style.display="none")}function Bt(e,n){var a=le(e);a&&(a.textContent=n,a.style.display="")}function aa(e){var n=le("tv2-dt");n&&(n.textContent=e.name);var a=le("tv2-drop");a&&a.classList.add("has-file"),Ut("tv2-se")}function Ws(){var e=le("topup-v2-ov");le("tv2-close").addEventListener("click",wt),e.addEventListener("click",function(i){i.target===e&&wt()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&wt()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(m){m.classList.remove("active")}),r.classList.add("active");var d=le("tv2-amt");d&&(d.value=r.dataset.val,Ut("tv2-ae"))}});var n=le("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),Ut("tv2-ae")});var a=le("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=de("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var o=le("tv2-drop"),s=le("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(i){i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(i){i.preventDefault(),o.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&aa(r)})),s&&s.addEventListener("change",function(){s.files[0]&&aa(s.files[0])}),le("tv2-back").addEventListener("click",function(){var i=yn();if(i<=1){wt();return}$t(i-1)}),le("tv2-next").addEventListener("click",function(){var i=yn();i===1?Ys():i===2?$t(3):Xs()})}async function Ys(){var e=le("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){Bt("tv2-ae",de("topup-amount-invalid"));return}if(n>5e5){Bt("tv2-ae",de("topup-amount-too-large"));return}Hn=n;var a=le("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+Mn()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),i=de("topup-submit-fail");try{var r=JSON.parse(s),d=r.detail;if(Array.isArray(d)&&d.length){var m=d[0]&&d[0].type||"";m.indexOf("less_than")>=0?i=de("topup-amount-too-large"):(m.indexOf("greater_than")>=0||m.indexOf("parsing")>=0)&&(i=de("topup-amount-invalid"))}else typeof d=="string"&&(i=d)}catch{}throw new Error(i)}var p=await o.json();$n=p.request_id,$t(2)}catch(f){Bt("tv2-ae",f.message||de("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=de("topup-btn-next"))}}async function Xs(){var e=le("tv2-file");if(!e||!e.files||!e.files[0]){Bt("tv2-se",de("topup-slip-required"));return}var n=le("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=le("tv2-payer"),s=le("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+$n,{method:"POST",headers:{Authorization:"Bearer "+Mn()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(de("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(de("topup-pending"),"info"),wt()}catch(d){Bt("tv2-ue",de("topup-upload-fail")+" · "+d.message),n&&(n.disabled=!1,n.textContent=de("topup-btn-submit"))}}function wt(){var e=le("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){Js(),$n=null,Hn=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=le(a);o&&(o.value="")});var e=le("tv2-file");e&&(e.value="");var n=le("tv2-drop");n&&n.classList.remove("has-file","drag-over"),le("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){Ut(a)}),Wa(),$t(1),le("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=le("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(Wa(),$t(yn()))});const Zs=`
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

    `;ke("page-test-center",Zs);(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",i=!1,r=!1;function d(H,T,D){let O=typeof t=="function"?t(H):null;return(!O||O===H)&&(O=T),D&&Object.keys(D).forEach(function(P){O=String(O).replace("{"+P+"}",String(D[P]))}),O}function m(){try{const H=localStorage.getItem(n);o=H?JSON.parse(H):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function p(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function f(H){const T=new Date(H),D=function(O){return O<10?"0"+O:""+O};return D(T.getHours())+":"+D(T.getMinutes())+":"+D(T.getSeconds())}function c(H){return String(H??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function l(H,T){try{typeof showToast=="function"?showToast(H,T||"info"):alert(H)}catch{}}function u(H){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(H).then(function(){l(d("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){v(H)}):v(H)}catch{v(H)}}function v(H){try{const T=document.createElement("textarea");T.value=H,T.style.position="fixed",T.style.opacity="0",document.body.appendChild(T),T.select();const D=document.execCommand("copy");document.body.removeChild(T),l(D?d("tc-toast-copied","已复制"):d("tc-toast-copy-fail","复制失败"),D?"success":"error")}catch{l(d("tc-toast-copy-fail","复制失败"),"error")}}function w(){const H=document.getElementById("tc-account-chip"),T=document.getElementById("tc-progress-chip");if(H&&(H.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),T){const D=a.length,O=a.filter(function(P){return o[P.id]}).length;T.textContent=O+" / "+D}}function b(){const H=document.getElementById("tc-checklist-body");if(!H)return;const T={};a.forEach(function(O){T[O.group]||(T[O.group]=[]),T[O.group].push(O)});const D=[];Object.keys(T).forEach(function(O){D.push('<div class="tc-checklist-group">'),D.push('<div class="tc-checklist-group-title">'+c(O)+"</div>"),T[O].forEach(function(P){const j=o[P.id]||"",N=j?"is-"+j:"";D.push('<div class="tc-check-item '+N+'" data-id="'+c(P.id)+'"><div class="tc-check-id">'+c(P.id)+'</div><div class="tc-check-desc">'+c(P.desc)+'</div><div class="tc-check-actions">'+g(P.id,"pass",j)+g(P.id,"fail",j)+g(P.id,"skip",j)+"</div></div>")}),D.push("</div>")}),H.innerHTML=D.join("")}function g(H,T,D){const O=D===T,P={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},j={pass:d("tc-status-pass","通过"),fail:d("tc-status-fail","失败"),skip:d("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(O?"is-active "+T:"")+'" data-id="'+c(H)+'" data-kind="'+T+'" title="'+c(j[T])+'">'+P[T]+"</button>"}function h(H){return s==="all"?!0:s==="js_error"?H.type==="js_error"||H.type==="promise_error":s==="api"?H.type==="api_error"||H.type==="api_fail":s==="api_slow"?H.type==="api_slow":s==="console"?H.type==="console_error"||H.type==="console_warn":!0}function I(){const H=document.getElementById("tc-logs-body"),T=document.getElementById("tc-logs-count");if(!H)return;const D=(window._pearnlyTcLogs||[]).slice().reverse(),O=D.filter(h);if(T&&(T.textContent=String(D.length)),O.length===0){H.innerHTML='<div class="tc-logs-empty">'+c(d("tc-logs-empty","暂无异常"))+"</div>";return}const P=O.slice(0,100).map(function(j){const N=typeof j.detail=="object"?JSON.stringify(j.detail,null,2):String(j.detail||"");return'<div class="tc-log-item t-'+c(j.type)+'" data-ts="'+j.ts+'"><span class="tc-log-time">'+f(j.ts)+'</span><span class="tc-log-type">'+c(j.type)+'</span><div class="tc-log-summary">'+c(j.summary)+'<div class="tc-log-detail">'+c(N)+"</div></div></div>"}).join("");H.innerHTML=P,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(j){j.classList.toggle("active",j.getAttribute("data-filter")===s)})}function y(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&I(),x()},200))}window._tcOnNewLog=y;function x(){const H=document.getElementById("nav-test-badge");if(!H)return;const T=(window._pearnlyTcLogs||[]).filter(function(D){return D.type==="js_error"||D.type==="promise_error"||D.type==="api_error"||D.type==="api_fail"||D.type==="console_error"}).length;T>0?(H.style.display="",H.textContent=T>99?"99+":String(T)):H.style.display="none"}function E(){w(),b(),I(),x()}function _(){const H=[],T=new Date,D=_userInfo&&(_userInfo.email||_userInfo.username)||"—";H.push("# Pearnly "+e+" 测试结果"),H.push("- 账号:"+D),H.push("- 时间:"+T.toISOString().replace("T"," ").slice(0,19));const O=a.length,P=a.filter(function(re){return o[re.id]==="pass"}).length,j=a.filter(function(re){return o[re.id]==="fail"}).length,N=a.filter(function(re){return o[re.id]==="skip"}).length,se=O-P-j-N;H.push("- 进度:"+(P+j+N)+" / "+O+" · ✅ "+P+" · ❌ "+j+" · ⏭ "+N+" · 未测 "+se),H.push(""),H.push("| ID | 描述 | 状态 |"),H.push("|---|---|---|"),a.forEach(function(re){const he=o[re.id],be=he==="pass"?"✅":he==="fail"?"❌":he==="skip"?"⏭":"⬜";H.push("| "+re.id+" | "+re.desc.replace(/\|/g,"\\|")+" | "+be+" |")});const ie=a.filter(function(re){return o[re.id]==="fail"});ie.length>0&&(H.push(""),H.push("## ❌ 失败项"),ie.forEach(function(re){H.push("- **"+re.id+"** · "+re.desc)}));const pe=(window._pearnlyTcLogs||[]).slice(-30).reverse();return pe.length>0&&(H.push(""),H.push("## 🔴 异常日志(最近 "+pe.length+" 条)"),pe.forEach(function(re){if(H.push("- `"+f(re.ts)+"` · **"+re.type+"** · "+re.summary),re.detail){let he;try{he=JSON.stringify(re.detail)}catch{he=String(re.detail)}he&&he!=="{}"&&H.push("  - "+he.slice(0,600))}})),H.join(`
`)}function k(H){const T=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(T.length===0)return"(暂无异常日志)";const D=["# Pearnly 异常日志(最近 "+T.length+" 条)"],O=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return D.push("- 账号:"+O),D.push("- 当前页:"+(currentRoute||"?")),D.push("- UA:"+navigator.userAgent),D.push(""),T.forEach(function(P){if(D.push("## `"+f(P.ts)+"` · "+P.type),D.push("- "+P.summary),P.detail){D.push("```");try{D.push(JSON.stringify(P.detail,null,2).slice(0,2e3))}catch{D.push(String(P.detail).slice(0,2e3))}D.push("```")}}),D.join(`
`)}function B(){const H=Date.now();fetch("/api/health").then(function(T){const D=Date.now()-H;T.ok?l(d("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:D}),"success"):l(d("tc-toast-health-fail","后端无响应")+" ("+T.status+")","error")}).catch(function(){l(d("tc-toast-health-fail","后端无响应"),"error")})}function L(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}E(),l(d("tc-toast-cleared","session 状态已清空"),"success")}function C(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(H){return H.json()}).then(function(H){window._clientsCache=H.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),l("客户缓存已刷新 · "+(H.clients||[]).length+" 个客户","success")}).catch(function(){l("刷新失败","error")})}catch{}}function S(){if(i||!document.getElementById("page-test-center"))return;i=!0;const T=document.getElementById("tc-checklist-body");T&&T.addEventListener("click",function(he){const be=he.target.closest(".tc-status-btn");if(!be)return;const A=be.getAttribute("data-id"),G=be.getAttribute("data-kind");!A||!G||(o[A]===G?delete o[A]:o[A]=G,p(),b(),w())});const D=document.getElementById("tc-btn-reset-checklist");D&&D.addEventListener("click",function(){o={},p(),b(),w()});const O=document.getElementById("tc-btn-copy-all");O&&O.addEventListener("click",function(){u(_())});const P=document.getElementById("tc-btn-copy-logs");P&&P.addEventListener("click",function(){u(k())});const j=document.getElementById("tc-btn-clear-logs");j&&j.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,I(),x()});const N=document.getElementById("tc-logs-filter");N&&N.addEventListener("click",function(he){const be=he.target.closest(".tc-filter-chip");be&&(s=be.getAttribute("data-filter")||"all",I())});const se=document.getElementById("tc-logs-body");se&&se.addEventListener("click",function(he){const be=he.target.closest(".tc-log-item");be&&be.classList.toggle("expanded")});const ie=document.getElementById("tc-tool-health");ie&&ie.addEventListener("click",B);const pe=document.getElementById("tc-tool-clear-session");pe&&pe.addEventListener("click",L);const re=document.getElementById("tc-tool-reload-clients");re&&re.addEventListener("click",C)}function M(){}window._tcApplyVisibility=M;let $=0;const q=setInterval(function(){$++,_userInfo&&clearInterval(q),$>60&&clearInterval(q)},500);window.loadTestCenterPage=function(){m(),S(),E()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){x(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&E()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(h,I){if(typeof window.t=="function"){const y=window.t(h);if(y&&y!==h)return y}return I}function o(){const h=window._userInfo||{},I=String(h.role||"").toLowerCase(),y=String(h.tenant_role||"").toLowerCase();return h.is_super_admin===!0||h.is_owner===!0||I==="owner"||I==="admin"||y==="owner"||y==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const h=localStorage.getItem(e);if(!h||h==="null"||h==="0"||h==="")return null;const I=parseInt(h,10);return isNaN(I)?null:I}function r(h){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:h,mode:s()}}))}catch{}}function d(h){const I=i();h==null||h===0?localStorage.removeItem(e):(localStorage.setItem(e,String(h)),localStorage.setItem(n,"client")),String(I)!==String(h)&&r(h)}function m(){const h=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),h!=null&&r(null)}async function p(){try{const h=window.apiGet;if(typeof h!="function")return[];const I=await h("/api/workspace/clients");return I&&(I.clients||I.items)||[]}catch{return[]}}async function f(h){if(s()==="client"&&i()!=null)return typeof h=="function"&&h(),!0;const I=a("ws-need-client","这个功能需要先选择工作空间"),y=a("ws-btn-pick","选择工作空间"),x=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(I,{okText:y,cancelText:x})&&c(h):window.confirm(I+`

[`+y+" / "+x+"]")&&c(h),!1}async function c(h){const I=await p();if(typeof h=="function"&&s()!=="personal"&&I.length===1){d(Number(I[0].id)),h();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:I,canCreate:o(),active:i(),onPersonal:m,onPick:function(y){d(Number(y)),typeof h=="function"&&h()},emptyHint:I.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!I.length){const y=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(y,"info")}}function l(h){const I=h||document.getElementById("workspace-switcher-root");if(!I)return;const y=s(),x=i();let E,_;if(y==="client"&&x!=null){const L=(window._workspaceClientsCache||[]).find(C=>Number(C.id)===Number(x));E=v("building"),_=L?L.name:a("ws-current-label","当前工作空间")}else E=v("user"),_=a("ws-personal","个人事务");I.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+E+'<span class="ws-ctrl-label">'+u(_)+"</span></button>";const k=I.querySelector("#ws-ctrl-btn");k&&k.addEventListener("click",()=>c(null))}function u(h){return String(h??"").replace(/[&<>"']/g,function(I){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[I]})}function v(h){const I='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return h==="building"?I+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':I+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function w(h){h=h||{};const I=h.clients||[],y=h.active,x=document.getElementById("ws-modal");x&&x.remove();const E=document.createElement("div");E.id="ws-modal",E.className="ws-modal";const k='<button type="button" class="ws-modal-item'+(s()==="personal"||y==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+v("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+u(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+u(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let B="";if(I.length){const $=['<option value="">'+u(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(I.map(function(q){const H=y!=null&&Number(y)===Number(q.id);return'<option value="'+u(q.id)+'"'+(H?" selected":"")+">"+u(q.name||"#"+q.id)+"</option>"}));B='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+u(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+$.join("")+"</select></div>"}const L=!I.length&&h.emptyHint?'<div class="ws-modal-empty">'+u(h.emptyHint)+"</div>":"",C=h.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+u(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+u(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+u(a("ws-create-submit","创建"))+"</button></div></div>":"";E.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+u(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+u(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+k+B+"</div>"+L+C+"</div>",document.body.appendChild(E);const S=E.querySelector("[data-ws-select]");S&&S.addEventListener("change",function(){const $=S.value;$&&(typeof h.onPick=="function"&&h.onPick($),M(),l())});function M(){E.remove()}E.addEventListener("click",function($){if($.target===E||$.target.closest("[data-ws-close]")){M();return}if($.target.closest("[data-ws-personal]")){typeof h.onPersonal=="function"&&h.onPersonal(),M(),l();return}const H=$.target.closest("[data-ws-pick]");if(H){const O=H.getAttribute("data-ws-pick");typeof h.onPick=="function"&&h.onPick(O),M(),l();return}if($.target.closest("[data-ws-create-toggle]")){const O=E.querySelector("[data-ws-create-form]");if(O){O.style.display=O.style.display==="none"?"flex":"none";const P=O.querySelector("[data-ws-create-name]");P&&P.focus()}return}if($.target.closest("[data-ws-create-submit]")){b(E,h,M);return}})}async function b(h,I,y){const x=h.querySelector("[data-ws-create-name]"),E=x?(x.value||"").trim():"";if(!E){x&&x.focus();return}let _=null;try{if(typeof window.apiPost=="function"){const B=await window.apiPost("/api/workspace/clients",{name:E});_=B&&typeof B.json=="function"?await B.json().catch(()=>null):B}}catch{_=null}const k=_&&(_.id||_.client&&_.client.id);if(!k){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await p(),d(Number(k)),I.onPick,y(),l()}window.openWorkspaceChooserUI=w,window.addEventListener("pearnly:workspace-changed",function(){l()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=d,window.enterPersonalMode=m,window.requireWorkspace=f,window.openWorkspaceChooser=c,window.renderWorkspaceControl=l,window.fetchWorkspaceClients=p;function g(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){c(null)},800)}catch{}}p().then(h=>{window._workspaceClientsCache=h,l(),g()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",l)})();(function(){const e=y=>document.querySelector('[data-num-target="'+y+'"]');function n(y){if(!y)return t("reconcile-last-activity-none");try{const x=new Date(y),E=new Date,_=E-x;if(_/6e4<5)return t("reconcile-last-activity-just-now");if(x.toDateString()===E.toDateString())return t("reconcile-last-activity-today");const B=Math.max(1,Math.floor(_/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",B)}catch{return t("reconcile-last-activity-none")}}function a(y,x,E){const _=e(y);_&&(_.textContent=E?"-":String(x),_.classList.toggle("is-empty",!!E))}function o(y){const x=document.getElementById("reconcile-error");x&&(x.style.display=y?"flex":"none")}function s(y){const x=document.getElementById("reconcile-empty");x&&(x.style.display=y?"flex":"none")}function i(y,x){const E=document.getElementById("reconcile-last-activity");E&&(E.textContent=y,E.classList.toggle("has-data",!!x))}function r(y){const x=!y||(y.total_sessions||0)===0;a("pending",y.pending||0,x),a("matched",y.matched||0,x),a("unmatched",y.unmatched||0,x),i(n(y.last_activity_at),!!y.last_activity_at),o(!1),s(x)}function d(y){const x=y.toUpperCase();return x==="KBANK"?"bank-chip-kbank":x==="SCB"?"bank-chip-scb":x==="BBL"?"bank-chip-bbl":x==="KTB"?"bank-chip-ktb":x==="TTB"?"bank-chip-ttb":"bank-chip-other"}function m(y,x){const E=_=>_?String(_).slice(0,10):"?";return!y&&!x?"":E(y)+" ~ "+E(x)}function p(y){return y==null?"":String(y).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function f(y){const x=document.getElementById("reconcile-recent"),E=document.getElementById("reconcile-recent-list");if(!x||!E)return;const _=(y||[]).slice(0,20);if(_.length===0){x.style.display="none";return}x.style.display="",s(!1),E.innerHTML=_.map(k=>{const B=k.parse_status==="parse_failed",L=k.bank_code||"OTHER",C=k.account_last4?" ···"+p(k.account_last4):"",S=m(k.period_start,k.period_end),M=p(k.source_filename||""),$=Number(k.tx_count||0),q=B?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",$)+"</span>";return'<div class="recon-card" data-session-id="'+p(k.id)+'" data-session-name="'+M+'"><span class="bank-chip '+d(L)+'">'+p(L)+'</span><div class="recon-card-main"><div class="recon-card-title">'+M+C+'</div><div class="recon-card-sub">'+p(S)+'</div></div><div class="recon-card-right">'+q+'</div><button class="recon-card-trash" data-trash="'+p(k.id)+'" title="'+p(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),E.querySelectorAll(".recon-card").forEach(k=>{k.addEventListener("click",B=>{B.target.closest(".recon-card-trash")||(k.dataset.sessionId,c())})}),E.querySelectorAll(".recon-card-trash").forEach(k=>{k.addEventListener("click",B=>{B.stopPropagation();const L=k.dataset.trash,C=k.closest(".recon-card"),S=C&&C.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(L,S)})})}function c(y){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const x=document.querySelector('[data-recon-tab="bank"]');x&&x.click()},150)}function l(){o(!0),s(!1)}function u(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const y=document.querySelector('[data-recon-tab="bank"]');y&&y.click()},150)}async function v(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),o(!1),s(!1);const y=document.getElementById("reconcile-recent");y&&(y.style.display="none");const x={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[E,_]=await Promise.all([fetch("/api/bank-recon/stats",{headers:x}),fetch("/api/bank-recon/sessions?limit=20",{headers:x})]);if(!E.ok)throw new Error("http "+E.status);const k=await E.json(),B=_.ok?await _.json():[];r(k||{}),f(B||[])}catch(E){console.warn("[reconcile] load failed",E),l()}}function w(y){if(!y||!y.length)return;const x="Bearer "+(localStorage.getItem("mrpilot_token")||"");let E=0;const _=y.length;Array.from(y).forEach(function(k){const B=new FormData;B.append("file",k,k.name);const L=new XMLHttpRequest;L.open("POST","/api/bank-recon/upload"),L.setRequestHeader("Authorization",x),L.onload=function(){E++;try{const C=JSON.parse(L.responseText);L.status===200&&C.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",C.tx_count),"success"):showToast(k.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(k.name+" "+(t("upload-failed")||"上传失败"),"error")}E===_&&setTimeout(v,600)},L.onerror=function(){E++,showToast(k.name+" "+(t("upload-failed")||"上传失败"),"error"),E===_&&setTimeout(v,600)},L.send(B)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function b(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const y=document.getElementById("reconcile-bank-file-input");y&&y.addEventListener("change",function(){w(this.files),this.value=""}),document.addEventListener("click",x=>{if(x.target.closest("#btn-reconcile-upload-top")||x.target.closest("#btn-reconcile-upload-empty")){u();return}if(x.target.closest("#btn-reconcile-retry")){v();return}if(x.target.closest("#btn-reconcile-dev-seed")){I();return}})}const g=["468b50c1-5593-4fd6-990d-515ce8085563"];function h(){const y=document.getElementById("btn-reconcile-dev-seed");if(!y)return;const x=typeof _userInfo<"u"?_userInfo:null,E=x&&x.id&&g.indexOf(String(x.id))>=0;y.style.display=E?"":"none"}async function I(){try{const y=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!y.ok)throw new Error("seed:"+y.status);const x=await y.json(),E=(t("reconcile-dev-seed-ok")||"").replace("{n}",x.tx_count||0);showToast(E,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const _=document.querySelector('[data-auto-tab="bank"]');_&&_.click(),x.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(x.session_id)},300)}catch(y){console.warn("[reconcile] dev seed failed",y),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){b(),h(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await v()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&v().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const v=a();if(v){if(!e.clients.length){v.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}v.innerHTML=e.clients.map(w=>{const b=String(w.id),g=e.selected.has(b)?"checked":"",h=escapeHtml(w.name||w.label||"#"+b),I=w.code?'<span class="assign-row-code">'+escapeHtml(w.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(b)+'" '+g+'><span class="assign-row-name">'+h+"</span>"+I+"</label>"}).join(""),d()}}function d(){const v=s();if(v){const b=t("assign-selected-count")||"已选 {n} / {total}";v.textContent=b.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const w=o();w&&(w.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function m(){const v=i();v&&(v.textContent=e.employeeName?" · "+e.employeeName:"")}async function p(v,w){e.employeeId=v,e.employeeName=w||"",e.opened=!0,e.selected=new Set,e.clients=[],m();const b=a();b&&(b.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const g=n();g&&(g.style.display="flex");try{const[h,I]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(v)+"/assignments")]);e.clients=h&&h.clients||[];const y=I&&I.client_ids||[];e.selected=new Set(y.map(String)),r()}catch(h){console.error("[assign-clients] load failed",h);const I=a();I&&(I.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function f(){e.opened=!1;const v=n();v&&(v.style.display="none")}async function c(){if(!e.employeeId)return;const v=Array.from(e.selected).map(b=>parseInt(b,10)).filter(b=>!isNaN(b)),w=document.getElementById("assign-modal-save");w&&(w.disabled=!0);try{const b=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:v});b&&b.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",v.length),"success"),f(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(b){console.error("[assign-clients] save failed",b),showToast(t("assign-save-failed")||"保存失败","error")}finally{w&&(w.disabled=!1)}}function l(){const v=n();if(!v||v.dataset.bound==="1")return;v.dataset.bound="1";const w=document.getElementById("assign-modal-close");w&&w.addEventListener("click",f);const b=document.getElementById("assign-modal-cancel");b&&b.addEventListener("click",f);const g=document.getElementById("assign-modal-save");g&&g.addEventListener("click",c),v.addEventListener("click",function(y){y.target===v&&f()});const h=o();h&&h.addEventListener("change",function(){h.checked?e.selected=new Set(e.clients.map(y=>String(y.id))):e.selected=new Set,r()});const I=a();I&&I.addEventListener("change",function(y){const x=y.target.closest('input[type="checkbox"][data-cid]');if(!x)return;const E=x.dataset.cid;x.checked?e.selected.add(E):e.selected.delete(E),d()})}function u(){e.opened&&(m(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",u),window.openAssignClientsModal=function(v,w){l(),p(v,w)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(f){if(!f)return"";try{return new Date(f).toLocaleString()}catch{return f}}function a(f){const c=document.getElementById("access-log-table");c&&(c.innerHTML='<div class="access-log-empty">'+escapeHtml(f)+"</div>");const l=document.getElementById("access-log-pager");l&&(l.innerHTML="")}function o(){const f=document.getElementById("access-log-table");if(!f)return;const c=e.rows||[];if(!c.length){a(t("set-access-log-empty"));return}const l=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,u=c.map(function(v){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(v.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(v.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(v.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(v.target_name||v.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(v.ip||"-")}</div>
                </div>`}).join("");f.innerHTML=l+u}function s(){const f=document.getElementById("access-log-pager");if(!f)return;const c=e.total||0;if(!c){f.innerHTML="";return}const l=e.page||1,u=e.per_page,v=Math.max(1,Math.ceil(c/u)),w=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",c),b=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",l).replace("{t}",v);f.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(w)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${l-1}" ${l<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(b)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${l+1}" ${l>=v?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(f){const c=localStorage.getItem("mrpilot_token");if(c){e.page=f||1,a(t("set-access-log-loading"));try{const l="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),u=await fetch(l,{headers:{Authorization:"Bearer "+c}});if(u.status===403){a(t("set-access-log-empty"));return}if(!u.ok)throw new Error("http_"+u.status);const v=await u.json();e.rows=v.logs||[],e.total=v.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const f=localStorage.getItem("mrpilot_token");if(f)try{const c="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),l=await fetch(c,{headers:{Authorization:"Bearer "+f}});if(!l.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const u=await l.blob(),v=document.createElement("a"),w=URL.createObjectURL(u);v.href=w,v.download="pearnly_access_log.csv",document.body.appendChild(v),v.click(),setTimeout(function(){URL.revokeObjectURL(w),v.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function d(){const f=document.querySelectorAll(".set-tab-owner-only"),c=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));f.forEach(function(l){l.style.display=c?"":"none"})}document.addEventListener("click",function(f){if(f.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(f.target.closest("#access-log-csv-btn")){f.preventDefault(),r();return}const u=f.target.closest(".access-log-pager-btn[data-access-log-page]");if(u&&!u.disabled){const v=parseInt(u.dataset.accessLogPage,10);i(v)}}),document.addEventListener("input",function(f){f.target&&f.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(f.target.value||"").trim(),i(1)},350))});let m=0;const p=setInterval(function(){m++,_userInfo&&(d(),clearInterval(p)),m>60&&clearInterval(p)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){d(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=E=>document.getElementById(E);async function n(E,_){return await fetch(E,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(_||{})})}async function a(E){return await fetch(E,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function i(E,_){if(!E)return;E.style.display="",E.className="notif-line-check "+(_?"bound":"unbound");const k=_?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';E.innerHTML=k+"<span>"+escapeHtml(t(_?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(E){if(E==null)return"-";const _=Number(E);return isNaN(_)?String(E):"฿ "+_.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function d(E){if(!E)return"-";try{const _=new Date(E),k=(_.getMonth()+1).toString().padStart(2,"0"),B=_.getDate().toString().padStart(2,"0"),L=_.getHours().toString().padStart(2,"0"),C=_.getMinutes().toString().padStart(2,"0");return`${k}-${B} ${L}:${C}`}catch{return E}}function m(E){const _=e("notif-rules-list"),k=e("notif-rules-empty"),B=e("notif-rules-count");if(!(!_||!k)){if(B.textContent=String(E.length),B.className="auto-status-pill "+(E.length>0?"active":"none"),!E.length){k.style.display="",_.style.display="none",_.innerHTML="";return}k.style.display="none",_.style.display="",_.innerHTML=E.map(L=>{const C=L.template_code==="large_invoice",S=C?"notif-rule-large-tag":"notif-rule-exception-tag",M=C?"large":"";let $=[];if(C){const H=L.params&&L.params.threshold?r(L.params.threshold):"-";$.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+H)}L.enabled||$.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const q=$.length?$.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${L.enabled?"":" disabled"}" data-rule-id="${L.id}">
                    <span class="notif-rule-tmpl-badge ${M}">${escapeHtml(t(S))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(L.name)}</div>
                        <div class="notif-rule-meta">${q}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${L.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function p(E){const _=e("notif-logs-list");if(_){if(!E.length){_.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}_.innerHTML=E.map(k=>{const B=k.status==="sent",L=k.event_type==="exception_high"?"notif-event-exception-high":k.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",C=B?"":" · "+escapeHtml(k.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${B?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(L))}</div>
                        <div class="notif-log-meta">${escapeHtml(k.template_code||"-")}${C}</div>
                    </div>
                    <div class="notif-log-time">${d(k.sent_at)}</div>
                </div>`}).join("")}}async function f(){try{const E=await apiGet("/api/notifications/rules");c=E&&E.items||[],m(c)}catch(E){console.warn("load rules fail",E)}try{const E=await apiGet("/api/notifications/logs?limit=20");l=E&&E.items||[],p(l)}catch(E){console.warn("load logs fail",E)}}let c=null,l=null;function u(){c&&m(c),l&&p(l);const E=e("notif-new-modal");E&&E.style.display!=="none"&&o&&i(e("notif-line-check"),!!(o&&o.bound))}function v(){const E=e("notif-new-modal");E&&(E.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(_=>_.checked=!1),s().then(_=>i(e("notif-line-check"),!!(_&&_.bound))))}function w(){const E=e("notif-new-modal");E&&(E.style.display="none")}function b(){const E=document.querySelector('input[name="notif-template"]:checked'),_=e("notif-new-threshold-row");if(!E){_.style.display="none";return}_.style.display=E.value==="large_invoice"?"":"none";const k=e("notif-new-name");k&&!k.value.trim()&&(k.value=E.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function g(){const E=document.querySelector('input[name="notif-template"]:checked');if(!E){showToast(t("notif-new-template"),"error");return}const _=(e("notif-new-name").value||"").trim();if(!_){showToast(t("notif-name-required"),"error");return}const k={name:_,template_code:E.value,params:{},enabled:!0};if(E.value==="large_invoice"){const B=parseFloat(e("notif-new-threshold").value||"0");if(!B||B<=0){showToast(t("notif-threshold-required"),"error");return}k.params.threshold=B}try{const B=await apiPost("/api/notifications/rules",k);if(B&&B.ok)showToast(t("notif-toast-created"),"success"),w(),f();else{const L=await(B&&B.json&&B.json().catch(()=>({})))||{};showToast(L&&L.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function h(E,_,k){if(E==="toggle"){const B=k.classList.contains("on"),L=await n("/api/notifications/rules/"+_,{enabled:!B});L&&L.ok?(showToast(t(B?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),f()):showToast("toggle failed","error");return}if(E==="test"){const B=await s();if(!B||!B.bound){showToast(t("notif-line-error-bind-first"),"error");return}const L=await apiPost("/api/notifications/rules/"+_+"/test",{});if(L&&L.ok)showToast(t("notif-toast-test-sent"),"success"),f();else{const C=await(L&&L.json&&L.json().catch(()=>({})))||{},S=C&&C.detail||"";showToast(S||t("notif-toast-test-failed"),"error"),f()}return}if(E==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const L=await a("/api/notifications/rules/"+_);L&&L.ok?(showToast(t("notif-toast-deleted"),"success"),f()):showToast("delete failed","error");return}}let I=!1;function y(){if(I)return;I=!0;const E=e("notif-btn-new");E&&E.addEventListener("click",v);const _=e("notif-btn-refresh-logs");_&&_.addEventListener("click",f);const k=e("notif-new-close");k&&k.addEventListener("click",w);const B=e("notif-new-cancel");B&&B.addEventListener("click",w);const L=e("notif-new-save");L&&L.addEventListener("click",g),document.querySelectorAll('input[name="notif-template"]').forEach(M=>{M.addEventListener("change",b)});const C=e("notif-rules-list");C&&C.addEventListener("click",M=>{const $=M.target.closest("button[data-action]");if(!$)return;const q=$.closest("[data-rule-id]");q&&h($.getAttribute("data-action"),q.getAttribute("data-rule-id"),$)});const S=e("notif-new-modal");S&&S.addEventListener("click",M=>{M.target===S&&w()})}async function x(){y(),await f()}window._loadNotificationsPanel=x,window._rerenderNotifications=u})();(function(){function n(g,h){try{return window.t&&window.t(g)||h}catch{return h}}function a(){var g="";try{g=localStorage.getItem("mrpilot_token")||""}catch{}return g?{Authorization:"Bearer "+g}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var g=document.createElement("style");g.id="recon-batch-style",g.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(g)}}function i(g){return g?g.dataset&&g.dataset.taskId?g.dataset.taskId:g.dataset&&g.dataset.taskid?g.dataset.taskid:"":""}function r(g){var h=document.getElementById(g.tbody);if(!h)return null;var I=h.closest("table");if(!I)return null;var y=I.querySelector("thead");if(!y)return null;if(y._reconReady)return y;var x=y.querySelector("tr");if(!x)return null;if(x.classList.add("recon-thead-default"),!x.querySelector(".recon-master-cb")){var E=document.createElement("th");E.className="recon-sel-cell";var _=document.createElement("input");_.type="checkbox",_.className="recon-master-cb",_.setAttribute("aria-label","select all"),_.addEventListener("change",function(){f(g,_.checked)}),E.appendChild(_),x.insertBefore(E,x.firstElementChild)}var k=x.children[1];k&&!k.classList.contains("recon-time-col")&&k.classList.add("recon-time-col");var B=x.children.length,L=document.createElement("tr");L.className="recon-thead-batch";var C=document.createElement("th");C.className="recon-sel-cell";var S=document.createElement("input");S.type="checkbox",S.className="recon-master-cb",S.checked=!0,S.setAttribute("aria-label","select all"),S.addEventListener("change",function(){f(g,S.checked)}),C.appendChild(S);var M=document.createElement("th");return M.setAttribute("colspan",String(B-1)),M.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',L.appendChild(C),L.appendChild(M),y.appendChild(L),M.querySelector("[data-recon-del]").addEventListener("click",function(){v(g)}),M.querySelector("[data-recon-clear]").addEventListener("click",function(){u(g)}),y._reconReady=!0,l(g),y}function d(g){var h=document.getElementById(g.tbody);if(h){var I=h.querySelectorAll("tr");I.forEach(function(y){var x=i(y);if(x&&!y.querySelector(".recon-sel-cb")){var E=y.querySelector("td");if(E){var _=document.createElement("td");_.className="recon-sel-cell";var k=document.createElement("input");k.type="checkbox",k.className="recon-sel-cb",k.dataset.taskId=x,k.dataset.kind=g.kind,k.addEventListener("click",function(L){L.stopPropagation()}),k.addEventListener("change",function(){c(g)}),_.appendChild(k),y.insertBefore(_,E);var B=y.children[1];B&&!B.classList.contains("recon-time-col")&&B.classList.add("recon-time-col")}}}),c(g)}}function m(g){var h=document.getElementById(g.tbody);return h?Array.prototype.slice.call(h.querySelectorAll(".recon-sel-cb")):[]}function p(g){return m(g).filter(function(h){return h.checked}).map(function(h){return h.dataset.taskId})}function f(g,h){m(g).forEach(function(I){I.checked=!!h}),c(g)}function c(g){var h=p(g),I=m(g),y=document.getElementById(g.tbody);if(y){var x=y.closest("table"),E=x&&x.querySelector("thead");if(E){h.length>0?E.classList.add("recon-batch-mode"):E.classList.remove("recon-batch-mode"),E.querySelectorAll(".recon-master-cb").forEach(function(k){if(I.length===0){k.checked=!1,k.indeterminate=!1;return}h.length===I.length?(k.checked=!0,k.indeterminate=!1):h.length===0?(k.checked=!1,k.indeterminate=!1):(k.checked=!1,k.indeterminate=!0)});var _=E.querySelector("[data-recon-count]");_&&(_.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",h.length))}}}function l(g){var h=document.getElementById(g.tbody);if(h){var I=h.closest("table"),y=I&&I.querySelector("thead");if(y){var x=y.querySelector("[data-recon-del-label]"),E=y.querySelector("[data-recon-clear]");x&&(x.textContent=n("recon-batch-delete","批量删除")),E&&(E.textContent=n("recon-batch-clear","取消")),c(g)}}}function u(g){m(g).forEach(function(h){h.checked=!1}),c(g)}async function v(g){var h=p(g);if(h.length){var I=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",h.length),y=!1;try{typeof window.pearnlyConfirm=="function"?y=await window.pearnlyConfirm(I,n("recon-batch-delete-title","批量删除")):y=window.confirm(I)}catch{y=!1}if(y)try{var x=Object.assign({"Content-Type":"application/json"},a()),E=g.kind==="glv"?h.map(function(L){return parseInt(L,10)}):h,_=await fetch(g.api,{method:"POST",headers:x,body:JSON.stringify({ids:E})});if(!_.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var k=await _.json(),B=k&&(k.deleted!=null?k.deleted:k.count)||h.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",B),"success"),g.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function w(g){r(g),d(g);var h=document.getElementById(g.tbody);if(!(!h||h._reconBatchWatched)){h._reconBatchWatched=!0;var I=new MutationObserver(function(){d(g)});I.observe(h,{childList:!0,subtree:!1})}}function b(){s(),o.forEach(w),document.querySelectorAll(".recon-batch-bar").forEach(function(g){try{g.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",b):b(),setTimeout(b,1500),setTimeout(b,4e3),document.addEventListener("keydown",function(g){g.key==="Escape"&&o.forEach(function(h){p(h).length>0&&u(h)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(l)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(p){};function i(p){n=p;for(let l=1;l<=a;l++){const u=document.getElementById("ob-step-"+l);u&&(u.style.display=l===p?"block":"none")}document.querySelectorAll(".ob-dot").forEach(l=>{const u=parseInt(l.dataset.step,10);l.classList.toggle("active",u===p),l.classList.toggle("done",u<p)});const f=document.getElementById("ob-step-label");f&&(f.textContent=p+" / "+a);const c=document.getElementById("ob-next");if(c&&(c.textContent=p===a?t("ob-finish"):t("ob-next")),p===4){const l=document.getElementById("ob-line-input");l&&(l.value=e.line_id||"")}}function r(p){const f=document.querySelector(".onboarding-modal");if(!f)return;let c=f.querySelector(".ob-feedback");c||(c=document.createElement("div"),c.className="ob-feedback",f.appendChild(c)),c.textContent=p,c.classList.add("show"),setTimeout(()=>c.classList.remove("show"),1800)}document.addEventListener("click",p=>{const f=p.target.closest(".ob-option");if(!f)return;const c=f.parentElement;if(!c||!c.classList.contains("ob-options"))return;c.querySelectorAll(".ob-option").forEach(u=>u.classList.remove("selected")),f.classList.add("selected");const l=f.dataset.value;c.id==="ob-role-options"?e.role=l:c.id==="ob-volume-options"?e.monthly_volume=l:c.id==="ob-country-options"&&(e.country=l)}),document.addEventListener("click",p=>{p.target.id==="ob-skip"&&d()}),document.addEventListener("click",p=>{if(p.target.id==="ob-next"){if(n===4){const f=document.getElementById("ob-line-input");e.line_id=(f&&f.value||"").trim().replace(/^@+/,"")}d()}}),document.addEventListener("click",p=>{if(p.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const f=document.getElementById("onboarding-modal");f&&(f.style.display="none")}});function d(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):m()}async function m(){const p=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const f={};if(e.role&&(f.role=e.role),e.monthly_volume&&(f.monthly_volume=e.monthly_volume),e.country&&(f.country=e.country),e.line_id&&(f.line_id=e.line_id),Object.keys(f).length===0){p&&(p.style.display="none");return}try{const c=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(f)});c.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,f),setTimeout(()=>{p&&(p.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(f)),console.warn("onboarding profile save failed",c.status),r(t("ob-fb-saved-local")),setTimeout(()=>{p&&(p.style.display="none")},1500))}catch(c){console.error("onboarding submit",c),localStorage.setItem("pilot_ob_pending",JSON.stringify(f)),p&&(p.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function d(){return"DHL Express (Thailand) Co., Ltd."}function m(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:d(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadArchiveSettings=()=>p();async function p(){const y=!!(_userInfo&&_userInfo.can_customize_archive);o=!y;const x=document.getElementById("archive-upgrade-banner");x&&(x.style.display=y?"none":"");const E=document.getElementById("archive-plus-badge");E&&(E.style.display=y?"none":"");try{const _=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!_.ok)throw new Error("load failed");const k=await _.json();e=Array.isArray(k.name_template)?k.name_template:[],n=k.folder_strategy||"by_month_seller"}catch(_){console.error("load archive settings failed",_),showToast(t("archive-load-failed"),"error");return}f(),c(),l(),u()}function f(){const y=document.getElementById("archive-rule-canvas");if(y){if(e.length===0){y.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}y.innerHTML=e.map((x,E)=>{const _=i[x.type]||{label:x.type},k=s[x.type]||"",B=x.type==="sep"?`"${escapeHtml(x.val||"_")}"`:escapeHtml(t(_.label));return`
                <span class="archive-token ${x.type}"
                      data-token-idx="${E}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${k}</span>
                    <span class="token-label">${B}</span>
                </span>
            `}).join("")}}function c(){const y=document.getElementById("archive-field-palette");if(!y)return;const x=["date","seller","category","amount","invoice","buyer","sep"];y.innerHTML=x.map(E=>{const _=i[E],k=s[E]||"";return`
                <button class="archive-palette-btn ${E}" data-add-field="${E}" ${o?"disabled":""}>
                    <span class="token-icon">${k}</span>
                    <span>${escapeHtml(t(_.label))}</span>
                </button>
            `}).join("")}function l(){document.querySelectorAll('input[name="folder-strategy"]').forEach(y=>{y.checked=y.value===n,y.disabled=o})}async function u(){const y=document.getElementById("archive-preview-name"),x=document.getElementById("archive-preview-hint");if(x&&(x.textContent=t("archive-preview-hint",{category:r()})),!!y){if(e.length===0){y.textContent="-";return}try{const _=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:m().merged_fields,name_template:e})})).json();y.textContent=(_.name||"-")+".pdf"}catch{y.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const y=document.getElementById("archive-rule-modal");!y||y.style.display==="none"||(f(),c(),u())};let v=-1;document.addEventListener("dragstart",y=>{const x=y.target.closest(".archive-token");!x||o||(v=parseInt(x.dataset.tokenIdx,10),x.classList.add("dragging"),y.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",y=>{document.querySelectorAll(".archive-token").forEach(x=>x.classList.remove("dragging","drop-target")),v=-1}),document.addEventListener("dragover",y=>{const x=y.target.closest(".archive-token");x&&(y.preventDefault(),y.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(E=>E.classList.remove("drop-target")),x.classList.add("drop-target"))}),document.addEventListener("drop",y=>{const x=y.target.closest(".archive-token");if(!x||v<0||o)return;y.preventDefault();const E=parseInt(x.dataset.tokenIdx,10);if(E===v)return;const _=e.splice(v,1)[0];e.splice(E,0,_),v=-1,f(),u()}),document.addEventListener("click",y=>{if(y.target.closest("#btn-open-archive-rule")||y.target.closest("#btn-open-archive-rule-from-settings")){const k=document.getElementById("archive-rule-modal");k&&(k.style.display="",p());return}if(y.target.closest("#archive-rule-modal-close")||y.target.id==="archive-rule-modal"){const k=document.getElementById("archive-rule-modal");k&&(k.style.display="none");return}const x=y.target.closest(".settings-nav-item");if(x){switchSettingsTab(x.dataset.settingsTab);return}if(o&&y.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const E=y.target.closest("[data-add-field]");if(E){const k=E.dataset.addField,B=i[k],L={type:k,...B.defaultCfg};e.push(L),f(),u();return}const _=y.target.closest(".archive-token");if(_&&!o){w(parseInt(_.dataset.tokenIdx,10));return}if(y.target.closest("#btn-archive-save"))return h();if(y.target.closest("#btn-archive-reset"))return I();(y.target.closest("#archive-token-close")||y.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),y.target.closest("#btn-archive-token-ok")&&b(),y.target.closest("#btn-archive-token-delete")&&g()}),document.addEventListener("change",y=>{y.target.name==="folder-strategy"&&(n=y.target.value)});function w(y){a=y;const x=e[y];if(!x)return;const E=document.getElementById("archive-token-body");let _="";x.type==="date"?_=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${x.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${x.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${x.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${x.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:x.type==="seller"?_=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${x.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:x.type==="amount"?_=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${x.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:x.type==="sep"?_=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${x.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${x.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${x.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(x.val)?"":escapeHtml(x.val||"")}">
                    </div>
                </div>`:_=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,E.innerHTML=_,document.getElementById("archive-token-modal").style.display="",E.querySelectorAll(".sep-chip").forEach(k=>{k.addEventListener("click",()=>{E.querySelectorAll(".sep-chip").forEach(L=>L.classList.remove("active")),k.classList.add("active");const B=document.getElementById("token-sep-custom");B&&(B.value="")})})}function b(){const y=e[a];if(y){if(y.type==="date")y.format=document.getElementById("token-date-format").value;else if(y.type==="seller")y.short=document.getElementById("token-seller-short").checked;else if(y.type==="amount")y.with_currency=document.getElementById("token-amount-currency").checked;else if(y.type==="sep"){const x=document.querySelector("#archive-token-body .sep-chip.active"),E=document.getElementById("token-sep-custom").value;y.val=E||(x?x.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",f(),u()}}function g(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",f(),u())}async function h(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const x=document.getElementById("archive-rule-modal");x&&(x.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function I(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",f(),l(),u())}})();(function(){window.loadAboutPanel=()=>e(),window.loadPrefsSettings=()=>n();function e(){const o=document.getElementById("settings-contact-grid");if(!o)return;const s=_contact?.phone||"086-889-2228",i=_contact?.line_id||"@Pearnly",r=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",d=_contact?.email||"hello@pearnly.com",m=_contact?.address||"Bangkok, Thailand";o.innerHTML=`
            <a class="contact-item" href="${escapeHtml(r)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(i)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(d)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(d)}</div>
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
        `}async function n(){try{const o=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!o.ok)return;const s=await o.json(),i=document.getElementById("pref-dup-check");i&&(i.checked=!!s.enabled)}catch(o){console.warn("load prefs failed",o)}}const a=document.getElementById("pref-dup-check");a&&!a.dataset.bound&&(a.dataset.bound="1",a.addEventListener("change",async o=>{const s=o.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:s})})).ok?showToast(s?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(o.target.checked=!s,showToast(t("pref-save-failed"),"error"))}catch{o.target.checked=!s,showToast(t("pref-save-failed"),"error")}}))})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,i=null,r=0,d=0,m=!1;function p(h){const I=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return h.preventDefault(),h.returnValue=I,I}function f(){m||(m=!0,window.addEventListener("beforeunload",p))}function c(){m&&(m=!1,window.removeEventListener("beforeunload",p))}function l(){if(document.getElementById("big-batch-progress"))return;const h=document.getElementById("file-list");if(!h||!h.parentNode)return;const I=document.createElement("div");I.id="big-batch-progress",I.className="big-batch-progress",I.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',h.parentNode.insertBefore(I,h);const y=document.getElementById("bbp-text");y&&(y.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function u(){const h=document.getElementById("big-batch-progress");h&&h.remove()}function v(){if(!i)return;let h=0;for(let L=0;L<i.length;L++){const C=i[L].status;(C==="success"||C==="error"||C==="cancelled")&&h++}const I=r,y=I>0?Math.min(100,Math.floor(100*h/I)):0,x=(Date.now()-d)/1e3;let E;if(h>=3&&x>1){const L=x/h;E=(I-h)*L}else E=(I-h)*6/6;const _=Math.max(1,Math.ceil(E/60)),k=document.getElementById("bbp-fill"),B=document.getElementById("bbp-text");k&&(k.style.width=y+"%"),B&&(h>=I?B.textContent=t("big-batch-progress-done").replace("{total}",I):B.textContent=t("big-batch-progress-running").replace("{done}",h).replace("{total}",I).replace("{min}",_))}function w(h){try{if(localStorage.getItem(o)==="1")return}catch{}const I=Math.max(1,Math.ceil(h*6/6/60)),y=t("big-batch-first-tip").replace("{n}",h).replace("{min}",I);typeof showToast=="function"&&showToast(y,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function b(h){!h||h.length<100||(i=h,r=h.length,d=Date.now(),l(),f(),w(r),s&&clearInterval(s),s=setInterval(v,250),v())}function g(){s&&(clearInterval(s),s=null),c(),i&&r>=100?(v(),setTimeout(u,1200)):u(),i=null,r=0}window._bigBatchStart=b,window._bigBatchStop=g,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&v()})})();(function(){let e=null,n=!1,a=!1;function o(k){return typeof escapeHtml=="function"?escapeHtml(k==null?"":String(k)):String(k??"")}function s(k,B){try{typeof showToast=="function"&&showToast(k,B||"info")}catch{}}function i(){const k=typeof _userInfo<"u"?_userInfo:null;return!!(k&&(k.role==="owner"||k.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function d(k){if(!k)return!1;const B=String(k.status||"").toLowerCase();return B==="exception"||B==="exception_pending"||B==="rejected"}async function m(k){if(n&&!k)return e;const B=localStorage.getItem("mrpilot_token");if(!B)return null;try{const L=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+B}});if(!L.ok)throw new Error("http_"+L.status);e=await L.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function p(){const k=document.getElementById("erp-connect-cards");if(!k)return;const B=e;let L,C=!1;B?B.configured?B.connected?(C=!0,L='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let S="";if(!B||!B.configured)S='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!B.connected)i()&&(S='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const j=!!B.auto_push,N=j?t("card-btn-disable"):t("card-btn-enable");S='<button type="button" class="'+(j?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(j?"1":"0")+'" title="'+o(j?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(N)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const M=B&&B.connected?"xero-card-desc-connected":"xero-card-desc-default",$=B&&B.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",q=(function(){const j=t(M);return j===M?$:j})();let H='<div class="integration-row erp-connect-xero'+(C?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+L+'</div><div class="int-desc">'+o(q)+'</div></div><div class="int-actions">'+S+"</div></div>";if(B&&B.configured&&B.connected&&i()){const j=B.organisations||[];let N="";if(j.length>0){N+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(j.length)))+"</div>",N+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",N+='<div class="erp-cc-orgs">',j.forEach(function(pe){N+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(pe.id)+'"'+(pe.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(pe.organisation_name||pe.organisation_id)+"</span></label>"}),N+="</div>";const se=!!B.auto_push,ie=se?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");N+='<div class="erp-cc-auto-push" title="'+o(ie)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(se?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",N+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}H+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+N+"</div>"}const T=k.querySelector(".erp-connect-xero"),D=k.querySelector("#erp-xero-details");D&&D.remove(),T?T.outerHTML=H:k.insertAdjacentHTML("afterbegin",H);const O=document.getElementById("btn-xero-edit-toggle");O&&O.addEventListener("click",function(j){j.preventDefault();const N=document.getElementById("erp-xero-details");N&&(N.style.display=N.style.display==="none"?"":"none")});const P=document.getElementById("btn-xero-toggle-enabled");P&&P.addEventListener("click",async function(j){if(j.preventDefault(),P.disabled)return;const se=!(P.getAttribute("data-xero-enabled")==="1");if(!se)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}P.disabled=!0,await u(se,null)})}async function f(){const k=localStorage.getItem("mrpilot_token");if(k)try{const B=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+k}});if(!B.ok){let C="unknown";try{C=(await B.json()).detail||"unknown"}catch{}const S=String(C).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+S)||C),"error");return}const L=await B.json();L.redirect_url&&(window.location.href=L.redirect_url)}catch(B){s(t("xero-push-fail").replace("{err}",B.message||"network"),"error")}}async function c(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const B=localStorage.getItem("mrpilot_token");try{const L=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+B}});if(!L.ok)throw new Error("http_"+L.status);await m(!0),p()}catch(L){s(t("xero-push-fail").replace("{err}",L.message),"error")}}async function l(k){const B=localStorage.getItem("mrpilot_token");try{const L=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+B,"Content-Type":"application/json"},body:JSON.stringify({token_id:k})});if(!L.ok)throw new Error("http_"+L.status);await m(!0),p()}catch(L){s(t("xero-push-fail").replace("{err}",L.message),"error")}}async function u(k,B){const L=localStorage.getItem("mrpilot_token");B&&(B.disabled=!0);try{const C=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+L,"Content-Type":"application/json"},body:JSON.stringify({on:!!k})});if(!C.ok){let S="unknown";try{S=(await C.json()).detail||"unknown"}catch{}throw new Error(S)}s(k?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await m(!0),p()}catch(C){B&&(B.checked=!k),s(t("erp-auto-push-toggle-fail").replace("{err}",C.message||"network"),"error")}finally{B&&(B.disabled=!1)}}async function v(){const k=document.getElementById("drawer-history-save");if(!k||k.querySelector("#btn-xero-push")||k.querySelector("#pn-push-wrap")||(await m(!1),k.querySelector("#pn-push-wrap"))||k.querySelector("#btn-xero-push"))return;const B=r();if(!(B&&(B._historyId||B.history_id)))return;let C=!1,S="xero-push-tip";!e||!e.configured?(C=!0,S="xero-err-not_configured"):e.connected?d(B)&&(C=!0,S="xero-push-disabled-exc"):(C=!0,S="xero-push-disabled-no-conn");const M=document.createElement("button");M.type="button",M.id="btn-xero-push",M.className="btn btn-ghost"+(C?" disabled":""),M.disabled=C,M.title=t(S)||"",M.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",M.addEventListener("click",w);const $=document.getElementById("btn-push-erp");$&&$.parentNode?$.parentNode.insertBefore(M,$.nextSibling):k.insertBefore(M,k.firstChild)}async function w(){const k=r(),B=k&&(k._historyId||k.history_id);if(!B)return;const L=document.getElementById("btn-xero-push");L&&(L.disabled=!0,L.classList.add("loading"));const C=localStorage.getItem("mrpilot_token");try{const S=await fetch("/api/erp/xero/push/"+encodeURIComponent(B),{method:"POST",headers:{Authorization:"Bearer "+C}});if(!S.ok){let M="unknown";try{M=(await S.json()).detail||"unknown"}catch{}const $=String(M).replace(/^xero\./,"").toLowerCase(),q=t("xero-"+$),H=q&&q!=="xero-"+$?q:M;s(t("xero-push-fail").replace("{err}",H),"error");return}s(t("xero-push-ok"),"success")}catch(S){s(t("xero-push-fail").replace("{err}",S.message||"network"),"error")}finally{L&&(L.disabled=!1,L.classList.remove("loading"))}}async function b(){await m(!0),p(),g()}async function g(){const k=document.getElementById("erp-global-push-mode");if(!k)return;const B=localStorage.getItem("mrpilot_token");if(B)try{const L=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+B}});if(L.ok){const C=await L.json();C.mode&&(k.value=C.mode,k.dataset.prev=C.mode)}}catch{}}async function h(k){const B=k.value,L=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+L,"Content-Type":"application/json"},body:JSON.stringify({mode:B})})).ok?(k.dataset.prev=B,s(t("pref-erp-mode-saved"),"success")):(k.value=k.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{k.value=k.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function I(){try{const k=String(window.location.hash||"");if(k.indexOf("xero=ok")>=0){const B=k.match(/n=(\d+)/),L=B?B[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",L),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),m(!0).then(p)}else k.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function y(){if(a)return;a=!0,document.addEventListener("click",function(B){if(B.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(b,50);return}if(B.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(b,80);return}if(B.target.closest("#btn-xero-connect")){B.preventDefault(),f();return}if(B.target.closest("#btn-xero-disconnect")){B.preventDefault(),c();return}}),document.addEventListener("change",function(B){B.target&&B.target.matches('input[name="xero-default-org"]')&&l(B.target.value),B.target&&B.target.id==="xero-auto-push-toggle"&&u(B.target.checked,B.target),B.target&&B.target.id==="erp-global-push-mode"&&h(B.target)});const k=function(){return document.getElementById("drawer-body")};try{const B=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&v()}),L=k();if(L)B.observe(L,{childList:!0,subtree:!0});else{const C=new MutationObserver(function(){const S=k();S&&(B.observe(S,{childList:!0,subtree:!0}),C.disconnect())});C.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(I,500)}function x(){e&&p();const k=document.getElementById("btn-xero-push");if(k){const B=k.querySelector("span");B&&(B.textContent=t("xero-push-btn"))}}y(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",x);async function E(k){const B=Date.now();for(;Date.now()-B<k;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(L=>setTimeout(L,80))}return null}async function _(){await E(5e3);const k=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),B=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');k&&B&&await b()}setTimeout(_,200)})();(function(){var e="https://www.mrerp4sme.com/dms/index.php",n=null,a=!1;function o(b){return typeof escapeHtml=="function"?escapeHtml(b==null?"":String(b)):String(b??"")}function s(b,g){try{typeof showToast=="function"&&showToast(b,g||"info")}catch{}}function i(){return localStorage.getItem("mrpilot_token")}async function r(b){var g=i();if(!g)return null;try{var h=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+g}});if(!h.ok)throw new Error("http_"+h.status);var I=await h.json(),y=I&&I.items||[];n=y.find(function(x){return x&&(x.adapter||"").toLowerCase()==="mrerp_dms"})||null,a=!0}catch{n=null,a=!1}return n}function d(){var b=document.getElementById("erp-connect-cards");if(b){var g=b.querySelector("[data-mrerp-dms-zone]");g||(g=document.createElement("div"),g.setAttribute("data-mrerp-dms-zone","1"),b.appendChild(g));var h=n,I=!!(h&&h.enabled!==!1),y;h?I?y='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("dms-card-connected"))+"</span>":y='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-disabled-pill"))+"</span>":y='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-not-connected"))+"</span>";var x;if(!h)x='<button type="button" class="int-btn-configure" id="btn-dms-connect">'+o(t("dms-card-connect"))+"</button>";else{var E=I?t("dms-card-disable"):t("dms-card-enable");x='<button type="button" class="int-btn-configure" id="btn-dms-edit">'+o(t("dms-card-edit"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-test">'+o(t("dms-card-test"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-toggle">'+o(E)+"</button>"}g.innerHTML='<div class="integration-row erp-connect-mrerp-dms'+(I?" connected":"")+'"><div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/><path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("dms-card-title"))+"</span>"+y+'</div><div class="int-desc">'+o(t("dms-card-desc"))+'</div></div><div class="int-actions">'+x+"</div></div>"}}function m(){var b=document.getElementById("dms-wizard-overlay");b&&b.remove(),document.removeEventListener("keydown",p)}function p(b){b.key==="Escape"&&m()}function f(){m();var b=n,g=b&&b.config&&b.config.booking_defaults&&b.config.booking_defaults.booking_prefix||"PN",h=function(x,E,_,k,B){return'<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">'+o(t(x))+'</span><input id="'+E+'" type="'+_+'" value="'+o(k||"")+'" placeholder="'+o(B||"")+'" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;"></label>'},I=document.createElement("div");I.id="dms-wizard-overlay",I.style.cssText="position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;",I.innerHTML='<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">'+o(t("dms-wizard-title"))+'</div><div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">'+o(t("dms-card-desc"))+"</div>"+h("dms-wizard-username","dms-w-user","text","","")+h("dms-wizard-password","dms-w-pass","password","","")+h("dms-wizard-prefix","dms-w-prefix","text",g,"PN")+'<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div><div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn btn-ghost" id="dms-w-cancel">'+o(t("dms-wizard-cancel"))+'</button><button type="button" class="btn btn-primary" id="dms-w-save">'+o(t("dms-wizard-save"))+"</button></div></div>",document.body.appendChild(I),document.addEventListener("keydown",p),I.addEventListener("click",function(x){x.target===I&&m()});var y=document.getElementById("dms-w-user");y&&y.focus()}function c(b){var g=document.getElementById("dms-w-err");g&&(g.textContent=b,g.style.display=b?"":"none")}async function l(){var b=n&&n.config&&n.config.system_url||e,g=(document.getElementById("dms-w-user")||{}).value||"",h=(document.getElementById("dms-w-pass")||{}).value||"",I=(document.getElementById("dms-w-prefix")||{}).value||"PN";if(b=b.trim(),g=g.trim(),!b||!g||!h){c(t("dms-wizard-required"));return}var y=document.getElementById("dms-w-save");y&&(y.disabled=!0,y.textContent=t("dms-wizard-saving")),c("");var x=i();try{var E=await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+x,"Content-Type":"application/json"},body:JSON.stringify({adapter:"mrerp_dms",config:{system_url:b,username:g,password:h}})}),_=await E.json().catch(function(){return{}});if(!E.ok||!_.ok){var k=_.error_friendly&&(_.error_friendly[window.currentLang]||_.error_friendly.en)||t("dms-connect-fail-generic");c(k),y&&(y.disabled=!1,y.textContent=t("dms-wizard-save"));return}var B={system_url:b,username_enc:g,password_enc:h,id_card_auto_push:!0,booking_defaults:{booking_prefix:I.trim()||"PN"}},L,C;n&&n.id?(L="PATCH",C="/api/erp/endpoints/"+encodeURIComponent(n.id)):(L="POST",C="/api/erp/endpoints");var S=L==="POST"?{name:"MR.ERP DMS",adapter:"mrerp_dms",config:B,is_default:!1,auto_push:!1}:{config:B,auto_push:!1},M=await fetch(C,{method:L,headers:{Authorization:"Bearer "+x,"Content-Type":"application/json"},body:JSON.stringify(S)});if(!M.ok){var $=await M.json().catch(function(){return{}}),q=$&&$.detail&&($.detail.code||$.detail)||"save_failed";c(t("dms-save-fail")+" ("+o(String(q))+")"),y&&(y.disabled=!1,y.textContent=t("dms-wizard-save"));return}m(),s(t("dms-connect-ok"),"success"),await r(!0),d(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{c(t("dms-connect-fail-generic")),y&&(y.disabled=!1,y.textContent=t("dms-wizard-save"))}}async function u(){if(!(!n||!n.id)){s(t("dms-test-running"),"info");var b=i();try{var g=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id)+"/test-connection?refresh=1",{method:"POST",headers:{Authorization:"Bearer "+b}}),h=await g.json().catch(function(){return{}});s(h&&h.ok?t("dms-test-ok"):t("dms-test-fail"),h&&h.ok?"success":"error")}catch{s(t("dms-test-fail"),"error")}}}async function v(){if(!(!n||!n.id)){var b=n.enabled===!1;if(!b)try{var g=await window.pearnlyConfirm(t("dms-confirm-disable"));if(!g)return}catch{}var h=i();try{var I=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id),{method:"PATCH",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({enabled:b})});if(!I.ok)throw new Error("http_"+I.status);s(b?t("dms-enabled-toast"):t("dms-disabled-toast"),"success"),await r(!0),d(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{s(t("dms-save-fail"),"error")}}}function w(){r().then(d)}document.addEventListener("click",function(b){if(b.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(w,60);return}if(b.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(w,90);return}if(b.target.closest("#btn-dms-connect")||b.target.closest("#btn-dms-edit")){b.preventDefault(),f();return}if(b.target.closest("#dms-w-cancel")){b.preventDefault(),m();return}if(b.target.closest("#dms-w-save")){b.preventDefault(),l();return}if(b.target.closest("#btn-dms-test")){b.preventDefault(),u();return}if(b.target.closest("#btn-dms-toggle")){b.preventDefault(),v();return}}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("mrerp-dms-adapter",d),setTimeout(function(){var b=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),g=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');b&&g&&w()},250)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const p=`
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
        </div>`,f=document.createElement("div");f.innerHTML=p,document.body.appendChild(f.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",c=>{c.target.id==="report-modal"&&a()})}function a(){const p=document.getElementById("report-modal");p&&(p.style.display="none"),o=null}let o=null;async function s(p,f){const c=p+":"+(f||"");if(e[c])return e[c];let l;try{const u=localStorage.getItem("mrpilot_token"),v=await fetch(`/api/reports/templates?lang=${encodeURIComponent(p)}`,{headers:{Authorization:"Bearer "+u}});if(!v.ok)throw new Error("templates fetch failed");l=(await v.json()).templates||[]}catch(u){console.error("fetchTemplates fail",u),l=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(l=l.filter(u=>u.code!=="erp"),f==="history-batch"){const u=l.findIndex(w=>w.code==="standard"),v=u>=0?u+1:l.length;l.splice(v,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[c]=l,l}function i(p){const f=document.getElementById("report-tpl-list"),c=p.map((u,v)=>`
            <label class="report-tpl-item${u.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${u.code}" ${u.recommended||v===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${r(u.name)}
                        ${u.recommended?`<span class="report-tpl-badge">${r(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${r(u.desc||"")}</div>
                </div>
            </label>
        `).join(""),l=`
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
        `;f.innerHTML=c+l}function r(p){return p==null?"":String(p).replace(/[&<>"']/g,f=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[f])}function d(p){const f=new Date,c=f.getFullYear(),l=f.getMonth()+1;if(p==="all")return"all";if(p==="this-month")return`${c}-${String(l).padStart(2,"0")}`;if(p==="last-month"){const u=new Date(c,l-2,1);return`${u.getFullYear()}-${String(u.getMonth()+1).padStart(2,"0")}`}return p==="this-year"?`${c}`:p==="this-quarter"?`${c}-Q${Math.floor((l-1)/3)+1}`:"all"}window.openReportModal=async function(p){p=p||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(w=>{const b=w.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][b]&&(w.textContent=I18N[currentLang][b])});const f=document.getElementById("report-period-section");f&&(f.style.display=p.mode==="client"?"":"none");const c=document.getElementById("report-tpl-list");c.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const l=await s(currentLang,p&&p.mode);i(l),o=p;const u=document.getElementById("report-modal-download"),v=u.cloneNode(!0);u.parentNode.replaceChild(v,u),v.addEventListener("click",()=>m(o))};async function m(p){if(!p)return;const f=document.querySelector('input[name="report-tpl"]:checked');if(!f){showToast(t("report-toast-no-selection"),"info");return}const c=f.value,l=document.querySelector('input[name="report-period"]:checked'),u=l?l.value:"all",v=d(u),w=document.getElementById("report-modal-download"),b=w.innerHTML;w.disabled=!0,w.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const g=localStorage.getItem("mrpilot_token");let h,I;if(p.mode==="records")h=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+g,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,records:p.records||[],meta:p.meta||{}})}),I=`mrpilot-${c}-${Date.now()}.xlsx`;else if(p.mode==="client"){const L=`/api/reports/clients/${p.clientId}/export?template=${encodeURIComponent(c)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(v)}`;h=await fetch(L,{headers:{Authorization:"Bearer "+g}}),I=`${(p.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${c}.xlsx`}else if(p.mode==="history-batch")c==="sales_detail_th"?(h=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+g,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),I=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(h=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+g,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),I=`mrpilot-batch-${c}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+p.mode);if(!h.ok){let L="HTTP "+h.status;try{const C=await h.json();C&&C.detail&&(L=C.detail)}catch(C){console.warn("[batch-export] resp.json err.detail parse failed:",C)}h.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+L,"error");return}const y=await h.blob();let x=I;const _=(h.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(_)try{x=decodeURIComponent(_[1])}catch{}const k=URL.createObjectURL(y),B=document.createElement("a");B.href=k,B.download=x,document.body.appendChild(B),B.click(),document.body.removeChild(B),URL.revokeObjectURL(k),showToast(t("report-toast-success"),"success"),a()}catch(g){console.error("doDownload fail",g),showToast(t("report-toast-fail")+" · "+(g.message||""),"error")}finally{w.disabled=!1,w.innerHTML=b}}document.addEventListener("DOMContentLoaded",()=>{const p=document.getElementById("btn-export");if(p){const c=p.cloneNode(!0);p.parentNode.replaceChild(c,p),c.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(l=>({filename:l.filename,merged_fields:l.merged_fields||{}}))})})}const f=document.getElementById("history-batch-export");f&&f.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(p,f){openReportModal({mode:"client",clientId:p,clientName:f||""})}})();const Qs=/\.(pdf|jpe?g|png|webp)$/i,ei="mrpilot_folder_watcher",ti=1;let qt=null;function an(){return qt||(qt=new Promise((e,n)=>{const a=indexedDB.open(ei,ti);a.onupgradeneeded=o=>{const s=o.target.result;s.objectStoreNames.contains("handles")||s.createObjectStore("handles"),s.objectStoreNames.contains("seen")||s.createObjectStore("seen"),s.objectStoreNames.contains("config")||s.createObjectStore("config")},a.onsuccess=o=>e(o.target.result),a.onerror=o=>n(o.target.error)}),qt)}function kt(e,n){return an().then(a=>new Promise((o,s)=>{const r=a.transaction(e,"readonly").objectStore(e).get(n);r.onsuccess=()=>o(r.result),r.onerror=()=>s(r.error)}))}function Ge(e,n,a){return an().then(o=>new Promise((s,i)=>{const r=o.transaction(e,"readwrite");r.objectStore(e).put(a,n),r.oncomplete=()=>s(),r.onerror=()=>i(r.error)}))}function yt(e,n){return an().then(a=>new Promise((o,s)=>{const i=a.transaction(e,"readwrite");i.objectStore(e).delete(n),i.oncomplete=()=>o(),i.onerror=()=>s(i.error)}))}function oa(e){return an().then(n=>new Promise((a,o)=>{const s=n.transaction(e,"readwrite");s.objectStore(e).clear(),s.oncomplete=()=>a(),s.onerror=()=>o(s.error)}))}async function sa(e){if(!e)return!1;try{const n={mode:"read"};let a=await e.queryPermission(n);return a==="granted"?!0:(a=await e.requestPermission(n),a==="granted")}catch(n){return console.warn("[folder] permission check failed:",n),!1}}async function ni(e){const n=new FormData;n.append("file",e,e.name),n.append("source","folder");const a=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:n});if(!a.ok){let o="http_"+a.status;try{const s=await a.json();o=s&&s.detail?typeof s.detail=="string"?s.detail:s.detail.code||JSON.stringify(s.detail):o}catch{}throw new Error(o)}return await a.json()}async function ai(e){try{const a=(await e.getFile()).size;return await new Promise(s=>setTimeout(s,3e3)),(await e.getFile()).size===a&&a>0}catch{return!1}}async function Ya(e,n,a,o){if(o>10)return;let s;try{s=await e.queryPermission({mode:"read"})}catch{s="denied"}if(s==="granted")for await(const i of e.values()){const r=n?`${n}/${i.name}`:i.name;if(i.kind==="file"){if(!Qs.test(i.name))continue;let d;try{d=await i.getFile()}catch{continue}const m=`${r}::${d.size}::${d.lastModified}`;if(await kt("seen",m))continue;a.push({entry:i,file:d,seenKey:m,relPath:r})}else if(i.kind==="directory")try{await Ya(i,r,a,o+1)}catch{}}}(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window;let a=null,o=null,s=60,i=!1,r=!1,d=0,m=0,p=0,f=[],c=null,l=!1;function u(P,j){const N=document.getElementById("folder-status-summary");N&&(N.setAttribute("data-i18n",P),N.textContent=t(P),N.className="auto-status-pill"+(j?" "+j:""))}function v(P){["folder-unsupported","folder-empty","folder-active"].forEach(j=>{const N=document.getElementById(j);N&&(N.style.display=j===P?"":"none")})}function w(P){if(!P)return"-";const j=P instanceof Date?P:new Date(P),N=String(j.getHours()).padStart(2,"0"),se=String(j.getMinutes()).padStart(2,"0"),ie=String(j.getSeconds()).padStart(2,"0");return`${N}:${se}:${ie}`}function b(){v("folder-active");const P=document.getElementById("folder-config-path");P&&a&&(P.textContent=a.name||"-");const j=document.getElementById("folder-interval-select");j&&(j.value=String(s)),document.getElementById("folder-stat-last").textContent=c?w(c):"-",document.getElementById("folder-stat-processed").textContent=String(d),document.getElementById("folder-stat-failed").textContent=String(m),document.getElementById("folder-stat-queue").textContent=String(p);const N=document.getElementById("btn-folder-pause"),se=document.getElementById("btn-folder-resume");N&&(N.style.display=i?"none":""),se&&(se.style.display=i?"":"none"),i?u("folder-status-paused","paused"):u("folder-status-running","running");const ie=document.getElementById("folder-status-text");ie&&(ie.setAttribute("data-i18n",i?"folder-status-paused":"folder-status-running"),ie.textContent=t(i?"folder-status-paused":"folder-status-running"));const pe=document.getElementById("folder-status-pulse");pe&&(pe.className="folder-status-pulse"+(i?" paused":"")),g()}function g(){const P=document.getElementById("folder-recent-list");if(P){if(f.length===0){P.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}P.innerHTML=f.slice(0,20).map(j=>{let N;j.status==="ok"?N=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:j.status==="dup"?N=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:j.status==="skip"?N=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:N=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const se=j.status==="fail"&&j.error?j.error:j.status==="dup"&&j.reason||j.status==="skip"&&j.reason?j.reason:"",ie=se?`<div class="folder-recent-err">${escapeHtml(se)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${N}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(j.name)}</div>
                        ${ie}
                    </div>
                    <div class="folder-recent-time">${w(j.time)}</div>
                </div>
            `}).join("")}}function h(P){f.unshift(P),f.length>50&&(f.length=50),Ge("config","recent_list",f).catch(()=>{})}async function I(){if(!(r||i||!a)){r=!0;try{if(await a.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),S(),showToast("warn",t("folder-permission-lost"));return}c=new Date;const j=[];await Ya(a,"",j,0),p=j.length,b();for(const N of j){if(i)break;if(!await ai(N.entry)){p=Math.max(0,p-1),b();continue}try{let ie;try{ie=await N.entry.getFile()}catch{ie=N.file}const pe=await ni(ie);await Ge("seen",N.seenKey,{name:ie.name,relPath:N.relPath,size:ie.size,lastModified:ie.lastModified,processed_at:Date.now()});const re=pe.history_ids||(pe.history_id?[pe.history_id]:[]),he=pe.duplicate_warnings||[],be=N.relPath||ie.name;re.length>0?(d+=re.length,h({name:be,status:"ok",time:new Date,history_id:re[0],count:re.length}),await Ge("config","processed_count",d)):he.length>0?h({name:be,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):h({name:be,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(ie){m++,h({name:N.relPath||N.file.name,status:"fail",time:new Date,error:String(ie.message||ie)}),await Ge("config","failed_count",m)}p=Math.max(0,p-1),b()}}catch(P){console.warn("[folder] scan error:",P)}finally{r=!1,b()}}}function y(){o&&clearInterval(o),o=setInterval(I,s*1e3)}function x(){o&&(clearInterval(o),o=null)}function E(P){if(!a||i)return;const j=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return P.preventDefault(),P.returnValue=j,j}function _(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",E))}function k(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",E))}function B(){i=!1,y(),_(),b(),I()}function L(){i=!0,x(),k(),b()}function C(){i=!1,y(),_(),b(),I()}function S(){i=!0,x(),k()}async function M(){try{const P=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await sa(P)){showToast("warn",t("folder-permission-denied"));return}a=P,await Ge("handles","main",P),d=0,m=0,p=0,f=[],await Ge("config","processed_count",0),await Ge("config","failed_count",0),await oa("seen"),B()}catch(P){P&&P.name!=="AbortError"&&console.warn("[folder] pick failed:",P)}}async function $(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(S(),a=null,d=0,m=0,p=0,f=[],await yt("handles","main"),await yt("config","processed_count"),await yt("config","failed_count"),await oa("seen"),v("folder-empty"),u("folder-status-empty",""))}async function q(){f=[];try{await yt("config","recent_list")}catch{}g()}async function H(){if(l)return;if(l=!0,!n){v("folder-unsupported"),u("folder-status-unsupported",""),O();return}T();let P=null;try{P=await kt("handles","main")}catch{}if(!P){v("folder-empty"),u("folder-status-empty","");return}if(!await sa(P)){v("folder-empty"),u("folder-status-empty",""),await yt("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}a=P;try{d=await kt("config","processed_count")||0}catch{}try{m=await kt("config","failed_count")||0}catch{}try{const N=await kt("config","recent_list");Array.isArray(N)&&(f=N.map(se=>({...se,time:se.time?new Date(se.time):new Date})))}catch{}B()}function T(){const P=document.getElementById("btn-folder-pick"),j=document.getElementById("btn-folder-pause"),N=document.getElementById("btn-folder-resume"),se=document.getElementById("btn-folder-scan-now"),ie=document.getElementById("btn-folder-remove"),pe=document.getElementById("btn-folder-clear-recent"),re=document.getElementById("folder-interval-select");P&&P.addEventListener("click",M),j&&j.addEventListener("click",L),N&&N.addEventListener("click",C),se&&se.addEventListener("click",()=>{I()}),ie&&ie.addEventListener("click",$),pe&&pe.addEventListener("click",q),re&&re.addEventListener("change",he=>{s=parseInt(he.target.value,10)||60,i||y()}),D()}function D(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(P=>{P.dataset.tabJumpBound||(P.dataset.tabJumpBound="1",P.addEventListener("click",j=>{const N=j.currentTarget.dataset.tabJump;if(N==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(N==="upload"){const se=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');se&&se.click()}}))})}function O(){D()}window._loadFolderWatcherPanel=H})();function oi(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(n=>/chromium|google chrome|microsoft edge/i.test(n.brand||""))}catch{}const e=navigator.userAgent||"";return!!(/Edg\//.test(e)||/Chrome\//.test(e)&&!/OPR\/|YaBrowser|Opera/.test(e))}function wn(){try{if(oi()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const e=document.getElementById("chrome-only-banner");if(!e)return;const n=e.querySelector('[data-i18n="chrome-banner-msg"]'),a=e.querySelector('[data-i18n="chrome-banner-dismiss"]');n&&typeof t=="function"&&(n.textContent=t("chrome-banner-msg")),a&&typeof t=="function"&&(a.textContent=t("chrome-banner-dismiss")),e.style.display="";const o=document.getElementById("chrome-only-banner-close");o&&!o.dataset.bound&&(o.dataset.bound="1",o.addEventListener("click",()=>{e.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",wn):setTimeout(wn,0));window._refreshChromeBanner=wn;const si=`
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
    `;ke("email-modal",si);const J={account:null,presets:null,modalMode:"new",loaded:!1,triggering:!1,autoRefreshTimer:null};function ia(e){J.modalMode=e;const n=document.getElementById("email-modal");if(!n)return;const a=document.getElementById("email-preset");a.innerHTML="";const o=J.presets||{},s=["gmail","outlook","yahoo","icloud","qq","163","custom"],i={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};s.forEach(g=>{if(!o[g])return;const h=document.createElement("option");h.value=g,h.textContent=g==="custom"?t("email-preset-custom"):i[g]||g,a.appendChild(h)});const r=document.getElementById("email-modal-title"),d=document.getElementById("email-address"),m=document.getElementById("email-password"),p=document.getElementById("email-imap-host"),f=document.getElementById("email-imap-port"),c=document.getElementById("email-imap-ssl"),l=document.getElementById("email-folder"),u=document.getElementById("email-mark-read"),v=document.getElementById("email-bind-enabled"),w=document.getElementById("email-test-result"),b=document.getElementById("email-adv-details");if(w&&(w.style.display="none",w.textContent=""),e==="edit"&&J.account){r.setAttribute("data-i18n","email-modal-title-edit"),r.textContent=t("email-modal-title-edit"),d.value=J.account.email_address||"",m.value="",m.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),m.placeholder=t("email-field-password-edit-ph"),p.value=J.account.imap_host||"",f.value=J.account.imap_port||993,c.checked=J.account.imap_use_ssl!==!1,l.value=J.account.folder||"INBOX",u.checked=J.account.mark_as_read!==!1,v.checked=J.account.enabled!==!1;const g=document.getElementById("email-filter-sender"),h=document.getElementById("email-filter-subject");g&&(g.value=J.account.filter_sender||""),h&&(h.value=J.account.filter_subject||""),la(J.account.interval_min||15),a.value=ri(J.account.imap_host)||"custom",b&&(b.open=!0)}else{r.setAttribute("data-i18n","email-modal-title-new"),r.textContent=t("email-modal-title-new"),d.value="",m.value="",m.setAttribute("data-i18n-placeholder","email-field-password-ph"),m.placeholder=t("email-field-password-ph"),a.value="gmail",An("gmail"),l.value="INBOX",u.checked=!0,v.checked=!0;const g=document.getElementById("email-filter-sender"),h=document.getElementById("email-filter-subject");g&&(g.value=""),h&&(h.value=""),la(15),b&&(b.open=!1)}li(),n.style.display="flex",setTimeout(()=>d.focus(),60)}function pn(){const e=document.getElementById("email-modal");e&&(e.style.display="none")}function An(e){const n=(J.presets||{})[e];if(!n||e==="custom")return;const a=document.getElementById("email-imap-host"),o=document.getElementById("email-imap-port"),s=document.getElementById("email-imap-ssl");a&&(a.value=n.host||""),o&&(o.value=n.port||993),s&&(s.checked=n.ssl!==!1)}const ii={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function ra(e){if(!e||!e.includes("@"))return;const n=e.split("@")[1].toLowerCase().trim(),a=ii[n];if(!a)return;const o=document.getElementById("email-preset");if(!o)return;const s=o.value;s&&s!=="custom"&&s!==""&&s===a||(o.value=a,An(a))}function ri(e){if(!e)return null;const n=J.presets||{};for(const a in n)if(a!=="custom"&&n[a]&&n[a].host===e)return a;return null}function Xa(){const e=document.querySelector("#email-interval-options .email-interval-btn.active"),n=e?parseInt(e.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(n)?n:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function li(){const e=document.getElementById("email-interval-options");!e||e._bound||(e._bound=!0,e.addEventListener("click",n=>{const a=n.target.closest(".email-interval-btn");a&&(e.querySelectorAll(".email-interval-btn").forEach(o=>o.classList.remove("active")),a.classList.add("active"))}))}function la(e){const n=[5,15,60].includes(e)?e:15,a=document.getElementById("email-interval-options");a&&a.querySelectorAll(".email-interval-btn").forEach(o=>{o.classList.toggle("active",parseInt(o.dataset.interval,10)===n)})}function Ee(e,n){const a=document.getElementById("email-test-result");a&&(a.style.display="",a.textContent=n,a.className="form-test-result "+(e==="ok"?"ok":e==="running"?"running":"fail"))}async function ci(){const e=Xa();if(!e.email_address){Ee("fail",t("email-addr-required"));return}if(!e.password){Ee("fail",t("email-password-required"));return}if(!e.imap_host){Ee("fail",t("email-host-required"));return}const n=document.getElementById("btn-email-modal-test");n&&(n.disabled=!0),Ee("running",t("email-test-running"));try{const a=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,password:e.password,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder})}),o=await a.json().catch(()=>({}));if(a.ok&&o.success)Ee("ok",t("email-test-ok",{folder:e.folder,n:o.folder_count??"?"}));else{const s=o.error_msg||"";s==="auth_failed"||/auth/i.test(s)?Ee("fail",t("email-test-auth-fail")):Ee("fail",t("email-test-fail",{msg:s||a.status}))}}catch(a){Ee("fail",t("email-test-fail",{msg:String(a).slice(0,120)}))}finally{n&&(n.disabled=!1)}}(function(){async function e(){const l=document.getElementById("email-empty"),u=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!l||!u))try{const v=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(v.status===401){localStorage.removeItem("mrpilot_token");const b=await v.json().catch(()=>({}));if((typeof b.detail=="string"?b.detail:b.detail&&b.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!v.ok){a("none");return}const w=await v.json();J.account=w.account||null,J.presets=w.presets||{},J.loaded=!0,n(),J.account&&p()}catch(v){console.error("[email-ingest] load failed",v),a("none")}}function n(){const l=document.getElementById("email-empty"),u=document.getElementById("email-account-card"),v=document.getElementById("email-logs-section");if(!J.account){l.style.display="",u.style.display="none",v&&(v.style.display="none"),a("none");return}l.style.display="none",u.style.display="",v&&(v.style.display="");const w=document.getElementById("email-account-addr"),b=document.getElementById("email-account-host"),g=document.getElementById("email-account-last"),h=document.getElementById("email-last-error"),I=document.getElementById("email-enabled-toggle");if(w&&(w.textContent=J.account.email_address||"-"),b&&(b.textContent=`${J.account.imap_host||"-"}:${J.account.imap_port||993}`),g){const y=J.account.last_fetched_at;if(!y)g.textContent=t("email-last-never");else{const x=o(y),E=!J.account.last_error;g.textContent=E?t("email-last-ok",{time:x}):t("email-last-fail",{time:x})}}h&&(J.account.last_error?(h.style.display="",h.textContent=s(J.account.last_error)):h.style.display="none"),I&&(I.checked=!!J.account.enabled),J.account.enabled?J.account.last_error?a("error"):a("on"):a("off")}function a(l){const u=document.getElementById("email-status-summary");if(!u)return;u.classList.remove("none","ready","active","coming");let v="auto-status-loading";l==="none"?(v="email-status-none",u.classList.add("none")):l==="on"?(v="email-status-on",u.classList.add("active")):l==="off"?(v="email-status-off",u.classList.add("coming")):l==="error"&&(v="email-status-error",u.classList.add("none")),u.setAttribute("data-i18n",v),u.textContent=t(v)}function o(l){if(!l)return"";const u=new Date(l);if(isNaN(u.getTime()))return"";const v=w=>String(w).padStart(2,"0");return`${v(u.getMonth()+1)}-${v(u.getDate())} ${v(u.getHours())}:${v(u.getMinutes())}`}function s(l){if(!l)return"";const u=String(l);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(u)?t("email-test-auth-fail"):/timeout|timed out/i.test(u)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(u),u)}async function i(){const l=Xa();if(!l.email_address){Ee("fail",t("email-addr-required"));return}if(J.modalMode==="new"&&!l.password){Ee("fail",t("email-password-required"));return}if(!l.imap_host){Ee("fail",t("email-host-required"));return}const u=document.getElementById("btn-email-modal-save");u&&(u.disabled=!0);const v={...l};J.modalMode==="edit"&&!v.password&&delete v.password;try{const w=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(v)}),b=await w.json().catch(()=>({}));if(w.ok&&b.ok)J.account=b.account,showToast(t("email-save-ok"),"success"),pn(),n(),p();else{const h="email."+(b.detail||"").split(".").slice(-1)[0];Ee("fail",t(h)!==h?t(h):t("email-save-fail"))}}catch{Ee("fail",t("email-save-fail"))}finally{u&&(u.disabled=!1)}}async function r(){if(!(!J.account||!await showConfirm(t("email-unbind-confirm",{email:J.account.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){J.account=null,showToast(t("email-unbind-ok"),"success"),n();const v=document.getElementById("email-logs-list");v&&(v.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function d(){if(!J.account||J.triggering)return;if(!J.account.enabled){showToast(t("email.disabled"),"error");return}J.triggering=!0;const l=document.getElementById("btn-email-trigger"),u=l?l.innerHTML:"";l&&(l.disabled=!0,l.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const v=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),w=await v.json().catch(()=>({}));if(v.ok){const b=w.emails_scanned||0,g=w.ocr_succeeded||0,h=w.ocr_failed||0;b===0&&g===0&&h===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:b,ok:g,fail:h}),h>0?"warn":"success")}else{const g="email."+(w.detail||"").split(".").slice(-1)[0];showToast(t(g)!==g?t(g):t("email-trigger-fail"),"error")}await e()}catch{showToast(t("email-trigger-fail"),"error")}finally{J.triggering=!1,l&&(l.disabled=!1,l.innerHTML=u)}}async function m(){if(!J.account)return;const l=document.getElementById("email-enabled-toggle"),u=!!(l&&l.checked),v=J.account.enabled;try{const w=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:J.account.email_address,imap_host:J.account.imap_host,imap_port:J.account.imap_port,imap_use_ssl:J.account.imap_use_ssl,folder:J.account.folder||"INBOX",filter_subject:J.account.filter_subject||null,filter_sender:J.account.filter_sender||null,mark_as_read:J.account.mark_as_read!==!1,enabled:u})}),b=await w.json().catch(()=>({}));w.ok&&b.ok?(J.account=b.account,n()):(l&&(l.checked=v),showToast(t("email-toggle-fail"),"error"))}catch{l&&(l.checked=v),showToast(t("email-toggle-fail"),"error")}}async function p(){const l=document.getElementById("email-logs-list");if(l){l.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const u=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!u.ok){l.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const v=await u.json();if(!Array.isArray(v)||v.length===0){l.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}l.innerHTML=v.map(f).join("")}catch{l.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function f(l){const u=o(l.created_at),v=l.status||"failed",w=v==="success"?"ok":v==="partial"?"partial":"fail",b=v==="success"?"✓":v==="partial"?"◐":"✗",g=l.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,h=t("email-log-counts",{scanned:l.emails_scanned||0,att:l.attachments_found||0,ok:l.ocr_succeeded||0,fail:l.ocr_failed||0}),I=(l.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${w}">
                <span class="log-time">${escapeHtml(u)}</span>
                <span class="log-status">${b}</span>
                ${g}
                <span class="log-counts">${escapeHtml(h)}</span>
                <span class="log-elapsed">${escapeHtml(I)}</span>
            </div>
        `}function c(){const l=document.getElementById("btn-email-bind");l&&l.addEventListener("click",()=>ia("new"));const u=document.getElementById("btn-email-edit");u&&u.addEventListener("click",()=>ia("edit"));const v=document.getElementById("btn-email-unbind");v&&v.addEventListener("click",r);const w=document.getElementById("btn-email-trigger");w&&w.addEventListener("click",d);const b=document.getElementById("email-enabled-toggle");b&&b.addEventListener("change",m);const g=document.getElementById("email-modal-close");g&&g.addEventListener("click",pn);const h=document.getElementById("btn-email-modal-cancel");h&&h.addEventListener("click",pn);const I=document.getElementById("btn-email-modal-test");I&&I.addEventListener("click",ci);const y=document.getElementById("btn-email-modal-save");y&&y.addEventListener("click",i);const x=document.getElementById("email-preset");x&&x.addEventListener("change",k=>An(k.target.value));const E=document.getElementById("email-address");E&&!E.dataset.autoBound&&(E.dataset.autoBound="1",E.addEventListener("blur",k=>ra((k.target.value||"").trim())),E.addEventListener("input",k=>{const B=(k.target.value||"").trim();B.includes("@")&&B.split("@")[1].includes(".")&&ra(B)}));const _=document.getElementById("btn-email-refresh-logs");_&&_.addEventListener("click",()=>{_.classList.add("spinning"),setTimeout(()=>_.classList.remove("spinning"),600),p()})}c(),window._loadEmailIngestPanel=e,window._rerenderEmailIngest=function(){if(!J.loaded)return;n();const l=document.getElementById("email-logs-section");J.account&&l&&l.open&&p()},window._startEmailLogAutoRefresh=function(){J.autoRefreshTimer||(J.autoRefreshTimer=setInterval(()=>{J.account&&J.loaded&&p()},3e4))},window._stopEmailLogAutoRefresh=function(){J.autoRefreshTimer&&(clearInterval(J.autoRefreshTimer),J.autoRefreshTimer=null)}})();const di=`
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
`;ke("bank-cand-drawer",di);const pi=`
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
`;ke("bank-client-picker-modal",pi);const F={sessions:[],currentSession:null,currentTxs:[],currentFilter:"all",currentTxForDrawer:null,loaded:!1,queue:[],qSeq:0,sessionFilter:"all",pickerSelected:null};function ui(e){const n=Number(e||0);let a="score-low";return n>=85?a="score-high":n>=60&&(a="score-mid"),'<span class="bank-cand-score '+a+'">'+n.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function fi(e){const n=document.getElementById("bank-upload-progress");n&&(n.style.display="none")}function mi(){const e=document.getElementById("bank-upload-error");e&&(e.style.display="none")}function vi(e){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[e]||t("bank-err-unknown")+" ("+e+")"}function Xe(e){if(e==null)return"-";const n=Number(e);return isNaN(n)?"-":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function pt(e){if(!e)return"-";const n=String(e);return n.length>=10?n.slice(0,10):n}function Za(e,n){return!e&&!n?"":(pt(e)||"?")+" ~ "+(pt(n)||"?")}function oe(e){return e==null?"":String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}async function hi(e){F.currentTxForDrawer=e;const n=document.getElementById("bank-detail-body");n&&n.classList.add("has-pane");const a=document.getElementById("bank-cand-pane-title"),o=document.getElementById("bank-cand-pane-sub"),s=document.getElementById("bank-cand-pane-foot");if(a&&(a.textContent=t("bank-cand-pane-current")),o){const r=e.direction==="OUT"?"-":"+",d=e.direction==="OUT"?"bank-out":"bank-in";o.innerHTML=`${oe(pt(e.tx_date))}
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <span>${oe(e.description||"-")}</span>
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <strong class="${d}">${r}${Xe(e.amount)}</strong>`}s&&(s.style.display="");const i=document.getElementById("bank-cand-pane-body");if(i){i.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const r=await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!r.ok)throw new Error("cands:"+r.status);const d=await r.json();bi(e,d.candidates||[])}catch{i.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function gi(e,n,a){const o=n.history_id,s=n.invoice_no||"-",i=n.vendor||"-",r=n.amount_total!==null&&n.amount_total!==void 0?Xe(n.amount_total):"-",d=n.invoice_date?pt(n.invoice_date):"-",m=n.filename||"",p=!!a&&e.matched_history_id===o,f="bank-cand-card"+(n.is_auto_picked?" is-auto":"")+(p?" is-picked":"");let c="";return p?c='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":c='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+oe(o)+'"><span>'+t(n.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+f+'" data-hid="'+oe(o)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+oe(i)+"</div>"+ui(n.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+oe(s)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+r+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+oe(d)+"</span></div>"+(m?'<div class="bank-cand-card-file" title="'+oe(m)+'">'+oe(m)+"</div>":"")+(n.reason?'<div class="bank-cand-card-reason">'+oe(n.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+c+"</div></div>"}function bi(e,n){const a=document.getElementById("bank-cand-pane-body");if(!a)return;const o=n||[];let s="";if(e.match_status==="matched")s='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",o.length)+"</div>";else if(e.match_status==="suggested")s='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",o.length)+"</div>";else if(o.length>0)s='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",o.length)+"</div>";else{a.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const i=e.match_status==="matched",r=o.map(d=>gi(e,d,i)).join("");a.innerHTML=s+'<div class="bank-cand-list">'+r+"</div>",a.querySelectorAll('[data-act="pick"]').forEach(d=>{d.addEventListener("click",()=>{ki(d.dataset.hid)})}),a.querySelectorAll('[data-act="unmatch"]').forEach(d=>{d.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),Ht(),await mt(F.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function Ht(){const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane");const n=document.getElementById("bank-cand-pane-title"),a=document.getElementById("bank-cand-pane-sub"),o=document.getElementById("bank-cand-pane-body"),s=document.getElementById("bank-cand-pane-foot");n&&(n.textContent=t("bank-cand-pane-empty-title")),a&&(a.textContent=t("bank-cand-pane-empty-sub")),s&&(s.style.display="none"),o&&(o.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const i=document.getElementById("bank-tx-tbody");i&&i.querySelectorAll("tr.is-selected").forEach(r=>r.classList.remove("is-selected")),F.currentTxForDrawer=null}async function mt(e){try{const n="/api/bank-recon/sessions/"+encodeURIComponent(e)+(F.currentFilter!=="all"?"?filter="+F.currentFilter:""),a=await fetch(n,{headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("detail:"+a.status);const o=await a.json();F.currentSession=o.session,F.currentTxs=o.transactions||[],Li()}catch(n){console.warn("[bank-recon] loadSessionDetail failed",n),showToast(t("bank-load-failed"),"error")}}async function yi(){if(!F.currentSession)return;const e=document.getElementById("btn-bank-run-match"),n=e.innerHTML;e.disabled=!0,e.innerHTML="<span>"+t("bank-matching")+"</span>";try{const a=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(F.currentSession.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("match:"+a.status);const o=await a.json();showToast(t("bank-match-done").replace("{matched}",o.matched).replace("{suggested}",o.suggested).replace("{unmatched}",o.unmatched),"success"),await mt(F.currentSession.id),await vt()}catch(a){console.warn("[bank-recon] match failed",a),showToast(t("bank-match-failed"),"error")}finally{e.disabled=!1,e.innerHTML=n}}async function wi(){if(!(!F.currentSession||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const n=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(F.currentSession.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!n.ok)throw new Error("delete:"+n.status);showToast(t("bank-deleted"),"success"),F.currentSession=null,F.currentTxs=[],Dn(),await vt()}catch(n){console.warn("[bank-recon] delete failed",n),showToast(t("bank-delete-failed"),"error")}}async function ca(){if(F.currentTxForDrawer)try{const e=await fetch("/api/bank-recon/tx/"+encodeURIComponent(F.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!e.ok)throw new Error("ignore:"+e.status);Ht(),await mt(F.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}async function ki(e){if(F.currentTxForDrawer)try{const n=await fetch("/api/bank-recon/tx/"+encodeURIComponent(F.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:e})});if(!n.ok)throw new Error("pick:"+n.status);showToast(t("bank-matched-ok"),"success"),Ht(),await mt(F.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}function Qa(){if(!F.currentSession)return;const e=F.currentSession;document.getElementById("bank-detail-title").textContent=(e.bank_code||"-")+(e.account_last4?" ···"+e.account_last4:"")+" · "+(e.source_filename||""),document.getElementById("bank-meta-period").textContent=Za(e.period_start,e.period_end)||"-",document.getElementById("bank-meta-opening").textContent=Xe(e.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+Xe(e.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+Xe(e.total_outflow),document.getElementById("bank-meta-closing").textContent=Xe(e.closing_balance);const n=F.currentTxs||[],a=n.length;let o=0,s=0,i=0;for(const r of n){const d=r.match_status||"unmatched";d==="matched"?o++:d==="suggested"?s++:i++}document.getElementById("bank-stat-total").textContent=a,document.getElementById("bank-stat-matched").textContent=o,document.getElementById("bank-stat-suggested").textContent=s,document.getElementById("bank-stat-unmatched").textContent=i}function jn(){const e=document.getElementById("bank-tx-tbody");if(!e)return;let n=F.currentTxs||[];if(F.currentFilter!=="all"&&(n=n.filter(a=>F.currentFilter==="matched"?a.match_status==="matched":F.currentFilter==="suggested"?a.match_status==="suggested":F.currentFilter==="unmatched"?a.match_status==="unmatched"||a.match_status==="ignored":!0)),n.length===0){e.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(e.innerHTML=n.map(a=>xi(a)).join(""),e.querySelectorAll("tr[data-tx-id]").forEach(a=>{a.addEventListener("click",()=>{const o=a.dataset.txId,s=F.currentTxs.find(i=>i.id===o);s&&(e.querySelectorAll("tr.is-selected").forEach(i=>i.classList.remove("is-selected")),a.classList.add("is-selected"),hi(s))})}),F.currentTxForDrawer){const a=e.querySelector('tr[data-tx-id="'+F.currentTxForDrawer.id+'"]');a&&a.classList.add("is-selected")}}function xi(e){const n=e.direction==="OUT",a=n?"-":"+",o=n?"bank-out":"bank-in",s=e.match_status||"unmatched",i=t("bank-match-"+s)||s,r=pt(e.tx_date),d=e.channel?`<span class="bank-tx-channel">${oe(e.channel)}</span>`:"";return`
        <tr data-tx-id="${oe(e.id)}">
            <td class="bank-tx-date">${oe(r)}</td>
            <td class="bank-tx-desc">${d}${oe(e.description||"-")}</td>
            <td class="bank-td-amount ${o}">${a}${Xe(e.amount)}</td>
            <td><span class="bank-tx-match mt-${s}">${oe(i)}</span></td>
        </tr>
    `}function Pn(){const e=document.getElementById("bank-client-badge");if(!e||!F.currentSession)return;const n=F.currentSession.client_id,a=document.getElementById("bank-client-badge-dot"),o=document.getElementById("bank-client-badge-name"),s=document.getElementById("bank-client-badge-caret"),i=typeof _userInfo<"u"?_userInfo:null,r=!(i&&i.role==="member");if(n!=null){const d=(window._clientsCache||[]).find(m=>Number(m.id)===Number(n));e.classList.remove("is-empty"),a&&(a.style.background=d&&d.color||"#111111"),o&&(o.textContent=d&&(d.short_name||d.name)||"#"+n)}else e.classList.add("is-empty"),a&&(a.style.background=""),o&&(o.textContent=t("bank-client-none"));r?(e.classList.remove("is-readonly"),e.disabled=!1,s&&(s.style.display="")):(e.classList.add("is-readonly"),e.disabled=!0,s&&(s.style.display="none")),e.style.display=""}function _i(){if(!F.currentSession)return;const e=typeof _userInfo<"u"?_userInfo:null;if(!!(e&&e.role==="member"))return;F.pickerSelected=F.currentSession.client_id!=null?Number(F.currentSession.client_id):null,to();const a=document.getElementById("bank-client-picker-modal");a&&(a.style.display="")}function eo(){const e=document.getElementById("bank-client-picker-modal");e&&(e.style.display="none"),F.pickerSelected=null}function to(){const e=document.getElementById("bank-client-picker-list");if(!e)return;const n=(window._clientsCache||[]).filter(o=>o&&(o.is_active===!0||o.is_active===void 0)),a=[];a.push('<div class="bank-client-picker-row is-none'+(F.pickerSelected==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+oe(t("bank-client-picker-none"))+"</span></div>"),n.forEach(o=>{const s=Number(o.id)===Number(F.pickerSelected)?" is-selected":"";a.push('<div class="bank-client-picker-row'+s+'" data-cid="'+oe(o.id)+'"><span class="bank-cp-dot" style="background:'+oe(o.color||"#111111")+'"></span><span>'+oe(o.short_name||o.name||"#"+o.id)+"</span></div>")}),e.innerHTML=a.join(""),e.querySelectorAll(".bank-client-picker-row").forEach(o=>{o.addEventListener("click",()=>{const s=o.dataset.cid;F.pickerSelected=s?Number(s):null,to()})})}async function Ei(){if(F.currentSession)try{const e=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(F.currentSession.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:F.pickerSelected})});if(!e.ok)throw new Error("client:"+e.status);F.currentSession.client_id=F.pickerSelected,Pn(),showToast(t("bank-client-changed"),"success"),eo();try{await vt()}catch{}}catch(e){console.warn("[bank-recon] save client failed",e),showToast(t("bank-client-change-failed"),"error")}}async function vt(){try{const e=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!e.ok)throw new Error("sessions:"+e.status);F.sessions=await e.json(),Gt()}catch(e){console.warn("[bank-recon] loadSessions failed",e),F.sessions=[],Gt()}}function da(){const e=document.getElementById("bank-status-summary");if(!e)return;if(F.sessions.length===0){e.textContent=t("bank-pill-none");return}let a=0;for(const o of F.sessions)o.parse_status==="parsed"&&(o.unmatched_count||0)>0&&a++;e.textContent=a>0?t("bank-pill-pending").replace("{n}",a):t("bank-pill-ok")}function Gt(){const e=document.getElementById("bank-sessions-list");if(!e)return;let n=F.sessions||[];if(F.sessionFilter==="parsed"?n=n.filter(a=>a.parse_status==="parsed"):F.sessionFilter==="failed"&&(n=n.filter(a=>a.parse_status==="parse_failed")),!F.sessions||F.sessions.length===0){e.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(n.length===0){e.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}e.innerHTML=n.map(a=>Bi(a)).join(""),e.querySelectorAll(".bank-session-row").forEach(a=>{a.addEventListener("click",o=>{o.target.closest(".bank-session-trash")||mt(a.dataset.sessionId)})}),e.querySelectorAll(".bank-session-trash").forEach(a=>{a.addEventListener("click",o=>{o.stopPropagation();const s=a.dataset.sessionId,i=a.dataset.sessionName||"";no(s,i)})})}async function no(e,n){if(!e)return;const a=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",n||"");if(await showConfirm(a,{danger:!0}))try{const s=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(e),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!s.ok)throw new Error("delete:"+s.status);showToast(t("bank-deleted"),"success"),F.currentSession&&F.currentSession.id===e&&(F.currentSession=null,F.currentTxs=[],Dn()),await vt(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(s){console.warn("[bank-recon] delete failed",s),showToast(t("bank-delete-failed"),"error")}}function Bi(e){const n=(e.bank_code||"OTHER").toUpperCase(),a=Za(e.period_start,e.period_end),o=e.account_last4?"···"+e.account_last4:"",s=Ii(e),i=pt(e.created_at);return`
        <div class="bank-session-row" data-session-id="${oe(e.id)}">
            <div class="bank-session-bank bk-${oe(n)}">${oe(n)}</div>
            <div class="bank-session-info">
                <div class="bank-session-title">${oe(e.source_filename||a||"-")}</div>
                <div class="bank-session-meta">${oe(a)} · ${oe(o)} · ${oe(i)}</div>
            </div>
            <div class="bank-session-counts">${s}</div>
            <button class="bank-session-trash" data-session-id="${oe(e.id)}" data-session-name="${oe(e.source_filename||"")}" title="${oe(t("bank-session-delete-tip")||"删除")}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                </svg>
            </button>
            <div class="bank-session-arrow">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
            </div>
        </div>
    `}function Ii(e){if(e.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(e.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const n=e.tx_count||0,a=e.matched_count||0,o=e.unmatched_count||0,s=[`<span class="bank-session-count">${n} ${t("bank-count-tx")}</span>`];return a>0&&s.push(`<span class="bank-session-count cnt-matched">${a} ${t("bank-count-matched")}</span>`),o>0&&s.push(`<span class="bank-session-count cnt-unmatched">${o} ${t("bank-count-unmatched")}</span>`),s.join("")}function Li(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",Qa(),jn(),Pn()}function Dn(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane"),F.currentTxForDrawer=null}const Ci=3;function Si(){return F.qSeq+=1,"q"+F.qSeq+"_"+Date.now()}async function Ti(e){const n=Array.from(e.target.files||[]);if(e.target.value="",n.length!==0){for(const a of n){const o={id:Si(),file:a,name:a.name,size:a.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};a.name.toLowerCase().endsWith(".pdf")?a.size>20*1024*1024&&(o.status="failed",o.error_code="bank_recon.file_too_large"):(o.status="failed",o.error_code="bank_recon.only_pdf"),F.queue.push(o)}Mi(),Ie(),qn()}}function Mi(){const e=document.getElementById("bank-upload-queue");e&&(e.style.display=""),fi(),mi()}function Ie(){const e=document.getElementById("bank-upload-queue-list"),n=document.getElementById("bank-upload-queue-summary");if(!e)return;if(F.queue.length===0){e.innerHTML="",n&&(n.textContent="");const r=document.getElementById("bank-upload-queue");r&&(r.style.display="none");return}let a=0,o=0,s=0,i=0;for(const r of F.queue)r.status==="ok"?a++:r.status==="failed"?o++:r.status==="uploading"||r.status==="parsing"?s++:i++;n&&(n.textContent=t("bank-queue-summary").replace("{ok}",a).replace("{run}",s).replace("{wait}",i).replace("{fail}",o)),e.innerHTML=F.queue.map($i).join(""),e.querySelectorAll("[data-q-act]").forEach(r=>{const d=r.dataset.qAct,m=r.dataset.qId;r.addEventListener("click",()=>{d==="retry"&&Hi(m),d==="remove"&&Ai(m)})})}function $i(e){const n=(e.size/1024).toFixed(0)+" KB";let a="",o="";if(e.status==="pending")a='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",o='<button data-q-act="remove" data-q-id="'+oe(e.id)+'" class="bq-act">×</button>';else if(e.status==="uploading")a='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(e.progress||0)+'%"></div></div>';else if(e.status==="parsing")a='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(e.status==="ok")a='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",e.tx_count||0)+"</span>",o='<button data-q-act="remove" data-q-id="'+oe(e.id)+'" class="bq-act">×</button>';else if(e.status==="failed"){const s=vi(e.error_code||"unknown");a='<span class="bq-stat bq-fail" title="'+oe(s)+'">'+oe(s)+"</span>",o='<button data-q-act="retry" data-q-id="'+oe(e.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+oe(e.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+oe(e.id)+'"><div class="bq-name" title="'+oe(e.name)+'">'+oe(e.name)+'</div><div class="bq-size">'+n+'</div><div class="bq-status">'+a+'</div><div class="bq-actions">'+o+"</div></div>"}function Hi(e){const n=F.queue.find(a=>a.id===e);n&&(n.status="pending",n.error_code=null,n.progress=0,Ie(),qn())}function Ai(e){const n=F.queue.findIndex(o=>o.id===e);if(n<0)return;const a=F.queue[n];a.status==="uploading"||a.status==="parsing"||(F.queue.splice(n,1),Ie())}function ji(){F.queue=F.queue.filter(e=>e.status!=="ok"),Ie()}async function qn(){for(;;){if(F.queue.filter(a=>a.status==="uploading"||a.status==="parsing").length>=Ci)return;const n=F.queue.find(a=>a.status==="pending");if(!n){F.queue.every(a=>a.status==="ok"||a.status==="failed")&&(await vt(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}Pi(n).then(()=>qn())}}async function Pi(e){e.status="uploading",e.progress=0,Ie();try{const n=new FormData;n.append("file",e.file,e.name);const a=await new Promise((s,i)=>{const r=new XMLHttpRequest;r.open("POST","/api/bank-recon/upload"),r.setRequestHeader("Authorization","Bearer "+token),r.upload.onprogress=d=>{d.lengthComputable&&(e.progress=Math.min(99,Math.round(d.loaded/d.total*100)),Ie())},r.upload.onload=()=>{e.status="parsing",Ie()},r.onload=()=>{r.status>=200&&r.status<300?s({status:r.status,text:r.responseText}):s({status:r.status,text:r.responseText})},r.onerror=()=>i(new Error("network")),r.send(n)});let o={};try{o=JSON.parse(a.text||"{}")}catch{o={}}if(a.status>=400){e.status="failed",e.error_code=o&&o.detail||"unknown",Ie();return}if(o.parse_status==="parse_failed"){e.status="failed",e.error_code=o.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",Ie();return}e.status="ok",e.tx_count=o.tx_count||0,e.session_id=o.session_id||null,Ie()}catch(n){console.warn("[bank-recon] upload failed",n),e.status="failed",e.error_code="network",Ie()}}async function ao(){if(F.loaded){da();return}F.loaded=!0,Di(),await vt(),da()}function Di(){const e=document.getElementById("bank-file-input");e&&!e._bound&&(e._bound=!0,e.addEventListener("change",Ti));const n=document.getElementById("btn-bank-queue-clear-done");n&&!n._bound&&(n._bound=!0,n.addEventListener("click",ji));const a=document.getElementById("btn-bank-back");a&&!a._bound&&(a._bound=!0,a.addEventListener("click",()=>{F.currentSession=null,F.currentTxs=[],Dn()}));const o=document.getElementById("btn-bank-delete");o&&!o._bound&&(o._bound=!0,o.addEventListener("click",wi));const s=document.getElementById("btn-bank-run-match");s&&!s._bound&&(s._bound=!0,s.addEventListener("click",yi)),document.querySelectorAll(".bank-filter-btn").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",()=>{F.currentFilter=f.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(c=>{c.classList.toggle("active",c===f)}),jn()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",Ht))});const i=document.getElementById("btn-bank-cand-pane-close");i&&!i._bound&&(i._bound=!0,i.addEventListener("click",Ht));const r=document.getElementById("btn-bank-cand-ignore");r&&!r._bound&&(r._bound=!0,r.addEventListener("click",ca));const d=document.getElementById("btn-bank-cand-ignore-pane");d&&!d._bound&&(d._bound=!0,d.addEventListener("click",ca));const m=document.getElementById("bank-client-badge");m&&!m._bound&&(m._bound=!0,m.addEventListener("click",_i)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",eo))});const p=document.getElementById("btn-bank-client-picker-save");p&&!p._bound&&(p._bound=!0,p.addEventListener("click",Ei)),document.querySelectorAll(".bank-sessions-chip").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",()=>{F.sessionFilter=f.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(c=>{c.classList.toggle("active",c===f)}),Gt()}))})}window._deleteBankSession=no;window._loadBankReconPanel=ao;window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(Gt(),F.currentSession&&(Qa(),jn(),Pn(),!F.currentTxForDrawer)){const e=document.getElementById("bank-cand-pane-title"),n=document.getElementById("bank-cand-pane-sub");e&&(e.textContent=t("bank-cand-pane-empty-title")),n&&(n.textContent=t("bank-cand-pane-empty-sub"))}Ie()}};typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon);window._openBankSession=async function(e){e&&(F.loaded||await ao(),await mt(e))};(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const qi=`
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
    `,Ri=`
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
    `;ke("client-modal-mask",qi);ke("wsclient-modal-mask",Ri);const Q={clients:[],editingClientId:null,historyClientFilter:"",custTab:"seller",sellerClients:[],editingWsClientId:null,catCache:{fetched:0,items:[],supplier_count:0}},we={page:0,pageSize:12,keyword:""},je=new Set,Kt={keyword:""};function Fi(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function Te(e,n={}){const a=await fetch(e,{...n,headers:{"Content-Type":"application/json",...Fi(),...n.headers||{}}});if(!a.ok){const o=await a.json().catch(()=>({}));throw new Error(o.detail||"HTTP "+a.status)}return a.json()}function zi(){const e=document.querySelector("#client-color-picker .color-swatch.active");return e?e.dataset.color:"#111111"}function pa(e){const n=document.getElementById("drawer-cat-learned-tag");n&&e>0&&(n.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",e))}async function ht(){try{const e=await Te("/api/clients");Q.clients=e.clients||[],window._clientsCache=Q.clients}catch(e){console.error("loadClientsCache fail",e),Q.clients=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return Q.clients}function Ni(){const e=we.keyword.trim().toLowerCase();return e?Q.clients.filter(n=>(n.name||"").toLowerCase().includes(e)||(n.short_name||"").toLowerCase().includes(e)||(n.tax_id||"").toLowerCase().includes(e)):Q.clients}function Rn(){const e=Ni(),n=we.pageSize,a=Math.max(0,Math.ceil(e.length/n)-1);we.page>a&&(we.page=a);const o=we.page*n;return{all:e,items:e.slice(o,o+n),start:o,ps:n,total:e.length,maxPage:a}}function Ae(){const e=document.getElementById("buyer-tbody");if(!e)return;const{items:n,start:a,ps:o,total:s,maxPage:i}=Rn();s?e.innerHTML=n.map(p=>{const f=je.has(p.id);return`<div class="cust-row buyer-grid${f?" selected":""}" data-cid="${p.id}">
                <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${p.id}" ${f?"checked":""}></div>
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
            </div>`}).join(""):e.innerHTML=`<div class="cust-empty">${escapeHtml(t(we.keyword?"cust-no-match":"clients-empty"))}</div>`;const r=document.getElementById("buyer-pager-info");r&&(r.textContent=s?`${a+1}–${Math.min(a+o,s)} / ${s}`:"0");const d=document.getElementById("buyer-prev");d&&(d.disabled=we.page<=0);const m=document.getElementById("buyer-next");m&&(m.disabled=we.page>=i),oo()}function oo(){const e=je.size,n=document.getElementById("buyer-batch-bar");n&&(n.style.display=e?"flex":"none");const a=document.getElementById("buyer-batch-count");a&&(a.textContent=t("cust-selected-n").replace("{n}",e));const o=document.getElementById("buyer-check-all");if(o){const{items:s}=Rn(),i=s.map(d=>d.id),r=i.filter(d=>je.has(d)).length;o.checked=i.length>0&&r===i.length,o.indeterminate=r>0&&r<i.length}}function Oi(){je.clear(),Ae()}async function Vi(){const e=Array.from(je);if(!(!e.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",e.length),{danger:!0})))try{await Te("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:e})}),showToast(t("client-msg-deleted"),"success"),je.clear(),await ht(),Ae(),on(),Fn()}catch{showToast(t("client-msg-save-fail"),"fail")}}function It(e){Q.editingClientId=e?e.id:null;const n=!!e;document.getElementById("client-modal-title").textContent=t(n?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=e&&e.name||"",document.getElementById("client-input-short").value=e&&e.short_name||"",document.getElementById("client-input-tax").value=e&&e.tax_id||"",document.getElementById("client-input-address").value=e&&e.address||"",document.getElementById("client-input-contact").value=e&&e.contact_person||"",document.getElementById("client-input-phone").value=e&&e.contact_phone||"",document.getElementById("client-input-email").value=e&&e.contact_email||"",document.getElementById("client-input-notes").value=e&&e.notes||"";const a=e&&e.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(o=>{o.classList.toggle("active",o.dataset.color===a)}),document.getElementById("client-modal-delete").style.display=n?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function Lt(){document.getElementById("client-modal-mask").style.display="none",Q.editingClientId=null}async function Ui(){const e=document.getElementById("client-input-name").value.trim();if(!e){showToast(t("client-msg-name-required"),"fail");return}const n={name:e,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:zi()};try{Q.editingClientId?(await Te(`/api/clients/${Q.editingClientId}`,{method:"PATCH",body:JSON.stringify(n)}),showToast(t("client-msg-updated"),"success")):(await Te("/api/clients",{method:"POST",body:JSON.stringify(n)}),showToast(t("client-msg-created"),"success")),Lt(),await ht(),currentRoute==="clients"&&Ae(),on(),Fn()}catch(a){console.error("saveClient fail",a);const o=a&&a.message?a.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+o,"fail")}}async function Gi(){if(!Q.editingClientId)return;const e=Q.clients.find(o=>o.id===Q.editingClientId);if(!e)return;const n=t("client-delete-confirm").replace("{name}",e.name);if(await showConfirm(n,{danger:!0}))try{await Te(`/api/clients/${Q.editingClientId}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),Lt(),await ht(),currentRoute==="clients"&&Ae(),on(),Fn()}catch(o){console.error(o),showToast(t("client-msg-save-fail"),"fail")}}async function Ki(e){const n=Q.clients.find(a=>a.id===e);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(e,n?n.name:"");return}try{const a=localStorage.getItem("mrpilot_token"),o=await fetch(`/api/clients/${e}/export?month=all`,{headers:{Authorization:"Bearer "+a}});if(!o.ok){let m="HTTP "+o.status;try{const p=await o.json();p&&p.detail&&(m=p.detail)}catch{}throw new Error(m)}const s=await o.blob();if(s.size<200){showToast(t("client-export-month-empty"),"info");return}const i=n&&n.name?n.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",r=URL.createObjectURL(s),d=document.createElement("a");d.href=r,d.download=`${i}_export.csv`,d.click(),URL.revokeObjectURL(r)}catch(a){console.error("exportClient fail",a),showToast(t("client-msg-save-fail")+" · "+(a.message||""),"fail")}}function on(){const e=document.getElementById("drawer-client-select");if(!e)return;const n=e.value;e.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+Q.clients.map(a=>`<option value="${a.id}">${escapeHtml(a.name)}</option>`).join(""),e.value=n||""}function Fn(){const e=document.getElementById("history-client-filter");if(!e)return;const n=e.value;e.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+Q.clients.map(a=>`<option value="${a.id}">${escapeHtml(a.name)}</option>`).join(""),e.value=n||""}function Ji(e){Q.custTab=e==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(o=>o.classList.toggle("active",o.dataset.custTab===Q.custTab));const n=document.getElementById("cust-pane-seller"),a=document.getElementById("cust-pane-buyer");n&&n.classList.toggle("active",Q.custTab==="seller"),a&&a.classList.toggle("active",Q.custTab==="buyer")}function Wi(){const e=window._userInfo||{},n=String(e.role||"").toLowerCase(),a=String(e.tenant_role||"").toLowerCase();return e.is_super_admin===!0||e.is_owner===!0||n==="owner"||n==="admin"||a==="owner"||a==="admin"}function so(){window._workspaceClientsCache=Q.sellerClients,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function zn(){try{const e=await Te("/api/workspace/clients");Q.sellerClients=e&&(e.clients||e.items)||[],window._workspaceClientsCache=Q.sellerClients}catch(e){console.error("loadSellerCache fail",e),Q.sellerClients=[]}return Q.sellerClients}function Yi(){const e=Kt.keyword.trim().toLowerCase();return e?Q.sellerClients.filter(n=>(n.name||"").toLowerCase().includes(e)||(n.tax_id||"").toLowerCase().includes(e)):Q.sellerClients}function Ze(){const e=document.getElementById("seller-tbody");if(!e)return;const n=Wi(),a=document.getElementById("btn-seller-new");a&&(a.style.display=n?"":"none");const o=Yi(),s=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!o.length){e.innerHTML=`<div class="cust-empty">${escapeHtml(t(Kt.keyword?"cust-no-match":"seller-empty"))}</div>`;return}e.innerHTML=o.map(i=>{const d=s!=null&&Number(s)===Number(i.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${i.id}">${escapeHtml(t("seller-set-current"))}</button>`,m=n?`
            <button class="cust-row-btn" data-saction="edit" data-wid="${i.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
            <button class="cust-row-btn danger" data-saction="archive" data-wid="${i.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${i.id}">
            <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(i.name||"#"+i.id)}</span></div>
            <div class="cust-cell-tax">${escapeHtml(i.tax_id||"—")}</div>
            <div class="align-right">${i.invoice_count||0}</div>
            <div class="cust-row-actions">${d}${m}</div>
        </div>`}).join("")}function ua(e){Q.editingWsClientId=e?e.id:null,document.getElementById("wsclient-modal-title").textContent=t(e?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=e&&e.name||"",document.getElementById("wsclient-input-tax").value=e&&e.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=e?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function Ct(){document.getElementById("wsclient-modal-mask").style.display="none",Q.editingWsClientId=null}async function Xi(){const e=document.getElementById("wsclient-input-name").value.trim(),n=document.getElementById("wsclient-input-tax").value.trim();if(!e){showToast(t("client-msg-name-required"),"fail");return}try{Q.editingWsClientId?(await Te("/api/workspace/clients/"+Q.editingWsClientId,{method:"PATCH",body:JSON.stringify({name:e,tax_id:n})}),showToast(t("client-msg-updated"),"success")):(await Te("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:e,tax_id:n||null})}),showToast(t("client-msg-created"),"success")),Ct(),await zn(),Ze(),so()}catch(a){const o=a&&a.message?a.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+o,"fail")}}async function fa(){if(!Q.editingWsClientId)return;const e=Q.sellerClients.find(a=>Number(a.id)===Number(Q.editingWsClientId));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",e?e.name:""),{danger:!0}))try{const a=Q.editingWsClientId;await Te("/api/workspace/clients/"+a,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(a)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),Ct(),await zn(),Ze(),so()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const e=document.getElementById("seller-tbody");e&&(e.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const n=document.getElementById("buyer-tbody");n&&(n.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([zn(),ht()]),Ze(),Ae()};window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&Ze()});window.bindDrawerClient=function(e,n){const a=document.getElementById("drawer-client-select");if(!a)return;if(on(),a.value=n?String(n):"",!e){a.onchange=null;const s=document.getElementById("drawer-client-add");s&&(s.onclick=()=>It(null));return}a.onchange=async()=>{const s=a.value?parseInt(a.value,10):null;try{await Te(`/api/history/${e}/assign_client`,{method:"POST",body:JSON.stringify({client_id:s})}),showToast(t("client-msg-updated"),"success");const i=_results[_drawerIdx];i&&(i.client_id=s),await ht()}catch(i){console.error(i),showToast(t("client-msg-save-fail"),"fail"),a.value=n?String(n):""}};const o=document.getElementById("drawer-client-add");o&&(o.onclick=()=>It(null))};window.fillCategoryDatalist=async function(){try{const e=document.getElementById("drawer-cat-datalist"),n=Date.now();if(n-Q.catCache.fetched<300*1e3){e&&(e.innerHTML=Q.catCache.items.map(o=>`<option value="${escapeHtml(o)}">`).join("")),pa(Q.catCache.supplier_count);return}const a=await Te("/api/categories",{method:"GET"});Q.catCache.fetched=n,Q.catCache.items=a&&a.categories||[],Q.catCache.supplier_count=a&&a.supplier_count||0,e&&(e.innerHTML=Q.catCache.items.map(o=>`<option value="${escapeHtml(o)}">`).join("")),pa(Q.catCache.supplier_count)}catch(e){console.warn("fillCategoryDatalist failed",e)}};window.getHistoryClientFilter=function(){return Q.historyClientFilter};document.addEventListener("DOMContentLoaded",()=>{const e=document.querySelector(".cust-tab-bar");e&&e.addEventListener("click",L=>{const C=L.target.closest("[data-cust-tab]");C&&Ji(C.dataset.custTab)});const n=document.getElementById("btn-buyer-new");n&&n.addEventListener("click",()=>It(null));const a=document.getElementById("buyer-tbody");a&&a.addEventListener("click",L=>{const C=L.target.closest(".buyer-row-check");if(C){const $=parseInt(C.dataset.cid,10);C.checked?je.add($):je.delete($);const q=C.closest(".cust-row");q&&q.classList.toggle("selected",C.checked),oo();return}const S=L.target.closest(".cust-row-btn");if(S){L.stopPropagation();const $=parseInt(S.dataset.cid,10);if(S.dataset.action==="edit"){const q=Q.clients.find(H=>H.id===$);q&&It(q)}else S.dataset.action==="export"&&Ki($);return}const M=L.target.closest(".cust-row");if(M&&!L.target.closest(".cust-cell-check")){const $=Q.clients.find(q=>q.id===parseInt(M.dataset.cid,10));$&&It($)}});const o=document.getElementById("buyer-check-all");o&&o.addEventListener("change",()=>{const{items:L}=Rn();L.forEach(C=>{o.checked?je.add(C.id):je.delete(C.id)}),Ae()});const s=document.getElementById("buyer-batch-cancel");s&&s.addEventListener("click",Oi);const i=document.getElementById("buyer-batch-delete");i&&i.addEventListener("click",Vi);const r=document.getElementById("buyer-prev");r&&r.addEventListener("click",()=>{we.page>0&&(we.page--,Ae())});const d=document.getElementById("buyer-next");d&&d.addEventListener("click",()=>{we.page++,Ae()});const m=document.getElementById("buyer-search");if(m){let L;m.addEventListener("input",()=>{clearTimeout(L),L=setTimeout(()=>{we.keyword=m.value,we.page=0;const C=document.getElementById("buyer-search-clear");C&&(C.style.display=m.value?"":"none"),Ae()},200)})}const p=document.getElementById("buyer-search-clear");p&&p.addEventListener("click",()=>{const L=document.getElementById("buyer-search");L&&(L.value=""),we.keyword="",we.page=0,p.style.display="none",Ae()});const f=document.getElementById("btn-seller-new");f&&f.addEventListener("click",()=>ua(null));const c=document.getElementById("seller-tbody");c&&c.addEventListener("click",L=>{const C=L.target.closest("[data-saction]");if(!C)return;L.stopPropagation();const S=parseInt(C.dataset.wid,10),M=C.dataset.saction,$=Q.sellerClients.find(q=>Number(q.id)===S);M==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(S),Ze(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",$?$.name:""),"success")):M==="edit"?$&&ua($):M==="archive"&&(Q.editingWsClientId=S,fa())});const l=document.getElementById("seller-search");if(l){let L;l.addEventListener("input",()=>{clearTimeout(L),L=setTimeout(()=>{Kt.keyword=l.value;const C=document.getElementById("seller-search-clear");C&&(C.style.display=l.value?"":"none"),Ze()},200)})}const u=document.getElementById("seller-search-clear");u&&u.addEventListener("click",()=>{const L=document.getElementById("seller-search");L&&(L.value=""),Kt.keyword="",u.style.display="none",Ze()});const v=document.getElementById("wsclient-modal-close");v&&v.addEventListener("click",Ct);const w=document.getElementById("wsclient-modal-cancel");w&&w.addEventListener("click",Ct);const b=document.getElementById("wsclient-modal-save");b&&b.addEventListener("click",Xi);const g=document.getElementById("wsclient-modal-archive");g&&g.addEventListener("click",fa);const h=document.getElementById("wsclient-modal-mask");h&&h.addEventListener("click",L=>{L.target===h&&Ct()});const I=document.getElementById("client-modal-close");I&&I.addEventListener("click",Lt);const y=document.getElementById("client-modal-cancel");y&&y.addEventListener("click",Lt);const x=document.getElementById("client-modal-save");x&&x.addEventListener("click",Ui);const E=document.getElementById("client-modal-delete");E&&E.addEventListener("click",Gi);const _=document.getElementById("client-modal-mask");_&&_.addEventListener("click",L=>{L.target===_&&Lt()});const k=document.getElementById("client-color-picker");k&&k.addEventListener("click",L=>{const C=L.target.closest(".color-swatch");C&&(k.querySelectorAll(".color-swatch").forEach(S=>S.classList.remove("active")),C.classList.add("active"))});const B=document.getElementById("history-client-filter");B&&B.addEventListener("change",()=>{Q.historyClientFilter=B.value,typeof renderHistoryList=="function"&&renderHistoryList()})});setTimeout(()=>ht(),1e3);(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const V={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0},K={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null},it={batchLoading:!1};function Ve(e,n){let a=t(e)||e;if(n)for(const o in n)a=a.replace(new RegExp("\\{"+o+"\\}","g"),String(n[o]));return a}function Zi(e){return e==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
    </svg>`}function Qi(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 19l5 5 13-13"/>
        <circle cx="20" cy="20" r="17"/>
    </svg>`}function er(e){if(e==null)return"—";const n=parseFloat(e);return isNaN(n)?"—":"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function tr(e){return e?e.slice(0,10):"—"}function at(e){if(e==null)return"—";const n=typeof e=="number"?e:parseFloat(String(e).replace(/,/g,""));return isNaN(n)?escapeHtml(String(e)):"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function nr(e){if(!e)return"—";try{const n=new Date(e),a=o=>String(o).padStart(2,"0");return`${n.getFullYear()}-${a(n.getMonth()+1)}-${a(n.getDate())} ${a(n.getHours())}:${a(n.getMinutes())}`}catch{return e.slice(0,16).replace("T"," ")}}function ar(e,n){if(n=n||{},e==="math_mismatch")return`
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(at(n.subtotal))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(at(n.vat))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(at(n.total_expected))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(at(n.total_actual))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(at(n.diff))}</span></div>
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
        `:e==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(n))}</span></div>`}function Re(){const e=K.excRow;if(!e)return;const n=e.seller_name&&e.seller_name.trim()?e.seller_name:t("exc-no-seller"),a=e.filename||"—";document.getElementById("exc-drawer-title").textContent=a;const o="exc-status-"+(e.status||"pending"),s=t(o)||e.status,i="s-"+(e.status||"pending"),r=(e.invoice_date||e.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
        <span>${escapeHtml(n)}</span>
        ${e.invoice_no?`<span>· ${escapeHtml(e.invoice_no)}</span>`:""}
        ${r?`<span>· ${escapeHtml(r)}</span>`:""}
        <span class="exc-status-chip ${i}">${escapeHtml(s)}</span>
    `;const d=e.severity||"medium",m=t("exc-rule-"+e.rule_code)||e.rule_code,p=ar(e.rule_code,e.detail||{}),f=ma(K.history),c=K.history===null,l=K.history&&K.history._err,u=new Set;e.rule_code==="math_mismatch"?(u.add("subtotal"),u.add("vat"),u.add("total_amount")):e.rule_code==="tax_id_format_invalid"?u.add("seller_tax"):e.rule_code==="amount_missing"&&(u.add("total_amount"),u.add("invoice_number"));const v=!!K.editing,w=K.editFields||{},b=(S,M,$)=>{if(c)return`<div class="exc-field-row"><label>${escapeHtml(t(M))}</label><span class="val empty">…</span></div>`;const q=v?w[S]!==void 0?w[S]:f[S]!==void 0&&f[S]!==null?f[S]:"":f[S],H=u.has(S)?"flagged":"";if(v){const O=$?"number":"text",P=$?' step="0.01" inputmode="decimal"':"",j=q==null?"":String(q).replace(/"/g,"&quot;");return`<div class="exc-field-row ${H} editing">
                <label>${escapeHtml(t(M))}</label>
                <input class="exc-field-input" type="${O}"${P} data-edit-key="${escapeHtml(S)}" value="${j}">
            </div>`}const T=$?at(q):q||"",D=q==null||q===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(T)}</span>`;return`<div class="exc-field-row ${H}"><label>${escapeHtml(t(M))}</label>${D}</div>`};let g="";l?g=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:g=`
            <div class="exc-fields">
                ${b("invoice_number","exc-fld-invoice-no",!1)}
                ${b("date","exc-fld-date",!1)}
                ${b("seller_name","exc-fld-seller",!1)}
                ${b("seller_tax","exc-fld-seller-tax",!1)}
                ${b("buyer_name","exc-fld-buyer",!1)}
                ${b("buyer_tax","exc-fld-buyer-tax",!1)}
                ${b("subtotal","exc-fld-subtotal",!0)}
                ${b("vat","exc-fld-vat",!0)}
                ${b("total_amount","exc-fld-total",!0)}
            </div>
        `;const h=(()=>{if(K.pdfStatus==="loading"||K.pdfStatus==="idle")return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M18 4v8a14 14 0 1014 14"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                </div>
            `;if(K.pdfStatus==="empty")return`
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
            `;if(K.pdfStatus==="error")return`
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
            `;const S=K.pdfUrl;return`
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
                <div class="exc-why sev-${escapeHtml(d)}">
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
                    ${e.status==="pending"&&!c&&!l?v?`
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
                ${g}
            </div>
        </div>
    `;const I=document.getElementById("exc-fld-edit");I&&I.addEventListener("click",()=>{K.editing=!0,K.editFields={...ma(K.history)},Re()});const y=document.getElementById("exc-fld-cancel");y&&y.addEventListener("click",()=>{K.editing=!1,K.editFields=null,Re()});const x=document.getElementById("exc-fld-save");x&&x.addEventListener("click",()=>ir()),document.querySelectorAll(".exc-field-input").forEach(S=>{S.addEventListener("input",()=>{K.editFields||(K.editFields={}),K.editFields[S.dataset.editKey]=S.value})});const _=document.getElementById("exc-pdf-retry");_&&K.openExcId&&_.addEventListener("click",()=>{K.excRow&&io(K.excRow.history_id,K.openExcId)});const k=e.status==="pending",B=!!(e.seller_name&&e.seller_name.trim()),L=document.getElementById("exc-btn-resolve"),C=document.getElementById("exc-btn-ignore");L.disabled=!k,C.disabled=!k||!B,C.title=B?t("exc-ignore-hint"):t("exc-ignore-no-seller")}function Nn(){if(K.pdfUrl){try{URL.revokeObjectURL(K.pdfUrl)}catch{}K.pdfUrl=null}K.pdfStatus="idle"}async function io(e,n){K.pdfStatus="loading",Re();try{const a=await fetch("/api/history/"+encodeURIComponent(e)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(K.openExcId!==n)return;if(a.status===404){K.pdfStatus="empty",Re();return}if(!a.ok)throw new Error("http "+a.status);const o=await a.blob();if(K.openExcId!==n)return;Nn(),K.pdfUrl=URL.createObjectURL(o),K.pdfStatus="ready",Re()}catch(a){if(K.openExcId!==n)return;console.warn("loadDrawerPdf fail",a),K.pdfStatus="error",Re()}}function or(e){const n=(V.listCache||[]).find(a=>a.id===e);if(!n){showToast(t("exc-drawer-error"),"error");return}V.listScrollY=window.scrollY||document.documentElement.scrollTop||0,Nn(),K.editing=!1,K.editFields=null,K.openExcId=e,K.excRow=n,K.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),Re(),sr(n.history_id),io(n.history_id,e)}function ut(){Nn(),K.editing=!1,K.editFields=null,K.openExcId=null,K.excRow=null,K.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const e=V.listScrollY||0;e>0&&requestAnimationFrame(()=>window.scrollTo(0,e))}async function sr(e){try{const n=await fetch("/api/history/"+encodeURIComponent(e),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);K.history=await n.json()}catch(n){console.warn("loadHistoryDetail fail",n),K.history={_err:!0}}K.excRow&&Re()}function ma(e){if(!e||!e.pages)return{};const n=e.pages,a=n.find(o=>!o.is_duplicate&&!o.is_copy)||n[0];return a&&a.fields||{}}async function ir(){if(!K.openExcId||!K.history||!K.history.pages||K.loading)return;K.loading=!0;const e=showToast(t("exc-fld-saving"),"loading",0);try{const n=JSON.parse(JSON.stringify(K.history.pages||[]));let a=n.findIndex(m=>!m.is_duplicate&&!m.is_copy);a<0&&(a=0),n[a]||(n[a]={fields:{}});const o=n[a].fields||{},s=K.editFields||{},i=new Set(["subtotal","vat","total_amount"]),r={...o};for(const m in s){let p=s[m];if((p===""||p===void 0)&&(p=null),i.has(m)&&p!==null){const f=parseFloat(p);p=isNaN(f)?null:f}r[m]=p}n[a].fields=r;const d=await fetch("/api/history/"+encodeURIComponent(K.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:n})});if(!d.ok)throw new Error("http "+d.status);e(),showToast(t("exc-fld-save-ok"),"success"),ut(),await gt(),await Ue(),Pe()}catch(n){e(),console.warn("save fields fail",n),showToast(t("exc-fld-save-fail"),"error")}finally{K.loading=!1}}async function rr(){if(!(!K.openExcId||K.loading)){K.loading=!0;try{const e=await fetch("/api/exceptions/"+K.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-resolved"),"success"),ut(),await gt(),await Ue(),Pe()}catch(e){console.warn("resolve fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{K.loading=!1}}}async function lr(){if(!(!K.openExcId||K.loading)){K.loading=!0;try{const e=await fetch("/api/exceptions/"+K.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-ignored"),"success"),ut(),await gt(),await Ue(),Pe()}catch(e){console.warn("ignore fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{K.loading=!1}}}async function Pe(){try{const e=V.currentClient||"",n="/api/exceptions/stats?status=pending"+(e?"&client_id="+encodeURIComponent(e):""),a=await fetch(n,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!a.ok)return;const o=await a.json(),s=document.getElementById("nav-exc-badge");if(!s)return;const i=parseInt(o.pending||0,10);i>0?(s.textContent=i>99?"99+":String(i),s.style.display=""):s.style.display="none"}catch{}}function ro(e){document.getElementById("exc-kpi-pending").textContent=e.pending||0,document.getElementById("exc-kpi-high").textContent=e.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=e.resolved||0,document.getElementById("exc-kpi-learned").textContent=e.learned_rules||0;const n=document.getElementById("exc-status-tab-count-pending"),a=document.getElementById("exc-status-tab-count-resolved"),o=document.getElementById("exc-status-tab-count-ignored");n&&(n.textContent=e.pending||0),a&&(a.textContent=e.resolved||0),o&&(o.textContent=e.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(i=>{i.classList.toggle("active",i.dataset.status===(V.currentStatus||"pending"))})}function On(e){const n=document.getElementById("exc-chips");if(!n)return;const a=e.by_rule||{},o=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let i=`<button class="exc-chip ${!V.currentRule?"active":""}" data-rule="">
        <span>${escapeHtml(t("exc-chip-all"))}</span>
        <span class="exc-chip-count">${e.pending||0}</span>
    </button>`;for(const r of o){const d=a[r]||0;if(d===0&&V.currentRule!==r)continue;const m=V.currentRule===r;i+=`<button class="exc-chip ${m?"active":""}" data-rule="${escapeHtml(r)}">
            <span>${escapeHtml(t("exc-chip-"+r))}</span>
            <span class="exc-chip-count">${d}</span>
        </button>`}n.innerHTML=i,n.querySelectorAll(".exc-chip").forEach(r=>{r.addEventListener("click",()=>{const d=r.dataset.rule||null;V.currentRule=d,Ue()})})}function Vn(e){const n=document.getElementById("exc-list");if(!n)return;if(!e||e.length===0){n.innerHTML=`<div class="exc-empty">
            ${Qi()}
            <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
            <div>${escapeHtml(t("exc-empty-desc"))}</div>
        </div>`,ha();return}const a='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',o=(V.currentStatus||"pending")==="pending";n.innerHTML=e.map(s=>{const i=s.severity||"medium",r=t("exc-rule-"+s.rule_code)||s.rule_code,d=s.seller_name&&s.seller_name.trim()?s.seller_name:t("exc-no-seller"),m=s.filename||"—",p=tr(s.invoice_date||s.created_at),f=s.status==="pending",c=V.selectedIds.has(s.id),l=o&&f;return`
            <div class="exc-row sev-${escapeHtml(i)} ${c?"selected":""}" data-exc-id="${escapeHtml(String(s.id))}">
                <div class="exc-row-check ${c?"checked":""}" data-check-id="${escapeHtml(String(s.id))}" ${l?"":'style="visibility:hidden;"'}>${a}</div>
                <div class="exc-row-sev">${Zi(i)}</div>
                <div class="exc-row-main">
                    <div class="exc-row-title">${escapeHtml(d)} · ${escapeHtml(m)}</div>
                    <div class="exc-row-meta">
                        ${s.invoice_no?`<span><b>${escapeHtml(s.invoice_no)}</b></span>`:""}
                        <span>${escapeHtml(p)}</span>
                    </div>
                </div>
                <div class="exc-row-rule r-${escapeHtml(i)}">${escapeHtml(r)}</div>
                <div class="exc-row-amount">${escapeHtml(er(s.total_amount))}</div>
            </div>
        `}).join(""),n.querySelectorAll(".exc-row").forEach(s=>{s.addEventListener("click",i=>{if(i.target.closest(".exc-row-check"))return;const r=s.dataset.excId;r&&or(parseInt(r,10))})}),n.querySelectorAll(".exc-row-check").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation();const r=parseInt(s.dataset.checkId,10);r&&(V.selectedIds.has(r)?(V.selectedIds.delete(r),s.classList.remove("checked"),s.closest(".exc-row").classList.remove("selected")):(V.selectedIds.add(r),s.classList.add("checked"),s.closest(".exc-row").classList.add("selected")),va())})}),va(),ha()}function va(){const e=document.getElementById("exc-batch-bar"),n=document.getElementById("exc-batch-count");if(!e||!n)return;const a=V.selectedIds.size;a===0?e.style.display="none":(e.style.display="",n.textContent=Ve("exc-batch-count",{n:a}))}function ha(){const e=document.getElementById("exc-list-foot"),n=document.getElementById("exc-list-count"),a=document.getElementById("exc-loadmore");if(!e||!n||!a)return;const o=V.listCache.length;if(o===0){e.style.display="none";return}e.style.display="";let s=o;const i=V.statsCache;i&&(V.currentRule?s=(i.by_rule||{})[V.currentRule]||o:s=i.pending||o),V.total=s,n.textContent=Ve("exc-list-count",{shown:o,total:s});const r=o<s&&o<500;a.style.display=r?"":"none"}async function gt(){try{if(navigator.onLine===!1)throw new Error("offline");const e=V.currentClient||"",n=V.currentStatus||"pending",a=new URLSearchParams;a.set("status",n),e&&a.set("client_id",e);const o="/api/exceptions/stats?"+a.toString(),s=await fetch(o,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!s.ok)throw new Error("http "+s.status);const i=await s.json();return V.statsCache=i,ro(i),On(i),i}catch(e){return console.warn("loadExceptionsStats fail",e),null}}function cr(e){const n=document.getElementById("exc-list");if(!n)return;const a=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="18" cy="18" r="14"/>
        <line x1="18" y1="11" x2="18" y2="19"/>
        <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
    </svg>`,o=e?t("exc-offline"):t("exc-error-retry-title"),s=e?"":t("exc-error-retry-desc");n.innerHTML=`
        <div class="exc-error">
            ${a}
            <div class="exc-error-msg">${escapeHtml(o)}${s?" · "+escapeHtml(s):""}</div>
            <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
        </div>`;const i=document.getElementById("exc-retry-btn");i&&i.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function Ue(e){e=e||{};const n=!!e.append,a=document.getElementById("exc-list");!n&&a&&V.listCache.length===0&&(a.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const o=new URLSearchParams;o.set("status",V.currentStatus||"pending"),V.currentRule&&o.set("rule_code",V.currentRule),V.currentClient&&o.set("client_id",V.currentClient);const s=n?V.listCache.length:0;o.set("limit",String(V.pageSize)),o.set("offset",String(s));try{if(navigator.onLine===!1)throw new Error("offline");const i=await fetch("/api/exceptions/list?"+o.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!i.ok)throw new Error("http "+i.status);const d=(await i.json()).items||[];n?V.listCache=V.listCache.concat(d):(V.listCache=d,V.selectedIds.clear()),V.loadFailed=!1,Vn(V.listCache),V.statsCache&&On(V.statsCache)}catch(i){console.warn("loadExceptionsList fail",i),V.loadFailed=!0;const r=navigator.onLine===!1||String(i.message||"").includes("offline");n?showToast(t("exc-toast-load-fail"),"error"):(cr(r),showToast(r?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function dr(){if(!V.loading&&!(V.listCache.length>=500)){V.loading=!0;try{await Ue({append:!0})}finally{V.loading=!1}}}function Un(){const e=document.getElementById("exc-client-filter");if(!e)return;const n=window._clientsCache||[],a=V.currentClient||"",o=typeof t=="function"?t("history-client-all"):"全部客户";e.innerHTML=`<option value="">${escapeHtml(o)}</option>`+n.map(s=>`<option value="${s.id}">${escapeHtml(s.name)}</option>`).join(""),e.value=a}async function pr(){if(it.batchLoading)return;const e=Array.from(V.selectedIds);if(e.length===0||!await showConfirm(Ve("exc-batch-confirm-resolve",{n:e.length})))return;it.batchLoading=!0;const a=showToast(Ve("exc-batch-count",{n:e.length})+" …","loading",0);try{const o=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"resolve"})});if(!o.ok)throw new Error("http "+o.status);const s=await o.json();a(),showToast(Ve("exc-toast-batch-resolved",{n:s.processed||0}),"success"),V.selectedIds.clear(),await gt(),await Ue(),Pe()}catch(o){a(),console.warn("batch resolve fail",o),showToast(t("exc-toast-batch-fail"),"error")}finally{it.batchLoading=!1}}async function ur(){if(it.batchLoading)return;const e=Array.from(V.selectedIds);if(e.length===0||!await showConfirm(Ve("exc-batch-confirm-ignore",{n:e.length}),{danger:!1}))return;it.batchLoading=!0;const a=showToast(Ve("exc-batch-count",{n:e.length})+" …","loading",0);try{const o=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"ignore"})});if(!o.ok)throw new Error("http "+o.status);const s=await o.json();a(),showToast(Ve("exc-toast-batch-ignored",{n:s.processed||0,wl:s.whitelist_added||0}),"success"),V.selectedIds.clear(),await gt(),await Ue(),Pe()}catch(o){a(),console.warn("batch ignore fail",o),showToast(t("exc-toast-batch-fail"),"error")}finally{it.batchLoading=!1}}function fr(){V.selectedIds.clear(),Vn(V.listCache)}async function lo(){const e=document.getElementById("learned-list");if(e){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const n=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);const o=(await n.json()).items||[];if(o.length===0){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const s=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
        </svg>`;e.innerHTML=o.map(i=>{const r=t("exc-rule-"+i.rule_code)||i.rule_code;return`
                <div class="learned-row" data-wl-id="${escapeHtml(String(i.id))}">
                    <div class="learned-seller" title="${escapeHtml(i.seller_name)}">${escapeHtml(i.seller_name)}</div>
                    <div class="learned-rule">${escapeHtml(r)}</div>
                    <div class="learned-date">${escapeHtml(nr(i.created_at))}</div>
                    <button class="learned-del-btn" data-del-wl="${escapeHtml(String(i.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${s}</button>
                </div>
            `}).join("")}catch(n){console.warn("loadLearnedRules fail",n),e.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadExceptionsPage=async function(){if(!V.loading){V.loading=!0;try{Un(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await gt(),await Ue()}finally{V.loading=!1}}};window.refreshExcBadge=Pe;window._refreshExcClientFilter=Un;window._excState=V;window._rerenderExceptions=function(){try{Un()}catch{}V.statsCache&&(ro(V.statsCache),On(V.statsCache)),V.listCache&&V.listCache.length&&Vn(V.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}K.openExcId&&Re()};document.addEventListener("click",e=>{e.target.closest("#exc-drawer-close")&&ut(),e.target.closest("#exc-drawer-mask")&&ut(),e.target.closest("#exc-btn-resolve")&&rr(),e.target.closest("#exc-btn-ignore")&&lr(),e.target.closest("#exc-batch-resolve")&&pr(),e.target.closest("#exc-batch-ignore")&&ur(),e.target.closest("#exc-batch-clear")&&fr(),e.target.closest("#exc-loadmore")&&dr()});document.addEventListener("keydown",e=>{e.key==="Escape"&&K.openExcId&&ut()});document.addEventListener("click",e=>{e.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),Pe())});document.addEventListener("change",e=>{if(!e.target.closest("#exc-client-filter"))return;const n=e.target;V.currentClient=n.value||"",V.currentRule=null,V.selectedIds.clear(),V.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),Pe()});document.addEventListener("click",e=>{const n=e.target.closest("#exc-status-tabs .exc-status-tab");if(!n)return;const a=n.dataset.status||"pending";a!==V.currentStatus&&(V.currentStatus=a,V.currentRule=null,V.selectedIds.clear(),V.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())});window.addEventListener("online",()=>{V.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()});setTimeout(Pe,1500);setInterval(Pe,6e4);window.loadLearnedRules=lo;document.addEventListener("click",async e=>{const n=e.target.closest("[data-del-wl]");if(!n)return;const a=parseInt(n.dataset.delWl,10);if(!a)return;const o=n.closest(".learned-row"),s=o&&o.querySelector(".learned-seller"),i=s?s.textContent.trim():"",r=t("set-learned-del-confirm").replace("{seller}",i);if(await showConfirm(r,{danger:!0}))try{const m=await fetch("/api/exception-whitelist/"+a,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!m.ok)throw new Error("http "+m.status);showToast(t("set-learned-del-ok"),"success"),lo(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(m){console.warn("delete whitelist fail",m),showToast(t("set-learned-del-fail"),"error")}});(function(){let e={items:[],q:"",cat:"",adapter:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(c){const l=typeof currentLang=="string"&&currentLang||window._currentLang||"th",u=c.error_friendly&&c.error_friendly[l];if(u)return u;if(typeof humanizeError=="function"&&c.error_msg)try{return humanizeError(c.error_msg)}catch{}return t("erp-exc-reason-"+(c.category||"other"))}function s(){const c=document.getElementById("erp-exc-batch");if(!c)return;const l=e.selected.size;c.hidden=l===0;const u=c.querySelector(".erp-exc-batch-count");u&&(u.textContent=String(l))}function i(){const c=document.getElementById("erp-exc-block");if(!c)return;const l=e;if(!(l.total>0||!!l.q||!!l.cat)){c.hidden=!0,c.innerHTML="";return}c.hidden=!1;const v=l.categories||{},w=Object.keys(v).reduce((T,D)=>T+v[D],0);let b=`<button class="erp-exc-chip ${l.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${w}</span></button>`;Object.keys(v).forEach(T=>{b+=`<button class="erp-exc-chip ${l.cat===T?"active":""}" data-erpexc-cat="${escapeHtml(T)}"><span>${escapeHtml(t("erp-exc-cat-"+T))}</span><span class="erp-exc-chip-count">${v[T]}</span></button>`});const g=l.items||[],h=g.length>0&&g.every(T=>l.selected.has(T.id)),I=g.map(T=>{const D=T.state==="needs_action"?"needs":T.state==="retrying"?"retry":"fail",O=t("erp-exc-state-"+(T.state||"failed")),P=o(T),j=l.selected.has(T.id)?"checked":"",N=T.push_type==="id_card",se=N?`<span class="erp-exc-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span> `:"",ie=N?`<span class="ex-inv" title="${escapeHtml(t("erp-log-col-booking"))}">${se}${escapeHtml(T.invoice_no||"—")}</span>`:`<span class="ex-inv" title="${escapeHtml(T.invoice_no||"")}">${escapeHtml(T.invoice_no||"—")}</span>`,pe=N?`<span class="ex-seller" title="${escapeHtml(t("erp-log-col-customer"))}">${escapeHtml(T.seller_name||"—")}</span>`:`<span class="ex-seller" title="${escapeHtml(T.seller_name||"")}">${escapeHtml(T.seller_name||"—")}</span>`,re=N?`<span class="ex-buyer" title="${escapeHtml(t("erp-log-col-idcard"))}">${T.id_card_tail?"••••"+escapeHtml(T.id_card_tail):"—"}</span>`:`<span class="ex-buyer" title="${escapeHtml(T.ocr_buyer_name||"")}">${escapeHtml(T.ocr_buyer_name||"—")}</span>`;return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(T.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(T.id)}" ${j}></span>
                ${ie}
                ${pe}
                ${re}
                <span class="ex-state"><span class="erp-exc-state ${D}">${escapeHtml(O)}</span></span>
                <span class="ex-reason" title="${escapeHtml(P)}">${escapeHtml(P)}${T.error_code?` <span class="erp-exc-code">${escapeHtml(T.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(T.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),y=g.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",x=g.length<l.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${g.length}/${l.total})</button>`:l.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:g.length,total:l.total}))}</div>`:"",E=l.adapter==="mrerp_dms",_=Array.isArray(window._erpEndpoints)?window._erpEndpoints:[],k=new Set;let B=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`;_.forEach(T=>{const D=(T&&T.adapter||"").toLowerCase();!D||k.has(D)||(k.add(D),B+=`<option value="${escapeHtml(D)}"${D===l.adapter?" selected":""}>${escapeHtml(T&&T.name||D)}</option>`)});const L=E?t("erp-log-col-booking"):t("erp-exc-f-invoice"),C=E?t("erp-log-col-customer"):t("erp-exc-f-seller"),S=E?t("erp-log-col-idcard"):t("erp-exc-f-buyer");c.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${B}</select>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(l.q)}">
            </div>
            <div class="erp-exc-chips">${b}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${l.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${l.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${h?"checked":""}></span>
                    <span class="ex-inv">${escapeHtml(L)}</span>
                    <span class="ex-seller">${escapeHtml(C)}</span>
                    <span class="ex-buyer">${escapeHtml(S)}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${I}${y}
            </div>
            <div class="erp-exc-foot">${x}</div>`;const M=document.getElementById("erp-exc-search");if(M){if(l.focusSearch){M.focus();try{M.setSelectionRange(l.searchCaret,l.searchCaret)}catch{}}M.addEventListener("input",()=>{l.q=M.value,l.focusSearch=!0,l.searchCaret=M.selectionStart||M.value.length,clearTimeout(n),n=setTimeout(()=>m(!1),350)}),M.addEventListener("blur",()=>{l.focusSearch=!1})}c.querySelectorAll(".erp-exc-chip").forEach(T=>{T.addEventListener("click",()=>{l.cat=T.dataset.erpexcCat||"",m(!1)})});const $=document.getElementById("erp-exc-erp-select");$&&$.addEventListener("change",()=>{l.adapter=$.value||"",m(!1)}),c.querySelectorAll("[data-erpexc-retry]").forEach(T=>{T.addEventListener("click",D=>{D.stopPropagation(),r(T.dataset.erpexcRetry,T)})}),c.querySelectorAll(".erp-exc-cb").forEach(T=>{T.addEventListener("change",()=>{const D=T.dataset.erpexcCb;T.checked?l.selected.add(D):l.selected.delete(D);const O=document.getElementById("erp-exc-cb-all");O&&(O.checked=g.length>0&&g.every(P=>l.selected.has(P.id))),s()})});const q=document.getElementById("erp-exc-cb-all");q&&q.addEventListener("change",()=>{g.forEach(T=>{q.checked?l.selected.add(T.id):l.selected.delete(T.id)}),c.querySelectorAll(".erp-exc-cb").forEach(T=>{T.checked=q.checked}),s()}),c.querySelectorAll("[data-erpexc-batch]").forEach(T=>{T.addEventListener("click",()=>d(T.dataset.erpexcBatch))});const H=document.getElementById("erp-exc-more");H&&H.addEventListener("click",()=>m(!0)),c.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(T=>{T.addEventListener("click",D=>{D.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(T.dataset.erpexcId)})})}async function r(c,l){if(c){l&&(l.disabled=!0,l.textContent=t("erp-exc-retrying"));try{const u=await fetch("/api/erp/logs/"+encodeURIComponent(c)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),v=await u.json().catch(()=>({}));showToast(u.ok&&v.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),u.ok&&v.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(c),m(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function d(c){const l=Array.from(e.selected);if(c==="clear"){e.selected.clear(),i();return}if(l.length!==0){if(c==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:l.length}),{danger:!0}))return;try{const v=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:l.slice(0,200)})}),w=await v.json().catch(()=>({}));showToast(v.ok?t("erp-exc-batch-delete-ok",{n:w.deleted||0}):t("erp-exc-retry-fail"),v.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(c==="retry")try{const u=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:l.slice(0,50)})}),v=await u.json().catch(()=>({}));showToast(u.ok?t("erp-exc-batch-retry-ok",{ok:v.succeeded||0,fail:(v.failed||0)+(v.skipped||0)}):t("erp-exc-retry-fail"),u.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),m(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function m(c){const l=document.getElementById("erp-exc-block");if(!(!l||e.loading)){e.loading=!0;try{if(!Array.isArray(window._erpEndpoints)||!window._erpEndpoints.length)try{const g=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+a()}});if(g.ok){const h=await g.json();window._erpEndpoints=h&&(h.items||h)||[]}}catch{}const u=new URLSearchParams;e.q&&u.set("q",e.q),e.cat&&u.set("category",e.cat),e.adapter&&u.set("adapter",e.adapter),u.set("limit",String(e.pageSize)),u.set("offset",String(c?e.items.length:0));const v=await fetch("/api/erp/exceptions?"+u.toString(),{headers:{Authorization:"Bearer "+a()}});if(!v.ok){c||(l.hidden=!0);return}const w=await v.json(),b=w.items||[];e.items=c?e.items.concat(b):b,e.total=w.total||0,e.categories=w.categories||{},i()}catch{c||(l.hidden=!0)}finally{e.loading=!1}}}let p={};function f(){const c=document.getElementById("erp-exc-modal");c&&c.remove()}window._erpExcOpenEdit=function(c){const l=(e.items||[]).find(x=>String(x.id)===String(c));if(!l)return;const u=l.push_type==="id_card",v=!!l.history_client_id&&l.category==="customer_mismatch",w=l.category==="product_mismatch"&&!!l.history_id&&!!l.endpoint_id,b=o(l),g=l.state==="needs_action"?"needs":l.state==="retrying"?"retry":"fail",h=(x,E)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(x)}</span><span class="erp-exc-m-v">${escapeHtml(E||"—")}</span></div>`;let I="";if(v)I=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(w)I=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const x="erp-exc-edit-hint-"+(l.category||"other");let E=t(x);(!E||E===x)&&(E=b),I=`<div class="erp-exc-m-hint">${escapeHtml(E)}</div>`}const y=document.createElement("div");if(y.id="erp-exc-modal",y.className="erp-exc-modal-overlay",y.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${g}">${escapeHtml(t("erp-exc-state-"+(l.state||"failed")))}</span> ${escapeHtml(b)}${l.error_code&&!u?` <span class="erp-exc-code">${escapeHtml(l.error_code)}</span>`:""}</div>
                    ${h(u?t("erp-log-col-booking"):t("erp-exc-f-invoice"),l.invoice_no)}
                    ${h(u?t("erp-log-col-customer"):t("erp-exc-f-seller"),l.seller_name)}
                    ${u?h(t("erp-log-col-idcard"),l.id_card_tail?"••••"+l.id_card_tail:"—"):h(t("erp-exc-f-buyer"),l.ocr_buyer_name)+h(t("erp-exc-edit-field-current"),l.client_name)}
                    ${I}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${v?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${w?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(y),y.addEventListener("click",x=>{x.target===y&&f()}),document.getElementById("erp-exc-m-close").addEventListener("click",f),document.getElementById("erp-exc-m-cancel").addEventListener("click",f),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{f(),r(l.id,null)}),v){let x="";const E=document.getElementById("erp-exc-m-bind"),_=document.getElementById("erp-exc-m-custlist"),k=document.getElementById("erp-exc-m-search"),B=(C,S)=>{const M=(S||"").trim().toLowerCase(),$=M?C.filter(q=>(q.code||"").toLowerCase().includes(M)||(q.name||"").toLowerCase().includes(M)):C;if($.length===0){_.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}_.innerHTML=$.slice(0,100).map(q=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(q.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(q.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(q.code||"")}</span>
                    </div>`).join(""),_.querySelectorAll(".erp-exc-m-cust").forEach(q=>{q.addEventListener("click",()=>{x=q.dataset.custCode||"",_.querySelectorAll(".erp-exc-m-cust").forEach(H=>H.classList.remove("sel")),q.classList.add("sel"),E&&(E.disabled=!x)})})},L=async()=>{const C=l.endpoint_id;if(p[C]){B(p[C],"");return}try{const S=await fetch("/api/erp/endpoints/"+encodeURIComponent(C)+"/customers",{headers:{Authorization:"Bearer "+a()}}),M=await S.json().catch(()=>({}));if(!S.ok||!M.ok){_.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const $=M.customers||[];p[C]=$,B($,"")}catch{_.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};k&&k.addEventListener("input",()=>B(p[l.endpoint_id]||[],k.value)),L(),E&&E.addEventListener("click",async()=>{if(x){E.disabled=!0,E.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:l.history_client_id,erp_type:l.endpoint_adapter,erp_code:x})})).ok){showToast(t("erp-exc-retry-fail"),"error"),E.disabled=!1,E.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),f(),await r(l.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),E.disabled=!1,E.textContent=t("erp-exc-edit-bind-retry")}}})}if(w){const x=document.getElementById("erp-exc-m-bind-prod"),E=document.getElementById("erp-exc-m-prodlist"),_={};let k=[];const B=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+k.slice(0,500).map(S=>`<option value="${escapeHtml(S.code||"")}" data-pname="${escapeHtml(S.name||"")}">`+escapeHtml((S.name||"")+" · "+(S.code||""))+"</option>").join(""),L=S=>{if(!S.length){E.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}E.innerHTML=S.map(M=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(M)}">${escapeHtml(M)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(M)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${B()}</select>
                    </div>`).join(""),E.querySelectorAll(".erp-exc-m-prod-sel").forEach(M=>{M.addEventListener("change",()=>{const $=M.dataset.item,q=M.options[M.selectedIndex];M.value?_[$]={code:M.value,name:q&&q.dataset.pname||""}:delete _[$],x&&(x.disabled=Object.keys(_).length===0)})})};(async()=>{try{const M=await(await fetch("/api/history/"+encodeURIComponent(l.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),$=M&&M.pages||[],q=[],H={};(Array.isArray($)?$:[]).forEach(O=>{const P=O&&O.fields&&O.fields.items||[];(Array.isArray(P)?P:[]).forEach(j=>{const N=(j&&(j.name||j.description)||"").trim();N&&!H[N]&&(H[N]=1,q.push(N))})});const T=await fetch("/api/erp/endpoints/"+encodeURIComponent(l.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),D=await T.json().catch(()=>({}));if(!T.ok||!D.ok){E.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}k=D.products||[],L(q)}catch{E.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),x&&x.addEventListener("click",async()=>{const S=Object.entries(_);if(S.length){x.disabled=!0,x.textContent=t("erp-exc-retrying");try{for(const[M,$]of S)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:l.endpoint_adapter,item_name:M,erp_code:$.code,erp_name:$.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),x.disabled=!1,x.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),f(),await r(l.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),x.disabled=!1,x.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=i,window.loadErpExceptions=m,window._erpExcState=e})();const mr=`
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
`;ke("cmdk-mask",mr);(function(){function e(c){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||c&&c.id&&String(c.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var l=window._userInfo,u=!1,v=!0,w=!1,b=!1;l&&(u=typeof canManageTeam=="function"?canManageTeam(l):!!(l.role==="owner"||l.is_super_admin),v=typeof shouldHideMoney=="function"?shouldHideMoney(l):l.role==="member"&&!l.is_super_admin,w=typeof isSuperAdmin=="function"?isSuperAdmin(l):!!l.is_super_admin,b=e(l)),document.querySelectorAll("[data-show-if-team]").forEach(function(h){h.style.display=u?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(h){h.style.display=v?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(h){h.style.display=w?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(h){h.style.display=b?"":"none"});var g=w||b;document.querySelectorAll("[data-show-if-special]").forEach(function(h){h.style.display=g?"":"none"})},window.renderAvatarMenu=function(l){if(l){var u=document.getElementById("avatar-btn"),v=document.getElementById("avatar-popup-name"),w=document.getElementById("avatar-popup-email");if(!(!u||!v||!w)){var b=(l.username||"").trim(),g=b.split("@")[0]||b||"—",h=(b.charAt(0)||"?").toUpperCase(),I=(l.avatar_url||"").trim();if(I){var y=I.replace(/"/g,"&quot;"),x=h.replace(/'/g,"\\'");u.innerHTML='<img src="'+y+'" alt="'+h+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+x+`'">`}else u.textContent=h;v.textContent=g,w.textContent=b||"—",u.setAttribute("title",b||"")}}};function n(){var c=document.getElementById("avatar-wrap"),l=document.getElementById("avatar-btn"),u=document.getElementById("avatar-popup");if(!c||!l||!u)return;function v(){u.classList.remove("show"),l.setAttribute("aria-expanded","false")}function w(){u.classList.add("show"),l.setAttribute("aria-expanded","true")}l.addEventListener("click",function(b){b.stopPropagation(),u.classList.contains("show")?v():w()}),document.addEventListener("click",function(b){u.classList.contains("show")&&!c.contains(b.target)&&v()}),u.addEventListener("click",function(b){var g=b.target.closest(".avatar-popup-item");if(g){var h=g.dataset.action;switch(v(),h){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var I=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(I||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var y=document.getElementById("help-modal");y&&(y.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=v}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(c){return c.style.display!=="none"})}function o(c){var l=a();l.forEach(function(u){u.classList.remove("focus")}),l[c]&&(l[c].classList.add("focus"),l[c].scrollIntoView({block:"nearest"}))}function s(c){var l=a();if(l.length){var u=l.findIndex(function(w){return w.classList.contains("focus")});u<0&&(u=0);var v=(u+c+l.length)%l.length;o(v)}}function i(c){c=(c||"").toLowerCase().trim();var l=0,u=window._userInfo,v=typeof isSuperAdmin=="function"?isSuperAdmin(u):!!(u&&u.is_super_admin),w=e(u);document.querySelectorAll(".cmdk-item").forEach(function(g){if(g.dataset.showIfAdmin==="1"&&!v){g.style.display="none";return}if(g.dataset.showIfTest==="1"&&!w){g.style.display="none";return}var h=(g.dataset.cmdkText||g.textContent||"").toLowerCase(),I=!c||h.indexOf(c)>=0;g.style.display=I?"":"none",g.classList.remove("focus"),I&&l++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(g){for(var h=g.nextElementSibling,I=!1;h&&!h.hasAttribute("data-cmdk-section");){if(h.classList&&h.classList.contains("cmdk-item")&&h.style.display!=="none"){I=!0;break}h=h.nextElementSibling}g.style.display=I?"":"none"});var b=document.getElementById("cmdk-empty");b&&(b.style.display=l===0?"flex":"none"),o(0)}window.openCmdk=function(){var l=document.getElementById("cmdk-mask");l&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),l.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var u=document.getElementById("cmdk-input");u&&(u.value="",i(""),u.focus(),o(0))},50))},window.closeCmdk=function(){var l=document.getElementById("cmdk-mask");l&&l.classList.remove("show")};function r(c){if(c){if(c.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var l=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(l||"即将上线","info")}return}var u=c.dataset.cmdkRoute,v=c.dataset.cmdkAction;if(window.closeCmdk(),u){typeof routeTo=="function"&&routeTo(u);return}if(v){if(v==="open-admin"){window.location.href="/admin/cost";return}if(v.indexOf("lang-")===0){var w=v.slice(5);typeof applyLang=="function"&&applyLang(w)}}}}function d(){var c=document.getElementById("cmdk-mask"),l=document.getElementById("cmdk-input"),u=document.getElementById("cmdk-body");if(!(!c||!l||!u)){c.addEventListener("click",function(b){b.target===c&&window.closeCmdk()});var v=document.getElementById("cmdk-esc-btn");v&&v.addEventListener("click",function(){window.closeCmdk()}),l.addEventListener("input",function(b){i(b.target.value)}),l.addEventListener("keydown",function(b){b.key==="ArrowDown"?(b.preventDefault(),s(1)):b.key==="ArrowUp"?(b.preventDefault(),s(-1)):b.key==="Enter"?(b.preventDefault(),r(c.querySelector(".cmdk-item.focus"))):b.key==="Escape"&&(b.preventDefault(),window.closeCmdk())}),u.addEventListener("click",function(b){var g=b.target.closest(".cmdk-item");g&&r(g)}),u.addEventListener("mousemove",function(b){var g=b.target.closest(".cmdk-item");!g||g.style.display==="none"||g.classList.contains("cmdk-item-locked")||(a().forEach(function(h){h.classList.remove("focus")}),g.classList.add("focus"))});var w=document.getElementById("topbar-search");w&&(w.addEventListener("click",function(){window.openCmdk()}),w.addEventListener("keydown",function(b){(b.key==="Enter"||b.key===" ")&&(b.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(c){if((c.metaKey||c.ctrlKey)&&(c.key==="k"||c.key==="K")){c.preventDefault(),window.openCmdk();return}if(c.key==="Escape"){var l=document.getElementById("cmdk-mask");if(l&&l.classList.contains("show")){window.closeCmdk();return}var u=document.getElementById("avatar-popup");u&&u.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var m=(navigator.userAgent||"").toLowerCase(),p=m.indexOf("mac")>=0||m.indexOf("iphone")>=0||m.indexOf("ipad")>=0;p||document.body.classList.add("is-windows")}catch{}function f(){n(),d(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",f):f()})();(function(){function n(v){return String(v??"").replace(/[&<>"']/g,function(w){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[w]})}function a(v){if(!v||isNaN(v))return"";var w=Number(v);return w<1024?w+" B":w<1024*1024?(w/1024).toFixed(1)+" KB":(w/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(v){var w=v.target.closest&&v.target.closest(".recon-collapse-head");if(w&&!(v.target.closest("button")||v.target.closest("a"))){var b=w.closest(".recon-collapse");if(b){var g=b.getAttribute("data-collapsed")==="true";b.setAttribute("data-collapsed",g?"false":"true"),g&&(b.id==="vex-summary-collapse"&&f(),b.id==="vex-detail-collapse"&&c())}}}),document.addEventListener("keydown",function(v){if(!(v.key!=="Enter"&&v.key!==" ")){var w=v.target.closest&&v.target.closest(".recon-collapse-head");w&&(v.preventDefault(),w.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){m("vat"),m("gl")}function d(v){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(v)||[]}catch{}var w=document.getElementById(v==="vat"?"glv-vat-input":"glv-gl-input");return w&&w.files?Array.from(w.files):[]}function m(v){var w=document.getElementById(v==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(w){var b=d(v),g=v==="vat"?"glv-up-vat-title":"glv-up-gl-title",h=v==="vat"?"① 销项税报告":"② 总账 GL",I=window.t&&window.t(g)||h,y=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),x=n(window.t&&window.t("vex-preview-clear-all")||"全清"),E=o[v]||"",_=b.length;w.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(I)+' <span class="vex-pp-col-count">'+_+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+v+'" type="text" placeholder="'+y+'" value="'+n(E)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+v+'" type="button">'+x+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+v+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+v+'-pg"></div>';var k=document.getElementById("glv-pp-search-"+v);k&&k.addEventListener("input",function(L){o[v]=L.target.value,p(v)});var B=document.getElementById("glv-pp-clearall-"+v);B&&B.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(v)}),p(v)}}function p(v){var w=document.getElementById("glv-pp-"+v+"-list"),b=document.getElementById("glv-pp-"+v+"-pg");if(w){var g=d(v),h=(o[v]||"").toLowerCase(),I=g.map(function(E,_){return{f:E,i:_}}),y=h?I.filter(function(E){return E.f.name.toLowerCase().indexOf(h)>=0}):I;if(w.innerHTML=y.map(function(E){var _=E.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(_.name)+'">'+n(_.name)+'</span><span class="vex-pp-fi-size">'+a(_.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+v+'" data-idx="'+E.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),w.querySelectorAll(".vex-pp-fi-del").forEach(function(E){E.addEventListener("click",function(){var _=E.dataset.kind,k=parseInt(E.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(_,isNaN(k)?null:k)})}),b){var x=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";b.textContent=x.replace("{n}",y.length).replace("{m}",y.length)}}}function f(){var v=function(b,g){var h=document.getElementById(b);h&&(h.textContent=g==null?"—":String(g))},w=window._vexLastTask||{};v("vex-sum-total",w.total),v("vex-sum-matched",w.matched),v("vex-sum-diff",w.diff),v("vex-sum-incomplete",w.incomplete),v("vex-sum-cash",w.cash),document.getElementById("vex-summary-sub")}function c(){var v=window._vexLastTask&&window._vexLastTask.diff_rows||[],w=document.getElementById("vex-detail-tbody"),b=document.getElementById("vex-detail-table"),g=document.getElementById("vex-detail-empty");if(!(!w||!b||!g)){if(v.length===0){b.style.display="none",g.style.display="";return}g.style.display="none",b.style.display="";var h=v.map(function(y){return'<tr><td class="recon-detail-cell-mono">'+n(y.invoice_no||"")+"</td><td>"+n(y.field||"")+"</td><td>"+n(y.report_value||"")+"</td><td>"+n(y.invoice_value||"")+"</td><td>"+n(y.kind||"")+"</td></tr>"}).join("");w.innerHTML=h;var I=document.getElementById("vex-detail-sub");I&&(I.textContent=String(v.length))}}function l(){var v=document.getElementById("glv-toggle-preview");v&&!v._reconBound&&(v._reconBound=!0,v.addEventListener("click",function(){var w=document.getElementById("glv-preview-panel"),b=document.getElementById("glv-toggle-preview-label"),g=w&&w.style.display!=="none";w&&(w.style.display=g?"none":""),v.classList.toggle("open",!g),b&&(b.textContent=g?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),g||r()})),["glv-vat-input","glv-gl-input"].forEach(function(w){var b=document.getElementById(w);!b||b._reconWatched||(b._reconWatched=!0,b.addEventListener("change",function(){var g=document.getElementById("glv-preview-panel");g&&g.style.display!=="none"&&r()}))})}function u(){var v=document.getElementById("vex-summary-collapse"),w=document.getElementById("vex-detail-collapse");v&&(v.style.display=""),w&&(w.style.display=""),f(),c()}window._fillVexSummary=f,window._fillVexDetail=c,window._onVexResultShown=u,document.addEventListener("DOMContentLoaded",function(){l()}),setTimeout(l,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var v=document.getElementById("glv-preview-panel");v&&v.style.display!=="none"&&r();var w=document.getElementById("glv-toggle-preview-label"),b=document.getElementById("glv-toggle-preview");w&&b&&(w.textContent=b.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:f,fillVexDetail:c}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(d=>{d.addEventListener("click",()=>{i.forEach(l=>l.classList.remove("active")),d.classList.add("active");const m=d.dataset.reconTab,p=document.getElementById("recon-pane-bank"),f=document.getElementById("recon-pane-sale-vat"),c=document.getElementById("recon-pane-gl-vat");p&&(p.style.display=m==="bank"?"":"none"),f&&(f.style.display=m==="sale-vat"?"":"none"),c&&(c.style.display=m==="gl-vat"?"":"none"),m==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),m==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const d=document.createElement("button");return d.id="settings-modal-close",d.className="settings-modal-close",d.setAttribute("aria-label","close"),d.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(d,i.firstChild),d.addEventListener("click",s),r.addEventListener("click",m=>{m.target===r&&s()}),r}function o(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(m){console.warn("renderSettings:",m)}let d=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');d&&d.click()},50)}function s(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=A=>document.getElementById(A);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function i(A){return String(A??"").replace(/[&<>"']/g,G=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[G])}function r(A){return A<1024?A+" B":A<1024*1024?(A/1024).toFixed(1)+" KB":(A/1024/1024).toFixed(1)+" MB"}let d=[],m=[],p=!1,f=[],c=50,l=50,u="",v="";async function w(){try{const A=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!A.ok)return;const Z=(await A.json()).kpi||{};[["vex-kpi-month-val",Z.this_month],["vex-kpi-running-val",Z.running],["vex-kpi-done-val",Z.done],["vex-kpi-failed-val",Z.failed]].forEach(([Y,W])=>{const ae=document.getElementById(Y);ae&&(ae.textContent=W??0)})}catch{}}async function b(){try{const A=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!A.ok)return;const G=await A.json();y(G.rows||[])}catch{}}const g=10;var h=1;function I(){var A=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(h=1,y(f),!!A){var G=document.getElementById("vex-task-tbody");G&&G.querySelectorAll("tr").forEach(function(Z){Z.dataset.taskId&&(Z.style.display=Z.textContent.toLowerCase().indexOf(A)>=0?"":"none")})}}function y(A){f=A||f;const G=document.getElementById("vex-task-tbody");if(!G)return;if(!f.length){G.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",x(0);return}const Z=Math.ceil(f.length/g);h>Z&&(h=Z);const Y=(h-1)*g;E(f.slice(Y,Y+g)),x(f.length)}function x(A){const G=document.getElementById("vex-task-pager"),Z=document.getElementById("vex-task-pager-info"),Y=document.getElementById("vex-task-prev"),W=document.getElementById("vex-task-next");if(!G)return;if(A<=g){G.style.display="none";return}G.style.display="";const ae=Math.ceil(A/g);Z&&(Z.textContent=h+" / "+ae),Y&&(Y.disabled=h<=1),W&&(W.disabled=h>=ae)}function E(A){const G=document.getElementById("vex-task-tbody");if(!G)return;const Z={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},Y={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},W='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ae='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';G.innerHTML=A.map(X=>{const ce=X.created_at?new Date(X.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",te=X.period||"—",me=X.matched_count!=null?X.matched_count+" ✓ · "+X.mismatched_count+" ⚠":"—",ue=X.mismatch_amount!=null?"฿ "+Number(X.mismatch_amount).toLocaleString():"—",ye=X.elapsed_seconds!=null?X.elapsed_seconds.toFixed(1)+" s":"—",Me=X.status||"pending",Oe=X.client_name&&X.client_name!=="client"?X.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${i(X.id)}" style="cursor:pointer">
                <td>${ce}</td>
                <td>${i(Oe)}</td>
                <td>${i(te)}</td>
                <td>${(X.invoice_count||0)+" / "+(X.report_count||0)}</td>
                <td>${me}</td>
                <td>${ue}</td>
                <td><span class="badge ${Y[Me]||"badge-gray"}">${Z[Me]||Me}</span></td>
                <td>${ye}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${i(X.id)}" title="${t("hist_export")||"导出"}">${W}</button>
                    <button class="vex-task-del-btn" data-task-id="${i(X.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ae}</button>
                </div></td>
            </tr>`}).join(""),G.querySelectorAll(".vex-task-dl-btn").forEach(X=>{X.addEventListener("click",async ce=>{ce.stopPropagation();const te=X.dataset.taskId;try{const me=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(te)+"/download",{credentials:"include",headers:s()});if(me.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!me.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const ue=await me.blob(),Me=(me.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),Oe=Me?decodeURIComponent(Me[1]):"vat_recon_"+te+".xlsx",ln=URL.createObjectURL(ue),et=document.createElement("a");et.href=ln,et.download=Oe,et.click(),setTimeout(()=>URL.revokeObjectURL(ln),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),G.querySelectorAll(".vex-task-del-btn").forEach(X=>{X.addEventListener("click",ce=>{ce.stopPropagation(),k(X.dataset.taskId)})}),I()}function _(){var A=document.getElementById("vex-task-prev"),G=document.getElementById("vex-task-next");A&&!A._vexBound&&(A._vexBound=!0,A.addEventListener("click",function(){h>1&&(h--,y())})),G&&!G._vexBound&&(G._vexBound=!0,G.addEventListener("click",function(){var Z=Math.ceil(f.length/g);h<Z&&(h++,y())}))}async function k(A){const G=t("vex-task-delete-confirm-title")||"删除对账任务?",Z=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(Z,{title:G,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const W=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(A),{method:"DELETE",credentials:"include",headers:s()});if(!W.ok)throw new Error(W.status);showToast(t("vex-task-delete-ok")||"已删除","success"),b(),w()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function B(A){const G=window._currentLang||"th",Z={zh:`已忽略 ${A} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${A} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${A} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${A} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(Z[G]||Z.th,"warn")}function L(A){const G=new Set(d.map(Y=>Y.name+"|"+Y.size));let Z=0;for(const Y of A){if(!a.test(Y.name)){Z++;continue}const W=Y.name+"|"+Y.size;if(!G.has(W)&&(G.add(W),d.push(Y),d.length>=1e3))break}Z>0&&B(Z),d.length>1e3&&(d=d.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),$()}function C(A){const G=new Set(m.map(Y=>Y.name+"|"+Y.size));let Z=0;for(const Y of A){if(!a.test(Y.name)){Z++;continue}const W=Y.name+"|"+Y.size;if(!G.has(W)&&(G.add(W),m.push(Y),m.length>=30))break}Z>0&&B(Z),m.length>30&&(m=m.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),$()}function S(A){d.splice(A,1),$()}function M(A){m.splice(A,1),$()}function $(){const A=o("vex-list-invoice"),G=o("vex-list-report"),Z=o("vex-count-invoice"),Y=o("vex-count-report");Z&&(Z.textContent=d.length),Y&&(Y.textContent=m.length);const W=(ce,te,me)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${i(ce.name)}">${i(ce.name)}</span>
            <span class="vex-fi-s">${r(ce.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${me}" data-vex-idx="${te}" aria-label="remove">×</button>
        </div>`;A&&(A.innerHTML=d.map((ce,te)=>W(ce,te,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),G&&(G.innerHTML=m.map((ce,te)=>W(ce,te,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(ce=>{ce.addEventListener("click",te=>{const me=ce.dataset.vexKind,ue=parseInt(ce.dataset.vexIdx,10);me==="inv"?S(ue):M(ue)})});const ae=d.length>0&&m.length>0;o("vex-build").disabled=!ae||p;const X=o("vex-action-info");X&&(!d.length||!m.length?(X.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",X.className="vex-action-info muted"):(X.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",d.length).replace("{b}",m.length),X.className="vex-action-info ok")),D()}const q='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',H='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',T='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function D(){const A=o("vex-preview-panel");if(!A||A.style.display==="none")return;O("inv"),O("rep");const G=o("vex-pp-guide");G&&(G.style.display=d.length>100?"flex":"none")}function O(A){const G=o(A==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!G)return;const Z=A==="inv"?d:m,Y=A==="inv"?u:v,W=t(A==="inv"?"vex-preview-invoice":"vex-preview-report")||(A==="inv"?"销售发票":"VAT 报告"),ae=i(t("vex-preview-search")||"搜索文件名..."),X=i(t("vex-preview-clear-all")||"全清");G.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${i(W)} <span class="vex-pp-col-count">${Z.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${A}" type="text"
                       placeholder="${ae}" value="${i(Y)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${A}" type="button">${X}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${A}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${A}-pg"></div>`;const ce=o("vex-pp-search-"+A);ce&&ce.addEventListener("input",me=>{A==="inv"?(u=me.target.value,c=50):(v=me.target.value,l=50),P(A)});const te=o("vex-pp-clearall-"+A);te&&te.addEventListener("click",()=>{A==="inv"?(d=[],u="",c=50):(m=[],v="",l=50),$()}),P(A)}function P(A){const G=o("vex-pp-"+A+"-list"),Z=o("vex-pp-"+A+"-pg");if(!G)return;const Y=A==="inv"?d:m,W=A==="inv"?u:v,ae=A==="inv"?c:l,X=A==="inv"?q:H,ce=Y.map((ue,ye)=>({f:ue,i:ye})),te=W?ce.filter(({f:ue})=>ue.name.toLowerCase().includes(W.toLowerCase())):ce,me=te.slice(0,ae);if(G.innerHTML=me.map(({f:ue,i:ye})=>`
            <div class="vex-pp-file-row">
                ${X}
                <span class="vex-pp-fi-name" title="${i(ue.name)}">${i(ue.name)}</span>
                <span class="vex-pp-fi-size">${r(ue.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${A}" data-ridx="${ye}" aria-label="remove">${T}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${A}" style="height:1px;flex-shrink:0"></div>`,G.querySelectorAll(".vex-pp-fi-del").forEach(ue=>{ue.addEventListener("click",()=>{const ye=parseInt(ue.dataset.ridx,10);ue.dataset.kind==="inv"?S(ye):M(ye)})}),Z){const ue=t("vex-preview-count")||"显示前 {n} / 共 {m}";Z.textContent=ue.replace("{n}",me.length).replace("{m}",te.length)}j(A,te.length)}function j(A,G){if((A==="inv"?c:l)>=G)return;const Y=o("vex-pp-sentinel-"+A),W=o("vex-pp-"+A+"-list");if(!Y||!W)return;const ae=new IntersectionObserver(X=>{X[0].isIntersecting&&(ae.disconnect(),A==="inv"?c+=50:l+=50,P(A))},{root:W,threshold:.8});ae.observe(Y)}function N(A,G,Z,Y){const W=o(A),ae=o(G);!W||!ae||(W.addEventListener("click",()=>ae.click()),W.addEventListener("keydown",X=>{(X.key==="Enter"||X.key===" ")&&(X.preventDefault(),ae.click())}),W.addEventListener("dragover",X=>{X.preventDefault(),W.classList.add("drag-over")}),W.addEventListener("dragleave",()=>W.classList.remove("drag-over")),W.addEventListener("drop",X=>{X.preventDefault(),W.classList.remove("drag-over");const te=Array.from(X.dataTransfer.files).filter(me=>a.test(me.name));if(!te.length){showToast(t("vex-toast-bad-ext"),"error");return}Z(te)}),ae.addEventListener("change",()=>{const X=Array.from(ae.files);Z(X),ae.value=""}))}async function se(){if(p||!d.length||!m.length)return;p=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var A=document.getElementById("vex-download");A&&(A.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(W){var ae=document.getElementById(W);ae&&(ae.style.display="none")});const G=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",d.length).replace("{b}",m.length);const Z=setInterval(()=>{const W=Math.floor((Date.now()-G)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",W).replace("{a}",d.length).replace("{b}",m.length)},1e3);try{const W=new FormData;for(const xe of d)W.append("invoices",xe);for(const xe of m)W.append("reports",xe);const ae=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";W.append("lang",ae);const X=localStorage.getItem("mrpilot_token")||"",ce=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:W});let te=null;try{te=await ce.json()}catch{te=null}if(!ce.ok||!te||!te.ok||!te.job_id)throw clearInterval(Z),new Error(te&&te.detail||"HTTP "+ce.status);const me=o("vex-progress-sub"),ue=await window._reconPollJob(te.job_id,X,{onProgress:xe=>{me&&(me.textContent=window._reconProgressText(xe,ae))}});if(clearInterval(Z),!ue||ue.status!=="done"||!ue.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const ye=ue.result_id;let Me=0;const Oe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(ye)+"/download",{headers:s()});if(!Oe.ok)throw new Error("HTTP "+Oe.status);const et=(Oe.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),Xn=et&&et[1]||"vat_recon_"+Date.now()+".xlsx",Co=await Oe.blob(),Zn=URL.createObjectURL(Co),Qn=o("vex-download");Qn.href=Zn,Qn.download=Xn;try{const xe=document.createElement("a");xe.href=Zn,xe.download=Xn,document.body.appendChild(xe),xe.click(),setTimeout(()=>xe.remove(),100)}catch{}o("vex-progress").style.display="none";var Y=document.getElementById("vex-download");Y&&(Y.style.display=""),ye&&(Me=await re(ye)),window._onVexResultShown&&window._onVexResultShown(),Me>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",Me),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),w(),setTimeout(b,800)}catch(W){clearInterval(Z),o("vex-progress").style.display="none";const ae=(t("vex-toast-fail")||"生成失败")+": "+(W.message||W);showToast(ae,"error")}finally{p=!1,o("vex-build").disabled=!1}}function ie(){d=[],m=[];var A=document.getElementById("vex-download");A&&(A.style.display="none"),$()}function pe(A){if(A==null)return"—";var G=parseFloat(A);return isNaN(G)?"—":G.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function re(A){try{var G=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(A),{headers:s()});if(!G.ok)throw new Error(G.status);var Z=await G.json(),Y=Z.raw_data_json;if(typeof Y=="string")try{Y=JSON.parse(Y)}catch{Y={}}Y=Y||{};var W=Y.rows||[],ae=[];W.forEach(function(te){te.kind==="invoice_orphan"?ae.push({invoice_no:te.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:pe(te.amount_inv),kind:te.kind}):te.kind==="report_orphan"?ae.push({invoice_no:te.invoice_no||"",field:"仅报告有",report_value:pe(te.amount_rep),invoice_value:"—",kind:te.kind}):te.dims&&Object.keys(te.dims).length>0&&Object.keys(te.dims).forEach(function(me){var ue=String(te.dims[me]||""),ye=ue.split(" ≠ ");ae.push({invoice_no:te.invoice_no||"",field:me,report_value:ye[0]||ue,invoice_value:ye.length>1?ye[1]:"—",kind:"diff"})})});var X=W.filter(function(te){return te.kind==="matched_cash"}).length,ce=Math.max(0,parseInt(Y.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:Y.n_total||0,matched:Y.n_ok||0,diff:Y.n_diff||0,incomplete:ce,cash:X,diff_rows:ae,task_id:A},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),ce}catch{return 0}}function he(){const A=document.getElementById("vex-pane");A&&A.querySelectorAll("[data-i18n]").forEach(G=>{const Z=t(G.dataset.i18n);Z&&(G.textContent=Z)}),$(),b()}function be(){N("vex-drop-invoice","vex-input-invoice",L),N("vex-drop-report","vex-input-report",C);const A=o("vex-build"),G=o("vex-reset");A&&A.addEventListener("click",se),G&&G.addEventListener("click",ie),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(W=>{W.addEventListener("click",()=>{w(),b()})}),_();const Z=document.getElementById("vex-task-search");Z&&Z.addEventListener("input",I);const Y=document.getElementById("vex-toggle-preview");Y&&Y.addEventListener("click",()=>{const W=o("vex-preview-panel"),ae=o("vex-toggle-preview-label"),X=W&&W.style.display!=="none";W&&(W.style.display=X?"none":""),Y&&Y.classList.toggle("open",!X),ae&&(ae.textContent=X?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),X||D()}),$(),w()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",be):be(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",he),window.subscribeI18n("vex-preview-panel",D))})();const ne={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},ee=e=>document.getElementById(e),co=()=>localStorage.getItem("mrpilot_token")||"",ft=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",Qe=()=>({Authorization:"Bearer "+co()}),ga={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},ve=e=>(ga[ft()]||ga.th)[e]||e;function vr(e){const n=ft(),o={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[e];return o?o[n]||o.th||o.en:ve("error")||"Error"}const St=e=>e==null||isNaN(e)?"":Number(e).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function Gn(e){ee("glv-kpi-matched")&&(ee("glv-kpi-matched").textContent=e&&e.matched!=null?e.matched:"—"),ee("glv-kpi-diff")&&(ee("glv-kpi-diff").textContent=e&&e.diff!=null?e.diff:"—"),ee("glv-kpi-unmatched")&&(ee("glv-kpi-unmatched").textContent=e&&e.unmatched!=null?e.unmatched:"—")}function hr(e){if(!e)return"";try{const n=new Date(e);if(isNaN(n.getTime()))return e;const a=o=>String(o).padStart(2,"0");return n.getFullYear()+"-"+a(n.getMonth()+1)+"-"+a(n.getDate())+" "+a(n.getHours())+":"+a(n.getMinutes())}catch{return e}}function ba(e,n,a,o){const s=ee(e),i=ee(n),r=ee(a);if(!s||!i||!r)return;const d=m=>{if(!m||!m.length)return;const p=Array.isArray(ne[o])?ne[o].slice():[],f=new Set(p.map(c=>c.name+"|"+c.size));for(const c of m){if(!c)continue;const l=c.name+"|"+c.size;f.has(l)||(p.push(c),f.add(l))}ne[o]=p,po(r,p),At(),Pt(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};s.addEventListener("click",()=>i.click()),s.addEventListener("keydown",m=>{(m.key==="Enter"||m.key===" ")&&(m.preventDefault(),i.click())}),i.addEventListener("change",()=>{d(Array.from(i.files||[])),i.value=""}),s.addEventListener("dragover",m=>{m.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",()=>s.classList.remove("drag-over")),s.addEventListener("drop",m=>{m.preventDefault(),s.classList.remove("drag-over");const p=m.dataTransfer&&m.dataTransfer.files?Array.from(m.dataTransfer.files):[];d(p)})}function po(e,n){if(!e)return;if(!n||n.length===0){e.textContent="";return}const a=n.reduce((o,s)=>o+Math.round(s.size/1024),0);if(n.length===1)e.textContent=n[0].name+"  ("+a+" KB)";else{const o=window.t&&window.t("glv-files-count")||"{n} 个文件";e.textContent=o.replace("{n}",n.length)+"  ("+a+" KB)"}}function Ne(e){const n=ne[e];return Array.isArray(n)?n:n?[n]:[]}function At(){const e=ee("btn-glv-run");if(!e)return;const n=Ne("glFile").length>0&&Ne("vatFile").length>0;e.disabled=!n||ne.running}function Pt(){const e=ee("glv-status");if(!e||ne.running)return;const n=Ne("vatFile").length,a=Ne("glFile").length;n===0&&a===0?(e.className="vex-action-info muted",e.innerHTML="<span>"+ve("hint_need_both")+"</span>"):n>0&&a>0?(e.className="vex-action-info ok",e.innerHTML="<span>"+ve("hint_ready")+"</span>"):(e.className="vex-action-info muted",e.innerHTML="<span>"+ve("hint_need_one_more")+"</span>")}function gr(e,n){const a=e==="vat"?"vatFile":"glFile",o=e==="vat"?"glv-vat-input":"glv-gl-input",s=e==="vat"?"glv-vat-name":"glv-gl-name",i=Ne(a);n==null?ne[a]=[]:ne[a]=i.filter((d,m)=>m!==n);const r=ee(o);r&&(r.value=""),po(ee(s),Ne(a)),At(),Pt(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function br(){ne.glFile=[],ne.vatFile=[],ne.currentTaskId=null,ne.lastDetail=[],ne.lastSummary=null;const e=ee("glv-vat-input");e&&(e.value="");const n=ee("glv-gl-input");n&&(n.value="");const a=ee("glv-vat-name");a&&(a.textContent="");const o=ee("glv-gl-name");o&&(o.textContent="");const s=ee("glv-result");s&&(s.style.display="none");const i=ee("glv-kpi-strip");i&&(i.style.display="none"),At(),Pt(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function Kn(e){const n=ee("glv-tbody");if(!n)return;kr(e.length),n.innerHTML="";const a=ve("not_found"),o=document.createDocumentFragment();e.forEach(s=>{const i=document.createElement("tr"),r=(c,l)=>{const u=document.createElement("td");return l&&(u.className=l),u.textContent=c,u},d=s.gl_amount===null||s.gl_amount===void 0,m=s.diff;let p="glv-num",f="glv-num";d?(f+=" glv-cell-missing",p+=" glv-cell-missing"):Math.abs(m||0)<.005?p+=" glv-cell-ok":p+=" glv-cell-diff",i.appendChild(r(s.doc_no||"","glv-doc")),i.appendChild(r(s.date||"","")),i.appendChild(r(s.customer_name||"","")),i.appendChild(r(St(s.vat_amount),"glv-num")),i.appendChild(r(d?a:St(s.gl_amount),f)),i.appendChild(r(d?a:St(s.diff),p)),i.appendChild(r(s.account_codes||"","glv-doc")),o.appendChild(i)}),n.appendChild(o)}function Jn(e){const n=ee("glv-summary-table")&&ee("glv-summary-table").querySelector("tbody");if(!n)return;n.innerHTML="",[{label:ve("s_gl_total"),amount:e.gl_total,emph:!0,items:[],negate:!1},{label:ve("s_minus_gl_cr"),amount:-(e.gl_only_credit||0),emph:!1,items:e.gl_only_credit_items||[],negate:!0},{label:ve("s_plus_gl_dr"),amount:e.gl_only_debit||0,emph:!1,items:e.gl_only_debit_items||[],negate:!1},{label:ve("s_plus_vat_p"),amount:e.vat_only_positive||0,emph:!1,items:e.vat_only_positive_items||[],negate:!1},{label:ve("s_minus_vat_n"),amount:e.vat_only_negative||0,emph:!1,items:e.vat_only_negative_items||[],negate:!1},{label:ve("s_vat_total"),amount:e.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:o,amount:s,emph:i,items:r,negate:d})=>{const m=document.createElement("tr");m.className=i?"glv-summary-total":"glv-summary-sect";const p=document.createElement("td"),f=document.createElement("td");p.textContent=o,f.textContent=i?St(s):"",m.appendChild(p),m.appendChild(f),n.appendChild(m),(r||[]).forEach(c=>{const l=document.createElement("tr");l.className="glv-summary-item";const u=document.createElement("td"),v=document.createElement("td"),w=[c.doc_no,c.date,c.name].filter(Boolean);u.textContent="· "+w.join("  ·  ");const b=d?-(c.amount||0):c.amount||0;v.textContent=St(b),l.appendChild(u),l.appendChild(v),n.appendChild(l)})})}async function yr(e){try{const a=await(await fetch("/api/recon/gl-vat/"+e,{headers:Qe()})).json();if(!a||!a.ok)throw new Error("load_failed");ne.currentTaskId=e,ne.lastDetail=a.detail||[],ne.lastSummary=a.summary||{},Gn(a.stats||{}),Kn(ne.lastDetail),Jn(ne.lastSummary);const o=ee("glv-result");o&&(o.style.display=""),uo(),window.scrollTo({top:o?o.offsetTop-80:0,behavior:"smooth"})}catch(n){console.error("[gl-vat] load task failed:",n),alert(ve("error")+": "+(n.message||n))}}function uo(){var e=ee("glv-kpi-strip");e&&(e.style.display="");var n=ee("glv-section-summary");n&&n.setAttribute("data-collapsed","false");var a=ee("glv-section-detail");a&&a.setAttribute("data-collapsed","false")}function wr(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(e=>{const n=e.getAttribute("data-toggle"),a=document.getElementById(n);if(!a)return;const o=s=>{if(s.target&&s.target.closest("button")!==null&&!s.target.classList.contains("glv-section-head"))return;const i=a.getAttribute("data-collapsed")==="true";a.setAttribute("data-collapsed",i?"false":"true")};e.addEventListener("click",o),e.addEventListener("keydown",s=>{(s.key==="Enter"||s.key===" ")&&(s.preventDefault(),o(s))})})}function kr(e){const n=ee("glv-detail-count");n&&(n.textContent=e!=null?String(e):"")}const xt=10;var ot=[],Le=1;function xr(){Le=1,Jt();var e=((ee("glv-hist-search")||{}).value||"").trim().toLowerCase();if(e){var n=ee("glv-history-tbody");n&&n.querySelectorAll("tr").forEach(function(a){a.dataset.taskId&&(a.style.display=a.textContent.toLowerCase().indexOf(e)>=0?"":"none")})}}function Jt(){const e=ee("glv-history-table-wrap"),n=ee("glv-history-empty"),a=ee("glv-history-tbody"),o=ee("glv-history-pager"),s=ee("glv-history-pager-info"),i=ee("glv-history-prev"),r=ee("glv-history-next");if(!a)return;if(a.innerHTML="",!ot.length){e&&(e.style.display="none"),n&&(n.style.display=""),o&&(o.style.display="none");return}e&&(e.style.display=""),n&&(n.style.display="none");const d=Math.ceil(ot.length/xt);Le>d&&(Le=d);const m=(Le-1)*xt,p=ot.slice(m,m+xt);o&&(o.style.display=ot.length>xt?"":"none",s&&(s.textContent=Le+" / "+d),i&&(i.disabled=Le<=1),r&&(r.disabled=Le>=d)),p.forEach(c=>{const l=document.createElement("tr");l.dataset.taskId=c.id;const u=document.createElement("td");u.textContent=hr(c.created_at);const v=document.createElement("td");v.className="glv-history-file",v.title=(c.vat_filename||"")+" + "+(c.gl_filename||""),v.textContent=(c.vat_filename||"?")+" + "+(c.gl_filename||"?");const w=document.createElement("td");w.className="glv-num",w.textContent=(c.vat_row_count||0)+" / "+(c.gl_row_count||0);const b=document.createElement("td");b.className="glv-num",b.textContent=c.matched_count||0;const g=document.createElement("td");g.className="glv-num",g.textContent=c.diff_count||0;const h=document.createElement("td");h.className="glv-num",h.textContent=c.unmatched_count||0;const I=document.createElement("td");I.className="glv-history-actions";const y=(k,B,L,C)=>{const S=document.createElement("button");return S.type="button",L&&(S.className=L),S.title=B,S.setAttribute("aria-label",B),S.innerHTML=k,S.onclick=C,S},x='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',E='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',_='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';I.appendChild(y(x,ve("hist_load"),"",()=>yr(c.id))),I.appendChild(y(E,ve("hist_export"),"",()=>Er(c.id))),I.appendChild(y(_,ve("hist_delete"),"glv-del",()=>Br(c.id))),[u,v,w,b,g,h,I].forEach(k=>l.appendChild(k)),a.appendChild(l)})}function _r(){var e=ee("glv-history-prev"),n=ee("glv-history-next");e&&!e._glvBound&&(e._glvBound=!0,e.addEventListener("click",function(){Le>1&&(Le--,Jt())})),n&&!n._glvBound&&(n._glvBound=!0,n.addEventListener("click",function(){var a=Math.ceil(ot.length/xt);Le<a&&(Le++,Jt())}))}async function rt(){try{const n=await(await fetch("/api/recon/gl-vat/tasks",{headers:Qe()})).json();ot=n&&n.tasks||[],Le=1,Jt(),_r()}catch(e){console.error("[gl-vat] history load failed:",e)}}async function Er(e){try{const n="/api/recon/gl-vat/"+e+"/export?lang="+encodeURIComponent(ft()),a=await fetch(n,{headers:Qe()});if(!a.ok)throw new Error("HTTP "+a.status);const o=await a.blob(),s=document.createElement("a");s.href=URL.createObjectURL(o),s.download="GL_VAT_recon_"+e+".xlsx",document.body.appendChild(s),s.click(),setTimeout(()=>{URL.revokeObjectURL(s.href),s.remove()},200)}catch(n){console.error("[gl-vat] exportTask failed:",n),typeof showToast=="function"&&showToast(ve("error")+": "+(n.message||n),"error")}}async function Br(e){let n;if(typeof window.showConfirm=="function"?n=await window.showConfirm(ve("confirm_delete"),{danger:!0}):n=confirm(ve("confirm_delete")),!!n)try{const a=await fetch("/api/recon/gl-vat/"+e,{method:"DELETE",headers:Qe()});if(!a.ok)throw new Error("HTTP "+a.status);rt()}catch(a){console.error("[gl-vat] delete failed:",a),typeof showToast=="function"&&showToast(ve("error")+": "+(a.message||a),"error")}}async function Ir(){if(!ne.glFile||!ne.vatFile){typeof showToast=="function"&&showToast(ve("need_files"),"warn");return}ne.running=!0,At();const e=ee("glv-status"),n=ee("glv-progress"),a=ee("glv-progress-sub");e&&(e.className="vex-action-info muted",e.style.color="",e.innerHTML="<span>"+ve("running")+"</span>"),n&&(n.style.display=""),a&&(a.textContent=(ne.vatFile.name||"VAT")+" + "+(ne.glFile.name||"GL"));const o=new FormData,s=Ne("vatFile"),i=Ne("glFile");for(const d of s)o.append("vat_files",d,d.name);for(const d of i)o.append("gl_files",d,d.name);const r=(ee("glv-prefix")&&ee("glv-prefix").value||"4").trim()||"4";o.append("revenue_prefix",r),o.append("lang",ft());try{const d=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:Qe(),body:o});let m=null;try{m=await d.json()}catch{m=null}if(!d.ok||!m||!m.ok||!m.job_id)throw new Error(m&&m.detail||m&&m.error||"HTTP "+d.status);const p=ee("glv-progress-sub"),f=await window._reconPollJob(m.job_id,co(),{onProgress:v=>{p&&(p.textContent=window._reconProgressText(v,ft()))}});if(!f||f.status!=="done"||!f.result_id)throw f&&f.status==="failed"&&f.error_code?new Error(vr(f.error_code)):new Error(ve("error")||"Error");const c=await fetch("/api/recon/gl-vat/"+encodeURIComponent(f.result_id),{headers:Qe()});let l=null;try{l=await c.json()}catch{l=null}if(!c.ok||!l||!l.ok)throw new Error(l&&l.detail||l&&l.error||"HTTP "+c.status);ne.currentTaskId=l.task_id,ne.lastDetail=l.detail||[],ne.lastSummary=l.summary||{},Gn(l.stats||{}),Kn(ne.lastDetail),Jn(ne.lastSummary);const u=ee("glv-result");u&&(u.style.display=""),uo(),e&&(e.className="vex-action-info ok",e.style.color="",e.innerHTML="<span>"+ve("done")+" · GL "+(l.gl_row_count||0)+" · VAT "+(l.vat_row_count||0)+"</span>"),rt()}catch(d){console.error("[gl-vat] run failed:",d),e&&(e.className="vex-action-info",e.style.color="#ef4444",e.innerHTML="<span>"+ve("error")+": "+(d.message||d)+"</span>")}finally{ne.running=!1,n&&(n.style.display="none"),At()}}async function Lr(){if(ne.currentTaskId)try{const e="/api/recon/gl-vat/"+ne.currentTaskId+"/export?lang="+encodeURIComponent(ft()),n=await fetch(e,{headers:Qe()});if(!n.ok)throw new Error("HTTP "+n.status);const a=await n.blob(),o=document.createElement("a");o.href=URL.createObjectURL(a),o.download="GL_VAT_recon_"+ne.currentTaskId+".xlsx",document.body.appendChild(o),o.click(),setTimeout(()=>{URL.revokeObjectURL(o.href),o.remove()},200)}catch(e){console.error("[gl-vat] export failed:",e),typeof showToast=="function"&&showToast(ve("error")+": "+(e.message||e),"error")}}function Cr(){ne.running||Pt(),rt(),ne.lastDetail&&ne.lastDetail.length&&Kn(ne.lastDetail),ne.lastSummary&&Jn(ne.lastSummary)}function Sr(){if(ne.inited){rt();return}ne.inited=!0,ba("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),ba("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const e=ee("btn-glv-run");e&&e.addEventListener("click",Ir);const n=ee("btn-glv-export");n&&n.addEventListener("click",Lr);const a=ee("btn-glv-reset");a&&a.addEventListener("click",br);const o=ee("glv-hist-search");o&&o.addEventListener("input",xr),wr(),Gn(null),Pt(),window._loadGlvHistory=rt,rt(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",Cr)}window._glvRemoveFile=gr;window.GlVatRecon={ensureInit:Sr};window._glvPreviewFiles=function(e){return Ne(e==="vat"?"vatFile":"glFile")};const Tr=["flowaccount","peak","xero","quickbooks","express"],fo={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},Mr=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],$r=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],Hr="468b50c1-5593-4fd6-990d-515ce8085563";let fe={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function Rt(){const e=typeof _userInfo<"u"?_userInfo:null;return!!(e&&(e.role==="owner"||e.is_super_admin))}function Ar(){const e=typeof _userInfo<"u"?_userInfo:null;return!!(e&&e.id===Hr)}function R(e){return typeof escapeHtml=="function"?escapeHtml(e==null?"":String(e)):String(e??"")}function Ke(e,n){try{typeof showToast=="function"&&showToast(e,n||"info")}catch{}}function jr(e){return e==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+R(t("erp-map-col-client"))+"</div><div>"+R(t("erp-map-col-erp"))+"</div><div>"+R(t("erp-map-col-erp-code"))+"</div><div>"+R(t("erp-map-col-notes"))+"</div><div>"+R(t("erp-map-col-actions"))+"</div></div>":e==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+R(t("erp-map-col-erp"))+"</div><div>"+R(t("erp-map-col-category"))+"</div><div>"+R(t("erp-map-col-erp-code"))+"</div><div>"+R(t("erp-map-col-erp-name"))+"</div><div>"+R(t("erp-map-col-notes"))+"</div><div>"+R(t("erp-map-col-actions"))+"</div></div>":e==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+R(t("erp-map-col-item-name"))+"</div><div>"+R(t("erp-map-col-erp-product-code"))+"</div><div>"+R(t("erp-map-col-erp-name"))+"</div><div>"+R(t("erp-map-col-notes"))+"</div><div>"+R(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+R(t("erp-map-col-erp"))+"</div><div>"+R(t("erp-map-col-tax"))+"</div><div>"+R(t("erp-map-col-erp-tax-code"))+"</div><div>"+R(t("erp-map-col-notes"))+"</div><div>"+R(t("erp-map-col-actions"))+"</div></div>"}function un(e,n){let a='<select class="form-input" data-erp-field="'+n+'">';return a+='<option value="">'+R(t("erp-map-pick-erp"))+"</option>",Tr.forEach(function(o){const s=o===e?" selected":"";a+='<option value="'+o+'"'+s+">"+R(fo[o])+"</option>"}),a+="</select>",a}function Pr(e){let n='<select class="form-input" data-erp-field="client_id">';return n+='<option value="">'+R(t("erp-map-pick-client"))+"</option>",(fe.clientList||[]).forEach(function(a){const o=String(a.id)===String(e)?" selected":"";n+='<option value="'+a.id+'"'+o+">"+R(a.name||"#"+a.id)+"</option>"}),n+="</select>",n}function Dr(e){let n='<select class="form-input" data-erp-field="pearnly_category">';return n+='<option value="">'+R(t("erp-map-pick-cat"))+"</option>",Mr.forEach(function(a){const o=a===e?" selected":"";n+='<option value="'+a+'"'+o+">"+R(t("erp-map-cat-"+a))+"</option>"}),n+="</select>",n}function qr(e){let n='<select class="form-input" data-erp-field="pearnly_tax_kind">';return n+='<option value="">'+R(t("erp-map-pick-tax"))+"</option>",$r.forEach(function(a){const o=a===e?" selected":"";n+='<option value="'+a+'"'+o+">"+R(t("erp-map-tax-"+a))+"</option>"}),n+="</select>",n}function Rr(e){const n='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+R(t("erp-map-save"))+"</button>";return e==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+R(t("erp-map-col-client"))+'">'+Pr("")+'</div><div data-label="'+R(t("erp-map-col-erp"))+'">'+un("","erp_type")+'</div><div data-label="'+R(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+R(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+R(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+R(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>":e==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+R(t("erp-map-col-erp"))+'">'+un("","erp_type")+'</div><div data-label="'+R(t("erp-map-col-category"))+'">'+Dr("")+'</div><div data-label="'+R(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+R(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+R(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+R(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+R(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+R(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+R(t("erp-map-col-erp"))+'">'+un("","erp_type")+'</div><div data-label="'+R(t("erp-map-col-tax"))+'">'+qr("")+'</div><div data-label="'+R(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+R(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+R(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+R(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>"}function Fr(e,n,a){const o=a?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+R(n.id)+'" title="'+R(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',s='<span class="erp-map-erp-badge">'+R(fo[n.erp_type]||n.erp_type)+"</span>";if(e==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+R(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+R(n.client_name||"#"+n.client_id)+'</div><div data-label="'+R(t("erp-map-col-erp"))+'">'+s+'</div><div data-label="'+R(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+R(n.erp_code||"")+'</div><div data-label="'+R(t("erp-map-col-notes"))+'">'+R(n.notes||"")+"</div><div>"+o+"</div></div>";if(e==="accounts"){const r=t("erp-map-cat-"+(n.pearnly_category||"other"))||n.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+R(t("erp-map-col-erp"))+'">'+s+'</div><div data-label="'+R(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+R(r)+'</div><div data-label="'+R(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+R(n.erp_code||"")+'</div><div data-label="'+R(t("erp-map-col-erp-name"))+'">'+R(n.erp_name||"")+'</div><div data-label="'+R(t("erp-map-col-notes"))+'">'+R(n.notes||"")+"</div><div>"+o+"</div></div>"}if(e==="products")return'<div class="erp-map-row row-products"><div data-label="'+R(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+R(n.item_name||"")+'</div><div data-label="'+R(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+R(n.erp_code||"")+'</div><div data-label="'+R(t("erp-map-col-erp-name"))+'">'+R(n.erp_name||"")+'</div><div data-label="'+R(t("erp-map-col-notes"))+'">'+R(n.notes||"")+"</div><div>"+o+"</div></div>";const i=t("erp-map-tax-"+(n.pearnly_tax_kind||""))||n.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+R(t("erp-map-col-erp"))+'">'+s+'</div><div data-label="'+R(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+R(i)+'</span></div><div data-label="'+R(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+R(n.erp_code||"")+'</div><div data-label="'+R(t("erp-map-col-notes"))+'">'+R(n.notes||"")+"</div><div>"+o+"</div></div>"}(function(){async function e(f,c){const l=localStorage.getItem("mrpilot_token");if(l&&!(fe.loaded[f]&&!c))try{const u=await fetch("/api/erp/mappings/"+f,{headers:{Authorization:"Bearer "+l}});if(!u.ok)throw new Error("http_"+u.status);const v=await u.json();fe.items[f]=v.items||[],fe.loaded[f]=!0}catch{fe.items[f]=[],fe.loaded[f]=!1}}async function n(f){if(fe.clientLoaded)return;const c=localStorage.getItem("mrpilot_token");if(c)try{const l=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+c}});if(!l.ok)throw new Error("http_"+l.status);const u=await l.json();fe.clientList=(u.clients||u.items||[]).filter(v=>v.is_active!==!1),fe.clientLoaded=!0}catch{fe.clientList=[]}}function a(){const f=document.getElementById("erp-map-pane-wrap");if(!f)return;const c=!Rt();let l="";c&&(l+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+R(t("erp-map-readonly-tip"))+"</div>"),l+='<div class="erp-map-toolbar">',!c&&fe.sub!=="products"&&(l+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+R(t("erp-map-add-row"))+"</button>"),l+="</div>",l+='<div class="erp-map-table" id="erp-map-table-host"></div>',f.innerHTML=l,o();const u=document.getElementById("erp-map-dev-bar");u&&(u.style.display=Rt()&&Ar()?"":"none")}function o(){const f=document.getElementById("erp-map-table-host");if(!f)return;const c=fe.sub,l=fe.items[c]||[],u=fe.addingNew[c],v=!Rt();if(!l.length&&!u){f.innerHTML='<div class="erp-map-empty"><strong>'+R(t("erp-map-empty-"+c))+"</strong>"+R(t("erp-map-empty-"+c+"-sub"))+"</div>";return}let w="";w+=jr(c),u&&!v&&(w+=Rr(c)),l.forEach(function(b){w+=Fr(c,b,v)}),f.innerHTML=w}async function s(f){const c=fe.sub,l={};f.querySelectorAll("[data-erp-field]").forEach(function(b){l[b.dataset.erpField]=(b.value||"").trim()});const u=localStorage.getItem("mrpilot_token");if(!u)return;let v={},w="/api/erp/mappings/"+c;if(c==="clients"){if(!l.client_id||!l.erp_type||!l.erp_code){Ke(t("erp-map-save-fail"),"error");return}v={client_id:parseInt(l.client_id,10),erp_type:l.erp_type,erp_code:l.erp_code,notes:l.notes||""}}else if(c==="accounts"){if(!l.erp_type||!l.pearnly_category||!l.erp_code){Ke(t("erp-map-save-fail"),"error");return}v={erp_type:l.erp_type,pearnly_category:l.pearnly_category,erp_code:l.erp_code,erp_name:l.erp_name||"",notes:l.notes||""}}else{if(!l.erp_type||!l.pearnly_tax_kind||!l.erp_code){Ke(t("erp-map-save-fail"),"error");return}v={erp_type:l.erp_type,pearnly_tax_kind:l.pearnly_tax_kind,erp_code:l.erp_code,notes:l.notes||""}}try{const b=await fetch(w,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+u},body:JSON.stringify(v)});if(!b.ok)throw new Error("http_"+b.status);fe.addingNew[c]=!1,await e(c,!0),o(),Ke(t("erp-map-saved-toast"),"success")}catch{Ke(t("erp-map-save-fail"),"error")}}async function i(f){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const l=fe.sub,u=localStorage.getItem("mrpilot_token");try{const v=await fetch("/api/erp/mappings/"+l+"/"+encodeURIComponent(f),{method:"DELETE",headers:{Authorization:"Bearer "+u}});if(!v.ok)throw new Error("http_"+v.status);await e(l,!0),o(),Ke(t("erp-map-deleted-toast"),"success")}catch{Ke(t("erp-map-delete-fail"),"error")}}async function r(){await n(),await e(fe.sub,!1),a()}function d(f){f!==fe.sub&&(fe.sub=f,fe.addingNew[f]=!1,["clients","accounts","taxes","products"].forEach(function(c){c!==f&&(fe.addingNew[c]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(c){c.classList.toggle("active",c.dataset.erpSubtab===f)}),e(f,!1).then(function(){a()}))}function m(){fe.bound||(fe.bound=!0,document.addEventListener("click",function(f){const c=f.target.closest(".erp-subtab[data-erp-subtab]");if(c){f.preventDefault();const b=c.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(g){g.classList.toggle("active",g.dataset.erpSubtab===b)}),document.querySelectorAll(".erp-subpanel").forEach(function(g){g.classList.toggle("active",g.dataset.erpSubpanel===b)}),b==="mappings"&&setTimeout(r,50);return}const l=f.target.closest(".erp-map-subtab[data-erp-subtab]");if(l){f.preventDefault(),d(l.dataset.erpSubtab);return}if(f.target.closest("#erp-map-add-btn")){if(f.preventDefault(),!Rt())return;fe.addingNew[fe.sub]=!0,o();return}const v=f.target.closest('[data-erp-save="new"]');if(v){f.preventDefault();const b=v.closest('[data-erp-row="new"]');b&&s(b);return}const w=f.target.closest("[data-erp-del]");if(w){f.preventDefault(),i(w.dataset.erpDel);return}}))}function p(){const f=document.getElementById("erp-map-pane-wrap");f&&f.children.length>0&&a(),document.querySelectorAll(".erp-map-subtab").forEach(function(c){const l="erp-map-subtab-"+c.dataset.erpSubtab,u=t(l);u&&u!==l&&(c.textContent=u)})}m(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",p)})();(function(){let e=null,n=0,a=!1;function o(_){return typeof escapeHtml=="function"?escapeHtml(_==null?"":String(_)):String(_??"")}function s(_,k){try{typeof showToast=="function"&&showToast(_,k||"info")}catch{}}async function i(_){const k=Date.now();if(e&&k-n<3e4)return e;const B=localStorage.getItem("mrpilot_token");if(!B)return[];try{const L=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+B}});if(!L.ok)return[];const C=await L.json();return e=C&&C.connectors||[],n=k,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function d(_){try{localStorage.setItem("pn_push_default_connector",_||"")}catch{}}function m(_){if(!_||!_.length)return null;const k=r();if(k){const L=_.find(C=>C.id===k);if(L)return L}const B=_.find(L=>L.is_default);return B||_[0]}function p(_){if(!_)return!1;const k=String(_.status||"").toLowerCase();return k==="exception"||k==="exception_pending"||k==="rejected"}function f(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(_){const k=_&&(_.type||_.id);return k==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':k==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function l(_,k){if(!_||!k)return!1;const B=document.getElementById("btn-push-default");B&&(B.disabled=!0,B.classList.add("loading"));const L=localStorage.getItem("mrpilot_token");try{let C,S={method:"POST",headers:{Authorization:"Bearer "+L}};_.type==="xero"?C="/api/erp/xero/push/"+encodeURIComponent(k):(C="/api/erp/push",S.headers["Content-Type"]="application/json",S.body=JSON.stringify({history_id:k,endpoint_id:_.endpoint_id||void 0}));const M=await fetch(C,S);let $={};try{$=await M.json()}catch{}if(!M.ok){let q=$&&$.detail||"unknown";typeof q=="object"&&(q=q.code||JSON.stringify(q));let H=String(q||"unknown");if(_.type==="xero"){const T=H.replace(/^xero\./,"").toLowerCase(),D=t("xero-"+T);D&&D!=="xero-"+T&&(H=D)}return s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",H),"error"),!1}if($&&$.ok===!1){let q=$.error_msg||$.error_code||"unknown";return q=String(q).slice(0,200),s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",q),"error"),!1}return s(t("unified-push-ok").replace("{name}",_.name),"success"),!0}catch(C){return s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",C.message||"network"),"error"),!1}finally{B&&(B.disabled=!1,B.classList.remove("loading"))}}async function u(_,k){for(const B of _)await l(B,k)}function v(_,k){const B=document.createElement("div");B.className="pn-push-dropdown",B.id="pn-push-dropdown";const L=(_||[]).map(S=>{const M=!!(k&&S.id===k.id),$=S.method==="download"?t("unified-push-tag-download"):M?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(S.id)+'"><span class="pn-pd-icon">'+c(S)+'</span><span class="pn-pd-name">'+o(S.name)+"</span>"+($?'<span class="pn-pd-tag">'+o($)+"</span>":"")+(M?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),C=_&&_.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",_.length))+"</span></div>":"";return B.innerHTML=L+C,B}function w(){const _=document.getElementById("pn-push-dropdown");_&&_.remove()}async function b(){if(document.getElementById("pn-push-dropdown")){w();return}const _=await i()||[],k=m(_),B=v(_,k),L=document.getElementById("pn-push-wrap");L&&L.appendChild(B)}async function g(){const _=await i()||[],k=m(_);if(!k)return;const B=f(),L=B&&(B._historyId||B.history_id);if(L){if(p(B)){s(t("unified-push-disabled-exc"),"warn");return}await l(k,L)}}async function h(_){w();const k=await i()||[],B=f(),L=B&&(B._historyId||B.history_id);if(!L)return;if(p(B)){s(t("unified-push-disabled-exc"),"warn");return}if(_==="__all__"){await u(k,L);return}const C=k.find(S=>S.id===_);C&&(d(_),await l(C,L),y())}async function I(){const _=document.getElementById("drawer-history-save");if(!_||_.querySelector("#pn-push-wrap"))return;const k=document.createElement("div");k.id="pn-push-wrap",k.className="pn-push-wrap",k.dataset.loading="1",_.insertBefore(k,_.firstChild),["btn-push-erp","btn-xero-push"].forEach($=>{_.querySelectorAll("#"+$).forEach(q=>{q.style.display="none"})});const B=await i()||[],L=m(B),C=B.length>0;if(!C)k.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const $=B.length>1;k.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+c(L)+"<span>"+o(t("unified-push-to").replace("{name}",L?L.name:""))+"</span></button>"+($?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete k.dataset.loading;const S=k.querySelector("#btn-push-default");S&&C&&S.addEventListener("click",g);const M=k.querySelector("#btn-push-arrow");M&&M.addEventListener("click",function($){$.stopPropagation(),b()}),a||(a=!0,document.addEventListener("click",function($){const q=$.target.closest(".pn-pd-item");if(q){const H=q.getAttribute("data-cid");h(H);return}$.target.closest("#btn-push-arrow")||w()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",y))}function y(){const _=document.getElementById("pn-push-wrap");_&&(_.remove(),e=null,n=0,I())}function x(){const _=document.getElementById("drawer-history-save");if(!_||!_.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(B=>{_.querySelectorAll("#"+B).forEach(L=>{L.style.display!=="none"&&(L.style.display="none")})});const k=_.querySelectorAll("#pn-push-wrap");if(k.length>1)for(let B=1;B<k.length;B++)k[B].remove()}function E(){try{const _=function(){return document.getElementById("drawer-body")},k=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&I(),x()}),B=_();if(B)k.observe(B,{childList:!0,subtree:!0});else{const L=new MutationObserver(function(){const C=_();C&&(k.observe(C,{childList:!0,subtree:!0}),L.disconnect())});L.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&I(),x()},200)}catch{}}E()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",d=t(r);d&&d!==r&&(i.textContent=d)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const m=document.getElementById("erp-onboard-title"),p=document.getElementById("erp-onboard-body"),f=document.getElementById("erp-onboard-ok"),c=document.getElementById("erp-onboard-later");m&&(m.textContent=t("erp-onboard-title")),p&&(p.textContent=t("erp-onboard-body")),f&&(f.textContent=t("erp-onboard-ok")),c&&(c.textContent=t("erp-onboard-later"))}r();function d(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}d();try{const m=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');m&&m.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}d()}),i.addEventListener("click",function(m){m.target===i&&d()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),d=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||d)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,i=s[a]||s.th||s.en,r=n.stage_total,d=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const m={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+m.replace("{d}",d||0).replace("{t}",r)}return i},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,i=o.maxMs||1200*1e3,r=Date.now();let d=0;for(;;){let m=null;try{const p=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{m=await p.json()}catch{m=null}(!p.ok||!m||!m.ok)&&(m=null)}catch{m=null}if(m){if(d=0,o.onProgress)try{o.onProgress(m.progress||{},m)}catch{}if(m.status==="done"||m.status==="failed"||m.status==="needs_review"||m.status==="needs_mapping")return m}else if(++d>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(p=>setTimeout(p,s))}}})();const U={initialized:!1,stmtFiles:[],glFiles:[],currentTask:null,currentFilter:"all",allRows:[],brv2Search:{stmt:"",gl:""},cachedHistoryTasks:[],brv2Page:1},z=e=>document.getElementById(e);function Fe(e){if(e==null)return"—";const n=Number(e);return isNaN(n)?"—":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function ya(e){return e?String(e).slice(0,10).split("-").reverse().join("/"):"—"}function ge(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function zr(e,n){n=window._currentLang||n||"th";const a={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},o={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},s=a[e]||o;return s[n]||s.th||s.en}function Nr(e){return e?e<1024?e+" B":e<1048576?(e/1024).toFixed(1)+" KB":(e/1048576).toFixed(1)+" MB":""}function nt(e,n){return window.t&&window.t(e)||n}function De(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function fn(e){return Number.isFinite(+e)?(+e).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}var mo="pearnly.brv2.lastAnchorOcr";function Or(e){try{var n=e&&e._anchor_ocr;if(!n||typeof n!="object")return;var a={stmt_opening:Number.isFinite(+n.stmt_opening)?+n.stmt_opening:null,gl_opening:Number.isFinite(+n.gl_opening)?+n.gl_opening:null,gl_closing:Number.isFinite(+n.gl_closing)?+n.gl_closing:null,stmt_closing:Number.isFinite(+n.stmt_closing)?+n.stmt_closing:null,ts:Date.now()};localStorage.setItem(mo,JSON.stringify(a))}catch{}}function Vr(){try{var e=localStorage.getItem(mo);if(!e)return null;var n=JSON.parse(e);return!n||typeof n!="object"?null:n}catch{return null}}function Ur(){var e=Vr();if(e){var n={"brv2-anchor-stmt-opening":e.stmt_opening,"brv2-anchor-gl-opening":e.gl_opening,"brv2-anchor-gl-closing":e.gl_closing,"brv2-anchor-stmt-closing":e.stmt_closing},a=0;Object.keys(n).forEach(function(d){var m=document.getElementById(d);if(m&&m.value===""){var p=n[d];if(Number.isFinite(p)){m.value=p.toFixed(2);var f=m.closest&&m.closest(".brv2-anchor-cell");f&&f.classList.add("is-prefilled"),a+=1}}});var o=document.getElementById("brv2-anchor-eq"),s=document.getElementById("brv2-anchor-eq-val");if(o&&s&&Number.isFinite(e.stmt_opening)&&Number.isFinite(e.gl_opening)){var i=e.stmt_opening-e.gl_opening;s.textContent=i.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),o.style.display=""}if(a>0){var r=document.getElementById("brv2-anchor-prefill-banner");r&&r.classList.add("show")}}}function Gr(){var e=document.getElementById("brv2-anchor-prefill-banner");if(e){var n=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(a){var o=document.getElementById(a);if(o){var s=o.closest&&o.closest(".brv2-anchor-cell");s&&s.classList.contains("is-prefilled")&&(n=!0)}}),e.classList.toggle("show",n)}}var Kr=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function Jr(e){var n=document.getElementById("brv2-summary-collapse");if(!(!n||!n.parentNode)){var a=document.getElementById("brv2-anchor-audit"),o=e&&e._anchor_overrides;if(!o||typeof o!="object"||Object.keys(o).length===0){a&&a.parentNode&&a.parentNode.removeChild(a);return}a||(a=document.createElement("div"),a.id="brv2-anchor-audit",a.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",n.parentNode.insertBefore(a,n.nextSibling));var s=Kr.map(function(i){var r=o[i[0]];if(!r)return"";var d=+r.ocr||0,m=+r.user||0,p=m-d,f=p>0?"+":(p<0,""),c=Math.abs(p)<.005?"#6b7280":p>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+De(nt(i[1],i[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+De(fn(d))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+De(fn(m))+'</td><td style="padding:6px 10px;color:'+c+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+De(f+fn(p))+"</td></tr>"}).join("");a.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+De(nt("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+De(nt("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+De(nt("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+De(nt("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+De(nt("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+s+"</tbody></table>"}}function Wt(e){const n=z("brv2-summary-collapse"),a=z("brv2-detail-collapse"),o=z("brv2-export-btn"),s=z("brv2-new-btn"),i=z("brv2-parse-info-wrap");n&&(n.style.display=e?"":"none"),a&&(a.style.display=e?"":"none"),o&&(o.style.display=e?"":"none"),s&&(s.style.display=e?"":"none"),!e&&i&&(i.style.display="none");const r=z("brv2-warnings");!e&&r&&(r.style.display="none",r.innerHTML="")}function Wr(e){const n=z("brv2-parse-info-wrap"),a=z("brv2-parse-info-body");if(!n||!a)return;const o=e.parse_info;if(!o){n.style.display="none";return}const s=window._currentLang||"zh",i={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},r=l=>(i[l]||{})[s]||(i[l]||{}).zh||l,d=[...(o.stmt_files||[]).map(l=>({...l,_type:"stmt",_extra:l.bank_code||""})),...(o.gl_files||[]).map(l=>({...l,_type:"gl",_extra:(l.accounts||[]).join(", ")}))],m={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},p=l=>{const u=String(l||"");return/Cannot detect bank statement column headers/i.test(u)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(u)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(u)?"stmt_no_rows":/unsupported format/i.test(u)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(u)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(u)?"ocr_failed":null},f=l=>{const u=l.error_code||p(l.error);if(u&&m[u]){const v=window._currentLang||"zh";return m[u][v]||m[u].zh}return String(l.error||"").slice(0,80)},c=l=>!l.ok&&l.error?`<span style="color:#dc2626">${r("fail")} — ${ge(f(l))}</span>`:l.rows?`<span style="color:#059669">${r("ok")} (${l.rows})</span>`:`<span style="color:#d97706">${r("warn")}</span>`;a.innerHTML=`
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
                ${d.map(l=>`<tr>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${l._type==="stmt"?r("stmt"):r("gl")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${ge(l.file||"")}">${ge(l.file||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${l.rows||0}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${ge(l._extra||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb">${c(l)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`,n.style.display=""}async function vo(e){const n=localStorage.getItem("mrpilot_token")||"",a=window._currentLang||"zh";try{const o=await fetch("/api/recon/bank-v2/"+e+"/export?lang="+a,{headers:{Authorization:"Bearer "+n}});if(!o.ok){const f=await o.json().catch(()=>({}));window.showToast&&window.showToast(f.detail||"Export failed","error");return}const s=await o.blob(),r=(o.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),d=r?r[1].replace(/['"]/g,""):"reconciliation.xlsx",m=URL.createObjectURL(s),p=document.createElement("a");p.href=m,p.download=d,document.body.appendChild(p),p.click(),document.body.removeChild(p),URL.revokeObjectURL(m)}catch(o){window.showToast&&window.showToast("Export error: "+o.message,"error")}}function Yr(e,n){const a=z("brv2-summary-collapse");let o=z("brv2-warnings");const s=window._currentLang||"zh",i={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[s]||"⏭ ",r=[];if((n||[]).forEach(d=>r.push(i+" "+d)),(e||[]).forEach(d=>r.push(d)),!r.length){o&&(o.style.display="none");return}if(!o)if(o=document.createElement("div"),o.id="brv2-warnings",a&&a.parentNode)a.parentNode.insertBefore(o,a);else return;o.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",o.innerHTML=r.map(d=>"<div>"+ge(d)+"</div>").join("")}function Wn(e){Wr(e),Yr(e.warnings||[],e.skipped_files||[]),!e.ok&&e.error&&window.showToast&&window.showToast(e.error,"error");const n=e.stats||{},a=e.summary||{},o=n.matched||0,s=(n.gl_debit_only||0)+(n.gl_credit_only||0),i=(n.stmt_withdrawal_only||0)+(n.stmt_deposit_only||0),r=Number(a.formula_diff||0),d=Math.abs(r)<.05;z("brv2-kpi-matched")&&(z("brv2-kpi-matched").textContent=o),z("brv2-kpi-diff")&&(z("brv2-kpi-diff").textContent=Fe(r)),z("brv2-kpi-unmatched")&&(z("brv2-kpi-unmatched").textContent=s+i);const m=z("brv2-kpi-diff-icon");m&&(m.style.background=d?"#d1fae5":"#fee2e2",m.style.color=d?"#065f46":"#b91c1c");const p=z("brv2-formula-sub");if(p){const v=window._currentLang||"zh";p.textContent=d?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[v]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[v]||"差 ")+Fe(r)}const f=z("brv2-detail-sub");if(f){const v=window._currentLang||"zh",w={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[v]||"共 {n} 行";f.textContent=w.replace("{n}",U.allRows.length)}function c(v,w,b){const g=z(v);g&&(g.textContent=(b&&w>0?"(":"")+Fe(b?-w:w)+(b&&w>0?")":""))}c("brf-gl-close",a.gl_closing||0),c("brf-open-diff",a.opening_diff||0),c("brf-gl-debit-only",a.gl_debit_only_amount||0,!0),c("brf-gl-credit-only",a.gl_credit_only_amount||0),c("brf-stmt-wd-only",a.stmt_withdrawal_only_amount||0,!0),c("brf-stmt-dep-only",a.stmt_deposit_only_amount||0),c("brf-calc-close",a.formula_stmt_closing||0),c("brf-stmt-close",a.stmt_closing||0),z("brf-diff")&&(z("brf-diff").textContent=Fe(r));const l=z("brv2-fcell-diff");l&&l.classList.toggle("brv2-fcell-diff-ok",d);const u=z("brv2-export-btn");u&&(u.onclick=()=>{U.currentTask&&vo(U.currentTask.task_id)}),Jr(a),Wt(!0),ho()}function ho(){const e=z("brv2-tbody");if(!e)return;const n=U.allRows.filter(i=>U.currentFilter==="all"?!0:U.currentFilter==="matched"?i.match_status==="matched":U.currentFilter==="gl_only"?i.match_status.startsWith("gl_"):U.currentFilter==="stmt_only"?i.match_status.startsWith("stmt_"):!0);if(n.length===0){const i={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";e.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${i}</td></tr>`;return}const a=window._currentLang||"zh",o={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[a],s={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[a];e.innerHTML=n.map(i=>{const r=i.match_status,d=i.match_layer;let m="",p="";r==="matched"?(d===1&&(m="matched",p='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),d===2&&(m="matched-l2",p='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),d===3&&(m="matched-l3",p='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):r==="gl_debit_only"||r==="gl_credit_only"?(m="gl-only",p='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(m="stmt-only",p=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[a]||"账单"}</span>`);let f="";return i.stmt_balance_ok===!1&&(f+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${ge(o)}">⚠</span>`,m+=" brv2-row-warn"),i.stmt_confidence==="low"&&(f+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${ge(s)}">◌</span>`,m.includes("brv2-row-warn")||(m+=" brv2-row-warn-soft")),`<tr class="${m.trim()}">
          <td>${p}${f}</td>
          <td>${ge(ya(i.stmt_date))}</td>
          <td title="${ge(i.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${ge(i.stmt_desc)}</td>
          <td class="num">${i.stmt_withdrawal?Fe(i.stmt_withdrawal):""}</td>
          <td class="num">${i.stmt_deposit?Fe(i.stmt_deposit):""}</td>
          <td>${ge(ya(i.gl_date))}</td>
          <td title="${ge(i.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${ge(i.gl_doc_no)}</td>
          <td class="num">${i.gl_debit?Fe(i.gl_debit):""}</td>
          <td class="num">${i.gl_credit?Fe(i.gl_credit):""}</td>
          <td>${d?"L"+d:"—"}</td>
        </tr>`}).join("")}async function Tt(){const e=localStorage.getItem("mrpilot_token")||"";try{const a=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+e}})).json();Yt(a.tasks||[])}catch{const a=z("brv2-history-empty"),o=window._currentLang||"zh",s={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[o]||"加载失败";a&&(a.textContent=s,a.style.display="");const i=z("brv2-history-table-wrap");i&&(i.style.display="none")}}const lt=10;function wa(){const e=z("brv2-history-pager"),n=z("brv2-history-pager-info"),a=z("brv2-history-prev"),o=z("brv2-history-next");if(!e)return;if(U.cachedHistoryTasks.length<=lt){e.style.display="none";return}e.style.display="";const s=Math.ceil(U.cachedHistoryTasks.length/lt);n&&(n.textContent=U.brv2Page+" / "+s),a&&(a.disabled=U.brv2Page<=1),o&&(o.disabled=U.brv2Page>=s)}function Xr(){const e=z("brv2-history-prev"),n=z("brv2-history-next");e&&!e._brv2Bound&&(e._brv2Bound=!0,e.addEventListener("click",()=>{U.brv2Page>1&&(U.brv2Page--,Yt(U.cachedHistoryTasks))})),n&&!n._brv2Bound&&(n._brv2Bound=!0,n.addEventListener("click",()=>{const a=Math.ceil(U.cachedHistoryTasks.length/lt);U.brv2Page<a&&(U.brv2Page++,Yt(U.cachedHistoryTasks))}))}function Yt(e){e!==void 0&&(U.cachedHistoryTasks=e||[],U.brv2Page=1);const n=U.cachedHistoryTasks,a=z("brv2-history-empty"),o=z("brv2-history-table-wrap"),s=z("brv2-history-tbody");if(!s)return;const i=window._currentLang||"zh";if(!n.length){const u={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[i]||"暂无对账记录";a&&(a.textContent=u,a.style.display=""),o&&(o.style.display="none"),wa();return}a&&(a.style.display="none"),o&&(o.style.display="");const r=Math.ceil(n.length/lt);U.brv2Page>r&&(U.brv2Page=r);const d=(U.brv2Page-1)*lt,m=n.slice(d,d+lt),p=localStorage.getItem("mrpilot_token")||"",f='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',c='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',l='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';s.innerHTML="",m.forEach(u=>{const v=Number(u.formula_diff||0),w=Math.abs(v)<.05,b=(u.stmt_files||"").split(";").map(T=>T.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),g=(u.gl_files||"").split(";").map(T=>T.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),h=u.created_at?String(u.created_at).slice(0,16).replace("T"," "):"",I=document.createElement("tr");I.dataset.taskId=u.id;const y=document.createElement("td");y.textContent=h;const x=document.createElement("td");x.className="glv-history-file",x.title=b+" + "+g,x.textContent=b+" + "+g;const E=document.createElement("td");E.className="glv-num",E.textContent=(u.stmt_row_count||0)+" / "+(u.gl_row_count||0);const _=document.createElement("td");_.className="glv-num",_.textContent=u.matched_count||0;const k=document.createElement("td");k.className="glv-num",k.textContent=u.unmatched_gl||0;const B=document.createElement("td");B.className="glv-num",B.textContent=u.unmatched_stmt||0;const L=document.createElement("td");L.className="glv-num",L.style.color=w?"#059669":"#dc2626",L.textContent=w?"✓":Fe(v);const C=document.createElement("td");C.className="glv-history-actions";const S=(T,D,O,P)=>{const j=document.createElement("button");return j.type="button",j.title=D,j.setAttribute("aria-label",D),O&&(j.className=O),j.innerHTML=T,j.onclick=N=>{N.stopPropagation(),P()},j},M={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[i]||"删除?",$={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[i]||"加载",q={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[i]||"导出",H={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[i]||"删除";C.appendChild(S(f,$,"",()=>ka(u.id,p))),C.appendChild(S(c,q,"",()=>vo(u.id))),C.appendChild(S(l,H,"glv-del",async()=>{await showConfirm(M,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+u.id,{method:"DELETE",headers:{Authorization:"Bearer "+p}}),Tt())})),[y,x,E,_,k,B,L,C].forEach(T=>I.appendChild(T)),I.style.cursor="pointer",I.addEventListener("click",async T=>{T.target.closest(".glv-del")||T.target.closest("button")||await ka(u.id,p)}),s.appendChild(I)}),wa(),go()}function go(){const e=((z("brv2-hist-search")||{}).value||"").trim().toLowerCase(),n=z("brv2-history-tbody");n&&n.querySelectorAll("tr").forEach(a=>{a.dataset.taskId&&(a.style.display=!e||a.textContent.toLowerCase().includes(e)?"":"none")})}async function ka(e,n){try{const o=await(await fetch("/api/recon/bank-v2/"+e,{headers:{Authorization:"Bearer "+n}})).json();if(!o.ok)return;U.currentTask={task_id:o.task_id,...o},U.allRows=o.detail||[],U.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(s=>s.classList.toggle("active",s.dataset.filter==="all")),Wn(U.currentTask)}catch{}}function He(e){const n=e==="stmt"?U.stmtFiles:U.glFiles,a=z(`brv2-${e}-name`);if(a)if(n.length===0)a.textContent="";else{const s=window._currentLang||"zh",i={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};a.textContent=n.length+(i[s]||" 个文件")}const o=z("brv2-preview-panel");o&&o.style.display!=="none"&&kn(e),Zr()}function Zr(){const e=z("brv2-toggle-preview"),n=z("brv2-preview-panel"),a=U.stmtFiles.length+U.glFiles.length>0;e&&(e.style.display=a?"":"none"),!a&&n&&(n.style.display="none",e&&e.classList.remove("open"))}function Qr(){kn("stmt"),kn("gl")}function kn(e){const n=z(e==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!n)return;const a=e==="stmt"?U.stmtFiles:U.glFiles,o=window._currentLang||"zh",s={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},i=(s[e]||{})[o]||s[e].zh,r=ge(window.t&&window.t("vex-preview-search")||"搜索文件名..."),d=ge(window.t&&window.t("vex-preview-clear-all")||"全清"),m=U.brv2Search[e]||"";n.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+ge(i)+' <span class="vex-pp-col-count">'+a.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+e+'" type="text" placeholder="'+r+'" value="'+ge(m)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+e+'" type="button">'+d+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+e+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+e+'-pg"></div>';const p=z("brv2-pp-search-"+e);p&&p.addEventListener("input",function(c){U.brv2Search[e]=c.target.value,xa(e)});const f=z("brv2-pp-clearall-"+e);f&&f.addEventListener("click",function(){e==="stmt"?U.stmtFiles.length=0:U.glFiles.length=0,He(e),ze()}),xa(e)}function xa(e){const n=z("brv2-pp-"+e+"-list"),a=z("brv2-pp-"+e+"-pg");if(!n)return;const o=e==="stmt"?U.stmtFiles:U.glFiles,s=(U.brv2Search[e]||"").toLowerCase(),i=s?o.filter(m=>m.name.toLowerCase().includes(s)):o.slice(),r='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',d='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(n.innerHTML=i.map((m,p)=>'<div class="vex-pp-file-row">'+r+'<span class="vex-pp-fi-name" title="'+ge(m.name)+'">'+ge(m.name)+'</span><span class="vex-pp-fi-size">'+Nr(m.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+e+'" data-idx="'+o.indexOf(m)+'" aria-label="remove">'+d+"</button></div>").join(""),n.querySelectorAll(".vex-pp-fi-del").forEach(function(m){m.addEventListener("click",function(){const p=parseInt(m.dataset.idx,10);m.dataset.zone==="stmt"?U.stmtFiles.splice(p,1):U.glFiles.splice(p,1),He(m.dataset.zone),ze()})}),a){const m=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";a.textContent=m.replace("{n}",i.length).replace("{m}",o.length)}}function el(){const e=z("brv2-toggle-preview");e&&!e._reconBound&&(e._reconBound=!0,e.addEventListener("click",function(){const n=z("brv2-preview-panel"),a=z("brv2-toggle-preview-label"),o=n&&n.style.display!=="none";n&&(n.style.display=o?"none":""),e.classList.toggle("open",!o),a&&(a.textContent=o?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),o||Qr()}))}function ze(){const e=z("brv2-run-btn"),n=z("brv2-status"),a=U.stmtFiles.length>0,o=U.glFiles.length>0;if(e&&(e.disabled=!(a&&o)),n){const s=window._currentLang||"zh";if(!a&&!o){const i={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};n.textContent=i[s]||i.zh}else if(a)if(o){const i={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};n.textContent=i[s]||i.zh}}}function _a(e,n,a){const o=z(e),s=z(n);!o||!s||(o.addEventListener("click",()=>s.click()),o.addEventListener("keydown",i=>{(i.key==="Enter"||i.key===" ")&&(i.preventDefault(),s.click())}),o.addEventListener("dragover",i=>{i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",()=>o.classList.remove("drag-over")),o.addEventListener("drop",i=>{i.preventDefault(),o.classList.remove("drag-over");const r=Array.from(i.dataTransfer.files||[]);a==="stmt"?U.stmtFiles.push(...r):U.glFiles.push(...r),He(a),ze()}),s.addEventListener("change",()=>{const i=Array.from(s.files||[]);a==="stmt"?U.stmtFiles.push(...i):U.glFiles.push(...i),s.value="",He(a),ze()}))}function Be(e){const n=z("brv2-progress"),a=z("brv2-run-btn"),o=z("brv2-error");n&&(n.style.display=e?"":"none"),a&&(a.disabled=e),o&&(o.style.display="none")}function $e(e){const n=z("brv2-error");n&&(n.textContent=e,n.style.display="",n.scrollIntoView({behavior:"smooth",block:"nearest"})),Be(!1),ze(),window.showToast&&window.showToast(e,"error")}async function xn(){if(U.stmtFiles.length===0||U.glFiles.length===0)return;const e=localStorage.getItem("mrpilot_token")||"",n=window._currentLang||"zh",a=(z("brv2-acct-select")||{}).value||"";Wt(!1),Be(!0);try{const o=new FormData;U.stmtFiles.forEach(u=>o.append("stmt_files",u)),U.glFiles.forEach(u=>o.append("gl_files",u)),o.append("gl_account",a),o.append("lang",n);const s=parseFloat((z("brv2-anchor-gl-closing")||{}).value),i=parseFloat((z("brv2-anchor-stmt-closing")||{}).value),r=parseFloat((z("brv2-anchor-stmt-opening")||{}).value),d=parseFloat((z("brv2-anchor-gl-opening")||{}).value);Number.isFinite(s)&&o.append("gl_closing_override",s),Number.isFinite(i)&&o.append("stmt_closing_override",i),Number.isFinite(r)&&o.append("stmt_opening_override",r),Number.isFinite(d)&&o.append("gl_opening_override",d);const m=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+e},body:o});let p=null;try{p=await m.json()}catch{p=null}if(p&&p.needs_mapping){Be(!1),window.ReconMapping?window.ReconMapping.show(p,{token:e,lang:n,onConfirmed:function(){xn()}}):$e(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!m.ok||!p||!p.ok||!p.job_id){Be(!1),p&&(p.detail||p.error)?$e(_humanizeBackendError(p.detail||p.error,"Error "+m.status)):$e(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const f=z("brv2-progress-sub"),c=await window._reconPollJob(p.job_id,e,{onProgress:u=>{f&&(f.textContent=window._reconProgressText(u,n))}});if(c&&c.status==="needs_mapping"&&c.mapping){Be(!1),window.ReconMapping?window.ReconMapping.show(c.mapping,{token:e,lang:n,onConfirmed:function(){xn()}}):$e(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(c&&c.status==="needs_review"&&c.review){Be(!1),window.ReconReview?window.ReconReview.show(c.review,{token:e,lang:n,jobId:p.job_id,onConfirmed:async function(u){Be(!0);const v=await window._reconPollJob(u,e,{onProgress:w=>{f&&(f.textContent=window._reconProgressText(w,n))}});await l(v)}}):$e(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(c&&c.status==="failed"){Be(!1),$e(zr(c.error_code,n));return}await l(c);async function l(u){try{if(!u||u.status!=="done"||!u.result_id){Be(!1),$e(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const v=await fetch("/api/recon/bank-v2/"+encodeURIComponent(u.result_id),{headers:{Authorization:"Bearer "+e}});let w=null;try{w=await v.json()}catch{w=null}if(!v.ok||w===null||!w.ok){Be(!1),$e(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(w.gl_accounts||[]).length>1&&tl(w.gl_accounts),U.currentTask=w,U.allRows=w.detail||[],U.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(g=>g.classList.toggle("active",g.dataset.filter==="all")),Or(w&&w.summary),Be(!1),Wn(w),Tt();const b=z("brv2-summary-collapse");b&&b.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(v){Be(!1),$e(v.message||"Network error")}}}catch(o){$e(o.message||"Network error")}}function tl(e){const n=z("brv2-acct-select");if(!n)return;const a=window._currentLang||"zh",o={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[a]||"全部账户";n.innerHTML=`<option value="">${o}</option>`+e.map(s=>`<option value="${ge(s)}">${ge(s)}</option>`).join(""),n.style.display=""}function Yn(){if(U.initialized){Tt();return}U.initialized=!0,_a("brv2-stmt-zone","brv2-stmt-input","stmt"),_a("brv2-gl-zone","brv2-gl-input","gl");const e=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function n(){const d=parseFloat((z("brv2-anchor-stmt-opening")||{}).value),m=parseFloat((z("brv2-anchor-gl-opening")||{}).value),p=z("brv2-anchor-eq"),f=z("brv2-anchor-eq-val");if(!(!p||!f))if(Number.isFinite(d)&&Number.isFinite(m)){const c=d-m;f.textContent=c.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),p.style.display=""}else p.style.display="none"}e.forEach(d=>{const m=z(d);m&&(m.addEventListener("input",n),m.addEventListener("input",()=>{const p=m.closest(".brv2-anchor-cell");p&&p.classList.remove("is-prefilled"),Gr()}))}),Ur();const a=z("brv2-run-btn");a&&a.addEventListener("click",xn);const o=z("brv2-reset-btn");o&&o.addEventListener("click",()=>{U.currentTask=null,U.allRows=[],U.stmtFiles=[],U.glFiles=[],He("stmt"),He("gl"),ze(),Wt(!1);const d=z("brv2-acct-select");d&&(d.style.display="none"),e.forEach(f=>{const c=z(f);if(c){c.value="";const l=c.closest&&c.closest(".brv2-anchor-cell");l&&l.classList.remove("is-prefilled")}});const m=z("brv2-anchor-eq");m&&(m.style.display="none");const p=z("brv2-anchor-prefill-banner");p&&p.classList.remove("show")});const s=z("brv2-new-btn");s&&s.addEventListener("click",()=>{U.currentTask=null,U.allRows=[],U.stmtFiles=[],U.glFiles=[],He("stmt"),He("gl"),ze(),Wt(!1)});const i=z("brv2-filter-tabs");i&&i.addEventListener("click",d=>{d.stopPropagation();const m=d.target.closest(".brv2-filter-btn");m&&(U.currentFilter=m.dataset.filter,i.querySelectorAll(".brv2-filter-btn").forEach(p=>p.classList.toggle("active",p===m)),ho())}),el(),Xr();const r=z("brv2-hist-search");r&&r.addEventListener("input",go),Tt(),ze(),window._brv2LoadHistory=Tt,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(d=>d.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){ze(),He("stmt"),He("gl"),U.currentTask&&Wn(U.currentTask),Yt()}})}window._loadBankReconV2Panel=function(e){const n=e?document.getElementById(e):null;n&&n.id!=="recon-pane-bank"&&(n.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
            银行对账 v2 · 请前往对账中心使用</div>`),Yn()};document.addEventListener("DOMContentLoaded",()=>{z("brv2-run-btn")&&Yn()});window._bankReconV2Init=Yn;(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const p=document.getElementById("general-tz"),f=document.getElementById("general-date"),c=document.getElementById("general-number");if(!(!p||!f||!c))try{p.value=localStorage.getItem(n)||s.tz,f.value=localStorage.getItem(a)||s.date,c.value=localStorage.getItem(o)||s.number}catch{p.value=s.tz,f.value=s.date,c.value=s.number}}async function r(){const p=document.getElementById("btn-save-general"),f=document.getElementById("general-save-msg");if(!p)return;const c=p.innerHTML;p.disabled=!0,p.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",f&&(f.textContent="",f.classList.remove("error"));try{const l=(document.getElementById("general-tz")||{}).value||s.tz,u=(document.getElementById("general-date")||{}).value||s.date,v=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,l),localStorage.setItem(a,u),localStorage.setItem(o,v)}catch{}window._pearnlyGeneral={tz:l,date_format:u,number_format:v},f&&(f.textContent=t("msg-saved")||"已保存")}catch{f&&(f.textContent=t("msg-save-failed")||"保存失败",f.classList.add("error"))}finally{p.disabled=!1,p.innerHTML=c,setTimeout(function(){f&&(f.textContent="")},3e3)}}function d(){const p=document.getElementById("btn-save-general");if(!p){setTimeout(d,200);return}p._pearnlyGenBound||(p._pearnlyGenBound=!0,p.addEventListener("click",r),i())}function m(){i();const p=document.getElementById("general-lang");if(p){const f=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";p.value=f}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",d):d(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",m)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(d){const m=d.dataset.collapsible;r[m]?d.classList.add("collapsed"):d.classList.remove("collapsed")})}function i(r){const d=a();d[r]=!d[r],o(d),s()}(function(){const d=a();let m=!1;d.sales===void 0&&(d.sales=!1,m=!0),d.expense===void 0&&(d.expense=!0,m=!0),m&&o(d)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const d=n[r];if(!d)return;const m=a();m[d]&&(m[d]=!1,o(m),s())}})();const nl=`
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
    </div>`;function Ea(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=nl;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,Ea();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const i=o.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let Ce=[];window._erpEndpoints=Ce;let jt=null;async function sn(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}Ce=(await e.json()).items||[],window._erpEndpoints=Ce,yo()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return sn()};async function bo(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const d=[];d.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&d.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&d.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&d.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=d.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function yo(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&Ce.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(Ce.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=Ce.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:Ce.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),bo(),e.innerHTML=Ce.map(s=>{const i=s.config||{},r=escapeHtml(i.url||"");i._token_set;const d=s.enabled!==!1,m=[];s.is_default&&m.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&m.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),d||m.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const p=[];return s.success_count>0&&p.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&p.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=Ce.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,d=document.createElement("div");d.className="erp-limit-hint",r==="free"?d.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:d.textContent=t("ep-plus-limit-hint",{used:s,limit:i}),e.appendChild(d)}}function al(e){jt=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),d=document.getElementById("ep-auto-push"),m=document.getElementById("ep-test-result");m.style.display="none",m.textContent="";const p=document.getElementById("ep-save-error");if(p&&p.remove(),e){const c=Ce.find(l=>l.id===e);if(!c)return;o.value=c.name||"",s.value=(c.config||{}).url||"",i.value=(c.config||{})._token_set&&c.config.token||"",i.placeholder=(c.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!c.is_default,d.checked=!!c.auto_push}else o.value="",s.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=Ce.length===0,d.checked=!0;const f=d.closest(".form-switch-row");if(d.disabled=!1,f){f.classList.remove("disabled-plus"),f.title="",f.style.cursor="",f.onclick=null;const c=f.querySelector(".plus-badge");c&&c.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function wo(){document.getElementById("endpoint-modal").style.display="none",jt=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function ko(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function xo(){const e=document.getElementById("ep-name").value.trim(),n=ko(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:i}}async function ol(){const{url:e,config:n}=xo(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function sl(){const e=xo(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){Ba(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let i;if(jt?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(jt)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const d=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof d=="string"?d:JSON.stringify(d))}wo(),showToast(t("ep-save-ok")),sn()}catch(i){Ba(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function Ba(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function il(e){const n=Ce.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),sn()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=sn;window.loadErpTodayStats=bo;window.renderErpEndpointsList=yo;window.openEndpointModal=al;window.closeEndpointModal=wo;window.saveEndpoint=sl;window.deleteEndpoint=il;window.testEndpointConnection=ol;window._sanitizeUrl=ko;async function _o(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function rl(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){_o(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const i=s.dataset.receiptAction;i==="retry"?window.retryPushLog(s.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(S=>S.id===o.endpoint_id),i=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),d=new Date(o.created_at).toLocaleString(),m=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),p=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),f=o.response_body||t("erp-receipt-no-tech"),c=o.status==="success";let l=typeof f=="string"?f:JSON.stringify(f,null,2);if(c)try{const S=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},M=S.row_count||(Array.isArray(S.imported_rows)?S.imported_rows.length:0);M>0&&(l=t("log-push-rows").replace("{n}",String(M)))}catch{}const u=(o.external_doc_no||"").trim(),v=(o.external_url||"").trim(),w=(o.external_doc_hint||"").trim(),b=(o.ocr_buyer_name||"").trim()||o.client_name||"-",g=o.seller_name||"-",h=o.push_type==="id_card";let I="-";const y=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(y)&&(I=y.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const x=c?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),E=c?"✓":"✗",_=[],k=(S,M)=>{_.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(S)}</span>
                    <span class="erp-receipt-val">${M}</span>
                </div>`)};if(k(h?t("erp-log-col-booking"):t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),k(t("erp-receipt-erp-name"),escapeHtml(i)),c){let S;u?S=`<strong class="erp-receipt-docno">${escapeHtml(u)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(u)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:S=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,k(t("erp-receipt-doc-no"),S)}h||k(t("erp-receipt-client"),escapeHtml(b)),k(h?t("erp-log-col-customer"):t("erp-receipt-seller"),escapeHtml(g)),c&&k(t("erp-receipt-amount"),escapeHtml(I)),k(t("erp-receipt-time"),escapeHtml(d)),k(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let B="";c&&v?B=`<a class="erp-receipt-primary-btn" href="${escapeHtml(v)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:c&&u&&(B=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(u)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let L="";if(c&&u&&w){const S="erp-receipt-hint-"+w,M=t(S);M&&M!==S&&(L=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(M)}</span></div>`)}let C="";if(!c){const S=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),M=S?S[0]:"",$=typeof currentLang=="string"&&currentLang||window._currentLang||"th",H=o.error_friendly&&o.error_friendly[$]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),T=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),D=!!(o.history_id&&o.endpoint_id),O=[];O.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),T&&O.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),D&&O.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),C=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${M?`<div class="erp-receipt-errcode">${escapeHtml(M)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(H)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${O.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${c?"ok":"fail"}">${E}</span>
                    ${escapeHtml(x)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(m)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${_.join("")}
            </div>

            ${L}
            ${B?`<div class="erp-receipt-primary-wrap">${B}</div>`:""}
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
                    <pre>${escapeHtml(l)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=_o;window.showLogDetail=rl;const ll=`
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
    `;ke("endpoint-modal",ll);let _t={key:"all",val:""},Mt="",mn=!1,qe=new Set;window._erpSelected=qe;async function cl(){const e=document.getElementById("erp-logs-erp-select");if(!(!e||mn)){mn=!0;try{let n=window._erpEndpoints;if(!Array.isArray(n)||n.length===0){const s=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(s.ok){const i=await s.json();n=i&&(i.items||i)||[]}}Array.isArray(n)||(n=[]);const a=new Set,o=[];n.forEach(s=>{const i=(s&&s.adapter||"").toLowerCase();!i||a.has(i)||(a.add(i),o.push({val:i,label:s&&s.name||i}))}),e.innerHTML=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`+o.map(s=>`<option value="${escapeHtml(s.val)}"${s.val===Mt?" selected":""}>${escapeHtml(s.label)}</option>`).join("")}catch{mn=!1}}}async function ct(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats(),cl();try{const a=new URLSearchParams({limit:"30"});_t.key==="status"&&a.set("status",_t.val),_t.key==="trigger"&&a.set("trigger",_t.val),Mt&&a.set("adapter",Mt);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(u){return u.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){ct(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const r=i.filter(function(u){var v=u.status==="failed"&&u.next_retry_at&&new Date(u.next_retry_at).getTime()>Date.now()-6e4;return!v}).map(function(u){return u.id}),d=Mt==="mrerp_dms",m=d?t("erp-log-col-booking"):t("erp-log-col-invoice"),p=d?t("erp-log-col-customer"):t("erp-log-col-seller"),f=d?t("erp-log-col-idcard"):t("erp-log-col-client"),c='<div class="erp-log-row erp-log-row-header" data-log-header>'+(r.length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(m)}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(f)}</span><span class="log-seller">${escapeHtml(p)}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=c+i.map(u=>{const v=new Date(u.created_at),w=`${String(v.getMonth()+1).padStart(2,"0")}-${String(v.getDate()).padStart(2,"0")} ${String(v.getHours()).padStart(2,"0")}:${String(v.getMinutes()).padStart(2,"0")}`,b=u.status==="failed"&&u.next_retry_at&&new Date(u.next_retry_at).getTime()>Date.now()-6e4;let g,h,I;u.status==="pending"?(g="retrying",h="⟳",I=t("erp-status-pending")):u.status==="success"?(g="ok",h="✓",I=t("erp-status-success")):u.status==="skipped_dup"?(g="skipped",h="⏭",I=t("erp-status-skipped")):b?(g="retrying",h="↻",I=t("erp-status-retrying")):(g="fail",h="✗",I=t("erp-status-failed"));let y;u.trigger==="auto"?y=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:u.trigger==="retry"?y=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:y=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;const x=u.push_type==="id_card",E=x?`<span class="log-tag log-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span>`:"",_=u.error_friendly&&(u.error_friendly[currentLang]||u.error_friendly.en)||"";let k="";const B=u.retry_count||0,L=u.max_retries||3;if(b){const N=new Date(u.next_retry_at).getTime()-Date.now(),se=Math.max(0,Math.round(N/6e4)),ie=se<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:se});k=`${t("erp-retry-attempt",{n:B,max:L})} · ${ie}`}else u.status==="failed"&&B>=L&&!u.next_retry_at&&(k=t("erp-retry-exhausted",{n:B}));const C=u.status==="failed"&&!b?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(u.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",S=!b,M=qe.has(u.id)?"checked":"",$=S?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(u.id)}" ${M}>`:'<span class="erp-log-cb-spacer"></span>',q=(u.ocr_buyer_name||"").trim()||(u.client_name||"").trim(),H=x?`<span class="log-client" title="${escapeHtml(t("erp-log-col-idcard"))}">${u.id_card_tail?"••••"+escapeHtml(u.id_card_tail):"—"}</span>`:q?`<span class="log-client" title="${escapeHtml(q)}">${escapeHtml(q.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,T=x?'<span class="log-workspace log-workspace-unresolved">—</span>':u.workspace_name?`<span class="log-workspace">${escapeHtml((u.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,D=u.endpoint_name?`<span class="log-erp">${escapeHtml((u.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,O=(u.external_doc_no||"").trim(),P=(u.external_url||"").trim();let j;return P?j=`<span class="log-doc"><a href="${escapeHtml(P)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(O||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:O?j=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(O)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(O.substring(0,18))}</span>`:u.status==="success"?j=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:j='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${g}" data-log-detail="${escapeHtml(u.id)}">
                    ${$}
                    <span class="log-time">${w}</span>
                    <span class="log-status" title="${escapeHtml(I+(k?" · "+k:"")+(_?" · "+_:""))}">${h}</span>
                    ${y}${E}
                    <span class="log-invoice"${x?` title="${escapeHtml(t("erp-log-col-booking"))}"`:""}>${escapeHtml(u.invoice_no||"-")}</span>
                    ${T}
                    ${H}
                    <span class="log-seller"${x?` title="${escapeHtml(t("erp-log-col-customer"))}"`:""}>${escapeHtml((u.seller_name||"").substring(0,20))}</span>
                    ${D}
                    ${j}
                    <span class="log-http">HTTP ${u.http_status||"-"}</span>
                    <span class="log-elapsed">${u.elapsed_ms}ms</span>
                    <span class="log-actions">${C}</span>
                </div>
            `}).join("");const l=new Set(i.map(u=>u.id));for(const u of Array.from(qe))l.has(u)||qe.delete(u);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function Eo(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),ct(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),Eo(s.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const f=i.dataset.logCb;i.checked?qe.add(f):qe.delete(f),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const f=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(l){l.checked=f;const u=l.dataset.logCb;f?qe.add(u):qe.delete(u)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),qe.clear(),document.querySelectorAll(".erp-log-cb").forEach(f=>{f.checked=!1}),window._refreshErpBatchBar();return}const d=n.target.closest("[data-log-detail]");if(d){if(n.target.closest("[data-log-cb]"))return;const f=n.target.closest("[data-copy-doc]");if(f){n.stopPropagation(),window.copyErpDocNo(f.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(d.dataset.logDetail);return}const m=n.target.closest(".chip-filter");if(m){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(f=>f.classList.remove("active")),m.classList.add("active"),_t={key:m.dataset.filterKey,val:m.dataset.filterVal},ct();return}if(n.target.closest("#btn-refresh-logs")){const f=n.target.closest("#btn-refresh-logs");f.classList.add("spinning"),setTimeout(()=>f.classList.remove("spinning"),600),ct();return}const p=n.target.closest(".auto-nav-item");if(p&&p.dataset.autoTab){switchAutomationTab(p.dataset.autoTab);return}}),document.addEventListener("change",n=>{n.target&&n.target.id==="erp-logs-erp-select"&&(Mt=n.target.value||"",ct())})})();window.loadErpLogs=ct;window.retryPushLog=Eo;function Bo(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function Io(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),i=o.failed&&o.failed>0?"warn":"success";showToast(s,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function Lo(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),Io()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),Lo()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),Bo()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=Bo;window._runErpBatchRetry=Io;window._runErpBatchDelete=Lo;(function(){let e=null,n=!1;function a(){if(e)return e;const d=document.createElement("div");d.id="line-email-modal",d.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",d.innerHTML=`
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
        `,document.body.appendChild(d),e=d;const m=d.querySelector("#line-email-input"),p=d.querySelector("#line-email-submit-btn"),f=d.querySelector("#line-email-err");async function c(){f.textContent="";const l=(m.value||"").trim().toLowerCase();if(!l||l.indexOf("@")<0||l.split("@")[1].indexOf(".")<0){f.textContent=t("line-email-err-invalid");return}p.disabled=!0,p.style.opacity="0.6";try{const u=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:l})});if(!u.ok)throw new Error("http_"+u.status);const v=await u.json();v.token&&localStorage.setItem("mrpilot_token",v.token),typeof showToast=="function"&&showToast(v.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{f.textContent=t("line-email-err-failed"),p.disabled=!1,p.style.opacity="1"}}return p.addEventListener("click",c),m.addEventListener("keydown",function(l){l.key==="Enter"&&c()}),d}function o(){if(!e)return;const d=e.querySelector("#line-email-title-h"),m=e.querySelector("#line-email-sub-p"),p=e.querySelector("#line-email-input"),f=e.querySelector("#line-email-submit-btn");d&&(d.textContent=t("line-email-title")),m&&(m.textContent=t("line-email-sub")),p&&(p.placeholder=t("line-email-placeholder")),f&&(f.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const d=e.querySelector("#line-email-input");d&&setTimeout(function(){d.focus()},100)}async function i(){const d=localStorage.getItem("mrpilot_token");if(d)try{const m=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+d}});if(!m.ok)return;const p=await m.json();p&&p.needs_email&&s()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(f){let c=0;return f.length>=8&&c++,f.length>=12&&c++,/[a-zA-Z]/.test(f)&&/\d/.test(f)&&c++,/[^a-zA-Z0-9]/.test(f)&&c++,Math.min(3,c)}function n(f,c){const l=document.getElementById("cpw-msg");l&&(l.textContent=f,l.className="cpw-msg "+(c||""))}function a(f){return typeof t=="function"?t(f):f}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(c=>{const l=document.getElementById(c);l&&(l.value="",l.setAttribute("readonly","readonly"))});const f=document.getElementById("cpw-strength-bar");f&&(f.style.width="0%",f.className="cpw-strength-bar"),n("","")}async function i(){const f=document.getElementById("btn-change-pw"),c=document.getElementById("cpw-old"),l=document.getElementById("cpw-new"),u=document.getElementById("cpw-confirm"),v=document.getElementById("cpw-strength-bar");if(!f||!c||!l||!u)return;const w=c.value,b=l.value,g=u.value;if(!w||!b||!g){n(a("settings-change-pw-empty"),"error");return}if(b.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(b)&&/\d/.test(b))){n(a("settings-change-pw-too-weak"),"error");return}if(b!==g){n(a("settings-change-pw-mismatch"),"error");return}f.disabled=!0;const h=f.textContent;f.textContent=a("settings-change-pw-submitting"),n("","");try{const I=localStorage.getItem("mrpilot_token"),y=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+I},body:JSON.stringify({old_password:w,new_password:b})}),x=await y.json().catch(()=>({}));if(y.ok&&x.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),c.value="",l.value="",u.value="",v&&(v.style.width="0%",v.className="cpw-strength-bar");else{const E=x.detail||"";let _=a("settings-change-pw-success");E==="wrong_old_password"?_=a("settings-change-pw-wrong-old"):E==="password_too_short"?_=a("settings-change-pw-too-short"):E==="password_too_weak"?_=a("settings-change-pw-too-weak"):_=E||"Error",n(_,"error")}}catch(I){console.error("change_password",I),n("Network error","error")}finally{f.disabled=!1,f.textContent=h}}function r(){o||(o=!0,document.addEventListener("click",f=>{if(!f.target||!f.target.closest)return;const c=f.target.closest(".cpw-eye");if(c){const l=document.getElementById(c.dataset.target);l&&(l.type=l.type==="password"?"text":"password");return}if(f.target.closest("#cpw-forgot-link")){f.preventDefault(),d();return}if(f.target.closest("#btn-change-pw")){i();return}f.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",f=>{if(f.target&&f.target.id==="cpw-new"){const c=document.getElementById("cpw-strength-bar");if(!c)return;const l=e(f.target.value),u=["0%","33%","66%","100%"],v=["","weak","medium","strong"];c.style.width=u[l],c.className="cpw-strength-bar "+v[l]}}),document.addEventListener("focusin",f=>{f.target&&["cpw-old","cpw-new","cpw-confirm"].includes(f.target.id)&&f.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function d(){const f=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),c=f&&f.username?f.username:"",l=m(c);let u=document.getElementById("cpw-forgot-overlay");u&&u.remove(),u=document.createElement("div"),u.id="cpw-forgot-overlay",u.className="cpw-forgot-overlay",u.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${p(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${p(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${p(l)}</div>
                    <p class="cpw-forgot-tip">${p(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${p(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${p(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(u);const v=()=>u.remove();u.querySelector("#cpw-forgot-close").addEventListener("click",v),u.querySelector("#cpw-forgot-cancel").addEventListener("click",v),u.addEventListener("click",w=>{w.target===u&&v()}),u.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const w=u.querySelector("#cpw-forgot-send"),b=u.querySelector("#cpw-forgot-msg");w.disabled=!0;const g=w.textContent;w.textContent=a("cpw-forgot-sending");try{const h=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:c})}),I=await h.json().catch(()=>({}));h.ok?(b.textContent=a("cpw-forgot-success"),b.className="cpw-forgot-msg success",w.style.display="none",u.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(b.textContent=I.detail||a("cpw-forgot-fail"),b.className="cpw-forgot-msg error",w.disabled=!1,w.textContent=g)}catch{b.textContent=a("cpw-forgot-fail"),b.className="cpw-forgot-msg error",w.disabled=!1,w.textContent=g}})}function m(f){if(!f||!f.includes("@"))return f||"";const[c,l]=f.split("@");return c.length<=2?c+"****@"+l:c.slice(0,2)+"****@"+l}function p(f){return f==null?"":String(f).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),d=r&&r.detail;let m="";if(typeof d=="string"?m=d:d&&typeof d=="object"&&(m=d.code||""),console.warn("[heartbeat] session revoked",m),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),m==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const p=m==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(p),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function rn(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),i=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const d=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",m=r.is_active===!1?"team-status-off":"team-status-on",p=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",f=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${m}"></span>
                            <span>${escapeHtml(p)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(d)}</span>
                            ${f}
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function dl(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),d=document.getElementById("add-emp-submit"),m=(o.value||"").trim(),p=(s.value||"").trim(),f=i.value||"";if(r.textContent="",r.classList.remove("error"),!m||m.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(m)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(p&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(f.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(f)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(f)&&/\d/.test(f))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}d.disabled=!0,d.textContent=t("msg-saving")||"保存中...";try{const c={username:m,password:f};p&&(c.email=p);const l=await apiPost("/api/team/employees",c),u=l?await l.json().catch(()=>({})):{};if(l&&l.ok&&u&&u.ok){showToast(t("team-added")||"员工已添加","success"),n(),rn();return}const v=u&&u.detail||"unknown",w={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=w[v]||(t("team-create-failed")||"创建失败")+" ("+v+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{d.disabled=!1,d.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function pl(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){rn();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function ul(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),rn();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function fl(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const d=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",m=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(d.replace("{ch}",m),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),dl();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),pl(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),ul(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),fl(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=rn;function ml(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=ml;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
