(function(){const n=[];function a(o){try{n.push(Object.assign({ts:Date.now()},o)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(o)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(o){o.target&&o.target!==window&&(o.target.src||o.target.href)||a({type:"js_error",summary:String(o.message||"JS Error").slice(0,200),detail:{file:o.filename||"",line:o.lineno||0,col:o.colno||0,stack:o.error&&o.error.stack?String(o.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(o){const i=o.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const s=window.fetch;typeof s=="function"&&(window.fetch=function(){const o=arguments,i=Date.now(),r=typeof o[0]=="string"?o[0]:o[0]&&o[0].url||"?",l=o[1]&&o[1].method||"GET",m=String(r).split("?")[0];return s.apply(this,o).then(function(d){const p=Date.now()-i;if(d.ok)p>2500&&a({type:"api_slow",summary:l+" "+m+" → 慢 "+p+"ms",detail:{url:r,method:l,status:d.status,elapsed_ms:p}});else{let c="";try{d.clone().text().then(function(v){c=String(v||"").slice(0,500),a({type:"api_error",summary:l+" "+m+" → "+d.status+" ("+p+"ms)",detail:{url:r,method:l,status:d.status,elapsed_ms:p,body_preview:c}})}).catch(function(){a({type:"api_error",summary:l+" "+m+" → "+d.status+" ("+p+"ms)",detail:{url:r,method:l,status:d.status,elapsed_ms:p,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:l+" "+m+" → "+d.status+" ("+p+"ms)",detail:{url:r,method:l,status:d.status,elapsed_ms:p}})}}return d}).catch(function(d){const p=Date.now()-i;throw a({type:"api_fail",summary:l+" "+m+" → 网络失败 ("+p+"ms)",detail:{url:r,method:l,elapsed_ms:p,error:String(d&&d.message||d)}}),d})}),["error","warn"].forEach(function(o){const i=console[o];typeof i=="function"&&(console[o]=function(){try{const r=[];for(let l=0;l<arguments.length;l++){const m=arguments[l];if(typeof m=="string")r.push(m);else if(m&&m instanceof Error)r.push(m.message);else try{r.push(JSON.stringify(m).slice(0,300))}catch{r.push(String(m))}}a({type:"console_"+o,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(s=>s.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function Qr(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function el(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function tl(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function pa(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const s in n)a=a.replace("{"+s+"}",n[s]);return a}function nl(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function al(e,n){n=n||14;const s={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${s}</svg>`}function ua(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},s={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},o=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[o]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[o]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+s[o]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function ma(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function sl(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...ma()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),s=a&&a.detail;let o="";if(typeof s=="string"?o=s:s&&typeof s=="object"&&(o=s.code||""),n.status===401||typeof o=="string"&&o.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,s),localStorage.removeItem("mrpilot_token"),o==="auth.session_revoked")ua();else{const l=o==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(pa(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=s,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function ol(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...ma()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const o=await a.clone().json().catch(()=>({})),i=o&&o.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")ua();else{const m=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(pa(m),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function il(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...ma()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const o=await a.json().catch(()=>({})),i=o&&o.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")ua();else{const m=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(pa(m),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const s=await a.json().catch(()=>({}));return{ok:a.ok&&s.ok!==!1,...s}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=sl;window.apiPost=ol;window.t=pa;window.escapeHtml=nl;window.svgIcon=al;window._showSessionRevokedModal=ua;window._wsHeader=ma;window.apiPut=il;window.getMaxFiles=Qr;window.getMaxPagesPerFile=el;window.getMaxMbPerFile=tl;function $e(e,n){const a=document.getElementById(e);if(!(!a||a.dataset.wbInjected==="1")){a.innerHTML=n,a.dataset.wbInjected="1";try{const s=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",o=window.I18N;if(!o||!o[s])return;a.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");r&&o[s][r]&&(i.textContent=o[s][r])}),a.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");r&&o[s][r]&&(i.placeholder=o[s][r])})}catch{}}}const rl=`
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
    `;$e("page-ocr",rl);const ll=`
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
            <img class="brand-icon" src="/static/brand/pwa-icon-192.png?v=1" alt="Pearnly" />
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
`,cl=`
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
            <div class="nav-sub-item nav-sales-head">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 2h8l3 3v13H5z"/>
                    <path d="M8 8h5M8 11h5M8 14h3"/>
                    <path d="M13 2v3h3"/>
                </svg>
                <span class="nav-label" data-i18n="nav-sales-invoices">销售发票</span>
                <svg class="nav-sub2-chev" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8l4 4 4-4"/></svg>
            </div>
            <!-- 销售发票 两子屏(PO-10)· 默认收起 · 点头部展开 · 工作台 / 账套(商品=共享主数据·见下方主数据区) -->
            <div class="nav-sub2">
                <div class="nav-item nav-sub2-item" data-route="sales-invoices">
                    <span class="nav-label" data-i18n="nav-sales-workbench">发票工作台</span>
                </div>
                <div class="nav-item nav-sub2-item" data-route="sales-account">
                    <span class="nav-label" data-i18n="nav-sales-account">账套 / 开票资料</span>
                </div>
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

    <!-- 主数据 · 商品/客户共享(以后 POS/库存复用同一份商品库)-->
    <div class="nav-section-label" data-i18n="nav-group-master">主数据</div>

    <!-- 商品管理 = 共享主数据(销项 PO-10 · 不归销售发票子菜单) -->
    <div class="nav-item" data-route="sales-products">
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 7l1-4h12l1 4M4 7v9h12V7M8 16v-4h4v4"/>
        </svg>
        <span class="nav-label" data-i18n="nav-sales-products">商品管理</span>
    </div>

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

    <!-- KNOWLEDGE · 客户知识中心入口(放「客户管理」下方)· 探针门控(知识库 flag 开才显示 · knowledge-center.ts) -->
    <div class="nav-item" data-route="knowledge" id="nav-knowledge" style="display:none;">
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="10" cy="10" r="7.5"/>
            <path d="M7.8 7.6a2.2 2.2 0 114.4 0c0 1.3-2.2 1.7-2.2 3"/>
            <line x1="10" y1="14" x2="10" y2="14.01"/>
        </svg>
        <span class="nav-label" data-i18n="nav-knowledge">客户知识</span>
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
`;$e("topbar",ll);$e("sidebar",cl);function ds(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const s=document.getElementById("general-lang");s&&(s.value=e);const o=document.getElementById("col-conf-th");o&&o.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&ps(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function dl(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",o=>{o.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(o=>{o.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(o)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});dl("lang-dropdown",e=>ds(e.dataset.lang));const di=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","sales-products","sales-account","receivables","reconcile","cloud","test-center","knowledge"];function pi(e){di.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(s=>s.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(s=>{s.classList.toggle("active",s.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="knowledge"&&typeof window.loadKnowledgePage=="function"&&window.loadKnowledgePage(),e==="sales-invoices"&&typeof window.loadSalesWorkbench=="function"&&window.loadSalesWorkbench(),e==="sales-products"&&typeof window.loadSalesProducts=="function"&&window.loadSalesProducts(),e==="sales-account"&&typeof window.loadSalesAccount=="function"&&window.loadSalesAccount(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function ps(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function ui(){try{const[e,n,a,s]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(o=>o.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,s&&(window._planState=s),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const o=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(o&&!i){window.location.replace("/home");return}if(!o&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=o}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,s&&(window._planState=s),window.renderBrandWorkspace(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(o){console.error("[nav-ia phase1] render avatar menu",o)}ps(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const o=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(o&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(o&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(o){console.error("force-pw init",o)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(o){console.error("onboarding init",o)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(o){console.error("settings forms init",o)}}catch(e){console.error(e)}}window.applyLang=ds;window.routeTo=pi;window.loadAll=ui;window.updateUploadHint=ps;try{ds(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");pi(di.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);ui();function pl(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){if(!i||typeof i!="string")return null;const r=i.trim();return r?r.includes("@")&&r.indexOf("@")>0&&r.indexOf(".")>r.indexOf("@")?r.split("@")[0]:r:null}const s=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let o=null;for(const i of s){const r=a(i);if(r){o=r;break}}o||(o=t("brand-workspace-fallback")||"我的工作台"),e.textContent=o,e.title=o,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",o,"· _userInfo fields:",Object.keys(n))}function ul(){const e=document.getElementById("offline-banner"),n=e??document.createElement("div");e||(n.id="offline-banner",n.className="offline-banner",n.style.display="none",document.body.insertBefore(n,document.body.firstChild));function a(){navigator.onLine===!1?(n.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",n.classList.remove("is-online"),n.classList.add("is-offline"),n.style.display="flex"):n.classList.contains("is-offline")?(n.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",n.classList.remove("is-offline"),n.classList.add("is-online"),setTimeout(()=>{n.style.display="none",n.classList.remove("is-online")},2e3)):n.style.display="none"}window.addEventListener("online",a),window.addEventListener("offline",a),a()}window.renderBrandWorkspace=pl;window.installNetworkBanner=ul;const mi="mrpilot_sidebar_collapsed";localStorage.getItem(mi)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(mi,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const s=document.querySelectorAll("#page-integrations .int-top-tab"),o=document.querySelectorAll("#page-integrations .int-top-panel");if(s.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),o.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}if(a==="push-exc"&&typeof window.loadErpExceptions=="function")try{window.loadErpExceptions()}catch{}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),s=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),s&&s.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const s=a.target.closest("#page-integrations .int-top-tab");if(s){const i=s.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const s=document.querySelector(".auto-content");s&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(o){o.style.display="",s.appendChild(o)})}window.openIntegrationDrawer=function(a,s){const o=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),l=document.getElementById("int-drawer-body");if(!o||!l)return;e(),o.dataset.currentTab=a||"",r&&(r.textContent=s||""),l.innerHTML="";var m={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},d=m[a]||a;const p=document.querySelector('.auto-panel[data-auto-panel="'+d+'"]');p?(p.style.display="block",l.appendChild(p)):l.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',o.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var c={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(c[a])try{c[a]()}catch(u){console.warn("[int-drawer] loader error",u)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(u){console.warn("[int-drawer] ERP load error",u)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),s=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),s&&(s.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),s=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),s&&s.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(o){o.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(o=>{o.addEventListener("click",()=>switchSettingsTab(o.dataset.tab))});let s=null;try{s=localStorage.getItem("mrpilot_settings_tab")}catch{}if(s){const o=document.querySelector(`.settings-tab[data-tab="${s}"]`);if(o&&o.style.display!=="none"){switchSettingsTab(s);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),s=document.getElementById("btn-save-company");if(!a&&!s){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),s&&s.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let zn=null;function ml(){Oa(),zn=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&Oa()}catch{}},1e4)}function Oa(){zn&&(clearInterval(zn),zn=null)}window.startEnginePolling=ml;window.stopEnginePolling=Oa;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target,a=n.closest("[data-rd-action]");if(a){const i=a.dataset.rdAction,r=a.dataset.rdSide;i==="verify"?callRdVerify(r):i==="sync"&&callRdSync(r);return}if(n.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=n.closest("[data-archive-copy]");if(o){const i=o.dataset.archiveCopy;navigator.clipboard?.writeText(i).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const to=document.getElementById("btn-custom-template");to&&to.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});const vl=`
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
    `,fl=`
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
`;$e("pearnly-confirm-modal",vl);$e("confirm-modal",fl);window.pearnlyConfirm=function(e,n){return new Promise(function(a){const s=document.getElementById("pearnly-confirm-modal"),o=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),l=document.getElementById("pearnly-confirm-cancel"),m=document.getElementById("pearnly-confirm-close");if(!s||!i||!r||!l){a(window.confirm(e));return}o&&(o.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",s.style.display="flex";function d(f){s.style.display="none",r.removeEventListener("click",p),l.removeEventListener("click",c),m&&m.removeEventListener("click",c),s.removeEventListener("click",u),document.removeEventListener("keydown",v),a(f)}function p(){d(!0)}function c(){d(!1)}function u(f){f.target===s&&d(!1)}function v(f){f.key==="Escape"?d(!1):f.key==="Enter"&&d(!0)}r.addEventListener("click",p),l.addEventListener("click",c),m&&m.addEventListener("click",c),s.addEventListener("click",u),document.addEventListener("keydown",v),setTimeout(function(){try{l.focus()}catch{}},50)})};const hl=`
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

`,gl=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=hl+gl,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");o&&a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");o&&a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
            <button class="int-top-tab" type="button" data-int-top-tab="push-exc" data-i18n="int-tab-push-exc">推送异常</button>
        </div>

        <!-- Tab 3: 推送异常(从异常页搬来 · 独立来源 · 派生自 erp_push_logs · 内容由 renderErpExceptions 填充) -->
        <div class="int-top-panel" data-int-top-panel="push-exc">
            <div class="erp-exc-block" id="erp-exc-block" hidden></div>
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e=document.getElementById("page-settings");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();const bl=`
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

`,yl=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=bl+yl,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");o&&a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");o&&a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e={"page-integration":`
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
`},n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;Object.keys(e).forEach(s=>{const o=document.getElementById(s);!o||o.dataset.wbInjected==="1"||(o.innerHTML=e[s],o.dataset.wbInjected="1",a&&a[n]&&o.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");a[n][r]&&(i.textContent=a[n][r])}))})})();(function(){const e=document.getElementById("page-dashboard");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])})}catch{}}})();function wl(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function kl(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function xl(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const s=t(a,e);if(s&&s!==a)return s}catch(s){console.warn("[i18n] t() failed for key:",a,s)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function _l(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function El(e,n,a){let s=document.getElementById("mp-toast-wrap");s||(s=document.createElement("div"),s.id="mp-toast-wrap",document.body.appendChild(s)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const o={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${o[n]||o.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,s.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let l=null;const m=()=>{l&&(clearTimeout(l),l=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(l=setTimeout(m,r)),m}window.showAlert=wl;window.hideAlerts=kl;window._humanizeBackendError=xl;window.humanizeError=_l;window.showToast=El;function Il(e,n){return n=n||{},new Promise(a=>{const s=document.getElementById("confirm-modal"),o=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),l=document.getElementById("confirm-modal-close"),m=document.getElementById("confirm-modal-title");if(!s||!o||!i||!r){a(!1);return}m.textContent=n.title||t("confirm-default-title");const d=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const v=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),f=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");o.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${v}</div>
                <input type="text" id="${d}" placeholder="${f}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else o.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",s.style.display="flex";const p=v=>{s.style.display="none",i.onclick=null,r.onclick=null,l.onclick=null,s.onclick=null,document.removeEventListener("keydown",u),n.promptInput&&(o.innerHTML=""),r.style.display="",a(v)},c=()=>{const v=d?document.getElementById(d):null;return v?v.value:""},u=v=>{v.key==="Escape"?p(n.promptInput?null:!1):v.key==="Enter"&&p(n.promptInput?c():!0)};i.onclick=()=>p(n.promptInput?c():!0),r.onclick=()=>p(n.promptInput?null:!1),l.onclick=()=>p(n.promptInput?null:!1),s.onclick=v=>{v.target===s&&p(n.promptInput?null:!1)},document.addEventListener("keydown",u),setTimeout(()=>{if(n.promptInput){const v=document.getElementById(d);v&&v.focus()}else i.focus()},50)})}window.showConfirm=Il;function Bl(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof Va=="function"&&Va()}catch(n){console.warn("settings tab side effect failed:",n)}}}function Ll(e){if(!e)return;const n=(a,s)=>{const o=document.getElementById(a);o&&(o.value=s||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function $l(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const s={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},o=await apiPut("/api/me/profile",s);if(o&&o.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function Sl(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const s={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},o=await apiPut("/api/me/profile",s);if(o&&o.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function Va(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const s=document.getElementById("api-key-card");s&&(s.style.display="");return}Cl(n,e);const a=document.getElementById("api-key-card");if(a){const s=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=s?"":"none"}}function Cl(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
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
    `}window.switchSettingsTab=Bl;window.fillSettingsForms=Ll;window.saveProfile=$l;window.saveCompany=Sl;window.renderSettings=Va;function va(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function us(e){return e=e||_userInfo,!!e&&(e.role==="owner"||va(e))}function vi(e){return e=e||_userInfo,!!e&&e.role==="member"&&!va(e)}function Tl(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!va(e)}function fi(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function hi(e){return vi(e)}function Hl(e){return us(e)}function Ml(e){return us(e)&&fi(e)}window.isMoneyHidden=hi;window.isSuperAdmin=va;window.isOwner=us;window.isEmployee=vi;window.isTrial=Tl;window.isLifetime=fi;window.shouldHideMoney=hi;window.canManageTeam=Hl;window.canManageApiKey=Ml;function Al(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const s=Math.max(0,a-n),o=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,l;if(s===0)r="danger",l=t("quota-banner-exhausted");else if(o>=90)r="danger",l=t("quota-banner-very-low",{n:s});else if(o>=70)r="warn",l=t("quota-banner-low",{n:s});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(l)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const m=e.querySelector(".quota-banner-close");m&&m.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function Pl(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),s=canManageApiKey(e),o=document.querySelector('.nav-item[data-route="templates"]');o&&(o.classList.remove("locked-for-plan"),o.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const l=document.querySelector('.settings-tab[data-tab="team"]');l&&(l.style.display=a?"":"none");const m=document.querySelector('.settings-panel[data-settings-panel="team"]');m&&(m.dataset.permHidden=a?"0":"1");const d=document.querySelector('.settings-tab[data-tab="api"]');d&&(d.style.display=s||isSuperAdmin(e)?"":"none");const p=document.querySelector('.settings-tab[data-tab="plan"]');p&&(p.style.display=n?"none":"");const c=document.querySelector('.settings-tab[data-tab="company"]');c&&(c.style.display=n?"none":"");const u=document.getElementById("info-bar");u&&(u.style.display=n?"none":"");const v=document.getElementById("trial-banner");v&&n&&(v.style.display="none");const f=document.getElementById("plan-banner");f&&n&&(f.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(y=>{y.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const y=document.querySelector(".settings-tab.active");y&&y.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(y){console.warn("[v118.12.3] failed to fix active tab:",y)}if(window.PEARNLY_ADMIN_MODE){const y=document.getElementById("admin-mode-banner");y&&(y.style.display="flex"),document.querySelectorAll(".nav-item").forEach(g=>{g.classList.contains("nav-admin-only")||(g.style.display="none")}),document.querySelectorAll(".nav-group").forEach(g=>{g.classList.contains("nav-group-admin-only")||(g.style.display="none")});const b=document.getElementById("client-switcher");b&&(b.style.display="none"),document.body.classList.add("admin-mode");const h=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(g=>{const _=g.dataset.tab;_&&!h.includes(_)&&(g.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(g=>{const _=g.dataset.pane;_&&!h.includes(_)&&(g.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(g=>{const _=g.querySelectorAll(".settings-tab");Array.from(_).some(k=>k.style.display!=="none")||(g.style.display="none")})}}function jl(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const s=e.tenant_type;if(s==="byo_api")e.has_own_gemini_key?a=`
                <div class="info-chip">
                    <span class="chip-value chip-value-lifetime">${escapeHtml(t("info-unlimited-own-key"))}</span>
                </div>
            `:a=`
                <div class="info-chip chip-warn">
                    <span class="chip-value">${escapeHtml(t("info-need-api-key"))}</span>
                </div>
            `;else if(s==="admin"||e.is_super_admin)a=`
            <div class="info-chip">
                <span class="chip-value chip-value-lifetime">${escapeHtml(t("info-unlimited-own-key"))}</span>
            </div>
        `;else{const o=e.tenant_used!=null?e.tenant_used:e.used_this_month||0,i=e.tenant_quota!=null&&e.tenant_quota>0?e.tenant_quota:e.monthly_quota||0,r=i>0?Math.min(100,o/i*100):0;let l="";r>=95?l="danger":r>=80&&(l="warn"),i>0?a=`
                <div class="info-chip">
                    <span class="chip-label">${escapeHtml(t("info-monthly"))}</span>
                    <span class="chip-value">${o} / ${i}</span>
                    <div class="mini-bar"><div class="mini-bar-fill ${l}" style="width:${r}%"></div></div>
                </div>
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=Al;window.applySidebarVisibility=Pl;window.renderInfoBar=jl;async function gi(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const s=await a.json().catch(()=>({}));return(typeof s.detail=="string"?s.detail:s.detail&&s.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function bi(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Yn(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function $t(e,n,a){const s=document.querySelector(`[data-rd-status="${e}"]`);s&&(s.innerHTML=n,s.className="rd-status"+(a?" "+a:""))}async function Dl(e){const a=Yn(e==="seller"?"seller_tax":"buyer_tax");$t(e,t("rd-verifying"),"loading");const s=await gi("/api/rd/verify",{tax_id:a});if(!s)return;if(!s.ok){$t(e,t(bi(s.error)),"error");return}s.data&&s.data.valid?$t(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):$t(e,t("rd-status-invalid"),"invalid")}async function ql(e){const a=Yn(e==="seller"?"seller_tax":"buyer_tax");$t(e,t("rd-syncing"),"loading");const s=await gi("/api/rd/lookup",{tax_id:a,branch:0});if(s){if(!s.ok){$t(e,t(bi(s.error)),"error");return}$t(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),Rl(e,s.data)}}function Rl(e,n){const a=e==="seller"?"seller_name":"buyer_name",s=e==="seller"?"seller_addr":"buyer_addr",o=Yn(a),i=Yn(s),r=[];n.name&&n.name!==o&&r.push({field:a,label:t("rd-field-name"),current:o,official:n.name}),n.address&&n.address!==i&&r.push({field:s,label:t("rd-field-address"),current:i,official:n.address});const l=[];n.branch_label&&l.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&l.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let m=document.getElementById("rd-sync-modal");if(m||(m=document.createElement("div"),m.id="rd-sync-modal",m.className="rd-modal-mask",document.body.appendChild(m)),r.length===0)m.innerHTML=`
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
                    ${l.length?`<div class="rd-modal-extra">${l.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                </div>
            </div>
        `;else{const c=r.map((u,v)=>`
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
        `).join("");m.innerHTML=`
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t("rd-modal-title"))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    ${c}
                    ${l.length?`<div class="rd-modal-extra">${l.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t("rd-modal-apply"))}</button>
                </div>
            </div>
        `}m.classList.add("show");const d=()=>m.classList.remove("show");m.querySelector(".rd-modal-close").addEventListener("click",d),m.querySelectorAll("[data-rd-modal-close]").forEach(c=>c.addEventListener("click",d)),m.addEventListener("click",c=>{c.target===m&&d()});const p=m.querySelector("[data-rd-modal-apply]");p&&p.addEventListener("click",()=>{const c=_results[_drawerIdx];if(!c){d();return}m.querySelectorAll("[data-rd-apply]:checked").forEach(u=>{const v=u.dataset.field,f=u.dataset.value;c.edits[v]=f,c.merged_fields[v]=f;const y=document.querySelector(`[data-field="${v}"]`);y&&(y.value=f);const b=document.querySelector(`[data-field-wrap="${v}"]`);b&&b.classList.add("edited")}),updateDrawerEditCount(),renderResults(),d()})}window.callRdVerify=Dl;window.callRdSync=ql;function Fl(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(o=>!o.is_duplicate&&!o.is_copy),s=a.length>0?a:e;for(const o of s){const i=o.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function zl(e){const n=e.target,a=n.dataset.field,s=n.value,o=_results[_drawerIdx],i=o.merged_fields[a];s===(i??"")?delete o.edits[a]:(o.edits[a]=s,o.merged_fields[a]=s);const r=document.querySelector(`[data-field-wrap="${a}"]`);r&&r.classList.toggle("edited",o.edits[a]!==void 0),yi(),renderResults()}function yi(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=Fl;window.onFieldEdit=zl;window.updateDrawerEditCount=yi;function Nl(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,s=document.getElementById("force-pw-new").value,o=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!s){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(s!==o){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(s.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(s)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(s)&&/\d/.test(s))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(s===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:s})}),l=await r.json().catch(()=>({}));if(!r.ok){const m=l&&l.detail||"unknown",d={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=d[m]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=Nl;(function(){let e=null,n=null,a=null,s=null;function o(g){return document.getElementById(g)}async function i(){f(),b(),await r()}async function r(){try{const g=localStorage.getItem("mrpilot_token"),_=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+g}});if(!_.ok){y(t("linebot-err-status"));return}const w=await _.json();w.bound?l(w):await m()}catch{y(t("linebot-err-status"))}}function l(g){v(),o("linebot-unbound").style.display="none",o("linebot-bound").style.display="block";const _=o("linebot-status-summary");_&&(_.textContent=t("linebot-status-bound"),_.style.background="#D1FAE5",_.style.color="#065F46");const w=o("linebot-bound-name");w&&(w.textContent=g.line_display_name||"(LINE User)");const k=o("linebot-avatar");k&&(g.line_picture_url?(k.src=g.line_picture_url,k.style.display=""):k.style.display="none");const x=o("linebot-bound-since");x&&g.bound_at&&(x.textContent=new Date(g.bound_at).toLocaleString())}async function m(){o("linebot-bound").style.display="none",o("linebot-unbound").style.display="block";const g=o("linebot-status-summary");g&&(g.textContent=t("linebot-status-unbound"),g.style.background="#FEE2E2",g.style.color="#B91C1C"),await d(),u()}async function d(){try{const g=localStorage.getItem("mrpilot_token"),_=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+g}});if(!_.ok){y(t("linebot-err-code"));return}const w=await _.json();a=w.code,s=new Date(w.expires_at).getTime(),p(w)}catch{y(t("linebot-err-code"))}}function p(g){const _=o("linebot-code");_&&(_.textContent=g.code);const w=o("linebot-bot-id");w&&(w.textContent=g.bot_basic_id||t("linebot-bot-id-missing"));const k=o("linebot-qr");if(k)if(g.bot_friend_url){const x="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(g.bot_friend_url);k.classList.remove("empty"),k.innerHTML='<img src="'+x+'" alt="LINE Bot QR">'}else k.classList.add("empty"),k.innerHTML="";c()}function c(){e&&clearInterval(e);const g=o("linebot-code-expires");function _(){if(!s)return;const w=s-Date.now();if(w<=0){g&&(g.textContent=t("linebot-code-expired"),g.classList.add("expiring"));const I=o("linebot-code");I&&(I.style.opacity="0.4"),clearInterval(e),e=null;return}const k=Math.floor(w/1e3),x=Math.floor(k/60),E=k%60;g&&(g.textContent=t("linebot-code-expires-in").replace("{m}",x).replace("{s}",String(E).padStart(2,"0")),w<6e4?g.classList.add("expiring"):g.classList.remove("expiring"))}_(),e=setInterval(_,1e3)}function u(){v(),n=setInterval(async()=>{try{const g=localStorage.getItem("mrpilot_token"),_=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+g}});if(!_.ok)return;const w=await _.json();w.bound&&l(w)}catch{}},4e3)}function v(){n&&(clearInterval(n),n=null)}function f(){e&&(clearInterval(e),e=null),v()}function y(g){const _=o("linebot-error");_&&(_.textContent=g,_.style.display="block")}function b(){const g=o("linebot-error");g&&(g.style.display="none")}async function h(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const _=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+_}})).ok){y(t("linebot-err-unbind"));return}await i()}catch{y(t("linebot-err-unbind"))}}document.addEventListener("click",g=>{if(g.target.closest("#linebot-code-refresh")){g.preventDefault(),b(),d();return}if(g.target.closest("#linebot-unbind")){g.preventDefault(),h();return}}),window._loadLineBotPanel=i})();function fa(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const l=parseFloat(r.merged_fields.total_amount);isNaN(l)||(n+=l)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,s=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${s}</span>
        </div>
    `;let o=_results.map((r,l)=>({...r,_idx:l}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();o=o.filter(l=>(l.filename||"").toLowerCase().includes(r)||(l.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&o.sort((r,l)=>{let m,d;return _sortKey==="filename"?(m=r.filename,d=l.filename):_sortKey==="invoice_no"?(m=r.merged_fields.invoice_number,d=l.merged_fields.invoice_number):_sortKey==="invoice_date"?(m=r.merged_fields.date,d=l.merged_fields.date):_sortKey==="total"?(m=parseFloat(r.merged_fields.total_amount)||0,d=parseFloat(l.merged_fields.total_amount)||0):_sortKey==="confidence"?(m=r.confidence,d=l.confidence):(m="",d=""),m<d?_sortDir==="asc"?-1:1:m>d?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=o.map((r,l)=>{const m=r.merged_fields,d=`<span class="empty-cell">${t("empty-val")}</span>`,p="conf-tip-"+(r.confidence||"low"),c="conf-"+(r.confidence||"low"),u=t(p),v=t(c);return`
            <tr data-idx="${r._idx}">
                <td class="num">${l+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${m.invoice_number?escapeHtml(m.invoice_number):d}</td>
                <td class="date">${m.date?escapeHtml(m.date):d}</td>
                <td class="amount">${m.total_amount?Number(m.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):d}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(u)}">${v}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const l=parseInt(r.dataset.idx,10);ki(l)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),fa()})});let no=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(no),no=setTimeout(()=>{_searchKeyword=n.trim(),fa(),wi()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",fa(),wi(),e.focus()});function wi(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const s of _results)[s.filename,s.merged_fields?.invoice_number,s.merged_fields?.seller_name,s.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function ki(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,s=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(s)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const o=_userInfo&&_userInfo.can_edit_fields,i=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,l=document.getElementById("drawer-body"),m=o?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,d=i?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(l.innerHTML=`
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
                        <select class="drawer-client-select" id="drawer-client-select" ${o?"":"disabled"}>
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
                               ${o?"":"readonly"}>
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
            ${Se("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",o)}
            ${Se("date","drawer-lbl-date",r.date,"input",o)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${Se("subtotal","drawer-lbl-subtotal",r.subtotal,"input",o)}
            ${Se("vat","drawer-lbl-vat",r.vat,"input",o)}
            ${Se("total_amount","drawer-lbl-total",r.total_amount,"input",o)}
            ${r.wht_amount||r.wht_rate?`
                ${Se("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",o,Ol(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${Se("seller_name","drawer-lbl-name",r.seller_name,"input",o)}
            ${Se("seller_tax","drawer-lbl-tax",r.seller_tax,"input",o,d,ao("seller"))}
            ${Se("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",o)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${Se("buyer_name","drawer-lbl-name",r.buyer_name,"input",o)}
            ${Se("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",o,d,ao("buyer"))}
            ${Se("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",o)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?Vl(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${Se("notes","drawer-lbl-notes",r.notes,"textarea",o)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(p=>`--- Page ${p.page||p.page_number||"?"} ---
${p.raw_text||p.text||""}`).join(`

`))}</pre>
        </details>
    `,o?l.querySelectorAll("[data-field]").forEach(p=>{p.addEventListener("input",onFieldEdit)}):l.querySelectorAll("[data-field]").forEach(p=>{p.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const p=n._historyId||n.history_id||null;window.bindDrawerClient(p,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const p=document.getElementById("drawer-cat-input");p&&!p.value&&!p.readOnly&&p.focus()},80)}function Ol(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function Se(e,n,a,s,o,i,r){const l=_results[_drawerIdx],m=l&&l.edits[e]!==void 0?l.edits[e]:a,d=l&&l.edits[e]!==void 0&&l.edits[e]!==a,p=escapeHtml(m??""),c=o?"":"readonly",u=s==="textarea"?`<textarea data-field="${e}" rows="2">${p}</textarea>`:`<input type="text" data-field="${e}" value="${p}">`;return`
        <div class="drawer-field ${d?"edited":""} ${c}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${u}
        </div>
    `}function ao(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function Vl(e){return`
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
    `}function Ul(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=fa;window.openDrawer=ki;window.closeDrawer=Ul;function Gl(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const s=(window._erpEndpoints||_erpEndpoints||[]).filter(function(l){return l&&l.enabled!==!1&&(l.adapter||"").toLowerCase()!=="mrerp_dms"});if(s.length===0)return;const o=document.createElement("button");o.id="drawer-ocr-push-btn",o.className="drawer-push-btn";let i;if(s.length===1){const l=s[0].name||s[0].adapter||"ERP";i=t("btn-push-to-name",{name:l}),o.title=i}else i=t("btn-push-erp")+" ▾",o.title=t("btn-push-erp-pick-tip");o.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,o.addEventListener("click",function(l){l.preventDefault(),l.stopPropagation(),s.length===1?xi(n,s[0].id):Wl(o,n,s)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(o,r):a.appendChild(o)}function Wl(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(m=>m.remove());const s=e.getBoundingClientRect(),o=document.createElement("div");o.className="drawer-push-picker history-popover",o.style.position="fixed",o.style.top=s.bottom+6+"px",o.style.left=Math.max(8,s.right-240)+"px",o.style.minWidth="220px",o.style.zIndex="12000";const i=a.map(function(m){const d=escapeHtml(m.name||m.adapter||"ERP"),p=escapeHtml((m.adapter||"").toLowerCase()),u=m.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(m.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+p+"</span>"+d+u+"</span></button>"}).join("");o.innerHTML=i,document.body.appendChild(o);const r=()=>{o.remove(),document.removeEventListener("click",l,!0)},l=m=>{!o.contains(m.target)&&m.target!==e&&!e.contains(m.target)&&r()};setTimeout(()=>document.addEventListener("click",l,!0),0),o.addEventListener("click",m=>{const d=m.target.closest("[data-ep-id]");if(!d)return;const p=d.getAttribute("data-ep-id");r(),xi(n,p)})}async function xi(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const s={history_id:e};n&&(s.endpoint_id=n);const o=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(s)}),i=await o.json();if(!o.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(s){showToast(t("erp-push-fail",{err:s.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=Gl;const Kl=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function _i(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function Yl(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function Ei(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,s=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const d=[];for(const p of _results){const c=p.invoices&&p.invoices.length>0?p.invoices:null;if(c&&c.length>1)for(let u=0;u<c.length;u++){const v=c[u]||{};d.push({filename:p.filename+" #"+(u+1)+"/"+c.length,engine:p.engine,merged_fields:v.fields||{}})}else d.push({filename:p.filename,engine:p.engine,merged_fields:p.merged_fields})}a=await apiPost("/api/ocr/export",{records:d,lang:currentLang,template:"sales_detail_th"})}else{const d=[];for(const c of _results)c.history_ids&&Array.isArray(c.history_ids)?d.push(...c.history_ids):c.history_id&&d.push(c.history_id);if(d.length===0){showToast(t("toast-export-error"),"error");return}const p=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+p,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:d,client_id:null})}),s=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let d="HTTP "+a.status;try{const c=await a.json();c&&c.detail&&(d=typeof c.detail=="string"?c.detail:JSON.stringify(c.detail))}catch(c){console.warn("[export] resp.json err.detail parse failed:",c)}const p=typeof d=="string"&&d.indexOf(".")>0?"err."+d:null;showToast(p?t(p):t("toast-export-error")+" · "+d,"error");return}const o=await a.blob();let i=s;const r=a.headers.get("X-Filename");if(r)i=r;else{const p=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(p)try{i=decodeURIComponent(p[1])}catch{}}const l=URL.createObjectURL(o),m=document.createElement("a");m.href=l,m.download=i,document.body.appendChild(m),m.click(),document.body.removeChild(m),URL.revokeObjectURL(l),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{Ei(_i())});function Jl(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=_i(),s=Kl.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
            <div class="export-dd-item ${i.id===a?"active":""}" data-tpl="${i.id}">
                <div class="export-dd-row">
                    <span class="export-dd-name">${escapeHtml(t(i.nameKey))}</span>
                    ${r}
                    ${i.id===a?'<span class="export-dd-check">✓</span>':""}
                </div>
                <div class="export-dd-desc">${escapeHtml(t(i.descKey))}</div>
            </div>
        `}).join(""),o=`
        <div class="export-dd-divider"></div>
        <div class="export-dd-item export-dd-custom" data-tpl="__custom" title="${escapeHtml(t("tpl-custom-coming"))}">
            <div class="export-dd-row">
                <span class="export-dd-name">+ ${escapeHtml(t("tpl-custom-new"))}</span>
                <span class="export-dd-badge badge-soon">${escapeHtml(t("cs-coming-soon"))}</span>
            </div>
        </div>
    `;n.innerHTML=s+o,e.appendChild(n)}function $a(){const e=document.getElementById("export-dropdown");e&&e.remove()}const Sa=document.getElementById("btn-export-arrow");Sa&&Sa.addEventListener("click",e=>{e.stopPropagation(),!Sa.disabled&&Jl()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){$a(),showToast(t("cs-coming-soon"),"info");return}Yl(a),$a(),Ei(a);return}e.target.closest("#btn-export-arrow")||$a()});function Xl(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(Xl,300);const Zl=`
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
`;(function(){const e=document.getElementById("page-history");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Zl,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();function ms(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const s=_historySelected.size;if(s>0?(e.style.display="",n.textContent=t("history-batch-count",{n:s})):e.style.display="none",a){const o=_historyState.items||[];if(o.length===0)a.checked=!1,a.indeterminate=!1;else{const i=o.filter(r=>_historySelected.has(r.id)).length;a.checked=i===o.length,a.indeterminate=i>0&&i<o.length}}}function Ql(){_historySelected.clear(),ms()}async function vs(){if(!_userInfo){setTimeout(()=>vs(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const s=_historyState.page*_historyState.pageSize,o=new URLSearchParams({limit:_historyState.pageSize,offset:s});_historyState.keyword&&o.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&o.set("client_id",String(i));const r=await fetch(`/api/history?${o}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const d=await r.json().catch(()=>({}));if((typeof d.detail=="string"?d.detail:d.detail&&d.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const l=await r.json();_historyState.items=l.items||[],_historyState.total=l.total||0;const m=new Set(_historyState.items.map(d=>d.id));for(const d of Array.from(_historySelected))m.has(d)||_historySelected.delete(d);Ii()}catch(s){console.error("load history failed",s)}finally{_historyState.loading=!1}}function Ii(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,s=document.getElementById("history-search-matches");if(s&&(s.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let o=0;a.forEach(d=>{d.confidence==="high"&&o++});const i=a.length>0?Math.round(o/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(d=>{const p=new Date(d.created_at),c=String(p.getMonth()+1).padStart(2,"0"),u=String(p.getDate()).padStart(2,"0"),v=String(p.getHours()).padStart(2,"0"),f=String(p.getMinutes()).padStart(2,"0"),y=`${c}-${u} ${v}:${f}`,b=escapeHtml(d.filename||""),h=b.length>50?b.substring(0,50)+"…":b,g=d.invoice_no?escapeHtml(d.invoice_no):h,_=[];d.seller_name&&_.push(escapeHtml(d.seller_name)),d.invoice_no&&d.filename&&_.push(h);const w=_.join(" · ")||"-",k=d.category_tag?`<span class="history-badge category">${escapeHtml(d.category_tag)}</span>`:"",x=d.source_total&&d.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:d.source_index||1,n:d.source_total}))}</span>`:"",E=d.total_amount!==null&&d.total_amount!==void 0?Number(d.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',I=[];(d.total_amount===null||d.total_amount===void 0)&&I.push(t("field-amount")),d.invoice_no||I.push(t("field-invoice-no")),d.invoice_date||I.push(t("field-invoice-date")),d.seller_name||I.push(t("field-seller-name")),I.length>0&&`${escapeHtml(d.id)}${escapeHtml(t("history-needs-review-tip")+" · "+I.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,d.edited&&`${escapeHtml(t("history-edited",{n:d.edit_count||1}))}`;const B=d.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",L=d.confidence==="high"?"high":d.confidence==="medium"?"mid":"low",$=d.confidence==="high"?t("conf-high"):d.confidence==="medium"?t("conf-medium"):t("conf-low"),S=`<span class="history-badge conf-${L}">${escapeHtml($)}</span>`;let H="";const R=d.source||"manual";return R==="email"?H=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:R==="folder"?H=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:R==="api"&&(H=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(d.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(d.id)}" ${_historySelected.has(d.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${y}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${g} ${k} ${x} ${H} ${B}</div>
                        <div class="history-cell-subtitle">${w}</div>
                    </div>
                    <div class="history-cell-amount">${E}</div>
                    <div class="history-cell-conf">${S}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(d.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),ms();const l=a.length>0?_historyState.page*_historyState.pageSize+1:0,m=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:l,to:m,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=vs;window.renderHistoryList=Ii;window.updateHistoryBatchBar=ms;window.clearHistorySelection=Ql;typeof currentRoute<"u"&&currentRoute==="history"&&vs();async function Jn(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),s=mergeFields(a.pages||[]),o={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:s,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(o),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),tc(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),nc(a.id)}catch(n){console.error("open history detail failed",n)}}async function ec(e){await Jn(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function tc(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",sc),document.getElementById("btn-push-erp").addEventListener("click",ac)}async function nc(e){}async function ac(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function sc(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const s=n.findIndex(l=>!l.is_duplicate&&!l.is_copy),o=s>=0?s:0,i=n[o].fields||(n[o].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function oc(e,n){document.querySelectorAll(".history-popover").forEach(d=>d.remove());const a=n.getBoundingClientRect(),s=(_historyState.items||[]).find(d=>d.id===e),o=s&&s.invoice_no?String(s.invoice_no):"",i=s&&s.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${o?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const l=()=>{r.remove(),document.removeEventListener("click",m,!0)},m=d=>{!r.contains(d.target)&&d.target!==n&&l()};setTimeout(()=>document.addEventListener("click",m,!0),0),r.addEventListener("click",async d=>{const p=d.target.closest("[data-act]");if(!p||p.disabled)return;const c=p.dataset.act;if(l(),c==="copy-invno"){if(!o)return;try{await navigator.clipboard.writeText(o),showToast(t("history-copy-invno-ok",{no:o}),"success")}catch{try{const v=document.createElement("textarea");v.value=o,v.style.position="fixed",v.style.opacity="0",document.body.appendChild(v),v.select(),document.execCommand("copy"),document.body.removeChild(v),showToast(t("history-copy-invno-ok",{no:o}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(c==="download-pdf"){const u=showToast(t("history-download-pdf-loading"),"loading",0);try{const v=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!v.ok)throw new Error("download failed");const f=await v.blob(),y=URL.createObjectURL(f),b=document.createElement("a");b.href=y,b.download=s&&s.filename?s.filename.endsWith(".pdf")?s.filename:s.filename+".pdf":"invoice.pdf",document.body.appendChild(b),b.click(),document.body.removeChild(b),setTimeout(()=>URL.revokeObjectURL(y),5e3),u(),showToast(t("history-download-pdf-ok"),"success")}catch{u(),showToast(t("history-download-pdf-fail"),"error")}}else if(c==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const l=r.target.closest(".history-row"),m=r.target.closest("[data-hmenu]");if(m){r.stopPropagation(),oc(m.dataset.hmenu,m);return}const d=r.target.closest("[data-review]");if(d){r.stopPropagation(),Jn(d.dataset.review);return}const p=r.target.closest("[data-fill-amount]");if(p){r.stopPropagation(),ec(p.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||l&&!r.target.closest("[data-hmenu]")&&Jn(l.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const l=r.target.closest(".history-row-check");if(!l)return;const m=l.dataset.hid;l.checked?_historySelected.add(m):_historySelected.delete(m),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const l=r.target.checked;for(const m of _historyState.items)l?_historySelected.add(m.id):_historySelected.delete(m.id);document.querySelectorAll(".history-row-check").forEach(m=>{m.checked=l}),updateHistoryBatchBar()});const s=document.getElementById("history-batch-cancel");s&&s.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const o=document.getElementById("history-batch-delete");o&&o.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const m=Array.from(_historySelected);try{const d=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:m})});if(!d.ok)throw new Error("batch delete failed");const p=await d.json();showToast(t("history-batch-done",{n:p.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(d){console.error("batch delete",d),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const l=r.target.value;document.getElementById("history-search-clear").style.display=l?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=l.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=Jn;const Wt=document.getElementById("drop-zone"),fs=document.getElementById("file-input");Wt.addEventListener("click",()=>fs.click());fs.addEventListener("change",e=>Bi(e.target.files));["dragover","dragenter"].forEach(e=>{Wt.addEventListener(e,n=>{n.preventDefault(),Wt.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{Wt.addEventListener(e,n=>{n.preventDefault(),Wt.classList.remove("drag-over")})});Wt.addEventListener("drop",e=>{e.preventDefault(),Bi(e.dataTransfer.files)});const ic=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function Ua(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function rc(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function lc(e){return rc(e)||Ua(e)||ic.test(e.name)}function Bi(e){hideAlerts();const n=Array.from(e),a=n.filter(lc);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const s=a.filter(l=>!Ua(l)),o=a.filter(Ua),i=new Set(_selectedFiles.map(l=>l.name+"_"+l.size));for(const l of s){const m=l.name+"_"+l.size;i.has(m)||(_selectedFiles.push({file:l,name:l.name,size:l.size,status:"waiting",errorKey:null,errorParams:null}),i.add(m))}if(o.length>0)try{handleCameraImages(o,"gallery")}catch(l){console.error("[upload] image route failed",l)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),ha(),hs(),fs.value=""}let Hn=!1;function ha(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(c=>c.status==="processing"||c.status==="retrying").length,s=_selectedFiles.filter(c=>c.status==="success").length,o=_selectedFiles.filter(c=>c.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),s&&r.push(`<span style="color: var(--success, #059669);">${s} ${escapeHtml(t("status-success"))}</span>`),o&&r.push(`<span style="color: var(--danger, #dc2626);">${o} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const l=Hn?t("file-list-collapse"):t("file-list-expand"),m=_selectedFiles.map((c,u)=>{let v=t("status-"+c.status);c.status==="retrying"&&(v=t("status-retrying")),c.status==="error"&&c.errorKey&&(v=t(c.errorKey,c.errorParams||{}));const f=c.status==="processing"||c.status==="retrying"?'<span class="spinner"></span>':"",y=c.status==="error"&&c.canRetry?`<button class="file-retry-btn" data-retry-idx="${u}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",b=c.status==="success"&&c.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</span>
                ${b}
                <span class="file-status ${c.status}">${f}${v}</span>
                ${y}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(l)}</button>`:""}
        </div>
        <ul class="file-list-body${Hn?" expanded":""}" id="file-list-body">
            ${m}
        </ul>
    `;const d=document.getElementById("file-list-toggle");d&&d.addEventListener("click",()=>{Hn=!Hn,ha()});const p=document.getElementById("file-list-body");p&&!p.dataset.retryBound&&(p.dataset.retryBound="1",p.addEventListener("click",async c=>{const u=c.target.closest(".file-retry-btn");if(!u)return;const v=parseInt(u.dataset.retryIdx||"-1",10);if(v<0||v>=_selectedFiles.length)return;const f=_selectedFiles[v];!f||f.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(f,!0)}))}function hs(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),s=_selectedFiles.some(o=>o.status==="waiting");e.disabled=_selectedFiles.length===0||!s,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],ha(),renderResults(),hs(),hideAlerts()});window.renderFileList=ha;window.updateStartButton=hs;const cc=`
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
`;$e("camera-tips-modal",cc);async function Xn(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const s=new Image;s.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),s.onload=()=>{const o=[],i=s.naturalWidth,r=s.naturalHeight;(i<1e3||r<1e3)&&o.push("low_res");try{const l=document.createElement("canvas");l.width=64,l.height=64;const m=l.getContext("2d");m.drawImage(s,0,0,64,64);const d=m.getImageData(0,0,64,64).data;let p=0,c=0;for(let v=0;v<d.length;v+=4)p+=.299*d[v]+.587*d[v+1]+.114*d[v+2],c++;const u=c?p/c:128;u<70?o.push("too_dark"):u>235&&o.push("too_bright"),n({warnings:o,width:i,height:r,brightness:u})}catch{n({warnings:o,width:i,height:r,brightness:128})}},s.src=a.result},a.readAsDataURL(e)})}async function Li(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,s=297,o=new n({unit:"mm",format:"a4",orientation:"p"});for(let d=0;d<e.length;d++){const p=e[d],{dataUrl:c,naturalW:u,naturalH:v}=await dc(p);d>0&&o.addPage("a4","p");const f=u/v;let y=a-10,b=y/f;b>s-10&&(b=s-10,y=b*f);const h=(a-y)/2,g=(s-b)/2,_=p.type==="image/png"?"PNG":"JPEG";o.addImage(c,_,h,g,y,b,void 0,"FAST")}const i=o.output("blob"),r=new Date,l=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),m=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${l}${m}.pdf`,{type:"application/pdf"})}function dc(e){return new Promise((n,a)=>{const s=new FileReader;s.onerror=a,s.onload=()=>{const o=new Image;o.onerror=a,o.onload=()=>n({dataUrl:s.result,naturalW:o.naturalWidth,naturalH:o.naturalHeight}),o.src=s.result},s.readAsDataURL(e)})}(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),s=document.getElementById("camera-input");if(!n)return;n.style.display="";const o=document.getElementById("btn-scan-doc");o&&s&&(o.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await uc()||s.click()}),s.addEventListener("change",async l=>{const m=Array.from(l.target.files||[]);if(l.target.value="",m.length!==0)for(const d of m)await Ga([d],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=l=>async m=>{const d=Array.from(m.target.files||[]);if(m.target.value="",d.length===0)return;const p=d.filter(u=>u.type==="application/pdf"||/\.pdf$/i.test(u.name)),c=d.filter(u=>!p.includes(u));p.length>0&&await pc(p),c.length>0&&await Ga(c,l)};a&&a.addEventListener("change",r("gallery"))})();async function pc(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function uc(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),s=document.getElementById("camera-tips-cancel"),o=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}o&&(o.checked=!1),n.style.display="flex";const i=l=>{n.style.display="none",o&&o.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,s&&(s.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(l)},r=l=>{l.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),s&&(s.onclick=()=>i(!1)),n.onclick=l=>{l.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}let Ue=[],Lt=null;async function Ga(e,n){if(hideAlerts(),!(!e||e.length===0)){var a=typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice";if(a==="thai_id_card"){for(const o of e)_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null});const s=getMaxFiles();_selectedFiles.length>s&&(showAlert("warn",t("alert-file-count",{n:s})),_selectedFiles=_selectedFiles.slice(0,s)),renderFileList(),updateStartButton();return}if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let s=0;s<30&&(await new Promise(o=>setTimeout(o,100)),!(window.jspdf&&window.jspdf.jsPDF));s++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const s=e[0];let o={};try{o=await Xn(s)}catch{}Ue.push({file:s,quality:o}),Lt="camera",zt();return}if(n==="gallery"&&(e.length>=2||Ue.length>0)){for(const s of e){let o={};try{o=await Xn(s)}catch{}Ue.push({file:s,quality:o})}Lt="gallery",zt();return}await $i(e)}}async function mc(e){const n=new Set;for(const s of e)try{((await Xn(s)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const s=await Li(e);s&&_selectedFiles.push({file:s,name:s.name,size:s.size,status:"waiting",errorKey:null,errorParams:null})}catch(s){console.error("[camera] convert failed",s),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function zt(){let e=document.getElementById("camera-buffer-bar");if(Ue.length===0){e&&e.remove(),Lt=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=Ue.length,a=n>=2,s=Lt==="gallery",o=s?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?s?i=`
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
            <button type="button" class="btn btn-ghost btn-sm" data-cbb-action="more">${escapeHtml(o)}</button>
            ${i}
        </div>
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{Ue=[],Lt=null,zt()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const m=s?"gallery-input":"camera-input",d=document.getElementById(m);d&&d.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const m=Ue.map(d=>d.file);Ue=[],Lt=null,zt(),await mc(m)});const l=e.querySelector('[data-cbb-action="separate"]');l&&(l.onclick=async()=>{const m=Ue.map(d=>d.file);Ue=[],Lt=null,zt(),await $i(m)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{Ue.length>0&&zt()});async function $i(e){const n=new Set;let a=0;for(const o of e)try{((await Xn(o)).warnings||[]).forEach(l=>n.add(l));const r=await Li([o]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const s=getMaxFiles();_selectedFiles.length>s&&(showAlert("warn",t("alert-file-count",{n:s})),_selectedFiles=_selectedFiles.slice(0,s)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}window.handleCameraImages=Ga;(function(){var e="pearnly_ocr_doc_mode",n=!1,a=!1;function s(u){return typeof escapeHtml=="function"?escapeHtml(u==null?"":String(u)):String(u??"")}function o(){try{return localStorage.getItem(e)==="thai_id_card"?"thai_id_card":"invoice"}catch{return"invoice"}}window.getOcrDocumentMode=function(){return n?o():"invoice"};function i(){var u=document.getElementById("drop-zone");return u?u.closest(".card"):null}function r(){var u=i();if(!u)return null;var v=u.querySelector("#ocr-doc-mode");if(v)return v;var f=u.querySelector(".section-head");return v=document.createElement("div"),v.id="ocr-doc-mode",v.className="ocr-doc-mode",v.setAttribute("role","tablist"),v.style.cssText="display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;",f&&f.parentNode?f.parentNode.insertBefore(v,f.nextSibling):u.insertBefore(v,u.firstChild),v}function l(u,v,f){return'<button type="button" class="ocr-doc-seg'+(f?" active":"")+'" data-doc-mode="'+u+'" role="tab" aria-selected="'+(f?"true":"false")+'" style="border:none;background:'+(f?"var(--card,#fff)":"transparent")+";color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:"+(f?"600":"500")+";padding:6px 16px;border-radius:7px;cursor:pointer;box-shadow:"+(f?"0 1px 3px rgba(0,0,0,.08)":"none")+';transition:background .15s;">'+s(t(v))+"</button>"}function m(){var u=r();if(u){if(!n){u.style.display="none";return}var v=o();u.style.display="flex",u.innerHTML=l("invoice","ocr-mode-invoice",v==="invoice")+l("thai_id_card","ocr-mode-id-card",v==="thai_id_card")}}function d(u){try{localStorage.setItem(e,u==="thai_id_card"?"thai_id_card":"invoice")}catch{}m();try{document.dispatchEvent(new CustomEvent("ocr-doc-mode-change",{detail:{mode:window.getOcrDocumentMode()}}))}catch{}}async function p(u){if(!(a&&!u)){var v=localStorage.getItem("mrpilot_token");if(v)try{var f=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+v}});if(!f.ok)return;var y=await f.json(),b=y&&y.items||[];n=b.some(function(h){return h&&(h.adapter||"").toLowerCase()==="mrerp_dms"&&h.enabled!==!1}),a=!0,window._dmsHasEndpoint=n,m()}catch{}}}window._refreshOcrDocMode=function(){p(!0)},document.addEventListener("click",function(u){var v=u.target.closest(".ocr-doc-seg");v&&v.getAttribute("data-doc-mode")&&(u.preventDefault(),d(v.getAttribute("data-doc-mode")))}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("ocr-doc-mode",m);function c(){r(),m(),p(!1)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),window.addEventListener("hashchange",function(){((location.hash||"").indexOf("ocr")>=0||location.hash===""||location.hash==="#home")&&setTimeout(function(){r(),p(!1)},60)})})();(function(){function e(i){return typeof escapeHtml=="function"?escapeHtml(i==null?"":String(i)):String(i??"")}function n(){var i=(function(){var l=document.getElementById("drop-zone");return l?l.closest(".card"):null})();if(!i||!i.parentNode)return null;var r=document.getElementById("dms-id-card-result");return r||(r=document.createElement("div"),r.id="dms-id-card-result",r.className="card",r.style.cssText="display:none;margin-top:16px;",i.parentNode.insertBefore(r,i.nextSibling),r)}function a(i,r){return'<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);"><span style="color:var(--muted,#6b6b66);font-size:13px;">'+e(t(i))+'</span><span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">'+e(r||"—")+"</span></div>"}function s(i){if(!i)return"";var r=[i.house_no,i.road,i.subdistrict,i.district,i.province,i.zipcode].filter(function(l){return l});return r.join(" ")||i.address_raw||""}function o(i){var r=i&&i.status||"failed",l,m,d;return r==="success"?(l="#0a7a2c",m="#d6f5e0",d="dms-result-status-success"):r==="needs_review"?(l="#9a6b00",m="#fdf0d0",d="dms-result-status-needs-review"):r==="skipped"?(l="#5d5d57",m="#eee",d="dms-result-status-skipped"):(l="#b3261e",m="#fbe0de",d="dms-result-status-failed"),'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:'+l+";background:"+m+';">'+e(t(d))+"</span>"}window.renderDmsIdCardResult=function(i){var r=n();if(r){i=i||{};var l=i.id_card||{},m=l.address||{},d=i.dms_push||{},p=d.status||(i.ok?"success":"failed"),c="";p==="success"&&(c=a("dms-result-customer",d.customer_id)+a("dms-result-booking",d.booking_no));var u=p==="failed"||p==="needs_review"?'<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">'+e(t("dms-result-retry"))+"</button>":"",v="";if(p==="failed"&&d.error_code){var f="dms-err-"+String(d.error_code).toLowerCase(),y=t(f);(!y||y===f)&&(y=t("dms-err-err_dms_unexpected")),v='<div style="margin-top:8px;color:#b3261e;font-size:12px;">'+e(y)+"</div>"}r.style.display="",r.innerHTML='<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;"><div class="section-title">'+e(t("dms-result-title"))+"</div>"+o(d)+'</div><div style="margin-top:8px;">'+a("dms-result-name",(l.first_name||"")+" "+(l.last_name||""))+a("dms-result-id",l.people_id_masked)+a("dms-result-birthday",l.birthday_be)+a("dms-result-address",s(m))+c+"</div>"+v+u}},window.clearDmsIdCardResult=function(){var i=document.getElementById("dms-id-card-result");i&&(i.style.display="none",i.innerHTML="")},document.addEventListener("click",function(i){i.target.closest("#dms-id-card-retry")&&(i.preventDefault(),typeof window._dmsRetryIdCard=="function"&&window._dmsRetryIdCard())})})();async function Si(e){let n;if(e)n=_selectedFiles.find(a=>a.file===e)||{file:e,name:e.name,status:"waiting"};else{const a=_selectedFiles.filter(s=>s.status==="waiting");if(!a.length)return;n=a[0]}window._dmsLastFile=n.file,n.status="processing",typeof renderFileList=="function"&&renderFileList();try{const a=new FormData;a.append("file",n.file,n.name),a.append("push","true");const s=await fetch("/api/dms/id-card-booking",{method:"POST",headers:{Authorization:"Bearer "+token},body:a});if(s.status===401||s.status===403){const i=await s.clone().json().catch(()=>({})),r=i&&i.detail,l=typeof r=="string"?r:r&&r.code||"";if(!l||l.startsWith("auth.")){localStorage.removeItem("mrpilot_token"),showToast(t("alert-session"),"error"),setTimeout(()=>{window.location.href="/"},1200);return}}const o=await s.json().catch(()=>({}));if(!s.ok){n.status="error";const i=o&&o.detail&&(o.detail.code||o.detail)||"unknown";n.errorKey="err."+i,n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:String(i)}});return}n.status=o.ok||o.dms_push&&o.dms_push.status==="needs_review"?"success":"error",typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult(o),typeof updateStartButton=="function"&&updateStartButton()}catch{n.status="error",n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:"network"}})}}window._dmsRetryIdCard=function(){window._dmsLastFile&&Si(window._dmsLastFile)};document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,(typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice")==="thai_id_card"){try{await Si()}finally{const c=document.getElementById("btn-start");c&&(c.disabled=!1)}return}if(_userInfo&&_userInfo.plan==="free"){const c=await fetch("/api/health").then(u=>u.json()).catch(()=>null);c&&!c.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const n=_selectedFiles.filter(c=>c.status==="waiting"),a=6;async function s(c,u){if(window._ocrAborted)return c.status="cancelled",c.errorKey=null,renderFileList(),{};c.status=u?"retrying":"processing",c.canRetry=!1,renderFileList();const v=new AbortController,f=setTimeout(()=>v.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(v);try{const y=new FormData;y.append("file",c.file,c.name);try{if(typeof window.getCurrentClientId=="function"){const w=window.getCurrentClientId();w!=null&&y.append("client_id",String(w))}}catch{}const b=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:y,signal:v.signal});if(clearTimeout(f),window._ocrCtrls.delete(v),b.status===401||b.status===403){const k=await b.clone().json().catch(()=>({})),x=k&&k.detail,E=typeof x=="string"?x:x&&x.code||"";if(!E||E.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),E==="auth.session_revoked")_showSessionRevokedModal();else{const I=E==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(I),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}E==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!b.ok){const k=(await b.json().catch(()=>({}))).detail;return typeof k=="string"?(c.errorKey="err."+k,c.errorParams=null):k&&k.code?(c.errorKey="err."+k.code,c.errorParams={...k,mb:_quota.max_file_size_mb}):(c.errorKey="err.unknown",c.errorParams=null),(c.errorKey==="err.unknown"||c.errorKey==="err.ocr.engine_error")&&(b.status===429?c.errorKey="err.rate_limit":b.status===502||b.status===503||b.status===504?c.errorKey="err.gemini_overloaded":b.status>=500&&(c.errorKey="err.server")),c.status="error",c.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(c.errorKey||""),renderFileList(),{}}const h=await b.json();c.status="success",c.fromCache=!!h.from_cache;const g=mergeFields(h.pages),_=h.confidence||(g.items&&g.items.length>0?"high":"low");if(_results.push({filename:h.filename,pages:h.pages,page_count:h.page_count,elapsed_ms:h.elapsed_ms,engine:h.engine,merged_fields:g,edits:{},confidence:_,history_id:h.history_id,history_ids:h.history_ids||[],invoice_count:h.invoice_count||1,invoices:h.invoices||[],archive_name:h.archive_name||null,category_tag:h.category_tag||null,auto_pushed:!!h.auto_pushed,typhoon_enhanced:!!h.typhoon_enhanced,typhoon_pages:h.typhoon_pages||[],from_cache:!!h.from_cache}),h.invoice_count&&h.invoice_count>1&&showToast(t("multi-invoice-toast",{file:h.filename,n:h.invoice_count}),"success"),h.missed_invoice_warnings&&h.missed_invoice_warnings.length){const w=h.missed_invoice_warnings.map(function(k){return k.page}).filter(function(k){return k!=null});showToast(t("missed-invoice-warn",{file:h.filename,pages:w.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",h.missed_invoice_warnings)}if(h.typhoon_enhanced&&h.typhoon_pages&&h.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:h.filename,n:h.typhoon_pages.length}),"success"),h.fallback_used){const w=h.engine_chain||[],k=h.engine||"";let x;k==="typhoon_nvidia"?x="fallback-typhoon-nvidia-toast":k==="easyocr"?x="fallback-easyocr-toast":x="fallback-generic-toast",showToast(t(x,{file:h.filename}),"warn"),console.info("[OCR Chain]",w)}if(h.from_cache&&showToast(t("cache-hit-toast",{file:h.filename}),"info"),h.duplicate_warnings&&h.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const w of h.duplicate_warnings)window._dupQueue.push({filename:h.filename,...w})}return h.auto_pushed&&showToast(t("auto-push-fired",{file:h.filename}),"info"),h.quota&&h.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=h.quota.used_this_month,_userInfo.tenant_used=h.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(y){clearTimeout(f);try{window._ocrCtrls&&window._ocrCtrls.delete(v)}catch{}console.error("[Upload] failed for",c.file.name,y);const b=y&&(y.name==="AbortError"||y==="timeout"),h=b&&(v.signal.reason==="timeout"||y==="timeout"),g=y&&y.message&&/NetworkError|Failed to fetch/i.test(y.message);return b&&(v.signal.reason==="user_stop"||window._ocrAborted)?(c.status="cancelled",c.errorKey=null,c.canRetry=!1,renderFileList(),{}):(h?c.errorKey="err.timeout":b?c.errorKey="err.aborted":g?c.errorKey="err.network":(c.errorKey="err.unknown",c.errorParams={msg:y&&y.message?y.message:String(y)}),c.status="error",!u&&!window._ocrAborted&&(g||h)&&navigator.onLine!==!1&&(c.canRetry=!0,renderFileList(),await new Promise(w=>setTimeout(w,2e3)),c.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?s(c,!0):(c.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=s;let o=0,i=!1;async function r(){for(;o<n.length&&!i&&!window._ocrAborted;){const c=o++,u=await s(n[c]);if(u&&u.abort){i=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const l=document.getElementById("btn-start"),m=document.getElementById("btn-stop");l&&(l.style.display="none"),m&&(m.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(n)}catch{}const d=[];for(let c=0;c<Math.min(a,n.length);c++)d.push(r());await Promise.all(d);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}l&&(l.style.display=""),m&&(m.style.display="none");const p=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const c={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const v of n)if(v.status==="success")c.success++;else if(v.status==="cancelled")c.cancelled++;else if(v.status==="error"){const f=v.errorKey||"";f==="err.network"?c.network++:f==="err.timeout"||f==="err.aborted"?c.timeout++:f.indexOf("quota")>=0||f==="err.monthly_limit_exceeded"?c.quota++:f==="err.gemini_overloaded"||f==="err.server"?c.overloaded++:f==="err.rate_limit"?c.rate++:c.other++}const u=n.length;p?showToast(vc(c,u),"warn",4e3):u>1&&c.network+c.timeout+c.quota+c.overloaded+c.rate+c.other>0&&showToast(fc(c),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function vc(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function fc(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});function Ci(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",s=n?"dup-desc-exact":"dup-desc-likely",o=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=v=>v!=null?Number(v).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",l=v=>v||"—",m=v=>{try{const f=new Date(v);return`${f.getFullYear()}-${String(f.getMonth()+1).padStart(2,"0")}-${String(f.getDate()).padStart(2,"0")}`}catch{return v}},d=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",p=(e.matched_fields||[]).map(v=>{const f=t("dup-field-"+v.replace("_","-"))||v;return`<span class="dup-field-chip">${escapeHtml(f)}</span>`}).join(" "),c=document.createElement("div");c.className="log-detail-modal",c.innerHTML=`
        <div class="log-detail-box dup-dialog">
            <div class="dup-head" style="background:${i};">
                <div class="dup-title" style="color:${o};">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:22px;height:22px;vertical-align:-5px;margin-right:6px;">
                        <path d="M10 2.5L1 17h18L10 2.5z"/><path d="M10 8v4M10 14v0.5"/>
                    </svg>
                    ${escapeHtml(t(a))}
                </div>
                <button class="log-detail-close dup-close" type="button">✕</button>
            </div>
            <div class="dup-body">
                <div class="dup-desc">${escapeHtml(t(s))}</div>
                <div class="dup-source">
                    <div class="dup-source-label">${escapeHtml(t("dup-current-file"))}${escapeHtml(d)}</div>
                    <div class="dup-source-name">${escapeHtml(e.filename)}</div>
                </div>
                <div class="dup-matched-label">${escapeHtml(t("dup-matched-on"))} ${p}</div>
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
                        <tr><td>${escapeHtml(t("dup-field-invoice-date"))}</td><td>${escapeHtml(l(e.current.invoice_date))}</td><td>${escapeHtml(l(e.match.invoice_date))}</td></tr>
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
    `,document.body.appendChild(c);const u=()=>{c.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(Ci,200)};c.querySelector(".dup-close").addEventListener("click",u),c.querySelector('[data-action="view"]').addEventListener("click",()=>{const v=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(v)},400),u()}),c.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const v=e.new_history_id;if(!v){u();return}try{(await fetch(`/api/history/${encodeURIComponent(v)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}u()}),c.querySelector('[data-action="keep"]').addEventListener("click",u)}window.showDuplicateDialog=Ci;function St(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function an(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function hc(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?St("time-just-now","刚刚"):a<3600?Math.floor(a/60)+St("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+St("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+St("time-day-ago-suffix"," 天前")}catch{return""}}async function gs(){Ti();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),s=document.getElementById("dash-kpi-plan"),o=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const l={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[m,d,p]=await Promise.all([fetch("/api/me/tenant-usage",{headers:l}).then(b=>b.ok?b.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:l}).then(b=>b.ok?b.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:l}).then(b=>b.ok?b.json():null).catch(()=>null)]),c=m&&m.ocr_this_month||0;let u=0;const v=d&&(d.items||d.history||d)||[],f=Array.isArray(v)?v:[];f.forEach(b=>{(b.status==="pending"||b.status==="reviewing")&&u++});const y=p&&(p.total||p.count||p.pending||0)||0;if(e&&(e.textContent=an(c)),n&&(n.textContent=an(u)),a&&(a.textContent=an(y)),r&&(y>0?(r.style.display="",r.textContent=y):r.style.display="none"),s&&m){const b=m.ocr_this_month||0,h=m.quota||0;s.textContent=an(b),o&&(o.textContent=h?b+" / "+an(h)+" 张":St("dash-kpi-plan-sub","本月用量"))}if(i)if(f.length===0)i.innerHTML='<div class="dash-recent-empty">'+St("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const b=f.slice(0,5).map(h=>{const g=(h.invoice_no||h.filename||h.id||"").toString(),_=(h.supplier_name||h.buyer_name||h.client_name||h.notes||"").toString(),w=hc(h.created_at||h.upload_time||h.date),k=x=>String(x).replace(/[&<>"']/g,E=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[E]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+k(g)+'">'+k(g)+'</span><span class="dash-recent-mid" title="'+k(_)+'">'+k(_)+'</span><span class="dash-recent-time">'+k(w)+"</span></div>"}).join("");i.innerHTML=b}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+St("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=gs;async function Ti(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),s=document.getElementById("dash-kpi-balance-sub"),o=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},l=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!l.ok){e.style.display="none",o&&(o.textContent="—"),i&&(i.textContent="");return}const m=await l.json(),d=!!m.is_owner,p=!!m.is_billing_exempt;if(!d)e.style.display="none";else if(e.style.display="",p)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),s&&(s.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const u=typeof m.balance_thb=="number"?m.balance_thb:0;if(a&&(a.textContent="฿"+u.toFixed(2),a.className=u<50?"dash-kpi-val dash-red":"dash-kpi-val"),s){const v=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",f=u<50?"#dc2626":"#6b7280",y=b=>typeof window.escapeHtml=="function"?window.escapeHtml(b):String(b).replace(/[&<>"']/g,h=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[h]);s.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+f+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+y(v)+"</a>"}}const c=typeof m.pages_this_month=="number"?m.pages_this_month:typeof m.my_invoice_count=="number"?m.my_invoice_count:0;if(n.style.display="",o&&(o.textContent=String(c)),i){const u=c>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",v=typeof window.t=="function"?window.t(u,{used:c}):c+" pages";i.textContent=v}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",o&&(o.textContent="—")}}window.loadCreditsCard=Ti;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(gs,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&gs()});function ne(e){return(typeof window.t=="function"?window.t(e):null)||e}function bs(){return localStorage.getItem("mrpilot_token")||""}function Q(e){return document.getElementById(e)}var Nn=null,un=null;function Hi(){un||(un=setInterval(function(){if(!document.hidden){var e=bs();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;Nn!==null&&a>Nn&&(window.showToast&&window.showToast(ne("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Nn=a}}).catch(function(){}))}},3e4))}function gc(){un&&(clearInterval(un),un=null),Nn=null}window._startCreditsPoll=Hi;window._stopCreditsPoll=gc;Hi();var ys=null,ws=0;function bc(){if(!Q("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),yc()}}function Mi(){var e=function(n,a){var s=Q(n);s&&(s.textContent=a)};e("tv2-title",ne("topup-title")),e("tv2-sl1",ne("topup-step1")),e("tv2-sl2",ne("topup-step2")),e("tv2-sl3",ne("topup-step3")),e("tv2-al",ne("topup-amount-label")),e("tv2-bl",ne("topup-bank-label")),e("tv2-copy",ne("topup-copy-account")),e("tv2-dt",ne("topup-slip-drop")),e("tv2-pl",ne("topup-payer-label")),e("tv2-nl",ne("topup-note-label"))}function xn(e){[1,2,3].forEach(function(o){var i=Q("tv2-s"+o);i&&(i.style.display=o===e?"":"none");var r=Q("tv2-d"+o);r&&r.classList.toggle("active",o<=e)});var n=Q("tv2-back"),a=Q("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=ne("topup-btn-cancel")):n&&(n.style.display="",n.textContent=ne("topup-btn-back")),a&&(a.textContent=ne(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var s=Q("tv2-bn");s&&(s.innerHTML=ne("topup-bank-note").replace("{amount}","<strong>฿"+Number(ws).toLocaleString()+"</strong>"))}}function Wa(){for(var e=1;e<=3;e++){var n=Q("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function Zn(e){var n=Q(e);n&&(n.textContent="",n.style.display="none")}function mn(e,n){var a=Q(e);a&&(a.textContent=n,a.style.display="")}function so(e){var n=Q("tv2-dt");n&&(n.textContent=e.name);var a=Q("tv2-drop");a&&a.classList.add("has-file"),Zn("tv2-se")}function yc(){var e=Q("topup-v2-ov");Q("tv2-close").addEventListener("click",rn),e.addEventListener("click",function(i){i.target===e&&rn()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&rn()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(m){m.classList.remove("active")}),r.classList.add("active");var l=Q("tv2-amt");l&&(l.value=r.dataset.val,Zn("tv2-ae"))}});var n=Q("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),Zn("tv2-ae")});var a=Q("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=ne("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var s=Q("tv2-drop"),o=Q("tv2-file");s&&(s.addEventListener("click",function(){o&&o.click()}),s.addEventListener("dragover",function(i){i.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",function(){s.classList.remove("drag-over")}),s.addEventListener("drop",function(i){i.preventDefault(),s.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&so(r)})),o&&o.addEventListener("change",function(){o.files[0]&&so(o.files[0])}),Q("tv2-back").addEventListener("click",function(){var i=Wa();if(i<=1){rn();return}xn(i-1)}),Q("tv2-next").addEventListener("click",function(){var i=Wa();i===1?wc():i===2?xn(3):kc()})}async function wc(){var e=Q("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){mn("tv2-ae",ne("topup-amount-invalid"));return}if(n>5e5){mn("tv2-ae",ne("topup-amount-too-large"));return}ws=n;var a=Q("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var s=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+bs()},body:JSON.stringify({amount_thb:n})});if(!s.ok){var o=await s.text(),i=ne("topup-submit-fail");try{var r=JSON.parse(o),l=r.detail;if(Array.isArray(l)&&l.length){var m=l[0]&&l[0].type||"";m.indexOf("less_than")>=0?i=ne("topup-amount-too-large"):(m.indexOf("greater_than")>=0||m.indexOf("parsing")>=0)&&(i=ne("topup-amount-invalid"))}else typeof l=="string"&&(i=l)}catch{}throw new Error(i)}var d=await s.json();ys=d.request_id,xn(2)}catch(p){mn("tv2-ae",p.message||ne("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=ne("topup-btn-next"))}}async function kc(){var e=Q("tv2-file");if(!e||!e.files||!e.files[0]){mn("tv2-se",ne("topup-slip-required"));return}var n=Q("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var s=Q("tv2-payer"),o=Q("tv2-note");s&&s.value.trim()&&a.append("payer_name",s.value.trim()),o&&o.value.trim()&&a.append("note",o.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+ys,{method:"POST",headers:{Authorization:"Bearer "+bs()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(ne("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(ne("topup-pending"),"info"),rn()}catch(l){mn("tv2-ue",ne("topup-upload-fail")+" · "+l.message),n&&(n.disabled=!1,n.textContent=ne("topup-btn-submit"))}}function rn(){var e=Q("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){bc(),ys=null,ws=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var s=Q(a);s&&(s.value="")});var e=Q("tv2-file");e&&(e.value="");var n=Q("tv2-drop");n&&n.classList.remove("has-file","drag-over"),Q("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){Zn(a)}),Mi(),xn(1),Q("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=Q("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(Mi(),xn(Wa()))});const xc=`
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

    `;$e("page-test-center",xc);const Ai="v118.28.5",ks="pearnly_tc_results_"+Ai,ot=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}],ee={results:{},logFilter:"all",bound:!1,renderScheduled:!1,checkN:0};function Pe(e,n,a){let s=typeof t=="function"?t(e):null;return(!s||s===e)&&(s=n),a&&Object.keys(a).forEach(function(o){s=String(s).replace("{"+o+"}",String(a[o]))}),s}function _c(){try{const e=localStorage.getItem(ks);ee.results=e?JSON.parse(e):{},(typeof ee.results!="object"||!ee.results)&&(ee.results={})}catch{ee.results={}}}function oo(){try{localStorage.setItem(ks,JSON.stringify(ee.results))}catch{}}function xs(e){const n=new Date(e),a=function(s){return s<10?"0"+s:""+s};return a(n.getHours())+":"+a(n.getMinutes())+":"+a(n.getSeconds())}function Oe(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function it(e,n){try{typeof showToast=="function"?showToast(e,n||"info"):alert(e)}catch{}}function io(e){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(e).then(function(){it(Pe("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){Ca(e)}):Ca(e)}catch{Ca(e)}}function Ca(e){try{const n=document.createElement("textarea");n.value=e,n.style.position="fixed",n.style.opacity="0",document.body.appendChild(n),n.select();const a=document.execCommand("copy");document.body.removeChild(n),it(a?Pe("tc-toast-copied","已复制"):Pe("tc-toast-copy-fail","复制失败"),a?"success":"error")}catch{it(Pe("tc-toast-copy-fail","复制失败"),"error")}}function Ec(){const e=[],n=new Date,a=_userInfo&&(_userInfo.email||_userInfo.username)||"—";e.push("# Pearnly "+Ai+" 测试结果"),e.push("- 账号:"+a),e.push("- 时间:"+n.toISOString().replace("T"," ").slice(0,19));const s=ot.length,o=ot.filter(function(p){return ee.results[p.id]==="pass"}).length,i=ot.filter(function(p){return ee.results[p.id]==="fail"}).length,r=ot.filter(function(p){return ee.results[p.id]==="skip"}).length,l=s-o-i-r;e.push("- 进度:"+(o+i+r)+" / "+s+" · ✅ "+o+" · ❌ "+i+" · ⏭ "+r+" · 未测 "+l),e.push(""),e.push("| ID | 描述 | 状态 |"),e.push("|---|---|---|"),ot.forEach(function(p){const c=ee.results[p.id],u=c==="pass"?"✅":c==="fail"?"❌":c==="skip"?"⏭":"⬜";e.push("| "+p.id+" | "+p.desc.replace(/\|/g,"\\|")+" | "+u+" |")});const m=ot.filter(function(p){return ee.results[p.id]==="fail"});m.length>0&&(e.push(""),e.push("## ❌ 失败项"),m.forEach(function(p){e.push("- **"+p.id+"** · "+p.desc)}));const d=(window._pearnlyTcLogs||[]).slice(-30).reverse();return d.length>0&&(e.push(""),e.push("## 🔴 异常日志(最近 "+d.length+" 条)"),d.forEach(function(p){if(e.push("- `"+xs(p.ts)+"` · **"+p.type+"** · "+p.summary),p.detail){let c;try{c=JSON.stringify(p.detail)}catch{c=String(p.detail)}c&&c!=="{}"&&e.push("  - "+c.slice(0,600))}})),e.join(`
`)}function Ic(e){const n=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(n.length===0)return"(暂无异常日志)";const a=["# Pearnly 异常日志(最近 "+n.length+" 条)"],s=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return a.push("- 账号:"+s),a.push("- 当前页:"+(currentRoute||"?")),a.push("- UA:"+navigator.userAgent),a.push(""),n.forEach(function(o){if(a.push("## `"+xs(o.ts)+"` · "+o.type),a.push("- "+o.summary),o.detail){a.push("```");try{a.push(JSON.stringify(o.detail,null,2).slice(0,2e3))}catch{a.push(String(o.detail).slice(0,2e3))}a.push("```")}}),a.join(`
`)}(function(){function e(){const f=document.getElementById("tc-account-chip"),y=document.getElementById("tc-progress-chip");if(f&&(f.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),y){const b=ot.length,h=ot.filter(function(g){return ee.results[g.id]}).length;y.textContent=h+" / "+b}}function n(){const f=document.getElementById("tc-checklist-body");if(!f)return;const y={};ot.forEach(function(h){y[h.group]||(y[h.group]=[]),y[h.group].push(h)});const b=[];Object.keys(y).forEach(function(h){b.push('<div class="tc-checklist-group">'),b.push('<div class="tc-checklist-group-title">'+Oe(h)+"</div>"),y[h].forEach(function(g){const _=ee.results[g.id]||"",w=_?"is-"+_:"";b.push('<div class="tc-check-item '+w+'" data-id="'+Oe(g.id)+'"><div class="tc-check-id">'+Oe(g.id)+'</div><div class="tc-check-desc">'+Oe(g.desc)+'</div><div class="tc-check-actions">'+a(g.id,"pass",_)+a(g.id,"fail",_)+a(g.id,"skip",_)+"</div></div>")}),b.push("</div>")}),f.innerHTML=b.join("")}function a(f,y,b){const h=b===y,g={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},_={pass:Pe("tc-status-pass","通过"),fail:Pe("tc-status-fail","失败"),skip:Pe("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(h?"is-active "+y:"")+'" data-id="'+Oe(f)+'" data-kind="'+y+'" title="'+Oe(_[y])+'">'+g[y]+"</button>"}function s(f){return ee.logFilter==="all"?!0:ee.logFilter==="js_error"?f.type==="js_error"||f.type==="promise_error":ee.logFilter==="api"?f.type==="api_error"||f.type==="api_fail":ee.logFilter==="api_slow"?f.type==="api_slow":ee.logFilter==="console"?f.type==="console_error"||f.type==="console_warn":!0}function o(){const f=document.getElementById("tc-logs-body"),y=document.getElementById("tc-logs-count");if(!f)return;const b=(window._pearnlyTcLogs||[]).slice().reverse(),h=b.filter(s);if(y&&(y.textContent=String(b.length)),h.length===0){f.innerHTML='<div class="tc-logs-empty">'+Oe(Pe("tc-logs-empty","暂无异常"))+"</div>";return}const g=h.slice(0,100).map(function(_){const w=typeof _.detail=="object"?JSON.stringify(_.detail,null,2):String(_.detail||"");return'<div class="tc-log-item t-'+Oe(_.type)+'" data-ts="'+_.ts+'"><span class="tc-log-time">'+xs(_.ts)+'</span><span class="tc-log-type">'+Oe(_.type)+'</span><div class="tc-log-summary">'+Oe(_.summary)+'<div class="tc-log-detail">'+Oe(w)+"</div></div></div>"}).join("");f.innerHTML=g,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(_){_.classList.toggle("active",_.getAttribute("data-filter")===ee.logFilter)})}function i(){ee.renderScheduled||(ee.renderScheduled=!0,setTimeout(function(){ee.renderScheduled=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&o(),r()},200))}window._tcOnNewLog=i;function r(){const f=document.getElementById("nav-test-badge");if(!f)return;const y=(window._pearnlyTcLogs||[]).filter(function(b){return b.type==="js_error"||b.type==="promise_error"||b.type==="api_error"||b.type==="api_fail"||b.type==="console_error"}).length;y>0?(f.style.display="",f.textContent=y>99?"99+":String(y)):f.style.display="none"}function l(){e(),n(),o(),r()}function m(){const f=Date.now();fetch("/api/health").then(function(y){const b=Date.now()-f;y.ok?it(Pe("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:b}),"success"):it(Pe("tc-toast-health-fail","后端无响应")+" ("+y.status+")","error")}).catch(function(){it(Pe("tc-toast-health-fail","后端无响应"),"error")})}function d(){try{localStorage.removeItem(ks),localStorage.removeItem("pearnly_current_client_id"),ee.results={},(window._pearnlyTcLogs||[]).length=0,ee.logFilter="all",window.setCurrentClientId}catch{}l(),it(Pe("tc-toast-cleared","session 状态已清空"),"success")}function p(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(f){return f.json()}).then(function(f){window._clientsCache=f.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),it("客户缓存已刷新 · "+(f.clients||[]).length+" 个客户","success")}).catch(function(){it("刷新失败","error")})}catch{}}function c(){if(ee.bound||!document.getElementById("page-test-center"))return;ee.bound=!0;const y=document.getElementById("tc-checklist-body");y&&y.addEventListener("click",function(B){const L=B.target.closest(".tc-status-btn");if(!L)return;const $=L.getAttribute("data-id"),S=L.getAttribute("data-kind");!$||!S||(ee.results[$]===S?delete ee.results[$]:ee.results[$]=S,oo(),n(),e())});const b=document.getElementById("tc-btn-reset-checklist");b&&b.addEventListener("click",function(){ee.results={},oo(),n(),e()});const h=document.getElementById("tc-btn-copy-all");h&&h.addEventListener("click",function(){io(Ec())});const g=document.getElementById("tc-btn-copy-logs");g&&g.addEventListener("click",function(){io(Ic())});const _=document.getElementById("tc-btn-clear-logs");_&&_.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,o(),r()});const w=document.getElementById("tc-logs-filter");w&&w.addEventListener("click",function(B){const L=B.target.closest(".tc-filter-chip");L&&(ee.logFilter=L.getAttribute("data-filter")||"all",o())});const k=document.getElementById("tc-logs-body");k&&k.addEventListener("click",function(B){const L=B.target.closest(".tc-log-item");L&&L.classList.toggle("expanded")});const x=document.getElementById("tc-tool-health");x&&x.addEventListener("click",m);const E=document.getElementById("tc-tool-clear-session");E&&E.addEventListener("click",d);const I=document.getElementById("tc-tool-reload-clients");I&&I.addEventListener("click",p)}function u(){}window._tcApplyVisibility=u;const v=setInterval(function(){ee.checkN++,_userInfo&&clearInterval(v),ee.checkN>60&&clearInterval(v)},500);window.loadTestCenterPage=function(){_c(),c(),l()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){r(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&l()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(h,g){if(typeof window.t=="function"){const _=window.t(h);if(_&&_!==h)return _}return g}function s(){const h=window._userInfo||{},g=String(h.role||"").toLowerCase(),_=String(h.tenant_role||"").toLowerCase();return h.is_super_admin===!0||h.is_owner===!0||g==="owner"||g==="admin"||_==="owner"||_==="admin"}function o(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const h=localStorage.getItem(e);if(!h||h==="null"||h==="0"||h==="")return null;const g=parseInt(h,10);return isNaN(g)?null:g}function r(h){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:h,mode:o()}}))}catch{}}function l(h){const g=i();h==null||h===0?localStorage.removeItem(e):(localStorage.setItem(e,String(h)),localStorage.setItem(n,"client")),String(g)!==String(h)&&r(h)}function m(){const h=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),h!=null&&r(null)}async function d(){try{const h=window.apiGet;if(typeof h!="function")return[];const g=await h("/api/workspace/clients");return g&&(g.clients||g.items)||[]}catch{return[]}}async function p(h){if(o()==="client"&&i()!=null)return typeof h=="function"&&h(),!0;const g=a("ws-need-client","这个功能需要先选择工作空间"),_=a("ws-btn-pick","选择工作空间"),w=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(g,{okText:_,cancelText:w})&&c(h):window.confirm(g+`

[`+_+" / "+w+"]")&&c(h),!1}async function c(h){const g=await d();if(typeof h=="function"&&o()!=="personal"&&g.length===1){l(Number(g[0].id)),h();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:g,active:i(),onPersonal:m,onPick:function(_){l(Number(_)),typeof h=="function"&&h()},emptyHint:g.length?null:s()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!g.length){const _=s()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(_,"info")}}function u(h){const g=h||document.getElementById("workspace-switcher-root");if(!g)return;const _=o(),w=i();let k,x;if(_==="client"&&w!=null){const B=(window._workspaceClientsCache||[]).find(L=>Number(L.id)===Number(w));k=f("building"),x=B?B.name:a("ws-current-label","当前工作空间")}else k=f("user"),x=a("ws-personal","个人事务");g.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+k+'<span class="ws-ctrl-label">'+v(x)+"</span></button>";const E=g.querySelector("#ws-ctrl-btn");E&&E.addEventListener("click",()=>c(null))}function v(h){return String(h??"").replace(/[&<>"']/g,function(g){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[g]})}function f(h){const g='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return h==="building"?g+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':g+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function y(h){h=h||{};const g=h.clients||[],_=h.active,w=document.getElementById("ws-modal");w&&w.remove();const k=document.createElement("div");k.id="ws-modal",k.className="ws-modal";const E='<button type="button" class="ws-modal-item'+(o()==="personal"||_==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+f("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+v(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+v(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let I="";if(g.length){const H=['<option value="">'+v(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(g.map(function(R){const G=_!=null&&Number(_)===Number(R.id);return'<option value="'+v(R.id)+'"'+(G?" selected":"")+">"+v(R.name||"#"+R.id)+"</option>"}));I='<div class="ws-modal-item ws-modal-item-account"><span class="ws-modal-item-ic">'+f("building")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;flex:1;"><span class="ws-modal-item-name">'+v(a("ws-select-label","账套主体"))+'</span><select class="ws-modal-select" data-ws-select="1" style="margin-top:6px;width:100%;">'+H.join("")+"</select></span></div>"}const B=!g.length&&h.emptyHint?'<div class="ws-modal-empty">'+v(h.emptyHint)+"</div>":"",L='<div class="ws-modal-hint" style="font-size:12px;color:#6b7280;padding:10px 4px 2px;line-height:1.5;white-space:normal;">'+v(a("ws-add-hint","如需新增账套主体,请前往「客户管理」添加"))+"</div>";k.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+v(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+v(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+E+I+"</div>"+B+L+"</div>",document.body.appendChild(k);const $=k.querySelector("[data-ws-select]");$&&$.addEventListener("change",function(){const H=$.value;H&&(typeof h.onPick=="function"&&h.onPick(H),S(),u())});function S(){k.remove()}k.addEventListener("click",function(H){if(H.target===k||H.target.closest("[data-ws-close]")){S();return}if(H.target.closest("[data-ws-personal]")){typeof h.onPersonal=="function"&&h.onPersonal(),S(),u();return}const G=H.target.closest("[data-ws-pick]");if(G){const se=G.getAttribute("data-ws-pick");typeof h.onPick=="function"&&h.onPick(se),S(),u();return}})}window.openWorkspaceChooserUI=y,window.addEventListener("pearnly:workspace-changed",function(){u()}),window.getWorkMode=o,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=l,window.enterPersonalMode=m,window.requireWorkspace=p,window.openWorkspaceChooser=c,window.renderWorkspaceControl=u,window.fetchWorkspaceClients=d;function b(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){c(null)},800)}catch{}}d().then(h=>{window._workspaceClientsCache=h,u(),b()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",u)})();(function(){const e=w=>document.querySelector('[data-num-target="'+w+'"]');function n(w){if(!w)return t("reconcile-last-activity-none");try{const k=new Date(w),x=new Date,E=x-k;if(E/6e4<5)return t("reconcile-last-activity-just-now");if(k.toDateString()===x.toDateString())return t("reconcile-last-activity-today");const B=Math.max(1,Math.floor(E/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",B)}catch{return t("reconcile-last-activity-none")}}function a(w,k,x){const E=e(w);E&&(E.textContent=x?"-":String(k),E.classList.toggle("is-empty",!!x))}function s(w){const k=document.getElementById("reconcile-error");k&&(k.style.display=w?"flex":"none")}function o(w){const k=document.getElementById("reconcile-empty");k&&(k.style.display=w?"flex":"none")}function i(w,k){const x=document.getElementById("reconcile-last-activity");x&&(x.textContent=w,x.classList.toggle("has-data",!!k))}function r(w){const k=!w||(w.total_sessions||0)===0;a("pending",w.pending||0,k),a("matched",w.matched||0,k),a("unmatched",w.unmatched||0,k),i(n(w.last_activity_at),!!w.last_activity_at),s(!1),o(k)}function l(w){const k=w.toUpperCase();return k==="KBANK"?"bank-chip-kbank":k==="SCB"?"bank-chip-scb":k==="BBL"?"bank-chip-bbl":k==="KTB"?"bank-chip-ktb":k==="TTB"?"bank-chip-ttb":"bank-chip-other"}function m(w,k){const x=E=>E?String(E).slice(0,10):"?";return!w&&!k?"":x(w)+" ~ "+x(k)}function d(w){return w==null?"":String(w).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function p(w){const k=document.getElementById("reconcile-recent"),x=document.getElementById("reconcile-recent-list");if(!k||!x)return;const E=(w||[]).slice(0,20);if(E.length===0){k.style.display="none";return}k.style.display="",o(!1),x.innerHTML=E.map(I=>{const B=I.parse_status==="parse_failed",L=I.bank_code||"OTHER",$=I.account_last4?" ···"+d(I.account_last4):"",S=m(I.period_start,I.period_end),H=d(I.source_filename||""),R=Number(I.tx_count||0),G=B?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",R)+"</span>";return'<div class="recon-card" data-session-id="'+d(I.id)+'" data-session-name="'+H+'"><span class="bank-chip '+l(L)+'">'+d(L)+'</span><div class="recon-card-main"><div class="recon-card-title">'+H+$+'</div><div class="recon-card-sub">'+d(S)+'</div></div><div class="recon-card-right">'+G+'</div><button class="recon-card-trash" data-trash="'+d(I.id)+'" title="'+d(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),x.querySelectorAll(".recon-card").forEach(I=>{I.addEventListener("click",B=>{B.target.closest(".recon-card-trash")||(I.dataset.sessionId,c())})}),x.querySelectorAll(".recon-card-trash").forEach(I=>{I.addEventListener("click",B=>{B.stopPropagation();const L=I.dataset.trash,$=I.closest(".recon-card"),S=$&&$.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(L,S)})})}function c(w){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const k=document.querySelector('[data-recon-tab="bank"]');k&&k.click()},150)}function u(){s(!0),o(!1)}function v(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const w=document.querySelector('[data-recon-tab="bank"]');w&&w.click()},150)}async function f(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),s(!1),o(!1);const w=document.getElementById("reconcile-recent");w&&(w.style.display="none");const k={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[x,E]=await Promise.all([fetch("/api/bank-recon/stats",{headers:k}),fetch("/api/bank-recon/sessions?limit=20",{headers:k})]);if(!x.ok)throw new Error("http "+x.status);const I=await x.json(),B=E.ok?await E.json():[];r(I||{}),p(B||[])}catch(x){console.warn("[reconcile] load failed",x),u()}}function y(w){if(!w||!w.length)return;const k="Bearer "+(localStorage.getItem("mrpilot_token")||"");let x=0;const E=w.length;Array.from(w).forEach(function(I){const B=new FormData;B.append("file",I,I.name);const L=new XMLHttpRequest;L.open("POST","/api/bank-recon/upload"),L.setRequestHeader("Authorization",k),L.onload=function(){x++;try{const $=JSON.parse(L.responseText);L.status===200&&$.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",$.tx_count),"success"):showToast(I.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(I.name+" "+(t("upload-failed")||"上传失败"),"error")}x===E&&setTimeout(f,600)},L.onerror=function(){x++,showToast(I.name+" "+(t("upload-failed")||"上传失败"),"error"),x===E&&setTimeout(f,600)},L.send(B)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function b(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const w=document.getElementById("reconcile-bank-file-input");w&&w.addEventListener("change",function(){y(this.files),this.value=""}),document.addEventListener("click",k=>{if(k.target.closest("#btn-reconcile-upload-top")||k.target.closest("#btn-reconcile-upload-empty")){v();return}if(k.target.closest("#btn-reconcile-retry")){f();return}if(k.target.closest("#btn-reconcile-dev-seed")){_();return}})}const h=["468b50c1-5593-4fd6-990d-515ce8085563"];function g(){const w=document.getElementById("btn-reconcile-dev-seed");if(!w)return;const k=typeof _userInfo<"u"?_userInfo:null,x=k&&k.id&&h.indexOf(String(k.id))>=0;w.style.display=x?"":"none"}async function _(){try{const w=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!w.ok)throw new Error("seed:"+w.status);const k=await w.json(),x=(t("reconcile-dev-seed-ok")||"").replace("{n}",k.tx_count||0);showToast(x,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const E=document.querySelector('[data-auto-tab="bank"]');E&&E.click(),k.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(k.session_id)},300)}catch(w){console.warn("[reconcile] dev seed failed",w),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){b(),g(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await f()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&f().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");o&&a[n][o]&&(s.textContent=a[n][o])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function s(){return document.getElementById("assign-select-all")}function o(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const f=a();if(f){if(!e.clients.length){f.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}f.innerHTML=e.clients.map(y=>{const b=String(y.id),h=e.selected.has(b)?"checked":"",g=escapeHtml(y.name||y.label||"#"+b),_=y.code?'<span class="assign-row-code">'+escapeHtml(y.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(b)+'" '+h+'><span class="assign-row-name">'+g+"</span>"+_+"</label>"}).join(""),l()}}function l(){const f=o();if(f){const b=t("assign-selected-count")||"已选 {n} / {total}";f.textContent=b.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const y=s();y&&(y.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function m(){const f=i();f&&(f.textContent=e.employeeName?" · "+e.employeeName:"")}async function d(f,y){e.employeeId=f,e.employeeName=y||"",e.opened=!0,e.selected=new Set,e.clients=[],m();const b=a();b&&(b.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const h=n();h&&(h.style.display="flex");try{const[g,_]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(f)+"/assignments")]);e.clients=g&&g.clients||[];const w=_&&_.client_ids||[];e.selected=new Set(w.map(String)),r()}catch(g){console.error("[assign-clients] load failed",g);const _=a();_&&(_.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function p(){e.opened=!1;const f=n();f&&(f.style.display="none")}async function c(){if(!e.employeeId)return;const f=Array.from(e.selected).map(b=>parseInt(b,10)).filter(b=>!isNaN(b)),y=document.getElementById("assign-modal-save");y&&(y.disabled=!0);try{const b=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:f});b&&b.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",f.length),"success"),p(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(b){console.error("[assign-clients] save failed",b),showToast(t("assign-save-failed")||"保存失败","error")}finally{y&&(y.disabled=!1)}}function u(){const f=n();if(!f||f.dataset.bound==="1")return;f.dataset.bound="1";const y=document.getElementById("assign-modal-close");y&&y.addEventListener("click",p);const b=document.getElementById("assign-modal-cancel");b&&b.addEventListener("click",p);const h=document.getElementById("assign-modal-save");h&&h.addEventListener("click",c),f.addEventListener("click",function(w){w.target===f&&p()});const g=s();g&&g.addEventListener("change",function(){g.checked?e.selected=new Set(e.clients.map(w=>String(w.id))):e.selected=new Set,r()});const _=a();_&&_.addEventListener("change",function(w){const k=w.target.closest('input[type="checkbox"][data-cid]');if(!k)return;const x=k.dataset.cid;k.checked?e.selected.add(x):e.selected.delete(x),l()})}function v(){e.opened&&(m(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",v),window.openAssignClientsModal=function(f,y){u(),d(f,y)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(p){if(!p)return"";try{return new Date(p).toLocaleString()}catch{return p}}function a(p){const c=document.getElementById("access-log-table");c&&(c.innerHTML='<div class="access-log-empty">'+escapeHtml(p)+"</div>");const u=document.getElementById("access-log-pager");u&&(u.innerHTML="")}function s(){const p=document.getElementById("access-log-table");if(!p)return;const c=e.rows||[];if(!c.length){a(t("set-access-log-empty"));return}const u=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,v=c.map(function(f){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(f.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(f.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(f.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(f.target_name||f.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(f.ip||"-")}</div>
                </div>`}).join("");p.innerHTML=u+v}function o(){const p=document.getElementById("access-log-pager");if(!p)return;const c=e.total||0;if(!c){p.innerHTML="";return}const u=e.page||1,v=e.per_page,f=Math.max(1,Math.ceil(c/v)),y=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",c),b=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",u).replace("{t}",f);p.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(y)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u-1}" ${u<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(b)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u+1}" ${u>=f?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(p){const c=localStorage.getItem("mrpilot_token");if(c){e.page=p||1,a(t("set-access-log-loading"));try{const u="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),v=await fetch(u,{headers:{Authorization:"Bearer "+c}});if(v.status===403){a(t("set-access-log-empty"));return}if(!v.ok)throw new Error("http_"+v.status);const f=await v.json();e.rows=f.logs||[],e.total=f.total||0,e.loaded=!0,s(),o()}catch{a(t("set-access-log-fail"))}}}async function r(){const p=localStorage.getItem("mrpilot_token");if(p)try{const c="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),u=await fetch(c,{headers:{Authorization:"Bearer "+p}});if(!u.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const v=await u.blob(),f=document.createElement("a"),y=URL.createObjectURL(v);f.href=y,f.download="pearnly_access_log.csv",document.body.appendChild(f),f.click(),setTimeout(function(){URL.revokeObjectURL(y),f.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function l(){const p=document.querySelectorAll(".set-tab-owner-only"),c=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));p.forEach(function(u){u.style.display=c?"":"none"})}document.addEventListener("click",function(p){if(p.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(p.target.closest("#access-log-csv-btn")){p.preventDefault(),r();return}const v=p.target.closest(".access-log-pager-btn[data-access-log-page]");if(v&&!v.disabled){const f=parseInt(v.dataset.accessLogPage,10);i(f)}}),document.addEventListener("input",function(p){p.target&&p.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(p.target.value||"").trim(),i(1)},350))});let m=0;const d=setInterval(function(){m++,_userInfo&&(l(),clearInterval(d)),m>60&&clearInterval(d)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){l(),e.loaded&&(s(),o())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
                    </div>
                </div>

                <div class="form-group">
                    <label class="form-label" for="notif-new-name" data-i18n="notif-new-name-label">规则名称</label>
                    <input type="text" id="notif-new-name" class="form-input" maxlength="100" data-i18n-placeholder="notif-new-name-ph" placeholder="例:大额发票推老板">
                </div>

                <div id="notif-line-check" class="notif-line-check" style="display:none;"></div>
            </div>
            <div class="modal-foot">
                <button class="btn btn-ghost" id="notif-new-cancel" type="button" data-i18n="btn-cancel">取消</button>
                <button class="btn btn-primary" id="notif-new-save" type="button" data-i18n="notif-new-save">保存规则</button>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");o&&a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");o&&a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e=k=>document.getElementById(k);async function n(k,x){return await fetch(k,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(x||{})})}async function a(k){return await fetch(k,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let s=null;async function o(){try{s=await apiGet("/api/line/binding")}catch{s={bound:!1}}return s}function i(k,x){if(!k)return;k.style.display="",k.className="notif-line-check "+(x?"bound":"unbound");const E=x?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';k.innerHTML=E+"<span>"+escapeHtml(t(x?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(k){if(!k)return"-";try{const x=new Date(k),E=(x.getMonth()+1).toString().padStart(2,"0"),I=x.getDate().toString().padStart(2,"0"),B=x.getHours().toString().padStart(2,"0"),L=x.getMinutes().toString().padStart(2,"0");return`${E}-${I} ${B}:${L}`}catch{return k}}function l(k){const x=e("notif-rules-list"),E=e("notif-rules-empty"),I=e("notif-rules-count");if(!(!x||!E)){if(I.textContent=String(k.length),I.className="auto-status-pill "+(k.length>0?"active":"none"),!k.length){E.style.display="",x.style.display="none",x.innerHTML="";return}E.style.display="none",x.style.display="",x.innerHTML=k.map(B=>{const L="notif-rule-exception-tag";let S=[];B.enabled||S.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const H=S.length?S.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${B.enabled?"":" disabled"}" data-rule-id="${B.id}">
                    <span class="notif-rule-tmpl-badge ">${escapeHtml(t(L))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(B.name)}</div>
                        <div class="notif-rule-meta">${H}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${B.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function m(k){const x=e("notif-logs-list");if(x){if(!k.length){x.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}x.innerHTML=k.map(E=>{const I=E.status==="sent",B=E.event_type==="exception_high"?"notif-event-exception-high":"notif-event-test-send",L=I?"":" · "+escapeHtml(E.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${I?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(B))}</div>
                        <div class="notif-log-meta">${escapeHtml(E.template_code||"-")}${L}</div>
                    </div>
                    <div class="notif-log-time">${r(E.sent_at)}</div>
                </div>`}).join("")}}async function d(){try{const k=await apiGet("/api/notifications/rules");p=k&&k.items||[],l(p)}catch(k){console.warn("load rules fail",k)}try{const k=await apiGet("/api/notifications/logs?limit=20");c=k&&k.items||[],m(c)}catch(k){console.warn("load logs fail",k)}}let p=null,c=null;function u(){p&&l(p),c&&m(c);const k=e("notif-new-modal");k&&k.style.display!=="none"&&s&&i(e("notif-line-check"),!!(s&&s.bound))}function v(){const k=e("notif-new-modal");k&&(k.style.display="",e("notif-new-name").value="",document.querySelectorAll('input[name="notif-template"]').forEach(x=>x.checked=!1),o().then(x=>i(e("notif-line-check"),!!(x&&x.bound))))}function f(){const k=e("notif-new-modal");k&&(k.style.display="none")}function y(){if(!document.querySelector('input[name="notif-template"]:checked'))return;const x=e("notif-new-name");x&&!x.value.trim()&&(x.value=t("notif-tmpl-exception-name"))}async function b(){const k=document.querySelector('input[name="notif-template"]:checked');if(!k){showToast(t("notif-new-template"),"error");return}const x=(e("notif-new-name").value||"").trim();if(!x){showToast(t("notif-name-required"),"error");return}const E={name:x,template_code:k.value,params:{},enabled:!0};try{const I=await apiPost("/api/notifications/rules",E);if(I&&I.ok)showToast(t("notif-toast-created"),"success"),f(),d();else{const B=await(I&&I.json&&I.json().catch(()=>({})))||{};showToast(B&&B.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function h(k,x,E){if(k==="toggle"){const I=E.classList.contains("on"),B=await n("/api/notifications/rules/"+x,{enabled:!I});B&&B.ok?(showToast(t(I?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),d()):showToast("toggle failed","error");return}if(k==="test"){const I=await o();if(!I||!I.bound){showToast(t("notif-line-error-bind-first"),"error");return}const B=await apiPost("/api/notifications/rules/"+x+"/test",{});if(B&&B.ok)showToast(t("notif-toast-test-sent"),"success"),d();else{const L=await(B&&B.json&&B.json().catch(()=>({})))||{},$=L&&L.detail||"";showToast($||t("notif-toast-test-failed"),"error"),d()}return}if(k==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const B=await a("/api/notifications/rules/"+x);B&&B.ok?(showToast(t("notif-toast-deleted"),"success"),d()):showToast("delete failed","error");return}}let g=!1;function _(){if(g)return;g=!0;const k=e("notif-btn-new");k&&k.addEventListener("click",v);const x=e("notif-btn-refresh-logs");x&&x.addEventListener("click",d);const E=e("notif-new-close");E&&E.addEventListener("click",f);const I=e("notif-new-cancel");I&&I.addEventListener("click",f);const B=e("notif-new-save");B&&B.addEventListener("click",b),document.querySelectorAll('input[name="notif-template"]').forEach(S=>{S.addEventListener("change",y)});const L=e("notif-rules-list");L&&L.addEventListener("click",S=>{const H=S.target.closest("button[data-action]");if(!H)return;const R=H.closest("[data-rule-id]");R&&h(H.getAttribute("data-action"),R.getAttribute("data-rule-id"),H)});const $=e("notif-new-modal");$&&$.addEventListener("click",S=>{S.target===$&&f()})}async function w(){_(),await d()}window._loadNotificationsPanel=w,window._rerenderNotifications=u})();(function(){function n(h,g){try{return window.t&&window.t(h)||g}catch{return g}}function a(){var h="";try{h=localStorage.getItem("mrpilot_token")||""}catch{}return h?{Authorization:"Bearer "+h}:{}}var s=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function o(){if(!document.getElementById("recon-batch-style")){var h=document.createElement("style");h.id="recon-batch-style",h.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(h)}}function i(h){return h?h.dataset&&h.dataset.taskId?h.dataset.taskId:h.dataset&&h.dataset.taskid?h.dataset.taskid:"":""}function r(h){var g=document.getElementById(h.tbody);if(!g)return null;var _=g.closest("table");if(!_)return null;var w=_.querySelector("thead");if(!w)return null;if(w._reconReady)return w;var k=w.querySelector("tr");if(!k)return null;if(k.classList.add("recon-thead-default"),!k.querySelector(".recon-master-cb")){var x=document.createElement("th");x.className="recon-sel-cell";var E=document.createElement("input");E.type="checkbox",E.className="recon-master-cb",E.setAttribute("aria-label","select all"),E.addEventListener("change",function(){p(h,E.checked)}),x.appendChild(E),k.insertBefore(x,k.firstElementChild)}var I=k.children[1];I&&!I.classList.contains("recon-time-col")&&I.classList.add("recon-time-col");var B=k.children.length,L=document.createElement("tr");L.className="recon-thead-batch";var $=document.createElement("th");$.className="recon-sel-cell";var S=document.createElement("input");S.type="checkbox",S.className="recon-master-cb",S.checked=!0,S.setAttribute("aria-label","select all"),S.addEventListener("change",function(){p(h,S.checked)}),$.appendChild(S);var H=document.createElement("th");return H.setAttribute("colspan",String(B-1)),H.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',L.appendChild($),L.appendChild(H),w.appendChild(L),H.querySelector("[data-recon-del]").addEventListener("click",function(){f(h)}),H.querySelector("[data-recon-clear]").addEventListener("click",function(){v(h)}),w._reconReady=!0,u(h),w}function l(h){var g=document.getElementById(h.tbody);if(g){var _=g.querySelectorAll("tr");_.forEach(function(w){var k=i(w);if(k&&!w.querySelector(".recon-sel-cb")){var x=w.querySelector("td");if(x){var E=document.createElement("td");E.className="recon-sel-cell";var I=document.createElement("input");I.type="checkbox",I.className="recon-sel-cb",I.dataset.taskId=k,I.dataset.kind=h.kind,I.addEventListener("click",function(L){L.stopPropagation()}),I.addEventListener("change",function(){c(h)}),E.appendChild(I),w.insertBefore(E,x);var B=w.children[1];B&&!B.classList.contains("recon-time-col")&&B.classList.add("recon-time-col")}}}),c(h)}}function m(h){var g=document.getElementById(h.tbody);return g?Array.prototype.slice.call(g.querySelectorAll(".recon-sel-cb")):[]}function d(h){return m(h).filter(function(g){return g.checked}).map(function(g){return g.dataset.taskId})}function p(h,g){m(h).forEach(function(_){_.checked=!!g}),c(h)}function c(h){var g=d(h),_=m(h),w=document.getElementById(h.tbody);if(w){var k=w.closest("table"),x=k&&k.querySelector("thead");if(x){g.length>0?x.classList.add("recon-batch-mode"):x.classList.remove("recon-batch-mode"),x.querySelectorAll(".recon-master-cb").forEach(function(I){if(_.length===0){I.checked=!1,I.indeterminate=!1;return}g.length===_.length?(I.checked=!0,I.indeterminate=!1):g.length===0?(I.checked=!1,I.indeterminate=!1):(I.checked=!1,I.indeterminate=!0)});var E=x.querySelector("[data-recon-count]");E&&(E.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",g.length))}}}function u(h){var g=document.getElementById(h.tbody);if(g){var _=g.closest("table"),w=_&&_.querySelector("thead");if(w){var k=w.querySelector("[data-recon-del-label]"),x=w.querySelector("[data-recon-clear]");k&&(k.textContent=n("recon-batch-delete","批量删除")),x&&(x.textContent=n("recon-batch-clear","取消")),c(h)}}}function v(h){m(h).forEach(function(g){g.checked=!1}),c(h)}async function f(h){var g=d(h);if(g.length){var _=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",g.length),w=!1;try{typeof window.pearnlyConfirm=="function"?w=await window.pearnlyConfirm(_,n("recon-batch-delete-title","批量删除")):w=window.confirm(_)}catch{w=!1}if(w)try{var k=Object.assign({"Content-Type":"application/json"},a()),x=h.kind==="glv"?g.map(function(L){return parseInt(L,10)}):g,E=await fetch(h.api,{method:"POST",headers:k,body:JSON.stringify({ids:x})});if(!E.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var I=await E.json(),B=I&&(I.deleted!=null?I.deleted:I.count)||g.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",B),"success"),h.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function y(h){r(h),l(h);var g=document.getElementById(h.tbody);if(!(!g||g._reconBatchWatched)){g._reconBatchWatched=!0;var _=new MutationObserver(function(){l(h)});_.observe(g,{childList:!0,subtree:!1})}}function b(){o(),s.forEach(y),document.querySelectorAll(".recon-batch-bar").forEach(function(h){try{h.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",b):b(),setTimeout(b,1500),setTimeout(b,4e3),document.addEventListener("keydown",function(h){h.key==="Escape"&&s.forEach(function(g){d(g).length>0&&v(g)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){s.forEach(u)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,s="pilot_ob_dismiss",o="pilot_ob_done";window.maybeShowOnboarding=function(d){};function i(d){n=d;for(let u=1;u<=a;u++){const v=document.getElementById("ob-step-"+u);v&&(v.style.display=u===d?"block":"none")}document.querySelectorAll(".ob-dot").forEach(u=>{const v=parseInt(u.dataset.step,10);u.classList.toggle("active",v===d),u.classList.toggle("done",v<d)});const p=document.getElementById("ob-step-label");p&&(p.textContent=d+" / "+a);const c=document.getElementById("ob-next");if(c&&(c.textContent=d===a?t("ob-finish"):t("ob-next")),d===4){const u=document.getElementById("ob-line-input");u&&(u.value=e.line_id||"")}}function r(d){const p=document.querySelector(".onboarding-modal");if(!p)return;let c=p.querySelector(".ob-feedback");c||(c=document.createElement("div"),c.className="ob-feedback",p.appendChild(c)),c.textContent=d,c.classList.add("show"),setTimeout(()=>c.classList.remove("show"),1800)}document.addEventListener("click",d=>{const p=d.target.closest(".ob-option");if(!p)return;const c=p.parentElement;if(!c||!c.classList.contains("ob-options"))return;c.querySelectorAll(".ob-option").forEach(v=>v.classList.remove("selected")),p.classList.add("selected");const u=p.dataset.value;c.id==="ob-role-options"?e.role=u:c.id==="ob-volume-options"?e.monthly_volume=u:c.id==="ob-country-options"&&(e.country=u)}),document.addEventListener("click",d=>{d.target.id==="ob-skip"&&l()}),document.addEventListener("click",d=>{if(d.target.id==="ob-next"){if(n===4){const p=document.getElementById("ob-line-input");e.line_id=(p&&p.value||"").trim().replace(/^@+/,"")}l()}}),document.addEventListener("click",d=>{if(d.target.closest("#ob-close")){localStorage.setItem(s,String(Date.now()));const p=document.getElementById("onboarding-modal");p&&(p.style.display="none")}});function l(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):m()}async function m(){const d=document.getElementById("onboarding-modal");localStorage.setItem(o,"1"),localStorage.removeItem(s);const p={};if(e.role&&(p.role=e.role),e.monthly_volume&&(p.monthly_volume=e.monthly_volume),e.country&&(p.country=e.country),e.line_id&&(p.line_id=e.line_id),Object.keys(p).length===0){d&&(d.style.display="none");return}try{const c=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(p)});c.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,p),setTimeout(()=>{d&&(d.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(p)),console.warn("onboarding profile save failed",c.status),r(t("ob-fb-saved-local")),setTimeout(()=>{d&&(d.style.display="none")},1500))}catch(c){console.error("onboarding submit",c),localStorage.setItem("pilot_ob_pending",JSON.stringify(p)),d&&(d.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");o&&a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");o&&a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();(function(){const e=document.getElementById("archive-token-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");o&&a[n][o]&&(s.textContent=a[n][o])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,s=!1;const o={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function l(){return"DHL Express (Thailand) Co., Ltd."}function m(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:l(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadArchiveSettings=()=>d();async function d(){const w=!!(_userInfo&&_userInfo.can_customize_archive);s=!w;const k=document.getElementById("archive-upgrade-banner");k&&(k.style.display=w?"none":"");const x=document.getElementById("archive-plus-badge");x&&(x.style.display=w?"none":"");try{const E=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!E.ok)throw new Error("load failed");const I=await E.json();e=Array.isArray(I.name_template)?I.name_template:[],n=I.folder_strategy||"by_month_seller"}catch(E){console.error("load archive settings failed",E),showToast(t("archive-load-failed"),"error");return}p(),c(),u(),v()}function p(){const w=document.getElementById("archive-rule-canvas");if(w){if(e.length===0){w.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}w.innerHTML=e.map((k,x)=>{const E=i[k.type]||{label:k.type},I=o[k.type]||"",B=k.type==="sep"?`"${escapeHtml(k.val||"_")}"`:escapeHtml(t(E.label));return`
                <span class="archive-token ${k.type}"
                      data-token-idx="${x}"
                      draggable="${s?"false":"true"}">
                    <span class="token-icon">${I}</span>
                    <span class="token-label">${B}</span>
                </span>
            `}).join("")}}function c(){const w=document.getElementById("archive-field-palette");if(!w)return;const k=["date","seller","category","amount","invoice","buyer","sep"];w.innerHTML=k.map(x=>{const E=i[x],I=o[x]||"";return`
                <button class="archive-palette-btn ${x}" data-add-field="${x}" ${s?"disabled":""}>
                    <span class="token-icon">${I}</span>
                    <span>${escapeHtml(t(E.label))}</span>
                </button>
            `}).join("")}function u(){document.querySelectorAll('input[name="folder-strategy"]').forEach(w=>{w.checked=w.value===n,w.disabled=s})}async function v(){const w=document.getElementById("archive-preview-name"),k=document.getElementById("archive-preview-hint");if(k&&(k.textContent=t("archive-preview-hint",{category:r()})),!!w){if(e.length===0){w.textContent="-";return}try{const E=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:m().merged_fields,name_template:e})})).json();w.textContent=(E.name||"-")+".pdf"}catch{w.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const w=document.getElementById("archive-rule-modal");!w||w.style.display==="none"||(p(),c(),v())};let f=-1;document.addEventListener("dragstart",w=>{const k=w.target.closest(".archive-token");!k||s||(f=parseInt(k.dataset.tokenIdx,10),k.classList.add("dragging"),w.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",w=>{document.querySelectorAll(".archive-token").forEach(k=>k.classList.remove("dragging","drop-target")),f=-1}),document.addEventListener("dragover",w=>{const k=w.target.closest(".archive-token");k&&(w.preventDefault(),w.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(x=>x.classList.remove("drop-target")),k.classList.add("drop-target"))}),document.addEventListener("drop",w=>{const k=w.target.closest(".archive-token");if(!k||f<0||s)return;w.preventDefault();const x=parseInt(k.dataset.tokenIdx,10);if(x===f)return;const E=e.splice(f,1)[0];e.splice(x,0,E),f=-1,p(),v()}),document.addEventListener("click",w=>{if(w.target.closest("#btn-open-archive-rule")||w.target.closest("#btn-open-archive-rule-from-settings")){const I=document.getElementById("archive-rule-modal");I&&(I.style.display="",d());return}if(w.target.closest("#archive-rule-modal-close")||w.target.id==="archive-rule-modal"){const I=document.getElementById("archive-rule-modal");I&&(I.style.display="none");return}const k=w.target.closest(".settings-nav-item");if(k){switchSettingsTab(k.dataset.settingsTab);return}if(s&&w.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const x=w.target.closest("[data-add-field]");if(x){const I=x.dataset.addField,B=i[I],L={type:I,...B.defaultCfg};e.push(L),p(),v();return}const E=w.target.closest(".archive-token");if(E&&!s){y(parseInt(E.dataset.tokenIdx,10));return}if(w.target.closest("#btn-archive-save"))return g();if(w.target.closest("#btn-archive-reset"))return _();(w.target.closest("#archive-token-close")||w.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),w.target.closest("#btn-archive-token-ok")&&b(),w.target.closest("#btn-archive-token-delete")&&h()}),document.addEventListener("change",w=>{w.target.name==="folder-strategy"&&(n=w.target.value)});function y(w){a=w;const k=e[w];if(!k)return;const x=document.getElementById("archive-token-body");let E="";k.type==="date"?E=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${k.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${k.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${k.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${k.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:k.type==="seller"?E=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${k.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:k.type==="amount"?E=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${k.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:k.type==="sep"?E=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${k.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${k.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${k.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(k.val)?"":escapeHtml(k.val||"")}">
                    </div>
                </div>`:E=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,x.innerHTML=E,document.getElementById("archive-token-modal").style.display="",x.querySelectorAll(".sep-chip").forEach(I=>{I.addEventListener("click",()=>{x.querySelectorAll(".sep-chip").forEach(L=>L.classList.remove("active")),I.classList.add("active");const B=document.getElementById("token-sep-custom");B&&(B.value="")})})}function b(){const w=e[a];if(w){if(w.type==="date")w.format=document.getElementById("token-date-format").value;else if(w.type==="seller")w.short=document.getElementById("token-seller-short").checked;else if(w.type==="amount")w.with_currency=document.getElementById("token-amount-currency").checked;else if(w.type==="sep"){const k=document.querySelector("#archive-token-body .sep-chip.active"),x=document.getElementById("token-sep-custom").value;w.val=x||(k?k.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",p(),v()}}function h(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",p(),v())}async function g(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const k=document.getElementById("archive-rule-modal");k&&(k.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function _(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",p(),u(),v())}})();(function(){window.loadAboutPanel=()=>e(),window.loadPrefsSettings=()=>n();function e(){const s=document.getElementById("settings-contact-grid");if(!s)return;const o=_contact?.phone||"086-889-2228",i=_contact?.line_id||"@pearnly",r=_contact?.line_url||"https://line.me/R/ti/p/@pearnly",l=_contact?.email||"hello@pearnly.com",m=_contact?.address||"Bangkok, Thailand";s.innerHTML=`
            <a class="contact-item" href="${escapeHtml(r)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(i)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(l)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(l)}</div>
                </div>
            </a>
            <a class="contact-item" href="tel:${escapeHtml(o.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(o)}</div>
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
        `}async function n(){try{const s=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!s.ok)return;const o=await s.json(),i=document.getElementById("pref-dup-check");i&&(i.checked=!!o.enabled)}catch(s){console.warn("load prefs failed",s)}}const a=document.getElementById("pref-dup-check");a&&!a.dataset.bound&&(a.dataset.bound="1",a.addEventListener("change",async s=>{const o=s.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:o})})).ok?showToast(o?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(s.target.checked=!o,showToast(t("pref-save-failed"),"error"))}catch{s.target.checked=!o,showToast(t("pref-save-failed"),"error")}}))})();(function(){const s="pearnly_big_batch_tip_shown";let o=null,i=null,r=0,l=0,m=!1;function d(g){const _=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return g.preventDefault(),g.returnValue=_,_}function p(){m||(m=!0,window.addEventListener("beforeunload",d))}function c(){m&&(m=!1,window.removeEventListener("beforeunload",d))}function u(){if(document.getElementById("big-batch-progress"))return;const g=document.getElementById("file-list");if(!g||!g.parentNode)return;const _=document.createElement("div");_.id="big-batch-progress",_.className="big-batch-progress",_.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',g.parentNode.insertBefore(_,g);const w=document.getElementById("bbp-text");w&&(w.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function v(){const g=document.getElementById("big-batch-progress");g&&g.remove()}function f(){if(!i)return;let g=0;for(let L=0;L<i.length;L++){const $=i[L].status;($==="success"||$==="error"||$==="cancelled")&&g++}const _=r,w=_>0?Math.min(100,Math.floor(100*g/_)):0,k=(Date.now()-l)/1e3;let x;if(g>=3&&k>1){const L=k/g;x=(_-g)*L}else x=(_-g)*6/6;const E=Math.max(1,Math.ceil(x/60)),I=document.getElementById("bbp-fill"),B=document.getElementById("bbp-text");I&&(I.style.width=w+"%"),B&&(g>=_?B.textContent=t("big-batch-progress-done").replace("{total}",_):B.textContent=t("big-batch-progress-running").replace("{done}",g).replace("{total}",_).replace("{min}",E))}function y(g){try{if(localStorage.getItem(s)==="1")return}catch{}const _=Math.max(1,Math.ceil(g*6/6/60)),w=t("big-batch-first-tip").replace("{n}",g).replace("{min}",_);typeof showToast=="function"&&showToast(w,"info",8e3);try{localStorage.setItem(s,"1")}catch{}}function b(g){!g||g.length<100||(i=g,r=g.length,l=Date.now(),u(),p(),y(r),o&&clearInterval(o),o=setInterval(f,250),f())}function h(){o&&(clearInterval(o),o=null),c(),i&&r>=100?(f(),setTimeout(v,1200)):v(),i=null,r=0}window._bigBatchStart=b,window._bigBatchStop=h,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&f()})})();const Ee={status:null,statusLoaded:!1,bound:!1};function ge(e){return typeof escapeHtml=="function"?escapeHtml(e==null?"":String(e)):String(e??"")}function Be(e,n){try{typeof showToast=="function"&&showToast(e,n||"info")}catch{}}function ro(){const e=typeof _userInfo<"u"?_userInfo:null;return!!(e&&(e.role==="owner"||e.is_super_admin))}function Pi(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function Bc(e){if(!e)return!1;const n=String(e.status||"").toLowerCase();return n==="exception"||n==="exception_pending"||n==="rejected"}async function Rt(e){if(Ee.statusLoaded&&!e)return Ee.status;const n=localStorage.getItem("mrpilot_token");if(!n)return null;try{const a=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+n}});if(!a.ok)throw new Error("http_"+a.status);Ee.status=await a.json(),Ee.statusLoaded=!0}catch{Ee.status={configured:!1,connected:!1,organisations:[]},Ee.statusLoaded=!1}return Ee.status}async function Lc(){const e=document.getElementById("drawer-history-save");if(!e||e.querySelector("#btn-xero-push")||e.querySelector("#pn-push-wrap")||(await Rt(!1),e.querySelector("#pn-push-wrap"))||e.querySelector("#btn-xero-push"))return;const n=Pi();if(!(n&&(n._historyId||n.history_id)))return;let s=!1,o="xero-push-tip";!Ee.status||!Ee.status.configured?(s=!0,o="xero-err-not_configured"):Ee.status.connected?Bc(n)&&(s=!0,o="xero-push-disabled-exc"):(s=!0,o="xero-push-disabled-no-conn");const i=document.createElement("button");i.type="button",i.id="btn-xero-push",i.className="btn btn-ghost"+(s?" disabled":""),i.disabled=s,i.title=t(o)||"",i.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+ge(t("xero-push-btn"))+"</span>",i.addEventListener("click",$c);const r=document.getElementById("btn-push-erp");r&&r.parentNode?r.parentNode.insertBefore(i,r.nextSibling):e.insertBefore(i,e.firstChild)}async function $c(){const e=Pi(),n=e&&(e._historyId||e.history_id);if(!n)return;const a=document.getElementById("btn-xero-push");a&&(a.disabled=!0,a.classList.add("loading"));const s=localStorage.getItem("mrpilot_token");try{const o=await fetch("/api/erp/xero/push/"+encodeURIComponent(n),{method:"POST",headers:{Authorization:"Bearer "+s}});if(!o.ok){let i="unknown";try{i=(await o.json()).detail||"unknown"}catch{}const r=String(i).replace(/^xero\./,"").toLowerCase(),l=t("xero-"+r),m=l&&l!=="xero-"+r?l:i;Be(t("xero-push-fail").replace("{err}",m),"error");return}Be(t("xero-push-ok"),"success")}catch(o){Be(t("xero-push-fail").replace("{err}",o.message||"network"),"error")}finally{a&&(a.disabled=!1,a.classList.remove("loading"))}}async function Sc(){const e=document.getElementById("erp-global-push-mode");if(!e)return;const n=localStorage.getItem("mrpilot_token");if(n)try{const a=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+n}});if(a.ok){const s=await a.json();s.mode&&(e.value=s.mode,e.dataset.prev=s.mode)}}catch{}}async function Cc(e){const n=e.value,a=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+a,"Content-Type":"application/json"},body:JSON.stringify({mode:n})})).ok?(e.dataset.prev=n,Be(t("pref-erp-mode-saved"),"success")):(e.value=e.dataset.prev||"smart",Be(t("pref-save-failed"),"error"))}catch{e.value=e.dataset.prev||"smart",Be(t("pref-save-failed"),"error")}}(function(){function e(){const c=document.getElementById("erp-connect-cards");if(!c)return;const u=Ee.status;let v,f=!1;u?u.configured?u.connected?(f=!0,v='<span class="mrerp-card-pill mrerp-pill-ok">'+ge(t("xero-card-connected"))+"</span>"):v='<span class="mrerp-card-pill mrerp-pill-neutral">'+ge(t("xero-card-not-connected"))+"</span>":v='<span class="mrerp-card-pill mrerp-pill-neutral">'+ge(t("xero-card-not-configured"))+"</span>":v='<span class="mrerp-card-pill mrerp-pill-neutral">'+ge(t("xero-card-not-connected"))+"</span>";let y="";if(!u||!u.configured)y='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+ge(t("xero-connect-btn"))+"</button>";else if(!u.connected)ro()&&(y='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+ge(t("xero-connect-btn"))+"</button>");else{const I=!!u.auto_push,B=I?t("card-btn-disable"):t("card-btn-enable");y='<button type="button" class="'+(I?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(I?"1":"0")+'" title="'+ge(I?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+ge(B)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+ge(t("card-btn-edit"))+"</button>"}const b=u&&u.connected?"xero-card-desc-connected":"xero-card-desc-default",h=u&&u.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",g=(function(){const I=t(b);return I===b?h:I})();let _='<div class="integration-row erp-connect-xero'+(f?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+ge(t("xero-card-title")||"Xero")+"</span>"+v+'</div><div class="int-desc">'+ge(g)+'</div></div><div class="int-actions">'+y+"</div></div>";if(u&&u.configured&&u.connected&&ro()){const I=u.organisations||[];let B="";if(I.length>0){B+='<div class="erp-cc-meta">'+ge((t("xero-org-count")||"").replace("{n}",String(I.length)))+"</div>",B+='<div class="erp-cc-org-label">'+ge(t("xero-default-org"))+":</div>",B+='<div class="erp-cc-orgs">',I.forEach(function(S){B+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+ge(S.id)+'"'+(S.is_default?" checked":"")+'><span class="erp-cc-org-name">'+ge(S.organisation_name||S.organisation_id)+"</span></label>"}),B+="</div>";const L=!!u.auto_push,$=L?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");B+='<div class="erp-cc-auto-push" title="'+ge($)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(L?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+ge(t("erp-auto-push-label"))+"</span></label></div>",B+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+ge(t("xero-disconnect-btn"))+"</button></div>"}_+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+B+"</div>"}const w=c.querySelector(".erp-connect-xero"),k=c.querySelector("#erp-xero-details");k&&k.remove(),w?w.outerHTML=_:c.insertAdjacentHTML("afterbegin",_);const x=document.getElementById("btn-xero-edit-toggle");x&&x.addEventListener("click",function(I){I.preventDefault();const B=document.getElementById("erp-xero-details");B&&(B.style.display=B.style.display==="none"?"":"none")});const E=document.getElementById("btn-xero-toggle-enabled");E&&E.addEventListener("click",async function(I){if(I.preventDefault(),E.disabled)return;const L=!(E.getAttribute("data-xero-enabled")==="1");if(!L)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}E.disabled=!0,await o(L,null)})}async function n(){const c=localStorage.getItem("mrpilot_token");if(c)try{const u=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+c}});if(!u.ok){let f="unknown";try{f=(await u.json()).detail||"unknown"}catch{}const y=String(f).replace(/^xero\./,"").toLowerCase();Be(t("xero-push-fail").replace("{err}",t("xero-err-"+y)||f),"error");return}const v=await u.json();v.redirect_url&&(window.location.href=v.redirect_url)}catch(u){Be(t("xero-push-fail").replace("{err}",u.message||"network"),"error")}}async function a(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const u=localStorage.getItem("mrpilot_token");try{const v=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+u}});if(!v.ok)throw new Error("http_"+v.status);await Rt(!0),e()}catch(v){Be(t("xero-push-fail").replace("{err}",v.message),"error")}}async function s(c){const u=localStorage.getItem("mrpilot_token");try{const v=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+u,"Content-Type":"application/json"},body:JSON.stringify({token_id:c})});if(!v.ok)throw new Error("http_"+v.status);await Rt(!0),e()}catch(v){Be(t("xero-push-fail").replace("{err}",v.message),"error")}}async function o(c,u){const v=localStorage.getItem("mrpilot_token");u&&(u.disabled=!0);try{const f=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+v,"Content-Type":"application/json"},body:JSON.stringify({on:!!c})});if(!f.ok){let y="unknown";try{y=(await f.json()).detail||"unknown"}catch{}throw new Error(y)}Be(c?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),Ee.statusLoaded=!1,await Rt(!0),e()}catch(f){u&&(u.checked=!c),Be(t("erp-auto-push-toggle-fail").replace("{err}",f.message||"network"),"error")}finally{u&&(u.disabled=!1)}}async function i(){await Rt(!0),e(),Sc()}function r(){try{const c=String(window.location.hash||"");if(c.indexOf("xero=ok")>=0){const u=c.match(/n=(\d+)/),v=u?u[1]:"1";Be((t("xero-toast-redirected-ok")||"").replace("{n}",v),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),Rt(!0).then(e)}else c.indexOf("xero=err")>=0&&(Be(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function l(){if(Ee.bound)return;Ee.bound=!0,document.addEventListener("click",function(u){if(u.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(i,50);return}if(u.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(i,80);return}if(u.target.closest("#btn-xero-connect")){u.preventDefault(),n();return}if(u.target.closest("#btn-xero-disconnect")){u.preventDefault(),a();return}}),document.addEventListener("change",function(u){u.target&&u.target.matches('input[name="xero-default-org"]')&&s(u.target.value),u.target&&u.target.id==="xero-auto-push-toggle"&&o(u.target.checked,u.target),u.target&&u.target.id==="erp-global-push-mode"&&Cc(u.target)});const c=function(){return document.getElementById("drawer-body")};try{const u=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&Lc()}),v=c();if(v)u.observe(v,{childList:!0,subtree:!0});else{const f=new MutationObserver(function(){const y=c();y&&(u.observe(y,{childList:!0,subtree:!0}),f.disconnect())});f.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(r,500)}function m(){Ee.status&&e();const c=document.getElementById("btn-xero-push");if(c){const u=c.querySelector("span");u&&(u.textContent=t("xero-push-btn"))}}l(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",m);async function d(c){const u=Date.now();for(;Date.now()-u<c;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(v=>setTimeout(v,80))}return null}async function p(){await d(5e3);const c=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),u=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');c&&u&&await i()}setTimeout(p,200)})();(function(){var e="https://www.mrerp4sme.com/dms/index.php",n=null,a=!1;function s(b){return typeof escapeHtml=="function"?escapeHtml(b==null?"":String(b)):String(b??"")}function o(b,h){try{typeof showToast=="function"&&showToast(b,h||"info")}catch{}}function i(){return localStorage.getItem("mrpilot_token")}async function r(b){var h=i();if(!h)return null;try{var g=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+h}});if(!g.ok)throw new Error("http_"+g.status);var _=await g.json(),w=_&&_.items||[];n=w.find(function(k){return k&&(k.adapter||"").toLowerCase()==="mrerp_dms"})||null,a=!0}catch{n=null,a=!1}return n}function l(){var b=document.getElementById("erp-connect-cards");if(b){var h=b.querySelector("[data-mrerp-dms-zone]");h||(h=document.createElement("div"),h.setAttribute("data-mrerp-dms-zone","1"),b.appendChild(h));var g=n,_=!!(g&&g.enabled!==!1),w;g?_?w='<span class="mrerp-card-pill mrerp-pill-ok">'+s(t("dms-card-connected"))+"</span>":w='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("dms-card-disabled-pill"))+"</span>":w='<span class="mrerp-card-pill mrerp-pill-neutral">'+s(t("dms-card-not-connected"))+"</span>";var k;if(!g)k='<button type="button" class="int-btn-configure" id="btn-dms-connect">'+s(t("dms-card-connect"))+"</button>";else{var x=_?t("dms-card-disable"):t("dms-card-enable");k='<button type="button" class="int-btn-configure" id="btn-dms-edit">'+s(t("dms-card-edit"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-test">'+s(t("dms-card-test"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-toggle">'+s(x)+"</button>"}h.innerHTML='<div class="integration-row erp-connect-mrerp-dms'+(_?" connected":"")+'"><div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/><path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/></svg></div><div class="int-info"><div class="int-name"><span>'+s(t("dms-card-title"))+"</span>"+w+'</div><div class="int-desc">'+s(t("dms-card-desc"))+'</div></div><div class="int-actions">'+k+"</div></div>"}}function m(){var b=document.getElementById("dms-wizard-overlay");b&&b.remove(),document.removeEventListener("keydown",d)}function d(b){b.key==="Escape"&&m()}function p(){m();var b=n,h=b&&b.config&&b.config.booking_defaults&&b.config.booking_defaults.booking_prefix||"PN",g=function(k,x,E,I,B){return'<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">'+s(t(k))+'</span><input id="'+x+'" type="'+E+'" value="'+s(I||"")+'" placeholder="'+s(B||"")+'" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;"></label>'},_=document.createElement("div");_.id="dms-wizard-overlay",_.style.cssText="position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;",_.innerHTML='<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">'+s(t("dms-wizard-title"))+'</div><div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">'+s(t("dms-card-desc"))+"</div>"+g("dms-wizard-username","dms-w-user","text","","")+g("dms-wizard-password","dms-w-pass","password","","")+g("dms-wizard-prefix","dms-w-prefix","text",h,"PN")+'<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div><div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn btn-ghost" id="dms-w-cancel">'+s(t("dms-wizard-cancel"))+'</button><button type="button" class="btn btn-primary" id="dms-w-save">'+s(t("dms-wizard-save"))+"</button></div></div>",document.body.appendChild(_),document.addEventListener("keydown",d),_.addEventListener("click",function(k){k.target===_&&m()});var w=document.getElementById("dms-w-user");w&&w.focus()}function c(b){var h=document.getElementById("dms-w-err");h&&(h.textContent=b,h.style.display=b?"":"none")}async function u(){var b=n&&n.config&&n.config.system_url||e,h=(document.getElementById("dms-w-user")||{}).value||"",g=(document.getElementById("dms-w-pass")||{}).value||"",_=(document.getElementById("dms-w-prefix")||{}).value||"PN";if(b=b.trim(),h=h.trim(),!b||!h||!g){c(t("dms-wizard-required"));return}var w=document.getElementById("dms-w-save");w&&(w.disabled=!0,w.textContent=t("dms-wizard-saving")),c("");var k=i();try{var x=await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+k,"Content-Type":"application/json"},body:JSON.stringify({adapter:"mrerp_dms",config:{system_url:b,username:h,password:g}})}),E=await x.json().catch(function(){return{}});if(!x.ok||!E.ok){var I=E.error_friendly&&(E.error_friendly[window.currentLang]||E.error_friendly.en)||t("dms-connect-fail-generic");c(I),w&&(w.disabled=!1,w.textContent=t("dms-wizard-save"));return}var B={system_url:b,username_enc:h,password_enc:g,id_card_auto_push:!0,booking_defaults:{booking_prefix:_.trim()||"PN"}},L,$;n&&n.id?(L="PATCH",$="/api/erp/endpoints/"+encodeURIComponent(n.id)):(L="POST",$="/api/erp/endpoints");var S=L==="POST"?{name:"MR.ERP DMS",adapter:"mrerp_dms",config:B,is_default:!1,auto_push:!1}:{config:B,auto_push:!1},H=await fetch($,{method:L,headers:{Authorization:"Bearer "+k,"Content-Type":"application/json"},body:JSON.stringify(S)});if(!H.ok){var R=await H.json().catch(function(){return{}}),G=R&&R.detail&&(R.detail.code||R.detail)||"save_failed";c(t("dms-save-fail")+" ("+s(String(G))+")"),w&&(w.disabled=!1,w.textContent=t("dms-wizard-save"));return}m(),o(t("dms-connect-ok"),"success"),await r(!0),l(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{c(t("dms-connect-fail-generic")),w&&(w.disabled=!1,w.textContent=t("dms-wizard-save"))}}async function v(){if(!(!n||!n.id)){o(t("dms-test-running"),"info");var b=i();try{var h=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id)+"/test-connection?refresh=1",{method:"POST",headers:{Authorization:"Bearer "+b}}),g=await h.json().catch(function(){return{}});o(g&&g.ok?t("dms-test-ok"):t("dms-test-fail"),g&&g.ok?"success":"error")}catch{o(t("dms-test-fail"),"error")}}}async function f(){if(!(!n||!n.id)){var b=n.enabled===!1;if(!b)try{var h=await window.pearnlyConfirm(t("dms-confirm-disable"));if(!h)return}catch{}var g=i();try{var _=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id),{method:"PATCH",headers:{Authorization:"Bearer "+g,"Content-Type":"application/json"},body:JSON.stringify({enabled:b})});if(!_.ok)throw new Error("http_"+_.status);o(b?t("dms-enabled-toast"):t("dms-disabled-toast"),"success"),await r(!0),l(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{o(t("dms-save-fail"),"error")}}}function y(){r().then(l)}document.addEventListener("click",function(b){if(b.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(y,60);return}if(b.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(y,90);return}if(b.target.closest("#btn-dms-connect")||b.target.closest("#btn-dms-edit")){b.preventDefault(),p();return}if(b.target.closest("#dms-w-cancel")){b.preventDefault(),m();return}if(b.target.closest("#dms-w-save")){b.preventDefault(),u();return}if(b.target.closest("#btn-dms-test")){b.preventDefault(),v();return}if(b.target.closest("#btn-dms-toggle")){b.preventDefault(),f();return}}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("mrerp-dms-adapter",l),setTimeout(function(){var b=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),h=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');b&&h&&y()},250)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const d=`
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
        </div>`,p=document.createElement("div");p.innerHTML=d,document.body.appendChild(p.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",c=>{c.target.id==="report-modal"&&a()})}function a(){const d=document.getElementById("report-modal");d&&(d.style.display="none"),s=null}let s=null;async function o(d,p){const c=d+":"+(p||"");if(e[c])return e[c];let u;try{const v=localStorage.getItem("mrpilot_token"),f=await fetch(`/api/reports/templates?lang=${encodeURIComponent(d)}`,{headers:{Authorization:"Bearer "+v}});if(!f.ok)throw new Error("templates fetch failed");u=(await f.json()).templates||[]}catch(v){console.error("fetchTemplates fail",v),u=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(u=u.filter(v=>v.code!=="erp"),p==="history-batch"){const v=u.findIndex(y=>y.code==="standard"),f=v>=0?v+1:u.length;u.splice(f,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[c]=u,u}function i(d){const p=document.getElementById("report-tpl-list"),c=d.map((v,f)=>`
            <label class="report-tpl-item${v.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${v.code}" ${v.recommended||f===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${r(v.name)}
                        ${v.recommended?`<span class="report-tpl-badge">${r(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${r(v.desc||"")}</div>
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
        `;p.innerHTML=c+u}function r(d){return d==null?"":String(d).replace(/[&<>"']/g,p=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[p])}function l(d){const p=new Date,c=p.getFullYear(),u=p.getMonth()+1;if(d==="all")return"all";if(d==="this-month")return`${c}-${String(u).padStart(2,"0")}`;if(d==="last-month"){const v=new Date(c,u-2,1);return`${v.getFullYear()}-${String(v.getMonth()+1).padStart(2,"0")}`}return d==="this-year"?`${c}`:d==="this-quarter"?`${c}-Q${Math.floor((u-1)/3)+1}`:"all"}window.openReportModal=async function(d){d=d||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(y=>{const b=y.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][b]&&(y.textContent=I18N[currentLang][b])});const p=document.getElementById("report-period-section");p&&(p.style.display=d.mode==="client"?"":"none");const c=document.getElementById("report-tpl-list");c.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const u=await o(currentLang,d&&d.mode);i(u),s=d;const v=document.getElementById("report-modal-download"),f=v.cloneNode(!0);v.parentNode.replaceChild(f,v),f.addEventListener("click",()=>m(s))};async function m(d){if(!d)return;const p=document.querySelector('input[name="report-tpl"]:checked');if(!p){showToast(t("report-toast-no-selection"),"info");return}const c=p.value,u=document.querySelector('input[name="report-period"]:checked'),v=u?u.value:"all",f=l(v),y=document.getElementById("report-modal-download"),b=y.innerHTML;y.disabled=!0,y.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const h=localStorage.getItem("mrpilot_token");let g,_;if(d.mode==="records")g=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,records:d.records||[],meta:d.meta||{}})}),_=`mrpilot-${c}-${Date.now()}.xlsx`;else if(d.mode==="client"){const L=`/api/reports/clients/${d.clientId}/export?template=${encodeURIComponent(c)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(f)}`;g=await fetch(L,{headers:{Authorization:"Bearer "+h}}),_=`${(d.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${c}.xlsx`}else if(d.mode==="history-batch")c==="sales_detail_th"?(g=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:d.historyIds||[],client_id:d.clientId||null})}),_=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(g=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,history_ids:d.historyIds||[],client_id:d.clientId||null})}),_=`mrpilot-batch-${c}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+d.mode);if(!g.ok){let L="HTTP "+g.status;try{const $=await g.json();$&&$.detail&&(L=$.detail)}catch($){console.warn("[batch-export] resp.json err.detail parse failed:",$)}g.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+L,"error");return}const w=await g.blob();let k=_;const E=(g.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(E)try{k=decodeURIComponent(E[1])}catch{}const I=URL.createObjectURL(w),B=document.createElement("a");B.href=I,B.download=k,document.body.appendChild(B),B.click(),document.body.removeChild(B),URL.revokeObjectURL(I),showToast(t("report-toast-success"),"success"),a()}catch(h){console.error("doDownload fail",h),showToast(t("report-toast-fail")+" · "+(h.message||""),"error")}finally{y.disabled=!1,y.innerHTML=b}}document.addEventListener("DOMContentLoaded",()=>{const d=document.getElementById("btn-export");if(d){const c=d.cloneNode(!0);d.parentNode.replaceChild(c,d),c.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(u=>({filename:u.filename,merged_fields:u.merged_fields||{}}))})})}const p=document.getElementById("history-batch-export");p&&p.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(d,p){openReportModal({mode:"client",clientId:d,clientName:p||""})}})();const Tc=/\.(pdf|jpe?g|png|webp)$/i,Hc="mrpilot_folder_watcher",Mc=1;let Mn=null;function ga(){return Mn||(Mn=new Promise((e,n)=>{const a=indexedDB.open(Hc,Mc);a.onupgradeneeded=s=>{const o=s.target.result;o.objectStoreNames.contains("handles")||o.createObjectStore("handles"),o.objectStoreNames.contains("seen")||o.createObjectStore("seen"),o.objectStoreNames.contains("config")||o.createObjectStore("config")},a.onsuccess=s=>e(s.target.result),a.onerror=s=>n(s.target.error)}),Mn)}function ln(e,n){return ga().then(a=>new Promise((s,o)=>{const r=a.transaction(e,"readonly").objectStore(e).get(n);r.onsuccess=()=>s(r.result),r.onerror=()=>o(r.error)}))}function Et(e,n,a){return ga().then(s=>new Promise((o,i)=>{const r=s.transaction(e,"readwrite");r.objectStore(e).put(a,n),r.oncomplete=()=>o(),r.onerror=()=>i(r.error)}))}function sn(e,n){return ga().then(a=>new Promise((s,o)=>{const i=a.transaction(e,"readwrite");i.objectStore(e).delete(n),i.oncomplete=()=>s(),i.onerror=()=>o(i.error)}))}function lo(e){return ga().then(n=>new Promise((a,s)=>{const o=n.transaction(e,"readwrite");o.objectStore(e).clear(),o.oncomplete=()=>a(),o.onerror=()=>s(o.error)}))}async function co(e){if(!e)return!1;try{const n={mode:"read"};let a=await e.queryPermission(n);return a==="granted"?!0:(a=await e.requestPermission(n),a==="granted")}catch(n){return console.warn("[folder] permission check failed:",n),!1}}async function Ac(e){const n=new FormData;n.append("file",e,e.name),n.append("source","folder");const a=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:n});if(!a.ok){let s="http_"+a.status;try{const o=await a.json();s=o&&o.detail?typeof o.detail=="string"?o.detail:o.detail.code||JSON.stringify(o.detail):s}catch{}throw new Error(s)}return await a.json()}async function Pc(e){try{const a=(await e.getFile()).size;return await new Promise(o=>setTimeout(o,3e3)),(await e.getFile()).size===a&&a>0}catch{return!1}}async function ji(e,n,a,s){if(s>10)return;let o;try{o=await e.queryPermission({mode:"read"})}catch{o="denied"}if(o==="granted")for await(const i of e.values()){const r=n?`${n}/${i.name}`:i.name;if(i.kind==="file"){if(!Tc.test(i.name))continue;let l;try{l=await i.getFile()}catch{continue}const m=`${r}::${l.size}::${l.lastModified}`;if(await ln("seen",m))continue;a.push({entry:i,file:l,seenKey:m,relPath:r})}else if(i.kind==="directory")try{await ji(i,r,a,s+1)}catch{}}}(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window;let a=null,s=null,o=60,i=!1,r=!1,l=0,m=0,d=0,p=[],c=null,u=!1;function v(O,N){const Y=document.getElementById("folder-status-summary");Y&&(Y.setAttribute("data-i18n",O),Y.textContent=t(O),Y.className="auto-status-pill"+(N?" "+N:""))}function f(O){["folder-unsupported","folder-empty","folder-active"].forEach(N=>{const Y=document.getElementById(N);Y&&(Y.style.display=N===O?"":"none")})}function y(O){if(!O)return"-";const N=O instanceof Date?O:new Date(O),Y=String(N.getHours()).padStart(2,"0"),de=String(N.getMinutes()).padStart(2,"0"),re=String(N.getSeconds()).padStart(2,"0");return`${Y}:${de}:${re}`}function b(){f("folder-active");const O=document.getElementById("folder-config-path");O&&a&&(O.textContent=a.name||"-");const N=document.getElementById("folder-interval-select");N&&(N.value=String(o)),document.getElementById("folder-stat-last").textContent=c?y(c):"-",document.getElementById("folder-stat-processed").textContent=String(l),document.getElementById("folder-stat-failed").textContent=String(m),document.getElementById("folder-stat-queue").textContent=String(d);const Y=document.getElementById("btn-folder-pause"),de=document.getElementById("btn-folder-resume");Y&&(Y.style.display=i?"none":""),de&&(de.style.display=i?"":"none"),i?v("folder-status-paused","paused"):v("folder-status-running","running");const re=document.getElementById("folder-status-text");re&&(re.setAttribute("data-i18n",i?"folder-status-paused":"folder-status-running"),re.textContent=t(i?"folder-status-paused":"folder-status-running"));const Ne=document.getElementById("folder-status-pulse");Ne&&(Ne.className="folder-status-pulse"+(i?" paused":"")),h()}function h(){const O=document.getElementById("folder-recent-list");if(O){if(p.length===0){O.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}O.innerHTML=p.slice(0,20).map(N=>{let Y;N.status==="ok"?Y=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:N.status==="dup"?Y=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:N.status==="skip"?Y=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:Y=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const de=N.status==="fail"&&N.error?N.error:N.status==="dup"&&N.reason||N.status==="skip"&&N.reason?N.reason:"",re=de?`<div class="folder-recent-err">${escapeHtml(de)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${Y}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(N.name)}</div>
                        ${re}
                    </div>
                    <div class="folder-recent-time">${y(N.time)}</div>
                </div>
            `}).join("")}}function g(O){p.unshift(O),p.length>50&&(p.length=50),Et("config","recent_list",p).catch(()=>{})}async function _(){if(!(r||i||!a)){r=!0;try{if(await a.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),S(),showToast("warn",t("folder-permission-lost"));return}c=new Date;const N=[];await ji(a,"",N,0),d=N.length,b();for(const Y of N){if(i)break;if(!await Pc(Y.entry)){d=Math.max(0,d-1),b();continue}try{let re;try{re=await Y.entry.getFile()}catch{re=Y.file}const Ne=await Ac(re);await Et("seen",Y.seenKey,{name:re.name,relPath:Y.relPath,size:re.size,lastModified:re.lastModified,processed_at:Date.now()});const _t=Ne.history_ids||(Ne.history_id?[Ne.history_id]:[]),Ba=Ne.duplicate_warnings||[],La=Y.relPath||re.name;_t.length>0?(l+=_t.length,g({name:La,status:"ok",time:new Date,history_id:_t[0],count:_t.length}),await Et("config","processed_count",l)):Ba.length>0?g({name:La,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):g({name:La,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(re){m++,g({name:Y.relPath||Y.file.name,status:"fail",time:new Date,error:String(re.message||re)}),await Et("config","failed_count",m)}d=Math.max(0,d-1),b()}}catch(O){console.warn("[folder] scan error:",O)}finally{r=!1,b()}}}function w(){s&&clearInterval(s),s=setInterval(_,o*1e3)}function k(){s&&(clearInterval(s),s=null)}function x(O){if(!a||i)return;const N=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return O.preventDefault(),O.returnValue=N,N}function E(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",x))}function I(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",x))}function B(){i=!1,w(),E(),b(),_()}function L(){i=!0,k(),I(),b()}function $(){i=!1,w(),E(),b(),_()}function S(){i=!0,k(),I()}async function H(){try{const O=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await co(O)){showToast("warn",t("folder-permission-denied"));return}a=O,await Et("handles","main",O),l=0,m=0,d=0,p=[],await Et("config","processed_count",0),await Et("config","failed_count",0),await lo("seen"),B()}catch(O){O&&O.name!=="AbortError"&&console.warn("[folder] pick failed:",O)}}async function R(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(S(),a=null,l=0,m=0,d=0,p=[],await sn("handles","main"),await sn("config","processed_count"),await sn("config","failed_count"),await lo("seen"),f("folder-empty"),v("folder-status-empty",""))}async function G(){p=[];try{await sn("config","recent_list")}catch{}h()}async function se(){if(u)return;if(u=!0,!n){f("folder-unsupported"),v("folder-status-unsupported",""),we();return}ce();let O=null;try{O=await ln("handles","main")}catch{}if(!O){f("folder-empty"),v("folder-status-empty","");return}if(!await co(O)){f("folder-empty"),v("folder-status-empty",""),await sn("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}a=O;try{l=await ln("config","processed_count")||0}catch{}try{m=await ln("config","failed_count")||0}catch{}try{const Y=await ln("config","recent_list");Array.isArray(Y)&&(p=Y.map(de=>({...de,time:de.time?new Date(de.time):new Date})))}catch{}B()}function ce(){const O=document.getElementById("btn-folder-pick"),N=document.getElementById("btn-folder-pause"),Y=document.getElementById("btn-folder-resume"),de=document.getElementById("btn-folder-scan-now"),re=document.getElementById("btn-folder-remove"),Ne=document.getElementById("btn-folder-clear-recent"),_t=document.getElementById("folder-interval-select");O&&O.addEventListener("click",H),N&&N.addEventListener("click",L),Y&&Y.addEventListener("click",$),de&&de.addEventListener("click",()=>{_()}),re&&re.addEventListener("click",R),Ne&&Ne.addEventListener("click",G),_t&&_t.addEventListener("change",Ba=>{o=parseInt(Ba.target.value,10)||60,i||w()}),_e()}function _e(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(O=>{O.dataset.tabJumpBound||(O.dataset.tabJumpBound="1",O.addEventListener("click",N=>{const Y=N.currentTarget.dataset.tabJump;if(Y==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(Y==="upload"){const de=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');de&&de.click()}}))})}function we(){_e()}window._loadFolderWatcherPanel=se})();function jc(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(n=>/chromium|google chrome|microsoft edge/i.test(n.brand||""))}catch{}const e=navigator.userAgent||"";return!!(/Edg\//.test(e)||/Chrome\//.test(e)&&!/OPR\/|YaBrowser|Opera/.test(e))}function Ka(){try{if(jc()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const e=document.getElementById("chrome-only-banner");if(!e)return;const n=e.querySelector('[data-i18n="chrome-banner-msg"]'),a=e.querySelector('[data-i18n="chrome-banner-dismiss"]');n&&typeof t=="function"&&(n.textContent=t("chrome-banner-msg")),a&&typeof t=="function"&&(a.textContent=t("chrome-banner-dismiss")),e.style.display="";const s=document.getElementById("chrome-only-banner-close");s&&!s.dataset.bound&&(s.dataset.bound="1",s.addEventListener("click",()=>{e.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",Ka):setTimeout(Ka,0));window._refreshChromeBanner=Ka;const Dc=`
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
    `;$e("email-modal",Dc);const F={account:null,presets:null,modalMode:"new",loaded:!1,triggering:!1,autoRefreshTimer:null};function po(e){F.modalMode=e;const n=document.getElementById("email-modal");if(!n)return;const a=document.getElementById("email-preset");a.innerHTML="";const s=F.presets||{},o=["gmail","outlook","yahoo","icloud","qq","163","custom"],i={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};o.forEach(h=>{if(!s[h])return;const g=document.createElement("option");g.value=h,g.textContent=h==="custom"?t("email-preset-custom"):i[h]||h,a.appendChild(g)});const r=document.getElementById("email-modal-title"),l=document.getElementById("email-address"),m=document.getElementById("email-password"),d=document.getElementById("email-imap-host"),p=document.getElementById("email-imap-port"),c=document.getElementById("email-imap-ssl"),u=document.getElementById("email-folder"),v=document.getElementById("email-mark-read"),f=document.getElementById("email-bind-enabled"),y=document.getElementById("email-test-result"),b=document.getElementById("email-adv-details");if(y&&(y.style.display="none",y.textContent=""),e==="edit"&&F.account){r.setAttribute("data-i18n","email-modal-title-edit"),r.textContent=t("email-modal-title-edit"),l.value=F.account.email_address||"",m.value="",m.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),m.placeholder=t("email-field-password-edit-ph"),d.value=F.account.imap_host||"",p.value=F.account.imap_port||993,c.checked=F.account.imap_use_ssl!==!1,u.value=F.account.folder||"INBOX",v.checked=F.account.mark_as_read!==!1,f.checked=F.account.enabled!==!1;const h=document.getElementById("email-filter-sender"),g=document.getElementById("email-filter-subject");h&&(h.value=F.account.filter_sender||""),g&&(g.value=F.account.filter_subject||""),mo(F.account.interval_min||15),a.value=Rc(F.account.imap_host)||"custom",b&&(b.open=!0)}else{r.setAttribute("data-i18n","email-modal-title-new"),r.textContent=t("email-modal-title-new"),l.value="",m.value="",m.setAttribute("data-i18n-placeholder","email-field-password-ph"),m.placeholder=t("email-field-password-ph"),a.value="gmail",_s("gmail"),u.value="INBOX",v.checked=!0,f.checked=!0;const h=document.getElementById("email-filter-sender"),g=document.getElementById("email-filter-subject");h&&(h.value=""),g&&(g.value=""),mo(15),b&&(b.open=!1)}Fc(),n.style.display="flex",setTimeout(()=>l.focus(),60)}function Ta(){const e=document.getElementById("email-modal");e&&(e.style.display="none")}function _s(e){const n=(F.presets||{})[e];if(!n||e==="custom")return;const a=document.getElementById("email-imap-host"),s=document.getElementById("email-imap-port"),o=document.getElementById("email-imap-ssl");a&&(a.value=n.host||""),s&&(s.value=n.port||993),o&&(o.checked=n.ssl!==!1)}const qc={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function uo(e){if(!e||!e.includes("@"))return;const n=e.split("@")[1].toLowerCase().trim(),a=qc[n];if(!a)return;const s=document.getElementById("email-preset");if(!s)return;const o=s.value;o&&o!=="custom"&&o!==""&&o===a||(s.value=a,_s(a))}function Rc(e){if(!e)return null;const n=F.presets||{};for(const a in n)if(a!=="custom"&&n[a]&&n[a].host===e)return a;return null}function Di(){const e=document.querySelector("#email-interval-options .email-interval-btn.active"),n=e?parseInt(e.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(n)?n:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function Fc(){const e=document.getElementById("email-interval-options");!e||e._bound||(e._bound=!0,e.addEventListener("click",n=>{const a=n.target.closest(".email-interval-btn");a&&(e.querySelectorAll(".email-interval-btn").forEach(s=>s.classList.remove("active")),a.classList.add("active"))}))}function mo(e){const n=[5,15,60].includes(e)?e:15,a=document.getElementById("email-interval-options");a&&a.querySelectorAll(".email-interval-btn").forEach(s=>{s.classList.toggle("active",parseInt(s.dataset.interval,10)===n)})}function Ce(e,n){const a=document.getElementById("email-test-result");a&&(a.style.display="",a.textContent=n,a.className="form-test-result "+(e==="ok"?"ok":e==="running"?"running":"fail"))}async function zc(){const e=Di();if(!e.email_address){Ce("fail",t("email-addr-required"));return}if(!e.password){Ce("fail",t("email-password-required"));return}if(!e.imap_host){Ce("fail",t("email-host-required"));return}const n=document.getElementById("btn-email-modal-test");n&&(n.disabled=!0),Ce("running",t("email-test-running"));try{const a=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,password:e.password,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder})}),s=await a.json().catch(()=>({}));if(a.ok&&s.success)Ce("ok",t("email-test-ok",{folder:e.folder,n:s.folder_count??"?"}));else{const o=s.error_msg||"";o==="auth_failed"||/auth/i.test(o)?Ce("fail",t("email-test-auth-fail")):Ce("fail",t("email-test-fail",{msg:o||a.status}))}}catch(a){Ce("fail",t("email-test-fail",{msg:String(a).slice(0,120)}))}finally{n&&(n.disabled=!1)}}(function(){async function e(){const u=document.getElementById("email-empty"),v=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!u||!v))try{const f=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(f.status===401){localStorage.removeItem("mrpilot_token");const b=await f.json().catch(()=>({}));if((typeof b.detail=="string"?b.detail:b.detail&&b.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!f.ok){a("none");return}const y=await f.json();F.account=y.account||null,F.presets=y.presets||{},F.loaded=!0,n(),F.account&&d()}catch(f){console.error("[email-ingest] load failed",f),a("none")}}function n(){const u=document.getElementById("email-empty"),v=document.getElementById("email-account-card"),f=document.getElementById("email-logs-section");if(!F.account){u.style.display="",v.style.display="none",f&&(f.style.display="none"),a("none");return}u.style.display="none",v.style.display="",f&&(f.style.display="");const y=document.getElementById("email-account-addr"),b=document.getElementById("email-account-host"),h=document.getElementById("email-account-last"),g=document.getElementById("email-last-error"),_=document.getElementById("email-enabled-toggle");if(y&&(y.textContent=F.account.email_address||"-"),b&&(b.textContent=`${F.account.imap_host||"-"}:${F.account.imap_port||993}`),h){const w=F.account.last_fetched_at;if(!w)h.textContent=t("email-last-never");else{const k=s(w),x=!F.account.last_error;h.textContent=x?t("email-last-ok",{time:k}):t("email-last-fail",{time:k})}}g&&(F.account.last_error?(g.style.display="",g.textContent=o(F.account.last_error)):g.style.display="none"),_&&(_.checked=!!F.account.enabled),F.account.enabled?F.account.last_error?a("error"):a("on"):a("off")}function a(u){const v=document.getElementById("email-status-summary");if(!v)return;v.classList.remove("none","ready","active","coming");let f="auto-status-loading";u==="none"?(f="email-status-none",v.classList.add("none")):u==="on"?(f="email-status-on",v.classList.add("active")):u==="off"?(f="email-status-off",v.classList.add("coming")):u==="error"&&(f="email-status-error",v.classList.add("none")),v.setAttribute("data-i18n",f),v.textContent=t(f)}function s(u){if(!u)return"";const v=new Date(u);if(isNaN(v.getTime()))return"";const f=y=>String(y).padStart(2,"0");return`${f(v.getMonth()+1)}-${f(v.getDate())} ${f(v.getHours())}:${f(v.getMinutes())}`}function o(u){if(!u)return"";const v=String(u);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(v)?t("email-test-auth-fail"):/timeout|timed out/i.test(v)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(v),v)}async function i(){const u=Di();if(!u.email_address){Ce("fail",t("email-addr-required"));return}if(F.modalMode==="new"&&!u.password){Ce("fail",t("email-password-required"));return}if(!u.imap_host){Ce("fail",t("email-host-required"));return}const v=document.getElementById("btn-email-modal-save");v&&(v.disabled=!0);const f={...u};F.modalMode==="edit"&&!f.password&&delete f.password;try{const y=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(f)}),b=await y.json().catch(()=>({}));if(y.ok&&b.ok)F.account=b.account,showToast(t("email-save-ok"),"success"),Ta(),n(),d();else{const g="email."+(b.detail||"").split(".").slice(-1)[0];Ce("fail",t(g)!==g?t(g):t("email-save-fail"))}}catch{Ce("fail",t("email-save-fail"))}finally{v&&(v.disabled=!1)}}async function r(){if(!(!F.account||!await showConfirm(t("email-unbind-confirm",{email:F.account.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){F.account=null,showToast(t("email-unbind-ok"),"success"),n();const f=document.getElementById("email-logs-list");f&&(f.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function l(){if(!F.account||F.triggering)return;if(!F.account.enabled){showToast(t("email.disabled"),"error");return}F.triggering=!0;const u=document.getElementById("btn-email-trigger"),v=u?u.innerHTML:"";u&&(u.disabled=!0,u.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const f=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),y=await f.json().catch(()=>({}));if(f.ok){const b=y.emails_scanned||0,h=y.ocr_succeeded||0,g=y.ocr_failed||0;b===0&&h===0&&g===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:b,ok:h,fail:g}),g>0?"warn":"success")}else{const h="email."+(y.detail||"").split(".").slice(-1)[0];showToast(t(h)!==h?t(h):t("email-trigger-fail"),"error")}await e()}catch{showToast(t("email-trigger-fail"),"error")}finally{F.triggering=!1,u&&(u.disabled=!1,u.innerHTML=v)}}async function m(){if(!F.account)return;const u=document.getElementById("email-enabled-toggle"),v=!!(u&&u.checked),f=F.account.enabled;try{const y=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:F.account.email_address,imap_host:F.account.imap_host,imap_port:F.account.imap_port,imap_use_ssl:F.account.imap_use_ssl,folder:F.account.folder||"INBOX",filter_subject:F.account.filter_subject||null,filter_sender:F.account.filter_sender||null,mark_as_read:F.account.mark_as_read!==!1,enabled:v})}),b=await y.json().catch(()=>({}));y.ok&&b.ok?(F.account=b.account,n()):(u&&(u.checked=f),showToast(t("email-toggle-fail"),"error"))}catch{u&&(u.checked=f),showToast(t("email-toggle-fail"),"error")}}async function d(){const u=document.getElementById("email-logs-list");if(u){u.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const v=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!v.ok){u.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const f=await v.json();if(!Array.isArray(f)||f.length===0){u.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}u.innerHTML=f.map(p).join("")}catch{u.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function p(u){const v=s(u.created_at),f=u.status||"failed",y=f==="success"?"ok":f==="partial"?"partial":"fail",b=f==="success"?"✓":f==="partial"?"◐":"✗",h=u.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,g=t("email-log-counts",{scanned:u.emails_scanned||0,att:u.attachments_found||0,ok:u.ocr_succeeded||0,fail:u.ocr_failed||0}),_=(u.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${y}">
                <span class="log-time">${escapeHtml(v)}</span>
                <span class="log-status">${b}</span>
                ${h}
                <span class="log-counts">${escapeHtml(g)}</span>
                <span class="log-elapsed">${escapeHtml(_)}</span>
            </div>
        `}function c(){const u=document.getElementById("btn-email-bind");u&&u.addEventListener("click",()=>po("new"));const v=document.getElementById("btn-email-edit");v&&v.addEventListener("click",()=>po("edit"));const f=document.getElementById("btn-email-unbind");f&&f.addEventListener("click",r);const y=document.getElementById("btn-email-trigger");y&&y.addEventListener("click",l);const b=document.getElementById("email-enabled-toggle");b&&b.addEventListener("change",m);const h=document.getElementById("email-modal-close");h&&h.addEventListener("click",Ta);const g=document.getElementById("btn-email-modal-cancel");g&&g.addEventListener("click",Ta);const _=document.getElementById("btn-email-modal-test");_&&_.addEventListener("click",zc);const w=document.getElementById("btn-email-modal-save");w&&w.addEventListener("click",i);const k=document.getElementById("email-preset");k&&k.addEventListener("change",I=>_s(I.target.value));const x=document.getElementById("email-address");x&&!x.dataset.autoBound&&(x.dataset.autoBound="1",x.addEventListener("blur",I=>uo((I.target.value||"").trim())),x.addEventListener("input",I=>{const B=(I.target.value||"").trim();B.includes("@")&&B.split("@")[1].includes(".")&&uo(B)}));const E=document.getElementById("btn-email-refresh-logs");E&&E.addEventListener("click",()=>{E.classList.add("spinning"),setTimeout(()=>E.classList.remove("spinning"),600),d()})}c(),window._loadEmailIngestPanel=e,window._rerenderEmailIngest=function(){if(!F.loaded)return;n();const u=document.getElementById("email-logs-section");F.account&&u&&u.open&&d()},window._startEmailLogAutoRefresh=function(){F.autoRefreshTimer||(F.autoRefreshTimer=setInterval(()=>{F.account&&F.loaded&&d()},3e4))},window._stopEmailLogAutoRefresh=function(){F.autoRefreshTimer&&(clearInterval(F.autoRefreshTimer),F.autoRefreshTimer=null)}})();const Nc=`
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
`;$e("bank-cand-drawer",Nc);const Oc=`
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
`;$e("bank-client-picker-modal",Oc);const M={sessions:[],currentSession:null,currentTxs:[],currentFilter:"all",currentTxForDrawer:null,loaded:!1,queue:[],qSeq:0,sessionFilter:"all",pickerSelected:null};function Vc(e){const n=Number(e||0);let a="score-low";return n>=85?a="score-high":n>=60&&(a="score-mid"),'<span class="bank-cand-score '+a+'">'+n.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Uc(e){const n=document.getElementById("bank-upload-progress");n&&(n.style.display="none")}function Gc(){const e=document.getElementById("bank-upload-error");e&&(e.style.display="none")}function Wc(e){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[e]||t("bank-err-unknown")+" ("+e+")"}function Ct(e){if(e==null)return"-";const n=Number(e);return isNaN(n)?"-":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function Kt(e){if(!e)return"-";const n=String(e);return n.length>=10?n.slice(0,10):n}function qi(e,n){return!e&&!n?"":(Kt(e)||"?")+" ~ "+(Kt(n)||"?")}function X(e){return e==null?"":String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}async function Kc(e){M.currentTxForDrawer=e;const n=document.getElementById("bank-detail-body");n&&n.classList.add("has-pane");const a=document.getElementById("bank-cand-pane-title"),s=document.getElementById("bank-cand-pane-sub"),o=document.getElementById("bank-cand-pane-foot");if(a&&(a.textContent=t("bank-cand-pane-current")),s){const r=e.direction==="OUT"?"-":"+",l=e.direction==="OUT"?"bank-out":"bank-in";s.innerHTML=`${X(Kt(e.tx_date))}
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <span>${X(e.description||"-")}</span>
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <strong class="${l}">${r}${Ct(e.amount)}</strong>`}o&&(o.style.display="");const i=document.getElementById("bank-cand-pane-body");if(i){i.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const r=await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!r.ok)throw new Error("cands:"+r.status);const l=await r.json();Jc(e,l.candidates||[])}catch{i.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function Yc(e,n,a){const s=n.history_id,o=n.invoice_no||"-",i=n.vendor||"-",r=n.amount_total!==null&&n.amount_total!==void 0?Ct(n.amount_total):"-",l=n.invoice_date?Kt(n.invoice_date):"-",m=n.filename||"",d=!!a&&e.matched_history_id===s,p="bank-cand-card"+(n.is_auto_picked?" is-auto":"")+(d?" is-picked":"");let c="";return d?c='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":c='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+X(s)+'"><span>'+t(n.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+p+'" data-hid="'+X(s)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+X(i)+"</div>"+Vc(n.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+X(o)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+r+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+X(l)+"</span></div>"+(m?'<div class="bank-cand-card-file" title="'+X(m)+'">'+X(m)+"</div>":"")+(n.reason?'<div class="bank-cand-card-reason">'+X(n.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+c+"</div></div>"}function Jc(e,n){const a=document.getElementById("bank-cand-pane-body");if(!a)return;const s=n||[];let o="";if(e.match_status==="matched")o='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",s.length)+"</div>";else if(e.match_status==="suggested")o='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",s.length)+"</div>";else if(s.length>0)o='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",s.length)+"</div>";else{a.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const i=e.match_status==="matched",r=s.map(l=>Yc(e,l,i)).join("");a.innerHTML=o+'<div class="bank-cand-list">'+r+"</div>",a.querySelectorAll('[data-act="pick"]').forEach(l=>{l.addEventListener("click",()=>{Qc(l.dataset.hid)})}),a.querySelectorAll('[data-act="unmatch"]').forEach(l=>{l.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(e.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),_n(),await Zt(M.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function _n(){const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane");const n=document.getElementById("bank-cand-pane-title"),a=document.getElementById("bank-cand-pane-sub"),s=document.getElementById("bank-cand-pane-body"),o=document.getElementById("bank-cand-pane-foot");n&&(n.textContent=t("bank-cand-pane-empty-title")),a&&(a.textContent=t("bank-cand-pane-empty-sub")),o&&(o.style.display="none"),s&&(s.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const i=document.getElementById("bank-tx-tbody");i&&i.querySelectorAll("tr.is-selected").forEach(r=>r.classList.remove("is-selected")),M.currentTxForDrawer=null}async function Zt(e){try{const n="/api/bank-recon/sessions/"+encodeURIComponent(e)+(M.currentFilter!=="all"?"?filter="+M.currentFilter:""),a=await fetch(n,{headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("detail:"+a.status);const s=await a.json();M.currentSession=s.session,M.currentTxs=s.transactions||[],od()}catch(n){console.warn("[bank-recon] loadSessionDetail failed",n),showToast(t("bank-load-failed"),"error")}}async function Xc(){if(!M.currentSession)return;const e=document.getElementById("btn-bank-run-match"),n=e.innerHTML;e.disabled=!0,e.innerHTML="<span>"+t("bank-matching")+"</span>";try{const a=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(M.currentSession.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!a.ok)throw new Error("match:"+a.status);const s=await a.json();showToast(t("bank-match-done").replace("{matched}",s.matched).replace("{suggested}",s.suggested).replace("{unmatched}",s.unmatched),"success"),await Zt(M.currentSession.id),await Qt()}catch(a){console.warn("[bank-recon] match failed",a),showToast(t("bank-match-failed"),"error")}finally{e.disabled=!1,e.innerHTML=n}}async function Zc(){if(!(!M.currentSession||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const n=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(M.currentSession.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!n.ok)throw new Error("delete:"+n.status);showToast(t("bank-deleted"),"success"),M.currentSession=null,M.currentTxs=[],Bs(),await Qt()}catch(n){console.warn("[bank-recon] delete failed",n),showToast(t("bank-delete-failed"),"error")}}async function vo(){if(M.currentTxForDrawer)try{const e=await fetch("/api/bank-recon/tx/"+encodeURIComponent(M.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!e.ok)throw new Error("ignore:"+e.status);_n(),await Zt(M.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}async function Qc(e){if(M.currentTxForDrawer)try{const n=await fetch("/api/bank-recon/tx/"+encodeURIComponent(M.currentTxForDrawer.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:e})});if(!n.ok)throw new Error("pick:"+n.status);showToast(t("bank-matched-ok"),"success"),_n(),await Zt(M.currentSession.id)}catch{showToast(t("bank-action-failed"),"error")}}function Ri(){if(!M.currentSession)return;const e=M.currentSession;document.getElementById("bank-detail-title").textContent=(e.bank_code||"-")+(e.account_last4?" ···"+e.account_last4:"")+" · "+(e.source_filename||""),document.getElementById("bank-meta-period").textContent=qi(e.period_start,e.period_end)||"-",document.getElementById("bank-meta-opening").textContent=Ct(e.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+Ct(e.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+Ct(e.total_outflow),document.getElementById("bank-meta-closing").textContent=Ct(e.closing_balance);const n=M.currentTxs||[],a=n.length;let s=0,o=0,i=0;for(const r of n){const l=r.match_status||"unmatched";l==="matched"?s++:l==="suggested"?o++:i++}document.getElementById("bank-stat-total").textContent=a,document.getElementById("bank-stat-matched").textContent=s,document.getElementById("bank-stat-suggested").textContent=o,document.getElementById("bank-stat-unmatched").textContent=i}function Es(){const e=document.getElementById("bank-tx-tbody");if(!e)return;let n=M.currentTxs||[];if(M.currentFilter!=="all"&&(n=n.filter(a=>M.currentFilter==="matched"?a.match_status==="matched":M.currentFilter==="suggested"?a.match_status==="suggested":M.currentFilter==="unmatched"?a.match_status==="unmatched"||a.match_status==="ignored":!0)),n.length===0){e.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(e.innerHTML=n.map(a=>ed(a)).join(""),e.querySelectorAll("tr[data-tx-id]").forEach(a=>{a.addEventListener("click",()=>{const s=a.dataset.txId,o=M.currentTxs.find(i=>i.id===s);o&&(e.querySelectorAll("tr.is-selected").forEach(i=>i.classList.remove("is-selected")),a.classList.add("is-selected"),Kc(o))})}),M.currentTxForDrawer){const a=e.querySelector('tr[data-tx-id="'+M.currentTxForDrawer.id+'"]');a&&a.classList.add("is-selected")}}function ed(e){const n=e.direction==="OUT",a=n?"-":"+",s=n?"bank-out":"bank-in",o=e.match_status||"unmatched",i=t("bank-match-"+o)||o,r=Kt(e.tx_date),l=e.channel?`<span class="bank-tx-channel">${X(e.channel)}</span>`:"";return`
        <tr data-tx-id="${X(e.id)}">
            <td class="bank-tx-date">${X(r)}</td>
            <td class="bank-tx-desc">${l}${X(e.description||"-")}</td>
            <td class="bank-td-amount ${s}">${a}${Ct(e.amount)}</td>
            <td><span class="bank-tx-match mt-${o}">${X(i)}</span></td>
        </tr>
    `}function Is(){const e=document.getElementById("bank-client-badge");if(!e||!M.currentSession)return;const n=M.currentSession.client_id,a=document.getElementById("bank-client-badge-dot"),s=document.getElementById("bank-client-badge-name"),o=document.getElementById("bank-client-badge-caret"),i=typeof _userInfo<"u"?_userInfo:null,r=!(i&&i.role==="member");if(n!=null){const l=(window._clientsCache||[]).find(m=>Number(m.id)===Number(n));e.classList.remove("is-empty"),a&&(a.style.background=l&&l.color||"#111111"),s&&(s.textContent=l&&(l.short_name||l.name)||"#"+n)}else e.classList.add("is-empty"),a&&(a.style.background=""),s&&(s.textContent=t("bank-client-none"));r?(e.classList.remove("is-readonly"),e.disabled=!1,o&&(o.style.display="")):(e.classList.add("is-readonly"),e.disabled=!0,o&&(o.style.display="none")),e.style.display=""}function td(){if(!M.currentSession)return;const e=typeof _userInfo<"u"?_userInfo:null;if(!!(e&&e.role==="member"))return;M.pickerSelected=M.currentSession.client_id!=null?Number(M.currentSession.client_id):null,zi();const a=document.getElementById("bank-client-picker-modal");a&&(a.style.display="")}function Fi(){const e=document.getElementById("bank-client-picker-modal");e&&(e.style.display="none"),M.pickerSelected=null}function zi(){const e=document.getElementById("bank-client-picker-list");if(!e)return;const n=(window._clientsCache||[]).filter(s=>s&&(s.is_active===!0||s.is_active===void 0)),a=[];a.push('<div class="bank-client-picker-row is-none'+(M.pickerSelected==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+X(t("bank-client-picker-none"))+"</span></div>"),n.forEach(s=>{const o=Number(s.id)===Number(M.pickerSelected)?" is-selected":"";a.push('<div class="bank-client-picker-row'+o+'" data-cid="'+X(s.id)+'"><span class="bank-cp-dot" style="background:'+X(s.color||"#111111")+'"></span><span>'+X(s.short_name||s.name||"#"+s.id)+"</span></div>")}),e.innerHTML=a.join(""),e.querySelectorAll(".bank-client-picker-row").forEach(s=>{s.addEventListener("click",()=>{const o=s.dataset.cid;M.pickerSelected=o?Number(o):null,zi()})})}async function nd(){if(M.currentSession)try{const e=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(M.currentSession.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:M.pickerSelected})});if(!e.ok)throw new Error("client:"+e.status);M.currentSession.client_id=M.pickerSelected,Is(),showToast(t("bank-client-changed"),"success"),Fi();try{await Qt()}catch{}}catch(e){console.warn("[bank-recon] save client failed",e),showToast(t("bank-client-change-failed"),"error")}}async function Qt(){try{const e=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!e.ok)throw new Error("sessions:"+e.status);M.sessions=await e.json(),Qn()}catch(e){console.warn("[bank-recon] loadSessions failed",e),M.sessions=[],Qn()}}function fo(){const e=document.getElementById("bank-status-summary");if(!e)return;if(M.sessions.length===0){e.textContent=t("bank-pill-none");return}let a=0;for(const s of M.sessions)s.parse_status==="parsed"&&(s.unmatched_count||0)>0&&a++;e.textContent=a>0?t("bank-pill-pending").replace("{n}",a):t("bank-pill-ok")}function Qn(){const e=document.getElementById("bank-sessions-list");if(!e)return;let n=M.sessions||[];if(M.sessionFilter==="parsed"?n=n.filter(a=>a.parse_status==="parsed"):M.sessionFilter==="failed"&&(n=n.filter(a=>a.parse_status==="parse_failed")),!M.sessions||M.sessions.length===0){e.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(n.length===0){e.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}e.innerHTML=n.map(a=>ad(a)).join(""),e.querySelectorAll(".bank-session-row").forEach(a=>{a.addEventListener("click",s=>{s.target.closest(".bank-session-trash")||Zt(a.dataset.sessionId)})}),e.querySelectorAll(".bank-session-trash").forEach(a=>{a.addEventListener("click",s=>{s.stopPropagation();const o=a.dataset.sessionId,i=a.dataset.sessionName||"";Ni(o,i)})})}async function Ni(e,n){if(!e)return;const a=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",n||"");if(await showConfirm(a,{danger:!0}))try{const o=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(e),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!o.ok)throw new Error("delete:"+o.status);showToast(t("bank-deleted"),"success"),M.currentSession&&M.currentSession.id===e&&(M.currentSession=null,M.currentTxs=[],Bs()),await Qt(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(o){console.warn("[bank-recon] delete failed",o),showToast(t("bank-delete-failed"),"error")}}function ad(e){const n=(e.bank_code||"OTHER").toUpperCase(),a=qi(e.period_start,e.period_end),s=e.account_last4?"···"+e.account_last4:"",o=sd(e),i=Kt(e.created_at);return`
        <div class="bank-session-row" data-session-id="${X(e.id)}">
            <div class="bank-session-bank bk-${X(n)}">${X(n)}</div>
            <div class="bank-session-info">
                <div class="bank-session-title">${X(e.source_filename||a||"-")}</div>
                <div class="bank-session-meta">${X(a)} · ${X(s)} · ${X(i)}</div>
            </div>
            <div class="bank-session-counts">${o}</div>
            <button class="bank-session-trash" data-session-id="${X(e.id)}" data-session-name="${X(e.source_filename||"")}" title="${X(t("bank-session-delete-tip")||"删除")}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                </svg>
            </button>
            <div class="bank-session-arrow">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
            </div>
        </div>
    `}function sd(e){if(e.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(e.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const n=e.tx_count||0,a=e.matched_count||0,s=e.unmatched_count||0,o=[`<span class="bank-session-count">${n} ${t("bank-count-tx")}</span>`];return a>0&&o.push(`<span class="bank-session-count cnt-matched">${a} ${t("bank-count-matched")}</span>`),s>0&&o.push(`<span class="bank-session-count cnt-unmatched">${s} ${t("bank-count-unmatched")}</span>`),o.join("")}function od(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",Ri(),Es(),Is()}function Bs(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const e=document.getElementById("bank-detail-body");e&&e.classList.remove("has-pane"),M.currentTxForDrawer=null}const id=3;function rd(){return M.qSeq+=1,"q"+M.qSeq+"_"+Date.now()}async function ld(e){const n=Array.from(e.target.files||[]);if(e.target.value="",n.length!==0){for(const a of n){const s={id:rd(),file:a,name:a.name,size:a.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};a.name.toLowerCase().endsWith(".pdf")?a.size>20*1024*1024&&(s.status="failed",s.error_code="bank_recon.file_too_large"):(s.status="failed",s.error_code="bank_recon.only_pdf"),M.queue.push(s)}cd(),je(),Ls()}}function cd(){const e=document.getElementById("bank-upload-queue");e&&(e.style.display=""),Uc(),Gc()}function je(){const e=document.getElementById("bank-upload-queue-list"),n=document.getElementById("bank-upload-queue-summary");if(!e)return;if(M.queue.length===0){e.innerHTML="",n&&(n.textContent="");const r=document.getElementById("bank-upload-queue");r&&(r.style.display="none");return}let a=0,s=0,o=0,i=0;for(const r of M.queue)r.status==="ok"?a++:r.status==="failed"?s++:r.status==="uploading"||r.status==="parsing"?o++:i++;n&&(n.textContent=t("bank-queue-summary").replace("{ok}",a).replace("{run}",o).replace("{wait}",i).replace("{fail}",s)),e.innerHTML=M.queue.map(dd).join(""),e.querySelectorAll("[data-q-act]").forEach(r=>{const l=r.dataset.qAct,m=r.dataset.qId;r.addEventListener("click",()=>{l==="retry"&&pd(m),l==="remove"&&ud(m)})})}function dd(e){const n=(e.size/1024).toFixed(0)+" KB";let a="",s="";if(e.status==="pending")a='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",s='<button data-q-act="remove" data-q-id="'+X(e.id)+'" class="bq-act">×</button>';else if(e.status==="uploading")a='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(e.progress||0)+'%"></div></div>';else if(e.status==="parsing")a='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(e.status==="ok")a='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",e.tx_count||0)+"</span>",s='<button data-q-act="remove" data-q-id="'+X(e.id)+'" class="bq-act">×</button>';else if(e.status==="failed"){const o=Wc(e.error_code||"unknown");a='<span class="bq-stat bq-fail" title="'+X(o)+'">'+X(o)+"</span>",s='<button data-q-act="retry" data-q-id="'+X(e.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+X(e.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+X(e.id)+'"><div class="bq-name" title="'+X(e.name)+'">'+X(e.name)+'</div><div class="bq-size">'+n+'</div><div class="bq-status">'+a+'</div><div class="bq-actions">'+s+"</div></div>"}function pd(e){const n=M.queue.find(a=>a.id===e);n&&(n.status="pending",n.error_code=null,n.progress=0,je(),Ls())}function ud(e){const n=M.queue.findIndex(s=>s.id===e);if(n<0)return;const a=M.queue[n];a.status==="uploading"||a.status==="parsing"||(M.queue.splice(n,1),je())}function md(){M.queue=M.queue.filter(e=>e.status!=="ok"),je()}async function Ls(){for(;;){if(M.queue.filter(a=>a.status==="uploading"||a.status==="parsing").length>=id)return;const n=M.queue.find(a=>a.status==="pending");if(!n){M.queue.every(a=>a.status==="ok"||a.status==="failed")&&(await Qt(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}vd(n).then(()=>Ls())}}async function vd(e){e.status="uploading",e.progress=0,je();try{const n=new FormData;n.append("file",e.file,e.name);const a=await new Promise((o,i)=>{const r=new XMLHttpRequest;r.open("POST","/api/bank-recon/upload"),r.setRequestHeader("Authorization","Bearer "+token),r.upload.onprogress=l=>{l.lengthComputable&&(e.progress=Math.min(99,Math.round(l.loaded/l.total*100)),je())},r.upload.onload=()=>{e.status="parsing",je()},r.onload=()=>{r.status>=200&&r.status<300?o({status:r.status,text:r.responseText}):o({status:r.status,text:r.responseText})},r.onerror=()=>i(new Error("network")),r.send(n)});let s={};try{s=JSON.parse(a.text||"{}")}catch{s={}}if(a.status>=400){e.status="failed",e.error_code=s&&s.detail||"unknown",je();return}if(s.parse_status==="parse_failed"){e.status="failed",e.error_code=s.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",je();return}e.status="ok",e.tx_count=s.tx_count||0,e.session_id=s.session_id||null,je()}catch(n){console.warn("[bank-recon] upload failed",n),e.status="failed",e.error_code="network",je()}}async function Oi(){if(M.loaded){fo();return}M.loaded=!0,fd(),await Qt(),fo()}function fd(){const e=document.getElementById("bank-file-input");e&&!e._bound&&(e._bound=!0,e.addEventListener("change",ld));const n=document.getElementById("btn-bank-queue-clear-done");n&&!n._bound&&(n._bound=!0,n.addEventListener("click",md));const a=document.getElementById("btn-bank-back");a&&!a._bound&&(a._bound=!0,a.addEventListener("click",()=>{M.currentSession=null,M.currentTxs=[],Bs()}));const s=document.getElementById("btn-bank-delete");s&&!s._bound&&(s._bound=!0,s.addEventListener("click",Zc));const o=document.getElementById("btn-bank-run-match");o&&!o._bound&&(o._bound=!0,o.addEventListener("click",Xc)),document.querySelectorAll(".bank-filter-btn").forEach(p=>{p._bound||(p._bound=!0,p.addEventListener("click",()=>{M.currentFilter=p.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(c=>{c.classList.toggle("active",c===p)}),Es()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(p=>{p._bound||(p._bound=!0,p.addEventListener("click",_n))});const i=document.getElementById("btn-bank-cand-pane-close");i&&!i._bound&&(i._bound=!0,i.addEventListener("click",_n));const r=document.getElementById("btn-bank-cand-ignore");r&&!r._bound&&(r._bound=!0,r.addEventListener("click",vo));const l=document.getElementById("btn-bank-cand-ignore-pane");l&&!l._bound&&(l._bound=!0,l.addEventListener("click",vo));const m=document.getElementById("bank-client-badge");m&&!m._bound&&(m._bound=!0,m.addEventListener("click",td)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(p=>{p._bound||(p._bound=!0,p.addEventListener("click",Fi))});const d=document.getElementById("btn-bank-client-picker-save");d&&!d._bound&&(d._bound=!0,d.addEventListener("click",nd)),document.querySelectorAll(".bank-sessions-chip").forEach(p=>{p._bound||(p._bound=!0,p.addEventListener("click",()=>{M.sessionFilter=p.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(c=>{c.classList.toggle("active",c===p)}),Qn()}))})}window._deleteBankSession=Ni;window._loadBankReconPanel=Oi;window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(Qn(),M.currentSession&&(Ri(),Es(),Is(),!M.currentTxForDrawer)){const e=document.getElementById("bank-cand-pane-title"),n=document.getElementById("bank-cand-pane-sub");e&&(e.textContent=t("bank-cand-pane-empty-title")),n&&(n.textContent=t("bank-cand-pane-empty-sub"))}je()}};typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon);window._openBankSession=async function(e){e&&(M.loaded||await Oi(),await Zt(e))};(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();const hd=`
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
                        <label data-i18n="client-field-party-type">买方类型</label>
                        <select id="client-input-party-type">
                            <option value="" data-i18n="client-party-unset">未指定</option>
                            <option value="company" data-i18n="client-party-company">公司</option>
                            <option value="individual" data-i18n="client-party-individual">个人</option>
                            <option value="foreigner" data-i18n="client-party-foreigner">外国</option>
                            <option value="anonymous" data-i18n="client-party-anonymous">匿名</option>
                        </select>
                    </div>
                    <div>
                        <label data-i18n="client-field-branch">总公司 / 分店</label>
                        <input type="text" id="client-input-branch" maxlength="120" data-i18n-placeholder="client-field-branch-ph">
                    </div>
                </div>
                <div class="form-row">
                    <label data-i18n="client-field-promptpay">PromptPay 收款号</label>
                    <input type="text" id="client-input-promptpay" maxlength="40">
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
    `,gd=`
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
                <div class="form-row">
                    <label data-i18n="wsclient-field-address">地址</label>
                    <input type="text" id="wsclient-input-address" maxlength="500" data-i18n-placeholder="wsclient-field-address-ph" placeholder="开票地址(印在税票上)">
                </div>
                <div class="form-row">
                    <label data-i18n="wsclient-field-branch">总公司 / 分公司</label>
                    <input type="text" id="wsclient-input-branch" maxlength="120" data-i18n-placeholder="wsclient-field-branch-ph" placeholder="สำนักงานใหญ่(总公司)或 สาขาที่ 1">
                </div>
                <div class="form-row">
                    <label data-i18n="wsclient-field-phone">电话</label>
                    <input type="text" id="wsclient-input-phone" maxlength="50">
                </div>
                <div class="form-row form-row-check">
                    <label class="wsclient-check"><input type="checkbox" id="wsclient-input-vat" checked> <span data-i18n="wsclient-field-vat">已注册 VAT(可开税务发票)</span></label>
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
    `;$e("client-modal-mask",hd);$e("wsclient-modal-mask",gd);const U={clients:[],editingClientId:null,historyClientFilter:"",custTab:"seller",sellerClients:[],editingWsClientId:null,catCache:{fetched:0,items:[],supplier_count:0}},Ie={page:0,pageSize:12,keyword:""},nt=new Set,ea={keyword:""};function bd(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function Ye(e,n={}){const a=await fetch(e,{...n,headers:{"Content-Type":"application/json",...bd(),...n.headers||{}}});if(!a.ok){const s=await a.json().catch(()=>({}));throw new Error(s.detail||"HTTP "+a.status)}return a.json()}function yd(){const e=document.querySelector("#client-color-picker .color-swatch.active");return e?e.dataset.color:"#111111"}function ho(e){const n=document.getElementById("drawer-cat-learned-tag");n&&e>0&&(n.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",String(e)))}async function en(){try{const e=await Ye("/api/clients");U.clients=e.clients||[],window._clientsCache=U.clients}catch(e){console.error("loadClientsCache fail",e),U.clients=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return U.clients}function wd(){const e=Ie.keyword.trim().toLowerCase();return e?U.clients.filter(n=>(n.name||"").toLowerCase().includes(e)||(n.short_name||"").toLowerCase().includes(e)||(n.tax_id||"").toLowerCase().includes(e)):U.clients}function $s(){const e=wd(),n=Ie.pageSize,a=Math.max(0,Math.ceil(e.length/n)-1);Ie.page>a&&(Ie.page=a);const s=Ie.page*n;return{all:e,items:e.slice(s,s+n),start:s,ps:n,total:e.length,maxPage:a}}function Ze(){const e=document.getElementById("buyer-tbody");if(!e)return;const{items:n,start:a,ps:s,total:o,maxPage:i}=$s();o?e.innerHTML=n.map(d=>{const p=nt.has(d.id);return`<div class="cust-row buyer-grid${p?" selected":""}" data-cid="${d.id}">
                <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${d.id}" ${p?"checked":""}></div>
                <div style="min-width:0">
                    <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(d.color||"#111")}"></span><span class="cust-name-text">${escapeHtml(d.name)}</span></div>
                    ${d.tax_id?`<div class="cust-cell-sub">${escapeHtml(d.tax_id)}</div>`:""}
                </div>
                <div class="align-right">${d.invoice_count||0}</div>
                <div class="align-right cust-cell-amount">฿${(d.total_amount||0).toLocaleString(void 0,{maximumFractionDigits:0})}</div>
                <div class="cust-row-actions">
                    <button class="cust-row-btn" data-action="edit" data-cid="${d.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                    <button class="cust-row-btn" data-action="export" data-cid="${d.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t("client-card-export"))}</span></button>
                </div>
            </div>`}).join(""):e.innerHTML=`<div class="cust-empty">${escapeHtml(t(Ie.keyword?"cust-no-match":"clients-empty"))}</div>`;const r=document.getElementById("buyer-pager-info");r&&(r.textContent=o?`${a+1}–${Math.min(a+s,o)} / ${o}`:"0");const l=document.getElementById("buyer-prev");l&&(l.disabled=Ie.page<=0);const m=document.getElementById("buyer-next");m&&(m.disabled=Ie.page>=i),Vi()}function Vi(){const e=nt.size,n=document.getElementById("buyer-batch-bar");n&&(n.style.display=e?"flex":"none");const a=document.getElementById("buyer-batch-count");a&&(a.textContent=t("cust-selected-n").replace("{n}",e));const s=document.getElementById("buyer-check-all");if(s){const{items:o}=$s(),i=o.map(l=>l.id),r=i.filter(l=>nt.has(l)).length;s.checked=i.length>0&&r===i.length,s.indeterminate=r>0&&r<i.length}}function kd(){nt.clear(),Ze()}async function xd(){const e=Array.from(nt);if(!(!e.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",e.length),{danger:!0})))try{await Ye("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:e})}),showToast(t("client-msg-deleted"),"success"),nt.clear(),await en(),Ze(),ba(),Ss()}catch{showToast(t("client-msg-save-fail"),"fail")}}function vn(e){U.editingClientId=e?e.id:null;const n=!!e;document.getElementById("client-modal-title").textContent=t(n?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=e&&e.name||"",document.getElementById("client-input-short").value=e&&e.short_name||"",document.getElementById("client-input-tax").value=e&&e.tax_id||"",document.getElementById("client-input-address").value=e&&e.address||"",document.getElementById("client-input-contact").value=e&&e.contact_person||"",document.getElementById("client-input-phone").value=e&&e.contact_phone||"",document.getElementById("client-input-email").value=e&&e.contact_email||"",document.getElementById("client-input-notes").value=e&&e.notes||"",document.getElementById("client-input-party-type").value=e&&e.party_type||"",document.getElementById("client-input-branch").value=e&&e.branch||"",document.getElementById("client-input-promptpay").value=e&&e.promptpay_id||"";const a=e&&e.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(s=>{s.classList.toggle("active",s.dataset.color===a)}),document.getElementById("client-modal-delete").style.display=n?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function fn(){document.getElementById("client-modal-mask").style.display="none",U.editingClientId=null}async function _d(){const e=document.getElementById("client-input-name").value.trim();if(!e){showToast(t("client-msg-name-required"),"fail");return}const n={name:e,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:yd(),party_type:document.getElementById("client-input-party-type").value||null,branch:document.getElementById("client-input-branch").value.trim()||null,promptpay_id:document.getElementById("client-input-promptpay").value.trim()||null};try{U.editingClientId?(await Ye(`/api/clients/${U.editingClientId}`,{method:"PATCH",body:JSON.stringify(n)}),showToast(t("client-msg-updated"),"success")):(await Ye("/api/clients",{method:"POST",body:JSON.stringify(n)}),showToast(t("client-msg-created"),"success")),fn(),await en(),currentRoute==="clients"&&Ze(),ba(),Ss()}catch(a){console.error("saveClient fail",a);const s=a&&a.message?a.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+s,"fail")}}async function Ed(){if(!U.editingClientId)return;const e=U.clients.find(s=>s.id===U.editingClientId);if(!e)return;const n=t("client-delete-confirm").replace("{name}",e.name);if(await showConfirm(n,{danger:!0}))try{await Ye(`/api/clients/${U.editingClientId}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),fn(),await en(),currentRoute==="clients"&&Ze(),ba(),Ss()}catch(s){console.error(s),showToast(t("client-msg-save-fail"),"fail")}}async function Id(e){const n=U.clients.find(a=>a.id===e);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(e,n?n.name:"");return}try{const a=localStorage.getItem("mrpilot_token"),s=await fetch(`/api/clients/${e}/export?month=all`,{headers:{Authorization:"Bearer "+a}});if(!s.ok){let m="HTTP "+s.status;try{const d=await s.json();d&&d.detail&&(m=d.detail)}catch{}throw new Error(m)}const o=await s.blob();if(o.size<200){showToast(t("client-export-month-empty"),"info");return}const i=n&&n.name?n.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",r=URL.createObjectURL(o),l=document.createElement("a");l.href=r,l.download=`${i}_export.csv`,l.click(),URL.revokeObjectURL(r)}catch(a){console.error("exportClient fail",a),showToast(t("client-msg-save-fail")+" · "+(a.message||""),"fail")}}function ba(){const e=document.getElementById("drawer-client-select");if(!e)return;const n=e.value;e.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+U.clients.map(a=>`<option value="${a.id}">${escapeHtml(a.name)}</option>`).join(""),e.value=n||""}function Ss(){const e=document.getElementById("history-client-filter");if(!e)return;const n=e.value;e.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+U.clients.map(a=>`<option value="${a.id}">${escapeHtml(a.name)}</option>`).join(""),e.value=n||""}function Bd(e){U.custTab=e==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(s=>s.classList.toggle("active",s.dataset.custTab===U.custTab));const n=document.getElementById("cust-pane-seller"),a=document.getElementById("cust-pane-buyer");n&&n.classList.toggle("active",U.custTab==="seller"),a&&a.classList.toggle("active",U.custTab==="buyer")}function Ld(){const e=window._userInfo||{},n=String(e.role||"").toLowerCase(),a=String(e.tenant_role||"").toLowerCase();return e.is_super_admin===!0||e.is_owner===!0||n==="owner"||n==="admin"||a==="owner"||a==="admin"}function Ui(){window._workspaceClientsCache=U.sellerClients,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function Cs(){try{const e=await Ye("/api/workspace/clients");U.sellerClients=e&&(e.clients||e.items)||[],window._workspaceClientsCache=U.sellerClients}catch(e){console.error("loadSellerCache fail",e),U.sellerClients=[]}return U.sellerClients}function $d(){const e=ea.keyword.trim().toLowerCase();return e?U.sellerClients.filter(n=>(n.name||"").toLowerCase().includes(e)||(n.tax_id||"").toLowerCase().includes(e)):U.sellerClients}function Ht(){const e=document.getElementById("seller-tbody");if(!e)return;const n=Ld(),a=document.getElementById("btn-seller-new");a&&(a.style.display=n?"":"none");const s=$d(),o=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!s.length){e.innerHTML=`<div class="cust-empty">${escapeHtml(t(ea.keyword?"cust-no-match":"seller-empty"))}</div>`;return}e.innerHTML=s.map(i=>{const l=o!=null&&Number(o)===Number(i.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${i.id}">${escapeHtml(t("seller-set-current"))}</button>`,m=n?`
            <button class="cust-row-btn" data-saction="edit" data-wid="${i.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
            <button class="cust-row-btn danger" data-saction="archive" data-wid="${i.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${i.id}">
            <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(i.name||"#"+i.id)}</span></div>
            <div class="cust-cell-tax">${escapeHtml(i.tax_id||"—")}</div>
            <div class="align-right">${i.invoice_count||0}</div>
            <div class="cust-row-actions">${l}${m}</div>
        </div>`}).join("")}function go(e){U.editingWsClientId=e?e.id:null,document.getElementById("wsclient-modal-title").textContent=t(e?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=e&&e.name||"",document.getElementById("wsclient-input-tax").value=e&&e.tax_id||"",document.getElementById("wsclient-input-address").value=e&&e.address||"",document.getElementById("wsclient-input-branch").value=e&&e.branch||"",document.getElementById("wsclient-input-phone").value=e&&e.phone||"",document.getElementById("wsclient-input-vat").checked=e?e.vat_registered!==!1:!0,document.getElementById("wsclient-modal-archive").style.display=e?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function hn(){document.getElementById("wsclient-modal-mask").style.display="none",U.editingWsClientId=null}async function Sd(){const e=document.getElementById("wsclient-input-name").value.trim(),n=document.getElementById("wsclient-input-tax").value.trim(),a=document.getElementById("wsclient-input-address").value.trim(),s=document.getElementById("wsclient-input-branch").value.trim(),o=document.getElementById("wsclient-input-phone").value.trim(),i=document.getElementById("wsclient-input-vat").checked;if(!e){showToast(t("client-msg-name-required"),"fail");return}const r={address:a||null,branch:s||null,phone:o||null,vat_registered:i};try{U.editingWsClientId?(await Ye("/api/workspace/clients/"+U.editingWsClientId,{method:"PATCH",body:JSON.stringify({name:e,tax_id:n,...r})}),showToast(t("client-msg-updated"),"success")):(await Ye("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:e,tax_id:n||null,...r})}),showToast(t("client-msg-created"),"success")),hn(),await Cs(),Ht(),Ui()}catch(l){const m=l&&l.message?l.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+m,"fail")}}async function bo(){if(!U.editingWsClientId)return;const e=U.sellerClients.find(a=>Number(a.id)===Number(U.editingWsClientId));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",e?e.name:""),{danger:!0}))try{const a=U.editingWsClientId;await Ye("/api/workspace/clients/"+a,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(a)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),hn(),await Cs(),Ht(),Ui()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const e=document.getElementById("seller-tbody");e&&(e.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const n=document.getElementById("buyer-tbody");n&&(n.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([Cs(),en()]),Ht(),Ze()};window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&Ht()});window.bindDrawerClient=function(e,n){const a=document.getElementById("drawer-client-select");if(!a)return;if(ba(),a.value=n?String(n):"",!e){a.onchange=null;const o=document.getElementById("drawer-client-add");o&&(o.onclick=()=>vn(null));return}a.onchange=async()=>{const o=a.value?parseInt(a.value,10):null;try{await Ye(`/api/history/${e}/assign_client`,{method:"POST",body:JSON.stringify({client_id:o})}),showToast(t("client-msg-updated"),"success");const i=_results[_drawerIdx];i&&(i.client_id=o),await en()}catch(i){console.error(i),showToast(t("client-msg-save-fail"),"fail"),a.value=n?String(n):""}};const s=document.getElementById("drawer-client-add");s&&(s.onclick=()=>vn(null))};window.fillCategoryDatalist=async function(){try{const e=document.getElementById("drawer-cat-datalist"),n=Date.now();if(n-U.catCache.fetched<300*1e3){e&&(e.innerHTML=U.catCache.items.map(s=>`<option value="${escapeHtml(s)}">`).join("")),ho(U.catCache.supplier_count);return}const a=await Ye("/api/categories",{method:"GET"});U.catCache.fetched=n,U.catCache.items=a&&a.categories||[],U.catCache.supplier_count=a&&a.supplier_count||0,e&&(e.innerHTML=U.catCache.items.map(s=>`<option value="${escapeHtml(s)}">`).join("")),ho(U.catCache.supplier_count)}catch(e){console.warn("fillCategoryDatalist failed",e)}};window.getHistoryClientFilter=function(){return U.historyClientFilter};document.addEventListener("DOMContentLoaded",()=>{const e=document.querySelector(".cust-tab-bar");e&&e.addEventListener("click",L=>{const $=L.target.closest("[data-cust-tab]");$&&Bd($.dataset.custTab)});const n=document.getElementById("btn-buyer-new");n&&n.addEventListener("click",()=>vn(null));const a=document.getElementById("buyer-tbody");a&&a.addEventListener("click",L=>{const $=L.target.closest(".buyer-row-check");if($){const R=parseInt($.dataset.cid,10);$.checked?nt.add(R):nt.delete(R);const G=$.closest(".cust-row");G&&G.classList.toggle("selected",$.checked),Vi();return}const S=L.target.closest(".cust-row-btn");if(S){L.stopPropagation();const R=parseInt(S.dataset.cid,10);if(S.dataset.action==="edit"){const G=U.clients.find(se=>se.id===R);G&&vn(G)}else S.dataset.action==="export"&&Id(R);return}const H=L.target.closest(".cust-row");if(H&&!L.target.closest(".cust-cell-check")){const R=U.clients.find(G=>G.id===parseInt(H.dataset.cid,10));R&&vn(R)}});const s=document.getElementById("buyer-check-all");s&&s.addEventListener("change",()=>{const{items:L}=$s();L.forEach($=>{s.checked?nt.add($.id):nt.delete($.id)}),Ze()});const o=document.getElementById("buyer-batch-cancel");o&&o.addEventListener("click",kd);const i=document.getElementById("buyer-batch-delete");i&&i.addEventListener("click",xd);const r=document.getElementById("buyer-prev");r&&r.addEventListener("click",()=>{Ie.page>0&&(Ie.page--,Ze())});const l=document.getElementById("buyer-next");l&&l.addEventListener("click",()=>{Ie.page++,Ze()});const m=document.getElementById("buyer-search");if(m){let L;m.addEventListener("input",()=>{clearTimeout(L),L=setTimeout(()=>{Ie.keyword=m.value,Ie.page=0;const $=document.getElementById("buyer-search-clear");$&&($.style.display=m.value?"":"none"),Ze()},200)})}const d=document.getElementById("buyer-search-clear");d&&d.addEventListener("click",()=>{const L=document.getElementById("buyer-search");L&&(L.value=""),Ie.keyword="",Ie.page=0,d.style.display="none",Ze()});const p=document.getElementById("btn-seller-new");p&&p.addEventListener("click",()=>go(null));const c=document.getElementById("seller-tbody");c&&c.addEventListener("click",L=>{const $=L.target.closest("[data-saction]");if(!$)return;L.stopPropagation();const S=parseInt($.dataset.wid,10),H=$.dataset.saction,R=U.sellerClients.find(G=>Number(G.id)===S);H==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(S),Ht(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",R?R.name:""),"success")):H==="edit"?R&&go(R):H==="archive"&&(U.editingWsClientId=S,bo())});const u=document.getElementById("seller-search");if(u){let L;u.addEventListener("input",()=>{clearTimeout(L),L=setTimeout(()=>{ea.keyword=u.value;const $=document.getElementById("seller-search-clear");$&&($.style.display=u.value?"":"none"),Ht()},200)})}const v=document.getElementById("seller-search-clear");v&&v.addEventListener("click",()=>{const L=document.getElementById("seller-search");L&&(L.value=""),ea.keyword="",v.style.display="none",Ht()});const f=document.getElementById("wsclient-modal-close");f&&f.addEventListener("click",hn);const y=document.getElementById("wsclient-modal-cancel");y&&y.addEventListener("click",hn);const b=document.getElementById("wsclient-modal-save");b&&b.addEventListener("click",Sd);const h=document.getElementById("wsclient-modal-archive");h&&h.addEventListener("click",bo);const g=document.getElementById("wsclient-modal-mask");g&&g.addEventListener("click",L=>{L.target===g&&hn()});const _=document.getElementById("client-modal-close");_&&_.addEventListener("click",fn);const w=document.getElementById("client-modal-cancel");w&&w.addEventListener("click",fn);const k=document.getElementById("client-modal-save");k&&k.addEventListener("click",_d);const x=document.getElementById("client-modal-delete");x&&x.addEventListener("click",Ed);const E=document.getElementById("client-modal-mask");E&&E.addEventListener("click",L=>{L.target===E&&fn()});const I=document.getElementById("client-color-picker");I&&I.addEventListener("click",L=>{const $=L.target.closest(".color-swatch");$&&(I.querySelectorAll(".color-swatch").forEach(S=>S.classList.remove("active")),$.classList.add("active"))});const B=document.getElementById("history-client-filter");B&&B.addEventListener("change",()=>{U.historyClientFilter=B.value,typeof renderHistoryList=="function"&&renderHistoryList()})});setTimeout(()=>en(),1e3);(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(s=>{const o=s.getAttribute("data-i18n-placeholder");a[n][o]&&(s.placeholder=a[n][o])}))}catch{}}})();const q={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0},D={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null},Nt={batchLoading:!1};function bt(e,n){let a=t(e)||e;if(n)for(const s in n)a=a.replace(new RegExp("\\{"+s+"\\}","g"),String(n[s]));return a}function Cd(e){return e==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
    </svg>`}function Td(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 19l5 5 13-13"/>
        <circle cx="20" cy="20" r="17"/>
    </svg>`}function Hd(e){if(e==null)return"—";const n=parseFloat(String(e));return isNaN(n)?"—":"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function Md(e){return e?e.slice(0,10):"—"}function rt(e){if(e==null)return"—";const n=typeof e=="number"?e:parseFloat(String(e).replace(/,/g,""));return isNaN(n)?escapeHtml(String(e)):"฿ "+n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}const Ad={"R-VAT-01":"risk.vat_mismatch","R-VAT-02":"risk.total_mismatch","R-SUM-01":"risk.line_sum_mismatch","R-LINE-01":"risk.line_amount_mismatch","R-MULTIPAGE-01":"risk.multipage_mismatch","R-TAXID-01":"risk.seller_tax_id_invalid","R-TAXID-02":"risk.buyer_tax_id_invalid","R-TAXID-03":"risk.tax_id_placeholder","R-DUP-01":"risk.duplicate_exact","R-DUP-02":"risk.duplicate_suspected","R-DATE-01":"risk.invoice_date_unparseable","R-DATE-02":"risk.invoice_date_out_of_period","R-SUP-01":"risk.supplier_not_allowlisted","R-SUP-02":"risk.supplier_force_review","R-LIMIT-01":"risk.amount_over_limit","R-CAT-01":"risk.category_no_auto_push"};function Ha(e,n){const a=t(e);return a&&a!==e?a:n}function Ts(e){const n=e.rule_code||"",a=e.detail&&e.detail.message_key;if(a){const i=Ha(a,"");if(i)return i}const s=Ha("exc-rule-"+n,"");if(s)return s;const o=Ad[n];if(o){const i=Ha(o,"");if(i)return i}return n}const Pd=[{labelKey:"exc-grp-arithmetic",codes:["R-VAT-01","R-VAT-02","R-SUM-01","R-LINE-01","R-MULTIPAGE-01","math_mismatch"]},{labelKey:"exc-grp-taxid",codes:["R-TAXID-01","R-TAXID-02","R-TAXID-03","tax_id_format_invalid"]},{labelKey:"exc-grp-dup",codes:["R-DUP-01","R-DUP-02","duplicate"]},{labelKey:"exc-grp-date",codes:["R-DATE-01","R-DATE-02"]},{labelKey:"exc-grp-customer",codes:["R-SUP-01","R-SUP-02","R-LIMIT-01","R-CAT-01"]},{labelKey:"exc-grp-fields",codes:["amount_missing"]},{labelKey:"exc-chip-confidence_low",codes:["confidence_low"]}];function jd(e){if(!e)return"—";try{const n=new Date(e),a=s=>String(s).padStart(2,"0");return`${n.getFullYear()}-${a(n.getMonth()+1)}-${a(n.getDate())} ${a(n.getHours())}:${a(n.getMinutes())}`}catch{return e.slice(0,16).replace("T"," ")}}function ae(e,n,a){return`<div class="exc-why-detail-row"><b>${escapeHtml(t(e))}</b><span class="${a||""}">${escapeHtml(n)}</span></div>`}function Dd(e,n){const a=o=>rt(n[o]),s=o=>n[o]===null||n[o]===void 0?"—":String(n[o]);switch(e){case"risk.vat_mismatch":return ae("exc-fld-subtotal",a("net_amount"))+ae("exc-fld-vat",a("vat_amount"),"v-bad")+ae("exc-detail-expected",a("expected_vat"),"v-good");case"risk.total_mismatch":{const o=Number(n.net_amount)||0,i=Number(n.vat_amount)||0;return ae("exc-fld-subtotal",a("net_amount"))+ae("exc-fld-vat",a("vat_amount"))+ae("exc-fld-total",a("total_amount"),"v-bad")+ae("exc-detail-expected",rt(o+i),"v-good")}case"risk.line_sum_mismatch":return ae("exc-ev-lines-sum",a("lines_sum"),"v-bad")+ae("exc-fld-subtotal",a("net_amount"),"v-good");case"risk.line_amount_mismatch":{const o=Number(n.qty)||0,i=Number(n.unit_price)||0;return ae("exc-ev-amount",a("amount"),"v-bad")+ae("exc-detail-expected",rt(o*i),"v-good")}case"risk.multipage_mismatch":return ae("exc-ev-pages",s("pages"));case"risk.seller_tax_id_invalid":return ae("exc-fld-seller-tax",s("seller_tax_id"),"v-bad");case"risk.buyer_tax_id_invalid":return ae("exc-fld-buyer-tax",s("buyer_tax_id"),"v-bad");case"risk.tax_id_placeholder":return ae("exc-ev-value",s("value"),"v-bad");case"risk.invoice_date_unparseable":case"risk.invoice_date_future":return ae("exc-fld-date",s("invoice_date"),"v-bad");case"risk.invoice_date_out_of_period":return ae("exc-fld-date",s("invoice_date"),"v-bad")+ae("exc-ev-period-start",s("period_start"))+ae("exc-ev-period-end",s("period_end"));case"risk.duplicate_exact":return(n.invoice_no?ae("exc-fld-invoice-no",s("invoice_no")):"")+ae("exc-fld-seller-tax",s("seller_tax_id"));case"risk.duplicate_suspected":{const o=Array.isArray(n.candidate_history_ids)?n.candidate_history_ids.length:0;return ae("exc-ev-dup-count",String(o))}case"risk.supplier_not_allowlisted":return ae("exc-fld-seller",s("seller_name"))+ae("exc-fld-seller-tax",s("seller_tax_id"));case"risk.supplier_force_review":return ae("exc-ev-reason",s("reason"),"v-bad")+ae("exc-fld-seller-tax",s("seller_tax_id"));case"risk.amount_over_limit":return ae("exc-ev-amount",a("value"),"v-bad")+ae("exc-ev-limit",a("limit"),"v-good");case"risk.category_no_auto_push":return ae("exc-ev-category",s("category"));default:return`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(n))}</span></div>`}}function qd(e,n){if(n=n||{},n.message_key)return Dd(n.message_key,n.evidence||{});if(e==="math_mismatch")return`
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(rt(n.subtotal))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(rt(n.vat))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(rt(n.total_expected))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(rt(n.total_actual))}</span></div>
            <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(rt(n.diff))}</span></div>
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
        `:e==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(n))}</span></div>`}function ct(){const e=D.excRow;if(!e)return;const n=e.seller_name&&e.seller_name.trim()?e.seller_name:t("exc-no-seller"),a=e.filename||"—";document.getElementById("exc-drawer-title").textContent=a;const s="exc-status-"+(e.status||"pending"),o=t(s)||e.status,i="s-"+(e.status||"pending"),r=(e.invoice_date||e.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
        <span>${escapeHtml(n)}</span>
        ${e.invoice_no?`<span>· ${escapeHtml(e.invoice_no)}</span>`:""}
        ${r?`<span>· ${escapeHtml(r)}</span>`:""}
        <span class="exc-status-chip ${i}">${escapeHtml(o)}</span>
    `;const l=e.severity||"medium",m=Ts(e),d=qd(e.rule_code,e.detail||{}),p=yo(D.history),c=D.history===null,u=D.history&&D.history._err,v=new Set,f=e.rule_code||"";["math_mismatch","R-VAT-01","R-VAT-02","R-SUM-01","R-LINE-01"].includes(f)?(v.add("subtotal"),v.add("vat"),v.add("total_amount")):f==="R-MULTIPAGE-01"||f==="R-LIMIT-01"?v.add("total_amount"):f==="tax_id_format_invalid"||f==="R-TAXID-01"?v.add("seller_tax"):f==="R-TAXID-02"?v.add("buyer_tax"):f==="R-TAXID-03"?(v.add("seller_tax"),v.add("buyer_tax")):f==="R-DATE-01"||f==="R-DATE-02"?v.add("date"):f==="R-DUP-01"||f==="R-DUP-02"?v.add("invoice_number"):f==="R-SUP-01"||f==="R-SUP-02"?(v.add("seller_name"),v.add("seller_tax")):f==="amount_missing"&&(v.add("total_amount"),v.add("invoice_number"));const y=!!D.editing,b=D.editFields||{},h=(H,R,G)=>{if(c)return`<div class="exc-field-row"><label>${escapeHtml(t(R))}</label><span class="val empty">…</span></div>`;const se=y?b[H]!==void 0?b[H]:p[H]!==void 0&&p[H]!==null?p[H]:"":p[H],ce=v.has(H)?"flagged":"";if(y){const O=G?"number":"text",N=G?' step="0.01" inputmode="decimal"':"",Y=se==null?"":String(se).replace(/"/g,"&quot;");return`<div class="exc-field-row ${ce} editing">
                <label>${escapeHtml(t(R))}</label>
                <input class="exc-field-input" type="${O}"${N} data-edit-key="${escapeHtml(H)}" value="${Y}">
            </div>`}const _e=G?rt(se):se||"",we=se==null||se===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(_e)}</span>`;return`<div class="exc-field-row ${ce}"><label>${escapeHtml(t(R))}</label>${we}</div>`};let g="";u?g=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:g=`
            <div class="exc-fields">
                ${h("invoice_number","exc-fld-invoice-no",!1)}
                ${h("date","exc-fld-date",!1)}
                ${h("seller_name","exc-fld-seller",!1)}
                ${h("seller_tax","exc-fld-seller-tax",!1)}
                ${h("buyer_name","exc-fld-buyer",!1)}
                ${h("buyer_tax","exc-fld-buyer-tax",!1)}
                ${h("subtotal","exc-fld-subtotal",!0)}
                ${h("vat","exc-fld-vat",!0)}
                ${h("total_amount","exc-fld-total",!0)}
            </div>
        `;const _=(()=>{if(D.pdfStatus==="loading"||D.pdfStatus==="idle")return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                </div>
                <div class="exc-pdf-empty">
                    <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M18 4v8a14 14 0 1014 14"/>
                    </svg>
                    <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                </div>
            `;if(D.pdfStatus==="empty")return`
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
            `;if(D.pdfStatus==="error")return`
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
            `;const H=D.pdfUrl;return`
            <div class="exc-pdf-toolbar">
                <span class="exc-pdf-toolbar-title">${escapeHtml(a)}</span>
                <div class="exc-pdf-toolbar-actions">
                    <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${H}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M8 2h4v4M12 2L7 7"/>
                            <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                        </svg>
                    </a>
                    <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${H}" download="${escapeHtml(a)}" title="${escapeHtml(t("exc-pdf-download"))}">
                        <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                        </svg>
                    </a>
                </div>
            </div>
            <iframe class="exc-pdf-frame" src="${H}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
        `})();document.getElementById("exc-drawer-body").innerHTML=`
        <div class="exc-pdf-pane">${_}</div>
        <div class="exc-fields-pane">
            <div class="exc-section">
                <div class="exc-section-title">
                    <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="7" cy="7" r="5.5"/><line x1="7" y1="4" x2="7" y2="7.5"/>
                        <circle cx="7" cy="9.6" r="0.5" fill="currentColor"/>
                    </svg>
                    <span>${escapeHtml(t("exc-sect-why"))}</span>
                </div>
                <div class="exc-why sev-${escapeHtml(l)}">
                    <div class="exc-why-rule">${escapeHtml(m)}</div>
                    <div class="exc-why-detail">${d}</div>
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
                    ${e.status==="pending"&&!c&&!u?y?`
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
    `;const w=document.getElementById("exc-fld-edit");w&&w.addEventListener("click",()=>{D.editing=!0,D.editFields={...yo(D.history)},ct()});const k=document.getElementById("exc-fld-cancel");k&&k.addEventListener("click",()=>{D.editing=!1,D.editFields=null,ct()});const x=document.getElementById("exc-fld-save");x&&x.addEventListener("click",()=>zd()),document.querySelectorAll(".exc-field-input").forEach(H=>{H.addEventListener("input",()=>{D.editFields||(D.editFields={}),D.editFields[H.dataset.editKey]=H.value})});const I=document.getElementById("exc-pdf-retry");I&&D.openExcId&&I.addEventListener("click",()=>{D.excRow&&Gi(D.excRow.history_id,D.openExcId)});const B=e.status==="pending",L=!!(e.seller_name&&e.seller_name.trim()),$=document.getElementById("exc-btn-resolve"),S=document.getElementById("exc-btn-ignore");$.disabled=!B,S.disabled=!B||!L,S.title=L?t("exc-ignore-hint"):t("exc-ignore-no-seller")}function Hs(){if(D.pdfUrl){try{URL.revokeObjectURL(D.pdfUrl)}catch{}D.pdfUrl=null}D.pdfStatus="idle"}async function Gi(e,n){D.pdfStatus="loading",ct();try{const a=await fetch("/api/history/"+encodeURIComponent(e)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(D.openExcId!==n)return;if(a.status===404){D.pdfStatus="empty",ct();return}if(!a.ok)throw new Error("http "+a.status);const s=await a.blob();if(D.openExcId!==n)return;Hs(),D.pdfUrl=URL.createObjectURL(s),D.pdfStatus="ready",ct()}catch(a){if(D.openExcId!==n)return;console.warn("loadDrawerPdf fail",a),D.pdfStatus="error",ct()}}function Rd(e){const n=(q.listCache||[]).find(a=>a.id===e);if(!n){showToast(t("exc-drawer-error"),"error");return}q.listScrollY=window.scrollY||document.documentElement.scrollTop||0,Hs(),D.editing=!1,D.editFields=null,D.openExcId=e,D.excRow=n,D.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),ct(),Fd(n.history_id),Gi(n.history_id,e)}function Yt(){Hs(),D.editing=!1,D.editFields=null,D.openExcId=null,D.excRow=null,D.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const e=q.listScrollY||0;e>0&&requestAnimationFrame(()=>window.scrollTo(0,e))}async function Fd(e){try{const n=await fetch("/api/history/"+encodeURIComponent(e),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);D.history=await n.json()}catch(n){console.warn("loadHistoryDetail fail",n),D.history={_err:!0}}D.excRow&&ct()}function yo(e){if(!e||!e.pages)return{};const n=e.pages,a=n.find(s=>!s.is_duplicate&&!s.is_copy)||n[0];return a&&a.fields||{}}async function zd(){if(!D.openExcId||!D.history||!D.history.pages||D.loading)return;D.loading=!0;const e=showToast(t("exc-fld-saving"),"loading",0);try{const n=JSON.parse(JSON.stringify(D.history.pages||[]));let a=n.findIndex(m=>!m.is_duplicate&&!m.is_copy);a<0&&(a=0),n[a]||(n[a]={fields:{}});const s=n[a].fields||{},o=D.editFields||{},i=new Set(["subtotal","vat","total_amount"]),r={...s};for(const m in o){let d=o[m];if((d===""||d===void 0)&&(d=null),i.has(m)&&d!==null){const p=parseFloat(d);d=isNaN(p)?null:p}r[m]=d}n[a].fields=r;const l=await fetch("/api/history/"+encodeURIComponent(D.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:n})});if(!l.ok)throw new Error("http "+l.status);e(),showToast(t("exc-fld-save-ok"),"success"),Yt(),await tn(),await xt(),at()}catch(n){e(),console.warn("save fields fail",n),showToast(t("exc-fld-save-fail"),"error")}finally{D.loading=!1}}async function Nd(){if(!(!D.openExcId||D.loading)){D.loading=!0;try{const e=await fetch("/api/exceptions/"+D.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-resolved"),"success"),Yt(),await tn(),await xt(),at()}catch(e){console.warn("resolve fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{D.loading=!1}}}async function Od(){if(!(!D.openExcId||D.loading)){D.loading=!0;try{const e=await fetch("/api/exceptions/"+D.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!e.ok)throw new Error("http "+e.status);showToast(t("exc-toast-ignored"),"success"),Yt(),await tn(),await xt(),at()}catch(e){console.warn("ignore fail",e),showToast(t("exc-toast-action-fail"),"error")}finally{D.loading=!1}}}async function at(){try{const e=q.currentClient||"",n="/api/exceptions/stats?status=pending"+(e?"&client_id="+encodeURIComponent(e):""),a=await fetch(n,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!a.ok)return;const s=await a.json(),o=document.getElementById("nav-exc-badge");if(!o)return;const i=parseInt(s.pending||0,10);i>0?(o.textContent=i>99?"99+":String(i),o.style.display=""):o.style.display="none"}catch{}}function Wi(e){document.getElementById("exc-kpi-pending").textContent=e.pending||0,document.getElementById("exc-kpi-high").textContent=e.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=e.resolved||0,document.getElementById("exc-kpi-learned").textContent=e.learned_rules||0;const n=document.getElementById("exc-status-tab-count-pending"),a=document.getElementById("exc-status-tab-count-resolved"),s=document.getElementById("exc-status-tab-count-ignored");n&&(n.textContent=e.pending||0),a&&(a.textContent=e.resolved||0),s&&(s.textContent=e.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(i=>{i.classList.toggle("active",i.dataset.status===(q.currentStatus||"pending"))})}function Ki(e,n){return n.split(",").reduce((a,s)=>a+(e[s]||0),0)}function Ms(e){const n=document.getElementById("exc-chips");if(!n)return;const a=e.by_rule||{};let o=`<button class="exc-chip ${!q.currentRule?"active":""}" data-rule="">
        <span>${escapeHtml(t("exc-chip-all"))}</span>
        <span class="exc-chip-count">${e.pending||0}</span>
    </button>`;for(const i of Pd){const r=i.codes.join(","),l=Ki(a,r),m=q.currentRule===r;l===0&&!m||(o+=`<button class="exc-chip ${m?"active":""}" data-rule="${escapeHtml(r)}">
            <span>${escapeHtml(t(i.labelKey))}</span>
            <span class="exc-chip-count">${l}</span>
        </button>`)}n.innerHTML=o,n.querySelectorAll(".exc-chip").forEach(i=>{i.addEventListener("click",()=>{const r=i.dataset.rule||null;q.currentRule=r,xt()})})}function As(e){const n=document.getElementById("exc-list");if(!n)return;if(!e||e.length===0){n.innerHTML=`<div class="exc-empty">
            ${Td()}
            <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
            <div>${escapeHtml(t("exc-empty-desc"))}</div>
        </div>`,ko();return}const a='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',s=(q.currentStatus||"pending")==="pending";n.innerHTML=e.map(o=>{const i=o.severity||"medium",r=Ts(o),l=o.seller_name&&o.seller_name.trim()?o.seller_name:t("exc-no-seller"),m=o.filename||"—",d=Md(o.invoice_date||o.created_at),p=o.status==="pending",c=q.selectedIds.has(o.id),u=s&&p;return`
            <div class="exc-row sev-${escapeHtml(i)} ${c?"selected":""}" data-exc-id="${escapeHtml(String(o.id))}">
                <div class="exc-row-check ${c?"checked":""}" data-check-id="${escapeHtml(String(o.id))}" ${u?"":'style="visibility:hidden;"'}>${a}</div>
                <div class="exc-row-sev">${Cd(i)}</div>
                <div class="exc-row-main">
                    <div class="exc-row-title">${escapeHtml(l)} · ${escapeHtml(m)}</div>
                    <div class="exc-row-meta">
                        ${o.invoice_no?`<span><b>${escapeHtml(o.invoice_no)}</b></span>`:""}
                        <span>${escapeHtml(d)}</span>
                    </div>
                </div>
                <div class="exc-row-rule r-${escapeHtml(i)}">${escapeHtml(r)}</div>
                <div class="exc-row-amount">${escapeHtml(Hd(o.total_amount))}</div>
            </div>
        `}).join(""),n.querySelectorAll(".exc-row").forEach(o=>{o.addEventListener("click",i=>{if(i.target.closest(".exc-row-check"))return;const r=o.dataset.excId;r&&Rd(parseInt(r,10))})}),n.querySelectorAll(".exc-row-check").forEach(o=>{o.addEventListener("click",i=>{i.stopPropagation();const r=parseInt(o.dataset.checkId,10);r&&(q.selectedIds.has(r)?(q.selectedIds.delete(r),o.classList.remove("checked"),o.closest(".exc-row").classList.remove("selected")):(q.selectedIds.add(r),o.classList.add("checked"),o.closest(".exc-row").classList.add("selected")),wo())})}),wo(),ko()}function wo(){const e=document.getElementById("exc-batch-bar"),n=document.getElementById("exc-batch-count");if(!e||!n)return;const a=q.selectedIds.size;a===0?e.style.display="none":(e.style.display="",n.textContent=bt("exc-batch-count",{n:a}))}function ko(){const e=document.getElementById("exc-list-foot"),n=document.getElementById("exc-list-count"),a=document.getElementById("exc-loadmore");if(!e||!n||!a)return;const s=q.listCache.length;if(s===0){e.style.display="none";return}e.style.display="";let o=s;const i=q.statsCache;i&&(q.currentRule?o=Ki(i.by_rule||{},q.currentRule)||s:o=i.pending||s),q.total=o,n.textContent=bt("exc-list-count",{shown:s,total:o});const r=s<o&&s<500;a.style.display=r?"":"none"}async function tn(){try{if(navigator.onLine===!1)throw new Error("offline");const e=q.currentClient||"",n=q.currentStatus||"pending",a=new URLSearchParams;a.set("status",n),e&&a.set("client_id",e);const s="/api/exceptions/stats?"+a.toString(),o=await fetch(s,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!o.ok)throw new Error("http "+o.status);const i=await o.json();return q.statsCache=i,Wi(i),Ms(i),i}catch(e){return console.warn("loadExceptionsStats fail",e),null}}function Vd(e){const n=document.getElementById("exc-list");if(!n)return;const a=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="18" cy="18" r="14"/>
        <line x1="18" y1="11" x2="18" y2="19"/>
        <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
    </svg>`,s=e?t("exc-offline"):t("exc-error-retry-title"),o=e?"":t("exc-error-retry-desc");n.innerHTML=`
        <div class="exc-error">
            ${a}
            <div class="exc-error-msg">${escapeHtml(s)}${o?" · "+escapeHtml(o):""}</div>
            <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
        </div>`;const i=document.getElementById("exc-retry-btn");i&&i.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function xt(e){e=e||{};const n=!!e.append,a=document.getElementById("exc-list");!n&&a&&q.listCache.length===0&&(a.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const s=new URLSearchParams;s.set("status",q.currentStatus||"pending"),q.currentRule&&s.set("rule_code",q.currentRule),q.currentClient&&s.set("client_id",q.currentClient);const o=n?q.listCache.length:0;s.set("limit",String(q.pageSize)),s.set("offset",String(o));try{if(navigator.onLine===!1)throw new Error("offline");const i=await fetch("/api/exceptions/list?"+s.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!i.ok)throw new Error("http "+i.status);const l=(await i.json()).items||[];n?q.listCache=q.listCache.concat(l):(q.listCache=l,q.selectedIds.clear()),q.loadFailed=!1,As(q.listCache),q.statsCache&&Ms(q.statsCache)}catch(i){console.warn("loadExceptionsList fail",i),q.loadFailed=!0;const r=navigator.onLine===!1||String(i.message||"").includes("offline");n?showToast(t("exc-toast-load-fail"),"error"):(Vd(r),showToast(r?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function Ud(){if(!q.loading&&!(q.listCache.length>=500)){q.loading=!0;try{await xt({append:!0})}finally{q.loading=!1}}}function Ps(){const e=document.getElementById("exc-client-filter");if(!e)return;const n=window._clientsCache||[],a=q.currentClient||"",s=typeof t=="function"?t("history-client-all"):"全部客户";e.innerHTML=`<option value="">${escapeHtml(s)}</option>`+n.map(o=>`<option value="${o.id}">${escapeHtml(o.name)}</option>`).join(""),e.value=a}async function Gd(){if(Nt.batchLoading)return;const e=Array.from(q.selectedIds);if(e.length===0||!await showConfirm(bt("exc-batch-confirm-resolve",{n:e.length})))return;Nt.batchLoading=!0;const a=showToast(bt("exc-batch-count",{n:e.length})+" …","loading",0);try{const s=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"resolve"})});if(!s.ok)throw new Error("http "+s.status);const o=await s.json();a(),showToast(bt("exc-toast-batch-resolved",{n:o.processed||0}),"success"),q.selectedIds.clear(),await tn(),await xt(),at()}catch(s){a(),console.warn("batch resolve fail",s),showToast(t("exc-toast-batch-fail"),"error")}finally{Nt.batchLoading=!1}}async function Wd(){if(Nt.batchLoading)return;const e=Array.from(q.selectedIds);if(e.length===0||!await showConfirm(bt("exc-batch-confirm-ignore",{n:e.length}),{danger:!1}))return;Nt.batchLoading=!0;const a=showToast(bt("exc-batch-count",{n:e.length})+" …","loading",0);try{const s=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:e,action:"ignore"})});if(!s.ok)throw new Error("http "+s.status);const o=await s.json();a(),showToast(bt("exc-toast-batch-ignored",{n:o.processed||0,wl:o.whitelist_added||0}),"success"),q.selectedIds.clear(),await tn(),await xt(),at()}catch(s){a(),console.warn("batch ignore fail",s),showToast(t("exc-toast-batch-fail"),"error")}finally{Nt.batchLoading=!1}}function Kd(){q.selectedIds.clear(),As(q.listCache)}async function Yi(){const e=document.getElementById("learned-list");if(e){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const n=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!n.ok)throw new Error("http "+n.status);const s=(await n.json()).items||[];if(s.length===0){e.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const o=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
        </svg>`;e.innerHTML=s.map(i=>{const r=Ts(i);return`
                <div class="learned-row" data-wl-id="${escapeHtml(String(i.id))}">
                    <div class="learned-seller" title="${escapeHtml(i.seller_name)}">${escapeHtml(i.seller_name)}</div>
                    <div class="learned-rule">${escapeHtml(r)}</div>
                    <div class="learned-date">${escapeHtml(jd(i.created_at))}</div>
                    <button class="learned-del-btn" data-del-wl="${escapeHtml(String(i.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${o}</button>
                </div>
            `}).join("")}catch(n){console.warn("loadLearnedRules fail",n),e.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadExceptionsPage=async function(){if(!q.loading){q.loading=!0;try{Ps(),await tn(),await xt()}finally{q.loading=!1}}};window.refreshExcBadge=at;window._refreshExcClientFilter=Ps;window._excState=q;window._rerenderExceptions=function(){try{Ps()}catch{}q.statsCache&&(Wi(q.statsCache),Ms(q.statsCache)),q.listCache&&q.listCache.length&&As(q.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}D.openExcId&&ct()};document.addEventListener("click",e=>{e.target.closest("#exc-drawer-close")&&Yt(),e.target.closest("#exc-drawer-mask")&&Yt(),e.target.closest("#exc-btn-resolve")&&Nd(),e.target.closest("#exc-btn-ignore")&&Od(),e.target.closest("#exc-batch-resolve")&&Gd(),e.target.closest("#exc-batch-ignore")&&Wd(),e.target.closest("#exc-batch-clear")&&Kd(),e.target.closest("#exc-loadmore")&&Ud()});document.addEventListener("keydown",e=>{e.key==="Escape"&&D.openExcId&&Yt()});document.addEventListener("click",e=>{e.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),at())});document.addEventListener("change",e=>{if(!e.target.closest("#exc-client-filter"))return;const n=e.target;q.currentClient=n.value||"",q.currentRule=null,q.selectedIds.clear(),q.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),at()});document.addEventListener("click",e=>{const n=e.target.closest("#exc-status-tabs .exc-status-tab");if(!n)return;const a=n.dataset.status||"pending";a!==q.currentStatus&&(q.currentStatus=a,q.currentRule=null,q.selectedIds.clear(),q.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())});window.addEventListener("online",()=>{q.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()});setTimeout(at,1500);setInterval(at,6e4);window.loadLearnedRules=Yi;document.addEventListener("click",async e=>{const n=e.target.closest("[data-del-wl]");if(!n)return;const a=parseInt(n.dataset.delWl,10);if(!a)return;const s=n.closest(".learned-row"),o=s&&s.querySelector(".learned-seller"),i=o?o.textContent.trim():"",r=t("set-learned-del-confirm").replace("{seller}",i);if(await showConfirm(r,{danger:!0}))try{const m=await fetch("/api/exception-whitelist/"+a,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!m.ok)throw new Error("http "+m.status);showToast(t("set-learned-del-ok"),"success"),Yi(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(m){console.warn("delete whitelist fail",m),showToast(t("set-learned-del-fail"),"error")}});let le={items:[],q:"",cat:"",adapter:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},xo=null;function Qe(){return localStorage.getItem("mrpilot_token")||""}function _o(e){return/<!?\s*doctype|<html|<\/?[a-z]+>|\bTraceback\b|^\s*ERR_[A-Z]/i.test(e)||e.length>200}function Ji(e){const n=typeof currentLang=="string"&&currentLang||window._currentLang||"th",a=e.error_friendly&&e.error_friendly[n];if(a)return a;if(typeof humanizeError=="function"&&e.error_msg&&!_o(e.error_msg))try{const s=humanizeError(e.error_msg);if(s&&!_o(s))return s}catch{}return t("erp-exc-reason-"+(e.category||"other"))}function Eo(){const e=document.getElementById("erp-exc-batch");if(!e)return;const n=le.selected.size;e.hidden=n===0;const a=e.querySelector(".erp-exc-batch-count");a&&(a.textContent=String(n))}function js(){const e=document.getElementById("erp-exc-block");if(!e)return;const n=le;if(!(n.total>0||!!n.q||!!n.cat)){e.hidden=!0,e.innerHTML="";return}e.hidden=!1;const s=n.categories||{},o=Object.keys(s).reduce((x,E)=>x+s[E],0);let i=`<button class="erp-exc-chip ${n.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${o}</span></button>`;Object.keys(s).forEach(x=>{i+=`<button class="erp-exc-chip ${n.cat===x?"active":""}" data-erpexc-cat="${escapeHtml(x)}"><span>${escapeHtml(t("erp-exc-cat-"+x))}</span><span class="erp-exc-chip-count">${s[x]}</span></button>`});const r=n.items||[],l=r.length>0&&r.every(x=>n.selected.has(x.id)),m=r.map(x=>{const E=x.state==="needs_action"?"needs":x.state==="retrying"?"retry":"fail",I=t("erp-exc-state-"+(x.state||"failed")),B=Ji(x),L=n.selected.has(x.id)?"checked":"",$=x.push_type==="id_card",S=$?`<span class="erp-exc-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span> `:"",H=$?`<span class="ex-inv" title="${escapeHtml(t("erp-log-col-booking"))}">${S}${escapeHtml(x.invoice_no||"—")}</span>`:`<span class="ex-inv" title="${escapeHtml(x.invoice_no||"")}">${escapeHtml(x.invoice_no||"—")}</span>`,R=$?`<span class="ex-seller" title="${escapeHtml(t("erp-log-col-customer"))}">${escapeHtml(x.seller_name||"—")}</span>`:`<span class="ex-seller" title="${escapeHtml(x.seller_name||"")}">${escapeHtml(x.seller_name||"—")}</span>`,G=$?`<span class="ex-buyer" title="${escapeHtml(t("erp-log-col-idcard"))}">${x.id_card_tail?"••••"+escapeHtml(x.id_card_tail):"—"}</span>`:`<span class="ex-buyer" title="${escapeHtml(x.ocr_buyer_name||"")}">${escapeHtml(x.ocr_buyer_name||"—")}</span>`;return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(x.id)}">
            <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(x.id)}" ${L}></span>
            ${H}
            ${R}
            ${G}
            <span class="ex-state"><span class="erp-exc-state ${E}">${escapeHtml(I)}</span></span>
            <span class="ex-reason" title="${escapeHtml(B)}${x.error_code?" ("+escapeHtml(x.error_code)+")":""}">${escapeHtml(B)}</span>
            <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(x.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
        </div>`}).join(""),d=r.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",p=r.length<n.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${r.length}/${n.total})</button>`:n.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:r.length,total:n.total}))}</div>`:"",c=n.adapter==="mrerp_dms",u=Array.isArray(window._erpEndpoints)?window._erpEndpoints:[],v=new Set;let f=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`;u.forEach(x=>{const E=(x&&x.adapter||"").toLowerCase();!E||v.has(E)||(v.add(E),f+=`<option value="${escapeHtml(E)}"${E===n.adapter?" selected":""}>${escapeHtml(x&&x.name||E)}</option>`)});const y=c?t("erp-log-col-booking"):t("erp-exc-f-invoice"),b=c?t("erp-log-col-customer"):t("erp-exc-f-seller"),h=c?t("erp-log-col-idcard"):t("erp-exc-f-buyer");e.innerHTML=`
        <div class="erp-exc-head">
            <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
            <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
            <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${f}</select>
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
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${l?"checked":""}></span>
                <span class="ex-inv">${escapeHtml(y)}</span>
                <span class="ex-seller">${escapeHtml(b)}</span>
                <span class="ex-buyer">${escapeHtml(h)}</span>
                <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                <span class="ex-act"></span>
            </div>
            ${m}${d}
        </div>
        <div class="erp-exc-foot">${p}</div>`;const g=document.getElementById("erp-exc-search");if(g){if(n.focusSearch){g.focus();try{g.setSelectionRange(n.searchCaret,n.searchCaret)}catch{}}g.addEventListener("input",()=>{n.q=g.value,n.focusSearch=!0,n.searchCaret=g.selectionStart||g.value.length,clearTimeout(xo),xo=setTimeout(()=>Tt(!1),350)}),g.addEventListener("blur",()=>{n.focusSearch=!1})}e.querySelectorAll(".erp-exc-chip").forEach(x=>{x.addEventListener("click",()=>{n.cat=x.dataset.erpexcCat||"",Tt(!1)})});const _=document.getElementById("erp-exc-erp-select");_&&_.addEventListener("change",()=>{n.adapter=_.value||"",Tt(!1)}),e.querySelectorAll("[data-erpexc-retry]").forEach(x=>{x.addEventListener("click",E=>{E.stopPropagation(),On(x.dataset.erpexcRetry,x)})}),e.querySelectorAll(".erp-exc-cb").forEach(x=>{x.addEventListener("change",()=>{const E=x.dataset.erpexcCb;x.checked?n.selected.add(E):n.selected.delete(E);const I=document.getElementById("erp-exc-cb-all");I&&(I.checked=r.length>0&&r.every(B=>n.selected.has(B.id))),Eo()})});const w=document.getElementById("erp-exc-cb-all");w&&w.addEventListener("change",()=>{r.forEach(x=>{w.checked?n.selected.add(x.id):n.selected.delete(x.id)}),e.querySelectorAll(".erp-exc-cb").forEach(x=>{x.checked=w.checked}),Eo()}),e.querySelectorAll("[data-erpexc-batch]").forEach(x=>{x.addEventListener("click",()=>Yd(x.dataset.erpexcBatch))});const k=document.getElementById("erp-exc-more");k&&k.addEventListener("click",()=>Tt(!0)),e.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(x=>{x.addEventListener("click",E=>{E.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(x.dataset.erpexcId)})})}async function On(e,n){if(e){n&&(n.disabled=!0,n.textContent=t("erp-exc-retrying"));try{const a=await fetch("/api/erp/logs/"+encodeURIComponent(e)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+Qe()}}),s=await a.json().catch(()=>({}));showToast(a.ok&&s.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),a.ok&&s.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(le.selected.delete(e),Tt(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function Yd(e){const n=Array.from(le.selected);if(e==="clear"){le.selected.clear(),js();return}if(n.length!==0){if(e==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:n.length}),{danger:!0}))return;try{const s=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+Qe(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:n.slice(0,200)})}),o=await s.json().catch(()=>({}));showToast(s.ok?t("erp-exc-batch-delete-ok",{n:o.deleted||0}):t("erp-exc-retry-fail"),s.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(e==="retry")try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+Qe(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:n.slice(0,50)})}),s=await a.json().catch(()=>({}));showToast(a.ok?t("erp-exc-batch-retry-ok",{ok:s.succeeded||0,fail:(s.failed||0)+(s.skipped||0)}):t("erp-exc-retry-fail"),a.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(le.selected.clear(),Tt(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function Tt(e){const n=document.getElementById("erp-exc-block");if(!(!n||le.loading)){le.loading=!0;try{if(!Array.isArray(window._erpEndpoints)||!window._erpEndpoints.length)try{const r=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+Qe()}});if(r.ok){const l=await r.json();window._erpEndpoints=l&&(l.items||l)||[]}}catch{}const a=new URLSearchParams;le.q&&a.set("q",le.q),le.cat&&a.set("category",le.cat),le.adapter&&a.set("adapter",le.adapter),a.set("limit",String(le.pageSize)),a.set("offset",String(e?le.items.length:0));const s=await fetch("/api/erp/exceptions?"+a.toString(),{headers:{Authorization:"Bearer "+Qe()}});if(!s.ok){e||(n.hidden=!0);return}const o=await s.json(),i=o.items||[];le.items=e?le.items.concat(i):i,le.total=o.total||0,le.categories=o.categories||{},js()}catch{e||(n.hidden=!0)}finally{le.loading=!1}}}window._rerenderErpExceptions=js;window.loadErpExceptions=Tt;window._erpExcState=le;let An={};function Dt(){const e=document.getElementById("erp-exc-modal");e&&e.remove()}window._erpExcOpenEdit=function(e){const n=(le.items||[]).find(p=>String(p.id)===String(e));if(!n)return;const a=n.push_type==="id_card",s=!!n.history_client_id&&n.category==="customer_mismatch",o=n.category==="product_mismatch"&&!!n.history_id&&!!n.endpoint_id,i=Ji(n),r=n.state==="needs_action"?"needs":n.state==="retrying"?"retry":"fail",l=(p,c)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(p)}</span><span class="erp-exc-m-v">${escapeHtml(c||"—")}</span></div>`;let m="";if(s)m=`
            <div class="erp-exc-m-fix">
                <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                    <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                </div>
            </div>`;else if(o)m=`
            <div class="erp-exc-m-fix">
                <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                    <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                </div>
            </div>`;else{const p="erp-exc-edit-hint-"+(n.category||"other");let c=t(p);(!c||c===p)&&(c=i),m=`<div class="erp-exc-m-hint">${escapeHtml(c)}</div>`}const d=document.createElement("div");if(d.id="erp-exc-modal",d.className="erp-exc-modal-overlay",d.innerHTML=`
        <div class="erp-exc-modal" role="dialog" aria-modal="true">
            <div class="erp-exc-m-head">
                <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
            </div>
            <div class="erp-exc-m-body">
                <div class="erp-exc-m-reason"><span class="erp-exc-state ${r}">${escapeHtml(t("erp-exc-state-"+(n.state||"failed")))}</span> ${escapeHtml(i)}${n.error_code&&!a?` <span class="erp-exc-code">${escapeHtml(n.error_code)}</span>`:""}</div>
                ${l(a?t("erp-log-col-booking"):t("erp-exc-f-invoice"),n.invoice_no)}
                ${l(a?t("erp-log-col-customer"):t("erp-exc-f-seller"),n.seller_name)}
                ${a?l(t("erp-log-col-idcard"),n.id_card_tail?"••••"+n.id_card_tail:"—"):l(t("erp-exc-f-buyer"),n.ocr_buyer_name)+l(t("erp-exc-edit-field-current"),n.client_name)}
                ${m}
            </div>
            <div class="erp-exc-m-foot">
                <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                ${s?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                ${o?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
            </div>
        </div>`,document.body.appendChild(d),d.addEventListener("click",p=>{p.target===d&&Dt()}),document.getElementById("erp-exc-m-close").addEventListener("click",Dt),document.getElementById("erp-exc-m-cancel").addEventListener("click",Dt),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{Dt(),On(n.id,null)}),s){let p="";const c=document.getElementById("erp-exc-m-bind"),u=document.getElementById("erp-exc-m-custlist"),v=document.getElementById("erp-exc-m-search"),f=(b,h)=>{const g=(h||"").trim().toLowerCase(),_=g?b.filter(w=>(w.code||"").toLowerCase().includes(g)||(w.name||"").toLowerCase().includes(g)):b;if(_.length===0){u.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}u.innerHTML=_.slice(0,100).map(w=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(w.code||"")}">
                    <span class="erp-exc-m-cust-name">${escapeHtml(w.name||"")}</span>
                    <span class="erp-exc-m-cust-code">${escapeHtml(w.code||"")}</span>
                </div>`).join(""),u.querySelectorAll(".erp-exc-m-cust").forEach(w=>{w.addEventListener("click",()=>{p=w.dataset.custCode||"",u.querySelectorAll(".erp-exc-m-cust").forEach(k=>k.classList.remove("sel")),w.classList.add("sel"),c&&(c.disabled=!p)})})},y=async()=>{const b=n.endpoint_id;if(An[b]){f(An[b],"");return}try{const h=await fetch("/api/erp/endpoints/"+encodeURIComponent(b)+"/customers",{headers:{Authorization:"Bearer "+Qe()}}),g=await h.json().catch(()=>({}));if(!h.ok||!g.ok){u.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const _=g.customers||[];An[b]=_,f(_,"")}catch{u.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};v&&v.addEventListener("input",()=>f(An[n.endpoint_id]||[],v.value)),y(),c&&c.addEventListener("click",async()=>{if(p){c.disabled=!0,c.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+Qe(),"Content-Type":"application/json"},body:JSON.stringify({client_id:n.history_client_id,erp_type:n.endpoint_adapter,erp_code:p})})).ok){showToast(t("erp-exc-retry-fail"),"error"),c.disabled=!1,c.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),Dt(),await On(n.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),c.disabled=!1,c.textContent=t("erp-exc-edit-bind-retry")}}})}if(o){const p=document.getElementById("erp-exc-m-bind-prod"),c=document.getElementById("erp-exc-m-prodlist"),u={};let v=[];const f=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+v.slice(0,500).map(h=>`<option value="${escapeHtml(h.code||"")}" data-pname="${escapeHtml(h.name||"")}">`+escapeHtml((h.name||"")+" · "+(h.code||""))+"</option>").join(""),y=h=>{if(!h.length){c.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}c.innerHTML=h.map(g=>`<div class="erp-exc-m-cust" style="cursor:default">
                    <span class="erp-exc-m-cust-name" title="${escapeHtml(g)}">${escapeHtml(g)}</span>
                    <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(g)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${f()}</select>
                </div>`).join(""),c.querySelectorAll(".erp-exc-m-prod-sel").forEach(g=>{g.addEventListener("change",()=>{const _=g.dataset.item,w=g.options[g.selectedIndex];g.value?u[_]={code:g.value,name:w&&w.dataset.pname||""}:delete u[_],p&&(p.disabled=Object.keys(u).length===0)})})};(async()=>{try{const g=await(await fetch("/api/history/"+encodeURIComponent(n.history_id),{headers:{Authorization:"Bearer "+Qe()}})).json().catch(()=>({})),_=g&&g.pages||[],w=[],k={};(Array.isArray(_)?_:[]).forEach(I=>{const B=I&&I.fields&&I.fields.items||[];(Array.isArray(B)?B:[]).forEach(L=>{const $=(L&&(L.name||L.description)||"").trim();$&&!k[$]&&(k[$]=1,w.push($))})});const x=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+Qe()}}),E=await x.json().catch(()=>({}));if(!x.ok||!E.ok){c.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}v=E.products||[],y(w)}catch{c.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),p&&p.addEventListener("click",async()=>{const h=Object.entries(u);if(h.length){p.disabled=!0,p.textContent=t("erp-exc-retrying");try{for(const[g,_]of h)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+Qe(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:n.endpoint_adapter,item_name:g,erp_code:_.code,erp_name:_.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),p.disabled=!1,p.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),Dt(),await On(n.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),p.disabled=!1,p.textContent=t("erp-exc-edit-bind-prod-retry")}}})}};const Io={zh:{title:"风险检查规矩",btn:"规矩设置",lead:"基础检查(VAT 算术、税号、重复票、日期)默认开着,不用配。下面这些规矩对所有客户生效。",gSupplier:"供应商规矩",gSupplierDesc:"哪些供应商要特别留意",gAmount:"金额上限",gAmountDesc:"单张票超过多少就提醒",gPeriod:"会计账期",gPeriodDesc:"票据日期得落在记账周期内",gCategory:"不自动推送的类别",gCategoryDesc:"某类发票必须人工确认",add:"添加",done:"完成",empty:"还没设置",sevHigh:"高",sevMid:"中",sevLow:"低",alsoLine:"也推 LINE",addTitle:"添加一条规矩",editTitle:"修改规矩",rType:"规矩类型",tForce:"供应商必审",tForceDesc:"指定供应商人工复核",tAmount:"金额上限",tAmountDesc:"超过就提醒",tPeriod:"会计账期",tPeriodDesc:"日期超期提醒",tCategory:"不自动推送",tCategoryDesc:"某类人工确认",fSupplierTax:"供应商税号",fAmountLimit:"金额上限(฿)",fCategory:"类别名称",fSeverity:"严重程度",fAlsoLine:"同时推 LINE 给老板",fPeriodMode:"账期范围",pmCurrent:"本月",pmPrev:"上月",anyInvoice:"任意发票",cancel:"取消",save:"保存",saved:"已保存",deleted:"已删除",delConfirm:"确定删除这条规矩?",loadFail:"加载失败",saveFail:"保存失败",enabled:"已启用 · 即时生效",disabled:"已停用",needSupplier:"请填供应商税号",needAmount:"请填一个有效金额",needCategory:"请填类别名称"},en:{title:"Risk-check rules",btn:"Rules",lead:"Base checks (VAT math, tax id, duplicates, dates) are always on. The rules below apply to every client.",gSupplier:"Supplier rules",gSupplierDesc:"Suppliers that need a closer look",gAmount:"Amount limits",gAmountDesc:"Flag an invoice over this amount",gPeriod:"Accounting period",gPeriodDesc:"Invoice date must fall in the period",gCategory:"Categories not auto-pushed",gCategoryDesc:"These categories need manual sign-off",add:"Add",done:"Done",empty:"Nothing set yet",sevHigh:"High",sevMid:"Medium",sevLow:"Low",alsoLine:"LINE too",addTitle:"Add a rule",editTitle:"Edit rule",rType:"Rule type",tForce:"Force review",tForceDesc:"Manual review for a supplier",tAmount:"Amount limit",tAmountDesc:"Flag when over",tPeriod:"Accounting period",tPeriodDesc:"Flag out-of-period dates",tCategory:"No auto-push",tCategoryDesc:"Manual sign-off",fSupplierTax:"Supplier tax id",fAmountLimit:"Amount limit (฿)",fCategory:"Category name",fSeverity:"Severity",fAlsoLine:"Also push LINE to the boss",fPeriodMode:"Period range",pmCurrent:"This month",pmPrev:"Last month",anyInvoice:"Any invoice",cancel:"Cancel",save:"Save",saved:"Saved",deleted:"Deleted",delConfirm:"Delete this rule?",loadFail:"Failed to load",saveFail:"Failed to save",enabled:"Enabled · effective now",disabled:"Disabled",needSupplier:"Enter the supplier tax id",needAmount:"Enter a valid amount",needCategory:"Enter a category name"},th:{title:"กฎตรวจความเสี่ยง",btn:"กฎ",lead:"การตรวจพื้นฐาน (VAT, เลขผู้เสียภาษี, ใบซ้ำ, วันที่) เปิดอยู่เสมอ กฎด้านล่างมีผลกับทุกลูกค้า",gSupplier:"กฎผู้ขาย",gSupplierDesc:"ผู้ขายที่ต้องดูให้ละเอียด",gAmount:"วงเงินสูงสุด",gAmountDesc:"แจ้งเตือนเมื่อใบเกินจำนวนนี้",gPeriod:"งวดบัญชี",gPeriodDesc:"วันที่ในใบต้องอยู่ในงวด",gCategory:"หมวดที่ไม่ส่งอัตโนมัติ",gCategoryDesc:"หมวดเหล่านี้ต้องยืนยันด้วยมือ",add:"เพิ่ม",done:"เสร็จ",empty:"ยังไม่ได้ตั้งค่า",sevHigh:"สูง",sevMid:"กลาง",sevLow:"ต่ำ",alsoLine:"ส่ง LINE ด้วย",addTitle:"เพิ่มกฎ",editTitle:"แก้ไขกฎ",rType:"ประเภทกฎ",tForce:"บังคับตรวจ",tForceDesc:"ตรวจด้วยมือสำหรับผู้ขาย",tAmount:"วงเงินสูงสุด",tAmountDesc:"แจ้งเมื่อเกิน",tPeriod:"งวดบัญชี",tPeriodDesc:"แจ้งวันที่นอกงวด",tCategory:"ไม่ส่งอัตโนมัติ",tCategoryDesc:"ยืนยันด้วยมือ",fSupplierTax:"เลขผู้เสียภาษีผู้ขาย",fAmountLimit:"วงเงินสูงสุด (฿)",fCategory:"ชื่อหมวด",fSeverity:"ความรุนแรง",fAlsoLine:"ส่ง LINE ถึงเจ้านายด้วย",fPeriodMode:"ช่วงงวด",pmCurrent:"เดือนนี้",pmPrev:"เดือนที่แล้ว",anyInvoice:"ใบแจ้งหนี้ใดก็ได้",cancel:"ยกเลิก",save:"บันทึก",saved:"บันทึกแล้ว",deleted:"ลบแล้ว",delConfirm:"ลบกฎนี้?",loadFail:"โหลดไม่สำเร็จ",saveFail:"บันทึกไม่สำเร็จ",enabled:"เปิดใช้แล้ว · มีผลทันที",disabled:"ปิดใช้แล้ว",needSupplier:"กรอกเลขผู้เสียภาษีผู้ขาย",needAmount:"กรอกจำนวนเงินที่ถูกต้อง",needCategory:"กรอกชื่อหมวด"},ja:{title:"リスクチェックのルール",btn:"ルール",lead:"基本チェック(VAT計算・税番号・重複・日付)は常に有効です。以下のルールは全クライアントに適用されます。",gSupplier:"取引先ルール",gSupplierDesc:"注意が必要な取引先",gAmount:"金額上限",gAmountDesc:"この金額を超えたら通知",gPeriod:"会計期間",gPeriodDesc:"請求日が期間内である必要",gCategory:"自動送信しないカテゴリ",gCategoryDesc:"これらは手動確認が必要",add:"追加",done:"完了",empty:"未設定",sevHigh:"高",sevMid:"中",sevLow:"低",alsoLine:"LINEも",addTitle:"ルールを追加",editTitle:"ルールを編集",rType:"ルールの種類",tForce:"要確認",tForceDesc:"取引先を手動確認",tAmount:"金額上限",tAmountDesc:"超過時に通知",tPeriod:"会計期間",tPeriodDesc:"期間外の日付を通知",tCategory:"自動送信しない",tCategoryDesc:"手動確認",fSupplierTax:"取引先の税番号",fAmountLimit:"金額上限 (฿)",fCategory:"カテゴリ名",fSeverity:"重大度",fAlsoLine:"上司にLINEも送信",fPeriodMode:"期間の範囲",pmCurrent:"今月",pmPrev:"先月",anyInvoice:"任意の請求書",cancel:"キャンセル",save:"保存",saved:"保存しました",deleted:"削除しました",delConfirm:"このルールを削除しますか?",loadFail:"読み込みに失敗",saveFail:"保存に失敗",enabled:"有効化しました · 即時反映",disabled:"無効化しました",needSupplier:"取引先の税番号を入力",needAmount:"正しい金額を入力",needCategory:"カテゴリ名を入力"}};function he(){const e=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",n=e in Io?e:"th";return Io[n]}const Jd={settings:'<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',building:'<rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/>',wallet:'<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',calendar:'<path d="M8 2v4M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',octagon:'<path d="M2.586 16.726A2 2 0 0 1 2 15.312V8.688a2 2 0 0 1 .586-1.414l4.688-4.688A2 2 0 0 1 8.688 2h6.624a2 2 0 0 1 1.414.586l4.688 4.688A2 2 0 0 1 22 8.688v6.624a2 2 0 0 1-.586 1.414l-4.688 4.688a2 2 0 0 1-1.414.586H8.688a2 2 0 0 1-1.414-.586z"/><path d="M12 8v4M12 16h.01"/>',bell:'<path d="M10.268 21a2 2 0 0 0 3.464 0"/><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"/>',pencil:'<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/>',trash:'<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',plus:'<path d="M5 12h14M12 5v14"/>',x:'<path d="M18 6 6 18M6 6l12 12"/>'};function ft(e,n=16){return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${Jd[e]}</svg>`}const Xd=`
#rules-settings-modal,#rs-add-modal{position:fixed;inset:0;z-index:9000;display:none;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,.38);}
#rs-add-modal{z-index:9010;}
#rules-settings-modal.rs-open,#rs-add-modal.rs-open{display:flex;}
.rs-pop{width:720px;max-width:100%;max-height:86vh;background:#fff;border-radius:16px;box-shadow:0 10px 32px rgba(0,0,0,.18);display:grid;grid-template-rows:auto 1fr auto;overflow:hidden;}
.rs-head{display:flex;align-items:center;gap:10px;padding:16px 20px;border-bottom:1px solid #e8e8e3;}
.rs-head h2{font-size:16px;font-weight:650;margin:0;color:#111;}
.rs-tag{font-size:11px;font-weight:600;color:#2563eb;background:#eaf1fe;border:1px solid #cfe0fc;padding:2px 7px;border-radius:6px;}
.rs-close{margin-left:auto;width:32px;height:32px;border-radius:8px;border:1px solid #e8e8e3;background:#fff;color:#999;cursor:pointer;display:grid;place-items:center;}
.rs-close:hover{border-color:#111;color:#111;}
.rs-body{overflow-y:auto;padding:16px 20px;}
.rs-foot{padding:12px 20px;border-top:1px solid #e8e8e3;display:flex;justify-content:flex-end;}
.rs-lead{font-size:13px;color:#555;line-height:1.6;margin:0 0 16px;}
.rs-group{border:1px solid #e8e8e3;border-radius:12px;margin-bottom:14px;overflow:hidden;}
.rs-ghead{display:flex;align-items:center;gap:10px;padding:13px 16px;border-bottom:1px solid #f0f0eb;}
.rs-gico{width:30px;height:30px;border-radius:8px;background:#f4f4f0;display:grid;place-items:center;color:#555;flex:none;}
.rs-gt{font-size:14px;font-weight:600;color:#111;}
.rs-gd{font-size:12px;color:#999;margin-top:1px;}
.rs-addbtn{margin-left:auto;display:inline-flex;align-items:center;gap:4px;font-size:12.5px;font-weight:600;color:#2563eb;background:#eaf1fe;border:1px solid #cfe0fc;border-radius:8px;padding:6px 11px;cursor:pointer;}
.rs-gbody{padding:4px 16px 12px;}
.rs-rule{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f0f0eb;}
.rs-rule:last-child{border-bottom:none;}
.rs-rm{min-width:0;flex:1;}
.rs-rt{font-size:13.5px;font-weight:500;color:#111;}
.rs-rt b{font-family:"SF Mono",Menlo,Consolas,monospace;font-weight:600;}
.rs-line{font-size:11px;font-weight:600;color:#16a34a;margin-left:6px;white-space:nowrap;}
.rs-rs{font-size:12px;color:#999;margin-top:3px;}
.rs-sev{font-size:11px;font-weight:600;padding:3px 9px;border-radius:10px;white-space:nowrap;flex:none;}
.rs-sev.high{background:#fee2e2;color:#dc2626;}
.rs-sev.medium{background:#fef3c7;color:#d97706;}
.rs-sev.low{background:#f4f4f0;color:#999;}
.rs-sw{width:38px;height:22px;border-radius:999px;background:#2563eb;position:relative;cursor:pointer;flex:none;border:none;padding:0;}
.rs-sw::after{content:"";position:absolute;top:2px;left:18px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.15s;}
.rs-sw.off{background:#cbd5e0;}
.rs-sw.off::after{left:2px;}
.rs-icobtn{width:28px;height:28px;border-radius:7px;border:1px solid #e8e8e3;background:#fff;color:#999;cursor:pointer;display:grid;place-items:center;flex:none;}
.rs-icobtn:hover{border-color:#111;color:#111;}
.rs-empty{font-size:12.5px;color:#999;padding:10px 0 4px;}
.rs-types{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:4px;}
.rs-type{border:1px solid #e8e8e3;border-radius:9px;padding:10px 11px;font-size:12.5px;cursor:pointer;text-align:left;background:#fff;}
.rs-type.on{border-color:#2563eb;background:#eaf1fe;}
.rs-type .tt{font-weight:600;color:#111;}
.rs-type .td{color:#999;font-size:11px;margin-top:2px;}
.rs-mlbl{font-size:12px;font-weight:600;color:#555;margin:14px 0 7px;}
.rs-field{font-size:13.5px;width:100%;border:1px solid #e8e8e3;border-radius:8px;padding:9px 11px;background:#fff;color:#111;box-sizing:border-box;}
.rs-two{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.rs-check{display:flex;align-items:center;gap:8px;font-size:13px;color:#555;margin-top:12px;cursor:pointer;}
.rs-check input{width:16px;height:16px;accent-color:#2563eb;}
.rs-btn{height:38px;padding:0 16px;border-radius:9px;font-size:13.5px;font-weight:600;cursor:pointer;border:1px solid transparent;}
.rs-btn-ghost{background:transparent;color:#6b7280;}
.rs-btn-ghost:hover{background:#f0f1ee;}
.rs-btn-primary{background:#2563eb;color:#fff;}
.rs-btn-primary:hover{background:#1d4ed8;}
@media (max-width:560px){
.rs-pop{max-height:94vh;border-radius:14px;}
.rs-types{grid-template-columns:1fr;}
.rs-two{grid-template-columns:1fr;}
.rs-rule{flex-wrap:wrap;}
.rs-rm{flex-basis:100%;}
}
`;let Bo=!1,ya=[],Ya=null,We="amount_limit",Ds="global";const Zd="/api/knowledge/rules";function Qd(){return localStorage.getItem("mrpilot_token")||""}async function Jt(e,n,a){return fetch(Zd+n,{method:e,headers:{Authorization:"Bearer "+Qd(),"Content-Type":"application/json"},body:a?JSON.stringify(a):void 0})}function ep(e){const n=Number(e);return Number.isFinite(n)?"฿ "+n.toLocaleString("en-US"):String(e)}function tp(e){const n=he(),a=s=>e===s?" selected":"";return`<option value="high"${a("high")}>${n.sevHigh}</option><option value="medium"${a("medium")}>${n.sevMid}</option><option value="low"${a("low")}>${n.sevLow}</option>`}function Lo(e,n){const a=n&&n.subject_key?escapeHtml(n.subject_key):"";return`<div class="rs-mlbl">${e}</div><input class="rs-field" id="rs-f-key" value="${a}"${n?" disabled":""}>`}function np(e){const n=he(),a=e.subject_key?escapeHtml(e.subject_key):"";if(e.rule_type==="amount_limit"){const s=ep(e.rule_body.limit);let o=n.gAmount;e.subject_type==="global"?o=n.anyInvoice:e.subject_type==="supplier"?o=`${n.fSupplierTax} <b>${a}</b>`:o=`「${a}」`;const i=e.rule_body.notify_line?` <span class="rs-line">${ft("bell",12)} ${n.alsoLine}</span>`:"";return`${o} &gt; <b>${s}</b>${i}`}if(e.rule_type==="supplier_force_review")return`<b>${a}</b> · ${n.tForceDesc}`;if(e.rule_type==="no_auto_push_category")return`「${a}」 · ${n.tCategoryDesc}`;if(e.rule_type==="accounting_period"){const o=e.rule_body.mode==="prev_month"?n.pmPrev:n.pmCurrent;return`${n.gPeriodDesc} · <b>${o}</b>`}return e.rule_type}function ap(e){const n=he(),a=e.severity||"medium",s=a==="high"?n.sevHigh:a==="low"?n.sevLow:n.sevMid;return`<div class="rs-rule"><div class="rs-rm"><div class="rs-rt">${np(e)}</div></div><span class="rs-sev ${a}">${s}</span><button class="rs-sw${e.is_active?"":" off"}" data-toggle="${e.id}" aria-label="toggle"></button><button class="rs-icobtn" data-edit="${e.id}" aria-label="edit">${ft("pencil",14)}</button><button class="rs-icobtn" data-del="${e.id}" aria-label="delete">${ft("trash",14)}</button></div>`}function Pn(e,n,a,s,o){const i=he(),l=ya.filter(m=>o.includes(m.rule_type)).map(ap).join("")||`<div class="rs-empty">${i.empty}</div>`;return`<div class="rs-group"><div class="rs-ghead"><div class="rs-gico">${ft(e,17)}</div><div><div class="rs-gt">${n}</div><div class="rs-gd">${a}</div></div><button class="rs-addbtn" data-add-type="${s}">${ft("plus",14)} ${i.add}</button></div><div class="rs-gbody">${l}</div></div>`}function Xi(){const e=he(),n=document.querySelector("#rules-settings-modal .rs-head h2");n&&(n.textContent=e.title);const a=document.getElementById("rs-body");a&&(a.innerHTML=`<p class="rs-lead">${e.lead}</p>`+Pn("building",e.gSupplier,e.gSupplierDesc,"supplier_force_review",["supplier_force_review"])+Pn("wallet",e.gAmount,e.gAmountDesc,"amount_limit",["amount_limit"])+Pn("calendar",e.gPeriod,e.gPeriodDesc,"accounting_period",["accounting_period"])+Pn("octagon",e.gCategory,e.gCategoryDesc,"no_auto_push_category",["no_auto_push_category"]))}async function qs(){try{const e=await Jt("GET","?include_inactive=1");if(!e.ok)throw new Error("http "+e.status);ya=(await e.json()).rules||[],Xi()}catch{showToast(he().loadFail,"error")}}function Ja(e){const n=he(),a=e?e.severity:We==="supplier_force_review"?"high":"medium",s=`<div class="rs-mlbl">${n.fSeverity}</div><select class="rs-field" id="rs-f-sev">${tp(a)}</select>`;if(We==="amount_limit"){const i=e?e.subject_type:Ds,r=e&&e.subject_key?escapeHtml(e.subject_key):"",l=e?String(e.rule_body.limit??""):"",m=e?!!e.rule_body.notify_line:!0,d=i==="global"?"":`<div class="rs-mlbl">${i==="category"?n.fCategory:n.fSupplierTax}</div><input class="rs-field" id="rs-f-key" value="${r}">`;return`<div class="rs-mlbl">${n.gAmountDesc}</div><select class="rs-field" id="rs-f-scope"${e?" disabled":""}><option value="global"${i==="global"?" selected":""}>${n.anyInvoice}</option><option value="supplier"${i==="supplier"?" selected":""}>${n.tForce}</option><option value="category"${i==="category"?" selected":""}>${n.fCategory}</option></select><div id="rs-f-subj">${d}</div><div class="rs-two"><div><div class="rs-mlbl">${n.fAmountLimit}</div><input class="rs-field" id="rs-f-limit" type="number" min="1" value="${l}"></div><div>${s}</div></div><label class="rs-check"><input type="checkbox" id="rs-f-line"${m?" checked":""}>${ft("bell",14)} ${n.fAlsoLine}</label>`}if(We==="supplier_force_review")return Lo(n.fSupplierTax,e)+s;if(We==="no_auto_push_category")return Lo(n.fCategory,e)+s;const o=e?e.rule_body.mode:"current_month";return`<div class="rs-mlbl">${n.fPeriodMode}</div><select class="rs-field" id="rs-f-mode"><option value="current_month"${o==="current_month"?" selected":""}>${n.pmCurrent}</option><option value="prev_month"${o==="prev_month"?" selected":""}>${n.pmPrev}</option></select>`+s}function jn(e,n,a){return`<button class="rs-type${We===e?" on":""}" data-type-pick="${e}"><div class="tt">${n}</div><div class="td">${a}</div></button>`}function sp(e){const n=he(),a=document.getElementById("rs-add-modal");if(!a)return;const s=e?"":`<div class="rs-mlbl">${n.rType}</div><div class="rs-types">`+jn("supplier_force_review",n.tForce,n.tForceDesc)+jn("amount_limit",n.tAmount,n.tAmountDesc)+jn("accounting_period",n.tPeriod,n.tPeriodDesc)+jn("no_auto_push_category",n.tCategory,n.tCategoryDesc)+"</div>";a.innerHTML=`<div class="rs-pop" style="max-width:460px;"><div class="rs-head"><h2>${e?n.editTitle:n.addTitle}</h2><button class="rs-close" id="rs-add-close">${ft("x",18)}</button></div><div class="rs-body">${s}<div id="rs-add-fields">${Ja(e)}</div></div><div class="rs-foot" style="gap:10px;"><button class="rs-btn rs-btn-ghost" id="rs-add-cancel">${n.cancel}</button><button class="rs-btn rs-btn-primary" id="rs-add-save">${n.save}</button></div></div>`,a.classList.add("rs-open")}function It(e){const n=document.getElementById(e);return n?String(n.value).trim():""}function op(){const e=he(),n=It("rs-f-sev")||"medium";if(We==="amount_limit"){const a=It("rs-f-scope")||"global",s=Number(It("rs-f-limit"));if(!Number.isFinite(s)||s<=0)return showToast(e.needAmount,"error"),{ok:!1};const o=a==="global"?null:It("rs-f-key");if(a!=="global"&&!o)return showToast(a==="category"?e.needCategory:e.needSupplier,"error"),{ok:!1};const i=document.getElementById("rs-f-line")?.checked;return{ok:!0,payload:{rule_type:"amount_limit",subject_type:a,subject_key:o,severity:n,rule_body:{limit:s,basis:"total",period:"per_invoice",notify_line:!!i}}}}if(We==="supplier_force_review"){const a=It("rs-f-key");return a?{ok:!0,payload:{rule_type:"supplier_force_review",subject_type:"supplier",subject_key:a,severity:n,rule_body:{}}}:(showToast(e.needSupplier,"error"),{ok:!1})}if(We==="no_auto_push_category"){const a=It("rs-f-key");return a?{ok:!0,payload:{rule_type:"no_auto_push_category",subject_type:"category",subject_key:a,severity:n,rule_body:{}}}:(showToast(e.needCategory,"error"),{ok:!1})}return{ok:!0,payload:{rule_type:"accounting_period",subject_type:"global",subject_key:null,severity:n,rule_body:{mode:It("rs-f-mode")||"current_month"}}}}async function ip(){const e=op();if(!(!e.ok||!e.payload))try{let n;if(Ya!==null){const a=e.payload;n=await Jt("PATCH","/"+Ya,{rule_body:a.rule_body,severity:a.severity})}else n=await Jt("POST","",e.payload);if(!n.ok)throw new Error("http "+n.status);showToast(he().saved,"success"),document.getElementById("rs-add-modal")?.classList.remove("rs-open"),await qs()}catch{showToast(he().saveFail,"error")}}async function rp(e){const n=ya.find(o=>o.id===e);if(!n)return;const a=!n.is_active;n.is_active=a;const s=document.querySelector(`#rules-settings-modal [data-toggle="${e}"]`);s&&s.classList.toggle("off",!a);try{const o=await Jt("PATCH","/"+e,{is_active:a});if(!o.ok)throw new Error("http "+o.status);showToast(a?he().enabled:he().disabled,"success")}catch{n.is_active=!a,s&&s.classList.toggle("off",a),showToast(he().saveFail,"error")}}async function lp(e){if(await showConfirm(he().delConfirm,{danger:!0}))try{const a=await Jt("DELETE","/"+e);if(!a.ok)throw new Error("http "+a.status);showToast(he().deleted,"success"),await qs()}catch{showToast(he().saveFail,"error")}}function $o(e,n){We=e,Ds="global",Ya=n?n.id:null,sp(n)}function cp(){if(Bo)return;const e=document.createElement("style");e.textContent=Xd,document.head.appendChild(e);const n=he(),a=document.createElement("div");a.id="rules-settings-modal",a.innerHTML=`<div class="rs-pop"><div class="rs-head"><h2>${n.title}</h2><span class="rs-tag">●</span><button class="rs-close" id="rs-main-close">${ft("x",18)}</button></div><div class="rs-body" id="rs-body"></div><div class="rs-foot"><button class="rs-btn rs-btn-primary" id="rs-done">${n.done}</button></div></div>`,document.body.appendChild(a);const s=document.createElement("div");s.id="rs-add-modal",document.body.appendChild(s),document.addEventListener("click",o=>{const i=o.target;(i.id==="rules-settings-modal"||i.closest("#rs-main-close")||i.closest("#rs-done"))&&a.classList.remove("rs-open"),(i.id==="rs-add-modal"||i.closest("#rs-add-close")||i.closest("#rs-add-cancel"))&&s.classList.remove("rs-open");const r=i.closest("[data-add-type]");r&&$o(r.dataset.addType);const l=i.closest("[data-edit]");if(l){const c=ya.find(u=>u.id===Number(l.dataset.edit));c&&$o(c.rule_type,c)}const m=i.closest("[data-del]");m&&lp(Number(m.dataset.del));const d=i.closest("[data-toggle]");d&&rp(Number(d.dataset.toggle));const p=i.closest("[data-type-pick]");if(p){We=p.dataset.typePick,document.querySelectorAll("#rs-add-modal .rs-type").forEach(u=>u.classList.toggle("on",u.dataset.typePick===We));const c=document.getElementById("rs-add-fields");c&&(c.innerHTML=Ja())}i.closest("#rs-add-save")&&ip()}),document.addEventListener("change",o=>{const i=o.target;if(i.id==="rs-f-scope"){Ds=i.value;const r=document.getElementById("rs-add-fields");r&&(r.innerHTML=Ja())}}),document.addEventListener("keydown",o=>{o.key==="Escape"&&(s.classList.contains("rs-open")?s.classList.remove("rs-open"):a.classList.contains("rs-open")&&a.classList.remove("rs-open"))}),Bo=!0}window.openRulesSettings=function(){cp(),document.getElementById("rules-settings-modal").classList.add("rs-open"),qs()};function dp(){const e=document.querySelector("#page-exceptions .page-head-actions");if(!e||document.getElementById("exc-rules-btn"))return;const n=document.createElement("button");n.id="exc-rules-btn",n.type="button",n.className="btn btn-ghost",n.innerHTML=ft("settings",16)+`<span class="rs-btn-label">${he().btn}</span>`,n.addEventListener("click",()=>window.openRulesSettings&&window.openRulesSettings()),e.insertBefore(n,e.firstChild)}let So=!1;async function pp(){if(!So){So=!0;try{(await Jt("GET","")).ok&&dp()}catch{}}}const Co=window.loadExceptionsPage;window.loadExceptionsPage=function(){pp(),Co&&Co()};Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]);window.__i18nSubs.push({name:"rules-settings",fn:()=>{const e=document.querySelector("#exc-rules-btn .rs-btn-label");e&&(e.textContent=he().btn),document.getElementById("rules-settings-modal")?.classList.contains("rs-open")&&Xi()}});(function(){const e=document.getElementById("page-knowledge");if(!(!e||e.dataset.wbInjected==="1")){if(!document.getElementById("kb-center-style")){const n=document.createElement("style");n.id="kb-center-style",n.textContent=`
.kb-ws-bar{display:flex;align-items:center;gap:9px;background:var(--card,#fff);border:1px solid var(--border,#e8e8e3);border-radius:9px;padding:8px 13px;font-size:13px;margin-bottom:16px}
.kb-ws-bar .kb-ws-dot{width:8px;height:8px;border-radius:50%;background:var(--ok,#16a34a);flex-shrink:0}
.kb-ws-bar.kb-ws-empty .kb-ws-dot{background:var(--warn,#d97706)}
.kb-ws-bar b{font-weight:600}
.kb-pane{display:none}
.kb-pane.active{display:block}
.kb-soon{background:var(--card,#fff);border:1px dashed var(--border,#e8e8e3);border-radius:12px;padding:46px 20px;text-align:center;color:var(--ink-3,#999)}
.kb-soon h3{color:var(--ink-2,#555);font-size:15px;margin:0 0 6px}
.kb-rules-intro{background:var(--card,#fff);border:1px solid var(--border,#e8e8e3);border-radius:12px;padding:20px}
.kb-rules-intro p{color:var(--ink-2,#555);font-size:13px;margin:0 0 14px;line-height:1.6}
.kb-info-btn{margin-left:auto;align-self:center;display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:var(--btn-blue,#2563eb);background:var(--info-bg,#dbeafe);border:none;border-radius:18px;padding:6px 13px;cursor:pointer}
.kb-info-btn:hover{background:#cfe0fd}
.kb-info-btn svg{width:14px;height:14px}
`,document.head.appendChild(n)}e.innerHTML=`
        <div class="page-head">
            <div class="page-head-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 3a9 9 0 100 18 9 9 0 000-18z"/>
                    <path d="M9.5 9a2.5 2.5 0 115 0c0 1.5-2.5 2-2.5 3.5"/>
                    <line x1="12" y1="17" x2="12" y2="17.01"/>
                </svg>
            </div>
            <div class="page-head-text">
                <h1 class="page-title" data-i18n="kb-title">客户知识</h1>
                <div class="page-subtitle" data-i18n="kb-sub">合同 / 政策 / 规矩按账套主体隔离 · AI 检查发票与问答均带出处</div>
            </div>
            <button class="kb-info-btn" id="kb-info-btn" type="button">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>
                <span data-i18n="kb-info-btn">功能介绍 · 费用</span>
            </button>
        </div>

        <div class="kb-ws-bar" id="kb-ws-bar">
            <span class="kb-ws-dot"></span>
            <span id="kb-ws-label"></span>
        </div>

        <div class="recon-tab-bar kb-tab-bar">
            <button class="recon-tab-btn active" data-kb-tab="docs">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M9.5 1.5H4a1 1 0 00-1 1v11a1 1 0 001 1h8a1 1 0 001-1V5z"/><path d="M9.5 1.5V5H13"/></svg>
                <span data-i18n="kb-tab-docs">文档库</span>
            </button>
            <button class="recon-tab-btn" data-kb-tab="qa">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M14 10a1.5 1.5 0 01-1.5 1.5H5L2 14V3.5A1.5 1.5 0 013.5 2h9A1.5 1.5 0 0114 3.5z"/></svg>
                <span data-i18n="kb-tab-qa">问答</span>
            </button>
            <button class="recon-tab-btn" data-kb-tab="rules">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 4h12M5 8h6M7 12h2"/></svg>
                <span data-i18n="kb-tab-rules">规则</span>
            </button>
        </div>

        <div id="kb-pane-docs" class="kb-pane active">
            <div class="kb-soon">
                <h3 data-i18n="kb-docs-soon-title">文档库</h3>
                <div data-i18n="kb-docs-soon">上传客户合同、采购政策、税务登记等资料,AI 检查发票和问答时引用。</div>
            </div>
        </div>

        <div id="kb-pane-qa" class="kb-pane">
            <div class="kb-soon">
                <h3 data-i18n="kb-qa-soon-title">问答</h3>
                <div data-i18n="kb-qa-soon">问关于这家客户的事,答案都带合同原文出处;查不到时如实说「资料不足」。</div>
            </div>
        </div>

        <div id="kb-pane-rules" class="kb-pane">
            <div class="kb-rules-intro">
                <p data-i18n="kb-rules-intro">客户规矩(供应商白名单 / 金额上限 / 强制人工复核 / 会计期间)直接喂给发票异常检测引擎,增删改即时生效。</p>
                <button class="btn btn-primary" id="kb-open-rules">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><path d="M2 4h12M5 8h6M7 12h2"/></svg>
                    <span data-i18n="kb-manage-rules">管理客户规矩</span>
                </button>
            </div>
        </div>
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");a[n][o]&&(s.textContent=a[n][o])})}catch{}}})();const up="/api/knowledge",kt="/static/brand/kb-cat.png?v=2";function mp(){return localStorage.getItem("mrpilot_token")||""}function z(e,n){if(typeof window.t=="function"){const a=window.t(e);if(a&&a!==e)return a}return n}function K(e){return typeof escapeHtml=="function"?escapeHtml(String(e??"")):String(e??"")}const To={file:'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>',"file-text":'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',sheet:'<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/>',image:'<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21"/>',upload:'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="m9 15 3-3 3 3"/>',message:'<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',"shield-check":'<path d="M20 13c0 5-3.5 7.5-7.7 9a1 1 0 0 1-.7 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',check:'<path d="M20 6 9 17l-5-5"/>',x:'<path d="M18 6 6 18"/><path d="M6 6l12 12"/>'};function Ke(e){return`<svg class="kb-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${To[e]||To.file}</svg>`}function Zi(e){const n=`kb-${e}-mask`,a=`kb-${e}-modal`,s=()=>document.getElementById(n)?.classList.add("open"),o=()=>document.getElementById(n)?.classList.remove("open");let i=document.getElementById(n);if(!i){i=document.createElement("div"),i.id=n,i.className=`kb-${e}-mask`,i.innerHTML=`<div class="kb-${e}-modal" id="${a}" role="dialog" aria-modal="true"></div>`,document.body.appendChild(i);const r=i;r.addEventListener("click",l=>{(l.target===r||l.target.closest(`[data-kb-${e}-close]`))&&o()}),document.addEventListener("keydown",l=>{l.key==="Escape"&&r.classList.contains("open")&&o()})}return{modal:document.getElementById(a),open:s,close:o}}function wa(){const e=window.getActiveWorkspaceClientId;if(typeof e!="function")return null;const n=e(),a=Number(n);return Number.isFinite(a)&&a>0?a:null}function Qi(){const e=wa();if(!e)return"";const a=(window._workspaceClientsCache||[]).find(s=>Number(s.id)===e);return a&&a.name?String(a.name):"#"+e}async function nn(e,n,a,s={}){const o=new URL(up+n,location.origin),i=wa();if(s.query)for(const[d,p]of Object.entries(s.query))p!=null&&o.searchParams.set(d,String(p));const r=s.withWorkspace!==!1&&i!=null;r&&(e==="GET"||e==="DELETE")&&o.searchParams.set("workspace_client_id",String(i));const l={Authorization:"Bearer "+mp()};let m=s.raw;if(!s.raw&&a!==void 0){const d=r?{workspace_client_id:i,...a}:a;l["Content-Type"]="application/json",m=JSON.stringify(d)}try{const d=await fetch(o.toString(),{method:e,headers:l,body:m});let p=null,c;const u=await d.text();if(u)try{const v=JSON.parse(u);d.ok?p=v:c=v?.detail?.error_code||v?.message_key||v?.detail||void 0}catch{}return{ok:d.ok,status:d.status,data:p,error:c}}catch{return{ok:!1,status:0,data:null,error:"network"}}}async function vp(e,n){const a=new FormData;a.append("file",e);const s=wa();return s!=null&&a.append("workspace_client_id",String(s)),nn("POST","/documents",void 0,{raw:a,withWorkspace:!1})}let Dn=null;async function er(){if(Dn!==null)return Dn;const e=await nn("GET","/bases",void 0,{withWorkspace:!1});return Dn=e.status===200||e.status===401||e.status===403,Dn}let Ho=!1;function tr(){const e=document.getElementById("kb-ws-bar"),n=document.getElementById("kb-ws-label");if(!e||!n)return;wa()?(e.classList.remove("kb-ws-empty"),n.innerHTML=z("kb-ws-current","账套主体")+"：<b>"+K(Qi())+"</b>"):(e.classList.add("kb-ws-empty"),n.textContent=z("kb-ws-none","请先在右上角选择账套主体,再使用客户私有文档与问答。"))}function fp(e){document.querySelectorAll(".kb-tab-bar .recon-tab-btn").forEach(n=>{n.classList.toggle("active",n.dataset.kbTab===e)}),document.querySelectorAll(".kb-pane").forEach(n=>{n.classList.toggle("active",n.id==="kb-pane-"+e)}),e==="docs"&&typeof window._kbRenderDocs=="function"&&window._kbRenderDocs(),e==="qa"&&typeof window._kbRenderAsk=="function"&&window._kbRenderAsk()}function hp(){if(Ho)return;const e=document.querySelector(".kb-tab-bar");if(!e)return;e.addEventListener("click",s=>{const o=s.target.closest(".recon-tab-btn");o&&o.dataset.kbTab&&fp(o.dataset.kbTab)});const n=document.getElementById("kb-open-rules");n&&n.addEventListener("click",()=>{typeof window.openRulesSettings=="function"&&window.openRulesSettings()});const a=document.getElementById("kb-info-btn");a&&a.addEventListener("click",()=>{typeof window._kbOpenInfo=="function"&&window._kbOpenInfo()}),Ho=!0}window.loadKnowledgePage=function(){hp(),tr(),document.querySelector('.kb-tab-bar .recon-tab-btn[data-kb-tab="docs"]')?.classList.contains("active")&&typeof window._kbRenderDocs=="function"&&window._kbRenderDocs()};async function Mo(){if(!window._knowledgeProbed){window._knowledgeProbed=!0;try{if(await er()){const e=document.getElementById("nav-knowledge");e&&(e.style.display="")}}catch{}}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",Mo):Mo();Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]);window.__i18nSubs.push({name:"knowledge-center",fn:tr});let Xa=!1,dt=[];function gp(e){if(e.status==="ready")return`<span class="kb-badge ready"><span class="kb-bdot"></span>${K(z("kb-doc-ready","已就绪"))}</span>`;if(e.status==="failed")return`<span class="kb-badge failed"><span class="kb-bdot"></span>${K(z("kb-doc-failed","失败"))}</span>`;const n=e.status==="uploading"?z("kb-doc-uploading","上传中…"):z("kb-doc-parsing","解析中");return`<span class="kb-badge parsing"><span class="kb-bdot"></span>${K(n)}</span>`}function bp(e){return e==="unsupported_document"?z("kb-err-unsupported_document","不支持的文件类型"):e==="embedding_failed"?z("kb-err-embedding_failed","向量化失败，可重试"):e==="processing_failed"?z("kb-err-processing_failed","文件无法解析，可能已损坏或加密"):e?z("kb-doc-failed","失败"):""}function yp(e){return(e||"").slice(0,10)}function wp(e){let n;e.status==="failed"&&e.error_code?n=`<div class="kb-doc-sub err">${K(bp(e.error_code))}</div>`:e.status==="uploading"?n=`<div class="kb-doc-sub">${K(z("kb-doc-uploading","上传中…"))}</div>`:n=`<div class="kb-doc-sub">${K((e.source_type||"").toUpperCase())} · ${K(yp(e.created_at))}</div>`;const a=e.status==="uploading"?"":`<button class="btn btn-sm btn-ghost kb-doc-del" data-id="${e.id}">${K(z("kb-doc-delete","删除"))}</button>`;return`<div class="kb-doc-row" data-id="${e.id}">
        <div class="kb-doc-ic">${kp(e.source_type)}</div>
        <div class="kb-doc-meta"><div class="kb-doc-name">${K(e.filename)}</div>${n}</div>
        ${gp(e)}${a}
    </div>`}function kp(e){const n=(e||"").toLowerCase();return n==="doc"||n==="docx"?Ke("file-text"):n==="xls"||n==="xlsx"||n==="csv"?Ke("sheet"):["png","jpg","jpeg","webp"].includes(n)?Ke("image"):Ke("file")}function nr(){return document.getElementById("kb-doc-list")}function En(){const e=nr();if(e){if(!dt.length){e.innerHTML=`<div class="kb-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>
            <h4>${K(z("kb-doc-empty-title","还没有文档"))}</h4>
            <div>${K(z("kb-doc-empty","上传客户合同、采购政策、税务登记等资料，AI 检查发票和问答时引用。"))}</div>
        </div>`;return}e.innerHTML=dt.map(wp).join("")}}function Ao(e){const n=nr();n&&(n.innerHTML=e)}async function ar(){Ao('<div class="kb-skel"><div class="kb-skrow"></div><div class="kb-skrow"></div><div class="kb-skrow"></div></div>');const e=await nn("GET","/documents");if(!e.ok){Ao(`<div class="kb-empty err">
            <div>${K(z("kb-doc-error","加载失败"))}</div>
            <button class="btn btn-sm kb-doc-reload" style="margin-top:12px">${K(z("kb-doc-retry","重试"))}</button>
        </div>`);return}dt=(e.data?.documents||[]).filter(n=>n.status!=="deleted"),En()}async function Po(e){const n=Array.from(e);if(n.length)for(const a of n){const s=-Date.now()-Math.floor(Math.random()*1e3);dt.unshift({id:s,filename:a.name,source_type:(a.name.split(".").pop()||"").toLowerCase(),status:"uploading",error_code:null,created_at:new Date().toISOString()}),En();const o=await vp(a),i=dt.findIndex(r=>r.id===s);i<0||(o.ok&&o.data?.document?(dt[i]=o.data.document,o.data.document.status==="failed"&&showToast(z("kb-doc-failed","失败")+"："+a.name,"error")):(dt.splice(i,1),showToast(z("kb-upload-fail","上传失败")+"："+a.name,"error")),En())}}async function xp(e){if(!(typeof showConfirm=="function"?await showConfirm(z("kb-doc-del-confirm","确定删除这份文档？删除后 AI 将不再引用它。")):!0))return;(await nn("DELETE","/documents/"+e)).ok?(dt=dt.filter(s=>s.id!==e),En()):showToast(z("kb-doc-del-fail","删除失败"),"error")}function _p(){const e=document.getElementById("kb-pane-docs");if(!e||Xa&&e.querySelector("#kb-doc-list"))return;if(!document.getElementById("kb-docs-style")){const s=document.createElement("style");s.id="kb-docs-style",s.textContent=`
.kb-up{border:1.5px dashed var(--border,#e8e8e3);border-radius:12px;background:var(--card,#fff);padding:22px;text-align:center;color:var(--ink-3,#999);margin-bottom:16px;cursor:pointer;transition:.15s}
.kb-up:hover,.kb-up.drag{border-color:var(--brand,#111);color:var(--ink-2,#555);background:var(--bg,#f4f4f0)}
.kb-up svg{width:26px;height:26px;stroke:currentColor;fill:none;stroke-width:1.5;margin-bottom:6px}
.kb-up b{color:var(--btn-blue,#2563eb)}
.kb-up .kb-up-types{font-size:11px;color:var(--ink-3,#999);margin-top:4px}
.kb-doc-list{background:var(--card,#fff);border:1px solid var(--border,#e8e8e3);border-radius:12px;overflow:hidden;min-height:80px}
.kb-doc-row{display:flex;align-items:center;gap:13px;padding:13px 16px;border-bottom:1px solid var(--border,#e8e8e3)}
.kb-doc-row:last-child{border-bottom:none}
.kb-doc-ic{width:34px;height:34px;border-radius:8px;background:var(--bg,#f4f4f0);display:grid;place-items:center;flex-shrink:0;color:var(--ink-2,#555)}
.kb-doc-ic svg{width:17px;height:17px}
.kb-doc-meta{flex:1;min-width:0}
.kb-doc-name{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kb-doc-sub{font-size:11px;color:var(--ink-3,#999);margin-top:1px}
.kb-doc-sub.err{color:var(--danger,#dc2626)}
.kb-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:600;flex-shrink:0}
.kb-bdot{width:6px;height:6px;border-radius:50%}
.kb-badge.ready{background:#ecfdf3;color:#067647}.kb-badge.ready .kb-bdot{background:#16a34a}
.kb-badge.parsing{background:#dbeafe;color:#1e40af}.kb-badge.parsing .kb-bdot{background:#2563eb}
.kb-badge.failed{background:#fef3f2;color:#b42318}.kb-badge.failed .kb-bdot{background:#dc2626}
.kb-doc-del{color:var(--ink-3,#999)!important}
.kb-doc-del:hover{color:var(--danger,#dc2626)!important}
.kb-empty{text-align:center;padding:42px 20px;color:var(--ink-3,#999)}
.kb-empty.err{color:var(--danger,#dc2626)}
.kb-empty svg{width:38px;height:38px;stroke:var(--ink-4,#cbd5e0);fill:none;stroke-width:1.4;margin-bottom:10px}
.kb-empty h4{color:var(--ink-2,#555);font-size:14px;margin:0 0 6px}
.kb-skel{padding:14px}
.kb-skrow{height:46px;border-radius:8px;margin-bottom:10px;background:linear-gradient(90deg,#f0f0ec 25%,#f7f7f3 50%,#f0f0ec 75%);background-size:200% 100%;animation:kbShine 1.3s infinite}
.kb-skrow:last-child{margin-bottom:0}
@keyframes kbShine{to{background-position:-200% 0}}
`,document.head.appendChild(s)}e.innerHTML=`
        <div class="kb-up" id="kb-up">
            <svg viewBox="0 0 24 24"><path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>
            <div><span data-i18n="kb-upload-hint">把文档拖到这里，或</span> <b data-i18n="kb-upload">点击上传</b></div>
            <div class="kb-up-types" data-i18n="kb-upload-types">支持 PDF · Word · Excel · 图片 — 合同 / 政策 / 税务登记等客户私有资料</div>
            <input type="file" id="kb-file" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.png,.jpg,.jpeg,.webp" style="display:none">
        </div>
        <div class="kb-doc-list" id="kb-doc-list"></div>
    `;try{const s=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",o=window.I18N;o&&o[s]&&e.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");o[s][r]&&(i.textContent=o[s][r])})}catch{}const n=e.querySelector("#kb-up"),a=e.querySelector("#kb-file");n.addEventListener("click",s=>{s.target.closest("input")||a.click()}),a.addEventListener("change",()=>{a.files&&Po(a.files),a.value=""}),["dragenter","dragover"].forEach(s=>n.addEventListener(s,o=>{o.preventDefault(),n.classList.add("drag")})),["dragleave","drop"].forEach(s=>n.addEventListener(s,o=>{o.preventDefault(),n.classList.remove("drag")})),n.addEventListener("drop",s=>{const o=s.dataTransfer;o?.files?.length&&Po(o.files)}),e.addEventListener("click",s=>{const o=s.target,i=o.closest(".kb-doc-del");if(i?.dataset.id){xp(Number(i.dataset.id));return}o.closest(".kb-doc-reload")&&ar()}),Xa=!0}function Ep(){_p(),ar()}window._kbRenderDocs=Ep;Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]);window.__i18nSubs.push({name:"knowledge-documents",fn:()=>{Xa&&En()}});let ta=null;function Ip(){if(ta)return;const e=document.createElement("style");e.id="kb-src-style",e.textContent=`
.kb-src-mask{position:fixed;inset:0;background:rgba(17,17,17,.42);z-index:1200;display:none;align-items:center;justify-content:center;padding:20px}
.kb-src-mask.open{display:flex}
.kb-src-modal{background:#fff;border-radius:16px;width:560px;max-width:100%;max-height:86vh;overflow:auto;box-shadow:0 30px 80px rgba(17,17,17,.3)}
.kb-src-head{display:flex;align-items:flex-start;gap:13px;padding:20px 22px 0}
.kb-src-head .ic{width:42px;height:42px;border-radius:11px;background:var(--bg,#f4f4f0);display:grid;place-items:center;color:var(--ink-2,#555);flex-shrink:0}
.kb-src-head .ic svg{width:20px;height:20px}
.kb-src-head h3{font-size:16px;font-weight:800;margin:0;word-break:break-all}
.kb-src-head .sub{font-size:12px;color:var(--ink-3,#999);margin-top:2px}
.kb-src-head .x{margin-left:auto;color:var(--ink-3,#999);width:30px;height:30px;border-radius:8px;display:grid;place-items:center;cursor:pointer;border:none;background:none;flex-shrink:0}
.kb-src-head .x svg{width:16px;height:16px}
.kb-src-head .x:hover{background:var(--bg,#f4f4f0);color:var(--ink,#111)}
.kb-src-body{padding:16px 22px 22px}
.kb-src-rel{display:inline-flex;align-items:center;gap:6px;margin-bottom:12px;font-size:12px;color:var(--info-ink,#1e40af);background:var(--info-bg,#dbeafe);border-radius:8px;padding:6px 11px}
.kb-src-preview{border:1px solid var(--border,#e8e8e3);border-radius:12px;padding:16px 18px;font-size:13px;line-height:1.8;color:var(--ink-2,#555);background:var(--card,#fff);max-height:44vh;overflow:auto}
.kb-src-preview .seg.hit{background:#fff3c4;border-radius:3px;padding:1px 3px;color:var(--ink,#111);font-weight:600;box-shadow:0 0 0 1px #fde68a}
.kb-src-loading,.kb-src-fail{color:var(--ink-3,#999);font-size:12.5px;line-height:1.6}
.kb-src-foot{font-size:12px;color:var(--ink-3,#999);margin-top:14px;line-height:1.6}
`,document.head.appendChild(e),ta=Zi("src")}function Bp(e){const n=K(e.text).replace(/\n/g,"<br>");return`<span class="seg${e.matched?" hit":""}">${n}</span>`}function Lp(e){return e.segments.map(Bp).join("<br><br>")}async function $p(e){Ip();const n=ta?.modal;if(!n)return;const a=e.filename||z("kb-src-unknown","未知来源"),s=typeof e.score=="number"?Math.round(Math.max(0,Math.min(1,e.score))*100):null,o=typeof e.chunk_id=="number";if(n.innerHTML=`
        <div class="kb-src-head">
            <span class="ic">${Ke("file")}</span>
            <div>
                <h3>${K(a)}</h3>
                <div class="sub">${K(z(o?"kb-src-hit":"kb-src-from",o?"命中片段已高亮":"此结论引用自以下文档"))}</div>
            </div>
            <button class="x" data-kb-src-close aria-label="close">${Ke("x")}</button>
        </div>
        <div class="kb-src-body">
            ${s!==null?`<div class="kb-src-rel">${K(z("kb-src-relevance","相关度"))} ${s}%</div>`:""}
            <div class="kb-src-preview" id="kb-src-preview">${o?`<div class="kb-src-loading">${K(z("kb-src-loading","正在取原文…"))}</div>`:`<div class="kb-src-fail">${K(z("kb-src-no-chunk","可在文档库打开原件核对。"))}</div>`}</div>
            <p class="kb-src-foot">${K(z("kb-src-verifiable","这就是「可核对」:AI 说的每句话都能点回原文这一句,会计自己一眼能确认,不用盲信。"))}</p>
        </div>
    `,ta?.open(),!o)return;const i=await nn("GET","/chunks/"+e.chunk_id),r=n.querySelector("#kb-src-preview");r&&(i.ok&&i.data?.segments?.length?r.innerHTML=Lp(i.data):r.innerHTML=`<div class="kb-src-fail">${K(z("kb-src-load-fail","原文片段暂时取不到,可在文档库打开原件核对。"))}</div>`)}window._kbOpenSource=e=>{$p(e)};function Sp(e){return`<div class="kb-msg user"><div class="kb-bub">${K(e)}</div></div>`}function Cp(e){const n=e.filename||z("kb-src-unknown","未知来源");return`<button class="kb-cite" data-cite='${K(JSON.stringify(e))}'>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>
        ${K(n)}<span class="ch">›</span></button>`}function Tp(e){if(e.no_answer){const a=z(e.message_key||"ask.no_source","资料不足，无法判断。");return`<div class="kb-msg ai"><div class="kb-ava"><img src="${kt}" alt=""></div>
            <div class="kb-bub no-src">${K(a)}</div></div>`}const n=(e.citations||[]).map(a=>Cp(a)).join("");return`<div class="kb-msg ai"><div class="kb-ava"><img src="${kt}" alt=""></div>
        <div class="kb-bub">${K(e.answer)}${n?`<div class="kb-cites">${n}</div>`:""}</div></div>`}function Hp(e){return nn("POST","/ask",{question:e})}function jo(e){return`<div class="kb-msg ai"><div class="kb-ava"><img src="${kt}" alt=""></div><div class="kb-bub no-src">${K(e)}</div></div>`}function sr(e,n,a){if(e.dataset.kbWired==="1")return;e.dataset.kbWired="1";let s=!1;function o(r){const l=document.createElement("div");l.innerHTML=r;const m=l.firstElementChild;return e.appendChild(m),e.scrollTop=e.scrollHeight,m}async function i(){const r=n.value.trim();if(!r||s)return;s=!0,n.value="",o(Sp(r));const l=o(`<div class="kb-msg ai"><div class="kb-ava"><img src="${kt}" alt=""></div><div class="kb-bub kb-thinking">${K(z("kb-ask-thinking","思考中…"))}</div></div>`),m=await Hp(r);if(l.remove(),m.status===402){const d=z("kb-ask-low-balance","余额不足，请先充值后再提问。");o(jo(d)),typeof showToast=="function"&&showToast(d,"error")}else if(!m.ok||!m.data){const d=z("kb-ask-error","出错了，请稍后重试。");o(jo(d)),typeof showToast=="function"&&showToast(d,"error")}else o(Tp(m.data));s=!1}a.addEventListener("click",i),n.addEventListener("keydown",r=>{r.key==="Enter"&&!r.shiftKey&&(r.preventDefault(),i())}),e.addEventListener("click",r=>{const l=r.target.closest(".kb-cite");if(!(!l||!l.dataset.cite))try{const m=JSON.parse(l.dataset.cite);typeof window._kbOpenSource=="function"&&window._kbOpenSource(m)}catch{}})}window._kbWireAsk=sr;function Mp(){if(document.getElementById("kb-ask-style"))return;const e=document.createElement("style");e.id="kb-ask-style",e.textContent=`
.kb-qa{background:var(--card,#fff);border:1px solid var(--border,#e8e8e3);border-radius:12px;display:flex;flex-direction:column;height:460px;max-width:760px}
.kb-qa-thread{flex:1;padding:18px;display:flex;flex-direction:column;gap:16px;overflow:auto}
.kb-msg{max-width:80%;display:flex;gap:9px}
.kb-msg.user{align-self:flex-end}
.kb-msg.user .kb-bub{background:var(--btn-blue,#2563eb);color:#fff;border-radius:14px 14px 4px 14px;padding:9px 13px}
.kb-msg.ai{align-self:flex-start}
.kb-ava{width:28px;height:28px;border-radius:8px;background:#fff7ee;flex-shrink:0;display:grid;place-items:center;overflow:hidden}
.kb-ava img{width:28px;height:28px;object-fit:cover;object-position:center 16%}
.kb-msg.ai .kb-bub{background:var(--bg,#f4f4f0);border-radius:14px 14px 14px 4px;padding:10px 14px;line-height:1.6}
.kb-bub.no-src{border-left:3px solid var(--warn,#d97706);color:var(--ink-2,#555)}
.kb-bub.kb-thinking{color:var(--ink-3,#999)}
.kb-cites{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}
.kb-cite{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid var(--border,#e8e8e3);border-radius:9px;padding:6px 10px;font-size:12px;font-weight:600;color:var(--info-ink,#1e40af);cursor:pointer}
.kb-cite:hover{border-color:var(--btn-blue,#2563eb);box-shadow:0 2px 8px rgba(37,99,235,.12)}
.kb-cite svg{width:13px;height:13px}
.kb-cite .ch{color:var(--ink-3,#999)}
.kb-qa-foot{border-top:1px solid var(--border,#e8e8e3);padding:0}
.kb-qa-ex{display:flex;flex-wrap:wrap;gap:7px;padding:11px 14px 0}
.kb-chip{background:#fff;border:1px solid var(--border,#e8e8e3);border-radius:18px;padding:5px 11px;font-size:12px;color:var(--ink-2,#555);cursor:pointer}
.kb-chip:hover{border-color:var(--btn-blue,#2563eb);color:var(--btn-blue,#2563eb)}
.kb-qa-input{display:flex;gap:9px;align-items:center;padding:12px 14px}
.kb-qa-input input{flex:1;border:1px solid var(--border,#e8e8e3);border-radius:9px;padding:9px 13px;font-size:13px;font-family:inherit;background:var(--bg,#f4f4f0)}
.kb-qa-input input:focus{outline:none;border-color:var(--btn-blue,#2563eb);background:#fff}
.kb-send{width:38px;height:38px;border-radius:9px;background:var(--btn-blue,#2563eb);color:#fff;display:grid;place-items:center;flex-shrink:0;border:none;cursor:pointer}
.kb-send:hover{background:var(--btn-blue-hover,#1d4ed8)}
.kb-send svg{width:17px;height:17px;stroke:#fff;fill:none;stroke-width:2}
.kb-qa-hint{font-size:12px;color:var(--ink-3,#999);margin-top:12px;max-width:760px;line-height:1.6}
.kb-ft{display:flex;align-items:center;gap:13px;background:var(--card,#fff);border:1px solid var(--border,#e8e8e3);border-radius:12px;padding:13px 16px;margin-bottom:16px;max-width:760px}
.kb-ft .ft-cat{width:38px;height:38px;border-radius:10px;background:#fff7ee;display:grid;place-items:center;overflow:hidden;flex-shrink:0}
.kb-ft .ft-cat img{width:34px;height:34px;object-fit:cover;object-position:center 16%}
.kb-ft .ft-txt{flex:1}
.kb-ft .ft-txt b{font-weight:700}
.kb-ft .ft-txt .sub{font-size:11px;color:var(--ink-3,#999);margin-top:1px}
.kb-switch{width:38px;height:22px;border-radius:20px;background:#d6d6d0;position:relative;transition:.18s;flex-shrink:0;cursor:pointer;border:none}
.kb-switch.on{background:var(--btn-blue,#2563eb)}
.kb-switch::after{content:"";position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.18s;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.kb-switch.on::after{left:18px}
`,document.head.appendChild(e)}function Ap(){const e=document.getElementById("kb-pane-qa");if(!e||e.dataset.kbBuilt==="1")return;Mp();const n=K(z("kb-ask-ex1","这家客户有金额上限吗？")),a=K(z("kb-ask-ex2","合同约定的付款周期是多久？")),s=K(z("kb-ask-ex3","哪些供应商需要人工复核？")),o=typeof window._kbFabEnabled=="function"&&window._kbFabEnabled();e.innerHTML=`
        <div class="kb-ft">
            <span class="ft-cat"><img src="${kt}" alt=""></span>
            <div class="ft-txt">
                <b>${K(z("kb-fab-toggle","桌面悬浮问答助手"))}</b>
                <div class="sub">${K(z("kb-fab-toggle-sub","打开后任意页面右下角常驻一只猫，随手就能问，可长按拖到屏幕任意一边。"))}</div>
            </div>
            <button class="kb-switch${o?" on":""}" id="kb-fab-switch" role="switch" aria-checked="${o}"></button>
        </div>
        <div class="kb-qa">
            <div class="kb-qa-thread" id="kb-qa-thread">
                <div class="kb-msg ai"><div class="kb-ava"><img src="${kt}" alt=""></div>
                <div class="kb-bub">${K(z("kb-ask-empty","问点关于这家客户的事，答案都带合同原文出处；查不到时如实说「资料不足」。"))}</div></div>
            </div>
            <div class="kb-qa-foot">
                <div class="kb-qa-ex">
                    <button class="kb-chip" data-q="${n}">${n}</button>
                    <button class="kb-chip" data-q="${a}">${a}</button>
                    <button class="kb-chip" data-q="${s}">${s}</button>
                </div>
                <div class="kb-qa-input">
                    <input id="kb-qa-input" data-i18n-placeholder="kb-ask-placeholder" placeholder="${K(z("kb-ask-placeholder","问点关于这家客户的事…"))}">
                    <button class="kb-send" id="kb-qa-send"><svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button>
                </div>
            </div>
        </div>
        <p class="kb-qa-hint">${K(z("kb-ask-disclaimer","AI 的每个结论都带可点开的出处；查不到依据时固定回答「资料不足」，绝不编。"))}</p>
    `,e.dataset.kbBuilt="1";const i=e.querySelector("#kb-qa-thread"),r=e.querySelector("#kb-qa-input"),l=e.querySelector("#kb-qa-send");sr(i,r,l),e.querySelectorAll(".kb-chip").forEach(d=>{d.addEventListener("click",()=>{r.value=d.dataset.q||"",l.click()})});const m=e.querySelector("#kb-fab-switch");m?.addEventListener("click",()=>{const d=!m.classList.contains("on");m.classList.toggle("on",d),m.setAttribute("aria-checked",String(d)),typeof window._kbFabSetEnabled=="function"&&window._kbFabSetEnabled(d)})}window._kbRenderAsk=Ap;const Rs="pearnly_kb_fab",Za=kt,pt=14;let Qa=!1,Do=!1;function Pp(){if(document.getElementById("kb-fab-style"))return;const e=document.createElement("style");e.id="kb-fab-style",e.textContent=`
.kb-fab{position:fixed;left:0;top:62%;z-index:1100;touch-action:none;display:none}
.kb-fab.on{display:block}
.kb-fab.snapping{transition:left .26s cubic-bezier(.3,.85,.3,1),top .26s cubic-bezier(.3,.85,.3,1)}
.kb-fab-btn{position:relative;width:56px;height:56px;background:none;border:none;padding:0;display:grid;place-items:center;cursor:grab;animation:kbBob 3.4s ease-in-out infinite}
.kb-fab-btn.jump{animation:kbJump .7s cubic-bezier(.3,1.5,.5,1)}
.kb-fab-btn.cheer{animation:kbCheer .6s ease}
.kb-fab.lifted .kb-fab-btn{cursor:grabbing;animation:none}
.kb-fab-btn img{width:56px;height:56px;object-fit:contain;pointer-events:none;filter:drop-shadow(0 6px 6px rgba(17,17,17,.22));transition:filter .15s,transform .15s;transform-origin:50% 90%}
.kb-fab-btn:hover img{transform:translateY(-2px) scale(1.05)}
.kb-fab.lifted .kb-fab-btn img{filter:drop-shadow(0 18px 14px rgba(17,17,17,.3));transform:scale(1.08) rotate(-3deg)}
@keyframes kbBob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
@keyframes kbJump{0%{transform:translateY(0)}30%{transform:translateY(-16px) rotate(-4deg)}55%{transform:translateY(0) scaleY(.92) scaleX(1.06)}75%{transform:translateY(-5px)}100%{transform:translateY(0)}}
@keyframes kbCheer{0%{transform:translateY(0)}25%{transform:translateY(-10px) rotate(6deg)}50%{transform:translateY(0) scaleY(.9) scaleX(1.08)}70%{transform:translateY(-6px) rotate(-5deg)}100%{transform:translateY(0)}}
.kb-say{position:absolute;bottom:60px;left:50%;transform:translateX(-50%) scale(.6);transform-origin:bottom center;background:#111;color:#fff;font-size:11px;font-weight:700;padding:5px 11px;border-radius:13px;white-space:nowrap;opacity:0;pointer-events:none;transition:.18s;box-shadow:0 4px 12px rgba(17,17,17,.2)}
.kb-say::after{content:"";position:absolute;bottom:-5px;left:50%;transform:translateX(-50%);border:5px solid transparent;border-top-color:#111;border-bottom:0}
.kb-say.show{opacity:1;transform:translateX(-50%) scale(1)}
.kb-spark{position:absolute;left:50%;top:8px;font-size:15px;pointer-events:none;animation:kbFloat 1s ease-out forwards}
@keyframes kbFloat{0%{opacity:0;transform:translate(-50%,0) scale(.4)}25%{opacity:1}100%{opacity:0;transform:translate(var(--dx,0),-46px) scale(1.1)}}
.kb-card{position:fixed;width:380px;height:520px;z-index:1101;display:none;flex-direction:column;background:rgba(255,255,255,.86);backdrop-filter:blur(22px) saturate(1.5);-webkit-backdrop-filter:blur(22px) saturate(1.5);border:1px solid rgba(255,255,255,.78);border-radius:18px;box-shadow:0 24px 60px rgba(17,17,17,.24);overflow:hidden}
.kb-card.open{display:flex;animation:kbPop .22s cubic-bezier(.2,.9,.3,1.2)}
@keyframes kbPop{from{opacity:0;transform:translateY(20px) scale(.96)}to{opacity:1;transform:none}}
.kb-card-top{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;border-bottom:1px solid rgba(17,17,17,.07)}
.kb-card-top .tt{font-weight:700;display:flex;align-items:center;gap:8px;font-size:13px}
.kb-card-top .tt .mini{width:26px;height:26px;border-radius:8px;background:#fff7ee;overflow:hidden;display:grid;place-items:center}
.kb-card-top .tt .mini img{width:26px;height:26px;object-fit:cover;object-position:center 16%}
.kb-card-top .ws{font-size:11px;color:var(--ink-2,#555);background:rgba(255,255,255,.6);border:1px solid var(--border,#e8e8e3);border-radius:7px;padding:3px 8px;font-weight:600;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kb-card-x{width:26px;height:26px;border-radius:7px;display:grid;place-items:center;color:var(--ink-3,#999);border:none;background:none;cursor:pointer}
.kb-card-x:hover{background:rgba(17,17,17,.06);color:var(--ink,#111)}
.kb-card .kb-qa-thread{background:transparent}
.kb-card .kb-qa-input{border-top:1px solid rgba(17,17,17,.07)}
@media(max-width:820px){.kb-card{right:0!important;left:0!important;bottom:0!important;top:auto!important;width:100%;height:78vh;border-radius:18px 18px 0 0}}
`,document.head.appendChild(e)}let Z,vt,Vn,He;function jp(){Qa||(Pp(),Z=document.createElement("div"),Z.className="kb-fab",Z.id="kb-fab",Z.innerHTML=`
        <span class="kb-say" id="kb-say">${z("kb-fab-hi","喵~")}</span>
        <button class="kb-fab-btn" id="kb-fab-btn" aria-label="${z("kb-fab-aria","问 AI")}"><img src="${Za}" alt=""></button>`,document.body.appendChild(Z),He=document.createElement("div"),He.className="kb-card",He.id="kb-card",He.innerHTML=`
        <div class="kb-card-top">
            <div class="tt"><span class="mini"><img src="${Za}" alt=""></span> ${z("kb-fab-title","客户知识助手")}</div>
            <div style="display:flex;align-items:center;gap:8px">
                <span class="ws" id="kb-card-ws"></span>
                <button class="kb-card-x" id="kb-card-x" aria-label="close">✕</button>
            </div>
        </div>
        <div class="kb-qa-thread" id="kb-card-thread" style="flex:1;padding:15px;display:flex;flex-direction:column;gap:14px;overflow:auto"></div>
        <div class="kb-qa-input">
            <input id="kb-card-input" placeholder="${z("kb-fab-ph","随处可问，不跳页…")}">
            <button class="kb-send" id="kb-card-send"><svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></button>
        </div>`,document.body.appendChild(He),vt=Z.querySelector("#kb-fab-btn"),Vn=Z.querySelector("#kb-say"),document.getElementById("kb-card-x")?.addEventListener("click",es),document.addEventListener("keydown",e=>{e.key==="Escape"&&es()}),Vp(),Np(),Op(),Qa=!0)}function Dp(){const e=document.getElementById("kb-card-thread"),n=document.getElementById("kb-card-input"),a=document.getElementById("kb-card-send");!Do&&typeof window._kbWireAsk=="function"&&(e.innerHTML=`<div class="kb-msg ai"><div class="kb-ava"><img src="${Za}" alt=""></div><div class="kb-bub">${z("kb-ask-empty","问点关于这家客户的事，答案都带出处；查不到时如实说「资料不足」。")}</div></div>`,window._kbWireAsk(e,n,a),Do=!0);const s=document.getElementById("kb-card-ws");s&&(s.textContent=Qi()||z("kb-fab-no-ws","未选账套")),qp(),He.classList.add("open"),Fp(),or(["💛","✨","💙","🐾"])}function es(){He?.classList.remove("open")}function qp(){const e=Z.getBoundingClientRect(),n=520,a=e.left+e.width/2<window.innerWidth/2,s=Math.min(Math.max(pt,e.top+e.height/2-n/2),window.innerHeight-n-pt);He.style.top=s+"px",a?(He.style.left=e.right+12+"px",He.style.right="auto"):(He.style.right=window.innerWidth-e.left+12+"px",He.style.left="auto")}let qo;function Rp(e,n=1500){Vn.textContent=e,Vn.classList.add("show"),clearTimeout(qo),qo=setTimeout(()=>Vn.classList.remove("show"),n)}function Fp(){vt.classList.remove("jump"),vt.classList.add("cheer"),setTimeout(()=>vt.classList.remove("cheer"),650)}function zp(){Z.classList.contains("lifted")||(vt.classList.remove("cheer"),vt.classList.add("jump"),setTimeout(()=>vt.classList.remove("jump"),720))}function or(e){for(let n=0;n<5;n++){const a=document.createElement("span");a.className="kb-spark",a.textContent=e[n%e.length],a.style.setProperty("--dx",n*14-28+"px"),a.style.left=30+n*10+"%",a.style.animationDelay=n*40+"ms",Z.appendChild(a),setTimeout(()=>a.remove(),1100)}}function Np(){const e=[z("kb-fab-hi","喵?"),z("kb-fab-ask","问我呀!"),"🐾"];vt.addEventListener("mouseenter",()=>{Z.classList.contains("lifted")||Rp(e[(Date.now()/1e3|0)%e.length],1400)}),setInterval(()=>{!Z.classList.contains("on")||Z.classList.contains("lifted")||He.classList.contains("open")||(Date.now()/1e3|0)%2===0&&(zp(),or(["✨","🐾"]))},5400)}function Ma(e){return Math.min(Math.max(pt,e),window.innerHeight-Z.offsetHeight-pt)}function Op(){Z.classList.add("snapping"),Z.style.left=window.innerWidth-56-pt+"px",Z.style.top="62%"}function Vp(){let e,n=!1,a=!1,s=0,o=0,i=0,r=0;function l(c){s=c.clientX,o=c.clientY,a=!1,n=!1;const u=Z.getBoundingClientRect();i=u.left,r=u.top,Z.classList.remove("snapping"),e=setTimeout(()=>{Z.classList.add("lifted")},180),window.addEventListener("pointermove",m),window.addEventListener("pointerup",d),c.preventDefault()}function m(c){const u=c.clientX-s,v=c.clientY-o;!n&&Math.hypot(u,v)>6&&(n=!0,Z.classList.add("lifted"),clearTimeout(e)),n&&(a=!0,Z.style.left=i+u+"px",Z.style.top=Ma(r+v)+"px")}function d(){if(clearTimeout(e),window.removeEventListener("pointermove",m),window.removeEventListener("pointerup",d),Z.classList.remove("lifted"),!a){Dp();return}p()}function p(){const c=Z.getBoundingClientRect();Z.classList.add("snapping"),Z.style.top=Ma(c.top)+"px",Z.style.left=(c.left+c.width/2<window.innerWidth/2?pt:window.innerWidth-Z.offsetWidth-pt)+"px"}vt.addEventListener("pointerdown",l),window.addEventListener("resize",()=>{if(!Qa)return;const c=Z.getBoundingClientRect();Z.style.top=Ma(c.top)+"px",Z.style.left=(c.left+c.width/2<window.innerWidth/2?pt:window.innerWidth-Z.offsetWidth-pt)+"px"})}function ir(e){jp(),localStorage.setItem(Rs,e?"1":"0"),Z.classList.toggle("on",e),e||es()}window._kbFabSetEnabled=ir;window._kbFabEnabled=()=>localStorage.getItem(Rs)==="1";async function Ro(){if(localStorage.getItem(Rs)==="1")try{await er()&&ir(!0)}catch{}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",Ro):Ro();let na=null;function Up(){if(na)return;const e=document.createElement("style");e.id="kb-info-style",e.textContent=`
.kb-info-mask{position:fixed;inset:0;background:rgba(17,17,17,.42);z-index:1300;display:none;align-items:center;justify-content:center;padding:20px}
.kb-info-mask.open{display:flex}
.kb-info-modal{background:#fff;border-radius:16px;width:560px;max-width:100%;max-height:88vh;overflow:auto;box-shadow:0 30px 80px rgba(17,17,17,.3)}
.kb-info-head{display:flex;align-items:flex-start;gap:14px;padding:22px 24px 0}
.kb-info-head .ic{width:52px;height:52px;border-radius:13px;background:#fff7ee;overflow:hidden;display:grid;place-items:center;flex-shrink:0}
.kb-info-head .ic img{width:48px;height:48px;object-fit:cover;object-position:center 14%}
.kb-info-head h2{font-size:18px;font-weight:800;margin:0}
.kb-info-head .lead{color:var(--ink-2,#555);font-size:12.5px;margin-top:3px;line-height:1.55}
.kb-info-head .x{margin-left:auto;color:var(--ink-3,#999);width:30px;height:30px;border-radius:8px;display:grid;place-items:center;cursor:pointer;border:none;background:none;flex-shrink:0}
.kb-info-head .x svg{width:16px;height:16px}
.kb-info-head .x:hover{background:var(--bg,#f4f4f0);color:var(--ink,#111)}
.kb-info-body{padding:18px 24px 24px}
.kb-info-h{font-size:13px;font-weight:800;margin:18px 0 9px;display:flex;align-items:center;gap:8px}
.kb-info-h .l{width:4px;height:14px;border-radius:3px;background:var(--btn-blue,#2563eb)}
.kb-info-use{list-style:none;display:flex;flex-direction:column;gap:9px;padding:0;margin:0}
.kb-info-use li{display:flex;gap:10px;font-size:12.5px;color:var(--ink-2,#555);line-height:1.55}
.kb-info-use li .ck{width:20px;height:20px;border-radius:6px;background:var(--info-bg,#dbeafe);color:var(--info-ink,#1e40af);display:grid;place-items:center;flex-shrink:0}
.kb-info-use li .ck svg{width:13px;height:13px;stroke-width:2.4}
.kb-info-price{border:1px solid var(--border,#e8e8e3);border-radius:12px;overflow:hidden}
.kb-info-price .row{display:flex;align-items:center;gap:12px;padding:13px 15px;border-bottom:1px solid var(--border,#e8e8e3)}
.kb-info-price .row:last-child{border-bottom:none}
.kb-info-price .pi{width:34px;height:34px;border-radius:9px;background:var(--bg,#f4f4f0);display:grid;place-items:center;color:var(--ink-2,#555);flex-shrink:0}
.kb-info-price .pi svg{width:17px;height:17px}
.kb-info-price .pm{flex:1}
.kb-info-price .pm b{font-weight:700;font-size:13px}
.kb-info-price .pm .d{font-size:11px;color:var(--ink-3,#999);margin-top:1px;line-height:1.4}
.kb-info-price .amt{font-size:11px;font-weight:700;color:var(--ink-3,#999);background:var(--bg,#f4f4f0);border-radius:7px;padding:4px 9px;white-space:nowrap}
.kb-info-tbd{display:flex;align-items:flex-start;gap:8px;background:#fffaeb;color:#b54708;border:1px solid #fde68a;border-radius:8px;padding:9px 12px;font-size:11.5px;font-weight:600;margin-top:12px;line-height:1.5}
.kb-info-foot{display:flex;justify-content:flex-end;padding:0 24px 22px}
`,document.head.appendChild(e),na=Zi("info")}function qn(e,n){return`<li><span class="ck">${Ke("check")}</span><span>${K(z(e,n))}</span></li>`}function Aa(e,n,a,s,o,i,r){return`<div class="row"><div class="pi">${e}</div>
        <div class="pm"><b>${K(z(n,a))}</b><div class="d">${K(z(s,o))}</div></div>
        <span class="amt">${K(z(i,r))}</span></div>`}function Gp(){const e=na?.modal;e&&(e.innerHTML=`
        <div class="kb-info-head">
            <span class="ic"><img src="${kt}" alt=""></span>
            <div>
                <h2>${K(z("kb-info-title","客户知识助手是什么"))}</h2>
                <div class="lead">${K(z("kb-info-lead","把每家客户的合同与规矩，变成系统记得住、能自动执行、还能随时问的「活资料」。"))}</div>
            </div>
            <button class="x" data-kb-info-close aria-label="close">${Ke("x")}</button>
        </div>
        <div class="kb-info-body">
            <div class="kb-info-h"><span class="l"></span>${K(z("kb-info-use-h","它真正帮你省什么"))}</div>
            <ul class="kb-info-use">
                ${qn("kb-info-use1","把客户的合同、采购政策、内部规矩上传一次，AI 读懂后建成可检索的资料库 —— 不用再翻文件夹找合同。")}
                ${qn("kb-info-use2","做账时 AI 自动按这家客户的规矩检查发票：金额超上限、供应商要不要人工复核、差旅超标…… 异常当场标出来。")}
                ${qn("kb-info-use3","任意页面右下角随手问「这家客户能不能这样报」，答案都带合同原文出处，点一下就能核对，AI 不瞎编。")}
                ${qn("kb-info-use4","把老会计脑子里记的客户规矩，变成系统记住、新人也能直接上手 —— 给多家公司做账的事务所尤其值。")}
            </ul>
            <div class="kb-info-h"><span class="l"></span>${K(z("kb-info-cost-h","费用怎么算"))}</div>
            <p style="font-size:12.5px;color:var(--ink-2,#555);margin:0 0 11px;line-height:1.55">${K(z("kb-info-cost-lead","从你的泰铢余额按用量扣，不用不花，跟 OCR 共用一个余额池："))}</p>
            <div class="kb-info-price">
                ${Aa(Ke("upload"),"kb-info-c1-n","上传建库","kb-info-c1-d","PDF / 图片按页、文档按字符 —— 跟现在 OCR 同价","kb-info-c1-amt","฿1.50/页起")}
                ${Aa(Ke("message"),"kb-info-c2-n","AI 问答","kb-info-c2-d","每次带合同原文出处的回答","kb-info-c2-amt","฿0.50/次")}
                ${Aa(Ke("shield-check"),"kb-info-c3-n","自动发票检查","kb-info-c3-d","死规则:算术 / 税号 / 查重 / 客户规矩","kb-info-c3-amt","免费")}
            </div>
            <div class="kb-info-tbd"><span>${K(z("kb-info-note","充值与扣费跟现有 OCR 共用同一个泰铢余额；问答按真实成本加合理毛利定价（与 OCR 同档）。"))}</span></div>
        </div>
        <div class="kb-info-foot"><button class="btn btn-primary" data-kb-info-close>${K(z("kb-info-close","知道了"))}</button></div>
    `)}function Wp(){Up(),Gp(),na?.open()}window._kbOpenInfo=Wp;const rr={tax_invoice:"sx-dt-tax_invoice",tax_invoice_receipt:"sx-dt-tax_invoice_receipt",tax_invoice_simple:"sx-dt-tax_invoice_simple",receipt:"sx-dt-receipt",quotation:"sx-dt-quotation",credit_note:"sx-dt-credit_note",debit_note:"sx-dt-debit_note"};function Fs(e){const n=e?rr[e]:null;return n?t(n):e||"—"}function De(e){return Number(e||0).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function zs(e){return e?e.slice(0,10):"—"}function Le(e){return escapeHtml(e==null?"":String(e))}function Kp(){const e={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const n=window._wsHeader&&window._wsHeader();n&&Object.assign(e,n)}catch{}return e}function gt(e,n={}){return fetch(e,{...n,headers:{...Kp(),...n.headers||{}}})}async function lr(e){const n=new FormData;n.append("file",e);try{const a=await gt("/api/uploads/image",{method:"POST",body:n}),s=await a.json().catch(()=>({}));return a.ok&&s.url?{url:String(s.url)}:{error:String(s.detail||"HTTP "+a.status)}}catch{return{error:"network"}}}const Ln='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>',Yp='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 9l5-5 5 5M12 4v12"/></svg>';function gn(e,n,a){const s=a||"";return`<div class="sx-dropwrap">
        <div class="sx-drop${s?" has":""}" id="${e}-drop">
            <input type="file" id="${e}-file" accept="image/png,image/jpeg,image/webp" hidden>
            <input type="hidden" id="${e}" value="${escapeHtml(s)}">
            <img id="${e}-prev" src="${escapeHtml(s)}" alt="" style="${s?"":"display:none"}">
            <span class="sx-drop-lbl" id="${e}-lbl" style="${s?"display:none":""}">${Yp} ${escapeHtml(n)}</span>
            <button type="button" class="sx-drop-clr" id="${e}-clr" style="${s?"":"display:none"}" title="${escapeHtml(t("sx-upload-clear"))}">×</button>
        </div>
        <div class="sx-field-err" id="${e}-err"></div>
    </div>`}function bn(e){const n=document.getElementById(e+"-file"),a=document.getElementById(e+"-drop"),s=document.getElementById(e+"-clr"),o=document.getElementById(e),i=document.getElementById(e+"-prev"),r=document.getElementById(e+"-lbl"),l=document.getElementById(e+"-err");if(!n||!a||!o)return;const m=d=>{o.value=d,i&&(i.src=d,i.style.display=d?"":"none"),r&&(r.style.display=d?"none":""),s&&(s.style.display=d?"":"none"),a.classList.toggle("has",!!d)};a.onclick=d=>{d.target.closest(".sx-drop-clr")||n.click()},n.onchange=async()=>{const d=n.files&&n.files[0];if(!d)return;l&&(l.textContent="");const p=await lr(d);p.url?m(p.url):l&&(l.textContent=t(p.error||"")!==p.error?t(p.error||""):t("sx-upload-fail")),n.value=""},s&&(s.onclick=d=>{d.stopPropagation(),m("")})}const Jp=Object.freeze(Object.defineProperty({__proto__:null,DOC_TYPE_KEY:rr,IC_X:Ln,bindImageField:bn,docTypeLabel:Fs,fmtDate:zs,fmtMoney:De,htmlVal:Le,imageFieldHtml:gn,salesFetch:gt,uploadImage:lr},Symbol.toStringTag,{value:"Module"})),Te={x:Ln,dl:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>',print:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v8H6z"/></svg>',send:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="m22 2-7 20-4-9-9-4Z"/></svg>',ban:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="9"/><path d="m5 5 14 14"/></svg>',undo:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M3 7v6h6M3 13a9 9 0 1 0 3-7.7L3 8"/></svg>',copy:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M9 9h11v11H9zM5 15H4V4h11v1"/></svg>',qr:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM21 14v7M17 21h4"/></svg>'};let ts={},Fo=null;function ze(){return document.getElementById("sales-detail-mask")}function fe(){return document.getElementById("sales-action-mask")}function yt(){ze().style.display="none",ze().innerHTML=""}function xe(){fe().style.display="none",fe().innerHTML=""}async function Xp(){if(!Object.keys(ts).length)try{const e=await apiGet("/api/sales/sellers"),n=e&&(e.sellers||e.items||e)||[];if(Array.isArray(n))for(const a of n)ts[String(a.workspace_client_id??a.id)]=a}catch{}}function Zp(e){const n=ts[String(e.seller_workspace_client_id??"")]||{},a=(e.lines||[]).map((s,o)=>`<tr><td>${o+1}</td><td>${escapeHtml(String(s.description||"—"))}</td><td style="text-align:right">${De(s.amount??Number(s.qty||0)*Number(s.unit_price||0))}</td></tr>`).join("");return`<div class="sx-inv">
        <div class="sx-cb">ต้นฉบับ</div>
        <h4>${escapeHtml(n.name||t("sx-seller"))}</h4>
        <div class="sx-no">${escapeHtml(Fs(e.doc_type))} · ${escapeHtml(e.doc_number||t("sx-draft-tag"))} · ${escapeHtml(zs(e.issue_date))}</div>
        <div class="sx-pp">
            <div><div class="sx-tt">ผู้ขาย / ${escapeHtml(t("sx-seller"))}</div>${escapeHtml(n.name||"—")}<br><span style="color:var(--ink-3)">Tax ID ${escapeHtml(n.tax_id||"—")}</span></div>
            <div><div class="sx-tt">ผู้ซื้อ / ${escapeHtml(t("sx-buyer"))}</div>${escapeHtml(e.buyer&&e.buyer.name||"—")}<br><span style="color:var(--ink-3)">${escapeHtml(e.buyer&&e.buyer.tax_id||"")}</span></div>
        </div>
        <table><thead><tr><th>#</th><th>${escapeHtml(t("sx-col-item"))}</th><th style="text-align:right">${escapeHtml(t("sx-col-amount"))}</th></tr></thead>
            <tbody>${a||'<tr><td colspan="3" style="color:var(--ink-3)">—</td></tr>'}</tbody></table>
        <div class="sx-tot">
            <div class="sx-tr"><span>${escapeHtml(t("sx-subtotal"))}</span><span>${De(e.subtotal)}</span></div>
            <div class="sx-tr"><span>VAT ${De(e.vat_rate)}%</span><span>${De(e.vat_amount)}</span></div>
            ${Number(e.wht_amount||0)?`<div class="sx-tr"><span>WHT</span><span>-${De(e.wht_amount)}</span></div>`:""}
            <div class="sx-tr g"><span>${escapeHtml(t("sx-grand"))}</span><span>฿ ${De(e.grand_total)}</span></div>
        </div>
    </div>`}function Qp(e){const n=e.status==="void",a=e.doc_type==="quotation",s=e.status==="issued"&&(e.payment?.status||"unpaid")!=="paid",o=n?`<span style="color:var(--ink-3)">${escapeHtml(t("sx-voided-note"))}</span>`:`<button class="btn btn-ghost btn-sm" data-act="download">${Te.dl}<span>${escapeHtml(t("sx-download"))}</span></button>
           <button class="btn btn-ghost btn-sm" data-act="print">${Te.print}<span>${escapeHtml(t("sx-print"))}</span></button>
           <button class="btn btn-ghost btn-sm" data-act="send">${Te.send}<span>${escapeHtml(t("sx-send-to"))}</span></button>
           ${s?`<button class="btn btn-accent btn-sm" data-act="promptpay">${Te.qr}<span>${escapeHtml(t("sx-promptpay"))}</span></button>`:""}
           <button class="btn btn-ghost btn-sm" data-act="copy">${Te.copy}<span>${escapeHtml(t("sx-copy"))}</span></button>`,i=n?"":`${a?`<button class="btn btn-ghost btn-sm" data-act="convert">${escapeHtml(t("sx-convert"))}</button>`:""}
           <button class="btn btn-ghost btn-sm" data-act="credit">${Te.undo}<span>${escapeHtml(t("sx-credit"))}</span></button>
           <button class="btn btn-ghost btn-sm" data-act="debit"><span>${escapeHtml(t("sx-debit"))}</span></button>
           <button class="btn btn-danger btn-sm" data-act="void">${Te.ban}<span>${escapeHtml(t("sx-void"))}</span></button>`;ze().innerHTML=`<div class="modal" role="dialog" style="max-width:640px">
        <div class="modal-header">
            <div class="modal-title">${escapeHtml(t("sx-detail-title"))} · ${escapeHtml(e.doc_number||t("sx-draft-tag"))}
                <span class="sx-badge ${escapeHtml(e.status)}" style="margin-left:6px">${escapeHtml(t("sx-st-"+e.status))}</span></div>
            <button class="modal-close" id="sx-detail-close">${Te.x}</button>
        </div>
        <div class="modal-body">
            <div class="sx-detail-acts">${o}</div>
            ${Zp(e)}
            <div class="sx-banner">${escapeHtml(t("sx-archived"))}${e.pdf_sha256?" · sha256 ✓":""}</div>
        </div>
        <div class="modal-footer" style="justify-content:space-between">
            <div style="display:flex;gap:7px;flex-wrap:wrap">${i}</div>
            <button class="btn btn-ghost" id="sx-detail-close2">${escapeHtml(t("sx-close"))}</button>
        </div>
    </div>`,ze().style.display="flex",eu(e)}function eu(e){document.getElementById("sx-detail-close").onclick=yt,document.getElementById("sx-detail-close2").onclick=yt,ze().onclick=n=>{n.target===ze()&&yt()},ze().querySelectorAll("[data-soft]").forEach(n=>n.onclick=()=>showToast(t(n.dataset.soft),"info")),ze().querySelectorAll("[data-act]").forEach(n=>n.onclick=()=>ru(n.dataset.act,e))}async function zo(e,n){try{const a=await gt(`/api/sales/documents/${e.id}/pdf?page=A4&copy=original`);if(!a.ok){showToast(t("sx-pdf-fail"),"error");return}const s=URL.createObjectURL(await a.blob()),o=window.open(s,"_blank");n&&o&&o.addEventListener("load",()=>o.print()),setTimeout(()=>URL.revokeObjectURL(s),6e4)}catch{showToast(t("sx-pdf-fail"),"error")}}async function tu(e){try{const n=await gt(`/api/sales/documents/${e.id}/promptpay-qr`);if(!n.ok){const o=await n.json().catch(()=>({})),i=String(o.detail||"").replace("sales.","");showToast(t("sx-pp-"+i)||t("sx-pp-fail"),"error");return}const a=URL.createObjectURL(await n.blob()),s=Number(e.grand_total||0)-Number(e.payment?.paid_amount||0);fe().innerHTML=`<div class="modal" role="dialog" style="max-width:380px">
            <div class="modal-header"><div class="modal-title">${escapeHtml(t("sx-promptpay"))} · PromptPay</div>
                <button class="modal-close" id="sx-pp-close">${Te.x}</button></div>
            <div class="modal-body" style="text-align:center">
                <div class="sx-qr"><img src="${a}" alt="PromptPay QR"></div>
                <div style="font-weight:700;font-size:16px">฿ ${De(s)}</div>
                <div style="color:var(--ink-3);font-size:12px;margin-top:4px">${escapeHtml(t("sx-pp-scan"))}</div>
            </div></div>`,fe().style.display="flex",document.getElementById("sx-pp-close").onclick=xe,fe().onclick=o=>{o.target===fe()&&xe()},setTimeout(()=>URL.revokeObjectURL(a),12e4)}catch{showToast(t("sx-pp-fail"),"error")}}function No(e,n){const a=n==="credit_note"?t("sx-credit-title"):t("sx-debit-title");fe().innerHTML=`<div class="modal" role="dialog" style="max-width:460px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(a)}</div>
            <button class="modal-close" id="sx-note-close">${Te.x}</button></div>
        <div class="modal-body">
            <div class="sx-banner">${escapeHtml(n==="credit_note"?t("sx-credit-note"):t("sx-debit-note"))}</div>
            <div class="form-row"><label>${escapeHtml(t("sx-reason"))}</label><input type="text" id="sx-note-reason" maxlength="200"></div>
            <div class="form-row"><label>${escapeHtml(t("sx-note-amount"))}</label><input type="number" id="sx-note-amount" min="0" step="0.01" placeholder="0.00"></div>
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-note-cancel">${escapeHtml(t("sx-cancel"))}</button>
            <button class="btn btn-primary" id="sx-note-ok">${escapeHtml(t("sx-note-ok"))}</button>
        </div></div>`,fe().style.display="flex",document.getElementById("sx-note-close").onclick=xe,document.getElementById("sx-note-cancel").onclick=xe,fe().onclick=s=>{s.target===fe()&&xe()},document.getElementById("sx-note-ok").onclick=async()=>{const s=document.getElementById("sx-note-reason").value.trim(),o=Number(document.getElementById("sx-note-amount").value);if(!(o>0)){showToast(t("sx-note-amount-required"),"error");return}await ka(`/api/sales/documents/${e.id}/${n==="credit_note"?"credit-note":"debit-note"}`,{reason:s||a,vat_rate:Number(e.vat_rate||7),wht_rate:0,lines:[{description:s||a,qty:1,unit_price:o,vat_applicable:!0}]})&&(xe(),yt(),showToast(t("sx-done"),"success"),window.dispatchEvent(new CustomEvent("pearnly:sales-changed")))}}function nu(e){fe().innerHTML=`<div class="modal" role="dialog" style="max-width:440px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t("sx-void-title"))}</div>
            <button class="modal-close" id="sx-void-close">${Te.x}</button></div>
        <div class="modal-body"><div class="sx-banner warn">${escapeHtml(t("sx-void-warn"))}</div></div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-void-cancel">${escapeHtml(t("sx-cancel"))}</button>
            <button class="btn btn-danger" id="sx-void-ok">${escapeHtml(t("sx-void"))}</button>
        </div></div>`,fe().style.display="flex",document.getElementById("sx-void-close").onclick=xe,document.getElementById("sx-void-cancel").onclick=xe,fe().onclick=n=>{n.target===fe()&&xe()},document.getElementById("sx-void-ok").onclick=async()=>{await ka(`/api/sales/documents/${e.id}/void`,{})&&(xe(),yt(),showToast(t("sx-done"),"success"),window.dispatchEvent(new CustomEvent("pearnly:sales-changed")))}}async function au(e){await ka(`/api/sales/documents/${e.id}/convert`,{target_doc_type:"tax_invoice"})&&(yt(),showToast(t("sx-converted"),"success"),window.dispatchEvent(new CustomEvent("pearnly:sales-changed")))}async function ka(e,n){try{const a=await apiPost(e,n);if(a&&a.ok)return!0;const s=a?await a.json().catch(()=>({})):{};return showToast(t("sx-action-fail")+(s.detail?" · "+s.detail:""),"error"),!1}catch{return showToast(t("sx-action-fail"),"error"),!1}}let cn="email";function su(e,n,a){return`<div class="sx-seg" style="width:100%">${e.map(s=>`<button type="button" data-${a}="${s[0]}" class="${n===s[0]?"on":""}" style="flex:1">${escapeHtml(s[1])}</button>`).join("")}</div>`}function cr(e){const n=cn==="email"?`<div class="sx-banner" style="margin-top:4px">${escapeHtml(t("sx-send-email-hint"))}</div>
               <div class="form-row" style="margin-top:12px"><label>${escapeHtml(t("sx-send-buyer-email"))}</label><input type="email" id="sx-send-email" placeholder="buyer@example.com"></div>`:`<div class="sx-banner" style="margin-top:4px">${escapeHtml(t("sx-send-line-hint"))}</div>`;fe().innerHTML=`<div class="modal" role="dialog" style="max-width:460px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t("sx-send-to-title"))}</div>
            <button class="modal-close" id="sx-send-close">${Te.x}</button></div>
        <div class="modal-body">
            <div class="form-row"><label>${escapeHtml(t("sx-send-how"))}</label>
                ${su([["email",t("sx-send-opt-email")],["line",t("sx-send-opt-line")]],cn,"ch")}</div>
            ${n}
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-send-cancel">${escapeHtml(t("sx-cancel"))}</button>
            <button class="btn btn-primary" id="sx-send-do">${escapeHtml(cn==="email"?t("sx-send-do"):t("sx-send-genlink"))}</button>
        </div></div>`,fe().style.display="flex",document.getElementById("sx-send-close").onclick=xe,document.getElementById("sx-send-cancel").onclick=xe,fe().onclick=a=>{a.target===fe()&&xe()},fe().querySelectorAll("[data-ch]").forEach(a=>a.onclick=()=>(cn=a.dataset.ch,cr(e))),document.getElementById("sx-send-do").onclick=()=>ou(e)}async function ou(e){if(cn==="email"){const o=document.getElementById("sx-send-email").value.trim();if(!o)return showToast(t("sx-send-email-required"),"error");const i=await apiPost(`/api/sales/documents/${e.id}/send`,{channel:"email",to:o});i&&i.ok?(xe(),showToast(t("sx-send-email-ok"),"success")):showToast(t("sx-send-fail"),"error");return}const n=await apiPost(`/api/sales/documents/${e.id}/send`,{channel:"line"}),a=n?await n.json().catch(()=>({})):{};if(!n||!n.ok||!a.share_url)return showToast(t("sx-send-fail"),"error");const s=String(a.share_url);fe().innerHTML=`<div class="modal" role="dialog" style="max-width:480px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t("sx-send-line-title"))}</div>
            <button class="modal-close" id="sx-link-close">${Te.x}</button></div>
        <div class="modal-body">
            <div class="sx-banner">${escapeHtml(t("sx-send-line-ready"))}</div>
            <div class="form-row" style="margin-top:10px"><input type="text" id="sx-link-url" readonly value="${escapeHtml(s)}"></div>
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-link-done">${escapeHtml(t("sx-close"))}</button>
            <button class="btn btn-primary" id="sx-link-copy">${escapeHtml(t("sx-send-copy"))}</button>
        </div></div>`,document.getElementById("sx-link-close").onclick=xe,document.getElementById("sx-link-done").onclick=xe,document.getElementById("sx-link-copy").onclick=()=>{document.getElementById("sx-link-url").select(),navigator.clipboard?.writeText(s).catch(()=>{}),showToast(t("sx-send-copied"),"success")}}async function iu(e){const n=e,a=(e.lines||[]).map(i=>{const r=i;return{description:(r.description||"").trim(),qty:Number(r.qty||0),unit_price:Number(r.unit_price||0),discount:Number(r.discount||0),vat_applicable:r.vat_applicable!==!1}}).filter(i=>i.description);if(!a.length)return showToast(t("sx-action-fail"),"error");const s={doc_type:e.doc_type,client_id:n.client_id,seller_workspace_client_id:n.seller_workspace_client_id,currency:n.currency||"THB",vat_rate:Number(e.vat_rate||0),wht_rate:Number(e.wht_rate||0),header_discount_amount:Number(n.header_discount_amount||0),header_discount_pct:Number(n.header_discount_pct||0),price_includes_vat:!!e.price_includes_vat,lines:a,buyer:e.buyer&&e.buyer.type?{...e.buyer}:null,payment:null};await ka("/api/sales/documents",s)&&(yt(),showToast(t("sx-copied"),"success"),window.dispatchEvent(new CustomEvent("pearnly:sales-changed")))}function ru(e,n){if(e==="download")return void zo(n,!1);if(e==="print")return void zo(n,!0);if(e==="send")return cr(n);if(e==="promptpay")return void tu(n);if(e==="copy")return void iu(n);if(e==="credit")return No(n,"credit_note");if(e==="debit")return No(n,"debit_note");if(e==="void")return nu(n);if(e==="convert")return void au(n)}window.openSalesDetail=async function(e){ze().innerHTML=`<div class="modal" role="dialog" style="max-width:640px"><div class="modal-body"><div class="sx-state">${escapeHtml(t("sx-loading"))}</div></div></div>`,ze().style.display="flex",await Xp();try{const n=await apiGet(`/api/sales/documents/${e}`);if(!n)return;Fo=n.document,Qp(Fo)}catch{ze().innerHTML=`<div class="modal" role="dialog" style="max-width:480px"><div class="modal-body"><div class="sx-state error">${escapeHtml(t("sx-error"))}</div></div></div>`;const a=ze();a.onclick=s=>{s.target===a&&yt()}}};const lu='<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h5"/></svg>',cu='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="3"/><path d="M19.4 13a7 7 0 0 0 0-2l2-1.5-2-3.5-2.3 1a7 7 0 0 0-1.7-1L15 3H9l-.4 2.5a7 7 0 0 0-1.7 1l-2.3-1-2 3.5L4.6 11a7 7 0 0 0 0 2l-2 1.5 2 3.5 2.3-1a7 7 0 0 0 1.7 1L9 21h6l.4-2.5a7 7 0 0 0 1.7-1l2.3 1 2-3.5-2-1.5Z"/></svg>',du='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg>',pu='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="m9 18 6-6-6-6"/></svg>',uu=["paid","unpaid","partial"];let aa=[],sa="all",Ns="";function dr(e){const n=e.payment&&e.payment.status||"";return uu.indexOf(n)>=0?n:"unpaid"}function pr(e){return e.buyer&&e.buyer.name||"—"}function mu(e){if(!e)return!1;const n=new Date,a=n.getFullYear()+"-"+String(n.getMonth()+1).padStart(2,"0");return e.slice(0,7)===a}function vu(){const e=aa.filter(i=>i.status==="issued"),n=e.filter(i=>mu(i.issue_date)),a=n.reduce((i,r)=>i+Number(r.grand_total||0),0),s=aa.filter(i=>i.status==="draft").length,o=e.filter(i=>dr(i)!=="paid").reduce((i,r)=>i+(Number(r.grand_total||0)-Number(r.payment.paid_amount||0)),0);return{count:n.length,amount:a,drafts:s,due:o}}function fu(){let e=aa;sa!=="all"&&(e=e.filter(a=>a.status===sa));const n=Ns.trim().toLowerCase();return n&&(e=e.filter(a=>(a.doc_number||"").toLowerCase().indexOf(n)>=0||pr(a).toLowerCase().indexOf(n)>=0)),e}function ur(){const e=fu();return e.length?e.map(n=>{const a=dr(n),s=n.doc_number||t("sx-draft-tag");return`<tr class="click" data-doc="${escapeHtml(n.id)}">
                <td><b>${escapeHtml(s)}</b></td>
                <td style="color:var(--ink-3)">${escapeHtml(zs(n.issue_date))}</td>
                <td>${escapeHtml(Fs(n.doc_type))}</td>
                <td>${escapeHtml(pr(n))}</td>
                <td class="r">${De(n.grand_total)}</td>
                <td>${n.status==="issued"?`<span class="sx-badge ${a}">${escapeHtml(t("sx-pay-"+a))}</span>`:"—"}</td>
                <td><span class="sx-badge ${escapeHtml(n.status)}">${escapeHtml(t("sx-st-"+n.status))}</span></td>
                <td class="r"><button class="sx-chev" data-doc="${escapeHtml(n.id)}" aria-label="${escapeHtml(t("sx-detail-title"))}">${pu}</button></td>
            </tr>`}).join(""):`<tr><td colspan="8"><div class="sx-state">${lu}<div>${escapeHtml(t("sx-empty"))}</div></div></td></tr>`}function mr(){const e=vu(),n=["all","draft","issued","void"].map(a=>`<button data-flt="${a}" class="${sa===a?"on":""}">${escapeHtml(t("sx-f-"+a))}</button>`).join("");return`<div class="sx-cards">
        <div class="sx-stat"><div class="sx-l">${escapeHtml(t("sx-card-month"))}</div><div class="sx-v">${e.count} <small>${escapeHtml(t("sx-unit-docs"))}</small></div></div>
        <div class="sx-stat"><div class="sx-l">${escapeHtml(t("sx-card-amount"))}</div><div class="sx-v">฿ ${De(e.amount)}</div></div>
        <div class="sx-stat"><div class="sx-l">${escapeHtml(t("sx-card-draft"))}</div><div class="sx-v">${e.drafts}</div></div>
        <div class="sx-stat"><div class="sx-l">${escapeHtml(t("sx-card-due"))}</div><div class="sx-v warn">฿ ${De(e.due)}</div></div>
    </div>
    <div class="sx-toolbar">
        <div class="sx-seg">${n}</div>
        <div class="sx-search"><input type="text" id="sx-wb-search" value="${escapeHtml(Ns)}" placeholder="${escapeHtml(t("sx-search-ph"))}"></div>
    </div>
    <div class="sx-panel"><table class="sx-tbl">
        <thead><tr>
            <th>${escapeHtml(t("sx-col-no"))}</th><th>${escapeHtml(t("sx-col-date"))}</th>
            <th>${escapeHtml(t("sx-col-type"))}</th><th>${escapeHtml(t("sx-col-client"))}</th>
            <th class="r">${escapeHtml(t("sx-col-amount"))}</th><th>${escapeHtml(t("sx-col-pay"))}</th>
            <th>${escapeHtml(t("sx-col-status"))}</th><th></th>
        </tr></thead>
        <tbody id="sx-wb-tbody">${ur()}</tbody>
    </table></div>`}function hu(){return`<div class="sx-page">
        <div class="sx-head">
            <h2 data-i18n="sx-wb-title">${escapeHtml(t("sx-wb-title"))}</h2>
            
            <div class="sx-actions">
                <button class="btn btn-ghost" id="sx-settings-btn">${cu}<span>${escapeHtml(t("sx-settings"))}</span></button>
                <button class="btn btn-primary" id="sx-new-btn">${du}<span>${escapeHtml(t("sx-new"))}</span></button>
            </div>
        </div>
        <div id="sx-wb-body"></div>
    </div>`}function Un(e){const n=document.getElementById("sx-wb-body");n&&(n.innerHTML=e)}function gu(){const e=document.getElementById("sx-wb-tbody");e&&(e.innerHTML=ur()),vr()}function vr(){document.querySelectorAll("#sx-wb-body [data-doc]").forEach(e=>{e.onclick=n=>{n.stopPropagation(),window.openSalesDetail&&window.openSalesDetail(e.dataset.doc)}})}function fr(){document.querySelectorAll("#sx-wb-body [data-flt]").forEach(n=>{n.onclick=()=>{sa=n.dataset.flt,Un(mr()),fr()}});const e=document.getElementById("sx-wb-search");e&&(e.oninput=()=>{Ns=e.value,gu()}),vr()}function bu(){const e=document.getElementById("sx-new-btn");e&&(e.onclick=()=>window.openSalesWizard?.());const n=document.getElementById("sx-settings-btn");n&&(n.onclick=()=>window.openSalesSettings?.())}async function Os(){Un(`<div class="sx-state">${escapeHtml(t("sx-loading"))}</div>`);try{const e=await apiGet("/api/sales/documents");if(!e)return;aa=e.documents||[],Un(mr()),fr()}catch{Un(`<div class="sx-state error">${escapeHtml(t("sx-error"))}<br><button class="btn btn-ghost" id="sx-retry">${escapeHtml(t("sx-retry"))}</button></div>`);const n=document.getElementById("sx-retry");n&&(n.onclick=()=>Os())}}window.loadSalesWorkbench=function(){const e=document.getElementById("page-sales-invoices");e&&(e.dataset.sxInit!=="1"&&(e.innerHTML=hu(),e.dataset.sxInit="1",bu()),Os())};window.addEventListener("pearnly:sales-changed",()=>{typeof currentRoute<"u"&&currentRoute==="sales-invoices"&&Os()});(function(){const n=document.querySelector(".nav-sales-head"),a=document.querySelector(".nav-sub2");if(!n||!a)return;const s=i=>{a.classList.toggle("show",i),n.classList.toggle("sx-open",i)},o=(location.hash||"").replace(/^#\//,"");(o==="sales-invoices"||o==="sales-account")&&s(!0),n.addEventListener("click",()=>s(!a.classList.contains("show")))})();const yu='<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 8 12 3 3 8l9 5 9-5ZM3 8v8l9 5 9-5V8"/></svg>',wu='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M11 4H4v16h16v-7M18.5 2.5a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>',ku='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>';let oa=[],Vs="";function hr(e){let n=document.getElementById(e);return n||(n=document.createElement("div"),n.id=e,n.className="modal-mask sx-modal-mask",n.style.display="none",document.body.appendChild(n)),n}function Mt(e){const n=document.getElementById(e);n&&(n.style.display="none",n.innerHTML="")}function xu(){const e=Vs.trim().toLowerCase();return e?oa.filter(n=>[n.code,n.name_th,n.name_en,n.name_zh,n.barcode].filter(Boolean).some(a=>a.toLowerCase().indexOf(e)>=0)):oa}function gr(){const e=xu();return e.length?e.map(n=>{const a=n.name_th||n.name_en||n.name_zh||"—";return`<tr>
                <td>${n.image_url?`<img src="${escapeHtml(n.image_url)}" alt="" style="width:34px;height:34px;border-radius:7px;object-fit:cover">`:`<div class="sx-thumb">${yu}</div>`}</td>
                <td style="color:var(--ink-3)">${escapeHtml(n.code||"—")}</td>
                <td><b>${escapeHtml(a)}</b></td>
                <td>${escapeHtml(n.unit||"—")}</td>
                <td class="r">${De(n.unit_price)}</td>
                <td>${n.vat_applicable?'<span class="sx-badge issued">7%</span>':'<span class="sx-badge draft">—</span>'}</td>
                <td class="r"><button class="sx-chev" data-edit="${escapeHtml(n.id)}">${wu}</button><button class="sx-chev" data-del="${escapeHtml(n.id)}">${ku}</button></td>
            </tr>`}).join(""):`<tr><td colspan="7"><div class="sx-state">${escapeHtml(t("sx-empty"))}</div></td></tr>`}function _u(){return`<div class="sx-toolbar">
        <div class="sx-search"><input type="text" id="sx-p-search" value="${escapeHtml(Vs)}" placeholder="${escapeHtml(t("sx-p-search-ph"))}"></div>
        <button class="btn btn-ghost" id="sx-p-import">${escapeHtml(t("sx-p-import"))}</button>
        <button class="btn btn-primary" id="sx-p-add">${escapeHtml(t("sx-p-add"))}</button>
    </div>
    <div class="sx-panel"><table class="sx-tbl">
        <thead><tr>
            <th>${escapeHtml(t("sx-p-col-img"))}</th><th>${escapeHtml(t("sx-p-col-code"))}</th>
            <th>${escapeHtml(t("sx-p-col-name"))}</th><th>${escapeHtml(t("sx-p-col-unit"))}</th>
            <th class="r">${escapeHtml(t("sx-p-col-price"))}</th><th>${escapeHtml(t("sx-p-col-vat"))}</th><th></th>
        </tr></thead>
        <tbody id="sx-p-tbody">${gr()}</tbody>
    </table></div>`}function Pa(e){const n=document.getElementById("sx-p-body");n&&(n.innerHTML=e)}function Eu(){const e=document.getElementById("sx-p-search");e&&(e.oninput=()=>{Vs=e.value;const n=document.getElementById("sx-p-tbody");n&&(n.innerHTML=gr()),Oo()}),document.getElementById("sx-p-add").onclick=()=>br(null),document.getElementById("sx-p-import").onclick=Su,Oo()}function Oo(){document.querySelectorAll("#sx-p-body [data-edit]").forEach(e=>{e.onclick=()=>br(oa.find(n=>n.id===e.dataset.edit)||null)}),document.querySelectorAll("#sx-p-body [data-del]").forEach(e=>{e.onclick=()=>$u(e.dataset.del)})}function br(e){const n=hr("sales-prod-mask");n.innerHTML=`<div class="modal" role="dialog" style="max-width:560px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t(e?"sx-p-edit":"sx-p-new"))}</div>
            <button class="modal-close" id="sx-p-close">${Ln}</button></div>
        <div class="modal-body">
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t("sx-p-f-code"))}</label><input type="text" id="sx-pf-code" value="${Le(e?.code)}" maxlength="100"><div class="sx-field-err" id="sx-pf-code-err"></div></div>
                <div><label>${escapeHtml(t("sx-p-f-barcode"))}</label><input type="text" id="sx-pf-barcode" value="${Le(e?.barcode)}" maxlength="100"></div>
            </div>
            <div class="form-row"><label>${escapeHtml(t("sx-p-f-name-th"))} *</label><input type="text" id="sx-pf-th" value="${Le(e?.name_th)}" maxlength="300"></div>
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t("sx-p-f-name-en"))}</label><input type="text" id="sx-pf-en" value="${Le(e?.name_en)}" maxlength="300"></div>
                <div><label>${escapeHtml(t("sx-p-f-name-zh"))}</label><input type="text" id="sx-pf-zh" value="${Le(e?.name_zh)}" maxlength="300"></div>
            </div>
            <div class="form-row form-row-2col">
                <div><label>${escapeHtml(t("sx-p-f-unit"))}</label><input type="text" id="sx-pf-unit" value="${Le(e?.unit)}" maxlength="50"></div>
                <div><label>${escapeHtml(t("sx-p-f-price"))}</label><input type="number" id="sx-pf-price" value="${e?e.unit_price:""}" min="0" step="0.01"></div>
            </div>
            <div class="form-row"><label style="display:flex;align-items:center;gap:8px;cursor:pointer"><input type="checkbox" id="sx-pf-vat" ${!e||e.vat_applicable?"checked":""} style="width:auto"> ${escapeHtml(t("sx-p-f-vat"))}</label></div>
            <div class="form-row">${gn("sx-pf-image",t("sx-p-f-image"),e?.image_url)}</div>
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-p-cancel">${escapeHtml(t("sx-cancel"))}</button>
            <button class="btn btn-primary" id="sx-p-save">${escapeHtml(t("sx-p-save"))}</button>
        </div></div>`,n.style.display="flex",document.getElementById("sx-p-close").onclick=()=>Mt("sales-prod-mask"),document.getElementById("sx-p-cancel").onclick=()=>Mt("sales-prod-mask"),n.onclick=a=>{a.target===n&&Mt("sales-prod-mask")},document.getElementById("sx-p-save").onclick=()=>Lu(e),bn("sx-pf-image")}function Iu(){const e=n=>document.getElementById(n).value.trim();return{name_th:e("sx-pf-th"),code:e("sx-pf-code")||null,barcode:e("sx-pf-barcode")||null,name_en:e("sx-pf-en")||null,name_zh:e("sx-pf-zh")||null,unit:e("sx-pf-unit")||null,unit_price:Number(e("sx-pf-price"))||0,vat_applicable:document.getElementById("sx-pf-vat").checked,image_url:e("sx-pf-image")||null}}async function Bu(e,n){const a=await e.json().catch(()=>({})),s=a&&a.detail?String(a.detail):"HTTP "+e.status;return t(n)+" · "+s}function Vo(e){const n=document.getElementById("sx-pf-code-err");n&&(n.textContent=e)}async function Lu(e){const n=Iu();if(Vo(""),!n.name_th)return showToast(t("sx-p-name-required"),"error");const a=e?`/api/sales/products/${e.id}`:"/api/sales/products";try{const s=await gt(a,{method:e?"PATCH":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});if(!s.ok){const o=await s.json().catch(()=>({})),i=o&&o.detail?String(o.detail):"HTTP "+s.status;if(i==="sales.product_code_exists"){Vo(t("sales.product_code_exists")),document.getElementById("sx-pf-code")?.focus();return}showToast(t("sx-p-save-fail")+" · "+i,"error");return}Mt("sales-prod-mask"),showToast(t("sx-p-saved"),"success"),await $n()}catch{showToast(t("sx-p-save-fail"),"error")}}async function $u(e){if(window.pearnlyConfirm){if(!await window.pearnlyConfirm(t("sx-p-del-confirm")))return}else if(!confirm(t("sx-p-del-confirm")))return;try{const n=await gt(`/api/sales/products/${e}`,{method:"DELETE"});if(!n.ok){showToast(await Bu(n,"sx-p-del-fail"),"error");return}showToast(t("sx-p-deleted"),"success"),await $n()}catch{showToast(t("sx-p-del-fail"),"error")}}function Su(){const e=hr("sales-prod-mask");e.innerHTML=`<div class="modal" role="dialog" style="max-width:480px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t("sx-p-import-title"))}</div>
            <button class="modal-close" id="sx-imp-close">${Ln}</button></div>
        <div class="modal-body">
            <input type="file" id="sx-imp-file" accept=".xlsx,.xls" style="width:100%">
            <div class="sx-banner" style="margin-top:10px">${escapeHtml(t("sx-p-import-hint"))}</div>
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sx-imp-cancel">${escapeHtml(t("sx-cancel"))}</button>
            <button class="btn btn-primary" id="sx-imp-go">${escapeHtml(t("sx-p-import-go"))}</button>
        </div></div>`,e.style.display="flex",document.getElementById("sx-imp-close").onclick=()=>Mt("sales-prod-mask"),document.getElementById("sx-imp-cancel").onclick=()=>Mt("sales-prod-mask"),document.getElementById("sx-imp-go").onclick=Cu}async function Cu(){const e=document.getElementById("sx-imp-file").files?.[0];if(!e)return showToast(t("sx-p-import-pick"),"error");const n=new FormData;n.append("file",e);try{const a=await gt("/api/sales/products/import",{method:"POST",body:n}),s=await a.json().catch(()=>({}));if(!a.ok)throw new Error;Mt("sales-prod-mask"),showToast(t("sx-p-import-done").replace("{n}",String(s.imported??0)),"success"),await $n()}catch{showToast(t("sx-p-import-fail"),"error")}}async function $n(){Pa(`<div class="sx-state">${escapeHtml(t("sx-loading"))}</div>`);try{const e=await apiGet("/api/sales/products");if(!e)return;oa=e.products||[],Pa(_u()),Eu()}catch{Pa(`<div class="sx-state error">${escapeHtml(t("sx-error"))}<br><button class="btn btn-ghost" id="sx-p-retry">${escapeHtml(t("sx-retry"))}</button></div>`);const n=document.getElementById("sx-p-retry");n&&(n.onclick=()=>$n())}}window.loadSalesProducts=function(){const e=document.getElementById("page-sales-products");e&&(e.dataset.sxInit!=="1"&&(e.innerHTML=`<div class="sx-page"><div class="sx-head"><h2>${escapeHtml(t("nav-sales-products"))}</h2></div><div id="sx-p-body"></div></div>`,e.dataset.sxInit="1"),$n())};const Tu=["classic","clean","brand","compact","official","mono"],Hu=["#2563eb","#0f766e","#b45309","#7c3aed","#be123c","#111827"];let Us=[],xa=0,Ge="classic",Pt="#2563eb";function Sn(){return Us[xa]}function Mu(){const e=Sn();if(!e)return`<div class="sx-state">${escapeHtml(t("sx-acc-none"))}</div>`;const n=Us.map((o,i)=>`<option value="${i}" ${i===xa?"selected":""}>${escapeHtml(o.name||"—")}</option>`).join(""),a=Tu.map(o=>{const i=o==="brand"||o==="official"?Pt:"#111827",r=o==="brand"?`<div class="sx-tpl-bar" style="background:${i}"></div>`:"";return`<div class="sx-tpl ${Ge===o?"on":""}" data-tpl="${o}"><div class="sx-tpl-pv">${r}<div class="sx-tpl-co" style="color:${i};${o==="official"?"text-align:center;":""}">บริษัท ตัวอย่าง</div><div class="sx-tpl-ln">รายการ … 1,000</div><div class="sx-tpl-tt">รวม 1,070</div></div><div class="sx-tpl-nm">${escapeHtml(t("sx-acc-tpl-"+o))}</div></div>`}).join(""),s=Hu.map(o=>`<span class="sx-sw ${Pt===o?"on":""}" data-color="${o}" style="background:${o}"></span>`).join("");return`<div class="sx-acc-2col">
      <div class="sx-acc-form">
        <div class="sx-field"><label>${escapeHtml(t("sx-acc-pick"))}</label><select id="sx-acc-sel">${n}</select></div>
        <div class="sx-acc-grid">
            <div class="sx-field"><label>${escapeHtml(t("sx-acc-name"))}</label><input type="text" id="sx-a-name" value="${Le(e.name)}" maxlength="200"></div>
            <div class="sx-field"><label>${escapeHtml(t("sx-acc-tax"))}</label><input type="text" id="sx-a-tax" value="${Le(e.tax_id)}" maxlength="20"></div>
        </div>
        <div class="sx-field"><label>${escapeHtml(t("sx-acc-address"))}</label><input type="text" id="sx-a-addr" value="${Le(e.address)}" maxlength="500"></div>
        <div class="sx-acc-grid">
            <div class="sx-field"><label>${escapeHtml(t("sx-acc-branch"))}</label><input type="text" id="sx-a-branch" value="${Le(e.branch)}" maxlength="120"></div>
            <div class="sx-field"><label>${escapeHtml(t("sx-acc-phone"))}</label><input type="text" id="sx-a-phone" value="${Le(e.phone)}" maxlength="50"></div>
        </div>
        <div class="sx-field"><label>${escapeHtml(t("sx-acc-promptpay"))}</label><input type="text" id="sx-a-pp" value="${Le(e.promptpay_id)}" maxlength="40" placeholder="08x-xxx-xxxx / ${escapeHtml(t("sx-acc-tax"))}"></div>

        <div class="sx-head" style="margin-top:18px"><h2 style="font-size:14px">${escapeHtml(t("sx-acc-sec-brand"))}</h2></div>
        <div class="sx-acc-assets">
            ${gn("sx-a-logo",t("sx-acc-logo"),e.logo_url)}
            ${gn("sx-a-seal",t("sx-acc-seal"),e.seal_url)}
            ${gn("sx-a-sign",t("sx-acc-sign"),e.signature_url)}
        </div>
        <div class="sx-field"><label>${escapeHtml(t("sx-acc-footer"))}</label><textarea id="sx-a-footer" rows="2" maxlength="500">${Le(e.footer_text)}</textarea></div>

        <div class="sx-head" style="margin-top:18px"><h2 style="font-size:14px">${escapeHtml(t("sx-acc-sec-template"))}</h2></div>
        <div class="sx-tpls">${a}</div>
        <div class="sx-head" style="margin-top:14px"><h2 style="font-size:14px">${escapeHtml(t("sx-acc-sec-color"))}</h2></div>
        <div style="display:flex;gap:10px">${s}</div>

        <button class="btn btn-primary" id="sx-a-save" style="margin-top:18px">${escapeHtml(t("sx-acc-save"))}</button>
      </div>
      <div class="sx-acc-preview-col">
        <div class="sx-set-h">${escapeHtml(t("sx-acc-preview"))}</div>
        <div id="sx-acc-prev">${yr()}</div>
      </div>
    </div>`}function yr(){const e=Sn();if(!e)return"";const n=Ge==="brand"||Ge==="official"?Pt:"#111827",a=Ge==="brand"?`<div style="height:7px;background:${n};margin:-18px -18px 12px;border-radius:8px 8px 0 0"></div>`:"";return`<div class="sx-prev-inv sx-prev-${Ge}" style="${Ge==="brand"?"border-color:"+n+"55":""}">
        ${a}
        <div class="sx-prev-co" style="color:${n};${Ge==="official"?"text-align:center":""}">${escapeHtml(e.name||"—")}</div>
        <div class="sx-prev-sub">${escapeHtml(t("sx-dt-tax_invoice"))} · INV2026-00001 · 2026-06-06</div>
        <div class="sx-prev-parties">
            <div><b>${escapeHtml(t("sx-seller"))}</b><br>${escapeHtml(e.name||"—")}<br><span class="sx-prev-mut">Tax ID ${escapeHtml(e.tax_id||"—")} · ${escapeHtml(e.branch||"")}</span></div>
            <div><b>${escapeHtml(t("sx-buyer"))}</b><br>—</div>
        </div>
        <div class="sx-prev-row"><span>1 · รายการตัวอย่าง</span><span>1,000.00</span></div>
        <div class="sx-prev-row sx-prev-vat"><span>VAT 7%</span><span>70.00</span></div>
        <div class="sx-prev-tot"><span>${escapeHtml(t("sx-grand"))}</span><span>฿ 1,070.00</span></div>
        ${e.footer_text?`<div class="sx-prev-foot">${escapeHtml(e.footer_text)}</div>`:""}
    </div>`}function ja(){const e=document.getElementById("sx-acc-prev");e&&(e.innerHTML=yr())}function Au(){const e=document.getElementById("sx-acc-body");e&&(e.innerHTML=Mu(),Pu())}function wr(e){xa=e;const n=Sn();Ge=n&&n.template_id||"classic",Pt=n&&n.brand_color||"#2563eb",Au()}function Pu(){const e=document.getElementById("sx-acc-sel");e&&(e.onchange=()=>wr(+e.value)),document.querySelectorAll("[data-tpl]").forEach(s=>{s.onclick=()=>{Ge=s.dataset.tpl,document.querySelectorAll("[data-tpl]").forEach(o=>o.classList.toggle("on",o.dataset.tpl===Ge)),ja()}}),document.querySelectorAll("[data-color]").forEach(s=>{s.onclick=()=>{Pt=s.dataset.color,document.querySelectorAll("[data-color]").forEach(o=>o.classList.toggle("on",o.dataset.color===Pt)),ja()}}),[["sx-a-name",s=>Rn().name=s],["sx-a-tax",s=>Rn().tax_id=s],["sx-a-branch",s=>Rn().branch=s],["sx-a-footer",s=>Rn().footer_text=s]].forEach(([s,o])=>{const i=document.getElementById(s);i&&(i.oninput=()=>{o(i.value),ja()})}),bn("sx-a-logo"),bn("sx-a-seal"),bn("sx-a-sign");const a=document.getElementById("sx-a-save");a&&(a.onclick=ju)}function Rn(){return Sn()}async function ju(){const e=Sn();if(!e)return;const n=s=>document.getElementById(s).value.trim(),a={name:n("sx-a-name"),tax_id:n("sx-a-tax")||null,address:n("sx-a-addr")||null,branch:n("sx-a-branch")||null,phone:n("sx-a-phone")||null,promptpay_id:n("sx-a-pp")||null,logo_url:n("sx-a-logo")||null,seal_url:n("sx-a-seal")||null,signature_url:n("sx-a-sign")||null,footer_text:document.getElementById("sx-a-footer").value.trim()||null,template_id:Ge,brand_color:Pt};try{if(!(await gt(`/api/sales/sellers/${e.id}`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)})).ok)throw new Error;Object.assign(e,a),showToast(t("sx-acc-saved"),"success")}catch{showToast(t("sx-acc-save-fail"),"error")}}async function kr(){const e=document.getElementById("sx-acc-body");e&&(e.innerHTML=`<div class="sx-state">${escapeHtml(t("sx-loading"))}</div>`);try{const n=await apiGet("/api/sales/sellers");if(!n)return;Us=n.sellers||[],xa=0,wr(0)}catch{e&&(e.innerHTML=`<div class="sx-state error">${escapeHtml(t("sx-error"))}<br><button class="btn btn-ghost" id="sx-acc-retry">${escapeHtml(t("sx-retry"))}</button></div>`);const a=document.getElementById("sx-acc-retry");a&&(a.onclick=()=>kr())}}window.loadSalesAccount=function(){const e=document.getElementById("page-sales-account");e&&(e.dataset.sxInit!=="1"&&(e.innerHTML=`<div class="sx-page"><div class="sx-head"><h2>${escapeHtml(t("nav-sales-account"))}</h2></div><div id="sx-acc-body" style="max-width:1040px"></div></div>`,e.dataset.sxInit="1"),kr())};const Uo=[["0","sx-wht-none"],["1","sx-wht-transport"],["2","sx-wht-ad"],["3","sx-wht-service"],["5","sx-wht-rent"]];let ve;function et(){let e=document.getElementById("sales-settings-mask");return e||(e=document.createElement("div"),e.id="sales-settings-mask",e.className="modal-mask sx-modal-mask",e.style.display="none",document.body.appendChild(e)),e}function ia(){const e=document.getElementById("sales-settings-mask");e&&(e.style.display="none",e.innerHTML="")}function on(e,n,a=!1){return`<div class="sx-seg" data-seg="${String(e)}"${a?' style="width:100%"':""}>${n.map(s=>`<button type="button" data-seg-v="${s[0]}" class="${String(ve[e])===s[0]?"on":""}"${a?' style="flex:1"':""}>${escapeHtml(s[1])}</button>`).join("")}</div>`}function xr(){const e=ve.number_prefix||"INV",n=new Date().getFullYear();return`${escapeHtml(e)}${n}-00001`}function Du(){const e=String(Number(ve.default_wht_rate)||0),n=Uo.some(s=>s[0]===e),a=Uo.map(([s,o])=>`<option value="${s}" ${e===s?"selected":""}>${s}% ${escapeHtml(t(o))}</option>`).join("")+`<option value="custom" ${n?"":"selected"}>${escapeHtml(t("sx-wht-custom"))}</option>`;et().innerHTML=`<div class="modal" role="dialog" style="max-width:720px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(t("sx-set-title"))}</div>
            <button class="modal-close" id="sx-set-close">${Ln}</button></div>
        <div class="modal-body">
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t("sx-set-num"))}</div>
                <div class="sx-set-row3">
                    <div class="sx-field"><label>${escapeHtml(t("sx-set-prefix"))}</label><input type="text" id="sx-set-prefix" value="${escapeHtml(ve.number_prefix||"")}" maxlength="20" placeholder="INV"></div>
                    <div class="sx-field"><label>${escapeHtml(t("sx-set-reset"))}</label>${on("number_reset",[["yearly",t("sx-set-reset-yearly")],["monthly",t("sx-set-reset-monthly")],["never",t("sx-set-reset-never")]],!0)}</div>
                    <div class="sx-field"><label>${escapeHtml(t("sx-set-start"))}</label><input type="number" id="sx-set-start" value="${ve.number_start||1}" min="1"></div>
                </div>
                <div class="sx-hint">${escapeHtml(t("sx-set-num-preview"))}: <b id="sx-set-preview">${xr()}</b> · ${escapeHtml(t("sx-set-num-preview-note"))}</div>
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t("sx-set-approval"))}</div>
                ${on("approval_mode",[["none",t("sx-set-appr-none")],["single",t("sx-set-appr-single")]])}
                <div class="sx-hint">${escapeHtml(t("sx-set-appr-hint"))}</div>
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t("sx-set-vat"))}</div>
                ${on("price_includes_vat_default",[["false",t("sx-set-vat-ex")],["true",t("sx-set-vat-in")]])}
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t("sx-set-wht"))}</div>
                <select id="sx-set-wht" style="width:100%">${a}</select>
                <input type="number" id="sx-set-wht-custom" min="0" max="100" step="0.5" value="${n?"":Number(ve.default_wht_rate)||0}" placeholder="%" style="width:120px;margin-top:8px;${n?"display:none":""}">
                <div class="sx-hint">${escapeHtml(t("sx-set-wht-hint"))}</div>
            </div>
            <div class="sx-set-card">
                <div class="sx-set-h">${escapeHtml(t("sx-set-output"))}</div>
                <div class="sx-acc-grid">
                    <div class="sx-field"><label>${escapeHtml(t("sx-set-lang"))}</label>${on("default_doc_lang",[["th",t("sx-set-lang-th")],["th_en",t("sx-set-lang-then")],["th_zh",t("sx-set-lang-thzh")]],!0)}</div>
                    <div class="sx-field"><label>${escapeHtml(t("sx-set-paper"))}</label>${on("default_paper",[["A4","A4"],["A5","A5"],["80mm","80mm"]],!0)}</div>
                </div>
                <label style="display:flex;align-items:center;gap:8px;margin-top:8px;cursor:pointer"><input type="checkbox" id="sx-set-2up" ${ve.default_copies_layout==="two_up"?"checked":""} style="width:auto"> ${escapeHtml(t("sx-set-copies-2up"))}</label>
            </div>
        </div>
        <div class="modal-footer" style="justify-content:space-between">
            <span class="sx-hint">${escapeHtml(t("sx-set-note"))}</span>
            <button class="btn btn-primary" id="sx-set-save">${escapeHtml(t("sx-set-save"))}</button>
        </div></div>`,et().style.display="flex",qu()}function qu(){document.getElementById("sx-set-close").onclick=ia,et().onclick=o=>{o.target===et()&&ia()},et().querySelectorAll("[data-seg]").forEach(o=>{const i=o.dataset.seg;o.querySelectorAll("[data-seg-v]").forEach(r=>{r.onclick=()=>{const l=r.dataset.segV;ve[i]=i==="price_includes_vat_default"?l==="true":l,o.querySelectorAll("[data-seg-v]").forEach(m=>m.classList.toggle("on",m.dataset.segV===l))}})});const e=document.getElementById("sx-set-prefix");e&&(e.oninput=()=>{ve.number_prefix=e.value;const o=document.getElementById("sx-set-preview");o&&(o.textContent=xr())});const n=document.getElementById("sx-set-wht"),a=document.getElementById("sx-set-wht-custom");n&&(n.onchange=()=>{const o=n.value==="custom";a&&(a.style.display=o?"":"none"),ve.default_wht_rate=o?Number(a?.value)||0:n.value}),a&&(a.oninput=()=>ve.default_wht_rate=Number(a.value)||0);const s=document.getElementById("sx-set-2up");s&&(s.onchange=()=>ve.default_copies_layout=s.checked?"two_up":"separate"),document.getElementById("sx-set-save").onclick=Ru}async function Ru(){const e={number_prefix:document.getElementById("sx-set-prefix").value.trim()||null,number_reset:ve.number_reset,number_start:Number(document.getElementById("sx-set-start").value)||1,approval_mode:ve.approval_mode,price_includes_vat_default:ve.price_includes_vat_default,default_wht_rate:Number(ve.default_wht_rate)||0,default_doc_lang:ve.default_doc_lang,default_paper:ve.default_paper,default_copies_layout:ve.default_copies_layout};try{if(!(await gt("/api/sales/settings",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)})).ok)throw new Error;ia(),showToast(t("sx-set-saved"),"success")}catch{showToast(t("sx-set-save-fail"),"error")}}window.openSalesSettings=async function(){et().innerHTML=`<div class="modal" role="dialog" style="max-width:560px"><div class="modal-body"><div class="sx-state">${escapeHtml(t("sx-loading"))}</div></div></div>`,et().style.display="flex";try{const e=await apiGet("/api/sales/settings");if(!e)return;ve=e.settings,Du()}catch{et().innerHTML=`<div class="modal" role="dialog" style="max-width:480px"><div class="modal-body"><div class="sx-state error">${escapeHtml(t("sx-error"))}</div></div></div>`,et().onclick=n=>{n.target===et()&&ia()}}};const Fu=["tax_invoice","tax_invoice_receipt"],zu=["receipt","tax_invoice_receipt"];function Gn(e){return zu.includes(e.docType)}function Gs(e){return e.docType!=="quotation"}function be(e){return(Math.round(e*100)/100).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function _a(e){let n=0,a=0;e.lines.forEach(d=>{const p=Math.max(0,(+d.qty||0)*(+d.price||0)-(+d.disc||0));n+=p,d.vat&&(a+=p)});const s=Math.min(+e.hdisc||0,n),o=n>0?(n-s)/n:1;a*=o;const i=n-s,r=a*(+e.vatRate||0)/100,l=i*(+e.whtRate||0)/100,m=i+r-l;return{sub:n,hd:s,subAfter:i,vat:r,wht:l,grand:m}}function Nu(e){const n=["","หนึ่ง","สอง","สาม","สี่","ห้า","หก","เจ็ด","แปด","เก้า"],a=["","สิบ","ร้อย","พัน","หมื่น","แสน"];let s="";const o=e.length;for(let i=0;i<o;i++){const r=+e[i],l=o-1-i;r!==0&&(l===1&&r===1?s+="สิบ":l===1&&r===2?s+="ยี่สิบ":l===0&&r===1&&o>1?s+="เอ็ด":s+=n[r]+a[l])}return s}function Go(e){if(e===0)return"ศูนย์";const n=[];let a=String(e);for(;a.length>6;)n.unshift(a.slice(-6)),a=a.slice(0,-6);n.unshift(a);let s="";return n.forEach((o,i)=>{const r=+o;if(r===0)return;s+=Nu(String(r));const l=n.length-1-i;for(let m=0;m<l;m++)s+="ล้าน"}),s}function Ou(e){e=Math.round(e*100)/100;const n=Math.floor(e),a=Math.round((e-n)*100);let s=Go(n)+"บาท";return s+=a===0?"ถ้วน":Go(a)+"สตางค์",s}function Vu(e){e=Math.round(e*100)/100;const n=Math.floor(e),a=Math.round((e-n)*100),s=["零","壹","贰","叁","肆","伍","陆","柒","捌","玖"],o=["","拾","佰","仟"],i=["","万","亿"],r=d=>{let p="";const c=String(d);for(let u=0;u<c.length;u++){const v=+c[u],f=c.length-1-u;v===0?!p.endsWith("零")&&p&&(p+="零"):p+=s[v]+o[f]}return p.replace(/零+$/,"")};let m=(d=>{if(d===0)return"零";const p=[];let c=String(d);for(;c.length>4;)p.unshift(c.slice(-4)),c=c.slice(0,-4);p.unshift(c);let u="";return p.forEach((v,f)=>{const y=+v,b=p.length-1-f;y!==0?u+=r(y)+i[b]:u&&!u.endsWith("零")&&(u+="零")}),u.replace(/零+$/,"")})(n)+"泰铢";return m+=a===0?"整":s[Math.floor(a/10)]+"角"+(a%10?s[a%10]+"分":""),m}function _r(e){const n=e.buyer,a=Fu.includes(e.docType),s=n.type==="anonymous",o=a?!s&&!!(n.name&&n.addr&&n.tin&&(n.type!=="company"||n.branchType==="hq"||/^\d{5}$/.test(n.branchNo))):!0;let i=!0;["company","individual"].includes(n.type)&&n.tin&&(i=/^\d{13}$/.test(n.tin)),n.type==="foreigner"&&n.tin&&(i=/^[A-Za-z0-9]{4,20}$/.test(n.tin));const r=!Gn(e)||e.pay.status!=="unpaid",l=a||e.docType==="tax_invoice_simple";return[{key:"ckBuyer",descKey:"ckBuyerD",pass:o,req:a,na:!a},{key:"ckTin",descKey:"ckTinD",pass:i,req:a,na:e.docType==="quotation"},{key:"ckVat",descKey:"ckVatD",pass:!0,req:l,na:!l},{key:"ckPay",descKey:"ckPayD",pass:r,req:Gn(e),na:!Gn(e)},{key:"ckSeq",descKey:"ckSeqD",pass:!0,req:!0,na:!1},{key:"ckWords",descKey:"ckWordsD",pass:!0,req:l,na:!l}]}const Uu="modulepreload",Gu=function(e){return"/"+e},Wo={},Wu=function(n,a,s){let o=Promise.resolve();if(a&&a.length>0){let r=function(d){return Promise.all(d.map(p=>Promise.resolve(p).then(c=>({status:"fulfilled",value:c}),c=>({status:"rejected",reason:c}))))};document.getElementsByTagName("link");const l=document.querySelector("meta[property=csp-nonce]"),m=l?.nonce||l?.getAttribute("nonce");o=r(a.map(d=>{if(d=Gu(d),d in Wo)return;Wo[d]=!0;const p=d.endsWith(".css"),c=p?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${d}"]${c}`))return;const u=document.createElement("link");if(u.rel=p?"stylesheet":Uu,p||(u.as="script"),u.crossOrigin="",u.href=d,m&&u.setAttribute("nonce",m),document.head.appendChild(u),p)return new Promise((v,f)=>{u.addEventListener("load",v),u.addEventListener("error",()=>f(new Error(`Unable to preload CSS for ${d}`)))})}))}function i(r){const l=new Event("vite:preloadError",{cancelable:!0});if(l.payload=r,window.dispatchEvent(l),!l.defaultPrevented)throw r}return o.then(r=>{for(const l of r||[])l.status==="rejected"&&i(l.reason);return n().catch(i)})};let Ws=[],Er=[];function Ir(){return Ws}function Br(){return Er}async function Ku(){const[e,n]=await Promise.all([apiGet("/api/sales/sellers").catch(()=>null),apiGet("/api/sales/products").catch(()=>null)]);Ws=e&&e.sellers||[],Er=n&&n.products||[]}async function Yu(e){const n=await apiPost("/api/rd/verify",{tax_id:e});return!n||!n.ok?{valid:!1}:{valid:!!(await n.json().catch(()=>({}))).valid}}async function Ju(e,n=0){const a=await apiPost("/api/rd/lookup",{tax_id:e,branch:n});if(!a||!a.ok)return{found:!1};const s=await a.json().catch(()=>({}));return{found:!!(s.found||s.name),name:s.name||s.company_name,address:s.address||s.full_address,branch_no:s.branch_no||s.branch}}function Xu(e){const n=Ws[e.sellerIdx],a=_a(e),s=e.lines.filter(i=>(i.desc||"").trim()).map(i=>({description:i.desc.trim(),product_id:i.product_id||null,qty:+i.qty||0,unit_price:+i.price||0,discount:+i.disc||0,vat_applicable:!!i.vat}));let o=null;if(Gs(e)){const i=e.pay.status==="paid"?a.grand:e.pay.status==="partial"?+(e.pay.paidAmt||0):0;o={status:e.pay.status,paid_amount:i,method:e.pay.method,date:e.pay.date}}return{doc_type:e.docType,seller_workspace_client_id:n?n.id:null,currency:"THB",vat_rate:+e.vatRate||0,wht_rate:+e.whtRate||0,header_discount_amount:+e.hdisc||0,header_discount_pct:0,price_includes_vat:!1,due_date:e.docType==="tax_invoice"&&e.dueDate?e.dueDate:null,lines:s,buyer:{type:e.buyer.type,name:e.buyer.name||null,address:e.buyer.addr||null,tax_id:e.buyer.tin||null,branch_type:e.buyer.type==="company"?e.buyer.branchType:null,branch_no:e.buyer.branchType==="branch"?e.buyer.branchNo:null},payment:o}}async function ns(e){if(!e)return{ok:!1,error:"network"};const n=await e.json().catch(()=>({}));return e.ok?{ok:!0,id:n.document&&String(n.document.id)}:{ok:!1,error:n.detail||"http_"+e.status}}async function Lr(e){const n=Xu(e);if(e.draftId){const{salesFetch:a}=await Wu(async()=>{const{salesFetch:o}=await Promise.resolve().then(()=>Jp);return{salesFetch:o}},void 0),s=await a(`/api/sales/documents/${e.draftId}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(n)});return ns(s)}return ns(await apiPost("/api/sales/documents",n))}async function Zu(e){const n=await Lr(e);if(!n.ok||!n.id)return n;const a=await apiPost(`/api/sales/documents/${n.id}/issue`,{issue_date:e.issueDate||null}),s=await ns(a);return s.ok?{ok:!0,id:n.id}:s}const Qu={steps:["ประเภทเอกสาร","ผู้ขาย/ผู้ซื้อ","รายการสินค้า","รับชำระ / วันที่","ตรวจ & ออก"],sc:[["ขายปลีกรับเงินสด","รวม · ลูกค้าบุคคลจ่ายสด"],["ขายเชื่อ B2B","ใบกำกับ · นิติบุคคล · เครดิต"],["บุคคลขอลดหย่อน","รวม · บุคคล+เลขบัตร"],["POS แบบย่อ","อย่างย่อ · ไม่ระบุชื่อ"]],docTypes:[["tax_invoice_receipt","ใบกำกับภาษี/ใบเสร็จรับเงิน","พบบ่อยสุด รับเงินแล้วออกทันที"],["tax_invoice","ใบกำกับภาษี (ขายเชื่อ)","ออกก่อน รับเงินทีหลัง"],["tax_invoice_simple","ใบกำกับภาษีอย่างย่อ","ขายปลีก ผู้ซื้อขอคืนภาษีไม่ได้"],["receipt","ใบเสร็จรับเงิน","หลักฐานรับเงิน"],["quotation","ใบเสนอราคา","ไม่ใช่เอกสารภาษี"]],bt:[["company","นิติบุคคล","ขอคืนภาษีซื้อได้"],["individual","บุคคลธรรมดา","คนไทย"],["foreigner","ชาวต่างชาติ","ใช้พาสปอร์ต"],["anonymous","ลูกค้าทั่วไป","ไม่ระบุ"]],methods:[["cash","เงินสด"],["transfer","โอน"],["promptpay","พร้อมเพย์"],["card","บัตร"],["cheque","เช็ค"]],s:{title:"ออกใบกำกับภาษี",sub:"· ใบกำกับขาย",back:"ย้อนกลับ",next:"ถัดไป",draft:"บันทึกร่าง",issue:"ออกใบกำกับภาษี",s1h:"เลือกประเภทเอกสาร",s1sub:"แต่ละประเภทจะให้กรอกข้อมูลต่างกัน เลือกสถานการณ์เพื่อตั้งค่าอัตโนมัติได้",scenarios:"สถานการณ์ที่พบบ่อย (กดเพื่อตั้งค่า)",orManual:"หรือเลือกประเภทเอง",s2h:"ผู้ขาย / ผู้ซื้อ",s2sub:"ผู้ขายดึงจากกิจการที่เลือก ผู้ซื้อปรับช่องตามประเภทอัตโนมัติ",seller:"ผู้ขาย (กิจการ)",sellerPick:"เลือกกิจการที่ออกบิล",buyer:"ผู้ซื้อ",buyerType:"ประเภทผู้ซื้อ",name:"ชื่อ",addr:"ที่อยู่",tin:"เลขผู้เสียภาษี",natid:"เลขบัตรประชาชน",passport:"เลขพาสปอร์ต",branch:"สำนักงานใหญ่ / สาขา",hq:"สำนักงานใหญ่",br:"สาขา",brno:"เลขสาขา",tinHintInd:"บุคคลใช้เลขบัตรประชาชนเป็นเลขผู้เสียภาษีได้",tinErr:"ต้องเป็นตัวเลข 13 หลัก",passErr:"พาสปอร์ต 4–20 ตัวอักษร/ตัวเลข",brErr:"เลขสาขาต้อง 5 หลัก",anonNote:"ลูกค้าทั่วไป: เว้นว่างได้ แต่ผู้ซื้อจะใช้ขอคืนภาษีไม่ได้",verify:"ตรวจสอบเลขภาษี",verifyLookup:"ตรวจสอบและดึงข้อมูล",verifiedCo:"ตรวจผ่าน · ดึงข้อมูลจากสรรพากร (แก้ได้)",verified:"ตรวจผ่าน",rdNeedTin:"กรอกเลขภาษีก่อน",rdCo13:"เลขภาษี 13 หลัก",lookupFail:"ไม่พบ · กรอกเอง",verifyFail:"ตรวจไม่ผ่าน / ไม่พบ",s3h:"รายการสินค้า",s3subMenu:"แตะเลือกสินค้าเหมือนสั่งอาหาร → ออกบิลอัตโนมัติ",searchPh:"ค้นหา / สแกน…",addCustom:"เพิ่มรายการเอง",cartEmpty:"แตะสินค้าทางซ้ายเพื่อเพิ่ม",saveCatalog:"บันทึกเข้าคลังสินค้า",lineNamePh:"ชื่อสินค้า/บริการ",linePrice:"ราคา",lineDisc:"ส่วนลด",hdisc:"ส่วนลดท้ายบิล",subtotal:"รวมเงิน",vat:"ภาษีมูลค่าเพิ่ม",whtL:"หัก ณ ที่จ่าย",grand:"ยอดสุทธิ",taxFree:"ยกเว้นภาษี",s4h:"รับชำระ & วันที่",s4sub:"ใบเสร็จ/ใบรวมต้องบันทึกการรับเงินก่อน",payStatus:"สถานะชำระ",paid:"รับเงินแล้ว",partial:"รับบางส่วน",unpaid:"ยังไม่รับ",payMethod:"วิธีรับเงิน",payDate:"วันที่รับ",paidAmt:"จำนวนที่รับ",issueDate:"วันที่ออก",dueDate:"ครบกำหนดชำระ",calendar:"ปฏิทิน",ce:"ค.ศ.",be:"พ.ศ.",payReqWarn:"เอกสารนี้เป็นใบเสร็จ/ใบรวม ต้องบันทึกรับเงินก่อนออก",payNA:"เอกสารประเภทนี้ไม่ต้องระบุการรับเงิน",s5h:"ตรวจสอบ & ออก",s5sub:"ออกแล้วเลขที่ล็อก แก้ไม่ได้ (ต้องใช้ใบลด/เพิ่มหนี้)",compliance:"ตรวจความถูกต้อง (มาตรา 86/4)",preview:"ตัวอย่างเอกสาร",ckBuyer:"ข้อมูลผู้ซื้อครบ",ckBuyerD:"ใบเต็มต้องมีชื่อ/ที่อยู่/เลขภาษี",ckTin:"รูปแบบเลขภาษีถูก",ckTinD:"13 หลัก / พาสปอร์ต",ckVat:"แยกบรรทัด VAT",ckVatD:"แยกภาษีออกจากราคาสินค้า",ckPay:"บันทึกรับเงินแล้ว",ckPayD:"ใบเสร็จ/ใบรวมต้องรับเงิน",ckSeq:"เลขที่ต่อเนื่อง",ckSeqD:"ออกเลขในทรานแซกชัน",ckWords:"จำนวนเงินตัวอักษร",ckWordsD:"สร้างคำอ่านบาทแล้ว",ckNa:"ไม่เกี่ยวข้อง",output:"ตั้งค่าการออก",paper:"กระดาษ",paperA4:"A4",paperA5:"A5",paperPos:"80mm ความร้อน",docLangL:"ภาษาเอกสาร",dlTh:"ไทย",dlThEn:"ไทย+อังกฤษ",dlThZh:"ไทย+จีน",layoutL:"รูปแบบ",laySingle:"ต้นฉบับหน้าเดียว",layPair:"ต้นฉบับ+สำเนาในแผ่นเดียว",tear:"ตัดตามเส้นประ · ส่วนบนให้ลูกค้า · ส่วนล่างเก็บไว้",okTitle:"ออกเอกสารแล้ว",okSeq:"ล็อกเลขที่แล้ว",okArchived:"จัดเก็บสำเนาอัตโนมัติ (5 ปี)",dl:"ดาวน์โหลด PDF",viewSend:"ดู / ส่ง",done:"เสร็จสิ้น",newOne:"ออกใบใหม่",blockers:"ยังออกไม่ได้:",draftSaved:"บันทึกร่างแล้ว (ยังไม่กินเลขที่)",saveFail:"บันทึกไม่สำเร็จ",issueFail:"ออกไม่สำเร็จ",needLines:"เพิ่มอย่างน้อยหนึ่งรายการ"}},em={steps:["書類の種類","売手/買手","明細","入金 / 日付","確認 & 発行"],sc:[["小売現金","合算 · 個人が現金払い"],["B2B 掛売","税額票 · 法人 · 掛け"],["個人の控除","合算 · 個人+身分証"],["POS 簡易","簡易票 · 匿名"]],docTypes:[["tax_invoice_receipt","税額票 + 領収書","一枚で両方を兼ねる(タイで最も一般的)"],["tax_invoice","税額票(掛売)","先に発行・後で入金"],["tax_invoice_simple","簡易税額票 ABB","小売・買手は仕入税額控除不可"],["receipt","領収書","入金証憑のみ・税額票ではない"],["quotation","見積書","見積用・税務証憑ではない"]],bt:[["company","法人","仕入税額控除可"],["individual","個人","タイ国籍の個人"],["foreigner","外国人","パスポート番号"],["anonymous","匿名客","記名なし"]],methods:[["cash","現金"],["transfer","振込"],["promptpay","PromptPay"],["card","カード"],["cheque","小切手"]],s:{title:"発行",sub:"· 売上請求書",back:"戻る",next:"次へ",draft:"下書き保存",issue:"請求書を発行",s1h:"書類の種類を選択",s1sub:"種類で後の入力項目が変わります。よくある場面から自動設定も可能。",scenarios:"よくある場面(タップで設定)",orManual:"または手動で選択",s2h:"売手 / 買手",s2sub:"売手は帳簿主体から自動入力、買手は種類で項目が変化。",seller:"売手(帳簿主体)",sellerPick:"どの会社で発行するか",buyer:"買手",buyerType:"買手の種類",name:"名称 / 氏名",addr:"住所",tin:"納税番号",natid:"身分証番号",passport:"パスポート番号",branch:"本店 / 支店",hq:"本店",br:"支店",brno:"支店番号",tinHintInd:"個人は身分証番号を納税番号に使えます",tinErr:"13 桁の数字",passErr:"パスポート 4–20 桁英数",brErr:"支店番号は 5 桁",anonNote:"匿名客:買手情報は空でも可。ただし買手は仕入控除に使えません。",verify:"番号照合",verifyLookup:"照合して取得",verifiedCo:"照合成功 · 税務署の登録情報を取得(編集可)",verified:"納税番号 照合成功",rdNeedTin:"先に納税番号を入力",rdCo13:"法人番号は 13 桁",lookupFail:"見つかりません · 手入力",verifyFail:"照合失敗 / 見つからない",s3h:"明細",s3subMenu:"注文のように左の商品をタップ → 右に自動で明細(自由行も追加可)",searchPh:"検索 / スキャン…",addCustom:"自由行を追加(サービス/在庫外)",cartEmpty:"左の商品をタップして追加",saveCatalog:"商品マスタに保存",lineNamePh:"商品/サービス名",linePrice:"単価",lineDisc:"割引",hdisc:"伝票全体の割引",subtotal:"小計",vat:"付加価値税 VAT",whtL:"源泉税 WHT",grand:"請求合計",taxFree:"非課税",s4h:"入金 & 日付",s4sub:"領収書/合算は先に入金記録が必要。掛売は未入金でも可。",payStatus:"入金状態",paid:"入金済",partial:"一部入金",unpaid:"未入金",payMethod:"入金方法",payDate:"入金日",paidAmt:"入金額",issueDate:"発行日",dueDate:"支払期日",calendar:"暦",ce:"西暦",be:"仏暦 (พ.ศ.)",payReqWarn:"これは領収書/合算です:発行前に入金(または一部)を記録してください。",payNA:"この種類は入金情報が不要です。",s5h:"確認して発行",s5sub:"発行後は番号がロックされ内容は変更不可(貸方/借方票で調整)。",compliance:"コンプライアンス確認(歳入法第86/4条)",preview:"請求書プレビュー",ckBuyer:"買手情報が完全",ckBuyerD:"完全な税額票は名称/住所/納税番号が必要(法人は支店も)",ckTin:"納税番号の形式が正しい",ckTinD:"13 桁 / パスポート",ckVat:"VAT を分離表示",ckVatD:"税額と本体価格を分離",ckPay:"入金記録済",ckPayD:"領収書/合算は入金必須",ckSeq:"連番(欠番なし)",ckSeqD:"発行時にトランザクションで採番",ckWords:"金額の文字表記",ckWordsD:"バーツ表記を生成済",ckNa:"対象外",output:"出力設定",paper:"用紙",paperA4:"A4",paperA5:"A5",paperPos:"80mm 感熱",docLangL:"書類の言語",dlTh:"タイ語",dlThEn:"タイ+英",dlThZh:"タイ+中",layoutL:"レイアウト",laySingle:"正本のみ1ページ",layPair:"正本+副本を1ページ",tear:"破線で切離 · 上を客へ · 下を控え",okTitle:"発行完了",okSeq:"番号をロック",okArchived:"副本を自動保管(5年)",dl:"PDF をダウンロード",viewSend:"表示 / 送信",done:"完了",newOne:"もう一枚",blockers:"発行にはあと:",draftSaved:"下書き保存(番号は未使用)",saveFail:"保存失敗",issueFail:"発行失敗",needLines:"明細を1行以上追加"}},tm={steps:["单据类型","买卖双方","商品明细","收款 / 日期","核对开出"],sc:[["零售收现金","合并单 · 个人散客付现"],["B2B 赊销","税票 · 公司 · 月结"],["个人要抵税","合并单 · 个人带身份证"],["POS 简易票","简易票 · 不记名"]],docTypes:[["tax_invoice_receipt","税票 + 收据合并单","一张纸既是税票又是收据(泰国最常见,收钱当场开)"],["tax_invoice","税票(赊销)","先开票后收款,月结/账期常用"],["tax_invoice_simple","简易税票 ABB","零售小票,不记买方,买方不能抵扣"],["receipt","收据","纯收款凭证,非税票"],["quotation","报价单","报价用,不是税务凭证"]],bt:[["company","公司","法人,可抵进项"],["individual","个人","本国自然人"],["foreigner","外国个人","用护照号"],["anonymous","匿名散客","不记名"]],methods:[["cash","现金"],["transfer","转账"],["promptpay","PromptPay"],["card","刷卡"],["cheque","支票"]],s:{title:"开票",sub:"· 销项发票",back:"上一步",next:"下一步",draft:"存草稿",issue:"开出发票",s1h:"选择单据类型",s1sub:"不同单据,后面要填的内容会自动变。也可以点常见场景一键带出。",scenarios:"常见场景(点一下自动设置)",orManual:"或手动选类型",s2h:"买卖双方",s2sub:"卖方按账套主体自动带出;买方按类型动态显示该填什么。",seller:"卖方(账套主体)",sellerPick:"选择以哪家公司开票",buyer:"买方",buyerType:"买方类型",name:"名称 / 姓名",addr:"地址",tin:"税号",natid:"身份证号",passport:"护照号",branch:"总公司 / 分店",hq:"总公司",br:"分店",brno:"分店号",tinHintInd:"个人可用身份证号作为税号",tinErr:"需为 13 位数字",passErr:"护照号 4–20 位字母数字",brErr:"分店号需 5 位数字",anonNote:"匿名散客:买方信息留空也可,但买方将无法用于抵扣进项 / 个税。",verify:"核验税号",verifyLookup:"核验并带出",verifiedCo:"税号验真通过 · 已从税局带出登记信息(可改)",verified:"税号验真通过",rdNeedTin:"先填税号",rdCo13:"公司税号需 13 位",lookupFail:"查不到 · 请手填",verifyFail:"验真不通过 / 查不到",s3h:"商品明细",s3subMenu:"像餐厅点单:左边点商品 → 右边自动成单(没有的可加自定义行)",searchPh:"搜商品 / 扫码…",addCustom:"加自定义行(服务/不在库)",cartEmpty:"点左边商品加入 · 像点菜单",saveCatalog:"存入商品库(以后也能点)",lineNamePh:"商品/服务名",linePrice:"单价",lineDisc:"折扣",hdisc:"整单折扣",subtotal:"小计",vat:"增值税 VAT",whtL:"预扣税 WHT",grand:"合计应付",taxFree:"免税",s4h:"收款与日期",s4sub:"收据/合并单必须先记收款;赊销税票可暂不收。",payStatus:"收款状态",paid:"已收款",partial:"部分收款",unpaid:"未收款",payMethod:"收款方式",payDate:"收款日",paidAmt:"已收金额",issueDate:"开票日期",dueDate:"付款到期日",calendar:"日期历法",ce:"公历",be:"佛历 พ.ศ.",payReqWarn:"当前单据是收据/合并单:开出前必须记为已收款(或部分收款)。",payNA:"此单据类型无需收款信息。",s5h:"核对并开出",s5sub:"确认无误后开出。开出后连号锁定、内容不可改(红冲/补开才能调整)。",compliance:"合规检查(泰国税法第 86/4 条)",preview:"发票预览",ckBuyer:"买方信息齐全",ckBuyerD:"完整税票需买方名称/地址/税号(公司还要分店)",ckTin:"税号格式正确",ckTinD:"13 位数字 / 护照号",ckVat:"VAT 单独列示",ckVatD:"税额与货值分开",ckPay:"收款已记录",ckPayD:"收据/合并单须已收款",ckSeq:"连号不跳号",ckSeqD:"开出时事务取号",ckWords:"金额大写",ckWordsD:"泰铢大写已生成",ckNa:"不适用",output:"输出设置",paper:"纸张",paperA4:"A4",paperA5:"A5",paperPos:"80mm 热敏",docLangL:"文档语言",dlTh:"泰文",dlThEn:"泰+英",dlThZh:"泰+中",layoutL:"版式 / 联数",laySingle:"正本单页",layPair:"正本+副本同页",tear:"沿虚线裁开 · 上联给顾客 · 下联自留",okTitle:"已开出",okSeq:"连号已锁定",okArchived:"副本已自动归档(留底 5 年)",dl:"下载 PDF 正本",viewSend:"查看 / 发送",done:"完成",newOne:"再开一张",blockers:"还差这些才能开出:",draftSaved:"草稿已保存(未占连号)",saveFail:"保存失败",issueFail:"开出失败",needLines:"请至少加一行商品"}},nm={steps:["Document type","Parties","Line items","Payment / Date","Review & issue"],sc:[["Retail cash","Combined · individual pays cash"],["B2B credit","Tax invoice · company · terms"],["Individual tax","Combined · individual w/ ID"],["POS simplified","Simplified · anonymous"]],docTypes:[["tax_invoice_receipt","Tax Invoice + Receipt","One paper that is both (most common in Thailand)"],["tax_invoice","Tax Invoice (credit)","Issued first, paid later"],["tax_invoice_simple","Simplified ABB","Retail; buyer cannot claim input VAT"],["receipt","Receipt","Payment proof only, not a tax invoice"],["quotation","Quotation","For quoting, not a tax document"]],bt:[["company","Company","Legal entity, can claim VAT"],["individual","Individual","Thai natural person"],["foreigner","Foreigner","Uses passport no."],["anonymous","Walk-in","Anonymous"]],methods:[["cash","Cash"],["transfer","Transfer"],["promptpay","PromptPay"],["card","Card"],["cheque","Cheque"]],s:{title:"New Invoice",sub:"· Sales invoice",back:"Back",next:"Next",draft:"Save draft",issue:"Issue invoice",s1h:"Choose document type",s1sub:"Each type changes later fields. Or pick a common scenario.",scenarios:"Common scenarios (tap to set)",orManual:"Or pick a type manually",s2h:"Parties",s2sub:"Seller auto-fills from your company; buyer fields adapt to type.",seller:"Seller (company)",sellerPick:"Choose which company issues",buyer:"Buyer",buyerType:"Buyer type",name:"Name",addr:"Address",tin:"Tax ID",natid:"National ID",passport:"Passport no.",branch:"HQ / Branch",hq:"HQ",br:"Branch",brno:"Branch no.",tinHintInd:"Individuals may use national ID as tax ID",tinErr:"Must be 13 digits",passErr:"Passport 4–20 alphanumeric",brErr:"Branch no. must be 5 digits",anonNote:"Walk-in: buyer info may be blank, but the buyer cannot claim input VAT / tax.",verify:"Verify Tax ID",verifyLookup:"Verify & autofill",verifiedCo:"Verified · pulled registration from RD (editable)",verified:"Tax ID verified",rdNeedTin:"Enter the tax ID first",rdCo13:"Company tax ID must be 13 digits",lookupFail:"Not found · enter manually",verifyFail:"Verification failed / not found",s3h:"Line items",s3subMenu:"Like ordering food: tap products on the left → cart on the right (add custom rows too)",searchPh:"Search / scan…",addCustom:"Add custom row (service / off-catalog)",cartEmpty:"Tap a product to add · like a menu",saveCatalog:"Save to product catalog",lineNamePh:"Item / service name",linePrice:"Price",lineDisc:"Discount",hdisc:"Whole-bill discount",subtotal:"Subtotal",vat:"VAT",whtL:"WHT",grand:"Total due",taxFree:"tax-free",s4h:"Payment & date",s4sub:"Receipts/combined must record payment first; credit invoices may stay unpaid.",payStatus:"Payment status",paid:"Paid",partial:"Partial",unpaid:"Unpaid",payMethod:"Method",payDate:"Paid date",paidAmt:"Paid amount",issueDate:"Issue date",dueDate:"Due date",calendar:"Calendar",ce:"CE",be:"BE (พ.ศ.)",payReqWarn:"This is a receipt/combined: must be marked paid (or partial) before issuing.",payNA:"This document type needs no payment info.",s5h:"Review & issue",s5sub:"Once issued, the number is locked and content cannot change (use credit/debit notes).",compliance:"Compliance check (Revenue Code §86/4)",preview:"Invoice preview",ckBuyer:"Buyer info complete",ckBuyerD:"Full tax invoice needs name/address/tax ID (company also branch)",ckTin:"Tax ID format valid",ckTinD:"13 digits / passport",ckVat:"VAT shown separately",ckVatD:"Tax split from goods value",ckPay:"Payment recorded",ckPayD:"Receipt/combined must be paid",ckSeq:"Sequential numbering",ckSeqD:"Number drawn in a transaction",ckWords:"Amount in words",ckWordsD:"Baht text generated",ckNa:"N/A",output:"Output settings",paper:"Paper",paperA4:"A4",paperA5:"A5",paperPos:"80mm thermal",docLangL:"Document language",dlTh:"Thai",dlThEn:"Thai+Eng",dlThZh:"Thai+Chi",layoutL:"Layout",laySingle:"Original single page",layPair:"Original + copy on one page",tear:"Cut along the dashed line · top to customer · bottom kept",okTitle:"Issued",okSeq:"Number locked",okArchived:"Copy auto-archived (kept 5 yrs)",dl:"Download PDF",viewSend:"View / Send",done:"Done",newOne:"New invoice",blockers:"Still needed before issuing:",draftSaved:"Draft saved (no number used)",saveFail:"Save failed",issueFail:"Issue failed",needLines:"Add at least one line item"}},as={zh:tm,en:nm,th:Qu,ja:em};let Ks="th";function am(e){as[e]&&(Ks=e)}function sm(){return Ks}function Cn(){return as[Ks]||as.th}function C(e){return Cn().s[e]||e}const om={no:{th:"เลขที่",en:"No.",zh:"号码"},date:{th:"วันที่",en:"Date",zh:"日期"},seller:{th:"ผู้ขาย",en:"Seller",zh:"卖方"},buyer:{th:"ผู้ซื้อ",en:"Buyer",zh:"买方"},desc:{th:"รายการ",en:"Description",zh:"商品"},qty:{th:"จำนวน",en:"Qty",zh:"数量"},price:{th:"ราคา",en:"Price",zh:"单价"},disc:{th:"ส่วนลด",en:"Discount",zh:"折扣"},amount:{th:"จำนวนเงิน",en:"Amount",zh:"金额"},subtotal:{th:"มูลค่า",en:"Subtotal",zh:"小计"},grand:{th:"รวมทั้งสิ้น",en:"Grand Total",zh:"合计"},words:{th:"ตัวอักษร",en:"In words",zh:"大写"},paid:{th:"การรับเงิน",en:"Payment",zh:"收款"},wht:{th:"หัก ณ ที่จ่าย",en:"WHT",zh:"预扣税"},signSeller:{th:"ผู้รับเงิน / ผู้มีอำนาจ",en:"Authorized",zh:"收款人/授权"},signBuyer:{th:"ผู้ซื้อ",en:"Buyer",zh:"买方签收"}};function ke(e,n){const a=om[n];return e.docLang==="th"?a.th:a.th+" / "+(e.docLang==="th_zh"?a.zh:a.en)}const im={tax_invoice_receipt:"ใบกำกับภาษี/ใบเสร็จรับเงิน · Tax Invoice / Receipt",tax_invoice:"ใบกำกับภาษี · Tax Invoice",tax_invoice_simple:"ใบกำกับภาษีอย่างย่อ · Simplified",receipt:"ใบเสร็จรับเงิน · Receipt",quotation:"ใบเสนอราคา · Quotation"},rm={cash:"เงินสด",transfer:"โอน",promptpay:"พร้อมเพย์",card:"บัตร",cheque:"เช็ค"};function Ko(e,n){if(!n)return"-";if(e.be){const a=n.split("-");return+a[0]+543+"-"+a[1]+"-"+a[2]}return n}function Da(e,n){const a=Ir()[e.sellerIdx]||{name:"",tax_id:"",address:"",branch:""},s=e.buyer,o=_a(e),i=s.type==="individual"?"เลขบัตรประชาชน":s.type==="foreigner"?"Passport":"Tax ID",r=s.name||(s.type==="anonymous"?"ลูกค้าทั่วไป":"-"),l=s.type==="anonymous"&&!s.name?"":`<div class="sw-pl">${escapeHtml(s.addr)||""}</div><div class="sw-pl">${i}: ${escapeHtml(s.tin)||"-"}</div>
               ${s.type==="company"?`<div class="sw-pl">${s.branchType==="hq"?"สำนักงานใหญ่":"สาขาที่ "+(escapeHtml(s.branchNo)||"-")}</div>`:""}`,m=e.lines.map((v,f)=>`<tr><td>${f+1}</td><td>${escapeHtml(v.desc)||"-"}</td><td class="r">${be(+v.qty||0)}</td><td class="r">${be(+v.price||0)}</td><td class="r">${+v.disc>0?"-"+be(+v.disc):"-"}</td><td class="r">${be(Math.max(0,(+v.qty||0)*(+v.price||0)-(+v.disc||0)))}</td></tr>`).join(""),d=Gs(e)&&e.pay.status!=="unpaid"?`<div class="sw-inv-pay"><b>${ke(e,"paid")}:</b> ${rm[e.pay.method]||e.pay.method} · ${Ko(e,e.pay.date)} · ${e.pay.status==="partial"?"฿ "+be(+(e.pay.paidAmt||0)):"฿ "+be(o.grand)}</div>`:"",p=e.docLang==="th_zh"?Vu(o.grand):Ou(o.grand),c=n==="copy",u=c?e.docLang==="th"?"สำเนา":"สำเนา / Copy":e.docLang==="th"?"ต้นฉบับ":"ต้นฉบับ / Original";return`<div class="sw-invoice ${e.paper==="pos"?"pos":""} ${e.layout==="pair"?"half":""}">
        <div class="sw-copybadge ${c?"copy":""}">${u}</div>
        <h3>${im[e.docType]}</h3>
        <div class="sw-docno">${ke(e,"no")}: — &nbsp;·&nbsp; ${ke(e,"date")}: ${Ko(e,e.issueDate)}${e.be?" (พ.ศ.)":""}</div>
        <div class="sw-inv-parties">
            <div><div class="sw-ptitle">${ke(e,"seller")}</div>
                <div class="sw-pname">${escapeHtml(a.name||"")}</div><div class="sw-pl">${escapeHtml(a.address||"")}</div>
                <div class="sw-pl">Tax ID: ${escapeHtml(a.tax_id||"-")} · ${escapeHtml(a.branch||"")}</div></div>
            <div><div class="sw-ptitle">${ke(e,"buyer")}</div>
                <div class="sw-pname">${escapeHtml(r)}</div>${l}</div>
        </div>
        <table class="sw-inv-items">
            <thead><tr><th>#</th><th>${ke(e,"desc")}</th><th class="r">${ke(e,"qty")}</th><th class="r">${ke(e,"price")}</th><th class="r">${ke(e,"disc")}</th><th class="r">${ke(e,"amount")}</th></tr></thead>
            <tbody>${m}</tbody>
        </table>
        <div class="sw-inv-tot">
            <div class="sw-tr"><span>${ke(e,"subtotal")}</span><span>${be(o.subAfter)}</span></div>
            <div class="sw-tr"><span>VAT ${e.vatRate}%</span><span>${be(o.vat)}</span></div>
            ${o.wht>0?`<div class="sw-tr"><span>${ke(e,"wht")}</span><span>-${be(o.wht)}</span></div>`:""}
            <div class="sw-tr g"><span>${ke(e,"grand")}</span><span>฿ ${be(o.grand)}</span></div>
        </div>
        <div class="sw-inv-words"><b>${ke(e,"words")}:</b> ${p}</div>
        ${d}
        <div class="sw-inv-sign"><div class="s">${ke(e,"signSeller")}</div><div class="s">${ke(e,"signBuyer")}</div></div>
    </div>`}function lm(e,n,a){return e.layout==="pair"&&e.paper!=="pos"?`<div class="sw-pairwrap">${Da(e,"original")}
            <div class="sw-tear"><span>${a} ${escapeHtml(n)}</span></div>
            ${Da(e,"copy")}</div>`:Da(e,"original")}const ye={check:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg>',checkG:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg>',x:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M18 6 6 18M6 6l12 12"/></svg>',plus:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg>',trash:'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>',info:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5v.5"/></svg>',close:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>',box:'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.7"><path d="M21 8 12 3 3 8l9 5 9-5ZM3 8v8l9 5 9-5V8"/></svg>'},Yo=["#2563eb","#db2777","#16a34a","#d97706","#0891b2","#7c3aed","#92400e","#e11d48","#059669"];function $r(e){const n=sm();return n==="zh"&&(e.name_zh||e.name_th)||n==="en"&&(e.name_en||e.name_th)||e.name_th||e.name_en||e.name_zh||"—"}function cm(e){const n=Cn(),a=n.sc.map((o,i)=>`<span class="sw-chip" data-sc="${i}"><b>${escapeHtml(o[0])}</b> · <span class="sw-muted">${escapeHtml(o[1])}</span></span>`).join(""),s=n.docTypes.map(o=>`<div class="sw-choice ${e.docType===o[0]?"on":""}" data-doc="${o[0]}"><div class="sw-ck">${ye.check}</div><div><div class="sw-t">${escapeHtml(o[1])}</div><div class="sw-d">${escapeHtml(o[2])}</div></div></div>`).join("");return`<div class="sw-card"><h2>${escapeHtml(C("s1h"))}</h2><div class="sw-sub">${escapeHtml(C("s1sub"))}</div>
        <div class="sw-sectitle">${escapeHtml(C("scenarios"))}</div><div class="sw-chips">${a}</div>
        <div class="sw-sectitle">${escapeHtml(C("orManual"))}</div><div class="sw-choices">${s}</div></div>`}function dm(e){const n=Cn(),a=Ir(),s=a[e.sellerIdx],o=a.map((f,y)=>`<option value="${y}" ${y===e.sellerIdx?"selected":""}>${escapeHtml(f.name||"—")}</option>`).join(""),i=n.bt.map(f=>`<div class="sw-choice ${e.buyer.type===f[0]?"on":""}" data-bt="${f[0]}" style="padding:10px 12px"><div class="sw-ck">${ye.check}</div><div><div class="sw-t">${escapeHtml(f[1])}</div><div class="sw-d">${escapeHtml(f[2])}</div></div></div>`).join(""),r=e.buyer,l=r.type==="anonymous",m=r.type==="company",d=r.type==="individual"?C("natid"):r.type==="foreigner"?C("passport"):C("tin"),p=l?"":'<span class="sw-req">*</span>';let c="";l||(r.type==="foreigner"?r.tin&&!/^[A-Za-z0-9]{4,20}$/.test(r.tin)&&(c=`<div class="sw-hint err">${escapeHtml(C("passErr"))}</div>`):r.tin&&!/^\d{13}$/.test(r.tin)?c=`<div class="sw-hint err">${escapeHtml(C("tinErr"))}</div>`:r.type==="individual"&&(c=`<div class="sw-hint info">${ye.info} ${escapeHtml(C("tinHintInd"))}</div>`));const u=s?`${escapeHtml(s.name||"")} · ${escapeHtml(s.tax_id||"")} · ${escapeHtml(s.branch||"")}`:"—",v=l?`<div class="sw-banner warn">${ye.info}<span>${escapeHtml(C("anonNote"))}</span></div>
           <div class="sw-field"><label>${escapeHtml(C("name"))}</label><input type="text" id="sw-bname" value="${escapeHtml(r.name)}"></div>`:`<div class="sw-field"><label>${escapeHtml(C("name"))} ${p}</label><input type="text" id="sw-bname" value="${escapeHtml(r.name)}"></div>
           <div class="sw-field"><label>${escapeHtml(C("addr"))} ${p}</label><input type="text" id="sw-baddr" value="${escapeHtml(r.addr)}"></div>
           <div class="sw-field"><label>${escapeHtml(d)} ${p}</label>
             <div style="display:flex;gap:8px"><input type="text" id="sw-btin" value="${escapeHtml(r.tin)}" style="flex:1">
               <button type="button" id="sw-rd" class="btn btn-primary" style="white-space:nowrap">${r.type==="company"?escapeHtml(C("verifyLookup")):escapeHtml(C("verify"))}</button></div>
             ${r.verified?`<div class="sw-hint ok">${ye.checkG} ${escapeHtml(r.type==="company"?C("verifiedCo"):C("verified"))}</div>`:c}</div>
           ${m?pm(e):""}`;return`<div class="sw-card"><h2>${escapeHtml(C("s2h"))}</h2><div class="sw-sub">${escapeHtml(C("s2sub"))}</div>
        <div class="sw-sectitle">${escapeHtml(C("seller"))}</div>
        <div class="sw-field"><label>${escapeHtml(C("sellerPick"))}</label><select id="sw-seller">${o}</select></div>
        <div class="sw-banner">${ye.info}<span>${u}</span></div>
        <div class="sw-sectitle">${escapeHtml(C("buyer"))} — ${escapeHtml(C("buyerType"))}</div>
        <div class="sw-choices">${i}</div>
        <div style="margin-top:16px">${v}</div></div>`}function pm(e){const n=e.buyer,a=n.branchNo&&!/^\d{5}$/.test(n.branchNo);return`<div class="sw-field"><label>${escapeHtml(C("branch"))} <span class="sw-req">*</span></label>
        <div class="sw-seg" style="margin-bottom:8px">
            <button type="button" data-brt="hq" class="${n.branchType==="hq"?"on":""}">${escapeHtml(C("hq"))}</button>
            <button type="button" data-brt="branch" class="${n.branchType==="branch"?"on":""}">${escapeHtml(C("br"))}</button></div>
        ${n.branchType==="branch"?`<input type="text" id="sw-brno" value="${escapeHtml(n.branchNo)}" placeholder="${escapeHtml(C("brno"))} (5)">${a?`<div class="sw-hint err">${escapeHtml(C("brErr"))}</div>`:""}`:""}</div>`}function um(e){const n=_a(e),a=Br(),s=a.map((l,m)=>`<div class="sw-pcard" data-add="${m}"><div class="sw-pimg" style="background:${Yo[m%Yo.length]}">${l.image_url?`<img src="${escapeHtml(l.image_url)}" alt="">`:ye.box}</div><div class="sw-pn">${escapeHtml($r(l))}</div><div class="sw-pp">฿${be(l.unit_price)}${l.vat_applicable?"":` <span class="sw-muted" style="font-size:10px">${escapeHtml(C("taxFree"))}</span>`}</div></div>`).join(""),o=a.length?"":'<div class="sw-muted" style="padding:20px;text-align:center">—</div>',r=e.lines.some(l=>l.desc||+l.price||l.custom)?e.lines.map((l,m)=>`<div class="sw-citem">
            <div class="sw-crow1"><input type="text" data-ln="${m}" data-f="desc" value="${escapeHtml(l.desc)}" placeholder="${escapeHtml(C("lineNamePh"))}" style="border:0;font-weight:600;padding:2px;flex:1;background:transparent"><button class="sw-iconbtn" data-rm="${m}">${ye.trash}</button></div>
            <div class="sw-crow2"><div class="sw-cqty"><button data-q="${m}" data-d="-1">−</button><span>${l.qty}</span><button data-q="${m}" data-d="1">+</button></div>
              <div class="sw-cfield"><label>${escapeHtml(C("linePrice"))}</label><input type="number" data-ln="${m}" data-f="price" value="${l.price}" min="0" step="0.01"></div>
              <div class="sw-cfield"><label>${escapeHtml(C("lineDisc"))}</label><input type="number" data-ln="${m}" data-f="disc" value="${l.disc}" min="0" step="0.01"></div>
              <span class="sw-amt">฿${be(Math.max(0,(+l.qty||0)*(+l.price||0)-(+l.disc||0)))}</span></div>
            ${l.custom?`<label style="display:flex;align-items:center;gap:6px;margin-top:7px;font-size:11px;color:var(--ink-3);cursor:pointer"><input type="checkbox" style="width:auto" data-save="${m}" ${l.save?"checked":""}> ${escapeHtml(C("saveCatalog"))}</label>`:""}</div>`).join(""):`<div class="sw-cart-empty">${escapeHtml(C("cartEmpty"))}</div>`;return`<div class="sw-card"><h2>${escapeHtml(C("s3h"))}</h2><div class="sw-sub">${escapeHtml(C("s3subMenu"))}</div>
        <div class="sw-menu">
            <div><input type="text" placeholder="${escapeHtml(C("searchPh"))}" style="margin-bottom:10px" id="sw-psearch"><div class="sw-pgrid">${s}${o}</div>
              <button class="sw-addline" id="sw-addcustom">${ye.plus} ${escapeHtml(C("addCustom"))}</button></div>
            <div><div class="sw-cart">${r}</div>
              <div class="sw-row" style="margin-top:12px">
                <div class="sw-field" style="margin:0"><label>${escapeHtml(C("hdisc"))}</label><input type="number" id="sw-hdisc" value="${e.hdisc}" min="0" step="0.01"></div>
                <div class="sw-field" style="margin:0"><label>VAT %</label><input type="number" id="sw-vat" value="${e.vatRate}" min="0" step="0.5"></div>
                <div class="sw-field" style="margin:0"><label>WHT %</label><input type="number" id="sw-wht" value="${e.whtRate}" min="0" step="0.5"></div></div>
              <div class="sw-totals">
                <div class="sw-tr"><span>${escapeHtml(C("subtotal"))}</span><span class="v">${be(n.sub)}</span></div>
                ${n.hd>0?`<div class="sw-tr disc"><span>${escapeHtml(C("hdisc"))}</span><span class="v">-${be(n.hd)}</span></div>`:""}
                <div class="sw-tr"><span>${escapeHtml(C("vat"))} ${e.vatRate}%</span><span class="v">${be(n.vat)}</span></div>
                ${n.wht>0?`<div class="sw-tr disc"><span>${escapeHtml(C("whtL"))} ${e.whtRate}%</span><span class="v">-${be(n.wht)}</span></div>`:""}
                <div class="sw-tr grand"><span>${escapeHtml(C("grand"))}</span><span class="v">฿ ${be(n.grand)}</span></div></div></div>
        </div></div>`}function mm(e){const n=Cn(),a=_a(e);if(!Gs(e))return`<div class="sw-card"><h2>${escapeHtml(C("s4h"))}</h2><div class="sw-sub">${escapeHtml(C("s4sub"))}</div>
            <div class="sw-banner">${ye.info}<span>${escapeHtml(C("payNA"))}</span></div>${Jo(e)}</div>`;const s=e.pay,o=n.methods.map(i=>`<option value="${i[0]}" ${s.method===i[0]?"selected":""}>${escapeHtml(i[1])}</option>`).join("");return`<div class="sw-card"><h2>${escapeHtml(C("s4h"))}</h2><div class="sw-sub">${escapeHtml(C("s4sub"))}</div>
        ${Gn(e)?`<div class="sw-banner warn">${ye.info}<span>${escapeHtml(C("payReqWarn"))}</span></div>`:""}
        <div class="sw-field"><label>${escapeHtml(C("payStatus"))}</label><div class="sw-seg">
            <button type="button" data-ps="paid" class="${s.status==="paid"?"on":""}">${escapeHtml(C("paid"))}</button>
            <button type="button" data-ps="partial" class="${s.status==="partial"?"on":""}">${escapeHtml(C("partial"))}</button>
            <button type="button" data-ps="unpaid" class="${s.status==="unpaid"?"on":""}">${escapeHtml(C("unpaid"))}</button></div></div>
        ${s.status!=="unpaid"?`<div class="sw-row3">
            <div class="sw-field"><label>${escapeHtml(C("payMethod"))}</label><select id="sw-pm">${o}</select></div>
            <div class="sw-field"><label>${escapeHtml(C("payDate"))}</label><input type="date" id="sw-pdate" value="${s.date}"></div>
            ${s.status==="partial"?`<div class="sw-field"><label>${escapeHtml(C("paidAmt"))}</label><input type="number" id="sw-paid" value="${s.paidAmt!=null?s.paidAmt:""}" placeholder="${be(a.grand)}"></div>`:`<div class="sw-field"><label>${escapeHtml(C("paidAmt"))}</label><input type="text" value="฿ ${be(a.grand)}" disabled></div>`}</div>`:""}
        ${Jo(e)}</div>`}function Jo(e){return`<div class="sw-sectitle">${escapeHtml(C("issueDate"))}</div><div class="sw-row3">
        <div class="sw-field"><label>${escapeHtml(C("issueDate"))}</label><input type="date" id="sw-idate" value="${e.issueDate}"></div>
        ${e.docType==="tax_invoice"?`<div class="sw-field"><label>${escapeHtml(C("dueDate"))}</label><input type="date" id="sw-ddate" value="${e.dueDate}"></div>`:"<div></div>"}
        <div class="sw-field"><label>${escapeHtml(C("calendar"))}</label><div class="sw-seg">
            <button type="button" data-cal="ce" class="${e.be?"":"on"}">${escapeHtml(C("ce"))}</button>
            <button type="button" data-cal="be" class="${e.be?"on":""}">${escapeHtml(C("be"))}</button></div></div></div>`}function vm(e){const n=_r(e).map(i=>i.na?`<div class="sw-check"><div class="sw-ci" style="background:#eee;color:#999">${ye.checkG}</div><div><div class="sw-ct">${escapeHtml(C(i.key))} <span class="sw-pill">${escapeHtml(C("ckNa"))}</span></div></div></div>`:`<div class="sw-check ${i.pass?"pass":"fail"}"><div class="sw-ci">${i.pass?ye.checkG:ye.x}</div><div><div class="sw-ct">${escapeHtml(C(i.key))}${i.req&&!i.pass?' <span class="sw-req">*</span>':""}</div><div class="sw-cd">${escapeHtml(C(i.descKey))}</div></div></div>`).join(""),a={a4:"paperA4",a5:"paperA5",pos:"paperPos"},s=["a4","a5","pos"].map(i=>`<button type="button" data-paper="${i}" class="${e.paper===i?"on":""}">${escapeHtml(C(a[i]))}</button>`).join(""),o=["th","th_en","th_zh"].map(i=>`<button type="button" data-dlang="${i}" class="${e.docLang===i?"on":""}">${escapeHtml(C(i==="th"?"dlTh":i==="th_en"?"dlThEn":"dlThZh"))}</button>`).join("");return`<div class="sw-card"><h2>${escapeHtml(C("s5h"))}</h2><div class="sw-sub">${escapeHtml(C("s5sub"))}</div>
        <div class="sw-sectitle">${escapeHtml(C("compliance"))}</div><div class="sw-checks">${n}</div>
        <div class="sw-sectitle" style="margin-top:22px">${escapeHtml(C("output"))}</div>
        <div class="sw-row" style="max-width:580px">
            <div class="sw-field"><label>${escapeHtml(C("paper"))}</label><div class="sw-seg">${s}</div></div>
            <div class="sw-field"><label>${escapeHtml(C("docLangL"))}</label><div class="sw-seg">${o}</div></div></div>
        ${e.paper!=="pos"?`<div class="sw-field" style="max-width:580px;margin-top:4px"><label>${escapeHtml(C("layoutL"))}</label><div class="sw-seg"><button type="button" data-layout="single" class="${e.layout==="single"?"on":""}">${escapeHtml(C("laySingle"))}</button><button type="button" data-layout="pair" class="${e.layout==="pair"?"on":""}">${escapeHtml(C("layPair"))}</button></div></div>`:""}
        <div class="sw-sectitle" style="margin-top:18px">${escapeHtml(C("preview"))}</div>
        <div id="sw-print">${lm(e,C("tear"),ye.info)}</div></div>`}function ss(){const e=new Date;return e.getFullYear()+"-"+String(e.getMonth()+1).padStart(2,"0")+"-"+String(e.getDate()).padStart(2,"0")}let qe=0,V;function Sr(){return{docType:"tax_invoice_receipt",sellerIdx:0,buyer:{type:"company",name:"",addr:"",tin:"",branchType:"hq",branchNo:""},lines:[],hdisc:0,vatRate:7,whtRate:0,pay:{status:"paid",method:"transfer",date:ss(),paidAmt:null},issueDate:ss(),dueDate:"",be:!1,paper:"a4",docLang:"th_en",layout:"single",draftId:null}}function ue(){let e=document.getElementById("sales-wizard-mask");return e||(e=document.createElement("div"),e.id="sales-wizard-mask",e.className="sw-mask",document.body.appendChild(e)),e}function os(){const e=document.getElementById("sales-wizard-mask");e&&(e.style.display="none",e.innerHTML="")}function me(){const n=Cn().steps.map((s,o)=>{const i=o===qe?"active":o<qe?"done":"",r=o<qe?ye.check:o+1;return`<div class="sw-step ${i}"><div class="sw-num">${r}</div><div class="sw-lbl">${escapeHtml(s)}</div>${o<4?'<div class="sw-bar"></div>':""}</div>`}).join(""),a=[cm,dm,um,mm,vm][qe](V);ue().innerHTML=`<div class="sw-wrap">
        <div class="sw-topbar">
            <div class="sw-brand">${escapeHtml(C("title"))}<small>${escapeHtml(C("sub"))}</small></div>
            <button class="sw-x" id="sw-close" aria-label="close">${ye.close}</button>
        </div>
        <div class="sw-stepper">${n}</div>
        <div id="sw-body">${a}</div>
        <div class="sw-nav">
            <div class="sw-left">
                <button class="btn btn-ghost" id="sw-back" ${qe===0?"disabled":""}>${escapeHtml(C("back"))}</button>
                <button class="btn btn-ghost" id="sw-draft">${escapeHtml(C("draft"))}</button>
            </div>
            <button class="btn btn-primary" id="sw-next">${escapeHtml(C(qe===4?"issue":"next"))}</button>
        </div>
    </div>`,ue().style.display="flex",fm()}function Ve(e,n,a=!1){const s=document.getElementById(e);s&&(s.oninput=()=>n(s.value),a&&(s.onblur=me))}function fm(){document.getElementById("sw-close").onclick=os,document.getElementById("sw-back").onclick=()=>Xo(-1),document.getElementById("sw-next").onclick=()=>Xo(1),document.getElementById("sw-draft").onclick=_m,ue().querySelectorAll("[data-doc]").forEach(o=>o.onclick=()=>(V.docType=o.dataset.doc,me())),ue().querySelectorAll("[data-sc]").forEach(o=>o.onclick=()=>km(+o.dataset.sc));const e=document.getElementById("sw-seller");e&&(e.onchange=()=>(V.sellerIdx=+e.value,me())),ue().querySelectorAll("[data-bt]").forEach(o=>o.onclick=()=>hm(o.dataset.bt)),ue().querySelectorAll("[data-brt]").forEach(o=>o.onclick=()=>(V.buyer.branchType=o.dataset.brt,o.dataset.brt==="hq"&&(V.buyer.branchNo=""),me())),Ve("sw-bname",o=>V.buyer.name=o),Ve("sw-baddr",o=>V.buyer.addr=o),Ve("sw-btin",o=>(V.buyer.tin=o,V.buyer.verified=!1),!0),Ve("sw-brno",o=>V.buyer.branchNo=o,!0);const n=document.getElementById("sw-rd");n&&(n.onclick=xm),ue().querySelectorAll("[data-add]").forEach(o=>o.onclick=()=>gm(+o.dataset.add)),ue().querySelectorAll("[data-q]").forEach(o=>o.onclick=()=>bm(+o.dataset.q,+o.dataset.d)),ue().querySelectorAll("[data-rm]").forEach(o=>o.onclick=()=>ym(+o.dataset.rm)),ue().querySelectorAll("[data-ln]").forEach(o=>{const i=+o.dataset.ln,r=o.dataset.f;o.oninput=()=>V.lines[i][r]=o.value,o.onblur=me});const a=document.getElementById("sw-addcustom");a&&(a.onclick=()=>(V.lines.push({desc:"",qty:1,price:0,disc:0,vat:!0,custom:!0}),me())),ue().querySelectorAll("[data-save]").forEach(o=>o.onchange=()=>V.lines[+o.dataset.save].save=o.checked),Ve("sw-hdisc",o=>V.hdisc=o,!0),Ve("sw-vat",o=>V.vatRate=o,!0),Ve("sw-wht",o=>V.whtRate=o,!0),ue().querySelectorAll("[data-ps]").forEach(o=>o.onclick=()=>(V.pay.status=o.dataset.ps,me()));const s=document.getElementById("sw-pm");s&&(s.onchange=()=>V.pay.method=s.value),Ve("sw-pdate",o=>V.pay.date=o),Ve("sw-paid",o=>V.pay.paidAmt=o),Ve("sw-idate",o=>V.issueDate=o),Ve("sw-ddate",o=>V.dueDate=o),ue().querySelectorAll("[data-cal]").forEach(o=>o.onclick=()=>(V.be=o.dataset.cal==="be",me())),ue().querySelectorAll("[data-paper]").forEach(o=>o.onclick=()=>(V.paper=o.dataset.paper,me())),ue().querySelectorAll("[data-dlang]").forEach(o=>o.onclick=()=>(V.docLang=o.dataset.dlang,me())),ue().querySelectorAll("[data-layout]").forEach(o=>o.onclick=()=>(V.layout=o.dataset.layout,me()))}function Xo(e){const n=qe+e;if(!(n<0||n>4)){if(e>0&&qe===4)return void Em();qe=n,me()}}function hm(e){V.buyer.type!==e&&(V.buyer.type=e,V.buyer.tin="",V.buyer.verified=!1,V.buyer.branchType="hq",V.buyer.branchNo="",me())}function gm(e){const n=Br()[e];if(!n)return;const a=$r(n),s=V.lines.find(o=>o.product_id===n.id);s?s.qty=(+s.qty||0)+1:V.lines.push({desc:a,qty:1,price:n.unit_price,disc:0,vat:n.vat_applicable,product_id:n.id}),me()}function bm(e,n){V.lines[e].qty=Math.max(0,(+V.lines[e].qty||0)+n),+V.lines[e].qty==0&&V.lines.splice(e,1),me()}function ym(e){V.lines.splice(e,1),me()}const wm=[["tax_invoice_receipt","individual","paid","cash"],["tax_invoice","company","unpaid","transfer"],["tax_invoice_receipt","individual","paid","transfer"],["tax_invoice_simple","anonymous","paid","cash"]];function km(e){const n=wm[e];if(!n)return;const[a,s,o,i]=n;V.docType=a,V.buyer={type:s,name:"",addr:"",tin:"",branchType:"hq",branchNo:""},V.pay={status:o,method:i,date:ss(),paidAmt:null},qe=0,me()}async function xm(){const e=V.buyer;if(!e.tin)return showToast(C("rdNeedTin"),"error");if(e.type==="company"){if(!/^\d{13}$/.test(e.tin))return showToast(C("rdCo13"),"error");const n=await Ju(e.tin,0);if(!n.found)return showToast(C("lookupFail"),"error");n.name&&(e.name=n.name),n.address&&(e.addr=n.address),e.branchType="hq",e.branchNo="",e.verified=!0}else{if(!(await Yu(e.tin)).valid)return showToast(C("verifyFail"),"error");e.verified=!0}me()}async function _m(){if(!V.lines.some(n=>(n.desc||"").trim()))return showToast(C("needLines"),"error");const e=await Lr(V);e.ok?(V.draftId=e.id||V.draftId,showToast(C("draftSaved"),"success"),window.dispatchEvent(new CustomEvent("pearnly:sales-changed"))):showToast(C("saveFail")+(e.error?" · "+e.error:""),"error")}async function Em(){const e=_r(V).filter(a=>a.req&&!a.pass);if(e.length)return showToast(C("blockers")+" "+e.map(a=>C(a.key)).join(", "),"error");if(!V.lines.some(a=>(a.desc||"").trim()))return showToast(C("needLines"),"error");const n=await Zu(V);n.ok&&n.id?(Im(n.id),window.dispatchEvent(new CustomEvent("pearnly:sales-changed"))):showToast(C("issueFail")+(n.error?" · "+n.error:""),"error")}function Im(e){ue().innerHTML=`<div class="sw-okwrap"><div class="sw-okbox">
        <div class="sw-okic">${ye.checkG}</div>
        <h3>${escapeHtml(C("okTitle"))}</h3>
        <div class="sw-okarch">${ye.checkG} ${escapeHtml(C("okArchived"))}</div>
        <div class="sw-okacts">
            <button class="btn btn-primary" id="sw-ok-view">${escapeHtml(C("viewSend"))}</button>
            <button class="btn btn-ghost" id="sw-ok-new">${escapeHtml(C("newOne"))}</button>
            <button class="btn btn-ghost" id="sw-ok-done" style="grid-column:1/-1">${escapeHtml(C("done"))}</button>
        </div></div></div>`,ue().style.display="flex",document.getElementById("sw-ok-done").onclick=os,document.getElementById("sw-ok-new").onclick=()=>{V=Sr(),qe=0,me()},document.getElementById("sw-ok-view").onclick=()=>{os(),window.openSalesDetail&&window.openSalesDetail(e)}}window.openSalesWizard=async function(){V=Sr(),qe=0;const e=typeof currentLang<"u"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";am(e),ue().innerHTML=`<div class="sw-wrap"><div class="sw-card"><div class="sx-state">${escapeHtml(C("s1h"))}…</div></div></div>`,ue().style.display="flex",await Ku(),me()};const Bm=`
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
`;$e("cmdk-mask",Bm);(function(){function e(c){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||c&&c.id&&String(c.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var u=window._userInfo,v=!1,f=!0,y=!1,b=!1;u&&(v=typeof canManageTeam=="function"?canManageTeam(u):!!(u.role==="owner"||u.is_super_admin),f=typeof shouldHideMoney=="function"?shouldHideMoney(u):u.role==="member"&&!u.is_super_admin,y=typeof isSuperAdmin=="function"?isSuperAdmin(u):!!u.is_super_admin,b=e(u)),document.querySelectorAll("[data-show-if-team]").forEach(function(g){g.style.display=v?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(g){g.style.display=f?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(g){g.style.display=y?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(g){g.style.display=b?"":"none"});var h=y||b;document.querySelectorAll("[data-show-if-special]").forEach(function(g){g.style.display=h?"":"none"})},window.renderAvatarMenu=function(u){if(u){var v=document.getElementById("avatar-btn"),f=document.getElementById("avatar-popup-name"),y=document.getElementById("avatar-popup-email");if(!(!v||!f||!y)){var b=(u.username||"").trim(),h=b.split("@")[0]||b||"—",g=(b.charAt(0)||"?").toUpperCase(),_=(u.avatar_url||"").trim();if(_){var w=_.replace(/"/g,"&quot;"),k=g.replace(/'/g,"\\'");v.innerHTML='<img src="'+w+'" alt="'+g+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+k+`'">`}else v.textContent=g;f.textContent=h,y.textContent=b||"—",v.setAttribute("title",b||"")}}};function n(){var c=document.getElementById("avatar-wrap"),u=document.getElementById("avatar-btn"),v=document.getElementById("avatar-popup");if(!c||!u||!v)return;function f(){v.classList.remove("show"),u.setAttribute("aria-expanded","false")}function y(){v.classList.add("show"),u.setAttribute("aria-expanded","true")}u.addEventListener("click",function(b){b.stopPropagation(),v.classList.contains("show")?f():y()}),document.addEventListener("click",function(b){v.classList.contains("show")&&!c.contains(b.target)&&f()}),v.addEventListener("click",function(b){var h=b.target.closest(".avatar-popup-item");if(h){var g=h.dataset.action;switch(f(),g){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var _=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(_||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var w=document.getElementById("help-modal");w&&(w.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=f}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(c){return c.style.display!=="none"})}function s(c){var u=a();u.forEach(function(v){v.classList.remove("focus")}),u[c]&&(u[c].classList.add("focus"),u[c].scrollIntoView({block:"nearest"}))}function o(c){var u=a();if(u.length){var v=u.findIndex(function(y){return y.classList.contains("focus")});v<0&&(v=0);var f=(v+c+u.length)%u.length;s(f)}}function i(c){c=(c||"").toLowerCase().trim();var u=0,v=window._userInfo,f=typeof isSuperAdmin=="function"?isSuperAdmin(v):!!(v&&v.is_super_admin),y=e(v);document.querySelectorAll(".cmdk-item").forEach(function(h){if(h.dataset.showIfAdmin==="1"&&!f){h.style.display="none";return}if(h.dataset.showIfTest==="1"&&!y){h.style.display="none";return}var g=(h.dataset.cmdkText||h.textContent||"").toLowerCase(),_=!c||g.indexOf(c)>=0;h.style.display=_?"":"none",h.classList.remove("focus"),_&&u++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(h){for(var g=h.nextElementSibling,_=!1;g&&!g.hasAttribute("data-cmdk-section");){if(g.classList&&g.classList.contains("cmdk-item")&&g.style.display!=="none"){_=!0;break}g=g.nextElementSibling}h.style.display=_?"":"none"});var b=document.getElementById("cmdk-empty");b&&(b.style.display=u===0?"flex":"none"),s(0)}window.openCmdk=function(){var u=document.getElementById("cmdk-mask");u&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),u.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var v=document.getElementById("cmdk-input");v&&(v.value="",i(""),v.focus(),s(0))},50))},window.closeCmdk=function(){var u=document.getElementById("cmdk-mask");u&&u.classList.remove("show")};function r(c){if(c){if(c.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var u=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(u||"即将上线","info")}return}var v=c.dataset.cmdkRoute,f=c.dataset.cmdkAction;if(window.closeCmdk(),v){typeof routeTo=="function"&&routeTo(v);return}if(f){if(f==="open-admin"){window.location.href="/admin/cost";return}if(f.indexOf("lang-")===0){var y=f.slice(5);typeof applyLang=="function"&&applyLang(y)}}}}function l(){var c=document.getElementById("cmdk-mask"),u=document.getElementById("cmdk-input"),v=document.getElementById("cmdk-body");if(!(!c||!u||!v)){c.addEventListener("click",function(b){b.target===c&&window.closeCmdk()});var f=document.getElementById("cmdk-esc-btn");f&&f.addEventListener("click",function(){window.closeCmdk()}),u.addEventListener("input",function(b){i(b.target.value)}),u.addEventListener("keydown",function(b){b.key==="ArrowDown"?(b.preventDefault(),o(1)):b.key==="ArrowUp"?(b.preventDefault(),o(-1)):b.key==="Enter"?(b.preventDefault(),r(c.querySelector(".cmdk-item.focus"))):b.key==="Escape"&&(b.preventDefault(),window.closeCmdk())}),v.addEventListener("click",function(b){var h=b.target.closest(".cmdk-item");h&&r(h)}),v.addEventListener("mousemove",function(b){var h=b.target.closest(".cmdk-item");!h||h.style.display==="none"||h.classList.contains("cmdk-item-locked")||(a().forEach(function(g){g.classList.remove("focus")}),h.classList.add("focus"))});var y=document.getElementById("topbar-search");y&&(y.addEventListener("click",function(){window.openCmdk()}),y.addEventListener("keydown",function(b){(b.key==="Enter"||b.key===" ")&&(b.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(c){if((c.metaKey||c.ctrlKey)&&(c.key==="k"||c.key==="K")){c.preventDefault(),window.openCmdk();return}if(c.key==="Escape"){var u=document.getElementById("cmdk-mask");if(u&&u.classList.contains("show")){window.closeCmdk();return}var v=document.getElementById("avatar-popup");v&&v.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var m=(navigator.userAgent||"").toLowerCase(),d=m.indexOf("mac")>=0||m.indexOf("iphone")>=0||m.indexOf("ipad")>=0;d||document.body.classList.add("is-windows")}catch{}function p(){n(),l(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",p):p()})();(function(){function n(f){return String(f??"").replace(/[&<>"']/g,function(y){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[y]})}function a(f){if(!f||isNaN(f))return"";var y=Number(f);return y<1024?y+" B":y<1024*1024?(y/1024).toFixed(1)+" KB":(y/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(f){var y=f.target.closest&&f.target.closest(".recon-collapse-head");if(y&&!(f.target.closest("button")||f.target.closest("a"))){var b=y.closest(".recon-collapse");if(b){var h=b.getAttribute("data-collapsed")==="true";b.setAttribute("data-collapsed",h?"false":"true"),h&&(b.id==="vex-summary-collapse"&&p(),b.id==="vex-detail-collapse"&&c())}}}),document.addEventListener("keydown",function(f){if(!(f.key!=="Enter"&&f.key!==" ")){var y=f.target.closest&&f.target.closest(".recon-collapse-head");y&&(f.preventDefault(),y.click())}});var s={vat:"",gl:""};window._glvClearPreviewSearch=function(){s.vat="",s.gl=""};var o='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){m("vat"),m("gl")}function l(f){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(f)||[]}catch{}var y=document.getElementById(f==="vat"?"glv-vat-input":"glv-gl-input");return y&&y.files?Array.from(y.files):[]}function m(f){var y=document.getElementById(f==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(y){var b=l(f),h=f==="vat"?"glv-up-vat-title":"glv-up-gl-title",g=f==="vat"?"① 销项税报告":"② 总账 GL",_=window.t&&window.t(h)||g,w=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),k=n(window.t&&window.t("vex-preview-clear-all")||"全清"),x=s[f]||"",E=b.length;y.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(_)+' <span class="vex-pp-col-count">'+E+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+f+'" type="text" placeholder="'+w+'" value="'+n(x)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+f+'" type="button">'+k+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+f+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+f+'-pg"></div>';var I=document.getElementById("glv-pp-search-"+f);I&&I.addEventListener("input",function(L){s[f]=L.target.value,d(f)});var B=document.getElementById("glv-pp-clearall-"+f);B&&B.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(f)}),d(f)}}function d(f){var y=document.getElementById("glv-pp-"+f+"-list"),b=document.getElementById("glv-pp-"+f+"-pg");if(y){var h=l(f),g=(s[f]||"").toLowerCase(),_=h.map(function(x,E){return{f:x,i:E}}),w=g?_.filter(function(x){return x.f.name.toLowerCase().indexOf(g)>=0}):_;if(y.innerHTML=w.map(function(x){var E=x.f;return'<div class="vex-pp-file-row">'+o+'<span class="vex-pp-fi-name" title="'+n(E.name)+'">'+n(E.name)+'</span><span class="vex-pp-fi-size">'+a(E.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+f+'" data-idx="'+x.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),y.querySelectorAll(".vex-pp-fi-del").forEach(function(x){x.addEventListener("click",function(){var E=x.dataset.kind,I=parseInt(x.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(E,isNaN(I)?null:I)})}),b){var k=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";b.textContent=k.replace("{n}",w.length).replace("{m}",w.length)}}}function p(){var f=function(b,h){var g=document.getElementById(b);g&&(g.textContent=h==null?"—":String(h))},y=window._vexLastTask||{};f("vex-sum-total",y.total),f("vex-sum-matched",y.matched),f("vex-sum-diff",y.diff),f("vex-sum-incomplete",y.incomplete),f("vex-sum-cash",y.cash),document.getElementById("vex-summary-sub")}function c(){var f=window._vexLastTask&&window._vexLastTask.diff_rows||[],y=document.getElementById("vex-detail-tbody"),b=document.getElementById("vex-detail-table"),h=document.getElementById("vex-detail-empty");if(!(!y||!b||!h)){if(f.length===0){b.style.display="none",h.style.display="";return}h.style.display="none",b.style.display="";var g=f.map(function(w){return'<tr><td class="recon-detail-cell-mono">'+n(w.invoice_no||"")+"</td><td>"+n(w.field||"")+"</td><td>"+n(w.report_value||"")+"</td><td>"+n(w.invoice_value||"")+"</td><td>"+n(w.kind||"")+"</td></tr>"}).join("");y.innerHTML=g;var _=document.getElementById("vex-detail-sub");_&&(_.textContent=String(f.length))}}function u(){var f=document.getElementById("glv-toggle-preview");f&&!f._reconBound&&(f._reconBound=!0,f.addEventListener("click",function(){var y=document.getElementById("glv-preview-panel"),b=document.getElementById("glv-toggle-preview-label"),h=y&&y.style.display!=="none";y&&(y.style.display=h?"none":""),f.classList.toggle("open",!h),b&&(b.textContent=h?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),h||r()})),["glv-vat-input","glv-gl-input"].forEach(function(y){var b=document.getElementById(y);!b||b._reconWatched||(b._reconWatched=!0,b.addEventListener("change",function(){var h=document.getElementById("glv-preview-panel");h&&h.style.display!=="none"&&r()}))})}function v(){var f=document.getElementById("vex-summary-collapse"),y=document.getElementById("vex-detail-collapse");f&&(f.style.display=""),y&&(y.style.display=""),p(),c()}window._fillVexSummary=p,window._fillVexDetail=c,window._onVexResultShown=v,document.addEventListener("DOMContentLoaded",function(){u()}),setTimeout(u,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var f=document.getElementById("glv-preview-panel");f&&f.style.display!=="none"&&r();var y=document.getElementById("glv-toggle-preview-label"),b=document.getElementById("glv-toggle-preview");y&&b&&(y.textContent=b.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:p,fillVexDetail:c}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(l=>{l.addEventListener("click",()=>{i.forEach(u=>u.classList.remove("active")),l.classList.add("active");const m=l.dataset.reconTab,d=document.getElementById("recon-pane-bank"),p=document.getElementById("recon-pane-sale-vat"),c=document.getElementById("recon-pane-gl-vat");d&&(d.style.display=m==="bank"?"":"none"),p&&(p.style.display=m==="sale-vat"?"":"none"),c&&(c.style.display=m==="gl-vat"?"":"none"),m==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),m==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const l=document.createElement("button");return l.id="settings-modal-close",l.className="settings-modal-close",l.setAttribute("aria-label","close"),l.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(l,i.firstChild),l.addEventListener("click",o),r.addEventListener("click",m=>{m.target===r&&o()}),r}function s(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(m){console.warn("renderSettings:",m)}let l=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');l&&l.click()},50)}function o(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=s,window.closeSettingsModal=o,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&o()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&s()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&s()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();const qa=1e3,Ra=30,Ys=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,te=e=>document.getElementById(e);function At(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function Me(e){const n={"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"};return String(e??"").replace(/[&<>"']/g,a=>n[a])}function Cr(e){return e<1024?e+" B":e<1024*1024?(e/1024).toFixed(1)+" KB":(e/1024/1024).toFixed(1)+" MB"}const A={invoiceFiles:[],reportFiles:[],running:!1,vexAllRows:[],previewLimitInv:50,previewLimitRep:50,previewSearchInv:"",previewSearchRep:"",vexPage:1};async function Wn(){try{const e=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:At()});if(!e.ok)return;const a=(await e.json()).kpi||{};[["vex-kpi-month-val",a.this_month],["vex-kpi-running-val",a.running],["vex-kpi-done-val",a.done],["vex-kpi-failed-val",a.failed]].forEach(([s,o])=>{const i=document.getElementById(s);i&&(i.textContent=o??0)})}catch{}}async function Kn(){try{const e=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:At()});if(!e.ok)return;const n=await e.json();ra(n.rows||[])}catch{}}const Ot=10;function Tr(){var e=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(A.vexPage=1,ra(A.vexAllRows),!!e){var n=document.getElementById("vex-task-tbody");n&&n.querySelectorAll("tr").forEach(function(a){a.dataset.taskId&&(a.style.display=a.textContent.toLowerCase().indexOf(e)>=0?"":"none")})}}function ra(e){A.vexAllRows=e||A.vexAllRows;const n=document.getElementById("vex-task-tbody");if(!n)return;if(!A.vexAllRows.length){n.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",Zo(0);return}const a=Math.ceil(A.vexAllRows.length/Ot);A.vexPage>a&&(A.vexPage=a);const s=(A.vexPage-1)*Ot;Lm(A.vexAllRows.slice(s,s+Ot)),Zo(A.vexAllRows.length)}function Zo(e){const n=document.getElementById("vex-task-pager"),a=document.getElementById("vex-task-pager-info"),s=document.getElementById("vex-task-prev"),o=document.getElementById("vex-task-next");if(!n)return;if(e<=Ot){n.style.display="none";return}n.style.display="";const i=Math.ceil(e/Ot);a&&(a.textContent=A.vexPage+" / "+i),s&&(s.disabled=A.vexPage<=1),o&&(o.disabled=A.vexPage>=i)}function Lm(e){const n=document.getElementById("vex-task-tbody");if(!n)return;const a={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},s={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},o='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',i='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';n.innerHTML=e.map(r=>{const l=r.created_at?new Date(r.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",m=r.period||"—",d=r.matched_count!=null?r.matched_count+" ✓ · "+r.mismatched_count+" ⚠":"—",p=r.mismatch_amount!=null?"฿ "+Number(r.mismatch_amount).toLocaleString():"—",c=r.elapsed_seconds!=null?r.elapsed_seconds.toFixed(1)+" s":"—",u=r.status||"pending",v=r.client_name&&r.client_name!=="client"?r.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${Me(r.id)}" style="cursor:pointer">
            <td>${l}</td>
            <td>${Me(v)}</td>
            <td>${Me(m)}</td>
            <td>${(r.invoice_count||0)+" / "+(r.report_count||0)}</td>
            <td>${d}</td>
            <td>${p}</td>
            <td><span class="badge ${s[u]||"badge-gray"}">${a[u]||u}</span></td>
            <td>${c}</td>
            <td><div class="vex-task-actions">
                <button class="vex-task-dl-btn" data-task-id="${Me(r.id)}" title="${t("hist_export")||"导出"}">${o}</button>
                <button class="vex-task-del-btn" data-task-id="${Me(r.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${i}</button>
            </div></td>
        </tr>`}).join(""),n.querySelectorAll(".vex-task-dl-btn").forEach(r=>{r.addEventListener("click",async l=>{l.stopPropagation();const m=r.dataset.taskId;try{const d=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(m)+"/download",{credentials:"include",headers:At()});if(d.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!d.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const p=await d.blob(),u=(d.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),v=u?decodeURIComponent(u[1]):"vat_recon_"+m+".xlsx",f=URL.createObjectURL(p),y=document.createElement("a");y.href=f,y.download=v,y.click(),setTimeout(()=>URL.revokeObjectURL(f),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),n.querySelectorAll(".vex-task-del-btn").forEach(r=>{r.addEventListener("click",l=>{l.stopPropagation(),Sm(r.dataset.taskId)})}),Tr()}function $m(){var e=document.getElementById("vex-task-prev"),n=document.getElementById("vex-task-next");e&&!e._vexBound&&(e._vexBound=!0,e.addEventListener("click",function(){A.vexPage>1&&(A.vexPage--,ra())})),n&&!n._vexBound&&(n._vexBound=!0,n.addEventListener("click",function(){var a=Math.ceil(A.vexAllRows.length/Ot);A.vexPage<a&&(A.vexPage++,ra())}))}async function Sm(e){const n=t("vex-task-delete-confirm-title")||"删除对账任务?",a=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(a,{title:n,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const o=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(e),{method:"DELETE",credentials:"include",headers:At()});if(!o.ok)throw new Error(o.status);showToast(t("vex-task-delete-ok")||"已删除","success"),Kn(),Wn()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function Hr(e){const n=window._currentLang||"th",a={zh:`已忽略 ${e} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${e} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${e} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${e} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(a[n]||a.th,"warn")}function Cm(e){const n=new Set(A.invoiceFiles.map(s=>s.name+"|"+s.size));let a=0;for(const s of e){if(!Ys.test(s.name)){a++;continue}const o=s.name+"|"+s.size;if(!n.has(o)&&(n.add(o),A.invoiceFiles.push(s),A.invoiceFiles.length>=qa))break}a>0&&Hr(a),A.invoiceFiles.length>qa&&(A.invoiceFiles=A.invoiceFiles.slice(0,qa),showToast(t("vex-toast-cap-inv"),"warn")),wt()}function Tm(e){const n=new Set(A.reportFiles.map(s=>s.name+"|"+s.size));let a=0;for(const s of e){if(!Ys.test(s.name)){a++;continue}const o=s.name+"|"+s.size;if(!n.has(o)&&(n.add(o),A.reportFiles.push(s),A.reportFiles.length>=Ra))break}a>0&&Hr(a),A.reportFiles.length>Ra&&(A.reportFiles=A.reportFiles.slice(0,Ra),showToast(t("vex-toast-cap-rep"),"warn")),wt()}function Mr(e){A.invoiceFiles.splice(e,1),wt()}function Ar(e){A.reportFiles.splice(e,1),wt()}function wt(){const e=te("vex-list-invoice"),n=te("vex-list-report"),a=te("vex-count-invoice"),s=te("vex-count-report");a&&(a.textContent=A.invoiceFiles.length),s&&(s.textContent=A.reportFiles.length);const o=(l,m,d)=>`<div class="vex-fi">
        <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
        <span class="vex-fi-n" title="${Me(l.name)}">${Me(l.name)}</span>
        <span class="vex-fi-s">${Cr(l.size)}</span>
        <button class="vex-fi-x" type="button" data-vex-kind="${d}" data-vex-idx="${m}" aria-label="remove">×</button>
    </div>`;e&&(e.innerHTML=A.invoiceFiles.map((l,m)=>o(l,m,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),n&&(n.innerHTML=A.reportFiles.map((l,m)=>o(l,m,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(l=>{l.addEventListener("click",m=>{const d=l.dataset.vexKind,p=parseInt(l.dataset.vexIdx,10);d==="inv"?Mr(p):Ar(p)})});const i=A.invoiceFiles.length>0&&A.reportFiles.length>0;te("vex-build").disabled=!i||A.running;const r=te("vex-action-info");r&&(!A.invoiceFiles.length||!A.reportFiles.length?(r.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",r.className="vex-action-info muted"):(r.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",A.invoiceFiles.length).replace("{b}",A.reportFiles.length),r.className="vex-action-info ok")),is()}const Hm='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',Mm='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',Am='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function is(){const e=te("vex-preview-panel");if(!e||e.style.display==="none")return;Qo("inv"),Qo("rep");const n=te("vex-pp-guide");n&&(n.style.display=A.invoiceFiles.length>100?"flex":"none")}function Qo(e){const n=te(e==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!n)return;const a=e==="inv"?A.invoiceFiles:A.reportFiles,s=e==="inv"?A.previewSearchInv:A.previewSearchRep,o=t(e==="inv"?"vex-preview-invoice":"vex-preview-report")||(e==="inv"?"销售发票":"VAT 报告"),i=Me(t("vex-preview-search")||"搜索文件名..."),r=Me(t("vex-preview-clear-all")||"全清");n.innerHTML=`
        <div class="vex-pp-col-title">
            <span class="vex-pp-col-name">${Me(o)} <span class="vex-pp-col-count">${a.length}</span></span>
        </div>
        <div class="vex-pp-search-row">
            <input class="vex-pp-search" id="vex-pp-search-${e}" type="text"
                   placeholder="${i}" value="${Me(s)}" autocomplete="off">
            <button class="vex-pp-clear-btn" id="vex-pp-clearall-${e}" type="button">${r}</button>
        </div>
        <div class="vex-pp-file-list" id="vex-pp-${e}-list"></div>
        <div class="vex-pp-pagination" id="vex-pp-${e}-pg"></div>`;const l=te("vex-pp-search-"+e);l&&l.addEventListener("input",d=>{e==="inv"?(A.previewSearchInv=d.target.value,A.previewLimitInv=50):(A.previewSearchRep=d.target.value,A.previewLimitRep=50),rs(e)});const m=te("vex-pp-clearall-"+e);m&&m.addEventListener("click",()=>{e==="inv"?(A.invoiceFiles=[],A.previewSearchInv="",A.previewLimitInv=50):(A.reportFiles=[],A.previewSearchRep="",A.previewLimitRep=50),wt()}),rs(e)}function rs(e){const n=te("vex-pp-"+e+"-list"),a=te("vex-pp-"+e+"-pg");if(!n)return;const s=e==="inv"?A.invoiceFiles:A.reportFiles,o=e==="inv"?A.previewSearchInv:A.previewSearchRep,i=e==="inv"?A.previewLimitInv:A.previewLimitRep,r=e==="inv"?Hm:Mm,l=s.map((p,c)=>({f:p,i:c})),m=o?l.filter(({f:p})=>p.name.toLowerCase().includes(o.toLowerCase())):l,d=m.slice(0,i);if(n.innerHTML=d.map(({f:p,i:c})=>`
        <div class="vex-pp-file-row">
            ${r}
            <span class="vex-pp-fi-name" title="${Me(p.name)}">${Me(p.name)}</span>
            <span class="vex-pp-fi-size">${Cr(p.size)}</span>
            <button class="vex-pp-fi-del" type="button" data-kind="${e}" data-ridx="${c}" aria-label="remove">${Am}</button>
        </div>`).join("")+`<div id="vex-pp-sentinel-${e}" style="height:1px;flex-shrink:0"></div>`,n.querySelectorAll(".vex-pp-fi-del").forEach(p=>{p.addEventListener("click",()=>{const c=parseInt(p.dataset.ridx,10);p.dataset.kind==="inv"?Mr(c):Ar(c)})}),a){const p=t("vex-preview-count")||"显示前 {n} / 共 {m}";a.textContent=p.replace("{n}",d.length).replace("{m}",m.length)}Pm(e,m.length)}function Pm(e,n){if((e==="inv"?A.previewLimitInv:A.previewLimitRep)>=n)return;const s=te("vex-pp-sentinel-"+e),o=te("vex-pp-"+e+"-list");if(!s||!o)return;const i=new IntersectionObserver(r=>{r[0].isIntersecting&&(i.disconnect(),e==="inv"?A.previewLimitInv+=50:A.previewLimitRep+=50,rs(e))},{root:o,threshold:.8});i.observe(s)}function ei(e,n,a,s){const o=te(e),i=te(n);!o||!i||(o.addEventListener("click",()=>i.click()),o.addEventListener("keydown",r=>{(r.key==="Enter"||r.key===" ")&&(r.preventDefault(),i.click())}),o.addEventListener("dragover",r=>{r.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",()=>o.classList.remove("drag-over")),o.addEventListener("drop",r=>{r.preventDefault(),o.classList.remove("drag-over");const m=Array.from(r.dataTransfer.files).filter(d=>Ys.test(d.name));if(!m.length){showToast(t("vex-toast-bad-ext"),"error");return}a(m)}),i.addEventListener("change",()=>{const r=Array.from(i.files);a(r),i.value=""}))}(function(){async function e(){if(A.running||!A.invoiceFiles.length||!A.reportFiles.length)return;A.running=!0,te("vex-build").disabled=!0,te("vex-progress").style.display="flex";var r=document.getElementById("vex-download");r&&(r.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(p){var c=document.getElementById(p);c&&(c.style.display="none")});const l=Date.now();te("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",te("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",A.invoiceFiles.length).replace("{b}",A.reportFiles.length);const m=setInterval(()=>{const p=Math.floor((Date.now()-l)/1e3);te("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",p).replace("{a}",A.invoiceFiles.length).replace("{b}",A.reportFiles.length)},1e3);try{const p=new FormData;for(const L of A.invoiceFiles)p.append("invoices",L);for(const L of A.reportFiles)p.append("reports",L);const c=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";p.append("lang",c);const u=localStorage.getItem("mrpilot_token")||"",v=await fetch("/api/vat_excel/submit",{method:"POST",headers:At(),body:p});let f=null;try{f=await v.json()}catch{f=null}if(!v.ok||!f||!f.ok||!f.job_id)throw clearInterval(m),new Error(f&&f.detail||"HTTP "+v.status);const y=te("vex-progress-sub"),b=await window._reconPollJob(f.job_id,u,{onProgress:L=>{y&&(y.textContent=window._reconProgressText(L,c))}});if(clearInterval(m),!b||b.status!=="done"||!b.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const h=b.result_id;let g=0;const _=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(h)+"/download",{headers:At()});if(!_.ok)throw new Error("HTTP "+_.status);const k=(_.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),x=k&&k[1]||"vat_recon_"+Date.now()+".xlsx",E=await _.blob(),I=URL.createObjectURL(E),B=te("vex-download");B.href=I,B.download=x;try{const L=document.createElement("a");L.href=I,L.download=x,document.body.appendChild(L),L.click(),setTimeout(()=>L.remove(),100)}catch{}te("vex-progress").style.display="none";var d=document.getElementById("vex-download");d&&(d.style.display=""),h&&(g=await s(h)),window._onVexResultShown&&window._onVexResultShown(),g>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",g),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),Wn(),setTimeout(Kn,800)}catch(p){clearInterval(m),te("vex-progress").style.display="none";const c=(t("vex-toast-fail")||"生成失败")+": "+(p.message||p);showToast(c,"error")}finally{A.running=!1,te("vex-build").disabled=!1}}function n(){A.invoiceFiles=[],A.reportFiles=[];var r=document.getElementById("vex-download");r&&(r.style.display="none"),wt()}function a(r){if(r==null)return"—";var l=parseFloat(r);return isNaN(l)?"—":l.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function s(r){try{var l=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(r),{headers:At()});if(!l.ok)throw new Error(l.status);var m=await l.json(),d=m.raw_data_json;if(typeof d=="string")try{d=JSON.parse(d)}catch{d={}}d=d||{};var p=d.rows||[],c=[];p.forEach(function(f){f.kind==="invoice_orphan"?c.push({invoice_no:f.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:a(f.amount_inv),kind:f.kind}):f.kind==="report_orphan"?c.push({invoice_no:f.invoice_no||"",field:"仅报告有",report_value:a(f.amount_rep),invoice_value:"—",kind:f.kind}):f.dims&&Object.keys(f.dims).length>0&&Object.keys(f.dims).forEach(function(y){var b=String(f.dims[y]||""),h=b.split(" ≠ ");c.push({invoice_no:f.invoice_no||"",field:y,report_value:h[0]||b,invoice_value:h.length>1?h[1]:"—",kind:"diff"})})});var u=p.filter(function(f){return f.kind==="matched_cash"}).length,v=Math.max(0,parseInt(d.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:d.n_total||0,matched:d.n_ok||0,diff:d.n_diff||0,incomplete:v,cash:u,diff_rows:c,task_id:r},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),v}catch{return 0}}function o(){const r=document.getElementById("vex-pane");r&&r.querySelectorAll("[data-i18n]").forEach(l=>{const m=t(l.dataset.i18n);m&&(l.textContent=m)}),wt(),Kn()}function i(){ei("vex-drop-invoice","vex-input-invoice",Cm),ei("vex-drop-report","vex-input-report",Tm);const r=te("vex-build"),l=te("vex-reset");r&&r.addEventListener("click",e),l&&l.addEventListener("click",n),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(p=>{p.addEventListener("click",()=>{Wn(),Kn()})}),$m();const m=document.getElementById("vex-task-search");m&&m.addEventListener("input",Tr);const d=document.getElementById("vex-toggle-preview");d&&d.addEventListener("click",()=>{const p=te("vex-preview-panel"),c=te("vex-toggle-preview-label"),u=p&&p.style.display!=="none";p&&(p.style.display=u?"none":""),d&&d.classList.toggle("open",!u),c&&(c.textContent=u?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),u||is()}),wt(),Wn()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",i):i(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",o),window.subscribeI18n("vex-preview-panel",is))})();const J={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},W=e=>document.getElementById(e),Pr=()=>localStorage.getItem("mrpilot_token")||"",Xt=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",jt=()=>({Authorization:"Bearer "+Pr()}),ti={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},ie=e=>(ti[Xt()]||ti.th)[e]||e;function jm(e){const n=Xt(),s={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[e];return s?s[n]||s.th||s.en:ie("error")||"Error"}const yn=e=>e==null||isNaN(e)?"":Number(e).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function Js(e){W("glv-kpi-matched")&&(W("glv-kpi-matched").textContent=e&&e.matched!=null?e.matched:"—"),W("glv-kpi-diff")&&(W("glv-kpi-diff").textContent=e&&e.diff!=null?e.diff:"—"),W("glv-kpi-unmatched")&&(W("glv-kpi-unmatched").textContent=e&&e.unmatched!=null?e.unmatched:"—")}function Dm(e){if(!e)return"";try{const n=new Date(e);if(isNaN(n.getTime()))return e;const a=s=>String(s).padStart(2,"0");return n.getFullYear()+"-"+a(n.getMonth()+1)+"-"+a(n.getDate())+" "+a(n.getHours())+":"+a(n.getMinutes())}catch{return e}}function ni(e,n,a,s){const o=W(e),i=W(n),r=W(a);if(!o||!i||!r)return;const l=m=>{if(!m||!m.length)return;const d=Array.isArray(J[s])?J[s].slice():[],p=new Set(d.map(c=>c.name+"|"+c.size));for(const c of m){if(!c)continue;const u=c.name+"|"+c.size;p.has(u)||(d.push(c),p.add(u))}J[s]=d,jr(r,d),In(),Tn(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};o.addEventListener("click",()=>i.click()),o.addEventListener("keydown",m=>{(m.key==="Enter"||m.key===" ")&&(m.preventDefault(),i.click())}),i.addEventListener("change",()=>{l(Array.from(i.files||[])),i.value=""}),o.addEventListener("dragover",m=>{m.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",()=>o.classList.remove("drag-over")),o.addEventListener("drop",m=>{m.preventDefault(),o.classList.remove("drag-over");const d=m.dataTransfer&&m.dataTransfer.files?Array.from(m.dataTransfer.files):[];l(d)})}function jr(e,n){if(!e)return;if(!n||n.length===0){e.textContent="";return}const a=n.reduce((s,o)=>s+Math.round(o.size/1024),0);if(n.length===1)e.textContent=n[0].name+"  ("+a+" KB)";else{const s=window.t&&window.t("glv-files-count")||"{n} 个文件";e.textContent=s.replace("{n}",n.length)+"  ("+a+" KB)"}}function ht(e){const n=J[e];return Array.isArray(n)?n:n?[n]:[]}function In(){const e=W("btn-glv-run");if(!e)return;const n=ht("glFile").length>0&&ht("vatFile").length>0;e.disabled=!n||J.running}function Tn(){const e=W("glv-status");if(!e||J.running)return;const n=ht("vatFile").length,a=ht("glFile").length;n===0&&a===0?(e.className="vex-action-info muted",e.innerHTML="<span>"+ie("hint_need_both")+"</span>"):n>0&&a>0?(e.className="vex-action-info ok",e.innerHTML="<span>"+ie("hint_ready")+"</span>"):(e.className="vex-action-info muted",e.innerHTML="<span>"+ie("hint_need_one_more")+"</span>")}function qm(e,n){const a=e==="vat"?"vatFile":"glFile",s=e==="vat"?"glv-vat-input":"glv-gl-input",o=e==="vat"?"glv-vat-name":"glv-gl-name",i=ht(a);n==null?J[a]=[]:J[a]=i.filter((l,m)=>m!==n);const r=W(s);r&&(r.value=""),jr(W(o),ht(a)),In(),Tn(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function Rm(){J.glFile=[],J.vatFile=[],J.currentTaskId=null,J.lastDetail=[],J.lastSummary=null;const e=W("glv-vat-input");e&&(e.value="");const n=W("glv-gl-input");n&&(n.value="");const a=W("glv-vat-name");a&&(a.textContent="");const s=W("glv-gl-name");s&&(s.textContent="");const o=W("glv-result");o&&(o.style.display="none");const i=W("glv-kpi-strip");i&&(i.style.display="none"),In(),Tn(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function Xs(e){const n=W("glv-tbody");if(!n)return;Nm(e.length),n.innerHTML="";const a=ie("not_found"),s=document.createDocumentFragment();e.forEach(o=>{const i=document.createElement("tr"),r=(c,u)=>{const v=document.createElement("td");return u&&(v.className=u),v.textContent=c,v},l=o.gl_amount===null||o.gl_amount===void 0,m=o.diff;let d="glv-num",p="glv-num";l?(p+=" glv-cell-missing",d+=" glv-cell-missing"):Math.abs(m||0)<.005?d+=" glv-cell-ok":d+=" glv-cell-diff",i.appendChild(r(o.doc_no||"","glv-doc")),i.appendChild(r(o.date||"","")),i.appendChild(r(o.customer_name||"","")),i.appendChild(r(yn(o.vat_amount),"glv-num")),i.appendChild(r(l?a:yn(o.gl_amount),p)),i.appendChild(r(l?a:yn(o.diff),d)),i.appendChild(r(o.account_codes||"","glv-doc")),s.appendChild(i)}),n.appendChild(s)}function Zs(e){const n=W("glv-summary-table")&&W("glv-summary-table").querySelector("tbody");if(!n)return;n.innerHTML="",[{label:ie("s_gl_total"),amount:e.gl_total,emph:!0,items:[],negate:!1},{label:ie("s_minus_gl_cr"),amount:-(e.gl_only_credit||0),emph:!1,items:e.gl_only_credit_items||[],negate:!0},{label:ie("s_plus_gl_dr"),amount:e.gl_only_debit||0,emph:!1,items:e.gl_only_debit_items||[],negate:!1},{label:ie("s_plus_vat_p"),amount:e.vat_only_positive||0,emph:!1,items:e.vat_only_positive_items||[],negate:!1},{label:ie("s_minus_vat_n"),amount:e.vat_only_negative||0,emph:!1,items:e.vat_only_negative_items||[],negate:!1},{label:ie("s_vat_total"),amount:e.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:s,amount:o,emph:i,items:r,negate:l})=>{const m=document.createElement("tr");m.className=i?"glv-summary-total":"glv-summary-sect";const d=document.createElement("td"),p=document.createElement("td");d.textContent=s,p.textContent=i?yn(o):"",m.appendChild(d),m.appendChild(p),n.appendChild(m),(r||[]).forEach(c=>{const u=document.createElement("tr");u.className="glv-summary-item";const v=document.createElement("td"),f=document.createElement("td"),y=[c.doc_no,c.date,c.name].filter(Boolean);v.textContent="· "+y.join("  ·  ");const b=l?-(c.amount||0):c.amount||0;f.textContent=yn(b),u.appendChild(v),u.appendChild(f),n.appendChild(u)})})}async function Fm(e){try{const a=await(await fetch("/api/recon/gl-vat/"+e,{headers:jt()})).json();if(!a||!a.ok)throw new Error("load_failed");J.currentTaskId=e,J.lastDetail=a.detail||[],J.lastSummary=a.summary||{},Js(a.stats||{}),Xs(J.lastDetail),Zs(J.lastSummary);const s=W("glv-result");s&&(s.style.display=""),Dr(),window.scrollTo({top:s?s.offsetTop-80:0,behavior:"smooth"})}catch(n){console.error("[gl-vat] load task failed:",n),alert(ie("error")+": "+(n.message||n))}}function Dr(){var e=W("glv-kpi-strip");e&&(e.style.display="");var n=W("glv-section-summary");n&&n.setAttribute("data-collapsed","false");var a=W("glv-section-detail");a&&a.setAttribute("data-collapsed","false")}function zm(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(e=>{const n=e.getAttribute("data-toggle"),a=document.getElementById(n);if(!a)return;const s=o=>{if(o.target&&o.target.closest("button")!==null&&!o.target.classList.contains("glv-section-head"))return;const i=a.getAttribute("data-collapsed")==="true";a.setAttribute("data-collapsed",i?"false":"true")};e.addEventListener("click",s),e.addEventListener("keydown",o=>{(o.key==="Enter"||o.key===" ")&&(o.preventDefault(),s(o))})})}function Nm(e){const n=W("glv-detail-count");n&&(n.textContent=e!=null?String(e):"")}const dn=10;var Ft=[],Re=1;function Om(){Re=1,la();var e=((W("glv-hist-search")||{}).value||"").trim().toLowerCase();if(e){var n=W("glv-history-tbody");n&&n.querySelectorAll("tr").forEach(function(a){a.dataset.taskId&&(a.style.display=a.textContent.toLowerCase().indexOf(e)>=0?"":"none")})}}function la(){const e=W("glv-history-table-wrap"),n=W("glv-history-empty"),a=W("glv-history-tbody"),s=W("glv-history-pager"),o=W("glv-history-pager-info"),i=W("glv-history-prev"),r=W("glv-history-next");if(!a)return;if(a.innerHTML="",!Ft.length){e&&(e.style.display="none"),n&&(n.style.display=""),s&&(s.style.display="none");return}e&&(e.style.display=""),n&&(n.style.display="none");const l=Math.ceil(Ft.length/dn);Re>l&&(Re=l);const m=(Re-1)*dn,d=Ft.slice(m,m+dn);s&&(s.style.display=Ft.length>dn?"":"none",o&&(o.textContent=Re+" / "+l),i&&(i.disabled=Re<=1),r&&(r.disabled=Re>=l)),d.forEach(c=>{const u=document.createElement("tr");u.dataset.taskId=c.id;const v=document.createElement("td");v.textContent=Dm(c.created_at);const f=document.createElement("td");f.className="glv-history-file",f.title=(c.vat_filename||"")+" + "+(c.gl_filename||""),f.textContent=(c.vat_filename||"?")+" + "+(c.gl_filename||"?");const y=document.createElement("td");y.className="glv-num",y.textContent=(c.vat_row_count||0)+" / "+(c.gl_row_count||0);const b=document.createElement("td");b.className="glv-num",b.textContent=c.matched_count||0;const h=document.createElement("td");h.className="glv-num",h.textContent=c.diff_count||0;const g=document.createElement("td");g.className="glv-num",g.textContent=c.unmatched_count||0;const _=document.createElement("td");_.className="glv-history-actions";const w=(I,B,L,$)=>{const S=document.createElement("button");return S.type="button",L&&(S.className=L),S.title=B,S.setAttribute("aria-label",B),S.innerHTML=I,S.onclick=$,S},k='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',x='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',E='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';_.appendChild(w(k,ie("hist_load"),"",()=>Fm(c.id))),_.appendChild(w(x,ie("hist_export"),"",()=>Um(c.id))),_.appendChild(w(E,ie("hist_delete"),"glv-del",()=>Gm(c.id))),[v,f,y,b,h,g,_].forEach(I=>u.appendChild(I)),a.appendChild(u)})}function Vm(){var e=W("glv-history-prev"),n=W("glv-history-next");e&&!e._glvBound&&(e._glvBound=!0,e.addEventListener("click",function(){Re>1&&(Re--,la())})),n&&!n._glvBound&&(n._glvBound=!0,n.addEventListener("click",function(){var a=Math.ceil(Ft.length/dn);Re<a&&(Re++,la())}))}async function Vt(){try{const n=await(await fetch("/api/recon/gl-vat/tasks",{headers:jt()})).json();Ft=n&&n.tasks||[],Re=1,la(),Vm()}catch(e){console.error("[gl-vat] history load failed:",e)}}async function Um(e){try{const n="/api/recon/gl-vat/"+e+"/export?lang="+encodeURIComponent(Xt()),a=await fetch(n,{headers:jt()});if(!a.ok)throw new Error("HTTP "+a.status);const s=await a.blob(),o=document.createElement("a");o.href=URL.createObjectURL(s),o.download="GL_VAT_recon_"+e+".xlsx",document.body.appendChild(o),o.click(),setTimeout(()=>{URL.revokeObjectURL(o.href),o.remove()},200)}catch(n){console.error("[gl-vat] exportTask failed:",n),typeof showToast=="function"&&showToast(ie("error")+": "+(n.message||n),"error")}}async function Gm(e){let n;if(typeof window.showConfirm=="function"?n=await window.showConfirm(ie("confirm_delete"),{danger:!0}):n=confirm(ie("confirm_delete")),!!n)try{const a=await fetch("/api/recon/gl-vat/"+e,{method:"DELETE",headers:jt()});if(!a.ok)throw new Error("HTTP "+a.status);Vt()}catch(a){console.error("[gl-vat] delete failed:",a),typeof showToast=="function"&&showToast(ie("error")+": "+(a.message||a),"error")}}async function Wm(){if(!J.glFile||!J.vatFile){typeof showToast=="function"&&showToast(ie("need_files"),"warn");return}J.running=!0,In();const e=W("glv-status"),n=W("glv-progress"),a=W("glv-progress-sub");e&&(e.className="vex-action-info muted",e.style.color="",e.innerHTML="<span>"+ie("running")+"</span>"),n&&(n.style.display=""),a&&(a.textContent=(J.vatFile.name||"VAT")+" + "+(J.glFile.name||"GL"));const s=new FormData,o=ht("vatFile"),i=ht("glFile");for(const l of o)s.append("vat_files",l,l.name);for(const l of i)s.append("gl_files",l,l.name);const r=(W("glv-prefix")&&W("glv-prefix").value||"4").trim()||"4";s.append("revenue_prefix",r),s.append("lang",Xt());try{const l=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:jt(),body:s});let m=null;try{m=await l.json()}catch{m=null}if(!l.ok||!m||!m.ok||!m.job_id)throw new Error(m&&m.detail||m&&m.error||"HTTP "+l.status);const d=W("glv-progress-sub"),p=await window._reconPollJob(m.job_id,Pr(),{onProgress:f=>{d&&(d.textContent=window._reconProgressText(f,Xt()))}});if(!p||p.status!=="done"||!p.result_id)throw p&&p.status==="failed"&&p.error_code?new Error(jm(p.error_code)):new Error(ie("error")||"Error");const c=await fetch("/api/recon/gl-vat/"+encodeURIComponent(p.result_id),{headers:jt()});let u=null;try{u=await c.json()}catch{u=null}if(!c.ok||!u||!u.ok)throw new Error(u&&u.detail||u&&u.error||"HTTP "+c.status);J.currentTaskId=u.task_id,J.lastDetail=u.detail||[],J.lastSummary=u.summary||{},Js(u.stats||{}),Xs(J.lastDetail),Zs(J.lastSummary);const v=W("glv-result");v&&(v.style.display=""),Dr(),e&&(e.className="vex-action-info ok",e.style.color="",e.innerHTML="<span>"+ie("done")+" · GL "+(u.gl_row_count||0)+" · VAT "+(u.vat_row_count||0)+"</span>"),Vt()}catch(l){console.error("[gl-vat] run failed:",l),e&&(e.className="vex-action-info",e.style.color="#ef4444",e.innerHTML="<span>"+ie("error")+": "+(l.message||l)+"</span>")}finally{J.running=!1,n&&(n.style.display="none"),In()}}async function Km(){if(J.currentTaskId)try{const e="/api/recon/gl-vat/"+J.currentTaskId+"/export?lang="+encodeURIComponent(Xt()),n=await fetch(e,{headers:jt()});if(!n.ok)throw new Error("HTTP "+n.status);const a=await n.blob(),s=document.createElement("a");s.href=URL.createObjectURL(a),s.download="GL_VAT_recon_"+J.currentTaskId+".xlsx",document.body.appendChild(s),s.click(),setTimeout(()=>{URL.revokeObjectURL(s.href),s.remove()},200)}catch(e){console.error("[gl-vat] export failed:",e),typeof showToast=="function"&&showToast(ie("error")+": "+(e.message||e),"error")}}function Ym(){J.running||Tn(),Vt(),J.lastDetail&&J.lastDetail.length&&Xs(J.lastDetail),J.lastSummary&&Zs(J.lastSummary)}function Jm(){if(J.inited){Vt();return}J.inited=!0,ni("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),ni("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const e=W("btn-glv-run");e&&e.addEventListener("click",Wm);const n=W("btn-glv-export");n&&n.addEventListener("click",Km);const a=W("btn-glv-reset");a&&a.addEventListener("click",Rm);const s=W("glv-hist-search");s&&s.addEventListener("input",Om),zm(),Js(null),Tn(),window._loadGlvHistory=Vt,Vt(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",Ym)}window._glvRemoveFile=qm;window.GlVatRecon={ensureInit:Jm};window._glvPreviewFiles=function(e){return ht(e==="vat"?"vatFile":"glFile")};const Xm=["flowaccount","peak","xero","quickbooks","express"],qr={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},Zm=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],Qm=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],ev="468b50c1-5593-4fd6-990d-515ce8085563";let oe={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function Fn(){const e=typeof _userInfo<"u"?_userInfo:null;return!!(e&&(e.role==="owner"||e.is_super_admin))}function tv(){const e=typeof _userInfo<"u"?_userInfo:null;return!!(e&&e.id===ev)}function T(e){return typeof escapeHtml=="function"?escapeHtml(e==null?"":String(e)):String(e??"")}function Bt(e,n){try{typeof showToast=="function"&&showToast(e,n||"info")}catch{}}function nv(e){return e==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+T(t("erp-map-col-client"))+"</div><div>"+T(t("erp-map-col-erp"))+"</div><div>"+T(t("erp-map-col-erp-code"))+"</div><div>"+T(t("erp-map-col-notes"))+"</div><div>"+T(t("erp-map-col-actions"))+"</div></div>":e==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+T(t("erp-map-col-erp"))+"</div><div>"+T(t("erp-map-col-category"))+"</div><div>"+T(t("erp-map-col-erp-code"))+"</div><div>"+T(t("erp-map-col-erp-name"))+"</div><div>"+T(t("erp-map-col-notes"))+"</div><div>"+T(t("erp-map-col-actions"))+"</div></div>":e==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+T(t("erp-map-col-item-name"))+"</div><div>"+T(t("erp-map-col-erp-product-code"))+"</div><div>"+T(t("erp-map-col-erp-name"))+"</div><div>"+T(t("erp-map-col-notes"))+"</div><div>"+T(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+T(t("erp-map-col-erp"))+"</div><div>"+T(t("erp-map-col-tax"))+"</div><div>"+T(t("erp-map-col-erp-tax-code"))+"</div><div>"+T(t("erp-map-col-notes"))+"</div><div>"+T(t("erp-map-col-actions"))+"</div></div>"}function Fa(e,n){let a='<select class="form-input" data-erp-field="'+n+'">';return a+='<option value="">'+T(t("erp-map-pick-erp"))+"</option>",Xm.forEach(function(s){const o=s===e?" selected":"";a+='<option value="'+s+'"'+o+">"+T(qr[s])+"</option>"}),a+="</select>",a}function av(e){let n='<select class="form-input" data-erp-field="client_id">';return n+='<option value="">'+T(t("erp-map-pick-client"))+"</option>",(oe.clientList||[]).forEach(function(a){const s=String(a.id)===String(e)?" selected":"";n+='<option value="'+a.id+'"'+s+">"+T(a.name||"#"+a.id)+"</option>"}),n+="</select>",n}function sv(e){let n='<select class="form-input" data-erp-field="pearnly_category">';return n+='<option value="">'+T(t("erp-map-pick-cat"))+"</option>",Zm.forEach(function(a){const s=a===e?" selected":"";n+='<option value="'+a+'"'+s+">"+T(t("erp-map-cat-"+a))+"</option>"}),n+="</select>",n}function ov(e){let n='<select class="form-input" data-erp-field="pearnly_tax_kind">';return n+='<option value="">'+T(t("erp-map-pick-tax"))+"</option>",Qm.forEach(function(a){const s=a===e?" selected":"";n+='<option value="'+a+'"'+s+">"+T(t("erp-map-tax-"+a))+"</option>"}),n+="</select>",n}function iv(e){const n='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+T(t("erp-map-save"))+"</button>";return e==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+T(t("erp-map-col-client"))+'">'+av("")+'</div><div data-label="'+T(t("erp-map-col-erp"))+'">'+Fa("","erp_type")+'</div><div data-label="'+T(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+T(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+T(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+T(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>":e==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+T(t("erp-map-col-erp"))+'">'+Fa("","erp_type")+'</div><div data-label="'+T(t("erp-map-col-category"))+'">'+sv("")+'</div><div data-label="'+T(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+T(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+T(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+T(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+T(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+T(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+T(t("erp-map-col-erp"))+'">'+Fa("","erp_type")+'</div><div data-label="'+T(t("erp-map-col-tax"))+'">'+ov("")+'</div><div data-label="'+T(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+T(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+T(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+T(t("erp-map-ph-notes"))+'"></div><div>'+n+"</div></div>"}function rv(e,n,a){const s=a?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+T(n.id)+'" title="'+T(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',o='<span class="erp-map-erp-badge">'+T(qr[n.erp_type]||n.erp_type)+"</span>";if(e==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+T(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+T(n.client_name||"#"+n.client_id)+'</div><div data-label="'+T(t("erp-map-col-erp"))+'">'+o+'</div><div data-label="'+T(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+T(n.erp_code||"")+'</div><div data-label="'+T(t("erp-map-col-notes"))+'">'+T(n.notes||"")+"</div><div>"+s+"</div></div>";if(e==="accounts"){const r=t("erp-map-cat-"+(n.pearnly_category||"other"))||n.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+T(t("erp-map-col-erp"))+'">'+o+'</div><div data-label="'+T(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+T(r)+'</div><div data-label="'+T(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+T(n.erp_code||"")+'</div><div data-label="'+T(t("erp-map-col-erp-name"))+'">'+T(n.erp_name||"")+'</div><div data-label="'+T(t("erp-map-col-notes"))+'">'+T(n.notes||"")+"</div><div>"+s+"</div></div>"}if(e==="products")return'<div class="erp-map-row row-products"><div data-label="'+T(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+T(n.item_name||"")+'</div><div data-label="'+T(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+T(n.erp_code||"")+'</div><div data-label="'+T(t("erp-map-col-erp-name"))+'">'+T(n.erp_name||"")+'</div><div data-label="'+T(t("erp-map-col-notes"))+'">'+T(n.notes||"")+"</div><div>"+s+"</div></div>";const i=t("erp-map-tax-"+(n.pearnly_tax_kind||""))||n.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+T(t("erp-map-col-erp"))+'">'+o+'</div><div data-label="'+T(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+T(i)+'</span></div><div data-label="'+T(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+T(n.erp_code||"")+'</div><div data-label="'+T(t("erp-map-col-notes"))+'">'+T(n.notes||"")+"</div><div>"+s+"</div></div>"}(function(){async function e(p,c){const u=localStorage.getItem("mrpilot_token");if(u&&!(oe.loaded[p]&&!c))try{const v=await fetch("/api/erp/mappings/"+p,{headers:{Authorization:"Bearer "+u}});if(!v.ok)throw new Error("http_"+v.status);const f=await v.json();oe.items[p]=f.items||[],oe.loaded[p]=!0}catch{oe.items[p]=[],oe.loaded[p]=!1}}async function n(p){if(oe.clientLoaded)return;const c=localStorage.getItem("mrpilot_token");if(c)try{const u=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+c}});if(!u.ok)throw new Error("http_"+u.status);const v=await u.json();oe.clientList=(v.clients||v.items||[]).filter(f=>f.is_active!==!1),oe.clientLoaded=!0}catch{oe.clientList=[]}}function a(){const p=document.getElementById("erp-map-pane-wrap");if(!p)return;const c=!Fn();let u="";c&&(u+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+T(t("erp-map-readonly-tip"))+"</div>"),u+='<div class="erp-map-toolbar">',!c&&oe.sub!=="products"&&(u+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+T(t("erp-map-add-row"))+"</button>"),u+="</div>",u+='<div class="erp-map-table" id="erp-map-table-host"></div>',p.innerHTML=u,s();const v=document.getElementById("erp-map-dev-bar");v&&(v.style.display=Fn()&&tv()?"":"none")}function s(){const p=document.getElementById("erp-map-table-host");if(!p)return;const c=oe.sub,u=oe.items[c]||[],v=oe.addingNew[c],f=!Fn();if(!u.length&&!v){p.innerHTML='<div class="erp-map-empty"><strong>'+T(t("erp-map-empty-"+c))+"</strong>"+T(t("erp-map-empty-"+c+"-sub"))+"</div>";return}let y="";y+=nv(c),v&&!f&&(y+=iv(c)),u.forEach(function(b){y+=rv(c,b,f)}),p.innerHTML=y}async function o(p){const c=oe.sub,u={};p.querySelectorAll("[data-erp-field]").forEach(function(b){u[b.dataset.erpField]=(b.value||"").trim()});const v=localStorage.getItem("mrpilot_token");if(!v)return;let f={},y="/api/erp/mappings/"+c;if(c==="clients"){if(!u.client_id||!u.erp_type||!u.erp_code){Bt(t("erp-map-save-fail"),"error");return}f={client_id:parseInt(u.client_id,10),erp_type:u.erp_type,erp_code:u.erp_code,notes:u.notes||""}}else if(c==="accounts"){if(!u.erp_type||!u.pearnly_category||!u.erp_code){Bt(t("erp-map-save-fail"),"error");return}f={erp_type:u.erp_type,pearnly_category:u.pearnly_category,erp_code:u.erp_code,erp_name:u.erp_name||"",notes:u.notes||""}}else{if(!u.erp_type||!u.pearnly_tax_kind||!u.erp_code){Bt(t("erp-map-save-fail"),"error");return}f={erp_type:u.erp_type,pearnly_tax_kind:u.pearnly_tax_kind,erp_code:u.erp_code,notes:u.notes||""}}try{const b=await fetch(y,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+v},body:JSON.stringify(f)});if(!b.ok)throw new Error("http_"+b.status);oe.addingNew[c]=!1,await e(c,!0),s(),Bt(t("erp-map-saved-toast"),"success")}catch{Bt(t("erp-map-save-fail"),"error")}}async function i(p){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const u=oe.sub,v=localStorage.getItem("mrpilot_token");try{const f=await fetch("/api/erp/mappings/"+u+"/"+encodeURIComponent(p),{method:"DELETE",headers:{Authorization:"Bearer "+v}});if(!f.ok)throw new Error("http_"+f.status);await e(u,!0),s(),Bt(t("erp-map-deleted-toast"),"success")}catch{Bt(t("erp-map-delete-fail"),"error")}}async function r(){await n(),await e(oe.sub,!1),a()}function l(p){p!==oe.sub&&(oe.sub=p,oe.addingNew[p]=!1,["clients","accounts","taxes","products"].forEach(function(c){c!==p&&(oe.addingNew[c]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(c){c.classList.toggle("active",c.dataset.erpSubtab===p)}),e(p,!1).then(function(){a()}))}function m(){oe.bound||(oe.bound=!0,document.addEventListener("click",function(p){const c=p.target.closest(".erp-subtab[data-erp-subtab]");if(c){p.preventDefault();const b=c.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(h){h.classList.toggle("active",h.dataset.erpSubtab===b)}),document.querySelectorAll(".erp-subpanel").forEach(function(h){h.classList.toggle("active",h.dataset.erpSubpanel===b)}),b==="mappings"&&setTimeout(r,50);return}const u=p.target.closest(".erp-map-subtab[data-erp-subtab]");if(u){p.preventDefault(),l(u.dataset.erpSubtab);return}if(p.target.closest("#erp-map-add-btn")){if(p.preventDefault(),!Fn())return;oe.addingNew[oe.sub]=!0,s();return}const f=p.target.closest('[data-erp-save="new"]');if(f){p.preventDefault();const b=f.closest('[data-erp-row="new"]');b&&o(b);return}const y=p.target.closest("[data-erp-del]");if(y){p.preventDefault(),i(y.dataset.erpDel);return}}))}function d(){const p=document.getElementById("erp-map-pane-wrap");p&&p.children.length>0&&a(),document.querySelectorAll(".erp-map-subtab").forEach(function(c){const u="erp-map-subtab-"+c.dataset.erpSubtab,v=t(u);v&&v!==u&&(c.textContent=v)})}m(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",d)})();(function(){let e=null,n=0,a=!1;function s(E){return typeof escapeHtml=="function"?escapeHtml(E==null?"":String(E)):String(E??"")}function o(E,I){try{typeof showToast=="function"&&showToast(E,I||"info")}catch{}}async function i(E){const I=Date.now();if(e&&I-n<3e4)return e;const B=localStorage.getItem("mrpilot_token");if(!B)return[];try{const L=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+B}});if(!L.ok)return[];const $=await L.json();return e=$&&$.connectors||[],n=I,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function l(E){try{localStorage.setItem("pn_push_default_connector",E||"")}catch{}}function m(E){if(!E||!E.length)return null;const I=r();if(I){const L=E.find($=>$.id===I);if(L)return L}const B=E.find(L=>L.is_default);return B||E[0]}function d(E){if(!E)return!1;const I=String(E.status||"").toLowerCase();return I==="exception"||I==="exception_pending"||I==="rejected"}function p(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(E){const I=E&&(E.type||E.id);return I==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':I==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function u(E,I){if(!E||!I)return!1;const B=document.getElementById("btn-push-default");B&&(B.disabled=!0,B.classList.add("loading"));const L=localStorage.getItem("mrpilot_token");try{let $,S={method:"POST",headers:{Authorization:"Bearer "+L}};E.type==="xero"?$="/api/erp/xero/push/"+encodeURIComponent(I):($="/api/erp/push",S.headers["Content-Type"]="application/json",S.body=JSON.stringify({history_id:I,endpoint_id:E.endpoint_id||void 0}));const H=await fetch($,S);let R={};try{R=await H.json()}catch{}if(!H.ok){let G=R&&R.detail||"unknown";typeof G=="object"&&(G=G.code||JSON.stringify(G));let se=String(G||"unknown");if(E.type==="xero"){const ce=se.replace(/^xero\./,"").toLowerCase(),_e=t("xero-"+ce);_e&&_e!=="xero-"+ce&&(se=_e)}return o(t("unified-push-fail").replace("{name}",E.name).replace("{err}",se),"error"),!1}if(R&&R.ok===!1){let G=R.error_msg||R.error_code||"unknown";return G=String(G).slice(0,200),o(t("unified-push-fail").replace("{name}",E.name).replace("{err}",G),"error"),!1}return o(t("unified-push-ok").replace("{name}",E.name),"success"),!0}catch($){return o(t("unified-push-fail").replace("{name}",E.name).replace("{err}",$.message||"network"),"error"),!1}finally{B&&(B.disabled=!1,B.classList.remove("loading"))}}async function v(E,I){for(const B of E)await u(B,I)}function f(E,I){const B=document.createElement("div");B.className="pn-push-dropdown",B.id="pn-push-dropdown";const L=(E||[]).map(S=>{const H=!!(I&&S.id===I.id),R=S.method==="download"?t("unified-push-tag-download"):H?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+s(S.id)+'"><span class="pn-pd-icon">'+c(S)+'</span><span class="pn-pd-name">'+s(S.name)+"</span>"+(R?'<span class="pn-pd-tag">'+s(R)+"</span>":"")+(H?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),$=E&&E.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+s(t("unified-push-all").replace("{n}",E.length))+"</span></div>":"";return B.innerHTML=L+$,B}function y(){const E=document.getElementById("pn-push-dropdown");E&&E.remove()}async function b(){if(document.getElementById("pn-push-dropdown")){y();return}const E=await i()||[],I=m(E),B=f(E,I),L=document.getElementById("pn-push-wrap");L&&L.appendChild(B)}async function h(){const E=await i()||[],I=m(E);if(!I)return;const B=p(),L=B&&(B._historyId||B.history_id);if(L){if(d(B)){o(t("unified-push-disabled-exc"),"warn");return}await u(I,L)}}async function g(E){y();const I=await i()||[],B=p(),L=B&&(B._historyId||B.history_id);if(!L)return;if(d(B)){o(t("unified-push-disabled-exc"),"warn");return}if(E==="__all__"){await v(I,L);return}const $=I.find(S=>S.id===E);$&&(l(E),await u($,L),w())}async function _(){const E=document.getElementById("drawer-history-save");if(!E||E.querySelector("#pn-push-wrap"))return;const I=document.createElement("div");I.id="pn-push-wrap",I.className="pn-push-wrap",I.dataset.loading="1",E.insertBefore(I,E.firstChild),["btn-push-erp","btn-xero-push"].forEach(R=>{E.querySelectorAll("#"+R).forEach(G=>{G.style.display="none"})});const B=await i()||[],L=m(B),$=B.length>0;if(!$)I.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+s(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+s(t("unified-push-empty"))+"</span></button>";else{const R=B.length>1;I.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+s(t("unified-push-tip"))+'">'+c(L)+"<span>"+s(t("unified-push-to").replace("{name}",L?L.name:""))+"</span></button>"+(R?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+s(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete I.dataset.loading;const S=I.querySelector("#btn-push-default");S&&$&&S.addEventListener("click",h);const H=I.querySelector("#btn-push-arrow");H&&H.addEventListener("click",function(R){R.stopPropagation(),b()}),a||(a=!0,document.addEventListener("click",function(R){const G=R.target.closest(".pn-pd-item");if(G){const se=G.getAttribute("data-cid");g(se);return}R.target.closest("#btn-push-arrow")||y()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",w))}function w(){const E=document.getElementById("pn-push-wrap");E&&(E.remove(),e=null,n=0,_())}function k(){const E=document.getElementById("drawer-history-save");if(!E||!E.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(B=>{E.querySelectorAll("#"+B).forEach(L=>{L.style.display!=="none"&&(L.style.display="none")})});const I=E.querySelectorAll("#pn-push-wrap");if(I.length>1)for(let B=1;B<I.length;B++)I[B].remove()}function x(){try{const E=function(){return document.getElementById("drawer-body")},I=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&_(),k()}),B=E();if(B)I.observe(B,{childList:!0,subtree:!0});else{const L=new MutationObserver(function(){const $=E();$&&(I.observe($,{childList:!0,subtree:!0}),L.disconnect())});L.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&_(),k()},200)}catch{}}x()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const s=document.getElementById("erp-map-subtabs");if(!s)return;const o=s.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=o?"erp-map-hide-advanced":"erp-map-show-advanced",l=t(r);l&&l!==r&&(i.textContent=l)}a.setAttribute("aria-pressed",o?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const o=document.getElementById("erp-map-subtabs");if(o&&(o.classList.toggle("show-advanced"),e(),!o.classList.contains("show-advanced")&&o.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=o.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function s(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const m=document.getElementById("erp-onboard-title"),d=document.getElementById("erp-onboard-body"),p=document.getElementById("erp-onboard-ok"),c=document.getElementById("erp-onboard-later");m&&(m.textContent=t("erp-onboard-title")),d&&(d.textContent=t("erp-onboard-body")),p&&(p.textContent=t("erp-onboard-ok")),c&&(c.textContent=t("erp-onboard-later"))}r();function l(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}l();try{const m=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');m&&m.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}l()}),i.addEventListener("click",function(m){m.target===i&&l()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function o(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,s(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),l=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||l)&&setTimeout(o,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const s=n.stage||"parse",o=e[s]||e.parse,i=o[a]||o.th||o.en,r=n.stage_total,l=n.stage_done;if(s==="parse"&&typeof r=="number"&&r>0){const m={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+m.replace("{d}",String(l||0)).replace("{t}",String(r))}return i},window._reconPollJob=async function(n,a,s){s=s||{};const o=s.intervalMs||1500,i=s.maxMs||1200*1e3,r=Date.now();let l=0;for(;;){let m=null;try{const d=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{m=await d.json()}catch{m=null}(!d.ok||!m||!m.ok)&&(m=null)}catch{m=null}if(m){if(l=0,s.onProgress)try{s.onProgress(m.progress||{},m)}catch{}if(m.status==="done"||m.status==="failed"||m.status==="needs_review"||m.status==="needs_mapping")return m}else if(++l>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(d=>setTimeout(d,o))}}})();const j={initialized:!1,stmtFiles:[],glFiles:[],currentTask:null,currentFilter:"all",allRows:[],brv2Search:{stmt:"",gl:""},cachedHistoryTasks:[],brv2Page:1},P=e=>document.getElementById(e);function ut(e){if(e==null)return"—";const n=Number(e);return isNaN(n)?"—":n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function ai(e){return e?String(e).slice(0,10).split("-").reverse().join("/"):"—"}function pe(e){return String(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function lv(e,n){n=window._currentLang||n||"th";const a={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},s={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},o=a[e]||s;return o[n]||o.th||o.en}function cv(e){return e?e<1024?e+" B":e<1048576?(e/1024).toFixed(1)+" KB":(e/1048576).toFixed(1)+" MB":""}function qt(e,n){return window.t&&window.t(e)||n}function st(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function za(e){const n=Number(e);return Number.isFinite(n)?n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}var Rr="pearnly.brv2.lastAnchorOcr";function dv(e){try{var n=e&&e._anchor_ocr;if(!n||typeof n!="object")return;var a={stmt_opening:Number.isFinite(+n.stmt_opening)?+n.stmt_opening:null,gl_opening:Number.isFinite(+n.gl_opening)?+n.gl_opening:null,gl_closing:Number.isFinite(+n.gl_closing)?+n.gl_closing:null,stmt_closing:Number.isFinite(+n.stmt_closing)?+n.stmt_closing:null,ts:Date.now()};localStorage.setItem(Rr,JSON.stringify(a))}catch{}}function pv(){try{var e=localStorage.getItem(Rr);if(!e)return null;var n=JSON.parse(e);return!n||typeof n!="object"?null:n}catch{return null}}function uv(){var e=pv();if(e){var n={"brv2-anchor-stmt-opening":e.stmt_opening,"brv2-anchor-gl-opening":e.gl_opening,"brv2-anchor-gl-closing":e.gl_closing,"brv2-anchor-stmt-closing":e.stmt_closing},a=0;Object.keys(n).forEach(function(l){var m=document.getElementById(l);if(m&&m.value===""){var d=n[l];if(Number.isFinite(d)){m.value=d.toFixed(2);var p=m.closest&&m.closest(".brv2-anchor-cell");p&&p.classList.add("is-prefilled"),a+=1}}});var s=document.getElementById("brv2-anchor-eq"),o=document.getElementById("brv2-anchor-eq-val");if(s&&o&&Number.isFinite(e.stmt_opening)&&Number.isFinite(e.gl_opening)){var i=e.stmt_opening-e.gl_opening;o.textContent=i.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),s.style.display=""}if(a>0){var r=document.getElementById("brv2-anchor-prefill-banner");r&&r.classList.add("show")}}}function mv(){var e=document.getElementById("brv2-anchor-prefill-banner");if(e){var n=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(a){var s=document.getElementById(a);if(s){var o=s.closest&&s.closest(".brv2-anchor-cell");o&&o.classList.contains("is-prefilled")&&(n=!0)}}),e.classList.toggle("show",n)}}var vv=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function fv(e){var n=document.getElementById("brv2-summary-collapse");if(!(!n||!n.parentNode)){var a=document.getElementById("brv2-anchor-audit"),s=e&&e._anchor_overrides;if(!s||typeof s!="object"||Object.keys(s).length===0){a&&a.parentNode&&a.parentNode.removeChild(a);return}a||(a=document.createElement("div"),a.id="brv2-anchor-audit",a.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",n.parentNode.insertBefore(a,n.nextSibling));var o=vv.map(function(i){var r=s[i[0]];if(!r)return"";var l=+r.ocr||0,m=+r.user||0,d=m-l,p=d>0?"+":(d<0,""),c=Math.abs(d)<.005?"#6b7280":d>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+st(qt(i[1],i[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+st(za(l))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+st(za(m))+'</td><td style="padding:6px 10px;color:'+c+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+st(p+za(d))+"</td></tr>"}).join("");a.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+st(qt("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+st(qt("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+st(qt("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+st(qt("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+st(qt("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+o+"</tbody></table>"}}function ca(e){const n=P("brv2-summary-collapse"),a=P("brv2-detail-collapse"),s=P("brv2-export-btn"),o=P("brv2-new-btn"),i=P("brv2-parse-info-wrap");n&&(n.style.display=e?"":"none"),a&&(a.style.display=e?"":"none"),s&&(s.style.display=e?"":"none"),o&&(o.style.display=e?"":"none"),!e&&i&&(i.style.display="none");const r=P("brv2-warnings");!e&&r&&(r.style.display="none",r.innerHTML="")}function hv(e){const n=P("brv2-parse-info-wrap"),a=P("brv2-parse-info-body");if(!n||!a)return;const s=e.parse_info;if(!s){n.style.display="none";return}const o=window._currentLang||"zh",i={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},r=u=>(i[u]||{})[o]||(i[u]||{}).zh||u,l=[...(s.stmt_files||[]).map(u=>({...u,_type:"stmt",_extra:u.bank_code||""})),...(s.gl_files||[]).map(u=>({...u,_type:"gl",_extra:(u.accounts||[]).join(", ")}))],m={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},d=u=>{const v=String(u||"");return/Cannot detect bank statement column headers/i.test(v)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(v)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(v)?"stmt_no_rows":/unsupported format/i.test(v)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(v)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(v)?"ocr_failed":null},p=u=>{const v=u.error_code||d(u.error);if(v&&m[v]){const f=window._currentLang||"zh";return m[v][f]||m[v].zh}return String(u.error||"").slice(0,80)},c=u=>!u.ok&&u.error?`<span style="color:#dc2626">${r("fail")} — ${pe(p(u))}</span>`:u.rows?`<span style="color:#059669">${r("ok")} (${u.rows})</span>`:`<span style="color:#d97706">${r("warn")}</span>`;a.innerHTML=`
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
                ${l.map(u=>`<tr>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${u._type==="stmt"?r("stmt"):r("gl")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${pe(u.file||"")}">${pe(u.file||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${u.rows||0}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${pe(u._extra||"")}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb">${c(u)}</td>
                </tr>`).join("")}
            </tbody>
        </table>`,n.style.display=""}async function Fr(e){const n=localStorage.getItem("mrpilot_token")||"",a=window._currentLang||"zh";try{const s=await fetch("/api/recon/bank-v2/"+e+"/export?lang="+a,{headers:{Authorization:"Bearer "+n}});if(!s.ok){const p=await s.json().catch(()=>({}));window.showToast&&window.showToast(p.detail||"Export failed","error");return}const o=await s.blob(),r=(s.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),l=r?r[1].replace(/['"]/g,""):"reconciliation.xlsx",m=URL.createObjectURL(o),d=document.createElement("a");d.href=m,d.download=l,document.body.appendChild(d),d.click(),document.body.removeChild(d),URL.revokeObjectURL(m)}catch(s){window.showToast&&window.showToast("Export error: "+s.message,"error")}}function gv(e,n){const a=P("brv2-summary-collapse");let s=P("brv2-warnings");const o=window._currentLang||"zh",i={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[o]||"⏭ ",r=[];if((n||[]).forEach(l=>r.push(i+" "+l)),(e||[]).forEach(l=>r.push(l)),!r.length){s&&(s.style.display="none");return}if(!s)if(s=document.createElement("div"),s.id="brv2-warnings",a&&a.parentNode)a.parentNode.insertBefore(s,a);else return;s.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",s.innerHTML=r.map(l=>"<div>"+pe(l)+"</div>").join("")}function Qs(e){hv(e),gv(e.warnings||[],e.skipped_files||[]),!e.ok&&e.error&&window.showToast&&window.showToast(e.error,"error");const n=e.stats||{},a=e.summary||{},s=n.matched||0,o=(n.gl_debit_only||0)+(n.gl_credit_only||0),i=(n.stmt_withdrawal_only||0)+(n.stmt_deposit_only||0),r=Number(a.formula_diff||0),l=Math.abs(r)<.05;P("brv2-kpi-matched")&&(P("brv2-kpi-matched").textContent=s),P("brv2-kpi-diff")&&(P("brv2-kpi-diff").textContent=ut(r)),P("brv2-kpi-unmatched")&&(P("brv2-kpi-unmatched").textContent=o+i);const m=P("brv2-kpi-diff-icon");m&&(m.style.background=l?"#d1fae5":"#fee2e2",m.style.color=l?"#065f46":"#b91c1c");const d=P("brv2-formula-sub");if(d){const f=window._currentLang||"zh";d.textContent=l?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[f]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[f]||"差 ")+ut(r)}const p=P("brv2-detail-sub");if(p){const f=window._currentLang||"zh",y={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[f]||"共 {n} 行";p.textContent=y.replace("{n}",j.allRows.length)}function c(f,y,b){const h=P(f);h&&(h.textContent=(b&&y>0?"(":"")+ut(b?-y:y)+(b&&y>0?")":""))}c("brf-gl-close",a.gl_closing||0),c("brf-open-diff",a.opening_diff||0),c("brf-gl-debit-only",a.gl_debit_only_amount||0,!0),c("brf-gl-credit-only",a.gl_credit_only_amount||0),c("brf-stmt-wd-only",a.stmt_withdrawal_only_amount||0,!0),c("brf-stmt-dep-only",a.stmt_deposit_only_amount||0),c("brf-calc-close",a.formula_stmt_closing||0),c("brf-stmt-close",a.stmt_closing||0),P("brf-diff")&&(P("brf-diff").textContent=ut(r));const u=P("brv2-fcell-diff");u&&u.classList.toggle("brv2-fcell-diff-ok",l);const v=P("brv2-export-btn");v&&(v.onclick=()=>{j.currentTask&&Fr(j.currentTask.task_id)}),fv(a),ca(!0),zr()}function zr(){const e=P("brv2-tbody");if(!e)return;const n=j.allRows.filter(i=>j.currentFilter==="all"?!0:j.currentFilter==="matched"?i.match_status==="matched":j.currentFilter==="gl_only"?i.match_status.startsWith("gl_"):j.currentFilter==="stmt_only"?i.match_status.startsWith("stmt_"):!0);if(n.length===0){const i={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";e.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${i}</td></tr>`;return}const a=window._currentLang||"zh",s={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[a],o={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[a];e.innerHTML=n.map(i=>{const r=i.match_status,l=i.match_layer;let m="",d="";r==="matched"?(l===1&&(m="matched",d='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),l===2&&(m="matched-l2",d='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),l===3&&(m="matched-l3",d='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):r==="gl_debit_only"||r==="gl_credit_only"?(m="gl-only",d='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(m="stmt-only",d=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[a]||"账单"}</span>`);let p="";return i.stmt_balance_ok===!1&&(p+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${pe(s)}">⚠</span>`,m+=" brv2-row-warn"),i.stmt_confidence==="low"&&(p+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${pe(o)}">◌</span>`,m.includes("brv2-row-warn")||(m+=" brv2-row-warn-soft")),`<tr class="${m.trim()}">
          <td>${d}${p}</td>
          <td>${pe(ai(i.stmt_date))}</td>
          <td title="${pe(i.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${pe(i.stmt_desc)}</td>
          <td class="num">${i.stmt_withdrawal?ut(i.stmt_withdrawal):""}</td>
          <td class="num">${i.stmt_deposit?ut(i.stmt_deposit):""}</td>
          <td>${pe(ai(i.gl_date))}</td>
          <td title="${pe(i.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${pe(i.gl_doc_no)}</td>
          <td class="num">${i.gl_debit?ut(i.gl_debit):""}</td>
          <td class="num">${i.gl_credit?ut(i.gl_credit):""}</td>
          <td>${l?"L"+l:"—"}</td>
        </tr>`}).join("")}async function wn(){const e=localStorage.getItem("mrpilot_token")||"";try{const a=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+e}})).json();da(a.tasks||[])}catch{const a=P("brv2-history-empty"),s=window._currentLang||"zh",o={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[s]||"加载失败";a&&(a.textContent=o,a.style.display="");const i=P("brv2-history-table-wrap");i&&(i.style.display="none")}}const Ut=10;function si(){const e=P("brv2-history-pager"),n=P("brv2-history-pager-info"),a=P("brv2-history-prev"),s=P("brv2-history-next");if(!e)return;if(j.cachedHistoryTasks.length<=Ut){e.style.display="none";return}e.style.display="";const o=Math.ceil(j.cachedHistoryTasks.length/Ut);n&&(n.textContent=j.brv2Page+" / "+o),a&&(a.disabled=j.brv2Page<=1),s&&(s.disabled=j.brv2Page>=o)}function bv(){const e=P("brv2-history-prev"),n=P("brv2-history-next");e&&!e._brv2Bound&&(e._brv2Bound=!0,e.addEventListener("click",()=>{j.brv2Page>1&&(j.brv2Page--,da(j.cachedHistoryTasks))})),n&&!n._brv2Bound&&(n._brv2Bound=!0,n.addEventListener("click",()=>{const a=Math.ceil(j.cachedHistoryTasks.length/Ut);j.brv2Page<a&&(j.brv2Page++,da(j.cachedHistoryTasks))}))}function da(e){e!==void 0&&(j.cachedHistoryTasks=e||[],j.brv2Page=1);const n=j.cachedHistoryTasks,a=P("brv2-history-empty"),s=P("brv2-history-table-wrap"),o=P("brv2-history-tbody");if(!o)return;const i=window._currentLang||"zh";if(!n.length){const v={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[i]||"暂无对账记录";a&&(a.textContent=v,a.style.display=""),s&&(s.style.display="none"),si();return}a&&(a.style.display="none"),s&&(s.style.display="");const r=Math.ceil(n.length/Ut);j.brv2Page>r&&(j.brv2Page=r);const l=(j.brv2Page-1)*Ut,m=n.slice(l,l+Ut),d=localStorage.getItem("mrpilot_token")||"",p='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',c='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',u='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';o.innerHTML="",m.forEach(v=>{const f=Number(v.formula_diff||0),y=Math.abs(f)<.05,b=(v.stmt_files||"").split(";").map(ce=>ce.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),h=(v.gl_files||"").split(";").map(ce=>ce.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),g=v.created_at?String(v.created_at).slice(0,16).replace("T"," "):"",_=document.createElement("tr");_.dataset.taskId=v.id;const w=document.createElement("td");w.textContent=g;const k=document.createElement("td");k.className="glv-history-file",k.title=b+" + "+h,k.textContent=b+" + "+h;const x=document.createElement("td");x.className="glv-num",x.textContent=(v.stmt_row_count||0)+" / "+(v.gl_row_count||0);const E=document.createElement("td");E.className="glv-num",E.textContent=v.matched_count||0;const I=document.createElement("td");I.className="glv-num",I.textContent=v.unmatched_gl||0;const B=document.createElement("td");B.className="glv-num",B.textContent=v.unmatched_stmt||0;const L=document.createElement("td");L.className="glv-num",L.style.color=y?"#059669":"#dc2626",L.textContent=y?"✓":ut(f);const $=document.createElement("td");$.className="glv-history-actions";const S=(ce,_e,we,O)=>{const N=document.createElement("button");return N.type="button",N.title=_e,N.setAttribute("aria-label",_e),we&&(N.className=we),N.innerHTML=ce,N.onclick=Y=>{Y.stopPropagation(),O()},N},H={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[i]||"删除?",R={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[i]||"加载",G={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[i]||"导出",se={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[i]||"删除";$.appendChild(S(p,R,"",()=>oi(v.id,d))),$.appendChild(S(c,G,"",()=>Fr(v.id))),$.appendChild(S(u,se,"glv-del",async()=>{await showConfirm(H,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+v.id,{method:"DELETE",headers:{Authorization:"Bearer "+d}}),wn())})),[w,k,x,E,I,B,L,$].forEach(ce=>_.appendChild(ce)),_.style.cursor="pointer",_.addEventListener("click",async ce=>{ce.target.closest(".glv-del")||ce.target.closest("button")||await oi(v.id,d)}),o.appendChild(_)}),si(),Nr()}function Nr(){const e=((P("brv2-hist-search")||{}).value||"").trim().toLowerCase(),n=P("brv2-history-tbody");n&&n.querySelectorAll("tr").forEach(a=>{a.dataset.taskId&&(a.style.display=!e||a.textContent.toLowerCase().includes(e)?"":"none")})}async function oi(e,n){try{const s=await(await fetch("/api/recon/bank-v2/"+e,{headers:{Authorization:"Bearer "+n}})).json();if(!s.ok)return;j.currentTask={task_id:s.task_id,...s},j.allRows=s.detail||[],j.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(o=>o.classList.toggle("active",o.dataset.filter==="all")),Qs(j.currentTask)}catch{}}function Xe(e){const n=e==="stmt"?j.stmtFiles:j.glFiles,a=P(`brv2-${e}-name`);if(a)if(n.length===0)a.textContent="";else{const o=window._currentLang||"zh",i={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};a.textContent=n.length+(i[o]||" 个文件")}const s=P("brv2-preview-panel");s&&s.style.display!=="none"&&ls(e),yv()}function yv(){const e=P("brv2-toggle-preview"),n=P("brv2-preview-panel"),a=j.stmtFiles.length+j.glFiles.length>0;e&&(e.style.display=a?"":"none"),!a&&n&&(n.style.display="none",e&&e.classList.remove("open"))}function wv(){ls("stmt"),ls("gl")}function ls(e){const n=P(e==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!n)return;const a=e==="stmt"?j.stmtFiles:j.glFiles,s=window._currentLang||"zh",o={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},i=(o[e]||{})[s]||o[e].zh,r=pe(window.t&&window.t("vex-preview-search")||"搜索文件名..."),l=pe(window.t&&window.t("vex-preview-clear-all")||"全清"),m=j.brv2Search[e]||"";n.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+pe(i)+' <span class="vex-pp-col-count">'+a.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+e+'" type="text" placeholder="'+r+'" value="'+pe(m)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+e+'" type="button">'+l+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+e+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+e+'-pg"></div>';const d=P("brv2-pp-search-"+e);d&&d.addEventListener("input",function(c){j.brv2Search[e]=c.target.value,ii(e)});const p=P("brv2-pp-clearall-"+e);p&&p.addEventListener("click",function(){e==="stmt"?j.stmtFiles.length=0:j.glFiles.length=0,Xe(e),mt()}),ii(e)}function ii(e){const n=P("brv2-pp-"+e+"-list"),a=P("brv2-pp-"+e+"-pg");if(!n)return;const s=e==="stmt"?j.stmtFiles:j.glFiles,o=(j.brv2Search[e]||"").toLowerCase(),i=o?s.filter(m=>m.name.toLowerCase().includes(o)):s.slice(),r='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',l='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(n.innerHTML=i.map((m,d)=>'<div class="vex-pp-file-row">'+r+'<span class="vex-pp-fi-name" title="'+pe(m.name)+'">'+pe(m.name)+'</span><span class="vex-pp-fi-size">'+cv(m.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+e+'" data-idx="'+s.indexOf(m)+'" aria-label="remove">'+l+"</button></div>").join(""),n.querySelectorAll(".vex-pp-fi-del").forEach(function(m){m.addEventListener("click",function(){const d=parseInt(m.dataset.idx,10);m.dataset.zone==="stmt"?j.stmtFiles.splice(d,1):j.glFiles.splice(d,1),Xe(m.dataset.zone),mt()})}),a){const m=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";a.textContent=m.replace("{n}",i.length).replace("{m}",s.length)}}function kv(){const e=P("brv2-toggle-preview");e&&!e._reconBound&&(e._reconBound=!0,e.addEventListener("click",function(){const n=P("brv2-preview-panel"),a=P("brv2-toggle-preview-label"),s=n&&n.style.display!=="none";n&&(n.style.display=s?"none":""),e.classList.toggle("open",!s),a&&(a.textContent=s?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),s||wv()}))}function mt(){const e=P("brv2-run-btn"),n=P("brv2-status"),a=j.stmtFiles.length>0,s=j.glFiles.length>0;if(e&&(e.disabled=!(a&&s)),n){const o=window._currentLang||"zh";if(!a&&!s){const i={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};n.textContent=i[o]||i.zh}else if(a)if(s){const i={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};n.textContent=i[o]||i.zh}else{const i={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};n.textContent=i[o]||i.zh}else{const i={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};n.textContent=i[o]||i.zh}}}function ri(e,n,a){const s=P(e),o=P(n);!s||!o||(s.addEventListener("click",()=>o.click()),s.addEventListener("keydown",i=>{(i.key==="Enter"||i.key===" ")&&(i.preventDefault(),o.click())}),s.addEventListener("dragover",i=>{i.preventDefault(),s.classList.add("drag-over")}),s.addEventListener("dragleave",()=>s.classList.remove("drag-over")),s.addEventListener("drop",i=>{i.preventDefault(),s.classList.remove("drag-over");const r=Array.from(i.dataTransfer.files||[]);a==="stmt"?j.stmtFiles.push(...r):j.glFiles.push(...r),Xe(a),mt()}),o.addEventListener("change",()=>{const i=Array.from(o.files||[]);a==="stmt"?j.stmtFiles.push(...i):j.glFiles.push(...i),o.value="",Xe(a),mt()}))}function Ae(e){const n=P("brv2-progress"),a=P("brv2-run-btn"),s=P("brv2-error");n&&(n.style.display=e?"":"none"),a&&(a.disabled=e),s&&(s.style.display="none")}function Je(e){const n=P("brv2-error");n&&(n.textContent=e,n.style.display="",n.scrollIntoView({behavior:"smooth",block:"nearest"})),Ae(!1),mt(),window.showToast&&window.showToast(e,"error")}async function cs(){if(j.stmtFiles.length===0||j.glFiles.length===0)return;const e=localStorage.getItem("mrpilot_token")||"",n=window._currentLang||"zh",a=(P("brv2-acct-select")||{}).value||"";ca(!1),Ae(!0);try{const s=new FormData;j.stmtFiles.forEach(v=>s.append("stmt_files",v)),j.glFiles.forEach(v=>s.append("gl_files",v)),s.append("gl_account",a),s.append("lang",n);const o=parseFloat((P("brv2-anchor-gl-closing")||{}).value),i=parseFloat((P("brv2-anchor-stmt-closing")||{}).value),r=parseFloat((P("brv2-anchor-stmt-opening")||{}).value),l=parseFloat((P("brv2-anchor-gl-opening")||{}).value);Number.isFinite(o)&&s.append("gl_closing_override",o),Number.isFinite(i)&&s.append("stmt_closing_override",i),Number.isFinite(r)&&s.append("stmt_opening_override",r),Number.isFinite(l)&&s.append("gl_opening_override",l);const m=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+e},body:s});let d=null;try{d=await m.json()}catch{d=null}if(d&&d.needs_mapping){Ae(!1),window.ReconMapping?window.ReconMapping.show(d,{token:e,lang:n,onConfirmed:function(){cs()}}):Je(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!m.ok||!d||!d.ok||!d.job_id){Ae(!1),d&&(d.detail||d.error)?Je(_humanizeBackendError(d.detail||d.error,"Error "+m.status)):Je(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const p=P("brv2-progress-sub"),c=await window._reconPollJob(d.job_id,e,{onProgress:v=>{p&&(p.textContent=window._reconProgressText(v,n))}});if(c&&c.status==="needs_mapping"&&c.mapping){Ae(!1),window.ReconMapping?window.ReconMapping.show(c.mapping,{token:e,lang:n,onConfirmed:function(){cs()}}):Je(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(c&&c.status==="needs_review"&&c.review){Ae(!1),window.ReconReview?window.ReconReview.show(c.review,{token:e,lang:n,jobId:d.job_id,onConfirmed:async function(v){Ae(!0);const f=await window._reconPollJob(v,e,{onProgress:y=>{p&&(p.textContent=window._reconProgressText(y,n))}});await u(f)}}):Je(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(c&&c.status==="failed"){Ae(!1),Je(lv(c.error_code,n));return}await u(c);async function u(v){try{if(!v||v.status!=="done"||!v.result_id){Ae(!1),Je(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const f=await fetch("/api/recon/bank-v2/"+encodeURIComponent(v.result_id),{headers:{Authorization:"Bearer "+e}});let y=null;try{y=await f.json()}catch{y=null}if(!f.ok||y===null||!y.ok){Ae(!1),Je(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(y.gl_accounts||[]).length>1&&xv(y.gl_accounts),j.currentTask=y,j.allRows=y.detail||[],j.currentFilter="all",document.querySelectorAll(".brv2-filter-btn").forEach(h=>h.classList.toggle("active",h.dataset.filter==="all")),dv(y&&y.summary),Ae(!1),Qs(y),wn();const b=P("brv2-summary-collapse");b&&b.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(f){Ae(!1),Je(f.message||"Network error")}}}catch(s){Je(s.message||"Network error")}}function xv(e){const n=P("brv2-acct-select");if(!n)return;const a=window._currentLang||"zh",s={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[a]||"全部账户";n.innerHTML=`<option value="">${s}</option>`+e.map(o=>`<option value="${pe(o)}">${pe(o)}</option>`).join(""),n.style.display=""}function eo(){if(j.initialized){wn();return}j.initialized=!0,ri("brv2-stmt-zone","brv2-stmt-input","stmt"),ri("brv2-gl-zone","brv2-gl-input","gl");const e=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function n(){const l=parseFloat((P("brv2-anchor-stmt-opening")||{}).value),m=parseFloat((P("brv2-anchor-gl-opening")||{}).value),d=P("brv2-anchor-eq"),p=P("brv2-anchor-eq-val");if(!(!d||!p))if(Number.isFinite(l)&&Number.isFinite(m)){const c=l-m;p.textContent=c.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),d.style.display=""}else d.style.display="none"}e.forEach(l=>{const m=P(l);m&&(m.addEventListener("input",n),m.addEventListener("input",()=>{const d=m.closest(".brv2-anchor-cell");d&&d.classList.remove("is-prefilled"),mv()}))}),uv();const a=P("brv2-run-btn");a&&a.addEventListener("click",cs);const s=P("brv2-reset-btn");s&&s.addEventListener("click",()=>{j.currentTask=null,j.allRows=[],j.stmtFiles=[],j.glFiles=[],Xe("stmt"),Xe("gl"),mt(),ca(!1);const l=P("brv2-acct-select");l&&(l.style.display="none"),e.forEach(p=>{const c=P(p);if(c){c.value="";const u=c.closest&&c.closest(".brv2-anchor-cell");u&&u.classList.remove("is-prefilled")}});const m=P("brv2-anchor-eq");m&&(m.style.display="none");const d=P("brv2-anchor-prefill-banner");d&&d.classList.remove("show")});const o=P("brv2-new-btn");o&&o.addEventListener("click",()=>{j.currentTask=null,j.allRows=[],j.stmtFiles=[],j.glFiles=[],Xe("stmt"),Xe("gl"),mt(),ca(!1)});const i=P("brv2-filter-tabs");i&&i.addEventListener("click",l=>{l.stopPropagation();const m=l.target.closest(".brv2-filter-btn");m&&(j.currentFilter=m.dataset.filter,i.querySelectorAll(".brv2-filter-btn").forEach(d=>d.classList.toggle("active",d===m)),zr())}),kv(),bv();const r=P("brv2-hist-search");r&&r.addEventListener("input",Nr),wn(),mt(),window._brv2LoadHistory=wn,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(l=>l.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){mt(),Xe("stmt"),Xe("gl"),j.currentTask&&Qs(j.currentTask),da()}})}window._loadBankReconV2Panel=function(e){const n=e?document.getElementById(e):null;n&&n.id!=="recon-pane-bank"&&(n.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
            银行对账 v2 · 请前往对账中心使用</div>`),eo()};document.addEventListener("DOMContentLoaded",()=>{P("brv2-run-btn")&&eo()});window._bankReconV2Init=eo;(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const s=a.target.value;s&&applyLang(s)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",s="pearnly_general_number_format",o={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const d=document.getElementById("general-tz"),p=document.getElementById("general-date"),c=document.getElementById("general-number");if(!(!d||!p||!c))try{d.value=localStorage.getItem(n)||o.tz,p.value=localStorage.getItem(a)||o.date,c.value=localStorage.getItem(s)||o.number}catch{d.value=o.tz,p.value=o.date,c.value=o.number}}async function r(){const d=document.getElementById("btn-save-general"),p=document.getElementById("general-save-msg");if(!d)return;const c=d.innerHTML;d.disabled=!0,d.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",p&&(p.textContent="",p.classList.remove("error"));try{const u=(document.getElementById("general-tz")||{}).value||o.tz,v=(document.getElementById("general-date")||{}).value||o.date,f=(document.getElementById("general-number")||{}).value||o.number;try{localStorage.setItem(n,u),localStorage.setItem(a,v),localStorage.setItem(s,f)}catch{}window._pearnlyGeneral={tz:u,date_format:v,number_format:f},p&&(p.textContent=t("msg-saved")||"已保存")}catch{p&&(p.textContent=t("msg-save-failed")||"保存失败",p.classList.add("error"))}finally{d.disabled=!1,d.innerHTML=c,setTimeout(function(){p&&(p.textContent="")},3e3)}}function l(){const d=document.getElementById("btn-save-general");if(!d){setTimeout(l,200);return}d._pearnlyGenBound||(d._pearnlyGenBound=!0,d.addEventListener("click",r),i())}function m(){i();const d=document.getElementById("general-lang");if(d){const p=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";d.value=p}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",l):l(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",m)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales","sales-account":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function s(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function o(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(l){const m=l.dataset.collapsible;r[m]?l.classList.add("collapsed"):l.classList.remove("collapsed")})}function i(r){const l=a();l[r]=!l[r],s(l),o()}(function(){const l=a();let m=!1;l.sales===void 0&&(l.sales=!1,m=!0),l.expense===void 0&&(l.expense=!0,m=!0),m&&s(l)})(),o(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const l=n[r];if(!l)return;const m=a();m[l]&&(m[l]=!1,s(m),o())}})();const _v=`
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
                <a class="help-contact-card" href="https://line.me/R/ti/p/@pearnly" target="_blank" rel="noopener">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>
                    </svg>
                    <div>
                        <div class="help-contact-label" data-i18n="contact-line-label">LINE 客服</div>
                        <div class="help-contact-value">@pearnly</div>
                    </div>
                </a>
            </div>
        </div>
    </div>`;function li(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=_v;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(s=>{const o=s.getAttribute("data-i18n");o&&a[o]&&(s.textContent=a[o])})}document.readyState,li();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(s){s.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(s){s.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const s=a.closest(".integration-row"),o=s?s.dataset.intAnchor:null;if(o&&e[o]){const i=s.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[o],r)}})})();let Fe=[];window._erpEndpoints=Fe;let Bn=null;async function Ea(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}Fe=(await e.json()).items||[],window._erpEndpoints=Fe,Vr()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return Ea()};async function Or(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),s=a.total||0,o=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(s===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const l=[];l.push(`<span class="erp-today-item"><strong>${s}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),o>0&&l.push(`<span class="erp-today-item ok"><strong>${o}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&l.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&l.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=l.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function Vr(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const o=_userInfo.endpoints_limit;o!==-1&&Fe.length>=o?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:o}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(Fe.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const s=Fe.some(o=>o.auto_push&&o.enabled);if(n&&(n.textContent=t("auto-status-active",{n:Fe.length,mode:s?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(s?"active":"ready")),Or(),e.innerHTML=Fe.map(o=>{const i=o.config||{},r=escapeHtml(i.url||"");i._token_set;const l=o.enabled!==!1,m=[];o.is_default&&m.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),o.auto_push&&m.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),l||m.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const d=[];return o.success_count>0&&d.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:o.success_count}))}</span>`),o.failure_count>0&&d.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:o.failure_count}))}</span>`),`
            <div class="erp-endpoint" data-ep-id="${escapeHtml(o.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(o.name)}</div>
                        <div class="ep-badges">${m.join("")}</div>
                    </div>
                    <div class="ep-url">${r||"-"}</div>
                    <div class="ep-stats">${d.join(" · ")}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(o.id)}">
                        <span>${escapeHtml(t("ep-edit"))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(o.id)}">
                        <span>${escapeHtml(t("ep-delete"))}</span>
                    </button>
                </div>
            </div>
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const o=Fe.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,l=document.createElement("div");l.className="erp-limit-hint",r==="free"?l.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:o,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:l.textContent=t("ep-plus-limit-hint",{used:o,limit:i}),e.appendChild(l)}}function Ev(e){Bn=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const s=document.getElementById("ep-name"),o=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),l=document.getElementById("ep-auto-push"),m=document.getElementById("ep-test-result");m.style.display="none",m.textContent="";const d=document.getElementById("ep-save-error");if(d&&d.remove(),e){const c=Fe.find(u=>u.id===e);if(!c)return;s.value=c.name||"",o.value=(c.config||{}).url||"",i.value=(c.config||{})._token_set&&c.config.token||"",i.placeholder=(c.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!c.is_default,l.checked=!!c.auto_push}else s.value="",o.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=Fe.length===0,l.checked=!0;const p=l.closest(".form-switch-row");if(l.disabled=!1,p){p.classList.remove("disabled-plus"),p.title="",p.style.cursor="",p.onclick=null;const c=p.querySelector(".plus-badge");c&&c.remove()}n.style.display="",setTimeout(()=>s.focus(),50)}function Ur(){document.getElementById("endpoint-modal").style.display="none",Bn=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function Gr(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function Wr(){const e=document.getElementById("ep-name").value.trim(),n=Gr(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,s=document.getElementById("ep-is-default").checked,o=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:s,autoPush:o,config:i}}async function Iv(){const{url:e,config:n}=Wr(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const o=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();o.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:o.http_status,ms:o.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.error_msg||"unknown"}))}catch(s){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.message})}}async function Bv(){const e=Wr(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){ci(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},s=document.getElementById("btn-ep-save"),o=s.innerHTML;s.disabled=!0,s.classList.add("loading");try{let i;if(Bn?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(Bn)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const l=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof l=="string"?l:JSON.stringify(l))}Ur(),showToast(t("ep-save-ok")),Ea()}catch(i){ci(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{s.disabled=!1,s.classList.remove("loading"),s.innerHTML=o}}function ci(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function Lv(e){const n=Fe.find(s=>s.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),Ea()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=Ea;window.loadErpTodayStats=Or;window.renderErpEndpointsList=Vr;window.openEndpointModal=Ev;window.closeEndpointModal=Ur;window.saveEndpoint=Bv;window.deleteEndpoint=Lv;window.testEndpointConnection=Iv;window._sanitizeUrl=Gr;async function Kr(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function $v(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const s=a.target.closest("[data-receipt-copy]");if(s){Kr(s.dataset.receiptCopy);return}const o=a.target.closest("[data-receipt-action]");if(o){const i=o.dataset.receiptAction;i==="retry"?window.retryPushLog(o.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const s=await a.json(),o=window._erpEndpoints.find(S=>S.id===s.endpoint_id),i=s.endpoint_name||(o?o.name:s.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(s.endpoint_adapter||o&&o.adapter||"").toLowerCase(),l=new Date(s.created_at).toLocaleString(),m=s.trigger==="auto"?t("log-tag-auto"):s.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),d=s.request_body?JSON.stringify(s.request_body,null,2):t("erp-receipt-no-tech"),p=s.response_body||t("erp-receipt-no-tech"),c=s.status==="success";let u=typeof p=="string"?p:JSON.stringify(p,null,2);if(c)try{const S=typeof s.response_body=="string"?JSON.parse(s.response_body):s.response_body||{},H=S.row_count||(Array.isArray(S.imported_rows)?S.imported_rows.length:0);H>0&&(u=t("log-push-rows").replace("{n}",String(H)))}catch{}const v=(s.external_doc_no||"").trim(),f=(s.external_url||"").trim(),y=(s.external_doc_hint||"").trim(),b=(s.ocr_buyer_name||"").trim()||s.client_name||"-",h=s.seller_name||"-",g=s.push_type==="id_card";let _="-";const w=Number(s.total_amount);s.total_amount!=null&&s.total_amount!==""&&!isNaN(w)&&(_=w.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const k=c?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),x=c?"✓":"✗",E=[],I=(S,H)=>{E.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(S)}</span>
                    <span class="erp-receipt-val">${H}</span>
                </div>`)};if(I(g?t("erp-log-col-booking"):t("erp-receipt-invoice-no"),`<strong>${escapeHtml(s.invoice_no||"-")}</strong>`),I(t("erp-receipt-erp-name"),escapeHtml(i)),c){let S;v?S=`<strong class="erp-receipt-docno">${escapeHtml(v)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(v)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:S=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,I(t("erp-receipt-doc-no"),S)}g||I(t("erp-receipt-client"),escapeHtml(b)),I(g?t("erp-log-col-customer"):t("erp-receipt-seller"),escapeHtml(h)),c&&I(t("erp-receipt-amount"),escapeHtml(_)),I(t("erp-receipt-time"),escapeHtml(l)),I(t("erp-receipt-elapsed"),escapeHtml((s.elapsed_ms!=null?s.elapsed_ms:"-")+"ms"));let B="";c&&f?B=`<a class="erp-receipt-primary-btn" href="${escapeHtml(f)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:c&&v&&(B=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(v)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let L="";if(c&&v&&y){const S="erp-receipt-hint-"+y,H=t(S);H&&H!==S&&(L=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(H)}</span></div>`)}let $="";if(!c){const S=(s.error_msg||"").match(/ERR_[A-Z0-9_]+/),H=S?S[0]:"",R=typeof currentLang=="string"&&currentLang||window._currentLang||"th",se=s.error_friendly&&s.error_friendly[R]||(s.error_msg?humanizeError(s.error_msg):t("erp-receipt-no-error")),ce=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(s.error_msg||""),_e=!!(s.history_id&&s.endpoint_id),we=[];we.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),ce&&we.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),_e&&we.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(s.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),$=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${H?`<div class="erp-receipt-errcode">${escapeHtml(H)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(se)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${we.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${c?"ok":"fail"}">${x}</span>
                    ${escapeHtml(k)}
                    <span class="log-tag ${s.trigger}">${escapeHtml(m)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${E.join("")}
            </div>

            ${L}
            ${B?`<div class="erp-receipt-primary-wrap">${B}</div>`:""}
            ${$}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t("erp-receipt-tech-toggle"))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${s.http_status||"-"}</span>
                    <span>${s.elapsed_ms}ms</span>
                    <span>${escapeHtml(t("log-detail-attempt",{n:s.attempt||1}))}</span>
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
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=Kr;window.showLogDetail=$v;const Sv=`
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
    `;$e("endpoint-modal",Sv);let pn={key:"all",val:""},kn="",Na=!1,lt=new Set;window._erpSelected=lt;async function Cv(){const e=document.getElementById("erp-logs-erp-select");if(!(!e||Na)){Na=!0;try{let n=window._erpEndpoints;if(!Array.isArray(n)||n.length===0){const o=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(o.ok){const i=await o.json();n=i&&(i.items||i)||[]}}Array.isArray(n)||(n=[]);const a=new Set,s=[];n.forEach(o=>{const i=(o&&o.adapter||"").toLowerCase();!i||a.has(i)||(a.add(i),s.push({val:i,label:o&&o.name||i}))}),e.innerHTML=`<option value="">${escapeHtml(t("erp-logs-erp-all"))}</option>`+s.map(o=>`<option value="${escapeHtml(o.val)}"${o.val===kn?" selected":""}>${escapeHtml(o.label)}</option>`).join("")}catch{Na=!1}}}async function Gt(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats(),Cv();try{const a=new URLSearchParams({limit:"30"});pn.key==="status"&&a.set("status",pn.val),pn.key==="trigger"&&a.set("trigger",pn.val),kn&&a.set("adapter",kn);const s=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!s.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await s.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(v){return v.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){Gt(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const r=i.filter(function(v){var f=v.status==="failed"&&v.next_retry_at&&new Date(v.next_retry_at).getTime()>Date.now()-6e4;return!f}).map(function(v){return v.id}),l=kn==="mrerp_dms",m=l?t("erp-log-col-booking"):t("erp-log-col-invoice"),d=l?t("erp-log-col-customer"):t("erp-log-col-seller"),p=l?t("erp-log-col-idcard"):t("erp-log-col-client"),c='<div class="erp-log-row erp-log-row-header" data-log-header>'+(r.length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(m)}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(p)}</span><span class="log-seller">${escapeHtml(d)}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=c+i.map(v=>{const f=new Date(v.created_at),y=`${String(f.getMonth()+1).padStart(2,"0")}-${String(f.getDate()).padStart(2,"0")} ${String(f.getHours()).padStart(2,"0")}:${String(f.getMinutes()).padStart(2,"0")}`,b=v.status==="failed"&&v.next_retry_at&&new Date(v.next_retry_at).getTime()>Date.now()-6e4;let h,g,_;v.status==="pending"?(h="retrying",g="⟳",_=t("erp-status-pending")):v.status==="success"?(h="ok",g="✓",_=t("erp-status-success")):v.status==="skipped_dup"?(h="skipped",g="⏭",_=t("erp-status-skipped")):b?(h="retrying",g="↻",_=t("erp-status-retrying")):(h="fail",g="✗",_=t("erp-status-failed"));let w;v.trigger==="auto"?w=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:v.trigger==="retry"?w=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:w=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;const k=v.push_type==="id_card",x=k?`<span class="log-tag log-type-idcard">${escapeHtml(t("erp-log-type-idcard"))}</span>`:"",E=v.error_friendly&&(v.error_friendly[currentLang]||v.error_friendly.en)||"";let I="";const B=v.retry_count||0,L=v.max_retries||3;if(b){const Y=new Date(v.next_retry_at).getTime()-Date.now(),de=Math.max(0,Math.round(Y/6e4)),re=de<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:de});I=`${t("erp-retry-attempt",{n:B,max:L})} · ${re}`}else v.status==="failed"&&B>=L&&!v.next_retry_at&&(I=t("erp-retry-exhausted",{n:B}));const $=v.status==="failed"&&!b?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(v.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",S=!b,H=lt.has(v.id)?"checked":"",R=S?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(v.id)}" ${H}>`:'<span class="erp-log-cb-spacer"></span>',G=(v.ocr_buyer_name||"").trim()||(v.client_name||"").trim(),se=k?`<span class="log-client" title="${escapeHtml(t("erp-log-col-idcard"))}">${v.id_card_tail?"••••"+escapeHtml(v.id_card_tail):"—"}</span>`:G?`<span class="log-client" title="${escapeHtml(G)}">${escapeHtml(G.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,ce=k?'<span class="log-workspace log-workspace-unresolved">—</span>':v.workspace_name?`<span class="log-workspace">${escapeHtml((v.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,_e=v.endpoint_name?`<span class="log-erp">${escapeHtml((v.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,we=(v.external_doc_no||"").trim(),O=(v.external_url||"").trim();let N;return O?N=`<span class="log-doc"><a href="${escapeHtml(O)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(we||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:we?N=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(we)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(we.substring(0,18))}</span>`:v.status==="success"?N=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:N='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${h}" data-log-detail="${escapeHtml(v.id)}">
                    ${R}
                    <span class="log-time">${y}</span>
                    <span class="log-status" title="${escapeHtml(_+(I?" · "+I:"")+(E?" · "+E:""))}">${g}</span>
                    ${w}${x}
                    <span class="log-invoice"${k?` title="${escapeHtml(t("erp-log-col-booking"))}"`:""}>${escapeHtml(v.invoice_no||"-")}</span>
                    ${ce}
                    ${se}
                    <span class="log-seller"${k?` title="${escapeHtml(t("erp-log-col-customer"))}"`:""}>${escapeHtml((v.seller_name||"").substring(0,20))}</span>
                    ${_e}
                    ${N}
                    <span class="log-http">HTTP ${v.http_status||"-"}</span>
                    <span class="log-elapsed">${v.elapsed_ms}ms</span>
                    <span class="log-actions">${$}</span>
                </div>
            `}).join("");const u=new Set(i.map(v=>v.id));for(const v of Array.from(lt))u.has(v)||lt.delete(v);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function Yr(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),Gt(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),s=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),s&&window.deleteEndpoint(s.dataset.epDel);const o=n.target.closest("[data-log-retry]");if(o){n.stopPropagation(),Yr(o.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const p=i.dataset.logCb;i.checked?lt.add(p):lt.delete(p),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const p=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(u){u.checked=p;const v=u.dataset.logCb;p?lt.add(v):lt.delete(v)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),lt.clear(),document.querySelectorAll(".erp-log-cb").forEach(p=>{p.checked=!1}),window._refreshErpBatchBar();return}const l=n.target.closest("[data-log-detail]");if(l){if(n.target.closest("[data-log-cb]"))return;const p=n.target.closest("[data-copy-doc]");if(p){n.stopPropagation(),window.copyErpDocNo(p.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(l.dataset.logDetail);return}const m=n.target.closest(".chip-filter");if(m){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(p=>p.classList.remove("active")),m.classList.add("active"),pn={key:m.dataset.filterKey,val:m.dataset.filterVal},Gt();return}if(n.target.closest("#btn-refresh-logs")){const p=n.target.closest("#btn-refresh-logs");p.classList.add("spinning"),setTimeout(()=>p.classList.remove("spinning"),600),Gt();return}const d=n.target.closest(".auto-nav-item");if(d&&d.dataset.autoTab){switchAutomationTab(d.dataset.autoTab);return}}),document.addEventListener("change",n=>{n.target&&n.target.id==="erp-logs-erp-select"&&(kn=n.target.value||"",Gt())})})();window.loadErpLogs=Gt;window.retryPushLog=Yr;function Jr(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const s=window._erpSelected.size;if(s===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:s})}async function Xr(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const s=await a.json(),o=t("erp-batch-result",{ok:s.succeeded||0,fail:s.failed||0,skip:s.skipped||0}),i=s.failed&&s.failed>0?"warn":"success";showToast(o,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function Zr(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const s=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!s.ok){showToast(t("erp-logs-error"),"error");return}const o=await s.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:o.deleted||0,skip:o.skipped||0}),o.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(s){console.error("batch delete failed",s),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),s=document.getElementById("btn-erp-batch-delete"),o=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),Xr()}),a.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),Zr()}),s.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),Jr()}),o.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=Jr;window._runErpBatchRetry=Xr;window._runErpBatchDelete=Zr;(function(){let e=null,n=!1;function a(){if(e)return e;const l=document.createElement("div");l.id="line-email-modal",l.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",l.innerHTML=`
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
        `,document.body.appendChild(l),e=l;const m=l.querySelector("#line-email-input"),d=l.querySelector("#line-email-submit-btn"),p=l.querySelector("#line-email-err");async function c(){p.textContent="";const u=(m.value||"").trim().toLowerCase();if(!u||u.indexOf("@")<0||u.split("@")[1].indexOf(".")<0){p.textContent=t("line-email-err-invalid");return}d.disabled=!0,d.style.opacity="0.6";try{const v=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:u})});if(!v.ok)throw new Error("http_"+v.status);const f=await v.json();f.token&&localStorage.setItem("mrpilot_token",f.token),typeof showToast=="function"&&showToast(f.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{p.textContent=t("line-email-err-failed"),d.disabled=!1,d.style.opacity="1"}}return d.addEventListener("click",c),m.addEventListener("keydown",function(u){u.key==="Enter"&&c()}),l}function s(){if(!e)return;const l=e.querySelector("#line-email-title-h"),m=e.querySelector("#line-email-sub-p"),d=e.querySelector("#line-email-input"),p=e.querySelector("#line-email-submit-btn");l&&(l.textContent=t("line-email-title")),m&&(m.textContent=t("line-email-sub")),d&&(d.placeholder=t("line-email-placeholder")),p&&(p.textContent=t("line-email-submit"))}function o(){a(),s(),e.style.display="flex",n=!0;const l=e.querySelector("#line-email-input");l&&setTimeout(function(){l.focus()},100)}async function i(){const l=localStorage.getItem("mrpilot_token");if(l)try{const m=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+l}});if(!m.ok)return;const d=await m.json();d&&d.needs_email&&o()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&s()})})();(function(){function e(p){let c=0;return p.length>=8&&c++,p.length>=12&&c++,/[a-zA-Z]/.test(p)&&/\d/.test(p)&&c++,/[^a-zA-Z0-9]/.test(p)&&c++,Math.min(3,c)}function n(p,c){const u=document.getElementById("cpw-msg");u&&(u.textContent=p,u.className="cpw-msg "+(c||""))}function a(p){return typeof t=="function"?t(p):p}let s=!1;function o(){["cpw-old","cpw-new","cpw-confirm"].forEach(c=>{const u=document.getElementById(c);u&&(u.value="",u.setAttribute("readonly","readonly"))});const p=document.getElementById("cpw-strength-bar");p&&(p.style.width="0%",p.className="cpw-strength-bar"),n("","")}async function i(){const p=document.getElementById("btn-change-pw"),c=document.getElementById("cpw-old"),u=document.getElementById("cpw-new"),v=document.getElementById("cpw-confirm"),f=document.getElementById("cpw-strength-bar");if(!p||!c||!u||!v)return;const y=c.value,b=u.value,h=v.value;if(!y||!b||!h){n(a("settings-change-pw-empty"),"error");return}if(b.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(b)&&/\d/.test(b))){n(a("settings-change-pw-too-weak"),"error");return}if(b!==h){n(a("settings-change-pw-mismatch"),"error");return}p.disabled=!0;const g=p.textContent;p.textContent=a("settings-change-pw-submitting"),n("","");try{const _=localStorage.getItem("mrpilot_token"),w=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+_},body:JSON.stringify({old_password:y,new_password:b})}),k=await w.json().catch(()=>({}));if(w.ok&&k.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),c.value="",u.value="",v.value="",f&&(f.style.width="0%",f.className="cpw-strength-bar");else{const x=k.detail||"";let E=a("settings-change-pw-success");x==="wrong_old_password"?E=a("settings-change-pw-wrong-old"):x==="password_too_short"?E=a("settings-change-pw-too-short"):x==="password_too_weak"?E=a("settings-change-pw-too-weak"):E=x||"Error",n(E,"error")}}catch(_){console.error("change_password",_),n("Network error","error")}finally{p.disabled=!1,p.textContent=g}}function r(){s||(s=!0,document.addEventListener("click",p=>{if(!p.target||!p.target.closest)return;const c=p.target.closest(".cpw-eye");if(c){const u=document.getElementById(c.dataset.target);u&&(u.type=u.type==="password"?"text":"password");return}if(p.target.closest("#cpw-forgot-link")){p.preventDefault(),l();return}if(p.target.closest("#btn-change-pw")){i();return}p.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(o,100)}),document.addEventListener("input",p=>{if(p.target&&p.target.id==="cpw-new"){const c=document.getElementById("cpw-strength-bar");if(!c)return;const u=e(p.target.value),v=["0%","33%","66%","100%"],f=["","weak","medium","strong"];c.style.width=v[u],c.className="cpw-strength-bar "+f[u]}}),document.addEventListener("focusin",p=>{p.target&&["cpw-old","cpw-new","cpw-confirm"].includes(p.target.id)&&p.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&o())}function l(){const p=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),c=p&&p.username?p.username:"",u=m(c);let v=document.getElementById("cpw-forgot-overlay");v&&v.remove(),v=document.createElement("div"),v.id="cpw-forgot-overlay",v.className="cpw-forgot-overlay",v.innerHTML=`
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
        `,document.body.appendChild(v);const f=()=>v.remove();v.querySelector("#cpw-forgot-close").addEventListener("click",f),v.querySelector("#cpw-forgot-cancel").addEventListener("click",f),v.addEventListener("click",y=>{y.target===v&&f()}),v.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const y=v.querySelector("#cpw-forgot-send"),b=v.querySelector("#cpw-forgot-msg");y.disabled=!0;const h=y.textContent;y.textContent=a("cpw-forgot-sending");try{const g=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:c})}),_=await g.json().catch(()=>({}));g.ok?(b.textContent=a("cpw-forgot-success"),b.className="cpw-forgot-msg success",y.style.display="none",v.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(b.textContent=_.detail||a("cpw-forgot-fail"),b.className="cpw-forgot-msg error",y.disabled=!1,y.textContent=h)}catch{b.textContent=a("cpw-forgot-fail"),b.className="cpw-forgot-msg error",y.disabled=!1,y.textContent=h}})}function m(p){if(!p||!p.includes("@"))return p||"";const[c,u]=p.split("@");return c.length<=2?c+"****@"+u:c.slice(0,2)+"****@"+u}function d(p){return p==null?"":String(p).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const o=localStorage.getItem("mrpilot_token");if(o){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+o},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),l=r&&r.detail;let m="";if(typeof l=="string"?m=l:l&&typeof l=="object"&&(m=l.code||""),console.warn("[heartbeat] session revoked",m),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),m==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const d=m==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(d),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function s(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&s(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function Ia(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),s=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const o=await apiGet("/api/team/employees"),i=o&&o.employees||[];if(e&&(e.style.display="none"),s&&(s.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const l=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",m=r.is_active===!1?"team-status-off":"team-status-on",d=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",p=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${m}"></span>
                            <span>${escapeHtml(d)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(l)}</span>
                            ${p}
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
            </div>`}).join("")}catch(o){console.error("loadTeamList failed:",o),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Tv(){document.querySelectorAll(".add-emp-overlay").forEach(s=>s.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const s=document.getElementById("add-emp-username");s&&s.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",s=>{s.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const s=document.getElementById("add-emp-username"),o=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),l=document.getElementById("add-emp-submit"),m=(s.value||"").trim(),d=(o.value||"").trim(),p=i.value||"";if(r.textContent="",r.classList.remove("error"),!m||m.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(m)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(d&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(p.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(p)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(p)&&/\d/.test(p))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}l.disabled=!0,l.textContent=t("msg-saving")||"保存中...";try{const c={username:m,password:p};d&&(c.email=d);const u=await apiPost("/api/team/employees",c),v=u?await u.json().catch(()=>({})):{};if(u&&u.ok&&v&&v.ok){showToast(t("team-added")||"员工已添加","success"),n(),Ia();return}const f=v&&v.detail||"unknown",y={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=y[f]||(t("team-create-failed")||"创建失败")+" ("+f+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{l.disabled=!1,l.textContent=t("team-add")||"添加员工"}});function a(s){s.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function Hv(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){Ia();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Mv(e,n){const s=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(s,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),Ia();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function Av(e,n){const s=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(s,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const l=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",m=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(l.replace("{ch}",m),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Tv();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),Hv(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),Mv(a.dataset.removeEmployee,a.dataset.name||"");return}const s=e.target.closest("[data-reset-pwd-employee]");if(s){e.preventDefault(),Av(s.dataset.resetPwdEmployee,s.dataset.name||"");return}const o=e.target.closest("[data-assign-clients]");if(o){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(o.dataset.assignClients,o.dataset.name||"");return}});window.loadTeamList=Ia;function Pv(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=Pv;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
