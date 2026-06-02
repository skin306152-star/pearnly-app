(function(){const n=[];function a(s){try{n.push(Object.assign({ts:Date.now()},s)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(s)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(s){s.target&&s.target!==window&&(s.target.src||s.target.href)||a({type:"js_error",summary:String(s.message||"JS Error").slice(0,200),detail:{file:s.filename||"",line:s.lineno||0,col:s.colno||0,stack:s.error&&s.error.stack?String(s.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(s){const i=s.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const o=window.fetch;typeof o=="function"&&(window.fetch=function(){const s=arguments,i=Date.now(),r=typeof s[0]=="string"?s[0]:s[0]&&s[0].url||"?",d=s[1]&&s[1].method||"GET",l=String(r).split("?")[0];return o.apply(this,s).then(function(p){const m=Date.now()-i;if(p.ok)m>2500&&a({type:"api_slow",summary:d+" "+l+" → 慢 "+m+"ms",detail:{url:r,method:d,status:p.status,elapsed_ms:m}});else{let c="";try{p.clone().text().then(function(f){c=String(f||"").slice(0,500),a({type:"api_error",summary:d+" "+l+" → "+p.status+" ("+m+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:m,body_preview:c}})}).catch(function(){a({type:"api_error",summary:d+" "+l+" → "+p.status+" ("+m+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:m,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:d+" "+l+" → "+p.status+" ("+m+"ms)",detail:{url:r,method:d,status:p.status,elapsed_ms:m}})}}return p}).catch(function(p){const m=Date.now()-i;throw a({type:"api_fail",summary:d+" "+l+" → 网络失败 ("+m+"ms)",detail:{url:r,method:d,elapsed_ms:m,error:String(p&&p.message||p)}}),p})}),["error","warn"].forEach(function(s){const i=console[s];typeof i=="function"&&(console[s]=function(){try{const r=[];for(let d=0;d<arguments.length;d++){const l=arguments[d];if(typeof l=="string")r.push(l);else if(l&&l instanceof Error)r.push(l.message);else try{r.push(JSON.stringify(l).slice(0,300))}catch{r.push(String(l))}}a({type:"console_"+s,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(o=>o.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function ia(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function ra(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function la(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function vt(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const o in n)a=a.replace("{"+o+"}",n[o]);return a}function ca(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function da(e,n){n=n||14;const o={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${o}</svg>`}function ht(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},o={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},s=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[s]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[s]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+o[s]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function gt(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function pa(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...gt()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),o=a&&a.detail;let s="";if(typeof o=="string"?s=o:o&&typeof o=="object"&&(s=o.code||""),n.status===401||typeof s=="string"&&s.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,o),localStorage.removeItem("mrpilot_token"),s==="auth.session_revoked")ht();else{const d=s==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(vt(d),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=o,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function ua(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...gt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.clone().json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")ht();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(vt(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function fa(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...gt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")ht();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(vt(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const o=await a.json().catch(()=>({}));return{ok:a.ok&&o.ok!==!1,...o}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=pa;window.apiPost=ua;window.t=vt;window.escapeHtml=ca;window.svgIcon=da;window._showSessionRevokedModal=ht;window._wsHeader=gt;window.apiPut=fa;window.getMaxFiles=ia;window.getMaxPagesPerFile=ra;window.getMaxMbPerFile=la;function we(e,n){const a=document.getElementById(e);if(!(!a||a.dataset.wbInjected==="1")){a.innerHTML=n,a.dataset.wbInjected="1";try{const o=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",s=window.I18N;if(!s||!s[o])return;a.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");s[o][r]&&(i.textContent=s[o][r])}),a.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");s[o][r]&&(i.placeholder=s[o][r])})}catch{}}}const ma=`
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
    `;we("page-ocr",ma);const va=`
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
`,ha=`
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
`;we("topbar",va);we("sidebar",ha);function jt(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const o=document.getElementById("general-lang");o&&(o.value=e);const s=document.getElementById("col-conf-th");s&&s.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&Pt(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function ga(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",s=>{s.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(s)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});ga("lang-dropdown",e=>jt(e.dataset.lang));const un=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","receivables","reconcile","cloud","test-center"];function fn(e){un.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(o=>o.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(o=>{o.classList.toggle("active",o.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function mn(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){return!i||typeof i!="string"||(i=i.trim(),!i)?null:i.includes("@")&&i.indexOf("@")>0&&i.indexOf(".")>i.indexOf("@")?i.split("@")[0]:i}const o=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let s=null;for(const i of o){const r=a(i);if(r){s=r;break}}s||(s=t("brand-workspace-fallback")||"我的工作台"),e.textContent=s,e.title=s,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",s,"· _userInfo fields:",Object.keys(n))}function Pt(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function vn(){try{const[e,n,a,o]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(s=>s.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,o&&(window._planState=o),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const s=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(s&&!i){window.location.replace("/home");return}if(!s&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=s}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,o&&(window._planState=o),mn(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(s){console.error("[nav-ia phase1] render avatar menu",s)}Pt(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const s=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(s&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(s&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(s){console.error("force-pw init",s)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(s){console.error("onboarding init",s)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(s){console.error("settings forms init",s)}}catch(e){console.error(e)}}function ba(){let e=document.getElementById("offline-banner");e||(e=document.createElement("div"),e.id="offline-banner",e.className="offline-banner",e.style.display="none",document.body.insertBefore(e,document.body.firstChild));function n(){navigator.onLine===!1?(e.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",e.classList.remove("is-online"),e.classList.add("is-offline"),e.style.display="flex"):e.classList.contains("is-offline")?(e.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",e.classList.remove("is-offline"),e.classList.add("is-online"),setTimeout(()=>{e.style.display="none",e.classList.remove("is-online")},2e3)):e.style.display="none"}window.addEventListener("online",n),window.addEventListener("offline",n),n()}window.applyLang=jt;window.routeTo=fn;window.loadAll=vn;window.renderBrandWorkspace=mn;window.updateUploadHint=Pt;window.installNetworkBanner=ba;try{jt(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");fn(un.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);vn();const hn="mrpilot_sidebar_collapsed";localStorage.getItem(hn)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(hn,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const o=document.querySelectorAll("#page-integrations .int-top-tab"),s=document.querySelectorAll("#page-integrations .int-top-panel");if(o.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),s.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),o&&o.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const o=a.target.closest("#page-integrations .int-top-tab");if(o){const i=o.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const o=document.querySelector(".auto-content");o&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(s){s.style.display="",o.appendChild(s)})}window.openIntegrationDrawer=function(a,o){const s=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),d=document.getElementById("int-drawer-body");if(!s||!d)return;e(),s.dataset.currentTab=a||"",r&&(r.textContent=o||""),d.innerHTML="";var l={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},p=l[a]||a;const m=document.querySelector('.auto-panel[data-auto-panel="'+p+'"]');m?(m.style.display="block",d.appendChild(m)):d.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',s.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var c={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(c[a])try{c[a]()}catch(u){console.warn("[int-drawer] loader error",u)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(u){console.warn("[int-drawer] ERP load error",u)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),o&&(o.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),o=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),o&&o.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(s){s.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(s=>{s.addEventListener("click",()=>switchSettingsTab(s.dataset.tab))});let o=null;try{o=localStorage.getItem("mrpilot_settings_tab")}catch{}if(o){const s=document.querySelector(`.settings-tab[data-tab="${o}"]`);if(s&&s.style.display!=="none"){switchSettingsTab(o);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),o=document.getElementById("btn-save-company");if(!a&&!o){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),o&&o.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let it=null;function ya(){Ct(),it=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&Ct()}catch{}},1e4)}function Ct(){it&&(clearInterval(it),it=null)}window.startEnginePolling=ya;window.stopEnginePolling=Ct;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target.closest("[data-rd-action]");if(n){const s=n.dataset.rdAction,i=n.dataset.rdSide;s==="verify"?callRdVerify(i):s==="sync"&&callRdSync(i);return}if(e.target.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=e.target.closest("[data-archive-copy]");if(o){const s=o.dataset.archiveCopy;navigator.clipboard?.writeText(s).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const Zt=document.getElementById("btn-custom-template");Zt&&Zt.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});const wa=`
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
    `,ka=`
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
`;we("pearnly-confirm-modal",wa);we("confirm-modal",ka);window.pearnlyConfirm=function(e,n){return new Promise(function(a){const o=document.getElementById("pearnly-confirm-modal"),s=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),d=document.getElementById("pearnly-confirm-cancel"),l=document.getElementById("pearnly-confirm-close");if(!o||!i||!r||!d){a(window.confirm(e));return}s&&(s.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",o.style.display="flex";function p(b){o.style.display="none",r.removeEventListener("click",m),d.removeEventListener("click",c),l&&l.removeEventListener("click",c),o.removeEventListener("click",u),document.removeEventListener("keydown",f),a(b)}function m(){p(!0)}function c(){p(!1)}function u(b){b.target===o&&p(!1)}function f(b){b.key==="Escape"?p(!1):b.key==="Enter"&&p(!0)}r.addEventListener("click",m),d.addEventListener("click",c),l&&l.addEventListener("click",c),o.addEventListener("click",u),document.addEventListener("keydown",f),setTimeout(function(){try{d.focus()}catch{}},50)})};const xa=`
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

`,_a=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=xa+_a,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Ea=`
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

`,Ba=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Ea+Ba,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function Ia(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function La(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function Ca(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function Sa(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function Ta(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let d=null;const l=()=>{d&&(clearTimeout(d),d=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(d=setTimeout(l,r)),l}window.showAlert=Ia;window.hideAlerts=La;window._humanizeBackendError=Ca;window.humanizeError=Sa;window.showToast=Ta;function Ma(e,n){return n=n||{},new Promise(a=>{const o=document.getElementById("confirm-modal"),s=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),d=document.getElementById("confirm-modal-close"),l=document.getElementById("confirm-modal-title");if(!o||!s||!i||!r){a(!1);return}l.textContent=n.title||t("confirm-default-title");const p=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const f=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),b=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");s.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${f}</div>
                <input type="text" id="${p}" placeholder="${b}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else s.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",o.style.display="flex";const m=f=>{o.style.display="none",i.onclick=null,r.onclick=null,d.onclick=null,o.onclick=null,document.removeEventListener("keydown",u),n.promptInput&&(s.innerHTML=""),r.style.display="",a(f)},c=()=>{const f=p?document.getElementById(p):null;return f?f.value:""},u=f=>{f.key==="Escape"?m(n.promptInput?null:!1):f.key==="Enter"&&m(n.promptInput?c():!0)};i.onclick=()=>m(n.promptInput?c():!0),r.onclick=()=>m(n.promptInput?null:!1),d.onclick=()=>m(n.promptInput?null:!1),o.onclick=f=>{f.target===o&&m(n.promptInput?null:!1)},document.addEventListener("keydown",u),setTimeout(()=>{if(n.promptInput){const f=document.getElementById(p);f&&f.focus()}else i.focus()},50)})}window.showConfirm=Ma;function $a(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof St=="function"&&St()}catch(n){console.warn("settings tab side effect failed:",n)}}}function Ha(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function Aa(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function ja(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function St(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}Pa(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function Pa(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
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
    `}window.switchSettingsTab=$a;window.fillSettingsForms=Ha;window.saveProfile=Aa;window.saveCompany=ja;window.renderSettings=St;function bt(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function Dt(e){return e=e||_userInfo,!!e&&(e.role==="owner"||bt(e))}function gn(e){return e=e||_userInfo,!!e&&e.role==="member"&&!bt(e)}function Da(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!bt(e)}function bn(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function yn(e){return gn(e)}function qa(e){return Dt(e)}function Ra(e){return Dt(e)&&bn(e)}window.isMoneyHidden=yn;window.isSuperAdmin=bt;window.isOwner=Dt;window.isEmployee=gn;window.isTrial=Da;window.isLifetime=bn;window.shouldHideMoney=yn;window.canManageTeam=qa;window.canManageApiKey=Ra;function Fa(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,d;if(o===0)r="danger",d=t("quota-banner-exhausted");else if(s>=90)r="danger",d=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",d=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(d)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const l=e.querySelector(".quota-banner-close");l&&l.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function za(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const d=document.querySelector('.settings-tab[data-tab="team"]');d&&(d.style.display=a?"":"none");const l=document.querySelector('.settings-panel[data-settings-panel="team"]');l&&(l.dataset.permHidden=a?"0":"1");const p=document.querySelector('.settings-tab[data-tab="api"]');p&&(p.style.display=o||isSuperAdmin(e)?"":"none");const m=document.querySelector('.settings-tab[data-tab="plan"]');m&&(m.style.display=n?"none":"");const c=document.querySelector('.settings-tab[data-tab="company"]');c&&(c.style.display=n?"none":"");const u=document.getElementById("info-bar");u&&(u.style.display=n?"none":"");const f=document.getElementById("trial-banner");f&&n&&(f.style.display="none");const b=document.getElementById("plan-banner");b&&n&&(b.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(B=>{B.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const B=document.querySelector(".settings-tab.active");B&&B.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(B){console.warn("[v118.12.3] failed to fix active tab:",B)}if(window.PEARNLY_ADMIN_MODE){const B=document.getElementById("admin-mode-banner");B&&(B.style.display="flex"),document.querySelectorAll(".nav-item").forEach(h=>{h.classList.contains("nav-admin-only")||(h.style.display="none")}),document.querySelectorAll(".nav-group").forEach(h=>{h.classList.contains("nav-group-admin-only")||(h.style.display="none")});const x=document.getElementById("client-switcher");x&&(x.style.display="none"),document.body.classList.add("admin-mode");const v=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(h=>{const L=h.dataset.tab;L&&!v.includes(L)&&(h.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(h=>{const L=h.dataset.pane;L&&!v.includes(L)&&(h.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(h=>{const L=h.querySelectorAll(".settings-tab");Array.from(L).some(S=>S.style.display!=="none")||(h.style.display="none")})}}function Na(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
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
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=Fa;window.applySidebarVisibility=za;window.renderInfoBar=Na;async function wn(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function kn(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function lt(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function De(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function Oa(e){const a=lt(e==="seller"?"seller_tax":"buyer_tax");De(e,t("rd-verifying"),"loading");const o=await wn("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){De(e,t(kn(o.error)),"error");return}o.data&&o.data.valid?De(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):De(e,t("rd-status-invalid"),"invalid")}async function Va(e){const a=lt(e==="seller"?"seller_tax":"buyer_tax");De(e,t("rd-syncing"),"loading");const o=await wn("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){De(e,t(kn(o.error)),"error");return}De(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),Ua(e,o.data)}}function Ua(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=lt(a),i=lt(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==i&&r.push({field:o,label:t("rd-field-address"),current:i,official:n.address});const d=[];n.branch_label&&d.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&d.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let l=document.getElementById("rd-sync-modal");if(l||(l=document.createElement("div"),l.id="rd-sync-modal",l.className="rd-modal-mask",document.body.appendChild(l)),r.length===0)l.innerHTML=`
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
        `;else{const c=r.map((u,f)=>`
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
        `}l.classList.add("show");const p=()=>l.classList.remove("show");l.querySelector(".rd-modal-close").addEventListener("click",p),l.querySelectorAll("[data-rd-modal-close]").forEach(c=>c.addEventListener("click",p)),l.addEventListener("click",c=>{c.target===l&&p()});const m=l.querySelector("[data-rd-modal-apply]");m&&m.addEventListener("click",()=>{const c=_results[_drawerIdx];if(!c){p();return}l.querySelectorAll("[data-rd-apply]:checked").forEach(u=>{const f=u.dataset.field,b=u.dataset.value;c.edits[f]=b,c.merged_fields[f]=b;const B=document.querySelector(`[data-field="${f}"]`);B&&(B.value=b);const x=document.querySelector(`[data-field-wrap="${f}"]`);x&&x.classList.add("edited")}),updateDrawerEditCount(),renderResults(),p()})}window.callRdVerify=Oa;window.callRdSync=Va;function Ga(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(s=>!s.is_duplicate&&!s.is_copy),o=a.length>0?a:e;for(const s of o){const i=s.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function Ka(e){const n=e.target.dataset.field,a=e.target.value,o=_results[_drawerIdx],s=o.merged_fields[n];a===(s??"")?delete o.edits[n]:(o.edits[n]=a,o.merged_fields[n]=a);const i=document.querySelector(`[data-field-wrap="${n}"]`);i&&i.classList.toggle("edited",o.edits[n]!==void 0),xn(),renderResults()}function xn(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=Ga;window.onFieldEdit=Ka;window.updateDrawerEditCount=xn;function Ja(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,o=document.getElementById("force-pw-new").value,s=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!o){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(o!==s){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(o.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(o)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(o)&&/\d/.test(o))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(o===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:o})}),d=await r.json().catch(()=>({}));if(!r.ok){const l=d&&d.detail||"unknown",p={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=p[l]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=Ja;(function(){let e=null,n=null,a=null,o=null;function s(h){return document.getElementById(h)}async function i(){b(),x(),await r()}async function r(){try{const h=localStorage.getItem("mrpilot_token"),L=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!L.ok){B(t("linebot-err-status"));return}const I=await L.json();I.bound?d(I):await l()}catch{B(t("linebot-err-status"))}}function d(h){f(),s("linebot-unbound").style.display="none",s("linebot-bound").style.display="block";const L=s("linebot-status-summary");L&&(L.textContent=t("linebot-status-bound"),L.style.background="#D1FAE5",L.style.color="#065F46");const I=s("linebot-bound-name");I&&(I.textContent=h.line_display_name||"(LINE User)");const S=s("linebot-avatar");S&&(h.line_picture_url?(S.src=h.line_picture_url,S.style.display=""):S.style.display="none");const C=s("linebot-bound-since");C&&h.bound_at&&(C.textContent=new Date(h.bound_at).toLocaleString())}async function l(){s("linebot-bound").style.display="none",s("linebot-unbound").style.display="block";const h=s("linebot-status-summary");h&&(h.textContent=t("linebot-status-unbound"),h.style.background="#FEE2E2",h.style.color="#B91C1C"),await p(),u()}async function p(){try{const h=localStorage.getItem("mrpilot_token"),L=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+h}});if(!L.ok){B(t("linebot-err-code"));return}const I=await L.json();a=I.code,o=new Date(I.expires_at).getTime(),m(I)}catch{B(t("linebot-err-code"))}}function m(h){const L=s("linebot-code");L&&(L.textContent=h.code);const I=s("linebot-bot-id");I&&(I.textContent=h.bot_basic_id||t("linebot-bot-id-missing"));const S=s("linebot-qr");if(S)if(h.bot_friend_url){const C="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(h.bot_friend_url);S.classList.remove("empty"),S.innerHTML='<img src="'+C+'" alt="LINE Bot QR">'}else S.classList.add("empty"),S.innerHTML="";c()}function c(){e&&clearInterval(e);const h=s("linebot-code-expires");function L(){if(!o)return;const I=o-Date.now();if(I<=0){h&&(h.textContent=t("linebot-code-expired"),h.classList.add("expiring"));const g=s("linebot-code");g&&(g.style.opacity="0.4"),clearInterval(e),e=null;return}const S=Math.floor(I/1e3),C=Math.floor(S/60),w=S%60;h&&(h.textContent=t("linebot-code-expires-in").replace("{m}",C).replace("{s}",String(w).padStart(2,"0")),I<6e4?h.classList.add("expiring"):h.classList.remove("expiring"))}L(),e=setInterval(L,1e3)}function u(){f(),n=setInterval(async()=>{try{const h=localStorage.getItem("mrpilot_token"),L=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!L.ok)return;const I=await L.json();I.bound&&d(I)}catch{}},4e3)}function f(){n&&(clearInterval(n),n=null)}function b(){e&&(clearInterval(e),e=null),f()}function B(h){const L=s("linebot-error");L&&(L.textContent=h,L.style.display="block")}function x(){const h=s("linebot-error");h&&(h.style.display="none")}async function v(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const L=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+L}})).ok){B(t("linebot-err-unbind"));return}await i()}catch{B(t("linebot-err-unbind"))}}document.addEventListener("click",h=>{if(h.target.closest("#linebot-code-refresh")){h.preventDefault(),x(),p();return}if(h.target.closest("#linebot-unbind")){h.preventDefault(),v();return}}),window._loadLineBotPanel=i})();function yt(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const d=parseFloat(r.merged_fields.total_amount);isNaN(d)||(n+=d)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,d)=>({...r,_idx:d}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(d=>(d.filename||"").toLowerCase().includes(r)||(d.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,d)=>{let l,p;return _sortKey==="filename"?(l=r.filename,p=d.filename):_sortKey==="invoice_no"?(l=r.merged_fields.invoice_number,p=d.merged_fields.invoice_number):_sortKey==="invoice_date"?(l=r.merged_fields.date,p=d.merged_fields.date):_sortKey==="total"?(l=parseFloat(r.merged_fields.total_amount)||0,p=parseFloat(d.merged_fields.total_amount)||0):_sortKey==="confidence"?(l=r.confidence,p=d.confidence):(l="",p=""),l<p?_sortDir==="asc"?-1:1:l>p?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=s.map((r,d)=>{const l=r.merged_fields,p=`<span class="empty-cell">${t("empty-val")}</span>`,m="conf-tip-"+(r.confidence||"low"),c="conf-"+(r.confidence||"low"),u=t(m),f=t(c);return`
            <tr data-idx="${r._idx}">
                <td class="num">${d+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${l.invoice_number?escapeHtml(l.invoice_number):p}</td>
                <td class="date">${l.date?escapeHtml(l.date):p}</td>
                <td class="amount">${l.total_amount?Number(l.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):p}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(u)}">${f}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const d=parseInt(r.dataset.idx,10);En(d)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),yt()})});let Qt=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(Qt),Qt=setTimeout(()=>{_searchKeyword=n.trim(),yt(),_n()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",yt(),_n(),e.focus()});function _n(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function En(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
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
            ${xe("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",s)}
            ${xe("date","drawer-lbl-date",r.date,"input",s)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${xe("subtotal","drawer-lbl-subtotal",r.subtotal,"input",s)}
            ${xe("vat","drawer-lbl-vat",r.vat,"input",s)}
            ${xe("total_amount","drawer-lbl-total",r.total_amount,"input",s)}
            ${r.wht_amount||r.wht_rate?`
                ${xe("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,Ya(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${xe("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${xe("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,p,en("seller"))}
            ${xe("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${xe("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${xe("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,p,en("buyer"))}
            ${xe("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?Wa(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${xe("notes","drawer-lbl-notes",r.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(m=>`--- Page ${m.page||m.page_number||"?"} ---
${m.raw_text||m.text||""}`).join(`

`))}</pre>
        </details>
    `,s?d.querySelectorAll("[data-field]").forEach(m=>{m.addEventListener("input",onFieldEdit)}):d.querySelectorAll("[data-field]").forEach(m=>{m.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const m=n._historyId||n.history_id||null;window.bindDrawerClient(m,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const m=document.getElementById("drawer-cat-input");m&&!m.value&&!m.readOnly&&m.focus()},80)}function Ya(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function xe(e,n,a,o,s,i,r){const d=_results[_drawerIdx],l=d&&d.edits[e]!==void 0?d.edits[e]:a,p=d&&d.edits[e]!==void 0&&d.edits[e]!==a,m=escapeHtml(l??""),c=s?"":"readonly",u=o==="textarea"?`<textarea data-field="${e}" rows="2">${m}</textarea>`:`<input type="text" data-field="${e}" value="${m}">`;return`
        <div class="drawer-field ${p?"edited":""} ${c}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${u}
        </div>
    `}function en(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function Wa(e){return`
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
    `}function Xa(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=yt;window.openDrawer=En;window.closeDrawer=Xa;function Za(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(d){return d&&d.enabled!==!1&&(d.adapter||"").toLowerCase()!=="mrerp_dms"});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let i;if(o.length===1){const d=o[0].name||o[0].adapter||"ERP";i=t("btn-push-to-name",{name:d}),s.title=i}else i=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,s.addEventListener("click",function(d){d.preventDefault(),d.stopPropagation(),o.length===1?Bn(n,o[0].id):Qa(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function Qa(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(l=>l.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const i=a.map(function(l){const p=escapeHtml(l.name||l.adapter||"ERP"),m=escapeHtml((l.adapter||"").toLowerCase()),u=l.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(l.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+m+"</span>"+p+u+"</span></button>"}).join("");s.innerHTML=i,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",d,!0)},d=l=>{!s.contains(l.target)&&l.target!==e&&!e.contains(l.target)&&r()};setTimeout(()=>document.addEventListener("click",d,!0),0),s.addEventListener("click",l=>{const p=l.target.closest("[data-ep-id]");if(!p)return;const m=p.getAttribute("data-ep-id");r(),Bn(n,m)})}async function Bn(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),i=await s.json();if(!s.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=Za;const eo=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function In(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function to(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function Ln(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const p=[];for(const m of _results){const c=m.invoices&&m.invoices.length>0?m.invoices:null;if(c&&c.length>1)for(let u=0;u<c.length;u++){const f=c[u]||{};p.push({filename:m.filename+" #"+(u+1)+"/"+c.length,engine:m.engine,merged_fields:f.fields||{}})}else p.push({filename:m.filename,engine:m.engine,merged_fields:m.merged_fields})}a=await apiPost("/api/ocr/export",{records:p,lang:currentLang,template:"sales_detail_th"})}else{const p=[];for(const c of _results)c.history_ids&&Array.isArray(c.history_ids)?p.push(...c.history_ids):c.history_id&&p.push(c.history_id);if(p.length===0){showToast(t("toast-export-error"),"error");return}const m=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+m,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:p,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let p="HTTP "+a.status;try{const c=await a.json();c&&c.detail&&(p=typeof c.detail=="string"?c.detail:JSON.stringify(c.detail))}catch(c){console.warn("[export] resp.json err.detail parse failed:",c)}const m=typeof p=="string"&&p.indexOf(".")>0?"err."+p:null;showToast(m?t(m):t("toast-export-error")+" · "+p,"error");return}const s=await a.blob();let i=o;const r=a.headers.get("X-Filename");if(r)i=r;else{const m=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(m)try{i=decodeURIComponent(m[1])}catch{}}const d=URL.createObjectURL(s),l=document.createElement("a");l.href=d,l.download=i,document.body.appendChild(l),l.click(),document.body.removeChild(l),URL.revokeObjectURL(d),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{Ln(In())});function no(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=In(),o=eo.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
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
    `;n.innerHTML=o+s,e.appendChild(n)}function Et(){const e=document.getElementById("export-dropdown");e&&e.remove()}const Bt=document.getElementById("btn-export-arrow");Bt&&Bt.addEventListener("click",e=>{e.stopPropagation(),!Bt.disabled&&no()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){Et(),showToast(t("cs-coming-soon"),"info");return}to(a),Et(),Ln(a);return}e.target.closest("#btn-export-arrow")||Et()});function ao(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(ao,300);const oo=`
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
`;(function(){const e=document.getElementById("page-history");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=oo,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();function qt(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const i=s.filter(r=>_historySelected.has(r.id)).length;a.checked=i===s.length,a.indeterminate=i>0&&i<s.length}}}function so(){_historySelected.clear(),qt()}async function Rt(){if(!_userInfo){setTimeout(()=>Rt(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&s.set("client_id",String(i));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const p=await r.json().catch(()=>({}));if((typeof p.detail=="string"?p.detail:p.detail&&p.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const d=await r.json();_historyState.items=d.items||[],_historyState.total=d.total||0;const l=new Set(_historyState.items.map(p=>p.id));for(const p of Array.from(_historySelected))l.has(p)||_historySelected.delete(p);Cn()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function Cn(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(p=>{p.confidence==="high"&&s++});const i=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(p=>{const m=new Date(p.created_at),c=String(m.getMonth()+1).padStart(2,"0"),u=String(m.getDate()).padStart(2,"0"),f=String(m.getHours()).padStart(2,"0"),b=String(m.getMinutes()).padStart(2,"0"),B=`${c}-${u} ${f}:${b}`,x=escapeHtml(p.filename||""),v=x.length>50?x.substring(0,50)+"…":x,h=p.invoice_no?escapeHtml(p.invoice_no):v,L=[];p.seller_name&&L.push(escapeHtml(p.seller_name)),p.invoice_no&&p.filename&&L.push(v);const I=L.join(" · ")||"-",S=p.category_tag?`<span class="history-badge category">${escapeHtml(p.category_tag)}</span>`:"",C=p.source_total&&p.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:p.source_index||1,n:p.source_total}))}</span>`:"",w=p.total_amount!==null&&p.total_amount!==void 0?Number(p.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',g=[];(p.total_amount===null||p.total_amount===void 0)&&g.push(t("field-amount")),p.invoice_no||g.push(t("field-invoice-no")),p.invoice_date||g.push(t("field-invoice-date")),p.seller_name||g.push(t("field-seller-name")),g.length>0&&`${escapeHtml(p.id)}${escapeHtml(t("history-needs-review-tip")+" · "+g.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,p.edited&&`${escapeHtml(t("history-edited",{n:p.edit_count||1}))}`;const E=p.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",M=p.confidence==="high"?"high":p.confidence==="medium"?"mid":"low",$=p.confidence==="high"?t("conf-high"):p.confidence==="medium"?t("conf-medium"):t("conf-low"),j=`<span class="history-badge conf-${M}">${escapeHtml($)}</span>`;let _="";const A=p.source||"manual";return A==="email"?_=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:A==="folder"?_=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:A==="api"&&(_=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(p.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(p.id)}" ${_historySelected.has(p.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${B}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${h} ${S} ${C} ${_} ${E}</div>
                        <div class="history-cell-subtitle">${I}</div>
                    </div>
                    <div class="history-cell-amount">${w}</div>
                    <div class="history-cell-conf">${j}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(p.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),qt();const d=a.length>0?_historyState.page*_historyState.pageSize+1:0,l=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:d,to:l,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=Rt;window.renderHistoryList=Cn;window.updateHistoryBatchBar=qt;window.clearHistorySelection=so;typeof currentRoute<"u"&&currentRoute==="history"&&Rt();async function ct(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),ro(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),lo(a.id)}catch(n){console.error("open history detail failed",n)}}async function io(e){await ct(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function ro(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",po),document.getElementById("btn-push-erp").addEventListener("click",co)}async function lo(e){}async function co(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function po(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(d=>!d.is_duplicate&&!d.is_copy),s=o>=0?o:0,i=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function uo(e,n){document.querySelectorAll(".history-popover").forEach(p=>p.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(p=>p.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",i=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const d=()=>{r.remove(),document.removeEventListener("click",l,!0)},l=p=>{!r.contains(p.target)&&p.target!==n&&d()};setTimeout(()=>document.addEventListener("click",l,!0),0),r.addEventListener("click",async p=>{const m=p.target.closest("[data-act]");if(!m||m.disabled)return;const c=m.dataset.act;if(d(),c==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const f=document.createElement("textarea");f.value=s,f.style.position="fixed",f.style.opacity="0",document.body.appendChild(f),f.select(),document.execCommand("copy"),document.body.removeChild(f),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(c==="download-pdf"){const u=showToast(t("history-download-pdf-loading"),"loading",0);try{const f=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!f.ok)throw new Error("download failed");const b=await f.blob(),B=URL.createObjectURL(b),x=document.createElement("a");x.href=B,x.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(x),x.click(),document.body.removeChild(x),setTimeout(()=>URL.revokeObjectURL(B),5e3),u(),showToast(t("history-download-pdf-ok"),"success")}catch{u(),showToast(t("history-download-pdf-fail"),"error")}}else if(c==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const d=r.target.closest(".history-row"),l=r.target.closest("[data-hmenu]");if(l){r.stopPropagation(),uo(l.dataset.hmenu,l);return}const p=r.target.closest("[data-review]");if(p){r.stopPropagation(),ct(p.dataset.review);return}const m=r.target.closest("[data-fill-amount]");if(m){r.stopPropagation(),io(m.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||d&&!r.target.closest("[data-hmenu]")&&ct(d.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const d=r.target.closest(".history-row-check");if(!d)return;const l=d.dataset.hid;d.checked?_historySelected.add(l):_historySelected.delete(l),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const d=r.target.checked;for(const l of _historyState.items)d?_historySelected.add(l.id):_historySelected.delete(l.id);document.querySelectorAll(".history-row-check").forEach(l=>{l.checked=d}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const l=Array.from(_historySelected);try{const p=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:l})});if(!p.ok)throw new Error("batch delete failed");const m=await p.json();showToast(t("history-batch-done",{n:m.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(p){console.error("batch delete",p),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const d=r.target.value;document.getElementById("history-search-clear").style.display=d?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=d.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=ct;const Ve=document.getElementById("drop-zone"),Ft=document.getElementById("file-input");Ve.addEventListener("click",()=>Ft.click());Ft.addEventListener("change",e=>Sn(e.target.files));["dragover","dragenter"].forEach(e=>{Ve.addEventListener(e,n=>{n.preventDefault(),Ve.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{Ve.addEventListener(e,n=>{n.preventDefault(),Ve.classList.remove("drag-over")})});Ve.addEventListener("drop",e=>{e.preventDefault(),Sn(e.dataTransfer.files)});const fo=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function Tt(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function mo(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function vo(e){return mo(e)||Tt(e)||fo.test(e.name)}function Sn(e){hideAlerts();const n=Array.from(e),a=n.filter(vo);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(d=>!Tt(d)),s=a.filter(Tt),i=new Set(_selectedFiles.map(d=>d.name+"_"+d.size));for(const d of o){const l=d.name+"_"+d.size;i.has(l)||(_selectedFiles.push({file:d,name:d.name,size:d.size,status:"waiting",errorKey:null,errorParams:null}),i.add(l))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(d){console.error("[upload] image route failed",d)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),wt(),zt(),Ft.value=""}let st=!1;function wt(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(c=>c.status==="processing"||c.status==="retrying").length,o=_selectedFiles.filter(c=>c.status==="success").length,s=_selectedFiles.filter(c=>c.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const d=st?t("file-list-collapse"):t("file-list-expand"),l=_selectedFiles.map((c,u)=>{let f=t("status-"+c.status);c.status==="retrying"&&(f=t("status-retrying")),c.status==="error"&&c.errorKey&&(f=t(c.errorKey,c.errorParams||{}));const b=c.status==="processing"||c.status==="retrying"?'<span class="spinner"></span>':"",B=c.status==="error"&&c.canRetry?`<button class="file-retry-btn" data-retry-idx="${u}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",x=c.status==="success"&&c.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</span>
                ${x}
                <span class="file-status ${c.status}">${b}${f}</span>
                ${B}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(d)}</button>`:""}
        </div>
        <ul class="file-list-body${st?" expanded":""}" id="file-list-body">
            ${l}
        </ul>
    `;const p=document.getElementById("file-list-toggle");p&&p.addEventListener("click",()=>{st=!st,wt()});const m=document.getElementById("file-list-body");m&&!m.dataset.retryBound&&(m.dataset.retryBound="1",m.addEventListener("click",async c=>{const u=c.target.closest(".file-retry-btn");if(!u)return;const f=parseInt(u.dataset.retryIdx||"-1",10);if(f<0||f>=_selectedFiles.length)return;const b=_selectedFiles[f];!b||b.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(b,!0)}))}function zt(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],wt(),renderResults(),zt(),hideAlerts()});window.renderFileList=wt;window.updateStartButton=zt;const ho=`
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
`;we("camera-tips-modal",ho);(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await bo()||o.click()}),o.addEventListener("change",async d=>{const l=Array.from(d.target.files||[]);if(d.target.value="",l.length!==0)for(const p of l)await Mt([p],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=d=>async l=>{const p=Array.from(l.target.files||[]);if(l.target.value="",p.length===0)return;const m=p.filter(u=>u.type==="application/pdf"||/\.pdf$/i.test(u.name)),c=p.filter(u=>!m.includes(u));m.length>0&&await go(m),c.length>0&&await Mt(c,d)};a&&a.addEventListener("change",r("gallery"))})();async function go(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function bo(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const i=d=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(d)},r=d=>{d.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),o&&(o.onclick=()=>i(!1)),n.onclick=d=>{d.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}async function dt(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],i=o.naturalWidth,r=o.naturalHeight;(i<1e3||r<1e3)&&s.push("low_res");try{const d=document.createElement("canvas");d.width=64,d.height=64;const l=d.getContext("2d");l.drawImage(o,0,0,64,64);const p=l.getImageData(0,0,64,64).data;let m=0,c=0;for(let f=0;f<p.length;f+=4)m+=.299*p[f]+.587*p[f+1]+.114*p[f+2],c++;const u=c?m/c:128;u<70?s.push("too_dark"):u>235&&s.push("too_bright"),n({warnings:s,width:i,height:r,brightness:u})}catch{n({warnings:s,width:i,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}let Ce=[],Pe=null;async function Mt(e,n){if(hideAlerts(),!(!e||e.length===0)){var a=typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice";if(a==="thai_id_card"){for(const s of e)_selectedFiles.push({file:s,name:s.name,size:s.size,status:"waiting",errorKey:null,errorParams:null});const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton();return}if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let o=0;o<30&&(await new Promise(s=>setTimeout(s,100)),!(window.jspdf&&window.jspdf.jsPDF));o++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const o=e[0];let s={};try{s=await dt(o)}catch{}Ce.push({file:o,quality:s}),Pe="camera",ze();return}if(n==="gallery"&&(e.length>=2||Ce.length>0)){for(const o of e){let s={};try{s=await dt(o)}catch{}Ce.push({file:o,quality:s})}Pe="gallery",ze();return}await Tn(e)}}async function yo(e){const n=new Set;for(const o of e)try{((await dt(o)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const o=await Mn(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function ze(){let e=document.getElementById("camera-buffer-bar");if(Ce.length===0){e&&e.remove(),Pe=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=Ce.length,a=n>=2,o=Pe==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?o?i=`
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
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{Ce=[],Pe=null,ze()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const l=o?"gallery-input":"camera-input",p=document.getElementById(l);p&&p.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const l=Ce.map(p=>p.file);Ce=[],Pe=null,ze(),await yo(l)});const d=e.querySelector('[data-cbb-action="separate"]');d&&(d.onclick=async()=>{const l=Ce.map(p=>p.file);Ce=[],Pe=null,ze(),await Tn(l)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{Ce.length>0&&ze()});async function Tn(e){const n=new Set;let a=0;for(const s of e)try{((await dt(s)).warnings||[]).forEach(d=>n.add(d));const r=await Mn([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}async function Mn(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let p=0;p<e.length;p++){const m=e[p],{dataUrl:c,naturalW:u,naturalH:f}=await wo(m);p>0&&s.addPage("a4","p");const b=u/f;let B=a-10,x=B/b;x>o-10&&(x=o-10,B=x*b);const v=(a-B)/2,h=(o-x)/2,L=m.type==="image/png"?"PNG":"JPEG";s.addImage(c,L,v,h,B,x,void 0,"FAST")}const i=s.output("blob"),r=new Date,d=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),l=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${d}${l}.pdf`,{type:"application/pdf"})}function wo(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}window.handleCameraImages=Mt;(function(){var e="pearnly_ocr_doc_mode",n=!1,a=!1;function o(u){return typeof escapeHtml=="function"?escapeHtml(u==null?"":String(u)):String(u??"")}function s(){try{return localStorage.getItem(e)==="thai_id_card"?"thai_id_card":"invoice"}catch{return"invoice"}}window.getOcrDocumentMode=function(){return n?s():"invoice"};function i(){var u=document.getElementById("drop-zone");return u?u.closest(".card"):null}function r(){var u=i();if(!u)return null;var f=u.querySelector("#ocr-doc-mode");if(f)return f;var b=u.querySelector(".section-head");return f=document.createElement("div"),f.id="ocr-doc-mode",f.className="ocr-doc-mode",f.setAttribute("role","tablist"),f.style.cssText="display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;",b&&b.parentNode?b.parentNode.insertBefore(f,b.nextSibling):u.insertBefore(f,u.firstChild),f}function d(u,f,b){return'<button type="button" class="ocr-doc-seg'+(b?" active":"")+'" data-doc-mode="'+u+'" role="tab" aria-selected="'+(b?"true":"false")+'" style="border:none;background:'+(b?"var(--card,#fff)":"transparent")+";color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:"+(b?"600":"500")+";padding:6px 16px;border-radius:7px;cursor:pointer;box-shadow:"+(b?"0 1px 3px rgba(0,0,0,.08)":"none")+';transition:background .15s;">'+o(t(f))+"</button>"}function l(){var u=r();if(u){if(!n){u.style.display="none";return}var f=s();u.style.display="flex",u.innerHTML=d("invoice","ocr-mode-invoice",f==="invoice")+d("thai_id_card","ocr-mode-id-card",f==="thai_id_card")}}function p(u){try{localStorage.setItem(e,u==="thai_id_card"?"thai_id_card":"invoice")}catch{}l();try{document.dispatchEvent(new CustomEvent("ocr-doc-mode-change",{detail:{mode:window.getOcrDocumentMode()}}))}catch{}}async function m(u){if(!(a&&!u)){var f=localStorage.getItem("mrpilot_token");if(f)try{var b=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+f}});if(!b.ok)return;var B=await b.json(),x=B&&B.items||[];n=x.some(function(v){return v&&(v.adapter||"").toLowerCase()==="mrerp_dms"&&v.enabled!==!1}),a=!0,window._dmsHasEndpoint=n,l()}catch{}}}window._refreshOcrDocMode=function(){m(!0)},document.addEventListener("click",function(u){var f=u.target.closest(".ocr-doc-seg");f&&f.getAttribute("data-doc-mode")&&(u.preventDefault(),p(f.getAttribute("data-doc-mode")))}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("ocr-doc-mode",l);function c(){r(),l(),m(!1)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),window.addEventListener("hashchange",function(){((location.hash||"").indexOf("ocr")>=0||location.hash===""||location.hash==="#home")&&setTimeout(function(){r(),m(!1)},60)})})();(function(){function e(i){return typeof escapeHtml=="function"?escapeHtml(i==null?"":String(i)):String(i??"")}function n(){var i=(function(){var d=document.getElementById("drop-zone");return d?d.closest(".card"):null})();if(!i||!i.parentNode)return null;var r=document.getElementById("dms-id-card-result");return r||(r=document.createElement("div"),r.id="dms-id-card-result",r.className="card",r.style.cssText="display:none;margin-top:16px;",i.parentNode.insertBefore(r,i.nextSibling),r)}function a(i,r){return'<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);"><span style="color:var(--muted,#6b6b66);font-size:13px;">'+e(t(i))+'</span><span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">'+e(r||"—")+"</span></div>"}function o(i){if(!i)return"";var r=[i.house_no,i.road,i.subdistrict,i.district,i.province,i.zipcode].filter(function(d){return d});return r.join(" ")||i.address_raw||""}function s(i){var r=i&&i.status||"failed",d,l,p;return r==="success"?(d="#0a7a2c",l="#d6f5e0",p="dms-result-status-success"):r==="needs_review"?(d="#9a6b00",l="#fdf0d0",p="dms-result-status-needs-review"):r==="skipped"?(d="#5d5d57",l="#eee",p="dms-result-status-skipped"):(d="#b3261e",l="#fbe0de",p="dms-result-status-failed"),'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:'+d+";background:"+l+';">'+e(t(p))+"</span>"}window.renderDmsIdCardResult=function(i){var r=n();if(r){i=i||{};var d=i.id_card||{},l=d.address||{},p=i.dms_push||{},m=p.status||(i.ok?"success":"failed"),c="";m==="success"&&(c=a("dms-result-customer",p.customer_id)+a("dms-result-booking",p.booking_no));var u=m==="failed"||m==="needs_review"?'<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">'+e(t("dms-result-retry"))+"</button>":"",f="";if(m==="failed"&&p.error_code){var b="dms-err-"+String(p.error_code).toLowerCase(),B=t(b);(!B||B===b)&&(B=t("dms-err-err_dms_unexpected")),f='<div style="margin-top:8px;color:#b3261e;font-size:12px;">'+e(B)+"</div>"}r.style.display="",r.innerHTML='<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;"><div class="section-title">'+e(t("dms-result-title"))+"</div>"+s(p)+'</div><div style="margin-top:8px;">'+a("dms-result-name",(d.first_name||"")+" "+(d.last_name||""))+a("dms-result-id",d.people_id_masked)+a("dms-result-birthday",d.birthday_be)+a("dms-result-address",o(l))+c+"</div>"+f+u}},window.clearDmsIdCardResult=function(){var i=document.getElementById("dms-id-card-result");i&&(i.style.display="none",i.innerHTML="")},document.addEventListener("click",function(i){i.target.closest("#dms-id-card-retry")&&(i.preventDefault(),typeof window._dmsRetryIdCard=="function"&&window._dmsRetryIdCard())})})();document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,(typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice")==="thai_id_card"){try{await $n()}finally{const c=document.getElementById("btn-start");c&&(c.disabled=!1)}return}if(_userInfo&&_userInfo.plan==="free"){const c=await fetch("/api/health").then(u=>u.json()).catch(()=>null);c&&!c.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const n=_selectedFiles.filter(c=>c.status==="waiting"),a=6;async function o(c,u){if(window._ocrAborted)return c.status="cancelled",c.errorKey=null,renderFileList(),{};c.status=u?"retrying":"processing",c.canRetry=!1,renderFileList();const f=new AbortController,b=setTimeout(()=>f.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(f);try{const B=new FormData;B.append("file",c.file,c.name);try{if(typeof window.getCurrentClientId=="function"){const I=window.getCurrentClientId();I!=null&&B.append("client_id",String(I))}}catch{}const x=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:B,signal:f.signal});if(clearTimeout(b),window._ocrCtrls.delete(f),x.status===401||x.status===403){const S=await x.clone().json().catch(()=>({})),C=S&&S.detail,w=typeof C=="string"?C:C&&C.code||"";if(!w||w.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),w==="auth.session_revoked")_showSessionRevokedModal();else{const g=w==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(g),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}w==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!x.ok){const S=(await x.json().catch(()=>({}))).detail;return typeof S=="string"?(c.errorKey="err."+S,c.errorParams=null):S&&S.code?(c.errorKey="err."+S.code,c.errorParams={...S,mb:_quota.max_file_size_mb}):(c.errorKey="err.unknown",c.errorParams=null),(c.errorKey==="err.unknown"||c.errorKey==="err.ocr.engine_error")&&(x.status===429?c.errorKey="err.rate_limit":x.status===502||x.status===503||x.status===504?c.errorKey="err.gemini_overloaded":x.status>=500&&(c.errorKey="err.server")),c.status="error",c.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(c.errorKey||""),renderFileList(),{}}const v=await x.json();c.status="success",c.fromCache=!!v.from_cache;const h=mergeFields(v.pages),L=v.confidence||(h.items&&h.items.length>0?"high":"low");if(_results.push({filename:v.filename,pages:v.pages,page_count:v.page_count,elapsed_ms:v.elapsed_ms,engine:v.engine,merged_fields:h,edits:{},confidence:L,history_id:v.history_id,history_ids:v.history_ids||[],invoice_count:v.invoice_count||1,invoices:v.invoices||[],archive_name:v.archive_name||null,category_tag:v.category_tag||null,auto_pushed:!!v.auto_pushed,typhoon_enhanced:!!v.typhoon_enhanced,typhoon_pages:v.typhoon_pages||[],from_cache:!!v.from_cache}),v.invoice_count&&v.invoice_count>1&&showToast(t("multi-invoice-toast",{file:v.filename,n:v.invoice_count}),"success"),v.missed_invoice_warnings&&v.missed_invoice_warnings.length){const I=v.missed_invoice_warnings.map(function(S){return S.page}).filter(function(S){return S!=null});showToast(t("missed-invoice-warn",{file:v.filename,pages:I.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",v.missed_invoice_warnings)}if(v.typhoon_enhanced&&v.typhoon_pages&&v.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:v.filename,n:v.typhoon_pages.length}),"success"),v.fallback_used){const I=v.engine_chain||[],S=v.engine||"";let C;S==="typhoon_nvidia"?C="fallback-typhoon-nvidia-toast":S==="easyocr"?C="fallback-easyocr-toast":C="fallback-generic-toast",showToast(t(C,{file:v.filename}),"warn"),console.info("[OCR Chain]",I)}if(v.from_cache&&showToast(t("cache-hit-toast",{file:v.filename}),"info"),v.duplicate_warnings&&v.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const I of v.duplicate_warnings)window._dupQueue.push({filename:v.filename,...I})}return v.auto_pushed&&showToast(t("auto-push-fired",{file:v.filename}),"info"),v.quota&&v.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=v.quota.used_this_month,_userInfo.tenant_used=v.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(B){clearTimeout(b);try{window._ocrCtrls&&window._ocrCtrls.delete(f)}catch{}console.error("[Upload] failed for",c.file.name,B);const x=B&&(B.name==="AbortError"||B==="timeout"),v=x&&(f.signal.reason==="timeout"||B==="timeout"),h=B&&B.message&&/NetworkError|Failed to fetch/i.test(B.message);return x&&(f.signal.reason==="user_stop"||window._ocrAborted)?(c.status="cancelled",c.errorKey=null,c.canRetry=!1,renderFileList(),{}):(v?c.errorKey="err.timeout":x?c.errorKey="err.aborted":h?c.errorKey="err.network":(c.errorKey="err.unknown",c.errorParams={msg:B&&B.message?B.message:String(B)}),c.status="error",!u&&!window._ocrAborted&&(h||v)&&navigator.onLine!==!1&&(c.canRetry=!0,renderFileList(),await new Promise(I=>setTimeout(I,2e3)),c.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?o(c,!0):(c.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=o;let s=0,i=!1;async function r(){for(;s<n.length&&!i&&!window._ocrAborted;){const c=s++,u=await o(n[c]);if(u&&u.abort){i=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const d=document.getElementById("btn-start"),l=document.getElementById("btn-stop");d&&(d.style.display="none"),l&&(l.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(n)}catch{}const p=[];for(let c=0;c<Math.min(a,n.length);c++)p.push(r());await Promise.all(p);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}d&&(d.style.display=""),l&&(l.style.display="none");const m=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const c={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const f of n)if(f.status==="success")c.success++;else if(f.status==="cancelled")c.cancelled++;else if(f.status==="error"){const b=f.errorKey||"";b==="err.network"?c.network++:b==="err.timeout"||b==="err.aborted"?c.timeout++:b.indexOf("quota")>=0||b==="err.monthly_limit_exceeded"?c.quota++:b==="err.gemini_overloaded"||b==="err.server"?c.overloaded++:b==="err.rate_limit"?c.rate++:c.other++}const u=n.length;m?showToast(ko(c,u),"warn",4e3):u>1&&c.network+c.timeout+c.quota+c.overloaded+c.rate+c.other>0&&showToast(xo(c),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function ko(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function xo(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});async function $n(e){let n;if(e)n=_selectedFiles.find(a=>a.file===e)||{file:e,name:e.name,status:"waiting"};else{const a=_selectedFiles.filter(o=>o.status==="waiting");if(!a.length)return;n=a[0]}window._dmsLastFile=n.file,n.status="processing",typeof renderFileList=="function"&&renderFileList();try{const a=new FormData;a.append("file",n.file,n.name),a.append("push","true");const o=await fetch("/api/dms/id-card-booking",{method:"POST",headers:{Authorization:"Bearer "+token},body:a});if(o.status===401||o.status===403){const i=await o.clone().json().catch(()=>({})),r=i&&i.detail,d=typeof r=="string"?r:r&&r.code||"";if(!d||d.startsWith("auth.")){localStorage.removeItem("mrpilot_token"),showToast(t("alert-session"),"error"),setTimeout(()=>{window.location.href="/"},1200);return}}const s=await o.json().catch(()=>({}));if(!o.ok){n.status="error";const i=s&&s.detail&&(s.detail.code||s.detail)||"unknown";n.errorKey="err."+i,n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:String(i)}});return}n.status=s.ok||s.dms_push&&s.dms_push.status==="needs_review"?"success":"error",typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult(s),typeof updateStartButton=="function"&&updateStartButton()}catch{n.status="error",n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:"network"}})}}window._dmsRetryIdCard=function(){window._dmsLastFile&&$n(window._dmsLastFile)};function Hn(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=f=>f!=null?Number(f).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",d=f=>f||"—",l=f=>{try{const b=new Date(f);return`${b.getFullYear()}-${String(b.getMonth()+1).padStart(2,"0")}-${String(b.getDate()).padStart(2,"0")}`}catch{return f}},p=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",m=(e.matched_fields||[]).map(f=>{const b=t("dup-field-"+f.replace("_","-"))||f;return`<span class="dup-field-chip">${escapeHtml(b)}</span>`}).join(" "),c=document.createElement("div");c.className="log-detail-modal",c.innerHTML=`
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
                <div class="dup-matched-label">${escapeHtml(t("dup-matched-on"))} ${m}</div>
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
    `,document.body.appendChild(c);const u=()=>{c.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(Hn,200)};c.querySelector(".dup-close").addEventListener("click",u),c.querySelector('[data-action="view"]').addEventListener("click",()=>{const f=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(f)},400),u()}),c.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const f=e.new_history_id;if(!f){u();return}try{(await fetch(`/api/history/${encodeURIComponent(f)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}u()}),c.querySelector('[data-action="keep"]').addEventListener("click",u)}window.showDuplicateDialog=Hn;function qe(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function Je(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function _o(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?qe("time-just-now","刚刚"):a<3600?Math.floor(a/60)+qe("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+qe("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+qe("time-day-ago-suffix"," 天前")}catch{return""}}async function Nt(){An();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const d={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[l,p,m]=await Promise.all([fetch("/api/me/tenant-usage",{headers:d}).then(x=>x.ok?x.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:d}).then(x=>x.ok?x.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:d}).then(x=>x.ok?x.json():null).catch(()=>null)]),c=l&&l.ocr_this_month||0;let u=0;const f=p&&(p.items||p.history||p)||[],b=Array.isArray(f)?f:[];b.forEach(x=>{(x.status==="pending"||x.status==="reviewing")&&u++});const B=m&&(m.total||m.count||m.pending||0)||0;if(e&&(e.textContent=Je(c)),n&&(n.textContent=Je(u)),a&&(a.textContent=Je(B)),r&&(B>0?(r.style.display="",r.textContent=B):r.style.display="none"),o&&l){const x=l.ocr_this_month||0,v=l.quota||0;o.textContent=Je(x),s&&(s.textContent=v?x+" / "+Je(v)+" 张":qe("dash-kpi-plan-sub","本月用量"))}if(i)if(b.length===0)i.innerHTML='<div class="dash-recent-empty">'+qe("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const x=b.slice(0,5).map(v=>{const h=(v.invoice_no||v.filename||v.id||"").toString(),L=(v.supplier_name||v.buyer_name||v.client_name||v.notes||"").toString(),I=_o(v.created_at||v.upload_time||v.date),S=C=>String(C).replace(/[&<>"']/g,w=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[w]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+S(h)+'">'+S(h)+'</span><span class="dash-recent-mid" title="'+S(L)+'">'+S(L)+'</span><span class="dash-recent-time">'+S(I)+"</span></div>"}).join("");i.innerHTML=x}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+qe("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Nt;async function An(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},d=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!d.ok){e.style.display="none",s&&(s.textContent="—"),i&&(i.textContent="");return}const l=await d.json(),p=!!l.is_owner,m=!!l.is_billing_exempt;if(!p)e.style.display="none";else if(e.style.display="",m)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const u=typeof l.balance_thb=="number"?l.balance_thb:0;if(a&&(a.textContent="฿"+u.toFixed(2),a.className=u<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const f=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",b=u<50?"#dc2626":"#6b7280",B=x=>typeof window.escapeHtml=="function"?window.escapeHtml(x):String(x).replace(/[&<>"']/g,v=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[v]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+b+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+B(f)+"</a>"}}const c=typeof l.pages_this_month=="number"?l.pages_this_month:typeof l.my_invoice_count=="number"?l.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(c)),i){const u=c>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",f=typeof window.t=="function"?window.t(u,{used:c}):c+" pages";i.textContent=f}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=An;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Nt,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Nt()});function ue(e){return(typeof window.t=="function"?window.t(e):null)||e}function Ot(){return localStorage.getItem("mrpilot_token")||""}function pe(e){return document.getElementById(e)}var rt=null,Xe=null;function jn(){Xe||(Xe=setInterval(function(){if(!document.hidden){var e=Ot();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;rt!==null&&a>rt&&(window.showToast&&window.showToast(ue("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),rt=a}}).catch(function(){}))}},3e4))}function Eo(){Xe&&(clearInterval(Xe),Xe=null),rt=null}window._startCreditsPoll=jn;window._stopCreditsPoll=Eo;jn();var Vt=null,Ut=0;function Bo(){if(!pe("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),Io()}}function Pn(){var e=function(n,a){var o=pe(n);o&&(o.textContent=a)};e("tv2-title",ue("topup-title")),e("tv2-sl1",ue("topup-step1")),e("tv2-sl2",ue("topup-step2")),e("tv2-sl3",ue("topup-step3")),e("tv2-al",ue("topup-amount-label")),e("tv2-bl",ue("topup-bank-label")),e("tv2-copy",ue("topup-copy-account")),e("tv2-dt",ue("topup-slip-drop")),e("tv2-pl",ue("topup-payer-label")),e("tv2-nl",ue("topup-note-label"))}function nt(e){[1,2,3].forEach(function(s){var i=pe("tv2-s"+s);i&&(i.style.display=s===e?"":"none");var r=pe("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=pe("tv2-back"),a=pe("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=ue("topup-btn-cancel")):n&&(n.style.display="",n.textContent=ue("topup-btn-back")),a&&(a.textContent=ue(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=pe("tv2-bn");o&&(o.innerHTML=ue("topup-bank-note").replace("{amount}","<strong>฿"+Number(Ut).toLocaleString()+"</strong>"))}}function $t(){for(var e=1;e<=3;e++){var n=pe("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function pt(e){var n=pe(e);n&&(n.textContent="",n.style.display="none")}function Ze(e,n){var a=pe(e);a&&(a.textContent=n,a.style.display="")}function tn(e){var n=pe("tv2-dt");n&&(n.textContent=e.name);var a=pe("tv2-drop");a&&a.classList.add("has-file"),pt("tv2-se")}function Io(){var e=pe("topup-v2-ov");pe("tv2-close").addEventListener("click",Ye),e.addEventListener("click",function(i){i.target===e&&Ye()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&Ye()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(l){l.classList.remove("active")}),r.classList.add("active");var d=pe("tv2-amt");d&&(d.value=r.dataset.val,pt("tv2-ae"))}});var n=pe("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),pt("tv2-ae")});var a=pe("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=ue("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var o=pe("tv2-drop"),s=pe("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(i){i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(i){i.preventDefault(),o.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&tn(r)})),s&&s.addEventListener("change",function(){s.files[0]&&tn(s.files[0])}),pe("tv2-back").addEventListener("click",function(){var i=$t();if(i<=1){Ye();return}nt(i-1)}),pe("tv2-next").addEventListener("click",function(){var i=$t();i===1?Lo():i===2?nt(3):Co()})}async function Lo(){var e=pe("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){Ze("tv2-ae",ue("topup-amount-invalid"));return}if(n>5e5){Ze("tv2-ae",ue("topup-amount-too-large"));return}Ut=n;var a=pe("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+Ot()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),i=ue("topup-submit-fail");try{var r=JSON.parse(s),d=r.detail;if(Array.isArray(d)&&d.length){var l=d[0]&&d[0].type||"";l.indexOf("less_than")>=0?i=ue("topup-amount-too-large"):(l.indexOf("greater_than")>=0||l.indexOf("parsing")>=0)&&(i=ue("topup-amount-invalid"))}else typeof d=="string"&&(i=d)}catch{}throw new Error(i)}var p=await o.json();Vt=p.request_id,nt(2)}catch(m){Ze("tv2-ae",m.message||ue("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=ue("topup-btn-next"))}}async function Co(){var e=pe("tv2-file");if(!e||!e.files||!e.files[0]){Ze("tv2-se",ue("topup-slip-required"));return}var n=pe("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=pe("tv2-payer"),s=pe("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+Vt,{method:"POST",headers:{Authorization:"Bearer "+Ot()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(ue("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(ue("topup-pending"),"info"),Ye()}catch(d){Ze("tv2-ue",ue("topup-upload-fail")+" · "+d.message),n&&(n.disabled=!1,n.textContent=ue("topup-btn-submit"))}}function Ye(){var e=pe("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){Bo(),Vt=null,Ut=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=pe(a);o&&(o.value="")});var e=pe("tv2-file");e&&(e.value="");var n=pe("tv2-drop");n&&n.classList.remove("has-file","drag-over"),pe("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){pt(a)}),Pn(),nt(1),pe("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=pe("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(Pn(),nt($t()))});const So=`
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

    `;we("page-test-center",So);(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",i=!1,r=!1;function d(F,D,V){let Y=typeof t=="function"?t(F):null;return(!Y||Y===F)&&(Y=D),V&&Object.keys(V).forEach(function(T){Y=String(Y).replace("{"+T+"}",String(V[T]))}),Y}function l(){try{const F=localStorage.getItem(n);o=F?JSON.parse(F):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function p(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function m(F){const D=new Date(F),V=function(Y){return Y<10?"0"+Y:""+Y};return V(D.getHours())+":"+V(D.getMinutes())+":"+V(D.getSeconds())}function c(F){return String(F??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function u(F,D){try{typeof showToast=="function"?showToast(F,D||"info"):alert(F)}catch{}}function f(F){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(F).then(function(){u(d("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){b(F)}):b(F)}catch{b(F)}}function b(F){try{const D=document.createElement("textarea");D.value=F,D.style.position="fixed",D.style.opacity="0",document.body.appendChild(D),D.select();const V=document.execCommand("copy");document.body.removeChild(D),u(V?d("tc-toast-copied","已复制"):d("tc-toast-copy-fail","复制失败"),V?"success":"error")}catch{u(d("tc-toast-copy-fail","复制失败"),"error")}}function B(){const F=document.getElementById("tc-account-chip"),D=document.getElementById("tc-progress-chip");if(F&&(F.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),D){const V=a.length,Y=a.filter(function(T){return o[T.id]}).length;D.textContent=Y+" / "+V}}function x(){const F=document.getElementById("tc-checklist-body");if(!F)return;const D={};a.forEach(function(Y){D[Y.group]||(D[Y.group]=[]),D[Y.group].push(Y)});const V=[];Object.keys(D).forEach(function(Y){V.push('<div class="tc-checklist-group">'),V.push('<div class="tc-checklist-group-title">'+c(Y)+"</div>"),D[Y].forEach(function(T){const k=o[T.id]||"",y=k?"is-"+k:"";V.push('<div class="tc-check-item '+y+'" data-id="'+c(T.id)+'"><div class="tc-check-id">'+c(T.id)+'</div><div class="tc-check-desc">'+c(T.desc)+'</div><div class="tc-check-actions">'+v(T.id,"pass",k)+v(T.id,"fail",k)+v(T.id,"skip",k)+"</div></div>")}),V.push("</div>")}),F.innerHTML=V.join("")}function v(F,D,V){const Y=V===D,T={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},k={pass:d("tc-status-pass","通过"),fail:d("tc-status-fail","失败"),skip:d("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(Y?"is-active "+D:"")+'" data-id="'+c(F)+'" data-kind="'+D+'" title="'+c(k[D])+'">'+T[D]+"</button>"}function h(F){return s==="all"?!0:s==="js_error"?F.type==="js_error"||F.type==="promise_error":s==="api"?F.type==="api_error"||F.type==="api_fail":s==="api_slow"?F.type==="api_slow":s==="console"?F.type==="console_error"||F.type==="console_warn":!0}function L(){const F=document.getElementById("tc-logs-body"),D=document.getElementById("tc-logs-count");if(!F)return;const V=(window._pearnlyTcLogs||[]).slice().reverse(),Y=V.filter(h);if(D&&(D.textContent=String(V.length)),Y.length===0){F.innerHTML='<div class="tc-logs-empty">'+c(d("tc-logs-empty","暂无异常"))+"</div>";return}const T=Y.slice(0,100).map(function(k){const y=typeof k.detail=="object"?JSON.stringify(k.detail,null,2):String(k.detail||"");return'<div class="tc-log-item t-'+c(k.type)+'" data-ts="'+k.ts+'"><span class="tc-log-time">'+m(k.ts)+'</span><span class="tc-log-type">'+c(k.type)+'</span><div class="tc-log-summary">'+c(k.summary)+'<div class="tc-log-detail">'+c(y)+"</div></div></div>"}).join("");F.innerHTML=T,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(k){k.classList.toggle("active",k.getAttribute("data-filter")===s)})}function I(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&L(),S()},200))}window._tcOnNewLog=I;function S(){const F=document.getElementById("nav-test-badge");if(!F)return;const D=(window._pearnlyTcLogs||[]).filter(function(V){return V.type==="js_error"||V.type==="promise_error"||V.type==="api_error"||V.type==="api_fail"||V.type==="console_error"}).length;D>0?(F.style.display="",F.textContent=D>99?"99+":String(D)):F.style.display="none"}function C(){B(),x(),L(),S()}function w(){const F=[],D=new Date,V=_userInfo&&(_userInfo.email||_userInfo.username)||"—";F.push("# Pearnly "+e+" 测试结果"),F.push("- 账号:"+V),F.push("- 时间:"+D.toISOString().replace("T"," ").slice(0,19));const Y=a.length,T=a.filter(function(G){return o[G.id]==="pass"}).length,k=a.filter(function(G){return o[G.id]==="fail"}).length,y=a.filter(function(G){return o[G.id]==="skip"}).length,H=Y-T-k-y;F.push("- 进度:"+(T+k+y)+" / "+Y+" · ✅ "+T+" · ❌ "+k+" · ⏭ "+y+" · 未测 "+H),F.push(""),F.push("| ID | 描述 | 状态 |"),F.push("|---|---|---|"),a.forEach(function(G){const Q=o[G.id],te=Q==="pass"?"✅":Q==="fail"?"❌":Q==="skip"?"⏭":"⬜";F.push("| "+G.id+" | "+G.desc.replace(/\|/g,"\\|")+" | "+te+" |")});const P=a.filter(function(G){return o[G.id]==="fail"});P.length>0&&(F.push(""),F.push("## ❌ 失败项"),P.forEach(function(G){F.push("- **"+G.id+"** · "+G.desc)}));const z=(window._pearnlyTcLogs||[]).slice(-30).reverse();return z.length>0&&(F.push(""),F.push("## 🔴 异常日志(最近 "+z.length+" 条)"),z.forEach(function(G){if(F.push("- `"+m(G.ts)+"` · **"+G.type+"** · "+G.summary),G.detail){let Q;try{Q=JSON.stringify(G.detail)}catch{Q=String(G.detail)}Q&&Q!=="{}"&&F.push("  - "+Q.slice(0,600))}})),F.join(`
`)}function g(F){const D=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(D.length===0)return"(暂无异常日志)";const V=["# Pearnly 异常日志(最近 "+D.length+" 条)"],Y=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return V.push("- 账号:"+Y),V.push("- 当前页:"+(currentRoute||"?")),V.push("- UA:"+navigator.userAgent),V.push(""),D.forEach(function(T){if(V.push("## `"+m(T.ts)+"` · "+T.type),V.push("- "+T.summary),T.detail){V.push("```");try{V.push(JSON.stringify(T.detail,null,2).slice(0,2e3))}catch{V.push(String(T.detail).slice(0,2e3))}V.push("```")}}),V.join(`
`)}function E(){const F=Date.now();fetch("/api/health").then(function(D){const V=Date.now()-F;D.ok?u(d("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:V}),"success"):u(d("tc-toast-health-fail","后端无响应")+" ("+D.status+")","error")}).catch(function(){u(d("tc-toast-health-fail","后端无响应"),"error")})}function M(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}C(),u(d("tc-toast-cleared","session 状态已清空"),"success")}function $(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(F){return F.json()}).then(function(F){window._clientsCache=F.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),u("客户缓存已刷新 · "+(F.clients||[]).length+" 个客户","success")}).catch(function(){u("刷新失败","error")})}catch{}}function j(){if(i||!document.getElementById("page-test-center"))return;i=!0;const D=document.getElementById("tc-checklist-body");D&&D.addEventListener("click",function(Q){const te=Q.target.closest(".tc-status-btn");if(!te)return;const R=te.getAttribute("data-id"),U=te.getAttribute("data-kind");!R||!U||(o[R]===U?delete o[R]:o[R]=U,p(),x(),B())});const V=document.getElementById("tc-btn-reset-checklist");V&&V.addEventListener("click",function(){o={},p(),x(),B()});const Y=document.getElementById("tc-btn-copy-all");Y&&Y.addEventListener("click",function(){f(w())});const T=document.getElementById("tc-btn-copy-logs");T&&T.addEventListener("click",function(){f(g())});const k=document.getElementById("tc-btn-clear-logs");k&&k.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,L(),S()});const y=document.getElementById("tc-logs-filter");y&&y.addEventListener("click",function(Q){const te=Q.target.closest(".tc-filter-chip");te&&(s=te.getAttribute("data-filter")||"all",L())});const H=document.getElementById("tc-logs-body");H&&H.addEventListener("click",function(Q){const te=Q.target.closest(".tc-log-item");te&&te.classList.toggle("expanded")});const P=document.getElementById("tc-tool-health");P&&P.addEventListener("click",E);const z=document.getElementById("tc-tool-clear-session");z&&z.addEventListener("click",M);const G=document.getElementById("tc-tool-reload-clients");G&&G.addEventListener("click",$)}function _(){}window._tcApplyVisibility=_;let A=0;const q=setInterval(function(){A++,_userInfo&&clearInterval(q),A>60&&clearInterval(q)},500);window.loadTestCenterPage=function(){l(),j(),C()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){S(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&C()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(h,L){if(typeof window.t=="function"){const I=window.t(h);if(I&&I!==h)return I}return L}function o(){const h=window._userInfo||{},L=String(h.role||"").toLowerCase(),I=String(h.tenant_role||"").toLowerCase();return h.is_super_admin===!0||h.is_owner===!0||L==="owner"||L==="admin"||I==="owner"||I==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const h=localStorage.getItem(e);if(!h||h==="null"||h==="0"||h==="")return null;const L=parseInt(h,10);return isNaN(L)?null:L}function r(h){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:h,mode:s()}}))}catch{}}function d(h){const L=i();h==null||h===0?localStorage.removeItem(e):(localStorage.setItem(e,String(h)),localStorage.setItem(n,"client")),String(L)!==String(h)&&r(h)}function l(){const h=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),h!=null&&r(null)}async function p(){try{const h=window.apiGet;if(typeof h!="function")return[];const L=await h("/api/workspace/clients");return L&&(L.clients||L.items)||[]}catch{return[]}}async function m(h){if(s()==="client"&&i()!=null)return typeof h=="function"&&h(),!0;const L=a("ws-need-client","这个功能需要先选择工作空间"),I=a("ws-btn-pick","选择工作空间"),S=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(L,{okText:I,cancelText:S})&&c(h):window.confirm(L+`

[`+I+" / "+S+"]")&&c(h),!1}async function c(h){const L=await p();if(typeof h=="function"&&s()!=="personal"&&L.length===1){d(Number(L[0].id)),h();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:L,canCreate:o(),active:i(),onPersonal:l,onPick:function(I){d(Number(I)),typeof h=="function"&&h()},emptyHint:L.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!L.length){const I=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(I,"info")}}function u(h){const L=h||document.getElementById("workspace-switcher-root");if(!L)return;const I=s(),S=i();let C,w;if(I==="client"&&S!=null){const M=(window._workspaceClientsCache||[]).find($=>Number($.id)===Number(S));C=b("building"),w=M?M.name:a("ws-current-label","当前工作空间")}else C=b("user"),w=a("ws-personal","个人事务");L.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+C+'<span class="ws-ctrl-label">'+f(w)+"</span></button>";const g=L.querySelector("#ws-ctrl-btn");g&&g.addEventListener("click",()=>c(null))}function f(h){return String(h??"").replace(/[&<>"']/g,function(L){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[L]})}function b(h){const L='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return h==="building"?L+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':L+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function B(h){h=h||{};const L=h.clients||[],I=h.active,S=document.getElementById("ws-modal");S&&S.remove();const C=document.createElement("div");C.id="ws-modal",C.className="ws-modal";const g='<button type="button" class="ws-modal-item'+(s()==="personal"||I==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+b("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+f(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+f(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let E="";if(L.length){const A=['<option value="">'+f(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(L.map(function(q){const F=I!=null&&Number(I)===Number(q.id);return'<option value="'+f(q.id)+'"'+(F?" selected":"")+">"+f(q.name||"#"+q.id)+"</option>"}));E='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+f(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+A.join("")+"</select></div>"}const M=!L.length&&h.emptyHint?'<div class="ws-modal-empty">'+f(h.emptyHint)+"</div>":"",$=h.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+f(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+f(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+f(a("ws-create-submit","创建"))+"</button></div></div>":"";C.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+f(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+f(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+g+E+"</div>"+M+$+"</div>",document.body.appendChild(C);const j=C.querySelector("[data-ws-select]");j&&j.addEventListener("change",function(){const A=j.value;A&&(typeof h.onPick=="function"&&h.onPick(A),_(),u())});function _(){C.remove()}C.addEventListener("click",function(A){if(A.target===C||A.target.closest("[data-ws-close]")){_();return}if(A.target.closest("[data-ws-personal]")){typeof h.onPersonal=="function"&&h.onPersonal(),_(),u();return}const F=A.target.closest("[data-ws-pick]");if(F){const Y=F.getAttribute("data-ws-pick");typeof h.onPick=="function"&&h.onPick(Y),_(),u();return}if(A.target.closest("[data-ws-create-toggle]")){const Y=C.querySelector("[data-ws-create-form]");if(Y){Y.style.display=Y.style.display==="none"?"flex":"none";const T=Y.querySelector("[data-ws-create-name]");T&&T.focus()}return}if(A.target.closest("[data-ws-create-submit]")){x(C,h,_);return}})}async function x(h,L,I){const S=h.querySelector("[data-ws-create-name]"),C=S?(S.value||"").trim():"";if(!C){S&&S.focus();return}let w=null;try{if(typeof window.apiPost=="function"){const E=await window.apiPost("/api/workspace/clients",{name:C});w=E&&typeof E.json=="function"?await E.json().catch(()=>null):E}}catch{w=null}const g=w&&(w.id||w.client&&w.client.id);if(!g){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await p(),d(Number(g)),L.onPick,I(),u()}window.openWorkspaceChooserUI=B,window.addEventListener("pearnly:workspace-changed",function(){u()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=d,window.enterPersonalMode=l,window.requireWorkspace=m,window.openWorkspaceChooser=c,window.renderWorkspaceControl=u,window.fetchWorkspaceClients=p;function v(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){c(null)},800)}catch{}}p().then(h=>{window._workspaceClientsCache=h,u(),v()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",u)})();(function(){const e=I=>document.querySelector('[data-num-target="'+I+'"]');function n(I){if(!I)return t("reconcile-last-activity-none");try{const S=new Date(I),C=new Date,w=C-S;if(w/6e4<5)return t("reconcile-last-activity-just-now");if(S.toDateString()===C.toDateString())return t("reconcile-last-activity-today");const E=Math.max(1,Math.floor(w/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",E)}catch{return t("reconcile-last-activity-none")}}function a(I,S,C){const w=e(I);w&&(w.textContent=C?"-":String(S),w.classList.toggle("is-empty",!!C))}function o(I){const S=document.getElementById("reconcile-error");S&&(S.style.display=I?"flex":"none")}function s(I){const S=document.getElementById("reconcile-empty");S&&(S.style.display=I?"flex":"none")}function i(I,S){const C=document.getElementById("reconcile-last-activity");C&&(C.textContent=I,C.classList.toggle("has-data",!!S))}function r(I){const S=!I||(I.total_sessions||0)===0;a("pending",I.pending||0,S),a("matched",I.matched||0,S),a("unmatched",I.unmatched||0,S),i(n(I.last_activity_at),!!I.last_activity_at),o(!1),s(S)}function d(I){const S=I.toUpperCase();return S==="KBANK"?"bank-chip-kbank":S==="SCB"?"bank-chip-scb":S==="BBL"?"bank-chip-bbl":S==="KTB"?"bank-chip-ktb":S==="TTB"?"bank-chip-ttb":"bank-chip-other"}function l(I,S){const C=w=>w?String(w).slice(0,10):"?";return!I&&!S?"":C(I)+" ~ "+C(S)}function p(I){return I==null?"":String(I).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function m(I){const S=document.getElementById("reconcile-recent"),C=document.getElementById("reconcile-recent-list");if(!S||!C)return;const w=(I||[]).slice(0,20);if(w.length===0){S.style.display="none";return}S.style.display="",s(!1),C.innerHTML=w.map(g=>{const E=g.parse_status==="parse_failed",M=g.bank_code||"OTHER",$=g.account_last4?" ···"+p(g.account_last4):"",j=l(g.period_start,g.period_end),_=p(g.source_filename||""),A=Number(g.tx_count||0),q=E?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",A)+"</span>";return'<div class="recon-card" data-session-id="'+p(g.id)+'" data-session-name="'+_+'"><span class="bank-chip '+d(M)+'">'+p(M)+'</span><div class="recon-card-main"><div class="recon-card-title">'+_+$+'</div><div class="recon-card-sub">'+p(j)+'</div></div><div class="recon-card-right">'+q+'</div><button class="recon-card-trash" data-trash="'+p(g.id)+'" title="'+p(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),C.querySelectorAll(".recon-card").forEach(g=>{g.addEventListener("click",E=>{E.target.closest(".recon-card-trash")||(g.dataset.sessionId,c())})}),C.querySelectorAll(".recon-card-trash").forEach(g=>{g.addEventListener("click",E=>{E.stopPropagation();const M=g.dataset.trash,$=g.closest(".recon-card"),j=$&&$.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(M,j)})})}function c(I){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const S=document.querySelector('[data-recon-tab="bank"]');S&&S.click()},150)}function u(){o(!0),s(!1)}function f(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const I=document.querySelector('[data-recon-tab="bank"]');I&&I.click()},150)}async function b(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),o(!1),s(!1);const I=document.getElementById("reconcile-recent");I&&(I.style.display="none");const S={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[C,w]=await Promise.all([fetch("/api/bank-recon/stats",{headers:S}),fetch("/api/bank-recon/sessions?limit=20",{headers:S})]);if(!C.ok)throw new Error("http "+C.status);const g=await C.json(),E=w.ok?await w.json():[];r(g||{}),m(E||[])}catch(C){console.warn("[reconcile] load failed",C),u()}}function B(I){if(!I||!I.length)return;const S="Bearer "+(localStorage.getItem("mrpilot_token")||"");let C=0;const w=I.length;Array.from(I).forEach(function(g){const E=new FormData;E.append("file",g,g.name);const M=new XMLHttpRequest;M.open("POST","/api/bank-recon/upload"),M.setRequestHeader("Authorization",S),M.onload=function(){C++;try{const $=JSON.parse(M.responseText);M.status===200&&$.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",$.tx_count),"success"):showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error")}C===w&&setTimeout(b,600)},M.onerror=function(){C++,showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error"),C===w&&setTimeout(b,600)},M.send(E)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function x(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const I=document.getElementById("reconcile-bank-file-input");I&&I.addEventListener("change",function(){B(this.files),this.value=""}),document.addEventListener("click",S=>{if(S.target.closest("#btn-reconcile-upload-top")||S.target.closest("#btn-reconcile-upload-empty")){f();return}if(S.target.closest("#btn-reconcile-retry")){b();return}if(S.target.closest("#btn-reconcile-dev-seed")){L();return}})}const v=["468b50c1-5593-4fd6-990d-515ce8085563"];function h(){const I=document.getElementById("btn-reconcile-dev-seed");if(!I)return;const S=typeof _userInfo<"u"?_userInfo:null,C=S&&S.id&&v.indexOf(String(S.id))>=0;I.style.display=C?"":"none"}async function L(){try{const I=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!I.ok)throw new Error("seed:"+I.status);const S=await I.json(),C=(t("reconcile-dev-seed-ok")||"").replace("{n}",S.tx_count||0);showToast(C,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const w=document.querySelector('[data-auto-tab="bank"]');w&&w.click(),S.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(S.session_id)},300)}catch(I){console.warn("[reconcile] dev seed failed",I),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){x(),h(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await b()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&b().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const b=a();if(b){if(!e.clients.length){b.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}b.innerHTML=e.clients.map(B=>{const x=String(B.id),v=e.selected.has(x)?"checked":"",h=escapeHtml(B.name||B.label||"#"+x),L=B.code?'<span class="assign-row-code">'+escapeHtml(B.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(x)+'" '+v+'><span class="assign-row-name">'+h+"</span>"+L+"</label>"}).join(""),d()}}function d(){const b=s();if(b){const x=t("assign-selected-count")||"已选 {n} / {total}";b.textContent=x.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const B=o();B&&(B.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function l(){const b=i();b&&(b.textContent=e.employeeName?" · "+e.employeeName:"")}async function p(b,B){e.employeeId=b,e.employeeName=B||"",e.opened=!0,e.selected=new Set,e.clients=[],l();const x=a();x&&(x.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const v=n();v&&(v.style.display="flex");try{const[h,L]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(b)+"/assignments")]);e.clients=h&&h.clients||[];const I=L&&L.client_ids||[];e.selected=new Set(I.map(String)),r()}catch(h){console.error("[assign-clients] load failed",h);const L=a();L&&(L.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function m(){e.opened=!1;const b=n();b&&(b.style.display="none")}async function c(){if(!e.employeeId)return;const b=Array.from(e.selected).map(x=>parseInt(x,10)).filter(x=>!isNaN(x)),B=document.getElementById("assign-modal-save");B&&(B.disabled=!0);try{const x=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:b});x&&x.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",b.length),"success"),m(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(x){console.error("[assign-clients] save failed",x),showToast(t("assign-save-failed")||"保存失败","error")}finally{B&&(B.disabled=!1)}}function u(){const b=n();if(!b||b.dataset.bound==="1")return;b.dataset.bound="1";const B=document.getElementById("assign-modal-close");B&&B.addEventListener("click",m);const x=document.getElementById("assign-modal-cancel");x&&x.addEventListener("click",m);const v=document.getElementById("assign-modal-save");v&&v.addEventListener("click",c),b.addEventListener("click",function(I){I.target===b&&m()});const h=o();h&&h.addEventListener("change",function(){h.checked?e.selected=new Set(e.clients.map(I=>String(I.id))):e.selected=new Set,r()});const L=a();L&&L.addEventListener("change",function(I){const S=I.target.closest('input[type="checkbox"][data-cid]');if(!S)return;const C=S.dataset.cid;S.checked?e.selected.add(C):e.selected.delete(C),d()})}function f(){e.opened&&(l(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",f),window.openAssignClientsModal=function(b,B){u(),p(b,B)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(m){if(!m)return"";try{return new Date(m).toLocaleString()}catch{return m}}function a(m){const c=document.getElementById("access-log-table");c&&(c.innerHTML='<div class="access-log-empty">'+escapeHtml(m)+"</div>");const u=document.getElementById("access-log-pager");u&&(u.innerHTML="")}function o(){const m=document.getElementById("access-log-table");if(!m)return;const c=e.rows||[];if(!c.length){a(t("set-access-log-empty"));return}const u=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,f=c.map(function(b){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(b.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(b.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(b.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(b.target_name||b.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(b.ip||"-")}</div>
                </div>`}).join("");m.innerHTML=u+f}function s(){const m=document.getElementById("access-log-pager");if(!m)return;const c=e.total||0;if(!c){m.innerHTML="";return}const u=e.page||1,f=e.per_page,b=Math.max(1,Math.ceil(c/f)),B=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",c),x=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",u).replace("{t}",b);m.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(B)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u-1}" ${u<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(x)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u+1}" ${u>=b?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(m){const c=localStorage.getItem("mrpilot_token");if(c){e.page=m||1,a(t("set-access-log-loading"));try{const u="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),f=await fetch(u,{headers:{Authorization:"Bearer "+c}});if(f.status===403){a(t("set-access-log-empty"));return}if(!f.ok)throw new Error("http_"+f.status);const b=await f.json();e.rows=b.logs||[],e.total=b.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const m=localStorage.getItem("mrpilot_token");if(m)try{const c="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),u=await fetch(c,{headers:{Authorization:"Bearer "+m}});if(!u.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const f=await u.blob(),b=document.createElement("a"),B=URL.createObjectURL(f);b.href=B,b.download="pearnly_access_log.csv",document.body.appendChild(b),b.click(),setTimeout(function(){URL.revokeObjectURL(B),b.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function d(){const m=document.querySelectorAll(".set-tab-owner-only"),c=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));m.forEach(function(u){u.style.display=c?"":"none"})}document.addEventListener("click",function(m){if(m.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(m.target.closest("#access-log-csv-btn")){m.preventDefault(),r();return}const f=m.target.closest(".access-log-pager-btn[data-access-log-page]");if(f&&!f.disabled){const b=parseInt(f.dataset.accessLogPage,10);i(b)}}),document.addEventListener("input",function(m){m.target&&m.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(m.target.value||"").trim(),i(1)},350))});let l=0;const p=setInterval(function(){l++,_userInfo&&(d(),clearInterval(p)),l>60&&clearInterval(p)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){d(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=C=>document.getElementById(C);async function n(C,w){return await fetch(C,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(w||{})})}async function a(C){return await fetch(C,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function i(C,w){if(!C)return;C.style.display="",C.className="notif-line-check "+(w?"bound":"unbound");const g=w?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';C.innerHTML=g+"<span>"+escapeHtml(t(w?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(C){if(C==null)return"-";const w=Number(C);return isNaN(w)?String(C):"฿ "+w.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function d(C){if(!C)return"-";try{const w=new Date(C),g=(w.getMonth()+1).toString().padStart(2,"0"),E=w.getDate().toString().padStart(2,"0"),M=w.getHours().toString().padStart(2,"0"),$=w.getMinutes().toString().padStart(2,"0");return`${g}-${E} ${M}:${$}`}catch{return C}}function l(C){const w=e("notif-rules-list"),g=e("notif-rules-empty"),E=e("notif-rules-count");if(!(!w||!g)){if(E.textContent=String(C.length),E.className="auto-status-pill "+(C.length>0?"active":"none"),!C.length){g.style.display="",w.style.display="none",w.innerHTML="";return}g.style.display="none",w.style.display="",w.innerHTML=C.map(M=>{const $=M.template_code==="large_invoice",j=$?"notif-rule-large-tag":"notif-rule-exception-tag",_=$?"large":"";let A=[];if($){const F=M.params&&M.params.threshold?r(M.params.threshold):"-";A.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+F)}M.enabled||A.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const q=A.length?A.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${M.enabled?"":" disabled"}" data-rule-id="${M.id}">
                    <span class="notif-rule-tmpl-badge ${_}">${escapeHtml(t(j))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(M.name)}</div>
                        <div class="notif-rule-meta">${q}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${M.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function p(C){const w=e("notif-logs-list");if(w){if(!C.length){w.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}w.innerHTML=C.map(g=>{const E=g.status==="sent",M=g.event_type==="exception_high"?"notif-event-exception-high":g.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",$=E?"":" · "+escapeHtml(g.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${E?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(M))}</div>
                        <div class="notif-log-meta">${escapeHtml(g.template_code||"-")}${$}</div>
                    </div>
                    <div class="notif-log-time">${d(g.sent_at)}</div>
                </div>`}).join("")}}async function m(){try{const C=await apiGet("/api/notifications/rules");c=C&&C.items||[],l(c)}catch(C){console.warn("load rules fail",C)}try{const C=await apiGet("/api/notifications/logs?limit=20");u=C&&C.items||[],p(u)}catch(C){console.warn("load logs fail",C)}}let c=null,u=null;function f(){c&&l(c),u&&p(u);const C=e("notif-new-modal");C&&C.style.display!=="none"&&o&&i(e("notif-line-check"),!!(o&&o.bound))}function b(){const C=e("notif-new-modal");C&&(C.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(w=>w.checked=!1),s().then(w=>i(e("notif-line-check"),!!(w&&w.bound))))}function B(){const C=e("notif-new-modal");C&&(C.style.display="none")}function x(){const C=document.querySelector('input[name="notif-template"]:checked'),w=e("notif-new-threshold-row");if(!C){w.style.display="none";return}w.style.display=C.value==="large_invoice"?"":"none";const g=e("notif-new-name");g&&!g.value.trim()&&(g.value=C.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function v(){const C=document.querySelector('input[name="notif-template"]:checked');if(!C){showToast(t("notif-new-template"),"error");return}const w=(e("notif-new-name").value||"").trim();if(!w){showToast(t("notif-name-required"),"error");return}const g={name:w,template_code:C.value,params:{},enabled:!0};if(C.value==="large_invoice"){const E=parseFloat(e("notif-new-threshold").value||"0");if(!E||E<=0){showToast(t("notif-threshold-required"),"error");return}g.params.threshold=E}try{const E=await apiPost("/api/notifications/rules",g);if(E&&E.ok)showToast(t("notif-toast-created"),"success"),B(),m();else{const M=await(E&&E.json&&E.json().catch(()=>({})))||{};showToast(M&&M.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function h(C,w,g){if(C==="toggle"){const E=g.classList.contains("on"),M=await n("/api/notifications/rules/"+w,{enabled:!E});M&&M.ok?(showToast(t(E?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),m()):showToast("toggle failed","error");return}if(C==="test"){const E=await s();if(!E||!E.bound){showToast(t("notif-line-error-bind-first"),"error");return}const M=await apiPost("/api/notifications/rules/"+w+"/test",{});if(M&&M.ok)showToast(t("notif-toast-test-sent"),"success"),m();else{const $=await(M&&M.json&&M.json().catch(()=>({})))||{},j=$&&$.detail||"";showToast(j||t("notif-toast-test-failed"),"error"),m()}return}if(C==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const M=await a("/api/notifications/rules/"+w);M&&M.ok?(showToast(t("notif-toast-deleted"),"success"),m()):showToast("delete failed","error");return}}let L=!1;function I(){if(L)return;L=!0;const C=e("notif-btn-new");C&&C.addEventListener("click",b);const w=e("notif-btn-refresh-logs");w&&w.addEventListener("click",m);const g=e("notif-new-close");g&&g.addEventListener("click",B);const E=e("notif-new-cancel");E&&E.addEventListener("click",B);const M=e("notif-new-save");M&&M.addEventListener("click",v),document.querySelectorAll('input[name="notif-template"]').forEach(_=>{_.addEventListener("change",x)});const $=e("notif-rules-list");$&&$.addEventListener("click",_=>{const A=_.target.closest("button[data-action]");if(!A)return;const q=A.closest("[data-rule-id]");q&&h(A.getAttribute("data-action"),q.getAttribute("data-rule-id"),A)});const j=e("notif-new-modal");j&&j.addEventListener("click",_=>{_.target===j&&B()})}async function S(){I(),await m()}window._loadNotificationsPanel=S,window._rerenderNotifications=f})();(function(){function n(v,h){try{return window.t&&window.t(v)||h}catch{return h}}function a(){var v="";try{v=localStorage.getItem("mrpilot_token")||""}catch{}return v?{Authorization:"Bearer "+v}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var v=document.createElement("style");v.id="recon-batch-style",v.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(v)}}function i(v){return v?v.dataset&&v.dataset.taskId?v.dataset.taskId:v.dataset&&v.dataset.taskid?v.dataset.taskid:"":""}function r(v){var h=document.getElementById(v.tbody);if(!h)return null;var L=h.closest("table");if(!L)return null;var I=L.querySelector("thead");if(!I)return null;if(I._reconReady)return I;var S=I.querySelector("tr");if(!S)return null;if(S.classList.add("recon-thead-default"),!S.querySelector(".recon-master-cb")){var C=document.createElement("th");C.className="recon-sel-cell";var w=document.createElement("input");w.type="checkbox",w.className="recon-master-cb",w.setAttribute("aria-label","select all"),w.addEventListener("change",function(){m(v,w.checked)}),C.appendChild(w),S.insertBefore(C,S.firstElementChild)}var g=S.children[1];g&&!g.classList.contains("recon-time-col")&&g.classList.add("recon-time-col");var E=S.children.length,M=document.createElement("tr");M.className="recon-thead-batch";var $=document.createElement("th");$.className="recon-sel-cell";var j=document.createElement("input");j.type="checkbox",j.className="recon-master-cb",j.checked=!0,j.setAttribute("aria-label","select all"),j.addEventListener("change",function(){m(v,j.checked)}),$.appendChild(j);var _=document.createElement("th");return _.setAttribute("colspan",String(E-1)),_.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',M.appendChild($),M.appendChild(_),I.appendChild(M),_.querySelector("[data-recon-del]").addEventListener("click",function(){b(v)}),_.querySelector("[data-recon-clear]").addEventListener("click",function(){f(v)}),I._reconReady=!0,u(v),I}function d(v){var h=document.getElementById(v.tbody);if(h){var L=h.querySelectorAll("tr");L.forEach(function(I){var S=i(I);if(S&&!I.querySelector(".recon-sel-cb")){var C=I.querySelector("td");if(C){var w=document.createElement("td");w.className="recon-sel-cell";var g=document.createElement("input");g.type="checkbox",g.className="recon-sel-cb",g.dataset.taskId=S,g.dataset.kind=v.kind,g.addEventListener("click",function(M){M.stopPropagation()}),g.addEventListener("change",function(){c(v)}),w.appendChild(g),I.insertBefore(w,C);var E=I.children[1];E&&!E.classList.contains("recon-time-col")&&E.classList.add("recon-time-col")}}}),c(v)}}function l(v){var h=document.getElementById(v.tbody);return h?Array.prototype.slice.call(h.querySelectorAll(".recon-sel-cb")):[]}function p(v){return l(v).filter(function(h){return h.checked}).map(function(h){return h.dataset.taskId})}function m(v,h){l(v).forEach(function(L){L.checked=!!h}),c(v)}function c(v){var h=p(v),L=l(v),I=document.getElementById(v.tbody);if(I){var S=I.closest("table"),C=S&&S.querySelector("thead");if(C){h.length>0?C.classList.add("recon-batch-mode"):C.classList.remove("recon-batch-mode"),C.querySelectorAll(".recon-master-cb").forEach(function(g){if(L.length===0){g.checked=!1,g.indeterminate=!1;return}h.length===L.length?(g.checked=!0,g.indeterminate=!1):h.length===0?(g.checked=!1,g.indeterminate=!1):(g.checked=!1,g.indeterminate=!0)});var w=C.querySelector("[data-recon-count]");w&&(w.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",h.length))}}}function u(v){var h=document.getElementById(v.tbody);if(h){var L=h.closest("table"),I=L&&L.querySelector("thead");if(I){var S=I.querySelector("[data-recon-del-label]"),C=I.querySelector("[data-recon-clear]");S&&(S.textContent=n("recon-batch-delete","批量删除")),C&&(C.textContent=n("recon-batch-clear","取消")),c(v)}}}function f(v){l(v).forEach(function(h){h.checked=!1}),c(v)}async function b(v){var h=p(v);if(h.length){var L=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",h.length),I=!1;try{typeof window.pearnlyConfirm=="function"?I=await window.pearnlyConfirm(L,n("recon-batch-delete-title","批量删除")):I=window.confirm(L)}catch{I=!1}if(I)try{var S=Object.assign({"Content-Type":"application/json"},a()),C=v.kind==="glv"?h.map(function(M){return parseInt(M,10)}):h,w=await fetch(v.api,{method:"POST",headers:S,body:JSON.stringify({ids:C})});if(!w.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var g=await w.json(),E=g&&(g.deleted!=null?g.deleted:g.count)||h.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",E),"success"),v.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function B(v){r(v),d(v);var h=document.getElementById(v.tbody);if(!(!h||h._reconBatchWatched)){h._reconBatchWatched=!0;var L=new MutationObserver(function(){d(v)});L.observe(h,{childList:!0,subtree:!1})}}function x(){s(),o.forEach(B),document.querySelectorAll(".recon-batch-bar").forEach(function(v){try{v.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",x):x(),setTimeout(x,1500),setTimeout(x,4e3),document.addEventListener("keydown",function(v){v.key==="Escape"&&o.forEach(function(h){p(h).length>0&&f(h)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(u)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(p){};function i(p){n=p;for(let u=1;u<=a;u++){const f=document.getElementById("ob-step-"+u);f&&(f.style.display=u===p?"block":"none")}document.querySelectorAll(".ob-dot").forEach(u=>{const f=parseInt(u.dataset.step,10);u.classList.toggle("active",f===p),u.classList.toggle("done",f<p)});const m=document.getElementById("ob-step-label");m&&(m.textContent=p+" / "+a);const c=document.getElementById("ob-next");if(c&&(c.textContent=p===a?t("ob-finish"):t("ob-next")),p===4){const u=document.getElementById("ob-line-input");u&&(u.value=e.line_id||"")}}function r(p){const m=document.querySelector(".onboarding-modal");if(!m)return;let c=m.querySelector(".ob-feedback");c||(c=document.createElement("div"),c.className="ob-feedback",m.appendChild(c)),c.textContent=p,c.classList.add("show"),setTimeout(()=>c.classList.remove("show"),1800)}document.addEventListener("click",p=>{const m=p.target.closest(".ob-option");if(!m)return;const c=m.parentElement;if(!c||!c.classList.contains("ob-options"))return;c.querySelectorAll(".ob-option").forEach(f=>f.classList.remove("selected")),m.classList.add("selected");const u=m.dataset.value;c.id==="ob-role-options"?e.role=u:c.id==="ob-volume-options"?e.monthly_volume=u:c.id==="ob-country-options"&&(e.country=u)}),document.addEventListener("click",p=>{p.target.id==="ob-skip"&&d()}),document.addEventListener("click",p=>{if(p.target.id==="ob-next"){if(n===4){const m=document.getElementById("ob-line-input");e.line_id=(m&&m.value||"").trim().replace(/^@+/,"")}d()}}),document.addEventListener("click",p=>{if(p.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const m=document.getElementById("onboarding-modal");m&&(m.style.display="none")}});function d(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):l()}async function l(){const p=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const m={};if(e.role&&(m.role=e.role),e.monthly_volume&&(m.monthly_volume=e.monthly_volume),e.country&&(m.country=e.country),e.line_id&&(m.line_id=e.line_id),Object.keys(m).length===0){p&&(p.style.display="none");return}try{const c=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(m)});c.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,m),setTimeout(()=>{p&&(p.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(m)),console.warn("onboarding profile save failed",c.status),r(t("ob-fb-saved-local")),setTimeout(()=>{p&&(p.style.display="none")},1500))}catch(c){console.error("onboarding submit",c),localStorage.setItem("pilot_ob_pending",JSON.stringify(m)),p&&(p.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function d(){return"DHL Express (Thailand) Co., Ltd."}function l(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:d(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>p(),window.loadPrefsSettings=()=>m(),window.loadArchiveSettings=()=>u();function p(){const w=document.getElementById("settings-contact-grid");if(!w)return;const g=_contact?.phone||"086-889-2228",E=_contact?.line_id||"@Pearnly",M=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",$=_contact?.email||"hello@pearnly.com",j=_contact?.address||"Bangkok, Thailand";w.innerHTML=`
            <a class="contact-item" href="${escapeHtml(M)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(E)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml($)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml($)}</div>
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
                    <div class="contact-value">${escapeHtml(j)}</div>
                </div>
            </div>
        `}async function m(){try{const w=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!w.ok)return;const g=await w.json(),E=document.getElementById("pref-dup-check");E&&(E.checked=!!g.enabled)}catch(w){console.warn("load prefs failed",w)}}const c=document.getElementById("pref-dup-check");c&&!c.dataset.bound&&(c.dataset.bound="1",c.addEventListener("change",async w=>{const g=w.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:g})})).ok?showToast(g?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(w.target.checked=!g,showToast(t("pref-save-failed"),"error"))}catch{w.target.checked=!g,showToast(t("pref-save-failed"),"error")}}));async function u(){const w=!!(_userInfo&&_userInfo.can_customize_archive);o=!w;const g=document.getElementById("archive-upgrade-banner");g&&(g.style.display=w?"none":"");const E=document.getElementById("archive-plus-badge");E&&(E.style.display=w?"none":"");try{const M=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!M.ok)throw new Error("load failed");const $=await M.json();e=Array.isArray($.name_template)?$.name_template:[],n=$.folder_strategy||"by_month_seller"}catch(M){console.error("load archive settings failed",M),showToast(t("archive-load-failed"),"error");return}f(),b(),B(),x()}function f(){const w=document.getElementById("archive-rule-canvas");if(w){if(e.length===0){w.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}w.innerHTML=e.map((g,E)=>{const M=i[g.type]||{label:g.type},$=s[g.type]||"",j=g.type==="sep"?`"${escapeHtml(g.val||"_")}"`:escapeHtml(t(M.label));return`
                <span class="archive-token ${g.type}"
                      data-token-idx="${E}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${$}</span>
                    <span class="token-label">${j}</span>
                </span>
            `}).join("")}}function b(){const w=document.getElementById("archive-field-palette");if(!w)return;const g=["date","seller","category","amount","invoice","buyer","sep"];w.innerHTML=g.map(E=>{const M=i[E],$=s[E]||"";return`
                <button class="archive-palette-btn ${E}" data-add-field="${E}" ${o?"disabled":""}>
                    <span class="token-icon">${$}</span>
                    <span>${escapeHtml(t(M.label))}</span>
                </button>
            `}).join("")}function B(){document.querySelectorAll('input[name="folder-strategy"]').forEach(w=>{w.checked=w.value===n,w.disabled=o})}async function x(){const w=document.getElementById("archive-preview-name"),g=document.getElementById("archive-preview-hint");if(g&&(g.textContent=t("archive-preview-hint",{category:r()})),!!w){if(e.length===0){w.textContent="-";return}try{const M=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:l().merged_fields,name_template:e})})).json();w.textContent=(M.name||"-")+".pdf"}catch{w.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const w=document.getElementById("archive-rule-modal");!w||w.style.display==="none"||(f(),b(),x())};let v=-1;document.addEventListener("dragstart",w=>{const g=w.target.closest(".archive-token");!g||o||(v=parseInt(g.dataset.tokenIdx,10),g.classList.add("dragging"),w.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",w=>{document.querySelectorAll(".archive-token").forEach(g=>g.classList.remove("dragging","drop-target")),v=-1}),document.addEventListener("dragover",w=>{const g=w.target.closest(".archive-token");g&&(w.preventDefault(),w.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(E=>E.classList.remove("drop-target")),g.classList.add("drop-target"))}),document.addEventListener("drop",w=>{const g=w.target.closest(".archive-token");if(!g||v<0||o)return;w.preventDefault();const E=parseInt(g.dataset.tokenIdx,10);if(E===v)return;const M=e.splice(v,1)[0];e.splice(E,0,M),v=-1,f(),x()}),document.addEventListener("click",w=>{if(w.target.closest("#btn-open-archive-rule")||w.target.closest("#btn-open-archive-rule-from-settings")){const $=document.getElementById("archive-rule-modal");$&&($.style.display="",u());return}if(w.target.closest("#archive-rule-modal-close")||w.target.id==="archive-rule-modal"){const $=document.getElementById("archive-rule-modal");$&&($.style.display="none");return}const g=w.target.closest(".settings-nav-item");if(g){switchSettingsTab(g.dataset.settingsTab);return}if(o&&w.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const E=w.target.closest("[data-add-field]");if(E){const $=E.dataset.addField,j=i[$],_={type:$,...j.defaultCfg};e.push(_),f(),x();return}const M=w.target.closest(".archive-token");if(M&&!o){h(parseInt(M.dataset.tokenIdx,10));return}if(w.target.closest("#btn-archive-save"))return S();if(w.target.closest("#btn-archive-reset"))return C();(w.target.closest("#archive-token-close")||w.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),w.target.closest("#btn-archive-token-ok")&&L(),w.target.closest("#btn-archive-token-delete")&&I()}),document.addEventListener("change",w=>{w.target.name==="folder-strategy"&&(n=w.target.value)});function h(w){a=w;const g=e[w];if(!g)return;const E=document.getElementById("archive-token-body");let M="";g.type==="date"?M=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${g.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${g.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${g.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${g.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:g.type==="seller"?M=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${g.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:g.type==="amount"?M=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${g.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:g.type==="sep"?M=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${g.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${g.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${g.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(g.val)?"":escapeHtml(g.val||"")}">
                    </div>
                </div>`:M=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,E.innerHTML=M,document.getElementById("archive-token-modal").style.display="",E.querySelectorAll(".sep-chip").forEach($=>{$.addEventListener("click",()=>{E.querySelectorAll(".sep-chip").forEach(_=>_.classList.remove("active")),$.classList.add("active");const j=document.getElementById("token-sep-custom");j&&(j.value="")})})}function L(){const w=e[a];if(w){if(w.type==="date")w.format=document.getElementById("token-date-format").value;else if(w.type==="seller")w.short=document.getElementById("token-seller-short").checked;else if(w.type==="amount")w.with_currency=document.getElementById("token-amount-currency").checked;else if(w.type==="sep"){const g=document.querySelector("#archive-token-body .sep-chip.active"),E=document.getElementById("token-sep-custom").value;w.val=E||(g?g.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",f(),x()}}function I(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",f(),x())}async function S(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const g=document.getElementById("archive-rule-modal");g&&(g.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function C(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",f(),B(),x())}})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,i=null,r=0,d=0,l=!1;function p(h){const L=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return h.preventDefault(),h.returnValue=L,L}function m(){l||(l=!0,window.addEventListener("beforeunload",p))}function c(){l&&(l=!1,window.removeEventListener("beforeunload",p))}function u(){if(document.getElementById("big-batch-progress"))return;const h=document.getElementById("file-list");if(!h||!h.parentNode)return;const L=document.createElement("div");L.id="big-batch-progress",L.className="big-batch-progress",L.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',h.parentNode.insertBefore(L,h);const I=document.getElementById("bbp-text");I&&(I.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function f(){const h=document.getElementById("big-batch-progress");h&&h.remove()}function b(){if(!i)return;let h=0;for(let M=0;M<i.length;M++){const $=i[M].status;($==="success"||$==="error"||$==="cancelled")&&h++}const L=r,I=L>0?Math.min(100,Math.floor(100*h/L)):0,S=(Date.now()-d)/1e3;let C;if(h>=3&&S>1){const M=S/h;C=(L-h)*M}else C=(L-h)*6/6;const w=Math.max(1,Math.ceil(C/60)),g=document.getElementById("bbp-fill"),E=document.getElementById("bbp-text");g&&(g.style.width=I+"%"),E&&(h>=L?E.textContent=t("big-batch-progress-done").replace("{total}",L):E.textContent=t("big-batch-progress-running").replace("{done}",h).replace("{total}",L).replace("{min}",w))}function B(h){try{if(localStorage.getItem(o)==="1")return}catch{}const L=Math.max(1,Math.ceil(h*6/6/60)),I=t("big-batch-first-tip").replace("{n}",h).replace("{min}",L);typeof showToast=="function"&&showToast(I,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function x(h){!h||h.length<100||(i=h,r=h.length,d=Date.now(),u(),m(),B(r),s&&clearInterval(s),s=setInterval(b,250),b())}function v(){s&&(clearInterval(s),s=null),c(),i&&r>=100?(b(),setTimeout(f,1200)):f(),i=null,r=0}window._bigBatchStart=x,window._bigBatchStop=v,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&b()})})();(function(){let e=null,n=!1,a=!1;function o(g){return typeof escapeHtml=="function"?escapeHtml(g==null?"":String(g)):String(g??"")}function s(g,E){try{typeof showToast=="function"&&showToast(g,E||"info")}catch{}}function i(){const g=typeof _userInfo<"u"?_userInfo:null;return!!(g&&(g.role==="owner"||g.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function d(g){if(!g)return!1;const E=String(g.status||"").toLowerCase();return E==="exception"||E==="exception_pending"||E==="rejected"}async function l(g){if(n&&!g)return e;const E=localStorage.getItem("mrpilot_token");if(!E)return null;try{const M=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+E}});if(!M.ok)throw new Error("http_"+M.status);e=await M.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function p(){const g=document.getElementById("erp-connect-cards");if(!g)return;const E=e;let M,$=!1;E?E.configured?E.connected?($=!0,M='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):M='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":M='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":M='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let j="";if(!E||!E.configured)j='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!E.connected)i()&&(j='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const k=!!E.auto_push,y=k?t("card-btn-disable"):t("card-btn-enable");j='<button type="button" class="'+(k?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(k?"1":"0")+'" title="'+o(k?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(y)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const _=E&&E.connected?"xero-card-desc-connected":"xero-card-desc-default",A=E&&E.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",q=(function(){const k=t(_);return k===_?A:k})();let F='<div class="integration-row erp-connect-xero'+($?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+M+'</div><div class="int-desc">'+o(q)+'</div></div><div class="int-actions">'+j+"</div></div>";if(E&&E.configured&&E.connected&&i()){const k=E.organisations||[];let y="";if(k.length>0){y+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(k.length)))+"</div>",y+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",y+='<div class="erp-cc-orgs">',k.forEach(function(z){y+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(z.id)+'"'+(z.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(z.organisation_name||z.organisation_id)+"</span></label>"}),y+="</div>";const H=!!E.auto_push,P=H?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");y+='<div class="erp-cc-auto-push" title="'+o(P)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(H?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",y+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}F+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+y+"</div>"}const D=g.querySelector(".erp-connect-xero"),V=g.querySelector("#erp-xero-details");V&&V.remove(),D?D.outerHTML=F:g.insertAdjacentHTML("afterbegin",F);const Y=document.getElementById("btn-xero-edit-toggle");Y&&Y.addEventListener("click",function(k){k.preventDefault();const y=document.getElementById("erp-xero-details");y&&(y.style.display=y.style.display==="none"?"":"none")});const T=document.getElementById("btn-xero-toggle-enabled");T&&T.addEventListener("click",async function(k){if(k.preventDefault(),T.disabled)return;const H=!(T.getAttribute("data-xero-enabled")==="1");if(!H)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}T.disabled=!0,await f(H,null)})}async function m(){const g=localStorage.getItem("mrpilot_token");if(g)try{const E=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+g}});if(!E.ok){let $="unknown";try{$=(await E.json()).detail||"unknown"}catch{}const j=String($).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+j)||$),"error");return}const M=await E.json();M.redirect_url&&(window.location.href=M.redirect_url)}catch(E){s(t("xero-push-fail").replace("{err}",E.message||"network"),"error")}}async function c(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const E=localStorage.getItem("mrpilot_token");try{const M=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+E}});if(!M.ok)throw new Error("http_"+M.status);await l(!0),p()}catch(M){s(t("xero-push-fail").replace("{err}",M.message),"error")}}async function u(g){const E=localStorage.getItem("mrpilot_token");try{const M=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+E,"Content-Type":"application/json"},body:JSON.stringify({token_id:g})});if(!M.ok)throw new Error("http_"+M.status);await l(!0),p()}catch(M){s(t("xero-push-fail").replace("{err}",M.message),"error")}}async function f(g,E){const M=localStorage.getItem("mrpilot_token");E&&(E.disabled=!0);try{const $=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+M,"Content-Type":"application/json"},body:JSON.stringify({on:!!g})});if(!$.ok){let j="unknown";try{j=(await $.json()).detail||"unknown"}catch{}throw new Error(j)}s(g?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await l(!0),p()}catch($){E&&(E.checked=!g),s(t("erp-auto-push-toggle-fail").replace("{err}",$.message||"network"),"error")}finally{E&&(E.disabled=!1)}}async function b(){const g=document.getElementById("drawer-history-save");if(!g||g.querySelector("#btn-xero-push")||g.querySelector("#pn-push-wrap")||(await l(!1),g.querySelector("#pn-push-wrap"))||g.querySelector("#btn-xero-push"))return;const E=r();if(!(E&&(E._historyId||E.history_id)))return;let $=!1,j="xero-push-tip";!e||!e.configured?($=!0,j="xero-err-not_configured"):e.connected?d(E)&&($=!0,j="xero-push-disabled-exc"):($=!0,j="xero-push-disabled-no-conn");const _=document.createElement("button");_.type="button",_.id="btn-xero-push",_.className="btn btn-ghost"+($?" disabled":""),_.disabled=$,_.title=t(j)||"",_.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",_.addEventListener("click",B);const A=document.getElementById("btn-push-erp");A&&A.parentNode?A.parentNode.insertBefore(_,A.nextSibling):g.insertBefore(_,g.firstChild)}async function B(){const g=r(),E=g&&(g._historyId||g.history_id);if(!E)return;const M=document.getElementById("btn-xero-push");M&&(M.disabled=!0,M.classList.add("loading"));const $=localStorage.getItem("mrpilot_token");try{const j=await fetch("/api/erp/xero/push/"+encodeURIComponent(E),{method:"POST",headers:{Authorization:"Bearer "+$}});if(!j.ok){let _="unknown";try{_=(await j.json()).detail||"unknown"}catch{}const A=String(_).replace(/^xero\./,"").toLowerCase(),q=t("xero-"+A),F=q&&q!=="xero-"+A?q:_;s(t("xero-push-fail").replace("{err}",F),"error");return}s(t("xero-push-ok"),"success")}catch(j){s(t("xero-push-fail").replace("{err}",j.message||"network"),"error")}finally{M&&(M.disabled=!1,M.classList.remove("loading"))}}async function x(){await l(!0),p(),v()}async function v(){const g=document.getElementById("erp-global-push-mode");if(!g)return;const E=localStorage.getItem("mrpilot_token");if(E)try{const M=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+E}});if(M.ok){const $=await M.json();$.mode&&(g.value=$.mode,g.dataset.prev=$.mode)}}catch{}}async function h(g){const E=g.value,M=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+M,"Content-Type":"application/json"},body:JSON.stringify({mode:E})})).ok?(g.dataset.prev=E,s(t("pref-erp-mode-saved"),"success")):(g.value=g.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{g.value=g.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function L(){try{const g=String(window.location.hash||"");if(g.indexOf("xero=ok")>=0){const E=g.match(/n=(\d+)/),M=E?E[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",M),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),l(!0).then(p)}else g.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function I(){if(a)return;a=!0,document.addEventListener("click",function(E){if(E.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(x,50);return}if(E.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(x,80);return}if(E.target.closest("#btn-xero-connect")){E.preventDefault(),m();return}if(E.target.closest("#btn-xero-disconnect")){E.preventDefault(),c();return}}),document.addEventListener("change",function(E){E.target&&E.target.matches('input[name="xero-default-org"]')&&u(E.target.value),E.target&&E.target.id==="xero-auto-push-toggle"&&f(E.target.checked,E.target),E.target&&E.target.id==="erp-global-push-mode"&&h(E.target)});const g=function(){return document.getElementById("drawer-body")};try{const E=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&b()}),M=g();if(M)E.observe(M,{childList:!0,subtree:!0});else{const $=new MutationObserver(function(){const j=g();j&&(E.observe(j,{childList:!0,subtree:!0}),$.disconnect())});$.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(L,500)}function S(){e&&p();const g=document.getElementById("btn-xero-push");if(g){const E=g.querySelector("span");E&&(E.textContent=t("xero-push-btn"))}}I(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",S);async function C(g){const E=Date.now();for(;Date.now()-E<g;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(M=>setTimeout(M,80))}return null}async function w(){await C(5e3);const g=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),E=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');g&&E&&await x()}setTimeout(w,200)})();(function(){var e="https://www.mrerp4sme.com/dms/index.php",n=null,a=!1;function o(x){return typeof escapeHtml=="function"?escapeHtml(x==null?"":String(x)):String(x??"")}function s(x,v){try{typeof showToast=="function"&&showToast(x,v||"info")}catch{}}function i(){return localStorage.getItem("mrpilot_token")}async function r(x){var v=i();if(!v)return null;try{var h=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+v}});if(!h.ok)throw new Error("http_"+h.status);var L=await h.json(),I=L&&L.items||[];n=I.find(function(S){return S&&(S.adapter||"").toLowerCase()==="mrerp_dms"})||null,a=!0}catch{n=null,a=!1}return n}function d(){var x=document.getElementById("erp-connect-cards");if(x){var v=x.querySelector("[data-mrerp-dms-zone]");v||(v=document.createElement("div"),v.setAttribute("data-mrerp-dms-zone","1"),x.appendChild(v));var h=n,L=!!(h&&h.enabled!==!1),I;h?L?I='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("dms-card-connected"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-disabled-pill"))+"</span>":I='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-not-connected"))+"</span>";var S;if(!h)S='<button type="button" class="int-btn-configure" id="btn-dms-connect">'+o(t("dms-card-connect"))+"</button>";else{var C=L?t("dms-card-disable"):t("dms-card-enable");S='<button type="button" class="int-btn-configure" id="btn-dms-edit">'+o(t("dms-card-edit"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-test">'+o(t("dms-card-test"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-toggle">'+o(C)+"</button>"}v.innerHTML='<div class="integration-row erp-connect-mrerp-dms'+(L?" connected":"")+'"><div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/><path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("dms-card-title"))+"</span>"+I+'</div><div class="int-desc">'+o(t("dms-card-desc"))+'</div></div><div class="int-actions">'+S+"</div></div>"}}function l(){var x=document.getElementById("dms-wizard-overlay");x&&x.remove(),document.removeEventListener("keydown",p)}function p(x){x.key==="Escape"&&l()}function m(){l();var x=n,v=x&&x.config&&x.config.booking_defaults&&x.config.booking_defaults.booking_prefix||"PN",h=function(S,C,w,g,E){return'<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">'+o(t(S))+'</span><input id="'+C+'" type="'+w+'" value="'+o(g||"")+'" placeholder="'+o(E||"")+'" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;"></label>'},L=document.createElement("div");L.id="dms-wizard-overlay",L.style.cssText="position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;",L.innerHTML='<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">'+o(t("dms-wizard-title"))+'</div><div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">'+o(t("dms-card-desc"))+"</div>"+h("dms-wizard-username","dms-w-user","text","","")+h("dms-wizard-password","dms-w-pass","password","","")+h("dms-wizard-prefix","dms-w-prefix","text",v,"PN")+'<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div><div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn btn-ghost" id="dms-w-cancel">'+o(t("dms-wizard-cancel"))+'</button><button type="button" class="btn btn-primary" id="dms-w-save">'+o(t("dms-wizard-save"))+"</button></div></div>",document.body.appendChild(L),document.addEventListener("keydown",p),L.addEventListener("click",function(S){S.target===L&&l()});var I=document.getElementById("dms-w-user");I&&I.focus()}function c(x){var v=document.getElementById("dms-w-err");v&&(v.textContent=x,v.style.display=x?"":"none")}async function u(){var x=n&&n.config&&n.config.system_url||e,v=(document.getElementById("dms-w-user")||{}).value||"",h=(document.getElementById("dms-w-pass")||{}).value||"",L=(document.getElementById("dms-w-prefix")||{}).value||"PN";if(x=x.trim(),v=v.trim(),!x||!v||!h){c(t("dms-wizard-required"));return}var I=document.getElementById("dms-w-save");I&&(I.disabled=!0,I.textContent=t("dms-wizard-saving")),c("");var S=i();try{var C=await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+S,"Content-Type":"application/json"},body:JSON.stringify({adapter:"mrerp_dms",config:{system_url:x,username:v,password:h}})}),w=await C.json().catch(function(){return{}});if(!C.ok||!w.ok){var g=w.error_friendly&&(w.error_friendly[window.currentLang]||w.error_friendly.en)||t("dms-connect-fail-generic");c(g),I&&(I.disabled=!1,I.textContent=t("dms-wizard-save"));return}var E={system_url:x,username_enc:v,password_enc:h,id_card_auto_push:!0,booking_defaults:{booking_prefix:L.trim()||"PN"}},M,$;n&&n.id?(M="PATCH",$="/api/erp/endpoints/"+encodeURIComponent(n.id)):(M="POST",$="/api/erp/endpoints");var j=M==="POST"?{name:"MR.ERP DMS",adapter:"mrerp_dms",config:E,is_default:!1,auto_push:!1}:{config:E,auto_push:!1},_=await fetch($,{method:M,headers:{Authorization:"Bearer "+S,"Content-Type":"application/json"},body:JSON.stringify(j)});if(!_.ok){var A=await _.json().catch(function(){return{}}),q=A&&A.detail&&(A.detail.code||A.detail)||"save_failed";c(t("dms-save-fail")+" ("+o(String(q))+")"),I&&(I.disabled=!1,I.textContent=t("dms-wizard-save"));return}l(),s(t("dms-connect-ok"),"success"),await r(!0),d(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{c(t("dms-connect-fail-generic")),I&&(I.disabled=!1,I.textContent=t("dms-wizard-save"))}}async function f(){if(!(!n||!n.id)){s(t("dms-test-running"),"info");var x=i();try{var v=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id)+"/test-connection?refresh=1",{method:"POST",headers:{Authorization:"Bearer "+x}}),h=await v.json().catch(function(){return{}});s(h&&h.ok?t("dms-test-ok"):t("dms-test-fail"),h&&h.ok?"success":"error")}catch{s(t("dms-test-fail"),"error")}}}async function b(){if(!(!n||!n.id)){var x=n.enabled===!1;if(!x)try{var v=await window.pearnlyConfirm(t("dms-confirm-disable"));if(!v)return}catch{}var h=i();try{var L=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id),{method:"PATCH",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({enabled:x})});if(!L.ok)throw new Error("http_"+L.status);s(x?t("dms-enabled-toast"):t("dms-disabled-toast"),"success"),await r(!0),d(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{s(t("dms-save-fail"),"error")}}}function B(){r().then(d)}document.addEventListener("click",function(x){if(x.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(B,60);return}if(x.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(B,90);return}if(x.target.closest("#btn-dms-connect")||x.target.closest("#btn-dms-edit")){x.preventDefault(),m();return}if(x.target.closest("#dms-w-cancel")){x.preventDefault(),l();return}if(x.target.closest("#dms-w-save")){x.preventDefault(),u();return}if(x.target.closest("#btn-dms-test")){x.preventDefault(),f();return}if(x.target.closest("#btn-dms-toggle")){x.preventDefault(),b();return}}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("mrerp-dms-adapter",d),setTimeout(function(){var x=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),v=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');x&&v&&B()},250)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const p=`
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
        </div>`,m=document.createElement("div");m.innerHTML=p,document.body.appendChild(m.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",c=>{c.target.id==="report-modal"&&a()})}function a(){const p=document.getElementById("report-modal");p&&(p.style.display="none"),o=null}let o=null;async function s(p,m){const c=p+":"+(m||"");if(e[c])return e[c];let u;try{const f=localStorage.getItem("mrpilot_token"),b=await fetch(`/api/reports/templates?lang=${encodeURIComponent(p)}`,{headers:{Authorization:"Bearer "+f}});if(!b.ok)throw new Error("templates fetch failed");u=(await b.json()).templates||[]}catch(f){console.error("fetchTemplates fail",f),u=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(u=u.filter(f=>f.code!=="erp"),m==="history-batch"){const f=u.findIndex(B=>B.code==="standard"),b=f>=0?f+1:u.length;u.splice(b,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[c]=u,u}function i(p){const m=document.getElementById("report-tpl-list"),c=p.map((f,b)=>`
            <label class="report-tpl-item${f.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${f.code}" ${f.recommended||b===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${r(f.name)}
                        ${f.recommended?`<span class="report-tpl-badge">${r(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${r(f.desc||"")}</div>
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
        `;m.innerHTML=c+u}function r(p){return p==null?"":String(p).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[m])}function d(p){const m=new Date,c=m.getFullYear(),u=m.getMonth()+1;if(p==="all")return"all";if(p==="this-month")return`${c}-${String(u).padStart(2,"0")}`;if(p==="last-month"){const f=new Date(c,u-2,1);return`${f.getFullYear()}-${String(f.getMonth()+1).padStart(2,"0")}`}return p==="this-year"?`${c}`:p==="this-quarter"?`${c}-Q${Math.floor((u-1)/3)+1}`:"all"}window.openReportModal=async function(p){p=p||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(B=>{const x=B.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][x]&&(B.textContent=I18N[currentLang][x])});const m=document.getElementById("report-period-section");m&&(m.style.display=p.mode==="client"?"":"none");const c=document.getElementById("report-tpl-list");c.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const u=await s(currentLang,p&&p.mode);i(u),o=p;const f=document.getElementById("report-modal-download"),b=f.cloneNode(!0);f.parentNode.replaceChild(b,f),b.addEventListener("click",()=>l(o))};async function l(p){if(!p)return;const m=document.querySelector('input[name="report-tpl"]:checked');if(!m){showToast(t("report-toast-no-selection"),"info");return}const c=m.value,u=document.querySelector('input[name="report-period"]:checked'),f=u?u.value:"all",b=d(f),B=document.getElementById("report-modal-download"),x=B.innerHTML;B.disabled=!0,B.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const v=localStorage.getItem("mrpilot_token");let h,L;if(p.mode==="records")h=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,records:p.records||[],meta:p.meta||{}})}),L=`mrpilot-${c}-${Date.now()}.xlsx`;else if(p.mode==="client"){const M=`/api/reports/clients/${p.clientId}/export?template=${encodeURIComponent(c)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(b)}`;h=await fetch(M,{headers:{Authorization:"Bearer "+v}}),L=`${(p.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${c}.xlsx`}else if(p.mode==="history-batch")c==="sales_detail_th"?(h=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),L=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(h=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),L=`mrpilot-batch-${c}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+p.mode);if(!h.ok){let M="HTTP "+h.status;try{const $=await h.json();$&&$.detail&&(M=$.detail)}catch($){console.warn("[batch-export] resp.json err.detail parse failed:",$)}h.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+M,"error");return}const I=await h.blob();let S=L;const w=(h.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(w)try{S=decodeURIComponent(w[1])}catch{}const g=URL.createObjectURL(I),E=document.createElement("a");E.href=g,E.download=S,document.body.appendChild(E),E.click(),document.body.removeChild(E),URL.revokeObjectURL(g),showToast(t("report-toast-success"),"success"),a()}catch(v){console.error("doDownload fail",v),showToast(t("report-toast-fail")+" · "+(v.message||""),"error")}finally{B.disabled=!1,B.innerHTML=x}}document.addEventListener("DOMContentLoaded",()=>{const p=document.getElementById("btn-export");if(p){const c=p.cloneNode(!0);p.parentNode.replaceChild(c,p),c.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(u=>({filename:u.filename,merged_fields:u.merged_fields||{}}))})})}const m=document.getElementById("history-batch-export");m&&m.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(p,m){openReportModal({mode:"client",clientId:p,clientName:m||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,o="mrpilot_folder_watcher",s=1;let i=null,r=null,d=null,l=60,p=!1,m=!1,c=0,u=0,f=0,b=[],B=null,x=!1;function v(){return i||(i=new Promise((N,K)=>{const O=indexedDB.open(o,s);O.onupgradeneeded=ae=>{const Z=ae.target.result;Z.objectStoreNames.contains("handles")||Z.createObjectStore("handles"),Z.objectStoreNames.contains("seen")||Z.createObjectStore("seen"),Z.objectStoreNames.contains("config")||Z.createObjectStore("config")},O.onsuccess=ae=>N(ae.target.result),O.onerror=ae=>K(ae.target.error)}),i)}function h(N,K){return v().then(O=>new Promise((ae,Z)=>{const ce=O.transaction(N,"readonly").objectStore(N).get(K);ce.onsuccess=()=>ae(ce.result),ce.onerror=()=>Z(ce.error)}))}function L(N,K,O){return v().then(ae=>new Promise((Z,ie)=>{const ce=ae.transaction(N,"readwrite");ce.objectStore(N).put(O,K),ce.oncomplete=()=>Z(),ce.onerror=()=>ie(ce.error)}))}function I(N,K){return v().then(O=>new Promise((ae,Z)=>{const ie=O.transaction(N,"readwrite");ie.objectStore(N).delete(K),ie.oncomplete=()=>ae(),ie.onerror=()=>Z(ie.error)}))}function S(N){return v().then(K=>new Promise((O,ae)=>{const Z=K.transaction(N,"readwrite");Z.objectStore(N).clear(),Z.oncomplete=()=>O(),Z.onerror=()=>ae(Z.error)}))}async function C(N){if(!N)return!1;try{const K={mode:"read"};let O=await N.queryPermission(K);return O==="granted"?!0:(O=await N.requestPermission(K),O==="granted")}catch(K){return console.warn("[folder] permission check failed:",K),!1}}function w(N,K){const O=document.getElementById("folder-status-summary");O&&(O.setAttribute("data-i18n",N),O.textContent=t(N),O.className="auto-status-pill"+(K?" "+K:""))}function g(N){["folder-unsupported","folder-empty","folder-active"].forEach(K=>{const O=document.getElementById(K);O&&(O.style.display=K===N?"":"none")})}function E(N){if(!N)return"-";const K=N instanceof Date?N:new Date(N),O=String(K.getHours()).padStart(2,"0"),ae=String(K.getMinutes()).padStart(2,"0"),Z=String(K.getSeconds()).padStart(2,"0");return`${O}:${ae}:${Z}`}function M(){g("folder-active");const N=document.getElementById("folder-config-path");N&&r&&(N.textContent=r.name||"-");const K=document.getElementById("folder-interval-select");K&&(K.value=String(l)),document.getElementById("folder-stat-last").textContent=B?E(B):"-",document.getElementById("folder-stat-processed").textContent=String(c),document.getElementById("folder-stat-failed").textContent=String(u),document.getElementById("folder-stat-queue").textContent=String(f);const O=document.getElementById("btn-folder-pause"),ae=document.getElementById("btn-folder-resume");O&&(O.style.display=p?"none":""),ae&&(ae.style.display=p?"":"none"),p?w("folder-status-paused","paused"):w("folder-status-running","running");const Z=document.getElementById("folder-status-text");Z&&(Z.setAttribute("data-i18n",p?"folder-status-paused":"folder-status-running"),Z.textContent=t(p?"folder-status-paused":"folder-status-running"));const ie=document.getElementById("folder-status-pulse");ie&&(ie.className="folder-status-pulse"+(p?" paused":"")),$()}function $(){const N=document.getElementById("folder-recent-list");if(N){if(b.length===0){N.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}N.innerHTML=b.slice(0,20).map(K=>{let O;K.status==="ok"?O=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:K.status==="dup"?O=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:K.status==="skip"?O=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:O=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const ae=K.status==="fail"&&K.error?K.error:K.status==="dup"&&K.reason||K.status==="skip"&&K.reason?K.reason:"",Z=ae?`<div class="folder-recent-err">${escapeHtml(ae)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${O}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(K.name)}</div>
                        ${Z}
                    </div>
                    <div class="folder-recent-time">${E(K.time)}</div>
                </div>
            `}).join("")}}function j(N){b.unshift(N),b.length>50&&(b.length=50),L("config","recent_list",b).catch(()=>{})}async function _(N){const K=new FormData;K.append("file",N,N.name),K.append("source","folder");const O=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:K});if(!O.ok){let ae="http_"+O.status;try{const Z=await O.json();ae=Z&&Z.detail?typeof Z.detail=="string"?Z.detail:Z.detail.code||JSON.stringify(Z.detail):ae}catch{}throw new Error(ae)}return await O.json()}async function A(N){try{const O=(await N.getFile()).size;return await new Promise(Z=>setTimeout(Z,3e3)),(await N.getFile()).size===O&&O>0}catch{return!1}}async function q(N,K,O,ae){if(ae>10)return;let Z;try{Z=await N.queryPermission({mode:"read"})}catch{Z="denied"}if(Z==="granted")for await(const ie of N.values()){const ce=K?`${K}/${ie.name}`:ie.name;if(ie.kind==="file"){if(!a.test(ie.name))continue;let fe;try{fe=await ie.getFile()}catch{continue}const ve=`${ce}::${fe.size}::${fe.lastModified}`;if(await h("seen",ve))continue;O.push({entry:ie,file:fe,seenKey:ve,relPath:ce})}else if(ie.kind==="directory")try{await q(ie,ce,O,ae+1)}catch{}}}async function F(){if(!(m||p||!r)){m=!0;try{if(await r.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),z(),showToast("warn",t("folder-permission-lost"));return}B=new Date;const K=[];await q(r,"",K,0),f=K.length,M();for(const O of K){if(p)break;if(!await A(O.entry)){f=Math.max(0,f-1),M();continue}try{let Z;try{Z=await O.entry.getFile()}catch{Z=O.file}const ie=await _(Z);await L("seen",O.seenKey,{name:Z.name,relPath:O.relPath,size:Z.size,lastModified:Z.lastModified,processed_at:Date.now()});const ce=ie.history_ids||(ie.history_id?[ie.history_id]:[]),fe=ie.duplicate_warnings||[],ve=O.relPath||Z.name;ce.length>0?(c+=ce.length,j({name:ve,status:"ok",time:new Date,history_id:ce[0],count:ce.length}),await L("config","processed_count",c)):fe.length>0?j({name:ve,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):j({name:ve,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(Z){u++,j({name:O.relPath||O.file.name,status:"fail",time:new Date,error:String(Z.message||Z)}),await L("config","failed_count",u)}f=Math.max(0,f-1),M()}}catch(N){console.warn("[folder] scan error:",N)}finally{m=!1,M()}}}function D(){d&&clearInterval(d),d=setInterval(F,l*1e3)}function V(){d&&(clearInterval(d),d=null)}function Y(N){if(!r||p)return;const K=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return N.preventDefault(),N.returnValue=K,K}function T(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",Y))}function k(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",Y))}function y(){p=!1,D(),T(),M(),F()}function H(){p=!0,V(),k(),M()}function P(){p=!1,D(),T(),M(),F()}function z(){p=!0,V(),k()}async function G(){try{const N=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await C(N)){showToast("warn",t("folder-permission-denied"));return}r=N,await L("handles","main",N),c=0,u=0,f=0,b=[],await L("config","processed_count",0),await L("config","failed_count",0),await S("seen"),y()}catch(N){N&&N.name!=="AbortError"&&console.warn("[folder] pick failed:",N)}}async function Q(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(z(),r=null,c=0,u=0,f=0,b=[],await I("handles","main"),await I("config","processed_count"),await I("config","failed_count"),await S("seen"),g("folder-empty"),w("folder-status-empty",""))}async function te(){b=[];try{await I("config","recent_list")}catch{}$()}async function R(){if(x)return;if(x=!0,!n){g("folder-unsupported"),w("folder-status-unsupported",""),W();return}U();let N=null;try{N=await h("handles","main")}catch{}if(!N){g("folder-empty"),w("folder-status-empty","");return}if(!await C(N)){g("folder-empty"),w("folder-status-empty",""),await I("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}r=N;try{c=await h("config","processed_count")||0}catch{}try{u=await h("config","failed_count")||0}catch{}try{const O=await h("config","recent_list");Array.isArray(O)&&(b=O.map(ae=>({...ae,time:ae.time?new Date(ae.time):new Date})))}catch{}y()}function U(){const N=document.getElementById("btn-folder-pick"),K=document.getElementById("btn-folder-pause"),O=document.getElementById("btn-folder-resume"),ae=document.getElementById("btn-folder-scan-now"),Z=document.getElementById("btn-folder-remove"),ie=document.getElementById("btn-folder-clear-recent"),ce=document.getElementById("folder-interval-select");N&&N.addEventListener("click",G),K&&K.addEventListener("click",H),O&&O.addEventListener("click",P),ae&&ae.addEventListener("click",()=>{F()}),Z&&Z.addEventListener("click",Q),ie&&ie.addEventListener("click",te),ce&&ce.addEventListener("change",fe=>{l=parseInt(fe.target.value,10)||60,p||D()}),J()}function J(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(N=>{N.dataset.tabJumpBound||(N.dataset.tabJumpBound="1",N.addEventListener("click",K=>{const O=K.currentTarget.dataset.tabJump;if(O==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(O==="upload"){const ae=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');ae&&ae.click()}}))})}function W(){J()}window._loadFolderWatcherPanel=R;function X(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(K=>/chromium|google chrome|microsoft edge/i.test(K.brand||""))}catch{}const N=navigator.userAgent||"";return!!(/Edg\//.test(N)||/Chrome\//.test(N)&&!/OPR\/|YaBrowser|Opera/.test(N))}function se(){try{if(X()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const N=document.getElementById("chrome-only-banner");if(!N)return;const K=N.querySelector('[data-i18n="chrome-banner-msg"]'),O=N.querySelector('[data-i18n="chrome-banner-dismiss"]');K&&typeof t=="function"&&(K.textContent=t("chrome-banner-msg")),O&&typeof t=="function"&&(O.textContent=t("chrome-banner-dismiss")),N.style.display="";const ae=document.getElementById("chrome-only-banner-close");ae&&!ae.dataset.bound&&(ae.dataset.bound="1",ae.addEventListener("click",()=>{N.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",se):setTimeout(se,0)),window._refreshChromeBanner=se})();const To=`
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
    `;we("email-modal",To);(function(){let e=null,n=null,a="new",o=!1,s=!1;async function i(){const _=document.getElementById("email-empty"),A=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!_||!A))try{const q=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(q.status===401){localStorage.removeItem("mrpilot_token");const D=await q.json().catch(()=>({}));if((typeof D.detail=="string"?D.detail:D.detail&&D.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!q.ok){d("none");return}const F=await q.json();e=F.account||null,n=F.presets||{},o=!0,r(),e&&E()}catch(q){console.error("[email-ingest] load failed",q),d("none")}}function r(){const _=document.getElementById("email-empty"),A=document.getElementById("email-account-card"),q=document.getElementById("email-logs-section");if(!e){_.style.display="",A.style.display="none",q&&(q.style.display="none"),d("none");return}_.style.display="none",A.style.display="",q&&(q.style.display="");const F=document.getElementById("email-account-addr"),D=document.getElementById("email-account-host"),V=document.getElementById("email-account-last"),Y=document.getElementById("email-last-error"),T=document.getElementById("email-enabled-toggle");if(F&&(F.textContent=e.email_address||"-"),D&&(D.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),V){const k=e.last_fetched_at;if(!k)V.textContent=t("email-last-never");else{const y=l(k),H=!e.last_error;V.textContent=H?t("email-last-ok",{time:y}):t("email-last-fail",{time:y})}}Y&&(e.last_error?(Y.style.display="",Y.textContent=p(e.last_error)):Y.style.display="none"),T&&(T.checked=!!e.enabled),e.enabled?e.last_error?d("error"):d("on"):d("off")}function d(_){const A=document.getElementById("email-status-summary");if(!A)return;A.classList.remove("none","ready","active","coming");let q="auto-status-loading";_==="none"?(q="email-status-none",A.classList.add("none")):_==="on"?(q="email-status-on",A.classList.add("active")):_==="off"?(q="email-status-off",A.classList.add("coming")):_==="error"&&(q="email-status-error",A.classList.add("none")),A.setAttribute("data-i18n",q),A.textContent=t(q)}function l(_){if(!_)return"";const A=new Date(_);if(isNaN(A.getTime()))return"";const q=F=>String(F).padStart(2,"0");return`${q(A.getMonth()+1)}-${q(A.getDate())} ${q(A.getHours())}:${q(A.getMinutes())}`}function p(_){if(!_)return"";const A=String(_);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(A)?t("email-test-auth-fail"):/timeout|timed out/i.test(A)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(A),A)}function m(_){a=_;const A=document.getElementById("email-modal");if(!A)return;const q=document.getElementById("email-preset");q.innerHTML="";const F=n||{},D=["gmail","outlook","yahoo","icloud","qq","163","custom"],V={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};D.forEach(U=>{if(!F[U])return;const J=document.createElement("option");J.value=U,J.textContent=U==="custom"?t("email-preset-custom"):V[U]||U,q.appendChild(J)});const Y=document.getElementById("email-modal-title"),T=document.getElementById("email-address"),k=document.getElementById("email-password"),y=document.getElementById("email-imap-host"),H=document.getElementById("email-imap-port"),P=document.getElementById("email-imap-ssl"),z=document.getElementById("email-folder"),G=document.getElementById("email-mark-read"),Q=document.getElementById("email-bind-enabled"),te=document.getElementById("email-test-result"),R=document.getElementById("email-adv-details");if(te&&(te.style.display="none",te.textContent=""),_==="edit"&&e){Y.setAttribute("data-i18n","email-modal-title-edit"),Y.textContent=t("email-modal-title-edit"),T.value=e.email_address||"",k.value="",k.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),k.placeholder=t("email-field-password-edit-ph"),y.value=e.imap_host||"",H.value=e.imap_port||993,P.checked=e.imap_use_ssl!==!1,z.value=e.folder||"INBOX",G.checked=e.mark_as_read!==!1,Q.checked=e.enabled!==!1;const U=document.getElementById("email-filter-sender"),J=document.getElementById("email-filter-subject");U&&(U.value=e.filter_sender||""),J&&(J.value=e.filter_subject||""),h(e.interval_min||15),q.value=B(e.imap_host)||"custom",R&&(R.open=!0)}else{Y.setAttribute("data-i18n","email-modal-title-new"),Y.textContent=t("email-modal-title-new"),T.value="",k.value="",k.setAttribute("data-i18n-placeholder","email-field-password-ph"),k.placeholder=t("email-field-password-ph"),q.value="gmail",u("gmail"),z.value="INBOX",G.checked=!0,Q.checked=!0;const U=document.getElementById("email-filter-sender"),J=document.getElementById("email-filter-subject");U&&(U.value=""),J&&(J.value=""),h(15),R&&(R.open=!1)}v(),A.style.display="flex",setTimeout(()=>T.focus(),60)}function c(){const _=document.getElementById("email-modal");_&&(_.style.display="none")}function u(_){const A=(n||{})[_];if(!A||_==="custom")return;const q=document.getElementById("email-imap-host"),F=document.getElementById("email-imap-port"),D=document.getElementById("email-imap-ssl");q&&(q.value=A.host||""),F&&(F.value=A.port||993),D&&(D.checked=A.ssl!==!1)}const f={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function b(_){if(!_||!_.includes("@"))return;const A=_.split("@")[1].toLowerCase().trim(),q=f[A];if(!q)return;const F=document.getElementById("email-preset");if(!F)return;const D=F.value;D&&D!=="custom"&&D!==""&&D===q||(F.value=q,u(q))}function B(_){if(!_)return null;const A=n||{};for(const q in A)if(q!=="custom"&&A[q]&&A[q].host===_)return q;return null}function x(){const _=document.querySelector("#email-interval-options .email-interval-btn.active"),A=_?parseInt(_.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(A)?A:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function v(){const _=document.getElementById("email-interval-options");!_||_._bound||(_._bound=!0,_.addEventListener("click",A=>{const q=A.target.closest(".email-interval-btn");q&&(_.querySelectorAll(".email-interval-btn").forEach(F=>F.classList.remove("active")),q.classList.add("active"))}))}function h(_){const A=[5,15,60].includes(_)?_:15,q=document.getElementById("email-interval-options");q&&q.querySelectorAll(".email-interval-btn").forEach(F=>{F.classList.toggle("active",parseInt(F.dataset.interval,10)===A)})}function L(_,A){const q=document.getElementById("email-test-result");q&&(q.style.display="",q.textContent=A,q.className="form-test-result "+(_==="ok"?"ok":_==="running"?"running":"fail"))}async function I(){const _=x();if(!_.email_address){L("fail",t("email-addr-required"));return}if(!_.password){L("fail",t("email-password-required"));return}if(!_.imap_host){L("fail",t("email-host-required"));return}const A=document.getElementById("btn-email-modal-test");A&&(A.disabled=!0),L("running",t("email-test-running"));try{const q=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:_.email_address,password:_.password,imap_host:_.imap_host,imap_port:_.imap_port,imap_use_ssl:_.imap_use_ssl,folder:_.folder})}),F=await q.json().catch(()=>({}));if(q.ok&&F.success)L("ok",t("email-test-ok",{folder:_.folder,n:F.folder_count??"?"}));else{const D=F.error_msg||"";D==="auth_failed"||/auth/i.test(D)?L("fail",t("email-test-auth-fail")):L("fail",t("email-test-fail",{msg:D||q.status}))}}catch(q){L("fail",t("email-test-fail",{msg:String(q).slice(0,120)}))}finally{A&&(A.disabled=!1)}}async function S(){const _=x();if(!_.email_address){L("fail",t("email-addr-required"));return}if(a==="new"&&!_.password){L("fail",t("email-password-required"));return}if(!_.imap_host){L("fail",t("email-host-required"));return}const A=document.getElementById("btn-email-modal-save");A&&(A.disabled=!0);const q={..._};a==="edit"&&!q.password&&delete q.password;try{const F=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(q)}),D=await F.json().catch(()=>({}));if(F.ok&&D.ok)e=D.account,showToast(t("email-save-ok"),"success"),c(),r(),E();else{const Y="email."+(D.detail||"").split(".").slice(-1)[0];L("fail",t(Y)!==Y?t(Y):t("email-save-fail"))}}catch{L("fail",t("email-save-fail"))}finally{A&&(A.disabled=!1)}}async function C(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),r();const q=document.getElementById("email-logs-list");q&&(q.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function w(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const _=document.getElementById("btn-email-trigger"),A=_?_.innerHTML:"";_&&(_.disabled=!0,_.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const q=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),F=await q.json().catch(()=>({}));if(q.ok){const D=F.emails_scanned||0,V=F.ocr_succeeded||0,Y=F.ocr_failed||0;D===0&&V===0&&Y===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:D,ok:V,fail:Y}),Y>0?"warn":"success")}else{const V="email."+(F.detail||"").split(".").slice(-1)[0];showToast(t(V)!==V?t(V):t("email-trigger-fail"),"error")}await i()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,_&&(_.disabled=!1,_.innerHTML=A)}}async function g(){if(!e)return;const _=document.getElementById("email-enabled-toggle"),A=!!(_&&_.checked),q=e.enabled;try{const F=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:A})}),D=await F.json().catch(()=>({}));F.ok&&D.ok?(e=D.account,r()):(_&&(_.checked=q),showToast(t("email-toggle-fail"),"error"))}catch{_&&(_.checked=q),showToast(t("email-toggle-fail"),"error")}}async function E(){const _=document.getElementById("email-logs-list");if(_){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const A=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!A.ok){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const q=await A.json();if(!Array.isArray(q)||q.length===0){_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}_.innerHTML=q.map(M).join("")}catch{_.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function M(_){const A=l(_.created_at),q=_.status||"failed",F=q==="success"?"ok":q==="partial"?"partial":"fail",D=q==="success"?"✓":q==="partial"?"◐":"✗",V=_.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,Y=t("email-log-counts",{scanned:_.emails_scanned||0,att:_.attachments_found||0,ok:_.ocr_succeeded||0,fail:_.ocr_failed||0}),T=(_.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${F}">
                <span class="log-time">${escapeHtml(A)}</span>
                <span class="log-status">${D}</span>
                ${V}
                <span class="log-counts">${escapeHtml(Y)}</span>
                <span class="log-elapsed">${escapeHtml(T)}</span>
            </div>
        `}function $(){const _=document.getElementById("btn-email-bind");_&&_.addEventListener("click",()=>m("new"));const A=document.getElementById("btn-email-edit");A&&A.addEventListener("click",()=>m("edit"));const q=document.getElementById("btn-email-unbind");q&&q.addEventListener("click",C);const F=document.getElementById("btn-email-trigger");F&&F.addEventListener("click",w);const D=document.getElementById("email-enabled-toggle");D&&D.addEventListener("change",g);const V=document.getElementById("email-modal-close");V&&V.addEventListener("click",c);const Y=document.getElementById("btn-email-modal-cancel");Y&&Y.addEventListener("click",c);const T=document.getElementById("btn-email-modal-test");T&&T.addEventListener("click",I);const k=document.getElementById("btn-email-modal-save");k&&k.addEventListener("click",S);const y=document.getElementById("email-preset");y&&y.addEventListener("change",z=>u(z.target.value));const H=document.getElementById("email-address");H&&!H.dataset.autoBound&&(H.dataset.autoBound="1",H.addEventListener("blur",z=>b((z.target.value||"").trim())),H.addEventListener("input",z=>{const G=(z.target.value||"").trim();G.includes("@")&&G.split("@")[1].includes(".")&&b(G)}));const P=document.getElementById("btn-email-refresh-logs");P&&P.addEventListener("click",()=>{P.classList.add("spinning"),setTimeout(()=>P.classList.remove("spinning"),600),E()})}$(),window._loadEmailIngestPanel=i,window._rerenderEmailIngest=function(){if(!o)return;r();const _=document.getElementById("email-logs-section");e&&_&&_.open&&E()};let j=null;window._startEmailLogAutoRefresh=function(){j||(j=setInterval(()=>{e&&o&&E()},3e4))},window._stopEmailLogAutoRefresh=function(){j&&(clearInterval(j),j=null)}})();const Mo=`
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
`;we("bank-cand-drawer",Mo);const $o=`
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
`;we("bank-client-picker-modal",$o);const ee={sessions:[],currentSession:null,currentTxs:[],currentFilter:"all",currentTxForDrawer:null,loaded:!1,queue:[],qSeq:0,sessionFilter:"all",pickerSelected:null};function Ho(e){const n=Number(e||0);let a="score-low";return n>=85?a="score-high":n>=60&&(a="score-mid"),'<span class="bank-cand-score '+a+'">'+n.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Ao(e){const n=document.getElementById("bank-upload-progress");n&&(n.style.display="none")}function jo(){const e=document.getElementById("bank-upload-error");e&&(e.style.display="none")}function Po(e){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[e]||t("bank-err-unknown")+" ("+e+")"}function Re(e){if(e==null)return"-";const n=Number(e);return isNaN(n)?"-":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function Ue(e){if(!e)return"-";const n=String(e);return n.length>=10?n.slice(0,10):n}function Dn(e,n){return!e&&!n?"":(Ue(e)||"?")+" ~ "+(Ue(n)||"?")}function de(e){return e==null?"":String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}async function Do(e){ee.currentTxForDrawer=e;const n=document.getElementById("bank-detail-body");n&&n.classList.add("has-pane");const a=document.getElementById("bank-cand-pane-title"),o=document.getElementById("bank-cand-pane-sub"),s=document.getElementById("bank-cand-pane-foot");if(a&&(a.textContent=t("bank-cand-pane-current")),o){const r=e.direction==="OUT"?"-":"+",d=e.direction==="OUT"?"bank-out":"bank-in";o.innerHTML=`${de(Ue(e.tx_date))}
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <span>${de(e.description||"-")}</span>
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <strong class="${d}">${r}${Re(e.amount)}</strong>`}s&&(s.style.display="");const i=document.getElementById("bank-cand-pane-body");if(i){i.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const r=await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!r.ok)throw new Error("cands:"+r.status);const d=await r.json();Ro(e,d.candidates||[])}catch{i.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function qo(e,n,a){const o=n.history_id,s=n.invoice_no||"-",i=n.vendor||"-",r=n.amount_total!==null&&n.amount_total!==void 0?Re(n.amount_total):"-",d=n.invoice_date?Ue(n.invoice_date):"-",l=n.filename||"",p=!!a&&e.matched_history_id===o,m="bank-cand-card"+(n.is_auto_picked?" is-auto":"")+(p?" is-picked":"");let c="";return p?c='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":c='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+de(o)+'"><span>'+t(n.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+m+'" data-hid="'+de(o)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+de(i)+"</div>"+Ho(n.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+de(s)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+r+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+de(d)+"</span></div>"+(l?'<div class="bank-cand-card-file" title="'+de(l)+'">'+de(l)+"</div>":"")+(n.reason?'<div class="bank-cand-card-reason">'+de(n.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+c+"</div></div>"}function Ro(e,n){const a=document.getElementById("bank-cand-pane-body");if(!a)return;const o=n||[];let s="";if(e.match_status==="matched")s='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",o.length)+"</div>";else if(e.match_status==="suggested")s='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",o.length)+"</div>";else if(o.length>0)s='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",o.length)+"</div>";else{a.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const i=e.match_status==="matched",r=o.map(d=>qo(e,d,i)).join("");a.innerHTML=s+'<div class="bank-cand-list">'+r+"</div>",a.querySelectorAll('[data-act="pick"]').forEach(d=>{d.addEventListener("click",()=>{No(d.dataset.hid)})}),a.querySelectorAll('[data-act="unmatch"]').forEach(d=>{d.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),at(),await Ge(ee.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function at(){const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane");const n=document.getElementById("bank-cand-pane-title"),a=document.getElementById("bank-cand-pane-sub"),o=document.getElementById("bank-cand-pane-body"),s=document.getElementById("bank-cand-pane-foot");n&&(n.textContent=t("bank-cand-pane-empty-title")),a&&(a.textContent=t("bank-cand-pane-empty-sub")),s&&(s.style.display="none"),o&&(o.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const i=document.getElementById("bank-tx-tbody");i&&i.querySelectorAll("tr.is-selected").forEach(r=>r.classList.remove("is-selected")),ee.currentTxForDrawer=null}async function Ge(e){try{const n="/api/bank-recon/sessions/"+encodeURIComponent(e)+(ee.currentFilter!=="all"?"?filter="+ee.currentFilter:""),a=await fetch(n,{headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("detail:"+a.status);const o=await a.json();ee.currentSession=o.session,ee.currentTxs=o.transactions||[],Jo()}catch(n){console.warn("[bank-recon] loadSessionDetail failed",n),showToast(t("bank-load-failed"),"error")}}async function Fo(){if(!ee.currentSession)return;const e=document.getElementById("btn-bank-run-match"),n=e.innerHTML;e.disabled=!0,e.innerHTML="<span>"+t("bank-matching")+"</span>";try{const a=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(ee.currentSession.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("match:"+a.status);const o=await a.json();showToast(t("bank-match-done").replace("{matched}",o.matched).replace("{suggested}",o.suggested).replace("{unmatched}",o.unmatched),"success"),await Ge(ee.currentSession.id),await Ke()}catch(a){console.warn("[bank-recon] match failed",a),showToast(t("bank-match-failed"),"error")}finally{e.disabled=!1,e.innerHTML=n}}async function zo(){if(!(!ee.currentSession||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const n=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(ee.currentSession.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!n.ok)throw new Error("delete:"+n.status);showToast(t("bank-deleted"),"success"),ee.currentSession=null,ee.currentTxs=[],Jt(),await Ke()}catch(n){console.warn("[bank-recon] delete failed",n),showToast(t("bank-delete-failed"),"error")}}async function nn(){if(ee.currentTxForDrawer)try{const e=await fetch("/api/bank-recon/tx/"+encodeURIComponent(ee.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!e.ok)throw new Error("ignore:"+e.status);at(),await Ge(ee.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}async function No(e){if(ee.currentTxForDrawer)try{const n=await fetch("/api/bank-recon/tx/"+encodeURIComponent(ee.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:e})});if(!n.ok)throw new Error("pick:"+n.status);showToast(t("bank-matched-ok"),"success"),at(),await Ge(ee.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}function qn(){if(!ee.currentSession)return;const e=ee.currentSession;document.getElementById("bank-detail-title").textContent=(e.bank_code||"-")+(e.account_last4?" ···"+e.account_last4:"")+" · "+(e.source_filename||""),document.getElementById("bank-meta-period").textContent=Dn(e.period_start,e.period_end)||"-",document.getElementById("bank-meta-opening").textContent=Re(e.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+Re(e.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+Re(e.total_outflow),document.getElementById("bank-meta-closing").textContent=Re(e.closing_balance);const n=ee.currentTxs||[],a=n.length;let o=0,s=0,i=0;for(const r of n){const d=r.match_status||"unmatched";d==="matched"?o++:d==="suggested"?s++:i++}document.getElementById("bank-stat-total").textContent=a,document.getElementById("bank-stat-matched").textContent=o,document.getElementById("bank-stat-suggested").textContent=s,document.getElementById("bank-stat-unmatched").textContent=i}function Gt(){const e=document.getElementById("bank-tx-tbody");if(!e)return;let n=ee.currentTxs||[];if(ee.currentFilter!=="all"&&(n=n.filter(a=>ee.currentFilter==="matched"?a.match_status==="matched":ee.currentFilter==="suggested"?a.match_status==="suggested":ee.currentFilter==="unmatched"?a.match_status==="unmatched"||a.match_status==="ignored":!0)),n.length===0){e.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(e.innerHTML=n.map(a=>Oo(a)).join(""),e.querySelectorAll("tr[data-tx-id]").forEach(a=>{a.addEventListener("click",()=>{const o=a.dataset.txId,s=ee.currentTxs.find(i=>i.id===o);s&&(e.querySelectorAll("tr.is-selected").forEach(i=>i.classList.remove("is-selected")),a.classList.add("is-selected"),Do(s))})}),ee.currentTxForDrawer){const a=e.querySelector('tr[data-tx-id="'+ee.currentTxForDrawer.id+'"]');a&&a.classList.add("is-selected")}}function Oo(e){const n=e.direction==="OUT",a=n?"-":"+",o=n?"bank-out":"bank-in",s=e.match_status||"unmatched",i=t("bank-match-"+s)||s,r=Ue(e.tx_date),d=e.channel?`<span class="bank-tx-channel">${de(e.channel)}</span>`:"";return`
        <tr data-tx-id="${de(e.id)}">
            <td class="bank-tx-date">${de(r)}</td>
            <td class="bank-tx-desc">${d}${de(e.description||"-")}</td>
            <td class="bank-td-amount ${o}">${a}${Re(e.amount)}</td>
            <td><span class="bank-tx-match mt-${s}">${de(i)}</span></td>
        </tr>
    `}function Kt(){const e=document.getElementById("bank-client-badge");if(!e||!ee.currentSession)return;const n=ee.currentSession.client_id,a=document.getElementById("bank-client-badge-dot"),o=document.getElementById("bank-client-badge-name"),s=document.getElementById("bank-client-badge-caret"),i=typeof _userInfo<"u"?_userInfo:null,r=!(i&&i.role==="member");if(n!=null){const d=(window._clientsCache||[]).find(l=>Number(l.id)===Number(n));e.classList.remove("is-empty"),a&&(a.style.background=d&&d.color||"#111111"),o&&(o.textContent=d&&(d.short_name||d.name)||"#"+n)}else e.classList.add("is-empty"),a&&(a.style.background=""),o&&(o.textContent=t("bank-client-none"));r?(e.classList.remove("is-readonly"),e.disabled=!1,s&&(s.style.display="")):(e.classList.add("is-readonly"),e.disabled=!0,s&&(s.style.display="none")),e.style.display=""}function Vo(){if(!ee.currentSession)return;const e=typeof _userInfo<"u"?_userInfo:null;if(!!(e&&e.role==="member"))return;ee.pickerSelected=ee.currentSession.client_id!=null?Number(ee.currentSession.client_id):null,Fn();const a=document.getElementById("bank-client-picker-modal");a&&(a.style.display="")}function Rn(){const e=document.getElementById("bank-client-picker-modal");e&&(e.style.display="none"),ee.pickerSelected=null}function Fn(){const e=document.getElementById("bank-client-picker-list");if(!e)return;const n=(window._clientsCache||[]).filter(o=>o&&(o.is_active===!0||o.is_active===void 0)),a=[];a.push('<div class="bank-client-picker-row is-none'+(ee.pickerSelected==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+de(t("bank-client-picker-none"))+"</span></div>"),n.forEach(o=>{const s=Number(o.id)===Number(ee.pickerSelected)?" is-selected":"";a.push('<div class="bank-client-picker-row'+s+'" data-cid="'+de(o.id)+'"><span class="bank-cp-dot" style="background:'+de(o.color||"#111111")+'"></span><span>'+de(o.short_name||o.name||"#"+o.id)+"</span></div>")}),e.innerHTML=a.join(""),e.querySelectorAll(".bank-client-picker-row").forEach(o=>{o.addEventListener("click",()=>{const s=o.dataset.cid;ee.pickerSelected=s?Number(s):null,Fn()})})}async function Uo(){if(ee.currentSession)try{const e=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(ee.currentSession.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:ee.pickerSelected})});if(!e.ok)throw new Error("client:"+e.status);ee.currentSession.client_id=ee.pickerSelected,Kt(),showToast(t("bank-client-changed"),"success"),Rn();try{await Ke()}catch{}}catch(e){console.warn("[bank-recon] save client failed",e),showToast(t("bank-client-change-failed"),"error")}}async function Ke(){try{const e=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!e.ok)throw new Error("sessions:"+e.status);ee.sessions=await e.json(),ut()}catch(e){console.warn("[bank-recon] loadSessions failed",e),ee.sessions=[],ut()}}function an(){const e=document.getElementById("bank-status-summary");if(!e)return;if(ee.sessions.length===0){e.textContent=t("bank-pill-none");return}let a=0;for(const o of ee.sessions)o.parse_status==="parsed"&&(o.unmatched_count||0)>0&&a++;e.textContent=a>0?t("bank-pill-pending").replace("{n}",a):t("bank-pill-ok")}function ut(){const e=document.getElementById("bank-sessions-list");if(!e)return;let n=ee.sessions||[];if(ee.sessionFilter==="parsed"?n=n.filter(a=>a.parse_status==="parsed"):ee.sessionFilter==="failed"&&(n=n.filter(a=>a.parse_status==="parse_failed")),!ee.sessions||ee.sessions.length===0){e.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(n.length===0){e.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}e.innerHTML=n.map(a=>Go(a)).join(""),e.querySelectorAll(".bank-session-row").forEach(a=>{a.addEventListener("click",o=>{o.target.closest(".bank-session-trash")||Ge(a.dataset.sessionId)})}),e.querySelectorAll(".bank-session-trash").forEach(a=>{a.addEventListener("click",o=>{o.stopPropagation();const s=a.dataset.sessionId,i=a.dataset.sessionName||"";zn(s,i)})})}async function zn(e,n){if(!e)return;const a=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",n||"");if(await showConfirm(a,{danger:!0}))try{const s=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(e),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!s.ok)throw new Error("delete:"+s.status);showToast(t("bank-deleted"),"success"),ee.currentSession&&ee.currentSession.id===e&&(ee.currentSession=null,ee.currentTxs=[],Jt()),await Ke(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(s){console.warn("[bank-recon] delete failed",s),showToast(t("bank-delete-failed"),"error")}}function Go(e){const n=(e.bank_code||"OTHER").toUpperCase(),a=Dn(e.period_start,e.period_end),o=e.account_last4?"···"+e.account_last4:"",s=Ko(e),i=Ue(e.created_at);return`
        <div class="bank-session-row" data-session-id="${de(e.id)}">
            <div class="bank-session-bank bk-${de(n)}">${de(n)}</div>
            <div class="bank-session-info">
                <div class="bank-session-title">${de(e.source_filename||a||"-")}</div>
                <div class="bank-session-meta">${de(a)} · ${de(o)} · ${de(i)}</div>
            </div>
            <div class="bank-session-counts">${s}</div>
            <button class="bank-session-trash" data-session-id="${de(e.id)}" data-session-name="${de(e.source_filename||"")}" title="${de(t("bank-session-delete-tip")||"删除")}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                </svg>
            </button>
            <div class="bank-session-arrow">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
            </div>
        </div>
    `}function Ko(e){if(e.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(e.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const n=e.tx_count||0,a=e.matched_count||0,o=e.unmatched_count||0,s=[`<span class="bank-session-count">${n} ${t("bank-count-tx")}</span>`];return a>0&&s.push(`<span class="bank-session-count cnt-matched">${a} ${t("bank-count-matched")}</span>`),o>0&&s.push(`<span class="bank-session-count cnt-unmatched">${o} ${t("bank-count-unmatched")}</span>`),s.join("")}function Jo(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",qn(),Gt(),Kt()}function Jt(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane"),ee.currentTxForDrawer=null}const Yo=3;function Wo(){return ee.qSeq+=1,"q"+ee.qSeq+"_"+Date.now()}async function Xo(e){const n=Array.from(e.target.files||[]);if(e.target.value="",n.length!==0){for(const a of n){const o={id:Wo(),file:a,name:a.name,size:a.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};a.name.toLowerCase().endsWith(".pdf")?a.size>20*1024*1024&&(o.status="failed",o.error_code="bank_recon.file_too_large"):(o.status="failed",o.error_code="bank_recon.only_pdf"),ee.queue.push(o)}Zo(),Be(),Yt()}}function Zo(){const e=document.getElementById("bank-upload-queue");e&&(e.style.display=""),Ao(),jo()}function Be(){const e=document.getElementById("bank-upload-queue-list"),n=document.getElementById("bank-upload-queue-summary");if(!e)return;if(ee.queue.length===0){e.innerHTML="",n&&(n.textContent="");const r=document.getElementById("bank-upload-queue");r&&(r.style.display="none");return}let a=0,o=0,s=0,i=0;for(const r of ee.queue)r.status==="ok"?a++:r.status==="failed"?o++:r.status==="uploading"||r.status==="parsing"?s++:i++;n&&(n.textContent=t("bank-queue-summary").replace("{ok}",a).replace("{run}",s).replace("{wait}",i).replace("{fail}",o)),e.innerHTML=ee.queue.map(Qo).join(""),e.querySelectorAll("[data-q-act]").forEach(r=>{const d=r.dataset.qAct,l=r.dataset.qId;r.addEventListener("click",()=>{d==="retry"&&es(l),d==="remove"&&ts(l)})})}function Qo(e){const n=(e.size/1024).toFixed(0)+" KB";let a="",o="";if(e.status==="pending")a='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",o='<button data-q-act="remove" data-q-id="'+de(e.id)+'" class="bq-act">×</button>';else if(e.status==="uploading")a='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(e.progress||0)+'%"></div></div>';else if(e.status==="parsing")a='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(e.status==="ok")a='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",e.tx_count||0)+"</span>",o='<button data-q-act="remove" data-q-id="'+de(e.id)+'" class="bq-act">×</button>';else if(e.status==="failed"){const s=Po(e.error_code||"unknown");a='<span class="bq-stat bq-fail" title="'+de(s)+'">'+de(s)+"</span>",o='<button data-q-act="retry" data-q-id="'+de(e.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+de(e.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+de(e.id)+'"><div class="bq-name" title="'+de(e.name)+'">'+de(e.name)+'</div><div class="bq-size">'+n+'</div><div class="bq-status">'+a+'</div><div class="bq-actions">'+o+"</div></div>"}function es(e){const n=ee.queue.find(a=>a.id===e);n&&(n.status="pending",n.error_code=null,n.progress=0,Be(),Yt())}function ts(e){const n=ee.queue.findIndex(o=>o.id===e);if(n<0)return;const a=ee.queue[n];a.status==="uploading"||a.status==="parsing"||(ee.queue.splice(n,1),Be())}function ns(){ee.queue=ee.queue.filter(e=>e.status!=="ok"),Be()}async function Yt(){for(;;){if(ee.queue.filter(a=>a.status==="uploading"||a.status==="parsing").length>=Yo)return;const n=ee.queue.find(a=>a.status==="pending");if(!n){ee.queue.every(a=>a.status==="ok"||a.status==="failed")&&(await Ke(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}as(n).then(()=>Yt())}}async function as(e){e.status="uploading",e.progress=0,Be();try{const n=new FormData;n.append("file",e.file,e.name);const a=await new Promise((s,i)=>{const r=new XMLHttpRequest;r.open("POST","/api/bank-recon/upload"),r.setRequestHeader("Authorization","Bearer "+token),r.upload.onprogress=d=>{d.lengthComputable&&(e.progress=Math.min(99,Math.round(d.loaded/d.total*100)),Be())},r.upload.onload=()=>{e.status="parsing",Be()},r.onload=()=>{r.status>=200&&r.status<300?s({status:r.status,text:r.responseText}):s({status:r.status,text:r.responseText})},r.onerror=()=>i(new Error("network")),r.send(n)});let o={};try{o=JSON.parse(a.text||"{}")}catch{o={}}if(a.status>=400){e.status="failed",e.error_code=o&&o.detail||"unknown",Be();return}if(o.parse_status==="parse_failed"){e.status="failed",e.error_code=o.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",Be();return}e.status="ok",e.tx_count=o.tx_count||0,e.session_id=o.session_id||null,Be()}catch(n){console.warn("[bank-recon] upload failed",n),e.status="failed",e.error_code="network",Be()}}async function Nn(){if(ee.loaded){an();return}ee.loaded=!0,os(),await Ke(),an()}function os(){const e=document.getElementById("bank-file-input");e&&!e._bound&&(e._bound=!0,e.addEventListener("change",Xo));const n=document.getElementById("btn-bank-queue-clear-done");n&&!n._bound&&(n._bound=!0,n.addEventListener("click",ns));const a=document.getElementById("btn-bank-back");a&&!a._bound&&(a._bound=!0,a.addEventListener("click",()=>{ee.currentSession=null,ee.currentTxs=[],Jt()}));const o=document.getElementById("btn-bank-delete");o&&!o._bound&&(o._bound=!0,o.addEventListener("click",zo));const s=document.getElementById("btn-bank-run-match");s&&!s._bound&&(s._bound=!0,s.addEventListener("click",Fo)),document.querySelectorAll(".bank-filter-btn").forEach(m=>{m._bound||(m._bound=!0,m.addEventListener("click",()=>{ee.currentFilter=m.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(c=>{c.classList.toggle("active",c===m)}),Gt()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(m=>{m._bound||(m._bound=!0,m.addEventListener("click",at))});const i=document.getElementById("btn-bank-cand-pane-close");i&&!i._bound&&(i._bound=!0,i.addEventListener("click",at));const r=document.getElementById("btn-bank-cand-ignore");r&&!r._bound&&(r._bound=!0,r.addEventListener("click",nn));const d=document.getElementById("btn-bank-cand-ignore-pane");d&&!d._bound&&(d._bound=!0,d.addEventListener("click",nn));const l=document.getElementById("bank-client-badge");l&&!l._bound&&(l._bound=!0,l.addEventListener("click",Vo)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(m=>{m._bound||(m._bound=!0,m.addEventListener("click",Rn))});const p=document.getElementById("btn-bank-client-picker-save");p&&!p._bound&&(p._bound=!0,p.addEventListener("click",Uo)),document.querySelectorAll(".bank-sessions-chip").forEach(m=>{m._bound||(m._bound=!0,m.addEventListener("click",()=>{ee.sessionFilter=m.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(c=>{c.classList.toggle("active",c===m)}),ut()}))})}window._deleteBankSession=zn;window._loadBankReconPanel=Nn;window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(ut(),ee.currentSession&&(qn(),Gt(),Kt(),!ee.currentTxForDrawer)){const e=document.getElementById("bank-cand-pane-title"),n=document.getElementById("bank-cand-pane-sub");e&&(e.textContent=t("bank-cand-pane-empty-title")),n&&(n.textContent=t("bank-cand-pane-empty-sub"))}Be()}};typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon);window._openBankSession=async function(e){e&&(ee.loaded||await Nn(),await Ge(e))};(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const ss=`
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
    `,is=`
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
    `;we("client-modal-mask",ss);we("wsclient-modal-mask",is);(function(){let e=[],n=null,a="",o="seller";const s={page:0,pageSize:12,keyword:""},i=new Set;let r=[];const d={keyword:""};let l=null;function p(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function m(y,H={}){const P=await fetch(y,{...H,headers:{"Content-Type":"application/json",...p(),...H.headers||{}}});if(!P.ok){const z=await P.json().catch(()=>({}));throw new Error(z.detail||"HTTP "+P.status)}return P.json()}async function c(){try{e=(await m("/api/clients")).clients||[],window._clientsCache=e}catch(y){console.error("loadClientsCache fail",y),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function u(y){o=y==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(z=>z.classList.toggle("active",z.dataset.custTab===o));const H=document.getElementById("cust-pane-seller"),P=document.getElementById("cust-pane-buyer");H&&H.classList.toggle("active",o==="seller"),P&&P.classList.toggle("active",o==="buyer")}function f(){const y=window._userInfo||{},H=String(y.role||"").toLowerCase(),P=String(y.tenant_role||"").toLowerCase();return y.is_super_admin===!0||y.is_owner===!0||H==="owner"||H==="admin"||P==="owner"||P==="admin"}function b(){window._workspaceClientsCache=r,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function B(){try{const y=await m("/api/workspace/clients");r=y&&(y.clients||y.items)||[],window._workspaceClientsCache=r}catch(y){console.error("loadSellerCache fail",y),r=[]}return r}function x(){const y=d.keyword.trim().toLowerCase();return y?r.filter(H=>(H.name||"").toLowerCase().includes(y)||(H.tax_id||"").toLowerCase().includes(y)):r}function v(){const y=document.getElementById("seller-tbody");if(!y)return;const H=f(),P=document.getElementById("btn-seller-new");P&&(P.style.display=H?"":"none");const z=x(),G=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!z.length){y.innerHTML=`<div class="cust-empty">${escapeHtml(t(d.keyword?"cust-no-match":"seller-empty"))}</div>`;return}y.innerHTML=z.map(Q=>{const R=G!=null&&Number(G)===Number(Q.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${Q.id}">${escapeHtml(t("seller-set-current"))}</button>`,U=H?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${Q.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${Q.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${Q.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(Q.name||"#"+Q.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(Q.tax_id||"—")}</div>
                <div class="align-right">${Q.invoice_count||0}</div>
                <div class="cust-row-actions">${R}${U}</div>
            </div>`}).join("")}function h(y){l=y?y.id:null,document.getElementById("wsclient-modal-title").textContent=t(y?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=y&&y.name||"",document.getElementById("wsclient-input-tax").value=y&&y.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=y?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function L(){document.getElementById("wsclient-modal-mask").style.display="none",l=null}async function I(){const y=document.getElementById("wsclient-input-name").value.trim(),H=document.getElementById("wsclient-input-tax").value.trim();if(!y){showToast(t("client-msg-name-required"),"fail");return}try{l?(await m("/api/workspace/clients/"+l,{method:"PATCH",body:JSON.stringify({name:y,tax_id:H})}),showToast(t("client-msg-updated"),"success")):(await m("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:y,tax_id:H||null})}),showToast(t("client-msg-created"),"success")),L(),await B(),v(),b()}catch(P){const z=P&&P.message?P.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+z,"fail")}}async function S(){if(!l)return;const y=r.find(P=>Number(P.id)===Number(l));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",y?y.name:""),{danger:!0}))try{const P=l;await m("/api/workspace/clients/"+P,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(P)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),L(),await B(),v(),b()}catch{showToast(t("client-msg-save-fail"),"fail")}}function C(){const y=s.keyword.trim().toLowerCase();return y?e.filter(H=>(H.name||"").toLowerCase().includes(y)||(H.short_name||"").toLowerCase().includes(y)||(H.tax_id||"").toLowerCase().includes(y)):e}function w(){const y=C(),H=s.pageSize,P=Math.max(0,Math.ceil(y.length/H)-1);s.page>P&&(s.page=P);const z=s.page*H;return{all:y,items:y.slice(z,z+H),start:z,ps:H,total:y.length,maxPage:P}}function g(){const y=document.getElementById("buyer-tbody");if(!y)return;const{items:H,start:P,ps:z,total:G,maxPage:Q}=w();G?y.innerHTML=H.map(J=>{const W=i.has(J.id);return`<div class="cust-row buyer-grid${W?" selected":""}" data-cid="${J.id}">
                    <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${J.id}" ${W?"checked":""}></div>
                    <div style="min-width:0">
                        <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(J.color||"#111")}"></span><span class="cust-name-text">${escapeHtml(J.name)}</span></div>
                        ${J.tax_id?`<div class="cust-cell-sub">${escapeHtml(J.tax_id)}</div>`:""}
                    </div>
                    <div class="align-right">${J.invoice_count||0}</div>
                    <div class="align-right cust-cell-amount">฿${(J.total_amount||0).toLocaleString(void 0,{maximumFractionDigits:0})}</div>
                    <div class="cust-row-actions">
                        <button class="cust-row-btn" data-action="edit" data-cid="${J.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                        <button class="cust-row-btn" data-action="export" data-cid="${J.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t("client-card-export"))}</span></button>
                    </div>
                </div>`}).join(""):y.innerHTML=`<div class="cust-empty">${escapeHtml(t(s.keyword?"cust-no-match":"clients-empty"))}</div>`;const te=document.getElementById("buyer-pager-info");te&&(te.textContent=G?`${P+1}–${Math.min(P+z,G)} / ${G}`:"0");const R=document.getElementById("buyer-prev");R&&(R.disabled=s.page<=0);const U=document.getElementById("buyer-next");U&&(U.disabled=s.page>=Q),E()}function E(){const y=i.size,H=document.getElementById("buyer-batch-bar");H&&(H.style.display=y?"flex":"none");const P=document.getElementById("buyer-batch-count");P&&(P.textContent=t("cust-selected-n").replace("{n}",y));const z=document.getElementById("buyer-check-all");if(z){const{items:G}=w(),Q=G.map(R=>R.id),te=Q.filter(R=>i.has(R)).length;z.checked=Q.length>0&&te===Q.length,z.indeterminate=te>0&&te<Q.length}}function M(){i.clear(),g()}async function $(){const y=Array.from(i);if(!(!y.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",y.length),{danger:!0})))try{await m("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:y})}),showToast(t("client-msg-deleted"),"success"),i.clear(),await c(),g(),V(),k()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const y=document.getElementById("seller-tbody");y&&(y.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const H=document.getElementById("buyer-tbody");H&&(H.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([B(),c()]),v(),g()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&v()});function j(y){n=y?y.id:null;const H=!!y;document.getElementById("client-modal-title").textContent=t(H?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=y&&y.name||"",document.getElementById("client-input-short").value=y&&y.short_name||"",document.getElementById("client-input-tax").value=y&&y.tax_id||"",document.getElementById("client-input-address").value=y&&y.address||"",document.getElementById("client-input-contact").value=y&&y.contact_person||"",document.getElementById("client-input-phone").value=y&&y.contact_phone||"",document.getElementById("client-input-email").value=y&&y.contact_email||"",document.getElementById("client-input-notes").value=y&&y.notes||"";const P=y&&y.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(z=>{z.classList.toggle("active",z.dataset.color===P)}),document.getElementById("client-modal-delete").style.display=H?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function _(){document.getElementById("client-modal-mask").style.display="none",n=null}function A(){const y=document.querySelector("#client-color-picker .color-swatch.active");return y?y.dataset.color:"#111111"}async function q(){const y=document.getElementById("client-input-name").value.trim();if(!y){showToast(t("client-msg-name-required"),"fail");return}const H={name:y,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:A()};try{n?(await m(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify(H)}),showToast(t("client-msg-updated"),"success")):(await m("/api/clients",{method:"POST",body:JSON.stringify(H)}),showToast(t("client-msg-created"),"success")),_(),await c(),currentRoute==="clients"&&g(),V(),k()}catch(P){console.error("saveClient fail",P);const z=P&&P.message?P.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+z,"fail")}}async function F(){if(!n)return;const y=e.find(z=>z.id===n);if(!y)return;const H=t("client-delete-confirm").replace("{name}",y.name);if(await showConfirm(H,{danger:!0}))try{await m(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),_(),await c(),currentRoute==="clients"&&g(),V(),k()}catch(z){console.error(z),showToast(t("client-msg-save-fail"),"fail")}}async function D(y){const H=e.find(P=>P.id===y);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(y,H?H.name:"");return}try{const P=localStorage.getItem("mrpilot_token"),z=await fetch(`/api/clients/${y}/export?month=all`,{headers:{Authorization:"Bearer "+P}});if(!z.ok){let U="HTTP "+z.status;try{const J=await z.json();J&&J.detail&&(U=J.detail)}catch{}throw new Error(U)}const G=await z.blob();if(G.size<200){showToast(t("client-export-month-empty"),"info");return}const Q=H&&H.name?H.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",te=URL.createObjectURL(G),R=document.createElement("a");R.href=te,R.download=`${Q}_export.csv`,R.click(),URL.revokeObjectURL(te)}catch(P){console.error("exportClient fail",P),showToast(t("client-msg-save-fail")+" · "+(P.message||""),"fail")}}function V(){const y=document.getElementById("drawer-client-select");if(!y)return;const H=y.value;y.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),y.value=H||""}window.bindDrawerClient=function(y,H){const P=document.getElementById("drawer-client-select");if(!P)return;if(V(),P.value=H?String(H):"",!y){P.onchange=null;const G=document.getElementById("drawer-client-add");G&&(G.onclick=()=>j(null));return}P.onchange=async()=>{const G=P.value?parseInt(P.value,10):null;try{await m(`/api/history/${y}/assign_client`,{method:"POST",body:JSON.stringify({client_id:G})}),showToast(t("client-msg-updated"),"success");const Q=_results[_drawerIdx];Q&&(Q.client_id=G),await c()}catch(Q){console.error(Q),showToast(t("client-msg-save-fail"),"fail"),P.value=H?String(H):""}};const z=document.getElementById("drawer-client-add");z&&(z.onclick=()=>j(null))};let Y={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const y=document.getElementById("drawer-cat-datalist"),H=Date.now();if(H-Y.fetched<300*1e3){y&&(y.innerHTML=Y.items.map(z=>`<option value="${escapeHtml(z)}">`).join("")),T(Y.supplier_count);return}const P=await m("/api/categories",{method:"GET"});Y.fetched=H,Y.items=P&&P.categories||[],Y.supplier_count=P&&P.supplier_count||0,y&&(y.innerHTML=Y.items.map(z=>`<option value="${escapeHtml(z)}">`).join("")),T(Y.supplier_count)}catch(y){console.warn("fillCategoryDatalist failed",y)}};function T(y){const H=document.getElementById("drawer-cat-learned-tag");H&&y>0&&(H.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",y))}function k(){const y=document.getElementById("history-client-filter");if(!y)return;const H=y.value;y.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),y.value=H||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const y=document.querySelector(".cust-tab-bar");y&&y.addEventListener("click",re=>{const le=re.target.closest("[data-cust-tab]");le&&u(le.dataset.custTab)});const H=document.getElementById("btn-buyer-new");H&&H.addEventListener("click",()=>j(null));const P=document.getElementById("buyer-tbody");P&&P.addEventListener("click",re=>{const le=re.target.closest(".buyer-row-check");if(le){const he=parseInt(le.dataset.cid,10);le.checked?i.add(he):i.delete(he);const Le=le.closest(".cust-row");Le&&Le.classList.toggle("selected",le.checked),E();return}const ye=re.target.closest(".cust-row-btn");if(ye){re.stopPropagation();const he=parseInt(ye.dataset.cid,10);if(ye.dataset.action==="edit"){const Le=e.find(_t=>_t.id===he);Le&&j(Le)}else ye.dataset.action==="export"&&D(he);return}const be=re.target.closest(".cust-row");if(be&&!re.target.closest(".cust-cell-check")){const he=e.find(Le=>Le.id===parseInt(be.dataset.cid,10));he&&j(he)}});const z=document.getElementById("buyer-check-all");z&&z.addEventListener("change",()=>{const{items:re}=w();re.forEach(le=>{z.checked?i.add(le.id):i.delete(le.id)}),g()});const G=document.getElementById("buyer-batch-cancel");G&&G.addEventListener("click",M);const Q=document.getElementById("buyer-batch-delete");Q&&Q.addEventListener("click",$);const te=document.getElementById("buyer-prev");te&&te.addEventListener("click",()=>{s.page>0&&(s.page--,g())});const R=document.getElementById("buyer-next");R&&R.addEventListener("click",()=>{s.page++,g()});const U=document.getElementById("buyer-search");if(U){let re;U.addEventListener("input",()=>{clearTimeout(re),re=setTimeout(()=>{s.keyword=U.value,s.page=0;const le=document.getElementById("buyer-search-clear");le&&(le.style.display=U.value?"":"none"),g()},200)})}const J=document.getElementById("buyer-search-clear");J&&J.addEventListener("click",()=>{const re=document.getElementById("buyer-search");re&&(re.value=""),s.keyword="",s.page=0,J.style.display="none",g()});const W=document.getElementById("btn-seller-new");W&&W.addEventListener("click",()=>h(null));const X=document.getElementById("seller-tbody");X&&X.addEventListener("click",re=>{const le=re.target.closest("[data-saction]");if(!le)return;re.stopPropagation();const ye=parseInt(le.dataset.wid,10),be=le.dataset.saction,he=r.find(Le=>Number(Le.id)===ye);be==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(ye),v(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",he?he.name:""),"success")):be==="edit"?he&&h(he):be==="archive"&&(l=ye,S())});const se=document.getElementById("seller-search");if(se){let re;se.addEventListener("input",()=>{clearTimeout(re),re=setTimeout(()=>{d.keyword=se.value;const le=document.getElementById("seller-search-clear");le&&(le.style.display=se.value?"":"none"),v()},200)})}const N=document.getElementById("seller-search-clear");N&&N.addEventListener("click",()=>{const re=document.getElementById("seller-search");re&&(re.value=""),d.keyword="",N.style.display="none",v()});const K=document.getElementById("wsclient-modal-close");K&&K.addEventListener("click",L);const O=document.getElementById("wsclient-modal-cancel");O&&O.addEventListener("click",L);const ae=document.getElementById("wsclient-modal-save");ae&&ae.addEventListener("click",I);const Z=document.getElementById("wsclient-modal-archive");Z&&Z.addEventListener("click",S);const ie=document.getElementById("wsclient-modal-mask");ie&&ie.addEventListener("click",re=>{re.target===ie&&L()});const ce=document.getElementById("client-modal-close");ce&&ce.addEventListener("click",_);const fe=document.getElementById("client-modal-cancel");fe&&fe.addEventListener("click",_);const ve=document.getElementById("client-modal-save");ve&&ve.addEventListener("click",q);const ge=document.getElementById("client-modal-delete");ge&&ge.addEventListener("click",F);const ke=document.getElementById("client-modal-mask");ke&&ke.addEventListener("click",re=>{re.target===ke&&_()});const Se=document.getElementById("client-color-picker");Se&&Se.addEventListener("click",re=>{const le=re.target.closest(".color-swatch");le&&(Se.querySelectorAll(".color-swatch").forEach(ye=>ye.classList.remove("active")),le.classList.add("active"))});const _e=document.getElementById("history-client-filter");_e&&_e.addEventListener("change",()=>{a=_e.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>c(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function n(T,k){let y=t(T)||T;if(k)for(const H in k)y=y.replace(new RegExp("\\{"+H+"\\}","g"),String(k[H]));return y}async function a(){try{const T=e.currentClient||"",k="/api/exceptions/stats?status=pending"+(T?"&client_id="+encodeURIComponent(T):""),y=await fetch(k,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!y.ok)return;const H=await y.json(),P=document.getElementById("nav-exc-badge");if(!P)return;const z=parseInt(H.pending||0,10);z>0?(P.textContent=z>99?"99+":String(z),P.style.display=""):P.style.display="none"}catch{}}function o(T){return T==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 1.5L1 12.5h12L7 1.5z"/>
                <line x1="7" y1="6" x2="7" y2="9"/>
                <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
            </svg>`:T==="medium"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="7" cy="7" r="5.5"/>
                <line x1="7" y1="4" x2="7" y2="7.5"/>
                <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
            </svg>`:`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="4.5" y1="7" x2="9.5" y2="7"/>
        </svg>`}function s(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function i(T){if(T==null)return"—";const k=parseFloat(T);return isNaN(k)?"—":"฿ "+k.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function r(T){return T?T.slice(0,10):"—"}function d(T){document.getElementById("exc-kpi-pending").textContent=T.pending||0,document.getElementById("exc-kpi-high").textContent=T.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=T.resolved||0,document.getElementById("exc-kpi-learned").textContent=T.learned_rules||0;const k=document.getElementById("exc-status-tab-count-pending"),y=document.getElementById("exc-status-tab-count-resolved"),H=document.getElementById("exc-status-tab-count-ignored");k&&(k.textContent=T.pending||0),y&&(y.textContent=T.resolved||0),H&&(H.textContent=T.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(z=>{z.classList.toggle("active",z.dataset.status===(e.currentStatus||"pending"))})}function l(T){const k=document.getElementById("exc-chips");if(!k)return;const y=T.by_rule||{},H=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let z=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${T.pending||0}</span>
        </button>`;for(const G of H){const Q=y[G]||0;if(Q===0&&e.currentRule!==G)continue;const te=e.currentRule===G;z+=`<button class="exc-chip ${te?"active":""}" data-rule="${escapeHtml(G)}">
                <span>${escapeHtml(t("exc-chip-"+G))}</span>
                <span class="exc-chip-count">${Q}</span>
            </button>`}k.innerHTML=z,k.querySelectorAll(".exc-chip").forEach(G=>{G.addEventListener("click",()=>{const Q=G.dataset.rule||null;e.currentRule=Q,b()})})}function p(T){const k=document.getElementById("exc-list");if(!k)return;if(!T||T.length===0){k.innerHTML=`<div class="exc-empty">
                ${s()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,c();return}const y='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',H=(e.currentStatus||"pending")==="pending";k.innerHTML=T.map(P=>{const z=P.severity||"medium",G=t("exc-rule-"+P.rule_code)||P.rule_code,Q=P.seller_name&&P.seller_name.trim()?P.seller_name:t("exc-no-seller"),te=P.filename||"—",R=r(P.invoice_date||P.created_at),U=P.status==="pending",J=e.selectedIds.has(P.id),W=H&&U;return`
                <div class="exc-row sev-${escapeHtml(z)} ${J?"selected":""}" data-exc-id="${escapeHtml(String(P.id))}">
                    <div class="exc-row-check ${J?"checked":""}" data-check-id="${escapeHtml(String(P.id))}" ${W?"":'style="visibility:hidden;"'}>${y}</div>
                    <div class="exc-row-sev">${o(z)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(Q)} · ${escapeHtml(te)}</div>
                        <div class="exc-row-meta">
                            ${P.invoice_no?`<span><b>${escapeHtml(P.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(R)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(z)}">${escapeHtml(G)}</div>
                    <div class="exc-row-amount">${escapeHtml(i(P.total_amount))}</div>
                </div>
            `}).join(""),k.querySelectorAll(".exc-row").forEach(P=>{P.addEventListener("click",z=>{if(z.target.closest(".exc-row-check"))return;const G=P.dataset.excId;G&&I(parseInt(G,10))})}),k.querySelectorAll(".exc-row-check").forEach(P=>{P.addEventListener("click",z=>{z.stopPropagation();const G=parseInt(P.dataset.checkId,10);G&&(e.selectedIds.has(G)?(e.selectedIds.delete(G),P.classList.remove("checked"),P.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(G),P.classList.add("checked"),P.closest(".exc-row").classList.add("selected")),m())})}),m(),c()}function m(){const T=document.getElementById("exc-batch-bar"),k=document.getElementById("exc-batch-count");if(!T||!k)return;const y=e.selectedIds.size;y===0?T.style.display="none":(T.style.display="",k.textContent=n("exc-batch-count",{n:y}))}function c(){const T=document.getElementById("exc-list-foot"),k=document.getElementById("exc-list-count"),y=document.getElementById("exc-loadmore");if(!T||!k||!y)return;const H=e.listCache.length;if(H===0){T.style.display="none";return}T.style.display="";let P=H;const z=e.statsCache;z&&(e.currentRule?P=(z.by_rule||{})[e.currentRule]||H:P=z.pending||H),e.total=P,k.textContent=n("exc-list-count",{shown:H,total:P});const G=H<P&&H<500;y.style.display=G?"":"none"}async function u(){try{if(navigator.onLine===!1)throw new Error("offline");const T=e.currentClient||"",k=e.currentStatus||"pending",y=new URLSearchParams;y.set("status",k),T&&y.set("client_id",T);const H="/api/exceptions/stats?"+y.toString(),P=await fetch(H,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!P.ok)throw new Error("http "+P.status);const z=await P.json();return e.statsCache=z,d(z),l(z),z}catch(T){return console.warn("loadExceptionsStats fail",T),null}}function f(T){const k=document.getElementById("exc-list");if(!k)return;const y=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,H=T?t("exc-offline"):t("exc-error-retry-title"),P=T?"":t("exc-error-retry-desc");k.innerHTML=`
            <div class="exc-error">
                ${y}
                <div class="exc-error-msg">${escapeHtml(H)}${P?" · "+escapeHtml(P):""}</div>
                <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const z=document.getElementById("exc-retry-btn");z&&z.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function b(T){T=T||{};const k=!!T.append,y=document.getElementById("exc-list");!k&&y&&e.listCache.length===0&&(y.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const H=new URLSearchParams;H.set("status",e.currentStatus||"pending"),e.currentRule&&H.set("rule_code",e.currentRule),e.currentClient&&H.set("client_id",e.currentClient);const P=k?e.listCache.length:0;H.set("limit",String(e.pageSize)),H.set("offset",String(P));try{if(navigator.onLine===!1)throw new Error("offline");const z=await fetch("/api/exceptions/list?"+H.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!z.ok)throw new Error("http "+z.status);const Q=(await z.json()).items||[];k?e.listCache=e.listCache.concat(Q):(e.listCache=Q,e.selectedIds.clear()),e.loadFailed=!1,p(e.listCache),e.statsCache&&l(e.statsCache)}catch(z){console.warn("loadExceptionsList fail",z),e.loadFailed=!0;const G=navigator.onLine===!1||String(z.message||"").includes("offline");k?showToast(t("exc-toast-load-fail"),"error"):(f(G),showToast(G?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function B(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await b({append:!0})}finally{e.loading=!1}}}function x(){const T=document.getElementById("exc-client-filter");if(!T)return;const k=window._clientsCache||[],y=e.currentClient||"",H=typeof t=="function"?t("history-client-all"):"全部客户";T.innerHTML=`<option value="">${escapeHtml(H)}</option>`+k.map(P=>`<option value="${P.id}">${escapeHtml(P.name)}</option>`).join(""),T.value=y}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{x(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await u(),await b()}finally{e.loading=!1}}},window.refreshExcBadge=a,window._refreshExcClientFilter=x,window._excState=e,window._rerenderExceptions=function(){try{x()}catch{}e.statsCache&&(d(e.statsCache),l(e.statsCache)),e.listCache&&e.listCache.length&&p(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}v.openExcId&&M()};let v={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function h(){if(v.pdfUrl){try{URL.revokeObjectURL(v.pdfUrl)}catch{}v.pdfUrl=null}v.pdfStatus="idle"}async function L(T,k){v.pdfStatus="loading",M();try{const y=await fetch("/api/history/"+encodeURIComponent(T)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(v.openExcId!==k)return;if(y.status===404){v.pdfStatus="empty",M();return}if(!y.ok)throw new Error("http "+y.status);const H=await y.blob();if(v.openExcId!==k)return;h(),v.pdfUrl=URL.createObjectURL(H),v.pdfStatus="ready",M()}catch(y){if(v.openExcId!==k)return;console.warn("loadDrawerPdf fail",y),v.pdfStatus="error",M()}}function I(T){const k=(e.listCache||[]).find(y=>y.id===T);if(!k){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,h(),v.editing=!1,v.editFields=null,v.openExcId=T,v.excRow=k,v.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),M(),C(k.history_id),L(k.history_id,T)}function S(){h(),v.editing=!1,v.editFields=null,v.openExcId=null,v.excRow=null,v.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const T=e.listScrollY||0;T>0&&requestAnimationFrame(()=>window.scrollTo(0,T))}async function C(T){try{const k=await fetch("/api/history/"+encodeURIComponent(T),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!k.ok)throw new Error("http "+k.status);v.history=await k.json()}catch(k){console.warn("loadHistoryDetail fail",k),v.history={_err:!0}}v.excRow&&M()}function w(T){if(!T||!T.pages)return{};const k=T.pages,y=k.find(H=>!H.is_duplicate&&!H.is_copy)||k[0];return y&&y.fields||{}}function g(T){if(T==null)return"—";const k=typeof T=="number"?T:parseFloat(String(T).replace(/,/g,""));return isNaN(k)?escapeHtml(String(T)):"฿ "+k.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function E(T,k){if(k=k||{},T==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(g(k.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(g(k.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(g(k.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(g(k.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(g(k.diff))}</span></div>
            `;if(T==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(k.tax_id_normalized||k.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(k.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(T==="duplicate"){const y=k.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(k.match_filename||"—")}</span></div>
                ${k.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(k.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(y)}</span></div>
            `}return T==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(k.confidence||"—")}</span></div>
            `:T==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(k))}</span></div>`}function M(){const T=v.excRow;if(!T)return;const k=T.seller_name&&T.seller_name.trim()?T.seller_name:t("exc-no-seller"),y=T.filename||"—";document.getElementById("exc-drawer-title").textContent=y;const H="exc-status-"+(T.status||"pending"),P=t(H)||T.status,z="s-"+(T.status||"pending"),G=(T.invoice_date||T.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(k)}</span>
            ${T.invoice_no?`<span>· ${escapeHtml(T.invoice_no)}</span>`:""}
            ${G?`<span>· ${escapeHtml(G)}</span>`:""}
            <span class="exc-status-chip ${z}">${escapeHtml(P)}</span>
        `;const Q=T.severity||"medium",te=t("exc-rule-"+T.rule_code)||T.rule_code,R=E(T.rule_code,T.detail||{}),U=w(v.history),J=v.history===null,W=v.history&&v.history._err,X=new Set;T.rule_code==="math_mismatch"?(X.add("subtotal"),X.add("vat"),X.add("total_amount")):T.rule_code==="tax_id_format_invalid"?X.add("seller_tax"):T.rule_code==="amount_missing"&&(X.add("total_amount"),X.add("invoice_number"));const se=!!v.editing,N=v.editFields||{},K=(re,le,ye)=>{if(J)return`<div class="exc-field-row"><label>${escapeHtml(t(le))}</label><span class="val empty">…</span></div>`;const be=se?N[re]!==void 0?N[re]:U[re]!==void 0&&U[re]!==null?U[re]:"":U[re],he=X.has(re)?"flagged":"";if(se){const aa=ye?"number":"text",oa=ye?' step="0.01" inputmode="decimal"':"",sa=be==null?"":String(be).replace(/"/g,"&quot;");return`<div class="exc-field-row ${he} editing">
                    <label>${escapeHtml(t(le))}</label>
                    <input class="exc-field-input" type="${aa}"${oa} data-edit-key="${escapeHtml(re)}" value="${sa}">
                </div>`}const Le=ye?g(be):be||"",_t=be==null||be===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(Le)}</span>`;return`<div class="exc-field-row ${he}"><label>${escapeHtml(t(le))}</label>${_t}</div>`};let O="";W?O=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:O=`
                <div class="exc-fields">
                    ${K("invoice_number","exc-fld-invoice-no",!1)}
                    ${K("date","exc-fld-date",!1)}
                    ${K("seller_name","exc-fld-seller",!1)}
                    ${K("seller_tax","exc-fld-seller-tax",!1)}
                    ${K("buyer_name","exc-fld-buyer",!1)}
                    ${K("buyer_tax","exc-fld-buyer-tax",!1)}
                    ${K("subtotal","exc-fld-subtotal",!0)}
                    ${K("vat","exc-fld-vat",!0)}
                    ${K("total_amount","exc-fld-total",!0)}
                </div>
            `;const ae=(()=>{if(v.pdfStatus==="loading"||v.pdfStatus==="idle")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M18 4v8a14 14 0 1014 14"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                    </div>
                `;if(v.pdfStatus==="empty")return`
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
                `;if(v.pdfStatus==="error")return`
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
                `;const re=v.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(y)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${re}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${re}" download="${escapeHtml(y)}" title="${escapeHtml(t("exc-pdf-download"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                            </svg>
                        </a>
                    </div>
                </div>
                <iframe class="exc-pdf-frame" src="${re}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
            `})();document.getElementById("exc-drawer-body").innerHTML=`
            <div class="exc-pdf-pane">${ae}</div>
            <div class="exc-fields-pane">
                <div class="exc-section">
                    <div class="exc-section-title">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="7" cy="7" r="5.5"/><line x1="7" y1="4" x2="7" y2="7.5"/>
                            <circle cx="7" cy="9.6" r="0.5" fill="currentColor"/>
                        </svg>
                        <span>${escapeHtml(t("exc-sect-why"))}</span>
                    </div>
                    <div class="exc-why sev-${escapeHtml(Q)}">
                        <div class="exc-why-rule">${escapeHtml(te)}</div>
                        <div class="exc-why-detail">${R}</div>
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
                        ${T.status==="pending"&&!J&&!W?se?`
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
                    ${O}
                </div>
            </div>
        `;const Z=document.getElementById("exc-fld-edit");Z&&Z.addEventListener("click",()=>{v.editing=!0,v.editFields={...w(v.history)},M()});const ie=document.getElementById("exc-fld-cancel");ie&&ie.addEventListener("click",()=>{v.editing=!1,v.editFields=null,M()});const ce=document.getElementById("exc-fld-save");ce&&ce.addEventListener("click",()=>$()),document.querySelectorAll(".exc-field-input").forEach(re=>{re.addEventListener("input",()=>{v.editFields||(v.editFields={}),v.editFields[re.dataset.editKey]=re.value})});const ve=document.getElementById("exc-pdf-retry");ve&&v.openExcId&&ve.addEventListener("click",()=>{v.excRow&&L(v.excRow.history_id,v.openExcId)});const ge=T.status==="pending",ke=!!(T.seller_name&&T.seller_name.trim()),Se=document.getElementById("exc-btn-resolve"),_e=document.getElementById("exc-btn-ignore");Se.disabled=!ge,_e.disabled=!ge||!ke,_e.title=ke?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function $(){if(!v.openExcId||!v.history||!v.history.pages||v.loading)return;v.loading=!0;const T=showToast(t("exc-fld-saving"),"loading",0);try{const k=JSON.parse(JSON.stringify(v.history.pages||[]));let y=k.findIndex(te=>!te.is_duplicate&&!te.is_copy);y<0&&(y=0),k[y]||(k[y]={fields:{}});const H=k[y].fields||{},P=v.editFields||{},z=new Set(["subtotal","vat","total_amount"]),G={...H};for(const te in P){let R=P[te];if((R===""||R===void 0)&&(R=null),z.has(te)&&R!==null){const U=parseFloat(R);R=isNaN(U)?null:U}G[te]=R}k[y].fields=G;const Q=await fetch("/api/history/"+encodeURIComponent(v.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:k})});if(!Q.ok)throw new Error("http "+Q.status);T(),showToast(t("exc-fld-save-ok"),"success"),S(),await u(),await b(),a()}catch(k){T(),console.warn("save fields fail",k),showToast(t("exc-fld-save-fail"),"error")}finally{v.loading=!1}}async function j(){if(!(!v.openExcId||v.loading)){v.loading=!0;try{const T=await fetch("/api/exceptions/"+v.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!T.ok)throw new Error("http "+T.status);showToast(t("exc-toast-resolved"),"success"),S(),await u(),await b(),a()}catch(T){console.warn("resolve fail",T),showToast(t("exc-toast-action-fail"),"error")}finally{v.loading=!1}}}async function _(){if(!(!v.openExcId||v.loading)){v.loading=!0;try{const T=await fetch("/api/exceptions/"+v.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!T.ok)throw new Error("http "+T.status);showToast(t("exc-toast-ignored"),"success"),S(),await u(),await b(),a()}catch(T){console.warn("ignore fail",T),showToast(t("exc-toast-action-fail"),"error")}finally{v.loading=!1}}}let A=!1;async function q(){if(A)return;const T=Array.from(e.selectedIds);if(T.length===0||!await showConfirm(n("exc-batch-confirm-resolve",{n:T.length})))return;A=!0;const y=showToast(n("exc-batch-count",{n:T.length})+" …","loading",0);try{const H=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:T,action:"resolve"})});if(!H.ok)throw new Error("http "+H.status);const P=await H.json();y(),showToast(n("exc-toast-batch-resolved",{n:P.processed||0}),"success"),e.selectedIds.clear(),await u(),await b(),a()}catch(H){y(),console.warn("batch resolve fail",H),showToast(t("exc-toast-batch-fail"),"error")}finally{A=!1}}async function F(){if(A)return;const T=Array.from(e.selectedIds);if(T.length===0||!await showConfirm(n("exc-batch-confirm-ignore",{n:T.length}),{danger:!1}))return;A=!0;const y=showToast(n("exc-batch-count",{n:T.length})+" …","loading",0);try{const H=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:T,action:"ignore"})});if(!H.ok)throw new Error("http "+H.status);const P=await H.json();y(),showToast(n("exc-toast-batch-ignored",{n:P.processed||0,wl:P.whitelist_added||0}),"success"),e.selectedIds.clear(),await u(),await b(),a()}catch(H){y(),console.warn("batch ignore fail",H),showToast(t("exc-toast-batch-fail"),"error")}finally{A=!1}}function D(){e.selectedIds.clear(),p(e.listCache)}document.addEventListener("click",T=>{T.target.closest("#exc-drawer-close")&&S(),T.target.closest("#exc-drawer-mask")&&S(),T.target.closest("#exc-btn-resolve")&&j(),T.target.closest("#exc-btn-ignore")&&_(),T.target.closest("#exc-batch-resolve")&&q(),T.target.closest("#exc-batch-ignore")&&F(),T.target.closest("#exc-batch-clear")&&D(),T.target.closest("#exc-loadmore")&&B()}),document.addEventListener("keydown",T=>{T.key==="Escape"&&v.openExcId&&S()}),document.addEventListener("click",T=>{T.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a())}),document.addEventListener("change",T=>{if(!T.target.closest("#exc-client-filter"))return;const k=T.target;e.currentClient=k.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a()}),document.addEventListener("click",T=>{const k=T.target.closest("#exc-status-tabs .exc-status-tab");if(!k)return;const y=k.dataset.status||"pending";y!==e.currentStatus&&(e.currentStatus=y,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(a,1500),setInterval(a,6e4);function V(T){if(!T)return"—";try{const k=new Date(T),y=H=>String(H).padStart(2,"0");return`${k.getFullYear()}-${y(k.getMonth()+1)}-${y(k.getDate())} ${y(k.getHours())}:${y(k.getMinutes())}`}catch{return T.slice(0,16).replace("T"," ")}}async function Y(){const T=document.getElementById("learned-list");if(T){T.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const k=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!k.ok)throw new Error("http "+k.status);const H=(await k.json()).items||[];if(H.length===0){T.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const P=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;T.innerHTML=H.map(z=>{const G=t("exc-rule-"+z.rule_code)||z.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(z.id))}">
                        <div class="learned-seller" title="${escapeHtml(z.seller_name)}">${escapeHtml(z.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(G)}</div>
                        <div class="learned-date">${escapeHtml(V(z.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(z.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${P}</button>
                    </div>
                `}).join("")}catch(k){console.warn("loadLearnedRules fail",k),T.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=Y,document.addEventListener("click",async T=>{const k=T.target.closest("[data-del-wl]");if(!k)return;const y=parseInt(k.dataset.delWl,10);if(!y)return;const H=k.closest(".learned-row"),P=H&&H.querySelector(".learned-seller"),z=P?P.textContent.trim():"",G=t("set-learned-del-confirm").replace("{seller}",z);if(await showConfirm(G,{danger:!0}))try{const te=await fetch("/api/exception-whitelist/"+y,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!te.ok)throw new Error("http "+te.status);showToast(t("set-learned-del-ok"),"success"),Y(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(te){console.warn("delete whitelist fail",te),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",adapter:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(c){const u=typeof currentLang=="string"&&currentLang||window._currentLang||"th",f=c.error_friendly&&c.error_friendly[u];if(f)return f;if(typeof humanizeError=="function"&&c.error_msg)try{return humanizeError(c.error_msg)}catch{}return t("erp-exc-reason-"+(c.category||"other"))}function s(){const c=document.getElementById("erp-exc-batch");if(!c)return;const u=e.selected.size;c.hidden=u===0;const f=c.querySelector(".erp-exc-batch-count");f&&(f.textContent=String(u))}function i(){const c=document.getElementById("erp-exc-block");if(!c)return;const u=e;if(!(u.total>0||!!u.q||!!u.cat)){c.hidden=!0,c.innerHTML="";return}c.hidden=!1;const b=u.categories||{},B=Object.keys(b).reduce((D,V)=>D+b[V],0);let x=`<button class="erp-exc-chip ${u.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${B}</span></button>`;Object.keys(b).forEach(D=>{x+=`<button class="erp-exc-chip ${u.cat===D?"active":""}" data-erpexc-cat="${escapeHtml(D)}"><span>${escapeHtml(t("erp-exc-cat-"+D))}</span><span class="erp-exc-chip-count">${b[D]}</span></button>`});const v=u.items||[],h=v.length>0&&v.every(D=>u.selected.has(D.id)),L=v.map(D=>{const V=D.state==="needs_action"?"needs":D.state==="retrying"?"retry":"fail",Y=t("erp-exc-state-"+(D.state||"failed")),T=o(D),k=u.selected.has(D.id)?"checked":"",y=D.push_type==="id_card",H=y?`<span class="erp-exc-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span> `:"",P=y?`<span class="ex-inv" title="${escapeHtml(t("erp-log-col-booking"))}">${H}${escapeHtml(D.invoice_no||"—")}</span>`:`<span class="ex-inv" title="${escapeHtml(D.invoice_no||"")}">${escapeHtml(D.invoice_no||"—")}</span>`,z=y?`<span class="ex-seller" title="${escapeHtml(t("erp-log-col-customer"))}">${escapeHtml(D.seller_name||"—")}</span>`:`<span class="ex-seller" title="${escapeHtml(D.seller_name||"")}">${escapeHtml(D.seller_name||"—")}</span>`,G=y?`<span class="ex-buyer" title="${escapeHtml(t("erp-log-col-idcard"))}">${D.id_card_tail?"••••"+escapeHtml(D.id_card_tail):"—"}</span>`:`<span class="ex-buyer" title="${escapeHtml(D.ocr_buyer_name||"")}">${escapeHtml(D.ocr_buyer_name||"—")}</span>`;return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(D.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(D.id)}" ${k}></span>
                ${P}
                ${z}
                ${G}
                <span class="ex-state"><span class="erp-exc-state ${V}">${escapeHtml(Y)}</span></span>
                <span class="ex-reason" title="${escapeHtml(T)}">${escapeHtml(T)}${D.error_code?` <span class="erp-exc-code">${escapeHtml(D.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(D.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),I=v.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",S=v.length<u.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${v.length}/${u.total})</button>`:u.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:v.length,total:u.total}))}</div>`:"",C=u.adapter==="mrerp_dms",w=Array.isArray(window._erpEndpoints)?window._erpEndpoints:[],g=new Set;let E=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`;w.forEach(D=>{const V=(D&&D.adapter||"").toLowerCase();!V||g.has(V)||(g.add(V),E+=`<option value="${escapeHtml(V)}"${V===u.adapter?" selected":""}>${escapeHtml(D&&D.name||V)}</option>`)});const M=C?t("erp-log-col-booking"):t("erp-exc-f-invoice"),$=C?t("erp-log-col-customer"):t("erp-exc-f-seller"),j=C?t("erp-log-col-idcard"):t("erp-exc-f-buyer");c.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${E}</select>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(u.q)}">
            </div>
            <div class="erp-exc-chips">${x}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${u.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${u.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${h?"checked":""}></span>
                    <span class="ex-inv">${escapeHtml(M)}</span>
                    <span class="ex-seller">${escapeHtml($)}</span>
                    <span class="ex-buyer">${escapeHtml(j)}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${L}${I}
            </div>
            <div class="erp-exc-foot">${S}</div>`;const _=document.getElementById("erp-exc-search");if(_){if(u.focusSearch){_.focus();try{_.setSelectionRange(u.searchCaret,u.searchCaret)}catch{}}_.addEventListener("input",()=>{u.q=_.value,u.focusSearch=!0,u.searchCaret=_.selectionStart||_.value.length,clearTimeout(n),n=setTimeout(()=>l(!1),350)}),_.addEventListener("blur",()=>{u.focusSearch=!1})}c.querySelectorAll(".erp-exc-chip").forEach(D=>{D.addEventListener("click",()=>{u.cat=D.dataset.erpexcCat||"",l(!1)})});const A=document.getElementById("erp-exc-erp-select");A&&A.addEventListener("change",()=>{u.adapter=A.value||"",l(!1)}),c.querySelectorAll("[data-erpexc-retry]").forEach(D=>{D.addEventListener("click",V=>{V.stopPropagation(),r(D.dataset.erpexcRetry,D)})}),c.querySelectorAll(".erp-exc-cb").forEach(D=>{D.addEventListener("change",()=>{const V=D.dataset.erpexcCb;D.checked?u.selected.add(V):u.selected.delete(V);const Y=document.getElementById("erp-exc-cb-all");Y&&(Y.checked=v.length>0&&v.every(T=>u.selected.has(T.id))),s()})});const q=document.getElementById("erp-exc-cb-all");q&&q.addEventListener("change",()=>{v.forEach(D=>{q.checked?u.selected.add(D.id):u.selected.delete(D.id)}),c.querySelectorAll(".erp-exc-cb").forEach(D=>{D.checked=q.checked}),s()}),c.querySelectorAll("[data-erpexc-batch]").forEach(D=>{D.addEventListener("click",()=>d(D.dataset.erpexcBatch))});const F=document.getElementById("erp-exc-more");F&&F.addEventListener("click",()=>l(!0)),c.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(D=>{D.addEventListener("click",V=>{V.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(D.dataset.erpexcId)})})}async function r(c,u){if(c){u&&(u.disabled=!0,u.textContent=t("erp-exc-retrying"));try{const f=await fetch("/api/erp/logs/"+encodeURIComponent(c)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),b=await f.json().catch(()=>({}));showToast(f.ok&&b.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),f.ok&&b.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(c),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function d(c){const u=Array.from(e.selected);if(c==="clear"){e.selected.clear(),i();return}if(u.length!==0){if(c==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:u.length}),{danger:!0}))return;try{const b=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,200)})}),B=await b.json().catch(()=>({}));showToast(b.ok?t("erp-exc-batch-delete-ok",{n:B.deleted||0}):t("erp-exc-retry-fail"),b.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(c==="retry")try{const f=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,50)})}),b=await f.json().catch(()=>({}));showToast(f.ok?t("erp-exc-batch-retry-ok",{ok:b.succeeded||0,fail:(b.failed||0)+(b.skipped||0)}):t("erp-exc-retry-fail"),f.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function l(c){const u=document.getElementById("erp-exc-block");if(!(!u||e.loading)){e.loading=!0;try{if(!Array.isArray(window._erpEndpoints)||!window._erpEndpoints.length)try{const v=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+a()}});if(v.ok){const h=await v.json();window._erpEndpoints=h&&(h.items||h)||[]}}catch{}const f=new URLSearchParams;e.q&&f.set("q",e.q),e.cat&&f.set("category",e.cat),e.adapter&&f.set("adapter",e.adapter),f.set("limit",String(e.pageSize)),f.set("offset",String(c?e.items.length:0));const b=await fetch("/api/erp/exceptions?"+f.toString(),{headers:{Authorization:"Bearer "+a()}});if(!b.ok){c||(u.hidden=!0);return}const B=await b.json(),x=B.items||[];e.items=c?e.items.concat(x):x,e.total=B.total||0,e.categories=B.categories||{},i()}catch{c||(u.hidden=!0)}finally{e.loading=!1}}}let p={};function m(){const c=document.getElementById("erp-exc-modal");c&&c.remove()}window._erpExcOpenEdit=function(c){const u=(e.items||[]).find(S=>String(S.id)===String(c));if(!u)return;const f=u.push_type==="id_card",b=!!u.history_client_id&&u.category==="customer_mismatch",B=u.category==="product_mismatch"&&!!u.history_id&&!!u.endpoint_id,x=o(u),v=u.state==="needs_action"?"needs":u.state==="retrying"?"retry":"fail",h=(S,C)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(S)}</span><span class="erp-exc-m-v">${escapeHtml(C||"—")}</span></div>`;let L="";if(b)L=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(B)L=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const S="erp-exc-edit-hint-"+(u.category||"other");let C=t(S);(!C||C===S)&&(C=x),L=`<div class="erp-exc-m-hint">${escapeHtml(C)}</div>`}const I=document.createElement("div");if(I.id="erp-exc-modal",I.className="erp-exc-modal-overlay",I.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${v}">${escapeHtml(t("erp-exc-state-"+(u.state||"failed")))}</span> ${escapeHtml(x)}${u.error_code&&!f?` <span class="erp-exc-code">${escapeHtml(u.error_code)}</span>`:""}</div>
                    ${h(f?t("erp-log-col-booking"):t("erp-exc-f-invoice"),u.invoice_no)}
                    ${h(f?t("erp-log-col-customer"):t("erp-exc-f-seller"),u.seller_name)}
                    ${f?h(t("erp-log-col-idcard"),u.id_card_tail?"••••"+u.id_card_tail:"—"):h(t("erp-exc-f-buyer"),u.ocr_buyer_name)+h(t("erp-exc-edit-field-current"),u.client_name)}
                    ${L}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${b?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${B?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(I),I.addEventListener("click",S=>{S.target===I&&m()}),document.getElementById("erp-exc-m-close").addEventListener("click",m),document.getElementById("erp-exc-m-cancel").addEventListener("click",m),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{m(),r(u.id,null)}),b){let S="";const C=document.getElementById("erp-exc-m-bind"),w=document.getElementById("erp-exc-m-custlist"),g=document.getElementById("erp-exc-m-search"),E=($,j)=>{const _=(j||"").trim().toLowerCase(),A=_?$.filter(q=>(q.code||"").toLowerCase().includes(_)||(q.name||"").toLowerCase().includes(_)):$;if(A.length===0){w.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}w.innerHTML=A.slice(0,100).map(q=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(q.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(q.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(q.code||"")}</span>
                    </div>`).join(""),w.querySelectorAll(".erp-exc-m-cust").forEach(q=>{q.addEventListener("click",()=>{S=q.dataset.custCode||"",w.querySelectorAll(".erp-exc-m-cust").forEach(F=>F.classList.remove("sel")),q.classList.add("sel"),C&&(C.disabled=!S)})})},M=async()=>{const $=u.endpoint_id;if(p[$]){E(p[$],"");return}try{const j=await fetch("/api/erp/endpoints/"+encodeURIComponent($)+"/customers",{headers:{Authorization:"Bearer "+a()}}),_=await j.json().catch(()=>({}));if(!j.ok||!_.ok){w.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const A=_.customers||[];p[$]=A,E(A,"")}catch{w.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};g&&g.addEventListener("input",()=>E(p[u.endpoint_id]||[],g.value)),M(),C&&C.addEventListener("click",async()=>{if(S){C.disabled=!0,C.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:u.history_client_id,erp_type:u.endpoint_adapter,erp_code:S})})).ok){showToast(t("erp-exc-retry-fail"),"error"),C.disabled=!1,C.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),m(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),C.disabled=!1,C.textContent=t("erp-exc-edit-bind-retry")}}})}if(B){const S=document.getElementById("erp-exc-m-bind-prod"),C=document.getElementById("erp-exc-m-prodlist"),w={};let g=[];const E=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+g.slice(0,500).map(j=>`<option value="${escapeHtml(j.code||"")}" data-pname="${escapeHtml(j.name||"")}">`+escapeHtml((j.name||"")+" · "+(j.code||""))+"</option>").join(""),M=j=>{if(!j.length){C.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}C.innerHTML=j.map(_=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(_)}">${escapeHtml(_)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(_)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${E()}</select>
                    </div>`).join(""),C.querySelectorAll(".erp-exc-m-prod-sel").forEach(_=>{_.addEventListener("change",()=>{const A=_.dataset.item,q=_.options[_.selectedIndex];_.value?w[A]={code:_.value,name:q&&q.dataset.pname||""}:delete w[A],S&&(S.disabled=Object.keys(w).length===0)})})};(async()=>{try{const _=await(await fetch("/api/history/"+encodeURIComponent(u.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),A=_&&_.pages||[],q=[],F={};(Array.isArray(A)?A:[]).forEach(Y=>{const T=Y&&Y.fields&&Y.fields.items||[];(Array.isArray(T)?T:[]).forEach(k=>{const y=(k&&(k.name||k.description)||"").trim();y&&!F[y]&&(F[y]=1,q.push(y))})});const D=await fetch("/api/erp/endpoints/"+encodeURIComponent(u.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),V=await D.json().catch(()=>({}));if(!D.ok||!V.ok){C.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}g=V.products||[],M(q)}catch{C.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),S&&S.addEventListener("click",async()=>{const j=Object.entries(w);if(j.length){S.disabled=!0,S.textContent=t("erp-exc-retrying");try{for(const[_,A]of j)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:u.endpoint_adapter,item_name:_,erp_code:A.code,erp_name:A.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),S.disabled=!1,S.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),m(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),S.disabled=!1,S.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=i,window.loadErpExceptions=l,window._erpExcState=e})();const rs=`
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
`;we("cmdk-mask",rs);(function(){function e(c){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||c&&c.id&&String(c.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var u=window._userInfo,f=!1,b=!0,B=!1,x=!1;u&&(f=typeof canManageTeam=="function"?canManageTeam(u):!!(u.role==="owner"||u.is_super_admin),b=typeof shouldHideMoney=="function"?shouldHideMoney(u):u.role==="member"&&!u.is_super_admin,B=typeof isSuperAdmin=="function"?isSuperAdmin(u):!!u.is_super_admin,x=e(u)),document.querySelectorAll("[data-show-if-team]").forEach(function(h){h.style.display=f?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(h){h.style.display=b?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(h){h.style.display=B?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(h){h.style.display=x?"":"none"});var v=B||x;document.querySelectorAll("[data-show-if-special]").forEach(function(h){h.style.display=v?"":"none"})},window.renderAvatarMenu=function(u){if(u){var f=document.getElementById("avatar-btn"),b=document.getElementById("avatar-popup-name"),B=document.getElementById("avatar-popup-email");if(!(!f||!b||!B)){var x=(u.username||"").trim(),v=x.split("@")[0]||x||"—",h=(x.charAt(0)||"?").toUpperCase(),L=(u.avatar_url||"").trim();if(L){var I=L.replace(/"/g,"&quot;"),S=h.replace(/'/g,"\\'");f.innerHTML='<img src="'+I+'" alt="'+h+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+S+`'">`}else f.textContent=h;b.textContent=v,B.textContent=x||"—",f.setAttribute("title",x||"")}}};function n(){var c=document.getElementById("avatar-wrap"),u=document.getElementById("avatar-btn"),f=document.getElementById("avatar-popup");if(!c||!u||!f)return;function b(){f.classList.remove("show"),u.setAttribute("aria-expanded","false")}function B(){f.classList.add("show"),u.setAttribute("aria-expanded","true")}u.addEventListener("click",function(x){x.stopPropagation(),f.classList.contains("show")?b():B()}),document.addEventListener("click",function(x){f.classList.contains("show")&&!c.contains(x.target)&&b()}),f.addEventListener("click",function(x){var v=x.target.closest(".avatar-popup-item");if(v){var h=v.dataset.action;switch(b(),h){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var L=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(L||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var I=document.getElementById("help-modal");I&&(I.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=b}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(c){return c.style.display!=="none"})}function o(c){var u=a();u.forEach(function(f){f.classList.remove("focus")}),u[c]&&(u[c].classList.add("focus"),u[c].scrollIntoView({block:"nearest"}))}function s(c){var u=a();if(u.length){var f=u.findIndex(function(B){return B.classList.contains("focus")});f<0&&(f=0);var b=(f+c+u.length)%u.length;o(b)}}function i(c){c=(c||"").toLowerCase().trim();var u=0,f=window._userInfo,b=typeof isSuperAdmin=="function"?isSuperAdmin(f):!!(f&&f.is_super_admin),B=e(f);document.querySelectorAll(".cmdk-item").forEach(function(v){if(v.dataset.showIfAdmin==="1"&&!b){v.style.display="none";return}if(v.dataset.showIfTest==="1"&&!B){v.style.display="none";return}var h=(v.dataset.cmdkText||v.textContent||"").toLowerCase(),L=!c||h.indexOf(c)>=0;v.style.display=L?"":"none",v.classList.remove("focus"),L&&u++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(v){for(var h=v.nextElementSibling,L=!1;h&&!h.hasAttribute("data-cmdk-section");){if(h.classList&&h.classList.contains("cmdk-item")&&h.style.display!=="none"){L=!0;break}h=h.nextElementSibling}v.style.display=L?"":"none"});var x=document.getElementById("cmdk-empty");x&&(x.style.display=u===0?"flex":"none"),o(0)}window.openCmdk=function(){var u=document.getElementById("cmdk-mask");u&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),u.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var f=document.getElementById("cmdk-input");f&&(f.value="",i(""),f.focus(),o(0))},50))},window.closeCmdk=function(){var u=document.getElementById("cmdk-mask");u&&u.classList.remove("show")};function r(c){if(c){if(c.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var u=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(u||"即将上线","info")}return}var f=c.dataset.cmdkRoute,b=c.dataset.cmdkAction;if(window.closeCmdk(),f){typeof routeTo=="function"&&routeTo(f);return}if(b){if(b==="open-admin"){window.location.href="/admin/cost";return}if(b.indexOf("lang-")===0){var B=b.slice(5);typeof applyLang=="function"&&applyLang(B)}}}}function d(){var c=document.getElementById("cmdk-mask"),u=document.getElementById("cmdk-input"),f=document.getElementById("cmdk-body");if(!(!c||!u||!f)){c.addEventListener("click",function(x){x.target===c&&window.closeCmdk()});var b=document.getElementById("cmdk-esc-btn");b&&b.addEventListener("click",function(){window.closeCmdk()}),u.addEventListener("input",function(x){i(x.target.value)}),u.addEventListener("keydown",function(x){x.key==="ArrowDown"?(x.preventDefault(),s(1)):x.key==="ArrowUp"?(x.preventDefault(),s(-1)):x.key==="Enter"?(x.preventDefault(),r(c.querySelector(".cmdk-item.focus"))):x.key==="Escape"&&(x.preventDefault(),window.closeCmdk())}),f.addEventListener("click",function(x){var v=x.target.closest(".cmdk-item");v&&r(v)}),f.addEventListener("mousemove",function(x){var v=x.target.closest(".cmdk-item");!v||v.style.display==="none"||v.classList.contains("cmdk-item-locked")||(a().forEach(function(h){h.classList.remove("focus")}),v.classList.add("focus"))});var B=document.getElementById("topbar-search");B&&(B.addEventListener("click",function(){window.openCmdk()}),B.addEventListener("keydown",function(x){(x.key==="Enter"||x.key===" ")&&(x.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(c){if((c.metaKey||c.ctrlKey)&&(c.key==="k"||c.key==="K")){c.preventDefault(),window.openCmdk();return}if(c.key==="Escape"){var u=document.getElementById("cmdk-mask");if(u&&u.classList.contains("show")){window.closeCmdk();return}var f=document.getElementById("avatar-popup");f&&f.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var l=(navigator.userAgent||"").toLowerCase(),p=l.indexOf("mac")>=0||l.indexOf("iphone")>=0||l.indexOf("ipad")>=0;p||document.body.classList.add("is-windows")}catch{}function m(){n(),d(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",m):m()})();(function(){function n(b){return String(b??"").replace(/[&<>"']/g,function(B){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[B]})}function a(b){if(!b||isNaN(b))return"";var B=Number(b);return B<1024?B+" B":B<1024*1024?(B/1024).toFixed(1)+" KB":(B/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(b){var B=b.target.closest&&b.target.closest(".recon-collapse-head");if(B&&!(b.target.closest("button")||b.target.closest("a"))){var x=B.closest(".recon-collapse");if(x){var v=x.getAttribute("data-collapsed")==="true";x.setAttribute("data-collapsed",v?"false":"true"),v&&(x.id==="vex-summary-collapse"&&m(),x.id==="vex-detail-collapse"&&c())}}}),document.addEventListener("keydown",function(b){if(!(b.key!=="Enter"&&b.key!==" ")){var B=b.target.closest&&b.target.closest(".recon-collapse-head");B&&(b.preventDefault(),B.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){l("vat"),l("gl")}function d(b){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(b)||[]}catch{}var B=document.getElementById(b==="vat"?"glv-vat-input":"glv-gl-input");return B&&B.files?Array.from(B.files):[]}function l(b){var B=document.getElementById(b==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(B){var x=d(b),v=b==="vat"?"glv-up-vat-title":"glv-up-gl-title",h=b==="vat"?"① 销项税报告":"② 总账 GL",L=window.t&&window.t(v)||h,I=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),S=n(window.t&&window.t("vex-preview-clear-all")||"全清"),C=o[b]||"",w=x.length;B.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(L)+' <span class="vex-pp-col-count">'+w+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+b+'" type="text" placeholder="'+I+'" value="'+n(C)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+b+'" type="button">'+S+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+b+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+b+'-pg"></div>';var g=document.getElementById("glv-pp-search-"+b);g&&g.addEventListener("input",function(M){o[b]=M.target.value,p(b)});var E=document.getElementById("glv-pp-clearall-"+b);E&&E.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(b)}),p(b)}}function p(b){var B=document.getElementById("glv-pp-"+b+"-list"),x=document.getElementById("glv-pp-"+b+"-pg");if(B){var v=d(b),h=(o[b]||"").toLowerCase(),L=v.map(function(C,w){return{f:C,i:w}}),I=h?L.filter(function(C){return C.f.name.toLowerCase().indexOf(h)>=0}):L;if(B.innerHTML=I.map(function(C){var w=C.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(w.name)+'">'+n(w.name)+'</span><span class="vex-pp-fi-size">'+a(w.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+b+'" data-idx="'+C.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),B.querySelectorAll(".vex-pp-fi-del").forEach(function(C){C.addEventListener("click",function(){var w=C.dataset.kind,g=parseInt(C.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(w,isNaN(g)?null:g)})}),x){var S=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";x.textContent=S.replace("{n}",I.length).replace("{m}",I.length)}}}function m(){var b=function(x,v){var h=document.getElementById(x);h&&(h.textContent=v==null?"—":String(v))},B=window._vexLastTask||{};b("vex-sum-total",B.total),b("vex-sum-matched",B.matched),b("vex-sum-diff",B.diff),b("vex-sum-incomplete",B.incomplete),b("vex-sum-cash",B.cash),document.getElementById("vex-summary-sub")}function c(){var b=window._vexLastTask&&window._vexLastTask.diff_rows||[],B=document.getElementById("vex-detail-tbody"),x=document.getElementById("vex-detail-table"),v=document.getElementById("vex-detail-empty");if(!(!B||!x||!v)){if(b.length===0){x.style.display="none",v.style.display="";return}v.style.display="none",x.style.display="";var h=b.map(function(I){return'<tr><td class="recon-detail-cell-mono">'+n(I.invoice_no||"")+"</td><td>"+n(I.field||"")+"</td><td>"+n(I.report_value||"")+"</td><td>"+n(I.invoice_value||"")+"</td><td>"+n(I.kind||"")+"</td></tr>"}).join("");B.innerHTML=h;var L=document.getElementById("vex-detail-sub");L&&(L.textContent=String(b.length))}}function u(){var b=document.getElementById("glv-toggle-preview");b&&!b._reconBound&&(b._reconBound=!0,b.addEventListener("click",function(){var B=document.getElementById("glv-preview-panel"),x=document.getElementById("glv-toggle-preview-label"),v=B&&B.style.display!=="none";B&&(B.style.display=v?"none":""),b.classList.toggle("open",!v),x&&(x.textContent=v?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),v||r()})),["glv-vat-input","glv-gl-input"].forEach(function(B){var x=document.getElementById(B);!x||x._reconWatched||(x._reconWatched=!0,x.addEventListener("change",function(){var v=document.getElementById("glv-preview-panel");v&&v.style.display!=="none"&&r()}))})}function f(){var b=document.getElementById("vex-summary-collapse"),B=document.getElementById("vex-detail-collapse");b&&(b.style.display=""),B&&(B.style.display=""),m(),c()}window._fillVexSummary=m,window._fillVexDetail=c,window._onVexResultShown=f,document.addEventListener("DOMContentLoaded",function(){u()}),setTimeout(u,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var b=document.getElementById("glv-preview-panel");b&&b.style.display!=="none"&&r();var B=document.getElementById("glv-toggle-preview-label"),x=document.getElementById("glv-toggle-preview");B&&x&&(B.textContent=x.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:m,fillVexDetail:c}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(d=>{d.addEventListener("click",()=>{i.forEach(u=>u.classList.remove("active")),d.classList.add("active");const l=d.dataset.reconTab,p=document.getElementById("recon-pane-bank"),m=document.getElementById("recon-pane-sale-vat"),c=document.getElementById("recon-pane-gl-vat");p&&(p.style.display=l==="bank"?"":"none"),m&&(m.style.display=l==="sale-vat"?"":"none"),c&&(c.style.display=l==="gl-vat"?"":"none"),l==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),l==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const d=document.createElement("button");return d.id="settings-modal-close",d.className="settings-modal-close",d.setAttribute("aria-label","close"),d.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(d,i.firstChild),d.addEventListener("click",s),r.addEventListener("click",l=>{l.target===r&&s()}),r}function o(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(l){console.warn("renderSettings:",l)}let d=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');d&&d.click()},50)}function s(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=R=>document.getElementById(R);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function i(R){return String(R??"").replace(/[&<>"']/g,U=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[U])}function r(R){return R<1024?R+" B":R<1024*1024?(R/1024).toFixed(1)+" KB":(R/1024/1024).toFixed(1)+" MB"}let d=[],l=[],p=!1,m=[],c=50,u=50,f="",b="";async function B(){try{const R=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!R.ok)return;const J=(await R.json()).kpi||{};[["vex-kpi-month-val",J.this_month],["vex-kpi-running-val",J.running],["vex-kpi-done-val",J.done],["vex-kpi-failed-val",J.failed]].forEach(([W,X])=>{const se=document.getElementById(W);se&&(se.textContent=X??0)})}catch{}}async function x(){try{const R=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!R.ok)return;const U=await R.json();I(U.rows||[])}catch{}}const v=10;var h=1;function L(){var R=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(h=1,I(m),!!R){var U=document.getElementById("vex-task-tbody");U&&U.querySelectorAll("tr").forEach(function(J){J.dataset.taskId&&(J.style.display=J.textContent.toLowerCase().indexOf(R)>=0?"":"none")})}}function I(R){m=R||m;const U=document.getElementById("vex-task-tbody");if(!U)return;if(!m.length){U.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",S(0);return}const J=Math.ceil(m.length/v);h>J&&(h=J);const W=(h-1)*v;C(m.slice(W,W+v)),S(m.length)}function S(R){const U=document.getElementById("vex-task-pager"),J=document.getElementById("vex-task-pager-info"),W=document.getElementById("vex-task-prev"),X=document.getElementById("vex-task-next");if(!U)return;if(R<=v){U.style.display="none";return}U.style.display="";const se=Math.ceil(R/v);J&&(J.textContent=h+" / "+se),W&&(W.disabled=h<=1),X&&(X.disabled=h>=se)}function C(R){const U=document.getElementById("vex-task-tbody");if(!U)return;const J={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},W={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';U.innerHTML=R.map(N=>{const K=N.created_at?new Date(N.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",O=N.period||"—",ae=N.matched_count!=null?N.matched_count+" ✓ · "+N.mismatched_count+" ⚠":"—",Z=N.mismatch_amount!=null?"฿ "+Number(N.mismatch_amount).toLocaleString():"—",ie=N.elapsed_seconds!=null?N.elapsed_seconds.toFixed(1)+" s":"—",ce=N.status||"pending",fe=N.client_name&&N.client_name!=="client"?N.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${i(N.id)}" style="cursor:pointer">
                <td>${K}</td>
                <td>${i(fe)}</td>
                <td>${i(O)}</td>
                <td>${(N.invoice_count||0)+" / "+(N.report_count||0)}</td>
                <td>${ae}</td>
                <td>${Z}</td>
                <td><span class="badge ${W[ce]||"badge-gray"}">${J[ce]||ce}</span></td>
                <td>${ie}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${i(N.id)}" title="${t("hist_export")||"导出"}">${X}</button>
                    <button class="vex-task-del-btn" data-task-id="${i(N.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${se}</button>
                </div></td>
            </tr>`}).join(""),U.querySelectorAll(".vex-task-dl-btn").forEach(N=>{N.addEventListener("click",async K=>{K.stopPropagation();const O=N.dataset.taskId;try{const ae=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(O)+"/download",{credentials:"include",headers:s()});if(ae.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!ae.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const Z=await ae.blob(),ce=(ae.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),fe=ce?decodeURIComponent(ce[1]):"vat_recon_"+O+".xlsx",ve=URL.createObjectURL(Z),ge=document.createElement("a");ge.href=ve,ge.download=fe,ge.click(),setTimeout(()=>URL.revokeObjectURL(ve),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),U.querySelectorAll(".vex-task-del-btn").forEach(N=>{N.addEventListener("click",K=>{K.stopPropagation(),g(N.dataset.taskId)})}),L()}function w(){var R=document.getElementById("vex-task-prev"),U=document.getElementById("vex-task-next");R&&!R._vexBound&&(R._vexBound=!0,R.addEventListener("click",function(){h>1&&(h--,I())})),U&&!U._vexBound&&(U._vexBound=!0,U.addEventListener("click",function(){var J=Math.ceil(m.length/v);h<J&&(h++,I())}))}async function g(R){const U=t("vex-task-delete-confirm-title")||"删除对账任务?",J=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(J,{title:U,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const X=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(R),{method:"DELETE",credentials:"include",headers:s()});if(!X.ok)throw new Error(X.status);showToast(t("vex-task-delete-ok")||"已删除","success"),x(),B()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function E(R){const U=window._currentLang||"th",J={zh:`已忽略 ${R} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${R} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${R} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${R} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(J[U]||J.th,"warn")}function M(R){const U=new Set(d.map(W=>W.name+"|"+W.size));let J=0;for(const W of R){if(!a.test(W.name)){J++;continue}const X=W.name+"|"+W.size;if(!U.has(X)&&(U.add(X),d.push(W),d.length>=1e3))break}J>0&&E(J),d.length>1e3&&(d=d.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),A()}function $(R){const U=new Set(l.map(W=>W.name+"|"+W.size));let J=0;for(const W of R){if(!a.test(W.name)){J++;continue}const X=W.name+"|"+W.size;if(!U.has(X)&&(U.add(X),l.push(W),l.length>=30))break}J>0&&E(J),l.length>30&&(l=l.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),A()}function j(R){d.splice(R,1),A()}function _(R){l.splice(R,1),A()}function A(){const R=o("vex-list-invoice"),U=o("vex-list-report"),J=o("vex-count-invoice"),W=o("vex-count-report");J&&(J.textContent=d.length),W&&(W.textContent=l.length);const X=(K,O,ae)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${i(K.name)}">${i(K.name)}</span>
            <span class="vex-fi-s">${r(K.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${ae}" data-vex-idx="${O}" aria-label="remove">×</button>
        </div>`;R&&(R.innerHTML=d.map((K,O)=>X(K,O,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),U&&(U.innerHTML=l.map((K,O)=>X(K,O,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(K=>{K.addEventListener("click",O=>{const ae=K.dataset.vexKind,Z=parseInt(K.dataset.vexIdx,10);ae==="inv"?j(Z):_(Z)})});const se=d.length>0&&l.length>0;o("vex-build").disabled=!se||p;const N=o("vex-action-info");N&&(!d.length||!l.length?(N.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",N.className="vex-action-info muted"):(N.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",d.length).replace("{b}",l.length),N.className="vex-action-info ok")),V()}const q='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',F='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',D='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function V(){const R=o("vex-preview-panel");if(!R||R.style.display==="none")return;Y("inv"),Y("rep");const U=o("vex-pp-guide");U&&(U.style.display=d.length>100?"flex":"none")}function Y(R){const U=o(R==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!U)return;const J=R==="inv"?d:l,W=R==="inv"?f:b,X=t(R==="inv"?"vex-preview-invoice":"vex-preview-report")||(R==="inv"?"销售发票":"VAT 报告"),se=i(t("vex-preview-search")||"搜索文件名..."),N=i(t("vex-preview-clear-all")||"全清");U.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${i(X)} <span class="vex-pp-col-count">${J.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${R}" type="text"
                       placeholder="${se}" value="${i(W)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${R}" type="button">${N}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${R}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${R}-pg"></div>`;const K=o("vex-pp-search-"+R);K&&K.addEventListener("input",ae=>{R==="inv"?(f=ae.target.value,c=50):(b=ae.target.value,u=50),T(R)});const O=o("vex-pp-clearall-"+R);O&&O.addEventListener("click",()=>{R==="inv"?(d=[],f="",c=50):(l=[],b="",u=50),A()}),T(R)}function T(R){const U=o("vex-pp-"+R+"-list"),J=o("vex-pp-"+R+"-pg");if(!U)return;const W=R==="inv"?d:l,X=R==="inv"?f:b,se=R==="inv"?c:u,N=R==="inv"?q:F,K=W.map((Z,ie)=>({f:Z,i:ie})),O=X?K.filter(({f:Z})=>Z.name.toLowerCase().includes(X.toLowerCase())):K,ae=O.slice(0,se);if(U.innerHTML=ae.map(({f:Z,i:ie})=>`
            <div class="vex-pp-file-row">
                ${N}
                <span class="vex-pp-fi-name" title="${i(Z.name)}">${i(Z.name)}</span>
                <span class="vex-pp-fi-size">${r(Z.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${R}" data-ridx="${ie}" aria-label="remove">${D}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${R}" style="height:1px;flex-shrink:0"></div>`,U.querySelectorAll(".vex-pp-fi-del").forEach(Z=>{Z.addEventListener("click",()=>{const ie=parseInt(Z.dataset.ridx,10);Z.dataset.kind==="inv"?j(ie):_(ie)})}),J){const Z=t("vex-preview-count")||"显示前 {n} / 共 {m}";J.textContent=Z.replace("{n}",ae.length).replace("{m}",O.length)}k(R,O.length)}function k(R,U){if((R==="inv"?c:u)>=U)return;const W=o("vex-pp-sentinel-"+R),X=o("vex-pp-"+R+"-list");if(!W||!X)return;const se=new IntersectionObserver(N=>{N[0].isIntersecting&&(se.disconnect(),R==="inv"?c+=50:u+=50,T(R))},{root:X,threshold:.8});se.observe(W)}function y(R,U,J,W){const X=o(R),se=o(U);!X||!se||(X.addEventListener("click",()=>se.click()),X.addEventListener("keydown",N=>{(N.key==="Enter"||N.key===" ")&&(N.preventDefault(),se.click())}),X.addEventListener("dragover",N=>{N.preventDefault(),X.classList.add("drag-over")}),X.addEventListener("dragleave",()=>X.classList.remove("drag-over")),X.addEventListener("drop",N=>{N.preventDefault(),X.classList.remove("drag-over");const O=Array.from(N.dataTransfer.files).filter(ae=>a.test(ae.name));if(!O.length){showToast(t("vex-toast-bad-ext"),"error");return}J(O)}),se.addEventListener("change",()=>{const N=Array.from(se.files);J(N),se.value=""}))}async function H(){if(p||!d.length||!l.length)return;p=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var R=document.getElementById("vex-download");R&&(R.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(X){var se=document.getElementById(X);se&&(se.style.display="none")});const U=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",d.length).replace("{b}",l.length);const J=setInterval(()=>{const X=Math.floor((Date.now()-U)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",X).replace("{a}",d.length).replace("{b}",l.length)},1e3);try{const X=new FormData;for(const le of d)X.append("invoices",le);for(const le of l)X.append("reports",le);const se=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";X.append("lang",se);const N=localStorage.getItem("mrpilot_token")||"",K=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:X});let O=null;try{O=await K.json()}catch{O=null}if(!K.ok||!O||!O.ok||!O.job_id)throw clearInterval(J),new Error(O&&O.detail||"HTTP "+K.status);const ae=o("vex-progress-sub"),Z=await window._reconPollJob(O.job_id,N,{onProgress:le=>{ae&&(ae.textContent=window._reconProgressText(le,se))}});if(clearInterval(J),!Z||Z.status!=="done"||!Z.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const ie=Z.result_id;let ce=0;const fe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(ie)+"/download",{headers:s()});if(!fe.ok)throw new Error("HTTP "+fe.status);const ge=(fe.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),ke=ge&&ge[1]||"vat_recon_"+Date.now()+".xlsx",Se=await fe.blob(),_e=URL.createObjectURL(Se),re=o("vex-download");re.href=_e,re.download=ke;try{const le=document.createElement("a");le.href=_e,le.download=ke,document.body.appendChild(le),le.click(),setTimeout(()=>le.remove(),100)}catch{}o("vex-progress").style.display="none";var W=document.getElementById("vex-download");W&&(W.style.display=""),ie&&(ce=await G(ie)),window._onVexResultShown&&window._onVexResultShown(),ce>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",ce),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),B(),setTimeout(x,800)}catch(X){clearInterval(J),o("vex-progress").style.display="none";const se=(t("vex-toast-fail")||"生成失败")+": "+(X.message||X);showToast(se,"error")}finally{p=!1,o("vex-build").disabled=!1}}function P(){d=[],l=[];var R=document.getElementById("vex-download");R&&(R.style.display="none"),A()}function z(R){if(R==null)return"—";var U=parseFloat(R);return isNaN(U)?"—":U.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function G(R){try{var U=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(R),{headers:s()});if(!U.ok)throw new Error(U.status);var J=await U.json(),W=J.raw_data_json;if(typeof W=="string")try{W=JSON.parse(W)}catch{W={}}W=W||{};var X=W.rows||[],se=[];X.forEach(function(O){O.kind==="invoice_orphan"?se.push({invoice_no:O.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:z(O.amount_inv),kind:O.kind}):O.kind==="report_orphan"?se.push({invoice_no:O.invoice_no||"",field:"仅报告有",report_value:z(O.amount_rep),invoice_value:"—",kind:O.kind}):O.dims&&Object.keys(O.dims).length>0&&Object.keys(O.dims).forEach(function(ae){var Z=String(O.dims[ae]||""),ie=Z.split(" ≠ ");se.push({invoice_no:O.invoice_no||"",field:ae,report_value:ie[0]||Z,invoice_value:ie.length>1?ie[1]:"—",kind:"diff"})})});var N=X.filter(function(O){return O.kind==="matched_cash"}).length,K=Math.max(0,parseInt(W.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:W.n_total||0,matched:W.n_ok||0,diff:W.n_diff||0,incomplete:K,cash:N,diff_rows:se,task_id:R},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),K}catch{return 0}}function Q(){const R=document.getElementById("vex-pane");R&&R.querySelectorAll("[data-i18n]").forEach(U=>{const J=t(U.dataset.i18n);J&&(U.textContent=J)}),A(),x()}function te(){y("vex-drop-invoice","vex-input-invoice",M),y("vex-drop-report","vex-input-report",$);const R=o("vex-build"),U=o("vex-reset");R&&R.addEventListener("click",H),U&&U.addEventListener("click",P),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(X=>{X.addEventListener("click",()=>{B(),x()})}),w();const J=document.getElementById("vex-task-search");J&&J.addEventListener("input",L);const W=document.getElementById("vex-toggle-preview");W&&W.addEventListener("click",()=>{const X=o("vex-preview-panel"),se=o("vex-toggle-preview-label"),N=X&&X.style.display!=="none";X&&(X.style.display=N?"none":""),W&&W.classList.toggle("open",!N),se&&(se.textContent=N?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),N||V()}),A(),B()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",te):te(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",Q),window.subscribeI18n("vex-preview-panel",V))})();(function(){const e=k=>document.getElementById(k),n=()=>localStorage.getItem("mrpilot_token")||"",a=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",o=()=>({Authorization:"Bearer "+n()}),s={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},i={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},r=k=>(i[a()]||i.th)[k]||k;function d(k){const y=a(),P={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[k];return P?P[y]||P.th||P.en:r("error")||"Error"}const l=k=>k==null||isNaN(k)?"":Number(k).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function p(k,y,H,P){const z=e(k),G=e(y),Q=e(H);if(!z||!G||!Q)return;const te=R=>{if(!R||!R.length)return;const U=Array.isArray(s[P])?s[P].slice():[],J=new Set(U.map(W=>W.name+"|"+W.size));for(const W of R){if(!W)continue;const X=W.name+"|"+W.size;J.has(X)||(U.push(W),J.add(X))}s[P]=U,m(Q,U),u(),f(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};z.addEventListener("click",()=>G.click()),z.addEventListener("keydown",R=>{(R.key==="Enter"||R.key===" ")&&(R.preventDefault(),G.click())}),G.addEventListener("change",()=>{te(Array.from(G.files||[])),G.value=""}),z.addEventListener("dragover",R=>{R.preventDefault(),z.classList.add("drag-over")}),z.addEventListener("dragleave",()=>z.classList.remove("drag-over")),z.addEventListener("drop",R=>{R.preventDefault(),z.classList.remove("drag-over");const U=R.dataTransfer&&R.dataTransfer.files?Array.from(R.dataTransfer.files):[];te(U)})}function m(k,y){if(!k)return;if(!y||y.length===0){k.textContent="";return}const H=y.reduce((P,z)=>P+Math.round(z.size/1024),0);if(y.length===1)k.textContent=y[0].name+"  ("+H+" KB)";else{const P=window.t&&window.t("glv-files-count")||"{n} 个文件";k.textContent=P.replace("{n}",y.length)+"  ("+H+" KB)"}}function c(k){const y=s[k];return Array.isArray(y)?y:y?[y]:[]}function u(){const k=e("btn-glv-run");if(!k)return;const y=c("glFile").length>0&&c("vatFile").length>0;k.disabled=!y||s.running}function f(){const k=e("glv-status");if(!k||s.running)return;const y=c("vatFile").length,H=c("glFile").length;y===0&&H===0?(k.className="vex-action-info muted",k.innerHTML="<span>"+r("hint_need_both")+"</span>"):y>0&&H>0?(k.className="vex-action-info ok",k.innerHTML="<span>"+r("hint_ready")+"</span>"):(k.className="vex-action-info muted",k.innerHTML="<span>"+r("hint_need_one_more")+"</span>")}function b(k,y){const H=k==="vat"?"vatFile":"glFile",P=k==="vat"?"glv-vat-input":"glv-gl-input",z=k==="vat"?"glv-vat-name":"glv-gl-name",G=c(H);y==null?s[H]=[]:s[H]=G.filter((te,R)=>R!==y);const Q=e(P);Q&&(Q.value=""),m(e(z),c(H)),u(),f(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=b;function B(){s.glFile=[],s.vatFile=[],s.currentTaskId=null,s.lastDetail=[],s.lastSummary=null;const k=e("glv-vat-input");k&&(k.value="");const y=e("glv-gl-input");y&&(y.value="");const H=e("glv-vat-name");H&&(H.textContent="");const P=e("glv-gl-name");P&&(P.textContent="");const z=e("glv-result");z&&(z.style.display="none");const G=e("glv-kpi-strip");G&&(G.style.display="none"),u(),f(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function x(k){const y=e("glv-tbody");if(!y)return;Y(k.length),y.innerHTML="";const H=r("not_found"),P=document.createDocumentFragment();k.forEach(z=>{const G=document.createElement("tr"),Q=(W,X)=>{const se=document.createElement("td");return X&&(se.className=X),se.textContent=W,se},te=z.gl_amount===null||z.gl_amount===void 0,R=z.diff;let U="glv-num",J="glv-num";te?(J+=" glv-cell-missing",U+=" glv-cell-missing"):Math.abs(R||0)<.005?U+=" glv-cell-ok":U+=" glv-cell-diff",G.appendChild(Q(z.doc_no||"","glv-doc")),G.appendChild(Q(z.date||"","")),G.appendChild(Q(z.customer_name||"","")),G.appendChild(Q(l(z.vat_amount),"glv-num")),G.appendChild(Q(te?H:l(z.gl_amount),J)),G.appendChild(Q(te?H:l(z.diff),U)),G.appendChild(Q(z.account_codes||"","glv-doc")),P.appendChild(G)}),y.appendChild(P)}function v(k){const y=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!y)return;y.innerHTML="",[{label:r("s_gl_total"),amount:k.gl_total,emph:!0,items:[],negate:!1},{label:r("s_minus_gl_cr"),amount:-(k.gl_only_credit||0),emph:!1,items:k.gl_only_credit_items||[],negate:!0},{label:r("s_plus_gl_dr"),amount:k.gl_only_debit||0,emph:!1,items:k.gl_only_debit_items||[],negate:!1},{label:r("s_plus_vat_p"),amount:k.vat_only_positive||0,emph:!1,items:k.vat_only_positive_items||[],negate:!1},{label:r("s_minus_vat_n"),amount:k.vat_only_negative||0,emph:!1,items:k.vat_only_negative_items||[],negate:!1},{label:r("s_vat_total"),amount:k.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:P,amount:z,emph:G,items:Q,negate:te})=>{const R=document.createElement("tr");R.className=G?"glv-summary-total":"glv-summary-sect";const U=document.createElement("td"),J=document.createElement("td");U.textContent=P,J.textContent=G?l(z):"",R.appendChild(U),R.appendChild(J),y.appendChild(R),(Q||[]).forEach(W=>{const X=document.createElement("tr");X.className="glv-summary-item";const se=document.createElement("td"),N=document.createElement("td"),K=[W.doc_no,W.date,W.name].filter(Boolean);se.textContent="· "+K.join("  ·  ");const O=te?-(W.amount||0):W.amount||0;N.textContent=l(O),X.appendChild(se),X.appendChild(N),y.appendChild(X)})})}function h(k){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=k&&k.matched!=null?k.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=k&&k.diff!=null?k.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=k&&k.unmatched!=null?k.unmatched:"—")}function L(k){if(!k)return"";try{const y=new Date(k);if(isNaN(y.getTime()))return k;const H=P=>String(P).padStart(2,"0");return y.getFullYear()+"-"+H(y.getMonth()+1)+"-"+H(y.getDate())+" "+H(y.getHours())+":"+H(y.getMinutes())}catch{return k}}const I=10;var S=[],C=1;function w(){C=1,g();var k=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(k){var y=e("glv-history-tbody");y&&y.querySelectorAll("tr").forEach(function(H){H.dataset.taskId&&(H.style.display=H.textContent.toLowerCase().indexOf(k)>=0?"":"none")})}}function g(){const k=e("glv-history-table-wrap"),y=e("glv-history-empty"),H=e("glv-history-tbody"),P=e("glv-history-pager"),z=e("glv-history-pager-info"),G=e("glv-history-prev"),Q=e("glv-history-next");if(!H)return;if(H.innerHTML="",!S.length){k&&(k.style.display="none"),y&&(y.style.display=""),P&&(P.style.display="none");return}k&&(k.style.display=""),y&&(y.style.display="none");const te=Math.ceil(S.length/I);C>te&&(C=te);const R=(C-1)*I,U=S.slice(R,R+I);P&&(P.style.display=S.length>I?"":"none",z&&(z.textContent=C+" / "+te),G&&(G.disabled=C<=1),Q&&(Q.disabled=C>=te)),U.forEach(W=>{const X=document.createElement("tr");X.dataset.taskId=W.id;const se=document.createElement("td");se.textContent=L(W.created_at);const N=document.createElement("td");N.className="glv-history-file",N.title=(W.vat_filename||"")+" + "+(W.gl_filename||""),N.textContent=(W.vat_filename||"?")+" + "+(W.gl_filename||"?");const K=document.createElement("td");K.className="glv-num",K.textContent=(W.vat_row_count||0)+" / "+(W.gl_row_count||0);const O=document.createElement("td");O.className="glv-num",O.textContent=W.matched_count||0;const ae=document.createElement("td");ae.className="glv-num",ae.textContent=W.diff_count||0;const Z=document.createElement("td");Z.className="glv-num",Z.textContent=W.unmatched_count||0;const ie=document.createElement("td");ie.className="glv-history-actions";const ce=(ke,Se,_e,re)=>{const le=document.createElement("button");return le.type="button",_e&&(le.className=_e),le.title=Se,le.setAttribute("aria-label",Se),le.innerHTML=ke,le.onclick=re,le},fe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',ve='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ge='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';ie.appendChild(ce(fe,r("hist_load"),"",()=>$(W.id))),ie.appendChild(ce(ve,r("hist_export"),"",()=>j(W.id))),ie.appendChild(ce(ge,r("hist_delete"),"glv-del",()=>_(W.id))),[se,N,K,O,ae,Z,ie].forEach(ke=>X.appendChild(ke)),H.appendChild(X)})}function E(){var k=e("glv-history-prev"),y=e("glv-history-next");k&&!k._glvBound&&(k._glvBound=!0,k.addEventListener("click",function(){C>1&&(C--,g())})),y&&!y._glvBound&&(y._glvBound=!0,y.addEventListener("click",function(){var H=Math.ceil(S.length/I);C<H&&(C++,g())}))}async function M(){try{const y=await(await fetch("/api/recon/gl-vat/tasks",{headers:o()})).json();S=y&&y.tasks||[],C=1,g(),E()}catch(k){console.error("[gl-vat] history load failed:",k)}}async function $(k){try{const H=await(await fetch("/api/recon/gl-vat/"+k,{headers:o()})).json();if(!H||!H.ok)throw new Error("load_failed");s.currentTaskId=k,s.lastDetail=H.detail||[],s.lastSummary=H.summary||{},h(H.stats||{}),x(s.lastDetail),v(s.lastSummary);const P=e("glv-result");P&&(P.style.display=""),D(),window.scrollTo({top:P?P.offsetTop-80:0,behavior:"smooth"})}catch(y){console.error("[gl-vat] load task failed:",y),alert(r("error")+": "+(y.message||y))}}async function j(k){try{const y="/api/recon/gl-vat/"+k+"/export?lang="+encodeURIComponent(a()),H=await fetch(y,{headers:o()});if(!H.ok)throw new Error("HTTP "+H.status);const P=await H.blob(),z=document.createElement("a");z.href=URL.createObjectURL(P),z.download="GL_VAT_recon_"+k+".xlsx",document.body.appendChild(z),z.click(),setTimeout(()=>{URL.revokeObjectURL(z.href),z.remove()},200)}catch(y){console.error("[gl-vat] exportTask failed:",y),typeof showToast=="function"&&showToast(r("error")+": "+(y.message||y),"error")}}async function _(k){let y;if(typeof window.showConfirm=="function"?y=await window.showConfirm(r("confirm_delete"),{danger:!0}):y=confirm(r("confirm_delete")),!!y)try{const H=await fetch("/api/recon/gl-vat/"+k,{method:"DELETE",headers:o()});if(!H.ok)throw new Error("HTTP "+H.status);M()}catch(H){console.error("[gl-vat] delete failed:",H),typeof showToast=="function"&&showToast(r("error")+": "+(H.message||H),"error")}}async function A(){if(!s.glFile||!s.vatFile){typeof showToast=="function"&&showToast(r("need_files"),"warn");return}s.running=!0,u();const k=e("glv-status"),y=e("glv-progress"),H=e("glv-progress-sub");k&&(k.className="vex-action-info muted",k.style.color="",k.innerHTML="<span>"+r("running")+"</span>"),y&&(y.style.display=""),H&&(H.textContent=(s.vatFile.name||"VAT")+" + "+(s.glFile.name||"GL"));const P=new FormData,z=c("vatFile"),G=c("glFile");for(const te of z)P.append("vat_files",te,te.name);for(const te of G)P.append("gl_files",te,te.name);const Q=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";P.append("revenue_prefix",Q),P.append("lang",a());try{const te=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:o(),body:P});let R=null;try{R=await te.json()}catch{R=null}if(!te.ok||!R||!R.ok||!R.job_id)throw new Error(R&&R.detail||R&&R.error||"HTTP "+te.status);const U=e("glv-progress-sub"),J=await window._reconPollJob(R.job_id,n(),{onProgress:N=>{U&&(U.textContent=window._reconProgressText(N,a()))}});if(!J||J.status!=="done"||!J.result_id)throw J&&J.status==="failed"&&J.error_code?new Error(d(J.error_code)):new Error(r("error")||"Error");const W=await fetch("/api/recon/gl-vat/"+encodeURIComponent(J.result_id),{headers:o()});let X=null;try{X=await W.json()}catch{X=null}if(!W.ok||!X||!X.ok)throw new Error(X&&X.detail||X&&X.error||"HTTP "+W.status);s.currentTaskId=X.task_id,s.lastDetail=X.detail||[],s.lastSummary=X.summary||{},h(X.stats||{}),x(s.lastDetail),v(s.lastSummary);const se=e("glv-result");se&&(se.style.display=""),D(),k&&(k.className="vex-action-info ok",k.style.color="",k.innerHTML="<span>"+r("done")+" · GL "+(X.gl_row_count||0)+" · VAT "+(X.vat_row_count||0)+"</span>"),M()}catch(te){console.error("[gl-vat] run failed:",te),k&&(k.className="vex-action-info",k.style.color="#ef4444",k.innerHTML="<span>"+r("error")+": "+(te.message||te)+"</span>")}finally{s.running=!1,y&&(y.style.display="none"),u()}}async function q(){if(s.currentTaskId)try{const k="/api/recon/gl-vat/"+s.currentTaskId+"/export?lang="+encodeURIComponent(a()),y=await fetch(k,{headers:o()});if(!y.ok)throw new Error("HTTP "+y.status);const H=await y.blob(),P=document.createElement("a");P.href=URL.createObjectURL(H),P.download="GL_VAT_recon_"+s.currentTaskId+".xlsx",document.body.appendChild(P),P.click(),setTimeout(()=>{URL.revokeObjectURL(P.href),P.remove()},200)}catch(k){console.error("[gl-vat] export failed:",k),typeof showToast=="function"&&showToast(r("error")+": "+(k.message||k),"error")}}function F(){s.running||f(),M(),s.lastDetail&&s.lastDetail.length&&x(s.lastDetail),s.lastSummary&&v(s.lastSummary)}function D(){var k=e("glv-kpi-strip");k&&(k.style.display="");var y=e("glv-section-summary");y&&y.setAttribute("data-collapsed","false");var H=e("glv-section-detail");H&&H.setAttribute("data-collapsed","false")}function V(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(k=>{const y=k.getAttribute("data-toggle"),H=document.getElementById(y);if(!H)return;const P=z=>{if(z.target&&z.target.closest("button")!==null&&!z.target.classList.contains("glv-section-head"))return;const G=H.getAttribute("data-collapsed")==="true";H.setAttribute("data-collapsed",G?"false":"true")};k.addEventListener("click",P),k.addEventListener("keydown",z=>{(z.key==="Enter"||z.key===" ")&&(z.preventDefault(),P(z))})})}function Y(k){const y=e("glv-detail-count");y&&(y.textContent=k!=null?String(k):"")}function T(){if(s.inited){M();return}s.inited=!0,p("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),p("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const k=e("btn-glv-run");k&&k.addEventListener("click",A);const y=e("btn-glv-export");y&&y.addEventListener("click",q);const H=e("btn-glv-reset");H&&H.addEventListener("click",B);const P=e("glv-hist-search");P&&P.addEventListener("input",w),V(),h(null),f(),window._loadGlvHistory=M,M(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",F)}window.GlVatRecon={ensureInit:T},window._glvPreviewFiles=function(k){return c(k==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let i={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function r(){const $=typeof _userInfo<"u"?_userInfo:null;return!!($&&($.role==="owner"||$.is_super_admin))}function d(){const $=typeof _userInfo<"u"?_userInfo:null;return!!($&&$.id===s)}function l($){return typeof escapeHtml=="function"?escapeHtml($==null?"":String($)):String($??"")}function p($,j){try{typeof showToast=="function"&&showToast($,j||"info")}catch{}}async function m($,j){const _=localStorage.getItem("mrpilot_token");if(_&&!(i.loaded[$]&&!j))try{const A=await fetch("/api/erp/mappings/"+$,{headers:{Authorization:"Bearer "+_}});if(!A.ok)throw new Error("http_"+A.status);const q=await A.json();i.items[$]=q.items||[],i.loaded[$]=!0}catch{i.items[$]=[],i.loaded[$]=!1}}async function c($){if(i.clientLoaded)return;const j=localStorage.getItem("mrpilot_token");if(j)try{const _=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+j}});if(!_.ok)throw new Error("http_"+_.status);const A=await _.json();i.clientList=(A.clients||A.items||[]).filter(q=>q.is_active!==!1),i.clientLoaded=!0}catch{i.clientList=[]}}function u(){const $=document.getElementById("erp-map-pane-wrap");if(!$)return;const j=!r();let _="";j&&(_+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+l(t("erp-map-readonly-tip"))+"</div>"),_+='<div class="erp-map-toolbar">',!j&&i.sub!=="products"&&(_+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+l(t("erp-map-add-row"))+"</button>"),_+="</div>",_+='<div class="erp-map-table" id="erp-map-table-host"></div>',$.innerHTML=_,f();const A=document.getElementById("erp-map-dev-bar");A&&(A.style.display=r()&&d()?"":"none")}function f(){const $=document.getElementById("erp-map-table-host");if(!$)return;const j=i.sub,_=i.items[j]||[],A=i.addingNew[j],q=!r();if(!_.length&&!A){$.innerHTML='<div class="erp-map-empty"><strong>'+l(t("erp-map-empty-"+j))+"</strong>"+l(t("erp-map-empty-"+j+"-sub"))+"</div>";return}let F="";F+=b(j),A&&!q&&(F+=L(j)),_.forEach(function(D){F+=I(j,D,q)}),$.innerHTML=F}function b($){return $==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+l(t("erp-map-col-client"))+"</div><div>"+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":$==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-category"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":$==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+l(t("erp-map-col-item-name"))+"</div><div>"+l(t("erp-map-col-erp-product-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-tax"))+"</div><div>"+l(t("erp-map-col-erp-tax-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>"}function B($,j){let _='<select class="form-input" data-erp-field="'+j+'">';return _+='<option value="">'+l(t("erp-map-pick-erp"))+"</option>",e.forEach(function(A){const q=A===$?" selected":"";_+='<option value="'+A+'"'+q+">"+l(n[A])+"</option>"}),_+="</select>",_}function x($){let j='<select class="form-input" data-erp-field="client_id">';return j+='<option value="">'+l(t("erp-map-pick-client"))+"</option>",(i.clientList||[]).forEach(function(_){const A=String(_.id)===String($)?" selected":"";j+='<option value="'+_.id+'"'+A+">"+l(_.name||"#"+_.id)+"</option>"}),j+="</select>",j}function v($){let j='<select class="form-input" data-erp-field="pearnly_category">';return j+='<option value="">'+l(t("erp-map-pick-cat"))+"</option>",a.forEach(function(_){const A=_===$?" selected":"";j+='<option value="'+_+'"'+A+">"+l(t("erp-map-cat-"+_))+"</option>"}),j+="</select>",j}function h($){let j='<select class="form-input" data-erp-field="pearnly_tax_kind">';return j+='<option value="">'+l(t("erp-map-pick-tax"))+"</option>",o.forEach(function(_){const A=_===$?" selected":"";j+='<option value="'+_+'"'+A+">"+l(t("erp-map-tax-"+_))+"</option>"}),j+="</select>",j}function L($){const j='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+l(t("erp-map-save"))+"</button>";return $==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+l(t("erp-map-col-client"))+'">'+x("")+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+B("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+j+"</div></div>":$==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+B("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-category"))+'">'+v("")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+l(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+l(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+j+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+B("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-tax"))+'">'+h("")+'</div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+j+"</div></div>"}function I($,j,_){const A=_?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+l(j.id)+'" title="'+l(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',q='<span class="erp-map-erp-badge">'+l(n[j.erp_type]||j.erp_type)+"</span>";if($==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+l(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+l(j.client_name||"#"+j.client_id)+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+q+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(j.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(j.notes||"")+"</div><div>"+A+"</div></div>";if($==="accounts"){const D=t("erp-map-cat-"+(j.pearnly_category||"other"))||j.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+l(t("erp-map-col-erp"))+'">'+q+'</div><div data-label="'+l(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+l(D)+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(j.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(j.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(j.notes||"")+"</div><div>"+A+"</div></div>"}if($==="products")return'<div class="erp-map-row row-products"><div data-label="'+l(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+l(j.item_name||"")+'</div><div data-label="'+l(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+l(j.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(j.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(j.notes||"")+"</div><div>"+A+"</div></div>";const F=t("erp-map-tax-"+(j.pearnly_tax_kind||""))||j.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+l(t("erp-map-col-erp"))+'">'+q+'</div><div data-label="'+l(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+l(F)+'</span></div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+l(j.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(j.notes||"")+"</div><div>"+A+"</div></div>"}async function S($){const j=i.sub,_={};$.querySelectorAll("[data-erp-field]").forEach(function(D){_[D.dataset.erpField]=(D.value||"").trim()});const A=localStorage.getItem("mrpilot_token");if(!A)return;let q={},F="/api/erp/mappings/"+j;if(j==="clients"){if(!_.client_id||!_.erp_type||!_.erp_code){p(t("erp-map-save-fail"),"error");return}q={client_id:parseInt(_.client_id,10),erp_type:_.erp_type,erp_code:_.erp_code,notes:_.notes||""}}else if(j==="accounts"){if(!_.erp_type||!_.pearnly_category||!_.erp_code){p(t("erp-map-save-fail"),"error");return}q={erp_type:_.erp_type,pearnly_category:_.pearnly_category,erp_code:_.erp_code,erp_name:_.erp_name||"",notes:_.notes||""}}else{if(!_.erp_type||!_.pearnly_tax_kind||!_.erp_code){p(t("erp-map-save-fail"),"error");return}q={erp_type:_.erp_type,pearnly_tax_kind:_.pearnly_tax_kind,erp_code:_.erp_code,notes:_.notes||""}}try{const D=await fetch(F,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+A},body:JSON.stringify(q)});if(!D.ok)throw new Error("http_"+D.status);i.addingNew[j]=!1,await m(j,!0),f(),p(t("erp-map-saved-toast"),"success")}catch{p(t("erp-map-save-fail"),"error")}}async function C($){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const _=i.sub,A=localStorage.getItem("mrpilot_token");try{const q=await fetch("/api/erp/mappings/"+_+"/"+encodeURIComponent($),{method:"DELETE",headers:{Authorization:"Bearer "+A}});if(!q.ok)throw new Error("http_"+q.status);await m(_,!0),f(),p(t("erp-map-deleted-toast"),"success")}catch{p(t("erp-map-delete-fail"),"error")}}async function w(){await c(),await m(i.sub,!1),u()}function g($){$!==i.sub&&(i.sub=$,i.addingNew[$]=!1,["clients","accounts","taxes","products"].forEach(function(j){j!==$&&(i.addingNew[j]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(j){j.classList.toggle("active",j.dataset.erpSubtab===$)}),m($,!1).then(function(){u()}))}function E(){i.bound||(i.bound=!0,document.addEventListener("click",function($){const j=$.target.closest(".erp-subtab[data-erp-subtab]");if(j){$.preventDefault();const D=j.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(V){V.classList.toggle("active",V.dataset.erpSubtab===D)}),document.querySelectorAll(".erp-subpanel").forEach(function(V){V.classList.toggle("active",V.dataset.erpSubpanel===D)}),D==="mappings"&&setTimeout(w,50);return}const _=$.target.closest(".erp-map-subtab[data-erp-subtab]");if(_){$.preventDefault(),g(_.dataset.erpSubtab);return}if($.target.closest("#erp-map-add-btn")){if($.preventDefault(),!r())return;i.addingNew[i.sub]=!0,f();return}const q=$.target.closest('[data-erp-save="new"]');if(q){$.preventDefault();const D=q.closest('[data-erp-row="new"]');D&&S(D);return}const F=$.target.closest("[data-erp-del]");if(F){$.preventDefault(),C(F.dataset.erpDel);return}}))}function M(){const $=document.getElementById("erp-map-pane-wrap");$&&$.children.length>0&&u(),document.querySelectorAll(".erp-map-subtab").forEach(function(j){const _="erp-map-subtab-"+j.dataset.erpSubtab,A=t(_);A&&A!==_&&(j.textContent=A)})}E(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",M)})();(function(){let e=null,n=0,a=!1;function o(w){return typeof escapeHtml=="function"?escapeHtml(w==null?"":String(w)):String(w??"")}function s(w,g){try{typeof showToast=="function"&&showToast(w,g||"info")}catch{}}async function i(w){const g=Date.now();if(e&&g-n<3e4)return e;const E=localStorage.getItem("mrpilot_token");if(!E)return[];try{const M=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+E}});if(!M.ok)return[];const $=await M.json();return e=$&&$.connectors||[],n=g,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function d(w){try{localStorage.setItem("pn_push_default_connector",w||"")}catch{}}function l(w){if(!w||!w.length)return null;const g=r();if(g){const M=w.find($=>$.id===g);if(M)return M}const E=w.find(M=>M.is_default);return E||w[0]}function p(w){if(!w)return!1;const g=String(w.status||"").toLowerCase();return g==="exception"||g==="exception_pending"||g==="rejected"}function m(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(w){const g=w&&(w.type||w.id);return g==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':g==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function u(w,g){if(!w||!g)return!1;const E=document.getElementById("btn-push-default");E&&(E.disabled=!0,E.classList.add("loading"));const M=localStorage.getItem("mrpilot_token");try{let $,j={method:"POST",headers:{Authorization:"Bearer "+M}};w.type==="xero"?$="/api/erp/xero/push/"+encodeURIComponent(g):($="/api/erp/push",j.headers["Content-Type"]="application/json",j.body=JSON.stringify({history_id:g,endpoint_id:w.endpoint_id||void 0}));const _=await fetch($,j);let A={};try{A=await _.json()}catch{}if(!_.ok){let q=A&&A.detail||"unknown";typeof q=="object"&&(q=q.code||JSON.stringify(q));let F=String(q||"unknown");if(w.type==="xero"){const D=F.replace(/^xero\./,"").toLowerCase(),V=t("xero-"+D);V&&V!=="xero-"+D&&(F=V)}return s(t("unified-push-fail").replace("{name}",w.name).replace("{err}",F),"error"),!1}if(A&&A.ok===!1){let q=A.error_msg||A.error_code||"unknown";return q=String(q).slice(0,200),s(t("unified-push-fail").replace("{name}",w.name).replace("{err}",q),"error"),!1}return s(t("unified-push-ok").replace("{name}",w.name),"success"),!0}catch($){return s(t("unified-push-fail").replace("{name}",w.name).replace("{err}",$.message||"network"),"error"),!1}finally{E&&(E.disabled=!1,E.classList.remove("loading"))}}async function f(w,g){for(const E of w)await u(E,g)}function b(w,g){const E=document.createElement("div");E.className="pn-push-dropdown",E.id="pn-push-dropdown";const M=(w||[]).map(j=>{const _=!!(g&&j.id===g.id),A=j.method==="download"?t("unified-push-tag-download"):_?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(j.id)+'"><span class="pn-pd-icon">'+c(j)+'</span><span class="pn-pd-name">'+o(j.name)+"</span>"+(A?'<span class="pn-pd-tag">'+o(A)+"</span>":"")+(_?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),$=w&&w.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",w.length))+"</span></div>":"";return E.innerHTML=M+$,E}function B(){const w=document.getElementById("pn-push-dropdown");w&&w.remove()}async function x(){if(document.getElementById("pn-push-dropdown")){B();return}const w=await i()||[],g=l(w),E=b(w,g),M=document.getElementById("pn-push-wrap");M&&M.appendChild(E)}async function v(){const w=await i()||[],g=l(w);if(!g)return;const E=m(),M=E&&(E._historyId||E.history_id);if(M){if(p(E)){s(t("unified-push-disabled-exc"),"warn");return}await u(g,M)}}async function h(w){B();const g=await i()||[],E=m(),M=E&&(E._historyId||E.history_id);if(!M)return;if(p(E)){s(t("unified-push-disabled-exc"),"warn");return}if(w==="__all__"){await f(g,M);return}const $=g.find(j=>j.id===w);$&&(d(w),await u($,M),I())}async function L(){const w=document.getElementById("drawer-history-save");if(!w||w.querySelector("#pn-push-wrap"))return;const g=document.createElement("div");g.id="pn-push-wrap",g.className="pn-push-wrap",g.dataset.loading="1",w.insertBefore(g,w.firstChild),["btn-push-erp","btn-xero-push"].forEach(A=>{w.querySelectorAll("#"+A).forEach(q=>{q.style.display="none"})});const E=await i()||[],M=l(E),$=E.length>0;if(!$)g.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const A=E.length>1;g.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+c(M)+"<span>"+o(t("unified-push-to").replace("{name}",M?M.name:""))+"</span></button>"+(A?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete g.dataset.loading;const j=g.querySelector("#btn-push-default");j&&$&&j.addEventListener("click",v);const _=g.querySelector("#btn-push-arrow");_&&_.addEventListener("click",function(A){A.stopPropagation(),x()}),a||(a=!0,document.addEventListener("click",function(A){const q=A.target.closest(".pn-pd-item");if(q){const F=q.getAttribute("data-cid");h(F);return}A.target.closest("#btn-push-arrow")||B()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",I))}function I(){const w=document.getElementById("pn-push-wrap");w&&(w.remove(),e=null,n=0,L())}function S(){const w=document.getElementById("drawer-history-save");if(!w||!w.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(E=>{w.querySelectorAll("#"+E).forEach(M=>{M.style.display!=="none"&&(M.style.display="none")})});const g=w.querySelectorAll("#pn-push-wrap");if(g.length>1)for(let E=1;E<g.length;E++)g[E].remove()}function C(){try{const w=function(){return document.getElementById("drawer-body")},g=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&L(),S()}),E=w();if(E)g.observe(E,{childList:!0,subtree:!0});else{const M=new MutationObserver(function(){const $=w();$&&(g.observe($,{childList:!0,subtree:!0}),M.disconnect())});M.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&L(),S()},200)}catch{}}C()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",d=t(r);d&&d!==r&&(i.textContent=d)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const l=document.getElementById("erp-onboard-title"),p=document.getElementById("erp-onboard-body"),m=document.getElementById("erp-onboard-ok"),c=document.getElementById("erp-onboard-later");l&&(l.textContent=t("erp-onboard-title")),p&&(p.textContent=t("erp-onboard-body")),m&&(m.textContent=t("erp-onboard-ok")),c&&(c.textContent=t("erp-onboard-later"))}r();function d(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}d();try{const l=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');l&&l.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}d()}),i.addEventListener("click",function(l){l.target===i&&d()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),d=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||d)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,i=s[a]||s.th||s.en,r=n.stage_total,d=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const l={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+l.replace("{d}",d||0).replace("{t}",r)}return i},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,i=o.maxMs||1200*1e3,r=Date.now();let d=0;for(;;){let l=null;try{const p=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{l=await p.json()}catch{l=null}(!p.ok||!l||!l.ok)&&(l=null)}catch{l=null}if(l){if(d=0,o.onProgress)try{o.onProgress(l.progress||{},l)}catch{}if(l.status==="done"||l.status==="failed"||l.status==="needs_review"||l.status==="needs_mapping")return l}else if(++d>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(p=>setTimeout(p,s))}}})();const oe={initialized:!1,stmtFiles:[],glFiles:[],currentTask:null,currentFilter:"all",allRows:[],brv2Search:{stmt:"",gl:""},cachedHistoryTasks:[],brv2Page:1},ne=e=>document.getElementById(e);function Ae(e){if(e==null)return"—";const n=Number(e);return isNaN(n)?"—":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function on(e){return e?String(e).slice(0,10).split("-").reverse().join("/"):"—"}function me(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function ls(e,n){n=window._currentLang||n||"th";const a={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},o={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},s=a[e]||o;return s[n]||s.th||s.en}function cs(e){return e?e<1024?e+" B":e<1048576?(e/1024).toFixed(1)+" KB":(e/1048576).toFixed(1)+" MB":""}function Fe(e,n){return window.t&&window.t(e)||n}function $e(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function It(e){return Number.isFinite(+e)?(+e).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}var On="pearnly.brv2.lastAnchorOcr";function ds(e){try{var n=e&&e._anchor_ocr;if(!n||typeof n!="object")return;var a={stmt_opening:Number.isFinite(+n.stmt_opening)?+n.stmt_opening:null,gl_opening:Number.isFinite(+n.gl_opening)?+n.gl_opening:null,gl_closing:Number.isFinite(+n.gl_closing)?+n.gl_closing:null,stmt_closing:Number.isFinite(+n.stmt_closing)?+n.stmt_closing:null,ts:Date.now()};localStorage.setItem(On,JSON.stringify(a))}catch{}}function ps(){try{var e=localStorage.getItem(On);if(!e)return null;var n=JSON.parse(e);return!n||typeof n!="object"?null:n}catch{return null}}function us(){var e=ps();if(e){var n={"brv2-anchor-stmt-opening":e.stmt_opening,"brv2-anchor-gl-opening":e.gl_opening,"brv2-anchor-gl-closing":e.gl_closing,"brv2-anchor-stmt-closing":e.stmt_closing},a=0;Object.keys(n).forEach(function(d){var l=document.getElementById(d);if(l&&l.value===""){var p=n[d];if(Number.isFinite(p)){l.value=p.toFixed(2);var m=l.closest&&l.closest(".brv2-anchor-cell");m&&m.classList.add("is-prefilled"),a+=1}}});var o=document.getElementById("brv2-anchor-eq"),s=document.getElementById("brv2-anchor-eq-val");if(o&&s&&Number.isFinite(e.stmt_opening)&&Number.isFinite(e.gl_opening)){var i=e.stmt_opening-e.gl_opening;s.textContent=i.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),o.style.display=""}if(a>0){var r=document.getElementById("brv2-anchor-prefill-banner");r&&r.classList.add("show")}}}function fs(){var e=document.getElementById("brv2-anchor-prefill-banner");if(e){var n=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(a){var o=document.getElementById(a);if(o){var s=o.closest&&o.closest(".brv2-anchor-cell");s&&s.classList.contains("is-prefilled")&&(n=!0)}}),e.classList.toggle("show",n)}}var ms=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function vs(e){var n=document.getElementById("brv2-summary-collapse");if(!(!n||!n.parentNode)){var a=document.getElementById("brv2-anchor-audit"),o=e&&e._anchor_overrides;if(!o||typeof o!="object"||Object.keys(o).length===0){a&&a.parentNode&&a.parentNode.removeChild(a);return}a||(a=document.createElement("div"),a.id="brv2-anchor-audit",a.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",n.parentNode.insertBefore(a,n.nextSibling));var s=ms.map(function(i){var r=o[i[0]];if(!r)return"";var d=+r.ocr||0,l=+r.user||0,p=l-d,m=p>0?"+":(p<0,""),c=Math.abs(p)<.005?"#6b7280":p>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+$e(Fe(i[1],i[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+$e(It(d))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+$e(It(l))+'</td><td style="padding:6px 10px;color:'+c+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+$e(m+It(p))+"</td></tr>"}).join("");a.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+$e(Fe("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+$e(Fe("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+$e(Fe("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+$e(Fe("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+$e(Fe("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+s+"</tbody></table>"}}function ft(e){const n=ne("brv2-summary-collapse"),a=ne("brv2-detail-collapse"),o=ne("brv2-export-btn"),s=ne("brv2-new-btn"),i=ne("brv2-parse-info-wrap");n&&(n.style.display=e?"":"none"),a&&(a.style.display=e?"":"none"),o&&(o.style.display=e?"":"none"),s&&(s.style.display=e?"":"none"),!e&&i&&(i.style.display="none");const r=ne("brv2-warnings");!e&&r&&(r.style.display="none",r.innerHTML="")}function hs(e){const n=ne("brv2-parse-info-wrap"),a=ne("brv2-parse-info-body");if(!n||!a)return;const o=e.parse_info;if(!o){n.style.display="none";return}const s=window._currentLang||"zh",i={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},r=u=>(i[u]||{})[s]||(i[u]||{}).zh||u,d=[...(o.stmt_files||[]).map(u=>({...u,_type:"stmt",_extra:u.bank_code||""})),...(o.gl_files||[]).map(u=>({...u,_type:"gl",_extra:(u.accounts||[]).join(", ")}))],l={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},p=u=>{const f=String(u||"");return/Cannot detect bank statement column headers/i.test(f)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(f)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(f)?"stmt_no_rows":/unsupported format/i.test(f)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(f)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(f)?"ocr_failed":null},m=u=>{const f=u.error_code||p(u.error);if(f&&l[f]){const b=window._currentLang||"zh";return l[f][b]||l[f].zh}return String(u.error||"").slice(0,80)},c=u=>!u.ok&&u.error?`<span style="color:#dc2626">${r("fail")} — ${me(m(u))}</span>`:u.rows?`<span style="color:#059669">${r("ok")} (${u.rows})</span>`:`<span style="color:#d97706">${r("warn")}</span>`;a.innerHTML=`
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
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${me(u.file||"")}">${me(u.file||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${u.rows||0}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${me(u._extra||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb">${c(u)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`,n.style.display=""}async function Vn(e){const n=localStorage.getItem("mrpilot_token")||"",a=window._currentLang||"zh";try{const o=await fetch("/api/recon/bank-v2/"+e+"/export?lang="+a,{headers:{Authorization:"Bearer "+n}});if(!o.ok){const m=await o.json().catch(()=>({}));window.showToast&&window.showToast(m.detail||"Export failed","error");return}const s=await o.blob(),r=(o.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),d=r?r[1].replace(/['"]/g,""):"reconciliation.xlsx",l=URL.createObjectURL(s),p=document.createElement("a");p.href=l,p.download=d,document.body.appendChild(p),p.click(),document.body.removeChild(p),URL.revokeObjectURL(l)}catch(o){window.showToast&&window.showToast("Export error: "+o.message,"error")}}function gs(e,n){const a=ne("brv2-summary-collapse");let o=ne("brv2-warnings");const s=window._currentLang||"zh",i={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[s]||"⏭ ",r=[];if((n||[]).forEach(d=>r.push(i+" "+d)),(e||[]).forEach(d=>r.push(d)),!r.length){o&&(o.style.display="none");return}if(!o)if(o=document.createElement("div"),o.id="brv2-warnings",a&&a.parentNode)a.parentNode.insertBefore(o,a);else return;o.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",o.innerHTML=r.map(d=>"<div>"+me(d)+"</div>").join("")}function Wt(e){hs(e),gs(e.warnings||[],e.skipped_files||[]),!e.ok&&e.error&&window.showToast&&window.showToast(e.error,"error");const n=e.stats||{},a=e.summary||{},o=n.matched||0,s=(n.gl_debit_only||0)+(n.gl_credit_only||0),i=(n.stmt_withdrawal_only||0)+(n.stmt_deposit_only||0),r=Number(a.formula_diff||0),d=Math.abs(r)<.05;ne("brv2-kpi-matched")&&(ne("brv2-kpi-matched").textContent=o),ne("brv2-kpi-diff")&&(ne("brv2-kpi-diff").textContent=Ae(r)),ne("brv2-kpi-unmatched")&&(ne("brv2-kpi-unmatched").textContent=s+i);const l=ne("brv2-kpi-diff-icon");l&&(l.style.background=d?"#d1fae5":"#fee2e2",l.style.color=d?"#065f46":"#b91c1c");const p=ne("brv2-formula-sub");if(p){const b=window._currentLang||"zh";p.textContent=d?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[b]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[b]||"差 ")+Ae(r)}const m=ne("brv2-detail-sub");if(m){const b=window._currentLang||"zh",B={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[b]||"共 {n} 行";m.textContent=B.replace("{n}",oe.allRows.length)}function c(b,B,x){const v=ne(b);v&&(v.textContent=(x&&B>0?"(":"")+Ae(x?-B:B)+(x&&B>0?")":""))}c("brf-gl-close",a.gl_closing||0),c("brf-open-diff",a.opening_diff||0),c("brf-gl-debit-only",a.gl_debit_only_amount||0,!0),c("brf-gl-credit-only",a.gl_credit_only_amount||0),c("brf-stmt-wd-only",a.stmt_withdrawal_only_amount||0,!0),c("brf-stmt-dep-only",a.stmt_deposit_only_amount||0),c("brf-calc-close",a.formula_stmt_closing||0),c("brf-stmt-close",a.stmt_closing||0),ne("brf-diff")&&(ne("brf-diff").textContent=Ae(r));const u=ne("brv2-fcell-diff");u&&u.classList.toggle("brv2-fcell-diff-ok",d);const f=ne("brv2-export-btn");f&&(f.onclick=()=>{oe.currentTask&&Vn(oe.currentTask.task_id)}),vs(a),ft(!0),Un()}function Un(){const e=ne("brv2-tbody");if(!e)return;const n=oe.allRows.filter(i=>oe.currentFilter==="all"?!0:oe.currentFilter==="matched"?i.match_status==="matched":oe.currentFilter==="gl_only"?i.match_status.startsWith("gl_"):oe.currentFilter==="stmt_only"?i.match_status.startsWith("stmt_"):!0);if(n.length===0){const i={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";e.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${i}</td></tr>`;return}const a=window._currentLang||"zh",o={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[a],s={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[a];e.innerHTML=n.map(i=>{const r=i.match_status,d=i.match_layer;let l="",p="";r==="matched"?(d===1&&(l="matched",p='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),d===2&&(l="matched-l2",p='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),d===3&&(l="matched-l3",p='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):r==="gl_debit_only"||r==="gl_credit_only"?(l="gl-only",p='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(l="stmt-only",p=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[a]||"账单"}</span>`);let m="";return i.stmt_balance_ok===!1&&(m+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${me(o)}">⚠</span>`,l+=" brv2-row-warn"),i.stmt_confidence==="low"&&(m+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${me(s)}">◌</span>`,l.includes("brv2-row-warn")||(l+=" brv2-row-warn-soft")),`<tr class="${l.trim()}">
          <td>${p}${m}</td>
          <td>${me(on(i.stmt_date))}</td>
          <td title="${me(i.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${me(i.stmt_desc)}</td>
          <td class="num">${i.stmt_withdrawal?Ae(i.stmt_withdrawal):""}</td>
          <td class="num">${i.stmt_deposit?Ae(i.stmt_deposit):""}</td>
          <td>${me(on(i.gl_date))}</td>
          <td title="${me(i.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${me(i.gl_doc_no)}</td>
          <td class="num">${i.gl_debit?Ae(i.gl_debit):""}</td>
          <td class="num">${i.gl_credit?Ae(i.gl_credit):""}</td>
          <td>${d?"L"+d:"—"}</td>
        </tr>`}).join("")}async function Qe(){const e=localStorage.getItem("mrpilot_token")||"";try{const a=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+e}})).json();mt(a.tasks||[])}catch{const a=ne("brv2-history-empty"),o=window._currentLang||"zh",s={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[o]||"加载失败";a&&(a.textContent=s,a.style.display="");const i=ne("brv2-history-table-wrap");i&&(i.style.display="none")}}const Ne=10;function sn(){const e=ne("brv2-history-pager"),n=ne("brv2-history-pager-info"),a=ne("brv2-history-prev"),o=ne("brv2-history-next");if(!e)return;if(oe.cachedHistoryTasks.length<=Ne){e.style.display="none";return}e.style.display="";const s=Math.ceil(oe.cachedHistoryTasks.length/Ne);n&&(n.textContent=oe.brv2Page+" / "+s),a&&(a.disabled=oe.brv2Page<=1),o&&(o.disabled=oe.brv2Page>=s)}function bs(){const e=ne("brv2-history-prev"),n=ne("brv2-history-next");e&&!e._brv2Bound&&(e._brv2Bound=!0,e.addEventListener("click",()=>{oe.brv2Page>1&&(oe.brv2Page--,mt(oe.cachedHistoryTasks))})),n&&!n._brv2Bound&&(n._brv2Bound=!0,n.addEventListener("click",()=>{const a=Math.ceil(oe.cachedHistoryTasks.length/Ne);oe.brv2Page<a&&(oe.brv2Page++,mt(oe.cachedHistoryTasks))}))}function mt(e){e!==void 0&&(oe.cachedHistoryTasks=e||[],oe.brv2Page=1);const n=oe.cachedHistoryTasks,a=ne("brv2-history-empty"),o=ne("brv2-history-table-wrap"),s=ne("brv2-history-tbody");if(!s)return;const i=window._currentLang||"zh";if(!n.length){const f={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[i]||"暂无对账记录";a&&(a.textContent=f,a.style.display=""),o&&(o.style.display="none"),sn();return}a&&(a.style.display="none"),o&&(o.style.display="");const r=Math.ceil(n.length/Ne);oe.brv2Page>r&&(oe.brv2Page=r);const d=(oe.brv2Page-1)*Ne,l=n.slice(d,d+Ne),p=localStorage.getItem("mrpilot_token")||"",m='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',c='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',u='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';s.innerHTML="",l.forEach(f=>{const b=Number(f.formula_diff||0),B=Math.abs(b)<.05,x=(f.stmt_files||"").split(";").map(D=>D.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),v=(f.gl_files||"").split(";").map(D=>D.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),h=f.created_at?String(f.created_at).slice(0,16).replace("T"," "):"",L=document.createElement("tr");L.dataset.taskId=f.id;const I=document.createElement("td");I.textContent=h;const S=document.createElement("td");S.className="glv-history-file",S.title=x+" + "+v,S.textContent=x+" + "+v;const C=document.createElement("td");C.className="glv-num",C.textContent=(f.stmt_row_count||0)+" / "+(f.gl_row_count||0);const w=document.createElement("td");w.className="glv-num",w.textContent=f.matched_count||0;const g=document.createElement("td");g.className="glv-num",g.textContent=f.unmatched_gl||0;const E=document.createElement("td");E.className="glv-num",E.textContent=f.unmatched_stmt||0;const M=document.createElement("td");M.className="glv-num",M.style.color=B?"#059669":"#dc2626",M.textContent=B?"✓":Ae(b);const $=document.createElement("td");$.className="glv-history-actions";const j=(D,V,Y,T)=>{const k=document.createElement("button");return k.type="button",k.title=V,k.setAttribute("aria-label",V),Y&&(k.className=Y),k.innerHTML=D,k.onclick=y=>{y.stopPropagation(),T()},k},_={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[i]||"删除?",A={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[i]||"加载",q={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[i]||"导出",F={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[i]||"删除";$.appendChild(j(m,A,"",()=>rn(f.id,p))),$.appendChild(j(c,q,"",()=>Vn(f.id))),$.appendChild(j(u,F,"glv-del",async()=>{await showConfirm(_,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+f.id,{method:"DELETE",headers:{Authorization:"Bearer "+p}}),Qe())})),[I,S,C,w,g,E,M,$].forEach(D=>L.appendChild(D)),L.style.cursor="pointer",L.addEventListener("click",async D=>{D.target.closest(".glv-del")||D.target.closest("button")||await rn(f.id,p)}),s.appendChild(L)}),sn(),Gn()}function Gn(){const e=((ne("brv2-hist-search")||{}).value||"").trim().toLowerCase(),n=ne("brv2-history-tbody");n&&n.querySelectorAll("tr").forEach(a=>{a.dataset.taskId&&(a.style.display=!e||a.textContent.toLowerCase().includes(e)?"":"none")})}async function rn(e,n){try{const o=await(await fetch("/api/recon/bank-v2/"+e,{headers:{Authorization:"Bearer "+n}})).json();if(!o.ok)return;oe.currentTask={task_id:o.task_id,...o},oe.allRows=o.detail||[],oe.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(s=>s.classList.toggle("active",s.dataset.filter==="all")),Wt(oe.currentTask)}catch{}}function Me(e){const n=e==="stmt"?oe.stmtFiles:oe.glFiles,a=ne(`brv2-${e}-name`);if(a)if(n.length===0)a.textContent="";else{const s=window._currentLang||"zh",i={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};a.textContent=n.length+(i[s]||" 个文件")}const o=ne("brv2-preview-panel");o&&o.style.display!=="none"&&Ht(e),ys()}function ys(){const e=ne("brv2-toggle-preview"),n=ne("brv2-preview-panel"),a=oe.stmtFiles.length+oe.glFiles.length>0;e&&(e.style.display=a?"":"none"),!a&&n&&(n.style.display="none",e&&e.classList.remove("open"))}function ws(){Ht("stmt"),Ht("gl")}function Ht(e){const n=ne(e==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!n)return;const a=e==="stmt"?oe.stmtFiles:oe.glFiles,o=window._currentLang||"zh",s={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},i=(s[e]||{})[o]||s[e].zh,r=me(window.t&&window.t("vex-preview-search")||"搜索文件名..."),d=me(window.t&&window.t("vex-preview-clear-all")||"全清"),l=oe.brv2Search[e]||"";n.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+me(i)+' <span class="vex-pp-col-count">'+a.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+e+'" type="text" placeholder="'+r+'" value="'+me(l)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+e+'" type="button">'+d+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+e+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+e+'-pg"></div>';const p=ne("brv2-pp-search-"+e);p&&p.addEventListener("input",function(c){oe.brv2Search[e]=c.target.value,ln(e)});const m=ne("brv2-pp-clearall-"+e);m&&m.addEventListener("click",function(){e==="stmt"?oe.stmtFiles.length=0:oe.glFiles.length=0,Me(e),je()}),ln(e)}function ln(e){const n=ne("brv2-pp-"+e+"-list"),a=ne("brv2-pp-"+e+"-pg");if(!n)return;const o=e==="stmt"?oe.stmtFiles:oe.glFiles,s=(oe.brv2Search[e]||"").toLowerCase(),i=s?o.filter(l=>l.name.toLowerCase().includes(s)):o.slice(),r='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',d='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(n.innerHTML=i.map((l,p)=>'<div class="vex-pp-file-row">'+r+'<span class="vex-pp-fi-name" title="'+me(l.name)+'">'+me(l.name)+'</span><span class="vex-pp-fi-size">'+cs(l.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+e+'" data-idx="'+o.indexOf(l)+'" aria-label="remove">'+d+"</button></div>").join(""),n.querySelectorAll(".vex-pp-fi-del").forEach(function(l){l.addEventListener("click",function(){const p=parseInt(l.dataset.idx,10);l.dataset.zone==="stmt"?oe.stmtFiles.splice(p,1):oe.glFiles.splice(p,1),Me(l.dataset.zone),je()})}),a){const l=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";a.textContent=l.replace("{n}",i.length).replace("{m}",o.length)}}function ks(){const e=ne("brv2-toggle-preview");e&&!e._reconBound&&(e._reconBound=!0,e.addEventListener("click",function(){const n=ne("brv2-preview-panel"),a=ne("brv2-toggle-preview-label"),o=n&&n.style.display!=="none";n&&(n.style.display=o?"none":""),e.classList.toggle("open",!o),a&&(a.textContent=o?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),o||ws()}))}function je(){const e=ne("brv2-run-btn"),n=ne("brv2-status"),a=oe.stmtFiles.length>0,o=oe.glFiles.length>0;if(e&&(e.disabled=!(a&&o)),n){const s=window._currentLang||"zh";if(!a&&!o){const i={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};n.textContent=i[s]||i.zh}else if(a)if(o){const i={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};n.textContent=i[s]||i.zh}}}function cn(e,n,a){const o=ne(e),s=ne(n);!o||!s||(o.addEventListener("click",()=>s.click()),o.addEventListener("keydown",i=>{(i.key==="Enter"||i.key===" ")&&(i.preventDefault(),s.click())}),o.addEventListener("dragover",i=>{i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",()=>o.classList.remove("drag-over")),o.addEventListener("drop",i=>{i.preventDefault(),o.classList.remove("drag-over");const r=Array.from(i.dataTransfer.files||[]);a==="stmt"?oe.stmtFiles.push(...r):oe.glFiles.push(...r),Me(a),je()}),s.addEventListener("change",()=>{const i=Array.from(s.files||[]);a==="stmt"?oe.stmtFiles.push(...i):oe.glFiles.push(...i),s.value="",Me(a),je()}))}function Ee(e){const n=ne("brv2-progress"),a=ne("brv2-run-btn"),o=ne("brv2-error");n&&(n.style.display=e?"":"none"),a&&(a.disabled=e),o&&(o.style.display="none")}function Te(e){const n=ne("brv2-error");n&&(n.textContent=e,n.style.display="",n.scrollIntoView({behavior:"smooth",block:"nearest"})),Ee(!1),je(),window.showToast&&window.showToast(e,"error")}async function At(){if(oe.stmtFiles.length===0||oe.glFiles.length===0)return;const e=localStorage.getItem("mrpilot_token")||"",n=window._currentLang||"zh",a=(ne("brv2-acct-select")||{}).value||"";ft(!1),Ee(!0);try{const o=new FormData;oe.stmtFiles.forEach(f=>o.append("stmt_files",f)),oe.glFiles.forEach(f=>o.append("gl_files",f)),o.append("gl_account",a),o.append("lang",n);const s=parseFloat((ne("brv2-anchor-gl-closing")||{}).value),i=parseFloat((ne("brv2-anchor-stmt-closing")||{}).value),r=parseFloat((ne("brv2-anchor-stmt-opening")||{}).value),d=parseFloat((ne("brv2-anchor-gl-opening")||{}).value);Number.isFinite(s)&&o.append("gl_closing_override",s),Number.isFinite(i)&&o.append("stmt_closing_override",i),Number.isFinite(r)&&o.append("stmt_opening_override",r),Number.isFinite(d)&&o.append("gl_opening_override",d);const l=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+e},body:o});let p=null;try{p=await l.json()}catch{p=null}if(p&&p.needs_mapping){Ee(!1),window.ReconMapping?window.ReconMapping.show(p,{token:e,lang:n,onConfirmed:function(){At()}}):Te(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!l.ok||!p||!p.ok||!p.job_id){Ee(!1),p&&(p.detail||p.error)?Te(_humanizeBackendError(p.detail||p.error,"Error "+l.status)):Te(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const m=ne("brv2-progress-sub"),c=await window._reconPollJob(p.job_id,e,{onProgress:f=>{m&&(m.textContent=window._reconProgressText(f,n))}});if(c&&c.status==="needs_mapping"&&c.mapping){Ee(!1),window.ReconMapping?window.ReconMapping.show(c.mapping,{token:e,lang:n,onConfirmed:function(){At()}}):Te(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(c&&c.status==="needs_review"&&c.review){Ee(!1),window.ReconReview?window.ReconReview.show(c.review,{token:e,lang:n,jobId:p.job_id,onConfirmed:async function(f){Ee(!0);const b=await window._reconPollJob(f,e,{onProgress:B=>{m&&(m.textContent=window._reconProgressText(B,n))}});await u(b)}}):Te(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(c&&c.status==="failed"){Ee(!1),Te(ls(c.error_code,n));return}await u(c);async function u(f){try{if(!f||f.status!=="done"||!f.result_id){Ee(!1),Te(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const b=await fetch("/api/recon/bank-v2/"+encodeURIComponent(f.result_id),{headers:{Authorization:"Bearer "+e}});let B=null;try{B=await b.json()}catch{B=null}if(!b.ok||B===null||!B.ok){Ee(!1),Te(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(B.gl_accounts||[]).length>1&&xs(B.gl_accounts),oe.currentTask=B,oe.allRows=B.detail||[],oe.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(v=>v.classList.toggle("active",v.dataset.filter==="all")),ds(B&&B.summary),Ee(!1),Wt(B),Qe();const x=ne("brv2-summary-collapse");x&&x.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(b){Ee(!1),Te(b.message||"Network error")}}}catch(o){Te(o.message||"Network error")}}function xs(e){const n=ne("brv2-acct-select");if(!n)return;const a=window._currentLang||"zh",o={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[a]||"全部账户";n.innerHTML=`<option value="">${o}</option>`+e.map(s=>`<option value="${me(s)}">${me(s)}</option>`).join(""),n.style.display=""}function Xt(){if(oe.initialized){Qe();return}oe.initialized=!0,cn("brv2-stmt-zone","brv2-stmt-input","stmt"),cn("brv2-gl-zone","brv2-gl-input","gl");const e=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function n(){const d=parseFloat((ne("brv2-anchor-stmt-opening")||{}).value),l=parseFloat((ne("brv2-anchor-gl-opening")||{}).value),p=ne("brv2-anchor-eq"),m=ne("brv2-anchor-eq-val");if(!(!p||!m))if(Number.isFinite(d)&&Number.isFinite(l)){const c=d-l;m.textContent=c.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),p.style.display=""}else p.style.display="none"}e.forEach(d=>{const l=ne(d);l&&(l.addEventListener("input",n),l.addEventListener("input",()=>{const p=l.closest(".brv2-anchor-cell");p&&p.classList.remove("is-prefilled"),fs()}))}),us();const a=ne("brv2-run-btn");a&&a.addEventListener("click",At);const o=ne("brv2-reset-btn");o&&o.addEventListener("click",()=>{oe.currentTask=null,oe.allRows=[],oe.stmtFiles=[],oe.glFiles=[],Me("stmt"),Me("gl"),je(),ft(!1);const d=ne("brv2-acct-select");d&&(d.style.display="none"),e.forEach(m=>{const c=ne(m);if(c){c.value="";const u=c.closest&&c.closest(".brv2-anchor-cell");u&&u.classList.remove("is-prefilled")}});const l=ne("brv2-anchor-eq");l&&(l.style.display="none");const p=ne("brv2-anchor-prefill-banner");p&&p.classList.remove("show")});const s=ne("brv2-new-btn");s&&s.addEventListener("click",()=>{oe.currentTask=null,oe.allRows=[],oe.stmtFiles=[],oe.glFiles=[],Me("stmt"),Me("gl"),je(),ft(!1)});const i=ne("brv2-filter-tabs");i&&i.addEventListener("click",d=>{d.stopPropagation();const l=d.target.closest(".brv2-filter-btn");l&&(oe.currentFilter=l.dataset.filter,i.querySelectorAll(".brv2-filter-btn").forEach(p=>p.classList.toggle("active",p===l)),Un())}),ks(),bs();const r=ne("brv2-hist-search");r&&r.addEventListener("input",Gn),Qe(),je(),window._brv2LoadHistory=Qe,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(d=>d.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){je(),Me("stmt"),Me("gl"),oe.currentTask&&Wt(oe.currentTask),mt()}})}window._loadBankReconV2Panel=function(e){const n=e?document.getElementById(e):null;n&&n.id!=="recon-pane-bank"&&(n.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
            银行对账 v2 · 请前往对账中心使用</div>`),Xt()};document.addEventListener("DOMContentLoaded",()=>{ne("brv2-run-btn")&&Xt()});window._bankReconV2Init=Xt;(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const p=document.getElementById("general-tz"),m=document.getElementById("general-date"),c=document.getElementById("general-number");if(!(!p||!m||!c))try{p.value=localStorage.getItem(n)||s.tz,m.value=localStorage.getItem(a)||s.date,c.value=localStorage.getItem(o)||s.number}catch{p.value=s.tz,m.value=s.date,c.value=s.number}}async function r(){const p=document.getElementById("btn-save-general"),m=document.getElementById("general-save-msg");if(!p)return;const c=p.innerHTML;p.disabled=!0,p.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",m&&(m.textContent="",m.classList.remove("error"));try{const u=(document.getElementById("general-tz")||{}).value||s.tz,f=(document.getElementById("general-date")||{}).value||s.date,b=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,u),localStorage.setItem(a,f),localStorage.setItem(o,b)}catch{}window._pearnlyGeneral={tz:u,date_format:f,number_format:b},m&&(m.textContent=t("msg-saved")||"已保存")}catch{m&&(m.textContent=t("msg-save-failed")||"保存失败",m.classList.add("error"))}finally{p.disabled=!1,p.innerHTML=c,setTimeout(function(){m&&(m.textContent="")},3e3)}}function d(){const p=document.getElementById("btn-save-general");if(!p){setTimeout(d,200);return}p._pearnlyGenBound||(p._pearnlyGenBound=!0,p.addEventListener("click",r),i())}function l(){i();const p=document.getElementById("general-lang");if(p){const m=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";p.value=m}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",d):d(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",l)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(d){const l=d.dataset.collapsible;r[l]?d.classList.add("collapsed"):d.classList.remove("collapsed")})}function i(r){const d=a();d[r]=!d[r],o(d),s()}(function(){const d=a();let l=!1;d.sales===void 0&&(d.sales=!1,l=!0),d.expense===void 0&&(d.expense=!0,l=!0),l&&o(d)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const d=n[r];if(!d)return;const l=a();l[d]&&(l[d]=!1,o(l),s())}})();const _s=`
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
    </div>`;function dn(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=_s;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,dn();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const i=o.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let Ie=[];window._erpEndpoints=Ie;let ot=null;async function kt(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}Ie=(await e.json()).items||[],window._erpEndpoints=Ie,Jn()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return kt()};async function Kn(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const d=[];d.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&d.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&d.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&d.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=d.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function Jn(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&Ie.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(Ie.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=Ie.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:Ie.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),Kn(),e.innerHTML=Ie.map(s=>{const i=s.config||{},r=escapeHtml(i.url||"");i._token_set;const d=s.enabled!==!1,l=[];s.is_default&&l.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&l.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),d||l.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const p=[];return s.success_count>0&&p.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&p.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=Ie.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,d=document.createElement("div");d.className="erp-limit-hint",r==="free"?d.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:d.textContent=t("ep-plus-limit-hint",{used:s,limit:i}),e.appendChild(d)}}function Es(e){ot=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),d=document.getElementById("ep-auto-push"),l=document.getElementById("ep-test-result");l.style.display="none",l.textContent="";const p=document.getElementById("ep-save-error");if(p&&p.remove(),e){const c=Ie.find(u=>u.id===e);if(!c)return;o.value=c.name||"",s.value=(c.config||{}).url||"",i.value=(c.config||{})._token_set&&c.config.token||"",i.placeholder=(c.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!c.is_default,d.checked=!!c.auto_push}else o.value="",s.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=Ie.length===0,d.checked=!0;const m=d.closest(".form-switch-row");if(d.disabled=!1,m){m.classList.remove("disabled-plus"),m.title="",m.style.cursor="",m.onclick=null;const c=m.querySelector(".plus-badge");c&&c.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function Yn(){document.getElementById("endpoint-modal").style.display="none",ot=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function Wn(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function Xn(){const e=document.getElementById("ep-name").value.trim(),n=Wn(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:i}}async function Bs(){const{url:e,config:n}=Xn(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function Is(){const e=Xn(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){pn(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let i;if(ot?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(ot)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const d=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof d=="string"?d:JSON.stringify(d))}Yn(),showToast(t("ep-save-ok")),kt()}catch(i){pn(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function pn(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function Ls(e){const n=Ie.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),kt()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=kt;window.loadErpTodayStats=Kn;window.renderErpEndpointsList=Jn;window.openEndpointModal=Es;window.closeEndpointModal=Yn;window.saveEndpoint=Is;window.deleteEndpoint=Ls;window.testEndpointConnection=Bs;window._sanitizeUrl=Wn;async function Zn(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function Cs(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){Zn(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const i=s.dataset.receiptAction;i==="retry"?window.retryPushLog(s.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(j=>j.id===o.endpoint_id),i=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),d=new Date(o.created_at).toLocaleString(),l=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),p=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),m=o.response_body||t("erp-receipt-no-tech"),c=o.status==="success";let u=typeof m=="string"?m:JSON.stringify(m,null,2);if(c)try{const j=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},_=j.row_count||(Array.isArray(j.imported_rows)?j.imported_rows.length:0);_>0&&(u=t("log-push-rows").replace("{n}",String(_)))}catch{}const f=(o.external_doc_no||"").trim(),b=(o.external_url||"").trim(),B=(o.external_doc_hint||"").trim(),x=(o.ocr_buyer_name||"").trim()||o.client_name||"-",v=o.seller_name||"-",h=o.push_type==="id_card";let L="-";const I=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(I)&&(L=I.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const S=c?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),C=c?"✓":"✗",w=[],g=(j,_)=>{w.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(j)}</span>
                    <span class="erp-receipt-val">${_}</span>
                </div>`)};if(g(h?t("erp-log-col-booking"):t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),g(t("erp-receipt-erp-name"),escapeHtml(i)),c){let j;f?j=`<strong class="erp-receipt-docno">${escapeHtml(f)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(f)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:j=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,g(t("erp-receipt-doc-no"),j)}h||g(t("erp-receipt-client"),escapeHtml(x)),g(h?t("erp-log-col-customer"):t("erp-receipt-seller"),escapeHtml(v)),c&&g(t("erp-receipt-amount"),escapeHtml(L)),g(t("erp-receipt-time"),escapeHtml(d)),g(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let E="";c&&b?E=`<a class="erp-receipt-primary-btn" href="${escapeHtml(b)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:c&&f&&(E=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(f)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let M="";if(c&&f&&B){const j="erp-receipt-hint-"+B,_=t(j);_&&_!==j&&(M=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(_)}</span></div>`)}let $="";if(!c){const j=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),_=j?j[0]:"",A=typeof currentLang=="string"&&currentLang||window._currentLang||"th",F=o.error_friendly&&o.error_friendly[A]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),D=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),V=!!(o.history_id&&o.endpoint_id),Y=[];Y.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),D&&Y.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),V&&Y.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),$=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${_?`<div class="erp-receipt-errcode">${escapeHtml(_)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(F)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${Y.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${c?"ok":"fail"}">${C}</span>
                    ${escapeHtml(S)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(l)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${w.join("")}
            </div>

            ${M}
            ${E?`<div class="erp-receipt-primary-wrap">${E}</div>`:""}
            ${$}

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
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=Zn;window.showLogDetail=Cs;const Ss=`
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
    `;we("endpoint-modal",Ss);let We={key:"all",val:""},et="",Lt=!1,He=new Set;window._erpSelected=He;async function Ts(){const e=document.getElementById("erp-logs-erp-select");if(!(!e||Lt)){Lt=!0;try{let n=window._erpEndpoints;if(!Array.isArray(n)||n.length===0){const s=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(s.ok){const i=await s.json();n=i&&(i.items||i)||[]}}Array.isArray(n)||(n=[]);const a=new Set,o=[];n.forEach(s=>{const i=(s&&s.adapter||"").toLowerCase();!i||a.has(i)||(a.add(i),o.push({val:i,label:s&&s.name||i}))}),e.innerHTML=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`+o.map(s=>`<option value="${escapeHtml(s.val)}"${s.val===et?" selected":""}>${escapeHtml(s.label)}</option>`).join("")}catch{Lt=!1}}}async function Oe(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats(),Ts();try{const a=new URLSearchParams({limit:"30"});We.key==="status"&&a.set("status",We.val),We.key==="trigger"&&a.set("trigger",We.val),et&&a.set("adapter",et);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(f){return f.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){Oe(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const r=i.filter(function(f){var b=f.status==="failed"&&f.next_retry_at&&new Date(f.next_retry_at).getTime()>Date.now()-6e4;return!b}).map(function(f){return f.id}),d=et==="mrerp_dms",l=d?t("erp-log-col-booking"):t("erp-log-col-invoice"),p=d?t("erp-log-col-customer"):t("erp-log-col-seller"),m=d?t("erp-log-col-idcard"):t("erp-log-col-client"),c='<div class="erp-log-row erp-log-row-header" data-log-header>'+(r.length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(l)}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(m)}</span><span class="log-seller">${escapeHtml(p)}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=c+i.map(f=>{const b=new Date(f.created_at),B=`${String(b.getMonth()+1).padStart(2,"0")}-${String(b.getDate()).padStart(2,"0")} ${String(b.getHours()).padStart(2,"0")}:${String(b.getMinutes()).padStart(2,"0")}`,x=f.status==="failed"&&f.next_retry_at&&new Date(f.next_retry_at).getTime()>Date.now()-6e4;let v,h,L;f.status==="pending"?(v="retrying",h="⟳",L=t("erp-status-pending")):f.status==="success"?(v="ok",h="✓",L=t("erp-status-success")):f.status==="skipped_dup"?(v="skipped",h="⏭",L=t("erp-status-skipped")):x?(v="retrying",h="↻",L=t("erp-status-retrying")):(v="fail",h="✗",L=t("erp-status-failed"));let I;f.trigger==="auto"?I=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:f.trigger==="retry"?I=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:I=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;const S=f.push_type==="id_card",C=S?`<span class="log-tag log-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span>`:"",w=f.error_friendly&&(f.error_friendly[currentLang]||f.error_friendly.en)||"";let g="";const E=f.retry_count||0,M=f.max_retries||3;if(x){const y=new Date(f.next_retry_at).getTime()-Date.now(),H=Math.max(0,Math.round(y/6e4)),P=H<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:H});g=`${t("erp-retry-attempt",{n:E,max:M})} · ${P}`}else f.status==="failed"&&E>=M&&!f.next_retry_at&&(g=t("erp-retry-exhausted",{n:E}));const $=f.status==="failed"&&!x?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(f.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",j=!x,_=He.has(f.id)?"checked":"",A=j?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(f.id)}" ${_}>`:'<span class="erp-log-cb-spacer"></span>',q=(f.ocr_buyer_name||"").trim()||(f.client_name||"").trim(),F=S?`<span class="log-client" title="${escapeHtml(t("erp-log-col-idcard"))}">${f.id_card_tail?"••••"+escapeHtml(f.id_card_tail):"—"}</span>`:q?`<span class="log-client" title="${escapeHtml(q)}">${escapeHtml(q.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,D=S?'<span class="log-workspace log-workspace-unresolved">—</span>':f.workspace_name?`<span class="log-workspace">${escapeHtml((f.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,V=f.endpoint_name?`<span class="log-erp">${escapeHtml((f.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,Y=(f.external_doc_no||"").trim(),T=(f.external_url||"").trim();let k;return T?k=`<span class="log-doc"><a href="${escapeHtml(T)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(Y||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:Y?k=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(Y)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(Y.substring(0,18))}</span>`:f.status==="success"?k=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:k='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${v}" data-log-detail="${escapeHtml(f.id)}">
                    ${A}
                    <span class="log-time">${B}</span>
                    <span class="log-status" title="${escapeHtml(L+(g?" · "+g:"")+(w?" · "+w:""))}">${h}</span>
                    ${I}${C}
                    <span class="log-invoice"${S?` title="${escapeHtml(t("erp-log-col-booking"))}"`:""}>${escapeHtml(f.invoice_no||"-")}</span>
                    ${D}
                    ${F}
                    <span class="log-seller"${S?` title="${escapeHtml(t("erp-log-col-customer"))}"`:""}>${escapeHtml((f.seller_name||"").substring(0,20))}</span>
                    ${V}
                    ${k}
                    <span class="log-http">HTTP ${f.http_status||"-"}</span>
                    <span class="log-elapsed">${f.elapsed_ms}ms</span>
                    <span class="log-actions">${$}</span>
                </div>
            `}).join("");const u=new Set(i.map(f=>f.id));for(const f of Array.from(He))u.has(f)||He.delete(f);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function Qn(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),Oe(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),Qn(s.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const m=i.dataset.logCb;i.checked?He.add(m):He.delete(m),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const m=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(u){u.checked=m;const f=u.dataset.logCb;m?He.add(f):He.delete(f)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),He.clear(),document.querySelectorAll(".erp-log-cb").forEach(m=>{m.checked=!1}),window._refreshErpBatchBar();return}const d=n.target.closest("[data-log-detail]");if(d){if(n.target.closest("[data-log-cb]"))return;const m=n.target.closest("[data-copy-doc]");if(m){n.stopPropagation(),window.copyErpDocNo(m.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(d.dataset.logDetail);return}const l=n.target.closest(".chip-filter");if(l){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(m=>m.classList.remove("active")),l.classList.add("active"),We={key:l.dataset.filterKey,val:l.dataset.filterVal},Oe();return}if(n.target.closest("#btn-refresh-logs")){const m=n.target.closest("#btn-refresh-logs");m.classList.add("spinning"),setTimeout(()=>m.classList.remove("spinning"),600),Oe();return}const p=n.target.closest(".auto-nav-item");if(p&&p.dataset.autoTab){switchAutomationTab(p.dataset.autoTab);return}}),document.addEventListener("change",n=>{n.target&&n.target.id==="erp-logs-erp-select"&&(et=n.target.value||"",Oe())})})();window.loadErpLogs=Oe;window.retryPushLog=Qn;function ea(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function ta(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),i=o.failed&&o.failed>0?"warn":"success";showToast(s,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function na(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),ta()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),na()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),ea()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=ea;window._runErpBatchRetry=ta;window._runErpBatchDelete=na;(function(){let e=null,n=!1;function a(){if(e)return e;const d=document.createElement("div");d.id="line-email-modal",d.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",d.innerHTML=`
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
        `,document.body.appendChild(d),e=d;const l=d.querySelector("#line-email-input"),p=d.querySelector("#line-email-submit-btn"),m=d.querySelector("#line-email-err");async function c(){m.textContent="";const u=(l.value||"").trim().toLowerCase();if(!u||u.indexOf("@")<0||u.split("@")[1].indexOf(".")<0){m.textContent=t("line-email-err-invalid");return}p.disabled=!0,p.style.opacity="0.6";try{const f=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:u})});if(!f.ok)throw new Error("http_"+f.status);const b=await f.json();b.token&&localStorage.setItem("mrpilot_token",b.token),typeof showToast=="function"&&showToast(b.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{m.textContent=t("line-email-err-failed"),p.disabled=!1,p.style.opacity="1"}}return p.addEventListener("click",c),l.addEventListener("keydown",function(u){u.key==="Enter"&&c()}),d}function o(){if(!e)return;const d=e.querySelector("#line-email-title-h"),l=e.querySelector("#line-email-sub-p"),p=e.querySelector("#line-email-input"),m=e.querySelector("#line-email-submit-btn");d&&(d.textContent=t("line-email-title")),l&&(l.textContent=t("line-email-sub")),p&&(p.placeholder=t("line-email-placeholder")),m&&(m.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const d=e.querySelector("#line-email-input");d&&setTimeout(function(){d.focus()},100)}async function i(){const d=localStorage.getItem("mrpilot_token");if(d)try{const l=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+d}});if(!l.ok)return;const p=await l.json();p&&p.needs_email&&s()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(m){let c=0;return m.length>=8&&c++,m.length>=12&&c++,/[a-zA-Z]/.test(m)&&/\d/.test(m)&&c++,/[^a-zA-Z0-9]/.test(m)&&c++,Math.min(3,c)}function n(m,c){const u=document.getElementById("cpw-msg");u&&(u.textContent=m,u.className="cpw-msg "+(c||""))}function a(m){return typeof t=="function"?t(m):m}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(c=>{const u=document.getElementById(c);u&&(u.value="",u.setAttribute("readonly","readonly"))});const m=document.getElementById("cpw-strength-bar");m&&(m.style.width="0%",m.className="cpw-strength-bar"),n("","")}async function i(){const m=document.getElementById("btn-change-pw"),c=document.getElementById("cpw-old"),u=document.getElementById("cpw-new"),f=document.getElementById("cpw-confirm"),b=document.getElementById("cpw-strength-bar");if(!m||!c||!u||!f)return;const B=c.value,x=u.value,v=f.value;if(!B||!x||!v){n(a("settings-change-pw-empty"),"error");return}if(x.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(x)&&/\d/.test(x))){n(a("settings-change-pw-too-weak"),"error");return}if(x!==v){n(a("settings-change-pw-mismatch"),"error");return}m.disabled=!0;const h=m.textContent;m.textContent=a("settings-change-pw-submitting"),n("","");try{const L=localStorage.getItem("mrpilot_token"),I=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+L},body:JSON.stringify({old_password:B,new_password:x})}),S=await I.json().catch(()=>({}));if(I.ok&&S.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),c.value="",u.value="",f.value="",b&&(b.style.width="0%",b.className="cpw-strength-bar");else{const C=S.detail||"";let w=a("settings-change-pw-success");C==="wrong_old_password"?w=a("settings-change-pw-wrong-old"):C==="password_too_short"?w=a("settings-change-pw-too-short"):C==="password_too_weak"?w=a("settings-change-pw-too-weak"):w=C||"Error",n(w,"error")}}catch(L){console.error("change_password",L),n("Network error","error")}finally{m.disabled=!1,m.textContent=h}}function r(){o||(o=!0,document.addEventListener("click",m=>{if(!m.target||!m.target.closest)return;const c=m.target.closest(".cpw-eye");if(c){const u=document.getElementById(c.dataset.target);u&&(u.type=u.type==="password"?"text":"password");return}if(m.target.closest("#cpw-forgot-link")){m.preventDefault(),d();return}if(m.target.closest("#btn-change-pw")){i();return}m.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",m=>{if(m.target&&m.target.id==="cpw-new"){const c=document.getElementById("cpw-strength-bar");if(!c)return;const u=e(m.target.value),f=["0%","33%","66%","100%"],b=["","weak","medium","strong"];c.style.width=f[u],c.className="cpw-strength-bar "+b[u]}}),document.addEventListener("focusin",m=>{m.target&&["cpw-old","cpw-new","cpw-confirm"].includes(m.target.id)&&m.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function d(){const m=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),c=m&&m.username?m.username:"",u=l(c);let f=document.getElementById("cpw-forgot-overlay");f&&f.remove(),f=document.createElement("div"),f.id="cpw-forgot-overlay",f.className="cpw-forgot-overlay",f.innerHTML=`
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
        `,document.body.appendChild(f);const b=()=>f.remove();f.querySelector("#cpw-forgot-close").addEventListener("click",b),f.querySelector("#cpw-forgot-cancel").addEventListener("click",b),f.addEventListener("click",B=>{B.target===f&&b()}),f.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const B=f.querySelector("#cpw-forgot-send"),x=f.querySelector("#cpw-forgot-msg");B.disabled=!0;const v=B.textContent;B.textContent=a("cpw-forgot-sending");try{const h=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:c})}),L=await h.json().catch(()=>({}));h.ok?(x.textContent=a("cpw-forgot-success"),x.className="cpw-forgot-msg success",B.style.display="none",f.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(x.textContent=L.detail||a("cpw-forgot-fail"),x.className="cpw-forgot-msg error",B.disabled=!1,B.textContent=v)}catch{x.textContent=a("cpw-forgot-fail"),x.className="cpw-forgot-msg error",B.disabled=!1,B.textContent=v}})}function l(m){if(!m||!m.includes("@"))return m||"";const[c,u]=m.split("@");return c.length<=2?c+"****@"+u:c.slice(0,2)+"****@"+u}function p(m){return m==null?"":String(m).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),d=r&&r.detail;let l="";if(typeof d=="string"?l=d:d&&typeof d=="object"&&(l=d.code||""),console.warn("[heartbeat] session revoked",l),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),l==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const p=l==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(p),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function xt(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),i=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const d=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",l=r.is_active===!1?"team-status-off":"team-status-on",p=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",m=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
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
                            ${m}
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Ms(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),d=document.getElementById("add-emp-submit"),l=(o.value||"").trim(),p=(s.value||"").trim(),m=i.value||"";if(r.textContent="",r.classList.remove("error"),!l||l.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(l)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(p&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(m.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(m)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(m)&&/\d/.test(m))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}d.disabled=!0,d.textContent=t("msg-saving")||"保存中...";try{const c={username:l,password:m};p&&(c.email=p);const u=await apiPost("/api/team/employees",c),f=u?await u.json().catch(()=>({})):{};if(u&&u.ok&&f&&f.ok){showToast(t("team-added")||"员工已添加","success"),n(),xt();return}const b=f&&f.detail||"unknown",B={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=B[b]||(t("team-create-failed")||"创建失败")+" ("+b+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{d.disabled=!1,d.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function $s(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){xt();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Hs(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),xt();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function As(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const d=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",l=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(d.replace("{ch}",l),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Ms();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),$s(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),Hs(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),As(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=xt;function js(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=js;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
