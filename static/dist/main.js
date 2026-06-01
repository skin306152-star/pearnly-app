(function(){const n=[];function a(s){try{n.push(Object.assign({ts:Date.now()},s)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(s)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(s){s.target&&s.target!==window&&(s.target.src||s.target.href)||a({type:"js_error",summary:String(s.message||"JS Error").slice(0,200),detail:{file:s.filename||"",line:s.lineno||0,col:s.colno||0,stack:s.error&&s.error.stack?String(s.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(s){const i=s.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const o=window.fetch;typeof o=="function"&&(window.fetch=function(){const s=arguments,i=Date.now(),r=typeof s[0]=="string"?s[0]:s[0]&&s[0].url||"?",p=s[1]&&s[1].method||"GET",l=String(r).split("?")[0];return o.apply(this,s).then(function(d){const m=Date.now()-i;if(d.ok)m>2500&&a({type:"api_slow",summary:p+" "+l+" → 慢 "+m+"ms",detail:{url:r,method:p,status:d.status,elapsed_ms:m}});else{let c="";try{d.clone().text().then(function(f){c=String(f||"").slice(0,500),a({type:"api_error",summary:p+" "+l+" → "+d.status+" ("+m+"ms)",detail:{url:r,method:p,status:d.status,elapsed_ms:m,body_preview:c}})}).catch(function(){a({type:"api_error",summary:p+" "+l+" → "+d.status+" ("+m+"ms)",detail:{url:r,method:p,status:d.status,elapsed_ms:m,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:p+" "+l+" → "+d.status+" ("+m+"ms)",detail:{url:r,method:p,status:d.status,elapsed_ms:m}})}}return d}).catch(function(d){const m=Date.now()-i;throw a({type:"api_fail",summary:p+" "+l+" → 网络失败 ("+m+"ms)",detail:{url:r,method:p,elapsed_ms:m,error:String(d&&d.message||d)}}),d})}),["error","warn"].forEach(function(s){const i=console[s];typeof i=="function"&&(console[s]=function(){try{const r=[];for(let p=0;p<arguments.length;p++){const l=arguments[p];if(typeof l=="string")r.push(l);else if(l&&l instanceof Error)r.push(l.message);else try{r.push(JSON.stringify(l).slice(0,300))}catch{r.push(String(l))}}a({type:"console_"+s,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(o=>o.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function Ln(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function Cn(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function Sn(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function Qe(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const o in n)a=a.replace("{"+o+"}",n[o]);return a}function Tn(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function Mn(e,n){n=n||14;const o={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${o}</svg>`}function et(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},o={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},s=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[s]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[s]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+o[s]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function nt(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function $n(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...nt()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),o=a&&a.detail;let s="";if(typeof o=="string"?s=o:o&&typeof o=="object"&&(s=o.code||""),n.status===401||typeof s=="string"&&s.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,o),localStorage.removeItem("mrpilot_token"),s==="auth.session_revoked")et();else{const p=s==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Qe(p),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=o,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function Hn(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...nt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.clone().json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")et();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Qe(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function An(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...nt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")et();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Qe(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const o=await a.json().catch(()=>({}));return{ok:a.ok&&o.ok!==!1,...o}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=$n;window.apiPost=Hn;window.t=Qe;window.escapeHtml=Tn;window.svgIcon=Mn;window._showSessionRevokedModal=et;window._wsHeader=nt;window.apiPut=An;window.getMaxFiles=Ln;window.getMaxPagesPerFile=Cn;window.getMaxMbPerFile=Sn;function ke(e,n){const a=document.getElementById(e);if(!(!a||a.dataset.wbInjected==="1")){a.innerHTML=n,a.dataset.wbInjected="1";try{const o=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",s=window.I18N;if(!s||!s[o])return;a.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");s[o][r]&&(i.textContent=s[o][r])}),a.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");s[o][r]&&(i.placeholder=s[o][r])})}catch{}}}const jn=`
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
    `;ke("page-ocr",jn);function wt(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const o=document.getElementById("general-lang");o&&(o.value=e);const s=document.getElementById("col-conf-th");s&&s.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&kt(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function Pn(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",s=>{s.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(s)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});Pn("lang-dropdown",e=>wt(e.dataset.lang));const Rt=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","receivables","reconcile","cloud","test-center"];function zt(e){Rt.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(o=>o.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(o=>{o.classList.toggle("active",o.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function Nt(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){return!i||typeof i!="string"||(i=i.trim(),!i)?null:i.includes("@")&&i.indexOf("@")>0&&i.indexOf(".")>i.indexOf("@")?i.split("@")[0]:i}const o=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let s=null;for(const i of o){const r=a(i);if(r){s=r;break}}s||(s=t("brand-workspace-fallback")||"我的工作台"),e.textContent=s,e.title=s,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",s,"· _userInfo fields:",Object.keys(n))}function kt(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function Ft(){try{const[e,n,a,o]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(s=>s.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,o&&(window._planState=o),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const s=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(s&&!i){window.location.replace("/home");return}if(!s&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=s}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,o&&(window._planState=o),Nt(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(s){console.error("[nav-ia phase1] render avatar menu",s)}kt(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const s=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(s&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(s&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(s){console.error("force-pw init",s)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(s){console.error("onboarding init",s)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(s){console.error("settings forms init",s)}}catch(e){console.error(e)}}function Dn(){let e=document.getElementById("offline-banner");e||(e=document.createElement("div"),e.id="offline-banner",e.className="offline-banner",e.style.display="none",document.body.insertBefore(e,document.body.firstChild));function n(){navigator.onLine===!1?(e.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",e.classList.remove("is-online"),e.classList.add("is-offline"),e.style.display="flex"):e.classList.contains("is-offline")?(e.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",e.classList.remove("is-offline"),e.classList.add("is-online"),setTimeout(()=>{e.style.display="none",e.classList.remove("is-online")},2e3)):e.style.display="none"}window.addEventListener("online",n),window.addEventListener("offline",n),n()}window.applyLang=wt;window.routeTo=zt;window.loadAll=Ft;window.renderBrandWorkspace=Nt;window.updateUploadHint=kt;window.installNetworkBanner=Dn;try{wt(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");zt(Rt.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);Ft();const Ot="mrpilot_sidebar_collapsed";localStorage.getItem(Ot)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(Ot,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const o=document.querySelectorAll("#page-integrations .int-top-tab"),s=document.querySelectorAll("#page-integrations .int-top-panel");if(o.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),s.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),o&&o.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const o=a.target.closest("#page-integrations .int-top-tab");if(o){const i=o.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const o=document.querySelector(".auto-content");o&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(s){s.style.display="",o.appendChild(s)})}window.openIntegrationDrawer=function(a,o){const s=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),p=document.getElementById("int-drawer-body");if(!s||!p)return;e(),s.dataset.currentTab=a||"",r&&(r.textContent=o||""),p.innerHTML="";var l={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},d=l[a]||a;const m=document.querySelector('.auto-panel[data-auto-panel="'+d+'"]');m?(m.style.display="block",p.appendChild(m)):p.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',s.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var c={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(c[a])try{c[a]()}catch(u){console.warn("[int-drawer] loader error",u)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(u){console.warn("[int-drawer] ERP load error",u)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),o&&(o.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),o=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),o&&o.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(s){s.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(s=>{s.addEventListener("click",()=>switchSettingsTab(s.dataset.tab))});let o=null;try{o=localStorage.getItem("mrpilot_settings_tab")}catch{}if(o){const s=document.querySelector(`.settings-tab[data-tab="${o}"]`);if(s&&s.style.display!=="none"){switchSettingsTab(o);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),o=document.getElementById("btn-save-company");if(!a&&!o){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),o&&o.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let Ke=null;function qn(){vt(),Ke=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&vt()}catch{}},1e4)}function vt(){Ke&&(clearInterval(Ke),Ke=null)}window.startEnginePolling=qn;window.stopEnginePolling=vt;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target.closest("[data-rd-action]");if(n){const s=n.dataset.rdAction,i=n.dataset.rdSide;s==="verify"?callRdVerify(i):s==="sync"&&callRdSync(i);return}if(e.target.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=e.target.closest("[data-archive-copy]");if(o){const s=o.dataset.archiveCopy;navigator.clipboard?.writeText(s).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const Ht=document.getElementById("btn-custom-template");Ht&&Ht.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});const Rn=`
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
    `,zn=`
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
`;ke("pearnly-confirm-modal",Rn);ke("confirm-modal",zn);window.pearnlyConfirm=function(e,n){return new Promise(function(a){const o=document.getElementById("pearnly-confirm-modal"),s=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),p=document.getElementById("pearnly-confirm-cancel"),l=document.getElementById("pearnly-confirm-close");if(!o||!i||!r||!p){a(window.confirm(e));return}s&&(s.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",o.style.display="flex";function d(w){o.style.display="none",r.removeEventListener("click",m),p.removeEventListener("click",c),l&&l.removeEventListener("click",c),o.removeEventListener("click",u),document.removeEventListener("keydown",f),a(w)}function m(){d(!0)}function c(){d(!1)}function u(w){w.target===o&&d(!1)}function f(w){w.key==="Escape"?d(!1):w.key==="Enter"&&d(!0)}r.addEventListener("click",m),p.addEventListener("click",c),l&&l.addEventListener("click",c),o.addEventListener("click",u),document.addEventListener("keydown",f),setTimeout(function(){try{p.focus()}catch{}},50)})};const Nn=`
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

`,Fn=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Nn+Fn,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const On=`
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

`,Vn=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=On+Vn,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function Un(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function Gn(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function Kn(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function Jn(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function Yn(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let p=null;const l=()=>{p&&(clearTimeout(p),p=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(p=setTimeout(l,r)),l}window.showAlert=Un;window.hideAlerts=Gn;window._humanizeBackendError=Kn;window.humanizeError=Jn;window.showToast=Yn;function Wn(e,n){return n=n||{},new Promise(a=>{const o=document.getElementById("confirm-modal"),s=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),p=document.getElementById("confirm-modal-close"),l=document.getElementById("confirm-modal-title");if(!o||!s||!i||!r){a(!1);return}l.textContent=n.title||t("confirm-default-title");const d=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const f=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),w=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");s.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${f}</div>
                <input type="text" id="${d}" placeholder="${w}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else s.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",o.style.display="flex";const m=f=>{o.style.display="none",i.onclick=null,r.onclick=null,p.onclick=null,o.onclick=null,document.removeEventListener("keydown",u),n.promptInput&&(s.innerHTML=""),r.style.display="",a(f)},c=()=>{const f=d?document.getElementById(d):null;return f?f.value:""},u=f=>{f.key==="Escape"?m(n.promptInput?null:!1):f.key==="Enter"&&m(n.promptInput?c():!0)};i.onclick=()=>m(n.promptInput?c():!0),r.onclick=()=>m(n.promptInput?null:!1),p.onclick=()=>m(n.promptInput?null:!1),o.onclick=f=>{f.target===o&&m(n.promptInput?null:!1)},document.addEventListener("keydown",u),setTimeout(()=>{if(n.promptInput){const f=document.getElementById(d);f&&f.focus()}else i.focus()},50)})}window.showConfirm=Wn;function Xn(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof ht=="function"&&ht()}catch(n){console.warn("settings tab side effect failed:",n)}}}function Zn(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function Qn(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function ea(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function ht(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}ta(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function ta(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
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
    `}window.switchSettingsTab=Xn;window.fillSettingsForms=Zn;window.saveProfile=Qn;window.saveCompany=ea;window.renderSettings=ht;function at(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function _t(e){return e=e||_userInfo,!!e&&(e.role==="owner"||at(e))}function Vt(e){return e=e||_userInfo,!!e&&e.role==="member"&&!at(e)}function na(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!at(e)}function Ut(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function Gt(e){return Vt(e)}function aa(e){return _t(e)}function oa(e){return _t(e)&&Ut(e)}window.isMoneyHidden=Gt;window.isSuperAdmin=at;window.isOwner=_t;window.isEmployee=Vt;window.isTrial=na;window.isLifetime=Ut;window.shouldHideMoney=Gt;window.canManageTeam=aa;window.canManageApiKey=oa;function sa(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,p;if(o===0)r="danger",p=t("quota-banner-exhausted");else if(s>=90)r="danger",p=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",p=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(p)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const l=e.querySelector(".quota-banner-close");l&&l.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function ia(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const p=document.querySelector('.settings-tab[data-tab="team"]');p&&(p.style.display=a?"":"none");const l=document.querySelector('.settings-panel[data-settings-panel="team"]');l&&(l.dataset.permHidden=a?"0":"1");const d=document.querySelector('.settings-tab[data-tab="api"]');d&&(d.style.display=o||isSuperAdmin(e)?"":"none");const m=document.querySelector('.settings-tab[data-tab="plan"]');m&&(m.style.display=n?"none":"");const c=document.querySelector('.settings-tab[data-tab="company"]');c&&(c.style.display=n?"none":"");const u=document.getElementById("info-bar");u&&(u.style.display=n?"none":"");const f=document.getElementById("trial-banner");f&&n&&(f.style.display="none");const w=document.getElementById("plan-banner");w&&n&&(w.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(S=>{S.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const S=document.querySelector(".settings-tab.active");S&&S.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(S){console.warn("[v118.12.3] failed to fix active tab:",S)}if(window.PEARNLY_ADMIN_MODE){const S=document.getElementById("admin-mode-banner");S&&(S.style.display="flex"),document.querySelectorAll(".nav-item").forEach(h=>{h.classList.contains("nav-admin-only")||(h.style.display="none")}),document.querySelectorAll(".nav-group").forEach(h=>{h.classList.contains("nav-group-admin-only")||(h.style.display="none")});const E=document.getElementById("client-switcher");E&&(E.style.display="none"),document.body.classList.add("admin-mode");const v=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(h=>{const C=h.dataset.tab;C&&!v.includes(C)&&(h.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(h=>{const C=h.dataset.pane;C&&!v.includes(C)&&(h.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(h=>{const C=h.querySelectorAll(".settings-tab");Array.from(C).some(A=>A.style.display!=="none")||(h.style.display="none")})}}function ra(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
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
        `;else{const s=e.tenant_used!=null?e.tenant_used:e.used_this_month||0,i=e.tenant_quota!=null&&e.tenant_quota>0?e.tenant_quota:e.monthly_quota||0,r=i>0?Math.min(100,s/i*100):0;let p="";r>=95?p="danger":r>=80&&(p="warn"),i>0?a=`
                <div class="info-chip">
                    <span class="chip-label">${escapeHtml(t("info-monthly"))}</span>
                    <span class="chip-value">${s} / ${i}</span>
                    <div class="mini-bar"><div class="mini-bar-fill ${p}" style="width:${r}%"></div></div>
                </div>
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=sa;window.applySidebarVisibility=ia;window.renderInfoBar=ra;async function Kt(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function Jt(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Ye(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function Ce(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function la(e){const a=Ye(e==="seller"?"seller_tax":"buyer_tax");Ce(e,t("rd-verifying"),"loading");const o=await Kt("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){Ce(e,t(Jt(o.error)),"error");return}o.data&&o.data.valid?Ce(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):Ce(e,t("rd-status-invalid"),"invalid")}async function ca(e){const a=Ye(e==="seller"?"seller_tax":"buyer_tax");Ce(e,t("rd-syncing"),"loading");const o=await Kt("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){Ce(e,t(Jt(o.error)),"error");return}Ce(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),da(e,o.data)}}function da(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=Ye(a),i=Ye(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==i&&r.push({field:o,label:t("rd-field-address"),current:i,official:n.address});const p=[];n.branch_label&&p.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&p.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let l=document.getElementById("rd-sync-modal");if(l||(l=document.createElement("div"),l.id="rd-sync-modal",l.className="rd-modal-mask",document.body.appendChild(l)),r.length===0)l.innerHTML=`
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
                    ${p.length?`<div class="rd-modal-extra">${p.join(" · ")}</div>`:""}
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
                    ${p.length?`<div class="rd-modal-extra">${p.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t("rd-modal-apply"))}</button>
                </div>
            </div>
        `}l.classList.add("show");const d=()=>l.classList.remove("show");l.querySelector(".rd-modal-close").addEventListener("click",d),l.querySelectorAll("[data-rd-modal-close]").forEach(c=>c.addEventListener("click",d)),l.addEventListener("click",c=>{c.target===l&&d()});const m=l.querySelector("[data-rd-modal-apply]");m&&m.addEventListener("click",()=>{const c=_results[_drawerIdx];if(!c){d();return}l.querySelectorAll("[data-rd-apply]:checked").forEach(u=>{const f=u.dataset.field,w=u.dataset.value;c.edits[f]=w,c.merged_fields[f]=w;const S=document.querySelector(`[data-field="${f}"]`);S&&(S.value=w);const E=document.querySelector(`[data-field-wrap="${f}"]`);E&&E.classList.add("edited")}),updateDrawerEditCount(),renderResults(),d()})}window.callRdVerify=la;window.callRdSync=ca;function pa(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(s=>!s.is_duplicate&&!s.is_copy),o=a.length>0?a:e;for(const s of o){const i=s.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function ua(e){const n=e.target.dataset.field,a=e.target.value,o=_results[_drawerIdx],s=o.merged_fields[n];a===(s??"")?delete o.edits[n]:(o.edits[n]=a,o.merged_fields[n]=a);const i=document.querySelector(`[data-field-wrap="${n}"]`);i&&i.classList.toggle("edited",o.edits[n]!==void 0),Yt(),renderResults()}function Yt(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=pa;window.onFieldEdit=ua;window.updateDrawerEditCount=Yt;function fa(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,o=document.getElementById("force-pw-new").value,s=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!o){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(o!==s){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(o.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(o)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(o)&&/\d/.test(o))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(o===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:o})}),p=await r.json().catch(()=>({}));if(!r.ok){const l=p&&p.detail||"unknown",d={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=d[l]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=fa;(function(){let e=null,n=null,a=null,o=null;function s(h){return document.getElementById(h)}async function i(){w(),E(),await r()}async function r(){try{const h=localStorage.getItem("mrpilot_token"),C=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!C.ok){S(t("linebot-err-status"));return}const L=await C.json();L.bound?p(L):await l()}catch{S(t("linebot-err-status"))}}function p(h){f(),s("linebot-unbound").style.display="none",s("linebot-bound").style.display="block";const C=s("linebot-status-summary");C&&(C.textContent=t("linebot-status-bound"),C.style.background="#D1FAE5",C.style.color="#065F46");const L=s("linebot-bound-name");L&&(L.textContent=h.line_display_name||"(LINE User)");const A=s("linebot-avatar");A&&(h.line_picture_url?(A.src=h.line_picture_url,A.style.display=""):A.style.display="none");const T=s("linebot-bound-since");T&&h.bound_at&&(T.textContent=new Date(h.bound_at).toLocaleString())}async function l(){s("linebot-bound").style.display="none",s("linebot-unbound").style.display="block";const h=s("linebot-status-summary");h&&(h.textContent=t("linebot-status-unbound"),h.style.background="#FEE2E2",h.style.color="#B91C1C"),await d(),u()}async function d(){try{const h=localStorage.getItem("mrpilot_token"),C=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+h}});if(!C.ok){S(t("linebot-err-code"));return}const L=await C.json();a=L.code,o=new Date(L.expires_at).getTime(),m(L)}catch{S(t("linebot-err-code"))}}function m(h){const C=s("linebot-code");C&&(C.textContent=h.code);const L=s("linebot-bot-id");L&&(L.textContent=h.bot_basic_id||t("linebot-bot-id-missing"));const A=s("linebot-qr");if(A)if(h.bot_friend_url){const T="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(h.bot_friend_url);A.classList.remove("empty"),A.innerHTML='<img src="'+T+'" alt="LINE Bot QR">'}else A.classList.add("empty"),A.innerHTML="";c()}function c(){e&&clearInterval(e);const h=s("linebot-code-expires");function C(){if(!o)return;const L=o-Date.now();if(L<=0){h&&(h.textContent=t("linebot-code-expired"),h.classList.add("expiring"));const g=s("linebot-code");g&&(g.style.opacity="0.4"),clearInterval(e),e=null;return}const A=Math.floor(L/1e3),T=Math.floor(A/60),k=A%60;h&&(h.textContent=t("linebot-code-expires-in").replace("{m}",T).replace("{s}",String(k).padStart(2,"0")),L<6e4?h.classList.add("expiring"):h.classList.remove("expiring"))}C(),e=setInterval(C,1e3)}function u(){f(),n=setInterval(async()=>{try{const h=localStorage.getItem("mrpilot_token"),C=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!C.ok)return;const L=await C.json();L.bound&&p(L)}catch{}},4e3)}function f(){n&&(clearInterval(n),n=null)}function w(){e&&(clearInterval(e),e=null),f()}function S(h){const C=s("linebot-error");C&&(C.textContent=h,C.style.display="block")}function E(){const h=s("linebot-error");h&&(h.style.display="none")}async function v(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const C=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+C}})).ok){S(t("linebot-err-unbind"));return}await i()}catch{S(t("linebot-err-unbind"))}}document.addEventListener("click",h=>{if(h.target.closest("#linebot-code-refresh")){h.preventDefault(),E(),d();return}if(h.target.closest("#linebot-unbind")){h.preventDefault(),v();return}}),window._loadLineBotPanel=i})();function ot(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const p=parseFloat(r.merged_fields.total_amount);isNaN(p)||(n+=p)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,p)=>({...r,_idx:p}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(p=>(p.filename||"").toLowerCase().includes(r)||(p.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,p)=>{let l,d;return _sortKey==="filename"?(l=r.filename,d=p.filename):_sortKey==="invoice_no"?(l=r.merged_fields.invoice_number,d=p.merged_fields.invoice_number):_sortKey==="invoice_date"?(l=r.merged_fields.date,d=p.merged_fields.date):_sortKey==="total"?(l=parseFloat(r.merged_fields.total_amount)||0,d=parseFloat(p.merged_fields.total_amount)||0):_sortKey==="confidence"?(l=r.confidence,d=p.confidence):(l="",d=""),l<d?_sortDir==="asc"?-1:1:l>d?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=s.map((r,p)=>{const l=r.merged_fields,d=`<span class="empty-cell">${t("empty-val")}</span>`,m="conf-tip-"+(r.confidence||"low"),c="conf-"+(r.confidence||"low"),u=t(m),f=t(c);return`
            <tr data-idx="${r._idx}">
                <td class="num">${p+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${l.invoice_number?escapeHtml(l.invoice_number):d}</td>
                <td class="date">${l.date?escapeHtml(l.date):d}</td>
                <td class="amount">${l.total_amount?Number(l.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):d}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(u)}">${f}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const p=parseInt(r.dataset.idx,10);Xt(p)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),ot()})});let At=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(At),At=setTimeout(()=>{_searchKeyword=n.trim(),ot(),Wt()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",ot(),Wt(),e.focus()});function Wt(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function Xt(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,i=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,p=document.getElementById("drawer-body"),l=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,d=i?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(p.innerHTML=`
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
            ${ye("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",s)}
            ${ye("date","drawer-lbl-date",r.date,"input",s)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${ye("subtotal","drawer-lbl-subtotal",r.subtotal,"input",s)}
            ${ye("vat","drawer-lbl-vat",r.vat,"input",s)}
            ${ye("total_amount","drawer-lbl-total",r.total_amount,"input",s)}
            ${r.wht_amount||r.wht_rate?`
                ${ye("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,ma(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${ye("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${ye("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,d,jt("seller"))}
            ${ye("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${ye("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${ye("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,d,jt("buyer"))}
            ${ye("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?va(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${ye("notes","drawer-lbl-notes",r.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(m=>`--- Page ${m.page||m.page_number||"?"} ---
${m.raw_text||m.text||""}`).join(`

`))}</pre>
        </details>
    `,s?p.querySelectorAll("[data-field]").forEach(m=>{m.addEventListener("input",onFieldEdit)}):p.querySelectorAll("[data-field]").forEach(m=>{m.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const m=n._historyId||n.history_id||null;window.bindDrawerClient(m,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const m=document.getElementById("drawer-cat-input");m&&!m.value&&!m.readOnly&&m.focus()},80)}function ma(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function ye(e,n,a,o,s,i,r){const p=_results[_drawerIdx],l=p&&p.edits[e]!==void 0?p.edits[e]:a,d=p&&p.edits[e]!==void 0&&p.edits[e]!==a,m=escapeHtml(l??""),c=s?"":"readonly",u=o==="textarea"?`<textarea data-field="${e}" rows="2">${m}</textarea>`:`<input type="text" data-field="${e}" value="${m}">`;return`
        <div class="drawer-field ${d?"edited":""} ${c}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${u}
        </div>
    `}function jt(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function va(e){return`
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
    `}function ha(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=ot;window.openDrawer=Xt;window.closeDrawer=ha;function ga(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(p){return p&&p.enabled!==!1&&(p.adapter||"").toLowerCase()!=="mrerp_dms"});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let i;if(o.length===1){const p=o[0].name||o[0].adapter||"ERP";i=t("btn-push-to-name",{name:p}),s.title=i}else i=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,s.addEventListener("click",function(p){p.preventDefault(),p.stopPropagation(),o.length===1?Zt(n,o[0].id):ba(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function ba(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(l=>l.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const i=a.map(function(l){const d=escapeHtml(l.name||l.adapter||"ERP"),m=escapeHtml((l.adapter||"").toLowerCase()),u=l.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(l.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+m+"</span>"+d+u+"</span></button>"}).join("");s.innerHTML=i,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",p,!0)},p=l=>{!s.contains(l.target)&&l.target!==e&&!e.contains(l.target)&&r()};setTimeout(()=>document.addEventListener("click",p,!0),0),s.addEventListener("click",l=>{const d=l.target.closest("[data-ep-id]");if(!d)return;const m=d.getAttribute("data-ep-id");r(),Zt(n,m)})}async function Zt(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),i=await s.json();if(!s.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=ga;const ya=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function Qt(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function wa(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function en(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const d=[];for(const m of _results){const c=m.invoices&&m.invoices.length>0?m.invoices:null;if(c&&c.length>1)for(let u=0;u<c.length;u++){const f=c[u]||{};d.push({filename:m.filename+" #"+(u+1)+"/"+c.length,engine:m.engine,merged_fields:f.fields||{}})}else d.push({filename:m.filename,engine:m.engine,merged_fields:m.merged_fields})}a=await apiPost("/api/ocr/export",{records:d,lang:currentLang,template:"sales_detail_th"})}else{const d=[];for(const c of _results)c.history_ids&&Array.isArray(c.history_ids)?d.push(...c.history_ids):c.history_id&&d.push(c.history_id);if(d.length===0){showToast(t("toast-export-error"),"error");return}const m=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+m,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:d,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let d="HTTP "+a.status;try{const c=await a.json();c&&c.detail&&(d=typeof c.detail=="string"?c.detail:JSON.stringify(c.detail))}catch(c){console.warn("[export] resp.json err.detail parse failed:",c)}const m=typeof d=="string"&&d.indexOf(".")>0?"err."+d:null;showToast(m?t(m):t("toast-export-error")+" · "+d,"error");return}const s=await a.blob();let i=o;const r=a.headers.get("X-Filename");if(r)i=r;else{const m=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(m)try{i=decodeURIComponent(m[1])}catch{}}const p=URL.createObjectURL(s),l=document.createElement("a");l.href=p,l.download=i,document.body.appendChild(l),l.click(),document.body.removeChild(l),URL.revokeObjectURL(p),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{en(Qt())});function ka(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=Qt(),o=ya.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
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
    `;n.innerHTML=o+s,e.appendChild(n)}function ut(){const e=document.getElementById("export-dropdown");e&&e.remove()}const ft=document.getElementById("btn-export-arrow");ft&&ft.addEventListener("click",e=>{e.stopPropagation(),!ft.disabled&&ka()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){ut(),showToast(t("cs-coming-soon"),"info");return}wa(a),ut(),en(a);return}e.target.closest("#btn-export-arrow")||ut()});function _a(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(_a,300);const xa=`
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
`;(function(){const e=document.getElementById("page-history");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=xa,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();function xt(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const i=s.filter(r=>_historySelected.has(r.id)).length;a.checked=i===s.length,a.indeterminate=i>0&&i<s.length}}}function Ea(){_historySelected.clear(),xt()}async function Et(){if(!_userInfo){setTimeout(()=>Et(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&s.set("client_id",String(i));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const d=await r.json().catch(()=>({}));if((typeof d.detail=="string"?d.detail:d.detail&&d.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const p=await r.json();_historyState.items=p.items||[],_historyState.total=p.total||0;const l=new Set(_historyState.items.map(d=>d.id));for(const d of Array.from(_historySelected))l.has(d)||_historySelected.delete(d);tn()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function tn(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(d=>{d.confidence==="high"&&s++});const i=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(d=>{const m=new Date(d.created_at),c=String(m.getMonth()+1).padStart(2,"0"),u=String(m.getDate()).padStart(2,"0"),f=String(m.getHours()).padStart(2,"0"),w=String(m.getMinutes()).padStart(2,"0"),S=`${c}-${u} ${f}:${w}`,E=escapeHtml(d.filename||""),v=E.length>50?E.substring(0,50)+"…":E,h=d.invoice_no?escapeHtml(d.invoice_no):v,C=[];d.seller_name&&C.push(escapeHtml(d.seller_name)),d.invoice_no&&d.filename&&C.push(v);const L=C.join(" · ")||"-",A=d.category_tag?`<span class="history-badge category">${escapeHtml(d.category_tag)}</span>`:"",T=d.source_total&&d.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:d.source_index||1,n:d.source_total}))}</span>`:"",k=d.total_amount!==null&&d.total_amount!==void 0?Number(d.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',g=[];(d.total_amount===null||d.total_amount===void 0)&&g.push(t("field-amount")),d.invoice_no||g.push(t("field-invoice-no")),d.invoice_date||g.push(t("field-invoice-date")),d.seller_name||g.push(t("field-seller-name")),g.length>0&&`${escapeHtml(d.id)}${escapeHtml(t("history-needs-review-tip")+" · "+g.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,d.edited&&`${escapeHtml(t("history-edited",{n:d.edit_count||1}))}`;const I=d.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",H=d.confidence==="high"?"high":d.confidence==="medium"?"mid":"low",D=d.confidence==="high"?t("conf-high"):d.confidence==="medium"?t("conf-medium"):t("conf-low"),R=`<span class="history-badge conf-${H}">${escapeHtml(D)}</span>`;let B="";const P=d.source||"manual";return P==="email"?B=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:P==="folder"?B=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:P==="api"&&(B=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(d.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(d.id)}" ${_historySelected.has(d.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${S}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${h} ${A} ${T} ${B} ${I}</div>
                        <div class="history-cell-subtitle">${L}</div>
                    </div>
                    <div class="history-cell-amount">${k}</div>
                    <div class="history-cell-conf">${R}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(d.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),xt();const p=a.length>0?_historyState.page*_historyState.pageSize+1:0,l=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:p,to:l,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=Et;window.renderHistoryList=tn;window.updateHistoryBatchBar=xt;window.clearHistorySelection=Ea;typeof currentRoute<"u"&&currentRoute==="history"&&Et();async function We(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),Ia(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),La(a.id)}catch(n){console.error("open history detail failed",n)}}async function Ba(e){await We(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function Ia(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",Sa),document.getElementById("btn-push-erp").addEventListener("click",Ca)}async function La(e){}async function Ca(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function Sa(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(p=>!p.is_duplicate&&!p.is_copy),s=o>=0?o:0,i=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function Ta(e,n){document.querySelectorAll(".history-popover").forEach(d=>d.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(d=>d.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",i=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const p=()=>{r.remove(),document.removeEventListener("click",l,!0)},l=d=>{!r.contains(d.target)&&d.target!==n&&p()};setTimeout(()=>document.addEventListener("click",l,!0),0),r.addEventListener("click",async d=>{const m=d.target.closest("[data-act]");if(!m||m.disabled)return;const c=m.dataset.act;if(p(),c==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const f=document.createElement("textarea");f.value=s,f.style.position="fixed",f.style.opacity="0",document.body.appendChild(f),f.select(),document.execCommand("copy"),document.body.removeChild(f),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(c==="download-pdf"){const u=showToast(t("history-download-pdf-loading"),"loading",0);try{const f=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!f.ok)throw new Error("download failed");const w=await f.blob(),S=URL.createObjectURL(w),E=document.createElement("a");E.href=S,E.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(E),E.click(),document.body.removeChild(E),setTimeout(()=>URL.revokeObjectURL(S),5e3),u(),showToast(t("history-download-pdf-ok"),"success")}catch{u(),showToast(t("history-download-pdf-fail"),"error")}}else if(c==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const p=r.target.closest(".history-row"),l=r.target.closest("[data-hmenu]");if(l){r.stopPropagation(),Ta(l.dataset.hmenu,l);return}const d=r.target.closest("[data-review]");if(d){r.stopPropagation(),We(d.dataset.review);return}const m=r.target.closest("[data-fill-amount]");if(m){r.stopPropagation(),Ba(m.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||p&&!r.target.closest("[data-hmenu]")&&We(p.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const p=r.target.closest(".history-row-check");if(!p)return;const l=p.dataset.hid;p.checked?_historySelected.add(l):_historySelected.delete(l),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const p=r.target.checked;for(const l of _historyState.items)p?_historySelected.add(l.id):_historySelected.delete(l.id);document.querySelectorAll(".history-row-check").forEach(l=>{l.checked=p}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const l=Array.from(_historySelected);try{const d=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:l})});if(!d.ok)throw new Error("batch delete failed");const m=await d.json();showToast(t("history-batch-done",{n:m.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(d){console.error("batch delete",d),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const p=r.target.value;document.getElementById("history-search-clear").style.display=p?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=p.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=We;const He=document.getElementById("drop-zone"),Bt=document.getElementById("file-input");He.addEventListener("click",()=>Bt.click());Bt.addEventListener("change",e=>nn(e.target.files));["dragover","dragenter"].forEach(e=>{He.addEventListener(e,n=>{n.preventDefault(),He.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{He.addEventListener(e,n=>{n.preventDefault(),He.classList.remove("drag-over")})});He.addEventListener("drop",e=>{e.preventDefault(),nn(e.dataTransfer.files)});const Ma=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function gt(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function $a(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function Ha(e){return $a(e)||gt(e)||Ma.test(e.name)}function nn(e){hideAlerts();const n=Array.from(e),a=n.filter(Ha);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(p=>!gt(p)),s=a.filter(gt),i=new Set(_selectedFiles.map(p=>p.name+"_"+p.size));for(const p of o){const l=p.name+"_"+p.size;i.has(l)||(_selectedFiles.push({file:p,name:p.name,size:p.size,status:"waiting",errorKey:null,errorParams:null}),i.add(l))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(p){console.error("[upload] image route failed",p)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),st(),It(),Bt.value=""}let Ge=!1;function st(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(c=>c.status==="processing"||c.status==="retrying").length,o=_selectedFiles.filter(c=>c.status==="success").length,s=_selectedFiles.filter(c=>c.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const p=Ge?t("file-list-collapse"):t("file-list-expand"),l=_selectedFiles.map((c,u)=>{let f=t("status-"+c.status);c.status==="retrying"&&(f=t("status-retrying")),c.status==="error"&&c.errorKey&&(f=t(c.errorKey,c.errorParams||{}));const w=c.status==="processing"||c.status==="retrying"?'<span class="spinner"></span>':"",S=c.status==="error"&&c.canRetry?`<button class="file-retry-btn" data-retry-idx="${u}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",E=c.status==="success"&&c.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</span>
                ${E}
                <span class="file-status ${c.status}">${w}${f}</span>
                ${S}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(p)}</button>`:""}
        </div>
        <ul class="file-list-body${Ge?" expanded":""}" id="file-list-body">
            ${l}
        </ul>
    `;const d=document.getElementById("file-list-toggle");d&&d.addEventListener("click",()=>{Ge=!Ge,st()});const m=document.getElementById("file-list-body");m&&!m.dataset.retryBound&&(m.dataset.retryBound="1",m.addEventListener("click",async c=>{const u=c.target.closest(".file-retry-btn");if(!u)return;const f=parseInt(u.dataset.retryIdx||"-1",10);if(f<0||f>=_selectedFiles.length)return;const w=_selectedFiles[f];!w||w.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(w,!0)}))}function It(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],st(),renderResults(),It(),hideAlerts()});window.renderFileList=st;window.updateStartButton=It;const Aa=`
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
`;ke("camera-tips-modal",Aa);(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await Pa()||o.click()}),o.addEventListener("change",async p=>{const l=Array.from(p.target.files||[]);if(p.target.value="",l.length!==0)for(const d of l)await bt([d],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=p=>async l=>{const d=Array.from(l.target.files||[]);if(l.target.value="",d.length===0)return;const m=d.filter(u=>u.type==="application/pdf"||/\.pdf$/i.test(u.name)),c=d.filter(u=>!m.includes(u));m.length>0&&await ja(m),c.length>0&&await bt(c,p)};a&&a.addEventListener("change",r("gallery"))})();async function ja(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function Pa(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const i=p=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(p)},r=p=>{p.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),o&&(o.onclick=()=>i(!1)),n.onclick=p=>{p.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}async function Xe(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],i=o.naturalWidth,r=o.naturalHeight;(i<1e3||r<1e3)&&s.push("low_res");try{const p=document.createElement("canvas");p.width=64,p.height=64;const l=p.getContext("2d");l.drawImage(o,0,0,64,64);const d=l.getImageData(0,0,64,64).data;let m=0,c=0;for(let f=0;f<d.length;f+=4)m+=.299*d[f]+.587*d[f+1]+.114*d[f+2],c++;const u=c?m/c:128;u<70?s.push("too_dark"):u>235&&s.push("too_bright"),n({warnings:s,width:i,height:r,brightness:u})}catch{n({warnings:s,width:i,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}let _e=[],Le=null;async function bt(e,n){if(hideAlerts(),!(!e||e.length===0)){var a=typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice";if(a==="thai_id_card"){for(const s of e)_selectedFiles.push({file:s,name:s.name,size:s.size,status:"waiting",errorKey:null,errorParams:null});const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton();return}if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let o=0;o<30&&(await new Promise(s=>setTimeout(s,100)),!(window.jspdf&&window.jspdf.jsPDF));o++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const o=e[0];let s={};try{s=await Xe(o)}catch{}_e.push({file:o,quality:s}),Le="camera",Me();return}if(n==="gallery"&&(e.length>=2||_e.length>0)){for(const o of e){let s={};try{s=await Xe(o)}catch{}_e.push({file:o,quality:s})}Le="gallery",Me();return}await an(e)}}async function Da(e){const n=new Set;for(const o of e)try{((await Xe(o)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const o=await on(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function Me(){let e=document.getElementById("camera-buffer-bar");if(_e.length===0){e&&e.remove(),Le=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=_e.length,a=n>=2,o=Le==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?o?i=`
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
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{_e=[],Le=null,Me()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const l=o?"gallery-input":"camera-input",d=document.getElementById(l);d&&d.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const l=_e.map(d=>d.file);_e=[],Le=null,Me(),await Da(l)});const p=e.querySelector('[data-cbb-action="separate"]');p&&(p.onclick=async()=>{const l=_e.map(d=>d.file);_e=[],Le=null,Me(),await an(l)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{_e.length>0&&Me()});async function an(e){const n=new Set;let a=0;for(const s of e)try{((await Xe(s)).warnings||[]).forEach(p=>n.add(p));const r=await on([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}async function on(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let d=0;d<e.length;d++){const m=e[d],{dataUrl:c,naturalW:u,naturalH:f}=await qa(m);d>0&&s.addPage("a4","p");const w=u/f;let S=a-10,E=S/w;E>o-10&&(E=o-10,S=E*w);const v=(a-S)/2,h=(o-E)/2,C=m.type==="image/png"?"PNG":"JPEG";s.addImage(c,C,v,h,S,E,void 0,"FAST")}const i=s.output("blob"),r=new Date,p=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),l=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${p}${l}.pdf`,{type:"application/pdf"})}function qa(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}window.handleCameraImages=bt;(function(){var e="pearnly_ocr_doc_mode",n=!1,a=!1;function o(u){return typeof escapeHtml=="function"?escapeHtml(u==null?"":String(u)):String(u??"")}function s(){try{return localStorage.getItem(e)==="thai_id_card"?"thai_id_card":"invoice"}catch{return"invoice"}}window.getOcrDocumentMode=function(){return n?s():"invoice"};function i(){var u=document.getElementById("drop-zone");return u?u.closest(".card"):null}function r(){var u=i();if(!u)return null;var f=u.querySelector("#ocr-doc-mode");if(f)return f;var w=u.querySelector(".section-head");return f=document.createElement("div"),f.id="ocr-doc-mode",f.className="ocr-doc-mode",f.setAttribute("role","tablist"),f.style.cssText="display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;",w&&w.parentNode?w.parentNode.insertBefore(f,w.nextSibling):u.insertBefore(f,u.firstChild),f}function p(u,f,w){return'<button type="button" class="ocr-doc-seg'+(w?" active":"")+'" data-doc-mode="'+u+'" role="tab" aria-selected="'+(w?"true":"false")+'" style="border:none;background:'+(w?"var(--card,#fff)":"transparent")+";color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:"+(w?"600":"500")+";padding:6px 16px;border-radius:7px;cursor:pointer;box-shadow:"+(w?"0 1px 3px rgba(0,0,0,.08)":"none")+';transition:background .15s;">'+o(t(f))+"</button>"}function l(){var u=r();if(u){if(!n){u.style.display="none";return}var f=s();u.style.display="flex",u.innerHTML=p("invoice","ocr-mode-invoice",f==="invoice")+p("thai_id_card","ocr-mode-id-card",f==="thai_id_card")}}function d(u){try{localStorage.setItem(e,u==="thai_id_card"?"thai_id_card":"invoice")}catch{}l();try{document.dispatchEvent(new CustomEvent("ocr-doc-mode-change",{detail:{mode:window.getOcrDocumentMode()}}))}catch{}}async function m(u){if(!(a&&!u)){var f=localStorage.getItem("mrpilot_token");if(f)try{var w=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+f}});if(!w.ok)return;var S=await w.json(),E=S&&S.items||[];n=E.some(function(v){return v&&(v.adapter||"").toLowerCase()==="mrerp_dms"&&v.enabled!==!1}),a=!0,window._dmsHasEndpoint=n,l()}catch{}}}window._refreshOcrDocMode=function(){m(!0)},document.addEventListener("click",function(u){var f=u.target.closest(".ocr-doc-seg");f&&f.getAttribute("data-doc-mode")&&(u.preventDefault(),d(f.getAttribute("data-doc-mode")))}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("ocr-doc-mode",l);function c(){r(),l(),m(!1)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),window.addEventListener("hashchange",function(){((location.hash||"").indexOf("ocr")>=0||location.hash===""||location.hash==="#home")&&setTimeout(function(){r(),m(!1)},60)})})();(function(){function e(i){return typeof escapeHtml=="function"?escapeHtml(i==null?"":String(i)):String(i??"")}function n(){var i=(function(){var p=document.getElementById("drop-zone");return p?p.closest(".card"):null})();if(!i||!i.parentNode)return null;var r=document.getElementById("dms-id-card-result");return r||(r=document.createElement("div"),r.id="dms-id-card-result",r.className="card",r.style.cssText="display:none;margin-top:16px;",i.parentNode.insertBefore(r,i.nextSibling),r)}function a(i,r){return'<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);"><span style="color:var(--muted,#6b6b66);font-size:13px;">'+e(t(i))+'</span><span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">'+e(r||"—")+"</span></div>"}function o(i){if(!i)return"";var r=[i.house_no,i.road,i.subdistrict,i.district,i.province,i.zipcode].filter(function(p){return p});return r.join(" ")||i.address_raw||""}function s(i){var r=i&&i.status||"failed",p,l,d;return r==="success"?(p="#0a7a2c",l="#d6f5e0",d="dms-result-status-success"):r==="needs_review"?(p="#9a6b00",l="#fdf0d0",d="dms-result-status-needs-review"):r==="skipped"?(p="#5d5d57",l="#eee",d="dms-result-status-skipped"):(p="#b3261e",l="#fbe0de",d="dms-result-status-failed"),'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:'+p+";background:"+l+';">'+e(t(d))+"</span>"}window.renderDmsIdCardResult=function(i){var r=n();if(r){i=i||{};var p=i.id_card||{},l=p.address||{},d=i.dms_push||{},m=d.status||(i.ok?"success":"failed"),c="";m==="success"&&(c=a("dms-result-customer",d.customer_id)+a("dms-result-booking",d.booking_no));var u=m==="failed"||m==="needs_review"?'<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">'+e(t("dms-result-retry"))+"</button>":"",f="";if(m==="failed"&&d.error_code){var w="dms-err-"+String(d.error_code).toLowerCase(),S=t(w);(!S||S===w)&&(S=t("dms-err-err_dms_unexpected")),f='<div style="margin-top:8px;color:#b3261e;font-size:12px;">'+e(S)+"</div>"}r.style.display="",r.innerHTML='<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;"><div class="section-title">'+e(t("dms-result-title"))+"</div>"+s(d)+'</div><div style="margin-top:8px;">'+a("dms-result-name",(p.first_name||"")+" "+(p.last_name||""))+a("dms-result-id",p.people_id_masked)+a("dms-result-birthday",p.birthday_be)+a("dms-result-address",o(l))+c+"</div>"+f+u}},window.clearDmsIdCardResult=function(){var i=document.getElementById("dms-id-card-result");i&&(i.style.display="none",i.innerHTML="")},document.addEventListener("click",function(i){i.target.closest("#dms-id-card-retry")&&(i.preventDefault(),typeof window._dmsRetryIdCard=="function"&&window._dmsRetryIdCard())})})();document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,(typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice")==="thai_id_card"){try{await sn()}finally{const c=document.getElementById("btn-start");c&&(c.disabled=!1)}return}if(_userInfo&&_userInfo.plan==="free"){const c=await fetch("/api/health").then(u=>u.json()).catch(()=>null);c&&!c.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const n=_selectedFiles.filter(c=>c.status==="waiting"),a=6;async function o(c,u){if(window._ocrAborted)return c.status="cancelled",c.errorKey=null,renderFileList(),{};c.status=u?"retrying":"processing",c.canRetry=!1,renderFileList();const f=new AbortController,w=setTimeout(()=>f.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(f);try{const S=new FormData;S.append("file",c.file,c.name);try{if(typeof window.getCurrentClientId=="function"){const L=window.getCurrentClientId();L!=null&&S.append("client_id",String(L))}}catch{}const E=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:S,signal:f.signal});if(clearTimeout(w),window._ocrCtrls.delete(f),E.status===401||E.status===403){const A=await E.clone().json().catch(()=>({})),T=A&&A.detail,k=typeof T=="string"?T:T&&T.code||"";if(!k||k.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),k==="auth.session_revoked")_showSessionRevokedModal();else{const g=k==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(g),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}k==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!E.ok){const A=(await E.json().catch(()=>({}))).detail;return typeof A=="string"?(c.errorKey="err."+A,c.errorParams=null):A&&A.code?(c.errorKey="err."+A.code,c.errorParams={...A,mb:_quota.max_file_size_mb}):(c.errorKey="err.unknown",c.errorParams=null),(c.errorKey==="err.unknown"||c.errorKey==="err.ocr.engine_error")&&(E.status===429?c.errorKey="err.rate_limit":E.status===502||E.status===503||E.status===504?c.errorKey="err.gemini_overloaded":E.status>=500&&(c.errorKey="err.server")),c.status="error",c.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(c.errorKey||""),renderFileList(),{}}const v=await E.json();c.status="success",c.fromCache=!!v.from_cache;const h=mergeFields(v.pages),C=v.confidence||(h.items&&h.items.length>0?"high":"low");if(_results.push({filename:v.filename,pages:v.pages,page_count:v.page_count,elapsed_ms:v.elapsed_ms,engine:v.engine,merged_fields:h,edits:{},confidence:C,history_id:v.history_id,history_ids:v.history_ids||[],invoice_count:v.invoice_count||1,invoices:v.invoices||[],archive_name:v.archive_name||null,category_tag:v.category_tag||null,auto_pushed:!!v.auto_pushed,typhoon_enhanced:!!v.typhoon_enhanced,typhoon_pages:v.typhoon_pages||[],from_cache:!!v.from_cache}),v.invoice_count&&v.invoice_count>1&&showToast(t("multi-invoice-toast",{file:v.filename,n:v.invoice_count}),"success"),v.missed_invoice_warnings&&v.missed_invoice_warnings.length){const L=v.missed_invoice_warnings.map(function(A){return A.page}).filter(function(A){return A!=null});showToast(t("missed-invoice-warn",{file:v.filename,pages:L.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",v.missed_invoice_warnings)}if(v.typhoon_enhanced&&v.typhoon_pages&&v.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:v.filename,n:v.typhoon_pages.length}),"success"),v.fallback_used){const L=v.engine_chain||[],A=v.engine||"";let T;A==="typhoon_nvidia"?T="fallback-typhoon-nvidia-toast":A==="easyocr"?T="fallback-easyocr-toast":T="fallback-generic-toast",showToast(t(T,{file:v.filename}),"warn"),console.info("[OCR Chain]",L)}if(v.from_cache&&showToast(t("cache-hit-toast",{file:v.filename}),"info"),v.duplicate_warnings&&v.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const L of v.duplicate_warnings)window._dupQueue.push({filename:v.filename,...L})}return v.auto_pushed&&showToast(t("auto-push-fired",{file:v.filename}),"info"),v.quota&&v.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=v.quota.used_this_month,_userInfo.tenant_used=v.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(S){clearTimeout(w);try{window._ocrCtrls&&window._ocrCtrls.delete(f)}catch{}console.error("[Upload] failed for",c.file.name,S);const E=S&&(S.name==="AbortError"||S==="timeout"),v=E&&(f.signal.reason==="timeout"||S==="timeout"),h=S&&S.message&&/NetworkError|Failed to fetch/i.test(S.message);return E&&(f.signal.reason==="user_stop"||window._ocrAborted)?(c.status="cancelled",c.errorKey=null,c.canRetry=!1,renderFileList(),{}):(v?c.errorKey="err.timeout":E?c.errorKey="err.aborted":h?c.errorKey="err.network":(c.errorKey="err.unknown",c.errorParams={msg:S&&S.message?S.message:String(S)}),c.status="error",!u&&!window._ocrAborted&&(h||v)&&navigator.onLine!==!1&&(c.canRetry=!0,renderFileList(),await new Promise(L=>setTimeout(L,2e3)),c.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?o(c,!0):(c.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=o;let s=0,i=!1;async function r(){for(;s<n.length&&!i&&!window._ocrAborted;){const c=s++,u=await o(n[c]);if(u&&u.abort){i=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const p=document.getElementById("btn-start"),l=document.getElementById("btn-stop");p&&(p.style.display="none"),l&&(l.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(n)}catch{}const d=[];for(let c=0;c<Math.min(a,n.length);c++)d.push(r());await Promise.all(d);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}p&&(p.style.display=""),l&&(l.style.display="none");const m=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const c={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const f of n)if(f.status==="success")c.success++;else if(f.status==="cancelled")c.cancelled++;else if(f.status==="error"){const w=f.errorKey||"";w==="err.network"?c.network++:w==="err.timeout"||w==="err.aborted"?c.timeout++:w.indexOf("quota")>=0||w==="err.monthly_limit_exceeded"?c.quota++:w==="err.gemini_overloaded"||w==="err.server"?c.overloaded++:w==="err.rate_limit"?c.rate++:c.other++}const u=n.length;m?showToast(Ra(c,u),"warn",4e3):u>1&&c.network+c.timeout+c.quota+c.overloaded+c.rate+c.other>0&&showToast(za(c),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function Ra(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function za(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});async function sn(e){let n;if(e)n=_selectedFiles.find(a=>a.file===e)||{file:e,name:e.name,status:"waiting"};else{const a=_selectedFiles.filter(o=>o.status==="waiting");if(!a.length)return;n=a[0]}window._dmsLastFile=n.file,n.status="processing",typeof renderFileList=="function"&&renderFileList();try{const a=new FormData;a.append("file",n.file,n.name),a.append("push","true");const o=await fetch("/api/dms/id-card-booking",{method:"POST",headers:{Authorization:"Bearer "+token},body:a});if(o.status===401||o.status===403){const i=await o.clone().json().catch(()=>({})),r=i&&i.detail,p=typeof r=="string"?r:r&&r.code||"";if(!p||p.startsWith("auth.")){localStorage.removeItem("mrpilot_token"),showToast(t("alert-session"),"error"),setTimeout(()=>{window.location.href="/"},1200);return}}const s=await o.json().catch(()=>({}));if(!o.ok){n.status="error";const i=s&&s.detail&&(s.detail.code||s.detail)||"unknown";n.errorKey="err."+i,n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:String(i)}});return}n.status=s.ok||s.dms_push&&s.dms_push.status==="needs_review"?"success":"error",typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult(s),typeof updateStartButton=="function"&&updateStartButton()}catch{n.status="error",n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:"network"}})}}window._dmsRetryIdCard=function(){window._dmsLastFile&&sn(window._dmsLastFile)};function rn(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=f=>f!=null?Number(f).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",p=f=>f||"—",l=f=>{try{const w=new Date(f);return`${w.getFullYear()}-${String(w.getMonth()+1).padStart(2,"0")}-${String(w.getDate()).padStart(2,"0")}`}catch{return f}},d=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",m=(e.matched_fields||[]).map(f=>{const w=t("dup-field-"+f.replace("_","-"))||f;return`<span class="dup-field-chip">${escapeHtml(w)}</span>`}).join(" "),c=document.createElement("div");c.className="log-detail-modal",c.innerHTML=`
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
                    <div class="dup-source-label">${escapeHtml(t("dup-current-file"))}${escapeHtml(d)}</div>
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
                        <tr><td>${escapeHtml(t("dup-field-invoice-date"))}</td><td>${escapeHtml(p(e.current.invoice_date))}</td><td>${escapeHtml(p(e.match.invoice_date))}</td></tr>
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
    `,document.body.appendChild(c);const u=()=>{c.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(rn,200)};c.querySelector(".dup-close").addEventListener("click",u),c.querySelector('[data-action="view"]').addEventListener("click",()=>{const f=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(f)},400),u()}),c.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const f=e.new_history_id;if(!f){u();return}try{(await fetch(`/api/history/${encodeURIComponent(f)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}u()}),c.querySelector('[data-action="keep"]').addEventListener("click",u)}window.showDuplicateDialog=rn;function Se(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function Pe(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function Na(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Se("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Se("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Se("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Se("time-day-ago-suffix"," 天前")}catch{return""}}async function Lt(){ln();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const p={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[l,d,m]=await Promise.all([fetch("/api/me/tenant-usage",{headers:p}).then(E=>E.ok?E.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:p}).then(E=>E.ok?E.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:p}).then(E=>E.ok?E.json():null).catch(()=>null)]),c=l&&l.ocr_this_month||0;let u=0;const f=d&&(d.items||d.history||d)||[],w=Array.isArray(f)?f:[];w.forEach(E=>{(E.status==="pending"||E.status==="reviewing")&&u++});const S=m&&(m.total||m.count||m.pending||0)||0;if(e&&(e.textContent=Pe(c)),n&&(n.textContent=Pe(u)),a&&(a.textContent=Pe(S)),r&&(S>0?(r.style.display="",r.textContent=S):r.style.display="none"),o&&l){const E=l.ocr_this_month||0,v=l.quota||0;o.textContent=Pe(E),s&&(s.textContent=v?E+" / "+Pe(v)+" 张":Se("dash-kpi-plan-sub","本月用量"))}if(i)if(w.length===0)i.innerHTML='<div class="dash-recent-empty">'+Se("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const E=w.slice(0,5).map(v=>{const h=(v.invoice_no||v.filename||v.id||"").toString(),C=(v.supplier_name||v.buyer_name||v.client_name||v.notes||"").toString(),L=Na(v.created_at||v.upload_time||v.date),A=T=>String(T).replace(/[&<>"']/g,k=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[k]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+A(h)+'">'+A(h)+'</span><span class="dash-recent-mid" title="'+A(C)+'">'+A(C)+'</span><span class="dash-recent-time">'+A(L)+"</span></div>"}).join("");i.innerHTML=E}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+Se("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Lt;async function ln(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},p=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!p.ok){e.style.display="none",s&&(s.textContent="—"),i&&(i.textContent="");return}const l=await p.json(),d=!!l.is_owner,m=!!l.is_billing_exempt;if(!d)e.style.display="none";else if(e.style.display="",m)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const u=typeof l.balance_thb=="number"?l.balance_thb:0;if(a&&(a.textContent="฿"+u.toFixed(2),a.className=u<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const f=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",w=u<50?"#dc2626":"#6b7280",S=E=>typeof window.escapeHtml=="function"?window.escapeHtml(E):String(E).replace(/[&<>"']/g,v=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[v]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+w+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+S(f)+"</a>"}}const c=typeof l.pages_this_month=="number"?l.pages_this_month:typeof l.my_invoice_count=="number"?l.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(c)),i){const u=c>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",f=typeof window.t=="function"?window.t(u,{used:c}):c+" pages";i.textContent=f}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=ln;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Lt,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Lt()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function Ct(){return localStorage.getItem("mrpilot_token")||""}function ve(e){return document.getElementById(e)}var Je=null,Re=null;function cn(){Re||(Re=setInterval(function(){if(!document.hidden){var e=Ct();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;Je!==null&&a>Je&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Je=a}}).catch(function(){}))}},3e4))}function Fa(){Re&&(clearInterval(Re),Re=null),Je=null}window._startCreditsPoll=cn;window._stopCreditsPoll=Fa;cn();var St=null,Tt=0;function Oa(){if(!ve("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),Va()}}function dn(){var e=function(n,a){var o=ve(n);o&&(o.textContent=a)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function Fe(e){[1,2,3].forEach(function(s){var i=ve("tv2-s"+s);i&&(i.style.display=s===e?"":"none");var r=ve("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=ve("tv2-back"),a=ve("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=he("topup-btn-cancel")):n&&(n.style.display="",n.textContent=he("topup-btn-back")),a&&(a.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=ve("tv2-bn");o&&(o.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(Tt).toLocaleString()+"</strong>"))}}function yt(){for(var e=1;e<=3;e++){var n=ve("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function Ze(e){var n=ve(e);n&&(n.textContent="",n.style.display="none")}function ze(e,n){var a=ve(e);a&&(a.textContent=n,a.style.display="")}function Pt(e){var n=ve("tv2-dt");n&&(n.textContent=e.name);var a=ve("tv2-drop");a&&a.classList.add("has-file"),Ze("tv2-se")}function Va(){var e=ve("topup-v2-ov");ve("tv2-close").addEventListener("click",De),e.addEventListener("click",function(i){i.target===e&&De()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&De()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(l){l.classList.remove("active")}),r.classList.add("active");var p=ve("tv2-amt");p&&(p.value=r.dataset.val,Ze("tv2-ae"))}});var n=ve("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),Ze("tv2-ae")});var a=ve("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=he("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var o=ve("tv2-drop"),s=ve("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(i){i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(i){i.preventDefault(),o.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&Pt(r)})),s&&s.addEventListener("change",function(){s.files[0]&&Pt(s.files[0])}),ve("tv2-back").addEventListener("click",function(){var i=yt();if(i<=1){De();return}Fe(i-1)}),ve("tv2-next").addEventListener("click",function(){var i=yt();i===1?Ua():i===2?Fe(3):Ga()})}async function Ua(){var e=ve("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){ze("tv2-ae",he("topup-amount-invalid"));return}if(n>5e5){ze("tv2-ae",he("topup-amount-too-large"));return}Tt=n;var a=ve("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+Ct()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),i=he("topup-submit-fail");try{var r=JSON.parse(s),p=r.detail;if(Array.isArray(p)&&p.length){var l=p[0]&&p[0].type||"";l.indexOf("less_than")>=0?i=he("topup-amount-too-large"):(l.indexOf("greater_than")>=0||l.indexOf("parsing")>=0)&&(i=he("topup-amount-invalid"))}else typeof p=="string"&&(i=p)}catch{}throw new Error(i)}var d=await o.json();St=d.request_id,Fe(2)}catch(m){ze("tv2-ae",m.message||he("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=he("topup-btn-next"))}}async function Ga(){var e=ve("tv2-file");if(!e||!e.files||!e.files[0]){ze("tv2-se",he("topup-slip-required"));return}var n=ve("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=ve("tv2-payer"),s=ve("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+St,{method:"POST",headers:{Authorization:"Bearer "+Ct()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),De()}catch(p){ze("tv2-ue",he("topup-upload-fail")+" · "+p.message),n&&(n.disabled=!1,n.textContent=he("topup-btn-submit"))}}function De(){var e=ve("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){Oa(),St=null,Tt=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=ve(a);o&&(o.value="")});var e=ve("tv2-file");e&&(e.value="");var n=ve("tv2-drop");n&&n.classList.remove("has-file","drag-over"),ve("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){Ze(a)}),dn(),Fe(1),ve("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=ve("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(dn(),Fe(yt()))});const Ka=`
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

    `;ke("page-test-center",Ka);(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",i=!1,r=!1;function p(G,F,Q){let oe=typeof t=="function"?t(G):null;return(!oe||oe===G)&&(oe=F),Q&&Object.keys(Q).forEach(function($){oe=String(oe).replace("{"+$+"}",String(Q[$]))}),oe}function l(){try{const G=localStorage.getItem(n);o=G?JSON.parse(G):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function d(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function m(G){const F=new Date(G),Q=function(oe){return oe<10?"0"+oe:""+oe};return Q(F.getHours())+":"+Q(F.getMinutes())+":"+Q(F.getSeconds())}function c(G){return String(G??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function u(G,F){try{typeof showToast=="function"?showToast(G,F||"info"):alert(G)}catch{}}function f(G){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(G).then(function(){u(p("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){w(G)}):w(G)}catch{w(G)}}function w(G){try{const F=document.createElement("textarea");F.value=G,F.style.position="fixed",F.style.opacity="0",document.body.appendChild(F),F.select();const Q=document.execCommand("copy");document.body.removeChild(F),u(Q?p("tc-toast-copied","已复制"):p("tc-toast-copy-fail","复制失败"),Q?"success":"error")}catch{u(p("tc-toast-copy-fail","复制失败"),"error")}}function S(){const G=document.getElementById("tc-account-chip"),F=document.getElementById("tc-progress-chip");if(G&&(G.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),F){const Q=a.length,oe=a.filter(function($){return o[$.id]}).length;F.textContent=oe+" / "+Q}}function E(){const G=document.getElementById("tc-checklist-body");if(!G)return;const F={};a.forEach(function(oe){F[oe.group]||(F[oe.group]=[]),F[oe.group].push(oe)});const Q=[];Object.keys(F).forEach(function(oe){Q.push('<div class="tc-checklist-group">'),Q.push('<div class="tc-checklist-group-title">'+c(oe)+"</div>"),F[oe].forEach(function($){const x=o[$.id]||"",y=x?"is-"+x:"";Q.push('<div class="tc-check-item '+y+'" data-id="'+c($.id)+'"><div class="tc-check-id">'+c($.id)+'</div><div class="tc-check-desc">'+c($.desc)+'</div><div class="tc-check-actions">'+v($.id,"pass",x)+v($.id,"fail",x)+v($.id,"skip",x)+"</div></div>")}),Q.push("</div>")}),G.innerHTML=Q.join("")}function v(G,F,Q){const oe=Q===F,$={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},x={pass:p("tc-status-pass","通过"),fail:p("tc-status-fail","失败"),skip:p("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(oe?"is-active "+F:"")+'" data-id="'+c(G)+'" data-kind="'+F+'" title="'+c(x[F])+'">'+$[F]+"</button>"}function h(G){return s==="all"?!0:s==="js_error"?G.type==="js_error"||G.type==="promise_error":s==="api"?G.type==="api_error"||G.type==="api_fail":s==="api_slow"?G.type==="api_slow":s==="console"?G.type==="console_error"||G.type==="console_warn":!0}function C(){const G=document.getElementById("tc-logs-body"),F=document.getElementById("tc-logs-count");if(!G)return;const Q=(window._pearnlyTcLogs||[]).slice().reverse(),oe=Q.filter(h);if(F&&(F.textContent=String(Q.length)),oe.length===0){G.innerHTML='<div class="tc-logs-empty">'+c(p("tc-logs-empty","暂无异常"))+"</div>";return}const $=oe.slice(0,100).map(function(x){const y=typeof x.detail=="object"?JSON.stringify(x.detail,null,2):String(x.detail||"");return'<div class="tc-log-item t-'+c(x.type)+'" data-ts="'+x.ts+'"><span class="tc-log-time">'+m(x.ts)+'</span><span class="tc-log-type">'+c(x.type)+'</span><div class="tc-log-summary">'+c(x.summary)+'<div class="tc-log-detail">'+c(y)+"</div></div></div>"}).join("");G.innerHTML=$,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(x){x.classList.toggle("active",x.getAttribute("data-filter")===s)})}function L(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&C(),A()},200))}window._tcOnNewLog=L;function A(){const G=document.getElementById("nav-test-badge");if(!G)return;const F=(window._pearnlyTcLogs||[]).filter(function(Q){return Q.type==="js_error"||Q.type==="promise_error"||Q.type==="api_error"||Q.type==="api_fail"||Q.type==="console_error"}).length;F>0?(G.style.display="",G.textContent=F>99?"99+":String(F)):G.style.display="none"}function T(){S(),E(),C(),A()}function k(){const G=[],F=new Date,Q=_userInfo&&(_userInfo.email||_userInfo.username)||"—";G.push("# Pearnly "+e+" 测试结果"),G.push("- 账号:"+Q),G.push("- 时间:"+F.toISOString().replace("T"," ").slice(0,19));const oe=a.length,$=a.filter(function(Z){return o[Z.id]==="pass"}).length,x=a.filter(function(Z){return o[Z.id]==="fail"}).length,y=a.filter(function(Z){return o[Z.id]==="skip"}).length,q=oe-$-x-y;G.push("- 进度:"+($+x+y)+" / "+oe+" · ✅ "+$+" · ❌ "+x+" · ⏭ "+y+" · 未测 "+q),G.push(""),G.push("| ID | 描述 | 状态 |"),G.push("|---|---|---|"),a.forEach(function(Z){const le=o[Z.id],re=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";G.push("| "+Z.id+" | "+Z.desc.replace(/\|/g,"\\|")+" | "+re+" |")});const z=a.filter(function(Z){return o[Z.id]==="fail"});z.length>0&&(G.push(""),G.push("## ❌ 失败项"),z.forEach(function(Z){G.push("- **"+Z.id+"** · "+Z.desc)}));const Y=(window._pearnlyTcLogs||[]).slice(-30).reverse();return Y.length>0&&(G.push(""),G.push("## 🔴 异常日志(最近 "+Y.length+" 条)"),Y.forEach(function(Z){if(G.push("- `"+m(Z.ts)+"` · **"+Z.type+"** · "+Z.summary),Z.detail){let le;try{le=JSON.stringify(Z.detail)}catch{le=String(Z.detail)}le&&le!=="{}"&&G.push("  - "+le.slice(0,600))}})),G.join(`
`)}function g(G){const F=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(F.length===0)return"(暂无异常日志)";const Q=["# Pearnly 异常日志(最近 "+F.length+" 条)"],oe=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return Q.push("- 账号:"+oe),Q.push("- 当前页:"+(currentRoute||"?")),Q.push("- UA:"+navigator.userAgent),Q.push(""),F.forEach(function($){if(Q.push("## `"+m($.ts)+"` · "+$.type),Q.push("- "+$.summary),$.detail){Q.push("```");try{Q.push(JSON.stringify($.detail,null,2).slice(0,2e3))}catch{Q.push(String($.detail).slice(0,2e3))}Q.push("```")}}),Q.join(`
`)}function I(){const G=Date.now();fetch("/api/health").then(function(F){const Q=Date.now()-G;F.ok?u(p("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:Q}),"success"):u(p("tc-toast-health-fail","后端无响应")+" ("+F.status+")","error")}).catch(function(){u(p("tc-toast-health-fail","后端无响应"),"error")})}function H(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}T(),u(p("tc-toast-cleared","session 状态已清空"),"success")}function D(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(G){return G.json()}).then(function(G){window._clientsCache=G.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),u("客户缓存已刷新 · "+(G.clients||[]).length+" 个客户","success")}).catch(function(){u("刷新失败","error")})}catch{}}function R(){if(i||!document.getElementById("page-test-center"))return;i=!0;const F=document.getElementById("tc-checklist-body");F&&F.addEventListener("click",function(le){const re=le.target.closest(".tc-status-btn");if(!re)return;const K=re.getAttribute("data-id"),ee=re.getAttribute("data-kind");!K||!ee||(o[K]===ee?delete o[K]:o[K]=ee,d(),E(),S())});const Q=document.getElementById("tc-btn-reset-checklist");Q&&Q.addEventListener("click",function(){o={},d(),E(),S()});const oe=document.getElementById("tc-btn-copy-all");oe&&oe.addEventListener("click",function(){f(k())});const $=document.getElementById("tc-btn-copy-logs");$&&$.addEventListener("click",function(){f(g())});const x=document.getElementById("tc-btn-clear-logs");x&&x.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,C(),A()});const y=document.getElementById("tc-logs-filter");y&&y.addEventListener("click",function(le){const re=le.target.closest(".tc-filter-chip");re&&(s=re.getAttribute("data-filter")||"all",C())});const q=document.getElementById("tc-logs-body");q&&q.addEventListener("click",function(le){const re=le.target.closest(".tc-log-item");re&&re.classList.toggle("expanded")});const z=document.getElementById("tc-tool-health");z&&z.addEventListener("click",I);const Y=document.getElementById("tc-tool-clear-session");Y&&Y.addEventListener("click",H);const Z=document.getElementById("tc-tool-reload-clients");Z&&Z.addEventListener("click",D)}function B(){}window._tcApplyVisibility=B;let P=0;const U=setInterval(function(){P++,_userInfo&&clearInterval(U),P>60&&clearInterval(U)},500);window.loadTestCenterPage=function(){l(),R(),T()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){A(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&T()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(h,C){if(typeof window.t=="function"){const L=window.t(h);if(L&&L!==h)return L}return C}function o(){const h=window._userInfo||{},C=String(h.role||"").toLowerCase(),L=String(h.tenant_role||"").toLowerCase();return h.is_super_admin===!0||h.is_owner===!0||C==="owner"||C==="admin"||L==="owner"||L==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const h=localStorage.getItem(e);if(!h||h==="null"||h==="0"||h==="")return null;const C=parseInt(h,10);return isNaN(C)?null:C}function r(h){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:h,mode:s()}}))}catch{}}function p(h){const C=i();h==null||h===0?localStorage.removeItem(e):(localStorage.setItem(e,String(h)),localStorage.setItem(n,"client")),String(C)!==String(h)&&r(h)}function l(){const h=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),h!=null&&r(null)}async function d(){try{const h=window.apiGet;if(typeof h!="function")return[];const C=await h("/api/workspace/clients");return C&&(C.clients||C.items)||[]}catch{return[]}}async function m(h){if(s()==="client"&&i()!=null)return typeof h=="function"&&h(),!0;const C=a("ws-need-client","这个功能需要先选择工作空间"),L=a("ws-btn-pick","选择工作空间"),A=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(C,{okText:L,cancelText:A})&&c(h):window.confirm(C+`

[`+L+" / "+A+"]")&&c(h),!1}async function c(h){const C=await d();if(typeof h=="function"&&s()!=="personal"&&C.length===1){p(Number(C[0].id)),h();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:C,canCreate:o(),active:i(),onPersonal:l,onPick:function(L){p(Number(L)),typeof h=="function"&&h()},emptyHint:C.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!C.length){const L=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(L,"info")}}function u(h){const C=h||document.getElementById("workspace-switcher-root");if(!C)return;const L=s(),A=i();let T,k;if(L==="client"&&A!=null){const H=(window._workspaceClientsCache||[]).find(D=>Number(D.id)===Number(A));T=w("building"),k=H?H.name:a("ws-current-label","当前工作空间")}else T=w("user"),k=a("ws-personal","个人事务");C.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+T+'<span class="ws-ctrl-label">'+f(k)+"</span></button>";const g=C.querySelector("#ws-ctrl-btn");g&&g.addEventListener("click",()=>c(null))}function f(h){return String(h??"").replace(/[&<>"']/g,function(C){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[C]})}function w(h){const C='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return h==="building"?C+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':C+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function S(h){h=h||{};const C=h.clients||[],L=h.active,A=document.getElementById("ws-modal");A&&A.remove();const T=document.createElement("div");T.id="ws-modal",T.className="ws-modal";const g='<button type="button" class="ws-modal-item'+(s()==="personal"||L==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+w("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+f(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+f(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let I="";if(C.length){const P=['<option value="">'+f(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(C.map(function(U){const G=L!=null&&Number(L)===Number(U.id);return'<option value="'+f(U.id)+'"'+(G?" selected":"")+">"+f(U.name||"#"+U.id)+"</option>"}));I='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+f(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+P.join("")+"</select></div>"}const H=!C.length&&h.emptyHint?'<div class="ws-modal-empty">'+f(h.emptyHint)+"</div>":"",D=h.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+f(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+f(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+f(a("ws-create-submit","创建"))+"</button></div></div>":"";T.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+f(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+f(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+g+I+"</div>"+H+D+"</div>",document.body.appendChild(T);const R=T.querySelector("[data-ws-select]");R&&R.addEventListener("change",function(){const P=R.value;P&&(typeof h.onPick=="function"&&h.onPick(P),B(),u())});function B(){T.remove()}T.addEventListener("click",function(P){if(P.target===T||P.target.closest("[data-ws-close]")){B();return}if(P.target.closest("[data-ws-personal]")){typeof h.onPersonal=="function"&&h.onPersonal(),B(),u();return}const G=P.target.closest("[data-ws-pick]");if(G){const oe=G.getAttribute("data-ws-pick");typeof h.onPick=="function"&&h.onPick(oe),B(),u();return}if(P.target.closest("[data-ws-create-toggle]")){const oe=T.querySelector("[data-ws-create-form]");if(oe){oe.style.display=oe.style.display==="none"?"flex":"none";const $=oe.querySelector("[data-ws-create-name]");$&&$.focus()}return}if(P.target.closest("[data-ws-create-submit]")){E(T,h,B);return}})}async function E(h,C,L){const A=h.querySelector("[data-ws-create-name]"),T=A?(A.value||"").trim():"";if(!T){A&&A.focus();return}let k=null;try{if(typeof window.apiPost=="function"){const I=await window.apiPost("/api/workspace/clients",{name:T});k=I&&typeof I.json=="function"?await I.json().catch(()=>null):I}}catch{k=null}const g=k&&(k.id||k.client&&k.client.id);if(!g){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await d(),p(Number(g)),C.onPick,L(),u()}window.openWorkspaceChooserUI=S,window.addEventListener("pearnly:workspace-changed",function(){u()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=p,window.enterPersonalMode=l,window.requireWorkspace=m,window.openWorkspaceChooser=c,window.renderWorkspaceControl=u,window.fetchWorkspaceClients=d;function v(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){c(null)},800)}catch{}}d().then(h=>{window._workspaceClientsCache=h,u(),v()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",u)})();(function(){const e=L=>document.querySelector('[data-num-target="'+L+'"]');function n(L){if(!L)return t("reconcile-last-activity-none");try{const A=new Date(L),T=new Date,k=T-A;if(k/6e4<5)return t("reconcile-last-activity-just-now");if(A.toDateString()===T.toDateString())return t("reconcile-last-activity-today");const I=Math.max(1,Math.floor(k/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",I)}catch{return t("reconcile-last-activity-none")}}function a(L,A,T){const k=e(L);k&&(k.textContent=T?"-":String(A),k.classList.toggle("is-empty",!!T))}function o(L){const A=document.getElementById("reconcile-error");A&&(A.style.display=L?"flex":"none")}function s(L){const A=document.getElementById("reconcile-empty");A&&(A.style.display=L?"flex":"none")}function i(L,A){const T=document.getElementById("reconcile-last-activity");T&&(T.textContent=L,T.classList.toggle("has-data",!!A))}function r(L){const A=!L||(L.total_sessions||0)===0;a("pending",L.pending||0,A),a("matched",L.matched||0,A),a("unmatched",L.unmatched||0,A),i(n(L.last_activity_at),!!L.last_activity_at),o(!1),s(A)}function p(L){const A=L.toUpperCase();return A==="KBANK"?"bank-chip-kbank":A==="SCB"?"bank-chip-scb":A==="BBL"?"bank-chip-bbl":A==="KTB"?"bank-chip-ktb":A==="TTB"?"bank-chip-ttb":"bank-chip-other"}function l(L,A){const T=k=>k?String(k).slice(0,10):"?";return!L&&!A?"":T(L)+" ~ "+T(A)}function d(L){return L==null?"":String(L).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function m(L){const A=document.getElementById("reconcile-recent"),T=document.getElementById("reconcile-recent-list");if(!A||!T)return;const k=(L||[]).slice(0,20);if(k.length===0){A.style.display="none";return}A.style.display="",s(!1),T.innerHTML=k.map(g=>{const I=g.parse_status==="parse_failed",H=g.bank_code||"OTHER",D=g.account_last4?" ···"+d(g.account_last4):"",R=l(g.period_start,g.period_end),B=d(g.source_filename||""),P=Number(g.tx_count||0),U=I?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",P)+"</span>";return'<div class="recon-card" data-session-id="'+d(g.id)+'" data-session-name="'+B+'"><span class="bank-chip '+p(H)+'">'+d(H)+'</span><div class="recon-card-main"><div class="recon-card-title">'+B+D+'</div><div class="recon-card-sub">'+d(R)+'</div></div><div class="recon-card-right">'+U+'</div><button class="recon-card-trash" data-trash="'+d(g.id)+'" title="'+d(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),T.querySelectorAll(".recon-card").forEach(g=>{g.addEventListener("click",I=>{I.target.closest(".recon-card-trash")||(g.dataset.sessionId,c())})}),T.querySelectorAll(".recon-card-trash").forEach(g=>{g.addEventListener("click",I=>{I.stopPropagation();const H=g.dataset.trash,D=g.closest(".recon-card"),R=D&&D.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(H,R)})})}function c(L){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const A=document.querySelector('[data-recon-tab="bank"]');A&&A.click()},150)}function u(){o(!0),s(!1)}function f(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const L=document.querySelector('[data-recon-tab="bank"]');L&&L.click()},150)}async function w(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),o(!1),s(!1);const L=document.getElementById("reconcile-recent");L&&(L.style.display="none");const A={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[T,k]=await Promise.all([fetch("/api/bank-recon/stats",{headers:A}),fetch("/api/bank-recon/sessions?limit=20",{headers:A})]);if(!T.ok)throw new Error("http "+T.status);const g=await T.json(),I=k.ok?await k.json():[];r(g||{}),m(I||[])}catch(T){console.warn("[reconcile] load failed",T),u()}}function S(L){if(!L||!L.length)return;const A="Bearer "+(localStorage.getItem("mrpilot_token")||"");let T=0;const k=L.length;Array.from(L).forEach(function(g){const I=new FormData;I.append("file",g,g.name);const H=new XMLHttpRequest;H.open("POST","/api/bank-recon/upload"),H.setRequestHeader("Authorization",A),H.onload=function(){T++;try{const D=JSON.parse(H.responseText);H.status===200&&D.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",D.tx_count),"success"):showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error")}T===k&&setTimeout(w,600)},H.onerror=function(){T++,showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error"),T===k&&setTimeout(w,600)},H.send(I)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function E(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const L=document.getElementById("reconcile-bank-file-input");L&&L.addEventListener("change",function(){S(this.files),this.value=""}),document.addEventListener("click",A=>{if(A.target.closest("#btn-reconcile-upload-top")||A.target.closest("#btn-reconcile-upload-empty")){f();return}if(A.target.closest("#btn-reconcile-retry")){w();return}if(A.target.closest("#btn-reconcile-dev-seed")){C();return}})}const v=["468b50c1-5593-4fd6-990d-515ce8085563"];function h(){const L=document.getElementById("btn-reconcile-dev-seed");if(!L)return;const A=typeof _userInfo<"u"?_userInfo:null,T=A&&A.id&&v.indexOf(String(A.id))>=0;L.style.display=T?"":"none"}async function C(){try{const L=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!L.ok)throw new Error("seed:"+L.status);const A=await L.json(),T=(t("reconcile-dev-seed-ok")||"").replace("{n}",A.tx_count||0);showToast(T,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const k=document.querySelector('[data-auto-tab="bank"]');k&&k.click(),A.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(A.session_id)},300)}catch(L){console.warn("[reconcile] dev seed failed",L),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){E(),h(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await w()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&w().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const w=a();if(w){if(!e.clients.length){w.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}w.innerHTML=e.clients.map(S=>{const E=String(S.id),v=e.selected.has(E)?"checked":"",h=escapeHtml(S.name||S.label||"#"+E),C=S.code?'<span class="assign-row-code">'+escapeHtml(S.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(E)+'" '+v+'><span class="assign-row-name">'+h+"</span>"+C+"</label>"}).join(""),p()}}function p(){const w=s();if(w){const E=t("assign-selected-count")||"已选 {n} / {total}";w.textContent=E.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const S=o();S&&(S.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function l(){const w=i();w&&(w.textContent=e.employeeName?" · "+e.employeeName:"")}async function d(w,S){e.employeeId=w,e.employeeName=S||"",e.opened=!0,e.selected=new Set,e.clients=[],l();const E=a();E&&(E.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const v=n();v&&(v.style.display="flex");try{const[h,C]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(w)+"/assignments")]);e.clients=h&&h.clients||[];const L=C&&C.client_ids||[];e.selected=new Set(L.map(String)),r()}catch(h){console.error("[assign-clients] load failed",h);const C=a();C&&(C.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function m(){e.opened=!1;const w=n();w&&(w.style.display="none")}async function c(){if(!e.employeeId)return;const w=Array.from(e.selected).map(E=>parseInt(E,10)).filter(E=>!isNaN(E)),S=document.getElementById("assign-modal-save");S&&(S.disabled=!0);try{const E=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:w});E&&E.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",w.length),"success"),m(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(E){console.error("[assign-clients] save failed",E),showToast(t("assign-save-failed")||"保存失败","error")}finally{S&&(S.disabled=!1)}}function u(){const w=n();if(!w||w.dataset.bound==="1")return;w.dataset.bound="1";const S=document.getElementById("assign-modal-close");S&&S.addEventListener("click",m);const E=document.getElementById("assign-modal-cancel");E&&E.addEventListener("click",m);const v=document.getElementById("assign-modal-save");v&&v.addEventListener("click",c),w.addEventListener("click",function(L){L.target===w&&m()});const h=o();h&&h.addEventListener("change",function(){h.checked?e.selected=new Set(e.clients.map(L=>String(L.id))):e.selected=new Set,r()});const C=a();C&&C.addEventListener("change",function(L){const A=L.target.closest('input[type="checkbox"][data-cid]');if(!A)return;const T=A.dataset.cid;A.checked?e.selected.add(T):e.selected.delete(T),p()})}function f(){e.opened&&(l(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",f),window.openAssignClientsModal=function(w,S){u(),d(w,S)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(m){if(!m)return"";try{return new Date(m).toLocaleString()}catch{return m}}function a(m){const c=document.getElementById("access-log-table");c&&(c.innerHTML='<div class="access-log-empty">'+escapeHtml(m)+"</div>");const u=document.getElementById("access-log-pager");u&&(u.innerHTML="")}function o(){const m=document.getElementById("access-log-table");if(!m)return;const c=e.rows||[];if(!c.length){a(t("set-access-log-empty"));return}const u=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,f=c.map(function(w){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(w.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(w.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(w.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(w.target_name||w.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(w.ip||"-")}</div>
                </div>`}).join("");m.innerHTML=u+f}function s(){const m=document.getElementById("access-log-pager");if(!m)return;const c=e.total||0;if(!c){m.innerHTML="";return}const u=e.page||1,f=e.per_page,w=Math.max(1,Math.ceil(c/f)),S=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",c),E=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",u).replace("{t}",w);m.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(S)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u-1}" ${u<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(E)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u+1}" ${u>=w?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(m){const c=localStorage.getItem("mrpilot_token");if(c){e.page=m||1,a(t("set-access-log-loading"));try{const u="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),f=await fetch(u,{headers:{Authorization:"Bearer "+c}});if(f.status===403){a(t("set-access-log-empty"));return}if(!f.ok)throw new Error("http_"+f.status);const w=await f.json();e.rows=w.logs||[],e.total=w.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const m=localStorage.getItem("mrpilot_token");if(m)try{const c="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),u=await fetch(c,{headers:{Authorization:"Bearer "+m}});if(!u.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const f=await u.blob(),w=document.createElement("a"),S=URL.createObjectURL(f);w.href=S,w.download="pearnly_access_log.csv",document.body.appendChild(w),w.click(),setTimeout(function(){URL.revokeObjectURL(S),w.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function p(){const m=document.querySelectorAll(".set-tab-owner-only"),c=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));m.forEach(function(u){u.style.display=c?"":"none"})}document.addEventListener("click",function(m){if(m.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(m.target.closest("#access-log-csv-btn")){m.preventDefault(),r();return}const f=m.target.closest(".access-log-pager-btn[data-access-log-page]");if(f&&!f.disabled){const w=parseInt(f.dataset.accessLogPage,10);i(w)}}),document.addEventListener("input",function(m){m.target&&m.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(m.target.value||"").trim(),i(1)},350))});let l=0;const d=setInterval(function(){l++,_userInfo&&(p(),clearInterval(d)),l>60&&clearInterval(d)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){p(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=T=>document.getElementById(T);async function n(T,k){return await fetch(T,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(k||{})})}async function a(T){return await fetch(T,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function i(T,k){if(!T)return;T.style.display="",T.className="notif-line-check "+(k?"bound":"unbound");const g=k?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';T.innerHTML=g+"<span>"+escapeHtml(t(k?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(T){if(T==null)return"-";const k=Number(T);return isNaN(k)?String(T):"฿ "+k.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function p(T){if(!T)return"-";try{const k=new Date(T),g=(k.getMonth()+1).toString().padStart(2,"0"),I=k.getDate().toString().padStart(2,"0"),H=k.getHours().toString().padStart(2,"0"),D=k.getMinutes().toString().padStart(2,"0");return`${g}-${I} ${H}:${D}`}catch{return T}}function l(T){const k=e("notif-rules-list"),g=e("notif-rules-empty"),I=e("notif-rules-count");if(!(!k||!g)){if(I.textContent=String(T.length),I.className="auto-status-pill "+(T.length>0?"active":"none"),!T.length){g.style.display="",k.style.display="none",k.innerHTML="";return}g.style.display="none",k.style.display="",k.innerHTML=T.map(H=>{const D=H.template_code==="large_invoice",R=D?"notif-rule-large-tag":"notif-rule-exception-tag",B=D?"large":"";let P=[];if(D){const G=H.params&&H.params.threshold?r(H.params.threshold):"-";P.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+G)}H.enabled||P.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const U=P.length?P.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${H.enabled?"":" disabled"}" data-rule-id="${H.id}">
                    <span class="notif-rule-tmpl-badge ${B}">${escapeHtml(t(R))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(H.name)}</div>
                        <div class="notif-rule-meta">${U}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${H.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function d(T){const k=e("notif-logs-list");if(k){if(!T.length){k.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}k.innerHTML=T.map(g=>{const I=g.status==="sent",H=g.event_type==="exception_high"?"notif-event-exception-high":g.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",D=I?"":" · "+escapeHtml(g.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${I?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(H))}</div>
                        <div class="notif-log-meta">${escapeHtml(g.template_code||"-")}${D}</div>
                    </div>
                    <div class="notif-log-time">${p(g.sent_at)}</div>
                </div>`}).join("")}}async function m(){try{const T=await apiGet("/api/notifications/rules");c=T&&T.items||[],l(c)}catch(T){console.warn("load rules fail",T)}try{const T=await apiGet("/api/notifications/logs?limit=20");u=T&&T.items||[],d(u)}catch(T){console.warn("load logs fail",T)}}let c=null,u=null;function f(){c&&l(c),u&&d(u);const T=e("notif-new-modal");T&&T.style.display!=="none"&&o&&i(e("notif-line-check"),!!(o&&o.bound))}function w(){const T=e("notif-new-modal");T&&(T.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(k=>k.checked=!1),s().then(k=>i(e("notif-line-check"),!!(k&&k.bound))))}function S(){const T=e("notif-new-modal");T&&(T.style.display="none")}function E(){const T=document.querySelector('input[name="notif-template"]:checked'),k=e("notif-new-threshold-row");if(!T){k.style.display="none";return}k.style.display=T.value==="large_invoice"?"":"none";const g=e("notif-new-name");g&&!g.value.trim()&&(g.value=T.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function v(){const T=document.querySelector('input[name="notif-template"]:checked');if(!T){showToast(t("notif-new-template"),"error");return}const k=(e("notif-new-name").value||"").trim();if(!k){showToast(t("notif-name-required"),"error");return}const g={name:k,template_code:T.value,params:{},enabled:!0};if(T.value==="large_invoice"){const I=parseFloat(e("notif-new-threshold").value||"0");if(!I||I<=0){showToast(t("notif-threshold-required"),"error");return}g.params.threshold=I}try{const I=await apiPost("/api/notifications/rules",g);if(I&&I.ok)showToast(t("notif-toast-created"),"success"),S(),m();else{const H=await(I&&I.json&&I.json().catch(()=>({})))||{};showToast(H&&H.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function h(T,k,g){if(T==="toggle"){const I=g.classList.contains("on"),H=await n("/api/notifications/rules/"+k,{enabled:!I});H&&H.ok?(showToast(t(I?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),m()):showToast("toggle failed","error");return}if(T==="test"){const I=await s();if(!I||!I.bound){showToast(t("notif-line-error-bind-first"),"error");return}const H=await apiPost("/api/notifications/rules/"+k+"/test",{});if(H&&H.ok)showToast(t("notif-toast-test-sent"),"success"),m();else{const D=await(H&&H.json&&H.json().catch(()=>({})))||{},R=D&&D.detail||"";showToast(R||t("notif-toast-test-failed"),"error"),m()}return}if(T==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const H=await a("/api/notifications/rules/"+k);H&&H.ok?(showToast(t("notif-toast-deleted"),"success"),m()):showToast("delete failed","error");return}}let C=!1;function L(){if(C)return;C=!0;const T=e("notif-btn-new");T&&T.addEventListener("click",w);const k=e("notif-btn-refresh-logs");k&&k.addEventListener("click",m);const g=e("notif-new-close");g&&g.addEventListener("click",S);const I=e("notif-new-cancel");I&&I.addEventListener("click",S);const H=e("notif-new-save");H&&H.addEventListener("click",v),document.querySelectorAll('input[name="notif-template"]').forEach(B=>{B.addEventListener("change",E)});const D=e("notif-rules-list");D&&D.addEventListener("click",B=>{const P=B.target.closest("button[data-action]");if(!P)return;const U=P.closest("[data-rule-id]");U&&h(P.getAttribute("data-action"),U.getAttribute("data-rule-id"),P)});const R=e("notif-new-modal");R&&R.addEventListener("click",B=>{B.target===R&&S()})}async function A(){L(),await m()}window._loadNotificationsPanel=A,window._rerenderNotifications=f})();(function(){function n(v,h){try{return window.t&&window.t(v)||h}catch{return h}}function a(){var v="";try{v=localStorage.getItem("mrpilot_token")||""}catch{}return v?{Authorization:"Bearer "+v}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var v=document.createElement("style");v.id="recon-batch-style",v.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(v)}}function i(v){return v?v.dataset&&v.dataset.taskId?v.dataset.taskId:v.dataset&&v.dataset.taskid?v.dataset.taskid:"":""}function r(v){var h=document.getElementById(v.tbody);if(!h)return null;var C=h.closest("table");if(!C)return null;var L=C.querySelector("thead");if(!L)return null;if(L._reconReady)return L;var A=L.querySelector("tr");if(!A)return null;if(A.classList.add("recon-thead-default"),!A.querySelector(".recon-master-cb")){var T=document.createElement("th");T.className="recon-sel-cell";var k=document.createElement("input");k.type="checkbox",k.className="recon-master-cb",k.setAttribute("aria-label","select all"),k.addEventListener("change",function(){m(v,k.checked)}),T.appendChild(k),A.insertBefore(T,A.firstElementChild)}var g=A.children[1];g&&!g.classList.contains("recon-time-col")&&g.classList.add("recon-time-col");var I=A.children.length,H=document.createElement("tr");H.className="recon-thead-batch";var D=document.createElement("th");D.className="recon-sel-cell";var R=document.createElement("input");R.type="checkbox",R.className="recon-master-cb",R.checked=!0,R.setAttribute("aria-label","select all"),R.addEventListener("change",function(){m(v,R.checked)}),D.appendChild(R);var B=document.createElement("th");return B.setAttribute("colspan",String(I-1)),B.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',H.appendChild(D),H.appendChild(B),L.appendChild(H),B.querySelector("[data-recon-del]").addEventListener("click",function(){w(v)}),B.querySelector("[data-recon-clear]").addEventListener("click",function(){f(v)}),L._reconReady=!0,u(v),L}function p(v){var h=document.getElementById(v.tbody);if(h){var C=h.querySelectorAll("tr");C.forEach(function(L){var A=i(L);if(A&&!L.querySelector(".recon-sel-cb")){var T=L.querySelector("td");if(T){var k=document.createElement("td");k.className="recon-sel-cell";var g=document.createElement("input");g.type="checkbox",g.className="recon-sel-cb",g.dataset.taskId=A,g.dataset.kind=v.kind,g.addEventListener("click",function(H){H.stopPropagation()}),g.addEventListener("change",function(){c(v)}),k.appendChild(g),L.insertBefore(k,T);var I=L.children[1];I&&!I.classList.contains("recon-time-col")&&I.classList.add("recon-time-col")}}}),c(v)}}function l(v){var h=document.getElementById(v.tbody);return h?Array.prototype.slice.call(h.querySelectorAll(".recon-sel-cb")):[]}function d(v){return l(v).filter(function(h){return h.checked}).map(function(h){return h.dataset.taskId})}function m(v,h){l(v).forEach(function(C){C.checked=!!h}),c(v)}function c(v){var h=d(v),C=l(v),L=document.getElementById(v.tbody);if(L){var A=L.closest("table"),T=A&&A.querySelector("thead");if(T){h.length>0?T.classList.add("recon-batch-mode"):T.classList.remove("recon-batch-mode"),T.querySelectorAll(".recon-master-cb").forEach(function(g){if(C.length===0){g.checked=!1,g.indeterminate=!1;return}h.length===C.length?(g.checked=!0,g.indeterminate=!1):h.length===0?(g.checked=!1,g.indeterminate=!1):(g.checked=!1,g.indeterminate=!0)});var k=T.querySelector("[data-recon-count]");k&&(k.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",h.length))}}}function u(v){var h=document.getElementById(v.tbody);if(h){var C=h.closest("table"),L=C&&C.querySelector("thead");if(L){var A=L.querySelector("[data-recon-del-label]"),T=L.querySelector("[data-recon-clear]");A&&(A.textContent=n("recon-batch-delete","批量删除")),T&&(T.textContent=n("recon-batch-clear","取消")),c(v)}}}function f(v){l(v).forEach(function(h){h.checked=!1}),c(v)}async function w(v){var h=d(v);if(h.length){var C=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",h.length),L=!1;try{typeof window.pearnlyConfirm=="function"?L=await window.pearnlyConfirm(C,n("recon-batch-delete-title","批量删除")):L=window.confirm(C)}catch{L=!1}if(L)try{var A=Object.assign({"Content-Type":"application/json"},a()),T=v.kind==="glv"?h.map(function(H){return parseInt(H,10)}):h,k=await fetch(v.api,{method:"POST",headers:A,body:JSON.stringify({ids:T})});if(!k.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var g=await k.json(),I=g&&(g.deleted!=null?g.deleted:g.count)||h.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",I),"success"),v.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function S(v){r(v),p(v);var h=document.getElementById(v.tbody);if(!(!h||h._reconBatchWatched)){h._reconBatchWatched=!0;var C=new MutationObserver(function(){p(v)});C.observe(h,{childList:!0,subtree:!1})}}function E(){s(),o.forEach(S),document.querySelectorAll(".recon-batch-bar").forEach(function(v){try{v.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",E):E(),setTimeout(E,1500),setTimeout(E,4e3),document.addEventListener("keydown",function(v){v.key==="Escape"&&o.forEach(function(h){d(h).length>0&&f(h)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(u)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(d){};function i(d){n=d;for(let u=1;u<=a;u++){const f=document.getElementById("ob-step-"+u);f&&(f.style.display=u===d?"block":"none")}document.querySelectorAll(".ob-dot").forEach(u=>{const f=parseInt(u.dataset.step,10);u.classList.toggle("active",f===d),u.classList.toggle("done",f<d)});const m=document.getElementById("ob-step-label");m&&(m.textContent=d+" / "+a);const c=document.getElementById("ob-next");if(c&&(c.textContent=d===a?t("ob-finish"):t("ob-next")),d===4){const u=document.getElementById("ob-line-input");u&&(u.value=e.line_id||"")}}function r(d){const m=document.querySelector(".onboarding-modal");if(!m)return;let c=m.querySelector(".ob-feedback");c||(c=document.createElement("div"),c.className="ob-feedback",m.appendChild(c)),c.textContent=d,c.classList.add("show"),setTimeout(()=>c.classList.remove("show"),1800)}document.addEventListener("click",d=>{const m=d.target.closest(".ob-option");if(!m)return;const c=m.parentElement;if(!c||!c.classList.contains("ob-options"))return;c.querySelectorAll(".ob-option").forEach(f=>f.classList.remove("selected")),m.classList.add("selected");const u=m.dataset.value;c.id==="ob-role-options"?e.role=u:c.id==="ob-volume-options"?e.monthly_volume=u:c.id==="ob-country-options"&&(e.country=u)}),document.addEventListener("click",d=>{d.target.id==="ob-skip"&&p()}),document.addEventListener("click",d=>{if(d.target.id==="ob-next"){if(n===4){const m=document.getElementById("ob-line-input");e.line_id=(m&&m.value||"").trim().replace(/^@+/,"")}p()}}),document.addEventListener("click",d=>{if(d.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const m=document.getElementById("onboarding-modal");m&&(m.style.display="none")}});function p(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):l()}async function l(){const d=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const m={};if(e.role&&(m.role=e.role),e.monthly_volume&&(m.monthly_volume=e.monthly_volume),e.country&&(m.country=e.country),e.line_id&&(m.line_id=e.line_id),Object.keys(m).length===0){d&&(d.style.display="none");return}try{const c=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(m)});c.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,m),setTimeout(()=>{d&&(d.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(m)),console.warn("onboarding profile save failed",c.status),r(t("ob-fb-saved-local")),setTimeout(()=>{d&&(d.style.display="none")},1500))}catch(c){console.error("onboarding submit",c),localStorage.setItem("pilot_ob_pending",JSON.stringify(m)),d&&(d.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function p(){return"DHL Express (Thailand) Co., Ltd."}function l(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:p(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>d(),window.loadPrefsSettings=()=>m(),window.loadArchiveSettings=()=>u();function d(){const k=document.getElementById("settings-contact-grid");if(!k)return;const g=_contact?.phone||"086-889-2228",I=_contact?.line_id||"@Pearnly",H=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",D=_contact?.email||"hello@pearnly.com",R=_contact?.address||"Bangkok, Thailand";k.innerHTML=`
            <a class="contact-item" href="${escapeHtml(H)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(I)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(D)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(D)}</div>
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
                    <div class="contact-value">${escapeHtml(R)}</div>
                </div>
            </div>
        `}async function m(){try{const k=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!k.ok)return;const g=await k.json(),I=document.getElementById("pref-dup-check");I&&(I.checked=!!g.enabled)}catch(k){console.warn("load prefs failed",k)}}const c=document.getElementById("pref-dup-check");c&&!c.dataset.bound&&(c.dataset.bound="1",c.addEventListener("change",async k=>{const g=k.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:g})})).ok?showToast(g?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(k.target.checked=!g,showToast(t("pref-save-failed"),"error"))}catch{k.target.checked=!g,showToast(t("pref-save-failed"),"error")}}));async function u(){const k=!!(_userInfo&&_userInfo.can_customize_archive);o=!k;const g=document.getElementById("archive-upgrade-banner");g&&(g.style.display=k?"none":"");const I=document.getElementById("archive-plus-badge");I&&(I.style.display=k?"none":"");try{const H=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!H.ok)throw new Error("load failed");const D=await H.json();e=Array.isArray(D.name_template)?D.name_template:[],n=D.folder_strategy||"by_month_seller"}catch(H){console.error("load archive settings failed",H),showToast(t("archive-load-failed"),"error");return}f(),w(),S(),E()}function f(){const k=document.getElementById("archive-rule-canvas");if(k){if(e.length===0){k.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}k.innerHTML=e.map((g,I)=>{const H=i[g.type]||{label:g.type},D=s[g.type]||"",R=g.type==="sep"?`"${escapeHtml(g.val||"_")}"`:escapeHtml(t(H.label));return`
                <span class="archive-token ${g.type}"
                      data-token-idx="${I}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${D}</span>
                    <span class="token-label">${R}</span>
                </span>
            `}).join("")}}function w(){const k=document.getElementById("archive-field-palette");if(!k)return;const g=["date","seller","category","amount","invoice","buyer","sep"];k.innerHTML=g.map(I=>{const H=i[I],D=s[I]||"";return`
                <button class="archive-palette-btn ${I}" data-add-field="${I}" ${o?"disabled":""}>
                    <span class="token-icon">${D}</span>
                    <span>${escapeHtml(t(H.label))}</span>
                </button>
            `}).join("")}function S(){document.querySelectorAll('input[name="folder-strategy"]').forEach(k=>{k.checked=k.value===n,k.disabled=o})}async function E(){const k=document.getElementById("archive-preview-name"),g=document.getElementById("archive-preview-hint");if(g&&(g.textContent=t("archive-preview-hint",{category:r()})),!!k){if(e.length===0){k.textContent="-";return}try{const H=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:l().merged_fields,name_template:e})})).json();k.textContent=(H.name||"-")+".pdf"}catch{k.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const k=document.getElementById("archive-rule-modal");!k||k.style.display==="none"||(f(),w(),E())};let v=-1;document.addEventListener("dragstart",k=>{const g=k.target.closest(".archive-token");!g||o||(v=parseInt(g.dataset.tokenIdx,10),g.classList.add("dragging"),k.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",k=>{document.querySelectorAll(".archive-token").forEach(g=>g.classList.remove("dragging","drop-target")),v=-1}),document.addEventListener("dragover",k=>{const g=k.target.closest(".archive-token");g&&(k.preventDefault(),k.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(I=>I.classList.remove("drop-target")),g.classList.add("drop-target"))}),document.addEventListener("drop",k=>{const g=k.target.closest(".archive-token");if(!g||v<0||o)return;k.preventDefault();const I=parseInt(g.dataset.tokenIdx,10);if(I===v)return;const H=e.splice(v,1)[0];e.splice(I,0,H),v=-1,f(),E()}),document.addEventListener("click",k=>{if(k.target.closest("#btn-open-archive-rule")||k.target.closest("#btn-open-archive-rule-from-settings")){const D=document.getElementById("archive-rule-modal");D&&(D.style.display="",u());return}if(k.target.closest("#archive-rule-modal-close")||k.target.id==="archive-rule-modal"){const D=document.getElementById("archive-rule-modal");D&&(D.style.display="none");return}const g=k.target.closest(".settings-nav-item");if(g){switchSettingsTab(g.dataset.settingsTab);return}if(o&&k.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const I=k.target.closest("[data-add-field]");if(I){const D=I.dataset.addField,R=i[D],B={type:D,...R.defaultCfg};e.push(B),f(),E();return}const H=k.target.closest(".archive-token");if(H&&!o){h(parseInt(H.dataset.tokenIdx,10));return}if(k.target.closest("#btn-archive-save"))return A();if(k.target.closest("#btn-archive-reset"))return T();(k.target.closest("#archive-token-close")||k.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),k.target.closest("#btn-archive-token-ok")&&C(),k.target.closest("#btn-archive-token-delete")&&L()}),document.addEventListener("change",k=>{k.target.name==="folder-strategy"&&(n=k.target.value)});function h(k){a=k;const g=e[k];if(!g)return;const I=document.getElementById("archive-token-body");let H="";g.type==="date"?H=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${g.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${g.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${g.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${g.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:g.type==="seller"?H=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${g.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:g.type==="amount"?H=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${g.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:g.type==="sep"?H=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${g.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${g.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${g.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(g.val)?"":escapeHtml(g.val||"")}">
                    </div>
                </div>`:H=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,I.innerHTML=H,document.getElementById("archive-token-modal").style.display="",I.querySelectorAll(".sep-chip").forEach(D=>{D.addEventListener("click",()=>{I.querySelectorAll(".sep-chip").forEach(B=>B.classList.remove("active")),D.classList.add("active");const R=document.getElementById("token-sep-custom");R&&(R.value="")})})}function C(){const k=e[a];if(k){if(k.type==="date")k.format=document.getElementById("token-date-format").value;else if(k.type==="seller")k.short=document.getElementById("token-seller-short").checked;else if(k.type==="amount")k.with_currency=document.getElementById("token-amount-currency").checked;else if(k.type==="sep"){const g=document.querySelector("#archive-token-body .sep-chip.active"),I=document.getElementById("token-sep-custom").value;k.val=I||(g?g.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",f(),E()}}function L(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",f(),E())}async function A(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const g=document.getElementById("archive-rule-modal");g&&(g.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function T(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",f(),S(),E())}})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,i=null,r=0,p=0,l=!1;function d(h){const C=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return h.preventDefault(),h.returnValue=C,C}function m(){l||(l=!0,window.addEventListener("beforeunload",d))}function c(){l&&(l=!1,window.removeEventListener("beforeunload",d))}function u(){if(document.getElementById("big-batch-progress"))return;const h=document.getElementById("file-list");if(!h||!h.parentNode)return;const C=document.createElement("div");C.id="big-batch-progress",C.className="big-batch-progress",C.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',h.parentNode.insertBefore(C,h);const L=document.getElementById("bbp-text");L&&(L.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function f(){const h=document.getElementById("big-batch-progress");h&&h.remove()}function w(){if(!i)return;let h=0;for(let H=0;H<i.length;H++){const D=i[H].status;(D==="success"||D==="error"||D==="cancelled")&&h++}const C=r,L=C>0?Math.min(100,Math.floor(100*h/C)):0,A=(Date.now()-p)/1e3;let T;if(h>=3&&A>1){const H=A/h;T=(C-h)*H}else T=(C-h)*6/6;const k=Math.max(1,Math.ceil(T/60)),g=document.getElementById("bbp-fill"),I=document.getElementById("bbp-text");g&&(g.style.width=L+"%"),I&&(h>=C?I.textContent=t("big-batch-progress-done").replace("{total}",C):I.textContent=t("big-batch-progress-running").replace("{done}",h).replace("{total}",C).replace("{min}",k))}function S(h){try{if(localStorage.getItem(o)==="1")return}catch{}const C=Math.max(1,Math.ceil(h*6/6/60)),L=t("big-batch-first-tip").replace("{n}",h).replace("{min}",C);typeof showToast=="function"&&showToast(L,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function E(h){!h||h.length<100||(i=h,r=h.length,p=Date.now(),u(),m(),S(r),s&&clearInterval(s),s=setInterval(w,250),w())}function v(){s&&(clearInterval(s),s=null),c(),i&&r>=100?(w(),setTimeout(f,1200)):f(),i=null,r=0}window._bigBatchStart=E,window._bigBatchStop=v,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&w()})})();(function(){let e=null,n=!1,a=!1;function o(g){return typeof escapeHtml=="function"?escapeHtml(g==null?"":String(g)):String(g??"")}function s(g,I){try{typeof showToast=="function"&&showToast(g,I||"info")}catch{}}function i(){const g=typeof _userInfo<"u"?_userInfo:null;return!!(g&&(g.role==="owner"||g.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function p(g){if(!g)return!1;const I=String(g.status||"").toLowerCase();return I==="exception"||I==="exception_pending"||I==="rejected"}async function l(g){if(n&&!g)return e;const I=localStorage.getItem("mrpilot_token");if(!I)return null;try{const H=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+I}});if(!H.ok)throw new Error("http_"+H.status);e=await H.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function d(){const g=document.getElementById("erp-connect-cards");if(!g)return;const I=e;let H,D=!1;I?I.configured?I.connected?(D=!0,H='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):H='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":H='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":H='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let R="";if(!I||!I.configured)R='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!I.connected)i()&&(R='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const x=!!I.auto_push,y=x?t("card-btn-disable"):t("card-btn-enable");R='<button type="button" class="'+(x?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(x?"1":"0")+'" title="'+o(x?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(y)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const B=I&&I.connected?"xero-card-desc-connected":"xero-card-desc-default",P=I&&I.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",U=(function(){const x=t(B);return x===B?P:x})();let G='<div class="integration-row erp-connect-xero'+(D?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+H+'</div><div class="int-desc">'+o(U)+'</div></div><div class="int-actions">'+R+"</div></div>";if(I&&I.configured&&I.connected&&i()){const x=I.organisations||[];let y="";if(x.length>0){y+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(x.length)))+"</div>",y+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",y+='<div class="erp-cc-orgs">',x.forEach(function(Y){y+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(Y.id)+'"'+(Y.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(Y.organisation_name||Y.organisation_id)+"</span></label>"}),y+="</div>";const q=!!I.auto_push,z=q?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");y+='<div class="erp-cc-auto-push" title="'+o(z)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(q?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",y+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}G+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+y+"</div>"}const F=g.querySelector(".erp-connect-xero"),Q=g.querySelector("#erp-xero-details");Q&&Q.remove(),F?F.outerHTML=G:g.insertAdjacentHTML("afterbegin",G);const oe=document.getElementById("btn-xero-edit-toggle");oe&&oe.addEventListener("click",function(x){x.preventDefault();const y=document.getElementById("erp-xero-details");y&&(y.style.display=y.style.display==="none"?"":"none")});const $=document.getElementById("btn-xero-toggle-enabled");$&&$.addEventListener("click",async function(x){if(x.preventDefault(),$.disabled)return;const q=!($.getAttribute("data-xero-enabled")==="1");if(!q)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}$.disabled=!0,await f(q,null)})}async function m(){const g=localStorage.getItem("mrpilot_token");if(g)try{const I=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+g}});if(!I.ok){let D="unknown";try{D=(await I.json()).detail||"unknown"}catch{}const R=String(D).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+R)||D),"error");return}const H=await I.json();H.redirect_url&&(window.location.href=H.redirect_url)}catch(I){s(t("xero-push-fail").replace("{err}",I.message||"network"),"error")}}async function c(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const I=localStorage.getItem("mrpilot_token");try{const H=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+I}});if(!H.ok)throw new Error("http_"+H.status);await l(!0),d()}catch(H){s(t("xero-push-fail").replace("{err}",H.message),"error")}}async function u(g){const I=localStorage.getItem("mrpilot_token");try{const H=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({token_id:g})});if(!H.ok)throw new Error("http_"+H.status);await l(!0),d()}catch(H){s(t("xero-push-fail").replace("{err}",H.message),"error")}}async function f(g,I){const H=localStorage.getItem("mrpilot_token");I&&(I.disabled=!0);try{const D=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+H,"Content-Type":"application/json"},body:JSON.stringify({on:!!g})});if(!D.ok){let R="unknown";try{R=(await D.json()).detail||"unknown"}catch{}throw new Error(R)}s(g?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await l(!0),d()}catch(D){I&&(I.checked=!g),s(t("erp-auto-push-toggle-fail").replace("{err}",D.message||"network"),"error")}finally{I&&(I.disabled=!1)}}async function w(){const g=document.getElementById("drawer-history-save");if(!g||g.querySelector("#btn-xero-push")||g.querySelector("#pn-push-wrap")||(await l(!1),g.querySelector("#pn-push-wrap"))||g.querySelector("#btn-xero-push"))return;const I=r();if(!(I&&(I._historyId||I.history_id)))return;let D=!1,R="xero-push-tip";!e||!e.configured?(D=!0,R="xero-err-not_configured"):e.connected?p(I)&&(D=!0,R="xero-push-disabled-exc"):(D=!0,R="xero-push-disabled-no-conn");const B=document.createElement("button");B.type="button",B.id="btn-xero-push",B.className="btn btn-ghost"+(D?" disabled":""),B.disabled=D,B.title=t(R)||"",B.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",B.addEventListener("click",S);const P=document.getElementById("btn-push-erp");P&&P.parentNode?P.parentNode.insertBefore(B,P.nextSibling):g.insertBefore(B,g.firstChild)}async function S(){const g=r(),I=g&&(g._historyId||g.history_id);if(!I)return;const H=document.getElementById("btn-xero-push");H&&(H.disabled=!0,H.classList.add("loading"));const D=localStorage.getItem("mrpilot_token");try{const R=await fetch("/api/erp/xero/push/"+encodeURIComponent(I),{method:"POST",headers:{Authorization:"Bearer "+D}});if(!R.ok){let B="unknown";try{B=(await R.json()).detail||"unknown"}catch{}const P=String(B).replace(/^xero\./,"").toLowerCase(),U=t("xero-"+P),G=U&&U!=="xero-"+P?U:B;s(t("xero-push-fail").replace("{err}",G),"error");return}s(t("xero-push-ok"),"success")}catch(R){s(t("xero-push-fail").replace("{err}",R.message||"network"),"error")}finally{H&&(H.disabled=!1,H.classList.remove("loading"))}}async function E(){await l(!0),d(),v()}async function v(){const g=document.getElementById("erp-global-push-mode");if(!g)return;const I=localStorage.getItem("mrpilot_token");if(I)try{const H=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+I}});if(H.ok){const D=await H.json();D.mode&&(g.value=D.mode,g.dataset.prev=D.mode)}}catch{}}async function h(g){const I=g.value,H=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+H,"Content-Type":"application/json"},body:JSON.stringify({mode:I})})).ok?(g.dataset.prev=I,s(t("pref-erp-mode-saved"),"success")):(g.value=g.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{g.value=g.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function C(){try{const g=String(window.location.hash||"");if(g.indexOf("xero=ok")>=0){const I=g.match(/n=(\d+)/),H=I?I[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",H),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),l(!0).then(d)}else g.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function L(){if(a)return;a=!0,document.addEventListener("click",function(I){if(I.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(E,50);return}if(I.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(E,80);return}if(I.target.closest("#btn-xero-connect")){I.preventDefault(),m();return}if(I.target.closest("#btn-xero-disconnect")){I.preventDefault(),c();return}}),document.addEventListener("change",function(I){I.target&&I.target.matches('input[name="xero-default-org"]')&&u(I.target.value),I.target&&I.target.id==="xero-auto-push-toggle"&&f(I.target.checked,I.target),I.target&&I.target.id==="erp-global-push-mode"&&h(I.target)});const g=function(){return document.getElementById("drawer-body")};try{const I=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&w()}),H=g();if(H)I.observe(H,{childList:!0,subtree:!0});else{const D=new MutationObserver(function(){const R=g();R&&(I.observe(R,{childList:!0,subtree:!0}),D.disconnect())});D.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(C,500)}function A(){e&&d();const g=document.getElementById("btn-xero-push");if(g){const I=g.querySelector("span");I&&(I.textContent=t("xero-push-btn"))}}L(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",A);async function T(g){const I=Date.now();for(;Date.now()-I<g;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(H=>setTimeout(H,80))}return null}async function k(){await T(5e3);const g=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),I=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');g&&I&&await E()}setTimeout(k,200)})();(function(){var e="https://www.mrerp4sme.com/dms/index.php",n=null,a=!1;function o(E){return typeof escapeHtml=="function"?escapeHtml(E==null?"":String(E)):String(E??"")}function s(E,v){try{typeof showToast=="function"&&showToast(E,v||"info")}catch{}}function i(){return localStorage.getItem("mrpilot_token")}async function r(E){var v=i();if(!v)return null;try{var h=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+v}});if(!h.ok)throw new Error("http_"+h.status);var C=await h.json(),L=C&&C.items||[];n=L.find(function(A){return A&&(A.adapter||"").toLowerCase()==="mrerp_dms"})||null,a=!0}catch{n=null,a=!1}return n}function p(){var E=document.getElementById("erp-connect-cards");if(E){var v=E.querySelector("[data-mrerp-dms-zone]");v||(v=document.createElement("div"),v.setAttribute("data-mrerp-dms-zone","1"),E.appendChild(v));var h=n,C=!!(h&&h.enabled!==!1),L;h?C?L='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("dms-card-connected"))+"</span>":L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-disabled-pill"))+"</span>":L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-not-connected"))+"</span>";var A;if(!h)A='<button type="button" class="int-btn-configure" id="btn-dms-connect">'+o(t("dms-card-connect"))+"</button>";else{var T=C?t("dms-card-disable"):t("dms-card-enable");A='<button type="button" class="int-btn-configure" id="btn-dms-edit">'+o(t("dms-card-edit"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-test">'+o(t("dms-card-test"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-toggle">'+o(T)+"</button>"}v.innerHTML='<div class="integration-row erp-connect-mrerp-dms'+(C?" connected":"")+'"><div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/><path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("dms-card-title"))+"</span>"+L+'</div><div class="int-desc">'+o(t("dms-card-desc"))+'</div></div><div class="int-actions">'+A+"</div></div>"}}function l(){var E=document.getElementById("dms-wizard-overlay");E&&E.remove(),document.removeEventListener("keydown",d)}function d(E){E.key==="Escape"&&l()}function m(){l();var E=n,v=E&&E.config&&E.config.booking_defaults&&E.config.booking_defaults.booking_prefix||"PN",h=function(A,T,k,g,I){return'<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">'+o(t(A))+'</span><input id="'+T+'" type="'+k+'" value="'+o(g||"")+'" placeholder="'+o(I||"")+'" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;"></label>'},C=document.createElement("div");C.id="dms-wizard-overlay",C.style.cssText="position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;",C.innerHTML='<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">'+o(t("dms-wizard-title"))+'</div><div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">'+o(t("dms-card-desc"))+"</div>"+h("dms-wizard-username","dms-w-user","text","","")+h("dms-wizard-password","dms-w-pass","password","","")+h("dms-wizard-prefix","dms-w-prefix","text",v,"PN")+'<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div><div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn btn-ghost" id="dms-w-cancel">'+o(t("dms-wizard-cancel"))+'</button><button type="button" class="btn btn-primary" id="dms-w-save">'+o(t("dms-wizard-save"))+"</button></div></div>",document.body.appendChild(C),document.addEventListener("keydown",d),C.addEventListener("click",function(A){A.target===C&&l()});var L=document.getElementById("dms-w-user");L&&L.focus()}function c(E){var v=document.getElementById("dms-w-err");v&&(v.textContent=E,v.style.display=E?"":"none")}async function u(){var E=n&&n.config&&n.config.system_url||e,v=(document.getElementById("dms-w-user")||{}).value||"",h=(document.getElementById("dms-w-pass")||{}).value||"",C=(document.getElementById("dms-w-prefix")||{}).value||"PN";if(E=E.trim(),v=v.trim(),!E||!v||!h){c(t("dms-wizard-required"));return}var L=document.getElementById("dms-w-save");L&&(L.disabled=!0,L.textContent=t("dms-wizard-saving")),c("");var A=i();try{var T=await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+A,"Content-Type":"application/json"},body:JSON.stringify({adapter:"mrerp_dms",config:{system_url:E,username:v,password:h}})}),k=await T.json().catch(function(){return{}});if(!T.ok||!k.ok){var g=k.error_friendly&&(k.error_friendly[window.currentLang]||k.error_friendly.en)||t("dms-connect-fail-generic");c(g),L&&(L.disabled=!1,L.textContent=t("dms-wizard-save"));return}var I={system_url:E,username_enc:v,password_enc:h,id_card_auto_push:!0,booking_defaults:{booking_prefix:C.trim()||"PN"}},H,D;n&&n.id?(H="PATCH",D="/api/erp/endpoints/"+encodeURIComponent(n.id)):(H="POST",D="/api/erp/endpoints");var R=H==="POST"?{name:"MR.ERP DMS",adapter:"mrerp_dms",config:I,is_default:!1,auto_push:!1}:{config:I,auto_push:!1},B=await fetch(D,{method:H,headers:{Authorization:"Bearer "+A,"Content-Type":"application/json"},body:JSON.stringify(R)});if(!B.ok){var P=await B.json().catch(function(){return{}}),U=P&&P.detail&&(P.detail.code||P.detail)||"save_failed";c(t("dms-save-fail")+" ("+o(String(U))+")"),L&&(L.disabled=!1,L.textContent=t("dms-wizard-save"));return}l(),s(t("dms-connect-ok"),"success"),await r(!0),p(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{c(t("dms-connect-fail-generic")),L&&(L.disabled=!1,L.textContent=t("dms-wizard-save"))}}async function f(){if(!(!n||!n.id)){s(t("dms-test-running"),"info");var E=i();try{var v=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id)+"/test-connection?refresh=1",{method:"POST",headers:{Authorization:"Bearer "+E}}),h=await v.json().catch(function(){return{}});s(h&&h.ok?t("dms-test-ok"):t("dms-test-fail"),h&&h.ok?"success":"error")}catch{s(t("dms-test-fail"),"error")}}}async function w(){if(!(!n||!n.id)){var E=n.enabled===!1;if(!E)try{var v=await window.pearnlyConfirm(t("dms-confirm-disable"));if(!v)return}catch{}var h=i();try{var C=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id),{method:"PATCH",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({enabled:E})});if(!C.ok)throw new Error("http_"+C.status);s(E?t("dms-enabled-toast"):t("dms-disabled-toast"),"success"),await r(!0),p(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{s(t("dms-save-fail"),"error")}}}function S(){r().then(p)}document.addEventListener("click",function(E){if(E.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(S,60);return}if(E.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(S,90);return}if(E.target.closest("#btn-dms-connect")||E.target.closest("#btn-dms-edit")){E.preventDefault(),m();return}if(E.target.closest("#dms-w-cancel")){E.preventDefault(),l();return}if(E.target.closest("#dms-w-save")){E.preventDefault(),u();return}if(E.target.closest("#btn-dms-test")){E.preventDefault(),f();return}if(E.target.closest("#btn-dms-toggle")){E.preventDefault(),w();return}}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("mrerp-dms-adapter",p),setTimeout(function(){var E=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),v=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');E&&v&&S()},250)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const d=`
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
        </div>`,m=document.createElement("div");m.innerHTML=d,document.body.appendChild(m.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",c=>{c.target.id==="report-modal"&&a()})}function a(){const d=document.getElementById("report-modal");d&&(d.style.display="none"),o=null}let o=null;async function s(d,m){const c=d+":"+(m||"");if(e[c])return e[c];let u;try{const f=localStorage.getItem("mrpilot_token"),w=await fetch(`/api/reports/templates?lang=${encodeURIComponent(d)}`,{headers:{Authorization:"Bearer "+f}});if(!w.ok)throw new Error("templates fetch failed");u=(await w.json()).templates||[]}catch(f){console.error("fetchTemplates fail",f),u=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(u=u.filter(f=>f.code!=="erp"),m==="history-batch"){const f=u.findIndex(S=>S.code==="standard"),w=f>=0?f+1:u.length;u.splice(w,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[c]=u,u}function i(d){const m=document.getElementById("report-tpl-list"),c=d.map((f,w)=>`
            <label class="report-tpl-item${f.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${f.code}" ${f.recommended||w===0?"checked":""}>
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
        `;m.innerHTML=c+u}function r(d){return d==null?"":String(d).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[m])}function p(d){const m=new Date,c=m.getFullYear(),u=m.getMonth()+1;if(d==="all")return"all";if(d==="this-month")return`${c}-${String(u).padStart(2,"0")}`;if(d==="last-month"){const f=new Date(c,u-2,1);return`${f.getFullYear()}-${String(f.getMonth()+1).padStart(2,"0")}`}return d==="this-year"?`${c}`:d==="this-quarter"?`${c}-Q${Math.floor((u-1)/3)+1}`:"all"}window.openReportModal=async function(d){d=d||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(S=>{const E=S.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][E]&&(S.textContent=I18N[currentLang][E])});const m=document.getElementById("report-period-section");m&&(m.style.display=d.mode==="client"?"":"none");const c=document.getElementById("report-tpl-list");c.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const u=await s(currentLang,d&&d.mode);i(u),o=d;const f=document.getElementById("report-modal-download"),w=f.cloneNode(!0);f.parentNode.replaceChild(w,f),w.addEventListener("click",()=>l(o))};async function l(d){if(!d)return;const m=document.querySelector('input[name="report-tpl"]:checked');if(!m){showToast(t("report-toast-no-selection"),"info");return}const c=m.value,u=document.querySelector('input[name="report-period"]:checked'),f=u?u.value:"all",w=p(f),S=document.getElementById("report-modal-download"),E=S.innerHTML;S.disabled=!0,S.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const v=localStorage.getItem("mrpilot_token");let h,C;if(d.mode==="records")h=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,records:d.records||[],meta:d.meta||{}})}),C=`mrpilot-${c}-${Date.now()}.xlsx`;else if(d.mode==="client"){const H=`/api/reports/clients/${d.clientId}/export?template=${encodeURIComponent(c)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(w)}`;h=await fetch(H,{headers:{Authorization:"Bearer "+v}}),C=`${(d.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${c}.xlsx`}else if(d.mode==="history-batch")c==="sales_detail_th"?(h=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:d.historyIds||[],client_id:d.clientId||null})}),C=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(h=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,history_ids:d.historyIds||[],client_id:d.clientId||null})}),C=`mrpilot-batch-${c}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+d.mode);if(!h.ok){let H="HTTP "+h.status;try{const D=await h.json();D&&D.detail&&(H=D.detail)}catch(D){console.warn("[batch-export] resp.json err.detail parse failed:",D)}h.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+H,"error");return}const L=await h.blob();let A=C;const k=(h.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(k)try{A=decodeURIComponent(k[1])}catch{}const g=URL.createObjectURL(L),I=document.createElement("a");I.href=g,I.download=A,document.body.appendChild(I),I.click(),document.body.removeChild(I),URL.revokeObjectURL(g),showToast(t("report-toast-success"),"success"),a()}catch(v){console.error("doDownload fail",v),showToast(t("report-toast-fail")+" · "+(v.message||""),"error")}finally{S.disabled=!1,S.innerHTML=E}}document.addEventListener("DOMContentLoaded",()=>{const d=document.getElementById("btn-export");if(d){const c=d.cloneNode(!0);d.parentNode.replaceChild(c,d),c.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(u=>({filename:u.filename,merged_fields:u.merged_fields||{}}))})})}const m=document.getElementById("history-batch-export");m&&m.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(d,m){openReportModal({mode:"client",clientId:d,clientName:m||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,o="mrpilot_folder_watcher",s=1;let i=null,r=null,p=null,l=60,d=!1,m=!1,c=0,u=0,f=0,w=[],S=null,E=!1;function v(){return i||(i=new Promise((_,M)=>{const j=indexedDB.open(o,s);j.onupgradeneeded=J=>{const O=J.target.result;O.objectStoreNames.contains("handles")||O.createObjectStore("handles"),O.objectStoreNames.contains("seen")||O.createObjectStore("seen"),O.objectStoreNames.contains("config")||O.createObjectStore("config")},j.onsuccess=J=>_(J.target.result),j.onerror=J=>M(J.target.error)}),i)}function h(_,M){return v().then(j=>new Promise((J,O)=>{const N=j.transaction(_,"readonly").objectStore(_).get(M);N.onsuccess=()=>J(N.result),N.onerror=()=>O(N.error)}))}function C(_,M,j){return v().then(J=>new Promise((O,b)=>{const N=J.transaction(_,"readwrite");N.objectStore(_).put(j,M),N.oncomplete=()=>O(),N.onerror=()=>b(N.error)}))}function L(_,M){return v().then(j=>new Promise((J,O)=>{const b=j.transaction(_,"readwrite");b.objectStore(_).delete(M),b.oncomplete=()=>J(),b.onerror=()=>O(b.error)}))}function A(_){return v().then(M=>new Promise((j,J)=>{const O=M.transaction(_,"readwrite");O.objectStore(_).clear(),O.oncomplete=()=>j(),O.onerror=()=>J(O.error)}))}async function T(_){if(!_)return!1;try{const M={mode:"read"};let j=await _.queryPermission(M);return j==="granted"?!0:(j=await _.requestPermission(M),j==="granted")}catch(M){return console.warn("[folder] permission check failed:",M),!1}}function k(_,M){const j=document.getElementById("folder-status-summary");j&&(j.setAttribute("data-i18n",_),j.textContent=t(_),j.className="auto-status-pill"+(M?" "+M:""))}function g(_){["folder-unsupported","folder-empty","folder-active"].forEach(M=>{const j=document.getElementById(M);j&&(j.style.display=M===_?"":"none")})}function I(_){if(!_)return"-";const M=_ instanceof Date?_:new Date(_),j=String(M.getHours()).padStart(2,"0"),J=String(M.getMinutes()).padStart(2,"0"),O=String(M.getSeconds()).padStart(2,"0");return`${j}:${J}:${O}`}function H(){g("folder-active");const _=document.getElementById("folder-config-path");_&&r&&(_.textContent=r.name||"-");const M=document.getElementById("folder-interval-select");M&&(M.value=String(l)),document.getElementById("folder-stat-last").textContent=S?I(S):"-",document.getElementById("folder-stat-processed").textContent=String(c),document.getElementById("folder-stat-failed").textContent=String(u),document.getElementById("folder-stat-queue").textContent=String(f);const j=document.getElementById("btn-folder-pause"),J=document.getElementById("btn-folder-resume");j&&(j.style.display=d?"none":""),J&&(J.style.display=d?"":"none"),d?k("folder-status-paused","paused"):k("folder-status-running","running");const O=document.getElementById("folder-status-text");O&&(O.setAttribute("data-i18n",d?"folder-status-paused":"folder-status-running"),O.textContent=t(d?"folder-status-paused":"folder-status-running"));const b=document.getElementById("folder-status-pulse");b&&(b.className="folder-status-pulse"+(d?" paused":"")),D()}function D(){const _=document.getElementById("folder-recent-list");if(_){if(w.length===0){_.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}_.innerHTML=w.slice(0,20).map(M=>{let j;M.status==="ok"?j=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:M.status==="dup"?j=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:M.status==="skip"?j=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:j=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const J=M.status==="fail"&&M.error?M.error:M.status==="dup"&&M.reason||M.status==="skip"&&M.reason?M.reason:"",O=J?`<div class="folder-recent-err">${escapeHtml(J)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${j}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(M.name)}</div>
                        ${O}
                    </div>
                    <div class="folder-recent-time">${I(M.time)}</div>
                </div>
            `}).join("")}}function R(_){w.unshift(_),w.length>50&&(w.length=50),C("config","recent_list",w).catch(()=>{})}async function B(_){const M=new FormData;M.append("file",_,_.name),M.append("source","folder");const j=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:M});if(!j.ok){let J="http_"+j.status;try{const O=await j.json();J=O&&O.detail?typeof O.detail=="string"?O.detail:O.detail.code||JSON.stringify(O.detail):J}catch{}throw new Error(J)}return await j.json()}async function P(_){try{const j=(await _.getFile()).size;return await new Promise(O=>setTimeout(O,3e3)),(await _.getFile()).size===j&&j>0}catch{return!1}}async function U(_,M,j,J){if(J>10)return;let O;try{O=await _.queryPermission({mode:"read"})}catch{O="denied"}if(O==="granted")for await(const b of _.values()){const N=M?`${M}/${b.name}`:b.name;if(b.kind==="file"){if(!a.test(b.name))continue;let V;try{V=await b.getFile()}catch{continue}const W=`${N}::${V.size}::${V.lastModified}`;if(await h("seen",W))continue;j.push({entry:b,file:V,seenKey:W,relPath:N})}else if(b.kind==="directory")try{await U(b,N,j,J+1)}catch{}}}async function G(){if(!(m||d||!r)){m=!0;try{if(await r.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),Y(),showToast("warn",t("folder-permission-lost"));return}S=new Date;const M=[];await U(r,"",M,0),f=M.length,H();for(const j of M){if(d)break;if(!await P(j.entry)){f=Math.max(0,f-1),H();continue}try{let O;try{O=await j.entry.getFile()}catch{O=j.file}const b=await B(O);await C("seen",j.seenKey,{name:O.name,relPath:j.relPath,size:O.size,lastModified:O.lastModified,processed_at:Date.now()});const N=b.history_ids||(b.history_id?[b.history_id]:[]),V=b.duplicate_warnings||[],W=j.relPath||O.name;N.length>0?(c+=N.length,R({name:W,status:"ok",time:new Date,history_id:N[0],count:N.length}),await C("config","processed_count",c)):V.length>0?R({name:W,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):R({name:W,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(O){u++,R({name:j.relPath||j.file.name,status:"fail",time:new Date,error:String(O.message||O)}),await C("config","failed_count",u)}f=Math.max(0,f-1),H()}}catch(_){console.warn("[folder] scan error:",_)}finally{m=!1,H()}}}function F(){p&&clearInterval(p),p=setInterval(G,l*1e3)}function Q(){p&&(clearInterval(p),p=null)}function oe(_){if(!r||d)return;const M=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return _.preventDefault(),_.returnValue=M,M}function $(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",oe))}function x(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",oe))}function y(){d=!1,F(),$(),H(),G()}function q(){d=!0,Q(),x(),H()}function z(){d=!1,F(),$(),H(),G()}function Y(){d=!0,Q(),x()}async function Z(){try{const _=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await T(_)){showToast("warn",t("folder-permission-denied"));return}r=_,await C("handles","main",_),c=0,u=0,f=0,w=[],await C("config","processed_count",0),await C("config","failed_count",0),await A("seen"),y()}catch(_){_&&_.name!=="AbortError"&&console.warn("[folder] pick failed:",_)}}async function le(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(Y(),r=null,c=0,u=0,f=0,w=[],await L("handles","main"),await L("config","processed_count"),await L("config","failed_count"),await A("seen"),g("folder-empty"),k("folder-status-empty",""))}async function re(){w=[];try{await L("config","recent_list")}catch{}D()}async function K(){if(E)return;if(E=!0,!n){g("folder-unsupported"),k("folder-status-unsupported",""),ne();return}ee();let _=null;try{_=await h("handles","main")}catch{}if(!_){g("folder-empty"),k("folder-status-empty","");return}if(!await T(_)){g("folder-empty"),k("folder-status-empty",""),await L("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}r=_;try{c=await h("config","processed_count")||0}catch{}try{u=await h("config","failed_count")||0}catch{}try{const j=await h("config","recent_list");Array.isArray(j)&&(w=j.map(J=>({...J,time:J.time?new Date(J.time):new Date})))}catch{}y()}function ee(){const _=document.getElementById("btn-folder-pick"),M=document.getElementById("btn-folder-pause"),j=document.getElementById("btn-folder-resume"),J=document.getElementById("btn-folder-scan-now"),O=document.getElementById("btn-folder-remove"),b=document.getElementById("btn-folder-clear-recent"),N=document.getElementById("folder-interval-select");_&&_.addEventListener("click",Z),M&&M.addEventListener("click",q),j&&j.addEventListener("click",z),J&&J.addEventListener("click",()=>{G()}),O&&O.addEventListener("click",le),b&&b.addEventListener("click",re),N&&N.addEventListener("change",V=>{l=parseInt(V.target.value,10)||60,d||F()}),te()}function te(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(_=>{_.dataset.tabJumpBound||(_.dataset.tabJumpBound="1",_.addEventListener("click",M=>{const j=M.currentTarget.dataset.tabJump;if(j==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(j==="upload"){const J=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');J&&J.click()}}))})}function ne(){te()}window._loadFolderWatcherPanel=K;function se(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(M=>/chromium|google chrome|microsoft edge/i.test(M.brand||""))}catch{}const _=navigator.userAgent||"";return!!(/Edg\//.test(_)||/Chrome\//.test(_)&&!/OPR\/|YaBrowser|Opera/.test(_))}function ue(){try{if(se()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const _=document.getElementById("chrome-only-banner");if(!_)return;const M=_.querySelector('[data-i18n="chrome-banner-msg"]'),j=_.querySelector('[data-i18n="chrome-banner-dismiss"]');M&&typeof t=="function"&&(M.textContent=t("chrome-banner-msg")),j&&typeof t=="function"&&(j.textContent=t("chrome-banner-dismiss")),_.style.display="";const J=document.getElementById("chrome-only-banner-close");J&&!J.dataset.bound&&(J.dataset.bound="1",J.addEventListener("click",()=>{_.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):setTimeout(ue,0)),window._refreshChromeBanner=ue})();const Ja=`
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
    `;ke("email-modal",Ja);(function(){let e=null,n=null,a="new",o=!1,s=!1;async function i(){const B=document.getElementById("email-empty"),P=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!B||!P))try{const U=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(U.status===401){localStorage.removeItem("mrpilot_token");const F=await U.json().catch(()=>({}));if((typeof F.detail=="string"?F.detail:F.detail&&F.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!U.ok){p("none");return}const G=await U.json();e=G.account||null,n=G.presets||{},o=!0,r(),e&&I()}catch(U){console.error("[email-ingest] load failed",U),p("none")}}function r(){const B=document.getElementById("email-empty"),P=document.getElementById("email-account-card"),U=document.getElementById("email-logs-section");if(!e){B.style.display="",P.style.display="none",U&&(U.style.display="none"),p("none");return}B.style.display="none",P.style.display="",U&&(U.style.display="");const G=document.getElementById("email-account-addr"),F=document.getElementById("email-account-host"),Q=document.getElementById("email-account-last"),oe=document.getElementById("email-last-error"),$=document.getElementById("email-enabled-toggle");if(G&&(G.textContent=e.email_address||"-"),F&&(F.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),Q){const x=e.last_fetched_at;if(!x)Q.textContent=t("email-last-never");else{const y=l(x),q=!e.last_error;Q.textContent=q?t("email-last-ok",{time:y}):t("email-last-fail",{time:y})}}oe&&(e.last_error?(oe.style.display="",oe.textContent=d(e.last_error)):oe.style.display="none"),$&&($.checked=!!e.enabled),e.enabled?e.last_error?p("error"):p("on"):p("off")}function p(B){const P=document.getElementById("email-status-summary");if(!P)return;P.classList.remove("none","ready","active","coming");let U="auto-status-loading";B==="none"?(U="email-status-none",P.classList.add("none")):B==="on"?(U="email-status-on",P.classList.add("active")):B==="off"?(U="email-status-off",P.classList.add("coming")):B==="error"&&(U="email-status-error",P.classList.add("none")),P.setAttribute("data-i18n",U),P.textContent=t(U)}function l(B){if(!B)return"";const P=new Date(B);if(isNaN(P.getTime()))return"";const U=G=>String(G).padStart(2,"0");return`${U(P.getMonth()+1)}-${U(P.getDate())} ${U(P.getHours())}:${U(P.getMinutes())}`}function d(B){if(!B)return"";const P=String(B);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(P)?t("email-test-auth-fail"):/timeout|timed out/i.test(P)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(P),P)}function m(B){a=B;const P=document.getElementById("email-modal");if(!P)return;const U=document.getElementById("email-preset");U.innerHTML="";const G=n||{},F=["gmail","outlook","yahoo","icloud","qq","163","custom"],Q={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};F.forEach(ee=>{if(!G[ee])return;const te=document.createElement("option");te.value=ee,te.textContent=ee==="custom"?t("email-preset-custom"):Q[ee]||ee,U.appendChild(te)});const oe=document.getElementById("email-modal-title"),$=document.getElementById("email-address"),x=document.getElementById("email-password"),y=document.getElementById("email-imap-host"),q=document.getElementById("email-imap-port"),z=document.getElementById("email-imap-ssl"),Y=document.getElementById("email-folder"),Z=document.getElementById("email-mark-read"),le=document.getElementById("email-bind-enabled"),re=document.getElementById("email-test-result"),K=document.getElementById("email-adv-details");if(re&&(re.style.display="none",re.textContent=""),B==="edit"&&e){oe.setAttribute("data-i18n","email-modal-title-edit"),oe.textContent=t("email-modal-title-edit"),$.value=e.email_address||"",x.value="",x.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),x.placeholder=t("email-field-password-edit-ph"),y.value=e.imap_host||"",q.value=e.imap_port||993,z.checked=e.imap_use_ssl!==!1,Y.value=e.folder||"INBOX",Z.checked=e.mark_as_read!==!1,le.checked=e.enabled!==!1;const ee=document.getElementById("email-filter-sender"),te=document.getElementById("email-filter-subject");ee&&(ee.value=e.filter_sender||""),te&&(te.value=e.filter_subject||""),h(e.interval_min||15),U.value=S(e.imap_host)||"custom",K&&(K.open=!0)}else{oe.setAttribute("data-i18n","email-modal-title-new"),oe.textContent=t("email-modal-title-new"),$.value="",x.value="",x.setAttribute("data-i18n-placeholder","email-field-password-ph"),x.placeholder=t("email-field-password-ph"),U.value="gmail",u("gmail"),Y.value="INBOX",Z.checked=!0,le.checked=!0;const ee=document.getElementById("email-filter-sender"),te=document.getElementById("email-filter-subject");ee&&(ee.value=""),te&&(te.value=""),h(15),K&&(K.open=!1)}v(),P.style.display="flex",setTimeout(()=>$.focus(),60)}function c(){const B=document.getElementById("email-modal");B&&(B.style.display="none")}function u(B){const P=(n||{})[B];if(!P||B==="custom")return;const U=document.getElementById("email-imap-host"),G=document.getElementById("email-imap-port"),F=document.getElementById("email-imap-ssl");U&&(U.value=P.host||""),G&&(G.value=P.port||993),F&&(F.checked=P.ssl!==!1)}const f={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function w(B){if(!B||!B.includes("@"))return;const P=B.split("@")[1].toLowerCase().trim(),U=f[P];if(!U)return;const G=document.getElementById("email-preset");if(!G)return;const F=G.value;F&&F!=="custom"&&F!==""&&F===U||(G.value=U,u(U))}function S(B){if(!B)return null;const P=n||{};for(const U in P)if(U!=="custom"&&P[U]&&P[U].host===B)return U;return null}function E(){const B=document.querySelector("#email-interval-options .email-interval-btn.active"),P=B?parseInt(B.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(P)?P:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function v(){const B=document.getElementById("email-interval-options");!B||B._bound||(B._bound=!0,B.addEventListener("click",P=>{const U=P.target.closest(".email-interval-btn");U&&(B.querySelectorAll(".email-interval-btn").forEach(G=>G.classList.remove("active")),U.classList.add("active"))}))}function h(B){const P=[5,15,60].includes(B)?B:15,U=document.getElementById("email-interval-options");U&&U.querySelectorAll(".email-interval-btn").forEach(G=>{G.classList.toggle("active",parseInt(G.dataset.interval,10)===P)})}function C(B,P){const U=document.getElementById("email-test-result");U&&(U.style.display="",U.textContent=P,U.className="form-test-result "+(B==="ok"?"ok":B==="running"?"running":"fail"))}async function L(){const B=E();if(!B.email_address){C("fail",t("email-addr-required"));return}if(!B.password){C("fail",t("email-password-required"));return}if(!B.imap_host){C("fail",t("email-host-required"));return}const P=document.getElementById("btn-email-modal-test");P&&(P.disabled=!0),C("running",t("email-test-running"));try{const U=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:B.email_address,password:B.password,imap_host:B.imap_host,imap_port:B.imap_port,imap_use_ssl:B.imap_use_ssl,folder:B.folder})}),G=await U.json().catch(()=>({}));if(U.ok&&G.success)C("ok",t("email-test-ok",{folder:B.folder,n:G.folder_count??"?"}));else{const F=G.error_msg||"";F==="auth_failed"||/auth/i.test(F)?C("fail",t("email-test-auth-fail")):C("fail",t("email-test-fail",{msg:F||U.status}))}}catch(U){C("fail",t("email-test-fail",{msg:String(U).slice(0,120)}))}finally{P&&(P.disabled=!1)}}async function A(){const B=E();if(!B.email_address){C("fail",t("email-addr-required"));return}if(a==="new"&&!B.password){C("fail",t("email-password-required"));return}if(!B.imap_host){C("fail",t("email-host-required"));return}const P=document.getElementById("btn-email-modal-save");P&&(P.disabled=!0);const U={...B};a==="edit"&&!U.password&&delete U.password;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(U)}),F=await G.json().catch(()=>({}));if(G.ok&&F.ok)e=F.account,showToast(t("email-save-ok"),"success"),c(),r(),I();else{const oe="email."+(F.detail||"").split(".").slice(-1)[0];C("fail",t(oe)!==oe?t(oe):t("email-save-fail"))}}catch{C("fail",t("email-save-fail"))}finally{P&&(P.disabled=!1)}}async function T(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),r();const U=document.getElementById("email-logs-list");U&&(U.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function k(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const B=document.getElementById("btn-email-trigger"),P=B?B.innerHTML:"";B&&(B.disabled=!0,B.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const U=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),G=await U.json().catch(()=>({}));if(U.ok){const F=G.emails_scanned||0,Q=G.ocr_succeeded||0,oe=G.ocr_failed||0;F===0&&Q===0&&oe===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:F,ok:Q,fail:oe}),oe>0?"warn":"success")}else{const Q="email."+(G.detail||"").split(".").slice(-1)[0];showToast(t(Q)!==Q?t(Q):t("email-trigger-fail"),"error")}await i()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,B&&(B.disabled=!1,B.innerHTML=P)}}async function g(){if(!e)return;const B=document.getElementById("email-enabled-toggle"),P=!!(B&&B.checked),U=e.enabled;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:P})}),F=await G.json().catch(()=>({}));G.ok&&F.ok?(e=F.account,r()):(B&&(B.checked=U),showToast(t("email-toggle-fail"),"error"))}catch{B&&(B.checked=U),showToast(t("email-toggle-fail"),"error")}}async function I(){const B=document.getElementById("email-logs-list");if(B){B.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const P=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!P.ok){B.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const U=await P.json();if(!Array.isArray(U)||U.length===0){B.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}B.innerHTML=U.map(H).join("")}catch{B.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function H(B){const P=l(B.created_at),U=B.status||"failed",G=U==="success"?"ok":U==="partial"?"partial":"fail",F=U==="success"?"✓":U==="partial"?"◐":"✗",Q=B.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,oe=t("email-log-counts",{scanned:B.emails_scanned||0,att:B.attachments_found||0,ok:B.ocr_succeeded||0,fail:B.ocr_failed||0}),$=(B.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${G}">
                <span class="log-time">${escapeHtml(P)}</span>
                <span class="log-status">${F}</span>
                ${Q}
                <span class="log-counts">${escapeHtml(oe)}</span>
                <span class="log-elapsed">${escapeHtml($)}</span>
            </div>
        `}function D(){const B=document.getElementById("btn-email-bind");B&&B.addEventListener("click",()=>m("new"));const P=document.getElementById("btn-email-edit");P&&P.addEventListener("click",()=>m("edit"));const U=document.getElementById("btn-email-unbind");U&&U.addEventListener("click",T);const G=document.getElementById("btn-email-trigger");G&&G.addEventListener("click",k);const F=document.getElementById("email-enabled-toggle");F&&F.addEventListener("change",g);const Q=document.getElementById("email-modal-close");Q&&Q.addEventListener("click",c);const oe=document.getElementById("btn-email-modal-cancel");oe&&oe.addEventListener("click",c);const $=document.getElementById("btn-email-modal-test");$&&$.addEventListener("click",L);const x=document.getElementById("btn-email-modal-save");x&&x.addEventListener("click",A);const y=document.getElementById("email-preset");y&&y.addEventListener("change",Y=>u(Y.target.value));const q=document.getElementById("email-address");q&&!q.dataset.autoBound&&(q.dataset.autoBound="1",q.addEventListener("blur",Y=>w((Y.target.value||"").trim())),q.addEventListener("input",Y=>{const Z=(Y.target.value||"").trim();Z.includes("@")&&Z.split("@")[1].includes(".")&&w(Z)}));const z=document.getElementById("btn-email-refresh-logs");z&&z.addEventListener("click",()=>{z.classList.add("spinning"),setTimeout(()=>z.classList.remove("spinning"),600),I()})}D(),window._loadEmailIngestPanel=i,window._rerenderEmailIngest=function(){if(!o)return;r();const B=document.getElementById("email-logs-section");e&&B&&B.open&&I()};let R=null;window._startEmailLogAutoRefresh=function(){R||(R=setInterval(()=>{e&&o&&I()},3e4))},window._stopEmailLogAutoRefresh=function(){R&&(clearInterval(R),R=null)}})();const Ya=`
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
`;ke("bank-cand-drawer",Ya);const Wa=`
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
`;ke("bank-client-picker-modal",Wa);(function(){let e=[],n=null,a=[],o="all",s=null,i=!1;async function r(){if(i){D();return}i=!0,p(),await l(),D()}function p(){const b=document.getElementById("bank-file-input");b&&!b._bound&&(b._bound=!0,b.addEventListener("change",w));const N=document.getElementById("btn-bank-queue-clear-done");N&&!N._bound&&(N._bound=!0,N.addEventListener("click",L));const V=document.getElementById("btn-bank-back");V&&!V._bound&&(V._bound=!0,V.addEventListener("click",()=>{n=null,a=[],Q()}));const W=document.getElementById("btn-bank-delete");W&&!W._bound&&(W._bound=!0,W.addEventListener("click",g));const X=document.getElementById("btn-bank-run-match");X&&!X._bound&&(X._bound=!0,X.addEventListener("click",k)),document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{o=fe.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(me=>{me.classList.toggle("active",me===fe)}),Z()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",ne))});const de=document.getElementById("btn-bank-cand-pane-close");de&&!de._bound&&(de._bound=!0,de.addEventListener("click",ne));const ie=document.getElementById("btn-bank-cand-ignore");ie&&!ie._bound&&(ie._bound=!0,ie.addEventListener("click",I));const ce=document.getElementById("btn-bank-cand-ignore-pane");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",I));const ae=document.getElementById("bank-client-badge");ae&&!ae._bound&&(ae._bound=!0,ae.addEventListener("click",x)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",y))});const pe=document.getElementById("btn-bank-client-picker-save");pe&&!pe._bound&&(pe._bound=!0,pe.addEventListener("click",z)),document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{R=fe.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(me=>{me.classList.toggle("active",me===fe)}),B()}))})}async function l(){try{const b=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!b.ok)throw new Error("sessions:"+b.status);e=await b.json(),B()}catch(b){console.warn("[bank-recon] loadSessions failed",b),e=[],B()}}async function d(b){try{const N="/api/bank-recon/sessions/"+encodeURIComponent(b)+(o!=="all"?"?filter="+o:""),V=await fetch(N,{headers:{Authorization:"Bearer "+token}});if(!V.ok)throw new Error("detail:"+V.status);const W=await V.json();n=W.session,a=W.transactions||[],F()}catch(N){console.warn("[bank-recon] loadSessionDetail failed",N),showToast(t("bank-load-failed"),"error")}}let m=[],c=0;const u=3;function f(){return c+=1,"q"+c+"_"+Date.now()}async function w(b){const N=Array.from(b.target.files||[]);if(b.target.value="",N.length!==0){for(const V of N){const W={id:f(),file:V,name:V.name,size:V.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};V.name.toLowerCase().endsWith(".pdf")?V.size>20*1024*1024&&(W.status="failed",W.error_code="bank_recon.file_too_large"):(W.status="failed",W.error_code="bank_recon.only_pdf"),m.push(W)}S(),E(),A()}}function S(){const b=document.getElementById("bank-upload-queue");b&&(b.style.display=""),se(),ue()}function E(){const b=document.getElementById("bank-upload-queue-list"),N=document.getElementById("bank-upload-queue-summary");if(!b)return;if(m.length===0){b.innerHTML="",N&&(N.textContent="");const ie=document.getElementById("bank-upload-queue");ie&&(ie.style.display="none");return}let V=0,W=0,X=0,de=0;for(const ie of m)ie.status==="ok"?V++:ie.status==="failed"?W++:ie.status==="uploading"||ie.status==="parsing"?X++:de++;N&&(N.textContent=t("bank-queue-summary").replace("{ok}",V).replace("{run}",X).replace("{wait}",de).replace("{fail}",W)),b.innerHTML=m.map(v).join(""),b.querySelectorAll("[data-q-act]").forEach(ie=>{const ce=ie.dataset.qAct,ae=ie.dataset.qId;ie.addEventListener("click",()=>{ce==="retry"&&h(ae),ce==="remove"&&C(ae)})})}function v(b){const N=(b.size/1024).toFixed(0)+" KB";let V="",W="";if(b.status==="pending")V='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",W='<button data-q-act="remove" data-q-id="'+O(b.id)+'" class="bq-act">×</button>';else if(b.status==="uploading")V='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(b.progress||0)+'%"></div></div>';else if(b.status==="parsing")V='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(b.status==="ok")V='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",b.tx_count||0)+"</span>",W='<button data-q-act="remove" data-q-id="'+O(b.id)+'" class="bq-act">×</button>';else if(b.status==="failed"){const X=_(b.error_code||"unknown");V='<span class="bq-stat bq-fail" title="'+O(X)+'">'+O(X)+"</span>",W='<button data-q-act="retry" data-q-id="'+O(b.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+O(b.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+O(b.id)+'"><div class="bq-name" title="'+O(b.name)+'">'+O(b.name)+'</div><div class="bq-size">'+N+'</div><div class="bq-status">'+V+'</div><div class="bq-actions">'+W+"</div></div>"}function h(b){const N=m.find(V=>V.id===b);N&&(N.status="pending",N.error_code=null,N.progress=0,E(),A())}function C(b){const N=m.findIndex(W=>W.id===b);if(N<0)return;const V=m[N];V.status==="uploading"||V.status==="parsing"||(m.splice(N,1),E())}function L(){m=m.filter(b=>b.status!=="ok"),E()}async function A(){for(;;){if(m.filter(V=>V.status==="uploading"||V.status==="parsing").length>=u)return;const N=m.find(V=>V.status==="pending");if(!N){m.every(V=>V.status==="ok"||V.status==="failed")&&(await l(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}T(N).then(()=>A())}}async function T(b){b.status="uploading",b.progress=0,E();try{const N=new FormData;N.append("file",b.file,b.name);const V=await new Promise((X,de)=>{const ie=new XMLHttpRequest;ie.open("POST","/api/bank-recon/upload"),ie.setRequestHeader("Authorization","Bearer "+token),ie.upload.onprogress=ce=>{ce.lengthComputable&&(b.progress=Math.min(99,Math.round(ce.loaded/ce.total*100)),E())},ie.upload.onload=()=>{b.status="parsing",E()},ie.onload=()=>{ie.status>=200&&ie.status<300?X({status:ie.status,text:ie.responseText}):X({status:ie.status,text:ie.responseText})},ie.onerror=()=>de(new Error("network")),ie.send(N)});let W={};try{W=JSON.parse(V.text||"{}")}catch{W={}}if(V.status>=400){b.status="failed",b.error_code=W&&W.detail||"unknown",E();return}if(W.parse_status==="parse_failed"){b.status="failed",b.error_code=W.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",E();return}b.status="ok",b.tx_count=W.tx_count||0,b.session_id=W.session_id||null,E()}catch(N){console.warn("[bank-recon] upload failed",N),b.status="failed",b.error_code="network",E()}}async function k(){if(!n)return;const b=document.getElementById("btn-bank-run-match"),N=b.innerHTML;b.disabled=!0,b.innerHTML="<span>"+t("bank-matching")+"</span>";try{const V=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!V.ok)throw new Error("match:"+V.status);const W=await V.json();showToast(t("bank-match-done").replace("{matched}",W.matched).replace("{suggested}",W.suggested).replace("{unmatched}",W.unmatched),"success"),await d(n.id),await l()}catch(V){console.warn("[bank-recon] match failed",V),showToast(t("bank-match-failed"),"error")}finally{b.disabled=!1,b.innerHTML=N}}async function g(){if(!(!n||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const N=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!N.ok)throw new Error("delete:"+N.status);showToast(t("bank-deleted"),"success"),n=null,a=[],Q(),await l()}catch(N){console.warn("[bank-recon] delete failed",N),showToast(t("bank-delete-failed"),"error")}}async function I(){if(s)try{const b=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!b.ok)throw new Error("ignore:"+b.status);ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}}async function H(b){if(s)try{const N=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:b})});if(!N.ok)throw new Error("pick:"+N.status);showToast(t("bank-matched-ok"),"success"),ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}}function D(){const b=document.getElementById("bank-status-summary");if(!b)return;if(e.length===0){b.textContent=t("bank-pill-none");return}let V=0;for(const W of e)W.parse_status==="parsed"&&(W.unmatched_count||0)>0&&V++;b.textContent=V>0?t("bank-pill-pending").replace("{n}",V):t("bank-pill-ok")}let R="all";function B(){const b=document.getElementById("bank-sessions-list");if(!b)return;let N=e||[];if(R==="parsed"?N=N.filter(V=>V.parse_status==="parsed"):R==="failed"&&(N=N.filter(V=>V.parse_status==="parse_failed")),!e||e.length===0){b.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(N.length===0){b.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}b.innerHTML=N.map(V=>U(V)).join(""),b.querySelectorAll(".bank-session-row").forEach(V=>{V.addEventListener("click",W=>{W.target.closest(".bank-session-trash")||d(V.dataset.sessionId)})}),b.querySelectorAll(".bank-session-trash").forEach(V=>{V.addEventListener("click",W=>{W.stopPropagation();const X=V.dataset.sessionId,de=V.dataset.sessionName||"";P(X,de)})})}async function P(b,N){if(!b)return;const V=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",N||"");if(await showConfirm(V,{danger:!0}))try{const X=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(b),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!X.ok)throw new Error("delete:"+X.status);showToast(t("bank-deleted"),"success"),n&&n.id===b&&(n=null,a=[],Q()),await l(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(X){console.warn("[bank-recon] delete failed",X),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=P;function U(b){const N=(b.bank_code||"OTHER").toUpperCase(),V=J(b.period_start,b.period_end),W=b.account_last4?"···"+b.account_last4:"",X=G(b),de=j(b.created_at);return`
            <div class="bank-session-row" data-session-id="${O(b.id)}">
                <div class="bank-session-bank bk-${O(N)}">${O(N)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${O(b.source_filename||V||"-")}</div>
                    <div class="bank-session-meta">${O(V)} · ${O(W)} · ${O(de)}</div>
                </div>
                <div class="bank-session-counts">${X}</div>
                <button class="bank-session-trash" data-session-id="${O(b.id)}" data-session-name="${O(b.source_filename||"")}" title="${O(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function G(b){if(b.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(b.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const N=b.tx_count||0,V=b.matched_count||0,W=b.unmatched_count||0,X=[`<span class="bank-session-count">${N} ${t("bank-count-tx")}</span>`];return V>0&&X.push(`<span class="bank-session-count cnt-matched">${V} ${t("bank-count-matched")}</span>`),W>0&&X.push(`<span class="bank-session-count cnt-unmatched">${W} ${t("bank-count-unmatched")}</span>`),X.join("")}function F(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",Y(),Z(),oe()}function Q(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const b=document.getElementById("bank-detail-body");b&&b.classList.remove("has-pane"),s=null}function oe(){const b=document.getElementById("bank-client-badge");if(!b||!n)return;const N=n.client_id,V=document.getElementById("bank-client-badge-dot"),W=document.getElementById("bank-client-badge-name"),X=document.getElementById("bank-client-badge-caret"),de=typeof _userInfo<"u"?_userInfo:null,ie=!(de&&de.role==="member");if(N!=null){const ce=(window._clientsCache||[]).find(ae=>Number(ae.id)===Number(N));b.classList.remove("is-empty"),V&&(V.style.background=ce&&ce.color||"#111111"),W&&(W.textContent=ce&&(ce.short_name||ce.name)||"#"+N)}else b.classList.add("is-empty"),V&&(V.style.background=""),W&&(W.textContent=t("bank-client-none"));ie?(b.classList.remove("is-readonly"),b.disabled=!1,X&&(X.style.display="")):(b.classList.add("is-readonly"),b.disabled=!0,X&&(X.style.display="none")),b.style.display=""}let $=null;function x(){if(!n)return;const b=typeof _userInfo<"u"?_userInfo:null;if(!!(b&&b.role==="member"))return;$=n.client_id!=null?Number(n.client_id):null,q();const V=document.getElementById("bank-client-picker-modal");V&&(V.style.display="")}function y(){const b=document.getElementById("bank-client-picker-modal");b&&(b.style.display="none"),$=null}function q(){const b=document.getElementById("bank-client-picker-list");if(!b)return;const N=(window._clientsCache||[]).filter(W=>W&&(W.is_active===!0||W.is_active===void 0)),V=[];V.push('<div class="bank-client-picker-row is-none'+($==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+O(t("bank-client-picker-none"))+"</span></div>"),N.forEach(W=>{const X=Number(W.id)===Number($)?" is-selected":"";V.push('<div class="bank-client-picker-row'+X+'" data-cid="'+O(W.id)+'"><span class="bank-cp-dot" style="background:'+O(W.color||"#111111")+'"></span><span>'+O(W.short_name||W.name||"#"+W.id)+"</span></div>")}),b.innerHTML=V.join(""),b.querySelectorAll(".bank-client-picker-row").forEach(W=>{W.addEventListener("click",()=>{const X=W.dataset.cid;$=X?Number(X):null,q()})})}async function z(){if(n)try{const b=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:$})});if(!b.ok)throw new Error("client:"+b.status);n.client_id=$,oe(),showToast(t("bank-client-changed"),"success"),y();try{await l()}catch{}}catch(b){console.warn("[bank-recon] save client failed",b),showToast(t("bank-client-change-failed"),"error")}}function Y(){if(!n)return;const b=n;document.getElementById("bank-detail-title").textContent=(b.bank_code||"-")+(b.account_last4?" ···"+b.account_last4:"")+" · "+(b.source_filename||""),document.getElementById("bank-meta-period").textContent=J(b.period_start,b.period_end)||"-",document.getElementById("bank-meta-opening").textContent=M(b.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+M(b.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+M(b.total_outflow),document.getElementById("bank-meta-closing").textContent=M(b.closing_balance);const N=a||[],V=N.length;let W=0,X=0,de=0;for(const ie of N){const ce=ie.match_status||"unmatched";ce==="matched"?W++:ce==="suggested"?X++:de++}document.getElementById("bank-stat-total").textContent=V,document.getElementById("bank-stat-matched").textContent=W,document.getElementById("bank-stat-suggested").textContent=X,document.getElementById("bank-stat-unmatched").textContent=de}function Z(){const b=document.getElementById("bank-tx-tbody");if(!b)return;let N=a||[];if(o!=="all"&&(N=N.filter(V=>o==="matched"?V.match_status==="matched":o==="suggested"?V.match_status==="suggested":o==="unmatched"?V.match_status==="unmatched"||V.match_status==="ignored":!0)),N.length===0){b.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(b.innerHTML=N.map(V=>le(V)).join(""),b.querySelectorAll("tr[data-tx-id]").forEach(V=>{V.addEventListener("click",()=>{const W=V.dataset.txId,X=a.find(de=>de.id===W);X&&(b.querySelectorAll("tr.is-selected").forEach(de=>de.classList.remove("is-selected")),V.classList.add("is-selected"),re(X))})}),s){const V=b.querySelector('tr[data-tx-id="'+s.id+'"]');V&&V.classList.add("is-selected")}}function le(b){const N=b.direction==="OUT",V=N?"-":"+",W=N?"bank-out":"bank-in",X=b.match_status||"unmatched",de=t("bank-match-"+X)||X,ie=j(b.tx_date),ce=b.channel?`<span class="bank-tx-channel">${O(b.channel)}</span>`:"";return`
            <tr data-tx-id="${O(b.id)}">
                <td class="bank-tx-date">${O(ie)}</td>
                <td class="bank-tx-desc">${ce}${O(b.description||"-")}</td>
                <td class="bank-td-amount ${W}">${V}${M(b.amount)}</td>
                <td><span class="bank-tx-match mt-${X}">${O(de)}</span></td>
            </tr>
        `}async function re(b){s=b;const N=document.getElementById("bank-detail-body");N&&N.classList.add("has-pane");const V=document.getElementById("bank-cand-pane-title"),W=document.getElementById("bank-cand-pane-sub"),X=document.getElementById("bank-cand-pane-foot");if(V&&(V.textContent=t("bank-cand-pane-current")),W){const ie=b.direction==="OUT"?"-":"+",ce=b.direction==="OUT"?"bank-out":"bank-in";W.innerHTML=`${O(j(b.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${O(b.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${ce}">${ie}${M(b.amount)}</strong>`}X&&(X.style.display="");const de=document.getElementById("bank-cand-pane-body");if(de){de.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const ie=await fetch("/api/bank-recon/tx/"+encodeURIComponent(b.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!ie.ok)throw new Error("cands:"+ie.status);const ce=await ie.json();te(b,ce.candidates||[])}catch{de.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function K(b){const N=Number(b||0);let V="score-low";return N>=85?V="score-high":N>=60&&(V="score-mid"),'<span class="bank-cand-score '+V+'">'+N.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function ee(b,N,V){const W=N.history_id,X=N.invoice_no||"-",de=N.vendor||"-",ie=N.amount_total!==null&&N.amount_total!==void 0?M(N.amount_total):"-",ce=N.invoice_date?j(N.invoice_date):"-",ae=N.filename||"",pe=!!V&&b.matched_history_id===W,fe="bank-cand-card"+(N.is_auto_picked?" is-auto":"")+(pe?" is-picked":"");let me="";return pe?me='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":me='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+O(W)+'"><span>'+t(N.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+fe+'" data-hid="'+O(W)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+O(de)+"</div>"+K(N.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+O(X)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+ie+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+O(ce)+"</span></div>"+(ae?'<div class="bank-cand-card-file" title="'+O(ae)+'">'+O(ae)+"</div>":"")+(N.reason?'<div class="bank-cand-card-reason">'+O(N.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+me+"</div></div>"}function te(b,N){const V=document.getElementById("bank-cand-pane-body");if(!V)return;const W=N||[];let X="";if(b.match_status==="matched")X='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",W.length)+"</div>";else if(b.match_status==="suggested")X='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",W.length)+"</div>";else if(W.length>0)X='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",W.length)+"</div>";else{V.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const de=b.match_status==="matched",ie=W.map(ce=>ee(b,ce,de)).join("");V.innerHTML=X+'<div class="bank-cand-list">'+ie+"</div>",V.querySelectorAll('[data-act="pick"]').forEach(ce=>{ce.addEventListener("click",()=>{H(ce.dataset.hid)})}),V.querySelectorAll('[data-act="unmatch"]').forEach(ce=>{ce.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(b.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function ne(){const b=document.getElementById("bank-detail-body");b&&b.classList.remove("has-pane");const N=document.getElementById("bank-cand-pane-title"),V=document.getElementById("bank-cand-pane-sub"),W=document.getElementById("bank-cand-pane-body"),X=document.getElementById("bank-cand-pane-foot");N&&(N.textContent=t("bank-cand-pane-empty-title")),V&&(V.textContent=t("bank-cand-pane-empty-sub")),X&&(X.style.display="none"),W&&(W.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const de=document.getElementById("bank-tx-tbody");de&&de.querySelectorAll("tr.is-selected").forEach(ie=>ie.classList.remove("is-selected")),s=null}function se(b){const N=document.getElementById("bank-upload-progress");N&&(N.style.display="none")}function ue(){const b=document.getElementById("bank-upload-error");b&&(b.style.display="none")}function _(b){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[b]||t("bank-err-unknown")+" ("+b+")"}function M(b){if(b==null)return"-";const N=Number(b);return isNaN(N)?"-":N.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function j(b){if(!b)return"-";const N=String(b);return N.length>=10?N.slice(0,10):N}function J(b,N){return!b&&!N?"":(j(b)||"?")+" ~ "+(j(N)||"?")}function O(b){return b==null?"":String(b).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=r,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(B(),n&&(Y(),Z(),oe(),!s)){const b=document.getElementById("bank-cand-pane-title"),N=document.getElementById("bank-cand-pane-sub");b&&(b.textContent=t("bank-cand-pane-empty-title")),N&&(N.textContent=t("bank-cand-pane-empty-sub"))}E()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(b){b&&(i||await r(),await d(b))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Xa=`
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
    `,Za=`
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
    `;ke("client-modal-mask",Xa);ke("wsclient-modal-mask",Za);(function(){let e=[],n=null,a="",o="seller";const s={page:0,pageSize:12,keyword:""},i=new Set;let r=[];const p={keyword:""};let l=null;function d(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function m(y,q={}){const z=await fetch(y,{...q,headers:{"Content-Type":"application/json",...d(),...q.headers||{}}});if(!z.ok){const Y=await z.json().catch(()=>({}));throw new Error(Y.detail||"HTTP "+z.status)}return z.json()}async function c(){try{e=(await m("/api/clients")).clients||[],window._clientsCache=e}catch(y){console.error("loadClientsCache fail",y),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function u(y){o=y==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(Y=>Y.classList.toggle("active",Y.dataset.custTab===o));const q=document.getElementById("cust-pane-seller"),z=document.getElementById("cust-pane-buyer");q&&q.classList.toggle("active",o==="seller"),z&&z.classList.toggle("active",o==="buyer")}function f(){const y=window._userInfo||{},q=String(y.role||"").toLowerCase(),z=String(y.tenant_role||"").toLowerCase();return y.is_super_admin===!0||y.is_owner===!0||q==="owner"||q==="admin"||z==="owner"||z==="admin"}function w(){window._workspaceClientsCache=r,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function S(){try{const y=await m("/api/workspace/clients");r=y&&(y.clients||y.items)||[],window._workspaceClientsCache=r}catch(y){console.error("loadSellerCache fail",y),r=[]}return r}function E(){const y=p.keyword.trim().toLowerCase();return y?r.filter(q=>(q.name||"").toLowerCase().includes(y)||(q.tax_id||"").toLowerCase().includes(y)):r}function v(){const y=document.getElementById("seller-tbody");if(!y)return;const q=f(),z=document.getElementById("btn-seller-new");z&&(z.style.display=q?"":"none");const Y=E(),Z=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!Y.length){y.innerHTML=`<div class="cust-empty">${escapeHtml(t(p.keyword?"cust-no-match":"seller-empty"))}</div>`;return}y.innerHTML=Y.map(le=>{const K=Z!=null&&Number(Z)===Number(le.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${le.id}">${escapeHtml(t("seller-set-current"))}</button>`,ee=q?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${le.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(le.name||"#"+le.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(le.tax_id||"—")}</div>
                <div class="align-right">${le.invoice_count||0}</div>
                <div class="cust-row-actions">${K}${ee}</div>
            </div>`}).join("")}function h(y){l=y?y.id:null,document.getElementById("wsclient-modal-title").textContent=t(y?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=y&&y.name||"",document.getElementById("wsclient-input-tax").value=y&&y.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=y?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function C(){document.getElementById("wsclient-modal-mask").style.display="none",l=null}async function L(){const y=document.getElementById("wsclient-input-name").value.trim(),q=document.getElementById("wsclient-input-tax").value.trim();if(!y){showToast(t("client-msg-name-required"),"fail");return}try{l?(await m("/api/workspace/clients/"+l,{method:"PATCH",body:JSON.stringify({name:y,tax_id:q})}),showToast(t("client-msg-updated"),"success")):(await m("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:y,tax_id:q||null})}),showToast(t("client-msg-created"),"success")),C(),await S(),v(),w()}catch(z){const Y=z&&z.message?z.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+Y,"fail")}}async function A(){if(!l)return;const y=r.find(z=>Number(z.id)===Number(l));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",y?y.name:""),{danger:!0}))try{const z=l;await m("/api/workspace/clients/"+z,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(z)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),C(),await S(),v(),w()}catch{showToast(t("client-msg-save-fail"),"fail")}}function T(){const y=s.keyword.trim().toLowerCase();return y?e.filter(q=>(q.name||"").toLowerCase().includes(y)||(q.short_name||"").toLowerCase().includes(y)||(q.tax_id||"").toLowerCase().includes(y)):e}function k(){const y=T(),q=s.pageSize,z=Math.max(0,Math.ceil(y.length/q)-1);s.page>z&&(s.page=z);const Y=s.page*q;return{all:y,items:y.slice(Y,Y+q),start:Y,ps:q,total:y.length,maxPage:z}}function g(){const y=document.getElementById("buyer-tbody");if(!y)return;const{items:q,start:z,ps:Y,total:Z,maxPage:le}=k();Z?y.innerHTML=q.map(te=>{const ne=i.has(te.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${te.id}">
                    <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${te.id}" ${ne?"checked":""}></div>
                    <div style="min-width:0">
                        <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(te.color||"#111")}"></span><span class="cust-name-text">${escapeHtml(te.name)}</span></div>
                        ${te.tax_id?`<div class="cust-cell-sub">${escapeHtml(te.tax_id)}</div>`:""}
                    </div>
                    <div class="align-right">${te.invoice_count||0}</div>
                    <div class="align-right cust-cell-amount">฿${(te.total_amount||0).toLocaleString(void 0,{maximumFractionDigits:0})}</div>
                    <div class="cust-row-actions">
                        <button class="cust-row-btn" data-action="edit" data-cid="${te.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                        <button class="cust-row-btn" data-action="export" data-cid="${te.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t("client-card-export"))}</span></button>
                    </div>
                </div>`}).join(""):y.innerHTML=`<div class="cust-empty">${escapeHtml(t(s.keyword?"cust-no-match":"clients-empty"))}</div>`;const re=document.getElementById("buyer-pager-info");re&&(re.textContent=Z?`${z+1}–${Math.min(z+Y,Z)} / ${Z}`:"0");const K=document.getElementById("buyer-prev");K&&(K.disabled=s.page<=0);const ee=document.getElementById("buyer-next");ee&&(ee.disabled=s.page>=le),I()}function I(){const y=i.size,q=document.getElementById("buyer-batch-bar");q&&(q.style.display=y?"flex":"none");const z=document.getElementById("buyer-batch-count");z&&(z.textContent=t("cust-selected-n").replace("{n}",y));const Y=document.getElementById("buyer-check-all");if(Y){const{items:Z}=k(),le=Z.map(K=>K.id),re=le.filter(K=>i.has(K)).length;Y.checked=le.length>0&&re===le.length,Y.indeterminate=re>0&&re<le.length}}function H(){i.clear(),g()}async function D(){const y=Array.from(i);if(!(!y.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",y.length),{danger:!0})))try{await m("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:y})}),showToast(t("client-msg-deleted"),"success"),i.clear(),await c(),g(),Q(),x()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const y=document.getElementById("seller-tbody");y&&(y.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const q=document.getElementById("buyer-tbody");q&&(q.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([S(),c()]),v(),g()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&v()});function R(y){n=y?y.id:null;const q=!!y;document.getElementById("client-modal-title").textContent=t(q?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=y&&y.name||"",document.getElementById("client-input-short").value=y&&y.short_name||"",document.getElementById("client-input-tax").value=y&&y.tax_id||"",document.getElementById("client-input-address").value=y&&y.address||"",document.getElementById("client-input-contact").value=y&&y.contact_person||"",document.getElementById("client-input-phone").value=y&&y.contact_phone||"",document.getElementById("client-input-email").value=y&&y.contact_email||"",document.getElementById("client-input-notes").value=y&&y.notes||"";const z=y&&y.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(Y=>{Y.classList.toggle("active",Y.dataset.color===z)}),document.getElementById("client-modal-delete").style.display=q?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function B(){document.getElementById("client-modal-mask").style.display="none",n=null}function P(){const y=document.querySelector("#client-color-picker .color-swatch.active");return y?y.dataset.color:"#111111"}async function U(){const y=document.getElementById("client-input-name").value.trim();if(!y){showToast(t("client-msg-name-required"),"fail");return}const q={name:y,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:P()};try{n?(await m(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify(q)}),showToast(t("client-msg-updated"),"success")):(await m("/api/clients",{method:"POST",body:JSON.stringify(q)}),showToast(t("client-msg-created"),"success")),B(),await c(),currentRoute==="clients"&&g(),Q(),x()}catch(z){console.error("saveClient fail",z);const Y=z&&z.message?z.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+Y,"fail")}}async function G(){if(!n)return;const y=e.find(Y=>Y.id===n);if(!y)return;const q=t("client-delete-confirm").replace("{name}",y.name);if(await showConfirm(q,{danger:!0}))try{await m(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),B(),await c(),currentRoute==="clients"&&g(),Q(),x()}catch(Y){console.error(Y),showToast(t("client-msg-save-fail"),"fail")}}async function F(y){const q=e.find(z=>z.id===y);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(y,q?q.name:"");return}try{const z=localStorage.getItem("mrpilot_token"),Y=await fetch(`/api/clients/${y}/export?month=all`,{headers:{Authorization:"Bearer "+z}});if(!Y.ok){let ee="HTTP "+Y.status;try{const te=await Y.json();te&&te.detail&&(ee=te.detail)}catch{}throw new Error(ee)}const Z=await Y.blob();if(Z.size<200){showToast(t("client-export-month-empty"),"info");return}const le=q&&q.name?q.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",re=URL.createObjectURL(Z),K=document.createElement("a");K.href=re,K.download=`${le}_export.csv`,K.click(),URL.revokeObjectURL(re)}catch(z){console.error("exportClient fail",z),showToast(t("client-msg-save-fail")+" · "+(z.message||""),"fail")}}function Q(){const y=document.getElementById("drawer-client-select");if(!y)return;const q=y.value;y.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(z=>`<option value="${z.id}">${escapeHtml(z.name)}</option>`).join(""),y.value=q||""}window.bindDrawerClient=function(y,q){const z=document.getElementById("drawer-client-select");if(!z)return;if(Q(),z.value=q?String(q):"",!y){z.onchange=null;const Z=document.getElementById("drawer-client-add");Z&&(Z.onclick=()=>R(null));return}z.onchange=async()=>{const Z=z.value?parseInt(z.value,10):null;try{await m(`/api/history/${y}/assign_client`,{method:"POST",body:JSON.stringify({client_id:Z})}),showToast(t("client-msg-updated"),"success");const le=_results[_drawerIdx];le&&(le.client_id=Z),await c()}catch(le){console.error(le),showToast(t("client-msg-save-fail"),"fail"),z.value=q?String(q):""}};const Y=document.getElementById("drawer-client-add");Y&&(Y.onclick=()=>R(null))};let oe={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const y=document.getElementById("drawer-cat-datalist"),q=Date.now();if(q-oe.fetched<300*1e3){y&&(y.innerHTML=oe.items.map(Y=>`<option value="${escapeHtml(Y)}">`).join("")),$(oe.supplier_count);return}const z=await m("/api/categories",{method:"GET"});oe.fetched=q,oe.items=z&&z.categories||[],oe.supplier_count=z&&z.supplier_count||0,y&&(y.innerHTML=oe.items.map(Y=>`<option value="${escapeHtml(Y)}">`).join("")),$(oe.supplier_count)}catch(y){console.warn("fillCategoryDatalist failed",y)}};function $(y){const q=document.getElementById("drawer-cat-learned-tag");q&&y>0&&(q.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",y))}function x(){const y=document.getElementById("history-client-filter");if(!y)return;const q=y.value;y.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(z=>`<option value="${z.id}">${escapeHtml(z.name)}</option>`).join(""),y.value=q||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const y=document.querySelector(".cust-tab-bar");y&&y.addEventListener("click",ae=>{const pe=ae.target.closest("[data-cust-tab]");pe&&u(pe.dataset.custTab)});const q=document.getElementById("btn-buyer-new");q&&q.addEventListener("click",()=>R(null));const z=document.getElementById("buyer-tbody");z&&z.addEventListener("click",ae=>{const pe=ae.target.closest(".buyer-row-check");if(pe){const ge=parseInt(pe.dataset.cid,10);pe.checked?i.add(ge):i.delete(ge);const be=pe.closest(".cust-row");be&&be.classList.toggle("selected",pe.checked),I();return}const fe=ae.target.closest(".cust-row-btn");if(fe){ae.stopPropagation();const ge=parseInt(fe.dataset.cid,10);if(fe.dataset.action==="edit"){const be=e.find(Ee=>Ee.id===ge);be&&R(be)}else fe.dataset.action==="export"&&F(ge);return}const me=ae.target.closest(".cust-row");if(me&&!ae.target.closest(".cust-cell-check")){const ge=e.find(be=>be.id===parseInt(me.dataset.cid,10));ge&&R(ge)}});const Y=document.getElementById("buyer-check-all");Y&&Y.addEventListener("change",()=>{const{items:ae}=k();ae.forEach(pe=>{Y.checked?i.add(pe.id):i.delete(pe.id)}),g()});const Z=document.getElementById("buyer-batch-cancel");Z&&Z.addEventListener("click",H);const le=document.getElementById("buyer-batch-delete");le&&le.addEventListener("click",D);const re=document.getElementById("buyer-prev");re&&re.addEventListener("click",()=>{s.page>0&&(s.page--,g())});const K=document.getElementById("buyer-next");K&&K.addEventListener("click",()=>{s.page++,g()});const ee=document.getElementById("buyer-search");if(ee){let ae;ee.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{s.keyword=ee.value,s.page=0;const pe=document.getElementById("buyer-search-clear");pe&&(pe.style.display=ee.value?"":"none"),g()},200)})}const te=document.getElementById("buyer-search-clear");te&&te.addEventListener("click",()=>{const ae=document.getElementById("buyer-search");ae&&(ae.value=""),s.keyword="",s.page=0,te.style.display="none",g()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>h(null));const se=document.getElementById("seller-tbody");se&&se.addEventListener("click",ae=>{const pe=ae.target.closest("[data-saction]");if(!pe)return;ae.stopPropagation();const fe=parseInt(pe.dataset.wid,10),me=pe.dataset.saction,ge=r.find(be=>Number(be.id)===fe);me==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(fe),v(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",ge?ge.name:""),"success")):me==="edit"?ge&&h(ge):me==="archive"&&(l=fe,A())});const ue=document.getElementById("seller-search");if(ue){let ae;ue.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{p.keyword=ue.value;const pe=document.getElementById("seller-search-clear");pe&&(pe.style.display=ue.value?"":"none"),v()},200)})}const _=document.getElementById("seller-search-clear");_&&_.addEventListener("click",()=>{const ae=document.getElementById("seller-search");ae&&(ae.value=""),p.keyword="",_.style.display="none",v()});const M=document.getElementById("wsclient-modal-close");M&&M.addEventListener("click",C);const j=document.getElementById("wsclient-modal-cancel");j&&j.addEventListener("click",C);const J=document.getElementById("wsclient-modal-save");J&&J.addEventListener("click",L);const O=document.getElementById("wsclient-modal-archive");O&&O.addEventListener("click",A);const b=document.getElementById("wsclient-modal-mask");b&&b.addEventListener("click",ae=>{ae.target===b&&C()});const N=document.getElementById("client-modal-close");N&&N.addEventListener("click",B);const V=document.getElementById("client-modal-cancel");V&&V.addEventListener("click",B);const W=document.getElementById("client-modal-save");W&&W.addEventListener("click",U);const X=document.getElementById("client-modal-delete");X&&X.addEventListener("click",G);const de=document.getElementById("client-modal-mask");de&&de.addEventListener("click",ae=>{ae.target===de&&B()});const ie=document.getElementById("client-color-picker");ie&&ie.addEventListener("click",ae=>{const pe=ae.target.closest(".color-swatch");pe&&(ie.querySelectorAll(".color-swatch").forEach(fe=>fe.classList.remove("active")),pe.classList.add("active"))});const ce=document.getElementById("history-client-filter");ce&&ce.addEventListener("change",()=>{a=ce.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>c(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function n($,x){let y=t($)||$;if(x)for(const q in x)y=y.replace(new RegExp("\\{"+q+"\\}","g"),String(x[q]));return y}async function a(){try{const $=e.currentClient||"",x="/api/exceptions/stats?status=pending"+($?"&client_id="+encodeURIComponent($):""),y=await fetch(x,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!y.ok)return;const q=await y.json(),z=document.getElementById("nav-exc-badge");if(!z)return;const Y=parseInt(q.pending||0,10);Y>0?(z.textContent=Y>99?"99+":String(Y),z.style.display=""):z.style.display="none"}catch{}}function o($){return $==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 1.5L1 12.5h12L7 1.5z"/>
                <line x1="7" y1="6" x2="7" y2="9"/>
                <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
            </svg>`:$==="medium"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="7" cy="7" r="5.5"/>
                <line x1="7" y1="4" x2="7" y2="7.5"/>
                <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
            </svg>`:`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="4.5" y1="7" x2="9.5" y2="7"/>
        </svg>`}function s(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function i($){if($==null)return"—";const x=parseFloat($);return isNaN(x)?"—":"฿ "+x.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function r($){return $?$.slice(0,10):"—"}function p($){document.getElementById("exc-kpi-pending").textContent=$.pending||0,document.getElementById("exc-kpi-high").textContent=$.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=$.resolved||0,document.getElementById("exc-kpi-learned").textContent=$.learned_rules||0;const x=document.getElementById("exc-status-tab-count-pending"),y=document.getElementById("exc-status-tab-count-resolved"),q=document.getElementById("exc-status-tab-count-ignored");x&&(x.textContent=$.pending||0),y&&(y.textContent=$.resolved||0),q&&(q.textContent=$.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(Y=>{Y.classList.toggle("active",Y.dataset.status===(e.currentStatus||"pending"))})}function l($){const x=document.getElementById("exc-chips");if(!x)return;const y=$.by_rule||{},q=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let Y=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${$.pending||0}</span>
        </button>`;for(const Z of q){const le=y[Z]||0;if(le===0&&e.currentRule!==Z)continue;const re=e.currentRule===Z;Y+=`<button class="exc-chip ${re?"active":""}" data-rule="${escapeHtml(Z)}">
                <span>${escapeHtml(t("exc-chip-"+Z))}</span>
                <span class="exc-chip-count">${le}</span>
            </button>`}x.innerHTML=Y,x.querySelectorAll(".exc-chip").forEach(Z=>{Z.addEventListener("click",()=>{const le=Z.dataset.rule||null;e.currentRule=le,w()})})}function d($){const x=document.getElementById("exc-list");if(!x)return;if(!$||$.length===0){x.innerHTML=`<div class="exc-empty">
                ${s()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,c();return}const y='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',q=(e.currentStatus||"pending")==="pending";x.innerHTML=$.map(z=>{const Y=z.severity||"medium",Z=t("exc-rule-"+z.rule_code)||z.rule_code,le=z.seller_name&&z.seller_name.trim()?z.seller_name:t("exc-no-seller"),re=z.filename||"—",K=r(z.invoice_date||z.created_at),ee=z.status==="pending",te=e.selectedIds.has(z.id),ne=q&&ee;return`
                <div class="exc-row sev-${escapeHtml(Y)} ${te?"selected":""}" data-exc-id="${escapeHtml(String(z.id))}">
                    <div class="exc-row-check ${te?"checked":""}" data-check-id="${escapeHtml(String(z.id))}" ${ne?"":'style="visibility:hidden;"'}>${y}</div>
                    <div class="exc-row-sev">${o(Y)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(le)} · ${escapeHtml(re)}</div>
                        <div class="exc-row-meta">
                            ${z.invoice_no?`<span><b>${escapeHtml(z.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(K)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(Y)}">${escapeHtml(Z)}</div>
                    <div class="exc-row-amount">${escapeHtml(i(z.total_amount))}</div>
                </div>
            `}).join(""),x.querySelectorAll(".exc-row").forEach(z=>{z.addEventListener("click",Y=>{if(Y.target.closest(".exc-row-check"))return;const Z=z.dataset.excId;Z&&L(parseInt(Z,10))})}),x.querySelectorAll(".exc-row-check").forEach(z=>{z.addEventListener("click",Y=>{Y.stopPropagation();const Z=parseInt(z.dataset.checkId,10);Z&&(e.selectedIds.has(Z)?(e.selectedIds.delete(Z),z.classList.remove("checked"),z.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(Z),z.classList.add("checked"),z.closest(".exc-row").classList.add("selected")),m())})}),m(),c()}function m(){const $=document.getElementById("exc-batch-bar"),x=document.getElementById("exc-batch-count");if(!$||!x)return;const y=e.selectedIds.size;y===0?$.style.display="none":($.style.display="",x.textContent=n("exc-batch-count",{n:y}))}function c(){const $=document.getElementById("exc-list-foot"),x=document.getElementById("exc-list-count"),y=document.getElementById("exc-loadmore");if(!$||!x||!y)return;const q=e.listCache.length;if(q===0){$.style.display="none";return}$.style.display="";let z=q;const Y=e.statsCache;Y&&(e.currentRule?z=(Y.by_rule||{})[e.currentRule]||q:z=Y.pending||q),e.total=z,x.textContent=n("exc-list-count",{shown:q,total:z});const Z=q<z&&q<500;y.style.display=Z?"":"none"}async function u(){try{if(navigator.onLine===!1)throw new Error("offline");const $=e.currentClient||"",x=e.currentStatus||"pending",y=new URLSearchParams;y.set("status",x),$&&y.set("client_id",$);const q="/api/exceptions/stats?"+y.toString(),z=await fetch(q,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!z.ok)throw new Error("http "+z.status);const Y=await z.json();return e.statsCache=Y,p(Y),l(Y),Y}catch($){return console.warn("loadExceptionsStats fail",$),null}}function f($){const x=document.getElementById("exc-list");if(!x)return;const y=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,q=$?t("exc-offline"):t("exc-error-retry-title"),z=$?"":t("exc-error-retry-desc");x.innerHTML=`
            <div class="exc-error">
                ${y}
                <div class="exc-error-msg">${escapeHtml(q)}${z?" · "+escapeHtml(z):""}</div>
                <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const Y=document.getElementById("exc-retry-btn");Y&&Y.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function w($){$=$||{};const x=!!$.append,y=document.getElementById("exc-list");!x&&y&&e.listCache.length===0&&(y.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const q=new URLSearchParams;q.set("status",e.currentStatus||"pending"),e.currentRule&&q.set("rule_code",e.currentRule),e.currentClient&&q.set("client_id",e.currentClient);const z=x?e.listCache.length:0;q.set("limit",String(e.pageSize)),q.set("offset",String(z));try{if(navigator.onLine===!1)throw new Error("offline");const Y=await fetch("/api/exceptions/list?"+q.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!Y.ok)throw new Error("http "+Y.status);const le=(await Y.json()).items||[];x?e.listCache=e.listCache.concat(le):(e.listCache=le,e.selectedIds.clear()),e.loadFailed=!1,d(e.listCache),e.statsCache&&l(e.statsCache)}catch(Y){console.warn("loadExceptionsList fail",Y),e.loadFailed=!0;const Z=navigator.onLine===!1||String(Y.message||"").includes("offline");x?showToast(t("exc-toast-load-fail"),"error"):(f(Z),showToast(Z?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function S(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await w({append:!0})}finally{e.loading=!1}}}function E(){const $=document.getElementById("exc-client-filter");if(!$)return;const x=window._clientsCache||[],y=e.currentClient||"",q=typeof t=="function"?t("history-client-all"):"全部客户";$.innerHTML=`<option value="">${escapeHtml(q)}</option>`+x.map(z=>`<option value="${z.id}">${escapeHtml(z.name)}</option>`).join(""),$.value=y}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{E(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await u(),await w()}finally{e.loading=!1}}},window.refreshExcBadge=a,window._refreshExcClientFilter=E,window._excState=e,window._rerenderExceptions=function(){try{E()}catch{}e.statsCache&&(p(e.statsCache),l(e.statsCache)),e.listCache&&e.listCache.length&&d(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}v.openExcId&&H()};let v={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function h(){if(v.pdfUrl){try{URL.revokeObjectURL(v.pdfUrl)}catch{}v.pdfUrl=null}v.pdfStatus="idle"}async function C($,x){v.pdfStatus="loading",H();try{const y=await fetch("/api/history/"+encodeURIComponent($)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(v.openExcId!==x)return;if(y.status===404){v.pdfStatus="empty",H();return}if(!y.ok)throw new Error("http "+y.status);const q=await y.blob();if(v.openExcId!==x)return;h(),v.pdfUrl=URL.createObjectURL(q),v.pdfStatus="ready",H()}catch(y){if(v.openExcId!==x)return;console.warn("loadDrawerPdf fail",y),v.pdfStatus="error",H()}}function L($){const x=(e.listCache||[]).find(y=>y.id===$);if(!x){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,h(),v.editing=!1,v.editFields=null,v.openExcId=$,v.excRow=x,v.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),H(),T(x.history_id),C(x.history_id,$)}function A(){h(),v.editing=!1,v.editFields=null,v.openExcId=null,v.excRow=null,v.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const $=e.listScrollY||0;$>0&&requestAnimationFrame(()=>window.scrollTo(0,$))}async function T($){try{const x=await fetch("/api/history/"+encodeURIComponent($),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!x.ok)throw new Error("http "+x.status);v.history=await x.json()}catch(x){console.warn("loadHistoryDetail fail",x),v.history={_err:!0}}v.excRow&&H()}function k($){if(!$||!$.pages)return{};const x=$.pages,y=x.find(q=>!q.is_duplicate&&!q.is_copy)||x[0];return y&&y.fields||{}}function g($){if($==null)return"—";const x=typeof $=="number"?$:parseFloat(String($).replace(/,/g,""));return isNaN(x)?escapeHtml(String($)):"฿ "+x.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function I($,x){if(x=x||{},$==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(g(x.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(g(x.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(g(x.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(g(x.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(g(x.diff))}</span></div>
            `;if($==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(x.tax_id_normalized||x.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(x.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if($==="duplicate"){const y=x.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(x.match_filename||"—")}</span></div>
                ${x.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(x.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(y)}</span></div>
            `}return $==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(x.confidence||"—")}</span></div>
            `:$==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(x))}</span></div>`}function H(){const $=v.excRow;if(!$)return;const x=$.seller_name&&$.seller_name.trim()?$.seller_name:t("exc-no-seller"),y=$.filename||"—";document.getElementById("exc-drawer-title").textContent=y;const q="exc-status-"+($.status||"pending"),z=t(q)||$.status,Y="s-"+($.status||"pending"),Z=($.invoice_date||$.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(x)}</span>
            ${$.invoice_no?`<span>· ${escapeHtml($.invoice_no)}</span>`:""}
            ${Z?`<span>· ${escapeHtml(Z)}</span>`:""}
            <span class="exc-status-chip ${Y}">${escapeHtml(z)}</span>
        `;const le=$.severity||"medium",re=t("exc-rule-"+$.rule_code)||$.rule_code,K=I($.rule_code,$.detail||{}),ee=k(v.history),te=v.history===null,ne=v.history&&v.history._err,se=new Set;$.rule_code==="math_mismatch"?(se.add("subtotal"),se.add("vat"),se.add("total_amount")):$.rule_code==="tax_id_format_invalid"?se.add("seller_tax"):$.rule_code==="amount_missing"&&(se.add("total_amount"),se.add("invoice_number"));const ue=!!v.editing,_=v.editFields||{},M=(ae,pe,fe)=>{if(te)return`<div class="exc-field-row"><label>${escapeHtml(t(pe))}</label><span class="val empty">…</span></div>`;const me=ue?_[ae]!==void 0?_[ae]:ee[ae]!==void 0&&ee[ae]!==null?ee[ae]:"":ee[ae],ge=se.has(ae)?"flagged":"";if(ue){const Ve=fe?"number":"text",Te=fe?' step="0.01" inputmode="decimal"':"",Ae=me==null?"":String(me).replace(/"/g,"&quot;");return`<div class="exc-field-row ${ge} editing">
                    <label>${escapeHtml(t(pe))}</label>
                    <input class="exc-field-input" type="${Ve}"${Te} data-edit-key="${escapeHtml(ae)}" value="${Ae}">
                </div>`}const be=fe?g(me):me||"",Ee=me==null||me===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(be)}</span>`;return`<div class="exc-field-row ${ge}"><label>${escapeHtml(t(pe))}</label>${Ee}</div>`};let j="";ne?j=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:j=`
                <div class="exc-fields">
                    ${M("invoice_number","exc-fld-invoice-no",!1)}
                    ${M("date","exc-fld-date",!1)}
                    ${M("seller_name","exc-fld-seller",!1)}
                    ${M("seller_tax","exc-fld-seller-tax",!1)}
                    ${M("buyer_name","exc-fld-buyer",!1)}
                    ${M("buyer_tax","exc-fld-buyer-tax",!1)}
                    ${M("subtotal","exc-fld-subtotal",!0)}
                    ${M("vat","exc-fld-vat",!0)}
                    ${M("total_amount","exc-fld-total",!0)}
                </div>
            `;const J=(()=>{if(v.pdfStatus==="loading"||v.pdfStatus==="idle")return`
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
                `;const ae=v.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(y)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${ae}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${ae}" download="${escapeHtml(y)}" title="${escapeHtml(t("exc-pdf-download"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                            </svg>
                        </a>
                    </div>
                </div>
                <iframe class="exc-pdf-frame" src="${ae}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
            `})();document.getElementById("exc-drawer-body").innerHTML=`
            <div class="exc-pdf-pane">${J}</div>
            <div class="exc-fields-pane">
                <div class="exc-section">
                    <div class="exc-section-title">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="7" cy="7" r="5.5"/><line x1="7" y1="4" x2="7" y2="7.5"/>
                            <circle cx="7" cy="9.6" r="0.5" fill="currentColor"/>
                        </svg>
                        <span>${escapeHtml(t("exc-sect-why"))}</span>
                    </div>
                    <div class="exc-why sev-${escapeHtml(le)}">
                        <div class="exc-why-rule">${escapeHtml(re)}</div>
                        <div class="exc-why-detail">${K}</div>
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
                        ${$.status==="pending"&&!te&&!ne?ue?`
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
                    ${j}
                </div>
            </div>
        `;const O=document.getElementById("exc-fld-edit");O&&O.addEventListener("click",()=>{v.editing=!0,v.editFields={...k(v.history)},H()});const b=document.getElementById("exc-fld-cancel");b&&b.addEventListener("click",()=>{v.editing=!1,v.editFields=null,H()});const N=document.getElementById("exc-fld-save");N&&N.addEventListener("click",()=>D()),document.querySelectorAll(".exc-field-input").forEach(ae=>{ae.addEventListener("input",()=>{v.editFields||(v.editFields={}),v.editFields[ae.dataset.editKey]=ae.value})});const W=document.getElementById("exc-pdf-retry");W&&v.openExcId&&W.addEventListener("click",()=>{v.excRow&&C(v.excRow.history_id,v.openExcId)});const X=$.status==="pending",de=!!($.seller_name&&$.seller_name.trim()),ie=document.getElementById("exc-btn-resolve"),ce=document.getElementById("exc-btn-ignore");ie.disabled=!X,ce.disabled=!X||!de,ce.title=de?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function D(){if(!v.openExcId||!v.history||!v.history.pages||v.loading)return;v.loading=!0;const $=showToast(t("exc-fld-saving"),"loading",0);try{const x=JSON.parse(JSON.stringify(v.history.pages||[]));let y=x.findIndex(re=>!re.is_duplicate&&!re.is_copy);y<0&&(y=0),x[y]||(x[y]={fields:{}});const q=x[y].fields||{},z=v.editFields||{},Y=new Set(["subtotal","vat","total_amount"]),Z={...q};for(const re in z){let K=z[re];if((K===""||K===void 0)&&(K=null),Y.has(re)&&K!==null){const ee=parseFloat(K);K=isNaN(ee)?null:ee}Z[re]=K}x[y].fields=Z;const le=await fetch("/api/history/"+encodeURIComponent(v.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:x})});if(!le.ok)throw new Error("http "+le.status);$(),showToast(t("exc-fld-save-ok"),"success"),A(),await u(),await w(),a()}catch(x){$(),console.warn("save fields fail",x),showToast(t("exc-fld-save-fail"),"error")}finally{v.loading=!1}}async function R(){if(!(!v.openExcId||v.loading)){v.loading=!0;try{const $=await fetch("/api/exceptions/"+v.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!$.ok)throw new Error("http "+$.status);showToast(t("exc-toast-resolved"),"success"),A(),await u(),await w(),a()}catch($){console.warn("resolve fail",$),showToast(t("exc-toast-action-fail"),"error")}finally{v.loading=!1}}}async function B(){if(!(!v.openExcId||v.loading)){v.loading=!0;try{const $=await fetch("/api/exceptions/"+v.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!$.ok)throw new Error("http "+$.status);showToast(t("exc-toast-ignored"),"success"),A(),await u(),await w(),a()}catch($){console.warn("ignore fail",$),showToast(t("exc-toast-action-fail"),"error")}finally{v.loading=!1}}}let P=!1;async function U(){if(P)return;const $=Array.from(e.selectedIds);if($.length===0||!await showConfirm(n("exc-batch-confirm-resolve",{n:$.length})))return;P=!0;const y=showToast(n("exc-batch-count",{n:$.length})+" …","loading",0);try{const q=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:$,action:"resolve"})});if(!q.ok)throw new Error("http "+q.status);const z=await q.json();y(),showToast(n("exc-toast-batch-resolved",{n:z.processed||0}),"success"),e.selectedIds.clear(),await u(),await w(),a()}catch(q){y(),console.warn("batch resolve fail",q),showToast(t("exc-toast-batch-fail"),"error")}finally{P=!1}}async function G(){if(P)return;const $=Array.from(e.selectedIds);if($.length===0||!await showConfirm(n("exc-batch-confirm-ignore",{n:$.length}),{danger:!1}))return;P=!0;const y=showToast(n("exc-batch-count",{n:$.length})+" …","loading",0);try{const q=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:$,action:"ignore"})});if(!q.ok)throw new Error("http "+q.status);const z=await q.json();y(),showToast(n("exc-toast-batch-ignored",{n:z.processed||0,wl:z.whitelist_added||0}),"success"),e.selectedIds.clear(),await u(),await w(),a()}catch(q){y(),console.warn("batch ignore fail",q),showToast(t("exc-toast-batch-fail"),"error")}finally{P=!1}}function F(){e.selectedIds.clear(),d(e.listCache)}document.addEventListener("click",$=>{$.target.closest("#exc-drawer-close")&&A(),$.target.closest("#exc-drawer-mask")&&A(),$.target.closest("#exc-btn-resolve")&&R(),$.target.closest("#exc-btn-ignore")&&B(),$.target.closest("#exc-batch-resolve")&&U(),$.target.closest("#exc-batch-ignore")&&G(),$.target.closest("#exc-batch-clear")&&F(),$.target.closest("#exc-loadmore")&&S()}),document.addEventListener("keydown",$=>{$.key==="Escape"&&v.openExcId&&A()}),document.addEventListener("click",$=>{$.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a())}),document.addEventListener("change",$=>{if(!$.target.closest("#exc-client-filter"))return;const x=$.target;e.currentClient=x.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a()}),document.addEventListener("click",$=>{const x=$.target.closest("#exc-status-tabs .exc-status-tab");if(!x)return;const y=x.dataset.status||"pending";y!==e.currentStatus&&(e.currentStatus=y,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(a,1500),setInterval(a,6e4);function Q($){if(!$)return"—";try{const x=new Date($),y=q=>String(q).padStart(2,"0");return`${x.getFullYear()}-${y(x.getMonth()+1)}-${y(x.getDate())} ${y(x.getHours())}:${y(x.getMinutes())}`}catch{return $.slice(0,16).replace("T"," ")}}async function oe(){const $=document.getElementById("learned-list");if($){$.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const x=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!x.ok)throw new Error("http "+x.status);const q=(await x.json()).items||[];if(q.length===0){$.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const z=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;$.innerHTML=q.map(Y=>{const Z=t("exc-rule-"+Y.rule_code)||Y.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(Y.id))}">
                        <div class="learned-seller" title="${escapeHtml(Y.seller_name)}">${escapeHtml(Y.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(Z)}</div>
                        <div class="learned-date">${escapeHtml(Q(Y.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(Y.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${z}</button>
                    </div>
                `}).join("")}catch(x){console.warn("loadLearnedRules fail",x),$.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=oe,document.addEventListener("click",async $=>{const x=$.target.closest("[data-del-wl]");if(!x)return;const y=parseInt(x.dataset.delWl,10);if(!y)return;const q=x.closest(".learned-row"),z=q&&q.querySelector(".learned-seller"),Y=z?z.textContent.trim():"",Z=t("set-learned-del-confirm").replace("{seller}",Y);if(await showConfirm(Z,{danger:!0}))try{const re=await fetch("/api/exception-whitelist/"+y,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!re.ok)throw new Error("http "+re.status);showToast(t("set-learned-del-ok"),"success"),oe(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(re){console.warn("delete whitelist fail",re),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",adapter:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(c){const u=typeof currentLang=="string"&&currentLang||window._currentLang||"th",f=c.error_friendly&&c.error_friendly[u];if(f)return f;if(typeof humanizeError=="function"&&c.error_msg)try{return humanizeError(c.error_msg)}catch{}return t("erp-exc-reason-"+(c.category||"other"))}function s(){const c=document.getElementById("erp-exc-batch");if(!c)return;const u=e.selected.size;c.hidden=u===0;const f=c.querySelector(".erp-exc-batch-count");f&&(f.textContent=String(u))}function i(){const c=document.getElementById("erp-exc-block");if(!c)return;const u=e;if(!(u.total>0||!!u.q||!!u.cat)){c.hidden=!0,c.innerHTML="";return}c.hidden=!1;const w=u.categories||{},S=Object.keys(w).reduce((F,Q)=>F+w[Q],0);let E=`<button class="erp-exc-chip ${u.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${S}</span></button>`;Object.keys(w).forEach(F=>{E+=`<button class="erp-exc-chip ${u.cat===F?"active":""}" data-erpexc-cat="${escapeHtml(F)}"><span>${escapeHtml(t("erp-exc-cat-"+F))}</span><span class="erp-exc-chip-count">${w[F]}</span></button>`});const v=u.items||[],h=v.length>0&&v.every(F=>u.selected.has(F.id)),C=v.map(F=>{const Q=F.state==="needs_action"?"needs":F.state==="retrying"?"retry":"fail",oe=t("erp-exc-state-"+(F.state||"failed")),$=o(F),x=u.selected.has(F.id)?"checked":"",y=F.push_type==="id_card",q=y?`<span class="erp-exc-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span> `:"",z=y?`<span class="ex-inv" title="${escapeHtml(t("erp-log-col-booking"))}">${q}${escapeHtml(F.invoice_no||"—")}</span>`:`<span class="ex-inv" title="${escapeHtml(F.invoice_no||"")}">${escapeHtml(F.invoice_no||"—")}</span>`,Y=y?`<span class="ex-seller" title="${escapeHtml(t("erp-log-col-customer"))}">${escapeHtml(F.seller_name||"—")}</span>`:`<span class="ex-seller" title="${escapeHtml(F.seller_name||"")}">${escapeHtml(F.seller_name||"—")}</span>`,Z=y?`<span class="ex-buyer" title="${escapeHtml(t("erp-log-col-idcard"))}">${F.id_card_tail?"••••"+escapeHtml(F.id_card_tail):"—"}</span>`:`<span class="ex-buyer" title="${escapeHtml(F.ocr_buyer_name||"")}">${escapeHtml(F.ocr_buyer_name||"—")}</span>`;return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(F.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(F.id)}" ${x}></span>
                ${z}
                ${Y}
                ${Z}
                <span class="ex-state"><span class="erp-exc-state ${Q}">${escapeHtml(oe)}</span></span>
                <span class="ex-reason" title="${escapeHtml($)}">${escapeHtml($)}${F.error_code?` <span class="erp-exc-code">${escapeHtml(F.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(F.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),L=v.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",A=v.length<u.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${v.length}/${u.total})</button>`:u.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:v.length,total:u.total}))}</div>`:"",T=u.adapter==="mrerp_dms",k=Array.isArray(window._erpEndpoints)?window._erpEndpoints:[],g=new Set;let I=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`;k.forEach(F=>{const Q=(F&&F.adapter||"").toLowerCase();!Q||g.has(Q)||(g.add(Q),I+=`<option value="${escapeHtml(Q)}"${Q===u.adapter?" selected":""}>${escapeHtml(F&&F.name||Q)}</option>`)});const H=T?t("erp-log-col-booking"):t("erp-exc-f-invoice"),D=T?t("erp-log-col-customer"):t("erp-exc-f-seller"),R=T?t("erp-log-col-idcard"):t("erp-exc-f-buyer");c.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${I}</select>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(u.q)}">
            </div>
            <div class="erp-exc-chips">${E}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${u.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${u.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${h?"checked":""}></span>
                    <span class="ex-inv">${escapeHtml(H)}</span>
                    <span class="ex-seller">${escapeHtml(D)}</span>
                    <span class="ex-buyer">${escapeHtml(R)}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${C}${L}
            </div>
            <div class="erp-exc-foot">${A}</div>`;const B=document.getElementById("erp-exc-search");if(B){if(u.focusSearch){B.focus();try{B.setSelectionRange(u.searchCaret,u.searchCaret)}catch{}}B.addEventListener("input",()=>{u.q=B.value,u.focusSearch=!0,u.searchCaret=B.selectionStart||B.value.length,clearTimeout(n),n=setTimeout(()=>l(!1),350)}),B.addEventListener("blur",()=>{u.focusSearch=!1})}c.querySelectorAll(".erp-exc-chip").forEach(F=>{F.addEventListener("click",()=>{u.cat=F.dataset.erpexcCat||"",l(!1)})});const P=document.getElementById("erp-exc-erp-select");P&&P.addEventListener("change",()=>{u.adapter=P.value||"",l(!1)}),c.querySelectorAll("[data-erpexc-retry]").forEach(F=>{F.addEventListener("click",Q=>{Q.stopPropagation(),r(F.dataset.erpexcRetry,F)})}),c.querySelectorAll(".erp-exc-cb").forEach(F=>{F.addEventListener("change",()=>{const Q=F.dataset.erpexcCb;F.checked?u.selected.add(Q):u.selected.delete(Q);const oe=document.getElementById("erp-exc-cb-all");oe&&(oe.checked=v.length>0&&v.every($=>u.selected.has($.id))),s()})});const U=document.getElementById("erp-exc-cb-all");U&&U.addEventListener("change",()=>{v.forEach(F=>{U.checked?u.selected.add(F.id):u.selected.delete(F.id)}),c.querySelectorAll(".erp-exc-cb").forEach(F=>{F.checked=U.checked}),s()}),c.querySelectorAll("[data-erpexc-batch]").forEach(F=>{F.addEventListener("click",()=>p(F.dataset.erpexcBatch))});const G=document.getElementById("erp-exc-more");G&&G.addEventListener("click",()=>l(!0)),c.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(F=>{F.addEventListener("click",Q=>{Q.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(F.dataset.erpexcId)})})}async function r(c,u){if(c){u&&(u.disabled=!0,u.textContent=t("erp-exc-retrying"));try{const f=await fetch("/api/erp/logs/"+encodeURIComponent(c)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),w=await f.json().catch(()=>({}));showToast(f.ok&&w.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),f.ok&&w.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(c),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function p(c){const u=Array.from(e.selected);if(c==="clear"){e.selected.clear(),i();return}if(u.length!==0){if(c==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:u.length}),{danger:!0}))return;try{const w=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,200)})}),S=await w.json().catch(()=>({}));showToast(w.ok?t("erp-exc-batch-delete-ok",{n:S.deleted||0}):t("erp-exc-retry-fail"),w.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(c==="retry")try{const f=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,50)})}),w=await f.json().catch(()=>({}));showToast(f.ok?t("erp-exc-batch-retry-ok",{ok:w.succeeded||0,fail:(w.failed||0)+(w.skipped||0)}):t("erp-exc-retry-fail"),f.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function l(c){const u=document.getElementById("erp-exc-block");if(!(!u||e.loading)){e.loading=!0;try{if(!Array.isArray(window._erpEndpoints)||!window._erpEndpoints.length)try{const v=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+a()}});if(v.ok){const h=await v.json();window._erpEndpoints=h&&(h.items||h)||[]}}catch{}const f=new URLSearchParams;e.q&&f.set("q",e.q),e.cat&&f.set("category",e.cat),e.adapter&&f.set("adapter",e.adapter),f.set("limit",String(e.pageSize)),f.set("offset",String(c?e.items.length:0));const w=await fetch("/api/erp/exceptions?"+f.toString(),{headers:{Authorization:"Bearer "+a()}});if(!w.ok){c||(u.hidden=!0);return}const S=await w.json(),E=S.items||[];e.items=c?e.items.concat(E):E,e.total=S.total||0,e.categories=S.categories||{},i()}catch{c||(u.hidden=!0)}finally{e.loading=!1}}}let d={};function m(){const c=document.getElementById("erp-exc-modal");c&&c.remove()}window._erpExcOpenEdit=function(c){const u=(e.items||[]).find(A=>String(A.id)===String(c));if(!u)return;const f=u.push_type==="id_card",w=!!u.history_client_id&&u.category==="customer_mismatch",S=u.category==="product_mismatch"&&!!u.history_id&&!!u.endpoint_id,E=o(u),v=u.state==="needs_action"?"needs":u.state==="retrying"?"retry":"fail",h=(A,T)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(A)}</span><span class="erp-exc-m-v">${escapeHtml(T||"—")}</span></div>`;let C="";if(w)C=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(S)C=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const A="erp-exc-edit-hint-"+(u.category||"other");let T=t(A);(!T||T===A)&&(T=E),C=`<div class="erp-exc-m-hint">${escapeHtml(T)}</div>`}const L=document.createElement("div");if(L.id="erp-exc-modal",L.className="erp-exc-modal-overlay",L.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${v}">${escapeHtml(t("erp-exc-state-"+(u.state||"failed")))}</span> ${escapeHtml(E)}${u.error_code&&!f?` <span class="erp-exc-code">${escapeHtml(u.error_code)}</span>`:""}</div>
                    ${h(f?t("erp-log-col-booking"):t("erp-exc-f-invoice"),u.invoice_no)}
                    ${h(f?t("erp-log-col-customer"):t("erp-exc-f-seller"),u.seller_name)}
                    ${f?h(t("erp-log-col-idcard"),u.id_card_tail?"••••"+u.id_card_tail:"—"):h(t("erp-exc-f-buyer"),u.ocr_buyer_name)+h(t("erp-exc-edit-field-current"),u.client_name)}
                    ${C}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${w?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${S?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(L),L.addEventListener("click",A=>{A.target===L&&m()}),document.getElementById("erp-exc-m-close").addEventListener("click",m),document.getElementById("erp-exc-m-cancel").addEventListener("click",m),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{m(),r(u.id,null)}),w){let A="";const T=document.getElementById("erp-exc-m-bind"),k=document.getElementById("erp-exc-m-custlist"),g=document.getElementById("erp-exc-m-search"),I=(D,R)=>{const B=(R||"").trim().toLowerCase(),P=B?D.filter(U=>(U.code||"").toLowerCase().includes(B)||(U.name||"").toLowerCase().includes(B)):D;if(P.length===0){k.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}k.innerHTML=P.slice(0,100).map(U=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(U.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(U.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(U.code||"")}</span>
                    </div>`).join(""),k.querySelectorAll(".erp-exc-m-cust").forEach(U=>{U.addEventListener("click",()=>{A=U.dataset.custCode||"",k.querySelectorAll(".erp-exc-m-cust").forEach(G=>G.classList.remove("sel")),U.classList.add("sel"),T&&(T.disabled=!A)})})},H=async()=>{const D=u.endpoint_id;if(d[D]){I(d[D],"");return}try{const R=await fetch("/api/erp/endpoints/"+encodeURIComponent(D)+"/customers",{headers:{Authorization:"Bearer "+a()}}),B=await R.json().catch(()=>({}));if(!R.ok||!B.ok){k.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const P=B.customers||[];d[D]=P,I(P,"")}catch{k.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};g&&g.addEventListener("input",()=>I(d[u.endpoint_id]||[],g.value)),H(),T&&T.addEventListener("click",async()=>{if(A){T.disabled=!0,T.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:u.history_client_id,erp_type:u.endpoint_adapter,erp_code:A})})).ok){showToast(t("erp-exc-retry-fail"),"error"),T.disabled=!1,T.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),m(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),T.disabled=!1,T.textContent=t("erp-exc-edit-bind-retry")}}})}if(S){const A=document.getElementById("erp-exc-m-bind-prod"),T=document.getElementById("erp-exc-m-prodlist"),k={};let g=[];const I=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+g.slice(0,500).map(R=>`<option value="${escapeHtml(R.code||"")}" data-pname="${escapeHtml(R.name||"")}">`+escapeHtml((R.name||"")+" · "+(R.code||""))+"</option>").join(""),H=R=>{if(!R.length){T.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}T.innerHTML=R.map(B=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(B)}">${escapeHtml(B)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(B)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${I()}</select>
                    </div>`).join(""),T.querySelectorAll(".erp-exc-m-prod-sel").forEach(B=>{B.addEventListener("change",()=>{const P=B.dataset.item,U=B.options[B.selectedIndex];B.value?k[P]={code:B.value,name:U&&U.dataset.pname||""}:delete k[P],A&&(A.disabled=Object.keys(k).length===0)})})};(async()=>{try{const B=await(await fetch("/api/history/"+encodeURIComponent(u.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),P=B&&B.pages||[],U=[],G={};(Array.isArray(P)?P:[]).forEach(oe=>{const $=oe&&oe.fields&&oe.fields.items||[];(Array.isArray($)?$:[]).forEach(x=>{const y=(x&&(x.name||x.description)||"").trim();y&&!G[y]&&(G[y]=1,U.push(y))})});const F=await fetch("/api/erp/endpoints/"+encodeURIComponent(u.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),Q=await F.json().catch(()=>({}));if(!F.ok||!Q.ok){T.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}g=Q.products||[],H(U)}catch{T.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),A&&A.addEventListener("click",async()=>{const R=Object.entries(k);if(R.length){A.disabled=!0,A.textContent=t("erp-exc-retrying");try{for(const[B,P]of R)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:u.endpoint_adapter,item_name:B,erp_code:P.code,erp_name:P.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),A.disabled=!1,A.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),m(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),A.disabled=!1,A.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=i,window.loadErpExceptions=l,window._erpExcState=e})();const Qa=`
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
`;ke("cmdk-mask",Qa);(function(){function e(c){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||c&&c.id&&String(c.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var u=window._userInfo,f=!1,w=!0,S=!1,E=!1;u&&(f=typeof canManageTeam=="function"?canManageTeam(u):!!(u.role==="owner"||u.is_super_admin),w=typeof shouldHideMoney=="function"?shouldHideMoney(u):u.role==="member"&&!u.is_super_admin,S=typeof isSuperAdmin=="function"?isSuperAdmin(u):!!u.is_super_admin,E=e(u)),document.querySelectorAll("[data-show-if-team]").forEach(function(h){h.style.display=f?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(h){h.style.display=w?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(h){h.style.display=S?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(h){h.style.display=E?"":"none"});var v=S||E;document.querySelectorAll("[data-show-if-special]").forEach(function(h){h.style.display=v?"":"none"})},window.renderAvatarMenu=function(u){if(u){var f=document.getElementById("avatar-btn"),w=document.getElementById("avatar-popup-name"),S=document.getElementById("avatar-popup-email");if(!(!f||!w||!S)){var E=(u.username||"").trim(),v=E.split("@")[0]||E||"—",h=(E.charAt(0)||"?").toUpperCase(),C=(u.avatar_url||"").trim();if(C){var L=C.replace(/"/g,"&quot;"),A=h.replace(/'/g,"\\'");f.innerHTML='<img src="'+L+'" alt="'+h+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+A+`'">`}else f.textContent=h;w.textContent=v,S.textContent=E||"—",f.setAttribute("title",E||"")}}};function n(){var c=document.getElementById("avatar-wrap"),u=document.getElementById("avatar-btn"),f=document.getElementById("avatar-popup");if(!c||!u||!f)return;function w(){f.classList.remove("show"),u.setAttribute("aria-expanded","false")}function S(){f.classList.add("show"),u.setAttribute("aria-expanded","true")}u.addEventListener("click",function(E){E.stopPropagation(),f.classList.contains("show")?w():S()}),document.addEventListener("click",function(E){f.classList.contains("show")&&!c.contains(E.target)&&w()}),f.addEventListener("click",function(E){var v=E.target.closest(".avatar-popup-item");if(v){var h=v.dataset.action;switch(w(),h){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var C=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(C||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var L=document.getElementById("help-modal");L&&(L.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=w}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(c){return c.style.display!=="none"})}function o(c){var u=a();u.forEach(function(f){f.classList.remove("focus")}),u[c]&&(u[c].classList.add("focus"),u[c].scrollIntoView({block:"nearest"}))}function s(c){var u=a();if(u.length){var f=u.findIndex(function(S){return S.classList.contains("focus")});f<0&&(f=0);var w=(f+c+u.length)%u.length;o(w)}}function i(c){c=(c||"").toLowerCase().trim();var u=0,f=window._userInfo,w=typeof isSuperAdmin=="function"?isSuperAdmin(f):!!(f&&f.is_super_admin),S=e(f);document.querySelectorAll(".cmdk-item").forEach(function(v){if(v.dataset.showIfAdmin==="1"&&!w){v.style.display="none";return}if(v.dataset.showIfTest==="1"&&!S){v.style.display="none";return}var h=(v.dataset.cmdkText||v.textContent||"").toLowerCase(),C=!c||h.indexOf(c)>=0;v.style.display=C?"":"none",v.classList.remove("focus"),C&&u++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(v){for(var h=v.nextElementSibling,C=!1;h&&!h.hasAttribute("data-cmdk-section");){if(h.classList&&h.classList.contains("cmdk-item")&&h.style.display!=="none"){C=!0;break}h=h.nextElementSibling}v.style.display=C?"":"none"});var E=document.getElementById("cmdk-empty");E&&(E.style.display=u===0?"flex":"none"),o(0)}window.openCmdk=function(){var u=document.getElementById("cmdk-mask");u&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),u.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var f=document.getElementById("cmdk-input");f&&(f.value="",i(""),f.focus(),o(0))},50))},window.closeCmdk=function(){var u=document.getElementById("cmdk-mask");u&&u.classList.remove("show")};function r(c){if(c){if(c.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var u=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(u||"即将上线","info")}return}var f=c.dataset.cmdkRoute,w=c.dataset.cmdkAction;if(window.closeCmdk(),f){typeof routeTo=="function"&&routeTo(f);return}if(w){if(w==="open-admin"){window.location.href="/admin/cost";return}if(w.indexOf("lang-")===0){var S=w.slice(5);typeof applyLang=="function"&&applyLang(S)}}}}function p(){var c=document.getElementById("cmdk-mask"),u=document.getElementById("cmdk-input"),f=document.getElementById("cmdk-body");if(!(!c||!u||!f)){c.addEventListener("click",function(E){E.target===c&&window.closeCmdk()});var w=document.getElementById("cmdk-esc-btn");w&&w.addEventListener("click",function(){window.closeCmdk()}),u.addEventListener("input",function(E){i(E.target.value)}),u.addEventListener("keydown",function(E){E.key==="ArrowDown"?(E.preventDefault(),s(1)):E.key==="ArrowUp"?(E.preventDefault(),s(-1)):E.key==="Enter"?(E.preventDefault(),r(c.querySelector(".cmdk-item.focus"))):E.key==="Escape"&&(E.preventDefault(),window.closeCmdk())}),f.addEventListener("click",function(E){var v=E.target.closest(".cmdk-item");v&&r(v)}),f.addEventListener("mousemove",function(E){var v=E.target.closest(".cmdk-item");!v||v.style.display==="none"||v.classList.contains("cmdk-item-locked")||(a().forEach(function(h){h.classList.remove("focus")}),v.classList.add("focus"))});var S=document.getElementById("topbar-search");S&&(S.addEventListener("click",function(){window.openCmdk()}),S.addEventListener("keydown",function(E){(E.key==="Enter"||E.key===" ")&&(E.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(c){if((c.metaKey||c.ctrlKey)&&(c.key==="k"||c.key==="K")){c.preventDefault(),window.openCmdk();return}if(c.key==="Escape"){var u=document.getElementById("cmdk-mask");if(u&&u.classList.contains("show")){window.closeCmdk();return}var f=document.getElementById("avatar-popup");f&&f.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var l=(navigator.userAgent||"").toLowerCase(),d=l.indexOf("mac")>=0||l.indexOf("iphone")>=0||l.indexOf("ipad")>=0;d||document.body.classList.add("is-windows")}catch{}function m(){n(),p(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",m):m()})();(function(){function n(w){return String(w??"").replace(/[&<>"']/g,function(S){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[S]})}function a(w){if(!w||isNaN(w))return"";var S=Number(w);return S<1024?S+" B":S<1024*1024?(S/1024).toFixed(1)+" KB":(S/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(w){var S=w.target.closest&&w.target.closest(".recon-collapse-head");if(S&&!(w.target.closest("button")||w.target.closest("a"))){var E=S.closest(".recon-collapse");if(E){var v=E.getAttribute("data-collapsed")==="true";E.setAttribute("data-collapsed",v?"false":"true"),v&&(E.id==="vex-summary-collapse"&&m(),E.id==="vex-detail-collapse"&&c())}}}),document.addEventListener("keydown",function(w){if(!(w.key!=="Enter"&&w.key!==" ")){var S=w.target.closest&&w.target.closest(".recon-collapse-head");S&&(w.preventDefault(),S.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){l("vat"),l("gl")}function p(w){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(w)||[]}catch{}var S=document.getElementById(w==="vat"?"glv-vat-input":"glv-gl-input");return S&&S.files?Array.from(S.files):[]}function l(w){var S=document.getElementById(w==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(S){var E=p(w),v=w==="vat"?"glv-up-vat-title":"glv-up-gl-title",h=w==="vat"?"① 销项税报告":"② 总账 GL",C=window.t&&window.t(v)||h,L=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),A=n(window.t&&window.t("vex-preview-clear-all")||"全清"),T=o[w]||"",k=E.length;S.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(C)+' <span class="vex-pp-col-count">'+k+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+w+'" type="text" placeholder="'+L+'" value="'+n(T)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+w+'" type="button">'+A+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+w+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+w+'-pg"></div>';var g=document.getElementById("glv-pp-search-"+w);g&&g.addEventListener("input",function(H){o[w]=H.target.value,d(w)});var I=document.getElementById("glv-pp-clearall-"+w);I&&I.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(w)}),d(w)}}function d(w){var S=document.getElementById("glv-pp-"+w+"-list"),E=document.getElementById("glv-pp-"+w+"-pg");if(S){var v=p(w),h=(o[w]||"").toLowerCase(),C=v.map(function(T,k){return{f:T,i:k}}),L=h?C.filter(function(T){return T.f.name.toLowerCase().indexOf(h)>=0}):C;if(S.innerHTML=L.map(function(T){var k=T.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(k.name)+'">'+n(k.name)+'</span><span class="vex-pp-fi-size">'+a(k.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+w+'" data-idx="'+T.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),S.querySelectorAll(".vex-pp-fi-del").forEach(function(T){T.addEventListener("click",function(){var k=T.dataset.kind,g=parseInt(T.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(k,isNaN(g)?null:g)})}),E){var A=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";E.textContent=A.replace("{n}",L.length).replace("{m}",L.length)}}}function m(){var w=function(E,v){var h=document.getElementById(E);h&&(h.textContent=v==null?"—":String(v))},S=window._vexLastTask||{};w("vex-sum-total",S.total),w("vex-sum-matched",S.matched),w("vex-sum-diff",S.diff),w("vex-sum-incomplete",S.incomplete),w("vex-sum-cash",S.cash),document.getElementById("vex-summary-sub")}function c(){var w=window._vexLastTask&&window._vexLastTask.diff_rows||[],S=document.getElementById("vex-detail-tbody"),E=document.getElementById("vex-detail-table"),v=document.getElementById("vex-detail-empty");if(!(!S||!E||!v)){if(w.length===0){E.style.display="none",v.style.display="";return}v.style.display="none",E.style.display="";var h=w.map(function(L){return'<tr><td class="recon-detail-cell-mono">'+n(L.invoice_no||"")+"</td><td>"+n(L.field||"")+"</td><td>"+n(L.report_value||"")+"</td><td>"+n(L.invoice_value||"")+"</td><td>"+n(L.kind||"")+"</td></tr>"}).join("");S.innerHTML=h;var C=document.getElementById("vex-detail-sub");C&&(C.textContent=String(w.length))}}function u(){var w=document.getElementById("glv-toggle-preview");w&&!w._reconBound&&(w._reconBound=!0,w.addEventListener("click",function(){var S=document.getElementById("glv-preview-panel"),E=document.getElementById("glv-toggle-preview-label"),v=S&&S.style.display!=="none";S&&(S.style.display=v?"none":""),w.classList.toggle("open",!v),E&&(E.textContent=v?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),v||r()})),["glv-vat-input","glv-gl-input"].forEach(function(S){var E=document.getElementById(S);!E||E._reconWatched||(E._reconWatched=!0,E.addEventListener("change",function(){var v=document.getElementById("glv-preview-panel");v&&v.style.display!=="none"&&r()}))})}function f(){var w=document.getElementById("vex-summary-collapse"),S=document.getElementById("vex-detail-collapse");w&&(w.style.display=""),S&&(S.style.display=""),m(),c()}window._fillVexSummary=m,window._fillVexDetail=c,window._onVexResultShown=f,document.addEventListener("DOMContentLoaded",function(){u()}),setTimeout(u,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var w=document.getElementById("glv-preview-panel");w&&w.style.display!=="none"&&r();var S=document.getElementById("glv-toggle-preview-label"),E=document.getElementById("glv-toggle-preview");S&&E&&(S.textContent=E.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:m,fillVexDetail:c}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(p=>{p.addEventListener("click",()=>{i.forEach(u=>u.classList.remove("active")),p.classList.add("active");const l=p.dataset.reconTab,d=document.getElementById("recon-pane-bank"),m=document.getElementById("recon-pane-sale-vat"),c=document.getElementById("recon-pane-gl-vat");d&&(d.style.display=l==="bank"?"":"none"),m&&(m.style.display=l==="sale-vat"?"":"none"),c&&(c.style.display=l==="gl-vat"?"":"none"),l==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),l==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const p=document.createElement("button");return p.id="settings-modal-close",p.className="settings-modal-close",p.setAttribute("aria-label","close"),p.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(p,i.firstChild),p.addEventListener("click",s),r.addEventListener("click",l=>{l.target===r&&s()}),r}function o(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(l){console.warn("renderSettings:",l)}let p=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');p&&p.click()},50)}function s(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=K=>document.getElementById(K);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function i(K){return String(K??"").replace(/[&<>"']/g,ee=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[ee])}function r(K){return K<1024?K+" B":K<1024*1024?(K/1024).toFixed(1)+" KB":(K/1024/1024).toFixed(1)+" MB"}let p=[],l=[],d=!1,m=[],c=50,u=50,f="",w="";async function S(){try{const K=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!K.ok)return;const te=(await K.json()).kpi||{};[["vex-kpi-month-val",te.this_month],["vex-kpi-running-val",te.running],["vex-kpi-done-val",te.done],["vex-kpi-failed-val",te.failed]].forEach(([ne,se])=>{const ue=document.getElementById(ne);ue&&(ue.textContent=se??0)})}catch{}}async function E(){try{const K=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!K.ok)return;const ee=await K.json();L(ee.rows||[])}catch{}}const v=10;var h=1;function C(){var K=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(h=1,L(m),!!K){var ee=document.getElementById("vex-task-tbody");ee&&ee.querySelectorAll("tr").forEach(function(te){te.dataset.taskId&&(te.style.display=te.textContent.toLowerCase().indexOf(K)>=0?"":"none")})}}function L(K){m=K||m;const ee=document.getElementById("vex-task-tbody");if(!ee)return;if(!m.length){ee.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",A(0);return}const te=Math.ceil(m.length/v);h>te&&(h=te);const ne=(h-1)*v;T(m.slice(ne,ne+v)),A(m.length)}function A(K){const ee=document.getElementById("vex-task-pager"),te=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),se=document.getElementById("vex-task-next");if(!ee)return;if(K<=v){ee.style.display="none";return}ee.style.display="";const ue=Math.ceil(K/v);te&&(te.textContent=h+" / "+ue),ne&&(ne.disabled=h<=1),se&&(se.disabled=h>=ue)}function T(K){const ee=document.getElementById("vex-task-tbody");if(!ee)return;const te={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ue='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';ee.innerHTML=K.map(_=>{const M=_.created_at?new Date(_.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",j=_.period||"—",J=_.matched_count!=null?_.matched_count+" ✓ · "+_.mismatched_count+" ⚠":"—",O=_.mismatch_amount!=null?"฿ "+Number(_.mismatch_amount).toLocaleString():"—",b=_.elapsed_seconds!=null?_.elapsed_seconds.toFixed(1)+" s":"—",N=_.status||"pending",V=_.client_name&&_.client_name!=="client"?_.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${i(_.id)}" style="cursor:pointer">
                <td>${M}</td>
                <td>${i(V)}</td>
                <td>${i(j)}</td>
                <td>${(_.invoice_count||0)+" / "+(_.report_count||0)}</td>
                <td>${J}</td>
                <td>${O}</td>
                <td><span class="badge ${ne[N]||"badge-gray"}">${te[N]||N}</span></td>
                <td>${b}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${i(_.id)}" title="${t("hist_export")||"导出"}">${se}</button>
                    <button class="vex-task-del-btn" data-task-id="${i(_.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ue}</button>
                </div></td>
            </tr>`}).join(""),ee.querySelectorAll(".vex-task-dl-btn").forEach(_=>{_.addEventListener("click",async M=>{M.stopPropagation();const j=_.dataset.taskId;try{const J=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(j)+"/download",{credentials:"include",headers:s()});if(J.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!J.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const O=await J.blob(),N=(J.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),V=N?decodeURIComponent(N[1]):"vat_recon_"+j+".xlsx",W=URL.createObjectURL(O),X=document.createElement("a");X.href=W,X.download=V,X.click(),setTimeout(()=>URL.revokeObjectURL(W),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),ee.querySelectorAll(".vex-task-del-btn").forEach(_=>{_.addEventListener("click",M=>{M.stopPropagation(),g(_.dataset.taskId)})}),C()}function k(){var K=document.getElementById("vex-task-prev"),ee=document.getElementById("vex-task-next");K&&!K._vexBound&&(K._vexBound=!0,K.addEventListener("click",function(){h>1&&(h--,L())})),ee&&!ee._vexBound&&(ee._vexBound=!0,ee.addEventListener("click",function(){var te=Math.ceil(m.length/v);h<te&&(h++,L())}))}async function g(K){const ee=t("vex-task-delete-confirm-title")||"删除对账任务?",te=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(te,{title:ee,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const se=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(K),{method:"DELETE",credentials:"include",headers:s()});if(!se.ok)throw new Error(se.status);showToast(t("vex-task-delete-ok")||"已删除","success"),E(),S()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function I(K){const ee=window._currentLang||"th",te={zh:`已忽略 ${K} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${K} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${K} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${K} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(te[ee]||te.th,"warn")}function H(K){const ee=new Set(p.map(ne=>ne.name+"|"+ne.size));let te=0;for(const ne of K){if(!a.test(ne.name)){te++;continue}const se=ne.name+"|"+ne.size;if(!ee.has(se)&&(ee.add(se),p.push(ne),p.length>=1e3))break}te>0&&I(te),p.length>1e3&&(p=p.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),P()}function D(K){const ee=new Set(l.map(ne=>ne.name+"|"+ne.size));let te=0;for(const ne of K){if(!a.test(ne.name)){te++;continue}const se=ne.name+"|"+ne.size;if(!ee.has(se)&&(ee.add(se),l.push(ne),l.length>=30))break}te>0&&I(te),l.length>30&&(l=l.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),P()}function R(K){p.splice(K,1),P()}function B(K){l.splice(K,1),P()}function P(){const K=o("vex-list-invoice"),ee=o("vex-list-report"),te=o("vex-count-invoice"),ne=o("vex-count-report");te&&(te.textContent=p.length),ne&&(ne.textContent=l.length);const se=(M,j,J)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${i(M.name)}">${i(M.name)}</span>
            <span class="vex-fi-s">${r(M.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${J}" data-vex-idx="${j}" aria-label="remove">×</button>
        </div>`;K&&(K.innerHTML=p.map((M,j)=>se(M,j,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),ee&&(ee.innerHTML=l.map((M,j)=>se(M,j,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(M=>{M.addEventListener("click",j=>{const J=M.dataset.vexKind,O=parseInt(M.dataset.vexIdx,10);J==="inv"?R(O):B(O)})});const ue=p.length>0&&l.length>0;o("vex-build").disabled=!ue||d;const _=o("vex-action-info");_&&(!p.length||!l.length?(_.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",_.className="vex-action-info muted"):(_.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",p.length).replace("{b}",l.length),_.className="vex-action-info ok")),Q()}const U='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',G='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',F='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function Q(){const K=o("vex-preview-panel");if(!K||K.style.display==="none")return;oe("inv"),oe("rep");const ee=o("vex-pp-guide");ee&&(ee.style.display=p.length>100?"flex":"none")}function oe(K){const ee=o(K==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!ee)return;const te=K==="inv"?p:l,ne=K==="inv"?f:w,se=t(K==="inv"?"vex-preview-invoice":"vex-preview-report")||(K==="inv"?"销售发票":"VAT 报告"),ue=i(t("vex-preview-search")||"搜索文件名..."),_=i(t("vex-preview-clear-all")||"全清");ee.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${i(se)} <span class="vex-pp-col-count">${te.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${K}" type="text"
                       placeholder="${ue}" value="${i(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${K}" type="button">${_}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${K}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${K}-pg"></div>`;const M=o("vex-pp-search-"+K);M&&M.addEventListener("input",J=>{K==="inv"?(f=J.target.value,c=50):(w=J.target.value,u=50),$(K)});const j=o("vex-pp-clearall-"+K);j&&j.addEventListener("click",()=>{K==="inv"?(p=[],f="",c=50):(l=[],w="",u=50),P()}),$(K)}function $(K){const ee=o("vex-pp-"+K+"-list"),te=o("vex-pp-"+K+"-pg");if(!ee)return;const ne=K==="inv"?p:l,se=K==="inv"?f:w,ue=K==="inv"?c:u,_=K==="inv"?U:G,M=ne.map((O,b)=>({f:O,i:b})),j=se?M.filter(({f:O})=>O.name.toLowerCase().includes(se.toLowerCase())):M,J=j.slice(0,ue);if(ee.innerHTML=J.map(({f:O,i:b})=>`
            <div class="vex-pp-file-row">
                ${_}
                <span class="vex-pp-fi-name" title="${i(O.name)}">${i(O.name)}</span>
                <span class="vex-pp-fi-size">${r(O.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${K}" data-ridx="${b}" aria-label="remove">${F}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${K}" style="height:1px;flex-shrink:0"></div>`,ee.querySelectorAll(".vex-pp-fi-del").forEach(O=>{O.addEventListener("click",()=>{const b=parseInt(O.dataset.ridx,10);O.dataset.kind==="inv"?R(b):B(b)})}),te){const O=t("vex-preview-count")||"显示前 {n} / 共 {m}";te.textContent=O.replace("{n}",J.length).replace("{m}",j.length)}x(K,j.length)}function x(K,ee){if((K==="inv"?c:u)>=ee)return;const ne=o("vex-pp-sentinel-"+K),se=o("vex-pp-"+K+"-list");if(!ne||!se)return;const ue=new IntersectionObserver(_=>{_[0].isIntersecting&&(ue.disconnect(),K==="inv"?c+=50:u+=50,$(K))},{root:se,threshold:.8});ue.observe(ne)}function y(K,ee,te,ne){const se=o(K),ue=o(ee);!se||!ue||(se.addEventListener("click",()=>ue.click()),se.addEventListener("keydown",_=>{(_.key==="Enter"||_.key===" ")&&(_.preventDefault(),ue.click())}),se.addEventListener("dragover",_=>{_.preventDefault(),se.classList.add("drag-over")}),se.addEventListener("dragleave",()=>se.classList.remove("drag-over")),se.addEventListener("drop",_=>{_.preventDefault(),se.classList.remove("drag-over");const j=Array.from(_.dataTransfer.files).filter(J=>a.test(J.name));if(!j.length){showToast(t("vex-toast-bad-ext"),"error");return}te(j)}),ue.addEventListener("change",()=>{const _=Array.from(ue.files);te(_),ue.value=""}))}async function q(){if(d||!p.length||!l.length)return;d=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var K=document.getElementById("vex-download");K&&(K.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(se){var ue=document.getElementById(se);ue&&(ue.style.display="none")});const ee=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",p.length).replace("{b}",l.length);const te=setInterval(()=>{const se=Math.floor((Date.now()-ee)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",se).replace("{a}",p.length).replace("{b}",l.length)},1e3);try{const se=new FormData;for(const pe of p)se.append("invoices",pe);for(const pe of l)se.append("reports",pe);const ue=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";se.append("lang",ue);const _=localStorage.getItem("mrpilot_token")||"",M=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:se});let j=null;try{j=await M.json()}catch{j=null}if(!M.ok||!j||!j.ok||!j.job_id)throw clearInterval(te),new Error(j&&j.detail||"HTTP "+M.status);const J=o("vex-progress-sub"),O=await window._reconPollJob(j.job_id,_,{onProgress:pe=>{J&&(J.textContent=window._reconProgressText(pe,ue))}});if(clearInterval(te),!O||O.status!=="done"||!O.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const b=O.result_id;let N=0;const V=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(b)+"/download",{headers:s()});if(!V.ok)throw new Error("HTTP "+V.status);const X=(V.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),de=X&&X[1]||"vat_recon_"+Date.now()+".xlsx",ie=await V.blob(),ce=URL.createObjectURL(ie),ae=o("vex-download");ae.href=ce,ae.download=de;try{const pe=document.createElement("a");pe.href=ce,pe.download=de,document.body.appendChild(pe),pe.click(),setTimeout(()=>pe.remove(),100)}catch{}o("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),b&&(N=await Z(b)),window._onVexResultShown&&window._onVexResultShown(),N>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",N),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),S(),setTimeout(E,800)}catch(se){clearInterval(te),o("vex-progress").style.display="none";const ue=(t("vex-toast-fail")||"生成失败")+": "+(se.message||se);showToast(ue,"error")}finally{d=!1,o("vex-build").disabled=!1}}function z(){p=[],l=[];var K=document.getElementById("vex-download");K&&(K.style.display="none"),P()}function Y(K){if(K==null)return"—";var ee=parseFloat(K);return isNaN(ee)?"—":ee.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function Z(K){try{var ee=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(K),{headers:s()});if(!ee.ok)throw new Error(ee.status);var te=await ee.json(),ne=te.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var se=ne.rows||[],ue=[];se.forEach(function(j){j.kind==="invoice_orphan"?ue.push({invoice_no:j.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:Y(j.amount_inv),kind:j.kind}):j.kind==="report_orphan"?ue.push({invoice_no:j.invoice_no||"",field:"仅报告有",report_value:Y(j.amount_rep),invoice_value:"—",kind:j.kind}):j.dims&&Object.keys(j.dims).length>0&&Object.keys(j.dims).forEach(function(J){var O=String(j.dims[J]||""),b=O.split(" ≠ ");ue.push({invoice_no:j.invoice_no||"",field:J,report_value:b[0]||O,invoice_value:b.length>1?b[1]:"—",kind:"diff"})})});var _=se.filter(function(j){return j.kind==="matched_cash"}).length,M=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:M,cash:_,diff_rows:ue,task_id:K},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),M}catch{return 0}}function le(){const K=document.getElementById("vex-pane");K&&K.querySelectorAll("[data-i18n]").forEach(ee=>{const te=t(ee.dataset.i18n);te&&(ee.textContent=te)}),P(),E()}function re(){y("vex-drop-invoice","vex-input-invoice",H),y("vex-drop-report","vex-input-report",D);const K=o("vex-build"),ee=o("vex-reset");K&&K.addEventListener("click",q),ee&&ee.addEventListener("click",z),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(se=>{se.addEventListener("click",()=>{S(),E()})}),k();const te=document.getElementById("vex-task-search");te&&te.addEventListener("input",C);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const se=o("vex-preview-panel"),ue=o("vex-toggle-preview-label"),_=se&&se.style.display!=="none";se&&(se.style.display=_?"none":""),ne&&ne.classList.toggle("open",!_),ue&&(ue.textContent=_?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),_||Q()}),P(),S()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",re):re(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",le),window.subscribeI18n("vex-preview-panel",Q))})();(function(){const e=x=>document.getElementById(x),n=()=>localStorage.getItem("mrpilot_token")||"",a=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",o=()=>({Authorization:"Bearer "+n()}),s={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},i={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},r=x=>(i[a()]||i.th)[x]||x;function p(x){const y=a(),z={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[x];return z?z[y]||z.th||z.en:r("error")||"Error"}const l=x=>x==null||isNaN(x)?"":Number(x).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function d(x,y,q,z){const Y=e(x),Z=e(y),le=e(q);if(!Y||!Z||!le)return;const re=K=>{if(!K||!K.length)return;const ee=Array.isArray(s[z])?s[z].slice():[],te=new Set(ee.map(ne=>ne.name+"|"+ne.size));for(const ne of K){if(!ne)continue;const se=ne.name+"|"+ne.size;te.has(se)||(ee.push(ne),te.add(se))}s[z]=ee,m(le,ee),u(),f(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};Y.addEventListener("click",()=>Z.click()),Y.addEventListener("keydown",K=>{(K.key==="Enter"||K.key===" ")&&(K.preventDefault(),Z.click())}),Z.addEventListener("change",()=>{re(Array.from(Z.files||[])),Z.value=""}),Y.addEventListener("dragover",K=>{K.preventDefault(),Y.classList.add("drag-over")}),Y.addEventListener("dragleave",()=>Y.classList.remove("drag-over")),Y.addEventListener("drop",K=>{K.preventDefault(),Y.classList.remove("drag-over");const ee=K.dataTransfer&&K.dataTransfer.files?Array.from(K.dataTransfer.files):[];re(ee)})}function m(x,y){if(!x)return;if(!y||y.length===0){x.textContent="";return}const q=y.reduce((z,Y)=>z+Math.round(Y.size/1024),0);if(y.length===1)x.textContent=y[0].name+"  ("+q+" KB)";else{const z=window.t&&window.t("glv-files-count")||"{n} 个文件";x.textContent=z.replace("{n}",y.length)+"  ("+q+" KB)"}}function c(x){const y=s[x];return Array.isArray(y)?y:y?[y]:[]}function u(){const x=e("btn-glv-run");if(!x)return;const y=c("glFile").length>0&&c("vatFile").length>0;x.disabled=!y||s.running}function f(){const x=e("glv-status");if(!x||s.running)return;const y=c("vatFile").length,q=c("glFile").length;y===0&&q===0?(x.className="vex-action-info muted",x.innerHTML="<span>"+r("hint_need_both")+"</span>"):y>0&&q>0?(x.className="vex-action-info ok",x.innerHTML="<span>"+r("hint_ready")+"</span>"):(x.className="vex-action-info muted",x.innerHTML="<span>"+r("hint_need_one_more")+"</span>")}function w(x,y){const q=x==="vat"?"vatFile":"glFile",z=x==="vat"?"glv-vat-input":"glv-gl-input",Y=x==="vat"?"glv-vat-name":"glv-gl-name",Z=c(q);y==null?s[q]=[]:s[q]=Z.filter((re,K)=>K!==y);const le=e(z);le&&(le.value=""),m(e(Y),c(q)),u(),f(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=w;function S(){s.glFile=[],s.vatFile=[],s.currentTaskId=null,s.lastDetail=[],s.lastSummary=null;const x=e("glv-vat-input");x&&(x.value="");const y=e("glv-gl-input");y&&(y.value="");const q=e("glv-vat-name");q&&(q.textContent="");const z=e("glv-gl-name");z&&(z.textContent="");const Y=e("glv-result");Y&&(Y.style.display="none");const Z=e("glv-kpi-strip");Z&&(Z.style.display="none"),u(),f(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function E(x){const y=e("glv-tbody");if(!y)return;oe(x.length),y.innerHTML="";const q=r("not_found"),z=document.createDocumentFragment();x.forEach(Y=>{const Z=document.createElement("tr"),le=(ne,se)=>{const ue=document.createElement("td");return se&&(ue.className=se),ue.textContent=ne,ue},re=Y.gl_amount===null||Y.gl_amount===void 0,K=Y.diff;let ee="glv-num",te="glv-num";re?(te+=" glv-cell-missing",ee+=" glv-cell-missing"):Math.abs(K||0)<.005?ee+=" glv-cell-ok":ee+=" glv-cell-diff",Z.appendChild(le(Y.doc_no||"","glv-doc")),Z.appendChild(le(Y.date||"","")),Z.appendChild(le(Y.customer_name||"","")),Z.appendChild(le(l(Y.vat_amount),"glv-num")),Z.appendChild(le(re?q:l(Y.gl_amount),te)),Z.appendChild(le(re?q:l(Y.diff),ee)),Z.appendChild(le(Y.account_codes||"","glv-doc")),z.appendChild(Z)}),y.appendChild(z)}function v(x){const y=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!y)return;y.innerHTML="",[{label:r("s_gl_total"),amount:x.gl_total,emph:!0,items:[],negate:!1},{label:r("s_minus_gl_cr"),amount:-(x.gl_only_credit||0),emph:!1,items:x.gl_only_credit_items||[],negate:!0},{label:r("s_plus_gl_dr"),amount:x.gl_only_debit||0,emph:!1,items:x.gl_only_debit_items||[],negate:!1},{label:r("s_plus_vat_p"),amount:x.vat_only_positive||0,emph:!1,items:x.vat_only_positive_items||[],negate:!1},{label:r("s_minus_vat_n"),amount:x.vat_only_negative||0,emph:!1,items:x.vat_only_negative_items||[],negate:!1},{label:r("s_vat_total"),amount:x.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:z,amount:Y,emph:Z,items:le,negate:re})=>{const K=document.createElement("tr");K.className=Z?"glv-summary-total":"glv-summary-sect";const ee=document.createElement("td"),te=document.createElement("td");ee.textContent=z,te.textContent=Z?l(Y):"",K.appendChild(ee),K.appendChild(te),y.appendChild(K),(le||[]).forEach(ne=>{const se=document.createElement("tr");se.className="glv-summary-item";const ue=document.createElement("td"),_=document.createElement("td"),M=[ne.doc_no,ne.date,ne.name].filter(Boolean);ue.textContent="· "+M.join("  ·  ");const j=re?-(ne.amount||0):ne.amount||0;_.textContent=l(j),se.appendChild(ue),se.appendChild(_),y.appendChild(se)})})}function h(x){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=x&&x.matched!=null?x.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=x&&x.diff!=null?x.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=x&&x.unmatched!=null?x.unmatched:"—")}function C(x){if(!x)return"";try{const y=new Date(x);if(isNaN(y.getTime()))return x;const q=z=>String(z).padStart(2,"0");return y.getFullYear()+"-"+q(y.getMonth()+1)+"-"+q(y.getDate())+" "+q(y.getHours())+":"+q(y.getMinutes())}catch{return x}}const L=10;var A=[],T=1;function k(){T=1,g();var x=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(x){var y=e("glv-history-tbody");y&&y.querySelectorAll("tr").forEach(function(q){q.dataset.taskId&&(q.style.display=q.textContent.toLowerCase().indexOf(x)>=0?"":"none")})}}function g(){const x=e("glv-history-table-wrap"),y=e("glv-history-empty"),q=e("glv-history-tbody"),z=e("glv-history-pager"),Y=e("glv-history-pager-info"),Z=e("glv-history-prev"),le=e("glv-history-next");if(!q)return;if(q.innerHTML="",!A.length){x&&(x.style.display="none"),y&&(y.style.display=""),z&&(z.style.display="none");return}x&&(x.style.display=""),y&&(y.style.display="none");const re=Math.ceil(A.length/L);T>re&&(T=re);const K=(T-1)*L,ee=A.slice(K,K+L);z&&(z.style.display=A.length>L?"":"none",Y&&(Y.textContent=T+" / "+re),Z&&(Z.disabled=T<=1),le&&(le.disabled=T>=re)),ee.forEach(ne=>{const se=document.createElement("tr");se.dataset.taskId=ne.id;const ue=document.createElement("td");ue.textContent=C(ne.created_at);const _=document.createElement("td");_.className="glv-history-file",_.title=(ne.vat_filename||"")+" + "+(ne.gl_filename||""),_.textContent=(ne.vat_filename||"?")+" + "+(ne.gl_filename||"?");const M=document.createElement("td");M.className="glv-num",M.textContent=(ne.vat_row_count||0)+" / "+(ne.gl_row_count||0);const j=document.createElement("td");j.className="glv-num",j.textContent=ne.matched_count||0;const J=document.createElement("td");J.className="glv-num",J.textContent=ne.diff_count||0;const O=document.createElement("td");O.className="glv-num",O.textContent=ne.unmatched_count||0;const b=document.createElement("td");b.className="glv-history-actions";const N=(de,ie,ce,ae)=>{const pe=document.createElement("button");return pe.type="button",ce&&(pe.className=ce),pe.title=ie,pe.setAttribute("aria-label",ie),pe.innerHTML=de,pe.onclick=ae,pe},V='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',W='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';b.appendChild(N(V,r("hist_load"),"",()=>D(ne.id))),b.appendChild(N(W,r("hist_export"),"",()=>R(ne.id))),b.appendChild(N(X,r("hist_delete"),"glv-del",()=>B(ne.id))),[ue,_,M,j,J,O,b].forEach(de=>se.appendChild(de)),q.appendChild(se)})}function I(){var x=e("glv-history-prev"),y=e("glv-history-next");x&&!x._glvBound&&(x._glvBound=!0,x.addEventListener("click",function(){T>1&&(T--,g())})),y&&!y._glvBound&&(y._glvBound=!0,y.addEventListener("click",function(){var q=Math.ceil(A.length/L);T<q&&(T++,g())}))}async function H(){try{const y=await(await fetch("/api/recon/gl-vat/tasks",{headers:o()})).json();A=y&&y.tasks||[],T=1,g(),I()}catch(x){console.error("[gl-vat] history load failed:",x)}}async function D(x){try{const q=await(await fetch("/api/recon/gl-vat/"+x,{headers:o()})).json();if(!q||!q.ok)throw new Error("load_failed");s.currentTaskId=x,s.lastDetail=q.detail||[],s.lastSummary=q.summary||{},h(q.stats||{}),E(s.lastDetail),v(s.lastSummary);const z=e("glv-result");z&&(z.style.display=""),F(),window.scrollTo({top:z?z.offsetTop-80:0,behavior:"smooth"})}catch(y){console.error("[gl-vat] load task failed:",y),alert(r("error")+": "+(y.message||y))}}async function R(x){try{const y="/api/recon/gl-vat/"+x+"/export?lang="+encodeURIComponent(a()),q=await fetch(y,{headers:o()});if(!q.ok)throw new Error("HTTP "+q.status);const z=await q.blob(),Y=document.createElement("a");Y.href=URL.createObjectURL(z),Y.download="GL_VAT_recon_"+x+".xlsx",document.body.appendChild(Y),Y.click(),setTimeout(()=>{URL.revokeObjectURL(Y.href),Y.remove()},200)}catch(y){console.error("[gl-vat] exportTask failed:",y),typeof showToast=="function"&&showToast(r("error")+": "+(y.message||y),"error")}}async function B(x){let y;if(typeof window.showConfirm=="function"?y=await window.showConfirm(r("confirm_delete"),{danger:!0}):y=confirm(r("confirm_delete")),!!y)try{const q=await fetch("/api/recon/gl-vat/"+x,{method:"DELETE",headers:o()});if(!q.ok)throw new Error("HTTP "+q.status);H()}catch(q){console.error("[gl-vat] delete failed:",q),typeof showToast=="function"&&showToast(r("error")+": "+(q.message||q),"error")}}async function P(){if(!s.glFile||!s.vatFile){typeof showToast=="function"&&showToast(r("need_files"),"warn");return}s.running=!0,u();const x=e("glv-status"),y=e("glv-progress"),q=e("glv-progress-sub");x&&(x.className="vex-action-info muted",x.style.color="",x.innerHTML="<span>"+r("running")+"</span>"),y&&(y.style.display=""),q&&(q.textContent=(s.vatFile.name||"VAT")+" + "+(s.glFile.name||"GL"));const z=new FormData,Y=c("vatFile"),Z=c("glFile");for(const re of Y)z.append("vat_files",re,re.name);for(const re of Z)z.append("gl_files",re,re.name);const le=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";z.append("revenue_prefix",le),z.append("lang",a());try{const re=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:o(),body:z});let K=null;try{K=await re.json()}catch{K=null}if(!re.ok||!K||!K.ok||!K.job_id)throw new Error(K&&K.detail||K&&K.error||"HTTP "+re.status);const ee=e("glv-progress-sub"),te=await window._reconPollJob(K.job_id,n(),{onProgress:_=>{ee&&(ee.textContent=window._reconProgressText(_,a()))}});if(!te||te.status!=="done"||!te.result_id)throw te&&te.status==="failed"&&te.error_code?new Error(p(te.error_code)):new Error(r("error")||"Error");const ne=await fetch("/api/recon/gl-vat/"+encodeURIComponent(te.result_id),{headers:o()});let se=null;try{se=await ne.json()}catch{se=null}if(!ne.ok||!se||!se.ok)throw new Error(se&&se.detail||se&&se.error||"HTTP "+ne.status);s.currentTaskId=se.task_id,s.lastDetail=se.detail||[],s.lastSummary=se.summary||{},h(se.stats||{}),E(s.lastDetail),v(s.lastSummary);const ue=e("glv-result");ue&&(ue.style.display=""),F(),x&&(x.className="vex-action-info ok",x.style.color="",x.innerHTML="<span>"+r("done")+" · GL "+(se.gl_row_count||0)+" · VAT "+(se.vat_row_count||0)+"</span>"),H()}catch(re){console.error("[gl-vat] run failed:",re),x&&(x.className="vex-action-info",x.style.color="#ef4444",x.innerHTML="<span>"+r("error")+": "+(re.message||re)+"</span>")}finally{s.running=!1,y&&(y.style.display="none"),u()}}async function U(){if(s.currentTaskId)try{const x="/api/recon/gl-vat/"+s.currentTaskId+"/export?lang="+encodeURIComponent(a()),y=await fetch(x,{headers:o()});if(!y.ok)throw new Error("HTTP "+y.status);const q=await y.blob(),z=document.createElement("a");z.href=URL.createObjectURL(q),z.download="GL_VAT_recon_"+s.currentTaskId+".xlsx",document.body.appendChild(z),z.click(),setTimeout(()=>{URL.revokeObjectURL(z.href),z.remove()},200)}catch(x){console.error("[gl-vat] export failed:",x),typeof showToast=="function"&&showToast(r("error")+": "+(x.message||x),"error")}}function G(){s.running||f(),H(),s.lastDetail&&s.lastDetail.length&&E(s.lastDetail),s.lastSummary&&v(s.lastSummary)}function F(){var x=e("glv-kpi-strip");x&&(x.style.display="");var y=e("glv-section-summary");y&&y.setAttribute("data-collapsed","false");var q=e("glv-section-detail");q&&q.setAttribute("data-collapsed","false")}function Q(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(x=>{const y=x.getAttribute("data-toggle"),q=document.getElementById(y);if(!q)return;const z=Y=>{if(Y.target&&Y.target.closest("button")!==null&&!Y.target.classList.contains("glv-section-head"))return;const Z=q.getAttribute("data-collapsed")==="true";q.setAttribute("data-collapsed",Z?"false":"true")};x.addEventListener("click",z),x.addEventListener("keydown",Y=>{(Y.key==="Enter"||Y.key===" ")&&(Y.preventDefault(),z(Y))})})}function oe(x){const y=e("glv-detail-count");y&&(y.textContent=x!=null?String(x):"")}function $(){if(s.inited){H();return}s.inited=!0,d("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),d("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const x=e("btn-glv-run");x&&x.addEventListener("click",P);const y=e("btn-glv-export");y&&y.addEventListener("click",U);const q=e("btn-glv-reset");q&&q.addEventListener("click",S);const z=e("glv-hist-search");z&&z.addEventListener("input",k),Q(),h(null),f(),window._loadGlvHistory=H,H(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",G)}window.GlVatRecon={ensureInit:$},window._glvPreviewFiles=function(x){return c(x==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let i={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function r(){const D=typeof _userInfo<"u"?_userInfo:null;return!!(D&&(D.role==="owner"||D.is_super_admin))}function p(){const D=typeof _userInfo<"u"?_userInfo:null;return!!(D&&D.id===s)}function l(D){return typeof escapeHtml=="function"?escapeHtml(D==null?"":String(D)):String(D??"")}function d(D,R){try{typeof showToast=="function"&&showToast(D,R||"info")}catch{}}async function m(D,R){const B=localStorage.getItem("mrpilot_token");if(B&&!(i.loaded[D]&&!R))try{const P=await fetch("/api/erp/mappings/"+D,{headers:{Authorization:"Bearer "+B}});if(!P.ok)throw new Error("http_"+P.status);const U=await P.json();i.items[D]=U.items||[],i.loaded[D]=!0}catch{i.items[D]=[],i.loaded[D]=!1}}async function c(D){if(i.clientLoaded)return;const R=localStorage.getItem("mrpilot_token");if(R)try{const B=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+R}});if(!B.ok)throw new Error("http_"+B.status);const P=await B.json();i.clientList=(P.clients||P.items||[]).filter(U=>U.is_active!==!1),i.clientLoaded=!0}catch{i.clientList=[]}}function u(){const D=document.getElementById("erp-map-pane-wrap");if(!D)return;const R=!r();let B="";R&&(B+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+l(t("erp-map-readonly-tip"))+"</div>"),B+='<div class="erp-map-toolbar">',!R&&i.sub!=="products"&&(B+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+l(t("erp-map-add-row"))+"</button>"),B+="</div>",B+='<div class="erp-map-table" id="erp-map-table-host"></div>',D.innerHTML=B,f();const P=document.getElementById("erp-map-dev-bar");P&&(P.style.display=r()&&p()?"":"none")}function f(){const D=document.getElementById("erp-map-table-host");if(!D)return;const R=i.sub,B=i.items[R]||[],P=i.addingNew[R],U=!r();if(!B.length&&!P){D.innerHTML='<div class="erp-map-empty"><strong>'+l(t("erp-map-empty-"+R))+"</strong>"+l(t("erp-map-empty-"+R+"-sub"))+"</div>";return}let G="";G+=w(R),P&&!U&&(G+=C(R)),B.forEach(function(F){G+=L(R,F,U)}),D.innerHTML=G}function w(D){return D==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+l(t("erp-map-col-client"))+"</div><div>"+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":D==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-category"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":D==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+l(t("erp-map-col-item-name"))+"</div><div>"+l(t("erp-map-col-erp-product-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-tax"))+"</div><div>"+l(t("erp-map-col-erp-tax-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>"}function S(D,R){let B='<select class="form-input" data-erp-field="'+R+'">';return B+='<option value="">'+l(t("erp-map-pick-erp"))+"</option>",e.forEach(function(P){const U=P===D?" selected":"";B+='<option value="'+P+'"'+U+">"+l(n[P])+"</option>"}),B+="</select>",B}function E(D){let R='<select class="form-input" data-erp-field="client_id">';return R+='<option value="">'+l(t("erp-map-pick-client"))+"</option>",(i.clientList||[]).forEach(function(B){const P=String(B.id)===String(D)?" selected":"";R+='<option value="'+B.id+'"'+P+">"+l(B.name||"#"+B.id)+"</option>"}),R+="</select>",R}function v(D){let R='<select class="form-input" data-erp-field="pearnly_category">';return R+='<option value="">'+l(t("erp-map-pick-cat"))+"</option>",a.forEach(function(B){const P=B===D?" selected":"";R+='<option value="'+B+'"'+P+">"+l(t("erp-map-cat-"+B))+"</option>"}),R+="</select>",R}function h(D){let R='<select class="form-input" data-erp-field="pearnly_tax_kind">';return R+='<option value="">'+l(t("erp-map-pick-tax"))+"</option>",o.forEach(function(B){const P=B===D?" selected":"";R+='<option value="'+B+'"'+P+">"+l(t("erp-map-tax-"+B))+"</option>"}),R+="</select>",R}function C(D){const R='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+l(t("erp-map-save"))+"</button>";return D==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+l(t("erp-map-col-client"))+'">'+E("")+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+S("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+R+"</div></div>":D==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+S("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-category"))+'">'+v("")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+l(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+l(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+R+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+S("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-tax"))+'">'+h("")+'</div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+R+"</div></div>"}function L(D,R,B){const P=B?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+l(R.id)+'" title="'+l(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',U='<span class="erp-map-erp-badge">'+l(n[R.erp_type]||R.erp_type)+"</span>";if(D==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+l(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+l(R.client_name||"#"+R.client_id)+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+U+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(R.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(R.notes||"")+"</div><div>"+P+"</div></div>";if(D==="accounts"){const F=t("erp-map-cat-"+(R.pearnly_category||"other"))||R.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+l(t("erp-map-col-erp"))+'">'+U+'</div><div data-label="'+l(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+l(F)+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(R.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(R.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(R.notes||"")+"</div><div>"+P+"</div></div>"}if(D==="products")return'<div class="erp-map-row row-products"><div data-label="'+l(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+l(R.item_name||"")+'</div><div data-label="'+l(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+l(R.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(R.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(R.notes||"")+"</div><div>"+P+"</div></div>";const G=t("erp-map-tax-"+(R.pearnly_tax_kind||""))||R.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+l(t("erp-map-col-erp"))+'">'+U+'</div><div data-label="'+l(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+l(G)+'</span></div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+l(R.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(R.notes||"")+"</div><div>"+P+"</div></div>"}async function A(D){const R=i.sub,B={};D.querySelectorAll("[data-erp-field]").forEach(function(F){B[F.dataset.erpField]=(F.value||"").trim()});const P=localStorage.getItem("mrpilot_token");if(!P)return;let U={},G="/api/erp/mappings/"+R;if(R==="clients"){if(!B.client_id||!B.erp_type||!B.erp_code){d(t("erp-map-save-fail"),"error");return}U={client_id:parseInt(B.client_id,10),erp_type:B.erp_type,erp_code:B.erp_code,notes:B.notes||""}}else if(R==="accounts"){if(!B.erp_type||!B.pearnly_category||!B.erp_code){d(t("erp-map-save-fail"),"error");return}U={erp_type:B.erp_type,pearnly_category:B.pearnly_category,erp_code:B.erp_code,erp_name:B.erp_name||"",notes:B.notes||""}}else{if(!B.erp_type||!B.pearnly_tax_kind||!B.erp_code){d(t("erp-map-save-fail"),"error");return}U={erp_type:B.erp_type,pearnly_tax_kind:B.pearnly_tax_kind,erp_code:B.erp_code,notes:B.notes||""}}try{const F=await fetch(G,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+P},body:JSON.stringify(U)});if(!F.ok)throw new Error("http_"+F.status);i.addingNew[R]=!1,await m(R,!0),f(),d(t("erp-map-saved-toast"),"success")}catch{d(t("erp-map-save-fail"),"error")}}async function T(D){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const B=i.sub,P=localStorage.getItem("mrpilot_token");try{const U=await fetch("/api/erp/mappings/"+B+"/"+encodeURIComponent(D),{method:"DELETE",headers:{Authorization:"Bearer "+P}});if(!U.ok)throw new Error("http_"+U.status);await m(B,!0),f(),d(t("erp-map-deleted-toast"),"success")}catch{d(t("erp-map-delete-fail"),"error")}}async function k(){await c(),await m(i.sub,!1),u()}function g(D){D!==i.sub&&(i.sub=D,i.addingNew[D]=!1,["clients","accounts","taxes","products"].forEach(function(R){R!==D&&(i.addingNew[R]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(R){R.classList.toggle("active",R.dataset.erpSubtab===D)}),m(D,!1).then(function(){u()}))}function I(){i.bound||(i.bound=!0,document.addEventListener("click",function(D){const R=D.target.closest(".erp-subtab[data-erp-subtab]");if(R){D.preventDefault();const F=R.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(Q){Q.classList.toggle("active",Q.dataset.erpSubtab===F)}),document.querySelectorAll(".erp-subpanel").forEach(function(Q){Q.classList.toggle("active",Q.dataset.erpSubpanel===F)}),F==="mappings"&&setTimeout(k,50);return}const B=D.target.closest(".erp-map-subtab[data-erp-subtab]");if(B){D.preventDefault(),g(B.dataset.erpSubtab);return}if(D.target.closest("#erp-map-add-btn")){if(D.preventDefault(),!r())return;i.addingNew[i.sub]=!0,f();return}const U=D.target.closest('[data-erp-save="new"]');if(U){D.preventDefault();const F=U.closest('[data-erp-row="new"]');F&&A(F);return}const G=D.target.closest("[data-erp-del]");if(G){D.preventDefault(),T(G.dataset.erpDel);return}}))}function H(){const D=document.getElementById("erp-map-pane-wrap");D&&D.children.length>0&&u(),document.querySelectorAll(".erp-map-subtab").forEach(function(R){const B="erp-map-subtab-"+R.dataset.erpSubtab,P=t(B);P&&P!==B&&(R.textContent=P)})}I(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",H)})();(function(){let e=null,n=0,a=!1;function o(k){return typeof escapeHtml=="function"?escapeHtml(k==null?"":String(k)):String(k??"")}function s(k,g){try{typeof showToast=="function"&&showToast(k,g||"info")}catch{}}async function i(k){const g=Date.now();if(e&&g-n<3e4)return e;const I=localStorage.getItem("mrpilot_token");if(!I)return[];try{const H=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+I}});if(!H.ok)return[];const D=await H.json();return e=D&&D.connectors||[],n=g,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function p(k){try{localStorage.setItem("pn_push_default_connector",k||"")}catch{}}function l(k){if(!k||!k.length)return null;const g=r();if(g){const H=k.find(D=>D.id===g);if(H)return H}const I=k.find(H=>H.is_default);return I||k[0]}function d(k){if(!k)return!1;const g=String(k.status||"").toLowerCase();return g==="exception"||g==="exception_pending"||g==="rejected"}function m(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(k){const g=k&&(k.type||k.id);return g==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':g==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function u(k,g){if(!k||!g)return!1;const I=document.getElementById("btn-push-default");I&&(I.disabled=!0,I.classList.add("loading"));const H=localStorage.getItem("mrpilot_token");try{let D,R={method:"POST",headers:{Authorization:"Bearer "+H}};k.type==="xero"?D="/api/erp/xero/push/"+encodeURIComponent(g):(D="/api/erp/push",R.headers["Content-Type"]="application/json",R.body=JSON.stringify({history_id:g,endpoint_id:k.endpoint_id||void 0}));const B=await fetch(D,R);let P={};try{P=await B.json()}catch{}if(!B.ok){let U=P&&P.detail||"unknown";typeof U=="object"&&(U=U.code||JSON.stringify(U));let G=String(U||"unknown");if(k.type==="xero"){const F=G.replace(/^xero\./,"").toLowerCase(),Q=t("xero-"+F);Q&&Q!=="xero-"+F&&(G=Q)}return s(t("unified-push-fail").replace("{name}",k.name).replace("{err}",G),"error"),!1}if(P&&P.ok===!1){let U=P.error_msg||P.error_code||"unknown";return U=String(U).slice(0,200),s(t("unified-push-fail").replace("{name}",k.name).replace("{err}",U),"error"),!1}return s(t("unified-push-ok").replace("{name}",k.name),"success"),!0}catch(D){return s(t("unified-push-fail").replace("{name}",k.name).replace("{err}",D.message||"network"),"error"),!1}finally{I&&(I.disabled=!1,I.classList.remove("loading"))}}async function f(k,g){for(const I of k)await u(I,g)}function w(k,g){const I=document.createElement("div");I.className="pn-push-dropdown",I.id="pn-push-dropdown";const H=(k||[]).map(R=>{const B=!!(g&&R.id===g.id),P=R.method==="download"?t("unified-push-tag-download"):B?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(R.id)+'"><span class="pn-pd-icon">'+c(R)+'</span><span class="pn-pd-name">'+o(R.name)+"</span>"+(P?'<span class="pn-pd-tag">'+o(P)+"</span>":"")+(B?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),D=k&&k.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",k.length))+"</span></div>":"";return I.innerHTML=H+D,I}function S(){const k=document.getElementById("pn-push-dropdown");k&&k.remove()}async function E(){if(document.getElementById("pn-push-dropdown")){S();return}const k=await i()||[],g=l(k),I=w(k,g),H=document.getElementById("pn-push-wrap");H&&H.appendChild(I)}async function v(){const k=await i()||[],g=l(k);if(!g)return;const I=m(),H=I&&(I._historyId||I.history_id);if(H){if(d(I)){s(t("unified-push-disabled-exc"),"warn");return}await u(g,H)}}async function h(k){S();const g=await i()||[],I=m(),H=I&&(I._historyId||I.history_id);if(!H)return;if(d(I)){s(t("unified-push-disabled-exc"),"warn");return}if(k==="__all__"){await f(g,H);return}const D=g.find(R=>R.id===k);D&&(p(k),await u(D,H),L())}async function C(){const k=document.getElementById("drawer-history-save");if(!k||k.querySelector("#pn-push-wrap"))return;const g=document.createElement("div");g.id="pn-push-wrap",g.className="pn-push-wrap",g.dataset.loading="1",k.insertBefore(g,k.firstChild),["btn-push-erp","btn-xero-push"].forEach(P=>{k.querySelectorAll("#"+P).forEach(U=>{U.style.display="none"})});const I=await i()||[],H=l(I),D=I.length>0;if(!D)g.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const P=I.length>1;g.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+c(H)+"<span>"+o(t("unified-push-to").replace("{name}",H?H.name:""))+"</span></button>"+(P?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete g.dataset.loading;const R=g.querySelector("#btn-push-default");R&&D&&R.addEventListener("click",v);const B=g.querySelector("#btn-push-arrow");B&&B.addEventListener("click",function(P){P.stopPropagation(),E()}),a||(a=!0,document.addEventListener("click",function(P){const U=P.target.closest(".pn-pd-item");if(U){const G=U.getAttribute("data-cid");h(G);return}P.target.closest("#btn-push-arrow")||S()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",L))}function L(){const k=document.getElementById("pn-push-wrap");k&&(k.remove(),e=null,n=0,C())}function A(){const k=document.getElementById("drawer-history-save");if(!k||!k.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(I=>{k.querySelectorAll("#"+I).forEach(H=>{H.style.display!=="none"&&(H.style.display="none")})});const g=k.querySelectorAll("#pn-push-wrap");if(g.length>1)for(let I=1;I<g.length;I++)g[I].remove()}function T(){try{const k=function(){return document.getElementById("drawer-body")},g=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&C(),A()}),I=k();if(I)g.observe(I,{childList:!0,subtree:!0});else{const H=new MutationObserver(function(){const D=k();D&&(g.observe(D,{childList:!0,subtree:!0}),H.disconnect())});H.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&C(),A()},200)}catch{}}T()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",p=t(r);p&&p!==r&&(i.textContent=p)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const l=document.getElementById("erp-onboard-title"),d=document.getElementById("erp-onboard-body"),m=document.getElementById("erp-onboard-ok"),c=document.getElementById("erp-onboard-later");l&&(l.textContent=t("erp-onboard-title")),d&&(d.textContent=t("erp-onboard-body")),m&&(m.textContent=t("erp-onboard-ok")),c&&(c.textContent=t("erp-onboard-later"))}r();function p(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}p();try{const l=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');l&&l.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}p()}),i.addEventListener("click",function(l){l.target===i&&p()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),p=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||p)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,i=s[a]||s.th||s.en,r=n.stage_total,p=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const l={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+l.replace("{d}",p||0).replace("{t}",r)}return i},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,i=o.maxMs||1200*1e3,r=Date.now();let p=0;for(;;){let l=null;try{const d=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{l=await d.json()}catch{l=null}(!d.ok||!l||!l.ok)&&(l=null)}catch{l=null}if(l){if(p=0,o.onProgress)try{o.onProgress(l.progress||{},l)}catch{}if(l.status==="done"||l.status==="failed"||l.status==="needs_review"||l.status==="needs_mapping")return l}else if(++p>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(d=>setTimeout(d,s))}}})();(function(){let e=!1,n=[],a=[],o=null,s="all",i=[],r={stmt:"",gl:""},p=[];const l=_=>document.getElementById(_);function d(_){if(_==null)return"—";const M=Number(_);return isNaN(M)?"—":M.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function m(_){return _?String(_).slice(0,10).split("-").reverse().join("/"):"—"}function c(_){return String(_||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function u(_,M){M=window._currentLang||M||"th";const j={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},J={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},O=j[_]||J;return O[M]||O.th||O.en}function f(_){const M=_==="stmt"?n:a,j=l(`brv2-${_}-name`);if(j)if(M.length===0)j.textContent="";else{const O=window._currentLang||"zh",b={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};j.textContent=M.length+(b[O]||" 个文件")}const J=l("brv2-preview-panel");J&&J.style.display!=="none"&&E(_),w()}function w(){const _=l("brv2-toggle-preview"),M=l("brv2-preview-panel"),j=n.length+a.length>0;_&&(_.style.display=j?"":"none"),!j&&M&&(M.style.display="none",_&&_.classList.remove("open"))}function S(){E("stmt"),E("gl")}function E(_){const M=l(_==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!M)return;const j=_==="stmt"?n:a,J=window._currentLang||"zh",O={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},b=(O[_]||{})[J]||O[_].zh,N=c(window.t&&window.t("vex-preview-search")||"搜索文件名..."),V=c(window.t&&window.t("vex-preview-clear-all")||"全清"),W=r[_]||"";M.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+c(b)+' <span class="vex-pp-col-count">'+j.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+_+'" type="text" placeholder="'+N+'" value="'+c(W)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+_+'" type="button">'+V+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+_+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+_+'-pg"></div>';const X=l("brv2-pp-search-"+_);X&&X.addEventListener("input",function(ie){r[_]=ie.target.value,v(_)});const de=l("brv2-pp-clearall-"+_);de&&de.addEventListener("click",function(){_==="stmt"?n.length=0:a.length=0,f(_),P()}),v(_)}function v(_){const M=l("brv2-pp-"+_+"-list"),j=l("brv2-pp-"+_+"-pg");if(!M)return;const J=_==="stmt"?n:a,O=(r[_]||"").toLowerCase(),b=O?J.filter(W=>W.name.toLowerCase().includes(O)):J.slice(),N='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',V='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(M.innerHTML=b.map((W,X)=>'<div class="vex-pp-file-row">'+N+'<span class="vex-pp-fi-name" title="'+c(W.name)+'">'+c(W.name)+'</span><span class="vex-pp-fi-size">'+h(W.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+_+'" data-idx="'+J.indexOf(W)+'" aria-label="remove">'+V+"</button></div>").join(""),M.querySelectorAll(".vex-pp-fi-del").forEach(function(W){W.addEventListener("click",function(){const X=parseInt(W.dataset.idx,10);W.dataset.zone==="stmt"?n.splice(X,1):a.splice(X,1),f(W.dataset.zone),P()})}),j){const W=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";j.textContent=W.replace("{n}",b.length).replace("{m}",J.length)}}function h(_){return _?_<1024?_+" B":_<1048576?(_/1024).toFixed(1)+" KB":(_/1048576).toFixed(1)+" MB":""}var C="pearnly.brv2.lastAnchorOcr";function L(_){try{var M=_&&_._anchor_ocr;if(!M||typeof M!="object")return;var j={stmt_opening:Number.isFinite(+M.stmt_opening)?+M.stmt_opening:null,gl_opening:Number.isFinite(+M.gl_opening)?+M.gl_opening:null,gl_closing:Number.isFinite(+M.gl_closing)?+M.gl_closing:null,stmt_closing:Number.isFinite(+M.stmt_closing)?+M.stmt_closing:null,ts:Date.now()};localStorage.setItem(C,JSON.stringify(j))}catch{}}function A(){try{var _=localStorage.getItem(C);if(!_)return null;var M=JSON.parse(_);return!M||typeof M!="object"?null:M}catch{return null}}function T(){var _=A();if(_){var M={"brv2-anchor-stmt-opening":_.stmt_opening,"brv2-anchor-gl-opening":_.gl_opening,"brv2-anchor-gl-closing":_.gl_closing,"brv2-anchor-stmt-closing":_.stmt_closing},j=0;Object.keys(M).forEach(function(V){var W=document.getElementById(V);if(W&&W.value===""){var X=M[V];if(Number.isFinite(X)){W.value=X.toFixed(2);var de=W.closest&&W.closest(".brv2-anchor-cell");de&&de.classList.add("is-prefilled"),j+=1}}});var J=document.getElementById("brv2-anchor-eq"),O=document.getElementById("brv2-anchor-eq-val");if(J&&O&&Number.isFinite(_.stmt_opening)&&Number.isFinite(_.gl_opening)){var b=_.stmt_opening-_.gl_opening;O.textContent=b.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),J.style.display=""}if(j>0){var N=document.getElementById("brv2-anchor-prefill-banner");N&&N.classList.add("show")}}}function k(){var _=document.getElementById("brv2-anchor-prefill-banner");if(_){var M=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(j){var J=document.getElementById(j);if(J){var O=J.closest&&J.closest(".brv2-anchor-cell");O&&O.classList.contains("is-prefilled")&&(M=!0)}}),_.classList.toggle("show",M)}}var g=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function I(_,M){return window.t&&window.t(_)||M}function H(_){return String(_??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function D(_){return Number.isFinite(+_)?(+_).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function R(_){var M=document.getElementById("brv2-summary-collapse");if(!(!M||!M.parentNode)){var j=document.getElementById("brv2-anchor-audit"),J=_&&_._anchor_overrides;if(!J||typeof J!="object"||Object.keys(J).length===0){j&&j.parentNode&&j.parentNode.removeChild(j);return}j||(j=document.createElement("div"),j.id="brv2-anchor-audit",j.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",M.parentNode.insertBefore(j,M.nextSibling));var O=g.map(function(b){var N=J[b[0]];if(!N)return"";var V=+N.ocr||0,W=+N.user||0,X=W-V,de=X>0?"+":(X<0,""),ie=Math.abs(X)<.005?"#6b7280":X>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+H(I(b[1],b[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+H(D(V))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+H(D(W))+'</td><td style="padding:6px 10px;color:'+ie+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+H(de+D(X))+"</td></tr>"}).join("");j.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+H(I("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+H(I("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+H(I("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+H(I("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+H(I("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+O+"</tbody></table>"}}function B(){const _=l("brv2-toggle-preview");_&&!_._reconBound&&(_._reconBound=!0,_.addEventListener("click",function(){const M=l("brv2-preview-panel"),j=l("brv2-toggle-preview-label"),J=M&&M.style.display!=="none";M&&(M.style.display=J?"none":""),_.classList.toggle("open",!J),j&&(j.textContent=J?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),J||S()}))}function P(){const _=l("brv2-run-btn"),M=l("brv2-status"),j=n.length>0,J=a.length>0;if(_&&(_.disabled=!(j&&J)),M){const O=window._currentLang||"zh";if(!j&&!J){const b={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};M.textContent=b[O]||b.zh}else if(j)if(J){const b={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};M.textContent=b[O]||b.zh}else{const b={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};M.textContent=b[O]||b.zh}else{const b={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};M.textContent=b[O]||b.zh}}}function U(_,M,j){const J=l(_),O=l(M);!J||!O||(J.addEventListener("click",()=>O.click()),J.addEventListener("keydown",b=>{(b.key==="Enter"||b.key===" ")&&(b.preventDefault(),O.click())}),J.addEventListener("dragover",b=>{b.preventDefault(),J.classList.add("drag-over")}),J.addEventListener("dragleave",()=>J.classList.remove("drag-over")),J.addEventListener("drop",b=>{b.preventDefault(),J.classList.remove("drag-over");const N=Array.from(b.dataTransfer.files||[]);j==="stmt"?n.push(...N):a.push(...N),f(j),P()}),O.addEventListener("change",()=>{const b=Array.from(O.files||[]);j==="stmt"?n.push(...b):a.push(...b),O.value="",f(j),P()}))}function G(_){const M=l("brv2-progress"),j=l("brv2-run-btn"),J=l("brv2-error");M&&(M.style.display=_?"":"none"),j&&(j.disabled=_),J&&(J.style.display="none")}function F(_){const M=l("brv2-error");M&&(M.textContent=_,M.style.display="",M.scrollIntoView({behavior:"smooth",block:"nearest"})),G(!1),P(),window.showToast&&window.showToast(_,"error")}async function Q(){if(n.length===0||a.length===0)return;const _=localStorage.getItem("mrpilot_token")||"",M=window._currentLang||"zh",j=(l("brv2-acct-select")||{}).value||"";$(!1),G(!0);try{const J=new FormData;n.forEach(ae=>J.append("stmt_files",ae)),a.forEach(ae=>J.append("gl_files",ae)),J.append("gl_account",j),J.append("lang",M);const O=parseFloat((l("brv2-anchor-gl-closing")||{}).value),b=parseFloat((l("brv2-anchor-stmt-closing")||{}).value),N=parseFloat((l("brv2-anchor-stmt-opening")||{}).value),V=parseFloat((l("brv2-anchor-gl-opening")||{}).value);Number.isFinite(O)&&J.append("gl_closing_override",O),Number.isFinite(b)&&J.append("stmt_closing_override",b),Number.isFinite(N)&&J.append("stmt_opening_override",N),Number.isFinite(V)&&J.append("gl_opening_override",V);const W=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+_},body:J});let X=null;try{X=await W.json()}catch{X=null}if(X&&X.needs_mapping){G(!1),window.ReconMapping?window.ReconMapping.show(X,{token:_,lang:M,onConfirmed:function(){Q()}}):F(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!W.ok||!X||!X.ok||!X.job_id){G(!1),X&&(X.detail||X.error)?F(_humanizeBackendError(X.detail||X.error,"Error "+W.status)):F(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const de=l("brv2-progress-sub"),ie=await window._reconPollJob(X.job_id,_,{onProgress:ae=>{de&&(de.textContent=window._reconProgressText(ae,M))}});if(ie&&ie.status==="needs_mapping"&&ie.mapping){G(!1),window.ReconMapping?window.ReconMapping.show(ie.mapping,{token:_,lang:M,onConfirmed:function(){Q()}}):F(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(ie&&ie.status==="needs_review"&&ie.review){G(!1),window.ReconReview?window.ReconReview.show(ie.review,{token:_,lang:M,jobId:X.job_id,onConfirmed:async function(ae){G(!0);const pe=await window._reconPollJob(ae,_,{onProgress:fe=>{de&&(de.textContent=window._reconProgressText(fe,M))}});await ce(pe)}}):F(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(ie&&ie.status==="failed"){G(!1),F(u(ie.error_code,M));return}await ce(ie);async function ce(ae){try{if(!ae||ae.status!=="done"||!ae.result_id){G(!1),F(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const pe=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ae.result_id),{headers:{Authorization:"Bearer "+_}});let fe=null;try{fe=await pe.json()}catch{fe=null}if(!pe.ok||fe===null||!fe.ok){G(!1),F(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(fe.gl_accounts||[]).length>1&&oe(fe.gl_accounts),o=fe,i=fe.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(ge=>ge.classList.toggle("active",ge.dataset.filter==="all")),L(fe&&fe.summary),G(!1),z(fe),Z();const me=l("brv2-summary-collapse");me&&me.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(pe){G(!1),F(pe.message||"Network error")}}}catch(J){F(J.message||"Network error")}}function oe(_){const M=l("brv2-acct-select");if(!M)return;const j=window._currentLang||"zh",J={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[j]||"全部账户";M.innerHTML=`<option value="">${J}</option>`+_.map(O=>`<option value="${c(O)}">${c(O)}</option>`).join(""),M.style.display=""}function $(_){const M=l("brv2-summary-collapse"),j=l("brv2-detail-collapse"),J=l("brv2-export-btn"),O=l("brv2-new-btn"),b=l("brv2-parse-info-wrap");M&&(M.style.display=_?"":"none"),j&&(j.style.display=_?"":"none"),J&&(J.style.display=_?"":"none"),O&&(O.style.display=_?"":"none"),!_&&b&&(b.style.display="none");const N=l("brv2-warnings");!_&&N&&(N.style.display="none",N.innerHTML="")}function x(_){const M=l("brv2-parse-info-wrap"),j=l("brv2-parse-info-body");if(!M||!j)return;const J=_.parse_info;if(!J){M.style.display="none";return}const O=window._currentLang||"zh",b={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},N=ce=>(b[ce]||{})[O]||(b[ce]||{}).zh||ce,V=[...(J.stmt_files||[]).map(ce=>({...ce,_type:"stmt",_extra:ce.bank_code||""})),...(J.gl_files||[]).map(ce=>({...ce,_type:"gl",_extra:(ce.accounts||[]).join(", ")}))],W={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},X=ce=>{const ae=String(ce||"");return/Cannot detect bank statement column headers/i.test(ae)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ae)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ae)?"stmt_no_rows":/unsupported format/i.test(ae)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ae)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ae)?"ocr_failed":null},de=ce=>{const ae=ce.error_code||X(ce.error);if(ae&&W[ae]){const pe=window._currentLang||"zh";return W[ae][pe]||W[ae].zh}return String(ce.error||"").slice(0,80)},ie=ce=>!ce.ok&&ce.error?`<span style="color:#dc2626">${N("fail")} — ${c(de(ce))}</span>`:ce.rows?`<span style="color:#059669">${N("ok")} (${ce.rows})</span>`:`<span style="color:#d97706">${N("warn")}</span>`;j.innerHTML=`
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${N("title")}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${N("type")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${N("file")}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${N("rows")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${N("bank")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${N("status")}</th>
                    </tr>
                </thead>
                <tbody>
                    ${V.map(ce=>`<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${ce._type==="stmt"?N("stmt"):N("gl")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${c(ce.file||"")}">${c(ce.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${ce.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${c(ce._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${ie(ce)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,M.style.display=""}async function y(_){const M=localStorage.getItem("mrpilot_token")||"",j=window._currentLang||"zh";try{const J=await fetch("/api/recon/bank-v2/"+_+"/export?lang="+j,{headers:{Authorization:"Bearer "+M}});if(!J.ok){const de=await J.json().catch(()=>({}));window.showToast&&window.showToast(de.detail||"Export failed","error");return}const O=await J.blob(),N=(J.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),V=N?N[1].replace(/['"]/g,""):"reconciliation.xlsx",W=URL.createObjectURL(O),X=document.createElement("a");X.href=W,X.download=V,document.body.appendChild(X),X.click(),document.body.removeChild(X),URL.revokeObjectURL(W)}catch(J){window.showToast&&window.showToast("Export error: "+J.message,"error")}}function q(_,M){const j=l("brv2-summary-collapse");let J=l("brv2-warnings");const O=window._currentLang||"zh",b={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[O]||"⏭ ",N=[];if((M||[]).forEach(V=>N.push(b+" "+V)),(_||[]).forEach(V=>N.push(V)),!N.length){J&&(J.style.display="none");return}if(!J)if(J=document.createElement("div"),J.id="brv2-warnings",j&&j.parentNode)j.parentNode.insertBefore(J,j);else return;J.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",J.innerHTML=N.map(V=>"<div>"+c(V)+"</div>").join("")}function z(_){x(_),q(_.warnings||[],_.skipped_files||[]),!_.ok&&_.error&&window.showToast&&window.showToast(_.error,"error");const M=_.stats||{},j=_.summary||{},J=M.matched||0,O=(M.gl_debit_only||0)+(M.gl_credit_only||0),b=(M.stmt_withdrawal_only||0)+(M.stmt_deposit_only||0),N=Number(j.formula_diff||0),V=Math.abs(N)<.05;l("brv2-kpi-matched")&&(l("brv2-kpi-matched").textContent=J),l("brv2-kpi-diff")&&(l("brv2-kpi-diff").textContent=d(N)),l("brv2-kpi-unmatched")&&(l("brv2-kpi-unmatched").textContent=O+b);const W=l("brv2-kpi-diff-icon");W&&(W.style.background=V?"#d1fae5":"#fee2e2",W.style.color=V?"#065f46":"#b91c1c");const X=l("brv2-formula-sub");if(X){const pe=window._currentLang||"zh";X.textContent=V?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[pe]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[pe]||"差 ")+d(N)}const de=l("brv2-detail-sub");if(de){const pe=window._currentLang||"zh",fe={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[pe]||"共 {n} 行";de.textContent=fe.replace("{n}",i.length)}function ie(pe,fe,me){const ge=l(pe);ge&&(ge.textContent=(me&&fe>0?"(":"")+d(me?-fe:fe)+(me&&fe>0?")":""))}ie("brf-gl-close",j.gl_closing||0),ie("brf-open-diff",j.opening_diff||0),ie("brf-gl-debit-only",j.gl_debit_only_amount||0,!0),ie("brf-gl-credit-only",j.gl_credit_only_amount||0),ie("brf-stmt-wd-only",j.stmt_withdrawal_only_amount||0,!0),ie("brf-stmt-dep-only",j.stmt_deposit_only_amount||0),ie("brf-calc-close",j.formula_stmt_closing||0),ie("brf-stmt-close",j.stmt_closing||0),l("brf-diff")&&(l("brf-diff").textContent=d(N));const ce=l("brv2-fcell-diff");ce&&ce.classList.toggle("brv2-fcell-diff-ok",V);const ae=l("brv2-export-btn");ae&&(ae.onclick=()=>{o&&y(o.task_id)}),R(j),$(!0),Y()}function Y(){const _=l("brv2-tbody");if(!_)return;const M=i.filter(b=>s==="all"?!0:s==="matched"?b.match_status==="matched":s==="gl_only"?b.match_status.startsWith("gl_"):s==="stmt_only"?b.match_status.startsWith("stmt_"):!0);if(M.length===0){const b={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";_.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${b}</td></tr>`;return}const j=window._currentLang||"zh",J={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[j],O={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[j];_.innerHTML=M.map(b=>{const N=b.match_status,V=b.match_layer;let W="",X="";N==="matched"?(V===1&&(W="matched",X='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),V===2&&(W="matched-l2",X='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),V===3&&(W="matched-l3",X='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):N==="gl_debit_only"||N==="gl_credit_only"?(W="gl-only",X='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(W="stmt-only",X=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[j]||"账单"}</span>`);let de="";return b.stmt_balance_ok===!1&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${c(J)}">⚠</span>`,W+=" brv2-row-warn"),b.stmt_confidence==="low"&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${c(O)}">◌</span>`,W.includes("brv2-row-warn")||(W+=" brv2-row-warn-soft")),`<tr class="${W.trim()}">
              <td>${X}${de}</td>
              <td>${c(m(b.stmt_date))}</td>
              <td title="${c(b.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c(b.stmt_desc)}</td>
              <td class="num">${b.stmt_withdrawal?d(b.stmt_withdrawal):""}</td>
              <td class="num">${b.stmt_deposit?d(b.stmt_deposit):""}</td>
              <td>${c(m(b.gl_date))}</td>
              <td title="${c(b.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c(b.gl_doc_no)}</td>
              <td class="num">${b.gl_debit?d(b.gl_debit):""}</td>
              <td class="num">${b.gl_credit?d(b.gl_credit):""}</td>
              <td>${V?"L"+V:"—"}</td>
            </tr>`}).join("")}async function Z(){const _=localStorage.getItem("mrpilot_token")||"";try{const j=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+_}})).json();te(j.tasks||[])}catch{const j=l("brv2-history-empty"),J=window._currentLang||"zh",O={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[J]||"加载失败";j&&(j.textContent=O,j.style.display="");const b=l("brv2-history-table-wrap");b&&(b.style.display="none")}}const le=10;let re=1;function K(){const _=l("brv2-history-pager"),M=l("brv2-history-pager-info"),j=l("brv2-history-prev"),J=l("brv2-history-next");if(!_)return;if(p.length<=le){_.style.display="none";return}_.style.display="";const O=Math.ceil(p.length/le);M&&(M.textContent=re+" / "+O),j&&(j.disabled=re<=1),J&&(J.disabled=re>=O)}function ee(){const _=l("brv2-history-prev"),M=l("brv2-history-next");_&&!_._brv2Bound&&(_._brv2Bound=!0,_.addEventListener("click",()=>{re>1&&(re--,te(p))})),M&&!M._brv2Bound&&(M._brv2Bound=!0,M.addEventListener("click",()=>{const j=Math.ceil(p.length/le);re<j&&(re++,te(p))}))}function te(_){_!==void 0&&(p=_||[],re=1);const M=p,j=l("brv2-history-empty"),J=l("brv2-history-table-wrap"),O=l("brv2-history-tbody");if(!O)return;const b=window._currentLang||"zh";if(!M.length){const ae={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[b]||"暂无对账记录";j&&(j.textContent=ae,j.style.display=""),J&&(J.style.display="none"),K();return}j&&(j.style.display="none"),J&&(J.style.display="");const N=Math.ceil(M.length/le);re>N&&(re=N);const V=(re-1)*le,W=M.slice(V,V+le),X=localStorage.getItem("mrpilot_token")||"",de='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',ie='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ce='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';O.innerHTML="",W.forEach(ae=>{const pe=Number(ae.formula_diff||0),fe=Math.abs(pe)<.05,me=(ae.stmt_files||"").split(";").map(xe=>xe.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ge=(ae.gl_files||"").split(";").map(xe=>xe.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),be=ae.created_at?String(ae.created_at).slice(0,16).replace("T"," "):"",Ee=document.createElement("tr");Ee.dataset.taskId=ae.id;const Ve=document.createElement("td");Ve.textContent=be;const Te=document.createElement("td");Te.className="glv-history-file",Te.title=me+" + "+ge,Te.textContent=me+" + "+ge;const Ae=document.createElement("td");Ae.className="glv-num",Ae.textContent=(ae.stmt_row_count||0)+" / "+(ae.gl_row_count||0);const lt=document.createElement("td");lt.className="glv-num",lt.textContent=ae.matched_count||0;const ct=document.createElement("td");ct.className="glv-num",ct.textContent=ae.unmatched_gl||0;const dt=document.createElement("td");dt.className="glv-num",dt.textContent=ae.unmatched_stmt||0;const Ue=document.createElement("td");Ue.className="glv-num",Ue.style.color=fe?"#059669":"#dc2626",Ue.textContent=fe?"✓":d(pe);const je=document.createElement("td");je.className="glv-history-actions";const pt=(xe,Mt,$t,Bn)=>{const Ie=document.createElement("button");return Ie.type="button",Ie.title=Mt,Ie.setAttribute("aria-label",Mt),$t&&(Ie.className=$t),Ie.innerHTML=xe,Ie.onclick=In=>{In.stopPropagation(),Bn()},Ie},kn={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[b]||"删除?",_n={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[b]||"加载",xn={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[b]||"导出",En={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[b]||"删除";je.appendChild(pt(de,_n,"",()=>se(ae.id,X))),je.appendChild(pt(ie,xn,"",()=>y(ae.id))),je.appendChild(pt(ce,En,"glv-del",async()=>{await showConfirm(kn,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ae.id,{method:"DELETE",headers:{Authorization:"Bearer "+X}}),Z())})),[Ve,Te,Ae,lt,ct,dt,Ue,je].forEach(xe=>Ee.appendChild(xe)),Ee.style.cursor="pointer",Ee.addEventListener("click",async xe=>{xe.target.closest(".glv-del")||xe.target.closest("button")||await se(ae.id,X)}),O.appendChild(Ee)}),K(),ne()}function ne(){const _=((l("brv2-hist-search")||{}).value||"").trim().toLowerCase(),M=l("brv2-history-tbody");M&&M.querySelectorAll("tr").forEach(j=>{j.dataset.taskId&&(j.style.display=!_||j.textContent.toLowerCase().includes(_)?"":"none")})}async function se(_,M){try{const J=await(await fetch("/api/recon/bank-v2/"+_,{headers:{Authorization:"Bearer "+M}})).json();if(!J.ok)return;o={task_id:J.task_id,...J},i=J.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(O=>O.classList.toggle("active",O.dataset.filter==="all")),z(o)}catch{}}function ue(){if(e){Z();return}e=!0,U("brv2-stmt-zone","brv2-stmt-input","stmt"),U("brv2-gl-zone","brv2-gl-input","gl");const _=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function M(){const V=parseFloat((l("brv2-anchor-stmt-opening")||{}).value),W=parseFloat((l("brv2-anchor-gl-opening")||{}).value),X=l("brv2-anchor-eq"),de=l("brv2-anchor-eq-val");if(!(!X||!de))if(Number.isFinite(V)&&Number.isFinite(W)){const ie=V-W;de.textContent=ie.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),X.style.display=""}else X.style.display="none"}_.forEach(V=>{const W=l(V);W&&(W.addEventListener("input",M),W.addEventListener("input",()=>{const X=W.closest(".brv2-anchor-cell");X&&X.classList.remove("is-prefilled"),k()}))}),T();const j=l("brv2-run-btn");j&&j.addEventListener("click",Q);const J=l("brv2-reset-btn");J&&J.addEventListener("click",()=>{o=null,i=[],n=[],a=[],f("stmt"),f("gl"),P(),$(!1);const V=l("brv2-acct-select");V&&(V.style.display="none"),_.forEach(de=>{const ie=l(de);if(ie){ie.value="";const ce=ie.closest&&ie.closest(".brv2-anchor-cell");ce&&ce.classList.remove("is-prefilled")}});const W=l("brv2-anchor-eq");W&&(W.style.display="none");const X=l("brv2-anchor-prefill-banner");X&&X.classList.remove("show")});const O=l("brv2-new-btn");O&&O.addEventListener("click",()=>{o=null,i=[],n=[],a=[],f("stmt"),f("gl"),P(),$(!1)});const b=l("brv2-filter-tabs");b&&b.addEventListener("click",V=>{V.stopPropagation();const W=V.target.closest(".brv2-filter-btn");W&&(s=W.dataset.filter,b.querySelectorAll(".brv2-filter-btn").forEach(X=>X.classList.toggle("active",X===W)),Y())}),B(),ee();const N=l("brv2-hist-search");N&&N.addEventListener("input",ne),Z(),P(),window._brv2LoadHistory=Z,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(V=>V.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){P(),f("stmt"),f("gl"),o&&z(o),te()}})}window._loadBankReconV2Panel=function(_){const M=_?document.getElementById(_):null;M&&M.id!=="recon-pane-bank"&&(M.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),ue()},document.addEventListener("DOMContentLoaded",()=>{l("brv2-run-btn")&&ue()}),window._bankReconV2Init=ue})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const d=document.getElementById("general-tz"),m=document.getElementById("general-date"),c=document.getElementById("general-number");if(!(!d||!m||!c))try{d.value=localStorage.getItem(n)||s.tz,m.value=localStorage.getItem(a)||s.date,c.value=localStorage.getItem(o)||s.number}catch{d.value=s.tz,m.value=s.date,c.value=s.number}}async function r(){const d=document.getElementById("btn-save-general"),m=document.getElementById("general-save-msg");if(!d)return;const c=d.innerHTML;d.disabled=!0,d.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",m&&(m.textContent="",m.classList.remove("error"));try{const u=(document.getElementById("general-tz")||{}).value||s.tz,f=(document.getElementById("general-date")||{}).value||s.date,w=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,u),localStorage.setItem(a,f),localStorage.setItem(o,w)}catch{}window._pearnlyGeneral={tz:u,date_format:f,number_format:w},m&&(m.textContent=t("msg-saved")||"已保存")}catch{m&&(m.textContent=t("msg-save-failed")||"保存失败",m.classList.add("error"))}finally{d.disabled=!1,d.innerHTML=c,setTimeout(function(){m&&(m.textContent="")},3e3)}}function p(){const d=document.getElementById("btn-save-general");if(!d){setTimeout(p,200);return}d._pearnlyGenBound||(d._pearnlyGenBound=!0,d.addEventListener("click",r),i())}function l(){i();const d=document.getElementById("general-lang");if(d){const m=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";d.value=m}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",p):p(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",l)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(p){const l=p.dataset.collapsible;r[l]?p.classList.add("collapsed"):p.classList.remove("collapsed")})}function i(r){const p=a();p[r]=!p[r],o(p),s()}(function(){const p=a();let l=!1;p.sales===void 0&&(p.sales=!1,l=!0),p.expense===void 0&&(p.expense=!0,l=!0),l&&o(p)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const p=n[r];if(!p)return;const l=a();l[p]&&(l[p]=!1,o(l),s())}})();const eo=`
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
    </div>`;function Dt(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=eo;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,Dt();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const i=o.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let we=[];window._erpEndpoints=we;let Oe=null;async function it(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}we=(await e.json()).items||[],window._erpEndpoints=we,un()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return it()};async function pn(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const p=[];p.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&p.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&p.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&p.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=p.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function un(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&we.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(we.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=we.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:we.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),pn(),e.innerHTML=we.map(s=>{const i=s.config||{},r=escapeHtml(i.url||"");i._token_set;const p=s.enabled!==!1,l=[];s.is_default&&l.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&l.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),p||l.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const d=[];return s.success_count>0&&d.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&d.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(s.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(s.name)}</div>
                        <div class="ep-badges">${l.join("")}</div>
                    </div>
                    <div class="ep-url">${r||"-"}</div>
                    <div class="ep-stats">${d.join(" · ")}</div>
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=we.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,p=document.createElement("div");p.className="erp-limit-hint",r==="free"?p.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:p.textContent=t("ep-plus-limit-hint",{used:s,limit:i}),e.appendChild(p)}}function to(e){Oe=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),p=document.getElementById("ep-auto-push"),l=document.getElementById("ep-test-result");l.style.display="none",l.textContent="";const d=document.getElementById("ep-save-error");if(d&&d.remove(),e){const c=we.find(u=>u.id===e);if(!c)return;o.value=c.name||"",s.value=(c.config||{}).url||"",i.value=(c.config||{})._token_set&&c.config.token||"",i.placeholder=(c.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!c.is_default,p.checked=!!c.auto_push}else o.value="",s.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=we.length===0,p.checked=!0;const m=p.closest(".form-switch-row");if(p.disabled=!1,m){m.classList.remove("disabled-plus"),m.title="",m.style.cursor="",m.onclick=null;const c=m.querySelector(".plus-badge");c&&c.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function fn(){document.getElementById("endpoint-modal").style.display="none",Oe=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function mn(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function vn(){const e=document.getElementById("ep-name").value.trim(),n=mn(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:i}}async function no(){const{url:e,config:n}=vn(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function ao(){const e=vn(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){qt(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let i;if(Oe?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(Oe)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const p=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof p=="string"?p:JSON.stringify(p))}fn(),showToast(t("ep-save-ok")),it()}catch(i){qt(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function qt(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function oo(e){const n=we.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),it()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=it;window.loadErpTodayStats=pn;window.renderErpEndpointsList=un;window.openEndpointModal=to;window.closeEndpointModal=fn;window.saveEndpoint=ao;window.deleteEndpoint=oo;window.testEndpointConnection=no;window._sanitizeUrl=mn;async function hn(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function so(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){hn(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const i=s.dataset.receiptAction;i==="retry"?window.retryPushLog(s.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(R=>R.id===o.endpoint_id),i=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),p=new Date(o.created_at).toLocaleString(),l=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),d=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),m=o.response_body||t("erp-receipt-no-tech"),c=o.status==="success";let u=typeof m=="string"?m:JSON.stringify(m,null,2);if(c)try{const R=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},B=R.row_count||(Array.isArray(R.imported_rows)?R.imported_rows.length:0);B>0&&(u=t("log-push-rows").replace("{n}",String(B)))}catch{}const f=(o.external_doc_no||"").trim(),w=(o.external_url||"").trim(),S=(o.external_doc_hint||"").trim(),E=(o.ocr_buyer_name||"").trim()||o.client_name||"-",v=o.seller_name||"-",h=o.push_type==="id_card";let C="-";const L=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(L)&&(C=L.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const A=c?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),T=c?"✓":"✗",k=[],g=(R,B)=>{k.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(R)}</span>
                    <span class="erp-receipt-val">${B}</span>
                </div>`)};if(g(h?t("erp-log-col-booking"):t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),g(t("erp-receipt-erp-name"),escapeHtml(i)),c){let R;f?R=`<strong class="erp-receipt-docno">${escapeHtml(f)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(f)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:R=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,g(t("erp-receipt-doc-no"),R)}h||g(t("erp-receipt-client"),escapeHtml(E)),g(h?t("erp-log-col-customer"):t("erp-receipt-seller"),escapeHtml(v)),c&&g(t("erp-receipt-amount"),escapeHtml(C)),g(t("erp-receipt-time"),escapeHtml(p)),g(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let I="";c&&w?I=`<a class="erp-receipt-primary-btn" href="${escapeHtml(w)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:c&&f&&(I=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(f)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let H="";if(c&&f&&S){const R="erp-receipt-hint-"+S,B=t(R);B&&B!==R&&(H=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(B)}</span></div>`)}let D="";if(!c){const R=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),B=R?R[0]:"",P=typeof currentLang=="string"&&currentLang||window._currentLang||"th",G=o.error_friendly&&o.error_friendly[P]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),F=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),Q=!!(o.history_id&&o.endpoint_id),oe=[];oe.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),F&&oe.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),Q&&oe.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),D=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${B?`<div class="erp-receipt-errcode">${escapeHtml(B)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(G)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${oe.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${c?"ok":"fail"}">${T}</span>
                    ${escapeHtml(A)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(l)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${k.join("")}
            </div>

            ${H}
            ${I?`<div class="erp-receipt-primary-wrap">${I}</div>`:""}
            ${D}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t("erp-receipt-tech-toggle"))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${o.http_status||"-"}</span>
                    <span>${o.elapsed_ms}ms</span>
                    <span>${escapeHtml(t("log-detail-attempt",{n:o.attempt||1}))}</span>
                </div>
                <div class="log-detail-section" style="margin-top:12px;">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-request-human"))}</div>
                    <pre>${escapeHtml(d)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(u)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=hn;window.showLogDetail=so;const io=`
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
    `;ke("endpoint-modal",io);let qe={key:"all",val:""},Ne="",mt=!1,Be=new Set;window._erpSelected=Be;async function ro(){const e=document.getElementById("erp-logs-erp-select");if(!(!e||mt)){mt=!0;try{let n=window._erpEndpoints;if(!Array.isArray(n)||n.length===0){const s=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(s.ok){const i=await s.json();n=i&&(i.items||i)||[]}}Array.isArray(n)||(n=[]);const a=new Set,o=[];n.forEach(s=>{const i=(s&&s.adapter||"").toLowerCase();!i||a.has(i)||(a.add(i),o.push({val:i,label:s&&s.name||i}))}),e.innerHTML=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`+o.map(s=>`<option value="${escapeHtml(s.val)}"${s.val===Ne?" selected":""}>${escapeHtml(s.label)}</option>`).join("")}catch{mt=!1}}}async function $e(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats(),ro();try{const a=new URLSearchParams({limit:"30"});qe.key==="status"&&a.set("status",qe.val),qe.key==="trigger"&&a.set("trigger",qe.val),Ne&&a.set("adapter",Ne);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(f){return f.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){$e(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const r=i.filter(function(f){var w=f.status==="failed"&&f.next_retry_at&&new Date(f.next_retry_at).getTime()>Date.now()-6e4;return!w}).map(function(f){return f.id}),p=Ne==="mrerp_dms",l=p?t("erp-log-col-booking"):t("erp-log-col-invoice"),d=p?t("erp-log-col-customer"):t("erp-log-col-seller"),m=p?t("erp-log-col-idcard"):t("erp-log-col-client"),c='<div class="erp-log-row erp-log-row-header" data-log-header>'+(r.length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(l)}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(m)}</span><span class="log-seller">${escapeHtml(d)}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=c+i.map(f=>{const w=new Date(f.created_at),S=`${String(w.getMonth()+1).padStart(2,"0")}-${String(w.getDate()).padStart(2,"0")} ${String(w.getHours()).padStart(2,"0")}:${String(w.getMinutes()).padStart(2,"0")}`,E=f.status==="failed"&&f.next_retry_at&&new Date(f.next_retry_at).getTime()>Date.now()-6e4;let v,h,C;f.status==="pending"?(v="retrying",h="⟳",C=t("erp-status-pending")):f.status==="success"?(v="ok",h="✓",C=t("erp-status-success")):f.status==="skipped_dup"?(v="skipped",h="⏭",C=t("erp-status-skipped")):E?(v="retrying",h="↻",C=t("erp-status-retrying")):(v="fail",h="✗",C=t("erp-status-failed"));let L;f.trigger==="auto"?L=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:f.trigger==="retry"?L=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:L=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;const A=f.push_type==="id_card",T=A?`<span class="log-tag log-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span>`:"",k=f.error_friendly&&(f.error_friendly[currentLang]||f.error_friendly.en)||"";let g="";const I=f.retry_count||0,H=f.max_retries||3;if(E){const y=new Date(f.next_retry_at).getTime()-Date.now(),q=Math.max(0,Math.round(y/6e4)),z=q<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:q});g=`${t("erp-retry-attempt",{n:I,max:H})} · ${z}`}else f.status==="failed"&&I>=H&&!f.next_retry_at&&(g=t("erp-retry-exhausted",{n:I}));const D=f.status==="failed"&&!E?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(f.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",R=!E,B=Be.has(f.id)?"checked":"",P=R?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(f.id)}" ${B}>`:'<span class="erp-log-cb-spacer"></span>',U=(f.ocr_buyer_name||"").trim()||(f.client_name||"").trim(),G=A?`<span class="log-client" title="${escapeHtml(t("erp-log-col-idcard"))}">${f.id_card_tail?"••••"+escapeHtml(f.id_card_tail):"—"}</span>`:U?`<span class="log-client" title="${escapeHtml(U)}">${escapeHtml(U.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,F=A?'<span class="log-workspace log-workspace-unresolved">—</span>':f.workspace_name?`<span class="log-workspace">${escapeHtml((f.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,Q=f.endpoint_name?`<span class="log-erp">${escapeHtml((f.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,oe=(f.external_doc_no||"").trim(),$=(f.external_url||"").trim();let x;return $?x=`<span class="log-doc"><a href="${escapeHtml($)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(oe||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:oe?x=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(oe)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(oe.substring(0,18))}</span>`:f.status==="success"?x=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:x='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${v}" data-log-detail="${escapeHtml(f.id)}">
                    ${P}
                    <span class="log-time">${S}</span>
                    <span class="log-status" title="${escapeHtml(C+(g?" · "+g:"")+(k?" · "+k:""))}">${h}</span>
                    ${L}${T}
                    <span class="log-invoice"${A?` title="${escapeHtml(t("erp-log-col-booking"))}"`:""}>${escapeHtml(f.invoice_no||"-")}</span>
                    ${F}
                    ${G}
                    <span class="log-seller"${A?` title="${escapeHtml(t("erp-log-col-customer"))}"`:""}>${escapeHtml((f.seller_name||"").substring(0,20))}</span>
                    ${Q}
                    ${x}
                    <span class="log-http">HTTP ${f.http_status||"-"}</span>
                    <span class="log-elapsed">${f.elapsed_ms}ms</span>
                    <span class="log-actions">${D}</span>
                </div>
            `}).join("");const u=new Set(i.map(f=>f.id));for(const f of Array.from(Be))u.has(f)||Be.delete(f);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function gn(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),$e(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),gn(s.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const m=i.dataset.logCb;i.checked?Be.add(m):Be.delete(m),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const m=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(u){u.checked=m;const f=u.dataset.logCb;m?Be.add(f):Be.delete(f)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),Be.clear(),document.querySelectorAll(".erp-log-cb").forEach(m=>{m.checked=!1}),window._refreshErpBatchBar();return}const p=n.target.closest("[data-log-detail]");if(p){if(n.target.closest("[data-log-cb]"))return;const m=n.target.closest("[data-copy-doc]");if(m){n.stopPropagation(),window.copyErpDocNo(m.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(p.dataset.logDetail);return}const l=n.target.closest(".chip-filter");if(l){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(m=>m.classList.remove("active")),l.classList.add("active"),qe={key:l.dataset.filterKey,val:l.dataset.filterVal},$e();return}if(n.target.closest("#btn-refresh-logs")){const m=n.target.closest("#btn-refresh-logs");m.classList.add("spinning"),setTimeout(()=>m.classList.remove("spinning"),600),$e();return}const d=n.target.closest(".auto-nav-item");if(d&&d.dataset.autoTab){switchAutomationTab(d.dataset.autoTab);return}}),document.addEventListener("change",n=>{n.target&&n.target.id==="erp-logs-erp-select"&&(Ne=n.target.value||"",$e())})})();window.loadErpLogs=$e;window.retryPushLog=gn;function bn(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function yn(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),i=o.failed&&o.failed>0?"warn":"success";showToast(s,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function wn(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),yn()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),wn()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),bn()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=bn;window._runErpBatchRetry=yn;window._runErpBatchDelete=wn;(function(){let e=null,n=!1;function a(){if(e)return e;const p=document.createElement("div");p.id="line-email-modal",p.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",p.innerHTML=`
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
        `,document.body.appendChild(p),e=p;const l=p.querySelector("#line-email-input"),d=p.querySelector("#line-email-submit-btn"),m=p.querySelector("#line-email-err");async function c(){m.textContent="";const u=(l.value||"").trim().toLowerCase();if(!u||u.indexOf("@")<0||u.split("@")[1].indexOf(".")<0){m.textContent=t("line-email-err-invalid");return}d.disabled=!0,d.style.opacity="0.6";try{const f=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:u})});if(!f.ok)throw new Error("http_"+f.status);const w=await f.json();w.token&&localStorage.setItem("mrpilot_token",w.token),typeof showToast=="function"&&showToast(w.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{m.textContent=t("line-email-err-failed"),d.disabled=!1,d.style.opacity="1"}}return d.addEventListener("click",c),l.addEventListener("keydown",function(u){u.key==="Enter"&&c()}),p}function o(){if(!e)return;const p=e.querySelector("#line-email-title-h"),l=e.querySelector("#line-email-sub-p"),d=e.querySelector("#line-email-input"),m=e.querySelector("#line-email-submit-btn");p&&(p.textContent=t("line-email-title")),l&&(l.textContent=t("line-email-sub")),d&&(d.placeholder=t("line-email-placeholder")),m&&(m.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const p=e.querySelector("#line-email-input");p&&setTimeout(function(){p.focus()},100)}async function i(){const p=localStorage.getItem("mrpilot_token");if(p)try{const l=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+p}});if(!l.ok)return;const d=await l.json();d&&d.needs_email&&s()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(m){let c=0;return m.length>=8&&c++,m.length>=12&&c++,/[a-zA-Z]/.test(m)&&/\d/.test(m)&&c++,/[^a-zA-Z0-9]/.test(m)&&c++,Math.min(3,c)}function n(m,c){const u=document.getElementById("cpw-msg");u&&(u.textContent=m,u.className="cpw-msg "+(c||""))}function a(m){return typeof t=="function"?t(m):m}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(c=>{const u=document.getElementById(c);u&&(u.value="",u.setAttribute("readonly","readonly"))});const m=document.getElementById("cpw-strength-bar");m&&(m.style.width="0%",m.className="cpw-strength-bar"),n("","")}async function i(){const m=document.getElementById("btn-change-pw"),c=document.getElementById("cpw-old"),u=document.getElementById("cpw-new"),f=document.getElementById("cpw-confirm"),w=document.getElementById("cpw-strength-bar");if(!m||!c||!u||!f)return;const S=c.value,E=u.value,v=f.value;if(!S||!E||!v){n(a("settings-change-pw-empty"),"error");return}if(E.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(E)&&/\d/.test(E))){n(a("settings-change-pw-too-weak"),"error");return}if(E!==v){n(a("settings-change-pw-mismatch"),"error");return}m.disabled=!0;const h=m.textContent;m.textContent=a("settings-change-pw-submitting"),n("","");try{const C=localStorage.getItem("mrpilot_token"),L=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+C},body:JSON.stringify({old_password:S,new_password:E})}),A=await L.json().catch(()=>({}));if(L.ok&&A.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),c.value="",u.value="",f.value="",w&&(w.style.width="0%",w.className="cpw-strength-bar");else{const T=A.detail||"";let k=a("settings-change-pw-success");T==="wrong_old_password"?k=a("settings-change-pw-wrong-old"):T==="password_too_short"?k=a("settings-change-pw-too-short"):T==="password_too_weak"?k=a("settings-change-pw-too-weak"):k=T||"Error",n(k,"error")}}catch(C){console.error("change_password",C),n("Network error","error")}finally{m.disabled=!1,m.textContent=h}}function r(){o||(o=!0,document.addEventListener("click",m=>{if(!m.target||!m.target.closest)return;const c=m.target.closest(".cpw-eye");if(c){const u=document.getElementById(c.dataset.target);u&&(u.type=u.type==="password"?"text":"password");return}if(m.target.closest("#cpw-forgot-link")){m.preventDefault(),p();return}if(m.target.closest("#btn-change-pw")){i();return}m.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",m=>{if(m.target&&m.target.id==="cpw-new"){const c=document.getElementById("cpw-strength-bar");if(!c)return;const u=e(m.target.value),f=["0%","33%","66%","100%"],w=["","weak","medium","strong"];c.style.width=f[u],c.className="cpw-strength-bar "+w[u]}}),document.addEventListener("focusin",m=>{m.target&&["cpw-old","cpw-new","cpw-confirm"].includes(m.target.id)&&m.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function p(){const m=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),c=m&&m.username?m.username:"",u=l(c);let f=document.getElementById("cpw-forgot-overlay");f&&f.remove(),f=document.createElement("div"),f.id="cpw-forgot-overlay",f.className="cpw-forgot-overlay",f.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${d(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${d(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${d(u)}</div>
                    <p class="cpw-forgot-tip">${d(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${d(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${d(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(f);const w=()=>f.remove();f.querySelector("#cpw-forgot-close").addEventListener("click",w),f.querySelector("#cpw-forgot-cancel").addEventListener("click",w),f.addEventListener("click",S=>{S.target===f&&w()}),f.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const S=f.querySelector("#cpw-forgot-send"),E=f.querySelector("#cpw-forgot-msg");S.disabled=!0;const v=S.textContent;S.textContent=a("cpw-forgot-sending");try{const h=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:c})}),C=await h.json().catch(()=>({}));h.ok?(E.textContent=a("cpw-forgot-success"),E.className="cpw-forgot-msg success",S.style.display="none",f.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(E.textContent=C.detail||a("cpw-forgot-fail"),E.className="cpw-forgot-msg error",S.disabled=!1,S.textContent=v)}catch{E.textContent=a("cpw-forgot-fail"),E.className="cpw-forgot-msg error",S.disabled=!1,S.textContent=v}})}function l(m){if(!m||!m.includes("@"))return m||"";const[c,u]=m.split("@");return c.length<=2?c+"****@"+u:c.slice(0,2)+"****@"+u}function d(m){return m==null?"":String(m).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),p=r&&r.detail;let l="";if(typeof p=="string"?l=p:p&&typeof p=="object"&&(l=p.code||""),console.warn("[heartbeat] session revoked",l),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),l==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const d=l==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(d),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function rt(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),i=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const p=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",l=r.is_active===!1?"team-status-off":"team-status-on",d=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",m=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${l}"></span>
                            <span>${escapeHtml(d)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(p)}</span>
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function lo(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),p=document.getElementById("add-emp-submit"),l=(o.value||"").trim(),d=(s.value||"").trim(),m=i.value||"";if(r.textContent="",r.classList.remove("error"),!l||l.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(l)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(d&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(m.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(m)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(m)&&/\d/.test(m))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}p.disabled=!0,p.textContent=t("msg-saving")||"保存中...";try{const c={username:l,password:m};d&&(c.email=d);const u=await apiPost("/api/team/employees",c),f=u?await u.json().catch(()=>({})):{};if(u&&u.ok&&f&&f.ok){showToast(t("team-added")||"员工已添加","success"),n(),rt();return}const w=f&&f.detail||"unknown",S={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=S[w]||(t("team-create-failed")||"创建失败")+" ("+w+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{p.disabled=!1,p.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function co(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){rt();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function po(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),rt();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function uo(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const p=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",l=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(p.replace("{ch}",l),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),lo();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),co(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),po(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),uo(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=rt;function fo(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=fo;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
