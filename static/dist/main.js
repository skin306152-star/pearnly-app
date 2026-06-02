(function(){const n=[];function a(s){try{n.push(Object.assign({ts:Date.now()},s)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(s)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(s){s.target&&s.target!==window&&(s.target.src||s.target.href)||a({type:"js_error",summary:String(s.message||"JS Error").slice(0,200),detail:{file:s.filename||"",line:s.lineno||0,col:s.colno||0,stack:s.error&&s.error.stack?String(s.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(s){const i=s.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const o=window.fetch;typeof o=="function"&&(window.fetch=function(){const s=arguments,i=Date.now(),r=typeof s[0]=="string"?s[0]:s[0]&&s[0].url||"?",d=s[1]&&s[1].method||"GET",l=String(r).split("?")[0];return o.apply(this,s).then(function(p){const f=Date.now()-i;if(p.ok)f>2500&&a({type:"api_slow",summary:d+" "+l+" → 慢 "+f+"ms",detail:{url:r,method:d,status:p.status,elapsed_ms:f}});else{let c="";try{p.clone().text().then(function(m){c=String(m||"").slice(0,500),a({type:"api_error",summary:d+" "+l+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:f,body_preview:c}})}).catch(function(){a({type:"api_error",summary:d+" "+l+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:f,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:d+" "+l+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:f}})}}return p}).catch(function(p){const f=Date.now()-i;throw a({type:"api_fail",summary:d+" "+l+" → 网络失败 ("+f+"ms)",detail:{url:r,method:d,elapsed_ms:f,error:String(p&&p.message||p)}}),p})}),["error","warn"].forEach(function(s){const i=console[s];typeof i=="function"&&(console[s]=function(){try{const r=[];for(let d=0;d<arguments.length;d++){const l=arguments[d];if(typeof l=="string")r.push(l);else if(l&&l instanceof Error)r.push(l.message);else try{r.push(JSON.stringify(l).slice(0,300))}catch{r.push(String(l))}}a({type:"console_"+s,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(o=>o.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function Ua(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function Ga(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function Ka(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function Rt(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const o in n)a=a.replace("{"+o+"}",n[o]);return a}function Ja(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function Ya(e,n){n=n||14;const o={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${o}</svg>`}function Ft(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},o={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},s=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[s]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[s]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+o[s]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function zt(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function Wa(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...zt()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),o=a&&a.detail;let s="";if(typeof o=="string"?s=o:o&&typeof o=="object"&&(s=o.code||""),n.status===401||typeof s=="string"&&s.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,o),localStorage.removeItem("mrpilot_token"),s==="auth.session_revoked")Ft();else{const d=s==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Rt(d),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=o,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function Xa(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...zt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.clone().json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Ft();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Rt(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function Za(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...zt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Ft();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Rt(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const o=await a.json().catch(()=>({}));return{ok:a.ok&&o.ok!==!1,...o}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=Wa;window.apiPost=Xa;window.t=Rt;window.escapeHtml=Ja;window.svgIcon=Ya;window._showSessionRevokedModal=Ft;window._wsHeader=zt;window.apiPut=Za;window.getMaxFiles=Ua;window.getMaxPagesPerFile=Ga;window.getMaxMbPerFile=Ka;function we(e,n){const a=document.getElementById(e);if(!(!a||a.dataset.wbInjected==="1")){a.innerHTML=n,a.dataset.wbInjected="1";try{const o=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",s=window.I18N;if(!s||!s[o])return;a.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");s[o][r]&&(i.textContent=s[o][r])}),a.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");s[o][r]&&(i.placeholder=s[o][r])})}catch{}}}const Qa=`
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
    `;we("page-ocr",Qa);const eo=`
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
`,to=`
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
`;we("topbar",eo);we("sidebar",to);function on(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const o=document.getElementById("general-lang");o&&(o.value=e);const s=document.getElementById("col-conf-th");s&&s.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&sn(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function no(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",s=>{s.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(s)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});no("lang-dropdown",e=>on(e.dataset.lang));const Kn=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","receivables","reconcile","cloud","test-center"];function Jn(e){Kn.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(o=>o.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(o=>{o.classList.toggle("active",o.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function Yn(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){return!i||typeof i!="string"||(i=i.trim(),!i)?null:i.includes("@")&&i.indexOf("@")>0&&i.indexOf(".")>i.indexOf("@")?i.split("@")[0]:i}const o=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let s=null;for(const i of o){const r=a(i);if(r){s=r;break}}s||(s=t("brand-workspace-fallback")||"我的工作台"),e.textContent=s,e.title=s,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",s,"· _userInfo fields:",Object.keys(n))}function sn(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function Wn(){try{const[e,n,a,o]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(s=>s.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,o&&(window._planState=o),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const s=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(s&&!i){window.location.replace("/home");return}if(!s&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=s}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,o&&(window._planState=o),Yn(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(s){console.error("[nav-ia phase1] render avatar menu",s)}sn(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const s=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(s&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(s&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(s){console.error("force-pw init",s)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(s){console.error("onboarding init",s)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(s){console.error("settings forms init",s)}}catch(e){console.error(e)}}function ao(){let e=document.getElementById("offline-banner");e||(e=document.createElement("div"),e.id="offline-banner",e.className="offline-banner",e.style.display="none",document.body.insertBefore(e,document.body.firstChild));function n(){navigator.onLine===!1?(e.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",e.classList.remove("is-online"),e.classList.add("is-offline"),e.style.display="flex"):e.classList.contains("is-offline")?(e.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",e.classList.remove("is-offline"),e.classList.add("is-online"),setTimeout(()=>{e.style.display="none",e.classList.remove("is-online")},2e3)):e.style.display="none"}window.addEventListener("online",n),window.addEventListener("offline",n),n()}window.applyLang=on;window.routeTo=Jn;window.loadAll=Wn;window.renderBrandWorkspace=Yn;window.updateUploadHint=sn;window.installNetworkBanner=ao;try{on(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");Jn(Kn.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);Wn();const Xn="mrpilot_sidebar_collapsed";localStorage.getItem(Xn)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(Xn,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const o=document.querySelectorAll("#page-integrations .int-top-tab"),s=document.querySelectorAll("#page-integrations .int-top-panel");if(o.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),s.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),o&&o.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const o=a.target.closest("#page-integrations .int-top-tab");if(o){const i=o.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const o=document.querySelector(".auto-content");o&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(s){s.style.display="",o.appendChild(s)})}window.openIntegrationDrawer=function(a,o){const s=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),d=document.getElementById("int-drawer-body");if(!s||!d)return;e(),s.dataset.currentTab=a||"",r&&(r.textContent=o||""),d.innerHTML="";var l={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},p=l[a]||a;const f=document.querySelector('.auto-panel[data-auto-panel="'+p+'"]');f?(f.style.display="block",d.appendChild(f)):d.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',s.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var c={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(c[a])try{c[a]()}catch(u){console.warn("[int-drawer] loader error",u)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(u){console.warn("[int-drawer] ERP load error",u)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),o&&(o.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),o=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),o&&o.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(s){s.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(s=>{s.addEventListener("click",()=>switchSettingsTab(s.dataset.tab))});let o=null;try{o=localStorage.getItem("mrpilot_settings_tab")}catch{}if(o){const s=document.querySelector(`.settings-tab[data-tab="${o}"]`);if(s&&s.style.display!=="none"){switchSettingsTab(o);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),o=document.getElementById("btn-save-company");if(!a&&!o){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),o&&o.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let St=null;function oo(){Xt(),St=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&Xt()}catch{}},1e4)}function Xt(){St&&(clearInterval(St),St=null)}window.startEnginePolling=oo;window.stopEnginePolling=Xt;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target.closest("[data-rd-action]");if(n){const s=n.dataset.rdAction,i=n.dataset.rdSide;s==="verify"?callRdVerify(i):s==="sync"&&callRdSync(i);return}if(e.target.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=e.target.closest("[data-archive-copy]");if(o){const s=o.dataset.archiveCopy;navigator.clipboard?.writeText(s).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const Sn=document.getElementById("btn-custom-template");Sn&&Sn.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});const so=`
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
    `,io=`
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
`;we("pearnly-confirm-modal",so);we("confirm-modal",io);window.pearnlyConfirm=function(e,n){return new Promise(function(a){const o=document.getElementById("pearnly-confirm-modal"),s=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),d=document.getElementById("pearnly-confirm-cancel"),l=document.getElementById("pearnly-confirm-close");if(!o||!i||!r||!d){a(window.confirm(e));return}s&&(s.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",o.style.display="flex";function p(h){o.style.display="none",r.removeEventListener("click",f),d.removeEventListener("click",c),l&&l.removeEventListener("click",c),o.removeEventListener("click",u),document.removeEventListener("keydown",m),a(h)}function f(){p(!0)}function c(){p(!1)}function u(h){h.target===o&&p(!1)}function m(h){h.key==="Escape"?p(!1):h.key==="Enter"&&p(!0)}r.addEventListener("click",f),d.addEventListener("click",c),l&&l.addEventListener("click",c),o.addEventListener("click",u),document.addEventListener("keydown",m),setTimeout(function(){try{d.focus()}catch{}},50)})};const ro=`
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

`,lo=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=ro+lo,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const co=`
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

`,po=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=co+po,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function uo(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function fo(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function mo(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function vo(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function ho(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let d=null;const l=()=>{d&&(clearTimeout(d),d=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(d=setTimeout(l,r)),l}window.showAlert=uo;window.hideAlerts=fo;window._humanizeBackendError=mo;window.humanizeError=vo;window.showToast=ho;function go(e,n){return n=n||{},new Promise(a=>{const o=document.getElementById("confirm-modal"),s=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),d=document.getElementById("confirm-modal-close"),l=document.getElementById("confirm-modal-title");if(!o||!s||!i||!r){a(!1);return}l.textContent=n.title||t("confirm-default-title");const p=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const m=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),h=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");s.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${m}</div>
                <input type="text" id="${p}" placeholder="${h}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else s.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",o.style.display="flex";const f=m=>{o.style.display="none",i.onclick=null,r.onclick=null,d.onclick=null,o.onclick=null,document.removeEventListener("keydown",u),n.promptInput&&(s.innerHTML=""),r.style.display="",a(m)},c=()=>{const m=p?document.getElementById(p):null;return m?m.value:""},u=m=>{m.key==="Escape"?f(n.promptInput?null:!1):m.key==="Enter"&&f(n.promptInput?c():!0)};i.onclick=()=>f(n.promptInput?c():!0),r.onclick=()=>f(n.promptInput?null:!1),d.onclick=()=>f(n.promptInput?null:!1),o.onclick=m=>{m.target===o&&f(n.promptInput?null:!1)},document.addEventListener("keydown",u),setTimeout(()=>{if(n.promptInput){const m=document.getElementById(p);m&&m.focus()}else i.focus()},50)})}window.showConfirm=go;function bo(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof Zt=="function"&&Zt()}catch(n){console.warn("settings tab side effect failed:",n)}}}function yo(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function wo(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function ko(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function Zt(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}xo(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function xo(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
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
    `}window.switchSettingsTab=bo;window.fillSettingsForms=yo;window.saveProfile=wo;window.saveCompany=ko;window.renderSettings=Zt;function Nt(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function rn(e){return e=e||_userInfo,!!e&&(e.role==="owner"||Nt(e))}function Zn(e){return e=e||_userInfo,!!e&&e.role==="member"&&!Nt(e)}function _o(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!Nt(e)}function Qn(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function ea(e){return Zn(e)}function Eo(e){return rn(e)}function Bo(e){return rn(e)&&Qn(e)}window.isMoneyHidden=ea;window.isSuperAdmin=Nt;window.isOwner=rn;window.isEmployee=Zn;window.isTrial=_o;window.isLifetime=Qn;window.shouldHideMoney=ea;window.canManageTeam=Eo;window.canManageApiKey=Bo;function Io(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,d;if(o===0)r="danger",d=t("quota-banner-exhausted");else if(s>=90)r="danger",d=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",d=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(d)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const l=e.querySelector(".quota-banner-close");l&&l.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function Lo(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const d=document.querySelector('.settings-tab[data-tab="team"]');d&&(d.style.display=a?"":"none");const l=document.querySelector('.settings-panel[data-settings-panel="team"]');l&&(l.dataset.permHidden=a?"0":"1");const p=document.querySelector('.settings-tab[data-tab="api"]');p&&(p.style.display=o||isSuperAdmin(e)?"":"none");const f=document.querySelector('.settings-tab[data-tab="plan"]');f&&(f.style.display=n?"none":"");const c=document.querySelector('.settings-tab[data-tab="company"]');c&&(c.style.display=n?"none":"");const u=document.getElementById("info-bar");u&&(u.style.display=n?"none":"");const m=document.getElementById("trial-banner");m&&n&&(m.style.display="none");const h=document.getElementById("plan-banner");h&&n&&(h.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(_=>{_.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const _=document.querySelector(".settings-tab.active");_&&_.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(_){console.warn("[v118.12.3] failed to fix active tab:",_)}if(window.PEARNLY_ADMIN_MODE){const _=document.getElementById("admin-mode-banner");_&&(_.style.display="flex"),document.querySelectorAll(".nav-item").forEach(v=>{v.classList.contains("nav-admin-only")||(v.style.display="none")}),document.querySelectorAll(".nav-group").forEach(v=>{v.classList.contains("nav-group-admin-only")||(v.style.display="none")});const w=document.getElementById("client-switcher");w&&(w.style.display="none"),document.body.classList.add("admin-mode");const b=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(v=>{const E=v.dataset.tab;E&&!b.includes(E)&&(v.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(v=>{const E=v.dataset.pane;E&&!b.includes(E)&&(v.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(v=>{const E=v.querySelectorAll(".settings-tab");Array.from(E).some(C=>C.style.display!=="none")||(v.style.display="none")})}}function Co(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
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
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=Io;window.applySidebarVisibility=Lo;window.renderInfoBar=Co;async function ta(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function na(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Mt(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function Ve(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function So(e){const a=Mt(e==="seller"?"seller_tax":"buyer_tax");Ve(e,t("rd-verifying"),"loading");const o=await ta("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){Ve(e,t(na(o.error)),"error");return}o.data&&o.data.valid?Ve(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):Ve(e,t("rd-status-invalid"),"invalid")}async function To(e){const a=Mt(e==="seller"?"seller_tax":"buyer_tax");Ve(e,t("rd-syncing"),"loading");const o=await ta("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){Ve(e,t(na(o.error)),"error");return}Ve(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),Mo(e,o.data)}}function Mo(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=Mt(a),i=Mt(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==i&&r.push({field:o,label:t("rd-field-address"),current:i,official:n.address});const d=[];n.branch_label&&d.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&d.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let l=document.getElementById("rd-sync-modal");if(l||(l=document.createElement("div"),l.id="rd-sync-modal",l.className="rd-modal-mask",document.body.appendChild(l)),r.length===0)l.innerHTML=`
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
        `;else{const c=r.map((u,m)=>`
            <label class="rd-diff-row">
                <input type="checkbox" data-rd-apply data-field="${u.field}" data-value="${escapeHtml(u.official)}" checked>
                <div class="rd-diff-label">${escapeHtml(u.label)}</div>
                <div class="rd-diff-col rd-diff-current">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-current"))}</div>
                    <div class="rd-diff-val">${escapeHtml(u.current||"—")}</div>
                </div>
                <div class="rd-diff-arrow">→</div>
                <div class="rd-diff-col rd-diff-official">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-official"))}</div>
                    <div class="rd-diff-val">${escapeHtml(u.official)}</div>
                </div>
            </label>
        `).join("");l.innerHTML=`
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
        `}l.classList.add("show");const p=()=>l.classList.remove("show");l.querySelector(".rd-modal-close").addEventListener("click",p),l.querySelectorAll("[data-rd-modal-close]").forEach(c=>c.addEventListener("click",p)),l.addEventListener("click",c=>{c.target===l&&p()});const f=l.querySelector("[data-rd-modal-apply]");f&&f.addEventListener("click",()=>{const c=_results[_drawerIdx];if(!c){p();return}l.querySelectorAll("[data-rd-apply]:checked").forEach(u=>{const m=u.dataset.field,h=u.dataset.value;c.edits[m]=h,c.merged_fields[m]=h;const _=document.querySelector(`[data-field="${m}"]`);_&&(_.value=h);const w=document.querySelector(`[data-field-wrap="${m}"]`);w&&w.classList.add("edited")}),updateDrawerEditCount(),renderResults(),p()})}window.callRdVerify=So;window.callRdSync=To;function $o(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(s=>!s.is_duplicate&&!s.is_copy),o=a.length>0?a:e;for(const s of o){const i=s.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function Ho(e){const n=e.target.dataset.field,a=e.target.value,o=_results[_drawerIdx],s=o.merged_fields[n];a===(s??"")?delete o.edits[n]:(o.edits[n]=a,o.merged_fields[n]=a);const i=document.querySelector(`[data-field-wrap="${n}"]`);i&&i.classList.toggle("edited",o.edits[n]!==void 0),aa(),renderResults()}function aa(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=$o;window.onFieldEdit=Ho;window.updateDrawerEditCount=aa;function Ao(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,o=document.getElementById("force-pw-new").value,s=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!o){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(o!==s){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(o.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(o)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(o)&&/\d/.test(o))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(o===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:o})}),d=await r.json().catch(()=>({}));if(!r.ok){const l=d&&d.detail||"unknown",p={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=p[l]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=Ao;(function(){let e=null,n=null,a=null,o=null;function s(v){return document.getElementById(v)}async function i(){h(),w(),await r()}async function r(){try{const v=localStorage.getItem("mrpilot_token"),E=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+v}});if(!E.ok){_(t("linebot-err-status"));return}const B=await E.json();B.bound?d(B):await l()}catch{_(t("linebot-err-status"))}}function d(v){m(),s("linebot-unbound").style.display="none",s("linebot-bound").style.display="block";const E=s("linebot-status-summary");E&&(E.textContent=t("linebot-status-bound"),E.style.background="#D1FAE5",E.style.color="#065F46");const B=s("linebot-bound-name");B&&(B.textContent=v.line_display_name||"(LINE User)");const C=s("linebot-avatar");C&&(v.line_picture_url?(C.src=v.line_picture_url,C.style.display=""):C.style.display="none");const L=s("linebot-bound-since");L&&v.bound_at&&(L.textContent=new Date(v.bound_at).toLocaleString())}async function l(){s("linebot-bound").style.display="none",s("linebot-unbound").style.display="block";const v=s("linebot-status-summary");v&&(v.textContent=t("linebot-status-unbound"),v.style.background="#FEE2E2",v.style.color="#B91C1C"),await p(),u()}async function p(){try{const v=localStorage.getItem("mrpilot_token"),E=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+v}});if(!E.ok){_(t("linebot-err-code"));return}const B=await E.json();a=B.code,o=new Date(B.expires_at).getTime(),f(B)}catch{_(t("linebot-err-code"))}}function f(v){const E=s("linebot-code");E&&(E.textContent=v.code);const B=s("linebot-bot-id");B&&(B.textContent=v.bot_basic_id||t("linebot-bot-id-missing"));const C=s("linebot-qr");if(C)if(v.bot_friend_url){const L="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(v.bot_friend_url);C.classList.remove("empty"),C.innerHTML='<img src="'+L+'" alt="LINE Bot QR">'}else C.classList.add("empty"),C.innerHTML="";c()}function c(){e&&clearInterval(e);const v=s("linebot-code-expires");function E(){if(!o)return;const B=o-Date.now();if(B<=0){v&&(v.textContent=t("linebot-code-expired"),v.classList.add("expiring"));const g=s("linebot-code");g&&(g.style.opacity="0.4"),clearInterval(e),e=null;return}const C=Math.floor(B/1e3),L=Math.floor(C/60),y=C%60;v&&(v.textContent=t("linebot-code-expires-in").replace("{m}",L).replace("{s}",String(y).padStart(2,"0")),B<6e4?v.classList.add("expiring"):v.classList.remove("expiring"))}E(),e=setInterval(E,1e3)}function u(){m(),n=setInterval(async()=>{try{const v=localStorage.getItem("mrpilot_token"),E=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+v}});if(!E.ok)return;const B=await E.json();B.bound&&d(B)}catch{}},4e3)}function m(){n&&(clearInterval(n),n=null)}function h(){e&&(clearInterval(e),e=null),m()}function _(v){const E=s("linebot-error");E&&(E.textContent=v,E.style.display="block")}function w(){const v=s("linebot-error");v&&(v.style.display="none")}async function b(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const E=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+E}})).ok){_(t("linebot-err-unbind"));return}await i()}catch{_(t("linebot-err-unbind"))}}document.addEventListener("click",v=>{if(v.target.closest("#linebot-code-refresh")){v.preventDefault(),w(),p();return}if(v.target.closest("#linebot-unbind")){v.preventDefault(),b();return}}),window._loadLineBotPanel=i})();function Ot(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const d=parseFloat(r.merged_fields.total_amount);isNaN(d)||(n+=d)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,d)=>({...r,_idx:d}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(d=>(d.filename||"").toLowerCase().includes(r)||(d.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,d)=>{let l,p;return _sortKey==="filename"?(l=r.filename,p=d.filename):_sortKey==="invoice_no"?(l=r.merged_fields.invoice_number,p=d.merged_fields.invoice_number):_sortKey==="invoice_date"?(l=r.merged_fields.date,p=d.merged_fields.date):_sortKey==="total"?(l=parseFloat(r.merged_fields.total_amount)||0,p=parseFloat(d.merged_fields.total_amount)||0):_sortKey==="confidence"?(l=r.confidence,p=d.confidence):(l="",p=""),l<p?_sortDir==="asc"?-1:1:l>p?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=s.map((r,d)=>{const l=r.merged_fields,p=`<span class="empty-cell">${t("empty-val")}</span>`,f="conf-tip-"+(r.confidence||"low"),c="conf-"+(r.confidence||"low"),u=t(f),m=t(c);return`
            <tr data-idx="${r._idx}">
                <td class="num">${d+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${l.invoice_number?escapeHtml(l.invoice_number):p}</td>
                <td class="date">${l.date?escapeHtml(l.date):p}</td>
                <td class="amount">${l.total_amount?Number(l.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):p}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(u)}">${m}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const d=parseInt(r.dataset.idx,10);sa(d)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),Ot()})});let Tn=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(Tn),Tn=setTimeout(()=>{_searchKeyword=n.trim(),Ot(),oa()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",Ot(),oa(),e.focus()});function oa(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function sa(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,i=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,d=document.getElementById("drawer-body"),l=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,p=i?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(d.innerHTML=`
        ${l}

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
                ${_e("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,jo(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${_e("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${_e("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,p,Mn("seller"))}
            ${_e("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${_e("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${_e("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,p,Mn("buyer"))}
            ${_e("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?Po(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
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
    `,s?d.querySelectorAll("[data-field]").forEach(f=>{f.addEventListener("input",onFieldEdit)}):d.querySelectorAll("[data-field]").forEach(f=>{f.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const f=n._historyId||n.history_id||null;window.bindDrawerClient(f,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const f=document.getElementById("drawer-cat-input");f&&!f.value&&!f.readOnly&&f.focus()},80)}function jo(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function _e(e,n,a,o,s,i,r){const d=_results[_drawerIdx],l=d&&d.edits[e]!==void 0?d.edits[e]:a,p=d&&d.edits[e]!==void 0&&d.edits[e]!==a,f=escapeHtml(l??""),c=s?"":"readonly",u=o==="textarea"?`<textarea data-field="${e}" rows="2">${f}</textarea>`:`<input type="text" data-field="${e}" value="${f}">`;return`
        <div class="drawer-field ${p?"edited":""} ${c}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${u}
        </div>
    `}function Mn(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function Po(e){return`
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
    `}function Do(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=Ot;window.openDrawer=sa;window.closeDrawer=Do;function qo(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(d){return d&&d.enabled!==!1&&(d.adapter||"").toLowerCase()!=="mrerp_dms"});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let i;if(o.length===1){const d=o[0].name||o[0].adapter||"ERP";i=t("btn-push-to-name",{name:d}),s.title=i}else i=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,s.addEventListener("click",function(d){d.preventDefault(),d.stopPropagation(),o.length===1?ia(n,o[0].id):Ro(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function Ro(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(l=>l.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const i=a.map(function(l){const p=escapeHtml(l.name||l.adapter||"ERP"),f=escapeHtml((l.adapter||"").toLowerCase()),u=l.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(l.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+f+"</span>"+p+u+"</span></button>"}).join("");s.innerHTML=i,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",d,!0)},d=l=>{!s.contains(l.target)&&l.target!==e&&!e.contains(l.target)&&r()};setTimeout(()=>document.addEventListener("click",d,!0),0),s.addEventListener("click",l=>{const p=l.target.closest("[data-ep-id]");if(!p)return;const f=p.getAttribute("data-ep-id");r(),ia(n,f)})}async function ia(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),i=await s.json();if(!s.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=qo;const Fo=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function ra(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function zo(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function la(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const p=[];for(const f of _results){const c=f.invoices&&f.invoices.length>0?f.invoices:null;if(c&&c.length>1)for(let u=0;u<c.length;u++){const m=c[u]||{};p.push({filename:f.filename+" #"+(u+1)+"/"+c.length,engine:f.engine,merged_fields:m.fields||{}})}else p.push({filename:f.filename,engine:f.engine,merged_fields:f.merged_fields})}a=await apiPost("/api/ocr/export",{records:p,lang:currentLang,template:"sales_detail_th"})}else{const p=[];for(const c of _results)c.history_ids&&Array.isArray(c.history_ids)?p.push(...c.history_ids):c.history_id&&p.push(c.history_id);if(p.length===0){showToast(t("toast-export-error"),"error");return}const f=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+f,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:p,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let p="HTTP "+a.status;try{const c=await a.json();c&&c.detail&&(p=typeof c.detail=="string"?c.detail:JSON.stringify(c.detail))}catch(c){console.warn("[export] resp.json err.detail parse failed:",c)}const f=typeof p=="string"&&p.indexOf(".")>0?"err."+p:null;showToast(f?t(f):t("toast-export-error")+" · "+p,"error");return}const s=await a.blob();let i=o;const r=a.headers.get("X-Filename");if(r)i=r;else{const f=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(f)try{i=decodeURIComponent(f[1])}catch{}}const d=URL.createObjectURL(s),l=document.createElement("a");l.href=d,l.download=i,document.body.appendChild(l),l.click(),document.body.removeChild(l),URL.revokeObjectURL(d),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{la(ra())});function No(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=ra(),o=Fo.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
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
    `;n.innerHTML=o+s,e.appendChild(n)}function Kt(){const e=document.getElementById("export-dropdown");e&&e.remove()}const Jt=document.getElementById("btn-export-arrow");Jt&&Jt.addEventListener("click",e=>{e.stopPropagation(),!Jt.disabled&&No()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){Kt(),showToast(t("cs-coming-soon"),"info");return}zo(a),Kt(),la(a);return}e.target.closest("#btn-export-arrow")||Kt()});function Oo(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(Oo,300);const Vo=`
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
`;(function(){const e=document.getElementById("page-history");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Vo,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();function ln(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const i=s.filter(r=>_historySelected.has(r.id)).length;a.checked=i===s.length,a.indeterminate=i>0&&i<s.length}}}function Uo(){_historySelected.clear(),ln()}async function cn(){if(!_userInfo){setTimeout(()=>cn(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&s.set("client_id",String(i));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const p=await r.json().catch(()=>({}));if((typeof p.detail=="string"?p.detail:p.detail&&p.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const d=await r.json();_historyState.items=d.items||[],_historyState.total=d.total||0;const l=new Set(_historyState.items.map(p=>p.id));for(const p of Array.from(_historySelected))l.has(p)||_historySelected.delete(p);ca()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function ca(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(p=>{p.confidence==="high"&&s++});const i=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(p=>{const f=new Date(p.created_at),c=String(f.getMonth()+1).padStart(2,"0"),u=String(f.getDate()).padStart(2,"0"),m=String(f.getHours()).padStart(2,"0"),h=String(f.getMinutes()).padStart(2,"0"),_=`${c}-${u} ${m}:${h}`,w=escapeHtml(p.filename||""),b=w.length>50?w.substring(0,50)+"…":w,v=p.invoice_no?escapeHtml(p.invoice_no):b,E=[];p.seller_name&&E.push(escapeHtml(p.seller_name)),p.invoice_no&&p.filename&&E.push(b);const B=E.join(" · ")||"-",C=p.category_tag?`<span class="history-badge category">${escapeHtml(p.category_tag)}</span>`:"",L=p.source_total&&p.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:p.source_index||1,n:p.source_total}))}</span>`:"",y=p.total_amount!==null&&p.total_amount!==void 0?Number(p.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',g=[];(p.total_amount===null||p.total_amount===void 0)&&g.push(t("field-amount")),p.invoice_no||g.push(t("field-invoice-no")),p.invoice_date||g.push(t("field-invoice-date")),p.seller_name||g.push(t("field-seller-name")),g.length>0&&`${escapeHtml(p.id)}${escapeHtml(t("history-needs-review-tip")+" · "+g.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,p.edited&&`${escapeHtml(t("history-edited",{n:p.edit_count||1}))}`;const x=p.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",T=p.confidence==="high"?"high":p.confidence==="medium"?"mid":"low",S=p.confidence==="high"?t("conf-high"):p.confidence==="medium"?t("conf-medium"):t("conf-low"),I=`<span class="history-badge conf-${T}">${escapeHtml(S)}</span>`;let k="";const M=p.source||"manual";return M==="email"?k=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:M==="folder"?k=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:M==="api"&&(k=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(p.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(p.id)}" ${_historySelected.has(p.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${_}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${v} ${C} ${L} ${k} ${x}</div>
                        <div class="history-cell-subtitle">${B}</div>
                    </div>
                    <div class="history-cell-amount">${y}</div>
                    <div class="history-cell-conf">${I}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(p.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),ln();const d=a.length>0?_historyState.page*_historyState.pageSize+1:0,l=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:d,to:l,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=cn;window.renderHistoryList=ca;window.updateHistoryBatchBar=ln;window.clearHistorySelection=Uo;typeof currentRoute<"u"&&currentRoute==="history"&&cn();async function $t(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),Ko(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),Jo(a.id)}catch(n){console.error("open history detail failed",n)}}async function Go(e){await $t(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function Ko(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",Wo),document.getElementById("btn-push-erp").addEventListener("click",Yo)}async function Jo(e){}async function Yo(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function Wo(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(d=>!d.is_duplicate&&!d.is_copy),s=o>=0?o:0,i=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function Xo(e,n){document.querySelectorAll(".history-popover").forEach(p=>p.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(p=>p.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",i=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const d=()=>{r.remove(),document.removeEventListener("click",l,!0)},l=p=>{!r.contains(p.target)&&p.target!==n&&d()};setTimeout(()=>document.addEventListener("click",l,!0),0),r.addEventListener("click",async p=>{const f=p.target.closest("[data-act]");if(!f||f.disabled)return;const c=f.dataset.act;if(d(),c==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const m=document.createElement("textarea");m.value=s,m.style.position="fixed",m.style.opacity="0",document.body.appendChild(m),m.select(),document.execCommand("copy"),document.body.removeChild(m),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(c==="download-pdf"){const u=showToast(t("history-download-pdf-loading"),"loading",0);try{const m=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!m.ok)throw new Error("download failed");const h=await m.blob(),_=URL.createObjectURL(h),w=document.createElement("a");w.href=_,w.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(w),w.click(),document.body.removeChild(w),setTimeout(()=>URL.revokeObjectURL(_),5e3),u(),showToast(t("history-download-pdf-ok"),"success")}catch{u(),showToast(t("history-download-pdf-fail"),"error")}}else if(c==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const d=r.target.closest(".history-row"),l=r.target.closest("[data-hmenu]");if(l){r.stopPropagation(),Xo(l.dataset.hmenu,l);return}const p=r.target.closest("[data-review]");if(p){r.stopPropagation(),$t(p.dataset.review);return}const f=r.target.closest("[data-fill-amount]");if(f){r.stopPropagation(),Go(f.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||d&&!r.target.closest("[data-hmenu]")&&$t(d.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const d=r.target.closest(".history-row-check");if(!d)return;const l=d.dataset.hid;d.checked?_historySelected.add(l):_historySelected.delete(l),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const d=r.target.checked;for(const l of _historyState.items)d?_historySelected.add(l.id):_historySelected.delete(l.id);document.querySelectorAll(".history-row-check").forEach(l=>{l.checked=d}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const l=Array.from(_historySelected);try{const p=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:l})});if(!p.ok)throw new Error("batch delete failed");const f=await p.json();showToast(t("history-batch-done",{n:f.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(p){console.error("batch delete",p),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const d=r.target.value;document.getElementById("history-search-clear").style.display=d?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=d.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=$t;const it=document.getElementById("drop-zone"),dn=document.getElementById("file-input");it.addEventListener("click",()=>dn.click());dn.addEventListener("change",e=>da(e.target.files));["dragover","dragenter"].forEach(e=>{it.addEventListener(e,n=>{n.preventDefault(),it.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{it.addEventListener(e,n=>{n.preventDefault(),it.classList.remove("drag-over")})});it.addEventListener("drop",e=>{e.preventDefault(),da(e.dataTransfer.files)});const Zo=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function Qt(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function Qo(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function es(e){return Qo(e)||Qt(e)||Zo.test(e.name)}function da(e){hideAlerts();const n=Array.from(e),a=n.filter(es);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(d=>!Qt(d)),s=a.filter(Qt),i=new Set(_selectedFiles.map(d=>d.name+"_"+d.size));for(const d of o){const l=d.name+"_"+d.size;i.has(l)||(_selectedFiles.push({file:d,name:d.name,size:d.size,status:"waiting",errorKey:null,errorParams:null}),i.add(l))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(d){console.error("[upload] image route failed",d)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),Vt(),pn(),dn.value=""}let Ct=!1;function Vt(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(c=>c.status==="processing"||c.status==="retrying").length,o=_selectedFiles.filter(c=>c.status==="success").length,s=_selectedFiles.filter(c=>c.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const d=Ct?t("file-list-collapse"):t("file-list-expand"),l=_selectedFiles.map((c,u)=>{let m=t("status-"+c.status);c.status==="retrying"&&(m=t("status-retrying")),c.status==="error"&&c.errorKey&&(m=t(c.errorKey,c.errorParams||{}));const h=c.status==="processing"||c.status==="retrying"?'<span class="spinner"></span>':"",_=c.status==="error"&&c.canRetry?`<button class="file-retry-btn" data-retry-idx="${u}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",w=c.status==="success"&&c.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</span>
                ${w}
                <span class="file-status ${c.status}">${h}${m}</span>
                ${_}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(d)}</button>`:""}
        </div>
        <ul class="file-list-body${Ct?" expanded":""}" id="file-list-body">
            ${l}
        </ul>
    `;const p=document.getElementById("file-list-toggle");p&&p.addEventListener("click",()=>{Ct=!Ct,Vt()});const f=document.getElementById("file-list-body");f&&!f.dataset.retryBound&&(f.dataset.retryBound="1",f.addEventListener("click",async c=>{const u=c.target.closest(".file-retry-btn");if(!u)return;const m=parseInt(u.dataset.retryIdx||"-1",10);if(m<0||m>=_selectedFiles.length)return;const h=_selectedFiles[m];!h||h.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(h,!0)}))}function pn(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],Vt(),renderResults(),pn(),hideAlerts()});window.renderFileList=Vt;window.updateStartButton=pn;const ts=`
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
`;we("camera-tips-modal",ts);(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await as()||o.click()}),o.addEventListener("change",async d=>{const l=Array.from(d.target.files||[]);if(d.target.value="",l.length!==0)for(const p of l)await en([p],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=d=>async l=>{const p=Array.from(l.target.files||[]);if(l.target.value="",p.length===0)return;const f=p.filter(u=>u.type==="application/pdf"||/\.pdf$/i.test(u.name)),c=p.filter(u=>!f.includes(u));f.length>0&&await ns(f),c.length>0&&await en(c,d)};a&&a.addEventListener("change",r("gallery"))})();async function ns(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function as(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const i=d=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(d)},r=d=>{d.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),o&&(o.onclick=()=>i(!1)),n.onclick=d=>{d.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}async function Ht(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],i=o.naturalWidth,r=o.naturalHeight;(i<1e3||r<1e3)&&s.push("low_res");try{const d=document.createElement("canvas");d.width=64,d.height=64;const l=d.getContext("2d");l.drawImage(o,0,0,64,64);const p=l.getImageData(0,0,64,64).data;let f=0,c=0;for(let m=0;m<p.length;m+=4)f+=.299*p[m]+.587*p[m+1]+.114*p[m+2],c++;const u=c?f/c:128;u<70?s.push("too_dark"):u>235&&s.push("too_bright"),n({warnings:s,width:i,height:r,brightness:u})}catch{n({warnings:s,width:i,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}let Ce=[],Oe=null;async function en(e,n){if(hideAlerts(),!(!e||e.length===0)){var a=typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice";if(a==="thai_id_card"){for(const s of e)_selectedFiles.push({file:s,name:s.name,size:s.size,status:"waiting",errorKey:null,errorParams:null});const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton();return}if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let o=0;o<30&&(await new Promise(s=>setTimeout(s,100)),!(window.jspdf&&window.jspdf.jsPDF));o++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const o=e[0];let s={};try{s=await Ht(o)}catch{}Ce.push({file:o,quality:s}),Oe="camera",et();return}if(n==="gallery"&&(e.length>=2||Ce.length>0)){for(const o of e){let s={};try{s=await Ht(o)}catch{}Ce.push({file:o,quality:s})}Oe="gallery",et();return}await pa(e)}}async function os(e){const n=new Set;for(const o of e)try{((await Ht(o)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const o=await ua(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function et(){let e=document.getElementById("camera-buffer-bar");if(Ce.length===0){e&&e.remove(),Oe=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=Ce.length,a=n>=2,o=Oe==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?o?i=`
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
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{Ce=[],Oe=null,et()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const l=o?"gallery-input":"camera-input",p=document.getElementById(l);p&&p.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const l=Ce.map(p=>p.file);Ce=[],Oe=null,et(),await os(l)});const d=e.querySelector('[data-cbb-action="separate"]');d&&(d.onclick=async()=>{const l=Ce.map(p=>p.file);Ce=[],Oe=null,et(),await pa(l)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{Ce.length>0&&et()});async function pa(e){const n=new Set;let a=0;for(const s of e)try{((await Ht(s)).warnings||[]).forEach(d=>n.add(d));const r=await ua([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}async function ua(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let p=0;p<e.length;p++){const f=e[p],{dataUrl:c,naturalW:u,naturalH:m}=await ss(f);p>0&&s.addPage("a4","p");const h=u/m;let _=a-10,w=_/h;w>o-10&&(w=o-10,_=w*h);const b=(a-_)/2,v=(o-w)/2,E=f.type==="image/png"?"PNG":"JPEG";s.addImage(c,E,b,v,_,w,void 0,"FAST")}const i=s.output("blob"),r=new Date,d=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),l=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${d}${l}.pdf`,{type:"application/pdf"})}function ss(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}window.handleCameraImages=en;(function(){var e="pearnly_ocr_doc_mode",n=!1,a=!1;function o(u){return typeof escapeHtml=="function"?escapeHtml(u==null?"":String(u)):String(u??"")}function s(){try{return localStorage.getItem(e)==="thai_id_card"?"thai_id_card":"invoice"}catch{return"invoice"}}window.getOcrDocumentMode=function(){return n?s():"invoice"};function i(){var u=document.getElementById("drop-zone");return u?u.closest(".card"):null}function r(){var u=i();if(!u)return null;var m=u.querySelector("#ocr-doc-mode");if(m)return m;var h=u.querySelector(".section-head");return m=document.createElement("div"),m.id="ocr-doc-mode",m.className="ocr-doc-mode",m.setAttribute("role","tablist"),m.style.cssText="display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;",h&&h.parentNode?h.parentNode.insertBefore(m,h.nextSibling):u.insertBefore(m,u.firstChild),m}function d(u,m,h){return'<button type="button" class="ocr-doc-seg'+(h?" active":"")+'" data-doc-mode="'+u+'" role="tab" aria-selected="'+(h?"true":"false")+'" style="border:none;background:'+(h?"var(--card,#fff)":"transparent")+";color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:"+(h?"600":"500")+";padding:6px 16px;border-radius:7px;cursor:pointer;box-shadow:"+(h?"0 1px 3px rgba(0,0,0,.08)":"none")+';transition:background .15s;">'+o(t(m))+"</button>"}function l(){var u=r();if(u){if(!n){u.style.display="none";return}var m=s();u.style.display="flex",u.innerHTML=d("invoice","ocr-mode-invoice",m==="invoice")+d("thai_id_card","ocr-mode-id-card",m==="thai_id_card")}}function p(u){try{localStorage.setItem(e,u==="thai_id_card"?"thai_id_card":"invoice")}catch{}l();try{document.dispatchEvent(new CustomEvent("ocr-doc-mode-change",{detail:{mode:window.getOcrDocumentMode()}}))}catch{}}async function f(u){if(!(a&&!u)){var m=localStorage.getItem("mrpilot_token");if(m)try{var h=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+m}});if(!h.ok)return;var _=await h.json(),w=_&&_.items||[];n=w.some(function(b){return b&&(b.adapter||"").toLowerCase()==="mrerp_dms"&&b.enabled!==!1}),a=!0,window._dmsHasEndpoint=n,l()}catch{}}}window._refreshOcrDocMode=function(){f(!0)},document.addEventListener("click",function(u){var m=u.target.closest(".ocr-doc-seg");m&&m.getAttribute("data-doc-mode")&&(u.preventDefault(),p(m.getAttribute("data-doc-mode")))}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("ocr-doc-mode",l);function c(){r(),l(),f(!1)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),window.addEventListener("hashchange",function(){((location.hash||"").indexOf("ocr")>=0||location.hash===""||location.hash==="#home")&&setTimeout(function(){r(),f(!1)},60)})})();(function(){function e(i){return typeof escapeHtml=="function"?escapeHtml(i==null?"":String(i)):String(i??"")}function n(){var i=(function(){var d=document.getElementById("drop-zone");return d?d.closest(".card"):null})();if(!i||!i.parentNode)return null;var r=document.getElementById("dms-id-card-result");return r||(r=document.createElement("div"),r.id="dms-id-card-result",r.className="card",r.style.cssText="display:none;margin-top:16px;",i.parentNode.insertBefore(r,i.nextSibling),r)}function a(i,r){return'<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);"><span style="color:var(--muted,#6b6b66);font-size:13px;">'+e(t(i))+'</span><span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">'+e(r||"—")+"</span></div>"}function o(i){if(!i)return"";var r=[i.house_no,i.road,i.subdistrict,i.district,i.province,i.zipcode].filter(function(d){return d});return r.join(" ")||i.address_raw||""}function s(i){var r=i&&i.status||"failed",d,l,p;return r==="success"?(d="#0a7a2c",l="#d6f5e0",p="dms-result-status-success"):r==="needs_review"?(d="#9a6b00",l="#fdf0d0",p="dms-result-status-needs-review"):r==="skipped"?(d="#5d5d57",l="#eee",p="dms-result-status-skipped"):(d="#b3261e",l="#fbe0de",p="dms-result-status-failed"),'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:'+d+";background:"+l+';">'+e(t(p))+"</span>"}window.renderDmsIdCardResult=function(i){var r=n();if(r){i=i||{};var d=i.id_card||{},l=d.address||{},p=i.dms_push||{},f=p.status||(i.ok?"success":"failed"),c="";f==="success"&&(c=a("dms-result-customer",p.customer_id)+a("dms-result-booking",p.booking_no));var u=f==="failed"||f==="needs_review"?'<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">'+e(t("dms-result-retry"))+"</button>":"",m="";if(f==="failed"&&p.error_code){var h="dms-err-"+String(p.error_code).toLowerCase(),_=t(h);(!_||_===h)&&(_=t("dms-err-err_dms_unexpected")),m='<div style="margin-top:8px;color:#b3261e;font-size:12px;">'+e(_)+"</div>"}r.style.display="",r.innerHTML='<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;"><div class="section-title">'+e(t("dms-result-title"))+"</div>"+s(p)+'</div><div style="margin-top:8px;">'+a("dms-result-name",(d.first_name||"")+" "+(d.last_name||""))+a("dms-result-id",d.people_id_masked)+a("dms-result-birthday",d.birthday_be)+a("dms-result-address",o(l))+c+"</div>"+m+u}},window.clearDmsIdCardResult=function(){var i=document.getElementById("dms-id-card-result");i&&(i.style.display="none",i.innerHTML="")},document.addEventListener("click",function(i){i.target.closest("#dms-id-card-retry")&&(i.preventDefault(),typeof window._dmsRetryIdCard=="function"&&window._dmsRetryIdCard())})})();document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,(typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice")==="thai_id_card"){try{await fa()}finally{const c=document.getElementById("btn-start");c&&(c.disabled=!1)}return}if(_userInfo&&_userInfo.plan==="free"){const c=await fetch("/api/health").then(u=>u.json()).catch(()=>null);c&&!c.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const n=_selectedFiles.filter(c=>c.status==="waiting"),a=6;async function o(c,u){if(window._ocrAborted)return c.status="cancelled",c.errorKey=null,renderFileList(),{};c.status=u?"retrying":"processing",c.canRetry=!1,renderFileList();const m=new AbortController,h=setTimeout(()=>m.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(m);try{const _=new FormData;_.append("file",c.file,c.name);try{if(typeof window.getCurrentClientId=="function"){const B=window.getCurrentClientId();B!=null&&_.append("client_id",String(B))}}catch{}const w=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:_,signal:m.signal});if(clearTimeout(h),window._ocrCtrls.delete(m),w.status===401||w.status===403){const C=await w.clone().json().catch(()=>({})),L=C&&C.detail,y=typeof L=="string"?L:L&&L.code||"";if(!y||y.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),y==="auth.session_revoked")_showSessionRevokedModal();else{const g=y==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(g),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}y==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!w.ok){const C=(await w.json().catch(()=>({}))).detail;return typeof C=="string"?(c.errorKey="err."+C,c.errorParams=null):C&&C.code?(c.errorKey="err."+C.code,c.errorParams={...C,mb:_quota.max_file_size_mb}):(c.errorKey="err.unknown",c.errorParams=null),(c.errorKey==="err.unknown"||c.errorKey==="err.ocr.engine_error")&&(w.status===429?c.errorKey="err.rate_limit":w.status===502||w.status===503||w.status===504?c.errorKey="err.gemini_overloaded":w.status>=500&&(c.errorKey="err.server")),c.status="error",c.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(c.errorKey||""),renderFileList(),{}}const b=await w.json();c.status="success",c.fromCache=!!b.from_cache;const v=mergeFields(b.pages),E=b.confidence||(v.items&&v.items.length>0?"high":"low");if(_results.push({filename:b.filename,pages:b.pages,page_count:b.page_count,elapsed_ms:b.elapsed_ms,engine:b.engine,merged_fields:v,edits:{},confidence:E,history_id:b.history_id,history_ids:b.history_ids||[],invoice_count:b.invoice_count||1,invoices:b.invoices||[],archive_name:b.archive_name||null,category_tag:b.category_tag||null,auto_pushed:!!b.auto_pushed,typhoon_enhanced:!!b.typhoon_enhanced,typhoon_pages:b.typhoon_pages||[],from_cache:!!b.from_cache}),b.invoice_count&&b.invoice_count>1&&showToast(t("multi-invoice-toast",{file:b.filename,n:b.invoice_count}),"success"),b.missed_invoice_warnings&&b.missed_invoice_warnings.length){const B=b.missed_invoice_warnings.map(function(C){return C.page}).filter(function(C){return C!=null});showToast(t("missed-invoice-warn",{file:b.filename,pages:B.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",b.missed_invoice_warnings)}if(b.typhoon_enhanced&&b.typhoon_pages&&b.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:b.filename,n:b.typhoon_pages.length}),"success"),b.fallback_used){const B=b.engine_chain||[],C=b.engine||"";let L;C==="typhoon_nvidia"?L="fallback-typhoon-nvidia-toast":C==="easyocr"?L="fallback-easyocr-toast":L="fallback-generic-toast",showToast(t(L,{file:b.filename}),"warn"),console.info("[OCR Chain]",B)}if(b.from_cache&&showToast(t("cache-hit-toast",{file:b.filename}),"info"),b.duplicate_warnings&&b.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const B of b.duplicate_warnings)window._dupQueue.push({filename:b.filename,...B})}return b.auto_pushed&&showToast(t("auto-push-fired",{file:b.filename}),"info"),b.quota&&b.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=b.quota.used_this_month,_userInfo.tenant_used=b.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(_){clearTimeout(h);try{window._ocrCtrls&&window._ocrCtrls.delete(m)}catch{}console.error("[Upload] failed for",c.file.name,_);const w=_&&(_.name==="AbortError"||_==="timeout"),b=w&&(m.signal.reason==="timeout"||_==="timeout"),v=_&&_.message&&/NetworkError|Failed to fetch/i.test(_.message);return w&&(m.signal.reason==="user_stop"||window._ocrAborted)?(c.status="cancelled",c.errorKey=null,c.canRetry=!1,renderFileList(),{}):(b?c.errorKey="err.timeout":w?c.errorKey="err.aborted":v?c.errorKey="err.network":(c.errorKey="err.unknown",c.errorParams={msg:_&&_.message?_.message:String(_)}),c.status="error",!u&&!window._ocrAborted&&(v||b)&&navigator.onLine!==!1&&(c.canRetry=!0,renderFileList(),await new Promise(B=>setTimeout(B,2e3)),c.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?o(c,!0):(c.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=o;let s=0,i=!1;async function r(){for(;s<n.length&&!i&&!window._ocrAborted;){const c=s++,u=await o(n[c]);if(u&&u.abort){i=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const d=document.getElementById("btn-start"),l=document.getElementById("btn-stop");d&&(d.style.display="none"),l&&(l.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(n)}catch{}const p=[];for(let c=0;c<Math.min(a,n.length);c++)p.push(r());await Promise.all(p);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}d&&(d.style.display=""),l&&(l.style.display="none");const f=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const c={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const m of n)if(m.status==="success")c.success++;else if(m.status==="cancelled")c.cancelled++;else if(m.status==="error"){const h=m.errorKey||"";h==="err.network"?c.network++:h==="err.timeout"||h==="err.aborted"?c.timeout++:h.indexOf("quota")>=0||h==="err.monthly_limit_exceeded"?c.quota++:h==="err.gemini_overloaded"||h==="err.server"?c.overloaded++:h==="err.rate_limit"?c.rate++:c.other++}const u=n.length;f?showToast(is(c,u),"warn",4e3):u>1&&c.network+c.timeout+c.quota+c.overloaded+c.rate+c.other>0&&showToast(rs(c),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function is(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function rs(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});async function fa(e){let n;if(e)n=_selectedFiles.find(a=>a.file===e)||{file:e,name:e.name,status:"waiting"};else{const a=_selectedFiles.filter(o=>o.status==="waiting");if(!a.length)return;n=a[0]}window._dmsLastFile=n.file,n.status="processing",typeof renderFileList=="function"&&renderFileList();try{const a=new FormData;a.append("file",n.file,n.name),a.append("push","true");const o=await fetch("/api/dms/id-card-booking",{method:"POST",headers:{Authorization:"Bearer "+token},body:a});if(o.status===401||o.status===403){const i=await o.clone().json().catch(()=>({})),r=i&&i.detail,d=typeof r=="string"?r:r&&r.code||"";if(!d||d.startsWith("auth.")){localStorage.removeItem("mrpilot_token"),showToast(t("alert-session"),"error"),setTimeout(()=>{window.location.href="/"},1200);return}}const s=await o.json().catch(()=>({}));if(!o.ok){n.status="error";const i=s&&s.detail&&(s.detail.code||s.detail)||"unknown";n.errorKey="err."+i,n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:String(i)}});return}n.status=s.ok||s.dms_push&&s.dms_push.status==="needs_review"?"success":"error",typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult(s),typeof updateStartButton=="function"&&updateStartButton()}catch{n.status="error",n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:"network"}})}}window._dmsRetryIdCard=function(){window._dmsLastFile&&fa(window._dmsLastFile)};function ma(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=m=>m!=null?Number(m).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",d=m=>m||"—",l=m=>{try{const h=new Date(m);return`${h.getFullYear()}-${String(h.getMonth()+1).padStart(2,"0")}-${String(h.getDate()).padStart(2,"0")}`}catch{return m}},p=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",f=(e.matched_fields||[]).map(m=>{const h=t("dup-field-"+m.replace("_","-"))||m;return`<span class="dup-field-chip">${escapeHtml(h)}</span>`}).join(" "),c=document.createElement("div");c.className="log-detail-modal",c.innerHTML=`
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
                        <tr><td>${escapeHtml(t("dup-field-uploaded-at"))}</td><td>—</td><td>${escapeHtml(l(e.match.created_at))}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="dup-actions">
                <button class="btn btn-ghost btn-tiny" data-action="view">${escapeHtml(t("dup-action-view"))}</button>
                <button class="btn btn-danger btn-tiny" data-action="delete">${escapeHtml(t("dup-action-delete"))}</button>
                <button class="btn btn-primary btn-tiny" data-action="keep">${escapeHtml(t("dup-action-keep"))}</button>
            </div>
        </div>
    `,document.body.appendChild(c);const u=()=>{c.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(ma,200)};c.querySelector(".dup-close").addEventListener("click",u),c.querySelector('[data-action="view"]').addEventListener("click",()=>{const m=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(m)},400),u()}),c.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const m=e.new_history_id;if(!m){u();return}try{(await fetch(`/api/history/${encodeURIComponent(m)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}u()}),c.querySelector('[data-action="keep"]').addEventListener("click",u)}window.showDuplicateDialog=ma;function Ue(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function mt(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function ls(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ue("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ue("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ue("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ue("time-day-ago-suffix"," 天前")}catch{return""}}async function un(){va();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const d={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[l,p,f]=await Promise.all([fetch("/api/me/tenant-usage",{headers:d}).then(w=>w.ok?w.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:d}).then(w=>w.ok?w.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:d}).then(w=>w.ok?w.json():null).catch(()=>null)]),c=l&&l.ocr_this_month||0;let u=0;const m=p&&(p.items||p.history||p)||[],h=Array.isArray(m)?m:[];h.forEach(w=>{(w.status==="pending"||w.status==="reviewing")&&u++});const _=f&&(f.total||f.count||f.pending||0)||0;if(e&&(e.textContent=mt(c)),n&&(n.textContent=mt(u)),a&&(a.textContent=mt(_)),r&&(_>0?(r.style.display="",r.textContent=_):r.style.display="none"),o&&l){const w=l.ocr_this_month||0,b=l.quota||0;o.textContent=mt(w),s&&(s.textContent=b?w+" / "+mt(b)+" 张":Ue("dash-kpi-plan-sub","本月用量"))}if(i)if(h.length===0)i.innerHTML='<div class="dash-recent-empty">'+Ue("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const w=h.slice(0,5).map(b=>{const v=(b.invoice_no||b.filename||b.id||"").toString(),E=(b.supplier_name||b.buyer_name||b.client_name||b.notes||"").toString(),B=ls(b.created_at||b.upload_time||b.date),C=L=>String(L).replace(/[&<>"']/g,y=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[y]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+C(v)+'">'+C(v)+'</span><span class="dash-recent-mid" title="'+C(E)+'">'+C(E)+'</span><span class="dash-recent-time">'+C(B)+"</span></div>"}).join("");i.innerHTML=w}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+Ue("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=un;async function va(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},d=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!d.ok){e.style.display="none",s&&(s.textContent="—"),i&&(i.textContent="");return}const l=await d.json(),p=!!l.is_owner,f=!!l.is_billing_exempt;if(!p)e.style.display="none";else if(e.style.display="",f)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const u=typeof l.balance_thb=="number"?l.balance_thb:0;if(a&&(a.textContent="฿"+u.toFixed(2),a.className=u<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const m=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",h=u<50?"#dc2626":"#6b7280",_=w=>typeof window.escapeHtml=="function"?window.escapeHtml(w):String(w).replace(/[&<>"']/g,b=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[b]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+h+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+_(m)+"</a>"}}const c=typeof l.pages_this_month=="number"?l.pages_this_month:typeof l.my_invoice_count=="number"?l.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(c)),i){const u=c>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",m=typeof window.t=="function"?window.t(u,{used:c}):c+" pages";i.textContent=m}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=va;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(un,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&un()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function fn(){return localStorage.getItem("mrpilot_token")||""}function me(e){return document.getElementById(e)}var Tt=null,bt=null;function ha(){bt||(bt=setInterval(function(){if(!document.hidden){var e=fn();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;Tt!==null&&a>Tt&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Tt=a}}).catch(function(){}))}},3e4))}function cs(){bt&&(clearInterval(bt),bt=null),Tt=null}window._startCreditsPoll=ha;window._stopCreditsPoll=cs;ha();var mn=null,vn=0;function ds(){if(!me("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),ps()}}function ga(){var e=function(n,a){var o=me(n);o&&(o.textContent=a)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function _t(e){[1,2,3].forEach(function(s){var i=me("tv2-s"+s);i&&(i.style.display=s===e?"":"none");var r=me("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=me("tv2-back"),a=me("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=he("topup-btn-cancel")):n&&(n.style.display="",n.textContent=he("topup-btn-back")),a&&(a.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=me("tv2-bn");o&&(o.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(vn).toLocaleString()+"</strong>"))}}function tn(){for(var e=1;e<=3;e++){var n=me("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function At(e){var n=me(e);n&&(n.textContent="",n.style.display="none")}function yt(e,n){var a=me(e);a&&(a.textContent=n,a.style.display="")}function $n(e){var n=me("tv2-dt");n&&(n.textContent=e.name);var a=me("tv2-drop");a&&a.classList.add("has-file"),At("tv2-se")}function ps(){var e=me("topup-v2-ov");me("tv2-close").addEventListener("click",vt),e.addEventListener("click",function(i){i.target===e&&vt()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&vt()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(l){l.classList.remove("active")}),r.classList.add("active");var d=me("tv2-amt");d&&(d.value=r.dataset.val,At("tv2-ae"))}});var n=me("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),At("tv2-ae")});var a=me("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=he("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var o=me("tv2-drop"),s=me("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(i){i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(i){i.preventDefault(),o.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&$n(r)})),s&&s.addEventListener("change",function(){s.files[0]&&$n(s.files[0])}),me("tv2-back").addEventListener("click",function(){var i=tn();if(i<=1){vt();return}_t(i-1)}),me("tv2-next").addEventListener("click",function(){var i=tn();i===1?us():i===2?_t(3):fs()})}async function us(){var e=me("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){yt("tv2-ae",he("topup-amount-invalid"));return}if(n>5e5){yt("tv2-ae",he("topup-amount-too-large"));return}vn=n;var a=me("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+fn()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),i=he("topup-submit-fail");try{var r=JSON.parse(s),d=r.detail;if(Array.isArray(d)&&d.length){var l=d[0]&&d[0].type||"";l.indexOf("less_than")>=0?i=he("topup-amount-too-large"):(l.indexOf("greater_than")>=0||l.indexOf("parsing")>=0)&&(i=he("topup-amount-invalid"))}else typeof d=="string"&&(i=d)}catch{}throw new Error(i)}var p=await o.json();mn=p.request_id,_t(2)}catch(f){yt("tv2-ae",f.message||he("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=he("topup-btn-next"))}}async function fs(){var e=me("tv2-file");if(!e||!e.files||!e.files[0]){yt("tv2-se",he("topup-slip-required"));return}var n=me("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=me("tv2-payer"),s=me("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+mn,{method:"POST",headers:{Authorization:"Bearer "+fn()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),vt()}catch(d){yt("tv2-ue",he("topup-upload-fail")+" · "+d.message),n&&(n.disabled=!1,n.textContent=he("topup-btn-submit"))}}function vt(){var e=me("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){ds(),mn=null,vn=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=me(a);o&&(o.value="")});var e=me("tv2-file");e&&(e.value="");var n=me("tv2-drop");n&&n.classList.remove("has-file","drag-over"),me("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){At(a)}),ga(),_t(1),me("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=me("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(ga(),_t(tn()))});const ms=`
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

    `;we("page-test-center",ms);(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",i=!1,r=!1;function d(j,$,q){let F=typeof t=="function"?t(j):null;return(!F||F===j)&&(F=$),q&&Object.keys(q).forEach(function(W){F=String(F).replace("{"+W+"}",String(q[W]))}),F}function l(){try{const j=localStorage.getItem(n);o=j?JSON.parse(j):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function p(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function f(j){const $=new Date(j),q=function(F){return F<10?"0"+F:""+F};return q($.getHours())+":"+q($.getMinutes())+":"+q($.getSeconds())}function c(j){return String(j??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function u(j,$){try{typeof showToast=="function"?showToast(j,$||"info"):alert(j)}catch{}}function m(j){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(j).then(function(){u(d("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){h(j)}):h(j)}catch{h(j)}}function h(j){try{const $=document.createElement("textarea");$.value=j,$.style.position="fixed",$.style.opacity="0",document.body.appendChild($),$.select();const q=document.execCommand("copy");document.body.removeChild($),u(q?d("tc-toast-copied","已复制"):d("tc-toast-copy-fail","复制失败"),q?"success":"error")}catch{u(d("tc-toast-copy-fail","复制失败"),"error")}}function _(){const j=document.getElementById("tc-account-chip"),$=document.getElementById("tc-progress-chip");if(j&&(j.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),$){const q=a.length,F=a.filter(function(W){return o[W.id]}).length;$.textContent=F+" / "+q}}function w(){const j=document.getElementById("tc-checklist-body");if(!j)return;const $={};a.forEach(function(F){$[F.group]||($[F.group]=[]),$[F.group].push(F)});const q=[];Object.keys($).forEach(function(F){q.push('<div class="tc-checklist-group">'),q.push('<div class="tc-checklist-group-title">'+c(F)+"</div>"),$[F].forEach(function(W){const G=o[W.id]||"",A=G?"is-"+G:"";q.push('<div class="tc-check-item '+A+'" data-id="'+c(W.id)+'"><div class="tc-check-id">'+c(W.id)+'</div><div class="tc-check-desc">'+c(W.desc)+'</div><div class="tc-check-actions">'+b(W.id,"pass",G)+b(W.id,"fail",G)+b(W.id,"skip",G)+"</div></div>")}),q.push("</div>")}),j.innerHTML=q.join("")}function b(j,$,q){const F=q===$,W={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},G={pass:d("tc-status-pass","通过"),fail:d("tc-status-fail","失败"),skip:d("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(F?"is-active "+$:"")+'" data-id="'+c(j)+'" data-kind="'+$+'" title="'+c(G[$])+'">'+W[$]+"</button>"}function v(j){return s==="all"?!0:s==="js_error"?j.type==="js_error"||j.type==="promise_error":s==="api"?j.type==="api_error"||j.type==="api_fail":s==="api_slow"?j.type==="api_slow":s==="console"?j.type==="console_error"||j.type==="console_warn":!0}function E(){const j=document.getElementById("tc-logs-body"),$=document.getElementById("tc-logs-count");if(!j)return;const q=(window._pearnlyTcLogs||[]).slice().reverse(),F=q.filter(v);if($&&($.textContent=String(q.length)),F.length===0){j.innerHTML='<div class="tc-logs-empty">'+c(d("tc-logs-empty","暂无异常"))+"</div>";return}const W=F.slice(0,100).map(function(G){const A=typeof G.detail=="object"?JSON.stringify(G.detail,null,2):String(G.detail||"");return'<div class="tc-log-item t-'+c(G.type)+'" data-ts="'+G.ts+'"><span class="tc-log-time">'+f(G.ts)+'</span><span class="tc-log-type">'+c(G.type)+'</span><div class="tc-log-summary">'+c(G.summary)+'<div class="tc-log-detail">'+c(A)+"</div></div></div>"}).join("");j.innerHTML=W,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(G){G.classList.toggle("active",G.getAttribute("data-filter")===s)})}function B(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&E(),C()},200))}window._tcOnNewLog=B;function C(){const j=document.getElementById("nav-test-badge");if(!j)return;const $=(window._pearnlyTcLogs||[]).filter(function(q){return q.type==="js_error"||q.type==="promise_error"||q.type==="api_error"||q.type==="api_fail"||q.type==="console_error"}).length;$>0?(j.style.display="",j.textContent=$>99?"99+":String($)):j.style.display="none"}function L(){_(),w(),E(),C()}function y(){const j=[],$=new Date,q=_userInfo&&(_userInfo.email||_userInfo.username)||"—";j.push("# Pearnly "+e+" 测试结果"),j.push("- 账号:"+q),j.push("- 时间:"+$.toISOString().replace("T"," ").slice(0,19));const F=a.length,W=a.filter(function(oe){return o[oe.id]==="pass"}).length,G=a.filter(function(oe){return o[oe.id]==="fail"}).length,A=a.filter(function(oe){return o[oe.id]==="skip"}).length,N=F-W-G-A;j.push("- 进度:"+(W+G+A)+" / "+F+" · ✅ "+W+" · ❌ "+G+" · ⏭ "+A+" · 未测 "+N),j.push(""),j.push("| ID | 描述 | 状态 |"),j.push("|---|---|---|"),a.forEach(function(oe){const se=o[oe.id],ue=se==="pass"?"✅":se==="fail"?"❌":se==="skip"?"⏭":"⬜";j.push("| "+oe.id+" | "+oe.desc.replace(/\|/g,"\\|")+" | "+ue+" |")});const V=a.filter(function(oe){return o[oe.id]==="fail"});V.length>0&&(j.push(""),j.push("## ❌ 失败项"),V.forEach(function(oe){j.push("- **"+oe.id+"** · "+oe.desc)}));const X=(window._pearnlyTcLogs||[]).slice(-30).reverse();return X.length>0&&(j.push(""),j.push("## 🔴 异常日志(最近 "+X.length+" 条)"),X.forEach(function(oe){if(j.push("- `"+f(oe.ts)+"` · **"+oe.type+"** · "+oe.summary),oe.detail){let se;try{se=JSON.stringify(oe.detail)}catch{se=String(oe.detail)}se&&se!=="{}"&&j.push("  - "+se.slice(0,600))}})),j.join(`
`)}function g(j){const $=(window._pearnlyTcLogs||[]).slice(-30).reverse();if($.length===0)return"(暂无异常日志)";const q=["# Pearnly 异常日志(最近 "+$.length+" 条)"],F=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return q.push("- 账号:"+F),q.push("- 当前页:"+(currentRoute||"?")),q.push("- UA:"+navigator.userAgent),q.push(""),$.forEach(function(W){if(q.push("## `"+f(W.ts)+"` · "+W.type),q.push("- "+W.summary),W.detail){q.push("```");try{q.push(JSON.stringify(W.detail,null,2).slice(0,2e3))}catch{q.push(String(W.detail).slice(0,2e3))}q.push("```")}}),q.join(`
`)}function x(){const j=Date.now();fetch("/api/health").then(function($){const q=Date.now()-j;$.ok?u(d("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:q}),"success"):u(d("tc-toast-health-fail","后端无响应")+" ("+$.status+")","error")}).catch(function(){u(d("tc-toast-health-fail","后端无响应"),"error")})}function T(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}L(),u(d("tc-toast-cleared","session 状态已清空"),"success")}function S(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(j){return j.json()}).then(function(j){window._clientsCache=j.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),u("客户缓存已刷新 · "+(j.clients||[]).length+" 个客户","success")}).catch(function(){u("刷新失败","error")})}catch{}}function I(){if(i||!document.getElementById("page-test-center"))return;i=!0;const $=document.getElementById("tc-checklist-body");$&&$.addEventListener("click",function(se){const ue=se.target.closest(".tc-status-btn");if(!ue)return;const D=ue.getAttribute("data-id"),O=ue.getAttribute("data-kind");!D||!O||(o[D]===O?delete o[D]:o[D]=O,p(),w(),_())});const q=document.getElementById("tc-btn-reset-checklist");q&&q.addEventListener("click",function(){o={},p(),w(),_()});const F=document.getElementById("tc-btn-copy-all");F&&F.addEventListener("click",function(){m(y())});const W=document.getElementById("tc-btn-copy-logs");W&&W.addEventListener("click",function(){m(g())});const G=document.getElementById("tc-btn-clear-logs");G&&G.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,E(),C()});const A=document.getElementById("tc-logs-filter");A&&A.addEventListener("click",function(se){const ue=se.target.closest(".tc-filter-chip");ue&&(s=ue.getAttribute("data-filter")||"all",E())});const N=document.getElementById("tc-logs-body");N&&N.addEventListener("click",function(se){const ue=se.target.closest(".tc-log-item");ue&&ue.classList.toggle("expanded")});const V=document.getElementById("tc-tool-health");V&&V.addEventListener("click",x);const X=document.getElementById("tc-tool-clear-session");X&&X.addEventListener("click",T);const oe=document.getElementById("tc-tool-reload-clients");oe&&oe.addEventListener("click",S)}function k(){}window._tcApplyVisibility=k;let M=0;const H=setInterval(function(){M++,_userInfo&&clearInterval(H),M>60&&clearInterval(H)},500);window.loadTestCenterPage=function(){l(),I(),L()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){C(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&L()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(v,E){if(typeof window.t=="function"){const B=window.t(v);if(B&&B!==v)return B}return E}function o(){const v=window._userInfo||{},E=String(v.role||"").toLowerCase(),B=String(v.tenant_role||"").toLowerCase();return v.is_super_admin===!0||v.is_owner===!0||E==="owner"||E==="admin"||B==="owner"||B==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const v=localStorage.getItem(e);if(!v||v==="null"||v==="0"||v==="")return null;const E=parseInt(v,10);return isNaN(E)?null:E}function r(v){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:v,mode:s()}}))}catch{}}function d(v){const E=i();v==null||v===0?localStorage.removeItem(e):(localStorage.setItem(e,String(v)),localStorage.setItem(n,"client")),String(E)!==String(v)&&r(v)}function l(){const v=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),v!=null&&r(null)}async function p(){try{const v=window.apiGet;if(typeof v!="function")return[];const E=await v("/api/workspace/clients");return E&&(E.clients||E.items)||[]}catch{return[]}}async function f(v){if(s()==="client"&&i()!=null)return typeof v=="function"&&v(),!0;const E=a("ws-need-client","这个功能需要先选择工作空间"),B=a("ws-btn-pick","选择工作空间"),C=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(E,{okText:B,cancelText:C})&&c(v):window.confirm(E+`

[`+B+" / "+C+"]")&&c(v),!1}async function c(v){const E=await p();if(typeof v=="function"&&s()!=="personal"&&E.length===1){d(Number(E[0].id)),v();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:E,canCreate:o(),active:i(),onPersonal:l,onPick:function(B){d(Number(B)),typeof v=="function"&&v()},emptyHint:E.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!E.length){const B=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(B,"info")}}function u(v){const E=v||document.getElementById("workspace-switcher-root");if(!E)return;const B=s(),C=i();let L,y;if(B==="client"&&C!=null){const T=(window._workspaceClientsCache||[]).find(S=>Number(S.id)===Number(C));L=h("building"),y=T?T.name:a("ws-current-label","当前工作空间")}else L=h("user"),y=a("ws-personal","个人事务");E.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+L+'<span class="ws-ctrl-label">'+m(y)+"</span></button>";const g=E.querySelector("#ws-ctrl-btn");g&&g.addEventListener("click",()=>c(null))}function m(v){return String(v??"").replace(/[&<>"']/g,function(E){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[E]})}function h(v){const E='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return v==="building"?E+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':E+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function _(v){v=v||{};const E=v.clients||[],B=v.active,C=document.getElementById("ws-modal");C&&C.remove();const L=document.createElement("div");L.id="ws-modal",L.className="ws-modal";const g='<button type="button" class="ws-modal-item'+(s()==="personal"||B==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+h("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+m(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+m(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let x="";if(E.length){const M=['<option value="">'+m(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(E.map(function(H){const j=B!=null&&Number(B)===Number(H.id);return'<option value="'+m(H.id)+'"'+(j?" selected":"")+">"+m(H.name||"#"+H.id)+"</option>"}));x='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+m(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+M.join("")+"</select></div>"}const T=!E.length&&v.emptyHint?'<div class="ws-modal-empty">'+m(v.emptyHint)+"</div>":"",S=v.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+m(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+m(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+m(a("ws-create-submit","创建"))+"</button></div></div>":"";L.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+m(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+m(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+g+x+"</div>"+T+S+"</div>",document.body.appendChild(L);const I=L.querySelector("[data-ws-select]");I&&I.addEventListener("change",function(){const M=I.value;M&&(typeof v.onPick=="function"&&v.onPick(M),k(),u())});function k(){L.remove()}L.addEventListener("click",function(M){if(M.target===L||M.target.closest("[data-ws-close]")){k();return}if(M.target.closest("[data-ws-personal]")){typeof v.onPersonal=="function"&&v.onPersonal(),k(),u();return}const j=M.target.closest("[data-ws-pick]");if(j){const F=j.getAttribute("data-ws-pick");typeof v.onPick=="function"&&v.onPick(F),k(),u();return}if(M.target.closest("[data-ws-create-toggle]")){const F=L.querySelector("[data-ws-create-form]");if(F){F.style.display=F.style.display==="none"?"flex":"none";const W=F.querySelector("[data-ws-create-name]");W&&W.focus()}return}if(M.target.closest("[data-ws-create-submit]")){w(L,v,k);return}})}async function w(v,E,B){const C=v.querySelector("[data-ws-create-name]"),L=C?(C.value||"").trim():"";if(!L){C&&C.focus();return}let y=null;try{if(typeof window.apiPost=="function"){const x=await window.apiPost("/api/workspace/clients",{name:L});y=x&&typeof x.json=="function"?await x.json().catch(()=>null):x}}catch{y=null}const g=y&&(y.id||y.client&&y.client.id);if(!g){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await p(),d(Number(g)),E.onPick,B(),u()}window.openWorkspaceChooserUI=_,window.addEventListener("pearnly:workspace-changed",function(){u()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=d,window.enterPersonalMode=l,window.requireWorkspace=f,window.openWorkspaceChooser=c,window.renderWorkspaceControl=u,window.fetchWorkspaceClients=p;function b(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){c(null)},800)}catch{}}p().then(v=>{window._workspaceClientsCache=v,u(),b()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",u)})();(function(){const e=B=>document.querySelector('[data-num-target="'+B+'"]');function n(B){if(!B)return t("reconcile-last-activity-none");try{const C=new Date(B),L=new Date,y=L-C;if(y/6e4<5)return t("reconcile-last-activity-just-now");if(C.toDateString()===L.toDateString())return t("reconcile-last-activity-today");const x=Math.max(1,Math.floor(y/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",x)}catch{return t("reconcile-last-activity-none")}}function a(B,C,L){const y=e(B);y&&(y.textContent=L?"-":String(C),y.classList.toggle("is-empty",!!L))}function o(B){const C=document.getElementById("reconcile-error");C&&(C.style.display=B?"flex":"none")}function s(B){const C=document.getElementById("reconcile-empty");C&&(C.style.display=B?"flex":"none")}function i(B,C){const L=document.getElementById("reconcile-last-activity");L&&(L.textContent=B,L.classList.toggle("has-data",!!C))}function r(B){const C=!B||(B.total_sessions||0)===0;a("pending",B.pending||0,C),a("matched",B.matched||0,C),a("unmatched",B.unmatched||0,C),i(n(B.last_activity_at),!!B.last_activity_at),o(!1),s(C)}function d(B){const C=B.toUpperCase();return C==="KBANK"?"bank-chip-kbank":C==="SCB"?"bank-chip-scb":C==="BBL"?"bank-chip-bbl":C==="KTB"?"bank-chip-ktb":C==="TTB"?"bank-chip-ttb":"bank-chip-other"}function l(B,C){const L=y=>y?String(y).slice(0,10):"?";return!B&&!C?"":L(B)+" ~ "+L(C)}function p(B){return B==null?"":String(B).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function f(B){const C=document.getElementById("reconcile-recent"),L=document.getElementById("reconcile-recent-list");if(!C||!L)return;const y=(B||[]).slice(0,20);if(y.length===0){C.style.display="none";return}C.style.display="",s(!1),L.innerHTML=y.map(g=>{const x=g.parse_status==="parse_failed",T=g.bank_code||"OTHER",S=g.account_last4?" ···"+p(g.account_last4):"",I=l(g.period_start,g.period_end),k=p(g.source_filename||""),M=Number(g.tx_count||0),H=x?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",M)+"</span>";return'<div class="recon-card" data-session-id="'+p(g.id)+'" data-session-name="'+k+'"><span class="bank-chip '+d(T)+'">'+p(T)+'</span><div class="recon-card-main"><div class="recon-card-title">'+k+S+'</div><div class="recon-card-sub">'+p(I)+'</div></div><div class="recon-card-right">'+H+'</div><button class="recon-card-trash" data-trash="'+p(g.id)+'" title="'+p(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),L.querySelectorAll(".recon-card").forEach(g=>{g.addEventListener("click",x=>{x.target.closest(".recon-card-trash")||(g.dataset.sessionId,c())})}),L.querySelectorAll(".recon-card-trash").forEach(g=>{g.addEventListener("click",x=>{x.stopPropagation();const T=g.dataset.trash,S=g.closest(".recon-card"),I=S&&S.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(T,I)})})}function c(B){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const C=document.querySelector('[data-recon-tab="bank"]');C&&C.click()},150)}function u(){o(!0),s(!1)}function m(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const B=document.querySelector('[data-recon-tab="bank"]');B&&B.click()},150)}async function h(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),o(!1),s(!1);const B=document.getElementById("reconcile-recent");B&&(B.style.display="none");const C={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[L,y]=await Promise.all([fetch("/api/bank-recon/stats",{headers:C}),fetch("/api/bank-recon/sessions?limit=20",{headers:C})]);if(!L.ok)throw new Error("http "+L.status);const g=await L.json(),x=y.ok?await y.json():[];r(g||{}),f(x||[])}catch(L){console.warn("[reconcile] load failed",L),u()}}function _(B){if(!B||!B.length)return;const C="Bearer "+(localStorage.getItem("mrpilot_token")||"");let L=0;const y=B.length;Array.from(B).forEach(function(g){const x=new FormData;x.append("file",g,g.name);const T=new XMLHttpRequest;T.open("POST","/api/bank-recon/upload"),T.setRequestHeader("Authorization",C),T.onload=function(){L++;try{const S=JSON.parse(T.responseText);T.status===200&&S.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",S.tx_count),"success"):showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error")}L===y&&setTimeout(h,600)},T.onerror=function(){L++,showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error"),L===y&&setTimeout(h,600)},T.send(x)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function w(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const B=document.getElementById("reconcile-bank-file-input");B&&B.addEventListener("change",function(){_(this.files),this.value=""}),document.addEventListener("click",C=>{if(C.target.closest("#btn-reconcile-upload-top")||C.target.closest("#btn-reconcile-upload-empty")){m();return}if(C.target.closest("#btn-reconcile-retry")){h();return}if(C.target.closest("#btn-reconcile-dev-seed")){E();return}})}const b=["468b50c1-5593-4fd6-990d-515ce8085563"];function v(){const B=document.getElementById("btn-reconcile-dev-seed");if(!B)return;const C=typeof _userInfo<"u"?_userInfo:null,L=C&&C.id&&b.indexOf(String(C.id))>=0;B.style.display=L?"":"none"}async function E(){try{const B=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!B.ok)throw new Error("seed:"+B.status);const C=await B.json(),L=(t("reconcile-dev-seed-ok")||"").replace("{n}",C.tx_count||0);showToast(L,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const y=document.querySelector('[data-auto-tab="bank"]');y&&y.click(),C.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(C.session_id)},300)}catch(B){console.warn("[reconcile] dev seed failed",B),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){w(),v(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await h()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&h().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const h=a();if(h){if(!e.clients.length){h.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}h.innerHTML=e.clients.map(_=>{const w=String(_.id),b=e.selected.has(w)?"checked":"",v=escapeHtml(_.name||_.label||"#"+w),E=_.code?'<span class="assign-row-code">'+escapeHtml(_.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(w)+'" '+b+'><span class="assign-row-name">'+v+"</span>"+E+"</label>"}).join(""),d()}}function d(){const h=s();if(h){const w=t("assign-selected-count")||"已选 {n} / {total}";h.textContent=w.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const _=o();_&&(_.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function l(){const h=i();h&&(h.textContent=e.employeeName?" · "+e.employeeName:"")}async function p(h,_){e.employeeId=h,e.employeeName=_||"",e.opened=!0,e.selected=new Set,e.clients=[],l();const w=a();w&&(w.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const b=n();b&&(b.style.display="flex");try{const[v,E]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(h)+"/assignments")]);e.clients=v&&v.clients||[];const B=E&&E.client_ids||[];e.selected=new Set(B.map(String)),r()}catch(v){console.error("[assign-clients] load failed",v);const E=a();E&&(E.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function f(){e.opened=!1;const h=n();h&&(h.style.display="none")}async function c(){if(!e.employeeId)return;const h=Array.from(e.selected).map(w=>parseInt(w,10)).filter(w=>!isNaN(w)),_=document.getElementById("assign-modal-save");_&&(_.disabled=!0);try{const w=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:h});w&&w.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",h.length),"success"),f(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(w){console.error("[assign-clients] save failed",w),showToast(t("assign-save-failed")||"保存失败","error")}finally{_&&(_.disabled=!1)}}function u(){const h=n();if(!h||h.dataset.bound==="1")return;h.dataset.bound="1";const _=document.getElementById("assign-modal-close");_&&_.addEventListener("click",f);const w=document.getElementById("assign-modal-cancel");w&&w.addEventListener("click",f);const b=document.getElementById("assign-modal-save");b&&b.addEventListener("click",c),h.addEventListener("click",function(B){B.target===h&&f()});const v=o();v&&v.addEventListener("change",function(){v.checked?e.selected=new Set(e.clients.map(B=>String(B.id))):e.selected=new Set,r()});const E=a();E&&E.addEventListener("change",function(B){const C=B.target.closest('input[type="checkbox"][data-cid]');if(!C)return;const L=C.dataset.cid;C.checked?e.selected.add(L):e.selected.delete(L),d()})}function m(){e.opened&&(l(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",m),window.openAssignClientsModal=function(h,_){u(),p(h,_)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(f){if(!f)return"";try{return new Date(f).toLocaleString()}catch{return f}}function a(f){const c=document.getElementById("access-log-table");c&&(c.innerHTML='<div class="access-log-empty">'+escapeHtml(f)+"</div>");const u=document.getElementById("access-log-pager");u&&(u.innerHTML="")}function o(){const f=document.getElementById("access-log-table");if(!f)return;const c=e.rows||[];if(!c.length){a(t("set-access-log-empty"));return}const u=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,m=c.map(function(h){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(h.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(h.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(h.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(h.target_name||h.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(h.ip||"-")}</div>
                </div>`}).join("");f.innerHTML=u+m}function s(){const f=document.getElementById("access-log-pager");if(!f)return;const c=e.total||0;if(!c){f.innerHTML="";return}const u=e.page||1,m=e.per_page,h=Math.max(1,Math.ceil(c/m)),_=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",c),w=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",u).replace("{t}",h);f.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(_)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u-1}" ${u<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(w)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u+1}" ${u>=h?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(f){const c=localStorage.getItem("mrpilot_token");if(c){e.page=f||1,a(t("set-access-log-loading"));try{const u="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),m=await fetch(u,{headers:{Authorization:"Bearer "+c}});if(m.status===403){a(t("set-access-log-empty"));return}if(!m.ok)throw new Error("http_"+m.status);const h=await m.json();e.rows=h.logs||[],e.total=h.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const f=localStorage.getItem("mrpilot_token");if(f)try{const c="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),u=await fetch(c,{headers:{Authorization:"Bearer "+f}});if(!u.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const m=await u.blob(),h=document.createElement("a"),_=URL.createObjectURL(m);h.href=_,h.download="pearnly_access_log.csv",document.body.appendChild(h),h.click(),setTimeout(function(){URL.revokeObjectURL(_),h.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function d(){const f=document.querySelectorAll(".set-tab-owner-only"),c=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));f.forEach(function(u){u.style.display=c?"":"none"})}document.addEventListener("click",function(f){if(f.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(f.target.closest("#access-log-csv-btn")){f.preventDefault(),r();return}const m=f.target.closest(".access-log-pager-btn[data-access-log-page]");if(m&&!m.disabled){const h=parseInt(m.dataset.accessLogPage,10);i(h)}}),document.addEventListener("input",function(f){f.target&&f.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(f.target.value||"").trim(),i(1)},350))});let l=0;const p=setInterval(function(){l++,_userInfo&&(d(),clearInterval(p)),l>60&&clearInterval(p)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){d(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=L=>document.getElementById(L);async function n(L,y){return await fetch(L,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(y||{})})}async function a(L){return await fetch(L,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function i(L,y){if(!L)return;L.style.display="",L.className="notif-line-check "+(y?"bound":"unbound");const g=y?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';L.innerHTML=g+"<span>"+escapeHtml(t(y?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(L){if(L==null)return"-";const y=Number(L);return isNaN(y)?String(L):"฿ "+y.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function d(L){if(!L)return"-";try{const y=new Date(L),g=(y.getMonth()+1).toString().padStart(2,"0"),x=y.getDate().toString().padStart(2,"0"),T=y.getHours().toString().padStart(2,"0"),S=y.getMinutes().toString().padStart(2,"0");return`${g}-${x} ${T}:${S}`}catch{return L}}function l(L){const y=e("notif-rules-list"),g=e("notif-rules-empty"),x=e("notif-rules-count");if(!(!y||!g)){if(x.textContent=String(L.length),x.className="auto-status-pill "+(L.length>0?"active":"none"),!L.length){g.style.display="",y.style.display="none",y.innerHTML="";return}g.style.display="none",y.style.display="",y.innerHTML=L.map(T=>{const S=T.template_code==="large_invoice",I=S?"notif-rule-large-tag":"notif-rule-exception-tag",k=S?"large":"";let M=[];if(S){const j=T.params&&T.params.threshold?r(T.params.threshold):"-";M.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+j)}T.enabled||M.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const H=M.length?M.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${T.enabled?"":" disabled"}" data-rule-id="${T.id}">
                    <span class="notif-rule-tmpl-badge ${k}">${escapeHtml(t(I))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(T.name)}</div>
                        <div class="notif-rule-meta">${H}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${T.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function p(L){const y=e("notif-logs-list");if(y){if(!L.length){y.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}y.innerHTML=L.map(g=>{const x=g.status==="sent",T=g.event_type==="exception_high"?"notif-event-exception-high":g.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",S=x?"":" · "+escapeHtml(g.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${x?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(T))}</div>
                        <div class="notif-log-meta">${escapeHtml(g.template_code||"-")}${S}</div>
                    </div>
                    <div class="notif-log-time">${d(g.sent_at)}</div>
                </div>`}).join("")}}async function f(){try{const L=await apiGet("/api/notifications/rules");c=L&&L.items||[],l(c)}catch(L){console.warn("load rules fail",L)}try{const L=await apiGet("/api/notifications/logs?limit=20");u=L&&L.items||[],p(u)}catch(L){console.warn("load logs fail",L)}}let c=null,u=null;function m(){c&&l(c),u&&p(u);const L=e("notif-new-modal");L&&L.style.display!=="none"&&o&&i(e("notif-line-check"),!!(o&&o.bound))}function h(){const L=e("notif-new-modal");L&&(L.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(y=>y.checked=!1),s().then(y=>i(e("notif-line-check"),!!(y&&y.bound))))}function _(){const L=e("notif-new-modal");L&&(L.style.display="none")}function w(){const L=document.querySelector('input[name="notif-template"]:checked'),y=e("notif-new-threshold-row");if(!L){y.style.display="none";return}y.style.display=L.value==="large_invoice"?"":"none";const g=e("notif-new-name");g&&!g.value.trim()&&(g.value=L.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function b(){const L=document.querySelector('input[name="notif-template"]:checked');if(!L){showToast(t("notif-new-template"),"error");return}const y=(e("notif-new-name").value||"").trim();if(!y){showToast(t("notif-name-required"),"error");return}const g={name:y,template_code:L.value,params:{},enabled:!0};if(L.value==="large_invoice"){const x=parseFloat(e("notif-new-threshold").value||"0");if(!x||x<=0){showToast(t("notif-threshold-required"),"error");return}g.params.threshold=x}try{const x=await apiPost("/api/notifications/rules",g);if(x&&x.ok)showToast(t("notif-toast-created"),"success"),_(),f();else{const T=await(x&&x.json&&x.json().catch(()=>({})))||{};showToast(T&&T.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function v(L,y,g){if(L==="toggle"){const x=g.classList.contains("on"),T=await n("/api/notifications/rules/"+y,{enabled:!x});T&&T.ok?(showToast(t(x?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),f()):showToast("toggle failed","error");return}if(L==="test"){const x=await s();if(!x||!x.bound){showToast(t("notif-line-error-bind-first"),"error");return}const T=await apiPost("/api/notifications/rules/"+y+"/test",{});if(T&&T.ok)showToast(t("notif-toast-test-sent"),"success"),f();else{const S=await(T&&T.json&&T.json().catch(()=>({})))||{},I=S&&S.detail||"";showToast(I||t("notif-toast-test-failed"),"error"),f()}return}if(L==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const T=await a("/api/notifications/rules/"+y);T&&T.ok?(showToast(t("notif-toast-deleted"),"success"),f()):showToast("delete failed","error");return}}let E=!1;function B(){if(E)return;E=!0;const L=e("notif-btn-new");L&&L.addEventListener("click",h);const y=e("notif-btn-refresh-logs");y&&y.addEventListener("click",f);const g=e("notif-new-close");g&&g.addEventListener("click",_);const x=e("notif-new-cancel");x&&x.addEventListener("click",_);const T=e("notif-new-save");T&&T.addEventListener("click",b),document.querySelectorAll('input[name="notif-template"]').forEach(k=>{k.addEventListener("change",w)});const S=e("notif-rules-list");S&&S.addEventListener("click",k=>{const M=k.target.closest("button[data-action]");if(!M)return;const H=M.closest("[data-rule-id]");H&&v(M.getAttribute("data-action"),H.getAttribute("data-rule-id"),M)});const I=e("notif-new-modal");I&&I.addEventListener("click",k=>{k.target===I&&_()})}async function C(){B(),await f()}window._loadNotificationsPanel=C,window._rerenderNotifications=m})();(function(){function n(b,v){try{return window.t&&window.t(b)||v}catch{return v}}function a(){var b="";try{b=localStorage.getItem("mrpilot_token")||""}catch{}return b?{Authorization:"Bearer "+b}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var b=document.createElement("style");b.id="recon-batch-style",b.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(b)}}function i(b){return b?b.dataset&&b.dataset.taskId?b.dataset.taskId:b.dataset&&b.dataset.taskid?b.dataset.taskid:"":""}function r(b){var v=document.getElementById(b.tbody);if(!v)return null;var E=v.closest("table");if(!E)return null;var B=E.querySelector("thead");if(!B)return null;if(B._reconReady)return B;var C=B.querySelector("tr");if(!C)return null;if(C.classList.add("recon-thead-default"),!C.querySelector(".recon-master-cb")){var L=document.createElement("th");L.className="recon-sel-cell";var y=document.createElement("input");y.type="checkbox",y.className="recon-master-cb",y.setAttribute("aria-label","select all"),y.addEventListener("change",function(){f(b,y.checked)}),L.appendChild(y),C.insertBefore(L,C.firstElementChild)}var g=C.children[1];g&&!g.classList.contains("recon-time-col")&&g.classList.add("recon-time-col");var x=C.children.length,T=document.createElement("tr");T.className="recon-thead-batch";var S=document.createElement("th");S.className="recon-sel-cell";var I=document.createElement("input");I.type="checkbox",I.className="recon-master-cb",I.checked=!0,I.setAttribute("aria-label","select all"),I.addEventListener("change",function(){f(b,I.checked)}),S.appendChild(I);var k=document.createElement("th");return k.setAttribute("colspan",String(x-1)),k.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',T.appendChild(S),T.appendChild(k),B.appendChild(T),k.querySelector("[data-recon-del]").addEventListener("click",function(){h(b)}),k.querySelector("[data-recon-clear]").addEventListener("click",function(){m(b)}),B._reconReady=!0,u(b),B}function d(b){var v=document.getElementById(b.tbody);if(v){var E=v.querySelectorAll("tr");E.forEach(function(B){var C=i(B);if(C&&!B.querySelector(".recon-sel-cb")){var L=B.querySelector("td");if(L){var y=document.createElement("td");y.className="recon-sel-cell";var g=document.createElement("input");g.type="checkbox",g.className="recon-sel-cb",g.dataset.taskId=C,g.dataset.kind=b.kind,g.addEventListener("click",function(T){T.stopPropagation()}),g.addEventListener("change",function(){c(b)}),y.appendChild(g),B.insertBefore(y,L);var x=B.children[1];x&&!x.classList.contains("recon-time-col")&&x.classList.add("recon-time-col")}}}),c(b)}}function l(b){var v=document.getElementById(b.tbody);return v?Array.prototype.slice.call(v.querySelectorAll(".recon-sel-cb")):[]}function p(b){return l(b).filter(function(v){return v.checked}).map(function(v){return v.dataset.taskId})}function f(b,v){l(b).forEach(function(E){E.checked=!!v}),c(b)}function c(b){var v=p(b),E=l(b),B=document.getElementById(b.tbody);if(B){var C=B.closest("table"),L=C&&C.querySelector("thead");if(L){v.length>0?L.classList.add("recon-batch-mode"):L.classList.remove("recon-batch-mode"),L.querySelectorAll(".recon-master-cb").forEach(function(g){if(E.length===0){g.checked=!1,g.indeterminate=!1;return}v.length===E.length?(g.checked=!0,g.indeterminate=!1):v.length===0?(g.checked=!1,g.indeterminate=!1):(g.checked=!1,g.indeterminate=!0)});var y=L.querySelector("[data-recon-count]");y&&(y.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",v.length))}}}function u(b){var v=document.getElementById(b.tbody);if(v){var E=v.closest("table"),B=E&&E.querySelector("thead");if(B){var C=B.querySelector("[data-recon-del-label]"),L=B.querySelector("[data-recon-clear]");C&&(C.textContent=n("recon-batch-delete","批量删除")),L&&(L.textContent=n("recon-batch-clear","取消")),c(b)}}}function m(b){l(b).forEach(function(v){v.checked=!1}),c(b)}async function h(b){var v=p(b);if(v.length){var E=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",v.length),B=!1;try{typeof window.pearnlyConfirm=="function"?B=await window.pearnlyConfirm(E,n("recon-batch-delete-title","批量删除")):B=window.confirm(E)}catch{B=!1}if(B)try{var C=Object.assign({"Content-Type":"application/json"},a()),L=b.kind==="glv"?v.map(function(T){return parseInt(T,10)}):v,y=await fetch(b.api,{method:"POST",headers:C,body:JSON.stringify({ids:L})});if(!y.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var g=await y.json(),x=g&&(g.deleted!=null?g.deleted:g.count)||v.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",x),"success"),b.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function _(b){r(b),d(b);var v=document.getElementById(b.tbody);if(!(!v||v._reconBatchWatched)){v._reconBatchWatched=!0;var E=new MutationObserver(function(){d(b)});E.observe(v,{childList:!0,subtree:!1})}}function w(){s(),o.forEach(_),document.querySelectorAll(".recon-batch-bar").forEach(function(b){try{b.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",w):w(),setTimeout(w,1500),setTimeout(w,4e3),document.addEventListener("keydown",function(b){b.key==="Escape"&&o.forEach(function(v){p(v).length>0&&m(v)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(u)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(p){};function i(p){n=p;for(let u=1;u<=a;u++){const m=document.getElementById("ob-step-"+u);m&&(m.style.display=u===p?"block":"none")}document.querySelectorAll(".ob-dot").forEach(u=>{const m=parseInt(u.dataset.step,10);u.classList.toggle("active",m===p),u.classList.toggle("done",m<p)});const f=document.getElementById("ob-step-label");f&&(f.textContent=p+" / "+a);const c=document.getElementById("ob-next");if(c&&(c.textContent=p===a?t("ob-finish"):t("ob-next")),p===4){const u=document.getElementById("ob-line-input");u&&(u.value=e.line_id||"")}}function r(p){const f=document.querySelector(".onboarding-modal");if(!f)return;let c=f.querySelector(".ob-feedback");c||(c=document.createElement("div"),c.className="ob-feedback",f.appendChild(c)),c.textContent=p,c.classList.add("show"),setTimeout(()=>c.classList.remove("show"),1800)}document.addEventListener("click",p=>{const f=p.target.closest(".ob-option");if(!f)return;const c=f.parentElement;if(!c||!c.classList.contains("ob-options"))return;c.querySelectorAll(".ob-option").forEach(m=>m.classList.remove("selected")),f.classList.add("selected");const u=f.dataset.value;c.id==="ob-role-options"?e.role=u:c.id==="ob-volume-options"?e.monthly_volume=u:c.id==="ob-country-options"&&(e.country=u)}),document.addEventListener("click",p=>{p.target.id==="ob-skip"&&d()}),document.addEventListener("click",p=>{if(p.target.id==="ob-next"){if(n===4){const f=document.getElementById("ob-line-input");e.line_id=(f&&f.value||"").trim().replace(/^@+/,"")}d()}}),document.addEventListener("click",p=>{if(p.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const f=document.getElementById("onboarding-modal");f&&(f.style.display="none")}});function d(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):l()}async function l(){const p=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const f={};if(e.role&&(f.role=e.role),e.monthly_volume&&(f.monthly_volume=e.monthly_volume),e.country&&(f.country=e.country),e.line_id&&(f.line_id=e.line_id),Object.keys(f).length===0){p&&(p.style.display="none");return}try{const c=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(f)});c.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,f),setTimeout(()=>{p&&(p.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(f)),console.warn("onboarding profile save failed",c.status),r(t("ob-fb-saved-local")),setTimeout(()=>{p&&(p.style.display="none")},1500))}catch(c){console.error("onboarding submit",c),localStorage.setItem("pilot_ob_pending",JSON.stringify(f)),p&&(p.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function d(){return"DHL Express (Thailand) Co., Ltd."}function l(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:d(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>p(),window.loadPrefsSettings=()=>f(),window.loadArchiveSettings=()=>u();function p(){const y=document.getElementById("settings-contact-grid");if(!y)return;const g=_contact?.phone||"086-889-2228",x=_contact?.line_id||"@Pearnly",T=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",S=_contact?.email||"hello@pearnly.com",I=_contact?.address||"Bangkok, Thailand";y.innerHTML=`
            <a class="contact-item" href="${escapeHtml(T)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(x)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(S)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(S)}</div>
                </div>
            </a>
            <a class="contact-item" href="tel:${escapeHtml(g.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(g)}</div>
                </div>
            </a>
            <div class="contact-item">
                <div class="contact-icon address">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s-7-7.5-7-13a7 7 0 1114 0c0 5.5-7 13-7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-address"))}</div>
                    <div class="contact-value">${escapeHtml(I)}</div>
                </div>
            </div>
        `}async function f(){try{const y=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!y.ok)return;const g=await y.json(),x=document.getElementById("pref-dup-check");x&&(x.checked=!!g.enabled)}catch(y){console.warn("load prefs failed",y)}}const c=document.getElementById("pref-dup-check");c&&!c.dataset.bound&&(c.dataset.bound="1",c.addEventListener("change",async y=>{const g=y.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:g})})).ok?showToast(g?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(y.target.checked=!g,showToast(t("pref-save-failed"),"error"))}catch{y.target.checked=!g,showToast(t("pref-save-failed"),"error")}}));async function u(){const y=!!(_userInfo&&_userInfo.can_customize_archive);o=!y;const g=document.getElementById("archive-upgrade-banner");g&&(g.style.display=y?"none":"");const x=document.getElementById("archive-plus-badge");x&&(x.style.display=y?"none":"");try{const T=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!T.ok)throw new Error("load failed");const S=await T.json();e=Array.isArray(S.name_template)?S.name_template:[],n=S.folder_strategy||"by_month_seller"}catch(T){console.error("load archive settings failed",T),showToast(t("archive-load-failed"),"error");return}m(),h(),_(),w()}function m(){const y=document.getElementById("archive-rule-canvas");if(y){if(e.length===0){y.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}y.innerHTML=e.map((g,x)=>{const T=i[g.type]||{label:g.type},S=s[g.type]||"",I=g.type==="sep"?`"${escapeHtml(g.val||"_")}"`:escapeHtml(t(T.label));return`
                <span class="archive-token ${g.type}"
                      data-token-idx="${x}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${S}</span>
                    <span class="token-label">${I}</span>
                </span>
            `}).join("")}}function h(){const y=document.getElementById("archive-field-palette");if(!y)return;const g=["date","seller","category","amount","invoice","buyer","sep"];y.innerHTML=g.map(x=>{const T=i[x],S=s[x]||"";return`
                <button class="archive-palette-btn ${x}" data-add-field="${x}" ${o?"disabled":""}>
                    <span class="token-icon">${S}</span>
                    <span>${escapeHtml(t(T.label))}</span>
                </button>
            `}).join("")}function _(){document.querySelectorAll('input[name="folder-strategy"]').forEach(y=>{y.checked=y.value===n,y.disabled=o})}async function w(){const y=document.getElementById("archive-preview-name"),g=document.getElementById("archive-preview-hint");if(g&&(g.textContent=t("archive-preview-hint",{category:r()})),!!y){if(e.length===0){y.textContent="-";return}try{const T=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:l().merged_fields,name_template:e})})).json();y.textContent=(T.name||"-")+".pdf"}catch{y.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const y=document.getElementById("archive-rule-modal");!y||y.style.display==="none"||(m(),h(),w())};let b=-1;document.addEventListener("dragstart",y=>{const g=y.target.closest(".archive-token");!g||o||(b=parseInt(g.dataset.tokenIdx,10),g.classList.add("dragging"),y.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",y=>{document.querySelectorAll(".archive-token").forEach(g=>g.classList.remove("dragging","drop-target")),b=-1}),document.addEventListener("dragover",y=>{const g=y.target.closest(".archive-token");g&&(y.preventDefault(),y.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(x=>x.classList.remove("drop-target")),g.classList.add("drop-target"))}),document.addEventListener("drop",y=>{const g=y.target.closest(".archive-token");if(!g||b<0||o)return;y.preventDefault();const x=parseInt(g.dataset.tokenIdx,10);if(x===b)return;const T=e.splice(b,1)[0];e.splice(x,0,T),b=-1,m(),w()}),document.addEventListener("click",y=>{if(y.target.closest("#btn-open-archive-rule")||y.target.closest("#btn-open-archive-rule-from-settings")){const S=document.getElementById("archive-rule-modal");S&&(S.style.display="",u());return}if(y.target.closest("#archive-rule-modal-close")||y.target.id==="archive-rule-modal"){const S=document.getElementById("archive-rule-modal");S&&(S.style.display="none");return}const g=y.target.closest(".settings-nav-item");if(g){switchSettingsTab(g.dataset.settingsTab);return}if(o&&y.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const x=y.target.closest("[data-add-field]");if(x){const S=x.dataset.addField,I=i[S],k={type:S,...I.defaultCfg};e.push(k),m(),w();return}const T=y.target.closest(".archive-token");if(T&&!o){v(parseInt(T.dataset.tokenIdx,10));return}if(y.target.closest("#btn-archive-save"))return C();if(y.target.closest("#btn-archive-reset"))return L();(y.target.closest("#archive-token-close")||y.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),y.target.closest("#btn-archive-token-ok")&&E(),y.target.closest("#btn-archive-token-delete")&&B()}),document.addEventListener("change",y=>{y.target.name==="folder-strategy"&&(n=y.target.value)});function v(y){a=y;const g=e[y];if(!g)return;const x=document.getElementById("archive-token-body");let T="";g.type==="date"?T=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${g.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${g.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${g.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${g.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:g.type==="seller"?T=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${g.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:g.type==="amount"?T=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${g.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:g.type==="sep"?T=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${g.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${g.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${g.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(g.val)?"":escapeHtml(g.val||"")}">
                    </div>
                </div>`:T=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,x.innerHTML=T,document.getElementById("archive-token-modal").style.display="",x.querySelectorAll(".sep-chip").forEach(S=>{S.addEventListener("click",()=>{x.querySelectorAll(".sep-chip").forEach(k=>k.classList.remove("active")),S.classList.add("active");const I=document.getElementById("token-sep-custom");I&&(I.value="")})})}function E(){const y=e[a];if(y){if(y.type==="date")y.format=document.getElementById("token-date-format").value;else if(y.type==="seller")y.short=document.getElementById("token-seller-short").checked;else if(y.type==="amount")y.with_currency=document.getElementById("token-amount-currency").checked;else if(y.type==="sep"){const g=document.querySelector("#archive-token-body .sep-chip.active"),x=document.getElementById("token-sep-custom").value;y.val=x||(g?g.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",m(),w()}}function B(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",m(),w())}async function C(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const g=document.getElementById("archive-rule-modal");g&&(g.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function L(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",m(),_(),w())}})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,i=null,r=0,d=0,l=!1;function p(v){const E=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return v.preventDefault(),v.returnValue=E,E}function f(){l||(l=!0,window.addEventListener("beforeunload",p))}function c(){l&&(l=!1,window.removeEventListener("beforeunload",p))}function u(){if(document.getElementById("big-batch-progress"))return;const v=document.getElementById("file-list");if(!v||!v.parentNode)return;const E=document.createElement("div");E.id="big-batch-progress",E.className="big-batch-progress",E.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',v.parentNode.insertBefore(E,v);const B=document.getElementById("bbp-text");B&&(B.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function m(){const v=document.getElementById("big-batch-progress");v&&v.remove()}function h(){if(!i)return;let v=0;for(let T=0;T<i.length;T++){const S=i[T].status;(S==="success"||S==="error"||S==="cancelled")&&v++}const E=r,B=E>0?Math.min(100,Math.floor(100*v/E)):0,C=(Date.now()-d)/1e3;let L;if(v>=3&&C>1){const T=C/v;L=(E-v)*T}else L=(E-v)*6/6;const y=Math.max(1,Math.ceil(L/60)),g=document.getElementById("bbp-fill"),x=document.getElementById("bbp-text");g&&(g.style.width=B+"%"),x&&(v>=E?x.textContent=t("big-batch-progress-done").replace("{total}",E):x.textContent=t("big-batch-progress-running").replace("{done}",v).replace("{total}",E).replace("{min}",y))}function _(v){try{if(localStorage.getItem(o)==="1")return}catch{}const E=Math.max(1,Math.ceil(v*6/6/60)),B=t("big-batch-first-tip").replace("{n}",v).replace("{min}",E);typeof showToast=="function"&&showToast(B,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function w(v){!v||v.length<100||(i=v,r=v.length,d=Date.now(),u(),f(),_(r),s&&clearInterval(s),s=setInterval(h,250),h())}function b(){s&&(clearInterval(s),s=null),c(),i&&r>=100?(h(),setTimeout(m,1200)):m(),i=null,r=0}window._bigBatchStart=w,window._bigBatchStop=b,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&h()})})();(function(){let e=null,n=!1,a=!1;function o(g){return typeof escapeHtml=="function"?escapeHtml(g==null?"":String(g)):String(g??"")}function s(g,x){try{typeof showToast=="function"&&showToast(g,x||"info")}catch{}}function i(){const g=typeof _userInfo<"u"?_userInfo:null;return!!(g&&(g.role==="owner"||g.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function d(g){if(!g)return!1;const x=String(g.status||"").toLowerCase();return x==="exception"||x==="exception_pending"||x==="rejected"}async function l(g){if(n&&!g)return e;const x=localStorage.getItem("mrpilot_token");if(!x)return null;try{const T=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+x}});if(!T.ok)throw new Error("http_"+T.status);e=await T.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function p(){const g=document.getElementById("erp-connect-cards");if(!g)return;const x=e;let T,S=!1;x?x.configured?x.connected?(S=!0,T='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):T='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":T='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":T='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let I="";if(!x||!x.configured)I='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!x.connected)i()&&(I='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const G=!!x.auto_push,A=G?t("card-btn-disable"):t("card-btn-enable");I='<button type="button" class="'+(G?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(G?"1":"0")+'" title="'+o(G?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(A)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const k=x&&x.connected?"xero-card-desc-connected":"xero-card-desc-default",M=x&&x.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",H=(function(){const G=t(k);return G===k?M:G})();let j='<div class="integration-row erp-connect-xero'+(S?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+T+'</div><div class="int-desc">'+o(H)+'</div></div><div class="int-actions">'+I+"</div></div>";if(x&&x.configured&&x.connected&&i()){const G=x.organisations||[];let A="";if(G.length>0){A+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(G.length)))+"</div>",A+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",A+='<div class="erp-cc-orgs">',G.forEach(function(X){A+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(X.id)+'"'+(X.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(X.organisation_name||X.organisation_id)+"</span></label>"}),A+="</div>";const N=!!x.auto_push,V=N?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");A+='<div class="erp-cc-auto-push" title="'+o(V)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(N?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",A+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}j+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+A+"</div>"}const $=g.querySelector(".erp-connect-xero"),q=g.querySelector("#erp-xero-details");q&&q.remove(),$?$.outerHTML=j:g.insertAdjacentHTML("afterbegin",j);const F=document.getElementById("btn-xero-edit-toggle");F&&F.addEventListener("click",function(G){G.preventDefault();const A=document.getElementById("erp-xero-details");A&&(A.style.display=A.style.display==="none"?"":"none")});const W=document.getElementById("btn-xero-toggle-enabled");W&&W.addEventListener("click",async function(G){if(G.preventDefault(),W.disabled)return;const N=!(W.getAttribute("data-xero-enabled")==="1");if(!N)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}W.disabled=!0,await m(N,null)})}async function f(){const g=localStorage.getItem("mrpilot_token");if(g)try{const x=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+g}});if(!x.ok){let S="unknown";try{S=(await x.json()).detail||"unknown"}catch{}const I=String(S).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+I)||S),"error");return}const T=await x.json();T.redirect_url&&(window.location.href=T.redirect_url)}catch(x){s(t("xero-push-fail").replace("{err}",x.message||"network"),"error")}}async function c(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const x=localStorage.getItem("mrpilot_token");try{const T=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+x}});if(!T.ok)throw new Error("http_"+T.status);await l(!0),p()}catch(T){s(t("xero-push-fail").replace("{err}",T.message),"error")}}async function u(g){const x=localStorage.getItem("mrpilot_token");try{const T=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+x,"Content-Type":"application/json"},body:JSON.stringify({token_id:g})});if(!T.ok)throw new Error("http_"+T.status);await l(!0),p()}catch(T){s(t("xero-push-fail").replace("{err}",T.message),"error")}}async function m(g,x){const T=localStorage.getItem("mrpilot_token");x&&(x.disabled=!0);try{const S=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+T,"Content-Type":"application/json"},body:JSON.stringify({on:!!g})});if(!S.ok){let I="unknown";try{I=(await S.json()).detail||"unknown"}catch{}throw new Error(I)}s(g?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await l(!0),p()}catch(S){x&&(x.checked=!g),s(t("erp-auto-push-toggle-fail").replace("{err}",S.message||"network"),"error")}finally{x&&(x.disabled=!1)}}async function h(){const g=document.getElementById("drawer-history-save");if(!g||g.querySelector("#btn-xero-push")||g.querySelector("#pn-push-wrap")||(await l(!1),g.querySelector("#pn-push-wrap"))||g.querySelector("#btn-xero-push"))return;const x=r();if(!(x&&(x._historyId||x.history_id)))return;let S=!1,I="xero-push-tip";!e||!e.configured?(S=!0,I="xero-err-not_configured"):e.connected?d(x)&&(S=!0,I="xero-push-disabled-exc"):(S=!0,I="xero-push-disabled-no-conn");const k=document.createElement("button");k.type="button",k.id="btn-xero-push",k.className="btn btn-ghost"+(S?" disabled":""),k.disabled=S,k.title=t(I)||"",k.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",k.addEventListener("click",_);const M=document.getElementById("btn-push-erp");M&&M.parentNode?M.parentNode.insertBefore(k,M.nextSibling):g.insertBefore(k,g.firstChild)}async function _(){const g=r(),x=g&&(g._historyId||g.history_id);if(!x)return;const T=document.getElementById("btn-xero-push");T&&(T.disabled=!0,T.classList.add("loading"));const S=localStorage.getItem("mrpilot_token");try{const I=await fetch("/api/erp/xero/push/"+encodeURIComponent(x),{method:"POST",headers:{Authorization:"Bearer "+S}});if(!I.ok){let k="unknown";try{k=(await I.json()).detail||"unknown"}catch{}const M=String(k).replace(/^xero\./,"").toLowerCase(),H=t("xero-"+M),j=H&&H!=="xero-"+M?H:k;s(t("xero-push-fail").replace("{err}",j),"error");return}s(t("xero-push-ok"),"success")}catch(I){s(t("xero-push-fail").replace("{err}",I.message||"network"),"error")}finally{T&&(T.disabled=!1,T.classList.remove("loading"))}}async function w(){await l(!0),p(),b()}async function b(){const g=document.getElementById("erp-global-push-mode");if(!g)return;const x=localStorage.getItem("mrpilot_token");if(x)try{const T=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+x}});if(T.ok){const S=await T.json();S.mode&&(g.value=S.mode,g.dataset.prev=S.mode)}}catch{}}async function v(g){const x=g.value,T=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+T,"Content-Type":"application/json"},body:JSON.stringify({mode:x})})).ok?(g.dataset.prev=x,s(t("pref-erp-mode-saved"),"success")):(g.value=g.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{g.value=g.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function E(){try{const g=String(window.location.hash||"");if(g.indexOf("xero=ok")>=0){const x=g.match(/n=(\d+)/),T=x?x[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",T),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),l(!0).then(p)}else g.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function B(){if(a)return;a=!0,document.addEventListener("click",function(x){if(x.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(w,50);return}if(x.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(w,80);return}if(x.target.closest("#btn-xero-connect")){x.preventDefault(),f();return}if(x.target.closest("#btn-xero-disconnect")){x.preventDefault(),c();return}}),document.addEventListener("change",function(x){x.target&&x.target.matches('input[name="xero-default-org"]')&&u(x.target.value),x.target&&x.target.id==="xero-auto-push-toggle"&&m(x.target.checked,x.target),x.target&&x.target.id==="erp-global-push-mode"&&v(x.target)});const g=function(){return document.getElementById("drawer-body")};try{const x=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&h()}),T=g();if(T)x.observe(T,{childList:!0,subtree:!0});else{const S=new MutationObserver(function(){const I=g();I&&(x.observe(I,{childList:!0,subtree:!0}),S.disconnect())});S.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(E,500)}function C(){e&&p();const g=document.getElementById("btn-xero-push");if(g){const x=g.querySelector("span");x&&(x.textContent=t("xero-push-btn"))}}B(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",C);async function L(g){const x=Date.now();for(;Date.now()-x<g;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(T=>setTimeout(T,80))}return null}async function y(){await L(5e3);const g=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),x=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');g&&x&&await w()}setTimeout(y,200)})();(function(){var e="https://www.mrerp4sme.com/dms/index.php",n=null,a=!1;function o(w){return typeof escapeHtml=="function"?escapeHtml(w==null?"":String(w)):String(w??"")}function s(w,b){try{typeof showToast=="function"&&showToast(w,b||"info")}catch{}}function i(){return localStorage.getItem("mrpilot_token")}async function r(w){var b=i();if(!b)return null;try{var v=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+b}});if(!v.ok)throw new Error("http_"+v.status);var E=await v.json(),B=E&&E.items||[];n=B.find(function(C){return C&&(C.adapter||"").toLowerCase()==="mrerp_dms"})||null,a=!0}catch{n=null,a=!1}return n}function d(){var w=document.getElementById("erp-connect-cards");if(w){var b=w.querySelector("[data-mrerp-dms-zone]");b||(b=document.createElement("div"),b.setAttribute("data-mrerp-dms-zone","1"),w.appendChild(b));var v=n,E=!!(v&&v.enabled!==!1),B;v?E?B='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("dms-card-connected"))+"</span>":B='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-disabled-pill"))+"</span>":B='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-not-connected"))+"</span>";var C;if(!v)C='<button type="button" class="int-btn-configure" id="btn-dms-connect">'+o(t("dms-card-connect"))+"</button>";else{var L=E?t("dms-card-disable"):t("dms-card-enable");C='<button type="button" class="int-btn-configure" id="btn-dms-edit">'+o(t("dms-card-edit"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-test">'+o(t("dms-card-test"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-toggle">'+o(L)+"</button>"}b.innerHTML='<div class="integration-row erp-connect-mrerp-dms'+(E?" connected":"")+'"><div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/><path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("dms-card-title"))+"</span>"+B+'</div><div class="int-desc">'+o(t("dms-card-desc"))+'</div></div><div class="int-actions">'+C+"</div></div>"}}function l(){var w=document.getElementById("dms-wizard-overlay");w&&w.remove(),document.removeEventListener("keydown",p)}function p(w){w.key==="Escape"&&l()}function f(){l();var w=n,b=w&&w.config&&w.config.booking_defaults&&w.config.booking_defaults.booking_prefix||"PN",v=function(C,L,y,g,x){return'<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">'+o(t(C))+'</span><input id="'+L+'" type="'+y+'" value="'+o(g||"")+'" placeholder="'+o(x||"")+'" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;"></label>'},E=document.createElement("div");E.id="dms-wizard-overlay",E.style.cssText="position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;",E.innerHTML='<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">'+o(t("dms-wizard-title"))+'</div><div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">'+o(t("dms-card-desc"))+"</div>"+v("dms-wizard-username","dms-w-user","text","","")+v("dms-wizard-password","dms-w-pass","password","","")+v("dms-wizard-prefix","dms-w-prefix","text",b,"PN")+'<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div><div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn btn-ghost" id="dms-w-cancel">'+o(t("dms-wizard-cancel"))+'</button><button type="button" class="btn btn-primary" id="dms-w-save">'+o(t("dms-wizard-save"))+"</button></div></div>",document.body.appendChild(E),document.addEventListener("keydown",p),E.addEventListener("click",function(C){C.target===E&&l()});var B=document.getElementById("dms-w-user");B&&B.focus()}function c(w){var b=document.getElementById("dms-w-err");b&&(b.textContent=w,b.style.display=w?"":"none")}async function u(){var w=n&&n.config&&n.config.system_url||e,b=(document.getElementById("dms-w-user")||{}).value||"",v=(document.getElementById("dms-w-pass")||{}).value||"",E=(document.getElementById("dms-w-prefix")||{}).value||"PN";if(w=w.trim(),b=b.trim(),!w||!b||!v){c(t("dms-wizard-required"));return}var B=document.getElementById("dms-w-save");B&&(B.disabled=!0,B.textContent=t("dms-wizard-saving")),c("");var C=i();try{var L=await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+C,"Content-Type":"application/json"},body:JSON.stringify({adapter:"mrerp_dms",config:{system_url:w,username:b,password:v}})}),y=await L.json().catch(function(){return{}});if(!L.ok||!y.ok){var g=y.error_friendly&&(y.error_friendly[window.currentLang]||y.error_friendly.en)||t("dms-connect-fail-generic");c(g),B&&(B.disabled=!1,B.textContent=t("dms-wizard-save"));return}var x={system_url:w,username_enc:b,password_enc:v,id_card_auto_push:!0,booking_defaults:{booking_prefix:E.trim()||"PN"}},T,S;n&&n.id?(T="PATCH",S="/api/erp/endpoints/"+encodeURIComponent(n.id)):(T="POST",S="/api/erp/endpoints");var I=T==="POST"?{name:"MR.ERP DMS",adapter:"mrerp_dms",config:x,is_default:!1,auto_push:!1}:{config:x,auto_push:!1},k=await fetch(S,{method:T,headers:{Authorization:"Bearer "+C,"Content-Type":"application/json"},body:JSON.stringify(I)});if(!k.ok){var M=await k.json().catch(function(){return{}}),H=M&&M.detail&&(M.detail.code||M.detail)||"save_failed";c(t("dms-save-fail")+" ("+o(String(H))+")"),B&&(B.disabled=!1,B.textContent=t("dms-wizard-save"));return}l(),s(t("dms-connect-ok"),"success"),await r(!0),d(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{c(t("dms-connect-fail-generic")),B&&(B.disabled=!1,B.textContent=t("dms-wizard-save"))}}async function m(){if(!(!n||!n.id)){s(t("dms-test-running"),"info");var w=i();try{var b=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id)+"/test-connection?refresh=1",{method:"POST",headers:{Authorization:"Bearer "+w}}),v=await b.json().catch(function(){return{}});s(v&&v.ok?t("dms-test-ok"):t("dms-test-fail"),v&&v.ok?"success":"error")}catch{s(t("dms-test-fail"),"error")}}}async function h(){if(!(!n||!n.id)){var w=n.enabled===!1;if(!w)try{var b=await window.pearnlyConfirm(t("dms-confirm-disable"));if(!b)return}catch{}var v=i();try{var E=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id),{method:"PATCH",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({enabled:w})});if(!E.ok)throw new Error("http_"+E.status);s(w?t("dms-enabled-toast"):t("dms-disabled-toast"),"success"),await r(!0),d(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{s(t("dms-save-fail"),"error")}}}function _(){r().then(d)}document.addEventListener("click",function(w){if(w.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(_,60);return}if(w.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(_,90);return}if(w.target.closest("#btn-dms-connect")||w.target.closest("#btn-dms-edit")){w.preventDefault(),f();return}if(w.target.closest("#dms-w-cancel")){w.preventDefault(),l();return}if(w.target.closest("#dms-w-save")){w.preventDefault(),u();return}if(w.target.closest("#btn-dms-test")){w.preventDefault(),m();return}if(w.target.closest("#btn-dms-toggle")){w.preventDefault(),h();return}}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("mrerp-dms-adapter",d),setTimeout(function(){var w=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),b=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');w&&b&&_()},250)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const p=`
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
        </div>`,f=document.createElement("div");f.innerHTML=p,document.body.appendChild(f.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",c=>{c.target.id==="report-modal"&&a()})}function a(){const p=document.getElementById("report-modal");p&&(p.style.display="none"),o=null}let o=null;async function s(p,f){const c=p+":"+(f||"");if(e[c])return e[c];let u;try{const m=localStorage.getItem("mrpilot_token"),h=await fetch(`/api/reports/templates?lang=${encodeURIComponent(p)}`,{headers:{Authorization:"Bearer "+m}});if(!h.ok)throw new Error("templates fetch failed");u=(await h.json()).templates||[]}catch(m){console.error("fetchTemplates fail",m),u=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(u=u.filter(m=>m.code!=="erp"),f==="history-batch"){const m=u.findIndex(_=>_.code==="standard"),h=m>=0?m+1:u.length;u.splice(h,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[c]=u,u}function i(p){const f=document.getElementById("report-tpl-list"),c=p.map((m,h)=>`
            <label class="report-tpl-item${m.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${m.code}" ${m.recommended||h===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${r(m.name)}
                        ${m.recommended?`<span class="report-tpl-badge">${r(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${r(m.desc||"")}</div>
                </div>
            </label>
        `).join(""),u=`
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
        `;f.innerHTML=c+u}function r(p){return p==null?"":String(p).replace(/[&<>"']/g,f=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[f])}function d(p){const f=new Date,c=f.getFullYear(),u=f.getMonth()+1;if(p==="all")return"all";if(p==="this-month")return`${c}-${String(u).padStart(2,"0")}`;if(p==="last-month"){const m=new Date(c,u-2,1);return`${m.getFullYear()}-${String(m.getMonth()+1).padStart(2,"0")}`}return p==="this-year"?`${c}`:p==="this-quarter"?`${c}-Q${Math.floor((u-1)/3)+1}`:"all"}window.openReportModal=async function(p){p=p||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(_=>{const w=_.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][w]&&(_.textContent=I18N[currentLang][w])});const f=document.getElementById("report-period-section");f&&(f.style.display=p.mode==="client"?"":"none");const c=document.getElementById("report-tpl-list");c.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const u=await s(currentLang,p&&p.mode);i(u),o=p;const m=document.getElementById("report-modal-download"),h=m.cloneNode(!0);m.parentNode.replaceChild(h,m),h.addEventListener("click",()=>l(o))};async function l(p){if(!p)return;const f=document.querySelector('input[name="report-tpl"]:checked');if(!f){showToast(t("report-toast-no-selection"),"info");return}const c=f.value,u=document.querySelector('input[name="report-period"]:checked'),m=u?u.value:"all",h=d(m),_=document.getElementById("report-modal-download"),w=_.innerHTML;_.disabled=!0,_.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const b=localStorage.getItem("mrpilot_token");let v,E;if(p.mode==="records")v=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,records:p.records||[],meta:p.meta||{}})}),E=`mrpilot-${c}-${Date.now()}.xlsx`;else if(p.mode==="client"){const T=`/api/reports/clients/${p.clientId}/export?template=${encodeURIComponent(c)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(h)}`;v=await fetch(T,{headers:{Authorization:"Bearer "+b}}),E=`${(p.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${c}.xlsx`}else if(p.mode==="history-batch")c==="sales_detail_th"?(v=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),E=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(v=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),E=`mrpilot-batch-${c}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+p.mode);if(!v.ok){let T="HTTP "+v.status;try{const S=await v.json();S&&S.detail&&(T=S.detail)}catch(S){console.warn("[batch-export] resp.json err.detail parse failed:",S)}v.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+T,"error");return}const B=await v.blob();let C=E;const y=(v.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(y)try{C=decodeURIComponent(y[1])}catch{}const g=URL.createObjectURL(B),x=document.createElement("a");x.href=g,x.download=C,document.body.appendChild(x),x.click(),document.body.removeChild(x),URL.revokeObjectURL(g),showToast(t("report-toast-success"),"success"),a()}catch(b){console.error("doDownload fail",b),showToast(t("report-toast-fail")+" · "+(b.message||""),"error")}finally{_.disabled=!1,_.innerHTML=w}}document.addEventListener("DOMContentLoaded",()=>{const p=document.getElementById("btn-export");if(p){const c=p.cloneNode(!0);p.parentNode.replaceChild(c,p),c.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(u=>({filename:u.filename,merged_fields:u.merged_fields||{}}))})})}const f=document.getElementById("history-batch-export");f&&f.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(p,f){openReportModal({mode:"client",clientId:p,clientName:f||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,o="mrpilot_folder_watcher",s=1;let i=null,r=null,d=null,l=60,p=!1,f=!1,c=0,u=0,m=0,h=[],_=null,w=!1;function b(){return i||(i=new Promise((P,z)=>{const R=indexedDB.open(o,s);R.onupgradeneeded=Z=>{const K=Z.target.result;K.objectStoreNames.contains("handles")||K.createObjectStore("handles"),K.objectStoreNames.contains("seen")||K.createObjectStore("seen"),K.objectStoreNames.contains("config")||K.createObjectStore("config")},R.onsuccess=Z=>P(Z.target.result),R.onerror=Z=>z(Z.target.error)}),i)}function v(P,z){return b().then(R=>new Promise((Z,K)=>{const fe=R.transaction(P,"readonly").objectStore(P).get(z);fe.onsuccess=()=>Z(fe.result),fe.onerror=()=>K(fe.error)}))}function E(P,z,R){return b().then(Z=>new Promise((K,ie)=>{const fe=Z.transaction(P,"readwrite");fe.objectStore(P).put(R,z),fe.oncomplete=()=>K(),fe.onerror=()=>ie(fe.error)}))}function B(P,z){return b().then(R=>new Promise((Z,K)=>{const ie=R.transaction(P,"readwrite");ie.objectStore(P).delete(z),ie.oncomplete=()=>Z(),ie.onerror=()=>K(ie.error)}))}function C(P){return b().then(z=>new Promise((R,Z)=>{const K=z.transaction(P,"readwrite");K.objectStore(P).clear(),K.oncomplete=()=>R(),K.onerror=()=>Z(K.error)}))}async function L(P){if(!P)return!1;try{const z={mode:"read"};let R=await P.queryPermission(z);return R==="granted"?!0:(R=await P.requestPermission(z),R==="granted")}catch(z){return console.warn("[folder] permission check failed:",z),!1}}function y(P,z){const R=document.getElementById("folder-status-summary");R&&(R.setAttribute("data-i18n",P),R.textContent=t(P),R.className="auto-status-pill"+(z?" "+z:""))}function g(P){["folder-unsupported","folder-empty","folder-active"].forEach(z=>{const R=document.getElementById(z);R&&(R.style.display=z===P?"":"none")})}function x(P){if(!P)return"-";const z=P instanceof Date?P:new Date(P),R=String(z.getHours()).padStart(2,"0"),Z=String(z.getMinutes()).padStart(2,"0"),K=String(z.getSeconds()).padStart(2,"0");return`${R}:${Z}:${K}`}function T(){g("folder-active");const P=document.getElementById("folder-config-path");P&&r&&(P.textContent=r.name||"-");const z=document.getElementById("folder-interval-select");z&&(z.value=String(l)),document.getElementById("folder-stat-last").textContent=_?x(_):"-",document.getElementById("folder-stat-processed").textContent=String(c),document.getElementById("folder-stat-failed").textContent=String(u),document.getElementById("folder-stat-queue").textContent=String(m);const R=document.getElementById("btn-folder-pause"),Z=document.getElementById("btn-folder-resume");R&&(R.style.display=p?"none":""),Z&&(Z.style.display=p?"":"none"),p?y("folder-status-paused","paused"):y("folder-status-running","running");const K=document.getElementById("folder-status-text");K&&(K.setAttribute("data-i18n",p?"folder-status-paused":"folder-status-running"),K.textContent=t(p?"folder-status-paused":"folder-status-running"));const ie=document.getElementById("folder-status-pulse");ie&&(ie.className="folder-status-pulse"+(p?" paused":"")),S()}function S(){const P=document.getElementById("folder-recent-list");if(P){if(h.length===0){P.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}P.innerHTML=h.slice(0,20).map(z=>{let R;z.status==="ok"?R=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:z.status==="dup"?R=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:z.status==="skip"?R=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:R=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const Z=z.status==="fail"&&z.error?z.error:z.status==="dup"&&z.reason||z.status==="skip"&&z.reason?z.reason:"",K=Z?`<div class="folder-recent-err">${escapeHtml(Z)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${R}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(z.name)}</div>
                        ${K}
                    </div>
                    <div class="folder-recent-time">${x(z.time)}</div>
                </div>
            `}).join("")}}function I(P){h.unshift(P),h.length>50&&(h.length=50),E("config","recent_list",h).catch(()=>{})}async function k(P){const z=new FormData;z.append("file",P,P.name),z.append("source","folder");const R=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:z});if(!R.ok){let Z="http_"+R.status;try{const K=await R.json();Z=K&&K.detail?typeof K.detail=="string"?K.detail:K.detail.code||JSON.stringify(K.detail):Z}catch{}throw new Error(Z)}return await R.json()}async function M(P){try{const R=(await P.getFile()).size;return await new Promise(K=>setTimeout(K,3e3)),(await P.getFile()).size===R&&R>0}catch{return!1}}async function H(P,z,R,Z){if(Z>10)return;let K;try{K=await P.queryPermission({mode:"read"})}catch{K="denied"}if(K==="granted")for await(const ie of P.values()){const fe=z?`${z}/${ie.name}`:ie.name;if(ie.kind==="file"){if(!a.test(ie.name))continue;let be;try{be=await ie.getFile()}catch{continue}const ke=`${fe}::${be.size}::${be.lastModified}`;if(await v("seen",ke))continue;R.push({entry:ie,file:be,seenKey:ke,relPath:fe})}else if(ie.kind==="directory")try{await H(ie,fe,R,Z+1)}catch{}}}async function j(){if(!(f||p||!r)){f=!0;try{if(await r.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),X(),showToast("warn",t("folder-permission-lost"));return}_=new Date;const z=[];await H(r,"",z,0),m=z.length,T();for(const R of z){if(p)break;if(!await M(R.entry)){m=Math.max(0,m-1),T();continue}try{let K;try{K=await R.entry.getFile()}catch{K=R.file}const ie=await k(K);await E("seen",R.seenKey,{name:K.name,relPath:R.relPath,size:K.size,lastModified:K.lastModified,processed_at:Date.now()});const fe=ie.history_ids||(ie.history_id?[ie.history_id]:[]),be=ie.duplicate_warnings||[],ke=R.relPath||K.name;fe.length>0?(c+=fe.length,I({name:ke,status:"ok",time:new Date,history_id:fe[0],count:fe.length}),await E("config","processed_count",c)):be.length>0?I({name:ke,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):I({name:ke,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(K){u++,I({name:R.relPath||R.file.name,status:"fail",time:new Date,error:String(K.message||K)}),await E("config","failed_count",u)}m=Math.max(0,m-1),T()}}catch(P){console.warn("[folder] scan error:",P)}finally{f=!1,T()}}}function $(){d&&clearInterval(d),d=setInterval(j,l*1e3)}function q(){d&&(clearInterval(d),d=null)}function F(P){if(!r||p)return;const z=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return P.preventDefault(),P.returnValue=z,z}function W(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",F))}function G(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",F))}function A(){p=!1,$(),W(),T(),j()}function N(){p=!0,q(),G(),T()}function V(){p=!1,$(),W(),T(),j()}function X(){p=!0,q(),G()}async function oe(){try{const P=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await L(P)){showToast("warn",t("folder-permission-denied"));return}r=P,await E("handles","main",P),c=0,u=0,m=0,h=[],await E("config","processed_count",0),await E("config","failed_count",0),await C("seen"),A()}catch(P){P&&P.name!=="AbortError"&&console.warn("[folder] pick failed:",P)}}async function se(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(X(),r=null,c=0,u=0,m=0,h=[],await B("handles","main"),await B("config","processed_count"),await B("config","failed_count"),await C("seen"),g("folder-empty"),y("folder-status-empty",""))}async function ue(){h=[];try{await B("config","recent_list")}catch{}S()}async function D(){if(w)return;if(w=!0,!n){g("folder-unsupported"),y("folder-status-unsupported",""),ne();return}O();let P=null;try{P=await v("handles","main")}catch{}if(!P){g("folder-empty"),y("folder-status-empty","");return}if(!await L(P)){g("folder-empty"),y("folder-status-empty",""),await B("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}r=P;try{c=await v("config","processed_count")||0}catch{}try{u=await v("config","failed_count")||0}catch{}try{const R=await v("config","recent_list");Array.isArray(R)&&(h=R.map(Z=>({...Z,time:Z.time?new Date(Z.time):new Date})))}catch{}A()}function O(){const P=document.getElementById("btn-folder-pick"),z=document.getElementById("btn-folder-pause"),R=document.getElementById("btn-folder-resume"),Z=document.getElementById("btn-folder-scan-now"),K=document.getElementById("btn-folder-remove"),ie=document.getElementById("btn-folder-clear-recent"),fe=document.getElementById("folder-interval-select");P&&P.addEventListener("click",oe),z&&z.addEventListener("click",N),R&&R.addEventListener("click",V),Z&&Z.addEventListener("click",()=>{j()}),K&&K.addEventListener("click",se),ie&&ie.addEventListener("click",ue),fe&&fe.addEventListener("change",be=>{l=parseInt(be.target.value,10)||60,p||$()}),U()}function U(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(P=>{P.dataset.tabJumpBound||(P.dataset.tabJumpBound="1",P.addEventListener("click",z=>{const R=z.currentTarget.dataset.tabJump;if(R==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(R==="upload"){const Z=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');Z&&Z.click()}}))})}function ne(){U()}window._loadFolderWatcherPanel=D;function ae(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(z=>/chromium|google chrome|microsoft edge/i.test(z.brand||""))}catch{}const P=navigator.userAgent||"";return!!(/Edg\//.test(P)||/Chrome\//.test(P)&&!/OPR\/|YaBrowser|Opera/.test(P))}function le(){try{if(ae()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const P=document.getElementById("chrome-only-banner");if(!P)return;const z=P.querySelector('[data-i18n="chrome-banner-msg"]'),R=P.querySelector('[data-i18n="chrome-banner-dismiss"]');z&&typeof t=="function"&&(z.textContent=t("chrome-banner-msg")),R&&typeof t=="function"&&(R.textContent=t("chrome-banner-dismiss")),P.style.display="";const Z=document.getElementById("chrome-only-banner-close");Z&&!Z.dataset.bound&&(Z.dataset.bound="1",Z.addEventListener("click",()=>{P.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",le):setTimeout(le,0)),window._refreshChromeBanner=le})();const vs=`
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
    `;we("email-modal",vs);(function(){let e=null,n=null,a="new",o=!1,s=!1;async function i(){const k=document.getElementById("email-empty"),M=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!k||!M))try{const H=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(H.status===401){localStorage.removeItem("mrpilot_token");const $=await H.json().catch(()=>({}));if((typeof $.detail=="string"?$.detail:$.detail&&$.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!H.ok){d("none");return}const j=await H.json();e=j.account||null,n=j.presets||{},o=!0,r(),e&&x()}catch(H){console.error("[email-ingest] load failed",H),d("none")}}function r(){const k=document.getElementById("email-empty"),M=document.getElementById("email-account-card"),H=document.getElementById("email-logs-section");if(!e){k.style.display="",M.style.display="none",H&&(H.style.display="none"),d("none");return}k.style.display="none",M.style.display="",H&&(H.style.display="");const j=document.getElementById("email-account-addr"),$=document.getElementById("email-account-host"),q=document.getElementById("email-account-last"),F=document.getElementById("email-last-error"),W=document.getElementById("email-enabled-toggle");if(j&&(j.textContent=e.email_address||"-"),$&&($.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),q){const G=e.last_fetched_at;if(!G)q.textContent=t("email-last-never");else{const A=l(G),N=!e.last_error;q.textContent=N?t("email-last-ok",{time:A}):t("email-last-fail",{time:A})}}F&&(e.last_error?(F.style.display="",F.textContent=p(e.last_error)):F.style.display="none"),W&&(W.checked=!!e.enabled),e.enabled?e.last_error?d("error"):d("on"):d("off")}function d(k){const M=document.getElementById("email-status-summary");if(!M)return;M.classList.remove("none","ready","active","coming");let H="auto-status-loading";k==="none"?(H="email-status-none",M.classList.add("none")):k==="on"?(H="email-status-on",M.classList.add("active")):k==="off"?(H="email-status-off",M.classList.add("coming")):k==="error"&&(H="email-status-error",M.classList.add("none")),M.setAttribute("data-i18n",H),M.textContent=t(H)}function l(k){if(!k)return"";const M=new Date(k);if(isNaN(M.getTime()))return"";const H=j=>String(j).padStart(2,"0");return`${H(M.getMonth()+1)}-${H(M.getDate())} ${H(M.getHours())}:${H(M.getMinutes())}`}function p(k){if(!k)return"";const M=String(k);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(M)?t("email-test-auth-fail"):/timeout|timed out/i.test(M)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(M),M)}function f(k){a=k;const M=document.getElementById("email-modal");if(!M)return;const H=document.getElementById("email-preset");H.innerHTML="";const j=n||{},$=["gmail","outlook","yahoo","icloud","qq","163","custom"],q={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};$.forEach(O=>{if(!j[O])return;const U=document.createElement("option");U.value=O,U.textContent=O==="custom"?t("email-preset-custom"):q[O]||O,H.appendChild(U)});const F=document.getElementById("email-modal-title"),W=document.getElementById("email-address"),G=document.getElementById("email-password"),A=document.getElementById("email-imap-host"),N=document.getElementById("email-imap-port"),V=document.getElementById("email-imap-ssl"),X=document.getElementById("email-folder"),oe=document.getElementById("email-mark-read"),se=document.getElementById("email-bind-enabled"),ue=document.getElementById("email-test-result"),D=document.getElementById("email-adv-details");if(ue&&(ue.style.display="none",ue.textContent=""),k==="edit"&&e){F.setAttribute("data-i18n","email-modal-title-edit"),F.textContent=t("email-modal-title-edit"),W.value=e.email_address||"",G.value="",G.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),G.placeholder=t("email-field-password-edit-ph"),A.value=e.imap_host||"",N.value=e.imap_port||993,V.checked=e.imap_use_ssl!==!1,X.value=e.folder||"INBOX",oe.checked=e.mark_as_read!==!1,se.checked=e.enabled!==!1;const O=document.getElementById("email-filter-sender"),U=document.getElementById("email-filter-subject");O&&(O.value=e.filter_sender||""),U&&(U.value=e.filter_subject||""),v(e.interval_min||15),H.value=_(e.imap_host)||"custom",D&&(D.open=!0)}else{F.setAttribute("data-i18n","email-modal-title-new"),F.textContent=t("email-modal-title-new"),W.value="",G.value="",G.setAttribute("data-i18n-placeholder","email-field-password-ph"),G.placeholder=t("email-field-password-ph"),H.value="gmail",u("gmail"),X.value="INBOX",oe.checked=!0,se.checked=!0;const O=document.getElementById("email-filter-sender"),U=document.getElementById("email-filter-subject");O&&(O.value=""),U&&(U.value=""),v(15),D&&(D.open=!1)}b(),M.style.display="flex",setTimeout(()=>W.focus(),60)}function c(){const k=document.getElementById("email-modal");k&&(k.style.display="none")}function u(k){const M=(n||{})[k];if(!M||k==="custom")return;const H=document.getElementById("email-imap-host"),j=document.getElementById("email-imap-port"),$=document.getElementById("email-imap-ssl");H&&(H.value=M.host||""),j&&(j.value=M.port||993),$&&($.checked=M.ssl!==!1)}const m={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function h(k){if(!k||!k.includes("@"))return;const M=k.split("@")[1].toLowerCase().trim(),H=m[M];if(!H)return;const j=document.getElementById("email-preset");if(!j)return;const $=j.value;$&&$!=="custom"&&$!==""&&$===H||(j.value=H,u(H))}function _(k){if(!k)return null;const M=n||{};for(const H in M)if(H!=="custom"&&M[H]&&M[H].host===k)return H;return null}function w(){const k=document.querySelector("#email-interval-options .email-interval-btn.active"),M=k?parseInt(k.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(M)?M:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function b(){const k=document.getElementById("email-interval-options");!k||k._bound||(k._bound=!0,k.addEventListener("click",M=>{const H=M.target.closest(".email-interval-btn");H&&(k.querySelectorAll(".email-interval-btn").forEach(j=>j.classList.remove("active")),H.classList.add("active"))}))}function v(k){const M=[5,15,60].includes(k)?k:15,H=document.getElementById("email-interval-options");H&&H.querySelectorAll(".email-interval-btn").forEach(j=>{j.classList.toggle("active",parseInt(j.dataset.interval,10)===M)})}function E(k,M){const H=document.getElementById("email-test-result");H&&(H.style.display="",H.textContent=M,H.className="form-test-result "+(k==="ok"?"ok":k==="running"?"running":"fail"))}async function B(){const k=w();if(!k.email_address){E("fail",t("email-addr-required"));return}if(!k.password){E("fail",t("email-password-required"));return}if(!k.imap_host){E("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-test");M&&(M.disabled=!0),E("running",t("email-test-running"));try{const H=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:k.email_address,password:k.password,imap_host:k.imap_host,imap_port:k.imap_port,imap_use_ssl:k.imap_use_ssl,folder:k.folder})}),j=await H.json().catch(()=>({}));if(H.ok&&j.success)E("ok",t("email-test-ok",{folder:k.folder,n:j.folder_count??"?"}));else{const $=j.error_msg||"";$==="auth_failed"||/auth/i.test($)?E("fail",t("email-test-auth-fail")):E("fail",t("email-test-fail",{msg:$||H.status}))}}catch(H){E("fail",t("email-test-fail",{msg:String(H).slice(0,120)}))}finally{M&&(M.disabled=!1)}}async function C(){const k=w();if(!k.email_address){E("fail",t("email-addr-required"));return}if(a==="new"&&!k.password){E("fail",t("email-password-required"));return}if(!k.imap_host){E("fail",t("email-host-required"));return}const M=document.getElementById("btn-email-modal-save");M&&(M.disabled=!0);const H={...k};a==="edit"&&!H.password&&delete H.password;try{const j=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(H)}),$=await j.json().catch(()=>({}));if(j.ok&&$.ok)e=$.account,showToast(t("email-save-ok"),"success"),c(),r(),x();else{const F="email."+($.detail||"").split(".").slice(-1)[0];E("fail",t(F)!==F?t(F):t("email-save-fail"))}}catch{E("fail",t("email-save-fail"))}finally{M&&(M.disabled=!1)}}async function L(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),r();const H=document.getElementById("email-logs-list");H&&(H.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function y(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const k=document.getElementById("btn-email-trigger"),M=k?k.innerHTML:"";k&&(k.disabled=!0,k.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const H=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),j=await H.json().catch(()=>({}));if(H.ok){const $=j.emails_scanned||0,q=j.ocr_succeeded||0,F=j.ocr_failed||0;$===0&&q===0&&F===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:$,ok:q,fail:F}),F>0?"warn":"success")}else{const q="email."+(j.detail||"").split(".").slice(-1)[0];showToast(t(q)!==q?t(q):t("email-trigger-fail"),"error")}await i()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,k&&(k.disabled=!1,k.innerHTML=M)}}async function g(){if(!e)return;const k=document.getElementById("email-enabled-toggle"),M=!!(k&&k.checked),H=e.enabled;try{const j=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:M})}),$=await j.json().catch(()=>({}));j.ok&&$.ok?(e=$.account,r()):(k&&(k.checked=H),showToast(t("email-toggle-fail"),"error"))}catch{k&&(k.checked=H),showToast(t("email-toggle-fail"),"error")}}async function x(){const k=document.getElementById("email-logs-list");if(k){k.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const M=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!M.ok){k.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const H=await M.json();if(!Array.isArray(H)||H.length===0){k.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}k.innerHTML=H.map(T).join("")}catch{k.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function T(k){const M=l(k.created_at),H=k.status||"failed",j=H==="success"?"ok":H==="partial"?"partial":"fail",$=H==="success"?"✓":H==="partial"?"◐":"✗",q=k.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,F=t("email-log-counts",{scanned:k.emails_scanned||0,att:k.attachments_found||0,ok:k.ocr_succeeded||0,fail:k.ocr_failed||0}),W=(k.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${j}">
                <span class="log-time">${escapeHtml(M)}</span>
                <span class="log-status">${$}</span>
                ${q}
                <span class="log-counts">${escapeHtml(F)}</span>
                <span class="log-elapsed">${escapeHtml(W)}</span>
            </div>
        `}function S(){const k=document.getElementById("btn-email-bind");k&&k.addEventListener("click",()=>f("new"));const M=document.getElementById("btn-email-edit");M&&M.addEventListener("click",()=>f("edit"));const H=document.getElementById("btn-email-unbind");H&&H.addEventListener("click",L);const j=document.getElementById("btn-email-trigger");j&&j.addEventListener("click",y);const $=document.getElementById("email-enabled-toggle");$&&$.addEventListener("change",g);const q=document.getElementById("email-modal-close");q&&q.addEventListener("click",c);const F=document.getElementById("btn-email-modal-cancel");F&&F.addEventListener("click",c);const W=document.getElementById("btn-email-modal-test");W&&W.addEventListener("click",B);const G=document.getElementById("btn-email-modal-save");G&&G.addEventListener("click",C);const A=document.getElementById("email-preset");A&&A.addEventListener("change",X=>u(X.target.value));const N=document.getElementById("email-address");N&&!N.dataset.autoBound&&(N.dataset.autoBound="1",N.addEventListener("blur",X=>h((X.target.value||"").trim())),N.addEventListener("input",X=>{const oe=(X.target.value||"").trim();oe.includes("@")&&oe.split("@")[1].includes(".")&&h(oe)}));const V=document.getElementById("btn-email-refresh-logs");V&&V.addEventListener("click",()=>{V.classList.add("spinning"),setTimeout(()=>V.classList.remove("spinning"),600),x()})}S(),window._loadEmailIngestPanel=i,window._rerenderEmailIngest=function(){if(!o)return;r();const k=document.getElementById("email-logs-section");e&&k&&k.open&&x()};let I=null;window._startEmailLogAutoRefresh=function(){I||(I=setInterval(()=>{e&&o&&x()},3e4))},window._stopEmailLogAutoRefresh=function(){I&&(clearInterval(I),I=null)}})();const hs=`
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
`;we("bank-cand-drawer",hs);const gs=`
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
`;we("bank-client-picker-modal",gs);const J={sessions:[],currentSession:null,currentTxs:[],currentFilter:"all",currentTxForDrawer:null,loaded:!1,queue:[],qSeq:0,sessionFilter:"all",pickerSelected:null};function bs(e){const n=Number(e||0);let a="score-low";return n>=85?a="score-high":n>=60&&(a="score-mid"),'<span class="bank-cand-score '+a+'">'+n.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function ys(e){const n=document.getElementById("bank-upload-progress");n&&(n.style.display="none")}function ws(){const e=document.getElementById("bank-upload-error");e&&(e.style.display="none")}function ks(e){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[e]||t("bank-err-unknown")+" ("+e+")"}function Ge(e){if(e==null)return"-";const n=Number(e);return isNaN(n)?"-":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function rt(e){if(!e)return"-";const n=String(e);return n.length>=10?n.slice(0,10):n}function ba(e,n){return!e&&!n?"":(rt(e)||"?")+" ~ "+(rt(n)||"?")}function pe(e){return e==null?"":String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}async function xs(e){J.currentTxForDrawer=e;const n=document.getElementById("bank-detail-body");n&&n.classList.add("has-pane");const a=document.getElementById("bank-cand-pane-title"),o=document.getElementById("bank-cand-pane-sub"),s=document.getElementById("bank-cand-pane-foot");if(a&&(a.textContent=t("bank-cand-pane-current")),o){const r=e.direction==="OUT"?"-":"+",d=e.direction==="OUT"?"bank-out":"bank-in";o.innerHTML=`${pe(rt(e.tx_date))}
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <span>${pe(e.description||"-")}</span>
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <strong class="${d}">${r}${Ge(e.amount)}</strong>`}s&&(s.style.display="");const i=document.getElementById("bank-cand-pane-body");if(i){i.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const r=await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!r.ok)throw new Error("cands:"+r.status);const d=await r.json();Es(e,d.candidates||[])}catch{i.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function _s(e,n,a){const o=n.history_id,s=n.invoice_no||"-",i=n.vendor||"-",r=n.amount_total!==null&&n.amount_total!==void 0?Ge(n.amount_total):"-",d=n.invoice_date?rt(n.invoice_date):"-",l=n.filename||"",p=!!a&&e.matched_history_id===o,f="bank-cand-card"+(n.is_auto_picked?" is-auto":"")+(p?" is-picked":"");let c="";return p?c='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":c='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+pe(o)+'"><span>'+t(n.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+f+'" data-hid="'+pe(o)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+pe(i)+"</div>"+bs(n.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+pe(s)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+r+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+pe(d)+"</span></div>"+(l?'<div class="bank-cand-card-file" title="'+pe(l)+'">'+pe(l)+"</div>":"")+(n.reason?'<div class="bank-cand-card-reason">'+pe(n.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+c+"</div></div>"}function Es(e,n){const a=document.getElementById("bank-cand-pane-body");if(!a)return;const o=n||[];let s="";if(e.match_status==="matched")s='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",o.length)+"</div>";else if(e.match_status==="suggested")s='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",o.length)+"</div>";else if(o.length>0)s='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",o.length)+"</div>";else{a.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const i=e.match_status==="matched",r=o.map(d=>_s(e,d,i)).join("");a.innerHTML=s+'<div class="bank-cand-list">'+r+"</div>",a.querySelectorAll('[data-act="pick"]').forEach(d=>{d.addEventListener("click",()=>{Ls(d.dataset.hid)})}),a.querySelectorAll('[data-act="unmatch"]').forEach(d=>{d.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),Et(),await dt(J.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function Et(){const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane");const n=document.getElementById("bank-cand-pane-title"),a=document.getElementById("bank-cand-pane-sub"),o=document.getElementById("bank-cand-pane-body"),s=document.getElementById("bank-cand-pane-foot");n&&(n.textContent=t("bank-cand-pane-empty-title")),a&&(a.textContent=t("bank-cand-pane-empty-sub")),s&&(s.style.display="none"),o&&(o.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const i=document.getElementById("bank-tx-tbody");i&&i.querySelectorAll("tr.is-selected").forEach(r=>r.classList.remove("is-selected")),J.currentTxForDrawer=null}async function dt(e){try{const n="/api/bank-recon/sessions/"+encodeURIComponent(e)+(J.currentFilter!=="all"?"?filter="+J.currentFilter:""),a=await fetch(n,{headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("detail:"+a.status);const o=await a.json();J.currentSession=o.session,J.currentTxs=o.transactions||[],Hs()}catch(n){console.warn("[bank-recon] loadSessionDetail failed",n),showToast(t("bank-load-failed"),"error")}}async function Bs(){if(!J.currentSession)return;const e=document.getElementById("btn-bank-run-match"),n=e.innerHTML;e.disabled=!0,e.innerHTML="<span>"+t("bank-matching")+"</span>";try{const a=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(J.currentSession.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("match:"+a.status);const o=await a.json();showToast(t("bank-match-done").replace("{matched}",o.matched).replace("{suggested}",o.suggested).replace("{unmatched}",o.unmatched),"success"),await dt(J.currentSession.id),await pt()}catch(a){console.warn("[bank-recon] match failed",a),showToast(t("bank-match-failed"),"error")}finally{e.disabled=!1,e.innerHTML=n}}async function Is(){if(!(!J.currentSession||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const n=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(J.currentSession.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!n.ok)throw new Error("delete:"+n.status);showToast(t("bank-deleted"),"success"),J.currentSession=null,J.currentTxs=[],bn(),await pt()}catch(n){console.warn("[bank-recon] delete failed",n),showToast(t("bank-delete-failed"),"error")}}async function Hn(){if(J.currentTxForDrawer)try{const e=await fetch("/api/bank-recon/tx/"+encodeURIComponent(J.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!e.ok)throw new Error("ignore:"+e.status);Et(),await dt(J.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}async function Ls(e){if(J.currentTxForDrawer)try{const n=await fetch("/api/bank-recon/tx/"+encodeURIComponent(J.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:e})});if(!n.ok)throw new Error("pick:"+n.status);showToast(t("bank-matched-ok"),"success"),Et(),await dt(J.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}function ya(){if(!J.currentSession)return;const e=J.currentSession;document.getElementById("bank-detail-title").textContent=(e.bank_code||"-")+(e.account_last4?" ···"+e.account_last4:"")+" · "+(e.source_filename||""),document.getElementById("bank-meta-period").textContent=ba(e.period_start,e.period_end)||"-",document.getElementById("bank-meta-opening").textContent=Ge(e.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+Ge(e.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+Ge(e.total_outflow),document.getElementById("bank-meta-closing").textContent=Ge(e.closing_balance);const n=J.currentTxs||[],a=n.length;let o=0,s=0,i=0;for(const r of n){const d=r.match_status||"unmatched";d==="matched"?o++:d==="suggested"?s++:i++}document.getElementById("bank-stat-total").textContent=a,document.getElementById("bank-stat-matched").textContent=o,document.getElementById("bank-stat-suggested").textContent=s,document.getElementById("bank-stat-unmatched").textContent=i}function hn(){const e=document.getElementById("bank-tx-tbody");if(!e)return;let n=J.currentTxs||[];if(J.currentFilter!=="all"&&(n=n.filter(a=>J.currentFilter==="matched"?a.match_status==="matched":J.currentFilter==="suggested"?a.match_status==="suggested":J.currentFilter==="unmatched"?a.match_status==="unmatched"||a.match_status==="ignored":!0)),n.length===0){e.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(e.innerHTML=n.map(a=>Cs(a)).join(""),e.querySelectorAll("tr[data-tx-id]").forEach(a=>{a.addEventListener("click",()=>{const o=a.dataset.txId,s=J.currentTxs.find(i=>i.id===o);s&&(e.querySelectorAll("tr.is-selected").forEach(i=>i.classList.remove("is-selected")),a.classList.add("is-selected"),xs(s))})}),J.currentTxForDrawer){const a=e.querySelector('tr[data-tx-id="'+J.currentTxForDrawer.id+'"]');a&&a.classList.add("is-selected")}}function Cs(e){const n=e.direction==="OUT",a=n?"-":"+",o=n?"bank-out":"bank-in",s=e.match_status||"unmatched",i=t("bank-match-"+s)||s,r=rt(e.tx_date),d=e.channel?`<span class="bank-tx-channel">${pe(e.channel)}</span>`:"";return`
        <tr data-tx-id="${pe(e.id)}">
            <td class="bank-tx-date">${pe(r)}</td>
            <td class="bank-tx-desc">${d}${pe(e.description||"-")}</td>
            <td class="bank-td-amount ${o}">${a}${Ge(e.amount)}</td>
            <td><span class="bank-tx-match mt-${s}">${pe(i)}</span></td>
        </tr>
    `}function gn(){const e=document.getElementById("bank-client-badge");if(!e||!J.currentSession)return;const n=J.currentSession.client_id,a=document.getElementById("bank-client-badge-dot"),o=document.getElementById("bank-client-badge-name"),s=document.getElementById("bank-client-badge-caret"),i=typeof _userInfo<"u"?_userInfo:null,r=!(i&&i.role==="member");if(n!=null){const d=(window._clientsCache||[]).find(l=>Number(l.id)===Number(n));e.classList.remove("is-empty"),a&&(a.style.background=d&&d.color||"#111111"),o&&(o.textContent=d&&(d.short_name||d.name)||"#"+n)}else e.classList.add("is-empty"),a&&(a.style.background=""),o&&(o.textContent=t("bank-client-none"));r?(e.classList.remove("is-readonly"),e.disabled=!1,s&&(s.style.display="")):(e.classList.add("is-readonly"),e.disabled=!0,s&&(s.style.display="none")),e.style.display=""}function Ss(){if(!J.currentSession)return;const e=typeof _userInfo<"u"?_userInfo:null;if(!!(e&&e.role==="member"))return;J.pickerSelected=J.currentSession.client_id!=null?Number(J.currentSession.client_id):null,ka();const a=document.getElementById("bank-client-picker-modal");a&&(a.style.display="")}function wa(){const e=document.getElementById("bank-client-picker-modal");e&&(e.style.display="none"),J.pickerSelected=null}function ka(){const e=document.getElementById("bank-client-picker-list");if(!e)return;const n=(window._clientsCache||[]).filter(o=>o&&(o.is_active===!0||o.is_active===void 0)),a=[];a.push('<div class="bank-client-picker-row is-none'+(J.pickerSelected==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+pe(t("bank-client-picker-none"))+"</span></div>"),n.forEach(o=>{const s=Number(o.id)===Number(J.pickerSelected)?" is-selected":"";a.push('<div class="bank-client-picker-row'+s+'" data-cid="'+pe(o.id)+'"><span class="bank-cp-dot" style="background:'+pe(o.color||"#111111")+'"></span><span>'+pe(o.short_name||o.name||"#"+o.id)+"</span></div>")}),e.innerHTML=a.join(""),e.querySelectorAll(".bank-client-picker-row").forEach(o=>{o.addEventListener("click",()=>{const s=o.dataset.cid;J.pickerSelected=s?Number(s):null,ka()})})}async function Ts(){if(J.currentSession)try{const e=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(J.currentSession.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:J.pickerSelected})});if(!e.ok)throw new Error("client:"+e.status);J.currentSession.client_id=J.pickerSelected,gn(),showToast(t("bank-client-changed"),"success"),wa();try{await pt()}catch{}}catch(e){console.warn("[bank-recon] save client failed",e),showToast(t("bank-client-change-failed"),"error")}}async function pt(){try{const e=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!e.ok)throw new Error("sessions:"+e.status);J.sessions=await e.json(),jt()}catch(e){console.warn("[bank-recon] loadSessions failed",e),J.sessions=[],jt()}}function An(){const e=document.getElementById("bank-status-summary");if(!e)return;if(J.sessions.length===0){e.textContent=t("bank-pill-none");return}let a=0;for(const o of J.sessions)o.parse_status==="parsed"&&(o.unmatched_count||0)>0&&a++;e.textContent=a>0?t("bank-pill-pending").replace("{n}",a):t("bank-pill-ok")}function jt(){const e=document.getElementById("bank-sessions-list");if(!e)return;let n=J.sessions||[];if(J.sessionFilter==="parsed"?n=n.filter(a=>a.parse_status==="parsed"):J.sessionFilter==="failed"&&(n=n.filter(a=>a.parse_status==="parse_failed")),!J.sessions||J.sessions.length===0){e.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(n.length===0){e.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}e.innerHTML=n.map(a=>Ms(a)).join(""),e.querySelectorAll(".bank-session-row").forEach(a=>{a.addEventListener("click",o=>{o.target.closest(".bank-session-trash")||dt(a.dataset.sessionId)})}),e.querySelectorAll(".bank-session-trash").forEach(a=>{a.addEventListener("click",o=>{o.stopPropagation();const s=a.dataset.sessionId,i=a.dataset.sessionName||"";xa(s,i)})})}async function xa(e,n){if(!e)return;const a=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",n||"");if(await showConfirm(a,{danger:!0}))try{const s=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(e),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!s.ok)throw new Error("delete:"+s.status);showToast(t("bank-deleted"),"success"),J.currentSession&&J.currentSession.id===e&&(J.currentSession=null,J.currentTxs=[],bn()),await pt(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(s){console.warn("[bank-recon] delete failed",s),showToast(t("bank-delete-failed"),"error")}}function Ms(e){const n=(e.bank_code||"OTHER").toUpperCase(),a=ba(e.period_start,e.period_end),o=e.account_last4?"···"+e.account_last4:"",s=$s(e),i=rt(e.created_at);return`
        <div class="bank-session-row" data-session-id="${pe(e.id)}">
            <div class="bank-session-bank bk-${pe(n)}">${pe(n)}</div>
            <div class="bank-session-info">
                <div class="bank-session-title">${pe(e.source_filename||a||"-")}</div>
                <div class="bank-session-meta">${pe(a)} · ${pe(o)} · ${pe(i)}</div>
            </div>
            <div class="bank-session-counts">${s}</div>
            <button class="bank-session-trash" data-session-id="${pe(e.id)}" data-session-name="${pe(e.source_filename||"")}" title="${pe(t("bank-session-delete-tip")||"删除")}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                </svg>
            </button>
            <div class="bank-session-arrow">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
            </div>
        </div>
    `}function $s(e){if(e.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(e.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const n=e.tx_count||0,a=e.matched_count||0,o=e.unmatched_count||0,s=[`<span class="bank-session-count">${n} ${t("bank-count-tx")}</span>`];return a>0&&s.push(`<span class="bank-session-count cnt-matched">${a} ${t("bank-count-matched")}</span>`),o>0&&s.push(`<span class="bank-session-count cnt-unmatched">${o} ${t("bank-count-unmatched")}</span>`),s.join("")}function Hs(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",ya(),hn(),gn()}function bn(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane"),J.currentTxForDrawer=null}const As=3;function js(){return J.qSeq+=1,"q"+J.qSeq+"_"+Date.now()}async function Ps(e){const n=Array.from(e.target.files||[]);if(e.target.value="",n.length!==0){for(const a of n){const o={id:js(),file:a,name:a.name,size:a.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};a.name.toLowerCase().endsWith(".pdf")?a.size>20*1024*1024&&(o.status="failed",o.error_code="bank_recon.file_too_large"):(o.status="failed",o.error_code="bank_recon.only_pdf"),J.queue.push(o)}Ds(),Be(),yn()}}function Ds(){const e=document.getElementById("bank-upload-queue");e&&(e.style.display=""),ys(),ws()}function Be(){const e=document.getElementById("bank-upload-queue-list"),n=document.getElementById("bank-upload-queue-summary");if(!e)return;if(J.queue.length===0){e.innerHTML="",n&&(n.textContent="");const r=document.getElementById("bank-upload-queue");r&&(r.style.display="none");return}let a=0,o=0,s=0,i=0;for(const r of J.queue)r.status==="ok"?a++:r.status==="failed"?o++:r.status==="uploading"||r.status==="parsing"?s++:i++;n&&(n.textContent=t("bank-queue-summary").replace("{ok}",a).replace("{run}",s).replace("{wait}",i).replace("{fail}",o)),e.innerHTML=J.queue.map(qs).join(""),e.querySelectorAll("[data-q-act]").forEach(r=>{const d=r.dataset.qAct,l=r.dataset.qId;r.addEventListener("click",()=>{d==="retry"&&Rs(l),d==="remove"&&Fs(l)})})}function qs(e){const n=(e.size/1024).toFixed(0)+" KB";let a="",o="";if(e.status==="pending")a='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",o='<button data-q-act="remove" data-q-id="'+pe(e.id)+'" class="bq-act">×</button>';else if(e.status==="uploading")a='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(e.progress||0)+'%"></div></div>';else if(e.status==="parsing")a='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(e.status==="ok")a='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",e.tx_count||0)+"</span>",o='<button data-q-act="remove" data-q-id="'+pe(e.id)+'" class="bq-act">×</button>';else if(e.status==="failed"){const s=ks(e.error_code||"unknown");a='<span class="bq-stat bq-fail" title="'+pe(s)+'">'+pe(s)+"</span>",o='<button data-q-act="retry" data-q-id="'+pe(e.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+pe(e.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+pe(e.id)+'"><div class="bq-name" title="'+pe(e.name)+'">'+pe(e.name)+'</div><div class="bq-size">'+n+'</div><div class="bq-status">'+a+'</div><div class="bq-actions">'+o+"</div></div>"}function Rs(e){const n=J.queue.find(a=>a.id===e);n&&(n.status="pending",n.error_code=null,n.progress=0,Be(),yn())}function Fs(e){const n=J.queue.findIndex(o=>o.id===e);if(n<0)return;const a=J.queue[n];a.status==="uploading"||a.status==="parsing"||(J.queue.splice(n,1),Be())}function zs(){J.queue=J.queue.filter(e=>e.status!=="ok"),Be()}async function yn(){for(;;){if(J.queue.filter(a=>a.status==="uploading"||a.status==="parsing").length>=As)return;const n=J.queue.find(a=>a.status==="pending");if(!n){J.queue.every(a=>a.status==="ok"||a.status==="failed")&&(await pt(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}Ns(n).then(()=>yn())}}async function Ns(e){e.status="uploading",e.progress=0,Be();try{const n=new FormData;n.append("file",e.file,e.name);const a=await new Promise((s,i)=>{const r=new XMLHttpRequest;r.open("POST","/api/bank-recon/upload"),r.setRequestHeader("Authorization","Bearer "+token),r.upload.onprogress=d=>{d.lengthComputable&&(e.progress=Math.min(99,Math.round(d.loaded/d.total*100)),Be())},r.upload.onload=()=>{e.status="parsing",Be()},r.onload=()=>{r.status>=200&&r.status<300?s({status:r.status,text:r.responseText}):s({status:r.status,text:r.responseText})},r.onerror=()=>i(new Error("network")),r.send(n)});let o={};try{o=JSON.parse(a.text||"{}")}catch{o={}}if(a.status>=400){e.status="failed",e.error_code=o&&o.detail||"unknown",Be();return}if(o.parse_status==="parse_failed"){e.status="failed",e.error_code=o.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",Be();return}e.status="ok",e.tx_count=o.tx_count||0,e.session_id=o.session_id||null,Be()}catch(n){console.warn("[bank-recon] upload failed",n),e.status="failed",e.error_code="network",Be()}}async function _a(){if(J.loaded){An();return}J.loaded=!0,Os(),await pt(),An()}function Os(){const e=document.getElementById("bank-file-input");e&&!e._bound&&(e._bound=!0,e.addEventListener("change",Ps));const n=document.getElementById("btn-bank-queue-clear-done");n&&!n._bound&&(n._bound=!0,n.addEventListener("click",zs));const a=document.getElementById("btn-bank-back");a&&!a._bound&&(a._bound=!0,a.addEventListener("click",()=>{J.currentSession=null,J.currentTxs=[],bn()}));const o=document.getElementById("btn-bank-delete");o&&!o._bound&&(o._bound=!0,o.addEventListener("click",Is));const s=document.getElementById("btn-bank-run-match");s&&!s._bound&&(s._bound=!0,s.addEventListener("click",Bs)),document.querySelectorAll(".bank-filter-btn").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",()=>{J.currentFilter=f.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(c=>{c.classList.toggle("active",c===f)}),hn()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",Et))});const i=document.getElementById("btn-bank-cand-pane-close");i&&!i._bound&&(i._bound=!0,i.addEventListener("click",Et));const r=document.getElementById("btn-bank-cand-ignore");r&&!r._bound&&(r._bound=!0,r.addEventListener("click",Hn));const d=document.getElementById("btn-bank-cand-ignore-pane");d&&!d._bound&&(d._bound=!0,d.addEventListener("click",Hn));const l=document.getElementById("bank-client-badge");l&&!l._bound&&(l._bound=!0,l.addEventListener("click",Ss)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",wa))});const p=document.getElementById("btn-bank-client-picker-save");p&&!p._bound&&(p._bound=!0,p.addEventListener("click",Ts)),document.querySelectorAll(".bank-sessions-chip").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",()=>{J.sessionFilter=f.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(c=>{c.classList.toggle("active",c===f)}),jt()}))})}window._deleteBankSession=xa;window._loadBankReconPanel=_a;window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(jt(),J.currentSession&&(ya(),hn(),gn(),!J.currentTxForDrawer)){const e=document.getElementById("bank-cand-pane-title"),n=document.getElementById("bank-cand-pane-sub");e&&(e.textContent=t("bank-cand-pane-empty-title")),n&&(n.textContent=t("bank-cand-pane-empty-sub"))}Be()}};typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon);window._openBankSession=async function(e){e&&(J.loaded||await _a(),await dt(e))};(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Vs=`
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
    `,Us=`
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
    `;we("client-modal-mask",Vs);we("wsclient-modal-mask",Us);(function(){let e=[],n=null,a="",o="seller";const s={page:0,pageSize:12,keyword:""},i=new Set;let r=[];const d={keyword:""};let l=null;function p(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function f(A,N={}){const V=await fetch(A,{...N,headers:{"Content-Type":"application/json",...p(),...N.headers||{}}});if(!V.ok){const X=await V.json().catch(()=>({}));throw new Error(X.detail||"HTTP "+V.status)}return V.json()}async function c(){try{e=(await f("/api/clients")).clients||[],window._clientsCache=e}catch(A){console.error("loadClientsCache fail",A),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function u(A){o=A==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(X=>X.classList.toggle("active",X.dataset.custTab===o));const N=document.getElementById("cust-pane-seller"),V=document.getElementById("cust-pane-buyer");N&&N.classList.toggle("active",o==="seller"),V&&V.classList.toggle("active",o==="buyer")}function m(){const A=window._userInfo||{},N=String(A.role||"").toLowerCase(),V=String(A.tenant_role||"").toLowerCase();return A.is_super_admin===!0||A.is_owner===!0||N==="owner"||N==="admin"||V==="owner"||V==="admin"}function h(){window._workspaceClientsCache=r,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function _(){try{const A=await f("/api/workspace/clients");r=A&&(A.clients||A.items)||[],window._workspaceClientsCache=r}catch(A){console.error("loadSellerCache fail",A),r=[]}return r}function w(){const A=d.keyword.trim().toLowerCase();return A?r.filter(N=>(N.name||"").toLowerCase().includes(A)||(N.tax_id||"").toLowerCase().includes(A)):r}function b(){const A=document.getElementById("seller-tbody");if(!A)return;const N=m(),V=document.getElementById("btn-seller-new");V&&(V.style.display=N?"":"none");const X=w(),oe=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!X.length){A.innerHTML=`<div class="cust-empty">${escapeHtml(t(d.keyword?"cust-no-match":"seller-empty"))}</div>`;return}A.innerHTML=X.map(se=>{const D=oe!=null&&Number(oe)===Number(se.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${se.id}">${escapeHtml(t("seller-set-current"))}</button>`,O=N?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${se.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${se.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${se.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(se.name||"#"+se.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(se.tax_id||"—")}</div>
                <div class="align-right">${se.invoice_count||0}</div>
                <div class="cust-row-actions">${D}${O}</div>
            </div>`}).join("")}function v(A){l=A?A.id:null,document.getElementById("wsclient-modal-title").textContent=t(A?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=A&&A.name||"",document.getElementById("wsclient-input-tax").value=A&&A.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=A?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function E(){document.getElementById("wsclient-modal-mask").style.display="none",l=null}async function B(){const A=document.getElementById("wsclient-input-name").value.trim(),N=document.getElementById("wsclient-input-tax").value.trim();if(!A){showToast(t("client-msg-name-required"),"fail");return}try{l?(await f("/api/workspace/clients/"+l,{method:"PATCH",body:JSON.stringify({name:A,tax_id:N})}),showToast(t("client-msg-updated"),"success")):(await f("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:A,tax_id:N||null})}),showToast(t("client-msg-created"),"success")),E(),await _(),b(),h()}catch(V){const X=V&&V.message?V.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+X,"fail")}}async function C(){if(!l)return;const A=r.find(V=>Number(V.id)===Number(l));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",A?A.name:""),{danger:!0}))try{const V=l;await f("/api/workspace/clients/"+V,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(V)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),E(),await _(),b(),h()}catch{showToast(t("client-msg-save-fail"),"fail")}}function L(){const A=s.keyword.trim().toLowerCase();return A?e.filter(N=>(N.name||"").toLowerCase().includes(A)||(N.short_name||"").toLowerCase().includes(A)||(N.tax_id||"").toLowerCase().includes(A)):e}function y(){const A=L(),N=s.pageSize,V=Math.max(0,Math.ceil(A.length/N)-1);s.page>V&&(s.page=V);const X=s.page*N;return{all:A,items:A.slice(X,X+N),start:X,ps:N,total:A.length,maxPage:V}}function g(){const A=document.getElementById("buyer-tbody");if(!A)return;const{items:N,start:V,ps:X,total:oe,maxPage:se}=y();oe?A.innerHTML=N.map(U=>{const ne=i.has(U.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${U.id}">
                    <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${U.id}" ${ne?"checked":""}></div>
                    <div style="min-width:0">
                        <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(U.color||"#111")}"></span><span class="cust-name-text">${escapeHtml(U.name)}</span></div>
                        ${U.tax_id?`<div class="cust-cell-sub">${escapeHtml(U.tax_id)}</div>`:""}
                    </div>
                    <div class="align-right">${U.invoice_count||0}</div>
                    <div class="align-right cust-cell-amount">฿${(U.total_amount||0).toLocaleString(void 0,{maximumFractionDigits:0})}</div>
                    <div class="cust-row-actions">
                        <button class="cust-row-btn" data-action="edit" data-cid="${U.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                        <button class="cust-row-btn" data-action="export" data-cid="${U.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t("client-card-export"))}</span></button>
                    </div>
                </div>`}).join(""):A.innerHTML=`<div class="cust-empty">${escapeHtml(t(s.keyword?"cust-no-match":"clients-empty"))}</div>`;const ue=document.getElementById("buyer-pager-info");ue&&(ue.textContent=oe?`${V+1}–${Math.min(V+X,oe)} / ${oe}`:"0");const D=document.getElementById("buyer-prev");D&&(D.disabled=s.page<=0);const O=document.getElementById("buyer-next");O&&(O.disabled=s.page>=se),x()}function x(){const A=i.size,N=document.getElementById("buyer-batch-bar");N&&(N.style.display=A?"flex":"none");const V=document.getElementById("buyer-batch-count");V&&(V.textContent=t("cust-selected-n").replace("{n}",A));const X=document.getElementById("buyer-check-all");if(X){const{items:oe}=y(),se=oe.map(D=>D.id),ue=se.filter(D=>i.has(D)).length;X.checked=se.length>0&&ue===se.length,X.indeterminate=ue>0&&ue<se.length}}function T(){i.clear(),g()}async function S(){const A=Array.from(i);if(!(!A.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",A.length),{danger:!0})))try{await f("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:A})}),showToast(t("client-msg-deleted"),"success"),i.clear(),await c(),g(),q(),G()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const A=document.getElementById("seller-tbody");A&&(A.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const N=document.getElementById("buyer-tbody");N&&(N.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([_(),c()]),b(),g()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&b()});function I(A){n=A?A.id:null;const N=!!A;document.getElementById("client-modal-title").textContent=t(N?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=A&&A.name||"",document.getElementById("client-input-short").value=A&&A.short_name||"",document.getElementById("client-input-tax").value=A&&A.tax_id||"",document.getElementById("client-input-address").value=A&&A.address||"",document.getElementById("client-input-contact").value=A&&A.contact_person||"",document.getElementById("client-input-phone").value=A&&A.contact_phone||"",document.getElementById("client-input-email").value=A&&A.contact_email||"",document.getElementById("client-input-notes").value=A&&A.notes||"";const V=A&&A.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(X=>{X.classList.toggle("active",X.dataset.color===V)}),document.getElementById("client-modal-delete").style.display=N?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function k(){document.getElementById("client-modal-mask").style.display="none",n=null}function M(){const A=document.querySelector("#client-color-picker .color-swatch.active");return A?A.dataset.color:"#111111"}async function H(){const A=document.getElementById("client-input-name").value.trim();if(!A){showToast(t("client-msg-name-required"),"fail");return}const N={name:A,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:M()};try{n?(await f(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify(N)}),showToast(t("client-msg-updated"),"success")):(await f("/api/clients",{method:"POST",body:JSON.stringify(N)}),showToast(t("client-msg-created"),"success")),k(),await c(),currentRoute==="clients"&&g(),q(),G()}catch(V){console.error("saveClient fail",V);const X=V&&V.message?V.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+X,"fail")}}async function j(){if(!n)return;const A=e.find(X=>X.id===n);if(!A)return;const N=t("client-delete-confirm").replace("{name}",A.name);if(await showConfirm(N,{danger:!0}))try{await f(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),k(),await c(),currentRoute==="clients"&&g(),q(),G()}catch(X){console.error(X),showToast(t("client-msg-save-fail"),"fail")}}async function $(A){const N=e.find(V=>V.id===A);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(A,N?N.name:"");return}try{const V=localStorage.getItem("mrpilot_token"),X=await fetch(`/api/clients/${A}/export?month=all`,{headers:{Authorization:"Bearer "+V}});if(!X.ok){let O="HTTP "+X.status;try{const U=await X.json();U&&U.detail&&(O=U.detail)}catch{}throw new Error(O)}const oe=await X.blob();if(oe.size<200){showToast(t("client-export-month-empty"),"info");return}const se=N&&N.name?N.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",ue=URL.createObjectURL(oe),D=document.createElement("a");D.href=ue,D.download=`${se}_export.csv`,D.click(),URL.revokeObjectURL(ue)}catch(V){console.error("exportClient fail",V),showToast(t("client-msg-save-fail")+" · "+(V.message||""),"fail")}}function q(){const A=document.getElementById("drawer-client-select");if(!A)return;const N=A.value;A.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(V=>`<option value="${V.id}">${escapeHtml(V.name)}</option>`).join(""),A.value=N||""}window.bindDrawerClient=function(A,N){const V=document.getElementById("drawer-client-select");if(!V)return;if(q(),V.value=N?String(N):"",!A){V.onchange=null;const oe=document.getElementById("drawer-client-add");oe&&(oe.onclick=()=>I(null));return}V.onchange=async()=>{const oe=V.value?parseInt(V.value,10):null;try{await f(`/api/history/${A}/assign_client`,{method:"POST",body:JSON.stringify({client_id:oe})}),showToast(t("client-msg-updated"),"success");const se=_results[_drawerIdx];se&&(se.client_id=oe),await c()}catch(se){console.error(se),showToast(t("client-msg-save-fail"),"fail"),V.value=N?String(N):""}};const X=document.getElementById("drawer-client-add");X&&(X.onclick=()=>I(null))};let F={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const A=document.getElementById("drawer-cat-datalist"),N=Date.now();if(N-F.fetched<300*1e3){A&&(A.innerHTML=F.items.map(X=>`<option value="${escapeHtml(X)}">`).join("")),W(F.supplier_count);return}const V=await f("/api/categories",{method:"GET"});F.fetched=N,F.items=V&&V.categories||[],F.supplier_count=V&&V.supplier_count||0,A&&(A.innerHTML=F.items.map(X=>`<option value="${escapeHtml(X)}">`).join("")),W(F.supplier_count)}catch(A){console.warn("fillCategoryDatalist failed",A)}};function W(A){const N=document.getElementById("drawer-cat-learned-tag");N&&A>0&&(N.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",A))}function G(){const A=document.getElementById("history-client-filter");if(!A)return;const N=A.value;A.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(V=>`<option value="${V.id}">${escapeHtml(V.name)}</option>`).join(""),A.value=N||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const A=document.querySelector(".cust-tab-bar");A&&A.addEventListener("click",ve=>{const de=ve.target.closest("[data-cust-tab]");de&&u(de.dataset.custTab)});const N=document.getElementById("btn-buyer-new");N&&N.addEventListener("click",()=>I(null));const V=document.getElementById("buyer-tbody");V&&V.addEventListener("click",ve=>{const de=ve.target.closest(".buyer-row-check");if(de){const xe=parseInt(de.dataset.cid,10);de.checked?i.add(xe):i.delete(xe);const Ae=de.closest(".cust-row");Ae&&Ae.classList.toggle("selected",de.checked),x();return}const Te=ve.target.closest(".cust-row-btn");if(Te){ve.stopPropagation();const xe=parseInt(Te.dataset.cid,10);if(Te.dataset.action==="edit"){const Ae=e.find(Va=>Va.id===xe);Ae&&I(Ae)}else Te.dataset.action==="export"&&$(xe);return}const We=ve.target.closest(".cust-row");if(We&&!ve.target.closest(".cust-cell-check")){const xe=e.find(Ae=>Ae.id===parseInt(We.dataset.cid,10));xe&&I(xe)}});const X=document.getElementById("buyer-check-all");X&&X.addEventListener("change",()=>{const{items:ve}=y();ve.forEach(de=>{X.checked?i.add(de.id):i.delete(de.id)}),g()});const oe=document.getElementById("buyer-batch-cancel");oe&&oe.addEventListener("click",T);const se=document.getElementById("buyer-batch-delete");se&&se.addEventListener("click",S);const ue=document.getElementById("buyer-prev");ue&&ue.addEventListener("click",()=>{s.page>0&&(s.page--,g())});const D=document.getElementById("buyer-next");D&&D.addEventListener("click",()=>{s.page++,g()});const O=document.getElementById("buyer-search");if(O){let ve;O.addEventListener("input",()=>{clearTimeout(ve),ve=setTimeout(()=>{s.keyword=O.value,s.page=0;const de=document.getElementById("buyer-search-clear");de&&(de.style.display=O.value?"":"none"),g()},200)})}const U=document.getElementById("buyer-search-clear");U&&U.addEventListener("click",()=>{const ve=document.getElementById("buyer-search");ve&&(ve.value=""),s.keyword="",s.page=0,U.style.display="none",g()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>v(null));const ae=document.getElementById("seller-tbody");ae&&ae.addEventListener("click",ve=>{const de=ve.target.closest("[data-saction]");if(!de)return;ve.stopPropagation();const Te=parseInt(de.dataset.wid,10),We=de.dataset.saction,xe=r.find(Ae=>Number(Ae.id)===Te);We==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(Te),b(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",xe?xe.name:""),"success")):We==="edit"?xe&&v(xe):We==="archive"&&(l=Te,C())});const le=document.getElementById("seller-search");if(le){let ve;le.addEventListener("input",()=>{clearTimeout(ve),ve=setTimeout(()=>{d.keyword=le.value;const de=document.getElementById("seller-search-clear");de&&(de.style.display=le.value?"":"none"),b()},200)})}const P=document.getElementById("seller-search-clear");P&&P.addEventListener("click",()=>{const ve=document.getElementById("seller-search");ve&&(ve.value=""),d.keyword="",P.style.display="none",b()});const z=document.getElementById("wsclient-modal-close");z&&z.addEventListener("click",E);const R=document.getElementById("wsclient-modal-cancel");R&&R.addEventListener("click",E);const Z=document.getElementById("wsclient-modal-save");Z&&Z.addEventListener("click",B);const K=document.getElementById("wsclient-modal-archive");K&&K.addEventListener("click",C);const ie=document.getElementById("wsclient-modal-mask");ie&&ie.addEventListener("click",ve=>{ve.target===ie&&E()});const fe=document.getElementById("client-modal-close");fe&&fe.addEventListener("click",k);const be=document.getElementById("client-modal-cancel");be&&be.addEventListener("click",k);const ke=document.getElementById("client-modal-save");ke&&ke.addEventListener("click",H);const Se=document.getElementById("client-modal-delete");Se&&Se.addEventListener("click",j);const Je=document.getElementById("client-modal-mask");Je&&Je.addEventListener("click",ve=>{ve.target===Je&&k()});const ft=document.getElementById("client-color-picker");ft&&ft.addEventListener("click",ve=>{const de=ve.target.closest(".color-swatch");de&&(ft.querySelectorAll(".color-swatch").forEach(Te=>Te.classList.remove("active")),de.classList.add("active"))});const Ye=document.getElementById("history-client-filter");Ye&&Ye.addEventListener("change",()=>{a=Ye.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>c(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Q={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0},te={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null},nt={batchLoading:!1};function ze(e,n){let a=t(e)||e;if(n)for(const o in n)a=a.replace(new RegExp("\\{"+o+"\\}","g"),String(n[o]));return a}function Gs(e){return e==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
    </svg>`}function Ks(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 19l5 5 13-13"/>
        <circle cx="20" cy="20" r="17"/>
    </svg>`}function Js(e){if(e==null)return"—";const n=parseFloat(e);return isNaN(n)?"—":"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function Ys(e){return e?e.slice(0,10):"—"}function Ze(e){if(e==null)return"—";const n=typeof e=="number"?e:parseFloat(String(e).replace(/,/g,""));return isNaN(n)?escapeHtml(String(e)):"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function Ws(e){if(!e)return"—";try{const n=new Date(e),a=o=>String(o).padStart(2,"0");return`${n.getFullYear()}-${a(n.getMonth()+1)}-${a(n.getDate())} ${a(n.getHours())}:${a(n.getMinutes())}`}catch{return e.slice(0,16).replace("T"," ")}}function Xs(e,n){if(n=n||{},e==="math_mismatch")return`
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(Ze(n.subtotal))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(Ze(n.vat))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(Ze(n.total_expected))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(Ze(n.total_actual))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(Ze(n.diff))}</span></div>
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
        `:e==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(n))}</span></div>`}function De(){const e=te.excRow;if(!e)return;const n=e.seller_name&&e.seller_name.trim()?e.seller_name:t("exc-no-seller"),a=e.filename||"—";document.getElementById("exc-drawer-title").textContent=a;const o="exc-status-"+(e.status||"pending"),s=t(o)||e.status,i="s-"+(e.status||"pending"),r=(e.invoice_date||e.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
        <span>${escapeHtml(n)}</span>
        ${e.invoice_no?`<span>· ${escapeHtml(e.invoice_no)}</span>`:""}
        ${r?`<span>· ${escapeHtml(r)}</span>`:""}
        <span class="exc-status-chip ${i}">${escapeHtml(s)}</span>
    `;const d=e.severity||"medium",l=t("exc-rule-"+e.rule_code)||e.rule_code,p=Xs(e.rule_code,e.detail||{}),f=jn(te.history),c=te.history===null,u=te.history&&te.history._err,m=new Set;e.rule_code==="math_mismatch"?(m.add("subtotal"),m.add("vat"),m.add("total_amount")):e.rule_code==="tax_id_format_invalid"?m.add("seller_tax"):e.rule_code==="amount_missing"&&(m.add("total_amount"),m.add("invoice_number"));const h=!!te.editing,_=te.editFields||{},w=(I,k,M)=>{if(c)return`<div class="exc-field-row"><label>${escapeHtml(t(k))}</label><span class="val empty">…</span></div>`;const H=h?_[I]!==void 0?_[I]:f[I]!==void 0&&f[I]!==null?f[I]:"":f[I],j=m.has(I)?"flagged":"";if(h){const F=M?"number":"text",W=M?' step="0.01" inputmode="decimal"':"",G=H==null?"":String(H).replace(/"/g,"&quot;");return`<div class="exc-field-row ${j} editing">
                <label>${escapeHtml(t(k))}</label>
                <input class="exc-field-input" type="${F}"${W} data-edit-key="${escapeHtml(I)}" value="${G}">
            </div>`}const $=M?Ze(H):H||"",q=H==null||H===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml($)}</span>`;return`<div class="exc-field-row ${j}"><label>${escapeHtml(t(k))}</label>${q}</div>`};let b="";u?b=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:b=`
            <div class="exc-fields">
                ${w("invoice_number","exc-fld-invoice-no",!1)}
                ${w("date","exc-fld-date",!1)}
                ${w("seller_name","exc-fld-seller",!1)}
                ${w("seller_tax","exc-fld-seller-tax",!1)}
                ${w("buyer_name","exc-fld-buyer",!1)}
                ${w("buyer_tax","exc-fld-buyer-tax",!1)}
                ${w("subtotal","exc-fld-subtotal",!0)}
                ${w("vat","exc-fld-vat",!0)}
                ${w("total_amount","exc-fld-total",!0)}
            </div>
        `;const v=(()=>{if(te.pdfStatus==="loading"||te.pdfStatus==="idle")return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M18 4v8a14 14 0 1014 14"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                </div>
            `;if(te.pdfStatus==="empty")return`
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
            `;if(te.pdfStatus==="error")return`
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
            `;const I=te.pdfUrl;return`
            <div class="exc-pdf-toolbar">
                <span class="exc-pdf-toolbar-title">${escapeHtml(a)}</span>
                <div class="exc-pdf-toolbar-actions">
                    <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${I}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M8 2h4v4M12 2L7 7"/>
                            <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                        </svg>
                    </a>
                    <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${I}" download="${escapeHtml(a)}" title="${escapeHtml(t("exc-pdf-download"))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                        </svg>
                    </a>
                </div>
            </div>
            <iframe class="exc-pdf-frame" src="${I}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
        `})();document.getElementById("exc-drawer-body").innerHTML=`
        <div class="exc-pdf-pane">${v}</div>
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
                    <div class="exc-why-rule">${escapeHtml(l)}</div>
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
                    ${e.status==="pending"&&!c&&!u?h?`
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
    `;const E=document.getElementById("exc-fld-edit");E&&E.addEventListener("click",()=>{te.editing=!0,te.editFields={...jn(te.history)},De()});const B=document.getElementById("exc-fld-cancel");B&&B.addEventListener("click",()=>{te.editing=!1,te.editFields=null,De()});const C=document.getElementById("exc-fld-save");C&&C.addEventListener("click",()=>ei()),document.querySelectorAll(".exc-field-input").forEach(I=>{I.addEventListener("input",()=>{te.editFields||(te.editFields={}),te.editFields[I.dataset.editKey]=I.value})});const y=document.getElementById("exc-pdf-retry");y&&te.openExcId&&y.addEventListener("click",()=>{te.excRow&&Ea(te.excRow.history_id,te.openExcId)});const g=e.status==="pending",x=!!(e.seller_name&&e.seller_name.trim()),T=document.getElementById("exc-btn-resolve"),S=document.getElementById("exc-btn-ignore");T.disabled=!g,S.disabled=!g||!x,S.title=x?t("exc-ignore-hint"):t("exc-ignore-no-seller")}function wn(){if(te.pdfUrl){try{URL.revokeObjectURL(te.pdfUrl)}catch{}te.pdfUrl=null}te.pdfStatus="idle"}async function Ea(e,n){te.pdfStatus="loading",De();try{const a=await fetch("/api/history/"+encodeURIComponent(e)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(te.openExcId!==n)return;if(a.status===404){te.pdfStatus="empty",De();return}if(!a.ok)throw new Error("http "+a.status);const o=await a.blob();if(te.openExcId!==n)return;wn(),te.pdfUrl=URL.createObjectURL(o),te.pdfStatus="ready",De()}catch(a){if(te.openExcId!==n)return;console.warn("loadDrawerPdf fail",a),te.pdfStatus="error",De()}}function Zs(e){const n=(Q.listCache||[]).find(a=>a.id===e);if(!n){showToast(t("exc-drawer-error"),"error");return}Q.listScrollY=window.scrollY||document.documentElement.scrollTop||0,wn(),te.editing=!1,te.editFields=null,te.openExcId=e,te.excRow=n,te.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),De(),Qs(n.history_id),Ea(n.history_id,e)}function lt(){wn(),te.editing=!1,te.editFields=null,te.openExcId=null,te.excRow=null,te.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const e=Q.listScrollY||0;e>0&&requestAnimationFrame(()=>window.scrollTo(0,e))}async function Qs(e){try{const n=await fetch("/api/history/"+encodeURIComponent(e),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);te.history=await n.json()}catch(n){console.warn("loadHistoryDetail fail",n),te.history={_err:!0}}te.excRow&&De()}function jn(e){if(!e||!e.pages)return{};const n=e.pages,a=n.find(o=>!o.is_duplicate&&!o.is_copy)||n[0];return a&&a.fields||{}}async function ei(){if(!te.openExcId||!te.history||!te.history.pages||te.loading)return;te.loading=!0;const e=showToast(t("exc-fld-saving"),"loading",0);try{const n=JSON.parse(JSON.stringify(te.history.pages||[]));let a=n.findIndex(l=>!l.is_duplicate&&!l.is_copy);a<0&&(a=0),n[a]||(n[a]={fields:{}});const o=n[a].fields||{},s=te.editFields||{},i=new Set(["subtotal","vat","total_amount"]),r={...o};for(const l in s){let p=s[l];if((p===""||p===void 0)&&(p=null),i.has(l)&&p!==null){const f=parseFloat(p);p=isNaN(f)?null:f}r[l]=p}n[a].fields=r;const d=await fetch("/api/history/"+encodeURIComponent(te.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:n})});if(!d.ok)throw new Error("http "+d.status);e(),showToast(t("exc-fld-save-ok"),"success"),lt(),await ut(),await Ne(),He()}catch(n){e(),console.warn("save fields fail",n),showToast(t("exc-fld-save-fail"),"error")}finally{te.loading=!1}}async function ti(){if(!(!te.openExcId||te.loading)){te.loading=!0;try{const e=await fetch("/api/exceptions/"+te.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-resolved"),"success"),lt(),await ut(),await Ne(),He()}catch(e){console.warn("resolve fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{te.loading=!1}}}async function ni(){if(!(!te.openExcId||te.loading)){te.loading=!0;try{const e=await fetch("/api/exceptions/"+te.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-ignored"),"success"),lt(),await ut(),await Ne(),He()}catch(e){console.warn("ignore fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{te.loading=!1}}}async function He(){try{const e=Q.currentClient||"",n="/api/exceptions/stats?status=pending"+(e?"&client_id="+encodeURIComponent(e):""),a=await fetch(n,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!a.ok)return;const o=await a.json(),s=document.getElementById("nav-exc-badge");if(!s)return;const i=parseInt(o.pending||0,10);i>0?(s.textContent=i>99?"99+":String(i),s.style.display=""):s.style.display="none"}catch{}}function Ba(e){document.getElementById("exc-kpi-pending").textContent=e.pending||0,document.getElementById("exc-kpi-high").textContent=e.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=e.resolved||0,document.getElementById("exc-kpi-learned").textContent=e.learned_rules||0;const n=document.getElementById("exc-status-tab-count-pending"),a=document.getElementById("exc-status-tab-count-resolved"),o=document.getElementById("exc-status-tab-count-ignored");n&&(n.textContent=e.pending||0),a&&(a.textContent=e.resolved||0),o&&(o.textContent=e.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(i=>{i.classList.toggle("active",i.dataset.status===(Q.currentStatus||"pending"))})}function kn(e){const n=document.getElementById("exc-chips");if(!n)return;const a=e.by_rule||{},o=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let i=`<button class="exc-chip ${!Q.currentRule?"active":""}" data-rule="">
        <span>${escapeHtml(t("exc-chip-all"))}</span>
        <span class="exc-chip-count">${e.pending||0}</span>
    </button>`;for(const r of o){const d=a[r]||0;if(d===0&&Q.currentRule!==r)continue;const l=Q.currentRule===r;i+=`<button class="exc-chip ${l?"active":""}" data-rule="${escapeHtml(r)}">
            <span>${escapeHtml(t("exc-chip-"+r))}</span>
            <span class="exc-chip-count">${d}</span>
        </button>`}n.innerHTML=i,n.querySelectorAll(".exc-chip").forEach(r=>{r.addEventListener("click",()=>{const d=r.dataset.rule||null;Q.currentRule=d,Ne()})})}function xn(e){const n=document.getElementById("exc-list");if(!n)return;if(!e||e.length===0){n.innerHTML=`<div class="exc-empty">
            ${Ks()}
            <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
            <div>${escapeHtml(t("exc-empty-desc"))}</div>
        </div>`,Dn();return}const a='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',o=(Q.currentStatus||"pending")==="pending";n.innerHTML=e.map(s=>{const i=s.severity||"medium",r=t("exc-rule-"+s.rule_code)||s.rule_code,d=s.seller_name&&s.seller_name.trim()?s.seller_name:t("exc-no-seller"),l=s.filename||"—",p=Ys(s.invoice_date||s.created_at),f=s.status==="pending",c=Q.selectedIds.has(s.id),u=o&&f;return`
            <div class="exc-row sev-${escapeHtml(i)} ${c?"selected":""}" data-exc-id="${escapeHtml(String(s.id))}">
                <div class="exc-row-check ${c?"checked":""}" data-check-id="${escapeHtml(String(s.id))}" ${u?"":'style="visibility:hidden;"'}>${a}</div>
                <div class="exc-row-sev">${Gs(i)}</div>
                <div class="exc-row-main">
                    <div class="exc-row-title">${escapeHtml(d)} · ${escapeHtml(l)}</div>
                    <div class="exc-row-meta">
                        ${s.invoice_no?`<span><b>${escapeHtml(s.invoice_no)}</b></span>`:""}
                        <span>${escapeHtml(p)}</span>
                    </div>
                </div>
                <div class="exc-row-rule r-${escapeHtml(i)}">${escapeHtml(r)}</div>
                <div class="exc-row-amount">${escapeHtml(Js(s.total_amount))}</div>
            </div>
        `}).join(""),n.querySelectorAll(".exc-row").forEach(s=>{s.addEventListener("click",i=>{if(i.target.closest(".exc-row-check"))return;const r=s.dataset.excId;r&&Zs(parseInt(r,10))})}),n.querySelectorAll(".exc-row-check").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation();const r=parseInt(s.dataset.checkId,10);r&&(Q.selectedIds.has(r)?(Q.selectedIds.delete(r),s.classList.remove("checked"),s.closest(".exc-row").classList.remove("selected")):(Q.selectedIds.add(r),s.classList.add("checked"),s.closest(".exc-row").classList.add("selected")),Pn())})}),Pn(),Dn()}function Pn(){const e=document.getElementById("exc-batch-bar"),n=document.getElementById("exc-batch-count");if(!e||!n)return;const a=Q.selectedIds.size;a===0?e.style.display="none":(e.style.display="",n.textContent=ze("exc-batch-count",{n:a}))}function Dn(){const e=document.getElementById("exc-list-foot"),n=document.getElementById("exc-list-count"),a=document.getElementById("exc-loadmore");if(!e||!n||!a)return;const o=Q.listCache.length;if(o===0){e.style.display="none";return}e.style.display="";let s=o;const i=Q.statsCache;i&&(Q.currentRule?s=(i.by_rule||{})[Q.currentRule]||o:s=i.pending||o),Q.total=s,n.textContent=ze("exc-list-count",{shown:o,total:s});const r=o<s&&o<500;a.style.display=r?"":"none"}async function ut(){try{if(navigator.onLine===!1)throw new Error("offline");const e=Q.currentClient||"",n=Q.currentStatus||"pending",a=new URLSearchParams;a.set("status",n),e&&a.set("client_id",e);const o="/api/exceptions/stats?"+a.toString(),s=await fetch(o,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!s.ok)throw new Error("http "+s.status);const i=await s.json();return Q.statsCache=i,Ba(i),kn(i),i}catch(e){return console.warn("loadExceptionsStats fail",e),null}}function ai(e){const n=document.getElementById("exc-list");if(!n)return;const a=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="18" cy="18" r="14"/>
        <line x1="18" y1="11" x2="18" y2="19"/>
        <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
    </svg>`,o=e?t("exc-offline"):t("exc-error-retry-title"),s=e?"":t("exc-error-retry-desc");n.innerHTML=`
        <div class="exc-error">
            ${a}
            <div class="exc-error-msg">${escapeHtml(o)}${s?" · "+escapeHtml(s):""}</div>
            <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
        </div>`;const i=document.getElementById("exc-retry-btn");i&&i.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function Ne(e){e=e||{};const n=!!e.append,a=document.getElementById("exc-list");!n&&a&&Q.listCache.length===0&&(a.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const o=new URLSearchParams;o.set("status",Q.currentStatus||"pending"),Q.currentRule&&o.set("rule_code",Q.currentRule),Q.currentClient&&o.set("client_id",Q.currentClient);const s=n?Q.listCache.length:0;o.set("limit",String(Q.pageSize)),o.set("offset",String(s));try{if(navigator.onLine===!1)throw new Error("offline");const i=await fetch("/api/exceptions/list?"+o.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!i.ok)throw new Error("http "+i.status);const d=(await i.json()).items||[];n?Q.listCache=Q.listCache.concat(d):(Q.listCache=d,Q.selectedIds.clear()),Q.loadFailed=!1,xn(Q.listCache),Q.statsCache&&kn(Q.statsCache)}catch(i){console.warn("loadExceptionsList fail",i),Q.loadFailed=!0;const r=navigator.onLine===!1||String(i.message||"").includes("offline");n?showToast(t("exc-toast-load-fail"),"error"):(ai(r),showToast(r?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function oi(){if(!Q.loading&&!(Q.listCache.length>=500)){Q.loading=!0;try{await Ne({append:!0})}finally{Q.loading=!1}}}function _n(){const e=document.getElementById("exc-client-filter");if(!e)return;const n=window._clientsCache||[],a=Q.currentClient||"",o=typeof t=="function"?t("history-client-all"):"全部客户";e.innerHTML=`<option value="">${escapeHtml(o)}</option>`+n.map(s=>`<option value="${s.id}">${escapeHtml(s.name)}</option>`).join(""),e.value=a}async function si(){if(nt.batchLoading)return;const e=Array.from(Q.selectedIds);if(e.length===0||!await showConfirm(ze("exc-batch-confirm-resolve",{n:e.length})))return;nt.batchLoading=!0;const a=showToast(ze("exc-batch-count",{n:e.length})+" …","loading",0);try{const o=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"resolve"})});if(!o.ok)throw new Error("http "+o.status);const s=await o.json();a(),showToast(ze("exc-toast-batch-resolved",{n:s.processed||0}),"success"),Q.selectedIds.clear(),await ut(),await Ne(),He()}catch(o){a(),console.warn("batch resolve fail",o),showToast(t("exc-toast-batch-fail"),"error")}finally{nt.batchLoading=!1}}async function ii(){if(nt.batchLoading)return;const e=Array.from(Q.selectedIds);if(e.length===0||!await showConfirm(ze("exc-batch-confirm-ignore",{n:e.length}),{danger:!1}))return;nt.batchLoading=!0;const a=showToast(ze("exc-batch-count",{n:e.length})+" …","loading",0);try{const o=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"ignore"})});if(!o.ok)throw new Error("http "+o.status);const s=await o.json();a(),showToast(ze("exc-toast-batch-ignored",{n:s.processed||0,wl:s.whitelist_added||0}),"success"),Q.selectedIds.clear(),await ut(),await Ne(),He()}catch(o){a(),console.warn("batch ignore fail",o),showToast(t("exc-toast-batch-fail"),"error")}finally{nt.batchLoading=!1}}function ri(){Q.selectedIds.clear(),xn(Q.listCache)}async function Ia(){const e=document.getElementById("learned-list");if(e){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const n=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);const o=(await n.json()).items||[];if(o.length===0){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const s=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
        </svg>`;e.innerHTML=o.map(i=>{const r=t("exc-rule-"+i.rule_code)||i.rule_code;return`
                <div class="learned-row" data-wl-id="${escapeHtml(String(i.id))}">
                    <div class="learned-seller" title="${escapeHtml(i.seller_name)}">${escapeHtml(i.seller_name)}</div>
                    <div class="learned-rule">${escapeHtml(r)}</div>
                    <div class="learned-date">${escapeHtml(Ws(i.created_at))}</div>
                    <button class="learned-del-btn" data-del-wl="${escapeHtml(String(i.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${s}</button>
                </div>
            `}).join("")}catch(n){console.warn("loadLearnedRules fail",n),e.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadExceptionsPage=async function(){if(!Q.loading){Q.loading=!0;try{_n(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await ut(),await Ne()}finally{Q.loading=!1}}};window.refreshExcBadge=He;window._refreshExcClientFilter=_n;window._excState=Q;window._rerenderExceptions=function(){try{_n()}catch{}Q.statsCache&&(Ba(Q.statsCache),kn(Q.statsCache)),Q.listCache&&Q.listCache.length&&xn(Q.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}te.openExcId&&De()};document.addEventListener("click",e=>{e.target.closest("#exc-drawer-close")&&lt(),e.target.closest("#exc-drawer-mask")&&lt(),e.target.closest("#exc-btn-resolve")&&ti(),e.target.closest("#exc-btn-ignore")&&ni(),e.target.closest("#exc-batch-resolve")&&si(),e.target.closest("#exc-batch-ignore")&&ii(),e.target.closest("#exc-batch-clear")&&ri(),e.target.closest("#exc-loadmore")&&oi()});document.addEventListener("keydown",e=>{e.key==="Escape"&&te.openExcId&&lt()});document.addEventListener("click",e=>{e.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),He())});document.addEventListener("change",e=>{if(!e.target.closest("#exc-client-filter"))return;const n=e.target;Q.currentClient=n.value||"",Q.currentRule=null,Q.selectedIds.clear(),Q.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),He()});document.addEventListener("click",e=>{const n=e.target.closest("#exc-status-tabs .exc-status-tab");if(!n)return;const a=n.dataset.status||"pending";a!==Q.currentStatus&&(Q.currentStatus=a,Q.currentRule=null,Q.selectedIds.clear(),Q.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())});window.addEventListener("online",()=>{Q.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()});setTimeout(He,1500);setInterval(He,6e4);window.loadLearnedRules=Ia;document.addEventListener("click",async e=>{const n=e.target.closest("[data-del-wl]");if(!n)return;const a=parseInt(n.dataset.delWl,10);if(!a)return;const o=n.closest(".learned-row"),s=o&&o.querySelector(".learned-seller"),i=s?s.textContent.trim():"",r=t("set-learned-del-confirm").replace("{seller}",i);if(await showConfirm(r,{danger:!0}))try{const l=await fetch("/api/exception-whitelist/"+a,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!l.ok)throw new Error("http "+l.status);showToast(t("set-learned-del-ok"),"success"),Ia(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(l){console.warn("delete whitelist fail",l),showToast(t("set-learned-del-fail"),"error")}});(function(){let e={items:[],q:"",cat:"",adapter:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(c){const u=typeof currentLang=="string"&&currentLang||window._currentLang||"th",m=c.error_friendly&&c.error_friendly[u];if(m)return m;if(typeof humanizeError=="function"&&c.error_msg)try{return humanizeError(c.error_msg)}catch{}return t("erp-exc-reason-"+(c.category||"other"))}function s(){const c=document.getElementById("erp-exc-batch");if(!c)return;const u=e.selected.size;c.hidden=u===0;const m=c.querySelector(".erp-exc-batch-count");m&&(m.textContent=String(u))}function i(){const c=document.getElementById("erp-exc-block");if(!c)return;const u=e;if(!(u.total>0||!!u.q||!!u.cat)){c.hidden=!0,c.innerHTML="";return}c.hidden=!1;const h=u.categories||{},_=Object.keys(h).reduce(($,q)=>$+h[q],0);let w=`<button class="erp-exc-chip ${u.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${_}</span></button>`;Object.keys(h).forEach($=>{w+=`<button class="erp-exc-chip ${u.cat===$?"active":""}" data-erpexc-cat="${escapeHtml($)}"><span>${escapeHtml(t("erp-exc-cat-"+$))}</span><span class="erp-exc-chip-count">${h[$]}</span></button>`});const b=u.items||[],v=b.length>0&&b.every($=>u.selected.has($.id)),E=b.map($=>{const q=$.state==="needs_action"?"needs":$.state==="retrying"?"retry":"fail",F=t("erp-exc-state-"+($.state||"failed")),W=o($),G=u.selected.has($.id)?"checked":"",A=$.push_type==="id_card",N=A?`<span class="erp-exc-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span> `:"",V=A?`<span class="ex-inv" title="${escapeHtml(t("erp-log-col-booking"))}">${N}${escapeHtml($.invoice_no||"—")}</span>`:`<span class="ex-inv" title="${escapeHtml($.invoice_no||"")}">${escapeHtml($.invoice_no||"—")}</span>`,X=A?`<span class="ex-seller" title="${escapeHtml(t("erp-log-col-customer"))}">${escapeHtml($.seller_name||"—")}</span>`:`<span class="ex-seller" title="${escapeHtml($.seller_name||"")}">${escapeHtml($.seller_name||"—")}</span>`,oe=A?`<span class="ex-buyer" title="${escapeHtml(t("erp-log-col-idcard"))}">${$.id_card_tail?"••••"+escapeHtml($.id_card_tail):"—"}</span>`:`<span class="ex-buyer" title="${escapeHtml($.ocr_buyer_name||"")}">${escapeHtml($.ocr_buyer_name||"—")}</span>`;return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml($.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml($.id)}" ${G}></span>
                ${V}
                ${X}
                ${oe}
                <span class="ex-state"><span class="erp-exc-state ${q}">${escapeHtml(F)}</span></span>
                <span class="ex-reason" title="${escapeHtml(W)}">${escapeHtml(W)}${$.error_code?` <span class="erp-exc-code">${escapeHtml($.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml($.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),B=b.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",C=b.length<u.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${b.length}/${u.total})</button>`:u.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:b.length,total:u.total}))}</div>`:"",L=u.adapter==="mrerp_dms",y=Array.isArray(window._erpEndpoints)?window._erpEndpoints:[],g=new Set;let x=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`;y.forEach($=>{const q=($&&$.adapter||"").toLowerCase();!q||g.has(q)||(g.add(q),x+=`<option value="${escapeHtml(q)}"${q===u.adapter?" selected":""}>${escapeHtml($&&$.name||q)}</option>`)});const T=L?t("erp-log-col-booking"):t("erp-exc-f-invoice"),S=L?t("erp-log-col-customer"):t("erp-exc-f-seller"),I=L?t("erp-log-col-idcard"):t("erp-exc-f-buyer");c.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${x}</select>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(u.q)}">
            </div>
            <div class="erp-exc-chips">${w}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${u.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${u.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${v?"checked":""}></span>
                    <span class="ex-inv">${escapeHtml(T)}</span>
                    <span class="ex-seller">${escapeHtml(S)}</span>
                    <span class="ex-buyer">${escapeHtml(I)}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${E}${B}
            </div>
            <div class="erp-exc-foot">${C}</div>`;const k=document.getElementById("erp-exc-search");if(k){if(u.focusSearch){k.focus();try{k.setSelectionRange(u.searchCaret,u.searchCaret)}catch{}}k.addEventListener("input",()=>{u.q=k.value,u.focusSearch=!0,u.searchCaret=k.selectionStart||k.value.length,clearTimeout(n),n=setTimeout(()=>l(!1),350)}),k.addEventListener("blur",()=>{u.focusSearch=!1})}c.querySelectorAll(".erp-exc-chip").forEach($=>{$.addEventListener("click",()=>{u.cat=$.dataset.erpexcCat||"",l(!1)})});const M=document.getElementById("erp-exc-erp-select");M&&M.addEventListener("change",()=>{u.adapter=M.value||"",l(!1)}),c.querySelectorAll("[data-erpexc-retry]").forEach($=>{$.addEventListener("click",q=>{q.stopPropagation(),r($.dataset.erpexcRetry,$)})}),c.querySelectorAll(".erp-exc-cb").forEach($=>{$.addEventListener("change",()=>{const q=$.dataset.erpexcCb;$.checked?u.selected.add(q):u.selected.delete(q);const F=document.getElementById("erp-exc-cb-all");F&&(F.checked=b.length>0&&b.every(W=>u.selected.has(W.id))),s()})});const H=document.getElementById("erp-exc-cb-all");H&&H.addEventListener("change",()=>{b.forEach($=>{H.checked?u.selected.add($.id):u.selected.delete($.id)}),c.querySelectorAll(".erp-exc-cb").forEach($=>{$.checked=H.checked}),s()}),c.querySelectorAll("[data-erpexc-batch]").forEach($=>{$.addEventListener("click",()=>d($.dataset.erpexcBatch))});const j=document.getElementById("erp-exc-more");j&&j.addEventListener("click",()=>l(!0)),c.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach($=>{$.addEventListener("click",q=>{q.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit($.dataset.erpexcId)})})}async function r(c,u){if(c){u&&(u.disabled=!0,u.textContent=t("erp-exc-retrying"));try{const m=await fetch("/api/erp/logs/"+encodeURIComponent(c)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),h=await m.json().catch(()=>({}));showToast(m.ok&&h.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),m.ok&&h.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(c),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function d(c){const u=Array.from(e.selected);if(c==="clear"){e.selected.clear(),i();return}if(u.length!==0){if(c==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:u.length}),{danger:!0}))return;try{const h=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,200)})}),_=await h.json().catch(()=>({}));showToast(h.ok?t("erp-exc-batch-delete-ok",{n:_.deleted||0}):t("erp-exc-retry-fail"),h.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(c==="retry")try{const m=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,50)})}),h=await m.json().catch(()=>({}));showToast(m.ok?t("erp-exc-batch-retry-ok",{ok:h.succeeded||0,fail:(h.failed||0)+(h.skipped||0)}):t("erp-exc-retry-fail"),m.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function l(c){const u=document.getElementById("erp-exc-block");if(!(!u||e.loading)){e.loading=!0;try{if(!Array.isArray(window._erpEndpoints)||!window._erpEndpoints.length)try{const b=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+a()}});if(b.ok){const v=await b.json();window._erpEndpoints=v&&(v.items||v)||[]}}catch{}const m=new URLSearchParams;e.q&&m.set("q",e.q),e.cat&&m.set("category",e.cat),e.adapter&&m.set("adapter",e.adapter),m.set("limit",String(e.pageSize)),m.set("offset",String(c?e.items.length:0));const h=await fetch("/api/erp/exceptions?"+m.toString(),{headers:{Authorization:"Bearer "+a()}});if(!h.ok){c||(u.hidden=!0);return}const _=await h.json(),w=_.items||[];e.items=c?e.items.concat(w):w,e.total=_.total||0,e.categories=_.categories||{},i()}catch{c||(u.hidden=!0)}finally{e.loading=!1}}}let p={};function f(){const c=document.getElementById("erp-exc-modal");c&&c.remove()}window._erpExcOpenEdit=function(c){const u=(e.items||[]).find(C=>String(C.id)===String(c));if(!u)return;const m=u.push_type==="id_card",h=!!u.history_client_id&&u.category==="customer_mismatch",_=u.category==="product_mismatch"&&!!u.history_id&&!!u.endpoint_id,w=o(u),b=u.state==="needs_action"?"needs":u.state==="retrying"?"retry":"fail",v=(C,L)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(C)}</span><span class="erp-exc-m-v">${escapeHtml(L||"—")}</span></div>`;let E="";if(h)E=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(_)E=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const C="erp-exc-edit-hint-"+(u.category||"other");let L=t(C);(!L||L===C)&&(L=w),E=`<div class="erp-exc-m-hint">${escapeHtml(L)}</div>`}const B=document.createElement("div");if(B.id="erp-exc-modal",B.className="erp-exc-modal-overlay",B.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${b}">${escapeHtml(t("erp-exc-state-"+(u.state||"failed")))}</span> ${escapeHtml(w)}${u.error_code&&!m?` <span class="erp-exc-code">${escapeHtml(u.error_code)}</span>`:""}</div>
                    ${v(m?t("erp-log-col-booking"):t("erp-exc-f-invoice"),u.invoice_no)}
                    ${v(m?t("erp-log-col-customer"):t("erp-exc-f-seller"),u.seller_name)}
                    ${m?v(t("erp-log-col-idcard"),u.id_card_tail?"••••"+u.id_card_tail:"—"):v(t("erp-exc-f-buyer"),u.ocr_buyer_name)+v(t("erp-exc-edit-field-current"),u.client_name)}
                    ${E}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${h?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${_?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(B),B.addEventListener("click",C=>{C.target===B&&f()}),document.getElementById("erp-exc-m-close").addEventListener("click",f),document.getElementById("erp-exc-m-cancel").addEventListener("click",f),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{f(),r(u.id,null)}),h){let C="";const L=document.getElementById("erp-exc-m-bind"),y=document.getElementById("erp-exc-m-custlist"),g=document.getElementById("erp-exc-m-search"),x=(S,I)=>{const k=(I||"").trim().toLowerCase(),M=k?S.filter(H=>(H.code||"").toLowerCase().includes(k)||(H.name||"").toLowerCase().includes(k)):S;if(M.length===0){y.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}y.innerHTML=M.slice(0,100).map(H=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(H.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(H.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(H.code||"")}</span>
                    </div>`).join(""),y.querySelectorAll(".erp-exc-m-cust").forEach(H=>{H.addEventListener("click",()=>{C=H.dataset.custCode||"",y.querySelectorAll(".erp-exc-m-cust").forEach(j=>j.classList.remove("sel")),H.classList.add("sel"),L&&(L.disabled=!C)})})},T=async()=>{const S=u.endpoint_id;if(p[S]){x(p[S],"");return}try{const I=await fetch("/api/erp/endpoints/"+encodeURIComponent(S)+"/customers",{headers:{Authorization:"Bearer "+a()}}),k=await I.json().catch(()=>({}));if(!I.ok||!k.ok){y.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const M=k.customers||[];p[S]=M,x(M,"")}catch{y.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};g&&g.addEventListener("input",()=>x(p[u.endpoint_id]||[],g.value)),T(),L&&L.addEventListener("click",async()=>{if(C){L.disabled=!0,L.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:u.history_client_id,erp_type:u.endpoint_adapter,erp_code:C})})).ok){showToast(t("erp-exc-retry-fail"),"error"),L.disabled=!1,L.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),f(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),L.disabled=!1,L.textContent=t("erp-exc-edit-bind-retry")}}})}if(_){const C=document.getElementById("erp-exc-m-bind-prod"),L=document.getElementById("erp-exc-m-prodlist"),y={};let g=[];const x=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+g.slice(0,500).map(I=>`<option value="${escapeHtml(I.code||"")}" data-pname="${escapeHtml(I.name||"")}">`+escapeHtml((I.name||"")+" · "+(I.code||""))+"</option>").join(""),T=I=>{if(!I.length){L.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}L.innerHTML=I.map(k=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(k)}">${escapeHtml(k)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(k)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${x()}</select>
                    </div>`).join(""),L.querySelectorAll(".erp-exc-m-prod-sel").forEach(k=>{k.addEventListener("change",()=>{const M=k.dataset.item,H=k.options[k.selectedIndex];k.value?y[M]={code:k.value,name:H&&H.dataset.pname||""}:delete y[M],C&&(C.disabled=Object.keys(y).length===0)})})};(async()=>{try{const k=await(await fetch("/api/history/"+encodeURIComponent(u.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),M=k&&k.pages||[],H=[],j={};(Array.isArray(M)?M:[]).forEach(F=>{const W=F&&F.fields&&F.fields.items||[];(Array.isArray(W)?W:[]).forEach(G=>{const A=(G&&(G.name||G.description)||"").trim();A&&!j[A]&&(j[A]=1,H.push(A))})});const $=await fetch("/api/erp/endpoints/"+encodeURIComponent(u.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),q=await $.json().catch(()=>({}));if(!$.ok||!q.ok){L.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}g=q.products||[],T(H)}catch{L.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),C&&C.addEventListener("click",async()=>{const I=Object.entries(y);if(I.length){C.disabled=!0,C.textContent=t("erp-exc-retrying");try{for(const[k,M]of I)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:u.endpoint_adapter,item_name:k,erp_code:M.code,erp_name:M.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),C.disabled=!1,C.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),f(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),C.disabled=!1,C.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=i,window.loadErpExceptions=l,window._erpExcState=e})();const li=`
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
`;we("cmdk-mask",li);(function(){function e(c){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||c&&c.id&&String(c.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var u=window._userInfo,m=!1,h=!0,_=!1,w=!1;u&&(m=typeof canManageTeam=="function"?canManageTeam(u):!!(u.role==="owner"||u.is_super_admin),h=typeof shouldHideMoney=="function"?shouldHideMoney(u):u.role==="member"&&!u.is_super_admin,_=typeof isSuperAdmin=="function"?isSuperAdmin(u):!!u.is_super_admin,w=e(u)),document.querySelectorAll("[data-show-if-team]").forEach(function(v){v.style.display=m?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(v){v.style.display=h?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(v){v.style.display=_?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(v){v.style.display=w?"":"none"});var b=_||w;document.querySelectorAll("[data-show-if-special]").forEach(function(v){v.style.display=b?"":"none"})},window.renderAvatarMenu=function(u){if(u){var m=document.getElementById("avatar-btn"),h=document.getElementById("avatar-popup-name"),_=document.getElementById("avatar-popup-email");if(!(!m||!h||!_)){var w=(u.username||"").trim(),b=w.split("@")[0]||w||"—",v=(w.charAt(0)||"?").toUpperCase(),E=(u.avatar_url||"").trim();if(E){var B=E.replace(/"/g,"&quot;"),C=v.replace(/'/g,"\\'");m.innerHTML='<img src="'+B+'" alt="'+v+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+C+`'">`}else m.textContent=v;h.textContent=b,_.textContent=w||"—",m.setAttribute("title",w||"")}}};function n(){var c=document.getElementById("avatar-wrap"),u=document.getElementById("avatar-btn"),m=document.getElementById("avatar-popup");if(!c||!u||!m)return;function h(){m.classList.remove("show"),u.setAttribute("aria-expanded","false")}function _(){m.classList.add("show"),u.setAttribute("aria-expanded","true")}u.addEventListener("click",function(w){w.stopPropagation(),m.classList.contains("show")?h():_()}),document.addEventListener("click",function(w){m.classList.contains("show")&&!c.contains(w.target)&&h()}),m.addEventListener("click",function(w){var b=w.target.closest(".avatar-popup-item");if(b){var v=b.dataset.action;switch(h(),v){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var E=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(E||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var B=document.getElementById("help-modal");B&&(B.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=h}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(c){return c.style.display!=="none"})}function o(c){var u=a();u.forEach(function(m){m.classList.remove("focus")}),u[c]&&(u[c].classList.add("focus"),u[c].scrollIntoView({block:"nearest"}))}function s(c){var u=a();if(u.length){var m=u.findIndex(function(_){return _.classList.contains("focus")});m<0&&(m=0);var h=(m+c+u.length)%u.length;o(h)}}function i(c){c=(c||"").toLowerCase().trim();var u=0,m=window._userInfo,h=typeof isSuperAdmin=="function"?isSuperAdmin(m):!!(m&&m.is_super_admin),_=e(m);document.querySelectorAll(".cmdk-item").forEach(function(b){if(b.dataset.showIfAdmin==="1"&&!h){b.style.display="none";return}if(b.dataset.showIfTest==="1"&&!_){b.style.display="none";return}var v=(b.dataset.cmdkText||b.textContent||"").toLowerCase(),E=!c||v.indexOf(c)>=0;b.style.display=E?"":"none",b.classList.remove("focus"),E&&u++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(b){for(var v=b.nextElementSibling,E=!1;v&&!v.hasAttribute("data-cmdk-section");){if(v.classList&&v.classList.contains("cmdk-item")&&v.style.display!=="none"){E=!0;break}v=v.nextElementSibling}b.style.display=E?"":"none"});var w=document.getElementById("cmdk-empty");w&&(w.style.display=u===0?"flex":"none"),o(0)}window.openCmdk=function(){var u=document.getElementById("cmdk-mask");u&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),u.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var m=document.getElementById("cmdk-input");m&&(m.value="",i(""),m.focus(),o(0))},50))},window.closeCmdk=function(){var u=document.getElementById("cmdk-mask");u&&u.classList.remove("show")};function r(c){if(c){if(c.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var u=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(u||"即将上线","info")}return}var m=c.dataset.cmdkRoute,h=c.dataset.cmdkAction;if(window.closeCmdk(),m){typeof routeTo=="function"&&routeTo(m);return}if(h){if(h==="open-admin"){window.location.href="/admin/cost";return}if(h.indexOf("lang-")===0){var _=h.slice(5);typeof applyLang=="function"&&applyLang(_)}}}}function d(){var c=document.getElementById("cmdk-mask"),u=document.getElementById("cmdk-input"),m=document.getElementById("cmdk-body");if(!(!c||!u||!m)){c.addEventListener("click",function(w){w.target===c&&window.closeCmdk()});var h=document.getElementById("cmdk-esc-btn");h&&h.addEventListener("click",function(){window.closeCmdk()}),u.addEventListener("input",function(w){i(w.target.value)}),u.addEventListener("keydown",function(w){w.key==="ArrowDown"?(w.preventDefault(),s(1)):w.key==="ArrowUp"?(w.preventDefault(),s(-1)):w.key==="Enter"?(w.preventDefault(),r(c.querySelector(".cmdk-item.focus"))):w.key==="Escape"&&(w.preventDefault(),window.closeCmdk())}),m.addEventListener("click",function(w){var b=w.target.closest(".cmdk-item");b&&r(b)}),m.addEventListener("mousemove",function(w){var b=w.target.closest(".cmdk-item");!b||b.style.display==="none"||b.classList.contains("cmdk-item-locked")||(a().forEach(function(v){v.classList.remove("focus")}),b.classList.add("focus"))});var _=document.getElementById("topbar-search");_&&(_.addEventListener("click",function(){window.openCmdk()}),_.addEventListener("keydown",function(w){(w.key==="Enter"||w.key===" ")&&(w.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(c){if((c.metaKey||c.ctrlKey)&&(c.key==="k"||c.key==="K")){c.preventDefault(),window.openCmdk();return}if(c.key==="Escape"){var u=document.getElementById("cmdk-mask");if(u&&u.classList.contains("show")){window.closeCmdk();return}var m=document.getElementById("avatar-popup");m&&m.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var l=(navigator.userAgent||"").toLowerCase(),p=l.indexOf("mac")>=0||l.indexOf("iphone")>=0||l.indexOf("ipad")>=0;p||document.body.classList.add("is-windows")}catch{}function f(){n(),d(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",f):f()})();(function(){function n(h){return String(h??"").replace(/[&<>"']/g,function(_){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[_]})}function a(h){if(!h||isNaN(h))return"";var _=Number(h);return _<1024?_+" B":_<1024*1024?(_/1024).toFixed(1)+" KB":(_/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(h){var _=h.target.closest&&h.target.closest(".recon-collapse-head");if(_&&!(h.target.closest("button")||h.target.closest("a"))){var w=_.closest(".recon-collapse");if(w){var b=w.getAttribute("data-collapsed")==="true";w.setAttribute("data-collapsed",b?"false":"true"),b&&(w.id==="vex-summary-collapse"&&f(),w.id==="vex-detail-collapse"&&c())}}}),document.addEventListener("keydown",function(h){if(!(h.key!=="Enter"&&h.key!==" ")){var _=h.target.closest&&h.target.closest(".recon-collapse-head");_&&(h.preventDefault(),_.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){l("vat"),l("gl")}function d(h){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(h)||[]}catch{}var _=document.getElementById(h==="vat"?"glv-vat-input":"glv-gl-input");return _&&_.files?Array.from(_.files):[]}function l(h){var _=document.getElementById(h==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(_){var w=d(h),b=h==="vat"?"glv-up-vat-title":"glv-up-gl-title",v=h==="vat"?"① 销项税报告":"② 总账 GL",E=window.t&&window.t(b)||v,B=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),C=n(window.t&&window.t("vex-preview-clear-all")||"全清"),L=o[h]||"",y=w.length;_.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(E)+' <span class="vex-pp-col-count">'+y+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+h+'" type="text" placeholder="'+B+'" value="'+n(L)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+h+'" type="button">'+C+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+h+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+h+'-pg"></div>';var g=document.getElementById("glv-pp-search-"+h);g&&g.addEventListener("input",function(T){o[h]=T.target.value,p(h)});var x=document.getElementById("glv-pp-clearall-"+h);x&&x.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(h)}),p(h)}}function p(h){var _=document.getElementById("glv-pp-"+h+"-list"),w=document.getElementById("glv-pp-"+h+"-pg");if(_){var b=d(h),v=(o[h]||"").toLowerCase(),E=b.map(function(L,y){return{f:L,i:y}}),B=v?E.filter(function(L){return L.f.name.toLowerCase().indexOf(v)>=0}):E;if(_.innerHTML=B.map(function(L){var y=L.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(y.name)+'">'+n(y.name)+'</span><span class="vex-pp-fi-size">'+a(y.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+h+'" data-idx="'+L.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),_.querySelectorAll(".vex-pp-fi-del").forEach(function(L){L.addEventListener("click",function(){var y=L.dataset.kind,g=parseInt(L.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(y,isNaN(g)?null:g)})}),w){var C=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";w.textContent=C.replace("{n}",B.length).replace("{m}",B.length)}}}function f(){var h=function(w,b){var v=document.getElementById(w);v&&(v.textContent=b==null?"—":String(b))},_=window._vexLastTask||{};h("vex-sum-total",_.total),h("vex-sum-matched",_.matched),h("vex-sum-diff",_.diff),h("vex-sum-incomplete",_.incomplete),h("vex-sum-cash",_.cash),document.getElementById("vex-summary-sub")}function c(){var h=window._vexLastTask&&window._vexLastTask.diff_rows||[],_=document.getElementById("vex-detail-tbody"),w=document.getElementById("vex-detail-table"),b=document.getElementById("vex-detail-empty");if(!(!_||!w||!b)){if(h.length===0){w.style.display="none",b.style.display="";return}b.style.display="none",w.style.display="";var v=h.map(function(B){return'<tr><td class="recon-detail-cell-mono">'+n(B.invoice_no||"")+"</td><td>"+n(B.field||"")+"</td><td>"+n(B.report_value||"")+"</td><td>"+n(B.invoice_value||"")+"</td><td>"+n(B.kind||"")+"</td></tr>"}).join("");_.innerHTML=v;var E=document.getElementById("vex-detail-sub");E&&(E.textContent=String(h.length))}}function u(){var h=document.getElementById("glv-toggle-preview");h&&!h._reconBound&&(h._reconBound=!0,h.addEventListener("click",function(){var _=document.getElementById("glv-preview-panel"),w=document.getElementById("glv-toggle-preview-label"),b=_&&_.style.display!=="none";_&&(_.style.display=b?"none":""),h.classList.toggle("open",!b),w&&(w.textContent=b?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),b||r()})),["glv-vat-input","glv-gl-input"].forEach(function(_){var w=document.getElementById(_);!w||w._reconWatched||(w._reconWatched=!0,w.addEventListener("change",function(){var b=document.getElementById("glv-preview-panel");b&&b.style.display!=="none"&&r()}))})}function m(){var h=document.getElementById("vex-summary-collapse"),_=document.getElementById("vex-detail-collapse");h&&(h.style.display=""),_&&(_.style.display=""),f(),c()}window._fillVexSummary=f,window._fillVexDetail=c,window._onVexResultShown=m,document.addEventListener("DOMContentLoaded",function(){u()}),setTimeout(u,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var h=document.getElementById("glv-preview-panel");h&&h.style.display!=="none"&&r();var _=document.getElementById("glv-toggle-preview-label"),w=document.getElementById("glv-toggle-preview");_&&w&&(_.textContent=w.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:f,fillVexDetail:c}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(d=>{d.addEventListener("click",()=>{i.forEach(u=>u.classList.remove("active")),d.classList.add("active");const l=d.dataset.reconTab,p=document.getElementById("recon-pane-bank"),f=document.getElementById("recon-pane-sale-vat"),c=document.getElementById("recon-pane-gl-vat");p&&(p.style.display=l==="bank"?"":"none"),f&&(f.style.display=l==="sale-vat"?"":"none"),c&&(c.style.display=l==="gl-vat"?"":"none"),l==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),l==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const d=document.createElement("button");return d.id="settings-modal-close",d.className="settings-modal-close",d.setAttribute("aria-label","close"),d.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(d,i.firstChild),d.addEventListener("click",s),r.addEventListener("click",l=>{l.target===r&&s()}),r}function o(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(l){console.warn("renderSettings:",l)}let d=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');d&&d.click()},50)}function s(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=D=>document.getElementById(D);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function i(D){return String(D??"").replace(/[&<>"']/g,O=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[O])}function r(D){return D<1024?D+" B":D<1024*1024?(D/1024).toFixed(1)+" KB":(D/1024/1024).toFixed(1)+" MB"}let d=[],l=[],p=!1,f=[],c=50,u=50,m="",h="";async function _(){try{const D=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!D.ok)return;const U=(await D.json()).kpi||{};[["vex-kpi-month-val",U.this_month],["vex-kpi-running-val",U.running],["vex-kpi-done-val",U.done],["vex-kpi-failed-val",U.failed]].forEach(([ne,ae])=>{const le=document.getElementById(ne);le&&(le.textContent=ae??0)})}catch{}}async function w(){try{const D=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!D.ok)return;const O=await D.json();B(O.rows||[])}catch{}}const b=10;var v=1;function E(){var D=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(v=1,B(f),!!D){var O=document.getElementById("vex-task-tbody");O&&O.querySelectorAll("tr").forEach(function(U){U.dataset.taskId&&(U.style.display=U.textContent.toLowerCase().indexOf(D)>=0?"":"none")})}}function B(D){f=D||f;const O=document.getElementById("vex-task-tbody");if(!O)return;if(!f.length){O.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",C(0);return}const U=Math.ceil(f.length/b);v>U&&(v=U);const ne=(v-1)*b;L(f.slice(ne,ne+b)),C(f.length)}function C(D){const O=document.getElementById("vex-task-pager"),U=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),ae=document.getElementById("vex-task-next");if(!O)return;if(D<=b){O.style.display="none";return}O.style.display="";const le=Math.ceil(D/b);U&&(U.textContent=v+" / "+le),ne&&(ne.disabled=v<=1),ae&&(ae.disabled=v>=le)}function L(D){const O=document.getElementById("vex-task-tbody");if(!O)return;const U={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},ae='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',le='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';O.innerHTML=D.map(P=>{const z=P.created_at?new Date(P.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",R=P.period||"—",Z=P.matched_count!=null?P.matched_count+" ✓ · "+P.mismatched_count+" ⚠":"—",K=P.mismatch_amount!=null?"฿ "+Number(P.mismatch_amount).toLocaleString():"—",ie=P.elapsed_seconds!=null?P.elapsed_seconds.toFixed(1)+" s":"—",fe=P.status||"pending",be=P.client_name&&P.client_name!=="client"?P.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${i(P.id)}" style="cursor:pointer">
                <td>${z}</td>
                <td>${i(be)}</td>
                <td>${i(R)}</td>
                <td>${(P.invoice_count||0)+" / "+(P.report_count||0)}</td>
                <td>${Z}</td>
                <td>${K}</td>
                <td><span class="badge ${ne[fe]||"badge-gray"}">${U[fe]||fe}</span></td>
                <td>${ie}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${i(P.id)}" title="${t("hist_export")||"导出"}">${ae}</button>
                    <button class="vex-task-del-btn" data-task-id="${i(P.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${le}</button>
                </div></td>
            </tr>`}).join(""),O.querySelectorAll(".vex-task-dl-btn").forEach(P=>{P.addEventListener("click",async z=>{z.stopPropagation();const R=P.dataset.taskId;try{const Z=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(R)+"/download",{credentials:"include",headers:s()});if(Z.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!Z.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const K=await Z.blob(),fe=(Z.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),be=fe?decodeURIComponent(fe[1]):"vat_recon_"+R+".xlsx",ke=URL.createObjectURL(K),Se=document.createElement("a");Se.href=ke,Se.download=be,Se.click(),setTimeout(()=>URL.revokeObjectURL(ke),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),O.querySelectorAll(".vex-task-del-btn").forEach(P=>{P.addEventListener("click",z=>{z.stopPropagation(),g(P.dataset.taskId)})}),E()}function y(){var D=document.getElementById("vex-task-prev"),O=document.getElementById("vex-task-next");D&&!D._vexBound&&(D._vexBound=!0,D.addEventListener("click",function(){v>1&&(v--,B())})),O&&!O._vexBound&&(O._vexBound=!0,O.addEventListener("click",function(){var U=Math.ceil(f.length/b);v<U&&(v++,B())}))}async function g(D){const O=t("vex-task-delete-confirm-title")||"删除对账任务?",U=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(U,{title:O,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const ae=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(D),{method:"DELETE",credentials:"include",headers:s()});if(!ae.ok)throw new Error(ae.status);showToast(t("vex-task-delete-ok")||"已删除","success"),w(),_()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function x(D){const O=window._currentLang||"th",U={zh:`已忽略 ${D} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${D} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${D} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${D} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(U[O]||U.th,"warn")}function T(D){const O=new Set(d.map(ne=>ne.name+"|"+ne.size));let U=0;for(const ne of D){if(!a.test(ne.name)){U++;continue}const ae=ne.name+"|"+ne.size;if(!O.has(ae)&&(O.add(ae),d.push(ne),d.length>=1e3))break}U>0&&x(U),d.length>1e3&&(d=d.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),M()}function S(D){const O=new Set(l.map(ne=>ne.name+"|"+ne.size));let U=0;for(const ne of D){if(!a.test(ne.name)){U++;continue}const ae=ne.name+"|"+ne.size;if(!O.has(ae)&&(O.add(ae),l.push(ne),l.length>=30))break}U>0&&x(U),l.length>30&&(l=l.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),M()}function I(D){d.splice(D,1),M()}function k(D){l.splice(D,1),M()}function M(){const D=o("vex-list-invoice"),O=o("vex-list-report"),U=o("vex-count-invoice"),ne=o("vex-count-report");U&&(U.textContent=d.length),ne&&(ne.textContent=l.length);const ae=(z,R,Z)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${i(z.name)}">${i(z.name)}</span>
            <span class="vex-fi-s">${r(z.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${Z}" data-vex-idx="${R}" aria-label="remove">×</button>
        </div>`;D&&(D.innerHTML=d.map((z,R)=>ae(z,R,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),O&&(O.innerHTML=l.map((z,R)=>ae(z,R,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(z=>{z.addEventListener("click",R=>{const Z=z.dataset.vexKind,K=parseInt(z.dataset.vexIdx,10);Z==="inv"?I(K):k(K)})});const le=d.length>0&&l.length>0;o("vex-build").disabled=!le||p;const P=o("vex-action-info");P&&(!d.length||!l.length?(P.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",P.className="vex-action-info muted"):(P.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",d.length).replace("{b}",l.length),P.className="vex-action-info ok")),q()}const H='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',j='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',$='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function q(){const D=o("vex-preview-panel");if(!D||D.style.display==="none")return;F("inv"),F("rep");const O=o("vex-pp-guide");O&&(O.style.display=d.length>100?"flex":"none")}function F(D){const O=o(D==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!O)return;const U=D==="inv"?d:l,ne=D==="inv"?m:h,ae=t(D==="inv"?"vex-preview-invoice":"vex-preview-report")||(D==="inv"?"销售发票":"VAT 报告"),le=i(t("vex-preview-search")||"搜索文件名..."),P=i(t("vex-preview-clear-all")||"全清");O.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${i(ae)} <span class="vex-pp-col-count">${U.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${D}" type="text"
                       placeholder="${le}" value="${i(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${D}" type="button">${P}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${D}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${D}-pg"></div>`;const z=o("vex-pp-search-"+D);z&&z.addEventListener("input",Z=>{D==="inv"?(m=Z.target.value,c=50):(h=Z.target.value,u=50),W(D)});const R=o("vex-pp-clearall-"+D);R&&R.addEventListener("click",()=>{D==="inv"?(d=[],m="",c=50):(l=[],h="",u=50),M()}),W(D)}function W(D){const O=o("vex-pp-"+D+"-list"),U=o("vex-pp-"+D+"-pg");if(!O)return;const ne=D==="inv"?d:l,ae=D==="inv"?m:h,le=D==="inv"?c:u,P=D==="inv"?H:j,z=ne.map((K,ie)=>({f:K,i:ie})),R=ae?z.filter(({f:K})=>K.name.toLowerCase().includes(ae.toLowerCase())):z,Z=R.slice(0,le);if(O.innerHTML=Z.map(({f:K,i:ie})=>`
            <div class="vex-pp-file-row">
                ${P}
                <span class="vex-pp-fi-name" title="${i(K.name)}">${i(K.name)}</span>
                <span class="vex-pp-fi-size">${r(K.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${D}" data-ridx="${ie}" aria-label="remove">${$}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${D}" style="height:1px;flex-shrink:0"></div>`,O.querySelectorAll(".vex-pp-fi-del").forEach(K=>{K.addEventListener("click",()=>{const ie=parseInt(K.dataset.ridx,10);K.dataset.kind==="inv"?I(ie):k(ie)})}),U){const K=t("vex-preview-count")||"显示前 {n} / 共 {m}";U.textContent=K.replace("{n}",Z.length).replace("{m}",R.length)}G(D,R.length)}function G(D,O){if((D==="inv"?c:u)>=O)return;const ne=o("vex-pp-sentinel-"+D),ae=o("vex-pp-"+D+"-list");if(!ne||!ae)return;const le=new IntersectionObserver(P=>{P[0].isIntersecting&&(le.disconnect(),D==="inv"?c+=50:u+=50,W(D))},{root:ae,threshold:.8});le.observe(ne)}function A(D,O,U,ne){const ae=o(D),le=o(O);!ae||!le||(ae.addEventListener("click",()=>le.click()),ae.addEventListener("keydown",P=>{(P.key==="Enter"||P.key===" ")&&(P.preventDefault(),le.click())}),ae.addEventListener("dragover",P=>{P.preventDefault(),ae.classList.add("drag-over")}),ae.addEventListener("dragleave",()=>ae.classList.remove("drag-over")),ae.addEventListener("drop",P=>{P.preventDefault(),ae.classList.remove("drag-over");const R=Array.from(P.dataTransfer.files).filter(Z=>a.test(Z.name));if(!R.length){showToast(t("vex-toast-bad-ext"),"error");return}U(R)}),le.addEventListener("change",()=>{const P=Array.from(le.files);U(P),le.value=""}))}async function N(){if(p||!d.length||!l.length)return;p=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var D=document.getElementById("vex-download");D&&(D.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(ae){var le=document.getElementById(ae);le&&(le.style.display="none")});const O=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",d.length).replace("{b}",l.length);const U=setInterval(()=>{const ae=Math.floor((Date.now()-O)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",ae).replace("{a}",d.length).replace("{b}",l.length)},1e3);try{const ae=new FormData;for(const de of d)ae.append("invoices",de);for(const de of l)ae.append("reports",de);const le=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";ae.append("lang",le);const P=localStorage.getItem("mrpilot_token")||"",z=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:ae});let R=null;try{R=await z.json()}catch{R=null}if(!z.ok||!R||!R.ok||!R.job_id)throw clearInterval(U),new Error(R&&R.detail||"HTTP "+z.status);const Z=o("vex-progress-sub"),K=await window._reconPollJob(R.job_id,P,{onProgress:de=>{Z&&(Z.textContent=window._reconProgressText(de,le))}});if(clearInterval(U),!K||K.status!=="done"||!K.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const ie=K.result_id;let fe=0;const be=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(ie)+"/download",{headers:s()});if(!be.ok)throw new Error("HTTP "+be.status);const Se=(be.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),Je=Se&&Se[1]||"vat_recon_"+Date.now()+".xlsx",ft=await be.blob(),Ye=URL.createObjectURL(ft),ve=o("vex-download");ve.href=Ye,ve.download=Je;try{const de=document.createElement("a");de.href=Ye,de.download=Je,document.body.appendChild(de),de.click(),setTimeout(()=>de.remove(),100)}catch{}o("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),ie&&(fe=await oe(ie)),window._onVexResultShown&&window._onVexResultShown(),fe>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",fe),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),_(),setTimeout(w,800)}catch(ae){clearInterval(U),o("vex-progress").style.display="none";const le=(t("vex-toast-fail")||"生成失败")+": "+(ae.message||ae);showToast(le,"error")}finally{p=!1,o("vex-build").disabled=!1}}function V(){d=[],l=[];var D=document.getElementById("vex-download");D&&(D.style.display="none"),M()}function X(D){if(D==null)return"—";var O=parseFloat(D);return isNaN(O)?"—":O.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function oe(D){try{var O=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(D),{headers:s()});if(!O.ok)throw new Error(O.status);var U=await O.json(),ne=U.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var ae=ne.rows||[],le=[];ae.forEach(function(R){R.kind==="invoice_orphan"?le.push({invoice_no:R.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:X(R.amount_inv),kind:R.kind}):R.kind==="report_orphan"?le.push({invoice_no:R.invoice_no||"",field:"仅报告有",report_value:X(R.amount_rep),invoice_value:"—",kind:R.kind}):R.dims&&Object.keys(R.dims).length>0&&Object.keys(R.dims).forEach(function(Z){var K=String(R.dims[Z]||""),ie=K.split(" ≠ ");le.push({invoice_no:R.invoice_no||"",field:Z,report_value:ie[0]||K,invoice_value:ie.length>1?ie[1]:"—",kind:"diff"})})});var P=ae.filter(function(R){return R.kind==="matched_cash"}).length,z=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:z,cash:P,diff_rows:le,task_id:D},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),z}catch{return 0}}function se(){const D=document.getElementById("vex-pane");D&&D.querySelectorAll("[data-i18n]").forEach(O=>{const U=t(O.dataset.i18n);U&&(O.textContent=U)}),M(),w()}function ue(){A("vex-drop-invoice","vex-input-invoice",T),A("vex-drop-report","vex-input-report",S);const D=o("vex-build"),O=o("vex-reset");D&&D.addEventListener("click",N),O&&O.addEventListener("click",V),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(ae=>{ae.addEventListener("click",()=>{_(),w()})}),y();const U=document.getElementById("vex-task-search");U&&U.addEventListener("input",E);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const ae=o("vex-preview-panel"),le=o("vex-toggle-preview-label"),P=ae&&ae.style.display!=="none";ae&&(ae.style.display=P?"none":""),ne&&ne.classList.toggle("open",!P),le&&(le.textContent=P?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),P||q()}),M(),_()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):ue(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",se),window.subscribeI18n("vex-preview-panel",q))})();const ce={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},re=e=>document.getElementById(e),La=()=>localStorage.getItem("mrpilot_token")||"",ct=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",Ke=()=>({Authorization:"Bearer "+La()}),qn={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},ge=e=>(qn[ct()]||qn.th)[e]||e;function ci(e){const n=ct(),o={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[e];return o?o[n]||o.th||o.en:ge("error")||"Error"}const wt=e=>e==null||isNaN(e)?"":Number(e).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function En(e){re("glv-kpi-matched")&&(re("glv-kpi-matched").textContent=e&&e.matched!=null?e.matched:"—"),re("glv-kpi-diff")&&(re("glv-kpi-diff").textContent=e&&e.diff!=null?e.diff:"—"),re("glv-kpi-unmatched")&&(re("glv-kpi-unmatched").textContent=e&&e.unmatched!=null?e.unmatched:"—")}function di(e){if(!e)return"";try{const n=new Date(e);if(isNaN(n.getTime()))return e;const a=o=>String(o).padStart(2,"0");return n.getFullYear()+"-"+a(n.getMonth()+1)+"-"+a(n.getDate())+" "+a(n.getHours())+":"+a(n.getMinutes())}catch{return e}}function Rn(e,n,a,o){const s=re(e),i=re(n),r=re(a);if(!s||!i||!r)return;const d=l=>{if(!l||!l.length)return;const p=Array.isArray(ce[o])?ce[o].slice():[],f=new Set(p.map(c=>c.name+"|"+c.size));for(const c of l){if(!c)continue;const u=c.name+"|"+c.size;f.has(u)||(p.push(c),f.add(u))}ce[o]=p,Ca(r,p),Bt(),Lt(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};s.addEventListener("click",()=>i.click()),s.addEventListener("keydown",l=>{(l.key==="Enter"||l.key===" ")&&(l.preventDefault(),i.click())}),i.addEventListener("change",()=>{d(Array.from(i.files||[])),i.value=""}),s.addEventListener("dragover",l=>{l.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",()=>s.classList.remove("drag-over")),s.addEventListener("drop",l=>{l.preventDefault(),s.classList.remove("drag-over");const p=l.dataTransfer&&l.dataTransfer.files?Array.from(l.dataTransfer.files):[];d(p)})}function Ca(e,n){if(!e)return;if(!n||n.length===0){e.textContent="";return}const a=n.reduce((o,s)=>o+Math.round(s.size/1024),0);if(n.length===1)e.textContent=n[0].name+"  ("+a+" KB)";else{const o=window.t&&window.t("glv-files-count")||"{n} 个文件";e.textContent=o.replace("{n}",n.length)+"  ("+a+" KB)"}}function Fe(e){const n=ce[e];return Array.isArray(n)?n:n?[n]:[]}function Bt(){const e=re("btn-glv-run");if(!e)return;const n=Fe("glFile").length>0&&Fe("vatFile").length>0;e.disabled=!n||ce.running}function Lt(){const e=re("glv-status");if(!e||ce.running)return;const n=Fe("vatFile").length,a=Fe("glFile").length;n===0&&a===0?(e.className="vex-action-info muted",e.innerHTML="<span>"+ge("hint_need_both")+"</span>"):n>0&&a>0?(e.className="vex-action-info ok",e.innerHTML="<span>"+ge("hint_ready")+"</span>"):(e.className="vex-action-info muted",e.innerHTML="<span>"+ge("hint_need_one_more")+"</span>")}function pi(e,n){const a=e==="vat"?"vatFile":"glFile",o=e==="vat"?"glv-vat-input":"glv-gl-input",s=e==="vat"?"glv-vat-name":"glv-gl-name",i=Fe(a);n==null?ce[a]=[]:ce[a]=i.filter((d,l)=>l!==n);const r=re(o);r&&(r.value=""),Ca(re(s),Fe(a)),Bt(),Lt(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function ui(){ce.glFile=[],ce.vatFile=[],ce.currentTaskId=null,ce.lastDetail=[],ce.lastSummary=null;const e=re("glv-vat-input");e&&(e.value="");const n=re("glv-gl-input");n&&(n.value="");const a=re("glv-vat-name");a&&(a.textContent="");const o=re("glv-gl-name");o&&(o.textContent="");const s=re("glv-result");s&&(s.style.display="none");const i=re("glv-kpi-strip");i&&(i.style.display="none"),Bt(),Lt(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function Bn(e){const n=re("glv-tbody");if(!n)return;vi(e.length),n.innerHTML="";const a=ge("not_found"),o=document.createDocumentFragment();e.forEach(s=>{const i=document.createElement("tr"),r=(c,u)=>{const m=document.createElement("td");return u&&(m.className=u),m.textContent=c,m},d=s.gl_amount===null||s.gl_amount===void 0,l=s.diff;let p="glv-num",f="glv-num";d?(f+=" glv-cell-missing",p+=" glv-cell-missing"):Math.abs(l||0)<.005?p+=" glv-cell-ok":p+=" glv-cell-diff",i.appendChild(r(s.doc_no||"","glv-doc")),i.appendChild(r(s.date||"","")),i.appendChild(r(s.customer_name||"","")),i.appendChild(r(wt(s.vat_amount),"glv-num")),i.appendChild(r(d?a:wt(s.gl_amount),f)),i.appendChild(r(d?a:wt(s.diff),p)),i.appendChild(r(s.account_codes||"","glv-doc")),o.appendChild(i)}),n.appendChild(o)}function In(e){const n=re("glv-summary-table")&&re("glv-summary-table").querySelector("tbody");if(!n)return;n.innerHTML="",[{label:ge("s_gl_total"),amount:e.gl_total,emph:!0,items:[],negate:!1},{label:ge("s_minus_gl_cr"),amount:-(e.gl_only_credit||0),emph:!1,items:e.gl_only_credit_items||[],negate:!0},{label:ge("s_plus_gl_dr"),amount:e.gl_only_debit||0,emph:!1,items:e.gl_only_debit_items||[],negate:!1},{label:ge("s_plus_vat_p"),amount:e.vat_only_positive||0,emph:!1,items:e.vat_only_positive_items||[],negate:!1},{label:ge("s_minus_vat_n"),amount:e.vat_only_negative||0,emph:!1,items:e.vat_only_negative_items||[],negate:!1},{label:ge("s_vat_total"),amount:e.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:o,amount:s,emph:i,items:r,negate:d})=>{const l=document.createElement("tr");l.className=i?"glv-summary-total":"glv-summary-sect";const p=document.createElement("td"),f=document.createElement("td");p.textContent=o,f.textContent=i?wt(s):"",l.appendChild(p),l.appendChild(f),n.appendChild(l),(r||[]).forEach(c=>{const u=document.createElement("tr");u.className="glv-summary-item";const m=document.createElement("td"),h=document.createElement("td"),_=[c.doc_no,c.date,c.name].filter(Boolean);m.textContent="· "+_.join("  ·  ");const w=d?-(c.amount||0):c.amount||0;h.textContent=wt(w),u.appendChild(m),u.appendChild(h),n.appendChild(u)})})}async function fi(e){try{const a=await(await fetch("/api/recon/gl-vat/"+e,{headers:Ke()})).json();if(!a||!a.ok)throw new Error("load_failed");ce.currentTaskId=e,ce.lastDetail=a.detail||[],ce.lastSummary=a.summary||{},En(a.stats||{}),Bn(ce.lastDetail),In(ce.lastSummary);const o=re("glv-result");o&&(o.style.display=""),Sa(),window.scrollTo({top:o?o.offsetTop-80:0,behavior:"smooth"})}catch(n){console.error("[gl-vat] load task failed:",n),alert(ge("error")+": "+(n.message||n))}}function Sa(){var e=re("glv-kpi-strip");e&&(e.style.display="");var n=re("glv-section-summary");n&&n.setAttribute("data-collapsed","false");var a=re("glv-section-detail");a&&a.setAttribute("data-collapsed","false")}function mi(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(e=>{const n=e.getAttribute("data-toggle"),a=document.getElementById(n);if(!a)return;const o=s=>{if(s.target&&s.target.closest("button")!==null&&!s.target.classList.contains("glv-section-head"))return;const i=a.getAttribute("data-collapsed")==="true";a.setAttribute("data-collapsed",i?"false":"true")};e.addEventListener("click",o),e.addEventListener("keydown",s=>{(s.key==="Enter"||s.key===" ")&&(s.preventDefault(),o(s))})})}function vi(e){const n=re("glv-detail-count");n&&(n.textContent=e!=null?String(e):"")}const ht=10;var Qe=[],Ie=1;function hi(){Ie=1,Pt();var e=((re("glv-hist-search")||{}).value||"").trim().toLowerCase();if(e){var n=re("glv-history-tbody");n&&n.querySelectorAll("tr").forEach(function(a){a.dataset.taskId&&(a.style.display=a.textContent.toLowerCase().indexOf(e)>=0?"":"none")})}}function Pt(){const e=re("glv-history-table-wrap"),n=re("glv-history-empty"),a=re("glv-history-tbody"),o=re("glv-history-pager"),s=re("glv-history-pager-info"),i=re("glv-history-prev"),r=re("glv-history-next");if(!a)return;if(a.innerHTML="",!Qe.length){e&&(e.style.display="none"),n&&(n.style.display=""),o&&(o.style.display="none");return}e&&(e.style.display=""),n&&(n.style.display="none");const d=Math.ceil(Qe.length/ht);Ie>d&&(Ie=d);const l=(Ie-1)*ht,p=Qe.slice(l,l+ht);o&&(o.style.display=Qe.length>ht?"":"none",s&&(s.textContent=Ie+" / "+d),i&&(i.disabled=Ie<=1),r&&(r.disabled=Ie>=d)),p.forEach(c=>{const u=document.createElement("tr");u.dataset.taskId=c.id;const m=document.createElement("td");m.textContent=di(c.created_at);const h=document.createElement("td");h.className="glv-history-file",h.title=(c.vat_filename||"")+" + "+(c.gl_filename||""),h.textContent=(c.vat_filename||"?")+" + "+(c.gl_filename||"?");const _=document.createElement("td");_.className="glv-num",_.textContent=(c.vat_row_count||0)+" / "+(c.gl_row_count||0);const w=document.createElement("td");w.className="glv-num",w.textContent=c.matched_count||0;const b=document.createElement("td");b.className="glv-num",b.textContent=c.diff_count||0;const v=document.createElement("td");v.className="glv-num",v.textContent=c.unmatched_count||0;const E=document.createElement("td");E.className="glv-history-actions";const B=(g,x,T,S)=>{const I=document.createElement("button");return I.type="button",T&&(I.className=T),I.title=x,I.setAttribute("aria-label",x),I.innerHTML=g,I.onclick=S,I},C='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',L='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',y='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';E.appendChild(B(C,ge("hist_load"),"",()=>fi(c.id))),E.appendChild(B(L,ge("hist_export"),"",()=>bi(c.id))),E.appendChild(B(y,ge("hist_delete"),"glv-del",()=>yi(c.id))),[m,h,_,w,b,v,E].forEach(g=>u.appendChild(g)),a.appendChild(u)})}function gi(){var e=re("glv-history-prev"),n=re("glv-history-next");e&&!e._glvBound&&(e._glvBound=!0,e.addEventListener("click",function(){Ie>1&&(Ie--,Pt())})),n&&!n._glvBound&&(n._glvBound=!0,n.addEventListener("click",function(){var a=Math.ceil(Qe.length/ht);Ie<a&&(Ie++,Pt())}))}async function at(){try{const n=await(await fetch("/api/recon/gl-vat/tasks",{headers:Ke()})).json();Qe=n&&n.tasks||[],Ie=1,Pt(),gi()}catch(e){console.error("[gl-vat] history load failed:",e)}}async function bi(e){try{const n="/api/recon/gl-vat/"+e+"/export?lang="+encodeURIComponent(ct()),a=await fetch(n,{headers:Ke()});if(!a.ok)throw new Error("HTTP "+a.status);const o=await a.blob(),s=document.createElement("a");s.href=URL.createObjectURL(o),s.download="GL_VAT_recon_"+e+".xlsx",document.body.appendChild(s),s.click(),setTimeout(()=>{URL.revokeObjectURL(s.href),s.remove()},200)}catch(n){console.error("[gl-vat] exportTask failed:",n),typeof showToast=="function"&&showToast(ge("error")+": "+(n.message||n),"error")}}async function yi(e){let n;if(typeof window.showConfirm=="function"?n=await window.showConfirm(ge("confirm_delete"),{danger:!0}):n=confirm(ge("confirm_delete")),!!n)try{const a=await fetch("/api/recon/gl-vat/"+e,{method:"DELETE",headers:Ke()});if(!a.ok)throw new Error("HTTP "+a.status);at()}catch(a){console.error("[gl-vat] delete failed:",a),typeof showToast=="function"&&showToast(ge("error")+": "+(a.message||a),"error")}}async function wi(){if(!ce.glFile||!ce.vatFile){typeof showToast=="function"&&showToast(ge("need_files"),"warn");return}ce.running=!0,Bt();const e=re("glv-status"),n=re("glv-progress"),a=re("glv-progress-sub");e&&(e.className="vex-action-info muted",e.style.color="",e.innerHTML="<span>"+ge("running")+"</span>"),n&&(n.style.display=""),a&&(a.textContent=(ce.vatFile.name||"VAT")+" + "+(ce.glFile.name||"GL"));const o=new FormData,s=Fe("vatFile"),i=Fe("glFile");for(const d of s)o.append("vat_files",d,d.name);for(const d of i)o.append("gl_files",d,d.name);const r=(re("glv-prefix")&&re("glv-prefix").value||"4").trim()||"4";o.append("revenue_prefix",r),o.append("lang",ct());try{const d=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:Ke(),body:o});let l=null;try{l=await d.json()}catch{l=null}if(!d.ok||!l||!l.ok||!l.job_id)throw new Error(l&&l.detail||l&&l.error||"HTTP "+d.status);const p=re("glv-progress-sub"),f=await window._reconPollJob(l.job_id,La(),{onProgress:h=>{p&&(p.textContent=window._reconProgressText(h,ct()))}});if(!f||f.status!=="done"||!f.result_id)throw f&&f.status==="failed"&&f.error_code?new Error(ci(f.error_code)):new Error(ge("error")||"Error");const c=await fetch("/api/recon/gl-vat/"+encodeURIComponent(f.result_id),{headers:Ke()});let u=null;try{u=await c.json()}catch{u=null}if(!c.ok||!u||!u.ok)throw new Error(u&&u.detail||u&&u.error||"HTTP "+c.status);ce.currentTaskId=u.task_id,ce.lastDetail=u.detail||[],ce.lastSummary=u.summary||{},En(u.stats||{}),Bn(ce.lastDetail),In(ce.lastSummary);const m=re("glv-result");m&&(m.style.display=""),Sa(),e&&(e.className="vex-action-info ok",e.style.color="",e.innerHTML="<span>"+ge("done")+" · GL "+(u.gl_row_count||0)+" · VAT "+(u.vat_row_count||0)+"</span>"),at()}catch(d){console.error("[gl-vat] run failed:",d),e&&(e.className="vex-action-info",e.style.color="#ef4444",e.innerHTML="<span>"+ge("error")+": "+(d.message||d)+"</span>")}finally{ce.running=!1,n&&(n.style.display="none"),Bt()}}async function ki(){if(ce.currentTaskId)try{const e="/api/recon/gl-vat/"+ce.currentTaskId+"/export?lang="+encodeURIComponent(ct()),n=await fetch(e,{headers:Ke()});if(!n.ok)throw new Error("HTTP "+n.status);const a=await n.blob(),o=document.createElement("a");o.href=URL.createObjectURL(a),o.download="GL_VAT_recon_"+ce.currentTaskId+".xlsx",document.body.appendChild(o),o.click(),setTimeout(()=>{URL.revokeObjectURL(o.href),o.remove()},200)}catch(e){console.error("[gl-vat] export failed:",e),typeof showToast=="function"&&showToast(ge("error")+": "+(e.message||e),"error")}}function xi(){ce.running||Lt(),at(),ce.lastDetail&&ce.lastDetail.length&&Bn(ce.lastDetail),ce.lastSummary&&In(ce.lastSummary)}function _i(){if(ce.inited){at();return}ce.inited=!0,Rn("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),Rn("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const e=re("btn-glv-run");e&&e.addEventListener("click",wi);const n=re("btn-glv-export");n&&n.addEventListener("click",ki);const a=re("btn-glv-reset");a&&a.addEventListener("click",ui);const o=re("glv-hist-search");o&&o.addEventListener("input",hi),mi(),En(null),Lt(),window._loadGlvHistory=at,at(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",xi)}window._glvRemoveFile=pi;window.GlVatRecon={ensureInit:_i};window._glvPreviewFiles=function(e){return Fe(e==="vat"?"vatFile":"glFile")};(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let i={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function r(){const S=typeof _userInfo<"u"?_userInfo:null;return!!(S&&(S.role==="owner"||S.is_super_admin))}function d(){const S=typeof _userInfo<"u"?_userInfo:null;return!!(S&&S.id===s)}function l(S){return typeof escapeHtml=="function"?escapeHtml(S==null?"":String(S)):String(S??"")}function p(S,I){try{typeof showToast=="function"&&showToast(S,I||"info")}catch{}}async function f(S,I){const k=localStorage.getItem("mrpilot_token");if(k&&!(i.loaded[S]&&!I))try{const M=await fetch("/api/erp/mappings/"+S,{headers:{Authorization:"Bearer "+k}});if(!M.ok)throw new Error("http_"+M.status);const H=await M.json();i.items[S]=H.items||[],i.loaded[S]=!0}catch{i.items[S]=[],i.loaded[S]=!1}}async function c(S){if(i.clientLoaded)return;const I=localStorage.getItem("mrpilot_token");if(I)try{const k=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+I}});if(!k.ok)throw new Error("http_"+k.status);const M=await k.json();i.clientList=(M.clients||M.items||[]).filter(H=>H.is_active!==!1),i.clientLoaded=!0}catch{i.clientList=[]}}function u(){const S=document.getElementById("erp-map-pane-wrap");if(!S)return;const I=!r();let k="";I&&(k+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+l(t("erp-map-readonly-tip"))+"</div>"),k+='<div class="erp-map-toolbar">',!I&&i.sub!=="products"&&(k+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+l(t("erp-map-add-row"))+"</button>"),k+="</div>",k+='<div class="erp-map-table" id="erp-map-table-host"></div>',S.innerHTML=k,m();const M=document.getElementById("erp-map-dev-bar");M&&(M.style.display=r()&&d()?"":"none")}function m(){const S=document.getElementById("erp-map-table-host");if(!S)return;const I=i.sub,k=i.items[I]||[],M=i.addingNew[I],H=!r();if(!k.length&&!M){S.innerHTML='<div class="erp-map-empty"><strong>'+l(t("erp-map-empty-"+I))+"</strong>"+l(t("erp-map-empty-"+I+"-sub"))+"</div>";return}let j="";j+=h(I),M&&!H&&(j+=E(I)),k.forEach(function($){j+=B(I,$,H)}),S.innerHTML=j}function h(S){return S==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+l(t("erp-map-col-client"))+"</div><div>"+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":S==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-category"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":S==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+l(t("erp-map-col-item-name"))+"</div><div>"+l(t("erp-map-col-erp-product-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-tax"))+"</div><div>"+l(t("erp-map-col-erp-tax-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>"}function _(S,I){let k='<select class="form-input" data-erp-field="'+I+'">';return k+='<option value="">'+l(t("erp-map-pick-erp"))+"</option>",e.forEach(function(M){const H=M===S?" selected":"";k+='<option value="'+M+'"'+H+">"+l(n[M])+"</option>"}),k+="</select>",k}function w(S){let I='<select class="form-input" data-erp-field="client_id">';return I+='<option value="">'+l(t("erp-map-pick-client"))+"</option>",(i.clientList||[]).forEach(function(k){const M=String(k.id)===String(S)?" selected":"";I+='<option value="'+k.id+'"'+M+">"+l(k.name||"#"+k.id)+"</option>"}),I+="</select>",I}function b(S){let I='<select class="form-input" data-erp-field="pearnly_category">';return I+='<option value="">'+l(t("erp-map-pick-cat"))+"</option>",a.forEach(function(k){const M=k===S?" selected":"";I+='<option value="'+k+'"'+M+">"+l(t("erp-map-cat-"+k))+"</option>"}),I+="</select>",I}function v(S){let I='<select class="form-input" data-erp-field="pearnly_tax_kind">';return I+='<option value="">'+l(t("erp-map-pick-tax"))+"</option>",o.forEach(function(k){const M=k===S?" selected":"";I+='<option value="'+k+'"'+M+">"+l(t("erp-map-tax-"+k))+"</option>"}),I+="</select>",I}function E(S){const I='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+l(t("erp-map-save"))+"</button>";return S==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+l(t("erp-map-col-client"))+'">'+w("")+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+_("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+I+"</div></div>":S==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+_("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-category"))+'">'+b("")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+l(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+l(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+I+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+_("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-tax"))+'">'+v("")+'</div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+I+"</div></div>"}function B(S,I,k){const M=k?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+l(I.id)+'" title="'+l(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',H='<span class="erp-map-erp-badge">'+l(n[I.erp_type]||I.erp_type)+"</span>";if(S==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+l(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+l(I.client_name||"#"+I.client_id)+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+H+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(I.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(I.notes||"")+"</div><div>"+M+"</div></div>";if(S==="accounts"){const $=t("erp-map-cat-"+(I.pearnly_category||"other"))||I.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+l(t("erp-map-col-erp"))+'">'+H+'</div><div data-label="'+l(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+l($)+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(I.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(I.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(I.notes||"")+"</div><div>"+M+"</div></div>"}if(S==="products")return'<div class="erp-map-row row-products"><div data-label="'+l(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+l(I.item_name||"")+'</div><div data-label="'+l(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+l(I.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(I.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(I.notes||"")+"</div><div>"+M+"</div></div>";const j=t("erp-map-tax-"+(I.pearnly_tax_kind||""))||I.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+l(t("erp-map-col-erp"))+'">'+H+'</div><div data-label="'+l(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+l(j)+'</span></div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+l(I.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(I.notes||"")+"</div><div>"+M+"</div></div>"}async function C(S){const I=i.sub,k={};S.querySelectorAll("[data-erp-field]").forEach(function($){k[$.dataset.erpField]=($.value||"").trim()});const M=localStorage.getItem("mrpilot_token");if(!M)return;let H={},j="/api/erp/mappings/"+I;if(I==="clients"){if(!k.client_id||!k.erp_type||!k.erp_code){p(t("erp-map-save-fail"),"error");return}H={client_id:parseInt(k.client_id,10),erp_type:k.erp_type,erp_code:k.erp_code,notes:k.notes||""}}else if(I==="accounts"){if(!k.erp_type||!k.pearnly_category||!k.erp_code){p(t("erp-map-save-fail"),"error");return}H={erp_type:k.erp_type,pearnly_category:k.pearnly_category,erp_code:k.erp_code,erp_name:k.erp_name||"",notes:k.notes||""}}else{if(!k.erp_type||!k.pearnly_tax_kind||!k.erp_code){p(t("erp-map-save-fail"),"error");return}H={erp_type:k.erp_type,pearnly_tax_kind:k.pearnly_tax_kind,erp_code:k.erp_code,notes:k.notes||""}}try{const $=await fetch(j,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+M},body:JSON.stringify(H)});if(!$.ok)throw new Error("http_"+$.status);i.addingNew[I]=!1,await f(I,!0),m(),p(t("erp-map-saved-toast"),"success")}catch{p(t("erp-map-save-fail"),"error")}}async function L(S){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const k=i.sub,M=localStorage.getItem("mrpilot_token");try{const H=await fetch("/api/erp/mappings/"+k+"/"+encodeURIComponent(S),{method:"DELETE",headers:{Authorization:"Bearer "+M}});if(!H.ok)throw new Error("http_"+H.status);await f(k,!0),m(),p(t("erp-map-deleted-toast"),"success")}catch{p(t("erp-map-delete-fail"),"error")}}async function y(){await c(),await f(i.sub,!1),u()}function g(S){S!==i.sub&&(i.sub=S,i.addingNew[S]=!1,["clients","accounts","taxes","products"].forEach(function(I){I!==S&&(i.addingNew[I]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(I){I.classList.toggle("active",I.dataset.erpSubtab===S)}),f(S,!1).then(function(){u()}))}function x(){i.bound||(i.bound=!0,document.addEventListener("click",function(S){const I=S.target.closest(".erp-subtab[data-erp-subtab]");if(I){S.preventDefault();const $=I.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(q){q.classList.toggle("active",q.dataset.erpSubtab===$)}),document.querySelectorAll(".erp-subpanel").forEach(function(q){q.classList.toggle("active",q.dataset.erpSubpanel===$)}),$==="mappings"&&setTimeout(y,50);return}const k=S.target.closest(".erp-map-subtab[data-erp-subtab]");if(k){S.preventDefault(),g(k.dataset.erpSubtab);return}if(S.target.closest("#erp-map-add-btn")){if(S.preventDefault(),!r())return;i.addingNew[i.sub]=!0,m();return}const H=S.target.closest('[data-erp-save="new"]');if(H){S.preventDefault();const $=H.closest('[data-erp-row="new"]');$&&C($);return}const j=S.target.closest("[data-erp-del]");if(j){S.preventDefault(),L(j.dataset.erpDel);return}}))}function T(){const S=document.getElementById("erp-map-pane-wrap");S&&S.children.length>0&&u(),document.querySelectorAll(".erp-map-subtab").forEach(function(I){const k="erp-map-subtab-"+I.dataset.erpSubtab,M=t(k);M&&M!==k&&(I.textContent=M)})}x(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",T)})();(function(){let e=null,n=0,a=!1;function o(y){return typeof escapeHtml=="function"?escapeHtml(y==null?"":String(y)):String(y??"")}function s(y,g){try{typeof showToast=="function"&&showToast(y,g||"info")}catch{}}async function i(y){const g=Date.now();if(e&&g-n<3e4)return e;const x=localStorage.getItem("mrpilot_token");if(!x)return[];try{const T=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+x}});if(!T.ok)return[];const S=await T.json();return e=S&&S.connectors||[],n=g,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function d(y){try{localStorage.setItem("pn_push_default_connector",y||"")}catch{}}function l(y){if(!y||!y.length)return null;const g=r();if(g){const T=y.find(S=>S.id===g);if(T)return T}const x=y.find(T=>T.is_default);return x||y[0]}function p(y){if(!y)return!1;const g=String(y.status||"").toLowerCase();return g==="exception"||g==="exception_pending"||g==="rejected"}function f(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(y){const g=y&&(y.type||y.id);return g==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':g==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function u(y,g){if(!y||!g)return!1;const x=document.getElementById("btn-push-default");x&&(x.disabled=!0,x.classList.add("loading"));const T=localStorage.getItem("mrpilot_token");try{let S,I={method:"POST",headers:{Authorization:"Bearer "+T}};y.type==="xero"?S="/api/erp/xero/push/"+encodeURIComponent(g):(S="/api/erp/push",I.headers["Content-Type"]="application/json",I.body=JSON.stringify({history_id:g,endpoint_id:y.endpoint_id||void 0}));const k=await fetch(S,I);let M={};try{M=await k.json()}catch{}if(!k.ok){let H=M&&M.detail||"unknown";typeof H=="object"&&(H=H.code||JSON.stringify(H));let j=String(H||"unknown");if(y.type==="xero"){const $=j.replace(/^xero\./,"").toLowerCase(),q=t("xero-"+$);q&&q!=="xero-"+$&&(j=q)}return s(t("unified-push-fail").replace("{name}",y.name).replace("{err}",j),"error"),!1}if(M&&M.ok===!1){let H=M.error_msg||M.error_code||"unknown";return H=String(H).slice(0,200),s(t("unified-push-fail").replace("{name}",y.name).replace("{err}",H),"error"),!1}return s(t("unified-push-ok").replace("{name}",y.name),"success"),!0}catch(S){return s(t("unified-push-fail").replace("{name}",y.name).replace("{err}",S.message||"network"),"error"),!1}finally{x&&(x.disabled=!1,x.classList.remove("loading"))}}async function m(y,g){for(const x of y)await u(x,g)}function h(y,g){const x=document.createElement("div");x.className="pn-push-dropdown",x.id="pn-push-dropdown";const T=(y||[]).map(I=>{const k=!!(g&&I.id===g.id),M=I.method==="download"?t("unified-push-tag-download"):k?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(I.id)+'"><span class="pn-pd-icon">'+c(I)+'</span><span class="pn-pd-name">'+o(I.name)+"</span>"+(M?'<span class="pn-pd-tag">'+o(M)+"</span>":"")+(k?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),S=y&&y.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",y.length))+"</span></div>":"";return x.innerHTML=T+S,x}function _(){const y=document.getElementById("pn-push-dropdown");y&&y.remove()}async function w(){if(document.getElementById("pn-push-dropdown")){_();return}const y=await i()||[],g=l(y),x=h(y,g),T=document.getElementById("pn-push-wrap");T&&T.appendChild(x)}async function b(){const y=await i()||[],g=l(y);if(!g)return;const x=f(),T=x&&(x._historyId||x.history_id);if(T){if(p(x)){s(t("unified-push-disabled-exc"),"warn");return}await u(g,T)}}async function v(y){_();const g=await i()||[],x=f(),T=x&&(x._historyId||x.history_id);if(!T)return;if(p(x)){s(t("unified-push-disabled-exc"),"warn");return}if(y==="__all__"){await m(g,T);return}const S=g.find(I=>I.id===y);S&&(d(y),await u(S,T),B())}async function E(){const y=document.getElementById("drawer-history-save");if(!y||y.querySelector("#pn-push-wrap"))return;const g=document.createElement("div");g.id="pn-push-wrap",g.className="pn-push-wrap",g.dataset.loading="1",y.insertBefore(g,y.firstChild),["btn-push-erp","btn-xero-push"].forEach(M=>{y.querySelectorAll("#"+M).forEach(H=>{H.style.display="none"})});const x=await i()||[],T=l(x),S=x.length>0;if(!S)g.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const M=x.length>1;g.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+c(T)+"<span>"+o(t("unified-push-to").replace("{name}",T?T.name:""))+"</span></button>"+(M?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete g.dataset.loading;const I=g.querySelector("#btn-push-default");I&&S&&I.addEventListener("click",b);const k=g.querySelector("#btn-push-arrow");k&&k.addEventListener("click",function(M){M.stopPropagation(),w()}),a||(a=!0,document.addEventListener("click",function(M){const H=M.target.closest(".pn-pd-item");if(H){const j=H.getAttribute("data-cid");v(j);return}M.target.closest("#btn-push-arrow")||_()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",B))}function B(){const y=document.getElementById("pn-push-wrap");y&&(y.remove(),e=null,n=0,E())}function C(){const y=document.getElementById("drawer-history-save");if(!y||!y.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(x=>{y.querySelectorAll("#"+x).forEach(T=>{T.style.display!=="none"&&(T.style.display="none")})});const g=y.querySelectorAll("#pn-push-wrap");if(g.length>1)for(let x=1;x<g.length;x++)g[x].remove()}function L(){try{const y=function(){return document.getElementById("drawer-body")},g=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&E(),C()}),x=y();if(x)g.observe(x,{childList:!0,subtree:!0});else{const T=new MutationObserver(function(){const S=y();S&&(g.observe(S,{childList:!0,subtree:!0}),T.disconnect())});T.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&E(),C()},200)}catch{}}L()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",d=t(r);d&&d!==r&&(i.textContent=d)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const l=document.getElementById("erp-onboard-title"),p=document.getElementById("erp-onboard-body"),f=document.getElementById("erp-onboard-ok"),c=document.getElementById("erp-onboard-later");l&&(l.textContent=t("erp-onboard-title")),p&&(p.textContent=t("erp-onboard-body")),f&&(f.textContent=t("erp-onboard-ok")),c&&(c.textContent=t("erp-onboard-later"))}r();function d(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}d();try{const l=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');l&&l.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}d()}),i.addEventListener("click",function(l){l.target===i&&d()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),d=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||d)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,i=s[a]||s.th||s.en,r=n.stage_total,d=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const l={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+l.replace("{d}",d||0).replace("{t}",r)}return i},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,i=o.maxMs||1200*1e3,r=Date.now();let d=0;for(;;){let l=null;try{const p=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{l=await p.json()}catch{l=null}(!p.ok||!l||!l.ok)&&(l=null)}catch{l=null}if(l){if(d=0,o.onProgress)try{o.onProgress(l.progress||{},l)}catch{}if(l.status==="done"||l.status==="failed"||l.status==="needs_review"||l.status==="needs_mapping")return l}else if(++d>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(p=>setTimeout(p,s))}}})();const ee={initialized:!1,stmtFiles:[],glFiles:[],currentTask:null,currentFilter:"all",allRows:[],brv2Search:{stmt:"",gl:""},cachedHistoryTasks:[],brv2Page:1},Y=e=>document.getElementById(e);function qe(e){if(e==null)return"—";const n=Number(e);return isNaN(n)?"—":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function Fn(e){return e?String(e).slice(0,10).split("-").reverse().join("/"):"—"}function ye(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function Ei(e,n){n=window._currentLang||n||"th";const a={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},o={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},s=a[e]||o;return s[n]||s.th||s.en}function Bi(e){return e?e<1024?e+" B":e<1048576?(e/1024).toFixed(1)+" KB":(e/1048576).toFixed(1)+" MB":""}function Xe(e,n){return window.t&&window.t(e)||n}function je(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function Yt(e){return Number.isFinite(+e)?(+e).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}var Ta="pearnly.brv2.lastAnchorOcr";function Ii(e){try{var n=e&&e._anchor_ocr;if(!n||typeof n!="object")return;var a={stmt_opening:Number.isFinite(+n.stmt_opening)?+n.stmt_opening:null,gl_opening:Number.isFinite(+n.gl_opening)?+n.gl_opening:null,gl_closing:Number.isFinite(+n.gl_closing)?+n.gl_closing:null,stmt_closing:Number.isFinite(+n.stmt_closing)?+n.stmt_closing:null,ts:Date.now()};localStorage.setItem(Ta,JSON.stringify(a))}catch{}}function Li(){try{var e=localStorage.getItem(Ta);if(!e)return null;var n=JSON.parse(e);return!n||typeof n!="object"?null:n}catch{return null}}function Ci(){var e=Li();if(e){var n={"brv2-anchor-stmt-opening":e.stmt_opening,"brv2-anchor-gl-opening":e.gl_opening,"brv2-anchor-gl-closing":e.gl_closing,"brv2-anchor-stmt-closing":e.stmt_closing},a=0;Object.keys(n).forEach(function(d){var l=document.getElementById(d);if(l&&l.value===""){var p=n[d];if(Number.isFinite(p)){l.value=p.toFixed(2);var f=l.closest&&l.closest(".brv2-anchor-cell");f&&f.classList.add("is-prefilled"),a+=1}}});var o=document.getElementById("brv2-anchor-eq"),s=document.getElementById("brv2-anchor-eq-val");if(o&&s&&Number.isFinite(e.stmt_opening)&&Number.isFinite(e.gl_opening)){var i=e.stmt_opening-e.gl_opening;s.textContent=i.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),o.style.display=""}if(a>0){var r=document.getElementById("brv2-anchor-prefill-banner");r&&r.classList.add("show")}}}function Si(){var e=document.getElementById("brv2-anchor-prefill-banner");if(e){var n=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(a){var o=document.getElementById(a);if(o){var s=o.closest&&o.closest(".brv2-anchor-cell");s&&s.classList.contains("is-prefilled")&&(n=!0)}}),e.classList.toggle("show",n)}}var Ti=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function Mi(e){var n=document.getElementById("brv2-summary-collapse");if(!(!n||!n.parentNode)){var a=document.getElementById("brv2-anchor-audit"),o=e&&e._anchor_overrides;if(!o||typeof o!="object"||Object.keys(o).length===0){a&&a.parentNode&&a.parentNode.removeChild(a);return}a||(a=document.createElement("div"),a.id="brv2-anchor-audit",a.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",n.parentNode.insertBefore(a,n.nextSibling));var s=Ti.map(function(i){var r=o[i[0]];if(!r)return"";var d=+r.ocr||0,l=+r.user||0,p=l-d,f=p>0?"+":(p<0,""),c=Math.abs(p)<.005?"#6b7280":p>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+je(Xe(i[1],i[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+je(Yt(d))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+je(Yt(l))+'</td><td style="padding:6px 10px;color:'+c+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+je(f+Yt(p))+"</td></tr>"}).join("");a.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+je(Xe("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+je(Xe("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+je(Xe("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+je(Xe("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+je(Xe("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+s+"</tbody></table>"}}function Dt(e){const n=Y("brv2-summary-collapse"),a=Y("brv2-detail-collapse"),o=Y("brv2-export-btn"),s=Y("brv2-new-btn"),i=Y("brv2-parse-info-wrap");n&&(n.style.display=e?"":"none"),a&&(a.style.display=e?"":"none"),o&&(o.style.display=e?"":"none"),s&&(s.style.display=e?"":"none"),!e&&i&&(i.style.display="none");const r=Y("brv2-warnings");!e&&r&&(r.style.display="none",r.innerHTML="")}function $i(e){const n=Y("brv2-parse-info-wrap"),a=Y("brv2-parse-info-body");if(!n||!a)return;const o=e.parse_info;if(!o){n.style.display="none";return}const s=window._currentLang||"zh",i={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},r=u=>(i[u]||{})[s]||(i[u]||{}).zh||u,d=[...(o.stmt_files||[]).map(u=>({...u,_type:"stmt",_extra:u.bank_code||""})),...(o.gl_files||[]).map(u=>({...u,_type:"gl",_extra:(u.accounts||[]).join(", ")}))],l={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},p=u=>{const m=String(u||"");return/Cannot detect bank statement column headers/i.test(m)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(m)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(m)?"stmt_no_rows":/unsupported format/i.test(m)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(m)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(m)?"ocr_failed":null},f=u=>{const m=u.error_code||p(u.error);if(m&&l[m]){const h=window._currentLang||"zh";return l[m][h]||l[m].zh}return String(u.error||"").slice(0,80)},c=u=>!u.ok&&u.error?`<span style="color:#dc2626">${r("fail")} — ${ye(f(u))}</span>`:u.rows?`<span style="color:#059669">${r("ok")} (${u.rows})</span>`:`<span style="color:#d97706">${r("warn")}</span>`;a.innerHTML=`
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
                ${d.map(u=>`<tr>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${u._type==="stmt"?r("stmt"):r("gl")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${ye(u.file||"")}">${ye(u.file||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${u.rows||0}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${ye(u._extra||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb">${c(u)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`,n.style.display=""}async function Ma(e){const n=localStorage.getItem("mrpilot_token")||"",a=window._currentLang||"zh";try{const o=await fetch("/api/recon/bank-v2/"+e+"/export?lang="+a,{headers:{Authorization:"Bearer "+n}});if(!o.ok){const f=await o.json().catch(()=>({}));window.showToast&&window.showToast(f.detail||"Export failed","error");return}const s=await o.blob(),r=(o.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),d=r?r[1].replace(/['"]/g,""):"reconciliation.xlsx",l=URL.createObjectURL(s),p=document.createElement("a");p.href=l,p.download=d,document.body.appendChild(p),p.click(),document.body.removeChild(p),URL.revokeObjectURL(l)}catch(o){window.showToast&&window.showToast("Export error: "+o.message,"error")}}function Hi(e,n){const a=Y("brv2-summary-collapse");let o=Y("brv2-warnings");const s=window._currentLang||"zh",i={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[s]||"⏭ ",r=[];if((n||[]).forEach(d=>r.push(i+" "+d)),(e||[]).forEach(d=>r.push(d)),!r.length){o&&(o.style.display="none");return}if(!o)if(o=document.createElement("div"),o.id="brv2-warnings",a&&a.parentNode)a.parentNode.insertBefore(o,a);else return;o.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",o.innerHTML=r.map(d=>"<div>"+ye(d)+"</div>").join("")}function Ln(e){$i(e),Hi(e.warnings||[],e.skipped_files||[]),!e.ok&&e.error&&window.showToast&&window.showToast(e.error,"error");const n=e.stats||{},a=e.summary||{},o=n.matched||0,s=(n.gl_debit_only||0)+(n.gl_credit_only||0),i=(n.stmt_withdrawal_only||0)+(n.stmt_deposit_only||0),r=Number(a.formula_diff||0),d=Math.abs(r)<.05;Y("brv2-kpi-matched")&&(Y("brv2-kpi-matched").textContent=o),Y("brv2-kpi-diff")&&(Y("brv2-kpi-diff").textContent=qe(r)),Y("brv2-kpi-unmatched")&&(Y("brv2-kpi-unmatched").textContent=s+i);const l=Y("brv2-kpi-diff-icon");l&&(l.style.background=d?"#d1fae5":"#fee2e2",l.style.color=d?"#065f46":"#b91c1c");const p=Y("brv2-formula-sub");if(p){const h=window._currentLang||"zh";p.textContent=d?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[h]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[h]||"差 ")+qe(r)}const f=Y("brv2-detail-sub");if(f){const h=window._currentLang||"zh",_={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[h]||"共 {n} 行";f.textContent=_.replace("{n}",ee.allRows.length)}function c(h,_,w){const b=Y(h);b&&(b.textContent=(w&&_>0?"(":"")+qe(w?-_:_)+(w&&_>0?")":""))}c("brf-gl-close",a.gl_closing||0),c("brf-open-diff",a.opening_diff||0),c("brf-gl-debit-only",a.gl_debit_only_amount||0,!0),c("brf-gl-credit-only",a.gl_credit_only_amount||0),c("brf-stmt-wd-only",a.stmt_withdrawal_only_amount||0,!0),c("brf-stmt-dep-only",a.stmt_deposit_only_amount||0),c("brf-calc-close",a.formula_stmt_closing||0),c("brf-stmt-close",a.stmt_closing||0),Y("brf-diff")&&(Y("brf-diff").textContent=qe(r));const u=Y("brv2-fcell-diff");u&&u.classList.toggle("brv2-fcell-diff-ok",d);const m=Y("brv2-export-btn");m&&(m.onclick=()=>{ee.currentTask&&Ma(ee.currentTask.task_id)}),Mi(a),Dt(!0),$a()}function $a(){const e=Y("brv2-tbody");if(!e)return;const n=ee.allRows.filter(i=>ee.currentFilter==="all"?!0:ee.currentFilter==="matched"?i.match_status==="matched":ee.currentFilter==="gl_only"?i.match_status.startsWith("gl_"):ee.currentFilter==="stmt_only"?i.match_status.startsWith("stmt_"):!0);if(n.length===0){const i={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";e.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${i}</td></tr>`;return}const a=window._currentLang||"zh",o={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[a],s={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[a];e.innerHTML=n.map(i=>{const r=i.match_status,d=i.match_layer;let l="",p="";r==="matched"?(d===1&&(l="matched",p='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),d===2&&(l="matched-l2",p='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),d===3&&(l="matched-l3",p='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):r==="gl_debit_only"||r==="gl_credit_only"?(l="gl-only",p='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(l="stmt-only",p=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[a]||"账单"}</span>`);let f="";return i.stmt_balance_ok===!1&&(f+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${ye(o)}">⚠</span>`,l+=" brv2-row-warn"),i.stmt_confidence==="low"&&(f+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${ye(s)}">◌</span>`,l.includes("brv2-row-warn")||(l+=" brv2-row-warn-soft")),`<tr class="${l.trim()}">
          <td>${p}${f}</td>
          <td>${ye(Fn(i.stmt_date))}</td>
          <td title="${ye(i.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${ye(i.stmt_desc)}</td>
          <td class="num">${i.stmt_withdrawal?qe(i.stmt_withdrawal):""}</td>
          <td class="num">${i.stmt_deposit?qe(i.stmt_deposit):""}</td>
          <td>${ye(Fn(i.gl_date))}</td>
          <td title="${ye(i.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${ye(i.gl_doc_no)}</td>
          <td class="num">${i.gl_debit?qe(i.gl_debit):""}</td>
          <td class="num">${i.gl_credit?qe(i.gl_credit):""}</td>
          <td>${d?"L"+d:"—"}</td>
        </tr>`}).join("")}async function kt(){const e=localStorage.getItem("mrpilot_token")||"";try{const a=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+e}})).json();qt(a.tasks||[])}catch{const a=Y("brv2-history-empty"),o=window._currentLang||"zh",s={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[o]||"加载失败";a&&(a.textContent=s,a.style.display="");const i=Y("brv2-history-table-wrap");i&&(i.style.display="none")}}const ot=10;function zn(){const e=Y("brv2-history-pager"),n=Y("brv2-history-pager-info"),a=Y("brv2-history-prev"),o=Y("brv2-history-next");if(!e)return;if(ee.cachedHistoryTasks.length<=ot){e.style.display="none";return}e.style.display="";const s=Math.ceil(ee.cachedHistoryTasks.length/ot);n&&(n.textContent=ee.brv2Page+" / "+s),a&&(a.disabled=ee.brv2Page<=1),o&&(o.disabled=ee.brv2Page>=s)}function Ai(){const e=Y("brv2-history-prev"),n=Y("brv2-history-next");e&&!e._brv2Bound&&(e._brv2Bound=!0,e.addEventListener("click",()=>{ee.brv2Page>1&&(ee.brv2Page--,qt(ee.cachedHistoryTasks))})),n&&!n._brv2Bound&&(n._brv2Bound=!0,n.addEventListener("click",()=>{const a=Math.ceil(ee.cachedHistoryTasks.length/ot);ee.brv2Page<a&&(ee.brv2Page++,qt(ee.cachedHistoryTasks))}))}function qt(e){e!==void 0&&(ee.cachedHistoryTasks=e||[],ee.brv2Page=1);const n=ee.cachedHistoryTasks,a=Y("brv2-history-empty"),o=Y("brv2-history-table-wrap"),s=Y("brv2-history-tbody");if(!s)return;const i=window._currentLang||"zh";if(!n.length){const m={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[i]||"暂无对账记录";a&&(a.textContent=m,a.style.display=""),o&&(o.style.display="none"),zn();return}a&&(a.style.display="none"),o&&(o.style.display="");const r=Math.ceil(n.length/ot);ee.brv2Page>r&&(ee.brv2Page=r);const d=(ee.brv2Page-1)*ot,l=n.slice(d,d+ot),p=localStorage.getItem("mrpilot_token")||"",f='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',c='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',u='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';s.innerHTML="",l.forEach(m=>{const h=Number(m.formula_diff||0),_=Math.abs(h)<.05,w=(m.stmt_files||"").split(";").map($=>$.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),b=(m.gl_files||"").split(";").map($=>$.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),v=m.created_at?String(m.created_at).slice(0,16).replace("T"," "):"",E=document.createElement("tr");E.dataset.taskId=m.id;const B=document.createElement("td");B.textContent=v;const C=document.createElement("td");C.className="glv-history-file",C.title=w+" + "+b,C.textContent=w+" + "+b;const L=document.createElement("td");L.className="glv-num",L.textContent=(m.stmt_row_count||0)+" / "+(m.gl_row_count||0);const y=document.createElement("td");y.className="glv-num",y.textContent=m.matched_count||0;const g=document.createElement("td");g.className="glv-num",g.textContent=m.unmatched_gl||0;const x=document.createElement("td");x.className="glv-num",x.textContent=m.unmatched_stmt||0;const T=document.createElement("td");T.className="glv-num",T.style.color=_?"#059669":"#dc2626",T.textContent=_?"✓":qe(h);const S=document.createElement("td");S.className="glv-history-actions";const I=($,q,F,W)=>{const G=document.createElement("button");return G.type="button",G.title=q,G.setAttribute("aria-label",q),F&&(G.className=F),G.innerHTML=$,G.onclick=A=>{A.stopPropagation(),W()},G},k={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[i]||"删除?",M={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[i]||"加载",H={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[i]||"导出",j={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[i]||"删除";S.appendChild(I(f,M,"",()=>Nn(m.id,p))),S.appendChild(I(c,H,"",()=>Ma(m.id))),S.appendChild(I(u,j,"glv-del",async()=>{await showConfirm(k,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+m.id,{method:"DELETE",headers:{Authorization:"Bearer "+p}}),kt())})),[B,C,L,y,g,x,T,S].forEach($=>E.appendChild($)),E.style.cursor="pointer",E.addEventListener("click",async $=>{$.target.closest(".glv-del")||$.target.closest("button")||await Nn(m.id,p)}),s.appendChild(E)}),zn(),Ha()}function Ha(){const e=((Y("brv2-hist-search")||{}).value||"").trim().toLowerCase(),n=Y("brv2-history-tbody");n&&n.querySelectorAll("tr").forEach(a=>{a.dataset.taskId&&(a.style.display=!e||a.textContent.toLowerCase().includes(e)?"":"none")})}async function Nn(e,n){try{const o=await(await fetch("/api/recon/bank-v2/"+e,{headers:{Authorization:"Bearer "+n}})).json();if(!o.ok)return;ee.currentTask={task_id:o.task_id,...o},ee.allRows=o.detail||[],ee.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(s=>s.classList.toggle("active",s.dataset.filter==="all")),Ln(ee.currentTask)}catch{}}function $e(e){const n=e==="stmt"?ee.stmtFiles:ee.glFiles,a=Y(`brv2-${e}-name`);if(a)if(n.length===0)a.textContent="";else{const s=window._currentLang||"zh",i={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};a.textContent=n.length+(i[s]||" 个文件")}const o=Y("brv2-preview-panel");o&&o.style.display!=="none"&&nn(e),ji()}function ji(){const e=Y("brv2-toggle-preview"),n=Y("brv2-preview-panel"),a=ee.stmtFiles.length+ee.glFiles.length>0;e&&(e.style.display=a?"":"none"),!a&&n&&(n.style.display="none",e&&e.classList.remove("open"))}function Pi(){nn("stmt"),nn("gl")}function nn(e){const n=Y(e==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!n)return;const a=e==="stmt"?ee.stmtFiles:ee.glFiles,o=window._currentLang||"zh",s={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},i=(s[e]||{})[o]||s[e].zh,r=ye(window.t&&window.t("vex-preview-search")||"搜索文件名..."),d=ye(window.t&&window.t("vex-preview-clear-all")||"全清"),l=ee.brv2Search[e]||"";n.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+ye(i)+' <span class="vex-pp-col-count">'+a.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+e+'" type="text" placeholder="'+r+'" value="'+ye(l)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+e+'" type="button">'+d+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+e+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+e+'-pg"></div>';const p=Y("brv2-pp-search-"+e);p&&p.addEventListener("input",function(c){ee.brv2Search[e]=c.target.value,On(e)});const f=Y("brv2-pp-clearall-"+e);f&&f.addEventListener("click",function(){e==="stmt"?ee.stmtFiles.length=0:ee.glFiles.length=0,$e(e),Re()}),On(e)}function On(e){const n=Y("brv2-pp-"+e+"-list"),a=Y("brv2-pp-"+e+"-pg");if(!n)return;const o=e==="stmt"?ee.stmtFiles:ee.glFiles,s=(ee.brv2Search[e]||"").toLowerCase(),i=s?o.filter(l=>l.name.toLowerCase().includes(s)):o.slice(),r='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',d='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(n.innerHTML=i.map((l,p)=>'<div class="vex-pp-file-row">'+r+'<span class="vex-pp-fi-name" title="'+ye(l.name)+'">'+ye(l.name)+'</span><span class="vex-pp-fi-size">'+Bi(l.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+e+'" data-idx="'+o.indexOf(l)+'" aria-label="remove">'+d+"</button></div>").join(""),n.querySelectorAll(".vex-pp-fi-del").forEach(function(l){l.addEventListener("click",function(){const p=parseInt(l.dataset.idx,10);l.dataset.zone==="stmt"?ee.stmtFiles.splice(p,1):ee.glFiles.splice(p,1),$e(l.dataset.zone),Re()})}),a){const l=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";a.textContent=l.replace("{n}",i.length).replace("{m}",o.length)}}function Di(){const e=Y("brv2-toggle-preview");e&&!e._reconBound&&(e._reconBound=!0,e.addEventListener("click",function(){const n=Y("brv2-preview-panel"),a=Y("brv2-toggle-preview-label"),o=n&&n.style.display!=="none";n&&(n.style.display=o?"none":""),e.classList.toggle("open",!o),a&&(a.textContent=o?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),o||Pi()}))}function Re(){const e=Y("brv2-run-btn"),n=Y("brv2-status"),a=ee.stmtFiles.length>0,o=ee.glFiles.length>0;if(e&&(e.disabled=!(a&&o)),n){const s=window._currentLang||"zh";if(!a&&!o){const i={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};n.textContent=i[s]||i.zh}else if(a)if(o){const i={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};n.textContent=i[s]||i.zh}}}function Vn(e,n,a){const o=Y(e),s=Y(n);!o||!s||(o.addEventListener("click",()=>s.click()),o.addEventListener("keydown",i=>{(i.key==="Enter"||i.key===" ")&&(i.preventDefault(),s.click())}),o.addEventListener("dragover",i=>{i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",()=>o.classList.remove("drag-over")),o.addEventListener("drop",i=>{i.preventDefault(),o.classList.remove("drag-over");const r=Array.from(i.dataTransfer.files||[]);a==="stmt"?ee.stmtFiles.push(...r):ee.glFiles.push(...r),$e(a),Re()}),s.addEventListener("change",()=>{const i=Array.from(s.files||[]);a==="stmt"?ee.stmtFiles.push(...i):ee.glFiles.push(...i),s.value="",$e(a),Re()}))}function Ee(e){const n=Y("brv2-progress"),a=Y("brv2-run-btn"),o=Y("brv2-error");n&&(n.style.display=e?"":"none"),a&&(a.disabled=e),o&&(o.style.display="none")}function Me(e){const n=Y("brv2-error");n&&(n.textContent=e,n.style.display="",n.scrollIntoView({behavior:"smooth",block:"nearest"})),Ee(!1),Re(),window.showToast&&window.showToast(e,"error")}async function an(){if(ee.stmtFiles.length===0||ee.glFiles.length===0)return;const e=localStorage.getItem("mrpilot_token")||"",n=window._currentLang||"zh",a=(Y("brv2-acct-select")||{}).value||"";Dt(!1),Ee(!0);try{const o=new FormData;ee.stmtFiles.forEach(m=>o.append("stmt_files",m)),ee.glFiles.forEach(m=>o.append("gl_files",m)),o.append("gl_account",a),o.append("lang",n);const s=parseFloat((Y("brv2-anchor-gl-closing")||{}).value),i=parseFloat((Y("brv2-anchor-stmt-closing")||{}).value),r=parseFloat((Y("brv2-anchor-stmt-opening")||{}).value),d=parseFloat((Y("brv2-anchor-gl-opening")||{}).value);Number.isFinite(s)&&o.append("gl_closing_override",s),Number.isFinite(i)&&o.append("stmt_closing_override",i),Number.isFinite(r)&&o.append("stmt_opening_override",r),Number.isFinite(d)&&o.append("gl_opening_override",d);const l=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+e},body:o});let p=null;try{p=await l.json()}catch{p=null}if(p&&p.needs_mapping){Ee(!1),window.ReconMapping?window.ReconMapping.show(p,{token:e,lang:n,onConfirmed:function(){an()}}):Me(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!l.ok||!p||!p.ok||!p.job_id){Ee(!1),p&&(p.detail||p.error)?Me(_humanizeBackendError(p.detail||p.error,"Error "+l.status)):Me(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const f=Y("brv2-progress-sub"),c=await window._reconPollJob(p.job_id,e,{onProgress:m=>{f&&(f.textContent=window._reconProgressText(m,n))}});if(c&&c.status==="needs_mapping"&&c.mapping){Ee(!1),window.ReconMapping?window.ReconMapping.show(c.mapping,{token:e,lang:n,onConfirmed:function(){an()}}):Me(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(c&&c.status==="needs_review"&&c.review){Ee(!1),window.ReconReview?window.ReconReview.show(c.review,{token:e,lang:n,jobId:p.job_id,onConfirmed:async function(m){Ee(!0);const h=await window._reconPollJob(m,e,{onProgress:_=>{f&&(f.textContent=window._reconProgressText(_,n))}});await u(h)}}):Me(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(c&&c.status==="failed"){Ee(!1),Me(Ei(c.error_code,n));return}await u(c);async function u(m){try{if(!m||m.status!=="done"||!m.result_id){Ee(!1),Me(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const h=await fetch("/api/recon/bank-v2/"+encodeURIComponent(m.result_id),{headers:{Authorization:"Bearer "+e}});let _=null;try{_=await h.json()}catch{_=null}if(!h.ok||_===null||!_.ok){Ee(!1),Me(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(_.gl_accounts||[]).length>1&&qi(_.gl_accounts),ee.currentTask=_,ee.allRows=_.detail||[],ee.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(b=>b.classList.toggle("active",b.dataset.filter==="all")),Ii(_&&_.summary),Ee(!1),Ln(_),kt();const w=Y("brv2-summary-collapse");w&&w.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(h){Ee(!1),Me(h.message||"Network error")}}}catch(o){Me(o.message||"Network error")}}function qi(e){const n=Y("brv2-acct-select");if(!n)return;const a=window._currentLang||"zh",o={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[a]||"全部账户";n.innerHTML=`<option value="">${o}</option>`+e.map(s=>`<option value="${ye(s)}">${ye(s)}</option>`).join(""),n.style.display=""}function Cn(){if(ee.initialized){kt();return}ee.initialized=!0,Vn("brv2-stmt-zone","brv2-stmt-input","stmt"),Vn("brv2-gl-zone","brv2-gl-input","gl");const e=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function n(){const d=parseFloat((Y("brv2-anchor-stmt-opening")||{}).value),l=parseFloat((Y("brv2-anchor-gl-opening")||{}).value),p=Y("brv2-anchor-eq"),f=Y("brv2-anchor-eq-val");if(!(!p||!f))if(Number.isFinite(d)&&Number.isFinite(l)){const c=d-l;f.textContent=c.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),p.style.display=""}else p.style.display="none"}e.forEach(d=>{const l=Y(d);l&&(l.addEventListener("input",n),l.addEventListener("input",()=>{const p=l.closest(".brv2-anchor-cell");p&&p.classList.remove("is-prefilled"),Si()}))}),Ci();const a=Y("brv2-run-btn");a&&a.addEventListener("click",an);const o=Y("brv2-reset-btn");o&&o.addEventListener("click",()=>{ee.currentTask=null,ee.allRows=[],ee.stmtFiles=[],ee.glFiles=[],$e("stmt"),$e("gl"),Re(),Dt(!1);const d=Y("brv2-acct-select");d&&(d.style.display="none"),e.forEach(f=>{const c=Y(f);if(c){c.value="";const u=c.closest&&c.closest(".brv2-anchor-cell");u&&u.classList.remove("is-prefilled")}});const l=Y("brv2-anchor-eq");l&&(l.style.display="none");const p=Y("brv2-anchor-prefill-banner");p&&p.classList.remove("show")});const s=Y("brv2-new-btn");s&&s.addEventListener("click",()=>{ee.currentTask=null,ee.allRows=[],ee.stmtFiles=[],ee.glFiles=[],$e("stmt"),$e("gl"),Re(),Dt(!1)});const i=Y("brv2-filter-tabs");i&&i.addEventListener("click",d=>{d.stopPropagation();const l=d.target.closest(".brv2-filter-btn");l&&(ee.currentFilter=l.dataset.filter,i.querySelectorAll(".brv2-filter-btn").forEach(p=>p.classList.toggle("active",p===l)),$a())}),Di(),Ai();const r=Y("brv2-hist-search");r&&r.addEventListener("input",Ha),kt(),Re(),window._brv2LoadHistory=kt,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(d=>d.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){Re(),$e("stmt"),$e("gl"),ee.currentTask&&Ln(ee.currentTask),qt()}})}window._loadBankReconV2Panel=function(e){const n=e?document.getElementById(e):null;n&&n.id!=="recon-pane-bank"&&(n.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
            银行对账 v2 · 请前往对账中心使用</div>`),Cn()};document.addEventListener("DOMContentLoaded",()=>{Y("brv2-run-btn")&&Cn()});window._bankReconV2Init=Cn;(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const p=document.getElementById("general-tz"),f=document.getElementById("general-date"),c=document.getElementById("general-number");if(!(!p||!f||!c))try{p.value=localStorage.getItem(n)||s.tz,f.value=localStorage.getItem(a)||s.date,c.value=localStorage.getItem(o)||s.number}catch{p.value=s.tz,f.value=s.date,c.value=s.number}}async function r(){const p=document.getElementById("btn-save-general"),f=document.getElementById("general-save-msg");if(!p)return;const c=p.innerHTML;p.disabled=!0,p.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",f&&(f.textContent="",f.classList.remove("error"));try{const u=(document.getElementById("general-tz")||{}).value||s.tz,m=(document.getElementById("general-date")||{}).value||s.date,h=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,u),localStorage.setItem(a,m),localStorage.setItem(o,h)}catch{}window._pearnlyGeneral={tz:u,date_format:m,number_format:h},f&&(f.textContent=t("msg-saved")||"已保存")}catch{f&&(f.textContent=t("msg-save-failed")||"保存失败",f.classList.add("error"))}finally{p.disabled=!1,p.innerHTML=c,setTimeout(function(){f&&(f.textContent="")},3e3)}}function d(){const p=document.getElementById("btn-save-general");if(!p){setTimeout(d,200);return}p._pearnlyGenBound||(p._pearnlyGenBound=!0,p.addEventListener("click",r),i())}function l(){i();const p=document.getElementById("general-lang");if(p){const f=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";p.value=f}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",d):d(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",l)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(d){const l=d.dataset.collapsible;r[l]?d.classList.add("collapsed"):d.classList.remove("collapsed")})}function i(r){const d=a();d[r]=!d[r],o(d),s()}(function(){const d=a();let l=!1;d.sales===void 0&&(d.sales=!1,l=!0),d.expense===void 0&&(d.expense=!0,l=!0),l&&o(d)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const d=n[r];if(!d)return;const l=a();l[d]&&(l[d]=!1,o(l),s())}})();const Ri=`
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
    </div>`;function Un(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=Ri;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,Un();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const i=o.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let Le=[];window._erpEndpoints=Le;let It=null;async function Ut(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}Le=(await e.json()).items||[],window._erpEndpoints=Le,ja()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return Ut()};async function Aa(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const d=[];d.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&d.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&d.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&d.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=d.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function ja(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&Le.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(Le.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=Le.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:Le.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),Aa(),e.innerHTML=Le.map(s=>{const i=s.config||{},r=escapeHtml(i.url||"");i._token_set;const d=s.enabled!==!1,l=[];s.is_default&&l.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&l.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),d||l.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const p=[];return s.success_count>0&&p.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&p.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(s.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(s.name)}</div>
                        <div class="ep-badges">${l.join("")}</div>
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=Le.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,d=document.createElement("div");d.className="erp-limit-hint",r==="free"?d.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:d.textContent=t("ep-plus-limit-hint",{used:s,limit:i}),e.appendChild(d)}}function Fi(e){It=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),d=document.getElementById("ep-auto-push"),l=document.getElementById("ep-test-result");l.style.display="none",l.textContent="";const p=document.getElementById("ep-save-error");if(p&&p.remove(),e){const c=Le.find(u=>u.id===e);if(!c)return;o.value=c.name||"",s.value=(c.config||{}).url||"",i.value=(c.config||{})._token_set&&c.config.token||"",i.placeholder=(c.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!c.is_default,d.checked=!!c.auto_push}else o.value="",s.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=Le.length===0,d.checked=!0;const f=d.closest(".form-switch-row");if(d.disabled=!1,f){f.classList.remove("disabled-plus"),f.title="",f.style.cursor="",f.onclick=null;const c=f.querySelector(".plus-badge");c&&c.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function Pa(){document.getElementById("endpoint-modal").style.display="none",It=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function Da(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function qa(){const e=document.getElementById("ep-name").value.trim(),n=Da(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:i}}async function zi(){const{url:e,config:n}=qa(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function Ni(){const e=qa(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){Gn(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let i;if(It?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(It)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const d=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof d=="string"?d:JSON.stringify(d))}Pa(),showToast(t("ep-save-ok")),Ut()}catch(i){Gn(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function Gn(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function Oi(e){const n=Le.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),Ut()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=Ut;window.loadErpTodayStats=Aa;window.renderErpEndpointsList=ja;window.openEndpointModal=Fi;window.closeEndpointModal=Pa;window.saveEndpoint=Ni;window.deleteEndpoint=Oi;window.testEndpointConnection=zi;window._sanitizeUrl=Da;async function Ra(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function Vi(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){Ra(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const i=s.dataset.receiptAction;i==="retry"?window.retryPushLog(s.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(I=>I.id===o.endpoint_id),i=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),d=new Date(o.created_at).toLocaleString(),l=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),p=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),f=o.response_body||t("erp-receipt-no-tech"),c=o.status==="success";let u=typeof f=="string"?f:JSON.stringify(f,null,2);if(c)try{const I=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},k=I.row_count||(Array.isArray(I.imported_rows)?I.imported_rows.length:0);k>0&&(u=t("log-push-rows").replace("{n}",String(k)))}catch{}const m=(o.external_doc_no||"").trim(),h=(o.external_url||"").trim(),_=(o.external_doc_hint||"").trim(),w=(o.ocr_buyer_name||"").trim()||o.client_name||"-",b=o.seller_name||"-",v=o.push_type==="id_card";let E="-";const B=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(B)&&(E=B.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const C=c?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),L=c?"✓":"✗",y=[],g=(I,k)=>{y.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(I)}</span>
                    <span class="erp-receipt-val">${k}</span>
                </div>`)};if(g(v?t("erp-log-col-booking"):t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),g(t("erp-receipt-erp-name"),escapeHtml(i)),c){let I;m?I=`<strong class="erp-receipt-docno">${escapeHtml(m)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(m)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:I=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,g(t("erp-receipt-doc-no"),I)}v||g(t("erp-receipt-client"),escapeHtml(w)),g(v?t("erp-log-col-customer"):t("erp-receipt-seller"),escapeHtml(b)),c&&g(t("erp-receipt-amount"),escapeHtml(E)),g(t("erp-receipt-time"),escapeHtml(d)),g(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let x="";c&&h?x=`<a class="erp-receipt-primary-btn" href="${escapeHtml(h)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:c&&m&&(x=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(m)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let T="";if(c&&m&&_){const I="erp-receipt-hint-"+_,k=t(I);k&&k!==I&&(T=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(k)}</span></div>`)}let S="";if(!c){const I=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),k=I?I[0]:"",M=typeof currentLang=="string"&&currentLang||window._currentLang||"th",j=o.error_friendly&&o.error_friendly[M]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),$=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),q=!!(o.history_id&&o.endpoint_id),F=[];F.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),$&&F.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),q&&F.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),S=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${k?`<div class="erp-receipt-errcode">${escapeHtml(k)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(j)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${F.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${c?"ok":"fail"}">${L}</span>
                    ${escapeHtml(C)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(l)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${y.join("")}
            </div>

            ${T}
            ${x?`<div class="erp-receipt-primary-wrap">${x}</div>`:""}
            ${S}

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
                    <pre>${escapeHtml(u)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=Ra;window.showLogDetail=Vi;const Ui=`
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
    `;we("endpoint-modal",Ui);let gt={key:"all",val:""},xt="",Wt=!1,Pe=new Set;window._erpSelected=Pe;async function Gi(){const e=document.getElementById("erp-logs-erp-select");if(!(!e||Wt)){Wt=!0;try{let n=window._erpEndpoints;if(!Array.isArray(n)||n.length===0){const s=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(s.ok){const i=await s.json();n=i&&(i.items||i)||[]}}Array.isArray(n)||(n=[]);const a=new Set,o=[];n.forEach(s=>{const i=(s&&s.adapter||"").toLowerCase();!i||a.has(i)||(a.add(i),o.push({val:i,label:s&&s.name||i}))}),e.innerHTML=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`+o.map(s=>`<option value="${escapeHtml(s.val)}"${s.val===xt?" selected":""}>${escapeHtml(s.label)}</option>`).join("")}catch{Wt=!1}}}async function st(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats(),Gi();try{const a=new URLSearchParams({limit:"30"});gt.key==="status"&&a.set("status",gt.val),gt.key==="trigger"&&a.set("trigger",gt.val),xt&&a.set("adapter",xt);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(m){return m.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){st(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const r=i.filter(function(m){var h=m.status==="failed"&&m.next_retry_at&&new Date(m.next_retry_at).getTime()>Date.now()-6e4;return!h}).map(function(m){return m.id}),d=xt==="mrerp_dms",l=d?t("erp-log-col-booking"):t("erp-log-col-invoice"),p=d?t("erp-log-col-customer"):t("erp-log-col-seller"),f=d?t("erp-log-col-idcard"):t("erp-log-col-client"),c='<div class="erp-log-row erp-log-row-header" data-log-header>'+(r.length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(l)}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(f)}</span><span class="log-seller">${escapeHtml(p)}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=c+i.map(m=>{const h=new Date(m.created_at),_=`${String(h.getMonth()+1).padStart(2,"0")}-${String(h.getDate()).padStart(2,"0")} ${String(h.getHours()).padStart(2,"0")}:${String(h.getMinutes()).padStart(2,"0")}`,w=m.status==="failed"&&m.next_retry_at&&new Date(m.next_retry_at).getTime()>Date.now()-6e4;let b,v,E;m.status==="pending"?(b="retrying",v="⟳",E=t("erp-status-pending")):m.status==="success"?(b="ok",v="✓",E=t("erp-status-success")):m.status==="skipped_dup"?(b="skipped",v="⏭",E=t("erp-status-skipped")):w?(b="retrying",v="↻",E=t("erp-status-retrying")):(b="fail",v="✗",E=t("erp-status-failed"));let B;m.trigger==="auto"?B=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:m.trigger==="retry"?B=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:B=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;const C=m.push_type==="id_card",L=C?`<span class="log-tag log-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span>`:"",y=m.error_friendly&&(m.error_friendly[currentLang]||m.error_friendly.en)||"";let g="";const x=m.retry_count||0,T=m.max_retries||3;if(w){const A=new Date(m.next_retry_at).getTime()-Date.now(),N=Math.max(0,Math.round(A/6e4)),V=N<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:N});g=`${t("erp-retry-attempt",{n:x,max:T})} · ${V}`}else m.status==="failed"&&x>=T&&!m.next_retry_at&&(g=t("erp-retry-exhausted",{n:x}));const S=m.status==="failed"&&!w?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(m.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",I=!w,k=Pe.has(m.id)?"checked":"",M=I?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(m.id)}" ${k}>`:'<span class="erp-log-cb-spacer"></span>',H=(m.ocr_buyer_name||"").trim()||(m.client_name||"").trim(),j=C?`<span class="log-client" title="${escapeHtml(t("erp-log-col-idcard"))}">${m.id_card_tail?"••••"+escapeHtml(m.id_card_tail):"—"}</span>`:H?`<span class="log-client" title="${escapeHtml(H)}">${escapeHtml(H.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,$=C?'<span class="log-workspace log-workspace-unresolved">—</span>':m.workspace_name?`<span class="log-workspace">${escapeHtml((m.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,q=m.endpoint_name?`<span class="log-erp">${escapeHtml((m.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,F=(m.external_doc_no||"").trim(),W=(m.external_url||"").trim();let G;return W?G=`<span class="log-doc"><a href="${escapeHtml(W)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(F||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:F?G=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(F)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(F.substring(0,18))}</span>`:m.status==="success"?G=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:G='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${b}" data-log-detail="${escapeHtml(m.id)}">
                    ${M}
                    <span class="log-time">${_}</span>
                    <span class="log-status" title="${escapeHtml(E+(g?" · "+g:"")+(y?" · "+y:""))}">${v}</span>
                    ${B}${L}
                    <span class="log-invoice"${C?` title="${escapeHtml(t("erp-log-col-booking"))}"`:""}>${escapeHtml(m.invoice_no||"-")}</span>
                    ${$}
                    ${j}
                    <span class="log-seller"${C?` title="${escapeHtml(t("erp-log-col-customer"))}"`:""}>${escapeHtml((m.seller_name||"").substring(0,20))}</span>
                    ${q}
                    ${G}
                    <span class="log-http">HTTP ${m.http_status||"-"}</span>
                    <span class="log-elapsed">${m.elapsed_ms}ms</span>
                    <span class="log-actions">${S}</span>
                </div>
            `}).join("");const u=new Set(i.map(m=>m.id));for(const m of Array.from(Pe))u.has(m)||Pe.delete(m);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function Fa(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),st(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),Fa(s.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const f=i.dataset.logCb;i.checked?Pe.add(f):Pe.delete(f),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const f=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(u){u.checked=f;const m=u.dataset.logCb;f?Pe.add(m):Pe.delete(m)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),Pe.clear(),document.querySelectorAll(".erp-log-cb").forEach(f=>{f.checked=!1}),window._refreshErpBatchBar();return}const d=n.target.closest("[data-log-detail]");if(d){if(n.target.closest("[data-log-cb]"))return;const f=n.target.closest("[data-copy-doc]");if(f){n.stopPropagation(),window.copyErpDocNo(f.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(d.dataset.logDetail);return}const l=n.target.closest(".chip-filter");if(l){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(f=>f.classList.remove("active")),l.classList.add("active"),gt={key:l.dataset.filterKey,val:l.dataset.filterVal},st();return}if(n.target.closest("#btn-refresh-logs")){const f=n.target.closest("#btn-refresh-logs");f.classList.add("spinning"),setTimeout(()=>f.classList.remove("spinning"),600),st();return}const p=n.target.closest(".auto-nav-item");if(p&&p.dataset.autoTab){switchAutomationTab(p.dataset.autoTab);return}}),document.addEventListener("change",n=>{n.target&&n.target.id==="erp-logs-erp-select"&&(xt=n.target.value||"",st())})})();window.loadErpLogs=st;window.retryPushLog=Fa;function za(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function Na(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),i=o.failed&&o.failed>0?"warn":"success";showToast(s,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function Oa(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),Na()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),Oa()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),za()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=za;window._runErpBatchRetry=Na;window._runErpBatchDelete=Oa;(function(){let e=null,n=!1;function a(){if(e)return e;const d=document.createElement("div");d.id="line-email-modal",d.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",d.innerHTML=`
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
        `,document.body.appendChild(d),e=d;const l=d.querySelector("#line-email-input"),p=d.querySelector("#line-email-submit-btn"),f=d.querySelector("#line-email-err");async function c(){f.textContent="";const u=(l.value||"").trim().toLowerCase();if(!u||u.indexOf("@")<0||u.split("@")[1].indexOf(".")<0){f.textContent=t("line-email-err-invalid");return}p.disabled=!0,p.style.opacity="0.6";try{const m=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:u})});if(!m.ok)throw new Error("http_"+m.status);const h=await m.json();h.token&&localStorage.setItem("mrpilot_token",h.token),typeof showToast=="function"&&showToast(h.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{f.textContent=t("line-email-err-failed"),p.disabled=!1,p.style.opacity="1"}}return p.addEventListener("click",c),l.addEventListener("keydown",function(u){u.key==="Enter"&&c()}),d}function o(){if(!e)return;const d=e.querySelector("#line-email-title-h"),l=e.querySelector("#line-email-sub-p"),p=e.querySelector("#line-email-input"),f=e.querySelector("#line-email-submit-btn");d&&(d.textContent=t("line-email-title")),l&&(l.textContent=t("line-email-sub")),p&&(p.placeholder=t("line-email-placeholder")),f&&(f.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const d=e.querySelector("#line-email-input");d&&setTimeout(function(){d.focus()},100)}async function i(){const d=localStorage.getItem("mrpilot_token");if(d)try{const l=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+d}});if(!l.ok)return;const p=await l.json();p&&p.needs_email&&s()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(f){let c=0;return f.length>=8&&c++,f.length>=12&&c++,/[a-zA-Z]/.test(f)&&/\d/.test(f)&&c++,/[^a-zA-Z0-9]/.test(f)&&c++,Math.min(3,c)}function n(f,c){const u=document.getElementById("cpw-msg");u&&(u.textContent=f,u.className="cpw-msg "+(c||""))}function a(f){return typeof t=="function"?t(f):f}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(c=>{const u=document.getElementById(c);u&&(u.value="",u.setAttribute("readonly","readonly"))});const f=document.getElementById("cpw-strength-bar");f&&(f.style.width="0%",f.className="cpw-strength-bar"),n("","")}async function i(){const f=document.getElementById("btn-change-pw"),c=document.getElementById("cpw-old"),u=document.getElementById("cpw-new"),m=document.getElementById("cpw-confirm"),h=document.getElementById("cpw-strength-bar");if(!f||!c||!u||!m)return;const _=c.value,w=u.value,b=m.value;if(!_||!w||!b){n(a("settings-change-pw-empty"),"error");return}if(w.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(w)&&/\d/.test(w))){n(a("settings-change-pw-too-weak"),"error");return}if(w!==b){n(a("settings-change-pw-mismatch"),"error");return}f.disabled=!0;const v=f.textContent;f.textContent=a("settings-change-pw-submitting"),n("","");try{const E=localStorage.getItem("mrpilot_token"),B=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+E},body:JSON.stringify({old_password:_,new_password:w})}),C=await B.json().catch(()=>({}));if(B.ok&&C.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),c.value="",u.value="",m.value="",h&&(h.style.width="0%",h.className="cpw-strength-bar");else{const L=C.detail||"";let y=a("settings-change-pw-success");L==="wrong_old_password"?y=a("settings-change-pw-wrong-old"):L==="password_too_short"?y=a("settings-change-pw-too-short"):L==="password_too_weak"?y=a("settings-change-pw-too-weak"):y=L||"Error",n(y,"error")}}catch(E){console.error("change_password",E),n("Network error","error")}finally{f.disabled=!1,f.textContent=v}}function r(){o||(o=!0,document.addEventListener("click",f=>{if(!f.target||!f.target.closest)return;const c=f.target.closest(".cpw-eye");if(c){const u=document.getElementById(c.dataset.target);u&&(u.type=u.type==="password"?"text":"password");return}if(f.target.closest("#cpw-forgot-link")){f.preventDefault(),d();return}if(f.target.closest("#btn-change-pw")){i();return}f.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",f=>{if(f.target&&f.target.id==="cpw-new"){const c=document.getElementById("cpw-strength-bar");if(!c)return;const u=e(f.target.value),m=["0%","33%","66%","100%"],h=["","weak","medium","strong"];c.style.width=m[u],c.className="cpw-strength-bar "+h[u]}}),document.addEventListener("focusin",f=>{f.target&&["cpw-old","cpw-new","cpw-confirm"].includes(f.target.id)&&f.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function d(){const f=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),c=f&&f.username?f.username:"",u=l(c);let m=document.getElementById("cpw-forgot-overlay");m&&m.remove(),m=document.createElement("div"),m.id="cpw-forgot-overlay",m.className="cpw-forgot-overlay",m.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${p(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${p(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${p(u)}</div>
                    <p class="cpw-forgot-tip">${p(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${p(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${p(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(m);const h=()=>m.remove();m.querySelector("#cpw-forgot-close").addEventListener("click",h),m.querySelector("#cpw-forgot-cancel").addEventListener("click",h),m.addEventListener("click",_=>{_.target===m&&h()}),m.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const _=m.querySelector("#cpw-forgot-send"),w=m.querySelector("#cpw-forgot-msg");_.disabled=!0;const b=_.textContent;_.textContent=a("cpw-forgot-sending");try{const v=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:c})}),E=await v.json().catch(()=>({}));v.ok?(w.textContent=a("cpw-forgot-success"),w.className="cpw-forgot-msg success",_.style.display="none",m.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(w.textContent=E.detail||a("cpw-forgot-fail"),w.className="cpw-forgot-msg error",_.disabled=!1,_.textContent=b)}catch{w.textContent=a("cpw-forgot-fail"),w.className="cpw-forgot-msg error",_.disabled=!1,_.textContent=b}})}function l(f){if(!f||!f.includes("@"))return f||"";const[c,u]=f.split("@");return c.length<=2?c+"****@"+u:c.slice(0,2)+"****@"+u}function p(f){return f==null?"":String(f).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),d=r&&r.detail;let l="";if(typeof d=="string"?l=d:d&&typeof d=="object"&&(l=d.code||""),console.warn("[heartbeat] session revoked",l),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),l==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const p=l==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(p),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function Gt(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),i=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const d=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",l=r.is_active===!1?"team-status-off":"team-status-on",p=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",f=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${l}"></span>
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Ki(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),d=document.getElementById("add-emp-submit"),l=(o.value||"").trim(),p=(s.value||"").trim(),f=i.value||"";if(r.textContent="",r.classList.remove("error"),!l||l.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(l)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(p&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(f.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(f)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(f)&&/\d/.test(f))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}d.disabled=!0,d.textContent=t("msg-saving")||"保存中...";try{const c={username:l,password:f};p&&(c.email=p);const u=await apiPost("/api/team/employees",c),m=u?await u.json().catch(()=>({})):{};if(u&&u.ok&&m&&m.ok){showToast(t("team-added")||"员工已添加","success"),n(),Gt();return}const h=m&&m.detail||"unknown",_={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=_[h]||(t("team-create-failed")||"创建失败")+" ("+h+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{d.disabled=!1,d.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function Ji(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){Gt();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Yi(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),Gt();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function Wi(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const d=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",l=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(d.replace("{ch}",l),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Ki();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),Ji(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),Yi(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),Wi(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=Gt;function Xi(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=Xi;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
