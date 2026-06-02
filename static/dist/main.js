(function(){const n=[];function a(s){try{n.push(Object.assign({ts:Date.now()},s)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(s)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(s){s.target&&s.target!==window&&(s.target.src||s.target.href)||a({type:"js_error",summary:String(s.message||"JS Error").slice(0,200),detail:{file:s.filename||"",line:s.lineno||0,col:s.colno||0,stack:s.error&&s.error.stack?String(s.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(s){const i=s.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const o=window.fetch;typeof o=="function"&&(window.fetch=function(){const s=arguments,i=Date.now(),r=typeof s[0]=="string"?s[0]:s[0]&&s[0].url||"?",c=s[1]&&s[1].method||"GET",l=String(r).split("?")[0];return o.apply(this,s).then(function(p){const f=Date.now()-i;if(p.ok)f>2500&&a({type:"api_slow",summary:c+" "+l+" → 慢 "+f+"ms",detail:{url:r,method:c,status:p.status,elapsed_ms:f}});else{let d="";try{p.clone().text().then(function(m){d=String(m||"").slice(0,500),a({type:"api_error",summary:c+" "+l+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:c,status:p.status,elapsed_ms:f,body_preview:d}})}).catch(function(){a({type:"api_error",summary:c+" "+l+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:c,status:p.status,elapsed_ms:f,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:c+" "+l+" → "+p.status+" ("+f+"ms)",detail:{url:r,method:c,status:p.status,elapsed_ms:f}})}}return p}).catch(function(p){const f=Date.now()-i;throw a({type:"api_fail",summary:c+" "+l+" → 网络失败 ("+f+"ms)",detail:{url:r,method:c,elapsed_ms:f,error:String(p&&p.message||p)}}),p})}),["error","warn"].forEach(function(s){const i=console[s];typeof i=="function"&&(console[s]=function(){try{const r=[];for(let c=0;c<arguments.length;c++){const l=arguments[c];if(typeof l=="string")r.push(l);else if(l&&l instanceof Error)r.push(l.message);else try{r.push(JSON.stringify(l).slice(0,300))}catch{r.push(String(l))}}a({type:"console_"+s,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(o=>o.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function ho(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function go(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function bo(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function Ut(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const o in n)a=a.replace("{"+o+"}",n[o]);return a}function yo(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function wo(e,n){n=n||14;const o={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${o}</svg>`}function Gt(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},o={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},s=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[s]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[s]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+o[s]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function Kt(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function ko(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...Kt()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),o=a&&a.detail;let s="";if(typeof o=="string"?s=o:o&&typeof o=="object"&&(s=o.code||""),n.status===401||typeof s=="string"&&s.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,o),localStorage.removeItem("mrpilot_token"),s==="auth.session_revoked")Gt();else{const c=s==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Ut(c),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=o,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function xo(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...Kt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.clone().json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Gt();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Ut(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function _o(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...Kt()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Gt();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Ut(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const o=await a.json().catch(()=>({}));return{ok:a.ok&&o.ok!==!1,...o}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=ko;window.apiPost=xo;window.t=Ut;window.escapeHtml=yo;window.svgIcon=wo;window._showSessionRevokedModal=Gt;window._wsHeader=Kt;window.apiPut=_o;window.getMaxFiles=ho;window.getMaxPagesPerFile=go;window.getMaxMbPerFile=bo;function be(e,n){const a=document.getElementById(e);if(!(!a||a.dataset.wbInjected==="1")){a.innerHTML=n,a.dataset.wbInjected="1";try{const o=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",s=window.I18N;if(!s||!s[o])return;a.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");s[o][r]&&(i.textContent=s[o][r])}),a.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");s[o][r]&&(i.placeholder=s[o][r])})}catch{}}}const Eo=`
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
    `;be("page-ocr",Eo);const Bo=`
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
`,Io=`
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
`;be("topbar",Bo);be("sidebar",Io);function vn(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const o=document.getElementById("general-lang");o&&(o.value=e);const s=document.getElementById("col-conf-th");s&&s.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&hn(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function Lo(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",s=>{s.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(s)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});Lo("lang-dropdown",e=>vn(e.dataset.lang));const ma=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","receivables","reconcile","cloud","test-center"];function va(e){ma.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(o=>o.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(o=>{o.classList.toggle("active",o.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function ha(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){return!i||typeof i!="string"||(i=i.trim(),!i)?null:i.includes("@")&&i.indexOf("@")>0&&i.indexOf(".")>i.indexOf("@")?i.split("@")[0]:i}const o=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let s=null;for(const i of o){const r=a(i);if(r){s=r;break}}s||(s=t("brand-workspace-fallback")||"我的工作台"),e.textContent=s,e.title=s,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",s,"· _userInfo fields:",Object.keys(n))}function hn(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function ga(){try{const[e,n,a,o]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(s=>s.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,o&&(window._planState=o),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const s=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(s&&!i){window.location.replace("/home");return}if(!s&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=s}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,o&&(window._planState=o),ha(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(s){console.error("[nav-ia phase1] render avatar menu",s)}hn(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const s=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(s&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(s&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(s){console.error("force-pw init",s)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(s){console.error("onboarding init",s)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(s){console.error("settings forms init",s)}}catch(e){console.error(e)}}function Co(){let e=document.getElementById("offline-banner");e||(e=document.createElement("div"),e.id="offline-banner",e.className="offline-banner",e.style.display="none",document.body.insertBefore(e,document.body.firstChild));function n(){navigator.onLine===!1?(e.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",e.classList.remove("is-online"),e.classList.add("is-offline"),e.style.display="flex"):e.classList.contains("is-offline")?(e.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",e.classList.remove("is-offline"),e.classList.add("is-online"),setTimeout(()=>{e.style.display="none",e.classList.remove("is-online")},2e3)):e.style.display="none"}window.addEventListener("online",n),window.addEventListener("offline",n),n()}window.applyLang=vn;window.routeTo=va;window.loadAll=ga;window.renderBrandWorkspace=ha;window.updateUploadHint=hn;window.installNetworkBanner=Co;try{vn(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");va(ma.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);ga();const ba="mrpilot_sidebar_collapsed";localStorage.getItem(ba)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(ba,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const o=document.querySelectorAll("#page-integrations .int-top-tab"),s=document.querySelectorAll("#page-integrations .int-top-panel");if(o.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),s.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),o&&o.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const o=a.target.closest("#page-integrations .int-top-tab");if(o){const i=o.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const o=document.querySelector(".auto-content");o&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(s){s.style.display="",o.appendChild(s)})}window.openIntegrationDrawer=function(a,o){const s=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),c=document.getElementById("int-drawer-body");if(!s||!c)return;e(),s.dataset.currentTab=a||"",r&&(r.textContent=o||""),c.innerHTML="";var l={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},p=l[a]||a;const f=document.querySelector('.auto-panel[data-auto-panel="'+p+'"]');f?(f.style.display="block",c.appendChild(f)):c.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',s.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var d={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(d[a])try{d[a]()}catch(u){console.warn("[int-drawer] loader error",u)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(u){console.warn("[int-drawer] ERP load error",u)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),o&&(o.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),o=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),o&&o.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(s){s.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(s=>{s.addEventListener("click",()=>switchSettingsTab(s.dataset.tab))});let o=null;try{o=localStorage.getItem("mrpilot_settings_tab")}catch{}if(o){const s=document.querySelector(`.settings-tab[data-tab="${o}"]`);if(s&&s.style.display!=="none"){switchSettingsTab(o);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),o=document.getElementById("btn-save-company");if(!a&&!o){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),o&&o.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let At=null;function So(){rn(),At=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&rn()}catch{}},1e4)}function rn(){At&&(clearInterval(At),At=null)}window.startEnginePolling=So;window.stopEnginePolling=rn;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target.closest("[data-rd-action]");if(n){const s=n.dataset.rdAction,i=n.dataset.rdSide;s==="verify"?callRdVerify(i):s==="sync"&&callRdSync(i);return}if(e.target.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=e.target.closest("[data-archive-copy]");if(o){const s=o.dataset.archiveCopy;navigator.clipboard?.writeText(s).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const Un=document.getElementById("btn-custom-template");Un&&Un.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});const To=`
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
    `,Mo=`
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
`;be("pearnly-confirm-modal",To);be("confirm-modal",Mo);window.pearnlyConfirm=function(e,n){return new Promise(function(a){const o=document.getElementById("pearnly-confirm-modal"),s=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),c=document.getElementById("pearnly-confirm-cancel"),l=document.getElementById("pearnly-confirm-close");if(!o||!i||!r||!c){a(window.confirm(e));return}s&&(s.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",o.style.display="flex";function p(h){o.style.display="none",r.removeEventListener("click",f),c.removeEventListener("click",d),l&&l.removeEventListener("click",d),o.removeEventListener("click",u),document.removeEventListener("keydown",m),a(h)}function f(){p(!0)}function d(){p(!1)}function u(h){h.target===o&&p(!1)}function m(h){h.key==="Escape"?p(!1):h.key==="Enter"&&p(!0)}r.addEventListener("click",f),c.addEventListener("click",d),l&&l.addEventListener("click",d),o.addEventListener("click",u),document.addEventListener("keydown",m),setTimeout(function(){try{c.focus()}catch{}},50)})};const $o=`
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

`,Ho=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=$o+Ho,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Ao=`
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

`,jo=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Ao+jo,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function Po(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function Do(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function qo(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function Ro(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function Fo(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let c=null;const l=()=>{c&&(clearTimeout(c),c=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(c=setTimeout(l,r)),l}window.showAlert=Po;window.hideAlerts=Do;window._humanizeBackendError=qo;window.humanizeError=Ro;window.showToast=Fo;function zo(e,n){return n=n||{},new Promise(a=>{const o=document.getElementById("confirm-modal"),s=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),c=document.getElementById("confirm-modal-close"),l=document.getElementById("confirm-modal-title");if(!o||!s||!i||!r){a(!1);return}l.textContent=n.title||t("confirm-default-title");const p=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const m=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),h=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");s.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${m}</div>
                <input type="text" id="${p}" placeholder="${h}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else s.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",o.style.display="flex";const f=m=>{o.style.display="none",i.onclick=null,r.onclick=null,c.onclick=null,o.onclick=null,document.removeEventListener("keydown",u),n.promptInput&&(s.innerHTML=""),r.style.display="",a(m)},d=()=>{const m=p?document.getElementById(p):null;return m?m.value:""},u=m=>{m.key==="Escape"?f(n.promptInput?null:!1):m.key==="Enter"&&f(n.promptInput?d():!0)};i.onclick=()=>f(n.promptInput?d():!0),r.onclick=()=>f(n.promptInput?null:!1),c.onclick=()=>f(n.promptInput?null:!1),o.onclick=m=>{m.target===o&&f(n.promptInput?null:!1)},document.addEventListener("keydown",u),setTimeout(()=>{if(n.promptInput){const m=document.getElementById(p);m&&m.focus()}else i.focus()},50)})}window.showConfirm=zo;function No(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof ln=="function"&&ln()}catch(n){console.warn("settings tab side effect failed:",n)}}}function Oo(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function Vo(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function Uo(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function ln(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}Go(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function Go(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
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
    `}window.switchSettingsTab=No;window.fillSettingsForms=Oo;window.saveProfile=Vo;window.saveCompany=Uo;window.renderSettings=ln;function Jt(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function gn(e){return e=e||_userInfo,!!e&&(e.role==="owner"||Jt(e))}function ya(e){return e=e||_userInfo,!!e&&e.role==="member"&&!Jt(e)}function Ko(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!Jt(e)}function wa(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function ka(e){return ya(e)}function Jo(e){return gn(e)}function Wo(e){return gn(e)&&wa(e)}window.isMoneyHidden=ka;window.isSuperAdmin=Jt;window.isOwner=gn;window.isEmployee=ya;window.isTrial=Ko;window.isLifetime=wa;window.shouldHideMoney=ka;window.canManageTeam=Jo;window.canManageApiKey=Wo;function Yo(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,c;if(o===0)r="danger",c=t("quota-banner-exhausted");else if(s>=90)r="danger",c=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",c=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(c)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const l=e.querySelector(".quota-banner-close");l&&l.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function Xo(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const c=document.querySelector('.settings-tab[data-tab="team"]');c&&(c.style.display=a?"":"none");const l=document.querySelector('.settings-panel[data-settings-panel="team"]');l&&(l.dataset.permHidden=a?"0":"1");const p=document.querySelector('.settings-tab[data-tab="api"]');p&&(p.style.display=o||isSuperAdmin(e)?"":"none");const f=document.querySelector('.settings-tab[data-tab="plan"]');f&&(f.style.display=n?"none":"");const d=document.querySelector('.settings-tab[data-tab="company"]');d&&(d.style.display=n?"none":"");const u=document.getElementById("info-bar");u&&(u.style.display=n?"none":"");const m=document.getElementById("trial-banner");m&&n&&(m.style.display="none");const h=document.getElementById("plan-banner");h&&n&&(h.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(_=>{_.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const _=document.querySelector(".settings-tab.active");_&&_.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(_){console.warn("[v118.12.3] failed to fix active tab:",_)}if(window.PEARNLY_ADMIN_MODE){const _=document.getElementById("admin-mode-banner");_&&(_.style.display="flex"),document.querySelectorAll(".nav-item").forEach(v=>{v.classList.contains("nav-admin-only")||(v.style.display="none")}),document.querySelectorAll(".nav-group").forEach(v=>{v.classList.contains("nav-group-admin-only")||(v.style.display="none")});const y=document.getElementById("client-switcher");y&&(y.style.display="none"),document.body.classList.add("admin-mode");const b=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(v=>{const L=v.dataset.tab;L&&!b.includes(L)&&(v.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(v=>{const L=v.dataset.pane;L&&!b.includes(L)&&(v.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(v=>{const L=v.querySelectorAll(".settings-tab");Array.from(L).some(x=>x.style.display!=="none")||(v.style.display="none")})}}function Zo(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
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
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=Yo;window.applySidebarVisibility=Xo;window.renderInfoBar=Zo;async function xa(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function _a(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Pt(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function Ve(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function Qo(e){const a=Pt(e==="seller"?"seller_tax":"buyer_tax");Ve(e,t("rd-verifying"),"loading");const o=await xa("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){Ve(e,t(_a(o.error)),"error");return}o.data&&o.data.valid?Ve(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):Ve(e,t("rd-status-invalid"),"invalid")}async function es(e){const a=Pt(e==="seller"?"seller_tax":"buyer_tax");Ve(e,t("rd-syncing"),"loading");const o=await xa("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){Ve(e,t(_a(o.error)),"error");return}Ve(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),ts(e,o.data)}}function ts(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=Pt(a),i=Pt(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==i&&r.push({field:o,label:t("rd-field-address"),current:i,official:n.address});const c=[];n.branch_label&&c.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&c.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let l=document.getElementById("rd-sync-modal");if(l||(l=document.createElement("div"),l.id="rd-sync-modal",l.className="rd-modal-mask",document.body.appendChild(l)),r.length===0)l.innerHTML=`
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
        `;else{const d=r.map((u,m)=>`
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
                    ${d}
                    ${c.length?`<div class="rd-modal-extra">${c.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t("rd-modal-apply"))}</button>
                </div>
            </div>
        `}l.classList.add("show");const p=()=>l.classList.remove("show");l.querySelector(".rd-modal-close").addEventListener("click",p),l.querySelectorAll("[data-rd-modal-close]").forEach(d=>d.addEventListener("click",p)),l.addEventListener("click",d=>{d.target===l&&p()});const f=l.querySelector("[data-rd-modal-apply]");f&&f.addEventListener("click",()=>{const d=_results[_drawerIdx];if(!d){p();return}l.querySelectorAll("[data-rd-apply]:checked").forEach(u=>{const m=u.dataset.field,h=u.dataset.value;d.edits[m]=h,d.merged_fields[m]=h;const _=document.querySelector(`[data-field="${m}"]`);_&&(_.value=h);const y=document.querySelector(`[data-field-wrap="${m}"]`);y&&y.classList.add("edited")}),updateDrawerEditCount(),renderResults(),p()})}window.callRdVerify=Qo;window.callRdSync=es;function ns(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(s=>!s.is_duplicate&&!s.is_copy),o=a.length>0?a:e;for(const s of o){const i=s.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function as(e){const n=e.target.dataset.field,a=e.target.value,o=_results[_drawerIdx],s=o.merged_fields[n];a===(s??"")?delete o.edits[n]:(o.edits[n]=a,o.merged_fields[n]=a);const i=document.querySelector(`[data-field-wrap="${n}"]`);i&&i.classList.toggle("edited",o.edits[n]!==void 0),Ea(),renderResults()}function Ea(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=ns;window.onFieldEdit=as;window.updateDrawerEditCount=Ea;function os(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,o=document.getElementById("force-pw-new").value,s=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!o){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(o!==s){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(o.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(o)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(o)&&/\d/.test(o))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(o===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:o})}),c=await r.json().catch(()=>({}));if(!r.ok){const l=c&&c.detail||"unknown",p={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=p[l]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=os;(function(){let e=null,n=null,a=null,o=null;function s(v){return document.getElementById(v)}async function i(){h(),y(),await r()}async function r(){try{const v=localStorage.getItem("mrpilot_token"),L=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+v}});if(!L.ok){_(t("linebot-err-status"));return}const g=await L.json();g.bound?c(g):await l()}catch{_(t("linebot-err-status"))}}function c(v){m(),s("linebot-unbound").style.display="none",s("linebot-bound").style.display="block";const L=s("linebot-status-summary");L&&(L.textContent=t("linebot-status-bound"),L.style.background="#D1FAE5",L.style.color="#065F46");const g=s("linebot-bound-name");g&&(g.textContent=v.line_display_name||"(LINE User)");const x=s("linebot-avatar");x&&(v.line_picture_url?(x.src=v.line_picture_url,x.style.display=""):x.style.display="none");const B=s("linebot-bound-since");B&&v.bound_at&&(B.textContent=new Date(v.bound_at).toLocaleString())}async function l(){s("linebot-bound").style.display="none",s("linebot-unbound").style.display="block";const v=s("linebot-status-summary");v&&(v.textContent=t("linebot-status-unbound"),v.style.background="#FEE2E2",v.style.color="#B91C1C"),await p(),u()}async function p(){try{const v=localStorage.getItem("mrpilot_token"),L=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+v}});if(!L.ok){_(t("linebot-err-code"));return}const g=await L.json();a=g.code,o=new Date(g.expires_at).getTime(),f(g)}catch{_(t("linebot-err-code"))}}function f(v){const L=s("linebot-code");L&&(L.textContent=v.code);const g=s("linebot-bot-id");g&&(g.textContent=v.bot_basic_id||t("linebot-bot-id-missing"));const x=s("linebot-qr");if(x)if(v.bot_friend_url){const B="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(v.bot_friend_url);x.classList.remove("empty"),x.innerHTML='<img src="'+B+'" alt="LINE Bot QR">'}else x.classList.add("empty"),x.innerHTML="";d()}function d(){e&&clearInterval(e);const v=s("linebot-code-expires");function L(){if(!o)return;const g=o-Date.now();if(g<=0){v&&(v.textContent=t("linebot-code-expired"),v.classList.add("expiring"));const w=s("linebot-code");w&&(w.style.opacity="0.4"),clearInterval(e),e=null;return}const x=Math.floor(g/1e3),B=Math.floor(x/60),E=x%60;v&&(v.textContent=t("linebot-code-expires-in").replace("{m}",B).replace("{s}",String(E).padStart(2,"0")),g<6e4?v.classList.add("expiring"):v.classList.remove("expiring"))}L(),e=setInterval(L,1e3)}function u(){m(),n=setInterval(async()=>{try{const v=localStorage.getItem("mrpilot_token"),L=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+v}});if(!L.ok)return;const g=await L.json();g.bound&&c(g)}catch{}},4e3)}function m(){n&&(clearInterval(n),n=null)}function h(){e&&(clearInterval(e),e=null),m()}function _(v){const L=s("linebot-error");L&&(L.textContent=v,L.style.display="block")}function y(){const v=s("linebot-error");v&&(v.style.display="none")}async function b(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const L=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+L}})).ok){_(t("linebot-err-unbind"));return}await i()}catch{_(t("linebot-err-unbind"))}}document.addEventListener("click",v=>{if(v.target.closest("#linebot-code-refresh")){v.preventDefault(),y(),p();return}if(v.target.closest("#linebot-unbind")){v.preventDefault(),b();return}}),window._loadLineBotPanel=i})();function Wt(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const c=parseFloat(r.merged_fields.total_amount);isNaN(c)||(n+=c)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,c)=>({...r,_idx:c}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(c=>(c.filename||"").toLowerCase().includes(r)||(c.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,c)=>{let l,p;return _sortKey==="filename"?(l=r.filename,p=c.filename):_sortKey==="invoice_no"?(l=r.merged_fields.invoice_number,p=c.merged_fields.invoice_number):_sortKey==="invoice_date"?(l=r.merged_fields.date,p=c.merged_fields.date):_sortKey==="total"?(l=parseFloat(r.merged_fields.total_amount)||0,p=parseFloat(c.merged_fields.total_amount)||0):_sortKey==="confidence"?(l=r.confidence,p=c.confidence):(l="",p=""),l<p?_sortDir==="asc"?-1:1:l>p?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=s.map((r,c)=>{const l=r.merged_fields,p=`<span class="empty-cell">${t("empty-val")}</span>`,f="conf-tip-"+(r.confidence||"low"),d="conf-"+(r.confidence||"low"),u=t(f),m=t(d);return`
            <tr data-idx="${r._idx}">
                <td class="num">${c+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${l.invoice_number?escapeHtml(l.invoice_number):p}</td>
                <td class="date">${l.date?escapeHtml(l.date):p}</td>
                <td class="amount">${l.total_amount?Number(l.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):p}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(u)}">${m}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const c=parseInt(r.dataset.idx,10);Ia(c)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),Wt()})});let Gn=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(Gn),Gn=setTimeout(()=>{_searchKeyword=n.trim(),Wt(),Ba()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",Wt(),Ba(),e.focus()});function Ba(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function Ia(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,i=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,c=document.getElementById("drawer-body"),l=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,p=i?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(c.innerHTML=`
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
            ${we("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",s)}
            ${we("date","drawer-lbl-date",r.date,"input",s)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${we("subtotal","drawer-lbl-subtotal",r.subtotal,"input",s)}
            ${we("vat","drawer-lbl-vat",r.vat,"input",s)}
            ${we("total_amount","drawer-lbl-total",r.total_amount,"input",s)}
            ${r.wht_amount||r.wht_rate?`
                ${we("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,ss(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${we("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${we("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,p,Kn("seller"))}
            ${we("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${we("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${we("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,p,Kn("buyer"))}
            ${we("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?is(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${we("notes","drawer-lbl-notes",r.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(f=>`--- Page ${f.page||f.page_number||"?"} ---
${f.raw_text||f.text||""}`).join(`

`))}</pre>
        </details>
    `,s?c.querySelectorAll("[data-field]").forEach(f=>{f.addEventListener("input",onFieldEdit)}):c.querySelectorAll("[data-field]").forEach(f=>{f.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const f=n._historyId||n.history_id||null;window.bindDrawerClient(f,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const f=document.getElementById("drawer-cat-input");f&&!f.value&&!f.readOnly&&f.focus()},80)}function ss(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function we(e,n,a,o,s,i,r){const c=_results[_drawerIdx],l=c&&c.edits[e]!==void 0?c.edits[e]:a,p=c&&c.edits[e]!==void 0&&c.edits[e]!==a,f=escapeHtml(l??""),d=s?"":"readonly",u=o==="textarea"?`<textarea data-field="${e}" rows="2">${f}</textarea>`:`<input type="text" data-field="${e}" value="${f}">`;return`
        <div class="drawer-field ${p?"edited":""} ${d}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${u}
        </div>
    `}function Kn(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function is(e){return`
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
    `}function rs(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=Wt;window.openDrawer=Ia;window.closeDrawer=rs;function ls(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(c){return c&&c.enabled!==!1&&(c.adapter||"").toLowerCase()!=="mrerp_dms"});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let i;if(o.length===1){const c=o[0].name||o[0].adapter||"ERP";i=t("btn-push-to-name",{name:c}),s.title=i}else i=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,s.addEventListener("click",function(c){c.preventDefault(),c.stopPropagation(),o.length===1?La(n,o[0].id):cs(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function cs(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(l=>l.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const i=a.map(function(l){const p=escapeHtml(l.name||l.adapter||"ERP"),f=escapeHtml((l.adapter||"").toLowerCase()),u=l.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(l.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+f+"</span>"+p+u+"</span></button>"}).join("");s.innerHTML=i,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",c,!0)},c=l=>{!s.contains(l.target)&&l.target!==e&&!e.contains(l.target)&&r()};setTimeout(()=>document.addEventListener("click",c,!0),0),s.addEventListener("click",l=>{const p=l.target.closest("[data-ep-id]");if(!p)return;const f=p.getAttribute("data-ep-id");r(),La(n,f)})}async function La(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),i=await s.json();if(!s.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=ls;const ds=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function Ca(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function ps(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function Sa(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const p=[];for(const f of _results){const d=f.invoices&&f.invoices.length>0?f.invoices:null;if(d&&d.length>1)for(let u=0;u<d.length;u++){const m=d[u]||{};p.push({filename:f.filename+" #"+(u+1)+"/"+d.length,engine:f.engine,merged_fields:m.fields||{}})}else p.push({filename:f.filename,engine:f.engine,merged_fields:f.merged_fields})}a=await apiPost("/api/ocr/export",{records:p,lang:currentLang,template:"sales_detail_th"})}else{const p=[];for(const d of _results)d.history_ids&&Array.isArray(d.history_ids)?p.push(...d.history_ids):d.history_id&&p.push(d.history_id);if(p.length===0){showToast(t("toast-export-error"),"error");return}const f=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+f,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:p,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let p="HTTP "+a.status;try{const d=await a.json();d&&d.detail&&(p=typeof d.detail=="string"?d.detail:JSON.stringify(d.detail))}catch(d){console.warn("[export] resp.json err.detail parse failed:",d)}const f=typeof p=="string"&&p.indexOf(".")>0?"err."+p:null;showToast(f?t(f):t("toast-export-error")+" · "+p,"error");return}const s=await a.blob();let i=o;const r=a.headers.get("X-Filename");if(r)i=r;else{const f=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(f)try{i=decodeURIComponent(f[1])}catch{}}const c=URL.createObjectURL(s),l=document.createElement("a");l.href=c,l.download=i,document.body.appendChild(l),l.click(),document.body.removeChild(l),URL.revokeObjectURL(c),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{Sa(Ca())});function us(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=Ca(),o=ds.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
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
    `;n.innerHTML=o+s,e.appendChild(n)}function nn(){const e=document.getElementById("export-dropdown");e&&e.remove()}const an=document.getElementById("btn-export-arrow");an&&an.addEventListener("click",e=>{e.stopPropagation(),!an.disabled&&us()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){nn(),showToast(t("cs-coming-soon"),"info");return}ps(a),nn(),Sa(a);return}e.target.closest("#btn-export-arrow")||nn()});function fs(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(fs,300);const ms=`
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
`;(function(){const e=document.getElementById("page-history");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=ms,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();function bn(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const i=s.filter(r=>_historySelected.has(r.id)).length;a.checked=i===s.length,a.indeterminate=i>0&&i<s.length}}}function vs(){_historySelected.clear(),bn()}async function yn(){if(!_userInfo){setTimeout(()=>yn(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&s.set("client_id",String(i));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const p=await r.json().catch(()=>({}));if((typeof p.detail=="string"?p.detail:p.detail&&p.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const c=await r.json();_historyState.items=c.items||[],_historyState.total=c.total||0;const l=new Set(_historyState.items.map(p=>p.id));for(const p of Array.from(_historySelected))l.has(p)||_historySelected.delete(p);Ta()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function Ta(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(p=>{p.confidence==="high"&&s++});const i=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(p=>{const f=new Date(p.created_at),d=String(f.getMonth()+1).padStart(2,"0"),u=String(f.getDate()).padStart(2,"0"),m=String(f.getHours()).padStart(2,"0"),h=String(f.getMinutes()).padStart(2,"0"),_=`${d}-${u} ${m}:${h}`,y=escapeHtml(p.filename||""),b=y.length>50?y.substring(0,50)+"…":y,v=p.invoice_no?escapeHtml(p.invoice_no):b,L=[];p.seller_name&&L.push(escapeHtml(p.seller_name)),p.invoice_no&&p.filename&&L.push(b);const g=L.join(" · ")||"-",x=p.category_tag?`<span class="history-badge category">${escapeHtml(p.category_tag)}</span>`:"",B=p.source_total&&p.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:p.source_index||1,n:p.source_total}))}</span>`:"",E=p.total_amount!==null&&p.total_amount!==void 0?Number(p.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',w=[];(p.total_amount===null||p.total_amount===void 0)&&w.push(t("field-amount")),p.invoice_no||w.push(t("field-invoice-no")),p.invoice_date||w.push(t("field-invoice-date")),p.seller_name||w.push(t("field-seller-name")),w.length>0&&`${escapeHtml(p.id)}${escapeHtml(t("history-needs-review-tip")+" · "+w.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,p.edited&&`${escapeHtml(t("history-edited",{n:p.edit_count||1}))}`;const I=p.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",M=p.confidence==="high"?"high":p.confidence==="medium"?"mid":"low",S=p.confidence==="high"?t("conf-high"):p.confidence==="medium"?t("conf-medium"):t("conf-low"),C=`<span class="history-badge conf-${M}">${escapeHtml(S)}</span>`;let k="";const T=p.source||"manual";return T==="email"?k=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:T==="folder"?k=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:T==="api"&&(k=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(p.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(p.id)}" ${_historySelected.has(p.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${_}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${v} ${x} ${B} ${k} ${I}</div>
                        <div class="history-cell-subtitle">${g}</div>
                    </div>
                    <div class="history-cell-amount">${E}</div>
                    <div class="history-cell-conf">${C}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(p.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),bn();const c=a.length>0?_historyState.page*_historyState.pageSize+1:0,l=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:c,to:l,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=yn;window.renderHistoryList=Ta;window.updateHistoryBatchBar=bn;window.clearHistorySelection=vs;typeof currentRoute<"u"&&currentRoute==="history"&&yn();async function Dt(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),gs(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),bs(a.id)}catch(n){console.error("open history detail failed",n)}}async function hs(e){await Dt(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function gs(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",ws),document.getElementById("btn-push-erp").addEventListener("click",ys)}async function bs(e){}async function ys(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function ws(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(c=>!c.is_duplicate&&!c.is_copy),s=o>=0?o:0,i=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function ks(e,n){document.querySelectorAll(".history-popover").forEach(p=>p.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(p=>p.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",i=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const c=()=>{r.remove(),document.removeEventListener("click",l,!0)},l=p=>{!r.contains(p.target)&&p.target!==n&&c()};setTimeout(()=>document.addEventListener("click",l,!0),0),r.addEventListener("click",async p=>{const f=p.target.closest("[data-act]");if(!f||f.disabled)return;const d=f.dataset.act;if(c(),d==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const m=document.createElement("textarea");m.value=s,m.style.position="fixed",m.style.opacity="0",document.body.appendChild(m),m.select(),document.execCommand("copy"),document.body.removeChild(m),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(d==="download-pdf"){const u=showToast(t("history-download-pdf-loading"),"loading",0);try{const m=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!m.ok)throw new Error("download failed");const h=await m.blob(),_=URL.createObjectURL(h),y=document.createElement("a");y.href=_,y.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(y),y.click(),document.body.removeChild(y),setTimeout(()=>URL.revokeObjectURL(_),5e3),u(),showToast(t("history-download-pdf-ok"),"success")}catch{u(),showToast(t("history-download-pdf-fail"),"error")}}else if(d==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const c=r.target.closest(".history-row"),l=r.target.closest("[data-hmenu]");if(l){r.stopPropagation(),ks(l.dataset.hmenu,l);return}const p=r.target.closest("[data-review]");if(p){r.stopPropagation(),Dt(p.dataset.review);return}const f=r.target.closest("[data-fill-amount]");if(f){r.stopPropagation(),hs(f.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||c&&!r.target.closest("[data-hmenu]")&&Dt(c.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const c=r.target.closest(".history-row-check");if(!c)return;const l=c.dataset.hid;c.checked?_historySelected.add(l):_historySelected.delete(l),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const c=r.target.checked;for(const l of _historyState.items)c?_historySelected.add(l.id):_historySelected.delete(l.id);document.querySelectorAll(".history-row-check").forEach(l=>{l.checked=c}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const l=Array.from(_historySelected);try{const p=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:l})});if(!p.ok)throw new Error("batch delete failed");const f=await p.json();showToast(t("history-batch-done",{n:f.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(p){console.error("batch delete",p),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const c=r.target.value;document.getElementById("history-search-clear").style.display=c?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=c.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=Dt;const st=document.getElementById("drop-zone"),wn=document.getElementById("file-input");st.addEventListener("click",()=>wn.click());wn.addEventListener("change",e=>Ma(e.target.files));["dragover","dragenter"].forEach(e=>{st.addEventListener(e,n=>{n.preventDefault(),st.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{st.addEventListener(e,n=>{n.preventDefault(),st.classList.remove("drag-over")})});st.addEventListener("drop",e=>{e.preventDefault(),Ma(e.dataTransfer.files)});const xs=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function cn(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function _s(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function Es(e){return _s(e)||cn(e)||xs.test(e.name)}function Ma(e){hideAlerts();const n=Array.from(e),a=n.filter(Es);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(c=>!cn(c)),s=a.filter(cn),i=new Set(_selectedFiles.map(c=>c.name+"_"+c.size));for(const c of o){const l=c.name+"_"+c.size;i.has(l)||(_selectedFiles.push({file:c,name:c.name,size:c.size,status:"waiting",errorKey:null,errorParams:null}),i.add(l))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(c){console.error("[upload] image route failed",c)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),Yt(),kn(),wn.value=""}let $t=!1;function Yt(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(d=>d.status==="processing"||d.status==="retrying").length,o=_selectedFiles.filter(d=>d.status==="success").length,s=_selectedFiles.filter(d=>d.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const c=$t?t("file-list-collapse"):t("file-list-expand"),l=_selectedFiles.map((d,u)=>{let m=t("status-"+d.status);d.status==="retrying"&&(m=t("status-retrying")),d.status==="error"&&d.errorKey&&(m=t(d.errorKey,d.errorParams||{}));const h=d.status==="processing"||d.status==="retrying"?'<span class="spinner"></span>':"",_=d.status==="error"&&d.canRetry?`<button class="file-retry-btn" data-retry-idx="${u}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",y=d.status==="success"&&d.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(d.name)}">${escapeHtml(d.name)}</span>
                ${y}
                <span class="file-status ${d.status}">${h}${m}</span>
                ${_}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(c)}</button>`:""}
        </div>
        <ul class="file-list-body${$t?" expanded":""}" id="file-list-body">
            ${l}
        </ul>
    `;const p=document.getElementById("file-list-toggle");p&&p.addEventListener("click",()=>{$t=!$t,Yt()});const f=document.getElementById("file-list-body");f&&!f.dataset.retryBound&&(f.dataset.retryBound="1",f.addEventListener("click",async d=>{const u=d.target.closest(".file-retry-btn");if(!u)return;const m=parseInt(u.dataset.retryIdx||"-1",10);if(m<0||m>=_selectedFiles.length)return;const h=_selectedFiles[m];!h||h.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(h,!0)}))}function kn(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],Yt(),renderResults(),kn(),hideAlerts()});window.renderFileList=Yt;window.updateStartButton=kn;const Bs=`
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
`;be("camera-tips-modal",Bs);async function qt(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],i=o.naturalWidth,r=o.naturalHeight;(i<1e3||r<1e3)&&s.push("low_res");try{const c=document.createElement("canvas");c.width=64,c.height=64;const l=c.getContext("2d");l.drawImage(o,0,0,64,64);const p=l.getImageData(0,0,64,64).data;let f=0,d=0;for(let m=0;m<p.length;m+=4)f+=.299*p[m]+.587*p[m+1]+.114*p[m+2],d++;const u=d?f/d:128;u<70?s.push("too_dark"):u>235&&s.push("too_bright"),n({warnings:s,width:i,height:r,brightness:u})}catch{n({warnings:s,width:i,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}async function $a(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let p=0;p<e.length;p++){const f=e[p],{dataUrl:d,naturalW:u,naturalH:m}=await Is(f);p>0&&s.addPage("a4","p");const h=u/m;let _=a-10,y=_/h;y>o-10&&(y=o-10,_=y*h);const b=(a-_)/2,v=(o-y)/2,L=f.type==="image/png"?"PNG":"JPEG";s.addImage(d,L,b,v,_,y,void 0,"FAST")}const i=s.output("blob"),r=new Date,c=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),l=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${c}${l}.pdf`,{type:"application/pdf"})}function Is(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await Cs()||o.click()}),o.addEventListener("change",async c=>{const l=Array.from(c.target.files||[]);if(c.target.value="",l.length!==0)for(const p of l)await dn([p],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=c=>async l=>{const p=Array.from(l.target.files||[]);if(l.target.value="",p.length===0)return;const f=p.filter(u=>u.type==="application/pdf"||/\.pdf$/i.test(u.name)),d=p.filter(u=>!f.includes(u));f.length>0&&await Ls(f),d.length>0&&await dn(d,c)};a&&a.addEventListener("change",r("gallery"))})();async function Ls(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function Cs(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const i=c=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(c)},r=c=>{c.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),o&&(o.onclick=()=>i(!1)),n.onclick=c=>{c.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}let Be=[],Oe=null;async function dn(e,n){if(hideAlerts(),!(!e||e.length===0)){var a=typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice";if(a==="thai_id_card"){for(const s of e)_selectedFiles.push({file:s,name:s.name,size:s.size,status:"waiting",errorKey:null,errorParams:null});const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton();return}if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let o=0;o<30&&(await new Promise(s=>setTimeout(s,100)),!(window.jspdf&&window.jspdf.jsPDF));o++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const o=e[0];let s={};try{s=await qt(o)}catch{}Be.push({file:o,quality:s}),Oe="camera",Qe();return}if(n==="gallery"&&(e.length>=2||Be.length>0)){for(const o of e){let s={};try{s=await qt(o)}catch{}Be.push({file:o,quality:s})}Oe="gallery",Qe();return}await Ha(e)}}async function Ss(e){const n=new Set;for(const o of e)try{((await qt(o)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const o=await $a(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function Qe(){let e=document.getElementById("camera-buffer-bar");if(Be.length===0){e&&e.remove(),Oe=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=Be.length,a=n>=2,o=Oe==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?o?i=`
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
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{Be=[],Oe=null,Qe()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const l=o?"gallery-input":"camera-input",p=document.getElementById(l);p&&p.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const l=Be.map(p=>p.file);Be=[],Oe=null,Qe(),await Ss(l)});const c=e.querySelector('[data-cbb-action="separate"]');c&&(c.onclick=async()=>{const l=Be.map(p=>p.file);Be=[],Oe=null,Qe(),await Ha(l)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{Be.length>0&&Qe()});async function Ha(e){const n=new Set;let a=0;for(const s of e)try{((await qt(s)).warnings||[]).forEach(c=>n.add(c));const r=await $a([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}window.handleCameraImages=dn;(function(){var e="pearnly_ocr_doc_mode",n=!1,a=!1;function o(u){return typeof escapeHtml=="function"?escapeHtml(u==null?"":String(u)):String(u??"")}function s(){try{return localStorage.getItem(e)==="thai_id_card"?"thai_id_card":"invoice"}catch{return"invoice"}}window.getOcrDocumentMode=function(){return n?s():"invoice"};function i(){var u=document.getElementById("drop-zone");return u?u.closest(".card"):null}function r(){var u=i();if(!u)return null;var m=u.querySelector("#ocr-doc-mode");if(m)return m;var h=u.querySelector(".section-head");return m=document.createElement("div"),m.id="ocr-doc-mode",m.className="ocr-doc-mode",m.setAttribute("role","tablist"),m.style.cssText="display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;",h&&h.parentNode?h.parentNode.insertBefore(m,h.nextSibling):u.insertBefore(m,u.firstChild),m}function c(u,m,h){return'<button type="button" class="ocr-doc-seg'+(h?" active":"")+'" data-doc-mode="'+u+'" role="tab" aria-selected="'+(h?"true":"false")+'" style="border:none;background:'+(h?"var(--card,#fff)":"transparent")+";color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:"+(h?"600":"500")+";padding:6px 16px;border-radius:7px;cursor:pointer;box-shadow:"+(h?"0 1px 3px rgba(0,0,0,.08)":"none")+';transition:background .15s;">'+o(t(m))+"</button>"}function l(){var u=r();if(u){if(!n){u.style.display="none";return}var m=s();u.style.display="flex",u.innerHTML=c("invoice","ocr-mode-invoice",m==="invoice")+c("thai_id_card","ocr-mode-id-card",m==="thai_id_card")}}function p(u){try{localStorage.setItem(e,u==="thai_id_card"?"thai_id_card":"invoice")}catch{}l();try{document.dispatchEvent(new CustomEvent("ocr-doc-mode-change",{detail:{mode:window.getOcrDocumentMode()}}))}catch{}}async function f(u){if(!(a&&!u)){var m=localStorage.getItem("mrpilot_token");if(m)try{var h=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+m}});if(!h.ok)return;var _=await h.json(),y=_&&_.items||[];n=y.some(function(b){return b&&(b.adapter||"").toLowerCase()==="mrerp_dms"&&b.enabled!==!1}),a=!0,window._dmsHasEndpoint=n,l()}catch{}}}window._refreshOcrDocMode=function(){f(!0)},document.addEventListener("click",function(u){var m=u.target.closest(".ocr-doc-seg");m&&m.getAttribute("data-doc-mode")&&(u.preventDefault(),p(m.getAttribute("data-doc-mode")))}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("ocr-doc-mode",l);function d(){r(),l(),f(!1)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",d):d(),window.addEventListener("hashchange",function(){((location.hash||"").indexOf("ocr")>=0||location.hash===""||location.hash==="#home")&&setTimeout(function(){r(),f(!1)},60)})})();(function(){function e(i){return typeof escapeHtml=="function"?escapeHtml(i==null?"":String(i)):String(i??"")}function n(){var i=(function(){var c=document.getElementById("drop-zone");return c?c.closest(".card"):null})();if(!i||!i.parentNode)return null;var r=document.getElementById("dms-id-card-result");return r||(r=document.createElement("div"),r.id="dms-id-card-result",r.className="card",r.style.cssText="display:none;margin-top:16px;",i.parentNode.insertBefore(r,i.nextSibling),r)}function a(i,r){return'<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);"><span style="color:var(--muted,#6b6b66);font-size:13px;">'+e(t(i))+'</span><span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">'+e(r||"—")+"</span></div>"}function o(i){if(!i)return"";var r=[i.house_no,i.road,i.subdistrict,i.district,i.province,i.zipcode].filter(function(c){return c});return r.join(" ")||i.address_raw||""}function s(i){var r=i&&i.status||"failed",c,l,p;return r==="success"?(c="#0a7a2c",l="#d6f5e0",p="dms-result-status-success"):r==="needs_review"?(c="#9a6b00",l="#fdf0d0",p="dms-result-status-needs-review"):r==="skipped"?(c="#5d5d57",l="#eee",p="dms-result-status-skipped"):(c="#b3261e",l="#fbe0de",p="dms-result-status-failed"),'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:'+c+";background:"+l+';">'+e(t(p))+"</span>"}window.renderDmsIdCardResult=function(i){var r=n();if(r){i=i||{};var c=i.id_card||{},l=c.address||{},p=i.dms_push||{},f=p.status||(i.ok?"success":"failed"),d="";f==="success"&&(d=a("dms-result-customer",p.customer_id)+a("dms-result-booking",p.booking_no));var u=f==="failed"||f==="needs_review"?'<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">'+e(t("dms-result-retry"))+"</button>":"",m="";if(f==="failed"&&p.error_code){var h="dms-err-"+String(p.error_code).toLowerCase(),_=t(h);(!_||_===h)&&(_=t("dms-err-err_dms_unexpected")),m='<div style="margin-top:8px;color:#b3261e;font-size:12px;">'+e(_)+"</div>"}r.style.display="",r.innerHTML='<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;"><div class="section-title">'+e(t("dms-result-title"))+"</div>"+s(p)+'</div><div style="margin-top:8px;">'+a("dms-result-name",(c.first_name||"")+" "+(c.last_name||""))+a("dms-result-id",c.people_id_masked)+a("dms-result-birthday",c.birthday_be)+a("dms-result-address",o(l))+d+"</div>"+m+u}},window.clearDmsIdCardResult=function(){var i=document.getElementById("dms-id-card-result");i&&(i.style.display="none",i.innerHTML="")},document.addEventListener("click",function(i){i.target.closest("#dms-id-card-retry")&&(i.preventDefault(),typeof window._dmsRetryIdCard=="function"&&window._dmsRetryIdCard())})})();document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,(typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice")==="thai_id_card"){try{await Aa()}finally{const d=document.getElementById("btn-start");d&&(d.disabled=!1)}return}if(_userInfo&&_userInfo.plan==="free"){const d=await fetch("/api/health").then(u=>u.json()).catch(()=>null);d&&!d.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const n=_selectedFiles.filter(d=>d.status==="waiting"),a=6;async function o(d,u){if(window._ocrAborted)return d.status="cancelled",d.errorKey=null,renderFileList(),{};d.status=u?"retrying":"processing",d.canRetry=!1,renderFileList();const m=new AbortController,h=setTimeout(()=>m.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(m);try{const _=new FormData;_.append("file",d.file,d.name);try{if(typeof window.getCurrentClientId=="function"){const g=window.getCurrentClientId();g!=null&&_.append("client_id",String(g))}}catch{}const y=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:_,signal:m.signal});if(clearTimeout(h),window._ocrCtrls.delete(m),y.status===401||y.status===403){const x=await y.clone().json().catch(()=>({})),B=x&&x.detail,E=typeof B=="string"?B:B&&B.code||"";if(!E||E.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),E==="auth.session_revoked")_showSessionRevokedModal();else{const w=E==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(w),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}E==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!y.ok){const x=(await y.json().catch(()=>({}))).detail;return typeof x=="string"?(d.errorKey="err."+x,d.errorParams=null):x&&x.code?(d.errorKey="err."+x.code,d.errorParams={...x,mb:_quota.max_file_size_mb}):(d.errorKey="err.unknown",d.errorParams=null),(d.errorKey==="err.unknown"||d.errorKey==="err.ocr.engine_error")&&(y.status===429?d.errorKey="err.rate_limit":y.status===502||y.status===503||y.status===504?d.errorKey="err.gemini_overloaded":y.status>=500&&(d.errorKey="err.server")),d.status="error",d.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(d.errorKey||""),renderFileList(),{}}const b=await y.json();d.status="success",d.fromCache=!!b.from_cache;const v=mergeFields(b.pages),L=b.confidence||(v.items&&v.items.length>0?"high":"low");if(_results.push({filename:b.filename,pages:b.pages,page_count:b.page_count,elapsed_ms:b.elapsed_ms,engine:b.engine,merged_fields:v,edits:{},confidence:L,history_id:b.history_id,history_ids:b.history_ids||[],invoice_count:b.invoice_count||1,invoices:b.invoices||[],archive_name:b.archive_name||null,category_tag:b.category_tag||null,auto_pushed:!!b.auto_pushed,typhoon_enhanced:!!b.typhoon_enhanced,typhoon_pages:b.typhoon_pages||[],from_cache:!!b.from_cache}),b.invoice_count&&b.invoice_count>1&&showToast(t("multi-invoice-toast",{file:b.filename,n:b.invoice_count}),"success"),b.missed_invoice_warnings&&b.missed_invoice_warnings.length){const g=b.missed_invoice_warnings.map(function(x){return x.page}).filter(function(x){return x!=null});showToast(t("missed-invoice-warn",{file:b.filename,pages:g.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",b.missed_invoice_warnings)}if(b.typhoon_enhanced&&b.typhoon_pages&&b.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:b.filename,n:b.typhoon_pages.length}),"success"),b.fallback_used){const g=b.engine_chain||[],x=b.engine||"";let B;x==="typhoon_nvidia"?B="fallback-typhoon-nvidia-toast":x==="easyocr"?B="fallback-easyocr-toast":B="fallback-generic-toast",showToast(t(B,{file:b.filename}),"warn"),console.info("[OCR Chain]",g)}if(b.from_cache&&showToast(t("cache-hit-toast",{file:b.filename}),"info"),b.duplicate_warnings&&b.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const g of b.duplicate_warnings)window._dupQueue.push({filename:b.filename,...g})}return b.auto_pushed&&showToast(t("auto-push-fired",{file:b.filename}),"info"),b.quota&&b.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=b.quota.used_this_month,_userInfo.tenant_used=b.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(_){clearTimeout(h);try{window._ocrCtrls&&window._ocrCtrls.delete(m)}catch{}console.error("[Upload] failed for",d.file.name,_);const y=_&&(_.name==="AbortError"||_==="timeout"),b=y&&(m.signal.reason==="timeout"||_==="timeout"),v=_&&_.message&&/NetworkError|Failed to fetch/i.test(_.message);return y&&(m.signal.reason==="user_stop"||window._ocrAborted)?(d.status="cancelled",d.errorKey=null,d.canRetry=!1,renderFileList(),{}):(b?d.errorKey="err.timeout":y?d.errorKey="err.aborted":v?d.errorKey="err.network":(d.errorKey="err.unknown",d.errorParams={msg:_&&_.message?_.message:String(_)}),d.status="error",!u&&!window._ocrAborted&&(v||b)&&navigator.onLine!==!1&&(d.canRetry=!0,renderFileList(),await new Promise(g=>setTimeout(g,2e3)),d.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?o(d,!0):(d.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=o;let s=0,i=!1;async function r(){for(;s<n.length&&!i&&!window._ocrAborted;){const d=s++,u=await o(n[d]);if(u&&u.abort){i=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const c=document.getElementById("btn-start"),l=document.getElementById("btn-stop");c&&(c.style.display="none"),l&&(l.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(n)}catch{}const p=[];for(let d=0;d<Math.min(a,n.length);d++)p.push(r());await Promise.all(p);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}c&&(c.style.display=""),l&&(l.style.display="none");const f=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const d={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const m of n)if(m.status==="success")d.success++;else if(m.status==="cancelled")d.cancelled++;else if(m.status==="error"){const h=m.errorKey||"";h==="err.network"?d.network++:h==="err.timeout"||h==="err.aborted"?d.timeout++:h.indexOf("quota")>=0||h==="err.monthly_limit_exceeded"?d.quota++:h==="err.gemini_overloaded"||h==="err.server"?d.overloaded++:h==="err.rate_limit"?d.rate++:d.other++}const u=n.length;f?showToast(Ts(d,u),"warn",4e3):u>1&&d.network+d.timeout+d.quota+d.overloaded+d.rate+d.other>0&&showToast(Ms(d),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function Ts(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function Ms(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});async function Aa(e){let n;if(e)n=_selectedFiles.find(a=>a.file===e)||{file:e,name:e.name,status:"waiting"};else{const a=_selectedFiles.filter(o=>o.status==="waiting");if(!a.length)return;n=a[0]}window._dmsLastFile=n.file,n.status="processing",typeof renderFileList=="function"&&renderFileList();try{const a=new FormData;a.append("file",n.file,n.name),a.append("push","true");const o=await fetch("/api/dms/id-card-booking",{method:"POST",headers:{Authorization:"Bearer "+token},body:a});if(o.status===401||o.status===403){const i=await o.clone().json().catch(()=>({})),r=i&&i.detail,c=typeof r=="string"?r:r&&r.code||"";if(!c||c.startsWith("auth.")){localStorage.removeItem("mrpilot_token"),showToast(t("alert-session"),"error"),setTimeout(()=>{window.location.href="/"},1200);return}}const s=await o.json().catch(()=>({}));if(!o.ok){n.status="error";const i=s&&s.detail&&(s.detail.code||s.detail)||"unknown";n.errorKey="err."+i,n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:String(i)}});return}n.status=s.ok||s.dms_push&&s.dms_push.status==="needs_review"?"success":"error",typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult(s),typeof updateStartButton=="function"&&updateStartButton()}catch{n.status="error",n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:"network"}})}}window._dmsRetryIdCard=function(){window._dmsLastFile&&Aa(window._dmsLastFile)};function ja(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=m=>m!=null?Number(m).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",c=m=>m||"—",l=m=>{try{const h=new Date(m);return`${h.getFullYear()}-${String(h.getMonth()+1).padStart(2,"0")}-${String(h.getDate()).padStart(2,"0")}`}catch{return m}},p=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",f=(e.matched_fields||[]).map(m=>{const h=t("dup-field-"+m.replace("_","-"))||m;return`<span class="dup-field-chip">${escapeHtml(h)}</span>`}).join(" "),d=document.createElement("div");d.className="log-detail-modal",d.innerHTML=`
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
                        <tr><td>${escapeHtml(t("dup-field-invoice-date"))}</td><td>${escapeHtml(c(e.current.invoice_date))}</td><td>${escapeHtml(c(e.match.invoice_date))}</td></tr>
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
    `,document.body.appendChild(d);const u=()=>{d.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(ja,200)};d.querySelector(".dup-close").addEventListener("click",u),d.querySelector('[data-action="view"]').addEventListener("click",()=>{const m=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(m)},400),u()}),d.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const m=e.new_history_id;if(!m){u();return}try{(await fetch(`/api/history/${encodeURIComponent(m)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}u()}),d.querySelector('[data-action="keep"]').addEventListener("click",u)}window.showDuplicateDialog=ja;function Ue(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function ft(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function $s(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ue("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ue("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ue("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ue("time-day-ago-suffix"," 天前")}catch{return""}}async function xn(){Pa();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const c={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[l,p,f]=await Promise.all([fetch("/api/me/tenant-usage",{headers:c}).then(y=>y.ok?y.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:c}).then(y=>y.ok?y.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:c}).then(y=>y.ok?y.json():null).catch(()=>null)]),d=l&&l.ocr_this_month||0;let u=0;const m=p&&(p.items||p.history||p)||[],h=Array.isArray(m)?m:[];h.forEach(y=>{(y.status==="pending"||y.status==="reviewing")&&u++});const _=f&&(f.total||f.count||f.pending||0)||0;if(e&&(e.textContent=ft(d)),n&&(n.textContent=ft(u)),a&&(a.textContent=ft(_)),r&&(_>0?(r.style.display="",r.textContent=_):r.style.display="none"),o&&l){const y=l.ocr_this_month||0,b=l.quota||0;o.textContent=ft(y),s&&(s.textContent=b?y+" / "+ft(b)+" 张":Ue("dash-kpi-plan-sub","本月用量"))}if(i)if(h.length===0)i.innerHTML='<div class="dash-recent-empty">'+Ue("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const y=h.slice(0,5).map(b=>{const v=(b.invoice_no||b.filename||b.id||"").toString(),L=(b.supplier_name||b.buyer_name||b.client_name||b.notes||"").toString(),g=$s(b.created_at||b.upload_time||b.date),x=B=>String(B).replace(/[&<>"']/g,E=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[E]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+x(v)+'">'+x(v)+'</span><span class="dash-recent-mid" title="'+x(L)+'">'+x(L)+'</span><span class="dash-recent-time">'+x(g)+"</span></div>"}).join("");i.innerHTML=y}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+Ue("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=xn;async function Pa(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},c=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!c.ok){e.style.display="none",s&&(s.textContent="—"),i&&(i.textContent="");return}const l=await c.json(),p=!!l.is_owner,f=!!l.is_billing_exempt;if(!p)e.style.display="none";else if(e.style.display="",f)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const u=typeof l.balance_thb=="number"?l.balance_thb:0;if(a&&(a.textContent="฿"+u.toFixed(2),a.className=u<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const m=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",h=u<50?"#dc2626":"#6b7280",_=y=>typeof window.escapeHtml=="function"?window.escapeHtml(y):String(y).replace(/[&<>"']/g,b=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[b]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+h+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+_(m)+"</a>"}}const d=typeof l.pages_this_month=="number"?l.pages_this_month:typeof l.my_invoice_count=="number"?l.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(d)),i){const u=d>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",m=typeof window.t=="function"?window.t(u,{used:d}):d+" pages";i.textContent=m}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=Pa;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(xn,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&xn()});function ce(e){return(typeof window.t=="function"?window.t(e):null)||e}function _n(){return localStorage.getItem("mrpilot_token")||""}function re(e){return document.getElementById(e)}var jt=null,yt=null;function Da(){yt||(yt=setInterval(function(){if(!document.hidden){var e=_n();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;jt!==null&&a>jt&&(window.showToast&&window.showToast(ce("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),jt=a}}).catch(function(){}))}},3e4))}function Hs(){yt&&(clearInterval(yt),yt=null),jt=null}window._startCreditsPoll=Da;window._stopCreditsPoll=Hs;Da();var En=null,Bn=0;function As(){if(!re("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),js()}}function qa(){var e=function(n,a){var o=re(n);o&&(o.textContent=a)};e("tv2-title",ce("topup-title")),e("tv2-sl1",ce("topup-step1")),e("tv2-sl2",ce("topup-step2")),e("tv2-sl3",ce("topup-step3")),e("tv2-al",ce("topup-amount-label")),e("tv2-bl",ce("topup-bank-label")),e("tv2-copy",ce("topup-copy-account")),e("tv2-dt",ce("topup-slip-drop")),e("tv2-pl",ce("topup-payer-label")),e("tv2-nl",ce("topup-note-label"))}function Lt(e){[1,2,3].forEach(function(s){var i=re("tv2-s"+s);i&&(i.style.display=s===e?"":"none");var r=re("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=re("tv2-back"),a=re("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=ce("topup-btn-cancel")):n&&(n.style.display="",n.textContent=ce("topup-btn-back")),a&&(a.textContent=ce(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=re("tv2-bn");o&&(o.innerHTML=ce("topup-bank-note").replace("{amount}","<strong>฿"+Number(Bn).toLocaleString()+"</strong>"))}}function pn(){for(var e=1;e<=3;e++){var n=re("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function Rt(e){var n=re(e);n&&(n.textContent="",n.style.display="none")}function wt(e,n){var a=re(e);a&&(a.textContent=n,a.style.display="")}function Jn(e){var n=re("tv2-dt");n&&(n.textContent=e.name);var a=re("tv2-drop");a&&a.classList.add("has-file"),Rt("tv2-se")}function js(){var e=re("topup-v2-ov");re("tv2-close").addEventListener("click",vt),e.addEventListener("click",function(i){i.target===e&&vt()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&vt()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(l){l.classList.remove("active")}),r.classList.add("active");var c=re("tv2-amt");c&&(c.value=r.dataset.val,Rt("tv2-ae"))}});var n=re("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),Rt("tv2-ae")});var a=re("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=ce("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var o=re("tv2-drop"),s=re("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(i){i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(i){i.preventDefault(),o.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&Jn(r)})),s&&s.addEventListener("change",function(){s.files[0]&&Jn(s.files[0])}),re("tv2-back").addEventListener("click",function(){var i=pn();if(i<=1){vt();return}Lt(i-1)}),re("tv2-next").addEventListener("click",function(){var i=pn();i===1?Ps():i===2?Lt(3):Ds()})}async function Ps(){var e=re("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){wt("tv2-ae",ce("topup-amount-invalid"));return}if(n>5e5){wt("tv2-ae",ce("topup-amount-too-large"));return}Bn=n;var a=re("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+_n()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),i=ce("topup-submit-fail");try{var r=JSON.parse(s),c=r.detail;if(Array.isArray(c)&&c.length){var l=c[0]&&c[0].type||"";l.indexOf("less_than")>=0?i=ce("topup-amount-too-large"):(l.indexOf("greater_than")>=0||l.indexOf("parsing")>=0)&&(i=ce("topup-amount-invalid"))}else typeof c=="string"&&(i=c)}catch{}throw new Error(i)}var p=await o.json();En=p.request_id,Lt(2)}catch(f){wt("tv2-ae",f.message||ce("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=ce("topup-btn-next"))}}async function Ds(){var e=re("tv2-file");if(!e||!e.files||!e.files[0]){wt("tv2-se",ce("topup-slip-required"));return}var n=re("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=re("tv2-payer"),s=re("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+En,{method:"POST",headers:{Authorization:"Bearer "+_n()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(ce("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(ce("topup-pending"),"info"),vt()}catch(c){wt("tv2-ue",ce("topup-upload-fail")+" · "+c.message),n&&(n.disabled=!1,n.textContent=ce("topup-btn-submit"))}}function vt(){var e=re("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){As(),En=null,Bn=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=re(a);o&&(o.value="")});var e=re("tv2-file");e&&(e.value="");var n=re("tv2-drop");n&&n.classList.remove("has-file","drag-over"),re("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){Rt(a)}),qa(),Lt(1),re("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=re("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(qa(),Lt(pn()))});const qs=`
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

    `;be("page-test-center",qs);(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",i=!1,r=!1;function c(A,H,P){let R=typeof t=="function"?t(A):null;return(!R||R===A)&&(R=H),P&&Object.keys(P).forEach(function(D){R=String(R).replace("{"+D+"}",String(P[D]))}),R}function l(){try{const A=localStorage.getItem(n);o=A?JSON.parse(A):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function p(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function f(A){const H=new Date(A),P=function(R){return R<10?"0"+R:""+R};return P(H.getHours())+":"+P(H.getMinutes())+":"+P(H.getSeconds())}function d(A){return String(A??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function u(A,H){try{typeof showToast=="function"?showToast(A,H||"info"):alert(A)}catch{}}function m(A){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(A).then(function(){u(c("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){h(A)}):h(A)}catch{h(A)}}function h(A){try{const H=document.createElement("textarea");H.value=A,H.style.position="fixed",H.style.opacity="0",document.body.appendChild(H),H.select();const P=document.execCommand("copy");document.body.removeChild(H),u(P?c("tc-toast-copied","已复制"):c("tc-toast-copy-fail","复制失败"),P?"success":"error")}catch{u(c("tc-toast-copy-fail","复制失败"),"error")}}function _(){const A=document.getElementById("tc-account-chip"),H=document.getElementById("tc-progress-chip");if(A&&(A.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),H){const P=a.length,R=a.filter(function(D){return o[D.id]}).length;H.textContent=R+" / "+P}}function y(){const A=document.getElementById("tc-checklist-body");if(!A)return;const H={};a.forEach(function(R){H[R.group]||(H[R.group]=[]),H[R.group].push(R)});const P=[];Object.keys(H).forEach(function(R){P.push('<div class="tc-checklist-group">'),P.push('<div class="tc-checklist-group-title">'+d(R)+"</div>"),H[R].forEach(function(D){const j=o[D.id]||"",F=j?"is-"+j:"";P.push('<div class="tc-check-item '+F+'" data-id="'+d(D.id)+'"><div class="tc-check-id">'+d(D.id)+'</div><div class="tc-check-desc">'+d(D.desc)+'</div><div class="tc-check-actions">'+b(D.id,"pass",j)+b(D.id,"fail",j)+b(D.id,"skip",j)+"</div></div>")}),P.push("</div>")}),A.innerHTML=P.join("")}function b(A,H,P){const R=P===H,D={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},j={pass:c("tc-status-pass","通过"),fail:c("tc-status-fail","失败"),skip:c("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(R?"is-active "+H:"")+'" data-id="'+d(A)+'" data-kind="'+H+'" title="'+d(j[H])+'">'+D[H]+"</button>"}function v(A){return s==="all"?!0:s==="js_error"?A.type==="js_error"||A.type==="promise_error":s==="api"?A.type==="api_error"||A.type==="api_fail":s==="api_slow"?A.type==="api_slow":s==="console"?A.type==="console_error"||A.type==="console_warn":!0}function L(){const A=document.getElementById("tc-logs-body"),H=document.getElementById("tc-logs-count");if(!A)return;const P=(window._pearnlyTcLogs||[]).slice().reverse(),R=P.filter(v);if(H&&(H.textContent=String(P.length)),R.length===0){A.innerHTML='<div class="tc-logs-empty">'+d(c("tc-logs-empty","暂无异常"))+"</div>";return}const D=R.slice(0,100).map(function(j){const F=typeof j.detail=="object"?JSON.stringify(j.detail,null,2):String(j.detail||"");return'<div class="tc-log-item t-'+d(j.type)+'" data-ts="'+j.ts+'"><span class="tc-log-time">'+f(j.ts)+'</span><span class="tc-log-type">'+d(j.type)+'</span><div class="tc-log-summary">'+d(j.summary)+'<div class="tc-log-detail">'+d(F)+"</div></div></div>"}).join("");A.innerHTML=D,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(j){j.classList.toggle("active",j.getAttribute("data-filter")===s)})}function g(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&L(),x()},200))}window._tcOnNewLog=g;function x(){const A=document.getElementById("nav-test-badge");if(!A)return;const H=(window._pearnlyTcLogs||[]).filter(function(P){return P.type==="js_error"||P.type==="promise_error"||P.type==="api_error"||P.type==="api_fail"||P.type==="console_error"}).length;H>0?(A.style.display="",A.textContent=H>99?"99+":String(H)):A.style.display="none"}function B(){_(),y(),L(),x()}function E(){const A=[],H=new Date,P=_userInfo&&(_userInfo.email||_userInfo.username)||"—";A.push("# Pearnly "+e+" 测试结果"),A.push("- 账号:"+P),A.push("- 时间:"+H.toISOString().replace("T"," ").slice(0,19));const R=a.length,D=a.filter(function(ne){return o[ne.id]==="pass"}).length,j=a.filter(function(ne){return o[ne.id]==="fail"}).length,F=a.filter(function(ne){return o[ne.id]==="skip"}).length,ee=R-D-j-F;A.push("- 进度:"+(D+j+F)+" / "+R+" · ✅ "+D+" · ❌ "+j+" · ⏭ "+F+" · 未测 "+ee),A.push(""),A.push("| ID | 描述 | 状态 |"),A.push("|---|---|---|"),a.forEach(function(ne){const fe=o[ne.id],me=fe==="pass"?"✅":fe==="fail"?"❌":fe==="skip"?"⏭":"⬜";A.push("| "+ne.id+" | "+ne.desc.replace(/\|/g,"\\|")+" | "+me+" |")});const te=a.filter(function(ne){return o[ne.id]==="fail"});te.length>0&&(A.push(""),A.push("## ❌ 失败项"),te.forEach(function(ne){A.push("- **"+ne.id+"** · "+ne.desc)}));const ie=(window._pearnlyTcLogs||[]).slice(-30).reverse();return ie.length>0&&(A.push(""),A.push("## 🔴 异常日志(最近 "+ie.length+" 条)"),ie.forEach(function(ne){if(A.push("- `"+f(ne.ts)+"` · **"+ne.type+"** · "+ne.summary),ne.detail){let fe;try{fe=JSON.stringify(ne.detail)}catch{fe=String(ne.detail)}fe&&fe!=="{}"&&A.push("  - "+fe.slice(0,600))}})),A.join(`
`)}function w(A){const H=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(H.length===0)return"(暂无异常日志)";const P=["# Pearnly 异常日志(最近 "+H.length+" 条)"],R=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return P.push("- 账号:"+R),P.push("- 当前页:"+(currentRoute||"?")),P.push("- UA:"+navigator.userAgent),P.push(""),H.forEach(function(D){if(P.push("## `"+f(D.ts)+"` · "+D.type),P.push("- "+D.summary),D.detail){P.push("```");try{P.push(JSON.stringify(D.detail,null,2).slice(0,2e3))}catch{P.push(String(D.detail).slice(0,2e3))}P.push("```")}}),P.join(`
`)}function I(){const A=Date.now();fetch("/api/health").then(function(H){const P=Date.now()-A;H.ok?u(c("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:P}),"success"):u(c("tc-toast-health-fail","后端无响应")+" ("+H.status+")","error")}).catch(function(){u(c("tc-toast-health-fail","后端无响应"),"error")})}function M(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}B(),u(c("tc-toast-cleared","session 状态已清空"),"success")}function S(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(A){return A.json()}).then(function(A){window._clientsCache=A.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),u("客户缓存已刷新 · "+(A.clients||[]).length+" 个客户","success")}).catch(function(){u("刷新失败","error")})}catch{}}function C(){if(i||!document.getElementById("page-test-center"))return;i=!0;const H=document.getElementById("tc-checklist-body");H&&H.addEventListener("click",function(fe){const me=fe.target.closest(".tc-status-btn");if(!me)return;const q=me.getAttribute("data-id"),N=me.getAttribute("data-kind");!q||!N||(o[q]===N?delete o[q]:o[q]=N,p(),y(),_())});const P=document.getElementById("tc-btn-reset-checklist");P&&P.addEventListener("click",function(){o={},p(),y(),_()});const R=document.getElementById("tc-btn-copy-all");R&&R.addEventListener("click",function(){m(E())});const D=document.getElementById("tc-btn-copy-logs");D&&D.addEventListener("click",function(){m(w())});const j=document.getElementById("tc-btn-clear-logs");j&&j.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,L(),x()});const F=document.getElementById("tc-logs-filter");F&&F.addEventListener("click",function(fe){const me=fe.target.closest(".tc-filter-chip");me&&(s=me.getAttribute("data-filter")||"all",L())});const ee=document.getElementById("tc-logs-body");ee&&ee.addEventListener("click",function(fe){const me=fe.target.closest(".tc-log-item");me&&me.classList.toggle("expanded")});const te=document.getElementById("tc-tool-health");te&&te.addEventListener("click",I);const ie=document.getElementById("tc-tool-clear-session");ie&&ie.addEventListener("click",M);const ne=document.getElementById("tc-tool-reload-clients");ne&&ne.addEventListener("click",S)}function k(){}window._tcApplyVisibility=k;let T=0;const $=setInterval(function(){T++,_userInfo&&clearInterval($),T>60&&clearInterval($)},500);window.loadTestCenterPage=function(){l(),C(),B()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){x(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&B()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(v,L){if(typeof window.t=="function"){const g=window.t(v);if(g&&g!==v)return g}return L}function o(){const v=window._userInfo||{},L=String(v.role||"").toLowerCase(),g=String(v.tenant_role||"").toLowerCase();return v.is_super_admin===!0||v.is_owner===!0||L==="owner"||L==="admin"||g==="owner"||g==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const v=localStorage.getItem(e);if(!v||v==="null"||v==="0"||v==="")return null;const L=parseInt(v,10);return isNaN(L)?null:L}function r(v){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:v,mode:s()}}))}catch{}}function c(v){const L=i();v==null||v===0?localStorage.removeItem(e):(localStorage.setItem(e,String(v)),localStorage.setItem(n,"client")),String(L)!==String(v)&&r(v)}function l(){const v=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),v!=null&&r(null)}async function p(){try{const v=window.apiGet;if(typeof v!="function")return[];const L=await v("/api/workspace/clients");return L&&(L.clients||L.items)||[]}catch{return[]}}async function f(v){if(s()==="client"&&i()!=null)return typeof v=="function"&&v(),!0;const L=a("ws-need-client","这个功能需要先选择工作空间"),g=a("ws-btn-pick","选择工作空间"),x=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(L,{okText:g,cancelText:x})&&d(v):window.confirm(L+`

[`+g+" / "+x+"]")&&d(v),!1}async function d(v){const L=await p();if(typeof v=="function"&&s()!=="personal"&&L.length===1){c(Number(L[0].id)),v();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:L,canCreate:o(),active:i(),onPersonal:l,onPick:function(g){c(Number(g)),typeof v=="function"&&v()},emptyHint:L.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!L.length){const g=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(g,"info")}}function u(v){const L=v||document.getElementById("workspace-switcher-root");if(!L)return;const g=s(),x=i();let B,E;if(g==="client"&&x!=null){const M=(window._workspaceClientsCache||[]).find(S=>Number(S.id)===Number(x));B=h("building"),E=M?M.name:a("ws-current-label","当前工作空间")}else B=h("user"),E=a("ws-personal","个人事务");L.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+B+'<span class="ws-ctrl-label">'+m(E)+"</span></button>";const w=L.querySelector("#ws-ctrl-btn");w&&w.addEventListener("click",()=>d(null))}function m(v){return String(v??"").replace(/[&<>"']/g,function(L){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[L]})}function h(v){const L='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return v==="building"?L+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':L+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function _(v){v=v||{};const L=v.clients||[],g=v.active,x=document.getElementById("ws-modal");x&&x.remove();const B=document.createElement("div");B.id="ws-modal",B.className="ws-modal";const w='<button type="button" class="ws-modal-item'+(s()==="personal"||g==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+h("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+m(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+m(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let I="";if(L.length){const T=['<option value="">'+m(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(L.map(function($){const A=g!=null&&Number(g)===Number($.id);return'<option value="'+m($.id)+'"'+(A?" selected":"")+">"+m($.name||"#"+$.id)+"</option>"}));I='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+m(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+T.join("")+"</select></div>"}const M=!L.length&&v.emptyHint?'<div class="ws-modal-empty">'+m(v.emptyHint)+"</div>":"",S=v.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+m(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+m(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+m(a("ws-create-submit","创建"))+"</button></div></div>":"";B.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+m(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+m(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+w+I+"</div>"+M+S+"</div>",document.body.appendChild(B);const C=B.querySelector("[data-ws-select]");C&&C.addEventListener("change",function(){const T=C.value;T&&(typeof v.onPick=="function"&&v.onPick(T),k(),u())});function k(){B.remove()}B.addEventListener("click",function(T){if(T.target===B||T.target.closest("[data-ws-close]")){k();return}if(T.target.closest("[data-ws-personal]")){typeof v.onPersonal=="function"&&v.onPersonal(),k(),u();return}const A=T.target.closest("[data-ws-pick]");if(A){const R=A.getAttribute("data-ws-pick");typeof v.onPick=="function"&&v.onPick(R),k(),u();return}if(T.target.closest("[data-ws-create-toggle]")){const R=B.querySelector("[data-ws-create-form]");if(R){R.style.display=R.style.display==="none"?"flex":"none";const D=R.querySelector("[data-ws-create-name]");D&&D.focus()}return}if(T.target.closest("[data-ws-create-submit]")){y(B,v,k);return}})}async function y(v,L,g){const x=v.querySelector("[data-ws-create-name]"),B=x?(x.value||"").trim():"";if(!B){x&&x.focus();return}let E=null;try{if(typeof window.apiPost=="function"){const I=await window.apiPost("/api/workspace/clients",{name:B});E=I&&typeof I.json=="function"?await I.json().catch(()=>null):I}}catch{E=null}const w=E&&(E.id||E.client&&E.client.id);if(!w){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await p(),c(Number(w)),L.onPick,g(),u()}window.openWorkspaceChooserUI=_,window.addEventListener("pearnly:workspace-changed",function(){u()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=c,window.enterPersonalMode=l,window.requireWorkspace=f,window.openWorkspaceChooser=d,window.renderWorkspaceControl=u,window.fetchWorkspaceClients=p;function b(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){d(null)},800)}catch{}}p().then(v=>{window._workspaceClientsCache=v,u(),b()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",u)})();(function(){const e=g=>document.querySelector('[data-num-target="'+g+'"]');function n(g){if(!g)return t("reconcile-last-activity-none");try{const x=new Date(g),B=new Date,E=B-x;if(E/6e4<5)return t("reconcile-last-activity-just-now");if(x.toDateString()===B.toDateString())return t("reconcile-last-activity-today");const I=Math.max(1,Math.floor(E/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",I)}catch{return t("reconcile-last-activity-none")}}function a(g,x,B){const E=e(g);E&&(E.textContent=B?"-":String(x),E.classList.toggle("is-empty",!!B))}function o(g){const x=document.getElementById("reconcile-error");x&&(x.style.display=g?"flex":"none")}function s(g){const x=document.getElementById("reconcile-empty");x&&(x.style.display=g?"flex":"none")}function i(g,x){const B=document.getElementById("reconcile-last-activity");B&&(B.textContent=g,B.classList.toggle("has-data",!!x))}function r(g){const x=!g||(g.total_sessions||0)===0;a("pending",g.pending||0,x),a("matched",g.matched||0,x),a("unmatched",g.unmatched||0,x),i(n(g.last_activity_at),!!g.last_activity_at),o(!1),s(x)}function c(g){const x=g.toUpperCase();return x==="KBANK"?"bank-chip-kbank":x==="SCB"?"bank-chip-scb":x==="BBL"?"bank-chip-bbl":x==="KTB"?"bank-chip-ktb":x==="TTB"?"bank-chip-ttb":"bank-chip-other"}function l(g,x){const B=E=>E?String(E).slice(0,10):"?";return!g&&!x?"":B(g)+" ~ "+B(x)}function p(g){return g==null?"":String(g).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function f(g){const x=document.getElementById("reconcile-recent"),B=document.getElementById("reconcile-recent-list");if(!x||!B)return;const E=(g||[]).slice(0,20);if(E.length===0){x.style.display="none";return}x.style.display="",s(!1),B.innerHTML=E.map(w=>{const I=w.parse_status==="parse_failed",M=w.bank_code||"OTHER",S=w.account_last4?" ···"+p(w.account_last4):"",C=l(w.period_start,w.period_end),k=p(w.source_filename||""),T=Number(w.tx_count||0),$=I?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",T)+"</span>";return'<div class="recon-card" data-session-id="'+p(w.id)+'" data-session-name="'+k+'"><span class="bank-chip '+c(M)+'">'+p(M)+'</span><div class="recon-card-main"><div class="recon-card-title">'+k+S+'</div><div class="recon-card-sub">'+p(C)+'</div></div><div class="recon-card-right">'+$+'</div><button class="recon-card-trash" data-trash="'+p(w.id)+'" title="'+p(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),B.querySelectorAll(".recon-card").forEach(w=>{w.addEventListener("click",I=>{I.target.closest(".recon-card-trash")||(w.dataset.sessionId,d())})}),B.querySelectorAll(".recon-card-trash").forEach(w=>{w.addEventListener("click",I=>{I.stopPropagation();const M=w.dataset.trash,S=w.closest(".recon-card"),C=S&&S.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(M,C)})})}function d(g){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const x=document.querySelector('[data-recon-tab="bank"]');x&&x.click()},150)}function u(){o(!0),s(!1)}function m(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const g=document.querySelector('[data-recon-tab="bank"]');g&&g.click()},150)}async function h(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),o(!1),s(!1);const g=document.getElementById("reconcile-recent");g&&(g.style.display="none");const x={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[B,E]=await Promise.all([fetch("/api/bank-recon/stats",{headers:x}),fetch("/api/bank-recon/sessions?limit=20",{headers:x})]);if(!B.ok)throw new Error("http "+B.status);const w=await B.json(),I=E.ok?await E.json():[];r(w||{}),f(I||[])}catch(B){console.warn("[reconcile] load failed",B),u()}}function _(g){if(!g||!g.length)return;const x="Bearer "+(localStorage.getItem("mrpilot_token")||"");let B=0;const E=g.length;Array.from(g).forEach(function(w){const I=new FormData;I.append("file",w,w.name);const M=new XMLHttpRequest;M.open("POST","/api/bank-recon/upload"),M.setRequestHeader("Authorization",x),M.onload=function(){B++;try{const S=JSON.parse(M.responseText);M.status===200&&S.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",S.tx_count),"success"):showToast(w.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(w.name+" "+(t("upload-failed")||"上传失败"),"error")}B===E&&setTimeout(h,600)},M.onerror=function(){B++,showToast(w.name+" "+(t("upload-failed")||"上传失败"),"error"),B===E&&setTimeout(h,600)},M.send(I)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function y(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const g=document.getElementById("reconcile-bank-file-input");g&&g.addEventListener("change",function(){_(this.files),this.value=""}),document.addEventListener("click",x=>{if(x.target.closest("#btn-reconcile-upload-top")||x.target.closest("#btn-reconcile-upload-empty")){m();return}if(x.target.closest("#btn-reconcile-retry")){h();return}if(x.target.closest("#btn-reconcile-dev-seed")){L();return}})}const b=["468b50c1-5593-4fd6-990d-515ce8085563"];function v(){const g=document.getElementById("btn-reconcile-dev-seed");if(!g)return;const x=typeof _userInfo<"u"?_userInfo:null,B=x&&x.id&&b.indexOf(String(x.id))>=0;g.style.display=B?"":"none"}async function L(){try{const g=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!g.ok)throw new Error("seed:"+g.status);const x=await g.json(),B=(t("reconcile-dev-seed-ok")||"").replace("{n}",x.tx_count||0);showToast(B,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const E=document.querySelector('[data-auto-tab="bank"]');E&&E.click(),x.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(x.session_id)},300)}catch(g){console.warn("[reconcile] dev seed failed",g),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){y(),v(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await h()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&h().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const h=a();if(h){if(!e.clients.length){h.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}h.innerHTML=e.clients.map(_=>{const y=String(_.id),b=e.selected.has(y)?"checked":"",v=escapeHtml(_.name||_.label||"#"+y),L=_.code?'<span class="assign-row-code">'+escapeHtml(_.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(y)+'" '+b+'><span class="assign-row-name">'+v+"</span>"+L+"</label>"}).join(""),c()}}function c(){const h=s();if(h){const y=t("assign-selected-count")||"已选 {n} / {total}";h.textContent=y.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const _=o();_&&(_.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function l(){const h=i();h&&(h.textContent=e.employeeName?" · "+e.employeeName:"")}async function p(h,_){e.employeeId=h,e.employeeName=_||"",e.opened=!0,e.selected=new Set,e.clients=[],l();const y=a();y&&(y.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const b=n();b&&(b.style.display="flex");try{const[v,L]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(h)+"/assignments")]);e.clients=v&&v.clients||[];const g=L&&L.client_ids||[];e.selected=new Set(g.map(String)),r()}catch(v){console.error("[assign-clients] load failed",v);const L=a();L&&(L.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function f(){e.opened=!1;const h=n();h&&(h.style.display="none")}async function d(){if(!e.employeeId)return;const h=Array.from(e.selected).map(y=>parseInt(y,10)).filter(y=>!isNaN(y)),_=document.getElementById("assign-modal-save");_&&(_.disabled=!0);try{const y=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:h});y&&y.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",h.length),"success"),f(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(y){console.error("[assign-clients] save failed",y),showToast(t("assign-save-failed")||"保存失败","error")}finally{_&&(_.disabled=!1)}}function u(){const h=n();if(!h||h.dataset.bound==="1")return;h.dataset.bound="1";const _=document.getElementById("assign-modal-close");_&&_.addEventListener("click",f);const y=document.getElementById("assign-modal-cancel");y&&y.addEventListener("click",f);const b=document.getElementById("assign-modal-save");b&&b.addEventListener("click",d),h.addEventListener("click",function(g){g.target===h&&f()});const v=o();v&&v.addEventListener("change",function(){v.checked?e.selected=new Set(e.clients.map(g=>String(g.id))):e.selected=new Set,r()});const L=a();L&&L.addEventListener("change",function(g){const x=g.target.closest('input[type="checkbox"][data-cid]');if(!x)return;const B=x.dataset.cid;x.checked?e.selected.add(B):e.selected.delete(B),c()})}function m(){e.opened&&(l(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",m),window.openAssignClientsModal=function(h,_){u(),p(h,_)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(f){if(!f)return"";try{return new Date(f).toLocaleString()}catch{return f}}function a(f){const d=document.getElementById("access-log-table");d&&(d.innerHTML='<div class="access-log-empty">'+escapeHtml(f)+"</div>");const u=document.getElementById("access-log-pager");u&&(u.innerHTML="")}function o(){const f=document.getElementById("access-log-table");if(!f)return;const d=e.rows||[];if(!d.length){a(t("set-access-log-empty"));return}const u=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,m=d.map(function(h){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(h.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(h.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(h.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(h.target_name||h.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(h.ip||"-")}</div>
                </div>`}).join("");f.innerHTML=u+m}function s(){const f=document.getElementById("access-log-pager");if(!f)return;const d=e.total||0;if(!d){f.innerHTML="";return}const u=e.page||1,m=e.per_page,h=Math.max(1,Math.ceil(d/m)),_=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",d),y=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",u).replace("{t}",h);f.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(_)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u-1}" ${u<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(y)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u+1}" ${u>=h?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(f){const d=localStorage.getItem("mrpilot_token");if(d){e.page=f||1,a(t("set-access-log-loading"));try{const u="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),m=await fetch(u,{headers:{Authorization:"Bearer "+d}});if(m.status===403){a(t("set-access-log-empty"));return}if(!m.ok)throw new Error("http_"+m.status);const h=await m.json();e.rows=h.logs||[],e.total=h.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const f=localStorage.getItem("mrpilot_token");if(f)try{const d="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),u=await fetch(d,{headers:{Authorization:"Bearer "+f}});if(!u.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const m=await u.blob(),h=document.createElement("a"),_=URL.createObjectURL(m);h.href=_,h.download="pearnly_access_log.csv",document.body.appendChild(h),h.click(),setTimeout(function(){URL.revokeObjectURL(_),h.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function c(){const f=document.querySelectorAll(".set-tab-owner-only"),d=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));f.forEach(function(u){u.style.display=d?"":"none"})}document.addEventListener("click",function(f){if(f.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(f.target.closest("#access-log-csv-btn")){f.preventDefault(),r();return}const m=f.target.closest(".access-log-pager-btn[data-access-log-page]");if(m&&!m.disabled){const h=parseInt(m.dataset.accessLogPage,10);i(h)}}),document.addEventListener("input",function(f){f.target&&f.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(f.target.value||"").trim(),i(1)},350))});let l=0;const p=setInterval(function(){l++,_userInfo&&(c(),clearInterval(p)),l>60&&clearInterval(p)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){c(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=B=>document.getElementById(B);async function n(B,E){return await fetch(B,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(E||{})})}async function a(B){return await fetch(B,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function i(B,E){if(!B)return;B.style.display="",B.className="notif-line-check "+(E?"bound":"unbound");const w=E?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';B.innerHTML=w+"<span>"+escapeHtml(t(E?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(B){if(B==null)return"-";const E=Number(B);return isNaN(E)?String(B):"฿ "+E.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function c(B){if(!B)return"-";try{const E=new Date(B),w=(E.getMonth()+1).toString().padStart(2,"0"),I=E.getDate().toString().padStart(2,"0"),M=E.getHours().toString().padStart(2,"0"),S=E.getMinutes().toString().padStart(2,"0");return`${w}-${I} ${M}:${S}`}catch{return B}}function l(B){const E=e("notif-rules-list"),w=e("notif-rules-empty"),I=e("notif-rules-count");if(!(!E||!w)){if(I.textContent=String(B.length),I.className="auto-status-pill "+(B.length>0?"active":"none"),!B.length){w.style.display="",E.style.display="none",E.innerHTML="";return}w.style.display="none",E.style.display="",E.innerHTML=B.map(M=>{const S=M.template_code==="large_invoice",C=S?"notif-rule-large-tag":"notif-rule-exception-tag",k=S?"large":"";let T=[];if(S){const A=M.params&&M.params.threshold?r(M.params.threshold):"-";T.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+A)}M.enabled||T.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const $=T.length?T.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${M.enabled?"":" disabled"}" data-rule-id="${M.id}">
                    <span class="notif-rule-tmpl-badge ${k}">${escapeHtml(t(C))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(M.name)}</div>
                        <div class="notif-rule-meta">${$}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${M.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function p(B){const E=e("notif-logs-list");if(E){if(!B.length){E.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}E.innerHTML=B.map(w=>{const I=w.status==="sent",M=w.event_type==="exception_high"?"notif-event-exception-high":w.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",S=I?"":" · "+escapeHtml(w.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${I?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(M))}</div>
                        <div class="notif-log-meta">${escapeHtml(w.template_code||"-")}${S}</div>
                    </div>
                    <div class="notif-log-time">${c(w.sent_at)}</div>
                </div>`}).join("")}}async function f(){try{const B=await apiGet("/api/notifications/rules");d=B&&B.items||[],l(d)}catch(B){console.warn("load rules fail",B)}try{const B=await apiGet("/api/notifications/logs?limit=20");u=B&&B.items||[],p(u)}catch(B){console.warn("load logs fail",B)}}let d=null,u=null;function m(){d&&l(d),u&&p(u);const B=e("notif-new-modal");B&&B.style.display!=="none"&&o&&i(e("notif-line-check"),!!(o&&o.bound))}function h(){const B=e("notif-new-modal");B&&(B.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(E=>E.checked=!1),s().then(E=>i(e("notif-line-check"),!!(E&&E.bound))))}function _(){const B=e("notif-new-modal");B&&(B.style.display="none")}function y(){const B=document.querySelector('input[name="notif-template"]:checked'),E=e("notif-new-threshold-row");if(!B){E.style.display="none";return}E.style.display=B.value==="large_invoice"?"":"none";const w=e("notif-new-name");w&&!w.value.trim()&&(w.value=B.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function b(){const B=document.querySelector('input[name="notif-template"]:checked');if(!B){showToast(t("notif-new-template"),"error");return}const E=(e("notif-new-name").value||"").trim();if(!E){showToast(t("notif-name-required"),"error");return}const w={name:E,template_code:B.value,params:{},enabled:!0};if(B.value==="large_invoice"){const I=parseFloat(e("notif-new-threshold").value||"0");if(!I||I<=0){showToast(t("notif-threshold-required"),"error");return}w.params.threshold=I}try{const I=await apiPost("/api/notifications/rules",w);if(I&&I.ok)showToast(t("notif-toast-created"),"success"),_(),f();else{const M=await(I&&I.json&&I.json().catch(()=>({})))||{};showToast(M&&M.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function v(B,E,w){if(B==="toggle"){const I=w.classList.contains("on"),M=await n("/api/notifications/rules/"+E,{enabled:!I});M&&M.ok?(showToast(t(I?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),f()):showToast("toggle failed","error");return}if(B==="test"){const I=await s();if(!I||!I.bound){showToast(t("notif-line-error-bind-first"),"error");return}const M=await apiPost("/api/notifications/rules/"+E+"/test",{});if(M&&M.ok)showToast(t("notif-toast-test-sent"),"success"),f();else{const S=await(M&&M.json&&M.json().catch(()=>({})))||{},C=S&&S.detail||"";showToast(C||t("notif-toast-test-failed"),"error"),f()}return}if(B==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const M=await a("/api/notifications/rules/"+E);M&&M.ok?(showToast(t("notif-toast-deleted"),"success"),f()):showToast("delete failed","error");return}}let L=!1;function g(){if(L)return;L=!0;const B=e("notif-btn-new");B&&B.addEventListener("click",h);const E=e("notif-btn-refresh-logs");E&&E.addEventListener("click",f);const w=e("notif-new-close");w&&w.addEventListener("click",_);const I=e("notif-new-cancel");I&&I.addEventListener("click",_);const M=e("notif-new-save");M&&M.addEventListener("click",b),document.querySelectorAll('input[name="notif-template"]').forEach(k=>{k.addEventListener("change",y)});const S=e("notif-rules-list");S&&S.addEventListener("click",k=>{const T=k.target.closest("button[data-action]");if(!T)return;const $=T.closest("[data-rule-id]");$&&v(T.getAttribute("data-action"),$.getAttribute("data-rule-id"),T)});const C=e("notif-new-modal");C&&C.addEventListener("click",k=>{k.target===C&&_()})}async function x(){g(),await f()}window._loadNotificationsPanel=x,window._rerenderNotifications=m})();(function(){function n(b,v){try{return window.t&&window.t(b)||v}catch{return v}}function a(){var b="";try{b=localStorage.getItem("mrpilot_token")||""}catch{}return b?{Authorization:"Bearer "+b}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var b=document.createElement("style");b.id="recon-batch-style",b.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(b)}}function i(b){return b?b.dataset&&b.dataset.taskId?b.dataset.taskId:b.dataset&&b.dataset.taskid?b.dataset.taskid:"":""}function r(b){var v=document.getElementById(b.tbody);if(!v)return null;var L=v.closest("table");if(!L)return null;var g=L.querySelector("thead");if(!g)return null;if(g._reconReady)return g;var x=g.querySelector("tr");if(!x)return null;if(x.classList.add("recon-thead-default"),!x.querySelector(".recon-master-cb")){var B=document.createElement("th");B.className="recon-sel-cell";var E=document.createElement("input");E.type="checkbox",E.className="recon-master-cb",E.setAttribute("aria-label","select all"),E.addEventListener("change",function(){f(b,E.checked)}),B.appendChild(E),x.insertBefore(B,x.firstElementChild)}var w=x.children[1];w&&!w.classList.contains("recon-time-col")&&w.classList.add("recon-time-col");var I=x.children.length,M=document.createElement("tr");M.className="recon-thead-batch";var S=document.createElement("th");S.className="recon-sel-cell";var C=document.createElement("input");C.type="checkbox",C.className="recon-master-cb",C.checked=!0,C.setAttribute("aria-label","select all"),C.addEventListener("change",function(){f(b,C.checked)}),S.appendChild(C);var k=document.createElement("th");return k.setAttribute("colspan",String(I-1)),k.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',M.appendChild(S),M.appendChild(k),g.appendChild(M),k.querySelector("[data-recon-del]").addEventListener("click",function(){h(b)}),k.querySelector("[data-recon-clear]").addEventListener("click",function(){m(b)}),g._reconReady=!0,u(b),g}function c(b){var v=document.getElementById(b.tbody);if(v){var L=v.querySelectorAll("tr");L.forEach(function(g){var x=i(g);if(x&&!g.querySelector(".recon-sel-cb")){var B=g.querySelector("td");if(B){var E=document.createElement("td");E.className="recon-sel-cell";var w=document.createElement("input");w.type="checkbox",w.className="recon-sel-cb",w.dataset.taskId=x,w.dataset.kind=b.kind,w.addEventListener("click",function(M){M.stopPropagation()}),w.addEventListener("change",function(){d(b)}),E.appendChild(w),g.insertBefore(E,B);var I=g.children[1];I&&!I.classList.contains("recon-time-col")&&I.classList.add("recon-time-col")}}}),d(b)}}function l(b){var v=document.getElementById(b.tbody);return v?Array.prototype.slice.call(v.querySelectorAll(".recon-sel-cb")):[]}function p(b){return l(b).filter(function(v){return v.checked}).map(function(v){return v.dataset.taskId})}function f(b,v){l(b).forEach(function(L){L.checked=!!v}),d(b)}function d(b){var v=p(b),L=l(b),g=document.getElementById(b.tbody);if(g){var x=g.closest("table"),B=x&&x.querySelector("thead");if(B){v.length>0?B.classList.add("recon-batch-mode"):B.classList.remove("recon-batch-mode"),B.querySelectorAll(".recon-master-cb").forEach(function(w){if(L.length===0){w.checked=!1,w.indeterminate=!1;return}v.length===L.length?(w.checked=!0,w.indeterminate=!1):v.length===0?(w.checked=!1,w.indeterminate=!1):(w.checked=!1,w.indeterminate=!0)});var E=B.querySelector("[data-recon-count]");E&&(E.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",v.length))}}}function u(b){var v=document.getElementById(b.tbody);if(v){var L=v.closest("table"),g=L&&L.querySelector("thead");if(g){var x=g.querySelector("[data-recon-del-label]"),B=g.querySelector("[data-recon-clear]");x&&(x.textContent=n("recon-batch-delete","批量删除")),B&&(B.textContent=n("recon-batch-clear","取消")),d(b)}}}function m(b){l(b).forEach(function(v){v.checked=!1}),d(b)}async function h(b){var v=p(b);if(v.length){var L=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",v.length),g=!1;try{typeof window.pearnlyConfirm=="function"?g=await window.pearnlyConfirm(L,n("recon-batch-delete-title","批量删除")):g=window.confirm(L)}catch{g=!1}if(g)try{var x=Object.assign({"Content-Type":"application/json"},a()),B=b.kind==="glv"?v.map(function(M){return parseInt(M,10)}):v,E=await fetch(b.api,{method:"POST",headers:x,body:JSON.stringify({ids:B})});if(!E.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var w=await E.json(),I=w&&(w.deleted!=null?w.deleted:w.count)||v.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",I),"success"),b.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function _(b){r(b),c(b);var v=document.getElementById(b.tbody);if(!(!v||v._reconBatchWatched)){v._reconBatchWatched=!0;var L=new MutationObserver(function(){c(b)});L.observe(v,{childList:!0,subtree:!1})}}function y(){s(),o.forEach(_),document.querySelectorAll(".recon-batch-bar").forEach(function(b){try{b.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",y):y(),setTimeout(y,1500),setTimeout(y,4e3),document.addEventListener("keydown",function(b){b.key==="Escape"&&o.forEach(function(v){p(v).length>0&&m(v)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(u)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(p){};function i(p){n=p;for(let u=1;u<=a;u++){const m=document.getElementById("ob-step-"+u);m&&(m.style.display=u===p?"block":"none")}document.querySelectorAll(".ob-dot").forEach(u=>{const m=parseInt(u.dataset.step,10);u.classList.toggle("active",m===p),u.classList.toggle("done",m<p)});const f=document.getElementById("ob-step-label");f&&(f.textContent=p+" / "+a);const d=document.getElementById("ob-next");if(d&&(d.textContent=p===a?t("ob-finish"):t("ob-next")),p===4){const u=document.getElementById("ob-line-input");u&&(u.value=e.line_id||"")}}function r(p){const f=document.querySelector(".onboarding-modal");if(!f)return;let d=f.querySelector(".ob-feedback");d||(d=document.createElement("div"),d.className="ob-feedback",f.appendChild(d)),d.textContent=p,d.classList.add("show"),setTimeout(()=>d.classList.remove("show"),1800)}document.addEventListener("click",p=>{const f=p.target.closest(".ob-option");if(!f)return;const d=f.parentElement;if(!d||!d.classList.contains("ob-options"))return;d.querySelectorAll(".ob-option").forEach(m=>m.classList.remove("selected")),f.classList.add("selected");const u=f.dataset.value;d.id==="ob-role-options"?e.role=u:d.id==="ob-volume-options"?e.monthly_volume=u:d.id==="ob-country-options"&&(e.country=u)}),document.addEventListener("click",p=>{p.target.id==="ob-skip"&&c()}),document.addEventListener("click",p=>{if(p.target.id==="ob-next"){if(n===4){const f=document.getElementById("ob-line-input");e.line_id=(f&&f.value||"").trim().replace(/^@+/,"")}c()}}),document.addEventListener("click",p=>{if(p.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const f=document.getElementById("onboarding-modal");f&&(f.style.display="none")}});function c(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):l()}async function l(){const p=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const f={};if(e.role&&(f.role=e.role),e.monthly_volume&&(f.monthly_volume=e.monthly_volume),e.country&&(f.country=e.country),e.line_id&&(f.line_id=e.line_id),Object.keys(f).length===0){p&&(p.style.display="none");return}try{const d=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(f)});d.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,f),setTimeout(()=>{p&&(p.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(f)),console.warn("onboarding profile save failed",d.status),r(t("ob-fb-saved-local")),setTimeout(()=>{p&&(p.style.display="none")},1500))}catch(d){console.error("onboarding submit",d),localStorage.setItem("pilot_ob_pending",JSON.stringify(f)),p&&(p.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function c(){return"DHL Express (Thailand) Co., Ltd."}function l(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:c(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadArchiveSettings=()=>p();async function p(){const g=!!(_userInfo&&_userInfo.can_customize_archive);o=!g;const x=document.getElementById("archive-upgrade-banner");x&&(x.style.display=g?"none":"");const B=document.getElementById("archive-plus-badge");B&&(B.style.display=g?"none":"");try{const E=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!E.ok)throw new Error("load failed");const w=await E.json();e=Array.isArray(w.name_template)?w.name_template:[],n=w.folder_strategy||"by_month_seller"}catch(E){console.error("load archive settings failed",E),showToast(t("archive-load-failed"),"error");return}f(),d(),u(),m()}function f(){const g=document.getElementById("archive-rule-canvas");if(g){if(e.length===0){g.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}g.innerHTML=e.map((x,B)=>{const E=i[x.type]||{label:x.type},w=s[x.type]||"",I=x.type==="sep"?`"${escapeHtml(x.val||"_")}"`:escapeHtml(t(E.label));return`
                <span class="archive-token ${x.type}"
                      data-token-idx="${B}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${w}</span>
                    <span class="token-label">${I}</span>
                </span>
            `}).join("")}}function d(){const g=document.getElementById("archive-field-palette");if(!g)return;const x=["date","seller","category","amount","invoice","buyer","sep"];g.innerHTML=x.map(B=>{const E=i[B],w=s[B]||"";return`
                <button class="archive-palette-btn ${B}" data-add-field="${B}" ${o?"disabled":""}>
                    <span class="token-icon">${w}</span>
                    <span>${escapeHtml(t(E.label))}</span>
                </button>
            `}).join("")}function u(){document.querySelectorAll('input[name="folder-strategy"]').forEach(g=>{g.checked=g.value===n,g.disabled=o})}async function m(){const g=document.getElementById("archive-preview-name"),x=document.getElementById("archive-preview-hint");if(x&&(x.textContent=t("archive-preview-hint",{category:r()})),!!g){if(e.length===0){g.textContent="-";return}try{const E=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:l().merged_fields,name_template:e})})).json();g.textContent=(E.name||"-")+".pdf"}catch{g.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const g=document.getElementById("archive-rule-modal");!g||g.style.display==="none"||(f(),d(),m())};let h=-1;document.addEventListener("dragstart",g=>{const x=g.target.closest(".archive-token");!x||o||(h=parseInt(x.dataset.tokenIdx,10),x.classList.add("dragging"),g.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",g=>{document.querySelectorAll(".archive-token").forEach(x=>x.classList.remove("dragging","drop-target")),h=-1}),document.addEventListener("dragover",g=>{const x=g.target.closest(".archive-token");x&&(g.preventDefault(),g.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(B=>B.classList.remove("drop-target")),x.classList.add("drop-target"))}),document.addEventListener("drop",g=>{const x=g.target.closest(".archive-token");if(!x||h<0||o)return;g.preventDefault();const B=parseInt(x.dataset.tokenIdx,10);if(B===h)return;const E=e.splice(h,1)[0];e.splice(B,0,E),h=-1,f(),m()}),document.addEventListener("click",g=>{if(g.target.closest("#btn-open-archive-rule")||g.target.closest("#btn-open-archive-rule-from-settings")){const w=document.getElementById("archive-rule-modal");w&&(w.style.display="",p());return}if(g.target.closest("#archive-rule-modal-close")||g.target.id==="archive-rule-modal"){const w=document.getElementById("archive-rule-modal");w&&(w.style.display="none");return}const x=g.target.closest(".settings-nav-item");if(x){switchSettingsTab(x.dataset.settingsTab);return}if(o&&g.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const B=g.target.closest("[data-add-field]");if(B){const w=B.dataset.addField,I=i[w],M={type:w,...I.defaultCfg};e.push(M),f(),m();return}const E=g.target.closest(".archive-token");if(E&&!o){_(parseInt(E.dataset.tokenIdx,10));return}if(g.target.closest("#btn-archive-save"))return v();if(g.target.closest("#btn-archive-reset"))return L();(g.target.closest("#archive-token-close")||g.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),g.target.closest("#btn-archive-token-ok")&&y(),g.target.closest("#btn-archive-token-delete")&&b()}),document.addEventListener("change",g=>{g.target.name==="folder-strategy"&&(n=g.target.value)});function _(g){a=g;const x=e[g];if(!x)return;const B=document.getElementById("archive-token-body");let E="";x.type==="date"?E=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${x.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${x.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${x.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${x.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:x.type==="seller"?E=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${x.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:x.type==="amount"?E=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${x.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:x.type==="sep"?E=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${x.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${x.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${x.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(x.val)?"":escapeHtml(x.val||"")}">
                    </div>
                </div>`:E=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,B.innerHTML=E,document.getElementById("archive-token-modal").style.display="",B.querySelectorAll(".sep-chip").forEach(w=>{w.addEventListener("click",()=>{B.querySelectorAll(".sep-chip").forEach(M=>M.classList.remove("active")),w.classList.add("active");const I=document.getElementById("token-sep-custom");I&&(I.value="")})})}function y(){const g=e[a];if(g){if(g.type==="date")g.format=document.getElementById("token-date-format").value;else if(g.type==="seller")g.short=document.getElementById("token-seller-short").checked;else if(g.type==="amount")g.with_currency=document.getElementById("token-amount-currency").checked;else if(g.type==="sep"){const x=document.querySelector("#archive-token-body .sep-chip.active"),B=document.getElementById("token-sep-custom").value;g.val=B||(x?x.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",f(),m()}}function b(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",f(),m())}async function v(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const x=document.getElementById("archive-rule-modal");x&&(x.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function L(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",f(),u(),m())}})();(function(){window.loadAboutPanel=()=>e(),window.loadPrefsSettings=()=>n();function e(){const o=document.getElementById("settings-contact-grid");if(!o)return;const s=_contact?.phone||"086-889-2228",i=_contact?.line_id||"@Pearnly",r=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",c=_contact?.email||"hello@pearnly.com",l=_contact?.address||"Bangkok, Thailand";o.innerHTML=`
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
                    <div class="contact-value">${escapeHtml(l)}</div>
                </div>
            </div>
        `}async function n(){try{const o=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!o.ok)return;const s=await o.json(),i=document.getElementById("pref-dup-check");i&&(i.checked=!!s.enabled)}catch(o){console.warn("load prefs failed",o)}}const a=document.getElementById("pref-dup-check");a&&!a.dataset.bound&&(a.dataset.bound="1",a.addEventListener("change",async o=>{const s=o.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:s})})).ok?showToast(s?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(o.target.checked=!s,showToast(t("pref-save-failed"),"error"))}catch{o.target.checked=!s,showToast(t("pref-save-failed"),"error")}}))})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,i=null,r=0,c=0,l=!1;function p(v){const L=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return v.preventDefault(),v.returnValue=L,L}function f(){l||(l=!0,window.addEventListener("beforeunload",p))}function d(){l&&(l=!1,window.removeEventListener("beforeunload",p))}function u(){if(document.getElementById("big-batch-progress"))return;const v=document.getElementById("file-list");if(!v||!v.parentNode)return;const L=document.createElement("div");L.id="big-batch-progress",L.className="big-batch-progress",L.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',v.parentNode.insertBefore(L,v);const g=document.getElementById("bbp-text");g&&(g.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function m(){const v=document.getElementById("big-batch-progress");v&&v.remove()}function h(){if(!i)return;let v=0;for(let M=0;M<i.length;M++){const S=i[M].status;(S==="success"||S==="error"||S==="cancelled")&&v++}const L=r,g=L>0?Math.min(100,Math.floor(100*v/L)):0,x=(Date.now()-c)/1e3;let B;if(v>=3&&x>1){const M=x/v;B=(L-v)*M}else B=(L-v)*6/6;const E=Math.max(1,Math.ceil(B/60)),w=document.getElementById("bbp-fill"),I=document.getElementById("bbp-text");w&&(w.style.width=g+"%"),I&&(v>=L?I.textContent=t("big-batch-progress-done").replace("{total}",L):I.textContent=t("big-batch-progress-running").replace("{done}",v).replace("{total}",L).replace("{min}",E))}function _(v){try{if(localStorage.getItem(o)==="1")return}catch{}const L=Math.max(1,Math.ceil(v*6/6/60)),g=t("big-batch-first-tip").replace("{n}",v).replace("{min}",L);typeof showToast=="function"&&showToast(g,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function y(v){!v||v.length<100||(i=v,r=v.length,c=Date.now(),u(),f(),_(r),s&&clearInterval(s),s=setInterval(h,250),h())}function b(){s&&(clearInterval(s),s=null),d(),i&&r>=100?(h(),setTimeout(m,1200)):m(),i=null,r=0}window._bigBatchStart=y,window._bigBatchStop=b,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&h()})})();(function(){let e=null,n=!1,a=!1;function o(w){return typeof escapeHtml=="function"?escapeHtml(w==null?"":String(w)):String(w??"")}function s(w,I){try{typeof showToast=="function"&&showToast(w,I||"info")}catch{}}function i(){const w=typeof _userInfo<"u"?_userInfo:null;return!!(w&&(w.role==="owner"||w.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(w){if(!w)return!1;const I=String(w.status||"").toLowerCase();return I==="exception"||I==="exception_pending"||I==="rejected"}async function l(w){if(n&&!w)return e;const I=localStorage.getItem("mrpilot_token");if(!I)return null;try{const M=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+I}});if(!M.ok)throw new Error("http_"+M.status);e=await M.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function p(){const w=document.getElementById("erp-connect-cards");if(!w)return;const I=e;let M,S=!1;I?I.configured?I.connected?(S=!0,M='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):M='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":M='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":M='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let C="";if(!I||!I.configured)C='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!I.connected)i()&&(C='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const j=!!I.auto_push,F=j?t("card-btn-disable"):t("card-btn-enable");C='<button type="button" class="'+(j?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(j?"1":"0")+'" title="'+o(j?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(F)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const k=I&&I.connected?"xero-card-desc-connected":"xero-card-desc-default",T=I&&I.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",$=(function(){const j=t(k);return j===k?T:j})();let A='<div class="integration-row erp-connect-xero'+(S?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+M+'</div><div class="int-desc">'+o($)+'</div></div><div class="int-actions">'+C+"</div></div>";if(I&&I.configured&&I.connected&&i()){const j=I.organisations||[];let F="";if(j.length>0){F+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(j.length)))+"</div>",F+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",F+='<div class="erp-cc-orgs">',j.forEach(function(ie){F+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(ie.id)+'"'+(ie.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(ie.organisation_name||ie.organisation_id)+"</span></label>"}),F+="</div>";const ee=!!I.auto_push,te=ee?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");F+='<div class="erp-cc-auto-push" title="'+o(te)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(ee?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",F+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}A+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+F+"</div>"}const H=w.querySelector(".erp-connect-xero"),P=w.querySelector("#erp-xero-details");P&&P.remove(),H?H.outerHTML=A:w.insertAdjacentHTML("afterbegin",A);const R=document.getElementById("btn-xero-edit-toggle");R&&R.addEventListener("click",function(j){j.preventDefault();const F=document.getElementById("erp-xero-details");F&&(F.style.display=F.style.display==="none"?"":"none")});const D=document.getElementById("btn-xero-toggle-enabled");D&&D.addEventListener("click",async function(j){if(j.preventDefault(),D.disabled)return;const ee=!(D.getAttribute("data-xero-enabled")==="1");if(!ee)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}D.disabled=!0,await m(ee,null)})}async function f(){const w=localStorage.getItem("mrpilot_token");if(w)try{const I=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+w}});if(!I.ok){let S="unknown";try{S=(await I.json()).detail||"unknown"}catch{}const C=String(S).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+C)||S),"error");return}const M=await I.json();M.redirect_url&&(window.location.href=M.redirect_url)}catch(I){s(t("xero-push-fail").replace("{err}",I.message||"network"),"error")}}async function d(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const I=localStorage.getItem("mrpilot_token");try{const M=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+I}});if(!M.ok)throw new Error("http_"+M.status);await l(!0),p()}catch(M){s(t("xero-push-fail").replace("{err}",M.message),"error")}}async function u(w){const I=localStorage.getItem("mrpilot_token");try{const M=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+I,"Content-Type":"application/json"},body:JSON.stringify({token_id:w})});if(!M.ok)throw new Error("http_"+M.status);await l(!0),p()}catch(M){s(t("xero-push-fail").replace("{err}",M.message),"error")}}async function m(w,I){const M=localStorage.getItem("mrpilot_token");I&&(I.disabled=!0);try{const S=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+M,"Content-Type":"application/json"},body:JSON.stringify({on:!!w})});if(!S.ok){let C="unknown";try{C=(await S.json()).detail||"unknown"}catch{}throw new Error(C)}s(w?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await l(!0),p()}catch(S){I&&(I.checked=!w),s(t("erp-auto-push-toggle-fail").replace("{err}",S.message||"network"),"error")}finally{I&&(I.disabled=!1)}}async function h(){const w=document.getElementById("drawer-history-save");if(!w||w.querySelector("#btn-xero-push")||w.querySelector("#pn-push-wrap")||(await l(!1),w.querySelector("#pn-push-wrap"))||w.querySelector("#btn-xero-push"))return;const I=r();if(!(I&&(I._historyId||I.history_id)))return;let S=!1,C="xero-push-tip";!e||!e.configured?(S=!0,C="xero-err-not_configured"):e.connected?c(I)&&(S=!0,C="xero-push-disabled-exc"):(S=!0,C="xero-push-disabled-no-conn");const k=document.createElement("button");k.type="button",k.id="btn-xero-push",k.className="btn btn-ghost"+(S?" disabled":""),k.disabled=S,k.title=t(C)||"",k.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",k.addEventListener("click",_);const T=document.getElementById("btn-push-erp");T&&T.parentNode?T.parentNode.insertBefore(k,T.nextSibling):w.insertBefore(k,w.firstChild)}async function _(){const w=r(),I=w&&(w._historyId||w.history_id);if(!I)return;const M=document.getElementById("btn-xero-push");M&&(M.disabled=!0,M.classList.add("loading"));const S=localStorage.getItem("mrpilot_token");try{const C=await fetch("/api/erp/xero/push/"+encodeURIComponent(I),{method:"POST",headers:{Authorization:"Bearer "+S}});if(!C.ok){let k="unknown";try{k=(await C.json()).detail||"unknown"}catch{}const T=String(k).replace(/^xero\./,"").toLowerCase(),$=t("xero-"+T),A=$&&$!=="xero-"+T?$:k;s(t("xero-push-fail").replace("{err}",A),"error");return}s(t("xero-push-ok"),"success")}catch(C){s(t("xero-push-fail").replace("{err}",C.message||"network"),"error")}finally{M&&(M.disabled=!1,M.classList.remove("loading"))}}async function y(){await l(!0),p(),b()}async function b(){const w=document.getElementById("erp-global-push-mode");if(!w)return;const I=localStorage.getItem("mrpilot_token");if(I)try{const M=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+I}});if(M.ok){const S=await M.json();S.mode&&(w.value=S.mode,w.dataset.prev=S.mode)}}catch{}}async function v(w){const I=w.value,M=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+M,"Content-Type":"application/json"},body:JSON.stringify({mode:I})})).ok?(w.dataset.prev=I,s(t("pref-erp-mode-saved"),"success")):(w.value=w.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{w.value=w.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function L(){try{const w=String(window.location.hash||"");if(w.indexOf("xero=ok")>=0){const I=w.match(/n=(\d+)/),M=I?I[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",M),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),l(!0).then(p)}else w.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function g(){if(a)return;a=!0,document.addEventListener("click",function(I){if(I.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(y,50);return}if(I.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(y,80);return}if(I.target.closest("#btn-xero-connect")){I.preventDefault(),f();return}if(I.target.closest("#btn-xero-disconnect")){I.preventDefault(),d();return}}),document.addEventListener("change",function(I){I.target&&I.target.matches('input[name="xero-default-org"]')&&u(I.target.value),I.target&&I.target.id==="xero-auto-push-toggle"&&m(I.target.checked,I.target),I.target&&I.target.id==="erp-global-push-mode"&&v(I.target)});const w=function(){return document.getElementById("drawer-body")};try{const I=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&h()}),M=w();if(M)I.observe(M,{childList:!0,subtree:!0});else{const S=new MutationObserver(function(){const C=w();C&&(I.observe(C,{childList:!0,subtree:!0}),S.disconnect())});S.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(L,500)}function x(){e&&p();const w=document.getElementById("btn-xero-push");if(w){const I=w.querySelector("span");I&&(I.textContent=t("xero-push-btn"))}}g(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",x);async function B(w){const I=Date.now();for(;Date.now()-I<w;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(M=>setTimeout(M,80))}return null}async function E(){await B(5e3);const w=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),I=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');w&&I&&await y()}setTimeout(E,200)})();(function(){var e="https://www.mrerp4sme.com/dms/index.php",n=null,a=!1;function o(y){return typeof escapeHtml=="function"?escapeHtml(y==null?"":String(y)):String(y??"")}function s(y,b){try{typeof showToast=="function"&&showToast(y,b||"info")}catch{}}function i(){return localStorage.getItem("mrpilot_token")}async function r(y){var b=i();if(!b)return null;try{var v=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+b}});if(!v.ok)throw new Error("http_"+v.status);var L=await v.json(),g=L&&L.items||[];n=g.find(function(x){return x&&(x.adapter||"").toLowerCase()==="mrerp_dms"})||null,a=!0}catch{n=null,a=!1}return n}function c(){var y=document.getElementById("erp-connect-cards");if(y){var b=y.querySelector("[data-mrerp-dms-zone]");b||(b=document.createElement("div"),b.setAttribute("data-mrerp-dms-zone","1"),y.appendChild(b));var v=n,L=!!(v&&v.enabled!==!1),g;v?L?g='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("dms-card-connected"))+"</span>":g='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-disabled-pill"))+"</span>":g='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-not-connected"))+"</span>";var x;if(!v)x='<button type="button" class="int-btn-configure" id="btn-dms-connect">'+o(t("dms-card-connect"))+"</button>";else{var B=L?t("dms-card-disable"):t("dms-card-enable");x='<button type="button" class="int-btn-configure" id="btn-dms-edit">'+o(t("dms-card-edit"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-test">'+o(t("dms-card-test"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-toggle">'+o(B)+"</button>"}b.innerHTML='<div class="integration-row erp-connect-mrerp-dms'+(L?" connected":"")+'"><div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/><path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("dms-card-title"))+"</span>"+g+'</div><div class="int-desc">'+o(t("dms-card-desc"))+'</div></div><div class="int-actions">'+x+"</div></div>"}}function l(){var y=document.getElementById("dms-wizard-overlay");y&&y.remove(),document.removeEventListener("keydown",p)}function p(y){y.key==="Escape"&&l()}function f(){l();var y=n,b=y&&y.config&&y.config.booking_defaults&&y.config.booking_defaults.booking_prefix||"PN",v=function(x,B,E,w,I){return'<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">'+o(t(x))+'</span><input id="'+B+'" type="'+E+'" value="'+o(w||"")+'" placeholder="'+o(I||"")+'" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;"></label>'},L=document.createElement("div");L.id="dms-wizard-overlay",L.style.cssText="position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;",L.innerHTML='<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">'+o(t("dms-wizard-title"))+'</div><div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">'+o(t("dms-card-desc"))+"</div>"+v("dms-wizard-username","dms-w-user","text","","")+v("dms-wizard-password","dms-w-pass","password","","")+v("dms-wizard-prefix","dms-w-prefix","text",b,"PN")+'<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div><div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn btn-ghost" id="dms-w-cancel">'+o(t("dms-wizard-cancel"))+'</button><button type="button" class="btn btn-primary" id="dms-w-save">'+o(t("dms-wizard-save"))+"</button></div></div>",document.body.appendChild(L),document.addEventListener("keydown",p),L.addEventListener("click",function(x){x.target===L&&l()});var g=document.getElementById("dms-w-user");g&&g.focus()}function d(y){var b=document.getElementById("dms-w-err");b&&(b.textContent=y,b.style.display=y?"":"none")}async function u(){var y=n&&n.config&&n.config.system_url||e,b=(document.getElementById("dms-w-user")||{}).value||"",v=(document.getElementById("dms-w-pass")||{}).value||"",L=(document.getElementById("dms-w-prefix")||{}).value||"PN";if(y=y.trim(),b=b.trim(),!y||!b||!v){d(t("dms-wizard-required"));return}var g=document.getElementById("dms-w-save");g&&(g.disabled=!0,g.textContent=t("dms-wizard-saving")),d("");var x=i();try{var B=await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+x,"Content-Type":"application/json"},body:JSON.stringify({adapter:"mrerp_dms",config:{system_url:y,username:b,password:v}})}),E=await B.json().catch(function(){return{}});if(!B.ok||!E.ok){var w=E.error_friendly&&(E.error_friendly[window.currentLang]||E.error_friendly.en)||t("dms-connect-fail-generic");d(w),g&&(g.disabled=!1,g.textContent=t("dms-wizard-save"));return}var I={system_url:y,username_enc:b,password_enc:v,id_card_auto_push:!0,booking_defaults:{booking_prefix:L.trim()||"PN"}},M,S;n&&n.id?(M="PATCH",S="/api/erp/endpoints/"+encodeURIComponent(n.id)):(M="POST",S="/api/erp/endpoints");var C=M==="POST"?{name:"MR.ERP DMS",adapter:"mrerp_dms",config:I,is_default:!1,auto_push:!1}:{config:I,auto_push:!1},k=await fetch(S,{method:M,headers:{Authorization:"Bearer "+x,"Content-Type":"application/json"},body:JSON.stringify(C)});if(!k.ok){var T=await k.json().catch(function(){return{}}),$=T&&T.detail&&(T.detail.code||T.detail)||"save_failed";d(t("dms-save-fail")+" ("+o(String($))+")"),g&&(g.disabled=!1,g.textContent=t("dms-wizard-save"));return}l(),s(t("dms-connect-ok"),"success"),await r(!0),c(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{d(t("dms-connect-fail-generic")),g&&(g.disabled=!1,g.textContent=t("dms-wizard-save"))}}async function m(){if(!(!n||!n.id)){s(t("dms-test-running"),"info");var y=i();try{var b=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id)+"/test-connection?refresh=1",{method:"POST",headers:{Authorization:"Bearer "+y}}),v=await b.json().catch(function(){return{}});s(v&&v.ok?t("dms-test-ok"):t("dms-test-fail"),v&&v.ok?"success":"error")}catch{s(t("dms-test-fail"),"error")}}}async function h(){if(!(!n||!n.id)){var y=n.enabled===!1;if(!y)try{var b=await window.pearnlyConfirm(t("dms-confirm-disable"));if(!b)return}catch{}var v=i();try{var L=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id),{method:"PATCH",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({enabled:y})});if(!L.ok)throw new Error("http_"+L.status);s(y?t("dms-enabled-toast"):t("dms-disabled-toast"),"success"),await r(!0),c(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{s(t("dms-save-fail"),"error")}}}function _(){r().then(c)}document.addEventListener("click",function(y){if(y.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(_,60);return}if(y.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(_,90);return}if(y.target.closest("#btn-dms-connect")||y.target.closest("#btn-dms-edit")){y.preventDefault(),f();return}if(y.target.closest("#dms-w-cancel")){y.preventDefault(),l();return}if(y.target.closest("#dms-w-save")){y.preventDefault(),u();return}if(y.target.closest("#btn-dms-test")){y.preventDefault(),m();return}if(y.target.closest("#btn-dms-toggle")){y.preventDefault(),h();return}}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("mrerp-dms-adapter",c),setTimeout(function(){var y=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),b=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');y&&b&&_()},250)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const p=`
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
        </div>`,f=document.createElement("div");f.innerHTML=p,document.body.appendChild(f.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",d=>{d.target.id==="report-modal"&&a()})}function a(){const p=document.getElementById("report-modal");p&&(p.style.display="none"),o=null}let o=null;async function s(p,f){const d=p+":"+(f||"");if(e[d])return e[d];let u;try{const m=localStorage.getItem("mrpilot_token"),h=await fetch(`/api/reports/templates?lang=${encodeURIComponent(p)}`,{headers:{Authorization:"Bearer "+m}});if(!h.ok)throw new Error("templates fetch failed");u=(await h.json()).templates||[]}catch(m){console.error("fetchTemplates fail",m),u=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(u=u.filter(m=>m.code!=="erp"),f==="history-batch"){const m=u.findIndex(_=>_.code==="standard"),h=m>=0?m+1:u.length;u.splice(h,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[d]=u,u}function i(p){const f=document.getElementById("report-tpl-list"),d=p.map((m,h)=>`
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
        `;f.innerHTML=d+u}function r(p){return p==null?"":String(p).replace(/[&<>"']/g,f=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[f])}function c(p){const f=new Date,d=f.getFullYear(),u=f.getMonth()+1;if(p==="all")return"all";if(p==="this-month")return`${d}-${String(u).padStart(2,"0")}`;if(p==="last-month"){const m=new Date(d,u-2,1);return`${m.getFullYear()}-${String(m.getMonth()+1).padStart(2,"0")}`}return p==="this-year"?`${d}`:p==="this-quarter"?`${d}-Q${Math.floor((u-1)/3)+1}`:"all"}window.openReportModal=async function(p){p=p||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(_=>{const y=_.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][y]&&(_.textContent=I18N[currentLang][y])});const f=document.getElementById("report-period-section");f&&(f.style.display=p.mode==="client"?"":"none");const d=document.getElementById("report-tpl-list");d.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const u=await s(currentLang,p&&p.mode);i(u),o=p;const m=document.getElementById("report-modal-download"),h=m.cloneNode(!0);m.parentNode.replaceChild(h,m),h.addEventListener("click",()=>l(o))};async function l(p){if(!p)return;const f=document.querySelector('input[name="report-tpl"]:checked');if(!f){showToast(t("report-toast-no-selection"),"info");return}const d=f.value,u=document.querySelector('input[name="report-period"]:checked'),m=u?u.value:"all",h=c(m),_=document.getElementById("report-modal-download"),y=_.innerHTML;_.disabled=!0,_.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const b=localStorage.getItem("mrpilot_token");let v,L;if(p.mode==="records")v=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:d,lang:currentLang,records:p.records||[],meta:p.meta||{}})}),L=`mrpilot-${d}-${Date.now()}.xlsx`;else if(p.mode==="client"){const M=`/api/reports/clients/${p.clientId}/export?template=${encodeURIComponent(d)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(h)}`;v=await fetch(M,{headers:{Authorization:"Bearer "+b}}),L=`${(p.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${d}.xlsx`}else if(p.mode==="history-batch")d==="sales_detail_th"?(v=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),L=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(v=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+b,"Content-Type":"application/json"},body:JSON.stringify({template:d,lang:currentLang,history_ids:p.historyIds||[],client_id:p.clientId||null})}),L=`mrpilot-batch-${d}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+p.mode);if(!v.ok){let M="HTTP "+v.status;try{const S=await v.json();S&&S.detail&&(M=S.detail)}catch(S){console.warn("[batch-export] resp.json err.detail parse failed:",S)}v.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+M,"error");return}const g=await v.blob();let x=L;const E=(v.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(E)try{x=decodeURIComponent(E[1])}catch{}const w=URL.createObjectURL(g),I=document.createElement("a");I.href=w,I.download=x,document.body.appendChild(I),I.click(),document.body.removeChild(I),URL.revokeObjectURL(w),showToast(t("report-toast-success"),"success"),a()}catch(b){console.error("doDownload fail",b),showToast(t("report-toast-fail")+" · "+(b.message||""),"error")}finally{_.disabled=!1,_.innerHTML=y}}document.addEventListener("DOMContentLoaded",()=>{const p=document.getElementById("btn-export");if(p){const d=p.cloneNode(!0);p.parentNode.replaceChild(d,p),d.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(u=>({filename:u.filename,merged_fields:u.merged_fields||{}}))})})}const f=document.getElementById("history-batch-export");f&&f.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(p,f){openReportModal({mode:"client",clientId:p,clientName:f||""})}})();const Rs=/\.(pdf|jpe?g|png|webp)$/i,Fs="mrpilot_folder_watcher",zs=1;let Ht=null;function Xt(){return Ht||(Ht=new Promise((e,n)=>{const a=indexedDB.open(Fs,zs);a.onupgradeneeded=o=>{const s=o.target.result;s.objectStoreNames.contains("handles")||s.createObjectStore("handles"),s.objectStoreNames.contains("seen")||s.createObjectStore("seen"),s.objectStoreNames.contains("config")||s.createObjectStore("config")},a.onsuccess=o=>e(o.target.result),a.onerror=o=>n(o.target.error)}),Ht)}function ht(e,n){return Xt().then(a=>new Promise((o,s)=>{const r=a.transaction(e,"readonly").objectStore(e).get(n);r.onsuccess=()=>o(r.result),r.onerror=()=>s(r.error)}))}function Ne(e,n,a){return Xt().then(o=>new Promise((s,i)=>{const r=o.transaction(e,"readwrite");r.objectStore(e).put(a,n),r.oncomplete=()=>s(),r.onerror=()=>i(r.error)}))}function mt(e,n){return Xt().then(a=>new Promise((o,s)=>{const i=a.transaction(e,"readwrite");i.objectStore(e).delete(n),i.oncomplete=()=>o(),i.onerror=()=>s(i.error)}))}function Wn(e){return Xt().then(n=>new Promise((a,o)=>{const s=n.transaction(e,"readwrite");s.objectStore(e).clear(),s.oncomplete=()=>a(),s.onerror=()=>o(s.error)}))}async function Yn(e){if(!e)return!1;try{const n={mode:"read"};let a=await e.queryPermission(n);return a==="granted"?!0:(a=await e.requestPermission(n),a==="granted")}catch(n){return console.warn("[folder] permission check failed:",n),!1}}async function Ns(e){const n=new FormData;n.append("file",e,e.name),n.append("source","folder");const a=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:n});if(!a.ok){let o="http_"+a.status;try{const s=await a.json();o=s&&s.detail?typeof s.detail=="string"?s.detail:s.detail.code||JSON.stringify(s.detail):o}catch{}throw new Error(o)}return await a.json()}async function Os(e){try{const a=(await e.getFile()).size;return await new Promise(s=>setTimeout(s,3e3)),(await e.getFile()).size===a&&a>0}catch{return!1}}async function Ra(e,n,a,o){if(o>10)return;let s;try{s=await e.queryPermission({mode:"read"})}catch{s="denied"}if(s==="granted")for await(const i of e.values()){const r=n?`${n}/${i.name}`:i.name;if(i.kind==="file"){if(!Rs.test(i.name))continue;let c;try{c=await i.getFile()}catch{continue}const l=`${r}::${c.size}::${c.lastModified}`;if(await ht("seen",l))continue;a.push({entry:i,file:c,seenKey:l,relPath:r})}else if(i.kind==="directory")try{await Ra(i,r,a,o+1)}catch{}}}(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window;let a=null,o=null,s=60,i=!1,r=!1,c=0,l=0,p=0,f=[],d=null,u=!1;function m(D,j){const F=document.getElementById("folder-status-summary");F&&(F.setAttribute("data-i18n",D),F.textContent=t(D),F.className="auto-status-pill"+(j?" "+j:""))}function h(D){["folder-unsupported","folder-empty","folder-active"].forEach(j=>{const F=document.getElementById(j);F&&(F.style.display=j===D?"":"none")})}function _(D){if(!D)return"-";const j=D instanceof Date?D:new Date(D),F=String(j.getHours()).padStart(2,"0"),ee=String(j.getMinutes()).padStart(2,"0"),te=String(j.getSeconds()).padStart(2,"0");return`${F}:${ee}:${te}`}function y(){h("folder-active");const D=document.getElementById("folder-config-path");D&&a&&(D.textContent=a.name||"-");const j=document.getElementById("folder-interval-select");j&&(j.value=String(s)),document.getElementById("folder-stat-last").textContent=d?_(d):"-",document.getElementById("folder-stat-processed").textContent=String(c),document.getElementById("folder-stat-failed").textContent=String(l),document.getElementById("folder-stat-queue").textContent=String(p);const F=document.getElementById("btn-folder-pause"),ee=document.getElementById("btn-folder-resume");F&&(F.style.display=i?"none":""),ee&&(ee.style.display=i?"":"none"),i?m("folder-status-paused","paused"):m("folder-status-running","running");const te=document.getElementById("folder-status-text");te&&(te.setAttribute("data-i18n",i?"folder-status-paused":"folder-status-running"),te.textContent=t(i?"folder-status-paused":"folder-status-running"));const ie=document.getElementById("folder-status-pulse");ie&&(ie.className="folder-status-pulse"+(i?" paused":"")),b()}function b(){const D=document.getElementById("folder-recent-list");if(D){if(f.length===0){D.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}D.innerHTML=f.slice(0,20).map(j=>{let F;j.status==="ok"?F=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:j.status==="dup"?F=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:j.status==="skip"?F=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:F=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const ee=j.status==="fail"&&j.error?j.error:j.status==="dup"&&j.reason||j.status==="skip"&&j.reason?j.reason:"",te=ee?`<div class="folder-recent-err">${escapeHtml(ee)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${F}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(j.name)}</div>
                        ${te}
                    </div>
                    <div class="folder-recent-time">${_(j.time)}</div>
                </div>
            `}).join("")}}function v(D){f.unshift(D),f.length>50&&(f.length=50),Ne("config","recent_list",f).catch(()=>{})}async function L(){if(!(r||i||!a)){r=!0;try{if(await a.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),C(),showToast("warn",t("folder-permission-lost"));return}d=new Date;const j=[];await Ra(a,"",j,0),p=j.length,y();for(const F of j){if(i)break;if(!await Os(F.entry)){p=Math.max(0,p-1),y();continue}try{let te;try{te=await F.entry.getFile()}catch{te=F.file}const ie=await Ns(te);await Ne("seen",F.seenKey,{name:te.name,relPath:F.relPath,size:te.size,lastModified:te.lastModified,processed_at:Date.now()});const ne=ie.history_ids||(ie.history_id?[ie.history_id]:[]),fe=ie.duplicate_warnings||[],me=F.relPath||te.name;ne.length>0?(c+=ne.length,v({name:me,status:"ok",time:new Date,history_id:ne[0],count:ne.length}),await Ne("config","processed_count",c)):fe.length>0?v({name:me,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):v({name:me,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(te){l++,v({name:F.relPath||F.file.name,status:"fail",time:new Date,error:String(te.message||te)}),await Ne("config","failed_count",l)}p=Math.max(0,p-1),y()}}catch(D){console.warn("[folder] scan error:",D)}finally{r=!1,y()}}}function g(){o&&clearInterval(o),o=setInterval(L,s*1e3)}function x(){o&&(clearInterval(o),o=null)}function B(D){if(!a||i)return;const j=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return D.preventDefault(),D.returnValue=j,j}function E(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",B))}function w(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",B))}function I(){i=!1,g(),E(),y(),L()}function M(){i=!0,x(),w(),y()}function S(){i=!1,g(),E(),y(),L()}function C(){i=!0,x(),w()}async function k(){try{const D=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await Yn(D)){showToast("warn",t("folder-permission-denied"));return}a=D,await Ne("handles","main",D),c=0,l=0,p=0,f=[],await Ne("config","processed_count",0),await Ne("config","failed_count",0),await Wn("seen"),I()}catch(D){D&&D.name!=="AbortError"&&console.warn("[folder] pick failed:",D)}}async function T(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(C(),a=null,c=0,l=0,p=0,f=[],await mt("handles","main"),await mt("config","processed_count"),await mt("config","failed_count"),await Wn("seen"),h("folder-empty"),m("folder-status-empty",""))}async function $(){f=[];try{await mt("config","recent_list")}catch{}b()}async function A(){if(u)return;if(u=!0,!n){h("folder-unsupported"),m("folder-status-unsupported",""),R();return}H();let D=null;try{D=await ht("handles","main")}catch{}if(!D){h("folder-empty"),m("folder-status-empty","");return}if(!await Yn(D)){h("folder-empty"),m("folder-status-empty",""),await mt("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}a=D;try{c=await ht("config","processed_count")||0}catch{}try{l=await ht("config","failed_count")||0}catch{}try{const F=await ht("config","recent_list");Array.isArray(F)&&(f=F.map(ee=>({...ee,time:ee.time?new Date(ee.time):new Date})))}catch{}I()}function H(){const D=document.getElementById("btn-folder-pick"),j=document.getElementById("btn-folder-pause"),F=document.getElementById("btn-folder-resume"),ee=document.getElementById("btn-folder-scan-now"),te=document.getElementById("btn-folder-remove"),ie=document.getElementById("btn-folder-clear-recent"),ne=document.getElementById("folder-interval-select");D&&D.addEventListener("click",k),j&&j.addEventListener("click",M),F&&F.addEventListener("click",S),ee&&ee.addEventListener("click",()=>{L()}),te&&te.addEventListener("click",T),ie&&ie.addEventListener("click",$),ne&&ne.addEventListener("change",fe=>{s=parseInt(fe.target.value,10)||60,i||g()}),P()}function P(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(D=>{D.dataset.tabJumpBound||(D.dataset.tabJumpBound="1",D.addEventListener("click",j=>{const F=j.currentTarget.dataset.tabJump;if(F==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(F==="upload"){const ee=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');ee&&ee.click()}}))})}function R(){P()}window._loadFolderWatcherPanel=A})();function Vs(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(n=>/chromium|google chrome|microsoft edge/i.test(n.brand||""))}catch{}const e=navigator.userAgent||"";return!!(/Edg\//.test(e)||/Chrome\//.test(e)&&!/OPR\/|YaBrowser|Opera/.test(e))}function un(){try{if(Vs()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const e=document.getElementById("chrome-only-banner");if(!e)return;const n=e.querySelector('[data-i18n="chrome-banner-msg"]'),a=e.querySelector('[data-i18n="chrome-banner-dismiss"]');n&&typeof t=="function"&&(n.textContent=t("chrome-banner-msg")),a&&typeof t=="function"&&(a.textContent=t("chrome-banner-dismiss")),e.style.display="";const o=document.getElementById("chrome-only-banner-close");o&&!o.dataset.bound&&(o.dataset.bound="1",o.addEventListener("click",()=>{e.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",un):setTimeout(un,0));window._refreshChromeBanner=un;const Us=`
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
    `;be("email-modal",Us);(function(){let e=null,n=null,a="new",o=!1,s=!1;async function i(){const k=document.getElementById("email-empty"),T=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!k||!T))try{const $=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if($.status===401){localStorage.removeItem("mrpilot_token");const H=await $.json().catch(()=>({}));if((typeof H.detail=="string"?H.detail:H.detail&&H.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!$.ok){c("none");return}const A=await $.json();e=A.account||null,n=A.presets||{},o=!0,r(),e&&I()}catch($){console.error("[email-ingest] load failed",$),c("none")}}function r(){const k=document.getElementById("email-empty"),T=document.getElementById("email-account-card"),$=document.getElementById("email-logs-section");if(!e){k.style.display="",T.style.display="none",$&&($.style.display="none"),c("none");return}k.style.display="none",T.style.display="",$&&($.style.display="");const A=document.getElementById("email-account-addr"),H=document.getElementById("email-account-host"),P=document.getElementById("email-account-last"),R=document.getElementById("email-last-error"),D=document.getElementById("email-enabled-toggle");if(A&&(A.textContent=e.email_address||"-"),H&&(H.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),P){const j=e.last_fetched_at;if(!j)P.textContent=t("email-last-never");else{const F=l(j),ee=!e.last_error;P.textContent=ee?t("email-last-ok",{time:F}):t("email-last-fail",{time:F})}}R&&(e.last_error?(R.style.display="",R.textContent=p(e.last_error)):R.style.display="none"),D&&(D.checked=!!e.enabled),e.enabled?e.last_error?c("error"):c("on"):c("off")}function c(k){const T=document.getElementById("email-status-summary");if(!T)return;T.classList.remove("none","ready","active","coming");let $="auto-status-loading";k==="none"?($="email-status-none",T.classList.add("none")):k==="on"?($="email-status-on",T.classList.add("active")):k==="off"?($="email-status-off",T.classList.add("coming")):k==="error"&&($="email-status-error",T.classList.add("none")),T.setAttribute("data-i18n",$),T.textContent=t($)}function l(k){if(!k)return"";const T=new Date(k);if(isNaN(T.getTime()))return"";const $=A=>String(A).padStart(2,"0");return`${$(T.getMonth()+1)}-${$(T.getDate())} ${$(T.getHours())}:${$(T.getMinutes())}`}function p(k){if(!k)return"";const T=String(k);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(T)?t("email-test-auth-fail"):/timeout|timed out/i.test(T)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(T),T)}function f(k){a=k;const T=document.getElementById("email-modal");if(!T)return;const $=document.getElementById("email-preset");$.innerHTML="";const A=n||{},H=["gmail","outlook","yahoo","icloud","qq","163","custom"],P={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};H.forEach(N=>{if(!A[N])return;const K=document.createElement("option");K.value=N,K.textContent=N==="custom"?t("email-preset-custom"):P[N]||N,$.appendChild(K)});const R=document.getElementById("email-modal-title"),D=document.getElementById("email-address"),j=document.getElementById("email-password"),F=document.getElementById("email-imap-host"),ee=document.getElementById("email-imap-port"),te=document.getElementById("email-imap-ssl"),ie=document.getElementById("email-folder"),ne=document.getElementById("email-mark-read"),fe=document.getElementById("email-bind-enabled"),me=document.getElementById("email-test-result"),q=document.getElementById("email-adv-details");if(me&&(me.style.display="none",me.textContent=""),k==="edit"&&e){R.setAttribute("data-i18n","email-modal-title-edit"),R.textContent=t("email-modal-title-edit"),D.value=e.email_address||"",j.value="",j.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),j.placeholder=t("email-field-password-edit-ph"),F.value=e.imap_host||"",ee.value=e.imap_port||993,te.checked=e.imap_use_ssl!==!1,ie.value=e.folder||"INBOX",ne.checked=e.mark_as_read!==!1,fe.checked=e.enabled!==!1;const N=document.getElementById("email-filter-sender"),K=document.getElementById("email-filter-subject");N&&(N.value=e.filter_sender||""),K&&(K.value=e.filter_subject||""),v(e.interval_min||15),$.value=_(e.imap_host)||"custom",q&&(q.open=!0)}else{R.setAttribute("data-i18n","email-modal-title-new"),R.textContent=t("email-modal-title-new"),D.value="",j.value="",j.setAttribute("data-i18n-placeholder","email-field-password-ph"),j.placeholder=t("email-field-password-ph"),$.value="gmail",u("gmail"),ie.value="INBOX",ne.checked=!0,fe.checked=!0;const N=document.getElementById("email-filter-sender"),K=document.getElementById("email-filter-subject");N&&(N.value=""),K&&(K.value=""),v(15),q&&(q.open=!1)}b(),T.style.display="flex",setTimeout(()=>D.focus(),60)}function d(){const k=document.getElementById("email-modal");k&&(k.style.display="none")}function u(k){const T=(n||{})[k];if(!T||k==="custom")return;const $=document.getElementById("email-imap-host"),A=document.getElementById("email-imap-port"),H=document.getElementById("email-imap-ssl");$&&($.value=T.host||""),A&&(A.value=T.port||993),H&&(H.checked=T.ssl!==!1)}const m={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function h(k){if(!k||!k.includes("@"))return;const T=k.split("@")[1].toLowerCase().trim(),$=m[T];if(!$)return;const A=document.getElementById("email-preset");if(!A)return;const H=A.value;H&&H!=="custom"&&H!==""&&H===$||(A.value=$,u($))}function _(k){if(!k)return null;const T=n||{};for(const $ in T)if($!=="custom"&&T[$]&&T[$].host===k)return $;return null}function y(){const k=document.querySelector("#email-interval-options .email-interval-btn.active"),T=k?parseInt(k.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(T)?T:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function b(){const k=document.getElementById("email-interval-options");!k||k._bound||(k._bound=!0,k.addEventListener("click",T=>{const $=T.target.closest(".email-interval-btn");$&&(k.querySelectorAll(".email-interval-btn").forEach(A=>A.classList.remove("active")),$.classList.add("active"))}))}function v(k){const T=[5,15,60].includes(k)?k:15,$=document.getElementById("email-interval-options");$&&$.querySelectorAll(".email-interval-btn").forEach(A=>{A.classList.toggle("active",parseInt(A.dataset.interval,10)===T)})}function L(k,T){const $=document.getElementById("email-test-result");$&&($.style.display="",$.textContent=T,$.className="form-test-result "+(k==="ok"?"ok":k==="running"?"running":"fail"))}async function g(){const k=y();if(!k.email_address){L("fail",t("email-addr-required"));return}if(!k.password){L("fail",t("email-password-required"));return}if(!k.imap_host){L("fail",t("email-host-required"));return}const T=document.getElementById("btn-email-modal-test");T&&(T.disabled=!0),L("running",t("email-test-running"));try{const $=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:k.email_address,password:k.password,imap_host:k.imap_host,imap_port:k.imap_port,imap_use_ssl:k.imap_use_ssl,folder:k.folder})}),A=await $.json().catch(()=>({}));if($.ok&&A.success)L("ok",t("email-test-ok",{folder:k.folder,n:A.folder_count??"?"}));else{const H=A.error_msg||"";H==="auth_failed"||/auth/i.test(H)?L("fail",t("email-test-auth-fail")):L("fail",t("email-test-fail",{msg:H||$.status}))}}catch($){L("fail",t("email-test-fail",{msg:String($).slice(0,120)}))}finally{T&&(T.disabled=!1)}}async function x(){const k=y();if(!k.email_address){L("fail",t("email-addr-required"));return}if(a==="new"&&!k.password){L("fail",t("email-password-required"));return}if(!k.imap_host){L("fail",t("email-host-required"));return}const T=document.getElementById("btn-email-modal-save");T&&(T.disabled=!0);const $={...k};a==="edit"&&!$.password&&delete $.password;try{const A=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify($)}),H=await A.json().catch(()=>({}));if(A.ok&&H.ok)e=H.account,showToast(t("email-save-ok"),"success"),d(),r(),I();else{const R="email."+(H.detail||"").split(".").slice(-1)[0];L("fail",t(R)!==R?t(R):t("email-save-fail"))}}catch{L("fail",t("email-save-fail"))}finally{T&&(T.disabled=!1)}}async function B(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),r();const $=document.getElementById("email-logs-list");$&&($.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function E(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const k=document.getElementById("btn-email-trigger"),T=k?k.innerHTML:"";k&&(k.disabled=!0,k.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const $=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),A=await $.json().catch(()=>({}));if($.ok){const H=A.emails_scanned||0,P=A.ocr_succeeded||0,R=A.ocr_failed||0;H===0&&P===0&&R===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:H,ok:P,fail:R}),R>0?"warn":"success")}else{const P="email."+(A.detail||"").split(".").slice(-1)[0];showToast(t(P)!==P?t(P):t("email-trigger-fail"),"error")}await i()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,k&&(k.disabled=!1,k.innerHTML=T)}}async function w(){if(!e)return;const k=document.getElementById("email-enabled-toggle"),T=!!(k&&k.checked),$=e.enabled;try{const A=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:T})}),H=await A.json().catch(()=>({}));A.ok&&H.ok?(e=H.account,r()):(k&&(k.checked=$),showToast(t("email-toggle-fail"),"error"))}catch{k&&(k.checked=$),showToast(t("email-toggle-fail"),"error")}}async function I(){const k=document.getElementById("email-logs-list");if(k){k.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const T=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!T.ok){k.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const $=await T.json();if(!Array.isArray($)||$.length===0){k.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}k.innerHTML=$.map(M).join("")}catch{k.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function M(k){const T=l(k.created_at),$=k.status||"failed",A=$==="success"?"ok":$==="partial"?"partial":"fail",H=$==="success"?"✓":$==="partial"?"◐":"✗",P=k.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,R=t("email-log-counts",{scanned:k.emails_scanned||0,att:k.attachments_found||0,ok:k.ocr_succeeded||0,fail:k.ocr_failed||0}),D=(k.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${A}">
                <span class="log-time">${escapeHtml(T)}</span>
                <span class="log-status">${H}</span>
                ${P}
                <span class="log-counts">${escapeHtml(R)}</span>
                <span class="log-elapsed">${escapeHtml(D)}</span>
            </div>
        `}function S(){const k=document.getElementById("btn-email-bind");k&&k.addEventListener("click",()=>f("new"));const T=document.getElementById("btn-email-edit");T&&T.addEventListener("click",()=>f("edit"));const $=document.getElementById("btn-email-unbind");$&&$.addEventListener("click",B);const A=document.getElementById("btn-email-trigger");A&&A.addEventListener("click",E);const H=document.getElementById("email-enabled-toggle");H&&H.addEventListener("change",w);const P=document.getElementById("email-modal-close");P&&P.addEventListener("click",d);const R=document.getElementById("btn-email-modal-cancel");R&&R.addEventListener("click",d);const D=document.getElementById("btn-email-modal-test");D&&D.addEventListener("click",g);const j=document.getElementById("btn-email-modal-save");j&&j.addEventListener("click",x);const F=document.getElementById("email-preset");F&&F.addEventListener("change",ie=>u(ie.target.value));const ee=document.getElementById("email-address");ee&&!ee.dataset.autoBound&&(ee.dataset.autoBound="1",ee.addEventListener("blur",ie=>h((ie.target.value||"").trim())),ee.addEventListener("input",ie=>{const ne=(ie.target.value||"").trim();ne.includes("@")&&ne.split("@")[1].includes(".")&&h(ne)}));const te=document.getElementById("btn-email-refresh-logs");te&&te.addEventListener("click",()=>{te.classList.add("spinning"),setTimeout(()=>te.classList.remove("spinning"),600),I()})}S(),window._loadEmailIngestPanel=i,window._rerenderEmailIngest=function(){if(!o)return;r();const k=document.getElementById("email-logs-section");e&&k&&k.open&&I()};let C=null;window._startEmailLogAutoRefresh=function(){C||(C=setInterval(()=>{e&&o&&I()},3e4))},window._stopEmailLogAutoRefresh=function(){C&&(clearInterval(C),C=null)}})();const Gs=`
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
`;be("bank-cand-drawer",Gs);const Ks=`
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
`;be("bank-client-picker-modal",Ks);const z={sessions:[],currentSession:null,currentTxs:[],currentFilter:"all",currentTxForDrawer:null,loaded:!1,queue:[],qSeq:0,sessionFilter:"all",pickerSelected:null};function Js(e){const n=Number(e||0);let a="score-low";return n>=85?a="score-high":n>=60&&(a="score-mid"),'<span class="bank-cand-score '+a+'">'+n.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Ws(e){const n=document.getElementById("bank-upload-progress");n&&(n.style.display="none")}function Ys(){const e=document.getElementById("bank-upload-error");e&&(e.style.display="none")}function Xs(e){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[e]||t("bank-err-unknown")+" ("+e+")"}function Ge(e){if(e==null)return"-";const n=Number(e);return isNaN(n)?"-":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function it(e){if(!e)return"-";const n=String(e);return n.length>=10?n.slice(0,10):n}function Fa(e,n){return!e&&!n?"":(it(e)||"?")+" ~ "+(it(n)||"?")}function se(e){return e==null?"":String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}async function Zs(e){z.currentTxForDrawer=e;const n=document.getElementById("bank-detail-body");n&&n.classList.add("has-pane");const a=document.getElementById("bank-cand-pane-title"),o=document.getElementById("bank-cand-pane-sub"),s=document.getElementById("bank-cand-pane-foot");if(a&&(a.textContent=t("bank-cand-pane-current")),o){const r=e.direction==="OUT"?"-":"+",c=e.direction==="OUT"?"bank-out":"bank-in";o.innerHTML=`${se(it(e.tx_date))}
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <span>${se(e.description||"-")}</span>
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <strong class="${c}">${r}${Ge(e.amount)}</strong>`}s&&(s.style.display="");const i=document.getElementById("bank-cand-pane-body");if(i){i.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const r=await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!r.ok)throw new Error("cands:"+r.status);const c=await r.json();ei(e,c.candidates||[])}catch{i.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function Qs(e,n,a){const o=n.history_id,s=n.invoice_no||"-",i=n.vendor||"-",r=n.amount_total!==null&&n.amount_total!==void 0?Ge(n.amount_total):"-",c=n.invoice_date?it(n.invoice_date):"-",l=n.filename||"",p=!!a&&e.matched_history_id===o,f="bank-cand-card"+(n.is_auto_picked?" is-auto":"")+(p?" is-picked":"");let d="";return p?d='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":d='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+se(o)+'"><span>'+t(n.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+f+'" data-hid="'+se(o)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+se(i)+"</div>"+Js(n.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+se(s)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+r+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+se(c)+"</span></div>"+(l?'<div class="bank-cand-card-file" title="'+se(l)+'">'+se(l)+"</div>":"")+(n.reason?'<div class="bank-cand-card-reason">'+se(n.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+d+"</div></div>"}function ei(e,n){const a=document.getElementById("bank-cand-pane-body");if(!a)return;const o=n||[];let s="";if(e.match_status==="matched")s='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",o.length)+"</div>";else if(e.match_status==="suggested")s='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",o.length)+"</div>";else if(o.length>0)s='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",o.length)+"</div>";else{a.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const i=e.match_status==="matched",r=o.map(c=>Qs(e,c,i)).join("");a.innerHTML=s+'<div class="bank-cand-list">'+r+"</div>",a.querySelectorAll('[data-act="pick"]').forEach(c=>{c.addEventListener("click",()=>{ai(c.dataset.hid)})}),a.querySelectorAll('[data-act="unmatch"]').forEach(c=>{c.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),Ct(),await ct(z.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function Ct(){const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane");const n=document.getElementById("bank-cand-pane-title"),a=document.getElementById("bank-cand-pane-sub"),o=document.getElementById("bank-cand-pane-body"),s=document.getElementById("bank-cand-pane-foot");n&&(n.textContent=t("bank-cand-pane-empty-title")),a&&(a.textContent=t("bank-cand-pane-empty-sub")),s&&(s.style.display="none"),o&&(o.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const i=document.getElementById("bank-tx-tbody");i&&i.querySelectorAll("tr.is-selected").forEach(r=>r.classList.remove("is-selected")),z.currentTxForDrawer=null}async function ct(e){try{const n="/api/bank-recon/sessions/"+encodeURIComponent(e)+(z.currentFilter!=="all"?"?filter="+z.currentFilter:""),a=await fetch(n,{headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("detail:"+a.status);const o=await a.json();z.currentSession=o.session,z.currentTxs=o.transactions||[],ci()}catch(n){console.warn("[bank-recon] loadSessionDetail failed",n),showToast(t("bank-load-failed"),"error")}}async function ti(){if(!z.currentSession)return;const e=document.getElementById("btn-bank-run-match"),n=e.innerHTML;e.disabled=!0,e.innerHTML="<span>"+t("bank-matching")+"</span>";try{const a=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(z.currentSession.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("match:"+a.status);const o=await a.json();showToast(t("bank-match-done").replace("{matched}",o.matched).replace("{suggested}",o.suggested).replace("{unmatched}",o.unmatched),"success"),await ct(z.currentSession.id),await dt()}catch(a){console.warn("[bank-recon] match failed",a),showToast(t("bank-match-failed"),"error")}finally{e.disabled=!1,e.innerHTML=n}}async function ni(){if(!(!z.currentSession||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const n=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(z.currentSession.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!n.ok)throw new Error("delete:"+n.status);showToast(t("bank-deleted"),"success"),z.currentSession=null,z.currentTxs=[],Cn(),await dt()}catch(n){console.warn("[bank-recon] delete failed",n),showToast(t("bank-delete-failed"),"error")}}async function Xn(){if(z.currentTxForDrawer)try{const e=await fetch("/api/bank-recon/tx/"+encodeURIComponent(z.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!e.ok)throw new Error("ignore:"+e.status);Ct(),await ct(z.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}async function ai(e){if(z.currentTxForDrawer)try{const n=await fetch("/api/bank-recon/tx/"+encodeURIComponent(z.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:e})});if(!n.ok)throw new Error("pick:"+n.status);showToast(t("bank-matched-ok"),"success"),Ct(),await ct(z.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}function za(){if(!z.currentSession)return;const e=z.currentSession;document.getElementById("bank-detail-title").textContent=(e.bank_code||"-")+(e.account_last4?" ···"+e.account_last4:"")+" · "+(e.source_filename||""),document.getElementById("bank-meta-period").textContent=Fa(e.period_start,e.period_end)||"-",document.getElementById("bank-meta-opening").textContent=Ge(e.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+Ge(e.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+Ge(e.total_outflow),document.getElementById("bank-meta-closing").textContent=Ge(e.closing_balance);const n=z.currentTxs||[],a=n.length;let o=0,s=0,i=0;for(const r of n){const c=r.match_status||"unmatched";c==="matched"?o++:c==="suggested"?s++:i++}document.getElementById("bank-stat-total").textContent=a,document.getElementById("bank-stat-matched").textContent=o,document.getElementById("bank-stat-suggested").textContent=s,document.getElementById("bank-stat-unmatched").textContent=i}function In(){const e=document.getElementById("bank-tx-tbody");if(!e)return;let n=z.currentTxs||[];if(z.currentFilter!=="all"&&(n=n.filter(a=>z.currentFilter==="matched"?a.match_status==="matched":z.currentFilter==="suggested"?a.match_status==="suggested":z.currentFilter==="unmatched"?a.match_status==="unmatched"||a.match_status==="ignored":!0)),n.length===0){e.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(e.innerHTML=n.map(a=>oi(a)).join(""),e.querySelectorAll("tr[data-tx-id]").forEach(a=>{a.addEventListener("click",()=>{const o=a.dataset.txId,s=z.currentTxs.find(i=>i.id===o);s&&(e.querySelectorAll("tr.is-selected").forEach(i=>i.classList.remove("is-selected")),a.classList.add("is-selected"),Zs(s))})}),z.currentTxForDrawer){const a=e.querySelector('tr[data-tx-id="'+z.currentTxForDrawer.id+'"]');a&&a.classList.add("is-selected")}}function oi(e){const n=e.direction==="OUT",a=n?"-":"+",o=n?"bank-out":"bank-in",s=e.match_status||"unmatched",i=t("bank-match-"+s)||s,r=it(e.tx_date),c=e.channel?`<span class="bank-tx-channel">${se(e.channel)}</span>`:"";return`
        <tr data-tx-id="${se(e.id)}">
            <td class="bank-tx-date">${se(r)}</td>
            <td class="bank-tx-desc">${c}${se(e.description||"-")}</td>
            <td class="bank-td-amount ${o}">${a}${Ge(e.amount)}</td>
            <td><span class="bank-tx-match mt-${s}">${se(i)}</span></td>
        </tr>
    `}function Ln(){const e=document.getElementById("bank-client-badge");if(!e||!z.currentSession)return;const n=z.currentSession.client_id,a=document.getElementById("bank-client-badge-dot"),o=document.getElementById("bank-client-badge-name"),s=document.getElementById("bank-client-badge-caret"),i=typeof _userInfo<"u"?_userInfo:null,r=!(i&&i.role==="member");if(n!=null){const c=(window._clientsCache||[]).find(l=>Number(l.id)===Number(n));e.classList.remove("is-empty"),a&&(a.style.background=c&&c.color||"#111111"),o&&(o.textContent=c&&(c.short_name||c.name)||"#"+n)}else e.classList.add("is-empty"),a&&(a.style.background=""),o&&(o.textContent=t("bank-client-none"));r?(e.classList.remove("is-readonly"),e.disabled=!1,s&&(s.style.display="")):(e.classList.add("is-readonly"),e.disabled=!0,s&&(s.style.display="none")),e.style.display=""}function si(){if(!z.currentSession)return;const e=typeof _userInfo<"u"?_userInfo:null;if(!!(e&&e.role==="member"))return;z.pickerSelected=z.currentSession.client_id!=null?Number(z.currentSession.client_id):null,Oa();const a=document.getElementById("bank-client-picker-modal");a&&(a.style.display="")}function Na(){const e=document.getElementById("bank-client-picker-modal");e&&(e.style.display="none"),z.pickerSelected=null}function Oa(){const e=document.getElementById("bank-client-picker-list");if(!e)return;const n=(window._clientsCache||[]).filter(o=>o&&(o.is_active===!0||o.is_active===void 0)),a=[];a.push('<div class="bank-client-picker-row is-none'+(z.pickerSelected==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+se(t("bank-client-picker-none"))+"</span></div>"),n.forEach(o=>{const s=Number(o.id)===Number(z.pickerSelected)?" is-selected":"";a.push('<div class="bank-client-picker-row'+s+'" data-cid="'+se(o.id)+'"><span class="bank-cp-dot" style="background:'+se(o.color||"#111111")+'"></span><span>'+se(o.short_name||o.name||"#"+o.id)+"</span></div>")}),e.innerHTML=a.join(""),e.querySelectorAll(".bank-client-picker-row").forEach(o=>{o.addEventListener("click",()=>{const s=o.dataset.cid;z.pickerSelected=s?Number(s):null,Oa()})})}async function ii(){if(z.currentSession)try{const e=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(z.currentSession.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:z.pickerSelected})});if(!e.ok)throw new Error("client:"+e.status);z.currentSession.client_id=z.pickerSelected,Ln(),showToast(t("bank-client-changed"),"success"),Na();try{await dt()}catch{}}catch(e){console.warn("[bank-recon] save client failed",e),showToast(t("bank-client-change-failed"),"error")}}async function dt(){try{const e=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!e.ok)throw new Error("sessions:"+e.status);z.sessions=await e.json(),Ft()}catch(e){console.warn("[bank-recon] loadSessions failed",e),z.sessions=[],Ft()}}function Zn(){const e=document.getElementById("bank-status-summary");if(!e)return;if(z.sessions.length===0){e.textContent=t("bank-pill-none");return}let a=0;for(const o of z.sessions)o.parse_status==="parsed"&&(o.unmatched_count||0)>0&&a++;e.textContent=a>0?t("bank-pill-pending").replace("{n}",a):t("bank-pill-ok")}function Ft(){const e=document.getElementById("bank-sessions-list");if(!e)return;let n=z.sessions||[];if(z.sessionFilter==="parsed"?n=n.filter(a=>a.parse_status==="parsed"):z.sessionFilter==="failed"&&(n=n.filter(a=>a.parse_status==="parse_failed")),!z.sessions||z.sessions.length===0){e.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(n.length===0){e.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}e.innerHTML=n.map(a=>ri(a)).join(""),e.querySelectorAll(".bank-session-row").forEach(a=>{a.addEventListener("click",o=>{o.target.closest(".bank-session-trash")||ct(a.dataset.sessionId)})}),e.querySelectorAll(".bank-session-trash").forEach(a=>{a.addEventListener("click",o=>{o.stopPropagation();const s=a.dataset.sessionId,i=a.dataset.sessionName||"";Va(s,i)})})}async function Va(e,n){if(!e)return;const a=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",n||"");if(await showConfirm(a,{danger:!0}))try{const s=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(e),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!s.ok)throw new Error("delete:"+s.status);showToast(t("bank-deleted"),"success"),z.currentSession&&z.currentSession.id===e&&(z.currentSession=null,z.currentTxs=[],Cn()),await dt(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(s){console.warn("[bank-recon] delete failed",s),showToast(t("bank-delete-failed"),"error")}}function ri(e){const n=(e.bank_code||"OTHER").toUpperCase(),a=Fa(e.period_start,e.period_end),o=e.account_last4?"···"+e.account_last4:"",s=li(e),i=it(e.created_at);return`
        <div class="bank-session-row" data-session-id="${se(e.id)}">
            <div class="bank-session-bank bk-${se(n)}">${se(n)}</div>
            <div class="bank-session-info">
                <div class="bank-session-title">${se(e.source_filename||a||"-")}</div>
                <div class="bank-session-meta">${se(a)} · ${se(o)} · ${se(i)}</div>
            </div>
            <div class="bank-session-counts">${s}</div>
            <button class="bank-session-trash" data-session-id="${se(e.id)}" data-session-name="${se(e.source_filename||"")}" title="${se(t("bank-session-delete-tip")||"删除")}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                </svg>
            </button>
            <div class="bank-session-arrow">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
            </div>
        </div>
    `}function li(e){if(e.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(e.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const n=e.tx_count||0,a=e.matched_count||0,o=e.unmatched_count||0,s=[`<span class="bank-session-count">${n} ${t("bank-count-tx")}</span>`];return a>0&&s.push(`<span class="bank-session-count cnt-matched">${a} ${t("bank-count-matched")}</span>`),o>0&&s.push(`<span class="bank-session-count cnt-unmatched">${o} ${t("bank-count-unmatched")}</span>`),s.join("")}function ci(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",za(),In(),Ln()}function Cn(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane"),z.currentTxForDrawer=null}const di=3;function pi(){return z.qSeq+=1,"q"+z.qSeq+"_"+Date.now()}async function ui(e){const n=Array.from(e.target.files||[]);if(e.target.value="",n.length!==0){for(const a of n){const o={id:pi(),file:a,name:a.name,size:a.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};a.name.toLowerCase().endsWith(".pdf")?a.size>20*1024*1024&&(o.status="failed",o.error_code="bank_recon.file_too_large"):(o.status="failed",o.error_code="bank_recon.only_pdf"),z.queue.push(o)}fi(),xe(),Sn()}}function fi(){const e=document.getElementById("bank-upload-queue");e&&(e.style.display=""),Ws(),Ys()}function xe(){const e=document.getElementById("bank-upload-queue-list"),n=document.getElementById("bank-upload-queue-summary");if(!e)return;if(z.queue.length===0){e.innerHTML="",n&&(n.textContent="");const r=document.getElementById("bank-upload-queue");r&&(r.style.display="none");return}let a=0,o=0,s=0,i=0;for(const r of z.queue)r.status==="ok"?a++:r.status==="failed"?o++:r.status==="uploading"||r.status==="parsing"?s++:i++;n&&(n.textContent=t("bank-queue-summary").replace("{ok}",a).replace("{run}",s).replace("{wait}",i).replace("{fail}",o)),e.innerHTML=z.queue.map(mi).join(""),e.querySelectorAll("[data-q-act]").forEach(r=>{const c=r.dataset.qAct,l=r.dataset.qId;r.addEventListener("click",()=>{c==="retry"&&vi(l),c==="remove"&&hi(l)})})}function mi(e){const n=(e.size/1024).toFixed(0)+" KB";let a="",o="";if(e.status==="pending")a='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",o='<button data-q-act="remove" data-q-id="'+se(e.id)+'" class="bq-act">×</button>';else if(e.status==="uploading")a='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(e.progress||0)+'%"></div></div>';else if(e.status==="parsing")a='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(e.status==="ok")a='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",e.tx_count||0)+"</span>",o='<button data-q-act="remove" data-q-id="'+se(e.id)+'" class="bq-act">×</button>';else if(e.status==="failed"){const s=Xs(e.error_code||"unknown");a='<span class="bq-stat bq-fail" title="'+se(s)+'">'+se(s)+"</span>",o='<button data-q-act="retry" data-q-id="'+se(e.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+se(e.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+se(e.id)+'"><div class="bq-name" title="'+se(e.name)+'">'+se(e.name)+'</div><div class="bq-size">'+n+'</div><div class="bq-status">'+a+'</div><div class="bq-actions">'+o+"</div></div>"}function vi(e){const n=z.queue.find(a=>a.id===e);n&&(n.status="pending",n.error_code=null,n.progress=0,xe(),Sn())}function hi(e){const n=z.queue.findIndex(o=>o.id===e);if(n<0)return;const a=z.queue[n];a.status==="uploading"||a.status==="parsing"||(z.queue.splice(n,1),xe())}function gi(){z.queue=z.queue.filter(e=>e.status!=="ok"),xe()}async function Sn(){for(;;){if(z.queue.filter(a=>a.status==="uploading"||a.status==="parsing").length>=di)return;const n=z.queue.find(a=>a.status==="pending");if(!n){z.queue.every(a=>a.status==="ok"||a.status==="failed")&&(await dt(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}bi(n).then(()=>Sn())}}async function bi(e){e.status="uploading",e.progress=0,xe();try{const n=new FormData;n.append("file",e.file,e.name);const a=await new Promise((s,i)=>{const r=new XMLHttpRequest;r.open("POST","/api/bank-recon/upload"),r.setRequestHeader("Authorization","Bearer "+token),r.upload.onprogress=c=>{c.lengthComputable&&(e.progress=Math.min(99,Math.round(c.loaded/c.total*100)),xe())},r.upload.onload=()=>{e.status="parsing",xe()},r.onload=()=>{r.status>=200&&r.status<300?s({status:r.status,text:r.responseText}):s({status:r.status,text:r.responseText})},r.onerror=()=>i(new Error("network")),r.send(n)});let o={};try{o=JSON.parse(a.text||"{}")}catch{o={}}if(a.status>=400){e.status="failed",e.error_code=o&&o.detail||"unknown",xe();return}if(o.parse_status==="parse_failed"){e.status="failed",e.error_code=o.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",xe();return}e.status="ok",e.tx_count=o.tx_count||0,e.session_id=o.session_id||null,xe()}catch(n){console.warn("[bank-recon] upload failed",n),e.status="failed",e.error_code="network",xe()}}async function Ua(){if(z.loaded){Zn();return}z.loaded=!0,yi(),await dt(),Zn()}function yi(){const e=document.getElementById("bank-file-input");e&&!e._bound&&(e._bound=!0,e.addEventListener("change",ui));const n=document.getElementById("btn-bank-queue-clear-done");n&&!n._bound&&(n._bound=!0,n.addEventListener("click",gi));const a=document.getElementById("btn-bank-back");a&&!a._bound&&(a._bound=!0,a.addEventListener("click",()=>{z.currentSession=null,z.currentTxs=[],Cn()}));const o=document.getElementById("btn-bank-delete");o&&!o._bound&&(o._bound=!0,o.addEventListener("click",ni));const s=document.getElementById("btn-bank-run-match");s&&!s._bound&&(s._bound=!0,s.addEventListener("click",ti)),document.querySelectorAll(".bank-filter-btn").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",()=>{z.currentFilter=f.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(d=>{d.classList.toggle("active",d===f)}),In()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",Ct))});const i=document.getElementById("btn-bank-cand-pane-close");i&&!i._bound&&(i._bound=!0,i.addEventListener("click",Ct));const r=document.getElementById("btn-bank-cand-ignore");r&&!r._bound&&(r._bound=!0,r.addEventListener("click",Xn));const c=document.getElementById("btn-bank-cand-ignore-pane");c&&!c._bound&&(c._bound=!0,c.addEventListener("click",Xn));const l=document.getElementById("bank-client-badge");l&&!l._bound&&(l._bound=!0,l.addEventListener("click",si)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",Na))});const p=document.getElementById("btn-bank-client-picker-save");p&&!p._bound&&(p._bound=!0,p.addEventListener("click",ii)),document.querySelectorAll(".bank-sessions-chip").forEach(f=>{f._bound||(f._bound=!0,f.addEventListener("click",()=>{z.sessionFilter=f.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(d=>{d.classList.toggle("active",d===f)}),Ft()}))})}window._deleteBankSession=Va;window._loadBankReconPanel=Ua;window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(Ft(),z.currentSession&&(za(),In(),Ln(),!z.currentTxForDrawer)){const e=document.getElementById("bank-cand-pane-title"),n=document.getElementById("bank-cand-pane-sub");e&&(e.textContent=t("bank-cand-pane-empty-title")),n&&(n.textContent=t("bank-cand-pane-empty-sub"))}xe()}};typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon);window._openBankSession=async function(e){e&&(z.loaded||await Ua(),await ct(e))};(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const wi=`
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
    `,ki=`
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
    `;be("client-modal-mask",wi);be("wsclient-modal-mask",ki);const X={clients:[],editingClientId:null,historyClientFilter:"",custTab:"seller",sellerClients:[],editingWsClientId:null,catCache:{fetched:0,items:[],supplier_count:0}},ge={page:0,pageSize:12,keyword:""},Me=new Set,zt={keyword:""};function xi(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function Ie(e,n={}){const a=await fetch(e,{...n,headers:{"Content-Type":"application/json",...xi(),...n.headers||{}}});if(!a.ok){const o=await a.json().catch(()=>({}));throw new Error(o.detail||"HTTP "+a.status)}return a.json()}function _i(){const e=document.querySelector("#client-color-picker .color-swatch.active");return e?e.dataset.color:"#111111"}function Qn(e){const n=document.getElementById("drawer-cat-learned-tag");n&&e>0&&(n.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",e))}async function pt(){try{const e=await Ie("/api/clients");X.clients=e.clients||[],window._clientsCache=X.clients}catch(e){console.error("loadClientsCache fail",e),X.clients=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return X.clients}function Ei(){const e=ge.keyword.trim().toLowerCase();return e?X.clients.filter(n=>(n.name||"").toLowerCase().includes(e)||(n.short_name||"").toLowerCase().includes(e)||(n.tax_id||"").toLowerCase().includes(e)):X.clients}function Tn(){const e=Ei(),n=ge.pageSize,a=Math.max(0,Math.ceil(e.length/n)-1);ge.page>a&&(ge.page=a);const o=ge.page*n;return{all:e,items:e.slice(o,o+n),start:o,ps:n,total:e.length,maxPage:a}}function Te(){const e=document.getElementById("buyer-tbody");if(!e)return;const{items:n,start:a,ps:o,total:s,maxPage:i}=Tn();s?e.innerHTML=n.map(p=>{const f=Me.has(p.id);return`<div class="cust-row buyer-grid${f?" selected":""}" data-cid="${p.id}">
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
            </div>`}).join(""):e.innerHTML=`<div class="cust-empty">${escapeHtml(t(ge.keyword?"cust-no-match":"clients-empty"))}</div>`;const r=document.getElementById("buyer-pager-info");r&&(r.textContent=s?`${a+1}–${Math.min(a+o,s)} / ${s}`:"0");const c=document.getElementById("buyer-prev");c&&(c.disabled=ge.page<=0);const l=document.getElementById("buyer-next");l&&(l.disabled=ge.page>=i),Ga()}function Ga(){const e=Me.size,n=document.getElementById("buyer-batch-bar");n&&(n.style.display=e?"flex":"none");const a=document.getElementById("buyer-batch-count");a&&(a.textContent=t("cust-selected-n").replace("{n}",e));const o=document.getElementById("buyer-check-all");if(o){const{items:s}=Tn(),i=s.map(c=>c.id),r=i.filter(c=>Me.has(c)).length;o.checked=i.length>0&&r===i.length,o.indeterminate=r>0&&r<i.length}}function Bi(){Me.clear(),Te()}async function Ii(){const e=Array.from(Me);if(!(!e.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",e.length),{danger:!0})))try{await Ie("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:e})}),showToast(t("client-msg-deleted"),"success"),Me.clear(),await pt(),Te(),Zt(),Mn()}catch{showToast(t("client-msg-save-fail"),"fail")}}function kt(e){X.editingClientId=e?e.id:null;const n=!!e;document.getElementById("client-modal-title").textContent=t(n?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=e&&e.name||"",document.getElementById("client-input-short").value=e&&e.short_name||"",document.getElementById("client-input-tax").value=e&&e.tax_id||"",document.getElementById("client-input-address").value=e&&e.address||"",document.getElementById("client-input-contact").value=e&&e.contact_person||"",document.getElementById("client-input-phone").value=e&&e.contact_phone||"",document.getElementById("client-input-email").value=e&&e.contact_email||"",document.getElementById("client-input-notes").value=e&&e.notes||"";const a=e&&e.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(o=>{o.classList.toggle("active",o.dataset.color===a)}),document.getElementById("client-modal-delete").style.display=n?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function xt(){document.getElementById("client-modal-mask").style.display="none",X.editingClientId=null}async function Li(){const e=document.getElementById("client-input-name").value.trim();if(!e){showToast(t("client-msg-name-required"),"fail");return}const n={name:e,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:_i()};try{X.editingClientId?(await Ie(`/api/clients/${X.editingClientId}`,{method:"PATCH",body:JSON.stringify(n)}),showToast(t("client-msg-updated"),"success")):(await Ie("/api/clients",{method:"POST",body:JSON.stringify(n)}),showToast(t("client-msg-created"),"success")),xt(),await pt(),currentRoute==="clients"&&Te(),Zt(),Mn()}catch(a){console.error("saveClient fail",a);const o=a&&a.message?a.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+o,"fail")}}async function Ci(){if(!X.editingClientId)return;const e=X.clients.find(o=>o.id===X.editingClientId);if(!e)return;const n=t("client-delete-confirm").replace("{name}",e.name);if(await showConfirm(n,{danger:!0}))try{await Ie(`/api/clients/${X.editingClientId}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),xt(),await pt(),currentRoute==="clients"&&Te(),Zt(),Mn()}catch(o){console.error(o),showToast(t("client-msg-save-fail"),"fail")}}async function Si(e){const n=X.clients.find(a=>a.id===e);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(e,n?n.name:"");return}try{const a=localStorage.getItem("mrpilot_token"),o=await fetch(`/api/clients/${e}/export?month=all`,{headers:{Authorization:"Bearer "+a}});if(!o.ok){let l="HTTP "+o.status;try{const p=await o.json();p&&p.detail&&(l=p.detail)}catch{}throw new Error(l)}const s=await o.blob();if(s.size<200){showToast(t("client-export-month-empty"),"info");return}const i=n&&n.name?n.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",r=URL.createObjectURL(s),c=document.createElement("a");c.href=r,c.download=`${i}_export.csv`,c.click(),URL.revokeObjectURL(r)}catch(a){console.error("exportClient fail",a),showToast(t("client-msg-save-fail")+" · "+(a.message||""),"fail")}}function Zt(){const e=document.getElementById("drawer-client-select");if(!e)return;const n=e.value;e.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+X.clients.map(a=>`<option value="${a.id}">${escapeHtml(a.name)}</option>`).join(""),e.value=n||""}function Mn(){const e=document.getElementById("history-client-filter");if(!e)return;const n=e.value;e.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+X.clients.map(a=>`<option value="${a.id}">${escapeHtml(a.name)}</option>`).join(""),e.value=n||""}function Ti(e){X.custTab=e==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(o=>o.classList.toggle("active",o.dataset.custTab===X.custTab));const n=document.getElementById("cust-pane-seller"),a=document.getElementById("cust-pane-buyer");n&&n.classList.toggle("active",X.custTab==="seller"),a&&a.classList.toggle("active",X.custTab==="buyer")}function Mi(){const e=window._userInfo||{},n=String(e.role||"").toLowerCase(),a=String(e.tenant_role||"").toLowerCase();return e.is_super_admin===!0||e.is_owner===!0||n==="owner"||n==="admin"||a==="owner"||a==="admin"}function Ka(){window._workspaceClientsCache=X.sellerClients,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function $n(){try{const e=await Ie("/api/workspace/clients");X.sellerClients=e&&(e.clients||e.items)||[],window._workspaceClientsCache=X.sellerClients}catch(e){console.error("loadSellerCache fail",e),X.sellerClients=[]}return X.sellerClients}function $i(){const e=zt.keyword.trim().toLowerCase();return e?X.sellerClients.filter(n=>(n.name||"").toLowerCase().includes(e)||(n.tax_id||"").toLowerCase().includes(e)):X.sellerClients}function Ke(){const e=document.getElementById("seller-tbody");if(!e)return;const n=Mi(),a=document.getElementById("btn-seller-new");a&&(a.style.display=n?"":"none");const o=$i(),s=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!o.length){e.innerHTML=`<div class="cust-empty">${escapeHtml(t(zt.keyword?"cust-no-match":"seller-empty"))}</div>`;return}e.innerHTML=o.map(i=>{const c=s!=null&&Number(s)===Number(i.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${i.id}">${escapeHtml(t("seller-set-current"))}</button>`,l=n?`
            <button class="cust-row-btn" data-saction="edit" data-wid="${i.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
            <button class="cust-row-btn danger" data-saction="archive" data-wid="${i.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${i.id}">
            <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(i.name||"#"+i.id)}</span></div>
            <div class="cust-cell-tax">${escapeHtml(i.tax_id||"—")}</div>
            <div class="align-right">${i.invoice_count||0}</div>
            <div class="cust-row-actions">${c}${l}</div>
        </div>`}).join("")}function ea(e){X.editingWsClientId=e?e.id:null,document.getElementById("wsclient-modal-title").textContent=t(e?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=e&&e.name||"",document.getElementById("wsclient-input-tax").value=e&&e.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=e?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function _t(){document.getElementById("wsclient-modal-mask").style.display="none",X.editingWsClientId=null}async function Hi(){const e=document.getElementById("wsclient-input-name").value.trim(),n=document.getElementById("wsclient-input-tax").value.trim();if(!e){showToast(t("client-msg-name-required"),"fail");return}try{X.editingWsClientId?(await Ie("/api/workspace/clients/"+X.editingWsClientId,{method:"PATCH",body:JSON.stringify({name:e,tax_id:n})}),showToast(t("client-msg-updated"),"success")):(await Ie("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:e,tax_id:n||null})}),showToast(t("client-msg-created"),"success")),_t(),await $n(),Ke(),Ka()}catch(a){const o=a&&a.message?a.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+o,"fail")}}async function ta(){if(!X.editingWsClientId)return;const e=X.sellerClients.find(a=>Number(a.id)===Number(X.editingWsClientId));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",e?e.name:""),{danger:!0}))try{const a=X.editingWsClientId;await Ie("/api/workspace/clients/"+a,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(a)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),_t(),await $n(),Ke(),Ka()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const e=document.getElementById("seller-tbody");e&&(e.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const n=document.getElementById("buyer-tbody");n&&(n.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([$n(),pt()]),Ke(),Te()};window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&Ke()});window.bindDrawerClient=function(e,n){const a=document.getElementById("drawer-client-select");if(!a)return;if(Zt(),a.value=n?String(n):"",!e){a.onchange=null;const s=document.getElementById("drawer-client-add");s&&(s.onclick=()=>kt(null));return}a.onchange=async()=>{const s=a.value?parseInt(a.value,10):null;try{await Ie(`/api/history/${e}/assign_client`,{method:"POST",body:JSON.stringify({client_id:s})}),showToast(t("client-msg-updated"),"success");const i=_results[_drawerIdx];i&&(i.client_id=s),await pt()}catch(i){console.error(i),showToast(t("client-msg-save-fail"),"fail"),a.value=n?String(n):""}};const o=document.getElementById("drawer-client-add");o&&(o.onclick=()=>kt(null))};window.fillCategoryDatalist=async function(){try{const e=document.getElementById("drawer-cat-datalist"),n=Date.now();if(n-X.catCache.fetched<300*1e3){e&&(e.innerHTML=X.catCache.items.map(o=>`<option value="${escapeHtml(o)}">`).join("")),Qn(X.catCache.supplier_count);return}const a=await Ie("/api/categories",{method:"GET"});X.catCache.fetched=n,X.catCache.items=a&&a.categories||[],X.catCache.supplier_count=a&&a.supplier_count||0,e&&(e.innerHTML=X.catCache.items.map(o=>`<option value="${escapeHtml(o)}">`).join("")),Qn(X.catCache.supplier_count)}catch(e){console.warn("fillCategoryDatalist failed",e)}};window.getHistoryClientFilter=function(){return X.historyClientFilter};document.addEventListener("DOMContentLoaded",()=>{const e=document.querySelector(".cust-tab-bar");e&&e.addEventListener("click",M=>{const S=M.target.closest("[data-cust-tab]");S&&Ti(S.dataset.custTab)});const n=document.getElementById("btn-buyer-new");n&&n.addEventListener("click",()=>kt(null));const a=document.getElementById("buyer-tbody");a&&a.addEventListener("click",M=>{const S=M.target.closest(".buyer-row-check");if(S){const T=parseInt(S.dataset.cid,10);S.checked?Me.add(T):Me.delete(T);const $=S.closest(".cust-row");$&&$.classList.toggle("selected",S.checked),Ga();return}const C=M.target.closest(".cust-row-btn");if(C){M.stopPropagation();const T=parseInt(C.dataset.cid,10);if(C.dataset.action==="edit"){const $=X.clients.find(A=>A.id===T);$&&kt($)}else C.dataset.action==="export"&&Si(T);return}const k=M.target.closest(".cust-row");if(k&&!M.target.closest(".cust-cell-check")){const T=X.clients.find($=>$.id===parseInt(k.dataset.cid,10));T&&kt(T)}});const o=document.getElementById("buyer-check-all");o&&o.addEventListener("change",()=>{const{items:M}=Tn();M.forEach(S=>{o.checked?Me.add(S.id):Me.delete(S.id)}),Te()});const s=document.getElementById("buyer-batch-cancel");s&&s.addEventListener("click",Bi);const i=document.getElementById("buyer-batch-delete");i&&i.addEventListener("click",Ii);const r=document.getElementById("buyer-prev");r&&r.addEventListener("click",()=>{ge.page>0&&(ge.page--,Te())});const c=document.getElementById("buyer-next");c&&c.addEventListener("click",()=>{ge.page++,Te()});const l=document.getElementById("buyer-search");if(l){let M;l.addEventListener("input",()=>{clearTimeout(M),M=setTimeout(()=>{ge.keyword=l.value,ge.page=0;const S=document.getElementById("buyer-search-clear");S&&(S.style.display=l.value?"":"none"),Te()},200)})}const p=document.getElementById("buyer-search-clear");p&&p.addEventListener("click",()=>{const M=document.getElementById("buyer-search");M&&(M.value=""),ge.keyword="",ge.page=0,p.style.display="none",Te()});const f=document.getElementById("btn-seller-new");f&&f.addEventListener("click",()=>ea(null));const d=document.getElementById("seller-tbody");d&&d.addEventListener("click",M=>{const S=M.target.closest("[data-saction]");if(!S)return;M.stopPropagation();const C=parseInt(S.dataset.wid,10),k=S.dataset.saction,T=X.sellerClients.find($=>Number($.id)===C);k==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(C),Ke(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",T?T.name:""),"success")):k==="edit"?T&&ea(T):k==="archive"&&(X.editingWsClientId=C,ta())});const u=document.getElementById("seller-search");if(u){let M;u.addEventListener("input",()=>{clearTimeout(M),M=setTimeout(()=>{zt.keyword=u.value;const S=document.getElementById("seller-search-clear");S&&(S.style.display=u.value?"":"none"),Ke()},200)})}const m=document.getElementById("seller-search-clear");m&&m.addEventListener("click",()=>{const M=document.getElementById("seller-search");M&&(M.value=""),zt.keyword="",m.style.display="none",Ke()});const h=document.getElementById("wsclient-modal-close");h&&h.addEventListener("click",_t);const _=document.getElementById("wsclient-modal-cancel");_&&_.addEventListener("click",_t);const y=document.getElementById("wsclient-modal-save");y&&y.addEventListener("click",Hi);const b=document.getElementById("wsclient-modal-archive");b&&b.addEventListener("click",ta);const v=document.getElementById("wsclient-modal-mask");v&&v.addEventListener("click",M=>{M.target===v&&_t()});const L=document.getElementById("client-modal-close");L&&L.addEventListener("click",xt);const g=document.getElementById("client-modal-cancel");g&&g.addEventListener("click",xt);const x=document.getElementById("client-modal-save");x&&x.addEventListener("click",Li);const B=document.getElementById("client-modal-delete");B&&B.addEventListener("click",Ci);const E=document.getElementById("client-modal-mask");E&&E.addEventListener("click",M=>{M.target===E&&xt()});const w=document.getElementById("client-color-picker");w&&w.addEventListener("click",M=>{const S=M.target.closest(".color-swatch");S&&(w.querySelectorAll(".color-swatch").forEach(C=>C.classList.remove("active")),S.classList.add("active"))});const I=document.getElementById("history-client-filter");I&&I.addEventListener("change",()=>{X.historyClientFilter=I.value,typeof renderHistoryList=="function"&&renderHistoryList()})});setTimeout(()=>pt(),1e3);(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const V={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0},G={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null},et={batchLoading:!1};function Fe(e,n){let a=t(e)||e;if(n)for(const o in n)a=a.replace(new RegExp("\\{"+o+"\\}","g"),String(n[o]));return a}function Ai(e){return e==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
    </svg>`}function ji(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 19l5 5 13-13"/>
        <circle cx="20" cy="20" r="17"/>
    </svg>`}function Pi(e){if(e==null)return"—";const n=parseFloat(e);return isNaN(n)?"—":"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function Di(e){return e?e.slice(0,10):"—"}function Xe(e){if(e==null)return"—";const n=typeof e=="number"?e:parseFloat(String(e).replace(/,/g,""));return isNaN(n)?escapeHtml(String(e)):"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function qi(e){if(!e)return"—";try{const n=new Date(e),a=o=>String(o).padStart(2,"0");return`${n.getFullYear()}-${a(n.getMonth()+1)}-${a(n.getDate())} ${a(n.getHours())}:${a(n.getMinutes())}`}catch{return e.slice(0,16).replace("T"," ")}}function Ri(e,n){if(n=n||{},e==="math_mismatch")return`
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(Xe(n.subtotal))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(Xe(n.vat))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(Xe(n.total_expected))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(Xe(n.total_actual))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(Xe(n.diff))}</span></div>
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
        `:e==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(n))}</span></div>`}function je(){const e=G.excRow;if(!e)return;const n=e.seller_name&&e.seller_name.trim()?e.seller_name:t("exc-no-seller"),a=e.filename||"—";document.getElementById("exc-drawer-title").textContent=a;const o="exc-status-"+(e.status||"pending"),s=t(o)||e.status,i="s-"+(e.status||"pending"),r=(e.invoice_date||e.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
        <span>${escapeHtml(n)}</span>
        ${e.invoice_no?`<span>· ${escapeHtml(e.invoice_no)}</span>`:""}
        ${r?`<span>· ${escapeHtml(r)}</span>`:""}
        <span class="exc-status-chip ${i}">${escapeHtml(s)}</span>
    `;const c=e.severity||"medium",l=t("exc-rule-"+e.rule_code)||e.rule_code,p=Ri(e.rule_code,e.detail||{}),f=na(G.history),d=G.history===null,u=G.history&&G.history._err,m=new Set;e.rule_code==="math_mismatch"?(m.add("subtotal"),m.add("vat"),m.add("total_amount")):e.rule_code==="tax_id_format_invalid"?m.add("seller_tax"):e.rule_code==="amount_missing"&&(m.add("total_amount"),m.add("invoice_number"));const h=!!G.editing,_=G.editFields||{},y=(C,k,T)=>{if(d)return`<div class="exc-field-row"><label>${escapeHtml(t(k))}</label><span class="val empty">…</span></div>`;const $=h?_[C]!==void 0?_[C]:f[C]!==void 0&&f[C]!==null?f[C]:"":f[C],A=m.has(C)?"flagged":"";if(h){const R=T?"number":"text",D=T?' step="0.01" inputmode="decimal"':"",j=$==null?"":String($).replace(/"/g,"&quot;");return`<div class="exc-field-row ${A} editing">
                <label>${escapeHtml(t(k))}</label>
                <input class="exc-field-input" type="${R}"${D} data-edit-key="${escapeHtml(C)}" value="${j}">
            </div>`}const H=T?Xe($):$||"",P=$==null||$===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(H)}</span>`;return`<div class="exc-field-row ${A}"><label>${escapeHtml(t(k))}</label>${P}</div>`};let b="";u?b=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:b=`
            <div class="exc-fields">
                ${y("invoice_number","exc-fld-invoice-no",!1)}
                ${y("date","exc-fld-date",!1)}
                ${y("seller_name","exc-fld-seller",!1)}
                ${y("seller_tax","exc-fld-seller-tax",!1)}
                ${y("buyer_name","exc-fld-buyer",!1)}
                ${y("buyer_tax","exc-fld-buyer-tax",!1)}
                ${y("subtotal","exc-fld-subtotal",!0)}
                ${y("vat","exc-fld-vat",!0)}
                ${y("total_amount","exc-fld-total",!0)}
            </div>
        `;const v=(()=>{if(G.pdfStatus==="loading"||G.pdfStatus==="idle")return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M18 4v8a14 14 0 1014 14"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                </div>
            `;if(G.pdfStatus==="empty")return`
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
            `;if(G.pdfStatus==="error")return`
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
            `;const C=G.pdfUrl;return`
            <div class="exc-pdf-toolbar">
                <span class="exc-pdf-toolbar-title">${escapeHtml(a)}</span>
                <div class="exc-pdf-toolbar-actions">
                    <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${C}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M8 2h4v4M12 2L7 7"/>
                            <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                        </svg>
                    </a>
                    <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${C}" download="${escapeHtml(a)}" title="${escapeHtml(t("exc-pdf-download"))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                        </svg>
                    </a>
                </div>
            </div>
            <iframe class="exc-pdf-frame" src="${C}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
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
                <div class="exc-why sev-${escapeHtml(c)}">
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
                    ${e.status==="pending"&&!d&&!u?h?`
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
    `;const L=document.getElementById("exc-fld-edit");L&&L.addEventListener("click",()=>{G.editing=!0,G.editFields={...na(G.history)},je()});const g=document.getElementById("exc-fld-cancel");g&&g.addEventListener("click",()=>{G.editing=!1,G.editFields=null,je()});const x=document.getElementById("exc-fld-save");x&&x.addEventListener("click",()=>Ni()),document.querySelectorAll(".exc-field-input").forEach(C=>{C.addEventListener("input",()=>{G.editFields||(G.editFields={}),G.editFields[C.dataset.editKey]=C.value})});const E=document.getElementById("exc-pdf-retry");E&&G.openExcId&&E.addEventListener("click",()=>{G.excRow&&Ja(G.excRow.history_id,G.openExcId)});const w=e.status==="pending",I=!!(e.seller_name&&e.seller_name.trim()),M=document.getElementById("exc-btn-resolve"),S=document.getElementById("exc-btn-ignore");M.disabled=!w,S.disabled=!w||!I,S.title=I?t("exc-ignore-hint"):t("exc-ignore-no-seller")}function Hn(){if(G.pdfUrl){try{URL.revokeObjectURL(G.pdfUrl)}catch{}G.pdfUrl=null}G.pdfStatus="idle"}async function Ja(e,n){G.pdfStatus="loading",je();try{const a=await fetch("/api/history/"+encodeURIComponent(e)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(G.openExcId!==n)return;if(a.status===404){G.pdfStatus="empty",je();return}if(!a.ok)throw new Error("http "+a.status);const o=await a.blob();if(G.openExcId!==n)return;Hn(),G.pdfUrl=URL.createObjectURL(o),G.pdfStatus="ready",je()}catch(a){if(G.openExcId!==n)return;console.warn("loadDrawerPdf fail",a),G.pdfStatus="error",je()}}function Fi(e){const n=(V.listCache||[]).find(a=>a.id===e);if(!n){showToast(t("exc-drawer-error"),"error");return}V.listScrollY=window.scrollY||document.documentElement.scrollTop||0,Hn(),G.editing=!1,G.editFields=null,G.openExcId=e,G.excRow=n,G.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),je(),zi(n.history_id),Ja(n.history_id,e)}function rt(){Hn(),G.editing=!1,G.editFields=null,G.openExcId=null,G.excRow=null,G.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const e=V.listScrollY||0;e>0&&requestAnimationFrame(()=>window.scrollTo(0,e))}async function zi(e){try{const n=await fetch("/api/history/"+encodeURIComponent(e),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);G.history=await n.json()}catch(n){console.warn("loadHistoryDetail fail",n),G.history={_err:!0}}G.excRow&&je()}function na(e){if(!e||!e.pages)return{};const n=e.pages,a=n.find(o=>!o.is_duplicate&&!o.is_copy)||n[0];return a&&a.fields||{}}async function Ni(){if(!G.openExcId||!G.history||!G.history.pages||G.loading)return;G.loading=!0;const e=showToast(t("exc-fld-saving"),"loading",0);try{const n=JSON.parse(JSON.stringify(G.history.pages||[]));let a=n.findIndex(l=>!l.is_duplicate&&!l.is_copy);a<0&&(a=0),n[a]||(n[a]={fields:{}});const o=n[a].fields||{},s=G.editFields||{},i=new Set(["subtotal","vat","total_amount"]),r={...o};for(const l in s){let p=s[l];if((p===""||p===void 0)&&(p=null),i.has(l)&&p!==null){const f=parseFloat(p);p=isNaN(f)?null:f}r[l]=p}n[a].fields=r;const c=await fetch("/api/history/"+encodeURIComponent(G.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:n})});if(!c.ok)throw new Error("http "+c.status);e(),showToast(t("exc-fld-save-ok"),"success"),rt(),await ut(),await ze(),$e()}catch(n){e(),console.warn("save fields fail",n),showToast(t("exc-fld-save-fail"),"error")}finally{G.loading=!1}}async function Oi(){if(!(!G.openExcId||G.loading)){G.loading=!0;try{const e=await fetch("/api/exceptions/"+G.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-resolved"),"success"),rt(),await ut(),await ze(),$e()}catch(e){console.warn("resolve fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{G.loading=!1}}}async function Vi(){if(!(!G.openExcId||G.loading)){G.loading=!0;try{const e=await fetch("/api/exceptions/"+G.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-ignored"),"success"),rt(),await ut(),await ze(),$e()}catch(e){console.warn("ignore fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{G.loading=!1}}}async function $e(){try{const e=V.currentClient||"",n="/api/exceptions/stats?status=pending"+(e?"&client_id="+encodeURIComponent(e):""),a=await fetch(n,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!a.ok)return;const o=await a.json(),s=document.getElementById("nav-exc-badge");if(!s)return;const i=parseInt(o.pending||0,10);i>0?(s.textContent=i>99?"99+":String(i),s.style.display=""):s.style.display="none"}catch{}}function Wa(e){document.getElementById("exc-kpi-pending").textContent=e.pending||0,document.getElementById("exc-kpi-high").textContent=e.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=e.resolved||0,document.getElementById("exc-kpi-learned").textContent=e.learned_rules||0;const n=document.getElementById("exc-status-tab-count-pending"),a=document.getElementById("exc-status-tab-count-resolved"),o=document.getElementById("exc-status-tab-count-ignored");n&&(n.textContent=e.pending||0),a&&(a.textContent=e.resolved||0),o&&(o.textContent=e.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(i=>{i.classList.toggle("active",i.dataset.status===(V.currentStatus||"pending"))})}function An(e){const n=document.getElementById("exc-chips");if(!n)return;const a=e.by_rule||{},o=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let i=`<button class="exc-chip ${!V.currentRule?"active":""}" data-rule="">
        <span>${escapeHtml(t("exc-chip-all"))}</span>
        <span class="exc-chip-count">${e.pending||0}</span>
    </button>`;for(const r of o){const c=a[r]||0;if(c===0&&V.currentRule!==r)continue;const l=V.currentRule===r;i+=`<button class="exc-chip ${l?"active":""}" data-rule="${escapeHtml(r)}">
            <span>${escapeHtml(t("exc-chip-"+r))}</span>
            <span class="exc-chip-count">${c}</span>
        </button>`}n.innerHTML=i,n.querySelectorAll(".exc-chip").forEach(r=>{r.addEventListener("click",()=>{const c=r.dataset.rule||null;V.currentRule=c,ze()})})}function jn(e){const n=document.getElementById("exc-list");if(!n)return;if(!e||e.length===0){n.innerHTML=`<div class="exc-empty">
            ${ji()}
            <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
            <div>${escapeHtml(t("exc-empty-desc"))}</div>
        </div>`,oa();return}const a='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',o=(V.currentStatus||"pending")==="pending";n.innerHTML=e.map(s=>{const i=s.severity||"medium",r=t("exc-rule-"+s.rule_code)||s.rule_code,c=s.seller_name&&s.seller_name.trim()?s.seller_name:t("exc-no-seller"),l=s.filename||"—",p=Di(s.invoice_date||s.created_at),f=s.status==="pending",d=V.selectedIds.has(s.id),u=o&&f;return`
            <div class="exc-row sev-${escapeHtml(i)} ${d?"selected":""}" data-exc-id="${escapeHtml(String(s.id))}">
                <div class="exc-row-check ${d?"checked":""}" data-check-id="${escapeHtml(String(s.id))}" ${u?"":'style="visibility:hidden;"'}>${a}</div>
                <div class="exc-row-sev">${Ai(i)}</div>
                <div class="exc-row-main">
                    <div class="exc-row-title">${escapeHtml(c)} · ${escapeHtml(l)}</div>
                    <div class="exc-row-meta">
                        ${s.invoice_no?`<span><b>${escapeHtml(s.invoice_no)}</b></span>`:""}
                        <span>${escapeHtml(p)}</span>
                    </div>
                </div>
                <div class="exc-row-rule r-${escapeHtml(i)}">${escapeHtml(r)}</div>
                <div class="exc-row-amount">${escapeHtml(Pi(s.total_amount))}</div>
            </div>
        `}).join(""),n.querySelectorAll(".exc-row").forEach(s=>{s.addEventListener("click",i=>{if(i.target.closest(".exc-row-check"))return;const r=s.dataset.excId;r&&Fi(parseInt(r,10))})}),n.querySelectorAll(".exc-row-check").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation();const r=parseInt(s.dataset.checkId,10);r&&(V.selectedIds.has(r)?(V.selectedIds.delete(r),s.classList.remove("checked"),s.closest(".exc-row").classList.remove("selected")):(V.selectedIds.add(r),s.classList.add("checked"),s.closest(".exc-row").classList.add("selected")),aa())})}),aa(),oa()}function aa(){const e=document.getElementById("exc-batch-bar"),n=document.getElementById("exc-batch-count");if(!e||!n)return;const a=V.selectedIds.size;a===0?e.style.display="none":(e.style.display="",n.textContent=Fe("exc-batch-count",{n:a}))}function oa(){const e=document.getElementById("exc-list-foot"),n=document.getElementById("exc-list-count"),a=document.getElementById("exc-loadmore");if(!e||!n||!a)return;const o=V.listCache.length;if(o===0){e.style.display="none";return}e.style.display="";let s=o;const i=V.statsCache;i&&(V.currentRule?s=(i.by_rule||{})[V.currentRule]||o:s=i.pending||o),V.total=s,n.textContent=Fe("exc-list-count",{shown:o,total:s});const r=o<s&&o<500;a.style.display=r?"":"none"}async function ut(){try{if(navigator.onLine===!1)throw new Error("offline");const e=V.currentClient||"",n=V.currentStatus||"pending",a=new URLSearchParams;a.set("status",n),e&&a.set("client_id",e);const o="/api/exceptions/stats?"+a.toString(),s=await fetch(o,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!s.ok)throw new Error("http "+s.status);const i=await s.json();return V.statsCache=i,Wa(i),An(i),i}catch(e){return console.warn("loadExceptionsStats fail",e),null}}function Ui(e){const n=document.getElementById("exc-list");if(!n)return;const a=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="18" cy="18" r="14"/>
        <line x1="18" y1="11" x2="18" y2="19"/>
        <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
    </svg>`,o=e?t("exc-offline"):t("exc-error-retry-title"),s=e?"":t("exc-error-retry-desc");n.innerHTML=`
        <div class="exc-error">
            ${a}
            <div class="exc-error-msg">${escapeHtml(o)}${s?" · "+escapeHtml(s):""}</div>
            <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
        </div>`;const i=document.getElementById("exc-retry-btn");i&&i.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function ze(e){e=e||{};const n=!!e.append,a=document.getElementById("exc-list");!n&&a&&V.listCache.length===0&&(a.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const o=new URLSearchParams;o.set("status",V.currentStatus||"pending"),V.currentRule&&o.set("rule_code",V.currentRule),V.currentClient&&o.set("client_id",V.currentClient);const s=n?V.listCache.length:0;o.set("limit",String(V.pageSize)),o.set("offset",String(s));try{if(navigator.onLine===!1)throw new Error("offline");const i=await fetch("/api/exceptions/list?"+o.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!i.ok)throw new Error("http "+i.status);const c=(await i.json()).items||[];n?V.listCache=V.listCache.concat(c):(V.listCache=c,V.selectedIds.clear()),V.loadFailed=!1,jn(V.listCache),V.statsCache&&An(V.statsCache)}catch(i){console.warn("loadExceptionsList fail",i),V.loadFailed=!0;const r=navigator.onLine===!1||String(i.message||"").includes("offline");n?showToast(t("exc-toast-load-fail"),"error"):(Ui(r),showToast(r?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function Gi(){if(!V.loading&&!(V.listCache.length>=500)){V.loading=!0;try{await ze({append:!0})}finally{V.loading=!1}}}function Pn(){const e=document.getElementById("exc-client-filter");if(!e)return;const n=window._clientsCache||[],a=V.currentClient||"",o=typeof t=="function"?t("history-client-all"):"全部客户";e.innerHTML=`<option value="">${escapeHtml(o)}</option>`+n.map(s=>`<option value="${s.id}">${escapeHtml(s.name)}</option>`).join(""),e.value=a}async function Ki(){if(et.batchLoading)return;const e=Array.from(V.selectedIds);if(e.length===0||!await showConfirm(Fe("exc-batch-confirm-resolve",{n:e.length})))return;et.batchLoading=!0;const a=showToast(Fe("exc-batch-count",{n:e.length})+" …","loading",0);try{const o=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"resolve"})});if(!o.ok)throw new Error("http "+o.status);const s=await o.json();a(),showToast(Fe("exc-toast-batch-resolved",{n:s.processed||0}),"success"),V.selectedIds.clear(),await ut(),await ze(),$e()}catch(o){a(),console.warn("batch resolve fail",o),showToast(t("exc-toast-batch-fail"),"error")}finally{et.batchLoading=!1}}async function Ji(){if(et.batchLoading)return;const e=Array.from(V.selectedIds);if(e.length===0||!await showConfirm(Fe("exc-batch-confirm-ignore",{n:e.length}),{danger:!1}))return;et.batchLoading=!0;const a=showToast(Fe("exc-batch-count",{n:e.length})+" …","loading",0);try{const o=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"ignore"})});if(!o.ok)throw new Error("http "+o.status);const s=await o.json();a(),showToast(Fe("exc-toast-batch-ignored",{n:s.processed||0,wl:s.whitelist_added||0}),"success"),V.selectedIds.clear(),await ut(),await ze(),$e()}catch(o){a(),console.warn("batch ignore fail",o),showToast(t("exc-toast-batch-fail"),"error")}finally{et.batchLoading=!1}}function Wi(){V.selectedIds.clear(),jn(V.listCache)}async function Ya(){const e=document.getElementById("learned-list");if(e){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const n=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);const o=(await n.json()).items||[];if(o.length===0){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const s=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
        </svg>`;e.innerHTML=o.map(i=>{const r=t("exc-rule-"+i.rule_code)||i.rule_code;return`
                <div class="learned-row" data-wl-id="${escapeHtml(String(i.id))}">
                    <div class="learned-seller" title="${escapeHtml(i.seller_name)}">${escapeHtml(i.seller_name)}</div>
                    <div class="learned-rule">${escapeHtml(r)}</div>
                    <div class="learned-date">${escapeHtml(qi(i.created_at))}</div>
                    <button class="learned-del-btn" data-del-wl="${escapeHtml(String(i.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${s}</button>
                </div>
            `}).join("")}catch(n){console.warn("loadLearnedRules fail",n),e.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadExceptionsPage=async function(){if(!V.loading){V.loading=!0;try{Pn(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await ut(),await ze()}finally{V.loading=!1}}};window.refreshExcBadge=$e;window._refreshExcClientFilter=Pn;window._excState=V;window._rerenderExceptions=function(){try{Pn()}catch{}V.statsCache&&(Wa(V.statsCache),An(V.statsCache)),V.listCache&&V.listCache.length&&jn(V.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}G.openExcId&&je()};document.addEventListener("click",e=>{e.target.closest("#exc-drawer-close")&&rt(),e.target.closest("#exc-drawer-mask")&&rt(),e.target.closest("#exc-btn-resolve")&&Oi(),e.target.closest("#exc-btn-ignore")&&Vi(),e.target.closest("#exc-batch-resolve")&&Ki(),e.target.closest("#exc-batch-ignore")&&Ji(),e.target.closest("#exc-batch-clear")&&Wi(),e.target.closest("#exc-loadmore")&&Gi()});document.addEventListener("keydown",e=>{e.key==="Escape"&&G.openExcId&&rt()});document.addEventListener("click",e=>{e.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),$e())});document.addEventListener("change",e=>{if(!e.target.closest("#exc-client-filter"))return;const n=e.target;V.currentClient=n.value||"",V.currentRule=null,V.selectedIds.clear(),V.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),$e()});document.addEventListener("click",e=>{const n=e.target.closest("#exc-status-tabs .exc-status-tab");if(!n)return;const a=n.dataset.status||"pending";a!==V.currentStatus&&(V.currentStatus=a,V.currentRule=null,V.selectedIds.clear(),V.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())});window.addEventListener("online",()=>{V.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()});setTimeout($e,1500);setInterval($e,6e4);window.loadLearnedRules=Ya;document.addEventListener("click",async e=>{const n=e.target.closest("[data-del-wl]");if(!n)return;const a=parseInt(n.dataset.delWl,10);if(!a)return;const o=n.closest(".learned-row"),s=o&&o.querySelector(".learned-seller"),i=s?s.textContent.trim():"",r=t("set-learned-del-confirm").replace("{seller}",i);if(await showConfirm(r,{danger:!0}))try{const l=await fetch("/api/exception-whitelist/"+a,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!l.ok)throw new Error("http "+l.status);showToast(t("set-learned-del-ok"),"success"),Ya(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(l){console.warn("delete whitelist fail",l),showToast(t("set-learned-del-fail"),"error")}});(function(){let e={items:[],q:"",cat:"",adapter:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(d){const u=typeof currentLang=="string"&&currentLang||window._currentLang||"th",m=d.error_friendly&&d.error_friendly[u];if(m)return m;if(typeof humanizeError=="function"&&d.error_msg)try{return humanizeError(d.error_msg)}catch{}return t("erp-exc-reason-"+(d.category||"other"))}function s(){const d=document.getElementById("erp-exc-batch");if(!d)return;const u=e.selected.size;d.hidden=u===0;const m=d.querySelector(".erp-exc-batch-count");m&&(m.textContent=String(u))}function i(){const d=document.getElementById("erp-exc-block");if(!d)return;const u=e;if(!(u.total>0||!!u.q||!!u.cat)){d.hidden=!0,d.innerHTML="";return}d.hidden=!1;const h=u.categories||{},_=Object.keys(h).reduce((H,P)=>H+h[P],0);let y=`<button class="erp-exc-chip ${u.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${_}</span></button>`;Object.keys(h).forEach(H=>{y+=`<button class="erp-exc-chip ${u.cat===H?"active":""}" data-erpexc-cat="${escapeHtml(H)}"><span>${escapeHtml(t("erp-exc-cat-"+H))}</span><span class="erp-exc-chip-count">${h[H]}</span></button>`});const b=u.items||[],v=b.length>0&&b.every(H=>u.selected.has(H.id)),L=b.map(H=>{const P=H.state==="needs_action"?"needs":H.state==="retrying"?"retry":"fail",R=t("erp-exc-state-"+(H.state||"failed")),D=o(H),j=u.selected.has(H.id)?"checked":"",F=H.push_type==="id_card",ee=F?`<span class="erp-exc-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span> `:"",te=F?`<span class="ex-inv" title="${escapeHtml(t("erp-log-col-booking"))}">${ee}${escapeHtml(H.invoice_no||"—")}</span>`:`<span class="ex-inv" title="${escapeHtml(H.invoice_no||"")}">${escapeHtml(H.invoice_no||"—")}</span>`,ie=F?`<span class="ex-seller" title="${escapeHtml(t("erp-log-col-customer"))}">${escapeHtml(H.seller_name||"—")}</span>`:`<span class="ex-seller" title="${escapeHtml(H.seller_name||"")}">${escapeHtml(H.seller_name||"—")}</span>`,ne=F?`<span class="ex-buyer" title="${escapeHtml(t("erp-log-col-idcard"))}">${H.id_card_tail?"••••"+escapeHtml(H.id_card_tail):"—"}</span>`:`<span class="ex-buyer" title="${escapeHtml(H.ocr_buyer_name||"")}">${escapeHtml(H.ocr_buyer_name||"—")}</span>`;return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(H.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(H.id)}" ${j}></span>
                ${te}
                ${ie}
                ${ne}
                <span class="ex-state"><span class="erp-exc-state ${P}">${escapeHtml(R)}</span></span>
                <span class="ex-reason" title="${escapeHtml(D)}">${escapeHtml(D)}${H.error_code?` <span class="erp-exc-code">${escapeHtml(H.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(H.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),g=b.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",x=b.length<u.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${b.length}/${u.total})</button>`:u.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:b.length,total:u.total}))}</div>`:"",B=u.adapter==="mrerp_dms",E=Array.isArray(window._erpEndpoints)?window._erpEndpoints:[],w=new Set;let I=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`;E.forEach(H=>{const P=(H&&H.adapter||"").toLowerCase();!P||w.has(P)||(w.add(P),I+=`<option value="${escapeHtml(P)}"${P===u.adapter?" selected":""}>${escapeHtml(H&&H.name||P)}</option>`)});const M=B?t("erp-log-col-booking"):t("erp-exc-f-invoice"),S=B?t("erp-log-col-customer"):t("erp-exc-f-seller"),C=B?t("erp-log-col-idcard"):t("erp-exc-f-buyer");d.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${I}</select>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(u.q)}">
            </div>
            <div class="erp-exc-chips">${y}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${u.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${u.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${v?"checked":""}></span>
                    <span class="ex-inv">${escapeHtml(M)}</span>
                    <span class="ex-seller">${escapeHtml(S)}</span>
                    <span class="ex-buyer">${escapeHtml(C)}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${L}${g}
            </div>
            <div class="erp-exc-foot">${x}</div>`;const k=document.getElementById("erp-exc-search");if(k){if(u.focusSearch){k.focus();try{k.setSelectionRange(u.searchCaret,u.searchCaret)}catch{}}k.addEventListener("input",()=>{u.q=k.value,u.focusSearch=!0,u.searchCaret=k.selectionStart||k.value.length,clearTimeout(n),n=setTimeout(()=>l(!1),350)}),k.addEventListener("blur",()=>{u.focusSearch=!1})}d.querySelectorAll(".erp-exc-chip").forEach(H=>{H.addEventListener("click",()=>{u.cat=H.dataset.erpexcCat||"",l(!1)})});const T=document.getElementById("erp-exc-erp-select");T&&T.addEventListener("change",()=>{u.adapter=T.value||"",l(!1)}),d.querySelectorAll("[data-erpexc-retry]").forEach(H=>{H.addEventListener("click",P=>{P.stopPropagation(),r(H.dataset.erpexcRetry,H)})}),d.querySelectorAll(".erp-exc-cb").forEach(H=>{H.addEventListener("change",()=>{const P=H.dataset.erpexcCb;H.checked?u.selected.add(P):u.selected.delete(P);const R=document.getElementById("erp-exc-cb-all");R&&(R.checked=b.length>0&&b.every(D=>u.selected.has(D.id))),s()})});const $=document.getElementById("erp-exc-cb-all");$&&$.addEventListener("change",()=>{b.forEach(H=>{$.checked?u.selected.add(H.id):u.selected.delete(H.id)}),d.querySelectorAll(".erp-exc-cb").forEach(H=>{H.checked=$.checked}),s()}),d.querySelectorAll("[data-erpexc-batch]").forEach(H=>{H.addEventListener("click",()=>c(H.dataset.erpexcBatch))});const A=document.getElementById("erp-exc-more");A&&A.addEventListener("click",()=>l(!0)),d.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(H=>{H.addEventListener("click",P=>{P.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(H.dataset.erpexcId)})})}async function r(d,u){if(d){u&&(u.disabled=!0,u.textContent=t("erp-exc-retrying"));try{const m=await fetch("/api/erp/logs/"+encodeURIComponent(d)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),h=await m.json().catch(()=>({}));showToast(m.ok&&h.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),m.ok&&h.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(d),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function c(d){const u=Array.from(e.selected);if(d==="clear"){e.selected.clear(),i();return}if(u.length!==0){if(d==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:u.length}),{danger:!0}))return;try{const h=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,200)})}),_=await h.json().catch(()=>({}));showToast(h.ok?t("erp-exc-batch-delete-ok",{n:_.deleted||0}):t("erp-exc-retry-fail"),h.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(d==="retry")try{const m=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,50)})}),h=await m.json().catch(()=>({}));showToast(m.ok?t("erp-exc-batch-retry-ok",{ok:h.succeeded||0,fail:(h.failed||0)+(h.skipped||0)}):t("erp-exc-retry-fail"),m.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function l(d){const u=document.getElementById("erp-exc-block");if(!(!u||e.loading)){e.loading=!0;try{if(!Array.isArray(window._erpEndpoints)||!window._erpEndpoints.length)try{const b=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+a()}});if(b.ok){const v=await b.json();window._erpEndpoints=v&&(v.items||v)||[]}}catch{}const m=new URLSearchParams;e.q&&m.set("q",e.q),e.cat&&m.set("category",e.cat),e.adapter&&m.set("adapter",e.adapter),m.set("limit",String(e.pageSize)),m.set("offset",String(d?e.items.length:0));const h=await fetch("/api/erp/exceptions?"+m.toString(),{headers:{Authorization:"Bearer "+a()}});if(!h.ok){d||(u.hidden=!0);return}const _=await h.json(),y=_.items||[];e.items=d?e.items.concat(y):y,e.total=_.total||0,e.categories=_.categories||{},i()}catch{d||(u.hidden=!0)}finally{e.loading=!1}}}let p={};function f(){const d=document.getElementById("erp-exc-modal");d&&d.remove()}window._erpExcOpenEdit=function(d){const u=(e.items||[]).find(x=>String(x.id)===String(d));if(!u)return;const m=u.push_type==="id_card",h=!!u.history_client_id&&u.category==="customer_mismatch",_=u.category==="product_mismatch"&&!!u.history_id&&!!u.endpoint_id,y=o(u),b=u.state==="needs_action"?"needs":u.state==="retrying"?"retry":"fail",v=(x,B)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(x)}</span><span class="erp-exc-m-v">${escapeHtml(B||"—")}</span></div>`;let L="";if(h)L=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(_)L=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const x="erp-exc-edit-hint-"+(u.category||"other");let B=t(x);(!B||B===x)&&(B=y),L=`<div class="erp-exc-m-hint">${escapeHtml(B)}</div>`}const g=document.createElement("div");if(g.id="erp-exc-modal",g.className="erp-exc-modal-overlay",g.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${b}">${escapeHtml(t("erp-exc-state-"+(u.state||"failed")))}</span> ${escapeHtml(y)}${u.error_code&&!m?` <span class="erp-exc-code">${escapeHtml(u.error_code)}</span>`:""}</div>
                    ${v(m?t("erp-log-col-booking"):t("erp-exc-f-invoice"),u.invoice_no)}
                    ${v(m?t("erp-log-col-customer"):t("erp-exc-f-seller"),u.seller_name)}
                    ${m?v(t("erp-log-col-idcard"),u.id_card_tail?"••••"+u.id_card_tail:"—"):v(t("erp-exc-f-buyer"),u.ocr_buyer_name)+v(t("erp-exc-edit-field-current"),u.client_name)}
                    ${L}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${h?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${_?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(g),g.addEventListener("click",x=>{x.target===g&&f()}),document.getElementById("erp-exc-m-close").addEventListener("click",f),document.getElementById("erp-exc-m-cancel").addEventListener("click",f),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{f(),r(u.id,null)}),h){let x="";const B=document.getElementById("erp-exc-m-bind"),E=document.getElementById("erp-exc-m-custlist"),w=document.getElementById("erp-exc-m-search"),I=(S,C)=>{const k=(C||"").trim().toLowerCase(),T=k?S.filter($=>($.code||"").toLowerCase().includes(k)||($.name||"").toLowerCase().includes(k)):S;if(T.length===0){E.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}E.innerHTML=T.slice(0,100).map($=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml($.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml($.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml($.code||"")}</span>
                    </div>`).join(""),E.querySelectorAll(".erp-exc-m-cust").forEach($=>{$.addEventListener("click",()=>{x=$.dataset.custCode||"",E.querySelectorAll(".erp-exc-m-cust").forEach(A=>A.classList.remove("sel")),$.classList.add("sel"),B&&(B.disabled=!x)})})},M=async()=>{const S=u.endpoint_id;if(p[S]){I(p[S],"");return}try{const C=await fetch("/api/erp/endpoints/"+encodeURIComponent(S)+"/customers",{headers:{Authorization:"Bearer "+a()}}),k=await C.json().catch(()=>({}));if(!C.ok||!k.ok){E.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const T=k.customers||[];p[S]=T,I(T,"")}catch{E.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};w&&w.addEventListener("input",()=>I(p[u.endpoint_id]||[],w.value)),M(),B&&B.addEventListener("click",async()=>{if(x){B.disabled=!0,B.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:u.history_client_id,erp_type:u.endpoint_adapter,erp_code:x})})).ok){showToast(t("erp-exc-retry-fail"),"error"),B.disabled=!1,B.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),f(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),B.disabled=!1,B.textContent=t("erp-exc-edit-bind-retry")}}})}if(_){const x=document.getElementById("erp-exc-m-bind-prod"),B=document.getElementById("erp-exc-m-prodlist"),E={};let w=[];const I=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+w.slice(0,500).map(C=>`<option value="${escapeHtml(C.code||"")}" data-pname="${escapeHtml(C.name||"")}">`+escapeHtml((C.name||"")+" · "+(C.code||""))+"</option>").join(""),M=C=>{if(!C.length){B.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}B.innerHTML=C.map(k=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(k)}">${escapeHtml(k)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(k)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${I()}</select>
                    </div>`).join(""),B.querySelectorAll(".erp-exc-m-prod-sel").forEach(k=>{k.addEventListener("change",()=>{const T=k.dataset.item,$=k.options[k.selectedIndex];k.value?E[T]={code:k.value,name:$&&$.dataset.pname||""}:delete E[T],x&&(x.disabled=Object.keys(E).length===0)})})};(async()=>{try{const k=await(await fetch("/api/history/"+encodeURIComponent(u.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),T=k&&k.pages||[],$=[],A={};(Array.isArray(T)?T:[]).forEach(R=>{const D=R&&R.fields&&R.fields.items||[];(Array.isArray(D)?D:[]).forEach(j=>{const F=(j&&(j.name||j.description)||"").trim();F&&!A[F]&&(A[F]=1,$.push(F))})});const H=await fetch("/api/erp/endpoints/"+encodeURIComponent(u.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),P=await H.json().catch(()=>({}));if(!H.ok||!P.ok){B.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}w=P.products||[],M($)}catch{B.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),x&&x.addEventListener("click",async()=>{const C=Object.entries(E);if(C.length){x.disabled=!0,x.textContent=t("erp-exc-retrying");try{for(const[k,T]of C)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:u.endpoint_adapter,item_name:k,erp_code:T.code,erp_name:T.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),x.disabled=!1,x.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),f(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),x.disabled=!1,x.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=i,window.loadErpExceptions=l,window._erpExcState=e})();const Yi=`
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
`;be("cmdk-mask",Yi);(function(){function e(d){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||d&&d.id&&String(d.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var u=window._userInfo,m=!1,h=!0,_=!1,y=!1;u&&(m=typeof canManageTeam=="function"?canManageTeam(u):!!(u.role==="owner"||u.is_super_admin),h=typeof shouldHideMoney=="function"?shouldHideMoney(u):u.role==="member"&&!u.is_super_admin,_=typeof isSuperAdmin=="function"?isSuperAdmin(u):!!u.is_super_admin,y=e(u)),document.querySelectorAll("[data-show-if-team]").forEach(function(v){v.style.display=m?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(v){v.style.display=h?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(v){v.style.display=_?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(v){v.style.display=y?"":"none"});var b=_||y;document.querySelectorAll("[data-show-if-special]").forEach(function(v){v.style.display=b?"":"none"})},window.renderAvatarMenu=function(u){if(u){var m=document.getElementById("avatar-btn"),h=document.getElementById("avatar-popup-name"),_=document.getElementById("avatar-popup-email");if(!(!m||!h||!_)){var y=(u.username||"").trim(),b=y.split("@")[0]||y||"—",v=(y.charAt(0)||"?").toUpperCase(),L=(u.avatar_url||"").trim();if(L){var g=L.replace(/"/g,"&quot;"),x=v.replace(/'/g,"\\'");m.innerHTML='<img src="'+g+'" alt="'+v+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+x+`'">`}else m.textContent=v;h.textContent=b,_.textContent=y||"—",m.setAttribute("title",y||"")}}};function n(){var d=document.getElementById("avatar-wrap"),u=document.getElementById("avatar-btn"),m=document.getElementById("avatar-popup");if(!d||!u||!m)return;function h(){m.classList.remove("show"),u.setAttribute("aria-expanded","false")}function _(){m.classList.add("show"),u.setAttribute("aria-expanded","true")}u.addEventListener("click",function(y){y.stopPropagation(),m.classList.contains("show")?h():_()}),document.addEventListener("click",function(y){m.classList.contains("show")&&!d.contains(y.target)&&h()}),m.addEventListener("click",function(y){var b=y.target.closest(".avatar-popup-item");if(b){var v=b.dataset.action;switch(h(),v){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var L=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(L||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var g=document.getElementById("help-modal");g&&(g.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=h}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(d){return d.style.display!=="none"})}function o(d){var u=a();u.forEach(function(m){m.classList.remove("focus")}),u[d]&&(u[d].classList.add("focus"),u[d].scrollIntoView({block:"nearest"}))}function s(d){var u=a();if(u.length){var m=u.findIndex(function(_){return _.classList.contains("focus")});m<0&&(m=0);var h=(m+d+u.length)%u.length;o(h)}}function i(d){d=(d||"").toLowerCase().trim();var u=0,m=window._userInfo,h=typeof isSuperAdmin=="function"?isSuperAdmin(m):!!(m&&m.is_super_admin),_=e(m);document.querySelectorAll(".cmdk-item").forEach(function(b){if(b.dataset.showIfAdmin==="1"&&!h){b.style.display="none";return}if(b.dataset.showIfTest==="1"&&!_){b.style.display="none";return}var v=(b.dataset.cmdkText||b.textContent||"").toLowerCase(),L=!d||v.indexOf(d)>=0;b.style.display=L?"":"none",b.classList.remove("focus"),L&&u++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(b){for(var v=b.nextElementSibling,L=!1;v&&!v.hasAttribute("data-cmdk-section");){if(v.classList&&v.classList.contains("cmdk-item")&&v.style.display!=="none"){L=!0;break}v=v.nextElementSibling}b.style.display=L?"":"none"});var y=document.getElementById("cmdk-empty");y&&(y.style.display=u===0?"flex":"none"),o(0)}window.openCmdk=function(){var u=document.getElementById("cmdk-mask");u&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),u.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var m=document.getElementById("cmdk-input");m&&(m.value="",i(""),m.focus(),o(0))},50))},window.closeCmdk=function(){var u=document.getElementById("cmdk-mask");u&&u.classList.remove("show")};function r(d){if(d){if(d.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var u=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(u||"即将上线","info")}return}var m=d.dataset.cmdkRoute,h=d.dataset.cmdkAction;if(window.closeCmdk(),m){typeof routeTo=="function"&&routeTo(m);return}if(h){if(h==="open-admin"){window.location.href="/admin/cost";return}if(h.indexOf("lang-")===0){var _=h.slice(5);typeof applyLang=="function"&&applyLang(_)}}}}function c(){var d=document.getElementById("cmdk-mask"),u=document.getElementById("cmdk-input"),m=document.getElementById("cmdk-body");if(!(!d||!u||!m)){d.addEventListener("click",function(y){y.target===d&&window.closeCmdk()});var h=document.getElementById("cmdk-esc-btn");h&&h.addEventListener("click",function(){window.closeCmdk()}),u.addEventListener("input",function(y){i(y.target.value)}),u.addEventListener("keydown",function(y){y.key==="ArrowDown"?(y.preventDefault(),s(1)):y.key==="ArrowUp"?(y.preventDefault(),s(-1)):y.key==="Enter"?(y.preventDefault(),r(d.querySelector(".cmdk-item.focus"))):y.key==="Escape"&&(y.preventDefault(),window.closeCmdk())}),m.addEventListener("click",function(y){var b=y.target.closest(".cmdk-item");b&&r(b)}),m.addEventListener("mousemove",function(y){var b=y.target.closest(".cmdk-item");!b||b.style.display==="none"||b.classList.contains("cmdk-item-locked")||(a().forEach(function(v){v.classList.remove("focus")}),b.classList.add("focus"))});var _=document.getElementById("topbar-search");_&&(_.addEventListener("click",function(){window.openCmdk()}),_.addEventListener("keydown",function(y){(y.key==="Enter"||y.key===" ")&&(y.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(d){if((d.metaKey||d.ctrlKey)&&(d.key==="k"||d.key==="K")){d.preventDefault(),window.openCmdk();return}if(d.key==="Escape"){var u=document.getElementById("cmdk-mask");if(u&&u.classList.contains("show")){window.closeCmdk();return}var m=document.getElementById("avatar-popup");m&&m.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var l=(navigator.userAgent||"").toLowerCase(),p=l.indexOf("mac")>=0||l.indexOf("iphone")>=0||l.indexOf("ipad")>=0;p||document.body.classList.add("is-windows")}catch{}function f(){n(),c(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",f):f()})();(function(){function n(h){return String(h??"").replace(/[&<>"']/g,function(_){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[_]})}function a(h){if(!h||isNaN(h))return"";var _=Number(h);return _<1024?_+" B":_<1024*1024?(_/1024).toFixed(1)+" KB":(_/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(h){var _=h.target.closest&&h.target.closest(".recon-collapse-head");if(_&&!(h.target.closest("button")||h.target.closest("a"))){var y=_.closest(".recon-collapse");if(y){var b=y.getAttribute("data-collapsed")==="true";y.setAttribute("data-collapsed",b?"false":"true"),b&&(y.id==="vex-summary-collapse"&&f(),y.id==="vex-detail-collapse"&&d())}}}),document.addEventListener("keydown",function(h){if(!(h.key!=="Enter"&&h.key!==" ")){var _=h.target.closest&&h.target.closest(".recon-collapse-head");_&&(h.preventDefault(),_.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){l("vat"),l("gl")}function c(h){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(h)||[]}catch{}var _=document.getElementById(h==="vat"?"glv-vat-input":"glv-gl-input");return _&&_.files?Array.from(_.files):[]}function l(h){var _=document.getElementById(h==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(_){var y=c(h),b=h==="vat"?"glv-up-vat-title":"glv-up-gl-title",v=h==="vat"?"① 销项税报告":"② 总账 GL",L=window.t&&window.t(b)||v,g=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),x=n(window.t&&window.t("vex-preview-clear-all")||"全清"),B=o[h]||"",E=y.length;_.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(L)+' <span class="vex-pp-col-count">'+E+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+h+'" type="text" placeholder="'+g+'" value="'+n(B)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+h+'" type="button">'+x+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+h+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+h+'-pg"></div>';var w=document.getElementById("glv-pp-search-"+h);w&&w.addEventListener("input",function(M){o[h]=M.target.value,p(h)});var I=document.getElementById("glv-pp-clearall-"+h);I&&I.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(h)}),p(h)}}function p(h){var _=document.getElementById("glv-pp-"+h+"-list"),y=document.getElementById("glv-pp-"+h+"-pg");if(_){var b=c(h),v=(o[h]||"").toLowerCase(),L=b.map(function(B,E){return{f:B,i:E}}),g=v?L.filter(function(B){return B.f.name.toLowerCase().indexOf(v)>=0}):L;if(_.innerHTML=g.map(function(B){var E=B.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(E.name)+'">'+n(E.name)+'</span><span class="vex-pp-fi-size">'+a(E.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+h+'" data-idx="'+B.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),_.querySelectorAll(".vex-pp-fi-del").forEach(function(B){B.addEventListener("click",function(){var E=B.dataset.kind,w=parseInt(B.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(E,isNaN(w)?null:w)})}),y){var x=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";y.textContent=x.replace("{n}",g.length).replace("{m}",g.length)}}}function f(){var h=function(y,b){var v=document.getElementById(y);v&&(v.textContent=b==null?"—":String(b))},_=window._vexLastTask||{};h("vex-sum-total",_.total),h("vex-sum-matched",_.matched),h("vex-sum-diff",_.diff),h("vex-sum-incomplete",_.incomplete),h("vex-sum-cash",_.cash),document.getElementById("vex-summary-sub")}function d(){var h=window._vexLastTask&&window._vexLastTask.diff_rows||[],_=document.getElementById("vex-detail-tbody"),y=document.getElementById("vex-detail-table"),b=document.getElementById("vex-detail-empty");if(!(!_||!y||!b)){if(h.length===0){y.style.display="none",b.style.display="";return}b.style.display="none",y.style.display="";var v=h.map(function(g){return'<tr><td class="recon-detail-cell-mono">'+n(g.invoice_no||"")+"</td><td>"+n(g.field||"")+"</td><td>"+n(g.report_value||"")+"</td><td>"+n(g.invoice_value||"")+"</td><td>"+n(g.kind||"")+"</td></tr>"}).join("");_.innerHTML=v;var L=document.getElementById("vex-detail-sub");L&&(L.textContent=String(h.length))}}function u(){var h=document.getElementById("glv-toggle-preview");h&&!h._reconBound&&(h._reconBound=!0,h.addEventListener("click",function(){var _=document.getElementById("glv-preview-panel"),y=document.getElementById("glv-toggle-preview-label"),b=_&&_.style.display!=="none";_&&(_.style.display=b?"none":""),h.classList.toggle("open",!b),y&&(y.textContent=b?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),b||r()})),["glv-vat-input","glv-gl-input"].forEach(function(_){var y=document.getElementById(_);!y||y._reconWatched||(y._reconWatched=!0,y.addEventListener("change",function(){var b=document.getElementById("glv-preview-panel");b&&b.style.display!=="none"&&r()}))})}function m(){var h=document.getElementById("vex-summary-collapse"),_=document.getElementById("vex-detail-collapse");h&&(h.style.display=""),_&&(_.style.display=""),f(),d()}window._fillVexSummary=f,window._fillVexDetail=d,window._onVexResultShown=m,document.addEventListener("DOMContentLoaded",function(){u()}),setTimeout(u,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var h=document.getElementById("glv-preview-panel");h&&h.style.display!=="none"&&r();var _=document.getElementById("glv-toggle-preview-label"),y=document.getElementById("glv-toggle-preview");_&&y&&(_.textContent=y.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:f,fillVexDetail:d}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(c=>{c.addEventListener("click",()=>{i.forEach(u=>u.classList.remove("active")),c.classList.add("active");const l=c.dataset.reconTab,p=document.getElementById("recon-pane-bank"),f=document.getElementById("recon-pane-sale-vat"),d=document.getElementById("recon-pane-gl-vat");p&&(p.style.display=l==="bank"?"":"none"),f&&(f.style.display=l==="sale-vat"?"":"none"),d&&(d.style.display=l==="gl-vat"?"":"none"),l==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),l==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const c=document.createElement("button");return c.id="settings-modal-close",c.className="settings-modal-close",c.setAttribute("aria-label","close"),c.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(c,i.firstChild),c.addEventListener("click",s),r.addEventListener("click",l=>{l.target===r&&s()}),r}function o(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(l){console.warn("renderSettings:",l)}let c=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');c&&c.click()},50)}function s(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=q=>document.getElementById(q);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function i(q){return String(q??"").replace(/[&<>"']/g,N=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[N])}function r(q){return q<1024?q+" B":q<1024*1024?(q/1024).toFixed(1)+" KB":(q/1024/1024).toFixed(1)+" MB"}let c=[],l=[],p=!1,f=[],d=50,u=50,m="",h="";async function _(){try{const q=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!q.ok)return;const K=(await q.json()).kpi||{};[["vex-kpi-month-val",K.this_month],["vex-kpi-running-val",K.running],["vex-kpi-done-val",K.done],["vex-kpi-failed-val",K.failed]].forEach(([W,J])=>{const oe=document.getElementById(W);oe&&(oe.textContent=J??0)})}catch{}}async function y(){try{const q=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!q.ok)return;const N=await q.json();g(N.rows||[])}catch{}}const b=10;var v=1;function L(){var q=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(v=1,g(f),!!q){var N=document.getElementById("vex-task-tbody");N&&N.querySelectorAll("tr").forEach(function(K){K.dataset.taskId&&(K.style.display=K.textContent.toLowerCase().indexOf(q)>=0?"":"none")})}}function g(q){f=q||f;const N=document.getElementById("vex-task-tbody");if(!N)return;if(!f.length){N.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",x(0);return}const K=Math.ceil(f.length/b);v>K&&(v=K);const W=(v-1)*b;B(f.slice(W,W+b)),x(f.length)}function x(q){const N=document.getElementById("vex-task-pager"),K=document.getElementById("vex-task-pager-info"),W=document.getElementById("vex-task-prev"),J=document.getElementById("vex-task-next");if(!N)return;if(q<=b){N.style.display="none";return}N.style.display="";const oe=Math.ceil(q/b);K&&(K.textContent=v+" / "+oe),W&&(W.disabled=v<=1),J&&(J.disabled=v>=oe)}function B(q){const N=document.getElementById("vex-task-tbody");if(!N)return;const K={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},W={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},J='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';N.innerHTML=q.map(Y=>{const le=Y.created_at?new Date(Y.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",Q=Y.period||"—",pe=Y.matched_count!=null?Y.matched_count+" ✓ · "+Y.mismatched_count+" ⚠":"—",de=Y.mismatch_amount!=null?"฿ "+Number(Y.mismatch_amount).toLocaleString():"—",he=Y.elapsed_seconds!=null?Y.elapsed_seconds.toFixed(1)+" s":"—",Le=Y.status||"pending",Re=Y.client_name&&Y.client_name!=="client"?Y.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${i(Y.id)}" style="cursor:pointer">
                <td>${le}</td>
                <td>${i(Re)}</td>
                <td>${i(Q)}</td>
                <td>${(Y.invoice_count||0)+" / "+(Y.report_count||0)}</td>
                <td>${pe}</td>
                <td>${de}</td>
                <td><span class="badge ${W[Le]||"badge-gray"}">${K[Le]||Le}</span></td>
                <td>${he}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${i(Y.id)}" title="${t("hist_export")||"导出"}">${J}</button>
                    <button class="vex-task-del-btn" data-task-id="${i(Y.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${oe}</button>
                </div></td>
            </tr>`}).join(""),N.querySelectorAll(".vex-task-dl-btn").forEach(Y=>{Y.addEventListener("click",async le=>{le.stopPropagation();const Q=Y.dataset.taskId;try{const pe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(Q)+"/download",{credentials:"include",headers:s()});if(pe.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!pe.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const de=await pe.blob(),Le=(pe.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),Re=Le?decodeURIComponent(Le[1]):"vat_recon_"+Q+".xlsx",tn=URL.createObjectURL(de),We=document.createElement("a");We.href=tn,We.download=Re,We.click(),setTimeout(()=>URL.revokeObjectURL(tn),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),N.querySelectorAll(".vex-task-del-btn").forEach(Y=>{Y.addEventListener("click",le=>{le.stopPropagation(),w(Y.dataset.taskId)})}),L()}function E(){var q=document.getElementById("vex-task-prev"),N=document.getElementById("vex-task-next");q&&!q._vexBound&&(q._vexBound=!0,q.addEventListener("click",function(){v>1&&(v--,g())})),N&&!N._vexBound&&(N._vexBound=!0,N.addEventListener("click",function(){var K=Math.ceil(f.length/b);v<K&&(v++,g())}))}async function w(q){const N=t("vex-task-delete-confirm-title")||"删除对账任务?",K=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(K,{title:N,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const J=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(q),{method:"DELETE",credentials:"include",headers:s()});if(!J.ok)throw new Error(J.status);showToast(t("vex-task-delete-ok")||"已删除","success"),y(),_()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function I(q){const N=window._currentLang||"th",K={zh:`已忽略 ${q} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${q} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${q} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${q} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(K[N]||K.th,"warn")}function M(q){const N=new Set(c.map(W=>W.name+"|"+W.size));let K=0;for(const W of q){if(!a.test(W.name)){K++;continue}const J=W.name+"|"+W.size;if(!N.has(J)&&(N.add(J),c.push(W),c.length>=1e3))break}K>0&&I(K),c.length>1e3&&(c=c.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),T()}function S(q){const N=new Set(l.map(W=>W.name+"|"+W.size));let K=0;for(const W of q){if(!a.test(W.name)){K++;continue}const J=W.name+"|"+W.size;if(!N.has(J)&&(N.add(J),l.push(W),l.length>=30))break}K>0&&I(K),l.length>30&&(l=l.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),T()}function C(q){c.splice(q,1),T()}function k(q){l.splice(q,1),T()}function T(){const q=o("vex-list-invoice"),N=o("vex-list-report"),K=o("vex-count-invoice"),W=o("vex-count-report");K&&(K.textContent=c.length),W&&(W.textContent=l.length);const J=(le,Q,pe)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${i(le.name)}">${i(le.name)}</span>
            <span class="vex-fi-s">${r(le.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${pe}" data-vex-idx="${Q}" aria-label="remove">×</button>
        </div>`;q&&(q.innerHTML=c.map((le,Q)=>J(le,Q,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),N&&(N.innerHTML=l.map((le,Q)=>J(le,Q,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(le=>{le.addEventListener("click",Q=>{const pe=le.dataset.vexKind,de=parseInt(le.dataset.vexIdx,10);pe==="inv"?C(de):k(de)})});const oe=c.length>0&&l.length>0;o("vex-build").disabled=!oe||p;const Y=o("vex-action-info");Y&&(!c.length||!l.length?(Y.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",Y.className="vex-action-info muted"):(Y.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",c.length).replace("{b}",l.length),Y.className="vex-action-info ok")),P()}const $='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',A='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',H='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function P(){const q=o("vex-preview-panel");if(!q||q.style.display==="none")return;R("inv"),R("rep");const N=o("vex-pp-guide");N&&(N.style.display=c.length>100?"flex":"none")}function R(q){const N=o(q==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!N)return;const K=q==="inv"?c:l,W=q==="inv"?m:h,J=t(q==="inv"?"vex-preview-invoice":"vex-preview-report")||(q==="inv"?"销售发票":"VAT 报告"),oe=i(t("vex-preview-search")||"搜索文件名..."),Y=i(t("vex-preview-clear-all")||"全清");N.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${i(J)} <span class="vex-pp-col-count">${K.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${q}" type="text"
                       placeholder="${oe}" value="${i(W)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${q}" type="button">${Y}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${q}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${q}-pg"></div>`;const le=o("vex-pp-search-"+q);le&&le.addEventListener("input",pe=>{q==="inv"?(m=pe.target.value,d=50):(h=pe.target.value,u=50),D(q)});const Q=o("vex-pp-clearall-"+q);Q&&Q.addEventListener("click",()=>{q==="inv"?(c=[],m="",d=50):(l=[],h="",u=50),T()}),D(q)}function D(q){const N=o("vex-pp-"+q+"-list"),K=o("vex-pp-"+q+"-pg");if(!N)return;const W=q==="inv"?c:l,J=q==="inv"?m:h,oe=q==="inv"?d:u,Y=q==="inv"?$:A,le=W.map((de,he)=>({f:de,i:he})),Q=J?le.filter(({f:de})=>de.name.toLowerCase().includes(J.toLowerCase())):le,pe=Q.slice(0,oe);if(N.innerHTML=pe.map(({f:de,i:he})=>`
            <div class="vex-pp-file-row">
                ${Y}
                <span class="vex-pp-fi-name" title="${i(de.name)}">${i(de.name)}</span>
                <span class="vex-pp-fi-size">${r(de.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${q}" data-ridx="${he}" aria-label="remove">${H}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${q}" style="height:1px;flex-shrink:0"></div>`,N.querySelectorAll(".vex-pp-fi-del").forEach(de=>{de.addEventListener("click",()=>{const he=parseInt(de.dataset.ridx,10);de.dataset.kind==="inv"?C(he):k(he)})}),K){const de=t("vex-preview-count")||"显示前 {n} / 共 {m}";K.textContent=de.replace("{n}",pe.length).replace("{m}",Q.length)}j(q,Q.length)}function j(q,N){if((q==="inv"?d:u)>=N)return;const W=o("vex-pp-sentinel-"+q),J=o("vex-pp-"+q+"-list");if(!W||!J)return;const oe=new IntersectionObserver(Y=>{Y[0].isIntersecting&&(oe.disconnect(),q==="inv"?d+=50:u+=50,D(q))},{root:J,threshold:.8});oe.observe(W)}function F(q,N,K,W){const J=o(q),oe=o(N);!J||!oe||(J.addEventListener("click",()=>oe.click()),J.addEventListener("keydown",Y=>{(Y.key==="Enter"||Y.key===" ")&&(Y.preventDefault(),oe.click())}),J.addEventListener("dragover",Y=>{Y.preventDefault(),J.classList.add("drag-over")}),J.addEventListener("dragleave",()=>J.classList.remove("drag-over")),J.addEventListener("drop",Y=>{Y.preventDefault(),J.classList.remove("drag-over");const Q=Array.from(Y.dataTransfer.files).filter(pe=>a.test(pe.name));if(!Q.length){showToast(t("vex-toast-bad-ext"),"error");return}K(Q)}),oe.addEventListener("change",()=>{const Y=Array.from(oe.files);K(Y),oe.value=""}))}async function ee(){if(p||!c.length||!l.length)return;p=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var q=document.getElementById("vex-download");q&&(q.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(J){var oe=document.getElementById(J);oe&&(oe.style.display="none")});const N=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",c.length).replace("{b}",l.length);const K=setInterval(()=>{const J=Math.floor((Date.now()-N)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",J).replace("{a}",c.length).replace("{b}",l.length)},1e3);try{const J=new FormData;for(const ye of c)J.append("invoices",ye);for(const ye of l)J.append("reports",ye);const oe=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";J.append("lang",oe);const Y=localStorage.getItem("mrpilot_token")||"",le=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:J});let Q=null;try{Q=await le.json()}catch{Q=null}if(!le.ok||!Q||!Q.ok||!Q.job_id)throw clearInterval(K),new Error(Q&&Q.detail||"HTTP "+le.status);const pe=o("vex-progress-sub"),de=await window._reconPollJob(Q.job_id,Y,{onProgress:ye=>{pe&&(pe.textContent=window._reconProgressText(ye,oe))}});if(clearInterval(K),!de||de.status!=="done"||!de.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const he=de.result_id;let Le=0;const Re=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(he)+"/download",{headers:s()});if(!Re.ok)throw new Error("HTTP "+Re.status);const We=(Re.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),Nn=We&&We[1]||"vat_recon_"+Date.now()+".xlsx",vo=await Re.blob(),On=URL.createObjectURL(vo),Vn=o("vex-download");Vn.href=On,Vn.download=Nn;try{const ye=document.createElement("a");ye.href=On,ye.download=Nn,document.body.appendChild(ye),ye.click(),setTimeout(()=>ye.remove(),100)}catch{}o("vex-progress").style.display="none";var W=document.getElementById("vex-download");W&&(W.style.display=""),he&&(Le=await ne(he)),window._onVexResultShown&&window._onVexResultShown(),Le>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",Le),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),_(),setTimeout(y,800)}catch(J){clearInterval(K),o("vex-progress").style.display="none";const oe=(t("vex-toast-fail")||"生成失败")+": "+(J.message||J);showToast(oe,"error")}finally{p=!1,o("vex-build").disabled=!1}}function te(){c=[],l=[];var q=document.getElementById("vex-download");q&&(q.style.display="none"),T()}function ie(q){if(q==null)return"—";var N=parseFloat(q);return isNaN(N)?"—":N.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function ne(q){try{var N=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(q),{headers:s()});if(!N.ok)throw new Error(N.status);var K=await N.json(),W=K.raw_data_json;if(typeof W=="string")try{W=JSON.parse(W)}catch{W={}}W=W||{};var J=W.rows||[],oe=[];J.forEach(function(Q){Q.kind==="invoice_orphan"?oe.push({invoice_no:Q.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:ie(Q.amount_inv),kind:Q.kind}):Q.kind==="report_orphan"?oe.push({invoice_no:Q.invoice_no||"",field:"仅报告有",report_value:ie(Q.amount_rep),invoice_value:"—",kind:Q.kind}):Q.dims&&Object.keys(Q.dims).length>0&&Object.keys(Q.dims).forEach(function(pe){var de=String(Q.dims[pe]||""),he=de.split(" ≠ ");oe.push({invoice_no:Q.invoice_no||"",field:pe,report_value:he[0]||de,invoice_value:he.length>1?he[1]:"—",kind:"diff"})})});var Y=J.filter(function(Q){return Q.kind==="matched_cash"}).length,le=Math.max(0,parseInt(W.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:W.n_total||0,matched:W.n_ok||0,diff:W.n_diff||0,incomplete:le,cash:Y,diff_rows:oe,task_id:q},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),le}catch{return 0}}function fe(){const q=document.getElementById("vex-pane");q&&q.querySelectorAll("[data-i18n]").forEach(N=>{const K=t(N.dataset.i18n);K&&(N.textContent=K)}),T(),y()}function me(){F("vex-drop-invoice","vex-input-invoice",M),F("vex-drop-report","vex-input-report",S);const q=o("vex-build"),N=o("vex-reset");q&&q.addEventListener("click",ee),N&&N.addEventListener("click",te),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(J=>{J.addEventListener("click",()=>{_(),y()})}),E();const K=document.getElementById("vex-task-search");K&&K.addEventListener("input",L);const W=document.getElementById("vex-toggle-preview");W&&W.addEventListener("click",()=>{const J=o("vex-preview-panel"),oe=o("vex-toggle-preview-label"),Y=J&&J.style.display!=="none";J&&(J.style.display=Y?"none":""),W&&W.classList.toggle("open",!Y),oe&&(oe.textContent=Y?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),Y||P()}),T(),_()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",me):me(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",fe),window.subscribeI18n("vex-preview-panel",P))})();const ae={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},Z=e=>document.getElementById(e),Xa=()=>localStorage.getItem("mrpilot_token")||"",lt=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",Je=()=>({Authorization:"Bearer "+Xa()}),sa={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},ue=e=>(sa[lt()]||sa.th)[e]||e;function Xi(e){const n=lt(),o={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[e];return o?o[n]||o.th||o.en:ue("error")||"Error"}const Et=e=>e==null||isNaN(e)?"":Number(e).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function Dn(e){Z("glv-kpi-matched")&&(Z("glv-kpi-matched").textContent=e&&e.matched!=null?e.matched:"—"),Z("glv-kpi-diff")&&(Z("glv-kpi-diff").textContent=e&&e.diff!=null?e.diff:"—"),Z("glv-kpi-unmatched")&&(Z("glv-kpi-unmatched").textContent=e&&e.unmatched!=null?e.unmatched:"—")}function Zi(e){if(!e)return"";try{const n=new Date(e);if(isNaN(n.getTime()))return e;const a=o=>String(o).padStart(2,"0");return n.getFullYear()+"-"+a(n.getMonth()+1)+"-"+a(n.getDate())+" "+a(n.getHours())+":"+a(n.getMinutes())}catch{return e}}function ia(e,n,a,o){const s=Z(e),i=Z(n),r=Z(a);if(!s||!i||!r)return;const c=l=>{if(!l||!l.length)return;const p=Array.isArray(ae[o])?ae[o].slice():[],f=new Set(p.map(d=>d.name+"|"+d.size));for(const d of l){if(!d)continue;const u=d.name+"|"+d.size;f.has(u)||(p.push(d),f.add(u))}ae[o]=p,Za(r,p),St(),Mt(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};s.addEventListener("click",()=>i.click()),s.addEventListener("keydown",l=>{(l.key==="Enter"||l.key===" ")&&(l.preventDefault(),i.click())}),i.addEventListener("change",()=>{c(Array.from(i.files||[])),i.value=""}),s.addEventListener("dragover",l=>{l.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",()=>s.classList.remove("drag-over")),s.addEventListener("drop",l=>{l.preventDefault(),s.classList.remove("drag-over");const p=l.dataTransfer&&l.dataTransfer.files?Array.from(l.dataTransfer.files):[];c(p)})}function Za(e,n){if(!e)return;if(!n||n.length===0){e.textContent="";return}const a=n.reduce((o,s)=>o+Math.round(s.size/1024),0);if(n.length===1)e.textContent=n[0].name+"  ("+a+" KB)";else{const o=window.t&&window.t("glv-files-count")||"{n} 个文件";e.textContent=o.replace("{n}",n.length)+"  ("+a+" KB)"}}function qe(e){const n=ae[e];return Array.isArray(n)?n:n?[n]:[]}function St(){const e=Z("btn-glv-run");if(!e)return;const n=qe("glFile").length>0&&qe("vatFile").length>0;e.disabled=!n||ae.running}function Mt(){const e=Z("glv-status");if(!e||ae.running)return;const n=qe("vatFile").length,a=qe("glFile").length;n===0&&a===0?(e.className="vex-action-info muted",e.innerHTML="<span>"+ue("hint_need_both")+"</span>"):n>0&&a>0?(e.className="vex-action-info ok",e.innerHTML="<span>"+ue("hint_ready")+"</span>"):(e.className="vex-action-info muted",e.innerHTML="<span>"+ue("hint_need_one_more")+"</span>")}function Qi(e,n){const a=e==="vat"?"vatFile":"glFile",o=e==="vat"?"glv-vat-input":"glv-gl-input",s=e==="vat"?"glv-vat-name":"glv-gl-name",i=qe(a);n==null?ae[a]=[]:ae[a]=i.filter((c,l)=>l!==n);const r=Z(o);r&&(r.value=""),Za(Z(s),qe(a)),St(),Mt(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function er(){ae.glFile=[],ae.vatFile=[],ae.currentTaskId=null,ae.lastDetail=[],ae.lastSummary=null;const e=Z("glv-vat-input");e&&(e.value="");const n=Z("glv-gl-input");n&&(n.value="");const a=Z("glv-vat-name");a&&(a.textContent="");const o=Z("glv-gl-name");o&&(o.textContent="");const s=Z("glv-result");s&&(s.style.display="none");const i=Z("glv-kpi-strip");i&&(i.style.display="none"),St(),Mt(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function qn(e){const n=Z("glv-tbody");if(!n)return;ar(e.length),n.innerHTML="";const a=ue("not_found"),o=document.createDocumentFragment();e.forEach(s=>{const i=document.createElement("tr"),r=(d,u)=>{const m=document.createElement("td");return u&&(m.className=u),m.textContent=d,m},c=s.gl_amount===null||s.gl_amount===void 0,l=s.diff;let p="glv-num",f="glv-num";c?(f+=" glv-cell-missing",p+=" glv-cell-missing"):Math.abs(l||0)<.005?p+=" glv-cell-ok":p+=" glv-cell-diff",i.appendChild(r(s.doc_no||"","glv-doc")),i.appendChild(r(s.date||"","")),i.appendChild(r(s.customer_name||"","")),i.appendChild(r(Et(s.vat_amount),"glv-num")),i.appendChild(r(c?a:Et(s.gl_amount),f)),i.appendChild(r(c?a:Et(s.diff),p)),i.appendChild(r(s.account_codes||"","glv-doc")),o.appendChild(i)}),n.appendChild(o)}function Rn(e){const n=Z("glv-summary-table")&&Z("glv-summary-table").querySelector("tbody");if(!n)return;n.innerHTML="",[{label:ue("s_gl_total"),amount:e.gl_total,emph:!0,items:[],negate:!1},{label:ue("s_minus_gl_cr"),amount:-(e.gl_only_credit||0),emph:!1,items:e.gl_only_credit_items||[],negate:!0},{label:ue("s_plus_gl_dr"),amount:e.gl_only_debit||0,emph:!1,items:e.gl_only_debit_items||[],negate:!1},{label:ue("s_plus_vat_p"),amount:e.vat_only_positive||0,emph:!1,items:e.vat_only_positive_items||[],negate:!1},{label:ue("s_minus_vat_n"),amount:e.vat_only_negative||0,emph:!1,items:e.vat_only_negative_items||[],negate:!1},{label:ue("s_vat_total"),amount:e.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:o,amount:s,emph:i,items:r,negate:c})=>{const l=document.createElement("tr");l.className=i?"glv-summary-total":"glv-summary-sect";const p=document.createElement("td"),f=document.createElement("td");p.textContent=o,f.textContent=i?Et(s):"",l.appendChild(p),l.appendChild(f),n.appendChild(l),(r||[]).forEach(d=>{const u=document.createElement("tr");u.className="glv-summary-item";const m=document.createElement("td"),h=document.createElement("td"),_=[d.doc_no,d.date,d.name].filter(Boolean);m.textContent="· "+_.join("  ·  ");const y=c?-(d.amount||0):d.amount||0;h.textContent=Et(y),u.appendChild(m),u.appendChild(h),n.appendChild(u)})})}async function tr(e){try{const a=await(await fetch("/api/recon/gl-vat/"+e,{headers:Je()})).json();if(!a||!a.ok)throw new Error("load_failed");ae.currentTaskId=e,ae.lastDetail=a.detail||[],ae.lastSummary=a.summary||{},Dn(a.stats||{}),qn(ae.lastDetail),Rn(ae.lastSummary);const o=Z("glv-result");o&&(o.style.display=""),Qa(),window.scrollTo({top:o?o.offsetTop-80:0,behavior:"smooth"})}catch(n){console.error("[gl-vat] load task failed:",n),alert(ue("error")+": "+(n.message||n))}}function Qa(){var e=Z("glv-kpi-strip");e&&(e.style.display="");var n=Z("glv-section-summary");n&&n.setAttribute("data-collapsed","false");var a=Z("glv-section-detail");a&&a.setAttribute("data-collapsed","false")}function nr(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(e=>{const n=e.getAttribute("data-toggle"),a=document.getElementById(n);if(!a)return;const o=s=>{if(s.target&&s.target.closest("button")!==null&&!s.target.classList.contains("glv-section-head"))return;const i=a.getAttribute("data-collapsed")==="true";a.setAttribute("data-collapsed",i?"false":"true")};e.addEventListener("click",o),e.addEventListener("keydown",s=>{(s.key==="Enter"||s.key===" ")&&(s.preventDefault(),o(s))})})}function ar(e){const n=Z("glv-detail-count");n&&(n.textContent=e!=null?String(e):"")}const gt=10;var Ze=[],_e=1;function or(){_e=1,Nt();var e=((Z("glv-hist-search")||{}).value||"").trim().toLowerCase();if(e){var n=Z("glv-history-tbody");n&&n.querySelectorAll("tr").forEach(function(a){a.dataset.taskId&&(a.style.display=a.textContent.toLowerCase().indexOf(e)>=0?"":"none")})}}function Nt(){const e=Z("glv-history-table-wrap"),n=Z("glv-history-empty"),a=Z("glv-history-tbody"),o=Z("glv-history-pager"),s=Z("glv-history-pager-info"),i=Z("glv-history-prev"),r=Z("glv-history-next");if(!a)return;if(a.innerHTML="",!Ze.length){e&&(e.style.display="none"),n&&(n.style.display=""),o&&(o.style.display="none");return}e&&(e.style.display=""),n&&(n.style.display="none");const c=Math.ceil(Ze.length/gt);_e>c&&(_e=c);const l=(_e-1)*gt,p=Ze.slice(l,l+gt);o&&(o.style.display=Ze.length>gt?"":"none",s&&(s.textContent=_e+" / "+c),i&&(i.disabled=_e<=1),r&&(r.disabled=_e>=c)),p.forEach(d=>{const u=document.createElement("tr");u.dataset.taskId=d.id;const m=document.createElement("td");m.textContent=Zi(d.created_at);const h=document.createElement("td");h.className="glv-history-file",h.title=(d.vat_filename||"")+" + "+(d.gl_filename||""),h.textContent=(d.vat_filename||"?")+" + "+(d.gl_filename||"?");const _=document.createElement("td");_.className="glv-num",_.textContent=(d.vat_row_count||0)+" / "+(d.gl_row_count||0);const y=document.createElement("td");y.className="glv-num",y.textContent=d.matched_count||0;const b=document.createElement("td");b.className="glv-num",b.textContent=d.diff_count||0;const v=document.createElement("td");v.className="glv-num",v.textContent=d.unmatched_count||0;const L=document.createElement("td");L.className="glv-history-actions";const g=(w,I,M,S)=>{const C=document.createElement("button");return C.type="button",M&&(C.className=M),C.title=I,C.setAttribute("aria-label",I),C.innerHTML=w,C.onclick=S,C},x='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',B='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',E='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';L.appendChild(g(x,ue("hist_load"),"",()=>tr(d.id))),L.appendChild(g(B,ue("hist_export"),"",()=>ir(d.id))),L.appendChild(g(E,ue("hist_delete"),"glv-del",()=>rr(d.id))),[m,h,_,y,b,v,L].forEach(w=>u.appendChild(w)),a.appendChild(u)})}function sr(){var e=Z("glv-history-prev"),n=Z("glv-history-next");e&&!e._glvBound&&(e._glvBound=!0,e.addEventListener("click",function(){_e>1&&(_e--,Nt())})),n&&!n._glvBound&&(n._glvBound=!0,n.addEventListener("click",function(){var a=Math.ceil(Ze.length/gt);_e<a&&(_e++,Nt())}))}async function nt(){try{const n=await(await fetch("/api/recon/gl-vat/tasks",{headers:Je()})).json();Ze=n&&n.tasks||[],_e=1,Nt(),sr()}catch(e){console.error("[gl-vat] history load failed:",e)}}async function ir(e){try{const n="/api/recon/gl-vat/"+e+"/export?lang="+encodeURIComponent(lt()),a=await fetch(n,{headers:Je()});if(!a.ok)throw new Error("HTTP "+a.status);const o=await a.blob(),s=document.createElement("a");s.href=URL.createObjectURL(o),s.download="GL_VAT_recon_"+e+".xlsx",document.body.appendChild(s),s.click(),setTimeout(()=>{URL.revokeObjectURL(s.href),s.remove()},200)}catch(n){console.error("[gl-vat] exportTask failed:",n),typeof showToast=="function"&&showToast(ue("error")+": "+(n.message||n),"error")}}async function rr(e){let n;if(typeof window.showConfirm=="function"?n=await window.showConfirm(ue("confirm_delete"),{danger:!0}):n=confirm(ue("confirm_delete")),!!n)try{const a=await fetch("/api/recon/gl-vat/"+e,{method:"DELETE",headers:Je()});if(!a.ok)throw new Error("HTTP "+a.status);nt()}catch(a){console.error("[gl-vat] delete failed:",a),typeof showToast=="function"&&showToast(ue("error")+": "+(a.message||a),"error")}}async function lr(){if(!ae.glFile||!ae.vatFile){typeof showToast=="function"&&showToast(ue("need_files"),"warn");return}ae.running=!0,St();const e=Z("glv-status"),n=Z("glv-progress"),a=Z("glv-progress-sub");e&&(e.className="vex-action-info muted",e.style.color="",e.innerHTML="<span>"+ue("running")+"</span>"),n&&(n.style.display=""),a&&(a.textContent=(ae.vatFile.name||"VAT")+" + "+(ae.glFile.name||"GL"));const o=new FormData,s=qe("vatFile"),i=qe("glFile");for(const c of s)o.append("vat_files",c,c.name);for(const c of i)o.append("gl_files",c,c.name);const r=(Z("glv-prefix")&&Z("glv-prefix").value||"4").trim()||"4";o.append("revenue_prefix",r),o.append("lang",lt());try{const c=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:Je(),body:o});let l=null;try{l=await c.json()}catch{l=null}if(!c.ok||!l||!l.ok||!l.job_id)throw new Error(l&&l.detail||l&&l.error||"HTTP "+c.status);const p=Z("glv-progress-sub"),f=await window._reconPollJob(l.job_id,Xa(),{onProgress:h=>{p&&(p.textContent=window._reconProgressText(h,lt()))}});if(!f||f.status!=="done"||!f.result_id)throw f&&f.status==="failed"&&f.error_code?new Error(Xi(f.error_code)):new Error(ue("error")||"Error");const d=await fetch("/api/recon/gl-vat/"+encodeURIComponent(f.result_id),{headers:Je()});let u=null;try{u=await d.json()}catch{u=null}if(!d.ok||!u||!u.ok)throw new Error(u&&u.detail||u&&u.error||"HTTP "+d.status);ae.currentTaskId=u.task_id,ae.lastDetail=u.detail||[],ae.lastSummary=u.summary||{},Dn(u.stats||{}),qn(ae.lastDetail),Rn(ae.lastSummary);const m=Z("glv-result");m&&(m.style.display=""),Qa(),e&&(e.className="vex-action-info ok",e.style.color="",e.innerHTML="<span>"+ue("done")+" · GL "+(u.gl_row_count||0)+" · VAT "+(u.vat_row_count||0)+"</span>"),nt()}catch(c){console.error("[gl-vat] run failed:",c),e&&(e.className="vex-action-info",e.style.color="#ef4444",e.innerHTML="<span>"+ue("error")+": "+(c.message||c)+"</span>")}finally{ae.running=!1,n&&(n.style.display="none"),St()}}async function cr(){if(ae.currentTaskId)try{const e="/api/recon/gl-vat/"+ae.currentTaskId+"/export?lang="+encodeURIComponent(lt()),n=await fetch(e,{headers:Je()});if(!n.ok)throw new Error("HTTP "+n.status);const a=await n.blob(),o=document.createElement("a");o.href=URL.createObjectURL(a),o.download="GL_VAT_recon_"+ae.currentTaskId+".xlsx",document.body.appendChild(o),o.click(),setTimeout(()=>{URL.revokeObjectURL(o.href),o.remove()},200)}catch(e){console.error("[gl-vat] export failed:",e),typeof showToast=="function"&&showToast(ue("error")+": "+(e.message||e),"error")}}function dr(){ae.running||Mt(),nt(),ae.lastDetail&&ae.lastDetail.length&&qn(ae.lastDetail),ae.lastSummary&&Rn(ae.lastSummary)}function pr(){if(ae.inited){nt();return}ae.inited=!0,ia("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),ia("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const e=Z("btn-glv-run");e&&e.addEventListener("click",lr);const n=Z("btn-glv-export");n&&n.addEventListener("click",cr);const a=Z("btn-glv-reset");a&&a.addEventListener("click",er);const o=Z("glv-hist-search");o&&o.addEventListener("input",or),nr(),Dn(null),Mt(),window._loadGlvHistory=nt,nt(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",dr)}window._glvRemoveFile=Qi;window.GlVatRecon={ensureInit:pr};window._glvPreviewFiles=function(e){return qe(e==="vat"?"vatFile":"glFile")};(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let i={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function r(){const S=typeof _userInfo<"u"?_userInfo:null;return!!(S&&(S.role==="owner"||S.is_super_admin))}function c(){const S=typeof _userInfo<"u"?_userInfo:null;return!!(S&&S.id===s)}function l(S){return typeof escapeHtml=="function"?escapeHtml(S==null?"":String(S)):String(S??"")}function p(S,C){try{typeof showToast=="function"&&showToast(S,C||"info")}catch{}}async function f(S,C){const k=localStorage.getItem("mrpilot_token");if(k&&!(i.loaded[S]&&!C))try{const T=await fetch("/api/erp/mappings/"+S,{headers:{Authorization:"Bearer "+k}});if(!T.ok)throw new Error("http_"+T.status);const $=await T.json();i.items[S]=$.items||[],i.loaded[S]=!0}catch{i.items[S]=[],i.loaded[S]=!1}}async function d(S){if(i.clientLoaded)return;const C=localStorage.getItem("mrpilot_token");if(C)try{const k=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+C}});if(!k.ok)throw new Error("http_"+k.status);const T=await k.json();i.clientList=(T.clients||T.items||[]).filter($=>$.is_active!==!1),i.clientLoaded=!0}catch{i.clientList=[]}}function u(){const S=document.getElementById("erp-map-pane-wrap");if(!S)return;const C=!r();let k="";C&&(k+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+l(t("erp-map-readonly-tip"))+"</div>"),k+='<div class="erp-map-toolbar">',!C&&i.sub!=="products"&&(k+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+l(t("erp-map-add-row"))+"</button>"),k+="</div>",k+='<div class="erp-map-table" id="erp-map-table-host"></div>',S.innerHTML=k,m();const T=document.getElementById("erp-map-dev-bar");T&&(T.style.display=r()&&c()?"":"none")}function m(){const S=document.getElementById("erp-map-table-host");if(!S)return;const C=i.sub,k=i.items[C]||[],T=i.addingNew[C],$=!r();if(!k.length&&!T){S.innerHTML='<div class="erp-map-empty"><strong>'+l(t("erp-map-empty-"+C))+"</strong>"+l(t("erp-map-empty-"+C+"-sub"))+"</div>";return}let A="";A+=h(C),T&&!$&&(A+=L(C)),k.forEach(function(H){A+=g(C,H,$)}),S.innerHTML=A}function h(S){return S==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+l(t("erp-map-col-client"))+"</div><div>"+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":S==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-category"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":S==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+l(t("erp-map-col-item-name"))+"</div><div>"+l(t("erp-map-col-erp-product-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-tax"))+"</div><div>"+l(t("erp-map-col-erp-tax-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>"}function _(S,C){let k='<select class="form-input" data-erp-field="'+C+'">';return k+='<option value="">'+l(t("erp-map-pick-erp"))+"</option>",e.forEach(function(T){const $=T===S?" selected":"";k+='<option value="'+T+'"'+$+">"+l(n[T])+"</option>"}),k+="</select>",k}function y(S){let C='<select class="form-input" data-erp-field="client_id">';return C+='<option value="">'+l(t("erp-map-pick-client"))+"</option>",(i.clientList||[]).forEach(function(k){const T=String(k.id)===String(S)?" selected":"";C+='<option value="'+k.id+'"'+T+">"+l(k.name||"#"+k.id)+"</option>"}),C+="</select>",C}function b(S){let C='<select class="form-input" data-erp-field="pearnly_category">';return C+='<option value="">'+l(t("erp-map-pick-cat"))+"</option>",a.forEach(function(k){const T=k===S?" selected":"";C+='<option value="'+k+'"'+T+">"+l(t("erp-map-cat-"+k))+"</option>"}),C+="</select>",C}function v(S){let C='<select class="form-input" data-erp-field="pearnly_tax_kind">';return C+='<option value="">'+l(t("erp-map-pick-tax"))+"</option>",o.forEach(function(k){const T=k===S?" selected":"";C+='<option value="'+k+'"'+T+">"+l(t("erp-map-tax-"+k))+"</option>"}),C+="</select>",C}function L(S){const C='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+l(t("erp-map-save"))+"</button>";return S==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+l(t("erp-map-col-client"))+'">'+y("")+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+_("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+C+"</div></div>":S==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+_("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-category"))+'">'+b("")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+l(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+l(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+C+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+_("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-tax"))+'">'+v("")+'</div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+C+"</div></div>"}function g(S,C,k){const T=k?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+l(C.id)+'" title="'+l(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',$='<span class="erp-map-erp-badge">'+l(n[C.erp_type]||C.erp_type)+"</span>";if(S==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+l(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+l(C.client_name||"#"+C.client_id)+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+$+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(C.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(C.notes||"")+"</div><div>"+T+"</div></div>";if(S==="accounts"){const H=t("erp-map-cat-"+(C.pearnly_category||"other"))||C.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+l(t("erp-map-col-erp"))+'">'+$+'</div><div data-label="'+l(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+l(H)+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(C.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(C.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(C.notes||"")+"</div><div>"+T+"</div></div>"}if(S==="products")return'<div class="erp-map-row row-products"><div data-label="'+l(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+l(C.item_name||"")+'</div><div data-label="'+l(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+l(C.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(C.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(C.notes||"")+"</div><div>"+T+"</div></div>";const A=t("erp-map-tax-"+(C.pearnly_tax_kind||""))||C.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+l(t("erp-map-col-erp"))+'">'+$+'</div><div data-label="'+l(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+l(A)+'</span></div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+l(C.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(C.notes||"")+"</div><div>"+T+"</div></div>"}async function x(S){const C=i.sub,k={};S.querySelectorAll("[data-erp-field]").forEach(function(H){k[H.dataset.erpField]=(H.value||"").trim()});const T=localStorage.getItem("mrpilot_token");if(!T)return;let $={},A="/api/erp/mappings/"+C;if(C==="clients"){if(!k.client_id||!k.erp_type||!k.erp_code){p(t("erp-map-save-fail"),"error");return}$={client_id:parseInt(k.client_id,10),erp_type:k.erp_type,erp_code:k.erp_code,notes:k.notes||""}}else if(C==="accounts"){if(!k.erp_type||!k.pearnly_category||!k.erp_code){p(t("erp-map-save-fail"),"error");return}$={erp_type:k.erp_type,pearnly_category:k.pearnly_category,erp_code:k.erp_code,erp_name:k.erp_name||"",notes:k.notes||""}}else{if(!k.erp_type||!k.pearnly_tax_kind||!k.erp_code){p(t("erp-map-save-fail"),"error");return}$={erp_type:k.erp_type,pearnly_tax_kind:k.pearnly_tax_kind,erp_code:k.erp_code,notes:k.notes||""}}try{const H=await fetch(A,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+T},body:JSON.stringify($)});if(!H.ok)throw new Error("http_"+H.status);i.addingNew[C]=!1,await f(C,!0),m(),p(t("erp-map-saved-toast"),"success")}catch{p(t("erp-map-save-fail"),"error")}}async function B(S){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const k=i.sub,T=localStorage.getItem("mrpilot_token");try{const $=await fetch("/api/erp/mappings/"+k+"/"+encodeURIComponent(S),{method:"DELETE",headers:{Authorization:"Bearer "+T}});if(!$.ok)throw new Error("http_"+$.status);await f(k,!0),m(),p(t("erp-map-deleted-toast"),"success")}catch{p(t("erp-map-delete-fail"),"error")}}async function E(){await d(),await f(i.sub,!1),u()}function w(S){S!==i.sub&&(i.sub=S,i.addingNew[S]=!1,["clients","accounts","taxes","products"].forEach(function(C){C!==S&&(i.addingNew[C]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(C){C.classList.toggle("active",C.dataset.erpSubtab===S)}),f(S,!1).then(function(){u()}))}function I(){i.bound||(i.bound=!0,document.addEventListener("click",function(S){const C=S.target.closest(".erp-subtab[data-erp-subtab]");if(C){S.preventDefault();const H=C.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(P){P.classList.toggle("active",P.dataset.erpSubtab===H)}),document.querySelectorAll(".erp-subpanel").forEach(function(P){P.classList.toggle("active",P.dataset.erpSubpanel===H)}),H==="mappings"&&setTimeout(E,50);return}const k=S.target.closest(".erp-map-subtab[data-erp-subtab]");if(k){S.preventDefault(),w(k.dataset.erpSubtab);return}if(S.target.closest("#erp-map-add-btn")){if(S.preventDefault(),!r())return;i.addingNew[i.sub]=!0,m();return}const $=S.target.closest('[data-erp-save="new"]');if($){S.preventDefault();const H=$.closest('[data-erp-row="new"]');H&&x(H);return}const A=S.target.closest("[data-erp-del]");if(A){S.preventDefault(),B(A.dataset.erpDel);return}}))}function M(){const S=document.getElementById("erp-map-pane-wrap");S&&S.children.length>0&&u(),document.querySelectorAll(".erp-map-subtab").forEach(function(C){const k="erp-map-subtab-"+C.dataset.erpSubtab,T=t(k);T&&T!==k&&(C.textContent=T)})}I(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",M)})();(function(){let e=null,n=0,a=!1;function o(E){return typeof escapeHtml=="function"?escapeHtml(E==null?"":String(E)):String(E??"")}function s(E,w){try{typeof showToast=="function"&&showToast(E,w||"info")}catch{}}async function i(E){const w=Date.now();if(e&&w-n<3e4)return e;const I=localStorage.getItem("mrpilot_token");if(!I)return[];try{const M=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+I}});if(!M.ok)return[];const S=await M.json();return e=S&&S.connectors||[],n=w,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function c(E){try{localStorage.setItem("pn_push_default_connector",E||"")}catch{}}function l(E){if(!E||!E.length)return null;const w=r();if(w){const M=E.find(S=>S.id===w);if(M)return M}const I=E.find(M=>M.is_default);return I||E[0]}function p(E){if(!E)return!1;const w=String(E.status||"").toLowerCase();return w==="exception"||w==="exception_pending"||w==="rejected"}function f(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function d(E){const w=E&&(E.type||E.id);return w==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':w==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function u(E,w){if(!E||!w)return!1;const I=document.getElementById("btn-push-default");I&&(I.disabled=!0,I.classList.add("loading"));const M=localStorage.getItem("mrpilot_token");try{let S,C={method:"POST",headers:{Authorization:"Bearer "+M}};E.type==="xero"?S="/api/erp/xero/push/"+encodeURIComponent(w):(S="/api/erp/push",C.headers["Content-Type"]="application/json",C.body=JSON.stringify({history_id:w,endpoint_id:E.endpoint_id||void 0}));const k=await fetch(S,C);let T={};try{T=await k.json()}catch{}if(!k.ok){let $=T&&T.detail||"unknown";typeof $=="object"&&($=$.code||JSON.stringify($));let A=String($||"unknown");if(E.type==="xero"){const H=A.replace(/^xero\./,"").toLowerCase(),P=t("xero-"+H);P&&P!=="xero-"+H&&(A=P)}return s(t("unified-push-fail").replace("{name}",E.name).replace("{err}",A),"error"),!1}if(T&&T.ok===!1){let $=T.error_msg||T.error_code||"unknown";return $=String($).slice(0,200),s(t("unified-push-fail").replace("{name}",E.name).replace("{err}",$),"error"),!1}return s(t("unified-push-ok").replace("{name}",E.name),"success"),!0}catch(S){return s(t("unified-push-fail").replace("{name}",E.name).replace("{err}",S.message||"network"),"error"),!1}finally{I&&(I.disabled=!1,I.classList.remove("loading"))}}async function m(E,w){for(const I of E)await u(I,w)}function h(E,w){const I=document.createElement("div");I.className="pn-push-dropdown",I.id="pn-push-dropdown";const M=(E||[]).map(C=>{const k=!!(w&&C.id===w.id),T=C.method==="download"?t("unified-push-tag-download"):k?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(C.id)+'"><span class="pn-pd-icon">'+d(C)+'</span><span class="pn-pd-name">'+o(C.name)+"</span>"+(T?'<span class="pn-pd-tag">'+o(T)+"</span>":"")+(k?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),S=E&&E.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",E.length))+"</span></div>":"";return I.innerHTML=M+S,I}function _(){const E=document.getElementById("pn-push-dropdown");E&&E.remove()}async function y(){if(document.getElementById("pn-push-dropdown")){_();return}const E=await i()||[],w=l(E),I=h(E,w),M=document.getElementById("pn-push-wrap");M&&M.appendChild(I)}async function b(){const E=await i()||[],w=l(E);if(!w)return;const I=f(),M=I&&(I._historyId||I.history_id);if(M){if(p(I)){s(t("unified-push-disabled-exc"),"warn");return}await u(w,M)}}async function v(E){_();const w=await i()||[],I=f(),M=I&&(I._historyId||I.history_id);if(!M)return;if(p(I)){s(t("unified-push-disabled-exc"),"warn");return}if(E==="__all__"){await m(w,M);return}const S=w.find(C=>C.id===E);S&&(c(E),await u(S,M),g())}async function L(){const E=document.getElementById("drawer-history-save");if(!E||E.querySelector("#pn-push-wrap"))return;const w=document.createElement("div");w.id="pn-push-wrap",w.className="pn-push-wrap",w.dataset.loading="1",E.insertBefore(w,E.firstChild),["btn-push-erp","btn-xero-push"].forEach(T=>{E.querySelectorAll("#"+T).forEach($=>{$.style.display="none"})});const I=await i()||[],M=l(I),S=I.length>0;if(!S)w.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const T=I.length>1;w.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+d(M)+"<span>"+o(t("unified-push-to").replace("{name}",M?M.name:""))+"</span></button>"+(T?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete w.dataset.loading;const C=w.querySelector("#btn-push-default");C&&S&&C.addEventListener("click",b);const k=w.querySelector("#btn-push-arrow");k&&k.addEventListener("click",function(T){T.stopPropagation(),y()}),a||(a=!0,document.addEventListener("click",function(T){const $=T.target.closest(".pn-pd-item");if($){const A=$.getAttribute("data-cid");v(A);return}T.target.closest("#btn-push-arrow")||_()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",g))}function g(){const E=document.getElementById("pn-push-wrap");E&&(E.remove(),e=null,n=0,L())}function x(){const E=document.getElementById("drawer-history-save");if(!E||!E.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(I=>{E.querySelectorAll("#"+I).forEach(M=>{M.style.display!=="none"&&(M.style.display="none")})});const w=E.querySelectorAll("#pn-push-wrap");if(w.length>1)for(let I=1;I<w.length;I++)w[I].remove()}function B(){try{const E=function(){return document.getElementById("drawer-body")},w=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&L(),x()}),I=E();if(I)w.observe(I,{childList:!0,subtree:!0});else{const M=new MutationObserver(function(){const S=E();S&&(w.observe(S,{childList:!0,subtree:!0}),M.disconnect())});M.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&L(),x()},200)}catch{}}B()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",c=t(r);c&&c!==r&&(i.textContent=c)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const l=document.getElementById("erp-onboard-title"),p=document.getElementById("erp-onboard-body"),f=document.getElementById("erp-onboard-ok"),d=document.getElementById("erp-onboard-later");l&&(l.textContent=t("erp-onboard-title")),p&&(p.textContent=t("erp-onboard-body")),f&&(f.textContent=t("erp-onboard-ok")),d&&(d.textContent=t("erp-onboard-later"))}r();function c(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}c();try{const l=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');l&&l.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}c()}),i.addEventListener("click",function(l){l.target===i&&c()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),c=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||c)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,i=s[a]||s.th||s.en,r=n.stage_total,c=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const l={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+l.replace("{d}",c||0).replace("{t}",r)}return i},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,i=o.maxMs||1200*1e3,r=Date.now();let c=0;for(;;){let l=null;try{const p=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{l=await p.json()}catch{l=null}(!p.ok||!l||!l.ok)&&(l=null)}catch{l=null}if(l){if(c=0,o.onProgress)try{o.onProgress(l.progress||{},l)}catch{}if(l.status==="done"||l.status==="failed"||l.status==="needs_review"||l.status==="needs_mapping")return l}else if(++c>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(p=>setTimeout(p,s))}}})();const U={initialized:!1,stmtFiles:[],glFiles:[],currentTask:null,currentFilter:"all",allRows:[],brv2Search:{stmt:"",gl:""},cachedHistoryTasks:[],brv2Page:1},O=e=>document.getElementById(e);function Pe(e){if(e==null)return"—";const n=Number(e);return isNaN(n)?"—":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function ra(e){return e?String(e).slice(0,10).split("-").reverse().join("/"):"—"}function ve(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function ur(e,n){n=window._currentLang||n||"th";const a={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},o={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},s=a[e]||o;return s[n]||s.th||s.en}function fr(e){return e?e<1024?e+" B":e<1048576?(e/1024).toFixed(1)+" KB":(e/1048576).toFixed(1)+" MB":""}function Ye(e,n){return window.t&&window.t(e)||n}function He(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function on(e){return Number.isFinite(+e)?(+e).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}var eo="pearnly.brv2.lastAnchorOcr";function mr(e){try{var n=e&&e._anchor_ocr;if(!n||typeof n!="object")return;var a={stmt_opening:Number.isFinite(+n.stmt_opening)?+n.stmt_opening:null,gl_opening:Number.isFinite(+n.gl_opening)?+n.gl_opening:null,gl_closing:Number.isFinite(+n.gl_closing)?+n.gl_closing:null,stmt_closing:Number.isFinite(+n.stmt_closing)?+n.stmt_closing:null,ts:Date.now()};localStorage.setItem(eo,JSON.stringify(a))}catch{}}function vr(){try{var e=localStorage.getItem(eo);if(!e)return null;var n=JSON.parse(e);return!n||typeof n!="object"?null:n}catch{return null}}function hr(){var e=vr();if(e){var n={"brv2-anchor-stmt-opening":e.stmt_opening,"brv2-anchor-gl-opening":e.gl_opening,"brv2-anchor-gl-closing":e.gl_closing,"brv2-anchor-stmt-closing":e.stmt_closing},a=0;Object.keys(n).forEach(function(c){var l=document.getElementById(c);if(l&&l.value===""){var p=n[c];if(Number.isFinite(p)){l.value=p.toFixed(2);var f=l.closest&&l.closest(".brv2-anchor-cell");f&&f.classList.add("is-prefilled"),a+=1}}});var o=document.getElementById("brv2-anchor-eq"),s=document.getElementById("brv2-anchor-eq-val");if(o&&s&&Number.isFinite(e.stmt_opening)&&Number.isFinite(e.gl_opening)){var i=e.stmt_opening-e.gl_opening;s.textContent=i.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),o.style.display=""}if(a>0){var r=document.getElementById("brv2-anchor-prefill-banner");r&&r.classList.add("show")}}}function gr(){var e=document.getElementById("brv2-anchor-prefill-banner");if(e){var n=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(a){var o=document.getElementById(a);if(o){var s=o.closest&&o.closest(".brv2-anchor-cell");s&&s.classList.contains("is-prefilled")&&(n=!0)}}),e.classList.toggle("show",n)}}var br=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function yr(e){var n=document.getElementById("brv2-summary-collapse");if(!(!n||!n.parentNode)){var a=document.getElementById("brv2-anchor-audit"),o=e&&e._anchor_overrides;if(!o||typeof o!="object"||Object.keys(o).length===0){a&&a.parentNode&&a.parentNode.removeChild(a);return}a||(a=document.createElement("div"),a.id="brv2-anchor-audit",a.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",n.parentNode.insertBefore(a,n.nextSibling));var s=br.map(function(i){var r=o[i[0]];if(!r)return"";var c=+r.ocr||0,l=+r.user||0,p=l-c,f=p>0?"+":(p<0,""),d=Math.abs(p)<.005?"#6b7280":p>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+He(Ye(i[1],i[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+He(on(c))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+He(on(l))+'</td><td style="padding:6px 10px;color:'+d+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+He(f+on(p))+"</td></tr>"}).join("");a.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+He(Ye("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+He(Ye("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+He(Ye("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+He(Ye("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+He(Ye("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+s+"</tbody></table>"}}function Ot(e){const n=O("brv2-summary-collapse"),a=O("brv2-detail-collapse"),o=O("brv2-export-btn"),s=O("brv2-new-btn"),i=O("brv2-parse-info-wrap");n&&(n.style.display=e?"":"none"),a&&(a.style.display=e?"":"none"),o&&(o.style.display=e?"":"none"),s&&(s.style.display=e?"":"none"),!e&&i&&(i.style.display="none");const r=O("brv2-warnings");!e&&r&&(r.style.display="none",r.innerHTML="")}function wr(e){const n=O("brv2-parse-info-wrap"),a=O("brv2-parse-info-body");if(!n||!a)return;const o=e.parse_info;if(!o){n.style.display="none";return}const s=window._currentLang||"zh",i={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},r=u=>(i[u]||{})[s]||(i[u]||{}).zh||u,c=[...(o.stmt_files||[]).map(u=>({...u,_type:"stmt",_extra:u.bank_code||""})),...(o.gl_files||[]).map(u=>({...u,_type:"gl",_extra:(u.accounts||[]).join(", ")}))],l={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},p=u=>{const m=String(u||"");return/Cannot detect bank statement column headers/i.test(m)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(m)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(m)?"stmt_no_rows":/unsupported format/i.test(m)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(m)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(m)?"ocr_failed":null},f=u=>{const m=u.error_code||p(u.error);if(m&&l[m]){const h=window._currentLang||"zh";return l[m][h]||l[m].zh}return String(u.error||"").slice(0,80)},d=u=>!u.ok&&u.error?`<span style="color:#dc2626">${r("fail")} — ${ve(f(u))}</span>`:u.rows?`<span style="color:#059669">${r("ok")} (${u.rows})</span>`:`<span style="color:#d97706">${r("warn")}</span>`;a.innerHTML=`
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
                ${c.map(u=>`<tr>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${u._type==="stmt"?r("stmt"):r("gl")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${ve(u.file||"")}">${ve(u.file||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${u.rows||0}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${ve(u._extra||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb">${d(u)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`,n.style.display=""}async function to(e){const n=localStorage.getItem("mrpilot_token")||"",a=window._currentLang||"zh";try{const o=await fetch("/api/recon/bank-v2/"+e+"/export?lang="+a,{headers:{Authorization:"Bearer "+n}});if(!o.ok){const f=await o.json().catch(()=>({}));window.showToast&&window.showToast(f.detail||"Export failed","error");return}const s=await o.blob(),r=(o.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),c=r?r[1].replace(/['"]/g,""):"reconciliation.xlsx",l=URL.createObjectURL(s),p=document.createElement("a");p.href=l,p.download=c,document.body.appendChild(p),p.click(),document.body.removeChild(p),URL.revokeObjectURL(l)}catch(o){window.showToast&&window.showToast("Export error: "+o.message,"error")}}function kr(e,n){const a=O("brv2-summary-collapse");let o=O("brv2-warnings");const s=window._currentLang||"zh",i={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[s]||"⏭ ",r=[];if((n||[]).forEach(c=>r.push(i+" "+c)),(e||[]).forEach(c=>r.push(c)),!r.length){o&&(o.style.display="none");return}if(!o)if(o=document.createElement("div"),o.id="brv2-warnings",a&&a.parentNode)a.parentNode.insertBefore(o,a);else return;o.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",o.innerHTML=r.map(c=>"<div>"+ve(c)+"</div>").join("")}function Fn(e){wr(e),kr(e.warnings||[],e.skipped_files||[]),!e.ok&&e.error&&window.showToast&&window.showToast(e.error,"error");const n=e.stats||{},a=e.summary||{},o=n.matched||0,s=(n.gl_debit_only||0)+(n.gl_credit_only||0),i=(n.stmt_withdrawal_only||0)+(n.stmt_deposit_only||0),r=Number(a.formula_diff||0),c=Math.abs(r)<.05;O("brv2-kpi-matched")&&(O("brv2-kpi-matched").textContent=o),O("brv2-kpi-diff")&&(O("brv2-kpi-diff").textContent=Pe(r)),O("brv2-kpi-unmatched")&&(O("brv2-kpi-unmatched").textContent=s+i);const l=O("brv2-kpi-diff-icon");l&&(l.style.background=c?"#d1fae5":"#fee2e2",l.style.color=c?"#065f46":"#b91c1c");const p=O("brv2-formula-sub");if(p){const h=window._currentLang||"zh";p.textContent=c?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[h]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[h]||"差 ")+Pe(r)}const f=O("brv2-detail-sub");if(f){const h=window._currentLang||"zh",_={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[h]||"共 {n} 行";f.textContent=_.replace("{n}",U.allRows.length)}function d(h,_,y){const b=O(h);b&&(b.textContent=(y&&_>0?"(":"")+Pe(y?-_:_)+(y&&_>0?")":""))}d("brf-gl-close",a.gl_closing||0),d("brf-open-diff",a.opening_diff||0),d("brf-gl-debit-only",a.gl_debit_only_amount||0,!0),d("brf-gl-credit-only",a.gl_credit_only_amount||0),d("brf-stmt-wd-only",a.stmt_withdrawal_only_amount||0,!0),d("brf-stmt-dep-only",a.stmt_deposit_only_amount||0),d("brf-calc-close",a.formula_stmt_closing||0),d("brf-stmt-close",a.stmt_closing||0),O("brf-diff")&&(O("brf-diff").textContent=Pe(r));const u=O("brv2-fcell-diff");u&&u.classList.toggle("brv2-fcell-diff-ok",c);const m=O("brv2-export-btn");m&&(m.onclick=()=>{U.currentTask&&to(U.currentTask.task_id)}),yr(a),Ot(!0),no()}function no(){const e=O("brv2-tbody");if(!e)return;const n=U.allRows.filter(i=>U.currentFilter==="all"?!0:U.currentFilter==="matched"?i.match_status==="matched":U.currentFilter==="gl_only"?i.match_status.startsWith("gl_"):U.currentFilter==="stmt_only"?i.match_status.startsWith("stmt_"):!0);if(n.length===0){const i={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";e.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${i}</td></tr>`;return}const a=window._currentLang||"zh",o={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[a],s={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[a];e.innerHTML=n.map(i=>{const r=i.match_status,c=i.match_layer;let l="",p="";r==="matched"?(c===1&&(l="matched",p='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),c===2&&(l="matched-l2",p='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),c===3&&(l="matched-l3",p='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):r==="gl_debit_only"||r==="gl_credit_only"?(l="gl-only",p='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(l="stmt-only",p=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[a]||"账单"}</span>`);let f="";return i.stmt_balance_ok===!1&&(f+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${ve(o)}">⚠</span>`,l+=" brv2-row-warn"),i.stmt_confidence==="low"&&(f+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${ve(s)}">◌</span>`,l.includes("brv2-row-warn")||(l+=" brv2-row-warn-soft")),`<tr class="${l.trim()}">
          <td>${p}${f}</td>
          <td>${ve(ra(i.stmt_date))}</td>
          <td title="${ve(i.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${ve(i.stmt_desc)}</td>
          <td class="num">${i.stmt_withdrawal?Pe(i.stmt_withdrawal):""}</td>
          <td class="num">${i.stmt_deposit?Pe(i.stmt_deposit):""}</td>
          <td>${ve(ra(i.gl_date))}</td>
          <td title="${ve(i.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${ve(i.gl_doc_no)}</td>
          <td class="num">${i.gl_debit?Pe(i.gl_debit):""}</td>
          <td class="num">${i.gl_credit?Pe(i.gl_credit):""}</td>
          <td>${c?"L"+c:"—"}</td>
        </tr>`}).join("")}async function Bt(){const e=localStorage.getItem("mrpilot_token")||"";try{const a=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+e}})).json();Vt(a.tasks||[])}catch{const a=O("brv2-history-empty"),o=window._currentLang||"zh",s={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[o]||"加载失败";a&&(a.textContent=s,a.style.display="");const i=O("brv2-history-table-wrap");i&&(i.style.display="none")}}const at=10;function la(){const e=O("brv2-history-pager"),n=O("brv2-history-pager-info"),a=O("brv2-history-prev"),o=O("brv2-history-next");if(!e)return;if(U.cachedHistoryTasks.length<=at){e.style.display="none";return}e.style.display="";const s=Math.ceil(U.cachedHistoryTasks.length/at);n&&(n.textContent=U.brv2Page+" / "+s),a&&(a.disabled=U.brv2Page<=1),o&&(o.disabled=U.brv2Page>=s)}function xr(){const e=O("brv2-history-prev"),n=O("brv2-history-next");e&&!e._brv2Bound&&(e._brv2Bound=!0,e.addEventListener("click",()=>{U.brv2Page>1&&(U.brv2Page--,Vt(U.cachedHistoryTasks))})),n&&!n._brv2Bound&&(n._brv2Bound=!0,n.addEventListener("click",()=>{const a=Math.ceil(U.cachedHistoryTasks.length/at);U.brv2Page<a&&(U.brv2Page++,Vt(U.cachedHistoryTasks))}))}function Vt(e){e!==void 0&&(U.cachedHistoryTasks=e||[],U.brv2Page=1);const n=U.cachedHistoryTasks,a=O("brv2-history-empty"),o=O("brv2-history-table-wrap"),s=O("brv2-history-tbody");if(!s)return;const i=window._currentLang||"zh";if(!n.length){const m={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[i]||"暂无对账记录";a&&(a.textContent=m,a.style.display=""),o&&(o.style.display="none"),la();return}a&&(a.style.display="none"),o&&(o.style.display="");const r=Math.ceil(n.length/at);U.brv2Page>r&&(U.brv2Page=r);const c=(U.brv2Page-1)*at,l=n.slice(c,c+at),p=localStorage.getItem("mrpilot_token")||"",f='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',d='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',u='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';s.innerHTML="",l.forEach(m=>{const h=Number(m.formula_diff||0),_=Math.abs(h)<.05,y=(m.stmt_files||"").split(";").map(H=>H.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),b=(m.gl_files||"").split(";").map(H=>H.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),v=m.created_at?String(m.created_at).slice(0,16).replace("T"," "):"",L=document.createElement("tr");L.dataset.taskId=m.id;const g=document.createElement("td");g.textContent=v;const x=document.createElement("td");x.className="glv-history-file",x.title=y+" + "+b,x.textContent=y+" + "+b;const B=document.createElement("td");B.className="glv-num",B.textContent=(m.stmt_row_count||0)+" / "+(m.gl_row_count||0);const E=document.createElement("td");E.className="glv-num",E.textContent=m.matched_count||0;const w=document.createElement("td");w.className="glv-num",w.textContent=m.unmatched_gl||0;const I=document.createElement("td");I.className="glv-num",I.textContent=m.unmatched_stmt||0;const M=document.createElement("td");M.className="glv-num",M.style.color=_?"#059669":"#dc2626",M.textContent=_?"✓":Pe(h);const S=document.createElement("td");S.className="glv-history-actions";const C=(H,P,R,D)=>{const j=document.createElement("button");return j.type="button",j.title=P,j.setAttribute("aria-label",P),R&&(j.className=R),j.innerHTML=H,j.onclick=F=>{F.stopPropagation(),D()},j},k={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[i]||"删除?",T={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[i]||"加载",$={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[i]||"导出",A={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[i]||"删除";S.appendChild(C(f,T,"",()=>ca(m.id,p))),S.appendChild(C(d,$,"",()=>to(m.id))),S.appendChild(C(u,A,"glv-del",async()=>{await showConfirm(k,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+m.id,{method:"DELETE",headers:{Authorization:"Bearer "+p}}),Bt())})),[g,x,B,E,w,I,M,S].forEach(H=>L.appendChild(H)),L.style.cursor="pointer",L.addEventListener("click",async H=>{H.target.closest(".glv-del")||H.target.closest("button")||await ca(m.id,p)}),s.appendChild(L)}),la(),ao()}function ao(){const e=((O("brv2-hist-search")||{}).value||"").trim().toLowerCase(),n=O("brv2-history-tbody");n&&n.querySelectorAll("tr").forEach(a=>{a.dataset.taskId&&(a.style.display=!e||a.textContent.toLowerCase().includes(e)?"":"none")})}async function ca(e,n){try{const o=await(await fetch("/api/recon/bank-v2/"+e,{headers:{Authorization:"Bearer "+n}})).json();if(!o.ok)return;U.currentTask={task_id:o.task_id,...o},U.allRows=o.detail||[],U.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(s=>s.classList.toggle("active",s.dataset.filter==="all")),Fn(U.currentTask)}catch{}}function Se(e){const n=e==="stmt"?U.stmtFiles:U.glFiles,a=O(`brv2-${e}-name`);if(a)if(n.length===0)a.textContent="";else{const s=window._currentLang||"zh",i={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};a.textContent=n.length+(i[s]||" 个文件")}const o=O("brv2-preview-panel");o&&o.style.display!=="none"&&fn(e),_r()}function _r(){const e=O("brv2-toggle-preview"),n=O("brv2-preview-panel"),a=U.stmtFiles.length+U.glFiles.length>0;e&&(e.style.display=a?"":"none"),!a&&n&&(n.style.display="none",e&&e.classList.remove("open"))}function Er(){fn("stmt"),fn("gl")}function fn(e){const n=O(e==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!n)return;const a=e==="stmt"?U.stmtFiles:U.glFiles,o=window._currentLang||"zh",s={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},i=(s[e]||{})[o]||s[e].zh,r=ve(window.t&&window.t("vex-preview-search")||"搜索文件名..."),c=ve(window.t&&window.t("vex-preview-clear-all")||"全清"),l=U.brv2Search[e]||"";n.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+ve(i)+' <span class="vex-pp-col-count">'+a.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+e+'" type="text" placeholder="'+r+'" value="'+ve(l)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+e+'" type="button">'+c+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+e+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+e+'-pg"></div>';const p=O("brv2-pp-search-"+e);p&&p.addEventListener("input",function(d){U.brv2Search[e]=d.target.value,da(e)});const f=O("brv2-pp-clearall-"+e);f&&f.addEventListener("click",function(){e==="stmt"?U.stmtFiles.length=0:U.glFiles.length=0,Se(e),De()}),da(e)}function da(e){const n=O("brv2-pp-"+e+"-list"),a=O("brv2-pp-"+e+"-pg");if(!n)return;const o=e==="stmt"?U.stmtFiles:U.glFiles,s=(U.brv2Search[e]||"").toLowerCase(),i=s?o.filter(l=>l.name.toLowerCase().includes(s)):o.slice(),r='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',c='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(n.innerHTML=i.map((l,p)=>'<div class="vex-pp-file-row">'+r+'<span class="vex-pp-fi-name" title="'+ve(l.name)+'">'+ve(l.name)+'</span><span class="vex-pp-fi-size">'+fr(l.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+e+'" data-idx="'+o.indexOf(l)+'" aria-label="remove">'+c+"</button></div>").join(""),n.querySelectorAll(".vex-pp-fi-del").forEach(function(l){l.addEventListener("click",function(){const p=parseInt(l.dataset.idx,10);l.dataset.zone==="stmt"?U.stmtFiles.splice(p,1):U.glFiles.splice(p,1),Se(l.dataset.zone),De()})}),a){const l=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";a.textContent=l.replace("{n}",i.length).replace("{m}",o.length)}}function Br(){const e=O("brv2-toggle-preview");e&&!e._reconBound&&(e._reconBound=!0,e.addEventListener("click",function(){const n=O("brv2-preview-panel"),a=O("brv2-toggle-preview-label"),o=n&&n.style.display!=="none";n&&(n.style.display=o?"none":""),e.classList.toggle("open",!o),a&&(a.textContent=o?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),o||Er()}))}function De(){const e=O("brv2-run-btn"),n=O("brv2-status"),a=U.stmtFiles.length>0,o=U.glFiles.length>0;if(e&&(e.disabled=!(a&&o)),n){const s=window._currentLang||"zh";if(!a&&!o){const i={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};n.textContent=i[s]||i.zh}else if(a)if(o){const i={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};n.textContent=i[s]||i.zh}else{const i={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};n.textContent=i[s]||i.zh}}}function pa(e,n,a){const o=O(e),s=O(n);!o||!s||(o.addEventListener("click",()=>s.click()),o.addEventListener("keydown",i=>{(i.key==="Enter"||i.key===" ")&&(i.preventDefault(),s.click())}),o.addEventListener("dragover",i=>{i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",()=>o.classList.remove("drag-over")),o.addEventListener("drop",i=>{i.preventDefault(),o.classList.remove("drag-over");const r=Array.from(i.dataTransfer.files||[]);a==="stmt"?U.stmtFiles.push(...r):U.glFiles.push(...r),Se(a),De()}),s.addEventListener("change",()=>{const i=Array.from(s.files||[]);a==="stmt"?U.stmtFiles.push(...i):U.glFiles.push(...i),s.value="",Se(a),De()}))}function ke(e){const n=O("brv2-progress"),a=O("brv2-run-btn"),o=O("brv2-error");n&&(n.style.display=e?"":"none"),a&&(a.disabled=e),o&&(o.style.display="none")}function Ce(e){const n=O("brv2-error");n&&(n.textContent=e,n.style.display="",n.scrollIntoView({behavior:"smooth",block:"nearest"})),ke(!1),De(),window.showToast&&window.showToast(e,"error")}async function mn(){if(U.stmtFiles.length===0||U.glFiles.length===0)return;const e=localStorage.getItem("mrpilot_token")||"",n=window._currentLang||"zh",a=(O("brv2-acct-select")||{}).value||"";Ot(!1),ke(!0);try{const o=new FormData;U.stmtFiles.forEach(m=>o.append("stmt_files",m)),U.glFiles.forEach(m=>o.append("gl_files",m)),o.append("gl_account",a),o.append("lang",n);const s=parseFloat((O("brv2-anchor-gl-closing")||{}).value),i=parseFloat((O("brv2-anchor-stmt-closing")||{}).value),r=parseFloat((O("brv2-anchor-stmt-opening")||{}).value),c=parseFloat((O("brv2-anchor-gl-opening")||{}).value);Number.isFinite(s)&&o.append("gl_closing_override",s),Number.isFinite(i)&&o.append("stmt_closing_override",i),Number.isFinite(r)&&o.append("stmt_opening_override",r),Number.isFinite(c)&&o.append("gl_opening_override",c);const l=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+e},body:o});let p=null;try{p=await l.json()}catch{p=null}if(p&&p.needs_mapping){ke(!1),window.ReconMapping?window.ReconMapping.show(p,{token:e,lang:n,onConfirmed:function(){mn()}}):Ce(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!l.ok||!p||!p.ok||!p.job_id){ke(!1),p&&(p.detail||p.error)?Ce(_humanizeBackendError(p.detail||p.error,"Error "+l.status)):Ce(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const f=O("brv2-progress-sub"),d=await window._reconPollJob(p.job_id,e,{onProgress:m=>{f&&(f.textContent=window._reconProgressText(m,n))}});if(d&&d.status==="needs_mapping"&&d.mapping){ke(!1),window.ReconMapping?window.ReconMapping.show(d.mapping,{token:e,lang:n,onConfirmed:function(){mn()}}):Ce(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(d&&d.status==="needs_review"&&d.review){ke(!1),window.ReconReview?window.ReconReview.show(d.review,{token:e,lang:n,jobId:p.job_id,onConfirmed:async function(m){ke(!0);const h=await window._reconPollJob(m,e,{onProgress:_=>{f&&(f.textContent=window._reconProgressText(_,n))}});await u(h)}}):Ce(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(d&&d.status==="failed"){ke(!1),Ce(ur(d.error_code,n));return}await u(d);async function u(m){try{if(!m||m.status!=="done"||!m.result_id){ke(!1),Ce(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const h=await fetch("/api/recon/bank-v2/"+encodeURIComponent(m.result_id),{headers:{Authorization:"Bearer "+e}});let _=null;try{_=await h.json()}catch{_=null}if(!h.ok||_===null||!_.ok){ke(!1),Ce(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(_.gl_accounts||[]).length>1&&Ir(_.gl_accounts),U.currentTask=_,U.allRows=_.detail||[],U.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(b=>b.classList.toggle("active",b.dataset.filter==="all")),mr(_&&_.summary),ke(!1),Fn(_),Bt();const y=O("brv2-summary-collapse");y&&y.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(h){ke(!1),Ce(h.message||"Network error")}}}catch(o){Ce(o.message||"Network error")}}function Ir(e){const n=O("brv2-acct-select");if(!n)return;const a=window._currentLang||"zh",o={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[a]||"全部账户";n.innerHTML=`<option value="">${o}</option>`+e.map(s=>`<option value="${ve(s)}">${ve(s)}</option>`).join(""),n.style.display=""}function zn(){if(U.initialized){Bt();return}U.initialized=!0,pa("brv2-stmt-zone","brv2-stmt-input","stmt"),pa("brv2-gl-zone","brv2-gl-input","gl");const e=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function n(){const c=parseFloat((O("brv2-anchor-stmt-opening")||{}).value),l=parseFloat((O("brv2-anchor-gl-opening")||{}).value),p=O("brv2-anchor-eq"),f=O("brv2-anchor-eq-val");if(!(!p||!f))if(Number.isFinite(c)&&Number.isFinite(l)){const d=c-l;f.textContent=d.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),p.style.display=""}else p.style.display="none"}e.forEach(c=>{const l=O(c);l&&(l.addEventListener("input",n),l.addEventListener("input",()=>{const p=l.closest(".brv2-anchor-cell");p&&p.classList.remove("is-prefilled"),gr()}))}),hr();const a=O("brv2-run-btn");a&&a.addEventListener("click",mn);const o=O("brv2-reset-btn");o&&o.addEventListener("click",()=>{U.currentTask=null,U.allRows=[],U.stmtFiles=[],U.glFiles=[],Se("stmt"),Se("gl"),De(),Ot(!1);const c=O("brv2-acct-select");c&&(c.style.display="none"),e.forEach(f=>{const d=O(f);if(d){d.value="";const u=d.closest&&d.closest(".brv2-anchor-cell");u&&u.classList.remove("is-prefilled")}});const l=O("brv2-anchor-eq");l&&(l.style.display="none");const p=O("brv2-anchor-prefill-banner");p&&p.classList.remove("show")});const s=O("brv2-new-btn");s&&s.addEventListener("click",()=>{U.currentTask=null,U.allRows=[],U.stmtFiles=[],U.glFiles=[],Se("stmt"),Se("gl"),De(),Ot(!1)});const i=O("brv2-filter-tabs");i&&i.addEventListener("click",c=>{c.stopPropagation();const l=c.target.closest(".brv2-filter-btn");l&&(U.currentFilter=l.dataset.filter,i.querySelectorAll(".brv2-filter-btn").forEach(p=>p.classList.toggle("active",p===l)),no())}),Br(),xr();const r=O("brv2-hist-search");r&&r.addEventListener("input",ao),Bt(),De(),window._brv2LoadHistory=Bt,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(c=>c.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){De(),Se("stmt"),Se("gl"),U.currentTask&&Fn(U.currentTask),Vt()}})}window._loadBankReconV2Panel=function(e){const n=e?document.getElementById(e):null;n&&n.id!=="recon-pane-bank"&&(n.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
            银行对账 v2 · 请前往对账中心使用</div>`),zn()};document.addEventListener("DOMContentLoaded",()=>{O("brv2-run-btn")&&zn()});window._bankReconV2Init=zn;(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const p=document.getElementById("general-tz"),f=document.getElementById("general-date"),d=document.getElementById("general-number");if(!(!p||!f||!d))try{p.value=localStorage.getItem(n)||s.tz,f.value=localStorage.getItem(a)||s.date,d.value=localStorage.getItem(o)||s.number}catch{p.value=s.tz,f.value=s.date,d.value=s.number}}async function r(){const p=document.getElementById("btn-save-general"),f=document.getElementById("general-save-msg");if(!p)return;const d=p.innerHTML;p.disabled=!0,p.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",f&&(f.textContent="",f.classList.remove("error"));try{const u=(document.getElementById("general-tz")||{}).value||s.tz,m=(document.getElementById("general-date")||{}).value||s.date,h=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,u),localStorage.setItem(a,m),localStorage.setItem(o,h)}catch{}window._pearnlyGeneral={tz:u,date_format:m,number_format:h},f&&(f.textContent=t("msg-saved")||"已保存")}catch{f&&(f.textContent=t("msg-save-failed")||"保存失败",f.classList.add("error"))}finally{p.disabled=!1,p.innerHTML=d,setTimeout(function(){f&&(f.textContent="")},3e3)}}function c(){const p=document.getElementById("btn-save-general");if(!p){setTimeout(c,200);return}p._pearnlyGenBound||(p._pearnlyGenBound=!0,p.addEventListener("click",r),i())}function l(){i();const p=document.getElementById("general-lang");if(p){const f=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";p.value=f}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",l)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(c){const l=c.dataset.collapsible;r[l]?c.classList.add("collapsed"):c.classList.remove("collapsed")})}function i(r){const c=a();c[r]=!c[r],o(c),s()}(function(){const c=a();let l=!1;c.sales===void 0&&(c.sales=!1,l=!0),c.expense===void 0&&(c.expense=!0,l=!0),l&&o(c)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const c=n[r];if(!c)return;const l=a();l[c]&&(l[c]=!1,o(l),s())}})();const Lr=`
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
    </div>`;function ua(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=Lr;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,ua();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const i=o.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let Ee=[];window._erpEndpoints=Ee;let Tt=null;async function Qt(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}Ee=(await e.json()).items||[],window._erpEndpoints=Ee,so()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return Qt()};async function oo(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const c=[];c.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&c.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&c.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&c.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=c.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function so(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&Ee.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(Ee.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=Ee.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:Ee.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),oo(),e.innerHTML=Ee.map(s=>{const i=s.config||{},r=escapeHtml(i.url||"");i._token_set;const c=s.enabled!==!1,l=[];s.is_default&&l.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&l.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),c||l.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const p=[];return s.success_count>0&&p.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&p.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=Ee.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,c=document.createElement("div");c.className="erp-limit-hint",r==="free"?c.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:c.textContent=t("ep-plus-limit-hint",{used:s,limit:i}),e.appendChild(c)}}function Cr(e){Tt=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),c=document.getElementById("ep-auto-push"),l=document.getElementById("ep-test-result");l.style.display="none",l.textContent="";const p=document.getElementById("ep-save-error");if(p&&p.remove(),e){const d=Ee.find(u=>u.id===e);if(!d)return;o.value=d.name||"",s.value=(d.config||{}).url||"",i.value=(d.config||{})._token_set&&d.config.token||"",i.placeholder=(d.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!d.is_default,c.checked=!!d.auto_push}else o.value="",s.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=Ee.length===0,c.checked=!0;const f=c.closest(".form-switch-row");if(c.disabled=!1,f){f.classList.remove("disabled-plus"),f.title="",f.style.cursor="",f.onclick=null;const d=f.querySelector(".plus-badge");d&&d.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function io(){document.getElementById("endpoint-modal").style.display="none",Tt=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function ro(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function lo(){const e=document.getElementById("ep-name").value.trim(),n=ro(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:i}}async function Sr(){const{url:e,config:n}=lo(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function Tr(){const e=lo(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){fa(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let i;if(Tt?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(Tt)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const c=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof c=="string"?c:JSON.stringify(c))}io(),showToast(t("ep-save-ok")),Qt()}catch(i){fa(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function fa(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function Mr(e){const n=Ee.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),Qt()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=Qt;window.loadErpTodayStats=oo;window.renderErpEndpointsList=so;window.openEndpointModal=Cr;window.closeEndpointModal=io;window.saveEndpoint=Tr;window.deleteEndpoint=Mr;window.testEndpointConnection=Sr;window._sanitizeUrl=ro;async function co(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function $r(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){co(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const i=s.dataset.receiptAction;i==="retry"?window.retryPushLog(s.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(C=>C.id===o.endpoint_id),i=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),c=new Date(o.created_at).toLocaleString(),l=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),p=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),f=o.response_body||t("erp-receipt-no-tech"),d=o.status==="success";let u=typeof f=="string"?f:JSON.stringify(f,null,2);if(d)try{const C=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},k=C.row_count||(Array.isArray(C.imported_rows)?C.imported_rows.length:0);k>0&&(u=t("log-push-rows").replace("{n}",String(k)))}catch{}const m=(o.external_doc_no||"").trim(),h=(o.external_url||"").trim(),_=(o.external_doc_hint||"").trim(),y=(o.ocr_buyer_name||"").trim()||o.client_name||"-",b=o.seller_name||"-",v=o.push_type==="id_card";let L="-";const g=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(g)&&(L=g.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const x=d?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),B=d?"✓":"✗",E=[],w=(C,k)=>{E.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(C)}</span>
                    <span class="erp-receipt-val">${k}</span>
                </div>`)};if(w(v?t("erp-log-col-booking"):t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),w(t("erp-receipt-erp-name"),escapeHtml(i)),d){let C;m?C=`<strong class="erp-receipt-docno">${escapeHtml(m)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(m)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:C=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,w(t("erp-receipt-doc-no"),C)}v||w(t("erp-receipt-client"),escapeHtml(y)),w(v?t("erp-log-col-customer"):t("erp-receipt-seller"),escapeHtml(b)),d&&w(t("erp-receipt-amount"),escapeHtml(L)),w(t("erp-receipt-time"),escapeHtml(c)),w(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let I="";d&&h?I=`<a class="erp-receipt-primary-btn" href="${escapeHtml(h)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:d&&m&&(I=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(m)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let M="";if(d&&m&&_){const C="erp-receipt-hint-"+_,k=t(C);k&&k!==C&&(M=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(k)}</span></div>`)}let S="";if(!d){const C=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),k=C?C[0]:"",T=typeof currentLang=="string"&&currentLang||window._currentLang||"th",A=o.error_friendly&&o.error_friendly[T]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),H=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),P=!!(o.history_id&&o.endpoint_id),R=[];R.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),H&&R.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),P&&R.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),S=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${k?`<div class="erp-receipt-errcode">${escapeHtml(k)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(A)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${R.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${d?"ok":"fail"}">${B}</span>
                    ${escapeHtml(x)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(l)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${E.join("")}
            </div>

            ${M}
            ${I?`<div class="erp-receipt-primary-wrap">${I}</div>`:""}
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
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=co;window.showLogDetail=$r;const Hr=`
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
    `;be("endpoint-modal",Hr);let bt={key:"all",val:""},It="",sn=!1,Ae=new Set;window._erpSelected=Ae;async function Ar(){const e=document.getElementById("erp-logs-erp-select");if(!(!e||sn)){sn=!0;try{let n=window._erpEndpoints;if(!Array.isArray(n)||n.length===0){const s=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(s.ok){const i=await s.json();n=i&&(i.items||i)||[]}}Array.isArray(n)||(n=[]);const a=new Set,o=[];n.forEach(s=>{const i=(s&&s.adapter||"").toLowerCase();!i||a.has(i)||(a.add(i),o.push({val:i,label:s&&s.name||i}))}),e.innerHTML=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`+o.map(s=>`<option value="${escapeHtml(s.val)}"${s.val===It?" selected":""}>${escapeHtml(s.label)}</option>`).join("")}catch{sn=!1}}}async function ot(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats(),Ar();try{const a=new URLSearchParams({limit:"30"});bt.key==="status"&&a.set("status",bt.val),bt.key==="trigger"&&a.set("trigger",bt.val),It&&a.set("adapter",It);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(m){return m.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){ot(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const r=i.filter(function(m){var h=m.status==="failed"&&m.next_retry_at&&new Date(m.next_retry_at).getTime()>Date.now()-6e4;return!h}).map(function(m){return m.id}),c=It==="mrerp_dms",l=c?t("erp-log-col-booking"):t("erp-log-col-invoice"),p=c?t("erp-log-col-customer"):t("erp-log-col-seller"),f=c?t("erp-log-col-idcard"):t("erp-log-col-client"),d='<div class="erp-log-row erp-log-row-header" data-log-header>'+(r.length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(l)}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(f)}</span><span class="log-seller">${escapeHtml(p)}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=d+i.map(m=>{const h=new Date(m.created_at),_=`${String(h.getMonth()+1).padStart(2,"0")}-${String(h.getDate()).padStart(2,"0")} ${String(h.getHours()).padStart(2,"0")}:${String(h.getMinutes()).padStart(2,"0")}`,y=m.status==="failed"&&m.next_retry_at&&new Date(m.next_retry_at).getTime()>Date.now()-6e4;let b,v,L;m.status==="pending"?(b="retrying",v="⟳",L=t("erp-status-pending")):m.status==="success"?(b="ok",v="✓",L=t("erp-status-success")):m.status==="skipped_dup"?(b="skipped",v="⏭",L=t("erp-status-skipped")):y?(b="retrying",v="↻",L=t("erp-status-retrying")):(b="fail",v="✗",L=t("erp-status-failed"));let g;m.trigger==="auto"?g=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:m.trigger==="retry"?g=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:g=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;const x=m.push_type==="id_card",B=x?`<span class="log-tag log-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span>`:"",E=m.error_friendly&&(m.error_friendly[currentLang]||m.error_friendly.en)||"";let w="";const I=m.retry_count||0,M=m.max_retries||3;if(y){const F=new Date(m.next_retry_at).getTime()-Date.now(),ee=Math.max(0,Math.round(F/6e4)),te=ee<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:ee});w=`${t("erp-retry-attempt",{n:I,max:M})} · ${te}`}else m.status==="failed"&&I>=M&&!m.next_retry_at&&(w=t("erp-retry-exhausted",{n:I}));const S=m.status==="failed"&&!y?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(m.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",C=!y,k=Ae.has(m.id)?"checked":"",T=C?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(m.id)}" ${k}>`:'<span class="erp-log-cb-spacer"></span>',$=(m.ocr_buyer_name||"").trim()||(m.client_name||"").trim(),A=x?`<span class="log-client" title="${escapeHtml(t("erp-log-col-idcard"))}">${m.id_card_tail?"••••"+escapeHtml(m.id_card_tail):"—"}</span>`:$?`<span class="log-client" title="${escapeHtml($)}">${escapeHtml($.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,H=x?'<span class="log-workspace log-workspace-unresolved">—</span>':m.workspace_name?`<span class="log-workspace">${escapeHtml((m.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,P=m.endpoint_name?`<span class="log-erp">${escapeHtml((m.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,R=(m.external_doc_no||"").trim(),D=(m.external_url||"").trim();let j;return D?j=`<span class="log-doc"><a href="${escapeHtml(D)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(R||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:R?j=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(R)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(R.substring(0,18))}</span>`:m.status==="success"?j=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:j='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${b}" data-log-detail="${escapeHtml(m.id)}">
                    ${T}
                    <span class="log-time">${_}</span>
                    <span class="log-status" title="${escapeHtml(L+(w?" · "+w:"")+(E?" · "+E:""))}">${v}</span>
                    ${g}${B}
                    <span class="log-invoice"${x?` title="${escapeHtml(t("erp-log-col-booking"))}"`:""}>${escapeHtml(m.invoice_no||"-")}</span>
                    ${H}
                    ${A}
                    <span class="log-seller"${x?` title="${escapeHtml(t("erp-log-col-customer"))}"`:""}>${escapeHtml((m.seller_name||"").substring(0,20))}</span>
                    ${P}
                    ${j}
                    <span class="log-http">HTTP ${m.http_status||"-"}</span>
                    <span class="log-elapsed">${m.elapsed_ms}ms</span>
                    <span class="log-actions">${S}</span>
                </div>
            `}).join("");const u=new Set(i.map(m=>m.id));for(const m of Array.from(Ae))u.has(m)||Ae.delete(m);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function po(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),ot(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),po(s.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const f=i.dataset.logCb;i.checked?Ae.add(f):Ae.delete(f),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const f=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(u){u.checked=f;const m=u.dataset.logCb;f?Ae.add(m):Ae.delete(m)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),Ae.clear(),document.querySelectorAll(".erp-log-cb").forEach(f=>{f.checked=!1}),window._refreshErpBatchBar();return}const c=n.target.closest("[data-log-detail]");if(c){if(n.target.closest("[data-log-cb]"))return;const f=n.target.closest("[data-copy-doc]");if(f){n.stopPropagation(),window.copyErpDocNo(f.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(c.dataset.logDetail);return}const l=n.target.closest(".chip-filter");if(l){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(f=>f.classList.remove("active")),l.classList.add("active"),bt={key:l.dataset.filterKey,val:l.dataset.filterVal},ot();return}if(n.target.closest("#btn-refresh-logs")){const f=n.target.closest("#btn-refresh-logs");f.classList.add("spinning"),setTimeout(()=>f.classList.remove("spinning"),600),ot();return}const p=n.target.closest(".auto-nav-item");if(p&&p.dataset.autoTab){switchAutomationTab(p.dataset.autoTab);return}}),document.addEventListener("change",n=>{n.target&&n.target.id==="erp-logs-erp-select"&&(It=n.target.value||"",ot())})})();window.loadErpLogs=ot;window.retryPushLog=po;function uo(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function fo(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),i=o.failed&&o.failed>0?"warn":"success";showToast(s,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function mo(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),fo()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),mo()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),uo()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=uo;window._runErpBatchRetry=fo;window._runErpBatchDelete=mo;(function(){let e=null,n=!1;function a(){if(e)return e;const c=document.createElement("div");c.id="line-email-modal",c.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",c.innerHTML=`
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
        `,document.body.appendChild(c),e=c;const l=c.querySelector("#line-email-input"),p=c.querySelector("#line-email-submit-btn"),f=c.querySelector("#line-email-err");async function d(){f.textContent="";const u=(l.value||"").trim().toLowerCase();if(!u||u.indexOf("@")<0||u.split("@")[1].indexOf(".")<0){f.textContent=t("line-email-err-invalid");return}p.disabled=!0,p.style.opacity="0.6";try{const m=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:u})});if(!m.ok)throw new Error("http_"+m.status);const h=await m.json();h.token&&localStorage.setItem("mrpilot_token",h.token),typeof showToast=="function"&&showToast(h.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{f.textContent=t("line-email-err-failed"),p.disabled=!1,p.style.opacity="1"}}return p.addEventListener("click",d),l.addEventListener("keydown",function(u){u.key==="Enter"&&d()}),c}function o(){if(!e)return;const c=e.querySelector("#line-email-title-h"),l=e.querySelector("#line-email-sub-p"),p=e.querySelector("#line-email-input"),f=e.querySelector("#line-email-submit-btn");c&&(c.textContent=t("line-email-title")),l&&(l.textContent=t("line-email-sub")),p&&(p.placeholder=t("line-email-placeholder")),f&&(f.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const c=e.querySelector("#line-email-input");c&&setTimeout(function(){c.focus()},100)}async function i(){const c=localStorage.getItem("mrpilot_token");if(c)try{const l=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+c}});if(!l.ok)return;const p=await l.json();p&&p.needs_email&&s()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(f){let d=0;return f.length>=8&&d++,f.length>=12&&d++,/[a-zA-Z]/.test(f)&&/\d/.test(f)&&d++,/[^a-zA-Z0-9]/.test(f)&&d++,Math.min(3,d)}function n(f,d){const u=document.getElementById("cpw-msg");u&&(u.textContent=f,u.className="cpw-msg "+(d||""))}function a(f){return typeof t=="function"?t(f):f}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(d=>{const u=document.getElementById(d);u&&(u.value="",u.setAttribute("readonly","readonly"))});const f=document.getElementById("cpw-strength-bar");f&&(f.style.width="0%",f.className="cpw-strength-bar"),n("","")}async function i(){const f=document.getElementById("btn-change-pw"),d=document.getElementById("cpw-old"),u=document.getElementById("cpw-new"),m=document.getElementById("cpw-confirm"),h=document.getElementById("cpw-strength-bar");if(!f||!d||!u||!m)return;const _=d.value,y=u.value,b=m.value;if(!_||!y||!b){n(a("settings-change-pw-empty"),"error");return}if(y.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(y)&&/\d/.test(y))){n(a("settings-change-pw-too-weak"),"error");return}if(y!==b){n(a("settings-change-pw-mismatch"),"error");return}f.disabled=!0;const v=f.textContent;f.textContent=a("settings-change-pw-submitting"),n("","");try{const L=localStorage.getItem("mrpilot_token"),g=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+L},body:JSON.stringify({old_password:_,new_password:y})}),x=await g.json().catch(()=>({}));if(g.ok&&x.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),d.value="",u.value="",m.value="",h&&(h.style.width="0%",h.className="cpw-strength-bar");else{const B=x.detail||"";let E=a("settings-change-pw-success");B==="wrong_old_password"?E=a("settings-change-pw-wrong-old"):B==="password_too_short"?E=a("settings-change-pw-too-short"):B==="password_too_weak"?E=a("settings-change-pw-too-weak"):E=B||"Error",n(E,"error")}}catch(L){console.error("change_password",L),n("Network error","error")}finally{f.disabled=!1,f.textContent=v}}function r(){o||(o=!0,document.addEventListener("click",f=>{if(!f.target||!f.target.closest)return;const d=f.target.closest(".cpw-eye");if(d){const u=document.getElementById(d.dataset.target);u&&(u.type=u.type==="password"?"text":"password");return}if(f.target.closest("#cpw-forgot-link")){f.preventDefault(),c();return}if(f.target.closest("#btn-change-pw")){i();return}f.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",f=>{if(f.target&&f.target.id==="cpw-new"){const d=document.getElementById("cpw-strength-bar");if(!d)return;const u=e(f.target.value),m=["0%","33%","66%","100%"],h=["","weak","medium","strong"];d.style.width=m[u],d.className="cpw-strength-bar "+h[u]}}),document.addEventListener("focusin",f=>{f.target&&["cpw-old","cpw-new","cpw-confirm"].includes(f.target.id)&&f.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function c(){const f=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),d=f&&f.username?f.username:"",u=l(d);let m=document.getElementById("cpw-forgot-overlay");m&&m.remove(),m=document.createElement("div"),m.id="cpw-forgot-overlay",m.className="cpw-forgot-overlay",m.innerHTML=`
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
        `,document.body.appendChild(m);const h=()=>m.remove();m.querySelector("#cpw-forgot-close").addEventListener("click",h),m.querySelector("#cpw-forgot-cancel").addEventListener("click",h),m.addEventListener("click",_=>{_.target===m&&h()}),m.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const _=m.querySelector("#cpw-forgot-send"),y=m.querySelector("#cpw-forgot-msg");_.disabled=!0;const b=_.textContent;_.textContent=a("cpw-forgot-sending");try{const v=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:d})}),L=await v.json().catch(()=>({}));v.ok?(y.textContent=a("cpw-forgot-success"),y.className="cpw-forgot-msg success",_.style.display="none",m.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(y.textContent=L.detail||a("cpw-forgot-fail"),y.className="cpw-forgot-msg error",_.disabled=!1,_.textContent=b)}catch{y.textContent=a("cpw-forgot-fail"),y.className="cpw-forgot-msg error",_.disabled=!1,_.textContent=b}})}function l(f){if(!f||!f.includes("@"))return f||"";const[d,u]=f.split("@");return d.length<=2?d+"****@"+u:d.slice(0,2)+"****@"+u}function p(f){return f==null?"":String(f).replace(/[&<>"']/g,d=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[d])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),c=r&&r.detail;let l="";if(typeof c=="string"?l=c:c&&typeof c=="object"&&(l=c.code||""),console.warn("[heartbeat] session revoked",l),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),l==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const p=l==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(p),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function en(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),i=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const c=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",l=r.is_active===!1?"team-status-off":"team-status-on",p=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",f=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${l}"></span>
                            <span>${escapeHtml(p)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(c)}</span>
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function jr(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),c=document.getElementById("add-emp-submit"),l=(o.value||"").trim(),p=(s.value||"").trim(),f=i.value||"";if(r.textContent="",r.classList.remove("error"),!l||l.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(l)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(p&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(f.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(f)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(f)&&/\d/.test(f))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}c.disabled=!0,c.textContent=t("msg-saving")||"保存中...";try{const d={username:l,password:f};p&&(d.email=p);const u=await apiPost("/api/team/employees",d),m=u?await u.json().catch(()=>({})):{};if(u&&u.ok&&m&&m.ok){showToast(t("team-added")||"员工已添加","success"),n(),en();return}const h=m&&m.detail||"unknown",_={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=_[h]||(t("team-create-failed")||"创建失败")+" ("+h+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{c.disabled=!1,c.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function Pr(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){en();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Dr(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),en();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function qr(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const c=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",l=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(c.replace("{ch}",l),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),jr();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),Pr(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),Dr(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),qr(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=en;function Rr(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=Rr;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
